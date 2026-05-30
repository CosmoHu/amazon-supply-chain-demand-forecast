"""页面4：补货计划 —— 回答「什么时候订、订多少」
   核心特性：输入实际期初库存与订货成本，PuLP 实时重新求解最优补货计划。"""
import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import pulp
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import data_loader as dl

st.set_page_config(page_title="补货计划", page_icon="🚚", layout="wide")
st.title("🚚 补货计划")

# ---- 加载数据 ----
sales = dl.load_sales()
forecast = dl.load_forecast()
cats = dl.get_categories()

sales = sales.copy()
sales['Week'] = sales['OrderDate'].dt.to_period('W').dt.start_time
weekly = sales.groupby(['Category', 'Week'])['Quantity'].sum().reset_index()

# ---- PuLP 优化函数 ----
def optimize(demand, h, order_cost, ss, init_inv):
    T = len(demand)
    M = float(sum(demand) + init_inv)
    prob = pulp.LpProblem("Replenishment", pulp.LpMinimize)
    O = [pulp.LpVariable(f"O_{t}", lowBound=0) for t in range(T)]
    I = [pulp.LpVariable(f"I_{t}", lowBound=ss) for t in range(T)]
    y = [pulp.LpVariable(f"y_{t}", cat="Binary") for t in range(T)]
    prob += pulp.lpSum(h*I[t] for t in range(T)) + pulp.lpSum(order_cost*y[t] for t in range(T))
    for t in range(T):
        prob += I[t] == (init_inv if t == 0 else I[t-1]) + O[t] - demand[t]
        prob += O[t] <= M * y[t]
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return ([pulp.value(O[t]) for t in range(T)],
            [pulp.value(I[t]) for t in range(T)],
            pulp.value(prob.objective))

# ---- 侧边栏控件 ----
st.sidebar.header("参数输入")
sel_cat = st.sidebar.selectbox("选择品类", cats)
service_level = st.sidebar.slider("服务水平", 0.80, 0.99, 0.95, 0.01)
order_cost = st.sidebar.number_input("单次订货成本（元）", 500, 5000, 2000, 100)
hold_rate = st.sidebar.slider("年持库成本率", 0.10, 0.45, 0.25, 0.05)

# 计算默认期初库存（安全库存），供输入框默认值
demand = forecast[forecast['Category'] == sel_cat]['Forecast_Demand'].values
HORIZON = len(demand)
wstd = weekly[weekly['Category'] == sel_cat]['Quantity'].std()
ss = float(round(stats.norm.ppf(service_level) * wstd, 0))
init_inv = st.sidebar.number_input("期初库存（件）", 0, 10000, int(ss), 10,
                                   help="输入仓库当前实际库存，系统据此重新求解")

# ---- 实时求解 ----
price = sales[sales['Category'] == sel_cat]['UnitPrice'].mean()
h = price * hold_rate / 52

with st.spinner("正在求解最优补货计划..."):
    orders, inventory, total_cost = optimize(demand, h, order_cost, ss, init_inv)

# ---- 指标卡 ----
n_orders = sum(1 for o in orders if o > 0.5)
first_week = next((t+1 for t, o in enumerate(orders) if o > 0.5), None)
c1, c2, c3, c4 = st.columns(4)
c1.metric("规划总成本", f"{total_cost:.0f} 元")
c2.metric("12周订货次数", f"{n_orders} 次")
c3.metric("首次订货", f"第 {first_week} 周" if first_week else "无需订货")
c4.metric("安全库存下限", f"{ss:.0f} 件")

st.divider()

# ---- 补货计划表 ----
st.subheader(f"{sel_cat}：未来12周补货计划")
plan_df = pd.DataFrame({
    '周次': [f'第{t+1}周' for t in range(HORIZON)],
    '预测需求': [round(d) for d in demand],
    '建议订货量': [round(o) for o in orders],
    '期末库存': [round(i) for i in inventory],
    '是否订货': ['✅ 订货' if o > 0.5 else '' for o in orders],
})
st.dataframe(plan_df, use_container_width=True, hide_index=True)

# ---- 库存与订货轨迹图 ----
st.subheader("库存与订货轨迹")
chart_df = pd.DataFrame({
    '预测需求': demand,
    '订货量': orders,
    '期末库存': inventory,
}, index=[f'第{t+1}周' for t in range(HORIZON)])
st.line_chart(chart_df)
st.caption(f"调整左侧「期初库存」可观察补货计划如何动态调整：期初库存越高，"
           f"首次订货时点越晚、订货次数越少。当前期初 {init_inv} 件，首次订货第 {first_week} 周。")

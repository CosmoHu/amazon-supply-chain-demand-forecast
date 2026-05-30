"""页面3：库存优化 —— 回答「该备多少货、服务水平与成本如何权衡」
   核心特性：拖动服务水平/持库率滑块，安全库存与EOQ实时重算。"""
import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import data_loader as dl

st.set_page_config(page_title="库存优化", page_icon="📦", layout="wide")
st.title("📦 库存优化")

# ---- 加载数据 ----
sales = dl.load_sales()
abc = dl.load_abc()
cats = dl.get_categories()

# ---- 侧边栏控件 ----
st.sidebar.header("参数调整")
sel_cat = st.sidebar.selectbox("选择品类", cats)
service_level = st.sidebar.slider("服务水平", 0.80, 0.99, 0.95, 0.01)
hold_rate = st.sidebar.slider("年持库成本率", 0.10, 0.45, 0.25, 0.05)
lead_time = st.sidebar.slider("提前期（天）", 3, 14, 7)
order_cost = st.sidebar.number_input("单次订货成本（元）", 10, 500, 50, 10)

# ---- ABC 分类展示 ----
st.subheader(f"{sel_cat}：ABC 分类结构")
cat_abc = abc[abc['Category'] == sel_cat]['ABC_Class'].value_counts().reindex(['A', 'B', 'C']).fillna(0)
c1, c2, c3 = st.columns(3)
c1.metric("A 类 SKU", f"{int(cat_abc['A'])} 个", help="高价值，重点管理")
c2.metric("B 类 SKU", f"{int(cat_abc['B'])} 个", help="中等价值")
c3.metric("C 类 SKU", f"{int(cat_abc['C'])} 个", help="低价值，粗放管理")

st.divider()

# ---- 实时计算：安全库存 + 期望缺货量 随服务水平变化 ----
st.subheader("安全库存与缺货成本（随服务水平实时变化）")

# 该品类各 SKU 日需求标准差的平均
dr = pd.date_range(sales['OrderDate'].min(), sales['OrderDate'].max(), freq='D')
stds = []
for pid in abc[abc['Category'] == sel_cat]['ProductID']:
    s = sales[sales['ProductID'] == pid].groupby('OrderDate')['Quantity'].sum().reindex(dr, fill_value=0)
    stds.append(s.std())
avg_std = np.mean(stds)
avg_price = sales[sales['Category'] == sel_cat]['UnitPrice'].mean()

# 当前滑块对应的值
z = stats.norm.ppf(service_level)
ss_now = z * avg_std * np.sqrt(lead_time)
Lz = stats.norm.pdf(z) - z * (1 - stats.norm.cdf(z))
exp_short = Lz * avg_std * np.sqrt(lead_time)
exp_cost = exp_short * avg_price * 2

m1, m2, m3 = st.columns(3)
m1.metric("当前安全库存", f"{ss_now:.1f} 件")
m2.metric("每周期期望缺货量", f"{exp_short:.2f} 件")
m3.metric("每周期期望缺货成本", f"{exp_cost:.0f} 元")

# 安全库存随服务水平变化曲线
sl_range = np.arange(0.80, 1.00, 0.01)
ss_curve = pd.DataFrame({
    '安全库存': [stats.norm.ppf(s) * avg_std * np.sqrt(lead_time) for s in sl_range],
}, index=[f'{s*100:.0f}%' for s in sl_range])
st.line_chart(ss_curve)
st.caption(f"提高服务水平需要更多安全库存。当前 {service_level*100:.0f}% 对应 {ss_now:.1f} 件。"
           "拖动左侧滑块可实时观察变化。")

st.divider()

# ---- 实时计算：EOQ 成本曲线 ----
st.subheader("经济订货批量 EOQ（随持库率实时变化）")
n_days = (sales['OrderDate'].max() - sales['OrderDate'].min()).days + 1
annual_demand = sales[sales['Category'] == sel_cat]['Quantity'].sum() * (365.0 / n_days) / max(int(cat_abc.sum()), 1)
holding_unit = avg_price * hold_rate
eoq = np.sqrt(2 * annual_demand * order_cost / holding_unit) if holding_unit > 0 else 0

e1, e2, e3 = st.columns(3)
e1.metric("单 SKU 年均需求", f"{annual_demand:.0f} 件")
e2.metric("最优订货批量 EOQ", f"{eoq:.0f} 件")
e3.metric("年订货次数", f"{annual_demand/eoq:.1f} 次" if eoq > 0 else "—")

# EOQ 成本曲线
q_range = np.arange(max(int(eoq*0.2), 1), int(eoq*2.5), 1)
cost_df = pd.DataFrame({
    '订货成本': annual_demand / q_range * order_cost,
    '持库成本': q_range / 2 * holding_unit,
    '总成本': annual_demand / q_range * order_cost + q_range / 2 * holding_unit,
}, index=q_range)
st.line_chart(cost_df)
st.caption(f"总成本曲线最低点即 EOQ（{eoq:.0f} 件）。持库率越高，EOQ 越小（每次少订）。")

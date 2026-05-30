"""页面1：销售概览 —— 回答「现在卖得怎么样」"""
import streamlit as st
import pandas as pd
import sys, os

# 让本页能 import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import data_loader as dl

st.set_page_config(page_title="销售概览", page_icon="📊", layout="wide")
st.title("📊 销售概览")

# ---- 加载数据 ----
sales = dl.load_sales()
cats = dl.get_categories()

# ---- 侧边栏控件 ----
st.sidebar.header("筛选条件")
sel_cats = st.sidebar.multiselect("选择品类", cats, default=cats)
min_date, max_date = sales['OrderDate'].min(), sales['OrderDate'].max()
date_range = st.sidebar.date_input(
    "选择日期范围", value=(min_date, max_date),
    min_value=min_date, max_value=max_date)

# ---- 过滤数据 ----
if len(date_range) == 2:
    d0, d1 = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
else:
    d0, d1 = min_date, max_date

sub = sales[(sales['Category'].isin(sel_cats)) & (sales['OrderDate'].between(d0, d1))]

if sub.empty:
    st.warning("当前筛选条件下没有数据，请调整品类或日期范围。")
    st.stop()

# ---- 指标卡 ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("总销售额", f"{sub['TotalAmount'].sum()/10000:.1f} 万")
c2.metric("总销量", f"{sub['Quantity'].sum():,} 件")
c3.metric("SKU 数量", f"{sub['ProductID'].nunique()} 个")
c4.metric("日均销量", f"{sub.groupby('OrderDate')['Quantity'].sum().mean():.0f} 件")

st.divider()

# ---- 日销量趋势 ----
st.subheader("日销量趋势")
daily = sub.groupby('OrderDate')['Quantity'].sum()
st.line_chart(daily)
st.caption("反映整体销售随时间的波动，可识别旺季、淡季与异常波动。")

# ---- 两列：品类占比 + 节假日对比 ----
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("品类销售额占比")
    cat_rev = sub.groupby('Category')['TotalAmount'].sum().sort_values(ascending=False)
    st.bar_chart(cat_rev)
    st.caption("识别主力品类，指导资源与库存的优先级分配。")

with col_b:
    st.subheader("节假日 vs 非节假日（日均销量）")
    hol = sub.groupby('IsHoliday')['Quantity'].mean()
    hol.index = ['非节假日' if i == 0 else '节假日' for i in hol.index]
    st.bar_chart(hol)
    st.caption("评估节假日对销量的影响，为促销备货提供依据。")

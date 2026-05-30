"""页面2：需求预测 —— 回答「未来会卖多少、预测有多准」"""
import streamlit as st
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import data_loader as dl

st.set_page_config(page_title="需求预测", page_icon="📈", layout="wide")
st.title("📈 需求预测")

# ---- 加载数据 ----
sales = dl.load_sales()
forecast = dl.load_forecast()
accuracy = dl.load_forecast_accuracy()
cats = dl.get_categories()

# ---- 侧边栏控件 ----
st.sidebar.header("筛选条件")
sel_cat = st.sidebar.selectbox("选择品类", cats)
n_hist = st.sidebar.slider("显示最近几周历史", 10, 52, 20)
n_future = st.sidebar.slider("预测周数", 4, 12, 12)

# ---- 历史周度销量 ----
sales = sales.copy()
sales['Week'] = sales['OrderDate'].dt.to_period('W').dt.start_time
hist = sales[sales['Category'] == sel_cat].groupby('Week')['Quantity'].sum()
hist_recent = hist.tail(n_hist)

# ---- 预测 ----
fc_cat = forecast[forecast['Category'] == sel_cat].head(n_future).set_index('Week')['Forecast_Demand']

# ---- 精度指标卡 ----
cat_wmape = accuracy[accuracy['Category'] == sel_cat]['WMAPE_%'].values[0]
c1, c2, c3 = st.columns(3)
c1.metric(f"{sel_cat} 预测精度 (WMAPE)", f"{cat_wmape:.2f}%")
c2.metric("全品类平均 WMAPE", f"{accuracy['WMAPE_%'].mean():.2f}%")
c3.metric("未来预测周数", f"{n_future} 周")

st.divider()

# ---- 历史 + 预测 合并图 ----
st.subheader(f"{sel_cat}：历史销量与未来预测")
combined = pd.DataFrame({'历史销量': hist_recent})
combined = combined.join(pd.DataFrame({'预测需求': fc_cat}), how='outer')
st.line_chart(combined)
st.caption("蓝线为历史实际销量，橙线为未来预测。两线衔接处体现预测的连续性。"
           "预测采用周度历史同期均值法，自然包含季节性规律。")

st.divider()

# ---- 各品类精度对比 ----
st.subheader("各品类预测精度对比")
acc_sorted = accuracy.sort_values('WMAPE_%').set_index('Category')['WMAPE_%']
st.bar_chart(acc_sorted)
st.caption("WMAPE 越低预测越准。可据此识别哪些品类需求规律性强、哪些波动大需谨慎备货。")

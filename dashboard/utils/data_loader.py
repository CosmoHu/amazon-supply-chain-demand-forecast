"""
数据加载工具
统一读取第5、6周生成的各 CSV，使用 Streamlit 缓存避免重复读取。
所有页面通过本模块获取数据，保证数据来源一致。
"""
import pandas as pd
import streamlit as st

# 数据目录（相对项目根目录）
BASE = 'data/processed/'


def _read(name, parse_dates=None):
    return pd.read_csv(BASE + name, parse_dates=parse_dates)


@st.cache_data
def load_sales():
    """日销售明细数据"""
    return _read('amazon_daily_sales_train.csv', parse_dates=['OrderDate'])


@st.cache_data
def load_forecast():
    """未来12周需求预测"""
    return _read('forecast_results.csv', parse_dates=['Week'])


@st.cache_data
def load_forecast_accuracy():
    """各品类预测精度(WMAPE)"""
    return _read('forecast_accuracy.csv')


@st.cache_data
def load_abc():
    """ABC 分类结果"""
    return _read('abc_classification.csv')


@st.cache_data
def load_safety_stock():
    """安全库存（三档服务水平）"""
    return _read('safety_stock.csv')


@st.cache_data
def load_eoq():
    """EOQ 经济订货批量"""
    return _read('eoq_results.csv')


@st.cache_data
def load_replenishment():
    """未来3个月补货计划"""
    return _read('replenishment_plan_3months.csv', parse_dates=['Week'])


@st.cache_data
def get_categories():
    """品类列表"""
    return sorted(load_sales()['Category'].unique().tolist())

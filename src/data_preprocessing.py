"""
亚马逊供应链项目 - 第二周：数据清洗与预处理脚本
功能：加载原始数据 -> 清理异常值 -> 提取时间特征 -> 构建产品-日期粒度数据集
"""
import pandas as pd
import os

def main():
    print("开始执行第二周数据预处理流程...")
    
    # 1. 定义绝对路径
    base_path = '/Users/huyujie/Documents/amazon-supply-chain-project/data/processed/'
    
    # 2. 读取带特征的数据
    print("正在读取数据...")
    df_amazon = pd.read_csv(base_path + 'train_amazon_features.csv')
    df_uci = pd.read_csv(base_path + 'train_uci_features.csv')
    
    # 3. 清理重复值
    df_uci = df_uci.drop_duplicates().reset_index(drop=True)
    
    # 4. 构建产品-日期粒度数据集 (Amazon)
    print("正在聚合 Amazon 数据...")
    amazon_daily = df_amazon.groupby(['OrderDate', 'ProductID']).agg({
        'Quantity': 'sum',
        'TotalAmount': 'sum',
        'UnitPrice': 'mean',
        'Category': 'first',
        'IsHoliday': 'first'
    }).reset_index()
    
    # 5. 构建产品-日期粒度数据集 (UCI)
    print("正在聚合 UCI 数据...")
    df_uci['JustDate'] = pd.to_datetime(df_uci['InvoiceDate']).dt.date
    uci_daily = df_uci.groupby(['JustDate', 'StockCode']).agg({
        'Quantity': 'sum',
        'UnitPrice': 'mean',
        'Description': 'first',
        'IsHoliday': 'first'
    }).reset_index()
    
    # 6. 保存最终结果
    print("正在保存最终数据集...")
    amazon_daily.to_csv(base_path + 'amazon_daily_sales_train.csv', index=False)
    uci_daily.to_csv(base_path + 'uci_daily_sales_train.csv', index=False)
    
    print("✅ 数据清洗与预处理脚本执行完毕！所有产出均已保存至 data/processed/ 目录。")

if __name__ == "__main__":
    main()
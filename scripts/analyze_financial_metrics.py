#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
財務指標分析腳本 - 展示如何從營收和毛利率推估EPS
"""

import sys
import os
from datetime import datetime
import pandas as pd

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
from app.services.data_collector import FinMindDataCollector
from loguru import logger

def get_financial_statements_sample(collector, stock_id="2330", start_date="2023-01-01"):
    """獲取財務報表範例資料"""
    try:
        data = collector._make_request(
            dataset="TaiwanStockFinancialStatements",
            data_id=stock_id,
            start_date=start_date,
            end_date="2025-07-23"
        )
        
        if data and 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            return df
        return None
        
    except Exception as e:
        print(f"獲取財務報表失敗: {e}")
        return None

def analyze_financial_metrics(df, stock_id):
    """分析財務指標"""
    if df is None or df.empty:
        print(f"❌ {stock_id} 無財務報表資料")
        return
    
    print(f"\n📊 {stock_id} 財務報表分析")
    print("=" * 60)
    
    # 按日期分組分析
    dates = df['date'].unique()
    
    for date in sorted(dates)[-4:]:  # 只看最近4個季度
        date_data = df[df['date'] == date]
        
        print(f"\n📅 {date} 財務數據:")
        print("-" * 40)
        
        # 建立數據字典
        metrics = {}
        for _, row in date_data.iterrows():
            metrics[row['type']] = row['value']
        
        # 關鍵財務指標
        revenue = metrics.get('Revenue', 0)
        cost_of_goods = metrics.get('CostOfGoodsSold', 0)
        gross_profit = metrics.get('GrossProfit', 0)
        operating_income = metrics.get('OperatingIncome', 0)
        net_income = metrics.get('IncomeAfterTaxes', 0)
        eps = metrics.get('EPS', 0)
        
        print(f"💰 營業收入: {revenue:,.0f} 千元")
        print(f"💸 營業成本: {cost_of_goods:,.0f} 千元")
        print(f"💵 營業毛利: {gross_profit:,.0f} 千元")
        print(f"📈 營業利益: {operating_income:,.0f} 千元")
        print(f"💎 本期淨利: {net_income:,.0f} 千元")
        print(f"🎯 每股盈餘: {eps:.2f} 元")
        
        # 計算比率
        if revenue > 0:
            gross_margin = (gross_profit / revenue) * 100
            operating_margin = (operating_income / revenue) * 100
            net_margin = (net_income / revenue) * 100
            
            print(f"\n📊 獲利能力分析:")
            print(f"  毛利率: {gross_margin:.1f}%")
            print(f"  營業利益率: {operating_margin:.1f}%")
            print(f"  淨利率: {net_margin:.1f}%")
        
        # EPS推估邏輯說明
        if revenue > 0 and gross_profit > 0:
            print(f"\n🔍 EPS推估邏輯:")
            print(f"  1. 營業收入: {revenue:,.0f}")
            print(f"  2. 減去營業成本: {cost_of_goods:,.0f}")
            print(f"  3. 得到營業毛利: {gross_profit:,.0f}")
            print(f"  4. 毛利率: {(gross_profit/revenue)*100:.1f}%")
            print(f"  5. 最終淨利: {net_income:,.0f}")
            print(f"  6. 每股盈餘: {eps:.2f} 元")
            
            # 簡化推估公式
            if eps > 0 and net_income > 0:
                estimated_shares = net_income / eps  # 推估流通股數
                print(f"  7. 推估流通股數: {estimated_shares:,.0f} 千股")

def demonstrate_eps_estimation():
    """展示EPS推估方法"""
    print("\n" + "=" * 60)
    print("📈 從營收和毛利率推估EPS的方法")
    print("=" * 60)
    
    print("""
🎯 EPS推估的完整公式鏈：

1️⃣ 基礎數據：
   • 營業收入 (Revenue)
   • 營業成本 (Cost of Goods Sold)
   • 營業毛利 = 營業收入 - 營業成本

2️⃣ 毛利率計算：
   • 毛利率 = (營業毛利 ÷ 營業收入) × 100%

3️⃣ EPS推估路徑：
   營業收入
   ↓ (減去營業成本)
   營業毛利
   ↓ (減去營業費用)
   營業利益
   ↓ (加減營業外收支)
   稅前淨利
   ↓ (減去所得稅)
   稅後淨利
   ↓ (除以流通股數)
   每股盈餘 (EPS)

4️⃣ 關鍵比率：
   • 毛利率 = 反映產品競爭力
   • 營業利益率 = 反映營運效率
   • 淨利率 = 反映整體獲利能力

5️⃣ 推估準確性：
   ✅ 高準確性：有完整財務報表
   ⚠️  中準確性：只有營收+歷史毛利率
   ❌ 低準確性：只有營收資料
""")

def show_available_financial_types(df):
    """顯示可用的財務報表欄位"""
    if df is None or df.empty:
        return
    
    print("\n📋 FinMind財務報表可用欄位:")
    print("=" * 60)
    
    types_with_names = df[['type', 'origin_name']].drop_duplicates()
    
    # 分類顯示
    revenue_related = types_with_names[types_with_names['type'].str.contains('Revenue|Income|Profit|Cost', case=False, na=False)]
    
    print("💰 營收和獲利相關:")
    for _, row in revenue_related.iterrows():
        print(f"  {row['type']:<30} - {row['origin_name']}")
    
    print(f"\n📊 總共有 {len(types_with_names)} 種財務指標可用")

def main():
    """主函數"""
    print("=" * 60)
    print("台股財務指標分析系統")
    print("=" * 60)
    
    try:
        # 初始化收集器
        collector = FinMindDataCollector(
            api_url=Config.FINMIND_API_URL,
            api_token=Config.FINMIND_API_TOKEN
        )
        
        # 分析台積電財務報表
        print("📊 正在獲取台積電(2330)財務報表...")
        df = get_financial_statements_sample(collector, "2330", "2023-01-01")
        
        if df is not None:
            # 顯示可用欄位
            show_available_financial_types(df)
            
            # 分析財務指標
            analyze_financial_metrics(df, "2330")
            
            # 展示推估方法
            demonstrate_eps_estimation()
            
            print("\n" + "=" * 60)
            print("✅ 財務指標分析完成")
            print("=" * 60)
            
            print("""
🎯 重要結論：

1. 毛利率 = (GrossProfit / Revenue) × 100%
2. 從月營收可以推估季營收
3. 結合歷史毛利率可以推估毛利
4. 但要準確推估EPS還需要：
   • 營業費用資料
   • 營業外收支
   • 所得稅率
   • 流通股數

💡 建議策略：
• 收集完整財務報表資料
• 建立歷史毛利率趨勢
• 結合月營收做季度預估
• 用多種方法交叉驗證
""")
        else:
            print("❌ 無法獲取財務報表資料")
            
    except Exception as e:
        print(f"❌ 分析失敗: {e}")

if __name__ == "__main__":
    main()

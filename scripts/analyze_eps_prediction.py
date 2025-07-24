#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPS分析和預估腳本 - 結合月營收和財務比率預估EPS
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
from loguru import logger

def init_logging():
    """初始化日誌"""
    log_dir = os.path.join(Config.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.add(
        os.path.join(log_dir, 'analyze_eps_prediction.log'),
        rotation="10 MB",
        retention="30 days",
        level="INFO"
    )

def get_stock_financial_data(db_manager, stock_id):
    """獲取股票的財務資料"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 獲取綜合損益表資料
        cursor.execute("""
            SELECT date, type, value
            FROM financial_statements 
            WHERE stock_id = ?
            AND type IN ('Revenue', 'GrossProfit', 'OperatingIncome', 'IncomeAfterTaxes', 'EPS')
            ORDER BY date DESC
        """, (stock_id,))
        
        financial_data = cursor.fetchall()
        
        # 獲取財務比率資料
        cursor.execute("""
            SELECT date, gross_margin, operating_margin, net_margin
            FROM financial_ratios 
            WHERE stock_id = ?
            ORDER BY date DESC
        """, (stock_id,))
        
        ratio_data = cursor.fetchall()
        
        # 獲取月營收資料
        cursor.execute("""
            SELECT revenue_year, revenue_month, revenue, revenue_growth_yoy
            FROM monthly_revenues 
            WHERE stock_id = ?
            ORDER BY revenue_year DESC, revenue_month DESC
            LIMIT 12
        """, (stock_id,))
        
        monthly_data = cursor.fetchall()
        
        return financial_data, ratio_data, monthly_data
        
    except Exception as e:
        logger.error(f"獲取股票 {stock_id} 財務資料失敗: {e}")
        return [], [], []
    finally:
        conn.close()

def analyze_financial_trends(financial_data, ratio_data):
    """分析財務趨勢"""
    if not financial_data or not ratio_data:
        return None
    
    # 整理財務資料
    financial_df = pd.DataFrame(financial_data, columns=['date', 'type', 'value'])
    financial_pivot = financial_df.pivot(index='date', columns='type', values='value')
    
    # 整理比率資料
    ratio_df = pd.DataFrame(ratio_data, columns=['date', 'gross_margin', 'operating_margin', 'net_margin'])
    ratio_df.set_index('date', inplace=True)
    
    # 合併資料
    combined_df = financial_pivot.join(ratio_df)
    combined_df.sort_index(ascending=False, inplace=True)
    
    return combined_df

def predict_eps_from_revenue(monthly_data, historical_ratios, target_quarter):
    """基於月營收和歷史比率預估EPS"""
    if not monthly_data or historical_ratios is None:
        return None
    
    # 計算最近3個月營收總和作為季營收
    recent_months = monthly_data[:3]
    if len(recent_months) < 3:
        return None
    
    quarterly_revenue = sum([month[2] for month in recent_months])  # 已經是千元單位
    
    # 計算歷史平均比率
    avg_gross_margin = historical_ratios['gross_margin'].mean()
    avg_operating_margin = historical_ratios['operating_margin'].mean()
    avg_net_margin = historical_ratios['net_margin'].mean()
    
    # 預估各項指標
    predicted_gross_profit = quarterly_revenue * (avg_gross_margin / 100)
    predicted_operating_income = quarterly_revenue * (avg_operating_margin / 100)
    predicted_net_income = quarterly_revenue * (avg_net_margin / 100)
    
    # 假設流通股數 (這裡需要實際的股數資料)
    # 暫時用歷史EPS和淨利推估
    if 'EPS' in historical_ratios.columns and 'IncomeAfterTaxes' in historical_ratios.columns:
        historical_eps = historical_ratios['EPS'].dropna()
        historical_net_income = historical_ratios['IncomeAfterTaxes'].dropna()
        
        if len(historical_eps) > 0 and len(historical_net_income) > 0:
            # 計算平均流通股數
            avg_shares = (historical_net_income / historical_eps).mean()
            if avg_shares > 0:
                predicted_eps = predicted_net_income / avg_shares
            else:
                predicted_eps = None
        else:
            predicted_eps = None
    else:
        predicted_eps = None
    
    return {
        'quarterly_revenue': quarterly_revenue,
        'predicted_gross_profit': predicted_gross_profit,
        'predicted_operating_income': predicted_operating_income,
        'predicted_net_income': predicted_net_income,
        'predicted_eps': predicted_eps,
        'avg_gross_margin': avg_gross_margin,
        'avg_operating_margin': avg_operating_margin,
        'avg_net_margin': avg_net_margin
    }

def analyze_stock_eps(db_manager, stock_id, stock_name):
    """分析單一股票的EPS"""
    print(f"\n📊 分析 {stock_id} ({stock_name}) EPS預估")
    print("=" * 60)
    
    # 獲取財務資料
    financial_data, ratio_data, monthly_data = get_stock_financial_data(db_manager, stock_id)
    
    if not financial_data:
        print(f"❌ {stock_id} 無財務報表資料")
        return
    
    # 分析財務趨勢
    trends_df = analyze_financial_trends(financial_data, ratio_data)
    
    if trends_df is None or trends_df.empty:
        print(f"❌ {stock_id} 無法分析財務趨勢")
        return
    
    # 顯示歷史財務表現
    print("📈 歷史財務表現 (最近4季):")
    print("-" * 60)
    
    for date in trends_df.index[:4]:
        row = trends_df.loc[date]
        revenue = row.get('Revenue', 0) / 1000000000  # 轉換為億元 (千元->億元)
        eps = row.get('EPS', 0)
        gross_margin = row.get('gross_margin', 0)
        net_margin = row.get('net_margin', 0)

        print(f"{date}: 營收 {revenue:>6.1f}億 EPS {eps:>5.2f}元 毛利率 {gross_margin:>5.1f}% 淨利率 {net_margin:>5.1f}%")
    
    # 月營收分析
    if monthly_data:
        print(f"\n📅 最近月營收表現:")
        print("-" * 60)
        
        for year, month, revenue, yoy_growth in monthly_data[:6]:
            revenue_billion = revenue / 1000000000  # 轉換為億元
            yoy_str = f"{yoy_growth:+.1f}%" if yoy_growth else "N/A"
            print(f"{year}/{month:02d}: {revenue_billion:>6.2f}億 (YoY: {yoy_str})")
    
    # EPS預估
    prediction = predict_eps_from_revenue(monthly_data, trends_df, "下季")
    
    if prediction:
        print(f"\n🎯 EPS預估 (基於最近3個月營收):")
        print("-" * 60)
        print(f"預估季營收: {prediction['quarterly_revenue']/1000000000:>8.1f} 億元")
        print(f"預估毛利率: {prediction['avg_gross_margin']:>8.1f}%")
        print(f"預估營業利益率: {prediction['avg_operating_margin']:>8.1f}%")
        print(f"預估淨利率: {prediction['avg_net_margin']:>8.1f}%")
        print(f"預估毛利: {prediction['predicted_gross_profit']/1000000000:>8.1f} 億元")
        print(f"預估營業利益: {prediction['predicted_operating_income']/1000000000:>8.1f} 億元")
        print(f"預估淨利: {prediction['predicted_net_income']/1000000000:>8.1f} 億元")
        
        if prediction['predicted_eps']:
            print(f"預估EPS: {prediction['predicted_eps']:>8.2f} 元")
        else:
            print("預估EPS: 無法計算 (缺少流通股數資料)")
    else:
        print("❌ 無法進行EPS預估 (資料不足)")
    
    # 風險提醒
    print(f"\n⚠️  預估風險提醒:")
    print("-" * 60)
    print("• 預估基於歷史平均比率，實際結果可能因市場變化而不同")
    print("• 未考慮一次性收入/支出、匯率變動等因素")
    print("• 流通股數變動會影響EPS計算")
    print("• 建議結合產業趨勢和公司公告進行綜合判斷")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='EPS分析和預估')
    parser.add_argument('--stock-id', help='指定股票代碼')
    parser.add_argument('--top', type=int, default=10, help='分析前N檔有資料的股票')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("台股EPS分析和預估系統")
    print("=" * 60)
    
    # 初始化日誌
    init_logging()
    logger.info("開始EPS分析和預估")
    
    try:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        
        if args.stock_id:
            # 分析指定股票
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT stock_name FROM stocks WHERE stock_id = ?", (args.stock_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                stock_name = result[0]
                analyze_stock_eps(db_manager, args.stock_id, stock_name)
            else:
                print(f"❌ 找不到股票 {args.stock_id}")
        else:
            # 分析有財務資料的前N檔股票
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT fs.stock_id, s.stock_name
                FROM financial_statements fs
                JOIN stocks s ON fs.stock_id = s.stock_id
                WHERE s.is_etf = 0
                ORDER BY fs.stock_id
                LIMIT ?
            """, (args.top,))
            
            stocks = cursor.fetchall()
            conn.close()
            
            if not stocks:
                print("❌ 未找到有財務資料的股票")
                return
            
            print(f"📊 分析前 {len(stocks)} 檔有財務資料的股票")
            
            for stock_id, stock_name in stocks:
                analyze_stock_eps(db_manager, stock_id, stock_name)
                print("\n" + "="*60)
        
        logger.info("EPS分析和預估完成")
        
    except Exception as e:
        error_msg = f"EPS分析和預估失敗: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()

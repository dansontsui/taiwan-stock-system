#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
潛力股評分分析系統
"""

import sys
import os
import json
import argparse
import warnings
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 隱藏 DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

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
        os.path.join(log_dir, 'analyze_potential_stocks.log'),
        rotation="10 MB",
        retention="30 days",
        level="INFO"
    )

def get_stock_comprehensive_data(db_manager, stock_id):
    """獲取股票綜合資料"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 基本資訊
        cursor.execute("SELECT stock_name, market FROM stocks WHERE stock_id = ?", (stock_id,))
        basic_info = cursor.fetchone()
        
        # 財務比率
        cursor.execute("""
            SELECT date, gross_margin, operating_margin, net_margin, debt_ratio, current_ratio
            FROM financial_ratios 
            WHERE stock_id = ?
            ORDER BY date DESC
            LIMIT 8
        """, (stock_id,))
        ratios = cursor.fetchall()
        
        # 月營收成長率
        cursor.execute("""
            SELECT revenue_year, revenue_month, revenue_growth_yoy
            FROM monthly_revenues 
            WHERE stock_id = ? AND revenue_growth_yoy IS NOT NULL
            ORDER BY revenue_year DESC, revenue_month DESC
            LIMIT 12
        """, (stock_id,))
        revenue_growth = cursor.fetchall()
        
        # 股利政策
        cursor.execute("""
            SELECT year, cash_earnings_distribution, cash_statutory_surplus
            FROM dividend_policies 
            WHERE stock_id = ? AND (cash_earnings_distribution > 0 OR cash_statutory_surplus > 0)
            ORDER BY year DESC
            LIMIT 5
        """, (stock_id,))
        dividends = cursor.fetchall()
        
        # EPS資料
        cursor.execute("""
            SELECT date, type, value
            FROM financial_statements 
            WHERE stock_id = ? AND type = 'EPS'
            ORDER BY date DESC
            LIMIT 8
        """, (stock_id,))
        eps_data = cursor.fetchall()
        
        return {
            'basic_info': basic_info,
            'ratios': ratios,
            'revenue_growth': revenue_growth,
            'dividends': dividends,
            'eps_data': eps_data
        }
        
    except Exception as e:
        logger.error(f"獲取股票 {stock_id} 綜合資料失敗: {e}")
        return None
    finally:
        conn.close()

def calculate_financial_health_score(ratios):
    """計算財務健康度評分 (0-100分)"""
    if not ratios:
        return 0, "無財務比率資料"
    
    score = 0
    details = []
    
    # 最近4季的平均值
    recent_ratios = ratios[:4]
    
    # 毛利率評分 (30分)
    gross_margins = [r[1] for r in recent_ratios if r[1] is not None]
    if gross_margins:
        avg_gross_margin = np.mean(gross_margins)
        if avg_gross_margin >= 30:
            gross_score = 30
        elif avg_gross_margin >= 20:
            gross_score = 25
        elif avg_gross_margin >= 10:
            gross_score = 20
        else:
            gross_score = 10
        score += gross_score
        details.append(f"毛利率: {avg_gross_margin:.1f}% ({gross_score}分)")
    
    # 營業利益率評分 (25分)
    operating_margins = [r[2] for r in recent_ratios if r[2] is not None]
    if operating_margins:
        avg_operating_margin = np.mean(operating_margins)
        if avg_operating_margin >= 15:
            operating_score = 25
        elif avg_operating_margin >= 10:
            operating_score = 20
        elif avg_operating_margin >= 5:
            operating_score = 15
        else:
            operating_score = 5
        score += operating_score
        details.append(f"營業利益率: {avg_operating_margin:.1f}% ({operating_score}分)")
    
    # 淨利率評分 (25分)
    net_margins = [r[3] for r in recent_ratios if r[3] is not None]
    if net_margins:
        avg_net_margin = np.mean(net_margins)
        if avg_net_margin >= 10:
            net_score = 25
        elif avg_net_margin >= 5:
            net_score = 20
        elif avg_net_margin >= 2:
            net_score = 15
        else:
            net_score = 5
        score += net_score
        details.append(f"淨利率: {avg_net_margin:.1f}% ({net_score}分)")
    
    # 負債比率評分 (20分)
    debt_ratios = [r[4] for r in recent_ratios if r[4] is not None]
    if debt_ratios:
        avg_debt_ratio = np.mean(debt_ratios)
        if avg_debt_ratio <= 30:
            debt_score = 20
        elif avg_debt_ratio <= 50:
            debt_score = 15
        elif avg_debt_ratio <= 70:
            debt_score = 10
        else:
            debt_score = 5
        score += debt_score
        details.append(f"負債比率: {avg_debt_ratio:.1f}% ({debt_score}分)")
    
    return min(score, 100), "; ".join(details)

def calculate_growth_score(revenue_growth):
    """計算成長性評分 (0-100分)"""
    if not revenue_growth:
        return 0, "無營收成長資料"
    
    # 計算最近12個月的平均年增率
    growth_rates = [r[2] for r in revenue_growth if r[2] is not None]
    
    if not growth_rates:
        return 0, "無有效成長率資料"
    
    avg_growth = np.mean(growth_rates)
    positive_months = len([g for g in growth_rates if g > 0])
    
    score = 0
    details = []
    
    # 平均成長率評分 (60分)
    if avg_growth >= 20:
        growth_score = 60
    elif avg_growth >= 10:
        growth_score = 50
    elif avg_growth >= 5:
        growth_score = 40
    elif avg_growth >= 0:
        growth_score = 30
    else:
        growth_score = 10
    
    score += growth_score
    details.append(f"平均年增率: {avg_growth:.1f}% ({growth_score}分)")
    
    # 成長穩定性評分 (40分)
    stability_ratio = positive_months / len(growth_rates)
    if stability_ratio >= 0.8:
        stability_score = 40
    elif stability_ratio >= 0.6:
        stability_score = 30
    elif stability_ratio >= 0.4:
        stability_score = 20
    else:
        stability_score = 10
    
    score += stability_score
    details.append(f"正成長月數比例: {stability_ratio:.1%} ({stability_score}分)")
    
    return min(score, 100), "; ".join(details)

def calculate_dividend_score(dividends):
    """計算配息穩定性評分 (0-100分)"""
    if not dividends:
        return 0, "無配息資料"
    
    # 計算配息穩定性
    dividend_years = len(dividends)
    total_dividends = []
    
    for year, cash_earnings, cash_statutory in dividends:
        total_dividend = (cash_earnings or 0) + (cash_statutory or 0)
        total_dividends.append(total_dividend)
    
    if not total_dividends or all(d == 0 for d in total_dividends):
        return 0, "無實際配息記錄"
    
    score = 0
    details = []
    
    # 配息連續性評分 (50分)
    consecutive_years = len([d for d in total_dividends if d > 0])
    if consecutive_years >= 5:
        continuity_score = 50
    elif consecutive_years >= 3:
        continuity_score = 40
    elif consecutive_years >= 2:
        continuity_score = 30
    else:
        continuity_score = 20
    
    score += continuity_score
    details.append(f"配息年數: {consecutive_years}年 ({continuity_score}分)")
    
    # 配息穩定性評分 (50分)
    if len(total_dividends) >= 3:
        dividend_std = np.std(total_dividends)
        dividend_mean = np.mean(total_dividends)
        
        if dividend_mean > 0:
            cv = dividend_std / dividend_mean  # 變異係數
            if cv <= 0.2:
                stability_score = 50
            elif cv <= 0.4:
                stability_score = 40
            elif cv <= 0.6:
                stability_score = 30
            else:
                stability_score = 20
        else:
            stability_score = 0
    else:
        stability_score = 25
    
    score += stability_score
    details.append(f"配息穩定性: {stability_score}分")
    
    return min(score, 100), "; ".join(details)

def calculate_overall_grade(total_score):
    """計算總體評等"""
    if total_score >= 85:
        return "A+"
    elif total_score >= 75:
        return "A"
    elif total_score >= 65:
        return "B+"
    elif total_score >= 55:
        return "B"
    elif total_score >= 45:
        return "C+"
    elif total_score >= 35:
        return "C"
    else:
        return "D"

def analyze_stock_potential(db_manager, stock_id):
    """分析單一股票潛力"""
    data = get_stock_comprehensive_data(db_manager, stock_id)
    
    if not data or not data['basic_info']:
        return None
    
    stock_name = data['basic_info'][0]
    
    # 計算各項評分
    financial_score, financial_details = calculate_financial_health_score(data['ratios'])
    growth_score, growth_details = calculate_growth_score(data['revenue_growth'])
    dividend_score, dividend_details = calculate_dividend_score(data['dividends'])
    
    # 計算總分 (加權平均)
    total_score = (financial_score * 0.4 + growth_score * 0.4 + dividend_score * 0.2)
    grade = calculate_overall_grade(total_score)
    
    # 組織評分詳情
    score_details = {
        'financial_health': {'score': financial_score, 'details': financial_details},
        'growth_potential': {'score': growth_score, 'details': growth_details},
        'dividend_stability': {'score': dividend_score, 'details': dividend_details}
    }
    
    return {
        'stock_id': stock_id,
        'stock_name': stock_name,
        'financial_health_score': financial_score,
        'growth_score': growth_score,
        'dividend_score': dividend_score,
        'total_score': total_score,
        'grade': grade,
        'score_details': json.dumps(score_details, ensure_ascii=False)
    }

def save_stock_score(db_manager, score_data):
    """儲存股票評分"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO stock_scores 
            (stock_id, analysis_date, financial_health_score, growth_score, 
             dividend_score, total_score, grade, score_details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            score_data['stock_id'],
            datetime.now().date(),
            score_data['financial_health_score'],
            score_data['growth_score'],
            score_data['dividend_score'],
            score_data['total_score'],
            score_data['grade'],
            score_data['score_details'],
            datetime.now()
        ))
        
        conn.commit()
        logger.info(f"股票 {score_data['stock_id']} 評分儲存成功")
        return True
        
    except Exception as e:
        logger.error(f"儲存股票評分失敗: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='潛力股評分分析')
    parser.add_argument('--stock-id', help='指定股票代碼')
    parser.add_argument('--top', type=int, default=20, help='分析前N檔股票')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("台股潛力股評分分析系統")
    print("=" * 60)
    
    init_logging()
    logger.info("開始潛力股評分分析")
    
    try:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        
        if args.stock_id:
            # 分析指定股票
            result = analyze_stock_potential(db_manager, args.stock_id)
            if result:
                save_stock_score(db_manager, result)
                print(f"\n {result['stock_id']} ({result['stock_name']}) 評分結果:")
                print(f"財務健康度: {result['financial_health_score']:.1f}分")
                print(f"成長潛力: {result['growth_score']:.1f}分")
                print(f"配息穩定性: {result['dividend_score']:.1f}分")
                print(f"總分: {result['total_score']:.1f}分")
                print(f"評等: {result['grade']}")
            else:
                print(f" 無法分析股票 {args.stock_id}")
        else:
            # 批次分析
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT fs.stock_id
                FROM financial_statements fs
                JOIN stocks s ON fs.stock_id = s.stock_id
                WHERE s.is_etf = 0
                AND LENGTH(s.stock_id) = 4
                ORDER BY fs.stock_id
                LIMIT ?
            """, (args.top,))
            
            stock_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not stock_ids:
                print(" 未找到有財務資料的股票")
                return
            
            print(f" 分析 {len(stock_ids)} 檔股票...")
            
            results = []
            for stock_id in stock_ids:
                result = analyze_stock_potential(db_manager, stock_id)
                if result:
                    save_stock_score(db_manager, result)
                    results.append(result)
                    print(f" {stock_id} ({result['stock_name']}) - {result['grade']} ({result['total_score']:.1f}分)")
            
            # 顯示排行榜
            if results:
                results.sort(key=lambda x: x['total_score'], reverse=True)
                print(f"\n 潛力股排行榜 (前10名):")
                print("-" * 60)
                for i, result in enumerate(results[:10], 1):
                    print(f"{i:2d}. {result['stock_id']} {result['stock_name']:<10} {result['grade']} ({result['total_score']:.1f}分)")
        
        logger.info("潛力股評分分析完成")
        
    except Exception as e:
        error_msg = f"潛力股評分分析失敗: {e}"
        print(f" {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股潛力股分析Web介面
"""

import sys
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'taiwan_stock_analysis_2025'

def get_db_manager():
    """獲取資料庫管理器"""
    return DatabaseManager(Config.DATABASE_PATH)

@app.route('/')
def index():
    """首頁 - 潛力股排行榜"""
    db_manager = get_db_manager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 獲取潛力股排行榜
        cursor.execute("""
            SELECT ss.stock_id, s.stock_name, ss.total_score, ss.grade,
                   ss.financial_health_score, ss.growth_score, ss.dividend_score,
                   ss.analysis_date
            FROM stock_scores ss
            JOIN stocks s ON ss.stock_id = s.stock_id
            ORDER BY ss.total_score DESC
            LIMIT 20
        """)
        
        top_stocks = []
        for row in cursor.fetchall():
            top_stocks.append({
                'stock_id': row[0],
                'stock_name': row[1],
                'total_score': row[2],
                'grade': row[3],
                'financial_health_score': row[4],
                'growth_score': row[5],
                'dividend_score': row[6],
                'analysis_date': row[7]
            })
        
        return render_template('index.html', top_stocks=top_stocks)
        
    except Exception as e:
        return f"資料庫錯誤: {e}"
    finally:
        conn.close()

@app.route('/stock/<stock_id>')
def stock_detail(stock_id):
    """股票詳細分析頁面"""
    db_manager = get_db_manager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 基本資訊
        cursor.execute("SELECT stock_name, market FROM stocks WHERE stock_id = ?", (stock_id,))
        basic_info = cursor.fetchone()
        
        if not basic_info:
            return "股票不存在"
        
        # 評分資訊
        cursor.execute("""
            SELECT total_score, grade, financial_health_score, growth_score, 
                   dividend_score, score_details, analysis_date
            FROM stock_scores 
            WHERE stock_id = ?
            ORDER BY analysis_date DESC
            LIMIT 1
        """, (stock_id,))
        
        score_info = cursor.fetchone()
        
        # 財務比率
        cursor.execute("""
            SELECT date, gross_margin, operating_margin, net_margin, debt_ratio, current_ratio
            FROM financial_ratios 
            WHERE stock_id = ?
            ORDER BY date DESC
            LIMIT 8
        """, (stock_id,))
        
        financial_ratios = cursor.fetchall()
        
        # 月營收成長
        cursor.execute("""
            SELECT revenue_year, revenue_month, revenue, revenue_growth_yoy
            FROM monthly_revenues 
            WHERE stock_id = ?
            ORDER BY revenue_year DESC, revenue_month DESC
            LIMIT 12
        """, (stock_id,))
        
        monthly_revenue = cursor.fetchall()
        
        # 股利政策
        cursor.execute("""
            SELECT year, cash_earnings_distribution, cash_statutory_surplus,
                   cash_ex_dividend_trading_date
            FROM dividend_policies 
            WHERE stock_id = ?
            ORDER BY year DESC
            LIMIT 5
        """, (stock_id,))
        
        dividend_data = cursor.fetchall()
        
        # EPS預估 (使用之前的邏輯)
        eps_prediction = predict_eps_for_web(cursor, stock_id, monthly_revenue, financial_ratios)
        
        stock_data = {
            'stock_id': stock_id,
            'stock_name': basic_info[0],
            'market': basic_info[1],
            'score_info': score_info,
            'financial_ratios': financial_ratios,
            'monthly_revenue': monthly_revenue,
            'dividend_data': dividend_data,
            'eps_prediction': eps_prediction
        }
        
        return render_template('stock_detail.html', stock=stock_data)
        
    except Exception as e:
        return f"資料庫錯誤: {e}"
    finally:
        conn.close()

def predict_eps_for_web(cursor, stock_id, monthly_revenue, financial_ratios):
    """為Web介面預估EPS"""
    if not monthly_revenue or len(monthly_revenue) < 3:
        return None
    
    try:
        # 最近3個月營收
        recent_revenue = sum([row[2] for row in monthly_revenue[:3]])
        
        # 計算歷史平均淨利率
        net_margins = [row[3] for row in financial_ratios if row[3] is not None]
        if not net_margins:
            return None
        
        avg_net_margin = sum(net_margins) / len(net_margins)
        
        # 預估淨利
        predicted_net_income = recent_revenue * (avg_net_margin / 100)
        
        # 獲取歷史EPS來推估股數
        cursor.execute("""
            SELECT value FROM financial_statements 
            WHERE stock_id = ? AND type = 'EPS' AND value > 0
            ORDER BY date DESC LIMIT 4
        """, (stock_id,))
        
        eps_history = [row[0] for row in cursor.fetchall()]
        
        if eps_history:
            # 使用歷史EPS推估股數
            cursor.execute("""
                SELECT value FROM financial_statements 
                WHERE stock_id = ? AND type = 'IncomeAfterTaxes'
                ORDER BY date DESC LIMIT 4
            """, (stock_id,))
            
            net_income_history = [row[0] for row in cursor.fetchall()]
            
            if net_income_history and len(eps_history) == len(net_income_history):
                avg_shares = sum([ni/eps for ni, eps in zip(net_income_history, eps_history) if eps > 0]) / len(eps_history)
                predicted_eps = predicted_net_income / avg_shares if avg_shares > 0 else None
            else:
                predicted_eps = None
        else:
            predicted_eps = None
        
        return {
            'quarterly_revenue': recent_revenue / 1000000000,  # 轉換為億元
            'avg_net_margin': avg_net_margin,
            'predicted_net_income': predicted_net_income / 1000000000,  # 轉換為億元
            'predicted_eps': predicted_eps
        }
        
    except Exception as e:
        return None

@app.route('/api/stocks')
def api_stocks():
    """API: 獲取股票清單"""
    db_manager = get_db_manager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT s.stock_id, s.stock_name, ss.total_score, ss.grade
            FROM stocks s
            LEFT JOIN stock_scores ss ON s.stock_id = ss.stock_id
            WHERE s.is_etf = 0 AND LENGTH(s.stock_id) = 4
            ORDER BY ss.total_score DESC NULLS LAST
            LIMIT 50
        """)
        
        stocks = []
        for row in cursor.fetchall():
            stocks.append({
                'stock_id': row[0],
                'stock_name': row[1],
                'total_score': row[2],
                'grade': row[3]
            })
        
        return jsonify(stocks)
        
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conn.close()

if __name__ == '__main__':
    # 確保templates目錄存在
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    print("🌐 啟動台股潛力股分析Web服務...")
    print("📊 訪問地址: http://localhost:8080")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=8080)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股歷史股價系統簡單演示
"""

import sys
import os
from datetime import datetime, timedelta

# 添加專案根目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager
from app.services.query_service import StockQueryService

def format_number(num):
    """格式化數字"""
    if num is None:
        return "N/A"
    
    if abs(num) >= 1e8:
        return f"{num/1e8:.2f}億"
    elif abs(num) >= 1e4:
        return f"{num/1e4:.2f}萬"
    else:
        return f"{num:,.0f}"

def show_system_info(query_service):
    """顯示系統資訊"""
    print("=" * 60)
    print("系統資訊")
    print("=" * 60)
    
    stats = query_service.get_database_stats()
    
    print(f"股票數量: {stats.get('stocks_count', 0):,}")
    print(f"股價記錄: {format_number(stats.get('stock_prices_count', 0))}")
    print(f"配息記錄: {stats.get('etf_dividends_count', 0):,}")
    print(f"資料庫大小: {stats.get('database_size', 'N/A')}")
    
    if 'earliest_date' in stats and 'latest_date' in stats:
        print(f"資料範圍: {stats['earliest_date']} ~ {stats['latest_date']}")

def show_market_overview(query_service):
    """顯示市場總覽"""
    print("\n" + "=" * 60)
    print("市場總覽")
    print("=" * 60)
    
    market_summary = query_service.get_market_summary()
    
    if not market_summary:
        print("暫無市場資料")
        return
    
    latest_date = market_summary.get('latest_date', 'N/A')
    summary = market_summary.get('summary', {})
    
    print(f"最新交易日: {latest_date}")
    print(f"總股票數: {summary.get('total_stocks', 0)}")
    print(f"上漲股票: {summary.get('up_stocks', 0)}")
    print(f"下跌股票: {summary.get('down_stocks', 0)}")
    print(f"平盤股票: {summary.get('flat_stocks', 0)}")
    print(f"總成交量: {format_number(summary.get('total_volume', 0))}")
    print(f"總成交金額: {format_number(summary.get('total_trading_money', 0))}")

def show_stock_rankings(query_service):
    """顯示股票排行"""
    print("\n" + "=" * 60)
    print("今日漲幅排行 TOP 10")
    print("=" * 60)
    
    gainers = query_service.get_top_performers(limit=10, performance_type='gain')
    
    if gainers:
        print(f"{'排名':<4} {'代碼':<8} {'名稱':<12} {'收盤價':<8} {'漲跌':<8} {'漲跌幅':<8}")
        print("-" * 65)
        
        for i, stock in enumerate(gainers, 1):
            change_pct = stock.get('change_percent', 0) or 0
            spread = stock.get('spread', 0) or 0
            close_price = stock.get('close_price', 0) or 0
            print(f"{i:<4} {stock['stock_id']:<8} {stock['stock_name'][:10]:<12} "
                  f"{close_price:<8.2f} {spread:+.2f}{'':>4} {change_pct:+.2f}%")
    else:
        print("暫無資料")
    
    print("\n" + "=" * 60)
    print("今日跌幅排行 TOP 10")
    print("=" * 60)
    
    losers = query_service.get_top_performers(limit=10, performance_type='loss')
    
    if losers:
        print(f"{'排名':<4} {'代碼':<8} {'名稱':<12} {'收盤價':<8} {'漲跌':<8} {'漲跌幅':<8}")
        print("-" * 65)
        
        for i, stock in enumerate(losers, 1):
            change_pct = stock.get('change_percent', 0) or 0
            spread = stock.get('spread', 0) or 0
            close_price = stock.get('close_price', 0) or 0
            print(f"{i:<4} {stock['stock_id']:<8} {stock['stock_name'][:10]:<12} "
                  f"{close_price:<8.2f} {spread:+.2f}{'':>4} {change_pct:+.2f}%")
    else:
        print("暫無資料")

def show_volume_leaders(query_service):
    """顯示成交量排行"""
    print("\n" + "=" * 60)
    print("成交量排行 TOP 10")
    print("=" * 60)
    
    volume_leaders = query_service.get_volume_leaders(limit=10)
    
    if volume_leaders:
        print(f"{'排名':<4} {'代碼':<8} {'名稱':<12} {'收盤價':<8} {'成交量':<12}")
        print("-" * 55)
        
        for i, stock in enumerate(volume_leaders, 1):
            close_price = stock.get('close_price', 0) or 0
            volume = stock.get('volume', 0) or 0
            print(f"{i:<4} {stock['stock_id']:<8} {stock['stock_name'][:10]:<12} "
                  f"{close_price:<8.2f} {format_number(volume):<12}")
    else:
        print("暫無資料")

def show_stock_detail(query_service, stock_id):
    """顯示股票詳細資訊"""
    print(f"\n" + "=" * 60)
    print(f"股票詳細資訊: {stock_id}")
    print("=" * 60)
    
    # 基本資訊
    stock_info = query_service.get_stock_info(stock_id)
    if not stock_info:
        print("找不到該股票")
        return
    
    print(f"股票名稱: {stock_info['stock_name']}")
    print(f"市場: {stock_info['market']}")
    print(f"是否為ETF: {'是' if stock_info['is_etf'] else '否'}")
    
    # 最新價格
    latest_price = query_service.get_latest_price(stock_id)
    if latest_price:
        print(f"\n最新價格資訊 ({latest_price['date']}):")
        print(f"開盤價: {latest_price.get('open_price', 0) or 0:.2f}")
        print(f"最高價: {latest_price.get('high_price', 0) or 0:.2f}")
        print(f"最低價: {latest_price.get('low_price', 0) or 0:.2f}")
        print(f"收盤價: {latest_price.get('close_price', 0) or 0:.2f}")
        spread = latest_price.get('spread', 0) or 0
        print(f"漲跌: {spread:+.2f}")
        print(f"成交量: {format_number(latest_price.get('volume', 0) or 0)}")
        if latest_price.get('trading_money'):
            print(f"成交金額: {format_number(latest_price['trading_money'])}")
    
    # 價格統計
    price_range = query_service.get_price_range(stock_id, days=30)
    if price_range:
        print(f"\n近30日統計:")
        print(f"最高價: {price_range.get('max_price', 0) or 0:.2f}")
        print(f"最低價: {price_range.get('min_price', 0) or 0:.2f}")
        print(f"平均價: {price_range.get('avg_price', 0) or 0:.2f}")
        print(f"總成交量: {format_number(price_range.get('total_volume', 0) or 0)}")
        print(f"交易天數: {price_range.get('trading_days', 0) or 0}")
    
    # 如果是ETF，顯示配息資訊
    if stock_info['is_etf']:
        dividends = query_service.get_etf_dividends(stock_id)
        if dividends:
            print(f"\n配息記錄 (最近5筆):")
            print(f"{'公告日期':<12} {'配息金額':<10} {'除息日':<12} {'發放日':<12}")
            print("-" * 50)
            
            for dividend in dividends[:5]:
                announce_date = dividend['announce_date']
                cash_dividend = dividend.get('cash_dividend', 0)
                ex_date = dividend.get('ex_dividend_date', 'N/A')
                pay_date = dividend.get('payment_date', 'N/A')
                
                print(f"{announce_date:<12} {cash_dividend:<10.3f} {ex_date:<12} {pay_date:<12}")

def interactive_demo(query_service):
    """互動式演示"""
    print("\n" + "=" * 60)
    print("互動式查詢")
    print("=" * 60)
    print("輸入股票代碼查詢詳細資訊 (輸入 'quit' 結束)")
    
    while True:
        try:
            stock_id = input("\n請輸入股票代碼: ").strip().upper()
            
            if stock_id.lower() == 'quit':
                break
            
            if not stock_id:
                continue
            
            show_stock_detail(query_service, stock_id)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"查詢錯誤: {e}")

def main():
    """主函數"""
    print("=" * 60)
    print("台股歷史股價系統 - 簡單演示")
    print("=" * 60)
    
    try:
        # 初始化服務
        db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
        query_service = StockQueryService(db_manager)
        
        # 顯示系統資訊
        show_system_info(query_service)
        
        # 顯示市場總覽
        show_market_overview(query_service)
        
        # 顯示排行榜
        show_stock_rankings(query_service)
        
        # 顯示成交量排行
        show_volume_leaders(query_service)
        
        # 顯示幾檔重點股票
        important_stocks = ['2330', '0050', '0056']
        for stock_id in important_stocks:
            show_stock_detail(query_service, stock_id)
        
        # 互動式查詢
        interactive_demo(query_service)
        
        print("\n" + "=" * 60)
        print("感謝使用台股歷史股價系統！")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] 系統錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

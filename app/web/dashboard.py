#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 儀表板
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# 添加專案根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager
from app.services.query_service import StockQueryService

# 頁面配置
st.set_page_config(
    page_title="台股歷史股價系統",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def init_services():
    """初始化服務"""
    db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
    query_service = StockQueryService(db_manager)
    return db_manager, query_service

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

def create_candlestick_chart(df, title):
    """建立K線圖"""
    fig = go.Figure(data=go.Candlestick(
        x=df['date'],
        open=df['open_price'],
        high=df['high_price'],
        low=df['low_price'],
        close=df['close_price'],
        name="K線"
    ))
    
    fig.update_layout(
        title=title,
        yaxis_title="價格 (元)",
        xaxis_title="日期",
        template="plotly_white",
        height=400
    )
    
    return fig

def create_volume_chart(df):
    """建立成交量圖"""
    colors = ['red' if close < open else 'green' 
              for close, open in zip(df['close_price'], df['open_price'])]
    
    fig = go.Figure(data=go.Bar(
        x=df['date'],
        y=df['volume'],
        marker_color=colors,
        name="成交量"
    ))
    
    fig.update_layout(
        title="成交量",
        yaxis_title="成交量 (股)",
        xaxis_title="日期",
        template="plotly_white",
        height=200
    )
    
    return fig

def main():
    """主函數"""
    st.title("📈 台股歷史股價系統")
    st.markdown("---")
    
    # 初始化服務
    try:
        db_manager, query_service = init_services()
    except Exception as e:
        st.error(f"系統初始化失敗: {e}")
        st.stop()
    
    # 側邊欄
    st.sidebar.title("功能選單")
    
    # 主要功能選擇
    main_function = st.sidebar.selectbox(
        "選擇功能",
        ["市場總覽", "股票查詢", "股價圖表", "排行榜", "系統狀態"]
    )
    
    if main_function == "市場總覽":
        show_market_overview(query_service)
    elif main_function == "股票查詢":
        show_stock_search(query_service)
    elif main_function == "股價圖表":
        show_stock_charts(query_service)
    elif main_function == "排行榜":
        show_rankings(query_service)
    elif main_function == "系統狀態":
        show_system_status(query_service)

def show_market_overview(query_service):
    """顯示市場總覽"""
    st.header("🏢 市場總覽")
    
    # 取得市場摘要
    market_summary = query_service.get_market_summary()
    
    if not market_summary:
        st.warning("暫無市場資料")
        return
    
    latest_date = market_summary.get('latest_date', 'N/A')
    summary = market_summary.get('summary', {})
    
    st.subheader(f"📅 最新交易日: {latest_date}")
    
    # 市場統計
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總股票數", summary.get('total_stocks', 0))
    
    with col2:
        up_stocks = summary.get('up_stocks', 0)
        down_stocks = summary.get('down_stocks', 0)
        if up_stocks + down_stocks > 0:
            up_ratio = up_stocks / (up_stocks + down_stocks) * 100
            st.metric("上漲股票", f"{up_stocks} ({up_ratio:.1f}%)")
        else:
            st.metric("上漲股票", up_stocks)
    
    with col3:
        st.metric("下跌股票", summary.get('down_stocks', 0))
    
    with col4:
        st.metric("平盤股票", summary.get('flat_stocks', 0))
    
    # 成交統計
    st.subheader("💰 成交統計")
    col1, col2 = st.columns(2)
    
    with col1:
        total_volume = summary.get('total_volume', 0)
        st.metric("總成交量", format_number(total_volume))
    
    with col2:
        total_money = summary.get('total_trading_money', 0)
        st.metric("總成交金額", format_number(total_money))

def show_stock_search(query_service):
    """顯示股票搜尋"""
    st.header("🔍 股票搜尋")
    
    # 搜尋框
    search_term = st.text_input("輸入股票代碼或名稱", placeholder="例如: 2330 或 台積電")
    
    if search_term:
        # 搜尋股票
        results = query_service.search_stocks(search_term)
        
        if results:
            st.subheader(f"搜尋結果 ({len(results)} 檔)")
            
            # 轉換為 DataFrame
            df = pd.DataFrame(results)
            
            # 取得最新價格
            stock_ids = df['stock_id'].tolist()
            latest_prices = query_service.get_multiple_latest_prices(stock_ids)
            
            if latest_prices:
                price_df = pd.DataFrame(latest_prices)
                
                # 合併資料
                merged_df = df.merge(
                    price_df[['stock_id', 'close_price', 'spread', 'volume', 'date']], 
                    on='stock_id', 
                    how='left'
                )
                
                # 顯示表格
                display_columns = ['stock_id', 'stock_name', 'market', 'close_price', 'spread', 'volume', 'date']
                display_df = merged_df[display_columns].copy()
                
                # 重命名欄位
                display_df.columns = ['代碼', '名稱', '市場', '收盤價', '漲跌', '成交量', '日期']
                
                # 格式化數值
                if '成交量' in display_df.columns:
                    display_df['成交量'] = display_df['成交量'].apply(lambda x: format_number(x) if pd.notna(x) else 'N/A')
                
                st.dataframe(display_df, use_container_width=True)
            else:
                st.dataframe(df[['stock_id', 'stock_name', 'market', 'is_etf']], use_container_width=True)
        else:
            st.info("未找到相關股票")

def show_stock_charts(query_service):
    """顯示股價圖表"""
    st.header("📊 股價圖表")
    
    # 股票選擇
    col1, col2 = st.columns([2, 1])
    
    with col1:
        stock_id = st.text_input("股票代碼", placeholder="例如: 2330")
    
    with col2:
        days = st.selectbox("顯示天數", [30, 60, 90, 180, 252], index=2)
    
    if stock_id:
        # 取得股票資訊
        stock_info = query_service.get_stock_info(stock_id)
        
        if not stock_info:
            st.error("找不到該股票")
            return
        
        st.subheader(f"{stock_info['stock_name']} ({stock_id})")
        
        # 取得股價資料
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        prices = query_service.get_stock_prices(
            stock_id, 
            start_date.isoformat(), 
            end_date.isoformat()
        )
        
        if prices:
            df = pd.DataFrame(prices)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 顯示最新價格資訊
            latest = df.iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("最新價格", f"{latest['close_price']:.2f}")
            with col2:
                change = latest['spread']
                change_pct = (change / (latest['close_price'] - change)) * 100 if latest['close_price'] != change else 0
                st.metric("漲跌", f"{change:+.2f}", f"{change_pct:+.2f}%")
            with col3:
                st.metric("成交量", format_number(latest['volume']))
            with col4:
                st.metric("日期", latest['date'].strftime('%Y-%m-%d'))
            
            # K線圖
            candlestick_fig = create_candlestick_chart(df, f"{stock_info['stock_name']} K線圖")
            st.plotly_chart(candlestick_fig, use_container_width=True)
            
            # 成交量圖
            volume_fig = create_volume_chart(df)
            st.plotly_chart(volume_fig, use_container_width=True)
            
            # 價格統計
            st.subheader("📈 價格統計")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("最高價", f"{df['high_price'].max():.2f}")
            with col2:
                st.metric("最低價", f"{df['low_price'].min():.2f}")
            with col3:
                st.metric("平均價", f"{df['close_price'].mean():.2f}")
            with col4:
                st.metric("總成交量", format_number(df['volume'].sum()))
        else:
            st.warning("該股票暫無價格資料")

def show_rankings(query_service):
    """顯示排行榜"""
    st.header("🏆 股票排行榜")
    
    tab1, tab2, tab3 = st.tabs(["漲幅排行", "跌幅排行", "成交量排行"])
    
    with tab1:
        st.subheader("📈 今日漲幅排行")
        gainers = query_service.get_top_performers(limit=20, performance_type='gain')
        
        if gainers:
            df = pd.DataFrame(gainers)
            display_df = df[['stock_id', 'stock_name', 'close_price', 'spread', 'change_percent', 'volume']].copy()
            display_df.columns = ['代碼', '名稱', '收盤價', '漲跌', '漲跌幅(%)', '成交量']
            display_df['成交量'] = display_df['成交量'].apply(format_number)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("暫無資料")
    
    with tab2:
        st.subheader("📉 今日跌幅排行")
        losers = query_service.get_top_performers(limit=20, performance_type='loss')
        
        if losers:
            df = pd.DataFrame(losers)
            display_df = df[['stock_id', 'stock_name', 'close_price', 'spread', 'change_percent', 'volume']].copy()
            display_df.columns = ['代碼', '名稱', '收盤價', '漲跌', '漲跌幅(%)', '成交量']
            display_df['成交量'] = display_df['成交量'].apply(format_number)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("暫無資料")
    
    with tab3:
        st.subheader("💹 成交量排行")
        volume_leaders = query_service.get_volume_leaders(limit=20)
        
        if volume_leaders:
            df = pd.DataFrame(volume_leaders)
            display_df = df[['stock_id', 'stock_name', 'close_price', 'spread', 'volume']].copy()
            display_df.columns = ['代碼', '名稱', '收盤價', '漲跌', '成交量']
            display_df['成交量'] = display_df['成交量'].apply(format_number)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("暫無資料")

def show_system_status(query_service):
    """顯示系統狀態"""
    st.header("⚙️ 系統狀態")
    
    # 資料庫統計
    stats = query_service.get_database_stats()
    
    st.subheader("📊 資料庫統計")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("股票數量", stats.get('stocks_count', 0))
    
    with col2:
        st.metric("股價記錄", format_number(stats.get('stock_prices_count', 0)))
    
    with col3:
        st.metric("配息記錄", stats.get('etf_dividends_count', 0))
    
    with col4:
        st.metric("資料庫大小", stats.get('database_size', 'N/A'))
    
    # 資料日期範圍
    if 'earliest_date' in stats and 'latest_date' in stats:
        st.subheader("📅 資料範圍")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("最早日期", stats['earliest_date'])
        
        with col2:
            st.metric("最新日期", stats['latest_date'])
    
    # 更新狀態
    st.subheader("🔄 最近更新狀態")
    update_status = query_service.get_data_update_status()
    
    if update_status:
        df = pd.DataFrame(update_status[:10])  # 只顯示最近10筆
        display_df = df[['stock_id', 'update_type', 'last_update_date', 'status']].copy()
        display_df.columns = ['股票代碼', '更新類型', '更新日期', '狀態']
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("暫無更新記錄")

if __name__ == "__main__":
    main()

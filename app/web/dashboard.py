#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 儀表板
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

def create_volume_chart(df, title="成交量"):
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
        title=title,
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
    st.sidebar.title("🎯 功能選單")

    # 初始化 session state
    if 'selected_function' not in st.session_state:
        st.session_state.selected_function = "市場總覽"

    # 主要功能選擇 - 使用按鈕
    st.sidebar.markdown("### 📊 主要功能")

    functions = [
        ("📈", "市場總覽", "整體市場狀況"),
        ("🔍", "股票分析", "完整個股分析"),
        ("🏆", "排行榜", "漲跌幅排行"),
        ("🎯", "潛力股分析", "智能評分系統"),
        ("📊", "資料庫狀態", "資料收集進度"),
        ("⚙️", "系統狀態", "系統運行狀況")
    ]

    for icon, func_name, description in functions:
        # 判斷是否為當前選中的功能
        is_selected = st.session_state.selected_function == func_name

        # 使用不同的樣式顯示按鈕
        if is_selected:
            st.sidebar.markdown(f"""
            <div style="
                background-color: #0066cc;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin: 5px 0;
                text-align: center;
                font-weight: bold;
            ">
                {icon} {func_name}<br>
                <small style="opacity: 0.8;">{description}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.sidebar.button(f"{icon} {func_name}", key=f"btn_{func_name}", help=description, use_container_width=True):
                st.session_state.selected_function = func_name
                st.rerun()

    main_function = st.session_state.selected_function
    
    if main_function == "市場總覽":
        show_market_overview(query_service)
    elif main_function == "股票分析":
        show_stock_analysis(db_manager, query_service)
    elif main_function == "排行榜":
        show_rankings(query_service)
    elif main_function == "潛力股分析":
        display_potential_analysis_page(db_manager, query_service)
    elif main_function == "資料庫狀態":
        show_database_status(db_manager, query_service)
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
        st.write("📅 顯示期間")

        # 初始化 session state for days
        if 'selected_days' not in st.session_state:
            st.session_state.selected_days = 90

        # 使用按鈕選擇天數
        day_options = [
            (30, "1個月"),
            (60, "2個月"),
            (90, "3個月"),
            (180, "6個月"),
            (252, "1年")
        ]

        cols = st.columns(len(day_options))
        for i, (day_value, day_label) in enumerate(day_options):
            with cols[i]:
                is_selected = st.session_state.selected_days == day_value
                if is_selected:
                    st.markdown(f"""
                    <div style="
                        background-color: #0066cc;
                        color: white;
                        padding: 5px;
                        border-radius: 3px;
                        text-align: center;
                        font-size: 12px;
                        font-weight: bold;
                    ">
                        {day_label}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    if st.button(day_label, key=f"days_{day_value}", use_container_width=True):
                        st.session_state.selected_days = day_value
                        st.rerun()

        days = st.session_state.selected_days
    
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
            volume_fig = create_volume_chart(df, f"{stock_info['stock_name']} 成交量")
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

            # 潛力股分析
            st.subheader("🎯 潛力股分析")

            # 獲取潛力評分
            potential_score = get_stock_potential_score(query_service.db, stock_id)

            if potential_score:
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    grade_color = {
                        'A+': '🟢', 'A': '🟢', 'B+': '🔵', 'B': '🔵',
                        'C+': '🟡', 'C': '🟡', 'D': '🔴'
                    }.get(potential_score['grade'], '⚪')
                    st.metric("評等", f"{grade_color} {potential_score['grade']}")

                with col2:
                    st.metric("總分", f"{potential_score['total_score']:.1f}")

                with col3:
                    st.metric("財務健康", f"{potential_score['financial_health_score']:.0f}")

                with col4:
                    st.metric("成長潛力", f"{potential_score['growth_score']:.0f}")

                with col5:
                    st.metric("配息穩定", f"{potential_score['dividend_score']:.0f}")

                # EPS預估
                eps_prediction = get_eps_prediction(query_service.db, stock_id)

                if eps_prediction:
                    st.subheader("💰 EPS預估")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("預估季營收", f"{eps_prediction['quarterly_revenue']:.1f}億")

                    with col2:
                        st.metric("平均淨利率", f"{eps_prediction['avg_net_margin']:.1f}%")

                    with col3:
                        st.metric("預估淨利", f"{eps_prediction['predicted_net_income']:.1f}億")

                    with col4:
                        if eps_prediction['predicted_eps']:
                            st.metric("預估EPS", f"{eps_prediction['predicted_eps']:.2f}元")
                        else:
                            st.metric("預估EPS", "N/A")

                    st.info("💡 EPS預估基於最近3個月營收和歷史平均淨利率，僅供參考")

            else:
                st.info("該股票暫無潛力分析資料，請先執行潛力股分析")

                if st.button(f"🚀 分析 {stock_id} 潛力"):
                    with st.spinner("正在分析..."):
                        import subprocess
                        try:
                            result = subprocess.run([
                                "python", "scripts/analyze_potential_stocks.py",
                                "--stock-id", stock_id
                            ], capture_output=True, text=True, cwd=".")

                            if result.returncode == 0:
                                st.success("分析完成！請重新整理頁面查看結果。")
                                st.experimental_rerun()
                            else:
                                st.error(f"分析失敗: {result.stderr}")
                        except Exception as e:
                            st.error(f"執行分析失敗: {e}")
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
    
    # 每日更新狀態
    st.subheader("📅 每日更新狀態")
    show_daily_update_status(query_service)

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

def show_daily_update_status(query_service):
    """顯示每日更新狀態"""
    try:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # 獲取資料庫連接
        conn = query_service.db.get_connection()
        cursor = conn.cursor()

        # 檢查今日和昨日的股價資料
        cursor.execute("""
            SELECT COUNT(*) FROM stock_prices
            WHERE date = ?
        """, (today.isoformat(),))
        today_prices = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM stock_prices
            WHERE date = ?
        """, (yesterday.isoformat(),))
        yesterday_prices = cursor.fetchone()[0]

        conn.close()

        # 檢查每日更新日誌
        daily_log_path = Path("logs/collect_daily_update.log")
        last_daily_update = "未執行"
        last_update_status = "⚠️"

        if daily_log_path.exists():
            try:
                with open(daily_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if "每日增量收集成功完成" in line:
                            # 提取時間戳
                            time_part = line.split('|')[0].strip()
                            last_daily_update = time_part
                            last_update_status = "✅"
                            break
                        elif "每日增量收集執行失敗" in line:
                            time_part = line.split('|')[0].strip()
                            last_daily_update = f"{time_part} (失敗)"
                            last_update_status = "❌"
                            break
            except Exception:
                pass

        # 顯示狀態
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("今日股價資料", f"{today_prices:,}筆")

        with col2:
            st.metric("昨日股價資料", f"{yesterday_prices:,}筆")

        with col3:
            st.metric("最後每日更新", last_update_status)
            st.caption(last_daily_update)

        with col4:
            # 執行每日更新按鈕
            if st.button("🚀 執行每日更新", key="daily_update_btn"):
                with st.spinner("正在執行每日更新..."):
                    import subprocess
                    try:
                        result = subprocess.run([
                            "python", "scripts/collect_daily_update.py",
                            "--batch-size", "5"
                        ], capture_output=True, text=True, cwd=".")

                        if result.returncode == 0:
                            st.success("每日更新執行成功！")
                            st.rerun()
                        else:
                            st.error(f"每日更新執行失敗: {result.stderr}")
                    except Exception as e:
                        st.error(f"執行每日更新失敗: {e}")

        # 建議和提示
        if today_prices == 0 and yesterday_prices > 0:
            st.warning("💡 建議執行每日更新以獲取最新資料")
        elif today_prices > 0:
            st.success("✅ 今日資料已更新")
        else:
            st.info("⚠️ 請檢查資料收集狀況")

    except Exception as e:
        st.error(f"載入每日更新狀態失敗: {e}")

def get_stock_potential_score(db_manager, stock_id):
    """獲取股票潛力評分"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT total_score, grade, financial_health_score, growth_score,
                   dividend_score, score_details, analysis_date
            FROM stock_scores
            WHERE stock_id = ?
            ORDER BY analysis_date DESC
            LIMIT 1
        """, (stock_id,))

        result = cursor.fetchone()
        if result:
            return {
                'total_score': result[0],
                'grade': result[1],
                'financial_health_score': result[2],
                'growth_score': result[3],
                'dividend_score': result[4],
                'score_details': result[5],
                'analysis_date': result[6]
            }
        return None
    except Exception as e:
        st.error(f"獲取潛力評分失敗: {e}")
        return None
    finally:
        conn.close()

def get_eps_prediction(db_manager, stock_id):
    """獲取EPS預估"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        # 獲取最近3個月營收
        cursor.execute("""
            SELECT revenue_year, revenue_month, revenue
            FROM monthly_revenues
            WHERE stock_id = ?
            ORDER BY revenue_year DESC, revenue_month DESC
            LIMIT 3
        """, (stock_id,))

        monthly_revenue = cursor.fetchall()

        if len(monthly_revenue) < 3:
            return None

        # 計算季營收
        quarterly_revenue = sum([row[2] for row in monthly_revenue])

        # 獲取歷史平均淨利率
        cursor.execute("""
            SELECT net_margin FROM financial_ratios
            WHERE stock_id = ? AND net_margin IS NOT NULL
            ORDER BY date DESC LIMIT 4
        """, (stock_id,))

        net_margins = [row[0] for row in cursor.fetchall()]

        if not net_margins:
            return None

        avg_net_margin = sum(net_margins) / len(net_margins)
        predicted_net_income = quarterly_revenue * (avg_net_margin / 100)

        # 嘗試預估EPS
        cursor.execute("""
            SELECT fs1.value as net_income, fs2.value as eps
            FROM financial_statements fs1
            JOIN financial_statements fs2 ON fs1.stock_id = fs2.stock_id AND fs1.date = fs2.date
            WHERE fs1.stock_id = ? AND fs1.type = 'IncomeAfterTaxes' AND fs2.type = 'EPS'
            AND fs2.value > 0
            ORDER BY fs1.date DESC LIMIT 4
        """, (stock_id,))

        eps_data = cursor.fetchall()

        predicted_eps = None
        if eps_data:
            avg_shares = sum([row[0]/row[1] for row in eps_data]) / len(eps_data)
            if avg_shares > 0:
                predicted_eps = predicted_net_income / avg_shares

        return {
            'quarterly_revenue': quarterly_revenue / 1000000000,  # 轉億元
            'avg_net_margin': avg_net_margin,
            'predicted_net_income': predicted_net_income / 1000000000,  # 轉億元
            'predicted_eps': predicted_eps
        }

    except Exception as e:
        st.error(f"EPS預估失敗: {e}")
        return None
    finally:
        conn.close()

def display_potential_analysis_page(db_manager, query_service):
    """顯示潛力股分析頁面"""
    st.header("🏆 潛力股分析")

    # 獲取潛力股排行榜
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT ss.stock_id, s.stock_name, ss.total_score, ss.grade,
                   ss.financial_health_score, ss.growth_score, ss.dividend_score,
                   ss.analysis_date
            FROM stock_scores ss
            JOIN stocks s ON ss.stock_id = s.stock_id
            ORDER BY ss.total_score DESC
            LIMIT 20
        """)

        potential_stocks = cursor.fetchall()

        if potential_stocks:
            st.subheader("📊 潛力股排行榜")

            # 創建DataFrame
            df = pd.DataFrame(potential_stocks, columns=[
                '股票代碼', '股票名稱', '總分', '評等',
                '財務健康', '成長潛力', '配息穩定', '分析日期'
            ])

            # 格式化顯示
            df['總分'] = df['總分'].round(1)
            df['財務健康'] = df['財務健康'].round(0).astype(int)
            df['成長潛力'] = df['成長潛力'].round(0).astype(int)
            df['配息穩定'] = df['配息穩定'].round(0).astype(int)

            # 顯示表格
            st.dataframe(df, use_container_width=True)

            # 統計資訊
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("已分析股票", len(df))

            with col2:
                a_grade_count = len(df[df['評等'].isin(['A+', 'A'])])
                st.metric("A級股票", a_grade_count)

            with col3:
                avg_score = df['總分'].mean()
                st.metric("平均分數", f"{avg_score:.1f}")

            with col4:
                top_score = df['總分'].max()
                st.metric("最高分數", f"{top_score:.1f}")

            # 評分分布圖
            st.subheader("📈 評分分布")

            fig = px.histogram(df, x='總分', nbins=20,
                             title="潛力股評分分布",
                             labels={'總分': '總分', 'count': '股票數量'})
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("暫無潛力股分析資料，請先執行潛力股分析腳本")

            if st.button("🚀 執行潛力股分析"):
                with st.spinner("正在分析潛力股..."):
                    import subprocess
                    try:
                        result = subprocess.run([
                            "python", "scripts/analyze_potential_stocks.py", "--top", "20"
                        ], capture_output=True, text=True, cwd=".")

                        if result.returncode == 0:
                            st.success("潛力股分析完成！請重新整理頁面查看結果。")
                            st.experimental_rerun()
                        else:
                            st.error(f"分析失敗: {result.stderr}")
                    except Exception as e:
                        st.error(f"執行分析失敗: {e}")

    except Exception as e:
        st.error(f"載入潛力股資料失敗: {e}")
    finally:
        conn.close()

def create_revenue_trend_chart(revenue_data, stock_name):
    """創建營收趨勢圖"""
    if not revenue_data:
        return None

    # 將tuple資料轉換為DataFrame，並指定正確的欄位名稱
    df = pd.DataFrame(revenue_data, columns=['revenue_year', 'revenue_month', 'revenue', 'revenue_growth_yoy'])

    # 創建日期欄位
    df['date'] = pd.to_datetime(df[['revenue_year', 'revenue_month']].assign(day=1))
    df = df.sort_values('date')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['revenue'] / 1000000000,  # 轉換為億元
        mode='lines+markers',
        name='月營收',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title=f"{stock_name} 月營收趨勢",
        xaxis_title="日期",
        yaxis_title="營收 (億元)",
        template="plotly_white",
        height=300
    )

    return fig

def calculate_technical_indicators(df):
    """計算技術指標"""
    if len(df) < 20:
        return df

    # 移動平均線
    df['MA5'] = df['close_price'].rolling(window=5).mean()
    df['MA10'] = df['close_price'].rolling(window=10).mean()
    df['MA20'] = df['close_price'].rolling(window=20).mean()
    df['MA60'] = df['close_price'].rolling(window=60).mean() if len(df) >= 60 else None

    # RSI
    delta = df['close_price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['close_price'].ewm(span=12).mean()
    exp2 = df['close_price'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_histogram'] = df['MACD'] - df['MACD_signal']

    # 布林通道
    df['BB_middle'] = df['close_price'].rolling(window=20).mean()
    bb_std = df['close_price'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)

    # 價格變化
    df['price_change'] = df['close_price'].pct_change()
    df['price_change_abs'] = df['close_price'].diff()

    return df

def show_overview_tab(df, stock_info, stock_id, db_manager):
    """顯示總覽標籤頁"""
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)

    # 最新股價資訊
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    # 計算漲跌
    price_change = latest['close_price'] - prev['close_price']
    price_change_pct = (price_change / prev['close_price']) * 100 if prev['close_price'] != 0 else 0

    # 股價指標卡片
    st.subheader("💰 即時股價資訊")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">收盤價</div>
            <div class="metric-value">{latest['close_price']:.2f}</div>
            <div class="{'performance-positive' if price_change >= 0 else 'performance-negative'}">
                {'+' if price_change >= 0 else ''}{price_change:.2f} ({'+' if price_change_pct >= 0 else ''}{price_change_pct:.2f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">開盤價</div>
            <div class="metric-value">{latest['open_price']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">最高價</div>
            <div class="metric-value">{latest['high_price']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">最低價</div>
            <div class="metric-value">{latest['low_price']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        volume_str = format_number(latest['volume'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">成交量</div>
            <div class="metric-value">{volume_str}</div>
        </div>
        """, unsafe_allow_html=True)

    # K線圖
    st.subheader("📊 股價走勢圖")
    candlestick_fig = create_enhanced_candlestick_chart(df, stock_info['stock_name'])
    st.plotly_chart(candlestick_fig, use_container_width=True)

    # 成交量圖
    volume_fig = create_volume_chart(df, f"{stock_info['stock_name']} 成交量")
    st.plotly_chart(volume_fig, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

def create_enhanced_candlestick_chart(df, title):
    """創建增強版K線圖（包含移動平均線）"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(title, 'RSI'),
        row_width=[0.7, 0.3]
    )

    # K線圖
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open_price'],
            high=df['high_price'],
            low=df['low_price'],
            close=df['close_price'],
            name="K線",
            increasing_line_color='#00C851',
            decreasing_line_color='#ff4444'
        ),
        row=1, col=1
    )

    # 移動平均線
    if 'MA5' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['MA5'],
                mode='lines',
                name='MA5',
                line=dict(color='orange', width=1)
            ),
            row=1, col=1
        )

    if 'MA20' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['MA20'],
                mode='lines',
                name='MA20',
                line=dict(color='blue', width=1)
            ),
            row=1, col=1
        )

    # 布林通道
    if 'BB_upper' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['BB_upper'],
                mode='lines',
                name='布林上軌',
                line=dict(color='gray', width=1, dash='dash'),
                opacity=0.5
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['BB_lower'],
                mode='lines',
                name='布林下軌',
                line=dict(color='gray', width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(128,128,128,0.1)',
                opacity=0.5
            ),
            row=1, col=1
        )

    # RSI
    if 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2)
            ),
            row=2, col=1
        )

        # RSI 超買超賣線
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=True,
        template="plotly_white"
    )

    fig.update_yaxes(title_text="價格", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])

    return fig

def show_technical_tab(df, stock_info):
    """顯示技術分析標籤頁"""
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)

    st.subheader("📈 技術指標分析")

    # 技術指標數值
    latest = df.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if 'RSI' in df.columns and not pd.isna(latest['RSI']):
            rsi_color = "red" if latest['RSI'] > 70 else "green" if latest['RSI'] < 30 else "blue"
            rsi_status = "超買" if latest['RSI'] > 70 else "超賣" if latest['RSI'] < 30 else "正常"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">RSI (14日)</div>
                <div class="metric-value" style="color: {rsi_color};">{latest['RSI']:.1f}</div>
                <div style="color: {rsi_color};">{rsi_status}</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if 'MACD' in df.columns and not pd.isna(latest['MACD']):
            macd_color = "green" if latest['MACD'] > latest['MACD_signal'] else "red"
            macd_trend = "多頭" if latest['MACD'] > latest['MACD_signal'] else "空頭"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">MACD</div>
                <div class="metric-value" style="color: {macd_color};">{latest['MACD']:.3f}</div>
                <div style="color: {macd_color};">{macd_trend}</div>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        if 'MA20' in df.columns and not pd.isna(latest['MA20']):
            ma_color = "green" if latest['close_price'] > latest['MA20'] else "red"
            ma_position = "站上" if latest['close_price'] > latest['MA20'] else "跌破"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">MA20位置</div>
                <div class="metric-value" style="color: {ma_color};">{latest['MA20']:.2f}</div>
                <div style="color: {ma_color};">{ma_position}均線</div>
            </div>
            """, unsafe_allow_html=True)

    with col4:
        if 'BB_upper' in df.columns and not pd.isna(latest['BB_upper']):
            bb_position = ""
            bb_color = "blue"
            if latest['close_price'] > latest['BB_upper']:
                bb_position = "上軌之上"
                bb_color = "red"
            elif latest['close_price'] < latest['BB_lower']:
                bb_position = "下軌之下"
                bb_color = "green"
            else:
                bb_position = "軌道內"
                bb_color = "blue"

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">布林通道</div>
                <div class="metric-value" style="color: {bb_color};">{latest['close_price']:.2f}</div>
                <div style="color: {bb_color};">{bb_position}</div>
            </div>
            """, unsafe_allow_html=True)

    # MACD圖表
    if 'MACD' in df.columns:
        st.subheader("📊 MACD指標")
        macd_fig = create_macd_chart(df, stock_info['stock_name'])
        st.plotly_chart(macd_fig, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

def create_macd_chart(df, title):
    """創建MACD圖表"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f"{title} MACD", "MACD柱狀圖"),
        row_heights=[0.7, 0.3]
    )

    # MACD線
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['MACD'],
            mode='lines',
            name='MACD',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )

    # 信號線
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['MACD_signal'],
            mode='lines',
            name='Signal',
            line=dict(color='red', width=2)
        ),
        row=1, col=1
    )

    # MACD柱狀圖
    colors = ['green' if val >= 0 else 'red' for val in df['MACD_histogram']]
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['MACD_histogram'],
            name='MACD Histogram',
            marker_color=colors
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=400,
        showlegend=True,
        template="plotly_white"
    )

    return fig

def show_fundamental_tab(stock_id, stock_info, db_manager):
    """顯示基本面分析標籤頁"""
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)

    conn = db_manager.get_connection()
    cursor = conn.cursor()

    # 營收分析
    st.subheader("📈 營收分析")

    try:
        # 獲取最近12個月營收
        cursor.execute("""
            SELECT revenue_year, revenue_month, revenue, revenue_growth_yoy
            FROM monthly_revenues
            WHERE stock_id = ?
            ORDER BY revenue_year DESC, revenue_month DESC
            LIMIT 12
        """, (stock_id,))

        revenue_data = cursor.fetchall()

        if revenue_data:
            # 營收指標卡片
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                latest_revenue = revenue_data[0][2] / 1000000000
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">最新月營收</div>
                    <div class="metric-value">{latest_revenue:.2f}億</div>
                    <div>{revenue_data[0][0]}年{revenue_data[0][1]}月</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                avg_revenue = sum([r[2] for r in revenue_data]) / len(revenue_data) / 1000000000
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">近12月平均</div>
                    <div class="metric-value">{avg_revenue:.2f}億</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                if revenue_data[0][3] is not None:
                    yoy_color = "green" if revenue_data[0][3] > 0 else "red"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">年成長率</div>
                        <div class="metric-value" style="color: {yoy_color};">{revenue_data[0][3]:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

            with col4:
                total_revenue = sum([r[2] for r in revenue_data]) / 1000000000
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">近12月總營收</div>
                    <div class="metric-value">{total_revenue:.2f}億</div>
                </div>
                """, unsafe_allow_html=True)

            # 營收趨勢圖
            revenue_chart = create_revenue_trend_chart(revenue_data, stock_info['stock_name'])
            if revenue_chart:
                st.plotly_chart(revenue_chart, use_container_width=True)

        else:
            st.info("📊 該股票暫無營收資料")

    except Exception as e:
        st.error(f"❌ 載入營收資料失敗: {e}")

    # 財務比率分析
    st.subheader("💼 財務比率")

    try:
        cursor.execute("""
            SELECT gross_margin, operating_margin, net_margin, roe, roa, debt_ratio, current_ratio, date
            FROM financial_ratios
            WHERE stock_id = ?
            ORDER BY date DESC
            LIMIT 1
        """, (stock_id,))

        financial_ratio = cursor.fetchone()

        if financial_ratio:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if financial_ratio[0] is not None:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">毛利率</div>
                        <div class="metric-value">{financial_ratio[0]:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

            with col2:
                if financial_ratio[1] is not None:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">營業利益率</div>
                        <div class="metric-value">{financial_ratio[1]:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

            with col3:
                if financial_ratio[3] is not None:
                    roe_color = "green" if financial_ratio[3] > 15 else "orange" if financial_ratio[3] > 10 else "red"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">ROE</div>
                        <div class="metric-value" style="color: {roe_color};">{financial_ratio[3]:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

            with col4:
                if financial_ratio[5] is not None:
                    debt_color = "green" if financial_ratio[5] < 40 else "orange" if financial_ratio[5] < 60 else "red"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">負債比率</div>
                        <div class="metric-value" style="color: {debt_color};">{financial_ratio[5]:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

        else:
            st.info("📊 該股票暫無財務比率資料")

    except Exception as e:
        st.error(f"❌ 載入財務比率失敗: {e}")

    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

def show_cashflow_tab(stock_id, stock_info, db_manager):
    """顯示現金流分析標籤頁"""
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)

    st.subheader("💸 現金流分析")

    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        # 獲取現金流資料
        cash_flow_types = [
            ('CashFlowsFromOperatingActivities', '營運現金流'),
            ('CashProvidedByInvestingActivities', '投資現金流'),
            ('CashFlowsProvidedFromFinancingActivities', '融資現金流')
        ]

        # 檢查是否有現金流資料
        cursor.execute("SELECT COUNT(*) FROM cash_flow_statements WHERE stock_id = ?", (stock_id,))
        cash_flow_count = cursor.fetchone()[0]

        if cash_flow_count == 0:
            st.info("📊 該股票暫無現金流資料")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # 獲取近5年現金流資料
        years = ['2020', '2021', '2022', '2023', '2024', '2025']
        cash_flow_data = {}

        for cf_type, cf_name in cash_flow_types:
            cash_flow_data[cf_name] = []
            for year in years:
                cursor.execute('''
                    SELECT value
                    FROM cash_flow_statements
                    WHERE stock_id = ? AND type = ? AND date LIKE ?
                    ORDER BY date DESC LIMIT 1
                ''', (stock_id, cf_type, f'{year}%'))

                result = cursor.fetchone()
                value = result[0] / 1000000000 if result and result[0] else 0  # 轉億元
                cash_flow_data[cf_name].append(value)

        # 現金流指標卡片
        col1, col2, col3 = st.columns(3)

        # 最新年度數據
        latest_year_idx = -1
        for i in range(len(years)-1, -1, -1):
            if any(cash_flow_data[cf_name][i] != 0 for cf_name in [cf[1] for cf in cash_flow_types]):
                latest_year_idx = i
                break

        if latest_year_idx >= 0:
            with col1:
                operating_cf = cash_flow_data['營運現金流'][latest_year_idx]
                cf_color = "green" if operating_cf > 0 else "red"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">營運現金流 ({years[latest_year_idx]})</div>
                    <div class="metric-value" style="color: {cf_color};">{operating_cf:.1f}億</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                investing_cf = cash_flow_data['投資現金流'][latest_year_idx]
                cf_color = "red" if investing_cf < 0 else "green"  # 投資現金流通常為負
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">投資現金流 ({years[latest_year_idx]})</div>
                    <div class="metric-value" style="color: {cf_color};">{investing_cf:.1f}億</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                # 自由現金流 = 營運現金流 - 投資現金流
                free_cf = operating_cf - investing_cf
                cf_color = "green" if free_cf > 0 else "red"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">自由現金流 ({years[latest_year_idx]})</div>
                    <div class="metric-value" style="color: {cf_color};">{free_cf:.1f}億</div>
                </div>
                """, unsafe_allow_html=True)

        # 現金流趨勢圖
        st.subheader("📊 現金流趨勢")
        cash_flow_fig = create_cashflow_chart(cash_flow_data, years, stock_info['stock_name'])
        st.plotly_chart(cash_flow_fig, use_container_width=True)

        # 現金流健康度分析
        st.subheader("🏥 現金流健康度")

        if latest_year_idx >= 0:
            operating_cf = cash_flow_data['營運現金流'][latest_year_idx]
            investing_cf = cash_flow_data['投資現金流'][latest_year_idx]
            financing_cf = cash_flow_data['融資現金流'][latest_year_idx]

            health_score = 0
            health_comments = []

            # 營運現金流評分
            if operating_cf > 0:
                health_score += 40
                health_comments.append("✅ 營運現金流為正，經營狀況良好")
            else:
                health_comments.append("❌ 營運現金流為負，需關注經營狀況")

            # 投資現金流評分（適度投資為佳）
            if -50 <= investing_cf <= 0:
                health_score += 30
                health_comments.append("✅ 投資現金流適中，持續投資發展")
            elif investing_cf < -50:
                health_score += 20
                health_comments.append("⚠️ 投資現金流較大，大幅擴張中")
            else:
                health_comments.append("⚠️ 投資現金流異常，可能缺乏投資")

            # 自由現金流評分
            free_cf = operating_cf - investing_cf
            if free_cf > 0:
                health_score += 30
                health_comments.append("✅ 自由現金流為正，財務彈性佳")
            else:
                health_comments.append("❌ 自由現金流為負，資金較緊張")

            # 顯示健康度評分
            health_color = "green" if health_score >= 80 else "orange" if health_score >= 60 else "red"
            health_level = "優秀" if health_score >= 80 else "良好" if health_score >= 60 else "需改善"

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">現金流健康度評分</div>
                <div class="metric-value" style="color: {health_color};">{health_score}/100</div>
                <div style="color: {health_color};">{health_level}</div>
            </div>
            """, unsafe_allow_html=True)

            # 顯示評分說明
            for comment in health_comments:
                st.write(comment)

    except Exception as e:
        st.error(f"❌ 載入現金流資料失敗: {e}")

    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

def create_cashflow_chart(cash_flow_data, years, title):
    """創建現金流趨勢圖"""
    fig = go.Figure()

    colors = {
        '營運現金流': '#00C851',
        '投資現金流': '#ff4444',
        '融資現金流': '#2196F3'
    }

    for cf_name, values in cash_flow_data.items():
        fig.add_trace(
            go.Scatter(
                x=years,
                y=values,
                mode='lines+markers',
                name=cf_name,
                line=dict(color=colors.get(cf_name, 'gray'), width=3),
                marker=dict(size=8)
            )
        )

    # 添加零線
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    fig.update_layout(
        title=f"{title} 現金流趨勢",
        xaxis_title="年份",
        yaxis_title="現金流 (億元)",
        height=400,
        template="plotly_white",
        showlegend=True
    )

    return fig

def show_rating_tab(stock_id, stock_info, db_manager):
    """顯示評分標籤頁"""
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)

    st.subheader("🎯 綜合評分")

    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        # 獲取潛力股評分
        cursor.execute("""
            SELECT total_score, financial_health_score, growth_score,
                   dividend_score, grade, analysis_date
            FROM stock_scores
            WHERE stock_id = ?
            ORDER BY analysis_date DESC
            LIMIT 1
        """, (stock_id,))

        score_data = cursor.fetchone()

        if score_data:
            total_score, financial_health, growth_potential, dividend_stability, rating, analysis_date = score_data

            # 總分顯示
            score_color = "green" if total_score >= 75 else "orange" if total_score >= 60 else "red"
            rating_emoji = "🌟" if total_score >= 75 else "⭐" if total_score >= 60 else "💫"

            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white; border-radius: 15px; margin-bottom: 20px;">
                <h2>{rating_emoji} 綜合評分</h2>
                <h1 style="font-size: 48px; margin: 10px 0;">{total_score:.1f}</h1>
                <h3>{rating}</h3>
                <p>分析日期: {analysis_date}</p>
            </div>
            """, unsafe_allow_html=True)

            # 分項評分
            col1, col2, col3 = st.columns(3)

            with col1:
                fh_color = "green" if financial_health >= 75 else "orange" if financial_health >= 60 else "red"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">財務健康度</div>
                    <div class="metric-value" style="color: {fh_color};">{financial_health:.1f}</div>
                    <div>基本面分析</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                gp_color = "green" if growth_potential >= 75 else "orange" if growth_potential >= 60 else "red"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">成長潛力</div>
                    <div class="metric-value" style="color: {gp_color};">{growth_potential:.1f}</div>
                    <div>營收成長分析</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                ds_color = "green" if dividend_stability >= 75 else "orange" if dividend_stability >= 60 else "red"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">股利穩定性</div>
                    <div class="metric-value" style="color: {ds_color};">{dividend_stability:.1f}</div>
                    <div>配息分析</div>
                </div>
                """, unsafe_allow_html=True)

            # 評分雷達圖
            st.subheader("📊 評分雷達圖")
            radar_fig = create_rating_radar_chart(financial_health, growth_potential, dividend_stability, stock_info['stock_name'])
            st.plotly_chart(radar_fig, use_container_width=True)

            # 投資建議
            st.subheader("💡 投資建議")

            if total_score >= 75:
                st.success("🌟 **優質股票** - 綜合表現優異，值得長期持有")
                st.write("- 財務狀況健康，獲利能力強")
                st.write("- 成長潛力佳，未來展望樂觀")
                st.write("- 股利政策穩定，適合價值投資")
            elif total_score >= 60:
                st.warning("⭐ **中等股票** - 表現尚可，需持續觀察")
                st.write("- 基本面表現中等，有改善空間")
                st.write("- 建議搭配技術分析進行投資決策")
                st.write("- 注意風險控制，適度配置")
            else:
                st.error("💫 **需謹慎** - 表現較弱，建議深入研究")
                st.write("- 基本面存在問題，需謹慎評估")
                st.write("- 建議等待更好的進場時機")
                st.write("- 如已持有，考慮適時調整部位")

        else:
            st.info("📊 該股票暫無評分資料，請先執行潛力股分析")

            if st.button("🔄 立即分析", key="analyze_stock"):
                with st.spinner("正在分析中..."):
                    try:
                        import subprocess
                        import os

                        # 執行潛力股分析
                        result = subprocess.run([
                            "python", "scripts/analyze_potential_stocks.py",
                            "--stock-id", stock_id
                        ], capture_output=True, text=True, cwd=os.getcwd())

                        if result.returncode == 0:
                            st.success("✅ 分析完成！請重新整理頁面查看結果")
                            st.info("💡 提示：點擊瀏覽器的重新整理按鈕或按F5來查看最新評分")

                            # 顯示分析結果預覽
                            if result.stdout:
                                with st.expander("📋 分析日誌"):
                                    st.text(result.stdout)
                        else:
                            st.error(f"❌ 分析失敗: {result.stderr}")
                            st.info("💡 可能原因：該股票缺少必要的財務資料")

                    except Exception as e:
                        st.error(f"❌ 執行分析失敗: {e}")
                        st.info("💡 請確保分析腳本存在且可執行")

    except Exception as e:
        st.error(f"❌ 載入評分資料失敗: {e}")

    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

def create_rating_radar_chart(financial_health, growth_potential, dividend_stability, title):
    """創建評分雷達圖"""
    categories = ['財務健康度', '成長潛力', '股利穩定性']
    values = [financial_health, growth_potential, dividend_stability]

    # 添加第一個點到最後，形成閉合圖形
    values += values[:1]
    categories += categories[:1]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=title,
        line_color='rgb(31, 78, 121)',
        fillcolor='rgba(31, 78, 121, 0.3)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickmode='linear',
                tick0=0,
                dtick=20
            )),
        showlegend=True,
        title=f"{title} 評分分析",
        height=400
    )

    return fig

def create_revenue_trend_chart(revenue_data, title):
    """創建營收趨勢圖"""
    if not revenue_data:
        return None

    # 準備資料
    dates = []
    revenues = []
    growth_rates = []

    for year, month, revenue, growth in reversed(revenue_data):  # 反轉以時間順序顯示
        date_str = f"{year}-{month:02d}"
        dates.append(date_str)
        revenues.append(revenue / 1000000000)  # 轉億元
        growth_rates.append(growth if growth is not None else 0)

    # 創建雙軸圖表
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=[f"{title} 營收趨勢"]
    )

    # 營收柱狀圖
    fig.add_trace(
        go.Bar(
            x=dates,
            y=revenues,
            name="月營收",
            marker_color='lightblue',
            yaxis='y'
        ),
        secondary_y=False,
    )

    # 成長率線圖
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=growth_rates,
            mode='lines+markers',
            name="年成長率",
            line=dict(color='red', width=2),
            marker=dict(size=6),
            yaxis='y2'
        ),
        secondary_y=True,
    )

    # 設定軸標題
    fig.update_xaxes(title_text="月份")
    fig.update_yaxes(title_text="營收 (億元)", secondary_y=False)
    fig.update_yaxes(title_text="年成長率 (%)", secondary_y=True)

    # 添加零線
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, secondary_y=True)

    fig.update_layout(
        height=400,
        showlegend=True,
        template="plotly_white",
        hovermode='x unified'
    )

    return fig

def create_volume_chart(df, title):
    """創建成交量圖表"""
    fig = go.Figure()

    # 成交量柱狀圖
    colors = ['green' if close >= open_price else 'red'
              for close, open_price in zip(df['close_price'], df['open_price'])]

    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='成交量',
        marker_color=colors,
        opacity=0.7
    ))

    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="成交量",
        height=300,
        template="plotly_white"
    )

    return fig

def show_stock_analysis(db_manager, query_service):
    """顯示FinMind風格的股票分析頁面"""

    # 自定義CSS樣式
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f4e79;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1f4e79;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
        margin-bottom: 5px;
    }
    .tab-container {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .stock-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .performance-positive {
        color: #00C851;
        font-weight: bold;
    }
    .performance-negative {
        color: #ff4444;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    # 主標題
    st.markdown("""
    <div class="main-header">
        <h1>🔍 台股個股分析系統</h1>
        <p>專業級股票分析工具 - 仿FinMind設計</p>
    </div>
    """, unsafe_allow_html=True)

    # 股票選擇區域
    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        stock_id = st.text_input("🔍 輸入股票代碼", placeholder="例如: 2330, 2317, 2454", help="輸入台股代碼進行分析")

    with col2:
        # 時間範圍選擇
        period_options = {
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 252,
            "2Y": 504
        }
        selected_period = st.selectbox("📅 分析期間", list(period_options.keys()), index=1)
        days = period_options[selected_period]

    with col3:
        # 分析類型選擇
        analysis_type = st.selectbox("📊 分析類型", ["完整分析", "技術分析", "基本面分析", "現金流分析"], index=0)

    if stock_id:
        # 取得股票資訊
        stock_info = query_service.get_stock_info(stock_id)

        if not stock_info:
            st.error("❌ 找不到該股票，請檢查股票代碼是否正確")
            return

        # 股票標題區域
        st.markdown(f"""
        <div class="stock-header">
            <h2>📈 {stock_info['stock_name']} ({stock_id})</h2>
            <p>市場別: {stock_info.get('market', 'N/A')} | ETF: {'是' if stock_info.get('is_etf') else '否'}</p>
        </div>
        """, unsafe_allow_html=True)

        # 獲取股價資料
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        prices = query_service.get_stock_prices(
            stock_id,
            start_date.isoformat(),
            end_date.isoformat()
        )

        if not prices:
            st.warning("⚠️ 該股票暫無股價資料")
            return

        df = pd.DataFrame(prices)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # 計算技術指標
        df = calculate_technical_indicators(df)

        # 創建標籤頁
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 總覽", "📈 技術分析", "💰 基本面", "💸 現金流", "🎯 評分"
        ])

        with tab1:
            show_overview_tab(df, stock_info, stock_id, db_manager)

        with tab2:
            show_technical_tab(df, stock_info)

        with tab3:
            show_fundamental_tab(stock_id, stock_info, db_manager)

        with tab4:
            show_cashflow_tab(stock_id, stock_info, db_manager)

        with tab5:
            show_rating_tab(stock_id, stock_info, db_manager)

def show_database_status(db_manager, query_service):
    """顯示資料庫狀態頁面"""
    st.header("📊 資料庫狀態")

    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        # 獲取各類資料統計
        st.subheader("📈 資料收集統計")

        # 股票基本資料
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stocks_count = cursor.fetchone()[0]

        # 股價資料
        cursor.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM stock_prices")
        price_stats = cursor.fetchone()

        # 月營收資料
        cursor.execute("SELECT COUNT(*) FROM monthly_revenues")
        revenue_count = cursor.fetchone()[0]

        # 綜合損益表
        cursor.execute("SELECT COUNT(*) FROM financial_statements")
        financial_count = cursor.fetchone()[0]

        # 資產負債表
        cursor.execute("SELECT COUNT(*) FROM balance_sheets")
        balance_count = cursor.fetchone()[0]

        # 股利政策
        cursor.execute("SELECT COUNT(*) FROM dividend_policies")
        dividend_count = cursor.fetchone()[0]

        # 財務比率
        cursor.execute("SELECT COUNT(*) FROM financial_ratios")
        ratio_count = cursor.fetchone()[0]

        # 潛力股評分
        cursor.execute("SELECT COUNT(*) FROM stock_scores")
        score_count = cursor.fetchone()[0]

        # 新增表統計
        cursor.execute("SELECT COUNT(*) FROM cash_flow_statements")
        cash_flow_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM market_values")
        market_value_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM stock_splits")
        split_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM dividend_results")
        dividend_result_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM technical_indicators")
        tech_indicator_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM etf_dividends")
        etf_dividend_count = cursor.fetchone()[0]

        # 顯示統計資訊
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("股票基本資料", f"{stocks_count:,}筆")
            st.metric("月營收資料", f"{revenue_count:,}筆")
            st.metric("現金流量表", f"{cash_flow_count:,}筆")

        with col2:
            st.metric("股價資料", f"{price_stats[0]:,}筆")
            st.metric("綜合損益表", f"{financial_count:,}筆")
            st.metric("市值資料", f"{market_value_count:,}筆")

        with col3:
            st.metric("資產負債表", f"{balance_count:,}筆")
            st.metric("股利政策", f"{dividend_count:,}筆")
            st.metric("股票分割", f"{split_count:,}筆")

        with col4:
            st.metric("財務比率", f"{ratio_count:,}筆")
            st.metric("潛力股評分", f"{score_count:,}筆")
            st.metric("技術指標", f"{tech_indicator_count:,}筆")

        # 額外資料統計
        st.subheader("📊 額外資料統計")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("股利發放結果", f"{dividend_result_count:,}筆")

        with col2:
            st.metric("ETF配息", f"{etf_dividend_count:,}筆")

        with col3:
            # 資料更新記錄
            cursor.execute("SELECT COUNT(*) FROM data_updates")
            update_count = cursor.fetchone()[0]
            st.metric("資料更新記錄", f"{update_count:,}筆")

        # 資料日期範圍
        if price_stats[1] and price_stats[2]:
            st.subheader("📅 股價資料範圍")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("最早日期", price_stats[1])

            with col2:
                st.metric("最新日期", price_stats[2])

        # 資料完整性分析
        st.subheader("🔍 資料完整性分析")

        # 更實際的完整度計算
        # 計算有資料的股票數量
        cursor.execute("SELECT COUNT(DISTINCT stock_id) FROM stock_prices")
        stocks_with_prices = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT stock_id) FROM monthly_revenues")
        stocks_with_revenue = cursor.fetchone()[0]

        # 計算平均每檔股票的資料量
        avg_price_per_stock = price_stats[0] / stocks_with_prices if stocks_with_prices > 0 else 0
        avg_revenue_per_stock = revenue_count / stocks_with_revenue if stocks_with_revenue > 0 else 0

        col1, col2, col3 = st.columns(3)

        with col1:
            stock_coverage = (stocks_with_prices / stocks_count * 100) if stocks_count > 0 else 0
            st.metric("股票覆蓋率", f"{stock_coverage:.1f}%")
            st.caption(f"平均每股 {avg_price_per_stock:.0f} 筆資料")

        with col2:
            revenue_coverage = (stocks_with_revenue / stocks_count * 100) if stocks_count > 0 else 0
            st.metric("營收覆蓋率", f"{revenue_coverage:.1f}%")
            st.caption(f"平均每股 {avg_revenue_per_stock:.0f} 筆資料")

        with col3:
            potential_coverage = (score_count / stocks_count * 100) if stocks_count > 0 else 0
            st.metric("潛力分析覆蓋率", f"{potential_coverage:.1f}%")
            st.caption(f"{score_count} 檔股票已分析")

        # 資料品質分析
        st.subheader("📈 資料品質分析")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("**📊 市場分布**")
            cursor.execute("""
                SELECT market, COUNT(*) as count
                FROM stocks
                WHERE market IS NOT NULL
                GROUP BY market
                ORDER BY count DESC
            """)
            market_distribution = cursor.fetchall()

            for market, count in market_distribution:
                market_name = {'TWSE': '上市', 'TPEX': '上櫃', 'EMERGING': '興櫃'}.get(market, market)
                st.metric(market_name, f"{count}檔")

        with col2:
            st.write("**💰 資料完整度**")
            # 計算有完整資料的股票數量
            cursor.execute("""
                SELECT
                    COUNT(CASE WHEN price_count >= 1000 THEN 1 END) as good_price,
                    COUNT(CASE WHEN revenue_count >= 50 THEN 1 END) as good_revenue,
                    COUNT(CASE WHEN financial_count >= 20 THEN 1 END) as good_financial
                FROM (
                    SELECT
                        s.stock_id,
                        COUNT(sp.date) as price_count,
                        COUNT(mr.revenue_year) as revenue_count,
                        COUNT(fs.date) as financial_count
                    FROM stocks s
                    LEFT JOIN stock_prices sp ON s.stock_id = sp.stock_id
                    LEFT JOIN monthly_revenues mr ON s.stock_id = mr.stock_id
                    LEFT JOIN financial_statements fs ON s.stock_id = fs.stock_id
                    GROUP BY s.stock_id
                ) as stats
            """)
            completeness = cursor.fetchone()

            st.metric("股價完整", f"{completeness[0]}檔")
            st.metric("營收完整", f"{completeness[1]}檔")
            st.metric("財務完整", f"{completeness[2]}檔")

        with col3:
            st.write("**🎯 熱門股票**")
            # 顯示資料量最多的前5檔股票
            cursor.execute("""
                SELECT s.stock_name, COUNT(sp.date) as price_count
                FROM stocks s
                JOIN stock_prices sp ON s.stock_id = sp.stock_id
                GROUP BY s.stock_id, s.stock_name
                ORDER BY price_count DESC
                LIMIT 5
            """)
            top_stocks = cursor.fetchall()

            for stock_name, count in top_stocks:
                # 截短股票名稱
                short_name = stock_name[:6] + "..." if len(stock_name) > 8 else stock_name
                st.metric(short_name, f"{count:,}筆")

        # 資料趨勢分析
        st.subheader("📊 資料趨勢分析")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**📈 近期資料增長**")
            # 計算最近7天的資料增長
            cursor.execute("""
                SELECT
                    COUNT(CASE WHEN created_at >= date('now', '-7 days') THEN 1 END) as week_count,
                    COUNT(CASE WHEN created_at >= date('now', '-1 day') THEN 1 END) as day_count,
                    COUNT(*) as total_count
                FROM stock_prices
            """)
            growth_stats = cursor.fetchone()

            if growth_stats and growth_stats[2] > 0:
                week_growth = (growth_stats[0] / growth_stats[2] * 100) if growth_stats[2] > 0 else 0
                st.metric("近7天新增", f"{growth_stats[0]:,}筆", f"{week_growth:.1f}%")
                st.metric("近1天新增", f"{growth_stats[1]:,}筆")
            else:
                st.info("暫無增長資料")

        with col2:
            st.write("**🎯 潛力股分析狀況**")
            cursor.execute("""
                SELECT
                    COUNT(CASE WHEN total_score >= 75 THEN 1 END) as excellent,
                    COUNT(CASE WHEN total_score >= 60 AND total_score < 75 THEN 1 END) as good,
                    COUNT(CASE WHEN total_score < 60 THEN 1 END) as average
                FROM stock_scores
            """)
            score_distribution = cursor.fetchone()

            if score_distribution:
                st.metric("優質股票(75+分)", f"{score_distribution[0]}檔")
                st.metric("良好股票(60-74分)", f"{score_distribution[1]}檔")
                st.metric("一般股票(<60分)", f"{score_distribution[2]}檔")
            else:
                st.info("暫無評分資料")

        # 最後更新時間
        st.subheader("⏰ 最後更新時間")

        # 獲取各類資料的最後更新時間
        cursor.execute("SELECT MAX(created_at) FROM stock_prices")
        last_price_update = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(created_at) FROM monthly_revenues")
        last_revenue_update = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(analysis_date) FROM stock_scores")
        last_score_update = cursor.fetchone()[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("股價資料", last_price_update or "無資料")

        with col2:
            st.metric("營收資料", last_revenue_update or "無資料")

        with col3:
            st.metric("潛力分析", last_score_update or "無資料")

        # 資料庫大小資訊
        st.subheader("💾 資料庫資訊")

        import os
        if os.path.exists(Config.DATABASE_PATH):
            db_size = os.path.getsize(Config.DATABASE_PATH)
            db_size_mb = db_size / (1024 * 1024)
            st.metric("資料庫大小", f"{db_size_mb:.1f} MB")
        else:
            st.metric("資料庫大小", "無法取得")

    except Exception as e:
        st.error(f"載入資料庫狀態失敗: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

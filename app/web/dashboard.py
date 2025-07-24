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

def show_stock_analysis(db_manager, query_service):
    """顯示合併後的股票分析頁面"""
    st.header("🔍 股票分析")

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

        # 基本資料
        st.subheader(f"📋 {stock_info['stock_name']} ({stock_id}) 基本資料")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("股票名稱", stock_info['stock_name'])
        with col2:
            st.metric("市場別", stock_info.get('market', 'N/A'))
        with col3:
            etf_status = "是" if stock_info.get('is_etf') else "否"
            st.metric("ETF", etf_status)

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

            # 最新股價資訊
            st.subheader("💰 最新股價資訊")
            latest = df.iloc[-1]

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("開盤價", f"{latest['open_price']:.2f}")
            with col2:
                st.metric("收盤價", f"{latest['close_price']:.2f}")
            with col3:
                st.metric("最高價", f"{latest['high_price']:.2f}")
            with col4:
                st.metric("最低價", f"{latest['low_price']:.2f}")
            with col5:
                st.metric("成交量", format_number(latest['volume']))

            # K線圖和成交量圖
            st.subheader("📊 股價走勢")

            # K線圖
            candlestick_fig = create_candlestick_chart(df, f"{stock_info['stock_name']} K線圖")
            st.plotly_chart(candlestick_fig, use_container_width=True)

            # 成交量圖
            volume_fig = create_volume_chart(df, f"{stock_info['stock_name']} 成交量")
            st.plotly_chart(volume_fig, use_container_width=True)

        else:
            st.warning("該股票暫無股價資料")

        # 月營收資料
        st.subheader("📈 月營收趨勢")
        conn = db_manager.get_connection()
        cursor = conn.cursor()

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
                # 創建營收趨勢圖
                revenue_chart = create_revenue_trend_chart(revenue_data, stock_info['stock_name'])

                if revenue_chart:
                    st.plotly_chart(revenue_chart, use_container_width=True)

                # 營收統計
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    latest_revenue = revenue_data[0][2] / 1000000000  # 轉億元
                    st.metric("最新月營收", f"{latest_revenue:.2f}億")
                with col2:
                    avg_revenue = sum([r[2] for r in revenue_data]) / len(revenue_data) / 1000000000
                    st.metric("平均月營收", f"{avg_revenue:.2f}億")
                with col3:
                    if revenue_data[0][3] is not None:
                        st.metric("最新成長率", f"{revenue_data[0][3]:.1f}%")
                    else:
                        st.metric("最新成長率", "N/A")
                with col4:
                    total_revenue = sum([r[2] for r in revenue_data]) / 1000000000
                    st.metric("近12月總營收", f"{total_revenue:.2f}億")
            else:
                st.info("該股票暫無月營收資料")

        except Exception as e:
            st.error(f"載入月營收資料失敗: {e}")

        # 財務指標
        st.subheader("📊 財務指標")

        try:
            # 獲取最新財務比率
            cursor.execute("""
                SELECT gross_margin, operating_margin, net_margin, roe, debt_ratio, date
                FROM financial_ratios
                WHERE stock_id = ?
                ORDER BY date DESC
                LIMIT 1
            """, (stock_id,))

            financial_ratio = cursor.fetchone()

            if financial_ratio:
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    if financial_ratio[0] is not None:
                        st.metric("毛利率", f"{financial_ratio[0]:.1f}%")
                    else:
                        st.metric("毛利率", "N/A")

                with col2:
                    if financial_ratio[1] is not None:
                        st.metric("營業利益率", f"{financial_ratio[1]:.1f}%")
                    else:
                        st.metric("營業利益率", "N/A")

                with col3:
                    if financial_ratio[2] is not None:
                        st.metric("淨利率", f"{financial_ratio[2]:.1f}%")
                    else:
                        st.metric("淨利率", "N/A")

                with col4:
                    if financial_ratio[3] is not None:
                        st.metric("ROE", f"{financial_ratio[3]:.1f}%")
                    else:
                        st.metric("ROE", "N/A")

                with col5:
                    if financial_ratio[4] is not None:
                        st.metric("負債比率", f"{financial_ratio[4]:.1f}%")
                    else:
                        st.metric("負債比率", "N/A")

                st.caption(f"資料日期: {financial_ratio[5]}")
            else:
                st.info("該股票暫無財務比率資料")

        except Exception as e:
            st.error(f"載入財務指標失敗: {e}")

        # 股利政策
        st.subheader("💰 股利政策")

        try:
            # 獲取歷年配息記錄
            cursor.execute("""
                SELECT year,
                       (cash_earnings_distribution + COALESCE(cash_statutory_surplus, 0)) as cash_dividend,
                       (stock_earnings_distribution + COALESCE(stock_statutory_surplus, 0)) as stock_dividend,
                       (cash_earnings_distribution + COALESCE(cash_statutory_surplus, 0) +
                        stock_earnings_distribution + COALESCE(stock_statutory_surplus, 0)) as total_dividend
                FROM dividend_policies
                WHERE stock_id = ?
                ORDER BY year DESC
                LIMIT 5
            """, (stock_id,))

            dividend_data = cursor.fetchall()

            if dividend_data:
                dividend_df = pd.DataFrame(dividend_data, columns=['年度', '現金股利', '股票股利', '總股利'])
                st.dataframe(dividend_df, use_container_width=True)

                # 配息統計
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_cash_dividend = sum([d[1] for d in dividend_data if d[1]]) / len([d for d in dividend_data if d[1]]) if any(d[1] for d in dividend_data) else 0
                    st.metric("平均現金股利", f"{avg_cash_dividend:.2f}元")
                with col2:
                    consecutive_years = len(dividend_data)
                    st.metric("連續配息年數", f"{consecutive_years}年")
                with col3:
                    if prices and dividend_data[0][1]:
                        yield_rate = (dividend_data[0][1] / latest['close_price']) * 100
                        st.metric("殖利率", f"{yield_rate:.2f}%")
                    else:
                        st.metric("殖利率", "N/A")
            else:
                st.info("該股票暫無股利政策資料")

        except Exception as e:
            st.error(f"載入股利政策失敗: {e}")

        # 潛力股分析
        st.subheader("🎯 潛力股分析")

        # 獲取潛力評分
        potential_score = get_stock_potential_score(db_manager, stock_id)

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
            eps_prediction = get_eps_prediction(db_manager, stock_id)

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
                            st.rerun()
                        else:
                            st.error(f"分析失敗: {result.stderr}")
                    except Exception as e:
                        st.error(f"執行分析失敗: {e}")

        conn.close()

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

        # 顯示統計資訊
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("股票基本資料", f"{stocks_count:,}筆")
            st.metric("月營收資料", f"{revenue_count:,}筆")

        with col2:
            st.metric("股價資料", f"{price_stats[0]:,}筆")
            st.metric("綜合損益表", f"{financial_count:,}筆")

        with col3:
            st.metric("資產負債表", f"{balance_count:,}筆")
            st.metric("股利政策", f"{dividend_count:,}筆")

        with col4:
            st.metric("財務比率", f"{ratio_count:,}筆")
            st.metric("潛力股評分", f"{score_count:,}筆")

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

        # 詳細統計
        st.subheader("📈 詳細統計")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**股價資料分布**")
            cursor.execute("""
                SELECT
                    CASE
                        WHEN COUNT(*) >= 2000 THEN '完整(2000+筆)'
                        WHEN COUNT(*) >= 1000 THEN '良好(1000-1999筆)'
                        WHEN COUNT(*) >= 500 THEN '一般(500-999筆)'
                        ELSE '不足(<500筆)'
                    END as category,
                    COUNT(DISTINCT stock_id) as stock_count
                FROM stock_prices
                GROUP BY stock_id
            """)
            price_distribution = cursor.fetchall()

            for category, count in price_distribution:
                st.metric(category, f"{count}檔")

        with col2:
            st.write("**營收資料分布**")
            cursor.execute("""
                SELECT
                    CASE
                        WHEN COUNT(*) >= 100 THEN '完整(100+筆)'
                        WHEN COUNT(*) >= 50 THEN '良好(50-99筆)'
                        WHEN COUNT(*) >= 20 THEN '一般(20-49筆)'
                        ELSE '不足(<20筆)'
                    END as category,
                    COUNT(DISTINCT stock_id) as stock_count
                FROM monthly_revenues
                GROUP BY stock_id
            """)
            revenue_distribution = cursor.fetchall()

            for category, count in revenue_distribution:
                st.metric(category, f"{count}檔")

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

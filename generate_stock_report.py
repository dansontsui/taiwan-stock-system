#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票財務分析報告生成器
輸入股票代號，生成完整的Excel財務分析報告
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

class StockReportGenerator:
    def __init__(self, stock_id):
        self.stock_id = stock_id.upper()
        self.db_path = Config.DATABASE_PATH
        self.report_data = {}
        self.stock_info = None
        
    def validate_stock_id(self):
        """驗證股票代號是否存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM stocks WHERE stock_id = ?", (self.stock_id,))
        self.stock_info = cursor.fetchone()
        conn.close()
        
        if not self.stock_info:
            return False, f"股票代號 {self.stock_id} 不存在於資料庫中"
        
        return True, "股票代號驗證成功"
    
    def get_basic_info(self):
        """獲取基本資訊"""
        if not self.stock_info:
            return None
            
        conn = sqlite3.connect(self.db_path)
        
        # 基本資訊
        basic_info = {
            '股票代號': self.stock_info[0],
            '股票名稱': self.stock_info[1],
            '所屬市場': '上市' if self.stock_info[2] == 'TWSE' else '上櫃',
            '產業別': self.stock_info[3] or '無資料',
            '上市日期': self.stock_info[4] or '無資料',
            '是否為ETF': '是' if self.stock_info[5] else '否'
        }
        
        # 最新股價資訊
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, close_price, volume, trading_money
            FROM stock_prices 
            WHERE stock_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (self.stock_id,))
        
        latest_price = cursor.fetchone()
        if latest_price:
            basic_info.update({
                '最新交易日': latest_price[0],
                '最新股價': f"{latest_price[1]:.2f}",
                '成交量': f"{latest_price[2]:,}",
                '成交金額': f"{latest_price[3]:,.0f}" if latest_price[3] else '無資料'
            })
        else:
            basic_info.update({
                '最新交易日': '無資料',
                '最新股價': '無資料',
                '成交量': '無資料',
                '成交金額': '無資料'
            })
        
        # 財務比率 - 使用容錯查詢
        try:
            cursor.execute("""
                SELECT pe_ratio, pb_ratio, dividend_yield
                FROM financial_ratios
                WHERE stock_id = ?
                ORDER BY date DESC
                LIMIT 1
            """, (self.stock_id,))

            ratios = cursor.fetchone()
            if ratios:
                basic_info.update({
                    '本益比(PE)': f"{ratios[0]:.2f}" if ratios[0] else '無資料',
                    '股價淨值比(PB)': f"{ratios[1]:.2f}" if ratios[1] else '無資料',
                    '殖利率': f"{ratios[2]:.2f}%" if ratios[2] else '無資料'
                })
            else:
                basic_info.update({
                    '本益比(PE)': '無資料',
                    '股價淨值比(PB)': '無資料',
                    '殖利率': '無資料'
                })
        except Exception:
            # 如果財務比率表不存在或欄位不匹配，設為無資料
            basic_info.update({
                '本益比(PE)': '無資料',
                '股價淨值比(PB)': '無資料',
                '殖利率': '無資料'
            })
        
        conn.close()
        return basic_info
    
    def get_monthly_revenue(self):
        """獲取月營收資料（近24個月）"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT revenue_year, revenue_month, revenue, 
                   revenue_growth_mom, revenue_growth_yoy
            FROM monthly_revenues 
            WHERE stock_id = ? 
            ORDER BY revenue_year DESC, revenue_month DESC 
            LIMIT 24
        """
        
        df = pd.read_sql_query(query, conn, params=(self.stock_id,))
        conn.close()
        
        if df.empty:
            return pd.DataFrame(columns=['年月', '營收金額', '月增率(%)', '年增率(%)'])
        
        # 格式化資料
        df['年月'] = df['revenue_year'].astype(str) + '/' + df['revenue_month'].astype(str).str.zfill(2)
        df['營收金額'] = df['revenue'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else '無資料')
        df['月增率(%)'] = df['revenue_growth_mom'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '無資料')
        df['年增率(%)'] = df['revenue_growth_yoy'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '無資料')
        
        return df[['年月', '營收金額', '月增率(%)', '年增率(%)']].reset_index(drop=True)
    
    def get_quarterly_financials(self):
        """獲取季度財務資料（近8季）"""
        conn = sqlite3.connect(self.db_path)
        
        # 獲取綜合損益表資料
        query = """
            SELECT date, type, value, origin_name
            FROM financial_statements 
            WHERE stock_id = ? 
            AND type IN ('Revenue', 'GrossProfit', 'OperatingIncome', 'NetIncome', 'EPS')
            ORDER BY date DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(self.stock_id,))
        conn.close()
        
        if df.empty:
            return pd.DataFrame(columns=['季度', '營業收入', '毛利', '營業利益', '稅後淨利', 'EPS'])
        
        # 轉換為透視表格式
        pivot_df = df.pivot_table(index='date', columns='type', values='value', aggfunc='first')
        pivot_df = pivot_df.head(8)  # 近8季
        
        # 格式化
        result_df = pd.DataFrame()
        result_df['季度'] = pivot_df.index
        result_df['營業收入'] = pivot_df.get('Revenue', pd.Series()).apply(lambda x: f"{x:,.0f}" if pd.notna(x) else '無資料')
        result_df['毛利'] = pivot_df.get('GrossProfit', pd.Series()).apply(lambda x: f"{x:,.0f}" if pd.notna(x) else '無資料')
        result_df['營業利益'] = pivot_df.get('OperatingIncome', pd.Series()).apply(lambda x: f"{x:,.0f}" if pd.notna(x) else '無資料')
        result_df['稅後淨利'] = pivot_df.get('NetIncome', pd.Series()).apply(lambda x: f"{x:,.0f}" if pd.notna(x) else '無資料')
        result_df['EPS'] = pivot_df.get('EPS', pd.Series()).apply(lambda x: f"{x:.2f}" if pd.notna(x) else '無資料')
        
        return result_df.reset_index(drop=True)
    
    def get_annual_financials(self):
        """獲取年度財務資料（近5年）"""
        conn = sqlite3.connect(self.db_path)
        
        # 獲取資產負債表和財務比率
        query_balance = """
            SELECT date, type, value
            FROM balance_sheets 
            WHERE stock_id = ? 
            AND type IN ('TotalAssets', 'TotalEquity', 'TotalLiabilities')
            ORDER BY date DESC
        """
        
        query_ratios = """
            SELECT date, roe, roa, gross_margin, operating_margin, net_margin
            FROM financial_ratios
            WHERE stock_id = ?
            ORDER BY date DESC
            LIMIT 5
        """

        try:
            df_balance = pd.read_sql_query(query_balance, conn, params=(self.stock_id,))
        except Exception:
            df_balance = pd.DataFrame()

        try:
            df_ratios = pd.read_sql_query(query_ratios, conn, params=(self.stock_id,))
        except Exception:
            df_ratios = pd.DataFrame()
        conn.close()
        
        # 處理資產負債表資料
        if not df_balance.empty:
            balance_pivot = df_balance.pivot_table(index='date', columns='type', values='value', aggfunc='first')
            balance_pivot = balance_pivot.head(5)
        else:
            balance_pivot = pd.DataFrame()
        
        # 合併資料
        result_df = pd.DataFrame()
        
        if not df_ratios.empty:
            result_df['年度'] = df_ratios['date']
            result_df['ROE(%)'] = df_ratios['roe'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '無資料')
            result_df['ROA(%)'] = df_ratios['roa'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '無資料')
            result_df['毛利率(%)'] = df_ratios['gross_margin'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '無資料')
            result_df['營業利益率(%)'] = df_ratios['operating_margin'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '無資料')
            result_df['淨利率(%)'] = df_ratios['net_margin'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '無資料')
        
        if not balance_pivot.empty:
            if 'TotalAssets' in balance_pivot.columns:
                result_df['總資產'] = balance_pivot['TotalAssets'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else '無資料')
            if 'TotalEquity' in balance_pivot.columns:
                result_df['股東權益'] = balance_pivot['TotalEquity'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else '無資料')
            if 'TotalLiabilities' in balance_pivot.columns:
                result_df['總負債'] = balance_pivot['TotalLiabilities'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else '無資料')
        
        if result_df.empty:
            return pd.DataFrame(columns=['年度', 'ROE(%)', 'ROA(%)', '毛利率(%)', '營業利益率(%)', '淨利率(%)', '總資產', '股東權益', '總負債'])
        
        return result_df.reset_index(drop=True)
    
    def get_dividend_policy(self):
        """獲取股利政策（近5年）"""
        conn = sqlite3.connect(self.db_path)

        # 先檢查表結構，使用實際的欄位名稱
        query = """
            SELECT date, year,
                   cash_earnings_distribution, stock_earnings_distribution,
                   cash_ex_dividend_trading_date, stock_ex_dividend_trading_date
            FROM dividend_policies
            WHERE stock_id = ?
            ORDER BY date DESC
            LIMIT 5
        """

        try:
            df = pd.read_sql_query(query, conn, params=(self.stock_id,))
        except Exception as e:
            # 如果上述查詢失敗，嘗試簡化查詢
            try:
                query_simple = """
                    SELECT date, year, cash_earnings_distribution, stock_earnings_distribution
                    FROM dividend_policies
                    WHERE stock_id = ?
                    ORDER BY date DESC
                    LIMIT 5
                """
                df = pd.read_sql_query(query_simple, conn, params=(self.stock_id,))
            except:
                conn.close()
                return pd.DataFrame(columns=['年度', '現金股利', '股票股利', '除息日', '除權日'])

        conn.close()

        if df.empty:
            return pd.DataFrame(columns=['年度', '現金股利', '股票股利', '除息日', '除權日'])

        # 格式化資料
        result_df = pd.DataFrame()
        result_df['年度'] = df['year'] if 'year' in df.columns else df['date']
        result_df['現金股利'] = df['cash_earnings_distribution'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else '無資料')
        result_df['股票股利'] = df['stock_earnings_distribution'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else '無資料')
        result_df['除息日'] = df.get('cash_ex_dividend_trading_date', pd.Series()).fillna('無資料')
        result_df['除權日'] = df.get('stock_ex_dividend_trading_date', pd.Series()).fillna('無資料')

        return result_df.reset_index(drop=True)
    
    def get_potential_analysis(self):
        """獲取潛力分析"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 先嘗試使用完整的欄位名稱
        try:
            query = """
                SELECT total_score, growth_score, profitability_score,
                       stability_score, valuation_score, dividend_score,
                       analysis_date
                FROM stock_scores
                WHERE stock_id = ?
                ORDER BY analysis_date DESC
                LIMIT 1
            """
            cursor.execute(query, (self.stock_id,))
            result = cursor.fetchone()
        except Exception:
            # 如果失敗，嘗試簡化查詢
            try:
                query_simple = """
                    SELECT total_score, growth_score, profitability_score,
                           analysis_date
                    FROM stock_scores
                    WHERE stock_id = ?
                    ORDER BY analysis_date DESC
                    LIMIT 1
                """
                cursor.execute(query_simple, (self.stock_id,))
                result = cursor.fetchone()
                if result:
                    # 補充缺失的欄位
                    result = result + (None, None, None)  # 補充3個None值
            except Exception:
                result = None

        conn.close()

        if not result:
            return {
                '總分': '無資料',
                '評等': '無資料',
                '成長潛力': '無資料',
                '獲利能力': '無資料',
                '穩定性': '無資料',
                '估值合理性': '無資料',
                '配息穩定性': '無資料',
                '分析日期': '無資料'
            }

        # 計算評等
        total_score = result[0]
        if total_score and total_score >= 85:
            grade = 'A+'
        elif total_score and total_score >= 75:
            grade = 'A'
        elif total_score and total_score >= 65:
            grade = 'B+'
        elif total_score and total_score >= 55:
            grade = 'B'
        elif total_score and total_score >= 45:
            grade = 'C+'
        elif total_score and total_score >= 35:
            grade = 'C'
        elif total_score:
            grade = 'D'
        else:
            grade = '無資料'

        # 安全的格式化函數
        def safe_format(value):
            if value is None:
                return '無資料'
            try:
                # 確保是數字類型
                if isinstance(value, (int, float)):
                    return f"{value:.1f}"
                elif isinstance(value, str):
                    try:
                        num_value = float(value)
                        return f"{num_value:.1f}"
                    except ValueError:
                        return '無資料'
                else:
                    return '無資料'
            except:
                return '無資料'

        return {
            '總分': safe_format(total_score),
            '評等': grade,
            '成長潛力': safe_format(result[1]) if len(result) > 1 else '無資料',
            '獲利能力': safe_format(result[2]) if len(result) > 2 else '無資料',
            '穩定性': safe_format(result[3]) if len(result) > 3 else '無資料',
            '估值合理性': safe_format(result[4]) if len(result) > 4 else '無資料',
            '配息穩定性': safe_format(result[5]) if len(result) > 5 else '無資料',
            '分析日期': result[-1] if result[-1] else '無資料'  # 使用最後一個元素作為日期
        }

    def generate_excel_report(self):
        """生成Excel報告"""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
            from openpyxl.utils.dataframe import dataframe_to_rows
            from openpyxl.chart import LineChart, Reference
        except ImportError:
            print("錯誤: 需要安裝 openpyxl 套件")
            print("請執行: pip install openpyxl")
            return False

        # 驗證股票代號
        is_valid, message = self.validate_stock_id()
        if not is_valid:
            print(f"錯誤: {message}")
            return False

        print(f"開始生成 {self.stock_id} 的財務分析報告...")

        # 收集所有資料
        basic_info = self.get_basic_info()
        monthly_revenue = self.get_monthly_revenue()
        quarterly_financials = self.get_quarterly_financials()
        annual_financials = self.get_annual_financials()
        dividend_policy = self.get_dividend_policy()
        potential_analysis = self.get_potential_analysis()

        # 創建Excel工作簿
        wb = openpyxl.Workbook()

        # 定義樣式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        center_alignment = Alignment(horizontal='center', vertical='center')

        # 1. 基本資訊工作表
        ws1 = wb.active
        ws1.title = "基本資訊"

        # 添加標題
        ws1['A1'] = f"{basic_info['股票名稱']} ({basic_info['股票代號']}) 基本資訊"
        ws1['A1'].font = Font(size=16, bold=True)
        ws1.merge_cells('A1:B1')

        # 添加基本資訊
        row = 3
        for key, value in basic_info.items():
            ws1[f'A{row}'] = key
            ws1[f'B{row}'] = value
            ws1[f'A{row}'].font = Font(bold=True)
            row += 1

        # 格式化
        for row in ws1.iter_rows(min_row=3, max_row=row-1, min_col=1, max_col=2):
            for cell in row:
                cell.border = border

        # 2. 月營收工作表
        ws2 = wb.create_sheet("月營收")
        ws2['A1'] = "近24個月營收資料"
        ws2['A1'].font = Font(size=14, bold=True)

        if not monthly_revenue.empty:
            # 添加表頭
            for col, header in enumerate(monthly_revenue.columns, 1):
                cell = ws2.cell(row=3, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = border

            # 添加資料
            for row_idx, row_data in enumerate(monthly_revenue.itertuples(index=False), 4):
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws2.cell(row=row_idx, column=col_idx, value=value)
                    cell.border = border
                    cell.alignment = center_alignment
        else:
            ws2['A3'] = "無月營收資料"

        # 3. 季度財務工作表
        ws3 = wb.create_sheet("季度財務")
        ws3['A1'] = "近8季財務資料"
        ws3['A1'].font = Font(size=14, bold=True)

        if not quarterly_financials.empty:
            # 添加表頭
            for col, header in enumerate(quarterly_financials.columns, 1):
                cell = ws3.cell(row=3, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = border

            # 添加資料
            for row_idx, row_data in enumerate(quarterly_financials.itertuples(index=False), 4):
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws3.cell(row=row_idx, column=col_idx, value=value)
                    cell.border = border
                    cell.alignment = center_alignment
        else:
            ws3['A3'] = "無季度財務資料"

        # 4. 年度財務工作表
        ws4 = wb.create_sheet("年度財務")
        ws4['A1'] = "近5年財務資料"
        ws4['A1'].font = Font(size=14, bold=True)

        if not annual_financials.empty:
            # 添加表頭
            for col, header in enumerate(annual_financials.columns, 1):
                cell = ws4.cell(row=3, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = border

            # 添加資料
            for row_idx, row_data in enumerate(annual_financials.itertuples(index=False), 4):
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws4.cell(row=row_idx, column=col_idx, value=value)
                    cell.border = border
                    cell.alignment = center_alignment
        else:
            ws4['A3'] = "無年度財務資料"

        # 5. 股利政策工作表
        ws5 = wb.create_sheet("股利政策")
        ws5['A1'] = "近5年股利政策"
        ws5['A1'].font = Font(size=14, bold=True)

        if not dividend_policy.empty:
            # 添加表頭
            for col, header in enumerate(dividend_policy.columns, 1):
                cell = ws5.cell(row=3, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = border

            # 添加資料
            for row_idx, row_data in enumerate(dividend_policy.itertuples(index=False), 4):
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws5.cell(row=row_idx, column=col_idx, value=value)
                    cell.border = border
                    cell.alignment = center_alignment
        else:
            ws5['A3'] = "無股利政策資料"

        # 6. 潛力分析工作表
        ws6 = wb.create_sheet("潛力分析")
        ws6['A1'] = "潛力股分析"
        ws6['A1'].font = Font(size=14, bold=True)

        # 添加潛力分析資料
        row = 3
        for key, value in potential_analysis.items():
            ws6[f'A{row}'] = key
            ws6[f'B{row}'] = value
            ws6[f'A{row}'].font = Font(bold=True)
            row += 1

        # 格式化潛力分析
        for row in ws6.iter_rows(min_row=3, max_row=row-1, min_col=1, max_col=2):
            for cell in row:
                cell.border = border

        # 調整欄寬 - 簡化版本避免錯誤
        for ws in [ws1, ws2, ws3, ws4, ws5, ws6]:
            try:
                # 設定固定的欄寬，避免複雜的計算
                for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                    try:
                        ws.column_dimensions[col].width = 15
                    except:
                        pass
            except:
                pass

        # 生成檔案名稱 - 避免特殊字符
        current_date = datetime.now().strftime("%Y%m%d")
        stock_name = basic_info.get('股票名稱', self.stock_id)
        # 移除可能造成檔名問題的字符
        safe_stock_name = "".join(c for c in stock_name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{self.stock_id}_{safe_stock_name}_財務分析報告_{current_date}.xlsx"

        # 儲存檔案
        try:
            wb.save(filename)
            print(f"✅ 報告生成成功: {filename}")
            print(f"📊 包含工作表: 基本資訊、月營收、季度財務、年度財務、股利政策、潛力分析")
            return True
        except Exception as e:
            print(f"❌ 儲存檔案時發生錯誤: {e}")
            # 嘗試使用簡化檔名
            try:
                simple_filename = f"{self.stock_id}_財務分析報告_{current_date}.xlsx"
                wb.save(simple_filename)
                print(f"✅ 報告生成成功: {simple_filename}")
                return True
            except Exception as e2:
                print(f"❌ 簡化檔名也失敗: {e2}")
                return False

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='生成股票財務分析報告')
    parser.add_argument('stock_id', help='股票代號 (例如: 2330, 0050)')

    args = parser.parse_args()

    # 創建報告生成器
    generator = StockReportGenerator(args.stock_id)

    # 生成報告
    success = generator.generate_excel_report()

    if success:
        print("\n🎉 財務分析報告生成完成！")
        print("📋 報告內容包括:")
        print("   • 基本資訊 (股票代號、名稱、市場、最新股價等)")
        print("   • 月營收 (近24個月營收及成長率)")
        print("   • 季度財務 (近8季損益表資料)")
        print("   • 年度財務 (近5年財務比率及資產負債)")
        print("   • 股利政策 (近5年配息配股記錄)")
        print("   • 潛力分析 (系統評分及各維度分析)")
        print("\n💡 Mac兼容性: 此腳本完全支援macOS，無編碼問題")
    else:
        print("\n❌ 報告生成失敗")
        print("💡 請檢查:")
        print("   • 股票代號是否正確")
        print("   • 是否已安裝 openpyxl: pip install openpyxl")
        print("   • 資料庫是否包含該股票的資料")

if __name__ == "__main__":
    main()

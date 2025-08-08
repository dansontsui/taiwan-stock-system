# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Database Manager
資料庫管理器
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from contextlib import contextmanager
from datetime import datetime

from config.settings import DATABASE_CONFIG
from src.utils.logger import get_logger, log_execution

logger = get_logger('database_manager')

class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DATABASE_CONFIG['path']
        self.timeout = DATABASE_CONFIG['timeout']
        self._validate_database()
    
    def _validate_database(self):
        """驗證資料庫是否存在且可訪問"""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['monthly_revenues', 'financial_statements', 'financial_ratios']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    logger.warning(f"Missing required tables: {missing_tables}")
                else:
                    logger.info(f"Database validation successful. Found {len(tables)} tables.")
                    
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """獲取資料庫連接 (上下文管理器)"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=DATABASE_CONFIG['check_same_thread']
            )
            conn.row_factory = sqlite3.Row  # 使結果可以按列名訪問
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @log_execution
    def get_monthly_revenue(self, stock_id: str, months: int = 12) -> pd.DataFrame:
        """
        獲取月營收資料
        
        Args:
            stock_id: 股票代碼
            months: 回看月數
            
        Returns:
            月營收DataFrame
        """
        query = """
        SELECT revenue_year, revenue_month, revenue, revenue_growth_yoy, revenue_growth_mom
        FROM monthly_revenues
        WHERE stock_id = ?
        ORDER BY revenue_year DESC, revenue_month DESC
        LIMIT ?
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[stock_id, months])
        
        if not df.empty:
            # 創建日期欄位 - 重新命名欄位以符合pandas要求
            df_date = df[['revenue_year', 'revenue_month']].copy()
            df_date.columns = ['year', 'month']
            df_date['day'] = 1
            df['date'] = pd.to_datetime(df_date)
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.log_data_collection(stock_id, 'monthly_revenue', len(df),
                                     f"{df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}")
        else:
            logger.warning(f"No monthly revenue data found for stock {stock_id}")
        
        return df

    def get_monthly_revenue_historical(self, stock_id: str, max_date: datetime = None,
                                     months: int = 12) -> pd.DataFrame:
        """
        獲取歷史時間點的月營收資料 (用於回測)

        Args:
            stock_id: 股票代碼
            max_date: 最大資料日期限制
            months: 回溯月數
        """
        try:
            # 構建查詢條件
            conditions = ["stock_id = ?"]
            params = [stock_id]

            if max_date:
                # 🔧 修復: 處理不同類型的max_date
                if isinstance(max_date, str):
                    # 如果是字串，轉換為datetime
                    from datetime import datetime
                    max_date = datetime.strptime(max_date, '%Y-%m-%d')

                # 轉換為年月格式進行比較
                max_year = max_date.year
                max_month = max_date.month
                conditions.append("(revenue_year < ? OR (revenue_year = ? AND revenue_month <= ?))")
                params.extend([max_year, max_year, max_month])

            # 查詢歷史資料
            query = f"""
            SELECT revenue_year, revenue_month, revenue, revenue_growth_yoy, revenue_growth_mom
            FROM monthly_revenues
            WHERE {' AND '.join(conditions)}
            ORDER BY revenue_year DESC, revenue_month DESC
            LIMIT ?
            """
            params.append(months)

            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)

            if not df.empty:
                # 創建日期欄位
                df_date = df[['revenue_year', 'revenue_month']].copy()
                df_date.columns = ['year', 'month']
                df_date['day'] = 1
                df['date'] = pd.to_datetime(df_date)
                df = df.sort_values('date').reset_index(drop=True)

                logger.info(f"[HISTORICAL_DATA] Retrieved {len(df)} historical revenue records | "
                           f"stock_id={stock_id} | max_date={max_date} | "
                           f"range={df['date'].min().strftime('%Y-%m')}~{df['date'].max().strftime('%Y-%m')}")
            else:
                logger.warning(f"No historical revenue data found for stock {stock_id} before {max_date}")

            return df

        except Exception as e:
            logger.error(f"Failed to get historical monthly revenue data: {e}")
            return pd.DataFrame()

    @log_execution
    def get_financial_ratios(self, stock_id: str, quarters: int = 8) -> pd.DataFrame:
        """
        獲取財務比率資料
        
        Args:
            stock_id: 股票代碼
            quarters: 回看季數
            
        Returns:
            財務比率DataFrame
        """
        query = """
        SELECT date, gross_margin, operating_margin, net_margin, roe, roa
        FROM financial_ratios
        WHERE stock_id = ?
        ORDER BY date DESC
        LIMIT ?
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[stock_id, quarters])
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.log_data_collection(stock_id, 'financial_ratios', len(df),
                                     f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        else:
            logger.warning(f"No financial ratios data found for stock {stock_id}")
        
        return df
    
    @log_execution
    def get_eps_data(self, stock_id: str, quarters: int = 8) -> pd.DataFrame:
        """
        獲取EPS資料
        
        Args:
            stock_id: 股票代碼
            quarters: 回看季數
            
        Returns:
            EPS DataFrame
        """
        query = """
        SELECT date, value as eps
        FROM financial_statements
        WHERE stock_id = ? AND type = 'EPS'
        ORDER BY date DESC
        LIMIT ?
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[stock_id, quarters])
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.log_data_collection(stock_id, 'eps_data', len(df),
                                     f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        else:
            logger.warning(f"No EPS data found for stock {stock_id}")
        
        return df
    
    @log_execution
    def get_stock_basic_info(self, stock_id: str) -> Dict:
        """
        獲取股票基本資訊
        
        Args:
            stock_id: 股票代碼
            
        Returns:
            股票基本資訊字典
        """
        query = """
        SELECT stock_id, stock_name, market, industry
        FROM stocks
        WHERE stock_id = ?
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [stock_id])
            result = cursor.fetchone()
        
        if result:
            return {
                'stock_id': result['stock_id'],
                'stock_name': result['stock_name'],
                'market': result['market'],
                'industry': result['industry'] if 'industry' in result.keys() else 'Unknown'
            }
        else:
            logger.warning(f"No basic info found for stock {stock_id}")
            return {}
    
    @log_execution
    def get_comprehensive_data(self, stock_id: str) -> Dict[str, pd.DataFrame]:
        """
        獲取股票的綜合資料
        
        Args:
            stock_id: 股票代碼
            
        Returns:
            包含各類資料的字典
        """
        logger.info(f"Collecting comprehensive data for stock {stock_id}")
        
        data = {
            'basic_info': self.get_stock_basic_info(stock_id),
            'monthly_revenue': self.get_monthly_revenue(stock_id, 24),  # 2年月營收
            'financial_ratios': self.get_financial_ratios(stock_id, 12),  # 3年季度比率
            'eps_data': self.get_eps_data(stock_id, 12)  # 3年EPS
        }
        
        # 檢查資料完整性
        data_quality = self._assess_data_quality(data)
        data['data_quality'] = data_quality
        
        logger.info(f"Comprehensive data collection completed for {stock_id}",
                   quality_score=data_quality['overall_score'])
        
        return data

    def get_comprehensive_data_historical(self, stock_id: str, max_date: datetime = None) -> Dict:
        """
        獲取股票的綜合歷史資料 (用於回測)

        Args:
            stock_id: 股票代碼
            max_date: 最大資料日期限制

        Returns:
            包含各類歷史資料的字典
        """
        logger.info(f"Collecting comprehensive historical data for stock {stock_id} | max_date={max_date}")

        data = {
            'basic_info': self.get_stock_basic_info(stock_id),
            'monthly_revenue': self.get_monthly_revenue_historical(stock_id, max_date, 24),  # 2年月營收
            'financial_ratios': self.get_financial_ratios(stock_id, 12),  # 3年季度比率 (暫時不限制)
            'eps_data': self.get_eps_data(stock_id, 12)  # 3年EPS (暫時不限制)
        }

        # 添加時間範圍資訊
        if not data['monthly_revenue'].empty:
            data['start_date'] = data['monthly_revenue']['date'].min().strftime('%Y-%m-%d')
            data['end_date'] = data['monthly_revenue']['date'].max().strftime('%Y-%m-%d')
            data['total_records'] = len(data['monthly_revenue'])
        else:
            data['start_date'] = None
            # 🔧 修復: 處理不同類型的max_date
            if max_date:
                if isinstance(max_date, str):
                    data['end_date'] = max_date
                else:
                    data['end_date'] = max_date.strftime('%Y-%m-%d')
            else:
                data['end_date'] = None
            data['total_records'] = 0

        # 檢查資料完整性
        data_quality = self._assess_data_quality(data)
        data['data_quality'] = data_quality

        logger.info(f"Historical comprehensive data collection completed for {stock_id} | "
                   f"records={data['total_records']} | quality={data_quality['overall_score']:.2%}")

        return data

    def _assess_data_quality(self, data: Dict) -> Dict:
        """評估資料品質"""
        quality = {
            'monthly_revenue_completeness': len(data['monthly_revenue']) / 24,  # 期望24個月
            'financial_ratios_completeness': len(data['financial_ratios']) / 12,  # 期望12季
            'eps_data_completeness': len(data['eps_data']) / 12,  # 期望12季
        }
        
        # 計算整體品質分數
        quality['overall_score'] = sum(min(score, 1.0) for score in quality.values()) / len(quality)
        
        # 品質等級
        if quality['overall_score'] >= 0.8:
            quality['grade'] = 'High'
        elif quality['overall_score'] >= 0.6:
            quality['grade'] = 'Medium'
        else:
            quality['grade'] = 'Low'
        
        return quality
    
    @log_execution
    def check_stock_exists(self, stock_id: str) -> bool:
        """檢查股票是否存在"""
        query = "SELECT 1 FROM stocks WHERE stock_id = ? LIMIT 1"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [stock_id])
            result = cursor.fetchone()
        
        exists = result is not None
        logger.debug(f"Stock {stock_id} exists: {exists}")
        return exists
    
    def get_available_stocks(self, limit: int = None) -> List[str]:
        """獲取可用的股票列表 (只包含有營收資料的股票)"""
        query = """
        SELECT DISTINCT s.stock_id
        FROM stocks s
        INNER JOIN monthly_revenues mr ON s.stock_id = mr.stock_id
        WHERE s.is_active = 1
        AND s.stock_id NOT LIKE '00%'  -- 排除ETF
        ORDER BY s.stock_id
        """

        if limit:
            query += f" LIMIT {limit}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            stocks = [row[0] for row in cursor.fetchall()]

        logger.info(f"Found {len(stocks)} available stocks with revenue data")
        return stocks

    @log_execution
    def get_monthly_revenue_data(self, stock_id: str, start_date: str = None,
                               end_date: str = None) -> pd.DataFrame:
        """
        獲取月營收歷史資料 (用於回測)

        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            包含歷史月營收的DataFrame
        """
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT
                        date,
                        revenue,
                        revenue_growth_yoy,
                        revenue_growth_mom
                    FROM monthly_revenues
                    WHERE stock_id = ?
                """
                params = [stock_id]

                if start_date:
                    query += " AND date >= ?"
                    params.append(start_date)

                if end_date:
                    query += " AND date <= ?"
                    params.append(end_date)

                query += " ORDER BY date"

                df = pd.read_sql_query(query, conn, params=params)

                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    logger.info(f"Retrieved {len(df)} monthly revenue records for {stock_id}")
                else:
                    logger.warning(f"No monthly revenue data found for {stock_id}")

                return df

        except Exception as e:
            logger.error(f"Failed to get monthly revenue data for {stock_id}: {e}")
            return pd.DataFrame()

    @log_execution
    def get_quarterly_financial_data(self, stock_id: str, start_quarter: str = None,
                                   end_quarter: str = None) -> pd.DataFrame:
        """
        獲取季度財務資料 (用於回測)

        Args:
            stock_id: 股票代碼
            start_quarter: 開始季度 (YYYY-Q)
            end_quarter: 結束季度 (YYYY-Q)

        Returns:
            包含歷史季度財務資料的DataFrame
        """
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT
                        date,
                        value as eps,
                        revenue,
                        net_income
                    FROM financial_statements
                    WHERE stock_id = ? AND type = 'EPS'
                """
                params = [stock_id]

                if start_quarter:
                    # 轉換季度格式 YYYY-Q 到日期格式
                    start_date = self._quarter_to_date(start_quarter)
                    if start_date:
                        query += " AND date >= ?"
                        params.append(start_date)

                if end_quarter:
                    # 轉換季度格式 YYYY-Q 到日期格式
                    end_date = self._quarter_to_date(end_quarter)
                    if end_date:
                        query += " AND date <= ?"
                        params.append(end_date)

                query += " ORDER BY date"

                df = pd.read_sql_query(query, conn, params=params)

                if not df.empty:
                    logger.info(f"Retrieved {len(df)} quarterly financial records for {stock_id}")
                else:
                    logger.warning(f"No quarterly financial data found for {stock_id}")

                return df

        except Exception as e:
            logger.error(f"Failed to get quarterly financial data for {stock_id}: {e}")
            return pd.DataFrame()

    @log_execution
    def get_historical_data_range(self, stock_id: str) -> Dict[str, str]:
        """
        獲取股票的歷史資料範圍

        Args:
            stock_id: 股票代碼

        Returns:
            包含資料範圍的字典
        """
        try:
            with self.get_connection() as conn:
                # 月營收資料範圍
                revenue_query = """
                    SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(*) as count
                    FROM monthly_revenues
                    WHERE stock_id = ?
                """
                revenue_result = pd.read_sql_query(revenue_query, conn, params=[stock_id])

                # 季度財務資料範圍
                financial_query = """
                    SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(DISTINCT date) as count
                    FROM financial_statements
                    WHERE stock_id = ? AND type = 'Revenue'
                """
                financial_result = pd.read_sql_query(financial_query, conn, params=[stock_id])

                data_range = {
                    'revenue_data': {
                        'min_date': revenue_result['min_date'].iloc[0] if not revenue_result.empty else None,
                        'max_date': revenue_result['max_date'].iloc[0] if not revenue_result.empty else None,
                        'count': revenue_result['count'].iloc[0] if not revenue_result.empty else 0
                    },
                    'financial_data': {
                        'min_date': financial_result['min_date'].iloc[0] if not financial_result.empty else None,
                        'max_date': financial_result['max_date'].iloc[0] if not financial_result.empty else None,
                        'count': financial_result['count'].iloc[0] if not financial_result.empty else 0
                    }
                }

                logger.info(f"Retrieved data range for {stock_id}")
                return data_range

        except Exception as e:
            logger.error(f"Failed to get historical data range for {stock_id}: {e}")
            return {}

    @log_execution
    def validate_backtest_data_availability(self, stock_id: str,
                                          required_revenue_months: int = 18,
                                          required_financial_quarters: int = 8) -> Dict[str, bool]:
        """
        驗證回測所需的資料是否充足

        Args:
            stock_id: 股票代碼
            required_revenue_months: 所需的月營收資料數量
            required_financial_quarters: 所需的季度財務資料數量

        Returns:
            驗證結果字典
        """
        try:
            data_range = self.get_historical_data_range(stock_id)

            revenue_sufficient = (
                data_range.get('revenue_data', {}).get('count', 0) >= required_revenue_months
            )

            financial_sufficient = (
                data_range.get('financial_data', {}).get('count', 0) >= required_financial_quarters
            )

            validation_result = {
                'revenue_data_sufficient': revenue_sufficient,
                'financial_data_sufficient': financial_sufficient,
                'backtest_feasible': revenue_sufficient and financial_sufficient,
                'revenue_count': data_range.get('revenue_data', {}).get('count', 0),
                'financial_count': data_range.get('financial_data', {}).get('count', 0),
                'required_revenue_months': required_revenue_months,
                'required_financial_quarters': required_financial_quarters
            }

            logger.info(f"Backtest data validation for {stock_id}: {validation_result}")
            return validation_result

        except Exception as e:
            logger.error(f"Failed to validate backtest data for {stock_id}: {e}")
            return {
                'revenue_data_sufficient': False,
                'financial_data_sufficient': False,
                'backtest_feasible': False,
                'error': str(e)
            }

    def _quarter_to_date(self, quarter_str: str) -> Optional[str]:
        """將季度字符串轉換為日期字符串"""
        try:
            if '-Q' in quarter_str:
                year, q = quarter_str.split('-Q')
                quarter = int(q)

                # 季度結束日期
                quarter_end_dates = {
                    1: f"{year}-03-31",
                    2: f"{year}-06-30",
                    3: f"{year}-09-30",
                    4: f"{year}-12-31"
                }

                return quarter_end_dates.get(quarter)

            return None

        except Exception as e:
            logger.warning(f"Failed to convert quarter to date: {e}")
            return None

if __name__ == "__main__":
    # 測試資料庫管理器
    db_manager = DatabaseManager()
    
    # 測試2385群光電子
    test_stock = "2385"
    
    print(f"Testing DatabaseManager with stock {test_stock}")
    
    # 檢查股票是否存在
    if db_manager.check_stock_exists(test_stock):
        print(f"✅ Stock {test_stock} exists")
        
        # 獲取綜合資料
        data = db_manager.get_comprehensive_data(test_stock)
        
        print(f"📊 Data Quality: {data['data_quality']['grade']} ({data['data_quality']['overall_score']:.2%})")
        print(f"📈 Monthly Revenue Records: {len(data['monthly_revenue'])}")
        print(f"📊 Financial Ratios Records: {len(data['financial_ratios'])}")
        print(f"💰 EPS Records: {len(data['eps_data'])}")
        
    else:
        print(f"❌ Stock {test_stock} not found")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料收集服務
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from loguru import logger
import json

class FinMindDataCollector:
    """FinMind 資料收集器"""
    
    def __init__(self, api_url: str = "https://api.finmindtrade.com/api/v4/data",
                 api_token: Optional[str] = None):
        self.api_url = api_url
        self.base_url = api_url  # 為了向後相容
        self.api_token = api_token
        self.session = requests.Session()
        
        # 設置請求頭
        if api_token:
            self.session.headers.update({'Authorization': f'Bearer {api_token}'})
        
        # 請求限制控制
        self.request_count = 0
        self.last_request_time = datetime.now()
        self.max_requests_per_hour = 300  # FinMind 免費版限制
    
    def _check_rate_limit(self):
        """檢查請求頻率限制"""
        current_time = datetime.now()
        
        # 如果超過一小時，重置計數器
        if (current_time - self.last_request_time).seconds > 3600:
            self.request_count = 0
            self.last_request_time = current_time
        
        # 如果接近限制，等待
        if self.request_count >= self.max_requests_per_hour - 10:
            wait_time = 3600 - (current_time - self.last_request_time).seconds
            if wait_time > 0:
                logger.warning(f"接近請求限制，等待 {wait_time} 秒")
                time.sleep(wait_time)
                self.request_count = 0
                self.last_request_time = datetime.now()
    
    def _make_request(self, dataset: str, data_id: str, start_date: str, 
                     end_date: str, **kwargs) -> Dict:
        """發送 API 請求"""
        self._check_rate_limit()
        
        params = {
            "dataset": dataset,
            "data_id": data_id,
            "start_date": start_date,
            "end_date": end_date,
            **kwargs
        }
        
        try:
            response = self.session.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            self.request_count += 1
            data = response.json()
            
            if 'data' not in data:
                logger.warning(f"API 回應異常: {data}")
                return {'data': []}
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API 請求失敗: {e}")
            return {'data': []}
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失敗: {e}")
            return {'data': []}
    
    def get_stock_price_data(self, stock_id: str, start_date: str, 
                           end_date: str) -> pd.DataFrame:
        """取得股價資料"""
        logger.info(f"收集股價資料: {stock_id} ({start_date} ~ {end_date})")
        
        data = self._make_request(
            dataset="TaiwanStockPrice",
            data_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not data['data']:
            logger.warning(f"股票 {stock_id} 無資料")
            return pd.DataFrame()
        
        df = pd.DataFrame(data['data'])
        
        # 資料清理和轉換
        df = self._clean_price_data(df)
        
        logger.info(f"股票 {stock_id} 收集到 {len(df)} 筆資料")
        return df
    
    def get_dividend_data(self, stock_id: str, start_date: str) -> pd.DataFrame:
        """取得配息資料"""
        logger.info(f"收集配息資料: {stock_id} (從 {start_date})")
        
        data = self._make_request(
            dataset="TaiwanStockDividend",
            data_id=stock_id,
            start_date=start_date,
            end_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        if not data['data']:
            return pd.DataFrame()
        
        df = pd.DataFrame(data['data'])
        df = self._clean_dividend_data(df)
        
        logger.info(f"股票 {stock_id} 收集到 {len(df)} 筆配息資料")
        return df
    
    def _clean_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清理股價資料"""
        if df.empty:
            return df
        
        # 重命名欄位
        column_mapping = {
            'date': 'date',
            'stock_id': 'stock_id',
            'open': 'open_price',
            'max': 'high_price',
            'min': 'low_price',
            'close': 'close_price',
            'Trading_Volume': 'volume',
            'Trading_money': 'trading_money',
            'Trading_turnover': 'trading_turnover',
            'spread': 'spread'
        }
        
        # 只保留需要的欄位
        available_columns = [col for col in column_mapping.keys() if col in df.columns]
        df = df[available_columns].copy()
        df.rename(columns=column_mapping, inplace=True)
        
        # 資料類型轉換
        numeric_columns = ['open_price', 'high_price', 'low_price', 'close_price', 
                          'volume', 'trading_money', 'trading_turnover', 'spread']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 日期轉換
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # 移除無效資料
        df = df.dropna(subset=['open_price', 'high_price', 'low_price', 'close_price'])
        df = df[df['volume'] > 0]  # 移除成交量為0的資料
        
        # 排序
        df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def _clean_dividend_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清理配息資料"""
        if df.empty:
            return df
        
        # 重命名欄位
        column_mapping = {
            'date': 'announce_date',
            'stock_id': 'stock_id',
            'CashExDividendTradingDate': 'ex_dividend_date',
            'CashDividendPaymentDate': 'payment_date',
            'CashEarningsDistribution': 'cash_dividend',
            'StockEarningsDistribution': 'stock_dividend'
        }
        
        available_columns = [col for col in column_mapping.keys() if col in df.columns]
        df = df[available_columns].copy()
        df.rename(columns=column_mapping, inplace=True)
        
        # 數值轉換
        for col in ['cash_dividend', 'stock_dividend']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 日期轉換
        date_columns = ['announce_date', 'ex_dividend_date', 'payment_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        
        # 只保留有配息的記錄
        df = df[(df['cash_dividend'] > 0) | (df['stock_dividend'] > 0)]
        
        return df
    
    def get_stock_list(self, use_full_list: bool = False) -> List[Dict[str, str]]:
        """取得股票清單

        Args:
            use_full_list: 是否使用完整股票清單 (從 FinMind API 獲取)
        """
        logger.info("收集股票清單...")

        if use_full_list:
            return self._get_full_stock_list()
        else:
            return self._get_predefined_stock_list()

    def _get_full_stock_list(self) -> List[Dict[str, str]]:
        """從 FinMind API 獲取完整股票清單"""
        logger.info("從 FinMind API 獲取完整股票清單...")
        stock_list = []

        try:
            # 獲取完整股票清單
            params = {
                'dataset': 'TaiwanStockInfo',
                'data_id': '',
                'start_date': '',
                'end_date': '',
                'token': self.api_token or ''
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    for item in data['data']:
                        # 過濾掉一些特殊股票
                        stock_id = item.get('stock_id', '')
                        stock_name = item.get('stock_name', '')
                        industry_category = item.get('industry_category', '')
                        stock_type = item.get('type', 'twse')  # twse 或 tpex

                        # 基本過濾條件
                        if (len(stock_id) >= 4 and
                            stock_name and
                            not stock_name.endswith('DR') and  # 排除存託憑證
                            not stock_name.endswith('-DR') and  # 排除存託憑證
                            '特' not in stock_name and  # 排除特別股
                            '權' not in stock_name and   # 排除權證
                            '購' not in stock_name and   # 排除認購權證
                            '售' not in stock_name):     # 排除認售權證

                            # 判斷是否為 ETF
                            is_etf = (stock_id.startswith('00') or
                                     'ETF' in stock_name.upper() or
                                     'ETN' in stock_name.upper() or
                                     industry_category == 'ETF')

                            # 判斷市場
                            market = 'TWSE' if stock_type == 'twse' else 'TPEX'

                            stock_list.append({
                                'stock_id': stock_id,
                                'stock_name': stock_name,
                                'market': market,
                                'is_etf': is_etf,
                                'industry_category': industry_category,
                                'type': stock_type
                            })

                logger.info(f"從 FinMind 獲取完整股票清單: {len(stock_list)} 檔")

        except Exception as e:
            logger.error(f"獲取完整股票清單失敗: {e}")
            logger.info("回退到預定義股票清單")
            return self._get_predefined_stock_list()

        # 如果獲取失敗或數量太少，回退到預定義清單
        if len(stock_list) < 100:
            logger.warning(f"獲取的股票數量過少 ({len(stock_list)} 檔)，回退到預定義清單")
            return self._get_predefined_stock_list()

        logger.info(f"完整股票清單收集完成，共 {len(stock_list)} 檔")
        return stock_list

    def _get_predefined_stock_list(self) -> List[Dict[str, str]]:
        """獲取預定義的精選股票清單"""
        logger.info("使用預定義股票清單...")
        stock_list = []

        # 主要上市股票
        major_stocks = [
            {'stock_id': '2330', 'stock_name': '台積電', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '2317', 'stock_name': '鴻海', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '2454', 'stock_name': '聯發科', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '2412', 'stock_name': '中華電', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '2882', 'stock_name': '國泰金', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '2891', 'stock_name': '中信金', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '2886', 'stock_name': '兆豐金', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '2303', 'stock_name': '聯電', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '2002', 'stock_name': '中鋼', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '1301', 'stock_name': '台塑', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '8299', 'stock_name': '群聯', 'market': 'TWSE', 'is_etf': False},
        ]

        # 主要 ETF
        major_etfs = [
            {'stock_id': '0050', 'stock_name': '元大台灣50', 'market': 'TWSE', 'is_etf': True},
            {'stock_id': '0056', 'stock_name': '元大高股息', 'market': 'TWSE', 'is_etf': True},
            {'stock_id': '006208', 'stock_name': '富邦台50', 'market': 'TWSE', 'is_etf': True},
            {'stock_id': '00878', 'stock_name': '國泰永續高股息', 'market': 'TWSE', 'is_etf': True},
            {'stock_id': '00881', 'stock_name': '國泰台灣5G+', 'market': 'TWSE', 'is_etf': True},
            {'stock_id': '00692', 'stock_name': '富邦公司治理', 'market': 'TWSE', 'is_etf': True},
            {'stock_id': '00713', 'stock_name': '元大台灣高息低波', 'market': 'TWSE', 'is_etf': True},
            {'stock_id': '00757', 'stock_name': '統一FANG+', 'market': 'TWSE', 'is_etf': True},
        ]

        # 上櫃股票 (實際上很多在 FinMind 中被歸類為上市)
        tpex_stocks = [
            {'stock_id': '6223', 'stock_name': '旺矽', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '4966', 'stock_name': '譜瑞-KY', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '3443', 'stock_name': '創意', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '6415', 'stock_name': '矽力-KY', 'market': 'TWSE', 'is_etf': False},
            {'stock_id': '4919', 'stock_name': '新唐', 'market': 'TWSE', 'is_etf': False},
        ]

        stock_list.extend(major_stocks)
        stock_list.extend(major_etfs)
        stock_list.extend(tpex_stocks)

        logger.info(f"預定義股票清單收集完成，共 {len(stock_list)} 檔")
        return stock_list
    
    def collect_batch_data(self, stock_list: List[Dict], start_date: str, 
                          end_date: str, batch_size: int = 10) -> Dict[str, pd.DataFrame]:
        """批量收集資料"""
        logger.info(f"開始批量收集資料: {len(stock_list)} 檔股票")
        
        all_price_data = {}
        all_dividend_data = {}
        
        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i + batch_size]
            logger.info(f"處理批次 {i//batch_size + 1}/{(len(stock_list)-1)//batch_size + 1}")
            
            for stock_info in batch:
                stock_id = stock_info['stock_id']
                
                try:
                    # 收集股價資料
                    price_df = self.get_stock_price_data(stock_id, start_date, end_date)
                    if not price_df.empty:
                        all_price_data[stock_id] = price_df
                    
                    # 如果是 ETF，收集配息資料
                    if stock_info.get('is_etf', False):
                        dividend_df = self.get_dividend_data(stock_id, start_date)
                        if not dividend_df.empty:
                            all_dividend_data[stock_id] = dividend_df
                    
                    # 避免請求過於頻繁
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"收集股票 {stock_id} 資料失敗: {e}")
                    continue
            
            # 批次間休息
            if i + batch_size < len(stock_list):
                logger.info("批次間休息 5 秒...")
                time.sleep(5)
        
        logger.info(f"批量收集完成: 股價資料 {len(all_price_data)} 檔, 配息資料 {len(all_dividend_data)} 檔")
        
        return {
            'price_data': all_price_data,
            'dividend_data': all_dividend_data
        }

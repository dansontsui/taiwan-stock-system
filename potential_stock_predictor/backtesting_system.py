#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
潛力股預測系統 - 回測框架
實現滾動窗口回測，模擬真實交易環境
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
import json

# 添加專案路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from src.utils.database import DatabaseManager
from src.features.feature_engineering import FeatureEngineer
from src.features.target_generator import TargetGenerator
import pickle

# 設置日誌 - 使用 UTF-8 編碼支援中文顯示
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backtesting.log', encoding='utf-8')
    ]
)

class BacktestingSystem:
    """回測系統"""
    
    def __init__(self, db_manager, train_start_date='2016-01-01', train_end_date='2023-12-31',
                 backtest_start_date='2024-01-31', backtest_end_date='2024-10-31'):
        self.db_manager = db_manager
        self.feature_engineer = FeatureEngineer(db_manager)
        self.target_generator = TargetGenerator(db_manager)

        # 回測配置 - 可自訂日期
        self.config = {
            'train_start_date': train_start_date,
            'train_end_date': train_end_date,
            'backtest_start_date': backtest_start_date,
            'backtest_end_date': backtest_end_date,
            'rebalance_frequency': 'quarterly',  # monthly, quarterly
            'prediction_horizon': 20,  # 預測天數
            'top_n_stocks': 20,  # 選擇前N檔股票
            'min_prediction_prob': 0.6,  # 最低預測機率
            'use_simple_features': True  # 使用簡易特徵
        }

        # 初始化回測結果儲存
        self.backtest_results = []
        self.portfolio_performance = []

    def clean_feature_data(self, X, feature_cols, log_prefix=""):
        """清理特徵資料，處理無限值和異常值"""
        logging.info(f"{log_prefix}資料清理前: {X.shape}")

        # 1. 處理缺失值
        X = X.fillna(0)

        # 2. 處理無限值
        X = X.replace([np.inf, -np.inf], 0)

        # 3. 處理過大的數值
        max_val = np.finfo(np.float64).max / 1000
        min_val = np.finfo(np.float64).min / 1000
        X = X.clip(lower=min_val, upper=max_val)

        # 4. 檢查是否還有問題值
        if not np.isfinite(X.values).all():
            logging.warning(f"{log_prefix}資料中仍有非有限值，進行最終清理")
            X = X.fillna(0)
            X = X.replace([np.inf, -np.inf], 0)

        # 5. 移除方差為0的特徵
        variance = X.var()
        zero_var_cols = variance[variance == 0].index.tolist()
        if zero_var_cols:
            logging.info(f"{log_prefix}移除零方差特徵: {len(zero_var_cols)} 個")
            X = X.drop(columns=zero_var_cols)
            feature_cols = [col for col in feature_cols if col not in zero_var_cols]

        logging.info(f"{log_prefix}資料清理後: {X.shape}")

        return X, feature_cols
        
    def generate_rebalance_dates(self):
        """生成再平衡日期"""
        start_date = pd.to_datetime(self.config['backtest_start_date'])
        end_date = pd.to_datetime(self.config['backtest_end_date'])
        
        if self.config['rebalance_frequency'] == 'monthly':
            dates = pd.date_range(start=start_date, end=end_date, freq='ME')
        elif self.config['rebalance_frequency'] == 'quarterly':
            dates = pd.date_range(start=start_date, end=end_date, freq='QE')
        else:
            raise ValueError(f"不支援的頻率: {self.config['rebalance_frequency']}")
        
        return [date.strftime('%Y-%m-%d') for date in dates]
    
    def get_available_stocks(self, date):
        """獲取指定日期可用的股票清單"""
        query = """
        SELECT DISTINCT stock_id
        FROM stock_prices
        WHERE date <= ?
        AND stock_id GLOB '[0-9][0-9][0-9][0-9]'
        AND stock_id NOT LIKE '00%'
        ORDER BY stock_id
        """

        with self.db_manager.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[date])

        stock_list = df['stock_id'].tolist()

        # 過濾掉可能有問題的股票範圍
        problematic_ranges = [
            #('1200', '1299'),  # 12xx 範圍
            #('1400', '1499'),  # 14xx 範圍
        ]

        filtered_stocks = []
        skipped_count = 0

        for stock_id in stock_list:
            skip_stock = False
            for start_range, end_range in problematic_ranges:
                if start_range <= stock_id <= end_range:
                    skip_stock = True
                    skipped_count += 1
                    break

            if not skip_stock:
                filtered_stocks.append(stock_id)

        if skipped_count > 0:
            logging.info(f"跳過可能有問題的股票: {skipped_count} 檔 (12xx, 14xx 範圍)")

        logging.info(f"可用股票數量: {len(filtered_stocks)} 檔 (原始: {len(stock_list)} 檔)")
        return filtered_stocks
    
    def generate_features_for_date(self, date, stock_ids):
        """為指定日期生成特徵"""
        logging.info(f"[CHART] 開始生成 {date} 的特徵資料，股票數量: {len(stock_ids)}")

        # 顯示股票範圍
        if stock_ids:
            logging.info(f"[LIST] 股票範圍: {stock_ids[0]} ~ {stock_ids[-1]}")

        all_features = []
        failed_stocks = []
        slow_stocks = []  # 記錄處理慢的股票

        for i, stock_id in enumerate(stock_ids):
            # 更頻繁的進度報告 - 每20檔顯示一次
            if (i + 1) % 20 == 0:
                progress_pct = (i + 1) / len(stock_ids) * 100
                logging.info(f"[PROGRESS] 特徵生成進度: {i+1}/{len(stock_ids)} ({progress_pct:.1f}%) - 當前: {stock_id}")

            # 每5個股票顯示當前處理的股票 (更頻繁)
            if (i + 1) % 5 == 0:
                logging.info(f"[PROCESS] 正在處理: {stock_id} ({i+1}/{len(stock_ids)})")

            try:
                # 記錄開始時間
                import time
                start_time = time.time()

                features = self.feature_engineer.generate_features(stock_id, date)

                # 檢查處理時間
                elapsed_time = time.time() - start_time
                if elapsed_time > 5:  # 超過5秒記錄為慢股票
                    slow_stocks.append((stock_id, elapsed_time))
                    if elapsed_time > 10:  # 超過10秒警告
                        logging.warning(f"[SLOW] 股票 {stock_id} 特徵生成耗時 {elapsed_time:.1f} 秒 (可能資料複雜)")

                if features is not None and not features.empty:
                    all_features.append(features)
                else:
                    logging.debug(f"股票 {stock_id} 沒有特徵資料")
                    failed_stocks.append(stock_id)

            except TimeoutError as e:
                logging.error(f"[TIMEOUT] {e}")
                failed_stocks.append(stock_id)
                continue
            except Exception as e:
                logging.warning(f"生成 {stock_id} 特徵失敗: {e}")
                failed_stocks.append(stock_id)
                continue

        # 報告處理結果
        if slow_stocks:
            slow_count = len(slow_stocks)
            avg_time = sum(time for _, time in slow_stocks) / slow_count
            logging.info(f"[SLOW] 處理較慢的股票: {slow_count} 檔，平均耗時 {avg_time:.1f} 秒")

        if failed_stocks:
            logging.warning(f"[FAIL] 特徵生成失敗: {len(failed_stocks)} 檔 - {failed_stocks[:5]}{'...' if len(failed_stocks) > 5 else ''}")

        if all_features:
            result = pd.concat(all_features, ignore_index=True)
            success_rate = (len(stock_ids) - len(failed_stocks)) / len(stock_ids) * 100
            logging.info(f"[SUCCESS] {date} 特徵生成完成: {len(result)} 筆資料，成功率 {success_rate:.1f}%")
            return result
        else:
            logging.warning(f"[WARN] {date} 沒有生成任何特徵 (失敗: {len(failed_stocks)} 檔)")
            return pd.DataFrame()
    
    def train_model_for_period(self, train_end_date):
        """為指定期間訓練模型 - 修正順序：先特徵後目標變數"""
        logging.info(f"訓練模型，資料截止: {train_end_date}")

        # 1. 先獲取可用股票
        stock_ids = self.get_available_stocks(train_end_date)
        limited_stocks = stock_ids[:100]  # 限制數量以加快速度
        logging.info(f"選擇 {len(limited_stocks)} 檔股票進行訓練")

        # 2. 生成特徵日期序列（季度頻率）
        start_date = pd.to_datetime(self.config['train_start_date'])
        end_date = pd.to_datetime(train_end_date)
        feature_dates = pd.date_range(start=start_date, end=end_date, freq='QE')
        feature_dates = [date.strftime('%Y-%m-%d') for date in feature_dates]

        logging.info(f"特徵生成日期: {len(feature_dates)} 個季度")

        # 3. 先生成所有特徵資料
        all_features = []
        for date_idx, date in enumerate(feature_dates):
            logging.info(f"[QUARTER] 生成特徵: {date} ({date_idx+1}/{len(feature_dates)} 季度)")
            logging.info(f"[INFO] 當前季度將處理 {len(limited_stocks)} 檔股票")

            features = self.generate_features_for_date(date, limited_stocks)
            if not features.empty:
                all_features.append(features)
                logging.info(f"[COMPLETE] {date} 特徵生成完成，獲得 {len(features)} 筆資料")
            else:
                logging.warning(f"[WARN] {date} 沒有生成任何特徵資料")

        if not all_features:
            logging.error("沒有特徵資料")
            return None

        features_df = pd.concat(all_features, ignore_index=True)
        logging.info(f"特徵資料生成完成: {len(features_df)} 筆")

        # 4. 再根據特徵資料生成對應的目標變數
        targets_df = self.target_generator.create_time_series_targets(
            stock_ids=limited_stocks,
            start_date=self.config['train_start_date'],
            end_date=train_end_date,
            frequency='quarterly'
        )

        if targets_df.empty:
            logging.error("沒有目標變數資料")
            return None

        logging.info(f"目標變數生成完成: {len(targets_df)} 筆")
        
        # 合併特徵和目標變數
        merged_df = pd.merge(
            features_df,
            targets_df[['stock_id', 'feature_date', 'target']],
            on=['stock_id', 'feature_date'],
            how='inner'
        )
        
        if merged_df.empty:
            logging.error("合併後沒有資料")
            return None
        
        # 訓練模型
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        
        # 準備訓練資料
        feature_cols = [col for col in merged_df.columns
                       if col not in ['stock_id', 'feature_date', 'target']]

        X = merged_df[feature_cols].copy()
        y = merged_df['target']

        # 使用統一的資料清理方法
        X, feature_cols = self.clean_feature_data(X, feature_cols)

        # 標準化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # 訓練模型
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_scaled, y)
        
        logging.info(f"模型訓練完成，訓練樣本: {len(X)}")
        
        return {
            'model': model,
            'scaler': scaler,
            'feature_cols': feature_cols,
            'train_end_date': train_end_date
        }
    
    def make_predictions(self, model_info, prediction_date):
        """進行預測"""
        logging.info(f"執行預測，日期: {prediction_date}")
        
        # 獲取可用股票
        stock_ids = self.get_available_stocks(prediction_date)
        
        # 生成特徵
        features_df = self.generate_features_for_date(prediction_date, stock_ids)
        
        if features_df.empty:
            logging.warning(f"{prediction_date} 沒有特徵資料")
            return pd.DataFrame()
        
        # 準備預測資料 - 使用完整的資料清理
        X = features_df[model_info['feature_cols']].copy()
        X, cleaned_feature_cols = self.clean_feature_data(X, model_info['feature_cols'], "[PREDICT] ")

        # 確保特徵欄位一致
        if set(cleaned_feature_cols) != set(model_info['feature_cols']):
            logging.warning(f"[PREDICT] 特徵欄位不一致，調整中...")
            # 如果清理後的特徵少了，用0填充
            for col in model_info['feature_cols']:
                if col not in cleaned_feature_cols:
                    X[col] = 0
            X = X[model_info['feature_cols']]

        X_scaled = model_info['scaler'].transform(X)
        
        # 預測
        predictions = model_info['model'].predict_proba(X_scaled)[:, 1]
        
        # 組合結果
        results = pd.DataFrame({
            'stock_id': features_df['stock_id'],
            'prediction_date': prediction_date,
            'prediction_prob': predictions
        })
        
        # 篩選高機率股票
        results = results[
            results['prediction_prob'] >= self.config['min_prediction_prob']
        ].sort_values('prediction_prob', ascending=False)
        
        # 選擇前N檔
        top_stocks = results.head(self.config['top_n_stocks'])
        
        logging.info(f"{prediction_date} 預測完成，選出 {len(top_stocks)} 檔股票")
        
        return top_stocks
    
    def calculate_returns(self, predictions, start_date, end_date):
        """計算預測期間的報酬率"""
        if predictions.empty:
            return pd.DataFrame()
        
        returns = []
        
        for _, row in predictions.iterrows():
            stock_id = row['stock_id']
            
            # 獲取股價資料
            query = """
            SELECT date, close_price 
            FROM stock_prices 
            WHERE stock_id = ? 
            AND date BETWEEN ? AND ?
            ORDER BY date
            """
            
            with self.db_manager.get_connection() as conn:
                price_df = pd.read_sql_query(
                    query, conn, 
                    params=[stock_id, start_date, end_date]
                )
            
            if len(price_df) >= 2:
                start_price = price_df.iloc[0]['close_price']
                end_price = price_df.iloc[-1]['close_price']
                
                if start_price > 0:
                    return_pct = (end_price - start_price) / start_price * 100
                    
                    returns.append({
                        'stock_id': stock_id,
                        'prediction_prob': row['prediction_prob'],
                        'start_price': start_price,
                        'end_price': end_price,
                        'return_pct': return_pct,
                        'start_date': start_date,
                        'end_date': end_date
                    })
        
        return pd.DataFrame(returns)
    
    def run_backtest(self):
        """執行完整回測"""
        logging.info("開始執行回測")
        logging.info(f"回測配置: {self.config}")
        
        # 生成再平衡日期
        rebalance_dates = self.generate_rebalance_dates()
        logging.info(f"再平衡日期: {rebalance_dates}")
        
        model_info = None
        
        for i, rebalance_date in enumerate(rebalance_dates):
            logging.info(f"處理再平衡日期 {i+1}/{len(rebalance_dates)}: {rebalance_date}")
            
            # 重新訓練模型（使用截至當前日期的資料）
            train_end_date = (pd.to_datetime(rebalance_date) - timedelta(days=1)).strftime('%Y-%m-%d')
            model_info = self.train_model_for_period(train_end_date)
            
            if model_info is None:
                logging.error(f"模型訓練失敗: {rebalance_date}")
                continue
            
            # 進行預測
            predictions = self.make_predictions(model_info, rebalance_date)
            
            if predictions.empty:
                logging.warning(f"沒有預測結果: {rebalance_date}")
                continue
            
            # 計算持有期間的報酬率
            hold_start_date = rebalance_date
            if i < len(rebalance_dates) - 1:
                hold_end_date = rebalance_dates[i + 1]
            else:
                hold_end_date = self.config['backtest_end_date']
            
            returns = self.calculate_returns(predictions, hold_start_date, hold_end_date)
            
            # 記錄結果
            period_result = {
                'rebalance_date': rebalance_date,
                'hold_start_date': hold_start_date,
                'hold_end_date': hold_end_date,
                'predictions': predictions,
                'returns': returns,
                'avg_return': returns['return_pct'].mean() if not returns.empty else 0,
                'success_rate': (returns['return_pct'] > 0).mean() if not returns.empty else 0
            }
            
            self.backtest_results.append(period_result)
            
            logging.info(f"期間 {hold_start_date} ~ {hold_end_date}:")
            logging.info(f"  平均報酬率: {period_result['avg_return']:.2f}%")
            logging.info(f"  成功率: {period_result['success_rate']:.2%}")
        
        # 生成總結報告
        self.generate_backtest_report()
    
    def generate_backtest_report(self):
        """生成回測報告"""
        logging.info("生成回測報告")
        
        if not self.backtest_results:
            logging.error("沒有回測結果")
            return
        
        # 計算整體統計
        all_returns = []
        for result in self.backtest_results:
            if not result['returns'].empty:
                all_returns.extend(result['returns']['return_pct'].tolist())
        
        if not all_returns:
            logging.error("沒有報酬率資料")
            return
        
        overall_stats = {
            'total_periods': len(self.backtest_results),
            'avg_return_per_period': np.mean([r['avg_return'] for r in self.backtest_results]),
            'overall_avg_return': np.mean(all_returns),
            'overall_success_rate': np.mean([r > 0 for r in all_returns]),
            'volatility': np.std(all_returns),
            'max_return': np.max(all_returns),
            'min_return': np.min(all_returns),
            'sharpe_ratio': np.mean(all_returns) / np.std(all_returns) if np.std(all_returns) > 0 else 0
        }
        
        # 保存報告
        report = {
            'config': self.config,
            'overall_stats': overall_stats,
            'period_results': []
        }
        
        for result in self.backtest_results:
            period_summary = {
                'rebalance_date': result['rebalance_date'],
                'hold_period': f"{result['hold_start_date']} ~ {result['hold_end_date']}",
                'num_stocks': len(result['predictions']),
                'avg_return': result['avg_return'],
                'success_rate': result['success_rate']
            }
            report['period_results'].append(period_summary)
        
        # 保存到檔案 - 使用 ASCII 編碼確保跨平台兼容性
        report_file = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='ascii', errors='replace') as f:
            json.dump(report, f, ensure_ascii=True, indent=2)
        
        logging.info(f"回測報告已保存: {report_file}")
        
        # 顯示總結
        print("\n" + "="*60)
        print("回測結果總結")
        print("="*60)
        print(f"回測期間: {self.config['backtest_start_date']} ~ {self.config['backtest_end_date']}")
        print(f"再平衡頻率: {self.config['rebalance_frequency']}")
        print(f"總期間數: {overall_stats['total_periods']}")
        print(f"平均報酬率: {overall_stats['overall_avg_return']:.2f}%")
        print(f"成功率: {overall_stats['overall_success_rate']:.2%}")
        print(f"波動率: {overall_stats['volatility']:.2f}%")
        print(f"夏普比率: {overall_stats['sharpe_ratio']:.3f}")
        print(f"最大報酬: {overall_stats['max_return']:.2f}%")
        print(f"最大虧損: {overall_stats['min_return']:.2f}%")

    def train_model_for_single_stock_only(self, train_end_date, target_stock_id):
        """為單一個股訓練模型 - 真正只使用該股票的資料"""
        logging.info(f"[TARGET] 純單一個股訓練：{target_stock_id}，資料截止: {train_end_date}")

        # 只使用目標股票
        training_stocks = [target_stock_id]

        # 生成特徵日期序列（季度頻率）
        start_date = pd.to_datetime(self.config['train_start_date'])
        end_date = pd.to_datetime(train_end_date)
        feature_dates = pd.date_range(start=start_date, end=end_date, freq='QE')
        feature_dates = [date.strftime('%Y-%m-%d') for date in feature_dates]

        logging.info(f"[TARGET] 只為 {target_stock_id} 生成特徵，日期數: {len(feature_dates)}")

        # 只為目標股票生成特徵
        all_features = []
        for date in feature_dates:
            logging.info(f"[TARGET] 生成 {target_stock_id} 在 {date} 的特徵")
            try:
                features = self.feature_engineer.generate_features(target_stock_id, date)
                if features is not None and not features.empty:
                    features['feature_date'] = date
                    features['stock_id'] = target_stock_id
                    all_features.append(features)
                else:
                    logging.warning(f"[TARGET] {target_stock_id} 在 {date} 無法生成特徵")
            except Exception as e:
                logging.warning(f"[TARGET] {target_stock_id} 在 {date} 特徵生成失敗: {e}")

        if not all_features:
            logging.error(f"[TARGET] {target_stock_id} 沒有任何特徵資料")
            return None

        features_df = pd.concat(all_features, ignore_index=True)
        logging.info(f"[TARGET] {target_stock_id} 特徵資料生成完成: {len(features_df)} 筆")

        # 只為目標股票生成目標變數
        targets_df = self.target_generator.create_time_series_targets(
            stock_ids=[target_stock_id],
            start_date=self.config['train_start_date'],
            end_date=train_end_date,
            frequency='quarterly'
        )

        if targets_df.empty:
            logging.error(f"[TARGET] {target_stock_id} 沒有目標變數資料")
            return None

        logging.info(f"[TARGET] {target_stock_id} 目標變數生成完成: {len(targets_df)} 筆")

        # 合併特徵和目標變數
        merged_df = pd.merge(
            features_df,
            targets_df[['stock_id', 'feature_date', 'target']],
            on=['stock_id', 'feature_date'],
            how='inner'
        )

        if merged_df.empty:
            logging.error(f"[TARGET] {target_stock_id} 合併後沒有資料")
            return None

        if len(merged_df) < 10:
            logging.warning(f"[TARGET] {target_stock_id} 訓練樣本太少: {len(merged_df)} 筆，可能影響模型品質")

        # 訓練模型
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler

        # 準備訓練資料
        feature_cols = [col for col in merged_df.columns
                       if col not in ['stock_id', 'feature_date', 'target']]

        X = merged_df[feature_cols].copy()
        y = merged_df['target']

        # 使用統一的資料清理方法
        X, feature_cols = self.clean_feature_data(X, feature_cols, "[TARGET] ")

        # 標準化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 訓練模型
        model = RandomForestClassifier(n_estimators=50, random_state=42)  # 減少樹的數量
        model.fit(X_scaled, y)

        logging.info(f"[TARGET] {target_stock_id} 純單股模型訓練完成，訓練樣本: {len(X)}")

        return {
            'model': model,
            'scaler': scaler,
            'feature_cols': feature_cols,
            'train_end_date': train_end_date,
            'target_stock_id': target_stock_id,
            'training_mode': 'single_stock_only'
        }

    def train_model_for_single_stock_mixed(self, train_end_date, target_stock_id):
        """為單一個股訓練模型 - 混合模式（多股票訓練，單股票預測）"""
        logging.info(f"[REFRESH] 混合模式訓練：目標 {target_stock_id}，資料截止: {train_end_date}")

        # 獲取相關股票（包含目標股票和一些相似股票）
        stock_ids = self.get_available_stocks(train_end_date)

        # 確保目標股票在列表中
        if target_stock_id not in stock_ids:
            logging.error(f"目標股票 {target_stock_id} 在 {train_end_date} 不可用")
            return None

        # 選擇訓練股票：目標股票 + 前20檔股票（減少訓練時間）
        training_stocks = [target_stock_id]
        other_stocks = [s for s in stock_ids[:20] if s != target_stock_id]
        training_stocks.extend(other_stocks)

        logging.info(f"[REFRESH] 混合訓練：目標股票 {target_stock_id}，總訓練股票 {len(training_stocks)} 檔")

        # 使用原本的訓練方法（但股票數量減少）
        return self.train_model_for_period(train_end_date, custom_stocks=training_stocks)

    def run_single_stock_backtest(self, stock_id, training_mode='pure'):
        """執行單一個股回測

        Args:
            stock_id: 股票代號
            training_mode: 訓練模式
                - 'pure': 純單一個股訓練（只用該股票資料）
                - 'mixed': 混合模式（多股票訓練，單股票預測）
        """
        logging.info(f"開始執行單一個股回測: {stock_id}, 訓練模式: {training_mode}")

        # 檢查股票是否存在
        if not self.check_stock_exists(stock_id):
            print(f"[ERROR] 股票 {stock_id} 不存在或資料不足")
            return

        print(f"\n[CHART] 執行 {stock_id} 個股回測")
        print(f"[TARGET] 訓練模式: {'純單一個股' if training_mode == 'pure' else '混合模式'}")
        print("="*60)

        # 生成再平衡日期
        rebalance_dates = self.generate_rebalance_dates()

        single_stock_results = []

        for i, rebalance_date in enumerate(rebalance_dates):
            print(f"處理日期 {i+1}/{len(rebalance_dates)}: {rebalance_date}")

            # 根據訓練模式選擇不同的訓練方法
            train_end_date = (pd.to_datetime(rebalance_date) - timedelta(days=1)).strftime('%Y-%m-%d')

            if training_mode == 'pure':
                model_info = self.train_model_for_single_stock_only(train_end_date, stock_id)
            else:
                model_info = self.train_model_for_single_stock_mixed(train_end_date, stock_id)

            if model_info is None:
                print(f"  [ERROR] 模型訓練失敗")
                continue

            # 為單一股票生成特徵並預測
            features = self.generate_features_for_date(rebalance_date, [stock_id])

            if features.empty:
                print(f"  [ERROR] 無法生成特徵")
                continue

            # 預測 - 使用完整的資料清理
            X = features[model_info['feature_cols']].copy()
            X, cleaned_feature_cols = self.clean_feature_data(X, model_info['feature_cols'], f"[SINGLE-{stock_id}] ")

            # 確保特徵欄位一致
            if set(cleaned_feature_cols) != set(model_info['feature_cols']):
                # 如果清理後的特徵少了，用0填充
                for col in model_info['feature_cols']:
                    if col not in cleaned_feature_cols:
                        X[col] = 0
                X = X[model_info['feature_cols']]

            X_scaled = model_info['scaler'].transform(X)
            prediction_prob = model_info['model'].predict_proba(X_scaled)[0, 1]

            # 計算持有期間報酬
            hold_start_date = rebalance_date
            if i < len(rebalance_dates) - 1:
                hold_end_date = rebalance_dates[i + 1]
            else:
                hold_end_date = self.config['backtest_end_date']

            # 獲取實際報酬率
            actual_return = self.get_stock_return(stock_id, hold_start_date, hold_end_date)

            result = {
                'date': rebalance_date,
                'stock_id': stock_id,
                'prediction_prob': prediction_prob,
                'actual_return': actual_return,
                'hold_period': f"{hold_start_date} ~ {hold_end_date}",
                'prediction_correct': (prediction_prob > 0.5 and actual_return > 0) or (prediction_prob <= 0.5 and actual_return <= 0)
            }

            single_stock_results.append(result)

            print(f"  預測機率: {prediction_prob:.3f}")
            print(f"  實際報酬: {actual_return:.2f}%")
            print(f"  預測正確: {'[OK]' if result['prediction_correct'] else '[ERROR]'}")

        # 生成單股回測報告
        self.generate_single_stock_report(stock_id, single_stock_results)

    def check_stock_exists(self, stock_id):
        """檢查股票是否存在足夠的資料"""
        query = """
        SELECT COUNT(*) as count
        FROM stock_prices
        WHERE stock_id = ?
        AND date >= ?
        AND date <= ?
        """

        with self.db_manager.get_connection() as conn:
            result = pd.read_sql_query(
                query, conn,
                params=[stock_id, self.config['train_start_date'], self.config['backtest_end_date']]
            )

        return result.iloc[0]['count'] > 100  # 至少要有100筆資料

    def get_stock_return(self, stock_id, start_date, end_date):
        """計算股票在指定期間的報酬率"""
        query = """
        SELECT date, close_price
        FROM stock_prices
        WHERE stock_id = ?
        AND date BETWEEN ? AND ?
        ORDER BY date
        """

        with self.db_manager.get_connection() as conn:
            price_df = pd.read_sql_query(query, conn, params=[stock_id, start_date, end_date])

        if len(price_df) >= 2:
            start_price = price_df.iloc[0]['close_price']
            end_price = price_df.iloc[-1]['close_price']

            if start_price > 0:
                return (end_price - start_price) / start_price * 100

        return 0.0

    def generate_single_stock_report(self, stock_id, results):
        """生成單一個股回測報告"""
        if not results:
            print("[ERROR] 沒有回測結果")
            return

        # 計算統計數據
        returns = [r['actual_return'] for r in results]
        predictions = [r['prediction_prob'] for r in results]
        correct_predictions = [r['prediction_correct'] for r in results]

        stats = {
            'stock_id': stock_id,
            'total_periods': len(results),
            'avg_return': np.mean(returns),
            'total_return': sum(returns),
            'volatility': np.std(returns),
            'max_return': max(returns),
            'min_return': min(returns),
            'accuracy': np.mean(correct_predictions),
            'avg_prediction_prob': np.mean(predictions)
        }

        # 顯示結果
        print(f"\n[UP] {stock_id} 個股回測結果")
        print("="*60)
        print(f"回測期間數: {stats['total_periods']}")
        print(f"平均報酬率: {stats['avg_return']:.2f}%")
        print(f"累積報酬率: {stats['total_return']:.2f}%")
        print(f"報酬波動率: {stats['volatility']:.2f}%")
        print(f"最大報酬: {stats['max_return']:.2f}%")
        print(f"最大虧損: {stats['min_return']:.2f}%")
        print(f"預測準確率: {stats['accuracy']:.2%}")
        print(f"平均預測機率: {stats['avg_prediction_prob']:.3f}")

        # 詳細結果
        print(f"\n[LIST] 詳細回測記錄:")
        print("-"*80)
        print(f"{'日期':<12} {'預測機率':<8} {'實際報酬':<8} {'預測結果':<8}")
        print("-"*80)

        for result in results:
            status = "[OK]正確" if result['prediction_correct'] else "[ERROR]錯誤"
            print(f"{result['date']:<12} {result['prediction_prob']:<8.3f} {result['actual_return']:<8.2f}% {status:<8}")

        # 保存報告
        report_file = f"single_stock_backtest_{stock_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        # 轉換為可序列化的格式
        serializable_results = []
        for result in results:
            serializable_results.append({
                'date': result['date'],
                'prediction_prob': float(result['prediction_prob']),
                'actual_return': float(result['actual_return']),
                'prediction_correct': bool(result['prediction_correct'])
            })

        report_data = {
            'stock_id': stock_id,
            'config': self.config,
            'stats': {k: float(v) if isinstance(v, (int, float)) else v for k, v in stats.items()},
            'detailed_results': serializable_results
        }

        with open(report_file, 'w', encoding='ascii', errors='replace') as f:
            json.dump(report_data, f, ensure_ascii=True, indent=2)

        print(f"\n[SAVE] 報告已保存: {report_file}")

def show_menu():
    """顯示主選單"""
    print("\n" + "="*60)
    print("[ROCKET] 潛力股預測系統 - 回測框架")
    print("="*60)
    print("1. 執行完整投資組合回測")
    print("2. 執行單一個股回測")
    print("3. 重新設定日期參數")
    print("4. 查看系統狀態")
    print("5. 退出系統")
    print("="*60)

def get_user_input(prompt, default=None):
    """獲取使用者輸入"""
    if default:
        user_input = input(f"{prompt} (預設: {default}): ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()

def get_backtest_config():
    """獲取回測配置"""
    print("\n[CONFIG] 設定回測參數")
    print("-"*40)

    train_start = get_user_input("訓練開始日期", "2016-01-01")
    train_end = get_user_input("訓練結束日期", "2023-12-31")
    backtest_start = get_user_input("回測開始日期", "2024-01-31")
    backtest_end = get_user_input("回測結束日期", "2024-10-31")

    return train_start, train_end, backtest_start, backtest_end

def show_system_status(db_manager):
    """顯示系統狀態"""
    print("\n[SEARCH] 系統狀態檢查")
    print("-"*40)

    try:
        # 檢查資料庫連線
        with db_manager.get_connection() as conn:
            # 檢查股價資料
            query = "SELECT COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date FROM stock_prices"
            result = pd.read_sql_query(query, conn)

            print(f"[OK] 資料庫連線正常")
            print(f"[CHART] 股價資料: {result.iloc[0]['count']:,} 筆")
            print(f"[DATE] 資料範圍: {result.iloc[0]['min_date']} ~ {result.iloc[0]['max_date']}")

            # 檢查股票數量
            query = "SELECT COUNT(DISTINCT stock_id) as stock_count FROM stock_prices WHERE stock_id GLOB '[0-9][0-9][0-9][0-9]' AND stock_id NOT LIKE '00%'"
            result = pd.read_sql_query(query, conn)
            print(f"🏢 可用股票: {result.iloc[0]['stock_count']} 檔")

    except Exception as e:
        print(f"[ERROR] 系統檢查失敗: {e}")

def get_custom_dates():
    """獲取用戶自訂日期"""
    print("\n[TOOL] 日期設定")
    print("=" * 50)

    # 預設日期
    default_train_start = "2018-01-01"
    default_train_end = "2023-12-31"
    default_backtest_start = "2024-01-31"
    default_backtest_end = "2024-12-31"

    print(f"預設訓練期間: {default_train_start} ~ {default_train_end}")
    print(f"預設回測期間: {default_backtest_start} ~ {default_backtest_end}")

    use_custom = input("\n是否使用自訂日期? (y/N): ").strip().lower()

    if use_custom == 'y':
        print("\n請輸入自訂日期 (格式: YYYY-MM-DD):")

        train_start = input(f"訓練開始日期 [{default_train_start}]: ").strip()
        if not train_start:
            train_start = default_train_start

        train_end = input(f"訓練結束日期 [{default_train_end}]: ").strip()
        if not train_end:
            train_end = default_train_end

        backtest_start = input(f"回測開始日期 [{default_backtest_start}]: ").strip()
        if not backtest_start:
            backtest_start = default_backtest_start

        backtest_end = input(f"回測結束日期 [{default_backtest_end}]: ").strip()
        if not backtest_end:
            backtest_end = default_backtest_end
    else:
        train_start = default_train_start
        train_end = default_train_end
        backtest_start = default_backtest_start
        backtest_end = default_backtest_end

    return train_start, train_end, backtest_start, backtest_end

def main():
    """主函數 - 選單式介面"""
    # 初始化
    db_manager = DatabaseManager()

    # 獲取日期設定
    train_start, train_end, backtest_start, backtest_end = get_custom_dates()

    while True:
        show_menu()
        choice = input("請選擇功能 (1-5): ").strip()

        if choice == "1":
            # 完整投資組合回測
            print(f"\n[REFRESH] 執行完整投資組合回測")
            print(f"訓練期間: {train_start} ~ {train_end}")
            print(f"回測期間: {backtest_start} ~ {backtest_end}")

            confirm = input("確認執行? (y/N): ").strip().lower()
            if confirm == 'y':
                print("\n[START] 開始執行完整投資組合回測...")
                print("[WARN] 注意：這個過程可能需要較長時間，請耐心等待")

                backtest_system = BacktestingSystem(
                    db_manager,
                    train_start_date=train_start,
                    train_end_date=train_end,
                    backtest_start_date=backtest_start,
                    backtest_end_date=backtest_end
                )

                try:
                    backtest_system.run_backtest()
                    print("\n[COMPLETE] 完整投資組合回測執行完成！")
                    print("[REPORT] 回測報告已生成，請查看日誌文件獲取詳細結果")

                    # 詢問是否要退出系統
                    exit_choice = input("\n回測已完成，是否要退出系統? (y/N): ").strip().lower()
                    if exit_choice == 'y':
                        print("\n[EXIT] 感謝使用潛力股預測系統！")
                        break

                except Exception as e:
                    print(f"\n[ERROR] 回測執行過程中發生錯誤: {e}")
                    logging.error(f"回測執行錯誤: {e}")
                    print("請檢查日誌文件獲取詳細錯誤信息")

        elif choice == "2":
            # 單一個股回測
            stock_id = get_user_input("請輸入股票代號 (例: 2330)")

            if stock_id:
                print(f"\n[TARGET] 選擇訓練模式:")
                print("1. 純單一個股訓練 (只用該股票資料)")
                print("2. 混合模式訓練 (多股票訓練，單股票預測)")

                mode_choice = input("請選擇訓練模式 (1/2): ").strip()
                training_mode = 'pure' if mode_choice == '1' else 'mixed'
                mode_name = '純單一個股' if training_mode == 'pure' else '混合模式'

                print(f"\n[REFRESH] 執行 {stock_id} 個股回測")
                print(f"訓練模式: {mode_name}")
                print(f"訓練期間: {train_start} ~ {train_end}")
                print(f"回測期間: {backtest_start} ~ {backtest_end}")

                if training_mode == 'pure':
                    print("[WARNING]  注意: 純單一個股模式可能因樣本數不足而影響預測準確性")

                confirm = input("確認執行? (y/N): ").strip().lower()
                if confirm == 'y':
                    print(f"\n[START] 開始執行 {stock_id} 個股回測...")
                    print("[WARN] 注意：這個過程可能需要較長時間，請耐心等待")

                    backtest_system = BacktestingSystem(
                        db_manager,
                        train_start_date=train_start,
                        train_end_date=train_end,
                        backtest_start_date=backtest_start,
                        backtest_end_date=backtest_end
                    )

                    try:
                        backtest_system.run_single_stock_backtest(stock_id, training_mode)
                        print(f"\n[COMPLETE] {stock_id} 個股回測執行完成！")
                        print("[REPORT] 回測報告已生成，請查看日誌文件獲取詳細結果")

                    except Exception as e:
                        print(f"\n[ERROR] 個股回測執行過程中發生錯誤: {e}")
                        logging.error(f"個股回測執行錯誤: {e}")
                        print("請檢查日誌文件獲取詳細錯誤信息")

        elif choice == "3":
            # 重新設定日期參數
            print(f"\n[TOOL] 重新設定日期參數")
            train_start, train_end, backtest_start, backtest_end = get_custom_dates()
            print(f"\n[OK] 日期參數已更新")
            print(f"訓練期間: {train_start} ~ {train_end}")
            print(f"回測期間: {backtest_start} ~ {backtest_end}")

        elif choice == "4":
            # 查看系統狀態
            show_system_status(db_manager)

        elif choice == "5":
            # 退出系統
            print("\n[EXIT] 感謝使用潛力股預測系統！")
            break

        else:
            print("[ERROR] 無效選擇，請重新輸入")

        input("\n按 Enter 繼續...")

if __name__ == "__main__":
    main()

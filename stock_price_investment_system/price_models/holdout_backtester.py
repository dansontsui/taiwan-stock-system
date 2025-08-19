# -*- coding: utf-8 -*-
"""
外層 Holdout 回測 - 僅針對候選池股票，在未見樣本期間執行月頻交易。
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import logging

import numpy as np
import pandas as pd

from ..config.settings import get_config
from ..data.data_manager import DataManager
from .feature_engineering import FeatureEngineer
from .stock_price_predictor import StockPricePredictor
from ..visualization.backtest_charts import BacktestCharts

logger = logging.getLogger(__name__)

class HoldoutBacktester:
    def __init__(self, feature_engineer: Optional[FeatureEngineer] = None):
        self.cfg = get_config()
        self.paths = self.cfg['output']['paths']
        self.wf = self.cfg['walkforward']
        self.fe = feature_engineer or FeatureEngineer()
        self.dm = DataManager()

    def run(self,
            candidate_pool_json: Optional[str] = None,
            holdout_start: Optional[str] = None,
            holdout_end: Optional[str] = None,
            dynamic_pool: bool = False) -> Dict[str, Any]:
        """
        執行外層回測

        Args:
            candidate_pool_json: 候選池JSON檔案路徑
            holdout_start: 回測開始日期
            holdout_end: 回測結束日期
            dynamic_pool: 是否使用動態候選池（每月重新篩選）
        """
        # 載入初始候選池
        if dynamic_pool:
            logger.info("使用動態候選池模式：每月重新篩選候選股票")
            # 動態模式下，先獲取所有可用股票
            stocks = self._get_all_available_stocks()
        else:
            logger.info("使用靜態候選池模式：固定候選股票清單")
            pool = self._load_candidate_pool(candidate_pool_json)
            stocks = [s['stock_id'] for s in pool.get('candidate_pool', [])]

        if not stocks:
            logger.warning("候選池為空，外層回測無法執行")
            return {'success': False, 'error': 'empty_candidate_pool'}

        # 設定期間
        start = (holdout_start or (self.wf['holdout_start'] + '-01'))
        end = (holdout_end or (self.wf['holdout_end'] + '-31'))

        # 使用簡化的月頻交易：每個月月底做一次等權買入持有20天
        # 為每檔股票建立使用最佳參數的預測器
        stock_predictors = self._create_stock_predictors(stocks)
        result_records: List[Dict[str, Any]] = []

        months = pd.date_range(start=start, end=end, freq='M')
        for m in months:
            as_of = m.strftime('%Y-%m-%d')

            # 為每檔股票訓練模型（使用截至當前日期的資料）
            for stock_id in stocks:
                if stock_id in stock_predictors:
                    try:
                        # 生成訓練資料，使用截至預測日期之前的資料
                        # 使用2015年作為訓練開始日期（與內層回測一致）
                        features_df, targets_df = self.fe.generate_training_dataset(
                            stock_ids=[stock_id],
                            start_date='2015-01-01',
                            end_date=as_of
                        )

                        if features_df.empty:
                            logger.warning(f"股票 {stock_id} 在 {as_of} 沒有訓練資料")
                            continue

                        # 訓練模型
                        train_result = stock_predictors[stock_id].train(
                            feature_df=features_df,
                            target_df=targets_df
                        )

                        if not train_result['success']:
                            logger.warning(f"模型訓練失敗 {stock_id} {as_of}: {train_result.get('error', '未知錯誤')}")
                        else:
                            logger.debug(f"模型訓練成功 {stock_id} {as_of}")

                    except Exception as e:
                        logger.warning(f"訓練資料生成失敗 {stock_id} {as_of}: {e}")

            # 使用個股專屬預測器進行預測
            predictions = []
            for stock_id in stocks:
                if stock_id in stock_predictors:
                    pred_result = stock_predictors[stock_id].predict(stock_id, as_of)
                    logger.debug(f"預測結果 {stock_id} {as_of}: success={pred_result['success']}, return={pred_result.get('predicted_return', 'N/A')}")
                    if pred_result['success']:
                        predictions.append({
                            'stock_id': stock_id,
                            'predicted_return': pred_result['predicted_return'],
                            'model_type': getattr(stock_predictors[stock_id], 'model_type', 'unknown')
                        })
                    else:
                        logger.warning(f"預測失敗 {stock_id} {as_of}: {pred_result.get('error', '未知錯誤')}")

            logger.info(f"日期 {as_of}: 總預測數 {len(predictions)}")
            if predictions:
                pred_returns = [p['predicted_return'] for p in predictions]
                logger.info(f"預測報酬範圍: {min(pred_returns):.4f} ~ {max(pred_returns):.4f}")

            # 使用設定檔中的買入條件
            config = get_config('selection')
            prediction_threshold = config['selection_rules']['min_expected_return']  # 使用設定檔門檻
            max_positions = 3  # 每月最多買3檔股票

            logger.info(f"使用預測門檻: {prediction_threshold} ({prediction_threshold*100:.1f}%)")

            # 第一層篩選：預測報酬大於門檻
            positive_preds = [p for p in predictions if p['predicted_return'] > prediction_threshold]
            logger.info(f"符合門檻的預測數: {len(positive_preds)} (門檻: {prediction_threshold})")

            # 第二層篩選：技術指標確認（可選）
            if config['selection_rules']['technical_confirmation']:
                confirmed_preds = []
                for pred in positive_preds:
                    if self._technical_confirmation(pred['stock_id'], as_of):
                        confirmed_preds.append(pred)
                    else:
                        logger.debug(f"股票 {pred['stock_id']} 技術指標不支持，跳過")
                positive_preds = confirmed_preds
                logger.info(f"技術確認後剩餘: {len(positive_preds)} 檔股票")

            if not positive_preds:
                logger.info(f"日期 {as_of}: 沒有股票符合買入條件，本月不交易")
                continue

            # 按預期報酬排序，選擇最好的股票
            positive_preds.sort(key=lambda x: x['predicted_return'], reverse=True)

            # 第二層篩選：限制持股數量，只買最好的幾檔
            selected_preds = positive_preds[:max_positions]
            logger.info(f"最終選中股票數: {len(selected_preds)}")
            for pred in selected_preds:
                logger.info(f"  {pred['stock_id']}: 預測報酬 {pred['predicted_return']:.4f}")

            # 等權下單
            for pred in selected_preds:
                sid = pred['stock_id']
                predicted_return = pred['predicted_return']

                # 動態持有期間：根據預測報酬調整
                if predicted_return > 0.08:  # 預測報酬 > 8%
                    holding_days = 30  # 持有30天
                elif predicted_return > 0.05:  # 預測報酬 > 5%
                    holding_days = 25  # 持有25天
                else:
                    holding_days = 20  # 持有20天

                logger.info(f"股票 {sid} 預測報酬 {predicted_return:.4f}，持有 {holding_days} 天")
                trade_info = self._execute_trade(sid, as_of, holding_days)
                if trade_info is None:
                    continue
                result_records.append({
                    'entry_date': as_of,
                    'stock_id': sid,
                    'model_type': pred['model_type'],
                    'predicted_return': float(pred['predicted_return']),
                    'entry_price': trade_info['entry_price'],
                    'exit_date': trade_info['exit_date'],
                    'exit_price': trade_info['exit_price'],
                    'actual_return': trade_info['actual_return'],
                    'holding_days': trade_info['holding_days'],
                    'profit_loss': trade_info['profit_loss']
                })

        df = pd.DataFrame(result_records)
        metrics = self._metrics(df)
        out = {
            'success': True,
            'start': start,
            'end': end,
            'stock_count': len(stocks),
            'trade_count': len(df),
            'metrics': metrics,
        }

        # 輸出
        out_dir = Path(self.paths['holdout_results'])
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fp = out_dir / f'holdout_{ts}.json'
        with open(fp, 'w', encoding='utf-8') as f:  # 修正：移除BOM編碼
            json.dump(out, f, ensure_ascii=False, indent=2)
        logger.info(f"外層回測結果輸出: {fp}")

        # 輸出詳細交易記錄CSV和圖表
        if not df.empty:
            csv_fp = out_dir / f'holdout_trades_{ts}.csv'
            df.to_csv(csv_fp, index=False, encoding='utf-8-sig')
            logger.info(f"交易記錄CSV輸出: {csv_fp}")

            # 生成圖表
            try:
                chart_generator = BacktestCharts(output_dir=str(out_dir / "charts"))
                charts = chart_generator.create_holdout_charts(df, metrics)
                out['charts'] = charts
                logger.info(f"回測圖表已生成: {len(charts)} 個圖表")
            except Exception as e:
                logger.warning(f"圖表生成失敗: {e}")
                out['charts'] = {}

        return out

    def _technical_confirmation(self, stock_id: str, as_of: str) -> bool:
        """技術指標確認：檢查是否有技術面支持"""
        try:
            # 獲取最近30天的價格資料
            start_date = (pd.to_datetime(as_of) - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
            price_df = self.dm.get_stock_prices(stock_id, start_date, as_of)

            if len(price_df) < 20:  # 資料不足
                return False

            # 計算技術指標
            closes = price_df['close'].values

            # 1. 價格趨勢：收盤價 > 20日均線
            ma20 = closes[-20:].mean()
            current_price = closes[-1]
            trend_ok = current_price > ma20

            # 2. 動量指標：RSI不能過高（避免追高）
            def calculate_rsi(prices, period=14):
                if len(prices) < period + 1:
                    return 50  # 預設值
                deltas = np.diff(prices)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                avg_gain = gains[-period:].mean()
                avg_loss = losses[-period:].mean()
                if avg_loss == 0:
                    return 100
                rs = avg_gain / avg_loss
                return 100 - (100 / (1 + rs))

            rsi = calculate_rsi(closes)
            rsi_ok = 30 < rsi < 70  # RSI在合理範圍

            # 3. 成交量確認：最近3天平均成交量 > 前10天平均
            if 'volume' in price_df.columns:
                volumes = price_df['volume'].values
                recent_vol = volumes[-3:].mean()
                prev_vol = volumes[-13:-3].mean()
                volume_ok = recent_vol > prev_vol * 1.1  # 成交量放大10%
            else:
                volume_ok = True  # 沒有成交量資料時跳過此檢查

            # 綜合判斷：至少2個指標支持
            confirmations = sum([trend_ok, rsi_ok, volume_ok])
            result = confirmations >= 2

            logger.debug(f"技術確認 {stock_id}: 趨勢={trend_ok}, RSI={rsi_ok}({rsi:.1f}), 成交量={volume_ok}, 結果={result}")
            return result

        except Exception as e:
            logger.warning(f"技術指標確認失敗 {stock_id}: {e}")
            return True  # 確認失敗時不阻擋交易

    def _get_all_available_stocks(self) -> List[str]:
        """獲取所有可用股票清單"""
        try:
            available_stocks = self.dm.get_available_stocks(
                start_date=self.wf['training_start'] + '-01',
                end_date=self.wf['training_end'] + '-31',
                min_history_months=self.wf['min_stock_history_months']
            )
            logger.info(f"動態候選池：找到 {len(available_stocks)} 檔可用股票")
            return available_stocks[:20]  # 限制最多20檔股票，避免計算時間過長
        except Exception as e:
            logger.error(f"獲取可用股票失敗: {e}")
            return []

    def _load_candidate_pool(self, path: Optional[str]) -> Dict[str, Any]:
        if path and Path(path).exists():
            # 嘗試不同編碼方式讀取
            for encoding in ['utf-8-sig', 'utf-8', 'utf-8-bom']:
                try:
                    with open(path, 'r', encoding=encoding) as f:
                        return json.load(f)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
            logger.error(f"無法讀取候選池檔案: {path}")
            return {}
        # fallback: 使用最新
        cdir = Path(self.paths['candidate_pools'])
        files = sorted(cdir.glob('candidate_pool_*.json'))
        if not files:
            return {}
        # 嘗試不同編碼方式讀取最新檔案
        for encoding in ['utf-8-sig', 'utf-8', 'utf-8-bom']:
            try:
                with open(files[-1], 'r', encoding=encoding) as f:
                    return json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        logger.error(f"無法讀取候選池檔案: {files[-1]}")
        return {}

    def _execute_trade(self, stock_id: str, entry_date: str, holding_days: int) -> Optional[Dict[str, Any]]:
        """執行交易並返回詳細資訊"""
        try:
            from datetime import datetime, timedelta

            # 獲取進場價格
            entry_df = self.dm.get_stock_prices(stock_id, entry_date, entry_date)
            if entry_df.empty:
                return None
            entry_price = float(entry_df.iloc[-1]['close'])

            # 計算出場日期
            entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
            exit_dt = entry_dt + timedelta(days=holding_days)
            exit_date = exit_dt.strftime('%Y-%m-%d')

            # 獲取出場價格
            exit_df = self.dm.get_stock_prices(stock_id, entry_date, exit_date)
            if len(exit_df) < 2:
                return None

            # 找到實際的出場日期和價格
            actual_exit_date = exit_df.iloc[-1]['date']
            exit_price = float(exit_df.iloc[-1]['close'])

            # 計算實際持有天數
            if isinstance(actual_exit_date, str):
                actual_exit_dt = datetime.strptime(actual_exit_date, '%Y-%m-%d')
            else:
                actual_exit_dt = actual_exit_date
            actual_holding_days = (actual_exit_dt - entry_dt).days

            # 計算報酬和損益
            actual_return = (exit_price - entry_price) / entry_price
            profit_loss = exit_price - entry_price

            return {
                'entry_price': entry_price,
                'exit_date': actual_exit_dt.strftime('%Y-%m-%d'),
                'exit_price': exit_price,
                'actual_return': float(actual_return),
                'holding_days': actual_holding_days,
                'profit_loss': float(profit_loss)
            }
        except Exception as e:
            logger.debug(f"交易執行失敗 {stock_id} {entry_date}: {e}")
            return None

    def _actual_return(self, stock_id: str, entry_date: str, holding_days: int) -> Optional[float]:
        """保留舊函數以維持相容性"""
        trade_info = self._execute_trade(stock_id, entry_date, holding_days)
        return trade_info['actual_return'] if trade_info else None

    def _metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        if df.empty:
            return {'total_return': 0.0, 'trade_count': 0}
        ret = df['actual_return'].fillna(0)
        return {
            'total_return': float(ret.sum()),
            'avg_return': float(ret.mean()),
            'win_rate': float((ret > 0).mean()),
            'trade_count': int(len(df))
        }

    def _create_stock_predictors(self, stocks: List[str]) -> Dict[str, StockPricePredictor]:
        """為每檔股票建立使用最佳參數的預測器"""
        from .hyperparameter_tuner import HyperparameterTuner

        stock_predictors = {}

        # 獲取已調優股票資訊
        tuned_df = HyperparameterTuner.get_tuned_stocks_info()

        for stock_id in stocks:
            # 檢查該股票是否有調優記錄
            if not tuned_df.empty:
                try:
                    stock_id_int = int(stock_id)
                    stock_tuned = tuned_df[
                        (tuned_df['股票代碼'] == stock_id_int) &
                        (tuned_df['是否成功'] == '成功')
                    ]
                except ValueError:
                    stock_tuned = tuned_df[
                        (tuned_df['股票代碼'].astype(str) == stock_id) &
                        (tuned_df['是否成功'] == '成功')
                    ]

                if not stock_tuned.empty:
                    # 選擇分數最高的模型
                    best_record = stock_tuned.loc[stock_tuned['最佳分數'].idxmax()]
                    model_type = best_record['模型類型']

                    # 獲取最佳參數
                    best_params = HyperparameterTuner.get_stock_best_params(stock_id, model_type)

                    if best_params:
                        predictor = StockPricePredictor(
                            self.fe,
                            model_type=model_type,
                            override_params=best_params
                        )
                        stock_predictors[stock_id] = predictor
                        logger.info(f"股票 {stock_id} 使用 {model_type} 最佳參數: {best_params}")
                        continue

            # 沒有調優記錄，使用預設預測器
            predictor = StockPricePredictor(self.fe)
            stock_predictors[stock_id] = predictor
            logger.info(f"股票 {stock_id} 使用預設參數")

        return stock_predictors


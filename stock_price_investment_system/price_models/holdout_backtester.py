# -*- coding: utf-8 -*-
"""
外層 Holdout 回測 - 僅針對候選池股票，在未見樣本期間執行月頻交易。
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json
import logging

import pandas as pd

from ..config.settings import get_config
from ..data.data_manager import DataManager
from .feature_engineering import FeatureEngineer
from .stock_price_predictor import StockPricePredictor
from ..visualization.backtest_charts import BacktestCharts

logger = logging.getLogger(__name__)

class HoldoutBacktester:
    def __init__(self, feature_engineer: FeatureEngineer | None = None):
        self.cfg = get_config()
        self.paths = self.cfg['output']['paths']
        self.wf = self.cfg['walkforward']
        self.fe = feature_engineer or FeatureEngineer()
        self.dm = DataManager()

    def run(self,
            candidate_pool_json: str | None = None,
            holdout_start: str | None = None,
            holdout_end: str | None = None) -> Dict[str, Any]:
        """執行外層回測"""
        # 載入候選池
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
                        train_data = self.fe.generate_training_dataset(
                            stock_ids=[stock_id],
                            end_date=as_of
                        )

                        if train_data['features'].empty:
                            logger.warning(f"股票 {stock_id} 在 {as_of} 沒有訓練資料")
                            continue

                        # 訓練模型
                        train_result = stock_predictors[stock_id].train(
                            feature_df=train_data['features'],
                            target_df=train_data['targets']
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

            # 選擇預期報酬大於門檻的股票（降低門檻以便測試）
            prediction_threshold = -0.05  # 允許預測報酬低至-5%的股票
            positive_preds = [p for p in predictions if p['predicted_return'] > prediction_threshold]
            logger.info(f"符合門檻的預測數: {len(positive_preds)} (門檻: {prediction_threshold})")
            # 按預期報酬排序
            positive_preds.sort(key=lambda x: x['predicted_return'], reverse=True)

            # 等權下單
            for pred in positive_preds:
                sid = pred['stock_id']
                trade_info = self._execute_trade(sid, as_of, 20)
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

    def _load_candidate_pool(self, path: str | None) -> Dict[str, Any]:
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

    def _execute_trade(self, stock_id: str, entry_date: str, holding_days: int) -> Dict[str, Any] | None:
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

    def _actual_return(self, stock_id: str, entry_date: str, holding_days: int) -> float | None:
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


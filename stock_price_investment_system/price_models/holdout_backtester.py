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

import pandas as pd

from ..config.settings import get_config
from ..data.data_manager import DataManager
from .feature_engineering import FeatureEngineer
from .stock_price_predictor import StockPricePredictor
from ..visualization.backtest_charts import BacktestCharts

logger = logging.getLogger(__name__)

class HoldoutBacktester:
    def __init__(self, feature_engineer: Optional[FeatureEngineer] = None, verbose_logging: bool = False, cli_only_logging: bool = False):
        self.cfg = get_config()
        self.paths = self.cfg['output']['paths']
        self.wf = self.cfg['walkforward']
        self.fe = feature_engineer or FeatureEngineer()
        self.dm = DataManager()
        self.verbose_logging = verbose_logging
        self.cli_only_logging = cli_only_logging

    def _log(self, message: str, level: str = "info", force_print: bool = False):
        """
        統一的日誌輸出方法

        Args:
            message: 日誌訊息
            level: 日誌級別 (info, warning, error)
            force_print: 是否強制輸出（用於重要訊息和錯誤）
        """
        # 決定是否輸出到控制台
        should_print = self.verbose_logging or force_print or level in ["warning", "error"]

        if should_print:
            if level == "error":
                print(f"❌ {message}")
            elif level == "warning":
                print(f"⚠️  {message}")
            else:
                print(f"ℹ️  {message}")

        # 決定是否記錄到日誌檔案
        if not self.cli_only_logging:
            if level == "error":
                logger.error(message)
            elif level == "warning":
                logger.warning(message)
            else:
                logger.info(message)

    def _create_progress_bar(self, current: int, total: int, width: int = 20) -> str:
        """創建ASCII進度條"""
        filled = int(width * current / total)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}]"

    def _display_monthly_results(self, month: str, trades: list, monthly_results: list, backtest_session_id: str = None):
        """顯示當月回測結果並保存到月度結果列表，同時立即保存到檔案"""
        # 計算當月統計
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['actual_return'] > 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        total_return = sum(t['actual_return'] for t in trades)
        avg_return = total_return / total_trades if total_trades > 0 else 0

        total_profit_loss = sum(t['profit_loss'] for t in trades)

        # 創建月度結果記錄
        monthly_result = {
            'month': month,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'total_profit_loss': total_profit_loss,
            'trades': trades.copy() if trades else []
        }

        # 添加到月度結果列表
        monthly_results.append(monthly_result)

        # 立即保存當月結果到檔案
        if backtest_session_id:
            self._save_monthly_result_immediately(monthly_result, backtest_session_id)

        # 顯示當月結果
        if not trades:
            self._log(f"📅 {month}: 無交易", "info", force_print=True)
        else:
            self._log(f"📅 {month} 回測結果:", "info", force_print=True)
            self._log(f"   📊 交易數: {total_trades} 筆", "info", force_print=True)
            self._log(f"   🎯 勝率: {win_rate:.1%} ({winning_trades}/{total_trades})", "info", force_print=True)
            self._log(f"   📈 平均報酬: {avg_return:.2%}", "info", force_print=True)
            self._log(f"   💰 損益: {total_profit_loss:,.0f}", "info", force_print=True)

            # 顯示前3名表現最好的股票
            if total_trades > 0:
                sorted_trades = sorted(trades, key=lambda x: x['actual_return'], reverse=True)
                top_trades = sorted_trades[:min(3, len(sorted_trades))]

                self._log(f"   🏆 表現最佳:", "info", force_print=True)
                for i, trade in enumerate(top_trades, 1):
                    self._log(f"      {i}. {trade['stock_id']}: {trade['actual_return']:+.2%} ({trade['profit_loss']:+,.0f})", "info", force_print=True)

        self._log("", "info", force_print=True)  # 空行分隔

    def _save_monthly_result_immediately(self, monthly_result: dict, session_id: str):
        """立即保存當月結果到CSV檔案"""
        try:
            import csv
            from datetime import datetime
            from pathlib import Path
            from stock_price_investment_system.config.settings import get_config

            # 獲取holdout結果目錄
            config = get_config()
            holdout_dir = Path(config['output']['paths']['holdout_results'])
            holdout_dir.mkdir(parents=True, exist_ok=True)

            # 生成月度結果檔案名稱
            month_str = monthly_result['month'].replace('-', '').replace(':', '')[:8]  # YYYYMMDD
            csv_filename = holdout_dir / f"holdout_monthly_{session_id}_{month_str}.csv"

            # 準備CSV資料
            csv_data = []

            # 添加摘要資訊
            csv_data.append(['項目', '數值'])
            csv_data.append(['月份', monthly_result['month']])
            csv_data.append(['交易數', monthly_result['total_trades']])
            csv_data.append(['勝利交易數', monthly_result['winning_trades']])
            csv_data.append(['勝率', f"{monthly_result['win_rate']:.2%}"])
            csv_data.append(['平均報酬率', f"{monthly_result['avg_return']:.2%}"])
            csv_data.append(['總損益', f"{monthly_result['total_profit_loss']:,.0f}"])
            csv_data.append(['保存時間', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            csv_data.append(['會話ID', session_id])
            csv_data.append([])  # 空行

            # 添加交易詳情標題
            if monthly_result['trades']:
                csv_data.append(['交易詳情'])
                # 與 holdout_trades 對齊的欄位, 並新增持有期間最大/最小報酬
                csv_data.append(['進場日', '股票代號', '模型', '預測報酬', '進場價', '出場日', '出場價', '實際報酬', '持有天數', '損益', '20日最大報酬', '20日最小報酬'])

                # 添加每筆交易
                for trade in monthly_result['trades']:
                    csv_data.append([
                        trade.get('entry_date', monthly_result['month']),
                        trade['stock_id'],
                        trade.get('model_type', ''),
                        f"{trade.get('predicted_return', 0.0):.2%}",
                        f"{trade.get('entry_price', 0.0):,.2f}",
                        trade.get('exit_date', ''),
                        f"{trade.get('exit_price', 0.0):,.2f}",
                        f"{trade['actual_return']:.2%}",
                        str(trade.get('holding_days', '')),
                        f"{trade['profit_loss']:,.0f}",
                        f"{trade.get('max_return_20d', 0.0):.2%}",
                        f"{trade.get('min_return_20d', 0.0):.2%}"
                    ])
            else:
                csv_data.append(['交易詳情'])
                csv_data.append(['本月無交易'])

            # 保存到CSV檔案
            with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerows(csv_data)

            self._log(f"💾 {monthly_result['month']} 結果已保存至: {csv_filename.name}", "info", force_print=True)

        except Exception as e:
            self._log(f"⚠️  保存月度結果失敗: {e}", "warning", force_print=True)

    def run(self,
            candidate_pool_json: Optional[str] = None,
            holdout_start: Optional[str] = None,
            holdout_end: Optional[str] = None,
            min_predicted_return: Optional[float] = None,
            top_k: Optional[int] = None,
            use_market_filter: bool = False) -> Dict[str, Any]:
        """執行外層回測"""
        # 載入候選池
        pool = self._load_candidate_pool(candidate_pool_json)
        stocks = [s['stock_id'] for s in pool.get('candidate_pool', [])]
        if not stocks:
            logger.warning("候選池為空，外層回測無法執行")
            return {'success': False, 'error': 'empty_candidate_pool'}

        # 設定期間
        start = (holdout_start or (self.wf['holdout_start'] + '-01'))

        # 正確處理結束日期
        if holdout_end:
            end = holdout_end
        else:
            # 使用配置中的結束日期，並正確處理月底
            from calendar import monthrange
            holdout_end_str = self.wf['holdout_end']
            year, month = map(int, holdout_end_str.split('-'))
            last_day = monthrange(year, month)[1]
            end = f"{holdout_end_str}-{last_day:02d}"

        # 預設參數
        sel_cfg = get_config('selection')
        default_threshold = sel_cfg.get('selection_rules', {}).get('min_expected_return', 0.02)
        threshold = default_threshold if min_predicted_return is None else float(min_predicted_return)
        k = 0 if top_k is None else int(top_k)

        # 使用簡化的月頻交易：每個月月底做一次等權買入持有20天
        # 為每檔股票建立使用最佳參數的預測器
        stock_predictors = self._create_stock_predictors(stocks)
        result_records: List[Dict[str, Any]] = []
        monthly_results: List[Dict[str, Any]] = []  # 存儲每月結果

        # 生成回測會話ID
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        months = pd.date_range(start=start, end=end, freq='M')
        total_months = len(months)

        self._log(f"🚀 開始外層回測，共 {total_months} 個月需要處理", "info", force_print=True)
        self._log(f"📅 回測期間: {start} ~ {end}", "info", force_print=True)
        self._log(f"📊 股票數量: {len(stocks)} 檔", "info", force_print=True)

        for month_idx, m in enumerate(months, 1):
            as_of = m.strftime('%Y-%m-%d')

            # 顯示進度
            progress_percent = (month_idx / total_months) * 100
            progress_bar = self._create_progress_bar(month_idx, total_months)
            self._log(f"📈 進度 [{month_idx:2d}/{total_months}] {progress_bar} {progress_percent:5.1f}% - 處理 {as_of}", "info", force_print=True)

            # 市場濾網：若啟用且市場不佳則跳過當月
            if use_market_filter and (not self._is_market_ok(as_of)):
                self._log(f"市場濾網觸發，跳過交易月份: {as_of}", "info")
                continue

            # 為每檔股票訓練模型（使用截至當前日期的資料）
            for stock_idx, stock_id in enumerate(stocks, 1):
                if stock_id in stock_predictors:
                    # 顯示股票處理進度（只在詳細模式下顯示）
                    if self.verbose_logging:
                        stock_progress = self._create_progress_bar(stock_idx, len(stocks), width=10)
                        self._log(f"   📊 [{stock_idx:2d}/{len(stocks)}] {stock_progress} processing {stock_id}", "info")

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
                            'predicted_return': float(pred_result['predicted_return']),
                            'model_type': getattr(stock_predictors[stock_id], 'model_type', 'unknown')
                        })
                    else:
                        logger.warning(f"預測失敗 {stock_id} {as_of}: {pred_result.get('error', '未知錯誤')}")

            self._log(f"日期 {as_of}: 總預測數 {len(predictions)}", "info")
            if predictions:
                pred_returns = [p['predicted_return'] for p in predictions]
                self._log(f"預測報酬範圍: {min(pred_returns):.4f} ~ {max(pred_returns):.4f}", "info")

            # 門檻與 TopK 篩選
            filtered = self._filter_predictions(predictions, threshold, k)
            self._log(f"符合門檻的預測數: {len(filtered)} (門檻: {threshold:.4f})，TopK: {k}", "info")

            # 等權下單
            month_trades = []
            for pred in filtered:
                sid = pred['stock_id']
                trade_info = self._execute_trade(sid, as_of, 20)
                if trade_info is None:
                    continue
                trade_record = {
                    'entry_date': as_of,
                    'stock_id': sid,
                    'model_type': pred['model_type'],
                    'predicted_return': float(pred['predicted_return']),
                    'entry_price': trade_info['entry_price'],
                    'exit_date': trade_info['exit_date'],
                    'exit_price': trade_info['exit_price'],
                    'actual_return': trade_info['actual_return'],
                    'holding_days': trade_info['holding_days'],
                    'profit_loss': trade_info['profit_loss'],
                    'max_return_20d': trade_info.get('max_return'),
                    'min_return_20d': trade_info.get('min_return')
                }
                result_records.append(trade_record)
                month_trades.append(trade_record)

            # 顯示當月結果並保存到月度結果，同時立即保存到檔案
            self._display_monthly_results(as_of, month_trades, monthly_results, session_id)

        df = pd.DataFrame(result_records)
        metrics = self._metrics(df)

        # 顯示回測完成總結
        self._log("🎉 外層回測完成！", "info", force_print=True)
        self._log(f"📊 總交易次數: {len(df)}", "info", force_print=True)
        self._log(f"📈 總報酬率: {metrics.get('total_return', 0):.2%}", "info", force_print=True)
        self._log(f"🎯 勝率: {metrics.get('win_rate', 0):.2%}", "info", force_print=True)

        out = {
            'success': True,
            'start': start,
            'end': end,
            'stock_count': len(stocks),
            'trade_count': len(df),
            'metrics': metrics,
            'params': {
                'min_predicted_return': threshold,
                'top_k': k,
                'use_market_filter': bool(use_market_filter)
            },
            'total_return': metrics.get('total_return', 0),  # 添加總報酬到輸出
            'monthly_results': monthly_results,  # 添加月度結果
            'detailed_trades': result_records  # 添加詳細交易記錄
        }

        # 輸出
        out_dir = Path(self.paths['holdout_results'])
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fp = out_dir / f'holdout_{ts}.json'
        with open(fp, 'w', encoding='utf-8') as f:  # 修正：移除BOM編碼
            json.dump(out, f, ensure_ascii=False, indent=2)
        self._log(f"外層回測結果輸出: {fp}", "info")

        # 輸出詳細交易記錄CSV和圖表
        if not df.empty:
            csv_fp = out_dir / f'holdout_trades_{ts}.csv'
            df.to_csv(csv_fp, index=False, encoding='utf-8-sig')
            self._log(f"交易記錄CSV輸出: {csv_fp}", "info")

            # 生成圖表
            try:
                chart_generator = BacktestCharts(output_dir=str(out_dir / "charts"))
                charts = chart_generator.create_holdout_charts(df, metrics)
                out['charts'] = charts
                self._log(f"回測圖表已生成: {len(charts)} 個圖表", "info")
            except Exception as e:
                logger.warning(f"圖表生成失敗: {e}")
                out['charts'] = {}

        return out

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

    def _filter_predictions(self, predictions: List[Dict[str, Any]], threshold: float, top_k: int) -> List[Dict[str, Any]]:
        """依門檻與TopK篩選預測結果，並按預期報酬由高到低排序"""
        if not predictions:
            return []
        # 門檻過濾
        filtered = [p for p in predictions if float(p.get('predicted_return', 0.0)) >= float(threshold)]
        # 依預期報酬排序
        filtered.sort(key=lambda x: x.get('predicted_return', 0.0), reverse=True)
        # TopK（0或負數代表不限制）
        if isinstance(top_k, int) and top_k > 0:
            filtered = filtered[:top_k]
        return filtered

    def _is_market_ok(self, as_of: str) -> bool:
        """簡易市場濾網：若可取得加權指數或以候補標的集合作替代，使用 50MA > 200MA 規則"""
        try:
            # 優先嘗試 0050 當作市場代理（若資料庫無指數）
            proxy_id = '0050'
            start = '2010-01-01'
            df = self.dm.get_price_data(proxy_id, start_date=start, end_date=as_of)
            if df is None or df.empty or 'close' not in df.columns:
                return True  # 無法取得市場資料時，不阻擋交易
            s = df['close'].astype(float)
            ma50 = s.rolling(50, min_periods=1).mean()
            ma200 = s.rolling(200, min_periods=1).mean()
            return bool(ma50.iloc[-1] >= ma200.iloc[-1])
        except Exception:
            # 任意錯誤時不阻擋交易，避免回測整體中斷
            return True

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

            # 獲取出場價格，以及期間價格序列
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

            # 計算持有期間內每日相對於進場價的最大/最小報酬
            try:
                closes = exit_df['close'].astype(float).values
                rel_returns = (closes - entry_price) / entry_price
                max_return = float(rel_returns.max())
                min_return = float(rel_returns.min())
            except Exception:
                max_return = float(actual_return)
                min_return = float(actual_return)

            return {
                'entry_price': entry_price,
                'exit_date': actual_exit_dt.strftime('%Y-%m-%d'),
                'exit_price': exit_price,
                'actual_return': float(actual_return),
                'holding_days': actual_holding_days,
                'profit_loss': float(profit_loss),
                'max_return': max_return,
                'min_return': min_return
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

        # 基本指標
        metrics = {
            'total_return': float(ret.sum()),
            'avg_return': float(ret.mean()),
            'win_rate': float((ret > 0).mean()),
            'trade_count': int(len(df))
        }

        # 進階指標
        if len(ret) > 1:
            metrics['volatility'] = float(ret.std())
            metrics['max_return'] = float(ret.max())
            metrics['min_return'] = float(ret.min())

            # 最大回撤計算
            cumulative_returns = (1 + ret).cumprod()
            running_max = cumulative_returns.cummax()
            drawdown = (cumulative_returns / running_max) - 1
            metrics['max_drawdown'] = float(drawdown.min())

            # 夏普比率 (假設無風險利率為0)
            if metrics['volatility'] > 0:
                metrics['sharpe_ratio'] = float(metrics['avg_return'] / metrics['volatility'])
            else:
                metrics['sharpe_ratio'] = 0.0

            # 盈虧比
            winning_trades = ret[ret > 0]
            losing_trades = ret[ret < 0]

            if len(winning_trades) > 0 and len(losing_trades) > 0:
                avg_win = float(winning_trades.mean())
                avg_loss = float(abs(losing_trades.mean()))
                metrics['profit_loss_ratio'] = avg_win / avg_loss if avg_loss > 0 else 0.0
            else:
                metrics['profit_loss_ratio'] = 0.0

        return metrics

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
                        # 僅在詳細模式下輸出
                        self._log(f"股票 {stock_id} 使用 {model_type} 最佳參數: {best_params}", "info")
                        continue

            # 沒有調優記錄，使用預設預測器
            predictor = StockPricePredictor(self.fe)
            stock_predictors[stock_id] = predictor
            self._log(f"股票 {stock_id} 使用預設參數", "info")

        return stock_predictors


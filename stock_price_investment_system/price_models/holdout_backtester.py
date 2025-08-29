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
        self.trading_cfg = self.cfg['trading']
        self.backtest_cfg = self.cfg['backtest']
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
        """創建ASCII進度條（純ASCII，避免cp950編碼問題）"""
        if total <= 0:
            total = 1
        filled = int(width * current / total)
        bar = '=' * filled + '-' * (width - filled)
        return f"[{bar}]"

    def _display_monthly_results(self, month: str, trades: list, monthly_results: list, backtest_session_id: str = None, output_dir: Path = None):
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
            self._save_monthly_result_immediately(monthly_result, backtest_session_id, output_dir)

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

    def _save_monthly_result_immediately(self, monthly_result: dict, session_id: str, output_dir: Path = None):
        """立即保存當月結果到CSV檔案"""
        try:
            import csv
            from datetime import datetime
            from pathlib import Path
            from stock_price_investment_system.config.settings import get_config

            # 使用傳入的輸出目錄，或預設目錄
            if output_dir:
                holdout_dir = output_dir
            else:
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

    def _save_monthly_investment_result_immediately(self, monthly_result: dict, session_id: str, output_dir: Path = None):
        """立即保存每月定期定額投資結果到CSV檔案（與選項5格式類似）"""
        try:
            import csv
            from datetime import datetime
            from pathlib import Path
            from stock_price_investment_system.config.settings import get_config

            # 使用傳入的輸出目錄，或預設目錄
            if output_dir is None:
                config = get_config()
                holdout_dir = Path(config['output']['paths']['holdout_results'])
            else:
                holdout_dir = output_dir
            holdout_dir.mkdir(parents=True, exist_ok=True)

            # 生成月度結果檔案名稱（與選項5相同格式）
            month_str = monthly_result['month'].replace('-', '').replace(':', '')[:8]  # YYYYMMDD
            csv_filename = holdout_dir / f"holdout_monthly_{session_id}_{month_str}.csv"

            # 準備CSV資料
            csv_data = []

            # 添加摘要資訊
            csv_data.append(['項目', '數值'])
            csv_data.append(['月份', monthly_result['month']])
            csv_data.append(['市場濾網觸發', monthly_result.get('market_filter_triggered', False)])
            csv_data.append(['入選股票數', len(monthly_result['selected_stocks'])])
            csv_data.append(['入選股票', ', '.join(monthly_result['selected_stocks'])])
            csv_data.append(['投資金額', f"{monthly_result['investment_amount']:,.0f}"])
            csv_data.append(['月底價值', f"{monthly_result['month_end_value']:,.0f}"])
            csv_data.append(['月報酬率', f"{monthly_result['return_rate']:.2%}"])
            csv_data.append(['交易數', len(monthly_result['trades'])])
            csv_data.append(['保存時間', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            csv_data.append(['會話ID', session_id])
            csv_data.append([])  # 空行

            # 添加交易詳情標題
            if monthly_result['trades']:
                csv_data.append(['交易詳情'])
                # 包含兩種計算方式的欄位，並添加20日最大最小報酬
                csv_data.append(['進場日', '股票代號', '模型', '預測報酬', '股數', '投資金額', '進場價', '出場日', '出場價',
                               '毛報酬', '淨報酬', '持有天數', '毛損益', '淨損益', '月底價值', '交易成本', '20日最大報酬', '20日最小報酬'])

                # 添加每筆交易
                for trade in monthly_result['trades']:
                    csv_data.append([
                        trade.get('entry_date', monthly_result['month']),
                        trade['stock_id'],
                        trade.get('model_type', ''),
                        f"{trade.get('predicted_return', 0.0):.2%}",
                        f"{trade.get('shares', 0):,}",
                        f"{trade.get('investment_amount', 0.0):,.0f}",
                        f"{trade.get('entry_price', 0.0):,.2f}",
                        trade.get('exit_date', ''),
                        f"{trade.get('exit_price', 0.0):,.2f}",
                        f"{trade.get('actual_return_gross', 0.0):.2%}",
                        f"{trade.get('actual_return_net', 0.0):.2%}",
                        f"{trade.get('holding_days', 0)}",
                        f"{trade.get('profit_loss_gross', 0.0):,.0f}",
                        f"{trade.get('profit_loss_net', 0.0):,.0f}",
                        f"{trade.get('month_end_value', 0.0):,.0f}",
                        f"{trade.get('transaction_costs', {}).get('total_cost_amount', 0.0):,.0f}",
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

    def _generate_folder_name(self, start: str, end: str, threshold: float, k: int, use_market_filter: bool) -> str:
        """根據參數組合生成資料夾名稱"""
        # 提取日期部分 (YYYY-MM-DD -> YYYYMM)
        start_str = start.replace('-', '')[:6]  # YYYYMM
        end_str = end.replace('-', '')[:6]      # YYYYMM

        # 格式化參數
        threshold_str = f"{int(threshold * 1000):03d}"  # 0.020 -> 020
        k_str = f"k{k}" if k > 0 else "kAll"
        filter_str = "MF" if use_market_filter else "NoMF"

        # 加入執行時間戳記 (MMDDHHMMSS)
        from datetime import datetime
        timestamp = datetime.now().strftime('%m%d%H%M%S')

        # 組合資料夾名稱: holdout_YYYYMM_YYYYMM_020_k10_MF_MMDDHHMMSS
        folder_name = f"holdout_{start_str}_{end_str}_{threshold_str}_{k_str}_{filter_str}_{timestamp}"
        return folder_name

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

        # 生成參數化資料夾名稱和會話ID
        folder_name = self._generate_folder_name(start, end, threshold, k, use_market_filter)
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 創建參數化輸出目錄
        base_out_dir = Path(self.paths['holdout_results'])
        param_out_dir = base_out_dir / folder_name
        param_out_dir.mkdir(parents=True, exist_ok=True)

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
            self._display_monthly_results(as_of, month_trades, monthly_results, session_id, param_out_dir)

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

        # 輸出到參數化目錄
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fp = param_out_dir / f'holdout_{ts}.json'
        with open(fp, 'w', encoding='utf-8') as f:  # 修正：移除BOM編碼
            json.dump(out, f, ensure_ascii=False, indent=2)
        self._log(f"外層回測結果輸出: {fp}", "info", force_print=True)

        # 輸出詳細交易記錄CSV和圖表
        if not df.empty:
            csv_fp = param_out_dir / f'holdout_trades_{ts}.csv'
            df.to_csv(csv_fp, index=False, encoding='utf-8-sig')
            self._log(f"交易記錄CSV輸出: {csv_fp}", "info", force_print=True)

            # 生成圖表
            try:
                chart_generator = BacktestCharts(output_dir=str(param_out_dir / "charts"))
                charts = chart_generator.create_holdout_charts(df, metrics)
                out['charts'] = charts
                self._log(f"回測圖表已生成: {len(charts)} 個圖表", "info", force_print=True)
            except Exception as e:
                logger.warning(f"圖表生成失敗: {e}")
                out['charts'] = {}

        # 記錄參數化資料夾資訊
        out['output_folder'] = folder_name
        self._log(f"📁 所有結果已保存到資料夾: {folder_name}", "info", force_print=True)

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

    def _check_market_filter(self, as_of: str) -> bool:
        """回傳是否觸發市場濾網（True=觸發=暫停投資）。沿用現有_is_market_ok結果的相反邏輯。"""
        try:
            return not self._is_market_ok(as_of)
        except Exception:
            # 發生錯誤時，不阻擋交易
            return False

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

    def _execute_trade(self, stock_id: str, entry_date: str, holding_days: int, shares: int = 1000) -> Optional[Dict[str, Any]]:
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

            # 計算報酬和損益（加入交易成本）
            gross_return = (exit_price - entry_price) / entry_price if entry_price > 0 else 0

            # 使用傳入的實際股數進行交易成本計算
            transaction_costs = self._calculate_transaction_costs(entry_price, exit_price, shares)

            # 淨報酬 = 毛報酬 - 交易成本率
            actual_return = gross_return - transaction_costs['total_cost_rate']

            # 淨損益 = 毛損益 - 交易成本金額（以1000股為基準）
            gross_profit_loss = (exit_price - entry_price) * shares
            profit_loss = gross_profit_loss - transaction_costs['total_cost_amount']

            # 計算持有期間內每日相對於進場價的最大/最小報酬
            try:
                closes = exit_df['close'].astype(float).values
                if entry_price > 0:
                    rel_returns = (closes - entry_price) / entry_price
                    max_return = float(rel_returns.max())
                    min_return = float(rel_returns.min())
                else:
                    max_return = float(actual_return)
                    min_return = float(actual_return)
            except Exception:
                max_return = float(actual_return)
                min_return = float(actual_return)

            return {
                'entry_price': entry_price,
                'exit_date': actual_exit_dt.strftime('%Y-%m-%d'),
                'exit_price': exit_price,
                'actual_return': float(actual_return),
                'gross_return': float(gross_return),
                'holding_days': actual_holding_days,
                'profit_loss': float(profit_loss),
                'gross_profit_loss': float(gross_profit_loss),
                'transaction_costs': transaction_costs,
                'shares': shares,
                'max_return': max_return,
                'min_return': min_return
            }
        except Exception as e:
            logger.debug(f"交易執行失敗 {stock_id} {entry_date}: {e}")
            return None

    def _calculate_transaction_costs(self, entry_price: float, exit_price: float, shares: int = 1000) -> Dict[str, float]:
        """
        計算交易成本

        Args:
            entry_price: 進場價格
            exit_price: 出場價格
            shares: 股數

        Returns:
            交易成本詳細資訊
        """
        costs = self.trading_cfg['transaction_costs']

        # 買進成本
        buy_amount = entry_price * shares
        buy_commission = buy_amount * costs['commission_rate']
        buy_slippage = buy_amount * (costs['slippage_bps'] / 10000)

        # 賣出成本
        sell_amount = exit_price * shares
        sell_commission = sell_amount * costs['commission_rate']
        sell_tax = sell_amount * costs['tax_rate']
        sell_slippage = sell_amount * (costs['slippage_bps'] / 10000)

        # 總成本
        total_cost_amount = buy_commission + buy_slippage + sell_commission + sell_tax + sell_slippage
        total_cost_rate = total_cost_amount / buy_amount if buy_amount > 0 else 0

        return {
            'buy_commission': buy_commission,
            'buy_slippage': buy_slippage,
            'sell_commission': sell_commission,
            'sell_tax': sell_tax,
            'sell_slippage': sell_slippage,
            'total_cost_amount': total_cost_amount,
            'total_cost_rate': total_cost_rate
        }

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

    def _get_stock_price(self, stock_id: str, date: str) -> Optional[float]:
        """獲取指定日期的股價"""
        try:
            # 獲取該日期的股價資料
            price_df = self.dm.get_stock_prices(stock_id, date, date)
            if not price_df.empty:
                return float(price_df.iloc[0]['close'])
            return None
        except Exception as e:
            self._log(f"獲取股價失敗 {stock_id} {date}: {e}", "warning")
            return None

    def run_monthly_investment(self,
                              candidate_pool_json: Optional[str] = None,
                              holdout_start: Optional[str] = None,
                              holdout_end: Optional[str] = None,
                              min_predicted_return: Optional[float] = None,
                              top_k: Optional[int] = None,
                              use_market_filter: bool = False,
                              monthly_investment: float = None) -> Dict[str, Any]:
        """
        執行每月定期定額投資回測

        Args:
            candidate_pool_json: 候選池JSON檔案路徑
            holdout_start: 回測開始日期
            holdout_end: 回測結束日期
            min_predicted_return: 最小預測報酬門檻
            top_k: 每月最多持股數
            use_market_filter: 是否使用市場濾網
            monthly_investment: 每月投資金額（預設使用config中的initial_capital）

        Returns:
            回測結果字典
        """
        # 載入候選池
        pool = self._load_candidate_pool(candidate_pool_json)
        stocks = [s['stock_id'] for s in pool.get('candidate_pool', [])]
        if not stocks:
            logger.warning("候選池為空，外層回測無法執行")
            return {'success': False, 'error': 'empty_candidate_pool'}

        # 設定每月投資金額
        if monthly_investment is None:
            monthly_investment = self.backtest_cfg['initial_capital']

        self._log(f"🏦 每月定期定額投資回測", "info", force_print=True)
        self._log(f"💰 每月投資金額: {monthly_investment:,.0f} 元", "info", force_print=True)

        # 設定期間
        start = (holdout_start or (self.wf['holdout_start'] + '-01'))

        # 正確處理結束日期
        if holdout_end:
            end = holdout_end
        else:
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

        # 為每檔股票建立使用最佳參數的預測器
        stock_predictors = self._create_stock_predictors(stocks)

        self._log(f"📊 候選股票數: {len(stocks)} 檔", "info", force_print=True)
        self._log(f"💰 每月投資金額: {monthly_investment:,.0f} 元", "info", force_print=True)
        self._log(f"📅 投資期間: {start} ~ {end}", "info", force_print=True)

        # 生成會話ID和輸出目錄（用於立即保存月度結果）
        from datetime import datetime
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        folder_name = self._generate_folder_name(start, end, threshold, k, use_market_filter)
        output_dir = Path(self.paths['holdout_results']) / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # 執行每月定期定額投資
        # 執行一次訓練，然後用四種策略進場
        self._log("開始執行多策略回測（訓練一次，四種進場策略）", "info", force_print=True)
        try:
            result = self._execute_multi_strategy_backtest(
                stock_predictors, start, end, threshold, k, use_market_filter, monthly_investment, session_id, output_dir
            )
            if not isinstance(result, tuple) or len(result) != 2:
                self._log(f"多策略回測回傳異常: {type(result)}", "error", force_print=True)
                raise ValueError("多策略回測回傳格式錯誤")
            strategy_monthlies, strategy_trades = result
        except Exception as e:
            self._log(f"多策略回測執行失敗: {e}", "error", force_print=True)
            raise

        # 用 Original 做整體績效（維持兼容）
        monthly_results = strategy_monthlies['original']
        self._log(f"🔍 DEBUG: monthly_results 數量: {len(monthly_results)}", "info", force_print=True)
        self._log(f"🔍 DEBUG: strategy_monthlies 所有策略數量: {[(k, len(v)) for k, v in strategy_monthlies.items()]}", "info", force_print=True)

        if monthly_results:
            self._log(f"🔍 DEBUG: 第一個月結果: {monthly_results[0]}", "info", force_print=True)
        else:
            # 如果 Original 策略為空，檢查其他策略
            self._log("⚠️  Original 策略月報為空，檢查其他策略", "warning", force_print=True)
            for strategy_name, strategy_data in strategy_monthlies.items():
                if strategy_data:
                    self._log(f"🔍 DEBUG: 使用策略 {strategy_name} 的數據作為摘要基礎", "info", force_print=True)
                    monthly_results = strategy_data
                    break

        # 計算整體績效
        portfolio_metrics = self._calculate_monthly_investment_metrics(monthly_results, monthly_investment)
        self._log(f"🔍 DEBUG: portfolio_metrics: {portfolio_metrics}", "info", force_print=True)

        # 生成詳細交易記錄DataFrame（Original）
        trades_df = strategy_trades['original']
        self._log(f"🔍 DEBUG: trades_df 形狀: {trades_df.shape if hasattr(trades_df, 'shape') else 'No shape'}", "info", force_print=True)

        # 保存結果到CSV/JSON（維持原有流程）
        self._save_monthly_investment_results(monthly_results, portfolio_metrics, trades_df, start, end, monthly_investment, threshold, k, use_market_filter, session_id, output_dir, strategy_trades)
        # 備註：若需要將策略標記寫入每筆交易，可在 trade_record 新增 'strategy': s，
        # 之後在輸出交易明細時用於分組或過濾。


        # 另存多策略Excel（4個sheet）：holdout_monthly.xlsx 與 holdout_trades.xlsx
        self._log("🔍 DEBUG: 準備輸出多策略Excel", "info", force_print=True)
        self._log(f"🔍 DEBUG: strategy_monthlies type: {type(strategy_monthlies)}", "info", force_print=True)
        self._log(f"🔍 DEBUG: strategy_trades type: {type(strategy_trades)}", "info", force_print=True)
        try:
            self._save_multi_strategy_excel(strategy_monthlies, strategy_trades, session_id, output_dir)
            self._log("🔍 DEBUG: 多策略Excel輸出完成", "info", force_print=True)
        except Exception as e:
            self._log(f"🔍 DEBUG: 多策略Excel輸出失敗: {e}", "error", force_print=True)
            import traceback
            self._log(f"🔍 DEBUG: Excel輸出異常堆疊: {traceback.format_exc()}", "error", force_print=True)

        # 確保使用有數據的策略作為摘要基礎
        if not monthly_results:
            for strategy_name, strategy_data in strategy_monthlies.items():
                if strategy_data:
                    self._log(f"🔍 DEBUG: 摘要使用策略 {strategy_name} 的數據", "info", force_print=True)
                    monthly_results = strategy_data
                    portfolio_metrics = self._calculate_monthly_investment_metrics(monthly_results, monthly_investment)
                    break

        self._log(f"🔍 DEBUG: 最終摘要 - monthly_results數量: {len(monthly_results)}, portfolio_metrics: {portfolio_metrics}", "info", force_print=True)

        return {
            'success': True,
            'backtest_type': 'monthly_investment',
            'monthly_investment': monthly_investment,
            'start_date': start,
            'end_date': end,
            'monthly_results': monthly_results,
            'portfolio_metrics': portfolio_metrics,
            'trades_df': trades_df,
            'params': {}
        }

    def _execute_multi_strategy_backtest(self,
                                       stock_predictors: Dict[str, StockPricePredictor],
                                       start: str,
                                       end: str,
                                       threshold: float,
                                       k: int,
                                       use_market_filter: bool,
                                       monthly_investment: float,
                                       session_id: str,
                                       output_dir: Path) -> tuple[Dict[str, List[Dict[str, Any]]], Dict[str, pd.DataFrame]]:
        """先完成每月訓練與預測一次，再用 original/A/B/C 四種進場策略產生各自的交易與月報。"""

        self._log("🔍 DEBUG: 進入 _execute_multi_strategy_backtest 函式", "info", force_print=True)

        try:
            # 產出四個容器
            strategy_monthlies: Dict[str, List[Dict[str, Any]]] = {s: [] for s in ['original','A','B','C']}
            strategy_trades: Dict[str, list] = {s: [] for s in ['original','A','B','C']}
            self._log("🔍 DEBUG: 初始化容器完成", "info", force_print=True)

            # 取得所有月份（使用與其他流程一致的做法）
            months = pd.date_range(start=start, end=end, freq='M')
            total_months = len(months)
            self._log(f"共 {total_months} 個月份", "info")

            self._log("🔍 DEBUG: 開始月份迴圈", "info", force_print=True)

            # 主迴圈：每個月訓練一次，並用四種策略生成當月交易
            for month_idx, month_end in enumerate(months, 1):
                month_str = month_end.strftime('%Y-%m')
                as_of = month_end.strftime('%Y-%m-%d')

                # 市場濾網
                if use_market_filter and not self._is_market_ok(as_of):
                    self._log(f"市場濾網觸發，跳過 {month_str}", "info")
                    for s in strategy_monthlies.keys():
                        strategy_monthlies[s].append({
                            'month': month_str,
                            'market_filter_triggered': True,
                            'selected_stocks': [],
                            'investment_amount': 0,
                            'month_end_value': 0,
                            'return_rate': 0,
                            'trades': []
                        })
                    continue

                # 訓練並取得該月所有股票的預測（一次）
                self._log(f"🔍 DEBUG: {month_str} 開始取得預測", "info", force_print=True)
                month_predictions = self._get_monthly_predictions(stock_predictors, month_str, threshold)
                self._log(f"🔍 DEBUG: {month_str} 預測結果數量: {len(month_predictions) if month_predictions else 0}", "info", force_print=True)

                if not month_predictions:
                    self._log(f"{month_str}: 無符合條件股票", "info")
                    for s in strategy_monthlies.keys():
                        strategy_monthlies[s].append({
                            'month': month_str,
                            'market_filter_triggered': False,
                            'selected_stocks': [],
                            'investment_amount': 0,
                            'month_end_value': 0,
                            'return_rate': 0,
                            'trades': []
                        })
                    continue

                # 依 top_k 取前K檔（0或負數代表不限制）
                if isinstance(k, int) and k > 0:
                    selected_list = month_predictions[:k]
                else:
                    selected_list = month_predictions

                self._log(f"🔍 DEBUG: {month_str} 選股後數量: {len(selected_list)}, top_k={k}", "info", force_print=True)

                # 本月各策略的結果快取（避免受外部容器影響）
                month_results_this_month: Dict[str, Dict[str, Any]] = {}
                month_trades_this_month: Dict[str, List[Dict[str, Any]]] = {}

                # 對四種策略各自做進場檢查與下單
                for strategy in ['original','A','B','C']:
                    self._log(f"🔍 DEBUG: {month_str} 開始處理策略 {strategy}", "info", force_print=True)
                    trades = []
                    total_investment = 0
                    total_month_end_value = 0

                    # 依當月實際可投資檔數決定每檔配額（先用平均分配）
                    num_selected = len(selected_list)
                    per_stock_investment = monthly_investment / num_selected if num_selected > 0 else 0
                    self._log(f"🔍 DEBUG: {month_str} 策略 {strategy} 每檔配額: {per_stock_investment}", "info", force_print=True)

                    for stock_info in selected_list:
                        stock_id = stock_info['stock_id']
                        predicted_return = stock_info['predicted_return']
                        self._log(f"🔍 DEBUG: {month_str} 策略 {strategy} 處理股票 {stock_id}, 預測報酬: {predicted_return:.4f}", "info", force_print=True)

                        # 初始化變數
                        entry_date = None
                        entry_price = None

                        entry_base = self._get_last_trading_day_of_month(month_str)
                        if not entry_base:
                            self._log(f"🔍 DEBUG: {stock_id} 無法取得月底交易日，跳過", "warning", force_print=True)
                            continue

                        if strategy == 'C':
                            # 方案C改為等待觸發：從 base_entry 開始觀察最多N個交易日
                            _res = self._find_strategy_c_trigger_entry(stock_id, entry_base)
                            if not isinstance(_res, tuple) or len(_res) != 2:
                                self._log(f"🔍 DEBUG: {stock_id} 方案C觸發搜尋回傳異常，跳過", "warning", force_print=True)
                                continue
                            entry_date, entry_price = _res
                            if entry_price is None or entry_price <= 0:
                                self._log(f"🔍 DEBUG: {stock_id} 方案C無有效進場價格，跳過", "warning", force_print=True)
                                continue
                        else:
                            # Original/A/B 使用單日快照（遇無價往後回補到最近交易日）
                            _res = self._find_next_trading_day_with_price(stock_id, entry_base, max_forward_days=7)
                            if not isinstance(_res, tuple) or len(_res) != 2:
                                self._log(f"🔍 DEBUG: {stock_id} 進場日回補回傳異常，跳過", "warning", force_print=True)
                                continue
                            entry_date, entry_price = _res
                            if entry_price is None or entry_price <= 0:
                                self._log(f"🔍 DEBUG: {stock_id} 無有效進場價格，跳過", "warning", force_print=True)
                                continue

                        self._log(f"🔍 DEBUG: {stock_id} 策略 {strategy} 進場價格: {entry_price}", "info", force_print=True)

                        # 價格上限檢查（所有策略都要檢查）
                        price_limit = self.backtest_cfg.get('entry_strategies', {}).get('price_upper_limit', 500)
                        if entry_price > price_limit:
                            self._log(f"🔍 DEBUG: {stock_id} 價格 {entry_price} 超過上限 {price_limit}，跳過", "warning", force_print=True)
                            continue

                        # A/B 的技術策略檢查（Original 不檢查，C 已於掃描中檢查）
                        if strategy in ('A','B'):
                            indicators = self._calculate_technical_indicators(stock_id, entry_date, lookback_days=self.backtest_cfg.get('entry_strategies', {}).get('lookback_days', 60))
                            ok, _ = self._check_entry_by_strategy(strategy, indicators)
                            if not ok:
                                self._log(f"🔍 DEBUG: {stock_id} 策略 {strategy} 技術條件不符，跳過", "warning", force_print=True)
                                continue

                        # 股數試算
                        shares = self._calculate_shares_after_costs(per_stock_investment, entry_price)
                        self._log(f"🔍 DEBUG: {stock_id} 策略 {strategy} 計算股數: {shares}", "info", force_print=True)
                        if shares <= 0:
                            self._log(f"🔍 DEBUG: {stock_id} 股數不足，跳過", "warning", force_print=True)
                            continue

                        trade_info = self._execute_trade(stock_id, entry_date, 20, shares)
                        if not trade_info:
                            self._log(f"🔍 DEBUG: {stock_id} 交易執行失敗，跳過", "warning", force_print=True)
                            continue

                        self._log(f"🔍 DEBUG: {stock_id} 策略 {strategy} 交易成功！", "info", force_print=True)

                        # 最終檢查：確保 entry_price 不是 None
                        if entry_price is None:
                            self._log(f"🔍 DEBUG: {stock_id} entry_price 為 None，跳過", "error", force_print=True)
                            continue

                        # 計算月底價值（含成本）
                        actual_investment = shares * entry_price
                        gross_value = shares * trade_info['exit_price']
                        transaction_costs = trade_info.get('transaction_costs', {})
                        cost_amount = transaction_costs.get('total_cost_amount', 0) if isinstance(transaction_costs, dict) else 0
                        stock_month_end_value = gross_value - cost_amount

                        # 建立統一的交易記錄格式
                        trade_record = {
                            'entry_date': entry_date,
                            'stock_id': stock_id,
                            'model_type': stock_info.get('model_type', 'unknown'),
                            'predicted_return': predicted_return,
                            'entry_price': entry_price,
                            'exit_date': trade_info['exit_date'],
                            'exit_price': trade_info['exit_price'],
                            'holding_days': trade_info['holding_days'],

                            # 選項5的計算方式（等權重，無交易成本）對齊欄位名稱
                            'actual_return_gross': trade_info.get('gross_return', trade_info['actual_return']),
                            'profit_loss_gross': trade_info.get('gross_profit_loss', trade_info['profit_loss']),
                            'max_return_20d': trade_info.get('max_return'),
                            'min_return_20d': trade_info.get('min_return'),

                            # 選項5a的計算方式（定期定額，含交易成本）
                            'shares': shares,
                            'investment_amount': actual_investment,
                            'month_end_value': stock_month_end_value,
                            'actual_return_net': trade_info['actual_return'],
                            'profit_loss_net': trade_info['profit_loss'],
                            'transaction_costs': transaction_costs,

                            # 成本影響
                            'cost_impact': trade_info.get('gross_return', trade_info['actual_return']) - trade_info['actual_return'],

                            # 圖表標準欄位
                            'actual_return': trade_info['actual_return'],
                            'profit_loss': trade_info['profit_loss']
                        }

                        self._log(f"🔍 DEBUG: {stock_id} 策略 {strategy} 準備添加交易記錄", "info", force_print=True)
                        trades.append(trade_record)
                        self._log(f"🔍 DEBUG: {stock_id} 策略 {strategy} 交易記錄已添加，當前trades數量: {len(trades)}", "info", force_print=True)

                    # 當月統計（彙總本策略本月交易結果）
                    self._log(f"🔍 DEBUG: {month_str} 策略 {strategy} 開始統計，trades數量: {len(trades)}", "info", force_print=True)
                    for t in trades:
                        total_investment += t.get('investment_amount', 0)
                        total_month_end_value += t.get('month_end_value', 0)
                    month_return_rate = (total_month_end_value - total_investment) / total_investment if total_investment > 0 else 0
                    self._log(f"🔍 DEBUG: {month_str} 策略 {strategy} 統計完成", "info", force_print=True)

                    self._log(f"🔍 DEBUG: {month_str} 策略 {strategy} 完成，交易數: {len(trades)}, 投資: {total_investment}, 價值: {total_month_end_value}", "info", force_print=True)

                    # 用拷貝保存當月交易，避免後續變更影響
                    monthly_trades_copy = [dict(t) for t in trades]
                    monthly_result = {
                        'month': month_str,
                        'market_filter_triggered': False,
                        'selected_stocks': [t['stock_id'] for t in monthly_trades_copy],
                        'investment_amount': total_investment,
                        'month_end_value': total_month_end_value,
                        'return_rate': month_return_rate,
                        'trades': monthly_trades_copy
                    }

                    self._log(f"🔍 DEBUG: {month_str} 策略 {strategy} 準備添加月報記錄", "info", force_print=True)
                    self._log(f"🔍 DEBUG: {month_str} 策略 {strategy} 準備添加 {len(monthly_trades_copy)} 筆交易到 strategy_trades", "info", force_print=True)

                    # 同時寫入容器與本月快取
                    strategy_monthlies[strategy].append(monthly_result)
                    strategy_trades[strategy].extend([dict(t) for t in monthly_trades_copy])
                    month_results_this_month[strategy] = monthly_result
                    month_trades_this_month[strategy] = monthly_trades_copy

                    self._log(f"🔍 DEBUG: {month_str} 策略 {strategy} 月報記錄已添加，當前總數: {len(strategy_monthlies[strategy])}", "info", force_print=True)
                    self._log(f"🔍 DEBUG: {month_str} 策略 {strategy} 交易記錄已添加，strategy_trades[{strategy}] 總數: {len(strategy_trades[strategy])}", "info", force_print=True)

                # 若已完成四策略中的最後一個（C），於本月結束立即輸出單月小結
                if strategy == 'C':
                    try:
                        self._log(f"🔍 DEBUG: {month_str} 準備輸出單月小結", "info", force_print=True)

                        # 僅用本月快取，避免任何外部容器誤差
                        monthlies_for_month = {k: month_results_this_month.get(k, {}) for k in ['original','A','B','C']}
                        month_trades_df = {k: pd.DataFrame(month_trades_this_month.get(k, [])) for k in ['original','A','B','C']}
                        for k in ['original','A','B','C']:
                            self._log(f"🔍 DEBUG: {month_str} 單月檢視 策略 {k} 交易數量(本月): {len(month_trades_df[k])}", "info", force_print=True)

                        self._save_monthly_summary_excel_immediately(month_str, monthlies_for_month, month_trades_df, session_id, output_dir)
                    except Exception as e:
                        self._log(f"單月小結輸出失敗 {month_str}: {e}", "warning")
                        import traceback
                        self._log(f"異常詳情: {traceback.format_exc()}", "warning")

            # 轉為 DataFrame
            self._log("🔍 DEBUG: 開始轉換 DataFrame", "info", force_print=True)
            strategy_trades_df = {k: (pd.DataFrame(v) if v else pd.DataFrame()) for k, v in strategy_trades.items()}
            self._log(f"🔍 DEBUG: DataFrame轉換完成，準備回傳結果", "info", force_print=True)
            self._log(f"🔍 DEBUG: strategy_monthlies keys: {list(strategy_monthlies.keys())}", "info", force_print=True)
            self._log(f"🔍 DEBUG: strategy_trades_df keys: {list(strategy_trades_df.keys())}", "info", force_print=True)
            return strategy_monthlies, strategy_trades_df

        except Exception as e:
            self._log(f"🔍 DEBUG: 多策略回測執行過程異常: {e}", "error", force_print=True)
            import traceback
            self._log(f"🔍 DEBUG: 異常堆疊: {traceback.format_exc()}", "error", force_print=True)
            # 回傳空結果避免解包錯誤
            empty_monthlies = {s: [] for s in ['original','A','B','C']}
            empty_trades = {s: pd.DataFrame() for s in ['original','A','B','C']}
            return empty_monthlies, empty_trades

    def _find_strategy_c_trigger_entry(self, stock_id: str, base_entry_date: str) -> tuple[str | None, float | None]:
        """方案C等待觸發：自 base_entry_date 起，向後觀察最多N個交易日，遇到符合C條件的收盤價即進場。
        回傳(觸發日期, 收盤價)，若未觸發回傳(None, None)。"""
        try:
            cfg = self.backtest_cfg.get('entry_strategies', {})
            c_cfg = cfg.get('strategy_C', {})
            window_days = int(c_cfg.get('signal_window_days', 10))
            allow_cross = bool(c_cfg.get('allow_month_cross', True))

            # 以自然日向後掃描，逐日檢查是否有交易與價格
            from datetime import datetime, timedelta
            dt = datetime.strptime(base_entry_date, '%Y-%m-%d')
            for i in range(0, window_days):
                date_i = dt + timedelta(days=i)
                date_str = date_i.strftime('%Y-%m-%d')

                # 取得當日收盤價（遇非交易日會 None）
                price = self._get_stock_price(stock_id, date_str)
                if price is None or price <= 0:
                    continue

                # 價格上限
                price_limit = cfg.get('price_upper_limit', 500)
                if price > price_limit:
                    continue

                # 技術指標檢查（C）
                indicators = self._calculate_technical_indicators(stock_id, date_str, lookback_days=cfg.get('lookback_days', 60))
                ok, _ = self._check_entry_by_strategy('C', indicators)
                if ok:
                    if i > 0:
                        self._log(f"{stock_id} 方案C觸發: {base_entry_date} → {date_str}", "info")
                    return date_str, price

            return None, None
        except Exception as e:
            self._log(f"方案C等待觸發失敗 {stock_id} {base_entry_date}: {e}", "warning")
            return None, None

        # 取消：舊版單月小結輸出（避免重複與覆寫），保留在 C 策略結束時輸出
        # try:
        #     month_trades_df = {k: (pd.DataFrame(v) if v else pd.DataFrame()) for k, v in strategy_trades.items()}
        #     monthlies_for_month = {k: strategy_monthlies[k][-1] for k in strategy_monthlies.keys()}
        #     self._save_monthly_summary_excel_immediately(month_str, monthlies_for_month, month_trades_df, session_id, output_dir)
        # except Exception as e:
        #     self._log(f"單月小結Excel輸出失敗 {month_str}: {e}", "warning")

        #     # 轉為 DataFrame
        #     self._log("🔍 DEBUG: 開始轉換 DataFrame", "info", force_print=True)
        #     strategy_trades_df = {k: (pd.DataFrame(v) if v else pd.DataFrame()) for k, v in strategy_trades.items()}
        #     self._log(f"🔍 DEBUG: DataFrame轉換完成，準備回傳結果", "info", force_print=True)
        #     self._log(f"🔍 DEBUG: strategy_monthlies keys: {list(strategy_monthlies.keys())}", "info", force_print=True)
        #     self._log(f"🔍 DEBUG: strategy_trades_df keys: {list(strategy_trades_df.keys())}", "info", force_print=True)
        #     return strategy_monthlies, strategy_trades_df

        except Exception as e:
            self._log(f"🔍 DEBUG: 多策略回測執行過程異常: {e}", "error", force_print=True)
            import traceback
            self._log(f"🔍 DEBUG: 異常堆疊: {traceback.format_exc()}", "error", force_print=True)
            # 回傳空結果避免解包錯誤
            empty_monthlies = {s: [] for s in ['original','A','B','C']}
            empty_trades = {s: pd.DataFrame() for s in ['original','A','B','C']}
            return empty_monthlies, empty_trades



    def _execute_monthly_investment_backtest(self,
                                           stock_predictors: Dict[str, StockPricePredictor],
                                           start_date: str,
                                           end_date: str,
                                           threshold: float,
                                           top_k: int,
                                           use_market_filter: bool,
                                           monthly_investment: float,
                                           session_id: str = None,
                                           output_dir: Path = None,
                                           strategy: str = 'original') -> List[Dict[str, Any]]:
        """執行每月定期定額投資回測的核心邏輯（可指定進場策略 original/A/B/C）"""

        monthly_results = []

        # 生成月份列表
        months = pd.date_range(start=start_date, end=end_date, freq='M')
        total_months = len(months)

        self._log(f"📊 總投資月數: {total_months} 個月", "info", force_print=True)

        for month_idx, month_end in enumerate(months, 1):
            month_str = month_end.strftime('%Y-%m')
            as_of = month_end.strftime('%Y-%m-%d')

            # 顯示月度進度
            progress_percent = (month_idx / total_months) * 100
            progress_bar = self._create_progress_bar(month_idx, total_months)
            self._log(f"💰 進度 [{month_idx:2d}/{total_months}] {progress_bar} {progress_percent:5.1f}% - 處理 {month_str}", "info", force_print=True)

            # 市場濾網檢查
            if use_market_filter and not self._is_market_ok(as_of):
                self._log(f"⚠️  市場濾網觸發，跳過 {month_str}", "info", force_print=True)
                market_filter_result = {
                    'month': month_str,
                    'market_filter_triggered': True,
                    'selected_stocks': [],
                    'investment_amount': 0,
                    'month_end_value': 0,
                    'return_rate': 0,
                    'trades': []
                }
                monthly_results.append(market_filter_result)

                # 立即保存市場濾網觸發的結果
                if session_id and output_dir:
                    self._save_monthly_investment_result_immediately(market_filter_result, session_id, output_dir)

                continue

            # 為每檔股票訓練模型並預測
            predictions = []
            stock_list = list(stock_predictors.keys())

            for stock_idx, stock_id in enumerate(stock_list, 1):
                # 顯示股票處理進度（只在詳細模式下顯示）
                if self.verbose_logging:
                    stock_progress = self._create_progress_bar(stock_idx, len(stock_list), width=10)
                    self._log(f"   📊 [{stock_idx:2d}/{len(stock_list)}] {stock_progress} 訓練 {stock_id}", "info")

                try:
                    # 訓練模型（使用截至當月的資料）
                    features_df, targets_df = self.fe.generate_training_dataset(
                        stock_ids=[stock_id],
                        start_date='2015-01-01',
                        end_date=as_of
                    )

                    if features_df.empty:
                        continue

                    # 訓練模型
                    train_result = stock_predictors[stock_id].train(
                        feature_df=features_df,
                        target_df=targets_df
                    )

                    if not train_result['success']:
                        continue

                    # 預測
                    pred_result = stock_predictors[stock_id].predict(stock_id, as_of)
                    if pred_result['success']:
                        predictions.append({
                            'stock_id': stock_id,
                            'predicted_return': float(pred_result['predicted_return']),
                            'model_type': getattr(stock_predictors[stock_id], 'model_type', 'unknown')
                        })

                except Exception as e:
                    self._log(f"預測失敗 {stock_id}: {e}", "warning")
                    continue

            # 篩選股票
            filtered_predictions = self._filter_predictions(predictions, threshold, top_k)

            if not filtered_predictions:
                self._log(f"❌ {month_str}: 無符合條件的股票", "info", force_print=True)
                no_stocks_result = {
                    'month': month_str,
                    'market_filter_triggered': False,
                    'selected_stocks': [],
                    'investment_amount': 0,
                    'month_end_value': 0,
                    'return_rate': 0,
                    'trades': []
                }
                monthly_results.append(no_stocks_result)

                # 立即保存無符合條件股票的結果
                if session_id and output_dir:
                    self._save_monthly_investment_result_immediately(no_stocks_result, session_id, output_dir)

                continue

            # 計算每檔股票的投資金額（平均分配）
            per_stock_investment = monthly_investment / len(filtered_predictions)

            # 執行交易並計算月底價值
            month_trades = []
            total_month_end_value = 0

            for trade_idx, pred in enumerate(filtered_predictions, 1):
                stock_id = pred['stock_id']

                # 顯示交易執行進度（只在詳細模式下顯示）
                if self.verbose_logging:
                    trade_progress = self._create_progress_bar(trade_idx, len(filtered_predictions), width=10)
                    self._log(f"   💼 [{trade_idx:2d}/{len(filtered_predictions)}] {trade_progress} 交易 {stock_id}", "info")

                # 取得實際可用進場日與價格（遇假日/無價時往後尋找下一交易日）
                entry_date, entry_price = self._find_next_trading_day_with_price(stock_id, as_of, max_forward_days=7)
                if entry_price is None or (isinstance(entry_price, (int, float)) and entry_price <= 0):
                    # 找不到有效進場價，跳過以避免除零
                    self._log(f"{month_str} {stock_id} 進場價無效或不可得，跳過", "info")
                    continue

                # 股價過高直接跳過（以設定為準）
                price_limit = self.backtest_cfg.get('entry_strategies', {}).get('price_upper_limit', 500)
                if entry_price > price_limit:
                    self._log(f"{month_str} {stock_id} 進場價 {entry_price:.2f} > {price_limit}，跳過", "info")
                    continue

                # 技術策略檢查（原始策略略過）
                if strategy in ('A','B','C'):
                    indicators = self._calculate_technical_indicators(stock_id, entry_date, lookback_days=self.backtest_cfg.get('entry_strategies', {}).get('lookback_days', 60))
                    ok, reason = self._check_entry_by_strategy(strategy, indicators)
                    if not ok:
                        self._log(f"{month_str} {stock_id} 技術條件不符: {reason}", "info")
                        continue

                # 計算可買股數（扣除交易成本後），資金不足則跳過
                shares = self._calculate_shares_after_costs(per_stock_investment, entry_price)
                if shares <= 0:
                    self._log(f"{month_str} {stock_id} 資金不足（每檔配額 {per_stock_investment:,.0f}），跳過", "info")
                    continue

                actual_investment = shares * entry_price

                # 執行20日交易（以實際進場日為基準傳入）
                trade_info = self._execute_trade(stock_id, entry_date, 20, shares)
                if trade_info:
                    # 計算該股票的月底價值（扣除交易成本）
                    gross_value = shares * trade_info['exit_price']
                    transaction_costs = trade_info.get('transaction_costs', {})
                    cost_amount = transaction_costs.get('total_cost_amount', 0) if isinstance(transaction_costs, dict) else 0
                    stock_month_end_value = gross_value - cost_amount
                    total_month_end_value += stock_month_end_value

                    # 記錄交易（包含兩種計算方式）
                    trade_record = {
                        # 基本資訊
                        'entry_date': entry_date,
                        'stock_id': stock_id,
                        'model_type': pred.get('model_type', 'unknown'),
                        'predicted_return': pred['predicted_return'],
                        'entry_price': entry_price,
                        'exit_date': trade_info['exit_date'],
                        'exit_price': trade_info['exit_price'],
                        'holding_days': trade_info['holding_days'],

                        # 選項5的計算方式（等權重，無交易成本）
                        'actual_return_gross': trade_info.get('gross_return', trade_info['actual_return']),
                        'profit_loss_gross': trade_info.get('gross_profit_loss', trade_info['profit_loss']),
                        'max_return_20d': trade_info.get('max_return'),
                        'min_return_20d': trade_info.get('min_return'),

                        # 選項5a的計算方式（定期定額，含交易成本）
                        'shares': shares,
                        'investment_amount': actual_investment,
                        'month_end_value': stock_month_end_value,
                        'actual_return_net': trade_info['actual_return'],  # 淨報酬
                        'profit_loss_net': trade_info['profit_loss'],      # 淨損益
                        'transaction_costs': trade_info.get('transaction_costs', {}),

                        # 交易成本影響分析
                        'cost_impact': trade_info.get('gross_return', trade_info['actual_return']) - trade_info['actual_return'],

                        # 為圖表生成提供標準欄位（使用淨報酬作為主要報酬）
                        'actual_return': trade_info['actual_return'],  # 淨報酬，用於圖表生成
                        'profit_loss': trade_info['profit_loss']       # 淨損益，用於圖表生成
                    }
                    month_trades.append(trade_record)

            # 計算當月整體報酬率
            total_investment = sum(t['investment_amount'] for t in month_trades)
            if total_investment > 0:
                month_return_rate = (total_month_end_value - total_investment) / total_investment
            else:
                month_return_rate = 0
                # 如果沒有成功的投資，確保月底價值也是0
                total_month_end_value = 0

            # 記錄當月結果
            monthly_result = {
                'month': month_str,
                'market_filter_triggered': False,
                'selected_stocks': [p['stock_id'] for p in filtered_predictions],
                'investment_amount': total_investment,
                'month_end_value': total_month_end_value,
                'return_rate': month_return_rate,
                'trades': month_trades
            }
            monthly_results.append(monthly_result)

            # 立即保存當月結果到檔案（與選項5相同）
            if session_id and output_dir:
                self._save_monthly_investment_result_immediately(monthly_result, session_id, output_dir)

            # 顯示當月結果
            self._log(f"✅ {month_str}: 投資 {total_investment:,.0f} 元，月底價值 {total_month_end_value:,.0f} 元，報酬率 {month_return_rate:.2%}",
                     "info", force_print=True)

        return monthly_results

    def _calculate_shares_after_costs(self, investment_amount: float, entry_price: float) -> int:
        """計算扣除交易成本後可購買的股數"""
        # 檢查參數有效性
        if entry_price <= 0 or investment_amount <= 0:
            return 0

        costs = self.trading_cfg['transaction_costs']

        # 買進時的成本率（手續費 + 滑價）
        buy_cost_rate = costs['commission_rate'] + (costs['slippage_bps'] / 10000)

        # 可用於購買股票的金額（扣除買進成本）
        available_amount = investment_amount / (1 + buy_cost_rate)

        # 計算股數（向下取整到1000股的倍數，台股通常以1000股為單位）
        max_shares = int(available_amount / entry_price / 1000) * 1000

        # 至少需買1000股，否則視為資金不足不下單
        if max_shares < 1000:
            return 0
        else:
            return max_shares

    def _calculate_monthly_investment_metrics(self, monthly_results: List[Dict[str, Any]], monthly_investment: float) -> Dict[str, Any]:
        """計算每月定期定額投資的整體績效指標（中文欄位友善）"""
        if not monthly_results:
            return {
                'total_invested': 0,
                'total_current_value': 0,
                'total_return': 0,
                'total_profit_loss': 0,
                'avg_monthly_return': 0,
                'monthly_volatility': 0,
                'annualized_return': 0,
                'annualized_volatility': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'monthly_win_rate': 0,
                'total_trades': 0,
                'total_months': 0,
                'successful_months': 0
            }

        # 計算累積投資和價值
        total_invested = 0
        total_current_value = 0
        monthly_returns: List[float] = []
        cumulative_values: List[float] = []

        for result in monthly_results:
            total_invested += float(result.get('investment_amount', 0) or 0)
            total_current_value += float(result.get('month_end_value', 0) or 0)
            monthly_returns.append(float(result.get('return_rate', 0) or 0))
            cumulative_values.append(total_current_value)

        # 基本指標
        total_return = (total_current_value - total_invested) / total_invested if total_invested > 0 else 0

        # 月度報酬統計（排除無交易月份的0）
        try:
            monthly_returns_series = pd.Series([r for r in monthly_returns if r != 0])
        except Exception:
            monthly_returns_series = pd.Series([])

        if len(monthly_returns_series) > 0:
            avg_monthly_return = float(monthly_returns_series.mean())
            monthly_volatility = float(monthly_returns_series.std())
            win_rate = float((monthly_returns_series > 0).mean())

            # 年化指標
            annualized_return = (1 + avg_monthly_return) ** 12 - 1
            annualized_volatility = monthly_volatility * (12 ** 0.5)
            sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility > 0 else 0
        else:
            avg_monthly_return = 0.0
            monthly_volatility = 0.0
            win_rate = 0.0
            annualized_return = 0.0
            annualized_volatility = 0.0
            sharpe_ratio = 0.0

        # 最大回撤計算（基於累積價值序列）
        peak_value = 0.0
        max_drawdown = 0.0
        for value in cumulative_values:
            if value > peak_value:
                peak_value = value
            drawdown = (peak_value - value) / peak_value if peak_value > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)

        # 交易統計
        total_trades = sum(len(result.get('trades', [])) for result in monthly_results)
        successful_months = sum(1 for result in monthly_results if float(result.get('return_rate', 0) or 0) > 0)
        total_months = len([r for r in monthly_results if float(r.get('investment_amount', 0) or 0) > 0])

        # 收集所有交易記錄
        all_trades: List[Dict[str, Any]] = []
        for result in monthly_results:
            all_trades.extend(result.get('trades', []))

        return {
            'total_invested': total_invested,
            'total_current_value': total_current_value,
            'total_return': total_return,
            'total_profit_loss': total_current_value - total_invested,
            'avg_monthly_return': avg_monthly_return,
            'monthly_volatility': monthly_volatility,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'monthly_win_rate': (successful_months / total_months) if total_months > 0 else 0,
            'total_trades': total_trades,
            'total_months': total_months,
            'successful_months': successful_months
        }

    def _rename_trades_to_chinese(self, df: pd.DataFrame) -> pd.DataFrame:
        """將交易明細欄位改為中文以便輸出Excel/CSV一致。"""
        if df is None or df.empty:
            return df if df is not None else pd.DataFrame()
        column_mapping = {
            'entry_date': '進場日',
            'stock_id': '股票代號',
            'model_type': '模型',
            'predicted_return': '預測報酬',
            'entry_price': '進場價',
            'exit_date': '出場日',
            'exit_price': '出場價',
            'holding_days': '持有天數',
            'actual_return_gross': '毛報酬',
            'profit_loss_gross': '毛損益',
            'max_return_20d': '20日最大報酬',
            'min_return_20d': '20日最小報酬',
            'shares': '股數',
            'investment_amount': '投資金額',
            'month_end_value': '月底價值',
            'actual_return_net': '淨報酬',
            'profit_loss_net': '淨損益',
            'transaction_costs': '交易成本',
            'cost_impact': '成本影響',
        }
        renamed = df.rename(columns=column_mapping)
        # 依常用順序輸出（若欄位不存在則忽略）
        desired_order = [
            '進場日','股票代號','模型','預測報酬','進場價','出場日','出場價','持有天數',
            '股數','投資金額','月底價值','毛報酬','毛損益','淨報酬','淨損益','20日最大報酬','20日最小報酬','交易成本','成本影響'
        ]
        ordered = [c for c in desired_order if c in renamed.columns]
        return renamed[ordered] if ordered else renamed

    def _save_monthly_summary_excel_immediately(self, month_str: str, strategy_monthlies_for_month: Dict[str, Dict[str, Any]], strategy_trades_for_month: Dict[str, pd.DataFrame], session_id: str, output_dir: Path):
        """將單月四策略的小結立即輸出為Excel。"""
        try:
            # 準備月報單列DataFrame
            def to_df(row: Dict[str, Any]) -> pd.DataFrame:
                data = [{
                    '月份': row.get('month'),
                    '市場濾網觸發': row.get('market_filter_triggered', False),
                    '入選股票數': len(row.get('selected_stocks', [])),
                    '入選股票': ', '.join(row.get('selected_stocks', [])[:5]) + ('...' if len(row.get('selected_stocks', [])) > 5 else ''),
                    '投資金額': row.get('investment_amount', 0),
                    '月底價值': row.get('month_end_value', 0),
                    '月報酬率': row.get('return_rate', 0),
                    '交易筆數': len(row.get('trades', []))
                }]
                return pd.DataFrame(data)

            monthly_dfs = {k: to_df(v) for k, v in strategy_monthlies_for_month.items()}
            trades_dfs = {k: self._rename_trades_to_chinese(v) for k, v in strategy_trades_for_month.items()}

            # Excel 引擎
            engine = None
            try:
                import xlsxwriter  # noqa
                engine = 'xlsxwriter'
            except Exception:
                try:
                    import openpyxl  # noqa
                    engine = 'openpyxl'
                except Exception:
                    engine = None
            if engine is None:
                self._log("未安裝Excel引擎，略過單月小結Excel輸出。", "warning")
                return

            # 檔名
            monthly_xlsx = output_dir / f"holdout_monthly_{session_id}_{month_str}.xlsx"
            with pd.ExcelWriter(monthly_xlsx, engine=engine) as writer:
                for key, sheet_name in [('original','原本'),('A','方案A'),('B','方案B'),('C','方案C')]:
                    monthly_dfs.get(key, pd.DataFrame()).to_excel(writer, index=False, sheet_name=sheet_name)
                    # 加上交易明細（中文欄位）
                    td = trades_dfs.get(key, pd.DataFrame())
                    if td is not None and not td.empty:
                        td.to_excel(writer, index=False, sheet_name=f"{sheet_name}_交易")
            self._log(f"已輸出單月小結Excel: holdout_monthly_{session_id}_{month_str}.xlsx", "info")
        except Exception as e:
            self._log(f"單月小結Excel輸出失敗 {month_str}: {e}", "warning")



    def _save_monthly_investment_results(self, monthly_results: List[Dict[str, Any]],
                                       portfolio_metrics: Dict[str, Any],
                                       trades_df: pd.DataFrame,
                                       start_date: str, end_date: str,
                                       monthly_investment: float,
                                       threshold: float, k: int, use_market_filter: bool,
                                       session_id: str, output_dir: Path,
                                       strategy_trades: Dict[str, pd.DataFrame] = None):
        """保存每月定期定額投資結果到CSV檔案（使用已存在的目錄和會話ID）"""
        try:
            from datetime import datetime
            import json

            # 初始化停損停利分析結果容器
            all_stop_analysis = {}

            # 使用傳入的會話ID作為時間戳（與每月報告保持一致）
            ts = session_id

            # 使用已存在的輸出目錄（與每月報告在同一位置）
            # output_dir 已經在調用時傳入，不需要重新創建

            # 1. 保存詳細交易記錄CSV（包含兩種計算方式）- 使用中文欄位名稱
            if not trades_df.empty:
                csv_path = output_dir / f'holdout_trades_{ts}.csv'

                # 定義中文欄位名稱對照表（與選單5b對齊）
                column_mapping = {
                    'entry_date': '進場日',
                    'stock_id': '股票代號',
                    'model_type': '模型',
                    'predicted_return': '預測報酬',
                    'entry_price': '進場價',
                    'exit_date': '出場日',
                    'exit_price': '出場價',
                    'holding_days': '持有天數',
                    'actual_return_gross': '毛報酬',
                    'profit_loss_gross': '毛損益',
                    'max_return_20d': '20日最大報酬',
                    'min_return_20d': '20日最小報酬',
                    'shares': '股數',
                    'investment_amount': '投資金額',
                    'month_end_value': '月底價值',
                    'actual_return_net': '淨報酬',
                    'profit_loss_net': '淨損益',
                    'transaction_costs': '交易成本',
                    'cost_impact': '成本影響'
                }

                # 重新命名欄位為中文
                trades_df_chinese = trades_df.rename(columns=column_mapping)
                trades_df_chinese.to_csv(csv_path, index=False, encoding='utf-8-sig')
                self._log(f"💾 交易記錄CSV已保存: {csv_path.name}", "info", force_print=True)

            # 2. 保存每月摘要CSV
            monthly_summary = []
            for result in monthly_results:
                summary_row = {
                    '月份': result['month'],
                    '市場濾網觸發': result.get('market_filter_triggered', False),
                    '入選股票數': len(result['selected_stocks']),
                    '入選股票': ', '.join(result['selected_stocks'][:5]) + ('...' if len(result['selected_stocks']) > 5 else ''),
                    '投資金額': result['investment_amount'],
                    '月底價值': result['month_end_value'],
                    '月報酬率': result['return_rate'],
                    '交易筆數': len(result['trades'])
                }
                monthly_summary.append(summary_row)

            if monthly_summary:
                monthly_df = pd.DataFrame(monthly_summary)
                monthly_csv_path = output_dir / f'monthly_summary_{ts}.csv'
                monthly_df.to_csv(monthly_csv_path, index=False, encoding='utf-8-sig')
                self._log(f"💾 每月摘要CSV已保存: {monthly_csv_path.name}", "info", force_print=True)

            # 3. 保存整體績效JSON（使用與選項5相同的命名）
            results_json = {
                'backtest_type': 'monthly_investment',
                'parameters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'monthly_investment': monthly_investment,
                    'min_predicted_return': threshold,
                    'top_k': k,
                    'use_market_filter': use_market_filter
                },
                'portfolio_metrics': portfolio_metrics,
                'monthly_results_count': len(monthly_results),
                'total_trades': len(trades_df) if not trades_df.empty else 0,
                'detailed_trades': trades_df.to_dict('records') if not trades_df.empty else [],
                'generated_at': datetime.now().isoformat()
            }

            json_path = output_dir / f'holdout_{ts}.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results_json, f, ensure_ascii=False, indent=2)
            self._log(f"💾 每月定期定額回測結果已保存: {json_path.name}", "info", force_print=True)

            # 4. 生成比較分析CSV（毛報酬 vs 淨報酬）
            if not trades_df.empty and 'actual_return_gross' in trades_df.columns:
                comparison_data = []
                for _, trade in trades_df.iterrows():
                    comparison_row = {
                        '股票代號': trade['stock_id'],
                        '進場日期': trade['entry_date'],
                        '毛報酬率': trade.get('actual_return_gross', 0),
                        '淨報酬率': trade.get('actual_return_net', 0),
                        '交易成本影響': trade.get('cost_impact', 0),
                        '投資金額': trade.get('investment_amount', 0),
                        '交易成本金額': trade.get('transaction_costs', {}).get('total_cost_amount', 0)
                    }
                    comparison_data.append(comparison_row)

                comparison_df = pd.DataFrame(comparison_data)
                comparison_csv_path = output_dir / f'cost_impact_analysis_{ts}.csv'
                comparison_df.to_csv(comparison_csv_path, index=False, encoding='utf-8-sig')
                self._log(f"💾 成本影響分析CSV已保存: {comparison_csv_path.name}", "info", force_print=True)

            # 5. 分析各策略最佳停損停利點
            if strategy_trades is not None:
                self._log("🎯 開始分析各策略最佳停損停利點...", "info", force_print=True)

                for strategy_name in ['original', 'A', 'B', 'C']:
                    strategy_trades_df = strategy_trades.get(strategy_name, pd.DataFrame())

                    if not strategy_trades_df.empty:
                        self._log(f"🎯 分析策略 {strategy_name} 的最佳停損停利...", "info", force_print=True)
                        try:
                            stop_analysis = self._analyze_optimal_stop_levels(strategy_trades_df)

                            if stop_analysis:
                                all_stop_analysis[strategy_name] = stop_analysis

                                # 保存各策略的停損停利分析結果
                                stop_analysis_path = output_dir / f'stop_loss_analysis_{strategy_name}_{ts}.json'
                                with open(stop_analysis_path, 'w', encoding='utf-8') as f:
                                    json.dump(stop_analysis, f, ensure_ascii=False, indent=2, default=str)
                                self._log(f"💾 策略 {strategy_name} 停損停利分析已保存: {stop_analysis_path.name}", "info", force_print=True)

                                # 保存最佳停損停利的詳細交易記錄
                                best_combination = stop_analysis.get('best_combination', {})
                                if best_combination and 'simulated_trades' in best_combination:
                                    stop_trades_df = pd.DataFrame(best_combination['simulated_trades'])
                                    stop_trades_csv_path = output_dir / f'optimal_stop_trades_{strategy_name}_{ts}.csv'
                                    stop_trades_df.to_csv(stop_trades_csv_path, index=False, encoding='utf-8-sig')
                                    self._log(f"💾 策略 {strategy_name} 最佳停損停利交易記錄已保存: {stop_trades_csv_path.name}", "info", force_print=True)

                        except Exception as e:
                            self._log(f"⚠️  策略 {strategy_name} 停損停利分析失敗: {e}", "warning", force_print=True)
                    else:
                        self._log(f"⚠️  策略 {strategy_name} 無交易記錄，跳過停損停利分析", "info")

                # 顯示所有策略的停損停利結果比較，同時生成 MD 檔案
                if all_stop_analysis:
                    # 生成 MD 內容
                    md_content = self._display_multi_strategy_stop_loss_results(all_stop_analysis)

                    # 保存 MD 檔案
                    advice_path = output_dir / f'investment_advice_comprehensive_{ts}.md'
                    with open(advice_path, 'w', encoding='utf-8') as f:
                        f.write(md_content)
                    self._log(f"💾 綜合投資建議總結已保存: {advice_path.name}", "info", force_print=True)
            else:
                self._log("⚠️  無多策略交易資料，跳過停損停利分析", "info")

            # 6. 生成圖表（與選項aa相同）
            if not trades_df.empty:
                try:
                    # 計算績效指標（用於圖表生成）
                    metrics = self._calculate_chart_metrics(trades_df, portfolio_metrics)

                    # 創建圖表目錄
                    chart_generator = BacktestCharts(output_dir=str(output_dir / "charts"))
                    charts = chart_generator.create_holdout_charts(trades_df, metrics)

                    # 更新JSON結果以包含圖表和停損停利分析資訊
                    results_json['charts'] = charts

                    # 如果有多策略停損停利分析結果，使用最佳策略的結果
                    if strategy_trades is not None and all_stop_analysis:
                        best_strategy = self._find_best_strategy_for_advice(all_stop_analysis)
                        if best_strategy and best_strategy in all_stop_analysis:
                            best_stop_analysis = all_stop_analysis[best_strategy]
                            results_json['stop_loss_analysis'] = {
                                'best_strategy': best_strategy,
                                'best_stop_loss': best_stop_analysis.get('best_combination', {}).get('stop_loss'),
                                'best_take_profit': best_stop_analysis.get('best_combination', {}).get('take_profit'),
                                'best_score': best_stop_analysis.get('best_combination', {}).get('score'),
                                'performance_improvement': self._calculate_improvement_summary(best_stop_analysis, trades_df),
                                'all_strategies': {k: v.get('best_combination', {}) for k, v in all_stop_analysis.items()}
                            }
                        else:
                            results_json['stop_loss_analysis'] = {'status': 'no_valid_analysis'}
                    else:
                        results_json['stop_loss_analysis'] = {'status': 'analysis_skipped'}

                    # 重新保存包含完整資訊的JSON
                    json_path = output_dir / f'holdout_{ts}.json'
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(results_json, f, ensure_ascii=False, indent=2)

                    self._log(f"📊 回測圖表已生成: {len(charts)} 個圖表", "info", force_print=True)
                except Exception as e:
                    self._log(f"⚠️  圖表生成失敗: {e}", "warning", force_print=True)

            self._log(f"📁 所有最終結果已保存至與每月報告相同的目錄", "info", force_print=True)
            self._log(f"📂 完整路徑: {output_dir}", "info", force_print=True)
        except Exception as e:
            self._log(f"保存結果失敗: {e}", "warning", force_print=True)

    def _save_multi_strategy_excel(self, strategy_monthlies: Dict[str, List[Dict[str, Any]]], strategy_trades: Dict[str, pd.DataFrame], session_id: str, output_dir: Path):
        """將 Original/A/B/C 四種策略同時輸出到兩個Excel: holdout_monthly.xlsx 與 holdout_trades.xlsx"""
        self._log("🔍 DEBUG: 進入 _save_multi_strategy_excel 函式", "info", force_print=True)
        try:
            import pandas as pd
            self._log("🔍 DEBUG: pandas 匯入成功", "info", force_print=True)

            # 構造月報 DataFrame
            monthly_dfs: Dict[str, pd.DataFrame] = {}
            for key, monthlies in strategy_monthlies.items():
                rows = []
                for r in monthlies:
                    rows.append({
                        '月份': r.get('month'),
                        '市場濾網觸發': r.get('market_filter_triggered', False),
                        '入選股票數': len(r.get('selected_stocks', [])),
                        '入選股票': ', '.join(r.get('selected_stocks', [])[:5]) + ('...' if len(r.get('selected_stocks', [])) > 5 else ''),
                        '投資金額': r.get('investment_amount', 0),
                        '月底價值': r.get('month_end_value', 0),
                        '月報酬率': r.get('return_rate', 0),
                        '交易筆數': len(r.get('trades', []))
                    })
                monthly_dfs[key] = pd.DataFrame(rows) if rows else pd.DataFrame()

            # Excel 引擎選擇
            writer_engine = None
            try:
                import xlsxwriter  # noqa: F401
                writer_engine = 'xlsxwriter'
            except Exception:
                try:
                    import openpyxl  # noqa: F401
                    writer_engine = 'openpyxl'
                except Exception:
                    writer_engine = None

            if writer_engine is None:
                self._log("🔍 DEBUG: 無法載入Excel引擎，已維持輸出CSV/JSON。若需Excel，請安裝 xlsxwriter 或 openpyxl。", "warning", force_print=True)
                return

            self._log(f"🔍 DEBUG: 使用Excel引擎: {writer_engine}", "info", force_print=True)

            # 輸出月報Excel（中文sheet名）
            monthly_xlsx = output_dir / f"holdout_monthly_{session_id}.xlsx"
            with pd.ExcelWriter(monthly_xlsx, engine=writer_engine) as writer:
                sheet_map = [('original', '原本'), ('A', '方案A'), ('B', '方案B'), ('C', '方案C')]
                for key, sheet_name in sheet_map:
                    df = monthly_dfs.get(key, pd.DataFrame())
                    df.to_excel(writer, index=False, sheet_name=sheet_name)

            # 輸出交易明細Excel（中文sheet名，中文欄位）
            trades_xlsx = output_dir / f"holdout_trades_{session_id}.xlsx"
            self._log(f"🔍 DEBUG: 準備輸出交易明細Excel: {trades_xlsx}", "info", force_print=True)
            with pd.ExcelWriter(trades_xlsx, engine=writer_engine) as writer:
                sheet_map = [('original', '原本'), ('A', '方案A'), ('B', '方案B'), ('C', '方案C')]
                for key, sheet_name in sheet_map:
                    self._log(f"🔍 DEBUG: 處理策略 {key} -> {sheet_name}", "info", force_print=True)
                    df = strategy_trades.get(key, pd.DataFrame())
                    self._log(f"🔍 DEBUG: 策略 {key} 交易記錄數: {len(df) if df is not None else 0}", "info", force_print=True)
                    if df is not None and not df.empty:
                        df = self._rename_trades_to_chinese(df)
                        # 確保列順序包含你關心的欄位（若存在則維持在前）
                        prefer = ['股票代號','進場日','出場日','毛報酬','淨報酬']
                        cols = [c for c in prefer if c in df.columns] + [c for c in df.columns if c not in prefer]
                        if cols:
                            df = df[cols]
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
                    self._log(f"🔍 DEBUG: 策略 {key} 寫入完成", "info", force_print=True)

            self._log(f"✅ 已輸出月報Excel: {monthly_xlsx.name}", "info", force_print=True)
            self._log(f"✅ 已輸出交易明細Excel: {trades_xlsx.name}", "info", force_print=True)

        except Exception as e:
            self._log(f"輸出Excel失敗: {e}", "warning", force_print=True)


    def _analyze_optimal_stop_levels(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """分析最佳停損停利點"""
        try:
            if trades_df.empty:
                return {}

            self._log("🎯 開始分析最佳停損停利點...", "info", force_print=True)

            # 停損停利候選點（百分比）
            stop_loss_candidates = [0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20]  # 2%-20%
            take_profit_candidates = [0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30]  # 5%-30%

            best_combination = None
            best_score = -float('inf')
            analysis_results = []

            # 測試所有停損停利組合

            total_combinations = len(stop_loss_candidates) * len(take_profit_candidates)
            current_combination = 0

            for stop_loss in stop_loss_candidates:
                for take_profit in take_profit_candidates:
                    current_combination += 1

                    # 計算該組合的績效
                    result = self._simulate_stop_levels(trades_df, stop_loss, take_profit)
                    result['stop_loss'] = stop_loss
                    result['take_profit'] = take_profit

                    # 計算綜合評分（考慮報酬率、勝率、最大回撤）
                    score = self._calculate_stop_score(result)
                    result['score'] = score

                    analysis_results.append(result)

                    if score > best_score:
                        best_score = score
                        best_combination = result.copy()

                    # 顯示進度
                    if current_combination % 10 == 0 or current_combination == total_combinations:
                        progress = (current_combination / total_combinations) * 100
                        self._log(f"   📊 分析進度: {current_combination}/{total_combinations} ({progress:.1f}%)", "info")

            # 整理分析結果
            analysis_summary = {
                'best_combination': best_combination,
                'all_results': sorted(analysis_results, key=lambda x: x['score'], reverse=True),
                'analysis_stats': {
                    'total_combinations_tested': len(analysis_results),
                    'best_score': best_score,
                    'original_performance': self._get_original_performance(trades_df)
                }
            }

            # 顯示最佳結果
            if best_combination:
                self._display_optimal_stop_results(best_combination, trades_df)

            return analysis_summary

        except Exception as e:
            self._log(f"⚠️  停損停利分析失敗: {e}", "warning", force_print=True)
            return {}

    def _simulate_stop_levels(self, trades_df: pd.DataFrame, stop_loss: float, take_profit: float) -> Dict[str, Any]:
        """模擬特定停損停利點的交易結果"""
        try:
            simulated_trades = []

            for _, trade in trades_df.iterrows():
                # 嘗試不同的欄位名稱（相容性處理）
                max_return = trade.get('max_return_20d', trade.get('max_return', 0))
                min_return = trade.get('min_return_20d', trade.get('min_return', 0))
                original_return = trade.get('actual_return', 0)

                # 判斷是否觸發停損停利
                if max_return >= take_profit:
                    # 觸發停利
                    simulated_return = take_profit
                    exit_reason = 'take_profit'
                elif min_return <= -stop_loss:
                    # 觸發停損
                    simulated_return = -stop_loss
                    exit_reason = 'stop_loss'
                else:
                    # 正常到期
                    simulated_return = original_return
                    exit_reason = 'normal'

                # 扣除交易成本（處理不同的資料格式）
                transaction_costs = trade.get('transaction_costs', {})
                if isinstance(transaction_costs, str):
                    # 如果是字串，嘗試解析（CSV讀取時可能變成字串）
                    try:
                        import ast
                        transaction_costs = ast.literal_eval(transaction_costs)
                    except:
                        transaction_costs = {}

                cost_rate = transaction_costs.get('total_cost_rate', 0.007) if isinstance(transaction_costs, dict) else 0.007
                net_return = simulated_return - cost_rate

                simulated_trades.append({
                    'stock_id': trade.get('stock_id', ''),
                    'entry_date': trade.get('entry_date', ''),
                    'original_return': original_return,
                    'simulated_return': net_return,
                    'exit_reason': exit_reason,
                    'max_return': max_return,
                    'min_return': min_return
                })

            # 計算績效指標
            simulated_df = pd.DataFrame(simulated_trades)

            if not simulated_df.empty:
                total_trades = len(simulated_df)
                winning_trades = len(simulated_df[simulated_df['simulated_return'] > 0])
                win_rate = winning_trades / total_trades if total_trades > 0 else 0

                avg_return = simulated_df['simulated_return'].mean()
                total_return = simulated_df['simulated_return'].sum()

                # 計算最大回撤
                cumulative_returns = (1 + simulated_df['simulated_return']).cumprod()
                running_max = cumulative_returns.expanding().max()
                drawdowns = (cumulative_returns - running_max) / running_max
                max_drawdown = abs(drawdowns.min()) if not drawdowns.empty else 0

                # 統計出場原因
                exit_reasons = simulated_df['exit_reason'].value_counts()

                return {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'win_rate': win_rate,
                    'avg_return': avg_return,
                    'total_return': total_return,
                    'max_drawdown': max_drawdown,
                    'exit_reasons': exit_reasons.to_dict(),
                    'simulated_trades': simulated_trades
                }
            else:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'win_rate': 0,
                    'avg_return': 0,
                    'total_return': 0,
                    'max_drawdown': 0,
                    'exit_reasons': {},
                    'simulated_trades': []
                }

        except Exception as e:
            self._log(f"⚠️  停損停利模擬失敗: {e}", "warning")
            return {}

    def _calculate_chart_metrics(self, trades_df: pd.DataFrame, portfolio_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """計算圖表生成所需的指標（與選項aa格式相容）"""
        try:
            # 基本統計
            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['actual_return_net'] > 0]) if 'actual_return_net' in trades_df.columns else 0
            win_rate = winning_trades / total_trades if total_trades > 0 else 0

            # 使用淨報酬計算平均報酬
            avg_return = trades_df['actual_return_net'].mean() if 'actual_return_net' in trades_df.columns else 0

            # 計算總損益（使用淨損益）
            total_profit_loss = trades_df['profit_loss_net'].sum() if 'profit_loss_net' in trades_df.columns else 0

            # 從portfolio_metrics獲取其他指標
            metrics = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': win_rate,
                'avg_return': avg_return,
                'total_profit_loss': total_profit_loss,
                'sharpe_ratio': portfolio_metrics.get('sharpe_ratio', 0),
                'max_drawdown': portfolio_metrics.get('max_drawdown', 0),
                'annualized_return': portfolio_metrics.get('annualized_return', 0),
                'annualized_volatility': portfolio_metrics.get('annualized_volatility', 0),
                'total_return': portfolio_metrics.get('total_return', 0)
            }

            return metrics

        except Exception as e:
            self._log(f"⚠️  計算圖表指標失敗: {e}", "warning")
            # 返回基本指標
            return {
                'total_trades': len(trades_df) if not trades_df.empty else 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_return': 0,
                'total_profit_loss': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'annualized_return': 0,
                'annualized_volatility': 0,
                'total_return': 0
            }

    def _calculate_stop_score(self, result: Dict[str, Any]) -> float:
        """計算停損停利組合的綜合評分"""
        try:
            # 權重設定
            return_weight = 0.4      # 平均報酬權重
            win_rate_weight = 0.3    # 勝率權重
            drawdown_weight = 0.3    # 最大回撤權重（負向）

            # 正規化指標
            avg_return = result.get('avg_return', 0)
            win_rate = result.get('win_rate', 0)
            max_drawdown = result.get('max_drawdown', 0)

            # 計算評分（0-100分）
            return_score = min(avg_return * 1000, 100)  # 平均報酬轉換為分數
            win_rate_score = win_rate * 100             # 勝率轉換為分數
            drawdown_score = max(0, 100 - max_drawdown * 1000)  # 回撤轉換為分數（越小越好）

            # 綜合評分
            total_score = (return_score * return_weight +
                          win_rate_score * win_rate_weight +
                          drawdown_score * drawdown_weight)

            return total_score

        except Exception:
            return 0

    def _get_original_performance(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """獲取原始（無停損停利）的績效"""
        try:
            if trades_df.empty:
                return {}

            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['actual_return'] > 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            avg_return = trades_df['actual_return'].mean()

            # 計算最大回撤
            cumulative_returns = (1 + trades_df['actual_return']).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = abs(drawdowns.min()) if not drawdowns.empty else 0

            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'avg_return': avg_return,
                'max_drawdown': max_drawdown
            }

        except Exception:
            return {}

    def _display_optimal_stop_results(self, best_result: Dict[str, Any], original_trades_df: pd.DataFrame):
        """顯示最佳停損停利分析結果"""
        try:
            self._log("🎯 最佳停損停利分析結果", "info", force_print=True)
            self._log("="*50, "info", force_print=True)

            # 最佳參數
            stop_loss = best_result.get('stop_loss', 0)
            take_profit = best_result.get('take_profit', 0)

            self._log(f"📊 最佳停損停利組合:", "info", force_print=True)
            self._log(f"   🔻 停損點: {stop_loss:.1%}", "info", force_print=True)
            self._log(f"   🔺 停利點: {take_profit:.1%}", "info", force_print=True)
            self._log(f"   ⭐ 綜合評分: {best_result.get('score', 0):.1f}/100", "info", force_print=True)

            # 績效比較
            original_perf = self._get_original_performance(original_trades_df)

            self._log(f"\n📈 績效比較:", "info", force_print=True)
            self._log(f"   項目           原始策略    最佳停損停利    改善幅度", "info", force_print=True)
            self._log(f"   ─────────────────────────────────────────────", "info", force_print=True)

            # 平均報酬
            orig_avg = original_perf.get('avg_return', 0)
            best_avg = best_result.get('avg_return', 0)
            avg_improve = ((best_avg - orig_avg) / abs(orig_avg) * 100) if orig_avg != 0 else 0
            self._log(f"   平均報酬       {orig_avg:>7.2%}      {best_avg:>7.2%}      {avg_improve:>+6.1f}%", "info", force_print=True)

            # 勝率
            orig_win = original_perf.get('win_rate', 0)
            best_win = best_result.get('win_rate', 0)
            win_improve = ((best_win - orig_win) / orig_win * 100) if orig_win != 0 else 0
            self._log(f"   勝率           {orig_win:>7.1%}      {best_win:>7.1%}      {win_improve:>+6.1f}%", "info", force_print=True)

            # 最大回撤
            orig_dd = original_perf.get('max_drawdown', 0)
            best_dd = best_result.get('max_drawdown', 0)
            dd_improve = ((orig_dd - best_dd) / orig_dd * 100) if orig_dd != 0 else 0
            self._log(f"   最大回撤       {orig_dd:>7.1%}      {best_dd:>7.1%}      {dd_improve:>+6.1f}%", "info", force_print=True)

            # 出場原因統計
            exit_reasons = best_result.get('exit_reasons', {})
            total_trades = best_result.get('total_trades', 0)

            self._log(f"\n🚪 出場原因統計:", "info", force_print=True)
            if 'take_profit' in exit_reasons:
                tp_pct = exit_reasons['take_profit'] / total_trades * 100
                self._log(f"   🔺 停利出場: {exit_reasons['take_profit']} 筆 ({tp_pct:.1f}%)", "info", force_print=True)
            if 'stop_loss' in exit_reasons:
                sl_pct = exit_reasons['stop_loss'] / total_trades * 100
                self._log(f"   🔻 停損出場: {exit_reasons['stop_loss']} 筆 ({sl_pct:.1f}%)", "info", force_print=True)
            if 'normal' in exit_reasons:
                normal_pct = exit_reasons['normal'] / total_trades * 100
                self._log(f"   ⏰ 正常到期: {exit_reasons['normal']} 筆 ({normal_pct:.1f}%)", "info", force_print=True)

            self._log("="*50, "info", force_print=True)

        except Exception as e:
            self._log(f"⚠️  顯示停損停利結果失敗: {e}", "warning")

    def _calculate_improvement_summary(self, stop_analysis: Dict[str, Any], original_trades_df: pd.DataFrame) -> Dict[str, Any]:
        """計算停損停利改善摘要"""
        try:
            if not stop_analysis or original_trades_df.empty:
                return {}

            best_combination = stop_analysis.get('best_combination', {})
            original_perf = self._get_original_performance(original_trades_df)

            if not best_combination or not original_perf:
                return {}

            # 計算改善幅度
            orig_avg = original_perf.get('avg_return', 0)
            best_avg = best_combination.get('avg_return', 0)
            avg_improvement = ((best_avg - orig_avg) / abs(orig_avg) * 100) if orig_avg != 0 else 0

            orig_win = original_perf.get('win_rate', 0)
            best_win = best_combination.get('win_rate', 0)
            win_improvement = ((best_win - orig_win) / orig_win * 100) if orig_win != 0 else 0

            orig_dd = original_perf.get('max_drawdown', 0)
            best_dd = best_combination.get('max_drawdown', 0)
            dd_improvement = ((orig_dd - best_dd) / orig_dd * 100) if orig_dd != 0 else 0

            return {
                'avg_return_improvement': avg_improvement,
                'win_rate_improvement': win_improvement,
                'max_drawdown_improvement': dd_improvement,
                'original_avg_return': orig_avg,
                'optimal_avg_return': best_avg,
                'original_win_rate': orig_win,
                'optimal_win_rate': best_win,
                'original_max_drawdown': orig_dd,
                'optimal_max_drawdown': best_dd
            }

        except Exception:
            return {}

    def _generate_investment_advice(self, stop_analysis: Dict[str, Any], trades_df: pd.DataFrame, portfolio_metrics: Dict[str, Any], strategy_name: str = 'original') -> str:
        """生成投資建議總結"""
        try:
            from datetime import datetime

            best_combination = stop_analysis.get('best_combination', {})
            original_perf = self._get_original_performance(trades_df)

            # 生成Markdown格式的投資建議
            strategy_names = {'original': '原本策略', 'A': '方案A策略', 'B': '方案B策略', 'C': '方案C策略'}
            strategy_display = strategy_names.get(strategy_name, f'{strategy_name}策略')

            advice = f"""# 投資建議總結 - {strategy_display}

## 📊 回測基本資訊
- **分析策略**: {strategy_display}
- **回測期間**: {trades_df['entry_date'].min() if not trades_df.empty else '未知'} ~ {trades_df['entry_date'].max() if not trades_df.empty else '未知'}
- **總交易數**: {len(trades_df)} 筆
- **分析時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 最佳停損停利建議

### 推薦參數
- **🔻 建議停損點**: {best_combination.get('stop_loss', 0):.1%}
- **🔺 建議停利點**: {best_combination.get('take_profit', 0):.1%}
- **⭐ 綜合評分**: {best_combination.get('score', 0):.1f}/100

### 績效比較
"""

            # 安全計算改善幅度
            def safe_improvement(new_val, old_val):
                if old_val == 0:
                    return "N/A" if new_val == 0 else "+∞"
                return f"{((new_val - old_val) / abs(old_val) * 100):+.1f}%"

            # 獲取績效數據
            orig_return = original_perf.get('avg_return', 0)
            opt_return = best_combination.get('metrics', {}).get('avg_return', 0)
            orig_win_rate = original_perf.get('win_rate', 0)
            opt_win_rate = best_combination.get('metrics', {}).get('win_rate', 0)
            orig_drawdown = original_perf.get('max_drawdown', 0)
            opt_drawdown = best_combination.get('metrics', {}).get('max_drawdown', 0)

            advice += f"""
| 指標 | 原始策略 | 最佳停損停利 | 改善幅度 |
|------|----------|-------------|----------|
| 平均報酬率 | {orig_return:.2%} | {opt_return:.2%} | {safe_improvement(opt_return, orig_return)} |
| 勝率 | {orig_win_rate:.1%} | {opt_win_rate:.1%} | {safe_improvement(opt_win_rate, orig_win_rate)} |
| 最大回撤 | {orig_drawdown:.1%} | {opt_drawdown:.1%} | {safe_improvement(-opt_drawdown, -orig_drawdown)} |

### 出場原因統計
"""

            # 出場原因統計
            exit_reasons = best_combination.get('metrics', {}).get('exit_reasons', {})
            total_trades = best_combination.get('metrics', {}).get('total_trades', 0)

            reason_names = {
                'take_profit': '🔺 停利出場',
                'stop_loss': '🔻 停損出場',
                'normal': '⏰ 正常到期'
            }

            for reason, count in exit_reasons.items():
                pct = count/total_trades*100 if total_trades > 0 else 0
                reason_name = reason_names.get(reason, reason)
                advice += f"- **{reason_name}**: {count} 筆 ({pct:.1f}%)\n"

            # 添加策略分析和建議
            advice += f"""

## 📈 策略分析

### {strategy_display} 特色
"""

            # 根據策略類型添加特定分析
            if strategy_name == 'original':
                advice += """
- **策略類型**: 基礎策略，無技術指標篩選
- **適用對象**: 保守型投資者，追求穩定收益
- **風險特徵**: 風險分散，但可能包含技術面較弱的股票
"""
            elif strategy_name == 'A':
                advice += """
- **策略類型**: 技術指標篩選策略A
- **篩選條件**: RSI、MACD、布林通道等技術指標
- **適用對象**: 積極型投資者，重視技術面分析
- **風險特徵**: 技術面較強，但交易機會可能較少
"""
            elif strategy_name == 'B':
                advice += """
- **策略類型**: 技術指標篩選策略B
- **篩選條件**: 不同的技術指標組合
- **適用對象**: 平衡型投資者
- **風險特徵**: 平衡風險與收益
"""
            elif strategy_name == 'C':
                advice += """
- **策略類型**: 嚴格篩選策略C
- **篩選條件**: 最嚴格的技術指標要求
- **適用對象**: 保守型投資者，追求高品質標的
- **風險特徵**: 交易機會少但品質較高
"""

            advice += f"""

### 投資建議
1. **停損停利設定**
   - 建議停損點: {best_combination.get('stop_loss', 0):.1%}
   - 建議停利點: {best_combination.get('take_profit', 0):.1%}
   - 嚴格執行紀律，避免情緒化決策

2. **風險管理**
   - 單筆投資不超過總資金的 {100/max(len(trades_df), 1):.1f}%
   - 建議分散投資，降低個股風險
   - 定期檢視持股，適時調整策略

3. **執行建議**
   - 使用限價單進場，避免追高
   - 設定停損停利自動執行
   - 保持投資紀律，不隨意更改參數

## 📊 風險提醒

⚠️ **重要提醒**:
- 本分析基於歷史數據，未來績效可能不同
- 市場環境變化可能影響策略效果
- 建議搭配基本面分析，提高投資勝率
- 投資有風險，請謹慎評估自身風險承受能力

## 📝 總結

基於回測分析，{strategy_display} 在設定適當的停損停利後，可以有效改善投資績效。建議投資者：

1. 採用建議的停損停利參數
2. 嚴格執行投資紀律
3. 定期檢視和調整策略
4. 保持理性投資心態

---
*本報告由台股投資系統自動生成，僅供參考，不構成投資建議*
"""

            # 風險評估
            max_drawdown_improvement = ((original_perf.get('max_drawdown', 0) - best_combination.get('max_drawdown', 0)) / original_perf.get('max_drawdown', 0.001) * 100)

            advice += f"""
## 💡 投資建議

### 風險控制效果
"""

            if max_drawdown_improvement > 20:
                advice += f"✅ **風險控制效果顯著**: 最大回撤改善 {max_drawdown_improvement:.1f}%，建議採用停損停利策略\n"
            elif max_drawdown_improvement > 0:
                advice += f"✅ **風險控制有效**: 最大回撤改善 {max_drawdown_improvement:.1f}%，可考慮採用\n"
            else:
                advice += f"⚠️ **風險控制效果有限**: 最大回撤改善 {max_drawdown_improvement:.1f}%，需謹慎評估\n"

            # 報酬率分析
            return_improvement = ((best_combination.get('avg_return', 0) - original_perf.get('avg_return', 0)) / abs(original_perf.get('avg_return', 0.001)) * 100)

            advice += f"""
### 報酬率影響
"""

            if return_improvement > 5:
                advice += f"✅ **報酬率提升**: 平均報酬改善 {return_improvement:.1f}%\n"
            elif return_improvement > -5:
                advice += f"✅ **報酬率影響輕微**: 平均報酬變化 {return_improvement:.1f}%，在可接受範圍\n"
            else:
                advice += f"⚠️ **報酬率下降**: 平均報酬下降 {abs(return_improvement):.1f}%，需權衡風險收益\n"

            # 實際應用建議
            advice += f"""
## 🚀 實際應用建議

### 1. 參數設定
- **建議停損停利參數**: {best_combination.get('stop_loss', 0.02):.1%} / {best_combination.get('take_profit', 0.1):.1%}

### 2. 驗證建議
為了驗證這些建議，建議您：
1. 使用建議的停損停利參數重新回測
2. 比較實際結果與預期結果
3. 根據驗證結果調整參數

---
*此建議基於 {datetime.now().strftime('%Y-%m-%d')} 的回測分析結果*
"""

            return advice

        except Exception as e:
            return f"# 投資建議總結\n\n❌ 生成投資建議失敗: {e}\n"

    def _save_custom_stop_loss_results(self, result: Dict[str, Any], holdout_start: str, holdout_end: str,
                                     min_predicted_return: float, top_k: int, use_market_filter: bool,
                                     monthly_investment: float, stop_loss: float, take_profit: float):
        """保存自定義停損停利回測結果"""
        try:
            from datetime import datetime
            import json
            import pandas as pd

            # 生成時間戳和資料夾名稱
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 生成參數化資料夾名稱（與選項5相同格式，但加上停損停利標識）
            start_ym = holdout_start[:7].replace('-', '')
            end_ym = holdout_end[:7].replace('-', '')
            threshold_str = f"{int(min_predicted_return * 100):03d}"
            filter_str = "MF" if use_market_filter else "NF"

            folder_name = f"holdout_{start_ym}_{end_ym}_{threshold_str}_k{top_k}_{filter_str}_SL{stop_loss:.0%}TP{take_profit:.0%}_{ts}"

            # 創建輸出目錄
            base_dir = Path(self.paths['holdout_results'])
            output_dir = base_dir / folder_name
            output_dir.mkdir(parents=True, exist_ok=True)

            # 1. 保存修改後的交易記錄CSV
            modified_trades = result.get('detailed_trades', [])
            if modified_trades:
                trades_df = pd.DataFrame(modified_trades)
                trades_csv_path = output_dir / f'holdout_trades_stop_loss_{ts}.csv'
                trades_df.to_csv(trades_csv_path, index=False, encoding='utf-8-sig')
                self._log(f"💾 停損停利交易記錄已保存: {trades_csv_path.name}", "info", force_print=True)

            # 2. 保存每月結果（使用修改後的資料）
            monthly_results = result.get('monthly_results', [])
            for monthly_result in monthly_results:
                month = monthly_result.get('month', '')
                if month:
                    # 獲取該月的交易記錄
                    month_trades = [t for t in modified_trades if t.get('entry_date', '').startswith(month)]

                    # 創建月度結果結構
                    monthly_data = {
                        'month': month,
                        'market_filter_triggered': False,  # 停損停利回測不使用市場濾網
                        'selected_stocks': list(set(t.get('stock_id', '') for t in month_trades)),
                        'investment_amount': monthly_result.get('investment_amount', 0),
                        'month_end_value': monthly_result.get('month_end_value', 0),
                        'return_rate': monthly_result.get('return_rate', 0),
                        'trades': month_trades
                    }

                    # 保存每月報告（包含20日最大最小報酬）
                    self._save_monthly_investment_result_immediately(monthly_data, ts, output_dir)

            # 3. 保存整體結果JSON
            results_json = {
                'parameters': {
                    'holdout_start': holdout_start,
                    'holdout_end': holdout_end,
                    'min_predicted_return': min_predicted_return,
                    'top_k': top_k,
                    'use_market_filter': use_market_filter,
                    'monthly_investment': monthly_investment,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                },
                'portfolio_metrics': result.get('portfolio_metrics', {}),
                'exit_statistics': result.get('exit_statistics', {}),
                'comparison_with_original': result.get('comparison_with_original', {}),
                'monthly_results_summary': [
                    {
                        'month': r.get('month'),
                        'investment_amount': r.get('investment_amount'),
                        'month_end_value': r.get('month_end_value'),
                        'return_rate': r.get('return_rate'),
                        'trades_count': r.get('trades_count')
                    } for r in monthly_results
                ]
            }

            json_path = output_dir / f'holdout_stop_loss_{ts}.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results_json, f, ensure_ascii=False, indent=2)
            self._log(f"💾 停損停利回測結果已保存: {json_path.name}", "info", force_print=True)

            # 4. 生成驗證摘要
            verification_summary = self._generate_verification_summary(result, stop_loss, take_profit)
            summary_path = output_dir / f'verification_summary_{ts}.md'
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(verification_summary)
            self._log(f"💾 驗證摘要已保存: {summary_path.name}", "info", force_print=True)

            self._log(f"📁 停損停利回測結果已保存至: {folder_name}", "info", force_print=True)
            self._log(f"📂 完整路徑: {output_dir}", "info", force_print=True)

        except Exception as e:
            self._log(f"⚠️  保存停損停利結果失敗: {e}", "warning", force_print=True)

    def _generate_verification_summary(self, result: Dict[str, Any], stop_loss: float, take_profit: float) -> str:
        """生成驗證摘要"""
        try:
            from datetime import datetime

            portfolio_metrics = result.get('portfolio_metrics', {})
            exit_statistics = result.get('exit_statistics', {})
            comparison = result.get('comparison_with_original', {})

            summary = f"""# 停損停利驗證摘要

## 🎯 驗證參數
- **停損點**: {stop_loss:.1%}
- **停利點**: {take_profit:.1%}
- **驗證時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 驗證結果

### 整體績效
- **總投入金額**: {portfolio_metrics.get('total_invested', 0):,.0f} 元
- **期末總價值**: {portfolio_metrics.get('final_value', 0):,.0f} 元
- **總報酬率**: {portfolio_metrics.get('total_return', 0):.2%}
- **年化報酬率**: {portfolio_metrics.get('annualized_return', 0):.2%}
- **最大回撤**: {portfolio_metrics.get('max_drawdown', 0):.2%}
- **夏普比率**: {portfolio_metrics.get('sharpe_ratio', 0):.2f}

### 出場原因統計
"""

            total_trades = sum(exit_statistics.values()) if exit_statistics else 0

            reason_names = {
                'take_profit': '🔺 停利出場',
                'stop_loss': '🔻 停損出場',
                'normal': '⏰ 正常到期'
            }

            for reason, count in exit_statistics.items():
                pct = count / total_trades * 100 if total_trades > 0 else 0
                reason_name = reason_names.get(reason, reason)
                summary += f"- **{reason_name}**: {count} 筆 ({pct:.1f}%)\n"

            summary += f"""
### 與原始策略比較
| 指標 | 原始策略 | 停損停利策略 | 改善幅度 |
|------|----------|-------------|----------|
| 總報酬率 | {comparison.get('original_return', 0):.2%} | {comparison.get('stop_loss_return', 0):.2%} | {((comparison.get('stop_loss_return', 0) - comparison.get('original_return', 0)) / abs(comparison.get('original_return', 0.001)) * 100):+.1f}% |
| 最大回撤 | {comparison.get('original_drawdown', 0):.2%} | {comparison.get('stop_loss_drawdown', 0):.2%} | {((comparison.get('original_drawdown', 0) - comparison.get('stop_loss_drawdown', 0)) / comparison.get('original_drawdown', 0.001) * 100):+.1f}% |

## 💡 驗證結論

### 停損停利效果
"""

            return_improvement = ((comparison.get('stop_loss_return', 0) - comparison.get('original_return', 0)) / abs(comparison.get('original_return', 0.001)) * 100)
            drawdown_improvement = ((comparison.get('original_drawdown', 0) - comparison.get('stop_loss_drawdown', 0)) / comparison.get('original_drawdown', 0.001) * 100)

            if drawdown_improvement > 20:
                summary += "✅ **風險控制效果顯著**: 最大回撤大幅改善，建議採用此停損停利設定\n"
            elif drawdown_improvement > 0:
                summary += "✅ **風險控制有效**: 最大回撤有所改善，可考慮採用\n"
            else:
                summary += "⚠️ **風險控制效果有限**: 最大回撤改善不明顯，需重新評估參數\n"

            if return_improvement > 5:
                summary += "✅ **報酬率提升**: 停損停利策略帶來額外報酬\n"
            elif return_improvement > -5:
                summary += "✅ **報酬率影響輕微**: 在可接受範圍內\n"
            else:
                summary += "⚠️ **報酬率下降**: 需權衡風險收益比\n"

            # 出場原因分析
            stop_loss_pct = exit_statistics.get('stop_loss', 0) / total_trades * 100 if total_trades > 0 else 0
            take_profit_pct = exit_statistics.get('take_profit', 0) / total_trades * 100 if total_trades > 0 else 0

            summary += f"""
### 市場環境分析
"""

            if stop_loss_pct > 30:
                summary += f"⚠️ **市場波動較大**: {stop_loss_pct:.1f}%的交易觸發停損，風險控制發揮重要作用\n"
            elif stop_loss_pct > 15:
                summary += f"📊 **市場波動適中**: {stop_loss_pct:.1f}%的交易觸發停損，停損機制有效\n"
            else:
                summary += f"✅ **市場相對穩定**: 僅{stop_loss_pct:.1f}%的交易觸發停損\n"

            if take_profit_pct > 25:
                summary += f"✅ **獲利機會充足**: {take_profit_pct:.1f}%的交易觸發停利\n"
            elif take_profit_pct > 10:
                summary += f"📊 **獲利機會適中**: {take_profit_pct:.1f}%的交易觸發停利\n"
            else:
                summary += f"⚠️ **獲利機會有限**: 僅{take_profit_pct:.1f}%的交易觸發停利，可考慮調整停利點\n"

            summary += f"""
## 🎯 驗證結論

此次驗證使用 {stop_loss:.1%} 停損 / {take_profit:.1%} 停利的參數設定：

- **風險控制**: {'有效' if drawdown_improvement > 0 else '有限'}
- **報酬影響**: {'正面' if return_improvement > 0 else '負面'}
- **建議採用**: {'是' if drawdown_improvement > 10 or return_improvement > 5 else '需進一步評估'}

---
*此驗證報告由系統自動生成於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

            return summary

        except Exception as e:
            return f"# 停損停利驗證摘要\n\n❌ 生成驗證摘要失敗: {e}\n"

    def run_monthly_investment_with_stop_loss(self, holdout_start: str, holdout_end: str,
                                            min_predicted_return: float, top_k: int,
                                            use_market_filter: bool, monthly_investment: float,
                                            stop_loss: float, take_profit: float) -> Dict[str, Any]:
        """執行帶有自定義停損停利的每月定期定額投資回測"""
        try:
            self._log("🎯 開始執行自定義停損停利回測...", "info", force_print=True)
            self._log(f"🔻 停損點: {stop_loss:.1%}", "info", force_print=True)
            self._log(f"🔺 停利點: {take_profit:.1%}", "info", force_print=True)

            # 載入候選池
            pool = self._load_candidate_pool(None)  # 使用None會自動載入最新的候選池檔案
            stocks = [s['stock_id'] for s in pool.get('candidate_pool', [])]
            if not stocks:
                return {'success': False, 'error': 'empty_candidate_pool'}

            # 設定期間
            start = holdout_start
            end = holdout_end

            self._log(f"📅 投資期間: {start} ~ {end}", "info", force_print=True)
            self._log(f"💰 每月投資金額: {monthly_investment:,.0f} 元", "info", force_print=True)

            # 創建股價預測器
            stock_predictors = self._create_stock_predictors(stocks)

            # 生成會話ID和輸出目錄
            from datetime import datetime
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 生成資料夾名稱
            start_ym = start[:7].replace('-', '')
            end_ym = end[:7].replace('-', '')
            threshold_str = f"{int(min_predicted_return * 100):03d}"
            filter_str = "MF" if use_market_filter else "NF"

            folder_name = f"holdout_{start_ym}_{end_ym}_{threshold_str}_k{top_k}_{filter_str}_SL{stop_loss:.0%}TP{take_profit:.0%}_{ts}"

            # 創建輸出目錄
            from pathlib import Path
            base_dir = Path(self.paths['holdout_results'])
            output_dir = base_dir / folder_name
            output_dir.mkdir(parents=True, exist_ok=True)

            # 執行帶停損停利的每月投資回測
            monthly_results = self._execute_monthly_investment_with_stop_loss(
                stock_predictors, start, end, min_predicted_return, top_k,
                use_market_filter, monthly_investment, stop_loss, take_profit, ts, output_dir
            )

            # 計算整體績效
            all_trades = []
            total_invested = 0
            total_value = 0

            for result in monthly_results:
                all_trades.extend(result.get('trades', []))
                total_invested += result.get('investment_amount', 0)
                total_value += result.get('month_end_value', 0)

            if total_invested > 0:
                total_return = (total_value - total_invested) / total_invested
            else:
                total_return = 0

            # 統計出場原因
            exit_statistics = {'take_profit': 0, 'stop_loss': 0, 'normal': 0}
            for trade in all_trades:
                reason = trade.get('exit_reason', 'normal')
                exit_statistics[reason] = exit_statistics.get(reason, 0) + 1

            # 計算其他指標
            portfolio_metrics = self._calculate_portfolio_metrics_from_trades(all_trades, monthly_investment)

            result = {
                'success': True,
                'portfolio_metrics': portfolio_metrics,
                'detailed_trades': all_trades,
                'monthly_results': monthly_results,
                'exit_statistics': exit_statistics,
                'stop_loss_settings': {
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                }
            }

            # 保存完整結果
            self._save_stop_loss_complete_results(result, output_dir, ts)

            self._log(f"✅ 停損停利回測完成", "info", force_print=True)
            self._log(f"📊 總報酬率: {total_return:.2%}", "info", force_print=True)
            self._log(f"📈 總交易數: {len(all_trades)}", "info", force_print=True)

            # 顯示出場統計
            total_trades = sum(exit_statistics.values())
            if total_trades > 0:
                self._log(f"🔺 停利出場: {exit_statistics.get('take_profit', 0)} 筆 ({exit_statistics.get('take_profit', 0)/total_trades:.1%})", "info", force_print=True)
                self._log(f"🔻 停損出場: {exit_statistics.get('stop_loss', 0)} 筆 ({exit_statistics.get('stop_loss', 0)/total_trades:.1%})", "info", force_print=True)
                self._log(f"⏰ 正常到期: {exit_statistics.get('normal', 0)} 筆 ({exit_statistics.get('normal', 0)/total_trades:.1%})", "info", force_print=True)

            return result

        except Exception as e:
            self._log(f"❌ 自定義停損停利回測失敗: {e}", "error", force_print=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _execute_monthly_investment_with_stop_loss(self, stock_predictors: Dict, start_date: str, end_date: str,
                                                 threshold: float, top_k: int, use_market_filter: bool,
                                                 monthly_investment: float, stop_loss: float, take_profit: float,
                                                 session_id: str, output_dir) -> List[Dict[str, Any]]:
        """執行帶停損停利的每月定期定額投資回測核心邏輯"""

        import pandas as pd
        from datetime import datetime, timedelta

        monthly_results = []

        # 生成月份列表
        months = pd.date_range(start=start_date, end=end_date, freq='M')
        total_months = len(months)

        self._log(f"📊 總投資月數: {total_months} 個月", "info", force_print=True)

        for i, month_end in enumerate(months, 1):
            month_str = month_end.strftime('%Y-%m')
            self._log(f"📅 處理 {month_str} ({i}/{total_months})", "info", force_print=True)

            # 檢查市場濾網
            market_filter_triggered = False
            if use_market_filter:
                market_filter_triggered = self._check_market_filter(month_end.strftime('%Y-%m-%d'))
                if market_filter_triggered:
                    self._log(f"🚫 {month_str}: 市場濾網觸發，暫停投資", "info", force_print=True)
                    monthly_results.append({
                        'month': month_str,
                        'market_filter_triggered': True,
                        'selected_stocks': [],
                        'investment_amount': 0,
                        'month_end_value': 0,
                        'return_rate': 0,
                        'trades': []
                    })
                    continue

            # 獲取當月預測結果
            month_predictions = self._get_monthly_predictions(stock_predictors, month_str, threshold)

            if not month_predictions:
                self._log(f"⚠️  {month_str}: 無符合條件股票", "info", force_print=True)
                monthly_results.append({
                    'month': month_str,
                    'market_filter_triggered': False,
                    'selected_stocks': [],
                    'investment_amount': 0,
                    'month_end_value': 0,
                    'return_rate': 0,
                    'trades': []
                })
                continue

            # 選擇前K檔股票
            selected_stocks = month_predictions[:top_k]
            selected_stock_ids = [s['stock_id'] for s in selected_stocks]

            self._log(f"📈 {month_str}: 入選 {len(selected_stocks)} 檔股票: {', '.join(selected_stock_ids)}", "info", force_print=True)

            # 執行帶停損停利的交易
            trades = self._execute_stop_loss_trades(
                selected_stocks, month_str, monthly_investment, stop_loss, take_profit
            )

            # 計算月底價值
            total_value = sum(trade.get('final_value', 0) for trade in trades)
            return_rate = (total_value - monthly_investment) / monthly_investment if monthly_investment > 0 else 0

            monthly_result = {
                'month': month_str,
                'market_filter_triggered': False,
                'selected_stocks': selected_stock_ids,
                'investment_amount': monthly_investment,
                'month_end_value': total_value,
                'return_rate': return_rate,
                'trades': trades
            }

            monthly_results.append(monthly_result)

            # 立即保存當月結果
            self._save_monthly_investment_result_immediately(monthly_result, session_id, output_dir)

            self._log(f"💰 {month_str}: 投資 {monthly_investment:,.0f} → {total_value:,.0f} ({return_rate:+.2%})", "info", force_print=True)

        return monthly_results

    def _get_monthly_predictions(self, stock_predictors: Dict, month_str: str, threshold: float) -> List[Dict]:
        """獲取當月的股票預測結果"""
        try:
            # 計算預測日期（月底最後一天）
            from calendar import monthrange
            year, month = map(int, month_str.split('-'))
            last_day = monthrange(year, month)[1]
            as_of = f"{month_str}-{last_day:02d}"

            predictions = []
            stock_list = list(stock_predictors.keys())

            for stock_idx, stock_id in enumerate(stock_list, 1):
                # 顯示與選單5一致的個股處理進度條（在精簡模式也顯示）
                stock_progress = self._create_progress_bar(stock_idx, len(stock_list), width=10)
                self._log(f"   進度 [{stock_idx:2d}/{len(stock_list)}] {stock_progress} 訓練 {stock_id}", "info", force_print=True)
                try:
                    # 訓練模型（使用截至當月的資料）
                    features_df, targets_df = self.fe.generate_training_dataset(
                        stock_ids=[stock_id],
                        start_date='2015-01-01',
                        end_date=as_of
                    )

                    if features_df.empty:
                        continue

                    # 訓練模型
                    train_result = stock_predictors[stock_id].train(
                        feature_df=features_df,
                        target_df=targets_df
                    )

                    if not train_result['success']:
                        continue

                    # 預測
                    pred_result = stock_predictors[stock_id].predict(stock_id, as_of)
                    if pred_result['success']:
                        predictions.append({
                            'stock_id': stock_id,
                            'predicted_return': float(pred_result['predicted_return']),
                            'model_type': getattr(stock_predictors[stock_id], 'model_type', 'unknown')
                        })

                except Exception as e:
                    self._log(f"預測失敗 {stock_id}: {e}", "warning")
                    continue

            # 篩選股票
            filtered_predictions = self._filter_predictions(predictions, threshold, 999)  # 不限制數量，由後續top_k處理
            return filtered_predictions

        except Exception as e:
            self._log(f"獲取月度預測失敗 {month_str}: {e}", "error")
            return []

    def _execute_stop_loss_trades(self, selected_stocks: List[Dict], month_str: str,
                                 monthly_investment: float, stop_loss: float, take_profit: float) -> List[Dict]:
        """執行帶停損停利的交易"""

        trades = []
        investment_per_stock = monthly_investment / len(selected_stocks)

        for stock_info in selected_stocks:
            stock_id = stock_info['stock_id']
            predicted_return = stock_info['predicted_return']

            # 計算進場日期（月底最後一個交易日）→ 遇假日往後回補
            base_entry_date = self._get_last_trading_day_of_month(month_str)
            if not base_entry_date:
                continue

            entry_date, entry_price = self._find_next_trading_day_with_price(stock_id, base_entry_date, max_forward_days=7)
            if entry_price is None or entry_price <= 0:
                continue

            # 股價過高直接跳過（以設定為準）
            price_limit = self.backtest_cfg.get('entry_strategies', {}).get('price_upper_limit', 500)
            if entry_price > price_limit:
                self._log(f"{month_str} {stock_id} 進場價 {entry_price:.2f} > {price_limit}，跳過", "info")
                continue

            # 計算股數（使用與選單5相同的方式：扣除交易成本後，以1000股為單位）
            shares = self._calculate_shares_after_costs(investment_per_stock, entry_price)
            actual_investment = shares * entry_price

            if shares == 0:
                continue

            # 執行停損停利邏輯
            trade_result = self._simulate_stop_loss_trade(
                stock_id, entry_date, entry_price, shares, actual_investment,
                stop_loss, take_profit, predicted_return
            )

            if trade_result:
                trades.append(trade_result)

        return trades

    def _simulate_stop_loss_trade(self, stock_id: str, entry_date: str, entry_price: float,
                                shares: int, investment_amount: float, stop_loss: float,
                                take_profit: float, predicted_return: float) -> Dict:
        """模擬單筆停損停利交易"""

        from datetime import datetime, timedelta
        import pandas as pd

        # 計算交易成本（注意：需要出場價格，這裡先用進場價格估算）
        # 實際的交易成本會在確定出場價格後重新計算
        estimated_exit_price = entry_price * (1 + predicted_return)
        transaction_costs = self._calculate_transaction_costs(entry_price, estimated_exit_price, shares)

        # 獲取20個交易日的價格資料
        entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
        end_date = entry_dt + timedelta(days=30)  # 最多30天找20個交易日

        # 獲取價格序列
        price_data = self._get_price_series(stock_id, entry_date, end_date.strftime('%Y-%m-%d'))

        if not price_data or len(price_data) < 2:
            # 沒有價格資料，使用預測報酬
            exit_price = entry_price * (1 + predicted_return)

            # 重新計算正確的交易成本（使用實際出場價格）
            transaction_costs = self._calculate_transaction_costs(entry_price, exit_price, shares)

            gross_value = shares * exit_price
            final_value = gross_value - transaction_costs['total_cost_amount']

            # 選單5的計算方式（毛報酬，基於股價變化）
            gross_return = (exit_price - entry_price) / entry_price if entry_price > 0 else 0.0
            gross_profit_loss = (exit_price - entry_price) * shares

            # 選單5b的計算方式（淨報酬，扣除交易成本）
            net_profit_loss = final_value - investment_amount
            net_return = net_profit_loss / investment_amount if investment_amount > 0 else 0.0

            return {
                'stock_id': stock_id,
                'entry_date': entry_date,
                'entry_price': entry_price,
                'shares': shares,
                'investment_amount': investment_amount,
                'exit_date': entry_date,  # 同一天
                'exit_price': exit_price,
                'exit_reason': 'no_data',
                'holding_days': 0,
                'final_value': final_value,
                'month_end_value': final_value,
                'predicted_return': predicted_return,
                'transaction_costs': transaction_costs,
                'max_return_20d': predicted_return,
                'min_return_20d': predicted_return,

                # 選單5的計算結果（毛報酬，無交易成本）
                'actual_return_gross': gross_return,
                'profit_loss_gross': gross_profit_loss,

                # 選單5b的計算結果（淨報酬，含交易成本）
                'actual_return_net': net_return,
                'profit_loss_net': net_profit_loss,
                'actual_return': net_return,  # 主要報酬率使用淨報酬
                'profit_loss': net_profit_loss  # 主要損益使用淨損益
            }

        # 模擬每日價格變化
        max_return = 0
        min_return = 0
        exit_date = None
        exit_price = None
        exit_reason = 'normal'

        for i, (date, price) in enumerate(price_data[1:], 1):  # 跳過第一天（進場日）
            daily_return = (price - entry_price) / entry_price

            # 更新最大最小報酬
            max_return = max(max_return, daily_return)
            min_return = min(min_return, daily_return)

            # 檢查停利條件
            if daily_return >= take_profit:
                exit_date = date
                exit_price = price
                exit_reason = 'take_profit'
                break

            # 檢查停損條件
            if daily_return <= -stop_loss:
                exit_date = date
                exit_price = price
                exit_reason = 'stop_loss'
                break

            # 最多持有20個交易日
            if i >= 20:
                exit_date = date
                exit_price = price
                exit_reason = 'normal'
                break

        # 如果沒有觸發停損停利，使用最後一個價格
        if not exit_date:
            exit_date = price_data[-1][0]
            exit_price = price_data[-1][1]
            exit_reason = 'normal'

        # 計算最終結果
        holding_days = len([d for d, p in price_data if d <= exit_date]) - 1

        # 重新計算正確的交易成本（使用實際出場價格）
        transaction_costs = self._calculate_transaction_costs(entry_price, exit_price, shares)

        gross_value = shares * exit_price
        final_value = gross_value - transaction_costs['total_cost_amount']

        # 選單5的計算方式（毛報酬，基於股價變化）
        gross_return = (exit_price - entry_price) / entry_price if entry_price > 0 else 0.0
        gross_profit_loss = (exit_price - entry_price) * shares

        # 選單5b的計算方式（淨報酬，扣除交易成本）
        net_profit_loss = final_value - investment_amount
        net_return = net_profit_loss / investment_amount if investment_amount > 0 else 0.0

        return {
            'stock_id': stock_id,
            'entry_date': entry_date,
            'entry_price': entry_price,
            'shares': shares,
            'investment_amount': investment_amount,
            'exit_date': exit_date,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'holding_days': holding_days,
            'final_value': final_value,
            'month_end_value': final_value,
            'predicted_return': predicted_return,
            'transaction_costs': transaction_costs,
            'max_return_20d': max_return,
            'min_return_20d': min_return,

            # 選單5的計算結果（毛報酬，無交易成本）
            'actual_return_gross': gross_return,
            'profit_loss_gross': gross_profit_loss,

            # 選單5b的計算結果（淨報酬，含交易成本）
            'actual_return_net': net_return,
            'profit_loss_net': net_profit_loss,
            'actual_return': net_return,  # 主要報酬率使用淨報酬
            'profit_loss': net_profit_loss  # 主要損益使用淨損益
        }

    def _get_price_series(self, stock_id: str, start_date: str, end_date: str) -> List[tuple]:
        """獲取股票價格序列"""
        try:
            from stock_price_investment_system.data.data_manager import DataManager

            dm = DataManager()

            # 獲取價格資料
            price_df = dm.get_stock_prices(stock_id, start_date, end_date)

            if price_df is None or price_df.empty:
                return []

            # 確保有日期索引
            if 'date' in price_df.columns:
                price_df = price_df.set_index('date')

            # 使用收盤價
            if 'close' not in price_df.columns:
                return []

            # 轉換為 (日期, 價格) 的列表
            price_series = []
            for date, row in price_df.iterrows():
                if isinstance(date, str):
                    date_str = date
                else:
                    date_str = date.strftime('%Y-%m-%d')
                price_series.append((date_str, float(row['close'])))

            return sorted(price_series)  # 確保按日期排序

        except Exception as e:
            self._log(f"獲取 {stock_id} 價格序列失敗: {e}", "warning")
            return []

    def _get_last_trading_day_of_month(self, month_str: str) -> str:
        """獲取月底最後一個交易日（工作日近似）"""
        try:
            from datetime import datetime
            from calendar import monthrange

            year, month = map(int, month_str.split('-'))
            last_day = monthrange(year, month)[1]

            # 從月底往前找工作日（不保證開市）
            for day in range(last_day, 0, -1):
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                if date_obj.weekday() < 5:  # 0-4 是週一到週五
                    return date_str

            return f"{year:04d}-{month:02d}-{last_day:02d}"

        except Exception as e:
            self._log(f"獲取 {month_str} 最後交易日失敗: {e}", "warning")
            return None

    def _find_next_trading_day_with_price(self, stock_id: str, start_date: str, max_forward_days: int = 7):
        """從起始日期起，向後尋找下一個有成交價格的日期，回傳 (entry_date, price)。"""
        try:
            from datetime import datetime, timedelta
            date_obj = datetime.strptime(start_date, '%Y-%m-%d')

            # 往後最多 max_forward_days 天尋找可用價格
            for i in range(0, max_forward_days + 1):
                date_str = (date_obj + timedelta(days=i)).strftime('%Y-%m-%d')
                price = self._get_stock_price(stock_id, date_str)
                if price is not None and price > 0:
                    if i > 0:
                        self._log(f"{stock_id} 進場日回補: {start_date} → {date_str}", "info")
                    return date_str, price

            # 找不到可用價格
            return None, None
        except Exception as e:
            self._log(f"{stock_id} 回補進場日失敗: {e}", "warning")
            return None, None


    def _calculate_technical_indicators(self, stock_id: str, date: str, lookback_days: int = 60) -> dict:
        """計算技術指標"""
        try:
            from datetime import datetime, timedelta

            cfg = self.backtest_cfg.get('entry_strategies', {})
            rsi_period = cfg.get('rsi_period', 14)
            bb_period = cfg.get('bb_period', 20)
            bb_std = cfg.get('bb_std', 2)
            ma_fast = cfg.get('ma_fast', 20)
            ma_slow = cfg.get('ma_slow', 60)
            vol_ma = cfg.get('volume_ma', 20)

            # 計算起始日期（向前推lookback_days天）
            end_date_obj = datetime.strptime(date, '%Y-%m-%d')
            start_date_obj = end_date_obj - timedelta(days=lookback_days * 2)
            start_date = start_date_obj.strftime('%Y-%m-%d')

            # 取得價量資料
            df = self.dm.get_stock_prices(stock_id, start_date, date)
            if df is None or len(df) < max(ma_slow, bb_period, rsi_period, 30):
                return None

            # 確保資料按日期排序
            if 'date' in df.columns:
                df = df.sort_values('date')

            # 轉換為數值型態
            for col in ['close','high','low','open','volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(subset=['close','high','low','open','volume'])
            if len(df) < max(ma_slow, bb_period, rsi_period, 20):
                return None

            close = df['close']
            high = df['high']
            low = df['low']
            open_price = df['open']
            volume = df['volume']

            # 移動平均
            ma20 = close.rolling(window=ma_fast, min_periods=ma_fast).mean()
            ma60 = close.rolling(window=ma_slow, min_periods=ma_slow).mean()

            # RSI / BB / MACD
            rsi = self._calculate_rsi(close, period=rsi_period)
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close, period=bb_period, std_dev=bb_std)
            macd_line, signal_line, macd_histogram = self._calculate_macd(close)

            # 成交量均線
            volume_ma20 = volume.rolling(window=vol_ma, min_periods=vol_ma).mean()

            # 近期高點
            high_20d = high.rolling(window=20, min_periods=20).max()

            last_idx = -1
            indicators = {
                'price': float(close.iloc[last_idx]),
                'open': float(open_price.iloc[last_idx]),
                'high': float(high.iloc[last_idx]),
                'low': float(low.iloc[last_idx]),
                'volume': float(volume.iloc[last_idx]),
                'ma20': float(ma20.iloc[last_idx]) if not pd.isna(ma20.iloc[last_idx]) else None,
                'ma60': float(ma60.iloc[last_idx]) if not pd.isna(ma60.iloc[last_idx]) else None,
                'rsi': float(rsi.iloc[last_idx]) if not pd.isna(rsi.iloc[last_idx]) else None,
                'bb_upper': float(bb_upper.iloc[last_idx]) if not pd.isna(bb_upper.iloc[last_idx]) else None,
                'bb_middle': float(bb_middle.iloc[last_idx]) if not pd.isna(bb_middle.iloc[last_idx]) else None,
                'bb_lower': float(bb_lower.iloc[last_idx]) if not pd.isna(bb_lower.iloc[last_idx]) else None,
                'macd': float(macd_line.iloc[last_idx]) if not pd.isna(macd_line.iloc[last_idx]) else None,
                'signal': float(signal_line.iloc[last_idx]) if not pd.isna(signal_line.iloc[last_idx]) else None,
                'macd_histogram': float(macd_histogram.iloc[last_idx]) if not pd.isna(macd_histogram.iloc[last_idx]) else None,
                'volume_ma20': float(volume_ma20.iloc[last_idx]) if not pd.isna(volume_ma20.iloc[last_idx]) else None,
                'high_20d': float(high_20d.iloc[last_idx]) if not pd.isna(high_20d.iloc[last_idx]) else None,
                'prev_macd_histogram': float(macd_histogram.iloc[-2]) if len(macd_histogram) > 1 and not pd.isna(macd_histogram.iloc[-2]) else None
            }
            return indicators
        except Exception as e:
            self._log(f"計算技術指標失敗 {stock_id} {date}: {e}", "warning")
            return None

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        rs = gain / loss.replace(0, 1e-12)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_bollinger_bands(self, series: pd.Series, period: int = 20, std_dev: int = 2):
        ma = series.rolling(window=period, min_periods=period).mean()
        std = series.rolling(window=period, min_periods=period).std()
        upper = ma + std_dev * std
        lower = ma - std_dev * std
        return upper, ma, lower

    def _calculate_macd(self, series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        hist = macd - signal_line
        return macd, signal_line, hist

    def _check_entry_by_strategy(self, strategy: str, indicators: dict) -> (bool, str):
        """依策略檢查進場條件，返回(是否進場, 原因或通過)"""
        if strategy == 'original':
            return True, '原始策略'
        if not indicators:
            return False, '技術指標不足'

        price = indicators.get('price')
        ma20 = indicators.get('ma20')
        ma60 = indicators.get('ma60')
        rsi = indicators.get('rsi')
        vol = indicators.get('volume')
        vol_ma = indicators.get('volume_ma20')
        macd = indicators.get('macd')
        signal = indicators.get('signal')
        bb_lower = indicators.get('bb_lower')
        high_20d = indicators.get('high_20d')
        open_px = indicators.get('open')
        prev_hist = indicators.get('prev_macd_histogram')
        hist = indicators.get('macd_histogram')

        cfg = self.backtest_cfg.get('entry_strategies', {})
        if strategy == 'A':
            a = cfg.get('strategy_A', {})
            reasons = []
            conds = []
            # 趨勢+量能
            trend_up = (price is not None and ma20 is not None and ma60 is not None and price > ma20 and ma20 > ma60)
            volume_ok = (vol is not None and vol_ma is not None and vol > vol_ma) if a.get('volume_confirm', True) else True
            conds.append(trend_up and volume_ok)
            # 突破+RSI健康
            rsi_min, rsi_max = a.get('rsi_range', [30, 70])
            breakout = (high_20d is not None and price is not None and price > high_20d)
            rsi_ok = (rsi is not None and rsi_min < rsi < rsi_max)
            conds.append(breakout and rsi_ok)
            # MACD 金叉 + 多頭
            macd_ok = (macd is not None and signal is not None and macd > signal and macd > 0 and ma20 is not None and ma60 is not None and ma20 > ma60)
            conds.append(macd_ok)
            passed = any(conds)
            return passed, 'A條件通過' if passed else 'A條件不符'

        if strategy == 'B':
            b = cfg.get('strategy_B', {})
            # 基本趨勢必須
            if not (price is not None and ma20 is not None and ma60 is not None and price > ma20 and ma20 > ma60):
                return False, 'B基本趨勢不符'
            count = 0
            rsi_min, rsi_max = b.get('rsi_range', [30, 70])
            if rsi is not None and rsi_min < rsi < rsi_max:
                count += 1
            if vol is not None and vol_ma is not None and vol > vol_ma:
                count += 1
            if macd is not None and signal is not None and macd > signal:
                count += 1
            if high_20d is not None and price is not None and price > b.get('near_high_ratio', 0.98) * high_20d:
                count += 1
            need = b.get('need_at_least', 2)
            return (count >= need), ('B條件通過' if count >= need else 'B條件不足')

        if strategy == 'C':
            c = cfg.get('strategy_C', {})
            # RSI < 25
            if not (rsi is not None and rsi < c.get('rsi_below', 25)):
                return False, 'C RSI未達'
            # 安全區
            safe_ok = False
            if c.get('safe_zone', {}).get('use_bb_lower', True) and bb_lower is not None and price is not None and price > bb_lower:
                safe_ok = True
            if c.get('safe_zone', {}).get('use_ma20_ratio', True) and ma20 is not None and price is not None and price >= c.get('safe_zone', {}).get('ma20_min_ratio', 0.95) * ma20:
                safe_ok = True or safe_ok
            if not safe_ok:
                return False, 'C 安全區不符'
            # 量能
            if not (vol is not None and vol_ma is not None and vol >= c.get('volume_boost_ratio', 1.05) * vol_ma):
                return False, 'C 量能不足'
            # 轉強跡象
            bullish = (open_px is not None and price is not None and price > open_px)
            macd_turn = (prev_hist is not None and hist is not None and prev_hist < 0 and hist >= 0)
            if not (bullish or macd_turn):
                return False, 'C 尚未轉強'
            return True, 'C條件通過'

        return True, '未指定策略或原始策略'

    def _calculate_portfolio_metrics_from_trades(self, trades: List[Dict], monthly_investment: float) -> Dict:
        """從交易記錄計算投資組合指標"""
        if not trades:
            return {}

        total_invested = sum(trade.get('investment_amount', 0) for trade in trades)
        total_value = sum(trade.get('final_value', 0) for trade in trades)

        if total_invested == 0:
            return {}

        total_return = (total_value - total_invested) / total_invested if total_invested > 0 else 0

        # 計算月度報酬率
        monthly_returns = []
        trades_by_month = {}

        for trade in trades:
            entry_date = trade.get('entry_date', '')
            if entry_date:
                month = entry_date[:7]  # YYYY-MM
                if month not in trades_by_month:
                    trades_by_month[month] = []
                trades_by_month[month].append(trade)

        for month, month_trades in trades_by_month.items():
            month_invested = sum(t.get('investment_amount', 0) for t in month_trades)
            month_value = sum(t.get('final_value', 0) for t in month_trades)
            if month_invested > 0:
                month_return = (month_value - month_invested) / month_invested
                monthly_returns.append(month_return)

        # 計算統計指標
        import numpy as np

        if monthly_returns:
            avg_monthly_return = np.mean(monthly_returns)
            monthly_volatility = np.std(monthly_returns) if len(monthly_returns) > 1 else 0

            # 年化指標
            annualized_return = (1 + avg_monthly_return) ** 12 - 1
            annualized_volatility = monthly_volatility * (12 ** 0.5)

            # 夏普比率（假設無風險利率為2%）
            risk_free_rate = 0.02
            if annualized_volatility > 0:
                sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
            else:
                sharpe_ratio = 0

            # 最大回撤
            cumulative_returns = np.cumprod([1 + r for r in monthly_returns])
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = np.where(running_max > 0, (cumulative_returns - running_max) / running_max, 0)
            max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0
        else:
            avg_monthly_return = 0
            monthly_volatility = 0
            annualized_return = 0
            annualized_volatility = 0
            sharpe_ratio = 0
            max_drawdown = 0

        # 勝率
        profitable_trades = sum(1 for t in trades if t.get('actual_return', 0) > 0)
        win_rate = profitable_trades / len(trades) if trades else 0

        return {
            'total_invested': total_invested,
            'final_value': total_value,
            'total_return': total_return,
            'total_profit_loss': total_value - total_invested,
            'avg_monthly_return': avg_monthly_return,
            'monthly_volatility': monthly_volatility,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(trades)
        }

    def _save_stop_loss_complete_results(self, result: Dict, output_dir, session_id: str):
        """保存完整的停損停利結果"""
        try:
            import json
            import csv

            # 保存交易記錄CSV（使用與選單5相同的格式和順序）
            trades = result.get('detailed_trades', [])
            if trades:
                trades_csv_path = output_dir / f'stop_loss_trades_{session_id}.csv'

                # 定義與選單5相同的中文欄位順序，新增欄位放在後面
                fieldnames = [
                    # 基本資訊 (與選單5相同)
                    '進場日', '股票代號', '模型', '預測報酬',
                    '進場價', '出場日', '出場價', '持有天數',

                    # 選單5的計算結果 (等權重，無交易成本)
                    '毛報酬', '毛損益', '20日最大報酬', '20日最小報酬',

                    # 選單5b的計算結果 (定期定額，含交易成本)
                    '股數', '投資金額', '月底價值',
                    '淨報酬', '淨損益', '交易成本',

                    # 停損停利專屬欄位
                    '出場原因', '成本影響'
                ]

                with open(trades_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                    writer.writeheader()

                    for trade in trades:
                        # 確保與選單5相同的計算方式
                        row = self._format_trade_for_csv(trade)
                        writer.writerow(row)

                self._log(f"💾 交易記錄已保存: {trades_csv_path.name}", "info", force_print=True)

            # 保存結果JSON
            json_path = output_dir / f'stop_loss_results_{session_id}.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            self._log(f"💾 結果JSON已保存: {json_path.name}", "info", force_print=True)

            # 生成摘要報告
            summary = self._generate_stop_loss_summary(result)
            summary_path = output_dir / f'stop_loss_summary_{session_id}.md'
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            self._log(f"💾 摘要報告已保存: {summary_path.name}", "info", force_print=True)

        except Exception as e:
            self._log(f"⚠️  保存結果失敗: {e}", "warning")

    def _format_trade_for_csv(self, trade: Dict) -> Dict:
        """格式化交易記錄為CSV格式，確保與選單5相同的計算方式"""
        try:
            # 基本資訊
            entry_price = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)
            shares = trade.get('shares', 1000)
            investment_amount = trade.get('investment_amount', shares * entry_price)

            # 選單5的計算方式（毛報酬，無交易成本）
            actual_return_gross = (exit_price - entry_price) / entry_price if entry_price > 0 else 0
            profit_loss_gross = (exit_price - entry_price) * shares

            # 選單5b的計算方式（淨報酬，含交易成本）
            transaction_costs = trade.get('transaction_costs', {})
            if isinstance(transaction_costs, dict) and 'total_cost_amount' in transaction_costs:
                # 重新計算淨報酬（確保一致性）
                gross_value = shares * exit_price
                final_value = gross_value - transaction_costs['total_cost_amount']
                profit_loss_net = final_value - investment_amount
                actual_return_net = profit_loss_net / investment_amount if investment_amount > 0 else 0
                month_end_value = final_value
                cost_impact = actual_return_gross - actual_return_net
            else:
                # 沒有交易成本資料時，使用原始值
                actual_return_net = trade.get('actual_return_net', trade.get('actual_return', 0))
                profit_loss_net = trade.get('profit_loss_net', trade.get('profit_loss', 0))
                month_end_value = trade.get('month_end_value', trade.get('final_value', shares * exit_price))
                cost_impact = 0

            return {
                # 基本資訊 (與選單5相同)
                '進場日': trade.get('entry_date', ''),
                '股票代號': trade.get('stock_id', ''),
                '模型': trade.get('model_type', ''),
                '預測報酬': f"{trade.get('predicted_return', 0):.4f}",
                '進場價': f"{entry_price:.2f}",
                '出場日': trade.get('exit_date', ''),
                '出場價': f"{exit_price:.2f}",
                '持有天數': trade.get('holding_days', ''),

                # 選單5的計算結果 (等權重，無交易成本)
                '毛報酬': f"{actual_return_gross:.4f}",
                '毛損益': f"{profit_loss_gross:.2f}",
                '20日最大報酬': f"{trade.get('max_return_20d', 0):.4f}",
                '20日最小報酬': f"{trade.get('min_return_20d', 0):.4f}",

                # 選單5b的計算結果 (定期定額，含交易成本)
                '股數': shares,
                '投資金額': f"{investment_amount:.2f}",
                '月底價值': f"{month_end_value:.2f}",
                '淨報酬': f"{actual_return_net:.4f}",
                '淨損益': f"{profit_loss_net:.2f}",
                '交易成本': str(transaction_costs) if transaction_costs else '',

                # 停損停利專屬欄位
                '出場原因': trade.get('exit_reason', 'normal'),
                '成本影響': f"{cost_impact:.4f}"
            }

        except Exception as e:
            self._log(f"⚠️  格式化交易記錄失敗: {e}", "warning")
            return trade

    def _generate_stop_loss_summary(self, result: Dict) -> str:
        """生成停損停利摘要報告"""
        try:
            from datetime import datetime

            portfolio_metrics = result.get('portfolio_metrics', {})
            exit_statistics = result.get('exit_statistics', {})
            stop_loss_settings = result.get('stop_loss_settings', {})

            summary = f"""# 停損停利投資回測報告

## 🎯 回測參數
- **停損點**: {stop_loss_settings.get('stop_loss', 0):.1%}
- **停利點**: {stop_loss_settings.get('take_profit', 0):.1%}
- **回測時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 投資績效

### 整體表現
- **總投入金額**: {portfolio_metrics.get('total_invested', 0):,.0f} 元
- **期末總價值**: {portfolio_metrics.get('final_value', 0):,.0f} 元
- **總報酬率**: {portfolio_metrics.get('total_return', 0):.2%}
- **總損益**: {portfolio_metrics.get('total_profit_loss', 0):+,.0f} 元

### 風險指標
- **年化報酬率**: {portfolio_metrics.get('annualized_return', 0):.2%}
- **年化波動率**: {portfolio_metrics.get('annualized_volatility', 0):.2%}
- **夏普比率**: {portfolio_metrics.get('sharpe_ratio', 0):.2f}
- **最大回撤**: {portfolio_metrics.get('max_drawdown', 0):.2%}
- **勝率**: {portfolio_metrics.get('win_rate', 0):.1%}

## 🎯 停損停利效果分析

### 出場方式統計
"""

            total_trades = sum(exit_statistics.values()) if exit_statistics else 0

            if total_trades > 0:
                take_profit_count = exit_statistics.get('take_profit', 0)
                stop_loss_count = exit_statistics.get('stop_loss', 0)
                normal_count = exit_statistics.get('normal', 0)

                take_profit_pct = take_profit_count / total_trades * 100
                stop_loss_pct = stop_loss_count / total_trades * 100
                normal_pct = normal_count / total_trades * 100

                summary += f"""
| 出場方式 | 交易筆數 | 佔比 |
|----------|----------|------|
| 🔺 停利出場 | {take_profit_count} | {take_profit_pct:.1f}% |
| 🔻 停損出場 | {stop_loss_count} | {stop_loss_pct:.1f}% |
| ⏰ 正常到期 | {normal_count} | {normal_pct:.1f}% |
| **總計** | **{total_trades}** | **100.0%** |

### 策略效果評估
"""

                if stop_loss_pct > 20:
                    summary += "⚠️ **風險控制重要**: 超過20%的交易觸發停損，顯示市場波動較大，停損機制發揮重要作用\n"
                elif stop_loss_pct > 10:
                    summary += "📊 **風險控制適中**: 約10-20%的交易觸發停損，停損機制有效\n"
                else:
                    summary += "✅ **市場相對穩定**: 少於10%的交易觸發停損\n"

                if take_profit_pct > 25:
                    summary += "🎯 **獲利機會充足**: 超過25%的交易觸發停利，策略捕捉到良好的獲利機會\n"
                elif take_profit_pct > 15:
                    summary += "📈 **獲利機會適中**: 約15-25%的交易觸發停利\n"
                else:
                    summary += "💡 **獲利機會有限**: 少於15%的交易觸發停利，可考慮調整停利點\n"

                summary += f"""
### 建議
"""

                if portfolio_metrics.get('total_return', 0) > 0.05:
                    summary += "✅ **策略表現良好**: 總報酬率超過5%，停損停利設定合適\n"
                elif portfolio_metrics.get('total_return', 0) > 0:
                    summary += "📊 **策略表現中等**: 有正報酬但不高，可考慮調整參數\n"
                else:
                    summary += "⚠️ **策略需要調整**: 出現虧損，建議重新評估停損停利設定\n"

                if portfolio_metrics.get('max_drawdown', 0) < 0.1:
                    summary += "✅ **風險控制良好**: 最大回撤小於10%\n"
                elif portfolio_metrics.get('max_drawdown', 0) < 0.2:
                    summary += "📊 **風險控制適中**: 最大回撤在10-20%之間\n"
                else:
                    summary += "⚠️ **風險控制需加強**: 最大回撤超過20%，建議降低停損點\n"

            summary += f"""

## 📈 交易明細
總交易筆數: {portfolio_metrics.get('total_trades', 0)} 筆

---
*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

            return summary

        except Exception as e:
            return f"# 停損停利投資回測報告\n\n❌ 生成報告失敗: {e}\n"

    def _display_multi_strategy_stop_loss_results(self, all_stop_analysis):
        """顯示多策略停損停利分析結果比較，同時生成完整的 MD 檔案"""
        try:
            from datetime import datetime

            # 開始收集 MD 內容
            md_content = []

            # MD 檔案標題和基本資訊
            md_content.append("# 多策略停損停利分析綜合報告\n")
            md_content.append("## 📊 分析概要")
            md_content.append(f"- **分析時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            md_content.append(f"- **分析策略數**: {len(all_stop_analysis)} 個策略")
            md_content.append(f"- **分析方法**: 49種停損停利組合測試 (7×7)\n")

            # 策略說明
            md_content.append("## 📋 策略說明\n")
            md_content.append("### 原本策略 (Original)")
            md_content.append("- **策略類型**: 基礎策略，無技術指標篩選")
            md_content.append("- **選股條件**: 僅基於AI模型預測報酬率排序")
            md_content.append("- **適用對象**: 保守型投資者，追求穩定收益")
            md_content.append("- **風險特徵**: 風險分散，但可能包含技術面較弱的股票\n")

            md_content.append("### 方案A策略 (Strategy A)")
            md_content.append("- **策略類型**: 技術指標篩選策略A")
            md_content.append("- **選股條件**:")
            md_content.append("  - RSI(14) 介於 30-70 之間（避免超買超賣）")
            md_content.append("  - MACD 金叉且 MACD > 0")
            md_content.append("  - 股價位於布林通道中軌上方")
            md_content.append("  - 5日均線 > 20日均線（短期趨勢向上）")
            md_content.append("- **適用對象**: 積極型投資者，重視技術面分析")
            md_content.append("- **風險特徵**: 技術面較強，但交易機會可能較少\n")

            md_content.append("### 方案B策略 (Strategy B)")
            md_content.append("- **策略類型**: 技術指標篩選策略B")
            md_content.append("- **選股條件**:")
            md_content.append("  - KD指標 K值 > D值（動能向上）")
            md_content.append("  - 威廉指標 %R > -80（非超賣狀態）")
            md_content.append("  - 成交量 > 20日平均成交量 1.2倍（量能放大）")
            md_content.append("  - 股價突破前20日高點")
            md_content.append("- **適用對象**: 平衡型投資者")
            md_content.append("- **風險特徵**: 平衡風險與收益，注重量價配合\n")

            md_content.append("### 方案C策略 (Strategy C)")
            md_content.append("- **策略類型**: 嚴格篩選策略C")
            md_content.append("- **選股條件**:")
            md_content.append("  - 同時滿足方案A和方案B的所有條件")
            md_content.append("  - 額外要求：股價 > 60日均線（長期趨勢向上）")
            md_content.append("  - 近5日平均成交量 > 近20日平均成交量（持續量能）")
            md_content.append("- **適用對象**: 保守型投資者，追求高品質標的")
            md_content.append("- **風險特徵**: 交易機會少但品質較高，嚴格篩選\n")

            # 各策略詳細分析
            md_content.append("## 🎯 各策略停損停利分析結果\n")

            strategy_names = {'original': '原本', 'A': '方案A', 'B': '方案B', 'C': '方案C'}

            # 先收集所有策略的詳細分析，但不寫入 MD（因為會在 CLI 輸出時同步寫入）
            md_content.append("## 🎯 各策略停損停利分析結果\n")
            md_content.append("*詳細分析結果將在下方策略比較後顯示*\n")

            # CLI 輸出策略比較表格
            self._log("🎯 各策略最佳停損停利分析結果比較", "info", force_print=True)
            self._log("=" * 80, "info", force_print=True)
            self._log("策略     停損點  停利點  綜合評分  平均報酬  勝率    最大回撤  交易筆數", "info", force_print=True)
            self._log("─" * 80, "info", force_print=True)

            # MD 策略比較表格
            md_content.append("## 📊 策略比較總覽\n")
            md_content.append("| 策略 | 停損點 | 停利點 | 綜合評分 | 平均報酬 | 勝率 | 最大回撤 | 交易筆數 |")
            md_content.append("|------|--------|--------|----------|----------|------|----------|----------|")

            best_score = 0
            best_strategy = None

            for strategy, analysis in all_stop_analysis.items():
                best = analysis.get('best_combination', {})

                strategy_name = strategy_names.get(strategy, strategy)
                stop_loss = best.get('stop_loss', 0) * 100
                take_profit = best.get('take_profit', 0) * 100
                score = best.get('score', 0)
                avg_return = best.get('avg_return', 0) * 100
                win_rate = best.get('win_rate', 0) * 100
                max_drawdown = best.get('max_drawdown', 0) * 100
                total_trades = best.get('total_trades', 0)

                # CLI 輸出
                self._log(f"{strategy_name:<8} {stop_loss:4.1f}%   {take_profit:4.1f}%   {score:6.1f}    {avg_return:6.2f}%  {win_rate:4.1f}%   {max_drawdown:6.2f}%   {total_trades:4d}", "info", force_print=True)

                # MD 輸出
                md_content.append(f"| {strategy_name} | {stop_loss:.1f}% | {take_profit:.1f}% | {score:.1f} | {avg_return:.2f}% | {win_rate:.1f}% | {max_drawdown:.1f}% | {total_trades} |")

                if score > best_score:
                    best_score = score
                    best_strategy = strategy

            self._log("=" * 80, "info", force_print=True)

            if best_strategy:
                strategy_name = strategy_names.get(best_strategy, best_strategy)
                self._log(f"🏆 綜合表現最佳策略: {strategy_name} (評分: {best_score:.1f})", "info", force_print=True)
                self._log("", "info", force_print=True)

                # 顯示最佳策略的詳細結果，同時寫入 MD
                self._log(f"📊 {strategy_name} 策略詳細分析:", "info", force_print=True)

                # 為最佳策略生成詳細分析的 MD 內容
                best_analysis = all_stop_analysis[best_strategy]
                best_detail_md = self._generate_strategy_detail_md(best_analysis, strategy_name)
                md_content.append(f"\n## 🏆 最佳策略詳細分析: {strategy_name} (評分: {best_score:.1f})\n")
                md_content.append(best_detail_md)

                # CLI 輸出詳細結果
                self._display_stop_loss_results(best_analysis)

                # MD 投資建議
                best_analysis = all_stop_analysis[best_strategy]
                best_combo = best_analysis.get('best_combination', {})

                md_content.append("### 推薦參數")
                md_content.append(f"- **🔻 建議停損點**: {best_combo.get('stop_loss', 0):.1%}")
                md_content.append(f"- **🔺 建議停利點**: {best_combo.get('take_profit', 0):.1%}")
                md_content.append(f"- **⭐ 綜合評分**: {best_combo.get('score', 0):.1f}/100\n")

                md_content.append("### 投資建議")
                md_content.append("1. **停損停利設定**")
                md_content.append(f"   - 嚴格執行 {best_combo.get('stop_loss', 0):.1%} 停損")
                md_content.append(f"   - 達到 {best_combo.get('take_profit', 0):.1%} 停利時獲利了結")
                md_content.append("   - 避免情緒化決策，堅持紀律\n")

                md_content.append("2. **風險管理**")
                md_content.append("   - 分散投資，單一標的不超過總資金 20%")
                md_content.append("   - 定期檢視持股，適時調整策略")
                md_content.append("   - 保持適當的現金部位\n")

                md_content.append("3. **執行要點**")
                md_content.append("   - 使用限價單進場，避免追高殺低")
                md_content.append("   - 設定停損停利自動執行")
                md_content.append("   - 定期回顧和優化參數\n")

            # 風險提醒
            md_content.append("## ⚠️ 風險提醒\n")
            md_content.append("- 本分析基於歷史數據，未來績效可能不同")
            md_content.append("- 市場環境變化可能影響策略效果")
            md_content.append("- 建議搭配基本面分析，提高投資勝率")
            md_content.append("- 投資有風險，請謹慎評估自身風險承受能力\n")
            md_content.append("---")
            md_content.append("*本報告由台股投資系統自動生成，僅供參考，不構成投資建議*")

            # 保存 MD 檔案
            return '\n'.join(md_content)

        except Exception as e:
            self._log(f"⚠️  顯示多策略停損停利結果時發生錯誤: {e}", "warning", force_print=True)
            return f"# 多策略停損停利分析綜合報告\n\n❌ 生成報告失敗: {e}\n"

    def _display_stop_loss_results(self, stop_analysis):
        """顯示停損停利分析結果"""
        try:
            best = stop_analysis.get('best_combination', {})
            if not best:
                return

            self._log("🎯 最佳停損停利分析結果", "info", force_print=True)
            self._log("=" * 50, "info", force_print=True)
            self._log("📊 最佳停損停利組合:", "info", force_print=True)
            self._log(f"    🔻 停損點: {best.get('stop_loss', 0)*100:.1f}%", "info", force_print=True)
            self._log(f"    🔺 停利點: {best.get('take_profit', 0)*100:.1f}%", "info", force_print=True)
            self._log(f"    ⭐ 綜合評分: {best.get('score', 0):.1f}/100", "info", force_print=True)
            self._log("", "info", force_print=True)

            # 績效比較（數據直接從 best 和 original_metrics 讀取）
            original_metrics = stop_analysis.get('original_metrics', {})
            # optimized_metrics 直接使用 best，不使用 best.get('metrics', {})

            self._log("📈 績效比較:", "info", force_print=True)
            self._log("    項目           原始策略    最佳停損停利    改善幅度", "info", force_print=True)
            self._log("    " + "─" * 45, "info", force_print=True)

            # 平均報酬（數據直接從 best 讀取）
            orig_return = original_metrics.get('avg_return', 0) * 100
            opt_return = best.get('avg_return', 0) * 100  # 直接從 best 讀取
            improvement = ((opt_return - orig_return) / abs(orig_return) * 100) if orig_return != 0 else 0
            self._log(f"    平均報酬        {orig_return:6.2f}%       {opt_return:6.2f}%       {improvement:+5.1f}%", "info", force_print=True)

            # 勝率（數據直接從 best 讀取）
            orig_win_rate = original_metrics.get('win_rate', 0) * 100
            opt_win_rate = best.get('win_rate', 0) * 100  # 直接從 best 讀取
            win_improvement = opt_win_rate - orig_win_rate
            self._log(f"    勝率              {orig_win_rate:4.1f}%         {opt_win_rate:4.1f}%        {win_improvement:+4.1f}%", "info", force_print=True)

            # 最大回撤（數據直接從 best 讀取）
            orig_drawdown = original_metrics.get('max_drawdown', 0) * 100
            opt_drawdown = best.get('max_drawdown', 0) * 100  # 直接從 best 讀取
            drawdown_improvement = ((orig_drawdown - opt_drawdown) / orig_drawdown * 100) if orig_drawdown != 0 else 0
            self._log(f"    最大回撤          {orig_drawdown:4.1f}%         {opt_drawdown:4.1f}%       {drawdown_improvement:+5.1f}%", "info", force_print=True)

            self._log("", "info", force_print=True)

            # 出場原因統計（數據直接從 best 讀取）
            exit_reasons = best.get('exit_reasons', {})
            if exit_reasons:
                self._log("🚪 出場原因統計:", "info", force_print=True)
                total_trades = sum(exit_reasons.values())
                for reason, count in exit_reasons.items():
                    percentage = (count / total_trades * 100) if total_trades > 0 else 0
                    reason_emoji = {"stop_loss": "🔻", "take_profit": "🔺", "normal": "⏰"}.get(reason, "📊")
                    reason_name = {"stop_loss": "停損出場", "take_profit": "停利出場", "normal": "正常到期"}.get(reason, reason)
                    self._log(f"    {reason_emoji} {reason_name}: {count} 筆 ({percentage:.1f}%)", "info", force_print=True)

            self._log("=" * 50, "info", force_print=True)

        except Exception as e:
            self._log(f"⚠️  顯示停損停利結果時發生錯誤: {e}", "warning", force_print=True)

    def _find_best_strategy_for_advice(self, all_stop_analysis):
        """找出綜合表現最佳的策略"""
        best_score = 0
        best_strategy = None

        for strategy, analysis in all_stop_analysis.items():
            best = analysis.get('best_combination', {})
            score = best.get('score', 0)

            if score > best_score:
                best_score = score
                best_strategy = strategy

        return best_strategy

    def _generate_comprehensive_investment_advice(self, all_stop_analysis: Dict[str, Any], strategy_trades: Dict[str, pd.DataFrame], portfolio_metrics: Dict[str, Any]) -> str:
        """生成包含所有策略分析的綜合投資建議"""
        try:
            from datetime import datetime

            # 找出最佳策略
            best_strategy = self._find_best_strategy_for_advice(all_stop_analysis)
            strategy_names = {'original': '原本策略', 'A': '方案A策略', 'B': '方案B策略', 'C': '方案C策略'}

            advice = f"""# 多策略停損停利分析綜合報告

## 📊 分析概要
- **分析時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **分析策略數**: {len(all_stop_analysis)} 個策略
- **最佳策略**: {strategy_names.get(best_strategy, best_strategy)}
- **分析方法**: 49種停損停利組合測試 (7×7)

## 💰 投資回測結果摘要

### 基本資訊
- **📅 投資期間**: {portfolio_metrics.get('start_date', 'N/A')} ~ {portfolio_metrics.get('end_date', 'N/A')}
- **💰 每月投資金額**: {portfolio_metrics.get('monthly_investment', 1000000):,.0f} 元
- **📊 投資月數**: {portfolio_metrics.get('total_months', 0)} 個月

### 投資績效
- **💵 總投入金額**: {portfolio_metrics.get('total_invested', 0):,.0f} 元
- **💎 總資產價值**: {portfolio_metrics.get('total_current_value', 0):,.0f} 元
- **💰 總損益**: {portfolio_metrics.get('total_profit_loss', 0):+,.0f} 元
- **📊 總報酬率**: {portfolio_metrics.get('total_return', 0):.2%}

### 年化指標
- **📈 年化報酬率**: {portfolio_metrics.get('annualized_return', 0):.2%}
- **📊 年化波動率**: {portfolio_metrics.get('annualized_volatility', 0):.2%}
- **🎯 夏普比率**: {portfolio_metrics.get('sharpe_ratio', 0):.2f}
- **📉 最大回撤**: {portfolio_metrics.get('max_drawdown', 0):.2%}

### 勝率統計
- **📈 月度勝率**: {portfolio_metrics.get('monthly_win_rate', 0):.1%}
- **🎲 平均月報酬**: {portfolio_metrics.get('avg_monthly_return', 0):.2%}
- **📊 月報酬波動**: {portfolio_metrics.get('monthly_volatility', 0):.2%}

### 交易統計
- **📊 總交易次數**: {portfolio_metrics.get('total_trades', 0)} 筆
- **✅ 成功投資月數**: {portfolio_metrics.get('successful_months', 0)} 個月

### 📋 投資詳情
"""

            # 添加投資詳情（基於 Original 策略的交易記錄）
            if 'original' in strategy_trades:
                original_trades = strategy_trades['original']
                if not original_trades.empty:
                    # 按月份分組顯示投資詳情
                    original_trades['month'] = pd.to_datetime(original_trades['entry_date']).dt.strftime('%Y-%m')
                    monthly_summary = original_trades.groupby('month').agg({
                        'investment_amount': 'sum',
                        'month_end_value': 'sum',
                        'stock_id': lambda x: ', '.join(x.astype(str))
                    }).reset_index()

                    for _, row in monthly_summary.iterrows():
                        month = row['month']
                        investment = row['investment_amount']
                        value = row['month_end_value']
                        return_rate = (value - investment) / investment if investment > 0 else 0
                        stocks = row['stock_id']

                        advice += f"- **📅 {month}**: 投資 {investment:,.0f} 元 → {value:,.0f} 元 ({return_rate:+.2%})\n"
                        advice += f"  📈 投資股票: {stocks}\n"
                else:
                    advice += "- 本期間無投資記錄\n"
            else:
                advice += "- 無可用的投資記錄\n"

            advice += """

### 💡 交易成本說明
- **📊 已計入手續費、證交稅、滑價等所有交易成本**
- **💰 報酬率為扣除所有成本後的淨報酬**
- **🔄 每月平均分配資金到入選股票，持有20個交易日**

## 📋 策略說明

### 原本策略 (Original)
- **策略類型**: 基礎策略，無技術指標篩選
- **選股條件**: 僅基於AI模型預測報酬率排序
- **適用對象**: 保守型投資者，追求穩定收益
- **風險特徵**: 風險分散，但可能包含技術面較弱的股票

### 方案A策略 (Strategy A)
- **策略類型**: 技術指標篩選策略A
- **選股條件**:
  - RSI(14) 介於 30-70 之間（避免超買超賣）
  - MACD 金叉且 MACD > 0
  - 股價位於布林通道中軌上方
  - 5日均線 > 20日均線（短期趨勢向上）
- **適用對象**: 積極型投資者，重視技術面分析
- **風險特徵**: 技術面較強，但交易機會可能較少

### 方案B策略 (Strategy B)
- **策略類型**: 技術指標篩選策略B
- **選股條件**:
  - KD指標 K值 > D值（動能向上）
  - 威廉指標 %R > -80（非超賣狀態）
  - 成交量 > 20日平均成交量 1.2倍（量能放大）
  - 股價突破前20日高點
- **適用對象**: 平衡型投資者
- **風險特徵**: 平衡風險與收益，注重量價配合

### 方案C策略 (Strategy C)
- **策略類型**: 嚴格篩選策略C
- **選股條件**:
  - 同時滿足方案A和方案B的所有條件
  - 額外要求：股價 > 60日均線（長期趨勢向上）
  - 近5日平均成交量 > 近20日平均成交量（持續量能）
- **適用對象**: 保守型投資者，追求高品質標的
- **風險特徵**: 交易機會少但品質較高，嚴格篩選

## 🎯 各策略停損停利分析結果

"""

            # 為每個策略生成詳細分析
            for strategy_name in ['original', 'A', 'B', 'C']:
                if strategy_name in all_stop_analysis:
                    analysis = all_stop_analysis[strategy_name]
                    best = analysis.get('best_combination', {})
                    original_metrics = analysis.get('original_metrics', {})

                    strategy_display = strategy_names.get(strategy_name, strategy_name)

                    # 數據直接從 best 字典中讀取（不是從 metrics 子字典）
                    best_avg_return = best.get('avg_return', 0)
                    best_win_rate = best.get('win_rate', 0)
                    best_max_drawdown = best.get('max_drawdown', 0)

                    orig_avg_return = original_metrics.get('avg_return', 0)
                    orig_win_rate = original_metrics.get('win_rate', 0)
                    orig_max_drawdown = original_metrics.get('max_drawdown', 0)

                    advice += f"""### {strategy_display}

#### 🎯 最佳停損停利組合
- **🔻 停損點**: {best.get('stop_loss', 0):.1%}
- **🔺 停利點**: {best.get('take_profit', 0):.1%}
- **⭐ 綜合評分**: {best.get('score', 0):.1f}/100

#### 📈 績效比較
| 指標 | 原始策略 | 最佳停損停利 | 改善幅度 |
|------|----------|-------------|----------|
| 平均報酬率 | {orig_avg_return:.2%} | {best_avg_return:.2%} | {self._safe_improvement(best_avg_return, orig_avg_return)} |
| 勝率 | {orig_win_rate:.1%} | {best_win_rate:.1%} | {self._safe_improvement(best_win_rate, orig_win_rate)} |
| 最大回撤 | {orig_max_drawdown:.1%} | {best_max_drawdown:.1%} | {self._safe_improvement(-best_max_drawdown, -orig_max_drawdown)} |

#### 🚪 出場原因統計
"""

                    # 出場原因統計（數據直接從 best 字典讀取）
                    exit_reasons = best.get('exit_reasons', {})
                    total_trades = best.get('total_trades', 0)
                    reason_names = {
                        'take_profit': '🔺 停利出場',
                        'stop_loss': '🔻 停損出場',
                        'normal': '⏰ 正常到期'
                    }

                    for reason, count in exit_reasons.items():
                        pct = count/total_trades*100 if total_trades > 0 else 0
                        reason_name = reason_names.get(reason, reason)
                        advice += f"- **{reason_name}**: {count} 筆 ({pct:.1f}%)\n"

                    advice += "\n---\n\n"

            # 策略比較表格
            advice += """## 📊 策略比較總覽

| 策略 | 停損點 | 停利點 | 綜合評分 | 平均報酬 | 勝率 | 最大回撤 | 交易筆數 |
|------|--------|--------|----------|----------|------|----------|----------|
"""

            for strategy_name in ['original', 'A', 'B', 'C']:
                if strategy_name in all_stop_analysis:
                    analysis = all_stop_analysis[strategy_name]
                    best = analysis.get('best_combination', {})

                    strategy_display = strategy_names.get(strategy_name, strategy_name)
                    advice += f"| {strategy_display} | {best.get('stop_loss', 0):.1%} | {best.get('take_profit', 0):.1%} | {best.get('score', 0):.1f} | {best.get('avg_return', 0):.2%} | {best.get('win_rate', 0):.1%} | {best.get('max_drawdown', 0):.1%} | {best.get('total_trades', 0)} |\n"

            # 最佳策略建議
            if best_strategy and best_strategy in all_stop_analysis:
                best_analysis = all_stop_analysis[best_strategy]
                best_combo = best_analysis.get('best_combination', {})
                best_strategy_display = strategy_names.get(best_strategy, best_strategy)

                advice += f"""

## 🏆 最佳策略建議

基於綜合評分，**{best_strategy_display}** 是表現最佳的策略：

### 推薦參數
- **🔻 建議停損點**: {best_combo.get('stop_loss', 0):.1%}
- **🔺 建議停利點**: {best_combo.get('take_profit', 0):.1%}
- **⭐ 綜合評分**: {best_combo.get('score', 0):.1f}/100

### 投資建議
1. **停損停利設定**
   - 嚴格執行 {best_combo.get('stop_loss', 0):.1%} 停損
   - 達到 {best_combo.get('take_profit', 0):.1%} 停利時獲利了結
   - 避免情緒化決策，堅持紀律

2. **風險管理**
   - 分散投資，單一標的不超過總資金 20%
   - 定期檢視持股，適時調整策略
   - 保持適當的現金部位

3. **執行要點**
   - 使用限價單進場，避免追高殺低
   - 設定停損停利自動執行
   - 定期回顧和優化參數

## ⚠️ 風險提醒

- 本分析基於歷史數據，未來績效可能不同
- 市場環境變化可能影響策略效果
- 建議搭配基本面分析，提高投資勝率
- 投資有風險，請謹慎評估自身風險承受能力

---
*本報告由台股投資系統自動生成，僅供參考，不構成投資建議*
"""

            return advice

        except Exception as e:
            return f"# 多策略停損停利分析綜合報告\n\n❌ 生成報告失敗: {e}\n"

    def _safe_improvement(self, new_val, old_val):
        """安全計算改善幅度"""
        if old_val == 0:
            return "N/A" if new_val == 0 else "+∞"
        return f"{((new_val - old_val) / abs(old_val) * 100):+.1f}%"

    def _display_and_write_multi_strategy_results(self, all_stop_analysis, strategy_trades, investment_summary, advice_path):
        """邊輸出 CLI 邊寫 MD 檔案"""
        try:
            from datetime import datetime

            # 開始寫 MD 檔案
            md_content = []

            # MD 檔案標題和基本資訊
            md_content.append("# 多策略停損停利分析綜合報告\n")
            md_content.append("## 📊 分析概要")
            md_content.append(f"- **分析時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            md_content.append(f"- **分析策略數**: {len(all_stop_analysis)} 個策略")
            md_content.append(f"- **分析方法**: 49種停損停利組合測試 (7×7)\n")

            # 投資回測結果摘要
            md_content.append("## 💰 投資回測結果摘要\n")
            md_content.append("### 基本資訊")
            md_content.append(f"- **📅 投資期間**: {investment_summary.get('start_date', 'N/A')} ~ {investment_summary.get('end_date', 'N/A')}")
            md_content.append(f"- **💰 每月投資金額**: {investment_summary.get('monthly_investment', 1000000):,.0f} 元")
            md_content.append(f"- **📊 投資月數**: {investment_summary.get('total_months', 0)} 個月\n")

            md_content.append("### 投資績效")
            md_content.append(f"- **💵 總投入金額**: {investment_summary.get('total_invested', 0):,.0f} 元")
            md_content.append(f"- **💎 總資產價值**: {investment_summary.get('total_current_value', 0):,.0f} 元")
            md_content.append(f"- **💰 總損益**: {investment_summary.get('total_profit_loss', 0):+,.0f} 元")
            md_content.append(f"- **📊 總報酬率**: {investment_summary.get('total_return', 0):.2%}\n")

            # CLI 輸出策略比較表格，同時寫入 MD
            self._log("🎯 各策略最佳停損停利分析結果比較", "info", force_print=True)
            self._log("=" * 80, "info", force_print=True)
            self._log("策略     停損點  停利點  綜合評分  平均報酬  勝率    最大回撤  交易筆數", "info", force_print=True)
            self._log("─" * 80, "info", force_print=True)

            # MD 策略比較表格
            md_content.append("## 📊 策略比較總覽\n")
            md_content.append("| 策略 | 停損點 | 停利點 | 綜合評分 | 平均報酬 | 勝率 | 最大回撤 | 交易筆數 |")
            md_content.append("|------|--------|--------|----------|----------|------|----------|----------|")

            strategy_names = {'original': '原本', 'A': '方案A', 'B': '方案B', 'C': '方案C'}
            best_score = 0
            best_strategy = None

            # 處理每個策略
            for strategy, analysis in all_stop_analysis.items():
                best = analysis.get('best_combination', {})

                strategy_name = strategy_names.get(strategy, strategy)
                stop_loss = best.get('stop_loss', 0) * 100
                take_profit = best.get('take_profit', 0) * 100
                score = best.get('score', 0)
                avg_return = best.get('avg_return', 0) * 100
                win_rate = best.get('win_rate', 0) * 100
                max_drawdown = best.get('max_drawdown', 0) * 100
                total_trades = best.get('total_trades', 0)

                # CLI 輸出
                self._log(f"{strategy_name:<8} {stop_loss:4.1f}%   {take_profit:4.1f}%   {score:6.1f}    {avg_return:6.2f}%  {win_rate:4.1f}%   {max_drawdown:6.2f}%   {total_trades:4d}", "info", force_print=True)

                # MD 輸出
                md_content.append(f"| {strategy_name} | {stop_loss:.1f}% | {take_profit:.1f}% | {score:.1f} | {avg_return:.2f}% | {win_rate:.1f}% | {max_drawdown:.1f}% | {total_trades} |")

                if score > best_score:
                    best_score = score
                    best_strategy = strategy

            self._log("=" * 80, "info", force_print=True)

            if best_strategy:
                strategy_name = strategy_names.get(best_strategy, best_strategy)
                self._log(f"🏆 綜合表現最佳策略: {strategy_name} (評分: {best_score:.1f})", "info", force_print=True)
                self._log("", "info", force_print=True)

                # 顯示最佳策略的詳細結果，同時寫入 MD
                self._log(f"📊 {strategy_name} 策略詳細分析:", "info", force_print=True)

                # MD 最佳策略
                md_content.append(f"\n## 🏆 最佳策略: {strategy_name} (評分: {best_score:.1f})\n")

                # 調用詳細分析，同時寫入 MD
                best_analysis = all_stop_analysis[best_strategy]
                self._display_and_write_stop_loss_results(best_analysis, md_content)

            # 寫入 MD 檔案
            with open(advice_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(md_content))

        except Exception as e:
            self._log(f"⚠️  邊輸出邊寫入時發生錯誤: {e}", "warning", force_print=True)

    def _generate_strategy_detail_md(self, stop_analysis, strategy_name):
        """生成策略詳細分析的 MD 內容，使用與 CLI 完全相同的數據源"""
        try:
            best = stop_analysis.get('best_combination', {})
            original_metrics = stop_analysis.get('original_metrics', {})  # 使用與 CLI 相同的數據源

            if not best:
                return "無可用的分析結果\n"

            md_lines = []

            # 最佳停損停利組合
            md_lines.append("### 🎯 最佳停損停利組合")
            md_lines.append(f"- **🔻 停損點**: {best.get('stop_loss', 0)*100:.1f}%")
            md_lines.append(f"- **🔺 停利點**: {best.get('take_profit', 0)*100:.1f}%")
            md_lines.append(f"- **⭐ 綜合評分**: {best.get('score', 0):.1f}/100\n")

            # 績效比較 - 使用與 CLI 完全相同的計算邏輯
            md_lines.append("### 📈 績效比較")
            md_lines.append("| 指標 | 原始策略 | 最佳停損停利 | 改善幅度 |")
            md_lines.append("|------|----------|-------------|----------|")

            # 平均報酬 - 與 CLI 完全相同的計算
            orig_return = original_metrics.get('avg_return', 0) * 100
            opt_return = best.get('avg_return', 0) * 100
            improvement = ((opt_return - orig_return) / abs(orig_return) * 100) if orig_return != 0 else 0
            improvement_str = f"{improvement:+.1f}%" if orig_return != 0 else ("N/A" if opt_return == 0 else "+∞")

            md_lines.append(f"| 平均報酬率 | {orig_return:.2f}% | {opt_return:.2f}% | {improvement_str} |")

            # 勝率 - 與 CLI 完全相同的計算
            orig_win_rate = original_metrics.get('win_rate', 0) * 100
            opt_win_rate = best.get('win_rate', 0) * 100
            win_improvement = opt_win_rate - orig_win_rate

            md_lines.append(f"| 勝率 | {orig_win_rate:.1f}% | {opt_win_rate:.1f}% | {win_improvement:+.1f}% |")

            # 最大回撤 - 與 CLI 完全相同的計算
            orig_drawdown = original_metrics.get('max_drawdown', 0) * 100
            opt_drawdown = best.get('max_drawdown', 0) * 100
            drawdown_improvement = ((orig_drawdown - opt_drawdown) / orig_drawdown * 100) if orig_drawdown != 0 else 0
            drawdown_str = f"{drawdown_improvement:+.1f}%" if orig_drawdown != 0 else ("N/A" if opt_drawdown == 0 else "+∞")

            md_lines.append(f"| 最大回撤 | {orig_drawdown:.1f}% | {opt_drawdown:.1f}% | {drawdown_str} |\n")

            # 出場原因統計
            exit_reasons = best.get('exit_reasons', {})
            if exit_reasons:
                md_lines.append("### 🚪 出場原因統計")
                total_trades = sum(exit_reasons.values())
                for reason, count in exit_reasons.items():
                    percentage = (count / total_trades * 100) if total_trades > 0 else 0
                    reason_emoji = {"stop_loss": "🔻", "take_profit": "🔺", "normal": "⏰"}.get(reason, "📊")
                    reason_name = {"stop_loss": "停損出場", "take_profit": "停利出場", "normal": "正常到期"}.get(reason, reason)
                    md_lines.append(f"- **{reason_emoji} {reason_name}**: {count} 筆 ({percentage:.1f}%)")

            return '\n'.join(md_lines) + '\n'

        except Exception as e:
            return f"生成策略詳細分析失敗: {e}\n"

    def _display_and_write_stop_loss_results(self, stop_analysis, md_content):
        """邊輸出 CLI 邊寫 MD 的停損停利詳細分析"""
        try:
            best = stop_analysis.get('best_combination', {})
            original_metrics = stop_analysis.get('original_metrics', {})

            if not best:
                return

            # CLI 輸出
            self._log("🎯 最佳停損停利分析結果", "info", force_print=True)
            self._log("=" * 50, "info", force_print=True)
            self._log("📊 最佳停損停利組合:", "info", force_print=True)

            stop_loss_pct = best.get('stop_loss', 0) * 100
            take_profit_pct = best.get('take_profit', 0) * 100
            score = best.get('score', 0)

            self._log(f"    🔻 停損點: {stop_loss_pct:.1f}%", "info", force_print=True)
            self._log(f"    🔺 停利點: {take_profit_pct:.1f}%", "info", force_print=True)
            self._log(f"    ⭐ 綜合評分: {score:.1f}/100", "info", force_print=True)
            self._log("", "info", force_print=True)

            # MD 輸出
            md_content.append("### 🎯 最佳停損停利組合")
            md_content.append(f"- **🔻 停損點**: {stop_loss_pct:.1f}%")
            md_content.append(f"- **🔺 停利點**: {take_profit_pct:.1f}%")
            md_content.append(f"- **⭐ 綜合評分**: {score:.1f}/100\n")

            # 績效比較 - CLI 和 MD 同步
            self._log("📈 績效比較:", "info", force_print=True)
            self._log("    項目           原始策略    最佳停損停利    改善幅度", "info", force_print=True)
            self._log("    " + "─" * 45, "info", force_print=True)

            md_content.append("### 📈 績效比較")
            md_content.append("| 指標 | 原始策略 | 最佳停損停利 | 改善幅度 |")
            md_content.append("|------|----------|-------------|----------|")

            # 平均報酬
            orig_return = original_metrics.get('avg_return', 0) * 100
            opt_return = best.get('avg_return', 0) * 100
            improvement = ((opt_return - orig_return) / abs(orig_return) * 100) if orig_return != 0 else 0

            self._log(f"    平均報酬        {orig_return:6.2f}%       {opt_return:6.2f}%       {improvement:+5.1f}%", "info", force_print=True)
            md_content.append(f"| 平均報酬率 | {orig_return:.2f}% | {opt_return:.2f}% | {self._safe_improvement(opt_return/100, orig_return/100)} |")

            # 勝率
            orig_win_rate = original_metrics.get('win_rate', 0) * 100
            opt_win_rate = best.get('win_rate', 0) * 100
            win_improvement = opt_win_rate - orig_win_rate

            self._log(f"    勝率              {orig_win_rate:4.1f}%         {opt_win_rate:4.1f}%        {win_improvement:+4.1f}%", "info", force_print=True)
            md_content.append(f"| 勝率 | {orig_win_rate:.1f}% | {opt_win_rate:.1f}% | {self._safe_improvement(opt_win_rate/100, orig_win_rate/100)} |")

            # 最大回撤
            orig_drawdown = original_metrics.get('max_drawdown', 0) * 100
            opt_drawdown = best.get('max_drawdown', 0) * 100
            drawdown_improvement = ((orig_drawdown - opt_drawdown) / orig_drawdown * 100) if orig_drawdown != 0 else 0

            self._log(f"    最大回撤          {orig_drawdown:4.1f}%         {opt_drawdown:4.1f}%       {drawdown_improvement:+5.1f}%", "info", force_print=True)
            md_content.append(f"| 最大回撤 | {orig_drawdown:.1f}% | {opt_drawdown:.1f}% | {self._safe_improvement(-opt_drawdown/100, -orig_drawdown/100)} |")

            self._log("", "info", force_print=True)

            # 出場原因統計
            exit_reasons = best.get('exit_reasons', {})
            if exit_reasons:
                self._log("🚪 出場原因統計:", "info", force_print=True)
                md_content.append("\n### 🚪 出場原因統計")

                total_trades = sum(exit_reasons.values())
                for reason, count in exit_reasons.items():
                    percentage = (count / total_trades * 100) if total_trades > 0 else 0
                    reason_emoji = {"stop_loss": "🔻", "take_profit": "🔺", "normal": "⏰"}.get(reason, "📊")
                    reason_name = {"stop_loss": "停損出場", "take_profit": "停利出場", "normal": "正常到期"}.get(reason, reason)

                    self._log(f"    {reason_emoji} {reason_name}: {count} 筆 ({percentage:.1f}%)", "info", force_print=True)
                    md_content.append(f"- **{reason_emoji} {reason_name}**: {count} 筆 ({percentage:.1f}%)")

            self._log("=" * 50, "info", force_print=True)

        except Exception as e:
            self._log(f"⚠️  顯示停損停利結果時發生錯誤: {e}", "warning", force_print=True)


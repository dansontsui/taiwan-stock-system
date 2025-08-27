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
        """創建ASCII進度條"""
        filled = int(width * current / total)
        bar = '█' * filled + '░' * (width - filled)
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
                # 包含兩種計算方式的欄位
                csv_data.append(['進場日', '股票代號', '模型', '預測報酬', '股數', '投資金額', '進場價', '出場日', '出場價',
                               '毛報酬', '淨報酬', '持有天數', '毛損益', '淨損益', '月底價值', '交易成本'])

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
                        f"{trade.get('transaction_costs', {}).get('total_cost_amount', 0.0):,.0f}"
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

            # 計算報酬和損益（加入交易成本）
            gross_return = (exit_price - entry_price) / entry_price

            # 假設固定1000股進行交易成本計算
            shares = 1000
            transaction_costs = self._calculate_transaction_costs(entry_price, exit_price, shares)

            # 淨報酬 = 毛報酬 - 交易成本率
            actual_return = gross_return - transaction_costs['total_cost_rate']

            # 淨損益 = 毛損益 - 交易成本金額（以1000股為基準）
            gross_profit_loss = (exit_price - entry_price) * shares
            profit_loss = gross_profit_loss - transaction_costs['total_cost_amount']

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
        total_cost_rate = total_cost_amount / buy_amount

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
        monthly_results = self._execute_monthly_investment_backtest(
            stock_predictors, start, end, threshold, k, use_market_filter, monthly_investment, session_id, output_dir
        )

        # 計算整體績效
        portfolio_metrics = self._calculate_monthly_investment_metrics(monthly_results, monthly_investment)

        # 生成詳細交易記錄DataFrame
        all_trades = []
        for month_result in monthly_results:
            all_trades.extend(month_result['trades'])

        trades_df = pd.DataFrame(all_trades) if all_trades else pd.DataFrame()

        # 保存結果到CSV（使用已存在的目錄和會話ID）
        self._save_monthly_investment_results(monthly_results, portfolio_metrics, trades_df, start, end, monthly_investment, threshold, k, use_market_filter, session_id, output_dir)

        return {
            'success': True,
            'backtest_type': 'monthly_investment',
            'monthly_investment': monthly_investment,
            'start_date': start,
            'end_date': end,
            'monthly_results': monthly_results,
            'portfolio_metrics': portfolio_metrics,
            'trades_df': trades_df,
            'params': {
                'min_predicted_return': threshold,
                'top_k': k,
                'use_market_filter': use_market_filter
            }
        }

    def _execute_monthly_investment_backtest(self,
                                           stock_predictors: Dict[str, StockPricePredictor],
                                           start_date: str,
                                           end_date: str,
                                           threshold: float,
                                           top_k: int,
                                           use_market_filter: bool,
                                           monthly_investment: float,
                                           session_id: str = None,
                                           output_dir: Path = None) -> List[Dict[str, Any]]:
        """執行每月定期定額投資回測的核心邏輯"""

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

                # 獲取進場價格（月底收盤價）
                entry_price = self._get_stock_price(stock_id, as_of)
                if entry_price is None:
                    continue

                # 計算可買股數（扣除交易成本後）
                shares = self._calculate_shares_after_costs(per_stock_investment, entry_price)
                actual_investment = shares * entry_price

                # 執行20日交易
                trade_info = self._execute_trade(stock_id, as_of, 20)
                if trade_info:
                    # 計算該股票的月底價值
                    stock_month_end_value = shares * trade_info['exit_price']
                    total_month_end_value += stock_month_end_value

                    # 記錄交易（包含兩種計算方式）
                    trade_record = {
                        # 基本資訊
                        'entry_date': as_of,
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
                        'cost_impact': trade_info.get('gross_return', trade_info['actual_return']) - trade_info['actual_return']
                    }
                    month_trades.append(trade_record)

            # 計算當月整體報酬率
            total_investment = sum(t['investment_amount'] for t in month_trades)
            month_return_rate = (total_month_end_value - total_investment) / total_investment if total_investment > 0 else 0

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
        costs = self.trading_cfg['transaction_costs']

        # 買進時的成本率（手續費 + 滑價）
        buy_cost_rate = costs['commission_rate'] + (costs['slippage_bps'] / 10000)

        # 可用於購買股票的金額（扣除買進成本）
        available_amount = investment_amount / (1 + buy_cost_rate)

        # 計算股數（向下取整到1000股的倍數，台股通常以1000股為單位）
        max_shares = int(available_amount / entry_price / 1000) * 1000

        # 確保至少買1000股，但不超過可負擔的股數
        if max_shares < 1000:
            # 如果連1000股都買不起，就買1000股（可能會超出預算）
            return 1000
        else:
            return max_shares

    def _calculate_monthly_investment_metrics(self, monthly_results: List[Dict[str, Any]], monthly_investment: float) -> Dict[str, Any]:
        """計算每月定期定額投資的整體績效指標"""

        if not monthly_results:
            return {}

        # 計算累積投資和價值
        total_invested = 0
        total_current_value = 0
        monthly_returns = []
        cumulative_values = []

        for result in monthly_results:
            total_invested += result['investment_amount']
            total_current_value += result['month_end_value']
            monthly_returns.append(result['return_rate'])
            cumulative_values.append(total_current_value)

        # 基本指標
        total_return = (total_current_value - total_invested) / total_invested if total_invested > 0 else 0

        # 月度報酬統計
        monthly_returns_series = pd.Series([r for r in monthly_returns if r != 0])  # 排除無交易月份

        if len(monthly_returns_series) > 0:
            avg_monthly_return = monthly_returns_series.mean()
            monthly_volatility = monthly_returns_series.std()
            win_rate = (monthly_returns_series > 0).mean()

            # 年化指標
            annualized_return = (1 + avg_monthly_return) ** 12 - 1
            annualized_volatility = monthly_volatility * (12 ** 0.5)
            sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility > 0 else 0
        else:
            avg_monthly_return = 0
            monthly_volatility = 0
            win_rate = 0
            annualized_return = 0
            annualized_volatility = 0
            sharpe_ratio = 0

        # 最大回撤計算
        peak_value = 0
        max_drawdown = 0
        for value in cumulative_values:
            if value > peak_value:
                peak_value = value
            drawdown = (peak_value - value) / peak_value if peak_value > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)

        # 交易統計
        total_trades = sum(len(result['trades']) for result in monthly_results)
        successful_months = sum(1 for result in monthly_results if result['return_rate'] > 0)
        total_months = len([r for r in monthly_results if r['investment_amount'] > 0])

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
            'monthly_win_rate': successful_months / total_months if total_months > 0 else 0,
            'total_trades': total_trades,
            'total_months': total_months,
            'successful_months': successful_months
        }

    def _save_monthly_investment_results(self, monthly_results: List[Dict[str, Any]],
                                       portfolio_metrics: Dict[str, Any],
                                       trades_df: pd.DataFrame,
                                       start_date: str, end_date: str,
                                       monthly_investment: float,
                                       threshold: float, k: int, use_market_filter: bool,
                                       session_id: str, output_dir: Path):
        """保存每月定期定額投資結果到CSV檔案（使用已存在的目錄和會話ID）"""
        try:
            from datetime import datetime
            import json

            # 使用傳入的會話ID作為時間戳（與每月報告保持一致）
            ts = session_id

            # 使用已存在的輸出目錄（與每月報告在同一位置）
            # output_dir 已經在調用時傳入，不需要重新創建

            # 1. 保存詳細交易記錄CSV（包含兩種計算方式）- 使用與選項5相同的命名
            if not trades_df.empty:
                csv_path = output_dir / f'holdout_trades_{ts}.csv'
                trades_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
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

            self._log(f"📁 所有最終結果已保存至與每月報告相同的目錄", "info", force_print=True)
            self._log(f"📂 完整路徑: {output_dir}", "info", force_print=True)

        except Exception as e:
            self._log(f"⚠️  保存結果失敗: {e}", "warning", force_print=True)


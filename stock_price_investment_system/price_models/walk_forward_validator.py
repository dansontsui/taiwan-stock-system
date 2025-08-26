# -*- coding: utf-8 -*-
"""
股價預測與投資建議系統 - Walk-forward驗證器
Stock Price Investment System - Walk-forward Validator
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

from .feature_engineering import FeatureEngineer
from .stock_price_predictor import StockPricePredictor
from ..config.settings import get_config

logger = logging.getLogger(__name__)

class WalkForwardValidator:
    """Walk-forward驗證器 - 實作內層滾動驗證"""

    def __init__(self,
                 feature_engineer: FeatureEngineer = None,
                 predictor_class: type = StockPricePredictor,
                 verbose_logging: bool = False,
                 cli_only_logging: bool = False):
        """
        初始化Walk-forward驗證器

        Args:
            feature_engineer: 特徵工程師
            predictor_class: 預測器類別
            verbose_logging: 是否啟用詳細日誌
            cli_only_logging: 是否只輸出到CLI（不記錄日誌檔案）
        """
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.predictor_class = predictor_class
        self.verbose_logging = verbose_logging
        self.cli_only_logging = cli_only_logging

        self.config = get_config()
        self.wf_config = self.config['walkforward']

        # 可選：指定使用的模型與其最佳參數
        self.models_to_use: Optional[List[str]] = None  # 例如 ['xgboost','lightgbm','random_forest']
        self.override_models: Optional[Dict[str, Dict[str, Any]]] = None  # 例如 {'xgboost': {...}, 'lightgbm': {...}}

        # 結果儲存
        self.fold_results = []
        self.stock_statistics = {}

        if verbose_logging:
            logger.info("WalkForwardValidator initialized with verbose logging")
        else:
            print("🔧 Walk-Forward驗證器已初始化")

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

    def run_validation(self,
                      stock_ids: List[str],
                      start_date: str = None,
                      end_date: str = None,
                      train_window_months: int = None,
                      test_window_months: int = None,
                      stride_months: int = None,
                      models_to_use: Optional[List[str]] = None,
                      override_models: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        執行Walk-forward驗證

        # 設定可選參數
        self.models_to_use = models_to_use or self.models_to_use
        self.override_models = override_models or self.override_models

        Args:
            stock_ids: 股票代碼清單
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            train_window_months: 訓練視窗月數
            test_window_months: 測試視窗月數
            stride_months: 步長月數

        Returns:
            驗證結果字典
        """
        # 使用配置預設值
        start_date = start_date or self.wf_config['training_start'] + '-01'
        end_date = end_date or self.wf_config['training_end'] + '-31'
        train_window_months = train_window_months or self.wf_config['train_window_months']
        test_window_months = test_window_months or self.wf_config['test_window_months']
        stride_months = stride_months or self.wf_config['stride_months']

        logger.info(f"Starting walk-forward validation for {len(stock_ids)} stocks")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Windows: train={train_window_months}m, test={test_window_months}m, stride={stride_months}m")

        # 生成fold時間範圍
        folds = self._generate_folds(
            start_date, end_date,
            train_window_months, test_window_months, stride_months
        )

        logger.info(f"Generated {len(folds)} folds for validation")

        # 執行每個fold
        self.fold_results = []

        for fold_idx, fold_info in enumerate(folds):
            logger.info(f"Processing fold {fold_idx + 1}/{len(folds)}")
            logger.info(f"Train: {fold_info['train_start']} to {fold_info['train_end']}")
            logger.info(f"Test: {fold_info['test_start']} to {fold_info['test_end']}")

            fold_result = self._run_single_fold(
                stock_ids, fold_info, fold_idx
            )

            if fold_result['success']:
                self.fold_results.append(fold_result)
                logger.info(f"Fold {fold_idx + 1} completed successfully")
            else:
                logger.warning(f"Fold {fold_idx + 1} failed: {fold_result.get('error', 'Unknown error')}")

        # 計算股票統計
        self._calculate_stock_statistics()

        # 生成總結報告
        summary = self._generate_summary()

        logger.info(f"Walk-forward validation completed: {len(self.fold_results)} successful folds")
        return summary

    def _generate_folds(self,
                       start_date: str,
                       end_date: str,
                       train_window_months: int,
                       test_window_months: int,
                       stride_months: int) -> List[Dict[str, str]]:
        """生成fold時間範圍"""
        folds = []

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        # 第一個fold的訓練開始時間
        current_train_start = start_dt

        while True:
            # 計算訓練結束時間
            train_end_dt = current_train_start + timedelta(days=train_window_months * 30)

            # 計算測試開始和結束時間
            test_start_dt = train_end_dt + timedelta(days=1)
            test_end_dt = test_start_dt + timedelta(days=test_window_months * 30)

            # 檢查是否超出範圍
            if test_end_dt > end_dt:
                break

            fold_info = {
                'train_start': current_train_start.strftime('%Y-%m-%d'),
                'train_end': train_end_dt.strftime('%Y-%m-%d'),
                'test_start': test_start_dt.strftime('%Y-%m-%d'),
                'test_end': test_end_dt.strftime('%Y-%m-%d')
            }

            folds.append(fold_info)

            # 移動到下一個fold
            current_train_start += timedelta(days=stride_months * 30)

        return folds

    def _run_single_fold(self,
                        stock_ids: List[str],
                        fold_info: Dict[str, str],
                        fold_idx: int) -> Dict[str, Any]:
        """執行單個fold - 改為每檔股票獨立建模"""
        try:
            logger.info(f"Fold {fold_idx}: 開始為 {len(stock_ids)} 檔股票建立獨立模型")

            # 儲存每檔股票的模型和結果
            stock_models = {}
            fold_trades = []
            stock_performance = {}

            # 為每檔股票建立獨立模型
            for stock_id in stock_ids:
                logger.debug(f"Fold {fold_idx}: 處理股票 {stock_id}")

                # 生成該股票的訓練資料
                train_features, train_targets = self.feature_engineer.generate_training_dataset(
                    [stock_id],  # 只訓練單一股票
                    fold_info['train_start'],
                    fold_info['train_end'],
                    target_periods=[20],
                    frequency='monthly'
                )

                if train_features.empty or train_targets.empty:
                    logger.debug(f"股票 {stock_id} 無訓練資料，跳過")
                    continue

                # 檢查最小樣本數
                if len(train_features) < self.wf_config['min_training_samples']:
                    logger.debug(f"股票 {stock_id} 訓練樣本不足 ({len(train_features)} < {self.wf_config['min_training_samples']})，跳過")
                    continue

                # 訓練該股票的獨立模型（使用該股票專屬的最佳參數）
                # 決定使用的模型清單
                model_types = self.models_to_use or [self.config['model']['primary_model']]

                # 檢查是否使用自動選擇最佳模型
                if model_types == ['auto_best']:
                    # 自動選擇該股票的最佳模型和參數
                    from .hyperparameter_tuner import HyperparameterTuner
                    best_model_info = HyperparameterTuner.get_stock_best_model_and_params(stock_id)

                    if best_model_info and best_model_info['success']:
                        model_types = [best_model_info['model_type']]
                        logger.debug(f"股票 {stock_id} 自動選擇最佳模型: {best_model_info['model_type']}, 分數: {best_model_info['score']:.4f}")
                    else:
                        # 如果沒有調優記錄，回退到主模型
                        model_types = [self.config['model']['primary_model']]
                        logger.debug(f"股票 {stock_id} 無調優記錄，使用主模型: {model_types[0]}")

                # 對每一種模型類型都訓練一次（各自一套模型）
                for mtype in model_types:
                    params_override = None

                    # 優先使用該股票專屬的最佳參數
                    from .hyperparameter_tuner import HyperparameterTuner
                    stock_best_params = HyperparameterTuner.get_stock_best_params(stock_id, mtype)

                    if stock_best_params:
                        params_override = stock_best_params
                        logger.debug(f"股票 {stock_id} 使用專屬最佳參數 {mtype}: {params_override}")
                    elif self.override_models and mtype in self.override_models:
                        params_override = self.override_models[mtype]
                        logger.debug(f"股票 {stock_id} 使用通用最佳參數 {mtype}: {params_override}")
                    else:
                        logger.debug(f"股票 {stock_id} 使用預設參數 {mtype}")

                    predictor = self.predictor_class(self.feature_engineer, model_type=mtype, override_params=params_override)
                    train_result = predictor.train(train_features, train_targets)

                    if not train_result['success']:
                        logger.debug(f"股票 {stock_id} 模型 {mtype} 訓練失敗: {train_result.get('error', 'Unknown')}")
                        continue

                    # 儲存模型（以 (stock_id, model_type) 做 key）
                    stock_models[(stock_id, mtype)] = predictor
                    logger.debug(f"股票 {stock_id} 模型 {mtype} 訓練成功，樣本數: {train_result['training_samples']}")

                if not train_result['success']:
                    logger.debug(f"股票 {stock_id} 模型訓練失敗: {train_result.get('error', 'Unknown')}")
                    continue

                # 儲存模型
                stock_models[stock_id] = predictor
                logger.debug(f"股票 {stock_id} 模型訓練成功，樣本數: {train_result['training_samples']}")

            logger.info(f"Fold {fold_idx}: 成功訓練 {len(stock_models)} 檔股票的模型")

            # 在測試期間進行預測和回測
            backtest_result = self._run_fold_backtest_individual(
                stock_models, fold_info, fold_idx
            )

            return {
                'success': True,
                'fold_idx': fold_idx,
                'fold_info': fold_info,
                'trained_stocks': len(stock_models),
                'backtest_result': backtest_result
            }

        except Exception as e:
            logger.error(f"Error in fold {fold_idx}: {e}")
            return {
                'success': False,
                'error': str(e),
                'fold_idx': fold_idx,
                'fold_info': fold_info
            }

    def _run_fold_backtest_individual(self,
                                     stock_models: Dict[str, StockPricePredictor],
                                     fold_info: Dict[str, str],
                                     fold_idx: int) -> Dict[str, Any]:
        """執行fold回測 - 使用個股獨立模型"""
        # 生成測試期間的月度時間點
        test_start = datetime.strptime(fold_info['test_start'], '%Y-%m-%d')
        test_end = datetime.strptime(fold_info['test_end'], '%Y-%m-%d')

        # 生成月度預測時點
        prediction_dates = pd.date_range(
            start=test_start,
            end=test_end,
            freq='M'
        )

        fold_trades = []
        stock_performance = {}

        # 獲取選股門檻
        selection_rules = get_config('selection')['selection_rules']
        min_expected_return = selection_rules['min_expected_return']

        for pred_date in prediction_dates:
            pred_date_str = pred_date.strftime('%Y-%m-%d')
            logger.debug(f"Fold {fold_idx}: 預測日期 {pred_date_str}")

            # 對每檔有模型的股票進行預測（支援多模型）
            for key, predictor in stock_models.items():
                try:
                    # 兼容舊鍵格式與新格式(key=(stock_id, model_type))
                    if isinstance(key, tuple):
                        stock_id, model_type = key
                    else:
                        stock_id, model_type = key, getattr(predictor, 'model_type', 'unknown')

                    # 使用該股票的模型預測
                    pred_result = predictor.predict(stock_id, pred_date_str)

                    if not pred_result['success']:
                        continue

                    predicted_return = pred_result['predicted_return']

                    # 選股邏輯：預期報酬大於門檻
                    if predicted_return > min_expected_return:
                        # 計算實際報酬
                        actual_return = self._calculate_actual_return(
                            stock_id, pred_date_str, holding_days=20
                        )

                        if actual_return is not None:
                            trade_info = {
                                'fold_idx': fold_idx,
                                'stock_id': stock_id,
                                'model_type': model_type,
                                'entry_date': pred_date_str,
                                'predicted_return': predicted_return,
                                'actual_return': actual_return,
                                'holding_days': 20
                            }

                            fold_trades.append(trade_info)

                            # 更新股票績效統計（仍以股票聚合，但在交易中保留模型資訊）
                            if stock_id not in stock_performance:
                                stock_performance[stock_id] = {
                                    'trades': [],
                                    'total_trades': 0,
                                    'winning_trades': 0,
                                    'total_return': 0
                                }

                            stock_perf = stock_performance[stock_id]
                            stock_perf['trades'].append(trade_info)
                            stock_perf['total_trades'] += 1
                            stock_perf['total_return'] += actual_return

                            if actual_return > 0:
                                stock_perf['winning_trades'] += 1

                except Exception as e:
                    logger.debug(f"股票 {stock_id} 預測失敗: {e}")
                    continue

        # 計算fold績效指標
        fold_metrics = self._calculate_fold_metrics(fold_trades, stock_performance)

        return {
            'trades': fold_trades,
            'stock_performance': stock_performance,
            'metrics': fold_metrics,
            'total_trades': len(fold_trades)
        }

    def _calculate_actual_return(self,
                               stock_id: str,
                               entry_date: str,
                               holding_days: int = 20) -> Optional[float]:
        """計算實際報酬率"""
        try:
            # 計算退出日期
            entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
            exit_dt = entry_dt + timedelta(days=holding_days)
            exit_date = exit_dt.strftime('%Y-%m-%d')

            # 獲取價格資料
            price_df = self.feature_engineer.data_manager.get_stock_prices(
                stock_id, entry_date, exit_date
            )

            if len(price_df) < 2:
                return None

            # 計算報酬率
            entry_price = price_df.iloc[0]['close']
            exit_price = price_df.iloc[-1]['close']

            return (exit_price - entry_price) / entry_price

        except Exception as e:
            logger.debug(f"Error calculating actual return for {stock_id}: {e}")
            return None

    def _calculate_fold_metrics(self,
                              trades: List[Dict],
                              stock_performance: Dict) -> Dict[str, float]:
        """計算fold績效指標"""
        if not trades:
            return {}

        returns = [trade['actual_return'] for trade in trades]

        metrics = {
            'total_trades': len(trades),
            'total_return': sum(returns),
            'average_return': np.mean(returns),
            'win_rate': sum(1 for r in returns if r > 0) / len(returns),
            'profit_loss_ratio': np.mean([r for r in returns if r > 0]) / abs(np.mean([r for r in returns if r < 0])) if any(r < 0 for r in returns) else float('inf'),
            'max_return': max(returns),
            'min_return': min(returns),
            'return_std': np.std(returns),
            'sharpe_ratio': np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        }

        return metrics

    def _calculate_stock_statistics(self):
        """計算股票統計"""
        self.stock_statistics = {}

        # 收集所有股票的交易記錄
        for fold_result in self.fold_results:
            if not fold_result['success']:
                continue

            backtest_result = fold_result['backtest_result']

            for stock_id, stock_perf in backtest_result['stock_performance'].items():
                if stock_id not in self.stock_statistics:
                    self.stock_statistics[stock_id] = {
                        'all_trades': [],
                        'fold_count': 0,
                        'total_trades': 0
                    }

                self.stock_statistics[stock_id]['all_trades'].extend(stock_perf['trades'])
                self.stock_statistics[stock_id]['fold_count'] += 1
                self.stock_statistics[stock_id]['total_trades'] += stock_perf['total_trades']

        # 計算每檔股票的綜合統計
        for stock_id, stock_stat in self.stock_statistics.items():
            trades = stock_stat['all_trades']

            if trades:
                returns = [trade['actual_return'] for trade in trades]

                stock_stat.update({
                    'win_rate': sum(1 for r in returns if r > 0) / len(returns),
                    'average_return': np.mean(returns),
                    'total_return': sum(returns),
                    'return_std': np.std(returns),
                    'max_return': max(returns),
                    'min_return': min(returns),
                    'profit_loss_ratio': np.mean([r for r in returns if r > 0]) / abs(np.mean([r for r in returns if r < 0])) if any(r < 0 for r in returns) else float('inf'),
                    'sharpe_ratio': np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
                })

    def _generate_summary(self) -> Dict[str, Any]:
        """生成總結報告"""
        summary = {
            'validation_config': {
                'train_window_months': self.wf_config['train_window_months'],
                'test_window_months': self.wf_config['test_window_months'],
                'stride_months': self.wf_config['stride_months']
            },
            'fold_count': len(self.fold_results),
            'stock_count': len(self.stock_statistics),
            'total_trades': sum(len(fold['backtest_result']['trades']) for fold in self.fold_results if fold['success']),
            'stock_statistics': self.stock_statistics,
            'fold_results': self.fold_results
        }

        return summary

    def save_results(self, filepath: str = None) -> str:
        """儲存驗證結果（統一寫入系統資料夾 results/walk_forward）"""
        out_paths = get_config('output')['paths']
        out_dir = Path(out_paths['walk_forward_results'])
        out_dir.mkdir(parents=True, exist_ok=True)

        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = out_dir / f"walk_forward_results_{timestamp}.json"
        else:
            filepath = out_dir / filepath

        results = {
            'stock_statistics': self.stock_statistics,
            'fold_results': self.fold_results,
            'config': self.wf_config,
            'created_at': datetime.now().isoformat()
        }

        with open(filepath, 'w', encoding='utf-8-sig') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        # 同時生成CSV檔案（交易明細）
        csv_filepath = filepath.with_suffix('.csv')
        self._save_trades_csv(csv_filepath)

        logger.info(f"Walk-forward results saved to {filepath}")
        logger.info(f"Walk-forward trades CSV saved to {csv_filepath}")
        return str(filepath)

    def _save_trades_csv(self, csv_filepath: Path):
        """儲存交易明細為CSV檔案"""
        import pandas as pd

        # 收集所有交易記錄（從stock_statistics中獲取）
        all_trades = []

        for stock_id, stock_stats in self.stock_statistics.items():
            for trade in stock_stats.get('all_trades', []):
                try:
                    # 處理預測報酬（可能是字串或數字）
                    pred_return = float(trade['predicted_return']) if isinstance(trade['predicted_return'], str) else trade['predicted_return']
                    actual_return = float(trade['actual_return'])

                    trade_record = {
                        '時間週期': f"Fold {trade['fold_idx']}",
                        '股票代碼': trade['stock_id'],
                        '模型類型': trade.get('model_type', 'unknown'),
                        '進場日期': trade['entry_date'],
                        '預測報酬': f"{pred_return:.2%}",
                        '實際報酬': f"{actual_return:.2%}",
                        '持有天數': trade['holding_days'],
                        '預測正確': '是' if (pred_return > 0) == (actual_return > 0) else '否'
                    }
                    all_trades.append(trade_record)
                except (ValueError, KeyError) as e:
                    logger.warning(f"跳過無效交易記錄: {e}")
                    continue

        if all_trades:
            trades_df = pd.DataFrame(all_trades)
            trades_df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
            logger.info(f"儲存 {len(all_trades)} 筆交易記錄到 CSV")
        else:
            logger.warning("沒有交易記錄可儲存")

# -*- coding: utf-8 -*-
"""
超參數調優器 - 針對單檔股票進行網格搜尋，找出最佳參數組合
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path
import json
import logging
from itertools import product

from .feature_engineering import FeatureEngineer
from .stock_price_predictor import StockPricePredictor
from ..config.settings import get_config

logger = logging.getLogger(__name__)

class HyperparameterTuner:
    """超參數調優器"""
    
    def __init__(self, feature_engineer: FeatureEngineer = None):
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.config = get_config()
        
        # 預設參數網格
        self.param_grids = {
            'xgboost': {
                'max_depth': [3, 6, 9],
                'learning_rate': [0.01, 0.1, 0.2],
                'n_estimators': [50, 100, 200],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            },
            'lightgbm': {
                'max_depth': [3, 6, 9],
                'learning_rate': [0.01, 0.1, 0.2],
                'n_estimators': [50, 100, 200],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            },
            'random_forest': {
                'max_depth': [3, 6, 9, None],
                'n_estimators': [50, 100, 200],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        }
        
        # 選股參數網格
        self.selection_grids = {
            'min_expected_return': [0.01, 0.02, 0.03, 0.05],
            'min_confidence_score': [0.2, 0.3, 0.4, 0.5, 0.6]
        }
        
        logger.info("HyperparameterTuner initialized")
    
    def tune_all_models(self,
                       stock_id: str,
                       train_start: str = None,
                       train_end: str = None,
                       test_start: str = None,
                       test_end: str = None,
                       max_combinations: int = 30) -> Dict[str, Any]:
        """對單檔股票測試所有模型類型"""
        logger.info(f"開始對股票 {stock_id} 進行全模型調優")

        model_types = ['xgboost', 'lightgbm', 'random_forest']
        all_results = {}
        best_overall = {'score': -float('inf'), 'model': None, 'params': None}

        for model_type in model_types:
            logger.info(f"測試模型: {model_type}")
            result = self.tune_single_stock(
                stock_id, model_type, train_start, train_end,
                test_start, test_end, max_combinations
            )
            all_results[model_type] = result

            if result['success'] and result['best_score'] > best_overall['score']:
                best_overall = {
                    'score': result['best_score'],
                    'model': model_type,
                    'params': result['best_params']
                }

        return {
            'stock_id': stock_id,
            'all_models': all_results,
            'best_overall': best_overall,
            'created_at': datetime.now().isoformat()
        }

    def tune_single_stock(self,
                         stock_id: str,
                         model_type: str = 'xgboost',
                         train_start: str = None,
                         train_end: str = None,
                         test_start: str = None,
                         test_end: str = None,
                         max_combinations: int = 50) -> Dict[str, Any]:
        """
        對單檔股票進行超參數調優
        
        Args:
            stock_id: 股票代碼
            model_type: 模型類型
            train_start: 訓練開始日期
            train_end: 訓練結束日期  
            test_start: 測試開始日期
            test_end: 測試結束日期
            max_combinations: 最大參數組合數
            
        Returns:
            調優結果字典
        """
        logger.info(f"開始對股票 {stock_id} 進行超參數調優")
        
        # 使用預設時間範圍
        wf_config = self.config['walkforward']
        train_start = train_start or (wf_config['training_start'] + '-01')
        train_end = train_end or (wf_config['training_end'] + '-31')
        test_start = test_start or (wf_config['holdout_start'] + '-01')
        test_end = test_end or (wf_config['holdout_end'] + '-31')
        
        # 準備訓練和測試資料
        train_features, train_targets = self.feature_engineer.generate_training_dataset(
            [stock_id], train_start, train_end, target_periods=[20], frequency='monthly'
        )
        
        test_features, test_targets = self.feature_engineer.generate_training_dataset(
            [stock_id], test_start, test_end, target_periods=[20], frequency='monthly'
        )
        
        if train_features.empty or test_features.empty:
            return {
                'success': False,
                'error': f'股票 {stock_id} 訓練或測試資料不足',
                'stock_id': stock_id
            }
        
        logger.info(f"股票 {stock_id} 訓練樣本: {len(train_features)}, 測試樣本: {len(test_features)}")
        
        # 生成參數組合
        param_combinations = self._generate_param_combinations(model_type, max_combinations)
        logger.info(f"將測試 {len(param_combinations)} 個參數組合")
        
        # 執行網格搜尋 - 記錄所有結果（包含失敗）
        results = []
        best_score = -float('inf')
        best_params = None

        for i, params in enumerate(param_combinations):
            logger.info(f"測試參數組合 {i+1}/{len(param_combinations)}: {params}")

            result = {
                'combination_id': i + 1,
                'stock_id': stock_id,
                'model_type': model_type,
                'parameters': params,
                'success': False,
                'error_message': None,
                'train_metrics': {},
                'test_score': -1.0,
                'test_metrics': {},
                'feature_count': 0
            }

            try:
                # 訓練模型
                predictor = StockPricePredictor(self.feature_engineer, model_type)
                predictor.model = self._create_model_with_params(model_type, params)

                train_result = predictor.train(train_features, train_targets)

                if not train_result['success']:
                    result['error_message'] = f"訓練失敗: {train_result.get('error', 'Unknown')}"
                    logger.warning(f"參數組合 {i+1} {result['error_message']}")
                else:
                    # 在測試集上評估
                    test_score, test_metrics = self._evaluate_on_test_set(
                        predictor, test_features, test_targets, stock_id
                    )

                    # 更新結果
                    result.update({
                        'success': True,
                        'train_metrics': train_result['validation_metrics'],
                        'test_score': test_score,
                        'test_metrics': test_metrics,
                        'feature_count': train_result['feature_count']
                    })

                    # 更新最佳參數
                    if test_score > best_score:
                        best_score = test_score
                        best_params = params.copy()

                    logger.info(f"參數組合 {i+1} 測試分數: {test_score:.4f}")

            except Exception as e:
                result['error_message'] = f"執行異常: {str(e)}"
                logger.error(f"參數組合 {i+1} 執行失敗: {e}")

            # 不管成功失敗都記錄
            results.append(result)
        
        # 統計成功失敗
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]

        # 整理結果 - 不管成功失敗都要有CSV
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('test_score', ascending=False)

        # 分析失敗原因
        failure_analysis = {}
        if failed_results:
            for result in failed_results:
                error_type = result['error_message'].split(':')[0] if result['error_message'] else 'Unknown'
                failure_analysis[error_type] = failure_analysis.get(error_type, 0) + 1

        tuning_result = {
            'success': len(successful_results) > 0,
            'stock_id': stock_id,
            'model_type': model_type,
            'best_params': best_params,
            'best_score': best_score,
            'total_combinations': len(param_combinations),
            'successful_combinations': len(successful_results),
            'failed_combinations': len(failed_results),
            'failure_analysis': failure_analysis,
            'train_period': f"{train_start} to {train_end}",
            'test_period': f"{test_start} to {test_end}",
            'all_results': results,
            'created_at': datetime.now().isoformat()
        }

        # 如果有成功的結果，計算統計
        if successful_results:
            successful_scores = [r['test_score'] for r in successful_results]
            tuning_result['results_summary'] = {
                'top_5_scores': sorted(successful_scores, reverse=True)[:5],
                'mean_score': np.mean(successful_scores),
                'std_score': np.std(successful_scores)
            }
        else:
            tuning_result['results_summary'] = {
                'top_5_scores': [],
                'mean_score': 0.0,
                'std_score': 0.0
            }

        # 儲存結果（不管成功失敗都儲存）
        self._save_tuning_results(tuning_result, results_df)

        if successful_results:
            logger.info(f"股票 {stock_id} 超參數調優完成，最佳分數: {best_score:.4f}")
        else:
            logger.warning(f"股票 {stock_id} 超參數調優失敗，所有參數組合都失敗")

        return tuning_result
    
    def _generate_param_combinations(self, model_type: str, max_combinations: int) -> List[Dict]:
        """生成參數組合"""
        if model_type not in self.param_grids:
            logger.warning(f"未知模型類型 {model_type}，使用 xgboost 參數")
            model_type = 'xgboost'
        
        param_grid = self.param_grids[model_type]
        
        # 生成所有組合
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        all_combinations = []
        for combination in product(*values):
            param_dict = dict(zip(keys, combination))
            all_combinations.append(param_dict)
        
        # 限制組合數量
        if len(all_combinations) > max_combinations:
            # 隨機採樣
            import random
            random.seed(42)
            all_combinations = random.sample(all_combinations, max_combinations)
        
        return all_combinations
    
    def _create_model_with_params(self, model_type: str, params: Dict) -> Any:
        """根據參數創建模型"""
        try:
            if model_type == 'xgboost':
                import xgboost as xgb
                base_params = self.config['model']['xgboost_params'].copy()
                base_params.update(params)
                return xgb.XGBRegressor(**base_params)
            
            elif model_type == 'lightgbm':
                import lightgbm as lgb
                base_params = self.config['model']['lightgbm_params'].copy()
                base_params.update(params)
                return lgb.LGBMRegressor(**base_params)
            
            elif model_type == 'random_forest':
                from sklearn.ensemble import RandomForestRegressor
                base_params = {'random_state': 42, 'n_jobs': -1}
                base_params.update(params)
                return RandomForestRegressor(**base_params)
            
        except ImportError:
            logger.warning(f"無法匯入 {model_type}，使用隨機森林")
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(random_state=42, n_jobs=-1)
    
    def _evaluate_on_test_set(self, predictor: StockPricePredictor, 
                            test_features: pd.DataFrame, 
                            test_targets: pd.DataFrame,
                            stock_id: str) -> Tuple[float, Dict]:
        """在測試集上評估模型"""
        # 合併特徵和目標
        merged_df = test_features.merge(
            test_targets[['stock_id', 'as_of_date', 'target_20d']], 
            on=['stock_id', 'as_of_date'], 
            how='inner'
        )
        
        if merged_df.empty:
            return -1.0, {}
        
        # 準備特徵
        feature_columns = [col for col in merged_df.columns 
                          if col not in ['stock_id', 'as_of_date', 'target_20d']]
        
        X_test = merged_df[feature_columns].values
        y_test = merged_df['target_20d'].values
        
        # 預測
        y_pred = predictor.model.predict(X_test)
        
        # 計算指標
        from sklearn.metrics import mean_squared_error, r2_score
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # 計算方向準確率（更重要的指標）
        direction_accuracy = np.mean(np.sign(y_pred) == np.sign(y_test))
        
        # 使用方向準確率作為主要評分
        score = direction_accuracy
        
        metrics = {
            'mse': mse,
            'rmse': np.sqrt(mse),
            'r2': r2,
            'direction_accuracy': direction_accuracy,
            'mean_pred': np.mean(y_pred),
            'std_pred': np.std(y_pred)
        }
        
        return score, metrics
    
    def _save_tuning_results(self, tuning_result: Dict, results_df: pd.DataFrame):
        """儲存調優結果"""
        # 確保輸出目錄存在
        out_paths = self.config['output']['paths']
        results_dir = Path(out_paths['models']) / 'hyperparameter_tuning'
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stock_id = tuning_result['stock_id']
        
        # 儲存 JSON 結果
        json_file = results_dir / f"tuning_{stock_id}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8-sig') as f:
            json.dump(tuning_result, f, ensure_ascii=False, indent=2, default=str)
        
        # 儲存 CSV 詳細結果
        csv_file = results_dir / f"tuning_{stock_id}_{timestamp}.csv"
        
        # 展開參數欄位 - 中文化欄位名稱
        expanded_results = []

        # 中文欄位對照表
        column_mapping = {
            'combination_id': '參數組合編號',
            'stock_id': '股票代碼',
            'model_type': '模型類型',
            'success': '是否成功',
            'error_message': '錯誤訊息',
            'test_score': '測試分數_方向準確率',
            'feature_count': '特徵數量',

            # 測試指標中文化
            'test_mse': '測試_均方誤差',
            'test_rmse': '測試_均方根誤差',
            'test_r2': '測試_R平方',
            'test_direction_accuracy': '測試_方向準確率',
            'test_mean_pred': '測試_預測平均值',
            'test_std_pred': '測試_預測標準差',

            # 訓練指標中文化
            'train_mse': '訓練_均方誤差',
            'train_rmse': '訓練_均方根誤差',
            'train_mae': '訓練_平均絕對誤差',
            'train_r2': '訓練_R平方',
            'train_mean_pred': '訓練_預測平均值',
            'train_std_pred': '訓練_預測標準差',

            # 參數中文化
            'param_max_depth': '參數_最大深度',
            'param_learning_rate': '參數_學習率',
            'param_n_estimators': '參數_樹的數量',
            'param_subsample': '參數_子樣本比例',
            'param_colsample_bytree': '參數_特徵子樣本比例',
            'param_min_samples_split': '參數_最小分割樣本數',
            'param_min_samples_leaf': '參數_最小葉節點樣本數',
        }

        for result in tuning_result['all_results']:
            row = {}

            # 基本資訊
            basic_info = {
                'combination_id': result['combination_id'],
                'stock_id': result['stock_id'],
                'model_type': result['model_type'],
                'success': '成功' if result['success'] else '失敗',
                'error_message': result.get('error_message', ''),
                'test_score': result['test_score'],
                'feature_count': result['feature_count']
            }

            for key, value in basic_info.items():
                chinese_key = column_mapping.get(key, key)
                row[chinese_key] = value

            # 展開參數
            for param_name, param_value in result['parameters'].items():
                param_key = f'param_{param_name}'
                chinese_key = column_mapping.get(param_key, param_key)
                row[chinese_key] = param_value

            # 展開測試指標
            for metric_name, metric_value in result.get('test_metrics', {}).items():
                test_key = f'test_{metric_name}'
                chinese_key = column_mapping.get(test_key, test_key)
                row[chinese_key] = metric_value

            # 展開訓練指標
            for metric_name, metric_value in result.get('train_metrics', {}).items():
                train_key = f'train_{metric_name}'
                chinese_key = column_mapping.get(train_key, train_key)
                row[chinese_key] = metric_value

            expanded_results.append(row)
        
        expanded_df = pd.DataFrame(expanded_results)
        expanded_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        logger.info(f"調優結果已儲存:")
        logger.info(f"  JSON: {json_file}")
        logger.info(f"  CSV:  {csv_file}")

        # 更新已調優股票清單
        self._update_tuned_stocks_registry(tuning_result)

    def update_config_with_best_params(self, tuning_result: Dict[str, Any]) -> bool:
        """將最佳參數更新到配置檔案"""
        if not tuning_result['success']:
            return False

        try:
            import json
            from pathlib import Path

            # 讀取現有配置
            config_file = Path(__file__).parent.parent / 'config' / 'settings.py'

            best_params = tuning_result['best_params']
            model_type = tuning_result['model_type']

            logger.info(f"準備更新 {model_type} 最佳參數到配置檔案: {best_params}")

            # 這裡可以實作配置更新邏輯
            # 為了安全起見，先記錄到日誌，讓使用者手動更新
            logger.info("建議手動更新以下參數到 config/settings.py:")
            logger.info(f"模型: {model_type}")
            for param, value in best_params.items():
                logger.info(f"  {param}: {value}")

            return True

        except Exception as e:
            logger.error(f"更新配置失敗: {e}")
            return False

    def _update_tuned_stocks_registry(self, tuning_result: Dict[str, Any]):
        """更新已調優股票註冊表"""
        try:
            from pathlib import Path
            import pandas as pd

            # 註冊表檔案位置
            registry_dir = Path(self.config['output']['paths']['models']) / 'hyperparameter_tuning'
            registry_file = registry_dir / 'tuned_stocks_registry.csv'

            # 讀取現有註冊表
            if registry_file.exists():
                try:
                    registry_df = pd.read_csv(registry_file, encoding='utf-8-sig')
                except:
                    registry_df = pd.DataFrame()
            else:
                registry_df = pd.DataFrame()

            # 準備新記錄
            new_record = {
                '股票代碼': tuning_result['stock_id'],
                '模型類型': tuning_result['model_type'],
                '最佳分數': tuning_result['best_score'] if tuning_result['success'] else 0,
                '是否成功': '成功' if tuning_result['success'] else '失敗',
                '調優時間': tuning_result['created_at'],
                '最佳參數': str(tuning_result.get('best_params', {})),
                '成功組合數': tuning_result.get('successful_combinations', 0),
                '總組合數': tuning_result.get('total_combinations', 0)
            }

            # 檢查是否已存在相同股票+模型的記錄
            if not registry_df.empty:
                mask = (registry_df.get('股票代碼', '') == tuning_result['stock_id']) & \
                       (registry_df.get('模型類型', '') == tuning_result['model_type'])
                has_existing = mask.any()
            else:
                has_existing = False

            if has_existing:
                # 更新現有記錄
                for col, val in new_record.items():
                    registry_df.loc[mask, col] = val
                logger.info(f"更新已調優股票註冊表: {tuning_result['stock_id']} ({tuning_result['model_type']})")
            else:
                # 新增記錄
                new_df = pd.DataFrame([new_record])
                registry_df = pd.concat([registry_df, new_df], ignore_index=True)
                logger.info(f"新增已調優股票註冊表: {tuning_result['stock_id']} ({tuning_result['model_type']})")

            # 儲存註冊表
            registry_df.to_csv(registry_file, index=False, encoding='utf-8-sig')

        except Exception as e:
            logger.error(f"更新已調優股票註冊表失敗: {e}")

    @classmethod
    def get_tuned_stocks_info(cls) -> pd.DataFrame:
        """獲取已調優股票資訊"""
        try:
            from pathlib import Path
            import pandas as pd

            config = get_config()
            registry_dir = Path(config['output']['paths']['models']) / 'hyperparameter_tuning'
            registry_file = registry_dir / 'tuned_stocks_registry.csv'

            if registry_file.exists():
                return pd.read_csv(registry_file, encoding='utf-8-sig')
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"讀取已調優股票註冊表失敗: {e}")
            return pd.DataFrame()

    @classmethod
    def get_stock_best_params(cls, stock_id: str, model_type: str) -> Dict[str, Any] | None:
        """獲取特定股票的最佳參數"""
        try:
            registry_df = cls.get_tuned_stocks_info()

            if registry_df.empty:
                return None

            # 查找該股票+模型的記錄（處理股票代碼的類型轉換）
            try:
                # 嘗試將股票代碼轉為整數比較
                stock_id_int = int(stock_id)
                mask = (registry_df['股票代碼'] == stock_id_int) & \
                       (registry_df['模型類型'] == model_type) & \
                       (registry_df['是否成功'] == '成功')
            except ValueError:
                # 如果轉換失敗，用字串比較
                mask = (registry_df['股票代碼'].astype(str) == stock_id) & \
                       (registry_df['模型類型'] == model_type) & \
                       (registry_df['是否成功'] == '成功')

            matching_records = registry_df[mask]

            if not matching_records.empty:
                # 如果有多筆記錄，取分數最高的
                best_record = matching_records.loc[matching_records['最佳分數'].idxmax()]
                params_str = best_record['最佳參數']

                # 將字串轉回字典
                try:
                    import ast
                    result = ast.literal_eval(params_str)
                    logger.debug(f"成功獲取 {stock_id} {model_type} 最佳參數: {result}")
                    return result
                except Exception as e:
                    logger.error(f"解析參數字串失敗: {params_str}, 錯誤: {e}")
                    return None

            return None

        except Exception as e:
            logger.error(f"獲取股票 {stock_id} 最佳參數失敗: {e}")
            return None

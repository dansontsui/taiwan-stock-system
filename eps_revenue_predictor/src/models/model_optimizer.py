# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Model Optimizer
AI模型優化器 - 基於回測結果調整模型參數
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

try:
    from lightgbm import LGBMRegressor
    LIGHTGBM_AVAILABLE = True
except ImportError:
    from sklearn.ensemble import GradientBoostingRegressor
    LIGHTGBM_AVAILABLE = False

from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
import joblib

from config.settings import PROJECT_ROOT, AI_MODEL_CONFIG
from src.data.database_manager import DatabaseManager
from src.models.adjustment_model import AIAdjustmentModel
from src.utils.logger import get_logger, log_execution
from src.utils.accuracy_metrics import AccuracyMetrics

logger = get_logger('model_optimizer')

class ModelOptimizer:
    """AI模型優化器
    
    基於回測結果自動調整AI模型參數和權重
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.ai_model = AIAdjustmentModel(self.db_manager)
        self.accuracy_metrics = AccuracyMetrics()
        
        # 優化歷史記錄
        self.optimization_history_path = PROJECT_ROOT / 'models' / 'optimization_history.json'
        self.optimization_history_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("ModelOptimizer initialized")
    
    @log_execution
    def optimize_based_on_backtest(self, stock_id: str, backtest_results: Dict) -> Dict:
        """
        基於回測結果優化模型
        
        Args:
            stock_id: 股票代碼
            backtest_results: 回測結果
            
        Returns:
            優化結果字典
        """
        logger.info(f"Starting model optimization for {stock_id} based on backtest results")
        
        try:
            optimization_result = {
                'stock_id': stock_id,
                'optimization_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'optimizations_applied': [],
                'performance_before': {},
                'performance_after': {},
                'recommendations': []
            }
            
            # 分析回測結果
            analysis = self._analyze_backtest_performance(backtest_results)
            optimization_result['performance_before'] = analysis
            
            # 決定優化策略
            optimization_strategies = self._determine_optimization_strategies(analysis)
            
            # 執行優化
            for strategy in optimization_strategies:
                logger.info(f"Applying optimization strategy: {strategy['type']}")
                
                strategy_result = self._apply_optimization_strategy(
                    stock_id, strategy, backtest_results
                )
                
                optimization_result['optimizations_applied'].append(strategy_result)
            
            # 生成建議
            recommendations = self._generate_optimization_recommendations(analysis)
            optimization_result['recommendations'] = recommendations
            
            # 記錄優化歷史
            self._save_optimization_history(optimization_result)
            
            logger.info(f"Model optimization completed for {stock_id}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Model optimization failed for {stock_id}: {e}")
            return {
                'stock_id': stock_id,
                'error': str(e),
                'optimization_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _analyze_backtest_performance(self, backtest_results: Dict) -> Dict:
        """分析回測表現"""
        try:
            analysis = {
                'revenue_performance': {},
                'eps_performance': {},
                'overall_assessment': {},
                'problem_areas': []
            }
            
            # 營收表現分析
            revenue_results = backtest_results.get('results', {}).get('revenue', {})
            if revenue_results.get('success'):
                revenue_stats = revenue_results.get('statistics', {})
                analysis['revenue_performance'] = {
                    'direction_accuracy': revenue_stats.get('direction_accuracy', 0),
                    'mape': revenue_stats.get('avg_revenue_mape', 0),
                    'rmse': revenue_stats.get('rmse_growth', 0),
                    'periods_tested': revenue_stats.get('total_periods', 0)
                }
                
                # 識別問題
                if revenue_stats.get('direction_accuracy', 0) < 0.6:
                    analysis['problem_areas'].append('revenue_direction_accuracy')
                if revenue_stats.get('avg_revenue_mape', 0) > 15:
                    analysis['problem_areas'].append('revenue_magnitude_error')
            
            # EPS表現分析
            eps_results = backtest_results.get('results', {}).get('eps', {})
            if eps_results.get('success'):
                eps_stats = eps_results.get('statistics', {})
                analysis['eps_performance'] = {
                    'direction_accuracy': eps_stats.get('direction_accuracy', 0),
                    'mape': eps_stats.get('avg_eps_mape', 0),
                    'rmse': eps_stats.get('rmse_growth', 0),
                    'periods_tested': eps_stats.get('total_periods', 0)
                }
                
                # 識別問題
                if eps_stats.get('direction_accuracy', 0) < 0.6:
                    analysis['problem_areas'].append('eps_direction_accuracy')
                if eps_stats.get('avg_eps_mape', 0) > 20:
                    analysis['problem_areas'].append('eps_magnitude_error')
            
            # 整體評估
            overall_stats = backtest_results.get('overall_statistics', {})
            combined_perf = overall_stats.get('combined_performance', {})
            
            if combined_perf:
                analysis['overall_assessment'] = {
                    'combined_direction_accuracy': combined_perf.get('avg_direction_accuracy', 0),
                    'total_predictions': combined_perf.get('total_predictions', 0),
                    'needs_optimization': combined_perf.get('avg_direction_accuracy', 0) < 0.65
                }
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Failed to analyze backtest performance: {e}")
            return {}
    
    def _determine_optimization_strategies(self, analysis: Dict) -> List[Dict]:
        """決定優化策略"""
        strategies = []
        problem_areas = analysis.get('problem_areas', [])
        
        # 方向準確度問題
        if 'revenue_direction_accuracy' in problem_areas or 'eps_direction_accuracy' in problem_areas:
            strategies.append({
                'type': 'retrain_ai_model',
                'priority': 'high',
                'reason': 'Poor directional accuracy',
                'target': 'ai_adjustment_model'
            })
        
        # 幅度誤差問題
        if 'revenue_magnitude_error' in problem_areas or 'eps_magnitude_error' in problem_areas:
            strategies.append({
                'type': 'adjust_formula_weights',
                'priority': 'medium',
                'reason': 'High magnitude errors',
                'target': 'formula_weights'
            })
        
        # 整體表現不佳
        overall_needs_opt = analysis.get('overall_assessment', {}).get('needs_optimization', False)
        if overall_needs_opt:
            strategies.append({
                'type': 'hyperparameter_tuning',
                'priority': 'medium',
                'reason': 'Overall performance below threshold',
                'target': 'ai_model_hyperparameters'
            })
        
        # 如果沒有明顯問題，進行微調
        if not strategies:
            strategies.append({
                'type': 'fine_tuning',
                'priority': 'low',
                'reason': 'Preventive optimization',
                'target': 'model_parameters'
            })
        
        # 按優先級排序
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        strategies.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return strategies
    
    def _apply_optimization_strategy(self, stock_id: str, strategy: Dict, 
                                   backtest_results: Dict) -> Dict:
        """應用優化策略"""
        strategy_type = strategy['type']
        
        try:
            if strategy_type == 'retrain_ai_model':
                return self._retrain_ai_model(stock_id)
            
            elif strategy_type == 'adjust_formula_weights':
                return self._adjust_formula_weights(stock_id, backtest_results)
            
            elif strategy_type == 'hyperparameter_tuning':
                return self._tune_hyperparameters(stock_id)
            
            elif strategy_type == 'fine_tuning':
                return self._fine_tune_model(stock_id)
            
            else:
                return {
                    'strategy': strategy_type,
                    'success': False,
                    'error': 'Unknown strategy type'
                }
                
        except Exception as e:
            logger.error(f"Failed to apply strategy {strategy_type}: {e}")
            return {
                'strategy': strategy_type,
                'success': False,
                'error': str(e)
            }
    
    def _retrain_ai_model(self, stock_id: str) -> Dict:
        """重新訓練AI模型"""
        logger.info(f"Retraining AI model for {stock_id}")
        
        try:
            # 重新訓練通用AI模型
            retrain_result = self.ai_model.train_model(retrain=True)
            
            # 如果可能，訓練股票專用模型
            stock_specific_result = None
            try:
                # 檢查是否有足夠資料訓練專用模型
                data_validation = self.db_manager.validate_backtest_data_availability(stock_id)
                if data_validation.get('backtest_feasible', False):
                    # 這裡可以添加股票專用模型訓練邏輯
                    stock_specific_result = {'status': 'stock_specific_training_available'}
            except Exception as e:
                logger.warning(f"Stock-specific model training failed: {e}")
            
            return {
                'strategy': 'retrain_ai_model',
                'success': retrain_result.get('status') in ['success', 'loaded_existing'],
                'general_model_result': retrain_result,
                'stock_specific_result': stock_specific_result,
                'improvement_expected': 'Better directional accuracy'
            }
            
        except Exception as e:
            logger.error(f"AI model retraining failed: {e}")
            return {
                'strategy': 'retrain_ai_model',
                'success': False,
                'error': str(e)
            }
    
    def _adjust_formula_weights(self, stock_id: str, backtest_results: Dict) -> Dict:
        """調整財務公式權重"""
        logger.info(f"Adjusting formula weights for {stock_id}")
        
        try:
            # 分析各方法的表現
            revenue_results = backtest_results.get('results', {}).get('revenue', {}).get('backtest_results', [])
            eps_results = backtest_results.get('results', {}).get('eps', {}).get('backtest_results', [])
            
            weight_adjustments = {
                'revenue_weights': self._analyze_method_performance(revenue_results, 'revenue'),
                'eps_weights': self._analyze_method_performance(eps_results, 'eps')
            }
            
            # 保存權重調整建議
            adjustment_file = PROJECT_ROOT / 'models' / f'weight_adjustments_{stock_id}.json'
            with open(adjustment_file, 'w', encoding='utf-8') as f:
                json.dump(weight_adjustments, f, ensure_ascii=False, indent=2)
            
            return {
                'strategy': 'adjust_formula_weights',
                'success': True,
                'weight_adjustments': weight_adjustments,
                'adjustment_file': str(adjustment_file),
                'improvement_expected': 'Better magnitude accuracy'
            }
            
        except Exception as e:
            logger.error(f"Formula weight adjustment failed: {e}")
            return {
                'strategy': 'adjust_formula_weights',
                'success': False,
                'error': str(e)
            }
    
    def _tune_hyperparameters(self, stock_id: str) -> Dict:
        """調整超參數"""
        logger.info(f"Tuning hyperparameters for {stock_id}")
        
        try:
            # 定義超參數搜索空間
            if LIGHTGBM_AVAILABLE:
                param_grid = {
                    'n_estimators': [50, 100, 150],
                    'max_depth': [4, 6, 8],
                    'learning_rate': [0.05, 0.1, 0.15],
                    'num_leaves': [20, 31, 40]
                }
                base_model = LGBMRegressor(random_state=42, verbose=-1)
            else:
                param_grid = {
                    'n_estimators': [50, 100, 150],
                    'max_depth': [4, 6, 8],
                    'learning_rate': [0.05, 0.1, 0.15]
                }
                base_model = GradientBoostingRegressor(random_state=42)
            
            # 獲取訓練資料
            training_data = self._prepare_hyperparameter_tuning_data(stock_id)
            
            if training_data is None or len(training_data) < 10:
                return {
                    'strategy': 'hyperparameter_tuning',
                    'success': False,
                    'error': 'Insufficient training data'
                }
            
            X, y = training_data
            
            # 執行網格搜索
            grid_search = GridSearchCV(
                base_model, param_grid, cv=3, scoring='neg_mean_squared_error',
                n_jobs=-1, verbose=0
            )
            
            grid_search.fit(X, y)
            
            # 保存最佳參數
            best_params_file = PROJECT_ROOT / 'models' / f'best_params_{stock_id}.json'
            with open(best_params_file, 'w', encoding='utf-8') as f:
                json.dump(grid_search.best_params_, f, ensure_ascii=False, indent=2)
            
            return {
                'strategy': 'hyperparameter_tuning',
                'success': True,
                'best_params': grid_search.best_params_,
                'best_score': grid_search.best_score_,
                'params_file': str(best_params_file),
                'improvement_expected': 'Better overall performance'
            }
            
        except Exception as e:
            logger.error(f"Hyperparameter tuning failed: {e}")
            return {
                'strategy': 'hyperparameter_tuning',
                'success': False,
                'error': str(e)
            }
    
    def _fine_tune_model(self, stock_id: str) -> Dict:
        """微調模型"""
        logger.info(f"Fine-tuning model for {stock_id}")
        
        try:
            # 微調策略：調整AI調整範圍
            current_range = AI_MODEL_CONFIG.get('adjustment_range', 0.2)
            
            # 基於歷史表現調整範圍
            adjustment_suggestions = {
                'current_adjustment_range': current_range,
                'suggested_range': min(0.25, current_range * 1.1),  # 略微增加調整範圍
                'confidence_threshold_adjustment': 0.05,  # 調整信心閾值
                'feature_importance_rebalancing': True
            }
            
            return {
                'strategy': 'fine_tuning',
                'success': True,
                'adjustments': adjustment_suggestions,
                'improvement_expected': 'Marginal performance improvement'
            }
            
        except Exception as e:
            logger.error(f"Model fine-tuning failed: {e}")
            return {
                'strategy': 'fine_tuning',
                'success': False,
                'error': str(e)
            }

    def _analyze_method_performance(self, backtest_results: List[Dict],
                                  prediction_type: str) -> Dict:
        """分析各預測方法的表現"""
        try:
            method_performance = {}

            for result in backtest_results:
                prediction = result.get('prediction', {})
                method_breakdown = prediction.get('method_breakdown', {})
                accuracy = result.get('accuracy', {})

                # 分析各方法的貢獻
                for method_name, method_result in method_breakdown.items():
                    if method_name not in method_performance:
                        method_performance[method_name] = {
                            'errors': [],
                            'contributions': []
                        }

                    # 記錄誤差和貢獻
                    if prediction_type == 'revenue':
                        error = accuracy.get('revenue_mape', 0)
                    else:
                        error = accuracy.get('eps_mape', 0)

                    method_performance[method_name]['errors'].append(error)
                    method_performance[method_name]['contributions'].append(
                        method_result.get('growth', 0)
                    )

            # 計算各方法的平均表現
            method_scores = {}
            for method_name, data in method_performance.items():
                if data['errors']:
                    avg_error = np.mean(data['errors'])
                    error_std = np.std(data['errors'])

                    # 計算方法分數 (誤差越低分數越高)
                    score = max(0, 1 - (avg_error / 100))  # 將MAPE轉換為分數

                    method_scores[method_name] = {
                        'score': score,
                        'avg_error': avg_error,
                        'error_std': error_std,
                        'suggested_weight_adjustment': self._calculate_weight_adjustment(score)
                    }

            return method_scores

        except Exception as e:
            logger.warning(f"Failed to analyze method performance: {e}")
            return {}

    def _calculate_weight_adjustment(self, score: float) -> float:
        """計算權重調整建議"""
        # 基於分數調整權重
        if score > 0.8:
            return 1.1  # 增加10%權重
        elif score > 0.6:
            return 1.0  # 維持權重
        elif score > 0.4:
            return 0.9  # 減少10%權重
        else:
            return 0.8  # 減少20%權重

    def _prepare_hyperparameter_tuning_data(self, stock_id: str) -> Optional[Tuple]:
        """準備超參數調整的訓練資料"""
        try:
            # 獲取股票的歷史資料
            comprehensive_data = self.db_manager.get_comprehensive_data(stock_id)

            if comprehensive_data['data_quality']['overall_score'] < 0.5:
                return None

            # 提取特徵 (使用AI模型的特徵提取方法)
            features = self.ai_model._extract_features(stock_id)
            if features is None:
                return None

            # 計算歷史預測誤差作為目標變數
            target = self.ai_model._calculate_historical_error(comprehensive_data)
            if target is None:
                return None

            # 創建訓練資料
            X = np.array([features])
            y = np.array([target])

            return X, y

        except Exception as e:
            logger.warning(f"Failed to prepare hyperparameter tuning data: {e}")
            return None

    def _generate_optimization_recommendations(self, analysis: Dict) -> List[str]:
        """生成優化建議"""
        recommendations = []

        try:
            problem_areas = analysis.get('problem_areas', [])
            revenue_perf = analysis.get('revenue_performance', {})
            eps_perf = analysis.get('eps_performance', {})

            # 基於問題區域生成建議
            if 'revenue_direction_accuracy' in problem_areas:
                recommendations.append(
                    f"營收方向預測準確度偏低 ({revenue_perf.get('direction_accuracy', 0):.1%})，"
                    "建議重新訓練AI模型或增加更多歷史資料"
                )

            if 'eps_direction_accuracy' in problem_areas:
                recommendations.append(
                    f"EPS方向預測準確度偏低 ({eps_perf.get('direction_accuracy', 0):.1%})，"
                    "建議檢查EPS預測方法的權重配置"
                )

            if 'revenue_magnitude_error' in problem_areas:
                recommendations.append(
                    f"營收幅度誤差較大 (MAPE: {revenue_perf.get('mape', 0):.1f}%)，"
                    "建議調整財務公式的權重分配"
                )

            if 'eps_magnitude_error' in problem_areas:
                recommendations.append(
                    f"EPS幅度誤差較大 (MAPE: {eps_perf.get('mape', 0):.1f}%)，"
                    "建議優化利潤率分析方法"
                )

            # 整體建議
            overall_assessment = analysis.get('overall_assessment', {})
            if overall_assessment.get('needs_optimization', False):
                recommendations.append(
                    "整體預測表現需要改善，建議考慮訓練股票專用AI模型"
                )

            # 資料品質建議
            revenue_periods = revenue_perf.get('periods_tested', 0)
            eps_periods = eps_perf.get('periods_tested', 0)

            if revenue_periods < 6:
                recommendations.append("營收回測期數不足，建議增加更多歷史資料以提高模型穩定性")

            if eps_periods < 4:
                recommendations.append("EPS回測期數不足，建議增加更多季度財務資料")

            if not recommendations:
                recommendations.append("模型表現良好，建議持續監控並定期進行回測驗證")

            return recommendations

        except Exception as e:
            logger.warning(f"Failed to generate optimization recommendations: {e}")
            return ["無法生成優化建議，請檢查分析結果"]

    def _save_optimization_history(self, optimization_result: Dict) -> None:
        """保存優化歷史"""
        try:
            # 讀取現有歷史
            history = []
            if self.optimization_history_path.exists():
                with open(self.optimization_history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)

            # 添加新記錄
            history.append(optimization_result)

            # 保持最近100條記錄
            if len(history) > 100:
                history = history[-100:]

            # 保存更新的歷史
            with open(self.optimization_history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

            logger.info(f"Optimization history saved for {optimization_result.get('stock_id')}")

        except Exception as e:
            logger.warning(f"Failed to save optimization history: {e}")

    def get_optimization_history(self, stock_id: str = None) -> List[Dict]:
        """獲取優化歷史"""
        try:
            if not self.optimization_history_path.exists():
                return []

            with open(self.optimization_history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)

            if stock_id:
                # 過濾特定股票的歷史
                history = [h for h in history if h.get('stock_id') == stock_id]

            return history

        except Exception as e:
            logger.warning(f"Failed to get optimization history: {e}")
            return []

    def display_optimization_summary(self, optimization_result: Dict) -> None:
        """顯示優化摘要"""
        try:
            stock_id = optimization_result.get('stock_id', 'Unknown')
            optimization_time = optimization_result.get('optimization_time', 'Unknown')

            print(f"\n{'='*60}")
            print(f"🔧 {stock_id} AI模型優化結果")
            print(f"{'='*60}")
            print(f"⏰ 優化時間: {optimization_time}")

            # 顯示應用的優化策略
            optimizations = optimization_result.get('optimizations_applied', [])
            if optimizations:
                print(f"\n🎯 已應用的優化策略:")
                for i, opt in enumerate(optimizations, 1):
                    strategy = opt.get('strategy', 'Unknown')
                    success = opt.get('success', False)
                    status = "✅ 成功" if success else "❌ 失敗"
                    print(f"   {i}. {strategy}: {status}")

                    if success and 'improvement_expected' in opt:
                        print(f"      預期改善: {opt['improvement_expected']}")
                    elif not success and 'error' in opt:
                        print(f"      錯誤: {opt['error']}")

            # 顯示建議
            recommendations = optimization_result.get('recommendations', [])
            if recommendations:
                print(f"\n💡 優化建議:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec}")

            print(f"\n{'='*60}")

        except Exception as e:
            logger.error(f"Failed to display optimization summary: {e}")
            print(f"❌ 無法顯示優化摘要: {e}")

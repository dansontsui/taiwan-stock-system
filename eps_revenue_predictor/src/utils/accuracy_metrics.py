# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Accuracy Metrics
準確度評估指標模組
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from src.utils.logger import get_logger

logger = get_logger('accuracy_metrics')

class AccuracyMetrics:
    """準確度評估指標計算器"""
    
    def __init__(self):
        logger.info("AccuracyMetrics initialized")
    
    def calculate_comprehensive_metrics(self, predictions: List[float], 
                                      actuals: List[float],
                                      prediction_type: str = 'growth_rate') -> Dict:
        """
        計算全面的準確度指標
        
        Args:
            predictions: 預測值列表
            actuals: 實際值列表
            prediction_type: 預測類型 ('growth_rate', 'absolute_value')
            
        Returns:
            包含各種準確度指標的字典
        """
        try:
            if len(predictions) != len(actuals) or len(predictions) == 0:
                return {'error': 'Invalid input data'}
            
            predictions = np.array(predictions)
            actuals = np.array(actuals)
            
            metrics = {}
            
            # 基本誤差指標
            metrics.update(self._calculate_basic_errors(predictions, actuals))
            
            # 百分比誤差指標
            metrics.update(self._calculate_percentage_errors(predictions, actuals))
            
            # 方向準確度
            metrics.update(self._calculate_directional_accuracy(predictions, actuals))
            
            # 統計指標
            metrics.update(self._calculate_statistical_metrics(predictions, actuals))
            
            # 分佈分析
            metrics.update(self._calculate_distribution_metrics(predictions, actuals))
            
            # 預測類型特定指標
            if prediction_type == 'growth_rate':
                metrics.update(self._calculate_growth_rate_metrics(predictions, actuals))
            
            logger.info(f"Calculated comprehensive metrics for {len(predictions)} predictions")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate comprehensive metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_basic_errors(self, predictions: np.ndarray, actuals: np.ndarray) -> Dict:
        """計算基本誤差指標"""
        errors = predictions - actuals
        abs_errors = np.abs(errors)
        
        return {
            'mae': np.mean(abs_errors),  # Mean Absolute Error
            'mse': np.mean(errors ** 2),  # Mean Squared Error
            'rmse': np.sqrt(np.mean(errors ** 2)),  # Root Mean Squared Error
            'mean_error': np.mean(errors),  # Mean Error (bias)
            'std_error': np.std(errors),  # Standard Deviation of Errors
            'max_error': np.max(abs_errors),  # Maximum Absolute Error
            'min_error': np.min(abs_errors)   # Minimum Absolute Error
        }
    
    def _calculate_percentage_errors(self, predictions: np.ndarray, actuals: np.ndarray) -> Dict:
        """計算百分比誤差指標"""
        # 避免除零錯誤
        actuals_safe = np.where(np.abs(actuals) < 1e-8, 1e-8, actuals)
        
        percentage_errors = np.abs((predictions - actuals) / actuals_safe) * 100
        
        return {
            'mape': np.mean(percentage_errors),  # Mean Absolute Percentage Error
            'median_ape': np.median(percentage_errors),  # Median Absolute Percentage Error
            'mape_std': np.std(percentage_errors),  # Standard Deviation of APE
            'mape_95th': np.percentile(percentage_errors, 95),  # 95th percentile APE
            'mape_75th': np.percentile(percentage_errors, 75),  # 75th percentile APE
            'mape_25th': np.percentile(percentage_errors, 25)   # 25th percentile APE
        }
    
    def _calculate_directional_accuracy(self, predictions: np.ndarray, actuals: np.ndarray) -> Dict:
        """計算方向準確度"""
        # 計算變化方向
        pred_directions = np.sign(predictions)
        actual_directions = np.sign(actuals)
        
        # 方向一致性
        direction_matches = (pred_directions == actual_directions)
        direction_accuracy = np.mean(direction_matches)
        
        # 分別計算正向和負向的準確度
        positive_mask = actual_directions > 0
        negative_mask = actual_directions < 0
        zero_mask = actual_directions == 0
        
        positive_accuracy = (
            np.mean(direction_matches[positive_mask]) 
            if np.any(positive_mask) else 0
        )
        
        negative_accuracy = (
            np.mean(direction_matches[negative_mask]) 
            if np.any(negative_mask) else 0
        )
        
        return {
            'direction_accuracy': direction_accuracy,
            'positive_direction_accuracy': positive_accuracy,
            'negative_direction_accuracy': negative_accuracy,
            'positive_predictions': np.sum(positive_mask),
            'negative_predictions': np.sum(negative_mask),
            'zero_predictions': np.sum(zero_mask)
        }
    
    def _calculate_statistical_metrics(self, predictions: np.ndarray, actuals: np.ndarray) -> Dict:
        """計算統計指標"""
        try:
            # 相關係數
            correlation, p_value = stats.pearsonr(predictions, actuals)
            
            # R-squared
            ss_res = np.sum((actuals - predictions) ** 2)
            ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
            r_squared = 1 - (ss_res / (ss_tot + 1e-8))
            
            # Theil's U統計量
            theil_u = self._calculate_theil_u(predictions, actuals)
            
            return {
                'correlation': correlation,
                'correlation_p_value': p_value,
                'r_squared': r_squared,
                'theil_u': theil_u,
                'prediction_variance': np.var(predictions),
                'actual_variance': np.var(actuals),
                'variance_ratio': np.var(predictions) / (np.var(actuals) + 1e-8)
            }
            
        except Exception as e:
            logger.warning(f"Failed to calculate some statistical metrics: {e}")
            return {
                'correlation': 0,
                'r_squared': 0,
                'theil_u': 1
            }
    
    def _calculate_distribution_metrics(self, predictions: np.ndarray, actuals: np.ndarray) -> Dict:
        """計算分佈指標"""
        errors = predictions - actuals
        
        # 偏度和峰度
        error_skewness = stats.skew(errors)
        error_kurtosis = stats.kurtosis(errors)
        
        # 正態性檢驗
        try:
            shapiro_stat, shapiro_p = stats.shapiro(errors)
        except:
            shapiro_stat, shapiro_p = 0, 1
        
        return {
            'error_skewness': error_skewness,
            'error_kurtosis': error_kurtosis,
            'shapiro_statistic': shapiro_stat,
            'shapiro_p_value': shapiro_p,
            'errors_normal_distributed': shapiro_p > 0.05
        }
    
    def _calculate_growth_rate_metrics(self, predictions: np.ndarray, actuals: np.ndarray) -> Dict:
        """計算成長率特定指標"""
        # 成長率範圍分析
        high_growth_mask = np.abs(actuals) > 0.1  # 10%以上成長率
        medium_growth_mask = (np.abs(actuals) > 0.05) & (np.abs(actuals) <= 0.1)
        low_growth_mask = np.abs(actuals) <= 0.05
        
        metrics = {}
        
        for mask, label in [(high_growth_mask, 'high'), 
                           (medium_growth_mask, 'medium'), 
                           (low_growth_mask, 'low')]:
            if np.any(mask):
                subset_pred = predictions[mask]
                subset_actual = actuals[mask]
                subset_errors = np.abs(subset_pred - subset_actual)
                
                metrics[f'{label}_growth_mape'] = np.mean(
                    subset_errors / (np.abs(subset_actual) + 1e-8) * 100
                )
                metrics[f'{label}_growth_count'] = np.sum(mask)
                metrics[f'{label}_growth_direction_acc'] = np.mean(
                    np.sign(subset_pred) == np.sign(subset_actual)
                )
        
        return metrics
    
    def _calculate_theil_u(self, predictions: np.ndarray, actuals: np.ndarray) -> float:
        """計算Theil's U統計量"""
        try:
            # Theil's U = sqrt(MSE) / sqrt(mean(actual^2))
            mse = np.mean((predictions - actuals) ** 2)
            mean_actual_squared = np.mean(actuals ** 2)
            
            if mean_actual_squared == 0:
                return 1.0
            
            theil_u = np.sqrt(mse) / np.sqrt(mean_actual_squared)
            return theil_u
            
        except:
            return 1.0
    
    def calculate_confidence_calibration(self, predictions: List[Dict], 
                                       actuals: List[float]) -> Dict:
        """
        計算信心水準校準度
        
        Args:
            predictions: 包含預測值和信心水準的字典列表
            actuals: 實際值列表
            
        Returns:
            信心水準校準結果
        """
        try:
            confidence_groups = {'High': [], 'Medium': [], 'Low': []}
            
            for pred_dict, actual in zip(predictions, actuals):
                confidence = pred_dict.get('confidence', 'Unknown')
                pred_value = pred_dict.get('value', 0)
                
                if confidence in confidence_groups:
                    error = abs(pred_value - actual)
                    confidence_groups[confidence].append(error)
            
            calibration_results = {}
            
            for conf_level, errors in confidence_groups.items():
                if errors:
                    calibration_results[conf_level] = {
                        'count': len(errors),
                        'mean_error': np.mean(errors),
                        'std_error': np.std(errors),
                        'median_error': np.median(errors)
                    }
            
            # 計算校準分數 (高信心應該有低誤差)
            calibration_score = self._calculate_calibration_score(calibration_results)
            calibration_results['calibration_score'] = calibration_score
            
            return calibration_results
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence calibration: {e}")
            return {'error': str(e)}
    
    def _calculate_calibration_score(self, calibration_results: Dict) -> float:
        """計算校準分數 (0-1，1為完美校準)"""
        try:
            high_error = calibration_results.get('High', {}).get('mean_error', float('inf'))
            medium_error = calibration_results.get('Medium', {}).get('mean_error', float('inf'))
            low_error = calibration_results.get('Low', {}).get('mean_error', float('inf'))
            
            # 理想情況：High < Medium < Low (誤差)
            if high_error <= medium_error <= low_error:
                # 計算相對改善程度
                if low_error > 0:
                    score = 1 - (high_error / low_error)
                    return max(0, min(1, score))
            
            return 0.5  # 中等校準
            
        except:
            return 0.0
    
    def generate_accuracy_summary(self, metrics: Dict) -> str:
        """生成準確度摘要報告"""
        try:
            summary_lines = []
            
            # 基本指標
            mape = metrics.get('mape', 0)
            direction_acc = metrics.get('direction_accuracy', 0)
            correlation = metrics.get('correlation', 0)
            
            summary_lines.append(f"📊 準確度摘要:")
            summary_lines.append(f"   MAPE: {mape:.1f}%")
            summary_lines.append(f"   方向準確度: {direction_acc:.1%}")
            summary_lines.append(f"   相關係數: {correlation:.3f}")
            
            # 評級
            if mape < 10 and direction_acc > 0.8:
                grade = "A (優秀)"
            elif mape < 15 and direction_acc > 0.7:
                grade = "B (良好)"
            elif mape < 20 and direction_acc > 0.6:
                grade = "C (中等)"
            elif mape < 30 and direction_acc > 0.5:
                grade = "D (需改善)"
            else:
                grade = "F (不及格)"
            
            summary_lines.append(f"   整體評級: {grade}")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            logger.error(f"Failed to generate accuracy summary: {e}")
            return "❌ 無法生成準確度摘要"

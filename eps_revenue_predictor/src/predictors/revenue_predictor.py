# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Revenue Growth Predictor
營收成長預測器
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from config.settings import PREDICTION_CONFIG, FORMULA_CONFIG
from config.formulas import FinancialFormulas
from src.data.database_manager import DatabaseManager
from src.utils.logger import get_logger, log_execution

logger = get_logger('revenue_predictor')

class RevenuePredictor:
    """營收成長預測器"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.formulas = FinancialFormulas()
        self.config = PREDICTION_CONFIG
        self.formula_config = FORMULA_CONFIG
        
        logger.info("RevenuePredictor initialized")
    
    @log_execution
    def predict_monthly_growth(self, stock_id: str, target_month: str = None) -> Dict:
        """
        預測月營收成長率
        
        Args:
            stock_id: 股票代碼
            target_month: 目標月份 (YYYY-MM)，None表示下個月
            
        Returns:
            預測結果字典
        """
        logger.log_prediction_start(stock_id, 'monthly_revenue_growth')
        
        try:
            # 獲取歷史月營收資料
            monthly_data = self.db_manager.get_monthly_revenue(
                stock_id, self.config['revenue_lookback_months']
            )
            
            if monthly_data.empty:
                return self._create_error_result("No monthly revenue data available")
            
            # 資料品質檢查
            quality_check = self._validate_revenue_data(monthly_data)
            if not quality_check['is_valid']:
                return self._create_error_result(quality_check['reason'])
            
            # 確定目標月份
            if target_month is None:
                latest_date = monthly_data['date'].max()
                target_date = latest_date + pd.DateOffset(months=1)
                target_month = target_date.strftime('%Y-%m')
            
            # 執行預測
            prediction_result = self._execute_revenue_prediction(monthly_data, target_month)
            
            # 添加額外資訊
            prediction_result.update({
                'stock_id': stock_id,
                'target_month': target_month,
                'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_quality': quality_check,
                'historical_data_points': len(monthly_data)
            })
            
            logger.log_prediction_result(
                stock_id, 'monthly_revenue_growth', 
                prediction_result, prediction_result['confidence']
            )
            
            return prediction_result
            
        except Exception as e:
            error_msg = f"Revenue prediction failed: {str(e)}"
            logger.error(error_msg, stock_id=stock_id)
            return self._create_error_result(error_msg)

    def predict_monthly_growth_historical(self, stock_id: str, target_month: str,
                                        max_date: datetime = None) -> Dict:
        """
        歷史時間點營收預測 (用於回測)

        Args:
            stock_id: 股票代碼
            target_month: 目標月份 (YYYY-MM)
            max_date: 最大資料日期限制 (用於回測)
        """
        logger.info(f"[HISTORICAL_PREDICTION] Starting historical revenue prediction | "
                   f"stock_id={stock_id} | target_month={target_month} | max_date={max_date}")

        try:
            # 🔧 獲取限制時間範圍的歷史資料
            monthly_data = self.db_manager.get_monthly_revenue_historical(
                stock_id, max_date=max_date
            )

            if monthly_data.empty or len(monthly_data) < 6:
                return self._create_error_result(
                    f"Insufficient historical data for backtest (got {len(monthly_data)} records)",
                    extra_info={
                        'training_data_range': {
                            'start_date': None,
                            'end_date': max_date.strftime('%Y-%m-%d') if max_date else None,
                            'data_points': len(monthly_data) if not monthly_data.empty else 0
                        },
                        'model_retrained': False,
                        'backtest_mode': True
                    }
                )

            # 🤖 重新訓練專用AI模型 (基於歷史資料)
            model_retrained = False
            if hasattr(self, 'ai_adjustment') and self.ai_adjustment:
                try:
                    # 使用歷史資料重新訓練專用模型
                    self.ai_adjustment.train_stock_specific_model(
                        stock_id, max_date=max_date
                    )
                    model_retrained = True
                    logger.info(f"[AI_RETRAIN] Stock-specific model retrained for {stock_id} | max_date={max_date}")
                except Exception as e:
                    logger.warning(f"AI model retraining failed: {e}")

            # 資料品質檢查
            quality_check = self._validate_revenue_data(monthly_data)
            if not quality_check['is_valid']:
                return self._create_error_result(quality_check['reason'])

            # 執行預測 (使用限制範圍的資料)
            prediction_result = self._execute_revenue_prediction(monthly_data, target_month)

            # 添加回測特有資訊
            prediction_result.update({
                'stock_id': stock_id,
                'target_month': target_month,
                'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_quality': quality_check,
                'historical_data_points': len(monthly_data),
                'training_data_range': {
                    'start_date': monthly_data['date'].min().strftime('%Y-%m-%d'),
                    'end_date': monthly_data['date'].max().strftime('%Y-%m-%d'),
                    'data_points': len(monthly_data)
                },
                'model_retrained': model_retrained,
                'backtest_mode': True
            })

            logger.info(f"[HISTORICAL_PREDICTION] Historical revenue prediction completed | "
                       f"predicted_revenue={prediction_result.get('predicted_revenue', 0)/1e8:.1f}億 | "
                       f"growth_rate={prediction_result.get('growth_rate', 0)*100:.1f}% | "
                       f"data_range={monthly_data['date'].min().strftime('%Y-%m')}~{monthly_data['date'].max().strftime('%Y-%m')}")

            return prediction_result

        except Exception as e:
            error_msg = f"Historical revenue prediction failed: {str(e)}"
            logger.error(error_msg, stock_id=stock_id)
            return self._create_error_result(
                error_msg,
                extra_info={
                    'training_data_range': {
                        'start_date': None,
                        'end_date': max_date.strftime('%Y-%m-%d') if max_date else None,
                        'data_points': 0
                    },
                    'model_retrained': False,
                    'backtest_mode': True
                }
            )

    def _execute_revenue_prediction(self, monthly_data: pd.DataFrame, target_month: str) -> Dict:
        """執行營收預測計算"""
        
        # 方法1: 趨勢外推法
        trend_result = self._predict_by_trend(monthly_data)
        
        # 方法2: 移動平均法
        ma_result = self._predict_by_moving_average(monthly_data)
        
        # 方法3: 年增率趨勢法
        yoy_result = self._predict_by_yoy_trend(monthly_data)
        
        # 季節調整
        target_month_num = int(target_month.split('-')[1])
        seasonal_factor = self.formulas.calculate_seasonal_factor(monthly_data, target_month_num)
        
        # 加權平均
        weights = self.formula_config['revenue_methods']
        
        final_growth = (
            trend_result['growth'] * weights['trend_extrapolation'] +
            ma_result['growth'] * weights['moving_average'] +
            yoy_result['growth'] * weights['yoy_trend']
        )
        
        # 應用季節調整
        adjusted_growth = final_growth * seasonal_factor
        
        # 計算預測營收金額
        latest_revenue = monthly_data['revenue'].iloc[-1]
        predicted_revenue = latest_revenue * (1 + adjusted_growth)
        
        # 計算信心水準
        confidence = self._calculate_confidence([
            trend_result['growth'], ma_result['growth'], yoy_result['growth']
        ])
        
        # 風險因子分析
        risk_factors = self._analyze_risk_factors(monthly_data)
        
        return {
            'predicted_revenue': predicted_revenue,
            'growth_rate': adjusted_growth,
            'growth_rate_before_seasonal': final_growth,
            'seasonal_factor': seasonal_factor,
            'confidence': confidence,
            'method_breakdown': {
                'trend_extrapolation': trend_result,
                'moving_average': ma_result,
                'yoy_trend': yoy_result
            },
            'weights_used': weights,
            'risk_factors': risk_factors,
            'latest_revenue': latest_revenue
        }
    
    def _predict_by_trend(self, monthly_data: pd.DataFrame) -> Dict:
        """趨勢外推法預測"""
        if len(monthly_data) < 6:
            return {'growth': 0.0, 'confidence': 'Low', 'method': 'trend_extrapolation'}
        
        # 使用最近12個月計算趨勢
        recent_data = monthly_data.tail(12)
        trend_growth = self.formulas.calculate_revenue_trend(recent_data, method='linear')
        
        # 趨勢穩定性評估
        if len(recent_data) >= 6:
            first_half = recent_data.head(6)
            second_half = recent_data.tail(6)
            trend1 = self.formulas.calculate_revenue_trend(first_half)
            trend2 = self.formulas.calculate_revenue_trend(second_half)
            stability = 1 - abs(trend1 - trend2) / (abs(trend1) + abs(trend2) + 0.01)
        else:
            stability = 0.5
        
        confidence = 'High' if stability > 0.7 else 'Medium' if stability > 0.4 else 'Low'
        
        return {
            'growth': trend_growth,
            'confidence': confidence,
            'method': 'trend_extrapolation',
            'stability_score': stability
        }
    
    def _predict_by_moving_average(self, monthly_data: pd.DataFrame) -> Dict:
        """移動平均法預測"""
        if len(monthly_data) < 6:
            return {'growth': 0.0, 'confidence': 'Low', 'method': 'moving_average'}
        
        # 計算不同期間的移動平均
        ma_3 = monthly_data['revenue'].tail(3).mean()
        ma_6 = monthly_data['revenue'].tail(6).mean()
        ma_12 = monthly_data['revenue'].tail(min(12, len(monthly_data))).mean()
        
        # 動量計算
        momentum_3_6 = (ma_3 - ma_6) / ma_6 if ma_6 > 0 else 0
        momentum_6_12 = (ma_6 - ma_12) / ma_12 if ma_12 > 0 else 0
        
        # 綜合動量
        combined_momentum = (momentum_3_6 * 0.6 + momentum_6_12 * 0.4)
        
        # 信心水準基於動量一致性
        momentum_consistency = 1 - abs(momentum_3_6 - momentum_6_12) / (abs(momentum_3_6) + abs(momentum_6_12) + 0.01)
        confidence = 'High' if momentum_consistency > 0.7 else 'Medium' if momentum_consistency > 0.4 else 'Low'
        
        return {
            'growth': combined_momentum,
            'confidence': confidence,
            'method': 'moving_average',
            'ma_3': ma_3,
            'ma_6': ma_6,
            'ma_12': ma_12,
            'momentum_consistency': momentum_consistency
        }
    
    def _predict_by_yoy_trend(self, monthly_data: pd.DataFrame) -> Dict:
        """年增率趨勢法預測"""
        if 'revenue_growth_yoy' not in monthly_data.columns:
            return {'growth': 0.0, 'confidence': 'Low', 'method': 'yoy_trend'}
        
        yoy_data = monthly_data['revenue_growth_yoy'].dropna()
        if len(yoy_data) < 3:
            return {'growth': 0.0, 'confidence': 'Low', 'method': 'yoy_trend'}
        
        # 計算年增率趨勢
        yoy_trend = self.formulas.calculate_yoy_trend(monthly_data)
        
        # 最近年增率
        latest_yoy = yoy_data.iloc[-1] / 100  # 轉換為小數
        
        # 預測下個月的年增率
        predicted_yoy = latest_yoy + yoy_trend
        
        # 轉換為月增率 (簡化假設)
        monthly_growth = predicted_yoy / 12
        
        # 年增率穩定性評估
        yoy_volatility = yoy_data.std() / (abs(yoy_data.mean()) + 1)
        confidence = 'High' if yoy_volatility < 0.3 else 'Medium' if yoy_volatility < 0.6 else 'Low'
        
        return {
            'growth': monthly_growth,
            'confidence': confidence,
            'method': 'yoy_trend',
            'latest_yoy': latest_yoy,
            'predicted_yoy': predicted_yoy,
            'yoy_volatility': yoy_volatility
        }
    
    def _calculate_confidence(self, growth_rates: list) -> str:
        """計算整體信心水準"""
        if not growth_rates or len(growth_rates) < 2:
            return 'Low'
        
        # 計算各方法的一致性
        std_dev = np.std(growth_rates)
        mean_abs = np.mean([abs(rate) for rate in growth_rates])
        
        # 相對標準差
        relative_std = std_dev / (mean_abs + 0.01)
        
        if relative_std < 0.3:
            return 'High'
        elif relative_std < 0.6:
            return 'Medium'
        else:
            return 'Low'
    
    def _analyze_risk_factors(self, monthly_data: pd.DataFrame) -> list:
        """分析風險因子"""
        risk_factors = []
        
        # 營收波動性風險
        revenue_volatility = monthly_data['revenue'].std() / monthly_data['revenue'].mean()
        if revenue_volatility > 0.3:
            risk_factors.append(f"High revenue volatility ({revenue_volatility:.2%})")
        
        # 趨勢不穩定風險
        if len(monthly_data) >= 12:
            first_half = monthly_data.head(6)
            second_half = monthly_data.tail(6)
            trend1 = self.formulas.calculate_revenue_trend(first_half)
            trend2 = self.formulas.calculate_revenue_trend(second_half)
            
            if abs(trend1 - trend2) > 0.1:  # 10%差異
                risk_factors.append("Unstable revenue trend")
        
        # 資料不足風險
        if len(monthly_data) < 12:
            risk_factors.append(f"Limited historical data ({len(monthly_data)} months)")
        
        # 年增率異常風險
        if 'revenue_growth_yoy' in monthly_data.columns:
            yoy_data = monthly_data['revenue_growth_yoy'].dropna()
            if not yoy_data.empty:
                latest_yoy = yoy_data.iloc[-1]
                if abs(latest_yoy) > 50:  # 年增率超過50%
                    risk_factors.append(f"Extreme YoY growth ({latest_yoy:.1f}%)")
        
        return risk_factors
    
    def _validate_revenue_data(self, monthly_data: pd.DataFrame) -> Dict:
        """驗證營收資料品質"""
        if monthly_data.empty:
            return {'is_valid': False, 'reason': 'No data available'}
        
        if len(monthly_data) < 3:
            return {'is_valid': False, 'reason': 'Insufficient data (less than 3 months)'}
        
        # 檢查是否有異常值
        revenue_values = monthly_data['revenue'].dropna()
        if revenue_values.empty:
            return {'is_valid': False, 'reason': 'No valid revenue values'}
        
        # 檢查是否有負值
        if (revenue_values < 0).any():
            return {'is_valid': False, 'reason': 'Negative revenue values found'}
        
        # 檢查是否有極端異常值
        q1, q3 = revenue_values.quantile([0.25, 0.75])
        iqr = q3 - q1
        outliers = revenue_values[(revenue_values < q1 - 3*iqr) | (revenue_values > q3 + 3*iqr)]
        
        outlier_ratio = len(outliers) / len(revenue_values)
        if outlier_ratio > 0.3:
            return {'is_valid': False, 'reason': f'Too many outliers ({outlier_ratio:.1%})'}
        
        return {
            'is_valid': True,
            'data_points': len(monthly_data),
            'outlier_ratio': outlier_ratio,
            'latest_date': monthly_data['date'].max().strftime('%Y-%m-%d')
        }
    
    def _create_error_result(self, error_message: str, extra_info: Dict = None) -> Dict:
        """創建錯誤結果"""
        result = {
            'predicted_revenue': None,
            'growth_rate': None,
            'confidence': 'Low',
            'error': error_message,
            'success': False
        }

        # 添加額外資訊
        if extra_info:
            result.update(extra_info)

        return result

if __name__ == "__main__":
    # 測試營收預測器
    predictor = RevenuePredictor()
    
    # 測試2385群光電子
    test_stock = "2385"
    print(f"Testing RevenuePredictor with stock {test_stock}")
    
    result = predictor.predict_monthly_growth(test_stock)
    
    if result.get('success', True):  # 沒有error就是成功
        print(f"✅ Prediction successful")
        print(f"📈 Predicted Growth: {result['growth_rate']:.2%}")
        print(f"💰 Predicted Revenue: {result['predicted_revenue']:,.0f} thousand TWD")
        print(f"🎯 Confidence: {result['confidence']}")
        print(f"📊 Risk Factors: {len(result['risk_factors'])}")
    else:
        print(f"❌ Prediction failed: {result['error']}")

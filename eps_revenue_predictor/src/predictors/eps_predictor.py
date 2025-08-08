# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - EPS Growth Predictor
EPS成長預測器
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import warnings
import sys
import os
from pathlib import Path

warnings.filterwarnings('ignore')

# 添加專案路徑
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from config.settings import PREDICTION_CONFIG, FORMULA_CONFIG
from config.formulas import FinancialFormulas
from src.data.database_manager import DatabaseManager
from src.models.adjustment_model import AIAdjustmentModel
from src.utils.logger import get_logger, log_execution

logger = get_logger('eps_predictor')

class EPSPredictor:
    """EPS成長預測器"""
    
    def __init__(self, db_manager: DatabaseManager = None, ai_model: AIAdjustmentModel = None):
        self.db_manager = db_manager or DatabaseManager()
        self.ai_model = ai_model or AIAdjustmentModel(self.db_manager)
        self.formulas = FinancialFormulas()
        self.config = PREDICTION_CONFIG
        self.formula_config = FORMULA_CONFIG

        logger.info("EPSPredictor initialized")
    
    @log_execution
    def predict_quarterly_growth(self, stock_id: str, target_quarter: str = None) -> Dict:
        """
        預測季度EPS成長率 (財務公式 + AI調整)

        Args:
            stock_id: 股票代碼
            target_quarter: 目標季度 (YYYY-Q)，None表示下個季度

        Returns:
            預測結果字典
        """
        logger.log_prediction_start(stock_id, 'quarterly_eps_growth')

        try:
            # 步驟1: 財務公式預測 (80%權重)
            formula_result = self._predict_eps_with_formula(stock_id, target_quarter)
            if not formula_result.get('success', True):
                return formula_result

            # 步驟2: AI調整 (20%權重)
            base_prediction = formula_result['growth_rate']
            ai_adjustment = self._apply_ai_adjustment(stock_id, base_prediction)

            # 步驟3: 整合預測結果
            comprehensive_data = formula_result.get('comprehensive_data')
            final_result = self._integrate_predictions(formula_result, ai_adjustment, target_quarter, comprehensive_data)

            # 添加額外資訊
            final_result.update({
                'stock_id': stock_id,
                'target_quarter': formula_result.get('target_quarter'),
                'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_quality': formula_result.get('data_quality'),
                'historical_data_points': formula_result.get('historical_data_points')
            })

            logger.log_prediction_result(
                stock_id, 'quarterly_eps_growth',
                final_result, final_result['confidence']
            )

            return final_result

        except Exception as e:
            error_msg = f"EPS prediction failed: {str(e)}"
            logger.error(error_msg, stock_id=stock_id)
            return self._create_error_result(error_msg)

    def predict_quarterly_growth_historical(self, stock_id: str, target_quarter: str,
                                          max_date: datetime = None) -> Dict:
        """
        歷史時間點EPS預測 (用於回測)

        Args:
            stock_id: 股票代碼
            target_quarter: 目標季度 (YYYY-Q)
            max_date: 最大資料日期限制 (用於回測)
        """
        logger.info(f"[HISTORICAL_PREDICTION] Starting historical EPS prediction | "
                   f"stock_id={stock_id} | target_quarter={target_quarter} | max_date={max_date}")

        try:
            # 🔧 獲取限制時間範圍的歷史資料
            comprehensive_data = self.db_manager.get_comprehensive_data_historical(
                stock_id, max_date=max_date
            )

            # 資料品質檢查
            quality_check = self._validate_eps_data(comprehensive_data)
            if not quality_check['is_valid']:
                return self._create_error_result(
                    quality_check['reason'],
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

            # 🤖 重新訓練專用AI模型 (基於歷史資料)
            model_retrained = False
            if hasattr(self, 'ai_adjustment') and self.ai_adjustment:
                try:
                    # 使用歷史資料重新訓練專用模型
                    self.ai_adjustment.train_stock_specific_model(
                        stock_id, max_date=max_date
                    )
                    model_retrained = True
                    logger.info(f"[AI_RETRAIN] Stock-specific EPS model retrained for {stock_id} | max_date={max_date}")
                except Exception as e:
                    logger.warning(f"EPS AI model retraining failed: {e}")

            # 步驟1: 財務公式預測 (基於歷史資料)
            formula_result = self._predict_eps_with_formula_historical(
                stock_id, target_quarter, comprehensive_data
            )
            if not formula_result.get('success', True):
                return formula_result

            # 步驟2: AI調整 (使用重新訓練的模型)
            base_prediction = formula_result['growth_rate']
            ai_adjustment = self._apply_ai_adjustment(stock_id, base_prediction)

            # 步驟3: 整合預測結果
            final_result = self._integrate_predictions(formula_result, ai_adjustment, target_quarter, comprehensive_data)

            # 添加回測特有資訊
            final_result.update({
                'stock_id': stock_id,
                'target_quarter': target_quarter,
                'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_quality': quality_check,
                'historical_data_points': formula_result.get('historical_data_points'),
                'training_data_range': {
                    'start_date': comprehensive_data.get('start_date'),
                    'end_date': comprehensive_data.get('end_date'),
                    'data_points': comprehensive_data.get('total_records', 0)
                },
                'model_retrained': model_retrained,
                'backtest_mode': True
            })

            logger.info(f"[HISTORICAL_PREDICTION] Historical EPS prediction completed | "
                       f"predicted_eps={final_result.get('predicted_eps', 0):.2f} | "
                       f"growth_rate={final_result.get('growth_rate', 0)*100:.1f}%")

            return final_result

        except Exception as e:
            error_msg = f"Historical EPS prediction failed: {str(e)}"
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

    def _predict_eps_with_formula(self, stock_id: str, target_quarter: str = None) -> Dict:
        """使用財務公式預測EPS"""
        try:
            # 獲取綜合資料
            comprehensive_data = self.db_manager.get_comprehensive_data(stock_id)

            # 資料品質檢查
            quality_check = self._validate_eps_data(comprehensive_data)
            if not quality_check['is_valid']:
                return self._create_error_result(quality_check['reason'])

            # 確定目標季度
            if target_quarter is None:
                target_quarter = self._get_next_quarter(comprehensive_data['eps_data'])

            # 執行預測
            prediction_result = self._execute_eps_prediction(comprehensive_data, target_quarter)

            # 添加基本資訊
            prediction_result.update({
                'target_quarter': target_quarter,
                'data_quality': quality_check,
                'historical_data_points': len(comprehensive_data['eps_data']),
                'comprehensive_data': comprehensive_data,  # 🔧 添加comprehensive_data
                'success': True
            })

            return prediction_result

        except Exception as e:
            return self._create_error_result(f"Formula prediction failed: {str(e)}")

    def _predict_eps_with_formula_historical(self, stock_id: str, target_quarter: str,
                                           comprehensive_data: Dict) -> Dict:
        """使用財務公式預測EPS (歷史版本)"""
        try:
            # 資料品質檢查
            quality_check = self._validate_eps_data(comprehensive_data)
            if not quality_check['is_valid']:
                return self._create_error_result(quality_check['reason'])

            # 執行預測 (使用提供的歷史資料)
            prediction_result = self._execute_eps_prediction(comprehensive_data, target_quarter)

            # 添加基本資訊
            prediction_result.update({
                'target_quarter': target_quarter,
                'data_quality': quality_check,
                'historical_data_points': len(comprehensive_data.get('eps_data', pd.DataFrame())),
                'success': True
            })

            return prediction_result

        except Exception as e:
            return self._create_error_result(f"Historical formula prediction failed: {str(e)}")

    def _apply_ai_adjustment(self, stock_id: str, base_prediction: float) -> Dict:
        """應用AI調整"""
        try:
            # 確保AI模型可用
            if not self.ai_model.is_trained:
                train_result = self.ai_model.train_model(retrain=False)
                if train_result['status'] not in ['success', 'loaded_existing']:
                    logger.warning("AI model not available, using formula-only prediction")
                    return {
                        'adjustment_factor': 0.0,
                        'adjusted_prediction': base_prediction,
                        'confidence': 'N/A',
                        'reason': 'ai_model_unavailable'
                    }

            # 預測調整因子
            ai_adjustment = self.ai_model.predict_adjustment_factor(
                stock_id, base_prediction, 'eps'
            )

            return ai_adjustment

        except Exception as e:
            logger.warning(f"AI adjustment failed: {e}")
            return {
                'adjustment_factor': 0.0,
                'adjusted_prediction': base_prediction,
                'confidence': 'Low',
                'reason': f'ai_adjustment_error: {str(e)}'
            }

    def _integrate_predictions(self, formula_result: Dict, ai_adjustment: Dict, target_quarter: str = None, comprehensive_data: Dict = None) -> Dict:
        """整合財務公式和AI調整的預測結果"""
        # 權重配置
        formula_weight = self.config['formula_weight']  # 80%
        ai_weight = self.config['ai_adjustment_weight']  # 20%

        base_prediction = formula_result['growth_rate']

        # 整合預測
        if ai_adjustment['adjustment_factor'] != 0.0:
            final_prediction = (base_prediction * formula_weight +
                              ai_adjustment['adjusted_prediction'] * ai_weight)
        else:
            final_prediction = base_prediction

        # 🔧 修復: 計算最終EPS金額 (統一使用YoY基準)
        latest_eps = formula_result['latest_eps']
        target_year, target_quarter_num = target_quarter.split('-Q')

        # 獲取去年同期EPS作為基準 (YoY)
        if comprehensive_data and target_quarter:
            yoy_base_eps = self._get_yoy_base_eps(comprehensive_data, target_quarter)
        else:
            yoy_base_eps = None
        if yoy_base_eps and yoy_base_eps > 0:
            final_eps = yoy_base_eps * (1 + final_prediction)
            logger.info(f"[YOY_CALCULATION] Using YoY base | base_eps={yoy_base_eps:.2f} | "
                       f"growth_rate={final_prediction*100:.1f}% | predicted_eps={final_eps:.2f}")
        else:
            # 如果沒有去年同期資料，使用最新EPS
            final_eps = latest_eps * (1 + final_prediction)
            logger.warning(f"[YOY_FALLBACK] No YoY base available, using latest EPS | "
                          f"latest_eps={latest_eps:.2f} | predicted_eps={final_eps:.2f}")

        # 整合信心水準
        formula_confidence = formula_result['confidence']
        ai_confidence = ai_adjustment.get('confidence', 'N/A')

        # 綜合信心水準
        if ai_confidence == 'High' and formula_confidence == 'High':
            final_confidence = 'High'
        elif ai_confidence in ['High', 'Medium'] and formula_confidence in ['High', 'Medium']:
            final_confidence = 'Medium'
        else:
            final_confidence = 'Low'

        return {
            'predicted_eps': final_eps,
            'growth_rate': final_prediction,
            'confidence': final_confidence,
            'formula_prediction': {
                'growth_rate': base_prediction,
                'confidence': formula_confidence,
                'method_breakdown': formula_result['method_breakdown'],
                'weights_used': formula_result['weights_used']
            },
            'ai_adjustment': ai_adjustment,
            'integration_weights': {
                'formula_weight': formula_weight,
                'ai_weight': ai_weight
            },
            'risk_factors': formula_result.get('risk_factors', []),
            'latest_eps': latest_eps,
            'success': True
        }

    def _get_yoy_base_eps(self, comprehensive_data: Dict, target_quarter: str) -> float:
        """
        獲取去年同期EPS作為計算基準

        Args:
            comprehensive_data: 綜合資料
            target_quarter: 目標季度 (YYYY-Q)

        Returns:
            去年同期EPS值
        """
        try:
            year, quarter_num = target_quarter.split('-Q')
            prev_year = int(year) - 1
            prev_year_quarter = f"{prev_year}-Q{quarter_num}"

            eps_data = comprehensive_data.get('eps_data', pd.DataFrame())
            if eps_data.empty:
                return None

            # 轉換目標季度為日期
            target_date = self._quarter_to_date(prev_year_quarter)
            if not target_date:
                return None

            # 查找去年同期的EPS
            target_pd_date = pd.to_datetime(target_date)
            eps_data['date_pd'] = pd.to_datetime(eps_data['date'])

            # 找最接近的日期
            eps_data['date_diff'] = abs(eps_data['date_pd'] - target_pd_date)
            closest_idx = eps_data['date_diff'].idxmin()

            if eps_data.loc[closest_idx, 'date_diff'].days <= 90:  # 90天內算有效
                yoy_eps = eps_data.loc[closest_idx, 'eps']
                logger.info(f"[YOY_BASE] Found YoY base EPS | target={prev_year_quarter} | "
                           f"date={eps_data.loc[closest_idx, 'date']} | eps={yoy_eps:.2f}")
                return yoy_eps
            else:
                logger.warning(f"[YOY_BASE] No valid YoY base found for {prev_year_quarter}")
                return None

        except Exception as e:
            logger.error(f"Failed to get YoY base EPS: {e}")
            return None

    def _quarter_to_date(self, quarter: str) -> str:
        """將季度轉換為日期"""
        try:
            year, q = quarter.split('-Q')
            quarter_end_dates = {
                '1': f"{year}-03-31",
                '2': f"{year}-06-30",  # 6月只有30天
                '3': f"{year}-09-30",  # 9月只有30天
                '4': f"{year}-12-31"
            }
            return quarter_end_dates.get(q)
        except:
            return None

    def _execute_eps_prediction(self, comprehensive_data: Dict, target_quarter: str) -> Dict:
        """執行EPS預測計算"""
        
        # 方法1: 營收驅動法
        revenue_driven_result = self._predict_by_revenue_driven(comprehensive_data)
        
        # 方法2: 利潤率趨勢法
        margin_trend_result = self._predict_by_margin_trend(comprehensive_data)
        
        # 方法3: 歷史EPS趨勢法
        eps_trend_result = self._predict_by_eps_trend(comprehensive_data)
        
        # 加權平均
        weights = self.formula_config['eps_components']
        
        final_growth = (
            revenue_driven_result['growth'] * weights['revenue_weight'] +
            margin_trend_result['growth'] * weights['margin_weight'] +
            eps_trend_result['growth'] * weights['efficiency_weight']
        )
        
        # 🔧 修復: 計算預測EPS金額 (統一使用YoY基準)
        latest_eps = comprehensive_data['eps_data']['eps'].iloc[-1] if not comprehensive_data['eps_data'].empty else 0

        # 獲取去年同期EPS作為基準
        yoy_base_eps = self._get_yoy_base_eps(comprehensive_data, target_quarter)
        if yoy_base_eps and yoy_base_eps > 0:
            predicted_eps = yoy_base_eps * (1 + final_growth)
            base_eps_used = yoy_base_eps
            calculation_method = "YoY"
        else:
            predicted_eps = latest_eps * (1 + final_growth)
            base_eps_used = latest_eps
            calculation_method = "Latest"

        logger.info(f"[EPS_CALCULATION] Method={calculation_method} | base_eps={base_eps_used:.2f} | "
                   f"growth={final_growth*100:.1f}% | predicted_eps={predicted_eps:.2f}")
        
        # 計算信心水準
        confidence = self._calculate_confidence([
            revenue_driven_result['growth'], 
            margin_trend_result['growth'], 
            eps_trend_result['growth']
        ])
        
        # 風險因子分析
        risk_factors = self._analyze_risk_factors(comprehensive_data)
        
        return {
            'predicted_eps': predicted_eps,
            'growth_rate': final_growth,
            'confidence': confidence,
            'method_breakdown': {
                'revenue_driven': revenue_driven_result,
                'margin_trend': margin_trend_result,
                'eps_trend': eps_trend_result
            },
            'weights_used': weights,
            'risk_factors': risk_factors,
            'latest_eps': latest_eps
        }
    
    def _predict_by_revenue_driven(self, comprehensive_data: Dict) -> Dict:
        """營收驅動法預測EPS"""
        try:
            monthly_revenue = comprehensive_data.get('monthly_revenue', pd.DataFrame())
            financial_ratios = comprehensive_data.get('financial_ratios', pd.DataFrame())

            if monthly_revenue.empty:
                return {'growth': 0.0, 'confidence': 'Low', 'method': 'revenue_driven', 'reason': 'No revenue data'}

            # 計算季度營收成長趨勢
            if len(monthly_revenue) >= 12:
                # 取最近12個月轉換為4個季度
                quarterly_revenue = self._convert_monthly_to_quarterly(monthly_revenue)
                revenue_growth = self.formulas.calculate_revenue_trend(quarterly_revenue)
            else:
                revenue_growth = 0.0

            # 獲取平均淨利率
            avg_net_margin = 0.0
            if not financial_ratios.empty and 'net_margin' in financial_ratios.columns:
                recent_margins = financial_ratios['net_margin'].dropna().tail(4)
                if not recent_margins.empty:
                    avg_net_margin = recent_margins.mean() / 100  # 轉換為小數

            # EPS成長 ≈ 營收成長 × (1 + 淨利率變化)
            # 簡化假設：淨利率保持穩定，EPS成長主要來自營收成長
            eps_growth = revenue_growth * (1 + avg_net_margin)

            # 信心水準基於資料完整性
            confidence = 'High' if len(monthly_revenue) >= 12 and not financial_ratios.empty else 'Medium' if len(monthly_revenue) >= 6 else 'Low'

            return {
                'growth': eps_growth,
                'confidence': confidence,
                'method': 'revenue_driven',
                'revenue_growth': revenue_growth,
                'avg_net_margin': avg_net_margin,
                'data_points': len(monthly_revenue)
            }

        except Exception as e:
            logger.warning(f"Revenue-driven EPS prediction failed: {e}")
            return {'growth': 0.0, 'confidence': 'Low', 'method': 'revenue_driven', 'error': str(e)}

    def _predict_by_margin_trend(self, comprehensive_data: Dict) -> Dict:
        """利潤率趨勢法預測EPS"""
        try:
            financial_ratios = comprehensive_data.get('financial_ratios', pd.DataFrame())

            if financial_ratios.empty or 'net_margin' not in financial_ratios.columns:
                return {'growth': 0.0, 'confidence': 'Low', 'method': 'margin_trend', 'reason': 'No margin data'}

            # 計算淨利率趨勢
            margin_trend = self.formulas.calculate_margin_trend(financial_ratios['net_margin'])

            # 計算營業效率趨勢
            opex_efficiency = 0.0
            if 'gross_margin' in financial_ratios.columns and 'operating_margin' in financial_ratios.columns:
                opex_efficiency = self.formulas.calculate_opex_efficiency(financial_ratios)

            # EPS成長 ≈ 利潤率改善 + 營業效率提升
            eps_growth = margin_trend + opex_efficiency

            # 信心水準基於資料品質和趨勢穩定性
            data_quality = len(financial_ratios)
            margin_volatility = financial_ratios['net_margin'].std() / abs(financial_ratios['net_margin'].mean()) if len(financial_ratios) > 1 else 1.0

            if data_quality >= 8 and margin_volatility < 0.3:
                confidence = 'High'
            elif data_quality >= 4 and margin_volatility < 0.5:
                confidence = 'Medium'
            else:
                confidence = 'Low'

            return {
                'growth': eps_growth,
                'confidence': confidence,
                'method': 'margin_trend',
                'margin_trend': margin_trend,
                'opex_efficiency': opex_efficiency,
                'margin_volatility': margin_volatility,
                'data_points': data_quality
            }

        except Exception as e:
            logger.warning(f"Margin trend EPS prediction failed: {e}")
            return {'growth': 0.0, 'confidence': 'Low', 'method': 'margin_trend', 'error': str(e)}

    def _predict_by_eps_trend(self, comprehensive_data: Dict) -> Dict:
        """歷史EPS趨勢法預測"""
        try:
            eps_data = comprehensive_data.get('eps_data', pd.DataFrame())

            if eps_data.empty or len(eps_data) < 3:
                return {'growth': 0.0, 'confidence': 'Low', 'method': 'eps_trend', 'reason': 'Insufficient EPS data'}

            # 計算EPS成長趨勢
            eps_values = eps_data['eps'].dropna()
            if len(eps_values) < 3:
                return {'growth': 0.0, 'confidence': 'Low', 'method': 'eps_trend', 'reason': 'Insufficient valid EPS values'}

            # 計算季度成長率
            quarterly_growth_rates = []
            for i in range(1, len(eps_values)):
                if eps_values.iloc[i-1] != 0:
                    growth = (eps_values.iloc[i] - eps_values.iloc[i-1]) / abs(eps_values.iloc[i-1])
                    quarterly_growth_rates.append(growth)

            if not quarterly_growth_rates:
                return {'growth': 0.0, 'confidence': 'Low', 'method': 'eps_trend', 'reason': 'Cannot calculate growth rates'}

            # 使用移動平均預測下季成長
            if len(quarterly_growth_rates) >= 4:
                # 使用最近4季的平均成長率
                recent_growth = np.mean(quarterly_growth_rates[-4:])
            elif len(quarterly_growth_rates) >= 2:
                # 使用最近2季的平均成長率
                recent_growth = np.mean(quarterly_growth_rates[-2:])
            else:
                recent_growth = quarterly_growth_rates[-1]

            # 趨勢穩定性評估
            growth_volatility = np.std(quarterly_growth_rates) if len(quarterly_growth_rates) > 1 else 0

            if len(quarterly_growth_rates) >= 6 and growth_volatility < 0.3:
                confidence = 'High'
            elif len(quarterly_growth_rates) >= 3 and growth_volatility < 0.5:
                confidence = 'Medium'
            else:
                confidence = 'Low'

            return {
                'growth': recent_growth,
                'confidence': confidence,
                'method': 'eps_trend',
                'growth_volatility': growth_volatility,
                'historical_growth_rates': quarterly_growth_rates[-4:],  # 最近4季
                'data_points': len(eps_values)
            }

        except Exception as e:
            logger.warning(f"EPS trend prediction failed: {e}")
            return {'growth': 0.0, 'confidence': 'Low', 'method': 'eps_trend', 'error': str(e)}
    
    def _convert_monthly_to_quarterly(self, monthly_data: pd.DataFrame) -> pd.DataFrame:
        """將月營收資料轉換為季度營收資料"""
        if monthly_data.empty:
            return pd.DataFrame()

        try:
            # 確保有日期欄位
            if 'date' not in monthly_data.columns:
                return pd.DataFrame()

            # 按季度分組
            monthly_data = monthly_data.copy()
            monthly_data['quarter'] = monthly_data['date'].dt.to_period('Q')

            # 計算季度營收（3個月總和）
            quarterly_data = monthly_data.groupby('quarter').agg({
                'revenue': 'sum',
                'date': 'max'  # 使用該季度最後一個月的日期
            }).reset_index()

            # 重新命名欄位以符合預期格式
            quarterly_data = quarterly_data.rename(columns={'revenue': 'revenue'})
            quarterly_data = quarterly_data.sort_values('date').reset_index(drop=True)

            return quarterly_data

        except Exception as e:
            logger.warning(f"Failed to convert monthly to quarterly data: {e}")
            return pd.DataFrame()

    def _get_next_quarter(self, eps_data: pd.DataFrame) -> str:
        """獲取下個季度"""
        if eps_data.empty:
            current_date = datetime.now()
            return f"{current_date.year}-Q{(current_date.month-1)//3 + 1}"
        
        latest_date = eps_data['date'].max()
        next_quarter_date = latest_date + pd.DateOffset(months=3)
        quarter = (next_quarter_date.month - 1) // 3 + 1
        return f"{next_quarter_date.year}-Q{quarter}"
    
    def _validate_eps_data(self, comprehensive_data: Dict) -> Dict:
        """驗證EPS資料品質"""
        # 基本資料檢查
        if not comprehensive_data or 'eps_data' not in comprehensive_data:
            return {'is_valid': False, 'reason': 'No EPS data available'}
        
        eps_data = comprehensive_data['eps_data']
        if eps_data.empty:
            return {'is_valid': False, 'reason': 'EPS data is empty'}
        
        if len(eps_data) < 2:
            return {'is_valid': False, 'reason': 'Insufficient EPS data (less than 2 quarters)'}
        
        return {
            'is_valid': True,
            'data_points': len(eps_data),
            'latest_date': eps_data['date'].max().strftime('%Y-%m-%d')
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
    
    def _analyze_risk_factors(self, comprehensive_data: Dict) -> list:
        """分析風險因子"""
        risk_factors = []
        
        # EPS波動性風險
        eps_data = comprehensive_data.get('eps_data', pd.DataFrame())
        if not eps_data.empty and len(eps_data) >= 4:
            eps_volatility = eps_data['eps'].std() / abs(eps_data['eps'].mean())
            if eps_volatility > 0.5:
                risk_factors.append(f"High EPS volatility ({eps_volatility:.2%})")
        
        # 資料不足風險
        if len(eps_data) < 8:
            risk_factors.append(f"Limited historical EPS data ({len(eps_data)} quarters)")
        
        return risk_factors
    
    def _create_error_result(self, error_message: str) -> Dict:
        """創建錯誤結果"""
        return {
            'predicted_eps': None,
            'growth_rate': None,
            'confidence': 'Low',
            'error': error_message,
            'success': False
        }

if __name__ == "__main__":
    # 測試EPS預測器
    predictor = EPSPredictor()
    
    # 測試2385群光電子
    test_stock = "2385"
    print(f"Testing EPSPredictor with stock {test_stock}")
    
    result = predictor.predict_quarterly_growth(test_stock)
    
    if result.get('success', True):  # 沒有error就是成功
        print(f"✅ Prediction successful")
        print(f"📈 Predicted EPS Growth: {result['growth_rate']:.2%}")
        print(f"💰 Predicted EPS: {result['predicted_eps']:.2f}")
        print(f"🎯 Confidence: {result['confidence']}")
        print(f"📊 Risk Factors: {len(result['risk_factors'])}")
    else:
        print(f"❌ Prediction failed: {result['error']}")

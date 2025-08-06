# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Financial Formulas
財務公式定義
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

class FinancialFormulas:
    """財務公式計算類別"""
    
    @staticmethod
    def calculate_revenue_trend(monthly_data: pd.DataFrame, method: str = 'linear') -> float:
        """
        計算營收趨勢
        
        Args:
            monthly_data: 月營收資料 DataFrame
            method: 趨勢計算方法 ('linear', 'exponential')
            
        Returns:
            趨勢斜率 (月成長率)
        """
        if len(monthly_data) < 3:
            return 0.0
        
        # 準備資料
        x = np.arange(len(monthly_data))
        y = monthly_data['revenue'].values
        
        if method == 'linear':
            # 線性趨勢
            coeffs = np.polyfit(x, y, 1)
            trend_slope = coeffs[0]
            # 轉換為月成長率
            avg_revenue = np.mean(y)
            monthly_growth_rate = trend_slope / avg_revenue if avg_revenue > 0 else 0
            return monthly_growth_rate
        
        elif method == 'exponential':
            # 指數趨勢 (對數線性回歸)
            y_log = np.log(y + 1)  # 避免log(0)
            coeffs = np.polyfit(x, y_log, 1)
            return coeffs[0]  # 指數成長率
        
        return 0.0
    
    @staticmethod
    def calculate_seasonal_factor(monthly_data: pd.DataFrame, target_month: int) -> float:
        """
        計算季節調整因子
        
        Args:
            monthly_data: 月營收資料
            target_month: 目標月份 (1-12)
            
        Returns:
            季節調整因子
        """
        if len(monthly_data) < 12:
            return 1.0
        
        # 按月份分組計算平均
        monthly_data['month'] = pd.to_datetime(monthly_data['date']).dt.month
        monthly_avg = monthly_data.groupby('month')['revenue'].mean()
        overall_avg = monthly_data['revenue'].mean()
        
        if target_month in monthly_avg.index and overall_avg > 0:
            seasonal_factor = monthly_avg[target_month] / overall_avg
            return seasonal_factor
        
        return 1.0
    
    @staticmethod
    def calculate_yoy_trend(monthly_data: pd.DataFrame) -> float:
        """
        計算年增率趨勢
        
        Args:
            monthly_data: 包含年增率的月營收資料
            
        Returns:
            年增率趨勢 (月變化率)
        """
        if 'revenue_growth_yoy' not in monthly_data.columns:
            return 0.0
        
        yoy_data = monthly_data['revenue_growth_yoy'].dropna()
        if len(yoy_data) < 3:
            return 0.0
        
        # 計算年增率的趨勢
        x = np.arange(len(yoy_data))
        y = yoy_data.values
        
        try:
            coeffs = np.polyfit(x, y, 1)
            return coeffs[0]  # 年增率的月變化率
        except:
            return 0.0
    
    @staticmethod
    def predict_revenue_growth(monthly_data: pd.DataFrame, 
                             weights: Dict[str, float] = None) -> Dict[str, float]:
        """
        預測營收成長率 (綜合方法)
        
        Args:
            monthly_data: 月營收資料
            weights: 各方法權重
            
        Returns:
            預測結果字典
        """
        if weights is None:
            weights = {
                'trend_extrapolation': 0.4,
                'moving_average': 0.3,
                'yoy_trend': 0.3
            }
        
        results = {}
        
        # 方法1: 趨勢外推法
        trend_growth = FinancialFormulas.calculate_revenue_trend(monthly_data)
        results['trend_extrapolation'] = trend_growth
        
        # 方法2: 移動平均法
        if len(monthly_data) >= 6:
            ma_3 = monthly_data['revenue'].tail(3).mean()
            ma_6 = monthly_data['revenue'].tail(6).mean()
            ma_growth = (ma_3 - ma_6) / ma_6 if ma_6 > 0 else 0
            results['moving_average'] = ma_growth
        else:
            results['moving_average'] = 0.0
        
        # 方法3: 年增率趨勢法
        yoy_trend = FinancialFormulas.calculate_yoy_trend(monthly_data)
        results['yoy_trend'] = yoy_trend
        
        # 加權平均
        weighted_growth = sum(results[method] * weights[method] 
                            for method in results.keys() if method in weights)
        
        results['final_prediction'] = weighted_growth
        results['confidence'] = FinancialFormulas._calculate_prediction_confidence(results)
        
        return results
    
    @staticmethod
    def predict_eps_growth(revenue_growth: float, 
                          margin_data: pd.DataFrame,
                          historical_eps: pd.DataFrame) -> Dict[str, float]:
        """
        預測EPS成長率
        
        Args:
            revenue_growth: 預測的營收成長率
            margin_data: 歷史利潤率資料
            historical_eps: 歷史EPS資料
            
        Returns:
            EPS預測結果
        """
        results = {}
        
        # 預測利潤率趨勢
        if 'net_margin' in margin_data.columns:
            margin_trend = FinancialFormulas.calculate_margin_trend(margin_data['net_margin'])
            predicted_margin_change = margin_trend
        else:
            predicted_margin_change = 0.0
        
        # 預測營業費用率變化
        if 'operating_margin' in margin_data.columns and 'gross_margin' in margin_data.columns:
            opex_efficiency = FinancialFormulas.calculate_opex_efficiency(margin_data)
        else:
            opex_efficiency = 0.0
        
        # 綜合EPS成長率預測
        # EPS成長 ≈ 營收成長 + 利潤率改善 + 營運效率提升
        eps_growth = revenue_growth + predicted_margin_change + opex_efficiency
        
        results['predicted_eps_growth'] = eps_growth
        results['revenue_contribution'] = revenue_growth
        results['margin_contribution'] = predicted_margin_change
        results['efficiency_contribution'] = opex_efficiency
        results['confidence'] = FinancialFormulas._calculate_eps_confidence(
            revenue_growth, margin_data, historical_eps
        )
        
        return results
    
    @staticmethod
    def calculate_margin_trend(margin_series: pd.Series) -> float:
        """計算利潤率趨勢"""
        if len(margin_series) < 3:
            return 0.0
        
        # 移除異常值
        margin_clean = margin_series.dropna()
        if len(margin_clean) < 3:
            return 0.0
        
        # 計算趨勢
        x = np.arange(len(margin_clean))
        y = margin_clean.values
        
        try:
            coeffs = np.polyfit(x, y, 1)
            return coeffs[0] / 100  # 轉換為小數
        except:
            return 0.0
    
    @staticmethod
    def calculate_opex_efficiency(margin_data: pd.DataFrame) -> float:
        """計算營業費用效率變化"""
        if len(margin_data) < 4:
            return 0.0
        
        # 營業費用率 = 毛利率 - 營業利益率
        if 'gross_margin' in margin_data.columns and 'operating_margin' in margin_data.columns:
            opex_ratio = margin_data['gross_margin'] - margin_data['operating_margin']
            opex_trend = FinancialFormulas.calculate_margin_trend(opex_ratio)
            return -opex_trend  # 營業費用率下降是好事，所以取負號
        
        return 0.0
    
    @staticmethod
    def _calculate_prediction_confidence(results: Dict[str, float]) -> str:
        """計算預測信心水準"""
        # 檢查各方法的一致性
        methods = ['trend_extrapolation', 'moving_average', 'yoy_trend']
        values = [results.get(method, 0) for method in methods]
        
        # 計算標準差作為一致性指標
        std_dev = np.std(values)
        
        if std_dev < 0.05:  # 5%以內
            return 'High'
        elif std_dev < 0.15:  # 15%以內
            return 'Medium'
        else:
            return 'Low'
    
    @staticmethod
    def _calculate_eps_confidence(revenue_growth: float, 
                                margin_data: pd.DataFrame,
                                historical_eps: pd.DataFrame) -> str:
        """計算EPS預測信心水準"""
        confidence_score = 0
        
        # 營收預測信心
        if abs(revenue_growth) < 0.3:  # 30%以內的成長率較可信
            confidence_score += 1
        
        # 利潤率資料完整性
        if len(margin_data) >= 8:  # 至少8季資料
            confidence_score += 1
        
        # EPS歷史穩定性
        if len(historical_eps) >= 8:
            eps_volatility = historical_eps['eps'].std() / historical_eps['eps'].mean()
            if eps_volatility < 0.5:  # 變異係數小於50%
                confidence_score += 1
        
        if confidence_score >= 3:
            return 'High'
        elif confidence_score >= 2:
            return 'Medium'
        else:
            return 'Low'

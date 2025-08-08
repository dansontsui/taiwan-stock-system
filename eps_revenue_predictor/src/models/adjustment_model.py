# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - AI Adjustment Model
專用型AI調整模型 (20%權重)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    from lightgbm import LGBMRegressor
    LIGHTGBM_AVAILABLE = True
except ImportError:
    from sklearn.ensemble import GradientBoostingRegressor
    LIGHTGBM_AVAILABLE = False

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path

from config.settings import AI_MODEL_CONFIG, PROJECT_ROOT
from src.data.database_manager import DatabaseManager
from src.utils.logger import get_logger, log_execution

logger = get_logger('adjustment_model')

class AIAdjustmentModel:
    """專用型AI調整模型
    
    用於對財務公式預測結果進行智能調整
    調整範圍限制在±20%以內
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.config = AI_MODEL_CONFIG
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = PROJECT_ROOT / 'models' / 'adjustment_model.pkl'
        self.scaler_path = PROJECT_ROOT / 'models' / 'adjustment_scaler.pkl'
        
        # 確保模型目錄存在
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AIAdjustmentModel initialized (LightGBM: {LIGHTGBM_AVAILABLE})")
    
    @log_execution
    def train_model(self, stock_list: List[str] = None, retrain: bool = False) -> Dict:
        """
        訓練調整模型
        
        Args:
            stock_list: 訓練用股票列表
            retrain: 是否強制重新訓練
            
        Returns:
            訓練結果
        """
        # 檢查是否需要訓練
        if not retrain and self._load_existing_model():
            logger.info("Loaded existing trained model")
            return {'status': 'loaded_existing', 'model_exists': True}
        
        logger.info("Starting AI adjustment model training")
        
        # 獲取訓練股票列表
        if stock_list is None:
            stock_list = self.db_manager.get_available_stocks(limit=50)  # 限制50檔股票
        
        # 收集訓練資料
        training_data = self._collect_training_data(stock_list)
        
        if training_data.empty:
            logger.error("No training data available")
            return {'status': 'failed', 'reason': 'no_data'}
        
        # 準備特徵和目標變數
        X, y = self._prepare_training_data(training_data)
        
        if len(X) < 10:
            logger.warning(f"Insufficient training samples: {len(X)}")
            return {'status': 'failed', 'reason': 'insufficient_samples'}
        
        # 分割訓練和驗證集
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 標準化特徵
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # 訓練模型
        self.model = self._create_model()
        self.model.fit(X_train_scaled, y_train)
        
        # 評估模型
        train_score = self.model.score(X_train_scaled, y_train)
        val_score = self.model.score(X_val_scaled, y_val)
        
        # 預測驗證集
        y_pred = self.model.predict(X_val_scaled)
        mae = np.mean(np.abs(y_val - y_pred))
        rmse = np.sqrt(np.mean((y_val - y_pred) ** 2))
        
        self.is_trained = True
        
        # 保存模型
        self._save_model()
        
        training_result = {
            'status': 'success',
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'train_r2': train_score,
            'validation_r2': val_score,
            'mae': mae,
            'rmse': rmse,
            'features_used': self.config['features']
        }
        
        logger.log_model_training('AI_Adjustment', len(X_train), training_result)
        
        return training_result

    def train_stock_specific_model(self, stock_id: str, max_date: datetime = None) -> Dict:
        """
        訓練股票專用AI模型 (用於回測)

        Args:
            stock_id: 股票代碼
            max_date: 最大資料日期限制 (用於回測)

        Returns:
            訓練結果
        """
        logger.info(f"[STOCK_SPECIFIC_TRAINING] Training stock-specific model | "
                   f"stock_id={stock_id} | max_date={max_date}")

        try:
            # 🔧 收集該股票的歷史訓練資料 (限制時間範圍)
            training_data = self._collect_stock_specific_training_data(stock_id, max_date)

            if training_data.empty or len(training_data) < 5:
                logger.warning(f"Insufficient stock-specific training data: {len(training_data)} samples")
                # 如果專用資料不足，使用通用模型
                return {'status': 'fallback_to_general', 'samples': len(training_data)}

            # 準備特徵和目標變數
            X, y = self._prepare_training_data(training_data)

            if len(X) < 3:
                logger.warning(f"Insufficient training samples after preparation: {len(X)}")
                return {'status': 'fallback_to_general', 'samples': len(X)}

            # 🤖 創建並訓練專用模型
            stock_specific_model = self._create_model()

            # 如果樣本太少，使用簡單的線性回歸
            if len(X) < 10:
                from sklearn.linear_model import LinearRegression
                stock_specific_model = LinearRegression()

            # 標準化特徵 (使用專用的scaler)
            stock_scaler = StandardScaler()
            X_scaled = stock_scaler.fit_transform(X)

            # 訓練專用模型
            stock_specific_model.fit(X_scaled, y)

            # 評估模型
            train_score = stock_specific_model.score(X_scaled, y)
            y_pred = stock_specific_model.predict(X_scaled)
            mae = np.mean(np.abs(y - y_pred))
            rmse = np.sqrt(np.mean((y - y_pred) ** 2))

            # 🔧 替換當前模型為專用模型 (臨時)
            self.model = stock_specific_model
            self.scaler = stock_scaler
            self.is_trained = True

            training_result = {
                'status': 'success',
                'model_type': 'stock_specific',
                'training_samples': len(X),
                'train_r2': train_score,
                'mae': mae,
                'rmse': rmse,
                'data_range': {
                    'start_date': training_data['date'].min().strftime('%Y-%m-%d') if 'date' in training_data.columns else None,
                    'end_date': training_data['date'].max().strftime('%Y-%m-%d') if 'date' in training_data.columns else None
                }
            }

            logger.info(f"[STOCK_SPECIFIC_TRAINING] Stock-specific model trained successfully | "
                       f"samples={len(X)} | r2={train_score:.3f} | mae={mae:.3f}")

            return training_result

        except Exception as e:
            logger.error(f"Stock-specific model training failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    def _calculate_features_for_stock(self, monthly_data: pd.DataFrame,
                                    financial_data: pd.DataFrame,
                                    current_date: datetime) -> Dict:
        """為單一股票計算特徵"""
        try:
            features = {}

            if len(monthly_data) >= 3:
                # 營收相關特徵
                recent_revenues = monthly_data['revenue'].tail(3).values
                features['revenue_trend'] = (recent_revenues[-1] - recent_revenues[0]) / recent_revenues[0]
                features['revenue_volatility'] = np.std(recent_revenues) / np.mean(recent_revenues)

                # 成長率特徵
                if len(monthly_data) >= 12:
                    yoy_growth = monthly_data['revenue_growth_yoy'].tail(3).mean()
                    features['avg_yoy_growth'] = yoy_growth if not pd.isna(yoy_growth) else 0
                else:
                    features['avg_yoy_growth'] = 0

                # 季節性特徵
                month = current_date.month
                features['month'] = month
                features['quarter'] = (month - 1) // 3 + 1
            else:
                # 預設值
                features['revenue_trend'] = 0
                features['revenue_volatility'] = 0
                features['avg_yoy_growth'] = 0
                features['month'] = current_date.month
                features['quarter'] = (current_date.month - 1) // 3 + 1

            # 財務比率特徵 (如果有的話)
            if not financial_data.empty:
                latest_financial = financial_data.iloc[-1]
                features['roe'] = latest_financial.get('roe', 0) or 0
                features['roa'] = latest_financial.get('roa', 0) or 0
            else:
                features['roe'] = 0
                features['roa'] = 0

            return features

        except Exception as e:
            logger.warning(f"Feature calculation failed: {e}")
            return {
                'revenue_trend': 0,
                'revenue_volatility': 0,
                'avg_yoy_growth': 0,
                'month': current_date.month,
                'quarter': (current_date.month - 1) // 3 + 1,
                'roe': 0,
                'roa': 0
            }

    def _collect_stock_specific_training_data(self, stock_id: str, max_date: datetime = None) -> pd.DataFrame:
        """收集股票專用訓練資料"""
        try:
            # 獲取該股票的歷史資料 (限制時間範圍)
            if max_date:
                # 使用歷史資料查詢
                comprehensive_data = self.db_manager.get_comprehensive_data_historical(
                    stock_id, max_date=max_date
                )
            else:
                comprehensive_data = self.db_manager.get_comprehensive_data(stock_id)

            if not comprehensive_data or comprehensive_data.get('monthly_revenue', pd.DataFrame()).empty:
                return pd.DataFrame()

            # 構建訓練資料
            monthly_data = comprehensive_data.get('monthly_revenue', pd.DataFrame())
            financial_data = comprehensive_data.get('financial_data', pd.DataFrame())

            # 合併資料並計算特徵
            training_records = []

            for i in range(1, len(monthly_data)):
                current_month = monthly_data.iloc[i]
                prev_month = monthly_data.iloc[i-1]

                # 計算實際成長率 (目標變數)
                actual_growth = (current_month['revenue'] - prev_month['revenue']) / prev_month['revenue']

                # 計算特徵
                features = self._calculate_features_for_stock(
                    monthly_data.iloc[:i], financial_data, current_month['date']
                )

                if features:
                    record = features.copy()
                    record['actual_growth'] = actual_growth
                    record['date'] = current_month['date']
                    training_records.append(record)

            if training_records:
                training_df = pd.DataFrame(training_records)
                logger.info(f"Collected {len(training_df)} stock-specific training records for {stock_id}")
                return training_df

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to collect stock-specific training data: {e}")
            return pd.DataFrame()

    @log_execution
    def predict_adjustment_factor(self, stock_id: str, base_prediction: float,
                                prediction_type: str = 'revenue') -> Dict:
        """
        預測調整因子
        
        Args:
            stock_id: 股票代碼
            base_prediction: 基礎預測值
            prediction_type: 預測類型 ('revenue' 或 'eps')
            
        Returns:
            調整結果
        """
        if not self.is_trained and not self._load_existing_model():
            logger.warning("Model not trained, returning zero adjustment")
            return {
                'adjustment_factor': 0.0,
                'adjusted_prediction': base_prediction,
                'confidence': 'Low',
                'reason': 'model_not_trained'
            }
        
        try:
            # 提取特徵
            features = self._extract_features(stock_id)
            
            if features is None:
                return {
                    'adjustment_factor': 0.0,
                    'adjusted_prediction': base_prediction,
                    'confidence': 'Low',
                    'reason': 'feature_extraction_failed'
                }
            
            # 標準化特徵
            features_scaled = self.scaler.transform([features])
            
            # 預測調整因子
            raw_adjustment = self.model.predict(features_scaled)[0]
            
            # 限制調整範圍在±20%以內
            max_adjustment = self.config['adjustment_range']
            adjustment_factor = np.clip(raw_adjustment, -max_adjustment, max_adjustment)
            
            # 計算調整後的預測值
            adjusted_prediction = base_prediction * (1 + adjustment_factor)
            
            # 評估調整信心度
            confidence = self._evaluate_adjustment_confidence(features, adjustment_factor)
            
            result = {
                'adjustment_factor': adjustment_factor,
                'adjusted_prediction': adjusted_prediction,
                'raw_adjustment': raw_adjustment,
                'confidence': confidence,
                'features_used': dict(zip(self.config['features'], features)),
                'base_prediction': base_prediction
            }
            
            logger.debug(f"AI adjustment for {stock_id}: {adjustment_factor:.3f} ({confidence})")
            
            return result
            
        except Exception as e:
            logger.error(f"AI adjustment prediction failed: {e}", stock_id=stock_id)
            return {
                'adjustment_factor': 0.0,
                'adjusted_prediction': base_prediction,
                'confidence': 'Low',
                'reason': f'prediction_error: {str(e)}'
            }
    
    def _create_model(self):
        """創建機器學習模型"""
        if LIGHTGBM_AVAILABLE:
            return LGBMRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                verbose=-1
            )
        else:
            return GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
    
    def _collect_training_data(self, stock_list: List[str]) -> pd.DataFrame:
        """收集訓練資料"""
        logger.info(f"Collecting training data for {len(stock_list)} stocks")
        
        training_records = []
        
        for stock_id in stock_list[:20]:  # 限制20檔股票以加快訓練
            try:
                # 獲取股票資料
                data = self.db_manager.get_comprehensive_data(stock_id)
                
                if data['data_quality']['overall_score'] < 0.5:
                    continue
                
                # 提取特徵和目標變數
                features = self._extract_features(stock_id)
                if features is None:
                    continue
                
                # 計算歷史預測誤差作為目標變數
                target = self._calculate_historical_error(data)
                if target is None:
                    continue
                
                record = {
                    'stock_id': stock_id,
                    'target': target,
                    **dict(zip(self.config['features'], features))
                }
                
                training_records.append(record)
                
            except Exception as e:
                logger.warning(f"Failed to process stock {stock_id}: {e}")
                continue
        
        df = pd.DataFrame(training_records)
        logger.info(f"Collected {len(df)} training records")
        
        return df
    
    def _extract_features(self, stock_id: str) -> Optional[List[float]]:
        """提取調整模型特徵"""
        try:
            data = self.db_manager.get_comprehensive_data(stock_id)
            
            if data['data_quality']['overall_score'] < 0.3:
                return None
            
            features = []
            
            # 特徵1: 營收波動性
            revenue_data = data['monthly_revenue']
            if not revenue_data.empty:
                revenue_volatility = revenue_data['revenue'].std() / revenue_data['revenue'].mean()
                features.append(revenue_volatility)
            else:
                features.append(0.5)  # 預設值
            
            # 特徵2: 利潤率趨勢
            ratio_data = data['financial_ratios']
            if not ratio_data.empty and 'net_margin' in ratio_data.columns:
                margin_trend = self._calculate_trend(ratio_data['net_margin'])
                features.append(margin_trend)
            else:
                features.append(0.0)
            
            # 特徵3: 營業費用效率
            if not ratio_data.empty and 'operating_margin' in ratio_data.columns and 'gross_margin' in ratio_data.columns:
                opex_efficiency = self._calculate_opex_efficiency(ratio_data)
                features.append(opex_efficiency)
            else:
                features.append(0.0)
            
            # 特徵4: 產業動能 (簡化版)
            industry_momentum = self._estimate_industry_momentum(stock_id)
            features.append(industry_momentum)
            
            # 特徵5: 市場情緒 (簡化版)
            market_sentiment = self._estimate_market_sentiment()
            features.append(market_sentiment)
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed for {stock_id}: {e}")
            return None
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """計算時間序列趨勢"""
        if len(series) < 3:
            return 0.0
        
        clean_series = series.dropna()
        if len(clean_series) < 3:
            return 0.0
        
        x = np.arange(len(clean_series))
        y = clean_series.values
        
        try:
            coeffs = np.polyfit(x, y, 1)
            return coeffs[0] / (np.mean(y) + 0.01)  # 標準化趨勢
        except:
            return 0.0
    
    def _calculate_opex_efficiency(self, ratio_data: pd.DataFrame) -> float:
        """計算營業費用效率"""
        if 'gross_margin' not in ratio_data.columns or 'operating_margin' not in ratio_data.columns:
            return 0.0
        
        opex_ratio = ratio_data['gross_margin'] - ratio_data['operating_margin']
        return -self._calculate_trend(opex_ratio)  # 營業費用率下降是好事
    
    def _estimate_industry_momentum(self, stock_id: str) -> float:
        """估算產業動能 (簡化版)"""
        # 這裡可以實作更複雜的產業分析
        # 目前返回隨機值作為佔位符
        np.random.seed(hash(stock_id) % 2**32)
        return np.random.normal(0, 0.1)
    
    def _estimate_market_sentiment(self) -> float:
        """估算市場情緒 (簡化版)"""
        # 這裡可以實作市場情緒分析
        # 目前返回固定值
        return 0.0
    
    def _calculate_historical_error(self, data: Dict) -> Optional[float]:
        """計算歷史預測誤差作為訓練目標"""
        # 簡化版：使用營收波動性作為代理變數
        revenue_data = data['monthly_revenue']
        if revenue_data.empty or len(revenue_data) < 6:
            return None
        
        # 計算預測誤差的代理指標
        recent_volatility = revenue_data['revenue'].tail(6).std() / revenue_data['revenue'].tail(6).mean()
        overall_volatility = revenue_data['revenue'].std() / revenue_data['revenue'].mean()
        
        # 誤差代理 = 近期波動性 - 整體波動性
        error_proxy = recent_volatility - overall_volatility
        
        # 限制在合理範圍內
        return np.clip(error_proxy, -0.2, 0.2)
    
    def _prepare_training_data(self, training_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """準備訓練資料"""
        feature_cols = self.config['features']
        
        X = training_data[feature_cols].values
        y = training_data['target'].values
        
        # 移除異常值
        mask = (np.abs(y) < 0.5) & np.isfinite(X).all(axis=1) & np.isfinite(y)
        X = X[mask]
        y = y[mask]
        
        return X, y
    
    def _evaluate_adjustment_confidence(self, features: List[float], adjustment: float) -> str:
        """評估調整信心度"""
        # 基於特徵品質和調整幅度評估信心度
        feature_quality = 1 - np.mean([abs(f) for f in features if abs(f) < 10])  # 避免極端值
        adjustment_magnitude = abs(adjustment)
        
        if feature_quality > 0.7 and adjustment_magnitude < 0.1:
            return 'High'
        elif feature_quality > 0.5 and adjustment_magnitude < 0.15:
            return 'Medium'
        else:
            return 'Low'
    
    def _save_model(self):
        """保存模型"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def _load_existing_model(self) -> bool:
        """載入現有模型"""
        try:
            if self.model_path.exists() and self.scaler_path.exists():
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                logger.info("Existing model loaded successfully")
                return True
        except Exception as e:
            logger.warning(f"Failed to load existing model: {e}")
        
        return False

if __name__ == "__main__":
    # 測試AI調整模型
    model = AIAdjustmentModel()
    
    print("Testing AI Adjustment Model")
    
    # 訓練模型
    print("Training model...")
    train_result = model.train_model(retrain=True)
    print(f"Training result: {train_result['status']}")
    
    if train_result['status'] == 'success':
        # 測試預測
        test_stock = "2385"
        base_prediction = 0.15  # 15%成長率
        
        adjustment_result = model.predict_adjustment_factor(test_stock, base_prediction)
        
        print(f"Base prediction: {base_prediction:.2%}")
        print(f"Adjustment factor: {adjustment_result['adjustment_factor']:.3f}")
        print(f"Adjusted prediction: {adjustment_result['adjusted_prediction']:.2%}")
        print(f"Confidence: {adjustment_result['confidence']}")

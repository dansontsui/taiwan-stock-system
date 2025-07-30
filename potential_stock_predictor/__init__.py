"""
潛力股預測系統

基於台灣股票系統的機器學習預測模組，用於識別具有潛力的股票。
預測目標：財務資料公布後20個交易日內股價上漲超過5%的股票。

主要功能：
1. 特徵工程：月營收、財務比率、現金流、技術指標
2. 模型訓練：LightGBM、XGBoost、Random Forest、Logistic Regression
3. 預測服務：潛力股排行榜、預測結果追蹤
4. 系統整合：Web介面、API接口

作者：Taiwan Stock System Team
版本：1.0.0
"""

__version__ = "1.0.0"
__author__ = "Taiwan Stock System Team"

from .config.config import (
    DATABASE_CONFIG,
    MODEL_CONFIG,
    FEATURE_CONFIG,
    TRAINING_CONFIG,
    PREDICTION_CONFIG
)

# 主要模組導入（延遲導入避免循環依賴）
def get_feature_engineer():
    """獲取特徵工程器"""
    from .src.features.feature_engineering import FeatureEngineer
    return FeatureEngineer()

def get_model_trainer():
    """獲取模型訓練器"""
    from .src.models.model_trainer import ModelTrainer
    return ModelTrainer()

def get_predictor():
    """獲取預測器"""
    from .src.models.predictor import Predictor
    return Predictor()

# 快速啟動函數
def quick_predict(stock_ids=None, model_type='lightgbm'):
    """
    快速預測潛力股
    
    Args:
        stock_ids: 股票代碼列表，None表示預測所有股票
        model_type: 模型類型
    
    Returns:
        預測結果DataFrame
    """
    predictor = get_predictor()
    return predictor.predict(stock_ids=stock_ids, model_type=model_type)

def train_models():
    """訓練所有模型"""
    trainer = get_model_trainer()
    return trainer.train_all_models()

# 版本資訊
def get_version_info():
    """獲取版本資訊"""
    return {
        'version': __version__,
        'author': __author__,
        'description': '潛力股預測系統',
        'target': '20日內股價上漲超過5%',
        'models': MODEL_CONFIG['model_types']
    }

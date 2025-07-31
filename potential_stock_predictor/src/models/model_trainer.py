#!/usr/bin/env python3
"""
模型訓練器

支援多種機器學習模型的訓練、驗證和評估：
- LightGBM
- XGBoost  
- Random Forest
- Logistic Regression

包含時序交叉驗證、超參數調校和模型評估功能。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import pickle
import json
from datetime import datetime

# 機器學習套件
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, auc
)
from sklearn.preprocessing import StandardScaler

# 可選的高級機器學習套件
try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import optuna
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

from ..utils.database import DatabaseManager
from ..utils.helpers import save_model, save_json
try:
    from ...config.config import MODEL_CONFIG, TRAINING_CONFIG, HYPERPARAMETERS
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..')
    sys.path.insert(0, project_root)
    from config.config import MODEL_CONFIG, TRAINING_CONFIG, HYPERPARAMETERS

logger = logging.getLogger(__name__)

class ModelTrainer:
    """模型訓練器"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化模型訓練器
        
        Args:
            db_manager: 資料庫管理器
        """
        self.db_manager = db_manager or DatabaseManager()
        self.model_config = MODEL_CONFIG
        self.training_config = TRAINING_CONFIG
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        
        # 確保模型目錄存在
        self.model_config['models_dir'].mkdir(parents=True, exist_ok=True)
    
    def prepare_data(self, features_df: pd.DataFrame, targets_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        準備訓練資料
        
        Args:
            features_df: 特徵DataFrame
            targets_df: 目標變數DataFrame
            
        Returns:
            (特徵矩陣, 目標向量)
        """
        logger.info("準備訓練資料...")
        
        # 合併特徵和目標變數
        data = features_df.merge(
            targets_df[['stock_id', 'feature_date', 'target']], 
            on=['stock_id', 'feature_date'], 
            how='inner'
        )
        
        if data.empty:
            raise ValueError("合併後的資料為空")
        
        # 移除非特徵欄位
        feature_columns = [col for col in data.columns 
                          if col not in ['stock_id', 'feature_date', 'target']]
        
        X = data[feature_columns].copy()
        y = data['target'].copy()
        
        # 處理缺失值
        X = X.fillna(0)
        
        # 移除無變異的特徵
        variance_threshold = 1e-8
        feature_variances = X.var()
        valid_features = feature_variances[feature_variances > variance_threshold].index
        X = X[valid_features]
        
        self.feature_names = list(X.columns)
        
        logger.info(f"準備完成: {len(X)} 個樣本, {len(self.feature_names)} 個特徵")
        logger.info(f"正樣本比例: {y.mean():.2%}")
        
        return X, y
    
    def split_data(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        分割訓練和測試資料
        
        Args:
            X: 特徵矩陣
            y: 目標向量
            
        Returns:
            (X_train, X_test, y_train, y_test)
        """
        config = self.training_config['train_test_split']
        
        if config['time_series_split']:
            # 時序分割：使用最後的資料作為測試集
            split_idx = int(len(X) * (1 - config['test_size']))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        else:
            # 隨機分割
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=config['test_size'], 
                random_state=42, stratify=y
            )
        
        logger.info(f"資料分割完成: 訓練集 {len(X_train)}, 測試集 {len(X_test)}")
        
        return X_train, X_test, y_train, y_test
    
    def train_lightgbm(self, X_train: pd.DataFrame, y_train: pd.Series,
                      X_val: pd.DataFrame = None, y_val: pd.Series = None,
                      params: Dict = None) -> lgb.LGBMClassifier:
        """訓練LightGBM模型"""
        logger.info("訓練LightGBM模型...")
        
        if params is None:
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbosity': -1,
                'random_state': 42
            }
        
        model = lgb.LGBMClassifier(**params)
        
        # 設置驗證集
        eval_set = [(X_train, y_train)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))
        
        model.fit(
            X_train, y_train,
            eval_set=eval_set,
            callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(0)]
        )
        
        return model
    
    def train_xgboost(self, X_train: pd.DataFrame, y_train: pd.Series,
                     X_val: pd.DataFrame = None, y_val: pd.Series = None,
                     params: Dict = None) -> xgb.XGBClassifier:
        """訓練XGBoost模型"""
        logger.info("訓練XGBoost模型...")
        
        if params is None:
            params = {
                'objective': 'binary:logistic',
                'eval_metric': 'logloss',
                'max_depth': 6,
                'learning_rate': 0.05,
                'n_estimators': 1000,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42
            }
        
        model = xgb.XGBClassifier(**params)
        
        # 設置驗證集
        eval_set = [(X_train, y_train)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))
        
        model.fit(
            X_train, y_train,
            eval_set=eval_set,
            early_stopping_rounds=50,
            verbose=False
        )
        
        return model
    
    def train_random_forest(self, X_train: pd.DataFrame, y_train: pd.Series,
                           params: Dict = None) -> RandomForestClassifier:
        """訓練Random Forest模型"""
        logger.info("訓練Random Forest模型...")
        
        if params is None:
            params = {
                'n_estimators': 200,
                'max_depth': 20,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'max_features': 'sqrt',
                'random_state': 42,
                'n_jobs': -1
            }
        
        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)
        
        return model
    
    def train_logistic_regression(self, X_train: pd.DataFrame, y_train: pd.Series,
                                 params: Dict = None) -> LogisticRegression:
        """訓練Logistic Regression模型"""
        logger.info("訓練Logistic Regression模型...")
        
        # 標準化特徵
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        self.scalers['logistic_regression'] = scaler
        
        if params is None:
            params = {
                'C': 1.0,
                'penalty': 'l2',
                'solver': 'liblinear',
                'max_iter': 1000,
                'random_state': 42
            }
        
        model = LogisticRegression(**params)
        model.fit(X_train_scaled, y_train)
        
        return model

    def evaluate_model(self, model: Any, X_test: pd.DataFrame, y_test: pd.Series,
                      model_name: str = 'model') -> Dict:
        """
        評估模型性能

        Args:
            model: 訓練好的模型
            X_test: 測試特徵
            y_test: 測試目標
            model_name: 模型名稱

        Returns:
            評估結果字典
        """
        logger.info(f"評估模型: {model_name}")

        # 預處理測試資料
        if model_name == 'logistic_regression' and model_name in self.scalers:
            X_test_processed = self.scalers[model_name].transform(X_test)
        else:
            X_test_processed = X_test

        # 預測
        y_pred = model.predict(X_test_processed)
        y_pred_proba = model.predict_proba(X_test_processed)[:, 1]

        # 計算評估指標
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba)
        }

        # 計算Precision-Recall AUC
        precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
        metrics['pr_auc'] = auc(recall, precision)

        logger.info(f"{model_name} 評估結果: AUC={metrics['roc_auc']:.4f}, F1={metrics['f1_score']:.4f}")

        return metrics

    def save_model(self, model: Any, model_name: str):
        """儲存模型"""
        model_path = self.model_config['models_dir'] / f"{model_name}_{self.model_config['model_version']}.pkl"
        save_model(model, str(model_path))

        # 儲存scaler（如果有的話）
        if model_name in self.scalers:
            scaler_path = self.model_config['models_dir'] / f"{model_name}_scaler_{self.model_config['model_version']}.pkl"
            save_model(self.scalers[model_name], str(scaler_path))

        logger.info(f"模型已儲存: {model_path}")

    def save_training_results(self, results: Dict):
        """儲存訓練結果"""
        # 準備儲存的結果（移除模型物件）
        save_results = {}
        for model_name, result in results.items():
            save_results[model_name] = {
                'metrics': result['metrics'],
                'feature_names': result['feature_names'],
                'training_time': datetime.now().isoformat()
            }

        # 儲存結果
        results_path = self.model_config['models_dir'] / f"training_results_{self.model_config['model_version']}.json"
        save_json(save_results, str(results_path))

        # 儲存特徵名稱
        features_path = self.model_config['models_dir'] / f"feature_names_{self.model_config['model_version']}.json"
        save_json({'feature_names': self.feature_names}, str(features_path))

        logger.info(f"訓練結果已儲存: {results_path}")

    def train_all_models(self, features_df: pd.DataFrame, targets_df: pd.DataFrame) -> Dict:
        """
        訓練所有模型

        Args:
            features_df: 特徵DataFrame
            targets_df: 目標變數DataFrame

        Returns:
            訓練結果字典
        """
        logger.info("開始訓練所有模型...")

        # 準備資料
        X, y = self.prepare_data(features_df, targets_df)
        X_train, X_test, y_train, y_test = self.split_data(X, y)

        # 進一步分割驗證集
        X_train_split, X_val, y_train_split, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
        )

        results = {}

        # 訓練各種模型
        for model_type in self.model_config['model_types']:
            try:
                logger.info(f"訓練 {model_type} 模型...")

                if model_type == 'lightgbm':
                    model = self.train_lightgbm(X_train_split, y_train_split, X_val, y_val)
                elif model_type == 'xgboost':
                    model = self.train_xgboost(X_train_split, y_train_split, X_val, y_val)
                elif model_type == 'random_forest':
                    model = self.train_random_forest(X_train_split, y_train_split)
                elif model_type == 'logistic_regression':
                    model = self.train_logistic_regression(X_train_split, y_train_split)
                else:
                    logger.warning(f"未知的模型類型: {model_type}")
                    continue

                # 評估模型
                metrics = self.evaluate_model(model, X_test, y_test, model_type)

                # 儲存模型
                self.save_model(model, model_type)

                # 儲存結果
                results[model_type] = {
                    'model': model,
                    'metrics': metrics,
                    'feature_names': self.feature_names
                }

                self.models[model_type] = model

            except Exception as e:
                logger.error(f"訓練 {model_type} 模型失敗: {e}")
                continue

        # 儲存訓練結果
        self.save_training_results(results)

        logger.info(f"模型訓練完成，成功訓練 {len(results)} 個模型")

        return results

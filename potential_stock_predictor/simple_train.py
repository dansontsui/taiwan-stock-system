#!/usr/bin/env python3
"""
簡化版模型訓練器

使用基本機器學習模型訓練潛力股預測模型
"""

import sys
import os
import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix
)
from sklearn.preprocessing import StandardScaler

def load_data(features_file, targets_file):
    """載入特徵和目標變數資料"""
    print("📊 載入資料...")
    
    # 載入特徵資料
    if not Path(features_file).exists():
        raise FileNotFoundError(f"找不到特徵檔案: {features_file}")
    
    features_df = pd.read_csv(features_file)
    print(f"   ✅ 特徵資料: {len(features_df)} 個樣本, {len(features_df.columns)-2} 個特徵")
    
    # 載入目標變數資料
    if not Path(targets_file).exists():
        raise FileNotFoundError(f"找不到目標變數檔案: {targets_file}")
    
    targets_df = pd.read_csv(targets_file)
    print(f"   ✅ 目標變數: {len(targets_df)} 個樣本")
    
    return features_df, targets_df

def prepare_data(features_df, targets_df):
    """準備訓練資料"""
    print("🔧 準備訓練資料...")
    
    # 合併特徵和目標變數
    data = features_df.merge(
        targets_df[['stock_id', 'feature_date', 'target']], 
        on=['stock_id', 'feature_date'], 
        how='inner'
    )
    
    if data.empty:
        raise ValueError("合併後的資料為空，請檢查特徵和目標變數的股票代碼和日期是否匹配")
    
    print(f"   ✅ 合併後資料: {len(data)} 個樣本")
    
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
    
    print(f"   ✅ 最終特徵數: {len(X.columns)}")
    print(f"   ✅ 正樣本比例: {y.mean():.2%}")
    
    return X, y, list(X.columns)

def train_random_forest(X_train, y_train, X_val, y_val):
    """訓練Random Forest模型"""
    print("\n🌲 訓練Random Forest模型...")
    
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # 驗證集評估
    y_pred = model.predict(X_val)
    y_pred_proba = model.predict_proba(X_val)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_val, y_pred),
        'precision': precision_score(y_val, y_pred),
        'recall': recall_score(y_val, y_pred),
        'f1_score': f1_score(y_val, y_pred),
        'roc_auc': roc_auc_score(y_val, y_pred_proba)
    }
    
    print(f"   準確率: {metrics['accuracy']:.3f}")
    print(f"   精確率: {metrics['precision']:.3f}")
    print(f"   召回率: {metrics['recall']:.3f}")
    print(f"   F1分數: {metrics['f1_score']:.3f}")
    print(f"   ROC AUC: {metrics['roc_auc']:.3f}")
    
    return model, metrics

def train_logistic_regression(X_train, y_train, X_val, y_val):
    """訓練Logistic Regression模型"""
    print("\n📈 訓練Logistic Regression模型...")
    
    # 標準化特徵
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    model = LogisticRegression(
        C=1.0,
        penalty='l2',
        solver='liblinear',
        max_iter=1000,
        random_state=42
    )
    
    model.fit(X_train_scaled, y_train)
    
    # 驗證集評估
    y_pred = model.predict(X_val_scaled)
    y_pred_proba = model.predict_proba(X_val_scaled)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_val, y_pred),
        'precision': precision_score(y_val, y_pred),
        'recall': recall_score(y_val, y_pred),
        'f1_score': f1_score(y_val, y_pred),
        'roc_auc': roc_auc_score(y_val, y_pred_proba)
    }
    
    print(f"   準確率: {metrics['accuracy']:.3f}")
    print(f"   精確率: {metrics['precision']:.3f}")
    print(f"   召回率: {metrics['recall']:.3f}")
    print(f"   F1分數: {metrics['f1_score']:.3f}")
    print(f"   ROC AUC: {metrics['roc_auc']:.3f}")
    
    return model, scaler, metrics

def save_model(model, model_name, scaler=None, feature_names=None, metrics=None):
    """儲存模型"""
    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # 儲存模型
    model_path = models_dir / f"{model_name}_v1.0.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"   ✅ 模型已儲存: {model_path}")
    
    # 儲存scaler（如果有）
    if scaler:
        scaler_path = models_dir / f"{model_name}_scaler_v1.0.pkl"
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        print(f"   ✅ Scaler已儲存: {scaler_path}")
    
    # 儲存特徵名稱和評估結果
    if feature_names or metrics:
        info = {
            'model_name': model_name,
            'feature_names': feature_names,
            'metrics': metrics,
            'training_time': datetime.now().isoformat()
        }
        
        info_path = models_dir / f"{model_name}_info_v1.0.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 模型資訊已儲存: {info_path}")

def analyze_feature_importance(model, feature_names, top_k=10):
    """分析特徵重要性"""
    if hasattr(model, 'feature_importances_'):
        print(f"\n📊 特徵重要性分析 (前{top_k}名):")
        
        importance_pairs = list(zip(feature_names, model.feature_importances_))
        importance_pairs.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, importance) in enumerate(importance_pairs[:top_k]):
            print(f"   {i+1:2d}. {name}: {importance:.4f}")
        
        return importance_pairs
    else:
        print("\n⚠️ 此模型不支援特徵重要性分析")
        return None

def main():
    """主程式"""
    print("🤖 簡化版模型訓練器")
    print("=" * 50)
    
    # 獲取檔案路徑
    if len(sys.argv) >= 3:
        features_file = sys.argv[1]
        targets_file = sys.argv[2]
    else:
        features_file = input("請輸入特徵檔案路徑 (預設: data/features/features_2024-06-30.csv): ").strip()
        if not features_file:
            features_file = "data/features/features_2024-06-30.csv"
        
        targets_file = input("請輸入目標變數檔案路徑 (預設: data/targets/targets_quarterly_2024-06-30.csv): ").strip()
        if not targets_file:
            targets_file = "data/targets/targets_quarterly_2024-06-30.csv"
    
    try:
        # 載入資料
        features_df, targets_df = load_data(features_file, targets_file)
        
        # 準備資料
        X, y, feature_names = prepare_data(features_df, targets_df)
        
        # 分割資料（時序分割）
        print("\n🔄 分割訓練和測試資料...")
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # 進一步分割驗證集
        X_train_split, X_val, y_train_split, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
        )
        
        print(f"   訓練集: {len(X_train_split)} 個樣本")
        print(f"   驗證集: {len(X_val)} 個樣本")
        print(f"   測試集: {len(X_test)} 個樣本")
        
        # 訓練Random Forest
        rf_model, rf_metrics = train_random_forest(X_train_split, y_train_split, X_val, y_val)
        
        # 訓練Logistic Regression
        lr_model, lr_scaler, lr_metrics = train_logistic_regression(X_train_split, y_train_split, X_val, y_val)
        
        # 測試集最終評估
        print("\n🎯 測試集最終評估:")
        
        # Random Forest測試
        rf_test_pred = rf_model.predict(X_test)
        rf_test_proba = rf_model.predict_proba(X_test)[:, 1]
        rf_test_auc = roc_auc_score(y_test, rf_test_proba)
        rf_test_f1 = f1_score(y_test, rf_test_pred)
        
        print(f"   Random Forest - AUC: {rf_test_auc:.3f}, F1: {rf_test_f1:.3f}")
        
        # Logistic Regression測試
        X_test_scaled = lr_scaler.transform(X_test)
        lr_test_pred = lr_model.predict(X_test_scaled)
        lr_test_proba = lr_model.predict_proba(X_test_scaled)[:, 1]
        lr_test_auc = roc_auc_score(y_test, lr_test_proba)
        lr_test_f1 = f1_score(y_test, lr_test_pred)
        
        print(f"   Logistic Regression - AUC: {lr_test_auc:.3f}, F1: {lr_test_f1:.3f}")
        
        # 儲存模型
        print("\n💾 儲存模型...")
        save_model(rf_model, "random_forest", feature_names=feature_names, metrics=rf_metrics)
        save_model(lr_model, "logistic_regression", scaler=lr_scaler, feature_names=feature_names, metrics=lr_metrics)
        
        # 特徵重要性分析
        analyze_feature_importance(rf_model, feature_names)
        
        print(f"\n🎉 模型訓練完成！")
        print(f"📁 模型儲存位置: models/")
        print(f"🏆 最佳模型: {'Random Forest' if rf_test_auc > lr_test_auc else 'Logistic Regression'}")
        
    except Exception as e:
        print(f"❌ 訓練失敗: {e}")
        return

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本版模型訓練器 - 使用生成的特徵進行訓練
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
import joblib

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_features(features_file):
    """載入特徵資料"""
    if not Path(features_file).exists():
        raise FileNotFoundError(f"找不到特徵檔案: {features_file}")
    
    df = pd.read_csv(features_file)
    logger.info(f"載入特徵資料: {len(df)} 筆記錄, {len(df.columns)} 個欄位")
    
    return df

def generate_targets(features_df, prediction_days=20, target_return=0.05):
    """生成目標變數 (簡化版)"""
    import sqlite3
    
    db_path = Path("../data/taiwan_stock.db")
    conn = sqlite3.connect(str(db_path))
    
    targets = []
    
    for _, row in features_df.iterrows():
        stock_id = row['stock_id']
        feature_date = row['date']
        
        try:
            # 計算目標日期範圍
            start_date = datetime.strptime(feature_date, '%Y-%m-%d') + timedelta(days=1)
            end_date = start_date + timedelta(days=prediction_days)
            
            # 獲取未來價格資料
            query = """
            SELECT close_price 
            FROM stock_prices 
            WHERE stock_id = ? AND date >= ? AND date <= ?
            ORDER BY date
            """
            
            future_prices = pd.read_sql_query(
                query, conn, 
                params=[stock_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
            )
            
            if len(future_prices) >= 10:  # 至少需要10個交易日
                # 計算最大漲幅
                base_price = future_prices['close_price'].iloc[0]
                max_price = future_prices['close_price'].max()
                max_return = (max_price - base_price) / base_price
                
                # 目標: 是否在預測期間內漲幅超過目標漲幅
                target = 1 if max_return >= target_return else 0
            else:
                target = 0  # 資料不足，標記為0
            
            targets.append({
                'stock_id': stock_id,
                'date': feature_date,
                'target': target,
                'future_return': max_return if len(future_prices) >= 10 else 0
            })
            
        except Exception as e:
            logger.warning(f"生成股票 {stock_id} 目標變數時發生錯誤: {e}")
            targets.append({
                'stock_id': stock_id,
                'date': feature_date,
                'target': 0,
                'future_return': 0
            })
    
    conn.close()
    
    targets_df = pd.DataFrame(targets)
    logger.info(f"生成目標變數: {len(targets_df)} 筆, 正樣本比例: {targets_df['target'].mean():.3f}")
    
    return targets_df

def prepare_training_data(features_df, targets_df):
    """準備訓練資料"""
    # 合併特徵和目標
    data = features_df.merge(targets_df, on=['stock_id', 'date'], how='inner')
    
    # 選擇特徵欄位 (排除非特徵欄位)
    feature_columns = [col for col in data.columns 
                      if col not in ['stock_id', 'date', 'target', 'future_return']]
    
    X = data[feature_columns]
    y = data['target']
    
    # 處理缺失值
    X = X.fillna(0)
    
    logger.info(f"訓練資料準備完成: {len(X)} 筆樣本, {len(feature_columns)} 個特徵")
    logger.info(f"特徵欄位: {feature_columns}")
    
    return X, y, feature_columns

def train_models(X, y, feature_columns):
    """訓練多個模型"""
    # 分割訓練和測試資料
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"訓練集: {len(X_train)} 筆, 測試集: {len(X_test)} 筆")
    logger.info(f"訓練集正樣本比例: {y_train.mean():.3f}")
    logger.info(f"測試集正樣本比例: {y_test.mean():.3f}")
    
    # 特徵標準化
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    models = {}
    results = {}
    
    # 1. Random Forest
    logger.info("訓練 Random Forest 模型...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42
    )
    rf_model.fit(X_train, y_train)
    
    rf_pred = rf_model.predict(X_test)
    rf_prob = rf_model.predict_proba(X_test)[:, 1]
    
    models['random_forest'] = rf_model
    results['random_forest'] = evaluate_model(y_test, rf_pred, rf_prob, "Random Forest")
    
    # 2. Logistic Regression
    logger.info("訓練 Logistic Regression 模型...")
    lr_model = LogisticRegression(
        random_state=42,
        max_iter=1000
    )
    lr_model.fit(X_train_scaled, y_train)
    
    lr_pred = lr_model.predict(X_test_scaled)
    lr_prob = lr_model.predict_proba(X_test_scaled)[:, 1]
    
    models['logistic_regression'] = lr_model
    results['logistic_regression'] = evaluate_model(y_test, lr_pred, lr_prob, "Logistic Regression")
    
    # 保存模型和標準化器
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)
    
    joblib.dump(rf_model, model_dir / "random_forest_basic.pkl")
    joblib.dump(lr_model, model_dir / "logistic_regression_basic.pkl")
    joblib.dump(scaler, model_dir / "scaler_basic.pkl")
    
    # 保存特徵名稱
    feature_info = {
        'feature_columns': feature_columns,
        'n_features': len(feature_columns)
    }
    joblib.dump(feature_info, model_dir / "feature_info_basic.pkl")
    
    logger.info(f"模型已保存到 {model_dir}")
    
    return models, results, scaler

def evaluate_model(y_true, y_pred, y_prob, model_name):
    """評估模型性能"""
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    try:
        auc = roc_auc_score(y_true, y_prob)
    except ValueError:
        auc = 0.5  # 如果只有一個類別
    
    results = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'auc': auc
    }
    
    logger.info(f"{model_name} 性能:")
    logger.info(f"  準確率: {accuracy:.4f}")
    logger.info(f"  精確率: {precision:.4f}")
    logger.info(f"  召回率: {recall:.4f}")
    logger.info(f"  F1分數: {f1:.4f}")
    logger.info(f"  AUC: {auc:.4f}")
    
    return results

def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("使用方法: python simple_train_basic.py <features_file>")
        print("範例: python simple_train_basic.py data/features/features_basic_2024-06-30.csv")
        sys.exit(1)
    
    features_file = sys.argv[1]
    
    print("基本版模型訓練器")
    print("=" * 50)
    print(f"特徵檔案: {features_file}")
    
    try:
        # 1. 載入特徵
        features_df = load_features(features_file)
        
        # 2. 生成目標變數
        print("\n生成目標變數...")
        targets_df = generate_targets(features_df)
        
        # 3. 準備訓練資料
        print("\n準備訓練資料...")
        X, y, feature_columns = prepare_training_data(features_df, targets_df)
        
        if len(X) == 0:
            print("錯誤: 沒有可用的訓練資料")
            return
        
        # 4. 訓練模型
        print("\n開始訓練模型...")
        models, results, scaler = train_models(X, y, feature_columns)
        
        # 5. 總結結果
        print("\n" + "=" * 50)
        print("訓練完成！")
        print("=" * 50)
        
        print("\n模型性能比較:")
        for model_name, result in results.items():
            print(f"\n{model_name}:")
            print(f"  準確率: {result['accuracy']:.4f}")
            print(f"  F1分數: {result['f1']:.4f}")
            print(f"  AUC: {result['auc']:.4f}")
        
        # 推薦最佳模型
        best_model = max(results.keys(), key=lambda k: results[k]['f1'])
        print(f"\n推薦模型: {best_model} (F1分數: {results[best_model]['f1']:.4f})")
        
        print(f"\n模型檔案已保存到 models/ 目錄")
        print("\n下一步可以執行:")
        print("python simple_predict_basic.py <stock_id>")
        
    except Exception as e:
        logger.error(f"訓練過程發生錯誤: {e}")
        print(f"錯誤: {e}")

if __name__ == "__main__":
    main()

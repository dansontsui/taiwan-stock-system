#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比較完整特徵 vs 簡易特徵的預測準確度
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('feature_comparison.log')
    ]
)

def load_and_prepare_data(features_file, targets_file):
    """載入和準備資料"""
    try:
        # 載入特徵資料
        features_df = pd.read_csv(features_file)
        targets_df = pd.read_csv(targets_file)
        
        logging.info(f"特徵資料: {len(features_df)} 筆, {len(features_df.columns)} 個欄位")
        logging.info(f"目標資料: {len(targets_df)} 筆")
        
        # 合併資料
        merged_df = pd.merge(
            features_df, 
            targets_df[['stock_id', 'feature_date', 'target']], 
            on=['stock_id', 'feature_date'], 
            how='inner'
        )
        
        logging.info(f"合併後資料: {len(merged_df)} 筆")
        
        # 分離特徵和目標
        feature_cols = [col for col in merged_df.columns if col not in ['stock_id', 'feature_date', 'target']]
        X = merged_df[feature_cols]
        y = merged_df['target']
        
        # 處理缺失值
        X = X.fillna(X.median())
        
        logging.info(f"特徵數量: {len(feature_cols)}")
        logging.info(f"特徵欄位: {feature_cols}")
        
        return X, y, feature_cols
        
    except Exception as e:
        logging.error(f"資料載入失敗: {e}")
        return None, None, None

def evaluate_model(model, X_test, y_test, model_name):
    """評估模型性能"""
    try:
        # 預測
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        # 計算指標
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba) if y_pred_proba is not None else None
        
        results = {
            'model': model_name,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'auc_score': auc
        }
        
        logging.info(f"{model_name} 結果:")
        logging.info(f"  準確率: {accuracy:.4f}")
        logging.info(f"  精確率: {precision:.4f}")
        logging.info(f"  召回率: {recall:.4f}")
        logging.info(f"  F1分數: {f1:.4f}")
        if auc:
            logging.info(f"  AUC分數: {auc:.4f}")
        
        return results
        
    except Exception as e:
        logging.error(f"{model_name} 評估失敗: {e}")
        return None

def compare_features():
    """比較不同特徵系統的性能"""
    
    # 檢查檔案是否存在
    simple_features = "data/features/features_basic_2024-06-30.csv"
    full_features = "data/features/features_2024-06-30.csv"
    targets_file = "data/targets/targets_monthly_2024-06-30.csv"
    
    results = []
    
    # 測試簡易特徵
    if Path(simple_features).exists():
        logging.info("=" * 60)
        logging.info("測試簡易特徵系統 (16個特徵)")
        logging.info("=" * 60)
        
        X_simple, y_simple, simple_cols = load_and_prepare_data(simple_features, targets_file)
        
        if X_simple is not None:
            # 分割資料
            X_train, X_test, y_train, y_test = train_test_split(
                X_simple, y_simple, test_size=0.2, random_state=42, stratify=y_simple
            )
            
            # 標準化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Random Forest
            rf_simple = RandomForestClassifier(n_estimators=100, random_state=42)
            rf_simple.fit(X_train, y_train)
            rf_results = evaluate_model(rf_simple, X_test, y_test, "簡易特徵 - Random Forest")
            if rf_results:
                rf_results['feature_type'] = 'simple'
                rf_results['feature_count'] = len(simple_cols)
                results.append(rf_results)
            
            # Logistic Regression
            lr_simple = LogisticRegression(random_state=42, max_iter=1000)
            lr_simple.fit(X_train_scaled, y_train)
            lr_results = evaluate_model(lr_simple, X_test_scaled, y_test, "簡易特徵 - Logistic Regression")
            if lr_results:
                lr_results['feature_type'] = 'simple'
                lr_results['feature_count'] = len(simple_cols)
                results.append(lr_results)
    
    # 測試完整特徵
    if Path(full_features).exists():
        logging.info("=" * 60)
        logging.info("測試完整特徵系統 (30個特徵)")
        logging.info("=" * 60)
        
        X_full, y_full, full_cols = load_and_prepare_data(full_features, targets_file)
        
        if X_full is not None:
            # 分割資料
            X_train, X_test, y_train, y_test = train_test_split(
                X_full, y_full, test_size=0.2, random_state=42, stratify=y_full
            )
            
            # 標準化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Random Forest
            rf_full = RandomForestClassifier(n_estimators=100, random_state=42)
            rf_full.fit(X_train, y_train)
            rf_results = evaluate_model(rf_full, X_test, y_test, "完整特徵 - Random Forest")
            if rf_results:
                rf_results['feature_type'] = 'full'
                rf_results['feature_count'] = len(full_cols)
                results.append(rf_results)
            
            # Logistic Regression
            lr_full = LogisticRegression(random_state=42, max_iter=1000)
            lr_full.fit(X_train_scaled, y_train)
            lr_results = evaluate_model(lr_full, X_test_scaled, y_test, "完整特徵 - Logistic Regression")
            if lr_results:
                lr_results['feature_type'] = 'full'
                lr_results['feature_count'] = len(full_cols)
                results.append(lr_results)
    
    # 生成比較報告
    if results:
        results_df = pd.DataFrame(results)
        
        logging.info("=" * 60)
        logging.info("特徵系統比較結果")
        logging.info("=" * 60)
        
        print("\n特徵系統性能比較:")
        print(results_df.to_string(index=False))
        
        # 保存結果
        results_df.to_csv('feature_comparison_results.csv', index=False)
        logging.info("比較結果已保存到: feature_comparison_results.csv")
        
        # 分析結論
        logging.info("\n分析結論:")
        simple_avg = results_df[results_df['feature_type'] == 'simple']['accuracy'].mean()
        full_avg = results_df[results_df['feature_type'] == 'full']['accuracy'].mean()
        
        logging.info(f"簡易特徵平均準確率: {simple_avg:.4f}")
        logging.info(f"完整特徵平均準確率: {full_avg:.4f}")
        
        if full_avg > simple_avg:
            improvement = (full_avg - simple_avg) / simple_avg * 100
            logging.info(f"完整特徵比簡易特徵準確率提升: {improvement:.2f}%")
        else:
            decline = (simple_avg - full_avg) / simple_avg * 100
            logging.info(f"簡易特徵比完整特徵準確率更好: {decline:.2f}%")

if __name__ == "__main__":
    compare_features()

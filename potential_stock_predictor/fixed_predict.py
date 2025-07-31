#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復版股票預測器 - 解決編碼和相容性問題
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import joblib

def load_models():
    """載入訓練好的模型"""
    model_dir = Path("models")
    
    if not model_dir.exists():
        print("錯誤: 找不到模型目錄，請先執行訓練")
        return None, None, None
    
    models = {}
    
    # 載入基本版模型 (相容性更好)
    rf_path = model_dir / "random_forest_basic.pkl"
    lr_path = model_dir / "logistic_regression_basic.pkl"
    scaler_path = model_dir / "scaler_basic.pkl"
    feature_info_path = model_dir / "feature_info_basic.pkl"
    
    try:
        if rf_path.exists():
            models['random_forest'] = joblib.load(rf_path)
            print("成功載入 Random Forest 模型")
        
        if lr_path.exists():
            models['logistic_regression'] = joblib.load(lr_path)
            print("成功載入 Logistic Regression 模型")
        
        scaler = joblib.load(scaler_path) if scaler_path.exists() else None
        feature_info = joblib.load(feature_info_path) if feature_info_path.exists() else None
        
        if feature_info:
            print(f"載入特徵資訊: {feature_info['n_features']} 個特徵")
        
        return models, scaler, feature_info
        
    except Exception as e:
        print(f"載入模型時發生錯誤: {e}")
        return None, None, None

def predict_stock(stock_id, models, scaler, feature_info):
    """預測單一股票"""
    features_file = "data/features/features_basic_2024-06-30.csv"
    
    if not Path(features_file).exists():
        print(f"錯誤: 找不到特徵檔案 {features_file}")
        return None
    
    try:
        features_df = pd.read_csv(features_file)
        features_df['stock_id'] = features_df['stock_id'].astype(str)
        
        # 找到指定股票
        stock_data = features_df[features_df['stock_id'] == str(stock_id)]
        
        if len(stock_data) == 0:
            print(f"錯誤: 找不到股票 {stock_id} 的特徵資料")
            print(f"可用股票: {sorted(features_df['stock_id'].tolist())}")
            return None
        
        # 準備特徵
        feature_columns = feature_info['feature_columns']
        X = stock_data[feature_columns].fillna(0)
        
        print(f"\n股票 {stock_id} 預測結果")
        print("=" * 50)
        
        # 使用各個模型進行預測
        for model_name, model in models.items():
            try:
                if model_name == 'logistic_regression' and scaler is not None:
                    X_scaled = scaler.transform(X)
                    prob = model.predict_proba(X_scaled)[0, 1]
                    pred = model.predict(X_scaled)[0]
                else:
                    prob = model.predict_proba(X)[0, 1]
                    pred = model.predict(X)[0]
                
                prediction = "看漲" if pred == 1 else "看跌"
                confidence = "High" if prob > 0.7 or prob < 0.3 else "Medium"
                
                print(f"\n{model_name}:")
                print(f"  預測結果: {prediction}")
                print(f"  預測機率: {prob:.3f}")
                print(f"  信心度: {confidence}")
                
            except Exception as e:
                print(f"  {model_name} 預測失敗: {e}")
        
        # 顯示關鍵特徵
        print(f"\n關鍵特徵 (股票 {stock_id}):")
        print("-" * 30)
        
        key_features = [
            'price_vs_ma_20', 'rsi_14', 'revenue_yoy_growth', 
            'momentum_20', 'volume_vs_ma_20'
        ]
        
        stock_row = stock_data.iloc[0]
        for feature in key_features:
            if feature in stock_row:
                value = stock_row[feature]
                print(f"  {feature}: {value:.4f}")
        
        return True
        
    except Exception as e:
        print(f"預測過程發生錯誤: {e}")
        return None

def generate_ranking(models, scaler, feature_info, top_k=20):
    """生成潛力股排行榜"""
    features_file = "data/features/features_basic_2024-06-30.csv"
    
    if not Path(features_file).exists():
        print(f"錯誤: 找不到特徵檔案 {features_file}")
        return None
    
    try:
        features_df = pd.read_csv(features_file)
        
        # 準備特徵
        feature_columns = feature_info['feature_columns']
        X = features_df[feature_columns].fillna(0)
        
        # 使用 Random Forest 進行預測
        if 'random_forest' in models:
            model = models['random_forest']
            probabilities = model.predict_proba(X)[:, 1]
        elif 'logistic_regression' in models:
            model = models['logistic_regression']
            X_scaled = scaler.transform(X) if scaler else X
            probabilities = model.predict_proba(X_scaled)[:, 1]
        else:
            print("錯誤: 沒有可用的模型")
            return None
        
        # 創建結果
        results = features_df[['stock_id', 'date']].copy()
        results['probability'] = probabilities
        results['prediction'] = (probabilities > 0.5).astype(int)
        
        # 排序並取前K名
        top_stocks = results.nlargest(top_k, 'probability')
        
        print(f"\nTOP {top_k} 潛力股排行榜")
        print("=" * 60)
        print(f"{'排名':>4} {'股票代碼':>8} {'預測機率':>10} {'預測結果':>8}")
        print("-" * 60)
        
        for i, (_, row) in enumerate(top_stocks.iterrows(), 1):
            stock_id = row['stock_id']
            probability = row['probability']
            prediction = "看漲" if row['prediction'] == 1 else "看跌"
            
            print(f"{i:>4} {stock_id:>8} {probability:>9.3f} {prediction:>8}")
        
        # 保存結果
        output_file = f"data/predictions/ranking_top_{top_k}_fixed.csv"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        top_stocks.to_csv(output_file, index=False)
        print(f"\n排行榜已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"生成排行榜時發生錯誤: {e}")
        return None

def main():
    """主程式"""
    print("修復版股票預測器")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  預測單一股票: python fixed_predict.py <stock_id>")
        print("  生成排行榜: python fixed_predict.py ranking [top_k]")
        print("\n範例:")
        print("  python fixed_predict.py 8299")
        print("  python fixed_predict.py ranking 20")
        sys.exit(1)
    
    # 載入模型
    print("載入模型...")
    models, scaler, feature_info = load_models()
    
    if not models or not feature_info:
        print("錯誤: 無法載入模型或特徵資訊")
        return
    
    command = sys.argv[1]
    
    if command == "ranking":
        # 生成排行榜
        top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        print(f"\n生成 TOP {top_k} 潛力股排行榜...")
        generate_ranking(models, scaler, feature_info, top_k)
        
    else:
        # 預測單一股票
        stock_id = command
        print(f"\n預測股票: {stock_id}")
        predict_stock(stock_id, models, scaler, feature_info)

if __name__ == "__main__":
    main()

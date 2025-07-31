#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本版股票預測器 - 使用訓練好的模型進行預測
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import joblib

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_models():
    """載入訓練好的模型"""
    model_dir = Path("models")
    
    if not model_dir.exists():
        raise FileNotFoundError("找不到模型目錄，請先執行訓練")
    
    models = {}
    
    # 載入模型
    rf_path = model_dir / "random_forest_basic.pkl"
    lr_path = model_dir / "logistic_regression_basic.pkl"
    scaler_path = model_dir / "scaler_basic.pkl"
    feature_info_path = model_dir / "feature_info_basic.pkl"
    
    if rf_path.exists():
        models['random_forest'] = joblib.load(rf_path)
        logger.info("載入 Random Forest 模型")
    
    if lr_path.exists():
        models['logistic_regression'] = joblib.load(lr_path)
        logger.info("載入 Logistic Regression 模型")
    
    if scaler_path.exists():
        scaler = joblib.load(scaler_path)
        logger.info("載入特徵標準化器")
    else:
        scaler = None
    
    if feature_info_path.exists():
        feature_info = joblib.load(feature_info_path)
        logger.info(f"載入特徵資訊: {feature_info['n_features']} 個特徵")
    else:
        feature_info = None
    
    return models, scaler, feature_info

def predict_single_stock(stock_id, models, scaler, feature_info):
    """預測單一股票"""
    # 這裡應該生成該股票的最新特徵
    # 為了演示，我們使用已有的特徵檔案
    features_file = "data/features/features_basic_2024-06-30.csv"
    
    if not Path(features_file).exists():
        raise FileNotFoundError(f"找不到特徵檔案: {features_file}")
    
    features_df = pd.read_csv(features_file)
    
    # 找到指定股票 (確保資料類型一致)
    features_df['stock_id'] = features_df['stock_id'].astype(str)
    stock_data = features_df[features_df['stock_id'] == str(stock_id)]
    
    if len(stock_data) == 0:
        raise ValueError(f"找不到股票 {stock_id} 的特徵資料")
    
    # 準備特徵
    feature_columns = feature_info['feature_columns']
    X = stock_data[feature_columns].fillna(0)
    
    predictions = {}
    
    # 使用各個模型進行預測
    for model_name, model in models.items():
        if model_name == 'logistic_regression' and scaler is not None:
            X_scaled = scaler.transform(X)
            prob = model.predict_proba(X_scaled)[0, 1]
            pred = model.predict(X_scaled)[0]
        else:
            prob = model.predict_proba(X)[0, 1]
            pred = model.predict(X)[0]
        
        predictions[model_name] = {
            'prediction': pred,
            'probability': prob,
            'confidence': 'High' if prob > 0.7 or prob < 0.3 else 'Medium'
        }
    
    return predictions, stock_data.iloc[0]

def generate_ranking(models, scaler, feature_info, top_k=20):
    """生成潛力股排行榜"""
    features_file = "data/features/features_basic_2024-06-30.csv"
    
    if not Path(features_file).exists():
        raise FileNotFoundError(f"找不到特徵檔案: {features_file}")
    
    features_df = pd.read_csv(features_file)
    
    # 準備特徵
    feature_columns = feature_info['feature_columns']
    X = features_df[feature_columns].fillna(0)
    
    # 使用最佳模型進行預測 (這裡使用 Random Forest)
    if 'random_forest' in models:
        model = models['random_forest']
        probabilities = model.predict_proba(X)[:, 1]
    elif 'logistic_regression' in models:
        model = models['logistic_regression']
        X_scaled = scaler.transform(X) if scaler else X
        probabilities = model.predict_proba(X_scaled)[:, 1]
    else:
        raise ValueError("沒有可用的模型")
    
    # 創建結果DataFrame
    results = features_df[['stock_id', 'date']].copy()
    results['probability'] = probabilities
    results['prediction'] = (probabilities > 0.5).astype(int)
    
    # 排序並取前K名
    top_stocks = results.nlargest(top_k, 'probability')
    
    return top_stocks

def main():
    """主程式"""
    print("基本版股票預測器")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  預測單一股票: python simple_predict_basic.py <stock_id>")
        print("  生成排行榜: python simple_predict_basic.py ranking [top_k]")
        print("\n範例:")
        print("  python simple_predict_basic.py 2330")
        print("  python simple_predict_basic.py ranking 20")
        sys.exit(1)
    
    try:
        # 載入模型
        print("載入模型...")
        models, scaler, feature_info = load_models()
        
        if len(models) == 0:
            print("錯誤: 沒有找到訓練好的模型")
            return
        
        command = sys.argv[1]
        
        if command == "ranking":
            # 生成排行榜
            top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            
            print(f"\n生成 TOP {top_k} 潛力股排行榜...")
            ranking = generate_ranking(models, scaler, feature_info, top_k)
            
            print(f"\nTOP {top_k} 潛力股排行榜")
            print("=" * 60)
            print(f"{'排名':>4} {'股票代碼':>8} {'預測機率':>10} {'預測結果':>8}")
            print("-" * 60)
            
            for i, (_, row) in enumerate(ranking.iterrows(), 1):
                stock_id = row['stock_id']
                probability = row['probability']
                prediction = "看漲" if row['prediction'] == 1 else "看跌"
                
                print(f"{i:>4} {stock_id:>8} {probability:>9.3f} {prediction:>8}")
            
            # 保存結果
            output_file = f"data/predictions/ranking_top_{top_k}_basic.csv"
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            ranking.to_csv(output_file, index=False)
            print(f"\n排行榜已保存到: {output_file}")
            
        else:
            # 預測單一股票
            stock_id = command
            
            print(f"\n預測股票: {stock_id}")
            predictions, stock_features = predict_single_stock(
                stock_id, models, scaler, feature_info
            )
            
            print(f"\n股票 {stock_id} 預測結果")
            print("=" * 50)
            
            for model_name, result in predictions.items():
                prediction = "看漲" if result['prediction'] == 1 else "看跌"
                probability = result['probability']
                confidence = result['confidence']
                
                print(f"\n{model_name}:")
                print(f"  預測結果: {prediction}")
                print(f"  預測機率: {probability:.3f}")
                print(f"  信心度: {confidence}")
            
            # 顯示關鍵特徵
            print(f"\n關鍵特徵 (股票 {stock_id}):")
            print("-" * 30)
            key_features = [
                'price_vs_ma_20', 'rsi_14', 'revenue_yoy_growth', 
                'momentum_20', 'volume_vs_ma_20'
            ]
            
            for feature in key_features:
                if feature in stock_features:
                    value = stock_features[feature]
                    print(f"  {feature}: {value:.4f}")
    
    except Exception as e:
        logger.error(f"預測過程發生錯誤: {e}")
        print(f"錯誤: {e}")

if __name__ == "__main__":
    main()

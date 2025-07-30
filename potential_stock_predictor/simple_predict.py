#!/usr/bin/env python3
"""
簡化版預測器

使用訓練好的模型進行潛力股預測
"""

import sys
import os
import pandas as pd
import numpy as np
import pickle
import json
import sqlite3
from datetime import datetime
from pathlib import Path

def load_model(model_name):
    """載入訓練好的模型"""
    models_dir = Path("models")
    
    # 載入模型
    model_path = models_dir / f"{model_name}_v1.0.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"找不到模型檔案: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # 載入scaler（如果有）
    scaler = None
    scaler_path = models_dir / f"{model_name}_scaler_v1.0.pkl"
    if scaler_path.exists():
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
    
    # 載入模型資訊
    info_path = models_dir / f"{model_name}_info_v1.0.json"
    feature_names = None
    if info_path.exists():
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
            feature_names = info.get('feature_names', [])
    
    return model, scaler, feature_names

def connect_database():
    """連接資料庫"""
    db_path = Path("../data/taiwan_stock.db")
    if not db_path.exists():
        raise FileNotFoundError(f"找不到資料庫檔案: {db_path}")
    
    return sqlite3.connect(str(db_path))

def get_stock_list():
    """獲取股票清單"""
    conn = connect_database()
    
    query = """
    SELECT stock_id, stock_name, market, industry
    FROM stocks 
    WHERE is_active = 1 AND stock_id NOT LIKE '00%'
    ORDER BY stock_id
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 過濾只包含數字的股票代碼
    df = df[df['stock_id'].str.isdigit()]
    
    return df

def load_latest_features():
    """載入最新的特徵資料"""
    features_dir = Path("data/features")
    
    # 找到最新的特徵檔案
    feature_files = list(features_dir.glob("features_*.csv"))
    if not feature_files:
        raise FileNotFoundError("找不到特徵檔案")
    
    latest_file = max(feature_files, key=lambda x: x.stat().st_mtime)
    print(f"📊 載入特徵檔案: {latest_file}")
    
    features_df = pd.read_csv(latest_file)
    return features_df

def prepare_features_for_prediction(features_df, feature_names):
    """為預測準備特徵"""
    # 移除非特徵欄位
    feature_columns = [col for col in features_df.columns 
                      if col not in ['stock_id', 'feature_date']]
    
    X = features_df[feature_columns].copy()
    
    # 處理缺失值
    X = X.fillna(0)
    
    # 確保特徵順序與訓練時一致
    if feature_names:
        # 添加缺失的特徵（填充為0）
        for feature in feature_names:
            if feature not in X.columns:
                X[feature] = 0
        
        # 重新排序特徵
        X = X[feature_names]
    
    return X

def predict_stocks(model_name="random_forest", top_k=20):
    """預測潛力股"""
    print(f"🔮 使用 {model_name} 模型進行預測...")
    
    # 載入模型
    model, scaler, feature_names = load_model(model_name)
    print(f"   ✅ 模型載入成功")
    
    # 載入特徵資料
    features_df = load_latest_features()
    print(f"   ✅ 特徵資料: {len(features_df)} 個股票")
    
    # 準備特徵
    X = prepare_features_for_prediction(features_df, feature_names)
    
    # 應用scaler（如果有）
    if scaler:
        X = scaler.transform(X)
    
    # 進行預測
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]
    
    # 創建結果DataFrame
    results_df = pd.DataFrame({
        'stock_id': features_df['stock_id'],
        'feature_date': features_df['feature_date'],
        'prediction': predictions,
        'probability': probabilities
    })
    
    # 獲取股票基本資訊
    stock_list = get_stock_list()

    # 確保stock_id類型一致
    results_df['stock_id'] = results_df['stock_id'].astype(str)
    stock_list['stock_id'] = stock_list['stock_id'].astype(str)

    results_df = results_df.merge(
        stock_list[['stock_id', 'stock_name', 'market', 'industry']],
        on='stock_id',
        how='left'
    )
    
    # 按機率排序
    results_df = results_df.sort_values('probability', ascending=False)
    
    # 統計結果
    total_stocks = len(results_df)
    predicted_positive = (results_df['prediction'] == 1).sum()
    
    print(f"   ✅ 預測完成")
    print(f"   📊 總股票數: {total_stocks}")
    print(f"   🎯 預測為潛力股: {predicted_positive} ({predicted_positive/total_stocks:.1%})")
    print(f"   📈 平均預測機率: {results_df['probability'].mean():.3f}")
    
    return results_df.head(top_k)

def save_predictions(predictions_df, model_name):
    """儲存預測結果"""
    predictions_dir = Path("data/predictions")
    predictions_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = predictions_dir / f"predictions_{model_name}_{timestamp}.csv"
    
    predictions_df.to_csv(output_file, index=False)
    print(f"   ✅ 預測結果已儲存: {output_file}")
    
    return output_file

def generate_ranking(model_name="random_forest", top_k=20):
    """生成潛力股排行榜"""
    print(f"🏆 生成潛力股排行榜 (TOP {top_k})")
    print("=" * 50)
    
    # 執行預測
    ranking_df = predict_stocks(model_name, top_k)
    
    # 儲存結果
    rankings_dir = Path("data/rankings")
    rankings_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = rankings_dir / f"ranking_{model_name}_{timestamp}.csv"
    ranking_df.to_csv(output_file, index=False)
    
    # 顯示排行榜
    print(f"\n🎯 潛力股排行榜 (TOP {len(ranking_df)}):")
    print("=" * 80)
    print(f"{'排名':>4} {'股票代碼':>8} {'股票名稱':<12} {'預測機率':>8} {'預測結果':>8} {'市場':>6}")
    print("-" * 80)
    
    for i, (_, row) in enumerate(ranking_df.iterrows()):
        rank = i + 1
        stock_id = row['stock_id']
        stock_name = row['stock_name'][:10] if pd.notna(row['stock_name']) else 'N/A'
        probability = row['probability']
        prediction = "看漲" if row['prediction'] == 1 else "看跌"
        market = row['market'] if pd.notna(row['market']) else 'N/A'
        
        print(f"{rank:>4} {stock_id:>8} {stock_name:<12} {probability:>8.3f} {prediction:>8} {market:>6}")
    
    print("=" * 80)
    print(f"📁 完整結果已儲存: {output_file}")
    
    return ranking_df, output_file

def predict_specific_stocks(stock_ids, model_name="random_forest"):
    """預測特定股票"""
    print(f"🎯 預測特定股票: {', '.join(stock_ids)}")
    print("=" * 50)
    
    # 載入模型
    model, scaler, feature_names = load_model(model_name)
    
    # 載入特徵資料
    features_df = load_latest_features()
    
    # 過濾指定股票
    target_features = features_df[features_df['stock_id'].isin(stock_ids)]
    
    if target_features.empty:
        print("❌ 找不到指定股票的特徵資料")
        return None
    
    # 準備特徵
    X = prepare_features_for_prediction(target_features, feature_names)
    
    # 應用scaler（如果有）
    if scaler:
        X = scaler.transform(X)
    
    # 進行預測
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]
    
    # 創建結果
    results = []
    for i, (_, row) in enumerate(target_features.iterrows()):
        results.append({
            'stock_id': row['stock_id'],
            'prediction': "看漲" if predictions[i] == 1 else "看跌",
            'probability': probabilities[i],
            'confidence': "高" if probabilities[i] > 0.7 or probabilities[i] < 0.3 else "中"
        })
    
    # 顯示結果
    print(f"📊 預測結果:")
    print("-" * 50)
    for result in results:
        print(f"   {result['stock_id']}: {result['prediction']} (機率: {result['probability']:.3f}, 信心: {result['confidence']})")
    
    return results

def main():
    """主程式"""
    print("🔮 簡化版預測器")
    print("=" * 50)
    
    # 檢查可用模型
    models_dir = Path("models")
    available_models = []
    for model_file in models_dir.glob("*_v1.0.pkl"):
        model_name = model_file.stem.replace("_v1.0", "")
        if not model_name.endswith("_scaler"):
            available_models.append(model_name)
    
    if not available_models:
        print("❌ 找不到訓練好的模型")
        print("請先執行模型訓練: python simple_train.py")
        return
    
    print(f"📋 可用模型: {', '.join(available_models)}")
    
    # 獲取參數
    if len(sys.argv) >= 2:
        action = sys.argv[1]
        model_name = sys.argv[2] if len(sys.argv) >= 3 else "random_forest"
        top_k = int(sys.argv[3]) if len(sys.argv) >= 4 else 20
    else:
        print("\n請選擇功能:")
        print("1. 生成潛力股排行榜")
        print("2. 預測特定股票")
        choice = input("請輸入選擇 (1-2): ").strip()
        action = "ranking" if choice == "1" else "specific"

        # 選擇模型
        model_name = input(f"請選擇模型 ({'/'.join(available_models)}, 預設: random_forest): ").strip()
        if not model_name:
            model_name = "random_forest"

        top_k = 20
    
    try:
        if action == "ranking":
            if len(sys.argv) < 4:  # 如果沒有通過命令列參數指定
                top_k_input = input("請輸入排行榜數量 (預設: 20): ").strip()
                top_k = int(top_k_input) if top_k_input else 20

            ranking_df, output_file = generate_ranking(model_name, top_k)
            
        elif action == "specific":
            stock_ids_input = input("請輸入股票代碼 (逗號分隔): ").strip()
            stock_ids = [s.strip() for s in stock_ids_input.split(',')]
            
            results = predict_specific_stocks(stock_ids, model_name)
            
        else:
            print("❌ 無效的功能選擇")
    
    except Exception as e:
        print(f"❌ 預測失敗: {e}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
潛力股預測系統基本示範程式

使用基本機器學習模型，不依賴 LightGBM/XGBoost
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加當前目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_basic_prediction():
    """測試基本預測功能"""
    print("🤖 測試基本機器學習預測...")
    
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        # 創建模擬的股票特徵資料
        np.random.seed(42)
        n_samples = 1000
        n_features = 20
        
        # 生成特徵
        features = np.random.randn(n_samples, n_features)
        
        # 添加一些有意義的特徵
        features[:, 0] = np.random.normal(0.02, 0.1, n_samples)  # 月營收成長率
        features[:, 1] = np.random.normal(0.15, 0.05, n_samples)  # ROE
        features[:, 2] = np.random.normal(0.3, 0.1, n_samples)   # 毛利率
        features[:, 3] = np.random.normal(0.02, 0.05, n_samples)  # 波動率
        
        # 生成目標變數（20日內上漲超過5%）
        # 簡單規則：ROE高且波動率低的股票更可能上漲
        target_prob = 1 / (1 + np.exp(-(features[:, 1] * 5 - features[:, 3] * 10 + features[:, 0] * 3)))
        targets = np.random.binomial(1, target_prob, n_samples)
        
        print(f"   📊 生成模擬資料: {n_samples} 個樣本, {n_features} 個特徵")
        print(f"   🎯 正樣本比例: {targets.mean():.2%}")
        
        # 分割資料
        X_train, X_test, y_train, y_test = train_test_split(
            features, targets, test_size=0.2, random_state=42, stratify=targets
        )
        
        # 測試 Random Forest
        print("\n   🌲 測試 Random Forest 模型...")
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_train, y_train)
        rf_pred = rf_model.predict(X_test)
        
        rf_metrics = {
            'accuracy': accuracy_score(y_test, rf_pred),
            'precision': precision_score(y_test, rf_pred),
            'recall': recall_score(y_test, rf_pred),
            'f1_score': f1_score(y_test, rf_pred)
        }
        
        print(f"      準確率: {rf_metrics['accuracy']:.3f}")
        print(f"      精確率: {rf_metrics['precision']:.3f}")
        print(f"      召回率: {rf_metrics['recall']:.3f}")
        print(f"      F1分數: {rf_metrics['f1_score']:.3f}")
        
        # 測試 Logistic Regression
        print("\n   📈 測試 Logistic Regression 模型...")
        lr_model = LogisticRegression(random_state=42, max_iter=1000)
        lr_model.fit(X_train, y_train)
        lr_pred = lr_model.predict(X_test)
        
        lr_metrics = {
            'accuracy': accuracy_score(y_test, lr_pred),
            'precision': precision_score(y_test, lr_pred),
            'recall': recall_score(y_test, lr_pred),
            'f1_score': f1_score(y_test, lr_pred)
        }
        
        print(f"      準確率: {lr_metrics['accuracy']:.3f}")
        print(f"      精確率: {lr_metrics['precision']:.3f}")
        print(f"      召回率: {lr_metrics['recall']:.3f}")
        print(f"      F1分數: {lr_metrics['f1_score']:.3f}")
        
        # 特徵重要性分析
        print("\n   📊 特徵重要性分析 (Random Forest):")
        feature_names = [
            '月營收成長率', 'ROE', '毛利率', '波動率', '特徵5', '特徵6', '特徵7', '特徵8', 
            '特徵9', '特徵10', '特徵11', '特徵12', '特徵13', '特徵14', '特徵15', 
            '特徵16', '特徵17', '特徵18', '特徵19', '特徵20'
        ]
        
        importance_pairs = list(zip(feature_names, rf_model.feature_importances_))
        importance_pairs.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, importance) in enumerate(importance_pairs[:5]):
            print(f"      {i+1}. {name}: {importance:.3f}")
        
        # 生成預測排行榜
        print("\n   🏆 生成潛力股預測排行榜...")
        
        # 使用測試集生成預測機率
        rf_proba = rf_model.predict_proba(X_test)[:, 1]
        lr_proba = lr_model.predict_proba(X_test)[:, 1]
        
        # 組合預測（簡單平均）
        ensemble_proba = (rf_proba + lr_proba) / 2
        
        # 創建排行榜
        ranking_data = pd.DataFrame({
            'stock_id': [f'TEST{i:04d}' for i in range(len(X_test))],
            'rf_probability': rf_proba,
            'lr_probability': lr_proba,
            'ensemble_probability': ensemble_proba,
            'actual_target': y_test
        })
        
        # 按組合機率排序
        ranking_data = ranking_data.sort_values('ensemble_probability', ascending=False)
        
        print("      前10名潛力股預測:")
        print("      排名  股票代碼  RF機率  LR機率  組合機率  實際結果")
        print("      " + "="*50)
        
        for i, (_, row) in enumerate(ranking_data.head(10).iterrows()):
            actual = "✅" if row['actual_target'] == 1 else "❌"
            print(f"      {i+1:2d}   {row['stock_id']}   {row['rf_probability']:.3f}   "
                  f"{row['lr_probability']:.3f}    {row['ensemble_probability']:.3f}     {actual}")
        
        # 計算前10名的準確率
        top10_accuracy = ranking_data.head(10)['actual_target'].mean()
        print(f"\n      前10名準確率: {top10_accuracy:.1%}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 基本預測測試失敗: {e}")
        return False

def test_technical_indicators():
    """測試技術指標計算"""
    print("\n📈 測試技術指標計算...")
    
    try:
        # 生成模擬股價資料
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        
        # 生成隨機遊走股價
        returns = np.random.normal(0.001, 0.02, 100)
        prices = 100 * np.exp(np.cumsum(returns))
        
        # 添加一些噪音
        high_prices = prices * (1 + np.random.uniform(0, 0.02, 100))
        low_prices = prices * (1 - np.random.uniform(0, 0.02, 100))
        volumes = np.random.randint(1000, 10000, 100)
        
        stock_data = pd.DataFrame({
            'date': dates,
            'close_price': prices,
            'high_price': high_prices,
            'low_price': low_prices,
            'volume': volumes
        })
        
        print(f"   📊 生成模擬股價資料: {len(stock_data)} 個交易日")
        
        # 計算移動平均
        stock_data['ma_5'] = stock_data['close_price'].rolling(window=5).mean()
        stock_data['ma_20'] = stock_data['close_price'].rolling(window=20).mean()
        
        # 計算報酬率
        stock_data['returns'] = stock_data['close_price'].pct_change()
        
        # 計算波動率
        stock_data['volatility'] = stock_data['returns'].rolling(window=20).std() * np.sqrt(252)
        
        # 計算RSI
        delta = stock_data['close_price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        stock_data['rsi'] = 100 - (100 / (1 + rs))
        stock_data['rsi'] = stock_data['rsi'].fillna(50)
        
        # 計算動量指標
        stock_data['momentum_10'] = stock_data['close_price'] / stock_data['close_price'].shift(10) - 1
        
        print("   ✅ 技術指標計算完成:")
        print(f"      5日移動平均: {stock_data['ma_5'].iloc[-1]:.2f}")
        print(f"      20日移動平均: {stock_data['ma_20'].iloc[-1]:.2f}")
        print(f"      當前RSI: {stock_data['rsi'].iloc[-1]:.1f}")
        print(f"      20日波動率: {stock_data['volatility'].iloc[-1]:.1%}")
        print(f"      10日動量: {stock_data['momentum_10'].iloc[-1]:.1%}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 技術指標計算失敗: {e}")
        return False

def main():
    """主程式"""
    print("🚀 潛力股預測系統基本示範")
    print("=" * 60)
    print("使用基本機器學習模型 (Random Forest + Logistic Regression)")
    print("=" * 60)
    
    results = []
    
    # 測試技術指標計算
    results.append(("技術指標計算", test_technical_indicators()))
    
    # 測試基本預測功能
    results.append(("機器學習預測", test_basic_prediction()))
    
    # 總結
    print("\n📋 測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 總體結果: {passed}/{total} 通過 ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 基本機器學習功能完全正常！")
        print("\n📚 系統功能說明:")
        print("   ✅ 技術指標計算 (移動平均、RSI、波動率、動量)")
        print("   ✅ 機器學習模型 (Random Forest、Logistic Regression)")
        print("   ✅ 特徵重要性分析")
        print("   ✅ 潛力股排行榜生成")
        print("   ✅ 模型評估指標")
        
        print("\n🔧 可選高級功能:")
        print("   - LightGBM/XGBoost (需要安裝 libomp)")
        print("   - 超參數調校 (Optuna)")
        print("   - 模型解釋 (SHAP)")
        
        print("\n🚀 下一步:")
        print("   1. 使用真實資料訓練模型:")
        print("      python main.py generate-features --date 2024-06-30")
        print("   2. 執行預測:")
        print("      python main.py predict --model random_forest")
        print("   3. 生成排行榜:")
        print("      python main.py ranking --top-k 20")
    else:
        print("\n⚠️ 部分功能測試失敗，請檢查相關問題")

if __name__ == "__main__":
    main()

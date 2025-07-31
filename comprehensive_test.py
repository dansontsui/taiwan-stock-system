#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股潛力股分析系統完整測試
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemTester:
    """系統測試器"""
    
    def __init__(self):
        self.results = []
        self.db_path = Path('data/taiwan_stock.db')
        self.predictor_path = Path('potential_stock_predictor')
    
    def log_result(self, test_name, success, message=""):
        """記錄測試結果"""
        self.results.append((test_name, success, message))
        status = "通過" if success else "失敗"
        logger.info(f"{test_name}: {status} {message}")
    
    def test_database(self):
        """測試主資料庫"""
        try:
            if not self.db_path.exists():
                self.log_result("資料庫存在性", False, "資料庫檔案不存在")
                return False
            
            # 檢查資料庫大小
            size_mb = self.db_path.stat().st_size / 1024 / 1024
            self.log_result("資料庫大小", True, f"{size_mb:.1f} MB")
            
            # 連接資料庫
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 檢查資料表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['stocks', 'stock_prices', 'monthly_revenues', 'financial_statements']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                self.log_result("資料表完整性", False, f"缺少: {missing_tables}")
                return False
            
            # 檢查資料量
            stats = {}
            for table in required_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            
            self.log_result("資料表完整性", True, f"資料表: {len(tables)}")
            self.log_result("資料量統計", True, 
                          f"股票: {stats.get('stocks', 0)}, "
                          f"價格: {stats.get('stock_prices', 0)}, "
                          f"營收: {stats.get('monthly_revenues', 0)}")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_result("資料庫測試", False, str(e))
            return False
    
    def test_python_packages(self):
        """測試Python套件"""
        required_packages = [
            ('pandas', 'pd'),
            ('numpy', 'np'),
            ('sklearn', 'sklearn'),
            ('matplotlib', 'plt'),
            ('tqdm', 'tqdm'),
            ('joblib', 'joblib')
        ]
        
        missing_packages = []
        for package, alias in required_packages:
            try:
                __import__(package)
                self.log_result(f"套件-{package}", True)
            except ImportError:
                missing_packages.append(package)
                self.log_result(f"套件-{package}", False, "未安裝")
        
        if missing_packages:
            self.log_result("套件完整性", False, f"需安裝: {missing_packages}")
            return False
        else:
            self.log_result("套件完整性", True, "所有必需套件已安裝")
            return True
    
    def test_predictor_structure(self):
        """測試預測系統結構"""
        if not self.predictor_path.exists():
            self.log_result("預測系統目錄", False, "目錄不存在")
            return False
        
        # 檢查核心檔案
        core_files = [
            'config/config.py',
            'src/__init__.py',
            'src/features/feature_engineering.py',
            'src/features/target_generator.py',
            'src/models/model_trainer.py',
            'src/models/predictor.py',
            'src/utils/database.py',
            'main.py',
            'requirements.txt'
        ]
        
        missing_files = []
        for file_path in core_files:
            full_path = self.predictor_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log_result("預測系統檔案", False, f"缺少: {missing_files}")
            return False
        
        # 創建必要目錄
        data_dirs = ['data', 'data/features', 'data/targets', 'data/predictions', 'models', 'logs']
        for dir_name in data_dirs:
            dir_path = self.predictor_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.log_result("預測系統結構", True, "檔案完整，目錄已準備")
        return True
    
    def test_feature_generation(self):
        """測試特徵生成功能"""
        try:
            # 獲取測試股票
            conn = sqlite3.connect(str(self.db_path))
            query = """
            SELECT DISTINCT stock_id 
            FROM stock_prices 
            WHERE stock_id NOT LIKE '00%'
            AND stock_id IN (SELECT stock_id FROM stocks WHERE is_active = 1)
            LIMIT 3
            """
            test_stocks = pd.read_sql_query(query, conn)['stock_id'].tolist()
            
            if not test_stocks:
                self.log_result("測試股票獲取", False, "沒有可用的測試股票")
                return False
            
            # 測試單一股票特徵生成
            stock_id = test_stocks[0]
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # 獲取股價資料
            price_query = """
            SELECT date, open_price, high_price, low_price, close_price, volume
            FROM stock_prices 
            WHERE stock_id = ? AND date >= ? AND date <= ?
            ORDER BY date
            """
            
            prices_df = pd.read_sql_query(price_query, conn, params=[stock_id, start_date, end_date])
            
            if len(prices_df) < 50:
                self.log_result("股價資料充足性", False, f"股票 {stock_id} 只有 {len(prices_df)} 筆資料")
                return False
            
            # 計算基本技術指標
            prices_df['ma_5'] = prices_df['close_price'].rolling(window=5).mean()
            prices_df['ma_20'] = prices_df['close_price'].rolling(window=20).mean()
            prices_df['rsi'] = self.calculate_rsi(prices_df['close_price'], 14)
            prices_df['volatility'] = prices_df['close_price'].pct_change().rolling(window=20).std()
            
            # 檢查特徵有效性
            features = ['ma_5', 'ma_20', 'rsi', 'volatility']
            valid_features = []
            
            for feature in features:
                valid_count = prices_df[feature].notna().sum()
                if valid_count > 20:  # 至少20個有效值
                    valid_features.append(feature)
            
            self.log_result("特徵生成測試", True, 
                          f"股票 {stock_id}, 資料 {len(prices_df)} 筆, 特徵 {len(valid_features)} 個")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_result("特徵生成測試", False, str(e))
            return False
    
    def calculate_rsi(self, prices, window=14):
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def test_machine_learning(self):
        """測試機器學習功能"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, roc_auc_score
            
            # 創建模擬資料
            np.random.seed(42)
            n_samples = 1000
            n_features = 10
            
            # 生成特徵
            X = np.random.randn(n_samples, n_features)
            
            # 生成目標變數 (模擬潛力股預測)
            # 使用前幾個特徵的線性組合加上噪音
            y_prob = 1 / (1 + np.exp(-(X[:, 0] + 0.5 * X[:, 1] - 0.3 * X[:, 2] + np.random.randn(n_samples) * 0.1)))
            y = (y_prob > 0.5).astype(int)
            
            # 分割資料
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 訓練模型
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # 預測
            y_pred = model.predict(X_test)
            y_prob_pred = model.predict_proba(X_test)[:, 1]
            
            # 評估
            accuracy = accuracy_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_prob_pred)
            
            # 特徵重要性
            feature_importance = model.feature_importances_
            top_features = np.argsort(feature_importance)[-3:][::-1]
            
            self.log_result("機器學習測試", True, 
                          f"準確率: {accuracy:.3f}, AUC: {auc:.3f}, "
                          f"重要特徵: {top_features}")
            
            return True
            
        except Exception as e:
            self.log_result("機器學習測試", False, str(e))
            return False
    
    def run_all_tests(self):
        """執行所有測試"""
        logger.info("開始執行系統完整測試...")
        
        tests = [
            ("資料庫測試", self.test_database),
            ("Python套件測試", self.test_python_packages),
            ("預測系統結構測試", self.test_predictor_structure),
            ("特徵生成測試", self.test_feature_generation),
            ("機器學習測試", self.test_machine_learning),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"執行 {test_name}...")
            try:
                test_func()
            except Exception as e:
                self.log_result(test_name, False, f"異常: {str(e)}")
        
        self.print_summary()
    
    def print_summary(self):
        """列印測試總結"""
        print("\n" + "=" * 60)
        print("台股潛力股分析系統測試總結")
        print("=" * 60)
        
        passed = 0
        total = len(self.results)
        
        for test_name, success, message in self.results:
            status = "✓ 通過" if success else "✗ 失敗"
            print(f"{status:8} {test_name:20} {message}")
            if success:
                passed += 1
        
        print("-" * 60)
        print(f"總體結果: {passed}/{total} 通過 ({passed/total:.1%})")
        
        if passed >= total * 0.8:  # 80%以上通過
            print("\n🎉 系統狀態良好！")
            print("\n建議下一步:")
            print("1. cd potential_stock_predictor")
            print("2. python simple_features.py 2024-06-30")
            print("3. python simple_train.py")
            print("4. python simple_predict.py ranking random_forest 20")
        else:
            print("\n⚠️ 系統存在問題，請檢查失敗項目")
            
            # 提供修復建議
            failed_tests = [name for name, success, _ in self.results if not success]
            if any("套件" in test for test in failed_tests):
                print("\n套件安裝建議:")
                print("pip install pandas numpy scikit-learn matplotlib tqdm joblib")
            
            if any("資料庫" in test for test in failed_tests):
                print("\n資料庫問題建議:")
                print("請先執行主系統收集資料: python scripts/collect_data.py --test")

def main():
    """主程式"""
    tester = SystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()

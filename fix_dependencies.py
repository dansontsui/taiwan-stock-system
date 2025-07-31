#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復依賴套件問題
"""

import subprocess
import sys
import os
from pathlib import Path
import logging

# 設置日誌
log_file = Path('logs/fix_dependencies.log')
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_package(package_name):
    """檢查套件是否已安裝"""
    try:
        __import__(package_name)
        logger.info(f"套件 {package_name} 已安裝")
        return True
    except ImportError:
        logger.warning(f"套件 {package_name} 未安裝")
        return False

def install_package(package_name):
    """安裝套件"""
    logger.info(f"正在安裝 {package_name}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=300  # 5分鐘超時
        )
        
        if result.returncode == 0:
            logger.info(f"成功安裝 {package_name}")
            return True
        else:
            logger.error(f"安裝 {package_name} 失敗: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"安裝 {package_name} 超時")
        return False
    except Exception as e:
        logger.error(f"安裝 {package_name} 時發生錯誤: {e}")
        return False

def fix_unicode_issues():
    """修復 Unicode 編碼問題"""
    logger.info("修復 Unicode 編碼問題...")
    
    files_to_fix = [
        'potential_stock_predictor/main.py',
        'potential_stock_predictor/menu.py'
    ]
    
    unicode_chars = {
        '❌': 'X',
        '✅': 'OK',
        '⚠️': 'WARNING',
        '🔍': '',
        '🚀': '',
        '📈': '',
        '🎯': '',
        '🤖': '',
        '📊': '',
        '⏳': '',
        '🚨': '',
        '👋': '',
        '🔧': '',
        '1️⃣': '1.',
        '2️⃣': '2.',
        '3️⃣': '3.',
        '4️⃣': '4.',
        '5️⃣': '5.'
    }
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"檔案不存在: {file_path}")
            continue
        
        try:
            # 讀取檔案
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替換 Unicode 字符
            original_content = content
            for unicode_char, replacement in unicode_chars.items():
                content = content.replace(unicode_char, replacement)
            
            # 如果有變更，寫回檔案
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"修復檔案: {file_path}")
                fixed_count += 1
            else:
                logger.info(f"檔案無需修復: {file_path}")
                
        except Exception as e:
            logger.error(f"修復檔案 {file_path} 時發生錯誤: {e}")
    
    logger.info(f"修復完成，共修復 {fixed_count} 個檔案")
    return fixed_count > 0

def create_requirements_file():
    """創建 requirements.txt 檔案"""
    logger.info("創建 requirements.txt 檔案...")
    
    requirements = [
        "pandas>=1.3.0",
        "numpy>=1.21.0", 
        "scikit-learn>=1.0.0",
        "matplotlib>=3.3.0",
        "tqdm>=4.60.0",
        "joblib>=1.0.0",
        "lightgbm>=3.2.0",
        "xgboost>=1.5.0",
        "optuna>=2.10.0"
    ]
    
    req_file = Path('potential_stock_predictor/requirements.txt')
    
    try:
        with open(req_file, 'w', encoding='utf-8') as f:
            for req in requirements:
                f.write(req + '\n')
        
        logger.info(f"創建 requirements.txt: {req_file}")
        return True
        
    except Exception as e:
        logger.error(f"創建 requirements.txt 失敗: {e}")
        return False

def main():
    """主程式"""
    print("修復潛力股預測系統依賴問題")
    print("=" * 50)
    
    logger.info("開始修復依賴問題")
    
    # 1. 檢查必要套件
    required_packages = [
        'pandas',
        'numpy', 
        'sklearn',
        'matplotlib',
        'tqdm',
        'joblib'
    ]
    
    optional_packages = [
        'lightgbm',
        'xgboost', 
        'optuna'
    ]
    
    print("\n1. 檢查必要套件...")
    missing_required = []
    for package in required_packages:
        if not check_package(package):
            missing_required.append(package)
    
    print("\n2. 檢查可選套件...")
    missing_optional = []
    for package in optional_packages:
        if not check_package(package):
            missing_optional.append(package)
    
    # 2. 安裝缺少的套件
    if missing_required:
        print(f"\n3. 安裝必要套件: {missing_required}")
        for package in missing_required:
            install_package(package)
    
    if missing_optional:
        print(f"\n4. 安裝可選套件: {missing_optional}")
        choice = input("是否安裝可選的機器學習套件？(y/N): ").strip().lower()
        if choice == 'y':
            for package in missing_optional:
                install_package(package)
        else:
            logger.info("跳過可選套件安裝")
    
    # 3. 修復編碼問題
    print("\n5. 修復 Unicode 編碼問題...")
    fix_unicode_issues()
    
    # 4. 創建 requirements.txt
    print("\n6. 創建 requirements.txt...")
    create_requirements_file()
    
    # 5. 最終檢查
    print("\n7. 最終檢查...")
    all_packages = required_packages + optional_packages
    working_packages = []
    
    for package in all_packages:
        if check_package(package):
            working_packages.append(package)
    
    print(f"\n修復完成！")
    print(f"可用套件: {len(working_packages)}/{len(all_packages)}")
    print(f"詳細日誌: {log_file.absolute()}")
    
    if len(working_packages) >= len(required_packages):
        print("\n系統已準備就緒！")
        print("建議測試:")
        print("1. cd potential_stock_predictor")
        print("2. python test_features_simple.py")
        print("3. python simple_features_basic.py 2024-06-30")
    else:
        print("\n仍有問題需要解決，請檢查日誌檔案")
    
    logger.info("修復程序完成")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化資料庫腳本
"""

import sys
import os
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
from loguru import logger

def init_logging():
    """初始化日誌"""
    log_dir = os.path.join(Config.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.add(
        os.path.join(log_dir, 'init_database.log'),
        rotation="10 MB",
        retention="30 days",
        level="INFO"
    )

def main():
    """主函數"""
    print("=" * 60)
    print("台股歷史股價系統 - 資料庫初始化")
    print("=" * 60)
    
    # 初始化日誌
    init_logging()
    logger.info("開始初始化資料庫")
    
    try:
        # 建立資料庫管理器
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        
        print(f"資料庫路徑: {Config.DATABASE_PATH}")
        
        # 建立資料表
        print("正在建立資料表...")
        db_manager.create_tables()
        print("✅ 資料表建立完成")
        
        # 顯示資料表資訊
        print("\n資料表資訊:")
        print("-" * 40)
        
        tables = ['stocks', 'stock_prices', 'technical_indicators', 'etf_dividends', 'data_updates']
        
        for table in tables:
            try:
                count = db_manager.get_table_count(table)
                print(f"{table:<20}: {count:>10} 筆記錄")
            except Exception as e:
                print(f"{table:<20}: 建立失敗 ({e})")
        
        # 顯示資料庫大小
        db_size = db_manager.get_database_size()
        print(f"\n資料庫大小: {db_size}")
        
        # 測試資料庫連接
        print("\n測試資料庫連接...")
        test_query = "SELECT name FROM sqlite_master WHERE type='table'"
        result = db_manager.execute_query(test_query)
        print(f"✅ 資料庫連接正常，共有 {len(result)} 個資料表")

        print("\n資料表列表:")
        for row in result:
            print(f"  - {row['name']}")
        
        # 關閉資料庫連接
        db_manager.close()
        
        print("\n" + "=" * 60)
        print("✅ 資料庫初始化完成！")
        print("=" * 60)
        
        print("\n下一步:")
        print("1. 執行 python scripts/collect_data.py 收集歷史資料")
        print("2. 執行 python run.py 啟動系統")
        
        logger.info("資料庫初始化成功完成")
        
    except Exception as e:
        error_msg = f"資料庫初始化失敗: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()

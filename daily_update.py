#!/usr/bin/env python3
"""
台股每日更新 - 快速執行腳本
簡化版本，適合每日定時執行
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

def main():
    """執行每日更新"""
    print("=" * 60)
    print("🚀 台股每日增量資料更新")
    print("=" * 60)
    print(f"⏰ 執行時間: {datetime.now()}")
    print()
    
    try:
        # 執行每日更新腳本
        print("🔄 開始執行每日增量收集...")
        
        result = subprocess.run([
            sys.executable, "scripts/collect_daily_update.py",
            "--batch-size", "5",
            "--days-back", "7"
        ], cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ 每日更新執行成功！")
            print("🌐 您可以在 Web 介面查看最新資料")
        else:
            print("❌ 每日更新執行失敗")
            print("📋 請檢查日誌文件: logs/collect_daily_update.log")
            
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main()

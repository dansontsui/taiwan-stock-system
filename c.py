#!/usr/bin/env python3
"""
超簡潔的收集啟動器
用法: python c.py [選項]
"""

import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

def get_default_dates():
    """獲取預設日期範圍 (10年)"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=10*365)
    return start_date.isoformat(), end_date.isoformat()

def run_collect(start_date, end_date, batch_size, stock_scope):
    """執行收集"""
    script_path = Path(__file__).parent / "scripts" / "collect_with_detailed_logs.py"
    
    cmd = [
        sys.executable,
        str(script_path),
        "--start-date", start_date,
        "--end-date", end_date,
        "--batch-size", str(batch_size),
        "--stock-scope", stock_scope
    ]
    
    print(f"🚀 啟動收集: {stock_scope} 範圍, 批次大小 {batch_size}")
    print(f"📅 {start_date} ~ {end_date}")
    print("💡 按 Ctrl+C 停止")
    print("=" * 40)
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n⚠️ 已停止")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")

def main():
    """主程式"""
    start_date, end_date = get_default_dates()
    
    if len(sys.argv) == 1:
        # 無參數 = 快速收集所有股票
        print("🌐 快速收集所有股票 (預設)")
        run_collect(start_date, end_date, 5, "all")
    
    elif len(sys.argv) == 2:
        option = sys.argv[1].lower()
        
        if option in ['all', 'a']:
            print("🌐 收集所有股票")
            run_collect(start_date, end_date, 5, "all")
        
        elif option in ['main', 'm']:
            print("⭐ 收集主要股票")
            run_collect(start_date, end_date, 5, "main")
        
        elif option in ['test', 't']:
            print("🧪 測試收集")
            run_collect(start_date, end_date, 1, "test")
        
        elif option in ['help', 'h', '--help', '-h']:
            print("📋 用法:")
            print("  python c.py        # 收集所有股票 (預設)")
            print("  python c.py all    # 收集所有股票")
            print("  python c.py main   # 收集主要股票 (50檔)")
            print("  python c.py test   # 測試收集 (5檔)")
            print("  python c.py help   # 顯示說明")
        
        else:
            print(f"❌ 未知選項: {option}")
            print("💡 使用 'python c.py help' 查看說明")
    
    else:
        print("❌ 參數過多")
        print("💡 使用 'python c.py help' 查看說明")

if __name__ == "__main__":
    main()

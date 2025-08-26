# -*- coding: utf-8 -*-
"""
備份和還原選單3的結果檔案
"""

import shutil
import os
from datetime import datetime
from pathlib import Path

def backup_walk_forward_results():
    """備份walk-forward結果"""
    print("💾 備份Walk-Forward結果")
    print("=" * 50)
    
    try:
        # 來源路徑
        source_dir = Path("stock_price_investment_system/results/walk_forward")
        
        if not source_dir.exists():
            print("❌ 找不到結果資料夾")
            return
        
        # 檢查是否有結果檔案
        result_files = list(source_dir.glob("walk_forward_results_*.json"))
        if not result_files:
            print("❌ 沒有找到結果檔案")
            return
        
        print(f"📊 找到 {len(result_files)} 個結果檔案")
        
        # 備份路徑
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path(f"backup_walk_forward_{timestamp}")
        backup_dir.mkdir(exist_ok=True)
        
        # 複製整個資料夾
        shutil.copytree(source_dir, backup_dir / "walk_forward", dirs_exist_ok=True)
        
        print(f"✅ 備份完成！")
        print(f"📁 備份位置: {backup_dir.absolute()}")
        
        # 顯示備份內容
        backup_files = list((backup_dir / "walk_forward").glob("*.json"))
        print(f"\n📋 備份檔案清單:")
        for i, file in enumerate(backup_files, 1):
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            print(f"  {i}. {file.name} ({file_time.strftime('%Y-%m-%d %H:%M')})")
        
        return str(backup_dir)
        
    except Exception as e:
        print(f"❌ 備份失敗: {e}")
        return None

def restore_walk_forward_results(backup_dir: str):
    """還原walk-forward結果"""
    print("🔄 還原Walk-Forward結果")
    print("=" * 50)
    
    try:
        backup_path = Path(backup_dir)
        source_path = backup_path / "walk_forward"
        
        if not source_path.exists():
            print(f"❌ 備份路徑不存在: {source_path}")
            return False
        
        # 目標路徑
        target_dir = Path("stock_price_investment_system/results/walk_forward")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 複製檔案
        backup_files = list(source_path.glob("*.json"))
        csv_files = list(source_path.glob("*.csv"))
        
        for file in backup_files + csv_files:
            target_file = target_dir / file.name
            shutil.copy2(file, target_file)
            print(f"✅ 還原: {file.name}")
        
        print(f"\n✅ 還原完成！")
        print(f"📁 還原到: {target_dir.absolute()}")
        print(f"📊 還原檔案數: {len(backup_files + csv_files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 還原失敗: {e}")
        return False

def list_backups():
    """列出所有備份"""
    print("📋 備份清單")
    print("=" * 50)
    
    backup_dirs = [d for d in Path(".").iterdir() if d.is_dir() and d.name.startswith("backup_walk_forward_")]
    
    if not backup_dirs:
        print("❌ 沒有找到備份")
        return []
    
    backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for i, backup_dir in enumerate(backup_dirs, 1):
        backup_time = datetime.fromtimestamp(backup_dir.stat().st_mtime)
        walk_forward_dir = backup_dir / "walk_forward"
        
        if walk_forward_dir.exists():
            file_count = len(list(walk_forward_dir.glob("*.json")))
            print(f"  {i}. {backup_dir.name}")
            print(f"     時間: {backup_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     檔案數: {file_count}")
            print()
    
    return backup_dirs

def main():
    """主程式"""
    print("🏦 Walk-Forward結果備份工具")
    print("=" * 60)
    
    while True:
        print("\n選擇操作:")
        print("1. 備份當前結果")
        print("2. 還原備份")
        print("3. 列出所有備份")
        print("4. 退出")
        
        choice = input("\n請選擇 (1-4): ").strip()
        
        if choice == '1':
            backup_dir = backup_walk_forward_results()
            if backup_dir:
                print(f"\n💡 使用方式:")
                print(f"   python backup_results.py")
                print(f"   選擇選項2，輸入: {backup_dir}")
        
        elif choice == '2':
            backups = list_backups()
            if backups:
                try:
                    idx = int(input("選擇要還原的備份編號: ")) - 1
                    if 0 <= idx < len(backups):
                        restore_walk_forward_results(str(backups[idx]))
                    else:
                        print("❌ 無效的編號")
                except ValueError:
                    print("❌ 請輸入數字")
        
        elif choice == '3':
            list_backups()
        
        elif choice == '4':
            print("👋 再見！")
            break
        
        else:
            print("❌ 無效選擇")

if __name__ == "__main__":
    main()

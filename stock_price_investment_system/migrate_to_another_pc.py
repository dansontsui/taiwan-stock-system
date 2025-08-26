# -*- coding: utf-8 -*-
"""
跨電腦遷移工具 - 打包A電腦的結果到B電腦
"""

import shutil
import os
from datetime import datetime
from pathlib import Path
import zipfile

def create_migration_package():
    """創建遷移包"""
    print("📦 創建跨電腦遷移包")
    print("=" * 50)
    
    try:
        # 創建遷移包資料夾
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        package_name = f"stock_migration_{timestamp}"
        package_dir = Path(package_name)
        package_dir.mkdir(exist_ok=True)
        
        # 需要遷移的路徑
        migration_paths = {
            'hyperparameter_tuning': 'stock_price_investment_system/models/hyperparameter_tuning',
            'walk_forward': 'stock_price_investment_system/results/walk_forward',
            'candidate_pools': 'stock_price_investment_system/results/candidate_pools'
        }
        
        copied_files = 0
        
        for folder_name, source_path in migration_paths.items():
            source = Path(source_path)
            target = package_dir / folder_name
            
            if source.exists():
                print(f"📁 複製 {folder_name}...")
                shutil.copytree(source, target, dirs_exist_ok=True)
                
                # 統計檔案數量
                files = list(target.rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                copied_files += file_count
                print(f"   ✅ {file_count} 個檔案")
            else:
                print(f"   ⚠️  路徑不存在: {source}")
        
        # 創建說明檔案
        readme_content = f"""# 股票預測系統遷移包

## 遷移時間
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 包含內容
- hyperparameter_tuning/: 超參數調優結果（選單9）
- walk_forward/: Walk-Forward驗證結果（選單3）  
- candidate_pools/: 候選池結果（選單4）

## 使用方式

### 在B電腦上執行：

1. 解壓此遷移包
2. 執行還原腳本：
   ```bash
   python restore_migration.py {package_name}
   ```

3. 或手動複製：
   ```bash
   cp -r {package_name}/hyperparameter_tuning/ stock_price_investment_system/models/
   cp -r {package_name}/walk_forward/ stock_price_investment_system/results/
   cp -r {package_name}/candidate_pools/ stock_price_investment_system/results/
   ```

## 注意事項
- B電腦需要有相同的股價資料庫
- 確保Python環境和套件版本一致
- 執行選單5前確保所有檔案都已正確還原

## 檔案統計
總檔案數: {copied_files}
"""
        
        readme_file = package_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 創建ZIP檔案
        zip_filename = f"{package_name}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(package_dir.parent)
                    zipf.write(file_path, arcname)
        
        print(f"\n✅ 遷移包創建完成！")
        print(f"📁 資料夾: {package_dir}")
        print(f"📦 ZIP檔案: {zip_filename}")
        print(f"📊 總檔案數: {copied_files}")
        print(f"💾 檔案大小: {os.path.getsize(zip_filename) / 1024 / 1024:.1f} MB")
        
        print(f"\n🚀 使用方式:")
        print(f"1. 將 {zip_filename} 複製到B電腦")
        print(f"2. 在B電腦解壓並執行還原")
        print(f"3. 執行選單5進行外層回測")
        
        return zip_filename
        
    except Exception as e:
        print(f"❌ 創建遷移包失敗: {e}")
        return None

def restore_migration_package(package_path: str):
    """還原遷移包"""
    print("🔄 還原遷移包")
    print("=" * 50)
    
    try:
        package_dir = Path(package_path)
        
        if not package_dir.exists():
            print(f"❌ 找不到遷移包: {package_path}")
            return False
        
        # 還原路徑對應
        restore_paths = {
            'hyperparameter_tuning': 'stock_price_investment_system/models/hyperparameter_tuning',
            'walk_forward': 'stock_price_investment_system/results/walk_forward',
            'candidate_pools': 'stock_price_investment_system/results/candidate_pools'
        }
        
        restored_files = 0
        
        for folder_name, target_path in restore_paths.items():
            source = package_dir / folder_name
            target = Path(target_path)
            
            if source.exists():
                print(f"📁 還原 {folder_name}...")
                target.parent.mkdir(parents=True, exist_ok=True)
                
                if target.exists():
                    shutil.rmtree(target)
                
                shutil.copytree(source, target)
                
                # 統計檔案數量
                files = list(target.rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                restored_files += file_count
                print(f"   ✅ {file_count} 個檔案")
            else:
                print(f"   ⚠️  來源不存在: {source}")
        
        print(f"\n✅ 還原完成！")
        print(f"📊 總還原檔案數: {restored_files}")
        print(f"\n🎯 現在可以執行:")
        print(f"   python stock_price_investment_system/start.py")
        print(f"   選擇選單5進行外層回測")
        
        return True
        
    except Exception as e:
        print(f"❌ 還原失敗: {e}")
        return False

def main():
    """主程式"""
    print("🏦 股票預測系統跨電腦遷移工具")
    print("=" * 60)
    
    while True:
        print("\n選擇操作:")
        print("1. 創建遷移包（A電腦使用）")
        print("2. 還原遷移包（B電腦使用）")
        print("3. 退出")
        
        choice = input("\n請選擇 (1-3): ").strip()
        
        if choice == '1':
            create_migration_package()
        
        elif choice == '2':
            package_path = input("輸入遷移包路徑: ").strip()
            restore_migration_package(package_path)
        
        elif choice == '3':
            print("👋 再見！")
            break
        
        else:
            print("❌ 無效選擇")

if __name__ == "__main__":
    main()

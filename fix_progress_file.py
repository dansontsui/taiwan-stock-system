#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復損壞的進度檔案
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

# 設置編碼
os.environ['PYTHONIOENCODING'] = 'utf-8'

def backup_corrupted_file(progress_file):
    """備份損壞的檔案"""
    try:
        corrupted_backup = progress_file.parent / f"corrupted_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(progress_file, corrupted_backup)
        print(f"📁 已備份損壞檔案: {corrupted_backup.name}")
        return True
    except Exception as e:
        print(f"❌ 備份損壞檔案失敗: {e}")
        return False

def try_repair_json(file_path):
    """嘗試修復JSON檔案"""
    try:
        print(f"🔧 嘗試修復JSON檔案: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 常見的修復策略
        original_content = content
        
        # 1. 移除末尾不完整的行
        lines = content.split('\n')
        
        # 找到最後一個完整的JSON結構
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            
            # 如果這行不完整（沒有值或沒有結束符號）
            if (line.endswith(':') or 
                line.endswith(',') or 
                (line and not line.endswith('}') and not line.endswith(']') and not line.endswith('"') and not line.endswith('null'))):
                print(f"🔍 發現不完整的行 {i+1}: {line}")
                lines = lines[:i]
                break
        
        # 2. 確保JSON結構完整
        repaired_content = '\n'.join(lines)
        
        # 3. 嘗試添加缺失的結束符號
        if repaired_content.strip():
            # 計算大括號和方括號的平衡
            open_braces = repaired_content.count('{') - repaired_content.count('}')
            open_brackets = repaired_content.count('[') - repaired_content.count(']')
            
            # 添加缺失的結束符號
            repaired_content += '\n' + '  }' * open_brackets + '\n' + '}' * open_braces
        
        # 4. 驗證修復後的JSON
        try:
            json.loads(repaired_content)
            print("✅ JSON修復成功")
            return repaired_content
        except json.JSONDecodeError as e:
            print(f"❌ JSON修復失敗: {e}")
            return None
            
    except Exception as e:
        print(f"❌ 修復過程失敗: {e}")
        return None

def restore_from_backup(progress_dir):
    """從備份恢復"""
    try:
        backup_dir = progress_dir / "backups"
        if not backup_dir.exists():
            print("❌ 沒有找到備份目錄")
            return False
        
        # 獲取所有備份檔案，按時間排序
        backup_files = list(backup_dir.glob("progress_backup_*.json"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not backup_files:
            print("❌ 沒有找到備份檔案")
            return False
        
        print(f"🔍 找到 {len(backup_files)} 個備份檔案")
        
        # 嘗試從最新的備份恢復
        for i, backup_file in enumerate(backup_files):
            try:
                print(f"🔄 嘗試備份 {i+1}/{len(backup_files)}: {backup_file.name}")
                
                # 驗證備份檔案
                with open(backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 如果驗證成功，複製到主檔案
                progress_file = progress_dir / "collection_progress.json"
                shutil.copy2(backup_file, progress_file)
                
                print(f"✅ 成功從備份恢復: {backup_file.name}")
                print(f"📊 恢復的任務數量: {len(data.get('tasks', {}))}")
                return True
                
            except json.JSONDecodeError:
                print(f"⚠️ 備份檔案也損壞: {backup_file.name}")
                continue
            except Exception as e:
                print(f"⚠️ 恢復失敗: {backup_file.name}, 錯誤: {e}")
                continue
        
        print("❌ 所有備份檔案都無法使用")
        return False
        
    except Exception as e:
        print(f"❌ 備份恢復失敗: {e}")
        return False

def fix_progress_file():
    """修復進度檔案"""
    print("🔧 進度檔案修復工具")
    print("=" * 50)
    
    progress_dir = Path("data/progress")
    progress_file = progress_dir / "collection_progress.json"
    
    if not progress_file.exists():
        print("❌ 進度檔案不存在")
        return False
    
    print(f"📁 檢查進度檔案: {progress_file}")
    
    # 1. 嘗試載入檔案
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ 進度檔案格式正確，無需修復")
        print(f"📊 任務數量: {len(data.get('tasks', {}))}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"🚨 發現JSON格式錯誤: {e}")
        print(f"   錯誤位置: 行 {e.lineno}, 列 {e.colno}")
        
        # 2. 備份損壞的檔案
        backup_success = backup_corrupted_file(progress_file)
        
        # 3. 嘗試修復
        print("\n🔧 嘗試修復策略...")
        
        # 策略1: 嘗試修復JSON
        repaired_content = try_repair_json(progress_file)
        if repaired_content:
            try:
                # 寫入修復後的內容
                with open(progress_file, 'w', encoding='utf-8') as f:
                    f.write(repaired_content)
                
                # 驗證修復結果
                with open(progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print("✅ JSON修復成功")
                print(f"📊 修復後任務數量: {len(data.get('tasks', {}))}")
                return True
                
            except Exception as e:
                print(f"❌ 修復後寫入失敗: {e}")
        
        # 策略2: 從備份恢復
        print("\n🔄 嘗試從備份恢復...")
        if restore_from_backup(progress_dir):
            return True
        
        # 策略3: 創建空白進度檔案
        print("\n🆕 創建空白進度檔案...")
        try:
            empty_data = {
                'tasks': {},
                'last_updated': datetime.now().isoformat()
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(empty_data, f, ensure_ascii=False, indent=2)
            
            print("✅ 已創建空白進度檔案")
            print("⚠️ 所有進度記錄已丟失，需要重新開始任務")
            return True
            
        except Exception as e:
            print(f"❌ 創建空白檔案失敗: {e}")
            return False
    
    except Exception as e:
        print(f"❌ 檔案檢查失敗: {e}")
        return False

def main():
    """主函數"""
    try:
        success = fix_progress_file()
        
        if success:
            print("\n🎉 進度檔案修復完成！")
            print("\n💡 建議:")
            print("   1. 重新執行中斷的任務")
            print("   2. 使用 --resume-task 參數續傳任務")
            print("   3. 定期檢查備份檔案")
        else:
            print("\n❌ 進度檔案修復失敗")
            print("\n🆘 手動處理建議:")
            print("   1. 刪除損壞的進度檔案")
            print("   2. 重新開始資料收集任務")
            print("   3. 聯繫技術支援")
        
    except KeyboardInterrupt:
        print("\n\n❌ 使用者中斷修復")
    except Exception as e:
        print(f"\n❌ 修復過程發生錯誤: {e}")

if __name__ == "__main__":
    main()

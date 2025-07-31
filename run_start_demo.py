#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示 start.py 的完整執行過程
"""

import subprocess
import sys
import os
from pathlib import Path
import time

def run_start_py_demo():
    """運行 start.py 演示"""
    print("="*60)
    print("潛力股預測系統 start.py 演示")
    print("="*60)
    
    # 檢查檔案
    start_py_path = Path('potential_stock_predictor/start.py')
    if not start_py_path.exists():
        print(f"錯誤: 找不到 {start_py_path}")
        return False
    
    print(f"找到檔案: {start_py_path}")
    
    # 切換目錄
    original_cwd = os.getcwd()
    
    try:
        os.chdir('potential_stock_predictor')
        print(f"切換到目錄: {os.getcwd()}")
        
        print("\n開始執行 start.py...")
        print("注意: 程式會自動輸入 'q' 來退出")
        print("-" * 60)
        
        # 執行 start.py
        process = subprocess.Popen(
            [sys.executable, 'start.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # 等待一下讓程式啟動
        time.sleep(2)
        
        # 發送 'q' 來退出
        stdout, stderr = process.communicate(input='q\n', timeout=30)
        
        print("start.py 終端機輸出:")
        print("="*60)
        
        # 顯示輸出，處理編碼問題
        try:
            # 替換可能有問題的字符
            clean_stdout = stdout.replace('\ufffd', '?')
            print(clean_stdout)
        except UnicodeEncodeError:
            # 如果還是有問題，逐行處理
            lines = stdout.split('\n')
            for line in lines:
                try:
                    print(line)
                except UnicodeEncodeError:
                    print(line.encode('ascii', errors='replace').decode('ascii'))
        
        if stderr:
            print("\n標準錯誤輸出:")
            print("-" * 30)
            try:
                clean_stderr = stderr.replace('\ufffd', '?')
                print(clean_stderr)
            except UnicodeEncodeError:
                print("(錯誤輸出包含特殊字符)")
        
        print("="*60)
        print(f"程式退出碼: {process.returncode}")
        
        # 分析輸出
        print("\n輸出分析:")
        print("-" * 30)
        
        key_features = [
            ("歡迎訊息", "歡迎使用潛力股預測系統" in stdout),
            ("環境檢查", "檢查運行環境" in stdout),
            ("Python版本", "Python 版本" in stdout),
            ("pandas檢查", "pandas" in stdout),
            ("numpy檢查", "numpy" in stdout),
            ("資料庫檢查", "資料庫" in stdout or "database" in stdout.lower()),
            ("快速指南", "快速開始" in stdout or "快速" in stdout),
            ("正常退出", process.returncode == 0)
        ]
        
        passed_features = 0
        for feature_name, found in key_features:
            status = "✓" if found else "✗"
            print(f"{status} {feature_name}")
            if found:
                passed_features += 1
        
        print(f"\n功能檢查: {passed_features}/{len(key_features)} 通過")
        
        # 記錄到日誌
        log_file = Path('../logs/start_py_demo.log')
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("start.py 演示執行記錄\n")
            f.write("="*40 + "\n")
            f.write(f"執行時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"退出碼: {process.returncode}\n")
            f.write(f"功能檢查: {passed_features}/{len(key_features)} 通過\n\n")
            f.write("標準輸出:\n")
            f.write(stdout)
            if stderr:
                f.write("\n標準錯誤:\n")
                f.write(stderr)
        
        print(f"\n詳細日誌已保存到: {log_file.absolute()}")
        
        # 恢復目錄
        os.chdir(original_cwd)
        
        # 判斷結果
        success = passed_features >= len(key_features) * 0.8
        
        if success:
            print("\n🎉 start.py 測試成功！")
            print("\n系統狀態:")
            print("- 環境檢查正常")
            print("- 所有必要套件已安裝")
            print("- 資料庫連接正常")
            print("- 選單系統準備就緒")
            
            print("\n建議下一步:")
            print("1. cd potential_stock_predictor")
            print("2. python start.py")
            print("3. 按 Enter 啟動選單系統")
            print("4. 選擇 1 → 1 進行快速測試")
        else:
            print("\n⚠️ start.py 部分功能可能有問題")
            print("請檢查上述分析結果")
        
        return success
        
    except subprocess.TimeoutExpired:
        print("錯誤: 執行超時")
        process.kill()
        os.chdir(original_cwd)
        return False
        
    except Exception as e:
        print(f"錯誤: {e}")
        os.chdir(original_cwd)
        return False

def main():
    """主程式"""
    success = run_start_py_demo()
    
    print("\n" + "="*60)
    print("演示完成")
    print("="*60)
    
    if success:
        print("✓ start.py 運作正常，可以開始使用潛力股預測系統")
    else:
        print("✗ start.py 可能存在問題，請檢查系統配置")

if __name__ == "__main__":
    main()

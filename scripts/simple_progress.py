#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單進度記錄系統 - 只記錄當前處理到哪支股票
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

class SimpleProgress:
    """簡單進度記錄器"""
    
    def __init__(self, progress_dir: str = "data/simple_progress"):
        """初始化進度記錄器"""
        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        
        # 進度檔案
        self.current_stock_file = self.progress_dir / "current_stock.json"
        self.completed_stocks_file = self.progress_dir / "completed_stocks.json"
        self.failed_stocks_file = self.progress_dir / "failed_stocks.json"
    
    def save_current_stock(self, stock_id: str, stock_name: str = "", total_stocks: int = 0, current_index: int = 0):
        """保存當前處理的股票"""
        try:
            data = {
                "stock_id": stock_id,
                "stock_name": stock_name,
                "current_index": current_index,
                "total_stocks": total_stocks,
                "last_updated": datetime.now().isoformat(),
                "progress_percent": round((current_index / total_stocks * 100), 2) if total_stocks > 0 else 0
            }
            
            with open(self.current_stock_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"📝 進度記錄: [{current_index}/{total_stocks}] {stock_id} {stock_name}")
            
        except Exception as e:
            print(f"⚠️ 保存當前股票失敗: {e}")
    
    def get_current_stock(self) -> Optional[Dict]:
        """獲取當前處理的股票"""
        try:
            if not self.current_stock_file.exists():
                return None
            
            with open(self.current_stock_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            print(f"⚠️ 讀取當前股票失敗: {e}")
            return None
    
    def add_completed_stock(self, stock_id: str, stock_name: str = "", datasets: List[str] = None):
        """添加已完成的股票"""
        try:
            # 讀取現有完成清單
            completed = []
            if self.completed_stocks_file.exists():
                with open(self.completed_stocks_file, 'r', encoding='utf-8') as f:
                    completed = json.load(f)
            
            # 添加新完成的股票
            completed_stock = {
                "stock_id": stock_id,
                "stock_name": stock_name,
                "datasets": datasets or [],
                "completed_at": datetime.now().isoformat()
            }
            
            # 避免重複
            completed = [s for s in completed if s["stock_id"] != stock_id]
            completed.append(completed_stock)
            
            # 保存
            with open(self.completed_stocks_file, 'w', encoding='utf-8') as f:
                json.dump(completed, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 完成記錄: {stock_id} {stock_name}")
            
        except Exception as e:
            print(f"⚠️ 保存完成股票失敗: {e}")
    
    def add_failed_stock(self, stock_id: str, stock_name: str = "", error_message: str = ""):
        """添加失敗的股票"""
        try:
            # 讀取現有失敗清單
            failed = []
            if self.failed_stocks_file.exists():
                with open(self.failed_stocks_file, 'r', encoding='utf-8') as f:
                    failed = json.load(f)
            
            # 添加新失敗的股票
            failed_stock = {
                "stock_id": stock_id,
                "stock_name": stock_name,
                "error_message": error_message,
                "failed_at": datetime.now().isoformat()
            }
            
            # 避免重複
            failed = [s for s in failed if s["stock_id"] != stock_id]
            failed.append(failed_stock)
            
            # 保存
            with open(self.failed_stocks_file, 'w', encoding='utf-8') as f:
                json.dump(failed, f, ensure_ascii=False, indent=2)
            
            print(f"❌ 失敗記錄: {stock_id} {stock_name} - {error_message}")
            
        except Exception as e:
            print(f"⚠️ 保存失敗股票失敗: {e}")
    
    def get_completed_stocks(self) -> List[str]:
        """獲取已完成的股票ID清單"""
        try:
            if not self.completed_stocks_file.exists():
                return []
            
            with open(self.completed_stocks_file, 'r', encoding='utf-8') as f:
                completed = json.load(f)
            
            return [s["stock_id"] for s in completed]
            
        except Exception as e:
            print(f"⚠️ 讀取完成股票失敗: {e}")
            return []
    
    def get_failed_stocks(self) -> List[str]:
        """獲取失敗的股票ID清單"""
        try:
            if not self.failed_stocks_file.exists():
                return []
            
            with open(self.failed_stocks_file, 'r', encoding='utf-8') as f:
                failed = json.load(f)
            
            return [s["stock_id"] for s in failed]
            
        except Exception as e:
            print(f"⚠️ 讀取失敗股票失敗: {e}")
            return []
    
    def find_resume_position(self, all_stocks: List[Dict]) -> int:
        """找到續傳位置"""
        try:
            completed_ids = set(self.get_completed_stocks())
            
            # 找到第一個未完成的股票位置
            for i, stock in enumerate(all_stocks):
                stock_id = stock.get('stock_id', '')
                if stock_id not in completed_ids:
                    print(f"🔄 續傳位置: 第 {i+1} 檔股票 {stock_id}")
                    return i
            
            # 如果所有股票都完成了
            print("✅ 所有股票都已完成")
            return len(all_stocks)
            
        except Exception as e:
            print(f"⚠️ 查找續傳位置失敗: {e}")
            return 0
    
    def show_progress_summary(self):
        """顯示進度摘要"""
        try:
            print("\n📊 進度摘要")
            print("=" * 40)
            
            # 當前股票
            current = self.get_current_stock()
            if current:
                print(f"📍 當前股票: {current['stock_id']} {current.get('stock_name', '')}")
                print(f"📈 進度: {current.get('current_index', 0)}/{current.get('total_stocks', 0)} ({current.get('progress_percent', 0)}%)")
                print(f"🕒 最後更新: {current.get('last_updated', '')}")
            else:
                print("📍 當前股票: 無")
            
            # 完成統計
            completed = self.get_completed_stocks()
            failed = self.get_failed_stocks()
            
            print(f"✅ 已完成: {len(completed)} 檔")
            print(f"❌ 失敗: {len(failed)} 檔")
            
            if failed:
                print("\n❌ 失敗股票:")
                try:
                    with open(self.failed_stocks_file, 'r', encoding='utf-8') as f:
                        failed_data = json.load(f)
                    for stock in failed_data[-5:]:  # 顯示最近5個失敗
                        print(f"   {stock['stock_id']} - {stock.get('error_message', '')}")
                except:
                    pass
            
        except Exception as e:
            print(f"⚠️ 顯示進度摘要失敗: {e}")
    
    def clear_progress(self):
        """清除所有進度記錄"""
        try:
            files_to_clear = [
                self.current_stock_file,
                self.completed_stocks_file,
                self.failed_stocks_file
            ]
            
            for file_path in files_to_clear:
                if file_path.exists():
                    file_path.unlink()
            
            print("🧹 已清除所有進度記錄")
            
        except Exception as e:
            print(f"⚠️ 清除進度記錄失敗: {e}")

def main():
    """測試簡單進度記錄系統"""
    print("🧪 測試簡單進度記錄系統")
    print("=" * 40)
    
    # 創建進度記錄器
    progress = SimpleProgress("data/test_simple_progress")
    
    # 模擬股票清單
    test_stocks = [
        {"stock_id": "1101", "stock_name": "台泥"},
        {"stock_id": "1102", "stock_name": "亞泥"},
        {"stock_id": "2330", "stock_name": "台積電"},
        {"stock_id": "2317", "stock_name": "鴻海"},
    ]
    
    # 測試進度記錄
    print("\n1. 測試進度記錄")
    for i, stock in enumerate(test_stocks):
        progress.save_current_stock(
            stock["stock_id"], 
            stock["stock_name"], 
            len(test_stocks), 
            i + 1
        )
        
        if i == 1:  # 模擬第2檔完成
            progress.add_completed_stock(
                test_stocks[0]["stock_id"], 
                test_stocks[0]["stock_name"],
                ["股價", "月營收"]
            )
        elif i == 2:  # 模擬第3檔失敗
            progress.add_failed_stock(
                stock["stock_id"], 
                stock["stock_name"],
                "API連接失敗"
            )
    
    # 測試續傳位置查找
    print("\n2. 測試續傳位置查找")
    resume_pos = progress.find_resume_position(test_stocks)
    print(f"續傳位置: {resume_pos}")
    
    # 顯示進度摘要
    print("\n3. 進度摘要")
    progress.show_progress_summary()
    
    # 清理測試資料
    print("\n4. 清理測試資料")
    progress.clear_progress()
    
    import shutil
    test_dir = Path("data/test_simple_progress")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    print("✅ 測試完成")

if __name__ == "__main__":
    main()

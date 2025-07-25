#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣股票系統全面自動化測試和資料收集工作流程

這個腳本執行以下步驟：
1. 資料庫清理階段 - 清空所有資料表並驗證
2. 初始資料收集 - 執行10檔股票收集腳本
3. 錯誤檢測和修復 - 自動檢測並修復常見錯誤
4. 資料完整性驗證 - 檢查所有表的資料狀況
5. 收集增強 - 修改腳本以改善資料收集
6. 完整週期重新執行 - 清理並重新收集
7. 成功標準驗證 - 確認所有目標達成
"""

import sqlite3
import os
import sys
import subprocess
import time
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
    db_path = Config.DATABASE_PATH
except:
    db_path = "data/taiwan_stock.db"

# 預期的10檔精選股票
EXPECTED_STOCKS = ['2330', '2317', '2454', '2412', '2882', '2891', '2303', '2002', '1301', '0050']

# 預期的資料表
EXPECTED_TABLES = [
    'stocks', 'stock_prices', 'monthly_revenues', 'financial_statements',
    'balance_sheets', 'cash_flow_statements', 'dividend_policies',
    'dividend_results', 'financial_ratios', 'stock_scores'
]

class WorkflowLogger:
    """工作流程日誌記錄器"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.step_times = {}
        
    def log_step(self, step_name: str, message: str, status: str = "INFO"):
        """記錄步驟日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_symbol = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "PROGRESS": "🔄"
        }.get(status, "📝")
        
        print(f"[{timestamp}] {status_symbol} {step_name}: {message}")
        
    def start_step(self, step_name: str):
        """開始步驟計時"""
        self.step_times[step_name] = datetime.now()
        self.log_step(step_name, "開始執行", "PROGRESS")
        
    def end_step(self, step_name: str, success: bool = True):
        """結束步驟計時"""
        if step_name in self.step_times:
            duration = datetime.now() - self.step_times[step_name]
            status = "SUCCESS" if success else "ERROR"
            self.log_step(step_name, f"完成 (耗時: {duration.total_seconds():.1f}秒)", status)

class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self, logger: WorkflowLogger):
        self.logger = logger
        self.db_path = db_path
        
    def clear_database(self, max_attempts: int = 3) -> bool:
        """清空資料庫所有資料表"""
        self.logger.start_step("資料庫清理")
        
        for attempt in range(max_attempts):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 獲取所有資料表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                cleared_tables = []
                failed_tables = []
                
                for table_name in tables:
                    try:
                        cursor.execute(f"DELETE FROM {table_name}")
                        affected_rows = cursor.rowcount
                        cleared_tables.append((table_name, affected_rows))
                        self.logger.log_step("清理", f"{table_name}: {affected_rows} 筆資料")
                    except Exception as e:
                        failed_tables.append((table_name, str(e)))
                        self.logger.log_step("清理", f"{table_name} 失敗: {e}", "WARNING")
                
                conn.commit()
                conn.close()
                
                # 驗證清理結果
                if self.verify_empty_database():
                    self.logger.end_step("資料庫清理", True)
                    return True
                else:
                    self.logger.log_step("清理", f"第 {attempt + 1} 次嘗試未完全清空", "WARNING")
                    
            except Exception as e:
                self.logger.log_step("清理", f"第 {attempt + 1} 次嘗試失敗: {e}", "ERROR")
        
        self.logger.end_step("資料庫清理", False)
        return False
    
    def verify_empty_database(self) -> bool:
        """驗證資料庫是否為空"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            non_empty_tables = []
            for table_name in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                if count > 0:
                    non_empty_tables.append((table_name, count))
            
            conn.close()
            
            if non_empty_tables:
                self.logger.log_step("驗證", f"仍有 {len(non_empty_tables)} 個表有資料", "WARNING")
                for table_name, count in non_empty_tables:
                    self.logger.log_step("驗證", f"  {table_name}: {count} 筆", "WARNING")
                return False
            else:
                self.logger.log_step("驗證", f"所有 {len(tables)} 個表都是空的", "SUCCESS")
                return True
                
        except Exception as e:
            self.logger.log_step("驗證", f"檢查失敗: {e}", "ERROR")
            return False
    
    def check_data_completeness(self) -> Dict[str, Dict[str, int]]:
        """檢查資料完整性"""
        self.logger.start_step("資料完整性檢查")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 檢查每個表的資料狀況
            table_data = {}
            for table_name in EXPECTED_TABLES:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    total_count = cursor.fetchone()[0]
                    
                    # 檢查每檔股票的資料
                    stock_data = {}
                    if total_count > 0:
                        # 檢查是否有stock_id欄位
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        if 'stock_id' in columns:
                            for stock_id in EXPECTED_STOCKS:
                                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE stock_id = ?", (stock_id,))
                                count = cursor.fetchone()[0]
                                stock_data[stock_id] = count
                        else:
                            stock_data['total'] = total_count
                    
                    table_data[table_name] = {
                        'total': total_count,
                        'stocks': stock_data
                    }
                    
                    self.logger.log_step("檢查", f"{table_name}: {total_count:,} 筆總資料")
                    
                except Exception as e:
                    self.logger.log_step("檢查", f"{table_name} 檢查失敗: {e}", "ERROR")
                    table_data[table_name] = {'total': 0, 'stocks': {}}
            
            conn.close()
            self.logger.end_step("資料完整性檢查", True)
            return table_data
            
        except Exception as e:
            self.logger.log_step("檢查", f"檢查失敗: {e}", "ERROR")
            self.logger.end_step("資料完整性檢查", False)
            return {}

class ScriptExecutor:
    """腳本執行器"""
    
    def __init__(self, logger: WorkflowLogger):
        self.logger = logger
        
    def execute_collection_script(self, timeout: int = 1800) -> Tuple[bool, str, str]:
        """執行資料收集腳本"""
        self.logger.start_step("資料收集執行")
        
        cmd = [sys.executable, "scripts/collect_10_stocks_10years.py", "--batch-size", "3"]
        
        try:
            self.logger.log_step("執行", f"命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            success = result.returncode == 0
            self.logger.end_step("資料收集執行", success)
            
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            self.logger.log_step("執行", f"執行超時 ({timeout}秒)", "ERROR")
            self.logger.end_step("資料收集執行", False)
            return False, "", "執行超時"
        except Exception as e:
            self.logger.log_step("執行", f"執行失敗: {e}", "ERROR")
            self.logger.end_step("資料收集執行", False)
            return False, "", str(e)

class ErrorAnalyzer:
    """錯誤分析器"""
    
    def __init__(self, logger: WorkflowLogger):
        self.logger = logger
        
    def analyze_errors(self, stdout: str, stderr: str) -> List[Dict[str, str]]:
        """分析執行錯誤"""
        self.logger.start_step("錯誤分析")
        
        errors = []
        combined_output = stdout + "\n" + stderr
        
        # 檢測常見錯誤模式
        error_patterns = [
            {
                'type': 'Unicode編碼錯誤',
                'pattern': r"'cp950' codec can't encode character",
                'description': 'Windows命令提示字元無法顯示emoji字符'
            },
            {
                'type': 'API錯誤',
                'pattern': r'502 Server Error|Bad Gateway',
                'description': 'FinMind API服務器錯誤'
            },
            {
                'type': 'SQLite警告',
                'pattern': r'DeprecationWarning.*datetime adapter',
                'description': 'Python 3.12 SQLite日期適配器警告'
            },
            {
                'type': '導入錯誤',
                'pattern': r'ImportError|ModuleNotFoundError',
                'description': '模組導入失敗'
            },
            {
                'type': 'API限制',
                'pattern': r'API請求限制|402',
                'description': 'API請求頻率限制'
            }
        ]
        
        for error_info in error_patterns:
            if re.search(error_info['pattern'], combined_output, re.IGNORECASE):
                errors.append(error_info)
                self.logger.log_step("分析", f"發現 {error_info['type']}: {error_info['description']}", "WARNING")
        
        if not errors:
            self.logger.log_step("分析", "未發現已知錯誤模式", "SUCCESS")
        
        self.logger.end_step("錯誤分析", True)
        return errors

class ScriptFixer:
    """腳本修復器"""

    def __init__(self, logger: WorkflowLogger):
        self.logger = logger

    def fix_unicode_errors(self) -> bool:
        """修復Unicode編碼錯誤"""
        self.logger.start_step("Unicode修復")

        try:
            # 修復collect_10_stocks_10years.py中的emoji
            script_path = "scripts/collect_10_stocks_10years.py"

            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 移除常見的emoji字符
            emoji_replacements = {
                '📊 ': '',
                '🧪 ': '',
                '📈 ': '',
                '💰 ': '',
                '🎯 ': '',
                '✅ ': '',
                '❌ ': '',
                '🔄 ': '',
                '⏰ ': '',
                '⏳ ': ''
            }

            modified = False
            for emoji, replacement in emoji_replacements.items():
                if emoji in content:
                    content = content.replace(emoji, replacement)
                    modified = True
                    self.logger.log_step("修復", f"移除 {emoji}")

            if modified:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.log_step("修復", f"已更新 {script_path}", "SUCCESS")

            self.logger.end_step("Unicode修復", True)
            return True

        except Exception as e:
            self.logger.log_step("修復", f"Unicode修復失敗: {e}", "ERROR")
            self.logger.end_step("Unicode修復", False)
            return False

    def fix_sqlite_warnings(self) -> bool:
        """修復SQLite警告"""
        self.logger.start_step("SQLite修復")

        try:
            script_path = "scripts/collect_10_stocks_10years.py"

            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 檢查是否已經有SQLite適配器修復
            if 'sqlite3.register_adapter' not in content:
                # 在import部分添加SQLite適配器
                import_section = """import sqlite3
from datetime import datetime, timedelta

# 修復Python 3.12 SQLite日期適配器警告
sqlite3.register_adapter(datetime, lambda x: x.isoformat())
sqlite3.register_converter("TIMESTAMP", lambda x: datetime.fromisoformat(x.decode()))"""

                # 替換原有的import
                content = re.sub(
                    r'from datetime import datetime, timedelta',
                    import_section,
                    content
                )

                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.logger.log_step("修復", "已添加SQLite日期適配器", "SUCCESS")

            self.logger.end_step("SQLite修復", True)
            return True

        except Exception as e:
            self.logger.log_step("修復", f"SQLite修復失敗: {e}", "ERROR")
            self.logger.end_step("SQLite修復", False)
            return False

class WorkflowOrchestrator:
    """工作流程協調器"""

    def __init__(self):
        self.logger = WorkflowLogger()
        self.db_manager = DatabaseManager(self.logger)
        self.script_executor = ScriptExecutor(self.logger)
        self.error_analyzer = ErrorAnalyzer(self.logger)
        self.script_fixer = ScriptFixer(self.logger)

    def run_complete_workflow(self) -> bool:
        """執行完整的工作流程"""
        self.logger.log_step("工作流程", "開始台灣股票系統全面自動化測試", "INFO")

        # 階段1: 資料庫清理
        if not self.phase_1_database_cleanup():
            return False

        # 階段2: 初始資料收集
        success, stdout, stderr = self.phase_2_initial_collection()

        # 階段3: 錯誤檢測和修復
        if not success:
            if not self.phase_3_error_detection_and_fixing(stdout, stderr):
                return False
            # 重新執行收集
            success, stdout, stderr = self.phase_2_initial_collection()

        # 階段4: 資料完整性驗證
        data_status = self.phase_4_data_verification()

        # 階段5: 收集增強 (如果需要)
        if not self.is_data_complete(data_status):
            if not self.phase_5_collection_enhancement(data_status):
                return False

        # 階段6: 完整週期重新執行
        if not self.phase_6_full_cycle_reexecution():
            return False

        # 階段7: 成功標準驗證
        return self.phase_7_success_criteria_verification()

    def phase_1_database_cleanup(self) -> bool:
        """階段1: 資料庫清理"""
        self.logger.log_step("階段1", "開始資料庫清理階段", "INFO")
        return self.db_manager.clear_database()

    def phase_2_initial_collection(self) -> Tuple[bool, str, str]:
        """階段2: 初始資料收集"""
        self.logger.log_step("階段2", "開始初始資料收集階段", "INFO")
        return self.script_executor.execute_collection_script()

    def phase_3_error_detection_and_fixing(self, stdout: str, stderr: str) -> bool:
        """階段3: 錯誤檢測和修復"""
        self.logger.log_step("階段3", "開始錯誤檢測和修復階段", "INFO")

        errors = self.error_analyzer.analyze_errors(stdout, stderr)

        if not errors:
            return True

        # 根據錯誤類型進行修復
        for error in errors:
            if error['type'] == 'Unicode編碼錯誤':
                self.script_fixer.fix_unicode_errors()
            elif error['type'] == 'SQLite警告':
                self.script_fixer.fix_sqlite_warnings()

        return True

    def phase_4_data_verification(self) -> Dict[str, Dict[str, int]]:
        """階段4: 資料完整性驗證"""
        self.logger.log_step("階段4", "開始資料完整性驗證階段", "INFO")
        return self.db_manager.check_data_completeness()

    def phase_5_collection_enhancement(self, data_status: Dict) -> bool:
        """階段5: 收集增強"""
        self.logger.log_step("階段5", "開始收集增強階段", "INFO")

        # 分析缺失的資料並提供建議
        empty_tables = [table for table, data in data_status.items() if data['total'] == 0]

        if empty_tables:
            self.logger.log_step("增強", f"發現 {len(empty_tables)} 個空表: {', '.join(empty_tables)}", "WARNING")
            # 這裡可以添加具體的增強邏輯

        return True

    def phase_6_full_cycle_reexecution(self) -> bool:
        """階段6: 完整週期重新執行"""
        self.logger.log_step("階段6", "開始完整週期重新執行階段", "INFO")

        # 重新清理資料庫
        if not self.db_manager.clear_database():
            return False

        # 重新執行收集
        success, stdout, stderr = self.script_executor.execute_collection_script()
        return success

    def phase_7_success_criteria_verification(self) -> bool:
        """階段7: 成功標準驗證"""
        self.logger.log_step("階段7", "開始成功標準驗證階段", "INFO")

        data_status = self.db_manager.check_data_completeness()

        # 檢查成功標準
        success_criteria = {
            'all_tables_have_data': all(data['total'] > 0 for data in data_status.values()),
            'all_stocks_present': self.check_all_stocks_present(data_status),
            'reasonable_data_counts': self.check_reasonable_data_counts(data_status)
        }

        overall_success = all(success_criteria.values())

        self.logger.log_step("驗證", f"所有表有資料: {success_criteria['all_tables_have_data']}")
        self.logger.log_step("驗證", f"所有股票存在: {success_criteria['all_stocks_present']}")
        self.logger.log_step("驗證", f"資料量合理: {success_criteria['reasonable_data_counts']}")

        if overall_success:
            self.logger.log_step("成功", "所有成功標準都已達成！", "SUCCESS")
        else:
            self.logger.log_step("失敗", "部分成功標準未達成", "ERROR")

        return overall_success

    def is_data_complete(self, data_status: Dict) -> bool:
        """檢查資料是否完整"""
        return all(data['total'] > 0 for data in data_status.values())

    def check_all_stocks_present(self, data_status: Dict) -> bool:
        """檢查所有股票是否都存在"""
        for table_name, data in data_status.items():
            if 'stocks' in data and data['stocks']:
                missing_stocks = [stock for stock in EXPECTED_STOCKS if stock not in data['stocks'] or data['stocks'][stock] == 0]
                if missing_stocks:
                    self.logger.log_step("檢查", f"{table_name} 缺少股票: {missing_stocks}", "WARNING")
                    return False
        return True

    def check_reasonable_data_counts(self, data_status: Dict) -> bool:
        """檢查資料量是否合理"""
        # 定義最小預期資料量
        min_expected_counts = {
            'stocks': 10,
            'stock_prices': 1000,
            'monthly_revenues': 100,
            'financial_statements': 100,
            'balance_sheets': 100
        }

        for table_name, min_count in min_expected_counts.items():
            if table_name in data_status:
                actual_count = data_status[table_name]['total']
                if actual_count < min_count:
                    self.logger.log_step("檢查", f"{table_name} 資料量不足: {actual_count} < {min_count}", "WARNING")
                    return False

        return True

def main():
    """主函數"""
    print("=" * 80)
    print("🚀 台灣股票系統全面自動化測試和資料收集工作流程")
    print("=" * 80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目標股票: {', '.join(EXPECTED_STOCKS)}")
    print(f"目標資料表: {len(EXPECTED_TABLES)} 個")
    print("=" * 80)

    orchestrator = WorkflowOrchestrator()

    try:
        success = orchestrator.run_complete_workflow()

        print("\n" + "=" * 80)
        if success:
            print("🎉 工作流程執行成功！所有目標都已達成。")
        else:
            print("❌ 工作流程執行失敗，請檢查上述錯誤訊息。")

        total_time = datetime.now() - orchestrator.logger.start_time
        print(f"總執行時間: {total_time.total_seconds():.1f} 秒")
        print("=" * 80)

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷執行")
        return 1
    except Exception as e:
        print(f"\n❌ 工作流程執行異常: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

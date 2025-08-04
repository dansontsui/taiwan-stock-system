#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Taiwan Stock System - 跨平台啟動腳本
使用方法: python start.py [選項]
"""

import sys
import os
import subprocess
import shutil
import sqlite3
from pathlib import Path
from pathlib import Path

# 顏色定義 (支援 Windows 和 Unix)
class Colors:
    if os.name == 'nt':  # Windows
        try:
            import colorama
            colorama.init()
            RED = '\033[0;31m'
            GREEN = '\033[0;32m'
            YELLOW = '\033[1;33m'
            BLUE = '\033[0;34m'
            NC = '\033[0m'
        except ImportError:
            RED = GREEN = YELLOW = BLUE = NC = ''
    else:  # Unix/Linux/Mac
        RED = '\033[0;31m'
        GREEN = '\033[0;32m'
        YELLOW = '\033[1;33m'
        BLUE = '\033[0;34m'
        NC = '\033[0m'

def check_python():
    """檢查Python環境"""
    python_cmd = None
    
    # 檢查 python3
    if shutil.which('python3'):
        python_cmd = 'python3'
    # 檢查 python
    elif shutil.which('python'):
        python_cmd = 'python'
    else:
        print(f"{Colors.RED}[ERROR] 找不到Python，請先安裝Python{Colors.NC}")
        sys.exit(1)
    
    return python_cmd

def check_venv():
    """檢查虛擬環境"""
    virtual_env = os.environ.get('VIRTUAL_ENV')
    if virtual_env:
        venv_name = Path(virtual_env).name
        print(f"{Colors.GREEN}[OK] 虛擬環境已啟動: {venv_name}{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}[WARNING] 建議啟動虛擬環境{Colors.NC}")
        if os.name == 'nt':  # Windows
            print(f"{Colors.BLUE}[INFO] 執行: .venv\\Scripts\\activate.bat{Colors.NC}")
        else:  # Unix/Linux/Mac
            print(f"{Colors.BLUE}[INFO] 執行: source .venv/bin/activate{Colors.NC}")

def show_menu():
    """顯示選單"""
    print(f"{Colors.BLUE}Taiwan Stock System - 跨平台啟動腳本{Colors.NC}")
    print("=" * 60)
    print(f"{Colors.GREEN}請選擇要執行的功能:{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}基礎資料收集:{Colors.NC}")
    print("1. 收集基礎資料 - 所有股票 (2,822檔)")
    print("2. 收集基礎資料 - 主要股票 (50檔)")
    print("3. 收集基礎資料 - 測試模式 (5檔)")
    print()
    print(f"{Colors.YELLOW}進階資料收集:{Colors.NC}")
    print("4. 收集財務報表資料")
    print("5. 收集資產負債表資料")
    print("6. 收集股利相關資料")
    print("7. 執行潛力股分析")
    print()
    print(f"{Colors.YELLOW}完整收集與系統:{Colors.NC}")
    print("8. 完整資料收集 (全部階段)")
    print("9. 完整資料收集 (測試模式)")
    print("10. 逐股完整收集 (測試模式) - 每支股票收集完全部資料再換下一隻")
    print("11. 逐股完整收集 (自動執行) - 所有股票逐一完整收集")
    print("12. 每日增量更新 (智能檢查)")
    print("13. 每日增量更新 (測試模式)")
    print("14. 個股資料缺失查詢")
    print("15. 啟動Web介面")
    print()
    print("16. 顯示說明")
    print("0. 退出")
    print()
    print("=" * 60)

def check_specific_stock(stock_id, conn, cursor):
    """檢查特定股票的資料情況"""
    # 檢查股票是否存在
    cursor.execute("SELECT stock_id, stock_name, market FROM stocks WHERE stock_id = ?", (stock_id,))
    stock_info = cursor.fetchone()

    if not stock_info:
        print(f'{Colors.RED}❌ 找不到股票代碼: {stock_id}{Colors.NC}')
        return False

    stock_name = stock_info[1]
    market = stock_info[2]

    print(f'{Colors.BLUE}🔍 個股資料查詢: {stock_id} ({stock_name}) [{market}]{Colors.NC}')
    print('=' * 60)

    tables_to_check = [
        ('stock_prices', '股價資料'),
        ('monthly_revenues', '月營收資料'),
        ('financial_statements', '財務報表資料'),
        ('dividend_policies', '股利政策資料'),
        ('stock_scores', '潛力股分析'),
        ('dividend_results', '除權除息'),
        ('cash_flow_statements', '現金流量表')
    ]

    missing_count = 0
    total_tables = len(tables_to_check)

    for table_name, table_desc in tables_to_check:
        # 檢查資料表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f'{table_desc:15} : {Colors.RED}❌ 資料表不存在{Colors.NC}')
            missing_count += 1
            continue

        # 檢查該股票是否有資料
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE stock_id = ?", (stock_id,))
        record_count = cursor.fetchone()[0]

        if record_count > 0:
            # 獲取最新資料日期
            try:
                cursor.execute(f"SELECT MAX(date) FROM {table_name} WHERE stock_id = ?", (stock_id,))
                latest_date = cursor.fetchone()[0]
                if not latest_date:
                    try:
                        cursor.execute(f"SELECT MAX(analysis_date) FROM {table_name} WHERE stock_id = ?", (stock_id,))
                        latest_date = cursor.fetchone()[0]
                    except:
                        latest_date = '無日期'
            except:
                try:
                    cursor.execute(f"SELECT MAX(analysis_date) FROM {table_name} WHERE stock_id = ?", (stock_id,))
                    latest_date = cursor.fetchone()[0]
                except:
                    latest_date = '無日期'

            print(f'{table_desc:15} : {Colors.GREEN}✅ {record_count:,} 筆記錄 (最新: {latest_date}){Colors.NC}')
        else:
            print(f'{table_desc:15} : {Colors.RED}❌ 無資料{Colors.NC}')
            missing_count += 1

    # 顯示完整度統計
    completeness = ((total_tables - missing_count) / total_tables) * 100
    print(f'\n{Colors.YELLOW}資料完整度: {completeness:.1f}% ({total_tables-missing_count}/{total_tables}){Colors.NC}')

    if completeness >= 85:
        status_color = Colors.GREEN
        status = "優秀"
    elif completeness >= 60:
        status_color = Colors.YELLOW
        status = "良好"
    else:
        status_color = Colors.RED
        status = "需改善"

    print(f'{Colors.BLUE}整體評級: {status_color}{status}{Colors.NC}')
    return True

def check_missing_data():
    """檢查個股資料缺失情況"""
    db_path = Path('data/taiwan_stock.db')
    if not db_path.exists():
        print(f"{Colors.RED}[ERROR] 找不到資料庫檔案{Colors.NC}")
        return

    print(f"{Colors.BLUE}台股個股資料缺失查詢{Colors.NC}")
    print("=" * 60)

    # 詢問查詢類型
    print(f"{Colors.YELLOW}請選擇查詢類型:{Colors.NC}")
    print("1. 整體資料庫覆蓋率分析")
    print("2. 單一個股資料查詢")
    print("0. 返回")

    while True:
        try:
            choice = input(f"{Colors.YELLOW}請輸入選項 (0-2): {Colors.NC}").strip()
            if choice in ['0', '1', '2']:
                break
            else:
                print(f"{Colors.RED}[ERROR] 請輸入有效的選項 (0-2){Colors.NC}")
        except KeyboardInterrupt:
            print(f"\n{Colors.BLUE}[INFO] 操作已取消{Colors.NC}")
            return

    if choice == '0':
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        if choice == '2':
            # 單一個股查詢
            while True:
                stock_id = input(f"{Colors.YELLOW}請輸入股票代碼 (或輸入 'q' 退出): {Colors.NC}").strip().upper()
                if stock_id.lower() == 'q':
                    break
                if not stock_id:
                    print(f"{Colors.RED}[ERROR] 請輸入有效的股票代碼{Colors.NC}")
                    continue

                print()
                if check_specific_stock(stock_id, conn, cursor):
                    print(f"\n{Colors.GREEN}查詢完成{Colors.NC}")

                # 詢問是否繼續查詢
                continue_query = input(f"\n{Colors.YELLOW}是否查詢其他股票? (y/n): {Colors.NC}").strip().lower()
                if continue_query != 'y':
                    break
                print()

            conn.close()
            return

        # choice == '1' - 整體分析
        # 獲取股票總數
        cursor.execute("""
            SELECT COUNT(*) FROM stocks
            WHERE is_active = 1 AND stock_id NOT LIKE '00%'
            AND stock_id GLOB '[0-9]*'
        """)
        total_stocks = cursor.fetchone()[0]
        print(f"{Colors.GREEN}總股票數: {total_stocks:,} 檔{Colors.NC}")

        # 檢查各資料表
        tables = [
            ('stock_prices', '股價資料'),
            ('monthly_revenues', '月營收資料'),
            ('financial_statements', '財務報表資料'),
            ('dividend_policies', '股利政策資料'),
            ('stock_scores', '潛力股分析'),
            ('dividend_results', '除權除息'),
            ('cash_flow_statements', '現金流量表')
        ]

        print(f"\n{Colors.YELLOW}各資料表覆蓋情況:{Colors.NC}")
        print("-" * 60)

        for table_name, table_desc in tables:
            # 檢查資料表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f'{table_desc:15} : {Colors.RED}資料表不存在{Colors.NC}')
                continue

            # 獲取有資料的股票數
            cursor.execute(f"""
                SELECT COUNT(DISTINCT stock_id)
                FROM {table_name}
                WHERE stock_id IN (
                    SELECT stock_id FROM stocks
                    WHERE is_active = 1 AND stock_id NOT LIKE '00%'
                    AND stock_id GLOB '[0-9]*'
                )
            """)
            has_data_count = cursor.fetchone()[0]

            coverage_rate = (has_data_count / total_stocks) * 100 if total_stocks > 0 else 0
            missing_count = total_stocks - has_data_count

            # 狀態顏色
            if coverage_rate >= 95:
                color = Colors.GREEN
                status = "優秀"
            elif coverage_rate >= 80:
                color = Colors.YELLOW
                status = "良好"
            elif coverage_rate >= 50:
                color = Colors.YELLOW
                status = "普通"
            else:
                color = Colors.RED
                status = "需改善"

            print(f'{table_desc:15} : {color}{coverage_rate:5.1f}% ({has_data_count:,}/{total_stocks:,}) 缺失 {missing_count:,} - {status}{Colors.NC}')

        print(f"\n{Colors.GREEN}查詢完成{Colors.NC}")
        print(f"{Colors.BLUE}提示: 可使用 'python start.py daily' 進行資料更新{Colors.NC}")

    except Exception as e:
        print(f"{Colors.RED}[ERROR] 查詢過程發生錯誤: {e}{Colors.NC}")

    finally:
        conn.close()

def show_help():
    """顯示說明"""
    print(f"{Colors.BLUE}Taiwan Stock System - 跨平台啟動腳本{Colors.NC}")
    print()
    print(f"{Colors.GREEN}命令列用法:{Colors.NC}")
    print("  python start.py              # 顯示互動選單")
    print("  python start.py all          # 收集基礎資料 (所有股票)")
    print("  python start.py main         # 收集基礎資料 (主要股票)")
    print("  python start.py test         # 收集基礎資料 (測試模式)")
    print("  python start.py financial    # 收集財務報表資料")
    print("  python start.py balance      # 收集資產負債表資料")
    print("  python start.py dividend     # 收集股利相關資料")
    print("  python start.py analysis     # 執行潛力股分析")
    print("  python start.py complete     # 完整資料收集")
    print("  python start.py complete-test # 完整資料收集 (測試模式)")
    print("  python start.py stock-by-stock-test # 逐股完整收集 (測試模式)")
    print("  python start.py stock-by-stock-auto # 逐股完整收集 (自動執行)")
    print("  python start.py daily        # 每日增量更新")
    print("  python start.py daily-test   # 每日增量更新 (測試模式)")
    print("  python start.py check        # 個股資料缺失查詢")
    print("  python start.py web          # 啟動Web介面")
    print("  python start.py help         # 顯示說明")
    print()
    print(f"{Colors.GREEN}資料收集階段說明:{Colors.NC}")
    print("  基礎資料: 股票清單、股價、月營收、現金流")
    print("  財務報表: 綜合損益表")
    print("  資產負債: 資產負債表、財務比率")
    print("  股利資料: 股利政策、除權除息結果")
    print("  潛力分析: 股票評分、潛力股排名")
    print("  每日更新: 智能檢查並更新需要的資料")
    print("  資料查詢: 檢查個股資料完整性和缺失情況")
    print()
    print(f"{Colors.YELLOW}[提示]:{Colors.NC}")
    print("  - 首次使用請先執行: pip install -r requirements.txt")
    print("  - 建議在虛擬環境中運行")
    print("  - 按 Ctrl+C 停止收集")
    print("  - 完整收集需要較長時間，建議分階段執行")

def get_user_choice():
    """取得使用者選擇"""
    while True:
        try:
            choice = input(f"{Colors.YELLOW}請輸入選項 (0-16): {Colors.NC}").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16']:
                return choice
            else:
                print(f"{Colors.RED}[ERROR] 請輸入有效的選項 (0-16){Colors.NC}")
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[WARNING] 使用者中斷執行{Colors.NC}")
            sys.exit(0)
        except EOFError:
            print(f"\n{Colors.YELLOW}[WARNING] 輸入結束{Colors.NC}")
            sys.exit(0)

def run_command(python_cmd, script, args=None):
    """執行命令"""
    cmd = [python_cmd, script]
    if args:
        cmd.extend(args)

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}[ERROR] 執行失敗: {e}{Colors.NC}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[WARNING] 使用者中斷執行{Colors.NC}")
        sys.exit(0)

def execute_choice(choice, python_cmd):
    """執行使用者選擇的功能"""
    if choice == '1':
        print(f"{Colors.GREEN}[ALL] 啟動收集基礎資料 - 所有股票{Colors.NC}")
        run_command(python_cmd, 'c.py', ['all'])

    elif choice == '2':
        print(f"{Colors.GREEN}[MAIN] 啟動收集基礎資料 - 主要股票{Colors.NC}")
        run_command(python_cmd, 'c.py', ['main'])

    elif choice == '3':
        print(f"{Colors.GREEN}[TEST] 啟動收集基礎資料 - 測試模式{Colors.NC}")
        run_command(python_cmd, 'c.py', ['test'])

    elif choice == '4':
        print(f"{Colors.GREEN}[FINANCIAL] 啟動收集財務報表資料{Colors.NC}")
        run_command(python_cmd, 'c.py', ['financial'])

    elif choice == '5':
        print(f"{Colors.GREEN}[BALANCE] 啟動收集資產負債表資料{Colors.NC}")
        run_command(python_cmd, 'c.py', ['balance'])

    elif choice == '6':
        print(f"{Colors.GREEN}[DIVIDEND] 啟動收集股利相關資料{Colors.NC}")
        run_command(python_cmd, 'c.py', ['dividend'])

    elif choice == '7':
        print(f"{Colors.GREEN}[ANALYSIS] 啟動潛力股分析{Colors.NC}")
        run_command(python_cmd, 'c.py', ['analysis'])

    elif choice == '8':
        print(f"{Colors.GREEN}[COMPLETE] 完整資料收集 (全部階段){Colors.NC}")
        print("=" * 60)
        print("請選擇收集範圍:")
        print("1. 所有股票 (2,822檔) - 完整收集")
        print("2. 指定個股 - 單一股票完整收集")
        print("0. 返回")
        print()

        sub_choice = input("請輸入選項 (0-2): ").strip()

        if sub_choice == '1':
            print(f"{Colors.GREEN}[COMPLETE-ALL] 啟動完整資料收集 - 所有股票{Colors.NC}")
            run_command(python_cmd, 'c.py', ['complete'])
        elif sub_choice == '2':
            stock_id = input("請輸入股票代碼 (例如: 2330): ").strip()
            if stock_id:
                print(f"{Colors.GREEN}[COMPLETE-STOCK] 啟動完整資料收集 - 個股 {stock_id}{Colors.NC}")
                run_command(python_cmd, 'c.py', ['complete', '--stock-id', stock_id])
            else:
                print(f"{Colors.RED}❌ 股票代碼不能為空{Colors.NC}")
                input("按 Enter 鍵返回選單...")
        elif sub_choice == '0':
            return
        else:
            print(f"{Colors.RED}❌ 無效選項{Colors.NC}")
            input("按 Enter 鍵返回選單...")

    elif choice == '9':
        print(f"{Colors.GREEN}[COMPLETE-TEST] 啟動完整資料收集 (測試模式){Colors.NC}")
        run_command(python_cmd, 'c.py', ['complete-test'])

    elif choice == '10':
        print(f"{Colors.GREEN}[STOCK-BY-STOCK] 啟動逐股完整收集 (測試模式){Colors.NC}")
        run_command(python_cmd, 'c.py', ['stock-by-stock-test'])

    elif choice == '11':
        print(f"{Colors.GREEN}[STOCK-BY-STOCK-AUTO] 啟動逐股完整收集 (自動執行){Colors.NC}")
        print("=" * 60)

        # 檢查是否有進度管理功能
        try:
            from scripts.progress_manager import ProgressManager
            progress_manager = ProgressManager()
            tasks = progress_manager.list_tasks()

            # 過濾出逐股收集的未完成任務
            stock_by_stock_tasks = []
            for task in tasks:
                if (task.get('task_type') == 'comprehensive' and
                    task.get('status') in ['not_started', 'in_progress'] and
                    ('逐股' in str(task.get('task_name', '')) or
                     'stock_by_stock' in str(task.get('task_name', '')).lower())):
                    stock_by_stock_tasks.append(task)

            if stock_by_stock_tasks:
                print(f"{Colors.YELLOW}發現 {len(stock_by_stock_tasks)} 個未完成的逐股收集任務:{Colors.NC}")
                for i, task in enumerate(stock_by_stock_tasks, 1):
                    progress_pct = (task['completed_stocks'] / task['total_stocks'] * 100) if task['total_stocks'] > 0 else 0
                    print(f"  {i}. {task['task_name']}")
                    print(f"     進度: {task['completed_stocks']}/{task['total_stocks']} ({progress_pct:.1f}%)")
                    print(f"     ID: {task['task_id']}")
                print()

                print("請選擇操作:")
                print("1. 開始新的逐股收集任務")
                print("2. 續傳現有任務")
                print("3. 重置並重新開始任務")
                print("0. 返回")
                print()

                sub_choice = input("請輸入選項 (0-3): ").strip()

                if sub_choice == '1':
                    # 開始新任務
                    print(f"{Colors.YELLOW}[WARNING] 這將處理所有股票，需要很長時間！{Colors.NC}")
                    confirm = input(f"{Colors.YELLOW}確定要開始新任務嗎？(y/N): {Colors.NC}").strip().lower()
                    if confirm == 'y':
                        run_command(python_cmd, 'c.py', ['stock-by-stock-auto'])
                    else:
                        print(f"{Colors.BLUE}[CANCELLED] 已取消執行{Colors.NC}")

                elif sub_choice == '2':
                    # 續傳任務
                    if len(stock_by_stock_tasks) == 1:
                        task_id = stock_by_stock_tasks[0]['task_id']
                        print(f"{Colors.GREEN}續傳任務: {stock_by_stock_tasks[0]['task_name']}{Colors.NC}")
                    else:
                        print("請選擇要續傳的任務:")
                        for i, task in enumerate(stock_by_stock_tasks, 1):
                            print(f"  {i}. {task['task_name']}")

                        task_choice = input(f"請輸入任務編號 (1-{len(stock_by_stock_tasks)}): ").strip()
                        try:
                            task_index = int(task_choice) - 1
                            if 0 <= task_index < len(stock_by_stock_tasks):
                                task_id = stock_by_stock_tasks[task_index]['task_id']
                                print(f"{Colors.GREEN}續傳任務: {stock_by_stock_tasks[task_index]['task_name']}{Colors.NC}")
                            else:
                                print(f"{Colors.RED}❌ 無效的任務編號{Colors.NC}")
                                return
                        except ValueError:
                            print(f"{Colors.RED}❌ 請輸入有效的數字{Colors.NC}")
                            return

                    run_command(python_cmd, 'c.py', ['stock-by-stock-auto', '--resume-task', task_id])

                elif sub_choice == '3':
                    # 重置任務
                    if len(stock_by_stock_tasks) == 1:
                        task_id = stock_by_stock_tasks[0]['task_id']
                        task_name = stock_by_stock_tasks[0]['task_name']
                    else:
                        print("請選擇要重置的任務:")
                        for i, task in enumerate(stock_by_stock_tasks, 1):
                            print(f"  {i}. {task['task_name']}")

                        task_choice = input(f"請輸入任務編號 (1-{len(stock_by_stock_tasks)}): ").strip()
                        try:
                            task_index = int(task_choice) - 1
                            if 0 <= task_index < len(stock_by_stock_tasks):
                                task_id = stock_by_stock_tasks[task_index]['task_id']
                                task_name = stock_by_stock_tasks[task_index]['task_name']
                            else:
                                print(f"{Colors.RED}❌ 無效的任務編號{Colors.NC}")
                                return
                        except ValueError:
                            print(f"{Colors.RED}❌ 請輸入有效的數字{Colors.NC}")
                            return

                    print(f"{Colors.YELLOW}⚠️ 即將重置任務: {task_name}{Colors.NC}")
                    print(f"   任務ID: {task_id}")
                    print(f"   這將清除所有進度記錄，重新開始收集")

                    confirm = input(f"{Colors.YELLOW}確定要重置嗎？(y/N): {Colors.NC}").strip().lower()
                    if confirm == 'y':
                        progress_manager.reset_task(task_id)
                        print(f"{Colors.GREEN}✅ 任務已重置{Colors.NC}")

                        start_confirm = input(f"{Colors.YELLOW}是否立即開始重置後的任務？(y/N): {Colors.NC}").strip().lower()
                        if start_confirm == 'y':
                            run_command(python_cmd, 'c.py', ['stock-by-stock-auto', '--resume-task', task_id])
                    else:
                        print(f"{Colors.BLUE}[CANCELLED] 已取消重置{Colors.NC}")

                elif sub_choice == '0':
                    return
                else:
                    print(f"{Colors.RED}❌ 無效選項{Colors.NC}")
                    input("按 Enter 鍵返回選單...")
            else:
                # 沒有未完成任務，直接開始新任務
                print(f"{Colors.YELLOW}[WARNING] 這將處理所有股票，需要很長時間！{Colors.NC}")
                confirm = input(f"{Colors.YELLOW}確定要繼續嗎？(y/N): {Colors.NC}").strip().lower()
                if confirm == 'y':
                    run_command(python_cmd, 'c.py', ['stock-by-stock-auto'])
                else:
                    print(f"{Colors.BLUE}[CANCELLED] 已取消執行{Colors.NC}")

        except ImportError:
            # 沒有進度管理功能，使用原來的邏輯
            print(f"{Colors.YELLOW}[WARNING] 這將處理所有股票，需要很長時間！{Colors.NC}")
            confirm = input(f"{Colors.YELLOW}確定要繼續嗎？(y/N): {Colors.NC}").strip().lower()
            if confirm == 'y':
                run_command(python_cmd, 'c.py', ['stock-by-stock-auto'])
            else:
                print(f"{Colors.BLUE}[CANCELLED] 已取消執行{Colors.NC}")

    elif choice == '12':
        print(f"{Colors.GREEN}[DAILY] 啟動每日增量更新{Colors.NC}")
        run_command(python_cmd, 'scripts/collect_daily_update.py')

    elif choice == '13':
        print(f"{Colors.GREEN}[DAILY-TEST] 啟動每日增量更新 (測試模式){Colors.NC}")
        run_command(python_cmd, 'scripts/collect_daily_update.py', ['--test'])

    elif choice == '14':
        print(f"{Colors.GREEN}[CHECK] 個股資料缺失查詢{Colors.NC}")
        check_missing_data()

    elif choice == '15':
        print(f"{Colors.GREEN}[WEB] 啟動Web介面{Colors.NC}")
        run_command(python_cmd, 'run.py')

    elif choice == '16':
        show_help()
        input(f"\n{Colors.BLUE}按 Enter 鍵返回選單...{Colors.NC}")

    elif choice == '0':
        print(f"{Colors.BLUE}[INFO] 感謝使用 Taiwan Stock System！{Colors.NC}")
        sys.exit(0)

def main():
    """主程式"""
    print(f"{Colors.BLUE}[START] Taiwan Stock System 啟動中...{Colors.NC}")

    # 檢查環境
    python_cmd = check_python()
    check_venv()
    print()

    # 如果有命令列參數，直接執行對應功能
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ['all', 'a']:
            print(f"{Colors.GREEN}[ALL] 啟動收集基礎資料 - 所有股票{Colors.NC}")
            run_command(python_cmd, 'c.py', ['all'])

        elif arg in ['main', 'm']:
            print(f"{Colors.GREEN}[MAIN] 啟動收集基礎資料 - 主要股票{Colors.NC}")
            run_command(python_cmd, 'c.py', ['main'])

        elif arg in ['test', 't']:
            print(f"{Colors.GREEN}[TEST] 啟動收集基礎資料 - 測試模式{Colors.NC}")
            run_command(python_cmd, 'c.py', ['test'])

        elif arg in ['financial', 'f']:
            print(f"{Colors.GREEN}[FINANCIAL] 啟動收集財務報表資料{Colors.NC}")
            run_command(python_cmd, 'c.py', ['financial'])

        elif arg in ['balance', 'b']:
            print(f"{Colors.GREEN}[BALANCE] 啟動收集資產負債表資料{Colors.NC}")
            run_command(python_cmd, 'c.py', ['balance'])

        elif arg in ['dividend', 'd']:
            print(f"{Colors.GREEN}[DIVIDEND] 啟動收集股利相關資料{Colors.NC}")
            run_command(python_cmd, 'c.py', ['dividend'])

        elif arg in ['analysis', 'analyze']:
            print(f"{Colors.GREEN}[ANALYSIS] 啟動潛力股分析{Colors.NC}")
            run_command(python_cmd, 'c.py', ['analysis'])

        elif arg in ['complete', 'c']:
            print(f"{Colors.GREEN}[COMPLETE] 啟動完整資料收集{Colors.NC}")
            run_command(python_cmd, 'c.py', ['complete'])

        elif arg in ['complete-test', 'ct']:
            print(f"{Colors.GREEN}[COMPLETE-TEST] 啟動完整資料收集 (測試模式){Colors.NC}")
            run_command(python_cmd, 'c.py', ['complete-test'])

        elif arg in ['stock-by-stock-test', 'sbs-test', 'sbs']:
            print(f"{Colors.GREEN}[STOCK-BY-STOCK] 啟動逐股完整收集 (測試模式){Colors.NC}")
            run_command(python_cmd, 'c.py', ['stock-by-stock-test'])

        elif arg in ['stock-by-stock-auto', 'sbs-auto', 'sbs-all']:
            print(f"{Colors.GREEN}[STOCK-BY-STOCK-AUTO] 啟動逐股完整收集 (自動執行){Colors.NC}")
            print(f"{Colors.YELLOW}[WARNING] 這將處理所有股票，需要很長時間！{Colors.NC}")
            run_command(python_cmd, 'c.py', ['stock-by-stock-auto'])

        elif arg in ['daily', 'daily-update']:
            print(f"{Colors.GREEN}[DAILY] 啟動每日增量更新{Colors.NC}")
            run_command(python_cmd, 'scripts/collect_daily_update.py')

        elif arg in ['daily-test', 'dt']:
            print(f"{Colors.GREEN}[DAILY-TEST] 啟動每日增量更新 (測試模式){Colors.NC}")
            run_command(python_cmd, 'scripts/collect_daily_update.py', ['--test'])

        elif arg in ['check', 'missing']:
            print(f"{Colors.GREEN}[CHECK] 個股資料缺失查詢{Colors.NC}")
            check_missing_data()

        elif arg in ['web', 'w']:
            print(f"{Colors.GREEN}[WEB] 啟動Web介面{Colors.NC}")
            run_command(python_cmd, 'run.py')

        elif arg in ['help', 'h', '--help', '-h']:
            show_help()

        else:
            print(f"{Colors.RED}[ERROR] 未知選項: {sys.argv[1]}{Colors.NC}")
            print(f"{Colors.BLUE}[INFO] 使用 'python start.py help' 查看說明{Colors.NC}")
            sys.exit(1)

    else:
        # 沒有參數時顯示互動式選單
        while True:
            try:
                show_menu()
                choice = get_user_choice()
                print()

                if choice == '0':
                    print(f"{Colors.BLUE}[INFO] 感謝使用 Taiwan Stock System！{Colors.NC}")
                    break
                elif choice == '5':
                    show_help()
                    input(f"\n{Colors.BLUE}按 Enter 鍵返回選單...{Colors.NC}")
                    print()
                else:
                    execute_choice(choice, python_cmd)
                    input(f"\n{Colors.BLUE}按 Enter 鍵返回選單...{Colors.NC}")
                    print()

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[WARNING] 使用者中斷執行{Colors.NC}")
                break

if __name__ == '__main__':
    main()

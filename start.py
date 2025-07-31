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
    print("10. 每日增量更新 (智能檢查)")
    print("11. 每日增量更新 (測試模式)")
    print("12. 啟動Web介面")
    print()
    print("13. 顯示說明")
    print("0. 退出")
    print()
    print("=" * 60)

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
    print("  python start.py daily        # 每日增量更新")
    print("  python start.py daily-test   # 每日增量更新 (測試模式)")
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
            choice = input(f"{Colors.YELLOW}請輸入選項 (0-13): {Colors.NC}").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13']:
                return choice
            else:
                print(f"{Colors.RED}[ERROR] 請輸入有效的選項 (0-13){Colors.NC}")
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
        print(f"{Colors.GREEN}[COMPLETE] 啟動完整資料收集{Colors.NC}")
        run_command(python_cmd, 'c.py', ['complete'])

    elif choice == '9':
        print(f"{Colors.GREEN}[COMPLETE-TEST] 啟動完整資料收集 (測試模式){Colors.NC}")
        run_command(python_cmd, 'c.py', ['complete-test'])

    elif choice == '10':
        print(f"{Colors.GREEN}[DAILY] 啟動每日增量更新{Colors.NC}")
        run_command(python_cmd, 'scripts/collect_daily_update.py')

    elif choice == '11':
        print(f"{Colors.GREEN}[DAILY-TEST] 啟動每日增量更新 (測試模式){Colors.NC}")
        run_command(python_cmd, 'scripts/collect_daily_update.py', ['--test'])

    elif choice == '12':
        print(f"{Colors.GREEN}[WEB] 啟動Web介面{Colors.NC}")
        run_command(python_cmd, 'run.py')

    elif choice == '13':
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

        elif arg in ['daily', 'daily-update']:
            print(f"{Colors.GREEN}[DAILY] 啟動每日增量更新{Colors.NC}")
            run_command(python_cmd, 'scripts/collect_daily_update.py')

        elif arg in ['daily-test', 'dt']:
            print(f"{Colors.GREEN}[DAILY-TEST] 啟動每日增量更新 (測試模式){Colors.NC}")
            run_command(python_cmd, 'scripts/collect_daily_update.py', ['--test'])

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

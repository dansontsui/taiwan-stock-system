#!/usr/bin/env python3
"""
完整的台股資料收集啟動器
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

def get_financial_dates():
    """獲取財務資料日期範圍 (5年)"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=5*365)
    return start_date.isoformat(), end_date.isoformat()

def get_dividend_dates():
    """獲取股利資料日期範圍 (10年)"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=10*365)
    return start_date.isoformat(), end_date.isoformat()

def run_script(script_name, args=None, description=""):
    """執行指定腳本"""
    script_path = Path(__file__).parent / "scripts" / script_name

    # 檢查腳本是否存在
    if not script_path.exists():
        print(f"[ERROR] 腳本不存在: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    print(f"[START] {description}")
    print(f"[SCRIPT] {script_name}")
    print(f"[PATH] {script_path}")
    if args:
        print(f"[ARGS] {' '.join(args)}")
    print(f"[CMD] {' '.join(cmd)}")
    print("=" * 50)

    try:
        result = subprocess.run(cmd, check=True)
        print(f"[SUCCESS] {description} 完成")
        return True
    except KeyboardInterrupt:
        print(f"\n[WARNING] {description} 已停止")
        return False
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] {description} 執行失敗，返回碼: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n[ERROR] {description} 錯誤: {e}")
        return False

def run_collect(start_date, end_date, batch_size, stock_scope):
    """執行基礎資料收集"""
    script_path = Path(__file__).parent / "simple_collect.py"

    cmd = [
        sys.executable,
        str(script_path)
    ]

    # 根據 stock_scope 決定是否加入 --test 參數
    if stock_scope == "test":
        cmd.append("--test")

    print(f"[START] 啟動基礎資料收集: {stock_scope} 範圍, 批次大小 {batch_size}")
    print(f"[DATE] {start_date} ~ {end_date}")
    print("[INFO] 按 Ctrl+C 停止")
    print("=" * 50)

    try:
        subprocess.run(cmd, check=True)
        return True
    except KeyboardInterrupt:
        print("\n[WARNING] 基礎資料收集已停止")
        return False
    except Exception as e:
        print(f"\n[ERROR] 基礎資料收集錯誤: {e}")
        return False

def run_financial_collection(test_mode=False):
    """執行財務報表資料收集"""
    start_date, end_date = get_financial_dates()
    args = [
        '--start-date', start_date,
        '--end-date', end_date,
        '--batch-size', '3'
    ]
    if test_mode:
        args.append('--test')

    return run_script('collect_financial_statements.py', args, '財務報表資料收集')

def run_balance_collection(test_mode=False):
    """執行資產負債表資料收集"""
    start_date, end_date = get_financial_dates()
    args = [
        '--start-date', start_date,
        '--end-date', end_date,
        '--batch-size', '3'
    ]
    if test_mode:
        args.append('--test')

    return run_script('collect_balance_sheets.py', args, '資產負債表資料收集')

def run_dividend_collection(test_mode=False):
    """執行股利資料收集"""
    start_date, end_date = get_dividend_dates()
    args = [
        '--start-date', start_date,
        '--end-date', end_date,
        '--batch-size', '3'
    ]
    if test_mode:
        args.append('--test')

    # 收集股利政策
    success1 = run_script('collect_dividend_data.py', args, '股利政策資料收集')

    # 收集除權除息結果
    success2 = run_script('collect_dividend_results.py', args, '除權除息結果收集')

    return success1 and success2

def run_analysis(stock_id=None, top=20):
    """執行潛力股分析"""
    args = ['--top', str(top)]
    if stock_id:
        args.extend(['--stock-id', stock_id])

    return run_script('analyze_potential_stocks.py', args, '潛力股分析')

def run_complete_collection(test_mode=False):
    """執行完整資料收集"""
    print("[COMPLETE] 開始完整資料收集流程")
    print("=" * 60)

    success_count = 0
    total_steps = 5

    # 階段1: 基礎資料收集
    print("\n階段 1/5: 基礎資料收集 (股價、月營收、現金流)")
    start_date, end_date = get_default_dates()
    scope = "test" if test_mode else "all"
    if run_collect(start_date, end_date, 5, scope):
        success_count += 1

    # 階段2: 財務報表收集
    print("\n階段 2/5: 財務報表資料收集")
    if run_financial_collection(test_mode):
        success_count += 1

    # 階段3: 資產負債表收集
    print("\n階段 3/5: 資產負債表資料收集")
    if run_balance_collection(test_mode):
        success_count += 1

    # 階段4: 股利資料收集
    print("\n階段 4/5: 股利資料收集")
    if run_dividend_collection(test_mode):
        success_count += 1

    # 階段5: 潛力股分析
    print("\n階段 5/5: 潛力股分析")
    top_count = 5 if test_mode else 50
    if run_analysis(top=top_count):
        success_count += 1

    # 總結
    print("\n" + "=" * 60)
    print(f"[COMPLETE] 完整收集流程結束")
    print(f"[RESULT] 成功完成 {success_count}/{total_steps} 個階段")
    if success_count == total_steps:
        print("[SUCCESS] 所有階段都成功完成！")
    else:
        print(f"[WARNING] 有 {total_steps - success_count} 個階段未成功完成")
    print("=" * 60)

def show_help():
    """顯示說明"""
    print("[HELP] 台股資料收集系統 - 完整版")
    print("=" * 50)
    print("基礎收集選項:")
    print("  python c.py              # 收集基礎資料 (預設)")
    print("  python c.py all          # 收集基礎資料 (所有股票)")
    print("  python c.py main         # 收集基礎資料 (主要50檔)")
    print("  python c.py test         # 收集基礎資料 (測試5檔)")
    print()
    print("進階收集選項:")
    print("  python c.py financial    # 收集財務報表資料")
    print("  python c.py balance      # 收集資產負債表資料")
    print("  python c.py dividend     # 收集股利相關資料")
    print("  python c.py analysis     # 執行潛力股分析")
    print()
    print("完整收集選項:")
    print("  python c.py complete     # 完整資料收集 (全部階段)")
    print("  python c.py complete-test # 完整資料收集 (測試模式)")
    print()
    print("說明:")
    print("  python c.py help         # 顯示此說明")
    print()
    print("資料收集階段說明:")
    print("  基礎資料: 股票清單、股價、月營收、現金流")
    print("  財務報表: 綜合損益表")
    print("  資產負債: 資產負債表、財務比率")
    print("  股利資料: 股利政策、除權除息結果")
    print("  潛力分析: 股票評分、潛力股排名")

def main():
    """主程式"""
    start_date, end_date = get_default_dates()

    if len(sys.argv) == 1:
        # 無參數 = 執行完整收集
        print("[DEFAULT] 執行完整資料收集 (預設)")
        run_complete_collection(test_mode=False)

    elif len(sys.argv) == 2:
        option = sys.argv[1].lower()

        if option in ['all', 'a']:
            print("[ALL] 收集基礎資料 - 所有股票")
            run_collect(start_date, end_date, 5, "all")

        elif option in ['main', 'm']:
            print("[MAIN] 收集基礎資料 - 主要股票")
            run_collect(start_date, end_date, 5, "main")

        elif option in ['test', 't']:
            print("[TEST] 收集基礎資料 - 測試模式")
            run_collect(start_date, end_date, 1, "test")

        elif option in ['financial', 'f']:
            print("[FINANCIAL] 收集財務報表資料")
            run_financial_collection(test_mode=False)

        elif option in ['balance', 'b']:
            print("[BALANCE] 收集資產負債表資料")
            run_balance_collection(test_mode=False)

        elif option in ['dividend', 'd']:
            print("[DIVIDEND] 收集股利相關資料")
            run_dividend_collection(test_mode=False)

        elif option in ['analysis', 'analyze']:
            print("[ANALYSIS] 執行潛力股分析")
            run_analysis(top=50)

        elif option in ['complete', 'c']:
            print("[COMPLETE] 執行完整資料收集")
            run_complete_collection(test_mode=False)

        elif option in ['complete-test', 'ct']:
            print("[COMPLETE-TEST] 執行完整資料收集 (測試模式)")
            run_complete_collection(test_mode=True)

        elif option in ['help', 'h', '--help', '-h']:
            show_help()

        else:
            print(f"[ERROR] 未知選項: {option}")
            print("[INFO] 使用 'python c.py help' 查看說明")

    else:
        print("[ERROR] 參數過多")
        print("[INFO] 使用 'python c.py help' 查看說明")

if __name__ == "__main__":
    main()

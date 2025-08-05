#!/usr/bin/env python3
"""
完整的台股資料收集啟動器 - 支援斷點續傳
用法: python c.py [選項]
"""

import sys
import subprocess
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 導入簡單進度記錄系統
try:
    from scripts.simple_progress import SimpleProgress
    PROGRESS_ENABLED = True
except ImportError:
    print("[WARNING] 無法導入簡單進度記錄系統，進度記錄功能將被停用")
    PROGRESS_ENABLED = False

def get_default_dates():
    """獲取預設日期範圍 (固定起始日期)"""
    end_date = datetime.now().date()
    start_date = "2010-01-01"  # 固定起始日期，避免資料遺失
    return start_date, end_date.isoformat()

def get_financial_dates():
    """獲取財務資料日期範圍 (固定起始日期)"""
    end_date = datetime.now().date()
    start_date = "2010-01-01"  # 固定起始日期，避免資料遺失
    return start_date, end_date.isoformat()

def get_dividend_dates():
    """獲取股利資料日期範圍 (固定起始日期)"""
    end_date = datetime.now().date()
    start_date = "2010-01-01"  # 固定起始日期，避免資料遺失
    return start_date, end_date.isoformat()

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
        result = subprocess.run(cmd, check=True, encoding='utf-8', errors='replace')
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
        str(script_path),
        "--start-date", start_date,
        "--end-date", end_date
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

def run_collect_with_stock(start_date, end_date, batch_size, stock_scope, stock_id):
    """執行基礎資料收集 - 指定個股"""
    script_path = Path(__file__).parent / "simple_collect.py"

    cmd = [
        sys.executable,
        str(script_path),
        "--start-date", start_date,
        "--end-date", end_date,
        "--test",  # 個股模式使用測試範圍
        "--stock-id", stock_id
    ]

    print(f"[START] 啟動基礎資料收集: 個股 {stock_id}, 批次大小 {batch_size}")
    print(f"[DATE] {start_date} ~ {end_date}")
    print("[INFO] 按 Ctrl+C 停止")
    print("=" * 50)

    try:
        subprocess.run(cmd, check=True)
        print(f"[SUCCESS] 個股 {stock_id} 基礎資料收集完成")
        return True
    except KeyboardInterrupt:
        print(f"\n[WARNING] 個股 {stock_id} 基礎資料收集已停止")
        return False
    except Exception as e:
        print(f"\n[ERROR] 個股 {stock_id} 基礎資料收集錯誤: {e}")
        return False

def run_financial_collection(test_mode=False, stock_id=None):
    """執行財務報表資料收集"""
    start_date, end_date = get_financial_dates()
    args = [
        '--start-date', start_date,
        '--end-date', end_date,
        '--batch-size', '3'
    ]
    if test_mode:
        args.append('--test')
    if stock_id:
        args.extend(['--stock-id', stock_id])

    return run_script('collect_financial_statements.py', args, '財務報表資料收集')

def run_balance_collection(test_mode=False, stock_id=None):
    """執行資產負債表資料收集"""
    start_date, end_date = get_financial_dates()
    args = [
        '--start-date', start_date,
        '--end-date', end_date,
        '--batch-size', '3'
    ]
    if test_mode:
        args.append('--test')
    if stock_id:
        args.extend(['--stock-id', stock_id])

    return run_script('collect_balance_sheets.py', args, '資產負債表資料收集')

def run_dividend_collection(test_mode=False, stock_id=None):
    """執行股利資料收集"""
    start_date, end_date = get_dividend_dates()
    args = [
        '--start-date', start_date,
        '--end-date', end_date,
        '--batch-size', '3'
    ]
    if test_mode:
        args.append('--test')
    if stock_id:
        args.extend(['--stock-id', stock_id])

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

def setup_logging():
    """設定日誌"""
    log_file = f"stock_by_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ],
        force=True
    )

    logger = logging.getLogger(__name__)
    logger.info(f"日誌檔案: {log_file}")
    return logger

def get_test_stock_list():
    """獲取測試用股票清單"""
    # 測試用股票清單 (5檔知名股票)
    return ['2330', '2317', '2454', '2412', '6505']

def get_all_stock_list():
    """從資料庫獲取所有活躍股票清單"""
    db_path = Path('data/taiwan_stock.db')
    if not db_path.exists():
        print(f"[ERROR] 資料庫檔案不存在: {db_path}")
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 獲取所有活躍的股票，排除ETF和特殊代碼
        cursor.execute("""
            SELECT stock_id, stock_name
            FROM stocks
            WHERE is_active = 1
            AND stock_id NOT LIKE '00%'  -- 排除ETF
            AND stock_id GLOB '[0-9]*'   -- 只要數字開頭的
            AND LENGTH(stock_id) = 4     -- 只要4位數的
            ORDER BY stock_id
        """)

        results = cursor.fetchall()
        conn.close()

        stock_list = [row[0] for row in results]
        print(f"[INFO] 從資料庫獲取 {len(stock_list)} 檔股票")

        return stock_list

    except Exception as e:
        print(f"[ERROR] 獲取股票清單失敗: {e}")
        return []

def check_stock_data_completeness(stock_id, logger):
    """檢查股票資料完整性和時效性"""
    db_path = Path('data/taiwan_stock.db')
    if not db_path.exists():
        return False, "資料庫不存在"

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 檢查股票是否存在
        cursor.execute("SELECT stock_name FROM stocks WHERE stock_id = ?", (stock_id,))
        stock_info = cursor.fetchone()
        if not stock_info:
            conn.close()
            return False, "股票不存在"

        stock_name = stock_info[0]

        # 獲取當前日期和時間閾值
        current_date = datetime.now().date()

        # 定義各資料表的時效性要求
        tables_to_check = [
            ('stock_prices', '股價資料', 7),        # 股價資料：7天內
            ('monthly_revenues', '月營收資料', 45),  # 月營收：45天內 (考慮公布時間)
            ('financial_statements', '財務報表資料', 120),  # 財報：120天內 (季報)
            ('dividend_policies', '股利政策資料', 365),      # 股利政策：365天內 (年度)
            ('stock_scores', '潛力股分析', 30)       # 潛力股分析：30天內
        ]

        missing_or_outdated = []
        total_tables = len(tables_to_check)

        for table_name, table_desc, days_threshold in tables_to_check:
            # 檢查資料表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                missing_or_outdated.append(f"{table_desc}(表不存在)")
                continue

            # 檢查該股票是否有資料
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE stock_id = ?", (stock_id,))
            record_count = cursor.fetchone()[0]

            if record_count == 0:
                missing_or_outdated.append(f"{table_desc}(無資料)")
                continue

            # 檢查資料時效性
            threshold_date = current_date - timedelta(days=days_threshold)

            # 根據不同資料表使用不同的日期欄位
            date_column = 'date'
            if table_name == 'stock_scores':
                date_column = 'analysis_date'
            elif table_name == 'dividend_policies':
                date_column = 'announcement_date'

            try:
                # 檢查是否有在時效範圍內的資料
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table_name}
                    WHERE stock_id = ? AND {date_column} >= ?
                """, (stock_id, threshold_date.isoformat()))

                recent_count = cursor.fetchone()[0]

                if recent_count == 0:
                    # 獲取最新資料日期
                    cursor.execute(f"""
                        SELECT MAX({date_column}) FROM {table_name}
                        WHERE stock_id = ?
                    """, (stock_id,))

                    latest_date = cursor.fetchone()[0]
                    if latest_date:
                        days_old = (current_date - datetime.fromisoformat(latest_date).date()).days
                        missing_or_outdated.append(f"{table_desc}(過舊:{days_old}天前)")
                    else:
                        missing_or_outdated.append(f"{table_desc}(無有效日期)")

            except Exception as e:
                # 如果日期欄位不存在或其他錯誤，降級為只檢查是否有資料
                logger.warning(f"無法檢查 {table_name} 的時效性: {e}")
                if record_count == 0:
                    missing_or_outdated.append(f"{table_desc}(無資料)")

        conn.close()

        # 計算完整度
        completeness = ((total_tables - len(missing_or_outdated)) / total_tables) * 100

        if missing_or_outdated:
            missing_info = f"{stock_id}({stock_name}) 需更新: {', '.join(missing_or_outdated)} (完整度: {completeness:.1f}%)"
            logger.warning(f"資料需更新 - {missing_info}")
            return False, missing_info
        else:
            logger.info(f"{stock_id}({stock_name}) 資料完整且時效性良好")
            return True, f"{stock_id}({stock_name}) 資料完整且時效性良好"

    except Exception as e:
        error_msg = f"{stock_id} 檢查失敗: {e}"
        logger.error(error_msg)
        return False, error_msg

def run_stock_by_stock_collection(test_mode=True, auto_mode=False, resume_mode=False):
    """執行逐股完整資料收集 - 每支股票收集完全部資料再換下一隻，支援簡單續傳"""
    # 設定日誌
    logger = setup_logging()

    mode_desc = "測試模式" if test_mode else ("自動執行模式" if auto_mode else "手動模式")
    if resume_mode:
        mode_desc += " (續傳模式)"

    print(f"[STOCK-BY-STOCK] 開始逐股完整資料收集流程 - {mode_desc}")
    logger.info(f"開始逐股完整資料收集流程 - {mode_desc}")
    print("=" * 60)

    # 使用簡單進度記錄系統
    progress = None

    try:
        from scripts.simple_progress import SimpleProgress
        progress = SimpleProgress()
        print("✅ 簡單進度記錄系統初始化成功")

        # 顯示當前進度摘要
        progress.show_progress_summary()

    except Exception as e:
        print(f"⚠️ 進度記錄系統初始化失敗: {e}")
        print("📝 將跳過進度記錄，但繼續執行主要功能")
        progress = None

    # 獲取股票清單
    if test_mode:
        all_stocks = get_test_stock_list()
        print(f"[TEST] 測試模式，總共 {len(all_stocks)} 檔股票")
        logger.info(f"測試模式，總共 {len(all_stocks)} 檔股票")
    else:
        all_stocks = get_all_stock_list()
        if not all_stocks:
            print("[ERROR] 無法獲取股票清單")
            logger.error("無法獲取股票清單")
            return False
        print(f"[ALL] 總共 {len(all_stocks)} 檔股票")
        logger.info(f"總共 {len(all_stocks)} 檔股票")

    if not all_stocks:
        print("[ERROR] 股票清單為空")
        logger.error("股票清單為空")
        return False

    # 準備股票清單格式（包含股票名稱）
    stock_list_with_names = []
    for stock_id in all_stocks:
        # 從資料庫獲取股票名稱
        try:
            db_path = Path('data/taiwan_stock.db')
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT stock_name FROM stocks WHERE stock_id = ?", (stock_id,))
                result = cursor.fetchone()
                stock_name = result[0] if result else stock_id
                conn.close()
            else:
                stock_name = stock_id
        except:
            stock_name = stock_id

        stock_list_with_names.append({'stock_id': stock_id, 'stock_name': stock_name})

    # 找到續傳位置
    start_index = 0
    if progress and resume_mode:
        start_index = progress.find_resume_position(stock_list_with_names)
        if start_index >= len(stock_list_with_names):
            print("[INFO] 所有股票都已完成")
            logger.info("所有股票都已完成")
            return True

    # 要處理的股票清單
    stocks_to_process = stock_list_with_names[start_index:]
    print(f"[PROCESS] 將處理 {len(stocks_to_process)} 檔股票 (從第 {start_index + 1} 檔開始)")
    logger.info(f"將處理 {len(stocks_to_process)} 檔股票 (從第 {start_index + 1} 檔開始)")

    # 顯示要處理的股票
    stock_ids = [s['stock_id'] for s in stocks_to_process]
    print(f"[STOCKS] 前10檔: {', '.join(stock_ids[:10])}{'...' if len(stock_ids) > 10 else ''}")
    logger.info(f"股票清單: {', '.join(stock_ids)}")
    print("=" * 60)

    total_stocks = len(stocks_to_process)
    success_stocks = 0
    failed_stocks = []
    skipped_stocks = []  # 資料已完整的股票

    for i, stock_info in enumerate(stocks_to_process, 1):
        stock_id = stock_info['stock_id']
        stock_name = stock_info['stock_name']
        current_index = start_index + i

        print(f"\n{'='*60}")
        print(f"[PROGRESS] 處理股票 {current_index}/{len(stock_list_with_names)}: {stock_id} {stock_name}")
        logger.info(f"開始處理股票 {current_index}/{len(stock_list_with_names)}: {stock_id} {stock_name}")
        print(f"{'='*60}")

        # 記錄當前處理的股票
        if progress:
            progress.save_current_stock(stock_id, stock_name, len(stock_list_with_names), current_index)

        is_complete, completeness_info = check_stock_data_completeness(stock_id, logger)

        if is_complete and not test_mode:  # 測試模式總是執行收集
            print(f"[SKIP] {completeness_info} - 跳過")
            skipped_stocks.append(stock_id)

            # 記錄為已完成
            if progress:
                progress.add_completed_stock(stock_id, stock_name, ["已存在完整資料"])
            continue

        # 為每支股票執行完整收集流程
        stock_success = run_single_stock_complete_collection(stock_id, test_mode, logger)

        if stock_success:
            success_stocks += 1
            print(f"[SUCCESS] 股票 {stock_id} {stock_name} 完整收集成功")
            logger.info(f"股票 {stock_id} {stock_name} 完整收集成功")

            # 記錄為已完成
            if progress:
                progress.add_completed_stock(stock_id, stock_name, ["完整收集成功"])
        else:
            failed_stocks.append(stock_id)
            print(f"[FAILED] 股票 {stock_id} {stock_name} 完整收集失敗")
            logger.error(f"股票 {stock_id} {stock_name} 完整收集失敗")

            # 記錄為失敗
            if progress:
                progress.add_failed_stock(stock_id, stock_name, "完整收集流程失敗")

        # 顯示進度
        processed = success_stocks + len(failed_stocks)
        print(f"[PROGRESS] 已處理 {processed}/{total_stocks} 檔股票，成功 {success_stocks} 檔，跳過 {len(skipped_stocks)} 檔")

        # 如果是自動模式，不詢問直接繼續
        if auto_mode:
            if i % 10 == 0:  # 每10檔顯示一次進度
                print(f"[AUTO] 自動模式進行中... {i}/{total_stocks}")
            continue

        # 手動模式：如果不是最後一檔股票，詢問是否繼續
        if i < total_stocks:
            try:
                continue_choice = input(f"\n[CONTINUE] 是否繼續處理下一檔股票？(y/n/q): ").strip().lower()
                if continue_choice == 'q':
                    print("[QUIT] 使用者選擇退出")
                    logger.info("使用者選擇退出")
                    break
                elif continue_choice == 'n':
                    print("[SKIP] 跳過剩餘股票")
                    logger.info("使用者選擇跳過剩餘股票")
                    break
                # 預設為 'y' 或其他輸入都繼續
            except KeyboardInterrupt:
                print(f"\n[INTERRUPT] 使用者中斷執行")
                logger.info("使用者中斷執行")
                break

    # 總結報告
    processed = success_stocks + len(failed_stocks)
    print(f"\n{'='*60}")
    print("[STOCK-BY-STOCK] 逐股完整收集流程結束")
    print(f"[RESULT] 總共處理 {processed} 檔股票")
    print(f"[SUCCESS] 成功收集: {success_stocks} 檔")
    print(f"[SKIPPED] 資料完整跳過: {len(skipped_stocks)} 檔")
    print(f"[FAILED] 收集失敗: {len(failed_stocks)} 檔")

    # 記錄到日誌
    logger.info(f"逐股完整收集流程結束")
    logger.info(f"總共處理 {processed} 檔股票，成功 {success_stocks} 檔，跳過 {len(skipped_stocks)} 檔，失敗 {len(failed_stocks)} 檔")

    if failed_stocks:
        print(f"[FAILED_LIST] 失敗股票: {', '.join(failed_stocks)}")
        logger.error(f"失敗股票清單: {', '.join(failed_stocks)}")

    if skipped_stocks and not test_mode:
        print(f"[SKIPPED_LIST] 跳過股票: {', '.join(skipped_stocks[:10])}{'...' if len(skipped_stocks) > 10 else ''}")
        logger.info(f"跳過股票清單: {', '.join(skipped_stocks)}")

    success_rate = (success_stocks / processed) * 100 if processed > 0 else 0
    print(f"[SUCCESS_RATE] 成功率: {success_rate:.1f}%")
    logger.info(f"成功率: {success_rate:.1f}%")
    print("=" * 60)

    return success_stocks > 0

def run_single_stock_complete_collection(stock_id, test_mode=True, logger=None):
    """執行單一股票的完整資料收集"""
    print(f"[SINGLE-STOCK] 開始股票 {stock_id} 的完整資料收集")
    if logger:
        logger.info(f"開始股票 {stock_id} 的完整資料收集")

    success_count = 0
    total_steps = 5

    # 資料集名稱對應
    dataset_names = [
        "basic_data",
        "financial_statements",
        "balance_sheets",
        "dividend_data",
        "analysis"
    ]

    # 階段1: 基礎資料收集
    print(f"\n[{stock_id}] 階段 1/5: 基礎資料收集 (股價、月營收、現金流)")
    start_date, end_date = get_default_dates()
    if run_collect_with_stock(start_date, end_date, 5, "test", stock_id):
        success_count += 1
        print(f"[{stock_id}] ✅ 基礎資料收集完成")
    else:
        print(f"[{stock_id}] ❌ 基礎資料收集失敗")

    # 階段2: 財務報表收集
    print(f"\n[{stock_id}] 階段 2/5: 財務報表資料收集")
    if run_financial_collection(test_mode, stock_id):
        success_count += 1
        print(f"[{stock_id}] ✅ 財務報表收集完成")
    else:
        print(f"[{stock_id}] ❌ 財務報表收集失敗")

    # 階段3: 資產負債表收集
    print(f"\n[{stock_id}] 階段 3/5: 資產負債表資料收集")
    if run_balance_collection(test_mode, stock_id):
        success_count += 1
        print(f"[{stock_id}] ✅ 資產負債表收集完成")
    else:
        print(f"[{stock_id}] ❌ 資產負債表收集失敗")

    # 階段4: 股利資料收集
    print(f"\n[{stock_id}] 階段 4/5: 股利資料收集")
    if run_dividend_collection(test_mode, stock_id):
        success_count += 1
        print(f"[{stock_id}] ✅ 股利資料收集完成")
    else:
        print(f"[{stock_id}] ❌ 股利資料收集失敗")

    # 階段5: 潛力股分析
    print(f"\n[{stock_id}] 階段 5/5: 潛力股分析")
    top_count = 5 if test_mode else 50
    if run_analysis(top=top_count, stock_id=stock_id):
        success_count += 1
        print(f"[{stock_id}] ✅ 潛力股分析完成")
    else:
        print(f"[{stock_id}] ❌ 潛力股分析失敗")

    # 單股總結
    print(f"\n[{stock_id}] 完整收集結果: {success_count}/{total_steps} 個階段成功")

    return success_count >= 3  # 至少3個階段成功才算成功

def run_complete_collection(test_mode=False, stock_id=None):
    """執行完整資料收集"""
    if stock_id:
        print(f"[COMPLETE] 開始完整資料收集流程 - 個股 {stock_id}")
    else:
        print("[COMPLETE] 開始完整資料收集流程")
    print("=" * 60)

    success_count = 0
    total_steps = 5

    # 階段1: 基礎資料收集
    print("\n階段 1/5: 基礎資料收集 (股價、月營收、現金流)")
    start_date, end_date = get_default_dates()
    if stock_id:
        # 個股模式：使用 test 範圍但指定股票
        scope = "test"
        if run_collect_with_stock(start_date, end_date, 5, scope, stock_id):
            success_count += 1
    else:
        # 全部股票模式
        scope = "test" if test_mode else "all"
        if run_collect(start_date, end_date, 5, scope):
            success_count += 1

    # 階段2: 財務報表收集
    print("\n階段 2/5: 財務報表資料收集")
    if run_financial_collection(test_mode, stock_id):
        success_count += 1

    # 階段3: 資產負債表收集
    print("\n階段 3/5: 資產負債表資料收集")
    if run_balance_collection(test_mode, stock_id):
        success_count += 1

    # 階段4: 股利資料收集
    print("\n階段 4/5: 股利資料收集")
    if run_dividend_collection(test_mode, stock_id):
        success_count += 1

    # 階段5: 潛力股分析
    print("\n階段 5/5: 潛力股分析")
    top_count = 5 if test_mode else 50
    if run_analysis(top=top_count, stock_id=stock_id):
        success_count += 1

    # 總結
    print("\n" + "=" * 60)
    if stock_id:
        print(f"[COMPLETE] 個股 {stock_id} 完整收集流程結束")
    else:
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
    print("  python c.py stock-by-stock-test # 逐股完整收集 (測試模式)")
    print("  python c.py stock-by-stock-auto # 逐股完整收集 (自動執行)")
    print()
    print("續傳選項:")
    print("  python c.py stock-by-stock-test --resume # 續傳逐股收集 (測試模式)")
    print("  python c.py stock-by-stock-auto --resume # 續傳逐股收集 (自動執行)")
    print()
    print("說明:")
    print("  python c.py help         # 顯示此說明")
    print("  --resume                 # 續傳模式，從上次中斷處繼續")
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

    elif len(sys.argv) >= 2:
        # 解析參數
        args = sys.argv[1:]
        option = args[0].lower()
        stock_id = None

        # 檢查是否有 --stock-id 參數
        if '--stock-id' in args:
            stock_id_index = args.index('--stock-id')
            if stock_id_index + 1 < len(args):
                stock_id = args[stock_id_index + 1]
            else:
                print("[ERROR] --stock-id 參數需要指定股票代碼")
                return

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
            if stock_id:
                print(f"[FINANCIAL] 收集財務報表資料 - 個股 {stock_id}")
            else:
                print("[FINANCIAL] 收集財務報表資料")
            run_financial_collection(test_mode=False, stock_id=stock_id)

        elif option in ['balance', 'b']:
            if stock_id:
                print(f"[BALANCE] 收集資產負債表資料 - 個股 {stock_id}")
            else:
                print("[BALANCE] 收集資產負債表資料")
            run_balance_collection(test_mode=False, stock_id=stock_id)

        elif option in ['dividend', 'd']:
            if stock_id:
                print(f"[DIVIDEND] 收集股利相關資料 - 個股 {stock_id}")
            else:
                print("[DIVIDEND] 收集股利相關資料")
            run_dividend_collection(test_mode=False, stock_id=stock_id)

        elif option in ['analysis', 'analyze']:
            if stock_id:
                print(f"[ANALYSIS] 執行潛力股分析 - 個股 {stock_id}")
            else:
                print("[ANALYSIS] 執行潛力股分析")
            run_analysis(top=50, stock_id=stock_id)

        elif option in ['complete', 'c']:
            if stock_id:
                print(f"[COMPLETE] 執行完整資料收集 - 個股 {stock_id}")
            else:
                print("[COMPLETE] 執行完整資料收集")
            run_complete_collection(test_mode=False, stock_id=stock_id)

        elif option in ['complete-test', 'ct']:
            if stock_id:
                print(f"[COMPLETE-TEST] 執行完整資料收集 (測試模式) - 個股 {stock_id}")
            else:
                print("[COMPLETE-TEST] 執行完整資料收集 (測試模式)")
            run_complete_collection(test_mode=True, stock_id=stock_id)

        elif option in ['stock-by-stock-test', 'sbs-test', 'sbs']:
            # 檢查是否有續傳參數
            resume_mode = '--resume' in args

            if resume_mode:
                print("[STOCK-BY-STOCK-TEST] 續傳逐股完整收集 (測試模式)")
            else:
                print("[STOCK-BY-STOCK-TEST] 執行逐股完整收集 (測試模式)")
            run_stock_by_stock_collection(test_mode=True, auto_mode=False, resume_mode=resume_mode)

        elif option in ['stock-by-stock-auto', 'sbs-auto', 'sbs-all']:
            # 檢查是否有續傳參數
            resume_mode = '--resume' in args

            if resume_mode:
                print("[STOCK-BY-STOCK-AUTO] 續傳逐股完整收集 (自動執行)")
            else:
                print("[STOCK-BY-STOCK-AUTO] 執行逐股完整收集 (自動執行)")
            run_stock_by_stock_collection(test_mode=False, auto_mode=True, resume_mode=resume_mode)

        elif option in ['help', 'h', '--help', '-h']:
            show_help()

        else:
            print(f"[ERROR] 未知選項: {option}")
            print("[INFO] 使用 'python c.py help' 查看說明")

if __name__ == "__main__":
    main()

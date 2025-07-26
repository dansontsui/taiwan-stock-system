#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料收集進度監控腳本
"""

import sys
import os
import time
import re
from datetime import datetime, timedelta
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager

def check_402_errors():
    """檢查最近的402錯誤"""
    log_files = [
        'logs/collect_stock_prices_smart.log',
        'logs/collect_all_10years.log',
        'logs/collect_monthly_revenue.log',
        'logs/collect_financial_statements.log',
        'logs/collect_balance_sheets.log',
        'logs/collect_dividend_data.log'
    ]

    latest_402_time = None
    latest_402_file = None

    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # 檢查最近的402錯誤 (檢查最後200行)
                for line in reversed(lines[-200:]):
                    if '402' in line or 'Payment Required' in line:
                        # 提取時間戳
                        time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if time_match:
                            error_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')
                            if latest_402_time is None or error_time > latest_402_time:
                                latest_402_time = error_time
                                latest_402_file = log_file
                        break

            except Exception:
                continue

    return latest_402_time, latest_402_file

def check_smart_waiting_status():
    """檢查智能等待狀態"""
    log_files = [
        'logs/collect_stock_prices_smart.log',
        'logs/collect_all_10years.log'
    ]

    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # 檢查最近的等待相關日誌 (檢查最後50行)
                for line in reversed(lines[-50:]):
                    if '智能等待' in line and '分鐘' in line:
                        # 提取時間戳
                        time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if time_match:
                            wait_start_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')
                            # 檢查是否在70分鐘內
                            time_diff = datetime.now() - wait_start_time
                            if time_diff.total_seconds() < 4200:  # 70分鐘 = 4200秒
                                remaining_seconds = 4200 - time_diff.total_seconds()
                                return True, remaining_seconds, wait_start_time
                        break
                    elif '等待完成' in line:
                        # 如果找到等待完成的日誌，說明不在等待中
                        return False, 0, None

            except Exception:
                continue

    return False, 0, None

def verify_smart_waiting_config():
    """驗證智能等待機制配置"""
    scripts_to_check = [
        'scripts/collect_stock_prices_smart.py',
        'scripts/collect_monthly_revenue.py',
        'scripts/collect_financial_statements.py',
        'scripts/collect_balance_sheets.py',
        'scripts/collect_dividend_data.py'
    ]

    config_status = {}

    for script in scripts_to_check:
        if os.path.exists(script):
            try:
                with open(script, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 檢查是否有wait_for_api_reset函數和70分鐘等待
                has_wait_function = 'def wait_for_api_reset' in content
                has_70min_wait = 'wait_minutes = 70' in content
                has_402_handling = '402' in content and 'wait_for_api_reset()' in content

                config_status[script] = {
                    'has_wait_function': has_wait_function,
                    'has_70min_wait': has_70min_wait,
                    'has_402_handling': has_402_handling,
                    'configured': has_wait_function and has_70min_wait and has_402_handling
                }

            except Exception:
                config_status[script] = {
                    'has_wait_function': False,
                    'has_70min_wait': False,
                    'has_402_handling': False,
                    'configured': False
                }
        else:
            config_status[script] = None

    return config_status

def get_data_statistics():
    """獲取資料統計"""
    db_manager = DatabaseManager(Config.DATABASE_PATH)
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    tables = [
        ('stocks', '股票基本資料'),
        ('stock_prices', '股價資料'),
        ('monthly_revenues', '月營收資料'),
        ('financial_statements', '綜合損益表'),
        ('balance_sheets', '資產負債表'),
        ('dividend_policies', '股利政策'),
        ('financial_ratios', '財務比率'),
        ('stock_scores', '潛力股評分'),
        ('cash_flow_statements', '現金流量表'),
        ('market_values', '市值資料'),
        ('stock_splits', '股票分割'),
        ('dividend_results', '股利發放結果'),
        ('technical_indicators', '技術指標'),
        ('etf_dividends', 'ETF配息'),
        ('data_updates', '資料更新記錄')
    ]
    
    try:
        for table, name in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[name] = count
            except:
                stats[name] = 0
        
        # 獲取最新更新時間
        try:
            cursor.execute("SELECT MAX(created_at) FROM stock_prices")
            latest_price = cursor.fetchone()[0]
            stats['最新股價時間'] = latest_price
        except:
            stats['最新股價時間'] = None
            
        try:
            cursor.execute("SELECT MAX(created_at) FROM monthly_revenues")
            latest_revenue = cursor.fetchone()[0]
            stats['最新營收時間'] = latest_revenue
        except:
            stats['最新營收時間'] = None
        
    except Exception as e:
        print(f"獲取統計資料失敗: {e}")
    finally:
        conn.close()
    
    return stats

def check_completion_status():
    """檢查收集完成狀態"""
    try:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # 檢查各類資料的完成度
        completion_checks = {
            'stocks': ('SELECT COUNT(*) FROM stocks', 2800),  # 預期股票數
            'stock_prices': ('SELECT COUNT(*) FROM stock_prices', 500000),  # 預期股價資料
            'monthly_revenues': ('SELECT COUNT(*) FROM monthly_revenues', 50000),  # 預期營收資料
            'financial_statements': ('SELECT COUNT(*) FROM financial_statements', 400000),  # 預期財務報表
            'balance_sheets': ('SELECT COUNT(*) FROM balance_sheets', 1000000),  # 預期資產負債表
            'stock_scores': ('SELECT COUNT(*) FROM stock_scores', 50)  # 預期潛力股評分
        }

        all_completed = True
        completion_status = {}

        for table, (query, expected) in completion_checks.items():
            try:
                cursor.execute(query)
                actual = cursor.fetchone()[0]
                completion_rate = (actual / expected * 100) if expected > 0 else 0
                completion_status[table] = {
                    'actual': actual,
                    'expected': expected,
                    'rate': completion_rate
                }

                # 如果完成度低於95%，認為未完成
                if completion_rate < 95:
                    all_completed = False

            except Exception:
                all_completed = False
                completion_status[table] = {'actual': 0, 'expected': expected, 'rate': 0}

        conn.close()
        return all_completed, completion_status

    except Exception:
        return False, {}

def display_progress():
    """顯示進度"""
    print("=" * 60)
    print("📊 台股十年資料收集 - 即時監控")
    print("=" * 60)
    print("⏰ 啟動時間:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🔄 更新頻率: 30秒")
    print("💡 按 Ctrl+C 停止監控")
    print("🎯 收集完成後將自動停止")
    print("=" * 60)

    consecutive_complete_checks = 0

    try:
        while True:
            # 清除螢幕 (可選)
            # os.system('clear' if os.name == 'posix' else 'cls')

            print("=" * 60)
            print("📊 台股十年資料收集 - 即時監控")
            print("=" * 60)
            print(f"⏰ 監控時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            # 檢查402錯誤狀態
            latest_402_time, latest_402_file = check_402_errors()
            is_waiting, remaining_seconds, wait_start_time = check_smart_waiting_status()

            # 顯示API狀態
            print("🌐 API狀態檢查:")
            print("-" * 40)

            if latest_402_time:
                time_since_402 = datetime.now() - latest_402_time
                hours_since = time_since_402.total_seconds() / 3600

                if hours_since < 1.2:  # 1.2小時 = 72分鐘
                    print(f"⚠️  最後402錯誤: {latest_402_time.strftime('%H:%M:%S')} ({hours_since:.1f}小時前)")
                    print(f"   來源: {latest_402_file}")
                else:
                    print(f"✅ 最後402錯誤: {latest_402_time.strftime('%H:%M:%S')} ({hours_since:.1f}小時前，已恢復)")
            else:
                print("✅ 無402錯誤記錄")

            # 顯示智能等待狀態
            if is_waiting:
                remaining_minutes = remaining_seconds / 60
                remaining_hours = remaining_minutes / 60
                if remaining_hours >= 1:
                    print(f"⏰ 智能等待中: 剩餘 {remaining_hours:.1f} 小時")
                else:
                    print(f"⏰ 智能等待中: 剩餘 {remaining_minutes:.0f} 分鐘")
                print(f"   開始時間: {wait_start_time.strftime('%H:%M:%S')}")
            else:
                print("✅ 目前無API限制，正常收集中")

            print()

            # 獲取統計資料
            stats = get_data_statistics()

            print("📈 資料收集進度:")
            print("-" * 40)

            for name, count in stats.items():
                if name not in ['最新股價時間', '最新營收時間']:
                    print(f"{name:<15}: {count:>10,} 筆")

            print()
            print("⏰ 最新更新時間:")
            print("-" * 40)

        if stats.get('最新股價時間'):
            print(f"股價資料: {stats['最新股價時間']}")

        if stats.get('最新營收時間'):
            print(f"營收資料: {stats['最新營收時間']}")

        # 檢查每日更新狀態
        print()
        print("📅 每日更新狀態:")
        print("-" * 40)
        check_daily_update_status()

        # 計算收集速度
        if stats.get('最新股價時間'):
            try:
                latest_time = datetime.fromisoformat(stats['最新股價時間'].replace(' ', 'T'))
                time_diff = datetime.now() - latest_time
                if time_diff.total_seconds() < 3600:  # 1小時內
                    print(f"📈 收集狀態: 活躍 (最後更新 {time_diff.total_seconds()/60:.0f} 分鐘前)")
                else:
                    print(f"⚠️  收集狀態: 可能暫停 (最後更新 {time_diff.total_seconds()/3600:.1f} 小時前)")
            except:
                print("📊 收集狀態: 檢查中...")

        # 估算完成度
        total_expected = {
            '股票基本資料': 2800,
            '股價資料': 500000,  # 估算十年資料量
            '月營收資料': 50000,
            '綜合損益表': 20000,
            '資產負債表': 20000,
            '股利政策': 5000,
            '財務比率': 10000,
            '潛力股評分': 100
        }

        print()
        print("📊 預估完成度:")
        print("-" * 40)

        for name, expected in total_expected.items():
            current = stats.get(name, 0)
            if expected > 0:
                progress = min((current / expected) * 100, 100)
                bar_length = 20
                filled_length = int(bar_length * progress / 100)
                bar = "█" * filled_length + "░" * (bar_length - filled_length)
                print(f"{name:<15}: [{bar}] {progress:>5.1f}%")

        # 智能等待機制配置狀態
        config_status = verify_smart_waiting_config()
        configured_count = sum(1 for status in config_status.values() if status and status['configured'])
        total_scripts = len([s for s in config_status.values() if s is not None])

        print()
        print("🔧 智能等待機制配置:")
        print("-" * 40)
        print(f"已配置腳本: {configured_count}/{total_scripts}")

        for script, status in config_status.items():
            if status is not None:
                script_name = script.split('/')[-1]
                if status['configured']:
                    print(f"✅ {script_name}")
                else:
                    missing = []
                    if not status['has_wait_function']:
                        missing.append("等待函數")
                    if not status['has_70min_wait']:
                        missing.append("70分鐘設定")
                    if not status['has_402_handling']:
                        missing.append("402處理")
                    print(f"❌ {script_name} (缺少: {', '.join(missing)})")

        print()
        print("💡 動態提示:")
        print("-" * 40)
        print("- 按 Ctrl+C 停止監控")

        if is_waiting:
            print(f"- ⏰ 正在智能等待中，剩餘 {remaining_seconds/60:.0f} 分鐘")
        else:
            print("- ✅ API正常，無需等待")

        if latest_402_time:
            time_since_402 = datetime.now() - latest_402_time
            if time_since_402.total_seconds() < 4200:  # 70分鐘內
                print("- ⚠️  最近遇到402錯誤，系統已自動處理")
            else:
                print("- ✅ 402錯誤已恢復，系統正常運行")
        else:
            print("- ✅ 無API限制問題")

        print("=" * 60)

        # 檢查完成狀態
        is_completed, completion_status = check_completion_status()

        if is_completed:
            consecutive_complete_checks += 1
            print(f"\n🎉 檢測到收集已完成 ({consecutive_complete_checks}/3)")

            # 連續3次檢查都完成才停止，避免誤判
            if consecutive_complete_checks >= 3:
                print("\n" + "=" * 60)
                print("🎊 台股十年資料收集已完成！")
                print("=" * 60)
                print("📊 完成統計:")
                for table, status in completion_status.items():
                    print(f"  {table}: {status['actual']:,} / {status['expected']:,} ({status['rate']:.1f}%)")
                print("=" * 60)
                print("🌐 您現在可以啟動 Web 介面: python run.py")
                print("🎯 或執行潛力股分析: python scripts/analyze_potential_stocks.py")
                print("=" * 60)
                break
            else:
                consecutive_complete_checks = 0

            # 等待30秒後更新
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                print("\n👋 監控已停止")
                break
    except KeyboardInterrupt:
        print("\n👋 監控已停止")
    except KeyboardInterrupt:
        print("\n👋 監控已停止")

def check_daily_update_status():
    """檢查每日更新狀態"""
    try:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        db_manager = DatabaseManager(Config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # 檢查今日是否有新的股價資料
        cursor.execute("""
            SELECT COUNT(*) FROM stock_prices
            WHERE date = ?
        """, (today.isoformat(),))
        today_prices = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM stock_prices
            WHERE date = ?
        """, (yesterday.isoformat(),))
        yesterday_prices = cursor.fetchone()[0]

        conn.close()

        # 檢查每日更新日誌
        daily_log_path = Path("logs/collect_daily_update.log")
        last_daily_update = "未執行"

        if daily_log_path.exists():
            try:
                with open(daily_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if "每日增量收集成功完成" in line:
                            # 提取時間戳
                            time_part = line.split('|')[0].strip()
                            last_daily_update = time_part
                            break
            except Exception:
                pass

        print(f"今日股價資料      : {today_prices:,} 筆")
        print(f"昨日股價資料      : {yesterday_prices:,} 筆")
        print(f"最後每日更新      : {last_daily_update}")

        # 建議
        if today_prices == 0 and yesterday_prices > 0:
            print("💡 建議執行每日更新: python scripts/collect_daily_update.py")
        elif today_prices > 0:
            print("✅ 今日資料已更新")
        else:
            print("⚠️  請檢查資料收集狀況")

    except Exception as e:
        print(f"檢查每日更新狀態失敗: {e}")

if __name__ == "__main__":
    display_progress()

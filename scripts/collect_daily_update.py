#!/usr/bin/env python3
"""
台股每日增量資料收集系統
自動檢測並收集從上次更新到今日的增量資料
"""

import os
import sys
import argparse
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from tqdm import tqdm

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.utils.simple_database import SimpleDatabaseManager
from config import Config

class DailyUpdateCollector:
    """每日增量資料收集器"""
    
    def __init__(self, batch_size=5, days_back=7):
        self.batch_size = batch_size
        self.days_back = days_back
        self.db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
        self.today = datetime.now().date()
        self.stats = {
            'stock_prices': 0,
            'monthly_revenues': 0,
            'financial_statements': 0,
            'dividend_policies': 0,
            'updated_stocks': set()
        }
        
        # 設定日誌
        log_file = project_root / "logs" / "collect_daily_update.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logger.add(
            log_file,
            rotation="10 MB",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO"
        )
    
    def get_last_update_date(self, table_name, date_column='date'):
        """獲取指定表的最後更新日期"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            if table_name == 'monthly_revenues':
                # 月營收使用特殊的日期計算
                cursor.execute("""
                    SELECT MAX(revenue_year || '-' || 
                               CASE WHEN revenue_month < 10 THEN '0' || revenue_month 
                                    ELSE revenue_month END || '-01') as last_date
                    FROM monthly_revenues
                """)
            else:
                cursor.execute(f"SELECT MAX({date_column}) FROM {table_name}")
            
            result = cursor.fetchone()
            if result and result[0]:
                if table_name == 'monthly_revenues':
                    return datetime.strptime(result[0], '%Y-%m-%d').date()
                else:
                    return datetime.strptime(result[0], '%Y-%m-%d').date()
            else:
                # 如果沒有資料，從7天前開始
                return self.today - timedelta(days=self.days_back)
                
        except Exception as e:
            logger.warning(f"獲取 {table_name} 最後更新日期失敗: {e}")
            return self.today - timedelta(days=self.days_back)
        finally:
            conn.close()
    
    def get_active_stocks(self, limit=None):
        """獲取活躍股票列表"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # 優先選擇有股價資料的股票，按資料量排序
            query = """
                SELECT s.stock_id, s.stock_name, COUNT(sp.date) as price_count
                FROM stocks s
                LEFT JOIN stock_prices sp ON s.stock_id = sp.stock_id
                WHERE s.is_active = 1
                GROUP BY s.stock_id, s.stock_name
                ORDER BY price_count DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            return cursor.fetchall()
            
        except Exception as e:
            logger.error(f"獲取股票列表失敗: {e}")
            return []
        finally:
            conn.close()
    
    def collect_stock_prices(self):
        """收集股價資料"""
        print("🔍 檢查股價資料更新需求...")
        logger.info("🔄 開始收集股價資料...")

        last_date = self.get_last_update_date('stock_prices', 'date')
        start_date = last_date + timedelta(days=1)

        if start_date > self.today:
            print("✅ 股價資料已是最新，無需更新")
            logger.info("✅ 股價資料已是最新，無需更新")
            return

        print(f"📅 需要收集期間: {start_date} 到 {self.today}")
        print("🚀 啟動股價收集腳本...")
        logger.info(f"📅 收集期間: {start_date} 到 {self.today}")

        # 執行股價收集腳本
        cmd = [
            "python", "scripts/collect_stock_prices_smart.py",
            "--start-date", start_date.isoformat(),
            "--end-date", self.today.isoformat(),
            "--batch-size", str(self.batch_size)
        ]

        try:
            print("⏳ 執行中，請稍候...")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, timeout=1800)  # 30分鐘超時

            if result.returncode == 0:
                new_records = self._count_new_records('stock_prices', start_date)
                print(f"✅ 股價資料收集完成，新增 {new_records:,} 筆資料")
                logger.info(f"✅ 股價資料收集完成，新增 {new_records:,} 筆資料")
                self.stats['stock_prices'] = new_records
            else:
                print(f"❌ 股價資料收集失敗")
                logger.error(f"❌ 股價資料收集失敗: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("⏰ 股價收集超時，可能遇到API限制")
            logger.warning("⏰ 股價收集超時")
        except Exception as e:
            print(f"❌ 執行股價收集腳本失敗: {e}")
            logger.error(f"❌ 執行股價收集腳本失敗: {e}")
    
    def collect_monthly_revenues(self):
        """收集月營收資料"""
        print("🔍 檢查月營收資料更新需求...")
        logger.info("🔄 開始收集月營收資料...")

        # 檢查是否需要收集新的月份資料
        current_month = self.today.replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)

        # 檢查上個月的資料是否完整
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT COUNT(DISTINCT stock_id)
                FROM monthly_revenues
                WHERE revenue_year = ? AND revenue_month = ?
            """, (last_month.year, last_month.month))

            last_month_count = cursor.fetchone()[0]

            print(f"📊 {last_month.year}-{last_month.month:02d} 月營收資料: {last_month_count} 檔股票")

            # 如果上個月資料少於100檔股票，則需要更新
            if last_month_count < 100:
                print(f"📅 需要更新 {last_month.year}-{last_month.month:02d} 月營收資料")
                print("🚀 啟動月營收收集腳本...")
                logger.info(f"📅 需要更新 {last_month.year}-{last_month.month:02d} 月營收資料")

                # 執行月營收收集腳本
                start_date = last_month.isoformat()
                end_date = self.today.isoformat()

                cmd = [
                    "python", "scripts/collect_monthly_revenue.py",
                    "--start-date", start_date,
                    "--end-date", end_date,
                    "--batch-size", str(self.batch_size)
                ]

                print("⏳ 執行中，請稍候...")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, timeout=1200)  # 20分鐘超時

                if result.returncode == 0:
                    new_records = self._count_new_records('monthly_revenues', last_month)
                    print(f"✅ 月營收資料收集完成，新增 {new_records:,} 筆資料")
                    logger.info(f"✅ 月營收資料收集完成，新增 {new_records:,} 筆資料")
                    self.stats['monthly_revenues'] = new_records
                else:
                    print("❌ 月營收資料收集失敗")
                    logger.error(f"❌ 月營收資料收集失敗: {result.stderr}")
            else:
                print("✅ 月營收資料已充足，無需更新")
                logger.info("✅ 月營收資料已是最新，無需更新")

        except subprocess.TimeoutExpired:
            print("⏰ 月營收收集超時")
            logger.warning("⏰ 月營收收集超時")
        except Exception as e:
            print(f"❌ 檢查月營收資料失敗: {e}")
            logger.error(f"❌ 檢查月營收資料失敗: {e}")
        finally:
            conn.close()
    
    def collect_financial_statements(self):
        """收集財務報表資料"""
        logger.info("🔄 檢查財務報表資料...")
        
        # 檢查是否有新的季報需要收集
        current_quarter = (self.today.month - 1) // 3 + 1
        current_year = self.today.year
        
        # 如果是季度的第二個月之後，檢查該季度資料
        if self.today.month % 3 >= 2:  # 2月、5月、8月、11月之後
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            try:
                # 檢查當前季度的資料完整性
                cursor.execute("""
                    SELECT COUNT(DISTINCT stock_id) 
                    FROM financial_statements 
                    WHERE date LIKE ?
                """, (f"{current_year}%",))
                
                current_year_count = cursor.fetchone()[0]
                
                if current_year_count < 500:  # 如果當年資料少於500檔
                    logger.info(f"📅 需要更新 {current_year} 年財務報表資料")
                    
                    cmd = [
                        "python", "scripts/collect_financial_statements.py",
                        "--start-date", f"{current_year}-01-01",
                        "--end-date", self.today.isoformat(),
                        "--batch-size", str(max(3, self.batch_size // 2))  # 財務報表用較小批次
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
                    
                    if result.returncode == 0:
                        logger.info("✅ 財務報表資料收集完成")
                        self.stats['financial_statements'] = self._count_new_records('financial_statements', 
                                                                                   datetime(current_year, 1, 1).date())
                    else:
                        logger.error(f"❌ 財務報表資料收集失敗: {result.stderr}")
                else:
                    logger.info("✅ 財務報表資料已是最新，無需更新")
                    
            except Exception as e:
                logger.error(f"❌ 檢查財務報表資料失敗: {e}")
            finally:
                conn.close()
        else:
            logger.info("✅ 非財報更新期間，跳過財務報表收集")
    
    def collect_dividend_policies(self):
        """收集股利政策資料"""
        logger.info("🔄 檢查股利政策資料...")

        # 股利政策通常在每年3-6月公布，檢查是否需要更新
        if 3 <= self.today.month <= 8:  # 股利公布期間
            current_year = self.today.year

            # 先檢查當年度股利資料的完整性
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    SELECT COUNT(DISTINCT stock_id)
                    FROM dividend_policies
                    WHERE year LIKE ?
                """, (f"{current_year}%",))

                current_year_dividend_count = cursor.fetchone()[0]

                # 如果當年度股利資料少於50檔股票，才執行收集
                if current_year_dividend_count < 50:
                    logger.info(f"📅 需要更新 {current_year} 年股利政策資料")

                    cmd = [
                        "python", "scripts/collect_dividend_data.py",
                        "--start-date", f"{current_year}-01-01",
                        "--end-date", self.today.isoformat(),
                        "--batch-size", str(max(3, self.batch_size // 2))
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, timeout=300)  # 5分鐘超時

                    if result.returncode == 0:
                        logger.info("✅ 股利政策資料收集完成")
                        self.stats['dividend_policies'] = self._count_new_records('dividend_policies',
                                                                                datetime(current_year, 1, 1).date())
                    else:
                        logger.error(f"❌ 股利政策資料收集失敗: {result.stderr}")
                else:
                    logger.info(f"✅ {current_year} 年股利政策資料已充足 ({current_year_dividend_count} 檔)，跳過收集")

            except subprocess.TimeoutExpired:
                logger.warning("⏰ 股利政策收集超時，跳過此步驟")
            except Exception as e:
                logger.error(f"❌ 執行股利政策收集失敗: {e}")
            finally:
                conn.close()
        else:
            logger.info("✅ 非股利公布期間，跳過股利政策收集")
    
    def _count_new_records(self, table_name, since_date):
        """統計新增的記錄數量"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            if table_name == 'monthly_revenues':
                cursor.execute("""
                    SELECT COUNT(*) FROM monthly_revenues 
                    WHERE created_at >= ?
                """, (since_date.isoformat(),))
            else:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE created_at >= ?
                """, (since_date.isoformat(),))
            
            return cursor.fetchone()[0]
            
        except Exception as e:
            logger.warning(f"統計 {table_name} 新增記錄失敗: {e}")
            return 0
        finally:
            conn.close()
    
    def update_potential_analysis(self):
        """更新潛力股分析"""
        print("🔍 檢查潛力股分析更新需求...")
        logger.info("🔄 更新潛力股分析...")

        try:
            print("🚀 啟動潛力股分析...")
            cmd = [
                "python", "scripts/analyze_potential_stocks.py",
                "--top", "100"
            ]

            print("⏳ 分析中，請稍候...")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, timeout=600)  # 10分鐘超時

            if result.returncode == 0:
                print("✅ 潛力股分析更新完成")
                logger.info("✅ 潛力股分析更新完成")
            else:
                print("❌ 潛力股分析更新失敗")
                logger.error(f"❌ 潛力股分析更新失敗: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("⏰ 潛力股分析超時")
            logger.warning("⏰ 潛力股分析超時")
        except Exception as e:
            print(f"❌ 執行潛力股分析失敗: {e}")
            logger.error(f"❌ 執行潛力股分析失敗: {e}")
    
    def run(self):
        """執行每日增量收集"""
        start_time = datetime.now()

        # 控制台輸出
        print("=" * 60)
        print("🚀 台股每日增量資料收集開始")
        print(f"⏰ 開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 目標日期: {self.today}")
        print(f"🔄 批次大小: {self.batch_size}")
        print(f"📊 回溯天數: {self.days_back}")
        print("=" * 60)

        # 日誌記錄
        logger.info("=" * 60)
        logger.info("🚀 台股每日增量資料收集開始")
        logger.info(f"⏰ 開始時間: {start_time}")
        logger.info(f"📅 目標日期: {self.today}")
        logger.info(f"🔄 批次大小: {self.batch_size}")
        logger.info(f"📊 回溯天數: {self.days_back}")
        logger.info("=" * 60)

        # 定義收集任務
        tasks = [
            ("📈 股價資料收集", self.collect_stock_prices),
            ("💰 月營收資料收集", self.collect_monthly_revenues),
            ("📊 財務報表檢查", self.collect_financial_statements),
            ("🎯 股利政策檢查", self.collect_dividend_policies),
            ("🧠 潛力股分析更新", self.update_potential_analysis)
        ]

        try:
            # 使用進度條執行任務
            with tqdm(total=len(tasks), desc="📋 總體進度", unit="任務",
                     bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:

                for i, (task_name, task_func) in enumerate(tasks, 1):
                    print(f"\n📌 任務 {i}/{len(tasks)}: {task_name}")
                    print("-" * 40)

                    pbar.set_description(f"📋 執行中: {task_name}")

                    try:
                        task_func()
                        print(f"✅ {task_name} 完成")
                    except Exception as e:
                        print(f"❌ {task_name} 失敗: {e}")
                        logger.error(f"❌ {task_name} 失敗: {e}")

                    pbar.update(1)

                    # 任務間短暫休息
                    if i < len(tasks):
                        time.sleep(1)

            # 顯示統計摘要
            self.show_summary(start_time)

        except Exception as e:
            print(f"❌ 每日增量收集執行失敗: {e}")
            logger.error(f"❌ 每日增量收集執行失敗: {e}")
            raise
    
    def show_summary(self, start_time):
        """顯示執行摘要"""
        end_time = datetime.now()
        duration = end_time - start_time

        # 控制台輸出
        print("\n" + "=" * 60)
        print("📊 每日增量收集完成摘要")
        print("=" * 60)
        print(f"⏰ 結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  執行時間: {duration}")
        print()
        print("📈 資料更新統計:")
        print(f"  股價資料         : +{self.stats['stock_prices']:,} 筆")
        print(f"  月營收資料       : +{self.stats['monthly_revenues']:,} 筆")
        print(f"  財務報表資料     : +{self.stats['financial_statements']:,} 筆")
        print(f"  股利政策資料     : +{self.stats['dividend_policies']:,} 筆")
        print()
        print("🎉 每日增量收集成功完成！")
        print("🌐 您可以在 Web 介面查看最新資料")
        print("=" * 60)

        # 日誌記錄
        logger.info("=" * 60)
        logger.info("📊 每日增量收集完成摘要")
        logger.info("=" * 60)
        logger.info(f"⏰ 結束時間: {end_time}")
        logger.info(f"⏱️  執行時間: {duration}")
        logger.info("")
        logger.info("📈 資料更新統計:")
        logger.info(f"  股價資料         : +{self.stats['stock_prices']:,} 筆")
        logger.info(f"  月營收資料       : +{self.stats['monthly_revenues']:,} 筆")
        logger.info(f"  財務報表資料     : +{self.stats['financial_statements']:,} 筆")
        logger.info(f"  股利政策資料     : +{self.stats['dividend_policies']:,} 筆")
        logger.info("")
        logger.info("🎉 每日增量收集成功完成！")
        logger.info("🌐 您可以在 Web 介面查看最新資料")
        logger.info("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="台股每日增量資料收集系統")
    parser.add_argument("--batch-size", type=int, default=5, help="批次大小 (預設: 5)")
    parser.add_argument("--days-back", type=int, default=7, help="往前收集天數 (預設: 7)")
    
    args = parser.parse_args()
    
    try:
        collector = DailyUpdateCollector(
            batch_size=args.batch_size,
            days_back=args.days_back
        )
        collector.run()
        
    except KeyboardInterrupt:
        logger.info("👋 用戶中斷執行")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 系統執行失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

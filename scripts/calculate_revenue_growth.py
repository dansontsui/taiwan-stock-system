#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
計算月營收成長率腳本
"""

import sys
import os
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
from loguru import logger

def init_logging():
    """初始化日誌"""
    log_dir = os.path.join(Config.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.add(
        os.path.join(log_dir, 'calculate_revenue_growth.log'),
        rotation="10 MB",
        retention="30 days",
        level="INFO"
    )

def calculate_growth_rates_for_stock(db_manager, stock_id):
    """計算單一股票的月營收成長率"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 獲取該股票的月營收資料，按年月排序
        cursor.execute("""
            SELECT revenue_year, revenue_month, revenue
            FROM monthly_revenues 
            WHERE stock_id = ?
            ORDER BY revenue_year, revenue_month
        """, (stock_id,))
        
        data = cursor.fetchall()
        
        if len(data) < 2:
            return 0
        
        updated_count = 0
        
        # 計算月增率和年增率
        for i in range(len(data)):
            year, month, revenue = data[i]
            
            # 計算月增率 (MoM)
            mom_growth = None
            if i > 0:
                prev_revenue = data[i-1][2]
                if prev_revenue and prev_revenue > 0:
                    mom_growth = ((revenue - prev_revenue) / prev_revenue) * 100
            
            # 計算年增率 (YoY)
            yoy_growth = None
            # 找去年同月的資料
            for j in range(i):
                prev_year, prev_month, prev_revenue = data[j]
                if prev_year == year - 1 and prev_month == month:
                    if prev_revenue and prev_revenue > 0:
                        yoy_growth = ((revenue - prev_revenue) / prev_revenue) * 100
                    break
            
            # 更新成長率資料
            if mom_growth is not None or yoy_growth is not None:
                cursor.execute("""
                    UPDATE monthly_revenues 
                    SET revenue_growth_mom = ?, revenue_growth_yoy = ?
                    WHERE stock_id = ? AND revenue_year = ? AND revenue_month = ?
                """, (mom_growth, yoy_growth, stock_id, year, month))
                updated_count += 1
        
        conn.commit()
        logger.info(f"股票 {stock_id} 成長率計算完成，更新 {updated_count} 筆記錄")
        return updated_count
        
    except Exception as e:
        logger.error(f"計算成長率失敗 {stock_id}: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def main():
    """主函數"""
    print("=" * 60)
    print("台股月營收成長率計算系統")
    print("=" * 60)
    
    # 初始化日誌
    init_logging()
    logger.info("開始計算月營收成長率")
    
    try:
        # 建立資料庫管理器
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        
        # 獲取有月營收資料的股票清單
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT stock_id 
            FROM monthly_revenues 
            ORDER BY stock_id
        """)
        stock_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not stock_ids:
            print(" 未找到月營收資料")
            return
        
        print(f" 找到 {len(stock_ids)} 檔股票有月營收資料")
        print("開始計算成長率...")
        
        total_updated = 0
        
        for i, stock_id in enumerate(stock_ids, 1):
            print(f"[{i:3d}/{len(stock_ids)}] 計算 {stock_id} 成長率...")
            
            updated_count = calculate_growth_rates_for_stock(db_manager, stock_id)
            total_updated += updated_count
            
            if updated_count > 0:
                print(f" {stock_id} 完成，更新 {updated_count} 筆記錄")
            else:
                print(f"  {stock_id} 無需更新")
        
        print("\n" + "=" * 60)
        print(" 月營收成長率計算完成")
        print("=" * 60)
        print(f" 處理股票: {len(stock_ids)} 檔")
        print(f" 總更新筆數: {total_updated}")
        
        # 顯示一些統計資訊
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 最高年增率
        cursor.execute("""
            SELECT stock_id, revenue_year, revenue_month, revenue_growth_yoy
            FROM monthly_revenues 
            WHERE revenue_growth_yoy IS NOT NULL
            ORDER BY revenue_growth_yoy DESC
            LIMIT 5
        """)
        
        print("\n 年增率最高的5筆記錄:")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]}/{row[2]:02d}): {row[3]:+.1f}%")
        
        # 最低年增率
        cursor.execute("""
            SELECT stock_id, revenue_year, revenue_month, revenue_growth_yoy
            FROM monthly_revenues 
            WHERE revenue_growth_yoy IS NOT NULL
            ORDER BY revenue_growth_yoy ASC
            LIMIT 5
        """)
        
        print("\n年增率最低的5筆記錄:")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]}/{row[2]:02d}): {row[3]:+.1f}%")
        
        conn.close()
        
        logger.info(f"月營收成長率計算完成，總更新 {total_updated} 筆記錄")
        
    except Exception as e:
        error_msg = f"月營收成長率計算失敗: {e}"
        print(f" {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()

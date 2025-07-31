#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帶進度顯示的目標變數生成器
"""

import sys
import argparse
from pathlib import Path
import logging

# 添加專案路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from src.features.target_generator import TargetGenerator
from src.utils.database import DatabaseManager

# 設置簡單的日誌配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='生成目標變數 (帶進度顯示)')
    parser.add_argument('--start-date', required=True, help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--frequency', default='quarterly', choices=['monthly', 'quarterly'], help='頻率')
    
    args = parser.parse_args()
    
    try:
        print("=" * 60)
        print("           目標變數生成器 (帶進度顯示)")
        print("=" * 60)
        print(f"開始日期: {args.start_date}")
        print(f"結束日期: {args.end_date}")
        print(f"頻率: {args.frequency}")
        print("=" * 60)
        
        # 初始化
        print("初始化資料庫連接...")
        db_manager = DatabaseManager()
        
        print("初始化目標變數生成器...")
        target_generator = TargetGenerator(db_manager)
        
        # 獲取所有活躍股票
        print("獲取股票清單...")
        stocks_query = """
        SELECT stock_id FROM stocks
        WHERE is_active = 1
        AND stock_id NOT LIKE '00%'  -- 排除ETF
        AND stock_id GLOB '[0-9][0-9][0-9][0-9]'  -- 只要4位數字的股票代碼
        AND LENGTH(stock_id) = 4  -- 確保長度為4
        ORDER BY stock_id
        """

        import pandas as pd
        with db_manager.get_connection() as conn:
            stocks_df = pd.read_sql_query(stocks_query, conn)
        stock_ids = stocks_df['stock_id'].tolist()
        
        print(f"找到 {len(stock_ids)} 檔活躍股票")
        
        # 生成目標變數
        print("\n開始生成目標變數...")
        print("-" * 60)
        
        result = target_generator.create_time_series_targets(
            stock_ids=stock_ids,
            start_date=args.start_date,
            end_date=args.end_date,
            frequency=args.frequency
        )
        
        print("-" * 60)
        print(f"目標變數生成完成！")
        print(f"總共生成: {len(result)} 筆目標變數")
        
        if len(result) > 0:
            positive_count = result['target'].sum()
            positive_ratio = positive_count / len(result)
            print(f"正樣本數量: {positive_count}")
            print(f"正樣本比例: {positive_ratio:.2%}")
            
            # 保存結果
            output_file = f"data/targets/targets_{args.frequency}_{args.end_date}.csv"
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_file, index=False)
            print(f"結果已保存到: {output_file}")
        else:
            print("沒有生成任何目標變數")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"生成目標變數時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

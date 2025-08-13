# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from .utils import log
from .etl import build_all_marts
from .export import export_quality_list


def main():
    parser = argparse.ArgumentParser(prog='quality_stock_system', description='績優股篩選系統 CLI')
    sub = parser.add_subparsers(dest='cmd')

    # 批量匯出年度清單
    p_bulk = sub.add_parser('bulk-export', help='批量匯出年度清單並寫入歷史')
    p_bulk.add_argument('--profile', default='conservative', help='規則檔（預設 conservative）')
    p_bulk.add_argument('--start-year', type=int, required=True, help='起始年度，例如 2018')
    p_bulk.add_argument('--end-year', type=int, required=True, help='結束年度，包含端點，例如 2024')
    p_bulk.add_argument('--top', type=int, default=100, help='Top N（預設 100）')
    p_bulk.add_argument('--db', dest='db_path', default=None, help='資料庫路徑')

    p_build = sub.add_parser('build-marts', help='建立品質與股利 marts')
    p_build.add_argument('--db', dest='db_path', default=None, help='資料庫路徑 (預設環境變數 TS_DB_PATH)')

    p_export = sub.add_parser('export', help='輸出清單 CSV/JSON')
    p_export.add_argument('--profile', default='conservative', help='規則檔（預設 conservative）')
    p_export.add_argument('--top', type=int, default=100, help='輸出前 N 名（預設 100）')
    p_export.add_argument('--db', dest='db_path', default=None, help='資料庫路徑')
    p_export.add_argument('--year', type=int, default=None, help='鎖定評估年度（例如 2024）')
    p_export.add_argument('--as-of-date', dest='as_of_date', default=None, help='as_of_date 標記（YYYY-MM-DD）')

    args = parser.parse_args()

    if args.cmd == 'build-marts':
        log('🔧 開始建立 marts ...')
        build_all_marts(args.db_path)
        log('🎉 完成')
    elif args.cmd == 'export':
        log('📤 開始輸出清單 ...')
        res = export_quality_list(profile=args.profile, top_n=args.top, db_path=args.db_path, year=args.year, as_of_date=args.as_of_date)
        if res:
            log(f"📄 CSV: {res['csv']}")
            log(f"🗂  JSON: {res['json']}")
            log(f"📊 筆數: {res['count']}")
        log('🎉 完成')
    elif args.cmd == 'bulk-export':
        log('📦 開始批量匯出年度清單 ...')
        # 清除歷史檔案，重新開始記錄
        from .history import clear_history
        clear_history()
        prof = args.profile
        start_y, end_y = int(args.start_year), int(args.end_year)
        if start_y > end_y:
            start_y, end_y = end_y, start_y
        for y in range(start_y, end_y + 1):
            as_of = f"{y}-12-31"
            log(f"➡️  匯出年度 {y}（as_of_date={as_of}）...")
            export_quality_list(profile=prof, top_n=args.top, db_path=args.db_path, year=y, as_of_date=as_of)
        log('🎉 批量匯出完成（歷史檔案已重建）')
    else:
        parser.print_help()

if __name__ == '__main__':
    main()


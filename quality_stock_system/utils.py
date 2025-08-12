# -*- coding: utf-8 -*-
"""
Utility functions for DB connection, safe I/O, and encoding handling.
- ASCII-only filenames
- UTF-8-SIG CSV export for Windows compatibility
- Chinese CLI/log messages allowed, but file system only ASCII
"""
import os
import sys
import csv
import json
import sqlite3
import datetime
from contextlib import contextmanager

# Ensure stdout encoding (avoid cp950 crash)
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')  # type: ignore[attr-defined]
except Exception:
    pass

DEFAULT_DB = os.environ.get('TS_DB_PATH', os.path.join('data', 'taiwan_stock.db'))
OUTPUT_DIR = os.environ.get('QS_OUTPUT_DIR', os.path.join('quality_stock_system', 'data'))
LOG_DIR = os.path.join(OUTPUT_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'qs.log')

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

@contextmanager
def get_conn(db_path: str = DEFAULT_DB):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

def safe_write_csv(path: str, rows, header):
    # use UTF-8-SIG to avoid Windows cp950 issue
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        writer.writerows(rows)

def safe_write_json(path: str, obj):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def ascii_path(*parts: str) -> str:
    path = os.path.join(*parts)
    # Validate ASCII
    try:
        path.encode('ascii')
    except UnicodeEncodeError:
        raise ValueError('Path must be ASCII only')
    return path

def log(msg: str):
    # Chinese logs allowed, printed safely
    try:
        print(msg)
    except Exception:
        pass
    # 同步寫入檔案
    try:
        from datetime import datetime
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a', encoding='utf-8-sig') as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


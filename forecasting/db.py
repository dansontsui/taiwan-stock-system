from __future__ import annotations
import os
import sqlite3
from typing import Optional
from contextlib import contextmanager


def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_db_path() -> str:
    # 直接讀取環境變數，避免 reload 造成的模組物件參照問題
    return os.getenv("TS_DB_PATH", os.path.join("data", "taiwan_stock.db"))


@contextmanager
def get_conn(dict_rows: bool = True):
    conn = sqlite3.connect(get_db_path())
    if dict_rows:
        conn.row_factory = _dict_factory
    try:
        yield conn
    finally:
        conn.close()


def fetch_schema_overview() -> dict:
    """回傳資料庫重要表格與欄位資訊（依據 c.py 資料庫分析報告）。"""
    return {
        "stocks": ["stock_id", "stock_name", "market", "industry", "listing_date"],
        "stock_prices": [
            "id",
            "stock_id",
            "date",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "volume",
        ],
        "monthly_revenues": [
            "id",
            "stock_id",
            "date",
            "country",
            "revenue",
            "revenue_month",
            "revenue_year",
        ],
        "cash_flow_statements": ["id", "stock_id", "date", "type", "value", "origin_name"],
        # 其他表格在報告中列出，但此系統以上述為核心
    }


def load_monthly_revenue(stock_id: str) -> "tuple[list[dict], list[str]]":
    """
    載入指定股票代碼的月營收資料（至少十年）。
    回傳 (rows, warnings)
    rows 欄位：date(實際營收月份YYYY-MM-DD), revenue(float), actual_month(實際營收月份)
    """
    warnings: list[str] = []
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT date, revenue, revenue_month, revenue_year
            FROM monthly_revenues
            WHERE stock_id = ?
            ORDER BY revenue_year ASC, revenue_month ASC
            """,
            (stock_id,),
        )
        rows = cur.fetchall()
    # 轉換、過濾，使用實際營收月份作為日期
    cleaned: list[dict] = []
    for r in rows:
        v = r["revenue"] if isinstance(r, dict) else r[1]
        rm = r["revenue_month"] if isinstance(r, dict) else r[2]
        ry = r["revenue_year"] if isinstance(r, dict) else r[3]
        if v is None or rm is None or ry is None:
            continue
        # 建立實際營收月份的日期
        actual_date = f"{ry}-{rm:02d}-01"
        cleaned.append({
            "date": actual_date,
            "revenue": float(v),
            "actual_month": f"{ry}-{rm:02d}"
        })
    # 檢查資料量
    if cleaned:
        first_year = int(cleaned[0]["date"][0:4])
        last_year = int(cleaned[-1]["date"][0:4])
        years = last_year - first_year + 1
        if years < 10:
            warnings.append(f"資料年限不足: 僅 {years} 年，需 >= 10 年")
    else:
        warnings.append("查無資料")
    return cleaned, warnings


def latest_month_in_db(stock_id: str) -> Optional[str]:
    """回傳該股在 monthly_revenues 的最新實際營收月份（YYYY-MM）"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT revenue_year, revenue_month
            FROM monthly_revenues
            WHERE stock_id = ?
            ORDER BY revenue_year DESC, revenue_month DESC
            LIMIT 1
            """,
            (stock_id,),
        )
        row = cur.fetchone()
        if row:
            year = row["revenue_year"] if isinstance(row, dict) else row[0]
            month = row["revenue_month"] if isinstance(row, dict) else row[1]
            return f"{year}-{month:02d}"
        return None


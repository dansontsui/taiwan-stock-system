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


def create_prediction_results_table():
    """創建預測結果統一資料表"""
    with get_conn(dict_rows=False) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                stock_name TEXT,
                model_name TEXT NOT NULL,
                prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                target_month TEXT NOT NULL,
                predicted_revenue REAL NOT NULL,
                latest_revenue REAL,
                latest_revenue_month TEXT,
                trend_accuracy REAL,
                mape REAL,
                scenario TEXT DEFAULT 'baseline',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_id, model_name, target_month, scenario, prediction_date)
            )
        """)

        # 創建索引以提高查詢效能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prediction_stock_model
            ON prediction_results(stock_id, model_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prediction_date
            ON prediction_results(prediction_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_target_month
            ON prediction_results(target_month)
        """)

        conn.commit()


def save_prediction_result(stock_id: str, stock_name: str, model_name: str,
                          target_month: str, predicted_revenue: float,
                          latest_revenue: float = None, latest_revenue_month: str = None,
                          trend_accuracy: float = None, mape: float = None,
                          scenario: str = 'baseline'):
    """保存預測結果到資料表"""
    create_prediction_results_table()  # 確保表格存在

    with get_conn(dict_rows=False) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO prediction_results
            (stock_id, stock_name, model_name, target_month, predicted_revenue,
             latest_revenue, latest_revenue_month, trend_accuracy, mape, scenario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (stock_id, stock_name, model_name, target_month, predicted_revenue,
              latest_revenue, latest_revenue_month, trend_accuracy, mape, scenario))
        conn.commit()


def get_prediction_results(stock_id: str = None, model_name: str = None,
                          limit: int = 100) -> list:
    """查詢預測結果"""
    create_prediction_results_table()  # 確保表格存在

    with get_conn() as conn:
        cursor = conn.cursor()

        query = """
            SELECT stock_id, stock_name, model_name, prediction_date,
                   target_month, predicted_revenue, latest_revenue,
                   latest_revenue_month, trend_accuracy, mape, scenario
            FROM prediction_results
            WHERE 1=1
        """
        params = []

        if stock_id:
            query += " AND stock_id = ?"
            params.append(stock_id)

        if model_name:
            query += " AND model_name = ?"
            params.append(model_name)

        query += " ORDER BY prediction_date DESC, stock_id, model_name"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        return cursor.fetchall()


def get_latest_prediction_summary() -> list:
    """獲取最新的預測結果摘要（每支股票每個模型的最新預測）"""
    create_prediction_results_table()  # 確保表格存在

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                pr.stock_id,
                pr.stock_name,
                pr.model_name,
                pr.prediction_date,
                pr.target_month,
                pr.predicted_revenue,
                pr.latest_revenue,
                pr.latest_revenue_month,
                pr.trend_accuracy,
                pr.mape,
                pr.scenario
            FROM prediction_results pr
            INNER JOIN (
                SELECT stock_id, model_name, scenario, MAX(prediction_date) as max_date
                FROM prediction_results
                WHERE scenario = 'baseline'
                GROUP BY stock_id, model_name
            ) latest ON pr.stock_id = latest.stock_id
                    AND pr.model_name = latest.model_name
                    AND pr.prediction_date = latest.max_date
                    AND pr.scenario = 'baseline'
            ORDER BY pr.stock_id, pr.model_name
        """)
        return cursor.fetchall()


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


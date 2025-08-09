"""
多變量特徵整合模組
整合 financial_statements、financial_ratios、balance_sheets、cash_flow_statements 等財務資料
"""
from __future__ import annotations
import pandas as pd
from typing import Dict, List, Optional
from .db import get_conn


def load_financial_statements(stock_id: str, years: int = 5) -> pd.DataFrame:
    """載入綜合損益表資料"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT date, type, value
                FROM financial_statements
                WHERE stock_id = ?
                AND date >= date('now', '-{} years')
                ORDER BY date ASC
            """.format(years), (stock_id,))
            rows = cur.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        # 轉換為寬表格式
        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # 透視表轉換
        pivot_df = df.pivot_table(
            index='date', 
            columns='type', 
            values='value', 
            aggfunc='first'
        ).reset_index()
        
        # 重新命名欄位，加上前綴
        rename_cols = {col: f"fs_{col}" for col in pivot_df.columns if col != 'date'}
        pivot_df = pivot_df.rename(columns=rename_cols)
        
        return pivot_df
        
    except Exception as e:
        print(f"⚠️  載入綜合損益表失敗: {e}")
        return pd.DataFrame()


def load_financial_ratios(stock_id: str, years: int = 5) -> pd.DataFrame:
    """載入財務比率資料"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT date, type, value
                FROM financial_ratios
                WHERE stock_id = ?
                AND date >= date('now', '-{} years')
                ORDER BY date ASC
            """.format(years), (stock_id,))
            rows = cur.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        # 轉換為寬表格式
        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # 透視表轉換
        pivot_df = df.pivot_table(
            index='date', 
            columns='type', 
            values='value', 
            aggfunc='first'
        ).reset_index()
        
        # 重新命名欄位，加上前綴
        rename_cols = {col: f"fr_{col}" for col in pivot_df.columns if col != 'date'}
        pivot_df = pivot_df.rename(columns=rename_cols)
        
        return pivot_df
        
    except Exception as e:
        print(f"⚠️  載入財務比率失敗: {e}")
        return pd.DataFrame()


def load_balance_sheets(stock_id: str, years: int = 5) -> pd.DataFrame:
    """載入資產負債表資料"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT date, type, value
                FROM balance_sheets
                WHERE stock_id = ?
                AND date >= date('now', '-{} years')
                ORDER BY date ASC
            """.format(years), (stock_id,))
            rows = cur.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        # 轉換為寬表格式
        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # 透視表轉換
        pivot_df = df.pivot_table(
            index='date', 
            columns='type', 
            values='value', 
            aggfunc='first'
        ).reset_index()
        
        # 重新命名欄位，加上前綴
        rename_cols = {col: f"bs_{col}" for col in pivot_df.columns if col != 'date'}
        pivot_df = pivot_df.rename(columns=rename_cols)
        
        return pivot_df
        
    except Exception as e:
        print(f"⚠️  載入資產負債表失敗: {e}")
        return pd.DataFrame()


def load_cash_flows(stock_id: str, years: int = 5) -> pd.DataFrame:
    """載入現金流量表資料"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT date, type, value
                FROM cash_flow_statements
                WHERE stock_id = ?
                AND date >= date('now', '-{} years')
                ORDER BY date ASC
            """.format(years), (stock_id,))
            rows = cur.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        # 轉換為寬表格式
        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # 透視表轉換
        pivot_df = df.pivot_table(
            index='date', 
            columns='type', 
            values='value', 
            aggfunc='first'
        ).reset_index()
        
        # 重新命名欄位，加上前綴
        rename_cols = {col: f"cf_{col}" for col in pivot_df.columns if col != 'date'}
        pivot_df = pivot_df.rename(columns=rename_cols)
        
        return pivot_df
        
    except Exception as e:
        print(f"⚠️  載入現金流量表失敗: {e}")
        return pd.DataFrame()


def integrate_multivariate_features(base_df: pd.DataFrame, stock_id: str) -> pd.DataFrame:
    """
    整合多變量特徵
    Args:
        base_df: 基礎營收特徵資料框
        stock_id: 股票代碼
    Returns:
        整合後的特徵資料框
    """
    result_df = base_df.copy()
    
    # 載入各類財務資料
    fs_df = load_financial_statements(stock_id)
    fr_df = load_financial_ratios(stock_id)
    bs_df = load_balance_sheets(stock_id)
    cf_df = load_cash_flows(stock_id)
    
    # 逐一合併（以日期為鍵）
    for name, df in [
        ("綜合損益表", fs_df),
        ("財務比率", fr_df), 
        ("資產負債表", bs_df),
        ("現金流量表", cf_df)
    ]:
        if not df.empty:
            # 轉換為月度頻率
            df['date'] = pd.to_datetime(df['date']).dt.to_period('M').dt.to_timestamp()
            
            # 左連接
            result_df = result_df.merge(df, on='date', how='left')
            print(f"✅ 已整合 {name}: {len(df)} 筆資料")
        else:
            print(f"⚠️  {name} 無資料")
    
    # 處理缺失值
    import numpy as np
    numeric_cols = result_df.select_dtypes(include=[np.number]).columns
    result_df[numeric_cols] = result_df[numeric_cols].ffill().fillna(0)
    
    print(f"📊 整合後特徵數量: {len(result_df.columns)} 個")
    return result_df


def analyze_feature_importance(df: pd.DataFrame, target_col: str = 'y') -> Dict:
    """
    分析特徵重要性
    Args:
        df: 特徵資料框
        target_col: 目標變數欄位名
    Returns:
        特徵重要性分析結果
    """
    from .config import cfg
    from .predictor import _safe_import
    import numpy as np

    if not cfg.enable_xgboost:
        return {"error": "需要 XGBoost 來計算特徵重要性"}

    xgb = _safe_import("xgboost")
    if xgb is None:
        return {"error": "XGBoost 未安裝"}

    from xgboost import XGBRegressor
    
    # 準備特徵
    feature_cols = [c for c in df.columns if c not in {"date", "revenue", target_col, "actual_month"}]
    numeric_features = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_features) == 0:
        return {"error": "沒有可用的數值特徵"}
    
    X = df[numeric_features].values
    y = df[target_col].values
    
    # 訓練 XGBoost
    model = XGBRegressor(
        n_estimators=100,
        max_depth=4,
        random_state=cfg.random_seed
    )
    model.fit(X, y)
    
    # 取得特徵重要性
    importance = model.feature_importances_
    
    # 排序
    feature_importance = list(zip(numeric_features, importance))
    feature_importance.sort(key=lambda x: x[1], reverse=True)
    
    return {
        "feature_importance": [
            {"特徵": name, "重要性": f"{score:.4f}"}
            for name, score in feature_importance[:20]  # 前20個
        ],
        "total_features": len(numeric_features)
    }

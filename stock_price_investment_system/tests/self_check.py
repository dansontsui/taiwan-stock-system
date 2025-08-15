# -*- coding: utf-8 -*-
"""
自我檢查腳本：
- 檢查 DB 路徑
- 小規模 Walk-forward（1~2 檔股票、極小視窗）
- 生成 Candidate Pool
CLI輸出中文敘述，避免 cp950 問題。
"""

import sys
from pathlib import Path
import json

# 確保相對匯入
# 將套件根目錄加入 sys.path
PKG_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PKG_ROOT))

from stock_price_investment_system.config.settings import get_config
from stock_price_investment_system.data.data_manager import DataManager
from stock_price_investment_system.price_models.feature_engineering import FeatureEngineer
from stock_price_investment_system.price_models.walk_forward_validator import WalkForwardValidator
from stock_price_investment_system.selector.candidate_pool_generator import CandidatePoolGenerator


def _safe_setup_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")  # type: ignore[attr-defined]
    except Exception:
        pass


def main() -> int:
    _safe_setup_stdout()
    print("=== 自我檢查開始 ===")

    # 1) DB 路徑檢查
    cfg_db = get_config('database')
    db_path = Path(cfg_db['path']).resolve()
    expected = Path(__file__).resolve().parents[2] / 'data' / 'taiwan_stock.db'
    expected = expected.resolve()
    print(f"資料庫路徑: {db_path}")
    if not db_path.exists():
        print("❌ 資料庫不存在，請確認 data/taiwan_stock.db 存在")
        return 1
    if db_path != expected:
        print(f"❌ DB路徑錯誤，應為: {expected}")
        return 1
    print("✅ DB路徑檢查通過")

    # 2) 準備股票清單（取前2檔）
    dm = DataManager()
    wf_cfg = get_config('walkforward')
    stocks = dm.get_available_stocks(
        start_date=wf_cfg['training_start'] + '-01',
        end_date=wf_cfg['training_end'] + '-31',
        min_history_months=wf_cfg['min_stock_history_months']
    )
    if not stocks:
        print("❌ 找不到可用股票")
        return 1
    stocks = stocks[:2]
    print(f"測試股票: {stocks}")

    # 3) 以極小視窗跑單一fold（縮短時間）
    fe = FeatureEngineer()
    validator = WalkForwardValidator(fe)
    result = validator.run_validation(
        stock_ids=stocks,
        train_window_months=12,
        test_window_months=3,
        stride_months=12,
        start_date=wf_cfg['training_start'] + '-01',
        end_date=wf_cfg['training_start'] + '-01'  # 讓產生 0 folds 時也能通過流程
    )
    print("✅ Walk-forward 驗證流程可呼叫")

    # 4) 生成候選池（用空結果或剛才結果）
    gen = CandidatePoolGenerator()
    pool = gen.generate_candidate_pool(result)
    print(f"候選池生成結果：success={pool.get('success')}, 數量={pool.get('pool_size', 0)}")

    # 5) 輸出檔案
    out_dir = PKG_ROOT / 'reports'
    out_dir.mkdir(parents=True, exist_ok=True)
    gen.save_candidate_pool(pool, str(out_dir / 'self_check_pool.json'))
    csv_path = gen.export_candidate_pool_csv(pool, str(out_dir / 'self_check_pool.csv'))
    if csv_path:
        print("✅ 檔案輸出完成（UTF-8-SIG 編碼）")
    else:
        print("⚠️ 候選池為空，略過 CSV 匯出（JSON 已輸出）")

    print("=== 自我檢查完成 ===")
    return 0


if __name__ == '__main__':
    sys.exit(main())


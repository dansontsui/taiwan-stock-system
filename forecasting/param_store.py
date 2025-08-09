from __future__ import annotations
import json
import os
from typing import Optional, Dict, Any
from .config import cfg, ensure_dirs

PARAMS_FILE = os.path.join(cfg.output_dir, "best_params.json")


def _load_all() -> Dict[str, Dict[str, Dict[str, Any]]]:
    ensure_dirs()
    if not os.path.exists(PARAMS_FILE):
        return {}
    try:
        with open(PARAMS_FILE, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_all(data: Dict[str, Dict[str, Dict[str, Any]]]) -> None:
    ensure_dirs()
    with open(PARAMS_FILE, "w", encoding="utf-8-sig") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))


def get_best_params(stock_id: str, model_name: str) -> Optional[Dict[str, Any]]:
    """取得該股票與模型的最佳參數"""
    data = _load_all()
    return data.get(stock_id, {}).get(model_name)


def save_best_params(stock_id: str, model_name: str, params: Dict[str, Any]) -> None:
    """儲存該股票與模型的最佳參數"""
    data = _load_all()
    data.setdefault(stock_id, {})[model_name] = params
    _save_all(data)


def get_best_model(stock_id: str) -> Optional[str]:
    """取得該股票最近保存的最佳模型名稱（由回測/調校得出）"""
    data = _load_all()
    val = data.get(stock_id, {}).get("_preferred_model")
    return str(val) if isinstance(val, str) else None


def save_best_model(stock_id: str, model_name: str) -> None:
    """保存該股票的最佳模型名稱，供單次預測優先採用"""
    data = _load_all()
    bucket = data.setdefault(stock_id, {})
    bucket["_preferred_model"] = model_name
    _save_all(data)


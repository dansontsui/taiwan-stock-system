# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional


def _safe_setup_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")  # type: ignore[attr-defined]
    except Exception:
        pass


def generate_project_status(
    system_status: Dict[str, Any],
    key_metrics: Dict[str, float],
    file_paths: Dict[str, str],
    execution_log: list[Dict[str, Any]],
    output_path: str = "stock_price_investment_system/Project_status.md"
) -> str:
    """
    自動生成 Project_status.md（中文）
    
    Args:
        system_status: 系統狀態（最新執行時間、使用模型、候選池數量等）
        key_metrics: 關鍵指標（年化報酬、夏普、最大回撤等）
        file_paths: 檔案路徑（模型檔、參數檔、報表檔位置）
        execution_log: 執行紀錄（最近 5 次執行結果）
        output_path: 輸出路徑
    
    Returns:
        生成的檔案路徑
    """
    _safe_setup_stdout()
    
    now = datetime.now()
    
    content = f"""# 股價預測與投資建議系統 - 專案狀態記錄

## 📊 系統狀態摘要

- **最新更新時間**：{now.strftime('%Y-%m-%d %H:%M:%S')}
- **使用模型**：{system_status.get('current_model', '未設定')}
- **候選池數量**：{system_status.get('candidate_pool_size', 0)} 檔股票
- **資料範圍**：{system_status.get('data_range', '未知')}
- **系統狀態**：{system_status.get('status', '正常運行')}

## 🎯 關鍵績效指標

### 外層 Holdout 回測結果
- **年化報酬率**：{key_metrics.get('annual_return', 0):.2f}%
- **夏普比率**：{key_metrics.get('sharpe_ratio', 0):.2f}
- **最大回撤**：{key_metrics.get('max_drawdown', 0):.2f}%
- **勝率**：{key_metrics.get('win_rate', 0):.1f}%
- **平均持有期**：{key_metrics.get('avg_holding_period', 0):.1f} 個月

### 模型表現
- **預測準確率**：{key_metrics.get('prediction_accuracy', 0):.1f}%
- **方向準確率**：{key_metrics.get('direction_accuracy', 0):.1f}%

## 📁 重要檔案路徑

### 模型與參數
- **最佳參數檔**：`{file_paths.get('best_params', '未生成')}`
- **訓練模型檔**：`{file_paths.get('trained_models', '未生成')}`
- **候選池清單**：`{file_paths.get('candidate_pool', '未生成')}`

### 報表與紀錄
- **外層回測報告**：`{file_paths.get('holdout_report', '未生成')}`
- **互動式圖表**：`{file_paths.get('interactive_charts', '未生成')}`
- **交易紀錄**：`{file_paths.get('trading_log', '未生成')}`

## 📋 最近執行紀錄

"""
    
    # 添加執行紀錄
    if execution_log:
        for i, log in enumerate(execution_log[-5:], 1):  # 最近 5 次
            content += f"""### 第 {i} 次執行
- **時間**：{log.get('timestamp', '未知')}
- **操作**：{log.get('operation', '未知')}
- **結果**：{log.get('result', '未知')}
- **警告**：{log.get('warnings', '無')}

"""
    else:
        content += "暫無執行紀錄\n\n"
    
    content += f"""## ⚙️ 系統配置

### 模型參數
- **訓練視窗**：{system_status.get('train_window', 48)} 個月
- **測試視窗**：{system_status.get('test_window', 12)} 個月
- **步長**：{system_status.get('stride', 12)} 個月

### 風控設定
- **單股權重上限**：{system_status.get('max_position_weight', 10)}%
- **停損**：{system_status.get('stop_loss', -15)}%
- **停利**：{system_status.get('take_profit', 25)}%

---

**系統版本**：股價預測與投資建議系統 v1.0  
**最後更新**：{now.strftime('%Y-%m-%d %H:%M:%S')}  
**狀態**：{'✅ 正常運行' if system_status.get('status') == '正常運行' else '⚠️ 需要關注'}
"""
    
    # 確保目錄存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 寫入檔案（UTF-8-SIG 避免 cp950）
    with open(output_path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    
    return output_path


def generate_commit_message(operation: str, metrics: Dict[str, float], details: str = "") -> str:
    """
    生成中文 git commit message
    
    Args:
        operation: 操作類型（如 '月度更新'、'參數調校'、'外層回測'）
        metrics: 關鍵指標
        details: 額外細節
    
    Returns:
        中文 commit message
    """
    base_msg = f"🔄 {operation}"
    
    if operation == "月度更新":
        candidate_count = int(metrics.get('candidate_pool_size', 0))
        annual_return = metrics.get('annual_return', 0)
        base_msg = f"🔄 完成月度股價預測更新 - 候選池{candidate_count}檔，外層年化報酬{annual_return:.1f}%"
    
    elif operation == "參數調校":
        accuracy = metrics.get('prediction_accuracy', 0)
        candidate_count = int(metrics.get('candidate_pool_size', 0))
        base_msg = f"⚙️ 重新調校股價模型參數 - 預測準確率{accuracy:.1f}%，候選池{candidate_count}檔"
    
    elif operation == "外層回測":
        sharpe = metrics.get('sharpe_ratio', 0)
        drawdown = metrics.get('max_drawdown', 0)
        base_msg = f"📊 外層回測完成 - 夏普比率{sharpe:.2f}，最大回撤{drawdown:.1f}%"
    
    if details:
        base_msg += f" ({details})"
    
    return base_msg


# 範例使用
if __name__ == "__main__":
    # 測試範例
    system_status = {
        'current_model': 'XGBoost',
        'candidate_pool_size': 12,
        'data_range': '2015-01 ~ 2024-12',
        'status': '正常運行',
        'train_window': 48,
        'test_window': 12,
        'stride': 12,
        'max_position_weight': 10,
        'stop_loss': -15,
        'take_profit': 25
    }
    
    key_metrics = {
        'annual_return': 8.5,
        'sharpe_ratio': 1.34,
        'max_drawdown': -8.9,
        'win_rate': 65.2,
        'avg_holding_period': 2.3,
        'prediction_accuracy': 72.1,
        'direction_accuracy': 68.4
    }
    
    file_paths = {
        'best_params': 'outputs/best_params.json',
        'trained_models': 'models/xgboost_stock_price.bin',
        'candidate_pool': 'outputs/candidate_pool.csv',
        'holdout_report': 'reports/holdout_backtest.html',
        'interactive_charts': 'reports/interactive_charts.html',
        'trading_log': 'reports/trading_log.csv'
    }
    
    execution_log = [
        {
            'timestamp': '2024-01-15 10:30:00',
            'operation': '參數調校',
            'result': '成功',
            'warnings': '無'
        }
    ]
    
    output_path = generate_project_status(system_status, key_metrics, file_paths, execution_log)
    print(f"✅ Project_status.md 已生成：{output_path}")
    
    # 測試 commit message
    commit_msg = generate_commit_message("月度更新", {'candidate_pool_size': 12, 'annual_return': 8.5})
    print(f"📝 Commit message：{commit_msg}")

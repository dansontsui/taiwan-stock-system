# -*- coding: utf-8 -*-
"""
以季度區間執行滾動回測（EPS），並輸出 ASCII 安全的中文日誌。
Windows/macOS 皆可執行，避免 cp950 無法編碼的字元（已移除表情符號）。
"""
import os
import sys
from datetime import datetime

# Ensure project imports work when run from repo root or this folder
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.data.database_manager import DatabaseManager
from src.predictors.backtest_engine import BacktestEngine

class TeeWriter:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
            except Exception:
                # Best-effort; ignore encoding issues on file stream
                pass
        return len(data)
    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass

def ascii_safe(text: str) -> str:
    # Replace common non-ASCII markers with ASCII equivalents
    repl = {
        '⚠️': '[ALERT]', '⚠': '[ALERT]', '✅': '[OK]', '❌': '[X]', '🎯': '', '📊': '', '📈': '', '💡': '', '🧭': '',
        '％': '%', '～': '~', '—': '-', '–': '-', '‧': '.', '、': ',', '：': ':', '．': '.', '－': '-', '＋': '+', '％': '%',
        '→': '->'
    }
    out = []
    for ch in text:
        if ch in repl:
            out.append(repl[ch])
        else:
            out.append(ch)
    return ''.join(out)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='以季度區間執行EPS滾動回測（中文、ASCII日誌）')
    parser.add_argument('--stock', default='8299')
    parser.add_argument('--start-quarter', default='2022-Q1')
    parser.add_argument('--end-quarter', default='2025-Q2')
    parser.add_argument('--optimize-after', action='store_true')
    parser.add_argument('--retrain-per-step', action='store_true')
    args = parser.parse_args()

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    logs_dir = os.path.join(PROJECT_ROOT, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, f'backtest_range_{args.stock}_{ts}.log')

    with open(log_path, 'w', encoding='utf-8') as logf:
        # Compose tee writer for ASCII-safe output
        tee = TeeWriter(sys.stdout, logf)
        def print2(*a, **kw):
            msg = ' '.join(str(x) for x in a)
            msg = ascii_safe(msg)
            tee.write(msg + ('\n' if not msg.endswith('\n') else ''))
            tee.flush()

        print2('=== 區間滾動回測（EPS） ===')
        print2('股票=', args.stock, '區間=', args.start_quarter, '→', args.end_quarter,
               '每步重訓=', args.retrain_per_step, '回測後優化=', args.optimize_after)

        db = DatabaseManager()
        engine = BacktestEngine(db)
        res = engine.run_comprehensive_backtest_by_range(
            stock_id=args.stock,
            start_quarter=args.start_quarter,
            end_quarter=args.end_quarter,
            prediction_types=['eps'],
            retrain_ai_per_step=args.retrain_per_step,
            optimize_after=args.optimize_after
        )

        eps = res.get('results', {}).get('eps', {})
        ok = eps.get('success', False)
        print2('success=', ok)
        data = eps.get('backtest_results', [])
        print2('periods_tested=', len(data))

        # 印出全部回測資料列（ASCII）
        print2('\n--- 全部回測資料列 ---')
        for i, row in enumerate(data):
            pred = row.get('prediction', {}).get('predicted_eps')
            act = row.get('actual', {}).get('actual_eps')
            tq = row.get('target_quarter')
            ab = row.get('abnormal', {})
            mark = '[ALERT]' if ab.get('is_abnormal') else ''
            print2(f"{i+1:02d} 目標季度={tq} 預測EPS={pred} 實際EPS={act} 標記={mark}")

        # Summary stats (operating vs overall)
        stats = eps.get('statistics', {})
        op = stats.get('operating_only', {}) if isinstance(stats, dict) else {}
        ov = stats.get('overall', {}) if isinstance(stats, dict) else {}
        ab = stats.get('abnormal_only', {}) if isinstance(stats, dict) else {}
        print2('\n--- EPS分層統計 ---')
        print2(f"營業（排除異常）: 期數={op.get('total_periods',0)} 平均MAPE={op.get('avg_eps_mape',0):.1f}% 方向準確度={op.get('direction_accuracy',0):.1%}")
        print2(f"總體（含異常）  : 期數={ov.get('total_periods',0)} 平均MAPE={ov.get('avg_eps_mape',0):.1f}% 方向準確度={ov.get('direction_accuracy',0):.1%}")
        print2(f"異常季度        : 期數={ab.get('total_periods',0)} 平均MAPE={ab.get('avg_eps_mape',0):.1f}%")

        # Abnormal reasons list
        print2('\n--- 異常季度清單 ---')
        cnt_ab = 0
        for row in data:
            abn = row.get('abnormal', {})
            if abn.get('is_abnormal'):
                cnt_ab += 1
                tq = row.get('target_quarter')
                reason = abn.get('reason') or 'N/A'
                nm = abn.get('net_margin')
                pm = abn.get('prev_net_margin')
                print2(f"- {tq}: {reason} | 淨利率={nm} 前期={pm}")
        print2('異常期數=', cnt_ab)

        # 基本檢查
        print2('\n--- 結果檢查 ---')
        if not ok:
            print2('[X] 回測失敗')
            sys.exit(1)
        if len(data) == 0:
            print2('[X] 無任何回測資料')
            sys.exit(1)
        print2('[OK] 回測產生資料')

        print2('\n日誌檔案=', log_path)

if __name__ == '__main__':
    main()


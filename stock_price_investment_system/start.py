# -*- coding: utf-8 -*-
from __future__ import annotations
import sys


def _safe_setup_stdout():
    try:
        # 避免 Windows cp950 編碼問題
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")  # type: ignore[attr-defined]
    except Exception:
        pass


def _p(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            sys.stdout.write(msg.encode("utf-8", "ignore").decode("utf-8", "ignore") + "\n")
        except Exception:
            pass


def main():
    _safe_setup_stdout()
    
    _p("\n============================================================")
    _p("🏦 股價預測與投資建議系統 - 功能選單")
    _p("============================================================")
    _p("  1) 執行月度流程（營收→股價→選股→建議→報告）")
    _p("  2) 只跑股價預測")
    _p("  3) 只產生投資建議")
    _p("  4) 查看追蹤清單")
    _p("  q) 離開系統")
    _p("------------------------------------------------------------")
    
    sel = input("🎯 請選擇功能 (1-4, q): ").strip().lower()
    
    if sel == "1":
        _p("⚙️  執行月度流程（尚未實作，將在 MVP 中補上）")
    elif sel == "2":
        _p("📈 執行股價預測（尚未實作，將在 MVP 中補上）")
    elif sel == "3":
        _p("🧭 產生投資建議（尚未實作，將在 MVP 中補上）")
    elif sel == "4":
        _p("📋 查看追蹤清單（尚未實作，將在 MVP 中補上）")
    elif sel in {"q", "quit", "exit"}:
        _p("👋 再見！")
        return 0
    else:
        _p("❌ 無效選項，請重試。")
    return 0


if __name__ == "__main__":
    sys.exit(main())


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
    _p("  5) AI 模型訓練（股價模型）")
    _p("  6) 參數調校與優化（股價模型）")
    _p("  7) 回測與模型評估（股價模型）")
    _p("  8) 模型與參數管理（列出/匯出/刪除）")
    _p("  9) 報表輸出（HTML/CSV，中文）")
    _p("  10) 生成 candidate pool（內層統計套門檻）")
    _p("  11) 執行外層 holdout 回測")
    _p("------------------------------------------------------------")
    _p("💡 建議執行順序：")
    _p("   首次建置：6→5→7→10→11")
    _p("   每月更新：5→7→10→11（若績效下降則從6開始）")
    _p("------------------------------------------------------------")

    sel = input("🎯 請選擇功能 (1-11, q): ").strip().lower()
    
    if sel == "1":
        _p("⚙️  執行月度流程（尚未實作，將在 MVP 中補上）")
    elif sel == "2":
        _p("📈 執行股價預測（尚未實作，將在 MVP 中補上）")
    elif sel == "3":
        _p("🧭 產生投資建議（尚未實作，將在 MVP 中補上）")
    elif sel == "4":
        _p("📋 查看追蹤清單（尚未實作，將在 MVP 中補上）")
    elif sel == "5":
        _p("🤖 AI 模型訓練（股價模型）- 使用最佳參數訓練模型並輸出 models/*.bin")
    elif sel == "6":
        _p("🔧 參數調校與優化（股價模型）- 網格搜尋最佳超參數並保存")
    elif sel == "7":
        _p("📊 回測與模型評估（股價模型）- 內層 walk-forward 多 fold 驗證")
    elif sel == "8":
        _p("🗂️  模型與參數管理 - 列出/匯出/刪除已訓練的模型與參數檔")
    elif sel == "9":
        _p("📋 報表輸出（HTML/CSV，中文）- 生成互動式回測與交易報表")
    elif sel == "10":
        _p("🎯 生成 candidate pool - 依內層統計套門檻篩選模型友善股票池")
    elif sel == "11":
        _p("🏆 執行外層 holdout 回測 - 在未見樣本驗證候選池真實績效")
    elif sel in {"q", "quit", "exit"}:
        _p("👋 再見！")
        return 0
    else:
        _p("❌ 無效選項，請重試。")
    return 0


if __name__ == "__main__":
    sys.exit(main())


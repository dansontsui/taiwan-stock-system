@echo off
chcp 65001 >nul
title 台股分析系統終端機啟動

echo ================================================================================
echo 🚀 台股分析系統終端機啟動 (Windows版)
echo ================================================================================
echo 📊 專為終端機使用者設計，不需要Web瀏覽器
echo ================================================================================
echo.

REM 檢查Python是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，請先安裝Python 3.8+
    echo 💡 下載地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python已安裝
python --version

REM 切換到腳本目錄
cd /d "%~dp0"

echo.
echo 📂 當前目錄: %CD%
echo.

REM 檢查必要檔案
if not exist "終端機啟動.py" (
    echo ❌ 未找到終端機啟動.py檔案
    pause
    exit /b 1
)

if not exist "config.py" (
    echo ❌ 未找到config.py檔案，請確認在正確的專案目錄
    pause
    exit /b 1
)

echo ✅ 必要檔案檢查通過

REM 顯示選單
:menu
cls
echo ================================================================================
echo 🚀 台股分析系統終端機啟動
echo ================================================================================
echo.
echo 📋 請選擇操作:
echo 1. 🧪 測試所有腳本 (推薦首次使用)
echo 2. 🔄 每日增量更新 + 監控
echo 3. 💰 現金流量表收集 + 監控
echo 4. 🎯 除權除息結果收集 + 監控
echo 5. 🖥️ 只啟動終端機監控
echo 6. 📊 查看資料庫統計
echo 7. 🎯 進入Python互動模式
echo 0. ❌ 退出
echo.

set /p choice="請輸入選項 (0-7): "

if "%choice%"=="0" (
    echo 👋 再見！
    goto end
) else if "%choice%"=="1" (
    echo.
    echo 🧪 開始測試所有腳本...
    python 測試所有腳本.py
    pause
    goto menu
) else if "%choice%"=="2" (
    echo.
    echo 🔄 執行每日增量更新...
    python scripts/collect_daily_update.py --batch-size 3
    if errorlevel 1 (
        echo ❌ 每日更新失敗
        pause
        goto menu
    )
    echo ✅ 每日更新完成，啟動監控...
    python 終端機監控.py --mode monitor
    goto menu
) else if "%choice%"=="3" (
    echo.
    echo 💰 執行現金流量表收集...
    python scripts/collect_cash_flows.py --batch-size 3 --test
    if errorlevel 1 (
        echo ❌ 現金流量收集失敗
        pause
        goto menu
    )
    echo ✅ 現金流量收集完成，啟動監控...
    python 終端機監控.py --mode monitor
    goto menu
) else if "%choice%"=="4" (
    echo.
    echo 🎯 執行除權除息結果收集...
    python scripts/collect_dividend_results.py --batch-size 3 --test
    if errorlevel 1 (
        echo ❌ 除權除息收集失敗
        pause
        goto menu
    )
    echo ✅ 除權除息收集完成，啟動監控...
    python 終端機監控.py --mode monitor
    goto menu
) else if "%choice%"=="5" (
    echo.
    echo 🖥️ 啟動終端機監控...
    python 終端機監控.py --mode monitor
    goto menu
) else if "%choice%"=="6" (
    echo.
    echo 📊 查看資料庫統計...
    python 終端機監控.py --mode stats
    pause
    goto menu
) else if "%choice%"=="7" (
    echo.
    echo 🎯 進入Python互動模式...
    python 終端機啟動.py
    goto menu
) else (
    echo ❌ 無效選項，請重新選擇
    pause
    goto menu
)

:end
echo.
echo 💡 使用提示:
echo    • 如果遇到PowerShell執行政策問題，請使用此批次檔
echo    • 建議首次使用先選擇「測試所有腳本」
echo    • 終端機監控按 Ctrl+C 可停止
echo    • 如需Web介面，請使用其他啟動方式
echo.
pause

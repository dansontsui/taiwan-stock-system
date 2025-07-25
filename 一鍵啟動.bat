@echo off
chcp 65001 >nul
title 台股分析系統一鍵啟動

echo ================================================================================
echo 🚀 台股分析系統一鍵啟動 (Windows版)
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
if not exist "一鍵啟動.py" (
    echo ❌ 未找到一鍵啟動.py檔案
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
echo.
echo 📋 請選擇啟動模式:
echo 1. 🔄 每日增量更新 + Web監控 (推薦)
echo 2. 📊 綜合資料收集 + Web監控
echo 3. 💰 現金流量表收集 + Web監控
echo 4. 🌐 只啟動Web監控介面
echo 5. 🔍 檢查系統狀態
echo 6. 🎯 互動模式 (完整選單)
echo.

set /p choice="請輸入選項 (1-6): "

if "%choice%"=="1" (
    echo.
    echo 🚀 啟動每日增量更新 + Web監控...
    python 一鍵啟動.py --mode daily
) else if "%choice%"=="2" (
    echo.
    echo 🚀 啟動綜合資料收集 + Web監控...
    python 一鍵啟動.py --mode comprehensive
) else if "%choice%"=="3" (
    echo.
    echo 🚀 啟動現金流量表收集 + Web監控...
    python 一鍵啟動.py --mode cash_flow
) else if "%choice%"=="4" (
    echo.
    echo 🚀 只啟動Web監控介面...
    python 一鍵啟動.py --mode web
) else if "%choice%"=="5" (
    echo.
    echo 🔍 檢查系統狀態...
    python 一鍵啟動.py --mode check
    pause
) else if "%choice%"=="6" (
    echo.
    echo 🎯 進入互動模式...
    python 一鍵啟動.py --mode auto
) else (
    echo ❌ 無效選項，啟動互動模式...
    python 一鍵啟動.py --mode auto
)

echo.
echo 💡 如果遇到問題，請檢查:
echo    • Python版本是否為3.8+
echo    • 是否已安裝必要套件: pip install streamlit pandas numpy
echo    • 是否在正確的專案目錄中執行
echo.
pause

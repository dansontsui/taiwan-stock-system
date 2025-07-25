#!/bin/bash
# -*- coding: utf-8 -*-
# 台股分析系統一鍵啟動腳本 (Mac/Linux版)

# 設定顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 顯示橫幅
echo "================================================================================"
echo -e "${BLUE}🚀 台股分析系統一鍵啟動 (Mac/Linux版)${NC}"
echo "================================================================================"
echo

# 檢查Python是否安裝
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ 未找到Python，請先安裝Python 3.8+${NC}"
        echo -e "${YELLOW}💡 Mac用戶可使用: brew install python${NC}"
        echo -e "${YELLOW}💡 Linux用戶可使用: sudo apt install python3${NC}"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo -e "${GREEN}✅ Python已安裝${NC}"
$PYTHON_CMD --version

# 切換到腳本目錄
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo
echo -e "${CYAN}📂 當前目錄: $(pwd)${NC}"
echo

# 檢查必要檔案
if [ ! -f "一鍵啟動.py" ]; then
    echo -e "${RED}❌ 未找到一鍵啟動.py檔案${NC}"
    exit 1
fi

if [ ! -f "config.py" ]; then
    echo -e "${RED}❌ 未找到config.py檔案，請確認在正確的專案目錄${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 必要檔案檢查通過${NC}"

# 檢查並安裝依賴
echo
echo -e "${YELLOW}🔧 檢查Python套件...${NC}"

# 檢查pip
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo -e "${RED}❌ pip未安裝，請先安裝pip${NC}"
    exit 1
fi

# 檢查必要套件
REQUIRED_PACKAGES=("streamlit" "pandas" "numpy")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! $PYTHON_CMD -c "import $package" &> /dev/null; then
        MISSING_PACKAGES+=("$package")
        echo -e "${RED}❌ $package${NC}"
    else
        echo -e "${GREEN}✅ $package${NC}"
    fi
done

# 如果有缺失套件，詢問是否安裝
if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo
    echo -e "${YELLOW}⚠️ 缺少套件: ${MISSING_PACKAGES[*]}${NC}"
    echo -e "${YELLOW}是否要自動安裝? (y/n)${NC}"
    read -r install_choice
    
    if [[ $install_choice =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}📦 安裝缺失套件...${NC}"
        $PYTHON_CMD -m pip install "${MISSING_PACKAGES[@]}"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 套件安裝完成${NC}"
        else
            echo -e "${RED}❌ 套件安裝失敗${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ 請手動安裝缺失套件: pip install ${MISSING_PACKAGES[*]}${NC}"
        exit 1
    fi
fi

# 顯示選單
echo
echo -e "${PURPLE}📋 請選擇啟動模式:${NC}"
echo "1. 🔄 每日增量更新 + Web監控 (推薦)"
echo "2. 📊 綜合資料收集 + Web監控"
echo "3. 💰 現金流量表收集 + Web監控"
echo "4. 🌐 只啟動Web監控介面"
echo "5. 🔍 檢查系統狀態"
echo "6. 🎯 互動模式 (完整選單)"
echo

read -p "請輸入選項 (1-6): " choice

case $choice in
    1)
        echo
        echo -e "${BLUE}🚀 啟動每日增量更新 + Web監控...${NC}"
        $PYTHON_CMD 一鍵啟動.py --mode daily
        ;;
    2)
        echo
        echo -e "${BLUE}🚀 啟動綜合資料收集 + Web監控...${NC}"
        $PYTHON_CMD 一鍵啟動.py --mode comprehensive
        ;;
    3)
        echo
        echo -e "${BLUE}🚀 啟動現金流量表收集 + Web監控...${NC}"
        $PYTHON_CMD 一鍵啟動.py --mode cash_flow
        ;;
    4)
        echo
        echo -e "${BLUE}🚀 只啟動Web監控介面...${NC}"
        $PYTHON_CMD 一鍵啟動.py --mode web
        ;;
    5)
        echo
        echo -e "${BLUE}🔍 檢查系統狀態...${NC}"
        $PYTHON_CMD 一鍵啟動.py --mode check
        echo
        echo -e "${YELLOW}按任意鍵繼續...${NC}"
        read -n 1
        ;;
    6)
        echo
        echo -e "${BLUE}🎯 進入互動模式...${NC}"
        $PYTHON_CMD 一鍵啟動.py --mode auto
        ;;
    *)
        echo -e "${RED}❌ 無效選項，啟動互動模式...${NC}"
        $PYTHON_CMD 一鍵啟動.py --mode auto
        ;;
esac

echo
echo -e "${YELLOW}💡 如果遇到問題，請檢查:${NC}"
echo "   • Python版本是否為3.8+"
echo "   • 是否已安裝必要套件: pip install streamlit pandas numpy"
echo "   • 是否在正確的專案目錄中執行"
echo "   • Mac用戶可能需要: chmod +x 一鍵啟動.sh"
echo

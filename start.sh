#!/bin/bash
# Taiwan Stock System - Mac專用啟動腳本
# 使用方法: ./start.sh [選項]

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 檢查Python環境
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ 找不到Python，請先安裝Python${NC}"
        exit 1
    fi
}

# 檢查虛擬環境
check_venv() {
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo -e "${GREEN}✅ 虛擬環境已啟動: $(basename $VIRTUAL_ENV)${NC}"
    else
        echo -e "${YELLOW}⚠️  建議啟動虛擬環境${NC}"
        echo -e "${BLUE}💡 執行: source .venv/bin/activate${NC}"
    fi
}

# 顯示說明
show_help() {
    echo -e "${BLUE}📋 Taiwan Stock System - Mac專用啟動腳本${NC}"
    echo ""
    echo -e "${GREEN}用法:${NC}"
    echo "  ./start.sh          # 收集所有股票 (預設)"
    echo "  ./start.sh all      # 收集所有股票 (2,822檔)"
    echo "  ./start.sh main     # 收集主要股票 (50檔)"
    echo "  ./start.sh test     # 測試收集 (5檔)"
    echo "  ./start.sh web      # 啟動Web介面"
    echo "  ./start.sh help     # 顯示說明"
    echo ""
    echo -e "${YELLOW}💡 提示:${NC}"
    echo "  - 首次使用請先執行: pip install -r requirements.txt"
    echo "  - 建議在虛擬環境中運行"
    echo "  - 按 Ctrl+C 停止收集"
}

# 主程式
main() {
    echo -e "${BLUE}🚀 Taiwan Stock System 啟動中...${NC}"
    
    # 檢查環境
    check_python
    check_venv
    
    # 處理參數
    case "${1:-default}" in
        "all"|"a")
            echo -e "${GREEN}🌐 啟動收集所有股票${NC}"
            $PYTHON_CMD c.py all
            ;;
        "main"|"m")
            echo -e "${GREEN}⭐ 啟動收集主要股票${NC}"
            $PYTHON_CMD c.py main
            ;;
        "test"|"t")
            echo -e "${GREEN}🧪 啟動測試收集${NC}"
            $PYTHON_CMD c.py test
            ;;
        "web"|"w")
            echo -e "${GREEN}🌐 啟動Web介面${NC}"
            $PYTHON_CMD run.py
            ;;
        "help"|"h"|"--help"|"-h")
            show_help
            ;;
        "default")
            echo -e "${GREEN}🌐 啟動收集所有股票 (預設)${NC}"
            $PYTHON_CMD c.py
            ;;
        *)
            echo -e "${RED}❌ 未知選項: $1${NC}"
            echo -e "${BLUE}💡 使用 './start.sh help' 查看說明${NC}"
            exit 1
            ;;
    esac
}

# 執行主程式
main "$@"

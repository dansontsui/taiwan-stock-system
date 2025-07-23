#!/bin/bash

# 台股系統 GitHub 設定腳本

echo "🚀 台股歷史股價系統 - GitHub 設定"
echo "=================================="

# 檢查是否已經初始化 Git
if [ ! -d ".git" ]; then
    echo "❌ 錯誤: 請先在專案目錄中執行此腳本"
    exit 1
fi

# 獲取用戶的 GitHub 用戶名
echo "📝 請輸入您的 GitHub 用戶名:"
read -p "GitHub 用戶名: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ 錯誤: GitHub 用戶名不能為空"
    exit 1
fi

# 設定倉庫名稱
REPO_NAME="taiwan-stock-system"
REMOTE_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"

echo ""
echo "📋 設定資訊:"
echo "   GitHub 用戶名: $GITHUB_USERNAME"
echo "   倉庫名稱: $REPO_NAME"
echo "   遠端 URL: $REMOTE_URL"
echo ""

# 確認是否繼續
read -p "確定要繼續嗎？(y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消設定"
    exit 1
fi

echo "🔧 開始設定 GitHub 遠端倉庫..."

# 檢查是否已有 origin 遠端
if git remote get-url origin > /dev/null 2>&1; then
    echo "⚠️  已存在 origin 遠端，將會覆蓋"
    git remote remove origin
fi

# 添加遠端倉庫
echo "📡 添加遠端倉庫..."
git remote add origin "$REMOTE_URL"

# 設定主分支為 main
echo "🌿 設定主分支為 main..."
git branch -M main

# 推送到 GitHub
echo "📤 推送到 GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 成功推送到 GitHub!"
    echo "📍 倉庫地址: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo ""
    echo "🔗 接下來您可以:"
    echo "   1. 前往 GitHub 查看您的倉庫"
    echo "   2. 設定倉庫描述和標籤"
    echo "   3. 邀請協作者 (如需要)"
    echo "   4. 設定 GitHub Pages (如需要)"
else
    echo ""
    echo "❌ 推送失敗!"
    echo "💡 可能的原因:"
    echo "   1. GitHub 倉庫尚未建立"
    echo "   2. 沒有推送權限"
    echo "   3. 網路連線問題"
    echo ""
    echo "🛠️  解決方案:"
    echo "   1. 請先在 GitHub 建立名為 '$REPO_NAME' 的倉庫"
    echo "   2. 確認您有該倉庫的推送權限"
    echo "   3. 檢查網路連線"
    echo "   4. 重新執行此腳本"
fi

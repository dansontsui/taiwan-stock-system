# 🔧 VS Code Git 設定指南

## 🎯 問題描述

VS Code 中看不到 Git 的樹狀圖和狀態顯示。

## 🛠️ 解決方案

### 方案1: 重新開啟專案 (推薦)

1. **關閉當前 VS Code 視窗**
2. **在專案目錄中開啟 VS Code**:
   ```bash
   cd /Users/danson/Documents/augment-projects/findeme/taiwan_stock_system
   code .
   ```
3. **或者開啟工作區文件**:
   ```bash
   code taiwan-stock-system.code-workspace
   ```

### 方案2: 檢查 Git 擴展

1. **開啟擴展面板** (`Cmd+Shift+X`)
2. **確認已安裝以下擴展**:
   - ✅ **Git** (內建)
   - ✅ **GitLens** (`eamodio.gitlens`)
   - ✅ **Git Graph** (`mhutchie.git-graph`)
   - ✅ **Git History** (`donjayamanne.githistory`)

3. **安裝推薦擴展**:
   - VS Code 會自動提示安裝 `.vscode/extensions.json` 中的推薦擴展
   - 點擊 "Install All" 安裝所有推薦擴展

### 方案3: 檢查 Git 設定

1. **開啟命令面板** (`Cmd+Shift+P`)
2. **執行**: `Git: Show Git Output`
3. **檢查是否有錯誤訊息**

### 方案4: 重新載入視窗

1. **開啟命令面板** (`Cmd+Shift+P`)
2. **執行**: `Developer: Reload Window`

### 方案5: 檢查 Source Control 面板

1. **開啟 Source Control 面板** (`Cmd+Shift+G`)
2. **應該會看到**:
   - 📁 **TAIWAN-STOCK-SYSTEM** (倉庫名稱)
   - 🌿 **main** (當前分支)
   - 📊 **Changes** (如果有未提交的變更)

## 🎯 預期的 VS Code Git 功能

### Source Control 面板
```
📁 TAIWAN-STOCK-SYSTEM (main)
├── 📊 Changes (0)
├── 📋 Staged Changes (0)
└── 🔄 Merge Changes (0)
```

### 檔案狀態指示
- **綠色 U**: 新增檔案 (Untracked)
- **黃色 M**: 修改檔案 (Modified)
- **綠色 A**: 已暫存檔案 (Added)
- **紅色 D**: 刪除檔案 (Deleted)

### Git 樹狀圖 (需要 Git Graph 擴展)
1. **開啟命令面板** (`Cmd+Shift+P`)
2. **執行**: `Git Graph: View Git Graph`
3. **會顯示提交歷史樹狀圖**

## 🔍 故障排除

### 如果仍然看不到 Git 狀態

1. **檢查 Git 是否正確安裝**:
   ```bash
   git --version
   ```

2. **檢查當前目錄是否為 Git 倉庫**:
   ```bash
   git status
   ```

3. **檢查 VS Code Git 設定**:
   - 開啟設定 (`Cmd+,`)
   - 搜尋 "git.enabled"
   - 確認已啟用

4. **重設 VS Code 設定**:
   - 刪除 `.vscode` 資料夾
   - 重新開啟 VS Code
   - 重新安裝擴展

### 如果 Git Graph 不顯示

1. **安裝 Git Graph 擴展**:
   ```
   擴展 ID: mhutchie.git-graph
   ```

2. **開啟 Git Graph**:
   - 方法1: `Cmd+Shift+P` → `Git Graph: View Git Graph`
   - 方法2: 點擊狀態列的分支名稱
   - 方法3: Source Control 面板右上角的圖示

## 📊 當前專案 Git 狀態

```bash
# 檢查 Git 狀態
git status
# 輸出: On branch main, Your branch is up to date with 'origin/main'

# 檢查提交歷史
git log --oneline -5
# 輸出:
# 9ae7377 (HEAD -> main, origin/main) 🔧 Fix main-stocks filtering
# 315d1e8 📚 Add GitHub setup guide and automation script
# b843724 🚀 Initial commit: Taiwan Stock System
```

## 🎉 成功指標

當設定正確時，您應該看到：

1. **Source Control 面板** 顯示倉庫資訊
2. **檔案旁邊** 有 Git 狀態指示
3. **狀態列** 顯示當前分支 (main)
4. **Git Graph** 可以正常開啟
5. **GitLens** 顯示檔案歷史和作者資訊

## 🚀 快速修復

**最快的解決方法**:
```bash
# 1. 關閉 VS Code
# 2. 在終端機中執行
cd /Users/danson/Documents/augment-projects/findeme/taiwan_stock_system
code taiwan-stock-system.code-workspace

# 3. 安裝推薦擴展
# 4. 重新載入視窗 (Cmd+Shift+P → Developer: Reload Window)
```

這樣應該就能看到完整的 Git 功能了！ 🎊

# start.py 使用說明

## 概述

`start.py` 是 Taiwan Stock System 的跨平台啟動腳本，功能與 `start.sh` 完全相同，但支援 Windows、macOS 和 Linux 系統。

## 功能特色

- ✅ **跨平台支援**：Windows、macOS、Linux 都能使用
- ✅ **互動式選單**：無參數執行時顯示友善的選單介面
- ✅ **自動檢測 Python**：自動尋找 python3 或 python 命令
- ✅ **虛擬環境檢查**：提醒使用者啟動虛擬環境
- ✅ **彩色輸出**：支援終端機顏色顯示（Windows 需要 colorama）
- ✅ **錯誤處理**：完整的錯誤處理和使用者中斷處理
- ✅ **編碼相容**：移除 emoji 字符，避免 cp950 編碼問題
- ✅ **雙重模式**：支援命令列參數和互動式選單兩種使用方式

## 使用方法

### 互動式選單模式

```bash
# 顯示互動式選單（推薦使用方式）
python start.py
```

執行後會看到：
```
Taiwan Stock System - 跨平台啟動腳本
==================================================
請選擇要執行的功能:

1. 收集所有股票 (2,822檔)
2. 收集主要股票 (50檔)
3. 測試收集 (3檔)
4. 啟動Web介面
5. 顯示說明
0. 退出

==================================================
請輸入選項 (0-5):
```

### 命令列參數模式

```bash
# 顯示說明
python start.py help

# 收集所有股票
python start.py all

# 收集主要股票（50檔）
python start.py main

# 測試收集（3檔）
python start.py test

# 啟動Web介面
python start.py web
```

### 簡化參數

```bash
# 簡化參數也支援
python start.py a      # = all
python start.py m      # = main
python start.py t      # = test
python start.py w      # = web
python start.py h      # = help
```

## 輸出範例

### 互動式選單
```
[START] Taiwan Stock System 啟動中...
[WARNING] 建議啟動虛擬環境
[INFO] 執行: .venv\Scripts\activate.bat

Taiwan Stock System - 跨平台啟動腳本
==================================================
請選擇要執行的功能:

1. 收集所有股票 (2,822檔)
2. 收集主要股票 (50檔)
3. 測試收集 (3檔)
4. 啟動Web介面
5. 顯示說明
0. 退出

==================================================
請輸入選項 (0-5): 3

[TEST] 啟動測試收集
... (執行測試收集)

按 Enter 鍵返回選單...
```

### 顯示說明
```
[START] Taiwan Stock System 啟動中...
[WARNING] 建議啟動虛擬環境
[INFO] 執行: .venv\Scripts\activate.bat

Taiwan Stock System - 跨平台啟動腳本

用法:
  python start.py          # 顯示選單
  python start.py all      # 收集所有股票 (2,822檔)
  python start.py main     # 收集主要股票 (50檔)
  python start.py test     # 測試收集 (3檔)
  python start.py web      # 啟動Web介面
  python start.py help     # 顯示說明

[提示]:
  - 首次使用請先執行: pip install -r requirements.txt
  - 建議在虛擬環境中運行
  - 按 Ctrl+C 停止收集
```

### 測試收集
```
[START] Taiwan Stock System 啟動中...
[WARNING] 建議啟動虛擬環境
[INFO] 執行: .venv\Scripts\activate.bat
[TEST] 啟動測試收集
[TEST] 測試收集
[START] 啟動收集: test 範圍, 批次大小 1
[DATE] 2015-08-03 ~ 2025-07-31
[INFO] 按 Ctrl+C 停止
========================================
簡化版資料收集
============================================================
找到 3 檔股票
測試模式：只收集前3檔

收集 股價 資料...
----------------------------------------
[1/3] 1101 (台泥)
  成功: 117 筆資料，儲存 117 筆
[2/3] 1102 (亞泥)
  成功: 116 筆資料，儲存 116 筆
[3/3] 1103 (嘉泥)
  成功: 117 筆資料，儲存 117 筆
股價 完成: 成功 3, 失敗 0, 儲存 350 筆
...
```

## 技術細節

### 環境檢查
- 自動檢測 `python3` 或 `python` 命令
- 檢查虛擬環境狀態
- 提供適合的啟動建議（Windows/Unix）

### 顏色支援
- Windows：嘗試使用 colorama 套件
- Unix/Linux/Mac：使用 ANSI 顏色碼
- 如果無法使用顏色，會自動降級為純文字

### 錯誤處理
- `KeyboardInterrupt`：使用者按 Ctrl+C 中斷
- `CalledProcessError`：子程序執行失敗
- `FileNotFoundError`：找不到 Python 或腳本檔案

## 與 start.sh 的差異

| 功能 | start.sh | start.py |
|------|----------|----------|
| 平台支援 | macOS/Linux | Windows/macOS/Linux |
| Python 檢測 | bash 命令 | Python shutil.which() |
| 顏色支援 | ANSI 碼 | 跨平台顏色支援 |
| 編碼問題 | 可能有 emoji 問題 | 已移除 emoji 字符 |
| 虛擬環境提示 | Unix 路徑 | 平台適應路徑 |

## 測試結果

✅ **功能測試通過**
- 所有參數選項正常運作
- 錯誤處理正確
- 虛擬環境檢查正常
- 跨平台相容性良好

✅ **編碼測試通過**
- 移除所有 emoji 字符
- 避免 cp950 編碼問題
- 中文字符正常顯示

## 建議使用方式

### 新手使用者
1. **互動式選單**：直接執行 `python start.py` 使用友善的選單介面
2. **測試功能**：選擇選項 3 進行測試收集，確認系統正常運作
3. **查看說明**：選擇選項 5 查看詳細使用說明

### 進階使用者
1. **快速測試**：使用 `python start.py test` 進行快速測試
2. **生產環境**：使用 `python start.py all` 收集完整資料
3. **開發除錯**：使用 `python start.py main` 收集主要股票
4. **Web 介面**：使用 `python start.py web` 啟動網頁介面

### 自動化腳本
- 在批次檔或自動化腳本中使用命令列參數模式
- 例如：`python start.py all > logs/collection.log 2>&1`

## 注意事項

- 建議在虛擬環境中運行
- 首次使用請先執行 `pip install -r requirements.txt`
- 使用 Ctrl+C 可以安全中斷執行
- 日誌檔案會自動儲存在 `logs/` 目錄下

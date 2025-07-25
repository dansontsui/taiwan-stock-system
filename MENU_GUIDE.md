# 🎯 互動式選單使用指南

## 🚀 啟動選單

```bash
python scripts/menu.py
```

## 📋 選單功能說明

### 1️⃣ 預設清單 (24檔) - 測試模式
**適合**: 初次使用、系統測試
- 📊 **收集範圍**: 24檔精選股票
- ⏰ **收集時間**: 5-10分鐘
- 🔄 **API請求**: ~240次
- ✅ **自動跳過**: 已有資料的股票

**執行命令**: `python scripts/collect_data.py --test --skip-existing`

---

### 2️⃣ 主要股票 (3,782檔) - 測試模式 ⭐ 推薦
**適合**: 了解系統功能、驗證收集範圍
- 📊 **收集範圍**: 上市+上櫃+00開頭ETF (3,782檔)
- ⏰ **收集時間**: 約1個月資料
- 🔄 **API請求**: 視已有資料而定
- ✅ **自動跳過**: 已有資料的股票

**執行命令**: `python scripts/collect_data.py --main-stocks --test --skip-existing`

---

### 3️⃣ 主要股票 (3,782檔) - 完整收集
**適合**: 專業分析、研究用途
- 📊 **收集範圍**: 上市+上櫃+00開頭ETF (3,782檔)
- ⏰ **收集時間**: 60-100小時
- 🔄 **API請求**: ~38,000次
- ⚠️ **注意**: 建議使用分批收集模式

**執行命令**: `python scripts/collect_data.py --main-stocks --skip-existing`

---

### 4️⃣ 分批收集 - 測試模式 🔥 最推薦
**適合**: 所有用戶的首選
- 📊 **收集範圍**: 上市+上櫃+00開頭ETF (3,782檔)
- ⏰ **收集時間**: 約1個月資料，自動處理
- 🤖 **智能功能**: 
  - ✅ 自動處理API限制
  - ✅ 智能等待 (節省30-50分鐘)
  - ✅ 自動跳過已有資料
  - ✅ 斷點續傳

**執行命令**: `python scripts/collect_batch.py --test`

---

### 5️⃣ 分批收集 - 完整收集
**適合**: 需要完整歷史資料的專業用戶
- 📊 **收集範圍**: 上市+上櫃+00開頭ETF (3,782檔)
- ⏰ **收集時間**: 15-20小時 (自動處理)
- 🤖 **全自動**: 無需人工干預
- 📦 **批次大小**: 可自定義 (建議100-300)

**執行命令**: `python scripts/collect_batch.py --batch-size {批次大小}`

---

### 6️⃣ 指定股票收集
**適合**: 特定股票需求
- 📊 **收集範圍**: 自定義股票代碼
- ⏰ **收集時間**: 視股票數量而定
- 🎯 **靈活性**: 完全自定義
- 📝 **輸入格式**: 用空格分隔，如 `2330 8299 0050 0056`

**執行命令**: `python scripts/collect_data.py --stocks {股票代碼} --skip-existing`

---

### 7️⃣ 指定時間範圍收集
**適合**: 特定時間段的資料需求
- 📊 **收集範圍**: 可選預設清單、主要股票或指定股票
- 📅 **時間範圍**: 自定義開始和結束日期
- 🎯 **精確控制**: 只收集需要的時間段
- 📝 **日期格式**: YYYY-MM-DD

**執行命令**: `python scripts/collect_data.py {範圍參數} --start-date {開始日期} --end-date {結束日期} --skip-existing`

---

### 8️⃣ 系統管理
**包含子選單**:
1. **啟動Web系統** - 開啟網頁介面 (http://localhost:5000)
2. **查看資料庫統計** - 顯示已收集的股票資料統計
3. **測試跳過功能** - 驗證跳過已有資料功能
4. **測試智能等待** - 驗證智能等待時間計算

---

### 9️⃣ 查看說明文檔
**包含文檔**:
1. **README.md** - 系統總覽和快速開始
2. **COLLECTION_MODES.md** - 收集模式詳細說明
3. **SMART_WAIT_GUIDE.md** - 智能等待功能說明
4. **SKIP_EXISTING_GUIDE.md** - 跳過已有資料功能說明

---

### 0️⃣ 退出
安全退出選單系統

## 🎯 使用建議

### 🆕 新用戶推薦流程
1. **選擇 4** - 分批收集測試模式 (驗證系統功能)
2. **選擇 8-2** - 查看資料庫統計 (確認收集結果)
3. **選擇 5** - 分批收集完整模式 (收集完整資料)

### 💼 專業用戶推薦
1. **選擇 2** - 主要股票測試模式 (快速驗證)
2. **選擇 5** - 分批收集完整模式 (一次性收集)
3. **選擇 7** - 指定時間範圍 (補充特定時段)

### 🎯 特定需求用戶
1. **選擇 6** - 指定股票收集 (只收集關注股票)
2. **選擇 7** - 指定時間範圍 (特定時段分析)

## 💡 選單優勢

### 🚫 不用記命令
- 所有功能都有清楚的選項說明
- 不需要記住複雜的參數組合
- 友善的中文介面

### 🛡️ 安全確認
- 每個操作都會顯示將要執行的命令
- 執行前會要求確認
- 可以隨時取消操作

### 📊 清楚說明
- 每個選項都有詳細的功能說明
- 顯示預估時間和收集範圍
- 提供使用建議

### 🔄 循環操作
- 執行完成後自動返回選單
- 可以連續執行多個操作
- 按 Enter 鍵繼續

## 🎮 操作示例

### 啟動選單
```bash
$ python scripts/menu.py

============================================================
🚀 台股歷史股價系統 - 互動式選單
============================================================

📋 請選擇收集模式:

1️⃣  預設清單 (24檔) - 測試模式
2️⃣  主要股票 (3,782檔) - 測試模式 ⭐ 推薦
3️⃣  主要股票 (3,782檔) - 完整收集
4️⃣  分批收集 - 測試模式 🔥 最推薦
5️⃣  分批收集 - 完整收集
6️⃣  指定股票收集
7️⃣  指定時間範圍收集
8️⃣  系統管理
9️⃣  查看說明文檔
0️⃣  退出

請選擇 (0-9): 
```

### 選擇功能
```bash
請選擇 (0-9): 4

🚀 分批收集主要股票 - 測試模式 (最推薦)
📝 執行命令: python scripts/collect_batch.py --test
------------------------------------------------------------
確定要執行嗎？(y/n): y

# 開始執行收集...
```

## 🎉 總結

互動式選單讓台股資料收集系統變得：
- 🎯 **更易用** - 不用記命令
- 🛡️ **更安全** - 執行前確認
- 📊 **更清楚** - 詳細功能說明
- 🔄 **更方便** - 循環操作介面

**立即體驗**: `python scripts/menu.py` 🚀

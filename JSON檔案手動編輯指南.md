# JSON檔案手動編輯指南

## 🎉 **問題已解決！**

您遇到的「unknown encoding: utf-8-bom」錯誤已經修復完成！

### ❌ **原始問題**
- JSON檔案包含UTF-8 BOM（位元組順序標記）
- 檔案末尾有重複或額外的資料
- Python無法正確解析JSON格式

### ✅ **修復結果**
- ✅ 已移除UTF-8 BOM
- ✅ 已清理重複資料
- ✅ JSON格式現在完全正確
- ✅ 包含2個候選股票

## 📝 **手動編輯指南**

現在您可以安全地手動編輯 `candidate_pool_20250828_092144.json` 檔案了！

### 1. 使用 **UltraEdit** 編輯

```
1. 開啟UltraEdit
2. 檔案 → 開啟 → 選擇JSON檔案
3. 編碼設定：
   - 檢視 → 設定 → 檔案處理 → Unicode/UTF-8偵測
   - 確保選擇「UTF-8 (無BOM)」
4. 編輯完成後：
   - 檔案 → 另存新檔
   - 編碼選擇：UTF-8 (無BOM)
   - 儲存
```

### 2. 使用 **Notepad++** 編輯

```
1. 開啟Notepad++
2. 檔案 → 開啟 → 選擇JSON檔案
3. 檢查編碼：
   - 編碼選單應該顯示「UTF-8」
   - 如果顯示「UTF-8-BOM」，請選擇：
     編碼 → 轉換為UTF-8 (無BOM)
4. 編輯完成後直接儲存 (Ctrl+S)
```

### 3. 使用 **記事本** 編輯

```
1. 開啟記事本
2. 檔案 → 開啟 → 選擇JSON檔案
3. 編輯完成後：
   - 檔案 → 另存新檔
   - 編碼選擇：UTF-8
   - 儲存
```

## 📋 **JSON格式注意事項**

### ✅ **正確的JSON格式**
```json
{
  "success": true,
  "candidate_pool": [
    {
      "stock_id": "1570",
      "stock_score": 80.26
    },
    {
      "stock_id": "2330", 
      "stock_score": 75.50
    }
  ],
  "generated_at": "2025-08-28T08:59:44.410063"
}
```

### ❌ **常見錯誤**
- 缺少逗號：`"key1": "value1" "key2": "value2"`
- 多餘逗號：`"key": "value",}`
- 引號錯誤：`{'key': 'value'}` (應該用雙引號)
- 括號不匹配：`{"key": "value"`

## 🔧 **驗證工具**

### 1. **線上JSON驗證器**
- https://jsonlint.com/
- https://jsonformatter.curiousconcept.com/

### 2. **本地驗證命令**
```bash
python -c "import json; json.load(open('檔案路徑.json', 'r', encoding='utf-8')); print('✅ JSON格式正確')"
```

## 🚨 **重要提醒**

### **編輯前備份**
```bash
# 建議先備份原檔案
copy candidate_pool_20250828_092144.json candidate_pool_20250828_092144.json.backup
```

### **編輯後測試**
編輯完成後，請執行選單5a測試是否正常：
```bash
python stock_price_investment_system/start.py
# 選擇 5a) 執行每月定期定額投資回測（含交易成本）
```

## 📊 **目前檔案狀態**

- ✅ **檔案路徑**: `stock_price_investment_system/results/candidate_pools/candidate_pool_20250828_092144.json`
- ✅ **編碼**: UTF-8 (無BOM)
- ✅ **格式**: 有效的JSON
- ✅ **內容**: 2個候選股票
- ✅ **可編輯**: 是

## 🎯 **現在您可以**

1. **安全編輯JSON檔案** - 使用上述任一編輯器
2. **執行選單5a** - 不會再出現編碼錯誤
3. **修改候選股票** - 新增、刪除或修改股票資料
4. **調整評分** - 修改stock_score數值

**編碼問題已完全解決！** 🎉

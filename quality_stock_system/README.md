# 長期存股「績優股」篩選系統

本資料夾為長期存股績優股（Quality Stock Screening）系統的專案根目錄與資料存放位置（data/）。

目標：以「可持續獲利、穩定配息、財務穩健、估值合理」為核心，建置可參數化、可回測、可視覺化的篩選系統。

目錄結構（初版）：
- data/                 # 系統輸出資料與產物（CSV、快照、暫存）
- sql/                  # 指標計算與清單產生的 SQL 範例
- README.md             # 簡介與使用方式
- DESIGN.md             # 系統設計與架構
- DATA_MODEL.md         # 指標對應資料表與計算來源
- RULE_PROFILES.md      # 規則模板（穩健派/高現金流/價值型等）
- ROADMAP.md            # 路線圖與里程碑

注意事項：
- 檔名一律使用 ASCII；文件內容採 UTF-8（建議以 UTF-8-SIG 匯出報表），避免 Windows cp950 問題。
- 跨平台（Windows/macOS）可執行；CLI 或日誌輸出以中文描述。

快速開始（之後將提供 CLI）：
- 先閱讀 DATA_MODEL.md 確認資料對應
- 依 ROADMAP.md 執行 Phase 1 的資料表補齊與指標計算
- 依 RULE_PROFILES.md 設定策略檔（rule_profile）
- 使用 sql/examples.sql 範例驗證基礎查詢


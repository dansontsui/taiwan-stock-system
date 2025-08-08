# -*- coding: utf-8 -*-
"""
調試成長率計算問題
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_growth_rate():
    """調試成長率計算問題"""
    
    print("🔍 調試成長率計算問題")
    print("=" * 60)
    
    try:
        from src.data.database_manager import DatabaseManager
        
        stock_id = "8299"
        
        print(f"📊 檢查股票: {stock_id}")
        
        # 初始化資料庫管理器
        db_manager = DatabaseManager()
        
        # 獲取EPS歷史資料
        print(f"\n1. 獲取EPS歷史資料...")
        
        query = """
        SELECT date, value as eps
        FROM financial_statements
        WHERE stock_id = ? AND type = 'EPS'
        ORDER BY date DESC
        LIMIT 10
        """
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (stock_id,))
            eps_results = cursor.fetchall()
            
            if eps_results:
                print(f"   最新10筆EPS資料:")
                for i, (date, eps) in enumerate(eps_results):
                    print(f"     {i+1}. {date}: {eps}")
                
                # 分析2024-Q4的情況
                print(f"\n2. 分析2024-Q4的成長率計算...")
                
                # 找到相關的EPS資料
                eps_2024_q4 = None  # 2024-12-31
                eps_2024_q3 = None  # 2024-09-30 (前一季)
                eps_2023_q4 = None  # 2023-12-31 (去年同期)
                
                for date, eps in eps_results:
                    if date == '2024-12-31':
                        eps_2024_q4 = eps
                    elif date == '2024-09-30':
                        eps_2024_q3 = eps
                    elif date == '2023-12-31':
                        eps_2023_q4 = eps
                
                print(f"   關鍵EPS資料:")
                print(f"     2023-Q4 (去年同期): {eps_2023_q4}")
                print(f"     2024-Q3 (前一季): {eps_2024_q3}")
                print(f"     2024-Q4 (目標期): {eps_2024_q4}")
                
                if eps_2024_q4 and eps_2024_q3 and eps_2023_q4:
                    # 計算不同基準的成長率
                    print(f"\n3. 計算不同基準的成長率...")
                    
                    # QoQ成長率 (季對季)
                    qoq_growth = (eps_2024_q4 - eps_2024_q3) / abs(eps_2024_q3)
                    print(f"   QoQ成長率 (vs前一季): {qoq_growth*100:.1f}%")
                    print(f"     計算: ({eps_2024_q4} - {eps_2024_q3}) / {eps_2024_q3} = {qoq_growth:.3f}")
                    
                    # YoY成長率 (年對年)
                    yoy_growth = (eps_2024_q4 - eps_2023_q4) / abs(eps_2023_q4)
                    print(f"   YoY成長率 (vs去年同期): {yoy_growth*100:.1f}%")
                    print(f"     計算: ({eps_2024_q4} - {eps_2023_q4}) / {eps_2023_q4} = {yoy_growth:.3f}")
                    
                    print(f"\n4. 對比回測結果...")
                    print(f"   回測顯示:")
                    print(f"     預測成長率: 9.3%")
                    print(f"     實際成長率: 10.1%")
                    print(f"     預測EPS: 6.04")
                    print(f"     實際EPS: 11.64")
                    
                    print(f"\n5. 分析問題...")
                    
                    # 檢查哪個成長率接近回測結果
                    if abs(yoy_growth * 100 - 10.1) < abs(qoq_growth * 100 - 10.1):
                        print(f"   ✅ 實際成長率10.1%接近YoY成長率{yoy_growth*100:.1f}%")
                        print(f"   ❌ 這表示實際成長率使用YoY計算")
                    else:
                        print(f"   ✅ 實際成長率10.1%接近QoQ成長率{qoq_growth*100:.1f}%")
                        print(f"   ❌ 這表示實際成長率使用QoQ計算")
                    
                    # 檢查預測EPS的計算基準
                    if eps_2024_q3:
                        predicted_eps_qoq = eps_2024_q3 * (1 + 0.093)  # 基於前一季
                        print(f"\n   如果預測基於前一季 (QoQ):")
                        print(f"     預測EPS = {eps_2024_q3} × (1 + 0.093) = {predicted_eps_qoq:.2f}")
                        print(f"     與實際預測6.04的差距: {abs(predicted_eps_qoq - 6.04):.2f}")
                    
                    if eps_2023_q4:
                        predicted_eps_yoy = eps_2023_q4 * (1 + 0.093)  # 基於去年同期
                        print(f"\n   如果預測基於去年同期 (YoY):")
                        print(f"     預測EPS = {eps_2023_q4} × (1 + 0.093) = {predicted_eps_yoy:.2f}")
                        print(f"     與實際預測6.04的差距: {abs(predicted_eps_yoy - 6.04):.2f}")
                    
                    print(f"\n6. 結論...")
                    print(f"   問題根源: 預測和實際使用了不同的成長率計算基準")
                    print(f"   預測可能使用: QoQ (季對季)")
                    print(f"   實際使用: YoY (年對年)")
                    print(f"   這導致成長率看似準確，但EPS數值差異巨大")
                
            else:
                print(f"   ❌ 沒有找到EPS資料")
        
        print(f"\n" + "="*60)
        
    except Exception as e:
        print(f"❌ 調試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_growth_rate()

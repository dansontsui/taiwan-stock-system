#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試增強版股票報告生成器
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_report_generator():
    """測試報告生成器"""
    print("🧪 測試增強版股票報告生成器")
    print("=" * 60)
    
    try:
        from generate_stock_report import StockReportGenerator
        
        # 測試股票代號（使用資料庫中存在的股票）
        test_stocks = ['2330', '2454', '2317', '1301', '2412']
        
        for stock_id in test_stocks:
            print(f"\n📊 測試股票: {stock_id}")
            print("-" * 40)
            
            try:
                # 創建報告生成器
                generator = StockReportGenerator(stock_id)
                
                # 驗證股票代號
                is_valid, message = generator.validate_stock_id()
                if not is_valid:
                    print(f"❌ {message}")
                    continue
                
                print(f"✅ 股票代號驗證成功")
                
                # 測試各個資料收集函數
                print("🔍 測試資料收集功能...")
                
                # 基本資訊
                basic_info = generator.get_basic_info()
                print(f"   📋 基本資訊: {'✅' if basic_info else '❌'}")
                
                # 月營收
                monthly_revenue = generator.get_monthly_revenue()
                print(f"   📊 月營收: {'✅' if not monthly_revenue.empty else '❌'} ({len(monthly_revenue)} 筆)")
                
                # 季度財務
                quarterly_financials = generator.get_quarterly_financials()
                print(f"   📋 季度財務: {'✅' if not quarterly_financials.empty else '❌'} ({len(quarterly_financials)} 筆)")
                
                # 年度財務
                annual_financials = generator.get_annual_financials()
                print(f"   📈 年度財務: {'✅' if not annual_financials.empty else '❌'} ({len(annual_financials)} 筆)")
                
                # 股利政策
                dividend_policy = generator.get_dividend_policy()
                print(f"   💎 股利政策: {'✅' if not dividend_policy.empty else '❌'} ({len(dividend_policy)} 筆)")
                
                # 現金流量 (新增)
                cash_flow_data = generator.get_cash_flow_data()
                print(f"   💰 現金流量: {'✅' if not cash_flow_data.empty else '❌'} ({len(cash_flow_data)} 筆)")
                
                # 除權除息結果 (新增)
                dividend_results = generator.get_dividend_results()
                print(f"   🎯 除權除息結果: {'✅' if not dividend_results.empty else '❌'} ({len(dividend_results)} 筆)")
                
                # 股價分析 (新增)
                stock_price_analysis = generator.get_stock_price_analysis()
                print(f"   📈 股價分析: {'✅' if stock_price_analysis else '❌'}")
                
                # 財務比率 (新增)
                financial_ratios = generator.get_financial_ratios_analysis()
                print(f"   📊 財務比率: {'✅' if not financial_ratios.empty else '❌'} ({len(financial_ratios)} 筆)")
                
                # 潛力分析
                potential_analysis = generator.get_potential_analysis()
                print(f"   🧠 潛力分析: {'✅' if potential_analysis else '❌'}")
                
                print(f"✅ {stock_id} 資料收集測試完成")
                
                # 只對第一個股票生成完整報告
                if stock_id == test_stocks[0]:
                    print(f"\n📄 生成 {stock_id} 的完整Excel報告...")
                    success = generator.generate_excel_report()
                    if success:
                        print(f"✅ Excel報告生成成功")
                    else:
                        print(f"❌ Excel報告生成失敗")
                
            except Exception as e:
                print(f"❌ 測試 {stock_id} 時發生錯誤: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("🎯 測試完成")
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        print("請確認 generate_stock_report.py 檔案存在且可正常導入")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def show_report_features():
    """顯示報告功能特色"""
    print("\n📊 增強版股票報告生成器功能")
    print("=" * 60)
    print("📋 Excel工作表 (10個):")
    print("   1. 📋 基本資訊 - 股票基本資料、最新股價、財務比率")
    print("   2. 📊 月營收 - 近24個月營收資料及成長率")
    print("   3. 📋 季度財務 - 近8季綜合損益表資料")
    print("   4. 📈 年度財務 - 近5年財務比率分析")
    print("   5. 💎 股利政策 - 近5年股利發放記錄")
    print("   6. 💰 現金流量 - 近8季現金流量分析 (NEW!)")
    print("   7. 🎯 除權除息結果 - 近5年除權息表現 (NEW!)")
    print("   8. 📈 股價分析 - 技術分析指標 (NEW!)")
    print("   9. 📊 財務比率 - 詳細財務比率分析 (NEW!)")
    print("  10. 🧠 潛力分析 - 系統評分和建議")
    
    print("\n🎯 新增功能亮點:")
    print("   ✅ 現金流量品質分析")
    print("   ✅ 填權息表現追蹤")
    print("   ✅ 52週股價區間分析")
    print("   ✅ 股價波動率計算")
    print("   ✅ 流動性比率分析")
    print("   ✅ 自由現金流計算")
    
    print("\n💡 使用方式:")
    print("   python generate_stock_report.py 2330")
    print("   python generate_stock_report.py --stock-id 2454")

def main():
    """主函數"""
    print("🚀 股票報告生成器測試工具")
    print("=" * 60)
    
    # 顯示功能特色
    show_report_features()
    
    # 詢問是否執行測試
    print("\n" + "=" * 60)
    choice = input("是否要執行完整測試？(y/N): ").strip().lower()
    
    if choice == 'y':
        test_report_generator()
    else:
        print("測試已取消")
        print("\n💡 您可以直接使用以下命令生成報告:")
        print("python generate_stock_report.py 2330")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
比較兩個交易記錄檔案
"""

import pandas as pd
import sys
from pathlib import Path

def compare_trade_files():
    """比較兩個交易記錄檔案"""
    
    # 檔案路徑
    file1 = 'stock_price_investment_system/results/holdout/holdout_202503_202505_020_k7_MF_0827152822/holdout_trades_20250827_152822.csv'
    file2 = 'stock_price_investment_system/results/holdout/holdout_202503_202505_020_k7_MF_0827154256/holdout_trades_20250827_154256.csv'
    
    try:
        # 讀取兩個檔案
        df1 = pd.read_csv(file1, encoding='utf-8-sig')
        df2 = pd.read_csv(file2, encoding='utf-8-sig')
        
        print('📊 檔案比較結果:')
        print(f'檔案1 (152822): {len(df1)} 筆交易')
        print(f'檔案2 (154256): {len(df2)} 筆交易')
        print()
        
        # 檢查檔案是否完全相同
        if df1.equals(df2):
            print('✅ 兩個檔案完全相同！')
            print('💡 這表示選項5b的停損停利驗證可能沒有正確執行')
            return
        
        # 比較關鍵欄位
        key_columns = ['stock_id', 'actual_return', 'actual_return_net', 'max_return_20d', 'min_return_20d']
        
        print('🔍 關鍵欄位比較:')
        for col in key_columns:
            if col in df1.columns and col in df2.columns:
                diff_count = (df1[col] != df2[col]).sum()
                print(f'   {col}: {diff_count} 筆不同')
                
                if diff_count > 0:
                    print(f'      檔案1範圍: {df1[col].min():.4f} ~ {df1[col].max():.4f}')
                    print(f'      檔案2範圍: {df2[col].min():.4f} ~ {df2[col].max():.4f}')
            else:
                print(f'   {col}: 欄位不存在')
        
        print()
        
        # 比較第一筆交易
        if len(df1) > 0 and len(df2) > 0:
            print('📈 第一筆交易詳細比較:')
            print('檔案1 (原始回測):')
            print(f'   股票: {df1.iloc[0]["stock_id"]}')
            print(f'   實際報酬: {df1.iloc[0]["actual_return"]:.4f}')
            print(f'   最大報酬: {df1.iloc[0]["max_return_20d"]:.4f}')
            print(f'   最小報酬: {df1.iloc[0]["min_return_20d"]:.4f}')
            print()
            print('檔案2 (停損停利回測):')
            print(f'   股票: {df2.iloc[0]["stock_id"]}')
            print(f'   實際報酬: {df2.iloc[0]["actual_return"]:.4f}')
            print(f'   最大報酬: {df2.iloc[0]["max_return_20d"]:.4f}')
            print(f'   最小報酬: {df2.iloc[0]["min_return_20d"]:.4f}')
            
            # 檢查是否應該觸發停損停利
            max_return = df1.iloc[0]["max_return_20d"]
            min_return = df1.iloc[0]["min_return_20d"]
            
            print()
            print('🎯 停損停利分析 (2%停損/10%停利):')
            if max_return >= 0.10:
                print(f'   ✅ 應觸發停利: 最大報酬 {max_return:.2%} >= 10%')
            elif min_return <= -0.02:
                print(f'   ✅ 應觸發停損: 最小報酬 {min_return:.2%} <= -2%')
            else:
                print(f'   ⏰ 應正常到期: 最大 {max_return:.2%}, 最小 {min_return:.2%}')
        
        # 檢查是否有新的欄位
        print()
        print('🔍 欄位差異:')
        cols1 = set(df1.columns)
        cols2 = set(df2.columns)
        
        only_in_1 = cols1 - cols2
        only_in_2 = cols2 - cols1
        
        if only_in_1:
            print(f'   只在檔案1: {list(only_in_1)}')
        if only_in_2:
            print(f'   只在檔案2: {list(only_in_2)}')
        if not only_in_1 and not only_in_2:
            print('   ✅ 兩個檔案的欄位完全相同')
            
    except Exception as e:
        print(f'❌ 比較失敗: {e}')
        import traceback
        traceback.print_exc()

def check_monthly_reports():
    """檢查每月報告是否包含20日最大最小報酬"""
    
    print('\n📄 檢查每月報告格式:')
    
    # 檢查一個每月報告檔案
    monthly_file = 'stock_price_investment_system/results/holdout/holdout_202503_202505_020_k7_MF_0827152822/holdout_monthly_20250827_152822_202503.csv'
    
    try:
        # 讀取每月報告
        with open(monthly_file, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        print(f'📊 每月報告內容預覽:')
        for i, line in enumerate(lines[:15], 1):
            print(f'   {i:2d}: {line.strip()}')
        
        # 檢查是否包含20日最大最小報酬
        content = ''.join(lines)
        if '20日最大報酬' in content:
            print('✅ 每月報告已包含"20日最大報酬"欄位')
        else:
            print('❌ 每月報告缺少"20日最大報酬"欄位')
            
        if '20日最小報酬' in content:
            print('✅ 每月報告已包含"20日最小報酬"欄位')
        else:
            print('❌ 每月報告缺少"20日最小報酬"欄位')
            
    except Exception as e:
        print(f'❌ 檢查每月報告失敗: {e}')

def main():
    """主函數"""
    print('🔍 交易記錄檔案比較分析')
    print('=' * 50)
    
    compare_trade_files()
    check_monthly_reports()
    
    print('\n💡 問題診斷:')
    print('1. 如果兩個交易記錄檔案完全相同，表示選項5b沒有正確應用停損停利')
    print('2. 如果每月報告缺少20日最大最小報酬，需要更新報告格式')
    print('3. 檢查停損停利邏輯是否正確觸發')

if __name__ == "__main__":
    main()

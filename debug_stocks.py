import sqlite3
import pandas as pd

conn = sqlite3.connect('data/taiwan_stock.db')

# 檢查 stocks 表中是否有 1101 這些股票
test_ids = ['1101', '1102', '1103']
print("=== 檢查特定股票 ===")
for stock_id in test_ids:
    result = pd.read_sql_query('SELECT stock_id, stock_name, industry FROM stocks WHERE stock_id = ?', conn, params=[stock_id])
    print(f'股票 {stock_id}: {len(result)} 筆')
    if not result.empty:
        print(f'  名稱: {result.iloc[0]["stock_name"]}')
        print(f'  產業: {result.iloc[0]["industry"]}')

print("\n=== stocks 表樣本 ===")
sample = pd.read_sql_query('SELECT stock_id, stock_name, industry FROM stocks WHERE stock_id LIKE "11%" LIMIT 5', conn)
print(sample)

print(f"\n=== stock_id 型別 ===")
print(f'stock_id dtype: {sample["stock_id"].dtype}')

conn.close()

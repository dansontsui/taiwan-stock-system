# -*- coding: utf-8 -*-
"""
修正run_monthly_investment方法的縮排問題
"""

def fix_indentation():
    """修正縮排問題"""
    
    file_path = "stock_price_investment_system/price_models/holdout_backtester.py"
    
    # 讀取檔案
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到run_monthly_investment方法的開始和結束
    start_line = None
    end_line = None
    
    for i, line in enumerate(lines):
        if 'def run_monthly_investment(' in line:
            start_line = i
        elif start_line is not None and line.strip().startswith('def ') and i > start_line:
            end_line = i
            break
        elif start_line is not None and line.strip().startswith('except Exception as e:') and 'run_monthly_investment' in ''.join(lines[i:i+5]):
            # 找到except語句的結束
            for j in range(i, len(lines)):
                if lines[j].strip() == '' and j > i + 5:
                    end_line = j
                    break
            break
    
    if start_line is None:
        print("❌ 找不到run_monthly_investment方法")
        return
    
    if end_line is None:
        end_line = len(lines)
    
    print(f"📍 找到方法範圍: 第{start_line+1}行 到 第{end_line}行")
    
    # 修正縮排
    fixed_lines = lines[:start_line+1]  # 保留方法定義行
    
    # 處理方法內容
    in_try_block = False
    for i in range(start_line+1, end_line):
        line = lines[i]
        
        if 'try:' in line and not line.strip().startswith('#'):
            in_try_block = True
            fixed_lines.append(line)
        elif 'except Exception as e:' in line:
            in_try_block = False
            fixed_lines.append(line)
        elif in_try_block and line.strip() and not line.startswith('        '):
            # 在try塊內，但縮排不正確
            if line.startswith('    '):
                # 已經有4個空格，再加4個
                fixed_lines.append('    ' + line)
            else:
                # 沒有縮排，加8個空格
                fixed_lines.append('        ' + line.lstrip())
        else:
            fixed_lines.append(line)
    
    # 添加剩餘的行
    fixed_lines.extend(lines[end_line:])
    
    # 寫回檔案
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ 縮排修正完成")

if __name__ == "__main__":
    fix_indentation()

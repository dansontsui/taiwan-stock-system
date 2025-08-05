#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
編碼輔助模組 - 提供統一的 subprocess 編碼處理
"""

import subprocess
import sys
import os

# 設置環境編碼
os.environ['PYTHONIOENCODING'] = 'utf-8'

def safe_subprocess_run(*args, **kwargs):
    """安全的 subprocess.run，自動處理編碼問題"""
    # 設置預設編碼參數
    if 'text' in kwargs and kwargs['text']:
        kwargs.setdefault('encoding', 'utf-8')
        kwargs.setdefault('errors', 'replace')
    
    return subprocess.run(*args, **kwargs)

def safe_subprocess_popen(*args, **kwargs):
    """安全的 subprocess.Popen，自動處理編碼問題"""
    # 設置預設編碼參數
    if kwargs.get('text') or kwargs.get('universal_newlines'):
        kwargs.setdefault('encoding', 'utf-8')
        kwargs.setdefault('errors', 'replace')
    
    return subprocess.Popen(*args, **kwargs)

# 向後兼容的別名
run = safe_subprocess_run
Popen = safe_subprocess_popen

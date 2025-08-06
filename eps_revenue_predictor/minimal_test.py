#!/usr/bin/env python3
# -*- coding: ascii -*-

import sys
from pathlib import Path

print("Minimal test starting...")

# Add project path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print(f"Current dir: {current_dir}")

try:
    print("Testing config import...")
    from config.settings import DATABASE_CONFIG
    print("Config imported successfully")
    print(f"DB path: {DATABASE_CONFIG['path']}")
    
except Exception as e:
    print(f"Config import failed: {e}")
    import traceback
    traceback.print_exc()

print("Minimal test completed")

#!/usr/bin/env python3
# -*- coding: ascii -*-
"""
Create a quick candidate pool JSON filtered by specific stock_ids.
This script avoids non-ASCII output to prevent cp950 encoding issues.
"""

import json
from pathlib import Path

SRC = Path('stock_price_investment_system/results/candidate_pools/candidate_pool_20250827_132845.json')
DST = Path('stock_price_investment_system/results/candidate_pools/candidate_pool_quick_8067_8279_2442.json')
KEEP = {'8067', '8279', '2442'}

def main():
    if not SRC.exists():
        print('ERROR: source file not found')
        return 1

    raw = SRC.read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    text = raw.decode('utf-8', errors='strict')

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data, _ = json.JSONDecoder().raw_decode(text)

    pool = data.get('candidate_pool', [])
    filtered = [c for c in pool if c.get('stock_id') in KEEP]

    out = {
        'success': True,
        'candidate_pool': filtered,
        'metadata': {
            'source': str(SRC),
            'kept_stocks': sorted(list(KEEP)),
            'total_candidates': len(filtered)
        }
    }

    DST.write_text(json.dumps(out, ensure_ascii=True, indent=2), encoding='ascii', newline='\n')
    print('OK: written', str(DST), 'count=', len(filtered))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

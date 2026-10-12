#!/usr/bin/env python3
"""Offline static re-scan of Idem.pattern (rev 2) for the 23 L2 assets with the CURRENT inspector's idem_scan (A.L2, INDEX section 1).

Static code analysis only (no DB): it reads the writer files on the checked-out main. The convention argument is any value other than
'upsert' (L2 is delete-then-insert).

Usage: python3 idem_remeasure.py <repo-root>
"""
import json, os, sys
root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
os.chdir(root + '/platform/scripts/governance')
sys.path.insert(0, '.')
import asset_census as ac
b = json.load(open(root + '/00_ARCHITECTURE/briefs/suvarna/layers/census/after_reader_grant/census_L2.json'))['L2']
for a in b['assets']:
    targets = [t for t in ([a['target_table']] + a['count_sql_tables']) if t]
    v, notes = ac.idem_scan(a['asset_id'], a['writer_files'], 'delete_insert', targets)
    print(a['asset_id'], v, '|', (notes[0] if notes else '')[:260])

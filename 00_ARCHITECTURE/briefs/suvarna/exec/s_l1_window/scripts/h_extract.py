#!/usr/bin/env python3
"""Extract every fenced ```sql block from the W7 read-back doc, keyed by its H-section (### H<n>...), in order.
usage: h_extract.py DOC OUTDIR -> OUTDIR/H<n>_<k>.sql (one SELECT each) + index.tsv"""
import re, sys, os
doc = open(sys.argv[1]).read(); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
sec = None; k = 0; idx = []
lines = doc.split('\n'); i = 0
while i < len(lines):
    m = re.match(r'^### (H\d+b?)\.', lines[i])
    if m: sec = m.group(1); k = 0
    if lines[i].strip() == '```sql' and sec:
        j = i + 1; buf = []
        while lines[j].strip() != '```': buf.append(lines[j]); j += 1
        k += 1; fn = f'{out}/{sec}_{k}.sql'
        open(fn, 'w').write('\n'.join(buf).strip().rstrip(';') + ';\n'); idx.append((sec, k, fn, len(buf)))
        i = j
    i += 1
open(f'{out}/index.tsv', 'w').write('\n'.join('\t'.join(map(str, r)) for r in idx) + '\n')
print(len(idx), 'sql blocks', sorted(set(r[0] for r in idx), key=lambda s: (int(re.sub(r'\D','',s)), s)))

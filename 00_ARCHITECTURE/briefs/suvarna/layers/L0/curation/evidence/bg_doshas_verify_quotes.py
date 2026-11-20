import json, subprocess, re, sys
L = json.load(open('ledger.json'))
cache = {}
def chunk(cid):
    if cid not in cache:
        out = subprocess.run(['/Users/Dev/suvarna-evidence/TrackI/ifl0/rq.sh', f"select content_en from classical_text_chunks where chunk_id='{cid}'"], capture_output=True, text=True).stdout
        cache[cid] = re.sub(r'\s+', ' ', out)
    return cache[cid]
def norm(s): return re.sub(r'\s+', ' ', s).strip()
bad = 0
for o in L:
    ents = list(o['corpus']) + [dict(chunk_id=c['chunk_id'], quote=c['note'], quote_is_note=True) for c in o.get('undecided_candidates', [])]
    for c in o['corpus']:
        q = norm(c['quote']); t = chunk(c['chunk_id'])
        n = len(q.split())
        ok = q in t
        if n > 15 or not ok:
            bad += 1
            print(o['row_key']['canonical_id'], c['chunk_id'], 'words', n, 'found', ok, '|', q)
    for c in o.get('undecided_candidates', []):
        t = chunk(c['chunk_id'])
        if len(t) < 5:
            bad += 1; print('MISSING CHUNK', o['row_key']['canonical_id'], c['chunk_id'])
print('bad', bad, 'chunks fetched', len(cache))

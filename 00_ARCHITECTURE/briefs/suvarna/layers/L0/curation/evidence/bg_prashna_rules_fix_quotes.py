import json, subprocess, re, difflib
rows = json.load(open('ledger.json', encoding='utf-8'))
raw = {}
def rawchunk(cid):
    if cid not in raw:
        out = subprocess.run(['/Users/Dev/suvarna-evidence/TrackI/ifl0/rq.sh',
            "select content_en from classical_text_chunks where chunk_id='%s'" % cid],
            capture_output=True, text=True, timeout=100).stdout
        raw[cid] = out.split('\n', 1)[1].rstrip('\n') if '\n' in out else ''
    return raw[cid]
def norm_map(t):
    chars, idx = [], []
    for i, ch in enumerate(t):
        if not ch.isspace() and ch != '‌':
            chars.append(ch); idx.append(i)
    return ''.join(chars), idx
def best_slice(t, q):
    nt, idx = norm_map(t)
    nq = re.sub(r'\s+', '', q).replace('‌', '')
    L = len(nq)
    best = (0, 0, 0)
    sm = difflib.SequenceMatcher(None, nq, '')
    for start in range(0, max(1, len(nt) - L + 1)):
        for w in (L - 2, L, L + 2):
            if w <= 0: continue
            seg = nt[start:start + w]
            sm.set_seq2(seg)
            r = sm.ratio()
            if r > best[0]:
                best = (r, start, start + w)
    r, s, e = best
    return r, t[idx[s]: idx[e - 1] + 1] if e - 1 < len(idx) else t[idx[s]:]
changed = 0
for r in rows:
    for c in r['corpus']:
        t = rawchunk(c['chunk_id'])
        nt = re.sub(r'\s+', '', t).replace('‌', '')
        parts = [p for p in re.split(r'\.\.\.|…', c['quote']) if p.strip()]
        ok = all(re.sub(r'\s+', '', p.strip(' .;,')).replace('‌','') in nt for p in parts)
        if ok: continue
        newparts = []
        for p in parts:
            pp = p.strip(' .;,')
            if re.sub(r'\s+', '', pp).replace('‌','') in nt:
                newparts.append(pp); continue
            ratio, sl = best_slice(t, pp)
            newparts.append(re.sub(r'\s+', ' ', sl).strip())
            print('FIX %.2f %s | %s -> %s' % (ratio, c['chunk_id'], pp, newparts[-1]))
        c['quote'] = ' ... '.join(newparts)
        changed += 1
json.dump(rows, open('ledger.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('changed', changed)

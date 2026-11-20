import re, json, subprocess, os
BASE = '/private/tmp/claude-504/scratch/curation/bg_reference_B'
RQ = '/Users/Dev/suvarna-evidence/TrackI/ifl0/rq.sh'
CACHE_F = BASE + '/chunk_cache.json'
SRC = {
    'bphs': 'Santhanam trans.',
    'bphs_jaimini': 'Suryanarain Rao trans. 1949',
    'hora_sara': 'Santhanam trans.',
    'phaladeepika': 'Sastri trans. 1950',
    'jataka_parijata': 'Subramanya Shashtri trans. 1932-33',
    'saravali': 'Santhanam trans.',
}
SHORT = {'bphs': 'BPHS', 'bphs_jaimini': 'Jaimini Sutras', 'hora_sara': 'Hora Sara',
         'phaladeepika': 'Phaladeepika', 'jataka_parijata': 'Jataka Parijata', 'saravali': 'Saravali'}

def rq(sql):
    r = subprocess.run([RQ, sql], capture_output=True, text=True, timeout=110)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:400])
    return r.stdout

def norm(s):
    return re.sub(r'\s+', ' ', s).strip().lower()

_cache = None
def cache():
    global _cache
    if _cache is None:
        _cache = json.load(open(CACHE_F)) if os.path.exists(CACHE_F) else {}
    return _cache

def fetch(chunk_ids):
    c = cache()
    need = [x for x in chunk_ids if x not in c]
    for i in range(0, len(need), 40):
        part = need[i:i+40]
        inl = ','.join("'%s'" % x for x in part)
        out = rq("select chunk_id, replace(replace(content_en,E'\\n',' '),E'\\r',' ') from classical_text_chunks where chunk_id in (%s)" % inl)
        for line in out.splitlines()[1:]:
            if line.startswith('(') and line.endswith('rows)') or line.startswith('(1 row'):
                continue
            if '|' not in line:
                continue
            cid, txt = line.split('|', 1)
            c[cid] = txt
    json.dump(c, open(CACHE_F, 'w'))
    return c

def textid_of(chunk_id):
    return re.sub(r'_pg\d+_c\d+$', '', chunk_id)

def page_of(chunk_id):
    m = re.search(r'_pg0*(\d+)_c0*(\d+)$', chunk_id)
    return 'PG%s' % m.group(1), 'C%s' % m.group(2)

def locator(chunk_id):
    t = textid_of(chunk_id)
    pg, c = page_of(chunk_id)
    return '%s:%s:%s' % (t, pg, c)

QUOTES = []   # (chunk_id, quote) to verify

def ev(chunk_id, quote, sloka=None):
    QUOTES.append((chunk_id, quote))
    pg, c = page_of(chunk_id)
    return {'text_id': textid_of(chunk_id), 'chunk_id': chunk_id, 'page': pg,
            'sloka_printed': sloka, 'quote': quote}

def cite(chunk_id, label, sloka=None, chapter=None):
    """house-style proposed citation"""
    t = textid_of(chunk_id)
    parts = [SHORT.get(t, t)]
    if chapter:
        parts.append(chapter)
    s = ', '.join(parts)
    if sloka:
        s += ', Sloka %s as printed' % sloka
    else:
        pg, _ = page_of(chunk_id)
        s += ', p.%s' % pg[2:]
    return '%s — %s (%s)' % (s, locator(chunk_id), SRC.get(t, ''))

def verify_all():
    ids = sorted({q[0] for q in QUOTES})
    c = fetch(ids)
    bad = []
    for cid, q in QUOTES:
        if cid not in c:
            bad.append((cid, q, 'CHUNK_MISSING'))
            continue
        if norm(q) not in norm(c[cid]):
            bad.append((cid, q, 'QUOTE_NOT_FOUND'))
        if len(q.split()) > 15:
            bad.append((cid, q, 'QUOTE_TOO_LONG %d' % len(q.split())))
    return bad

def row(asset, table, row_key, claim, current, state, support, corpus=None, inference=None,
        proposed=None, action='none', question=None, row_count=1, note=None, extra=None):
    d = {'asset': asset, 'table': table, 'row_key': row_key, 'row_count': row_count,
         'claim': claim, 'current_citation': current, 'state': state, 'support_class': support,
         'corpus': corpus or [], 'inference_step': inference, 'proposed_citation': proposed,
         'proposed_action': action, 'acharya_question': question}
    if note:
        d['note'] = note
    if extra:
        d.update(extra)
    return d

ASSET = 'bg_reference'

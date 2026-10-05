#!/usr/bin/env python3
"""A.L4 brief generator - shared helpers. Every number in a generated brief comes from (a) the read-only JSON receipts under
/Users/Dev/suvarna-evidence/A_L4/data (collected by collect.py / tables.py via suvarna_reader SELECTs), (b) the fresh/saved census JSON,
(c) the offline rollup JSON, or (d) a git log over the worktree. Authored prose cites file:line."""
import json, os, re, subprocess, collections
EV = '/Users/Dev/suvarna-evidence/A_L4'
WT = '/Users/Dev/suvarna-al4'
FRESH = '/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json'
SAVED = WT + '/00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json'
C = '482012f1-710e-4a25-994a-93821f5871aa'
BASE = '3de3f8b15'
PRODUCED = '2026-10-03'

TABLES = {
    'ph_nimitta': ['phala_anchors'], 'ph_muhurta': ['phala_muhurta'], 'ph_sodhana': ['phala_sodhana'],
    'ph_pratikara': ['phala_mitigation'], 'ph_suddha_sodhana': ['phala_suddha_sodhana'], 'ph_sankrama': ['phala_sankrama'],
    'ph_pramana': ['phala_pramana'], 'ph_phaladesa': ['phala_phaladesa'],
    'ph_rectification': ['phala_rectification', 'phala_rectification_best'],
}
WRITER = {
    'ph_nimitta': 'platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py',
    'ph_muhurta': 'platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py',
    'ph_sodhana': 'platform/python-sidecar/pipeline/orchestrator/writers/ph_sodhana.py',
    'ph_pratikara': 'platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py',
    'ph_suddha_sodhana': 'platform/python-sidecar/pipeline/orchestrator/writers/ph_suddha_sodhana.py',
    'ph_sankrama': 'platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py',
    'ph_pramana': 'platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py',
    'ph_phaladesa': 'platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py',
    'ph_rectification': 'platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py',
}
ENGINE = {a: f'platform/python-sidecar/services/{a}/engine.py' for a in WRITER}


def jl(p):
    return json.load(open(p))


def asset_data(a):
    d = jl(f'{EV}/data/{a}.json')
    d['tables'] = {t: jl(f'{EV}/data/table_{t}.json') for t in TABLES[a]}
    return d


_fresh = None
_saved = None
_roll = None


def fresh():
    global _fresh
    if _fresh is None:
        L = jl(FRESH)['L4']
        _fresh = {a['asset_id']: a for a in L['assets']}
        _fresh['_meta'] = {k: v for k, v in L.items() if k != 'assets'}
    return _fresh


def saved():
    global _saved
    if _saved is None:
        L = jl(SAVED)['L4']
        _saved = {a['asset_id']: a for a in L['assets']}
    return _saved


def roll():
    global _roll
    if _roll is None:
        _roll = jl(f'{EV}/rollup_L4.json')
    return _roll


def clip(s, n=420):
    s = re.sub(r'\s+', ' ', str(s)).strip()
    return s if len(s) <= n else s[: n - 1] + '…'


def esc(s):
    return str(s).replace('|', '\\|')


def census_section(a):
    f = fresh()[a]
    s = saved()[a]
    ms = f['measurements']
    rows = []
    passes = []
    order = ['Earn.build_record', 'Ldgr.source_presence', 'Idem.pattern', 'Null.schema_default', 'Null.blank_rows', 'Vocab.identity',
             'Narr.agree', 'Narr.checkable', 'Narr.fidelity_test', 'Narr.lint', 'Dens.served', 'Build.registered', 'Build.contract',
             'Build.target', 'Build.dag', 'Build.dep_liveness', 'Build.exercised', 'Build.completion', 'Build.count_integrity',
             'Build.history', 'Count.floor', 'Complete.depth', 'Complete.width', 'Reach.fields', 'Cost.baseline', 'Earn.service_state']
    for k in order:
        if k not in ms:
            continue
        m = ms[k]
        sv = s['measurements'].get(k, {}).get('v', '(absent in saved run)')
        if m['v'] == 'PASS':
            passes.append(k)
            continue
        flag = '' if sv == m['v'] else f' (saved 2026-09-30: {sv})'
        rows.append(f"| {k.split('.')[0]} | {k} | {m['v']}{flag} | {esc(clip(m['measured'], 520))} |")
    out = ['| gate | criterion | fresh verdict | measured (fresh census text) |', '|---|---|---|---|'] + rows
    out.append('')
    out.append('**PASS cells (compact):** ' + ', '.join(passes) + '.')
    r = roll()['runs']['fresh_2026-10-02_1e5781a']['rollup'][a]
    rs = roll()['runs']['saved_2026-09-30']['rollup'][a]
    gates = ['Ldgr', 'Idem', 'Earn', 'Null', 'Vocab', 'Carr', 'Narr', 'Dens', 'Build']
    out.append('')
    out.append('**Offline rollup** (main `asset_census.py` rollup rules at REGISTRY_REVISION %s applied to the FRESH census; N/A reads NO_DETECTOR while `NA_RULE_DECISIONS` is empty; this is not a re-measure and not a certification): ' % roll()['registry_revision']
               + ' · '.join(f"{g} {r[g]['v']}" for g in gates if g in r) + '.')
    out.append('Same rules over the SAVED 2026-09-30 census: ' + ' · '.join(f"{g} {rs[g]['v']}" for g in gates if g in rs) + '.')
    return '\n'.join(out)


def runs_line(d):
    rs = {(x['state'], x['disposition']): x for x in d['runs_summary']}
    parts = []
    for (st, disp), x in sorted(rs.items(), key=lambda kv: str(kv[0])):
        parts.append(f"{x['n']} {st}{'/' + disp if disp else ''}")
    return ', '.join(parts)


def post_build_commits(a):
    paths = [WRITER[a].rsplit('/', 1)[0] + '/' + os.path.basename(WRITER[a]) if not WRITER[a].endswith('__init__.py') else WRITER[a].rsplit('/', 1)[0], os.path.dirname(ENGINE[a])]
    r = subprocess.run(['git', '-C', WT, 'log', '--format=%h|%ad|%s', '--date=format:%Y-%m-%d', '--since=2026-08-13T01:17:00Z', '--'] + paths,
                       capture_output=True, text=True)
    return [l.split('|', 2) for l in r.stdout.strip().split('\n') if l]


def readers(a):
    files = []
    for t in TABLES[a] + [a]:
        p = f'{EV}/data/readers_{t}.txt'
        if os.path.exists(p):
            files += [l.strip() for l in open(p) if l.strip()]
    own = {WRITER[a], ENGINE[a]}
    out = sorted(set(f for f in files if f not in own and not f.startswith(WRITER[a].rsplit('/', 1)[0] + '/' + a) and f'services/{a}/' not in f))
    return out


def readers_md(a):
    fs = readers(a)
    groups = collections.OrderedDict([('L5 / other writers (python-sidecar pipeline/orchestrator/writers)', []), ('python-sidecar other', []),
                                      ('serving (platform-mcp/src)', []), ('retrieval + app (platform/src)', [])])
    for f in fs:
        if f.startswith('platform/python-sidecar/pipeline/orchestrator/writers/'):
            groups['L5 / other writers (python-sidecar pipeline/orchestrator/writers)'].append(f.rsplit('/', 1)[1])
        elif f.startswith('platform/python-sidecar'):
            groups['python-sidecar other'].append(f.replace('platform/python-sidecar/', ''))
        elif f.startswith('platform-mcp'):
            groups['serving (platform-mcp/src)'].append(f.replace('platform-mcp/src/', ''))
        else:
            groups['retrieval + app (platform/src)'].append(f.replace('platform/src/', ''))
    return '; '.join(f"{k}: {', '.join(v)}" for k, v in groups.items() if v) or '(none found)', len(fs)


def stored_vs_code(a):
    cs = post_build_commits(a)
    if not cs:
        return 'No commit touched the asset\'s writer or engine after the last build (2026-08-13T01:16Z).'
    return '; '.join(f"`{h}` {d} {clip(t, 110)}" for h, d, t in cs)


def md_table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    for r in rows:
        out.append('| ' + ' | '.join(esc(c) for c in r) + ' |')
    return '\n'.join(out)


TOK = {
    'W': WRITER['ph_nimitta'], 'E': ENGINE['ph_nimitta'],
    'WM': WRITER['ph_muhurta'], 'EM': ENGINE['ph_muhurta'],
    'WS': WRITER['ph_sodhana'], 'ES': ENGINE['ph_sodhana'],
    'WSS': WRITER['ph_suddha_sodhana'], 'ESS': ENGINE['ph_suddha_sodhana'],
    'WP': WRITER['ph_pratikara'], 'EP': ENGINE['ph_pratikara'],
    'WK': WRITER['ph_sankrama'], 'EK': ENGINE['ph_sankrama'],
    'WPR': WRITER['ph_pramana'], 'EPR': ENGINE['ph_pramana'],
    'WD': WRITER['ph_phaladesa'], 'ED': ENGINE['ph_phaladesa'],
    'WR': WRITER['ph_rectification'], 'ER': ENGINE['ph_rectification'],
}


def fixstr(s):
    s = re.sub(r"' \+ (\w+) \+ '", lambda m: '{' + m.group(1) + '}', s)
    def rep(m):
        k = m.group(1)
        return TOK.get(k, m.group(0))
    return re.sub(r'\{(\w+)\}', rep, s)


def fixall(o):
    if isinstance(o, str):
        return fixstr(o)
    if isinstance(o, list):
        return [fixall(x) for x in o]
    if isinstance(o, tuple):
        return tuple(fixall(x) for x in o)
    if isinstance(o, dict):
        return {k: fixall(v) for k, v in o.items()}
    return o

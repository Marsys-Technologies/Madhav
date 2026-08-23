#!/usr/bin/env python3
"""
NIRMĀṆA M0-T7 — DRAFT-but-served inventory + DAG edge audit.

READ-ONLY. Emits 00_ARCHITECTURE/control/DRAFT_INVENTORY.json (+ .md) and
DAG_AUDIT_v1_0.md. Issues no verdict and decides no disposition (charter G1 is
ADHIKĀRIN's). Every number here is re-derived by this script; none is inherited
from the plan's prose or from the M0-T1 census.

Four facts are kept APART on purpose (they are not the same claim):
  F1 registry_active   — the registry's claim about itself (is_active).
  F2 rows_exist        — the target table(s) actually hold rows (SELECT count(*)).
  F3 surface_references— a non-test serving-side source file issues a SQL read of
                         one of those tables.
  F4 caller_reachable  — that file is in the transitive import closure of a
                         caller-facing entrypoint (Next.js route.ts/page.tsx, the
                         MCP server.ts, the FastAPI main.py) AND, when it is a
                         retrieval CapabilityDescriptor, its descriptor is passed
                         to registerCapability() from a module in that closure.

F4 is module-level reachability plus registration. It does NOT prove a live HTTP
call succeeds, and it does not evaluate per-profile MCP allowlists.
"""
import json, re, pathlib, datetime, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT  = ROOT/'00_ARCHITECTURE/control'
NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'

# ── DB (read-only) ────────────────────────────────────────────────────────────
def db_url():
    for l in (ROOT/'platform/.env.local').read_text().splitlines():
        if l.startswith('DATABASE_URL='):
            return re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
    raise SystemExit('DATABASE_URL not found')

FROM = re.compile(r'\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)', re.I)
def tables_of(r):
    t = set()
    if r['target_table']: t.add(r['target_table'].lower())
    if r['count_sql']:    t |= {x.lower() for x in FROM.findall(re.sub(r'--[^\n]*', ' ', r['count_sql']))}
    if r['clear_tables']: t |= {x.lower() for x in r['clear_tables']}
    return t

def load_db():
    import psycopg
    reg, thr, counts = {}, [], {}
    with psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        c = conn.cursor(); c.execute("SET statement_timeout='60s'")
        c.execute("""SELECT asset_id,layer,layer_index,english_name,english_description,storage_type,
                     target_table,count_sql,target_floor,depends_on,clear_tables,scope,is_active,
                     asset_type,asset_kind,catalog_status,has_writer,has_substeps,service_health,
                     provides_apis,health_probe,last_invoked_at,last_selftest_at,selftest_detail,
                     integrity_check_sql,volume_explanation FROM asset_registry ORDER BY asset_id""")
        for r in c.fetchall(): reg[r['asset_id']] = r
        c.execute("""SELECT asset_id,state,count(*) n,max(last_built_at) last_built,
                     sum(rows_written) rows_written FROM asset_throughput GROUP BY 1,2 ORDER BY 1,2""")
        thr = c.fetchall()
        c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        real = {r['table_name'].lower() for r in c.fetchall()}
        c.execute("SELECT table_name FROM information_schema.views WHERE table_schema='public'")
        views = {r['table_name'].lower() for r in c.fetchall()}
        for a, r in reg.items():
            if r['catalog_status'] != 'DRAFT': continue
            rec = {'count_sql_native': None, 'count_sql_error': None, 'tables': {}}
            if r['count_sql']:
                try:
                    q = r['count_sql'].replace('%', '%%')
                    if '$1' in q: c.execute(q.replace('$1', '%s'), (NATIVE,)*q.count('$1'))
                    else:         c.execute(q)
                    row = c.fetchone()
                    rec['count_sql_native'] = int(list(row.values())[0]) if row else None
                except Exception as e:
                    rec['count_sql_error'] = str(e).splitlines()[0][:180]
            for t in sorted(tables_of(r)):
                e = {'exists': t in real, 'is_view': t in views, 'total_rows': None, 'native_rows': None}
                if t in real:
                    c.execute(f'SELECT count(*) n FROM "{t}"'); e['total_rows'] = c.fetchone()['n']
                    c.execute("""SELECT 1 FROM information_schema.columns WHERE table_schema='public'
                                 AND table_name=%s AND column_name='chart_id'""", (t,))
                    if c.fetchone():
                        c.execute(f'SELECT count(*) n FROM "{t}" WHERE chart_id=%s', (NATIVE,))
                        e['native_rows'] = c.fetchone()['n']
                rec['tables'][t] = e
            counts[a] = rec
    return reg, thr, counts

# ── source scan ───────────────────────────────────────────────────────────────
EXTS = {'.ts','.tsx','.js','.mjs','.py','.sql'}
SCAN_ROOTS = ['platform/src','platform-mcp/src','platform/python-sidecar','platform/scripts',
              'platform-mcp/scripts','platform/migrations']
def skip(p):
    parts=set(p.parts)
    return ('node_modules' in parts or 'venv' in parts or '__pycache__' in parts
            or 'dist' in parts or '_archive' in parts)
def is_test(p):
    parts=p.parts
    return ('__tests__' in parts or 'tests' in parts or 'test' in parts or '__mocks__' in parts
            or p.name.startswith('test_') or p.name.endswith(('.test.ts','.test.tsx','.spec.ts','_test.py'))
            or 'evals' in parts or 'verification' in parts)
WRITER_DIRS=('python-sidecar/ga_writers','python-sidecar/bodha_writers',
             'python-sidecar/pipeline/orchestrator/writers','python-sidecar/pipeline')
def classify(rel):
    if rel.startswith('platform/migrations/'): return 'migration'
    if rel.startswith(('platform/scripts/','platform-mcp/scripts/')): return 'script'
    if any(w in rel for w in WRITER_DIRS): return 'build_writer'
    if rel.startswith('platform/python-sidecar/'): return 'sidecar_serve'
    if rel.startswith('platform/src/app/api/'): return 'next_api'
    if rel.startswith('platform/src/app/'): return 'next_page'
    if rel.startswith('platform/src/lib/'): return 'platform_lib'
    if rel.startswith('platform/src/components/'): return 'ui_component'
    if rel.startswith('platform/src/'): return 'platform_other'
    if rel.startswith('platform-mcp/src/'): return 'mcp_tool'
    return 'other'
SERVE = {'next_api','next_page','platform_lib','ui_component','platform_other','mcp_tool','sidecar_serve'}

BLOCK=re.compile(r'/\*.*?\*/', re.S)
DOCSTR=re.compile(r'"""(?:.|\n)*?"""|\'\'\'(?:.|\n)*?\'\'\'')
def strip_comments(txt, suf):
    blank=lambda m: re.sub(r'[^\n]',' ',m.group(0))
    if suf in ('.ts','.tsx','.js','.mjs'):
        txt=BLOCK.sub(blank,txt)
        txt=re.sub(r'(?m)^(\s*)//[^\n]*', lambda m:m.group(1)+' '*(len(m.group(0))-len(m.group(1))), txt)
        txt=re.sub(r'(?m)\s//[^\n]*$', blank, txt)
    elif suf=='.py':
        txt=DOCSTR.sub(blank,txt); txt=re.sub(r'(?m)#[^\n]*',blank,txt)
    elif suf=='.sql':
        txt=BLOCK.sub(blank,txt); txt=re.sub(r'(?m)--[^\n]*',blank,txt)
    return txt

READ_CTX = re.compile(r'(?:\bFROM\b|\bJOIN\b|\.from\(\s*[\'"`])\s*$', re.I)
DEL_CTX  = re.compile(r'\bDELETE\s+FROM\s*$', re.I)
WRITE_CTX= re.compile(r'(?:\bINSERT\s+INTO\b|\bUPDATE\b|\bTRUNCATE\b|\bCREATE\s+(?:TABLE|INDEX|UNIQUE\s+INDEX|VIEW|MATERIALIZED\s+VIEW)?\b|\bALTER\s+TABLE\b|\bDROP\s+TABLE\b|\bON\s+CONFLICT\b|\bREFERENCES\b)[^;]{0,80}$', re.I)
DYN_SQL  = re.compile(r'(?:FROM|JOIN)\s*(?:\$\{|\{|"\s*\+|\'\s*\+|`\s*\+)', re.I)

def role(txt, m):
    pre = txt[max(0, m.start()-80):m.start()]
    if DEL_CTX.search(pre): return 'sql_write'
    if READ_CTX.search(pre): return 'sql_read'
    if WRITE_CTX.search(pre): return 'sql_write'
    return 'mention'

# ── TS import graph ───────────────────────────────────────────────────────────
def ts_graph():
    SRC={'platform':ROOT/'platform/src','mcp':ROOT/'platform-mcp/src'}
    tsx=['.ts','.tsx','.js','.mjs']
    files=[p for r in SRC.values() for p in r.rglob('*') if p.suffix in tsx and p.is_file() and not skip(p)]
    fs=set(files)
    IMP=re.compile(r"""(?:^|\n)\s*(?:import\s+(?:[^'"]*?\s+from\s+)?|export\s+(?:\*|\{[^}]*\})\s+from\s+)['"]([^'"]+)['"]""")
    DYN=re.compile(r"""import\(\s*['"]([^'"]+)['"]\s*\)""")
    def resolve(spec, frm):
        if spec.startswith('@/'): base=SRC['platform']/spec[2:]
        elif spec.startswith('.'): base=(frm.parent/spec).resolve()
        else: return None
        c=[]
        if base.suffix in ('.js','.mjs'):
            st=base.with_suffix(''); c+=[st.with_suffix(e) for e in tsx]
        c.append(base)
        if base.suffix=='': c+=[base.with_suffix(e) for e in tsx]
        c+=[base/('index'+e) for e in tsx]
        for x in c:
            if x in fs: return x
        return None
    g={}
    for p in files:
        t=p.read_text(encoding='utf-8',errors='ignore')
        g[p]={r for spec in set(IMP.findall(t))|set(DYN.findall(t)) if (r:=resolve(spec,p))}
    roots=set()
    for p in files:
        if is_test(p): continue
        rel=str(p.relative_to(ROOT))
        if '/app/' in rel and p.name in ('route.ts','route.tsx','page.tsx','page.ts','layout.tsx','default.tsx'):
            roots.add(p)
        if rel in ('platform-mcp/src/server.ts','platform/src/instrumentation.ts'): roots.add(p)
    rootof={}; allr=set()
    for r in sorted(roots):
        seen=set(); st=[r]
        while st:
            u=st.pop()
            for v in g.get(u,()):
                if v not in seen: seen.add(v); st.append(v)
        seen.add(r)
        for f in seen: rootof.setdefault(str(f.relative_to(ROOT)),set()).add(str(r.relative_to(ROOT)))
        allr|=seen
    return {str(f.relative_to(ROOT)) for f in allr}, {k:sorted(v) for k,v in rootof.items()}, len(files), len(roots)

def py_graph():
    import ast
    SC=ROOT/'platform/python-sidecar'
    files=[p for p in SC.rglob('*.py') if not skip(p)]
    fs=set(files)
    def m2p(mod, cur, level):
        c=[]
        if level:
            b=cur.parent
            for _ in range(level-1): b=b.parent
            b=b.joinpath(*(mod.split('.') if mod else []))
        else:
            b=SC.joinpath(*mod.split('.'))
        c+=[b.with_suffix('.py'), b/'__init__.py']
        return [x for x in c if x in fs]
    g={}
    for p in files:
        d=set()
        try: tree=ast.parse(p.read_text(encoding='utf-8',errors='ignore'))
        except Exception: g[p]=d; continue
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):
                for a in n.names: d.update(m2p(a.name,p,0))
            elif isinstance(n,ast.ImportFrom):
                base=n.module or ''
                d.update(m2p(base,p,n.level or 0))
                for a in n.names:
                    d.update(m2p((base+'.'+a.name) if base else a.name, p, n.level or 0))
        g[p]=d
    root=SC/'main.py'; seen={root}; st=[root]
    while st:
        u=st.pop()
        for v in g.get(u,()):
            if v not in seen: seen.add(v); st.append(v)
    return {str(f.relative_to(ROOT)) for f in seen}, len(files)

# ── capability registration map ───────────────────────────────────────────────
def cap_map(ts_reach):
    DESC=re.compile(r"export\s+const\s+(\w+)\s*:\s*CapabilityDescriptor\s*=\s*\{(.*?)\n\}", re.S)
    URI=re.compile(r"uri:\s*'([^']+)'"); NAME=re.compile(r"name:\s*'([^']+)'")
    REGCALL=re.compile(r"registerCapability\(\s*(\w+)\s*[,)]")
    caps={}; sites={}
    for p in (ROOT/'platform/src/lib').rglob('*.ts'):
        if is_test(p): continue
        rel=str(p.relative_to(ROOT)); t=p.read_text(encoding='utf-8',errors='ignore')
        for sym,body in DESC.findall(t):
            u=URI.search(body); n=NAME.search(body)
            caps[sym]={'file':rel,'uri':u.group(1) if u else None,'name':n.group(1) if n else None}
        for sym in REGCALL.findall(t): sites.setdefault(sym,[]).append(rel)
    byfile={}
    for sym,c in caps.items():
        c['symbol']=sym
        c['registered_in']=sites.get(sym,[])
        c['registered_from_reachable']=any(s in ts_reach for s in c['registered_in'])
        byfile.setdefault(c['file'],[]).append(c)
    return caps, byfile

DESC_DECL = re.compile(r"export\s+const\s+(\w+)\s*:\s*CapabilityDescriptor\s*=")
MCP_TOOL  = re.compile(r"registerTool\(\s*['\"]([a-z0-9_]+)['\"]|server\.tool\(\s*['\"]([a-z0-9_]+)['\"]|name:\s*['\"]([a-z0-9_]+)['\"]\s*,")

def owning_symbol(txt, pos):
    """Nearest preceding `export const X: CapabilityDescriptor =` before pos, or None."""
    best = None
    for m in DESC_DECL.finditer(txt):
        if m.start() < pos: best = m.group(1)
        else: break
    return best


def main():
    reg, thr, counts = load_db()
    ts_reach, rootof, n_ts, n_roots = ts_graph()
    py_reach, n_py = py_graph()
    caps, caps_by_file = cap_map(ts_reach)

    files=[]
    for r in SCAN_ROOTS:
        rp=ROOT/r
        if rp.exists(): files+=[p for p in rp.rglob('*') if p.is_file() and p.suffix in EXTS and not skip(p)]
    texts={}; dyn={}
    for p in files:
        try:
            t=strip_comments(p.read_text(encoding='utf-8',errors='ignore'), p.suffix)
            texts[p]=t; dyn[p]=bool(DYN_SQL.search(t))
        except Exception: pass

    def reach(rel):
        if rel.endswith(('.ts','.tsx','.js','.mjs')) and rel.startswith(('platform/src/','platform-mcp/src/')):
            return 'yes' if rel in ts_reach else 'no'
        if rel.startswith('platform/python-sidecar/') and rel.endswith('.py'):
            return 'yes' if rel in py_reach else 'no'
        return 'n/a'

    thr_by={}
    for r in thr: thr_by.setdefault(r['asset_id'],[]).append(r)

    rev={}
    for a,r in reg.items():
        for d in (r['depends_on'] or []): rev.setdefault(d,[]).append(a)

    draft=sorted(a for a,r in reg.items() if r['catalog_status']=='DRAFT')
    inv={}
    for a in draft:
        r=reg[a]; tbls=sorted(tables_of(r)); refs=[]
        for t in tbls:
            pat=re.compile(r'(?<![A-Za-z0-9_])'+re.escape(t)+r'(?![A-Za-z0-9_])')
            for p,txt in texts.items():
                occ=[(m,role(txt,m)) for m in pat.finditer(txt)]
                if not occ: continue
                rel=str(p.relative_to(ROOT))
                if is_test(p): cls='test'
                else: cls=classify(rel)
                roles=sorted({rl for _,rl in occ})
                if cls in SERVE and 'sql_read' not in roles and dyn.get(p):
                    roles.append('dynamic_sql_candidate')
                raw_lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
                capsyms = {c['symbol']: c for c in caps_by_file.get(rel, [])}
                ev = []
                for m, rl in occ:
                    if rl not in ('sql_read',) and 'dynamic_sql_candidate' not in roles: continue
                    ln = txt.count('\n', 0, m.start()) + 1
                    sym = owning_symbol(txt, m.start()) if capsyms else None
                    ev.append({'line': ln, 'role': rl, 'owning_symbol': sym,
                               'capability': ({k: capsyms[sym][k] for k in
                                               ('uri','name','registered_in','registered_from_reachable')}
                                              if sym in capsyms else None),
                               'text': raw_lines[ln-1].strip()[:200] if ln-1 < len(raw_lines) else ''})
                attributed = [e['capability'] for e in ev if e.get('capability')]
                refs.append({'table':t,'file':rel,'class':cls,'reachable':reach(rel),'roles':roles,
                             'lines':sorted({txt.count('\n',0,m.start())+1 for m,_ in occ})[:8],
                             'entrypoints':rootof.get(rel,[]),
                             'descriptors_in_file': sorted(capsyms),
                             'evidence': ev[:12],
                             'capabilities': attributed if attributed else
                                 ([{k:c[k] for k in ('symbol','uri','name','registered_in','registered_from_reachable')}
                                   for c in caps_by_file.get(rel,[])] if len(capsyms)==1 else [])})
        srv=[x for x in refs if x['class'] in SERVE and ('sql_read' in x['roles'] or 'dynamic_sql_candidate' in x['roles'])]
        srv_reach=[x for x in srv if x['reachable']=='yes']
        capnames=sorted({c['name'] for x in srv_reach for c in x['capabilities']
                         if c.get('registered_from_reachable') and c.get('name')})
        ambiguous=sorted({x['file'] for x in srv_reach
                          if not x['capabilities'] and x.get('descriptors_in_file')})
        cnt=counts.get(a,{})
        rows_native=cnt.get('count_sql_native')
        tot=sum(v['total_rows'] or 0 for v in cnt.get('tables',{}).values())
        f2 = ('yes' if (rows_native or 0) > 0 or tot > 0 else
              ('no' if tbls else 'n/a_no_table_declared'))
        f3 = 'yes' if srv else ('no' if tbls else 'n/a_no_table_declared')
        if srv_reach: f4='yes'
        elif srv: f4='no'
        elif not tbls: f4='UNKNOWN_no_table_to_trace'
        else: f4='no'
        inv[a]={
          'asset_id':a,'layer':r['layer'],'layer_index':r['layer_index'],'asset_kind':r['asset_kind'],
          'scope':r['scope'],'english_name':r['english_name'],
          'english_description':(r['english_description'] or '')[:400],
          'catalog_status':r['catalog_status'],
          'F1_registry_active':bool(r['is_active']),
          'F1_detail':{'is_active':r['is_active'],'has_writer':r['has_writer'],
                       'provides_apis':r['provides_apis'],'health_probe':r['health_probe'],
                       'service_health':r['service_health'],
                       'last_invoked_at':str(r['last_invoked_at']) if r['last_invoked_at'] else None,
                       'last_selftest_at':str(r['last_selftest_at']) if r['last_selftest_at'] else None,
                       'selftest_detail':r['selftest_detail']},
          'F2_rows_exist':f2,'F2_detail':{'count_sql':r['count_sql'],'count_sql_native':rows_native,
                       'count_sql_error':cnt.get('count_sql_error'),'tables':cnt.get('tables',{}),
                       'target_floor':r['target_floor']},
          'F3_surface_references':f3,
          'F4_caller_reachable':f4,
          'serving_surfaces':[{'file':x['file'],'class':x['class'],'roles':x['roles'],'lines':x['lines'],
                               'reachable':x['reachable'],'entrypoints':x['entrypoints'][:6],
                               'descriptors_in_file':x.get('descriptors_in_file',[]),
                               'evidence':x.get('evidence',[]),
                               'capabilities':x['capabilities']} for x in srv],
          'build_side_readers':[{'file':x['file'],'table':x['table'],'lines':x['lines']}
                                for x in refs if x['class']=='build_writer' and 'sql_read' in x['roles']
                                and not x['file'].endswith('/'+a+'.py')],
          'reachable_capability_names':capnames,
          'capability_attribution_ambiguous_files':ambiguous,
          'target_table':r['target_table'],'tables':tbls,
          'depends_on':sorted(r['depends_on'] or []),
          'depended_on_by':sorted(rev.get(a,[])),
          'depended_on_by_status':{d:reg[d]['catalog_status'] for d in sorted(rev.get(a,[]))},
          'throughput':[{'state':x['state'],'n':x['n'],'last_built':str(x['last_built']),
                         'rows_written':int(x['rows_written'] or 0)} for x in thr_by.get(a,[])],
          'integrity_check_sql':r['integrity_check_sql'],
          'volume_explanation':r['volume_explanation'],
          'all_refs':refs,
        }

    meta={'task':'M0-T7','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'git_head':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip(),
          'git_branch':subprocess.run(['git','rev-parse','--abbrev-ref','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip(),
          'native_chart':NATIVE,'database_access':'READ-ONLY (SELECT only, autocommit, statement_timeout 60s)',
          'credential_handling':'DATABASE_URL read from platform/.env.local; never emitted',
          'registry_rows':len(reg),'draft_count':len(draft),
          'ts_files_scanned':n_ts,'ts_entrypoint_roots':n_roots,'ts_reachable_files':len(ts_reach),
          'py_files_scanned':n_py,'py_reachable_from_main':len(py_reach),
          'capability_descriptors_found':len(caps)}
    json.dump({'_meta':meta,'assets':inv}, open(OUT/'DRAFT_INVENTORY.json','w'), indent=1, default=str)
    print('wrote DRAFT_INVENTORY.json —', len(draft), 'DRAFT assets')
    from collections import Counter
    print('F2', Counter(v['F2_rows_exist'] for v in inv.values()))
    print('F3', Counter(v['F3_surface_references'] for v in inv.values()))
    print('F4', Counter(v['F4_caller_reachable'] for v in inv.values()))

if __name__=='__main__':
    main()

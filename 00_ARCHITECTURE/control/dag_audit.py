#!/usr/bin/env python3
"""
NIRMĀṆA M0-T7 (B) — DAG edge audit.

READ-ONLY. Re-derives every number from the live registry, the seed file and the
writer sources. Emits 00_ARCHITECTURE/control/DAG_AUDIT.json. Issues no verdict.

Three questions:
  Q1 CURRENT assets whose depends_on names a DRAFT (or RETIRED / inactive) asset.
  Q2 Dangling edges — a depends_on entry naming an asset_id with no registry row.
     Checked in BOTH declaration surfaces: the live registry and
     platform/scripts/seed/asset_registry_seed.ts.
  Q3 Over-declaration — a declared edge A->B for which A's writer source shows no
     textual read of any table B produces. Reported as EVIDENCE STRENGTH, never as
     a verdict: the detector is a regex over source text and cannot see dynamic SQL,
     ORM access, or a read that happens inside a service package it did not resolve.
"""
import json, re, pathlib, datetime, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT  = ROOT/'00_ARCHITECTURE/control'
SC   = ROOT/'platform/python-sidecar'

def db_url():
    for l in (ROOT/'platform/.env.local').read_text().splitlines():
        if l.startswith('DATABASE_URL='):
            return re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
    raise SystemExit('DATABASE_URL not found')

FROM = re.compile(r'\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)', re.I)
def tables_of(r):
    t=set()
    if r['target_table']: t.add(r['target_table'].lower())
    if r['count_sql']:    t |= {x.lower() for x in FROM.findall(re.sub(r'--[^\n]*',' ',r['count_sql']))}
    if r['clear_tables']: t |= {x.lower() for x in r['clear_tables']}
    return t

def load_registry():
    import psycopg
    with psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        c=conn.cursor(); c.execute("SET statement_timeout='45s'")
        c.execute("""SELECT asset_id,layer,layer_index,catalog_status,is_active,asset_kind,scope,
                     target_table,count_sql,clear_tables,depends_on,has_writer
                     FROM asset_registry ORDER BY asset_id""")
        return {r['asset_id']: r for r in c.fetchall()}

# ── seed file edges ───────────────────────────────────────────────────────────
def seed_edges():
    """Parse depends_on out of the seed .ts.

    Deliberately does NOT strip /* */ block comments: the file contains prose
    strings holding glob patterns like `gochara_intensity/*`, and a naive block
    strip swallows 53 real entries between two such strings. Only line comments
    and jsdoc continuation lines are removed. `asset_id:` is matched with a
    left boundary so `upstream_asset_id:` / `downstream_asset_id:` in the
    CoefficientDef block are not counted as asset entries.
    """
    p = ROOT/'platform/scripts/seed/asset_registry_seed.ts'
    txt = p.read_text(encoding='utf-8', errors='ignore')
    txt = re.sub(r'(?m)^\s*//[^\n]*', ' ', txt)
    txt = re.sub(r'(?m)^\s*\*[^\n]*', ' ', txt)
    ms = list(re.finditer(r"(?<![A-Za-z_])asset_id:\s*'([a-z0-9_]+)'", txt))
    edges = []
    for i, m in enumerate(ms):
        end = ms[i+1].start() if i+1 < len(ms) else len(txt)
        seg = txt[m.end():end]
        d = re.search(r"depends_on:\s*\[([^\]]*)\]", seg)
        if d:
            for dep in re.findall(r"'([a-z0-9_.]+)'", d.group(1)):
                edges.append((m.group(1), dep))
    coeff = [(m.group(1), m.group(2)) for m in re.finditer(
        r"upstream_asset_id:\s*'([a-z0-9_]+)'[^}]*?downstream_asset_id:\s*'([a-z0-9_]+)'", txt, re.S)]
    return edges, sorted({m.group(1) for m in ms}), coeff

# ── writer sources ────────────────────────────────────────────────────────────
REGRE  = re.compile(r"@register\(\s*['\"]([a-z0-9_.]+)['\"]")
REGVAR = re.compile(r"@register\(\s*([A-Z_][A-Z0-9_]*)\s*\)")
IMP    = re.compile(r'(?m)^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))')

def writer_index():
    roots=[SC/'ga_writers', SC/'bodha_writers', SC/'pipeline'/'orchestrator'/'writers',
           SC/'services', SC/'brahmagyan']
    files=[p for r in roots if r.exists() for p in r.rglob('*.py')
           if '__pycache__' not in p.parts and 'venv' not in p.parts
           and not p.name.startswith('test_') and 'tests' not in p.parts]
    texts={p:p.read_text(encoding='utf-8',errors='ignore') for p in files}
    w={}
    for p,t in texts.items():
        aids=set(REGRE.findall(t))
        for var in REGVAR.findall(t):
            m=re.search(r"(?m)^"+re.escape(var)+r"\s*=\s*['\"]([a-z0-9_]+)['\"]", t)
            if m: aids.add(m.group(1))
        for a in aids: w.setdefault(a,[]).append(p)
    return w, texts

def universe(aid, writer_of, texts):
    files=set(writer_of.get(aid,[]))
    for f in list(files):
        for m in IMP.finditer(texts[f]):
            mod=(m.group(1) or m.group(2) or '')
            parts=mod.split('.')
            for base in (SC, f.parent):
                cand=base.joinpath(*parts)
                for c in (cand.with_suffix('.py'), cand/'__init__.py'):
                    if c in texts: files.add(c)
                if cand.is_dir():
                    for q in cand.rglob('*.py'):
                        if q in texts: files.add(q)
    return files

def main():
    reg = load_registry()
    ids = set(reg)
    edges = [(a, d) for a,r in reg.items() for d in (r['depends_on'] or [])]
    writer_of, texts = writer_index()

    q1_draft   = [(a,d) for a,d in edges if d in ids and reg[a]['catalog_status']=='CURRENT'
                                        and reg[d]['catalog_status']=='DRAFT']
    q1_retired = [(a,d) for a,d in edges if d in ids and reg[a]['catalog_status']=='CURRENT'
                                        and reg[d]['catalog_status']=='RETIRED']
    q1_inactive= [(a,d) for a,d in edges if d in ids and reg[a]['catalog_status']=='CURRENT'
                                        and not reg[d]['is_active']]
    q2_registry= sorted({(a,d) for a,d in edges if d not in ids})
    se, seed_ids_list, coeff = seed_edges()
    seed_ids = set(seed_ids_list)
    q2_seed = sorted({(a,d) for a,d in se if d not in ids})
    q2_seed_vs_seed = sorted({(a,d) for a,d in se if d not in seed_ids})

    # edge-set diff registry vs seed
    reg_set = set(edges); seed_set = set(se)
    only_reg  = sorted(reg_set - seed_set)
    only_seed = sorted(seed_set - reg_set)

    # cycles / self / dup
    adj={a:[d for d in (reg[a]['depends_on'] or []) if d in ids] for a in ids}
    color={}; cycles=[]
    def dfs(u,stack):
        color[u]=1; stack.append(u)
        for v in adj[u]:
            if color.get(v,0)==0: dfs(v,stack)
            elif color.get(v)==1: cycles.append(stack[stack.index(v):]+[v])
        color[u]=2; stack.pop()
    for a in sorted(ids):
        if color.get(a,0)==0: dfs(a,[])
    self_edges=[e for e in edges if e[0]==e[1]]
    from collections import Counter
    dup=[k for k,v in Counter(edges).items() if v>1]

    # Q3 over-declaration
    q3=[]
    for a,d in edges:
        row={'asset':a,'dep':d}
        if a not in writer_of:
            row.update(tight='UNKNOWN_no_writer_source', loose='UNKNOWN_no_writer_source'); q3.append(row); continue
        if d not in ids:
            row.update(tight='DANGLING', loose='DANGLING'); q3.append(row); continue
        pt=tables_of(reg[d])
        if not pt:
            row.update(tight='UNKNOWN_dep_declares_no_table', loose='UNKNOWN_dep_declares_no_table',
                       dep_tables=[]); q3.append(row); continue
        tb=re.sub(r'#[^\n]*',' ','\n'.join(texts[f] for f in writer_of[a]))
        lf=universe(a, writer_of, texts)
        lb=re.sub(r'#[^\n]*',' ','\n'.join(texts[f] for f in lf))
        def v(b):
            if any(re.search(r'\b(?:FROM|JOIN)\s+'+re.escape(t)+r'(?![A-Za-z0-9_])',b,re.I) for t in pt):
                return 'read_evidence'
            if any(re.search(r'(?<![A-Za-z0-9_])'+re.escape(t)+r'(?![A-Za-z0-9_])',b) for t in pt):
                return 'mentioned_not_read'
            return 'NO_TEXTUAL_READ_EVIDENCE'
        row.update(tight=v(tb), loose=v(lb), dep_tables=sorted(pt),
                   writer_files=sorted(str(f.relative_to(ROOT)) for f in writer_of[a]),
                   loose_scan_files=len(lf))
        q3.append(row)

    meta={'task':'M0-T7','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'git_head':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip(),
          'git_branch':subprocess.run(['git','rev-parse','--abbrev-ref','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip(),
          'database_access':'READ-ONLY (SELECT only, autocommit)',
          'registry_rows':len(reg),'registry_edges':len(edges),
          'assets_with_deps':sum(1 for r in reg.values() if r['depends_on']),
          'assets_without_deps':sum(1 for r in reg.values() if not r['depends_on']),
          'seed_assets':len(seed_ids),'seed_edges':len(se),'seed_coefficient_edges':len(coeff),
          'seed_assets_not_in_registry':sorted(seed_ids-set(reg)),
          'registry_assets_not_in_seed':sorted(set(reg)-seed_ids),
          'writers_resolved':len(writer_of)}
    res={'_meta':meta,
         'q1_current_depends_on_draft':sorted(q1_draft),
         'q1_current_depends_on_retired':sorted(q1_retired),
         'q1_current_depends_on_inactive':sorted(q1_inactive),
         'q2_dangling_registry':q2_registry,
         'q2_dangling_seed_vs_registry':q2_seed,
         'q2_dangling_seed_vs_seed':q2_seed_vs_seed,
         'edges_only_in_registry':only_reg,'edges_only_in_seed':only_seed,
         'seed_coefficient_edges':coeff,
         'seed_coefficient_dangling':sorted({(u,d) for u,d in coeff if u not in ids or d not in ids}),
         'cycles':cycles,'self_edges':self_edges,'duplicate_edges':dup,
         'q3_over_declaration':q3,
         'registry_status':{a:{'catalog_status':r['catalog_status'],'is_active':r['is_active'],
                               'layer':r['layer']} for a,r in reg.items()}}
    json.dump(res, open(OUT/'DAG_AUDIT.json','w'), indent=1, default=str)
    print('edges',len(edges),'| CURRENT->DRAFT',len(q1_draft),'| dangling(registry)',len(q2_registry),
          '| dangling(seed)',len(q2_seed),'| cycles',len(cycles))
    print('seed edges',len(se),'only_reg',len(only_reg),'only_seed',len(only_seed))
    print('q3', Counter(r['loose'] for r in q3))

if __name__=='__main__':
    main()

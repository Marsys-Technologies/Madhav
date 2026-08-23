#!/usr/bin/env python3
"""M0-T6 — asset -> serving-surface consumer map (static analysis, read-only).

Method summary (the limits are the point; see _meta.method_limits in the output):

  1. Each registered asset contributes its `target_table` (primary) and any table names
     parsed out of its `count_sql` / `clear_tables` (derived).
  2. Every non-test source file in the four corpora is scanned for whole-word occurrences
     of those table names. Each hit is graded `sql` (a FROM/JOIN/INTO/UPDATE/DELETE FROM/
     USING/TRUNCATE keyword immediately precedes it) or `weak` (anything else — a comment,
     a description string, a variable name). Only `sql`-graded hits are treated as reads.
  3. A read site is attributed to a consumer by ONE of four exact or near-exact relations,
     never by an unbounded transitive import walk:
       direct        — the read is inside the surface file itself (route.ts / page.tsx /
                       a file calling server.tool() / a FastAPI router).
       capability    — the read is inside a retrieval CapabilityDescriptor module; the
                       capability's own `marsys://` uri IS the served surface (dispatched
                       by POST /api/retrieval/capability), and the MCP tool name bound to
                       that uri (from platform-mcp's generated surface profile) is named.
       traced        — the read is in a library module forward-reachable from a route/page/
                       router within IMPORT_DEPTH hops, not crossing a hub module.
       writer        — the read is in a python module reachable from a @register()'d writer.
  4. Anything else the scan found is reported, per asset, in a non-serving bucket
     (ops_script / registry_declaration / prompt_text / unattributed) rather than dropped.
"""
import json, os, pathlib, re, sys, datetime, collections

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / '00_ARCHITECTURE/control/CONSUMER_MAP.json'
IMPORT_DEPTH = 3
HUB_FANIN = 30

# ---------------------------------------------------------------- registry (read-only)
def load_registry():
    import psycopg
    url = next(re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
               for l in (ROOT / 'platform/.env.local').read_text().splitlines()
               if l.startswith('DATABASE_URL='))
    with psycopg.connect(url, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        c = conn.cursor()
        c.execute("SET statement_timeout = '45s'")
        c.execute("""SELECT asset_id, layer, layer_index, asset_kind, catalog_status, is_active,
                            target_table, count_sql, clear_tables, provides_apis, storage_type,
                            scope, english_description, has_writer, target_floor
                     FROM asset_registry ORDER BY asset_id""")
        regs = c.fetchall()
        c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        db_tables = {r['table_name'] for r in c.fetchall()}
        c.execute("SELECT table_name FROM information_schema.views WHERE table_schema='public'")
        db_views = {r['table_name'] for r in c.fetchall()}
        c.execute("SELECT viewname AS n, definition AS d FROM pg_views WHERE schemaname='public'")
        defs = [(r['n'], r['d'] or '') for r in c.fetchall()]
        c.execute("SELECT matviewname AS n, definition AS d FROM pg_matviews WHERE schemaname='public'")
        defs += [(r['n'], r['d'] or '') for r in c.fetchall()]
        db_views |= {n for n, _ in defs}
        c.execute("""SELECT p.proname AS n, p.prosrc AS d FROM pg_proc p
                     JOIN pg_namespace ns ON ns.oid = p.pronamespace
                     WHERE ns.nspname='public' AND p.prokind='f'""")
        fdefs = [(r['n'], r['d'] or '') for r in c.fetchall()]
    return regs, db_tables, db_views, defs, fdefs

SQL_TABLE_RE = re.compile(
    r'\b(?:from|join|into|update|delete\s+from|table|using)\s+(?:only\s+)?(?:public\.)?"?([a-z_][a-z0-9_]*)"?',
    re.I)

def tables_from_sql(sql):
    return {m.group(1).lower() for m in SQL_TABLE_RE.finditer(sql)} if sql else set()

# ---------------------------------------------------------------- corpus
SKIP_DIRS = {'node_modules', 'dist', '.next', '__pycache__', 'venv', '.git',
             'test-results', 'coverage'}
TEST_PAT = re.compile(r'(^|/)(__tests__|tests|test|evals|eval|__mocks__|fixtures)(/|$)'
                      r'|\.(test|spec)\.[cm]?tsx?$|(^|/)test_[^/]*\.py$|_test\.py$'
                      r'|\.test\.py$|conftest\.py$')
def is_test(rel): return bool(TEST_PAT.search(rel))

CORPORA = [
    ('platform-mcp/src', ('.ts', '.tsx')),
    ('platform/src', ('.ts', '.tsx')),
    ('platform/scripts', ('.ts', '.py')),
    ('platform/python-sidecar/pipeline', ('.py',)),
    ('platform/python-sidecar/ga_writers', ('.py',)),
    ('platform/python-sidecar/bodha_writers', ('.py',)),
    ('platform/python-sidecar/brahma', ('.py',)),
    ('platform/python-sidecar/brahmagyan', ('.py',)),
    ('platform/python-sidecar/routers', ('.py',)),
    ('platform/python-sidecar/services', ('.py',)),
    ('platform/python-sidecar/muhurat', ('.py',)),
    ('platform/python-sidecar/panchang_engine', ('.py',)),
    ('platform/python-sidecar/pyjhora_adapter', ('.py',)),
    ('platform/python-sidecar/scripts', ('.py',)),
]

def collect_files():
    files = set()
    for base, exts in CORPORA:
        b = ROOT / base
        if not b.exists():
            continue
        for dp, dn, fn in os.walk(b):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            for f in fn:
                if any(f.endswith(e) for e in exts):
                    files.add(str((pathlib.Path(dp) / f).relative_to(ROOT)))
    for extra in ('platform/python-sidecar/main.py',):
        if (ROOT / extra).exists():
            files.add(extra)
    return files

# ---------------------------------------------------------------- imports
TS_IMPORT_RE = re.compile(r"""(?:from\s+|import\s*\(\s*|require\(\s*)['"]([^'"]+)['"]""")
PY_FROM_RE = re.compile(r'^[ \t]*from\s+([.\w]+)\s+import\s+(\(([^)]*)\)|[^\n#]+)', re.M)
PY_PLAIN_RE = re.compile(r'^[ \t]*import\s+([.\w]+)', re.M)

def py_import_specs(txt):
    """Yield candidate dotted module specs, including `from pkg import submodule` forms."""
    for m in PY_FROM_RE.finditer(txt):
        mod = m.group(1)
        yield mod
        names = (m.group(3) if m.group(3) is not None else m.group(2))
        for n in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', names or ''):
            if n in ('as', 'import'):
                continue
            yield (mod + '.' + n) if not mod.endswith('.') else (mod + n)
    for m in PY_PLAIN_RE.finditer(txt):
        yield m.group(1)
PY_ROOTS = ['platform/python-sidecar', 'platform/python-sidecar/pipeline']

def resolve_ts(spec, from_rel, all_files):
    if spec.startswith('.'):
        base = os.path.normpath(str(pathlib.PurePosixPath(from_rel).parent / spec)).replace('\\', '/')
    elif spec.startswith('@/'):
        base = 'platform/src/' + spec[2:]
    else:
        return None
    noext = re.sub(r'\.(js|ts|tsx|mjs|cjs)$', '', base)
    for suf in ('.ts', '.tsx', '/index.ts', '/index.tsx', '.js'):
        if noext + suf in all_files:
            return noext + suf
    return base if base in all_files else None

def resolve_py(mod, from_rel, all_files):
    if not mod:
        return None
    if mod.startswith('.'):
        nd = len(mod) - len(mod.lstrip('.'))
        rest = mod[nd:]
        pkg = pathlib.PurePosixPath(from_rel).parent
        for _ in range(nd - 1):
            pkg = pkg.parent
        base = str(pkg / rest.replace('.', '/')) if rest else str(pkg)
        for suf in ('.py', '/__init__.py'):
            if base + suf in all_files:
                return base + suf
        return None
    path = mod.replace('.', '/')
    for r in PY_ROOTS:
        for suf in ('.py', '/__init__.py'):
            if f'{r}/{path}{suf}' in all_files:
                return f'{r}/{path}{suf}'
    return None

# ---------------------------------------------------------------- surfaces
MCP_TOOL_RE = re.compile(r'(?:server\.tool|registerTool)\(\s*\n?\s*[\'"`]([a-zA-Z0-9_.]+)[\'"`]')
MCP_RES_RE = re.compile(r'server\.resource\(\s*\n?\s*[\'"`]([a-zA-Z0-9_.\-]+)[\'"`]')
FASTAPI_RE = re.compile(r'@(?:router|app)\.(get|post|put|delete|patch)\(\s*[\'"]([^\'"]+)[\'"]')
CAP_URI_RE = re.compile(r"uri:\s*'(marsys://[^']+)'")
REGISTER_RE = re.compile(r"@register\(\s*['\"]([^'\"]+)['\"]")

def main():
    regs, db_tables, db_views, view_defs, func_defs = load_registry()
    files = collect_files()
    texts = {}
    for rel in files:
        try:
            texts[rel] = (ROOT / rel).read_text(errors='replace')
        except Exception:
            texts[rel] = ''

    # ---- uri -> mcp tool name, from platform-mcp's generated surface profile
    uri_to_tool = {}
    gen = ROOT / 'platform-mcp/src/generated/mcp_surface_profiles.generated.ts'
    if gen.exists():
        g = gen.read_text()
        for m in re.finditer(r'"tool_name":\s*"([^"]+)"(.{0,60000}?)"uri":\s*"([^"]+)"', g, re.S):
            uri_to_tool.setdefault(m.group(3), set()).add(m.group(1))
    bridge = ROOT / 'platform/src/lib/retrieval/registry/mcp_capability_bridge.ts'
    if bridge.exists():
        for m in re.finditer(r"'([a-zA-Z0-9_.\-]+)':\s*'(marsys://[^']+)'", bridge.read_text()):
            uri_to_tool.setdefault(m.group(2), set()).add(m.group(1))

    # ---- per-file surface identity
    surface_of = {}        # rel -> list[(kind, name)]
    mcp_tool_lines = {}    # rel -> [(line, tool_name)] for nearest-enclosing scoping
    cap_of = {}            # rel -> list[uri]
    writer_of = {}         # rel -> list[asset_id]
    for rel, txt in texts.items():
        s = []
        if rel.startswith('platform/src/app/') and rel.endswith('/route.ts'):
            s.append(('api_route', '/' + rel[len('platform/src/app/'):-len('/route.ts')]))
        if rel.startswith('platform/src/app/') and re.search(r'/page\.tsx?$', rel):
            s.append(('ui_page', '/' + re.sub(r'/page\.tsx?$', '', rel[len('platform/src/app/'):])))
        if rel.startswith('platform-mcp/src/'):
            for m in MCP_RES_RE.finditer(txt):
                s.append(('mcp_resource', m.group(1)))
            offs = []
            for m in MCP_TOOL_RE.finditer(txt):
                s.append(('mcp_tool', m.group(1)))
                offs.append((txt.count('\n', 0, m.start()) + 1, m.group(1)))
            if offs and not is_test(rel):
                mcp_tool_lines[rel] = sorted(offs)
        if rel.startswith('platform/python-sidecar/routers/') or rel.endswith('python-sidecar/main.py'):
            for m in FASTAPI_RE.finditer(txt):
                s.append(('sidecar_endpoint', f'{m.group(1).upper()} {m.group(2)}'))
        if s and not is_test(rel):
            surface_of[rel] = sorted(set(s))
        if rel.startswith('platform/src/lib/retrieval/') and not is_test(rel):
            u = sorted(set(CAP_URI_RE.findall(txt)))
            if u:
                cap_of[rel] = u
        if rel.endswith('.py') and not is_test(rel):
            w = REGISTER_RE.findall(txt)
            if w:
                writer_of[rel] = w

    # ---- import graph
    imports = collections.defaultdict(set)
    for rel, txt in texts.items():
        if rel.endswith(('.ts', '.tsx')):
            for m in TS_IMPORT_RE.finditer(txt):
                t = resolve_ts(m.group(1), rel, texts)
                if t:
                    imports[rel].add(t)
        elif rel.endswith('.py'):
            for spec in py_import_specs(txt):
                t = resolve_py(spec, rel, texts)
                if t and t != rel:
                    imports[rel].add(t)
    fanin = collections.Counter()
    for a, bs in imports.items():
        for b in bs:
            fanin[b] += 1
    hubs = {f for f, n in fanin.items() if n >= HUB_FANIN}

    # ---- forward reach, depth-capped, hub-bounded
    RETRIEVAL_SUBTREE = 'platform/src/lib/retrieval/'
    def forward(rel, depth, block_retrieval):
        seen = {rel: 0}
        frontier = [(rel, 0)]
        while frontier:
            cur, d = frontier.pop(0)
            if d >= depth:
                continue
            if d > 0 and cur in hubs:
                continue
            for nxt in imports.get(cur, ()):
                if block_retrieval and nxt.startswith(RETRIEVAL_SUBTREE):
                    continue
                if nxt not in seen:
                    seen[nxt] = d + 1
                    frontier.append((nxt, d + 1))
        return seen

    reach = {}   # surface file -> {module: depth}
    for rel in surface_of:
        block = rel.startswith('platform/src/app/api/retrieval/')
        reach[rel] = forward(rel, IMPORT_DEPTH, block)
    # python writer reach
    writer_reach = {}
    for rel in writer_of:
        writer_reach[rel] = forward(rel, IMPORT_DEPTH, False)
    # module -> surfaces that reach it
    module_surfaces = collections.defaultdict(list)
    for srel, mods in reach.items():
        for m, d in mods.items():
            module_surfaces[m].append((srel, d))
    module_writers = collections.defaultdict(list)
    for wrel, mods in writer_reach.items():
        for m, d in mods.items():
            module_writers[m].append((wrel, d))

    # ---- table scan
    asset_tables = {}
    for r in regs:
        prim = (r['target_table'] or '').strip().lower() or None
        der = set(tables_from_sql(r['count_sql']))
        ct = r['clear_tables']
        if isinstance(ct, (list, tuple)):
            der |= {str(x).strip().lower() for x in ct if x}
        der = {t for t in der if re.fullmatch(r'[a-z_][a-z0-9_]*', t or '')}
        der.discard(prim)
        asset_tables[r['asset_id']] = {'primary': prim, 'derived': sorted(der)}

    GENERIC = {'select', 'values', 'dual', 'lateral', 'set', 'unnest', 'generate_series',
               'jsonb_array_elements', 'json_each', 'json_array_elements', 'only'}
    all_tables = set()
    for t in asset_tables.values():
        if t['primary']:
            all_tables.add(t['primary'])
        all_tables |= set(t['derived'])
    all_tables = {t for t in all_tables if t not in GENERIC and len(t) > 3}

    # ---- DB-side indirection: views / matviews / functions that read an asset's table.
    # Two passes so a view built on a view is caught.
    indirection = collections.defaultdict(set)   # base table -> {(kind, name)}
    base_for = collections.defaultdict(set)      # view/func name -> {base tables}
    def _hits(body, names):
        return {n for n in names if re.search(r'(?<![A-Za-z0-9_])' + re.escape(n) + r'(?![A-Za-z0-9_])', body)}
    known = set(all_tables)
    for _pass in range(2):
        added = set()
        for n, d in view_defs:
            for b in _hits(d, known):
                if b == n:
                    continue
                indirection[b].add(('view', n))
                base_for[n].add(b)
                added.add(n)
        for n, d in func_defs:
            for b in _hits(d, known):
                if b == n:
                    continue
                indirection[b].add(('function', n))
                base_for[n].add(b)
        known |= added
    view_names = {n for n, _ in view_defs}
    all_tables |= {n for n in base_for if n in view_names}

    SQL_READ_CTX = re.compile(r'\b(from|join|using)\s+(?:only\s+)?(?:public\.)?"?$', re.I)
    SQL_WRITE_CTX = re.compile(r'\b(into|update|delete\s+from|truncate|table)\s+(?:only\s+)?(?:public\.)?"?$', re.I)
    tbl_res = {t: re.compile(r'(?<![A-Za-z0-9_])(?:public\.)?' + re.escape(t) + r'(?![A-Za-z0-9_])')
               for t in all_tables}
    refs = collections.defaultdict(list)
    for rel, txt in texts.items():
        low = txt.lower()
        for t, rx in tbl_res.items():
            if t not in low:
                continue
            n_here = 0
            for m in rx.finditer(txt):
                st = txt.rfind('\n', 0, m.start()) + 1
                en = txt.find('\n', m.end())
                line = txt[st:en if en != -1 else len(txt)]
                pre = txt[max(0, m.start() - 40):m.start()]
                strength = ('sql_read' if SQL_READ_CTX.search(pre)
                            else 'sql_write' if SQL_WRITE_CTX.search(pre) else 'weak')
                refs[t].append((rel, txt.count('\n', 0, m.start()) + 1, strength, line.strip()[:180]))
                n_here += 1
                if n_here >= 8:
                    break

    # ---- code-module detector (for assets whose rows are not the interface: services,
    # engines, and any asset whose registry row declares a python/JS API instead of a table)
    module_owner = collections.defaultdict(set)     # asset_id -> {owning module file}
    for f, ids in writer_of.items():
        for i in ids:
            module_owner[i].add(f)
    for r0 in regs:
        a0 = r0['asset_id']
        for cand in (f'platform/python-sidecar/services/{a0}',
                     f'platform/python-sidecar/pipeline/orchestrator/writers/{a0}.py'):
            if cand in texts:
                module_owner[a0].add(cand)
            elif (ROOT / cand).is_dir():
                for f in texts:
                    if f.startswith(cand + '/'):
                        module_owner[a0].add(f)

    api_symbols = {}
    for r0 in regs:
        pa0 = r0['provides_apis']
        syms = set()
        if isinstance(pa0, list):
            for e in pa0:
                nm = (e or {}).get('api') if isinstance(e, dict) else None
                if isinstance(nm, str):
                    for part in re.split(r'[.\s(]', nm):
                        if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{4,}', part or ''):
                            syms.add(part)
        api_symbols[r0['asset_id']] = sorted(syms)

    SEED = 'platform/scripts/seed/asset_registry_seed.ts'
    def bucket(rel):
        if rel == SEED:
            return 'registry_declaration'
        if rel.startswith('platform/scripts/') or rel.startswith('platform/python-sidecar/scripts/'):
            return 'ops_script'
        if '/prompts/' in rel:
            return 'prompt_text'
        return None

    out = {}
    for r in regs:
        a = r['asset_id']
        ti = asset_tables[a]
        tabs = [t for t in ([ti['primary']] if ti['primary'] else []) + ti['derived'] if t in all_tables]
        base_tabs = list(tabs)
        via_view = []
        for bt in base_tabs:
            for kind_, nm in sorted(indirection.get(bt, ())):
                if kind_ == 'view' and nm not in tabs:
                    tabs.append(nm)
                    via_view.append({'base_table': bt, 'view': nm})
        db_func_indirection = sorted({nm for bt in base_tabs
                                      for k_, nm in indirection.get(bt, ()) if k_ == 'function'})
        serving = {}          # key -> record
        writers_c = {}
        nonserving = collections.defaultdict(list)
        unattributed = []
        n_sites = n_sql = n_read = n_write = 0

        own_writer_files = {f for f, ids in writer_of.items() if a in ids}
        owned = module_owner.get(a, set())
        mod_cons = {'serving': {}, 'writers': {}, 'scripts': [], 'other_modules': []}
        for om in sorted(owned):
            for imp, tgts in imports.items():
                if om not in tgts or imp in owned:
                    continue
                if is_test(imp):
                    continue
                if imp in surface_of:
                    for k, n in surface_of[imp]:
                        mod_cons['serving'].setdefault(f'{k}:{n}', []).append(
                            {'importer': imp, 'imports_module': om})
                elif imp in writer_of:
                    for wid in writer_of[imp]:
                        if wid != a:
                            mod_cons['writers'].setdefault(wid, []).append(
                                {'importer': imp, 'imports_module': om})
                elif imp.startswith('platform/scripts/') or '/scripts/' in imp:
                    mod_cons['scripts'].append({'importer': imp, 'imports_module': om})
                else:
                    mod_cons['other_modules'].append({'importer': imp, 'imports_module': om})
        for k_ in ('scripts', 'other_modules'):
            mod_cons[k_ + '_count'] = len(mod_cons[k_])
            mod_cons[k_] = mod_cons[k_][:6]
        # asset-id mention detector: an asset named by id inside a surface or capability
        # module is a strong pointer even when no table of its own is read there.
        id_rx = re.compile(r'(?<![A-Za-z0-9_])' + re.escape(a) + r'(?![A-Za-z0-9_])')
        id_mentions = {'in_surface_files': [], 'in_capability_modules': [], 'in_writers': [],
                       'in_scripts': 0, 'in_other_modules': 0}
        for rel2, txt2 in texts.items():
            if is_test(rel2) or rel2 == SEED or rel2 in owned or a not in txt2:
                continue
            m2 = id_rx.search(txt2)
            if not m2:
                continue
            ln = txt2.count('\n', 0, m2.start()) + 1
            st = txt2.rfind('\n', 0, m2.start()) + 1
            en = txt2.find('\n', m2.end())
            sn = txt2[st:en if en != -1 else len(txt2)].strip()[:160]
            item = {'file': rel2, 'line': ln, 'snippet': sn}
            if rel2 in surface_of:
                item['surfaces'] = [f'{k}:{n}' for k, n in surface_of[rel2]][:6]
                id_mentions['in_surface_files'].append(item)
            elif rel2 in cap_of:
                item['capabilities'] = cap_of[rel2][:6]
                id_mentions['in_capability_modules'].append(item)
            elif rel2 in writer_of:
                item['writer_assets'] = writer_of[rel2]
                id_mentions['in_writers'].append(item)
            elif rel2.startswith('platform/scripts/') or '/scripts/' in rel2:
                id_mentions['in_scripts'] += 1
            else:
                id_mentions['in_other_modules'] += 1
        for k2 in ('in_surface_files', 'in_capability_modules', 'in_writers'):
            id_mentions[k2 + '_count'] = len(id_mentions[k2])
            id_mentions[k2] = id_mentions[k2][:6]

        # provides_apis symbol detector
        sym_hits = []
        for s in api_symbols.get(a, []):
            rx = re.compile(r'(?<![A-Za-z0-9_])' + re.escape(s) + r'(?![A-Za-z0-9_])')
            n_hit = 0
            for rel2, txt2 in texts.items():
                if is_test(rel2) or rel2 in owned:
                    continue
                if s in txt2 and rx.search(txt2):
                    n_hit += 1
                    if len(sym_hits) < 40:
                        sym_hits.append({'symbol': s, 'file': rel2,
                                         'is_surface': rel2 in surface_of,
                                         'is_writer': rel2 in writer_of})
            if n_hit == 0:
                sym_hits.append({'symbol': s, 'file': None, 'note': 'symbol not found anywhere '
                                 'in the scanned corpus'})

        for t in tabs:
            role = ('primary' if t == ti['primary']
                    else 'derived' if t in base_tabs else 'via_db_view')
            for rel, line, strength, snip in refs.get(t, []):
                if is_test(rel):
                    continue
                n_sites += 1
                if strength == 'weak':
                    continue
                n_sql += 1
                if strength == 'sql_read':
                    n_read += 1
                else:
                    n_write += 1
                ev = {'table': t, 'table_role': role, 'file': rel, 'line': line,
                      'access': 'read' if strength == 'sql_read' else 'write', 'snippet': snip}
                b = bucket(rel)
                if b:
                    nonserving[b].append(ev)
                    continue
                if rel in own_writer_files:
                    nonserving['own_writer'].append(ev)
                    continue
                hit = False
                # direct
                direct_targets = surface_of.get(rel, [])
                if rel in mcp_tool_lines:
                    offs = mcp_tool_lines[rel]
                    prev = [nm for ln, nm in offs if ln <= line]
                    nearest = prev[-1] if prev else None
                    scoped = ('exact_nearest_registration' if nearest else 'file_scope')
                    direct_targets = ([('mcp_tool', nearest)] if nearest
                                      else [x for x in direct_targets if x[0] == 'mcp_tool'])
                    direct_targets += [x for x in surface_of.get(rel, []) if x[0] != 'mcp_tool']
                else:
                    scoped = 'exact'
                for k, n in direct_targets:
                    key = f'{k}:{n}'
                    rec = serving.setdefault(key, {'tier': 'direct', 'evidence': []})
                    rec['tier'] = 'direct'
                    rec['attribution_scope'] = scoped
                    rec['evidence'].append(dict(ev, relation='read is inside the surface file'))
                    hit = True
                # capability
                for uri in cap_of.get(rel, []):
                    key = f'capability:{uri}'
                    tools = sorted(uri_to_tool.get(uri, []))
                    rec = serving.setdefault(key, {'tier': 'capability', 'mcp_tools': tools,
                                                   'dispatched_by': 'POST /api/retrieval/capability',
                                                   'evidence': []})
                    rec['evidence'].append(dict(ev, relation='read is inside a CapabilityDescriptor module'))
                    hit = True
                # traced
                for srel, d in module_surfaces.get(rel, []):
                    if srel == rel:
                        continue
                    multi = len([1 for k2, _ in surface_of.get(srel, []) if k2 == 'mcp_tool']) > 1
                    for k, n in surface_of.get(srel, []):
                        key = f'{k}:{n}'
                        rec = serving.setdefault(key, {'tier': 'traced', 'evidence': []})
                        rec.setdefault('attribution_scope',
                                       'file_scope_multi_tool_registrar' if (k == 'mcp_tool' and multi)
                                       else 'exact')
                        rec['evidence'].append(dict(ev, relation=f'read in module imported by {srel} at depth {d}'))
                        hit = True
                # writers
                for wrel, d in module_writers.get(rel, []):
                    for wid in writer_of.get(wrel, []):
                        if wid == a:
                            continue
                        rec = writers_c.setdefault(wid, {'evidence': []})
                        rec['evidence'].append(dict(ev, relation=f'read in module reachable from writer {wrel} at depth {d}'))
                        hit = True
                if not hit:
                    unattributed.append(dict(ev, reason='sql-context read, but the file is neither a '
                                             'surface, a capability module, within import depth '
                                             f'{IMPORT_DEPTH} of one, nor reachable from a writer'))

        for rec in list(serving.values()) + list(writers_c.values()):
            rec['evidence_count'] = len(rec['evidence'])
            rec['evidence'] = rec['evidence'][:3]
        for k in nonserving:
            nonserving[k] = {'count': len(nonserving[k]), 'sample': nonserving[k][:4]}

        pa = r['provides_apis']
        if isinstance(pa, str):
            try:
                pa = json.loads(pa)
            except Exception:
                pass
        prim = ti['primary']
        out[a] = {
            'layer': r['layer'], 'layer_index': r['layer_index'], 'asset_kind': r['asset_kind'],
            'catalog_status': r['catalog_status'], 'is_active': r['is_active'],
            'scope': r['scope'], 'storage_type': r['storage_type'],
            'has_writer': r['has_writer'], 'target_floor': r['target_floor'],
            'target_table': prim,
            'target_table_in_db': (prim in db_tables) if prim else None,
            'target_table_is_view': (prim in db_views) if prim else None,
            'derived_tables': ti['derived'],
            'tables_scanned': tabs,
            'db_view_indirection': via_view,
            'db_function_indirection': db_func_indirection,
            'registry_provides_apis': pa,
            'reference_sites': n_sites,
            'sql_context_statements': n_sql,
            'sql_context_reads': n_read,
            'sql_context_writes': n_write,
            'serving_consumers': serving,
            'serving_consumer_count': len(serving),
            'writer_consumers': writers_c,
            'writer_consumer_count': len(writers_c),
            'non_serving_references': dict(nonserving),
            'owning_code_modules': sorted(owned)[:12],
            'owning_code_module_count': len(owned),
            'module_import_consumers': mod_cons,
            'provides_apis_symbol_hits': sym_hits[:24],
            'asset_id_mentions': id_mentions,
            'unattributed_reads': unattributed[:10],
            'unattributed_read_count': len(unattributed),
            'evidence_class': None,
        }
        # classification
        v = out[a]
        v['has_unattributed_reads'] = bool(v['unattributed_read_count'])
        if v['serving_consumer_count']:
            v['evidence_class'] = 'serving_consumer_detected'
        elif v['writer_consumer_count']:
            v['evidence_class'] = 'writer_consumer_only'
        elif not base_tabs and mod_cons['serving']:
            v['evidence_class'] = 'serving_consumer_detected_via_code_module'
        elif not base_tabs and mod_cons['writers']:
            v['evidence_class'] = 'writer_consumer_only_via_code_module'
        elif not base_tabs:
            v['evidence_class'] = 'UNKNOWN_no_table_declared'
        elif v['unattributed_read_count']:
            v['evidence_class'] = 'UNKNOWN_reads_exist_but_unattributed'
        elif v['sql_context_statements'] == 0:
            v['evidence_class'] = 'no_sql_statement_found_anywhere'
        else:
            v['evidence_class'] = 'statements_only_in_non_serving_buckets'

    meta = {
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'),
        'generator': '00_ARCHITECTURE/control/consumer_map.py',
        'task': 'M0-T6 (Nirmāṇa Phase 0.7 consumer map + 0.8c evidence)',
        'assets': len(regs), 'files_scanned': len(files),
        'tables_indexed': len(all_tables),
        'surfaces_detected': {
            'api_route': sum(1 for v in surface_of.values() for k, _ in v if k == 'api_route'),
            'ui_page': sum(1 for v in surface_of.values() for k, _ in v if k == 'ui_page'),
            'mcp_tool': len({n for v in surface_of.values() for k, n in v if k == 'mcp_tool'}),
            'sidecar_endpoint': sum(1 for v in surface_of.values() for k, _ in v if k == 'sidecar_endpoint'),
            'mcp_resource': len({n for v in surface_of.values() for k, n in v if k == 'mcp_resource'}),
            'retrieval_capability_uris': len({u for us in cap_of.values() for u in us}),
            'python_writers': len({w for ws in writer_of.values() for w in ws}),
        },
        'import_edges': sum(len(v) for v in imports.values()),
        'import_depth': IMPORT_DEPTH, 'hub_fanin_threshold': HUB_FANIN, 'hub_modules': len(hubs),
        'db_access': 'READ-ONLY (SELECT only, autocommit, statement_timeout 45s)',
        'method_limits': [
            'STATIC ONLY. A textual reference is not proof a caller can reach the surface at '
            'runtime; nothing here executes code, exercises a route, or reads server logs.',
            'Table names are matched as whole-word tokens. Each hit is graded `sql_read` '
            '(immediately preceded by FROM/JOIN/USING), `sql_write` (INTO/UPDATE/DELETE FROM/'
            'TRUNCATE/TABLE) or `weak` (everything else). ONLY sql_read and sql_write hits are '
            'counted as statements; `weak` hits are counted in reference_sites but are never '
            'treated as evidence of a consumer.',
            'A sql-graded hit is still only a textual statement: it does not distinguish a live '
            'code path from dead code, a commented-out query, or a stub that never runs.',
            'INVISIBLE TO THIS METHOD: dynamic SQL, table names built by concatenation or '
            'template interpolation, ORM/query-builder indirection, a table read only from inside '
            'a PL/pgSQL function body invoked by a surface, and any surface registered by a '
            'pattern not matched by the surface regexes below. (Views and matviews ARE followed — '
            'see the DB-side indirection note.)',
            'Surface detection is regex-based: app/**/route.ts (API), app/**/page.tsx (UI), '
            '`server.tool(`/`registerTool(` (MCP), FastAPI decorators (sidecar), and '
            "`uri: 'marsys://...'` (retrieval capability).",
            'MCP tool attribution for capability modules uses the EXACT uri binding from '
            "platform-mcp's generated surface profile and mcp_capability_bridge.ts — not an "
            'import walk. A capability with no bound tool name is still a served surface via '
            'POST /api/retrieval/capability; it is reported with an empty mcp_tools list.',
            f'`traced` attribution walks imports forward from a surface at most {IMPORT_DEPTH} '
            f'hops and never continues through a hub module (fan-in >= {HUB_FANIN}). A real '
            'consumer further away, or only reachable through a hub, is therefore NOT reported — '
            'this trades recall for precision deliberately.',
            'app/api/retrieval/capability/route.ts is excluded from `traced` attribution into the '
            'retrieval subtree, because it is a generic dispatcher that can reach every '
            'capability; attributing every capability read to that one route would be true but '
            'useless. Those reads appear under their own `capability:` key instead.',
            'ATTRIBUTION SCOPE. Several platform-mcp files register many tools in one module. A '
            'read INSIDE such a file is scoped to the nearest preceding server.tool() registration '
            "(attribution_scope='exact_nearest_registration') — a good heuristic, not a parse of "
            'the closure. A read in a module IMPORTED by such a file cannot be scoped at all and '
            "is attributed to every tool the file registers (attribution_scope="
            "'file_scope_multi_tool_registrar'); those entries over-report WHICH tool reads the "
            'asset while still correctly answering WHETHER something does.',
            'Test, eval, mock and fixture paths are excluded from evidence. A surface that exists '
            'only under test is invisible here by design.',
            'DB-side indirection IS followed one step: every view, materialized view and SQL '
            'function whose definition names an asset table is resolved from pg_views / '
            'pg_matviews / pg_proc, and the view name is scanned as an additional table for that '
            'asset (table_role = via_db_view). Function bodies are reported but not scanned as '
            'surfaces. Nested views are resolved to two levels only.',
            'The asset -> table mapping is only as good as the registry: 14 assets declare no '
            'target_table, and for those the scan can only use tables parsed out of count_sql. '
            'An asset with no table at all is reported UNKNOWN, not zero-consumer.',
            'A THIRD, weaker detector records where the asset_id itself is named inside a '
            'surface file or a CapabilityDescriptor module (asset_id_mentions). A name-mention is '
            'a pointer, not a read — it is reported separately and never counted as a serving '
            'consumer — but it is the only signal that finds a serving path re-implemented in '
            'TypeScript against a different table than the asset writes (ka_tulana is the live '
            'example).',
            'For an asset whose interface is CODE rather than rows (asset_kind=service, or a '
            'registry row with provides_apis and no target_table), a second detector is used: who '
            'imports the module(s) that own the asset, and whether the symbols named in '
            'provides_apis appear anywhere in the corpus. This detector answers a different '
            'question from the table scan and its result is reported separately, never merged.',
            'Co-written tables (5 of them, census §5) mean a consumer of the TABLE is not '
            'necessarily a consumer of THIS asset\'s rows. Attribution is table-level, not '
            'partition-level.',
        ],
        'certifies': 'nothing. Observations only (I16 / charter H7). Disposition is ADHIKĀRIN\'s (G1).',
    }
    OUT_JSON.write_text(json.dumps({'_meta': meta, 'assets': out}, indent=1, default=str))
    cnt = collections.Counter(v['evidence_class'] for v in out.values())
    print(json.dumps(cnt, indent=1))
    for a, v in sorted(out.items()):
        if v['evidence_class'] != 'serving_consumer_detected':
            print(' ', a, '|', v['evidence_class'], '| tables', v['tables_scanned'],
                  '| reads', v['sql_context_reads'], '| writes', v['sql_context_writes'],
                  '| unattr', v['unattributed_read_count'], '| writers', list(v['writer_consumers']))

if __name__ == '__main__':
    main()

"""Static test: every fact_category an L1 ga_* chart_facts writer can emit has an ownership row for THAT writer's asset.

Why: the live trigger l1_data_plane_mutation_guard (function l1_data_plane_guard_active_mutation, migration 1035) refuses a
chart_facts INSERT / UPDATE / DELETE by an L1 asset whose (fact_category, asset) pair has no fact_category_ownership row
('L1 asset % cannot mutate chart_facts category %'). A category a writer emits with no row therefore fails a whole build at
write time (the data-plane rehearsal found dasha_scope_cap that way). Migration 1219 seeds the ownership rows; this test
makes "seed list + the rows already live" a checked superset of what the writers can emit.

How the emitted set is found (pure static analysis, no database, no writer is imported or run). It parses exactly:
  (a) dict-literal "fact_category" keys;
  (b) fact_category= keyword arguments;
  (c) row["fact_category"] = ... assignments (a constant subscript key);
  (d) INSERT INTO chart_facts (...) VALUES (...) SQL string literals, only the parenthesised VALUES tuple, and only when the
      fact_category slot of that tuple is a quoted literal ('dasha_scope_cap' in ga_dashas_writer.py is the live case);
and it follows helper call sites: every call to a row-builder helper whose parameter feeds (a)-(c) is read at the argument
position the helper uses it from (found by fixpoint, per file, following imports between the writer modules), including the
helper's parameter default when the call omits the argument. Names are resolved through assignments, loop targets over literal
tuples / dict.items(), f-strings (including a parameter filled by literals at the same file's call sites) and module
constants. Anything it cannot resolve to literals is reported as UNRESOLVED and FAILS the test: a new dynamic category cannot
be silently ignored.

What it does NOT see (three known blind spots; no current writer uses any of them; post-window hardening):
  (1) a Python tuple row bound through INSERT ... VALUES (%s, %s, ...) (the category is then a bound parameter, not a literal);
  (2) variable-key assignments such as row[k] = ... (only a constant 'fact_category' subscript key is recognised);
  (3) INSERT ... SELECT 'literal' (a select list is not parsed; only a parenthesised VALUES tuple is).
A writer that adopts one of these shapes would not be enumerated by this test.

The expected owner of each emitted category is the asset of the writer file (FILE_TO_ASSET). The owner rows that count are
the ones live on 2026-10-02 (fixtures/argala_1219/owned_live_all_2026-10-02.txt, the documented allowlist, minus the five
panchanga rows 1219 deletes from ga_structural) plus the 1219 seed list, parsed from the migration file itself.

ga_vargas_writer.py is excluded on purpose: it writes chart_divisionals (its own protected table); its "fact_category"
dict key is a chart_divisionals column, not chart_facts.
"""
from __future__ import annotations

import ast
import collections
import pathlib
import re

import pytest

R = pathlib.Path(__file__).resolve().parents[1]                       # platform/python-sidecar
REPO = pathlib.Path(__file__).resolve().parents[3]
F1219 = REPO / "platform/migrations/1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_count_sql.sql"
LIVE_ALLOWLIST = pathlib.Path(__file__).resolve().parent / "fixtures" / "argala_1219" / "owned_live_all_2026-10-02.txt"

FILES = sorted(list((R / "ga_writers").glob("*.py")) + list((R / "pipeline/orchestrator/writers").glob("ga_*.py")))
FILES = [f for f in FILES if f.name != "__init__.py"]

# writer source file -> the L1 asset whose ownership rows it needs (guard allowlist for chart_facts, migration 1035)
FILE_TO_ASSET = {
    "ga_ayurdaya_writer.py": "ga_ayurdaya",
    "ga_condition_writer.py": "ga_condition",
    "ga_dashas_writer.py": "ga_dashas",
    "ga_kp_significators.py": "ga_nakshatra",            # imported by pipeline/orchestrator/writers/ga_nakshatra.py
    "ga_nakshatra.py": "ga_nakshatra",
    "ga_nakshatra_emitters.py": "ga_nakshatra",
    "ga_panchanga_writer.py": "ga_panchanga",
    "ga_positions_writer.py": "ga_positions",
    "ga_sade_sati_writer.py": "ga_sade_sati",
    "ga_sensitive_degree_writer.py": "ga_sensitive_degree",
    "ga_sensitive_writer.py": "ga_sensitive",
    "ga_strength_writer.py": "ga_strength",
    "ga_structural_writer.py": "ga_structural",
}
NOT_CHART_FACTS = {"ga_vargas_writer.py": "chart_divisionals"}        # its 'fact_category' key is a chart_divisionals column
GUARD_CHART_FACTS_ASSETS = {"ga_positions", "ga_dashas", "ga_nakshatra", "ga_panchanga", "ga_sensitive", "ga_sensitive_degree",
                            "ga_strength", "ga_structural", "ga_condition", "ga_sade_sati", "ga_ayurdaya"}   # migration 1035 allowlist
MOVED_TO_PANCHANGA = {"bhadra_flag", "chandra_bala_natal_baseline", "eclipse_proximity_natal", "panchaka_flag", "tara_bala_natal_baseline"}


def collect_assigns(nodes):
    d = collections.defaultdict(list)
    for top in nodes:
        for a in ast.walk(top):
            if isinstance(a, ast.Assign):
                for tg in a.targets:
                    if isinstance(tg, ast.Name): d[tg.id].append(a.value)
                    elif isinstance(tg, (ast.Tuple, ast.List)) and isinstance(a.value, (ast.Tuple, ast.List)) and len(tg.elts) == len(a.value.elts):
                        for x, y in zip(tg.elts, a.value.elts):
                            if isinstance(x, ast.Name): d[x.id].append(y)
            elif isinstance(a, ast.AnnAssign) and isinstance(a.target, ast.Name) and a.value is not None:
                d[a.target.id].append(a.value)
            elif isinstance(a, (ast.For, ast.comprehension)):
                def walk_t(tg, path):
                    if isinstance(tg, ast.Name): d[tg.id].append(("FOR", a.iter, tuple(path)))
                    elif isinstance(tg, (ast.Tuple, ast.List)):
                        for i, x in enumerate(tg.elts): walk_t(x, path + [i])
                walk_t(tg := a.target, [])
    return d

def _iter_elements(it, scope, mod):
    """Return list of element-expression nodes for a for-iterable, or None. A dict .items() yields (key, value) pairs."""
    if isinstance(it, (ast.Tuple, ast.List, ast.Set)): return list(it.elts)
    if isinstance(it, ast.Name):
        for m in (scope.get(it.id) or mod.get(it.id) or []):
            r = _iter_elements(m, scope, mod)
            if r is not None: return r
        return None
    if isinstance(it, ast.Dict): return list(it.keys)
    if isinstance(it, ast.Call):
        fnm = it.func.attr if isinstance(it.func, ast.Attribute) else (it.func.id if isinstance(it.func, ast.Name) else None)
        if fnm == 'items' and isinstance(it.func, ast.Attribute):
            tgt = it.func.value
            dicts = []
            if isinstance(tgt, ast.Name):
                dicts = [m for m in (scope.get(tgt.id) or mod.get(tgt.id) or []) if isinstance(m, ast.Dict)]
            elif isinstance(tgt, ast.Dict): dicts = [tgt]
            if dicts:
                return [ast.Tuple(elts=[k, v], ctx=ast.Load()) for d in dicts for k, v in zip(d.keys, d.values)]
            return None
        if fnm in ('values',) and isinstance(it.func, ast.Attribute) and isinstance(it.func.value, ast.Name):
            dicts = [m for m in (scope.get(it.func.value.id) or mod.get(it.func.value.id) or []) if isinstance(m, ast.Dict)]
            if dicts: return [v for d in dicts for v in d.values]
        if fnm in ('sorted', 'list', 'tuple', 'enumerate') and it.args:
            r = _iter_elements(it.args[0], scope, mod)
            if r is not None and fnm == 'enumerate':
                return [ast.Tuple(elts=[ast.Constant(value=0), e], ctx=ast.Load()) for e in r]
            return r
    return None

def resolve(node, scope, mod, depth=0, fnctx=None):
    out, bad = set(), []
    if isinstance(node, ast.Constant) and isinstance(node.value, str): out.add(node.value)
    elif isinstance(node, ast.IfExp):
        for b in (node.body, node.orelse):
            o, e = resolve(b, scope, mod, depth, fnctx); out |= o; bad += e
    elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        for el in node.elts:
            o, e = resolve(el, scope, mod, depth, fnctx); out |= o; bad += e
    elif isinstance(node, ast.JoinedStr):
        parts = [[]]
        ok = True
        for v in node.values:
            if isinstance(v, ast.Constant): opts = {v.value}
            elif isinstance(v, ast.FormattedValue):
                o, e = resolve(v.value, scope, mod, depth + 1, fnctx)
                if e or not o: ok = False; bad += e or ["fstr-part:" + ast.unparse(v.value)]; break
                opts = o
            else: ok = False; break
            parts = [p + [x] for p in parts for x in opts]
        if ok: out |= {"".join(p) for p in parts}
        else: bad.append("fstr:" + ast.unparse(node)[:70])
    elif isinstance(node, ast.Name) and depth < 5:
        vals = scope.get(node.id) or mod.get(node.id)
        if not vals and fnctx is not None:
            fn, tree, f_path, sinks_, imap_ = fnctx
            ps = [a.arg for a in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs]
            if node.id in ps:
                # interprocedural, same file: literal at each call site of the enclosing function
                allp = [a.arg for a in fn.args.posonlyargs + fn.args.args]
                off = 1 if allp and allp[0] in ('self', 'cls') else 0
                found = 0
                for c in ast.walk(tree):
                    if isinstance(c, ast.Call) and fname(c) == fn.name:
                        arg = None
                        for kw in c.keywords:
                            if kw.arg == node.id: arg = kw.value
                        if arg is None and node.id in allp and allp.index(node.id) - off < len(c.args): arg = c.args[allp.index(node.id) - off]
                        if arg is not None:
                            found += 1
                            o, e = resolve(arg, collect_assigns([enclosing_of(tree, c)]) if enclosing_of(tree, c) else {}, mod, depth + 1, None)
                            out |= o; bad += e
                if not found: bad.append("param-no-callsite:" + node.id)
                return out, bad
        if not vals: bad.append("name:" + node.id)
        for v in vals or []:
            if isinstance(v, tuple) and v[0] == "FOR":
                _, it, path = v
                elts = _iter_elements(it, scope, mod)
                if elts is None: bad.append("for-iter:" + ast.unparse(it)[:60]); continue
                for e in elts:
                    cur = e
                    okp = True
                    for i in path:
                        if isinstance(cur, (ast.Tuple, ast.List)) and i < len(cur.elts): cur = cur.elts[i]
                        else: okp = False; break
                    if not okp: bad.append("for-elt"); continue
                    o, b = resolve(cur, scope, mod, depth + 1, fnctx); out |= o; bad += b
            else:
                o, e = resolve(v, scope, mod, depth + 1, fnctx); out |= o; bad += e
    else: bad.append(type(node).__name__ + ":" + ast.unparse(node)[:70])
    return out, bad

def enclosing_of(tree, node):
    best = None
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) and fn.lineno <= node.lineno <= (fn.end_lineno or fn.lineno):
            if best is None or fn.lineno >= best.lineno: best = fn
    return best

def fname(c):
    return c.func.id if isinstance(c.func, ast.Name) else (c.func.attr if isinstance(c.func, ast.Attribute) else None)

def parse_all():
    return {f: ast.parse(f.read_text()) for f in FILES}

def imports_map(trees):
    """file -> {local name -> defining file} for ga_writers/pipeline imports of names defined in another scanned file."""
    bymod = {}
    for f in trees:
        bymod[f.stem] = f
    out = {}
    for f, t in trees.items():
        m = {}
        for n in ast.walk(t):
            if isinstance(n, ast.ImportFrom) and n.module and n.module.split('.')[-1] in bymod:
                for a in n.names: m[a.asname or a.name] = (bymod[n.module.split('.')[-1]], a.name)
        out[f] = m
    return out

def lookup(sinks, imap, f, n):
    if (f, n) in sinks: return sinks[(f, n)]
    if n in imap.get(f, {}):
        g, real = imap[f][n]
        return sinks.get((g, real), set())
    return set()

def sink_functions(trees):
    imap = imports_map(trees)
    sinks = collections.defaultdict(set)   # (file, fname) -> {(param_name, position_index_in_call)}
    changed = True
    while changed:
        changed = False
        for f, t in trees.items():
            for fn in ast.walk(t):
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)): continue
                params = [a.arg for a in fn.args.posonlyargs + fn.args.args]
                kwonly = [a.arg for a in fn.args.kwonlyargs]
                off = 1 if params and params[0] in ('self', 'cls') else 0
                hit = set()
                for d in ast.walk(fn):
                    if isinstance(d, ast.Dict):
                        for k, v in zip(d.keys, d.values):
                            if isinstance(k, ast.Constant) and k.value == 'fact_category' and isinstance(v, ast.Name): hit.add(v.id)
                    elif isinstance(d, ast.Call):
                        n = fname(d)
                        for pn, pos in list(lookup(sinks, imap, f, n)):
                            arg = None
                            for kw in d.keywords:
                                if kw.arg == pn: arg = kw.value
                            if arg is None and pos is not None and pos < len(d.args): arg = d.args[pos]
                            if isinstance(arg, ast.Name): hit.add(arg.id)
                        for kw in d.keywords:
                            if kw.arg == 'fact_category' and isinstance(kw.value, ast.Name): hit.add(kw.value.id)
                for p in hit:
                    if p in params or p in kwonly:
                        pos = params.index(p) - off if p in params else None
                        if (p, pos) not in sinks[(f, fn.name)]:
                            sinks[(f, fn.name)].add((p, pos)); changed = True
    return sinks, imap

SQL_INS = re.compile(r"INSERT\s+INTO\s+(?:public\.)?chart_facts\s*\((.*?)\)\s*(?:VALUES|SELECT)\s*(.*)", re.S | re.I)

def sql_literals(s):
    m = SQL_INS.search(s)
    if not m: return None
    cols = [c.strip() for c in m.group(1).split(',')]
    if 'fact_category' not in cols: return set()
    idx = cols.index('fact_category')
    body = m.group(2)
    # take the first parenthesised tuple after VALUES, or the select list
    vals, depth, cur = [], 0, ''
    started = False
    for ch in body:
        if ch == '(':
            depth += 1
            if depth == 1: started = True; continue
        if ch == ')':
            depth -= 1
            if depth == 0 and started: vals.append(cur); break
        if started:
            if ch == ',' and depth == 1: vals.append(cur); cur = ''; continue
            cur += ch
    if idx < len(vals):
        mm = re.fullmatch(r"\s*'([a-z0-9_]+)'\s*", vals[idx])
        if mm: return {mm.group(1)}
        if re.search(r"%\(fact_category\)s|%s|\$\d", vals[idx]): return set()   # bound parameter: python-side rows
        return {"?SQL:" + vals[idx].strip()}
    return set()

def extract(trees=None):
    trees = trees or parse_all()
    sinks, imap = sink_functions(trees)
    res = collections.defaultdict(lambda: collections.defaultdict(set))   # file -> cat -> {lineno}
    unresolved = []
    for f, t in trees.items():
        mod = collections.defaultdict(list)
        for st in t.body:
            for a in [st] if isinstance(st, (ast.Assign, ast.AnnAssign)) else []:
                if isinstance(a, ast.Assign):
                    for tg in a.targets:
                        if isinstance(tg, ast.Name): mod[tg.id].append(a.value)
                elif a.value is not None and isinstance(a.target, ast.Name): mod[a.target.id].append(a.value)
        funcs = [n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        def enclosing(node):
            best = None
            for fn in funcs:
                if fn.lineno <= node.lineno <= (fn.end_lineno or fn.lineno):
                    if best is None or fn.lineno >= best.lineno: best = fn
            return best
        def emit(expr, node, why):
            fn = enclosing(node)
            scope = collect_assigns([fn]) if fn else {}
            if isinstance(expr, ast.Name) and fn is not None and (f, fn.name) in sinks and any(expr.id == p for p, _ in sinks[(f, fn.name)]):
                return   # parameter of a sink function: resolved at its call sites
            o, b = resolve(expr, scope, mod, 0, (fn, t, f, sinks, imap) if fn else None)
            for c in o: res[f.name][c].add(node.lineno)
            for x in b: unresolved.append((f.name, node.lineno, why, x))
        for node in ast.walk(t):
            if isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if isinstance(k, ast.Constant) and k.value == 'fact_category': emit(v, node, 'dict')
            elif isinstance(node, ast.Assign):
                for tg in node.targets:
                    if isinstance(tg, ast.Subscript) and isinstance(tg.slice, ast.Constant) and tg.slice.value == 'fact_category': emit(node.value, node, 'subscript-assign')
            elif isinstance(node, ast.Call):
                n = fname(node)
                for kw in node.keywords:
                    if kw.arg == 'fact_category': emit(kw.value, node, 'kw')
                if True:
                    for pn, pos in lookup(sinks, imap, f, n):
                        arg = None
                        for kw in node.keywords:
                            if kw.arg == pn: arg = kw.value
                        if arg is None and pos is not None and pos < len(node.args): arg = node.args[pos]
                        if arg is None:
                            dflt = None
                            tgt_file = f if (f, n) in sinks else imap.get(f, {}).get(n, (None, None))[0]
                            for g, gt in trees.items():
                                if g == tgt_file:
                                    for fd in ast.walk(gt):
                                        if isinstance(fd, (ast.FunctionDef, ast.AsyncFunctionDef)) and fd.name == (n if (f, n) in sinks else imap[f][n][1]):
                                            allp = fd.args.posonlyargs + fd.args.args
                                            dfl = fd.args.defaults
                                            for i, a_ in enumerate(allp):
                                                if a_.arg == pn and i >= len(allp) - len(dfl): dflt = dfl[i - (len(allp) - len(dfl))]
                                            for a_, dv in zip(fd.args.kwonlyargs, fd.args.kw_defaults):
                                                if a_.arg == pn and dv is not None: dflt = dv
                                    break
                            if dflt is None: unresolved.append((f.name, node.lineno, 'call-' + n, 'arg-not-found:' + pn)); continue
                            gmod = collections.defaultdict(list)
                            for st in trees[tgt_file].body:
                                if isinstance(st, ast.Assign):
                                    for tg in st.targets:
                                        if isinstance(tg, ast.Name): gmod[tg.id].append(st.value)
                            o_, b_ = resolve(dflt, {}, gmod)
                            for c_ in o_: res[f.name][c_].add(node.lineno)
                            for x_ in b_: unresolved.append((f.name, node.lineno, 'default-' + n, x_))
                            continue
                        emit(arg, node, 'call-' + n)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and 'chart_facts' in node.value:
                r = sql_literals(node.value)
                if r:
                    for c in r:
                        if c.startswith('?SQL:'): unresolved.append((f.name, node.lineno, 'sql', c))
                        else: res[f.name][c].add(node.lineno)
    return res, unresolved, sinks



# ── data: owner rows ───────────────────────────────────────────────────────────────────────

def _seed_text() -> str:
    return F1219.read_text(encoding="utf-8")


def seed_pairs(text: str | None = None) -> set[tuple[str, str]]:
    text = _seed_text() if text is None else text
    block = text.split("INSERT INTO _own_1219 (fact_category, owning_asset_id) VALUES", 1)[1].split(";", 1)[0]
    return set(re.findall(r"\('([a-z0-9_]+)', '(ga_[a-z_]+)'\)", block))


def live_pairs() -> set[tuple[str, str]]:
    out = set()
    for line in LIVE_ALLOWLIST.read_text().split("\n"):
        if line.strip():
            c, a = line.split()
            out.add((c, a))
    return out


def effective_owner_pairs(text: str | None = None) -> set[tuple[str, str]]:
    """The ownership rows that exist once 1219 has applied: live rows (minus the five 1219 deletes from ga_structural) + seeds."""
    live = {p for p in live_pairs() if not (p[1] == "ga_structural" and p[0] in MOVED_TO_PANCHANGA)}
    return live | seed_pairs(text)


# ── the extractor, run once ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def extracted():
    res, unresolved, sinks = extract()
    return res, unresolved, sinks


def emitted_by_asset(res) -> dict[str, set[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    for fname_, cats in res.items():
        if fname_ in NOT_CHART_FACTS:
            continue
        asset = FILE_TO_ASSET.get(fname_)
        assert asset is not None, f"{fname_} emits fact_category values but is not mapped to an L1 asset in FILE_TO_ASSET"
        out[asset] |= set(cats)
    return out


def missing_rows(res, text: str | None = None) -> list[tuple[str, str]]:
    owners = effective_owner_pairs(text)
    return sorted((c, a) for a, cats in emitted_by_asset(res).items() for c in cats if (c, a) not in owners)


# ── tests ──────────────────────────────────────────────────────────────────────────────────

def test_the_extractor_resolves_every_category_expression(extracted):
    _, unresolved, _ = extracted
    assert unresolved == [], "unresolvable category expressions (extend the extractor or make the category a literal): %r" % unresolved[:10]


def test_the_extractor_finds_the_known_anchors(extracted):
    """Guards the extractor itself against silently finding nothing: literals, a helper-parameter call site, an f-string
    filled by a loop-fed parameter, a parameter default, a raw SQL INSERT literal and a dict.items() loop."""
    res, _, _ = extracted
    by = emitted_by_asset(res)
    assert "ayurdaya" in by["ga_ayurdaya"]                                   # module constant through a dict value
    assert "argala_graha_natal" in by["ga_structural"]                       # _base_row('...') call site
    assert "panchanga_rahu_kalam" in by["ga_panchanga"]                      # f"panchanga_{window_name}" via call-site literals
    assert "sensitive_point_yogi" in by["ga_sensitive_degree"]               # parameter default / module constant
    assert "dasha_scope_cap" in by["ga_dashas"]                              # raw SQL INSERT INTO chart_facts literal
    assert "house_bhava_bala_total" in by["ga_strength"]                     # for (cat, ...) in dict.items() loop
    assert sum(len(v) for v in by.values()) >= 230
    assert set(by) <= GUARD_CHART_FACTS_ASSETS, "a writer outside the migration-1035 chart_facts allowlist emits chart_facts rows"


def test_every_emitted_fact_category_has_an_ownership_row_for_its_asset(extracted):
    """The contract: live rows (documented allowlist) + the 1219 seed list cover every category any L1 chart_facts writer emits."""
    res, _, _ = extracted
    gaps = missing_rows(res)
    assert gaps == [], f"emitted fact_category with no ownership row for its writer's asset (add to migration 1219): {gaps}"


def test_dasha_scope_cap_and_amrit_kaal_are_in_the_seed_list():
    seeds = seed_pairs()
    assert ("dasha_scope_cap", "ga_dashas") in seeds
    assert ("panchanga_amrit_kaal", "ga_panchanga") in seeds


def test_the_live_allowlist_is_the_67_rows_read_on_2026_10_02():
    live = live_pairs()
    assert len(live) == 67 and len({c for c, _ in live}) == 67
    # contents, not only the count: its ga_structural rows are the 64 names read live and kept in the repo by the 1219 SQL test
    owned_structural = (LIVE_ALLOWLIST.parent / "owned_structural_2026-10-02.txt").read_text().split()
    assert {c for c, a in live if a == "ga_structural"} == set(owned_structural)


def test_mutation_removing_dasha_scope_cap_from_the_seed_list_fails_the_check(extracted):
    res, _, _ = extracted
    text = _seed_text()
    mutated = text.replace("    ('dasha_scope_cap', 'ga_dashas'),\n", "", 1)
    assert mutated != text
    assert ("dasha_scope_cap", "ga_dashas") in missing_rows(res, mutated)
    assert missing_rows(res, text) == []                                     # and the unmutated seed list passes


def test_mutation_a_new_emitted_category_without_a_row_fails_the_check():
    """Add a call that emits a brand-new category to the structural writer's source (in memory only) and re-extract."""
    trees = parse_all()
    key = next(f for f in trees if f.name == "ga_structural_writer.py")
    src = key.read_text() + "\n\ndef _mutation_probe(c):\n    return _base_row('zz_new_unowned_category', 'S', 'k', c, 1, 'b', 'now', 'v', 1, None, None, None, 'v', 's', 'c', [], 'p')\n"
    trees[key] = ast.parse(src)
    res, unresolved, _ = extract(trees)
    assert ("zz_new_unowned_category", "ga_structural") in missing_rows(res)
    # a new dynamic category the extractor cannot resolve is reported, not ignored
    src2 = key.read_text() + "\n\ndef _mutation_probe2(c, x):\n    return _base_row(x.lookup(), 'S', 'k', c, 1, 'b', 'now', 'v', 1, None, None, None, 'v', 's', 'c', [], 'p')\n"
    trees[key] = ast.parse(src2)
    _, unresolved2, _ = extract(trees)
    assert any("lookup" in u[3] for u in unresolved2)


def test_mutation_a_new_writer_file_emitting_chart_facts_is_not_ignored():
    trees = parse_all()
    fake = R / "ga_writers" / "ga_zz_new_writer.py"
    trees[fake] = ast.parse("def f():\n    return {'fact_category': 'zz_cat'}\n")
    res, _, _ = extract(trees)
    with pytest.raises(AssertionError, match="not mapped to an L1 asset"):
        emitted_by_asset(res)

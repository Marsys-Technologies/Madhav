#!/usr/bin/env python3
"""writer_substep_census.py — AST (not regex) census of registered writer classes.

Authored for Nirmāṇa task M0-T8 (Phase 0.6a). Durable and re-runnable: it is the
truth source behind DERIVED_FIELD_REPAIR_PROPOSAL_v1_0.md §4 and behind that
document's detector D-3 ("re-run the census and diff").

READ-ONLY. It touches no database and imports no project module — it only calls
ast.parse over source text, which is also how it satisfies D-9 (nothing under the
migrations tree is ever imported or executed).

REUSED, NOT RE-IMPLEMENTED (Nirmāṇa M0-T22 / D-25 part 2a): this module is now
importable. `census()` returns the full record and `registered_asset_ids()` returns
just the set of asset_ids that carry a @register decorator in production source —
which is the code-derived truth behind the workbook's `has_writer (code)` column.
D-25 part 3's standing rule ("any registry boolean that gates whether a check runs
must be derived from code") is served by that one function, so there is exactly ONE
AST parser for @register in the control plane, not a second one per consumer.

Two traps this parser exists to avoid, both found the hard way in M0-T8:
  · a regex over source text counts docstring mentions of `@register(` as writers;
  · a naive AST pass drops the `@register(ASSET_ID)` module-constant form (4 writers
    missed, 2 of them HEAVY). Both forms — and the class-attribute form — resolve here,
    and anything that does NOT resolve lands in `unresolved_registrations` rather than
    being silently dropped. `registered_asset_ids()` ASSERTS that list is empty.

Writers live in TWO trees under platform/python-sidecar — `writers/` and
`services/*/writer.py`. This scan is a full rglob over the sidecar, so both are covered
(measured 2026-08-23: 112 registrations under writers/, 11 under services/).

M0-T8 0.6a — AST (not regex) census of registered writer classes.

For every class decorated with @register('<asset_id>') anywhere under
platform/python-sidecar (excluding test trees), record which of the FROZEN
contract methods it defines, resolving inheritance through the collected
class graph. NO imports are executed (D-9: never import the migrations tree
or run module-level code); this is pure ast.parse over source text.
"""
import ast, json, pathlib, sys
ROOT = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')
BASE = ROOT/'platform/python-sidecar'

EXCLUDE_PARTS = {'__pycache__', 'node_modules', '.clone', 'tests', '__tests__', 'venv', '.venv', 'site-packages', 'build', 'dist'}

def dotted(node):
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute):
        p = dotted(node.value)
        return f'{p}.{node.attr}' if p else node.attr
    return None


_CACHE = None


def census(force: bool = False) -> dict:
    """Run the AST census and return its record. Cached — repeated callers in one
    process re-use the single parse. Pure function of source text on disk."""
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE

    classes = {}      # (module, classname) -> record
    unresolved_registrations = []
    registrations = []  # {asset_id, module, classname, lineno}
    by_name = {}      # classname -> [ (module, classname) ]
    parse_errors = []
    files_scanned = 0

    for p in sorted(BASE.rglob('*.py')):
        rel = p.relative_to(ROOT)
        if any(part in EXCLUDE_PARTS for part in rel.parts): continue
        files_scanned += 1
        try:
            tree = ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
        except (SyntaxError, UnicodeDecodeError) as e:
            parse_errors.append(f'{rel}: {e}'); continue
        mod = str(rel)
        # module-level string constants, so @register(ASSET_ID) resolves
        modconsts = {}
        for b in tree.body:
            if isinstance(b, ast.Assign):
                for t in b.targets:
                    if isinstance(t, ast.Name) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                        modconsts[t.id] = b.value.value
            elif isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name) \
                    and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                modconsts[b.target.id] = b.value.value
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef): continue
            methods = set()
            has_substeps_attr = None
            asset_id_attr = None
            for b in node.body:
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.add(b.name)
                elif isinstance(b, ast.Assign):
                    for t in b.targets:
                        if isinstance(t, ast.Name) and t.id == 'has_substeps':
                            if isinstance(b.value, ast.Constant): has_substeps_attr = b.value.value
                        if isinstance(t, ast.Name) and t.id == 'asset_id':
                            if isinstance(b.value, ast.Constant): asset_id_attr = b.value.value
                elif isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name):
                    if b.target.id == 'has_substeps' and isinstance(b.value, ast.Constant):
                        has_substeps_attr = b.value.value
                    if b.target.id == 'asset_id' and isinstance(b.value, ast.Constant):
                        asset_id_attr = b.value.value
            bases = [dotted(b) for b in node.bases]
            key = (mod, node.name)
            classes[key] = {'module': mod, 'classname': node.name, 'bases': bases,
                            'methods': sorted(methods), 'has_substeps_attr': has_substeps_attr,
                            'asset_id_attr': asset_id_attr, 'lineno': node.lineno}
            by_name.setdefault(node.name, []).append(key)
            for dec in node.decorator_list:
                fn = dec.func if isinstance(dec, ast.Call) else dec
                name = dotted(fn)
                if name and name.split('.')[-1] == 'register' and isinstance(dec, ast.Call):
                    aid = None; how = None
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        aid, how = dec.args[0].value, 'literal'
                    elif dec.args and isinstance(dec.args[0], ast.Name) and dec.args[0].id in modconsts:
                        aid, how = modconsts[dec.args[0].id], f'module_const:{dec.args[0].id}'
                    elif dec.args and isinstance(dec.args[0], ast.Attribute) and asset_id_attr:
                        aid, how = asset_id_attr, 'class_attr'
                    if aid is None:
                        unresolved_registrations.append({'module': mod, 'classname': node.name,
                                                         'lineno': node.lineno,
                                                         'arg': ast.dump(dec.args[0]) if dec.args else '<no args>'})
                    else:
                        registrations.append({'asset_id': aid, 'module': mod, 'how': how,
                                              'classname': node.name, 'lineno': node.lineno})

    def resolve(key, seen=None):
        """Walk the class's own methods then its bases (by simple name) within the
        collected graph. Returns (defines_map, chain)."""
        seen = seen or set()
        if key in seen: return {}, []
        seen.add(key)
        rec = classes[key]
        out = {m: key for m in rec['methods']}
        chain = [f"{rec['module']}::{rec['classname']}"]
        attr = rec['has_substeps_attr']
        for b in rec['bases']:
            if not b: continue
            simple = b.split('.')[-1]
            if simple == 'WriterBase':
                chain.append('WriterBase(frozen base)'); continue
            cands = by_name.get(simple, [])
            # prefer a candidate in the same module, else unique match
            pick = None
            for c in cands:
                if c[0] == rec['module']: pick = c; break
            if pick is None and len(cands) == 1: pick = cands[0]
            if pick is None:
                chain.append(f'UNRESOLVED_BASE:{b}'); continue
            sub, subchain = resolve(pick, seen)
            for m, k in sub.items(): out.setdefault(m, k)
            chain.extend(subchain)
            if attr is None and classes[pick]['has_substeps_attr'] is not None:
                attr = classes[pick]['has_substeps_attr']
        rec['_inherited_has_substeps'] = attr
        return out, chain

    results = {}
    dupes = {}
    for r in registrations:
        key = (r['module'], r['classname'])
        defines, chain = resolve(key)
        rec = classes[key]
        plan = 'plan_substeps' in defines
        runsub = 'run_substep' in defines
        runm = 'run' in defines
        # FROZEN contract (writers/__init__.py WriterBase docstring):
        #  HEAVY = overrides BOTH plan_substeps and run_substep
        #  LIGHT = implements run()
        truth = plan and runsub
        results.setdefault(r['asset_id'], []).append({
            'module': r['module'], 'classname': r['classname'], 'lineno': r['lineno'], 'register_arg': r['how'],
            'defines_plan_substeps': plan, 'plan_substeps_from': defines.get('plan_substeps', [None])[1] if plan else None,
            'defines_run_substep': runsub, 'run_substep_from': defines.get('run_substep', [None])[1] if runsub else None,
            'defines_run': runm,
            'class_attr_has_substeps': rec['has_substeps_attr'],
            'inherited_has_substeps': rec.get('_inherited_has_substeps'),
            'mro_chain': chain,
            'writer_truth_has_substeps': truth,
            'shape': 'HEAVY' if truth else ('LIGHT' if runm else ('PARTIAL_plan_only' if plan else ('PARTIAL_runsubstep_only' if runsub else 'NEITHER'))),
        })
    for a, v in results.items():
        if len(v) > 1: dupes[a] = v

    _CACHE = {'unresolved_registrations': unresolved_registrations, 'files_scanned': files_scanned,
              'parse_errors': parse_errors,
              'n_registrations': len(registrations), 'n_distinct_asset_ids': len(results),
              'duplicate_asset_ids': dupes, 'writers': results}
    return _CACHE


def registered_asset_ids(force: bool = False) -> set:
    """The code-derived truth for `has_writer`: every asset_id that a production
    @register decorator binds to a writer class.

    D-25 part 2(a)/2(c): the caller must NOT special-case any asset id. The two
    R0 assets the defect was found on (bg_nakshatra_medical, bg_transit_engine) are
    SECONDARY decorators stacked on a shared writer class — a general shape, and it
    falls out of this function because registrations are collected per-decorator,
    not per-class.

    H4/§N.8: this signal is only earned if the parser actually resolved everything it
    saw. An unresolved @register argument, or a file the parser could not read, means
    the census does NOT know the writer set — so it raises rather than returning a
    quietly-short set that would read as "no writer" for the assets it missed.
    """
    c = census(force=force)
    if c['unresolved_registrations']:
        raise SystemExit(
            'writer_substep_census: UNRESOLVED @register argument(s) — the code-derived '
            'has_writer set is NOT trustworthy and no value may be emitted from it: '
            + repr(c['unresolved_registrations']))
    if c['parse_errors']:
        raise SystemExit(
            'writer_substep_census: source files failed to parse — the code-derived '
            'has_writer set is incomplete: ' + repr(c['parse_errors']))
    return set(c['writers'])


if __name__ == '__main__':
    out = census()
    results = out['writers']
    unresolved_registrations = out['unresolved_registrations']
    files_scanned, parse_errors = out['files_scanned'], out['parse_errors']
    registrations_n, dupes = out['n_registrations'], out['duplicate_asset_ids']
    (pathlib.Path(__file__).resolve().parent/'writer_substep_census.json').write_text(json.dumps(out, indent=1, default=str))
    print('UNRESOLVED @register args:', unresolved_registrations)
    print(f'files_scanned={files_scanned} parse_errors={len(parse_errors)} registrations={registrations_n} distinct_asset_ids={len(results)} dupes={list(dupes)}')
    heavy = sorted(a for a,v in results.items() if v[0]['writer_truth_has_substeps'])
    print(f'HEAVY (plan_substeps+run_substep) n={len(heavy)}:'); [print('  ',h) for h in heavy]
    odd = {a: v[0]['shape'] for a,v in results.items() if v[0]['shape'] not in ('HEAVY','LIGHT')}
    print('non-standard shapes:', odd)
    unres = {a: [c for c in v[0]['mro_chain'] if c.startswith('UNRESOLVED')] for a,v in results.items() if any(c.startswith('UNRESOLVED') for c in v[0]['mro_chain'])}
    print('unresolved bases:', unres)

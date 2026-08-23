#!/usr/bin/env python3
"""M0-T20 INDEPENDENT re-derivation of has_substeps truth from the writer source tree.

Written from scratch for task M0-T20 (D-24 condition (a): "Re-derive the 12 yourself from the
writer classes by AST before writing anything"). It does NOT import, read or reuse
00_ARCHITECTURE/control/writer_substep_census.py — the point is an independent second opinion,
and a script that shares code with the thing it is checking is not one.

Truth rule, from the FROZEN contract (CLAUDE.md §N.2; writers/__init__.py WriterBase docstring):
    HEAVY  := the @register'd class OVERRIDES BOTH plan_substeps AND run_substep
    LIGHT  := it does not (it implements run(ctx))
"OVERRIDE" is load-bearing: WriterBase ITSELF defines default plan_substeps and run_substep, so
"has plan_substeps in the MRO" is a constant (true for every writer), not a detector. Methods
contributed by WriterBase are therefore excluded from the override set.

Nothing is imported and no module-level code is executed: ast.parse only.
"""
import ast, json, pathlib, sys, collections

ROOT = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')
SIDECAR = ROOT / 'platform/python-sidecar'
EXCLUDE_PARTS = {'venv', '.venv', 'site-packages', 'node_modules', '.clone', 'tests', '__tests__',
                 '__pycache__', '.git'}
BASE_EXCLUDE = {'WriterBase', 'object'}   # WriterBase's own defaults are NOT overrides

def wanted(p: pathlib.Path) -> bool:
    return not (set(p.parts) & EXCLUDE_PARTS)

files = [p for p in SIDECAR.rglob('*.py') if wanted(p)]

# class_key -> record.  Keyed by (module_path, class_name); also indexed by bare class name
classes = {}                  # (file, name) -> rec
by_name = collections.defaultdict(list)   # name -> [ (file,name) ]
registrations = []            # (asset_id, file, lineno, class_name, resolved_from)
unresolved = []               # @register args we could not resolve to a string
parse_errors = []

def decorator_register_arg(dec, consts):
    """Return (asset_id, how) if dec is @register(<str-or-module-const>), else None."""
    if not isinstance(dec, ast.Call):
        return None
    fn = dec.func
    name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
    if name != 'register':
        return None
    if not dec.args:
        return ('<NO-ARG>', 'unresolved')
    a = dec.args[0]
    if isinstance(a, ast.Constant) and isinstance(a.value, str):
        return (a.value, 'literal')
    if isinstance(a, ast.Name) and a.id in consts:
        return (consts[a.id], 'module-const')
    if isinstance(a, ast.Attribute):
        return (f'<ATTR:{ast.dump(a)[:60]}>', 'unresolved')
    return (f'<EXPR:{type(a).__name__}>', 'unresolved')

for f in files:
    try:
        tree = ast.parse(f.read_text(encoding='utf-8', errors='replace'), filename=str(f))
    except SyntaxError as e:
        parse_errors.append((str(f), str(e)))
        continue
    # module-level string constants (for @register(ASSET_ID))
    consts = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
           and isinstance(node.value.value, str):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    consts[t.id] = node.value.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
           and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            consts[node.target.id] = node.value.value

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        methods = {n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(b.attr)
        attr_has_substeps = None
        for n in node.body:
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id == 'has_substeps' and isinstance(n.value, ast.Constant):
                        attr_has_substeps = n.value.value
            if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) \
               and n.target.id == 'has_substeps' and isinstance(n.value, ast.Constant):
                attr_has_substeps = n.value.value
        key = (str(f.relative_to(ROOT)), node.name)
        classes[key] = {'file': key[0], 'name': node.name, 'lineno': node.lineno,
                        'methods': methods, 'bases': bases, 'attr_has_substeps': attr_has_substeps}
        by_name[node.name].append(key)
        for dec in node.decorator_list:
            r = decorator_register_arg(dec, consts)
            if r:
                aid, how = r
                if how == 'unresolved':
                    unresolved.append({'file': key[0], 'class': node.name, 'line': node.lineno, 'arg': aid})
                else:
                    registrations.append({'asset_id': aid, 'file': key[0], 'line': node.lineno,
                                          'class': node.name, 'resolved_from': how})

def override_methods(key, seen=None):
    """Union of methods defined by this class and its ancestors, EXCLUDING WriterBase/object."""
    if seen is None:
        seen = set()
    if key in seen or key not in classes:
        return set(), []
    seen.add(key)
    rec = classes[key]
    m = set(rec['methods'])
    chain = [f"{rec['file']}::{rec['name']}"]
    for b in rec['bases']:
        if b in BASE_EXCLUDE:
            continue
        cands = by_name.get(b, [])
        if not cands:
            chain.append(f'<unresolved-base:{b}>')
            continue
        # prefer same-file base, else first
        pick = next((c for c in cands if c[0] == rec['file']), cands[0])
        sm, sc = override_methods(pick, seen)
        m |= sm
        chain += sc
    return m, chain

out = {}
dupes = collections.Counter(r['asset_id'] for r in registrations)
for r in registrations:
    key = (r['file'], r['class'])
    m, chain = override_methods(key)
    heavy = ('plan_substeps' in m) and ('run_substep' in m)
    out[r['asset_id']] = {
        **r,
        'overrides_plan_substeps': 'plan_substeps' in m,
        'overrides_run_substep': 'run_substep' in m,
        'defines_run': 'run' in m,
        'heavy': heavy,
        'class_attr_has_substeps': classes[key]['attr_has_substeps'],
        'mro_chain_excl_writerbase': chain,
    }

# ---- the "constant, not a detector" control: how many if we DON'T exclude WriterBase ----
naive_heavy = 0
for aid, rec in out.items():
    naive_heavy += 1   # every writer inherits WriterBase's plan_substeps+run_substep
res = {
    'files_scanned': len(files),
    'parse_errors': parse_errors,
    'registrations': len(registrations),
    'distinct_asset_ids': len(out),
    'duplicate_asset_ids': [a for a, n in dupes.items() if n > 1],
    'unresolved_register_args': unresolved,
    'heavy_count_override_rule': sum(1 for v in out.values() if v['heavy']),
    'light_count': sum(1 for v in out.values() if not v['heavy']),
    'naive_mro_rule_would_say_heavy': naive_heavy,
    'nonstandard_shapes': {a: (v['overrides_plan_substeps'], v['overrides_run_substep'])
                           for a, v in out.items()
                           if v['overrides_plan_substeps'] != v['overrides_run_substep']},
    'writers': out,
}
p = pathlib.Path(sys.argv[1]) / 'independent_ast_derivation.json'
p.write_text(json.dumps(res, indent=1, default=str) + '\n')
print(f"files_scanned={res['files_scanned']} parse_errors={len(parse_errors)} "
      f"registrations={res['registrations']} distinct={res['distinct_asset_ids']} "
      f"dupes={res['duplicate_asset_ids']}")
print(f"unresolved @register args: {unresolved}")
print(f"HEAVY (override rule)={res['heavy_count_override_rule']}  LIGHT={res['light_count']}")
print(f"naive 'plan_substeps in MRO' rule would say HEAVY={naive_heavy}  <- constant, not a detector")
print(f"non-standard shapes (one of the pair only): {res['nonstandard_shapes']}")

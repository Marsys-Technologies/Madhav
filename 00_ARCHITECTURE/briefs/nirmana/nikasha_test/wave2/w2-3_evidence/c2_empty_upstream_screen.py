import sys, json, ast
sys.path.insert(0, "platform/scripts/governance")
import asset_census as ac
res = json.load(open(sys.argv[1]))
def empty_test(t):
    if isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.Not): return True
    if isinstance(t, ast.Compare) and len(t.ops) == 1:
        r = t.comparators[0]
        if isinstance(t.ops[0], ast.Is) and isinstance(r, ast.Constant) and r.value is None: return True
        if isinstance(t.ops[0], ast.Eq) and isinstance(r, ast.Constant) and r.value == 0: return True
    return False
skip, filt, helper = {}, {}, {}
for k, cfg in ac.LAYERS.items():
    reg, _ = ac.registry(k); regd = ac.registered_ids(cfg["prefix"])
    for aid in reg:
        if res.get(aid, {}).get("v") != "PASS": continue
        units, _ = ac._delegation_scope(aid, regd[aid])
        funcs = {}
        for u in units:
            for n in u["nodes"]:
                for f in ast.walk(n):
                    if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)): funcs.setdefault(id(f), (u, f))
        deleters = {f.name for _, f in funcs.values() if any(ac._SQL_DELETE.search(s) or ac._SQL_TRUNCATE.search(s) for s in ac._code_strings(f))}
        grew = True
        while grew:
            b = len(deleters); deleters |= {f.name for _, f in funcs.values() if any(ac._call_name(c) in deleters for c in ast.walk(f))}; grew = len(deleters) > b
        def reaches(nodes):
            return any((isinstance(c, ast.Call) and ac._call_name(c) in deleters) or
                       (isinstance(c, ast.Constant) and isinstance(c.value, str) and ac._SQL_DELETE.search(c.value)) for n in nodes for c in ast.walk(n))
        for u, f in funcs.values():
            parents = {}
            for p in ast.walk(f):
                for c in ast.iter_child_nodes(p): parents[id(c)] = p
            dls = [c.lineno for c in ast.walk(f) if (isinstance(c, ast.Call) and ac._call_name(c) in deleters) or (isinstance(c, ast.Constant) and isinstance(c.value, str) and ac._SQL_DELETE.search(c.value))]
            if not dls: continue
            for node in ast.walk(f):
                if not (isinstance(node, ast.If) and node.lineno < min(dls) and empty_test(node.test)): continue
                src = ast.unparse(node.test)
                if "dry_run" in src or "table_exists" in src: continue
                if reaches(node.body): continue          # the branch IS the replacement path (ka_sangam), not a skip
                stop = next((s for s in node.body if isinstance(s, (ast.Return, ast.Continue))), None)
                if stop is None: continue
                where = f"{u['rel']}:{node.lineno} `if {src}: {type(stop).__name__.lower()}` ({f.name})"
                if u["rel"].endswith("_idempotency.py"):
                    helper.setdefault(aid, []).append(where); continue
                if isinstance(stop, ast.Continue):
                    loop = parents.get(id(node))
                    while loop is not None and not isinstance(loop, (ast.For, ast.While, ast.AsyncFor)): loop = parents.get(id(loop))
                    (skip if loop is not None and reaches(loop.body) else filt).setdefault(aid, []).append(where)
                else:
                    skip.setdefault(aid, []).append(where)
json.dump(dict(skip=skip, filter=filt, helper=helper), open(sys.argv[2], "w"), indent=1)
print("WHOLE-REPLACEMENT SKIPS on empty input (review #7):", len(skip))
for a, xs in sorted(skip.items()):
    print(f"  {a} ({res[a]['v']}):"); [print("     ", x) for x in xs]
print("per-item filters only (not #7):", sorted(set(filt) - set(skip)))
print("helper `if not rows: return` (delete scoped to new rows' keys):", sorted(helper))

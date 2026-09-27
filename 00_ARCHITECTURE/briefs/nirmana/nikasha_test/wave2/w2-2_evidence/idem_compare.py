import sys, importlib.util; sys.path.insert(0, "platform/scripts/governance")
import asset_census as new
spec = importlib.util.spec_from_file_location("old_ac", sys.argv[1]); old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
moved = 0; n = 0
for L, cfg in new.LAYERS.items():
    reg, _ = new.registry(L); regd = new.registered_ids(cfg["prefix"])
    for aid, r in sorted(reg.items()):
        files = regd.get(aid, [])
        a = old._measure_idem(aid, files, cfg["idem"], r["has_writer"])
        b = new._measure_idem(aid, files, cfg["idem"], r["has_writer"], [r["target_table"]] + new._count_tables(r["count_sql"]))
        n += 1
        if a["v"] != b["v"]:
            moved += 1; print(f"{L} {aid}: {a['v']} -> {b['v']} | {b['measured'][:260]}")
print(f"{n} assets; Idem.pattern verdicts moved: {moved}")

"""Idem.pattern for all 127 active assets via the real _measure_idem, live registry. Usage: idem_all.py <out.json>"""
import json, sys, pathlib
sys.path.insert(0, "platform/scripts/governance")
import asset_census as ac
out = {}
for k, cfg in ac.LAYERS.items():
    reg, _ = ac.registry(k)
    regd = ac.registered_ids(cfg["prefix"])
    for aid, r in reg.items():
        res = ac._measure_idem(aid, regd.get(aid, []), cfg["idem"], r["has_writer"],
                               [r["target_table"]] + ac._count_tables(r["count_sql"]))
        out[aid] = dict(layer=k, files=regd.get(aid, []), target=r["target_table"],
                        ctables=ac._count_tables(r["count_sql"]), **res)
pathlib.Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
import collections
print(collections.Counter(v["v"] for v in out.values()))
for aid, v in sorted(out.items()):
    if v["v"] not in ("PASS", "N/A"):
        print(v["layer"], aid, v["v"], "|", v["files"], "|", v["measured"][:200])

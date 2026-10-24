#!/usr/bin/env python3
"""Reader-only: map every chunk_id cited in the given ledger files to {id (uuid), text_id, chapter, verse_ref}.
  dump_chunk_meta.py <rq.sh> <out.json> <ledger.json> [<ledger.json> ...]"""
import json, subprocess, sys
rq, out, ledgers = sys.argv[1], sys.argv[2], sys.argv[3:]
ids = set()
for p in ledgers:
    d = json.load(open(p)); d = d if isinstance(d, list) else [e for v in d.values() for e in (v if isinstance(v, list) else v.get("entries", []))]
    for e in d:
        for c in e.get("corpus") or []:
            if c.get("chunk_id"): ids.add(c["chunk_id"])
meta = {}
ids = sorted(ids)
for i in range(0, len(ids), 40):
    lst = ",".join("'" + c.replace("'", "''") + "'" for c in ids[i:i + 40])
    sql = f"select chunk_id||'|'||id||'|'||text_id||'|'||chapter||'|'||verse_ref from classical_text_chunks where chunk_id in ({lst})"
    for line in subprocess.run([rq, sql], capture_output=True, text=True).stdout.splitlines()[1:]:
        p = line.split("|")
        if len(p) == 5: meta[p[0]] = {"id": p[1], "text_id": p[2], "chapter": int(p[3]), "verse_ref": p[4]}
json.dump(meta, open(out, "w"), indent=0)
print(len(ids), "chunk ids;", len(meta), "resolved")

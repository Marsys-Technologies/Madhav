#!/usr/bin/env python3
"""Reader-only snapshot of tables (and the asset_registry rows) into a directory, for the disposable-replica tests.

  dump_tables.py <rq.sh> <outdir> <table>[,<table>...]  [--registry asset1,asset2]

Writes <table>.cols.json (name + exact format_type), <table>.rows.jsonl (row_to_json) and registry.json.
SELECT only, through the caller-supplied read-only helper; prints no credential."""
import json, pathlib, subprocess, sys

rq, out = sys.argv[1], pathlib.Path(sys.argv[2])
tables = [t for t in sys.argv[3].split(",") if t]
reg = []
if "--registry" in sys.argv:
    reg = sys.argv[sys.argv.index("--registry") + 1].split(",")
out.mkdir(parents=True, exist_ok=True)


def q(sql):
    p = subprocess.run([rq, sql], capture_output=True, text=True)
    if p.returncode: sys.exit(p.stderr[:300])
    return p.stdout.splitlines()[1:]


for spec in tables:
    t, _, where = spec.partition("@")
    where = f" where {where}" if where else ""
    cols = []
    for line in q(f"select a.attname||'|'||format_type(a.atttypid,a.atttypmod) from pg_attribute a where a.attrelid='{t}'::regclass and a.attnum>0 and not a.attisdropped order by a.attnum"):
        if "|" in line:
            n, ty = line.split("|", 1); cols.append({"name": n, "type": ty})
    json.dump(cols, open(out / f"{t}.cols.json", "w"), indent=0)
    rows = []
    for line in q(f"select encode(convert_to(row_to_json(t)::text,'UTF8'),'hex') from {t} t{where} order by 1"):
        if line and not line.startswith("("):
            rows.append(bytes.fromhex(line).decode("utf8"))
    (out / f"{t}.rows.jsonl").write_text("\n".join(rows) + "\n", encoding="utf8")
    print(t, len(cols), "cols", len(rows), "rows")
if reg:
    d = {}
    for a in reg:
        lines = q(f"select encode(convert_to(row_to_json(t)::text,'UTF8'),'hex') from (select asset_id, integrity_check_sql, english_description, target_floor from asset_registry where asset_id='{a}') t")
        d[a] = json.loads(bytes.fromhex(lines[0]).decode("utf8"))
    json.dump(d, open(out / "registry.json", "w"), ensure_ascii=False, indent=1)
    print("registry", list(d))

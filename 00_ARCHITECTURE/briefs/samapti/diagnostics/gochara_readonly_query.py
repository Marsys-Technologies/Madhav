#!/usr/bin/env python3
"""READ-ONLY query helper. Refuses anything that is not a SELECT/WITH."""
import os, sys, re

_env = "/Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env.local"
with open(_env) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

sql = sys.stdin.read()
# hard read-only guard
for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
    if not re.match(r"^(select|with)\b", stmt, re.I):
        sys.exit(f"REFUSED non-read statement: {stmt[:80]}")

import psycopg, psycopg.rows
_url = os.environ["DATABASE_URL"].replace("127.0.0.1:5433", os.environ.get("PROXY_HOSTPORT", "127.0.0.1:5433"))
conn = psycopg.connect(_url, row_factory=psycopg.rows.dict_row)
conn.read_only = True
with conn.cursor() as cur:
    for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
        cur.execute(stmt)
        rows = cur.fetchall()
        if not rows:
            print("(0 rows)")
        else:
            cols = list(rows[0].keys())
            print(" | ".join(cols))
            print("-" * 60)
            for r in rows:
                print(" | ".join(str(r[c]) for c in cols))
        print()
conn.close()

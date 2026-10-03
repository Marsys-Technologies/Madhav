#!/usr/bin/env python3
"""Self-test of generate_window_privilege_readback.py on a DISPOSABLE PostgreSQL (GOCHARA_A51_TEST_DATABASE_URL-style server; creates and drops its own database).
Builds stub tables/functions with the exact names/signatures the final 1206 §7 and 1240 §7 grants name, runs the ORIGINAL GRANT statements parsed from the files,
and proves: (1) the generated query returns ZERO rows when every grant took; (2) it returns exactly the revoked grant when one is revoked (table, column, function);
(3) it names a missing role and a missing object. Usage: python3 selftest_window_privilege_readback.py <migrations dir> <postgres dsn (a maintenance db)>"""
import re
import sys
import uuid
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_window_privilege_readback as G


def statements(sql: str) -> list[str]:
    return [m.group(0) for m in re.finditer(r"\bGRANT\s+.+?;", G.blank_strings(G.strip_comments(sql)), re.S | re.I)]


def main(mig: str, dsn: str) -> int:
    base = conninfo_to_dict(dsn)
    admin = psycopg.connect(make_conninfo(**{**base, "dbname": "postgres"}), autocommit=True)
    name = f"wpr_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    ok = True
    try:
        c = psycopg.connect(make_conninfo(**{**base, "dbname": name}), autocommit=True)
        items, stmts = [], []
        for f in G.FILES:
            sql = (Path(mig) / f).read_text(encoding="utf-8")
            items += G.parse(sql); stmts += statements(sql)
        for role in sorted({i["role"] for i in items}):
            c.execute(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='{role}') THEN CREATE ROLE {role} NOLOGIN; END IF; END $$")
        for obj in sorted({i["obj"] for i in items if i["kind"] in ("table", "column")}):
            cols = sorted({i["col"] for i in items if i["kind"] == "column" and i["obj"] == obj})
            c.execute(f"CREATE TABLE IF NOT EXISTS {obj} (id int{''.join(f', {x} text' for x in cols)})")
        for sig in sorted({i["obj"] for i in items if i["kind"] == "function"}):
            c.execute(_create_fn(sig))
            c.execute(f"REVOKE ALL ON FUNCTION {sig} FROM PUBLIC")                    # production: PUBLIC EXECUTE is revoked on every function amjis_app creates
        sql_q = G.render(items)
        for s in stmts:
            c.execute(s)
        rows = c.execute(sql_q).fetchall()
        print(f"[1] all {len(items)} grants applied -> readback rows: {len(rows)}"); ok &= len(rows) == 0
        # (2) revoke one of each kind
        c.execute("REVOKE UPDATE (inventory_digest) ON public.ka_gochara_search_inventory FROM data_plane_builder")
        c.execute("REVOKE DELETE ON public.ka_gochara_search_obligation FROM data_plane_builder")
        c.execute("REVOKE EXECUTE ON FUNCTION public.ka_gochara_lock_chart(uuid) FROM gochara_sealer")
        rows = c.execute(sql_q).fetchall()
        got = sorted((r[0], r[1], r[2], r[3].split(".")[-1], r[5]) for r in rows)
        print("[2] after 3 revokes:", got)
        ok &= got == sorted([("column", "data_plane_builder", "UPDATE", "ka_gochara_search_inventory", "PRIVILEGE NOT HELD"),
                             ("table", "data_plane_builder", "DELETE", "ka_gochara_search_obligation", "PRIVILEGE NOT HELD"),
                             ("function", "gochara_sealer", "EXECUTE", "ka_gochara_lock_chart(uuid)", "PRIVILEGE NOT HELD")])
        # (3) missing role and missing object
        c.execute("DROP OWNED BY gochara_verifier; DROP ROLE gochara_verifier")
        rows = c.execute(sql_q).fetchall()
        print("[3] after dropping gochara_verifier:", sorted({r[5] for r in rows}), len([r for r in rows if r[1] == 'gochara_verifier']), "verifier rows")
        ok &= any(r[5] == "ROLE MISSING" for r in rows)
        c.execute("DROP TABLE public.ka_gochara_eval_window_verification CASCADE")
        rows = c.execute(sql_q).fetchall()
        missing = [r for r in rows if r[5] == "OBJECT MISSING"]
        print("[4] after dropping the verification table:", len(missing), "OBJECT MISSING rows")
        ok &= len(missing) >= 1 and all(r[3].endswith("ka_gochara_eval_window_verification") for r in missing)
        c.close()
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _create_fn(sig: str) -> str:
    return f"CREATE OR REPLACE FUNCTION {sig} RETURNS int LANGUAGE sql AS $$ SELECT 1 $$"


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

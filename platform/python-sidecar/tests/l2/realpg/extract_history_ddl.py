#!/usr/bin/env python3
"""Extract, statement by statement, the DDL for the data-plane history relations a read-only reader cannot pg_dump (it has no SELECT on them)
from migrations 1035/1036, plus every GRANT/REVOKE statement of those two migrations. Writes 02_missing_history_tables.sql and
04_grants_from_migrations.sql next to this file. Nothing is invented: every statement is a verbatim statement of the migration files."""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
MIG = HERE.parents[3] / "supabase" / "migrations"
MISSING = sys.argv[1:]  # relation names the dump could not include (one per argument)
FILES = (("1035_data_plane_l1_producer_history.sql", "data_plane_l1_owner"), ("1036_data_plane_l2_producer_generations.sql", "data_plane_l2_owner"))


def split_sql(s):
    out, buf, i, n, dollar, inq = [], [], 0, len(s), None, False
    while i < n:
        c = s[i]
        if dollar:
            if s.startswith(dollar, i):
                buf.append(dollar); i += len(dollar); dollar = None; continue
            buf.append(c); i += 1; continue
        if inq:
            buf.append(c)
            if c == "'":
                if i + 1 < n and s[i + 1] == "'":
                    buf.append("'"); i += 2; continue
                inq = False
            i += 1; continue
        if s.startswith("--", i):
            j = s.find("\n", i); i = n if j < 0 else j; continue
        if c == "'":
            inq = True; buf.append(c); i += 1; continue
        if c == "$":
            m = re.match(r"\$[A-Za-z_0-9]*\$", s[i:])
            if m:
                dollar = m.group(0); buf.append(dollar); i += len(dollar); continue
        if c == ";":
            st = "".join(buf).strip()
            if st: out.append(st)
            buf = []; i += 1; continue
        buf.append(c); i += 1
    st = "".join(buf).strip()
    if st: out.append(st)
    return out


def target(st):
    for pat in (r"CREATE TABLE( IF NOT EXISTS)?\s+(?:public\.)?(\w+)", r"CREATE( OR REPLACE)? (?:MATERIALIZED )?VIEW\s+(?:public\.)?(\w+)",
                r"CREATE (?:UNIQUE )?INDEX( IF NOT EXISTS)?\s+\w+\s+ON\s+(?:ONLY )?(?:public\.)?(\w+)",
                r"CREATE (?:CONSTRAINT )?TRIGGER\s+\w+[\s\S]*?\sON\s+(?:public\.)?(\w+)",
                r"ALTER TABLE\s+(?:ONLY\s+)?(?:IF EXISTS\s+)?(?:public\.)?(\w+)", r"COMMENT ON (?:TABLE|VIEW|COLUMN)\s+(?:public\.)?(\w+)"):
        m = re.match(pat, st, re.I)
        if m:
            return m.group(m.lastindex)
    return None


ddl, grants = [], []
for fn, role in FILES:
    for st in split_sql((MIG / fn).read_text()):
        if re.match(r"(BEGIN|COMMIT)\b", st, re.I):
            continue
        if re.match(r"(GRANT|REVOKE)\b", st, re.I):
            grants.append(f"-- {fn}\n{st};")
        elif target(st) in MISSING:
            ddl.append((role, fn, target(st), st))
with open(HERE / "02_missing_history_tables.sql", "w") as f:
    cur = None
    for role, fn, tgt, st in ddl:
        if role != cur:
            f.write(f"\nRESET ROLE;\nSET ROLE {role};\n"); cur = role
        f.write(f"-- {fn} -> {tgt}\n{st};\n\n")
    f.write("RESET ROLE;\n")
(HERE / "04_grants_from_migrations.sql").write_text("\n".join(grants) + "\n")
print(f"{len(ddl)} DDL statements, {len(grants)} grant statements")

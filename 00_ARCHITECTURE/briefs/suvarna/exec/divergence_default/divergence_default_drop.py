#!/usr/bin/env python3
"""OWNER-PATH package (SS N-347/N-349): drop the 0.0 column default of chart_facts.cross_ayanamsha_divergence_arcsec.

WHY. The column is nullable but carries `DEFAULT 0.0`, so EVERY writer that does not name it stores a "measured zero" nothing measured (and
ga_sensitive names it and writes a hard 0.0 itself: fixed separately in PR-H1). A default of 0.0 for a cross-method divergence is a false green
(CLAUDE.md section N.8). Catalog read as suvarna_reader on production (N-347): attnotnull = false, default = 0.0, double precision, table owner
data_plane_l1_owner (NOT amjis_app), so this is NOT a routine migration: it is an owner-path change (D6 in-process pattern, as
exec/reader_grants/reader_grants.py), and SQL under platform/migrations must not carry it.

WHAT. One statement, as the table's owner, under a lock timeout:

    SET LOCAL lock_timeout = '5s';
    ALTER TABLE public.chart_facts ALTER COLUMN cross_ayanamsha_divergence_arcsec DROP DEFAULT;

Metadata only: no table rewrite, no backfill (each writer's next rebuild rewrites its own rows honestly; existing 0.0 values stay until then).

GUARDS (every one is a refusal, nothing is changed):
  * public.chart_facts is an ORDINARY TABLE (pg_class.relkind = 'r'; not a view, not a partitioned table), not a partition (relispartition false)
    and takes part in no table inheritance (no pg_inherits parent, no child: a DROP DEFAULT would reach the children), and the column is
    `double precision` (format_type), so the guard says what it means and a `numeric`/`real` column or a view named chart_facts is refused;
  * the column exists, is NOT NULL = false (a NOT NULL column stops the job: SS N-347), and the table owner is data_plane_l1_owner;
  * the default is exactly `0.0`;  if it is ALREADY gone the run is an idempotent NO-OP (exit 0, nothing committed);  any other default refuses;
  * after the statement the before/after diff of the table's column defaults and NOT NULL flags is EXACTLY the one planned line, the table ACL
    is unchanged, and role membership is unchanged (a transient membership the administrator lacked is added and removed in the same transaction).

MODES
  python3 divergence_default_drop.py --dry-run                         everything in ONE transaction, then ROLLBACK
  python3 divergence_default_drop.py --apply --expect-plan H           same transaction; COMMIT only if H equals the plan hash and every check holds
  python3 divergence_default_drop.py --rollback-dry-run                the inverse (SET DEFAULT 0.0), then ROLLBACK
  python3 divergence_default_drop.py --rollback --expect-plan H2       the inverse, committed (H2 is the rollback plan hash)

Connection: local Cloud SQL proxy 127.0.0.1:5433, database `amjis`, administrator password fetched from Secret Manager INSIDE this process
(never printed). EXEC runs it in the protected window and only with the owner's approval at run time; the Engine never runs it against any
real system. The tests inject a connection to a disposable PostgreSQL and never reach connect_admin().
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys

OWNER = "data_plane_l1_owner"
TABLE = "chart_facts"
COLUMN = "cross_ayanamsha_divergence_arcsec"
OLD_DEFAULT = "0.0"
COLUMN_TYPE = "double precision"
PROJECT = "madhav-astrology"

DROP_STATEMENTS = [
    "SET LOCAL lock_timeout = '5s'",
    "ALTER TABLE public.%s ALTER COLUMN %s DROP DEFAULT" % (TABLE, COLUMN),
]
RESTORE_STATEMENTS = [
    "SET LOCAL lock_timeout = '5s'",
    "ALTER TABLE public.%s ALTER COLUMN %s SET DEFAULT %s" % (TABLE, COLUMN, OLD_DEFAULT),
]

COLUMN_SQL = """
SELECT a.attnotnull, pg_get_expr(d.adbin, d.adrelid), pg_get_userbyid(c.relowner), c.relkind::text, c.relispartition,
       format_type(a.atttypid, a.atttypmod),
       (SELECT count(*) FROM pg_inherits i WHERE i.inhparent = c.oid), (SELECT count(*) FROM pg_inherits i WHERE i.inhrelid = c.oid)
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
WHERE n.nspname = 'public' AND c.relname = %s AND a.attname = %s AND NOT a.attisdropped
"""
SHAPE_SQL = """
SELECT a.attname, a.attnotnull, COALESCE(pg_get_expr(d.adbin, d.adrelid), '')
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
WHERE n.nspname = 'public' AND c.relname = %s AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY a.attnum
"""
ACL_SQL = "SELECT COALESCE(c.relacl::text, '') FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = %s"
MEMBER_SQL = ("SELECT r.rolname, m.rolname FROM pg_auth_members am JOIN pg_roles r ON r.oid = am.roleid "
              "JOIN pg_roles m ON m.oid = am.member ORDER BY 1, 2")


class Refused(Exception):
    """A guard failed: nothing was changed."""


def plan_text(rollback: bool = False) -> str:
    stmts = RESTORE_STATEMENTS if rollback else DROP_STATEMENTS
    lines = ["-- direction: %s" % ("ROLLBACK (restore the 0.0 default)" if rollback else "DROP DEFAULT"),
             "-- owner %s: transient membership for the administrator only if missing, removed before commit" % OWNER,
             "-- every statement below runs after SET LOCAL ROLE %s" % OWNER]
    return "\n".join(lines + stmts)


def expected_diff(rollback: bool = False) -> list:
    old, new = (None, OLD_DEFAULT) if rollback else (OLD_DEFAULT, None)
    return [[COLUMN, False, old or "", new or ""]]


def plan_hash(rollback: bool = False) -> str:
    return hashlib.sha256((plan_text(rollback) + "\n" + json.dumps(expected_diff(rollback))).encode()).hexdigest()


def column_state(cur) -> dict:
    cur.execute(COLUMN_SQL, (TABLE, COLUMN))
    row = cur.fetchone()
    if row is None:
        raise Refused("public.%s.%s does not exist" % (TABLE, COLUMN))
    return {"notnull": bool(row[0]), "default": row[1], "owner": row[2], "relkind": row[3], "is_partition": bool(row[4]),
            "type": row[5], "children": int(row[6]), "parents": int(row[7])}


def shape(cur) -> list:
    cur.execute(SHAPE_SQL, (TABLE,))
    return [[r[0], bool(r[1]), r[2]] for r in cur.fetchall()]


def acl_and_members(cur):
    cur.execute(ACL_SQL, (TABLE,))
    acl = cur.fetchone()[0]
    cur.execute(MEMBER_SQL)
    return acl, sorted("%s|%s" % (r[0], r[1]) for r in cur.fetchall())


def preflight(state: dict, rollback: bool) -> str:
    """'go', or 'noop' when the table is already in the wanted state; raises Refused otherwise. The structural pins come first, so a
    view, a partitioned table, a partition, an inheritance parent or child, or a column of another type is refused even when its default
    happens to read 0.0 (or is absent: a view without a default is a refusal, never a no-op)."""
    if state["relkind"] != "r":
        raise Refused("public.%s is not an ordinary table (pg_class.relkind = %r, wanted 'r'): this package does not apply" % (TABLE, state["relkind"]))
    if state["is_partition"]:
        raise Refused("public.%s is a partition (relispartition): this package does not apply" % TABLE)
    if state["children"] or state["parents"]:
        raise Refused("public.%s takes part in table inheritance (%d child(ren), %d parent(s)): DROP DEFAULT would reach the children, so this package does not apply"
                      % (TABLE, state["children"], state["parents"]))
    if state["type"] != COLUMN_TYPE:
        raise Refused("the column type is %r, not %s: this package does not apply" % (state["type"], COLUMN_TYPE))
    if state["owner"] != OWNER:
        raise Refused("the table owner is %r, not %s: this package does not apply" % (state["owner"], OWNER))
    if state["notnull"]:
        raise Refused("the column is NOT NULL: STOP and tell SS (N-347); a default drop would make every writer that omits it fail")
    if rollback:
        if state["default"] == OLD_DEFAULT:
            return "noop"
        if state["default"] is not None:
            raise Refused("rollback expects no default, found %r" % state["default"])
        return "go"
    if state["default"] is None:
        return "noop"
    if state["default"] != OLD_DEFAULT:
        raise Refused("the default is %r, not %s: refusing to drop an unexpected default" % (state["default"], OLD_DEFAULT))
    return "go"


def run(conn, mode: str, expect_plan: str | None = None, rollback: bool = False, out=print) -> str:
    """mode 'dry-run' or 'apply'. Returns 'dry_run', 'applied', 'noop'. Raises Refused on any failed guard (the transaction is rolled back)."""
    if mode == "apply" and expect_plan != plan_hash(rollback):
        raise Refused("--expect-plan does not equal the plan hash")
    out("PLAN\n" + plan_text(rollback))
    out("plan sha256: %s" % plan_hash(rollback))
    cur = conn.cursor()
    try:
        cur.execute("SET LOCAL search_path = pg_catalog, pg_temp")
        state = column_state(cur)
        verdict = preflight(state, rollback)
        if verdict == "noop":
            out("NO-OP: the default is already %s; nothing to do" % ("0.0" if rollback else "absent"))
            conn.rollback()
            return "noop"
        before_shape, (before_acl, before_members) = shape(cur), acl_and_members(cur)
        cur.execute("SELECT session_user, quote_ident(session_user), pg_has_role(session_user, %s, 'MEMBER')", (OWNER,))
        _, quoted_user, was_member = cur.fetchone()
        if not was_member:
            cur.execute("GRANT %s TO %s" % (OWNER, quoted_user))
        cur.execute("SET LOCAL ROLE %s" % OWNER)
        for statement in (RESTORE_STATEMENTS if rollback else DROP_STATEMENTS):
            cur.execute(statement)
        cur.execute("RESET ROLE")
        if not was_member:
            cur.execute("REVOKE %s FROM %s" % (OWNER, quoted_user))
        after_shape, (after_acl, after_members) = shape(cur), acl_and_members(cur)
        changed = [a for a, b in zip(after_shape, before_shape) if a != b]
        diff = [[a[0], a[1], b[2], a[2]] for a, b in zip(after_shape, before_shape) if a != b]
        checks = {
            "same columns": [r[0] for r in after_shape] == [r[0] for r in before_shape],
            "diff exactly the one planned line": diff == expected_diff(rollback),
            "acl unchanged": after_acl == before_acl,
            "membership unchanged": after_members == before_members,
        }
        out("changed columns: %s" % [c[0] for c in changed])
        for name, ok in checks.items():
            out("%s: %s" % (name, ok))
        if not all(checks.values()):
            raise Refused("a post-change check failed: " + ", ".join(n for n, ok in checks.items() if not ok))
        if mode == "apply":
            conn.commit()
            out("COMMITTED")
            return "applied"
        conn.rollback()
        out("ROLLED BACK (dry run)")
        return "dry_run"
    except BaseException:
        conn.rollback()
        raise


def secret(name: str) -> str:
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest", "--secret", name, "--project", PROJECT],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("secret access failed")
    return r.stdout.rstrip("\r\n")


def connect_admin():
    import psycopg
    return psycopg.connect(host="127.0.0.1", port=5433, dbname="amjis", user="postgres",
                           password=secret("cloudsql-postgres-admin-password"), sslmode="disable", connect_timeout=15)


def main(argv: list) -> int:
    args = list(argv)
    rollback = args[:1] in (["--rollback"], ["--rollback-dry-run"])
    if args[:1] in (["--dry-run"], ["--rollback-dry-run"]) and len(args) == 1:
        mode, expect = "dry-run", None
    elif args[:1] in (["--apply"], ["--rollback"]) and len(args) == 3 and args[1] == "--expect-plan":
        mode, expect = "apply", args[2]
    else:
        print("usage: --dry-run | --apply --expect-plan H | --rollback-dry-run | --rollback --expect-plan H2")
        return 2
    if mode == "apply" and expect != plan_hash(rollback):
        print("REFUSED: --expect-plan does not equal the plan hash")
        return 1
    try:
        with connect_admin() as conn:
            run(conn, mode, expect, rollback)
        return 0
    except Refused as exc:
        print("REFUSED: %s" % exc)
        return 1
    except SystemExit:
        raise
    except Exception as exc:  # never show a traceback (it can carry a connection string)
        print("failed: %s" % type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""D6 owner-path executor: create the node-series unique index on public.ephemeris_daily (migration 1227's DDL).
One-shot operator tool (not product code). NEVER run without SS approval of the plan hash.

  python3 node_index_exec.py --dry-run
  python3 node_index_exec.py --apply --expect-plan <sha256> --expect-evidence <digest the dry run printed>

The real dry run / apply MUST be started through run_gated.sh (prerun_gate.py: deploy runs + builds in flight == 0).
  exit codes: 0 ok / committed; 1 apply refused or aborted; 2 dry-run refused

WHY AN OWNER PATH: the routine migration login (amjis_app, PROD_DATABASE_URL) OWNS ephemeris_daily but holds USAGE only on schema
public, and PostgreSQL requires CREATE on the schema for CREATE INDEX (and ADD CONSTRAINT UNIQUE): reproduced on a disposable
PostgreSQL ("permission denied for schema public"). The Cloud SQL admin (`postgres`, CREATEROLE, not superuser) is made a
TRANSIENT member of amjis_app (ownership of the table) and data_plane_schema_owner (CREATE on public) inside ONE transaction, runs
the DDL, and revokes both memberships before the post-snapshot. Same mechanism as ChartGrants/cg_exec.py.

THE DDL IS NOT COPIED HERE. The executor runs the text of platform/migrations/1227_ephemeris_daily_node_series_unique_index.sql
itself (with all its guards and its own structure verification); the plan hash binds that file's sha256, so the schema-of-record and
the live change cannot drift. After this commits, migration 1227 applied by the routine runner finds the index, VERIFIES it and does
no DDL.

--dry-run runs EVERY check and the real DDL inside one transaction, then ALWAYS ROLLS BACK, and prints the plan hash and the evidence
digest. --apply re-runs every check in the same transaction and COMMITs only if every check holds, --expect-plan equals the plan hash
and --expect-evidence equals the evidence digest computed from the PRE-DDL state of THIS transaction (the apply must see exactly the
state the dry run showed). Evidence (before/after snapshots, reversal SQL, SHA256SUMS) is written to the evidence directory BEFORE
the DDL; if it cannot be written the run aborts (rollback).

Admin credential: Secret Manager in-process, never printed, logged or saved. Proxy 127.0.0.1:5433. `main()` is the only place that
reaches the real database; tests call `execute()` with an injected connection factory against a disposable local Postgres.
plan hash = sha256(plan_text + "\\n" + json.dumps(DIFF)); the plan text embeds this file's sha256 and the migration file's sha256.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys

import psycopg

PROJECT = "madhav-astrology"
OWNER = "amjis_app"
SCHEMA_OWNER = "data_plane_schema_owner"
TABLE = "public.ephemeris_daily"
IDX = "ephemeris_daily_date_body_ayanamsha_node_mode_uq"
OLD_KEY_DEF = "UNIQUE (date, body, ayanamsha_id)"
MIG_FILE = "1227_ephemeris_daily_node_series_unique_index.sql"
EVIDENCE_ROOT = "/Users/Dev/suvarna-evidence/NodeSeries/d6_index"
TEST_EVIDENCE_ENV = "NODEIDX_TEST_EVIDENCE_ROOT"
TEST_MIG_ENV = "NODEIDX_TEST_MIGRATION_FILE"          # tests only: run a mutated copy of the migration text
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[5]
EXPECTED_DIFF = ["ephemeris_daily_index|%s|absent->present" % IDX]

ACL_SQL = """
SELECT c.relname, COALESCE(r.rolname,'PUBLIC'), a.privilege_type, a.is_grantable::text
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault('r', c.relowner))) a
LEFT JOIN pg_roles r ON r.oid=a.grantee
WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')
"""
OWN_SQL = ("SELECT c.relname, pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
           "WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')")
NSP_SQL = ("SELECT n.nspname, pg_get_userbyid(n.nspowner), COALESCE(n.nspacl::text,'') FROM pg_namespace n "
           "WHERE n.nspname='public'")
MEMBER_SQL = ("SELECT r.rolname, m.rolname, (to_jsonb(am) - 'oid')::text FROM pg_auth_members am "
              "JOIN pg_roles r ON r.oid=am.roleid JOIN pg_roles m ON m.oid=am.member")
RLS_SQL = ("SELECT c.relname, c.relrowsecurity::text, c.relforcerowsecurity::text FROM pg_class c "
           "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p')")
POLICY_SQL = ("SELECT c.relname, p.polname, p.polcmd::text, p.polroles::text, pg_get_expr(p.polqual,p.polrelid), "
              "coalesce(pg_get_expr(p.polwithcheck,p.polrelid),'') FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid")
IDX_SQL = "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='ephemeris_daily'"
CON_SQL = ("SELECT x.conname, x.contype::text, pg_get_constraintdef(x.oid) FROM pg_constraint x JOIN pg_class c ON c.oid = x.conrelid "
           "WHERE c.relname = 'ephemeris_daily' AND c.relnamespace = 'public'::regnamespace")
DATA_SQL = ("SELECT count(*)::text, coalesce(bit_xor(hashtextextended(t::text, 0)), 0)::text, "
            "count(*) FILTER (WHERE node_mode = 'mean')::text FROM public.ephemeris_daily t")
FOREIGN_LOCKS_SQL = ("SELECT count(*) FROM pg_locks l JOIN pg_class c ON c.oid = l.relation WHERE c.relname = 'ephemeris_daily' "
                     "AND c.relnamespace = 'public'::regnamespace AND l.granted AND l.pid <> pg_backend_pid() "
                     "AND l.mode IN ('RowExclusiveLock','ShareUpdateExclusiveLock','ShareLock','ShareRowExclusiveLock',"
                     "'ExclusiveLock','AccessExclusiveLock')")
STRUCT_SQL = ("SELECT i.indisunique AND i.indisvalid AND i.indisready AND i.indnullsnotdistinct AND am.amname = 'btree' "
              "AND i.indnatts = 4 AND i.indpred IS NULL AND i.indexprs IS NULL AND i.indoption::text = '0 0 0 0' "
              "AND NOT EXISTS (SELECT 1 FROM unnest(i.indkey::int2[], i.indclass::oid[], i.indcollation::oid[]) AS k(attnum, opc, coll) "
              "JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = k.attnum LEFT JOIN pg_opclass oc ON oc.oid = k.opc "
              "WHERE oc.oid IS NULL OR NOT oc.opcdefault OR oc.opcintype <> a.atttypid OR k.coll <> a.attcollation) "
              "FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid JOIN pg_am am ON am.oid = c.relam "
              "JOIN pg_class t ON t.oid = i.indrelid WHERE c.relname = %s AND c.relnamespace = 'public'::regnamespace "
              "AND t.relname = 'ephemeris_daily'")


class EvidenceError(Exception):
    """evidence could not be written: the run aborts (rollback)."""


# --------------------------------------------------------------------------------------------- plan text + hash
def sha_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def mig_path():
    return pathlib.Path(os.environ.get(TEST_MIG_ENV) or REPO / "platform" / "migrations" / MIG_FILE)


def render_plan(sha, msha):
    return "\n".join([
        "-- plan: create the node-series unique index %s on %s via the D6 owner path (one new index; no data, column, constraint, grant or owner change)" % (IDX, TABLE),
        "SET LOCAL search_path = pg_catalog, pg_temp",
        "SET LOCAL lock_timeout = '5s'",
        "SET LOCAL statement_timeout = '120s'",
        "SET LOCAL TimeZone = 'UTC'",
        "-- snapshot A (session user): relacl + owner of every public relation, public schema owner + ACL, relrowsecurity/relforcerowsecurity, pg_policy, pg_auth_members, ephemeris_daily indexes + constraints, row count + order-free hash + mean-row count",
        "-- pre-checks (any failure: no DDL is issued, ROLLBACK):",
        "--   P1 server_version_num >= 150000 (NULLS NOT DISTINCT)",
        "--   P2 %s exists and is owned by %s" % (TABLE, OWNER),
        "--   P3 no relation named %s exists in schema public" % IDX,
        "--   P4 the old key exists exactly as '%s' (it stays until migration 1250)" % OLD_KEY_DEF,
        "--   P5 zero node_mode='mean' rows (the index precedes the series)",
        "--   P6 no OTHER backend holds a write-level lock on the table (no bg_ephemeris rebuild in flight)",
        "-- membership: GRANT %s and %s TO <session user> only if missing; REVOKE exactly what was granted before snapshot B" % (OWNER, SCHEMA_OWNER),
        "-- evidence: before.json, reversal.sql (DROP INDEX under the same owner path), SHA256SUMS written BEFORE the DDL; unwritable: abort + ROLLBACK",
        "-- E evidence digest: sha256 of the PRE-DDL state (snapshot A hash, data fingerprint, index and constraint catalogs, P1-P6): --apply requires --expect-evidence == it",
        "-- DDL: the exact text of platform/migrations/%s (sha256 %s), executed in this transaction (its own guards and structure verification run)" % (MIG_FILE, msha),
        "-- post-checks (commit only if all hold): relacl, owner, schema owner+ACL, relrowsecurity, pg_policy and pg_auth_members equal snapshot A; the index catalog differs by exactly +%s; the constraint catalog is equal; row count, data hash and mean count equal; the index is unique, valid, ready, btree, NULLS NOT DISTINCT on (date, body, ayanamsha_id, node_mode)" % IDX,
        "-- --dry-run: the same statements, then ROLLBACK, always. --apply: COMMIT only if every check holds, --expect-plan equals this plan hash AND --expect-evidence equals check E.",
        "-- the real run is started through run_gated.sh: prerun_gate.py must read zero non-completed main deploy runs and zero planned/running/paused build_runs, else the executor is not started.",
        "-- executor: node_index_exec.py sha256 %s" % sha,
    ])


def exec_sha():
    return sha_file(__file__)


def plan_hash(sha=None, msha=None):
    text = render_plan(sha or exec_sha(), msha or sha_file(mig_path()))
    return hashlib.sha256((text + "\n" + json.dumps(EXPECTED_DIFF)).encode()).hexdigest()


# --------------------------------------------------------------------------------------------- db plumbing
def secret(name):
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest", "--secret", name, "--project", PROJECT],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("secret access failed")
    return r.stdout.rstrip("\r\n")


def connect_admin():
    return psycopg.connect(host="127.0.0.1", port=5433, dbname="amjis", user="postgres",
                           password=secret("cloudsql-postgres-admin-password"), sslmode="disable", connect_timeout=15)


def snap_catalog(cur):
    """Catalog-only reads: they need no privilege on schema public (the admin has none until the transient membership)."""
    out = {}
    for k, sql in (("acl", ACL_SQL), ("own", OWN_SQL), ("nsp", NSP_SQL), ("mem", MEMBER_SQL), ("rls", RLS_SQL),
                   ("pol", POLICY_SQL), ("idx", IDX_SQL), ("con", CON_SQL)):
        cur.execute(sql)
        out[k] = sorted(tuple(map(str, row)) for row in cur.fetchall())
    return out


def snap_data(cur):
    """Reads the table itself: only valid while the transient membership gives USAGE on public and SELECT (ownership)."""
    cur.execute(DATA_SQL)
    return list(cur.fetchone())


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def mkdir_0700(path):
    path = pathlib.Path(path)
    missing = [p for p in [path] + list(path.parents) if not p.exists()]
    for p in reversed(missing):
        p.mkdir(mode=0o700)
        os.chmod(p, 0o700)
    if not missing:
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass


def write_evidence(root, ts, before, sha, msha, phash):
    """<root>/<UTC ts>/ (0700) with before.json, reversal.sql (0600) and SHA256SUMS."""
    try:
        rootp = pathlib.Path(root)
        mkdir_0700(rootp)
        d = rootp / ts
        mkdir_0700(d)
        files = {
            "before.json": json.dumps({"plan_hash": phash, "executor_sha256": sha, "migration_sha256": msha, "snapshot_a": before},
                                      indent=2, sort_keys=True, default=str) + "\n",
            "reversal.sql": "\n".join([
                "-- REVERSAL for the creation of %s on %s (a new index; nothing else changed)." % (IDX, TABLE),
                "-- Run in ONE transaction through the same D6 owner path (transient membership of %s and %s), through run_gated.sh's gate." % (OWNER, SCHEMA_OWNER),
                "-- Only valid while no writer relies on the new key (migration 1228, the writer change and 1250 are NOT applied).",
                "-- executor sha256 %s" % sha, "BEGIN;", "SET LOCAL lock_timeout = '5s';",
                "DROP INDEX public.%s;" % IDX, "COMMIT;", ""]),
        }
        for name, text in files.items():
            fd = os.open(str(d / name), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as fh:
                fh.write(text)
        sums = {n: sha_file(d / n) for n in files}
        (d / "SHA256SUMS").write_text("".join("%s  %s\n" % (h, n) for n, h in sorted(sums.items())))
        os.chmod(d / "SHA256SUMS", 0o600)
    except OSError as exc:
        raise EvidenceError("cannot write evidence under %s (%s)" % (root, type(exc).__name__))
    return {"dir": str(d), "sha256": sums}


# --------------------------------------------------------------------------------------------- the transaction
def run_txn(conn, args, sha, msha, phash, evidence_root, now):
    apply_mode = bool(args.apply)
    cur = conn.cursor()
    checks = collections.OrderedDict()

    def chk(name, ok, detail=None):
        checks[name] = {"ok": bool(ok), "detail": detail}
        return bool(ok)

    cur.execute("SET LOCAL search_path = pg_catalog, pg_temp")
    cur.execute("SET LOCAL lock_timeout = '5s'")
    cur.execute("SET LOCAL statement_timeout = '120s'")
    cur.execute("SET LOCAL TimeZone = 'UTC'")
    a = snap_catalog(cur)

    # ---- pre-checks that need no table access
    cur.execute("SELECT current_setting('server_version_num')::int")
    chk("P1_pg15", cur.fetchone()[0] >= 150000)
    cur.execute("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE relname = 'ephemeris_daily' "
                "AND relnamespace = 'public'::regnamespace AND relkind = 'r'")
    row = cur.fetchone()
    chk("P2_owner_is_amjis_app", row is not None and row[0] == OWNER, row[0] if row else "table missing")
    cur.execute("SELECT count(*) FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relname = %s", (IDX,))
    chk("P3_index_name_free", cur.fetchone()[0] == 0)
    chk("P4_old_key_present", sum(1 for r in a["con"] if r[1] == "u" and r[2] == OLD_KEY_DEF) == 1)
    cur.execute(FOREIGN_LOCKS_SQL)
    chk("P6_no_foreign_write_lock", cur.fetchone()[0] == 0)

    if not all(c["ok"] for c in checks.values()):            # refuse BEFORE any membership grant or table read
        conn.rollback()
        return (1 if apply_mode else 2), {"plan_hash": phash, "committed": False, "checks": checks,
                                           "refused": [k for k, v in checks.items() if not v["ok"]]}

    # ---- transient membership (ownership of the table + CREATE on schema public), then the pre-checks that read the table
    cur.execute("SELECT quote_ident(session_user)")
    who = cur.fetchone()[0]
    granted = []
    for role in (OWNER, SCHEMA_OWNER):
        cur.execute("SELECT pg_has_role(session_user, %s, 'MEMBER')", (role,))
        if not cur.fetchone()[0]:
            cur.execute("GRANT %s TO %s" % (role, who))
            granted.append(role)
    data_a = snap_data(cur)
    chk("P5_no_mean_rows", data_a[2] == "0", data_a[2])
    ev_digest = digest({"snapshot_a": a, "data_a": data_a, "pre": {k: v["ok"] for k, v in checks.items()}})
    report = {"plan_hash": phash, "executor_sha256": sha, "migration_sha256": msha, "evidence_digest": ev_digest,
              "checks": checks, "committed": False}
    if apply_mode:
        chk("E_evidence_digest", args.expect_evidence == ev_digest, "dry-run digest != this transaction's pre-DDL state")
    if not all(c["ok"] for c in checks.values()):
        conn.rollback()
        report["refused"] = [k for k, v in checks.items() if not v["ok"]]
        return (1 if apply_mode else 2), report

    # ---- evidence BEFORE the DDL
    report["evidence"] = write_evidence(evidence_root, now.strftime("%Y%m%dT%H%M%S%fZ"), a, sha, msha, phash)

    # ---- DDL (the migration text itself), then revoke exactly what was granted
    cur.execute(mig_path().read_text(encoding="utf-8"))          # no parameters: multi-statement, '%' untouched
    data_b = snap_data(cur)                                      # while still a member (needs the table privileges)
    cur.execute(STRUCT_SQL, (IDX,))
    struct = cur.fetchone()
    for role in granted:
        cur.execute("REVOKE %s FROM %s" % (role, who))
    b = snap_catalog(cur)

    # ---- post-checks
    for k in ("acl", "own", "nsp", "mem", "rls", "pol"):
        chk("A_%s_unchanged" % k, a[k] == b[k])
    new_idx = [r for r in b["idx"] if r not in a["idx"]]
    gone_idx = [r for r in a["idx"] if r not in b["idx"]]
    chk("A_index_diff_is_exactly_the_new_index", len(new_idx) == 1 and new_idx[0][0] == IDX and not gone_idx, new_idx)
    chk("A_constraints_unchanged", a["con"] == b["con"])
    chk("A_data_unchanged", data_a == data_b)
    chk("A_index_structure", struct is not None and struct[0] is True)
    report["after"] = {"index_added": [r[1] for r in new_idx]}
    ok = all(c["ok"] for c in checks.values()) and apply_mode and args.expect_plan == phash
    if apply_mode and args.expect_plan != phash:
        chk("PLAN_hash_matches", False)
    if ok:
        conn.commit()
        report["committed"] = True
        return 0, report
    conn.rollback()
    if not apply_mode:
        return (0 if all(c["ok"] for c in checks.values()) else 2), report
    report["refused"] = [k for k, v in checks.items() if not v["ok"]]
    return 1, report


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", dest="dry", action="store_true")
    g.add_argument("--apply", action="store_true")
    p.add_argument("--expect-plan")
    p.add_argument("--expect-evidence")
    a = p.parse_args(argv)
    if a.apply and not (a.expect_plan and a.expect_evidence):
        p.error("--apply requires --expect-plan and --expect-evidence")
    return a


def execute(args, connect, now=None):
    """Run one transaction on `connect()`. Returns (exit_code, report)."""
    sha, msha = exec_sha(), sha_file(mig_path())
    phash = plan_hash(sha, msha)
    env = os.environ.get(TEST_EVIDENCE_ENV)
    root = env if env else EVIDENCE_ROOT
    now = now or dt.datetime.now(dt.timezone.utc)
    if args.apply and args.expect_plan != phash:
        return 1, {"plan_hash": phash, "committed": False, "refused": ["PLAN_hash_matches"]}
    conn = connect()
    try:
        try:
            return run_txn(conn, args, sha, msha, phash, root, now)
        except EvidenceError as exc:
            conn.rollback()
            return (1 if args.apply else 2), {"plan_hash": phash, "committed": False, "refused": ["EVIDENCE: %s" % exc]}
        except Exception:
            conn.rollback()
            raise
    finally:
        conn.close()


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    print("plan sha256:", plan_hash())
    try:
        code, report = execute(args, connect_admin)
    except SystemExit:
        raise
    except Exception as exc:
        print("failed: %s %s" % (type(exc).__name__, str(exc)[:200].replace("\n", " ")))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    print("COMMITTED" if report.get("committed") else ("ROLLED BACK (%s)" % ("dry run" if args.dry else "checks failed")))
    return code


if __name__ == "__main__":
    sys.exit(main())

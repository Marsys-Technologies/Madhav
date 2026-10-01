#!/usr/bin/env python3
"""DRAFT D6 in-process executor: F-A2 key widening for public.chart_divisionals (Q-L1-01, SS-ruled N-62).

STATUS: DRAFT. NEVER RUN BY THE AUTHOR. No database was written. It needs, before any use:
  * SS `APPROVED <plan hash>` for the hash a --dry-run prints (the hash binds this script's statements to
    F_A2_KEY_WIDENING_D6_PLAN_v1_0.md), and
  * the owner's standing authorization in the executing session (same terms as the I-11 RLS fix).

WHY IT IS OWNER-PATH. chart_divisionals, its unique index, the L1 capture function and both L1 attestation tables
are owned by the NOLOGIN role data_plane_l1_owner (read from the catalog 2026-10-02). `postgres` reaches them only
through a transient `GRANT data_plane_l1_owner TO postgres` + `SET LOCAL ROLE data_plane_l1_owner`, exactly as the
D6 pattern of reader_grants.py / the I-11 executor.

WHAT IT CHANGES (all in ONE transaction; commit only if every check below holds, else ROLLBACK):
  1. unique index chart_divisionals_unique_idx: six columns -> the same six + fact_subject (NULLS NOT DISTINCT);
  2. the capture trigger l1_data_plane_capture on chart_divisionals: natural-key arguments gain 'fact_subject', and
     its row in l1_data_plane_trigger_attestations is re-attested (digest of pg_get_triggerdef);
  3. the capture function l1_data_plane_capture_row(): the ga_vargas dependency-identity hunk gains the same
     fact_subject element, and its row in l1_data_plane_function_attestations is re-attested.
WHY 2 AND 3 ARE NOT OPTIONAL: complete_l1_data_plane_partition compares the writer's reported rows_inserted with the
number of DISTINCT (source_table, row_identity) it captured, and row_identity is built from the trigger's arguments.
With the index widened and the trigger not, a rebuilt ga_vargas lands ~7.7k rows per ayanamsha but only ~4.9k
distinct identities and every partition aborts ("reported N rows but protected capture contains M").

WHAT IT DOES NOT TOUCH: any chart_divisionals row; RLS; policies; ACLs; memberships; any other table, index,
trigger or function. The two attestation UPDATEs bypass the append-only trigger by DISABLE/ENABLE TRIGGER inside the
same transaction (the same mechanism data_plane_protected_roles.db.test.ts uses); the end-state check proves the
trigger is enabled again and that exactly the two intended attestation rows changed.

  --count                       read-only: prints the pre-state and the plan hash, always ROLLBACK
  --dry-run                     applies the plan inside one transaction, runs every check, then ROLLBACK
  --apply --expect-plan H       same transaction; COMMIT only if H == plan hash and every check holds

The administrator password is fetched from Secret Manager inside this process and never printed or saved.
Connection: local Cloud SQL proxy 127.0.0.1:5433, database amjis.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

OWNER = "data_plane_l1_owner"
TABLE = "chart_divisionals"
INDEX = "chart_divisionals_unique_idx"
NEW_INDEX_TMP = "chart_divisionals_unique_idx_f_a2"
OLD_COLS = ("chart_id", "graha", "ayanamsha_id", "varga", "fact_category", "fact_key")
NEW_COLS = OLD_COLS + ("fact_subject",)
CAPTURE_FN = "public.l1_data_plane_capture_row()"
CAPTURE_FN_SIG = "l1_data_plane_capture_row()"
TRIGGER = "l1_data_plane_capture"
TRG_ATT = "public.l1_data_plane_trigger_attestations"
TRG_ATT_IMMUTABLE = "l1_data_plane_trigger_attestations_immutable"
FN_ATT = "public.l1_data_plane_function_attestations"
FN_ATT_IMMUTABLE = "l1_data_plane_function_attestations_immutable"
PROJECT = "madhav-astrology"
PLAN_DOC = pathlib.Path(__file__).with_name("F_A2_KEY_WIDENING_D6_PLAN_v1_0.md")

# The one hunk of the capture function that spells the chart_divisionals natural key (migration 1035, the
# ga_condition_composite dependency identities). Read from the live function on 2026-10-02: it occurs exactly once.
HUNK_OLD_KEY = "                  'fact_key=' || cd.fact_key\n                )\n              ) ORDER BY cd.varga, cd.fact_category, cd.fact_key\n"
HUNK_NEW_KEY = (
    "                  'fact_key=' || cd.fact_key,\n"
    "                  'fact_subject=' || COALESCE(cd.fact_subject, '<null>')\n"
    "                )\n"
    "              ) ORDER BY cd.varga, cd.fact_category, cd.fact_key, cd.fact_subject\n"
)

# every check below compares a before-snapshot with an after-snapshot of ALL public relations/triggers/functions
EXPECTED_DIFF = {
    "index": [f"{TABLE}|{INDEX}|6col->7col"],
    "trigger": [f"{TABLE}|{TRIGGER}|args 6->7"],
    "trigger_attestation": [f"{TABLE}|{TRIGGER}|digest"],
    "function": [f"{CAPTURE_FN_SIG}|definition|+fact_subject in ga_vargas dependency identity"],
    "function_attestation": [f"{CAPTURE_FN_SIG}|digest"],
    "rls_policy_acl_membership_rowdata": [],
}

SNAP_SQL = {
    "index": ("SELECT i.indexname, i.indexdef FROM pg_indexes i WHERE i.schemaname='public' ORDER BY 1"),
    "trigger": ("SELECT c.relname, t.tgname, pg_get_triggerdef(t.oid,true), t.tgenabled::text FROM pg_trigger t "
                "JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='public' AND NOT t.tgisinternal ORDER BY 1,2"),
    "trigger_attestation": (f"SELECT table_name, trigger_name, trigger_type::text, enabled::text, function_oid::text, "
                            f"function_signature, definition_digest FROM {TRG_ATT} ORDER BY 1,2"),
    "function": ("SELECT p.oid::regprocedure::text, md5(pg_get_functiondef(p.oid)), pg_get_userbyid(p.proowner), "
                 "p.prosecdef::text, COALESCE(p.proconfig::text,''), COALESCE(p.proacl::text,'') FROM pg_proc p "
                 "JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' "
                 "AND (p.proname LIKE 'l1\\_data\\_plane\\_%' OR p.proname LIKE 'l2\\_data\\_plane\\_%') ORDER BY 1"),
    "function_attestation": (f"SELECT function_signature, definition_digest, owner_name, security_definer::text, "
                             f"COALESCE(config::text,'') FROM {FN_ATT} ORDER BY 1"),
    "acl": ("SELECT c.relname, COALESCE(r.rolname,'PUBLIC'), a.privilege_type FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault('r', c.relowner))) a "
            "LEFT JOIN pg_roles r ON r.oid=a.grantee WHERE n.nspname='public' "
            "AND c.relkind IN ('r','p','v','m','f') ORDER BY 1,2,3"),
    "membership": ("SELECT r.rolname, m.rolname FROM pg_auth_members am JOIN pg_roles r ON r.oid=am.roleid "
                   "JOIN pg_roles m ON m.oid=am.member ORDER BY 1,2"),
    "rls": ("SELECT c.relname, c.relrowsecurity::text, c.relforcerowsecurity::text FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p') ORDER BY 1"),
    "policy": ("SELECT c.relname, p.polname, p.polcmd::text, p.polroles::text FROM pg_policy p "
               "JOIN pg_class c ON c.oid=p.polrelid ORDER BY 1,2"),
}
ROWDATA_SQL = ("SELECT chart_id::text, count(*), md5(string_agg(id::text, ',' ORDER BY id)) "
               f"FROM public.{TABLE} GROUP BY chart_id ORDER BY chart_id")


def secret(name: str) -> str:
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest", "--secret", name, "--project", PROJECT],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("secret access failed")
    return r.stdout.rstrip("\r\n")


def plan_hash() -> str:
    """Binds this script's statements and expected diff to the reviewed plan document."""
    body = PLAN_DOC.read_text(encoding="utf-8") + "\n" + json.dumps(EXPECTED_DIFF, sort_keys=True)
    body += "\n" + json.dumps([HUNK_OLD_KEY, HUNK_NEW_KEY, list(OLD_COLS), list(NEW_COLS)])
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def snap(cur) -> dict:
    out = {}
    for k, sql in SNAP_SQL.items():
        cur.execute(sql)
        out[k] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    cur.execute(ROWDATA_SQL)
    out["rowdata"] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    return out


def is_member(cur, role: str) -> bool:
    cur.execute("SELECT pg_has_role(current_user, %s, 'MEMBER')", (role,))
    return bool(cur.fetchone()[0])


def preconditions(cur) -> list[str]:
    """Refuse (return reasons) unless the table is quiescent. Admin reads; nothing is written."""
    problems = []
    cur.execute("SELECT count(*) FROM public.build_runs WHERE state IN ('planned','running','paused')")
    if cur.fetchone()[0]:
        problems.append("build_runs in planned/running/paused exist (merge/apply gate PF-1)")
    cur.execute("SELECT count(*) FROM public.l1_data_plane_generations WHERE status = 'building'")
    if cur.fetchone()[0]:
        problems.append("an L1 data-plane generation is still 'building'")
    cur.execute(f"SELECT indexdef FROM pg_indexes WHERE schemaname='public' AND indexname=%s", (INDEX,))
    row = cur.fetchone()
    want = "(" + ", ".join(OLD_COLS) + ") NULLS NOT DISTINCT"
    if not row or want not in row[0]:
        problems.append(f"{INDEX} is not the expected six-column index: {row[0] if row else None}")
    cur.execute("SELECT pg_get_triggerdef(t.oid,true) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
                "WHERE c.relname=%s AND t.tgname=%s", (TABLE, TRIGGER))
    row = cur.fetchone()
    if not row or "'fact_key')" not in row[0] or "fact_subject" in row[0]:
        problems.append(f"capture trigger is not the expected six-argument trigger: {row[0] if row else None}")
    cur.execute("SELECT pg_get_functiondef(%s::regprocedure)", (CAPTURE_FN,))
    fn = cur.fetchone()[0]
    if fn.count(HUNK_OLD_KEY) != 1 or "fact_subject=" in fn:
        problems.append("capture function does not contain the dependency-identity hunk exactly once")
    return problems


def apply_plan(cur) -> dict:
    """The statements. Runs as data_plane_l1_owner (caller has done SET LOCAL ROLE)."""
    # 1. index: build the wider unique index first, drop the old, rename: the name the writer's preflight reads stays.
    cur.execute(f"CREATE UNIQUE INDEX {NEW_INDEX_TMP} ON public.{TABLE} ({', '.join(NEW_COLS)}) NULLS NOT DISTINCT")
    cur.execute(f"DROP INDEX public.{INDEX}")
    cur.execute(f"ALTER INDEX public.{NEW_INDEX_TMP} RENAME TO {INDEX}")
    # 2. capture trigger: same event/timing/function, seven natural-key arguments
    cur.execute(f"DROP TRIGGER {TRIGGER} ON public.{TABLE}")
    args = ", ".join("'%s'" % c for c in NEW_COLS)
    cur.execute(f"CREATE TRIGGER {TRIGGER} AFTER INSERT OR UPDATE ON public.{TABLE} "
                f"FOR EACH ROW EXECUTE FUNCTION {CAPTURE_FN.split('(')[0]}({args})")
    # 3. capture function: CREATE OR REPLACE from its own live definition with exactly one hunk changed
    cur.execute("SELECT pg_get_functiondef(%s::regprocedure)", (CAPTURE_FN,))
    old_def = cur.fetchone()[0]
    assert old_def.count(HUNK_OLD_KEY) == 1
    new_def = old_def.replace(HUNK_OLD_KEY, HUNK_NEW_KEY)
    assert new_def != old_def and new_def.count("fact_subject=") == 1
    cur.execute(new_def)
    # 4. re-attest exactly the two rows whose digests moved (append-only trigger off, then on, same transaction)
    cur.execute(f"ALTER TABLE {TRG_ATT} DISABLE TRIGGER {TRG_ATT_IMMUTABLE}")
    cur.execute(
        f"UPDATE {TRG_ATT} a SET definition_digest = encode(public.digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex') "
        "FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
        "WHERE a.table_name=%s AND a.trigger_name=%s AND c.relname=a.table_name AND t.tgname=a.trigger_name",
        (TABLE, TRIGGER))
    trg_rows = cur.rowcount
    cur.execute(f"ALTER TABLE {TRG_ATT} ENABLE TRIGGER {TRG_ATT_IMMUTABLE}")
    cur.execute(f"ALTER TABLE {FN_ATT} DISABLE TRIGGER {FN_ATT_IMMUTABLE}")
    cur.execute(
        f"UPDATE {FN_ATT} a SET definition_digest = encode(public.digest(pg_get_functiondef(p.oid),'sha256'),'hex') "
        "FROM pg_proc p WHERE a.function_signature=%s AND p.oid=to_regprocedure('public.'||a.function_signature)",
        (CAPTURE_FN_SIG,))
    fn_rows = cur.rowcount
    cur.execute(f"ALTER TABLE {FN_ATT} ENABLE TRIGGER {FN_ATT_IMMUTABLE}")
    return {"trigger_attestation_rows": trg_rows, "function_attestation_rows": fn_rows}


def check_after(cur, before: dict, after: dict, counts: dict) -> list[str]:
    """Every commit condition. Returns the list of failures (empty = commit allowed)."""
    bad = []
    if counts != {"trigger_attestation_rows": 1, "function_attestation_rows": 1}:
        bad.append(f"attestation UPDATE row counts {counts}")
    # exactly the intended objects moved
    for key, expected_changed in (("index", 1), ("trigger", 1), ("trigger_attestation", 1),
                                  ("function", 1), ("function_attestation", 1)):
        removed, added = before[key] - after[key], after[key] - before[key]
        if len(removed) != expected_changed or len(added) != expected_changed:
            bad.append(f"{key}: expected exactly {expected_changed} changed entry, got -{len(removed)} +{len(added)}")
    for key in ("acl", "membership", "rls", "policy", "rowdata"):
        if before[key] != after[key]:
            bad.append(f"{key} changed")
    # the new index is the right one and is usable
    cur.execute("SELECT i.indisunique, i.indisvalid, i.indnullsnotdistinct, "
                "array(SELECT a.attname::text FROM unnest(i.indkey) WITH ORDINALITY k(attnum,ord) "
                "JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=k.attnum ORDER BY k.ord) "
                "FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE c.relname=%s", (INDEX,))
    row = cur.fetchone()
    if not row or not (row[0] and row[1] and row[2] and tuple(row[3]) == NEW_COLS):
        bad.append(f"new index shape wrong: {row}")
    # both attestation triggers are enabled again; function owner/secdef/config unchanged (covered by 'function')
    cur.execute("SELECT count(*) FROM pg_trigger WHERE tgname = ANY(%s) AND tgenabled = 'O'",
                ([TRG_ATT_IMMUTABLE, FN_ATT_IMMUTABLE],))
    if cur.fetchone()[0] != 2:
        bad.append("an attestation append-only trigger is not enabled after the plan")
    # the gate's own comparisons, in SQL, for the two re-attested rows
    cur.execute(
        f"SELECT count(*) FROM {TRG_ATT} a JOIN pg_class c ON c.relname=a.table_name JOIN pg_trigger t "
        "ON t.tgrelid=c.oid AND t.tgname=a.trigger_name WHERE a.table_name=%s AND a.trigger_name=%s "
        "AND a.definition_digest=encode(public.digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex') "
        "AND a.trigger_type=t.tgtype AND a.enabled=t.tgenabled AND a.function_oid=t.tgfoid", (TABLE, TRIGGER))
    if cur.fetchone()[0] != 1:
        bad.append("trigger attestation does not match the live trigger")
    cur.execute(
        f"SELECT count(*) FROM {FN_ATT} a JOIN pg_proc p ON p.oid=to_regprocedure('public.'||a.function_signature) "
        "WHERE a.function_signature=%s AND a.definition_digest=encode(public.digest(pg_get_functiondef(p.oid),'sha256'),'hex') "
        "AND a.owner_name=pg_get_userbyid(p.proowner) AND a.security_definer=p.prosecdef "
        "AND a.config IS NOT DISTINCT FROM p.proconfig", (CAPTURE_FN_SIG,))
    if cur.fetchone()[0] != 1:
        bad.append("function attestation does not match the live function")
    return bad


def run(conn, mode: str) -> bool:
    """Returns True only when the transaction may be committed (mode apply, all checks hold)."""
    cur = conn.cursor()
    cur.execute("SET LOCAL search_path = pg_catalog, pg_temp")
    cur.execute("SET LOCAL lock_timeout = '5s'")
    cur.execute("SET LOCAL statement_timeout = '120s'")
    granted = False
    if not is_member(cur, OWNER):
        cur.execute(f"GRANT {OWNER} TO CURRENT_USER")
        granted = True
    problems = preconditions(cur)
    print("preconditions:", "OK" if not problems else problems)
    if mode == "count":
        return False
    if problems:
        return False
    before = snap(cur)
    cur.execute(f"SET LOCAL ROLE {OWNER}")
    counts = apply_plan(cur)
    cur.execute("RESET ROLE")
    if granted:
        cur.execute(f"REVOKE {OWNER} FROM CURRENT_USER")
    after = snap(cur)
    bad = check_after(cur, before, after, counts)
    print("commit conditions:", "ALL HOLD" if not bad else bad)
    return not bad and mode == "apply"


def main(argv: list[str]) -> int:
    import psycopg  # imported late so a plan-hash --print needs no driver
    h = plan_hash()
    print("plan sha256:", h)
    if argv == ["--print-hash"]:
        return 0
    if argv == ["--count"]:
        mode, expect = "count", None
    elif argv == ["--dry-run"]:
        mode, expect = "dry-run", None
    elif len(argv) == 3 and argv[0] == "--apply" and argv[1] == "--expect-plan":
        mode, expect = "apply", argv[2]
    else:
        raise SystemExit("usage: --print-hash | --count | --dry-run | --apply --expect-plan <hash>")
    if mode == "apply" and expect != h:
        raise SystemExit("REFUSED: --expect-plan does not equal the plan hash")
    with psycopg.connect(host="127.0.0.1", port=5433, dbname="amjis", user="postgres",
                         password=secret("cloudsql-postgres-admin-password"), sslmode="disable",
                         connect_timeout=15) as conn:
        ok = run(conn, mode)
        if ok:
            conn.commit()
            print("COMMITTED")
            return 0
        conn.rollback()
        print("ROLLED BACK (%s)" % {"count": "read-only", "dry-run": "dry run", "apply": "checks failed"}[mode])
        return 1 if mode == "apply" else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:  # never show a traceback (could expose connection details)
        print("failed: %s %s" % (type(exc).__name__, str(exc)[:200].replace("\n", " ")))
        sys.exit(1)

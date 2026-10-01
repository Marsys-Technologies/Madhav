#!/usr/bin/env python3
"""DRAFT D6 in-process executor: F-A2 key widening for public.chart_divisionals (Q-L1-01, SS-ruled N-62).

STATUS: DRAFT. NEVER RUN BY THE AUTHOR AGAINST ANY REAL SYSTEM. It needs, before any apply:
  * SS `APPROVED <plan hash>` for the hash a --dry-run prints (the hash binds THIS SCRIPT's source and
    F_A2_KEY_WIDENING_D6_PLAN_v1_0.md together), and
  * the owner's standing authorization in the executing session (same terms as the I-11 RLS fix).

WHY IT IS OWNER-PATH. chart_divisionals, its unique index, the L1 capture function and both L1 attestation tables
are owned by the NOLOGIN role data_plane_l1_owner (catalog, 2026-10-02). The administrator reaches them only through a
transient `GRANT data_plane_l1_owner TO CURRENT_USER` + `SET LOCAL ROLE data_plane_l1_owner`, as in the I-11 executor.

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
same transaction (the mechanism data_plane_protected_roles.db.test.ts uses); the end-state check proves the trigger is
enabled again and that exactly the two intended attestation rows changed.

HARD RULE: THE WRITER DEPLOYS FIRST, THEN THIS PLAN. Never the reverse. A NEW writer on the six-column index fails
closed (assert_unique_key_grain raises before any DELETE). An OLD writer on the seven-column index returns 0 rows with
no exception and DELETES the scope's prior rows (reproduced by the independent review: 5 existing rows went to 0).
Before this plan applies, any ga_vargas build that starts fails closed. --apply therefore REQUIRES --writer-commit <sha>
and checks, read-only, that the Cloud Run job brahma-build-pipeline-job runs the image tagged with that commit and that
nirmana-writer-digests.json at that commit carries the ga_vargas digest this plan was frozen against.

DEPLOY GATE (the reviewed blocker): data-plane-ownership-status.ts recomputes the trigger and function digests under the
DEFAULT search_path. pg_get_triggerdef is search_path sensitive (under `pg_catalog, pg_temp` it prints
`ON public.chart_divisionals ... EXECUTE FUNCTION public.l1_data_plane_capture_row(`; under the default path it prints the
unqualified text), so a digest stored from the qualified text fails the gate after COMMIT while a check that recomputes
under the same path says ALL HOLD. This executor therefore (a) computes everything under SEARCH_PATH
`pg_catalog, public, pg_temp`, (b) COPIES the gate's own trigger-shape, trigger-surface and function-digest queries and
runs them under GATE_SEARCH_PATH (`public`) before AND after the plan as an explicit commit condition, and (c) prints the
stored, gate-side and executor-path digests in --dry-run.

LOCKS: the dry run is data-safe but NOT lock-free. It takes the same locks as the apply: SHARE on chart_divisionals for the
index build, then ACCESS EXCLUSIVE at DROP INDEX / DROP TRIGGER; lock_timeout 5s bounds the wait; concurrent reads and
writes of chart_divisionals block for the duration (an index build over ~71k rows is expected in the low hundreds of ms).
Run the dry run in the SAME quiet window as the apply (deploy idle, zero runs) and report both windows' timestamps.

GUARDS (any failure = print the reason and ROLLBACK; nothing else is touched):
  * ANY build_run in planned/running/paused, on ANY chart (no chart filter), and any L1 generation in 'building';
  * any data_plane_builder session that is active or idle-in-transaction;
  * the live index / trigger / function are not exactly the pre-state this plan was written against;
  * public.digest(text,text) does not resolve (pgcrypto's schema is printed; production: extension pgcrypto in `public`).
  If ANOTHER workstream's run appears in the gap, the guard refuses and this script never touches that run: it only
  reads build_runs, it never writes it.

MODES
  --print-hash                  print the frozen plan hash (needs no database)
  --count                       read-only: preconditions + pre-state, always ROLLBACK
  --dry-run [--writer-commit S] applies the plan inside one transaction, prints the exact catalog diff in readable
                                form, the gate-side digests, fires the identity probe, runs every commit condition,
                                then ROLLBACK; prints the same plan hash and UTC start/end timestamps
  --apply --expect-plan H --writer-commit S
                                same transaction; COMMIT only if H == plan hash, the writer image check passes and
                                every check holds; prints the UTC start/end timestamps of the window (report to SS)

SEQUENCING (see the plan, section 6): the WRITER deploys FIRST (it fails closed on a missing seven-column index), THEN
this plan runs. Between the index swap and the writer deploy any ga_vargas build fails either way, so the gap is kept
minimal and its timestamps are reported.

The administrator password is fetched from Secret Manager inside this process and never printed or saved.
Connection: local Cloud SQL proxy 127.0.0.1:5433, database amjis.
"""
from __future__ import annotations

import datetime
import difflib
import hashlib
import json
import pathlib
import re
import subprocess
import sys

OWNER = "data_plane_l1_owner"
BUILDER = "data_plane_builder"
APP_OWNER = "amjis_app"  # owns build_runs; the administrator holds no table privilege and reads only as an owner
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
REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
SEARCH_PATH = "pg_catalog, public, pg_temp"  # keeps pg_get_triggerdef unqualified, as under the gate's session
GATE_SEARCH_PATH = "public"                  # what the gate's pooled session resolves names with (default path)
# the writer this plan was frozen against: ga_vargas in platform/src/generated/nirmana-writer-digests.json
WRITER_DIGEST = "0d4f8a14a23fdd47efaea4c51346417ec18908de3d1047746e7036fa1fdb4c11"
WRITER_IMAGE_JOB = "brahma-build-pipeline-job"
WRITER_IMAGE_REGION = "asia-south1"
# data-plane-ownership-status.ts passes exactly these lifecycle functions to its function-digest query
GATE_LIFECYCLE_FUNCTIONS = (
    "open_l1_data_plane_generation", "capture_l1_data_plane_dasha_partition", "authorize_l1_chart_facts_delete",
    "complete_l1_data_plane_partition", "select_l1_data_plane_generation", "rollback_l1_data_plane_generation",
    "assert_l2_msr_delete_safe", "bind_l2_exact_inputs", "open_l2_data_plane_generation",
    "complete_l2_data_plane_partition", "select_l2_data_plane_generation", "rollback_l2_data_plane_generation",
)

# The one hunk of the capture function that spells the chart_divisionals natural key (migration 1035, the
# ga_condition_composite dependency identities). Read from the live function on 2026-10-02: it occurs exactly once.
HUNK_OLD_KEY = "                  'fact_key=' || cd.fact_key\n                )\n              ) ORDER BY cd.varga, cd.fact_category, cd.fact_key\n"
HUNK_NEW_KEY = (
    "                  'fact_key=' || cd.fact_key,\n"
    "                  'fact_subject=' || COALESCE(cd.fact_subject, '<null>')\n"
    "                )\n"
    "              ) ORDER BY cd.varga, cd.fact_category, cd.fact_key, cd.fact_subject\n"
)

# every check below compares a before-snapshot with an after-snapshot of ALL public indexes/triggers/l1_,l2_ functions
EXPECTED_DIFF = {
    "index": [f"{TABLE}|{INDEX}|6col->7col"],
    "trigger": [f"{TABLE}|{TRIGGER}|args 6->7"],
    "trigger_attestation": [f"{TABLE}|{TRIGGER}|digest"],
    "function": [f"{CAPTURE_FN_SIG}|definition|+fact_subject in ga_vargas dependency identity"],
    "function_attestation": [f"{CAPTURE_FN_SIG}|digest"],
    "rls_policy_acl_membership_rowdata": [],
    "identity_probe": "landed == distinct identities under the live widened trigger arguments (84 == 84; legacy 6 args: 18)",
    "deploy_gate": "the gate's own trigger-shape, trigger-surface and function-digest queries are false before AND after, under search_path public",
    "writer_first": "--apply requires --writer-commit: job image tag == commit and ga_vargas digest at that commit == WRITER_DIGEST",
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


def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def secret(name: str) -> str:
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest", "--secret", name, "--project", PROJECT],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("secret access failed")
    return r.stdout.rstrip("\r\n")


def plan_hash() -> str:
    """The FROZEN hash: this script's own bytes + the reviewed plan document + the expected diff."""
    body = PLAN_DOC.read_text(encoding="utf-8") + "\n" + json.dumps(EXPECTED_DIFF, sort_keys=True)
    body += "\n" + hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------------------------------------------------
# the deploy gate's own queries (platform/scripts/data-plane-ownership-status.ts), copied, parameterised by table list
# ------------------------------------------------------------------------------------------------------------------
GATE_TRIGGER_SHAPE = """
SELECT EXISTS (
  SELECT 1 FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
  JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_proc p ON p.oid=t.tgfoid
  WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname=ANY(%(tables)s::text[])
    AND (
      (t.tgname='l1_data_plane_mutation_guard' AND (t.tgtype<>31 OR p.oid<>'public.l1_data_plane_guard_active_mutation()'::regprocedure))
      OR (t.tgname='l1_data_plane_capture' AND (t.tgtype<>21 OR p.oid<>'public.l1_data_plane_capture_row()'::regprocedure))
      OR (t.tgname='l2_data_plane_mutation_guard' AND (t.tgtype<>31 OR p.oid<>'public.l2_data_plane_guard_active_mutation()'::regprocedure))
      OR (t.tgname='l2_data_plane_capture' AND (t.tgtype<>21 OR p.oid<>'public.l2_data_plane_capture_row()'::regprocedure))
    )
) OR (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
       JOIN pg_namespace n ON n.oid=c.relnamespace
       WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname=ANY(%(tables)s::text[])
         AND t.tgname IN ('l1_data_plane_mutation_guard','l2_data_plane_mutation_guard')) <> cardinality(%(tables)s::text[])
AS unsafe
"""
GATE_TRIGGER_SURFACE = """
WITH expected AS (
  SELECT * FROM public.l1_data_plane_trigger_attestations
  UNION ALL SELECT * FROM public.l2_data_plane_trigger_attestations
), actual AS (
  SELECT c.relname table_name,t.tgname trigger_name,t.tgtype trigger_type,
         t.tgenabled enabled,t.tgfoid function_oid,t.tgfoid::regprocedure::text function_signature,
         encode(digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex') definition_digest
  FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
  JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname=ANY(%(tables)s::text[])
)
SELECT EXISTS (
  SELECT 1 FROM actual a FULL JOIN expected e
    ON a.table_name=e.table_name AND a.trigger_name=e.trigger_name
   AND a.trigger_type=e.trigger_type AND a.enabled=e.enabled
   AND a.function_oid=e.function_oid AND a.function_signature=e.function_signature
   AND a.definition_digest=e.definition_digest
  WHERE a.table_name IS NULL OR e.table_name IS NULL
) AS unsafe
"""
GATE_FUNCTION_DIGESTS = """
SELECT EXISTS (
  SELECT 1 FROM (
    SELECT * FROM public.l1_data_plane_function_attestations
    UNION ALL SELECT * FROM public.l2_data_plane_function_attestations
  ) a
  LEFT JOIN pg_proc p ON p.oid=to_regprocedure('public.'||a.function_signature)
  WHERE p.oid IS NULL OR a.definition_digest<>encode(digest(pg_get_functiondef(p.oid),'sha256'),'hex')
    OR a.owner_name<>pg_get_userbyid(p.proowner)
    OR a.security_definer<>p.prosecdef
    OR a.config IS DISTINCT FROM p.proconfig
) OR EXISTS (
  SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  JOIN pg_roles owner ON owner.oid=p.proowner
  WHERE n.nspname='public' AND owner.rolname=ANY(%(owners)s::text[])
    AND (p.proname LIKE 'l1_data_plane_%%' OR p.proname LIKE 'l2_data_plane_%%'
      OR p.proname=ANY(%(lifecycle)s::text[]))
    AND NOT EXISTS (
      SELECT 1 FROM (
        SELECT function_signature FROM public.l1_data_plane_function_attestations
        UNION ALL SELECT function_signature FROM public.l2_data_plane_function_attestations
      ) a WHERE p.oid=to_regprocedure('public.'||a.function_signature)
    )
) AS unsafe
"""
GATE_DIGEST_SHOW = """
SELECT a.definition_digest,
       encode(digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex')
FROM public.l1_data_plane_trigger_attestations a
JOIN pg_class c ON c.relname=a.table_name JOIN pg_trigger t ON t.tgrelid=c.oid AND t.tgname=a.trigger_name
WHERE a.table_name=%s AND a.trigger_name=%s
"""
GATE_FN_DIGEST_SHOW = """
SELECT a.definition_digest, encode(digest(pg_get_functiondef(p.oid),'sha256'),'hex')
FROM public.l1_data_plane_function_attestations a
JOIN pg_proc p ON p.oid=to_regprocedure('public.'||a.function_signature)
WHERE a.function_signature=%s
"""


def load_gate_tables(root: pathlib.Path = REPO_ROOT) -> list[str]:
    """L1_ACTIVE_TABLES + L2_ACTIVE_TABLES, parsed from the gate's own source so they cannot drift from it."""
    text = (root / "platform/scripts/data-plane-ownership-preflight.ts").read_text(encoding="utf-8")
    out: list[str] = []
    for name in ("L1_ACTIVE_TABLES", "L2_ACTIVE_TABLES"):
        m = re.search(r"export const %s = \[(.*?)\] as const" % name, text, re.S)
        if not m:
            raise SystemExit(f"cannot parse {name} from data-plane-ownership-preflight.ts")
        out += re.findall(r"'([a-z0-9_]+)'", m.group(1))
    return out


def gate_mirror(cur, tables: list[str] | None = None) -> dict:
    """Run the deploy gate's OWN trigger and function digest queries, as the gate's session would resolve names
    (GATE_SEARCH_PATH), and return the three `unsafe` flags plus the capture trigger / function digests."""
    tables = tables if tables is not None else load_gate_tables()
    cur.execute(f"SET LOCAL ROLE {OWNER}")  # the attestation tables are owner-readable only
    cur.execute(f"SET LOCAL search_path = {GATE_SEARCH_PATH}")
    out: dict = {}
    cur.execute(GATE_TRIGGER_SHAPE, {"tables": tables})
    out["trigger_shape_unsafe"] = bool(cur.fetchone()[0])
    cur.execute(GATE_TRIGGER_SURFACE, {"tables": tables})
    out["trigger_surface_unsafe"] = bool(cur.fetchone()[0])
    cur.execute(GATE_FUNCTION_DIGESTS, {"owners": ["data_plane_l1_owner", "data_plane_l2_owner"],
                                        "lifecycle": list(GATE_LIFECYCLE_FUNCTIONS)})
    out["function_digests_unsafe"] = bool(cur.fetchone()[0])
    cur.execute(GATE_DIGEST_SHOW, (TABLE, TRIGGER))
    row = cur.fetchone()
    out["trigger_digest_stored"], out["trigger_digest_gate_side"] = (row[0], row[1]) if row else (None, None)
    cur.execute(GATE_FN_DIGEST_SHOW, (CAPTURE_FN_SIG,))
    row = cur.fetchone()
    out["function_digest_stored"], out["function_digest_gate_side"] = (row[0], row[1]) if row else (None, None)
    cur.execute(f"SET LOCAL search_path = {SEARCH_PATH}")
    cur.execute("RESET ROLE")
    return out


def gate_red(g: dict) -> list[str]:
    return [k for k in ("trigger_shape_unsafe", "trigger_surface_unsafe", "function_digests_unsafe") if g[k]]


def _run_cmd(argv: list[str]) -> str:
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{argv[0]} failed: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def writer_check(commit: str | None, run_cmd=_run_cmd) -> tuple[list[str], str]:
    """HARD RULE: the new writer is deployed before this plan. Read-only: the Cloud Run job's image tag and the
    ga_vargas digest recorded at that commit. Returns (problems, human line)."""
    if not commit:
        return ["--writer-commit <sha> is required: the writer must be deployed BEFORE this plan applies"], "NOT CHECKED"
    try:
        image = run_cmd(["gcloud", "run", "jobs", "describe", WRITER_IMAGE_JOB, "--project", PROJECT,
                         "--region", WRITER_IMAGE_REGION,
                         "--format=value(spec.template.spec.template.spec.containers[0].image)"])
        tag = image.rsplit(":", 1)[-1] if ":" in image else ""
        inventory = run_cmd(["git", "-C", str(REPO_ROOT), "show",
                             f"{commit}:platform/src/generated/nirmana-writer-digests.json"])
        digest = json.loads(inventory)["writers"]["ga_vargas"]
    except Exception as exc:  # fail closed: an unverifiable writer is not a deployed writer
        return [f"writer image check failed: {type(exc).__name__}: {str(exc)[:160]}"], "UNVERIFIED"
    problems = []
    if not tag or not (tag == commit or commit.startswith(tag) or tag.startswith(commit)):
        problems.append(f"job {WRITER_IMAGE_JOB} runs image tag {tag!r}, not commit {commit[:12]}")
    if digest != WRITER_DIGEST:
        problems.append(f"ga_vargas digest at {commit[:12]} is {digest[:12]}..., this plan was frozen against {WRITER_DIGEST[:12]}...")
    return problems, f"image tag {tag[:12]!r}; ga_vargas digest at {commit[:12]} = {digest[:12]}..."


def snap(cur) -> dict:
    """Snapshot read AS the owner: the administrator holds no table privilege (I-11 incident review), and the
    attestation tables and chart_divisionals are owner-readable. Catalog views are readable by every role."""
    out = {}
    cur.execute(f"SET LOCAL ROLE {OWNER}")
    for k, sql in SNAP_SQL.items():
        cur.execute(sql)
        out[k] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    cur.execute(ROWDATA_SQL)
    out["rowdata"] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    cur.execute("RESET ROLE")
    return out


def is_member(cur, role: str) -> bool:
    cur.execute("SELECT pg_has_role(current_user, %s, 'MEMBER')", (role,))
    return bool(cur.fetchone()[0])


def preconditions(cur) -> list[str]:
    """Refuse (return reasons) unless the table is quiescent. Reads only; nothing is written, no run is touched."""
    problems = []
    # ANY chart, ANY layer: no chart filter. build_runs.state is CHECK-constrained to
    # planned/running/paused/completed/stopped/failed, so these three are exactly the non-terminal states.
    cur.execute(f"SET LOCAL ROLE {APP_OWNER}")
    cur.execute("SELECT count(*), COALESCE(string_agg(DISTINCT left(chart_id::text,8) || ':' || state, ', '), '') "
                "FROM public.build_runs WHERE state IN ('planned','running','paused')")
    n, which = cur.fetchone()
    cur.execute("RESET ROLE")
    if n:
        problems.append(f"{n} build_run(s) in planned/running/paused on ANY chart ({which}); not touched, plan stops")
    cur.execute(f"SET LOCAL ROLE {OWNER}")
    cur.execute("SELECT count(*) FROM public.l1_data_plane_generations WHERE status = 'building'")
    building = cur.fetchone()[0]
    cur.execute("RESET ROLE")
    if building:
        problems.append("an L1 data-plane generation is still 'building'")
    cur.execute("SELECT count(*) FILTER (WHERE state IN ('active','idle in transaction','idle in transaction (aborted)')), "
                "count(*) FILTER (WHERE state IS NULL) FROM pg_stat_activity WHERE usename = %s AND pid <> pg_backend_pid()",
                (BUILDER,))
    busy, hidden = cur.fetchone()
    if hidden:
        print(f"WARNING: {hidden} {BUILDER} session(s) have a hidden state (no pg_read_all_stats); only build_runs guards them")
    if busy:
        problems.append(f"a {BUILDER} session is active or idle-in-transaction")
    cur.execute("SELECT indexdef FROM pg_indexes WHERE schemaname='public' AND indexname=%s", (INDEX,))
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
    # the digest function the plan (and the status gate) calls: where does pgcrypto live?
    cur.execute("SELECT extnamespace::regnamespace::text FROM pg_extension WHERE extname = 'pgcrypto'")
    ext = cur.fetchone()
    cur.execute("SELECT to_regprocedure('public.digest(text,text)') IS NOT NULL")
    ok = cur.fetchone()[0]
    print(f"pgcrypto schema: {ext[0] if ext else 'NOT INSTALLED'}; public.digest(text,text) resolves: {ok}")
    if not ok:
        problems.append("public.digest(text,text) does not resolve; this plan schema-qualifies it")
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
    return {"trigger_attestation_rows": trg_rows, "function_attestation_rows": fn_rows,
            "old_def": old_def, "new_def": new_def}


# ------------------------------------------------------------------------------------------------------------------
# identity probe: the capture path's identity arithmetic, fired on fixture rows inside the rolled-back transaction
# ------------------------------------------------------------------------------------------------------------------
_D30_ODD = [("Mars", 0, 5), ("Saturn", 5, 10), ("Jupiter", 10, 18), ("Mercury", 18, 25), ("Venus", 25, 30)]
_D30_EVEN = [("Venus", 0, 5), ("Mercury", 5, 12), ("Jupiter", 12, 20), ("Saturn", 20, 25), ("Mars", 25, 30)]
_SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]


def probe_rows() -> list[dict]:
    """The three families the old key collapsed, in the writer's own shapes: 60 D30 lords, 12 house lords, 12 bindus."""
    rows = []
    for s in range(12):
        for lord, a, b in (_D30_ODD if s % 2 == 0 else _D30_EVEN):
            rows.append(dict(graha=lord, varga="D30", fact_category="varga_d30_lord_per_amsa",
                             fact_key=f"{lord}_{a}_{b}", fact_subject=f"D30.S{s + 1}"))
    for h in range(12):
        rows.append(dict(graha=_SIGN_LORDS[h], varga="D1", fact_category="varga_house_lord",
                         fact_key="lord", fact_subject=f"D1.H{h + 1}"))
    for s in range(12):
        rows.append(dict(graha="Sun", varga="D1", fact_category="varga_ashtakavarga",
                         fact_key="bindus", fact_subject=f"D1.SUN.S{s + 1}"))
    return rows


def identity_probe(cur) -> dict:
    """Reproduce, on a session-local copy of the table, exactly what the live trigger + completion check do.

    What fires: an INSERT ... ON CONFLICT (<the LIVE unique index's columns>) DO NOTHING of 84 fixture rows; the
    capture identity of each stored row, built the way l1_data_plane_capture_row builds v_identity (the live trigger's
    own arguments, `col=value` joined with '|', NULL as '<null>'); then the completion arithmetic: stored rows must equal
    count(DISTINCT identity). What does NOT fire: the capture function itself and complete_l1_data_plane_partition.
    The first line of the live capture function is `IF session_user <> 'data_plane_builder' THEN RAISE EXCEPTION`, and a
    non-superuser administrator cannot SET SESSION AUTHORIZATION, so no administrator transaction can fire it; it also
    needs an admitted generation (build_runs running + build_run_assets building + a partition context).
    """
    cur.execute(f"SET LOCAL ROLE {OWNER}")  # the administrator cannot read chart_divisionals (LIKE needs SELECT)
    cur.execute("SELECT indexdef FROM pg_indexes WHERE schemaname='public' AND indexname=%s", (INDEX,))
    live_cols = tuple(c.strip() for c in re.search(r"\(([^)]*)\)", cur.fetchone()[0]).group(1).split(","))
    cur.execute("SELECT pg_get_triggerdef(t.oid,true) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
                "WHERE c.relname=%s AND t.tgname=%s", (TABLE, TRIGGER))
    trg_args = tuple(a.strip().strip("'") for a in
                     re.search(r"l1_data_plane_capture_row\((.*)\)\s*$", cur.fetchone()[0]).group(1).split(","))
    for ident in live_cols + trg_args:
        assert re.fullmatch(r"[a-z_]+", ident), ident
    cur.execute(f"CREATE TEMP TABLE fa2_probe (LIKE public.{TABLE} INCLUDING DEFAULTS) ON COMMIT DROP")
    cur.execute(f"CREATE UNIQUE INDEX fa2_probe_uq ON fa2_probe ({', '.join(live_cols)}) NULLS NOT DISTINCT")
    cols = ("chart_id", "ayanamsha_id", "build_id", "graha", "varga", "fact_category", "fact_key", "fact_subject")
    sql = (f"INSERT INTO fa2_probe ({', '.join(cols)}) VALUES (%(chart_id)s::uuid, %(ayanamsha_id)s, %(build_id)s, "
           f"%(graha)s, %(varga)s, %(fact_category)s, %(fact_key)s, %(fact_subject)s) "
           f"ON CONFLICT ({', '.join(live_cols)}) DO NOTHING")
    landed = 0
    fixture = probe_rows()
    for r in fixture:
        r = dict(r, chart_id="00000000-0000-0000-0000-00000000fa20", ayanamsha_id="fa2_probe", build_id="fa2-probe")
        cur.execute(sql, r)
        landed += cur.rowcount

    def distinct_identities(args) -> int:
        parts = ", ".join(f"'{a}=' || COALESCE(to_jsonb(t)->>'{a}', '<null>')" for a in args)
        cur.execute(f"SELECT count(DISTINCT array_to_string(ARRAY[{parts}], '|')) FROM fa2_probe t")
        return cur.fetchone()[0]

    result = {"fixture_rows": len(fixture), "landed": landed, "live_index_cols": live_cols,
              "trigger_args": trg_args, "identities_live_args": distinct_identities(trg_args),
              "identities_legacy_6_args": distinct_identities(OLD_COLS)}
    cur.execute("RESET ROLE")
    return result


def render_diff(before: dict, after: dict, plan: dict) -> str:
    """The exact catalog diff, readable: one block per category, plus what must be identical."""
    out = []
    names = {"index": "INDEX DEFINITION", "trigger": "TRIGGER DEFINITION",
             "trigger_attestation": "TRIGGER ATTESTATION ROW (table, trigger, type, enabled, fn oid, fn, digest)",
             "function": "FUNCTION (signature, md5(def), owner, secdef, config, acl)",
             "function_attestation": "FUNCTION ATTESTATION ROW (signature, digest, owner, secdef, config)"}
    for key, title in names.items():
        removed, added = sorted(before[key] - after[key]), sorted(after[key] - before[key])
        out.append(f"== {title}: exactly {len(removed)} removed / {len(added)} added "
                   f"({'ONE ENTRY CHANGES' if len(removed) == len(added) == 1 else 'UNEXPECTED'}) ==")
        for r in removed:
            out.append("  - " + " | ".join(r))
        for a in added:
            out.append("  + " + " | ".join(a))
    out.append("== FUNCTION HUNK (unified diff of pg_get_functiondef, before -> after) ==")
    out.extend("  " + line.rstrip("\n") for line in difflib.unified_diff(
        plan["old_def"].splitlines(True), plan["new_def"].splitlines(True),
        fromfile="l1_data_plane_capture_row() before", tofile="after", n=3))
    for key in ("acl", "membership", "rls", "policy", "rowdata"):
        out.append(f"== {key.upper()}: {'IDENTICAL' if before[key] == after[key] else 'CHANGED (UNEXPECTED)'} "
                   f"({len(before[key])} entries) ==")
    return "\n".join(out)


def check_after(cur, before: dict, after: dict, plan: dict, probe: dict) -> list[str]:
    """Every commit condition. Returns the list of failures (empty = commit allowed)."""
    bad = []
    cur.execute(f"SET LOCAL ROLE {OWNER}")  # the attestation tables are owner-readable only
    if (plan["trigger_attestation_rows"], plan["function_attestation_rows"]) != (1, 1):
        bad.append(f"attestation UPDATE row counts {plan['trigger_attestation_rows']}/{plan['function_attestation_rows']}")
    for key in ("index", "trigger", "trigger_attestation", "function", "function_attestation"):
        removed, added = before[key] - after[key], after[key] - before[key]
        if len(removed) != 1 or len(added) != 1:
            bad.append(f"{key}: expected exactly 1 changed entry, got -{len(removed)} +{len(added)}")
    for key in ("acl", "membership", "rls", "policy", "rowdata"):
        if before[key] != after[key]:
            bad.append(f"{key} changed")
    cur.execute("SELECT i.indisunique, i.indisvalid, i.indnullsnotdistinct, "
                "array(SELECT a.attname::text FROM unnest(i.indkey) WITH ORDINALITY k(attnum,ord) "
                "JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=k.attnum ORDER BY k.ord) "
                "FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE c.relname=%s", (INDEX,))
    row = cur.fetchone()
    if not row or not (row[0] and row[1] and row[2] and tuple(row[3]) == NEW_COLS):
        bad.append(f"new index shape wrong: {row}")
    cur.execute("SELECT count(*) FROM pg_trigger WHERE tgname = ANY(%s) AND tgenabled = 'O'",
                ([TRG_ATT_IMMUTABLE, FN_ATT_IMMUTABLE],))
    if cur.fetchone()[0] != 2:
        bad.append("an attestation append-only trigger is not enabled after the plan")
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
    if not (probe["landed"] == probe["fixture_rows"] == probe["identities_live_args"]
            and probe["trigger_args"] == NEW_COLS and probe["live_index_cols"] == NEW_COLS
            and probe["identities_legacy_6_args"] < probe["landed"]):
        bad.append(f"identity probe: {probe}")
    cur.execute("RESET ROLE")
    return bad


def run(conn, mode: str, out=print, writer_commit: str | None = None, gate_tables: list[str] | None = None,
        writer_runner=_run_cmd) -> bool:
    """Returns True only when the transaction may be committed (mode apply, all checks hold)."""
    cur = conn.cursor()
    started = utcnow()
    out(f"start (UTC): {started}")
    cur.execute(f"SET LOCAL search_path = {SEARCH_PATH}")
    cur.execute("SET LOCAL lock_timeout = '5s'")
    cur.execute("SET LOCAL statement_timeout = '120s'")
    cur.execute(SNAP_SQL["membership"])
    membership_before = {tuple(str(x) for x in row) for row in cur.fetchall()}  # BEFORE any transient grant
    transient = [r for r in (OWNER, APP_OWNER) if not is_member(cur, r)]
    for r in transient:
        cur.execute(f"GRANT {r} TO CURRENT_USER")
    problems = preconditions(cur)
    writer_problems, writer_line = writer_check(writer_commit, writer_runner)
    out(f"writer-first check: {writer_line}")
    if mode == "apply":  # a dry run may run without it (printed NOT CHECKED); an apply never may
        problems += writer_problems
    elif writer_commit:
        problems += writer_problems
    gate_before = gate_mirror(cur, gate_tables)
    if gate_red(gate_before):
        problems.append(f"the deploy gate is already RED before the plan ({gate_red(gate_before)}); not attributable to it")
    out("preconditions: " + ("OK" if not problems else "REFUSED"))
    for p in problems:
        out("  - " + p)
    if mode == "count" or problems:
        out(f"end (UTC): {utcnow()}")
        return False
    before = snap(cur)
    before["membership"] = membership_before
    cur.execute(f"SET LOCAL ROLE {OWNER}")
    window_start = utcnow()
    plan = apply_plan(cur)
    cur.execute("RESET ROLE")
    probe = identity_probe(cur)
    after = snap(cur)
    after["membership"] = membership_before  # placeholder until the transient grants are revoked below
    bad = check_after(cur, before, after, plan, probe)  # needs the owner role, so it runs before the revoke
    gate_after = gate_mirror(cur, gate_tables)
    if gate_red(gate_after):
        bad.append(f"DEPLOY GATE WOULD GO RED after commit: {gate_red(gate_after)} (stored vs gate-side digest mismatch)")
    if gate_after["trigger_digest_stored"] != gate_after["trigger_digest_gate_side"]:
        bad.append("capture trigger attestation digest != the digest the gate computes under its own search_path")
    if gate_after["function_digest_stored"] != gate_after["function_digest_gate_side"]:
        bad.append("capture function attestation digest != the digest the gate computes under its own search_path")
    for r in transient:
        cur.execute(f"REVOKE {r} FROM CURRENT_USER")
    cur.execute(SNAP_SQL["membership"])
    after["membership"] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    if after["membership"] != membership_before:
        bad.append("role membership differs from the pre-state after the transient grants were revoked")
    window_end = utcnow()
    out(render_diff(before, after, plan))
    out("== DEPLOY GATE, run as the gate does (its own queries, search_path = %s) ==" % GATE_SEARCH_PATH)
    for tag, g in (("before the plan", gate_before), ("after the plan ", gate_after)):
        out(f"  {tag}: trigger_shape_unsafe={g['trigger_shape_unsafe']} trigger_surface_unsafe={g['trigger_surface_unsafe']} "
            f"function_digests_unsafe={g['function_digests_unsafe']}")
    out(f"  capture trigger digest  stored {gate_after['trigger_digest_stored']}")
    out(f"                          gate   {gate_after['trigger_digest_gate_side']}")
    out(f"  capture function digest stored {gate_after['function_digest_stored']}")
    out(f"                          gate   {gate_after['function_digest_gate_side']}")
    out("== IDENTITY PROBE (fixture rows through the widened key; session-local table, rolled back) ==")
    out(f"  live unique index columns : {probe['live_index_cols']}")
    out(f"  live trigger arguments    : {probe['trigger_args']}")
    out(f"  fixture rows / landed     : {probe['fixture_rows']} / {probe['landed']}  (ON CONFLICT on the live index columns)")
    out(f"  distinct identities, live trigger args   : {probe['identities_live_args']}  "
        f"(completion check needs this == rows_inserted)")
    out(f"  distinct identities, legacy 6 args       : {probe['identities_legacy_6_args']}  "
        f"(what the unwidened trigger would capture: the abort the plan prevents)")
    out("commit conditions: " + ("ALL HOLD" if not bad else f"FAILED {bad}"))
    out(f"index-swap-to-end window (UTC): {window_start} -> {window_end}")
    out(f"end (UTC): {utcnow()}")
    return not bad and mode == "apply"


def main(argv: list[str]) -> int:
    h = plan_hash()
    print("plan sha256:", h)
    args = list(argv)
    writer_commit = None
    if "--writer-commit" in args:
        i = args.index("--writer-commit")
        writer_commit = args[i + 1] if i + 1 < len(args) else None
        if not writer_commit:
            raise SystemExit("--writer-commit needs a commit sha")
        del args[i:i + 2]
    if args == ["--print-hash"]:
        return 0
    if args == ["--count"]:
        mode, expect = "count", None
    elif args == ["--dry-run"]:
        mode, expect = "dry-run", None
    elif len(args) == 3 and args[0] == "--apply" and args[1] == "--expect-plan":
        mode, expect = "apply", args[2]
    else:
        raise SystemExit("usage: --print-hash | --count | --dry-run [--writer-commit S] | "
                         "--apply --expect-plan <hash> --writer-commit S")
    if mode == "apply" and expect != h:
        raise SystemExit("REFUSED: --expect-plan does not equal the plan hash")
    if mode == "apply" and not writer_commit:
        raise SystemExit("REFUSED: --apply requires --writer-commit (the writer deploys BEFORE this plan)")
    import psycopg  # imported late so --print-hash needs no driver
    with psycopg.connect(host="127.0.0.1", port=5433, dbname="amjis", user="postgres",
                         password=secret("cloudsql-postgres-admin-password"), sslmode="disable",
                         connect_timeout=15) as conn:
        ok = run(conn, mode, writer_commit=writer_commit)
        if ok:
            conn.commit()
            print("COMMITTED")
            print("plan sha256:", h)
            return 0
        conn.rollback()
        print("ROLLED BACK (%s)" % {"count": "read-only", "dry-run": "dry run", "apply": "refused or checks failed"}[mode])
        print("plan sha256:", h)
        return 1 if mode == "apply" else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:  # never show a traceback (could expose connection details)
        print("failed: %s %s" % (type(exc).__name__, str(exc)[:200].replace("\n", " ")))
        sys.exit(1)

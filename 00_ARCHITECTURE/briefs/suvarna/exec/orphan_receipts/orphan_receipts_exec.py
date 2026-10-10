#!/usr/bin/env python3
"""D6 owner-path executor: retire the ORPHANED legacy `__whole_asset__` receipt row (and its asset_freshness twin)
of ONE asset on ONE chart. One-shot operator tool (not product code); parameterised so the same executor serves
ga_positions at S-L1 and bo_laksana / bo_sangati / bo_cgm_motifs / bo_upaya at S-L2.

  ./run_gated.sh python3 orphan_receipts_exec.py --asset <asset_id> --chart <chart_id> --dry-run [--min-build-after <ISO ts>]
  ./run_gated.sh python3 orphan_receipts_exec.py --asset <asset_id> --chart <chart_id> --apply --expect-plan <sha256>
                                  --min-build-after <ISO ts, tz-aware> --expect-evidence <digest of the dry run>

v3 (GATE_V2 binding). The executor is NEVER started directly: run_gated.sh runs prerun_gate.py (non-completed main deploy
runs == 0 and planned/running/paused build_runs == 0, as suvarna_reader) and only then sets GATE_V2_LAUNCH and execs this
file. main() calls require_gate_launch(...) FIRST and refuses (exit 93) without a verifying marker, or when any of the three
gate files next to it (prerun_gate.py, run_gated.sh, executor_standards.py: byte-identical to gate_v2) differs from the sha256
pinned in GATE_PINS. In every mode (dry run, apply, any refusal after the arguments are valid, any exception) it writes
outcome.json (executor_standards.outcome_guard) into the run's evidence directory. An under_test launch marker is refused (exit 93)
outside a pytest run. If conn.commit() ITSELF raises, outcome.json records `commit_state_unknown` (the server may have committed: check
the database), not `failed`. outcome.json also records `under_test` (from the
launch marker) and `warnings`. **A MISSING outcome.json means "check the database": SIGKILL, power loss or a crash right after COMMIT
can leave none** (it never means "nothing happened"). After COMMIT a failure while writing it records `applied` with the warning
`outcome_write_failed_after_commit:<ExceptionClassName>`, never `failed`; SIGTERM / SIGHUP raise a clean SystemExit(128+signal) that is
held off (signal mask) until the COMMIT and its bookkeeping are done, so they too end in a correct outcome.json.

  exit codes: 0 ok / committed; 1 apply refused or aborted (or an unexpected failure); 2 dry-run refused; 3 dry-run
              counterfactual (no --min-build-after); 93 not launched by run_gated.sh / gate files differ from the pins;
              95 ORPH_TEST_EVIDENCE_ROOT set outside a pytest run

  --dry-run   runs EVERY check and the real DELETEs inside one transaction, then ALWAYS ROLLS BACK, and prints the
              full diff JSON plus the plan hash it computes.
  --apply     requires --expect-plan == the plan hash, --min-build-after and --expect-evidence (the evidence_digest the
              dry run printed: the apply must see exactly the state the dry run showed); re-checks every condition inside the
              same transaction; COMMITs only if all pass (otherwise ROLLBACK and exit 1).

Every condition is a CHECK that REFUSES (P1-P5 pre-checks, D/V/A post-checks, E evidence digest: see run_txn); nothing is committed unless all hold. Before-images of
both rows (all columns, JSON) and a reversal SQL file are written to the evidence directory BEFORE any DELETE; if they
cannot be written the run aborts (rollback) in both modes.

Admin credential: fetched from Secret Manager in-process (same mechanism as ChartGrants/cg_exec.py), never printed,
logged or saved. Proxy 127.0.0.1:5433. `main()` is the only place that reaches the real database; tests call
`execute()` with an injected connection factory against a disposable local Postgres.

plan hash = bind_gate_into_plan_hash(sha256(plan_text + "\\n" + json.dumps(DIFF)), gate fingerprint); the plan text embeds
this file's own sha256, that of resolver_verdicts.sql and the three gate-file shas, and bind_gate_into_plan_hash folds the
prerun_gate.py / run_gated.sh shas in again (editing any gate file changes the plan the operator approved). The hash is
computed WITHOUT the database. The DB-dependent part (before-images, verdict diff, row counts, ACL/RLS/policy/membership snapshots) is
computed at dry-run/apply time and bound by the optional `evidence_digest` (see PLAN.md).
"""
import argparse
import collections
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import uuid

import psycopg

HERE = pathlib.Path(__file__).resolve().parent


def _load_standards():
    """The executor_standards.py that sits NEXT TO this file (never one found on sys.path)."""
    spec = importlib.util.spec_from_file_location("executor_standards", HERE / "executor_standards.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


es = _load_standards()

PROJECT = "madhav-astrology"
OWNER = "amjis_app"
WHOLE = "__whole_asset__"
RECEIPTS = "asset_provenance_receipts"
FRESH = "asset_freshness"
EVIDENCE_ROOT = "/Users/Dev/suvarna-evidence/OrphanReceipts"
VERDICT_SQL_FILE = HERE / "resolver_verdicts.sql"
INFLIGHT_STATES = ("planned", "running", "paused")
EXPECTED_VERDICT = ("receipt_not_proven", "RESOLVED")
ASSET_RE = re.compile(r"[a-z][a-z0-9_]{1,62}")        # used with fullmatch (no trailing-newline loophole)
TEST_EVIDENCE_ENV = "ORPH_TEST_EVIDENCE_ROOT"
PYTEST_ENV = "PYTEST_CURRENT_TEST"
EXIT_NO_LAUNCH = es.EXIT_NO_LAUNCH            # 93: not launched by run_gated.sh / gate files differ from the pins
EXIT_TEST_ENV = 95                            # a test-only variable is set outside the test harness (same code as the gate)

# SS binding (GATE_V2, PR #2938): the three files next to this executor are BYTE-IDENTICAL copies of gate_v2's. Their sha256
# are pinned here (so a changed gate file is refused at start, in every mode) and folded into the plan hash.
GATE_PINS = {
    "prerun_gate.py": "01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e",
    "run_gated.sh": "305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076",
    "executor_standards.py": "bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135",
}

# The two DELETEs. Shared by the executor and the rendered plan text so they cannot drift apart.
# The state guards mean the executor can never delete a proven/fresh row (it only ever removes an `unknown`/non-fresh
# orphan; it never creates or edits a receipt, so no freshness is fabricated).
DELETE_FRESH = ("DELETE FROM public.asset_freshness WHERE asset_id = %(a)s AND chart_id = %(c)s::uuid "
                "AND partition_key = '__whole_asset__' AND freshness_state IN ('stale','unknown')")
DELETE_RECEIPT = ("DELETE FROM public.asset_provenance_receipts WHERE asset_id = %(a)s AND chart_id = %(c)s::uuid "
                  "AND partition_key = '__whole_asset__' AND receipt_state = 'unknown'")
LOCK_SQL = ("LOCK TABLE public.asset_provenance_receipts, public.asset_freshness, public.build_runs "
            "IN SHARE ROW EXCLUSIVE MODE")

ACL_SQL = """
SELECT c.relname, COALESCE(r.rolname,'PUBLIC'), a.privilege_type, a.is_grantable::text
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault('r', c.relowner))) a
LEFT JOIN pg_roles r ON r.oid=a.grantee
WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')
"""
OWN_SQL = ("SELECT c.relname, pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
           "WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')")
MEMBER_SQL = ("SELECT r.rolname, m.rolname, (to_jsonb(am) - 'oid')::text FROM pg_auth_members am "  # all option columns, any PG major
              "JOIN pg_roles r ON r.oid=am.roleid JOIN pg_roles m ON m.oid=am.member")
RLS_SQL = ("SELECT c.relname, c.relrowsecurity::text, c.relforcerowsecurity::text FROM pg_class c "
           "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p')")
POLICY_SQL = ("SELECT c.relname, p.polname, p.polcmd::text, p.polroles::text, pg_get_expr(p.polqual,p.polrelid), "
              "coalesce(pg_get_expr(p.polwithcheck,p.polrelid),'') FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid")


class EvidenceError(Exception):
    """before-images / reversal SQL could not be written: the run aborts (rollback)."""


# --------------------------------------------------------------------------------------------- plan text + hash
def exec_sha(path=None):
    return hashlib.sha256(pathlib.Path(path or __file__).read_bytes()).hexdigest()


def expected_diff(asset, chart):
    """The static, DB-independent expectation bound into the plan hash."""
    return sorted([
        "%s|%s|%s|%s|present->absent" % (FRESH, asset, chart, WHOLE),
        "%s|%s|%s|%s|present->absent" % (RECEIPTS, asset, chart, WHOLE),
        "resolver_verdict|%s|%s->%s" % ((asset,) + EXPECTED_VERDICT),
    ])


def gate_shas(gate_dir=None):
    """sha256 of the three gate files next to this executor (the live files, not the pins)."""
    d = pathlib.Path(gate_dir) if gate_dir else HERE
    return {name: sha_file(d / name) for name in GATE_PINS}


def render_plan(asset, chart, sha, vsha=None, gate=None):
    vsha = vsha or sha_file(VERDICT_SQL_FILE)
    gate = gate or gate_shas()
    d = {"a": asset, "c": chart}
    fresh = DELETE_FRESH.replace("%(a)s", "'%s'" % asset).replace("%(c)s", "'%s'" % chart)
    rec = DELETE_RECEIPT.replace("%(a)s", "'%s'" % asset).replace("%(c)s", "'%s'" % chart)
    return "\n".join([
        "-- plan: retire the ORPHANED legacy __whole_asset__ receipt row and its asset_freshness twin for asset %s on chart %s (data rows only: no grant, no schema, no code, no other row of any table)" % (asset, chart),
        "SET LOCAL search_path = pg_catalog, pg_temp",
        "SET LOCAL lock_timeout = '5s'",
        "SET LOCAL statement_timeout = '5s'",
        "SET LOCAL TimeZone = 'UTC'",
        "-- snapshot A (session user): relacl + owner of every public relation, relrowsecurity/relforcerowsecurity, pg_policy, pg_auth_members",
        "-- membership: GRANT %s TO <session user> only if missing; REVOKE before snapshot B only if granted here" % OWNER,
        "SET LOCAL ROLE %s" % OWNER,
        LOCK_SQL,
        "-- before-images (all columns, JSON) of both rows + reversal INSERT SQL written to the evidence directory BEFORE any DELETE; if unwritable: abort + ROLLBACK",
        "-- resolver port (resolver_verdicts.sql, chart-parameterised) run for ALL assets: verdicts A; row-key+md5 map of both tables A",
        "-- pre-checks (any failure: no DELETE is issued, ROLLBACK):",
        "--   P1 registry declares a non-empty natural_key_partition for the asset, != '__whole_asset__'",
        "--   P2 the __whole_asset__ receipt is receipt_state='unknown' and its twin freshness_state in ('stale','unknown') (never a proven/fresh row)",
        "--   P3 a PROVEN declared-partition receipt exists with freshness 'fresh', from a COMPLETED build that is newer than the __whole_asset__ row's build",
        "--      AND its receipt observed_at and its build created_at are > --min-build-after (required at --apply; a runtime parameter, tz-aware, bound by the evidence digest; a --dry-run without it is a counterfactual only, exit 3)",
        "--   P4 exactly 1 receipt row and exactly 1 freshness twin for (asset, chart, '__whole_asset__')",
        "--   P5 zero build_runs in state planned/running/paused on ANY chart",
        fresh + "   -- rowcount must be 1",
        rec + "   -- rowcount must be 1",
        "-- resolver port again: verdicts B; row-key+md5 map B",
        "RESET ROLE",
        "-- REVOKE %s FROM <session user> only if granted here; snapshot B" % OWNER,
        "-- commit only if: both DELETE rowcounts == 1; the row-key+md5 diff of BOTH tables is exactly the two removed keys (no other row of any table changed); the per-asset verdict diff over ALL assets is exactly {%s: %s -> %s}; relacl, owner, relrowsecurity, relforcerowsecurity, pg_policy and pg_auth_members diffs between snapshot A and B are all empty; chart-scoped receipt<->freshness twin integrity unchanged" % ((asset,) + EXPECTED_VERDICT),
        "-- --dry-run: the same statements, then ROLLBACK, always. --apply: COMMIT only if every check above holds, --expect-plan equals this plan hash AND --expect-evidence (REQUIRED) equals the evidence digest computed in this transaction (check E).",
        "-- the real run is started ONLY through run_gated.sh <executor> <args> (GATE_V2): prerun_gate.py must read zero non-completed main deploy.yml runs and zero planned/running/paused build_runs as suvarna_reader, else the executor is not started; run_gated.sh then sets GATE_V2_LAUNCH and the executor REFUSES (exit 93) unless that marker verifies against the gate files pinned below.",
        "-- in every mode the executor writes outcome.json (status dry_run | applied | failed | commit_state_unknown, UTC time, executor sha, plan hash, gate shas, evidence digest, failed check names, under_test from the launch marker, warnings) into its evidence directory (after COMMIT an interruption records applied with a warning, never failed; a MISSING outcome.json means check the database); it refuses (exit 95) when ORPH_TEST_EVIDENCE_ROOT is set outside a pytest run.",
        "-- gate files (byte-identical to gate_v2, PR #2938): prerun_gate.py sha256 %s; run_gated.sh sha256 %s; executor_standards.py sha256 %s" % (
            gate["prerun_gate.py"], gate["run_gated.sh"], gate["executor_standards.py"]),
        "-- plan hash = bind_gate_into_plan_hash(sha256(plan text + \"\\n\" + DIFF), prerun_gate.py sha256, run_gated.sh sha256)",
        "-- resolver port: resolver_verdicts.sql sha256 %s" % vsha,
        "-- executor: orphan_receipts_exec.py sha256 %s" % sha,
    ])


def plan_hash_unbound(asset, chart, sha=None, gate=None):
    """sha256(plan_text + "\\n" + DIFF): the v1.1 formula, before the gate shas are folded in."""
    text = render_plan(asset, chart, sha or exec_sha(), gate=gate)
    return hashlib.sha256((text + "\n" + json.dumps(expected_diff(asset, chart))).encode()).hexdigest()


def plan_hash(asset, chart, sha=None, gate=None):
    gate = gate or gate_shas()
    return es.bind_gate_into_plan_hash(plan_hash_unbound(asset, chart, sha, gate),
                                       {"gate_sha256": gate["prerun_gate.py"], "run_gated_sha256": gate["run_gated.sh"]})


# --------------------------------------------------------------------------------------------- db plumbing
def secret(name):
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest", "--secret", name, "--project", PROJECT],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("secret access failed")
    return r.stdout.rstrip("\r\n")


def connect_admin():
    return psycopg.connect(host="127.0.0.1", port=5433, dbname="amjis", user="postgres",
                           password=secret("cloudsql-postgres-admin-password"), sslmode="disable",
                           connect_timeout=15)


def load_verdict_sql():
    lines = [ln for ln in VERDICT_SQL_FILE.read_text().splitlines() if not ln.lstrip().startswith("--")]
    return "\n".join(lines).replace(":'chart'", "%(chart)s")


def verdicts(cur, chart, sql):
    cur.execute(sql, {"chart": chart})
    return {r[0]: r[1] for r in cur.fetchall()}


def snap(cur):
    out = {}
    for k, sql in (("acl", ACL_SQL), ("own", OWN_SQL), ("mem", MEMBER_SQL), ("rls", RLS_SQL), ("pol", POLICY_SQL)):
        cur.execute(sql)
        out[k] = {tuple(map(str, row)) for row in cur.fetchall()}
    return out


def key_map(cur, table):
    cur.execute("SELECT asset_id, scope_key, partition_key, md5(t::text) FROM public.%s t" % table)
    return sorted(tuple(r) for r in cur.fetchall())


def twin_integrity(cur, chart):
    cur.execute("SELECT (SELECT count(*) FROM public.asset_freshness f WHERE f.chart_id = %(c)s::uuid AND NOT EXISTS "
                "(SELECT 1 FROM public.asset_provenance_receipts r WHERE r.asset_id=f.asset_id AND r.scope_key=f.scope_key "
                "AND r.partition_key=f.partition_key)), "
                "(SELECT count(*) FROM public.asset_provenance_receipts r WHERE r.chart_id = %(c)s::uuid AND NOT EXISTS "
                "(SELECT 1 FROM public.asset_freshness f WHERE r.asset_id=f.asset_id AND r.scope_key=f.scope_key "
                "AND r.partition_key=f.partition_key))", {"c": chart})
    return list(cur.fetchone())


def chart_counts(cur, chart):
    cur.execute("SELECT (SELECT count(*) FROM public.asset_provenance_receipts WHERE chart_id=%(c)s::uuid), "
                "(SELECT count(*) FROM public.asset_freshness WHERE chart_id=%(c)s::uuid)", {"c": chart})
    r = cur.fetchone()
    return {RECEIPTS: r[0], FRESH: r[1]}


def table_columns(cur, table):
    cur.execute("SELECT quote_ident(a.attname), format_type(a.atttypid, a.atttypmod), a.attname, (a.attgenerated <> '') "
                "FROM pg_attribute a WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped "
                "ORDER BY a.attnum", ("public." + table,))
    return [{"ident": r[0], "type": r[1], "name": r[2], "generated": r[3]} for r in cur.fetchall()]


def fetch_images(cur, table, asset, chart):
    """Full before-image (to_jsonb of every column) plus the quoted-literal values for the reversal INSERT."""
    cols = table_columns(cur, table)
    ins = [c for c in cols if not c["generated"]]
    sel = ", ".join("quote_nullable(t.%s::text)" % c["ident"] for c in ins)
    cur.execute("SELECT to_jsonb(t)::text, ARRAY[%s] FROM public.%s t WHERE t.asset_id = %%(a)s AND "
                "t.chart_id = %%(c)s::uuid AND t.partition_key = %%(p)s ORDER BY 1" % (sel, table),
                {"a": asset, "c": chart, "p": WHOLE})
    rows = cur.fetchall()
    images = [json.loads(r[0]) for r in rows]
    inserts = ["INSERT INTO public.%s (%s) VALUES (%s);" % (
        table, ", ".join(c["ident"] for c in ins),
        ", ".join("%s::%s" % (v, c["type"]) for v, c in zip(r[1], ins))) for r in rows]
    return {"columns": [{"name": c["name"], "type": c["type"], "generated": c["generated"]} for c in cols],
            "rows": images}, inserts


def sha_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def resolve_evidence_root(flag=None, environ=None):
    """The real run ALWAYS writes under EVIDENCE_ROOT: --evidence-root is ignored unless the test-only env var
    ORPH_TEST_EVIDENCE_ROOT is set, and that variable is honoured ONLY inside a pytest run (PYTEST_CURRENT_TEST set, value
    non-empty): set anywhere else, even empty, it is REFUSED (exit 95), never silently ignored and never silently redirecting
    the evidence (a stray export in the operator's shell must stop the run, not move its evidence)."""
    environ = os.environ if environ is None else environ
    if TEST_EVIDENCE_ENV not in environ:
        return EVIDENCE_ROOT
    if PYTEST_ENV not in environ:
        sys.stderr.write("REFUSED: %s is set outside a pytest run; it would redirect the evidence directory. Unset it and run "
                         "through run_gated.sh.\n" % TEST_EVIDENCE_ENV)
        raise SystemExit(EXIT_TEST_ENV)
    root = flag or environ[TEST_EVIDENCE_ENV]
    if not root:
        sys.stderr.write("REFUSED: %s is set but empty (test harness): refusing to fall back to the real evidence root.\n"
                         % TEST_EVIDENCE_ENV)
        raise SystemExit(EXIT_TEST_ENV)
    return root


def mkdir_0700(path):
    """Create `path` (and any missing ancestors) with mode 0700 and chmod every directory THIS call created to 0700
    (mkdir's mode is masked by umask); a pre-existing directory is only chmod'ed on the leaf, tolerating failure."""
    path = pathlib.Path(path)
    missing = [p for p in [path] + list(path.parents) if not p.exists()]
    for p in reversed(missing):
        p.mkdir(mode=0o700)
        os.chmod(p, 0o700)
    if not missing:
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass            # an existing root we do not own: tolerated; the per-run directory below is ours and is 0700


def make_run_dir(root, asset, chart, ts):
    """Create <root>/<asset>_<chart8>_<UTC ts>/ (0700): the run's evidence directory. It is created BEFORE any connection so
    that outcome.json can be written in every mode; it never already exists (mkdir without exist_ok), so a run can never
    overwrite another run's evidence or outcome."""
    try:
        rootp = pathlib.Path(root)
        mkdir_0700(rootp)
        d = rootp / ("%s_%s_%s" % (asset, chart[:8], ts))
        d.mkdir(mode=0o700)               # NOT exist_ok: an existing run directory (a collision) is an abort, never a reuse
        os.chmod(d, 0o700)
    except OSError as exc:
        raise EvidenceError("cannot create the evidence directory under %s (%s)" % (root, type(exc).__name__))
    return d


def write_evidence(d, asset, chart, images, inserts, sha):
    """Write before_images.json + reversal.sql (0600) and SHA256SUMS into the run directory `d` (already created, 0700)."""
    try:
        d = pathlib.Path(d)
        bi = json.dumps({"asset_id": asset, "chart_id": chart, "partition_key": WHOLE, "tables": images},
                        indent=2, sort_keys=True) + "\n"
        rev = "\n".join([
            "-- REVERSAL for the retirement of the orphaned %s receipt + freshness twin of %s on chart %s." % (WHOLE, asset, chart),
            "-- Re-inserts exactly the rows captured in before_images.json (scope_key is GENERATED and is not inserted).",
            "-- Run in ONE transaction through the same D6 owner path (transient membership of %s + SET LOCAL ROLE %s)." % (OWNER, OWNER),
            "-- executor sha256 %s" % sha,
            "BEGIN;",
            "SET LOCAL TimeZone = 'UTC';",
            "SET LOCAL ROLE %s;" % OWNER,
        ] + inserts[RECEIPTS] + inserts[FRESH] + ["COMMIT;", ""])
        files = {"before_images.json": bi, "reversal.sql": rev}
        for name, text in files.items():
            fd = os.open(str(d / name), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as fh:
                fh.write(text)
        sums = {n: sha_file(d / n) for n in files}
        (d / "SHA256SUMS").write_text("".join("%s  %s\n" % (h, n) for n, h in sorted(sums.items())))
        os.chmod(d / "SHA256SUMS", 0o600)
    except OSError as exc:
        raise EvidenceError("cannot write evidence under %s (%s)" % (d, type(exc).__name__))
    return {"dir": str(d), "before_images.json": {"path": str(d / "before_images.json"), "sha256": sums["before_images.json"]},
            "reversal.sql": {"path": str(d / "reversal.sql"), "sha256": sums["reversal.sql"]}}


# --------------------------------------------------------------------------------------------- the transaction
def parse_min(value):
    if value is None:
        return None
    t = dt.datetime.fromisoformat(value)
    if t.tzinfo is None:
        raise SystemExit("REFUSED: --min-build-after must carry a timezone (e.g. 2026-10-05T09:00:00Z)")
    return t


def run_txn(conn, args, sha, phash, run_dir):
    asset, chart = args.asset, args.chart
    min_after = parse_min(args.min_build_after)
    apply_mode = bool(args.apply)
    cur = conn.cursor()
    checks = collections.OrderedDict()

    def chk(name, ok, detail=None):
        checks[name] = {"ok": bool(ok), "detail": detail}
        return bool(ok)

    def skip(name, why):  # a check that could not run because a pre-check already refused (ok=None, not a pass)
        checks[name] = {"ok": None, "detail": "not run: " + why}

    cur.execute("SET LOCAL search_path = pg_catalog, pg_temp")
    cur.execute("SET LOCAL lock_timeout = '5s'")
    cur.execute("SET LOCAL statement_timeout = '5s'")
    cur.execute("SET LOCAL TimeZone = 'UTC'")
    snap_a = snap(cur)
    cur.execute("SELECT pg_has_role(session_user, %s, 'MEMBER'), quote_ident(session_user)", (OWNER,))
    is_member, who = cur.fetchone()
    granted = False
    if not is_member:
        cur.execute("GRANT %s TO %s" % (OWNER, who))
        granted = True
    cur.execute("SET LOCAL ROLE %s" % OWNER)
    cur.execute(LOCK_SQL)

    # ---- before-images: written to disk BEFORE any DELETE; failure aborts the run
    images, inserts = {}, {}
    for t in (RECEIPTS, FRESH):
        images[t], inserts[t] = fetch_images(cur, t, asset, chart)
    evidence = write_evidence(run_dir, asset, chart, images, inserts, sha)
    n_rec, n_fr = len(images[RECEIPTS]["rows"]), len(images[FRESH]["rows"])

    sql_v = load_verdict_sql()
    v_before = verdicts(cur, chart, sql_v)
    km_before = {t: key_map(cur, t) for t in (RECEIPTS, FRESH)}
    counts_before = chart_counts(cur, chart)
    twin_before = twin_integrity(cur, chart)

    # ---- P1 registry declares a partition (orphan by definition, part 1)
    cur.execute("SELECT natural_key_partition FROM public.asset_registry WHERE asset_id = %s", (asset,))
    reg = cur.fetchall()
    declared = reg[0][0] if len(reg) == 1 else None
    declares = declared is not None and declared.strip() != "" and declared != WHOLE
    chk("P1_registry_declares_partition", declares,
        {"asset_in_registry": len(reg) == 1, "declared_partition_length": len(declared) if declared else 0})

    # ---- P2 the __whole_asset__ rows are the unproven artefact, never a proven/fresh row
    orphan = None
    if n_rec == 1:
        orphan = images[RECEIPTS]["rows"][0]
    ofr = images[FRESH]["rows"][0] if n_fr == 1 else None
    chk("P2_orphan_is_unproven",
        orphan is not None and orphan["receipt_state"] == "unknown" and ofr is not None
        and ofr["freshness_state"] in ("stale", "unknown"),
        {"receipt_state": orphan and orphan["receipt_state"], "freshness_state": ofr and ofr["freshness_state"]})

    # ---- P3 a PROVEN declared-partition receipt from a LATER, completed build exists (and is newer than --min-build-after)
    later = {"found": False}
    p3 = False
    if declares and orphan is not None:
        cur.execute(
            "SELECT d.receipt_state, f.freshness_state, d.observed_at, d.build_id::text, br.state, br.created_at, "
            "       (ba.run_id IS NOT NULL), ba.disposition, o.observed_at, obr.created_at "
            "FROM public.asset_provenance_receipts d "
            "LEFT JOIN public.asset_freshness f ON f.asset_id=d.asset_id AND f.scope_key=d.scope_key "
            "     AND f.partition_key=d.partition_key AND f.receipt_version=d.receipt_version "
            "LEFT JOIN public.build_runs br ON br.id=d.build_id AND br.chart_id=d.chart_id "
            "LEFT JOIN public.build_run_assets ba ON ba.run_id=d.build_id AND ba.asset_id=d.asset_id "
            "JOIN public.asset_provenance_receipts o ON o.asset_id=d.asset_id AND o.scope_key=d.scope_key AND o.partition_key=%(w)s "
            "LEFT JOIN public.build_runs obr ON obr.id=o.build_id AND obr.chart_id=o.chart_id "
            "WHERE d.asset_id=%(a)s AND d.chart_id=%(c)s::uuid AND d.partition_key=%(p)s",
            {"a": asset, "c": chart, "p": declared, "w": WHOLE})
        r = cur.fetchall()
        if len(r) == 1:
            (rs, fs, d_obs, d_build, run_state, run_created, asset_row, disp, o_obs, o_run_created) = r[0]
            d_ts = run_created or d_obs
            o_ts = o_run_created or o_obs
            newer_than_orphan = (d_ts is not None and o_ts is not None and d_ts > o_ts and d_obs > o_obs)
            after_min = (min_after is None) or (d_obs > min_after and run_created is not None and run_created > min_after)
            p3 = (rs == "proven" and fs == "fresh" and run_state == "completed" and asset_row
                  and newer_than_orphan and after_min)
            later = {"found": True, "receipt_state": rs, "freshness_state": fs, "run_state": run_state,
                     "build_disposition": disp, "newer_than_orphan_build": bool(newer_than_orphan),
                     "after_min_build_after": bool(after_min), "min_build_after_given": min_after is not None,
                     "declared_observed_at": d_obs.isoformat(), "declared_build_created_at": run_created and run_created.isoformat(),
                     "orphan_build_created_at": o_run_created and o_run_created.isoformat(),
                     "orphan_observed_at": o_obs.isoformat()}
    chk("P3_later_proven_declared_receipt", p3, later)

    # ---- P4 exactly one receipt row and exactly one freshness twin
    chk("P4_rowcount_receipt_is_1", n_rec == 1, {"found": n_rec})
    chk("P4_rowcount_freshness_is_1", n_fr == 1, {"found": n_fr})

    # ---- P5 no build in flight on ANY chart (real column: build_runs.state)
    cur.execute("SELECT left(chart_id::text, 8), state FROM public.build_runs WHERE state = ANY(%s) ORDER BY 1, 2",
                (list(INFLIGHT_STATES),))
    inflight = [list(r) for r in cur.fetchall()]
    chk("P5_no_build_in_flight", len(inflight) == 0, {"in_flight": len(inflight), "chart_prefix_state": inflight})

    pre_ok = all(c["ok"] is True for c in checks.values())
    d_fresh = d_rec = None
    v_after, km_after, counts_after, twin_after = v_before, km_before, counts_before, twin_before
    if pre_ok:
        cur.execute(DELETE_FRESH, {"a": asset, "c": chart})
        d_fresh = cur.rowcount
        cur.execute(DELETE_RECEIPT, {"a": asset, "c": chart})
        d_rec = cur.rowcount
        chk("D_delete_rowcounts_are_1_and_1", d_fresh == 1 and d_rec == 1, {"freshness": d_fresh, "receipt": d_rec})
        v_after = verdicts(cur, chart, sql_v)
        km_after = {t: key_map(cur, t) for t in (RECEIPTS, FRESH)}
        counts_after = chart_counts(cur, chart)
        twin_after = twin_integrity(cur, chart)
    else:
        skip("D_delete_rowcounts_are_1_and_1", "a pre-check refused; no DELETE was issued")

    # ---- other rows untouched (row-key + md5 of the whole row, both tables)
    removed = lambda r: r[0] == asset and r[1] == chart and r[2] == WHOLE
    exp_after = {t: sorted(r for r in km_before[t] if not removed(r)) for t in (RECEIPTS, FRESH)}
    if pre_ok:
        chk("D_no_other_row_touched", all(km_after[t] == exp_after[t] for t in (RECEIPTS, FRESH)),
            {"receipts_before": len(km_before[RECEIPTS]), "receipts_after": len(km_after[RECEIPTS]),
             "freshness_before": len(km_before[FRESH]), "freshness_after": len(km_after[FRESH])})
        chk("D_twin_integrity_unchanged", twin_before == twin_after,
            {"freshness_without_receipt_and_receipt_without_freshness_before": twin_before, "after": twin_after})
    else:
        skip("D_no_other_row_touched", "a pre-check refused")
        skip("D_twin_integrity_unchanged", "a pre-check refused")

    # ---- resolver verdict diff over ALL assets
    vdiff = {a: [v_before.get(a), v_after.get(a)] for a in sorted(set(v_before) | set(v_after))
             if v_before.get(a) != v_after.get(a)}
    if pre_ok:
        chk("V_verdict_diff_is_exactly_the_asset", vdiff == {asset: list(EXPECTED_VERDICT)},
            {"diff": vdiff, "expected": {asset: list(EXPECTED_VERDICT)}})
    else:
        skip("V_verdict_diff_is_exactly_the_asset", "a pre-check refused")

    # ---- ACL / owner / RLS / policy / membership diffs: all must be empty (transient membership revoked first)
    cur.execute("RESET ROLE")
    if granted:
        cur.execute("REVOKE %s FROM %s" % (OWNER, who))
    snap_b = snap(cur)
    acl_diff = sorted("%s|%s|%s|grantable=%s|absent->present" % t for t in (snap_b["acl"] - snap_a["acl"])) + \
        sorted("%s|%s|%s|grantable=%s|present->absent" % t for t in (snap_a["acl"] - snap_b["acl"]))
    diffs = {k: len(snap_a[k] ^ snap_b[k]) for k in ("own", "rls", "pol", "mem")}
    chk("A_acl_diff_empty", acl_diff == [], {"acl_diff": acl_diff})
    chk("A_owner_diff_empty", diffs["own"] == 0, {"count": diffs["own"]})
    chk("A_rls_diff_empty", diffs["rls"] == 0, {"count": diffs["rls"]})
    chk("A_policy_diff_empty", diffs["pol"] == 0, {"count": diffs["pol"]})
    chk("A_membership_diff_empty", diffs["mem"] == 0, {"count": diffs["mem"], "transient_membership_granted": granted})

    n_res = lambda v: {"resolved": sum(1 for x in v.values() if x == "RESOLVED"),
                       "unresolved": sum(1 for x in v.values() if x != "RESOLVED")}
    rowcounts = {"orphan_rows_found": {RECEIPTS: n_rec, FRESH: n_fr}, "delete_rowcounts": {RECEIPTS: d_rec, FRESH: d_fresh},
                 "chart_scoped_before": counts_before, "chart_scoped_after": counts_after,
                 "table_totals_before": {t: len(km_before[t]) for t in km_before},
                 "table_totals_after": {t: len(km_after[t]) for t in km_after}}
    evidence_digest = hashlib.sha256(json.dumps({
        "asset": asset, "chart": chart, "min_build_after": min_after.isoformat() if min_after else None,
        "plan_hash": phash, "executor_sha256": sha,
        "before_images_sha256": evidence["before_images.json"]["sha256"], "reversal_sha256": evidence["reversal.sql"]["sha256"],
        "verdict_diff": vdiff, "chart_scoped_before": counts_before, "chart_scoped_after": counts_after,
        "checks": {k: v["ok"] for k, v in checks.items()}}, sort_keys=True).encode()).hexdigest()
    if apply_mode:
        chk("E_evidence_digest_matches_expected", args.expect_evidence == evidence_digest,
            {"computed": evidence_digest, "expected": args.expect_evidence})

    failed = [k for k, v in checks.items() if v["ok"] is False]
    skipped = [k for k, v in checks.items() if v["ok"] is None]
    result = {
        "asset": asset, "chart": chart, "mode": "apply" if apply_mode else "dry-run",
        "executor_sha256": sha, "plan_hash": phash, "min_build_after": min_after.isoformat() if min_after else None,
        "checks": checks, "failed_checks": failed, "skipped_checks": skipped,
        "rowcounts": rowcounts, "verdict_diff": vdiff,
        "verdict_counts": {"before": n_res(v_before), "after": n_res(v_after)},
        "acl_diff": acl_diff, "rls_diff": diffs["rls"], "policy_diff": diffs["pol"], "membership_diff": diffs["mem"],
        "owner_diff": diffs["own"],
        "before_images": evidence, "evidence_digest": evidence_digest,
    }
    return result, (not failed and not skipped)


def save_result(result):
    """Best effort: keep the printed diff JSON next to the before-images (not part of any hash)."""
    try:
        d = result["before_images"]["dir"]
        fd = os.open(os.path.join(d, "result.json"), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    except (OSError, KeyError):
        result.setdefault("warnings", []).append("result.json could not be saved next to the before-images")


def validate_params(asset, chart):
    """Single validation used by parse_args AND execute(): returns the canonical chart uuid text or exits (REFUSED)."""
    if not isinstance(asset, str) or not ASSET_RE.fullmatch(asset):
        raise SystemExit("REFUSED: --asset must match %s" % ASSET_RE.pattern)
    try:
        canon = str(uuid.UUID(chart))
    except (ValueError, AttributeError, TypeError):
        raise SystemExit("REFUSED: --chart must be a uuid")
    return canon


class SafeOutcome(es.outcome_guard):
    """executor_standards.outcome_guard whose own file write can never mask what actually happened: an OSError while writing
    outcome.json is recorded in `write_error` (and surfaced as a warning in the printed result) instead of replacing the real
    result or the real exception. Nothing else is changed: every mode, every exception, SystemExit and silent return still
    end in an outcome.json (status failed) when the file can be written."""

    write_error = None
    committed = False
    commit_unknown = None                    # class name of the exception conn.commit() itself raised: the server MAY have committed
    commit_digest = None

    def mark_committed(self, digest):
        """Called IMMEDIATELY after conn.commit(): from here on the truth is `applied`, whatever happens next."""
        self.committed, self.commit_digest = True, digest

    def mark_commit_unknown(self, digest, exc_name):
        """conn.commit() raised (e.g. the connection dropped at the acknowledgement): neither applied nor failed is known."""
        self.commit_unknown, self.commit_digest = exc_name, digest

    def _write(self, status, digest=None, checks=(), warnings=()):
        try:
            super()._write(status, digest, checks, warnings)
        except OSError as exc:
            self.write_error = type(exc).__name__
            self.done = True

    @staticmethod
    def _warn(text):
        """stderr is best effort: a closed / broken stderr (SIGHUP with the terminal gone) must never cost the outcome file."""
        try:
            sys.stderr.write(text)
            sys.stderr.flush()
        except BaseException:
            pass

    def __exit__(self, exc_type, exc, tb):
        if self.commit_unknown and not self.done:
            # the COMMIT call raised: the server may or may not have committed. Record that honestly FIRST, then say so.
            self._write("commit_state_unknown", self.commit_digest, (), ["commit_raised:" + self.commit_unknown])
            self._warn("WARNING: COMMIT STATE UNKNOWN (%s raised by commit()): the rows may or may not be committed. outcome.json records "
                       "commit_state_unknown. CHECK THE DATABASE before doing anything else.\n" % self.commit_unknown)
            return False
        if self.committed and not self.done:
            # rows ARE committed but no outcome was recorded (the applied write raised, or a signal/KeyboardInterrupt came first):
            # record `applied` + the cause, never the `failed` the base class would write for an exception
            why = re.sub(r"[^A-Za-z0-9_.:\-]", "_", exc_type.__name__ if exc_type is not None else "outcome_not_declared")[:40]
            self._write("applied", self.commit_digest, (), ["outcome_write_failed_after_commit:" + why])       # the outcome FIRST
            self._warn("WARNING: THE COMMIT HAPPENED but the run was interrupted (%s) before outcome.json was recorded; recorded "
                       "applied with a warning. Verify in the database.\n" % why)
            return False
        return super().__exit__(exc_type, exc, tb)


def conclude(o, result, kind, digest=None, checks=()):
    """Declare the outcome ('dry_run' | 'applied' | 'failed') and annotate the printed result with the file (or the problem)."""
    if kind == "dry_run":
        o.dry_run(digest)
    elif kind == "applied":
        o.applied(digest)
    else:
        o.fail(list(checks) or ["refused_unspecified"], digest)
    if o.write_error:
        result.setdefault("warnings", []).append(
            "outcome.json could not be written (%s)%s" % (o.write_error, "; THE COMMIT HAPPENED" if kind == "applied" else ""))
    else:
        result["outcome_file"] = o.path
    return result


def refuse(o, check, message):
    """A refusal that happens after the run directory exists: record it in outcome.json, then stop (SystemExit, exit 1)."""
    o.fail([check])
    raise SystemExit("REFUSED: " + message)


_HANDLED_SIGNALS = (signal.SIGTERM, signal.SIGHUP)
_HELD_SIGNALS = {signal.SIGTERM, signal.SIGHUP, signal.SIGINT}      # held (not handled) around the COMMIT: SIGINT keeps its KeyboardInterrupt


def _on_terminate(signum, frame):
    for sig in _HANDLED_SIGNALS:                       # a SECOND signal must not interrupt the outcome write: ignore from the first call on
        signal.signal(sig, signal.SIG_IGN)
    raise SystemExit(128 + signum)


def install_signal_handlers():
    """SIGTERM / SIGHUP end the run with a clean SystemExit(128+n): SafeOutcome then records `failed` (before COMMIT: the connection
    close rolls the transaction back) or `applied` + a warning (after COMMIT). A signal that is ALREADY ignored when the executor
    starts (nohup's SIGHUP) is left ignored. SIGKILL cannot be handled: no outcome.json."""
    for sig in _HANDLED_SIGNALS:
        if signal.getsignal(sig) != signal.SIG_IGN:
            signal.signal(sig, _on_terminate)


def execute(args, connect, now=None, gate_fp=None):
    """Returns (exit_code, result dict). `connect` is the only door to a database. `gate_fp` is what launch_gate() returned
    (fingerprint + under_test from the marker); without it the outcome records under_test false."""
    now = now or dt.datetime.now(dt.timezone.utc)
    evidence_root = resolve_evidence_root(getattr(args, "evidence_root", None))   # exit 95 on a stray test variable
    if validate_params(args.asset, args.chart) != args.chart:
        raise SystemExit("REFUSED: --chart must be the canonical lowercase uuid text")
    sha = exec_sha()
    gate_fp = gate_fp or es.fingerprint()
    phash = plan_hash(args.asset, args.chart, sha)
    try:   # BEFORE any argument gate and any connection: every later outcome (also a refusal) lands in this directory
        run_dir = make_run_dir(evidence_root, args.asset, args.chart, now.strftime("%Y%m%dT%H%M%S%fZ"))  # microseconds
    except EvidenceError as exc:
        return 1, {"status": "ABORTED_ROLLED_BACK", "reason": "before-images not writable: %s" % exc,
                   "plan_hash": phash, "executor_sha256": sha}
    with SafeOutcome(run_dir, __file__, phash, gate_fp) as o:
        if args.apply:
            if args.expect_plan != phash:
                refuse(o, "args_expect_plan_mismatch", "--expect-plan does not equal the plan hash")
            if args.min_build_after is None:
                refuse(o, "args_min_build_after_missing", "--apply requires --min-build-after")
            if not args.expect_evidence:
                refuse(o, "args_expect_evidence_missing", "--apply requires --expect-evidence <digest from the dry run>")
        try:
            parse_min(args.min_build_after)
        except SystemExit:
            o.fail(["args_min_build_after_not_tz_aware"])
            raise
        conn = connect()
        try:
            try:
                result, good = run_txn(conn, args, sha, phash, run_dir)
            except EvidenceError as exc:
                conn.rollback()
                result = {"status": "ABORTED_ROLLED_BACK", "reason": "before-images not writable: %s" % exc,
                          "plan_hash": phash, "executor_sha256": sha}
                conclude(o, result, "failed", None, ["evidence_not_writable"])
                return 1, result
            except Exception:
                conn.rollback()
                raise                                    # SafeOutcome records it (failed, exception class name)
            digest = result["evidence_digest"]
            if args.apply and good:
                result["status"] = "COMMITTED"
                signal.pthread_sigmask(signal.SIG_BLOCK, _HELD_SIGNALS)       # SIGTERM/SIGHUP/SIGINT wait until the COMMIT is recorded
                try:
                    try:
                        conn.commit()
                    except BaseException as exc:                              # the commit call ITSELF failed: the server may have committed
                        o.mark_commit_unknown(digest, type(exc).__name__)
                        raise
                    o.mark_committed(digest)                                  # IMMEDIATELY after the commit
                finally:
                    signal.pthread_sigmask(signal.SIG_UNBLOCK, _HELD_SIGNALS)  # a pending signal is delivered here, committed is already True
                save_result(result)
                return 0, conclude(o, result, "applied", digest)
            conn.rollback()  # --dry-run ALWAYS ends here
            failed_names = result["failed_checks"] or result["skipped_checks"]
            if args.apply:
                result["status"] = "REFUSED_ROLLED_BACK"
                save_result(result)
                return 1, conclude(o, result, "failed", digest, failed_names)
            if good and args.min_build_after is None:
                # P3 was evaluated WITHOUT the rebuild gate, so this is a counterfactual, not a rehearsal of --apply
                result["status"] = "DRY_RUN_ROLLED_BACK_COUNTERFACTUAL_NO_MIN_BUILD_AFTER"
                result["warnings"] = ["--min-build-after not supplied: the 'declared receipt is from the S-L1 rebuild' gate was not "
                                      "applied. --apply requires it and would refuse unless the declared receipt is newer than it."]
                save_result(result)
                return 3, conclude(o, result, "failed", digest, ["counterfactual_no_min_build_after"])
            result["status"] = "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD" if good else "DRY_RUN_ROLLED_BACK_REFUSED"
            save_result(result)
            if good:
                return 0, conclude(o, result, "dry_run", digest)
            return 2, conclude(o, result, "failed", digest, failed_names)
        finally:
            conn.close()


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--asset", required=True)
    p.add_argument("--chart", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", dest="dry_run")
    g.add_argument("--apply", action="store_true")
    p.add_argument("--expect-plan")
    p.add_argument("--expect-evidence")
    p.add_argument("--min-build-after")
    p.add_argument("--evidence-root", default=None, help="ignored unless %s is set (tests only)" % TEST_EVIDENCE_ENV)
    return p


def parse_args(argv):
    p = build_parser()
    a = p.parse_args(argv)
    try:
        a.chart = validate_params(a.asset, a.chart)
    except SystemExit as exc:
        p.error(str(exc))
    if a.apply and not a.expect_plan:
        p.error("--apply requires --expect-plan <sha256>")
    if a.apply and not a.expect_evidence:
        p.error("--apply requires --expect-evidence <digest printed by the dry run>")
    return a


def refuse_under_test_outside_pytest(gate_fp, environ=None):
    """An under_test launch marker (run_gated.sh started with GATE_V2_UNDER_TEST=1) is for the test harness only: the executor refuses
    it, in every mode, unless PYTEST_CURRENT_TEST is set. Otherwise an operator shell with GATE_V2_UNDER_TEST=1 + GATE_V2_PGENV would
    pass the real launcher and reach the real database with only a WARNING."""
    environ = os.environ if environ is None else environ
    if gate_fp.get("under_test") and PYTEST_ENV not in environ:
        sys.stderr.write("REFUSED: the launch marker says the gate ran under test (GATE_V2_UNDER_TEST=1): the executor does not run "
                         "against a database from such a launch outside a pytest run. Start it through run_gated.sh without the test flag.\n")
        raise SystemExit(EXIT_NO_LAUNCH)


def launch_gate(environ=None):
    """GATE_V2 binding: the FIRST thing main() does. Refuses (exit 93) unless (a) executor_standards.py is the pinned file, and
    (b) GATE_V2_LAUNCH verifies: set by run_gated.sh after a passing gate, check recomputes, shas equal the live gate files AND
    the pins in GATE_PINS, not from the future, not older than 6 hours. Returns the live gate fingerprint.
    Convention-grade guard against accidents (running the executor directly, a stale or edited gate); not authentication."""
    if es.sha256_file(es.__file__) != GATE_PINS["executor_standards.py"]:
        sys.stderr.write("REFUSED: executor_standards.py differs from the version pinned in this executor (GATE_PINS)\n")
        raise SystemExit(EXIT_NO_LAUNCH)
    return es.require_gate_launch(environ, expected_gate_sha=GATE_PINS["prerun_gate.py"],
                                  expected_launcher_sha=GATE_PINS["run_gated.sh"])


def main(argv=None):
    gate_fp = launch_gate()             # FIRST: before the arguments are even parsed
    refuse_under_test_outside_pytest(gate_fp)
    args = parse_args(sys.argv[1:] if argv is None else argv)
    install_signal_handlers()
    try:
        code, result = execute(args, connect_admin, gate_fp=gate_fp)
    except SystemExit:
        raise
    except Exception as exc:
        print("failed: %s %s" % (type(exc).__name__, str(exc)[:200].replace("\n", " ")))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return code


if __name__ == "__main__":
    sys.exit(main())

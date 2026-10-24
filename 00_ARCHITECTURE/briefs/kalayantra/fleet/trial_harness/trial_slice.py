"""TRIAL_SLICE harness v2 (PLAN T1): the 12-class trial of the gochara '5.0' generation on a throwaway database of the local lane cluster, under an EXPLICITLY NAMED
result policy, with the per-path numbered/blank-by-reason report, the optional inline verification and G-6 cross-check stages, the dispatch-gate evaluator
G-1..G-8 (`gates.py`), the century projection and the 12-class all-null baseline.  Job-local; not repository code.

Method = the J-4c/J-4d proofs job (recipe) as re-run by the J-5q dry run: real migration chain + AM5 stub tables (the slice harness's own DB test setup) + the real
1306, 1308, 1381, 1398 files, the approved canonical L1 export loaded in replica mode, the rule registry seeded, then the REAL `j4d_slice_qualify.build_slice` called
once per pending substep, final rules, strict certification, in-build verify DEFERRED (the final build's shape).  The harness never edits the checkout.

  trial_slice.py run       --checkout PATH --result-policy POLICY --out DIR [--label L] [--classes a,b,..] [--budget-s N] [--keep-db] [--code-head SHA]
                           [--baseline baseline_12.json] [--gate-entry module:function] [--verify] [--crosscheck [--crosscheck-seed N]]
  trial_slice.py report    --out DIR            re-render the report from the DB the state names (no build)
  trial_slice.py drop      --out DIR            drop the throwaway DB the state names (only one this harness created)
  trial_slice.py baseline  --report FILE --out baseline_12.json [--prior-4class FILE]     the all-null baseline from a passed default-policy run
  trial_slice.py evaluate  --report FILE --baseline FILE --profile FILE [--second-report FILE] [--dispatch-checkout PATH | --dispatch-modules FILE]
                           [--verification-report FILE] [--out FILE]                       the G-1..G-8 verdict
  trial_slice.py project   --report FILE --profile FILE                                    the century projection only
  trial_slice.py trial-ready --out DIR --repo PATH [--ref SHA] [--timeout-s N]               TRIAL_READY/1 (the merged evaluator) → <out>/trial_ready.json, attached to the report
  trial_slice.py eq-record   --out DIR --eq-repo PATH [--eq-tool FILE] [--pinned-extra FILE] EQUIVALENCE_RECORD/1 (the merged tool) for the trial head, attached to the report
  trial_slice.py amd64-readiness --head SHA [--image-digest sha256:..] [--out FILE]          the command + inputs of the ONE amd64 slice per TR head (NOT run)
  trial_slice.py amd64-finish --out DIR [--eq-repo PATH ..]                                  finish an amd64-run whose driver was killed after the container ran to its end
  trial_slice.py amd64-run --head SHA (--repo PATH | --export DIR) --out DIR [--classes ..] [--image-digest sha256:..] [--eq-repo PATH ..]
                                                                                              the ONE amd64 slice per TR head IN A linux/amd64 DOCKER CONTAINER (SR-T24-AMD64-DOCKER; amd64_docker.py)
  trial_slice.py check-table [--decision-table FILE]                                          validate the G-3 decision table (data) and print its digest

A10.1 (T1B): every run loads and validates the G-3 decision table (`g3_decision_table.json`: floors, forbidden reasons, caps, noninterference kinds) and the gates are
evaluated UNDER it; the report carries the natural-key noninterference snapshot, the registry/L0/ephemeris/convention/config digests record, the per-stage effective
wall (compute and lock wait separately), the TRIAL_READY/1 evaluation, the EQUIVALENCE_RECORD summary and the DIAGNOSTIC/qualifying label.

POLICY is one of  default | all_null_candidate/1 | window_qualification/1.
  `default` passes NO policy to the build: the checkout's own default applies (the baseline oracle of the all-null generation).
  The two named values are passed EXPLICITLY (build_slice(result_policy=...) -> ctx.config["result_policy"], the key the century config's `result_policy` field
  overlays in the writer's `_resolve_run_config`).
A run with --budget-s stops launching new work after N seconds and exits 75; running the same command again resumes from <out>/state.json (build substeps, then
verification per class, then cross-check per window).
Exit codes: 0 report written (and the baseline oracle, when it applies, PASSED) · 1 oracle/defect failure · 2 refused/usage · 75 resume.
Output is class ids, counts, statuses, seconds and hashes only: no dates (outside the horizon bounds), no life-event rows, no chart values.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))                  # `python -I` does not put the script directory on sys.path
import amd64_docker as ad                      # noqa: E402  (AMD64-DOCKER)
import crosscheck as cx                        # noqa: E402
import g5_cpu                                  # noqa: E402  (G5-CPU)
import gates                                   # noqa: E402
import trial_eval as te                        # noqa: E402

MARKER = "TRIAL_SLICE"
CLASSES = list(gates.TRIAL_CLASSES_12)          # the 4 ruled classes + the 8 decision-pending ND-H classes (PLAN §4.1)
ORIGINAL_4 = ("bereavement", "chronic_onset", "illness_acute", "major_loss")
NEW_8 = tuple(c for c in CLASSES if c not in ORIGINAL_4)
#: the all-null baseline of the 4 ruled classes, measured by the previous harness on origin/main d7552d029 (1,672 windows): a regression oracle for the 12-class
#: all-null baseline — the same classes on current main must reproduce it, or something other than the policy moved the window grain
PRIOR_4CLASS_WINDOWS = {"bereavement": 397, "chronic_onset": 447, "illness_acute": 447, "major_loss": 381}
SOLVER_MODULE = "services.gochara_kernel.window_solver"      # PLAN §2.7: where the checkout's solver lives; --solver-module overrides if it is named otherwise
DECISION_TABLE = HERE / "g3_decision_table.json"
HEAD_KINDS = ["rules", "convention", "body", "manifest", "snapshot"]          # class-less substep kinds (do not grow with the class count)
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
GENERATION = "5.0"
ADMIN_DSN = "postgresql://postgres@127.0.0.1:55433/postgres"
EPHE = "/Users/Dev/kalayantra/ephe"
EXPORT = Path("/Users/Dev/kalayantra/run/canonical_l1/20261016T135745Z")
DB_PREFIX = "ky_trial_"
POLICIES = ("default", "all_null_candidate/1", "window_qualification/1")
BASELINE_WINDOWS = 1672                       # the 4-class all-null baseline (J-4c proofs; J-5q dry run) — see PRIOR_4CLASS_WINDOWS
BASELINE_INFO = {"window_records": 24380, "contacts": 10644, "near_miss": 40}      # J-5q dry run on 3699138 (informational, not an oracle)
MIGRATIONS = ["1306_gochara_expected_class_census.sql", "1308_gochara_near_miss_storage.sql",
              "1381_gochara_near_miss_seal_integration.sql", "1398_gochara_snapshot_dasha_held.sql"]
LANE_FILES = ["1305_gochara_snapshot_owns_l1_copy.sql"] + MIGRATIONS
#: TR_GAPS B4.3 / F3: the AM5 stub has no L0 reference tables and no 1402 CHECK, so the merged P1 loaders (bg_dignity_reference, bg_combustion_orbs,
#: bg_graha_naisargika_friendship) raise UndefinedTable and any Form B window INSERT is unchecked.  After the stub and MIGRATIONS these real files are applied, in this order:
#: 250 seeds the three L0 tables (9 + 72 + 8 rows), 1401 is the node-dignity correction (its guard demands the 250 rows), 1402 is the solver-certificate CHECK.
#: 1403 edits the ka_gochara_v5 asset_registry row; the stub has no asset_registry, so it is applied only where its table exists and is otherwise RECORDED as skipped
#: (its ledger row is the lane database's business, T23).  (name, mandatory, table the file edits)
OVERLAY_MIGRATIONS = (("250_bg_dignity_reference.sql", True, None),
                      ("1401_l0_node_dignity_friendship.sql", True, None),
                      ("1402_gochara_qualification_provenance_certificate.sql", True, None),
                      ("1403_ka_gochara_v5_depends_on_l0_dignity.sql", False, "asset_registry"))
LANE_DB_DEFAULT = "ky_lane_head"            # TR_GAPS B4.1: the named, persistent head-chain database T10/T23/T25 read (built by the ops job, rebuilt after each integration advance)
LANE_DB_RE = re.compile(r"ky_lane_[a-z0-9_]{1,40}")
LANE_SHA_PROOFS = {      # the proofs job's lane.tsv (J-4c): informational drift detector for the lane's migration files
    "1305_gochara_snapshot_owns_l1_copy.sql": "b7ad2ba40ae81b29a2672c41a9f44212c67347e382dabefa153227a93da19a31",
    "1306_gochara_expected_class_census.sql": "b55e244e0e76fe783ad10e25656ecace29ead19ef7625a0668098e6529b2c574",
    "1308_gochara_near_miss_storage.sql": "bc7a220970b91d2d60b1532368e106df673f63a56d573d88acd78857e665204b",
    "1381_gochara_near_miss_seal_integration.sql": "8dd3ec863d58f77939314429a937a3412b359205bba5aba8afb8fc61c5056586",
    "1398_gochara_snapshot_dasha_held.sql": "3cf844b51ce671a402a1dfa31dde446082e4fe732131c13f38569f3e6575f741"}
BATCH = 5000
EX_RESUME = 75


# ── small helpers ───────────────────────────────────────────────────────────────────────────────────────────────

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha_bytes(p.read_bytes())


def scrub(text: str, limit: int = 300) -> str:
    """No dates and no long numbers leave this harness (refusal/exception text of a gate may quote an interval)."""
    text = re.sub(r"\d{4}-\d{2}-\d{2}([T ][0-9:.+\-Z]*)?", "<date>", str(text))
    text = re.sub(r"\d{6,}", "<num>", text)
    return text[:limit]


def write_json(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    tmp.replace(path)


def git(checkout: Path, *args: str) -> str | None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        return subprocess.run(["git", "-C", str(checkout), *args], capture_output=True, text=True, timeout=60, env=env).stdout.strip()
    except Exception:                                                       # noqa: BLE001
        return None


def job_name(out: Path) -> str:
    return Path(os.environ.get("JOB_SCRATCH", str(out))).name


class Refused(SystemExit):
    def __init__(self, msg: str, code: int = 2):
        print(f"REFUSED: {msg}", file=sys.stderr)
        super().__init__(code)


# ── checkout binding ────────────────────────────────────────────────────────────────────────────────────────────

def bind_checkout(checkout: Path) -> Path:
    """Put the checkout's sidecar on sys.path, chdir into it and set the lane environment; returns the sidecar directory."""
    sidecar = checkout / "platform" / "python-sidecar"
    if not (sidecar / "scripts" / "kala_gochara_cutover" / "j4d_slice_qualify.py").is_file():
        raise Refused(f"{checkout} is not a madhav checkout carrying scripts/kala_gochara_cutover/j4d_slice_qualify.py")
    os.environ.update({"SE_EPHE_PATH": EPHE, "GOCHARA_SE1_REQUIRE": "1", "PYTHONDONTWRITEBYTECODE": "1", "KALA_REQUIRE_DB": "1",
                       "KALA_ADMIN_DSN": ADMIN_DSN, "SIDECAR": str(sidecar)})
    sys.path.insert(0, str(sidecar))
    os.chdir(sidecar)
    return sidecar


# ── setup: the lane database ────────────────────────────────────────────────────────────────────────────────────

def prod_columns(table: str) -> dict:
    text = (EXPORT / "schema.sql").read_text()
    block = re.search(r"CREATE TABLE public\.%s \((.*?)\n\);" % table, text, re.S).group(1)
    cols = {}
    for line in block.splitlines():
        m = re.match(r"\s+([a-z_0-9]+) ((?:timestamp with time zone|double precision|text\[\]|[a-z]+))", line)
        if m and m.group(1) != "constraint":
            cols[m.group(1)] = m.group(2)
    return cols


def load_table(conn, table: str, rows: list) -> dict:
    have = {r[0] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s", (table,))}
    prod = prod_columns(table)
    for col in sorted(set(rows[0]) - have):
        if col not in prod:
            raise Refused(f"{table}.{col}: exported column unknown to the production schema")
        conn.execute(f'ALTER TABLE public.{table} ADD COLUMN IF NOT EXISTS "{col}" {prod[col]}')
    conn.execute(f"DELETE FROM public.{table} WHERE chart_id = %s", (CHART,))                       # the AM5 stub rows go
    for i in range(0, len(rows), BATCH):
        conn.execute(f"INSERT INTO public.{table} SELECT * FROM jsonb_populate_recordset(NULL::public.{table}, %s::jsonb)", (json.dumps(rows[i:i + BATCH]),))
    return {"table": table, "rows": len(rows)}


LANE_EFFECTS = {      # the migration's OWN effect, read back (the recipe applies file text, so a ledger read would be vacuous) — from the proofs job's lane_applied.py
    "1305": ("SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='ka_gochara_search_input_snapshot' AND column_name='consumed_fact_rows'",),
    "1306": ("SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname='ka_gochara_search_completeness_violations' AND position('expected_class_list_missing' IN prosrc) > 0",),
    "1308": ("SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace AND relname='ka_gochara_near_miss'",),
    "1381": ("SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace AND relname='ka_gochara_near_miss_verification'",),
    "1398": ("SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='ka_gochara_search_input_snapshot' AND column_name='consumed_dasha_held'",)}
OVERLAY_EFFECTS = {      # each overlay file's OWN effect, read back as a boolean (a ledger row would be vacuous: the overlay applies file text)
    "250": "SELECT (SELECT count(*) FROM public.bg_dignity_reference) = 9 AND (SELECT count(*) FROM public.bg_graha_naisargika_friendship) = 72 AND (SELECT count(*) FROM public.bg_combustion_orbs) = 8",
    "1401": ("SELECT (SELECT count(*) FROM public.bg_graha_naisargika_friendship WHERE (graha, other_graha, relation) IN (('Rahu','Mercury','neutral'),('Rahu','Mars','enemy'),"
             "('Rahu','Jupiter','friend'),('Ketu','Sun','enemy'),('Ketu','Moon','enemy'))) = 5 AND (SELECT count(*) FROM public.bg_dignity_reference WHERE (graha, moolatrikona_sign) "
             "IN (('Rahu','Gemini'),('Ketu','Sagittarius'))) = 2 AND (SELECT count(*) FROM public.bg_dignity_reference WHERE (graha, exaltation_sign) IN (('Rahu','Taurus'),('Ketu','Scorpio'))) = 2"),
    "1402": "SELECT to_regprocedure('public.ka_gochara_solver_certificate_ok(jsonb)') IS NOT NULL AND to_regprocedure('public.ka_gochara_window_qualification_ok(jsonb)') IS NOT NULL",
    "1403": "SELECT (SELECT depends_on FROM public.asset_registry WHERE asset_id = 'ka_gochara_v5') @> ARRAY['bg_dignity_reference']::text[]"}


#: SR-BASELINE-OVERLAY-SKIP: the code each MANDATORY overlay exists for, probed in the checkout's own production python (`platform/python-sidecar/services`, tests excluded).  A baseline of
#: origin/main legitimately lacks an overlay file whose requiring code has not merged yet; it may skip that file only when the checkout provably lacks that code.  The probe reads what the
#: code WRITES or READS (never a function name that a test or the harness also mentions): 250 and 1401 seed the three L0 tables the P1 loaders read; 1402 widens the window `qualification`
#: CHECK for the two keys `combustion_inheritance` (R-4) and `solver_certificate` (R-6/R-7), which the P1 builder / window solver write.  (1403 is not mandatory: it is always skippable.)
OVERLAY_REQUIRING_CODE = {
    "250_bg_dignity_reference.sql": re.compile(r"\b(?:bg_dignity_reference|bg_combustion_orbs|bg_graha_naisargika_friendship)\b"),
    "1401_l0_node_dignity_friendship.sql": re.compile(r"\b(?:bg_dignity_reference|bg_graha_naisargika_friendship)\b"),
    "1402_gochara_qualification_provenance_certificate.sql": re.compile(r"\b(?:combustion_inheritance|solver_certificate|stored_certificate|ka_gochara_solver_certificate_ok)\b"),
}
REQUIRING_CODE_ROOT = ("platform", "python-sidecar", "services")


def requiring_code(checkout: Path, overlay_file: str) -> list[str]:
    """The checkout's production python files (repo-relative, sorted) that need `overlay_file`; [] = provably none.  Refuses when the code root is absent (an unreadable checkout proves nothing)."""
    root = checkout.joinpath(*REQUIRING_CODE_ROOT)
    if not root.is_dir():
        raise Refused(f"cannot prove the requiring code of {overlay_file} is absent: {'/'.join(REQUIRING_CODE_ROOT)} is not a directory in the checkout")
    pat = OVERLAY_REQUIRING_CODE[overlay_file]
    hits = []
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root).parts                                  # relative to the code root: a checkout that itself lives under a directory named `tests` must not hide its production code
        if "tests" in rel or "__pycache__" in rel or p.name.startswith("test_"):
            continue
        if pat.search(p.read_text(encoding="utf-8", errors="replace")):
            hits.append(p.relative_to(checkout).as_posix())
    return hits


def plan_overlay(mig_dir: Path, has_table, *, baseline_checkout: Path | None = None) -> tuple[list[str], dict]:
    """(overlay files to apply, in order; {file: why it is skipped}).  A mandatory file missing from the checkout REFUSES — a trial database without the L0 seeds and the 1402 CHECK cannot
    run the merged P1 code — while an optional one is skipped BY NAME and recorded, never silently.  SR-BASELINE-OVERLAY-SKIP: only with `baseline_checkout` (BASELINE mode: make_baseline.sh,
    default policy, label baseline — see `baseline_mode_requested`) a missing mandatory file is skipped by name, and only when the checkout ALSO lacks the code that requires it; if any such
    code exists the run still REFUSES."""
    todo: list[str] = []
    skipped: dict = {}
    for f, mandatory, table in OVERLAY_MIGRATIONS:
        if not (mig_dir / f).is_file():
            if mandatory:
                if baseline_checkout is None:
                    raise Refused(f"overlay migration file missing in the checkout: {f}")
                code = requiring_code(baseline_checkout, f)
                if code:
                    raise Refused(f"overlay migration file missing in the checkout: {f} (baseline mode does not skip it: the checkout has the code that requires it, e.g. {code[0]})")
                skipped[f] = "baseline mode: absent in the checkout, and the checkout has no code that requires it (SR-BASELINE-OVERLAY-SKIP)"
                continue
            skipped[f] = "absent in the checkout"
        elif table is not None and not has_table(table):
            skipped[f] = f"table {table} is absent from the trial database"
        else:
            todo.append(f)
    return todo, skipped


def dsn_for(db: str) -> str:
    """The loopback DSN (no credential) of database `db` on the lane cluster named by ADMIN_DSN."""
    return urlunsplit(urlsplit(ADMIN_DSN)._replace(path="/" + db))


def lane_dsn(name: str | None = None) -> str:
    """The DSN of the named lane database T10/T23/T25 read (TR_GAPS B4): `name`, else $TRIAL_LANE_DB, else ky_lane_head.  Only ky_lane_* names are accepted, so the evaluator can never be
    pointed at a trial, test or foreign database by a typo."""
    name = name or os.environ.get("TRIAL_LANE_DB") or LANE_DB_DEFAULT
    if not LANE_DB_RE.fullmatch(name):
        raise Refused(f"the lane database name {name!r} is not ky_lane_<name>: refusing to point the TRIAL_READY/1 evaluator at it")
    return dsn_for(name)


def dsn_label(dsn: str) -> str:
    u = urlsplit(dsn)
    return f"db:{u.hostname}:{u.port}/{(u.path or '').lstrip('/')}"


@contextlib.contextmanager
def trial_ready_dsns(state: dict):
    """Export TRIAL_READY_LANE_DSN (the named lane database) and TRIAL_READY_TRIAL_DSN (THIS run's trial database, only while it still exists) for the evaluator, for the duration of the
    stage only.  A TRIAL_READY_TRIAL_DSN inherited from the caller is removed when this run has no live trial database, so a stale value can never stand in for it.  Yields the credential-free
    labels (host:port/db)."""
    keys = ("TRIAL_READY_LANE_DSN", "TRIAL_READY_TRIAL_DSN")
    want = {"TRIAL_READY_LANE_DSN": lane_dsn()}
    if state.get("db") and not state.get("dropped"):
        want["TRIAL_READY_TRIAL_DSN"] = dsn_for(state["db"])
    saved = {k: os.environ.get(k) for k in keys}
    try:
        for k in keys:
            if k in want:
                os.environ[k] = want[k]
            else:
                os.environ.pop(k, None)
        yield {k: dsn_label(v) for k, v in want.items()}
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def setup_lane(state: dict, checkout: Path, out: Path) -> None:
    import psycopg
    from psycopg.conninfo import make_conninfo
    from tests.l3.gochara._disposable_db_guard import guarded_admin_connect
    from tests.l3.gochara.test_a53_inventory import _populate_am5_database
    from services.gochara_kernel.rule_registry import RuleRegistryStore
    from scripts.kala_gochara_cutover import j4d_slice_qualify as q

    manifest = json.loads((EXPORT / "manifest.json").read_text())
    for name, meta in manifest["files"].items():                         # the approved bytes, before use
        if name in ("chart_facts.json", "chart_dashas.json") and sha_file(EXPORT / name) != meta["sha256"]:
            raise Refused(f"{name} bytes differ from the approved canonical-L1 manifest")
    mig_dir = checkout / "platform" / "migrations"
    for f in MIGRATIONS:
        if not (mig_dir / f).is_file():
            raise Refused(f"migration file missing in the checkout: {f}")
    base_co = checkout if state.get("baseline_mode") else None
    plan_overlay(mig_dir, lambda _t: True, baseline_checkout=base_co)    # a mandatory overlay file missing in the checkout refuses BEFORE a database is created (baseline mode: unless the code needing it is absent too)
    t0 = time.time()
    name = f"{DB_PREFIX}{uuid.uuid4().hex[:8]}"
    admin = guarded_admin_connect(ADMIN_DSN, autocommit=True, connect_timeout=5)
    admin.execute(f'CREATE DATABASE "{name}"')
    admin.execute(f"COMMENT ON DATABASE \"{name}\" IS 'ky.job={job_name(out)}'")
    state["db"] = name                                                    # recorded before anything else can fail: the drop must find it
    write_json(out / "state.json", state)
    dsn = make_conninfo(ADMIN_DSN, dbname=name)
    lane = {"database_created_by": job_name(out)}
    with psycopg.connect(dsn, autocommit=True, connect_timeout=5) as conn:
        _populate_am5_database(conn, apply_1305=True)
        for f in MIGRATIONS:                                              # the real files, one transaction each, lane connection only
            q.require_lane(conn)
            with conn.transaction():
                conn.execute((mig_dir / f).read_text(encoding="utf-8"))
        overlay, overlay_skipped = plan_overlay(mig_dir, lambda t: conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"public.{t}",)).fetchone()[0],
                                                 baseline_checkout=base_co)
        for f in overlay:                                                 # TR_GAPS B4.3: the L0 P1 seeds (250), node dignity (1401), the 1402 CHECK, and 1403 where its table exists
            q.require_lane(conn)
            with conn.transaction():
                conn.execute((mig_dir / f).read_text(encoding="utf-8"))
        facts = json.loads((EXPORT / "chart_facts.json").read_text())
        dashas = json.loads((EXPORT / "chart_dashas.json").read_text())
        if not ({r["chart_id"] for r in facts} == {CHART} == {r["chart_id"] for r in dashas}):
            raise Refused("the canonical L1 export names another chart")
        with conn.transaction():
            if conn.execute("SHOW session_replication_role").fetchone()[0] != "origin":
                raise Refused("session_replication_role is not origin before the L1 load")
            conn.execute("SET LOCAL session_replication_role = replica")
            lane["loads"] = [load_table(conn, "chart_facts", facts), load_table(conn, "chart_dashas", dashas)]
        got = {"chart_facts": conn.execute("SELECT count(*) FROM public.chart_facts WHERE chart_id=%s", (CHART,)).fetchone()[0],
               "chart_dashas": conn.execute("SELECT count(*) FROM public.chart_dashas WHERE chart_id=%s", (CHART,)).fetchone()[0]}
        if got != {"chart_facts": len(facts), "chart_dashas": len(dashas)}:
            raise Refused(f"L1 row counts differ from the export: {got}")
        h = lambda items: hashlib.sha256("\n".join(sorted(items)).encode()).hexdigest()          # noqa: E731
        lane["fact_id_set_equal"] = h(r["fact_id"] for r in facts) == h(str(r[0]) for r in conn.execute("SELECT fact_id FROM public.chart_facts WHERE chart_id=%s", (CHART,)))
        lane["dasha_id_set_equal"] = h(r["dasha_row_id"] for r in dashas) == h(str(r[0]) for r in conn.execute("SELECT dasha_row_id FROM public.chart_dashas WHERE chart_id=%s", (CHART,)))
        if not (lane["fact_id_set_equal"] and lane["dasha_id_set_equal"]):
            raise Refused("the loaded L1 id sets differ from the approved export")
        schema_text = (EXPORT / "schema.sql").read_text()
        for m in re.finditer(r"^(CREATE INDEX (?:cd_parent_idx|cd_temporal_lookup_idx|cd_lord_lookup_idx|cd_chart_accretion_key_idx|chart_facts_chart_id_idx|"
                             r"chart_facts_subject_idx|chart_facts_chart_cat_sub_key_idx|chart_facts_chart_aya_cat_idx) ON [^;]+;)", schema_text, re.M):
            conn.execute(m.group(1))
        conn.execute("ANALYZE public.chart_dashas")
        conn.execute("ANALYZE public.chart_facts")
        RuleRegistryStore(conn).seed()
        effects = {}
        for num, (sql,) in LANE_EFFECTS.items():
            effects[num] = conn.execute(sql).fetchone()[0] == 1
        if not all(effects.values()):
            raise Refused(f"the lane lacks the effect of migration(s) {[k for k, v in effects.items() if not v]}: it is not the final build's database")
        lane["migration_effects_present"] = effects
        overlay_effects = {f.split("_", 1)[0]: bool(conn.execute(OVERLAY_EFFECTS[f.split("_", 1)[0]]).fetchone()[0]) for f in overlay}
        if not all(overlay_effects.values()):
            raise Refused(f"the trial database lacks the effect of overlay migration(s) {[k for k, v in overlay_effects.items() if not v]}")
        lane["overlay_applied"] = overlay
        lane["overlay_skipped"] = overlay_skipped
        lane["overlay_effects_present"] = overlay_effects
        lane["overlay_sha256"] = {f: sha_file(mig_dir / f) for f in overlay}
        lane["migration_sha256_equal_to_proofs_job"] = {f: sha_file(mig_dir / f) == LANE_SHA_PROOFS[f] for f in LANE_FILES if (mig_dir / f).is_file()}
        lane["server_version"] = conn.execute("SHOW server_version").fetchone()[0]
        lane["port"] = conn.execute("SELECT inet_server_port()").fetchone()[0]
    admin.close()
    lane["setup_s"] = round(time.time() - t0, 1)
    state["lane"] = lane
    write_json(out / "state.json", state)


# ── build: one build_slice call per pending substep (resumable) ─────────────────────────────────────────────────

def ruled_horizon() -> tuple:
    """The horizon the slice (and, unless the dispatch says otherwise, the century run) builds: the ruled horizon of the checkout (ruling 7+13)."""
    from services.gochara_kernel import horizon as H
    return tuple(H.RULED_HORIZON)


@contextlib.contextmanager
def probe_solver(calls: dict, name: str = "services.gochara_kernel.window_solver"):
    """Count the calls into the checkout's solver module, if it has one (`services.gochara_kernel.window_solver`, PLAN §2.7): every public function DEFINED in
    that module is wrapped and every module-level alias of it (a `from .window_solver import solve` binding) is re-pointed for the duration.  Yields whether the
    module is present.  With no solver module (SR-OD1 head, main) it yields False and counts nothing — the legacy `maximise_earliest` counter is separate."""
    import importlib
    try:
        mod = importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name != name:
            raise
        yield False
        return
    patched = []
    holders = [m for n, m in list(sys.modules.items()) if m is not None and n.startswith(("services.gochara_kernel", "pipeline.orchestrator"))]
    for fname, fn in list(vars(mod).items()):
        if fname.startswith("_") or isinstance(fn, type) or not callable(fn) or getattr(fn, "__module__", None) != name:
            continue

        def make(_n, _f):
            def counted(*args, **kwargs):
                calls[_n] = calls.get(_n, 0) + 1
                return _f(*args, **kwargs)
            counted.__wrapped__ = _f
            return counted
        wrapper = make(fname, fn)
        for holder in holders:
            for attr, val in list(vars(holder).items()):
                if val is fn:
                    setattr(holder, attr, wrapper)
                    patched.append((holder, attr, fn))
    try:
        yield True
    finally:
        for holder, attr, fn in patched:
            setattr(holder, attr, fn)


def make_clock(state: dict) -> "te.StageClock":
    """One effective-wall clock per run, restored from state.json on a resume; its probe asks the cluster (a separate admin connection) who waits on a lock."""
    clock = te.StageClock(te.lock_probe(ADMIN_DSN, state["db"]))
    clock.load(state.get("effective_wall"))
    return clock


def make_cpu_meter(state: dict):
    """G5-CPU: one attributed-CPU meter per stage loop (SR-G5-LOAD), restored from state.json on a resume; a seam like `make_clock`."""
    return g5_cpu.make_meter(ADMIN_DSN, state.get("db"), state)


def build(state: dict, out: Path, deadline: float | None) -> bool:
    """Returns True when the plan is complete (every substep done or its class closed by a defect).  `deadline` = an absolute time.time(), or None.

    Two modes (HARNESS-3.3, O-2).  Default = stop-at-first (the TR shape): a class's first defect closes the class, its later grains are never run.  `state["collect"]` = COLLECT (a diagnostic /
    PRETR run): a defect does NOT close the class; every remaining grain of it is still evaluated and the class is marked dead only at the END, with the full defect list."""
    import psycopg
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    from scripts.kala_gochara_cutover import j4d_slice_qualify as q

    classes = state["classes"]
    policy = None if state["requested_policy"] == "default" else state["requested_policy"]
    horizon = ruled_horizon()
    state["horizon"] = {"start": horizon[0].isoformat(), "end": horizon[1].isoformat(), "days": (horizon[1] - horizon[0]).total_seconds() / 86400.0}
    done = {s["step"] for s in state["steps"]} | {d["step"] for d in state["defects"]}
    collect = bool(state.get("collect"))
    dead = set() if collect else set(state.get("dead_classes", []))                    # COLLECT never skips a class on a defect: dead_classes is written once, at the end
    stage: dict = {}                                                                    # O-1: the kind of the step about to run, set BEFORE it runs so a failed step is booked under its own kind
    real_plan = writer_mod.GocharaV5Writer.plan_substeps
    real_run = writer_mod.GocharaV5Writer.run_substep
    plan_seen: list = []

    def next_only(self, ctx):
        steps = [s for s in real_plan(self, ctx) if writer_mod._class_of_grain(s.key) in set(classes) | {None}]
        plan_seen[:] = [s.key for s in steps]
        pending = [s for s in steps if s.key not in done and writer_mod._class_of_grain(s.key) not in dead]
        if pending:
            stage["kind"] = pending[0].key.split(":")[0]
        return pending[:1]

    def run_deferring(self, ctx, step):                                   # the final build's own shape: verify:<class> is the named deferral no-op
        ctx.config[writer_mod.DEFER_VERIFY_KEY] = True
        return real_run(self, ctx, step)

    writer_mod.GocharaV5Writer.plan_substeps = next_only
    writer_mod.GocharaV5Writer.run_substep = run_deferring
    dsn = f"postgresql://postgres@127.0.0.1:55433/{state['db']}"
    obs = state.setdefault("observed", {"certification_policies": [], "maximise_earliest_calls": 0, "near_miss_layer": []})
    obs.setdefault("solver_calls", {})
    complete = False
    clock = make_clock(state)
    meter = make_cpu_meter(state)                                                                            # G5-CPU: attributed CPU per stage (SR-G5-LOAD)
    with contextlib.closing(clock), contextlib.closing(meter), psycopg.connect(dsn, autocommit=True, connect_timeout=5) as conn:       # closing(clock) releases the lock probe's admin connection (N4)
        while True:
            if deadline is not None and time.time() >= deadline:
                break
            notes: dict = {}
            t0 = time.time()
            stage.clear()
            with clock.measure(lambda: "build:" + stage.get("kind", "empty")), meter.measure(lambda: "build:" + stage.get("kind", "empty")) as cpu_box:       # T17: compute and lock wait, per stage; G5-CPU
                with probe_solver(obs["solver_calls"], state.get("solver_module") or SOLVER_MODULE) as present:
                    obs["solver_module_present"] = bool(present)
                    res = q.build_slice(conn, chart_id=CHART, horizon=horizon, classes=classes, ephe_path=EPHE, build_id="trial-slice", final_rules=True,
                                        result_policy=policy, on_step=lambda k, r: notes.update({k: (r.notes or "")}))
            secs = round(time.time() - t0, 2)
            state["effective_wall"] = clock.record()
            state["g5_cpu"] = meter.record()                                                  # G5-CPU
            if not res["steps"] and not res["defects"]:
                complete = True
                break
            obs["certification_policies"] += res["observed"]["certification_policies"]
            obs["maximise_earliest_calls"] += res["observed"]["maximise_earliest_calls"]
            obs["near_miss_layer"].append(res["near_miss_layer"])
            for s in res["steps"]:
                state["steps"].append({"step": s["step"], "rows": s["rows"], "secs": secs, "cpu_s": cpu_box["cpu_s"]})
                done.add(s["step"])
                print(f"{secs:9.2f}s  {s['step']}", flush=True)
            for d in res["defects"]:
                state["defects"].append({"step": d["step"], "kind": d["step"].split(":")[0], "status": "failed" if d["defect"] == "substep_raised" else d["defect"],
                                         "defect": d["defect"], "detail": scrub(d.get("detail", "")), "secs": secs})
                done.add(d["step"])
                cls = writer_mod._class_of_grain(d["step"])
                print(f"{secs:9.2f}s  {d['step']}  DEFECT {d['defect']}", flush=True)
                if cls is None:
                    state["aborted"] = f"class-less substep {d['step']} raised"
                    complete = True
                elif not collect:
                    dead.add(cls)
                    state["dead_classes"] = sorted(dead)
            write_json(out / "state.json", state)
            if state.get("aborted"):
                break
    if collect and complete:                                                            # the END: every class that carries a defect is failed, with all its defects in state["defects"]
        state["dead_classes"] = sorted({writer_mod._class_of_grain(d["step"]) for d in state["defects"]} - {None})
    state["plan_substeps"] = list(plan_seen) or state.get("plan_substeps", [])
    write_json(out / "state.json", state)
    return complete


# ── analysis ────────────────────────────────────────────────────────────────────────────────────────────────────

NUMERIC = ("score", "evidence_for", "severity", "peak_instant")
WINDOW_SQL = """
SELECT event_class, path_id,
       count(*)                                                                         AS total,
       count(*) FILTER (WHERE peak_instant IS NOT NULL)                                 AS with_peak,
       count(*) FILTER (WHERE score IS NOT NULL)                                        AS with_score,
       count(*) FILTER (WHERE evidence_for IS NOT NULL)                                 AS with_evidence_for,
       count(*) FILTER (WHERE severity IS NOT NULL)                                     AS with_severity,
       count(*) FILTER (WHERE score IS NOT NULL OR evidence_for IS NOT NULL OR severity IS NOT NULL OR peak_instant IS NOT NULL
                                OR evidence_against IS NOT NULL OR objective_value IS NOT NULL) AS with_any_number,
       count(*) FILTER (WHERE score IS NULL AND evidence_for IS NULL AND severity IS NULL AND peak_instant IS NULL
                                AND evidence_against IS NULL AND objective_value IS NULL)   AS blank,
       count(*) FILTER (WHERE score IS NULL AND (evidence_for IS NOT NULL OR severity IS NOT NULL OR peak_instant IS NOT NULL
                                OR evidence_against IS NOT NULL OR objective_value IS NOT NULL)) AS number_without_score,
       count(*) FILTER (WHERE peak_instant IS NOT NULL AND score IS NULL)               AS peak_without_score,
       count(*) FILTER (WHERE outcome_valence_for_native <> 'unqualified' AND score IS NULL) AS valence_without_score
FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s)
GROUP BY event_class, path_id"""
GRAIN_SQL = """
SELECT event_class, path_id, rule_version, count(*) AS windows,
       count(*) FILTER (WHERE peak_instant IS NOT NULL) AS numbered,
       count(*) FILTER (WHERE score IS NOT NULL)        AS with_score,
       count(*) FILTER (WHERE peak_instant IS NULL)     AS not_numbered
FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s)
GROUP BY 1, 2, 3 ORDER BY 1, 2, 3"""
GRAIN_REASON_SQL = """
SELECT event_class, path_id, rule_version,
       COALESCE(qualification ->> 'unqualified_reason', CASE WHEN qualification IS NULL THEN 'no_qualification_recorded' ELSE 'none_recorded' END) AS reason, count(*)
FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s) AND peak_instant IS NULL
GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4"""
# a window's STORED reason is only the first (sorted) unresolved one; the others sit in `qualification.unresolved`.  This counts each not-numbered window
# once per distinct code it carries in EITHER place — the number the wiring gate (G-2) and the solver-budget cap (G-3) must read.
GRAIN_ANY_REASON_SQL = """
SELECT event_class, path_id, rule_version, code, count(*) FROM (
  SELECT DISTINCT w.window_id, w.event_class, w.path_id, w.rule_version, c.code
  FROM public.ka_gochara_eval_window w
  CROSS JOIN LATERAL (
     SELECT w.qualification ->> 'unqualified_reason' AS code WHERE w.qualification ->> 'unqualified_reason' IS NOT NULL
     UNION
     SELECT k FROM jsonb_object_keys(CASE WHEN jsonb_typeof(w.qualification -> 'unresolved') = 'object' THEN w.qualification -> 'unresolved' ELSE '{}'::jsonb END) k
  ) c
  WHERE w.chart_id = %s AND w.generation = %s AND w.event_class = ANY(%s) AND w.peak_instant IS NULL) z
GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4"""
VALENCE_SQL = """SELECT event_class, outcome_valence_for_native, count(*) FROM public.ka_gochara_eval_window
                 WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s) GROUP BY 1, 2"""
BLANK_SQL = """SELECT event_class, COALESCE(qualification ->> 'unqualified_reason', CASE WHEN qualification IS NULL THEN 'no_qualification_recorded'
                                                                                        ELSE 'none_recorded' END) AS reason, count(*)
               FROM public.ka_gochara_eval_window
               WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s) AND score IS NULL AND evidence_for IS NULL AND severity IS NULL
                     AND peak_instant IS NULL AND evidence_against IS NULL AND objective_value IS NULL
               GROUP BY 1, 2"""
UNRESOLVED_SQL = """SELECT w.event_class, u.key, count(*) AS windows, sum((u.value)::numeric)::bigint AS members
                    FROM public.ka_gochara_eval_window w, LATERAL jsonb_each(w.qualification -> 'unresolved') u
                    WHERE w.chart_id = %s AND w.generation = %s AND w.event_class = ANY(%s) AND w.score IS NULL AND w.qualification IS NOT NULL
                          AND jsonb_typeof(w.qualification -> 'unresolved') = 'object'
                    GROUP BY 1, 2"""
UNRESOLVED_ALL_SQL = """SELECT w.event_class, u.key, count(*) AS windows, sum((u.value)::numeric)::bigint AS members
                        FROM public.ka_gochara_eval_window w, LATERAL jsonb_each(w.qualification -> 'unresolved') u
                        WHERE w.chart_id = %s AND w.generation = %s AND w.event_class = ANY(%s) AND w.qualification IS NOT NULL
                              AND jsonb_typeof(w.qualification -> 'unresolved') = 'object'
                        GROUP BY 1, 2"""
POLICY_SQL = """SELECT COALESCE(qualification ->> 'policy', 'none') AS policy, count(*) FROM public.ka_gochara_eval_window
                WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s) GROUP BY 1"""
#: window columns that are not part of "the window rows" for the byte-identity check (wall-clock stamps): excluded by NAME PATTERN and listed in the report
NONDETERMINISTIC_COLUMN = re.compile(r"(^|_)(created|updated|inserted|modified|recorded|written|ingested|loaded|verified)(_|$)|_at$")


def _zero():
    return {"windows_total": 0, "with_peak": 0, "with_score": 0, "with_evidence_for": 0, "with_severity": 0, "with_any_number": 0, "blank": 0, "number_without_score": 0,
            "valence": {}, "blank_reasons": {}, "unresolved_factors_in_blank_windows": {}, "unresolved_factors_all_windows": {}, "by_path": {}}


def window_rows_digest(conn, state: dict) -> dict:
    """sha256 over the canonical JSON of every stored window row of the trial classes (columns minus wall-clock stamps), in a total order, plus per-class
    digests and a digest of the (window_id, record_id) membership pairs.  G-7 compares two runs' digests."""
    cols = [r[0] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_eval_window'"
                                       " ORDER BY ordinal_position").fetchall()]
    excluded = [c for c in cols if NONDETERMINISTIC_COLUMN.search(c)]
    args = (excluded, CHART, GENERATION, state["classes"])
    total, per_class, n = hashlib.sha256(), {}, 0
    for ec, js in conn.execute("SELECT w.event_class, to_jsonb(w) - %s::text[] FROM public.ka_gochara_eval_window w WHERE w.chart_id = %s AND w.generation = %s"
                               " AND w.event_class = ANY(%s) ORDER BY w.event_class, w.path_id, w.rule_version, lower(w.interval), w.window_id", args):
        line = json.dumps(js, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        total.update(line + b"\n")
        per_class.setdefault(ec, hashlib.sha256()).update(line + b"\n")
        n += 1
    mem = hashlib.sha256()
    pairs = 0
    for (pair,) in conn.execute("SELECT window_id::text || ':' || record_id::text FROM public.ka_gochara_eval_window_record WHERE chart_id = %s AND generation = %s"
                                " AND event_class = ANY(%s) ORDER BY 1", (CHART, GENERATION, state["classes"])):
        mem.update(pair.encode() + b"\n")
        pairs += 1
    return {"sha256": total.hexdigest(), "windows": n, "columns": [c for c in cols if c not in excluded], "excluded_columns": excluded,
            "per_class": {c: h.hexdigest() for c, h in sorted(per_class.items())}, "memberships_sha256": mem.hexdigest(), "memberships": pairs}


TIE_ISOLATION_REASON = "tie_isolation_unresolved"          # the blank reason the near-station tie rule writes (SR-NEAR-STATION-TIE; window_solver.REASON_TIE_ISOLATION)


class _StoredBlank:
    """A stored window as `near_station_tie_report` reads it: only its `unqualified_reason` (the function counts from the drafts' own reason, nothing else)."""
    __slots__ = ("unqualified_reason",)

    def __init__(self, reason):
        self.unqualified_reason = reason


def near_station_tie_section(per: dict, report_fn=None) -> tuple[dict | None, str | None]:
    """SR-NEAR-STATION-TIE: the per-class count of windows blanked by the near-station tie rule, from `window_sweep.near_station_tie_report` fed the STORED windows of each class
    (one stand-in per window carrying its stored `unqualified_reason`; numbered windows carry none).  `report_fn` None = import it from the checkout; the function exists only on the
    od1 integration line, so when it cannot be imported the section is None with the reason — the gate then reads NOT_EVALUATED, never a pass (§N.8)."""
    if report_fn is None:
        try:
            from services.gochara_kernel import window_sweep as _ws
            report_fn = _ws.near_station_tie_report
        except (ImportError, AttributeError) as exc:
            return None, f"window_sweep.near_station_tie_report is not importable from this checkout ({type(exc).__name__})"
    drafts = {}
    for ec, c in sorted(per.items()):
        blank = c["blank_reasons"]
        stubs = [_StoredBlank(None)] * max(c["windows_total"] - sum(blank.values()), 0)
        for reason, n in sorted(blank.items()):
            stubs += [_StoredBlank(reason)] * n
        drafts[ec] = stubs
    return report_fn(drafts), None


def analyse(conn, state: dict, sidecar_mods: dict) -> dict:
    classes = state["classes"]
    args = (CHART, GENERATION, classes)
    per = {c: _zero() for c in classes}
    anomalies = {"number_without_score": 0, "peak_without_score": 0, "valence_without_score": 0, "blank_without_reason_code": 0}
    for ec, path, total, wpk, wsc, wev, wsv, wany, blank, nws, pws, vws in conn.execute(WINDOW_SQL, args).fetchall():
        c = per[ec]
        c["number_without_score"] += nws
        c["windows_total"] += total; c["with_peak"] += wpk; c["with_score"] += wsc; c["with_evidence_for"] += wev
        c["with_severity"] += wsv; c["with_any_number"] += wany; c["blank"] += blank
        c["by_path"][path] = {"windows": total, "with_score": wsc, "with_peak": wpk, "blank": blank}
        anomalies["number_without_score"] += nws; anomalies["peak_without_score"] += pws; anomalies["valence_without_score"] += vws
    for ec, val, n in conn.execute(VALENCE_SQL, args).fetchall():
        per[ec]["valence"][val] = n
    for ec, reason, n in conn.execute(BLANK_SQL, args).fetchall():
        per[ec]["blank_reasons"][reason] = n
        if reason in ("none_recorded", "no_qualification_recorded"):
            anomalies["blank_without_reason_code"] += n
    for ec, key, windows, members in conn.execute(UNRESOLVED_SQL, args).fetchall():
        per[ec]["unresolved_factors_in_blank_windows"][key] = {"windows": windows, "members": members}
    for ec, key, windows, members in conn.execute(UNRESOLVED_ALL_SQL, args).fetchall():
        per[ec]["unresolved_factors_all_windows"][key] = {"windows": windows, "members": members}
    totals = _zero()
    for c in per.values():
        for k in ("windows_total", "with_peak", "with_score", "with_evidence_for", "with_severity", "with_any_number", "blank", "number_without_score"):
            totals[k] += c[k]
        for k in ("valence", "blank_reasons"):
            for kk, v in c[k].items():
                totals[k][kk] = totals[k].get(kk, 0) + v
        for field in ("unresolved_factors_in_blank_windows", "unresolved_factors_all_windows"):
            for kk, v in c[field].items():
                t = totals[field].setdefault(kk, {"windows": 0, "members": 0})
                t["windows"] += v["windows"]; t["members"] += v["members"]
        for p, v in c["by_path"].items():
            t = totals["by_path"].setdefault(p, {"windows": 0, "with_score": 0, "with_peak": 0, "blank": 0})
            for kk in t:
                t[kk] += v[kk]
    for c in list(per.values()) + [totals]:
        c["valence"] = dict(sorted(c["valence"].items()))
        c["blank_without_reason_code"] = sum(n for r, n in c["blank_reasons"].items() if r in ("none_recorded", "no_qualification_recorded"))
    # ── the per-path / per-grain numbered-or-blank-by-reason report (PLAN T1) ──
    grains: dict = {}
    for ec, path, ver, windows, numbered, wsc, notnum in conn.execute(GRAIN_SQL, args).fetchall():
        grains[(ec, path, ver)] = {"event_class": ec, "path_id": path, "rule_version": ver, "windows": windows, "numbered": numbered, "with_score": wsc,
                                   "blank": notnum, "blank_by_reason": {}, "windows_with_reason": {}}
    for ec, path, ver, reason, n in conn.execute(GRAIN_REASON_SQL, args).fetchall():
        grains[(ec, path, ver)]["blank_by_reason"][reason] = n
    for ec, path, ver, code, n in conn.execute(GRAIN_ANY_REASON_SQL, args).fetchall():
        grains[(ec, path, ver)]["windows_with_reason"][code] = n
    paths: dict = {}
    by_class_path: dict = {c: {} for c in classes}
    reason_any: dict = {}
    for g in grains.values():
        p = paths.setdefault(g["path_id"], {"windows": 0, "numbered": 0, "with_score": 0, "blank": 0, "blank_by_reason": {}, "windows_with_reason": {}, "versions": {}})
        for k in ("windows", "numbered", "with_score", "blank"):
            p[k] += g[k]
        for k in ("blank_by_reason", "windows_with_reason"):
            for r, n in g[k].items():
                p[k][r] = p[k].get(r, 0) + n
        p["versions"][g["rule_version"]] = p["versions"].get(g["rule_version"], 0) + g["windows"]
        for r, n in g["windows_with_reason"].items():
            reason_any[r] = reason_any.get(r, 0) + n
        slot = by_class_path[g["event_class"]].setdefault(g["path_id"], {"windows": 0, "numbered": 0, "blank": 0, "blank_by_reason": {}})
        slot["windows"] += g["windows"]; slot["numbered"] += g["numbered"]; slot["blank"] += g["blank"]
        for r, n in g["blank_by_reason"].items():
            slot["blank_by_reason"][r] = slot["blank_by_reason"].get(r, 0) + n
    for p in paths.values():
        p["numbered_share"] = round(p["numbered"] / p["windows"], 6) if p["windows"] else None
        p["blank_by_reason"] = dict(sorted(p["blank_by_reason"].items()))
        p["windows_with_reason"] = dict(sorted(p["windows_with_reason"].items()))
    counts = {}
    for label, sql in (("window_records", "SELECT count(*) FROM public.ka_gochara_eval_window_record WHERE chart_id=%s AND generation=%s AND event_class = ANY(%s)"),
                       ("relationship_records", "SELECT count(*) FROM public.ka_gochara_relationship_record WHERE chart_id=%s AND generation=%s AND event_class = ANY(%s)"),
                       ("contacts", "SELECT count(*) FROM public.ka_gochara_contact WHERE chart_id=%s AND generation=%s"),
                       ("near_miss", "SELECT count(*) FROM public.ka_gochara_near_miss WHERE chart_id=%s AND generation=%s")):
        try:
            counts[label] = conn.execute(sql, args if "event_class" in sql else (CHART, GENERATION)).fetchone()[0]
        except Exception as exc:                                         # noqa: BLE001 — a missing relation is a null, never a guess
            counts[label] = None
            counts[f"{label}_error"] = type(exc).__name__
    stored_policies = {p: n for p, n in conn.execute(POLICY_SQL, args).fetchall()}
    manifest = None
    try:
        manifest = sidecar_mods["result_policy"].manifest_policy(conn, CHART, GENERATION)
    except Exception as exc:                                             # noqa: BLE001
        manifest = f"unreadable: {type(exc).__name__}"
    requested = state["requested_policy"]
    expected = None if requested == "default" else requested
    policy_effect = {"requested": requested, "manifest_policy": manifest, "window_qualification_policies": stored_policies}
    if expected is not None:
        policy_effect["took_effect"] = (manifest == expected and set(stored_policies) == {expected})
    else:
        policy_effect["took_effect"] = None
        policy_effect["note"] = "default policy requested: the checkout's own default applies; the baseline oracle below judges the outcome"
    tie, tie_why = near_station_tie_section(per)
    return {"classes": per, "totals": totals, "paths": dict(sorted(paths.items())), "by_class_path": by_class_path, "grains": [grains[k] for k in sorted(grains)],
            "reason_windows_any": dict(sorted(reason_any.items())), "slice_counts": counts, "anomalies": anomalies, "policy_effect": policy_effect,
            "near_station_tie": tie, "near_station_tie_unavailable": tie_why}


# ── the builder's numerical-window gate (read back after the build) ─────────────────────────────────────────────

GATE_DEFAULT_ENTRY = "services.gochara_kernel.numerical_window_gate:generation_verdict"


def discover_gate(sidecar: Path, explicit: str | None) -> tuple:
    """The numerical-window gate (the verification job's re-derivation of strength / peak / valence for EVERY window): `module:function` given explicitly
    (`--gate-entry`), else `numerical_window_gate.generation_verdict` when the checkout has it, else the unique public callable whose name says
    numerical + window + (gate|verify|re-derive) in the verification job or the gochara kernel.  Returns (entry or None, reason)."""
    if explicit:
        return explicit, "explicit --gate-entry"
    mod, fn = GATE_DEFAULT_ENTRY.split(":")
    p = sidecar / (mod.replace(".", "/") + ".py")
    if p.is_file() and re.search(rf"^def {fn}\(", p.read_text(encoding="utf-8"), re.M):
        return GATE_DEFAULT_ENTRY, "the gate module's own generation_verdict"
    hits = []
    pat = re.compile(r"^def ((?=\w*numer)(?=\w*window)(?:\w*(?:gate|verif|rederiv|re_deriv)\w*))\(", re.M)
    for rel in ["pipeline/orchestrator/verification_job.py"] + sorted(str(q.relative_to(sidecar)) for q in (sidecar / "services" / "gochara_kernel").glob("*.py")):
        q = sidecar / rel
        if q.is_file():
            for m in pat.finditer(q.read_text(encoding="utf-8")):
                hits.append(f"{rel[:-3].replace('/', '.')}:{m.group(1)}")
    hits = [h for h in hits if not h.split(":")[1].startswith("_")]
    if len(hits) == 1:
        return hits[0], "discovered by name"
    return None, ("no numerical-window gate function found (pass --gate-entry module:function)" if not hits else f"ambiguous: {hits}")


def run_gate(conn, sidecar: Path, explicit: str | None) -> dict:
    import importlib
    entry, why = discover_gate(sidecar, explicit)
    if entry is None:
        return {"status": "ABSENT", "entry": None, "detail": why}
    mod_name, fn_name = entry.split(":")
    t0 = time.time()
    try:
        fn = getattr(importlib.import_module(mod_name), fn_name)
    except Exception as exc:                                                 # noqa: BLE001
        return {"status": "NOT_RUN", "entry": entry, "detail": f"import failed: {type(exc).__name__}: {scrub(exc)}"}
    try:
        try:
            result = fn(conn, chart_id=CHART, generation=GENERATION)
        except TypeError:
            result = fn(conn, CHART, GENERATION)
    except Exception as exc:                                                 # noqa: BLE001 — a raising gate is a REFUSED, with the exception class and a scrubbed message
        return {"status": "REFUSED", "entry": entry, "detail": f"{type(exc).__name__}: {scrub(exc)}", "gate_s": round(time.time() - t0, 2)}
    status, detail = "UNRECOGNISED_RESULT", f"returned {type(result).__name__}"
    vocab = {"PASSED": "PASSED", "REFUSED": "REFUSED", "FAILED": "REFUSED", "NOT_APPLICABLE": "NOT_APPLICABLE"}
    if isinstance(result, bool):
        status = "PASSED" if result else "REFUSED"
    elif isinstance(result, (list, tuple, set)):
        status, detail = ("PASSED", "0 problems") if not result else ("REFUSED", f"{len(result)} problem(s)")
    elif isinstance(result, dict):
        for key in ("status", "verdict", "result"):
            if isinstance(result.get(key), str) and result[key].upper() in vocab:
                status, detail = vocab[result[key].upper()], f"dict key {key}"
                if result.get("problems"):
                    detail += f"; {len(result['problems'])} problem(s)"
                break
        else:
            for key in ("passed", "ok"):
                if isinstance(result.get(key), bool):
                    status, detail = ("PASSED" if result[key] else "REFUSED"), f"dict key {key}"
                    break
    elif isinstance(result, str) and result.upper() in vocab:
        status, detail = vocab[result.upper()], "string result"
    return {"status": status, "entry": entry, "detail": detail, "gate_s": round(time.time() - t0, 2)}


# ── the G-4 stage: the verification job, run inline on the trial database ───────────────────────────────────────

VERIFY_UNVERIFIED_SQL = """
SELECT count(*) FROM public.ka_gochara_eval_window w WHERE w.chart_id = %s AND w.generation = %s AND w.event_class = ANY(%s)
  AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_eval_window_verification v WHERE v.chart_id = w.chart_id AND v.generation = w.generation
                  AND v.event_class = w.event_class AND v.path_id = w.path_id AND v.rule_version = w.rule_version AND v.status = 'VERIFIED')"""
VERIFY_UNVERIFIED_ROWS_SQL = """SELECT COALESCE(sum(windows_unverified), 0) FROM public.ka_gochara_eval_window_verification
                                WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s)"""
VERIFY_ATTESTED_SQL = """
SELECT COALESCE(sum((runner_identity::jsonb -> 'numerical_window_gate' ->> 'windows')::bigint), 0),
       COALESCE(sum((runner_identity::jsonb -> 'numerical_window_gate' ->> 'numbered')::bigint), 0),
       count(*) FILTER (WHERE runner_identity::jsonb -> 'numerical_window_gate' IS NULL)
FROM public.ka_gochara_eval_window_verification WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s)"""
LIVE_COUNT_SQL = """SELECT count(*), count(*) FILTER (WHERE peak_instant IS NOT NULL) FROM public.ka_gochara_eval_window
                    WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s)"""
# R-6: the verifier's demoted windows, as the attestation names them (numerical_window_gate.demotions: sorted {window_id, reason}), and which of those ids the live table
# holds as numbered windows (a peak is stored) - G-4 matches the attested numbered count against the live one by these ids (gates.recount_agrees)
VERIFY_DEMOTED_SQL = """
SELECT d.e ->> 'window_id', d.e ->> 'reason'
FROM public.ka_gochara_eval_window_verification v,
     LATERAL jsonb_array_elements(COALESCE(v.runner_identity::jsonb -> 'numerical_window_gate' -> 'demoted_windows', '[]'::jsonb)) AS d(e)
WHERE v.chart_id = %s AND v.generation = %s AND v.event_class = ANY(%s)
ORDER BY 1, 2"""
LIVE_NUMBERED_AMONG_SQL = """SELECT window_id::text FROM public.ka_gochara_eval_window
                             WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s) AND peak_instant IS NOT NULL AND window_id::text = ANY(%s) ORDER BY 1"""


def collect_attestation_recount(conn, chart, generation, classes) -> dict:
    """The G-4 recount: the attested counts (summed over the grains' persisted attestations) with the attested demoted windows, against the live table's counts with
    the subset of those demoted ids that are live numbered windows."""
    args = (chart, generation, classes)
    att_w, att_n, unattested = conn.execute(VERIFY_ATTESTED_SQL, args).fetchone()
    live_w, live_n = conn.execute(LIVE_COUNT_SQL, args).fetchone()
    demoted = [{"window_id": r[0], "reason": r[1]} for r in conn.execute(VERIFY_DEMOTED_SQL, args).fetchall()]
    held = [r[0] for r in conn.execute(LIVE_NUMBERED_AMONG_SQL, (*args, [e["window_id"] for e in demoted])).fetchall()]
    return {"attested": {"windows": int(att_w), "numbered": int(att_n), "demoted_windows": demoted},
            "live": {"windows": live_w, "numbered": live_n, "numbered_among_demoted": held}, "grains_without_attestation": unattested}


def make_trial_census(vj, trial_classes):
    """The G8 class census applied to a deliberate SLICE (job census-diag, CENSUS_DIAG §3): the same shared predicate
    (`vj.class_census_violations`), but with the trial's class list as the expected universe. The manifest pin must still CONTAIN every
    trial class, and the generation must claim exactly the trial classes — a lost class or a stray class is refused by name, as in
    production. Every other precondition (pin == verifier universe included) is untouched."""
    want = sorted(trial_classes)

    def trial_census(conn, *, chart_id, generation, vector, found):
        vec = vector if isinstance(vector, dict) else json.loads(vector)
        pins = vec.get("scored_classes") if isinstance(vec, dict) else None
        if not isinstance(pins, list) or not set(want) <= set(pins):
            raise vj.VerificationRefused("class_census_mismatch", "trial classes are not inside the manifest's pinned universe")
        bad = vj.class_census_violations({"scored_classes": want}, vj._claimed_classes(conn, chart_id, generation, found))
        if bad:
            raise vj.VerificationRefused("class_census_mismatch",
                                         f"the trial claims a different set than it was asked to build: {[(c, v) for c, v, _ in bad][:5]}")
    return trial_census


def verify_stage(state: dict, out: Path, conn, deadline: float | None) -> bool:
    """Run the REAL verification job (`services.gochara_kernel.verification_job.run`, the library behind `pipeline.orchestrator.verification_job`) one class at
    a time on the trial database, persisting its 1240 rows and attestations — `enforce_identity=False` is the library's own TEST SEAM for a superuser lane
    connection (the production entry point never passes it; the throwaway lane has no separate verifier role).  Per-class seconds, and the seconds spent in
    `window_verifier.verify_window_semantics` (the solver check's cost), are measured by wrapping that function.  True when every class has been attempted."""
    from pipeline.orchestrator import verification_job as vjob
    from services.gochara_kernel import numerical_window_gate as nwg
    from services.gochara_kernel import rule_registry
    from services.gochara_kernel import verification_job as vj
    from services.gochara_kernel import window_verifier as wv

    v = state.setdefault("verification", {"classes": {}, "ran": False})
    dead = set(state.get("dead_classes", []))
    pending = [c for c in state["classes"] if c not in v["classes"] and c not in dead]
    real_sem = wv.verify_window_semantics
    spent = {"window_check_s": 0.0}

    def timed(*args, **kwargs):
        t = time.time()
        try:
            return real_sem(*args, **kwargs)
        finally:
            spent["window_check_s"] += time.time() - t
    real_census = vj._enforce_class_census
    trial_census = make_trial_census(vj, state["classes"])
    clock = make_clock(state)
    meter = make_cpu_meter(state)                                                            # G5-CPU
    for cls in pending:
        if deadline is not None and time.time() >= deadline:
            break
        spent["window_check_s"] = 0.0
        t0 = time.time()
        wv.verify_window_semantics = timed
        vj._enforce_class_census = trial_census                          # CENSUS_DIAG §3: the slice is judged against the TRIAL universe
        try:
            with clock.measure(f"verify:{cls}"), meter.measure(f"verify:{cls}"), rule_registry.rule_profile(final_rules=True):
                rep = vj.run(conn, chart_id=CHART, generation=GENERATION, classes=[cls], enforce_identity=False, report_only=False,
                             **vjob._build_kwargs(conn, EPHE))
            entry = rep["classes"].get(cls) or {}
            v["classes"][cls] = {"status": entry.get("status", "MISSING"), "detail": scrub(entry.get("detail") or entry.get("reason") or "", 200), "seconds": round(time.time() - t0, 2),
                                 "window_check_s": round(spent["window_check_s"], 2), "run_status": rep.get("status"), "gate_violations": len(rep.get("gate") or [])}
            v["ran"] = True
        except vj.VerificationRefused as exc:
            v["not_run_reason"] = f"VerificationRefused {exc.code}: {scrub(exc.detail, 240)}"
            v["classes"][cls] = {"status": "REFUSED", "detail": v["not_run_reason"], "seconds": round(time.time() - t0, 2), "window_check_s": None}
            print(f"verify {cls}: REFUSED {exc.code}", flush=True)
            break
        except Exception as exc:                                             # noqa: BLE001 — recorded by class and type, never swallowed
            v["classes"][cls] = {"status": "ERROR", "detail": f"{type(exc).__name__}: {scrub(exc, 240)}", "seconds": round(time.time() - t0, 2), "window_check_s": None}
            v["ran"] = True
        finally:
            wv.verify_window_semantics = real_sem
            vj._enforce_class_census = real_census
        print(f"{v['classes'][cls]['seconds']:9.2f}s  verify {cls}: {v['classes'][cls]['status']}", flush=True)
        state["effective_wall"] = clock.record()
        state["g5_cpu"] = meter.record()                                                      # G5-CPU
        write_json(out / "state.json", state)
    state["effective_wall"] = clock.record()
    state["g5_cpu"] = meter.record()                                                          # G5-CPU
    meter.close()                                                                             # G5-CPU
    clock.close()                                                            # the lock probe's admin connection (N4); every exception of the loop is caught above
    finished = all(c in v["classes"] for c in state["classes"] if c not in dead) or bool(v.get("not_run_reason"))
    if finished and not v.get("final"):
        v["final"] = True
        if v.get("not_run_reason"):
            v["ran"] = False
        else:
            args = (CHART, GENERATION, state["classes"])
            v["source"] = "harness_inline: services.gochara_kernel.verification_job.run(enforce_identity=False), per class"
            v["generation_verdict"] = nwg.generation_verdict(conn, CHART, GENERATION, classes=state["classes"])        # D-9: the verdict of THIS trial's classes, not of the 26-class universe
            v["generation_verdict_scope"] = {"classes": sorted(state["classes"]), "scoped": True,
                                             "not_part_of_this_reading": "the aggregate-only checks of numerical_window_gate.generation_verdict (pinned-universe coverage, shard stamps, G-6 evidence, wall "
                                                                         "rule; DEFECT_MAP D-9) — a subset verdict does not carry them; the R8/R8X fixtures and the seal verification job cover them"}
            v["attestation_recount"] = collect_attestation_recount(conn, *args)
            v["unverified_windows"] = conn.execute(VERIFY_UNVERIFIED_SQL, args).fetchone()[0] + int(conn.execute(VERIFY_UNVERIFIED_ROWS_SQL, args).fetchone()[0])
            gv = v["generation_verdict"]
            v["generation_verdict"] = {k: gv.get(k) for k in ("status", "policy", "grains", "windows", "numbered_windows", "blank_windows", "judgment_flags", "problems", "by_path",
                                                              "honest_nulls", "valence_of_numbered")}
            v["generation_verdict"]["problems"] = [scrub(p, 240) for p in (gv.get("problems") or [])][:20]
        write_json(out / "state.json", state)
    return finished


# ── the A10.1 record stages: digests, noninterference snapshot, TRIAL_READY/1, EQUIVALENCE_RECORD/1 ────────────────────────────────────────────

def load_decision_table(path: str | None) -> dict:
    """The G-3 decision table (data), validated.  An unreadable or invalid table REFUSES the run: a gate without its table would be a silent default."""
    p = Path(path) if path else DECISION_TABLE
    try:
        return gates.load_decision_table(json.loads(p.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:                       # DecisionTableError is a ValueError
        raise Refused(f"the G-3 decision table {p} is not usable: {scrub(exc, 240)}")


def capture_a10(state: dict, out: Path, conn, sidecar_mods: dict) -> None:
    """Read the stored manifest vector (→ digests record, written to <out>/input_vector.json for the equivalence tool) and the four natural-key sets.  Each failure is
    recorded by type and leaves the item null, so the evaluator reads NOT_EVALUATED (never equal)."""
    vec = None
    try:
        vec = sidecar_mods["result_policy"].manifest_vector(conn, CHART, GENERATION)
    except Exception as exc:                                                         # noqa: BLE001
        state["a10_errors"] = {**state.get("a10_errors", {}), "manifest_vector": type(exc).__name__}
    state["digests_record"] = te.digests_record(vec)
    if vec is not None:
        write_json(out / "input_vector.json", vec)
    geometry = te.geometry_config(vec, state.get("horizon"), state["classes"])
    try:
        state["noninterference"] = te.capture_noninterference(conn, CHART, GENERATION, state["classes"], geometry)
    except Exception as exc:                                                         # noqa: BLE001
        state["noninterference"] = None
        state["a10_errors"] = {**state.get("a10_errors", {}), "noninterference": f"{type(exc).__name__}: {scrub(exc, 160)}"}
    write_json(out / "state.json", state)


def trial_ready_stage(state: dict, out: Path, repo: str | None, ready_json: str | None, timeout_s: int) -> dict:
    """TRIAL_READY/1 for THIS trial's head: a supplied evaluation (--trial-ready-json), or the merged evaluator run on a clean work tree at the head."""
    head = state["code"]["head"]
    if ready_json:
        try:
            doc = json.loads(Path(ready_json).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            doc = {"predicate": gates.TRIAL_READY_PREDICATE, "head_sha": head, "checks": [], "ready": False, "not_run_reason": f"{ready_json} is not readable JSON"}
        doc["supplied_from"] = str(ready_json)
        doc["supplied_sha256"] = sha_file(Path(ready_json)) if Path(ready_json).is_file() else None
        return doc
    return te.run_trial_ready(Path(repo) if repo else None, head, out / "trial_ready.json", python=sys.executable, timeout_s=timeout_s)


def equivalence_stage(state: dict, out: Path, eq_repo: str | None, eq_tool: str | None, extra_path: str | None, image_digest: str | None, extra_inline: dict | None = None) -> dict:
    """EQUIVALENCE_RECORD/1 for the trial head by the merged tool.  The pinned inputs are what the trial can read (the stored vector, its own horizon, the runtime it ran
    on as a ROLLING DIAGNOSTIC) plus an operator-supplied file for what only the dispatch config / L0 / L1 can say."""
    vec = None
    try:
        vec = json.loads((out / "input_vector.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    extra = json.loads(Path(extra_path).read_text(encoding="utf-8")) if extra_path else None
    if extra_inline:                                      # AMD64-DOCKER: the runtime block read inside the container and the emulation note win over a file's runtime/provenance keys
        extra = {**(extra or {}), **{k: {**((extra or {}).get(k) or {}), **v} for k, v in extra_inline.items()}}
    g5 = g5_cpu.equivalence_fields(state)                                                     # G5-CPU: the method inputs ride the runtime block
    extra = {**(extra or {}), "runtime": {**((extra or {}).get("runtime") or {}), **g5}}
    pinned = None if vec is None else te.pinned_inputs(vec, trial_horizon=(state.get("horizon") or {}).get("days") and [state["horizon"]["start"], state["horizon"]["end"]],
                                                       provenance={"branch": state["code"].get("branch") or "", "image_digest": image_digest or ""}, extra=extra)
    rec = te.emit_equivalence_record(Path(eq_repo) if eq_repo else None, state["code"]["head"], pinned, out / "equivalence", python=sys.executable,
                                     tool=Path(eq_tool) if eq_tool else None)
    return {**rec, **g5}                                                                      # G5-CPU


def attach_to_report(out: Path, key: str, value) -> list:
    """Write `key` into the run's report files (<label>_report.json and report.json) and refresh the qualification label; returns the files changed."""
    changed = []
    for name in sorted({f"{load_state(out)['label']}_report.json", "report.json"}):
        p = out / name
        if not p.is_file():
            continue
        rep = json.loads(p.read_text())
        rep[key] = value
        rep["qualification"] = te.qualification_block(rep, load_state(out).get("image_digest"))
        write_json(p, rep)
        changed.append(name)
    return changed


# ── the G-6 stage: cross-check of a sample of the numbered windows ──────────────────────────────────────────────

class _CrosscheckEnv:
    """Per-trial context for re-solving windows: the writer's own position probe, the bound factor rows, the grain's stored records (read once per grain)."""

    def __init__(self, conn, ws):
        from pipeline.orchestrator.writers import ka_gochara_v5 as w
        from services.gochara_kernel.rule_registry import RuleRegistryStore
        from services.gochara_kernel.window_store import WindowStore
        self.conn, self.ws, self.w = conn, ws, w
        self.store, self.bound_rows = WindowStore(conn), RuleRegistryStore(conn).bound_factor_rows
        self.records: dict = {}

        def position_at(body, t):
            jd = t.timestamp() / 86400.0 + w._JD_UNIX_EPOCH
            lon, retflag = w.calc_sidereal_lon(body.title(), jd, EPHE)
            if not (retflag & 2):
                raise RuntimeError(f"position probe {body}: retflag {retflag} lacks the Swiss bit")
            return lon
        self.position_at = position_at

    def _p1_operands(self, path_id: str, rows: list):
        """The writer's P1 operand sources (`_run_window_phase.p1_operands_for`): the Form B table the grain's version declares, else the writer's per-factor rules; None when
        neither is bound.  A P1 record built without them is unqualified, which this stage would report as a defect of the window."""
        if path_id != "P1":
            return None
        from services.gochara_kernel import p1_operands as p1o
        form_b = p1o.form_b_mapping(rows)
        if form_b is None and self.w.P1_VALUE_RULES is None:
            return None
        return p1o.P1Operands(p1o.load_p1_l0(self.conn.cursor()), self.position_at, rules=None if form_b is not None else self.w.P1_VALUE_RULES, form_b=form_b)

    def _vedha_for(self, key: tuple):
        """The vedha operand source bound to THIS grain, exactly as the writer binds it (`vedha_source()` of the active rule profile, then `for_grain(..., position_at=)` — the
        post-vedha-residence signature, SR-VEDHA-RESIDENCE-SOURCE).  Never the module constant `VEDHA_SOURCE` (None unless explicitly bound)."""
        source_of = getattr(self.w, "vedha_source", None)
        if source_of is None:
            raise RuntimeError("the checkout's writer has no vedha_source(): the cross-check needs the head that carries od1-vedha-residence")
        vedha = source_of()
        if hasattr(vedha, "for_grain"):
            vedha = vedha.for_grain(self.conn, chart_id=CHART, generation=GENERATION, event_class=key[0], records=list(self.records[key].values()), position_at=self.position_at)
        return vedha

    def pieces(self, win: dict) -> list:
        from services.gochara_kernel import rule_registry
        with rule_registry.rule_profile(final_rules=True):               # the profile the trial's build and verification ran under (`verify_stage`): final-profile factor rows and vedha source
            return self._pieces_under_profile(win)

    def _pieces_under_profile(self, win: dict) -> list:
        ws = self.ws
        key = (win["event_class"], win["path_id"], win["rule_version"])
        rows = self.bound_rows(key[1], key[2])
        if key not in self.records:
            self.records[key] = {r.record_id: r for r in self.store.read_grain(chart_id=CHART, generation=GENERATION, event_class=key[0], path_id=key[1],
                                                                              rule_version=key[2], position_at=self.position_at, p1=self._p1_operands(key[1], rows))}
        ids = [r[0] for r in self.conn.execute("SELECT record_id::text FROM public.ka_gochara_eval_window_record WHERE window_id = %s", (win["window_id"],)).fetchall()]
        vedha = self._vedha_for(key)
        progs = []
        for rid in ids:
            p = ws.build_program(self.records[key][rid], rows, drishti=self.w.DRISHTI_SOURCE, vedha=vedha)
            if p.has_channel_fn:                                            # draft_windows: a record whose side a factor decides per instant (P1 agent_nature, Q3(c)) has no static channel
                p.channel = None
            elif hasattr(ws, "_program_channel"):
                p.channel = ws._program_channel(key[0], p.rec, p.qualified)
            if not p.qualified:
                raise RuntimeError(f"member {rid} is unqualified although the window is numbered")
            progs.append(p)
        return cx.pieces_of(ws, progs, key[1], key[0], win["lo"], win["hi"])


NUMBERED_SQL = """SELECT window_id::text, event_class, path_id, rule_version, lower(interval), upper(interval), peak_instant, objective_value
                  FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s) AND peak_instant IS NOT NULL
                  ORDER BY window_id"""


def crosscheck_stage(state: dict, out: Path, conn, deadline: float | None, profile: dict, seed_arg: int | None) -> bool:
    """Select (once, persisted) the random 3 % sample of the numbered windows plus, per path, the windows with a mixed piece among the top-N by stored objective
    value, then re-solve them (resumable per window).  True when every selected window has a result (or the adapter cannot run: status recorded)."""
    from services.gochara_kernel import window_sweep as ws
    cfg = {**{"sample_rate": 0.03, "top_n_mixed": 5, "dense_max_days": 3.0, "dense_step_s": 1.0, "mixed_scan_limit": 60, "window_timeout_floor_s": 240}, **(profile.get("crosscheck") or {})}
    c = state.setdefault("crosscheck", {"results": {}})
    try:
        cx.check_adapter(ws)
    except cx.AdapterMismatch as exc:
        c["final"] = {"status": "ADAPTER_MISMATCH", "detail": str(exc)}
        write_json(out / "state.json", state)
        return True
    wins = {r[0]: {"window_id": r[0], "event_class": r[1], "path_id": r[2], "rule_version": r[3], "lo": r[4], "hi": r[5], "peak": r[6], "value": r[7]}
            for r in conn.execute(NUMBERED_SQL, (CHART, GENERATION, state["classes"])).fetchall()}
    env = _CrosscheckEnv(conn, ws)
    if "selection" not in c:
        seed = seed_arg if seed_arg is not None else int(hashlib.sha256(state["window_rows_digest"]["sha256"].encode()).hexdigest()[:8], 16)
        rnd = cx.random_sample(list(wins), cfg["sample_rate"], seed)
        top = []
        for path in sorted({w["path_id"] for w in wins.values()}):
            cands = sorted((w for w in wins.values() if w["path_id"] == path and w["value"] is not None), key=lambda w: (-w["value"], w["window_id"]))[:cfg["mixed_scan_limit"]]
            found = 0
            for w in cands:
                if found >= cfg["top_n_mixed"]:
                    break
                try:
                    if cx.window_is_mixed(env.pieces(w)):
                        top.append(w["window_id"]); found += 1
                except Exception:                                           # noqa: BLE001 — a window that cannot be rebuilt is checked (and reported) via the random path
                    continue
        c["selection"] = {"seed": seed, "random": rnd, "top_mixed": sorted(top), "scan_limit": cfg["mixed_scan_limit"], "numbered_windows": len(wins), "config": cfg}
        write_json(out / "state.json", state)
    sel = c["selection"]
    todo = [w for w in dict.fromkeys(sel["random"] + sel["top_mixed"]) if w not in c["results"]]
    for wid in todo:
        if deadline is not None and time.time() >= deadline:
            break
        win = wins[wid]
        t0 = time.time()
        floor = time.time() + cfg["window_timeout_floor_s"]
        win_deadline = None if deadline is None else max(deadline, floor)
        try:
            if win["value"] is None:
                res = {"violations": [{"kind": "recompute_inconsistent", "detail": "a numbered window carries no objective_value"}], "days": None}
            else:
                res = cx.check_window(ws, env.pieces(win), float(win["value"]), win["peak"], win["lo"], win["hi"], dense_max_days=cfg["dense_max_days"],
                                      step_s=cfg["dense_step_s"], deadline=win_deadline)
        except Exception as exc:                                            # noqa: BLE001 — cannot rebuild = inconsistent, named; never skipped
            res = {"violations": [{"kind": "recompute_inconsistent", "detail": f"cannot rebuild the window: {type(exc).__name__}: {scrub(exc, 160)}"}], "days": None}
        res.update({"event_class": win["event_class"], "path_id": win["path_id"], "rule_version": win["rule_version"]})
        c["results"][wid] = res
        write_json(out / "state.json", state)
        print(f"{time.time() - t0:9.2f}s  crosscheck {win['event_class']}/{win['path_id']} {wid[:8]} violations={len(res['violations'])}", flush=True)
    done = all(w in c["results"] for w in sel["random"] + sel["top_mixed"])
    if done:
        c["final"] = cx.aggregate(sel, c["results"], len(wins), cfg["sample_rate"])
        c["final"]["config"] = cfg
        write_json(out / "state.json", state)
    return done


# ── G-8: the implementation-module digests ──────────────────────────────────────────────────────────────────────

_MODULES_SCRIPT = """
import hashlib, json, os, sys
sidecar = sys.argv[1]
sys.path.insert(0, sidecar); os.chdir(sidecar)
from services.gochara_kernel import input_vector as iv
out = {}
for m in sorted({m for v in iv.IMPLEMENTATION_MODULES.values() for m in v}):
    p = os.path.join(sidecar, m.replace('.', '/') + '.py')
    out[m] = hashlib.sha256(open(p, 'rb').read()).hexdigest() if os.path.isfile(p) else 'MISSING'
print(json.dumps(out, sort_keys=True))
"""


def module_digests(checkout: Path) -> dict:
    """sha256 of every file of the checkout's `IMPLEMENTATION_MODULES` (all three stages), read in a throwaway interpreter so two checkouts never share a process."""
    sidecar = checkout / "platform" / "python-sidecar"
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "SE_EPHE_PATH": EPHE})
    r = subprocess.run([sys.executable, "-I", "-c", _MODULES_SCRIPT, str(sidecar)], capture_output=True, text=True, timeout=300, env=env)
    if r.returncode != 0:
        raise Refused(f"cannot read IMPLEMENTATION_MODULES of {checkout}: {scrub(r.stderr, 200)}")
    return json.loads(r.stdout.strip().splitlines()[-1])


# ── baseline comparison and the oracle ──────────────────────────────────────────────────────────────────────────

def compare_baseline(rep: dict, baseline_path: str | None) -> dict:
    t = rep["totals"]["windows_total"]
    cmp = {"windows_total": t, "informational_slice_counts_j5q": {k: {"j5q_dry_run": v, "now": rep["slice_counts"].get(k)} for k, v in BASELINE_INFO.items()}}
    if baseline_path:
        try:
            base = json.loads(Path(baseline_path).read_text())
            cmp["baseline_file_sha256"] = sha_file(Path(baseline_path))
            cmp["baseline_total_windows"] = base.get("totals", {}).get("windows_total")
            cmp["per_class"] = {c: {"baseline_windows": base["classes"][c]["windows_total"], "windows": v["windows_total"],
                                    "delta": None if base["classes"][c]["windows_total"] is None else v["windows_total"] - base["classes"][c]["windows_total"],
                                    "baseline_blank": base["classes"][c].get("blank"), "blank": v["blank"]}
                                for c, v in rep["classes"].items() if c in base.get("classes", {})}
            cmp["equal"] = all(x["delta"] == 0 for x in cmp["per_class"].values()) and len(cmp["per_class"]) == len(rep["classes"])
        except Exception as exc:                                            # noqa: BLE001
            cmp["baseline_file_error"] = f"{type(exc).__name__}: {scrub(exc)}"
    return cmp


def baseline_oracle(rep: dict, state: dict) -> dict:
    """The harness's own oracle: the DEFAULT policy on origin/main yields the all-null generation — every window of every trial class blank with the reason
    `all_null_candidate_policy`, valence `unqualified`, no peak, no score, `all_null_candidate/1` stored and no `maximise_earliest` call; the build ran its whole
    plan without a defect; and the four classes the previous harness measured (1,672 windows, d7552d029) reproduce their window counts.  Each line measures one
    claim and can read false."""
    t, problems = rep["totals"], []
    for c in state["classes"]:
        if rep["classes"][c]["windows_total"] == 0:
            problems.append(f"{c}: no windows stored")
    if t["blank"] != t["windows_total"]:
        problems.append(f"blank {t['blank']} != windows_total {t['windows_total']}")
    for k in ("with_peak", "with_score", "with_evidence_for", "with_severity", "with_any_number"):
        if t[k]:
            problems.append(f"{k} = {t[k]} (expected 0)")
    if set(t["valence"]) - {"unqualified"}:
        problems.append(f"valence values {sorted(t['valence'])} (expected only unqualified)")
    if set(t["blank_reasons"]) - {"all_null_candidate_policy"}:
        problems.append(f"blank reason codes {sorted(t['blank_reasons'])} (expected only all_null_candidate_policy)")
    if rep["policy_effect"]["manifest_policy"] != "all_null_candidate/1":
        problems.append(f"manifest policy {rep['policy_effect']['manifest_policy']!r}")
    if set(rep["policy_effect"]["window_qualification_policies"]) != {"all_null_candidate/1"}:
        problems.append(f"stored qualification policies {sorted(rep['policy_effect']['window_qualification_policies'])}")
    if rep["build"]["defects"] or rep["build"]["aborted"]:
        problems.append(f"{len(rep['build']['defects'])} build defect(s) / aborted={rep['build']['aborted']}")
    planned = rep["build"]["substeps_planned"]
    if not planned or rep["build"]["substeps_done"] != planned:
        problems.append(f"substeps done {rep['build']['substeps_done']} != planned {planned}")
    if rep["build"]["observed"]["maximise_earliest_calls"] != 0:
        problems.append("maximise_earliest called under the all-null policy")
    reproduced = {}
    for c, n in PRIOR_4CLASS_WINDOWS.items():
        if c in rep["classes"]:
            reproduced[c] = {"prior": n, "now": rep["classes"][c]["windows_total"]}
            if rep["classes"][c]["windows_total"] != n:
                problems.append(f"{c}: {rep['classes'][c]['windows_total']} windows != the previous harness's {n}")
    return {"name": "baseline_all_null_reproduction", "expected": {"all_blank": True, "classes": len(state["classes"]), "prior_4class_windows": PRIOR_4CLASS_WINDOWS},
            "prior_4class_reproduced": reproduced, "passed": not problems, "problems": problems}


def build_mode(state: dict) -> str:
    """The defect-handling mode the build ran in, as the report names it (HARNESS-3.3, O-2)."""
    return "collect" if state.get("collect") else "stop_at_first_defect"


def failed_steps_by_kind(state: dict) -> dict:
    """O-1: the substeps that raised, counted and timed under their OWN kind (`window`, `record`, …) — never under `empty`, never dropped from the table."""
    out: dict = {}
    for d in state["defects"]:
        if d.get("status", "failed") == "failed":
            f = out.setdefault(d.get("kind") or d["step"].split(":")[0], {"steps": 0, "secs": 0.0})
            f["steps"] += 1
            f["secs"] = round(f["secs"] + d.get("secs", 0), 2)
    return out


def _grain_class(state: dict, key: str) -> str | None:
    parts = key.split(":")
    return parts[1] if len(parts) > 1 and parts[1] in state["classes"] else None


def defects_by_class(state: dict) -> dict:
    """Every defect of the build, grouped by class — the full list in COLLECT mode, the first only (per class) in stop-at-first mode."""
    out: dict = {}
    for d in state["defects"]:
        out.setdefault(_grain_class(state, d["step"]) or "(class-less)", []).append({"step": d["step"], "defect": d["defect"], "status": d.get("status")})
    return dict(sorted(out.items()))


def untested_after_defect(state: dict) -> list:
    """Planned grains of a dead class that were never run (stop-at-first mode): the 'first defect only; later paths untested' statement, as data.  Empty in COLLECT mode."""
    ran = {s["step"] for s in state["steps"]} | {d["step"] for d in state["defects"]}
    dead = set(state.get("dead_classes", []))
    return [k for k in state.get("plan_substeps", []) if k not in ran and _grain_class(state, k) in dead]


def build_report(state: dict, out: Path, conn, sidecar: Path, gate_entry: str | None, baseline_path: str | None) -> dict:
    from services.gochara_kernel import result_policy
    t0 = time.time()
    gate = run_gate(conn, sidecar, gate_entry)
    rep = analyse(conn, state, {"result_policy": result_policy})
    steps = state["steps"]
    by_class = {c: round(sum(s["secs"] for s in steps if (s["step"].split(":") + ["", ""])[1] == c), 2) for c in state["classes"]}
    head_s = round(sum(s["secs"] for s in steps if (s["step"].split(":") + [""])[0] in HEAD_KINDS), 2)
    by_kind = {}
    for s in steps:
        k = s["step"].split(":")[0]
        by_kind[k] = round(by_kind.get(k, 0) + s["secs"], 2)
    failed_by_kind = failed_steps_by_kind(state)
    obs = state["observed"]
    search_calls = obs["maximise_earliest_calls"] + sum(obs.get("solver_calls", {}).values())
    rep["anomalies"]["peaks_without_search_calls"] = 0 if (search_calls or not rep["totals"]["with_peak"]) else rep["totals"]["with_peak"]
    rep.update({
        "schema": "ky.trial_slice_report/2", "marker": MARKER, "not_evidence": True, "label": state["label"], "generated_utc": now(),
        "code": state["code"], "config": {"requested_result_policy": state["requested_policy"], "collect": bool(state.get("collect")), "baseline_mode": bool(state.get("baseline_mode")),
                                           "policy_passed_to_build": None if state["requested_policy"] == "default" else state["requested_policy"],
                                           "classes": state["classes"], "final_rules": True, "in_build_verify_deferred": True, "chart": "canonical (482012f1-…)"},
        "horizon": state.get("horizon"),
        "lane": state["lane"],
        "build": {"substeps_planned": len(state.get("plan_substeps", [])), "substeps_done": len(steps), "defects": state["defects"],
                  "mode": build_mode(state), "defects_by_class": defects_by_class(state), "untested_after_defect": untested_after_defect(state),
                  "dead_classes": state.get("dead_classes", []), "aborted": state.get("aborted"),
                  "observed": {"certification_policies": obs["certification_policies"], "maximise_earliest_calls": obs["maximise_earliest_calls"],
                               "solver_module_present": obs.get("solver_module_present", False), "solver_calls": obs.get("solver_calls", {}),
                               "near_miss_layer": sorted(set(obs["near_miss_layer"]))}},
        "gate": gate,
        "window_rows_digest": state.get("window_rows_digest") or window_rows_digest(conn, state),
        "digests_record": state.get("digests_record"),
        "noninterference": state.get("noninterference"),
        "effective_wall": state.get("effective_wall"),
        "g5_cpu": state.get("g5_cpu"),                                                        # G5-CPU: attributed CPU per stage (SR-G5-LOAD)
        "trial_ready": state.get("trial_ready"),
        "equivalence_record": state.get("equivalence_record"),
        "decision_table": state.get("decision_table"),
        "a10_errors": state.get("a10_errors"),
    })
    if state.get("verification"):
        rep["verification"] = state["verification"]
    if state.get("crosscheck") and state["crosscheck"].get("final"):
        rep["crosscheck"] = state["crosscheck"]["final"]
    rep["baseline_comparison"] = compare_baseline(rep, baseline_path)
    rep["oracle"] = baseline_oracle(rep, state) if state["requested_policy"] in ("default", "all_null_candidate/1") else None
    report_s = round(time.time() - t0, 2)
    load = os.getloadavg()
    rep["runtime_s"] = {"setup": state["lane"]["setup_s"], "build_substeps_sum": round(sum(s["secs"] for s in steps), 2), "head_substeps": head_s, "head_kinds": HEAD_KINDS,
                        "by_class_build": by_class, "by_step_kind": dict(sorted(by_kind.items())), "failed_by_step_kind": dict(sorted(failed_by_kind.items())), "gate": gate.get("gate_s"), "report_and_gate": report_s,
                        "verification_by_class": {c: {"seconds": x.get("seconds"), "window_check_s": x.get("window_check_s")}
                                                  for c, x in (state.get("verification") or {}).get("classes", {}).items()},
                        "steps": [{"step": s["step"], "secs": s["secs"], "rows": s["rows"], "cpu_s": s.get("cpu_s")} for s in steps],
                        "load_average_at_report": [round(x, 1) for x in load],
                        "note": "local-Mac wall seconds on a shared machine; not Cloud Run seconds and not a projection of the century build (see `project`)"}
    rep["database"] = {"name": state["db"], "dropped": False}
    rep["qualification"] = te.qualification_block(rep, state.get("image_digest"))
    return rep


# ── commands ────────────────────────────────────────────────────────────────────────────────────────────────────

def drop_db(state: dict, out: Path) -> bool:
    import psycopg
    name = state.get("db")
    if not name or state.get("dropped"):
        return bool(state.get("dropped"))
    assert name.startswith(DB_PREFIX), name                                   # never drop what this harness did not create
    with psycopg.connect(ADMIN_DSN, autocommit=True, connect_timeout=5) as admin:
        comment = admin.execute("SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname = %s", (name,)).fetchone()
        if comment is None:
            state["dropped"] = True
        elif comment[0] != f"ky.job={state['job']}":
            raise Refused(f"database {name} carries comment {comment[0]!r}, not this harness's: not dropping it")
        else:
            admin.execute(f'DROP DATABASE "{name}" WITH (FORCE)')
            state["dropped"] = True
    write_json(out / "state.json", state)
    return True


def load_state(out: Path) -> dict:
    p = out / "state.json"
    if not p.is_file():
        raise Refused(f"no state.json in {out}")
    return json.loads(p.read_text())


def load_profile(path: str | None) -> dict:
    return json.loads(Path(path or (HERE / "gate_profile.plan_defaults.json")).read_text())


def per_path_table(rep: dict) -> str:
    lines = [f"  {'path':<5}{'windows':>9}{'numbered':>10}{'share':>8}   blank by reason"]
    for p, v in rep["paths"].items():
        why = ", ".join(f"{r}={n}" for r, n in v["blank_by_reason"].items()) or "-"
        share = "-" if v["numbered_share"] is None else f"{v['numbered_share']:.1%}"
        lines.append(f"  {p:<5}{v['windows']:>9}{v['numbered']:>10}{share:>8}   {why}")
    return "\n".join(lines)


def collect_requested(a) -> bool:
    """HARNESS-3.3 (O-2): COLLECT is asked for explicitly (`--collect` or TRIAL_COLLECT=1); the default is stop-at-first, the TR shape."""
    return bool(getattr(a, "collect", False)) or os.environ.get("TRIAL_COLLECT") == "1"


def baseline_mode_requested(a) -> bool:
    """SR-BASELINE-OVERLAY-SKIP: BASELINE mode is asked for explicitly (`--baseline-mode`, set only by make_baseline.sh through TRIAL_BASELINE_MODE=1), never inferred from a missing file, and
    only for the default policy under the label `baseline`: any other run (every trial policy) that asks for it is refused."""
    asked = bool(getattr(a, "baseline_mode", False)) or os.environ.get("TRIAL_BASELINE_MODE") == "1"
    if asked and (a.result_policy != "default" or a.label != "baseline"):
        raise Refused(f"baseline mode needs --result-policy default and --label baseline, not {a.result_policy!r} / {a.label!r}: a trial run never skips an overlay")
    return asked


def cmd_run(a) -> int:
    started = time.time()
    deadline = None if a.budget_s is None else started + a.budget_s
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    checkout = Path(a.checkout).resolve()
    if a.result_policy not in POLICIES:
        raise Refused(f"--result-policy must be one of {POLICIES}, not {a.result_policy!r}")
    classes = [c for c in a.classes.split(",") if c]
    collect = collect_requested(a)
    baseline_mode = baseline_mode_requested(a)
    profile = load_profile(a.profile)
    table = load_decision_table(a.decision_table)                    # A10.1: the G-3 table is checked on EVERY run; an unusable table refuses before any work
    sidecar = bind_checkout(checkout)
    state_path = out / "state.json"
    if state_path.is_file():
        state = json.loads(state_path.read_text())
        if (state["requested_policy"], state["code"]["checkout"], state["classes"]) != (a.result_policy, str(checkout), classes):
            raise Refused("state.json in --out belongs to another policy / checkout / class list: use a fresh --out")
        if bool(state.get("collect")) != collect:
            raise Refused(f"state.json in --out was started in {build_mode(state)} mode, this run asks for {'collect' if collect else 'stop_at_first_defect'}: use a fresh --out")
        if bool(state.get("baseline_mode")) != baseline_mode:
            raise Refused(f"state.json in --out was started with baseline_mode={bool(state.get('baseline_mode'))}, this run asks for {baseline_mode}: use a fresh --out")
        if (state.get("decision_table") or {}).get("sha256") != table["sha256"]:
            raise Refused("state.json in --out was started under another G-3 decision table: use a fresh --out")
        if state.get("dropped"):
            raise Refused("the database of this state was already dropped: use a fresh --out")
    else:
        head = a.code_head or git(checkout, "rev-parse", "HEAD")
        if not head or not re.fullmatch(r"[0-9a-f]{40}", head):
            raise Refused("the checkout is not a git work tree (a `git archive` export): pass --code-head <40-hex> so the report names the code it measured")
        dirty = git(checkout, "status", "--porcelain", "--untracked-files=no")
        mods = module_digests(checkout)
        state = {"schema": "ky.trial_slice_state/2", "marker": MARKER, "label": a.label, "job": job_name(out), "requested_policy": a.result_policy, "classes": classes,
                 "code": {"checkout": str(checkout), "head": head, "tracked_files_modified_vs_head": len([l for l in (dirty or "").splitlines() if l.strip()]),
                          "branch": git(checkout, "rev-parse", "--abbrev-ref", "HEAD"), "implementation_modules": mods,
                          "implementation_modules_missing": sorted(m for m, d in mods.items() if d == "MISSING")},
                 "decision_table": {"id": table["table_id"], "sha256": table["sha256"]}, "image_digest": a.image_digest,
                 "solver_module": a.solver_module, "started_utc": now(), "load_average_at_start": [round(x, 1) for x in os.getloadavg()], "steps": [], "defects": [], "db": None, "collect": collect,
                 "baseline_mode": baseline_mode}
        write_json(state_path, state)
    if state["db"] is None:
        print(f"[{now()}] setup: creating the throwaway lane database", flush=True)
        setup_lane(state, checkout, out)
        print(f"[{now()}] setup done in {state['lane']['setup_s']}s: {state['db']}", flush=True)
    print(f"[{now()}] build: mode={build_mode(state)} policy={a.result_policy} classes={len(classes)} head={state['code']['head'][:12]} budget={a.budget_s}", flush=True)
    if not build(state, out, deadline):
        print(f"RESUME: budget reached with {len(state['steps'])} substeps done; run the same command again", flush=True)
        return EX_RESUME
    import psycopg
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{state['db']}", autocommit=True, connect_timeout=5) as conn:
        if "window_rows_digest" not in state:
            state["window_rows_digest"] = window_rows_digest(conn, state)
            write_json(state_path, state)
        if a.verify and not verify_stage(state, out, conn, deadline):
            print("RESUME: verification not finished; run the same command again", flush=True)
            return EX_RESUME
        if a.crosscheck and not crosscheck_stage(state, out, conn, deadline, profile, a.crosscheck_seed):
            print("RESUME: cross-check not finished; run the same command again", flush=True)
            return EX_RESUME
        if "digests_record" not in state:
            from services.gochara_kernel import result_policy
            capture_a10(state, out, conn, {"result_policy": result_policy})
        if "trial_ready" not in state:
            with trial_ready_dsns(state) as dsn_labels:                  # TR_GAPS B4.3: the evaluator reads the lane DB and THIS trial DB, which is dropped only after this stage
                state["trial_ready"] = trial_ready_stage(state, out, a.trial_ready_repo, a.trial_ready_json, a.trial_ready_timeout_s)
            state["trial_ready_dsn_labels"] = dsn_labels
            write_json(state_path, state)
        if "equivalence_record" not in state:
            state["equivalence_record"] = equivalence_stage(state, out, a.eq_repo, a.eq_tool, a.eq_pinned_extra, a.image_digest)
            write_json(state_path, state)
        rep = build_report(state, out, conn, sidecar, a.gate_entry, a.baseline)
    if not a.keep_db:
        drop_db(state, out)
        rep["database"]["dropped"] = bool(state.get("dropped"))
    rep_path = out / f"{a.label}_report.json"
    write_json(rep_path, rep)
    write_json(out / "report.json", rep)
    write_json(state_path, state)
    t = rep["totals"]
    print(f"[{now()}] {MARKER} report: {rep_path}\n  windows={t['windows_total']} peak={t['with_peak']} score={t['with_score']} blank={t['blank']} valence={t['valence']}\n"
          f"  mode={rep['build']['mode']} gate={rep['gate']['status']} defects={len(rep['build']['defects'])} oracle={None if rep['oracle'] is None else rep['oracle']['passed']} db_dropped={rep['database']['dropped']}\n"
          + per_path_table(rep))
    if a.baseline and a.result_policy == "window_qualification/1":
        verdict = gates.evaluate(rep, json.loads(Path(a.baseline).read_text()), profile,
                                 dispatch_modules=json.loads(Path(a.dispatch_modules).read_text()) if a.dispatch_modules else None,
                                 decision_table=table, dispatch_digests=json.loads(Path(a.dispatch_digests).read_text()) if a.dispatch_digests else None)
        write_json(out / "gate_verdict.json", verdict)
        print(f"  gates: {verdict['overall']} failed={verdict['failed']} not_evaluated={verdict['not_evaluated']} reported={verdict['reported']}")
    print(f"  qualification: {rep['qualification']['label']} (qualifying={rep['qualification']['qualifying']}, TRIAL_READY/1 G-0 {rep['qualification']['g0']})")
    if rep["build"]["defects"] or rep["build"]["aborted"] or (rep["oracle"] is not None and not rep["oracle"]["passed"]):
        return 1
    return 0


def cmd_report(a) -> int:
    out = Path(a.out).resolve()
    state = load_state(out)
    if state.get("dropped"):
        raise Refused("the database was dropped; the report.json written at the end of `run` is the record")
    sidecar = bind_checkout(Path(state["code"]["checkout"]))
    import psycopg
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{state['db']}", autocommit=True, connect_timeout=5) as conn:
        rep = build_report(state, out, conn, sidecar, a.gate_entry, a.baseline)
    write_json(out / f"{state['label']}_report.json", rep)
    return 0


def cmd_drop(a) -> int:
    out = Path(a.out).resolve()
    state = load_state(out)
    drop_db(state, out)
    print(f"dropped={state.get('dropped')} db={state.get('db')}")
    return 0


def write_partial_baseline(a) -> int:
    """What is KNOWN when the 12-class all-null run could not be made: the 4 ruled classes from the previous harness's measured baseline (origin/main d7552d029),
    the 8 decision-pending classes UNMEASURED (null).  G-1 reads such a baseline as NOT_EVALUATED for those classes — never as equal, never as a pass."""
    if not a.prior_4class:
        raise Refused("--from-prior-only needs --prior-4class FILE")
    prior = json.loads(Path(a.prior_4class).read_text())
    classes = {}
    for c in CLASSES:
        if c in ORIGINAL_4:
            classes[c] = {"windows_total": prior["classes"][c]["windows_total"], "blank": prior["classes"][c]["blank"], "group": "prior_4class",
                          "by_path_windows": {p: x["windows"] for p, x in sorted(prior["classes"][c]["by_path"].items())}, "source": "previous harness, origin/main d7552d029"}
        else:
            classes[c] = {"windows_total": None, "blank": None, "group": "new_8", "source": "NOT MEASURED: the 12-class all-null run on origin/main has not been made"}
    base = {"schema": "ky.trial_baseline/2", "marker": MARKER, "not_evidence": True, "status": "PARTIAL_PRIOR_ONLY", "policy": "all_null_candidate/1", "generated_utc": now(),
            "classes": classes, "totals": {"windows_total": None, "prior_4class_windows": sum(classes[c]["windows_total"] for c in ORIGINAL_4), "new_8_windows": None},
            "oracle": None, "prior_4class_baseline": {"file_sha256": sha_file(Path(a.prior_4class)), "windows": prior["totals"]["windows_total"]},
            "note": a.note or "partial baseline: see status"}
    write_json(Path(a.out), base)
    print(f"PARTIAL baseline written: {a.out}  (8 classes unmeasured)")
    return 0


def cmd_baseline(a) -> int:
    """The 12-class all-null baseline from a PASSED default-policy (or all-null) run: counts only.  Refuses a report whose oracle did not pass, or that did not run the
    12 classes — a baseline is never written from a run that cannot vouch for itself."""
    if a.from_prior_only:
        return write_partial_baseline(a)
    if not a.report:
        raise Refused("--report is required (or --from-prior-only --prior-4class FILE for the honest partial baseline)")
    rep = json.loads(Path(a.report).read_text())
    if not rep.get("oracle") or not rep["oracle"].get("passed"):
        raise Refused("the report's baseline oracle did not pass (or the run was not a default/all-null one): no baseline written")
    if sorted(rep["config"]["classes"]) != sorted(CLASSES):
        raise Refused(f"the report ran {len(rep['config']['classes'])} classes, not the 12 required")
    prior = None
    if a.prior_4class:
        prior = json.loads(Path(a.prior_4class).read_text())
    classes = {}
    for c in CLASSES:
        v = rep["classes"][c]
        classes[c] = {"windows_total": v["windows_total"], "blank": v["blank"], "group": "prior_4class" if c in ORIGINAL_4 else "new_8",
                      "by_path_windows": {p: x["windows"] for p, x in sorted(v["by_path"].items())}, "valence": v["valence"], "blank_reasons": v["blank_reasons"]}
        if prior is not None and c in ORIGINAL_4:
            classes[c]["prior_harness_windows_total"] = prior["classes"][c]["windows_total"]
    base = {"schema": "ky.trial_baseline/2", "marker": MARKER, "not_evidence": True, "policy": "all_null_candidate/1", "generated_utc": now(),
            "code": {k: rep["code"].get(k) for k in ("head", "branch", "checkout", "tracked_files_modified_vs_head")},
            "classes": classes,
            "totals": {"windows_total": rep["totals"]["windows_total"], "blank": rep["totals"]["blank"],
                       "prior_4class_windows": sum(classes[c]["windows_total"] for c in ORIGINAL_4), "new_8_windows": sum(classes[c]["windows_total"] for c in NEW_8)},
            "paths": {p: v["windows"] for p, v in rep["paths"].items()},
            "oracle": rep["oracle"], "source_report_sha256": sha_file(Path(a.report)),
            "baseline_mode": bool(rep["config"].get("baseline_mode")), "overlay_skipped": (rep.get("lane") or {}).get("overlay_skipped"),          # SR-BASELINE-OVERLAY-SKIP: each skipped overlay, by name, with its reason
            "prior_4class_baseline": None if prior is None else {"file_sha256": sha_file(Path(a.prior_4class)), "windows": prior["totals"]["windows_total"]},
            "runtime_s": {"by_step_kind": rep["runtime_s"]["by_step_kind"], "build_substeps_sum": rep["runtime_s"]["build_substeps_sum"],
                          "load_average_at_report": rep["runtime_s"]["load_average_at_report"]},
            "window_rows_sha256": rep["window_rows_digest"]["sha256"],
            "noninterference": rep.get("noninterference")}          # A10.1 N3: the natural-key snapshot G-7 compares a trial against (null = made before A10.1: G-7 reads NOT_EVALUATED)
    write_json(Path(a.out), base)
    print(f"baseline written: {a.out}  windows={base['totals']['windows_total']} (prior 4 classes {base['totals']['prior_4class_windows']}, new 8 {base['totals']['new_8_windows']})"
          f"  noninterference snapshot={'yes' if base['noninterference'] else 'NO (G-7 will read NOT_EVALUATED)'}")
    return 0


def cmd_evaluate(a) -> int:
    rep = json.loads(Path(a.report).read_text())
    base = json.loads(Path(a.baseline).read_text())
    profile = load_profile(a.profile)
    second = json.loads(Path(a.second_report).read_text()) if a.second_report else None
    if a.dispatch_checkout:
        dispatch = module_digests(Path(a.dispatch_checkout).resolve())
    else:
        dispatch = json.loads(Path(a.dispatch_modules).read_text()) if a.dispatch_modules else None
    verification = gates.verification_from_job_report(json.loads(Path(a.verification_report).read_text())) if a.verification_report else None
    table = load_decision_table(a.decision_table)
    digests = json.loads(Path(a.dispatch_digests).read_text()) if a.dispatch_digests else None
    verdict = gates.evaluate(rep, base, profile, second_report=second, dispatch_modules=dispatch, verification=verification, decision_table=table, dispatch_digests=digests)
    verdict["inputs"] = {"report_sha256": sha_file(Path(a.report)), "baseline_sha256": sha_file(Path(a.baseline)), "profile_sha256": sha_file(Path(a.profile or HERE / "gate_profile.plan_defaults.json")),
                         "decision_table_sha256": table["sha256"]}
    if a.out:
        write_json(Path(a.out), verdict)
    for gid in ("G-0",) + gates.GATE_IDS:
        g = verdict["gates"][gid]
        print(f"{gid} {g['name']:<26}{g['status']}")
    print(f"overall: {verdict['overall']}  dispatchable={verdict['dispatchable']}  failed={verdict['failed']}  not_evaluated={verdict['not_evaluated']}  reported={verdict['reported']}")
    return 0 if verdict["dispatchable"] else 3


def cmd_trial_ready(a) -> int:
    """Evaluate TRIAL_READY/1 for the head of the run in --out with the merged evaluator, write <out>/trial_ready.json and attach it to the report."""
    out = Path(a.out).resolve()
    state = load_state(out)
    head = a.ref or state["code"]["head"]
    if head != state["code"]["head"]:
        raise Refused(f"--ref {head[:12]} is not the head this run measured ({state['code']['head'][:12]}): TRIAL_READY/1 must be evaluated at the trial's own head")
    doc = te.run_trial_ready(Path(a.repo), head, out / "trial_ready.json", python=sys.executable, timeout_s=a.timeout_s)
    write_json(out / "trial_ready.json", doc)
    state["trial_ready"] = doc
    write_json(out / "state.json", state)
    print(f"trial_ready: head={head[:12]} ready={doc.get('ready')} true={sum(1 for c in doc.get('checks', []) if c.get('value') is True)}/{len(doc.get('checks', []))}"
          + (f" NOT RUN: {doc['not_run_reason']}" if doc.get("not_run_reason") else "") + f" attached to {attach_to_report(out, 'trial_ready', doc)}")
    return 0 if doc.get("ready") is True else 3


def cmd_eq_record(a) -> int:
    out = Path(a.out).resolve()
    state = load_state(out)
    doc = equivalence_stage(state, out, a.eq_repo, a.eq_tool, a.pinned_extra, state.get("image_digest"))
    state["equivalence_record"] = doc
    write_json(out / "state.json", state)
    print(f"eq-record: {doc['status']}" + (f" ({doc.get('reason')})" if doc.get("reason") else f" digest={doc.get('record_digest')} unreadable={doc.get('unreadable')}")
          + f" attached to {attach_to_report(out, 'equivalence_record', doc)}")
    return 0 if doc["status"] == "COMPLETE" else 3


def cmd_amd64_readiness(a) -> int:
    doc = te.amd64_readiness(a.head, a.image_digest)
    if a.out:
        write_json(Path(a.out), doc)
    print(json.dumps(doc, indent=1, sort_keys=True))
    return 0 if doc["ready"] else 3


#: what a container run needs of the head: the sidecar and migrations (the harness), and the three files the pipeline Dockerfile COPYs from 035_DISCOVERY_LAYER
EXPORT_PATHS = ("platform/python-sidecar", "platform/migrations", "035_DISCOVERY_LAYER")


def export_head(repo: Path, head: str, dest: Path) -> Path:
    """`git archive` of the head into `dest` (read-only git; reused when `<dest>.head` already names this head).  A path without a .git is taken as an export already."""
    if not (repo / ".git").exists():
        return repo
    marker = dest.with_name(dest.name + ".head")
    if dest.is_dir() and marker.is_file() and marker.read_text().strip() == head:
        return dest
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    tar = subprocess.Popen(["git", "-C", str(repo), "archive", "--format=tar", head, "--", *EXPORT_PATHS], stdout=subprocess.PIPE, env=env)
    subprocess.run(["tar", "-x", "-C", str(dest)], stdin=tar.stdout, check=True, timeout=600)
    if tar.wait() != 0:
        raise Refused(f"git archive {head[:12]} failed in {repo}")
    marker.write_text(head + "\n")
    return dest


def amd64_finish(out: Path, rec: dict, *, eq_repo: str | None, eq_tool: str | None, pinned_extra: str | None) -> dict:
    """After the container slice: build the runtime block from the IN-CONTAINER probe (refused without it), attach the `platform` block (G-5 reads wall_comparable) and the run record to the
    report, and emit EQUIVALENCE_RECORD/1 with runtime.kind qualifying_run / arch linux/amd64 / the emulation note (host side: the record tool needs a git repo holding the head)."""
    probe = ad._json(out / "runtime_probe.json")
    rb = ad.runtime_block(probe, nonce=rec["nonce"], emulation=rec["emulation"], image_digest=rec["image"]["digest"])
    state = load_state(out)
    state["image_digest"] = rec["image"]["digest"]
    attach_to_report(out, "platform", rb["platform"])
    summary = {"stages": {k: {kk: vv for kk, vv in v.items() if kk in ("status", "wall_s", "exit")} for k, v in rec["stages"].items()},
               "image": rec["image"], "pg": rec["pg"], "engine": rec["engine"], "emulation": rec["emulation"], "probe": {k: probe[k] for k in (
                   "uname_machine", "uname_sysname", "platform_machine", "sys_platform", "python", "cpu", "distributions", "dependency_lock_digest", "swiss")},
               "teardown": rec.get("teardown"), "rule": "SR-T24-AMD64-DOCKER: runtime.kind qualifying_run, arch read in the container; wall time not used for G-5 (SR-G5-LOAD)"}
    attach_to_report(out, "amd64_docker", summary)
    eq = equivalence_stage(state, out, eq_repo, eq_tool, pinned_extra, rec["image"]["digest"],
                           extra_inline={"runtime": rb["runtime"], "provenance": {"platform_notes": rb["platform_notes"]}})
    state["equivalence_record"] = eq
    state["amd64_docker"] = summary
    write_json(out / "state.json", state)
    attach_to_report(out, "equivalence_record", eq)
    e4 = Path(eq["record_file"] + ".manifests") / "E4.json" if eq.get("record_file") else None
    return {"platform": rb["platform"], "equivalence_record": {k: eq.get(k) for k in ("status", "reason", "complete", "record_digest", "unreadable", "record_file")},
            "e4_manifest": str(e4) if e4 and e4.is_file() else None}


def cmd_amd64_run(a) -> int:
    out = Path(a.out).resolve()
    try:
        repo = Path(a.export or a.repo).resolve()
        classes = ad.check_classes([c for c in (a.classes or ",".join(ad.SLICE_CLASSES)).split(",") if c])
        export = export_head(repo, a.head, out.with_name(out.name + ".export"))
        rec = ad.run(head=a.head, export=export, harness=HERE, out=out, classes=classes, ephe=Path(EPHE), l1_export=EXPORT, image_digest=a.image_digest,
                     budget_s=a.budget_s, keep_image=a.keep_image, build_timeout_s=a.build_timeout_s, slice_timeout_s=a.slice_timeout_s)
        fin = None
        if rec["status"] in ("complete", "failed") and (out / "runtime_probe.json").is_file() and rec.get("emulation") and rec.get("image") and rec.get("pg"):
            fin = amd64_finish(out, rec, eq_repo=a.eq_repo, eq_tool=a.eq_tool, pinned_extra=a.pinned_extra)
    except (ad.Amd64Refused, Refused) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    wall = {k: v.get("wall_s") for k, v in rec["stages"].items()}
    print(json.dumps({"status": rec["status"], "run_id": rec["run_id"], "head": a.head, "classes": rec["classes"], "wall_s": wall, "teardown": rec.get("teardown"), "finish": fin},
                     indent=1, sort_keys=True))
    return {"complete": 0, "resume": EX_RESUME}.get(rec["status"], 1)


def cmd_amd64_finish(a) -> int:
    """Finish an `amd64-run` whose driver was killed (a foreground session limit) after the slice container ran to its end: read the run record, refuse while the container still runs, take the emulation
    from the engine record and the probe, attach `platform` / the run record / EQUIVALENCE_RECORD like a driver that survived, and tear the sibling PG and the network down.  The container's exit code
    was not observed by the killed driver: it is recorded as null (the report's own build/defect fields say how the slice went)."""
    out = Path(a.out).resolve()
    rec = ad._json(out / "amd64_run.json")
    try:
        if not rec:
            raise Refused(f"no amd64_run.json in {out}")
        docker = ad.Docker()
        if rec["names"]["slice"] in docker("ps", "--format", "{{.Names}}", check=False).stdout.split():
            raise Refused("the slice container is still running: wait for it (or run amd64-run again to resume)")
        label = load_state(out)["label"]
        if not (out / f"{label}_report.json").is_file() or not (out / "runtime_probe.json").is_file():
            raise Refused("no report or no runtime probe in the out directory: the slice did not finish (run amd64-run again to resume)")
        probe = ad._json(out / "runtime_probe.json")
        rec["emulation"] = ad.detect_emulation(rec["engine"], (probe or {}).get("cpu"))
        rec["stages"]["slice"] = {**rec["stages"].get("slice", {}), "status": "done_unobserved", "exit": None,
                                  "note": "the driver was killed while the container ran; its exit code was not observed"}
        rec["status"] = "complete"
        rec["teardown"] = ad.teardown(docker, rec["run_id"])
        if not a.keep_image and rec.get("image", {}).get("built"):
            rec["teardown"]["image_removed"] = docker("rmi", rec["image"]["tag"], check=False).returncode == 0
        (out / "amd64_run.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
        fin = amd64_finish(out, rec, eq_repo=a.eq_repo, eq_tool=a.eq_tool, pinned_extra=a.pinned_extra)
    except (ad.Amd64Refused, Refused) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": rec["status"], "run_id": rec["run_id"], "teardown": rec["teardown"], "finish": fin}, indent=1, sort_keys=True))
    return 0


def cmd_check_table(a) -> int:
    table = load_decision_table(a.decision_table)
    print(f"G-3 decision table OK: {table['table_id']} sha256={table['sha256']} rows={[r['id'] for r in table['rows']]} caps={[c['id'] for c in table['caps']]} "
          f"allowed={len(table['allowed_reasons'])} forbidden={len(table['forbidden_reasons'])}")
    return 0


def cmd_project(a) -> int:
    rep = json.loads(Path(a.report).read_text())
    print(json.dumps(gates.runtime_projection(rep, load_profile(a.profile)), indent=1, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--checkout", required=True)
    r.add_argument("--result-policy", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--label", default="trial")
    r.add_argument("--budget-s", type=float, default=None)
    r.add_argument("--keep-db", action="store_true")
    r.add_argument("--collect", action="store_true", help="COLLECT mode (diagnostic / PRETR runs; env TRIAL_COLLECT=1): a class's first defect does not stop it — every remaining grain is evaluated and the class "
                                                         "is failed at the END with the full defect list.  Default (TR): stop at the class's first defect")
    r.add_argument("--baseline-mode", action="store_true", help="BASELINE mode (env TRIAL_BASELINE_MODE=1, set by make_baseline.sh; default policy + label baseline only): a mandatory overlay migration the checkout "
                                                                "lacks is skipped BY NAME when the checkout also lacks the code that requires it (SR-BASELINE-OVERLAY-SKIP); a trial run always refuses")
    r.add_argument("--baseline", default=None, help="baseline_12.json: windows per class compared in the report; with a numerical policy the gates are evaluated too")
    r.add_argument("--gate-entry", default=None, help="module:function of the numerical-window gate (default: numerical_window_gate.generation_verdict when present)")
    r.add_argument("--code-head", default=None)
    r.add_argument("--classes", default=",".join(CLASSES))
    r.add_argument("--profile", default=None, help="gate profile JSON (default: gate_profile.plan_defaults.json — PLACEHOLDER doctrine values)")
    r.add_argument("--verify", action="store_true", help="run the verification job inline after the build (G-4, G-5 verifier half)")
    r.add_argument("--crosscheck", action="store_true", help="run the G-6 cross-check after the build")
    r.add_argument("--crosscheck-seed", type=int, default=None)
    r.add_argument("--solver-module", default=SOLVER_MODULE, help="dotted module whose public functions are counted as solver calls (the peaks-need-a-search anomaly detector)")
    r.add_argument("--dispatch-modules", default=None, help="JSON {module: sha256} of the dispatch head (G-8)")
    r.add_argument("--dispatch-digests", default=None, help="JSON digests record of the dispatch head (G-8: registry/L0/ephemeris/convention/orb/rulings/config)")
    r.add_argument("--decision-table", default=None, help="the G-3 decision table (default: g3_decision_table.json next to this script)")
    r.add_argument("--trial-ready-repo", default=None, help="a clean work tree checked out at the trial head: the merged TRIAL_READY/1 evaluator is run on it")
    r.add_argument("--trial-ready-json", default=None, help="an already-evaluated trial_ready.json for this head (instead of running the evaluator)")
    r.add_argument("--trial-ready-timeout-s", type=int, default=3600)
    r.add_argument("--eq-repo", default=None, help="a git repository containing the trial head: EQUIVALENCE_RECORD/1 is emitted for it by the merged tool")
    r.add_argument("--eq-tool", default=None, help="equivalence_record.py (default: <eq-repo>/00_ARCHITECTURE/briefs/kalayantra/fleet/equivalence_record.py)")
    r.add_argument("--eq-pinned-extra", default=None, help="JSON with the pinned inputs only the dispatch config / L0 / L1 can say (rules, inputs, century_config, runtime)")
    r.add_argument("--image-digest", default=None, help="the image digest the run executed in, if any (provenance; a local run has none)")
    p = sub.add_parser("report")
    p.add_argument("--out", required=True)
    p.add_argument("--baseline", default=None)
    p.add_argument("--gate-entry", default=None)
    d = sub.add_parser("drop")
    d.add_argument("--out", required=True)
    b = sub.add_parser("baseline")
    b.add_argument("--report", default=None)
    b.add_argument("--out", required=True)
    b.add_argument("--prior-4class", default=None)
    b.add_argument("--from-prior-only", action="store_true", help="write the honest PARTIAL baseline (4 prior classes measured, 8 null) when the 12-class run could not be made")
    b.add_argument("--note", default=None)
    e = sub.add_parser("evaluate")
    e.add_argument("--report", required=True)
    e.add_argument("--baseline", required=True)
    e.add_argument("--profile", default=None)
    e.add_argument("--second-report", default=None)
    e.add_argument("--dispatch-checkout", default=None)
    e.add_argument("--dispatch-modules", default=None)
    e.add_argument("--verification-report", default=None, help="the verification job's own JSON report (G-4/G-5 from the real job instead of the inline stage)")
    e.add_argument("--dispatch-digests", default=None)
    e.add_argument("--decision-table", default=None)
    e.add_argument("--out", default=None)
    t = sub.add_parser("trial-ready")
    t.add_argument("--out", required=True)
    t.add_argument("--repo", required=True)
    t.add_argument("--ref", default=None)
    t.add_argument("--timeout-s", type=int, default=3600)
    q = sub.add_parser("eq-record")
    q.add_argument("--out", required=True)
    q.add_argument("--eq-repo", required=True)
    q.add_argument("--eq-tool", default=None)
    q.add_argument("--pinned-extra", default=None)
    m = sub.add_parser("amd64-readiness")
    m.add_argument("--head", default=None)
    m.add_argument("--image-digest", default=None)
    m.add_argument("--out", default=None)
    r = sub.add_parser("amd64-run")
    r.add_argument("--head", required=True, help="the TR head (40 hex) the slice is bound to")
    r.add_argument("--repo", default=None, help="a git repo/work tree holding the head (exported with git archive) — or a tree that is already an export")
    r.add_argument("--export", default=None, help="an export of the head (no git needed)")
    r.add_argument("--out", required=True)
    r.add_argument("--classes", default=None, help="a subset of the 4-class slice (default: all four)")
    r.add_argument("--image-digest", default=None, help="use this already-present image BY DIGEST instead of building from the head's Dockerfile")
    r.add_argument("--budget-s", type=int, default=None)
    r.add_argument("--keep-image", action="store_true")
    r.add_argument("--build-timeout-s", type=int, default=3600, help="the hard limit of the docker build in this invocation (a cold build is ~12 min; a timeout leaves the run resumable)")
    r.add_argument("--slice-timeout-s", type=int, default=7200, help="the hard limit of the slice container in this invocation (a timeout kills the container; its finished substeps are kept)")
    r.add_argument("--eq-repo", default=None)
    r.add_argument("--eq-tool", default=None)
    r.add_argument("--pinned-extra", default=None)
    f = sub.add_parser("amd64-finish")
    f.add_argument("--out", required=True)
    f.add_argument("--keep-image", action="store_true")
    f.add_argument("--eq-repo", default=None)
    f.add_argument("--eq-tool", default=None)
    f.add_argument("--pinned-extra", default=None)
    c = sub.add_parser("check-table")
    c.add_argument("--decision-table", default=None)
    j = sub.add_parser("project")
    j.add_argument("--report", required=True)
    j.add_argument("--profile", default=None)
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return {"run": cmd_run, "report": cmd_report, "drop": cmd_drop, "baseline": cmd_baseline, "evaluate": cmd_evaluate, "project": cmd_project,
            "trial-ready": cmd_trial_ready, "eq-record": cmd_eq_record, "amd64-readiness": cmd_amd64_readiness, "amd64-run": cmd_amd64_run, "amd64-finish": cmd_amd64_finish, "check-table": cmd_check_table}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())

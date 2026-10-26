"""TR-26 completion probe (SR-J4E-HORIZON-BASIS, SR-J4E-POSTRUN-READBACKS): the two century G-completion checks that TR #2 never exercised, read by the gate's OWN predicates.

TR #2 drove the writer's substeps through `j4d_slice_qualify.build_slice` (build_id 'trial-slice': no build_runs row, no staged century config, no `run_asset`), so neither of these could ever read
anything; the century's first completion gate then read FALSE on `horizon_basis` and NULL on `digests_equal_dry_run`.  This module closes both, on the local disposable cluster only:

  (a) horizon_basis — a CENTURY-SHAPED run (unmarked, build_runs.plan_manifest carries the staged `gochara_v5_century_config`, the horizon is the checkout's ruled horizon) is driven through the
      writer's real plan up to and including the manifest substep; the candidate manifest's `input_generation_vector->'horizon_basis'` is then read with the pack's own query
      (`w5-j4e-horizon-basis.sql`) and judged by the pack's own test (`completion_gate.horizon_basis`, `teardown_gate.horizon_basis_if_manifest`): candidate status, ruled horizon, a non-null pin.
  (b) provenance — a TR-26-shaped build (all 26 scored classes, a short test-slice horizon) is run through the REAL build entry, `pipeline.orchestrator.asset_runner.run_asset` ->
      `_run_data_writer` (success path), on the production table definitions; `asset_provenance_receipts` must then hold the receipt: non-empty, `code_digest` == the plan manifest's
      `expected_code_digest` (computed by a SEPARATE interpreter, as the dispatch dry run does), `build_id` == the run id (`completion_gate.digests_equal_dry_run`, plus the run-id binding).

Pure predicates here (no database, no import of the checkout) are what `gates.g8_completion_checks` re-runs on the recorded raw readbacks: the probe's own words are never the verdict (§N.8).  The
driver (`run_completion_probe`) imports the checkout lazily.  Counts, digests and names only: no personal data is written (the chart row is read from the approved canonical-L1 export at run time)."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

SCHEMA = "ky.completion_probe/1"
ASSET = "ka_gochara_v5"
HEX64 = re.compile(r"[0-9a-f]{64}")
STORED_SCOPE = "stored_non_moon"
BASIS_SCHEMA = "horizon_basis/1"
CENTURY_TRIGGER = "gochara-v5-century"
#: the production tables the real build entry touches (`asset_runner.run_asset` -> `_run_data_writer` -> `provenance.capture_and_persist_receipt`), taken from the approved canonical-L1 export's schema.sql
ORCH_TABLES = ("charts", "asset_registry", "asset_throughput", "asset_freshness", "asset_provenance_receipts", "asset_output_digest_specs", "build_runs", "build_run_assets")

#: the pack's `w5-j4e-horizon-basis.sql` (PACK/century/sql), with the chart and the generation as parameters instead of the pinned literals
HORIZON_BASIS_SQL = ("SELECT jsonb_build_object('stored_scope', input_generation_vector->>'stored_scope', 'test_slice', input_generation_vector->'test_slice', "
                     "'horizon_basis', input_generation_vector->'horizon_basis', 'manifest_horizon', horizon::text, 'status', status)::text AS horizon_basis "
                     "FROM kala_gochara_publication WHERE chart_id=%s AND generation=%s")
#: the receipts part of the pack's `w5-j4e-terminal.sql`
RECEIPTS_SQL = ("SELECT jsonb_agg(to_jsonb(p) ORDER BY p.build_id)::text FROM asset_provenance_receipts p WHERE p.chart_id=%s AND p.asset_id=%s")
#: the asset / throughput part of the same query, the terminal evidence that the run really completed through the entry
TERMINAL_SQL = ("SELECT (SELECT jsonb_agg(to_jsonb(a) ORDER BY a.asset_id) FROM build_run_assets a WHERE a.run_id=%s)::text AS assets, "
                "(SELECT jsonb_agg(to_jsonb(t)) FROM asset_throughput t WHERE t.chart_id=%s AND t.asset_id=%s)::text AS throughput")


# ── the pure predicates (what the gate re-runs) ─────────────────────────────────────────────────────────────────

def _json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


def horizon_basis_check(cell, ruled_horizon) -> tuple:
    """`(state, why)` with state True | False | None.  The pack's test (`completion_gate.horizon_basis`): candidate status, the manifest horizon is the ruled one, the manifest carries a
    `horizon_basis` pin (FB-2) — plus the century-shape discriminators the probe needs so that a MARKED or measuring-scope manifest cannot satisfy a century check: `stored_scope` is the default
    scope and there is no test-slice marker, and the pin is an object of schema `horizon_basis/1`.  `ruled_horizon` = (start, end) ISO strings; None/unreadable evidence is None, never True."""
    h = _json(cell)
    if not isinstance(h, dict):
        return None, "horizon basis unreadable"
    if not (isinstance(ruled_horizon, (list, tuple)) and len(ruled_horizon) == 2 and all(isinstance(x, str) and len(x) >= 10 for x in ruled_horizon)):
        return None, "the ruled horizon is not known"
    bad = []
    if h.get("status") != "candidate":
        bad.append(f"manifest status {h.get('status')!r}")
    if h.get("stored_scope") != STORED_SCOPE or h.get("test_slice") is not None:
        bad.append(f"not a century-shaped manifest (stored_scope {h.get('stored_scope')!r}, test_slice {'present' if h.get('test_slice') is not None else 'absent'})")
    hz = h.get("manifest_horizon")
    if not isinstance(hz, str) or not all(x[:10] in hz for x in ruled_horizon):
        bad.append(f"manifest horizon {hz!r} is not the ruled {ruled_horizon[0][:10]} -> {ruled_horizon[1][:10]}")
    pin = h.get("horizon_basis")
    if not pin:
        bad.append("the manifest carries no horizon_basis pin (FB-2)")
    elif not (isinstance(pin, dict) and pin.get("schema") == BASIS_SCHEMA):
        bad.append(f"the horizon_basis pin is not a {BASIS_SCHEMA} object")
    return (False, "; ".join(bad)) if bad else (True, "candidate manifest, ruled horizon, century-shaped, horizon_basis pinned")


def provenance_check(run_id, expected_code_digest, receipts, run_completed) -> tuple:
    """`(state, why)`.  `digests_equal_dry_run`'s receipt half (`completion_gate.digests_equal_dry_run`): receipts non-empty, every `code_digest` == the plan manifest's `expected_code_digest`;
    plus the binding the pack leaves to the dry run: every receipt's `build_id` is THIS run (a stale or foreign receipt reads FALSE, the stale-receipt hazard).  A run that did not complete through
    the entry cannot be judged (None); a COMPLETED run with no receipt is FALSE — that is exactly what a bypass of the real entry looks like."""
    if run_completed is not True:
        return None, "the run did not complete through the real entry: no receipt is owed"
    if not (isinstance(expected_code_digest, str) and HEX64.fullmatch(expected_code_digest)):
        return None, "expected_code_digest is missing"
    receipts = _json(receipts)
    if receipts is None:
        return False, "the run completed through the entry but no provenance receipt exists for the asset"
    if not isinstance(receipts, list) or not all(isinstance(r, dict) for r in receipts):
        return None, "receipts unreadable"
    if not receipts:
        return False, "the run completed through the entry but no provenance receipt exists for the asset"
    bad = []
    if any(r.get("code_digest") != expected_code_digest for r in receipts):
        bad.append("a provenance receipt's code_digest differs from expected_code_digest")
    if any(str(r.get("build_id")) != str(run_id) for r in receipts):
        bad.append("a provenance receipt's build_id is not this run (stale or foreign receipt)")
    return (False, "; ".join(bad)) if bad else (True, f"{len(receipts)} receipt(s): code_digest equals expected_code_digest, build_id is this run")


def terminal_ok(terminal, asset_id: str = ASSET) -> tuple:
    """The asset/throughput half of `completion_gate.terminal_success`: build_run_assets row complete/build without error, throughput lit without error."""
    t = _json(terminal)
    if not isinstance(t, dict):
        return None, "terminal evidence unreadable"
    assets, thr = _json(t.get("assets")), _json(t.get("throughput"))
    if not (isinstance(assets, list) and len(assets) == 1 and isinstance(thr, list) and len(thr) == 1):
        return None, "terminal evidence does not carry exactly one asset and one throughput row"
    a, x = assets[0], thr[0]
    bad = []
    if a.get("asset_id") != asset_id or a.get("state") != "complete" or a.get("disposition") != "build" or a.get("error") is not None:
        bad.append(f"asset {a.get('asset_id')!r} state {a.get('state')!r} disposition {a.get('disposition')!r}")
    if x.get("state") != "lit" or x.get("last_error") is not None:
        bad.append(f"throughput state {x.get('state')!r}")
    return (False, "; ".join(bad)) if bad else (True, "asset complete/build, throughput lit, no error")


def evaluate_record(record: dict, trial_horizon) -> dict:
    """The two checks over a recorded `completion` section, from its RAW readbacks: `{"horizon_basis": (state, why), "provenance": (state, why)}`.  `trial_horizon` = the trial report's own ruled
    horizon (start, end) — the probe's recorded horizon is never trusted as the reference."""
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        return {"horizon_basis": (None, "no completion probe record"), "provenance": (None, "no completion probe record")}
    hb, pv = record.get("horizon_basis") or {}, record.get("provenance") or {}
    out = {"horizon_basis": horizon_basis_check(hb.get("readback"), trial_horizon) if hb.get("readback") is not None else (None, "the manifest was not read back")}
    done = terminal_ok(pv.get("terminal"))[0] if pv.get("terminal") is not None else None
    out["provenance"] = provenance_check(pv.get("run_id"), pv.get("expected_code_digest"), pv.get("receipts"), done) if pv else (None, "the real-entry build was not run")
    return out


# ── the production table definitions (approved canonical-L1 export's schema.sql) ─────────────────────────────────

def orchestrator_ddl(schema_text: str, tables=ORCH_TABLES) -> list:
    """CREATE TABLE plus the primary-key / unique constraints and the indexes of each table, taken verbatim from a pg_dump schema file; foreign keys and triggers are NOT taken (the other side of
    most of them is not in the lane).  A table that is not found exactly once is a refusal, never a guess."""
    stmts = []
    for t in tables:
        m = list(re.finditer(rf"^CREATE TABLE public\.{t} \(\n.*?\n\);\n", schema_text, re.M | re.S))
        if len(m) != 1:
            raise ValueError(f"schema file: CREATE TABLE public.{t} found {len(m)} times, not once")
        stmts.append(m[0].group(0))
        stmts += [x.group(0) for x in re.finditer(rf"^ALTER TABLE ONLY public\.{t}\n\s+ADD CONSTRAINT \S+ (?:PRIMARY KEY|UNIQUE) [^;]*;\n", schema_text, re.M)]
        stmts += [x.group(0) for x in re.finditer(rf"^CREATE (?:UNIQUE )?INDEX \S+ ON public\.{t} USING [^;]*;\n", schema_text, re.M)]
    return stmts


def manifest_digest(manifest) -> str:
    """The runner's own canonicalisation of a run manifest (the writer's `_manifest_digest` is pinned equal to it)."""
    return hashlib.sha256(json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def expected_code_digest(sidecar: Path, asset_id: str = ASSET, python: str | None = None, timeout_s: int = 300) -> str:
    """The dispatch dry run's `expected_code_digest`: the registered writer's source hash computed in a SEPARATE interpreter (isolated mode, the checkout's sidecar on sys.path), so it is not
    the build process's own value reused."""
    code = ("import sys; sys.path.insert(0, sys.argv[1]); from pipeline.orchestrator.writers import discover_all; from pipeline.orchestrator.writer_runtime_support import get_writer_source_hash; "
            "discover_all(); print(get_writer_source_hash(sys.argv[2]))")
    p = subprocess.run([python or sys.executable, "-I", "-c", code, str(sidecar), asset_id], capture_output=True, text=True, timeout=timeout_s, cwd=str(sidecar))
    out = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
    if p.returncode != 0 or not HEX64.fullmatch(out):
        raise RuntimeError(f"expected_code_digest: the separate interpreter did not return a digest (exit {p.returncode}): {p.stderr.strip()[-200:]}")
    return out


# ── staging (the dispatch's shapes) ─────────────────────────────────────────────────────────────────────────────

def century_config(ruled_horizon, result_policy: str = "all_null_candidate/1") -> dict:
    """The staged century config the dispatch writes into plan_manifest (`validate_century_config`'s exact field set)."""
    return {"schema": "gochara_v5_century_config/2", "final_rules": True, "defer_in_build_verify": True, "horizon": list(ruled_horizon), "result_policy": result_policy}


def slice_marker(classes, horizon_days: int, start_iso: str = "2020-01-01T00:00:00+00:00") -> dict:
    """An `all_classes_1y` test-slice marker over every scored class for `horizon_days` (<= 366) days: the cheapest legitimate TR-26-shaped build through the real entry."""
    from datetime import datetime, timedelta
    start = datetime.fromisoformat(start_iso)
    return {"schema": "gochara_v5_test_slice/1", "run": "all_classes_1y", "horizon": [start.isoformat(), (start + timedelta(days=horizon_days)).isoformat()], "classes": list(classes)}


def stage_run(conn, *, chart_id: str, triggered_by: str, manifest: dict) -> str:
    """One build_runs row exactly as a dispatch stages it (plan_manifest + its digest) and its build_run_assets row.  Returns the run id."""
    rid = str(uuid.uuid4())
    plan = {"version": "nirmana-run-manifest/v1", "chart_id": chart_id, "scope": "asset", "scope_target": ASSET, "action": "rebuild", "waves": [[ASSET]], "assets": [{"asset_id": ASSET}]}
    conn.execute("INSERT INTO public.build_runs (id, chart_id, scope, scope_target, action, state, plan, triggered_by, plan_manifest, plan_manifest_digest) "
                 "VALUES (%s, %s, 'asset', %s, 'rebuild', 'running', %s::jsonb, %s, %s::jsonb, %s)",
                 (rid, chart_id, ASSET, json.dumps(plan), triggered_by, json.dumps(manifest), manifest_digest(manifest)))
    return rid


RESUME_BINDING_KEY = "gochara_v5_century_resume"          # build_ledger.RESUME_BINDING_KEY: restated here only to NAME it in a manifest the harness stages; the writer's own constant is what judges it
RESUME_BINDING_SCHEMA = "gochara_v5_century_resume/1"
KILL_TRIGGER, RESUME_TRIGGER = "tr26-g7-century-kill", "tr26-g7-century-resume"


def ensure_build_runs(conn, schema_text: str) -> bool:
    """The production `build_runs` (CREATE TABLE + its constraints and indexes, from the approved canonical-L1 export's schema.sql) in the trial database, when the lane did not carry it; True when it was
    created.  A stub that already exists is NEVER replaced here (the lane may hold other tables' rows): it must carry the staging columns or the refusal is by name."""
    if conn.execute("SELECT to_regclass('public.build_runs') IS NOT NULL").fetchone()[0]:
        have = {r[0] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'build_runs'")}
        need = {"id", "chart_id", "scope", "scope_target", "action", "state", "plan", "triggered_by", "plan_manifest", "plan_manifest_digest"}
        if not need <= have:
            raise ValueError(f"the trial database's build_runs lacks the staging column(s) {sorted(need - have)}")
        return False
    for stmt in orchestrator_ddl(schema_text, ("build_runs",)):
        conn.execute(stmt)
    return True


def century_manifest(ruled_horizon, result_policy: str, binding: dict | None = None) -> dict:
    """The plan_manifest of a century-staged harness run: the dispatch's staged `gochara_v5_century_config` (unmarked: no test-slice marker, the ruled horizon) and — for a RESUME run only — the explicit
    `gochara_v5_century_resume` binding.  The same shape `_century_manifest` stages for the completion probe."""
    m = {"version": "nirmana-run-manifest/v1", "chart_id": None, "assets": [{"asset_id": ASSET}], "gochara_v5_century_config": century_config(ruled_horizon, result_policy)}
    if binding is not None:
        m[RESUME_BINDING_KEY] = binding
    return m


def resume_binding(entries, resumes_run_id: str) -> dict:
    """The explicit resume binding for a run that continues `resumes_run_id`, from the LEDGER the killed run left (`build_ledger.load` entries, plan order): the program identity every row carries (the first row's;
    a row that disagrees is the writer's to refuse by name — `check_resume_binding` — never the harness's to paper over) and the ordered keys the ledger holds.  Pure.  An empty ledger is a ValueError: a run that
    ledgered nothing has nothing to resume, and the writer's validation refuses an empty list."""
    entries = sorted(entries, key=lambda e: e.ordinal)
    if not entries:
        raise ValueError("the killed run left no ledger rows: there is nothing to resume")
    first = entries[0]
    return {"schema": RESUME_BINDING_SCHEMA, "resumes_run_id": str(resumes_run_id),
            "program": {"implementation_digest": first.implementation_digest, "writer_digest": first.writer_digest, "plan_digest": first.plan_digest,
                        "horizon": [h.isoformat() for h in first.horizon]},
            "ledger_substeps": [e.substep_key for e in entries]}


def stage_century_run(conn, *, chart_id: str, ruled_horizon, result_policy: str, resumes: str | None = None, entries=None) -> str:
    """One century-staged build_runs row, as the dispatch (or, for a resume, the executor's century_resume operation) stages it.  `resumes` = the id of the killed run: it is closed `failed` first (production
    allows ONE active run per chart) and the new row carries the binding built from `entries`, the ledger the harness read back."""
    manifest = century_manifest(ruled_horizon, result_policy, None if resumes is None else resume_binding(entries or [], resumes))
    manifest["chart_id"] = chart_id
    if resumes is not None:
        conn.execute("UPDATE public.build_runs SET state = 'failed', ended_at = now(), last_error = %s WHERE id = %s AND state IN ('planned', 'running', 'paused')",
                     ("tr26 harness: killed on purpose (kill+resume leg)", resumes))
    return stage_run(conn, chart_id=chart_id, triggered_by=KILL_TRIGGER if resumes is None else RESUME_TRIGGER, manifest=manifest)


def registry_row(conn, asset_id: str = ASSET, has_substeps: bool = True) -> None:
    """The asset_registry row the build entry reads (a data asset, per chart, with a writer); the NOT NULL descriptive columns carry the asset id."""
    conn.execute("INSERT INTO public.asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, scope, is_active, "
                 "has_writer, has_substeps, writer_timeout_seconds, catalog_status, asset_kind, asset_type, depends_on) "
                 "VALUES (%s, 'kala', 0, %s, %s, %s, 'postgres_table', 'kala_gochara_publication', 'per_chart', true, true, %s, 72000, 'CURRENT', 'data', 'data', ARRAY[]::text[])",
                 (asset_id, asset_id, asset_id, "completion-probe registry row", has_substeps))


# ── the driver ──────────────────────────────────────────────────────────────────────────────────────────────────

def run_completion_probe(out: Path, checkout: Path, *, slice_days: int = 30, policy: str = "all_null_candidate/1", keep_db: bool = False, code_head: str | None = None) -> dict:
    """Both checks, end to end, on the local lane cluster; writes `<out>/completion.json` (raw readbacks, counts, names) and returns it.  Needs `trial_slice.bind_checkout(checkout)` done by the caller."""
    import psycopg
    from psycopg.rows import dict_row
    import trial_slice as ts

    t0 = time.time()
    state = {"job": ts.job_name(out), "db": None, "baseline_mode": False, "code": {"checkout": str(checkout)}}
    ts.setup_lane(state, checkout, out)
    base = state["db"]
    sidecar = checkout / "platform" / "python-sidecar"
    record: dict = {"schema": SCHEMA, "marker": ts.MARKER, "code_head": code_head, "asset_id": ASSET, "chart_id": ts.CHART,
                    "entry": "pipeline.orchestrator.asset_runner.run_asset -> _run_data_writer", "lane_setup_s": state["lane"]["setup_s"]}
    created = [base]
    try:
        with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{base}", autocommit=True, connect_timeout=5) as conn:
            have = sorted(t for t in ORCH_TABLES if conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"public.{t}",)).fetchone()[0])
            for t in have:                                                            # the AM5 stub's own `charts` (it types a column char(1)): replaced by the production definition, in THIS probe database only
                conn.execute(f"DROP TABLE public.{t} CASCADE")
            for stmt in orchestrator_ddl((ts.EXPORT / "schema.sql").read_text()):
                conn.execute(stmt)
            record["lane_stub_tables_replaced"] = have
            charts = json.loads((ts.EXPORT / "charts.json").read_text())
            manifest = json.loads((ts.EXPORT / "manifest.json").read_text())
            if ts.sha_file(ts.EXPORT / "charts.json") != manifest["files"]["charts.json"]["sha256"]:
                raise ts.Refused("charts.json bytes differ from the approved canonical-L1 manifest")
            ts.load_table(conn, "charts", charts)
            registry_row(conn)
        horizon = ts.ruled_horizon()
        ruled = [horizon[0].isoformat(), horizon[1].isoformat()]
        expected = expected_code_digest(sidecar)
        record.update({"ruled_horizon": ruled, "expected_code_digest": expected})
        admin = psycopg.connect(ts.ADMIN_DSN, autocommit=True, connect_timeout=5)

        def clone(tag):
            name = ts.DB_PREFIX + uuid.uuid4().hex[:8]
            admin.execute(f'CREATE DATABASE "{name}" TEMPLATE "{base}"')
            admin.execute(f"COMMENT ON DATABASE \"{name}\" IS 'ky.job={state['job']}'")
            created.append(name)
            return name

        # (a) century-shaped: the writer's real plan to the manifest substep, under a run whose plan_manifest stages the century config
        db_a = clone("a")
        t_a = time.time()
        with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{db_a}", autocommit=True) as conn:
            record["horizon_basis"] = _century_manifest(conn, ts, ruled, policy, expected)
            cell = conn.execute(HORIZON_BASIS_SQL, (ts.CHART, ts.GENERATION)).fetchone()
            record["horizon_basis"]["readback"] = cell[0] if cell else None
        record["horizon_basis"]["wall_s"] = round(time.time() - t_a, 1)
        # (b) the real build entry
        db_b = clone("b")
        t_b = time.time()
        with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{db_b}", row_factory=dict_row) as conn:
            record["provenance"] = _real_entry_build(conn, ts, expected, slice_days)
        record["provenance"]["wall_s"] = round(time.time() - t_b, 1)
        admin.close()
    finally:
        record["total_wall_s"] = round(time.time() - t0, 1)
        if not keep_db:
            with psycopg.connect(ts.ADMIN_DSN, autocommit=True, connect_timeout=5) as admin2:
                for name in created:
                    assert name.startswith(ts.DB_PREFIX), name
                    c = admin2.execute("SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname = %s", (name,)).fetchone()
                    if c is not None and c[0] == f"ky.job={state['job']}":              # only a database this command created
                        admin2.execute(f'DROP DATABASE "{name}" WITH (FORCE)')
        ts.write_json(out / "completion.json", record)
    return record


def _century_manifest(conn, ts, ruled, policy, expected) -> dict:
    """Run the writer's real plan, in order, up to and including the manifest substep, under an unmarked century-staged run built from `{chart_id, birth_params}` only (what the orchestrator hands the writer)."""
    from pipeline.orchestrator.birth_params import fetch_birth_params
    from pipeline.orchestrator.writers import ContextSpec, ka_gochara_v5 as writer_mod

    manifest = {"version": "nirmana-run-manifest/v1", "chart_id": ts.CHART, "assets": [{"asset_id": ASSET, "expected_code_digest": expected}], writer_mod.CENTURY_CONFIG_KEY: century_config(ruled, policy)}
    rid = stage_run(conn, chart_id=ts.CHART, triggered_by=CENTURY_TRIGGER, manifest=manifest)
    ctx = ContextSpec(asset_id=ASSET, build_id=rid, db_conn=conn, dry_run=False, config={"chart_id": ts.CHART, "birth_params": fetch_birth_params(conn, ts.CHART)})
    writer = writer_mod.GocharaV5Writer()
    steps = []
    for step in writer.plan_substeps(ctx):
        with conn.transaction():
            writer.run_substep(ctx, step)
        steps.append(step.key)
        if step.key == writer_mod.MANIFEST_SUBSTEP:
            break
    else:
        raise RuntimeError("the writer's plan has no manifest substep")
    return {"run_id": rid, "shape": "unmarked run, staged century config, ruled horizon", "substeps_run": len(steps), "last_substep": steps[-1]}


def _real_entry_build(conn, ts, expected, slice_days) -> dict:
    """One all-class test-slice build through `asset_runner.run_asset` on the orchestrator's own connection (dict rows, savepoint per sub-step), then the receipts and terminal evidence."""
    from pipeline.orchestrator import asset_runner
    from pipeline.orchestrator.birth_params import fetch_birth_params  # noqa: F401  (the entry fetches it itself; imported so a missing module fails here, loudly)
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod

    marker = slice_marker(writer_mod.SCORED_CLASSES, slice_days)
    manifest = {"version": "nirmana-run-manifest/v1", "chart_id": ts.CHART, "assets": [{"asset_id": ASSET, "expected_code_digest": expected}], writer_mod.TEST_SLICE_KEY: marker}
    conn.autocommit = True
    rid = stage_run(conn, chart_id=ts.CHART, triggered_by="tr26-completion-probe", manifest=manifest)
    conn.autocommit = False
    t0 = time.time()
    cur = conn.cursor()
    asset_runner.run_asset(conn, cur, rid, ts.CHART, ASSET, 0, declared_deps=[], natural_key_partition=None, has_cowriters=False)
    conn.commit()
    secs = round(time.time() - t0, 1)
    cur.execute(RECEIPTS_SQL, (ts.CHART, ASSET))
    receipts = next(iter(cur.fetchone().values()))
    cur.execute(TERMINAL_SQL, (rid, ts.CHART, ASSET))
    row = cur.fetchone()
    a, t = row["assets"], row["throughput"]
    keep = ("asset_id", "partition_key", "receipt_state", "code_digest", "build_id")
    slim = [{k: r.get(k) for k in keep} for r in (json.loads(receipts) if receipts else [])]
    return {"run_id": rid, "entry_seconds": secs, "slice": {"run": marker["run"], "classes": len(marker["classes"]), "horizon_days": slice_days},
            "expected_code_digest": expected, "receipts": slim if slim else None, "terminal": {"assets": a, "throughput": t}}

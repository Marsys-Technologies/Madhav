"""Pravāha A2.5 — ka_gochara_v4_41_candidate heavy writer + step06 refactor.

What this file proves (steward conditions 1-6):

  (a) the writer's call path never commits/rolls back/closes ctx.db_conn and
      opens no connection — a fake conn records every lifecycle call through
      the manifest substep AND the ledger write path, plus a static source
      guard that the writer module carries no .commit(/.rollback(/connect(
      outside test-only seams;
  (b) candidate-only refusal: the real ledger guards
      (services/gochara_kernel/ledger.py's _require_not_published /
      _candidate_manifest_id / publish_candidate) raise
      PublishedGenerationRefusal against a published '4.1' manifest, and the
      writer module never calls the flip machinery (ledger.publish) nor
      touches kala_gochara_authority (the serving-side gate — platform-mcp
      register_gochara_windows.ts AUTHORITATIVE_GENERATION_FILTER serves only
      the authority row's generation);
  (c) no window outside the pinned horizon [1998-01-01, 2026-04-18]: the
      writer's row_validator refuses offending rows (fail-closed, never
      clamped);
  (d) substep idempotency: the body-scoped ledger writes issue a DELETE
      scoped to chart × '4.1' × body BEFORE any INSERT, so re-running a body
      substep replaces rather than duplicates;
  (e) defaults byte-unchanged: the step06 CLIs still own their connection
      lifecycle (connect + commit + close inside main()) while the extracted
      cores perform no commit/rollback/connect, and the ledger's default
      (bodies=None) delete scope is unchanged.
  (f) the dispatch script carries the idempotent registry insert (ON CONFLICT
      DO NOTHING, depends_on '{}', chart-scoped count_sql), the live
      no-dependents check, and the exact teardown DELETEs in its --help.

No live DB, no ephemeris: every DB touch runs against a recording fake conn.
"""
from __future__ import annotations

import inspect
import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pipeline.orchestrator.writers.ka_gochara_v4_41_candidate as writer_mod  # noqa: E402
from pipeline.orchestrator.writers import ContextSpec, SubStep, get_writer  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[3]
CUTOVER = SIDECAR / "scripts" / "kala_gochara_cutover"
PLATFORM = SIDECAR.parent
DISPATCH = PLATFORM / "scripts" / "dispatch_a25_v41_candidate_job.py"

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# ledger.py is loaded by importlib under several module instances (the writer's
# own, step06b's, step06's) — each has a DISTINCT PublishedGenerationRefusal
# class object. Match the refusal by name across all of them.
def _pub_refusal_classes():
    classes = {writer_mod.ledger.PublishedGenerationRefusal,
                   writer_mod.step06b_windows.ledger.PublishedGenerationRefusal,
                   writer_mod.step06_build._load_ledger().PublishedGenerationRefusal}
    return tuple(classes)


# ── recording fake conn ──────────────────────────────────────────────────────


class FakeCursor:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._conn.execute(sql, params)

    def executemany(self, sql, rows):
        rows = list(rows)
        self._conn.statements.append((sql, ("<many>", len(rows))))
        self._conn.rows_inserted += len(rows)

    def fetchone(self):
        return self._conn._fetchone()

    def fetchall(self):
        return self._conn._fetchall()


class FakeConn:
    """Recording conn. `manifest_status` steers the publication SELECT:
    None → no manifest row; otherwise (manifest_id, status)."""

    def __init__(self, manifest_status=None):
        self.statements: list[tuple[str, object]] = []
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0
        self.rows_inserted = 0
        self.manifest_status = manifest_status
        self._last_sql = ""

    # lifecycle — must NEVER be exercised by the writer's call path
    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closes += 1

    def cursor(self, **kwargs):
        return FakeCursor(self)

    def execute(self, sql, params=None):
        self._last_sql = sql
        self.statements.append((sql, params))
        return FakeCursor(self)

    def _fetchone(self):
        sql = self._last_sql
        if "FROM kala_gochara_publication" in sql:
            if self.manifest_status is None:
                return None
            return (uuid.uuid4(), self.manifest_status)
        if "RETURNING manifest_id" in sql:
            return (uuid.uuid4(),)
        if "method_version FROM kala_gochara_convention" in sql:
            return ("1.0.0",)
        if "RETURNING id" in sql:
            return (1,)
        return None

    def _fetchall(self):
        return []

    # convenience assertions
    def sql_of(self, needle: str) -> list[tuple[str, object]]:
        return [(s, p) for s, p in self.statements if needle in s]


def _ctx(conn) -> ContextSpec:
    return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="test-build",
                       db_conn=conn, config={"chart_id": CHART_ID})


class _FreshReport:
    state = "FRESH"
    current = "sha256:test"

    def summary(self):
        return "fresh (test stub)"


@pytest.fixture
def fresh_gate(monkeypatch):
    """Stub the §12.9 freshness gate to FRESH (the real one needs a live
    overlay schema far deeper than this fake conn models)."""
    from services.ka_vedha_gochara import freshness as fr
    monkeypatch.setattr(fr, "check_overlay_freshness",
                        lambda conn, chart_id: {
                            "house_vedha": _FreshReport(),
                            "moorti": _FreshReport()})
    monkeypatch.setattr(fr, "gate_allows_overlays", lambda reports: True)


# ── (1) registration + identity ──────────────────────────────────────────────


def test_writer_is_registered_and_discoverable():
    cls = get_writer(writer_mod.ASSET_ID)
    assert cls is writer_mod.GocharaV41CandidateWriter
    assert cls.asset_id == writer_mod.ASSET_ID
    assert cls.has_substeps is True


def test_asset_identity_pins_generation_and_horizon():
    assert writer_mod.GENERATION == "4.1"
    assert writer_mod.HORIZON_START == "1998-01-01T00:00:00+00:00"
    assert writer_mod.HORIZON_END == "2026-04-18T00:00:00+00:00"
    assert writer_mod.HORIZON_TEXT == (
        "[1998-01-01T00:00:00+00:00,2026-04-18T00:00:00+00:00)")


def test_plan_substeps_shape():
    w = writer_mod.GocharaV41CandidateWriter()
    steps = w.plan_substeps(_ctx(FakeConn()))
    keys = [s.key for s in steps]
    assert keys[0] == "manifest"
    assert keys[-1] == "windows"
    assert keys[1:-1] == [f"body:{b}" for b in writer_mod.PERSISTED_BODIES]
    assert len(keys) == 10


# ── (a2) hard chart refusal — any chart ≠ the pinned A2.5 candidate chart ────

OTHER_CHART_ID = "11111111-2222-4333-8444-555555555555"


def _ctx_for_chart(conn, chart_id: str) -> ContextSpec:
    return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="test-build",
                       db_conn=conn, config={"chart_id": chart_id})


def test_plan_substeps_refuses_any_other_chart():
    w = writer_mod.GocharaV41CandidateWriter()
    with pytest.raises(writer_mod.ChartRefusal):
        w.plan_substeps(_ctx_for_chart(FakeConn(), OTHER_CHART_ID))


def test_run_substep_refuses_any_other_chart_before_dispatch(fresh_gate):
    conn = FakeConn()
    w = writer_mod.GocharaV41CandidateWriter()
    with pytest.raises(writer_mod.ChartRefusal):
        w.run_substep(_ctx_for_chart(conn, OTHER_CHART_ID),
                      SubStep(key="manifest"))
    # refused BEFORE any DML on the conn
    assert conn.statements == []


def test_pinned_chart_id_matches_the_dispatch_chart():
    assert writer_mod.PINNED_CHART_ID == CHART_ID
    src = DISPATCH.read_text()
    assert f'CHART_ID = "{writer_mod.PINNED_CHART_ID}"' in src


# ── (a3) the seed row is inert to all planners (static guard) ────────────────

SEED = PLATFORM / "scripts" / "seed" / "asset_registry_seed.ts"


def test_seed_row_is_inactive_and_cites_both_planner_predicates():
    """(c) the seeded row stays OUT of runPreparation's set
    (src/lib/build/runPreparation.ts:183, WHERE is_active = true) and
    recalibrationEnqueue's writer sweep (src/lib/build/recalibrationEnqueue.ts:141,
    is_active = true AND has_writer = true). The executable version of this
    check is platform/scripts/__tests__/a25_v41_candidate_inert.test.ts; this
    static guard keeps the pytest suite honest without a TS runner."""
    src = SEED.read_text()
    block = src.split("asset_id: 'ka_gochara_v4_41_candidate'", 1)[1]
    block = block.split("asset_id:", 1)[0]  # this asset's entry only
    assert "is_active: false" in block
    assert "is_active: true" not in block
    assert "depends_on: []" in block
    # the inertness comment cites both planner predicates
    assert "runPreparation" in block and "recalibrationEnqueue" in block


# ── (a) the writer's call path never commits/closes/opens ────────────────────


def test_manifest_substep_never_commits_rolls_back_or_closes(fresh_gate):
    conn = FakeConn(manifest_status=None)
    w = writer_mod.GocharaV41CandidateWriter()
    result = w.run_substep(_ctx(conn), SubStep(key="manifest"))
    assert conn.commits == 0 and conn.rollbacks == 0 and conn.closes == 0
    # the manifest lifecycle really ran: convention insert + candidate publish
    assert conn.sql_of("INSERT INTO kala_gochara_convention")
    published = conn.sql_of("INSERT INTO kala_gochara_publication")
    assert published, "publish_candidate must have inserted the manifest"
    # the publish is pinned to generation '4.1' and this writer's asset id
    params = published[0][1]
    assert CHART_ID in params and "4.1" in params
    assert writer_mod.ASSET_ID in params
    assert result.asset_id == writer_mod.ASSET_ID


def test_manifest_substep_is_idempotent_while_candidate(fresh_gate):
    # an EXISTING candidate manifest → publish_candidate replaces in place
    # (UPDATE), never a second INSERT, never a refusal.
    conn = FakeConn(manifest_status="candidate")
    writer_mod.GocharaV41CandidateWriter().run_substep(
        _ctx(conn), SubStep(key="manifest"))
    assert not conn.sql_of("INSERT INTO kala_gochara_publication")
    assert conn.sql_of("UPDATE kala_gochara_publication")
    assert conn.commits == 0 and conn.rollbacks == 0


def test_writer_module_source_has_no_connection_lifecycle():
    src = inspect.getsource(writer_mod)
    for forbidden in (".commit(", ".rollback(", ".close(", "connect(",
                      "psycopg"):
        assert forbidden not in src, (
            f"writer module must not contain {forbidden!r} — the "
            "orchestrator owns the transaction and the connection")


def test_ledger_write_path_never_commits():
    """The per-body ledger write path (write_contacts/write_coverage) runs on
    the caller's conn without any lifecycle call."""
    ledger = writer_mod.ledger
    conn = FakeConn(manifest_status="candidate")
    episode = writer_mod.step06_build._synthetic_episodes()[0]
    episode["orb_max_deg"] = 5.0
    ids = ledger.write_contacts(
        conn, CHART_ID, "4.1", "conv-1", [episode], "b1", bodies=["Saturn"])
    assert conn.commits == 0 and conn.rollbacks == 0 and conn.closes == 0
    assert len(ids) == 1


# ── (b) candidate-only refusal ───────────────────────────────────────────────


def test_published_generation_refuses_every_write():
    ledger = writer_mod.ledger
    conn = FakeConn(manifest_status="published")
    with pytest.raises(_pub_refusal_classes()):
        ledger._require_not_published(conn, CHART_ID, "4.1", "write_contacts")
    with pytest.raises(_pub_refusal_classes()):
        ledger.publish_candidate(conn, CHART_ID, "4.1", "conv-1", {}, {},
                                 writer_mod.HORIZON_TEXT)
    with pytest.raises(_pub_refusal_classes()):
        ledger.write_contacts(conn, CHART_ID, "4.1", "conv-1", [], "b1",
                              bodies=["Saturn"])
    # the windows projection's own guard (step06b write_windows) refuses too
    with pytest.raises(_pub_refusal_classes()):
        writer_mod.step06b_windows.write_windows(
            conn, CHART_ID, "4.1", [], source="live",
            window_columns=set())
    assert conn.commits == 0


def test_manifest_substep_refuses_a_published_41(fresh_gate):
    conn = FakeConn(manifest_status="published")
    with pytest.raises(_pub_refusal_classes()):
        writer_mod.GocharaV41CandidateWriter().run_substep(
            _ctx(conn), SubStep(key="manifest"))


def test_writer_never_flips_or_touches_authority():
    """Serving gate: rows are served only where generation =
    kala_gochara_authority.authoritative_generation (platform-mcp
    register_gochara_windows.ts AUTHORITATIVE_GENERATION_FILTER). The writer
    must never write that table nor call ledger.publish (the flip)."""
    src = inspect.getsource(writer_mod).replace(inspect.getdoc(writer_mod), "")
    assert "kala_gochara_authority" not in src
    assert ".publish(" not in src


# ── (c) horizon refusal ──────────────────────────────────────────────────────


def _row(window_start, window_end):
    return {"event_class": "major_gain", "resolution": "era",
            "window_start": window_start, "window_end": window_end}


def test_horizon_validator_admits_in_horizon_rows():
    writer_mod._validate_windows_within_horizon([
        _row(date(1998, 1, 1), date(1998, 2, 1)),
        _row(date(2026, 4, 1), date(2026, 4, 17)),
    ])


def test_horizon_validator_refuses_early_start():
    with pytest.raises(writer_mod.HorizonViolation):
        writer_mod._validate_windows_within_horizon(
            [_row(date(1997, 12, 31), date(1998, 2, 1))])


def test_horizon_validator_refuses_late_end():
    with pytest.raises(writer_mod.HorizonViolation):
        writer_mod._validate_windows_within_horizon(
            [_row(date(2026, 4, 1), date(2026, 4, 19))])


# ── (d) substep idempotency: scoped DELETE precedes INSERT ──────────────────


def test_body_scoped_write_contacts_deletes_then_inserts_in_scope():
    ledger = writer_mod.ledger
    conn = FakeConn(manifest_status="candidate")
    episode = writer_mod.step06_build._synthetic_episodes()[0]
    episode["orb_max_deg"] = 5.0
    ledger.write_contacts(conn, CHART_ID, "4.1", "conv-1", [episode], "b1",
                          bodies=["Saturn"])
    deletes = conn.sql_of("DELETE FROM kala_gochara_contacts")
    inserts = [s for s, _ in conn.statements
               if "INSERT INTO kala_gochara_contacts" in s]
    assert len(deletes) == 1 and len(inserts) == 1
    d_sql, d_params = deletes[0]
    # scoped to chart × generation × body
    assert "chart_id = %s" in d_sql and "generation = %s" in d_sql
    assert "body = ANY(%s)" in d_sql
    assert d_params[0] == CHART_ID and d_params[1] == "4.1"
    assert d_params[2] == ["Saturn"]
    # DELETE strictly precedes the INSERT
    idx_delete = conn.statements.index((d_sql, d_params))
    idx_insert = next(i for i, (s, _) in enumerate(conn.statements)
                      if "INSERT INTO kala_gochara_contacts" in s)
    assert idx_delete < idx_insert
    assert conn.rows_inserted == 1  # replace, never duplicate


def test_body_scoped_write_refuses_foreign_body_payload():
    ledger = writer_mod.ledger
    conn = FakeConn(manifest_status="candidate")
    episode = writer_mod.step06_build._synthetic_episodes()[0]
    episode["orb_max_deg"] = 5.0
    episode["body"] = "Jupiter"
    with pytest.raises(ValueError, match="bodies-scope violation"):
        ledger.write_contacts(conn, CHART_ID, "4.1", "conv-1", [episode], "b1",
                              bodies=["Saturn"])
    assert not conn.sql_of("DELETE FROM kala_gochara_contacts")


def test_body_scoped_write_coverage_deletes_then_inserts_in_scope():
    ledger = writer_mod.ledger
    conn = FakeConn(manifest_status="candidate")
    partition = {
        "partition_kind": "body_target", "partition_key": "saturn:karaka",
        "requested_horizon": writer_mod.HORIZON_TEXT,
        "completed_horizon": writer_mod.HORIZON_TEXT,
        "resolution": 2.0, "relations_searched": ["conjunction"],
        "targets_requested": 1,
        "target_resolution_state_counts": {"resolved": 1},
        "unavailable_inputs": {}, "unsearched_reason": None,
    }
    n = ledger.write_coverage(conn, CHART_ID, "4.1", "conv-1", [partition],
                              "b1", bodies=["Saturn"])
    assert n == 1
    deletes = conn.sql_of("DELETE FROM kala_gochara_coverage")
    assert len(deletes) == 1
    d_sql, d_params = deletes[0]
    assert "generation = %s" in d_sql and "partition_key" in d_sql
    assert d_params[1] == "4.1" and d_params[2] == ["saturn"]
    idx_delete = conn.statements.index((d_sql, d_params))
    idx_insert = next(i for i, (s, _) in enumerate(conn.statements)
                      if "INSERT INTO kala_gochara_coverage" in s)
    assert idx_delete < idx_insert


# ── (e) defaults byte-unchanged ──────────────────────────────────────────────


def _fn_source(module, name):
    return inspect.getsource(getattr(module, name))


def test_step06_candidate_build_main_owns_its_connection_core_does_not():
    mod = writer_mod.step06_build
    main_src = _fn_source(mod, "main")
    core_src = _fn_source(mod, "build_candidate_core")
    assert "connect(" in main_src and "conn.commit()" in main_src
    assert "conn.close()" in main_src
    assert ".commit(" not in core_src and "connect(" not in core_src
    assert ".rollback(" not in core_src and ".close(" not in core_src


def test_step06_enumerate_main_owns_its_connection_core_does_not():
    mod = writer_mod.step06_enumerate
    main_src = _fn_source(mod, "main")
    core_src = _fn_source(mod, "enumerate_core")
    assert "connect(" in main_src and "conn.close()" in main_src
    assert ".commit(" not in core_src and "connect(" not in core_src
    assert ".rollback(" not in core_src and ".close(" not in core_src
    # the core must NOT write the CLI's JSON artifacts
    assert "write_text" not in core_src


def test_step06a_core_is_read_only_on_the_caller_conn():
    core_src = _fn_source(writer_mod.step06a_context, "build_all_class_contexts")
    assert ".commit(" not in core_src and "connect(" not in core_src
    assert ".rollback(" not in core_src and ".close(" not in core_src


def test_step06b_main_owns_its_connection_core_does_not():
    mod = writer_mod.step06b_windows
    main_src = _fn_source(mod, "main")
    core_src = _fn_source(mod, "project_windows_core")
    assert "connect(" in main_src and "conn.commit()" in main_src
    assert "conn.close()" in main_src
    assert ".commit(" not in core_src and "connect(" not in core_src
    assert ".rollback(" not in core_src and ".close(" not in core_src


def test_ledger_default_scope_is_byte_unchanged():
    """bodies=None keeps the ORIGINAL unscoped-per-body delete (chart ×
    generation only) — existing callers behave exactly as before."""
    ledger = writer_mod.ledger
    conn = FakeConn(manifest_status="candidate")
    episode = writer_mod.step06_build._synthetic_episodes()[0]
    episode["orb_max_deg"] = 5.0
    ledger.write_contacts(conn, CHART_ID, "4.0", "conv-1", [episode], "b1")
    d_sql, d_params = conn.sql_of("DELETE FROM kala_gochara_contacts")[0]
    assert "body" not in d_sql
    assert d_params == (CHART_ID, "4.0")


def test_cli_exit_codes_preserved_in_source():
    """The refactored mains keep their documented exit-code mapping."""
    enum_main = _fn_source(writer_mod.step06_enumerate, "main")
    assert "return 7" in enum_main and "return 3" in enum_main
    assert "return 5" in enum_main and "return 0" in enum_main
    build_main = _fn_source(writer_mod.step06_build, "main")
    assert "return 7" in build_main and "return 6" in build_main
    assert "return 3" in build_main and "return 0" in build_main
    win_main = _fn_source(writer_mod.step06b_windows, "main")
    assert "return 7" in win_main and "return 6" in win_main
    assert "return 3" in win_main and "return 0" in win_main


# ── (f) dispatch script contract ─────────────────────────────────────────────


def test_dispatch_script_registry_insert_is_idempotent_and_dependency_free():
    src = DISPATCH.read_text()
    assert "ON CONFLICT (asset_id) DO NOTHING" in src
    assert "'{}'::text[]" in src
    # chart-scoped count_sql pinned to the '4.1' candidate generation
    assert "WHERE chart_id=$1 AND generation='4.1'" in src.replace("''", "'")
    # live no-dependents check before staging
    assert "ANY(depends_on)" in src
    # build_run names ONLY this asset, dormant throughput, prints the run id
    assert "json.dumps([ASSET_ID])" in src
    assert "'dormant'" in src
    assert "print(run_id, flush=True)" in src
    # the A4 teardown ships in --help (the module docstring): chart-scoped,
    # generation-'4.1'-only, with the three refusals documented
    assert "--help" in src and "--teardown" in src
    assert ("DELETE FROM asset_registry   WHERE asset_id = "
            "'ka_gochara_v4_41_candidate';") in src
    assert ("DELETE FROM asset_throughput WHERE asset_id = "
            "'ka_gochara_v4_41_candidate'\n         AND chart_id = '<pinned>';") in src
    assert "REFUSES when any of these holds" in src


def test_dispatch_script_inserts_the_row_inert_and_restores_inertness():
    """(a) the dispatch registry row is born is_active = false; the flip to
    true (required by _load_candidate's active+has_writer predicate) and the
    restore to false happen inside ONE database transaction with a single
    COMMIT (steward refinement M20260930T203925-f792: no other session ever
    observes is_active=true under READ COMMITTED), try/except-rollback is the
    belt for any pre-commit failure, and --help documents the discipline."""
    src = DISPATCH.read_text()
    # the INSERT itself carries is_active = false (inert to all planners)
    values = src.split(") VALUES (", 1)[1]
    assert "0, 'per_chart', false, true, true," in values
    main_src = src.split("def main()", 1)[1]
    flip_true = main_src.index(
        "UPDATE asset_registry SET is_active = true WHERE asset_id = %s")
    flip_false = main_src.index(
        "UPDATE asset_registry SET is_active = false WHERE asset_id = %s")
    commit = main_src.index("conn.commit()")
    # flip true precedes flip false, and the ONLY commit lands after both —
    # a single transaction for the whole staging window
    assert flip_true < flip_false < commit
    assert main_src.count("conn.commit()") == 1
    # belt: a pre-commit failure rolls back (nothing staged, nothing flipped)
    assert "except Exception:" in src and "conn.rollback()" in src
    # --help documents the single-transaction flip/restore and the manual
    # recovery UPDATE
    assert "ONE database transaction" in src
    assert "UPDATE asset_registry SET is_active = false" in src


def test_dispatch_single_transaction_committed_end_state_is_inert():
    """The committed end state of a staging run: is_active=false AND the
    build_run staged — asserted against a recording fake psycopg module so
    the real statement order is exercised through main() itself."""
    import types

    statements: list[str] = []
    commits: list[int] = []

    class FakeCur:
        def execute(self, sql, params=None):
            statements.append(sql)
            self._last = sql

        def fetchall(self):
            if "ANY(depends_on)" in self._last:
                return []  # no dependents
            return []

        def fetchone(self):
            if "FROM asset_registry WHERE asset_id" in self._last:
                return {"scope": "per_chart", "is_active": False,
                        "has_writer": True, "has_substeps": True,
                        "writer_timeout_seconds": 7200, "depends_on": []}
            if "_load_candidate" in self._last or "has_cowriters" in self._last:
                return {
                    "asset_id": "ka_gochara_v4_41_candidate",
                    "layer": "kala", "scope": "per_chart",
                    "asset_kind": "data", "depends_on": [],
                    "natural_key_partition": None, "has_cowriters": True,
                }
            return None

    class FakeConn:
        autocommit = False

        def cursor(self):
            return FakeCur()

        def commit(self):
            commits.append(len(statements))

        def rollback(self):
            statements.append("ROLLBACK")

        def close(self):
            pass

    fake_psycopg = types.ModuleType("psycopg")
    fake_rows = types.ModuleType("psycopg.rows")
    fake_rows.dict_row = object()
    fake_psycopg.rows = fake_rows
    fake_psycopg.connect = lambda *a, **k: FakeConn()

    sys.path.insert(0, str(DISPATCH.parent))
    saved = dict(sys.modules)
    prior_db_url = os.environ.get("DATABASE_URL")
    try:
        sys.modules["psycopg"] = fake_psycopg
        sys.modules["psycopg.rows"] = fake_rows
        os.environ["DATABASE_URL"] = "postgresql://fake/fake"
        import importlib
        import dispatch_a25_v41_candidate_job as dispatch
        importlib.reload(dispatch)
        dispatch.main()
    finally:
        if prior_db_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior_db_url
        sys.modules.pop("psycopg", None)
        sys.modules.pop("psycopg.rows", None)
        for name in ("dispatch_a25_v41_candidate_job",):
            sys.modules.pop(name, None)
        sys.path.remove(str(DISPATCH.parent))
        for name, mod in saved.items():
            if name.startswith("psycopg"):
                sys.modules[name] = mod

    # exactly one commit, and at that commit the LAST is_active write was the
    # restore to false — the committed end state is inert
    assert len(commits) == 1
    staged = statements[: commits[0]]
    flips = [s for s in staged if "SET is_active" in s]
    assert flips[0].count("is_active = true") == 1
    assert flips[-1].count("is_active = false") == 1
    # staging happened inside the same transaction: build_runs + manifest
    assert any("INSERT INTO build_runs" in s and "plan_manifest" in s
               for s in staged)
    assert any("INSERT INTO build_run_assets" in s for s in staged)
    assert not any(s == "ROLLBACK" for s in statements)


def test_dispatch_script_stages_a_frozen_manifest_run():
    """Condition 3: build_runs carries plan_manifest/plan_manifest_digest from
    dispatch_frozen_rebuild.build_manifest (runner.py's
    validate_frozen_run_manifest requires both), with the writer's
    expected_code_digest from the checked-in digest inventory."""
    src = DISPATCH.read_text()
    assert "from dispatch_frozen_rebuild import" in src
    assert "build_manifest" in src and "_load_writer_digest" in src
    assert "_load_candidate" in src
    assert "plan_manifest, plan_manifest_digest" in src
    assert "%s::jsonb, %s, %s" in src


def test_dispatch_frozen_manifest_shape_for_this_asset():
    """The frozen manifest for the A2.5 asset is the asset_set/v1 shape the
    runner validates: scope_target = asset id, single wave, expected digest
    from src/generated/nirmana-writer-digests.json."""
    sys.path.insert(0, str(DISPATCH.parent))
    try:
        from dispatch_frozen_rebuild import build_manifest, _load_writer_digest
    finally:
        sys.path.remove(str(DISPATCH.parent))
    digest = _load_writer_digest("ka_gochara_v4_41_candidate")
    assert isinstance(digest, str) and len(digest) == 64
    candidate = {"asset_id": "ka_gochara_v4_41_candidate", "scope": "per_chart",
                 "depends_on": [], "natural_key_partition": None,
                 "has_cowriters": True}
    manifest, mdigest = build_manifest(
        chart_id=CHART_ID, candidate=candidate, expected_code_digest=digest)
    assert manifest["version"] == "nirmana-run-manifest/v1"
    assert manifest["scope"] == "asset_set"
    assert manifest["scope_target"] == "ka_gochara_v4_41_candidate"
    assert manifest["action"] == "rebuild"
    assert manifest["chart_id"] == CHART_ID
    assert manifest["waves"] == [["ka_gochara_v4_41_candidate"]]
    [asset] = manifest["assets"]
    assert asset["asset_id"] == "ka_gochara_v4_41_candidate"
    assert asset["depends_on"] == [] and asset["has_cowriters"] is True
    assert asset["expected_code_digest"] == digest
    import hashlib
    import json as _json
    canonical = _json.dumps(manifest, ensure_ascii=True, sort_keys=True,
                            separators=(",", ":"))
    assert mdigest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_dispatch_script_help_prints_docstring(capsys):
    import subprocess
    out = subprocess.run(
        [sys.executable, str(DISPATCH), "--help"],
        capture_output=True, text=True)
    assert out.returncode == 0
    assert "TEARDOWN" in out.stdout
    assert "ka_gochara_v4_41_candidate" in out.stdout


# ── ASTRA v1.0 PUSH 1: A1 (runner's real types), A6 (CLI exit 6), A8 (dry_run) ─


class DictFakeConn(FakeConn):
    """FakeConn returning DICT rows — the governed runner's connection uses
    psycopg.rows.dict_row (ASTRA A2.5 A1). Same steering as FakeConn."""

    def _fetchone(self):
        sql = self._last_sql
        if "FROM kala_gochara_publication" in sql:
            if self.manifest_status is None:
                return None
            return {"manifest_id": uuid.uuid4(), "status": self.manifest_status}
        if "RETURNING manifest_id" in sql:
            return {"manifest_id": uuid.uuid4()}
        if "method_version FROM kala_gochara_convention" in sql:
            return {"method_version": "1.0.0"}
        if "count(*)" in sql:
            return {"count": 0}
        if "to_regclass" in sql:
            return {"to_regclass": None}
        if "row_to_json" in sql:
            return {"row_to_json": {}}
        if "RETURNING id" in sql:
            return {"id": 1}
        return None


def test_chart_guard_accepts_the_runners_uuid_and_the_clis_string():
    """A1: runner.load_run() passes a psycopg UUID; the CLI passes a string.
    BOTH name the pinned chart; a foreign value of EITHER type refuses."""
    writer_mod._require_pinned_chart(CHART_ID)                      # CLI str
    writer_mod._require_pinned_chart(uuid.UUID(CHART_ID))           # runner UUID
    with pytest.raises(writer_mod.ChartRefusal):
        writer_mod._require_pinned_chart(uuid.uuid4())
    with pytest.raises(writer_mod.ChartRefusal):
        writer_mod._require_pinned_chart("not-the-chart")


def test_plan_and_refusal_behave_identically_for_uuid_chart():
    w = writer_mod.GocharaV41CandidateWriter()
    conn = FakeConn()
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="t",
                      db_conn=conn, config={"chart_id": uuid.UUID(CHART_ID)})
    keys = [s.key for s in w.plan_substeps(ctx)]
    assert keys[0] == "manifest" and len(keys) == 10


def test_ledger_manifest_path_accepts_dict_rows():
    """A1: the manifest lifecycle (create → candidate guard → replace) runs
    on a dict-row connection with no KeyError — and the refusal still fires."""
    ledger = writer_mod.ledger
    conn = DictFakeConn(manifest_status=None)
    mid = ledger.publish_candidate(conn, CHART_ID, "4.1", "conv-1",
                                   {"k": "v"}, {"backend": "swieph"},
                                   "[2020-01-01,2030-01-01)")
    assert mid
    conn.manifest_status = "candidate"
    assert ledger._candidate_manifest_id(conn, CHART_ID, "4.1")
    conn.manifest_status = "published"
    with pytest.raises(ledger.PublishedGenerationRefusal):
        ledger._require_not_published(conn, CHART_ID, "4.1", "write_contacts")
    with pytest.raises(ledger.PublishedGenerationRefusal):
        ledger.publish_candidate(conn, CHART_ID, "4.1", "conv-1", {}, {},
                                 "[2020-01-01,2030-01-01)")


def test_ledger_write_and_publish_paths_accept_dict_rows():
    """A1: write_contacts' method_version read, publish()'s row_to_json and
    count(*) reads, and the to_regclass probe all run on dict rows."""
    ledger = writer_mod.ledger
    conn = DictFakeConn(manifest_status="candidate")
    episode = writer_mod.step06_build._synthetic_episodes()[0]
    episode["orb_max_deg"] = 5.0
    ledger.write_contacts(conn, CHART_ID, "4.1", "conv-1", [episode], "b1",
                          bodies=["Saturn"])
    conn.manifest_status = "candidate"
    mid = ledger.publish(conn, CHART_ID, "4.1")
    assert mid


def test_step06b_fetchers_accept_dict_rows():
    """A1: the projection's contact/map/vedha/baseline reads run on dict rows."""
    mod = writer_mod.step06b_windows
    conn = DictFakeConn()
    cols = ("contact_id", "body", "relation", "target_type", "target_ref",
            "target_longitude_deg", "t_in", "t_exact", "t_out", "orb_max_deg",
            "completeness_state", "aspect_deg", "independence_group", "branch")
    t = datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    row = dict(zip(cols, ("c1", "Saturn", "residence", "sign", "libra",
                          200.0, t, t, t, 5.0, "exact", 0.0, "g1", "b")))
    conn_rows = [row]

    class _C(DictFakeConn):
        def _fetchall(self):
            return conn_rows
    out = mod.fetch_contacts(_C(), CHART_ID, "4.1")
    assert out[0]["body"] == "Saturn" and out[0]["_orb_deg"] == 5.0

    class _M(DictFakeConn):
        def _fetchall(self):
            return [{"event_class": "marriage", "target_type": "sign",
                     "target_ref": "libra", "weight": 1.0}]
    assert mod.fetch_map_rows(_M(), CHART_ID)[0]["event_class"] == "marriage"


def test_dry_run_suppresses_every_dml_path(fresh_gate):
    """A8: dry_run=True issues NO DML — through the inherited run() (whole
    plan) and through a direct run_substep() call."""
    w = writer_mod.GocharaV41CandidateWriter()
    conn = FakeConn()
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="t",
                      db_conn=conn, config={"chart_id": CHART_ID},
                      dry_run=True)
    result = w.run(ctx)  # inherited: aggregates plan_substeps × run_substep
    dml = [s for s, _ in conn.statements
           if any(k in s for k in ("INSERT", "UPDATE", "DELETE"))]
    assert dml == []
    conn2 = FakeConn()
    ctx2 = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="t",
                       db_conn=conn2, config={"chart_id": CHART_ID},
                       dry_run=True)
    r = w.run_substep(ctx2, SubStep(key="manifest", label="m"))
    assert r.rows_inserted == 0 and "dry_run" in r.notes
    assert conn2.statements == [] or not [
        s for s, _ in conn2.statements
        if any(k in s for k in ("INSERT", "UPDATE", "DELETE"))]
    assert result is not None


def _load_step06_build_from_git(revision: str, name: str, tmp_path: Path):
    """The merge-base CLI, loaded from git — the A6 comparison's baseline."""
    import subprocess
    import importlib.util
    blob = subprocess.run(
        ["git", "-C", str(SIDECAR.parent.parent), "show",
         f"{revision}:platform/python-sidecar/scripts/kala_gochara_cutover/"
         "step06_candidate_build.py"],
        capture_output=True, text=True, check=True).stdout
    path = tmp_path / f"{name}.py"
    path.write_text(blob)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    # the baseline's _LEDGER_PATH resolves against its tmp location — point
    # it at the real ledger so the comparison exercises the same core.
    mod._LEDGER_PATH = SIDECAR / "services" / "gochara_kernel" / "ledger.py"
    return mod


def _run_cli_refusal(mod, conn, monkeypatch, capsys):
    """Drive one step06_candidate_build main() against a published-manifest
    fake conn; return (exit_code, stderr)."""
    monkeypatch.setattr(mod, "connect", lambda *a, **k: conn)
    monkeypatch.setattr(sys, "argv",
                        ["step06_candidate_build.py", "--dsn", "fake",
                         "--chart-id", CHART_ID, "--generation", "4.1",
                         "--rehearse-synthetic"])
    try:
        code = mod.main()
    except SystemExit as exc:  # an uncaught refusal escaping via sys.exit
        code = exc.code
    except Exception as exc:  # an uncaught refusal escaping as a traceback
        code = f"RAISED:{type(exc).__name__}"
    return code, capsys.readouterr().err


def test_cli_published_refusal_exit6_baseline_vs_refactored(tmp_path,
                                                            monkeypatch,
                                                            capsys):
    """A6: the published-generation refusal exits 6 with REFUSED on BOTH the
    merge-base CLI and this commit's CLI — the exception class caught is the
    class the core raises (a fresh _load_ledger() per call mints a distinct
    class and the refusal escapes)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "a25_test_step06_current",
        CUTOVER / "step06_candidate_build.py")
    current = importlib.util.module_from_spec(spec)
    sys.modules["a25_test_step06_current"] = current
    spec.loader.exec_module(current)
    baseline = _load_step06_build_from_git(
        "2b3e096739b3501395a74c079846433c1bee3992",
        "a25_test_step06_baseline", tmp_path)

    for mod in (current, baseline):
        mod._LEDGER_MODULE = None  # isolate the comparison per module
    results = {}
    for label, mod in (("baseline", baseline), ("current", current)):
        conn = FakeConn(manifest_status="published")
        code, err = _run_cli_refusal(mod, conn, monkeypatch, capsys)
        results[label] = (code, err)
    assert results["baseline"][0] == 6, results
    assert "REFUSED" in results["baseline"][1]
    assert results["current"] == results["baseline"], results


# ── ASTRA v1.0 PUSH 2: A2 (half-open horizon), A5 (ephemeris resolution) ──────


def test_validator_refuses_a_day_row_on_the_excluded_end_date():
    """A2: the reviewer produced day [2026-04-18, 2026-04-18] through the real
    projection and the old validator ACCEPTED it."""
    row = {"event_class": "marriage", "resolution": "day",
           "window_start": date(2026, 4, 18), "window_end": date(2026, 4, 18),
           "peak_date": date(2026, 4, 18)}
    with pytest.raises(writer_mod.HorizonViolation):
        writer_mod._validate_windows_within_horizon([row])


def test_validator_refuses_a_peak_on_the_excluded_end_date():
    row = {"event_class": "marriage", "resolution": "era",
           "window_start": date(2026, 4, 8), "window_end": date(2026, 4, 18),
           "peak_date": date(2026, 4, 18)}
    with pytest.raises(writer_mod.HorizonViolation):
        writer_mod._validate_windows_within_horizon([row])


def test_validator_admits_a_window_ending_exactly_at_the_limit():
    """An exclusive interval endpoint legitimately EQUALS the horizon limit."""
    row = {"event_class": "marriage", "resolution": "era",
           "window_start": date(2026, 4, 8), "window_end": date(2026, 4, 18),
           "peak_date": date(2026, 4, 17)}
    writer_mod._validate_windows_within_horizon([row])


def test_validator_refuses_a_peak_outside_its_own_span():
    row = {"event_class": "marriage", "resolution": "month",
           "window_start": date(2026, 4, 1), "window_end": date(2026, 4, 17),
           "peak_date": date(2026, 3, 30)}
    with pytest.raises(writer_mod.HorizonViolation):
        writer_mod._validate_windows_within_horizon([row])


def test_episode_backstop_half_open():
    """A2: contact-side validation BEFORE contact DML."""
    h0 = datetime.fromisoformat(writer_mod.HORIZON_START)
    h1 = datetime.fromisoformat(writer_mod.HORIZON_END)
    ok = {"t_in": h0, "t_exact": h0, "t_out": h1}     # exact at start; end==limit
    writer_mod._validate_episodes_within_horizon([ok])
    truncated = {"t_in": h0, "t_exact": None, "t_out": h1}  # N3 truncated span
    writer_mod._validate_episodes_within_horizon([truncated])
    from datetime import timedelta
    early = {"t_in": h0, "t_exact": h0 - timedelta(microseconds=40),
             "t_out": h0 + timedelta(days=1)}
    with pytest.raises(writer_mod.HorizonViolation):
        writer_mod._validate_episodes_within_horizon([early])
    at_end = {"t_in": h1 - timedelta(days=1), "t_exact": h1, "t_out": h1}
    with pytest.raises(writer_mod.HorizonViolation):
        writer_mod._validate_episodes_within_horizon([at_end])


def _jd(y, m, d):
    import swisseph as swe
    return swe.julday(y, m, d, 0.0)


def _linear_index(body, jd0, jd1, slope_deg_per_day, offset_deg=0.0):
    """Daily-knot linear curve — spline-exact crossings with refine=False."""
    from services.gochara_kernel import arcs as gk_arcs
    jds, lons = [], []
    d = jd0
    while d <= jd1:
        jds.append(d)
        lons.append((offset_deg + (d - jd0) * slope_deg_per_day) % 360.0)
        d += 1.0
    return gk_arcs.build_arc_index(body, jds, lons, tolerance_arcsec=0.5)


def test_boundary_membership_is_half_open_and_exact():
    """A2 (root cause): solve_boundary_episodes keeps a crossing exactly AT
    the horizon start, drops one ~40µs before it, and drops one exactly AT
    the excluded end."""
    from services.gochara_kernel import episodes as gk_episodes
    h0, h1 = _jd(2020, 1, 1), _jd(2021, 1, 1)

    # slope 30°/day with a 0° crossing exactly at h0: crossings daily
    # thereafter; h1 = h0 + 366d (2020 is a leap year) → (366*30)%360 = 30°
    # crossing exactly at h1.
    index = _linear_index("Sun", h0 - 10, h1 + 10, 30.0)
    eps = gk_episodes.solve_boundary_episodes(
        index, "Sun", "sign_ingress", (h0, h1), refine=False)
    instants = [e.t_exact for e in eps]
    assert h0 in instants                      # start-inclusive (R2Q3)
    assert h1 not in instants                  # excluded end
    assert all(h0 <= t < h1 for t in instants)
    assert (h0 - 1.0) not in instants          # before the domain

    # a crossing 40µs before h0 must NOT be retained (the old 1e-9d slack
    # admitted it)
    eps_days = 40e-6 / 86400.0
    index2 = _linear_index("Sun", h0 - 10, h1 + 10, 30.0,
                           offset_deg=(-( - eps_days) * 30.0) % 360.0)
    # curve: λ(h0 - eps) = 0 (a crossing 40µs before h0)
    index2 = None
    jd0 = h0 - eps_days
    from services.gochara_kernel import arcs as gk_arcs
    jds, lons = [], []
    d = h0 - 10
    while d <= h1 + 10:
        jds.append(d)
        lons.append(((d - jd0) * 30.0) % 360.0)
        d += 1.0
    index2 = gk_arcs.build_arc_index("Sun", jds, lons, tolerance_arcsec=0.5)
    eps2 = gk_episodes.solve_boundary_episodes(
        index2, "Sun", "sign_ingress", (h0, h1), refine=False)
    instants2 = [e.t_exact for e in eps2]
    assert all(h0 <= t < h1 for t in instants2)
    assert (h0 - eps_days) not in instants2


def test_projection_series_never_samples_the_excluded_end():
    """A2 production side: the projection's series excludes horizon_jd[1]."""
    mod = writer_mod.step06b_windows
    src = inspect.getsource(mod.project_class_windows)
    assert "horizon_jd[0] <= b < horizon_jd[1]" in src
    assert "while t < horizon_jd[1]:" in src
    assert "<= horizon_jd[1]" not in src


def test_resolve_ephe_path_order(monkeypatch):
    """A5: explicit config > the image's SWE_EPHE_PATH > the dev default."""
    import os
    conn = FakeConn()
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="t",
                      db_conn=conn,
                      config={"chart_id": CHART_ID, "ephe_path": "/explicit"})
    assert writer_mod.resolve_ephe_path(ctx) == "/explicit"
    ctx2 = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="t",
                       db_conn=conn, config={"chart_id": CHART_ID})
    monkeypatch.setenv("SWE_EPHE_PATH", "/app/ephe")
    assert writer_mod.resolve_ephe_path(ctx2) == "/app/ephe"
    monkeypatch.delenv("SWE_EPHE_PATH")
    assert writer_mod.resolve_ephe_path(ctx2) == writer_mod.DEFAULT_EPHE_PATH


def test_swieph_backend_through_the_resolved_path():
    """A5: the resolved ephemeris path feeds the kernel's own sampler, which
    asserts the SWIEPH backend from the returned retflag on EVERY calc
    (F-14 — a Moshier fallback raises EphemerisBackendError). Runs against
    the checksum-pinned local .se1 set; the image gets the same check with
    SWE_EPHE_PATH=/app/ephe at dispatch."""
    from tests.l3.gochara import conftest as _c
    if _c._PROBLEMS:
        pytest.skip(f"NOT_RUN: .se1 ephemeris files: {_c._PROBLEMS}")
    from services.gochara_kernel.knots import sample_knots
    ks = sample_knots("Sun", date(2020, 1, 1), date(2020, 2, 1), _c.EPHE_PATH)
    assert ks.ephemeris_backend["backend"] == "swieph"
    assert len(ks.knot_jds) > 0


# ── ASTRA v1.0 PUSH 3: A4 (teardown), A10 (registry row validation) ──────────


class _DispatchCur:
    """Cursor for dispatch-script tests: records statements, answers from a
    steering dict keyed by a substring of the SQL."""

    def __init__(self, conn, answers):
        self._conn = conn
        self._answers = answers
        self._last = ""

    def execute(self, sql, params=None):
        self._conn.statements.append((sql, params))
        self._last = sql

    def fetchone(self):
        for key, val in self._answers.items():
            if key in self._last:
                return val[0] if isinstance(val, list) else val
        return None

    def fetchall(self):
        for key, val in self._answers.items():
            if key in self._last:
                return val if isinstance(val, list) else [val]
        return []


class _DispatchConn:
    def __init__(self, answers):
        self.statements: list[tuple[str, object]] = []
        self.commits = 0
        self.rollbacks = 0
        self._answers = answers

    def cursor(self):
        return _DispatchCur(self, self._answers)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        pass


def _run_dispatch(answers, argv, monkeypatch):
    """Run the dispatch script against a recording fake psycopg; returns
    (module, conn). `argv[0]` selects the mode: [] stages, ['--teardown']
    tears down."""
    import types

    conn = _DispatchConn(answers)
    fake_psycopg = types.ModuleType("psycopg")
    fake_rows = types.ModuleType("psycopg.rows")
    fake_rows.dict_row = object()
    fake_psycopg.rows = fake_rows
    fake_psycopg.connect = lambda *a, **k: conn
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", fake_rows)
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")
    monkeypatch.setattr(sys, "argv", ["dispatch_a25_v41_candidate_job.py"] + argv)
    sys.path.insert(0, str(DISPATCH.parent))
    try:
        import importlib
        import dispatch_a25_v41_candidate_job as dispatch
        importlib.reload(dispatch)
        yield_dispatch = dispatch
        if "--teardown" in argv:
            yield_dispatch.teardown()
        else:
            yield_dispatch.main()
    finally:
        sys.path.remove(str(DISPATCH.parent))
        sys.modules.pop("dispatch_a25_v41_candidate_job", None)
    return conn


_REGROW_OK = {
    "FROM asset_registry WHERE asset_id": {
        "scope": "per_chart", "is_active": False, "has_writer": True,
        "has_substeps": True, "writer_timeout_seconds": 7200,
        "depends_on": []},
    "has_cowriters": {
        "asset_id": "ka_gochara_v4_41_candidate", "layer": "kala",
        "scope": "per_chart", "asset_kind": "data", "depends_on": [],
        "natural_key_partition": None, "has_cowriters": True},
}


def test_teardown_refuses_a_published_generation(monkeypatch):
    """A4: a published '4.1' manifest for the pinned chart → loud refusal,
    NOTHING deleted, no commit."""
    answers = {"FROM kala_gochara_publication":
               {"manifest_id": str(uuid.uuid4()), "status": "published"}}
    with pytest.raises(RuntimeError, match="published"):
        _run_dispatch(answers, ["--teardown"], monkeypatch)


def test_teardown_refuses_a_serving_generation(monkeypatch):
    """A4: kala_gochara_authority naming '4.1' for the pinned chart → refuse."""
    answers = {"FROM kala_gochara_authority":
               {"authoritative_generation": "4.1"}}
    with pytest.raises(RuntimeError, match="authoritative"):
        _run_dispatch(answers, ["--teardown"], monkeypatch)


def test_teardown_refuses_an_active_run(monkeypatch):
    """A4: a planned/running/paused build_run for this asset+chart → refuse."""
    answers = {"FROM build_runs": [{"id": str(uuid.uuid4()), "state": "running"}]}
    with pytest.raises(RuntimeError, match="active"):
        _run_dispatch(answers, ["--teardown"], monkeypatch)


def test_teardown_deletes_chart_scoped_in_one_transaction(monkeypatch):
    """A4 happy path: every candidate-row DELETE is scoped to the pinned
    chart AND generation '4.1'; build-run/throughput deletes are chart- and
    run-scoped; ONE commit; no other generation is touched."""
    conn = _run_dispatch({}, ["--teardown"], monkeypatch)
    deletes = [s for s, _ in conn.statements if s.lstrip().upper().startswith("DELETE")]
    assert conn.commits == 1 and conn.rollbacks == 0
    assert deletes, "teardown issued no DELETEs"
    kala = [s for s in deletes if "kala_gochara" in s]
    assert len(kala) == 4  # windows, contacts, coverage, publication
    for s in kala:
        assert "chart_id" in s and "'4.1'" in s, s
    assert any("build_run_assets" in s for s in deletes)
    assert any("FROM build_runs" in s and "chart_id" in s for s in deletes)
    assert any("asset_throughput" in s and "chart_id" in s for s in deletes)
    assert any("asset_registry" in s for s in deletes)
    # never another generation
    assert not any("'3.0'" in s or "'v1'" in s for s in deletes)


def test_teardown_flag_dispatches_to_teardown(monkeypatch):
    """A4: `--teardown` on the CLI runs the teardown path, not staging."""
    conn = _run_dispatch({}, ["--teardown"], monkeypatch)
    assert not any("INSERT INTO build_runs" in s for s, _ in conn.statements)


def test_dispatch_refuses_a_preexisting_row_with_wrong_timeout(monkeypatch):
    """A10: ON CONFLICT DO NOTHING preserves a seeded row; if that row carries
    writer_timeout_seconds=600 (or any non-conforming field), staging REFUSES
    before the is_active flip — the runner would otherwise read the seeded
    ten-minute budget for this two-hour job."""
    answers = dict(_REGROW_OK)
    answers["FROM asset_registry WHERE asset_id"] = dict(
        answers["FROM asset_registry WHERE asset_id"],
        writer_timeout_seconds=600)
    conn_holder = {}

    def _connect(*a, **k):
        c = _DispatchConn(answers)
        conn_holder["c"] = c
        return c

    import types
    fake_psycopg = types.ModuleType("psycopg")
    fake_rows = types.ModuleType("psycopg.rows")
    fake_rows.dict_row = object()
    fake_psycopg.rows = fake_rows
    fake_psycopg.connect = _connect
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", fake_rows)
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")
    monkeypatch.setattr(sys, "argv", ["dispatch_a25_v41_candidate_job.py"])
    sys.path.insert(0, str(DISPATCH.parent))
    try:
        import importlib
        import dispatch_a25_v41_candidate_job as dispatch
        importlib.reload(dispatch)
        with pytest.raises(RuntimeError, match="writer_timeout_seconds"):
            dispatch.main()
    finally:
        sys.path.remove(str(DISPATCH.parent))
        sys.modules.pop("dispatch_a25_v41_candidate_job", None)
    # refused BEFORE the transient activation: no is_active flip, no staging
    stmts = [s for s, _ in conn_holder["c"].statements]
    assert not any("SET is_active = true" in s for s in stmts)
    assert not any("INSERT INTO build_runs" in s for s in stmts)
    assert conn_holder["c"].commits == 0


# ── ASTRA v1.0 PUSH 3: A3 (complete executable source closure) ───────────────


def test_writer_source_closure_covers_dynamically_loaded_modules():
    """A3: the frozen hasher follows static imports; this writer loads four
    cutover modules and two kernel modules BY PATH. The declared source_paths
    closure must cover all of them, so a change to any invalidates the
    writer's expected code digest."""
    from pipeline.orchestrator.asset_runner import (
        _writer_source_files,
        _writer_source_paths,
    )
    files = {p for p, _ in _writer_source_files(
        _writer_source_paths(writer_mod.ASSET_ID))}
    for frag in (
        "writers/ka_gochara_v4_41_candidate.py",
        "kala_gochara_cutover/step06_enumerate_episodes.py",
        "kala_gochara_cutover/step06_candidate_build.py",
        "kala_gochara_cutover/step06a_class_context.py",
        "kala_gochara_cutover/step06b_windows_projection.py",
        "gochara_kernel/ledger.py",
        "gochara_kernel/legacy_semantics.py",
    ):
        assert any(f.endswith(frag) for f in files), frag


def test_writer_source_closure_digest_covers_the_closure():
    """A3: two independent proofs in one — (1) the closure is non-trivial
    (the reviewer's run found 35 files WITHOUT the cutover/ledger modules;
    the declared closure must be strictly larger), and (2) mutating a
    dynamically loaded module changes the digest."""
    import hashlib
    from pipeline.orchestrator.asset_runner import (
        _writer_source_files,
        _writer_source_paths,
        get_writer_source_hash,
    )
    paths = _writer_source_paths(writer_mod.ASSET_ID)
    files = _writer_source_files(paths)
    assert len(files) > 35
    assert any("step06_candidate_build.py" in p for p, _ in files)

    digest = get_writer_source_hash(writer_mod.ASSET_ID)
    # recompute with one closure file's content perturbed → different digest
    perturbed = hashlib.sha256()
    import pipeline.orchestrator.asset_runner as ar
    orig = ar._writer_source_files
    try:
        def _tampered(paths_):
            out = []
            for p, c in orig(paths_):
                if p.endswith("step06_candidate_build.py"):
                    c = c + b"\n# tampered\n"
                out.append((p, c))
            return out
        ar._writer_source_files = _tampered
        assert get_writer_source_hash(writer_mod.ASSET_ID) != digest
    finally:
        ar._writer_source_files = orig

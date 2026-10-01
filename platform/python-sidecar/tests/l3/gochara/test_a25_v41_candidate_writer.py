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
    # exact teardown DELETEs ship in --help (the module docstring)
    assert "--help" in src
    assert ("DELETE FROM asset_registry   WHERE asset_id = "
            "'ka_gochara_v4_41_candidate';") in src
    assert ("DELETE FROM asset_throughput WHERE asset_id = "
            "'ka_gochara_v4_41_candidate';") in src


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
    flip_true = src.index(
        "UPDATE asset_registry SET is_active = true WHERE asset_id = %s")
    flip_false = src.index(
        "UPDATE asset_registry SET is_active = false WHERE asset_id = %s")
    commit = src.index("conn.commit()")
    # flip true precedes flip false, and the ONLY commit lands after both —
    # a single transaction for the whole staging window
    assert flip_true < flip_false < commit
    assert src.count("conn.commit()") == 1
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
            if "SELECT depends_on FROM asset_registry" in self._last:
                return {"depends_on": []}
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

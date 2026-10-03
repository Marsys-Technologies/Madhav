"""Regression: every registered ``bo_*`` L2 producer accepts the REAL-path ``uuid.UUID`` chart_id.

On the real orchestrator path ``ctx.config['chart_id']`` is a ``uuid.UUID``
(``runner.load_run`` reads ``build_runs.chart_id`` through ``dict_row`` and
``asset_runner._run_data_writer`` puts it into ``ContextSpec.config``
unconverted). ``begin_observation`` rejects a non-``str`` chart_id, and the
adapters hash chart_id payloads with ``json.dumps`` (no ``default``). The fix
is ONE conversion in the shared ``l2_producer`` wrapper
(``bodha_writers.data_plane_contracts._coerce_chart_id_to_str``).

Three code paths are covered, each with a real ``uuid.UUID`` and the REAL
registered adapters (all 23 ``CURRENT_WRITERS``):

1. wrapper level: ``run`` / ``run_substep`` driven directly;
2. orchestrator entrypoint: ``asset_runner._run_data_writer`` (the function the
   production scheduler calls), including ``plan_substeps`` and the savepoint
   driver, against the real registered adapter;
3. contract level: ``_resolve_upstream_context`` / ``_open_generation`` /
   ``_complete_partition`` receive ``str`` chart_ids and the generation id for
   a UUID equals the one for its ``str`` form (str behaviour unchanged).

A fake connection raises ``FirstDbAccess`` on the first non-contract SQL, so a
passing test proves the adapter got past ``begin_observation`` and into its own
body; it does not claim the adapter body is correct against a database.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

import bodha_writers.data_plane_contracts as dpc
from bodha_writers.data_plane_contracts import (
    ContractError,
    CURRENT_WRITERS,
    begin_observation,
    l2_producer,
)
from pipeline.orchestrator import asset_runner as ar
from pipeline.orchestrator.writers import ContextSpec, WriterBase, WriterResult, discover_all, get_writer

CHART_UUID = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
CHART_STR = str(CHART_UUID)
BUILD_ID = "00000000-0000-4000-8000-0000000000b1"

_CONTRACT_SQL = (
    "set_config",
    "open_l2_data_plane_generation",
    "bind_l2_exact_inputs",
    "complete_l2_data_plane_partition",
)


# Adapters whose body performs no DB access of its own.
_NO_DB_ADAPTERS = frozenset({"bo_samvada"})


class FirstDbAccess(Exception):
    """The adapter body reached its own first database access."""


class _Cursor:
    description = None

    def __init__(self, log):
        self._log = log

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        if any(token in sql for token in _CONTRACT_SQL):
            self._log.append((sql, params))
            return
        raise FirstDbAccess(" ".join(sql.split())[:80])

    def fetchall(self):
        raise FirstDbAccess("fetchall")

    def fetchone(self):
        raise FirstDbAccess("fetchone")


class _Conn:
    _l2_contract_test_double = True

    def __init__(self):
        self.contract_sql: list[tuple[str, object]] = []

    def cursor(self, *_args, **_kwargs):
        return _Cursor(self.contract_sql)

    def execute(self, sql, *_args, **_kwargs):
        raise FirstDbAccess("conn.execute " + " ".join(str(sql).split())[:60])

    def commit(self):
        pass

    def rollback(self):
        pass


def _upstream(chart_id, partition_key):
    vector = [{
        "layer": "L1",
        "asset_id": "ga_positions",
        "generation_id": "l1-generation-1",
        "semantic_output_digest": "f" * 64,
    }]
    context = {
        "subject_id": "subject-1",
        "chart_id": chart_id,
        "generation_context_id": "l2:generation-context:exact",
        "calculation_context_id": "l1ctx:exact",
        "ayanamsha_id": "mixed_or_invariant",
        "reference_frame": "sidereal",
        "varga_id": "row_declared_or_D1",
        "partition_key": partition_key,
    }
    return vector, context


@pytest.fixture
def contract_stubs(monkeypatch):
    """Stub only the DB-backed upstream resolver and the source-hash lookup."""
    seen_chart_ids: list[object] = []

    def resolve(_conn, *, chart_id, asset_id, partition_key):
        seen_chart_ids.append(chart_id)
        return _upstream(chart_id, partition_key)

    monkeypatch.setattr(dpc, "_resolve_upstream_context", resolve)
    monkeypatch.setattr(dpc, "_writer_source_digest", lambda _asset_id: "a" * 64)
    return seen_chart_ids


def _registered(asset_id: str) -> WriterBase:
    discover_all()
    writer_cls = get_writer(asset_id)
    assert writer_cls is not None, f"{asset_id} is not registered"
    return writer_cls()


def _ctx(conn, chart_id=CHART_UUID) -> ContextSpec:
    return ContextSpec(
        asset_id="ignored", build_id=BUILD_ID, db_conn=conn,
        config={"chart_id": chart_id, "birth_params": {}},
    )


def test_registered_set_is_exactly_the_23_contract_writers():
    discover_all()
    for asset_id in CURRENT_WRITERS:
        writer = _registered(asset_id)
        entry = writer.run_substep if writer.has_substeps else writer.run
        assert getattr(entry, "__l2_data_plane_contract__", False) is True, asset_id


@pytest.mark.parametrize("asset_id", CURRENT_WRITERS)
def test_wrapper_accepts_uuid_chart_id_and_reaches_adapter_body(asset_id, contract_stubs):
    writer = _registered(asset_id)
    conn = _Conn()
    ctx = _ctx(conn)
    assert isinstance(ctx.config["chart_id"], uuid.UUID)
    try:
        if writer.has_substeps:
            writer.run_substep(ctx, writer.plan_substeps(ctx)[0])
        else:
            result = writer.run(ctx)
            # A no-DB adapter (bo_samvada) completes: the contract closed it.
            assert "l2_generation=" in result.notes
    except FirstDbAccess:
        pass
    # The wrapper wrote the canonical string back, the resolver and the
    # generation SQL only ever saw that string.
    assert ctx.config["chart_id"] == CHART_STR
    assert type(ctx.config["chart_id"]) is str
    assert contract_stubs == [CHART_STR]
    opened = [p for sql, p in conn.contract_sql if "open_l2_data_plane_generation" in sql]
    assert len(opened) == 1 and opened[0][0] == CHART_STR
    assert ctx.config["_l2_calculation_context"]["chart_id"] == CHART_STR


@pytest.mark.parametrize("asset_id", CURRENT_WRITERS)
def test_orchestrator_entrypoint_runs_real_adapter_with_uuid_chart_id(
    asset_id, contract_stubs, monkeypatch,
):
    errors: list[str] = []
    monkeypatch.setattr(ar, "emit_event", lambda event, cur=None: None)
    monkeypatch.setattr(ar, "fetch_birth_params", lambda conn, chart_id: {})
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda cur, aid, cid, *a, **k: "up")
    monkeypatch.setattr(ar, "get_writer_source_hash", lambda aid: "a" * 64)
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [])
    monkeypatch.setattr(
        ar, "mark_asset_error",
        lambda conn, cur, run_id, chart_id, aid, error: errors.append(error),
    )

    class OrchestratorCursor:
        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return None

        def fetchall(self):
            return []

    conn = _Conn()
    completed = ar._run_data_writer(
        conn, OrchestratorCursor(), BUILD_ID, CHART_UUID, asset_id,
    )
    joined = "\n".join(errors)
    assert "ContractError" not in joined, joined
    assert "not JSON serializable" not in joined, joined
    assert "TypeError" not in joined, joined
    assert "requires non-empty chart_id" not in joined, joined
    if asset_id in _NO_DB_ADAPTERS:
        # bo_samvada is a passive adapter: it completes inside the contract.
        assert completed is True and errors == []
    else:
        # The adapter got past begin_observation into its own first DB access.
        assert completed is False
        assert len(errors) == 1 and errors[0].startswith("FirstDbAccess"), joined
    assert set(contract_stubs) == {CHART_STR}


def test_entrypoint_success_path_passes_str_chart_id_to_contract_sql(monkeypatch):
    """A successful decorated heavy writer through ``_run_data_writer`` + real UUID."""
    monkeypatch.setattr(dpc, "_writer_source_digest", lambda _asset_id: "a" * 64)
    seen: list[object] = []

    def resolve(_conn, *, chart_id, asset_id, partition_key):
        seen.append(chart_id)
        return _upstream(chart_id, partition_key)

    monkeypatch.setattr(dpc, "_resolve_upstream_context", resolve)

    @l2_producer("bo_samskara")
    class Heavy(WriterBase):
        asset_id = "bo_samskara"
        has_substeps = True

        def plan_substeps(self, ctx):
            return [SimpleNamespace(key="aya_lahiri", label="lahiri")]

        def run_substep(self, ctx, step):
            # The payload shape the real adapters hash: no ``default=`` hook.
            import json

            json.dumps({"chart_id": ctx.config["chart_id"]})
            return WriterResult(asset_id=self.asset_id, rows_inserted=1)

    monkeypatch.setattr(ar, "emit_event", lambda event, cur=None: None)
    monkeypatch.setattr(ar, "discover_all", lambda: None)
    monkeypatch.setattr(ar, "get_writer", lambda aid: Heavy)
    monkeypatch.setattr(ar, "fetch_birth_params", lambda conn, chart_id: {})
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda cur, aid, cid, *a, **k: "up")
    monkeypatch.setattr(ar, "get_writer_source_hash", lambda aid: "a" * 64)
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [])
    monkeypatch.setattr(ar, "compute_downstream_closure", lambda cur, aid: [])
    errors: list[str] = []
    monkeypatch.setattr(
        ar, "mark_asset_error",
        lambda conn, cur, run_id, chart_id, aid, error: errors.append(error),
    )

    class OrchestratorCursor:
        def __init__(self):
            self.executed = []

        def execute(self, sql, params=None):
            self.executed.append((sql, params))

        def fetchone(self):
            return None

        def fetchall(self):
            return []

    conn = _Conn()
    cur = OrchestratorCursor()
    assert ar._run_data_writer(conn, cur, BUILD_ID, CHART_UUID, "bo_samskara") is True
    assert errors == []
    assert seen == [CHART_STR]
    sql_by_kind = {
        token: [p for sql, p in conn.contract_sql if token in sql]
        for token in ("open_l2_data_plane_generation", "complete_l2_data_plane_partition")
    }
    assert [p[0] for p in sql_by_kind["open_l2_data_plane_generation"]] == [CHART_STR]
    assert [p[0] for p in sql_by_kind["complete_l2_data_plane_partition"]] == [CHART_STR]


def test_str_chart_id_behaviour_is_unchanged_and_matches_uuid_generation(contract_stubs):
    def observe(chart_id):
        ctx = SimpleNamespace(build_id=BUILD_ID, config={"chart_id": chart_id})
        vector, context = _upstream(CHART_STR, "bo_arudha")
        return begin_observation(
            ctx, "bo_arudha", "a" * 64,
            dependency_vector=vector, calculation_context=context,
        )

    # begin_observation itself still requires str (the wrapper is the adapter
    # boundary, the contract is not loosened).
    with pytest.raises(ContractError, match="non-empty chart_id"):
        observe(CHART_UUID)
    by_str = observe(CHART_STR)
    assert by_str.chart_id == CHART_STR

    class Probe:
        asset_id = "bo_arudha"

        def run(self, ctx):
            return SimpleNamespace(rows_inserted=0, rows_updated=0, rows_skipped=0, notes="")

    Wrapped = l2_producer("bo_arudha")(Probe)

    def generation(chart_id):
        conn = _Conn()
        ctx = SimpleNamespace(
            build_id=BUILD_ID, config={"chart_id": chart_id}, db_conn=conn, dry_run=False,
        )
        result = Wrapped().run(ctx)
        return result.notes, ctx.config["chart_id"]

    notes_uuid, cfg_uuid = generation(CHART_UUID)
    notes_str, cfg_str = generation(CHART_STR)
    assert notes_uuid == notes_str
    assert cfg_uuid == cfg_str == CHART_STR
    assert f"l2_generation={by_str.generation_id}" in notes_uuid


@pytest.mark.parametrize("dry_run", [True, False])
def test_wrapper_normalises_even_when_contract_sql_is_skipped(dry_run):
    """dry_run / plain-double connections skip the SQL contract but still get a str."""
    seen = {}

    class Probe:
        asset_id = "bo_arudha"

        def run(self, ctx):
            seen["chart_id"] = ctx.config["chart_id"]
            return SimpleNamespace(rows_inserted=0, rows_updated=0, rows_skipped=0, notes="")

    Wrapped = l2_producer("bo_arudha")(Probe)
    ctx = SimpleNamespace(
        build_id=BUILD_ID, config={"chart_id": CHART_UUID},
        db_conn=object(), dry_run=dry_run,
    )
    Wrapped().run(ctx)
    assert seen["chart_id"] == CHART_STR and type(seen["chart_id"]) is str


@pytest.mark.parametrize("missing", [None, ""])
def test_missing_chart_id_still_fails_closed(missing, contract_stubs):
    class Probe:
        asset_id = "bo_arudha"

        def run(self, ctx):
            raise AssertionError("must not run")

    Wrapped = l2_producer("bo_arudha")(Probe)
    ctx = SimpleNamespace(
        build_id=BUILD_ID, config={"chart_id": missing}, db_conn=_Conn(), dry_run=False,
    )
    with pytest.raises(ContractError, match="requires chart_id"):
        Wrapped().run(ctx)
    assert ctx.config["chart_id"] == missing

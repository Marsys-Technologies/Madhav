"""The l2_producer wrapper must BIND the exact inputs before it OPENS the generation.

``open_l2_data_plane_generation()`` (migration 1036:983-996) raises "L2 generation open requires an exact-input bind receipt" unless the
transaction-local ``pg_temp.l2_data_plane_bind_receipt`` created by ``bind_l2_exact_inputs()`` (1036:908-917) already exists. The wrapper
used to call open (line ~505) before bind (line ~521): on a real database every bo_* asset failed at open (confirmed on a disposable
PostgreSQL 15 as the production builder role, S_L2 evidence ``BO_UUID_FIX_REPORT_2.md``). The Python tests only ever used fake
connections, so nothing noticed. These tests pin the order with a recording connection (no database needed); the same order is proven on
a real PostgreSQL by ``test_l2_wrapper_real_pg.py`` (integration, skipped without ``L2_WRAPPER_REALPG_*``).
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

import bodha_writers.data_plane_contracts as dpc
from bodha_writers.data_plane_contracts import l2_producer

CHART = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
BUILD = "00000000-0000-4000-8000-0000000000b1"

_KINDS = (
    ("set_config", "set_config"),
    ("bind_l2_exact_inputs", "bind"),
    ("open_l2_data_plane_generation", "open"),
    ("complete_l2_data_plane_partition", "complete"),
    ("SET LOCAL search_path = public, pg_temp", "search_path"),
)


class _RecordingCursor:
    description = None

    def __init__(self, log):
        self._log = log

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def execute(self, sql, params=None):
        for needle, kind in _KINDS:
            if needle in sql:
                self._log.append(kind)
                return
        raise AssertionError(f"unexpected SQL in the wrapper: {sql!r}")


class _RecordingConn:
    _l2_contract_test_double = True

    def __init__(self):
        self.log: list[str] = []

    def cursor(self):
        return _RecordingCursor(self.log)


def _upstream(chart_id, partition_key):
    vector = [{"layer": "L1", "asset_id": "ga_positions", "generation_id": "g1", "semantic_output_digest": "f" * 64}]
    context = {
        "subject_id": "s", "chart_id": chart_id, "generation_context_id": "gc", "calculation_context_id": "cc",
        "ayanamsha_id": "mixed_or_invariant", "reference_frame": "sidereal", "varga_id": "row_declared_or_D1",
        "partition_key": partition_key,
    }
    return vector, context


@pytest.fixture(autouse=True)
def _stubs(monkeypatch):
    monkeypatch.setattr(dpc, "_resolve_upstream_context", lambda _c, *, chart_id, asset_id, partition_key: _upstream(chart_id, partition_key))
    monkeypatch.setattr(dpc, "_writer_source_digest", lambda _a: "a" * 64)


def test_wrapper_binds_before_it_opens_and_resets_name_resolution_last():
    class Probe:
        asset_id = "bo_arudha"

        def run(self, ctx):
            ctx.db_conn.log.append("body")
            return SimpleNamespace(rows_inserted=0, rows_updated=0, rows_skipped=0, notes="")

    Wrapped = l2_producer("bo_arudha")(Probe)
    conn = _RecordingConn()
    ctx = SimpleNamespace(build_id=BUILD, config={"chart_id": CHART}, db_conn=conn, dry_run=False)
    Wrapped().run(ctx)
    assert conn.log == ["set_config", "bind", "open", "body", "complete", "search_path"], conn.log


def test_open_generation_issues_bind_strictly_before_open():
    conn = _RecordingConn()
    ctx = SimpleNamespace(build_id=BUILD, config={"chart_id": str(CHART)}, db_conn=conn, dry_run=False)
    vector, context = _upstream(str(CHART), "bo_arudha")
    observation = dpc.begin_observation(ctx, "bo_arudha", "a" * 64, dependency_vector=vector, calculation_context=context)
    dpc._open_generation(ctx, observation, expected_partitions=1)
    assert conn.log == ["set_config", "bind", "open"], conn.log
    assert conn.log.index("bind") < conn.log.index("open")


@pytest.mark.parametrize("asset_id", dpc.CURRENT_WRITERS)
def test_every_registered_producer_uses_the_one_open_path(asset_id):
    """There is exactly one place that calls open: the shared wrapper. No bo_* module may call it (or bind) itself."""
    import pathlib
    writers = pathlib.Path(dpc.__file__).resolve().parents[1] / "pipeline" / "orchestrator" / "writers"
    for path in writers.glob("bo_*.py"):
        text = path.read_text()
        assert "open_l2_data_plane_generation" not in text and "bind_l2_exact_inputs" not in text, path.name

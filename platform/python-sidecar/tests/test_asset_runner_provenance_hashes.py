"""F0 provenance hashes must describe real, scoped inputs deterministically."""
from __future__ import annotations

from datetime import datetime, timezone
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar


class _Cursor:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self.rows


def test_canonical_upstream_hash_is_order_independent_and_input_sensitive():
    at = datetime(2026, 8, 25, 1, 2, 3, 456789, tzinfo=timezone.utc)
    rows = [
        {"asset_id": "ga_positions", "last_built_at": at},
        {"asset_id": "bg_ephemeris", "last_built_at": None},
    ]
    original = ar.canonical_upstream_hash("bo_summary", "chart-a", rows)

    assert original == ar.canonical_upstream_hash("bo_summary", "chart-a", list(reversed(rows)))
    assert len(original) == 64
    assert original != ar.canonical_upstream_hash("bo_summary", "chart-b", rows)
    assert original != ar.canonical_upstream_hash(
        "bo_summary", "chart-a", [{"asset_id": "ga_positions", "last_built_at": at}],
    )


def test_compute_upstream_hash_uses_the_global_row_for_a_global_dependency():
    rows = [
        {"asset_id": "bg_ephemeris", "last_built_at": datetime(2026, 8, 25, tzinfo=timezone.utc)},
        {"asset_id": "ga_positions", "last_built_at": datetime(2026, 8, 24, tzinfo=timezone.utc)},
    ]
    cursor = _Cursor(rows)

    actual = ar.compute_upstream_hash(cursor, "bo_summary", "chart-a")

    assert actual == ar.canonical_upstream_hash("bo_summary", "chart-a", rows)
    sql, params = cursor.calls[0]
    assert "LEFT JOIN LATERAL" in sql
    assert "CASE WHEN ar.scope = 'global' THEN at.chart_id IS NULL" in sql
    assert params == ("chart-a", "bo_summary")


def test_compute_upstream_hash_uses_global_scope_when_the_build_itself_is_global():
    cursor = _Cursor([{"asset_id": "bg_ephemeris", "last_built_at": None}])

    ar.compute_upstream_hash(cursor, "bg_fixture", None)

    _sql, params = cursor.calls[0]
    assert params == (None, "bg_fixture")


def _proven_row(asset_id, output_digest="out-digest", **overrides):
    row = {
        "asset_id": asset_id,
        "receipt_version": "nirmana-provenance-receipt-v2",
        "code_digest": "code", "config_digest": "config",
        "upstream_digest": "up", "partition_digest": "part",
        "output_digest": output_digest,
        "receipt_state": "proven",
        "observed_at": datetime(2026, 9, 7, tzinfo=timezone.utc),
        "asset_kind": "data", "service_health": None,
    }
    row.update(overrides)
    return row


def test_compute_upstream_hash_declared_deps_requires_proven_receipts_for_data_deps(monkeypatch):
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [
        _proven_row("ga_positions"),
        _proven_row("ga_dashas", receipt_state="unknown"),
    ])

    assert ar.compute_upstream_hash(_Cursor([]), "ga_yoga", "chart-a", ["ga_positions", "ga_dashas"]) is None


def test_compute_upstream_hash_accommodates_a_healthy_service_dependency_stuck_unknown(monkeypatch):
    """§7.2 (D-NATIVE-07): a service whose receipt is 'unknown' solely because
    output_digest_spec doesn't apply to it must not block its dependents --
    the service's own real, already-persisted output_digest is used, gated on
    a live asset_kind='service' + service_health='healthy' check."""
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [
        _proven_row(
            "bg_ephemeris_engine", output_digest="probe-digest",
            receipt_state="unknown", asset_kind="service", service_health="healthy",
        ),
    ])

    digest = ar.compute_upstream_hash(_Cursor([]), "bg_cohort", None, ["bg_ephemeris_engine"])

    assert digest is not None
    assert len(digest) == 64


def test_compute_upstream_hash_service_accommodation_is_not_a_blanket_bypass(monkeypatch):
    """A service dependency that is unhealthy, or a non-service dependency
    that is merely unproven, must still block -- the accommodation only
    fires for a live-verified healthy service, never as a general escape
    hatch for any 'unknown' receipt."""
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [
        _proven_row(
            "bg_ephemeris_engine", output_digest="probe-digest",
            receipt_state="unknown", asset_kind="service", service_health="degraded",
        ),
    ])
    assert ar.compute_upstream_hash(_Cursor([]), "bg_cohort", None, ["bg_ephemeris_engine"]) is None

    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [
        _proven_row("ga_structural", receipt_state="unknown", asset_kind="data", service_health=None),
    ])
    assert ar.compute_upstream_hash(_Cursor([]), "ga_yoga", "chart-a", ["ga_structural"]) is None


def test_compute_upstream_hash_still_requires_a_real_output_digest_from_a_healthy_service(monkeypatch):
    """A healthy service that has never been probed (no output_digest at
    all) is a genuinely unavailable upstream, not an accommodated one."""
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [
        _proven_row(
            "bg_ephemeris_engine", output_digest=None,
            receipt_state="unknown", asset_kind="service", service_health="healthy",
        ),
    ])

    assert ar.compute_upstream_hash(_Cursor([]), "bg_cohort", None, ["bg_ephemeris_engine"]) is None


def test_compute_upstream_hash_excludes_asset_kind_and_service_health_from_the_digest_payload(monkeypatch):
    """asset_kind/service_health are live lookups added to help this
    decision, not part of the receipt's own identity -- the digest a data
    dependency produces must be unaffected by their presence."""
    rows_without = [_proven_row("ga_positions")]
    for row in rows_without:
        del row["asset_kind"]
        del row["service_health"]
    rows_with = [_proven_row("ga_positions")]

    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: rows_without)
    without = ar.compute_upstream_hash(_Cursor([]), "ga_yoga", "chart-a", ["ga_positions"])

    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: rows_with)
    with_fields = ar.compute_upstream_hash(_Cursor([]), "ga_yoga", "chart-a", ["ga_positions"])

    assert without == with_fields


def test_writer_source_hash_is_content_based_and_order_independent(monkeypatch, tmp_path):
    first = tmp_path / "a_writer.py"
    second = tmp_path / "b_helper.py"
    first.write_text("VALUE = 'one'\n")
    second.write_text("VALUE = 'two'\n")
    monkeypatch.setattr(ar, "_writer_source_paths", lambda _: [str(tmp_path)])

    initial = ar.get_writer_source_hash("fixture.writer")
    assert len(initial) == 64
    assert initial == ar.get_writer_source_hash("fixture.writer")

    second.write_text("VALUE = 'changed'\n")
    assert initial != ar.get_writer_source_hash("fixture.writer")


def test_writer_source_hash_rejects_missing_source(monkeypatch, tmp_path):
    monkeypatch.setattr(ar, "_writer_source_paths", lambda _: [str(tmp_path / "missing.py")])

    with pytest.raises(RuntimeError, match="unavailable"):
        ar.get_writer_source_hash("fixture.writer")


def test_delegated_service_writer_hashes_its_full_implementation_package():
    from pipeline.orchestrator.writers import discover_all

    discover_all()
    dasha_files = ar._writer_source_files(ar._writer_source_paths("ka_dasha_kala"))
    dasha_names = {path.rsplit("/", 1)[-1] for path, _content in dasha_files}
    graha_files = ar._writer_source_files(ar._writer_source_paths("ka_graha_sancara"))
    graha_paths = {path for path, _content in graha_files}
    positions_files = ar._writer_source_files(ar._writer_source_paths("ga_positions"))
    positions_paths = {path for path, _content in positions_files}

    assert {"writer.py", "service.py", "eligibility.py", "tree_walk.py"} <= dasha_names
    assert "platform/python-sidecar/services/ka_graha_sancara/engine.py" in graha_paths
    assert "platform/python-sidecar/pyjhora_adapter/compute.py" in positions_paths
    assert "platform/python-sidecar/brahmagyan/graha_vocabulary.py" in positions_paths

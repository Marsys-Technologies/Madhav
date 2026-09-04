"""Unit coverage for the sidecar-owned provenance receipt contract."""
from __future__ import annotations

from dataclasses import replace
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from pipeline.orchestrator.provenance import (
    WHOLE_ASSET_PARTITION,
    build_receipt,
    canonical_digest,
    classify_receipt,
    persist_successful_receipt,
    previous_output_digest,
    previous_receipt_matches_inputs,
    reconcile_receipt,
)
from pipeline.orchestrator.provenance_inventory import DEFAULT_OUTPUT


def _receipt(**overrides):
    values = {
        "asset_id": "ga_positions",
        "chart_id": "00000000-0000-0000-0000-000000000001",
        "code_digest": "code-a",
        "config": {"birth": {"lat": 20, "lon": 85}, "mode": "sidereal"},
        "upstream_digest": "upstream-a",
        "upstream_receipts": [{"asset_id": "bg_ephemeris", "digest": "ephem-a"}],
        "partition_declaration": "chart_id",
        "has_cowriters": False,
        "output_digest": "output-a",
        "output_digest_spec_sha256": "a" * 64,
    }
    values.update(overrides)
    return build_receipt(**values)


def test_config_digest_is_stable_across_mapping_order():
    left = _receipt(config={"mode": "sidereal", "birth": {"lon": 85, "lat": 20}})
    right = _receipt(config={"birth": {"lat": 20, "lon": 85}, "mode": "sidereal"})
    assert left.config_digest == right.config_digest
    assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})


def test_checked_in_writer_digest_inventory_matches_sidecar_sources():
    # The broader suite deliberately mutates WRITER_REGISTRY in several tests.
    # Verify the generated artefact in a clean interpreter, matching the CI and
    # release invocation instead of depending on order-contaminated module state.
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pipeline.orchestrator.provenance_inventory",
            "--check",
            "--output",
            str(DEFAULT_OUTPUT),
        ],
        check=True,
        cwd=pathlib.Path(__file__).resolve().parents[3],
    )


def test_each_receipt_dimension_is_classified_independently():
    stored = _receipt()
    for field in ("code_digest", "config_digest", "upstream_digest", "partition_digest", "output_digest", "output_digest_spec_sha256"):
        current = replace(stored, **{field: f"changed-{field}"})
        assert classify_receipt(stored, current) == ("stale", [f"{field}_changed"])


def test_receipt_contract_version_change_is_never_fresh():
    stored = _receipt()
    current = replace(stored, receipt_version="nirmana-provenance-receipt-v3")
    assert classify_receipt(stored, current) == ("stale", ["receipt_version_changed"])


def test_partition_omission_is_unknown_only_for_shared_output():
    whole = _receipt(partition_declaration=None, has_cowriters=False)
    assert whole.partition_key == WHOLE_ASSET_PARTITION
    assert whole.receipt_state == "proven"

    shared = _receipt(partition_declaration=None, has_cowriters=True)
    assert shared.receipt_state == "unknown"
    assert shared.unknown_reasons == ("partition_digest_unavailable", "partition_undeclared")
    assert classify_receipt(shared, shared)[0] == "unknown"


def test_digest_omission_is_an_explicit_unknown_blocker():
    unknown = _receipt(code_digest=None, output_digest=None)
    assert unknown.receipt_state == "unknown"
    assert unknown.unknown_reasons == ("code_digest_unavailable", "output_digest_unavailable")
    assert classify_receipt(_receipt(), unknown) == (
        "unknown", ["code_digest_unavailable", "output_digest_unavailable"],
    )


def test_no_reviewed_output_spec_is_unknown_even_when_a_legacy_digest_exists():
    legacy = _receipt(output_digest_spec_sha256=None)
    assert legacy.receipt_state == "unknown"
    assert legacy.unknown_reasons == ("output_digest_spec_unavailable",)


def test_unserialisable_config_is_unknown_not_a_successful_digest():
    receipt = _receipt(config={"unsupported": object()})
    assert receipt.config_digest is None
    assert receipt.unknown_reasons == ("config_digest_unavailable",)


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.executed: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.rows.pop(0)


def test_reconciliation_records_stale_without_replacing_last_successful_receipt():
    current = _receipt()
    cursor = _Cursor([{
        "code_digest": "old-code", "config_digest": current.config_digest,
        "upstream_digest": current.upstream_digest, "partition_digest": current.partition_digest,
        "output_digest": current.output_digest, "upstream_receipts": [], "unknown_reasons": [],
        "output_digest_spec_sha256": current.output_digest_spec_sha256,
        "receipt_version": current.receipt_version,
    }])

    assert reconcile_receipt(cursor, current) == ("stale", ["code_digest_changed"])
    assert len(cursor.executed) == 2
    assert "SELECT code_digest" in cursor.executed[0][0]
    assert "INSERT INTO asset_freshness" in cursor.executed[1][0]
    assert "asset_provenance_receipts" not in cursor.executed[1][0]


def test_successful_receipt_replaces_receipt_and_restores_fresh_idempotently():
    receipt = _receipt()
    cursor = _Cursor([])

    assert persist_successful_receipt(cursor, receipt, "00000000-0000-0000-0000-000000000002") == ("fresh", [])
    assert persist_successful_receipt(cursor, receipt, "00000000-0000-0000-0000-000000000002") == ("fresh", [])
    assert len(cursor.executed) == 4
    assert all("ON CONFLICT" in sql for sql, _ in cursor.executed)
    assert "asset_provenance_receipts" in cursor.executed[0][0]
    assert "asset_freshness" in cursor.executed[1][0]


# ── previous_output_digest (O-wave WP-1, read-side lookup helper) ─────────────

def test_previous_output_digest_returns_none_when_no_receipt_exists():
    cursor = _Cursor([None])
    result = previous_output_digest(
        cursor, asset_id="ga_positions", chart_id="chart-1", partition_key=WHOLE_ASSET_PARTITION,
    )
    assert result is None
    assert "SELECT output_digest" in cursor.executed[0][0]
    assert cursor.executed[0][1] == ("ga_positions", "chart-1", WHOLE_ASSET_PARTITION)


def test_previous_output_digest_reads_the_stored_value_dict_row():
    cursor = _Cursor([{"output_digest": "output-a"}])
    result = previous_output_digest(
        cursor, asset_id="ga_positions", chart_id="chart-1", partition_key=WHOLE_ASSET_PARTITION,
    )
    assert result == "output-a"


def test_previous_output_digest_reads_the_stored_value_tuple_row():
    cursor = _Cursor([("output-b",)])
    result = previous_output_digest(
        cursor, asset_id="ga_positions", chart_id="chart-1", partition_key=WHOLE_ASSET_PARTITION,
    )
    assert result == "output-b"


def test_previous_output_digest_never_mutates():
    """A read-side helper must never INSERT/UPDATE -- only the one SELECT."""
    cursor = _Cursor([{"output_digest": "output-a"}])
    previous_output_digest(
        cursor, asset_id="ga_positions", chart_id="chart-1", partition_key=WHOLE_ASSET_PARTITION,
    )
    assert len(cursor.executed) == 1
    assert cursor.executed[0][0].strip().upper().startswith("SELECT")


# ── previous_receipt_matches_inputs (O-wave WP-2, pre-execution delta gate) ───

_MATCH_KWARGS = dict(
    asset_id="ga_positions",
    chart_id="00000000-0000-0000-0000-000000000001",
    code_digest="code-a",
    config={"birth": {"lat": 20, "lon": 85}, "mode": "sidereal"},
    upstream_digest="upstream-a",
    partition_declaration="chart_id",
    has_cowriters=False,
)


def _stored_row_matching(**overrides):
    """A stored asset_provenance_receipts row that exactly matches
    _MATCH_KWARGS's inputs (via the same build_receipt construction), with
    optional field overrides to simulate drift."""
    matching = build_receipt(
        asset_id=_MATCH_KWARGS["asset_id"], chart_id=_MATCH_KWARGS["chart_id"],
        code_digest=_MATCH_KWARGS["code_digest"], config=_MATCH_KWARGS["config"],
        upstream_digest=_MATCH_KWARGS["upstream_digest"], upstream_receipts=[],
        partition_declaration=_MATCH_KWARGS["partition_declaration"],
        has_cowriters=_MATCH_KWARGS["has_cowriters"],
        output_digest="output-a", output_digest_spec_sha256="a" * 64,
    )
    row = {
        "code_digest": matching.code_digest, "config_digest": matching.config_digest,
        "upstream_digest": matching.upstream_digest, "partition_digest": matching.partition_digest,
        "output_digest": matching.output_digest, "output_digest_spec_sha256": matching.output_digest_spec_sha256,
        "upstream_receipts": [], "unknown_reasons": [], "receipt_version": matching.receipt_version,
    }
    row.update(overrides)
    return row


def test_matches_when_every_input_digest_agrees_with_the_stored_proven_receipt():
    cursor = _Cursor([_stored_row_matching()])
    assert previous_receipt_matches_inputs(cursor, **_MATCH_KWARGS) is True


def test_does_not_match_when_code_digest_changed():
    assert previous_receipt_matches_inputs(
        _Cursor([_stored_row_matching()]), **{**_MATCH_KWARGS, "code_digest": "code-b"},
    ) is False


def test_does_not_match_when_config_changed():
    assert previous_receipt_matches_inputs(
        _Cursor([_stored_row_matching()]),
        **{**_MATCH_KWARGS, "config": {"mode": "tropical"}},
    ) is False


def test_does_not_match_when_upstream_digest_changed():
    assert previous_receipt_matches_inputs(
        _Cursor([_stored_row_matching()]), **{**_MATCH_KWARGS, "upstream_digest": "upstream-b"},
    ) is False


def test_fails_open_when_no_stored_receipt_exists():
    assert previous_receipt_matches_inputs(_Cursor([None]), **_MATCH_KWARGS) is False


def test_fails_open_when_the_stored_receipt_is_unknown():
    row = _stored_row_matching(code_digest=None, unknown_reasons=["code_digest_unavailable"])
    assert previous_receipt_matches_inputs(_Cursor([row]), **_MATCH_KWARGS) is False


def test_fails_open_when_the_stored_receipt_version_differs():
    row = _stored_row_matching(receipt_version="nirmana-provenance-receipt-v3")
    assert previous_receipt_matches_inputs(_Cursor([row]), **_MATCH_KWARGS) is False


def test_fails_open_when_current_code_digest_is_missing():
    """No query needed at all -- missing current input is decided before the
    stored-receipt lookup even runs."""
    cursor = _Cursor([])
    assert previous_receipt_matches_inputs(
        cursor, **{**_MATCH_KWARGS, "code_digest": None},
    ) is False
    assert cursor.executed == []


def test_fails_open_when_current_upstream_digest_is_missing():
    cursor = _Cursor([])
    assert previous_receipt_matches_inputs(
        cursor, **{**_MATCH_KWARGS, "upstream_digest": None},
    ) is False
    assert cursor.executed == []


def test_never_mutates():
    cursor = _Cursor([_stored_row_matching()])
    previous_receipt_matches_inputs(cursor, **_MATCH_KWARGS)
    assert len(cursor.executed) == 1
    assert cursor.executed[0][0].strip().upper().startswith("SELECT")

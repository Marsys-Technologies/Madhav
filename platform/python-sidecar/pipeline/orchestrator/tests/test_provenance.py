"""Unit coverage for the sidecar-owned provenance receipt contract."""
from __future__ import annotations

from dataclasses import replace
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from pipeline.orchestrator.provenance import (
    WHOLE_ASSET_PARTITION,
    build_receipt,
    canonical_digest,
    classify_receipt,
    persist_successful_receipt,
    reconcile_receipt,
)
from pipeline.orchestrator.provenance_inventory import DEFAULT_OUTPUT, build_inventory


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
    }
    values.update(overrides)
    return build_receipt(**values)


def test_config_digest_is_stable_across_mapping_order():
    left = _receipt(config={"mode": "sidereal", "birth": {"lon": 85, "lat": 20}})
    right = _receipt(config={"birth": {"lat": 20, "lon": 85}, "mode": "sidereal"})
    assert left.config_digest == right.config_digest
    assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})


def test_checked_in_writer_digest_inventory_matches_sidecar_sources():
    assert json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8")) == build_inventory()


def test_each_receipt_dimension_is_classified_independently():
    stored = _receipt()
    for field in ("code_digest", "config_digest", "upstream_digest", "partition_digest", "output_digest"):
        current = replace(stored, **{field: f"changed-{field}"})
        assert classify_receipt(stored, current) == ("stale", [f"{field}_changed"])


def test_receipt_contract_version_change_is_never_fresh():
    stored = _receipt()
    current = replace(stored, receipt_version="nirmana-provenance-receipt-v2")
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

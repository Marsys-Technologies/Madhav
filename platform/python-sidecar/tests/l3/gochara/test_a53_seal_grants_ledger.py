"""P05-B03: seal approval evidence binds the landed verifier/sealer grants, not archived 1241."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.gochara_kernel import seal_brief as sb


LANDED_FILENAME = "1378_gochara_verifier_sealer_inventory_grants.sql"
LANDED_SHA256 = "04540a995e849517d03d80835a4dfaae0ee588c081485337d976814e44a70108"
APPLIED_AT = datetime(2026, 10, 14, 20, 0, tzinfo=timezone.utc)


class LedgerConnection:
    """Supply applied-ledger rows without a live database; selection and hashing stay real."""

    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params=()):
        assert sql == "SELECT filename, sha256, applied_at FROM public._migrations_applied ORDER BY filename"
        return self

    def fetchall(self):
        return self.rows


def test_landed_grants_filename_and_hash_are_in_seal_approval_evidence():
    ledger = sb._ledger_evidence(LedgerConnection([(LANDED_FILENAME, LANDED_SHA256, APPLIED_AT)]))

    assert [entry for entry in ledger if entry["migration"] == "1378"] == [{
        "migration": "1378",
        "applied": [{"filename": LANDED_FILENAME, "sha256": LANDED_SHA256,
                     "applied_at": "2026-10-14T20:00:00+00:00"}],
    }]


def test_changing_landed_grants_hash_changes_seal_approval_evidence_digest():
    before = sb._ledger_evidence(LedgerConnection([(LANDED_FILENAME, LANDED_SHA256, APPLIED_AT)]))
    after = sb._ledger_evidence(LedgerConnection([(LANDED_FILENAME, "b" * 64, APPLIED_AT)]))

    assert sb.payload_digest({"ledger": before}) != sb.payload_digest({"ledger": after})


def test_archived_1241_alone_does_not_supply_landed_grants_evidence():
    ledger = sb._ledger_evidence(LedgerConnection([
        ("1241_gochara_verifier_sealer_inventory_grants.sql", "a" * 64, APPLIED_AT),
    ]))

    assert [entry for entry in ledger if entry["migration"] == "1378"] == [{"migration": "1378", "applied": []}]
    assert [entry for entry in ledger if entry["migration"] == "1241"] == [{
        "migration": "1241",
        "applied": [{"filename": "1241_gochara_verifier_sealer_inventory_grants.sql", "sha256": "a" * 64,
                     "applied_at": "2026-10-14T20:00:00+00:00"}],
    }]
    assert all(not entry["applied"] for entry in ledger if entry["migration"] != "1241")


@pytest.mark.parametrize("filename", [
    "1241_gochara_verifier_sealer_inventory_grants.sql",
    "1305_gochara_snapshot_owns_l1_copy.sql",
    "1306_gochara_expected_class_census.sql",
    "1308_gochara_near_miss_storage.sql",
    LANDED_FILENAME,
])
def test_required_migration_hash_changes_invalidate_the_approval_evidence(filename):
    before = sb._ledger_evidence(LedgerConnection([(filename, "a" * 64, APPLIED_AT)]))
    after = sb._ledger_evidence(LedgerConnection([(filename, "b" * 64, APPLIED_AT)]))

    assert sb.payload_digest({"ledger": before}) != sb.payload_digest({"ledger": after})

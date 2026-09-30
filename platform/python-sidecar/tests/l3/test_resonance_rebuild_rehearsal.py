"""ASTRA_REVIEW_A5_4 P1-7 / P1-8 — the resonance-rebuild rehearsal is a
FAILING acceptance check and the runbook's backup/rollback is verifiable.

Pure tests (no DB): the acceptance function fails on every violated R-1..R-6
property, the rerun and the rollback checks; the SQL module refuses unsafe
names/values, never uses IF NOT EXISTS for the snapshot, and the runbook
carries the module's statements verbatim (drift guard). The live disposable
run is `resonance_rebuild_disposable_rehearsal.py` itself (exit 1 on any
failure) — its output is recorded in evidence/resonance_rebuild_R1_R6_
evidence.md.
"""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "scripts" / "kala_gochara_cutover"
sys.path.insert(0, str(HERE))

import resonance_rebuild_backup_sql as B  # noqa: E402


def _load_rehearsal():
    spec = importlib.util.spec_from_file_location(
        "resonance_rebuild_disposable_rehearsal_t",
        HERE / "resonance_rebuild_disposable_rehearsal.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load_rehearsal()
CH = "482012f1-710e-4a25-994a-93821f5871aa"


def _passing_ver() -> dict:
    return {
        "before": {"sensitive_total": 176, "sensitive_negative": 154},
        "after": {"total": 481, "sensitive_total": 105, "sensitive_negative": 0,
                  "by_type": {}},
        "sensitive_keyed_to_positive_facts": 105,
        "dangling_or_null_refs": 0,
        "rows_missing_or_bad_resolution_state": 0,
        "arudha_rows": 67, "arudha_all_keyed_to_sign_facts": True,
        "arudha_invalid_sign_unavailable": 10,
        "yoga_rows": 4, "yoga_refs_not_live_fired": 0,
        "lord_rows": 51, "lord_states": {"resolved": 51},
        "afflicted_qualifier_rows": 6, "expected_afflicted_rows": 6,
        "writer_notes": {
            "sensitive_degree": {"negative_dropped_zero_rows": 735},
            "yoga_constituent": {"dropped_since_prior_build": ["yoga_demo_stopped"]}},
        "rerun_digest_equal": True,
        "rollback": {"refused_on_stale_snapshot": True,
                     "partition_untouched_after_refusal": True,
                     "restored_digest_equal": True,
                     "other_chart_untouched": True,
                     "rebuild_after_rollback_digest_equal": True},
    }


def test_passing_verification_is_accepted():
    assert R.verify_acceptance(_passing_ver()) == []


@pytest.mark.parametrize("mutate,needle", [
    (lambda v: v["after"].__setitem__("sensitive_negative", 1), "R-1"),
    (lambda v: v["after"].__setitem__("sensitive_total", 0), "R-1 control"),
    (lambda v: v.__setitem__("sensitive_keyed_to_positive_facts", 100), "not all keyed"),
    (lambda v: v["before"].__setitem__("sensitive_negative", 0), "fixture control"),
    (lambda v: v["after"].__setitem__("total", 0), "R-6 control"),
    (lambda v: v.__setitem__("dangling_or_null_refs", 2), "dangling"),
    (lambda v: v.__setitem__("rows_missing_or_bad_resolution_state", 1), "R-6"),
    (lambda v: v.__setitem__("arudha_rows", 0), "R-2"),
    (lambda v: v.__setitem__("arudha_all_keyed_to_sign_facts", False), "R-2"),
    (lambda v: v.__setitem__("arudha_invalid_sign_unavailable", 0), "R-2 control"),
    (lambda v: v.__setitem__("yoga_rows", 0), "R-3"),
    (lambda v: v.__setitem__("yoga_refs_not_live_fired", 1), "R-3"),
    (lambda v: v["writer_notes"]["yoga_constituent"].__setitem__("dropped_since_prior_build", []), "R-3 drift"),
    (lambda v: v.__setitem__("lord_states", {"resolved": 50, "unavailable": 1}), "R-4"),
    (lambda v: v.__setitem__("lord_rows", 0), "R-4"),
    (lambda v: v.__setitem__("afflicted_qualifier_rows", 5), "R-5"),
    (lambda v: v.__setitem__("expected_afflicted_rows", 0), "R-5"),
    (lambda v: v["writer_notes"]["sensitive_degree"].__setitem__("negative_dropped_zero_rows", 0), "notes"),
    (lambda v: v.__setitem__("rerun_digest_equal", False), "idempotency"),
    (lambda v: v["rollback"].__setitem__("refused_on_stale_snapshot", False), "refuse"),
    (lambda v: v["rollback"].__setitem__("partition_untouched_after_refusal", False), "refuse"),
    (lambda v: v["rollback"].__setitem__("restored_digest_equal", False), "exact preimage"),
    (lambda v: v["rollback"].__setitem__("other_chart_untouched", False), "foreign chart"),
    (lambda v: v["rollback"].__setitem__("rebuild_after_rollback_digest_equal", False), "rebuild after rollback"),
])
def test_each_violated_property_fails(mutate, needle):
    v = copy.deepcopy(_passing_ver())
    mutate(v)
    failures = R.verify_acceptance(v)
    assert failures and any(needle in f for f in failures), (needle, failures)


def test_empty_output_cannot_pass():
    v = _passing_ver()
    v["after"] = {"total": 0, "sensitive_total": 0, "sensitive_negative": 0, "by_type": {}}
    v.update(sensitive_keyed_to_positive_facts=0, arudha_rows=0, yoga_rows=0,
             lord_rows=0, lord_states={})
    failures = R.verify_acceptance(v)
    assert len(failures) >= 5


def test_expected_afflicted_rows_from_signature_models():
    assert R.expected_afflicted_lord_rows() == 6  # 10L, 7L, 2L/11L ×2


def test_main_returns_failure_when_acceptance_fails(monkeypatch, capsys):
    """The run must EXIT NON-ZERO on a violated invariant (the pre-rework
    script printed the block and returned 0)."""
    import types
    fake_report = {"acceptance": {"passed": False, "failures": ["R-1: 3 remain"]}}
    monkeypatch.setattr(R, "establish_disposable_database", lambda dsn, p: ("dsn", "rehearsal_a54_20260930000000_abcdef"))
    monkeypatch.setattr(R, "drop_disposable_database", lambda dsn, n: None)

    class _Conn:
        def cursor(self):
            raise RuntimeError("stop before any DDL")
    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(
        connect=lambda *a, **k: _Conn(), Error=Exception))
    with pytest.raises(RuntimeError, match="stop before any DDL"):
        R.main(["--maintenance-dsn", "postgresql://u:p@127.0.0.1:1/postgres"])
    # and the verify path itself
    assert R.verify_acceptance(copy.deepcopy(_passing_ver())) == []


def test_disposable_identity_refuses_wrong_or_non_empty_database():
    class _C:
        def __init__(self, db, addr, tables):
            self._r = [(db,), (addr,), (tables,)]

        def execute(self, sql):
            r = self._r.pop(0)

            class _X:
                def fetchone(self_inner):
                    return r
            return _X()
    name = "rehearsal_a54_20260930000000_abcdef"
    ok = R.assert_disposable_identity(_C(name, "127.0.0.1", 0), name)
    assert ok["database"] == name
    with pytest.raises(SystemExit, match="not the created database"):
        R.assert_disposable_identity(_C("madhav", "127.0.0.1", 0), name)
    with pytest.raises(SystemExit, match="not fresh"):
        R.assert_disposable_identity(_C(name, "127.0.0.1", 3), name)
    # a containerised server reports its container address — diagnostic only
    assert R.assert_disposable_identity(_C(name, "172.17.0.5", 0), name)["server_addr_diagnostic"] == "172.17.0.5"
    with pytest.raises(SystemExit, match="not loopback"):
        R.establish_disposable_database("postgresql://u:p@db.example.com:5432/postgres", "x")


# ── the SQL module ──────────────────────────────────────────────────────────

def test_snapshot_is_uniquely_named_and_never_if_not_exists():
    t = B.snapshot_table_name(CH, "20260930120000")
    assert t == "gochara_resonance_map_snap_482012f1_20260930120000"
    sql = B.create_snapshot_sql(t, CH)
    assert sql.startswith("CREATE TABLE gochara_resonance_map_snap_")
    assert "IF NOT EXISTS" not in sql
    with pytest.raises(ValueError):
        B.snapshot_table_name(CH, "bad")
    with pytest.raises(ValueError):
        B.create_snapshot_sql("gochara_resonance_map_pre_r1r6_backup", CH)
    with pytest.raises(ValueError):
        B.rollback_sql(t, "not-a-uuid", 1, "0" * 32)
    with pytest.raises(ValueError):
        B.rollback_sql(t, CH, 1, "DROP TABLE x")


def test_rollback_block_refuses_before_deleting_and_verifies_after():
    t = B.snapshot_table_name(CH, "20260930120000")
    sql = B.rollback_sql(t, CH, 177, "a" * 32)
    body = sql.split("DELETE FROM gochara_resonance_map")[0]
    assert "ROLLBACK REFUSED: snapshot table" in body
    assert "carries % rows of another chart" in body
    assert "stale or incomplete" in body
    assert "ROLLBACK FAILED VERIFICATION" in sql.split("INSERT INTO gochara_resonance_map")[1]
    assert sql.strip().startswith("BEGIN;") and sql.strip().endswith("COMMIT;")


def test_reference_checks_use_not_exists_not_not_in():
    assert "NOT EXISTS" in B.dangling_fact_refs_sql(CH)
    assert "NOT IN (" not in B.dangling_fact_refs_sql(CH).replace(
        "IS NULL", "").split("target_ref !~")[0]
    assert "f.fact_value_text IS NULL" in B.negative_sensitive_targets_sql(CH)


def test_runbook_carries_the_module_statements_verbatim():
    """Drift guard: the production runbook's SQL IS the module's rendering
    (example stamp 20260930000000, count 177, digest 32 zeros)."""
    text = (HERE / "resonance_rebuild_R1_R6_runbook.md").read_text()
    t = B.snapshot_table_name(CH, "20260930000000")
    for block in (B.create_snapshot_sql(t, CH),
                  B.partition_digest_sql("gochara_resonance_map", CH),
                  B.partition_digest_sql(t, CH),
                  B.negative_sensitive_targets_sql(CH),
                  B.dangling_fact_refs_sql(CH),
                  B.rollback_sql(t, CH, 177, "0" * 32)):
        assert block in text, block[:80]
    assert "IF NOT EXISTS gochara_resonance_map_pre_r1r6_backup" not in text
    assert "negative_dropped_zero_rows = 154" not in text
    assert "NOT IN (SELECT" not in text
    assert "MUST BE > 0" in text  # positive controls present

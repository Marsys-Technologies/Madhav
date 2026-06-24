"""
test_concordance_writer.py — Tests for brahmagyan.mimamsa.concordance_writer
=============================================================================

Stream E (postdeploy-e-multi-school) — Session e5

Tests:
  1.  ConcordanceClass.AYANAMSHA_DEPENDENT exists
  2.  ConcordanceClass.all_values() includes 'ayanamsha_dependent'
  3.  ConcordanceClass.all_values() includes all 5 expected values
  4.  ConcordanceClass.from_ws3_pattern('AGREE') → AGREE
  5.  ConcordanceClass.from_ws3_pattern('ORTHOGONAL') → ORTHOGONAL
  6.  ConcordanceClass.from_ws3_pattern('SYSTEM-DEFINING') → ORTHOGONAL
  7.  ConcordanceFlagRecord.to_db_row() returns tuple with 10 elements
  8.  ConcordanceFlagRecord.to_db_row() first element = topic_id
  9.  ConcordanceFlagRecord.to_db_row() third element = 'ayanamsha_dependent'
  10. C3_AYANAMSHA_DEPENDENT_RECORDS has exactly 3 entries
  11. All C3 records have concordance_class = AYANAMSHA_DEPENDENT
  12. All C3 records have ayanamsha_a = 'lahiri', ayanamsha_b = 'kp'
  13. All C3 records have non-empty description
  14. All C3 records have non-empty rule_refs list
  15. write_concordance_flags dry_run returns count without DB calls
  16. write_concordance_flags with mocked DB writes correct SQL
  17. seed_c3_resolution dry_run returns 3 (one per C3 record)
  18. TC.C3.SIGN_BOUNDARY topic_id is present in C3 records
  19. TC.C3.NAKSHATRA_BOUNDARY topic_id is present in C3 records
  20. TC.C3.DASHA_LORD topic_id is present in C3 records
"""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch


def _mod():
    from brahmagyan.mimamsa import concordance_writer
    return concordance_writer


# ── ConcordanceClass ──────────────────────────────────────────────────────────

class TestConcordanceClass:
    def test_ayanamsha_dependent_exists(self):
        mod = _mod()
        assert hasattr(mod.ConcordanceClass, "AYANAMSHA_DEPENDENT")

    def test_all_values_includes_ayanamsha_dependent(self):
        mod = _mod()
        assert "ayanamsha_dependent" in mod.ConcordanceClass.all_values()

    def test_all_values_has_five_entries(self):
        mod = _mod()
        vals = mod.ConcordanceClass.all_values()
        assert len(vals) == 5

    def test_all_values_contains_expected(self):
        mod = _mod()
        expected = {"agree", "disagree", "qualify", "orthogonal", "ayanamsha_dependent"}
        assert set(mod.ConcordanceClass.all_values()) == expected

    def test_from_ws3_agree(self):
        mod = _mod()
        result = mod.ConcordanceClass.from_ws3_pattern("AGREE")
        assert result == mod.ConcordanceClass.AGREE

    def test_from_ws3_orthogonal(self):
        mod = _mod()
        result = mod.ConcordanceClass.from_ws3_pattern("ORTHOGONAL")
        assert result == mod.ConcordanceClass.ORTHOGONAL

    def test_from_ws3_system_defining_maps_to_orthogonal(self):
        """SYSTEM-DEFINING (C3 house cusp convention) → ORTHOGONAL."""
        mod = _mod()
        result = mod.ConcordanceClass.from_ws3_pattern("SYSTEM-DEFINING")
        assert result == mod.ConcordanceClass.ORTHOGONAL

    def test_ayanamsha_dependent_string_value(self):
        mod = _mod()
        assert mod.ConcordanceClass.AYANAMSHA_DEPENDENT.value == "ayanamsha_dependent"


# ── ConcordanceFlagRecord ─────────────────────────────────────────────────────

class TestConcordanceFlagRecord:
    def _make_record(self, **kwargs):
        mod = _mod()
        defaults = dict(
            topic_id="TC.TEST.001",
            topic="Test topic",
            concordance_class=mod.ConcordanceClass.AYANAMSHA_DEPENDENT,
            description="Test description",
            source_citation="test-source",
        )
        defaults.update(kwargs)
        return mod.ConcordanceFlagRecord(**defaults)

    def test_to_db_row_returns_10_tuple(self):
        rec = self._make_record()
        row = rec.to_db_row()
        assert len(row) == 10

    def test_to_db_row_first_element_topic_id(self):
        rec = self._make_record()
        row = rec.to_db_row()
        assert row[0] == "TC.TEST.001"

    def test_to_db_row_third_element_concordance_class_value(self):
        rec = self._make_record()
        row = rec.to_db_row()
        assert row[2] == "ayanamsha_dependent"

    def test_to_db_row_rule_refs_serialized_as_json(self):
        rec = self._make_record(rule_refs=["BPHS.1.1.1", "KP.1.ch1.1"])
        row = rec.to_db_row()
        refs = json.loads(row[6])
        assert "BPHS.1.1.1" in refs

    def test_default_ayanamshas(self):
        rec = self._make_record()
        assert rec.ayanamsha_a == "lahiri"
        assert rec.ayanamsha_b == "kp"


# ── C3_AYANAMSHA_DEPENDENT_RECORDS ───────────────────────────────────────────

class TestC3Records:
    def test_has_exactly_three_records(self):
        mod = _mod()
        assert len(mod.C3_AYANAMSHA_DEPENDENT_RECORDS) == 3

    def test_all_have_ayanamsha_dependent_class(self):
        mod = _mod()
        for rec in mod.C3_AYANAMSHA_DEPENDENT_RECORDS:
            assert rec.concordance_class == mod.ConcordanceClass.AYANAMSHA_DEPENDENT

    def test_all_lahiri_kp_pair(self):
        mod = _mod()
        for rec in mod.C3_AYANAMSHA_DEPENDENT_RECORDS:
            assert rec.ayanamsha_a == "lahiri"
            assert rec.ayanamsha_b == "kp"

    def test_all_have_non_empty_description(self):
        mod = _mod()
        for rec in mod.C3_AYANAMSHA_DEPENDENT_RECORDS:
            assert rec.description and len(rec.description) > 20

    def test_all_have_rule_refs(self):
        mod = _mod()
        for rec in mod.C3_AYANAMSHA_DEPENDENT_RECORDS:
            assert isinstance(rec.rule_refs, list)
            assert len(rec.rule_refs) > 0

    def test_sign_boundary_present(self):
        mod = _mod()
        ids = [r.topic_id for r in mod.C3_AYANAMSHA_DEPENDENT_RECORDS]
        assert "TC.C3.SIGN_BOUNDARY" in ids

    def test_nakshatra_boundary_present(self):
        mod = _mod()
        ids = [r.topic_id for r in mod.C3_AYANAMSHA_DEPENDENT_RECORDS]
        assert "TC.C3.NAKSHATRA_BOUNDARY" in ids

    def test_dasha_lord_present(self):
        mod = _mod()
        ids = [r.topic_id for r in mod.C3_AYANAMSHA_DEPENDENT_RECORDS]
        assert "TC.C3.DASHA_LORD" in ids


# ── write_concordance_flags ───────────────────────────────────────────────────

class TestWriteConcordanceFlags:
    def test_dry_run_returns_count_no_db(self):
        """dry_run should return count without any DB connection."""
        mod = _mod()
        records = [
            mod.ConcordanceFlagRecord(
                topic_id=f"TC.TEST.{i:03d}",
                topic=f"Test {i}",
                concordance_class=mod.ConcordanceClass.AGREE,
                description="desc",
                source_citation="test",
            )
            for i in range(3)
        ]
        result = mod.write_concordance_flags(records, dry_run=True)
        assert result == 3

    def test_empty_records_returns_zero(self):
        mod = _mod()
        result = mod.write_concordance_flags([], dry_run=True)
        assert result == 0

    def test_writes_correct_sql_with_mock(self):
        """Verify the INSERT SQL is called for each record."""
        mod = _mod()
        mock_conn_ctx = MagicMock()
        mock_conn = MagicMock()
        mock_conn_ctx.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn_ctx.__exit__ = MagicMock(return_value=False)

        record = mod.ConcordanceFlagRecord(
            topic_id="TC.TEST.WRITE",
            topic="Write test",
            concordance_class=mod.ConcordanceClass.AYANAMSHA_DEPENDENT,
            description="write test description",
            source_citation="test-citation",
        )

        with patch.object(mod, "_conn", return_value=mock_conn_ctx):
            result = mod.write_concordance_flags([record])

        assert result == 1
        assert mock_conn.execute.call_count == 1
        assert mock_conn.commit.call_count == 1

        # Verify the INSERT SQL was called with the record's topic_id
        call_args = mock_conn.execute.call_args
        assert "TC.TEST.WRITE" in call_args[0][1]


# ── seed_c3_resolution ────────────────────────────────────────────────────────

class TestSeedC3Resolution:
    def test_dry_run_returns_three(self):
        """seed_c3_resolution dry_run should return 3 (one per C3 record)."""
        mod = _mod()
        result = mod.seed_c3_resolution(dry_run=True)
        assert result == 3

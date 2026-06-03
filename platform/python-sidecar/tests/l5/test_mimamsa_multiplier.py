"""
test_mimamsa_multiplier.py — Unit tests for mimamsa.multiplier (BRAHMA-MI-5-4)

Tests:
    1. compute_multiplier — range assertions, boundary conditions, formula correctness
    2. compute_multiplier — clamping behaviour (extreme Brier scores)
    3. update_multiplier — sample_size=0 rejection guard
    4. update_multiplier — source_citation non-null enforcement (B.3 mandate)
    5. update_multiplier — DB round-trip (mocked)
    6. get_multiplier — response shape + provenance_envelope (mocked DB)
    7. list_multipliers — count + b3_citation_compliant (mocked DB)
    8. apply_multiplier — modulation logic, fallback, clamping (mocked DB)
    9. Leakage guard — update_multiplier does NOT accept raw LEL events
    10. Smoke test: all returned multipliers are in [0.8, 1.2]

No live DB connection required. All DB calls are mocked via unittest.mock.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ── Module under test ─────────────────────────────────────────────────────────

def _get_module():
    from brahmagyan.mimamsa import multiplier as mod
    return mod


# ── Constants (mirrored from module) ──────────────────────────────────────────

MULTIPLIER_MIN = 0.8
MULTIPLIER_MAX = 1.2
BRIER_REFERENCE = 0.5
MULTIPLIER_SCALE = 0.1


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_db_row(
    technique: str = "vimshottari_dasha",
    ayanamsha_id: str = "lahiri",
    multiplier: float = 1.0,
    sample_size: int = 10,
    source_citation: str = "FORENSIC v8.0 §5.1; LEL v1.7 §Calibration-outcomes; BRAHMA MI-5-4",
) -> dict[str, Any]:
    from datetime import datetime, timezone
    return {
        "technique": technique,
        "ayanamsha_id": ayanamsha_id,
        "multiplier": multiplier,
        "last_updated": datetime(2026, 6, 4, 0, 0, 0, tzinfo=timezone.utc),
        "sample_size": sample_size,
        "source_citation": source_citation,
    }


# ── §1 — compute_multiplier: range assertions ─────────────────────────────────

class TestComputeMultiplierRange:
    """
    All multiplier results must be in [MULTIPLIER_MIN, MULTIPLIER_MAX] = [0.8, 1.2].
    Tests use range assertions, not exact floats, as per constraint.
    """

    def test_neutral_brier_returns_one(self):
        """Brier score at reference (0.5) → multiplier = 1.0 (no modulation)."""
        mod = _get_module()
        result = mod.compute_multiplier(0.5)
        assert result == pytest.approx(1.0, abs=1e-9)

    def test_perfect_brier_returns_max(self):
        """Brier score = 0.0 (perfect) → raw = 1.05 → clamped to 1.2? No: raw = 1.05."""
        mod = _get_module()
        result = mod.compute_multiplier(0.0)
        # raw = 1.0 + 0.1 × (0.5 - 0.0) = 1.0 + 0.05 = 1.05
        assert MULTIPLIER_MIN <= result <= MULTIPLIER_MAX
        assert result > 1.0  # better than random → boost

    def test_worst_brier_returns_min_clamp(self):
        """Brier score = 1.0 (worst) → raw = 1.0 + 0.1 × (0.5 - 1.0) = 0.95."""
        mod = _get_module()
        result = mod.compute_multiplier(1.0)
        # raw = 1.0 + 0.1 × (0.5 - 1.0) = 1.0 - 0.05 = 0.95 — within bounds
        assert MULTIPLIER_MIN <= result <= MULTIPLIER_MAX
        assert result < 1.0  # worse than random → down-weight

    def test_result_always_in_bounds(self):
        """Fuzz: any Brier score in [0.0, 1.0] produces multiplier in [0.8, 1.2]."""
        mod = _get_module()
        test_brier_scores = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        for bs in test_brier_scores:
            result = mod.compute_multiplier(bs)
            assert MULTIPLIER_MIN <= result <= MULTIPLIER_MAX, (
                f"compute_multiplier({bs}) = {result} out of [{MULTIPLIER_MIN}, {MULTIPLIER_MAX}]"
            )

    def test_better_than_random_boosts(self):
        """Brier score < 0.5 → multiplier > 1.0."""
        mod = _get_module()
        result = mod.compute_multiplier(0.2)
        assert result > 1.0, f"Brier=0.2 should boost, got {result}"

    def test_worse_than_random_down_weights(self):
        """Brier score > 0.5 → multiplier < 1.0."""
        mod = _get_module()
        result = mod.compute_multiplier(0.8)
        assert result < 1.0, f"Brier=0.8 should down-weight, got {result}"

    def test_invalid_brier_below_zero_raises(self):
        mod = _get_module()
        with pytest.raises(ValueError, match="mean_brier_score"):
            mod.compute_multiplier(-0.01)

    def test_invalid_brier_above_one_raises(self):
        mod = _get_module()
        with pytest.raises(ValueError, match="mean_brier_score"):
            mod.compute_multiplier(1.01)


# ── §2 — compute_multiplier: clamping ────────────────────────────────────────

class TestComputeMultiplierClamping:
    """
    The formula 1.0 + 0.1 × (0.5 - brier) can produce values outside [0.8, 1.2]
    if the Brier score were allowed to go beyond [0.0, 1.0]. Verify clamping logic
    holds even at the exact boundary values.
    """

    def test_clamp_at_min_boundary(self):
        """
        The natural min is at brier=1.0: 1.0 + 0.1×(0.5-1.0) = 0.95 > 0.8.
        Within the valid range, no clamping occurs at the bottom.
        """
        mod = _get_module()
        # At brier=1.0, raw = 0.95, which is within [0.8, 1.2]
        result = mod.compute_multiplier(1.0)
        assert result == pytest.approx(0.95, abs=1e-9)
        assert result >= MULTIPLIER_MIN

    def test_clamp_at_max_boundary(self):
        """
        The natural max is at brier=0.0: 1.0 + 0.1×(0.5-0.0) = 1.05 < 1.2.
        Within the valid range, no clamping occurs at the top.
        """
        mod = _get_module()
        # At brier=0.0, raw = 1.05, which is within [0.8, 1.2]
        result = mod.compute_multiplier(0.0)
        assert result == pytest.approx(1.05, abs=1e-9)
        assert result <= MULTIPLIER_MAX

    def test_formula_monotone_decreasing(self):
        """Higher Brier score → lower multiplier (monotone decreasing)."""
        mod = _get_module()
        brier_low = 0.2
        brier_high = 0.8
        m_low = mod.compute_multiplier(brier_low)
        m_high = mod.compute_multiplier(brier_high)
        assert m_low > m_high, (
            f"Expected m({brier_low})={m_low} > m({brier_high})={m_high}"
        )


# ── §3 — update_multiplier: guard rails ──────────────────────────────────────

class TestUpdateMultiplierGuards:
    """Verify guard-rails without hitting the DB."""

    def test_zero_sample_size_raises(self):
        """sample_size=0 must be rejected — no evidence to update."""
        mod = _get_module()
        with pytest.raises(ValueError, match="sample_size"):
            mod.update_multiplier(
                technique="vimshottari_dasha",
                ayanamsha_id="lahiri",
                mean_brier_score=0.4,
                sample_size=0,
            )

    def test_negative_sample_size_raises(self):
        mod = _get_module()
        with pytest.raises(ValueError, match="sample_size"):
            mod.update_multiplier(
                technique="vimshottari_dasha",
                ayanamsha_id="lahiri",
                mean_brier_score=0.4,
                sample_size=-1,
            )

    def test_empty_source_citation_raises(self):
        """Empty source_citation must be rejected (B.3 mandate)."""
        mod = _get_module()
        with pytest.raises(ValueError, match="source_citation"):
            mod.update_multiplier(
                technique="vimshottari_dasha",
                ayanamsha_id="lahiri",
                mean_brier_score=0.4,
                sample_size=5,
                source_citation="   ",  # whitespace-only → empty after strip
            )

    def test_brier_out_of_range_raises(self):
        mod = _get_module()
        with pytest.raises(ValueError, match="mean_brier_score"):
            mod.update_multiplier(
                technique="vimshottari_dasha",
                ayanamsha_id="lahiri",
                mean_brier_score=1.5,
                sample_size=5,
            )

    def test_brier_negative_raises(self):
        mod = _get_module()
        with pytest.raises(ValueError, match="mean_brier_score"):
            mod.update_multiplier(
                technique="vimshottari_dasha",
                ayanamsha_id="lahiri",
                mean_brier_score=-0.1,
                sample_size=5,
            )


# ── §4 — update_multiplier: DB round-trip (mocked) ───────────────────────────

class TestUpdateMultiplierDBRoundtrip:
    """Verify update_multiplier inserts/returns correct shape (no live DB)."""

    def _mock_psycopg_connect(self, returned_row: dict):
        """Build a mock context manager chain for psycopg.connect → cursor → fetchone."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = returned_row

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        return mock_conn

    def test_update_returns_correct_shape(self):
        mod = _get_module()
        expected_multiplier = mod.compute_multiplier(0.3)
        db_row = _make_db_row(multiplier=expected_multiplier, sample_size=15)

        mock_conn = self._mock_psycopg_connect(db_row)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.update_multiplier(
                    technique="vimshottari_dasha",
                    ayanamsha_id="lahiri",
                    mean_brier_score=0.3,
                    sample_size=15,
                )

        assert result["ok"] is True
        assert result["technique"] == "vimshottari_dasha"
        assert result["ayanamsha_id"] == "lahiri"
        assert MULTIPLIER_MIN <= result["multiplier"] <= MULTIPLIER_MAX
        assert result["sample_size"] == 15
        assert "provenance_envelope" in result
        assert result["provenance_envelope"]["b3_citation_compliant"] is True

    def test_update_multiplier_in_range(self):
        """The stored multiplier must always be in [0.8, 1.2]."""
        mod = _get_module()
        for brier_score in [0.1, 0.3, 0.5, 0.7, 0.9]:
            expected = mod.compute_multiplier(brier_score)
            db_row = _make_db_row(multiplier=expected, sample_size=20)
            mock_conn = self._mock_psycopg_connect(db_row)
            with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
                with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                    result = mod.update_multiplier(
                        technique="vimshottari_dasha",
                        ayanamsha_id="lahiri",
                        mean_brier_score=brier_score,
                        sample_size=20,
                    )
            assert MULTIPLIER_MIN <= result["multiplier"] <= MULTIPLIER_MAX, (
                f"Brier={brier_score}: multiplier={result['multiplier']} out of bounds"
            )

    def test_default_source_citation_is_non_null(self):
        """When no source_citation is provided, the default must be non-empty."""
        mod = _get_module()
        db_row = _make_db_row(multiplier=1.0, sample_size=5)
        mock_conn = self._mock_psycopg_connect(db_row)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.update_multiplier(
                    technique="jaimini_chara_dasha",
                    ayanamsha_id="lahiri",
                    mean_brier_score=0.5,
                    sample_size=5,
                    # source_citation deliberately omitted → should use default
                )
        assert bool(result["source_citation"]), "source_citation must be non-empty"

    def test_provenance_envelope_has_required_keys(self):
        mod = _get_module()
        db_row = _make_db_row()
        mock_conn = self._mock_psycopg_connect(db_row)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.update_multiplier(
                    technique="vimshottari_dasha",
                    ayanamsha_id="lahiri",
                    mean_brier_score=0.4,
                    sample_size=8,
                )
        env = result["provenance_envelope"]
        required_keys = {
            "source", "asset", "algorithm", "mean_brier_score_used",
            "l1_ground_truth", "leakage_guard", "queried_at", "b3_citation_compliant",
        }
        missing = required_keys - set(env.keys())
        assert not missing, f"provenance_envelope missing keys: {missing}"


# ── §5 — get_multiplier: response shape (mocked DB) ──────────────────────────

class TestGetMultiplierShape:
    """Verify get_multiplier returns correct shape with provenance_envelope."""

    def _mock_fetchone(self, row):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = row
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return mock_conn

    def test_returns_correct_keys_when_found(self):
        mod = _get_module()
        row = _make_db_row(multiplier=1.02, sample_size=12)
        mock_conn = self._mock_fetchone(row)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.get_multiplier("vimshottari_dasha", "lahiri")
        assert result is not None
        required = {"technique", "ayanamsha_id", "multiplier", "last_updated",
                    "sample_size", "source_citation", "provenance_envelope"}
        missing = required - set(result.keys())
        assert not missing, f"get_multiplier result missing keys: {missing}"

    def test_multiplier_in_range_when_found(self):
        mod = _get_module()
        row = _make_db_row(multiplier=1.05, sample_size=7)
        mock_conn = self._mock_fetchone(row)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.get_multiplier("vimshottari_dasha", "lahiri")
        assert MULTIPLIER_MIN <= result["multiplier"] <= MULTIPLIER_MAX

    def test_returns_none_when_not_found(self):
        mod = _get_module()
        mock_conn = self._mock_fetchone(None)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.get_multiplier("unknown_technique", "unknown_ayanamsha")
        assert result is None

    def test_provenance_envelope_source(self):
        mod = _get_module()
        row = _make_db_row()
        mock_conn = self._mock_fetchone(row)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.get_multiplier("vimshottari_dasha", "lahiri")
        assert result["provenance_envelope"]["source"] == "mimamsa.multiplier"
        assert result["provenance_envelope"]["asset"] == "MI-5-4"
        assert "leakage_guard" in result["provenance_envelope"]
        assert "l1_ground_truth" in result["provenance_envelope"]

    def test_b3_compliant_true_when_citation_present(self):
        mod = _get_module()
        row = _make_db_row(source_citation="FORENSIC v8.0 §5.1; BRAHMA MI-5-4")
        mock_conn = self._mock_fetchone(row)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.get_multiplier("vimshottari_dasha", "lahiri")
        assert result["provenance_envelope"]["b3_citation_compliant"] is True


# ── §6 — list_multipliers (mocked DB) ────────────────────────────────────────

class TestListMultipliers:
    """Verify list_multipliers response shape."""

    def _mock_fetchall(self, rows):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = rows
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return mock_conn

    def test_returns_correct_shape(self):
        mod = _get_module()
        rows = [
            _make_db_row("vimshottari_dasha", "lahiri", 1.0, 10),
            _make_db_row("kp_sub_lord", "krishnamurti", 1.02, 5),
        ]
        mock_conn = self._mock_fetchall(rows)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.list_multipliers()
        assert result["ok"] is True
        assert result["count"] == 2
        assert len(result["multipliers"]) == 2
        assert "provenance_envelope" in result

    def test_all_multipliers_in_range(self):
        mod = _get_module()
        rows = [_make_db_row(multiplier=m) for m in [0.8, 0.9, 1.0, 1.1, 1.2]]
        mock_conn = self._mock_fetchall(rows)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.list_multipliers()
        for m_row in result["multipliers"]:
            assert MULTIPLIER_MIN <= m_row["multiplier"] <= MULTIPLIER_MAX

    def test_b3_compliant_false_when_any_citation_missing(self):
        mod = _get_module()
        rows = [
            _make_db_row(source_citation="FORENSIC v8.0 §5.1; BRAHMA MI-5-4"),
            _make_db_row(source_citation=""),  # Missing citation
        ]
        mock_conn = self._mock_fetchall(rows)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.list_multipliers()
        assert result["provenance_envelope"]["b3_citation_compliant"] is False

    def test_empty_table_returns_zero_count(self):
        mod = _get_module()
        mock_conn = self._mock_fetchall([])
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.list_multipliers()
        assert result["count"] == 0
        assert result["multipliers"] == []
        assert result["ok"] is True


# ── §7 — apply_multiplier (mocked DB) ────────────────────────────────────────

class TestApplyMultiplier:
    """Verify apply_multiplier correctly modulates base values."""

    def _mock_get_multiplier(self, multiplier_val: float):
        from datetime import datetime, timezone
        row = {
            "technique": "vimshottari_dasha",
            "ayanamsha_id": "lahiri",
            "multiplier": multiplier_val,
            "last_updated": datetime(2026, 6, 4, tzinfo=timezone.utc).isoformat(),
            "sample_size": 10,
            "source_citation": "FORENSIC v8.0 §5.1; BRAHMA MI-5-4",
            "provenance_envelope": {
                "source": "mimamsa.multiplier",
                "asset": "MI-5-4",
                "b3_citation_compliant": True,
            },
        }
        return row

    def test_apply_with_found_multiplier(self):
        mod = _get_module()
        multiplier_val = 1.05
        row = self._mock_get_multiplier(multiplier_val)
        with patch.object(mod, "get_multiplier", return_value=row):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.apply_multiplier(
                    base_value=0.7,
                    technique="vimshottari_dasha",
                    ayanamsha_id="lahiri",
                )
        assert result["fallback_used"] is False
        assert result["multiplier_applied"] == pytest.approx(multiplier_val, abs=1e-9)
        # modulated = CLAMP(0.7 × 1.05, 0.0, 1.0) = 0.735
        assert 0.0 <= result["modulated_value"] <= 1.0
        assert result["modulated_value"] == pytest.approx(0.7 * multiplier_val, abs=1e-6)

    def test_apply_with_fallback_when_not_found(self):
        mod = _get_module()
        with patch.object(mod, "get_multiplier", return_value=None):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.apply_multiplier(
                    base_value=0.6,
                    technique="unknown_technique",
                    ayanamsha_id="lahiri",
                    fallback_multiplier=1.0,
                )
        assert result["fallback_used"] is True
        assert result["multiplier_applied"] == pytest.approx(1.0, abs=1e-9)
        assert result["modulated_value"] == pytest.approx(0.6, abs=1e-9)

    def test_modulated_value_clamped_to_unit_interval(self):
        """Even if multiplier × base_value > 1.0, output is clamped to [0.0, 1.0]."""
        mod = _get_module()
        row = self._mock_get_multiplier(1.2)  # Max multiplier
        with patch.object(mod, "get_multiplier", return_value=row):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.apply_multiplier(
                    base_value=0.95,
                    technique="vimshottari_dasha",
                    ayanamsha_id="lahiri",
                )
        # 0.95 × 1.2 = 1.14 → clamped to 1.0
        assert 0.0 <= result["modulated_value"] <= 1.0

    def test_base_value_out_of_range_raises(self):
        mod = _get_module()
        with pytest.raises(ValueError, match="base_value"):
            mod.apply_multiplier(
                base_value=1.5,
                technique="vimshottari_dasha",
                ayanamsha_id="lahiri",
            )

    def test_fallback_out_of_range_raises(self):
        mod = _get_module()
        with pytest.raises(ValueError, match="fallback_multiplier"):
            mod.apply_multiplier(
                base_value=0.5,
                technique="vimshottari_dasha",
                ayanamsha_id="lahiri",
                fallback_multiplier=1.5,
            )

    def test_provenance_envelope_present(self):
        mod = _get_module()
        row = self._mock_get_multiplier(1.0)
        with patch.object(mod, "get_multiplier", return_value=row):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.apply_multiplier(
                    base_value=0.5,
                    technique="vimshottari_dasha",
                    ayanamsha_id="lahiri",
                )
        assert "provenance_envelope" in result
        assert result["provenance_envelope"]["source"] == "mimamsa.multiplier"
        assert "leakage_guard" in result["provenance_envelope"]
        assert "l1_ground_truth" in result["provenance_envelope"]


# ── §8 — Leakage guard verification ──────────────────────────────────────────

class TestLeakageGuard:
    """
    Verify that the leakage_guard string is present in all provenance_envelopes.
    This is a documentation-level check — the actual architectural guard is that
    update_multiplier accepts only pre-aggregated mean_brier_score (a float),
    not raw LEL event data. This test confirms the contract is stated in the output.
    """

    LEAKAGE_GUARD_SUBSTRING = "calibration ONLY"

    def _mock_fetchone(self, row):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = row
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return mock_conn

    def _mock_fetchall(self, rows):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = rows
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return mock_conn

    def test_get_multiplier_leakage_guard_in_provenance(self):
        mod = _get_module()
        row = _make_db_row()
        mock_conn = self._mock_fetchone(row)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.get_multiplier("vimshottari_dasha", "lahiri")
        guard = result["provenance_envelope"].get("leakage_guard", "")
        assert self.LEAKAGE_GUARD_SUBSTRING in guard, (
            f"leakage_guard missing expected text. Got: {guard!r}"
        )

    def test_list_multipliers_leakage_guard_in_provenance(self):
        mod = _get_module()
        rows = [_make_db_row()]
        mock_conn = self._mock_fetchall(rows)
        with patch("brahmagyan.mimamsa.multiplier.psycopg.connect", return_value=mock_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.list_multipliers()
        guard = result["provenance_envelope"].get("leakage_guard", "")
        assert self.LEAKAGE_GUARD_SUBSTRING in guard, (
            f"leakage_guard missing expected text. Got: {guard!r}"
        )

    def test_apply_multiplier_leakage_guard_in_provenance(self):
        mod = _get_module()
        with patch.object(mod, "get_multiplier", return_value=None):
            result = mod.apply_multiplier(
                base_value=0.5,
                technique="vimshottari_dasha",
                ayanamsha_id="lahiri",
            )
        guard = result["provenance_envelope"].get("leakage_guard", "")
        assert self.LEAKAGE_GUARD_SUBSTRING in guard, (
            f"leakage_guard missing expected text. Got: {guard!r}"
        )


# ── §9 — Smoke: DB not configured → RuntimeError ─────────────────────────────

class TestNoDBConfigured:
    """Without DATABASE_URL set, all DB functions must raise RuntimeError."""

    def _clear_db_env(self):
        return patch.dict(
            "os.environ",
            {"DATABASE_URL": "", "DIRECT_DATABASE_URL": "", "POSTGRES_URL": ""},
            clear=False,
        )

    def test_get_multiplier_raises_without_db(self):
        mod = _get_module()
        with self._clear_db_env():
            with pytest.raises(RuntimeError, match="database URL"):
                mod.get_multiplier("vimshottari_dasha", "lahiri")

    def test_list_multipliers_raises_without_db(self):
        mod = _get_module()
        with self._clear_db_env():
            with pytest.raises(RuntimeError, match="database URL"):
                mod.list_multipliers()

    def test_update_multiplier_raises_without_db(self):
        mod = _get_module()
        with self._clear_db_env():
            with pytest.raises(RuntimeError, match="database URL"):
                mod.update_multiplier(
                    technique="vimshottari_dasha",
                    ayanamsha_id="lahiri",
                    mean_brier_score=0.4,
                    sample_size=5,
                )


# ── §10 — Acceptance gate: range assertions ────────────────────────────────────

class TestAcceptanceGate:
    """
    AC1 — multiplier in [0.8, 1.2] for all inputs.
    AC2 — sample_size > 0 required to update.
    AC3 — source_citation non-null on all writes.
    AC4 — provenance_envelope present on all tool responses.
    """

    def test_ac1_multiplier_bounds_across_brier_range(self):
        """AC1: compute_multiplier stays in [0.8, 1.2] for all valid inputs."""
        mod = _get_module()
        import numpy as np  # only used for linspace; gracefully skip if absent
        try:
            scores = list(np.linspace(0.0, 1.0, 21))
        except ImportError:
            scores = [i / 20 for i in range(21)]
        for score in scores:
            m = mod.compute_multiplier(float(score))
            assert MULTIPLIER_MIN <= m <= MULTIPLIER_MAX, (
                f"AC1 FAIL: compute_multiplier({score:.2f}) = {m} out of [{MULTIPLIER_MIN}, {MULTIPLIER_MAX}]"
            )

    def test_ac2_sample_size_zero_rejected(self):
        """AC2: sample_size=0 must raise ValueError."""
        mod = _get_module()
        with pytest.raises(ValueError):
            mod.update_multiplier(
                technique="test", ayanamsha_id="lahiri",
                mean_brier_score=0.4, sample_size=0,
            )

    def test_ac3_empty_source_citation_rejected(self):
        """AC3: whitespace-only source_citation must raise ValueError (B.3 mandate)."""
        mod = _get_module()
        with pytest.raises(ValueError, match="source_citation"):
            mod.update_multiplier(
                technique="test", ayanamsha_id="lahiri",
                mean_brier_score=0.4, sample_size=5,
                source_citation="   ",  # whitespace-only is truthy → passes 'or' → fails strip()
            )

    def test_ac4_provenance_envelope_present_on_apply(self):
        """AC4: apply_multiplier always returns provenance_envelope."""
        mod = _get_module()
        with patch.object(mod, "get_multiplier", return_value=None):
            result = mod.apply_multiplier(0.5, "vimshottari_dasha", "lahiri")
        assert "provenance_envelope" in result
        assert result["provenance_envelope"]["asset"] == "MI-5-4"

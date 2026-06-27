"""
test_mi_adhilepa_b7.py — B7: Signal-Adjustment Type Mismatch fix

Bug: mi_adhilepa.py signal overlay loop keyed on sig["signal_id"] (UUID)
     to look up multipliers dict, but multipliers is keyed by family_id
     strings like "fam_yoga", "fam_graha_natal" — so mult was always None
     and mimamsa_signal_adjustment was always empty.

Fix: _signal_family_key(sig) derives the correct family key from
     signal_type_class / source_subsystem / source_l1_asset, then the loop
     uses that key to look up the multiplier.

Tests:
  1. test_signal_family_key_maps_correctly — _signal_family_key returns the
     expected fam_* key for each known signal attribute combination.
  2. test_signal_overlay_matches_family_key — the overlay loop emits rows
     when multipliers exist for the signal's family; pre-fix UUID lookup emits 0.
  3. test_signal_overlay_zero_rows_without_multiplier — overlay emits 0 rows
     when the family has no multiplier (correct behaviour, not the bug).
  4. test_signal_family_key_fallback — unknown signal class → fam_msr_signal.
  5. test_multiple_signal_families_overlay — two signals from different families
     each match their own multiplier and produce distinct overlay rows.

No live DB connection required. All DB calls are mocked.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, call, patch

import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

def _import_writer():
    from pipeline.orchestrator.writers.mi_adhilepa import (
        MiAdhilepaWriter,
        _signal_family_key,
    )
    return MiAdhilepaWriter, _signal_family_key


def _make_multiplier_row(target_ref: str, applied: float = 1.1) -> dict:
    return {
        "target_ref": target_ref,
        "target_kind": "family",
        "applied_multiplier": applied,
        "raw_multiplier": applied,
        "n_observations": 15,
        "kill_switch_state": "active",
    }


def _sig(signal_id: str, signal_type_class: str = "", source_subsystem: str = "",
         source_l1_asset: str = "") -> dict:
    return {
        "signal_id": signal_id,
        "signal_type_class": signal_type_class,
        "source_subsystem": source_subsystem,
        "source_l1_asset": source_l1_asset,
    }


# ── Test 1 — _signal_family_key mapping ───────────────────────────────────────

class TestSignalFamilyKeyMapping:
    """_signal_family_key returns the correct fam_* key for every signal type."""

    def test_yoga_class_returns_fam_yoga(self):
        _, fn = _import_writer()
        assert fn(_sig("uuid-1", signal_type_class="yoga")) == "fam_yoga"

    def test_yoga_subsystem_returns_fam_yoga(self):
        _, fn = _import_writer()
        assert fn(_sig("uuid-1", source_subsystem="yoga")) == "fam_yoga"

    def test_yoga_class_beats_subsystem(self):
        """signal_type_class="yoga" wins even if subsystem is something else."""
        _, fn = _import_writer()
        assert fn(_sig("uuid-1", signal_type_class="yoga", source_subsystem="structural")) == "fam_yoga"

    def test_dosha_class_returns_fam_graha_natal(self):
        """'dosha' is not a registered family; falls through to structural → fam_graha_natal
        if subsystem matches, or fam_msr_signal as fallback."""
        _, fn = _import_writer()
        # dosha with structural subsystem → fam_graha_natal via subsystem rule
        result = fn(_sig("uuid-1", signal_type_class="dosha", source_subsystem="structural"))
        assert result == "fam_graha_natal"

    def test_strength_ashtakavarga_returns_fam_ashtakavarga(self):
        _, fn = _import_writer()
        assert fn(_sig("u", source_subsystem="strength_ashtakavarga")) == "fam_ashtakavarga"

    def test_dasha_subsystem_returns_fam_dasha_period(self):
        _, fn = _import_writer()
        assert fn(_sig("u", source_subsystem="dasha")) == "fam_dasha_period"

    def test_varga_subsystem_returns_fam_divisional(self):
        _, fn = _import_writer()
        assert fn(_sig("u", source_subsystem="varga")) == "fam_divisional"

    def test_structural_subsystem_returns_fam_graha_natal(self):
        _, fn = _import_writer()
        assert fn(_sig("u", source_subsystem="structural")) == "fam_graha_natal"

    def test_nakshatra_subsystem_returns_fam_graha_natal(self):
        _, fn = _import_writer()
        assert fn(_sig("u", source_subsystem="nakshatra")) == "fam_graha_natal"

    def test_sensitive_subsystem_returns_fam_graha_natal(self):
        _, fn = _import_writer()
        assert fn(_sig("u", source_subsystem="sensitive")) == "fam_graha_natal"

    def test_panchanga_subsystem_returns_fam_graha_natal(self):
        _, fn = _import_writer()
        assert fn(_sig("u", source_subsystem="panchanga")) == "fam_graha_natal"

    def test_ga_positions_asset_returns_fam_graha_natal(self):
        _, fn = _import_writer()
        assert fn(_sig("u", source_l1_asset="ga_positions")) == "fam_graha_natal"

    def test_dignity_class_returns_fam_graha_natal(self):
        _, fn = _import_writer()
        assert fn(_sig("u", signal_type_class="dignity")) == "fam_graha_natal"

    def test_strength_class_returns_fam_graha_natal(self):
        _, fn = _import_writer()
        assert fn(_sig("u", signal_type_class="strength")) == "fam_graha_natal"

    def test_position_class_returns_fam_graha_natal(self):
        _, fn = _import_writer()
        assert fn(_sig("u", signal_type_class="position")) == "fam_graha_natal"

    def test_magnitude_class_returns_fam_graha_natal(self):
        _, fn = _import_writer()
        assert fn(_sig("u", signal_type_class="magnitude")) == "fam_graha_natal"

    def test_configuration_class_returns_fam_msr_signal(self):
        _, fn = _import_writer()
        assert fn(_sig("u", signal_type_class="configuration")) == "fam_msr_signal"

    def test_unknown_returns_fam_msr_signal_fallback(self):
        _, fn = _import_writer()
        assert fn(_sig("u")) == "fam_msr_signal"

    def test_empty_strings_return_fallback(self):
        _, fn = _import_writer()
        result = fn({"signal_id": "u", "signal_type_class": "", "source_subsystem": "",
                     "source_l1_asset": ""})
        assert result == "fam_msr_signal"

    def test_none_values_return_fallback(self):
        _, fn = _import_writer()
        result = fn({"signal_id": "u", "signal_type_class": None,
                     "source_subsystem": None, "source_l1_asset": None})
        assert result == "fam_msr_signal"


# ── Test 2 — overlay loop emits row when family key matches ───────────────────

class TestSignalOverlayMatchesFamilyKey:
    """
    B7 core: with family-key lookup, a yoga signal finds its multiplier
    and produces 1 overlay row.  With the old UUID lookup it would produce 0.
    """

    def _build_mock_ctx(self, signals: list[dict], multipliers: dict[str, dict],
                        chart_id: str = "482012f1-0000-0000-0000-000000000000") -> MagicMock:
        """Build a minimal orchestrator ctx mock."""
        ctx = MagicMock()
        ctx.config = {"chart_id": chart_id}
        ctx.dry_run = False

        # Cursor factory: returns signals on SELECT, no-ops on DELETE/INSERT
        cursor_calls: list[MagicMock] = []

        def _make_cursor(row_factory=None):
            cur = MagicMock()
            cur.__enter__ = MagicMock(return_value=cur)
            cur.__exit__ = MagicMock(return_value=False)

            def _execute(sql, params=None):
                sql_clean = sql.strip().upper()
                if sql_clean.startswith("SELECT") and "MIMAMSA_MULTIPLIERS" in sql_clean:
                    cur._result = list(multipliers.values())
                elif sql_clean.startswith("SELECT") and "BODHA_MSR_SIGNALS" in sql_clean:
                    cur._result = signals
                elif sql_clean.startswith("SELECT") and "INFORMATION_SCHEMA" in sql_clean:
                    # table_exists check → table always present
                    cur._result = [(1,)]
                elif sql_clean.startswith("SELECT") and "CHART_FACTS" in sql_clean:
                    cur._result = []
                elif sql_clean.startswith("SELECT") and "KALA_CONVERGENCE" in sql_clean:
                    cur._result = []
                elif sql_clean.startswith("SELECT") and "PHALA_ANCHORS" in sql_clean:
                    cur._result = []
                else:
                    cur._result = []

            cur.execute = MagicMock(side_effect=_execute)
            cur.executemany = MagicMock()

            def _fetchone():
                r = cur._result
                return r[0] if r else None

            def _fetchall():
                return cur._result or []

            cur.fetchone = MagicMock(side_effect=_fetchone)
            cur.fetchall = MagicMock(side_effect=_fetchall)
            cursor_calls.append(cur)
            return cur

        ctx.db_conn.cursor = MagicMock(side_effect=_make_cursor)
        ctx._cursor_calls = cursor_calls
        return ctx

    def _count_signal_adjustment_inserts(self, ctx: MagicMock) -> int:
        """Count total rows passed to executemany for mimamsa_signal_adjustment."""
        total = 0
        for cur in ctx._cursor_calls:
            for em_call in cur.executemany.call_args_list:
                sql_arg = em_call.args[0] if em_call.args else ""
                if "mimamsa_signal_adjustment" in sql_arg.lower():
                    rows_arg = em_call.args[1] if len(em_call.args) > 1 else []
                    total += len(rows_arg)
        return total

    def test_yoga_signal_matches_fam_yoga_multiplier(self):
        """
        Fail-before scenario: UUID lookup always returns None → 0 rows.
        Pass-after:  family-key lookup finds fam_yoga → 1 row emitted.
        """
        _, _ = _import_writer()
        MiAdhilepaWriter, _ = _import_writer()

        signal_uuid = "8a4f2c1e-dead-beef-0000-000000000001"
        signals = [_sig(signal_uuid, signal_type_class="yoga")]
        multipliers = {"fam_yoga": _make_multiplier_row("fam_yoga", 1.15)}

        ctx = self._build_mock_ctx(signals, multipliers)
        writer = MiAdhilepaWriter()
        result = writer.run(ctx)

        count = self._count_signal_adjustment_inserts(ctx)
        assert count == 1, (
            f"Expected 1 signal overlay row (yoga → fam_yoga), got {count}. "
            f"WriterResult rows_inserted={result.rows_inserted}"
        )

    def test_pre_fix_uuid_lookup_would_produce_zero(self):
        """
        Demonstrate that the old bug (UUID as key) yields 0 rows.
        We simulate it directly by looking up a UUID in the multipliers dict.
        """
        _, _ = _import_writer()
        signal_uuid = "8a4f2c1e-dead-beef-0000-000000000001"
        multipliers = {"fam_yoga": _make_multiplier_row("fam_yoga", 1.15)}

        # Old (broken) code: mult = multipliers.get(str(signal_uuid))
        mult_old = multipliers.get(str(signal_uuid))
        assert mult_old is None, "UUID lookup should always return None (pre-fix behaviour)"

    def test_graha_natal_signal_matches_multiplier(self):
        """ga_positions signal → fam_graha_natal multiplier → row emitted."""
        MiAdhilepaWriter, _ = _import_writer()
        signal_uuid = "aaaa0001-0000-0000-0000-000000000001"
        signals = [_sig(signal_uuid, source_l1_asset="ga_positions")]
        multipliers = {"fam_graha_natal": _make_multiplier_row("fam_graha_natal", 1.05)}

        ctx = self._build_mock_ctx(signals, multipliers)
        writer = MiAdhilepaWriter()
        writer.run(ctx)

        count = self._count_signal_adjustment_inserts(ctx)
        assert count == 1

    def test_ashtakavarga_signal_matches_multiplier(self):
        MiAdhilepaWriter, _ = _import_writer()
        signal_uuid = "aaaa0002-0000-0000-0000-000000000001"
        signals = [_sig(signal_uuid, source_subsystem="strength_ashtakavarga")]
        multipliers = {"fam_ashtakavarga": _make_multiplier_row("fam_ashtakavarga", 0.95)}

        ctx = self._build_mock_ctx(signals, multipliers)
        writer = MiAdhilepaWriter()
        writer.run(ctx)

        count = self._count_signal_adjustment_inserts(ctx)
        assert count == 1

    def test_dasha_signal_matches_multiplier(self):
        MiAdhilepaWriter, _ = _import_writer()
        signal_uuid = "aaaa0003-0000-0000-0000-000000000001"
        signals = [_sig(signal_uuid, source_subsystem="dasha")]
        multipliers = {"fam_dasha_period": _make_multiplier_row("fam_dasha_period", 1.2)}

        ctx = self._build_mock_ctx(signals, multipliers)
        writer = MiAdhilepaWriter()
        writer.run(ctx)

        count = self._count_signal_adjustment_inserts(ctx)
        assert count == 1


# ── Test 3 — overlay emits 0 rows when no multiplier for the family ───────────

class TestSignalOverlayZeroRowsWithoutMultiplier:
    """Correct behaviour: a signal whose family has no multiplier produces 0 rows."""

    def test_yoga_signal_no_multiplier_emits_zero(self):
        MiAdhilepaWriter, _ = _import_writer()
        signals = [_sig("uuid-x", signal_type_class="yoga")]
        # No fam_yoga multiplier in the dict
        multipliers = {"fam_graha_natal": _make_multiplier_row("fam_graha_natal", 1.0)}

        from tests.l5.test_mi_adhilepa_b7 import TestSignalOverlayMatchesFamilyKey
        helper = TestSignalOverlayMatchesFamilyKey()
        ctx = helper._build_mock_ctx(signals, multipliers)
        MiAdhilepaWriter().run(ctx)
        count = helper._count_signal_adjustment_inserts(ctx)
        assert count == 0, f"No fam_yoga multiplier → expect 0 rows, got {count}"


# ── Test 4 — multiple families each match independently ───────────────────────

class TestMultipleSignalFamiliesOverlay:
    """Two signals from different families each produce one overlay row."""

    def test_two_families_produce_two_rows(self):
        MiAdhilepaWriter, _ = _import_writer()
        signals = [
            _sig("uuid-y1", signal_type_class="yoga"),
            _sig("uuid-g1", source_l1_asset="ga_positions"),
        ]
        multipliers = {
            "fam_yoga": _make_multiplier_row("fam_yoga", 1.1),
            "fam_graha_natal": _make_multiplier_row("fam_graha_natal", 1.05),
        }

        from tests.l5.test_mi_adhilepa_b7 import TestSignalOverlayMatchesFamilyKey
        helper = TestSignalOverlayMatchesFamilyKey()
        ctx = helper._build_mock_ctx(signals, multipliers)
        MiAdhilepaWriter().run(ctx)
        count = helper._count_signal_adjustment_inserts(ctx)
        assert count == 2, f"Two signals, two families → expect 2 rows, got {count}"

    def test_three_signals_same_family_produce_three_rows(self):
        """Multiple signals in the same family each get their own overlay row."""
        MiAdhilepaWriter, _ = _import_writer()
        signals = [
            _sig(f"uuid-y{i}", signal_type_class="yoga") for i in range(3)
        ]
        multipliers = {"fam_yoga": _make_multiplier_row("fam_yoga", 1.2)}

        from tests.l5.test_mi_adhilepa_b7 import TestSignalOverlayMatchesFamilyKey
        helper = TestSignalOverlayMatchesFamilyKey()
        ctx = helper._build_mock_ctx(signals, multipliers)
        MiAdhilepaWriter().run(ctx)
        count = helper._count_signal_adjustment_inserts(ctx)
        assert count == 3, f"Three yoga signals → expect 3 rows, got {count}"


# ── IMPORTANT-1: fam_transit routing for tajaka / sade_sati ──────────────────

class TestTransitFamilyRouting:
    """tajaka and sade_sati subsystems must route to fam_transit, not fam_msr_signal."""

    def test_tajaka_maps_to_fam_transit(self):
        _, fn = _import_writer()
        assert fn(_sig("uuid-t1", source_subsystem="tajaka")) == "fam_transit"

    def test_sade_sati_maps_to_fam_transit(self):
        _, fn = _import_writer()
        assert fn(_sig("uuid-t2", source_subsystem="sade_sati")) == "fam_transit"


# ── IMPORTANT-2: _load_multipliers filters by target_kind='family' ────────────

class TestLoadMultipliersFiltersByFamilyKind:
    """
    _load_multipliers must only return rows with target_kind='family'.
    Mixed-kind rows with the same target_ref must not silently overwrite
    the family row via the dict comprehension.
    """

    def test_load_multipliers_filters_by_family_kind(self):
        """
        Mock DB returns rows with target_kind in ('signal', 'family', 'edge').
        Only the 'family' row must appear in the returned dict.
        """
        from pipeline.orchestrator.writers.mi_adhilepa import _load_multipliers

        # Build a mock connection whose cursor returns mixed-kind rows
        family_row = {
            "target_ref": "fam_yoga",
            "target_kind": "family",
            "applied_multiplier": 1.1,
            "raw_multiplier": 1.1,
            "n_observations": 10,
            "kill_switch_state": "active",
        }
        signal_row = {
            "target_ref": "fam_yoga",   # same target_ref, different kind
            "target_kind": "signal",
            "applied_multiplier": 0.5,
            "raw_multiplier": 0.5,
            "n_observations": 2,
            "kill_switch_state": "active",
        }
        edge_row = {
            "target_ref": "fam_graha_natal",
            "target_kind": "edge",
            "applied_multiplier": 0.8,
            "raw_multiplier": 0.8,
            "n_observations": 5,
            "kill_switch_state": "active",
        }

        # The SQL now carries AND target_kind = 'family', so the DB should only
        # return family rows.  We verify that the query sent contains the filter.
        captured_sql = []

        def _make_cursor(row_factory=None):
            cur = MagicMock()
            cur.__enter__ = MagicMock(return_value=cur)
            cur.__exit__ = MagicMock(return_value=False)

            def _execute(sql, params=None):
                captured_sql.append(sql)
                # Simulate DB honouring the AND target_kind='family' filter:
                # only return the family row
                cur._result = [family_row]

            cur.execute = MagicMock(side_effect=_execute)
            cur.fetchall = MagicMock(side_effect=lambda: cur._result)
            return cur

        conn = MagicMock()
        conn.cursor = MagicMock(side_effect=_make_cursor)

        result = _load_multipliers(conn, "482012f1-0000-0000-0000-000000000000")

        # 1. The emitted SQL must contain the target_kind filter
        assert len(captured_sql) == 1
        assert "target_kind = 'family'" in captured_sql[0], (
            f"Expected AND target_kind = 'family' in query, got: {captured_sql[0]}"
        )

        # 2. Result dict contains only the family row
        assert "fam_yoga" in result
        assert result["fam_yoga"]["target_kind"] == "family"
        assert float(result["fam_yoga"]["applied_multiplier"]) == 1.1

        # 3. edge_row target_ref absent (DB filtered it; our mock confirms intent)
        assert "fam_graha_natal" not in result

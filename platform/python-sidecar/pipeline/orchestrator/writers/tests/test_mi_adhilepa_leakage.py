"""
Tests for the mi_adhilepa leakage_status fix (SIDDHANTA Phase 2).

Root cause: mi_adhilepa._overlay_row() sets leakage = None (the correct §N.7
honesty fix — "a verification flag must have a real detector behind it, or be
null"). But mimamsa_signal_adjustment.leakage_status is defined as text NOT NULL
(migration 350), so the honest null is forbidden by a schema encoding the
dishonest assumption ("clean" was always written, but no leakage detector exists).

Three-part fix:
  Part (a): Migration 547 — DROP NOT NULL, backfill NULLs/'clean' → 'not_assessed',
            restore NOT NULL with DEFAULT 'not_assessed'.
  Part (b): mi_adhilepa._overlay_row() emits 'not_assessed' instead of None.
  Part (c): mi_gunanaka's calibration-evidence filter stops requiring 'clean'
            (which excluded everything after the fix) and instead only excludes
            rows explicitly marked 'leaked'.

§N.7-4: a verification flag must have a real detector behind it, or be null.
§N.8: a filter that excludes everything because no detector has run is not a
      safety mechanism — it is a silent data destroyer.
"""
from __future__ import annotations

import inspect

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Part (b) tests: mi_adhilepa._overlay_row() must emit 'not_assessed'
# ──────────────────────────────────────────────────────────────────────────────

class TestOverlayRowLeakageStatus:
    """Part (b): mi_adhilepa must emit 'not_assessed', not None."""

    def _make_mult(self, target_ref: str = "fam_yoga") -> dict:
        return {
            "applied_multiplier": 1.5,
            "raw_multiplier": 1.5,
            "target_ref": target_ref,
            "kill_switch_state": "active",
            "n_observations": 3,
        }

    def test_overlay_row_emits_not_assessed(self):
        """_overlay_row must emit 'not_assessed' for leakage_status (index 9)."""
        from pipeline.orchestrator.writers.mi_adhilepa import _overlay_row

        mult = self._make_mult("fam_yoga")
        row = _overlay_row("chart-id", "L2", "bo_laksana", "sig-1", mult, 0)
        # leakage_status is at index 9 in the tuple
        assert row[9] == "not_assessed", (
            f"Expected 'not_assessed' for leakage_status (index 9), got {row[9]!r}. "
            "None would violate NOT NULL; 'clean' would be a lie (no detector exists — §N.7-4)."
        )

    def test_overlay_row_does_not_emit_none(self):
        """None violates the NOT NULL constraint on leakage_status."""
        from pipeline.orchestrator.writers.mi_adhilepa import _overlay_row

        mult = self._make_mult("fam_graha_natal")
        row = _overlay_row("chart-id", "L1", "ga_facts", "fact-1", mult, 0)
        assert row[9] is not None, (
            "leakage_status must not be None — the schema column is NOT NULL. "
            "Use 'not_assessed' as the honest named state."
        )

    def test_overlay_row_does_not_emit_clean(self):
        """'clean' implies a leakage detector ran and found nothing — no such
        detector exists (§N.7-4). Emitting 'clean' is an unimplemented check
        wearing a clean result's clothes."""
        from pipeline.orchestrator.writers.mi_adhilepa import _overlay_row

        mult = self._make_mult("fam_graha_natal")
        row = _overlay_row("chart-id", "L1", "ga_facts", "fact-2", mult, 0)
        assert row[9] != "clean", (
            "leakage_status must not be 'clean' — no real leakage detector exists (§N.7-4). "
            "Use 'not_assessed' as the honest named state."
        )

    def test_overlay_row_emits_not_assessed_for_all_families(self):
        """All family variants must produce 'not_assessed'."""
        from pipeline.orchestrator.writers.mi_adhilepa import _overlay_row

        families = [
            "fam_yoga", "fam_graha_natal", "fam_ashtakavarga",
            "fam_dasha_period", "fam_divisional", "fam_transit", "fam_msr_signal",
        ]
        for fam in families:
            mult = {
                "applied_multiplier": 1.0,
                "raw_multiplier": 1.0,
                "target_ref": fam,
                "kill_switch_state": "active",
                "n_observations": 0,
            }
            row = _overlay_row("chart-id", "L2", "bo_laksana", f"id-{fam}", mult, 0)
            assert row[9] == "not_assessed", (
                f"Family {fam}: expected 'not_assessed', got {row[9]!r}"
            )

    def test_overlay_row_leakage_is_string_not_null_type(self):
        """Verify the value is specifically the string 'not_assessed'."""
        from pipeline.orchestrator.writers.mi_adhilepa import _overlay_row

        mult = self._make_mult()
        row = _overlay_row("chart-id", "L2", "bo_laksana", "sig-x", mult, 0)
        leakage = row[9]
        assert isinstance(leakage, str), (
            f"leakage_status must be a str, got {type(leakage).__name__!r}"
        )
        assert leakage == "not_assessed"

    def test_overlay_row_tuple_length_unchanged(self):
        """The overlay tuple must still have 13 elements (schema columns)."""
        from pipeline.orchestrator.writers.mi_adhilepa import _overlay_row

        mult = self._make_mult()
        row = _overlay_row("chart-id", "L2", "bo_laksana", "sig-x", mult, 0)
        assert len(row) == 13, (
            f"_overlay_row must return 13-element tuple; got {len(row)}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Part (b) source-text checks
# ──────────────────────────────────────────────────────────────────────────────

class TestOverlayRowSourceText:
    """Source-text checks: the old None assignment is gone and 'not_assessed'
    is the assigned value."""

    def _src(self) -> str:
        from pipeline.orchestrator.writers import mi_adhilepa as mod
        return inspect.getsource(mod)

    def test_leakage_not_none_in_overlay_row(self):
        """'leakage = None' must not appear in _overlay_row context."""
        import ast
        src = self._src()
        # Find the _overlay_row function body — use the next top-level boundary
        # (could be '\ndef ' or '\n@register' for a decorated class).
        idx = src.index("def _overlay_row(")
        # Find the next top-level definition or decorator after this function
        import re
        next_boundary = re.search(r'\n(?:def |@)', src[idx + 1:])
        if next_boundary:
            fn_body = src[idx: idx + 1 + next_boundary.start()]
        else:
            fn_body = src[idx:]
        assert "leakage = None" not in fn_body, (
            "Found 'leakage = None' inside _overlay_row. "
            "This violates NOT NULL and must be replaced with 'not_assessed'."
        )

    def test_leakage_assigned_not_assessed(self):
        """'not_assessed' must appear as the leakage assignment."""
        import re
        src = self._src()
        idx = src.index("def _overlay_row(")
        next_boundary = re.search(r'\n(?:def |@)', src[idx + 1:])
        if next_boundary:
            fn_body = src[idx: idx + 1 + next_boundary.start()]
        else:
            fn_body = src[idx:]
        assert '"not_assessed"' in fn_body or "'not_assessed'" in fn_body, (
            "_overlay_row must assign leakage = 'not_assessed'."
        )

    def test_writer_parses_as_valid_python(self):
        import ast
        ast.parse(self._src())


# ──────────────────────────────────────────────────────────────────────────────
# Part (c) tests: mi_gunanaka must not require 'clean' for calibration evidence
# ──────────────────────────────────────────────────────────────────────────────

class TestGunakaLeakageFilter:
    """Part (c): mi_gunanaka must NOT filter out 'not_assessed' rows.

    The old code: `if cr.get("leakage_status") != "clean": continue`
    excluded everything when leakage_status is 'not_assessed' — because
    no leakage detector exists, all rows would be 'not_assessed' after
    Part (b), making the calibration evidence path silently empty.

    §N.8: a filter that can never pass is not a real filter.
    The fix: only exclude rows explicitly marked 'leaked'; admit 'clean'
    and 'not_assessed' both.
    """

    def _src(self) -> str:
        from pipeline.orchestrator.writers import mi_gunanaka as mod
        return inspect.getsource(mod)

    def test_gunanaka_does_not_require_clean_only(self):
        """The pattern `!= "clean"` must not be the sole leakage gate.

        After the fix, 'not_assessed' rows must be admitted to calibration
        evidence — excluding them would silently empty the calibration path
        when no detector exists (§N.8 earned-signal principle)."""
        src = self._src()
        # If '!= "clean"' appears, it must be accompanied by logic that
        # handles 'leaked' separately (i.e. the fix is in place).
        # The fix removes the '!= "clean"' pattern entirely OR adds an
        # explicit 'leaked' exclusion alongside it.
        has_old_pattern = '!= "clean"' in src or "!= 'clean'" in src
        has_leaked_exclusion = '"leaked"' in src or "'leaked'" in src
        if has_old_pattern:
            assert has_leaked_exclusion, (
                "mi_gunanaka still uses `!= 'clean'` as its sole leakage filter. "
                "After Part (b), ALL rows will be 'not_assessed', silently emptying "
                "calibration evidence. Fix: only exclude rows marked 'leaked' (§N.8)."
            )

    def test_gunanaka_excludes_leaked(self):
        """Rows explicitly marked 'leaked' should still be excluded from calibration."""
        src = self._src()
        assert '"leaked"' in src or "'leaked'" in src, (
            "mi_gunanaka must still exclude 'leaked' rows from calibration evidence. "
            "Genuine leakage detection results must be respected."
        )

    def test_gunanaka_source_valid_python(self):
        import ast
        ast.parse(self._src())

    def test_not_assessed_admitted_to_calibration(self):
        """Simulate the evidence aggregation loop: 'not_assessed' rows must
        contribute to calibration evidence, not be skipped."""
        # Simulate what the fixed loop should do:
        # Only skip rows where leakage_status == 'leaked'.
        cal_rows = [
            {"prediction_id": "p1", "composite_score": 0.7, "leakage_status": "not_assessed",
             "driving_signals": [{"family_id": "fam_yoga"}]},
            {"prediction_id": "p2", "composite_score": 0.6, "leakage_status": "clean",
             "driving_signals": [{"family_id": "fam_graha_natal"}]},
            {"prediction_id": "p3", "composite_score": 0.9, "leakage_status": "leaked",
             "driving_signals": [{"family_id": "fam_yoga"}]},
        ]

        # Replicate the FIXED loop logic (§N.8: only exclude 'leaked')
        evidence = {}
        excluded = 0
        for cr in cal_rows:
            ls = cr.get("leakage_status")
            if ls == "leaked":
                excluded += 1
                continue
            # 'not_assessed' and 'clean' both proceed
            driving = cr.get("driving_signals") or []
            score = float(cr.get("composite_score") or 0.5)
            for sig in driving:
                fid = sig.get("family_id", "unknown")
                evidence.setdefault(fid, []).append(score)

        assert excluded == 1, f"Expected 1 excluded (leaked) row, got {excluded}"
        assert "fam_yoga" in evidence, (
            "fam_yoga should appear in evidence from the 'not_assessed' p1 row"
        )
        assert "fam_graha_natal" in evidence, (
            "fam_graha_natal should appear in evidence from the 'clean' p2 row"
        )
        # p3 (leaked) must not contribute
        assert evidence.get("fam_yoga") == [0.7], (
            "Only the not_assessed p1 score (0.7) for fam_yoga — the leaked p3 must be excluded"
        )

    def test_old_filter_would_silently_empty_calibration(self):
        """Demonstrate the defect: the old 'clean'-only filter drops all
        'not_assessed' rows, leaving evidence empty when no detector ran."""
        cal_rows = [
            {"prediction_id": "p1", "composite_score": 0.7, "leakage_status": "not_assessed",
             "driving_signals": [{"family_id": "fam_yoga"}]},
            {"prediction_id": "p2", "composite_score": 0.8, "leakage_status": "not_assessed",
             "driving_signals": [{"family_id": "fam_graha_natal"}]},
        ]

        # OLD (broken) loop logic
        evidence_old = {}
        for cr in cal_rows:
            if cr.get("leakage_status") != "clean":
                continue  # This skips EVERYTHING when leakage_status = 'not_assessed'
            driving = cr.get("driving_signals") or []
            score = float(cr.get("composite_score") or 0.5)
            for sig in driving:
                fid = sig.get("family_id", "unknown")
                evidence_old.setdefault(fid, []).append(score)

        assert evidence_old == {}, (
            "This test documents the defect: the old 'clean'-only filter "
            "silently empties calibration evidence when all rows are 'not_assessed'. "
            "This test should always pass (documenting the bug, not the fix)."
        )

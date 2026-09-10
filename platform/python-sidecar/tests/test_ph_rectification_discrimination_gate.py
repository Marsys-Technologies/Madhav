"""ph_rectification: `load_bearing: true` on a fit that discriminates between nothing.

F3 (L4_W1_ANALYSIS_BATCH_D.md §ph_rectification / §N.8): `judgment_flags()`
(services.mimamsa.lel_calibration, shared with L5) computes `load_bearing` as a pure
function of event_count -- true iff calibration_state == 'calibrated'. That is a
statement about DATA AVAILABILITY (enough recorded life events). It says nothing
about DISCRIMINATION (did the fit actually distinguish between candidate offsets),
which only exists once `win_margin` is computed downstream. Measured live: 95/95
scored rows on the canonical chart have win_margin=0 with load_bearing=true.

_apply_discrimination_gate() closes that gap at the writer's own call site --
deliberately NOT inside the shared lel_calibration module, whose own docstring
forbids reshaping judgment_flags() without a coordinated migration.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.ph_rectification import _apply_discrimination_gate


def _calibrated_flags() -> dict:
    return {
        "calibration": "calibrated",
        "calibration_state": "calibrated",
        "rectification_basis": "lel_fit",
        "lel_event_count": 40,
        "load_bearing": True,
    }


def _structural_flags() -> dict:
    return {
        "calibration": "structural",
        "calibration_state": "structural",
        "rectification_basis": "structural_no_lel",
        "lel_event_count": 0,
        "load_bearing": False,
    }


class TestDiscriminationGate:
    def test_zero_win_margin_forces_load_bearing_false(self):
        # The measured live defect: calibration_state=calibrated (enough events),
        # win_margin=0 (the fit discriminates nothing) -> load_bearing must flip.
        gated = _apply_discrimination_gate(_calibrated_flags(), 0.0)
        assert gated["load_bearing"] is False
        assert "load_bearing_note" in gated
        assert "win_margin" in gated["load_bearing_note"]

    def test_none_win_margin_forces_load_bearing_false(self):
        # No training events scored at all -- select_best's own no-candidate path.
        gated = _apply_discrimination_gate(_calibrated_flags(), None)
        assert gated["load_bearing"] is False

    def test_real_win_margin_leaves_load_bearing_true(self):
        gated = _apply_discrimination_gate(_calibrated_flags(), 0.12)
        assert gated["load_bearing"] is True
        assert "load_bearing_note" not in gated

    def test_structural_chart_unaffected_by_gate(self):
        # load_bearing is already False (not enough events) -- the gate has
        # nothing to do and must not add a note where nothing was overridden.
        gated = _apply_discrimination_gate(_structural_flags(), 0.0)
        assert gated["load_bearing"] is False
        assert "load_bearing_note" not in gated

    def test_calibration_state_and_other_keys_untouched(self):
        # Only load_bearing (+ the new note) changes -- calibration_state still
        # honestly reports "enough events were available", a different claim.
        original = _calibrated_flags()
        gated = _apply_discrimination_gate(original, 0.0)
        assert gated["calibration_state"] == "calibrated"
        assert gated["lel_event_count"] == 40
        assert gated["rectification_basis"] == "lel_fit"

    def test_input_dict_not_mutated_in_place(self):
        original = _calibrated_flags()
        _apply_discrimination_gate(original, 0.0)
        assert original["load_bearing"] is True, "gate must return a new dict, not mutate the caller's"

    def test_small_nonzero_win_margin_is_not_gated(self):
        # The gate mirrors the measured defect (exact 0), not a fuzzy epsilon --
        # the shared serving-layer non_discriminating flag already handles
        # near-zero at read time; this writer-side gate is the narrower, exact
        # correction the integrity check (§ph_rectification check 8) tests for.
        gated = _apply_discrimination_gate(_calibrated_flags(), 0.001)
        assert gated["load_bearing"] is True

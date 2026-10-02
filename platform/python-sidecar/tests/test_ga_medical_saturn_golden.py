"""
test_ga_medical_saturn_golden.py -- SS ruling 2026-10-02 (band/X2 lane, decision a).

The ga_medical Saturn "FORENSIC guard" (a build-halting assertion about one chart's label) was
REMOVED from the writer: it lived inside a writer that runs for every chart, was tied to an
unsourced cut point, and is not one of the seven FORENSIC anchors (those are positional: Sun sign,
Moon nakshatra, Lagna, tithi, vara, yoga, karana). What it was trying to protect is pinned here as a
golden TEST instead, so a future change to Saturn's stored score or band shows in CI, not as a
production halt.

These goldens run the REAL ga_condition compute path (`dignity_d1_from_sign`, the dignity /
deeptaadi / baladi score tables, `_compute_varga_composite`, `compute_condition_score_v1`) on the READ
INPUTS in `_ga_condition_canonical_inputs.py` (sign, degree, motion, the D1..D2700 dignity spread; read
SELECT-only 2026-10-02 for the canonical chart), then the real band table and the two consumers' label
functions. The pinned scores are asserted against the COMPUTED score, never fed in as a literal, so a
change to any weight, table entry or rule that moves Saturn's score or band fails here.

Under the ruled 0.4 / 0.7 band table every canonical Saturn score is in the MID band, so the ga_medical
label is 'moderate' (the pre-lane stored 'mild' came from the old 0.6 cut); vastu stays 'neutral'.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_condition_bands as bands  # noqa: E402
from ga_writers import ga_condition_writer as cw  # noqa: E402
from ga_writers import ga_medical_writer as med  # noqa: E402
from tests import _ga_condition_canonical_inputs as fx  # noqa: E402

SATURN = list(zip(fx.AYANAMSHAS, fx.SATURN_PINNED_SCORES))


def _compute(ayanamsha):
    return fx.run_real_compute("Saturn", fx.SATURN_CANONICAL[ayanamsha])


def test_the_writer_no_longer_has_a_saturn_guard():
    assert not hasattr(med, "saturn_forensic_guard_violation")
    src = pathlib.Path(med.__file__).read_text(encoding="utf-8")
    assert "FORENSIC VIOLATION" not in src
    assert "raise AssertionError" not in src


@pytest.mark.parametrize("ayanamsha,pinned", SATURN)
def test_real_compute_path_reproduces_the_pinned_saturn_score(ayanamsha, pinned):
    r = _compute(ayanamsha)
    assert r["condition_score"] == pinned
    assert r["breakdown"]["varga_fallback_used"] is False   # the composite came from the D1..D2700 spread


@pytest.mark.parametrize("ayanamsha,pinned", SATURN)
def test_saturn_is_exalted_in_libra_by_the_real_dignity_rule(ayanamsha, pinned):
    row = fx.SATURN_CANONICAL[ayanamsha]
    assert row["sign"] == "Libra"                       # the READ chart_facts sign
    r = _compute(ayanamsha)
    assert r["dignity_d1"] == "exalted"                 # computed by dignity_d1_from_sign, not pinned
    assert r["dignity_score"] == cw.DIGNITY_SCORES["exalted"] == 1.0
    assert r["avastha_deeptaadi"] == "deepta"
    assert r["is_combust"] is False and r["is_deeply_combust"] is False


@pytest.mark.parametrize("ayanamsha,pinned", SATURN)
def test_every_intermediate_matches_what_the_writer_stored(ayanamsha, pinned):
    """The stored row is the second witness: each computed step equals the value the build wrote."""
    r, stored = _compute(ayanamsha), fx.SATURN_CANONICAL[ayanamsha]["stored"]
    assert r["dignity_d1"] == stored["dignity_d1"]
    assert r["avastha_baladi"] == stored["avastha_baladi"]
    assert r["avastha_deeptaadi"] == stored["avastha_deeptaadi"]
    assert r["varga_dignity_composite"] == stored["varga_dignity_composite"]
    assert r["condition_score"] == stored["condition_score"]


@pytest.mark.parametrize("ayanamsha,pinned", SATURN)
def test_canonical_saturn_band_and_labels_under_the_ruled_table(ayanamsha, pinned):
    r = _compute(ayanamsha)
    assert r["band"] == bands.BAND_MID                  # the ruled 0.4 / 0.7 table
    assert r["medical_label"] == "moderate"             # was 'mild' under the old 0.6 cut
    assert r["vastu_label"] == "neutral"                # unchanged by the lane


def test_headroom_below_the_high_edge_is_computed_so_a_cut_move_is_visible():
    """The closest canonical Saturn score to the 0.7 edge is raman (0.697162, 0.002838 below)."""
    scores = {ay: _compute(ay)["condition_score"] for ay in fx.AYANAMSHAS}
    assert max(scores.values()) < bands.CUT_MID_HIGH
    assert min(scores.values()) >= bands.CUT_LOW_MID
    assert max(scores, key=scores.get) == "raman"
    assert round(bands.CUT_MID_HIGH - scores["raman"], 6) == 0.002838


# ---- the goldens can fail: each mutation of a real input to the path moves a pinned value ------------

@pytest.mark.parametrize(
    "table,key,delta",
    [
        ("_DEEPTAADI_SCORES", "deepta", -0.30),   # Saturn's deeptaadi label
        ("DIGNITY_SCORES", "exalted", -0.20),     # Saturn's D1 dignity
        ("_BALADI_SCORES", "vriddha", +0.50),     # Saturn's baladi on 4 of 5 ayanamshas
        ("DIGNITY_SCORES", "neutral_sign", +0.30),  # the varga composite's dominant label
    ],
)
def test_mutating_a_score_table_entry_breaks_the_saturn_golden(monkeypatch, table, key, delta):
    tbl = getattr(cw, table)
    monkeypatch.setitem(tbl, key, tbl[key] + delta)
    moved = [ay for ay, pinned in SATURN if _compute(ay)["condition_score"] != pinned]
    assert moved, f"mutating {table}[{key!r}] by {delta:+} did not move any pinned Saturn score"


def test_mutating_a_formula_weight_breaks_the_saturn_golden(monkeypatch):
    monkeypatch.setitem(cw._FORMULA_WEIGHTS, "deeptaadi", cw._FORMULA_WEIGHTS["deeptaadi"] + 0.05)
    assert all(_compute(ay)["condition_score"] != pinned for ay, pinned in SATURN)


def test_moving_the_high_edge_breaks_the_band_assertion(monkeypatch):
    monkeypatch.setattr(bands, "CUT_MID_HIGH", 0.69)
    monkeypatch.setattr(bands, "SCORE_BANDS", tuple(
        bands.ScoreBand(b.name, 0.69 if b.name == bands.BAND_HIGH else b.lower,
                        0.69 if b.name == bands.BAND_MID else b.upper)
        for b in bands.SCORE_BANDS
    ))
    # raman (0.697162) and krishnamurti (0.691486) now fall in the HIGH band
    assert _compute("raman")["band"] != bands.BAND_MID

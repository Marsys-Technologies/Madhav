"""
test_ga_condition_f_c8_varga_dignity_composite.py — F-C8
(L1_W1_ANALYSIS_BATCH_C.md §3.3): `ga_condition_composite.varga_dignity_composite`
was NULL on 135/135 rows while `varga_dignity_spread` held a rich 29-varga JSON
per graha for every one of them.

Root cause: `chart_divisionals.dignity` (read by `_load_varga_dignity_spread`)
stores Title-Case bare labels ("Enemy", "Moolatrikona", ...) from
`ga_vargas_writer._compute_dignity`, while `DIGNITY_SCORES` is keyed lowercase
with a `_sign` suffix on the three relative tiers ("enemy_sign", not "enemy").
"Enemy" != "enemy_sign", not even case-insensitively, so every varga's fallback
lookup missed and `_compute_varga_composite` fell through its `total_w == 0`
branch to `None` on every row.

The fix reuses this same file's own pre-existing `_DIVISIONAL_DIGNITY_NORMALIZE`
map (already used for these rows' deeptaadi avastha, and already imported by
`ga_dashas_writer.py`) rather than adding a second, drifting copy of the same
translation.

DB-free: `_compute_varga_composite` is a pure function over an already-loaded
spread dict.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers.ga_condition_writer import (  # noqa: E402
    DIGNITY_SCORES,
    _DIVISIONAL_DIGNITY_NORMALIZE,
    _compute_varga_composite,
)


def test_title_case_dignity_label_no_longer_produces_none():
    """The exact live reproducer from W1: Sun's D1 dignity stored as 'Enemy'."""
    spread = {"D1": {"sign": "Capricorn", "dignity": "Enemy"}}
    assert _compute_varga_composite(spread) is not None


def test_every_normalized_label_resolves_to_its_dignity_scores_entry():
    """Every label _DIVISIONAL_DIGNITY_NORMALIZE can produce must land on the
    SAME score DIGNITY_SCORES assigns that key -- not merely non-None."""
    for label in _DIVISIONAL_DIGNITY_NORMALIZE:
        spread = {"D1": {"sign": "Aries", "dignity": label}}
        composite = _compute_varga_composite(spread)
        expected = DIGNITY_SCORES[_DIVISIONAL_DIGNITY_NORMALIZE[label]]
        assert composite == expected, (
            f"label {label!r} composited to {composite}, expected {expected} "
            f"(the D1-only weighted average is just DIGNITY_SCORES' own value)"
        )


def test_unrecognized_label_is_an_honest_none_not_a_default():
    """§N.7 item 6: an unmapped label must not silently default to some tier's
    score -- it must drop out of the weighted average like a missing score."""
    spread = {"D1": {"sign": "Aries", "dignity": "Unknown"}}
    assert _compute_varga_composite(spread) is None


def test_multi_varga_weighted_average_matches_hand_computation():
    """D1 (weight 3.5, Exalted=1.0) + D9 (weight 3.0, Own=0.8):
    (3.5*1.0 + 3.0*0.8) / (3.5+3.0) = 6.9/6.5"""
    spread = {
        "D1": {"sign": "Aries", "dignity": "Exalted"},
        "D9": {"sign": "Taurus", "dignity": "Own"},
    }
    composite = _compute_varga_composite(spread)
    assert composite == round((3.5 * 1.0 + 3.0 * 0.8) / (3.5 + 3.0), 6)


def test_numeric_score_key_still_takes_priority_over_the_label():
    """If a future writer ever populates the 'score' fast path directly, it must
    still win over deriving from the label."""
    spread = {"D1": {"sign": "Aries", "dignity": "Debilitated", "score": 0.9}}
    assert _compute_varga_composite(spread) == 0.9

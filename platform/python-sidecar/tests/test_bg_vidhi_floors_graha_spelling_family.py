"""bg_vidhi_floors: the graha-valued floor-item args (`karaka`, `point`) use ONE spelling family.

SS N-272/N-273: `vidhi_floor_items.args_override` mixed `jupiter` (karaka) with `JUPITER` / `SUN`
(point): one graha, three spellings in one column (the cross-layer drift graha_vocabulary.py
exists to stop). The seed now carries the released canonical subject code everywhere
(`JUP`, `SUN`, `KET_MEAN`, `LAGNA` ...). These tests re-derive each value from the L0 semantic
release (no hand-typed table here) so the seed cannot drift from it, and pin the
canonical-untouched / unknown-is-flagged behaviours.
"""
from __future__ import annotations

import pytest

from brahmagyan.l0_semantic_release import graha_subject_code
from pipeline.orchestrator.writers import bg_vidhi_floors as mod

GRAHA_ARG_KEYS = ("karaka", "point")


def _graha_args():
    out = []
    for (intent, _v, _cov, _notes, items) in mod.FLOORS:
        for (prim, order, _band, args, _hard) in items:
            for key in GRAHA_ARG_KEYS:
                if key in args:
                    out.append((intent, prim, order, key, args[key]))
    return out


def test_the_seed_carries_graha_args():
    got = _graha_args()
    assert any(k == "karaka" for *_x, k, _v in got)
    assert any(k == "point" for *_x, k, _v in got)


@pytest.mark.parametrize("intent,prim,order,key,value", _graha_args())
def test_graha_arg_is_the_released_canonical_code(intent, prim, order, key, value):
    # variant in -> canonical out would be graha_subject_code(value); canonical must be a fixed point
    assert graha_subject_code(value) == value, (
        f"{intent}#{order} {prim}.{key}={value!r} is not the released canonical subject code "
        f"({graha_subject_code(value)!r})")


def test_one_family_across_the_column():
    values = {v for *_x, v in _graha_args()}
    assert values <= {graha_subject_code(v) for v in values}
    assert not {v for v in values if v != v.upper()}, "a lower/title-case graha spelling is back"


@pytest.mark.parametrize("variant,canonical", [
    ("jupiter", "JUP"), ("JUPITER", "JUP"), ("Ketu", "KET_MEAN"), ("mercury", "MER"),
    ("SUN", "SUN"), ("LAGNA", "LAGNA"),
])
def test_resolver_maps_variants_to_the_seed_value_and_leaves_canonical(variant, canonical):
    assert graha_subject_code(variant) == canonical


def test_unknown_graha_is_refused_not_defaulted():
    with pytest.raises(ValueError):
        graha_subject_code("not-a-graha")


def test_non_graha_args_are_untouched():
    flat = [a for (_i, _v, _c, _n, items) in mod.FLOORS for (_p, _o, _b, a, _h) in items]
    assert {"chara_karaka": "AK"} in flat and {"chara_karaka": "AmK"} in flat
    assert {"house": 5} in flat and {"varga": "D9"} in flat and {"domain": "wealth"} in flat

"""A5.3 — the five closed graha adapters the R17 census excludes (steward M20261003T121341 / Suvarna M20261003T121400).

* the three BUILDER maps are now DERIVED from the SSoT (they migrated onto the graha_vocabulary helpers after the
  protected window): the equality pins below remain as drift guards — a hand-edit that re-introduces an
  independent literal still fails here, and each parity check is itself mutation-proofed;
* the two VERIFIER maps are PERMANENT exclusions (independence from builder and SSoT is their purpose): they are checked against FIXED
  LITERAL expectations ONLY — nothing here ties them to the SSoT.
Doctrine note (Suvarna, M20261003T121557): the parity test pins the MEAN-node mapping (RAH_MEAN / KET_MEAN). If a builder map is ever meant
to follow the TRUE nodes, that is a doctrine question for Suvarna, not a parity update.
Database-free; runs everywhere.
"""
from __future__ import annotations

import pytest

from brahmagyan import graha_vocabulary as gv
from services.gochara_kernel import chart_context, inventory_verifier, substrate, window_sweep, window_verifier

# the nine grahas of the kernel's (mean-node) convention, derived from the SSoT: its entities minus Lagna and the explicit true nodes
SSOT_NINE = {code: title for code, title in gv._SUBJECT_TO_TITLE.items() if code != "LAGNA" and not code.endswith("_TRUE")}


def _problems(actual: dict, expected: dict) -> list[str]:
    out = [f"key set differs: only-actual={sorted(set(actual) - set(expected))} only-expected={sorted(set(expected) - set(actual))}"] \
        if set(actual) != set(expected) else []
    out += [f"{k}: {actual[k]!r} != {expected[k]!r}" for k in expected if k in actual and actual[k] != expected[k]]
    return out


BUILDER_MAPS = {
    "chart_context._SUBJECT_TITLE": (chart_context._SUBJECT_TITLE, dict(SSOT_NINE)),                                   # subject code -> Title
    "substrate.DB_BODY": (substrate.DB_BODY, {t: t.lower() for t in SSOT_NINE.values()}),                               # Title -> lowercase DB value
    "window_sweep.GRAHA_TITLE": (window_sweep.GRAHA_TITLE, {t.lower(): t for t in SSOT_NINE.values()}),                 # lowercase -> Title
}


def test_the_ssot_nine_is_nine():
    assert len(SSOT_NINE) == 9 and SSOT_NINE["RAH_MEAN"] == "Rahu" and SSOT_NINE["KET_MEAN"] == "Ketu"


@pytest.mark.parametrize("name", sorted(BUILDER_MAPS))
def test_each_builder_map_equals_the_one_derived_from_the_ssot(name):
    actual, expected = BUILDER_MAPS[name]
    assert _problems(actual, expected) == [], name


@pytest.mark.parametrize("name", sorted(BUILDER_MAPS))
def test_each_parity_check_fails_when_one_value_or_key_is_altered(name):
    actual, expected = BUILDER_MAPS[name]
    key = sorted(actual)[0]
    assert _problems({**actual, key: actual[key] + "_x"}, expected), f"{name}: an altered value must be caught"
    assert _problems({k: v for k, v in actual.items() if k != key}, expected), f"{name}: a dropped key must be caught"
    assert _problems({**actual, "extra": "x"}, expected), f"{name}: an added key must be caught"


def test_the_verifier_maps_match_their_fixed_literal_expectations_and_nothing_else():
    assert window_verifier._TITLE == {"sun": "Sun", "moon": "Moon", "mars": "Mars", "mercury": "Mercury", "jupiter": "Jupiter",
                                      "venus": "Venus", "saturn": "Saturn", "rahu": "Rahu", "ketu": "Ketu"}
    assert inventory_verifier._FACT_SUBJECT == {"SUN": "sun", "MOON": "moon", "MAR": "mars", "MER": "mercury", "JUP": "jupiter",
                                                "VEN": "venus", "SAT": "saturn", "RAH_MEAN": "rahu", "KET_MEAN": "ketu"}

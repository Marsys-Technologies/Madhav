"""
Suvarna Track I-2 — ka_vighnakara malefic-transit reason must derive the chart's own signs.

THE DEFECT. `_check_malefic_transit` stored 'adversarial to native lagna (Aries) / moon
(Aquarius)' for EVERY chart, and the adversity tables `_SATURN_ADVERSE_SIGNS` /
`_RAHU_ADVERSE_SIGNS` were a literal Aries/Aquarius native's own. The sentence therefore asserted
false chart facts for any other chart, and the score behind it was not chart-relative either.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ka_vighnakara as kv
from pipeline.orchestrator.writers.ka_vighnakara import (
    _check_malefic_transit,
    _chart_adverse_signs,
)

WRITER = Path(kv.__file__)
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _lon(sign: str) -> float:
    return SIGNS.index(sign) * 30.0 + 10.0


class _FakeSwe:
    """swe.calc_ut stub: Saturn and Rahu fixed in the given signs (sidereal)."""
    FLG_SWIEPH = 2
    FLG_SIDEREAL = 65536

    def __init__(self, saturn_sign: str, rahu_sign: str = "Gemini"):
        self._lons = {6: _lon(saturn_sign), 11: _lon(rahu_sign)}

    def set_sid_mode(self, *a, **k): pass
    def calc_ut(self, jd, pid, flags=0):
        return ((self._lons[pid], 0.0, 1.0, 0.0, 0.0, 0.0), flags)


@pytest.fixture(autouse=True)
def _stub_sidereal(monkeypatch):
    monkeypatch.setattr(kv, "_get_sidereal_lon", lambda swe, jd, pid: swe._lons.get(pid))


def test_legacy_aries_aquarius_tables_are_reproduced_exactly() -> None:
    sat, rahu = _chart_adverse_signs(_lon("Aries"), _lon("Aquarius"))
    assert {k: v[0] for k, v in sat.items()} == {
        'Virgo': 0.50, 'Scorpio': 0.60, 'Pisces': 0.45, 'Capricorn': 0.45, 'Aquarius': 0.65}
    assert {k: v[0] for k, v in rahu.items()} == {'Libra': 0.40, 'Virgo': 0.45, 'Scorpio': 0.45}


def test_reason_names_aries_aquarius_for_that_chart() -> None:
    r = _check_malefic_transit("2030-01-01", jd=1.0, swe=_FakeSwe("Aquarius"),
                               natal_lagna_lon=_lon("Aries"), natal_moon_lon=_lon("Aquarius"))
    assert r["severity_score"] == 0.65
    assert "lagna (Aries)" in r["detail"]["reason"] and "Moon (Aquarius)" in r["detail"]["reason"]


def test_reason_names_leo_cancer_for_a_different_chart() -> None:
    # Saturn in Aquarius is the 7th from Leo lagna: NOT adverse here, and Aries/Aquarius must not appear.
    assert _check_malefic_transit("2030-01-01", jd=1.0, swe=_FakeSwe("Aquarius"),
                                  natal_lagna_lon=_lon("Leo"), natal_moon_lon=_lon("Cancer")) is None
    # Saturn in Capricorn is the 6th from Leo and the 8th from Cancer Moon: adverse for THIS chart.
    r = _check_malefic_transit("2030-01-01", jd=1.0, swe=_FakeSwe("Capricorn"),
                               natal_lagna_lon=_lon("Leo"), natal_moon_lon=_lon("Cancer"))
    assert r is not None
    reason = r["detail"]["reason"]
    assert "lagna (Leo)" in reason and "Moon (Cancer)" in reason
    assert "Aries" not in reason and "Aquarius" not in reason
    assert r["detail"]["natal_lagna_sign"] == "Leo" and r["detail"]["natal_moon_sign"] == "Cancer"
    assert "6th from lagna" in reason


def test_missing_lagna_and_moon_is_an_honest_null_not_a_default_chart() -> None:
    assert _check_malefic_transit("2030-01-01", jd=1.0, swe=_FakeSwe("Scorpio"),
                                  natal_lagna_lon=None, natal_moon_lon=None) is None


def test_only_moon_known_omits_the_lagna_clause() -> None:
    r = _check_malefic_transit("2030-01-01", jd=1.0, swe=_FakeSwe("Aquarius"),
                               natal_lagna_lon=None, natal_moon_lon=_lon("Aquarius"))
    assert r is not None
    assert "lagna" not in r["detail"]["reason"].lower()
    assert "Moon (Aquarius)" in r["detail"]["reason"]


def test_no_sign_literal_in_any_reason_template() -> None:
    """AST guard: no sign name inside an f-string / string constant that feeds a `reason` key."""
    tree = ast.parse(WRITER.read_text())
    pat = re.compile(r"\b(" + "|".join(SIGNS) + r")\b")
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == "reason":
                    for sub in ast.walk(v):
                        if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and pat.search(sub.value):
                            offenders.append((sub.lineno, sub.value))
    assert not offenders, offenders
    # And no module-level adversity table keyed by literal sign names remains.
    assert not hasattr(kv, "_SATURN_ADVERSE_SIGNS") and not hasattr(kv, "_RAHU_ADVERSE_SIGNS")

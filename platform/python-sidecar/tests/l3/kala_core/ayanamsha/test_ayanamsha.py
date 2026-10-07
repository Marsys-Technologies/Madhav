"""K0a-1a per-instant ayanāṃśa and single-policy oracles."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from brahmagyan.l0_ephemeris import AYANAMSHA_MAP
from services.kala_core.ayanamsha import (
    CANONICAL_AYANAMSHA, sidereal_longitude, sidereal_offset,
)


def test_offset_selects_l1_convention_and_computes_each_instant(monkeypatch) -> None:
    import swisseph as swe

    calls: list[tuple[str, float | int]] = []
    monkeypatch.setattr(swe, "set_sid_mode", lambda mode: calls.append(("mode", mode)))

    def fake_offset(jd_ut: float) -> float:
        calls.append(("offset", jd_ut))
        return 23.0 + (jd_ut - 2451545.0) / 36525.0

    monkeypatch.setattr(swe, "get_ayanamsa_ut", fake_offset)
    assert CANONICAL_AYANAMSHA == "lahiri_chitrapaksha"
    first = sidereal_offset(2451545.0)
    second = sidereal_offset(2451545.0 + 36525.0)
    assert (first, second) == (23.0, 24.0)
    assert calls == [
        ("mode", AYANAMSHA_MAP[CANONICAL_AYANAMSHA]),
        ("offset", 2451545.0),
        ("mode", AYANAMSHA_MAP[CANONICAL_AYANAMSHA]),
        ("offset", 2451545.0 + 36525.0),
    ]
    assert sidereal_offset.__swiss_state_serialized__ is True


def test_longitude_uses_the_offset_at_its_own_instant(monkeypatch) -> None:
    import swisseph as swe

    monkeypatch.setattr(swe, "set_sid_mode", lambda _mode: None)
    monkeypatch.setattr(swe, "get_ayanamsa_ut", lambda jd: 20.0 + (jd - 100.0))
    assert sidereal_longitude(10.0, 100.0) == 350.0
    assert sidereal_longitude(10.0, 101.0) == 349.0


def test_invalid_convention_and_instant_fail_closed() -> None:
    with pytest.raises(ValueError, match="unknown L1 ayanamsha"):
        sidereal_offset(2451545.0, "guess")
    with pytest.raises(ValueError, match="finite"):
        sidereal_offset(float("nan"))


def test_canonical_ayanamsha_is_defined_once_in_kala_core() -> None:
    package = Path(__file__).resolve().parents[4] / "services" / "kala_core"
    definitions = []
    for path in package.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(target, ast.Name) and target.id == "CANONICAL_AYANAMSHA"
                       for target in targets):
                    definitions.append(path.relative_to(package).as_posix())
    assert definitions == ["ayanamsha/__init__.py"]

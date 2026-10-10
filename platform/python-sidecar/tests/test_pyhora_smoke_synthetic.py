"""
test_pyhora_smoke_synthetic.py -- SS N-384 (PR-S6), item 2.

GET /api/pyhora/smoke used to compute one real person's chart from hard-coded birth details
and compare against that person's expected placements. It now runs on a clearly labelled
SYNTHETIC subject (a fictional "SMOKE-TEST" person at the Greenwich meridian, J2000 noon) and
proves the engine works by internal consistency, not by matching a real chart.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_SIDECAR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))

from routers import pyhora  # noqa: E402

ROUTER_PATH = _SIDECAR / "routers" / "pyhora.py"


def _app() -> TestClient:
    app = FastAPI()
    app.include_router(pyhora.router, prefix="/api/pyhora")
    return TestClient(app)


def _fake_chart(sun_lon: float = 256.5, sun_sign: str = "Sagittarius", moon_nak: str = "Swati") -> dict:
    return {"grahas": [
        {"name": "Sun", "sign": sun_sign, "longitude_deg": sun_lon},
        {"name": "Moon", "sign": "Libra", "longitude_deg": 199.47, "nakshatra": moon_nak},
    ]}


def _install_fake_engine(monkeypatch, compute_chart) -> None:
    """Stand-ins for pyjhora_adapter.{compute,version} so the route is tested without the engine."""
    import types

    pkg = types.ModuleType("pyjhora_adapter")
    pkg.__path__ = []  # type: ignore[attr-defined]
    comp = types.ModuleType("pyjhora_adapter.compute")
    comp.compute_chart = compute_chart  # type: ignore[attr-defined]
    ver = types.ModuleType("pyjhora_adapter.version")
    ver.ENGINE_VERSION = "test-engine"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pyjhora_adapter", pkg)
    monkeypatch.setitem(sys.modules, "pyjhora_adapter.compute", comp)
    monkeypatch.setitem(sys.modules, "pyjhora_adapter.version", ver)
    monkeypatch.setattr(pyhora, "ensure_swiss_backend", lambda *a, **k: None)


@pytest.fixture()
def captured(monkeypatch):
    """Replace the engine with a recorder; record the inputs the route feeds it."""
    seen: dict = {}

    def fake_compute_chart(*, inputs, ayanamsha_id, **_kw):
        seen["inputs"] = dict(inputs)
        seen["ayanamsha_id"] = ayanamsha_id
        return seen.get("chart") or _fake_chart()

    _install_fake_engine(monkeypatch, fake_compute_chart)
    return seen


def test_smoke_feeds_the_engine_synthetic_inputs_only(captured) -> None:
    body = _app().get("/api/pyhora/smoke").json()
    inputs = captured["inputs"]
    assert inputs["datetime_iso"] == "2000-01-01T12:00:00"
    assert inputs["subject_label"] == "SMOKE-TEST synthetic subject"
    assert (inputs["latitude_deg"], inputs["longitude_deg"]) == (51.4769, 0.0)
    assert inputs["tz_offset_hours"] == 0.0
    assert body["synthetic"] is True
    assert "synthetic" in body["note"].lower()
    assert body["inputs"]["subject_label"] == "SMOKE-TEST synthetic subject"


def test_smoke_passes_on_internally_consistent_output(captured) -> None:
    body = _app().get("/api/pyhora/smoke").json()
    assert body["status"] == "pass"
    assert body["sun_pass"] is True and body["moon_pass"] is True
    assert body["sun_sign"] == "Sagittarius"


def test_smoke_fails_when_sign_contradicts_longitude(captured) -> None:
    """A detector that can read false: the sign label disagrees with the longitude."""
    captured["chart"] = _fake_chart(sun_lon=256.5, sun_sign="Capricorn")
    body = _app().get("/api/pyhora/smoke").json()
    assert body["status"] == "fail" and body["sun_pass"] is False


def test_smoke_fails_when_moon_has_no_nakshatra(captured) -> None:
    captured["chart"] = _fake_chart(moon_nak="")
    body = _app().get("/api/pyhora/smoke").json()
    assert body["status"] == "fail" and body["moon_pass"] is False


def test_smoke_fails_when_sun_missing(captured) -> None:
    captured["chart"] = {"grahas": [{"name": "Moon", "sign": "Libra", "longitude_deg": 199.0, "nakshatra": "Swati"}]}
    body = _app().get("/api/pyhora/smoke").json()
    assert body["status"] == "fail" and body["sun_pass"] is False


def test_smoke_reports_engine_errors_honestly(monkeypatch) -> None:
    def boom(**_kw):
        raise RuntimeError("engine down")

    _install_fake_engine(monkeypatch, boom)
    body = _app().get("/api/pyhora/smoke").json()
    assert body["status"] == "error" and "engine down" in body["error"]


def test_smoke_source_has_no_real_person_literals() -> None:
    """No birth-date, coordinate or place literal of a real subject in the route's code."""
    tree = ast.parse(ROUTER_PATH.read_text())
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)]
    strs = [c for c in consts if isinstance(c, str)]
    nums = [c for c in consts if isinstance(c, float)]
    banned_text = ("19" + "84", "10" + ":" + "43", "Bhuba" + "neswar")          # fragments: not embedded here
    banned_nums = (float("20." + "2735"), float("85." + "8334"))
    assert not [s for s in strs if any(b in s for b in banned_text)]
    assert not [n for n in nums if n in banned_nums]


def test_smoke_on_the_real_engine_if_available() -> None:
    """End to end on PyJHora (skipped where the engine or ephemeris is not installed).
    The expected Sun longitude is the standard J2000 value, not any chart's: apparent tropical
    280.37 deg at 2000-01-01 12:00 UT minus the Lahiri ayanamsha at J2000 (23.857 deg)."""
    pytest.importorskip("pyjhora_adapter.compute")
    body = _app().get("/api/pyhora/smoke").json()
    if body["status"] == "error":
        pytest.skip(f"engine unavailable here: {body['error'][:80]}")
    assert body["status"] == "pass", body
    assert body["synthetic"] is True
    assert abs(body["sun_longitude_deg"] - 256.52) < 0.3

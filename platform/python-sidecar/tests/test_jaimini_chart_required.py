"""
test_jaimini_chart_required.py -- SS N-384 (PR-S6), item 3 (routers/jaimini.py).

GET /jaimini_drishti/chara_dasha and /chara_dasha/full used to default `chart_id` to one real
person's chart and, when `birth_date` was omitted, to that person's birth date for ANY chart.
chart_id is now required (422 without it) and an omitted birth_date is read from the requested
chart's own row, never from a constant.
"""
from __future__ import annotations

import ast
import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

_SIDECAR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))

from routers import jaimini  # noqa: E402

ROUTER_PATH = _SIDECAR / "routers" / "jaimini.py"
CHART_A = "aaaaaaaa-0000-4000-8000-00000000000a"
CHART_B = "bbbbbbbb-0000-4000-8000-00000000000b"
ROUTES = ["/chara_dasha", "/chara_dasha/full"]

# Synthetic sidereal longitudes (7 grahas + Lagna) -- not any real chart.
_LONS = {"Sun": 15.0, "Moon": 75.0, "Mars": 135.0, "Mercury": 195.0,
         "Jupiter": 255.0, "Venus": 315.0, "Saturn": 45.0, "Lagna": 100.0}
_BIRTHS = {CHART_A: date(2001, 3, 4), CHART_B: date(1990, 7, 8)}


@pytest.fixture()
def client(monkeypatch):
    seen = {"longitude_charts": [], "birth_charts": []}

    def fake_longitudes(chart_id, ayanamsha_id):
        seen["longitude_charts"].append(chart_id)
        return dict(_LONS)

    def fake_birth_date(chart_id):
        seen["birth_charts"].append(chart_id)
        if chart_id not in _BIRTHS:
            raise HTTPException(status_code=404, detail="chart not found")
        return _BIRTHS[chart_id]

    monkeypatch.setattr(jaimini, "_fetch_chart_longitudes", fake_longitudes)
    monkeypatch.setattr(jaimini, "_fetch_chart_birth_date", fake_birth_date, raising=False)
    app = FastAPI()
    app.include_router(jaimini.router, prefix="/jaimini_drishti")
    c = TestClient(app)
    c.seen = seen  # type: ignore[attr-defined]
    return c


@pytest.mark.parametrize("route", ROUTES)
def test_missing_chart_id_is_422_never_a_default_chart(client, route) -> None:
    r = client.get(f"/jaimini_drishti{route}")
    assert r.status_code == 422
    assert any(e["loc"][-1] == "chart_id" for e in r.json()["detail"])
    assert client.seen["longitude_charts"] == []          # nothing was resolved for any chart


@pytest.mark.parametrize("route", ROUTES)
def test_explicit_chart_id_works_and_uses_that_charts_birth_date(client, route) -> None:
    a = client.get(f"/jaimini_drishti{route}", params={"chart_id": CHART_A}).json()
    b = client.get(f"/jaimini_drishti{route}", params={"chart_id": CHART_B}).json()
    assert a["ok"] is True and b["ok"] is True
    assert a["chart_id"] == CHART_A and b["chart_id"] == CHART_B
    assert a["birth_date"] == "2001-03-04" and b["birth_date"] == "1990-07-08"
    assert set(client.seen["longitude_charts"]) == {CHART_A, CHART_B}
    assert set(client.seen["birth_charts"]) == {CHART_A, CHART_B}


@pytest.mark.parametrize("route", ROUTES)
def test_explicit_birth_date_overrides_without_reading_the_chart_row(client, route) -> None:
    r = client.get(f"/jaimini_drishti{route}", params={"chart_id": CHART_A, "birth_date": "1975-05-05"})
    assert r.json()["birth_date"] == "1975-05-05"
    assert client.seen["birth_charts"] == []


@pytest.mark.parametrize("route", ROUTES)
def test_unknown_chart_without_birth_date_is_404_not_a_constant(client, route) -> None:
    r = client.get(f"/jaimini_drishti{route}", params={"chart_id": "99999999-0000-4000-8000-000000000099"})
    assert r.status_code == 404


@pytest.mark.parametrize("route", ROUTES)
def test_bad_birth_date_is_400(client, route) -> None:
    r = client.get(f"/jaimini_drishti{route}", params={"chart_id": CHART_A, "birth_date": "nope"})
    assert r.status_code == 400


def test_module_has_no_native_chart_or_birth_constant() -> None:
    tree = ast.parse(ROUTER_PATH.read_text())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "_NATIVE_CHART_ID" not in names and "_NATIVE_BIRTH_DATE" not in names
    uuid_like = [n.value for n in ast.walk(tree)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) == 36 and n.value.count("-") == 4]
    assert uuid_like == []
    # no date(1984, 2, 5)-style construction
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and [getattr(a, "value", None) for a in n.args][:1] == [1984]:
            pytest.fail("a 1984 date constructor is back in routers/jaimini.py")

"""
test_lel_intake_route_chart_required.py -- SS N-384 (PR-S6), item 3 (lel_intake HTTP route).

POST /brahma/mimamsa/lel_query accepted a missing chart_id and then queried life_events with NO
chart filter, i.e. every chart's private life events. chart_id is now required (422 without it).
The route calls the library function with exactly the requested chart.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brahmagyan.mimamsa import lel_intake  # noqa: E402

CHART_A = "aaaaaaaa-0000-4000-8000-00000000000a"
CHART_B = "bbbbbbbb-0000-4000-8000-00000000000b"


@pytest.fixture()
def client(monkeypatch):
    calls: list[dict] = []

    def fake_lel_query(**kw):
        calls.append(kw)
        return {"events": [], "total_count": 0, "filter_applied": {"chart_id": kw.get("chart_id")}}

    monkeypatch.setattr(lel_intake, "lel_query", fake_lel_query)
    assert lel_intake.router is not None
    app = FastAPI()
    app.include_router(lel_intake.router, prefix="/brahma/mimamsa")
    c = TestClient(app)
    c.calls = calls  # type: ignore[attr-defined]
    return c


@pytest.mark.parametrize("payload", [{}, {"domain": "career"}, {"chart_id": None}])
def test_missing_chart_id_is_422_and_nothing_is_queried(client, payload) -> None:
    r = client.post("/brahma/mimamsa/lel_query", json=payload)
    assert r.status_code == 422
    assert client.calls == []


def test_explicit_chart_id_is_passed_through_unchanged(client) -> None:
    for cid in (CHART_A, CHART_B):
        r = client.post("/brahma/mimamsa/lel_query", json={"chart_id": cid, "domain": "career"})
        assert r.status_code == 200
    assert [c["chart_id"] for c in client.calls] == [CHART_A, CHART_B]
    assert all(c["domain"] == "career" for c in client.calls)

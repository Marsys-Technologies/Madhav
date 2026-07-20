"""
tests/l3/test_muhurta_score_sidecar_route.py — W2 dark-set wiring proof for
ka_muhurta_seva (DARK_SET_WIRING_PLAN_v1_0 §F gate ruling item 6):
POST /api/compute/muhurta_score.

Distinct subject from tests/test_ka_muhurta_seva.py (that file tests the WriterBase
`ka_muhurta_seva` L3 asset — FROZEN orchestrator writer logic, must_not_touch). This
file tests the NEW retrieval-plane compute-sidecar route `routers.muhurta_score` that
the previously-dark `call_muhurta_score` MCP capability now calls.

Also distinct from `ph_muhurta`/`muhurta_finder` (brahmagyan/phala/muhurta.py) — the
already-served electional-search tool. This route reuses the same score_muhurat()
primitive but scores a single arbitrary instant, no date-range search, no chart_id.

Calls the endpoint function directly (in-process, real panchang_engine compute — not
mocked). Proves real computed scores come back, not the old unconditional-error stub.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

SIDECAR = Path(__file__).parent.parent.parent
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))

from routers.muhurta_score import MuhurtaScoreRequest, muhurta_score  # noqa: E402
from panchang_engine.muhurat import EVENTS_MVP  # noqa: E402


class TestMuhurtaScoreRealCompute:
    def test_returns_real_score_in_valid_range(self):
        req = MuhurtaScoreRequest(datetime_utc="2026-07-20T12:00:00Z", event_class="vivah")
        res = muhurta_score(req)

        assert res["event_class"] == "vivah"
        assert res["local_date"] == "2026-07-20"
        assert 0.0 <= res["score"] <= 100.0
        assert res["stars"] in {1, 2, 3, 4, 5}
        assert res["panchang_context"]["tithi"]
        assert res["panchang_context"]["nakshatra"]
        assert res["panchang_context"]["vara"]
        assert res["panchang_context"]["yoga"]
        assert res["location"]["lat"] == 20.27
        assert res["location"]["lon"] == 85.84

    def test_all_events_mvp_values_score_without_error(self):
        """Every value the descriptor's enum now advertises must actually be scoreable —
        proves the enum wasn't left out of sync with what score_muhurat() accepts."""
        for event in EVENTS_MVP:
            res = muhurta_score(MuhurtaScoreRequest(datetime_utc="2026-07-20T12:00:00Z", event_class=event))
            assert 0.0 <= res["score"] <= 100.0, f"event={event}"

    def test_different_days_produce_different_scores_for_same_event(self):
        """Proves live compute, not a hardcoded/cached response — score varies with the
        day's actual panchang, not just the event_class."""
        scores = set()
        for day in ("2026-07-20T12:00:00Z", "2026-07-21T12:00:00Z", "2026-07-22T12:00:00Z", "2026-07-23T12:00:00Z"):
            res = muhurta_score(MuhurtaScoreRequest(datetime_utc=day, event_class="vivah"))
            scores.add(res["score"])
        assert len(scores) > 1, f"expected score variation across days, got {scores}"

    def test_local_date_reflects_utc_to_ist_conversion(self):
        """A UTC instant late enough in the day rolls into the next IST calendar date
        (UTC+5:30) — proves the tz_offset conversion is real, not a passthrough."""
        res = muhurta_score(MuhurtaScoreRequest(datetime_utc="2026-07-20T20:00:00Z", event_class="vivah"))
        assert res["local_date"] == "2026-07-21"


class TestMuhurtaScoreValidation:
    def test_unrecognized_event_class_fails_loud_422_not_silently_defaulted(self):
        """The pre-wiring descriptor's dead enum (marriage/travel/business/medical/
        education/ceremony) must now be rejected, not silently coerced — proves the
        contract correction actually took effect end to end."""
        with pytest.raises(HTTPException) as exc_info:
            muhurta_score(MuhurtaScoreRequest(datetime_utc="2026-07-20T12:00:00Z", event_class="marriage"))
        assert exc_info.value.status_code == 422
        assert "EXTERNAL_COMPUTATION_REQUIRED" in exc_info.value.detail

    def test_unrecognized_ayanamsha_fails_loud_422(self):
        with pytest.raises(HTTPException) as exc_info:
            muhurta_score(MuhurtaScoreRequest(
                datetime_utc="2026-07-20T12:00:00Z", event_class="vivah", ayanamsha_id="krishnamurti",
            ))
        assert exc_info.value.status_code == 422

    def test_invalid_datetime_fails_400(self):
        with pytest.raises(HTTPException) as exc_info:
            muhurta_score(MuhurtaScoreRequest(datetime_utc="not-a-datetime", event_class="vivah"))
        assert exc_info.value.status_code == 400

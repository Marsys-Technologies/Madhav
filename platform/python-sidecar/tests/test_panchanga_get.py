"""
test_panchanga_get.py — EL-49 fix regression tests.

EL-49: panchāṅga was reachable only through 2-day muhūrta windows serving
start-date panchāṅga only; missing outright: karaṇa, sunrise/sunset, horā
timing. This adds a first-class GET /api/compute/panchanga_get(date,
location?) route over the existing panchang_engine.compute_panchang() engine.

No live DB or network required — panchanga_get is engine-direct (pure
Swiss-Ephemeris compute), so these tests run the real FastAPI route via
TestClient with no mocking.

Charter's exact acceptance bar (§5 β.C / EL-49):
  1. Venus 2026-08-15 -> sidereal Lahiri sign = Virgo (covered in
     test_l0_ephemeris_sidereal_first.py; this file covers panchanga_get).
  2. The birth-date panchāṅga call reproduces all 7 FORENSIC anchors' panchāṅga
     subset exactly: Tithi=Shukla Tritiya, Vara=Ravivara, Yoga=Shiva,
     Karana=Garaja (+ Nakshatra=Purva Bhadrapada, a bonus 5th match).
  3. A forward date (2026-09-18) returns full panchāṅga in one call including
     sunrise + a complete horā table for that day.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import panchang as panchang_router


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = FastAPI()
    app.include_router(panchang_router.router, prefix="/api/compute")
    return TestClient(app)


# ── FORENSIC birth-date reproduction (the free correctness oracle) ─────────

class TestForensicBirthDateReproduction:
    """panchanga_get('1984-02-05', 'Bhubaneswar') must reproduce the panchāṅga
    subset of the 7 FORENSIC anchors EXACTLY — this is not PARKED-HONEST-
    eligible per the charter; if it doesn't match, the computation is wrong,
    full stop."""

    @pytest.fixture(scope="class")
    def forensic_response(self, client: TestClient):
        r = client.get("/api/compute/panchanga_get",
                        params={"date": "1984-02-05", "location": "Bhubaneswar"})
        assert r.status_code == 200, r.text
        return r.json()

    def test_tithi_shukla_tritiya(self, forensic_response):
        assert forensic_response["angas"]["tithi"]["name"] == "Shukla Tritiya"

    def test_vara_ravivara(self, forensic_response):
        assert forensic_response["angas"]["vara"]["name"] == "Ravivara"

    def test_yoga_shiva(self, forensic_response):
        assert forensic_response["angas"]["yoga"]["name"] == "Shiva"

    def test_karana_garaja(self, forensic_response):
        assert forensic_response["angas"]["karana"]["name"] == "Garaja"

    def test_nakshatra_purva_bhadrapada_bonus(self, forensic_response):
        """Not one of the 4 panchāṅga-specific FORENSIC anchors this endpoint
        owns (lagna/nakshatra-at-birth is chart_facts territory per the
        brief), but panchang_engine computes it as part of the same instant
        and it happens to match the FORENSIC Moon nakshatra too — a useful
        extra cross-check."""
        assert forensic_response["angas"]["nakshatra"]["name"] == "Purva Bhadrapada"

    def test_full_karana_pair_available(self, forensic_response):
        """karana_first (=the angas.karana alias) and karana_second are both
        present in the full panchang block — EL-49 explicitly named 'karana'
        as a previously-missing limb; both halves of the tithi are served."""
        panchang = forensic_response["panchang"]
        assert panchang["karana_first"]["name"] == "Garaja"
        assert panchang["karana_second"]["name"]  # non-empty, present

    def test_default_location_matches_named_bhubaneswar(self, client: TestClient):
        """Omitting location entirely must default to Bhubaneswar and still
        reproduce FORENSIC — the register's own complaint is a native asking
        about their own birth chart with no location typed."""
        r = client.get("/api/compute/panchanga_get", params={"date": "1984-02-05"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["location"]["lat"] == 20.27
        assert d["location"]["lon"] == 85.84
        assert d["angas"]["tithi"]["name"] == "Shukla Tritiya"
        assert d["angas"]["karana"]["name"] == "Garaja"


# ── Forward date: full panchāṅga in one call, sunrise + complete horā table ─

class TestForwardDateFullPanchanga:
    @pytest.fixture(scope="class")
    def forward_response(self, client: TestClient):
        r = client.get("/api/compute/panchanga_get",
                        params={"date": "2026-09-18", "location": "Bhubaneswar"})
        assert r.status_code == 200, r.text
        return r.json()

    def test_all_five_angas_present(self, forward_response):
        for anga in ("tithi", "nakshatra", "yoga", "karana", "vara"):
            assert forward_response["angas"][anga]["name"], anga

    def test_sunrise_and_sunset_present_with_ist(self, forward_response):
        assert forward_response["sunrise"]["utc"]
        assert forward_response["sunrise"]["ist"]
        assert forward_response["sunset"]["utc"]
        assert forward_response["sunset"]["ist"]
        # IST field must carry an explicit local offset, not a bare UTC 'Z'.
        assert forward_response["sunrise"]["ist"].endswith("+05:30")

    def test_complete_hora_table(self, forward_response):
        """A full day's hora cycle is 24 slots (day+night horas)."""
        assert forward_response["hora_count"] == 24
        assert len(forward_response["hora"]) == 24
        for h in forward_response["hora"]:
            assert h["label"].startswith("hora_")
            assert h["start_utc"] and h["end_utc"]
            assert h["start_ist"] and h["end_ist"]

    def test_hora_labels_cover_all_seven_classical_planets(self, forward_response):
        labels = {h["label"] for h in forward_response["hora"]}
        expected_planets = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}
        found_planets = {lbl.replace("hora_", "") for lbl in labels}
        assert expected_planets <= found_planets

    def test_response_is_a_single_call_no_pagination_needed(self, forward_response):
        """EL-49's complaint: evaluating a specific day inside a muhūrta window
        required a SECOND targeted call. This route must answer in one call."""
        assert forward_response["ok"] is True
        assert forward_response["date"] == "2026-09-18"


# ── IST-anchoring / timezone-ambiguity fix ──────────────────────────────────

class TestIstAnchoring:
    def test_ist_fields_carry_explicit_offset_not_bare_utc(self, client: TestClient):
        r = client.get("/api/compute/panchanga_get",
                        params={"date": "2026-09-18", "location": "Bhubaneswar"})
        d = r.json()
        for anga_name, anga in d["angas"].items():
            assert anga["end_utc"].endswith("Z"), anga_name
            assert anga["end_ist"].endswith("+05:30"), anga_name
            # The UTC and IST strings must actually differ in wall-clock time
            # (not just relabeled) — proves the +5:30 conversion really ran.
            assert anga["end_utc"][:19] != anga["end_ist"][:19], anga_name

    def test_non_ist_location_gets_local_not_mislabelled_ist(self, client: TestClient):
        """A non-+330 tz_offset_minutes must NOT be labelled '_ist' — that
        would mislabel a non-Indian timezone as India Standard Time."""
        r = client.get("/api/compute/panchanga_get", params={
            "date": "2026-09-18", "lat": 51.5074, "lon": -0.1278,
            "tz_offset_minutes": 60, "location": "London",
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert "local" in d["sunrise"]
        assert "ist" not in d["sunrise"]
        assert d["location"]["timezone_label"] == "UTC+01:00"


# ── Location resolution ──────────────────────────────────────────────────

class TestLocationResolution:
    def test_unknown_named_location_is_a_loud_422_not_a_silent_guess(self, client: TestClient):
        r = client.get("/api/compute/panchanga_get",
                        params={"date": "2026-09-18", "location": "Atlantis"})
        assert r.status_code == 422
        assert "EXTERNAL_COMPUTATION_REQUIRED" in r.json()["detail"]

    def test_explicit_lat_lon_overrides_and_works_for_any_location(self, client: TestClient):
        r = client.get("/api/compute/panchanga_get", params={
            "date": "2026-09-18", "lat": 28.6139, "lon": 77.2090,
            "tz_offset_minutes": 330, "location": "Delhi",
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["location"]["label"] == "Delhi"
        assert d["location"]["lat"] == 28.6139

    def test_location_case_insensitive(self, client: TestClient):
        r = client.get("/api/compute/panchanga_get",
                        params={"date": "2026-09-18", "location": "BHUBANESWAR"})
        assert r.status_code == 200, r.text


# ── Source disclosure (B.10 — never claim a computation source it isn't) ───

class TestSourceDisclosure:
    def test_source_field_present_and_honest(self, client: TestClient):
        r = client.get("/api/compute/panchanga_get",
                        params={"date": "2026-09-18", "location": "Bhubaneswar"})
        d = r.json()
        assert "panchang_engine" in d["source"]


# ── EL-49 IST enrichment on the ALREADY-LIVE POST endpoints ────────────────
#
# call_panchanga_service.ts (platform/src/lib/retrieval/registry/layers/
# L0_brahmagyan/call_panchanga_service.ts) is an existing, live-wired MCP
# tool that calls POST /api/compute/panchanga and /panchanga/range directly
# and passes the `panchang` payload through verbatim. The IST-timestamp
# enrichment therefore needed to land on THOSE endpoints too (not just the
# new /panchanga_get route) to reach a tool that already ships today.

class TestExistingPostEndpointsGetIstEnrichment:
    def test_single_date_forensic_and_ist(self, client: TestClient):
        r = client.post("/api/compute/panchanga", json={
            "date": "1984-02-05", "lat": 20.27, "lon": 85.84, "tz_offset_minutes": 330,
        })
        assert r.status_code == 200, r.text
        p = r.json()["panchang"]
        assert p["tithi"]["name"] == "Shukla Tritiya"
        assert p["vara"]["name"] == "Ravivara"
        assert p["yoga"]["name"] == "Shiva"
        assert p["karana_first"]["name"] == "Garaja"
        assert p["tithi"]["end_ist"].endswith("+05:30")
        assert p["sunrise_ist"].endswith("+05:30")

    def test_range_endpoint_ist_enrichment(self, client: TestClient):
        r = client.post("/api/compute/panchanga/range", json={
            "date_from": "2026-09-17", "date_to": "2026-09-19",
            "lat": 20.27, "lon": 85.84, "tz_offset_minutes": 330,
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["count"] == 3
        for day in d["panchangs"]:
            assert day["tithi"]["end_ist"].endswith("+05:30")
            assert day["sunrise_ist"].endswith("+05:30")
            assert day["hora"][0]["start_ist"].endswith("+05:30")

    def test_field_projection_still_works_with_enrichment(self, client: TestClient):
        r = client.post("/api/compute/panchanga", json={
            "date": "2026-09-18", "lat": 20.27, "lon": 85.84, "tz_offset_minutes": 330,
            "fields": ["tithi", "vara"],
        })
        assert r.status_code == 200, r.text
        p = r.json()["panchang"]
        assert set(p.keys()) == {"tithi", "vara"}
        assert p["tithi"]["end_ist"].endswith("+05:30")

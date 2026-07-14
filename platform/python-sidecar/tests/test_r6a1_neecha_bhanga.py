"""
test_r6a1_neecha_bhanga.py — R6A.1: generic bhanga evaluator + NBRY rules.

Covers:
  1. Unit tests per NBRY rule (synthetic per-varga positions).
  2. The GOLDEN-GATE tests — narrative correction (Ring-2 review): the
     native's REAL chart (Aries lagna, Sun=Capricorn per FORENSIC canon)
     already has Saturn's neecha-bhanga redeemed by rule 2 in D1 ALONE —
     Capricorn is the 10th sign from Aries, a kendra. The D9 navamsha
     extension is NOT what redeems the real chart; it is a separate,
     additional classical mechanism this phase also implements, verified
     here with an engineered SYNTHETIC fixture (D1 cancellers deliberately
     absent) so the D9 path is independently exercised. Do not conflate the
     two: `TestGoldenGateSyntheticD9Extension` proves the D9-extension
     *mechanism* works; `TestGoldenGateRealNativeShape` proves what the
     real chart's own D1 configuration actually does. An optional
     read-only DB integration test (`TestGoldenGateRealChartIntegration`)
     settles this against the real `chart_facts`/`chart_divisionals` rows
     for chart 482012f1 when a DB is reachable; it skips (not fails) when
     no DATABASE_URL is configured in this environment.
  3. Negative control: an uncancelled debilitation stays uncancelled
     (no false positives).
  4. Generic evaluator floor discipline: unregistered yogas keep the honest
     NULL + reason; NBRY rule 5 is floored (never fires).

Sections 1, 3, 4 and the synthetic half of section 2 are pure deterministic
functions — no DB, no LLM. The integration test in section 2 performs
READ-ONLY SELECTs against chart_id 482012f1-710e-4a25-994a-93821f5871aa —
no writes, no rebuild — and only when DATABASE_URL is set.
"""
from __future__ import annotations

import os
import pathlib

import pytest

from ga_writers.ga_yoga_writer import (
    NBRY_CANONICAL_ID,
    NBRY_RULE_5_FLOOR_REASON,
    ChartState,
    _d1_positions_from_state,
    _load_chart_facts,
    _load_d9_positions,
    detect_neecha_bhanga,
    evaluate_bhanga,
    evaluate_nbry,
    nbry_rule_1_dispositor_kendra,
    nbry_rule_2_exaltation_lord_kendra,
    nbry_rule_3_lord_aspect,
    nbry_rule_4_conjunct_exaltation_graha,
    nbry_rule_5_mutual_kendra_floored,
)

# ── Helpers ────────────────────────────────────────────────────────────────────
# positions shape: {planet: {"sign": lowercase, "house": int 1-12 from lagna}}.
# Saturn's debilitation sign is Aries; the graha exalted in Aries is the Sun;
# the lord (dispositor) of Aries is Mars; Saturn's exaltation sign is Libra,
# whose lord is Venus.


def _saturn_debilitated_base() -> dict:
    """Saturn in Aries in house 2 (i.e. Pisces lagna) with all potential
    cancellers parked in non-triggering places:
      - Mars (dispositor of Aries) in house 3: not a kendra from lagna; Moon in
        house 2 → Mars is 2nd from Moon (not kendra); Mars aspects 4/7/8 from
        house 3 → houses 6/9/10, not Saturn's house 2.
      - Sun (exalted in Aries) in house 3: not kendra from lagna, 2nd from
        Moon, not conjunct Saturn.
      - Venus (lord of Libra) in house 5: aspects 7th → house 11, not house 2.
      - Moon in house 2 (conjunct Saturn — Moon is not a canceller for Saturn).
    """
    return {
        "saturn": {"sign": "aries", "house": 2},
        "moon": {"sign": "aries", "house": 2},
        "mars": {"sign": "taurus", "house": 3},
        "sun": {"sign": "taurus", "house": 3},
        "venus": {"sign": "cancer", "house": 5},
        "mercury": {"sign": "capricorn", "house": 11},
        "jupiter": {"sign": "sagittarius", "house": 10},
    }


# ── 1. Per-rule unit tests ─────────────────────────────────────────────────────

class TestNbryRule1DispositorKendra:
    def test_fires_when_dispositor_in_kendra_from_lagna(self):
        pos = _saturn_debilitated_base()
        pos["mars"] = {"sign": "libra", "house": 7}  # kendra from lagna
        hit = nbry_rule_1_dispositor_kendra("saturn", pos)
        assert hit is not None
        assert hit["rule_id"] == "nbry_rule_1_dispositor_kendra"
        assert hit["supporting_planets"] == ["mars"]
        assert "lagna" in hit["kendra_basis"]
        assert hit["citation_ref"] and hit["citation_human"]

    def test_fires_when_dispositor_in_kendra_from_moon_only(self):
        pos = _saturn_debilitated_base()
        # Moon in house 2; Mars in house 5 → 4th from Moon (kendra), and house
        # 5 is not a kendra from lagna.
        pos["mars"] = {"sign": "cancer", "house": 5}
        hit = nbry_rule_1_dispositor_kendra("saturn", pos)
        assert hit is not None
        assert hit["kendra_basis"] == ["moon"]

    def test_does_not_fire_otherwise(self):
        assert nbry_rule_1_dispositor_kendra("saturn", _saturn_debilitated_base()) is None


class TestNbryRule2ExaltationLordKendra:
    def test_fires_when_exaltation_graha_in_kendra_from_lagna(self):
        pos = _saturn_debilitated_base()
        pos["sun"] = {"sign": "capricorn", "house": 10}  # kendra from lagna
        hit = nbry_rule_2_exaltation_lord_kendra("saturn", pos)
        assert hit is not None
        assert hit["rule_id"] == "nbry_rule_2_exaltation_lord_kendra"
        assert hit["supporting_planets"] == ["sun"]
        assert hit["citation_ref"] and hit["citation_human"]

    def test_fires_via_navamsha_extension_only(self):
        pos = _saturn_debilitated_base()  # Sun NOT in D1 kendra from lagna/moon
        d9 = {"sun": {"sign": "cancer", "house": 4}}  # kendra from D9 lagna
        assert nbry_rule_2_exaltation_lord_kendra("saturn", pos) is None
        hit = nbry_rule_2_exaltation_lord_kendra("saturn", pos, navamsa_positions=d9)
        assert hit is not None
        assert hit["varga_context"] == "D9"
        assert hit["kendra_basis"] == ["d9_lagna"]
        assert "navamsha" in hit["citation_human"].lower() or "navamsha" in hit["citation_ref"]

    def test_does_not_fire_otherwise(self):
        pos = _saturn_debilitated_base()
        d9 = {"sun": {"sign": "leo", "house": 5}}  # NOT a kendra from D9 lagna
        assert nbry_rule_2_exaltation_lord_kendra("saturn", pos, navamsa_positions=d9) is None


class TestNbryRule3LordAspect:
    def test_fires_when_dispositor_aspects_debilitated_planet(self):
        pos = _saturn_debilitated_base()
        # Mars in house 7 → special 8th aspect reaches house 2 (7+8-1=14→2).
        pos["mars"] = {"sign": "libra", "house": 7}
        hit = nbry_rule_3_lord_aspect("saturn", pos)
        assert hit is not None
        assert "mars" in hit["supporting_planets"]
        assert hit["citation_ref"] and hit["citation_human"]

    def test_fires_when_exaltation_sign_lord_aspects(self):
        pos = _saturn_debilitated_base()
        # Venus (lord of Libra, Saturn's exaltation sign) in house 8 →
        # 7th aspect reaches house 2.
        pos["venus"] = {"sign": "libra", "house": 8}
        hit = nbry_rule_3_lord_aspect("saturn", pos)
        assert hit is not None
        assert "venus" in hit["supporting_planets"]

    def test_conjunction_is_not_an_aspect(self):
        pos = _saturn_debilitated_base()
        pos["mars"] = {"sign": "aries", "house": 2}  # conjunct, not aspecting
        assert nbry_rule_3_lord_aspect("saturn", pos) is None

    def test_does_not_fire_otherwise(self):
        assert nbry_rule_3_lord_aspect("saturn", _saturn_debilitated_base()) is None


class TestNbryRule4ConjunctExaltationGraha:
    def test_fires_when_conjunct(self):
        pos = _saturn_debilitated_base()
        pos["sun"] = {"sign": "aries", "house": 2}  # with Saturn
        hit = nbry_rule_4_conjunct_exaltation_graha("saturn", pos)
        assert hit is not None
        assert hit["supporting_planets"] == ["sun"]
        assert hit["citation_ref"] and hit["citation_human"]

    def test_does_not_fire_otherwise(self):
        assert nbry_rule_4_conjunct_exaltation_graha("saturn", _saturn_debilitated_base()) is None


class TestNbryRule5Floored:
    def test_rule_5_is_floored_never_fires(self):
        # Even in a configuration where the mutual-kendra pattern holds
        # (Mars house 1, Sun house 4 → mutual kendra), rule 5 returns the
        # explicit floor, not a firing — B.10 citation discipline.
        pos = _saturn_debilitated_base()
        pos["mars"] = {"sign": "pisces", "house": 1}
        pos["sun"] = {"sign": "gemini", "house": 4}
        out = nbry_rule_5_mutual_kendra_floored("saturn", pos)
        assert out["floored"] is True
        assert out["floor_reason"] == NBRY_RULE_5_FLOOR_REASON
        # And it never contributes to a detection:
        findings = detect_neecha_bhanga(pos)
        for f in findings:
            assert all(r["rule_id"] != "nbry_rule_5_mutual_kendra" for r in f["rules_fired"])
            assert f["rules_floored"][0]["floored"] is True


# ── 2. Golden gate — the native's catch is the test ───────────────────────────

class TestGoldenGateSyntheticD9Extension:
    """SYNTHETIC fixture (not the real chart) engineered so every D1
    canceller is deliberately absent and only the D9 navamsha extension of
    rule 2 can redeem Saturn's debilitation. This proves the D9-extension
    *mechanism* fires correctly in isolation — it does NOT claim this is
    how the real native chart's Saturn gets redeemed (see
    TestGoldenGateRealNativeShape below for that)."""

    def _synthetic_d9_only_shape(self):
        d1 = {
            # Aries lagna → Saturn in Aries = house 1 (debilitated).
            "saturn": {"sign": "aries", "house": 1},
            "moon": {"sign": "aquarius", "house": 11},
            # D1-side cancellers deliberately absent/quiet so the D9 path is
            # the ONLY thing that can redeem Saturn:
            # Sun in house 12 (not kendra from lagna; 2nd from Moon — not
            # kendra), Mars in house 9 (not kendra from lagna; 11th from
            # Moon; aspects 12/3/4 from house 9 — not house 1), Venus in
            # house 12 (aspects house 6 — not house 1).
            "sun": {"sign": "pisces", "house": 12},
            "mars": {"sign": "sagittarius", "house": 9},
            "venus": {"sign": "pisces", "house": 12},
            "mercury": {"sign": "aquarius", "house": 11},
            "jupiter": {"sign": "sagittarius", "house": 9},
        }
        # D9: Aries navamsha-lagna, Sun in Cancer → house 4, a kendra.
        d9 = {
            "sun": {"sign": "cancer", "house": 4},
            "moon": {"sign": "leo", "house": 5},
            "saturn": {"sign": "gemini", "house": 3},
        }
        return d1, d9

    def test_d9_extension_alone_redeems_saturn_in_synthetic_fixture(self):
        d1, d9 = self._synthetic_d9_only_shape()
        bhanga_active, rule_fired, citation_ref, citation_human, findings = evaluate_nbry(d1, d9)
        assert bhanga_active is True
        assert rule_fired is not None
        assert "nbry_rule_2_exaltation_lord_kendra" in rule_fired
        assert "saturn@D1->D9" in rule_fired
        # A real citation must be present — not None (hard gate).
        assert citation_ref is not None and citation_ref != ""
        assert citation_human is not None and "Raja Yoga" in citation_human
        saturn_findings = [f for f in findings if f["planet"] == "saturn" and f["varga"] == "D1"]
        assert len(saturn_findings) == 1
        assert saturn_findings[0]["debilitation_sign"] == "aries"

    def test_d9_extension_via_generic_evaluator(self):
        d1, d9 = self._synthetic_d9_only_shape()
        out = evaluate_bhanga(NBRY_CANONICAL_ID, d1_positions=d1, d9_positions=d9)
        assert out["bhanga_active"] is True
        assert "nbry_rule_2_exaltation_lord_kendra" in out["bhanga_rule_fired"]
        assert out["citation_ref"] is not None
        assert out["bhanga_na_reason"] is None


class TestGoldenGateRealNativeShape:
    """The REAL native chart's actual configuration per this project's
    FORENSIC canon (CLAUDE.md §B): Lagna = Aries, Sun = Capricorn (all 5
    ayanamshas). Capricorn is the 10th sign counted from Aries — a kendra —
    so rule 2 fires from D1 ALONE for the real chart; the D9 extension
    (tested above) is not required to redeem the real chart's Saturn. This
    is the accurate account of "the native's catch": the underlying defect
    (Y-5: no bhanga evaluation existed at all) would have missed this D1
    redemption too, not only a D9-only case."""

    def test_real_native_d1_capricorn_sun_redeems_saturn_via_rule_2(self):
        d1 = {
            "saturn": {"sign": "aries", "house": 1},        # Aries lagna → house 1, debilitated
            "sun": {"sign": "capricorn", "house": 10},       # FORENSIC: Sun=Capricorn = 10th from Aries (kendra)
            "moon": {"sign": "aquarius", "house": 11},       # Purva Bhadrapada -> Aquarius
            "mars": {"sign": "sagittarius", "house": 9},
            "venus": {"sign": "pisces", "house": 12},
            "mercury": {"sign": "aquarius", "house": 11},
            "jupiter": {"sign": "sagittarius", "house": 9},
        }
        bhanga_active, rule_fired, citation_ref, _, findings = evaluate_nbry(d1, None)
        assert bhanga_active is True
        assert "saturn@D1:nbry_rule_2_exaltation_lord_kendra" in rule_fired
        assert citation_ref is not None
        assert findings[0]["varga"] == "D1"  # redeemed in D1 alone — no D9 data needed


class TestGoldenGateRealChartIntegration:
    """Optional read-only integration test against the REAL chart_facts /
    chart_divisionals rows for chart_id 482012f1-710e-4a25-994a-93821f5871aa
    (the native's canonical chart). Exercises the actual production
    build-path helpers (_load_chart_facts, ChartState, _d1_positions_from_state,
    _load_d9_positions, evaluate_nbry) against real data instead of synthetic
    fixtures. READ-ONLY: only SELECTs are issued, no writes, no rebuild.

    Skips (does not fail) when no DATABASE_URL is configured — this
    environment has no reachable DB, so the test is expected to skip here;
    it is left in place to run wherever a DB is reachable (CI, conductor
    review, etc.), settling the golden-gate question against real data.
    """

    CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

    def _get_conn(self):
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            env_file = pathlib.Path(__file__).resolve().parents[1] / ".env.local"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                        db_url = line.split("=", 1)[1].strip()
                        break
        if not db_url:
            pytest.skip("DATABASE_URL not set — skipping live read-only DB integration test")
        import psycopg
        return psycopg.connect(db_url)

    def test_production_path_against_real_chart_facts(self):
        conn = self._get_conn()
        try:
            facts = _load_chart_facts(conn, self.CHART_ID, "lahiri_chitrapaksha")
            if not facts:
                pytest.skip(
                    "chart_facts empty for chart 482012f1/lahiri_chitrapaksha in this "
                    "DB — cannot run the real-data integration assertion"
                )
            state = ChartState(facts)
            d1_positions = _d1_positions_from_state(state)
            d9_positions = _load_d9_positions(conn, self.CHART_ID, "lahiri_chitrapaksha")

            assert state.lagna_sign == "aries", (
                f"FORENSIC anchor violated: expected Aries lagna, got {state.lagna_sign}"
            )
            assert d1_positions.get("sun", {}).get("sign") == "capricorn", (
                f"FORENSIC anchor violated: expected Sun in Capricorn, got "
                f"{d1_positions.get('sun')}"
            )

            bhanga_active, rule_fired, citation_ref, _, findings = evaluate_nbry(
                d1_positions, d9_positions or None,
            )
            saturn_debilitated_d1 = (
                d1_positions.get("saturn", {}).get("sign") == "aries"
            )
            if saturn_debilitated_d1:
                assert bhanga_active is True, (
                    "Real chart has Saturn debilitated in D1 (Aries) but evaluate_nbry "
                    "found no cancelling rule — this is the exact production bug this "
                    "phase fixes"
                )
                assert "saturn" in rule_fired
                assert citation_ref is not None
        finally:
            conn.close()


# ── 3. Negative controls — no false positives ─────────────────────────────────

class TestNegativeControls:
    def test_uncancelled_debilitation_stays_uncancelled(self):
        pos = _saturn_debilitated_base()
        d9 = {"sun": {"sign": "leo", "house": 5}}  # no D9 kendra either
        bhanga_active, rule_fired, ref, human, findings = evaluate_nbry(pos, d9)
        assert bhanga_active is not True
        assert bhanga_active is None  # yoga does not form → no verdict row
        assert rule_fired is None and ref is None and human is None
        assert findings == []

    def test_no_debilitated_planet_no_finding(self):
        pos = {
            "sun": {"sign": "leo", "house": 1},
            "moon": {"sign": "taurus", "house": 10},
            "saturn": {"sign": "libra", "house": 3},
        }
        assert detect_neecha_bhanga(pos) == []
        assert evaluate_nbry(pos, None)[0] is None

    def test_debilitation_in_d9_only_is_detected_per_varga(self):
        # Saturn fine in D1, debilitated in D9 with dispositor Mars in D9
        # kendra → a D9-context finding.
        d1 = {"saturn": {"sign": "capricorn", "house": 1}}
        d9 = {
            "saturn": {"sign": "aries", "house": 2},
            "mars": {"sign": "cancer", "house": 7},  # kendra from D9 lagna
        }
        bhanga_active, rule_fired, _, _, findings = evaluate_nbry(d1, d9)
        assert bhanga_active is True
        assert "saturn@D9:nbry_rule_1_dispositor_kendra" in rule_fired
        assert findings[0]["varga"] == "D9"


# ── 4. Generic evaluator floor discipline ─────────────────────────────────────

class TestGenericEvaluatorFloor:
    def test_unregistered_yoga_with_catalog_cancellation_floors_honestly(self):
        out = evaluate_bhanga(
            "gajakesari", d1_positions={}, has_catalog_cancellation=True,
        )
        assert out["bhanga_active"] is None
        assert out["bhanga_rule_fired"] is None
        assert "not evaluated by ga_yoga_writer" in out["bhanga_na_reason"]
        assert "B.10" in out["bhanga_na_reason"]

    def test_unregistered_yoga_without_catalog_cancellation(self):
        # budha_aditya is no longer a valid "unregistered" example — Lane 3
        # (Night-1) registered a real combustion-based cancellation for it
        # (see test_lane3_detector_registry.py). Use a yoga with no
        # registered handler and no catalog cancellation instead.
        out = evaluate_bhanga("kendra_trikona_raja_yoga", d1_positions={})
        assert out["bhanga_active"] is None
        assert out["bhanga_na_reason"] == (
            "no classical bhanga (cancellation) rule exists for this yoga type"
        )

    def test_budha_aditya_now_has_a_real_registered_cancellation(self):
        # Lane 3 (Night-1): budha_aditya moved from the honest-NULL floor to
        # a real combustion-based verdict via _BHANGA_EVALUATORS.
        out = evaluate_bhanga("budha_aditya", d1_positions={}, special_states={"mercury": {"is_combust": False}})
        assert out["bhanga_active"] is False
        out2 = evaluate_bhanga("budha_aditya", d1_positions={}, special_states={"mercury": {"is_combust": True}})
        assert out2["bhanga_active"] is True
        assert out2["bhanga_rule_fired"] == "mercury_combust"

    def test_every_shipped_nbry_rule_has_a_citation(self):
        from ga_writers.ga_yoga_writer import NBRY_CITATIONS
        for rule_id, (ref, human) in NBRY_CITATIONS.items():
            assert ref, rule_id
            assert human and ("BPHS" in human or "Phaladeepika" in human), rule_id


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))

"""
test_lane3_deliverable_c_dosha_cancellation.py — Night-1 Lane 3 Deliverable C
==============================================================================
Covers 00_ARCHITECTURE/llm_consumption_audit/briefs/night1/LANE3_DETECTOR_REGISTRY.md
§1.3 (dosha cancellation-checks, CR-72/73/74) — the reconciliation-pass
deliverable Lane 3 originally HELD pending ga_vichara (L2), which is now
merged.

Doctrine under test (register CR-73): no dosha may fire without its
negative/cancelling condition being evaluated. Specimens:
  - Kemadruma x Anapha mutual exclusion (CR-73 primary specimen): Mercury
    (a non-luminary) in the 12th-from-Moon means Anapha's own arithmetic
    precondition holds, which is EXACTLY Kemadruma's cancelling condition —
    by construction the two can never both hold for the same chart.
  - Daridra cancellation by a strong 11th lord / fired dhana structure
    (CR-73's second specimen): "daridra fires despite an exalted 11L,
    own-sign dhana-karaka, and 2L in the 9th" — the cancellation must catch
    this, wired through ga_vichara's varga_ratification (11L strength) and
    ga_yoga_firings (dhana structure), never re-derived.
  - Kala Sarpa label agreement with the genuinely-computed
    kala_sarpa_per_varga fact (CR-74): no second detector.
  - Registry hygiene: every BESPOKE_DOSHA_DETECTORS id has a matching
    DOSHA_CANCELLATIONS callable.
  - Decorative-stub gating (CR-72): a `requires_pass` catalog dosha is never
    served as a firing — it carries an explicit `catalog_only`/`fires:null`
    marker instead.

Pure deterministic functions — no live DB, no LLM. Fake cursor stand-ins
supply canned chart_vichara / ga_yoga_firings rows where a test needs them.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import ga_writers.ga_structural_writer as sut
from test_ga8_writer import (
    MOCK_CHART_OUTPUT,
    CHART_ID,
    BUILD_ID,
    AY_ID,
    ENG_VER,
    COMPUTED_AT,
    NULL_CONN,
)


# ── Fake conn/cursor helpers ─────────────────────────────────────────────────

class _CannedCursor:
    """Cursor stand-in whose fetchone/fetchall are driven by which table the
    executed SQL names — mirrors test_ga8_writer._StrengthFakeCursor's
    pattern. `vichara_row` / `yoga_rows` are injected per-test."""

    def __init__(self, vichara_row=None, yoga_rows=None):
        self._last_query = ""
        self._vichara_row = vichara_row
        self._yoga_rows = yoga_rows or []

    def execute(self, query, params=None):
        self._last_query = query

    def fetchone(self):
        if "chart_vichara" in self._last_query:
            return self._vichara_row
        if "chart_facts" in self._last_query:
            return None  # _real_fact_id_ref: no constituent lookups in these tests
        return None

    def fetchall(self):
        if "ga_yoga_firings" in self._last_query:
            return self._yoga_rows
        return []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _CannedConn:
    def __init__(self, vichara_row=None, yoga_rows=None):
        self._vichara_row = vichara_row
        self._yoga_rows = yoga_rows or []

    def cursor(self, row_factory=None):
        return _CannedCursor(vichara_row=self._vichara_row, yoga_rows=self._yoga_rows)


def _dosha_entry(canonical_id: str, requires_text: str) -> dict:
    """Minimal brahma_dosha_catalog row shape — narrative 'requires' string,
    exactly as the live catalog stores kemadruma/daridra/kala_sarpa (verified
    via mcp postgres query against brahma_dosha_catalog 2026-07-14)."""
    return {
        "canonical_id": canonical_id,
        "name_en": canonical_id.replace("_", " ").title(),
        "formation_rule_jsonb": {"requires": requires_text},
        "classical_citations": {},
        "source_chunk_ids": [],
        "category": "dosha",
    }


def _find_row(rows: list[dict], subject: str) -> dict | None:
    return next((r for r in rows if r["fact_subject"] == subject), None)


# ── §1: Kemadruma x Anapha mutual exclusion (CR-73 primary specimen) ───────

class TestKemadrumaAnaphaMutualExclusion:
    def test_kemadruma_does_not_fire_when_anapha_condition_holds(self):
        # MOCK_CHART_OUTPUT: Moon in H11 (Aquarius); Mercury + Venus sit in
        # H10 == 12th-from-Moon (non-Sun/node planet in 12th-from-Moon is
        # exactly Anapha's own formation condition — verified against the
        # real 482012f1 chart per CR-73/CR-80: "Anapha Yoga genuinely fires
        # (Mercury in 12th-from-Moon) -> Kemadruma is FALSE").
        flank = sut._moon_flanking_planets(MOCK_CHART_OUTPUT)
        assert "Mercury" in flank["house_12th"], "fixture must reproduce the Anapha precondition"

        finding = sut._detect_kemadruma(MOCK_CHART_OUTPUT)
        assert finding is None, "Kemadruma must not form while a planet occupies the 12th-from-Moon (Anapha's own precondition)"

        rows = sut._build_dosha_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[_dosha_entry("kemadruma", "no planet in 2nd or 12th from Moon")],
        )
        assert _find_row(rows, "kemadruma") is None, "no dosha_label row may be written for a Kemadruma that never formed"

    def test_kemadruma_cancelled_by_tara_graha_in_kendra_from_moon(self):
        # Reproduces the native's chart shape (482012f1, CR-73): the Moon forms
        # Kemadruma structurally (no flanking/conjunct planet, Moon outside
        # kendra from lagna) but Jupiter sits in the 7th-from-Moon — a kendra
        # FROM THE MOON. `brahma_dosha_catalog.kemadruma` lists "any planet in
        # kendra from Moon or lagna" as a BPHS bhanga ground; the cancellation
        # must catch it (the pre-CR-73 code omitted the kendra-from-Moon ground
        # and let this fire, contradicting the Anapha/Sunapha firing authority).
        chart = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Sun", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 295.0, "retrograde": False},
                {"name": "Moon", "sign": "Gemini", "sign_id": 3, "house": 3, "longitude": 70.0, "retrograde": False},
                {"name": "Mars", "sign": "Leo", "sign_id": 5, "house": 5, "longitude": 130.0, "retrograde": False},
                {"name": "Mercury", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 300.0, "retrograde": False},
                {"name": "Jupiter", "sign": "Sagittarius", "sign_id": 9, "house": 9, "longitude": 265.0, "retrograde": False},
                {"name": "Venus", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 308.0, "retrograde": False},
                {"name": "Saturn", "sign": "Libra", "sign_id": 7, "house": 7, "longitude": 195.0, "retrograde": False},
                {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 2, "longitude": 48.0, "retrograde": True},
                {"name": "Ketu", "sign": "Scorpio", "sign_id": 8, "house": 8, "longitude": 228.0, "retrograde": True},
            ],
        }
        # Moon H3: 2nd-from-Moon=H4 (empty), 12th-from-Moon=H2 (Rahu only,
        # exempt) — no genuine flanking planet; Moon not in kendra from lagna.
        # Kendra from Moon (H3) = {H3, H6, H9, H12}: Jupiter (H9) is the 7th
        # from the Moon → a tara-graha in a kendra from the Moon → bhanga.
        finding = sut._detect_kemadruma(chart)
        assert finding is not None, "Kemadruma still FORMS structurally (no flanking, Moon outside lagna kendra)"
        verdict = sut._cancel_kemadruma(finding, chart)
        assert verdict["bhanga_active"] is True
        assert "kendra_from_moon" in verdict["bhanga_rule_fired"]
        assert "Jupiter" in verdict["bhanga_rule_fired"]

        rows = sut._build_dosha_rows(
            NULL_CONN, chart, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[_dosha_entry("kemadruma", "no planet in 2nd or 12th from Moon")],
        )
        row = _find_row(rows, "kemadruma")
        assert row is not None, "a formed-but-cancelled dosha still emits an auditable row (B.10/§N.6)"
        assert row["fact_value_jsonb"]["fires"] is False, "cancelled Kemadruma must not serve as a finding"
        assert row["fact_value_jsonb"]["bhanga_active"] is True

    def test_kemadruma_fires_only_when_no_kendra_support_at_all(self):
        # Genuinely uncancelled Kemadruma — proves the kendra-support rule
        # DISCRIMINATES (it does not simply always-cancel). All five tara-grahas
        # sit in H6/H9/H12, which are NEITHER kendras from the Moon (Moon H2 ->
        # kendras {H2,H5,H8,H11}) NOR kendras from the lagna ({H1,H4,H7,H10}),
        # and none flanks/conjoins the Moon. Sun and the nodes are exempt.
        chart = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Sun", "sign": "Pisces", "sign_id": 12, "house": 12, "longitude": 345.0, "retrograde": False},
                {"name": "Moon", "sign": "Taurus", "sign_id": 2, "house": 2, "longitude": 40.0, "retrograde": False},
                {"name": "Mars", "sign": "Virgo", "sign_id": 6, "house": 6, "longitude": 160.0, "retrograde": False},
                {"name": "Mercury", "sign": "Virgo", "sign_id": 6, "house": 6, "longitude": 165.0, "retrograde": False},
                {"name": "Jupiter", "sign": "Sagittarius", "sign_id": 9, "house": 9, "longitude": 255.0, "retrograde": False},
                {"name": "Venus", "sign": "Sagittarius", "sign_id": 9, "house": 9, "longitude": 260.0, "retrograde": False},
                {"name": "Saturn", "sign": "Pisces", "sign_id": 12, "house": 12, "longitude": 350.0, "retrograde": False},
                {"name": "Rahu", "sign": "Gemini", "sign_id": 3, "house": 3, "longitude": 75.0, "retrograde": True},
                {"name": "Ketu", "sign": "Sagittarius", "sign_id": 9, "house": 9, "longitude": 255.0, "retrograde": True},
            ],
        }
        finding = sut._detect_kemadruma(chart)
        assert finding is not None
        verdict = sut._cancel_kemadruma(finding, chart)
        assert verdict["bhanga_active"] is False, "no tara-graha in any kendra from Moon or lagna -> uncancelled"

        rows = sut._build_dosha_rows(
            NULL_CONN, chart, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[_dosha_entry("kemadruma", "no planet in 2nd or 12th from Moon")],
        )
        row = _find_row(rows, "kemadruma")
        assert row is not None
        assert row["fact_value_jsonb"]["fires"] is True
        assert row["fact_value_jsonb"]["bhanga_active"] is False


# ── §2: Daridra cancellation (CR-73 second specimen) ────────────────────────

class TestDaridraCancellation:
    def test_daridra_cancelled_by_exalted_11l_on_real_chart_shape(self):
        # MOCK_CHART_OUTPUT is Aries-lagna: 11L = Saturn, exalted in Libra
        # H7 (not a dusthana) — matches the real 482012f1 chart (CR-80).
        # Daridra's OWN formation condition (11L in dusthana OR 2L/11L
        # afflicted) is honestly false here: Saturn is exalted, not
        # debilitated/combust, and 2L Venus is neither debilitated nor
        # combust either — so the dosha never even forms.
        finding = sut._detect_daridra(MOCK_CHART_OUTPUT)
        assert finding is None, "Daridra must not form on a chart with a strong, unafflicted 2L/11L"

        rows = sut._build_dosha_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[_dosha_entry("daridra", "11th lord in dusthana or 2nd/11th lords afflicted")],
        )
        assert _find_row(rows, "daridra") is None

    def test_daridra_forms_but_is_cancelled_by_fired_dhana_structure(self):
        # Synthetic fixture where the formation condition IS genuinely true
        # (11L in a dusthana) so the cancellation logic actually executes —
        # CR-73's "daridra fires despite ... an own-sign dhana-karaka, and
        # 2L in the 9th" specimen: a fired dhana-family yoga involving the
        # 2L/11L/9L must cancel it.
        chart = {
            "ascendant": {"sign": "Cancer", "sign_id": 4, "longitude": 100.0},
            "grahas": [
                # H11 from Cancer lagna = Taurus -> Venus is 11L.
                # Put Venus (11L) in H8 (dusthana) to satisfy formation.
                {"name": "Venus", "sign": "Sagittarius", "sign_id": 9, "house": 8, "longitude": 250.0, "retrograde": False},
                # H2 from Cancer lagna = Leo -> Sun is 2L; keep unafflicted.
                {"name": "Sun", "sign": "Aries", "sign_id": 1, "house": 10, "longitude": 10.0, "retrograde": False},
                {"name": "Moon", "sign": "Cancer", "sign_id": 4, "house": 1, "longitude": 100.0, "retrograde": False},
                {"name": "Mars", "sign": "Capricorn", "sign_id": 10, "house": 7, "longitude": 280.0, "retrograde": False},
                {"name": "Mercury", "sign": "Pisces", "sign_id": 12, "house": 9, "longitude": 340.0, "retrograde": False},
                {"name": "Jupiter", "sign": "Libra", "sign_id": 7, "house": 4, "longitude": 190.0, "retrograde": False},
                {"name": "Saturn", "sign": "Aquarius", "sign_id": 11, "house": 8, "longitude": 310.0, "retrograde": False},
                {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 11, "longitude": 48.0, "retrograde": True},
                {"name": "Ketu", "sign": "Scorpio", "sign_id": 8, "house": 5, "longitude": 228.0, "retrograde": True},
            ],
        }
        finding = sut._detect_daridra(chart)
        assert finding is not None, "11L Venus in H8 (dusthana) must satisfy Daridra's own formation condition"
        assert finding["lord11"] == "Venus"

        # No vichara row (11L not exalted per ga_vichara or D1) but a fired
        # dhana-family yoga names the 2L/9L/11L.
        conn = _CannedConn(
            vichara_row=None,
            yoga_rows=[("dhana_yoga_house_lords", '["sun", "mercury", "venus"]')],
        )
        verdict = sut._cancel_daridra(finding, chart, conn, CHART_ID, AY_ID)
        assert verdict["bhanga_active"] is True
        assert "dhana_structure_fires" in verdict["bhanga_rule_fired"]

        rows = sut._build_dosha_rows(
            conn, chart, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[_dosha_entry("daridra", "11th lord in dusthana or 2nd/11th lords afflicted")],
        )
        row = _find_row(rows, "daridra")
        assert row is not None, "a formed-but-cancelled dosha still writes an 'evaluated, cancelled-by' row"
        vj = row["fact_value_jsonb"]
        assert vj["fires"] is False
        assert vj["bhanga_active"] is True
        assert "dhana_structure_fires" in vj["bhanga_rule_fired"]

    def test_daridra_cancelled_by_ga_vichara_exalted_11l_signal(self):
        """Wires ga_vichara's varga_ratification (domain=wealth) output — the
        exact dependency Lane 3 held Deliverable C for."""
        chart = {
            "ascendant": {"sign": "Cancer", "sign_id": 4, "longitude": 100.0},
            "grahas": [
                {"name": "Venus", "sign": "Sagittarius", "sign_id": 9, "house": 8, "longitude": 250.0, "retrograde": False},
                {"name": "Sun", "sign": "Aries", "sign_id": 1, "house": 10, "longitude": 10.0, "retrograde": False},
                {"name": "Moon", "sign": "Cancer", "sign_id": 4, "house": 1, "longitude": 100.0, "retrograde": False},
                {"name": "Mars", "sign": "Capricorn", "sign_id": 10, "house": 7, "longitude": 280.0, "retrograde": False},
                {"name": "Mercury", "sign": "Pisces", "sign_id": 12, "house": 9, "longitude": 340.0, "retrograde": False},
                {"name": "Jupiter", "sign": "Libra", "sign_id": 7, "house": 4, "longitude": 190.0, "retrograde": False},
                {"name": "Saturn", "sign": "Aquarius", "sign_id": 11, "house": 8, "longitude": 310.0, "retrograde": False},
                {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 11, "longitude": 48.0, "retrograde": True},
                {"name": "Ketu", "sign": "Scorpio", "sign_id": 8, "house": 5, "longitude": 228.0, "retrograde": True},
            ],
        }
        finding = sut._detect_daridra(chart)
        assert finding is not None

        conn = _CannedConn(
            vichara_row=(1.4, {"d1_dignity": "exalted", "n_agree": 3, "n_oppose": 0}),
            yoga_rows=[],
        )
        verdict = sut._cancel_daridra(finding, chart, conn, CHART_ID, AY_ID)
        assert verdict["bhanga_active"] is True
        assert "ga_vichara" in verdict["bhanga_rule_fired"]


# ── §3: Kala Sarpa label agreement with the computed fact (CR-74) ──────────

class TestKalaSarpaLabelAgreement:
    def test_kala_sarpa_label_matches_genuine_computed_verdict_none_on_forensic_chart(self):
        # MOCK_CHART_OUTPUT: Rahu H2 / Ketu H8, with Mars in H1 (not H7 as
        # the live 482012f1 chart has) — regardless of exact placement, the
        # dosha_label wiring must always AGREE with _detect_kala_sarpa's own
        # verdict for the same chart_output, by construction.
        expected = sut._detect_kala_sarpa(sut._extract_chart_state(MOCK_CHART_OUTPUT))
        finding = sut._detect_kala_sarpa_dosha(MOCK_CHART_OUTPUT)
        if expected["fires"] and expected["variant"] == "kala_sarpa":
            assert finding is not None
        else:
            assert finding is None

        rows = sut._build_dosha_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[_dosha_entry("kala_sarpa", "all 7 planets hemmed between Rahu and Ketu")],
        )
        row = _find_row(rows, "kala_sarpa")
        if finding is None:
            assert row is None
        else:
            assert row is not None
            assert row["fact_value_jsonb"]["fires"] is True

    def test_kala_sarpa_fires_and_agrees_when_all_seven_hemmed(self):
        chart = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Rahu", "sign": "Aries", "sign_id": 1, "house": 1, "longitude": 10.0, "retrograde": True},
                {"name": "Ketu", "sign": "Libra", "sign_id": 7, "house": 7, "longitude": 190.0, "retrograde": True},
                {"name": "Sun", "sign": "Taurus", "sign_id": 2, "house": 2, "longitude": 40.0, "retrograde": False},
                {"name": "Moon", "sign": "Gemini", "sign_id": 3, "house": 3, "longitude": 70.0, "retrograde": False},
                {"name": "Mars", "sign": "Cancer", "sign_id": 4, "house": 4, "longitude": 100.0, "retrograde": False},
                {"name": "Mercury", "sign": "Leo", "sign_id": 5, "house": 5, "longitude": 130.0, "retrograde": False},
                {"name": "Jupiter", "sign": "Virgo", "sign_id": 6, "house": 6, "longitude": 160.0, "retrograde": False},
                {"name": "Venus", "sign": "Virgo", "sign_id": 6, "house": 6, "longitude": 185.0, "retrograde": False},
                {"name": "Saturn", "sign": "Virgo", "sign_id": 6, "house": 6, "longitude": 187.0, "retrograde": False},
            ],
        }
        expected = sut._detect_kala_sarpa(sut._extract_chart_state(chart))
        assert expected["fires"] is True and expected["variant"] == "kala_sarpa"

        finding = sut._detect_kala_sarpa_dosha(chart)
        assert finding is not None

        rows = sut._build_dosha_rows(
            NULL_CONN, chart, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[_dosha_entry("kala_sarpa", "all 7 planets hemmed between Rahu and Ketu")],
        )
        row = _find_row(rows, "kala_sarpa")
        assert row is not None
        assert row["fact_value_jsonb"]["fires"] is True
        assert row["fact_value_jsonb"]["catalog_only"] is False


# ── §4: Decorative-stub gating (CR-72) ──────────────────────────────────────

class TestDecorativeStubGating:
    def test_requires_pass_catalog_dosha_is_marked_catalog_only_not_a_firing(self):
        """A catalog dosha whose formation_rule_jsonb is a STRUCTURED
        'requires' list where every clause vacuously passes (no dignity/
        house_class narrowing) — the CR-72 decorative-stub shape — must
        never be served as `fires: true`."""
        entry = {
            "canonical_id": "vacuous_stub_dosha",
            "name_en": "Vacuous Stub Dosha",
            "formation_rule_jsonb": {"requires": [{"planet": "moon"}]},
            "classical_citations": {},
            "source_chunk_ids": [],
            "category": "dosha",
        }
        rows = sut._build_dosha_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[entry],
        )
        row = _find_row(rows, "vacuous_stub_dosha")
        assert row is not None
        vj = row["fact_value_jsonb"]
        assert vj["catalog_only"] is True
        assert vj["fires"] is None
        assert vj["fire_reason"] == "requires_pass"

    def test_narrative_string_requires_dosha_produces_no_row_at_all(self):
        """A dosha whose 'requires' is an unstructured narrative string
        (the real brahma_dosha_catalog shape for most classical doshas)
        fails closed via _evaluate_catalog_rule — honest silence, not a
        decorative stub."""
        entry = _dosha_entry("pitru_dosha", "Sun/9th-house/9th-lord afflicted by Rahu/Ketu/Saturn")
        rows = sut._build_dosha_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[entry],
        )
        assert _find_row(rows, "pitru_dosha") is None


# ── §5: Registry hygiene ────────────────────────────────────────────────────

class TestRegistryHygiene:
    def test_every_bespoke_detector_has_a_cancellation_callable(self):
        for dosha_id in sut.BESPOKE_DOSHA_DETECTORS:
            assert dosha_id in sut.DOSHA_CANCELLATIONS, (
                f"{dosha_id} has a bespoke detector but no registered cancellation callable"
            )
            assert callable(sut.DOSHA_CANCELLATIONS[dosha_id])

    def test_bespoke_detector_ids_match_expected_set(self):
        # D-2 Lane V-6 (CR-73 completion): the 12 named Kala Sarpa variants
        # (Anant..Sheshnag) were added as bespoke detectors, each narrowing
        # the base `kala_sarpa` verdict to a specific Rahu house — no second
        # detector, per this file's own CR-74 non-duplication precedent
        # (see `_make_kala_sarpa_named_variant_detector` in
        # ga_structural_writer.py). Expected set grows from 3 to 15.
        expected = {"kemadruma", "daridra", "kala_sarpa"} | {
            f"kala_sarpa_{v}" for v in (
                "anant", "kulik", "vasuki", "shankhpal", "padma", "mahapadma",
                "takshak", "karkotak", "shankhachud", "ghatak", "vishdhar", "sheshnag",
            )
        }
        assert set(sut.BESPOKE_DOSHA_DETECTORS) == expected


# ── §6: Real dict_row regression guard (Night-1 post-merge production fix) ──
#
# Discovered during the guarded rebuild against real chart data: the
# orchestrator's DB connection uses psycopg3's dict_row factory (pipeline/
# orchestrator/db.py), so every cursor row is dict-like — NOT a tuple. The
# §1-§5 tests above all mock rows as tuples (_CannedCursor.fetchone/fetchall),
# which never exercises this path and is exactly why this bug reached a real
# rebuild before it reached a test. These tests use dict-shaped fake rows to
# close that gap.

class _DictRowCursor:
    """Cursor stand-in returning psycopg3 dict_row-shaped rows (plain dicts
    keyed by column name) — the real orchestrator shape, as opposed to
    _CannedCursor's tuple rows."""

    def __init__(self, vichara_row=None, yoga_rows=None):
        self._last_query = ""
        self._vichara_row = vichara_row
        self._yoga_rows = yoga_rows or []

    def execute(self, query, params=None):
        self._last_query = query

    def fetchone(self):
        if "chart_vichara" in self._last_query:
            return self._vichara_row
        return None

    def fetchall(self):
        if "ga_yoga_firings" in self._last_query:
            return self._yoga_rows
        return []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _DictRowConn:
    def __init__(self, vichara_row=None, yoga_rows=None):
        self._vichara_row = vichara_row
        self._yoga_rows = yoga_rows or []

    def cursor(self, row_factory=None):
        return _DictRowCursor(vichara_row=self._vichara_row, yoga_rows=self._yoga_rows)


# ── §7: S-2(d) — constituent_facts_array grounding (kills the shared-stub) ──
#
# CR-72's original defect: all 22 dosha_label rows shared ONE constituent
# fact_id. §1-§6 above fixed `fires`/`bhanga_active` genuinely-computed, but
# `_get_catalog_constituent_fact_ids` still resolved the SAME SUN/sign
# fact_id for every bespoke dosha (kemadruma/daridra/kala_sarpa all store
# their catalog "requires" as a narrative string, so the structured-list
# branch never matches and every one falls through to the single hardcoded
# SUN/sign fallback) — a shared-stub bug reappearing one layer down from the
# one CR-72 named. These tests pin the fix: each bespoke dosha's
# constituent_facts_array must be grounded in ITS OWN finding's
# constituent_planets, not a single chart-wide fallback fact.

class _PerPlanetFactCursor:
    """Cursor stand-in returning a distinct, deterministic fact_id per
    (fact_subject, fact_key) pair — mirrors real chart_facts uniqueness
    (each graha's each attribute has its own row/fact_id). Lets tests assert
    that two different doshas' constituent arrays are NOT identical."""

    def __init__(self):
        self._last_params = None

    def execute(self, query, params=None):
        self._last_params = params

    def fetchone(self):
        # _real_fact_id_ref params: (chart_id, ayanamsha_id, category, subject, key)
        if not self._last_params or len(self._last_params) < 5:
            return None
        _, _, category, subject, key = self._last_params
        return (f"FID::{category}::{subject}::{key}",)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _PerPlanetFactConn:
    def cursor(self, row_factory=None):
        return _PerPlanetFactCursor()


PER_PLANET_CONN = _PerPlanetFactConn()


class TestBespokeDoshaConstituentGrounding:
    def test_bespoke_resolver_grounds_on_the_findings_own_planets(self):
        """_bespoke_dosha_constituent_fact_ids must resolve fact_ids keyed to
        the finding's actual constituent_planets, not a fixed subject."""
        finding = {"constituent_planets": ["Moon"], "constituent_houses": [11]}
        fids = sut._bespoke_dosha_constituent_fact_ids(
            PER_PLANET_CONN, CHART_ID, AY_ID, finding,
        )
        assert fids, "must resolve at least one real fact_id"
        assert all("MOON" in f for f in fids), "Kemadruma must ground on Moon, not a fixed fallback subject"
        assert "SUN" not in "".join(fids)

    def test_kemadruma_and_daridra_constituent_arrays_are_not_identical(self):
        """The CR-72 defect, restated: two different doshas serving the same
        constituent_facts_array. Kemadruma grounds on Moon; Daridra (on
        MOCK_CHART_OUTPUT, Aries lagna) grounds on the 11L/2L house lords —
        different planets, so the resolved fact_id sets must differ."""
        kemadruma_finding = sut._detect_kemadruma(MOCK_CHART_OUTPUT)
        assert kemadruma_finding is None, (
            "MOCK_CHART_OUTPUT reproduces the Anapha precondition (Mercury in "
            "12th-from-Moon) — Kemadruma itself never forms here; use a chart "
            "shape where it does to compare against Daridra's grounding."
        )

        # Build a chart shape where Kemadruma DOES form (Moon isolated,
        # outside kendra) AND Daridra's own formation ground genuinely fires
        # (11L Saturn in a dusthana, H8) so both detectors can be compared
        # side by side. Aries lagna: 11th house = Aquarius -> 11L = Saturn.
        chart = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Sun", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 295.0, "retrograde": False},
                {"name": "Moon", "sign": "Gemini", "sign_id": 3, "house": 3, "longitude": 70.0, "retrograde": False},
                {"name": "Mars", "sign": "Leo", "sign_id": 5, "house": 5, "longitude": 130.0, "retrograde": False},
                {"name": "Mercury", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 300.0, "retrograde": False},
                {"name": "Jupiter", "sign": "Sagittarius", "sign_id": 9, "house": 9, "longitude": 265.0, "retrograde": False},
                {"name": "Venus", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 308.0, "retrograde": False},
                {"name": "Saturn", "sign": "Scorpio", "sign_id": 8, "house": 8, "longitude": 225.0, "retrograde": False},
                {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 2, "longitude": 48.0, "retrograde": True},
                {"name": "Ketu", "sign": "Scorpio", "sign_id": 8, "house": 8, "longitude": 228.0, "retrograde": True},
            ],
        }
        kema_finding = sut._detect_kemadruma(chart)
        assert kema_finding is not None
        dari_finding = sut._detect_daridra(chart)
        assert dari_finding is not None, "11L Saturn in H8 (dusthana) must satisfy Daridra's own formation ground"
        assert set(kema_finding["constituent_planets"]) != set(dari_finding["constituent_planets"]), (
            "fixture must exercise genuinely different constituent planets"
        )

        kema_fids = sut._bespoke_dosha_constituent_fact_ids(PER_PLANET_CONN, CHART_ID, AY_ID, kema_finding)
        dari_fids = sut._bespoke_dosha_constituent_fact_ids(PER_PLANET_CONN, CHART_ID, AY_ID, dari_finding)
        assert kema_fids, "Kemadruma must resolve real constituent fact_ids"
        assert dari_fids, "Daridra must resolve real constituent fact_ids"
        assert set(kema_fids) != set(dari_fids), (
            "CR-72 shared-stub regression: two different doshas must not serve "
            "the same constituent_facts_array"
        )

    def test_build_dosha_rows_end_to_end_no_shared_stub_across_bespoke_doshas(self):
        """Full _build_dosha_rows path (the actual served dosha_label rows):
        kemadruma/daridra/kala_sarpa, when co-firing on one chart, must not
        collapse onto the generic SUN/sign fallback fact_id."""
        chart = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Sun", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 295.0, "retrograde": False},
                {"name": "Moon", "sign": "Gemini", "sign_id": 3, "house": 3, "longitude": 70.0, "retrograde": False},
                {"name": "Mars", "sign": "Leo", "sign_id": 5, "house": 5, "longitude": 130.0, "retrograde": False},
                {"name": "Mercury", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 300.0, "retrograde": False},
                {"name": "Jupiter", "sign": "Sagittarius", "sign_id": 9, "house": 9, "longitude": 265.0, "retrograde": False},
                {"name": "Venus", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 308.0, "retrograde": False},
                {"name": "Saturn", "sign": "Libra", "sign_id": 7, "house": 7, "longitude": 195.0, "retrograde": False},
                {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 2, "longitude": 48.0, "retrograde": True},
                {"name": "Ketu", "sign": "Scorpio", "sign_id": 8, "house": 8, "longitude": 228.0, "retrograde": True},
            ],
        }
        rows = sut._build_dosha_rows(
            PER_PLANET_CONN, chart, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[
                _dosha_entry("kemadruma", "no planet in 2nd or 12th from Moon"),
                _dosha_entry("daridra", "11th lord in dusthana or 2nd/11th lords afflicted"),
            ],
        )
        served = {r["fact_subject"]: r["fact_value_jsonb"]["constituent_facts_array"] for r in rows}
        assert len(served) >= 1, "fixture must produce at least one served bespoke dosha row"
        arrays = [tuple(sorted(a)) for a in served.values() if a]
        if len(arrays) >= 2:
            assert len(set(arrays)) == len(arrays), (
                f"two dosha_label rows served the identical constituent_facts_array "
                f"(the CR-72 shared-stub regression): {served}"
            )
        for name, fids in served.items():
            assert fids, f"{name} dosha_label row must carry real constituent fact_ids, not an empty array"


class TestDictRowRegressionGuard:
    def test_dhana_yoga_fires_for_handles_dict_rows_not_just_tuples(self):
        conn = _DictRowConn(
            yoga_rows=[{"yoga_canonical_id": "dhana_yoga_house_lords", "constituent_planets": '["sun", "mercury", "venus"]'}],
        )
        hits = sut._dhana_yoga_fires_for(conn, CHART_ID, AY_ID, {"Venus"})
        assert hits == ["dhana_yoga_house_lords"], (
            "must extract yoga_canonical_id/constituent_planets by column name from a "
            "dict_row-shaped row; a bare row[0]/row[1] raises KeyError: 0 against a dict"
        )

    def test_load_wealth_ratification_handles_dict_rows_not_just_tuples(self):
        conn = _DictRowConn(vichara_row={"value_num": 1.4, "value_jsonb": {"d1_dignity": "exalted"}})
        result = sut._load_wealth_ratification(conn, CHART_ID, AY_ID, "VEN")
        assert result is not None
        assert result["ratification_factor"] == 1.4
        assert result["d1_dignity"] == "exalted"

    def test_daridra_cancellation_end_to_end_with_dict_row_conn(self):
        """The exact production failure mode: _cancel_daridra invoked with a
        real dict_row connection, dhana structure fired, cancellation must
        succeed rather than raising KeyError: 0."""
        chart = {
            "ascendant": {"sign": "Cancer", "sign_id": 4, "longitude": 100.0},
            "grahas": [
                {"name": "Venus", "sign": "Sagittarius", "sign_id": 9, "house": 8, "longitude": 250.0, "retrograde": False},
                {"name": "Sun", "sign": "Aries", "sign_id": 1, "house": 10, "longitude": 10.0, "retrograde": False},
                {"name": "Moon", "sign": "Cancer", "sign_id": 4, "house": 1, "longitude": 100.0, "retrograde": False},
                {"name": "Mars", "sign": "Capricorn", "sign_id": 10, "house": 7, "longitude": 280.0, "retrograde": False},
                {"name": "Mercury", "sign": "Pisces", "sign_id": 12, "house": 9, "longitude": 340.0, "retrograde": False},
                {"name": "Jupiter", "sign": "Libra", "sign_id": 7, "house": 4, "longitude": 190.0, "retrograde": False},
                {"name": "Saturn", "sign": "Aquarius", "sign_id": 11, "house": 8, "longitude": 310.0, "retrograde": False},
                {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 11, "longitude": 48.0, "retrograde": True},
                {"name": "Ketu", "sign": "Scorpio", "sign_id": 8, "house": 5, "longitude": 228.0, "retrograde": True},
            ],
        }
        finding = sut._detect_daridra(chart)
        assert finding is not None
        conn = _DictRowConn(
            vichara_row=None,
            yoga_rows=[{"yoga_canonical_id": "dhana_yoga_house_lords", "constituent_planets": '["sun", "mercury", "venus"]'}],
        )
        verdict = sut._cancel_daridra(finding, chart, conn, CHART_ID, AY_ID)  # must not raise
        assert verdict["bhanga_active"] is True
        assert "dhana_structure_fires" in verdict["bhanga_rule_fired"]

"""
test_lane4_msr_elevation.py — Night-1 Doctrine Campaign, Lane 4 (MSR elevation).

Covers the six changes in 00_ARCHITECTURE/llm_consumption_audit/briefs/night1/
LANE4_MSR_ELEVATION.md:

  Change 1 (CR-81)      — class_prior activation + hit-rate bookkeeping
  Change 2 (CR-82→CR-65)— tier ceiling retirement + percentile tier assignment
  Change 3 (CR-83/CR-54)— judged valence with visible fallback tagging
  Change 4 (CR-45)      — subject-bearing headlines
  Change 5 (CR-76/77)   — position-class subject resolution
  Change 6 (CR-55)      — weakest_graha root-cause finding is documented in
                           this lane's handback report (bo_upaya.py /
                           bo_samvada.py — outside this lane's file scope,
                           no test needed here)

RECONCILIATION UPDATE (2026-07-14, post-Lane-2 merge): ga_vichara/chart_vichara
now ships for real (Lane 2, migration 435). When this lane originally ran,
LANE2 was verified BLOCKED, so ONLY the keyword-heuristic fallback path was
ever exercised — `TestChange3JudgedValence.test_uses_vichara_row_when_present`
below asserted against a *synthetic* lookup key format ("2" as a bare house
number) that does NOT match what ga_vichara_writer.py actually produces
(`f"{varga}_HOUSE_{house}"`, e.g. "D1_HOUSE_2", and the actor code is always
ga_vichara's canonical PLANET_TO_SUBJECT form — but tags['lord'] on the
bhava_significance_link facts that drive ga_vichara's valence_pass is the LONG
planet name, e.g. "Mars"). Both were real, silent join-miss bugs: the
ga_vichara-sourced path could never fire even after ga_vichara shipped. Fixed
in bo_laksana.py (2026-07-14): _canonical_graha_code() normalizes the actor,
tags['target_house'] is captured from fact jsonb (added to the tag whitelist),
and _resolve_valence composes the exact ga_vichara target-key format.
TestChange3RealShapeIntegration below exercises the corrected path end-to-end
via _build_signal_row with fixtures shaped exactly like
ga_vichara_writer.build_valence_pass_rows's real output; the old synthetic
fixture test is corrected in place (not deleted) to the real key format.

These tests run entirely in-process; no DB required (mirrors
test_bo_a1_fixes.py's stub-import pattern).
"""
from __future__ import annotations

import json
import sys
import os
import types
import importlib
import importlib.util
import unittest
from unittest.mock import MagicMock

_HERE = os.path.dirname(__file__)
_WRITERS_DIR = os.path.abspath(os.path.join(_HERE, "../../pipeline/orchestrator/writers"))
_SIDECAR_ROOT = os.path.abspath(os.path.join(_HERE, "../.."))

if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, _SIDECAR_ROOT)


class _WriterBase:
    pass


def _register(asset_id):
    def decorator(cls):
        return cls
    return decorator


class _ContextSpec:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _WriterResult:
    def __init__(self, **kwargs):
        self.asset_id = kwargs.get("asset_id", "")
        self.rows_inserted = kwargs.get("rows_inserted", 0)
        self.rows_updated = kwargs.get("rows_updated", 0)
        self.rows_skipped = kwargs.get("rows_skipped", 0)
        self.duration_seconds = kwargs.get("duration_seconds", 0.0)
        self.notes = kwargs.get("notes", "")


class _SubStep:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# Use a PRIVATE stub package namespace (not "pipeline.orchestrator.writers")
# so this file's re-exec of bo_laksana.py can never collide with the real
# package's asset registry (which other test files in this same pytest
# session may have already populated via a genuine import — the real
# `register` decorator dedup-checks asset_id globally, and this file's
# in-process reload of bo_laksana.py would otherwise raise
# "duplicate writer registration for asset_id=bo_laksana").
_STUB_ROOT = "lane4_stub_pipeline"
_pkg_pipeline = types.ModuleType(_STUB_ROOT)
_pkg_orchestrator = types.ModuleType(f"{_STUB_ROOT}.orchestrator")
_pkg_writers = types.ModuleType(f"{_STUB_ROOT}.orchestrator.writers")

_pkg_writers.WriterBase = _WriterBase
_pkg_writers.register = _register
_pkg_writers.ContextSpec = _ContextSpec
_pkg_writers.WriterResult = _WriterResult
_pkg_writers.SubStep = _SubStep
_pkg_writers.__path__ = [_WRITERS_DIR]
_pkg_writers.__package__ = f"{_STUB_ROOT}.orchestrator.writers"

_pkg_orchestrator.writers = _pkg_writers
_pkg_orchestrator.__path__ = [os.path.dirname(_WRITERS_DIR)]
_pkg_pipeline.orchestrator = _pkg_orchestrator
_pkg_pipeline.__path__ = [os.path.dirname(os.path.dirname(_WRITERS_DIR))]

sys.modules[_STUB_ROOT] = _pkg_pipeline
sys.modules[f"{_STUB_ROOT}.orchestrator"] = _pkg_orchestrator
sys.modules[f"{_STUB_ROOT}.orchestrator.writers"] = _pkg_writers

_bo_laksana_path = os.path.join(_WRITERS_DIR, "bo_laksana.py")
_spec = importlib.util.spec_from_file_location(
    f"{_STUB_ROOT}.orchestrator.writers.bo_laksana",
    _bo_laksana_path,
    submodule_search_locations=[],
)
_mod = importlib.util.module_from_spec(_spec)
_mod.__package__ = f"{_STUB_ROOT}.orchestrator.writers"
sys.modules[f"{_STUB_ROOT}.orchestrator.writers.bo_laksana"] = _mod
_spec.loader.exec_module(_mod)

# ── Re-export targets under test ──────────────────────────────────────────────
_resolve_class_prior = _mod._resolve_class_prior
_load_class_priors = _mod._load_class_priors
_resolve_ratification_factor = _mod._resolve_ratification_factor
_load_varga_ratification = _mod._load_varga_ratification
_resolve_valence = _mod._resolve_valence
_load_vichara_valence = _mod._load_vichara_valence
_load_vichara_divergence_signals = _mod._load_vichara_divergence_signals
_infer_valence = _mod._infer_valence
_build_headline_text = _mod._build_headline_text
_tier_ceiling_for = _mod._tier_ceiling_for
_assign_tiers_by_percentile = _mod._assign_tiers_by_percentile
_resolve_position_subject = _mod._resolve_position_subject
_build_signal_row = _mod._build_signal_row
_FLOOD_PRONE_FAMILIES = _mod._FLOOD_PRONE_FAMILIES
_canonical_graha_code = _mod._canonical_graha_code


def _make_conn(rows_by_query):
    """Minimal mock DB connection — matches test_bo_a1_fixes.py's helper.
    `conn.execute(...)` (used by _fetch_dict) returns rows in sequence;
    `conn.cursor()` (used by the SAVEPOINT-guarded loaders) is a bare
    context-manager MagicMock that accepts any .execute() call silently."""
    conn = MagicMock()
    call_count = [0]
    results = list(rows_by_query)

    def execute(sql, params=None):
        cur = MagicMock()
        idx = call_count[0]
        call_count[0] += 1
        batch = results[idx] if idx < len(results) else []
        cur.fetchall.return_value = [dict(r) for r in batch]
        return cur

    conn.execute.side_effect = execute
    return conn


def _make_raising_conn(exc: Exception):
    """A conn whose .execute() (both direct and via .cursor()) always raises —
    simulates chart_vichara / the referenced table not existing."""
    conn = MagicMock()
    conn.execute.side_effect = exc

    cursor_mock = MagicMock()
    cursor_mock.__enter__.return_value.execute.side_effect = exc
    conn.cursor.return_value = cursor_mock
    return conn


# ──────────────────────────────────────────────────────────────────────────────
# Change 1 (CR-81) — class_prior activation
# ──────────────────────────────────────────────────────────────────────────────

class TestChange1ClassPrior(unittest.TestCase):
    def test_resolve_exact_match(self):
        priors = {("configuration", "yoga"): 1.15}
        val, hit = _resolve_class_prior(priors, "configuration", "yoga")
        self.assertEqual(val, 1.15)
        self.assertTrue(hit)

    def test_resolve_cascades_to_class_sentinel(self):
        priors = {("configuration", "*"): 1.40}
        val, hit = _resolve_class_prior(priors, "configuration", "structural")
        self.assertEqual(val, 1.40)
        self.assertTrue(hit)

    def test_resolve_cascades_to_subsystem_sentinel(self):
        priors = {("*", "vastu"): 0.70}
        val, hit = _resolve_class_prior(priors, "position", "vastu")
        self.assertEqual(val, 0.70)
        self.assertTrue(hit)

    def test_resolve_miss_defaults_to_neutral(self):
        val, hit = _resolve_class_prior({}, "position", "structural")
        self.assertEqual(val, 1.0)
        self.assertFalse(hit)

    def test_load_class_priors_parses_rows(self):
        rows = [
            {"signal_type_class": "configuration", "source_subsystem": "*", "class_prior": 1.40},
            {"signal_type_class": "*", "source_subsystem": "vastu", "class_prior": 0.70},
        ]
        conn = _make_conn([rows])
        priors = _load_class_priors(conn)
        self.assertEqual(priors[("configuration", "*")], 1.40)
        self.assertEqual(priors[("*", "vastu")], 0.70)

    def test_load_class_priors_degrades_to_empty_on_missing_table(self):
        conn = _make_raising_conn(Exception('relation "brahma_class_priors" does not exist'))
        priors = _load_class_priors(conn)
        self.assertEqual(priors, {})


# ──────────────────────────────────────────────────────────────────────────────
# Change 2 (CR-82→CR-65) — tier ceiling retirement + percentile tiers
# ──────────────────────────────────────────────────────────────────────────────

class TestChange2TierCeilingRetired(unittest.TestCase):
    def test_per_varga_category_no_longer_capped(self):
        # Pre-fix: this returned "supporting" (CR-82's structural prohibition).
        self.assertIsNone(_tier_ceiling_for("graha_dignity_per_varga", "D9"))

    def test_non_d1_varga_no_longer_capped(self):
        self.assertIsNone(_tier_ceiling_for("some_other_category", "D9"))

    def test_flood_family_ceiling_survives(self):
        for cat in _FLOOD_PRONE_FAMILIES:
            self.assertEqual(_tier_ceiling_for(cat, "D9"), "supporting")


class TestChange2PercentileTiers(unittest.TestCase):
    def _rows(self, saliences, ceilings=None):
        ceilings = ceilings or [None] * len(saliences)
        return [
            {"computed_salience": s, "_tier_ceiling": c}
            for s, c in zip(saliences, ceilings)
        ]

    def test_top_1_5_percent_is_chart_defining(self):
        # 1000 evenly-spaced saliences: top ~15 rows (1.5%) must be chart_defining.
        saliences = [i / 1000.0 * 5.0 for i in range(1000)]
        rows = self._rows(saliences)
        _assign_tiers_by_percentile(rows)
        chart_defining = [r for r in rows if r["signature_tier"] == "chart_defining"]
        # top 1.5% of 1000 = 15 rows (pctl >= 0.985 -> ranks 986..1000)
        self.assertGreaterEqual(len(chart_defining), 10)
        self.assertLessEqual(len(chart_defining), 20)
        # the single highest-salience row must be chart_defining
        self.assertEqual(max(rows, key=lambda r: r["computed_salience"])["signature_tier"], "chart_defining")

    def test_flood_ceiling_still_caps_after_percentile(self):
        saliences = [i / 10.0 for i in range(1, 101)]  # 100 rows, top row = 10.0
        ceilings = ["supporting"] * 100
        rows = self._rows(saliences, ceilings)
        _assign_tiers_by_percentile(rows)
        # every row was ceiling-capped at 'supporting' even though the top
        # rows would otherwise land in chart_defining/major by percentile.
        for r in rows:
            self.assertIn(r["signature_tier"], ("background", "supporting"))

    def test_low_salience_bulk_still_background_or_supporting(self):
        saliences = [0.05] * 50 + [0.5] * 40 + [3.0] * 10
        rows = self._rows(saliences)
        _assign_tiers_by_percentile(rows)
        low = [r for r in rows if r["computed_salience"] == 0.05]
        self.assertTrue(all(r["signature_tier"] == "background" for r in low))

    def test_empty_rows_no_crash(self):
        _assign_tiers_by_percentile([])  # must not raise


class TestChange2RatificationFactor(unittest.TestCase):
    def test_no_lookup_returns_none(self):
        factor, domain = _resolve_ratification_factor({}, "VEN", ["wealth"])
        self.assertIsNone(factor)
        self.assertIsNone(domain)

    def test_no_primary_graha_returns_none(self):
        factor, domain = _resolve_ratification_factor({("VEN", "wealth"): 1.4}, None, ["wealth"])
        self.assertIsNone(factor)

    def test_picks_max_magnitude_deviation_domain(self):
        lookup = {("SAT", "wealth"): 1.1, ("SAT", "career"): 0.65}
        factor, domain = _resolve_ratification_factor(lookup, "SAT", ["wealth", "career"])
        self.assertEqual(factor, 0.65)
        self.assertEqual(domain, "career")

    def test_load_varga_ratification_degrades_when_table_absent(self):
        conn = _make_raising_conn(Exception('relation "chart_vichara" does not exist'))
        lookup, available = _load_varga_ratification(conn, "chart-1")
        self.assertEqual(lookup, {})
        self.assertFalse(available)

    def test_load_varga_ratification_parses_rows_when_present(self):
        rows = [{"subject": "VEN", "domain": "wealth", "ratification_factor": 1.32}]
        conn = _make_conn([rows])
        lookup, available = _load_varga_ratification(conn, "chart-1")
        self.assertTrue(available)
        self.assertEqual(lookup[("VEN", "wealth")], 1.32)


# ──────────────────────────────────────────────────────────────────────────────
# Change 3 (CR-83/CR-54) — judged valence with visible fallback
# ──────────────────────────────────────────────────────────────────────────────

class TestChange3JudgedValence(unittest.TestCase):
    def test_falls_back_to_keyword_heuristic_when_no_vichara_row(self):
        valence, source, judged = _resolve_valence({}, "yoga_fires", "some exalted yoga", {})
        self.assertEqual(valence, _infer_valence("yoga_fires", "some exalted yoga"))
        self.assertEqual(source, "keyword_heuristic_v1")
        self.assertIsNone(judged)

    def test_uses_vichara_row_when_present(self):
        # Key format corrected 2026-07-14 to match ga_vichara_writer.py's real
        # output: target = f"{varga}_HOUSE_{house}", not a bare house number.
        lookup = {("MAR", "D1_HOUSE_2", "D1"): {"value_text": "strong_malefic", "value_num": -0.8}}
        tags = {"graha": "MAR", "house": "2", "varga": "D1"}
        valence, source, judged = _resolve_valence(lookup, "aspect_parashari_given", "irrelevant text", tags)
        self.assertEqual(valence, "malefic")
        self.assertEqual(source, "ga_vichara_v1")
        self.assertEqual(judged, -0.8)

    def test_uses_vichara_row_via_target_house_tag(self):
        # target_house (not house) is the tag ga_vichara's upstream
        # bhava_significance_link facts actually carry.
        lookup = {("MAR", "D1_HOUSE_2", "D1"): {"value_text": "strong_malefic", "value_num": -0.8}}
        tags = {"graha": "MAR", "target_house": 2, "varga": "D1"}
        valence, source, judged = _resolve_valence(lookup, "bhava_significance_link", "irrelevant", tags)
        self.assertEqual(valence, "malefic")
        self.assertEqual(source, "ga_vichara_v1")
        self.assertEqual(judged, -0.8)

    def test_uses_vichara_row_when_actor_tag_is_long_form(self):
        # tags['lord'] on bhava_significance_link facts is the LONG planet
        # name ('Mars'), while ga_vichara's actor/subject column is always
        # the canonical short code ('MAR') — must still match.
        lookup = {("MAR", "D1_HOUSE_2", "D1"): {"value_text": "strong_malefic", "value_num": -0.8}}
        tags = {"lord": "Mars", "target_house": 2, "varga": "D1"}
        valence, source, judged = _resolve_valence(lookup, "bhava_significance_link", "irrelevant", tags)
        self.assertEqual(valence, "malefic")
        self.assertEqual(source, "ga_vichara_v1")
        self.assertEqual(judged, -0.8)

    def test_bare_house_number_alone_does_not_falsely_match_wrong_varga(self):
        # A row keyed for D9 must not be matched by a D1 fact even if the
        # house number coincides.
        lookup = {("MAR", "D9_HOUSE_2", "D9"): {"value_text": "benefic", "value_num": 0.5}}
        tags = {"graha": "MAR", "target_house": 2, "varga": "D1"}
        valence, source, judged = _resolve_valence(lookup, "bhava_significance_link", "irrelevant", tags)
        self.assertEqual(source, "keyword_heuristic_v1")
        self.assertIsNone(judged)

    def test_load_vichara_valence_degrades_when_table_absent(self):
        conn = _make_raising_conn(Exception('relation "chart_vichara" does not exist'))
        lookup, available = _load_vichara_valence(conn, "chart-1")
        self.assertEqual(lookup, {})
        self.assertFalse(available)

    def test_load_vichara_divergence_signals_empty_when_table_absent(self):
        conn = _make_raising_conn(Exception('relation "chart_vichara" does not exist'))
        signals = _load_vichara_divergence_signals(conn, "chart-1", "lahiri_chitrapaksha", "build-1", "2026-01-01T00:00:00Z")
        self.assertEqual(signals, [])


# ──────────────────────────────────────────────────────────────────────────────
# Change 4 (CR-45) — subject-bearing headlines
# ──────────────────────────────────────────────────────────────────────────────

class TestChange4Headlines(unittest.TestCase):
    def test_headline_with_full_subject_house_varga(self):
        h = _build_headline_text(
            "graha_dignity_per_varga", "dignity_state", "own_star", None,
            "ga_structural", fact_subject="venus", house=9, varga_id="D1",
        )
        self.assertTrue(h.startswith("VENUS (H9, D1):"), h)
        self.assertIn("[ga_structural]", h)

    def test_headline_omits_absent_parts(self):
        h = _build_headline_text(
            "graha_dignity_per_varga", "dignity_state", "own_star", None,
            "ga_structural", fact_subject="venus", house=None, varga_id=None,
        )
        self.assertTrue(h.startswith("VENUS:"), h)

    def test_headline_falls_back_to_anonymous_form_when_no_subject(self):
        h = _build_headline_text(
            "panchanga_tithi", "tithi_name", "shukla_tritiya", None,
            "ga_panchanga", fact_subject=None, house=None, varga_id=None,
        )
        self.assertFalse(h[0].isupper() and " (" in h)
        self.assertIn("panchanga tithi: tithi name = shukla_tritiya [ga_panchanga]", h)


# ──────────────────────────────────────────────────────────────────────────────
# Change 5 (CR-76/77 AMENDED) — position-class subject resolution
# ──────────────────────────────────────────────────────────────────────────────

class TestChange5PositionResolution(unittest.TestCase):
    def test_explicit_jsonb_graha_key_wins(self):
        graha, house, rule = _resolve_position_subject(
            "special_lagna", "INDU_LAGNA", {"graha": "KET_MEAN", "house": 8}, None,
        )
        self.assertEqual(graha, "KET_MEAN")
        self.assertEqual(house, 8)
        self.assertEqual(rule, "explicit_jsonb:graha")

    def test_karaka_value_text_resolution(self):
        # AmK=Saturn specimen (brief §6, fact 3d8de38d)
        graha, house, rule = _resolve_position_subject(
            "karaka_chara_position", "AmK", {}, "Saturn",
        )
        self.assertEqual(graha, "SAT")
        self.assertEqual(rule, "karaka_value_text")

    def test_sign_lord_fallback(self):
        graha, house, rule = _resolve_position_subject(
            "special_lagna", "SREE_LAGNA", {"sign": "Libra", "house": 7}, None,
        )
        self.assertEqual(graha, "VEN")
        self.assertEqual(house, 7)
        self.assertEqual(rule, "sign_lord")

    def test_genuinely_unresolvable_returns_none_graha(self):
        graha, house, rule = _resolve_position_subject(
            "kp_cuspal_significators", "CUSP_11", {}, None,
        )
        self.assertIsNone(graha)
        self.assertIsNone(rule)


# ──────────────────────────────────────────────────────────────────────────────
# Actor-code normalization (2026-07-14 fix) — _canonical_graha_code
# ──────────────────────────────────────────────────────────────────────────────

class TestCanonicalGrahaCode(unittest.TestCase):
    def test_long_form_normalizes_to_short(self):
        self.assertEqual(_canonical_graha_code("Mars"), "MAR")
        self.assertEqual(_canonical_graha_code("Saturn"), "SAT")
        self.assertEqual(_canonical_graha_code("Rahu"), "RAH_MEAN")

    def test_already_canonical_passes_through(self):
        self.assertEqual(_canonical_graha_code("MAR"), "MAR")
        self.assertEqual(_canonical_graha_code("RAH_MEAN"), "RAH_MEAN")

    def test_lowercase_alias_normalizes(self):
        self.assertEqual(_canonical_graha_code("mars"), "MAR")
        self.assertEqual(_canonical_graha_code("kuja"), "MAR")

    def test_none_passes_through_as_none(self):
        self.assertIsNone(_canonical_graha_code(None))


# ──────────────────────────────────────────────────────────────────────────────
# Real-shape integration — _build_signal_row against ga_vichara's actual
# valence_pass output shape (build_valence_pass_rows in ga_vichara_writer.py),
# not a synthetic fixture. Exercises the ga_vichara-sourced path end-to-end,
# not just _resolve_valence in isolation.
# ──────────────────────────────────────────────────────────────────────────────

class TestChange3RealShapeIntegration(unittest.TestCase):
    """8th-lord-Mars-aspects-2nd-house specimen (CR-54 type case), built from
    a bhava_significance_link fact shaped exactly like
    ga_structural_writer.py's _build_bhava_web_per_varga_rows output."""

    def _mars_aspects_h2_fact(self):
        return {
            "fact_id": "1ea14404",
            "fact_category": "bhava_significance_link",
            "fact_key": "lord_aspects",
            "fact_subject": "D1_HOUSE_8_to_HOUSE_2",
            "ayanamsha_id": "lahiri_chitrapaksha",
            "verification_pass_status": "two_pass_verified",
            "fact_value_text": "dusthana_afflicts",
            "fact_value_num": None,
            "fact_value_jsonb": json.dumps({
                "varga": "D1",
                "source_house": 8,
                "target_house": 2,
                "lord": "Mars",
                "link_kind": "lord_aspects",
                "link_type": "dusthana_afflicts",
                "constituent_facts_array": ["82cc6f52"],
            }),
            "source_calculation": "ga_structural.bhava_web_per_varga/v1",
            "citation_ref": None,
            "citation_human": None,
        }

    def _vichara_lookup(self):
        # Shaped exactly like ga_vichara_writer.build_valence_pass_rows's
        # emitted row for 8th-lord Mars aspecting H2 in D1 (dusthana lord
        # afflicting the wealth axis -> strong_malefic per the valence matrix).
        return {("MAR", "D1_HOUSE_2", "D1"): {"value_text": "strong_malefic", "value_num": -1.0}}

    def test_ga_vichara_sourced_valence_wins_over_keyword_heuristic(self):
        row = _build_signal_row(
            self._mars_aspects_h2_fact(), "chart-1", "build-1",
            strength_lookup={"MAR": 1.2}, dignity_lookup={"MAR": "neutral"},
            av_lookup={i: 28 for i in range(1, 13)},
            now="2026-07-14T00:00:00+00:00",
            vichara_valence_lookup=self._vichara_lookup(),
        )
        self.assertEqual(row["valence"], "malefic")
        self.assertEqual(row["valence_source"], "ga_vichara_v1")
        epistemic = json.loads(row["epistemic_jsonb"])
        self.assertEqual(epistemic.get("judged_valence"), -1.0)

    def test_fallback_still_fires_when_no_vichara_row_for_this_combo(self):
        """A genuinely different graha/varga combo with no ga_vichara row must
        still degrade honestly to the keyword heuristic — the fallback is not
        collateral damage of wiring in the real path."""
        row = _build_signal_row(
            self._mars_aspects_h2_fact(), "chart-1", "build-1",
            strength_lookup={"MAR": 1.2}, dignity_lookup={"MAR": "neutral"},
            av_lookup={i: 28 for i in range(1, 13)},
            now="2026-07-14T00:00:00+00:00",
            # lookup populated, but for an unrelated (graha, house, varga) triple
            vichara_valence_lookup={("VEN", "D9_HOUSE_11", "D9"): {"value_text": "benefic", "value_num": 0.5}},
        )
        self.assertEqual(row["valence_source"], "keyword_heuristic_v1")
        epistemic = json.loads(row["epistemic_jsonb"])
        self.assertNotIn("judged_valence", epistemic)

    def test_fallback_when_vichara_lookup_entirely_empty(self):
        """Table absent / not yet built for this chart — still the honest,
        visibly-tagged degraded path, never silent."""
        row = _build_signal_row(
            self._mars_aspects_h2_fact(), "chart-1", "build-1",
            strength_lookup={"MAR": 1.2}, dignity_lookup={"MAR": "neutral"},
            av_lookup={i: 28 for i in range(1, 13)},
            now="2026-07-14T00:00:00+00:00",
            vichara_valence_lookup={},
        )
        self.assertEqual(row["valence_source"], "keyword_heuristic_v1")


if __name__ == "__main__":
    unittest.main()

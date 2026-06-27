"""
test_bo_a1_fixes.py — A1 swarm agent unit tests for bo_laksana fixes.

Covers:
  B2 — Salience stratification: lookup builders + compute_salience must produce
       stratified results, not uniform ~0.5058 for all signals.
  B3-src — yoga/dosha signals must have non-null graha in configuration_jsonb.
  O3 — Navamsha D9 cross-check signals emitted with correct classifications.

These tests run entirely in-process; no DB required.
All tests FAIL before the fix and PASS after.
"""
from __future__ import annotations

import json
import math
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Import the module under test ──────────────────────────────────────────────
import sys
import os
import importlib
import importlib.util

_HERE = os.path.dirname(__file__)
_WRITERS_DIR = os.path.abspath(os.path.join(_HERE, "../../pipeline/orchestrator/writers"))
_SIDECAR_ROOT = os.path.abspath(os.path.join(_HERE, "../.."))

# Insert sidecar root so package imports resolve
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, _SIDECAR_ROOT)

# Minimal stubs so the relative import `from . import WriterBase …` works.
# bo_laksana.py uses `from . import WriterBase, ContextSpec, WriterResult, SubStep, register`
# We inject a stub package so the relative import resolves cleanly.

class _WriterBase:
    pass

def _register(asset_id):
    def decorator(cls):
        return cls
    return decorator

class _ContextSpec:
    pass

class _WriterResult:
    def __init__(self, **kwargs):
        pass

class _SubStep:
    def __init__(self, **kwargs):
        pass

# Build the stub package hierarchy that the relative import expects
_pkg_pipeline = types.ModuleType("pipeline")
_pkg_orchestrator = types.ModuleType("pipeline.orchestrator")
_pkg_writers = types.ModuleType("pipeline.orchestrator.writers")

_pkg_writers.WriterBase = _WriterBase
_pkg_writers.register   = _register
_pkg_writers.ContextSpec  = _ContextSpec
_pkg_writers.WriterResult = _WriterResult
_pkg_writers.SubStep      = _SubStep
# Make writers a package (needs __path__ for relative imports to work)
_pkg_writers.__path__   = [_WRITERS_DIR]
_pkg_writers.__package__ = "pipeline.orchestrator.writers"

_pkg_orchestrator.writers = _pkg_writers
_pkg_orchestrator.__path__ = [os.path.dirname(_WRITERS_DIR)]
_pkg_pipeline.orchestrator = _pkg_orchestrator
_pkg_pipeline.__path__ = [os.path.dirname(os.path.dirname(_WRITERS_DIR))]

sys.modules.setdefault("pipeline", _pkg_pipeline)
sys.modules.setdefault("pipeline.orchestrator", _pkg_orchestrator)
sys.modules["pipeline.orchestrator.writers"] = _pkg_writers

# Now load bo_laksana.py as part of that stub package
_bo_laksana_path = os.path.join(_WRITERS_DIR, "bo_laksana.py")
_spec = importlib.util.spec_from_file_location(
    "pipeline.orchestrator.writers.bo_laksana",
    _bo_laksana_path,
    submodule_search_locations=[],
)
_mod = importlib.util.module_from_spec(_spec)
_mod.__package__ = "pipeline.orchestrator.writers"
sys.modules["pipeline.orchestrator.writers.bo_laksana"] = _mod
_spec.loader.exec_module(_mod)

# Re-export helpers we'll test
_build_strength_lookup    = _mod._build_strength_lookup
_build_dignity_lookup     = _mod._build_dignity_lookup
_build_av_lookup          = _mod._build_av_lookup
_compute_salience         = _mod._compute_salience
_graha_key_from_subject   = _mod._graha_key_from_subject
_infer_graha_for_yoga_dosha = _mod._infer_graha_for_yoga_dosha
_dignity_tier             = _mod._dignity_tier
_build_navamsha_cross_check_signals = _mod._build_navamsha_cross_check_signals
_build_signal_row         = _mod._build_signal_row
_signature_tier           = _mod._signature_tier
_DIGNITY_SCORE            = _mod._DIGNITY_SCORE


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_conn(rows_by_query: list[list[dict]]):
    """Build a minimal mock DB connection that returns rows in sequence."""
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


# ──────────────────────────────────────────────────────────────────────────────
# B2 — Lookup builder correctness
# ──────────────────────────────────────────────────────────────────────────────

class TestB2StrengthLookup(unittest.TestCase):
    """_build_strength_lookup must key on fact_subject, not fact_key."""

    def _make_shadbala_rows(self):
        return [
            {"fact_subject": "SUN",      "fact_value_num": 3.225},
            {"fact_subject": "MOON",     "fact_value_num": 2.5607},
            {"fact_subject": "MAR",      "fact_value_num": 3.106},
            {"fact_subject": "MER",      "fact_value_num": 2.5},
            {"fact_subject": "JUP",      "fact_value_num": 2.6598},
            {"fact_subject": "VEN",      "fact_value_num": 2.3592},
            {"fact_subject": "SAT",      "fact_value_num": 3.611},
            {"fact_subject": "RAH_MEAN", "fact_value_num": 0.375},
            {"fact_subject": "KET_MEAN", "fact_value_num": 0.625},
        ]

    def test_strength_lookup_keys_are_graha_names(self):
        conn = _make_conn([self._make_shadbala_rows()])
        result = _build_strength_lookup(conn, "chart-1", "lahiri_chitrapaksha")
        self.assertIn("SUN", result, "SUN must be a key in strength_lookup")
        self.assertIn("JUP", result, "JUP must be a key in strength_lookup")
        self.assertIn("SAT", result, "SAT must be a key in strength_lookup")
        # Old bug: 'rupa' was the key; verify it is NOT a key
        self.assertNotIn("rupa", result, "Old bug: 'rupa' must not be a lookup key")

    def test_strength_lookup_values_are_ratios(self):
        conn = _make_conn([self._make_shadbala_rows()])
        result = _build_strength_lookup(conn, "chart-1", "lahiri_chitrapaksha")
        # SAT has 3.611 rupas → clamped at 2.0
        self.assertAlmostEqual(result["SAT"], 2.0, places=3)
        # RAH_MEAN has 0.375 → 0.375
        self.assertAlmostEqual(result["RAH_MEAN"], 0.375, places=3)

    def test_strength_lookup_not_empty(self):
        conn = _make_conn([self._make_shadbala_rows()])
        result = _build_strength_lookup(conn, "chart-1", "lahiri_chitrapaksha")
        self.assertGreater(len(result), 0)


class TestB2DignityLookup(unittest.TestCase):
    """_build_dignity_lookup must use fact_subject ('D1_SUN') + jsonb varga='D1' filter."""

    def _make_dignity_rows(self):
        return [
            {"fact_subject": "D1_SUN",      "fact_value_text": "neutral"},
            {"fact_subject": "D1_MOON",     "fact_value_text": "neutral"},
            {"fact_subject": "D1_MAR",      "fact_value_text": "neutral"},
            {"fact_subject": "D1_MER",      "fact_value_text": "neutral"},
            {"fact_subject": "D1_JUP",      "fact_value_text": "own"},
            {"fact_subject": "D1_VEN",      "fact_value_text": "neutral"},
            {"fact_subject": "D1_SAT",      "fact_value_text": "exalted"},
            {"fact_subject": "D1_RAH_MEAN", "fact_value_text": "exalted"},
            {"fact_subject": "D1_KET_MEAN", "fact_value_text": "exalted"},
        ]

    def test_dignity_lookup_keys_correct(self):
        conn = _make_conn([self._make_dignity_rows()])
        result = _build_dignity_lookup(conn, "chart-1", "lahiri_chitrapaksha")
        self.assertIn("JUP", result)
        self.assertIn("SAT", result)
        self.assertIn("RAH_MEAN", result)

    def test_dignity_lookup_values_correct(self):
        conn = _make_conn([self._make_dignity_rows()])
        result = _build_dignity_lookup(conn, "chart-1", "lahiri_chitrapaksha")
        self.assertEqual(result.get("JUP"), "own")
        self.assertEqual(result.get("SAT"), "exalted")

    def test_dignity_lookup_not_empty(self):
        conn = _make_conn([self._make_dignity_rows()])
        result = _build_dignity_lookup(conn, "chart-1", "lahiri_chitrapaksha")
        self.assertGreater(len(result), 0)


class TestB2AvLookup(unittest.TestCase):
    """_build_av_lookup must use ashtakavarga_bindu SARVA-HOUSE_N rows."""

    def _make_av_rows(self):
        return [
            {"fact_subject": "SARVA-HOUSE_1",  "fact_value_num": 29},
            {"fact_subject": "SARVA-HOUSE_4",  "fact_value_num": 32},
            {"fact_subject": "SARVA-HOUSE_7",  "fact_value_num": 33},
            {"fact_subject": "SARVA-HOUSE_8",  "fact_value_num": 33},
            {"fact_subject": "SARVA-HOUSE_9",  "fact_value_num": 25},
            {"fact_subject": "SARVA-HOUSE_10", "fact_value_num": 26},
            {"fact_subject": "SARVA-HOUSE_11", "fact_value_num": 23},
            {"fact_subject": "SARVA-HOUSE_12", "fact_value_num": 23},
        ]

    def test_av_lookup_keys_are_house_numbers(self):
        conn = _make_conn([self._make_av_rows()])
        result = _build_av_lookup(conn, "chart-1", "lahiri_chitrapaksha")
        self.assertIn(1, result)
        self.assertIn(7, result)
        self.assertIn(10, result)

    def test_av_lookup_values_correct(self):
        conn = _make_conn([self._make_av_rows()])
        result = _build_av_lookup(conn, "chart-1", "lahiri_chitrapaksha")
        self.assertEqual(result[7], 33)
        self.assertEqual(result[9], 25)

    def test_av_lookup_not_empty(self):
        conn = _make_conn([self._make_av_rows()])
        result = _build_av_lookup(conn, "chart-1", "lahiri_chitrapaksha")
        self.assertGreater(len(result), 0)


# ──────────────────────────────────────────────────────────────────────────────
# B2 — Salience stratification end-to-end
# ──────────────────────────────────────────────────────────────────────────────

class TestB2SalienceStratification(unittest.TestCase):
    """B2: salience must stratify — multiple distinct values produced, not all ~0.5058."""

    def _make_lookups(self):
        strength = {
            "SUN": 2.0, "MOON": 1.5, "MAR": 1.8, "MER": 1.4,
            "JUP": 2.0, "VEN": 1.3, "SAT": 2.0,
        }
        dignity = {
            "SUN": "neutral", "MOON": "neutral", "MAR": "neutral",
            "MER": "neutral", "JUP": "own",      "VEN": "neutral",
            "SAT": "exalted",
        }
        av = {1: 29, 2: 29, 3: 28, 4: 32, 5: 30,
              6: 25, 7: 33, 8: 33, 9: 25, 10: 26, 11: 23, 12: 23}
        return strength, dignity, av

    def _make_fact(self, fact_subject, fact_cat, house, vpass="documented_approximation"):
        return {
            "fact_id": "aabbccdd",
            "fact_category": fact_cat,
            "fact_key": "dignity_state",
            "fact_subject": fact_subject,
            "ayanamsha_id": "lahiri_chitrapaksha",
            "verification_pass_status": vpass,
            "fact_value_text": "exalted",
            "fact_value_num": None,
            "fact_value_jsonb": {"house": house, "varga": "D1"},
        }

    def test_different_grahas_produce_different_saliences(self):
        strength, dignity, av = self._make_lookups()
        results = []
        for graha, house in [("SAT", 1), ("MOON", 9), ("RAH_MEAN", 6)]:
            fact = self._make_fact(graha, "graha_dignity_per_varga", house)
            tags = {"house": house}
            sal = _compute_salience(fact, tags, strength, dignity, av)
            results.append(round(sal["computed_salience"], 4))

        # Must not all be equal
        self.assertGreater(len(set(results)), 1,
            f"All saliences identical ({results}); stratification broken")

    def test_high_dignity_graha_outscores_neutral(self):
        """SAT (exalted, strength=2.0, house=1) should outscore MOON (neutral, strength=1.5, house=9)."""
        strength, dignity, av = self._make_lookups()

        sat_fact = self._make_fact("SAT", "graha_dignity_per_varga", 1)
        moon_fact = self._make_fact("MOON", "graha_dignity_per_varga", 9)

        sat_sal  = _compute_salience(sat_fact,  {"house": 1}, strength, dignity, av)["computed_salience"]
        moon_sal = _compute_salience(moon_fact, {"house": 9}, strength, dignity, av)["computed_salience"]

        self.assertGreater(sat_sal, moon_sal,
            f"SAT salience ({sat_sal}) should exceed MOON ({moon_sal})")

    def test_verified_fact_outscores_unverified(self):
        """two_pass_verified should produce higher salience than documented_approximation."""
        strength, dignity, av = self._make_lookups()

        verified = self._make_fact("JUP", "graha_dignity_per_varga", 5,
                                   vpass="two_pass_verified")
        approx   = self._make_fact("JUP", "graha_dignity_per_varga", 5,
                                   vpass="documented_approximation")

        s_v = _compute_salience(verified, {"house": 5}, strength, dignity, av)["computed_salience"]
        s_a = _compute_salience(approx,   {"house": 5}, strength, dignity, av)["computed_salience"]
        self.assertGreater(s_v, s_a, "Verified fact must have higher salience than approximation")

    def test_multiple_signature_tiers_reachable(self):
        """With realistic lookups, at least 'supporting' tier must be reachable."""
        # SAT exalted, house=1, strength=2.0, two_pass_verified → should hit ≥ supporting
        strength, dignity, av = self._make_lookups()
        fact = self._make_fact("SAT", "graha_dignity_per_varga", 1, "two_pass_verified")
        sal = _compute_salience(fact, {"house": 1}, strength, dignity, av)["computed_salience"]
        tier = _signature_tier(sal)
        self.assertIn(tier, ("supporting", "major", "chart_defining"),
            f"Expected at least 'supporting' tier; got {tier} (salience={sal})")

    def test_not_all_background(self):
        """Representative set of signals must not all land in 'background' tier."""
        strength, dignity, av = self._make_lookups()
        tiers = set()
        test_cases = [
            ("SAT", "graha_dignity_per_varga", 1, "two_pass_verified"),
            ("JUP", "graha_dignity_per_varga", 9, "two_pass_verified"),
            ("MOON", "graha_dignity_per_varga", 6, "documented_approximation"),
        ]
        for graha, cat, house, vpass in test_cases:
            fact = self._make_fact(graha, cat, house, vpass)
            sal = _compute_salience(fact, {"house": house}, strength, dignity, av)["computed_salience"]
            tiers.add(_signature_tier(sal))

        self.assertNotEqual(tiers, {"background"},
            f"All signals landed in 'background'; stratification still broken. Tiers: {tiers}")


# ──────────────────────────────────────────────────────────────────────────────
# B2 — _graha_key_from_subject
# ──────────────────────────────────────────────────────────────────────────────

class TestGrahaKeyFromSubject(unittest.TestCase):

    def test_plain_graha(self):
        self.assertEqual(_graha_key_from_subject("SUN"), "SUN")
        self.assertEqual(_graha_key_from_subject("MAR"), "MAR")
        self.assertEqual(_graha_key_from_subject("RAH_MEAN"), "RAH_MEAN")

    def test_d1_prefixed(self):
        self.assertEqual(_graha_key_from_subject("D1_SUN"), "SUN")
        self.assertEqual(_graha_key_from_subject("D1_SAT"), "SAT")
        self.assertEqual(_graha_key_from_subject("D1_RAH_MEAN"), "RAH_MEAN")

    def test_house_suffixed(self):
        self.assertEqual(_graha_key_from_subject("SAT-HOUSE_1"), "SAT")
        self.assertEqual(_graha_key_from_subject("JUP-HOUSE_9"), "JUP")

    def test_empty(self):
        self.assertIsNone(_graha_key_from_subject(""))
        self.assertIsNone(_graha_key_from_subject(None))


# ──────────────────────────────────────────────────────────────────────────────
# B3 — Yoga/dosha graha inference
# ──────────────────────────────────────────────────────────────────────────────

class TestB3InferGrahaForYogaDosha(unittest.TestCase):

    def test_explicit_graha_in_jsonb(self):
        fvj = {"graha": "JUP", "fire_reason": "Jupiter in house 9"}
        result = _infer_graha_for_yoga_dosha("yoga_fires", fvj, "RAJA_YOGA")
        self.assertEqual(result, "JUP")

    def test_mangal_dosha_group(self):
        fvj = {"dosha_group": "mangal", "fire_reason": "Mars in house 7"}
        result = _infer_graha_for_yoga_dosha("dosha_fires", fvj, "MANGAL_DOSHA_7H")
        self.assertEqual(result, "MAR")

    def test_kala_sarpa_dosha_group(self):
        fvj = {"dosha_group": "kala_sarpa", "fire_reason": ""}
        result = _infer_graha_for_yoga_dosha("dosha_fires", fvj, "KALA_SARPA")
        self.assertEqual(result, "RAH_MEAN")

    def test_fire_reason_jupiter(self):
        fvj = {"fire_reason": "Jupiter in kendra from Moon"}
        result = _infer_graha_for_yoga_dosha("yoga_fires", fvj, "GAJA_KESARI")
        self.assertEqual(result, "JUP")

    def test_fire_reason_saturn(self):
        fvj = {"fire_reason": "Saturn in 7th house"}
        result = _infer_graha_for_yoga_dosha("yoga_fires", fvj, "some_yoga")
        self.assertEqual(result, "SAT")

    def test_fact_value_text_fallback(self):
        fvj = {}
        result = _infer_graha_for_yoga_dosha("yoga_label", fvj, "Gaja Kesari yoga (Jupiter)")
        self.assertEqual(result, "JUP")

    def test_returns_none_when_no_graha(self):
        fvj = {}
        result = _infer_graha_for_yoga_dosha("yoga_label", fvj, "Akriti Yoga")
        # No recognizable graha name
        self.assertIsNone(result)

    def test_mars_in_fire_reason(self):
        fvj = {"fire_reason": "Mars in house 7"}
        result = _infer_graha_for_yoga_dosha("dosha_fires", fvj, "MANGAL_DOSHA_7H")
        self.assertEqual(result, "MAR")

    def test_venus_in_fact_value_text(self):
        fvj = {}
        result = _infer_graha_for_yoga_dosha("dosha_label", fvj, "Combust Dosha (Maudhya) - Venus")
        self.assertEqual(result, "VEN")


class TestB3GrahaPopulatedInConfig(unittest.TestCase):
    """B3: _build_signal_row must set config['graha'] for yoga/dosha facts."""

    def _make_yoga_fact_row(self):
        return {
            "fact_id": "aabbccdd",
            "fact_category": "yoga_fires",
            "fact_key": "yoga_name",
            "fact_subject": "GAJA_KESARI",
            "ayanamsha_id": "lahiri_chitrapaksha",
            "verification_pass_status": "documented_approximation",
            "fact_value_text": "GAJA_KESARI",
            "fact_value_num": None,
            "fact_value_jsonb": json.dumps({
                "yoga_group": "auspicious",
                "fire_reason": "Jupiter in kendra (9) from Moon",
                "cancellation_flag": False,
                "yoga_strength_score": 0.7,
                "classical_citation_id": "BPHS.Ch.91",
                "constituent_facts_array": ["da14ccc6318f955c"],
            }),
            "source_calculation": "pyjhora_adapter.yoga",
            "citation_ref": None,
            "citation_human": None,
        }

    def test_yoga_signal_has_graha(self):
        fact_row = self._make_yoga_fact_row()
        row = _build_signal_row(
            fact_row, "chart-1", "build-1",
            strength_lookup={"JUP": 2.0},
            dignity_lookup={"JUP": "own"},
            av_lookup={i: 28 for i in range(1, 13)},
            now="2026-06-28T00:00:00+00:00",
        )
        config = json.loads(row["configuration_jsonb"])
        self.assertIn("graha", config, "yoga_fires signal must have 'graha' in configuration_jsonb")
        self.assertEqual(config["graha"], "JUP",
                         f"Expected graha=JUP; got {config.get('graha')}")

    def test_dosha_fires_mangal_has_graha(self):
        fact_row = {
            "fact_id": "11223344",
            "fact_category": "dosha_fires",
            "fact_key": "dosha_name",
            "fact_subject": "MANGAL_DOSHA",
            "ayanamsha_id": "lahiri_chitrapaksha",
            "verification_pass_status": "documented_approximation",
            "fact_value_text": "MANGAL_DOSHA_7H",
            "fact_value_num": None,
            "fact_value_jsonb": json.dumps({
                "dosha_group": "mangal",
                "fire_reason": "Mars in house 7",
                "cancellation_flag": False,
                "constituent_facts_array": ["abc123"],
            }),
            "source_calculation": "pyjhora_adapter.dosha_fires",
            "citation_ref": None,
            "citation_human": None,
        }
        row = _build_signal_row(
            fact_row, "chart-1", "build-1",
            strength_lookup={"MAR": 1.8},
            dignity_lookup={"MAR": "neutral"},
            av_lookup={i: 28 for i in range(1, 13)},
            now="2026-06-28T00:00:00+00:00",
        )
        config = json.loads(row["configuration_jsonb"])
        self.assertIn("graha", config, "dosha_fires signal must have 'graha' in config")
        self.assertEqual(config["graha"], "MAR")


# ──────────────────────────────────────────────────────────────────────────────
# O3 — Navamsha cross-check signals
# ──────────────────────────────────────────────────────────────────────────────

class TestO3NavamshaSignals(unittest.TestCase):
    """O3: D9 cross-check signals emitted with correct classifications."""

    # Real D1 data (lahiri_chitrapaksha): SAT=exalted, JUP=own, VEN=neutral, SUN=neutral
    # Real D9 data: SAT=Debilitated, JUP=Enemy, VEN=Debilitated, SUN=Friend

    def _make_conn(self):
        # First call → D1 dignity rows; second call → D9 dignity rows from chart_divisionals
        d1_rows = [
            {"fact_subject": "D1_SUN",      "fact_value_text": "neutral"},
            {"fact_subject": "D1_MOON",     "fact_value_text": "neutral"},
            {"fact_subject": "D1_JUP",      "fact_value_text": "own"},
            {"fact_subject": "D1_VEN",      "fact_value_text": "neutral"},
            {"fact_subject": "D1_SAT",      "fact_value_text": "exalted"},
            {"fact_subject": "D1_MAR",      "fact_value_text": "neutral"},
        ]
        d9_rows = [
            {"graha": "Saturn",  "fact_value_text": "Debilitated"},
            {"graha": "Jupiter", "fact_value_text": "Enemy"},
            {"graha": "Venus",   "fact_value_text": "Debilitated"},
            {"graha": "Sun",     "fact_value_text": "Friend"},
            {"graha": "Moon",    "fact_value_text": "Friend"},
            {"graha": "Mars",    "fact_value_text": "Friend"},
        ]
        return _make_conn([d1_rows, d9_rows])

    def test_signals_are_emitted(self):
        conn = self._make_conn()
        signals = _build_navamsha_cross_check_signals(
            conn, "chart-1", "lahiri_chitrapaksha", "build-1",
            "2026-06-28T00:00:00+00:00",
            strength_lookup={}, dignity_lookup={}, av_lookup={},
        )
        self.assertGreater(len(signals), 0, "O3 must emit at least one navamsha signal")

    def test_signal_type_class_is_varga_pattern(self):
        conn = self._make_conn()
        signals = _build_navamsha_cross_check_signals(
            conn, "chart-1", "lahiri_chitrapaksha", "build-1",
            "2026-06-28T00:00:00+00:00",
            strength_lookup={}, dignity_lookup={}, av_lookup={},
        )
        for sig in signals:
            self.assertEqual(sig["signal_type_class"], "varga_pattern")

    def test_saturn_is_broken_promise(self):
        """SAT: D1=exalted (tier=3) × D9=Debilitated (tier=-2) → broken_promise."""
        conn = self._make_conn()
        signals = _build_navamsha_cross_check_signals(
            conn, "chart-1", "lahiri_chitrapaksha", "build-1",
            "2026-06-28T00:00:00+00:00",
            strength_lookup={}, dignity_lookup={}, av_lookup={},
        )
        sat_sig = next(
            (s for s in signals if "saturn" in s["signal_type_id"].lower()), None
        )
        self.assertIsNotNone(sat_sig, "Saturn cross-check signal must be emitted")
        config = json.loads(sat_sig["configuration_jsonb"])
        self.assertEqual(config["classification"], "broken_promise",
                         f"SAT D1=exalted × D9=Debilitated → broken_promise; got {config['classification']}")
        self.assertEqual(sat_sig["valence"], "malefic")

    def test_broken_promise_salience_above_background(self):
        """broken_promise classification must produce salience ≥ 1.5 (major tier)."""
        conn = self._make_conn()
        signals = _build_navamsha_cross_check_signals(
            conn, "chart-1", "lahiri_chitrapaksha", "build-1",
            "2026-06-28T00:00:00+00:00",
            strength_lookup={}, dignity_lookup={}, av_lookup={},
        )
        for sig in signals:
            config = json.loads(sig["configuration_jsonb"])
            if config["classification"] == "broken_promise":
                self.assertGreaterEqual(
                    sig["computed_salience"], 1.5,
                    f"broken_promise must reach major tier; got {sig['computed_salience']}"
                )

    def test_vargottama_resilience_classification(self):
        """D1=weak × D9=strong → vargottama_resilience."""
        # Mock: SUN D1=debilitated, D9=exalted
        d1_rows = [{"fact_subject": "D1_SUN", "fact_value_text": "debilitated"}]
        d9_rows = [{"graha": "Sun", "fact_value_text": "Exalted"}]
        conn = _make_conn([d1_rows, d9_rows])
        signals = _build_navamsha_cross_check_signals(
            conn, "chart-1", "lahiri_chitrapaksha", "build-1",
            "2026-06-28T00:00:00+00:00",
            strength_lookup={}, dignity_lookup={}, av_lookup={},
        )
        self.assertEqual(len(signals), 1)
        config = json.loads(signals[0]["configuration_jsonb"])
        self.assertEqual(config["classification"], "vargottama_resilience",
                         f"D1=debilitated × D9=exalted → vargottama_resilience; got {config['classification']}")
        self.assertEqual(signals[0]["valence"], "benefic")

    def test_concordant_strong_classification(self):
        """D1=exalted × D9=Own → concordant_strong."""
        d1_rows = [{"fact_subject": "D1_JUP", "fact_value_text": "exalted"}]
        d9_rows = [{"graha": "Jupiter", "fact_value_text": "Own"}]
        conn = _make_conn([d1_rows, d9_rows])
        signals = _build_navamsha_cross_check_signals(
            conn, "chart-1", "lahiri_chitrapaksha", "build-1",
            "2026-06-28T00:00:00+00:00",
            strength_lookup={}, dignity_lookup={}, av_lookup={},
        )
        config = json.loads(signals[0]["configuration_jsonb"])
        self.assertEqual(config["classification"], "concordant_strong")

    def test_signal_type_id_format(self):
        """signal_type_id must be navamsha_d9_cross_check:<graha_lower>."""
        d1_rows = [{"fact_subject": "D1_MAR", "fact_value_text": "own"}]
        d9_rows = [{"graha": "Mars", "fact_value_text": "Exalted"}]
        conn = _make_conn([d1_rows, d9_rows])
        signals = _build_navamsha_cross_check_signals(
            conn, "chart-1", "lahiri_chitrapaksha", "build-1",
            "2026-06-28T00:00:00+00:00",
            strength_lookup={}, dignity_lookup={}, av_lookup={},
        )
        self.assertEqual(signals[0]["signal_type_id"], "navamsha_d9_cross_check:mars")

    def test_all_required_columns_present(self):
        """Every O3 signal row must have all required INSERT columns."""
        conn = self._make_conn()
        signals = _build_navamsha_cross_check_signals(
            conn, "chart-1", "lahiri_chitrapaksha", "build-1",
            "2026-06-28T00:00:00+00:00",
            strength_lookup={}, dignity_lookup={}, av_lookup={},
        )
        required = [
            "signal_id", "chart_id", "ayanamsha_id", "build_id",
            "signal_type_id", "signal_type_class", "signal_tradition",
            "fact_kind", "source_l1_asset", "source_subsystem",
            "signal_summary_text", "signal_headline_text",
            "signature_tier", "valence", "lel_origin",
            "configuration_jsonb", "computed_salience",
            "verification_pass_status", "engine_version",
        ]
        for sig in signals:
            for col in required:
                self.assertIn(col, sig, f"O3 signal missing column: {col}")


# ──────────────────────────────────────────────────────────────────────────────
# _dignity_tier helper
# ──────────────────────────────────────────────────────────────────────────────

class TestDignityTier(unittest.TestCase):

    def test_exalted_tier(self):
        self.assertEqual(_dignity_tier("exalted"), 3)
        self.assertEqual(_dignity_tier("Exalted"), 3)

    def test_debilitated_tier(self):
        self.assertEqual(_dignity_tier("debilitated"), -2)
        self.assertEqual(_dignity_tier("Debilitated"), -2)

    def test_own_tier(self):
        self.assertEqual(_dignity_tier("own"), 2)

    def test_neutral_tier(self):
        self.assertEqual(_dignity_tier("neutral"), 0)
        self.assertEqual(_dignity_tier("Neutral"), 0)

    def test_enemy_tier(self):
        self.assertEqual(_dignity_tier("enemy"), -1)

    def test_unknown_defaults_zero(self):
        self.assertEqual(_dignity_tier(""), 0)
        self.assertEqual(_dignity_tier("something_unknown"), 0)


# ──────────────────────────────────────────────────────────────────────────────
# I2 — shadbala_norm key mapping for navamsha signals
# ──────────────────────────────────────────────────────────────────────────────

class TestI2NavamshaShаdbalaShortKey(unittest.TestCase):
    """I2: navamsha signal shadbala_norm must use the short key via _LONG_TO_SHORT,
    not graha.upper() which produces 'SATURN' instead of 'SAT'."""

    def test_navamsha_shadbala_norm_uses_short_key(self):
        """Saturn long name must resolve to SAT key, not SATURN → not 1.0 fallback."""
        # D1: SAT exalted; D9: Saturn Debilitated → broken_promise signal emitted
        d1_rows = [{"fact_subject": "D1_SAT", "fact_value_text": "exalted"}]
        d9_rows = [{"graha": "Saturn", "fact_value_text": "Debilitated"}]
        conn = _make_conn([d1_rows, d9_rows])

        signals = _build_navamsha_cross_check_signals(
            conn, "chart-1", "lahiri_chitrapaksha", "build-1",
            "2026-06-28T00:00:00+00:00",
            strength_lookup={"SAT": 1.8},
            dignity_lookup={},
            av_lookup={},
        )
        self.assertEqual(len(signals), 1, "Expected exactly one Saturn navamsha signal")
        sat_sig = signals[0]
        self.assertAlmostEqual(
            sat_sig["shadbala_norm"], 1.8, places=3,
            msg=(
                f"shadbala_norm should be 1.8 (SAT key hit); got {sat_sig['shadbala_norm']}. "
                "Bug: graha.upper()='SATURN' misses 'SAT' key and falls back to 1.0."
            ),
        )

    def test_navamsha_shadbala_norm_jupiter_short_key(self):
        """Jupiter long name must resolve to JUP key."""
        d1_rows = [{"fact_subject": "D1_JUP", "fact_value_text": "debilitated"}]
        d9_rows = [{"graha": "Jupiter", "fact_value_text": "Exalted"}]
        conn = _make_conn([d1_rows, d9_rows])

        signals = _build_navamsha_cross_check_signals(
            conn, "chart-1", "lahiri_chitrapaksha", "build-1",
            "2026-06-28T00:00:00+00:00",
            strength_lookup={"JUP": 1.6},
            dignity_lookup={},
            av_lookup={},
        )
        self.assertEqual(len(signals), 1)
        self.assertAlmostEqual(
            signals[0]["shadbala_norm"], 1.6, places=3,
            msg=f"shadbala_norm should be 1.6 (JUP key hit); got {signals[0]['shadbala_norm']}",
        )


if __name__ == "__main__":
    unittest.main()

"""test_bo_wp24_msr_ingestion.py — WP-2.4 MSR ingestion-redesign unit tests.

Covers LCA-9b-1..5 fixes in bo_laksana + the permanent §N.5 referential-integrity
validator. All tests run in-process; no DB required.

  9b-1  flood cap        — per-varga families no longer 1:1; oversized groups
                           collapse to one aggregate rollup citing every member.
  9b-2  re-tiering       — divisional/granular signals barred from major/
                           chart_defining via the tier ceiling.
  9b-3  KP house domains — cusp facts inherit their bhava's domains.
  9b-4  category ingest  — dosha_label / yoga_label build real signals.
  9b-5  constituents     — non-resolving candidates dropped, own fact_id unioned;
                           validator catches breaks and is mutation-proof.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import types
import unittest

# ── Load bo_laksana under a stub package (same pattern as test_bo_a1_fixes) ────
_HERE = os.path.dirname(__file__)
_WRITERS_DIR = os.path.abspath(os.path.join(_HERE, "../../pipeline/orchestrator/writers"))
_SIDECAR_ROOT = os.path.abspath(os.path.join(_HERE, "../.."))
_GOV_DIR = os.path.abspath(os.path.join(_HERE, "../../../scripts/governance"))
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, _SIDECAR_ROOT)


class _WriterBase:  # pragma: no cover
    pass


def _register(asset_id):  # pragma: no cover
    def d(c):
        return c
    return d


class _Stub:  # pragma: no cover
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


_pkg_pipeline = types.ModuleType("pipeline")
_pkg_orch = types.ModuleType("pipeline.orchestrator")
_pkg_writers = types.ModuleType("pipeline.orchestrator.writers")
_pkg_writers.WriterBase = _WriterBase
_pkg_writers.register = _register
_pkg_writers.ContextSpec = _Stub
_pkg_writers.WriterResult = _Stub
_pkg_writers.SubStep = _Stub
_pkg_writers.__path__ = [_WRITERS_DIR]
_pkg_writers.__package__ = "pipeline.orchestrator.writers"
_pkg_orch.writers = _pkg_writers
_pkg_orch.__path__ = [os.path.dirname(_WRITERS_DIR)]
_pkg_pipeline.orchestrator = _pkg_orch
_pkg_pipeline.__path__ = [os.path.dirname(os.path.dirname(_WRITERS_DIR))]
sys.modules.setdefault("pipeline", _pkg_pipeline)
sys.modules.setdefault("pipeline.orchestrator", _pkg_orch)
sys.modules.setdefault("pipeline.orchestrator.writers", _pkg_writers)

_spec = importlib.util.spec_from_file_location(
    "pipeline.orchestrator.writers.bo_laksana",
    os.path.join(_WRITERS_DIR, "bo_laksana.py"),
    submodule_search_locations=[],
)
bo = importlib.util.module_from_spec(_spec)
bo.__package__ = "pipeline.orchestrator.writers"
sys.modules["pipeline.orchestrator.writers.bo_laksana"] = bo
_spec.loader.exec_module(bo)

# Load the standalone validator too
_vspec = importlib.util.spec_from_file_location(
    "msr_referential_integrity",
    os.path.join(_GOV_DIR, "msr_referential_integrity.py"),
)
mri = importlib.util.module_from_spec(_vspec)
sys.modules["msr_referential_integrity"] = mri
_vspec.loader.exec_module(mri)


_NOW = "2026-07-13T00:00:00Z"


# ──────────────────────────────────────────────────────────────────────────────
# 9b-1 — Flood cap
# ──────────────────────────────────────────────────────────────────────────────

class TestFloodCap(unittest.TestCase):
    def _flood_rows(self, n, cat="aspect_jaimini_per_varga", varga="D1"):
        return [
            {"fact_category": cat, "fact_key": f"on_sign_{i}", "fact_id": f"fid{i}",
             "ayanamsha_id": "lahiri_chitrapaksha",
             "fact_value_jsonb": {"varga": varga}}
            for i in range(n)
        ]

    def test_oversized_group_collapses_to_one_aggregate(self):
        rows = self._flood_rows(200)
        passthrough, aggregates = bo._partition_flood(rows)
        self.assertEqual(len(aggregates), 1,
                         "200 per-varga members must collapse to ONE aggregate")
        self.assertEqual(passthrough, [],
                         "no oversized member should pass through 1:1")

    def test_aggregate_cites_every_member_as_constituent(self):
        rows = self._flood_rows(200)
        _, aggregates = bo._partition_flood(rows)
        agg = aggregates[0]
        members = agg["fact_value_jsonb"]["constituent_facts_array"]
        self.assertEqual(len(members), 200,
                         "aggregate must preserve full traceability to all 200 members")
        self.assertEqual(agg["fact_value_jsonb"]["member_count"], 200)

    def test_small_group_stays_1to1(self):
        rows = self._flood_rows(bo.RATIFIED_FLOOD_CAP)  # at the cap => not a flood
        passthrough, aggregates = bo._partition_flood(rows)
        self.assertEqual(aggregates, [], "at-cap group must not aggregate")
        self.assertEqual(len(passthrough), bo.RATIFIED_FLOOD_CAP)

    def test_non_flood_category_untouched(self):
        rows = [{"fact_category": "yoga_label", "fact_key": "y", "fact_id": "y1",
                 "ayanamsha_id": "lahiri_chitrapaksha", "fact_value_jsonb": {}}]
        passthrough, aggregates = bo._partition_flood(rows)
        self.assertEqual(aggregates, [])
        self.assertEqual(len(passthrough), 1)

    def test_separate_vargas_aggregate_separately(self):
        rows = self._flood_rows(50, varga="D1") + self._flood_rows(50, varga="D9")
        _, aggregates = bo._partition_flood(rows)
        self.assertEqual(len(aggregates), 2, "each varga collapses independently")


# ──────────────────────────────────────────────────────────────────────────────
# 9b-2 — Salience re-tiering
# ──────────────────────────────────────────────────────────────────────────────

class TestReTiering(unittest.TestCase):
    def test_per_varga_capped_at_supporting(self):
        # High salience that WOULD be chart_defining is clamped to supporting.
        tier = bo._signature_tier(2.5, bo._tier_ceiling_for("aspect_parashari_per_varga", "D1"))
        self.assertEqual(tier, "supporting")

    def test_non_d1_varga_no_longer_capped(self):
        # Night-1 Doctrine Campaign, Lane 4 (CR-82→CR-65): the blanket
        # "any non-D1 varga fact capped at supporting" rule is RETIRED — it
        # structurally forbade the varga layer from ever reaching
        # major/chart_defining (CR-65's defect: 95.7% of the corpus stuck at
        # 'supporting'). Replaced by ratification-aware weighting +
        # percentile-based tier assignment (_assign_tiers_by_percentile).
        # Only the flood-rollup ceiling (test_flood_family_capped_* below)
        # survives. A non-flood-prone, non-D1 category is now uncapped.
        self.assertIsNone(bo._tier_ceiling_for("graha_dignity", "D9"))

    def test_whole_chart_d1_uncapped(self):
        self.assertIsNone(bo._tier_ceiling_for("yoga_label", "D1"))
        self.assertEqual(bo._signature_tier(2.5, bo._tier_ceiling_for("yoga_label", "D1")),
                         "chart_defining")

    def test_flood_family_capped_even_without_per_varga_suffix(self):
        self.assertEqual(bo._tier_ceiling_for("virupa_drishti", "D1"), "supporting")


# ──────────────────────────────────────────────────────────────────────────────
# 9b-3 — KP house-aware domains
# ──────────────────────────────────────────────────────────────────────────────

class TestKpHouseDomains(unittest.TestCase):
    def test_second_cusp_yields_wealth(self):
        d = bo._assign_domains("cusp_kp_lords", "structural", fact_subject="CUSP_02")
        self.assertIn("wealth", d)

    def test_eleventh_cusp_yields_wealth(self):
        d = bo._assign_domains("cusp_kp_lords", "structural", fact_subject="CUSP_11")
        self.assertIn("wealth", d)

    def test_seventh_cusp_yields_relationship(self):
        d = bo._assign_domains("kp_cuspal_significators", "structural", fact_subject="CUSP_07")
        self.assertIn("relationship", d)

    def test_tenth_cusp_yields_career(self):
        d = bo._assign_domains("cusp_kp_lords", "structural", fact_subject="CUSP_10")
        self.assertIn("career", d)

    def test_house_parse_from_jsonb(self):
        self.assertEqual(bo._parse_house_number(None, {"house": 11}), 11)

    def test_unparseable_house_falls_back(self):
        # No house => not the fixed character|relationship-only bug; falls to default.
        d = bo._assign_domains("cusp_kp_lords", "structural", fact_subject="UNKNOWN")
        self.assertTrue(len(d) >= 1)


# ──────────────────────────────────────────────────────────────────────────────
# 9b-4 + 9b-5 — category ingest + constituent resolution
# ──────────────────────────────────────────────────────────────────────────────

class TestConstituentResolution(unittest.TestCase):
    def _dosha_fact(self):
        return {
            "fact_id": "real_dosha_1",
            "fact_category": "dosha_label",
            "fact_key": "dosha_name",
            "fact_value_text": "Mangal Dosha",
            "ayanamsha_id": "lahiri_chitrapaksha",
            "source_calculation": "brahma_dosha_catalog",
            "fact_value_jsonb": {"constituent_facts_array": ["ghost_ref_xyz"]},
        }

    def test_dosha_label_builds_a_signal(self):
        # 9b-4: dosha_label is ingested (not silently dropped).
        row = bo._build_signal_row(self._dosha_fact(), "c1", "b1", {}, {}, {}, _NOW,
                                   valid_fact_ids={"real_dosha_1"})
        self.assertTrue(row["signal_type_id"].startswith("dosha_label:"))

    def test_nonresolving_candidate_dropped_own_id_unioned(self):
        # 9b-5: the ghost L1 reference is dropped; the own resolving fact_id remains.
        row = bo._build_signal_row(self._dosha_fact(), "c1", "b1", {}, {}, {}, _NOW,
                                   valid_fact_ids={"real_dosha_1"})
        self.assertEqual(row["constituent_facts_array"], ["real_dosha_1"])
        self.assertNotIn("ghost_ref_xyz", row["constituent_facts_array"])

    def test_resolving_candidate_preserved(self):
        f = self._dosha_fact()
        f["fact_value_jsonb"]["constituent_facts_array"] = ["good_ref", "ghost_ref_xyz"]
        row = bo._build_signal_row(f, "c1", "b1", {}, {}, {}, _NOW,
                                   valid_fact_ids={"real_dosha_1", "good_ref"})
        self.assertIn("good_ref", row["constituent_facts_array"])
        self.assertIn("real_dosha_1", row["constituent_facts_array"])
        self.assertNotIn("ghost_ref_xyz", row["constituent_facts_array"])

    def test_every_constituent_resolves_after_build(self):
        # End-to-end §N.5: no emitted constituent is outside the valid set.
        valid = {"real_dosha_1"}
        row = bo._build_signal_row(self._dosha_fact(), "c1", "b1", {}, {}, {}, _NOW,
                                   valid_fact_ids=valid)
        for cf in row["constituent_facts_array"]:
            self.assertIn(cf, valid, f"constituent {cf} does not resolve")


# ──────────────────────────────────────────────────────────────────────────────
# The permanent §N.5 CI validator
# ──────────────────────────────────────────────────────────────────────────────

class TestReferentialIntegrityValidator(unittest.TestCase):
    def test_clean_signals_no_violations(self):
        v = mri.find_unresolved_constituents(
            [{"signal_id": "s", "signal_type_id": "t", "constituent_facts_array": ["a"]}],
            {"a"})
        self.assertEqual(v, [])

    def test_broken_constituent_flagged(self):
        v = mri.find_unresolved_constituents(
            [{"signal_id": "s", "signal_type_id": "dosha_label:x",
              "constituent_facts_array": ["ghost"]}],
            {"a"})
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0].unresolved, ("ghost",))

    def test_empty_constituents_is_legal(self):
        v = mri.find_unresolved_constituents(
            [{"signal_id": "s", "signal_type_id": "t", "constituent_facts_array": []}],
            set())
        self.assertEqual(v, [])

    def test_self_test_passes(self):
        # The DB-free CI gate itself passes (clean clean + mutation caught).
        self.assertEqual(mri._run_self_test(), 0)

    def test_self_test_is_mutation_proof(self):
        # If the core guard is inert, the self-test MUST fail (exit 1).
        orig = mri.find_unresolved_constituents
        try:
            mri.find_unresolved_constituents = lambda signals, valid: []
            self.assertEqual(mri._run_self_test(), 1)
        finally:
            mri.find_unresolved_constituents = orig


if __name__ == "__main__":
    unittest.main()

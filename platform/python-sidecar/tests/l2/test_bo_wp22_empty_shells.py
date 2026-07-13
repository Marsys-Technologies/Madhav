"""test_bo_wp22_empty_shells.py — WP-2.2 / LCA-5 empty-shell writer unit tests.

Proves the previously-inert / never-populated NON-CGM writers now emit rows:

  bodha_contradictions (bo_karanajala._detect_contradictions)
        — R-44e: the engine was inert. Now emits real yoga-vs-dosha tension rows
          (graha-keyed AND domain promise-vs-denial) wherever MSR holds opposing
          yoga/dosha signals on a shared domain.
  bodha_cdlm_domain_rollups / _pattern_clusters (bo_cdlm_summary)
        — never-invoked empty shells. Now deterministically aggregated from cells.
  bodha_rm_chart_summary / _dosha_remedy_bundles / _pattern_remedies (bo_upaya)
        — never-invoked empty shells. Now aggregated from resonances/prescriptions.
  phala_phaladesa.narration_jsonb (ph_phaladesa)
        — was NULL / status='pending'. Now deterministic template narration, non-NULL.

All in-process; no DB. Deferred (§7.3, NOT fabricated): bodha_cdlm_evolution_gradients
and bodha_rm_dasha_windowed_prescriptions — both need L3 dasha-window temporal data.
"""
from __future__ import annotations

import os
import sys
import unittest

_HERE = os.path.dirname(__file__)
_WRITERS_DIR = os.path.abspath(os.path.join(_HERE, "../../pipeline/orchestrator/writers"))
_SIDECAR_ROOT = os.path.abspath(os.path.join(_HERE, "../.."))
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, _SIDECAR_ROOT)


class _Stub:  # pragma: no cover
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


# ── Direct import of the real writers ───────────────────────────────────────────
# The four writers are exercised at the pure-function level (no DB). We import the
# real modules directly: @register() is idempotent for identical re-imports (W2 CI
# hardening), so a plain import is safe under a full-tree `pytest tests/` collection
# and correctly sees the merged writer bodies (e.g. bo_karanajala's yoga_node_subject
# import from bo_bimba). The earlier hand-rolled isolated loader stubbed bo_bimba and
# went stale the moment the writers grew a new cross-module import — replaced here.
from pipeline.orchestrator.writers import bo_karanajala as kj      # noqa: E402
from pipeline.orchestrator.writers import bo_cdlm_summary as cdlm  # noqa: E402
from pipeline.orchestrator.writers import bo_upaya as upaya        # noqa: E402
from pipeline.orchestrator.writers import ph_phaladesa as phd      # noqa: E402

_CID = "482012f1-710e-4a25-994a-93821f5871aa"
_AYA = "lahiri_chitrapaksha"
_BID = "00000000-0000-0000-0000-000000000001"
_NOW = "2026-07-13T00:00:00Z"


def _sig(sid, cls, domains, sal, graha=None, type_id="x"):
    cfg = {"graha": graha} if graha else {}
    return {
        "signal_id": sid, "signal_type_class": cls, "signal_tradition": "parashari",
        "configuration_jsonb": cfg, "domains_affected_array": domains,
        "computed_salience": sal, "verification_pass_status": "documented_approximation",
        "salience_formula_version": "v1.0", "signal_type_id": type_id,
    }


class ContradictionEngineTests(unittest.TestCase):
    def test_emits_domain_promise_vs_denial(self):
        # A wealth yoga AND a wealth dosha → a genuine promise-vs-denial contradiction.
        signals = [
            _sig("11111111-0000-0000-0000-000000000001", "yoga", ["wealth"], 0.8, graha="Jupiter"),
            _sig("22222222-0000-0000-0000-000000000002", "dosha", ["wealth"], 0.6, graha="Saturn"),
        ]
        rows = kj._detect_contradictions(_CID, _AYA, _BID, signals, _NOW)
        self.assertGreater(len(rows), 0, "contradiction engine must emit ≥1 row where MSR holds opposing pairs")
        classes = {r["tension_class"] for r in rows}
        self.assertIn("domain_promise_vs_denial", classes)
        r = rows[0]
        self.assertEqual(r["chart_id"], _CID)
        self.assertTrue(r["domains_affected_array"])
        self.assertGreater(float(r["combined_salience"]), 0)

    def test_emits_graha_keyed_yoga_vs_dosha(self):
        # Same graha (Mars) is a yoga-karaka and a dosha-karaka on shared 'career'.
        signals = [
            _sig("33333333-0000-0000-0000-000000000003", "yoga", ["career"], 0.7, graha="Mars"),
            _sig("44444444-0000-0000-0000-000000000004", "dosha", ["career"], 0.5, graha="Mars"),
        ]
        rows = kj._detect_contradictions(_CID, _AYA, _BID, signals, _NOW)
        self.assertTrue(any(r["tension_class"] == "graha_yoga_vs_dosha" for r in rows))

    def test_no_false_positive_when_domains_disjoint(self):
        # Yoga on career, dosha on health → no shared domain, no graha overlap → 0 rows.
        signals = [
            _sig("55555555-0000-0000-0000-000000000005", "yoga", ["career"], 0.7, graha="Venus"),
            _sig("66666666-0000-0000-0000-000000000006", "dosha", ["health"], 0.5, graha="Saturn"),
        ]
        rows = kj._detect_contradictions(_CID, _AYA, _BID, signals, _NOW)
        self.assertEqual(len(rows), 0)

    def test_pairs_deduped(self):
        signals = [
            _sig("77777777-0000-0000-0000-000000000007", "yoga", ["wealth"], 0.9, graha="Jupiter"),
            _sig("88888888-0000-0000-0000-000000000008", "dosha", ["wealth"], 0.4, graha="Jupiter"),
        ]
        rows = kj._detect_contradictions(_CID, _AYA, _BID, signals, _NOW)
        pairs = [frozenset((r["signal_a_id"], r["signal_b_id"])) for r in rows]
        self.assertEqual(len(pairs), len(set(pairs)), "no duplicate signal pairs")


def _cell(cid, drow, dcol, strength, rel, contradiction=False, sigs=None):
    return {
        "cell_id": cid, "domain_row": drow, "domain_col": dcol,
        "computed_linkage_strength": strength, "cross_domain_contradiction_flag": contradiction,
        "domain_relationship_class": rel, "shared_signal_ids_array": sigs or [],
    }


class CdlmSiblingTests(unittest.TestCase):
    def _cells(self):
        return [
            _cell("c1", "career", "wealth", 1200.0, "positive_moderate", sigs=["s1", "s2"]),
            _cell("c2", "career", "health", 300.0, "positive_weak", True, sigs=["s3"]),
            _cell("c3", "health", "wealth", 50.0, "inverse", sigs=["s4"]),
        ]

    def test_domain_rollups_nonempty(self):
        rows = cdlm._build_rollups(_CID, _AYA, _BID, self._cells(), _NOW)
        self.assertGreater(len(rows), 0)
        domains = {r["domain"] for r in rows}
        self.assertIn("career", domains)
        career = next(r for r in rows if r["domain"] == "career")
        # career participates in c1 (outbound) and c2 (outbound) as domain_row.
        self.assertGreater(float(career["total_outbound_linkage"]), 0)
        self.assertGreaterEqual(career["signal_count_for_domain"], 1)
        self.assertTrue(career["top_3_linked_domains_jsonb"])

    def test_pattern_clusters_nonempty(self):
        rows = cdlm._build_clusters(_CID, _AYA, _BID, self._cells(), _NOW)
        self.assertGreater(len(rows), 0)
        markers = {r["pattern_marker_type"] for r in rows}
        self.assertIn("inverse_linkage_cluster", markers)
        for r in rows:
            self.assertTrue(r["involved_cells_array"])
            self.assertIn(r["predicted_outcome_class"], ("reinforcing", "conflicting", "mixed"))

    def test_empty_cells_yields_no_rows(self):
        self.assertEqual(cdlm._build_rollups(_CID, _AYA, _BID, [], _NOW), [])
        self.assertEqual(cdlm._build_clusters(_CID, _AYA, _BID, [], _NOW), [])


def _res(rid, graha, score, pclass="high"):
    return {"resonance_id": rid, "graha": graha, "resonance_score": score,
            "remedy_priority_class": pclass, "chart_id": _CID}


def _presc(pid, rid, graha, dosha=None, trad="parashari", match=0.7, feas=0.8, acharya=False):
    return {
        "prescription_id": pid, "target_resonance_id": rid, "target_graha": graha,
        "targets_dosha_class": dosha, "tradition": trad, "remedy_category": "mantra",
        "resonance_match_score": match, "feasibility_score": feas,
        "requires_acharya_review_flag": acharya,
        "classical_sources_jsonb": '{"source_id": "BPHS"}',
    }


class RmSiblingTests(unittest.TestCase):
    def _data(self):
        res = [_res("r1", "Saturn", 0.9), _res("r2", "Mars", 0.5, "moderate")]
        presc = [
            _presc("p1", "r1", "Saturn", dosha="sade_sati"),
            _presc("p2", "r1", "Saturn", dosha="sade_sati", acharya=True),
            _presc("p3", "r2", "Mars", dosha="mangal"),
        ]
        return res, presc

    def test_rm_chart_summary(self):
        res, presc = self._data()
        row = upaya._build_rm_summary(_CID, _AYA, _BID, res, presc, "distributed", _NOW)
        self.assertEqual(row["chart_id"], _CID)
        self.assertEqual(row["total_active_dosha_count"], 2)
        self.assertEqual(row["acharya_review_required_count"], 1)
        self.assertEqual(row["primary_dosha_class"], "sade_sati")
        self.assertIn(row["recommended_intensity_class"],
                      ("intensive", "sustained", "moderate", "light"))

    def test_dosha_bundles(self):
        res, presc = self._data()
        rows = upaya._build_dosha_bundles(_CID, _AYA, _BID, presc, _NOW)
        self.assertEqual({r["dosha_class"] for r in rows}, {"sade_sati", "mangal"})
        ss = next(r for r in rows if r["dosha_class"] == "sade_sati")
        self.assertEqual(len(ss["prescription_ids_in_bundle_array"]), 2)

    def test_pattern_remedies(self):
        res, presc = self._data()
        rows = upaya._build_pattern_remedies(_CID, _AYA, _BID, res, presc, _NOW)
        self.assertGreater(len(rows), 0)
        r1 = next(r for r in rows if r["source_id"] == "r1")
        self.assertEqual(r1["remedy_theme"], "strengthen_Saturn")
        self.assertEqual(len(r1["prescription_ids_array"]), 2)


class PhaladesaNarrationTests(unittest.TestCase):
    def test_narration_nonnull_deterministic(self):
        rec = _Stub(
            domain="career", anchor_count=3, clean_anchor_count=2, magnitude="major",
            malleability="semi_influenceable", prediction_window_start="2027-01-01",
            prediction_window_end="2028-01-01", peak_date="2027-06-01",
            confidence_low=0.4, confidence_high=0.7, mitigation_available=True,
            muhurta_available=False, incoming_spillover_count=2,
            pramana_window_status="open", contradiction_summary_jsonb=[{"x": 1}],
        )
        n = phd._build_deterministic_narration(rec)
        self.assertTrue(n["text"], "narration text must be non-empty")
        self.assertIsNone(n["model"], "no LLM model — deterministic")
        self.assertEqual(n["method"], "deterministic_template_v1")
        self.assertIn("career", n["text"])
        self.assertIn("major", n["text"])

    def test_narration_handles_empty_domain(self):
        rec = _Stub(
            domain="health", anchor_count=0, clean_anchor_count=0, magnitude=None,
            malleability=None, prediction_window_start=None, prediction_window_end=None,
            peak_date=None, confidence_low=None, confidence_high=None,
            mitigation_available=False, muhurta_available=False,
            incoming_spillover_count=0, pramana_window_status=None,
            contradiction_summary_jsonb=None,
        )
        n = phd._build_deterministic_narration(rec)
        self.assertTrue(n["text"])  # still produces the "no anchors" sentence


if __name__ == "__main__":
    unittest.main()

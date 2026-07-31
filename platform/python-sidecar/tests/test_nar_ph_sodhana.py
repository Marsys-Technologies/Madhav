"""
test_nar_ph_sodhana.py — SAMAPTI B-NAR-PH narration-fidelity regression for
services/ph_sodhana/engine.py.

Covers the bare-pointer finding "P2 :38, :136" from
00_ARCHITECTURE/briefs/samapti/SAMAPTI_NARRATION_TRIAGE_AND_PARTITION_v1_0.md §4.5
(the describing census is lost per §6.1 — re-derived from the pointer here):

  :38  — the `_g_ladder_ceiling` comment claimed this formula "mirrors ph_nimitta
         engine.py". False since BA-P5B (2026-07-04, commit ab99ada1): ph_nimitta
         replaced its G-LADDER confidence_range model with a structured posterior
         (base_rate x promise_lift x activation_lift x trigger_lift x
         robustness_mod). ph_sodhana's copy was never updated and has been an
         independent, un-synced formula since. Comment corrected in place.

  :136 — `detect_magnitude_drift`'s docstring claimed it checks magnitude against
         "convergence_score quartile" (phala_anchors.confidence's real third
         factor). It does not and structurally cannot: AnchorRow only carries
         `convergence_id` (a kala_convergence FK), never the raw score — wiring
         it in requires the ph_sodhana WRITER (a file this engine-only lane does
         not own, §4.0). The detector actually substitutes confidence_high as a
         proxy. Fixed by naming the substitution honestly in the docstring and
         tagging the returned SodhanaRecord's derivation_ledger_jsonb with an
         explicit `check_basis` key, so no downstream consumer of the
         'magnitude_drift' anomaly (served via
         L4_phala/query_phala_calibration.ts and the generated dossier slices)
         can mistake this for a genuine convergence_score check.

This is the §N.7 item 1 / "what violates this principle" class of defect: a
grade/anomaly assignment keyed off a proxy signal, silently presented as if it
were the actual documented check.
"""
from __future__ import annotations

import os
import sys
import unittest

_HERE = os.path.dirname(__file__)
_SIDECAR_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, _SIDECAR_ROOT)

from services.ph_sodhana import engine as sodhana_engine  # noqa: E402
from services.ph_sodhana.engine import AnchorRow, detect_magnitude_drift  # noqa: E402


def _anchor(**overrides) -> AnchorRow:
    base = dict(
        anchor_id="AID-1", anchor_source="test", domain="career",
        magnitude="pivotal", confidence_high=0.10,  # well below pivotal's 0.80*0.80=0.64
    )
    base.update(overrides)
    return AnchorRow(**base)


class MagnitudeDriftCheckBasisTests(unittest.TestCase):
    """P2 :136 — the record must honestly name its proxy basis."""

    def test_drift_record_carries_check_basis_tag(self):
        rec = detect_magnitude_drift(_anchor())
        self.assertIsNotNone(rec, "fixture must trip the drift condition")
        self.assertEqual(
            rec.derivation_ledger_jsonb.get("check_basis"),
            "confidence_high_proxy_not_convergence_score",
            "magnitude_drift must tag its real basis (confidence_high proxy), "
            "not silently imply a convergence_score check it cannot perform.",
        )

    def test_docstring_names_the_proxy_substitution(self):
        doc = detect_magnitude_drift.__doc__ or ""
        self.assertIn(
            "PROXY", doc.upper(),
            "detect_magnitude_drift's docstring must disclose that confidence_high "
            "substitutes for convergence_score — AnchorRow has no raw score field.",
        )

    def test_recommendation_text_discloses_basis(self):
        rec = detect_magnitude_drift(_anchor())
        self.assertIn("proxy", rec.recommendation_text.lower())


class GLadderCommentStalenessTests(unittest.TestCase):
    """P2 :38 — the ceiling formula must not claim to mirror a dead ph_nimitta model."""

    def test_source_comment_does_not_claim_mirrors_ph_nimitta(self):
        src_path = sodhana_engine.__file__
        with open(src_path, encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn(
            "mirrors ph_nimitta engine.py", source,
            "the stale 'mirrors ph_nimitta engine.py' claim must be removed — "
            "ph_nimitta replaced G-LADDER with a structured posterior at BA-P5B "
            "(2026-07-04) and ph_sodhana's copy was never updated to track it.",
        )

    def test_source_comment_names_ba_p5b_supersession(self):
        src_path = sodhana_engine.__file__
        with open(src_path, encoding="utf-8") as f:
            source = f.read()
        self.assertIn("BA-P5B", source)


if __name__ == "__main__":
    unittest.main()

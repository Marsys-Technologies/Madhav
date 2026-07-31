"""
test_nar_ph_phaladesa.py — SAMAPTI B-NAR-PH narration-fidelity regressions for
pipeline/orchestrator/writers/ph_phaladesa.py.

Covers two findings from
00_ARCHITECTURE/briefs/samapti/SAMAPTI_NARRATION_TRIAGE_AND_PARTITION_v1_0.md §4.5:

  P1-b (:121, root cause :317-359) — `pa.precedent_refs_jsonb` and
  `pa.contradiction_jsonb` are SELECTed from phala_anchors in
  PhPhaladesakWriter._load_domain_summaries but were never assigned onto the
  DomainAnchorSummary the SQL loop builds — so PhaladosaRecord.contradiction_
  summary_jsonb / precedent_refs_jsonb were always None regardless of real
  phala_anchors data, and the "N contradiction signal(s) temper this reading"
  narration branch in _build_deterministic_narration was dead code on every
  build.

  Seed F18 (:69, CONFIRMED §3) — _DOMAIN_LABEL (the writer's label map) omitted
  'transition', a live _ALL_DOMAINS (engine.py) emission domain, so the
  deterministic narration template fell back to the raw slug "transition"
  instead of a proper label, e.g. "The transition domain rests on...".

Both are narration-fidelity defects per CLAUDE.md §N.7 item 6 (an honest null
or a real value beats a value that silently drops real data / a raw slug
standing in for a label).
"""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import MagicMock

_HERE = os.path.dirname(__file__)
_SIDECAR_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, _SIDECAR_ROOT)

from pipeline.orchestrator.writers.ph_phaladesa import (  # noqa: E402
    PhPhaladesakWriter,
    _DOMAIN_LABEL,
    _build_deterministic_narration,
)
from services.ph_phaladesa.engine import _ALL_DOMAINS  # noqa: E402

_CID = "482012f1-710e-4a25-994a-93821f5871aa"


def _row(**overrides):
    base = {
        "anchor_id": "AID-1",
        "domain": "career",
        "magnitude": "major",
        "confidence_low": 0.4,
        "confidence_high": 0.7,
        "malleability": "semi_influenceable",
        "window_start": None,
        "window_end": None,
        "peak_date": None,
        "precedent_refs_jsonb": None,
        "contradiction_jsonb": None,
        "clean_status": "clean",
        "flag_count": 0,
        "pramana_status": "open",
        "pramana_evidence_type": None,
    }
    base.update(overrides)
    return base


class _FakeCursor:
    """Minimal dict_row cursor stand-in: execute() records, fetchall() replays."""

    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, *args, **kwargs):
        return None

    def fetchall(self):
        return list(self._rows)


class _FakeConn:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self, *args, **kwargs):
        return _FakeCursor(self._rows)


class LoadDomainSummariesContradictionTests(unittest.TestCase):
    """P1-b: contradiction_jsonb / precedent_refs_jsonb must reach the summary."""

    def test_contradiction_jsonb_reaches_summary(self):
        contradiction = [{"conflicting_anchor_id": "AID-2", "note": "opposing window"}]
        conn = _FakeConn([_row(contradiction_jsonb=contradiction)])

        writer = PhPhaladesakWriter()
        summaries = writer._load_domain_summaries(conn, _CID)

        self.assertIn("career", summaries)
        self.assertEqual(
            summaries["career"].contradiction_summary, contradiction,
            "pa.contradiction_jsonb must be assigned onto DomainAnchorSummary."
            "contradiction_summary — before the P1-b fix this stayed None even "
            "when the SQL row carried real contradiction data.",
        )

    def test_precedent_refs_jsonb_reaches_summary(self):
        precedents = [{"precedent_event_id": "EVT-9"}]
        conn = _FakeConn([_row(precedent_refs_jsonb=precedents)])

        writer = PhPhaladesakWriter()
        summaries = writer._load_domain_summaries(conn, _CID)

        self.assertEqual(summaries["career"].precedent_refs_jsonb, precedents)

    def test_no_contradiction_row_leaves_summary_none(self):
        """Honest null (§N.7 item 6): no real contradiction data → None, not fabricated."""
        conn = _FakeConn([_row(contradiction_jsonb=None)])

        writer = PhPhaladesakWriter()
        summaries = writer._load_domain_summaries(conn, _CID)

        self.assertIsNone(summaries["career"].contradiction_summary)

    def test_contradiction_flows_through_to_narration_text(self):
        """End-to-end: a real contradiction row must produce the narration sentence."""
        contradiction = [{"a": 1}, {"b": 2}]
        conn = _FakeConn([_row(contradiction_jsonb=contradiction)])

        writer = PhPhaladesakWriter()
        summaries = writer._load_domain_summaries(conn, _CID)
        summary = summaries["career"]

        rec = MagicMock(
            domain="career", anchor_count=1, clean_anchor_count=1,
            magnitude="major", malleability="semi_influenceable",
            prediction_window_start=None, prediction_window_end=None,
            peak_date=None, confidence_low=None, confidence_high=None,
            mitigation_available=False, muhurta_available=False,
            incoming_spillover_count=0, pramana_window_status=None,
            contradiction_summary_jsonb=summary.contradiction_summary,
        )
        narration = _build_deterministic_narration(rec)
        self.assertIn(
            "2 contradiction signal(s)", narration["text"],
            "a real contradiction_jsonb row must reach the served narration text",
        )


class DomainLabelCoverageTests(unittest.TestCase):
    """Seed F18: _DOMAIN_LABEL must cover every _ALL_DOMAINS emission domain."""

    def test_domain_label_covers_all_emitted_domains(self):
        missing = set(_ALL_DOMAINS) - set(_DOMAIN_LABEL.keys())
        self.assertEqual(
            missing, set(),
            f"_DOMAIN_LABEL is missing an entry for emitted domain(s) {missing} — "
            "the narration template falls back to the raw slug for these.",
        )

    def test_transition_domain_has_a_proper_label(self):
        self.assertIn("transition", _DOMAIN_LABEL)
        label = _DOMAIN_LABEL["transition"]
        self.assertNotEqual(label, "transition", "must not be the raw slug")

    def test_transition_narration_does_not_emit_raw_slug(self):
        rec = MagicMock(
            domain="transition", anchor_count=1, clean_anchor_count=1,
            magnitude="minor", malleability="semi_influenceable",
            prediction_window_start=None, prediction_window_end=None,
            peak_date=None, confidence_low=None, confidence_high=None,
            mitigation_available=False, muhurta_available=False,
            incoming_spillover_count=0, pramana_window_status=None,
            contradiction_summary_jsonb=None,
        )
        narration = _build_deterministic_narration(rec)
        self.assertIn("The transition and change domain rests on", narration["text"])
        self.assertNotIn("The transition domain rests on", narration["text"])


if __name__ == "__main__":
    unittest.main()

"""
test_nar_ph_l4_anchors.py — SAMAPTI B-NAR-PH narration-fidelity / C2-002
privacy regression for brahmagyan/phala/l4_anchors.py.

Covers the bare-pointer finding "P2 :211" from
00_ARCHITECTURE/briefs/samapti/SAMAPTI_NARRATION_TRIAGE_AND_PARTITION_v1_0.md §4.5
(the describing census is lost per §6.1 — re-derived from the pointer here).

Re-deriving from :211 (inside ANC.CAREER.2027.01's `notes` literal) led to a
more serious, LIVE defect in the same file's strip_lel_citations() privacy
guard (C2-002): its catch-all regex `[^.]*\\bLEL\\b[^.]*(?:\\.|$)` treats ANY
bare '.' as a sentence terminator — including periods inside a mid-sentence
identifier. ANCHOR_CATALOG's real ANC.HLTH.2026.01 note hits this exactly:

  "...Active LEL chronic patterns: headaches, acrophobia (PATTERN.ACROPHOBIA.01)."

The old regex stopped at the first period inside "PATTERN.ACROPHOBIA",
leaking "ACROPHOBIA.01)." — private health information sourced from LEL —
into the served `notes` field. That is a live C2-002 violation in the very
function that exists to prevent it, discovered against real production
catalog data (not a synthetic string), per this campaign's practice of
re-deriving findings from bare pointers before fixing.

The fix also tidies the dangling space-before-period artifact the
parenthetical stripper leaves on the original :211 note
(ANC.CAREER.2027.01, "...native's US move (LEL EVT.2019 ...)." ->
"...native's US move ." pre-fix).
"""
from __future__ import annotations

import os
import sys
import unittest

_HERE = os.path.dirname(__file__)
_SIDECAR_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, _SIDECAR_ROOT)

from brahmagyan.phala.l4_anchors import (  # noqa: E402
    ANCHOR_CATALOG,
    strip_lel_citations,
)

# The real, live note carrying the leak (verbatim from ANCHOR_CATALOG's
# ANC.HLTH.2026.01 as of this fix — re-derived directly from production data,
# not invented for the test).
_LIVE_LEAKING_NOTE = (
    "Sade Sati Setting phase classically correlates with health issues related "
    "to Moon-ruled areas: mental health, chest, digestion, sleep. 3-signal + "
    "kala → 0.65. Active LEL chronic patterns: headaches, acrophobia "
    "(PATTERN.ACROPHOBIA.01)."
)

_LIVE_DANGLING_ARTIFACT_NOTE = (
    "Every Mahadasha change produces a perceptible discontinuity within ±6 "
    "months. Mercury-to-Ketu is among the sharpest regime changes: Mercury = "
    "analytical/commercial, Ketu = withdrawal/moksha. Historically: "
    "Saturn-to-Mercury MD in 2010 corresponded to native's US move "
    "(LEL EVT.2019 approximate; exact date in LEL gap register)."
)


class MidTokenPeriodPrivacyLeakTests(unittest.TestCase):
    """C2-002: a mid-sentence identifier's internal periods must not let a
    private LEL-sourced sentence survive strip_lel_citations()."""

    def test_acrophobia_health_detail_does_not_leak(self):
        cleaned = strip_lel_citations(_LIVE_LEAKING_NOTE)
        self.assertNotIn(
            "ACROPHOBIA", cleaned.upper(),
            "private health detail (acrophobia) leaked past strip_lel_citations "
            "because its identifier's internal periods fooled the old "
            "bare-period sentence terminator.",
        )
        self.assertNotIn("lel", cleaned.lower())

    def test_no_orphaned_closing_paren_survives(self):
        cleaned = strip_lel_citations(_LIVE_LEAKING_NOTE)
        self.assertNotIn(")", cleaned, "an orphaned ')' means the LEL sentence was only partially stripped")

    def test_non_lel_prefix_of_the_note_is_preserved(self):
        """The privacy guard must not over-delete: the clean lead sentences survive."""
        cleaned = strip_lel_citations(_LIVE_LEAKING_NOTE)
        self.assertIn("Sade Sati Setting phase", cleaned)
        self.assertIn("0.65", cleaned)

    def test_full_anchor_catalog_never_leaks_lel(self):
        """End-to-end: every real ANCHOR_CATALOG note, once cleaned, is LEL-free."""
        for anchor in ANCHOR_CATALOG:
            note = anchor.get("notes", "")
            if not note:
                continue
            cleaned = strip_lel_citations(note)
            self.assertNotIn(
                "lel", cleaned.lower(),
                f"{anchor['anchor_id']}: LEL residue survived cleaning: {cleaned!r}",
            )


class DanglingArtifactTests(unittest.TestCase):
    """The original :211 note (ANC.CAREER.2027.01) must not end with a
    dangling space-before-period artifact after parenthetical removal."""

    def test_no_dangling_space_before_period(self):
        cleaned = strip_lel_citations(_LIVE_DANGLING_ARTIFACT_NOTE)
        self.assertNotIn(" .", cleaned, f"dangling space-before-period artifact: {cleaned!r}")
        self.assertTrue(cleaned.endswith("move."), cleaned)


if __name__ == "__main__":
    unittest.main()

"""
l3_l4_reverification_report.py — WS-2 l3-l4-reverify session output
======================================================================

Re-verifies L3 convergence windows and L4 phala anchors against grounded
L2 bodha signals (post l2-bodha-grounded session: 569/569 signals GROUNDED,
mean match_confidence=0.806).

Key structural insight:
  L3 convergence windows (l3_convergence.py) do NOT consume MSR signals directly.
  They are computed from:
    1. DASHA_PERIODS — FORENSIC §5.1 Vimshottari schedule (weights 0.60-0.90)
    2. SIGNAL_ANCHORS — FORENSIC §2.1 planetary ingress events (weights 0.65-0.90)
  Both are FORENSIC L1 anchors, not MSR corpus signals. Therefore L3 windows
  have NO dependency on L2 grounding status — they are grounded at L1 directly.

  L4 anchors (l4_anchors.py) do consume MSR signals via signal_basis.
  Grounded match_confidence for all 34 unique SIG.MSR.* signals used in L4:
    Min: 0.760  Max: 0.910  Mean: 0.822  All >= 0.50: TRUE
  Since mean_grounded × 1.1 > original_confidence for every anchor, the
  formula anchor_confidence = min(orig, mean_grounded × 1.1) returns orig
  unchanged for all 25 anchors. Delta = 0.000 across the board.

Session: l3-l4-reverify
Branch:  feature/ws2-depth-build
Date:    2026-06-05
Author:  WS-2 autonomous session (Silpī role)
"""

from __future__ import annotations

REVERIFICATION_REPORT = {
    "session_id": "l3-l4-reverify",
    "date": "2026-06-05",
    "branch": "feature/ws2-depth-build",
    "l2_grounding_context": {
        "signals_grounded": 569,
        "coverage_pct": 100.0,
        "mean_match_confidence": 0.806,
        "min_match_confidence_in_l4_signals": 0.760,
        "max_match_confidence_in_l4_signals": 0.910,
        "mean_match_confidence_in_l4_signals": 0.822,
    },

    # ── L3 Convergence Windows ─────────────────────────────────────────────────
    "l3_convergence_windows": {
        "total": 23,
        "still_valid": 23,
        "revised": 0,
        "revised_details": [],
        "validity_rationale": (
            "All 23 convergence windows are STILL_VALID. "
            "l3_convergence.py computes windows from FORENSIC L1 anchors only: "
            "(1) DASHA_PERIODS from FORENSIC §5.1 (weight 0.60-0.90); "
            "(2) SIGNAL_ANCHORS from FORENSIC §2.1 planetary ingress events (weight 0.65-0.90). "
            "Neither source is an MSR corpus signal — they are hardcoded FORENSIC facts. "
            "The L2 grounding exercise (SIG.MSR.* signals) has zero structural impact on L3. "
            "All constituent factor weights are >= 0.45 (dasha_active background), "
            "with all signal_activation events >= 0.65. "
            "Majority-above-0.50 check: 23/23 PASS."
        ),
        "factor_weight_analysis": {
            "all_factors_min_weight_observed": 0.45,  # dasha_active background factor
            "signal_activation_min_weight": 0.65,
            "signal_activation_max_weight": 0.90,
            "dasha_transition_min_weight": 0.60,
            "dasha_transition_max_weight": 0.90,
            "majority_above_050_threshold": "23/23 PASS",
        },
    },

    # ── L4 Phala Anchors ───────────────────────────────────────────────────────
    "l4_anchors": {
        "total": 25,
        "unchanged": 25,
        "changed_gt_0_05": 0,
        "changed_gt_0_10": 0,
        "anchor_updates": [],
        "recomputation_detail": [
            # All 25 anchors: mean_grounded * 1.1 > original_confidence
            # → recomputed = min(orig, mean_grounded × 1.1) = orig
            # → delta = 0.000 for every anchor
            {"anchor_id": "ANC.CAREER.2026.01", "original": 0.72, "mean_grounded": 0.820, "recomputed": 0.720, "delta": 0.000},
            {"anchor_id": "ANC.CAREER.2026.02", "original": 0.61, "mean_grounded": 0.805, "recomputed": 0.610, "delta": 0.000},
            {"anchor_id": "ANC.CAREER.2027.01", "original": 0.75, "mean_grounded": 0.835, "recomputed": 0.750, "delta": 0.000},
            {"anchor_id": "ANC.CAREER.2029.01", "original": 0.58, "mean_grounded": 0.835, "recomputed": 0.580, "delta": 0.000},
            {"anchor_id": "ANC.CAREER.2032.01", "original": 0.68, "mean_grounded": 0.775, "recomputed": 0.680, "delta": 0.000},
            {"anchor_id": "ANC.REL.2026.01",    "original": 0.76, "mean_grounded": 0.840, "recomputed": 0.760, "delta": 0.000},
            {"anchor_id": "ANC.REL.2026.02",    "original": 0.62, "mean_grounded": 0.790, "recomputed": 0.620, "delta": 0.000},
            {"anchor_id": "ANC.REL.2028.01",    "original": 0.55, "mean_grounded": 0.820, "recomputed": 0.550, "delta": 0.000},
            {"anchor_id": "ANC.REL.2030.01",    "original": 0.58, "mean_grounded": 0.820, "recomputed": 0.580, "delta": 0.000},
            {"anchor_id": "ANC.FIN.2026.01",    "original": 0.65, "mean_grounded": 0.835, "recomputed": 0.650, "delta": 0.000},
            {"anchor_id": "ANC.FIN.2026.02",    "original": 0.58, "mean_grounded": 0.820, "recomputed": 0.580, "delta": 0.000},
            {"anchor_id": "ANC.FIN.2028.01",    "original": 0.64, "mean_grounded": 0.850, "recomputed": 0.640, "delta": 0.000},
            {"anchor_id": "ANC.FIN.2034.01",    "original": 0.72, "mean_grounded": 0.850, "recomputed": 0.720, "delta": 0.000},
            {"anchor_id": "ANC.FIN.2038.01",    "original": 0.56, "mean_grounded": 0.820, "recomputed": 0.560, "delta": 0.000},
            {"anchor_id": "ANC.SPR.2026.01",    "original": 0.68, "mean_grounded": 0.820, "recomputed": 0.680, "delta": 0.000},
            {"anchor_id": "ANC.SPR.2027.01",    "original": 0.70, "mean_grounded": 0.835, "recomputed": 0.700, "delta": 0.000},
            {"anchor_id": "ANC.SPR.2030.01",    "original": 0.65, "mean_grounded": 0.790, "recomputed": 0.650, "delta": 0.000},
            {"anchor_id": "ANC.SPR.2031.01",    "original": 0.74, "mean_grounded": 0.800, "recomputed": 0.740, "delta": 0.000},
            {"anchor_id": "ANC.SPR.2033.01",    "original": 0.58, "mean_grounded": 0.820, "recomputed": 0.580, "delta": 0.000},
            {"anchor_id": "ANC.HLTH.2026.01",   "original": 0.65, "mean_grounded": 0.775, "recomputed": 0.650, "delta": 0.000},
            {"anchor_id": "ANC.HLTH.2028.01",   "original": 0.55, "mean_grounded": 0.850, "recomputed": 0.550, "delta": 0.000},
            {"anchor_id": "ANC.HLTH.2032.01",   "original": 0.60, "mean_grounded": 0.865, "recomputed": 0.600, "delta": 0.000},
            {"anchor_id": "ANC.TRANS.2027.01",  "original": 0.67, "mean_grounded": 0.830, "recomputed": 0.670, "delta": 0.000},
            {"anchor_id": "ANC.TRANS.2034.01",  "original": 0.70, "mean_grounded": 0.850, "recomputed": 0.700, "delta": 0.000},
            {"anchor_id": "ANC.TRANS.2040.01",  "original": 0.55, "mean_grounded": 0.835, "recomputed": 0.550, "delta": 0.000},
        ],
        "formula_applied": "anchor_confidence = min(original_anchor_confidence, mean_grounded_signal_confidence × 1.1)",
        "formula_result": (
            "For all 25 anchors: mean_grounded × 1.1 >= original_confidence. "
            "The grounding pass only strengthened signal confidence (min 0.760 > scaffold ~0.50). "
            "All original confidence values are floor-bounded by the calibration rule "
            "(single sig ≤0.55; 2 sigs ≤0.65; 3 sigs ≤0.72; ≥4+kala ≤0.80). "
            "Grounded signals (mean 0.822) × 1.1 = 0.904 >> any anchor's original value. "
            "Therefore no anchor required downward revision."
        ),
        "cvg_signal_treatment": (
            "CVG.* entries in signal_basis (e.g. CVG.003, CVG.009) are convergence window "
            "identifiers (L3 cross-references), not MSR signals. They are excluded from the "
            "mean_grounded computation; only SIG.MSR.* signals are looked up in the grounded corpus. "
            "CVG references are satisfied by L3's own PASS status (STILL_VALID: 23/23)."
        ),
    },

    # ── Overall verdict ────────────────────────────────────────────────────────
    "overall_verdict": "PASS",
    "verdict_rationale": (
        "PASS: Both threshold criteria met with margin. "
        "(1) L3: 23/23 (100%) convergence windows STILL_VALID >= 90% threshold. "
        "(2) L4: 0 anchors changed by > 0.10 <= 3 threshold. "
        "The L2 bodha grounding exercise produced strictly positive results for the "
        "instrument: all 34 SIG.MSR.* signals used in L4 anchors grounded to "
        "match_confidence >= 0.760 (mean 0.822), well above the scaffold placeholder "
        "confidence they implicitly carried before WS-3. "
        "L3 windows are structurally independent of MSR grounding — they are "
        "computed from FORENSIC L1 dasha + transit anchors only. "
        "No L3 window or L4 anchor requires revision. "
        "red-team-is8b session is now unblocked."
    ),

    "provenance": {
        "grounding_source": "brahmagyan/bodha/l2_grounded_batch_1-6.py (WS-2 l2-bodha-grounded session)",
        "l3_source": "brahmagyan/kala/l3_convergence.py + l3_obstruction.py",
        "l4_source": "brahmagyan/phala/l4_anchors.py",
        "forensic_anchor": "FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1 §2.1 §22",
        "msr_anchor": "MSR_v5_0.md (573 signals; 569 loaded)",
        "session_date": "2026-06-05",
        "layer": "L3 Kāla + L4 Phala reverification",
    },
}


if __name__ == "__main__":
    import json
    print(json.dumps(REVERIFICATION_REPORT, indent=2, default=str))
    print()
    print(f"Overall verdict: {REVERIFICATION_REPORT['overall_verdict']}")
    print(f"L3 still_valid: {REVERIFICATION_REPORT['l3_convergence_windows']['still_valid']}/23")
    print(f"L4 unchanged:   {REVERIFICATION_REPORT['l4_anchors']['unchanged']}/25")
    print(f"L4 delta>0.10:  {REVERIFICATION_REPORT['l4_anchors']['changed_gt_0_10']}/25")

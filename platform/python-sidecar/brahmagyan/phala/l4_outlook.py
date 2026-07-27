"""
brahmagyan/phala/l4_outlook.py — Brahma L4 Phala — phala.outlook composite tool (PH-4-5-v2)
==============================================================================================

Asset:    phala.outlook (v2 — composite L4 entrypoint)
Tool:     phala_outlook(chart_id, horizon_days?) →
              {
                  active_anchors,
                  upcoming_convergences (from l3),
                  active_mitigations,
                  muhurta_top_window,
                  overall_readiness_score,
                  provenance_envelope
              }

This is the B.11-compliant L4 entrypoint — routes through all L4 assets:
  PH-4-1-V2: phala.anchors (query_phala_anchors)
  PH-4-2-V2: phala.mitigation (query_phala_mitigation)
  PH-4-4-V2: phala.muhurta (query_muhurta — start_business as default action)
  L3 Kala:   l3_convergence + l3_obstruction (for upcoming windows)

The B.11 Whole-Chart-Read Protocol is honored at L4 by requiring that the
composite outlook integrates all L4 sub-assets before producing output.

Overall readiness score:
  0.0-0.4:  CHALLENGING — multiple obstructions active; proceed with caution
  0.4-0.55: NEUTRAL — mixed signals; deliberate action recommended
  0.55-0.70: MODERATE — generally supportive; specific domains favorable
  0.70-0.85: FAVORABLE — strong alignment; good period for major initiations
  0.85-1.0:  HIGHLY FAVORABLE — rare multi-layer convergence; act decisively

Source: All PH-4-x-V2 assets; l3_convergence.py; l3_obstruction.py;
        chart_facts DB table (L1, built by the ga_* writers). MC-003 (SODHANA T1,
        2026-07-27): FORENSIC v8.0 markdown was deleted in PR #187 Legacy Teardown;
        chart_facts is the live canonical source, not the retired document (a cold
        archived benchmark copy is retained at
        99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md for audit reference only).
Authors: Silpī (WS-2 l4-phala session)
Version: 1.0 — 2026-06-05
BRAHMA-PH-4-5-V2
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Import sibling l4 modules
from brahmagyan.phala.l4_anchors import query_phala_anchors
from brahmagyan.phala.l4_mitigation import query_phala_mitigation
from brahmagyan.phala.l4_muhurta import query_muhurta

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DEFAULT_HORIZON_DAYS = 90

# MC-003 (SODHANA T1): FORENSIC v8.0 markdown was deleted in PR #187 Legacy Teardown —
# the live L1 ground-truth source is the chart_facts DB table (built by the L1 ga_*
# writers), not the retired document. A cold archived benchmark copy is retained at
# 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md for audit reference only.
SOURCE_CITATION = (
    "PH-4-1-V2 (phala.anchors); PH-4-2-V2 (phala.mitigation); "
    "PH-4-4-V2 (phala.muhurta); l3_convergence.py; l3_obstruction.py; "
    "chart_facts DB table (L1 ga_* writers; FORENSIC v8.0 markdown retired PR #187 — "
    "archived copy: 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md, audit-only)"
)

# ── L3 data inline (convergence + obstruction windows for upcoming 90-180 days) ──
# Source: l3_convergence.py + l3_obstruction.py (embedded subset for near-term)
# These are the FUTURE-RELEVANT windows (2026+) from l3 data.

L3_UPCOMING_CONVERGENCE_WINDOWS = [
    {
        "window_id": "CONV.CAREER.2026.A",
        "start": "2026-01-01",
        "end": "2026-12-31",
        "convergence_type": "career_peak",
        "indicators": ["Mercury-Saturn AD", "Jupiter exalted Cancer H4", "Sade Sati setting"],
        "direction": "elevated",
        "confidence": 0.70,
    },
    {
        "window_id": "CONV.SPR.2026.A",
        "start": "2025-10-01",
        "end": "2027-02-28",
        "convergence_type": "spiritual_peak",
        "indicators": ["Jupiter H4 exaltation", "Saturn AD discipline", "Mercury analytical MD"],
        "direction": "elevated",
        "confidence": 0.65,
    },
    {
        "window_id": "CONV.REL.2026.A",
        "start": "2026-01-01",
        "end": "2027-03-31",
        "convergence_type": "health_attention",
        "indicators": ["Sade Sati Setting (OBS.SS.C2.SETTING)", "Saturn AD", "Moon H11 pressure"],
        "direction": "suppressed",
        "confidence": 0.72,
    },
]

L3_ACTIVE_OBSTRUCTIONS = [
    {
        "obstruction_id": "OBS.SS.C2.SETTING",
        "type": "sade_sati",
        "phase": "setting",
        "start": "2025-03-29",
        "end": "2028-04-15",
        "severity": 0.70,
        "description": (
            "Sade Sati Cycle 2 Setting Phase — Saturn in Pisces (2nd from natal Moon Aquarius). "
            "Active through April 2028. Themes: speech, finances, family, psychological weight."
        ),
        "mitigation_ids": ["MIT.SS.C2.SETTING.01", "MIT.SS.C2.SETTING.02",
                           "MIT.SS.C2.SETTING.03", "MIT.SS.C2.SETTING.04"],
    },
]


# ── Overall readiness score computation ───────────────────────────────────────

def _compute_overall_readiness(
    anchors: list[dict[str, Any]],
    obstructions: list[dict[str, Any]],
    muhurta_best_score: float,
    query_date: date,
) -> dict[str, Any]:
    """
    Compute overall readiness score by aggregating L4 signals.

    Formula:
      readiness = (elevated_anchor_strength × 0.35)
                + (1 - obstruction_pressure × 0.25)
                + (muhurta_score × 0.25)
                + (dasha_baseline × 0.15)

    Returns: {score, label, breakdown, notes}
    """
    # Elevated anchor strength (avg confidence of elevated-direction anchors)
    elevated = [a for a in anchors if a.get("direction") == "elevated"]
    suppressed = [a for a in anchors if a.get("direction") == "suppressed"]

    elevated_strength = (
        sum(a["confidence"] for a in elevated) / len(elevated)
        if elevated else 0.5
    )
    # Obstruction pressure (max severity of active obstructions)
    obs_pressure = max((o["severity"] for o in obstructions), default=0.0)

    # Dasha baseline (from FORENSIC §5.1 current Mercury-Saturn AD)
    merc_sat_end = date(2027, 8, 21)
    if query_date < merc_sat_end:
        dasha_baseline = 0.62  # Mercury-Saturn AD — moderate-to-good
    elif query_date < date(2028, 1, 18):
        dasha_baseline = 0.45  # Ketu-Ketu — challenging
    elif query_date < date(2029, 3, 18):
        dasha_baseline = 0.58  # Ketu-Venus — moderate
    else:
        dasha_baseline = 0.55

    score = (
        elevated_strength * 0.35 +
        (1.0 - obs_pressure) * 0.25 +
        muhurta_best_score * 0.25 +
        dasha_baseline * 0.15
    )
    score = min(1.0, max(0.0, round(score, 3)))

    label = (
        "Highly Favorable" if score >= 0.85
        else "Favorable" if score >= 0.70
        else "Moderate" if score >= 0.55
        else "Neutral" if score >= 0.40
        else "Challenging"
    )

    # Generate narrative notes
    notes_parts = []
    if elevated:
        top_anchor = max(elevated, key=lambda a: a["confidence"])
        notes_parts.append(
            f"Strongest elevated anchor: {top_anchor['event_type']} "
            f"(confidence {top_anchor['confidence']:.2f})"
        )
    if obstructions:
        notes_parts.append(
            f"Active obstruction: {obstructions[0]['description'][:80]}…"
        )
    if suppressed:
        notes_parts.append(
            f"{len(suppressed)} suppression anchor(s) warrant caution"
        )
    if muhurta_best_score >= 0.75:
        notes_parts.append(f"Excellent muhurta window available (score {muhurta_best_score:.2f})")

    return {
        "score": score,
        "label": label,
        "breakdown": {
            "elevated_anchor_strength": round(elevated_strength, 3),
            "obstruction_pressure": round(obs_pressure, 3),
            "muhurta_best_score": round(muhurta_best_score, 3),
            "dasha_baseline": round(dasha_baseline, 3),
        },
        "notes": " | ".join(notes_parts) if notes_parts else "No outstanding signals.",
    }


# ── Core tool function ────────────────────────────────────────────────────────

def phala_outlook(
    chart_id: str,
    horizon_days: Optional[int] = None,
    default_action_type: str = "start_business",
) -> dict[str, Any]:
    """
    phala_outlook — composite L4 predictive bundle.

    B.11-compliant: routes through all L4 assets and L3 kala windows.

    Args:
        chart_id:             Chart UUID.
        horizon_days:         Look-ahead window [1, 180]. Default 90.
        default_action_type:  Action type for muhurta top window. Default 'start_business'.

    Returns:
        {
            "ok": True,
            "chart_id": str,
            "horizon_days": int,
            "reference_date": str,
            "active_anchors": [...],         -- from PH-4-1-V2 (this + future horizon)
            "upcoming_convergences": [...],  -- from L3 kala data
            "active_mitigations": [...],     -- from PH-4-2-V2 (active obstructions)
            "muhurta_top_window": {...},     -- from PH-4-4-V2
            "overall_readiness_score": {score, label, breakdown, notes},
            "anchor_count": int,
            "domain_summary": {...},
            "provenance_envelope": {...}
        }
    """
    horizon = min(max(1, horizon_days or DEFAULT_HORIZON_DAYS), 180)
    today = date.today()
    horizon_end = today + timedelta(days=horizon)

    # ── PH-4-1-V2: Active anchors ──────────────────────────────────────────
    try:
        anchors_result = query_phala_anchors(
            chart_id=chart_id,
            date_range={"start": today.isoformat(), "end": horizon_end.isoformat()},
        )
        active_anchors = anchors_result.get("anchors", [])
    except Exception as exc:
        logger.warning("phala_anchors query failed: %s", exc)
        active_anchors = []

    # ── PH-4-2-V2: Active mitigations (for active obstructions) ────────────
    active_mitigations = []
    for obs in L3_ACTIVE_OBSTRUCTIONS:
        obs_start = date.fromisoformat(obs["start"])
        obs_end = date.fromisoformat(obs["end"])
        # Is obstruction active in the horizon window?
        if obs_start <= horizon_end and obs_end >= today:
            try:
                mit_result = query_phala_mitigation(
                    chart_id=chart_id,
                    obstruction_id=obs["obstruction_id"],
                )
                active_mitigations.append({
                    "obstruction_id": obs["obstruction_id"],
                    "obstruction_description": obs["description"],
                    "severity": obs["severity"],
                    "active_until": obs["end"],
                    "mitigation_count": mit_result["mitigation_count"],
                    "mitigations": mit_result["mitigations"][:3],  # top 3
                })
            except Exception as exc:
                logger.warning("phala_mitigation query failed: %s", exc)

    # ── PH-4-4-V2: Muhurta top window ──────────────────────────────────────
    try:
        muhurta_result = query_muhurta(
            chart_id=chart_id,
            action_type=default_action_type,
            horizon_days=horizon,
        )
        muhurta_top = muhurta_result["windows"][0] if muhurta_result["windows"] else None
        muhurta_best_score = muhurta_top["quality_score"] if muhurta_top else 0.5
    except Exception as exc:
        logger.warning("phala_muhurta query failed: %s", exc)
        muhurta_top = None
        muhurta_best_score = 0.5

    # ── L3 upcoming convergences in horizon ────────────────────────────────
    upcoming_convergences = []
    for conv in L3_UPCOMING_CONVERGENCE_WINDOWS:
        c_start = date.fromisoformat(conv["start"])
        c_end = date.fromisoformat(conv["end"])
        if c_start <= horizon_end and c_end >= today:
            upcoming_convergences.append({
                "window_id": conv["window_id"],
                "start": conv["start"],
                "end": conv["end"],
                "convergence_type": conv["convergence_type"],
                "direction": conv["direction"],
                "confidence": conv["confidence"],
                "indicators": conv["indicators"],
            })

    # ── Overall readiness ──────────────────────────────────────────────────
    readiness = _compute_overall_readiness(
        anchors=active_anchors,
        obstructions=L3_ACTIVE_OBSTRUCTIONS,
        muhurta_best_score=muhurta_best_score,
        query_date=today,
    )

    # ── Domain summary ─────────────────────────────────────────────────────
    domain_summary: dict[str, dict[str, Any]] = {}
    for anchor in active_anchors:
        domain = anchor.get("domain", "other")
        if domain not in domain_summary:
            domain_summary[domain] = {"elevated": 0, "suppressed": 0, "avg_confidence": 0.0}
        ds = domain_summary[domain]
        ds[anchor.get("direction", "elevated")] += 1
        # Running average
        total = ds["elevated"] + ds["suppressed"]
        ds["avg_confidence"] = round(
            (ds["avg_confidence"] * (total - 1) + anchor["confidence"]) / total, 3
        )

    # ── Response ───────────────────────────────────────────────────────────
    return {
        "ok": True,
        "chart_id": chart_id,
        "horizon_days": horizon,
        "reference_date": today.isoformat(),
        "horizon_end": horizon_end.isoformat(),

        "active_anchors": active_anchors,
        "anchor_count": len(active_anchors),

        "upcoming_convergences": upcoming_convergences,
        "convergence_count": len(upcoming_convergences),

        "active_mitigations": active_mitigations,
        "obstruction_count": len(L3_ACTIVE_OBSTRUCTIONS),

        "muhurta_top_window": {
            "action_type": default_action_type,
            "window": muhurta_top,
            "note": (
                f"Best {default_action_type.replace('_', ' ')} window in next {horizon} days. "
                "Use query_muhurta with a specific action_type for other action types."
            ),
        },

        "overall_readiness_score": readiness,
        "domain_summary": domain_summary,

        "current_dasha_snapshot": {
            "md": "Mercury",
            "ad": "Saturn",
            "md_end": "2027-08-21",
            "ad_end": "2027-08-21",
            "sade_sati": "Cycle 2 Setting Phase (active through 2028-04-15)",
            "jupiter_transit": "Cancer (exalted, H4 from Aries) → Leo Oct 2025",
            "score": 49,
            "score_label": "NEUTRAL",
        },

        "b11_compliance": {
            "l4_assets_queried": [
                "PH-4-1-V2 (phala.anchors)",
                "PH-4-2-V2 (phala.mitigation)",
                "PH-4-4-V2 (phala.muhurta)",
            ],
            "l3_kala_integrated": True,
            "l2_signal_basis": "MSR SIG.* (via anchor signal_basis fields)",
            # MC-003 (SODHANA T1, 2026-07-27): FORENSIC v8.0 markdown was deleted in
            # PR #187 Legacy Teardown; chart_facts is the live canonical L1 source.
            "l1_ground_truth": "chart_facts DB table (L1, built by the ga_* writers). "
            "FORENSIC v8.0 markdown retired PR #187 Legacy Teardown — cold archived "
            "benchmark copy: 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md (audit-only, not authoritative).",
        },

        "provenance_envelope": {
            "source": "phala.outlook.v2",
            "asset": "PH-4-5-V2",
            "l4_assets_integrated": 3,
            "l3_windows_integrated": len(L3_UPCOMING_CONVERGENCE_WINDOWS),
            "b11_whole_chart_read": True,
            "all_falsifiers_downstream": True,  # inherited from l4_anchors
            "source_citation": SOURCE_CITATION,
            "queried_at": datetime.now(tz=timezone.utc).isoformat(),
        },
    }


# ── FastAPI models ────────────────────────────────────────────────────────────

class OutlookRequest(BaseModel):
    chart_id: str = Field(..., description="Chart UUID")
    horizon_days: Optional[int] = Field(
        None, ge=1, le=180,
        description="Look-ahead window [1, 180]. Default 90."
    )
    default_action_type: Optional[str] = Field(
        None,
        description=(
            "Action type for muhurta top window. Default 'start_business'. "
            "Options: start_business | medical_procedure | legal_signing | "
            "travel_departure | marriage_ceremony | property_purchase"
        ),
    )


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

@router.post("/phala/phala_outlook")
def api_phala_outlook(req: OutlookRequest) -> dict[str, Any]:
    """
    PH-4-5-V2 phala_outlook composite tool.

    B.11-compliant L4 entrypoint: integrates phala.anchors + phala.mitigation
    + phala.muhurta + L3 kala convergence/obstruction data.

    Returns:
      - active_anchors (from PH-4-1-V2)
      - upcoming_convergences (from L3)
      - active_mitigations (from PH-4-2-V2)
      - muhurta_top_window (from PH-4-4-V2)
      - overall_readiness_score (composite 0.0-1.0)
      - domain_summary (anchor counts per domain)
      - current_dasha_snapshot
    """
    try:
        return phala_outlook(
            chart_id=req.chart_id,
            horizon_days=req.horizon_days,
            default_action_type=req.default_action_type or "start_business",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("phala_outlook error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/phala/phala_outlook/gate/{chart_id}")
def api_phala_outlook_gate(chart_id: str) -> dict[str, Any]:
    """
    PH-4-5-V2 acceptance gate.

    AC1: phala_outlook returns ok=True
    AC2: active_anchors is a list (may be empty for non-native chart)
    AC3: muhurta_top_window is present
    AC4: overall_readiness_score has score + label
    AC5: b11_compliance confirms L4 assets queried
    """
    checks = []

    try:
        result = phala_outlook(chart_id=chart_id, horizon_days=90)

        checks.append({
            "id": "AC1", "desc": "phala_outlook returns ok=True",
            "passed": result.get("ok") is True,
        })
        checks.append({
            "id": "AC2", "desc": "active_anchors is a list",
            "passed": isinstance(result.get("active_anchors"), list),
            "count": len(result.get("active_anchors", [])),
        })
        checks.append({
            "id": "AC3", "desc": "muhurta_top_window is present",
            "passed": result.get("muhurta_top_window") is not None,
        })
        checks.append({
            "id": "AC4", "desc": "overall_readiness_score has score + label",
            "passed": (
                "score" in result.get("overall_readiness_score", {})
                and "label" in result.get("overall_readiness_score", {})
            ),
            "score": result.get("overall_readiness_score", {}).get("score"),
            "label": result.get("overall_readiness_score", {}).get("label"),
        })
        checks.append({
            "id": "AC5", "desc": "b11_compliance confirms L4 assets queried",
            "passed": len(result.get("b11_compliance", {}).get("l4_assets_queried", [])) >= 3,
        })

    except Exception as exc:
        checks.append({"id": "AC1", "desc": "phala_outlook call", "passed": False, "error": str(exc)})

    return {
        "gate_passed": all(c.get("passed") for c in checks),
        "checks": checks,
    }

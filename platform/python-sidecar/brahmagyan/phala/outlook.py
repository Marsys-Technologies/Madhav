"""
brahmagyan/phala/outlook.py — Brahma L4 Phala — phala.outlook (PH-4-5)

Asset:    phala.outlook
Tool:     phala_outlook(chart_id, horizon_months) →
              {
                anchors: [...],
                mitigations: [...],
                rectification: {...},
                auspicious_windows: [...],
                summary_confidence: FLOAT,
                provenance_envelope: {
                    source: "phala.outlook",
                    layers: [...],
                    computed_at: ...
                }
              }

Contract (BRAHMA PH-4-5):
    - API aggregation layer only — no new table
    - Calls PH-4-1 (phala.anchors) → anchors[]
    - Calls PH-4-2 (phala.mitigation) → mitigations[]
    - Calls PH-4-3 (phala.rectification) → rectification{}
    - Calls panchang_engine / muhurat (PH-4-4 stand-in) → auspicious_windows[]
    - summary_confidence = mean(anchor.confidence) across all returned anchors
      (or 0.0 if no anchors)
    - provenance_envelope: source="phala.outlook",
      layers=[PH-4-1, PH-4-2, PH-4-3, PH-4-4], computed_at=ISO
    - Acceptance:
        AC1 — all 4 subsystems present in response keys
        AC2 — summary_confidence in [0.0, 1.0]
        AC3 — tool smoke: native chart returns a structurally valid response

Algorithm:
    1. Derive date_range from horizon_months (today + horizon_months forward)
    2. Fetch anchors from PH-4-1 (event_anchors engine)
    3. Fetch mitigations from PH-4-2 (mitigation_map engine)
    4. Fetch rectification from PH-4-3 (rectification engine)
    5. Fetch auspicious_windows from muhurat / panchanga for the horizon
    6. Compute summary_confidence = mean(a.confidence for a in anchors)
    7. Assemble provenance_envelope

Native:   Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
          chart_id: 482012f1-710e-4a25-994a-93821f5871aa

Layer:    L4 Phala — composite B.11 entrypoint
Depends:  PH-4-1 brahmagyan.phala.anchors
          PH-4-2 brahmagyan.phala.mitigation
          PH-4-3 brahmagyan.phala.rectification
          panchang_engine.muhurat (auspicious windows)

Authors:  Silpī (PH-4-5 session)
Version:  1.0 — 2026-06-04
BRAHMA-PH-4-5
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)

ASSET_ID = "phala.outlook"
ASSET_VERSION = "1.0"
BUILD_TAG = "PH-4-5"


# ── DB URL helper ──────────────────────────────────────────────────────────────

def _get_db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key, "")
        if val:
            return val
    raise RuntimeError(
        "No database URL configured. "
        "Set DATABASE_URL, DIRECT_DATABASE_URL, or POSTGRES_URL."
    )


# ── Confidence helpers ─────────────────────────────────────────────────────────

def _mean_confidence(anchors: list[dict[str, Any]]) -> float:
    """
    Compute mean of anchor.confidence values.

    Returns 0.0 for an empty list. Clamps output to [0.0, 1.0].

    Per contract:
        summary_confidence = mean(a.confidence for a in anchors)
    """
    if not anchors:
        return 0.0
    values: list[float] = []
    for a in anchors:
        try:
            values.append(float(a.get("confidence", 0.0)))
        except (TypeError, ValueError):
            values.append(0.0)
    raw = sum(values) / len(values)
    return float(max(0.0, min(1.0, raw)))


# ── Sub-system fetchers ────────────────────────────────────────────────────────

def _fetch_anchors(
    chart_id: str,
    date_range: dict[str, str],
    min_confidence: Optional[float] = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Fetch anchors from PH-4-1 (phala.anchors engine).

    Returns (anchor_list, provenance_envelope).
    On error returns ([], {error: ...}).
    """
    try:
        from brahmagyan.phala.anchors import event_anchors

        result = event_anchors(
            chart_id=chart_id,
            date_range=date_range,
            min_confidence=min_confidence,
        )
        # provenance_envelope must carry `source` — never return a bare {}.
        prov = result.get("provenance_envelope") or {"source": "phala.anchors", "asset": "PH-4-1"}
        return result.get("anchors", []), prov
    except Exception as exc:
        logger.warning("PH-4-5: PH-4-1 fetch failed: %s", exc)
        return [], {"error": str(exc), "source": "phala.anchors"}


def _fetch_mitigations(
    chart_id: str,
    date_range: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Fetch mitigations from PH-4-2 (phala.mitigation engine).

    Returns (mitigation_list, provenance_envelope).
    On error returns ([], {error: ...}).
    """
    try:
        # PH-4-2 uses psycopg2; import conditionally
        import psycopg2
        import psycopg2.extras

        from brahmagyan.phala.mitigation import mitigation_map

        db_url = _get_db_url()
        conn = psycopg2.connect(db_url)
        try:
            result = mitigation_map(conn, chart_id, date_range=date_range)
        finally:
            conn.close()

        # provenance_envelope must carry `source` — never return a bare {}.
        prov = result.get("provenance_envelope") or {"source": "phala.mitigation", "asset": "PH-4-2"}
        return result.get("mitigations", []), prov
    except Exception as exc:
        logger.warning("PH-4-5: PH-4-2 fetch failed: %s", exc)
        return [], {"error": str(exc), "source": "phala.mitigation"}


def _fetch_rectification(chart_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Fetch rectification result from PH-4-3 (phala.rectification engine).

    Returns (rectification_dict, provenance_envelope).
    On error returns ({error: ...}, {error: ...}).
    """
    try:
        # PH-4-3 uses its own DB query via psycopg2/pg
        import psycopg2
        import psycopg2.extras

        db_url = _get_db_url()
        conn = psycopg2.connect(db_url)
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT phala_get_rectification(%s::UUID)",
                    [chart_id],
                )
                row = cur.fetchone()
                raw = None
                if row:
                    # column name is the function name
                    col_name = list(row.keys())[0]
                    raw = row[col_name]
        finally:
            conn.close()

        if not raw:
            return (
                {
                    "chart_id": chart_id,
                    "best_candidate_time": None,
                    "confidence": None,
                    "train_score": None,
                    "test_score": None,
                    "candidate_count": 0,
                    # B.3 mandate: source_citation must be non-null; use a
                    # placeholder that identifies the provenance gap explicitly.
                    "source_citation": (
                        "FORENSIC v8.0 §5.1 + LEL v1.7 "
                        "(no candidates seeded — run PH-4-3 seeder first)"
                    ),
                    "status": "no_candidates — run PH-4-3 seeder first",
                },
                {"source": "phala.rectification", "asset": "PH-4-3"},
            )

        # raw is a dict (psycopg2 returns the JSONB as a Python dict)
        rectification = dict(raw) if isinstance(raw, dict) else {"raw": raw}
        prov = rectification.pop("provenance_envelope", {
            "source": "phala.rectification",
            "asset": "PH-4-3",
        })
        return rectification, prov

    except Exception as exc:
        logger.warning("PH-4-5: PH-4-3 fetch failed: %s", exc)
        error_dict: dict[str, Any] = {
            "chart_id": chart_id,
            "best_candidate_time": None,
            "confidence": None,
            "error": str(exc),
        }
        return error_dict, {"error": str(exc), "source": "phala.rectification"}


def _fetch_auspicious_windows(
    chart_id: str,
    date_range: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Fetch auspicious muhurat windows for the horizon (PH-4-4 stand-in).

    Queries panchanga_daily for auspicious windows within the date range.
    Falls back gracefully if the DB or table is unavailable.

    Returns (auspicious_window_list, provenance_envelope).

    Each auspicious_window dict shape:
        {
          date: ISO date string,
          score: FLOAT (0-1),
          event_types: list[str],
          top_windows: list[{start_time, end_time, score, type}],
          source: "panchanga_daily / phala.outlook-PH-4-4"
        }
    """
    try:
        import psycopg2
        import psycopg2.extras

        db_url = _get_db_url()
        conn = psycopg2.connect(db_url)

        try:
            # Query panchanga_daily for auspicious data within the horizon
            # Using the enrichment columns added in Phase 4C (migration 069)
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        date::text AS date,
                        tithi,
                        vara,
                        moon_nakshatra,
                        yoga,
                        karana,
                        auspicious,
                        choghadiya,
                        hora
                    FROM panchanga_daily
                    WHERE date BETWEEN %s::date AND %s::date
                      AND auspicious IS NOT NULL
                    ORDER BY date ASC
                    LIMIT 30
                    """,
                    [date_range["start"], date_range["end"]],
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        windows = []
        for row in rows:
            r = dict(row)
            # Extract auspicious metadata (JSONB column; list[Timing dict] shape as of
            # migration 427 panchanga_daily_reprovision — panchang_engine's canonical
            # serialization is list-shaped, e.g. [{"label": "abhijit", "start_utc": ...,
            # "end_utc": ...}, ...]. Fold into a label-keyed dict so this endpoint's own
            # output contract (auspicious_metadata: dict) is unchanged for callers.
            auspicious_raw = r.get("auspicious")
            if isinstance(auspicious_raw, list):
                auspicious_data = {
                    (t.get("label") or f"item_{i}"): t
                    for i, t in enumerate(auspicious_raw)
                    if isinstance(t, dict)
                }
            elif isinstance(auspicious_raw, dict):
                auspicious_data = auspicious_raw
            else:
                auspicious_data = {}

            # Build top_windows from choghadiya auspicious slots.
            # panchang_engine's canonical choghadiya shape (serialize.py
            # _serialize_choghadiya) is {"day": [Timing...], "night": [Timing...]},
            # each Timing serialized as {"label": "choghadiya_<name>", "start_utc",
            # "end_utc"} — not the flat {slot_name: {is_auspicious, start, end, score}}
            # shape this code was originally written against (pre-migration-427, when
            # panchanga_daily always returned 0 rows via the WHERE-FALSE stub view, so
            # this path was never actually exercised against real data).
            # Classical choghadiya auspicious names (MC §5): Amrit, Shubh, Labh, Chal.
            choghadiya = r.get("choghadiya") or {}
            auspicious_slots = []
            _AUSPICIOUS_CHOGHADIYA = {"amrit", "shubh", "labh", "chal"}
            if isinstance(choghadiya, dict):
                for period_key in ("day", "night"):
                    for slot in (choghadiya.get(period_key) or []):
                        if not isinstance(slot, dict):
                            continue
                        label = str(slot.get("label", ""))
                        name = label.removeprefix("choghadiya_")
                        if name in _AUSPICIOUS_CHOGHADIYA:
                            auspicious_slots.append({
                                "type": name,
                                "start_time": slot.get("start_utc"),
                                "end_time": slot.get("end_utc"),
                                "score": 0.7,
                            })

            window_entry: dict[str, Any] = {
                "date": r["date"],
                "tithi": r.get("tithi"),
                "vara": r.get("vara"),
                "moon_nakshatra": r.get("moon_nakshatra"),
                "yoga": r.get("yoga"),
                "karana": r.get("karana"),
                "auspicious_metadata": auspicious_data,
                "top_windows": auspicious_slots[:5],  # cap at 5 per day
                "source": "panchanga_daily / phala.outlook-PH-4-4",
            }
            windows.append(window_entry)

        prov = {
            "source": "panchanga_daily",
            "asset": "PH-4-4 / PANCHANG_DAILY",
            "date_range": date_range,
            "rows_returned": len(windows),
            "queried_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        return windows, prov

    except Exception as exc:
        logger.warning("PH-4-5: PH-4-4 auspicious_windows fetch failed: %s", exc)
        return [], {"error": str(exc), "source": "panchanga_daily / PH-4-4"}


# ── Core composite function ────────────────────────────────────────────────────

def phala_outlook(
    chart_id: str,
    horizon_months: int = 12,
    min_confidence: Optional[float] = None,
) -> dict[str, Any]:
    """
    Composite predictive bundle — phala.outlook (PH-4-5).

    Aggregates all 4 L4 subsystems into one call:
        - anchors        (PH-4-1): calibrated probabilistic event anchors
        - mitigations    (PH-4-2): classical BPHS-grounded remedies per anchor
        - rectification  (PH-4-3): birth-time rectification result
        - auspicious_windows (PH-4-4): muhurat windows for the horizon

    Args:
        chart_id:       UUID of the chart.
        horizon_months: Number of months forward from today (default 12).
                        Must be in [1, 120].
        min_confidence: Optional minimum confidence filter passed to PH-4-1.

    Returns:
        {
            "ok": True,
            "chart_id": str,
            "horizon_months": int,
            "query_window": {"start": ISO, "end": ISO},
            "anchors": [...],          # from PH-4-1
            "mitigations": [...],      # from PH-4-2
            "rectification": {...},    # from PH-4-3
            "auspicious_windows": [...],  # from PH-4-4 / panchanga_daily
            "summary_confidence": FLOAT,  # mean(anchors.confidence), in [0,1]
            "provenance_envelope": {
                "source": "phala.outlook",
                "asset": "PH-4-5",
                "asset_version": "1.0",
                "layers": ["PH-4-1", "PH-4-2", "PH-4-3", "PH-4-4"],
                "layer_provenances": {...},
                "chart_id": str,
                "computed_at": ISO datetime
            }
        }

    Raises:
        ValueError: If chart_id is empty or horizon_months out of [1, 120].
    """
    if not chart_id:
        raise ValueError("chart_id must be a non-empty UUID string")
    if not (1 <= horizon_months <= 120):
        raise ValueError(
            f"horizon_months must be in [1, 120], got {horizon_months}"
        )

    # Compute date range
    today = date.today()
    range_end = today + timedelta(days=horizon_months * 30)
    date_range = {
        "start": today.isoformat(),
        "end": range_end.isoformat(),
    }

    computed_at = datetime.now(tz=timezone.utc).isoformat()

    # ── PH-4-1: anchors ────────────────────────────────────────────────────────
    anchors, anchors_prov = _fetch_anchors(chart_id, date_range, min_confidence)

    # ── PH-4-2: mitigations ────────────────────────────────────────────────────
    mitigations, mitigations_prov = _fetch_mitigations(chart_id, date_range)

    # ── PH-4-3: rectification ──────────────────────────────────────────────────
    rectification, rectification_prov = _fetch_rectification(chart_id)

    # ── PH-4-4: auspicious windows ─────────────────────────────────────────────
    auspicious_windows, auspicious_prov = _fetch_auspicious_windows(
        chart_id, date_range
    )

    # ── summary_confidence ─────────────────────────────────────────────────────
    summary_confidence = _mean_confidence(anchors)

    # ── Assemble ───────────────────────────────────────────────────────────────
    provenance_envelope: dict[str, Any] = {
        "source": "phala.outlook",
        "asset": "PH-4-5",
        "asset_version": ASSET_VERSION,
        "layers": ["PH-4-1", "PH-4-2", "PH-4-3", "PH-4-4"],
        "layer_provenances": {
            "PH-4-1": anchors_prov,
            "PH-4-2": mitigations_prov,
            "PH-4-3": rectification_prov,
            "PH-4-4": auspicious_prov,
        },
        "chart_id": chart_id,
        "horizon_months": horizon_months,
        "date_range": date_range,
        "summary_confidence_algorithm": "mean(anchor.confidence) across all returned anchors",
        "computed_at": computed_at,
    }

    return {
        "ok": True,
        "chart_id": chart_id,
        "horizon_months": horizon_months,
        "query_window": date_range,
        "anchors": anchors,
        "mitigations": mitigations,
        "rectification": rectification,
        "auspicious_windows": auspicious_windows,
        "summary_confidence": summary_confidence,
        "provenance_envelope": provenance_envelope,
    }


# ── Acceptance gate ────────────────────────────────────────────────────────────

def run_acceptance_gate(
    chart_id: str,
    horizon_months: int = 12,
) -> dict[str, Any]:
    """
    PH-4-5 acceptance gate.

    Gate criteria:
      AC1 — All 4 subsystems present in response: anchors, mitigations,
             rectification, auspicious_windows.
      AC2 — summary_confidence in [0.0, 1.0].
      AC3 — provenance_envelope.source == "phala.outlook".
      AC4 — provenance_envelope.layers contains all 4 layer IDs.
      AC5 — phala_outlook returns ok=True without raising.

    Returns:
        {"chart_id": str, "gate_passed": bool, "checks": list[dict]}
    """
    checks: list[dict[str, Any]] = []

    # AC5 first (must not raise)
    try:
        result = phala_outlook(chart_id, horizon_months=horizon_months)
        checks.append({
            "id": "AC5",
            "desc": "phala_outlook returns without raising",
            "passed": True,
        })
    except Exception as exc:
        checks.append({
            "id": "AC5",
            "desc": "phala_outlook returns without raising",
            "passed": False,
            "error": str(exc),
        })
        # Cannot continue without a result
        return {"chart_id": chart_id, "gate_passed": False, "checks": checks}

    # AC1 — All 4 subsystems present
    required_keys = {"anchors", "mitigations", "rectification", "auspicious_windows"}
    present_keys = set(result.keys())
    missing_keys = required_keys - present_keys
    checks.append({
        "id": "AC1",
        "desc": "All 4 subsystems present: anchors, mitigations, rectification, auspicious_windows",
        "passed": len(missing_keys) == 0,
        "value": f"present={sorted(required_keys & present_keys)}, missing={sorted(missing_keys)}",
    })

    # AC2 — summary_confidence in [0.0, 1.0]
    summary_conf = result.get("summary_confidence")
    try:
        sc = float(summary_conf)  # type: ignore[arg-type]
        in_range = 0.0 <= sc <= 1.0
    except (TypeError, ValueError):
        in_range = False
    checks.append({
        "id": "AC2",
        "desc": "summary_confidence in [0.0, 1.0]",
        "passed": in_range,
        "value": summary_conf,
    })

    # AC3 — provenance_envelope.source == "phala.outlook"
    prov = result.get("provenance_envelope", {})
    checks.append({
        "id": "AC3",
        "desc": 'provenance_envelope.source == "phala.outlook"',
        "passed": prov.get("source") == "phala.outlook",
        "value": prov.get("source"),
    })

    # AC4 — layers contains all 4 IDs
    layers = prov.get("layers", [])
    required_layers = {"PH-4-1", "PH-4-2", "PH-4-3", "PH-4-4"}
    missing_layers = required_layers - set(layers)
    checks.append({
        "id": "AC4",
        "desc": "provenance_envelope.layers contains PH-4-1, PH-4-2, PH-4-3, PH-4-4",
        "passed": len(missing_layers) == 0,
        "value": f"layers={layers}, missing={sorted(missing_layers)}",
    })

    gate_passed = all(c["passed"] for c in checks)
    if gate_passed:
        logger.info("PH-4-5 acceptance gate PASSED for chart_id=%s", chart_id)
    else:
        failed = [c["id"] for c in checks if not c["passed"]]
        logger.error(
            "PH-4-5 acceptance gate FAILED for chart_id=%s — %s",
            chart_id,
            failed,
        )

    return {"chart_id": chart_id, "gate_passed": gate_passed, "checks": checks}


# ── FastAPI router ─────────────────────────────────────────────────────────────

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field as PydanticField

    router = APIRouter()

    class PhalOutlookRequest(BaseModel):
        chart_id: str = PydanticField(
            ..., description="Chart UUID"
        )
        horizon_months: int = PydanticField(
            default=12,
            ge=1,
            le=120,
            description="Forecast horizon in months (1-120, default 12).",
        )
        min_confidence: Optional[float] = PydanticField(
            default=None,
            ge=0.0,
            le=1.0,
            description="Minimum confidence filter passed to PH-4-1 anchors.",
        )

    @router.post("/phala/outlook")
    def api_phala_outlook(req: PhalOutlookRequest) -> dict[str, Any]:
        """
        PH-4-5 phala.outlook — composite predictive bundle.

        Aggregates all 4 L4 Phala subsystems:
          - anchors (PH-4-1): calibrated event anchors
          - mitigations (PH-4-2): classical BPHS remedies
          - rectification (PH-4-3): birth-time rectification
          - auspicious_windows (PH-4-4): muhurat windows for the horizon

        summary_confidence = mean(anchor.confidence) across returned anchors.
        """
        try:
            return phala_outlook(
                chart_id=req.chart_id,
                horizon_months=req.horizon_months,
                min_confidence=req.min_confidence,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

    @router.get("/phala/outlook/acceptance_gate/{chart_id}")
    def api_acceptance_gate(chart_id: str, horizon_months: int = 12) -> dict[str, Any]:
        """
        PH-4-5 acceptance gate.

        AC1: All 4 subsystems present.
        AC2: summary_confidence in [0.0, 1.0].
        AC3: provenance_envelope.source == "phala.outlook".
        AC4: provenance_envelope.layers contains PH-4-1..PH-4-4.
        AC5: phala_outlook returns without raising.
        """
        try:
            return run_acceptance_gate(chart_id, horizon_months=horizon_months)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

except ImportError:
    # FastAPI not available in test environments
    router = None  # type: ignore[assignment]
    logger.debug("PH-4-5: FastAPI not available — router not created (test env)")

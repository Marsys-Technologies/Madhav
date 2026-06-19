"""
ga_prashna_cast — Direct prashna chart build module.

Bypasses the orchestrator adapter (which hardcodes NATIVE_BIRTH) and calls
build_ga_positions(birth_params=question_params) directly for a question-moment chart.

Does NOT commit — caller owns the transaction.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from dateutil.parser import parse as parse_dt

from ga_writers.ga_positions_writer import build_ga_positions, CANONICAL_AYANAMSHAS
from ga_writers.ga_prashna_writer import seed_prashna_judgment, compute_prashna_judgment

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_QUESTION_CLASSES: frozenset[str] = frozenset(
    [
        "marriage",
        "career",
        "litigation_legal",
        "lost_object",
        "health_illness",
        "finance_wealth",
        "travel_journey",
        "property_land",
        "children_progeny",
        "death_longevity",
        "spiritual_religious",
        "enemy_conflict",
    ]
)

_REJECTION_PATTERNS: list[str] = [
    "longitude",
    "degree",
    "sign of",
    "house of",
    "what is",
    "what are",
    "what's",
    "whats",
    "what're",
    " sign?",
    "tell me about",
    "describe",
    "explain",
    "show me",
]

_FORWARD_MARKERS: list[str] = [
    "will ",
    "shall ",
    "should ",
    "can i ",
    "would ",
    "when will",
    "is it possible",
    "are the chances",
    "do i have",
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_prashna_question(question_text: str) -> dict[str, Any]:
    """
    Validate whether the question text is a well-formed Prashna question.

    Returns {"valid": bool, "reason": str}.

    Logic is fully deterministic — no LLM call.
    """
    lower = question_text.lower()

    # Reject chart-data / lookup questions first
    for pat in _REJECTION_PATTERNS:
        if pat in lower:
            return {
                "valid": False,
                "reason": (
                    f"This is not a valid Prashna question — it appears to ask for chart data "
                    f"(matched: '{pat}'). A Prashna question asks about a future event or outcome, "
                    f"e.g. 'Will I get the promotion?'"
                ),
            }

    # Accept forward-looking questions
    for marker in _FORWARD_MARKERS:
        if marker in lower:
            return {"valid": True, "reason": ""}

    # Short question with no markers — reject
    if len(question_text.strip()) < 20:
        return {
            "valid": False,
            "reason": (
                "Question is too short and does not contain a recognisable forward-looking "
                "marker. A Prashna question asks about a future event or outcome, "
                "e.g. 'Will I get the promotion?'"
            ),
        }

    # Longer question — accept by default
    return {"valid": True, "reason": ""}


def cast_prashna_chart(
    *,
    conn,
    build_id: str,
    question_text: str,
    question_class: str,
    prashna_lagna_method: str,
    question_instant: str,
    question_lat: float,
    question_lon: float,
    querent_natal_chart_id: Optional[str] = None,
    kp_number: Optional[int] = None,
    querent_direction: Optional[str] = None,
    active_nostril: Optional[str] = None,
) -> dict[str, Any]:
    """
    Cast a Prashna chart for the question moment and run ga_positions + ga_prashna writers.

    Does NOT commit — caller owns the transaction.

    Returns:
        {
            "chart_id": str (UUID),
            "rows_inserted": int,
            "primary_judgment": dict | None,   # lahiri_chitrapaksha judgment
            "judgment_by_ayanamsha": dict,
        }
    """
    # 1. Validate question_class
    if question_class not in VALID_QUESTION_CLASSES:
        raise ValueError(
            f"Invalid question_class '{question_class}'. "
            f"Must be one of: {sorted(VALID_QUESTION_CLASSES)}"
        )

    # 2. Parse question_instant (ISO-8601) → UTC birth_params
    dt = parse_dt(question_instant)
    if dt.tzinfo is not None:
        # Convert to UTC
        from datetime import timezone
        dt = dt.astimezone(timezone.utc)

    birth_params: dict[str, Any] = {
        "datetime_iso": dt.isoformat(),
        "latitude_deg": question_lat,
        "longitude_deg": question_lon,
        "tz_offset_hours": 0.0,  # already normalized to UTC
        "place_name": "",
        "subject_label": "prashna",
    }

    # 3. Generate UUID for the prashna chart
    prashna_chart_id = str(uuid.uuid4())

    # 4. Insert into prashna_charts
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO prashna_charts (
                chart_id, question_text, question_class,
                querent_natal_chart_id, prashna_lagna_method,
                kp_number, querent_direction, active_nostril,
                question_instant, question_lat, question_lon
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (chart_id) DO NOTHING
            """,
            (
                prashna_chart_id,
                question_text,
                question_class,
                querent_natal_chart_id,
                prashna_lagna_method,
                kp_number,
                querent_direction,
                active_nostril,
                question_instant,
                question_lat,
                question_lon,
            ),
        )

    # 5. Build ga_positions directly with question-moment birth_params
    build_ga_positions(
        chart_id=prashna_chart_id,
        build_id=build_id,
        conn=conn,
        birth_params=birth_params,
    )

    # 6. Seed + compute prashna judgment for each ayanamsha
    total_rows = 0
    judgment_by_ayanamsha: dict[str, Any] = {}

    for ayanamsha_id in CANONICAL_AYANAMSHAS:
        rows = seed_prashna_judgment(conn, prashna_chart_id, ayanamsha_id, build_id)
        total_rows += rows

        if rows > 0:
            judgment = compute_prashna_judgment(conn, prashna_chart_id, ayanamsha_id)
            judgment_by_ayanamsha[ayanamsha_id] = judgment

    primary_judgment = judgment_by_ayanamsha.get("lahiri_chitrapaksha")

    return {
        "chart_id": prashna_chart_id,
        "rows_inserted": total_rows,
        "primary_judgment": primary_judgment,
        "judgment_by_ayanamsha": judgment_by_ayanamsha,
    }

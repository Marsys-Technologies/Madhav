"""
gochara_intensity.enrichment — best-effort natal-anchor resolution for
`ResonanceTarget` rows read live from G-1's `gochara_resonance_map`.

`gochara_grammar.models.ResonanceTarget`'s own docstring is explicit that
"G-2 does not own natal-position resolution ... that is a thin enrichment
step the caller performs from chart_facts before handing a ResonanceTarget
to a primitive." G-2's own tests perform this by hand per-fixture; G-3, to
live-verify against chart 482012f1, needs a real (if best-effort) version of
that step. `enrich_target` resolves what it honestly can from
`chart_facts.graha_position` rows (`ga_positions_writer.py`'s
`fact_category='graha_position'`, `fact_key in
('longitude_sidereal','sign')`, `fact_subject` = graha name or 'LAGNA') and
leaves the rest None -- primitives already degrade gracefully (log + return
[]) when a needed anchor is unresolved, so an under-enriched target never
crashes the engine, it just contributes nothing to X(t)/PERMISSION for the
primitives that need the anchor it lacks.

Resolution coverage (documented, NOT exhaustive -- an honest scope choice):
  - `target_type in ('karaka', 'dasha_lord_portfolio')` where `target_ref`
    names a graha: resolves via that graha's own `graha_position` row
    (longitude_sidereal, sign). This is the full anchor a target needs.
  - `target_type == 'bhava'`: resolves `target_sign` ONLY, via LAGNA's
    `graha_sign_attributes.sign_num` + whole-sign house offset (the same
    whole-sign convention `gochara_grammar.primitives._offset_sign` uses
    internally) -- `target_longitude_deg` is left unresolved (a bhava is a
    30-degree span, not a point; primitives needing an exact degree for a
    bhava target -- degree_contact, station_retro_loop, eclipse_degree,
    planetary_return -- honestly skip it; sign_ingress/av_threshold_state,
    which only need `target_sign`, work fully).
  - `target_type in ('lord', 'sensitive_degree', 'arudha',
    'mechanism_node', 'yoga_constituent')`: NOT resolved here (would
    require house-lord derivation, sensitive-degree fact-category lookups,
    arudha-pada tables, etc. -- each a further live-schema investigation
    beyond this lane's scope; left as a documented gap, honestly
    unenriched rather than silently guessed).
"""
from __future__ import annotations

import logging
from dataclasses import replace
from typing import Optional

from services.gochara_grammar.models import ResonanceTarget
from ._dbutil import safe_rollback

logger = logging.getLogger(__name__)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

_GRAHA_NAMES = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}


def _fetch_graha_position(conn, chart_id: str, subject: str, ayanamsha_id: str) -> Optional[dict]:
    if conn is None:
        return None
    try:
        cur = conn.execute(
            """
            SELECT fact_key, fact_value_text, fact_value_num
              FROM chart_facts
             WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_position'
               AND fact_subject = %s AND fact_key IN ('longitude_sidereal', 'sign')
            """,
            [chart_id, ayanamsha_id, subject],
        )
        rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[enrichment] graha_position read failed for subject=%s: %s", subject, exc)
        safe_rollback(conn)
        return None
    out: dict = {}
    for row in rows:
        d = row if isinstance(row, dict) else dict(zip(["fact_key", "fact_value_text", "fact_value_num"], row))
        if d["fact_key"] == "longitude_sidereal":
            out["longitude_deg"] = float(d["fact_value_num"]) if d.get("fact_value_num") is not None else None
        elif d["fact_key"] == "sign":
            out["sign"] = d.get("fact_value_text")
    return out or None


def enrich_target(
    conn, target: ResonanceTarget, ayanamsha_id: str = "lahiri_chitrapaksha",
) -> ResonanceTarget:
    """Returns a NEW ResonanceTarget (dataclasses.replace, never mutates the
    input) with whatever natal anchors this function could honestly
    resolve. See module docstring for coverage."""
    graha_ref = None
    if target.target_type in ("karaka", "dasha_lord_portfolio") and target.target_ref in _GRAHA_NAMES:
        graha_ref = target.target_ref
    elif target.natal_planet in _GRAHA_NAMES:
        graha_ref = target.natal_planet

    if graha_ref is not None:
        pos = _fetch_graha_position(conn, target.chart_id, graha_ref, ayanamsha_id)
        if pos:
            return replace(
                target,
                target_longitude_deg=pos.get("longitude_deg", target.target_longitude_deg),
                target_sign=pos.get("sign", target.target_sign),
                natal_planet=graha_ref,
            )
        return target

    if target.target_type == "bhava":
        try:
            house_num = int(target.target_ref)
        except (TypeError, ValueError):
            return target
        lagna_pos = _fetch_graha_position(conn, target.chart_id, "LAGNA", ayanamsha_id)
        if lagna_pos and lagna_pos.get("sign"):
            lagna_sign_idx = SIGNS.index(lagna_pos["sign"])
            bhava_sign = SIGNS[(lagna_sign_idx + (house_num - 1)) % 12]
            return replace(target, target_sign=bhava_sign)
        return target

    return target


def enrich_targets(conn, targets: list[ResonanceTarget], ayanamsha_id: str = "lahiri_chitrapaksha") -> list[ResonanceTarget]:
    return [enrich_target(conn, t, ayanamsha_id=ayanamsha_id) for t in targets]


__all__ = ["enrich_target", "enrich_targets", "SIGNS"]

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
('longitude_sidereal','sign')`, `fact_subject` = graha ABBREVIATION or
'LAGNA') and leaves the rest None -- primitives already degrade gracefully
(log + return []) when a needed anchor is unresolved, so an under-enriched
target never crashes the engine, it just contributes nothing to
X(t)/PERMISSION for the primitives that need the anchor it lacks.

`fact_subject` naming CORRECTION (found by the wave verifier, fixed
2026-07-19, live-confirmed via `SELECT DISTINCT fact_subject FROM
chart_facts WHERE chart_id=... AND fact_category='graha_position'` against
chart 482012f1): the live convention is NOT the full Title-case graha name
(`'Venus'`) that G-2's `gochara_grammar.primitives.ALL_GRAHAS` and this
package's own PERMISSION/relevance code use everywhere else -- it is a
3-letter abbreviation (`SUN, MOON, MAR, MER, JUP, VEN, SAT`) with the two
nodes carrying an explicit `_MEAN` suffix (`RAH_MEAN, KET_MEAN`) reflecting
this engine's mean (not true) node convention, plus `'LAGNA'` for the
ascendant. `GRAHA_TO_FACT_SUBJECT` below is the translation table applied
ONLY at this module's query boundary -- every other module in this package
(and all of G-2) keeps using full Title-case graha names throughout, since
that is what `pipeline.transit_search`/`gochara_grammar.primitives`
actually expect as their `planets` argument vocabulary. Before this fix,
`_fetch_graha_position` queried `fact_subject = 'Venus'` (etc.), which
never matches any live row -- graha-anchored targets silently never got
`target_longitude_deg`/`target_sign` (an honest empty-result degrade, not a
crash, but a real signal-loss bug: `guru_shani_double_transit` and
`planetary_return` PERMISSION generators, and every degree/drishti-contact
X(t) contribution for a graha-anchored (karaka/dasha_lord_portfolio)
target, could never fire against live data).

Resolution coverage (documented, NOT exhaustive -- an honest scope choice):
  - `target_type in ('karaka', 'dasha_lord_portfolio')` where `target_ref`
    names a graha: resolves via that graha's own `graha_position` row
    (longitude_sidereal, sign) AND, as of MR-41(b) (PK-R-5, 2026-08-11),
    `target_nakshatra_id` -- derived deterministically from that SAME
    resolved longitude (27 equal divisions; see `_nakshatra_id_from_
    longitude` below), no new DB read. Before MR-41(b), `target_nakshatra_id`
    was never populated anywhere in production enrichment (only
    `resonance_map.build_fixture_targets`'s synthetic fixture rows carried
    one) -- silencing `nakshatra_ingress_tara` and `sarvatobhadra_vedha`
    (gochara_grammar/primitives.py + sarvatobhadra.py) for EVERY
    graha-anchored target, since both primitives honestly return [] when
    `target.target_nakshatra_id is None`. This is the full anchor a
    graha-anchored target needs.
  - `target_type == 'bhava'`: resolves `target_sign` ONLY, via LAGNA's
    `graha_sign_attributes.sign_num` + whole-sign house offset (the same
    whole-sign convention `gochara_grammar.primitives._offset_sign` uses
    internally) -- `target_longitude_deg` AND `target_nakshatra_id` are left
    unresolved (a bhava is a 30-degree span, not a point -- there is no
    single natal DEGREE to derive either an exact longitude or a nakshatra
    from, only a sign; MR-41(b) confirmed this is a structural gap, not a
    missed lookup, and deliberately does NOT invent a point anchor -- e.g.
    from a house cusp -- to manufacture one). Primitives needing an exact
    degree or a nakshatra for a bhava target -- degree_contact,
    station_retro_loop, eclipse_degree, planetary_return,
    nakshatra_ingress_tara, sarvatobhadra_vedha -- honestly skip it;
    sign_ingress/av_threshold_state/kakshya_cell_crossing/gochara_vedha_pair,
    which only need `target_sign`, work fully.
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
from ._dbutil import savepoint_scope
from brahmagyan.graha_vocabulary import norm_graha

logger = logging.getLogger(__name__)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

_GRAHA_NAMES = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}

# MR-41(b) (PK-R-5, 2026-08-11): 27 equal 13°20' divisions, the SAME
# floor(longitude / (360/27)) + 1 convention this codebase already uses in
# several places (services.gochara_v3.mechanisms.w23_tara_bala.
# _longitude_to_nakshatra_index; ga_writers.ga_nakshatra_compute.
# _nakshatra_0based; tests/test_gochara_grammar.py's own
# _target_at_planet_position fixture helper) -- reimplemented locally here
# (rather than importing one of those, which live in unrelated packages/are
# private helpers of a different layer) to keep this module's own dependency
# footprint unchanged; the formula itself is not novel.
NAKSHATRA_ARC_DEG = 360.0 / 27.0


def _nakshatra_id_from_longitude(longitude_deg: float) -> int:
    """1-based nakshatra id (1=Ashwini..27=Revati) from a sidereal longitude."""
    idx = int((longitude_deg % 360.0) / NAKSHATRA_ARC_DEG) + 1
    return max(1, min(27, idx))

# Full Title-case graha name (this package's/G-2's vocabulary everywhere
# else) -> live chart_facts.fact_subject abbreviation. See module docstring
# "fact_subject naming CORRECTION" for provenance/live-verification.
# Values sourced from the graha SSoT (brahmagyan/graha_vocabulary) rather
# than hardcoded literals — ADHIṢṬHĀNA Lane A2 (found via the full-tree
# census; not one of the originally-enumerated retirement targets).
GRAHA_TO_FACT_SUBJECT: dict[str, str] = {
    name: norm_graha(name)
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
}


def _fetch_graha_position(conn, chart_id: str, subject: str, ayanamsha_id: str) -> Optional[dict]:
    """`subject` must already be a live `chart_facts.fact_subject` value
    (a `GRAHA_TO_FACT_SUBJECT` abbreviation, or `'LAGNA'`) -- callers
    translate from the full graha name BEFORE calling this, never here, so
    this function's own contract stays a direct 1:1 pass-through to the
    live column value."""
    if conn is None:
        return None
    try:
        with savepoint_scope(conn, "graha_position"):
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
        fact_subject = GRAHA_TO_FACT_SUBJECT[graha_ref]
        pos = _fetch_graha_position(conn, target.chart_id, fact_subject, ayanamsha_id)
        if pos:
            resolved_lon = pos.get("longitude_deg", target.target_longitude_deg)
            # MR-41(b): derive target_nakshatra_id from the SAME longitude
            # just resolved above -- deterministic, no new DB read. Falls
            # back to whatever the target already carried (normally None)
            # only in the honest degrade case where this graha_position row
            # had a sign but no longitude_sidereal value.
            resolved_nak_id = (
                _nakshatra_id_from_longitude(resolved_lon)
                if resolved_lon is not None
                else target.target_nakshatra_id
            )
            return replace(
                target,
                target_longitude_deg=resolved_lon,
                target_sign=pos.get("sign", target.target_sign),
                target_nakshatra_id=resolved_nak_id,
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
            # MR-41(b) honest skip: target_nakshatra_id (and
            # target_longitude_deg, already left unresolved above this
            # branch) is deliberately NOT populated for bhava targets. A
            # bhava is a 30-degree house span with no single natal DEGREE to
            # derive a point nakshatra from -- only a sign. This is a
            # structural gap (there is no anchor to resolve), not a missed
            # lookup, so no `skipped_reason` field is fabricated on
            # ResonanceTarget (its dataclass shape does not carry one, and
            # adding one is out of this lane's I2-authorized scope); the
            # honest skip is this comment plus the module docstring's
            # "target_type == 'bhava'" resolution-coverage note.
            # nakshatra_ingress_tara / sarvatobhadra_vedha already degrade
            # honestly (empty result, not a crash) when target_nakshatra_id
            # is None -- see each primitive's own docstring.
            return replace(target, target_sign=bhava_sign)
        return target

    return target


def enrich_targets(conn, targets: list[ResonanceTarget], ayanamsha_id: str = "lahiri_chitrapaksha") -> list[ResonanceTarget]:
    return [enrich_target(conn, t, ayanamsha_id=ayanamsha_id) for t in targets]


__all__ = ["enrich_target", "enrich_targets", "SIGNS", "NAKSHATRA_ARC_DEG", "_nakshatra_id_from_longitude"]

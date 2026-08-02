"""
brahmagyan.l0_kp_sublord_division — L0 Brahmagyan: the canonical 249-fold KP
sub-lord division of the sidereal zodiac.

ṢAḌ-DARŚANA campaign · W3K Lane 1 · ANTARYĀMIN ADJUDICATION-7 Part 1
(`00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`):

    "**1. `bg_kp_sublord_division` — L0, `scope='global'`, NEW.** The 249-fold
    division itself: nakṣatra → pāda → sub → sub-sub boundary **spans in sidereal
    longitude**, by Vimśottarī proportional subdivision. This is pure
    chart-independent reference geometry — §N.1's exact definition of `bg_*`."

    Binding sub-ruling: "the table is stored **in sidereal-longitude space and
    carries NO `ayanamsha_key`.** The division of the *sidereal* circle is
    ayanāṃśa-invariant; the ayanāṃśa enters only at the projection of a tropical
    longitude into it."

── WHAT THE 249 ARE, AND WHY THEY ARE 249 (derived here, not asserted) ─────────

Two classical rules compose:

  R1 (Vimśottarī proportional sub-division — BPHS Ch.46's year table, applied to
      arc instead of time). Each nakṣatra spans 360/27 = 13°20'. It is divided
      into nine SUB segments in the fixed Vimśottarī order, STARTING FROM THE
      NAKṢATRA'S OWN LORD, each sub's arc being that planet's Vimśottarī years
      as a fraction of 120:

          sub_span_deg = vimshottari_years / 120 × 360/27 = vimshottari_years / 9

      Exactly: Ketu 7/9°, Venus 20/9°, Sun 6/9°, Moon 10/9°, Mars 7/9°,
      Rahu 18/9°=2°, Jupiter 16/9°, Saturn 19/9°, Mercury 17/9°.
      Per nakṣatra the nine sum to 120/9 = 13°20' exactly. 27 × 9 = **243**
      sub segments over the circle.

  R2 (rāśi cut — the KP convention that a sub-division never straddles a sign,
      because the cusp's SIGN LORD is one of the four KP lordship limbs and must
      be single-valued inside a division). The 12 sign boundaries at multiples of
      30° are applied as cuts.

      Of the 12 sign boundaries, 3 (0°, 120°, 240°) coincide with a nakṣatra
      start and cut nothing; 3 more (60°, 180°, 300°) fall EXACTLY on an interior
      sub boundary and so also cut nothing — at 60° the boundary lands on the
      Saturn/Mercury sub edge inside Mṛgaśira, and likewise at 180° (Citrā) and
      300° (Dhaniṣṭhā), all three being Mars-lorded nakṣatras whose 4th sub edge
      falls at cumulative 60 Vimśottarī years = 60/9 × 60' = 400' = 6°40' into
      the nakṣatra. The remaining **6** boundaries (30°, 90°, 150°, 210°, 270°,
      330°) each fall strictly inside one sub segment and split it in two.

          243 + 6 = **249**

      This module DERIVES that count from R1 and R2; it does not hard-code it.
      `build_divisions()` returns whatever the arithmetic yields, and the tests
      assert the result is 249 — so if the arithmetic were ever wrong, the
      classical figure would fail to reproduce rather than be assumed.

── CITATION TIER (honest, per ADJUDICATION-7's own instruction) ────────────────

R1's numeric content — the Vimśottarī year table and its fixed planetary order —
is tier (i): ingested classical text, BPHS Ch.46, already seeded at L0
(`brahma_dasha_systems.canonical_id='vimshottari'`, `sequence_jsonb`).

R1's APPLICATION to arc rather than time, and R2, are the KP-specific
conventions. ADJUDICATION-7 records that the corpus holds **no ingested KP
text** ("3 chunks matching sub-lord/Krishnamurti terms and all three are false
positives"), so these two conventions sit at tier (iii): published KP reader
convention (K. S. Krishnamurti, *KP Reader* I–III / Stellar Astrology), stated
here as the derivation rule and VERIFIED against a committed fixture — the nine
natal star/sub lords recorded in `05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md` §2
(FORENSIC §4.2 column), which pass 9/9 on both limbs. The corpus gap is FILED as
an ingestion work item per the ruling's "**File that gap.**"

Nothing in this module is a fabricated numeric value: every constant is either a
Vimśottarī year count (BPHS), a count of nakṣatras/rāśis, or exact rational
arithmetic over those.

── SCOPE DISCLOSURE (what this table deliberately does NOT hold) ───────────────

The ruling's phrasing names "nakṣatra → pāda → sub → sub-sub" spans. This table
holds the **sub** level cut by rāśi — i.e. the canonical 249, the object the
ruling's own head noun ("The 249-fold division itself") and the W3K brief name.
It does NOT tabulate the sub-sub (prāṇa-level) grain, which at the same
treatment would be ~2,200 rows and is a different object from "the 249".
Sub-sub/prāṇa remain available from the identical proportional rule at call
time (`ga_writers.ga_nakshatra_compute.compute_kp_lords`). Pāda is carried as
an ATTRIBUTE of each division (`pada_at_start`/`pada_at_end`) rather than as a
further cut, because cutting at pāda boundaries would change the row count away
from the canonical 249. The sub-sub table is PARKED and named as a follow-on,
not silently omitted.

── IDEMPOTENCY ────────────────────────────────────────────────────────────────
L0 = ON CONFLICT DO UPDATE (global, no chart_id), per CLAUDE.md §N.3.

── VERSIONING (§B.8 / §N.3) ───────────────────────────────────────────────────
`table_version` zero-padded (`kp_sublord_division_v01`) per the
`phaladeepika_vedha_v01` / `kota_chakra_rings_vNN` precedent. A revision is a
new `_v02` row set landed by INSERT, never an in-place edit.
"""
from __future__ import annotations

import logging
from fractions import Fraction
from typing import Any

logger = logging.getLogger(__name__)

TABLE_VERSION = "kp_sublord_division_v01"

#: Vimśottarī year allotments. Source: BPHS Ch.46, already seeded at L0 in
#: `brahma_dasha_systems.canonical_id='vimshottari'` (`sequence_jsonb`). Held here
#: because THIS module is the L0 authority that derives the division geometry;
#: `tests/test_bg_kp_sublord_division.py` asserts byte-equality with the L1
#: consumer's copy (`ga_writers.ga_nakshatra_compute.VIMSHOTTARI_YEARS`) so the
#: two can never drift apart silently.
VIMSHOTTARI_YEARS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

#: The fixed Vimśottarī order (BPHS Ch.46). Nakṣatra n (1-based) is lorded by
#: PLANET_CYCLE[(n-1) % 9] — Aśvinī→Ketu, Bharaṇī→Venus, Kṛttikā→Sun, …
PLANET_CYCLE: list[str] = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]

TOTAL_VIMSHOTTARI_YEARS = 120
NAKSHATRA_COUNT = 27
RASHI_COUNT = 12
PADAS_PER_NAKSHATRA = 4

#: Exact rational arcs. Fractions (not floats) throughout the derivation so that a
#: sign boundary falling EXACTLY on a sub boundary is recognised as exact rather
#: than as a float near-miss that would spuriously add a 250th division.
NAK_SPAN_DEG = Fraction(360, NAKSHATRA_COUNT)          # 40/3 = 13°20'
PADA_SPAN_DEG = NAK_SPAN_DEG / PADAS_PER_NAKSHATRA      # 10/3 = 3°20'
RASHI_SPAN_DEG = Fraction(360, RASHI_COUNT)             # 30

SOURCE_CITATION = (
    "[TIER-III] Krishnamurti Paddhati sub-lord division — K. S. Krishnamurti, "
    "KP Reader I-III (Stellar Astrology): each nakshatra is sub-divided in the "
    "Vimshottari order starting from its own lord, each sub's arc proportional to "
    "that lord's Vimshottari years; divisions are further cut at rashi boundaries, "
    "giving 249. Proportional constants are BPHS Ch.46 (TIER-I, ingested; L0 "
    "brahma_dasha_systems.vimshottari). No KP text is ingested in this corpus "
    "(SHAD_DARSHANA_ADJUDICATIONS_NIGHT3 ADJUDICATION-7) — the KP-specific "
    "convention is verified against the committed fixture in "
    "05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md §2, not adjudicated from memory."
)


def _sub_span_deg(planet: str) -> Fraction:
    """Arc of one sub segment: years/120 × 13°20' = years/9 degrees (exact)."""
    return Fraction(VIMSHOTTARI_YEARS[planet], TOTAL_VIMSHOTTARI_YEARS) * NAK_SPAN_DEG


def _pada_at(longitude: Fraction, *, from_left: bool) -> int:
    """1-based pāda (1–4) of a longitude inside its nakṣatra.

    `from_left=False` reads the pāda of the arc ENDING at this longitude (i.e. the
    pāda just before it), which is what a half-open [start, end) division needs at
    its right edge.
    """
    lon = longitude % 360
    if not from_left:
        # The end edge belongs to the arc on its left.
        pos = (lon - Fraction(1, 10**9)) % NAK_SPAN_DEG
    else:
        pos = lon % NAK_SPAN_DEG
    return int(pos / PADA_SPAN_DEG) + 1


def build_sub_segments() -> list[dict[str, Any]]:
    """The 243 raw Vimśottarī sub segments (R1 only, before the rāśi cut)."""
    segments: list[dict[str, Any]] = []
    for nak0 in range(NAKSHATRA_COUNT):
        nak_start = nak0 * NAK_SPAN_DEG
        star_lord = PLANET_CYCLE[nak0 % len(PLANET_CYCLE)]
        start_idx = PLANET_CYCLE.index(star_lord)
        cursor = Fraction(0)
        for i in range(len(PLANET_CYCLE)):
            sub_lord = PLANET_CYCLE[(start_idx + i) % len(PLANET_CYCLE)]
            span = _sub_span_deg(sub_lord)
            segments.append({
                "start": nak_start + cursor,
                "end": nak_start + cursor + span,
                "nakshatra_number": nak0 + 1,
                "star_lord": star_lord,
                "sub_lord": sub_lord,
            })
            cursor += span
    return segments


def build_divisions(table_version: str = TABLE_VERSION) -> list[dict[str, Any]]:
    """The canonical KP sub-lord divisions: R1's 243 sub segments cut at rāśi
    boundaries (R2).

    Returns rows ready for INSERT, ordered by start longitude, `division_index`
    1-based. The row COUNT is derived, never asserted — see the module docstring.
    """
    rashi_boundaries = [k * RASHI_SPAN_DEG for k in range(RASHI_COUNT)]
    rows: list[dict[str, Any]] = []

    for seg in build_sub_segments():
        start, end = seg["start"], seg["end"]
        interior_cuts = [b for b in rashi_boundaries if start < b < end]
        edges = [start, *interior_cuts, end]
        was_split = bool(interior_cuts)
        for a, b in zip(edges, edges[1:]):
            rows.append({
                "start_deg": a,
                "end_deg": b,
                "nakshatra_number": seg["nakshatra_number"],
                "star_lord": seg["star_lord"],
                "sub_lord": seg["sub_lord"],
                "sign_number": int(a / RASHI_SPAN_DEG) + 1,
                "pada_at_start": _pada_at(a, from_left=True),
                "pada_at_end": _pada_at(b, from_left=False),
                "split_by_sign_boundary": was_split,
            })

    rows.sort(key=lambda r: r["start_deg"])

    out: list[dict[str, Any]] = []
    for idx, r in enumerate(rows, start=1):
        span_arcmin = (r["end_deg"] - r["start_deg"]) * 60
        out.append({
            "table_version": table_version,
            "division_index": idx,
            "start_longitude_deg": float(r["start_deg"]),
            "end_longitude_deg": float(r["end_deg"]),
            "span_arcmin": float(span_arcmin),
            "nakshatra_number": r["nakshatra_number"],
            "star_lord": r["star_lord"],
            "sub_lord": r["sub_lord"],
            "sign_number": r["sign_number"],
            "pada_at_start": r["pada_at_start"],
            "pada_at_end": r["pada_at_end"],
            "split_by_sign_boundary": r["split_by_sign_boundary"],
            "source_citation": SOURCE_CITATION,
            # Exact rationals retained for in-process lookup so a consumer never
            # has to re-derive a boundary from the rounded float column.
            "_start_exact": r["start_deg"],
            "_end_exact": r["end_deg"],
        })
    return out


def load_divisions(conn: Any, table_version: str = TABLE_VERSION) -> list[dict[str, Any]]:
    """Read the divisions FROM THE TABLE — the reference read an L1 consumer makes.

    §N.5: `ga_nakshatra` must reference this L0 authority rather than re-derive the
    boundaries for itself, so it calls this (which hits `bg_kp_sublord_division`)
    and never `build_divisions()`. The `_start_exact`/`_end_exact` Fractions are
    reconstructed from the stored NUMERIC columns so `lookup_division` compares
    without float drift.

    Raises if the table is absent or empty: an L1 pass that silently fell back to
    re-deriving the geometry would be exactly the authority inversion §N.5 exists
    to forbid.
    """
    import psycopg.rows as _pr

    with conn.cursor(row_factory=_pr.dict_row) as cur:
        cur.execute(
            """
            SELECT division_index, start_longitude_deg, end_longitude_deg, span_arcmin,
                   nakshatra_number, star_lord, sub_lord, sign_number,
                   pada_at_start, pada_at_end, split_by_sign_boundary
              FROM bg_kp_sublord_division
             WHERE table_version = %s
             ORDER BY division_index
            """,
            (table_version,),
        )
        rows = [dict(r) for r in cur.fetchall()]

    if not rows:
        raise RuntimeError(
            f"HALT: bg_kp_sublord_division holds no rows for table_version="
            f"{table_version!r} — the L0 KP boundary authority must be built before "
            "any L1 KP projection. Run the bg_kp_sublord_division writer first."
        )

    for r in rows:
        r["_start_exact"] = Fraction(r["start_longitude_deg"])
        r["_end_exact"] = Fraction(r["end_longitude_deg"])
    return rows


def lookup_division(longitude_deg: float,
                    divisions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """The division containing a sidereal longitude — the REFERENCE read.

    This is the function an L1 writer calls instead of re-deriving a sub-lord
    boundary for itself (§N.5: reference the authority, inherit its value).
    Half-open [start, end); 360° wraps to 0°.
    """
    divs = divisions if divisions is not None else build_divisions()
    lon = Fraction(longitude_deg).limit_denominator(10**12) % 360
    for d in divs:
        if d["_start_exact"] <= lon < d["_end_exact"]:
            return d
    # Only reachable if the divisions do not tile the circle — which the tests
    # forbid. Raise rather than return a plausible-looking neighbour (§N.7 item 6).
    raise ValueError(
        f"KP sub-lord division not found for longitude {longitude_deg} — "
        "the division table does not tile [0, 360). This is a halt-worthy bug."
    )


# ── Seeding ────────────────────────────────────────────────────────────────────

_INSERT_SQL = """
INSERT INTO bg_kp_sublord_division (
    table_version, division_index,
    start_longitude_deg, end_longitude_deg, span_arcmin,
    nakshatra_number, star_lord, sub_lord, sign_number,
    pada_at_start, pada_at_end, split_by_sign_boundary, source_citation
) VALUES (
    %(table_version)s, %(division_index)s,
    %(start_longitude_deg)s, %(end_longitude_deg)s, %(span_arcmin)s,
    %(nakshatra_number)s, %(star_lord)s, %(sub_lord)s, %(sign_number)s,
    %(pada_at_start)s, %(pada_at_end)s, %(split_by_sign_boundary)s, %(source_citation)s
)
ON CONFLICT (table_version, division_index) DO UPDATE SET
    start_longitude_deg    = EXCLUDED.start_longitude_deg,
    end_longitude_deg      = EXCLUDED.end_longitude_deg,
    span_arcmin            = EXCLUDED.span_arcmin,
    nakshatra_number       = EXCLUDED.nakshatra_number,
    star_lord              = EXCLUDED.star_lord,
    sub_lord               = EXCLUDED.sub_lord,
    sign_number            = EXCLUDED.sign_number,
    pada_at_start          = EXCLUDED.pada_at_start,
    pada_at_end            = EXCLUDED.pada_at_end,
    split_by_sign_boundary = EXCLUDED.split_by_sign_boundary,
    source_citation        = EXCLUDED.source_citation
"""


def verify_star_lords_against_reference(conn: Any) -> dict[str, Any]:
    """Real detector (§N.8): cross-check every division's `star_lord` against the
    L0 nakṣatra authority (`reference_nakshatra.vimshottari_lord`).

    Returns `{"checked": n, "mismatches": [...], "status": ...}` where status is
    one of `two_pass_verified` (every division agreed), `divergent_flagged` (at
    least one disagreed — the caller must halt), or `unverified` (the reference
    table was not available, so NO check ran — reported as unverified, never as a
    pass; §N.8's "a signal without a detector is null, not green").
    """
    import psycopg.rows as _pr

    try:
        with conn.cursor(row_factory=_pr.tuple_row) as cur:
            cur.execute(
                "SELECT nakshatra_id, vimshottari_lord FROM reference_nakshatra "
                "ORDER BY nakshatra_id"
            )
            ref = {int(r[0]): str(r[1]).capitalize() for r in cur.fetchall()}
    except Exception as exc:  # table absent in a bare test DB
        logger.warning(
            "[bg_kp_sublord_division] reference_nakshatra unreadable (%s) — star-lord "
            "cross-check DID NOT RUN; reporting 'unverified', not a pass.", exc,
        )
        return {"checked": 0, "mismatches": [], "status": "unverified"}

    if len(ref) < NAKSHATRA_COUNT:
        logger.warning(
            "[bg_kp_sublord_division] reference_nakshatra holds %d < %d rows — "
            "star-lord cross-check DID NOT RUN; reporting 'unverified'.",
            len(ref), NAKSHATRA_COUNT,
        )
        return {"checked": 0, "mismatches": [], "status": "unverified"}

    mismatches: list[str] = []
    checked = 0
    for d in build_divisions():
        expected = ref.get(d["nakshatra_number"])
        checked += 1
        if expected and expected != d["star_lord"]:
            mismatches.append(
                f"division {d['division_index']} (nakshatra {d['nakshatra_number']}): "
                f"derived star_lord={d['star_lord']} but reference_nakshatra says {expected}"
            )

    return {
        "checked": checked,
        "mismatches": mismatches,
        "status": "divergent_flagged" if mismatches else "two_pass_verified",
    }


def seed_kp_sublord_division(conn: Any, *, dry_run: bool = False,
                             autocommit: bool = False) -> dict[str, int]:
    """Upsert the 249 canonical KP sub-lord divisions (L0 idempotency, §N.3).

    Never commits when `autocommit=False` — the orchestrator owns the transaction
    (§N.2 FROZEN contract).
    """
    rows = build_divisions()

    verdict = verify_star_lords_against_reference(conn)
    if verdict["status"] == "divergent_flagged":
        raise RuntimeError(
            "HALT: bg_kp_sublord_division star_lord disagrees with the L0 nakshatra "
            f"authority (reference_nakshatra): {verdict['mismatches'][:5]}"
        )
    logger.info(
        "[bg_kp_sublord_division] star-lord cross-check: %s (%d divisions checked)",
        verdict["status"], verdict["checked"],
    )

    if dry_run:
        logger.info("[bg_kp_sublord_division] DRY RUN — %d divisions computed, none written",
                    len(rows))
        return {"bg_kp_sublord_division": len(rows)}

    with conn.cursor() as cur:
        for r in rows:
            cur.execute(_INSERT_SQL, {k: v for k, v in r.items() if not k.startswith("_")})

    if autocommit:
        conn.commit()

    logger.info("[bg_kp_sublord_division] seeded %d divisions (version=%s)",
                len(rows), TABLE_VERSION)
    return {"bg_kp_sublord_division": len(rows)}

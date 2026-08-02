"""
ga_writers.ga_kp_significators — the classical 4-limbed KP significator ladder,
per-house AND per-planet.

ṢAḌ-DARŚANA W3K Lane 1 · gap G-1 of `W3K_SUBSTRATE_INVENTORY_v1_0.md` §2 ·
seated by ANTARYĀMIN ADJUDICATION-7 Part 2 ("**`ga_*` — NO NEW ASSET.
`ga_nakshatra` is the standing L1 authority and W3K EXTENDS it** … Any natal KP
fact W3K finds missing is an **amendment to `ga_nakshatra`**, landing as an
additive emitter with `bg_kp_sublord_division` as its boundary authority —
never a restatement of it").

── WHAT WAS MISSING, AND WHY THIS IS NOT A DUPLICATE ───────────────────────────

`chart_facts.kp_cuspal_significators` (emitted by `ga_sensitive_writer.py`)
stores, per cusp, `[sign_lord, star_lord, sub_lord]` — the cusp's own lordship
CHAIN. That is a different object from a KP SIGNIFICATOR: the chain says who owns
the cusp, the significator ladder says which planets will DELIVER that house's
matters. The inventory's §2 G-1 named this precisely and found "no code path
computes this." This module computes it. It does not restate the chain, and it
does not create a second natal-KP writer (duplicate-copy rail) — it is an
additive emitter on the standing `ga_nakshatra` asset.

── THE LADDER (K. S. Krishnamurti, KP Reader IV — "Significators of a House") ──

For a house H, the significators in DESCENDING strength:

  Level A  planets tenanting the STAR (nakṣatra) of an OCCUPANT of H
  Level B  the OCCUPANTS of H
  Level C  planets tenanting the STAR of the OWNER (sign lord) of H
  Level D  the OWNER of H

The star-lord limbs outrank the occupancy/ownership limbs — this is the whole
methodological point of KP and the reason it is a genuinely independent voice
rather than a Parāśarī restatement (SHAD_DARSHANA brief §W3K; and see
`W3K_SUBSTRATE_INVENTORY_v1_0.md` §4 on judgment-method independence vs.
timing-generator independence). A planet appearing at more than one level is
ranked by its STRONGEST (earliest) appearance and appears once in the ranking.

── HOUSE FRAME: KP IS PLACIDUS, THE PROJECT DEFAULT IS WHOLE-SIGN ──────────────

Occupancy and ownership here are read off the **Placidus cusps** already stored
by `ga_positions` (`bhava_cusps`, `house_code='P'` via `drik.bhaava_madhya_swe`),
because KP is a cuspal system: a planet's KP house is the arc it falls in, not
the sign it falls in. The project's primary house frame is whole-sign
(DR-2 / `ga_vargas_writer.py`).

Per Elevation Law 4 and brief §W3K's "the divergence is served as data, never
silently reconciled", the divergence is EMITTED, not resolved: every planet
carries both `kp_cuspal_house` and `whole_sign_house` plus an explicit
`house_system_divergence` flag. Nothing downstream has to guess which frame a
number came from, and neither frame overwrites the other.

── §N.5: THE BOUNDARY AUTHORITY IS REFERENCED, NOT RE-DERIVED ─────────────────

Star lords come from `bg_kp_sublord_division` (L0), passed in as `divisions` and
read via `lookup_division`. This module does NOT contain a Vimśottarī
subdivision. It cross-checks each referenced star/sub lord against the live
`compute_kp_lords` path already used by `emit_kp_lords` in the same build pass —
two independently-implemented derivations (exact rational division table vs.
iterative float accumulation) that could disagree — and records the real verdict
via `two_pass_verdict`. A disagreement is stored as `divergent_flagged` and
logged, never silently reconciled (§N.8; the MSR computed-value-drift trap).

── HONEST GAP, DISCLOSED IN THE DATA ──────────────────────────────────────────

KP's nodal agency rule (Rahu/Ketu signify for the planets they are conjoined
with, the planets aspecting them, their star lord and their sign lord, in that
priority) is NOT applied here: its aspect limb needs an aspect model this
emitter does not own. The nodes therefore appear in the ladder on their own
account only. That omission is emitted as a visible
`nodal_agency_not_applied` row per node rather than left for a reader to
discover — B.10 / §N.7 (an honest empty is reported, never papered over).
"""
from __future__ import annotations

import logging
from typing import Any

from brahmagyan.l0_kp_sublord_division import lookup_division
from brahmagyan.verification_vocab import assert_legal, two_pass_verdict
from ga_writers.ga_nakshatra_compute import compute_kp_lords
from ga_writers.ga_nakshatra_emitters import PLANET_TO_SUBJECT

logger = logging.getLogger(__name__)

HOUSE_SIGNIFICATORS_CATEGORY = "kp_house_significators"
PLANET_SIGNIFICATIONS_CATEGORY = "kp_planet_significations"

#: The nine grahas that signify. Lagna is excluded deliberately: in KP the
#: ascendant is cusp 1 (a house), not a significator.
SIGNIFYING_BODIES: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

NODES: tuple[str, ...] = ("Rahu", "Ketu")

_NODAL_AGENCY_DISCLOSURE = (
    "[HONEST_GAP] KP nodal agency rule NOT applied: Rahu/Ketu classically signify "
    "for (1) planets conjoined with them, (2) planets aspecting them, (3) their "
    "star lord, (4) their sign lord. The aspect limb requires an aspect model this "
    "emitter does not own, so no limb is applied and the node signifies on its own "
    "account only. Consumers must not read these rows as the full KP nodal verdict."
)

_EXTERNAL_REQUIRED = (
    "[EXTERNAL_COMPUTATION_REQUIRED] real Placidus cusps unavailable "
    "(chart_output['bhava_chalit']['placidus'] absent) — KP significators need a "
    "cuspal house frame and none was computed; no whole-sign substitute emitted (B.10)."
)


def _row(chart_id: str, ayanamsha_id: str, build_id: str,
         fact_category: str, fact_subject: str, fact_key: str,
         value_text: str | None = None, value_num: float | None = None,
         source: str = "ga_nakshatra:kp_significators",
         verification_pass_status: str | None = None) -> dict:
    row = {
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "fact_category": fact_category,
        "fact_subject": fact_subject,
        "fact_key": fact_key,
        "fact_value_text": value_text,
        "fact_value_num": value_num,
        "source_calculation": source,
    }
    if verification_pass_status is not None:
        row["verification_pass_status"] = assert_legal(verification_pass_status)
    return row


def _join(names: list[str]) -> str:
    """List → the stored text form. Empty is reported as the literal 'none', never
    as an empty string a reader could mistake for a missing value (§N.7)."""
    return ",".join(names) if names else "none"


def _arc_contains(lon: float, start: float, end: float) -> bool:
    """Half-open [start, end) on the circle, wrap-safe."""
    lon, start, end = lon % 360.0, start % 360.0, end % 360.0
    if start <= end:
        return start <= lon < end
    return lon >= start or lon < end


def _cuspal_house(lon: float, cusps: list[dict[str, Any]]) -> int | None:
    for c in cusps:
        if _arc_contains(lon, float(c["start"]), float(c["end"])):
            return int(c["house"])
    return None


def _sign_of(lon: float) -> int:
    """1-based rāśi of a sidereal longitude."""
    return int((lon % 360.0) // 30.0) + 1


def _dedup(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def emit_kp_significators(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
    divisions: list[dict[str, Any]],
    sign_lords_by_number: dict[int, str],
) -> list[dict]:
    """Emit `kp_house_significators` (12 houses) + `kp_planet_significations` (9 grahas).

    `divisions` is the L0 `bg_kp_sublord_division` row set (the boundary authority).
    `sign_lords_by_number` maps 1..12 → lord name, loaded by the caller from the L0
    `reference_signs` table (never inlined here — L1-bypass discipline).
    """
    rows: list[dict] = []

    placidus = ((chart_output.get("bhava_chalit") or {}).get("placidus") or {})
    cusps = placidus.get("cusps") or []
    if len(cusps) < 12:
        for h in range(1, 13):
            rows.append(_row(chart_id, ayanamsha_id, build_id,
                             HOUSE_SIGNIFICATORS_CATEGORY, f"HOUSE_{h:02d}",
                             "ranked_significators", value_text=_EXTERNAL_REQUIRED,
                             source="ga_nakshatra:kp_significators:external_required",
                             verification_pass_status="external_computation_required"))
        logger.warning(
            "[ga_nakshatra:kp_significators] chart=%s ay=%s: Placidus cusps absent — "
            "12 EXTERNAL_COMPUTATION_REQUIRED markers emitted, no significators derived.",
            chart_id, ayanamsha_id,
        )
        return rows

    grahas = {g.get("name"): g for g in (chart_output.get("grahas") or [])}

    # ── Per-graha frame: star lord (REFERENCED from L0), KP house, whole-sign house ──
    star_lord: dict[str, str] = {}
    kp_house: dict[str, int] = {}
    ws_house: dict[str, int] = {}
    star_verdict: dict[str, str] = {}
    division_ref: dict[str, int] = {}
    sub_lord: dict[str, str] = {}

    for name in SIGNIFYING_BODIES:
        g = grahas.get(name)
        if not g or g.get("longitude_deg") is None:
            continue
        lon = float(g["longitude_deg"]) % 360.0

        div = lookup_division(lon, divisions)
        star_lord[name] = div["star_lord"]
        sub_lord[name] = div["sub_lord"]
        division_ref[name] = int(div["division_index"])

        # SECOND PASS: the live iterative subdivision used by emit_kp_lords in this
        # same build. Independently implemented (float accumulation vs. the L0 table's
        # exact rationals) so it could genuinely disagree.
        live = compute_kp_lords(lon)
        verdict = two_pass_verdict(
            (div["star_lord"], div["sub_lord"]),
            (live["star_lord"], live["sub_lord"]),
        )
        star_verdict[name] = verdict
        if verdict != "two_pass_verified":
            logger.warning(
                "[ga_nakshatra:kp_significators] DIVERGENCE for %s at %.6f°: "
                "bg_kp_sublord_division says %s/%s, compute_kp_lords says %s/%s — "
                "stored as divergent_flagged, NOT reconciled.",
                name, lon, div["star_lord"], div["sub_lord"],
                live["star_lord"], live["sub_lord"],
            )

        h = _cuspal_house(lon, cusps)
        if h is not None:
            kp_house[name] = h
        if g.get("house") is not None:
            ws_house[name] = int(g["house"])

    # ── Per-house ladder ────────────────────────────────────────────────────────
    occupants: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for name, h in kp_house.items():
        occupants[h].append(name)

    owner: dict[int, str] = {}
    cusp_lon: dict[int, float] = {}
    for c in cusps:
        h = int(c["house"])
        start = float(c["start"]) % 360.0
        cusp_lon[h] = start
        owner[h] = sign_lords_by_number.get(_sign_of(start), "UNKNOWN")

    level_houses: dict[str, dict[str, list[int]]] = {
        name: {"a": [], "b": [], "c": [], "d": []} for name in star_lord
    }

    for h in range(1, 13):
        occ = sorted(occupants[h], key=SIGNIFYING_BODIES.index)
        own = owner.get(h, "UNKNOWN")

        level_a = [p for p in SIGNIFYING_BODIES
                   if p in star_lord and star_lord[p] in occ]
        level_b = occ
        level_c = [p for p in SIGNIFYING_BODIES
                   if p in star_lord and star_lord[p] == own]
        level_d = [own] if own != "UNKNOWN" else []

        ranked = _dedup([*level_a, *level_b, *level_c, *level_d])

        for lvl, members in (("a", level_a), ("b", level_b),
                             ("c", level_c), ("d", level_d)):
            for p in members:
                if p in level_houses:
                    level_houses[p][lvl].append(h)

        subj = f"HOUSE_{h:02d}"
        src = (f"ga_nakshatra:kp_significators:house={h}:"
               f"placidus_cusp={cusp_lon.get(h, float('nan')):.4f}")
        rows.extend([
            _row(chart_id, ayanamsha_id, build_id, HOUSE_SIGNIFICATORS_CATEGORY, subj,
                 "house_system", value_text="placidus_kp", source=src),
            _row(chart_id, ayanamsha_id, build_id, HOUSE_SIGNIFICATORS_CATEGORY, subj,
                 "cusp_longitude_sidereal", value_num=round(cusp_lon.get(h, 0.0), 6), source=src),
            _row(chart_id, ayanamsha_id, build_id, HOUSE_SIGNIFICATORS_CATEGORY, subj,
                 "cusp_owner", value_text=own, source=src),
            _row(chart_id, ayanamsha_id, build_id, HOUSE_SIGNIFICATORS_CATEGORY, subj,
                 "level_a_star_of_occupants", value_text=_join(level_a), source=src),
            _row(chart_id, ayanamsha_id, build_id, HOUSE_SIGNIFICATORS_CATEGORY, subj,
                 "level_b_occupants", value_text=_join(level_b), source=src),
            _row(chart_id, ayanamsha_id, build_id, HOUSE_SIGNIFICATORS_CATEGORY, subj,
                 "level_c_star_of_owner", value_text=_join(level_c), source=src),
            _row(chart_id, ayanamsha_id, build_id, HOUSE_SIGNIFICATORS_CATEGORY, subj,
                 "level_d_owner", value_text=_join(level_d), source=src),
            _row(chart_id, ayanamsha_id, build_id, HOUSE_SIGNIFICATORS_CATEGORY, subj,
                 "ranked_significators", value_text=_join(ranked), source=src),
            _row(chart_id, ayanamsha_id, build_id, HOUSE_SIGNIFICATORS_CATEGORY, subj,
                 "significator_count", value_num=float(len(ranked)), source=src),
        ])

    # ── Per-planet direction ────────────────────────────────────────────────────
    for name in SIGNIFYING_BODIES:
        if name not in star_lord:
            continue
        subj = PLANET_TO_SUBJECT.get(name)
        if not subj:
            continue

        src = (f"ga_nakshatra:kp_significators:REF bg_kp_sublord_division:"
               f"division_index={division_ref[name]}")
        lv = level_houses[name]
        all_houses = _dedup([str(h) for h in (*lv["a"], *lv["b"], *lv["c"], *lv["d"])])
        strongest = next((k for k in ("a", "b", "c", "d") if lv[k]), "none")

        kp_h = kp_house.get(name)
        ws_h = ws_house.get(name)
        divergent = (kp_h is not None and ws_h is not None and kp_h != ws_h)

        rows.extend([
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "star_lord", value_text=star_lord[name], source=src,
                 verification_pass_status=star_verdict[name]),
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "sub_lord", value_text=sub_lord[name], source=src,
                 verification_pass_status=star_verdict[name]),
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "kp_cuspal_house",
                 value_num=float(kp_h) if kp_h is not None else None, source=src),
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "whole_sign_house",
                 value_num=float(ws_h) if ws_h is not None else None, source=src),
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "house_system_divergence",
                 value_text=("true" if divergent else "false"), source=src),
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "level_a_houses", value_text=_join([str(h) for h in lv["a"]]), source=src),
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "level_b_houses", value_text=_join([str(h) for h in lv["b"]]), source=src),
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "level_c_houses", value_text=_join([str(h) for h in lv["c"]]), source=src),
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "level_d_houses", value_text=_join([str(h) for h in lv["d"]]), source=src),
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "signified_houses", value_text=_join(all_houses), source=src),
            _row(chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                 "strongest_level", value_text=strongest, source=src),
        ])

        if name in NODES:
            rows.append(_row(
                chart_id, ayanamsha_id, build_id, PLANET_SIGNIFICATIONS_CATEGORY, subj,
                "nodal_agency_not_applied", value_text=_NODAL_AGENCY_DISCLOSURE,
                source="ga_nakshatra:kp_significators:honest_gap",
            ))

    # Rows that carry no explicit `verification_pass_status` inherit the honest
    # UNVERIFIED_DEFAULT ('single') in `ga_nakshatra._enrich_rows` — the ladder itself
    # is a deterministic join, not a second derivation, so it does not claim a pass.
    return rows

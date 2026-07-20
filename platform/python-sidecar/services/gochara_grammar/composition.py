"""
gochara_grammar.composition — the 6 composition operators (BRIEF_D5 §1 G-2
row / §10 promise-ledger). Each operator takes a list of already-generated
`ConfigurationSentence`s (from `primitives.py` / `sarvatobhadra.py`) for ONE
target and combines them into `CompositionSentence`s. None of these operators
touch swisseph directly -- they operate purely on the primitives' already-
computed event_jd / detail payloads, which is why they live in a separate
module from `primitives.py`.

Citation-or-uncited decision per operator (B.10):
  1. simultaneity        -> uncited_extension (a G-2 grammar-level composition
     concept; BPHS discusses combined/multiple influences qualitatively but no
     codebase-attested citation names a "simultaneity operator" as such).
  2. double_transit       -> BPHS Ch.29 + Phaladeepika Ch.26 §double-gochara
     when the pair is Jupiter+Saturn (the one double-transit combination this
     codebase has a live, cited `bg_transit_rules` row for -- migration 397);
     uncited_extension for any other two-graha pairing (still detected, just
     honestly unattributed to the JUPITER+SATURN-specific classical rule).
  2b. double_transit_mixed -> same Phaladeepika Ch.26 §double-gochara citation
     as #2 for Jupiter+Saturn, but on an explicit JUDGMENT CALL (not a
     codebase-attested citation naming the mixed case specifically) that
     "simultaneous transit" covers one leg occupying + one leg aspecting the
     same house, not only both aspecting it -- see this operator's own
     module comment for the full reasoning, stated so a reviewer can
     disagree. RED-D follow-up (2026-07-20): added because #2 above cannot
     represent a planet's own occupation of the target house at all.
  3. kartari              -> uncited_extension (kartari/pincer is classically
     attested as a NATAL yoga-formation concept — BPHS discusses graha kartari
     yoga — but no codebase-attested citation covers the TRANSIT/gochara
     application this operator performs; honestly flagged rather than
     borrowing the natal-yoga citation for a different technique).
  4. cancellation         -> INHERITS the member sentence's own citation
     (gochara_vedha_pair / sarvatobhadra_vedha already carry their own
     citation-or-uncited state; this operator's own sentence mirrors
     whichever the member fired with, since cancellation IS that member's
     vedha rule, not a separate technique).
  5. amplification         -> uncited_extension (stacking-effect framing is
     this grammar's own composition, not a single named classical technique).
  6. dasha_coincidence      -> uncited_extension (dvi-pramana / promise-times-
     delivery is the vision's framing per BRIEF_D5 §0, but that framing itself
     is this wave's engineering decomposition (G-3's λ_e), not a codebase-
     attested classical citation for "gochara-dasha co-occurrence" as a named
     technique -- honestly flagged here at the G-2 grammar layer).
"""
from __future__ import annotations

import logging
from itertools import combinations

from .models import ConfigurationSentence, CompositionSentence
from .dasha_data import period_contains
from . import citations as C

logger = logging.getLogger(__name__)

_JD_WINDOW_DEFAULT = 1.0  # days


def _group_by_target(sentences: list[ConfigurationSentence]) -> dict[str, list[ConfigurationSentence]]:
    grouped: dict[str, list[ConfigurationSentence]] = {}
    for s in sentences:
        grouped.setdefault(s.target_ref or "", []).append(s)
    return grouped


def _cluster_by_window(sentences: list[ConfigurationSentence], window_days: float) -> list[list[ConfigurationSentence]]:
    """Sentences with a resolved event_jd, sorted and clustered so that
    consecutive members are within window_days of the cluster's first
    member."""
    dated = sorted((s for s in sentences if s.event_jd is not None), key=lambda s: s.event_jd)
    clusters: list[list[ConfigurationSentence]] = []
    for s in dated:
        if clusters and (s.event_jd - clusters[-1][0].event_jd) <= window_days:
            clusters[-1].append(s)
        else:
            clusters.append([s])
    return clusters


# ── #1 — simultaneity ───────────────────────────────────────────────────────

def simultaneity(
    sentences: list[ConfigurationSentence],
    window_days: float = _JD_WINDOW_DEFAULT,
    min_primitives: int = 2,
) -> list[CompositionSentence]:
    """≥min_primitives DISTINCT primitive families active on the same target
    within window_days of each other."""
    out: list[CompositionSentence] = []
    for target_ref, group in _group_by_target(sentences).items():
        for cluster in _cluster_by_window(group, window_days):
            distinct_primitives = {s.primitive for s in cluster}
            if len(distinct_primitives) < min_primitives:
                continue
            first = cluster[0]
            out.append(CompositionSentence(
                operator="simultaneity",
                chart_id=first.chart_id,
                event_jd=first.event_jd,
                event_datetime_ist=first.event_datetime_ist,
                temporal_shape="point",
                member_sentences=cluster,
                classical_citation=None,
                uncited_extension=True,
                detail={"target_ref": target_ref, "primitives": sorted(distinct_primitives),
                        "member_count": len(cluster), "window_days": window_days},
            ))
    return out


# ── #2 — double-transit ─────────────────────────────────────────────────────

def double_transit(
    sentences: list[ConfigurationSentence],
    window_days: float = _JD_WINDOW_DEFAULT,
    contact_primitives: tuple[str, ...] = ("drishti_contact", "degree_contact"),
) -> list[CompositionSentence]:
    """Two DIFFERENT grahas' drishti/contact on ONE natal target
    simultaneously -- the wave's named double-transit specimen (marriage,
    2013-12-11, BRIEF_D5 §2)."""
    out: list[CompositionSentence] = []
    for target_ref, group in _group_by_target(sentences).items():
        contact_sentences = [s for s in group if s.primitive in contact_primitives]
        for cluster in _cluster_by_window(contact_sentences, window_days):
            planets_seen: dict[str, ConfigurationSentence] = {}
            for s in cluster:
                if s.transit_planet and s.transit_planet not in planets_seen:
                    planets_seen[s.transit_planet] = s
            if len(planets_seen) < 2:
                continue
            for planet_a, planet_b in combinations(sorted(planets_seen.keys()), 2):
                pair_members = [planets_seen[planet_a], planets_seen[planet_b]]
                is_guru_shani = {planet_a, planet_b} == {"Jupiter", "Saturn"}
                out.append(CompositionSentence(
                    operator="double_transit",
                    chart_id=pair_members[0].chart_id,
                    event_jd=pair_members[0].event_jd,
                    event_datetime_ist=pair_members[0].event_datetime_ist,
                    temporal_shape="point",
                    member_sentences=pair_members,
                    classical_citation=C.DOUBLE_GOCHARA_PHALADEEPIKA_26 if is_guru_shani else None,
                    uncited_extension=not is_guru_shani,
                    detail={"target_ref": target_ref, "planet_a": planet_a, "planet_b": planet_b,
                            "is_guru_shani_double_transit": is_guru_shani, "window_days": window_days},
                ))
    return out


# ── #2b — double-transit, MIXED occupation+aspect legs (RED-D follow-up) ────
#
# Added 2026-07-20 after the native's own worked example for chart
# 482012f1's 2013-12-11 marriage specimen turned out to be structurally
# UNREACHABLE by `double_transit` above even after `drishti_contact`'s
# rasi-drishti fix: the native's example is ONE leg occupation (transiting
# Saturn sitting IN Libra, the 7th house itself, conjunct natal Saturn) and
# ONE leg aspect (transiting Jupiter's 5th special drishti FROM Gemini ONTO
# Libra) -- `double_transit`'s `contact_primitives` tuple only ever accepts
# aspect-shaped sentences (`drishti_contact`/`degree_contact`) on BOTH legs,
# so a planet's own occupation of the target house can never satisfy either
# leg no matter how `drishti_contact` itself is fixed.
#
# Citation note (stated explicitly per BRIEF_D5 §6 disclosure discipline,
# not silently assumed): `DOUBLE_GOCHARA_PHALADEEPIKA_26`
# ("Phaladeepika Ch.26 double-gochara -- Jupiter+Saturn simultaneous
# transit") is reused here for the Jupiter+Saturn mixed case on the
# judgment that "simultaneous transit" in that citation's own wording does
# not restrict itself to "simultaneous ASPECT" -- a graha's occupation of a
# house is itself a classical gochara-phala influence on that house (BPHS
# Ch.29, the same base doctrine `sign_occupation`/`sign_ingress` cite),
# distinct from but complementary to drishti onto it, so "Jupiter and
# Saturn both classically influencing the same house simultaneously, one by
# sitting in it and one by aspecting it" is a reasonable reading of
# "simultaneous transit" rather than a stretch of "simultaneous aspect".
# This is this module's own judgment call, not a codebase-attested citation
# naming the mixed occupation+aspect case specifically -- flagged here
# explicitly (rather than silently reused) so a reviewer can disagree and
# override it without archaeology. Any non-guru-shani pairing still gets
# `uncited_extension=True`, exactly mirroring `double_transit`'s own
# pattern above.

def double_transit_mixed(
    sentences: list[ConfigurationSentence],
    window_days: float = _JD_WINDOW_DEFAULT,
    aspect_primitives: tuple[str, ...] = ("drishti_contact", "degree_contact"),
    occupation_primitives: tuple[str, ...] = ("sign_occupation",),
) -> list[CompositionSentence]:
    """One graha's occupation of a target sign (`occupation_primitives`,
    e.g. `sign_occupation`) paired with a DIFFERENT graha's drishti/contact
    onto the SAME target (`aspect_primitives`) within window_days -- the
    mixed-leg sibling to `double_transit` (which requires BOTH legs
    aspect-shaped). See module comment above for why this exists and the
    citation judgment call it makes."""
    out: list[CompositionSentence] = []
    for target_ref, group in _group_by_target(sentences).items():
        aspect_sentences = [s for s in group if s.primitive in aspect_primitives]
        occupation_sentences = [s for s in group if s.primitive in occupation_primitives]
        if not aspect_sentences or not occupation_sentences:
            continue
        combined = sorted(
            aspect_sentences + occupation_sentences,
            key=lambda s: s.event_jd if s.event_jd is not None else 0.0,
        )
        for cluster in _cluster_by_window(combined, window_days):
            asp_in_cluster = [s for s in cluster if s.primitive in aspect_primitives]
            occ_in_cluster = [s for s in cluster if s.primitive in occupation_primitives]
            if not asp_in_cluster or not occ_in_cluster:
                continue
            for asp in asp_in_cluster:
                for occ in occ_in_cluster:
                    if asp.transit_planet == occ.transit_planet:
                        continue  # a planet cannot supply both legs of its own double-transit
                    is_guru_shani = {asp.transit_planet, occ.transit_planet} == {"Jupiter", "Saturn"}
                    out.append(CompositionSentence(
                        operator="double_transit_mixed",
                        chart_id=asp.chart_id,
                        event_jd=asp.event_jd if asp.event_jd is not None else occ.event_jd,
                        event_datetime_ist=asp.event_datetime_ist or occ.event_datetime_ist,
                        temporal_shape="interval",
                        member_sentences=[asp, occ],
                        classical_citation=C.DOUBLE_GOCHARA_PHALADEEPIKA_26 if is_guru_shani else None,
                        uncited_extension=not is_guru_shani,
                        detail={
                            "target_ref": target_ref,
                            "aspecting_planet": asp.transit_planet,
                            "occupying_planet": occ.transit_planet,
                            "is_guru_shani_double_transit": is_guru_shani,
                            "window_days": window_days,
                            "leg_shapes": {"aspect": asp.primitive, "occupation": occ.primitive},
                        },
                    ))
    return out


# ── #3 — kartari (pincer) ───────────────────────────────────────────────────

def kartari(
    sentences: list[ConfigurationSentence],
    window_days: float = 3.0,
) -> list[CompositionSentence]:
    """Two grahas straddling a target from both sides -- one with a positive
    signed_offset_from_target_deg, one negative -- within window_days.
    Requires sentences carrying `detail['signed_offset_from_target_deg']`
    (degree_contact / drishti_contact primitives populate this)."""
    out: list[CompositionSentence] = []
    for target_ref, group in _group_by_target(sentences).items():
        offset_sentences = [s for s in group if "signed_offset_from_target_deg" in s.detail]
        for cluster in _cluster_by_window(offset_sentences, window_days):
            positives = [s for s in cluster if s.detail["signed_offset_from_target_deg"] > 0]
            negatives = [s for s in cluster if s.detail["signed_offset_from_target_deg"] < 0]
            if not positives or not negatives:
                continue
            # Different grahas on each side (a planet cannot straddle itself).
            for p_side in positives:
                for n_side in negatives:
                    if p_side.transit_planet == n_side.transit_planet:
                        continue
                    out.append(CompositionSentence(
                        operator="kartari",
                        chart_id=p_side.chart_id,
                        event_jd=p_side.event_jd,
                        event_datetime_ist=p_side.event_datetime_ist,
                        temporal_shape="point",
                        member_sentences=[p_side, n_side],
                        classical_citation=None,
                        uncited_extension=True,
                        detail={"target_ref": target_ref, "planet_positive_side": p_side.transit_planet,
                                "planet_negative_side": n_side.transit_planet, "window_days": window_days},
                    ))
    return out


# ── #4 — cancellation ────────────────────────────────────────────────────────

def cancellation(sentences: list[ConfigurationSentence]) -> list[CompositionSentence]:
    """Wires #7 (gochara_vedha_pair) and #8 (sarvatobhadra_vedha)'s own
    cancellation-state detail through to a composition-layer sentence. A
    gochara_vedha_pair sentence with detail['cancelled']=True, or ANY
    sarvatobhadra_vedha sentence (which represents an active vedha-state
    window by construction), becomes one cancellation CompositionSentence."""
    out: list[CompositionSentence] = []
    for s in sentences:
        fires = (
            (s.primitive == "gochara_vedha_pair" and s.detail.get("cancelled") is True)
            or s.primitive == "sarvatobhadra_vedha"
        )
        if not fires:
            continue
        out.append(CompositionSentence(
            operator="cancellation",
            chart_id=s.chart_id,
            event_jd=s.event_jd,
            event_datetime_ist=s.event_datetime_ist,
            temporal_shape=s.temporal_shape,
            member_sentences=[s],
            classical_citation=s.classical_citation,
            uncited_extension=s.uncited_extension,
            detail={"source_primitive": s.primitive, "target_ref": s.target_ref,
                    **{k: v for k, v in s.detail.items() if k in (
                        "cancelled", "cancelling_occupants", "vedha_house", "vedha_sign",
                        "vedha_nakshatra_id", "vedha_nakshatra_name", "cancellation_effect",
                    )}},
        ))
    return out


# ── #5 — amplification ──────────────────────────────────────────────────────

def amplification(
    sentences: list[ConfigurationSentence],
    window_days: float = _JD_WINDOW_DEFAULT,
    min_stack: int = 3,
) -> list[CompositionSentence]:
    """≥min_stack sentences (any primitive mix, INCLUDING repeats of the same
    primitive from different planets) stacking on one target within
    window_days -- a denser signal than `simultaneity` (which only requires
    ≥2 DISTINCT primitive families)."""
    out: list[CompositionSentence] = []
    for target_ref, group in _group_by_target(sentences).items():
        for cluster in _cluster_by_window(group, window_days):
            if len(cluster) < min_stack:
                continue
            first = cluster[0]
            out.append(CompositionSentence(
                operator="amplification",
                chart_id=first.chart_id,
                event_jd=first.event_jd,
                event_datetime_ist=first.event_datetime_ist,
                temporal_shape="point",
                member_sentences=cluster,
                classical_citation=None,
                uncited_extension=True,
                detail={"target_ref": target_ref, "stack_count": len(cluster),
                        "planets_involved": sorted({s.transit_planet for s in cluster if s.transit_planet}),
                        "window_days": window_days},
            ))
    return out


# ── #6 — dasha-coincidence ──────────────────────────────────────────────────

def dasha_coincidence(
    sentences: list[ConfigurationSentence],
    dasha_periods: list[dict],
    require_systems: int = 1,
) -> list[CompositionSentence]:
    """A primitive/composition co-occurring with an active dasha period,
    checked across MULTIPLE independent timing systems (DR-14 plurality --
    NOT Vimśottarī-gated, per BRIEF_D5). `require_systems` is the minimum
    number of DISTINCT dasha systems that must have a period covering the
    sentence's event_datetime_ist for a CompositionSentence to fire
    (require_systems=1 fires on any single-system coincidence but still
    reports every co-occurring system found; require_systems=2 requires
    genuine cross-system agreement)."""
    out: list[CompositionSentence] = []
    for s in sentences:
        if not s.event_datetime_ist:
            continue
        hits = [p for p in dasha_periods if period_contains(p, s.event_datetime_ist)]
        systems_hit = sorted({h["system_id"] for h in hits})
        if len(systems_hit) < require_systems:
            continue
        out.append(CompositionSentence(
            operator="dasha_coincidence",
            chart_id=s.chart_id,
            event_jd=s.event_jd,
            event_datetime_ist=s.event_datetime_ist,
            temporal_shape=s.temporal_shape,
            member_sentences=[s],
            classical_citation=None,
            uncited_extension=True,
            detail={
                "target_ref": s.target_ref,
                "systems_coinciding": systems_hit,
                "system_count": len(systems_hit),
                "dasha_lords_by_system": {h["system_id"]: h["lord_graha"] for h in hits},
            },
        ))
    return out


__all__ = [
    "simultaneity",
    "double_transit",
    "double_transit_mixed",
    "kartari",
    "cancellation",
    "amplification",
    "dasha_coincidence",
]

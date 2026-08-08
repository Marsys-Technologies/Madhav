"""
bo_pratijna_v4_engine.py — PRATIJÑĀ v4 Lane B2: the scoring engine LIBRARY.

Implements `V4_RUBRIC_SPEC_v1_0.md` §2-§6 exactly, for all 27 event classes
in `bo_pratijna_karyatva.KARYATVA_REGISTRY`. This module is a standalone,
importable, READ-ONLY scoring library — it never writes to the database, and
it is NOT the writer (that is a separate, later lane; this module is
deliberately never imported by `bo_pratijna.py`, the existing v3 writer,
which this lane does not touch).

Every fact this engine consumes comes through `brahmagyan.chart_reader_v4.
ChartReaderV4` (Lane B1) plus one small, disclosed extension this lane adds
to that Reader (`reference_planets` — see chart_reader_v4.py's own
docstring on that method for the justification). This engine never issues
raw SQL against `chart_facts`/`chart_divisionals` itself.

── R13 discipline ───────────────────────────────────────────────────────────
Every band, weight, denial rule, and threshold below is copied verbatim from
`V4_RUBRIC_SPEC_v1_0.md` (ratified 2026-08-08, written and checkpointed
BEFORE this engine was coded) and `CHECKPOINT_RECORD_v1_0.md`'s binding
application conventions. Nothing here was tuned, adjusted, or reverse-
engineered from chart `482012f1`'s known life outcomes. Where this module
had to make an implementation judgment the spec did not fully pin down
(always because `RUNG_P3_HAND_WORKED_v1_0.md`, the acceptance oracle, forced
a specific reading to reproduce its numbers), that judgment is flagged
in-line with a `# JUDGMENT CALL` comment and repeated in this campaign's PR
description — never silently baked in.

── Reused, not reinvented ───────────────────────────────────────────────────
The naisargika friend/enemy table, the tatkalika (temporal) relation rule,
and the panchadha-maitri (5-fold compound) matrix are NOT re-derived here —
they are the same functions already live in `ga_writers/ga_condition_writer.
py` (`compute_tatkalika_relation`, `compute_panchadha_maitri`), imported
directly, plus a literal copy of that module's `_NAISARGIKA` dict (a nested
function-local constant, not itself importable — copied with a drift-guard
test the same way `chart_reader_v4.py` copies `SIGN_LORD` from
`probe_p2_tracer.py`).

── The one documented honest gap: the yoga-presence slot (§2.5) ───────────
`RUNG_P3_HAND_WORKED_v1_0.md` §1.3/§5 found, by hand, that NONE of the nine
`yoga_keywords` across marriage/separation/childbirth resolved to a
`ganita_yogas_get` catalog match or a `ganita_yoga_firings_get` firings
match on chart `482012f1` — even though several have real, on-topic,
non-empty evidence in OTHER fact systems (Jaimini karakas, upapada lagna,
dosha labels) that the strict §2.5 band cannot see. The Chart Reader (Lane
B1) does not expose a yoga catalog/firings query (out of its 6-function
scope; those surfaces are MCP tools, not `chart_facts`/`chart_divisionals`/
`reference_planets` rows), and building a keyword-matching yoga resolver
here would re-introduce exactly the fuzzy-matching defect class this whole
campaign exists to retire (see `bo_pratijna.py`'s v3
`_match_signal_to_class`, NOT reused). This engine therefore scores the
yoga slot **0.00 for every class, always** — the same reading RUNG_P3 itself
used for all three of its hand-worked classes (not a shortcut invented
here) — and documents it loudly rather than silently. This is a REAL,
disclosed structural gap, not an improvisation: per RUNG_P3 §1.3's own
recommendation, closing it (broadening the yoga-tier band to accept
special-point/karaka evidence) is future work for a later campaign,
explicitly not this lane's authorization.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as F
from typing import Any

from brahmagyan.chart_reader_v4 import ChartReaderError, ChartReaderV4, SIGN_LORD
from ga_writers.ga_condition_writer import (
    compute_panchadha_maitri,
    compute_tatkalika_relation,
)

from .bo_pratijna_karyatva import KaryatvaMap, KARYATVA_REGISTRY, get_karyatva

ENGINE_VERSION = "bo_pratijna_v4_engine.0.1"
RUBRIC_VERSION = "V4_RUBRIC_SPEC_v1_0"

# ── §2.1 — the shared dignity band (verbatim from V4_RUBRIC_SPEC_v1_0.md §2.1,
#    itself adopted from ga_condition_writer.py's DIGNITY_SCORES / pañcadhā
#    maitri compound states) ──────────────────────────────────────────────
DIGNITY_BAND: dict[str, float] = {
    "exalted": 1.00,
    "moolatrikona": 0.90,
    "own": 0.80,
    "great_friend": 0.70,
    "friend": 0.60,
    "neutral": 0.50,
    "enemy": 0.30,
    "great_enemy": 0.20,
    "debilitated": 0.00,
}

CLASSICAL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
NODE_GRAHAS = ["Rahu", "Ketu"]
ALL_GRAHAS = CLASSICAL_GRAHAS + NODE_GRAHAS

# Literal copy of ga_condition_writer.py's function-local `_NAISARGIKA` dict
# (BPHS ch.3 naisargika friend/enemy table) — that constant is nested inside
# `dignity_d1_from_sign()`, not itself importable. Kept as a literal, not an
# import, with a drift-guard test
# (test_bo_pratijna_v4_engine.py::test_naisargika_matches_ga_condition_writer)
# the same way chart_reader_v4.py's SIGN_LORD is kept honest against
# probe_p2_tracer.py.
NAISARGIKA: dict[str, dict[str, str]] = {
    "Sun":     {"Moon": "friend", "Mars": "friend", "Jupiter": "friend",
                "Mercury": "neutral", "Venus": "enemy", "Saturn": "enemy",
                "Rahu": "enemy", "Ketu": "neutral"},
    "Moon":    {"Sun": "friend", "Mercury": "friend", "Mars": "neutral",
                "Jupiter": "neutral", "Venus": "neutral", "Saturn": "neutral",
                "Rahu": "enemy", "Ketu": "neutral"},
    "Mars":    {"Sun": "friend", "Moon": "friend", "Jupiter": "friend",
                "Venus": "neutral", "Saturn": "neutral", "Mercury": "enemy",
                "Rahu": "neutral", "Ketu": "friend"},
    "Mercury": {"Sun": "friend", "Venus": "friend", "Mars": "neutral",
                "Jupiter": "neutral", "Saturn": "neutral", "Moon": "enemy",
                "Rahu": "friend", "Ketu": "neutral"},
    "Jupiter": {"Sun": "friend", "Moon": "friend", "Mars": "friend",
                "Saturn": "neutral", "Mercury": "enemy", "Venus": "enemy",
                "Rahu": "neutral", "Ketu": "neutral"},
    "Venus":   {"Mercury": "friend", "Saturn": "friend", "Mars": "neutral",
                "Jupiter": "neutral", "Sun": "enemy", "Moon": "enemy",
                "Rahu": "friend", "Ketu": "friend"},
    "Saturn":  {"Mercury": "friend", "Venus": "friend", "Jupiter": "neutral",
                "Sun": "enemy", "Moon": "enemy", "Mars": "enemy",
                "Rahu": "friend", "Ketu": "friend"},
    "Rahu":    {"Venus": "friend", "Saturn": "friend", "Mercury": "friend",
                "Sun": "enemy", "Moon": "enemy", "Mars": "neutral",
                "Jupiter": "neutral", "Ketu": "enemy"},
    "Ketu":    {"Mars": "friend", "Venus": "friend", "Saturn": "friend",
                "Sun": "neutral", "Moon": "neutral", "Mercury": "neutral",
                "Jupiter": "neutral", "Rahu": "enemy"},
}

# ── §3.1 — the universal base-weight table (Fraction, exact) ───────────────
BASE_WEIGHTS: dict[str, F] = {
    "bhava_lord": F(35, 100),
    "dusthana": F(30, 100),
    "karaka": F(20, 100),
    "divisional": F(10, 100),
    "yoga": F(5, 100),
}

# ── §2.5 — yoga-presence 3-tier band (see module docstring: engine always
#    returns the 0.00 "no match" tier — the documented honest gap) ─────────
YOGA_BAND_NO_MATCH = 0.00
YOGA_BAND_CATALOG_ONLY = 0.50
YOGA_BAND_CONFIRMED = 1.00

# ── §6 — threshold bands (equal-width, stated a priori) ─────────────────────
OCCURRENCE_BANDS: list[tuple[float, float, str]] = [
    (0.00, 0.20, "DENIED"),
    (0.20, 0.40, "WEAK"),
    (0.40, 0.60, "MODERATE"),
    (0.60, 0.80, "STRONG"),
    (0.80, 1.0001, "VERY_STRONG"),
]
CONDITION_BANDS: list[tuple[float, float, str]] = [
    (0, 2, "CLEAN"),
    (2, 4, "MILD"),
    (4, 6, "MODERATE"),
    (6, 8, "SEVERE"),
    (8, 10.0001, "CRITICAL"),
]


def occurrence_band(occurrence: float) -> str:
    for lo, hi, label in OCCURRENCE_BANDS:
        if lo <= occurrence < hi:
            return label
    return "VERY_STRONG"  # occurrence == 1.0 exactly


def condition_band(condition: float) -> str:
    for lo, hi, label in CONDITION_BANDS:
        if lo <= condition < hi:
            return label
    return "CRITICAL"  # condition == 10.0 exactly


# ── §2.7 — classical graha-dṛṣṭi fractional aspect table ───────────────────

_SPECIAL_FULL_ASPECTS: dict[str, set[int]] = {
    "Mars": {4, 8},
    "Jupiter": {5, 9},
    "Saturn": {3, 10},
}


def house_distance(source_house: int, target_house: int) -> int:
    """Classical 'Nth house counted from source' distance (1 = same house/
    conjunction, 7 = opposition, ...), 1-indexed, wrapping at 12."""
    return ((target_house - source_house) % 12) + 1


def aspect_fraction(source_graha: str, source_house: int, target_house: int) -> float:
    """§2.7's fractional graha-dṛṣṭi table. 1.00 = conjunction, the universal
    7th aspect, or one of Mars/Jupiter/Saturn's named full-strength special
    aspects; 0.75/0.50/0.25 = the general (non-special-planet) 4th-8th/
    5th-9th/3rd-10th partial aspects; 0.00 = no contact."""
    d = house_distance(source_house, target_house)
    if d == 1 or d == 7:
        return 1.00
    if d in _SPECIAL_FULL_ASPECTS.get(source_graha, set()):
        return 1.00
    if d in (4, 8):
        return 0.75
    if d in (5, 9):
        return 0.50
    if d in (3, 10):
        return 0.25
    return 0.00


def full_contact(source_graha: str, source_house: int, target_house: int) -> bool:
    """JUDGMENT CALL (flagged per module docstring, forced by RUNG_P3
    reproduction): the BINARY §2.6 dusthana structural-connection test reads
    'aspects (classical dṛṣṭi, §2.7)' as full-strength contact ONLY
    (conjunction / universal 7th / a special-planet's named full aspect) —
    NOT the weaker general 4th-8th/5th-9th/3rd-10th partial-strength tier,
    which RUNG_P3_HAND_WORKED_v1_0.md §2.1's own worked dusthana table
    (house 6, Mercury's general 3rd/10th-tier reach into house 7 at
    distance 10) explicitly does NOT count as a structural connection.
    §2.7's full fractional table (including the weaker tiers) is used
    UNCHANGED for its own stated purpose, the condition-axis magnitude
    (§5.2) — this stricter binary reading applies ONLY to §2.6."""
    return aspect_fraction(source_graha, source_house, target_house) >= 1.00


# ── Dignity (§2.1, compound pañcadhā maitri per CHECKPOINT_RECORD_v1_0.md
#    Decision 1: "pañcadhā (compound naisargika+tātkālika) maitri for the
#    dignity band; tātkālika computed from D1 positions even for varga
#    dignity; nodes carry general aspects in §2.7; nodes' dignity band =
#    exalt/debil/neutral only.") ─────────────────────────────────────────


@dataclass(frozen=True)
class DignityResult:
    graha: str
    sign_number: int
    state: str
    band: float
    detail: str


def dignity_of(
    graha: str,
    sign_number: int,
    graha_house_d1: int | None,
    ref: dict[str, dict[str, Any]],
) -> DignityResult:
    """§2.1's nine-state dignity band for `graha` occupying `sign_number`
    (any varga — the sign test is always against the varga sign; the
    naisargika/tatkalika RELATION is always computed from D1 house per the
    checkpoint's binding convention, hence the caller passes
    `graha_house_d1`, not the varga house)."""
    r = ref.get(graha)
    if r is None:
        raise KeyError(f"No reference_planets row for graha={graha!r}")

    if sign_number == r["exaltation_sign"]:
        return DignityResult(graha, sign_number, "exalted", DIGNITY_BAND["exalted"],
                              f"sign={sign_number} matches exaltation_sign")
    if sign_number == r["debilitation_sign"]:
        return DignityResult(graha, sign_number, "debilitated", DIGNITY_BAND["debilitated"],
                              f"sign={sign_number} matches debilitation_sign")

    if graha in NODE_GRAHAS:
        # §2.1: nodes carry only exalted/debilitated/neutral-default.
        return DignityResult(graha, sign_number, "neutral", DIGNITY_BAND["neutral"],
                              "node — no exalt/debil match, neutral default (§2.1)")

    if r["mooltrikona_sign"] is not None and sign_number == r["mooltrikona_sign"]:
        return DignityResult(graha, sign_number, "moolatrikona", DIGNITY_BAND["moolatrikona"],
                              f"sign={sign_number} matches mooltrikona_sign")
    if sign_number in r["own_signs"]:
        return DignityResult(graha, sign_number, "own", DIGNITY_BAND["own"],
                              f"sign={sign_number} in own_signs={r['own_signs']}")

    sign_lord = SIGN_LORD[sign_number]
    if sign_lord == graha:
        # Graha rules its own sign's lord (self) — should be unreachable
        # given the own_signs check above already catches this case; kept
        # as an honest safety net per §2.1's literal text, not a new rule.
        return DignityResult(graha, sign_number, "neutral", DIGNITY_BAND["neutral"],
                              "sign_lord == graha (self) — neutral default")

    naisargika_rel = NAISARGIKA.get(graha, {}).get(sign_lord, "neutral")

    sign_lord_house_d1 = None  # filled by caller-provided lookup below
    # Caller passes graha_house_d1 for the SCORED graha; the sign LORD's own
    # D1 house is resolved by the caller via the shared D1 position map and
    # passed through `dignity_of_with_positions` below — this inner function
    # stays a pure, directly-testable unit (no DB/position-map dependency),
    # per TDD discipline.
    raise _NeedsSignLordHouse(graha, sign_number, sign_lord, naisargika_rel)


class _NeedsSignLordHouse(Exception):
    """Internal control-flow signal — `dignity_of` cannot finish a
    friend/enemy-tier read without the sign lord's own D1 house, which only
    the caller (holding the chart's D1 position map) has. Caught by
    `dignity_of_with_positions`, never escapes this module."""

    def __init__(self, graha: str, sign_number: int, sign_lord: str, naisargika_rel: str):
        self.graha = graha
        self.sign_number = sign_number
        self.sign_lord = sign_lord
        self.naisargika_rel = naisargika_rel


def dignity_of_with_positions(
    graha: str,
    sign_number: int,
    graha_house_d1: int | None,
    d1_houses: dict[str, int],
    ref: dict[str, dict[str, Any]],
) -> DignityResult:
    """Full §2.1 dignity resolution, including the pañcadhā-maitri compound
    tier, using `d1_houses` (graha -> D1 whole-sign house, for every
    classical graha) to resolve the sign lord's own D1 house for the
    tatkalika computation."""
    try:
        return dignity_of(graha, sign_number, graha_house_d1, ref)
    except _NeedsSignLordHouse as need:
        sign_lord_house_d1 = d1_houses.get(need.sign_lord)
        if graha_house_d1 is None or sign_lord_house_d1 is None:
            # Honest fallback: naisargika-only reading when D1 house data
            # for either graha is unavailable (should not occur for the 9
            # classical grahas on a fully-built chart; defensive only).
            state = {"friend": "friend", "enemy": "enemy"}.get(need.naisargika_rel, "neutral")
            return DignityResult(
                graha, sign_number, state, DIGNITY_BAND[state],
                f"naisargika-only (tatkalika unavailable): {graha}->{need.sign_lord}="
                f"{need.naisargika_rel}",
            )
        tatkalika_rel = compute_tatkalika_relation(sign_lord_house_d1, graha_house_d1)
        compound = compute_panchadha_maitri(need.naisargika_rel, tatkalika_rel)
        return DignityResult(
            graha, sign_number, compound, DIGNITY_BAND[compound],
            f"naisargika({graha}->{need.sign_lord})={need.naisargika_rel}, "
            f"tatkalika(lord_house={sign_lord_house_d1},graha_house={graha_house_d1})="
            f"{tatkalika_rel} -> panchadha={compound}",
        )


# ── §3 — per-class slot weights (mechanical, Fraction-exact) ───────────────


@dataclass(frozen=True)
class SlotWeight:
    slot: str            # "house_lord" | "karaka" | "divisional" | "yoga" | "dusthana"
    item: str | None      # house number (str) / graha name / None
    weight: F


def compute_class_weights(karyatva: KaryatvaMap) -> list[SlotWeight]:
    """§3.1's ONE mechanical rule, applied identically to all 27 classes:
    populate whichever slots this class's own KaryatvaMap carries, split
    multi-item slots evenly, renormalize the populated subset to sum to
    exactly 1 (Fraction, no float drift)."""
    if karyatva.dusthana_required:
        core_houses = [karyatva.primary_bhava[0]]
        dusthana_houses = karyatva.primary_bhava[1:]
    else:
        core_houses = list(karyatva.primary_bhava)
        dusthana_houses = []

    active: dict[str, F] = {
        "bhava_lord": BASE_WEIGHTS["bhava_lord"],
        "karaka": BASE_WEIGHTS["karaka"],
    }
    if karyatva.divisional:
        active["divisional"] = BASE_WEIGHTS["divisional"]
    if karyatva.yoga_keywords:
        active["yoga"] = BASE_WEIGHTS["yoga"]
    if karyatva.dusthana_required:
        active["dusthana"] = BASE_WEIGHTS["dusthana"]

    total = sum(active.values())
    norm = {k: v / total for k, v in active.items()}

    out: list[SlotWeight] = []
    for h in core_houses:
        out.append(SlotWeight("house_lord", str(h), norm["bhava_lord"] / len(core_houses)))
    for k in karyatva.karaka_grahas:
        out.append(SlotWeight("karaka", k, norm["karaka"] / len(karyatva.karaka_grahas)))
    if "divisional" in norm:
        out.append(SlotWeight("divisional", karyatva.divisional, norm["divisional"]))
    if "yoga" in norm:
        out.append(SlotWeight("yoga", None, norm["yoga"]))
    if "dusthana" in norm:
        for d in dusthana_houses:
            out.append(SlotWeight("dusthana", str(d), norm["dusthana"] / len(dusthana_houses)))
    return out


def verify_all_class_weights_sum_to_one() -> dict[str, F]:
    """§3.3's regression check, re-run against the LIVE `KARYATVA_REGISTRY`
    (not a hand-copied CLASSES dict) — 27/27 classes must sum to exactly
    Fraction(1). Returns {event_class_id: exact_sum} for callers that want
    the raw sums (the test suite asserts every value == Fraction(1))."""
    out: dict[str, F] = {}
    for event_class_id, karyatva in KARYATVA_REGISTRY.items():
        weights = compute_class_weights(karyatva)
        out[event_class_id] = sum(w.weight for w in weights)
    return out


# ── §4 — denial configurations ──────────────────────────────────────────────


@dataclass(frozen=True)
class DenialResult:
    config_id: str
    fired: bool
    deduction: F
    reason: str


def _is_kendra(house: int) -> bool:
    return house in (1, 4, 7, 10)


def _neecha_bhanga(
    graha: str,
    graha_sign_number: int,
    lagna_house_d1: int,
    moon_house_d1: int,
    d1_houses: dict[str, int],
) -> tuple[bool, str]:
    """Standard neecha-bhaṅga (debilitation-cancellation) test (§4
    DENIAL-CFG-1's citation): the debilitated graha's dispositor (lord of
    the sign it occupies) is itself angular (kendra: houses 1/4/7/10) from
    the lagna OR from the Moon."""
    dispositor = SIGN_LORD[graha_sign_number]
    dispositor_house_d1 = d1_houses.get(dispositor)
    if dispositor_house_d1 is None:
        return False, f"dispositor {dispositor}'s D1 house unavailable — cannot test cancellation"
    from_lagna = house_distance(lagna_house_d1, dispositor_house_d1)
    from_moon = house_distance(moon_house_d1, dispositor_house_d1)
    if _is_kendra(from_lagna):
        return True, f"dispositor {dispositor} is kendra ({from_lagna}th) from lagna"
    if _is_kendra(from_moon):
        return True, f"dispositor {dispositor} is kendra ({from_moon}th) from Moon"
    return False, f"dispositor {dispositor} not kendra from lagna ({from_lagna}th) or Moon ({from_moon}th)"


def check_denial_cfg1(
    karyatva: KaryatvaMap,
    weights: list[SlotWeight],
    dignities: dict[tuple[str, str], DignityResult],
    lagna_house_d1: int,
    moon_house_d1: int,
    d1_houses: dict[str, int],
) -> DenialResult:
    """DENIAL-CFG-1 — compound uncancelled double debilitation (all 27
    classes). `dignities` keys are (slot, item) matching `weights` entries,
    e.g. ("house_lord", "7") / ("karaka", "Venus")."""
    primary_house = str(karyatva.primary_bhava[0])
    primary_karaka = karyatva.karaka_grahas[0]

    house_lord_dig = dignities.get(("house_lord", primary_house))
    karaka_dig = dignities.get(("karaka", primary_karaka))
    if house_lord_dig is None or karaka_dig is None:
        return DenialResult("CFG-1", False, F(0), "primary house-lord/karaka dignity unavailable")

    both_debilitated = house_lord_dig.state == "debilitated" and karaka_dig.state == "debilitated"
    if not both_debilitated:
        return DenialResult(
            "CFG-1", False, F(0),
            f"house_lord={house_lord_dig.state}, karaka={karaka_dig.state} — not both debilitated",
        )

    # Test cancellation for each debilitated graha (house-lord graha and
    # karaka graha may be the same planet — tested once each regardless).
    cancelled_any = False
    reasons = []
    for dig in {house_lord_dig.graha: house_lord_dig, karaka_dig.graha: karaka_dig}.values():
        ok, why = _neecha_bhanga(dig.graha, dig.sign_number, lagna_house_d1, moon_house_d1, d1_houses)
        reasons.append(f"{dig.graha}: {why}")
        if ok:
            cancelled_any = True

    if cancelled_any:
        return DenialResult("CFG-1", False, F(0), "neecha-bhanga cancellation present: " + "; ".join(reasons))

    house_lord_w = next(w.weight for w in weights if w.slot == "house_lord" and w.item == primary_house)
    karaka_w = next(w.weight for w in weights if w.slot == "karaka" and w.item == primary_karaka)
    deduction = house_lord_w + karaka_w
    return DenialResult(
        "CFG-1", True, deduction,
        f"both primary house-lord ({house_lord_dig.graha}) and primary karaka "
        f"({karaka_dig.graha}) debilitated, uncancelled: " + "; ".join(reasons),
    )


def check_denial_cfg2(
    karyatva: KaryatvaMap,
    weights: list[SlotWeight],
    core_lord_graha: str,
    core_lord_house_d1: int,
    core_lord_sign_number: int,
    lagna_house_d1: int,
    moon_house_d1: int,
    d1_houses: dict[str, int],
    ref: dict[str, dict[str, Any]],
) -> DenialResult:
    """DENIAL-CFG-2 — lord in dusthana, uncancelled (dusthana-required
    classes only). Combustion is NOT tested (honest gap — see module PR
    description: the read-only Chart Reader exposes sign-level, not
    degree-level, position data, so this engine cannot compute combustion
    arcs; treating combust=False only ever makes this configuration LESS
    likely to fire, never fabricates an affliction)."""
    if not karyatva.dusthana_required:
        return DenialResult("CFG-2", False, F(0), "class is not dusthana_required — N/A")

    dusthana_houses = karyatva.primary_bhava[1:]
    if core_lord_house_d1 not in dusthana_houses:
        return DenialResult(
            "CFG-2", False, F(0),
            f"core lord ({core_lord_graha}) D1 house={core_lord_house_d1} not in "
            f"cited dusthana houses {dusthana_houses} — placement test fails",
        )

    debilitated = core_lord_sign_number == ref[core_lord_graha]["debilitation_sign"]
    # combust: honest gap, always False (see docstring).
    combust = False
    if not (debilitated or combust):
        return DenialResult(
            "CFG-2", False, F(0),
            f"core lord placed in dusthana house {core_lord_house_d1} but not debilitated "
            f"there (combustion not computable — honest gap, treated as False)",
        )

    ok, why = _neecha_bhanga(core_lord_graha, core_lord_sign_number, lagna_house_d1, moon_house_d1, d1_houses)
    if ok:
        return DenialResult("CFG-2", False, F(0), "neecha-bhanga cancellation present: " + why)

    benefics = [g for g in CLASSICAL_GRAHAS if ref.get(g, {}).get("natural_benefic")]
    for b in benefics:
        b_house = d1_houses.get(b)
        if b_house is not None and aspect_fraction(b, b_house, core_lord_house_d1) > 0:
            return DenialResult(
                "CFG-2", False, F(0), f"benefic {b} reaches core lord's house — cancelled",
            )

    house_lord_w = next(w.weight for w in weights if w.slot == "house_lord")
    dusthana_w = sum(w.weight for w in weights if w.slot == "dusthana")
    deduction = house_lord_w + dusthana_w
    return DenialResult(
        "CFG-2", True, deduction,
        f"core lord ({core_lord_graha}) debilitated in its own cited dusthana house "
        f"{core_lord_house_d1}, uncancelled, no benefic reach",
    )


def check_denial_cfg3(
    karyatva: KaryatvaMap,
    weights: list[SlotWeight],
    core_house: int,
    core_lord_house_d1: int,
    occupants_by_house: dict[int, list[str]],
    ref: dict[str, dict[str, Any]],
) -> DenialResult:
    """DENIAL-CFG-3 — pāpakartarī yoga on the core house (all 27 classes)."""
    house_before = ((core_house - 2) % 12) + 1  # "12th from" core (one before, wrapping)
    house_after = (core_house % 12) + 1          # "2nd from" core (one after, wrapping)

    malefics = {g for g in ALL_GRAHAS if not ref.get(g, {}).get("natural_benefic", True)}

    before_malefic = any(g in malefics for g in occupants_by_house.get(house_before, []))
    after_malefic = any(g in malefics for g in occupants_by_house.get(house_after, []))
    if not (before_malefic and after_malefic):
        return DenialResult(
            "CFG-3", False, F(0),
            f"house {house_before} malefic-occupied={before_malefic}, "
            f"house {house_after} malefic-occupied={after_malefic} — hemming test fails",
        )

    benefics = [g for g in CLASSICAL_GRAHAS if ref.get(g, {}).get("natural_benefic")]
    for b in benefics:
        for h in occupants_by_house:
            if b in occupants_by_house.get(h, []):
                if aspect_fraction(b, h, core_house) > 0 or aspect_fraction(b, h, core_lord_house_d1) > 0:
                    return DenialResult(
                        "CFG-3", False, F(0),
                        f"benefic {b}@house{h} reaches core house or its lord — cancelled",
                    )

    house_lord_w = next(w.weight for w in weights if w.slot == "house_lord" and w.item == str(core_house))
    return DenialResult(
        "CFG-3", True, house_lord_w,
        f"houses {house_before} and {house_after} (adjoining core house {core_house}) both "
        f"malefic-occupied, no benefic reach — pāpakartarī",
    )


# ── §5 — the two formulas ───────────────────────────────────────────────────


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def clamp_condition(x: float) -> float:
    return max(0.0, min(10.0, x))


# ── §2.6 — dusthana-involvement band ────────────────────────────────────────


@dataclass(frozen=True)
class DusthanaConnection:
    house: int
    connected: bool
    reason: str


def dusthana_connection(
    dusthana_house: int,
    core_house: int,
    core_lord_graha: str,
    core_lord_house_d1: int,
    core_lord_sign_number: int,
    d_lord_graha: str,
    d_lord_house_d1: int | None,
    d_lord_sign_number: int | None,
) -> DusthanaConnection:
    """§2.6's structural-connection test, one dusthana house at a time.
    JUDGMENT CALL (see `full_contact`'s own docstring): the aspect leg of
    this test uses FULL-strength contact only, not §2.7's weaker general
    partial-aspect tiers — forced by RUNG_P3's own worked example."""
    # (a) core house's lord is placed IN this dusthana house.
    if core_lord_house_d1 == dusthana_house:
        return DusthanaConnection(dusthana_house, True, f"{core_lord_graha} (core lord) placed in house {dusthana_house}")

    # (b) this dusthana house's lord aspects/conjoins the core house or its lord.
    if d_lord_house_d1 is not None:
        if full_contact(d_lord_graha, d_lord_house_d1, core_house):
            return DusthanaConnection(dusthana_house, True, f"{d_lord_graha} (lord of {dusthana_house}) full-contacts core house {core_house}")
        if full_contact(d_lord_graha, d_lord_house_d1, core_lord_house_d1):
            return DusthanaConnection(dusthana_house, True, f"{d_lord_graha} (lord of {dusthana_house}) full-contacts core lord's house {core_lord_house_d1}")

    # (c) parivartana (sign exchange) between core house's lord and this
    #     dusthana house's lord.
    if d_lord_sign_number is not None:
        if SIGN_LORD.get(core_lord_sign_number) == d_lord_graha and SIGN_LORD.get(d_lord_sign_number) == core_lord_graha:
            return DusthanaConnection(dusthana_house, True, f"parivartana between {core_lord_graha} and {d_lord_graha}")

    return DusthanaConnection(dusthana_house, False, f"no lord-in-house/full-contact/parivartana connection to house {dusthana_house}")


# ── §5.2 — condition axis ───────────────────────────────────────────────────


def condition_score(
    malefics: list[str],
    core_house: int,
    core_lord_house_d1: int,
    d1_houses: dict[str, int],
) -> tuple[float, list[dict[str, Any]]]:
    """§5.2's condition formula. Returns (condition[0,10], per-malefic ledger)."""
    if not malefics:
        return 0.0, []
    contributions = []
    ledger = []
    for m in malefics:
        m_house = d1_houses.get(m)
        if m_house is None:
            contributions.append(0.0)
            ledger.append({"malefic": m, "house": None, "contribution": 0.0, "reason": "no D1 house data"})
            continue
        to_core = aspect_fraction(m, m_house, core_house)
        to_lord = aspect_fraction(m, m_house, core_lord_house_d1)
        contrib = max(to_core, to_lord)
        contributions.append(contrib)
        ledger.append({
            "malefic": m, "house": m_house, "to_core_house": to_core,
            "to_core_lord_house": to_lord, "contribution": contrib,
        })
    condition = clamp_condition(10.0 * sum(contributions) / len(contributions))
    return round(condition, 2), ledger


# ── Top-level per-class result ──────────────────────────────────────────────


@dataclass
class ClassScore:
    event_class_id: str
    status: str  # "scored" | "no_evidence"
    occurrence: float | None = None
    occurrence_label: str | None = None
    condition: float | None = None
    condition_label: str | None = None
    occurrence_pre_denial: float | None = None
    factor_ledger: list[dict[str, Any]] = field(default_factory=list)
    denials: list[dict[str, Any]] = field(default_factory=list)
    condition_ledger: list[dict[str, Any]] = field(default_factory=list)
    weights: list[dict[str, Any]] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)
    engine_version: str = ENGINE_VERSION
    rubric_version: str = RUBRIC_VERSION


class PratijnaV4Engine:
    """The PRATIJÑĀ v4 scoring engine. READ-ONLY (R19): never writes to the
    database. One instance wraps one `ChartReaderV4` and caches the
    chart-wide D1 position map + the global reference_planets table (the
    latter is genuinely global, cached across charts within one process)."""

    def __init__(self, reader: ChartReaderV4):
        self.reader = reader
        self._ref_cache: dict[str, dict[str, Any]] | None = None
        self._d1_cache: dict[str, dict[str, Any]] = {}

    # -- caches --------------------------------------------------------

    def _reference(self) -> dict[str, dict[str, Any]]:
        if self._ref_cache is None:
            self._ref_cache = {row["graha"]: row for row in self.reader.reference_planets()}
        return self._ref_cache

    def _d1(self, chart_id: str) -> dict[str, Any]:
        cached = self._d1_cache.get(chart_id)
        if cached is not None:
            return cached
        houses: dict[str, int] = {}
        sign_numbers: dict[str, int] = {}
        occupants_by_house: dict[int, list[str]] = {}
        provenance: list[dict[str, Any]] = []
        for h in range(1, 13):
            occ = self.reader.occupants(chart_id, h, "D1")
            occupants_by_house[h] = [o["graha"] for o in occ if o["graha"] != "Lagna"]
            for o in occ:
                provenance.extend(o["provenance"])
                if o["graha"] == "Lagna":
                    houses["Lagna"] = h
                    continue
                houses[o["graha"]] = h
                sign_numbers[o["graha"]] = o["sign_number"]
        out = {
            "houses": houses,
            "sign_numbers": sign_numbers,
            "occupants_by_house": occupants_by_house,
            "provenance": provenance,
        }
        self._d1_cache[chart_id] = out
        return out

    # -- per-class scoring -----------------------------------------------

    def score_class(self, chart_id: str, event_class_id: str) -> ClassScore:
        karyatva = get_karyatva(event_class_id)
        if karyatva is None:
            return ClassScore(event_class_id=event_class_id, status="no_evidence")

        ref = self._reference()
        d1 = self._d1(chart_id)
        d1_houses = d1["houses"]
        d1_signs = d1["sign_numbers"]
        occupants_by_house = d1["occupants_by_house"]
        provenance: list[dict[str, Any]] = list(d1["provenance"])

        weights = compute_class_weights(karyatva)
        dignities: dict[tuple[str, str], DignityResult] = {}
        factor_ledger: list[dict[str, Any]] = []
        total = 0.0

        core_house = karyatva.primary_bhava[0]
        # House-lord slot(s)
        house_lord_names: dict[int, str] = {}
        for w in weights:
            if w.slot != "house_lord":
                continue
            house = int(w.item)
            lord_info = self.reader.lord_of(chart_id, house, "D1")
            provenance.extend(lord_info["provenance"])
            lord = lord_info["lord"]
            house_lord_names[house] = lord
            lord_sign = d1_signs.get(lord)
            lord_house_d1 = d1_houses.get(lord)
            if lord_sign is None:
                # Lord's own D1 sign unknown (defensive; should not occur).
                dig = DignityResult(lord, -1, "neutral", DIGNITY_BAND["neutral"], "lord D1 sign unavailable")
            else:
                dig = dignity_of_with_positions(lord, lord_sign, lord_house_d1, d1_houses, ref)
            dignities[("house_lord", str(house))] = dig
            contrib = float(w.weight) * dig.band
            total += contrib
            factor_ledger.append({
                "slot": "house_lord", "house": house, "lord": lord,
                "dignity_state": dig.state, "band": dig.band, "weight": float(w.weight),
                "contribution": contrib, "detail": dig.detail,
            })

        # Karaka slot(s)
        for w in weights:
            if w.slot != "karaka":
                continue
            graha = w.item
            sign = d1_signs.get(graha)
            house_d1 = d1_houses.get(graha)
            dig = dignity_of_with_positions(graha, sign, house_d1, d1_houses, ref)
            dignities[("karaka", graha)] = dig
            contrib = float(w.weight) * dig.band
            total += contrib
            factor_ledger.append({
                "slot": "karaka", "graha": graha, "dignity_state": dig.state,
                "band": dig.band, "weight": float(w.weight), "contribution": contrib,
                "detail": dig.detail,
            })

        # Divisional slot (primary/first-listed karaka, scored in the class's varga)
        for w in weights:
            if w.slot != "divisional":
                continue
            primary_karaka = karyatva.karaka_grahas[0]
            try:
                varga_pos = self.reader.sign_of(chart_id, primary_karaka, karyatva.divisional)
            except ChartReaderError as exc:
                # Honest data gap (§N.7 item 6: an honest null beats an
                # invented judgment) — this chart's build does not carry
                # `karyatva.divisional` varga rows for this graha. Scored
                # as a zero CONTRIBUTION (the slot's weight still counts
                # toward the class's 1.0 ceiling, per §5.1's clamp — this is
                # NOT the same claim as "debilitated", which is why the
                # ledger entry's dignity_state is explicitly None, not
                # "debilitated", and the weight is not redistributed to
                # other slots (redistribution would silently change every
                # OTHER slot's meaning to compensate for a gap in this one).
                factor_ledger.append({
                    "slot": "divisional", "varga": karyatva.divisional, "graha": primary_karaka,
                    "dignity_state": None, "band": None, "weight": float(w.weight),
                    "contribution": 0.0,
                    "detail": f"DATA GAP: {exc} — this chart's build does not carry "
                              f"{karyatva.divisional} varga data for {primary_karaka}; scored 0 "
                              f"contribution (not a debilitation claim).",
                })
                continue
            provenance.extend(varga_pos["provenance"])
            house_d1 = d1_houses.get(primary_karaka)  # tatkalika always from D1 (checkpoint ruling)
            dig = dignity_of_with_positions(
                primary_karaka, varga_pos["sign_number"], house_d1, d1_houses, ref,
            )
            contrib = float(w.weight) * dig.band
            total += contrib
            factor_ledger.append({
                "slot": "divisional", "varga": karyatva.divisional, "graha": primary_karaka,
                "varga_sign": varga_pos["sign"], "dignity_state": dig.state, "band": dig.band,
                "weight": float(w.weight), "contribution": contrib, "detail": dig.detail,
            })

        # Yoga slot — honest gap, always 0.00 (module docstring).
        for w in weights:
            if w.slot != "yoga":
                continue
            contrib = float(w.weight) * YOGA_BAND_NO_MATCH
            total += contrib
            factor_ledger.append({
                "slot": "yoga", "keywords": list(karyatva.yoga_keywords),
                "band": YOGA_BAND_NO_MATCH, "weight": float(w.weight), "contribution": contrib,
                "detail": "honest gap: yoga catalog/firings not exposed by the Chart Reader "
                          "(§2.5 out of Lane B1/B2 scope) — always scored as no-match. "
                          "See module docstring.",
            })

        # Dusthana slot
        core_lord = house_lord_names.get(core_house)
        core_lord_house_d1 = d1_houses.get(core_lord) if core_lord else None
        core_lord_sign = d1_signs.get(core_lord) if core_lord else None
        dusthana_conns: list[DusthanaConnection] = []
        dusthana_ws = [w for w in weights if w.slot == "dusthana"]
        if dusthana_ws:
            for w in dusthana_ws:
                d_house = int(w.item)
                d_lord_info = self.reader.lord_of(chart_id, d_house, "D1")
                provenance.extend(d_lord_info["provenance"])
                d_lord = d_lord_info["lord"]
                d_lord_house_d1 = d1_houses.get(d_lord)
                d_lord_sign = d1_signs.get(d_lord)
                conn = dusthana_connection(
                    d_house, core_house, core_lord, core_lord_house_d1, core_lord_sign,
                    d_lord, d_lord_house_d1, d_lord_sign,
                )
                dusthana_conns.append(conn)
            connected_count = sum(1 for c in dusthana_conns if c.connected)
            band = connected_count / len(dusthana_conns)
            total_dusthana_weight = sum(w.weight for w in dusthana_ws)
            contrib = float(total_dusthana_weight) * band
            total += contrib
            factor_ledger.append({
                "slot": "dusthana", "connections": [
                    {"house": c.house, "connected": c.connected, "reason": c.reason} for c in dusthana_conns
                ],
                "band": band, "weight": float(total_dusthana_weight), "contribution": contrib,
            })

        occurrence_pre_denial = clamp01(total)

        # ── Denials (§4) ────────────────────────────────────────────────
        lagna_house_d1 = d1_houses.get("Lagna", 1)
        moon_house_d1 = d1_houses.get("Moon")
        denial_results: list[DenialResult] = []
        denial_results.append(check_denial_cfg1(karyatva, weights, dignities, lagna_house_d1, moon_house_d1, d1_houses))
        if karyatva.dusthana_required and core_lord is not None:
            denial_results.append(check_denial_cfg2(
                karyatva, weights, core_lord, core_lord_house_d1, core_lord_sign,
                lagna_house_d1, moon_house_d1, d1_houses, ref,
            ))
        if core_lord_house_d1 is not None:
            denial_results.append(check_denial_cfg3(
                karyatva, weights, core_house, core_lord_house_d1, occupants_by_house, ref,
            ))

        total_deduction = sum(float(d.deduction) for d in denial_results if d.fired)
        occurrence = clamp01(total - total_deduction)

        # ── Condition (§5.2) ────────────────────────────────────────────
        condition, cond_ledger = condition_score(
            karyatva.condition_malefic_grahas, core_house, core_lord_house_d1 or core_house, d1_houses,
        )

        return ClassScore(
            event_class_id=event_class_id,
            status="scored",
            occurrence=round(occurrence, 3),
            occurrence_label=occurrence_band(occurrence),
            condition=condition,
            condition_label=condition_band(condition),
            occurrence_pre_denial=round(occurrence_pre_denial, 6),
            factor_ledger=factor_ledger,
            denials=[
                {"config_id": d.config_id, "fired": d.fired, "deduction": float(d.deduction), "reason": d.reason}
                for d in denial_results
            ],
            condition_ledger=cond_ledger,
            weights=[{"slot": w.slot, "item": w.item, "weight": float(w.weight)} for w in weights],
            provenance=provenance,
        )

    def score_all(self, chart_id: str) -> dict[str, ClassScore]:
        return {ec: self.score_class(chart_id, ec) for ec in KARYATVA_REGISTRY}

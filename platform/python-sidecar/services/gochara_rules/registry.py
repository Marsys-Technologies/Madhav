"""rule_path registry P1–P6, class universe, P3 truth table, factor definitions
(GOCHARA_DESIGN_SPECS_v1_4 §2; class table per EVALUATION_PROTOCOL_v2_3 §2).

The catalogue is DATA. Every row carries provenance ∈ {verse_cited,
uncited_extension}, operator_role ∈ {scored, testimony}, and ruling_ref where
required (§0: uncited_extension ⇒ ruling_ref NOT NULL). Primary keys are
composite (id, rule_version); all references between rows are composite —
a bare id is rejected at write time (§2.1).
"""
from __future__ import annotations

from .frames import Frame, SIGN_LORDS, house_span_sign

RULE_VERSION = "1.0.0"


def composite_ref(row_id: str, rule_version: str) -> tuple[str, str]:
    """A composite version-bound reference. Bare ids are rejected (§2.1)."""
    if not row_id or not rule_version:
        raise ValueError("composite reference requires (id, rule_version); bare id rejected")
    return (row_id, rule_version)


# ── Class universe (EVALUATION_PROTOCOL_v2_3 §2 — the sole enumeration) ──────
# polarity: gain | adverse | anchor | non-adverse (protocol's own labels).
CLASS_UNIVERSE: tuple[dict, ...] = tuple(
    {"class": name, "polarity": pol, "adverse": adv}
    for name, pol, adv in [
        ("achievement_recognition", "gain", False),
        ("bereavement", "adverse", True),
        ("birth_anchor", "anchor", False),
        ("business_launch", "gain", False),
        ("career_advancement", "gain", False),
        ("career_change", "gain", False),
        ("career_entry", "gain", False),
        ("career_setback", "adverse", True),
        ("childbirth", "gain", False),
        ("chronic_onset", "adverse", True),
        ("education_milestone", "gain", False),
        ("exam_outcome", "gain", False),
        ("financial_deception", "adverse", True),
        ("foreign_settlement", "gain", False),
        ("illness_acute", "adverse", True),
        ("major_gain", "gain", False),
        ("major_loss", "adverse", True),
        ("marriage", "gain", False),
        ("parental_event", "adverse", True),
        ("property_acquisition", "gain", False),
        ("psychological_arc", "non-adverse", False),
        ("relocation", "gain", False),
        ("romantic_start", "gain", False),
        ("separation", "adverse", True),
        ("spiritual_turn", "non-adverse", False),
        ("surgery", "adverse", True),
        ("travel_event", "gain", False),
    ]
)
assert len(CLASS_UNIVERSE) == 27
CLASS_BY_NAME = {row["class"]: row for row in CLASS_UNIVERSE}

# ── P3 per-class truth table (spec §2.2; H = signature house set) ────────────
# Houses are lagna-frame unless the row names a bhavat_bhavam frame.
P3_TRUTH_TABLE: dict[str, dict] = {
    "marriage_relationship_begin": {"H": {7}, "maraka_lords_of": {2, 7}},
    "separation_relationship_end": {"H": {7, 12, 6}, "maraka_lords_of": {2, 7}},
    # bereavement (father): 9 via bhavat_bhavam:9; 2/7/8 counted FROM the 9th.
    "bereavement_father": {
        "frame": Frame("bhavat_bhavam", 9),
        "H_anchor_house": 9,
        "H_offsets_from_anchor": {1, 2, 7, 8},
        "maraka_lords_of_offsets": {2, 7},
    },
    "childbirth": {"H": {5}, "maraka_lords_of": set()},
    "career": {"H": {10, 6}, "maraka_lords_of": set()},
    "education": {"H": {4, 5}, "maraka_lords_of": set()},
    "financial_gain": {"H": {11, 2}, "maraka_lords_of": set()},
    "financial_loss": {"H": {12, 8}, "maraka_lords_of": set()},
    "relocation_travel": {"H": {4, 12, 9}, "maraka_lords_of": set()},
    "health": {"H": {6, 8, 12}, "maraka_lords_of": set()},
}

# Row membership by protocol class name (spec §2.2, verbatim mapping).
# birth_anchor is excluded from enumeration entirely (O-CF-N6: zero rows).
# The eight named classes carry H = unknown ⇒ admission unqualified (§2.1),
# never false, never admitted — no H is assigned without a citation.
ROW_MEMBERSHIP: dict[str, str | None] = {
    "marriage": "marriage_relationship_begin",
    "romantic_start": "marriage_relationship_begin",
    "separation": "separation_relationship_end",
    "bereavement": "bereavement_father",
    "childbirth": "childbirth",
    "career_entry": "career",
    "career_advancement": "career",
    "career_change": "career",
    "career_setback": "career",
    "education_milestone": "education",
    "exam_outcome": "education",
    "major_gain": "financial_gain",
    "major_loss": "financial_loss",
    "relocation": "relocation_travel",
    "travel_event": "relocation_travel",
    "illness_acute": "health",
    "chronic_onset": "health",
    "surgery": "health",
    "birth_anchor": None,  # excluded entirely
    # H = unknown — the eight named classes (spec §2.2):
    "achievement_recognition": "unknown",
    "business_launch": "unknown",
    "financial_deception": "unknown",
    "foreign_settlement": "unknown",
    "parental_event": "unknown",
    "property_acquisition": "unknown",
    "psychological_arc": "unknown",
    "spiritual_turn": "unknown",
}
assert set(ROW_MEMBERSHIP) == set(CLASS_BY_NAME)


def signature_houses(event_class: str, chart: dict,
                     rule_version: str = RULE_VERSION) -> frozenset[str] | None:
    """The class's signature house set H as concrete sign names on this chart, UNDER THE H TABLE OF
    `rule_version` (FB-44: H is versioned; a generation is replayable under the H it used).

    None ⇒ H unknown at that version (the eight named classes before ND-H-20261005) — admission is
    `unqualified`. At an ND-H version (1.2.0) the eight classes resolve to their CORE tier only: DVI and
    SUPPORT members are NOT in H (`tier_signs`). Raises on birth_anchor (excluded from enumeration,
    O-CF-N6) and on a version with no H table (never a silent fallback to another version's H).
    """
    row_key = ROW_MEMBERSHIP[event_class]
    if row_key is None:
        raise ValueError("birth_anchor is excluded from enumeration entirely (O-CF-N6)")
    if rule_version not in H_TABLE_VERSIONS:
        raise ValueError(f"rule_version {rule_version!r} has no H table (known: {sorted(H_TABLE_VERSIONS)})")
    if row_key == "unknown":
        tiers = tier_signs(event_class, chart, rule_version)
        return None if tiers is None else tiers[TIER_CORE]
    row = P3_TRUTH_TABLE[row_key]
    if "H_anchor_house" in row:
        # e.g. bereavement (father): the 9th and its 2nd/7th/8th, counted
        # from the 9th itself (bhavat_bhavam:9 — spec §2.2 truth table).
        anchor = Frame("bhavat_bhavam", row["H_anchor_house"])
        return frozenset(
            house_span_sign(off, anchor, chart) for off in row["H_offsets_from_anchor"]
        )
    lagna = Frame("lagna")
    return frozenset(house_span_sign(h, lagna, chart) for h in row["H"])


def signature_lords(event_class: str, chart: dict,
                    rule_version: str = RULE_VERSION) -> frozenset[str] | None:
    """L(H): the lord set of the signature house set. None iff H unknown."""
    houses = signature_houses(event_class, chart, rule_version)
    if houses is None:
        return None
    return frozenset(SIGN_LORDS[s] for s in houses)


# ── Kāraka sets per class (spec §2.1: registry content, each row carrying
# its [D] citation) — merged from PROMISE_NATURE_YOGA_MAP_v1_1 §5, itself
# derived from Phaladīpikā Adh. II śl.1–7 (PG47:C1, PG48:C1, PG49:C1) read in
# full; no claim is made beyond those three chunks (F-32 absence predicate).
# State semantics: classes with cited kārakas are `computed`; the rest stay
# `computed_empty` (evaluated, no support found — a result, not an absence
# of work, §1.1).
KARAKA_SOURCE = "PROMISE_NATURE_YOGA_MAP_v1_1 §5 (phaladeepika Adh. II śl.1-7)"


def _karaka_row(karaka: str, locator: str | None, sloka: int | None,
                note: str, *, text: str = "phaladeepika",
                provenance: str = "verse_cited", ruling_ref: str | None = None,
                roles: tuple[str, ...] | None = None) -> dict:
    """Write-time guard: a `verse_cited` kāraka row without its citation is rejected — every cited row
    carries text/locator/śloka (§5; no citation ⇒ the class stays computed_empty instead). The row's
    source text and provenance are PARAMETERS (the Phaladīpikā Adh. II rows are the defaults, byte-for-byte
    as authored); an `uncited_extension` row (a ruled kāraka application) requires its `ruling_ref` (§0)
    and its premise locator, and carries the `roles` its ruling grants (K-A rank / K-B admission)."""
    if provenance not in ("verse_cited", "uncited_extension"):
        raise ValueError(f"kāraka {karaka}: provenance {provenance!r} is not in the closed set")
    if provenance == "verse_cited" and (not locator or sloka is None):
        raise ValueError(f"kāraka {karaka}: citation locator and śloka required")
    if provenance == "uncited_extension" and (not ruling_ref or not locator):
        raise ValueError(f"kāraka {karaka}: uncited_extension requires ruling_ref and a premise locator (§0)")
    row = {"karaka": karaka, "provenance": provenance,
           "citation": {"text": text, "locator": locator,
                        "sloka": sloka},
           "note": note}
    if ruling_ref is not None:
        row["ruling_ref"] = ruling_ref
    if roles is not None:
        row["roles"] = tuple(roles)
    return row


_CLASS_KARAKAS: dict[str, list[dict]] = {
    "marriage": [_karaka_row("Venus", "PG49:C1", 6, "wife/marriage")],
    "romantic_start": [_karaka_row("Venus", "PG49:C1", 6, "wife/marriage")],
    "bereavement": [_karaka_row("Sun", "PG47:C1", 1, "father")],
    "parental_event": [_karaka_row("Sun", "PG47:C1", 1, "father"),
                       _karaka_row("Moon", "PG47:C1", 2, "mother")],
    "childbirth": [_karaka_row("Jupiter", "PG48:C1", 5, "sons")],
    "education_milestone": [_karaka_row("Jupiter", "PG48:C1", 5,
                                        "knowledge/learning"),
                            _karaka_row("Mercury", "PG48:C1", 4,
                                        "learning/intelligence")],
    "exam_outcome": [_karaka_row("Jupiter", "PG48:C1", 5,
                                 "knowledge/learning"),
                     _karaka_row("Mercury", "PG48:C1", 4,
                                 "learning/intelligence")],
    "illness_acute": [_karaka_row("Saturn", "PG49:C1", 7, "sickness")],
    "chronic_onset": [_karaka_row("Saturn", "PG49:C1", 7, "sickness")],
    "surgery": [_karaka_row("Saturn", "PG49:C1", 7, "sickness")],
    "career_entry": [_karaka_row("Sun", "PG47:C1", 1,
                                 "service under the sovereign, glory")],
    "career_advancement": [_karaka_row("Sun", "PG47:C1", 1,
                                       "service under the sovereign, glory")],
    "career_change": [_karaka_row("Sun", "PG47:C1", 1,
                                  "service under the sovereign, glory")],
    "career_setback": [_karaka_row("Sun", "PG47:C1", 1,
                                   "service under the sovereign, glory")],
    "achievement_recognition": [
        _karaka_row("Sun", "PG47:C1", 1, "service under the sovereign, glory")],
    "major_gain": [_karaka_row("Venus", "PG48:C1/PG49:C1", 6,
                               "wealth (śl.6 head/tail)")],
    "major_loss": [_karaka_row("Venus", "PG48:C1/PG49:C1", 6,
                               "wealth (śl.6 head/tail)")],
}
# Mars (brothers, PG47:C1 śl.3) is recorded-but-unused: no sibling class
# exists in the 27-class universe (protocol §2).
KARAKA_UNATTACHED: tuple[dict, ...] = (
    _karaka_row("Mars", "PG47:C1", 3,
                "brothers — recorded, unused (no sibling class in the 27)"),
)

KARAKA_SETS: dict[str, dict] = {
    name: ({"state": "computed", "karakas": _CLASS_KARAKAS[name],
            "source": KARAKA_SOURCE}
           if name in _CLASS_KARAKAS else
           {"state": "computed_empty", "karakas": [], "source": KARAKA_SOURCE})
    for name in CLASS_BY_NAME
}

# ── Yoga→event map (PROMISE_NATURE_YOGA_MAP_v1_1 §6, verbatim; the
# `yoga_constituent` role of spec §2.1). The O-RR-5 fixture yoga ("7L Venus
# conjunct exalted Jupiter in the 9th") is a synthetic oracle fixture and is
# deliberately NOT in this map. §6 has 7 table rows / 9 distinct yoga_ids
# (the last row carries three); every entry is verse_cited with a locator.


def _yoga_row(yoga_id: str, definition: str, event_classes: list[str],
              locator: str | None, sloka: str | None,
              provenance: str = "verse_cited",
              ocr_degradation: str | None = None) -> dict:
    """Write-time guard: a verse_cited yoga entry with no locator fails
    validation (§6; citation is the admission ticket)."""
    if provenance == "verse_cited" and not locator:
        raise ValueError(f"{yoga_id}: verse_cited requires a locator")
    for cls in event_classes:
        if cls not in CLASS_BY_NAME:
            raise ValueError(f"{yoga_id}: unknown event class {cls!r}")
    return {"yoga_id": yoga_id, "definition": definition,
            "event_classes": tuple(event_classes),
            "citation": {"text": ("bphs" if locator and locator.startswith("PG38")
                                  else "phaladeepika"),
                         "locator": locator, "sloka": sloka},
            "provenance": provenance,
            "ocr_degradation": ocr_degradation,
            "source": "PROMISE_NATURE_YOGA_MAP_v1_1 §6"}


YOGA_EVENT_MAP: dict[str, dict] = {r["yoga_id"]: r for r in (
    _yoga_row("Y-MARRIAGE-T1",
              "Venus or 7L transits a sign triangular to lagna-lord's "
              "rāśi/navāṃśa",
              ["marriage"], "PG144:C1", "12"),
    _yoga_row("Y-MARRIAGE-D1",
              "daśā of the occupant / aspector / owner of the 7th",
              ["marriage"], "PG144:C1", "13"),
    _yoga_row("Y-MARRIAGE-DT1",
              "stronger of {7L's rāśi/navāṃśa lords} vs {Venus, Moon} daśā + "
              "Jupiter transiting triangular to 7L's rāśi/navāṃśa",
              ["marriage"], "PG145:C1", "14"),
    _yoga_row("Y-MARRIAGE-COND",
              "7L inimical/debilitated/eclipsed/malefic-aspected AND 7th "
              "afflicted — condition side of the marriage promise",
              ["separation"], "PG145:C1", "15"),
    _yoga_row("Y-ADHI",
              "benefics in 6/7/8 from Moon; result scales with participant "
              "strength",
              ["achievement_recognition", "career_advancement"],
              "PG384:C1", "5",
              ocr_degradation="house order OCR-jumbled in the printed chunk "
                              "('8th, 6th and ?th' = conventional 6/7/8 from "
                              "Moon); recorded [D-with-OCR-degradation] at "
                              "the house list; the event relation is clean"),
    _yoga_row("Y-DHANA",
              "3/2/1 benefics in upachaya from Moon ⇒ very/medium/negligible "
              "affluence",
              ["major_gain"], "PG384:C1", "6"),
    _yoga_row("Y-SUNAPHA",
              "planet (≠ Sun) 2nd from the Moon ⇒ king or equal, "
              "self-earned wealth",
              ["major_gain", "achievement_recognition"], "PG384:C1", "7-10"),
    _yoga_row("Y-ANAPHA",
              "planet (≠ Sun) 12th from the Moon ⇒ king, free from diseases, "
              "virtuous, famous",
              ["major_gain", "achievement_recognition"], "PG384:C1", "7-10"),
    _yoga_row("Y-DURADHARA",
              "planet (≠ Sun) both 2nd and 12th from the Moon ⇒ pleasures, "
              "charitable, wealth, conveyances",
              ["major_gain", "achievement_recognition"], "PG384:C1", "7-10"),
)}

# ── P5 missing-input matrix (spec §2.2, R2-S04) ─────────────────────────────
# Each operand gates exactly its own form — no cross-form knockouts; the whole
# AV build absent is the only cross-form case.
P5_MISSING_INPUT_MATRIX: tuple[dict, ...] = (
    {"form": "P5a", "operand": "per-sign BAV vector of the transiting graha",
     "missing_state": "P5a alone unqualified",
     "chart_state": "resolved, extract v1_0, tier single_pass verbatim"},
    {"form": "P5b", "operand": "SAV per sign",
     "missing_state": "P5b alone unqualified (never P5a)",
     "chart_state": "resolved, extract v1_0 SARVA row"},
    {"form": "P5c", "operand": "per-contributor BAV matrix + donor key",
     "missing_state": "P5c alone disabled",
     "chart_state": "disabled — donor rows pending the native-authorised "
                    "ga_strength rebuild (#2731)"},
    {"form": "P5d", "operand": "pinda + shodhana rows",
     "missing_state": "P5d alone unqualified",
     "chart_state": "resolved except donor-level, extract v1_1; pinda_sarva "
                    "split flagged not recompute-covered"},
    {"form": "P5e", "operand": "solar ingress substrate",
     "missing_state": "P5e alone unqualified",
     "chart_state": "available from L0/L1 as for P1"},
    {"form": "ALL", "operand": "whole AV build",
     "missing_state": "all P5 forms unqualified (the only cross-form case)",
     "chart_state": "n/a on this chart"},
)

# ── P1 prerequisite-(2) relation-kind table (spec §2.2, corpus read B3.8d) ───
P1_RELATION_KINDS: tuple[dict, ...] = (
    {"relation": "occupancy", "target": "signature_house",
     "provenance": "verse_cited", "operator_role": "scored",
     "ruling_ref": None,
     "source": "[D] Parāśari bhāva doctrine (as P3)"},
    {"relation": "ownership", "target": "signature_house",
     "provenance": "verse_cited", "operator_role": "scored",
     "ruling_ref": None,
     "source": "[D] Parāśari bhāva doctrine (as P3)"},
    {"relation": "dispositorship", "target": "node",
     "provenance": "uncited_extension", "operator_role": "testimony",
     "ruling_ref": "D-PADMIT",
     "source": "[P] node-dispositor delivery"},
    {"relation": "dispositorship", "target": "non_node",
     "provenance": "uncited_extension", "operator_role": "testimony",
     "ruling_ref": None,
     "source": "no clause found in PG249:C1/PG250:C1 (śl. 34–39): testimony "
               "pending a native ruling"},
    {"relation": "association", "target": "any",
     "provenance": "uncited_extension", "operator_role": "testimony",
     "ruling_ref": None,
     "source": "no clause found (śl.39's association clause is Rāhu-specific "
               "— testimony under D-PADMIT): testimony"},
)

# ── Factor definitions (spec §2.1 factor contract) ──────────────────────────
# Every scored factor's range ⊆ [0,1]; direction carries the sign with §3's
# class-relative polarity; a missing operand takes null_state, never 0 or 1
# by default. calibration_status = "uncalibrated_default" everywhere until L5.
FACTORS: dict[tuple[str, str], dict] = {}


def _factor(factor_id: str, **kw) -> None:
    row = {
        "factor_id": factor_id,
        "rule_version": RULE_VERSION,
        "calibration_status": "uncalibrated_default",
        **kw,
    }
    FACTORS[composite_ref(factor_id, row["rule_version"])] = row


_factor("dignity_of_transit_sign",
        operand="dignity of the transit sign for the period lord",
        function="categorical_ordered",
        categories=["exaltation", "own", "friendly", "neutral", "inimical",
                    "debility"],
        ordering_anchor={"mulatrikona": 45, "own": 30, "extreme_friend": 20,
                         "friend": 15, "neutral": 10, "enemy": 4,
                         "extreme_enemy": 2,
                         "units": "virupas (saptavargaja-bala)",
                         "source": "BPHS ch.27 śl.2-4, PG264:C1 [D] "
                                   "(PROMISE_NATURE_YOGA_MAP_v1_1 §1.1/§4.1) — "
                                   "ordering anchor ONLY while "
                                   "uncalibrated_default; no magnitude claim"},
        range=[0.0, 1.0], units="unitless",
        direction="doctrine-ordered; the direction field flips the assigned "
                  "channel/valence (O-RP-7), values stay in [0,1]",
        null_state="unqualified",
        effect="exaltation/own → +, debility/inimical → − (P1 factor inventory)")
_factor("combustion",
        operand="combustion state of the period lord",
        function="step", range=[0.0, 1.0], units="unitless",
        direction="lower = stronger", null_state="unqualified",
        effect="combustion → − (P1)")
_factor("activity_kernel",
        operand="angular distance |Δλ| to exact contact",
        function="linear", range=[0.0, 1.0], units="degrees",
        direction="higher = stronger", null_state="unqualified",
        effect="activity = 1 − |Δλ|/orb (M-1 angular kernel, §7.2 inv 3)")
_factor("graduated_drishti",
        operand="aspect house-offset",
        function="step", range=[0.0, 1.0], units="unitless",
        direction="higher = stronger", null_state="unqualified",
        effect="¼/½/¾/1 at 3-10/5-9/4-8/7; specials full (BPHS1:16496-16502)")
# ── AM-13 (RULED, steward M20261002T001617-8321): applicability by object kind ──
# A NEW version of each factor — the 1.0.0 rows above stay byte-for-byte as authored
# (a sealed version is never edited). §2.1 says a missing operand takes its null_state
# ("never silently 1"); a span has no |Δλ| to be missing — "not applicable" is a DECLARED
# state of the row, never a silent 1. `applicability` is the declaration; A's rule_binding
# carries it in operand_selector (token arrays are admitted by ka_gochara_named_operands_ok:
# no DDL). The ORB is NOT ratified anywhere in the spec/registry (draft AM-13 line cites;
# open native decision ND-ORB): `orb_deg` is None and the point branch is
# `unqualified` (reason orb_not_ratified) until it is decided — the unratified 5.0° is not
# carried forward.
KERNEL_VERSION = "1.1.0"
# Classification is by GEOMETRY, not by name (steward M20261002T002620-6575): any target with EXTENT
# (a sign, a house, a 13°20′ nakṣatra = `star:<n>`) takes the membership step; only a true POINT
# target (a longitude) takes the angular kernel. varga_position is not classified (unqualified).
SPAN_OBJECT_KINDS = ("sign_span", "house_span", "star")                  # 1155 kgrr_object_kind_ck
ANGULAR_OBJECT_KINDS = ("degree_point", "derived_point", "saham", "house_lord")
from .flat_selector import (  # noqa: E402  (declared at the point of use: the AM-13 block below)
    ORB_UNRATIFIED, decode_drishti, decode_kernel, encode_drishti, encode_kernel, flat_problems,
)

# The FLAT form is the source of truth (Codex R5): `ka_gochara_factor.operand_selector` admits only a flat
# object of tokens / numbers / token arrays (1154:221–240), so the declaration is written flat, the nested
# `applicability` evaluators read is DERIVED from it by `decode_*`, and a test proves
# encode(decode(flat)) == flat. An unavailable orb is OMITTED (no JSON null); ND-ORB is the `orb_state` token.
_KERNEL_FLAT = {
    "operand": "geometry:object_kind_dispatch",
    "span_kinds": list(SPAN_OBJECT_KINDS), "span_form": "membership_step", "span_inside": 1, "span_outside": 0,
    "point_kinds": list(ANGULAR_OBJECT_KINDS), "point_form": "one_minus_abs_delta_lambda_over_orb",
    "orb_state": ORB_UNRATIFIED,
    "aspect_geometry": "directed_aspect_ray",
    "uncovered_state": "unqualified",
}
_DRISHTI_FLAT = {
    "operand": "geometry:aspect_house_offset", "applicable_relations": ["aspect"],
    "not_applicable_state": "declared_omit", "node_cast_aspects": "none",
}
for _f in (_KERNEL_FLAT, _DRISHTI_FLAT):
    assert not flat_problems(_f), flat_problems(_f)
_factor("activity_kernel",
        rule_version=KERNEL_VERSION,
        operand="object kind + (extent: inside-the-extent membership of the validated contact geometry | "
                "point: seam-safe angular distance |Δλ| along the directed aspect ray, if any)",
        # a PIECEWISE function: membership step on extent targets, 1 − |Δλ|/orb on point targets
        function="piecewise_step_linear", range=[0.0, 1.0], units="unitless",
        direction="higher = stronger", null_state="unqualified",
        operand_selector=_KERNEL_FLAT, applicability=decode_kernel(_KERNEL_FLAT),
        effect="objects with extent (sign/house span, star = 13°20′ nakṣatra): membership step "
               "(1 inside, 0 outside — never a second admission filter); true point objects: "
               "activity = 1 − |Δλ|/orb (§7.2 inv 3), qualified only once the orb is a finite, strictly "
               "positive, RATIFIED decision (ND-ORB open: until then unqualified, reason orb_not_ratified); "
               "object kinds in neither group are unqualified, never 1")
_factor("graduated_drishti",
        rule_version=KERNEL_VERSION,
        operand="aspect house-offset (aspect records only)",
        function="step", range=[0.0, 1.0], units="unitless",
        direction="higher = stronger", null_state="unqualified",
        operand_selector=_DRISHTI_FLAT, applicability=decode_drishti(_DRISHTI_FLAT),
        effect="¼/½/¾/1 at 3-10/5-9/4-8/7; specials full per frozen O-CF-DRISHTI (ordinary graduation "
               "corroborated by brihat_jataka:PG65:C1); applicable to aspect records only — "
               "residence/conjunction have no offset (declared not-applicable, never 1)")
_factor("vedha_attenuation",
        operand="vedha interval state at t",
        function="step", range=[0.0, 1.0], units="unitless",
        direction="higher = stronger", null_state="unqualified",
        effect="attenuation only where state=active; absent overlay coverage "
               "⇒ unavailable, never 1.0 (§5); carried as a rule-row data "
               "field with calibration_status uncalibrated_default — recorded "
               "choice, steward-accepted 2026-09-30 (B5.1 gap 1)")
_factor("yoga_strength",
        operand="declared strength operand of the yoga",
        function="ratio", range=[0.0, 1.0], units="unitless",
        direction="higher = stronger", null_state="unqualified",
        effect="consumed as a named factor (O-RR-5: strength 0.8)")
_factor("promise_condition",
        operand="the promise's condition predicate",
        function="step", range=[0.0, 1.0], units="unitless",
        direction="higher = stronger", null_state="unqualified",
        effect="promise = strength × condition (§2.3 inv 8); condition false "
               "⇒ promise 0 (O-RP-6)")

# ── B5.2 nature/maitrī/strength factor rows (PROMISE_NATURE_YOGA_MAP_v1_1
# §1.1, §2, §3.3) — all interpretive modifiers: they assign channel/valence
# and rank; they NEVER admit, exclude, or zero (spec §2.3 inv 3).
_factor("agent_nature",
        operand="natural benefic/malefic of the agent (waning Moon malefic; "
                "Mercury malefic if joined to a malefic)",
        function="categorical_ordered",
        categories=["benefic", "malefic"],
        range=[0.0, 1.0], units="unitless",
        direction="benefic → favourable channel; malefic → adverse channel, "
                  "class-relative per spec §3.1",
        null_state="unqualified",
        effect="interpretive modifier — channel/valence assignment only "
               "(PROMISE_NATURE_YOGA_MAP_v1_1 §2; BPHS ch.3 śl.11 PG26:C1 [D])")
_factor("moon_paksa",
        operand="Sun–Moon elongation (waxing Śukla / waning Kṛṣṇa)",
        function="step", range=[0.0, 1.0], units="degrees",
        direction="waxing → benefic; waning → malefic",
        null_state="unqualified",
        effect="feeds agent_nature for the Moon (PG26:C1 śl.11 + translator's "
               "Saravali note PG26:C2)")
_factor("mercury_affiliation",
        operand="whether Mercury is joined to a malefic",
        function="step", range=[0.0, 1.0], units="unitless",
        direction="joined to a malefic → malefic; else benefic",
        null_state="unqualified",
        effect="condition predicate feeding agent_nature for Mercury "
               "(PG26:C1 śl.11)")
_factor("maitri_compound",
        operand="pañcādha (compound) maitrī of the agent pair",
        function="categorical_ordered",
        categories=["extreme_friend", "friend", "neutral", "enemy",
                    "extreme_enemy"],
        range=[0.0, 1.0], units="unitless",
        direction="doctrine-ordered five-fold; channel/valence per the §2 "
                  "agent-nature rule",
        null_state="unqualified",
        effect="interpretive modifier (BPHS ch.3 śl.57-58, PG40:C2 [D]; the "
               "chunk's truncated tail is flagged, not reconstructed)")
_factor("sad_bala_summary",
        operand="ṣaḍbala / bhāva-bala summary as L1 operands (never "
                "recomputed here)",
        function="step", range=[0.0, 1.0], units="rupas",
        direction="higher = stronger",
        null_state="unqualified",
        purna_bala_thresholds={"Sun": 6.5, "Moon": 6.0, "Mars": 5.0,
                               "Mercury": 7.0, "Jupiter": 6.5, "Venus": 5.5,
                               "Saturn": 5.0},
        bhava_bala_rule="bhāva-bala = lord's strength + 1 rūpa + dig-bala + "
                        "dṛg-bala of the bhāva (Phaladīpikā IV.24 PG80:C1)",
        effect="binary strong/weak predicate citable (pūrṇa-bala thresholds, "
               "Phaladīpikā IV.22-24 PG79:C1/PG80:C1 [D]); any finer scaling "
               "is not (PROMISE_NATURE_YOGA_MAP_v1_1 §1.1)")

# ── AM-6 Option C: sad_bala_sufficient v1.0 (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT
# §AM-6; Codex v1.4 "AM-6 pick — Option C"; steward M20261001T205832-b69b) ─────
# A unitless STEP factor carrying the cited sufficiency predicate and nothing
# else: output 1 when the operand's total ṣaḍbala (rūpas) is >= the graha's
# threshold (equality IS sufficient), else 0. `range` is the OUTPUT range;
# raw rūpas never bound it and never ride in the score — they travel as typed
# operand evidence (services/gochara_rules/strength.py). Rāhu/Ketu: no
# threshold in the citation, none manufactured → the factor is `unqualified`.
# `null_state` lives on THIS (versioned FACTOR) row — 1154:310-334 — never on a
# path's soft-factor membership row (1154:435-445). "v1.0" in the amendment ≡
# rule_version RULE_VERSION here (every registry row shares one version label).
#
# Citation, read from the SERVED corpus (classical_text_chunks, read-only,
# 2026-10-02): Phaladīpikā adhyāya IV śl.22 (Sun, Moon, Mars, Mercury,
# Jupiter, Venus) and śl.23 (Saturn; "less than the above … weak") are in
# chunk phaladeepika_pg0079_c01 (verse_ref PG79:C1); śl.24 (bhāvabala
# composition — a SEPARATE statement, never combined here) is in
# phaladeepika_pg0080_c01 (PG80:C1). The OCR renders the half-rūpa fractions
# of THREE thresholds as degraded glyphs (Sun "6J-", Jupiter "6j", Venus "5*"):
# the whole-rūpa part is explicit and the ½ is the reading of a degraded
# fraction glyph — [D-with-OCR-degradation], recorded per figure, not smoothed.
_factor("sad_bala_sufficient",
        operand="total ṣaḍbala of the graha, in rūpas — the L1 operand "
                "(never recomputed here); raw value carried as typed operand "
                "evidence, never scored",
        function="step", range=[0.0, 1.0], units="unitless",
        direction="higher = stronger",
        null_state="unqualified",
        factor_version_label="v1.0",
        threshold_comparison="total_rupas >= threshold_rupas -> 1.0, else 0.0 "
                             "(equality is sufficient)",
        thresholds_rupa={"Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
                         "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0},
        threshold_reading={
            "Sun": {"state": "ocr_degraded_fraction_glyph", "ocr_glyph": "6J-",
                    "fraction_confirmed_by": "BPHS ch.27 śl.32-33 (PG286:C1)"},
            "Moon": {"state": "explicit"},
            "Mars": {"state": "explicit"},
            "Mercury": {"state": "explicit"},
            "Jupiter": {"state": "ocr_degraded_fraction_glyph", "ocr_glyph": "6j",
                        "fraction_confirmed_by": "BPHS ch.27 śl.32-33 (PG286:C1)"},
            "Venus": {"state": "ocr_degraded_fraction_glyph", "ocr_glyph": "5*",
                      "fraction_confirmed_by": "BPHS ch.27 śl.32-33 (PG286:C1)"},
            "Saturn": {"state": "explicit"},
        },
        # Second, INDEPENDENT served source (steward M20261001T210607-03ec): BPHS
        # ch.27 śl.32-33 states the minimum ṣaḍbala requirement in virūpas, and the
        # translator's note below it states the same in rūpas. Both read from the
        # served corpus (chunk bphs_pg0286_c01, read-only, 2026-10-02). Per figure:
        # the virūpa figure and the translator's rūpa note agree with the
        # Phaladīpikā threshold above; the Sun/Jupiter/Venus HALF-rūpa fractions
        # are therefore CONFIRMED by a source whose figures (390, 390, 330 virūpas)
        # and rūpa notes (6.5, 6.5, 5.5) are explicit. One residual OCR blemish is
        # recorded, not smoothed: Mercury's virūpa figure prints "42C" in the verse
        # (a degraded 0); its rūpa note ("7'0") is explicit, so Mercury is
        # corroborated by the note, not by the degraded verse digit.
        corroboration={
            "work": "Bṛhat Pārāśara Horā Śāstra", "chapter": 27, "verses": "32-33",
            "corpus_locator": "bphs:PG286:C1", "chunk_id": "bphs_pg0286_c01",
            "chunk_content_sha256": "3c616170d786ffb58d36cdd6e58f1b70e9e43565c64781ef9404abc6ce3b30d6",
            "translator": "R. Santhanam", "edition": "Trans. R. Santhanam, Ranjan Publications, New Delhi (2 vols)",
            "text_id": "bphs",
            "statement": "SHADBALA REQUIREMENTS: 390, 360, 300, 420, 390, 330 and 300 "
                         "virūpas are the Ṣaḍbala piṇḍas needed for the Sun etc. (up to "
                         "Saturn) to be considered strong; if the strength exceeds, the "
                         "planet is very strong",
            "virupas": {"Sun": 390, "Moon": 360, "Mars": 300, "Mercury": 420,
                        "Jupiter": 390, "Venus": 330, "Saturn": 300},
            "translator_note_rupas": {"Sun": 6.5, "Moon": 6.0, "Mars": 5.0,
                                      "Mercury": 7.0, "Jupiter": 6.5, "Venus": 5.5,
                                      "Saturn": 5.0},
            "ocr_blemishes": {"Mercury": {"field": "virupa", "printed": "42C",
                                          "read": 420,
                                          "note": "the rūpa note (7'0) is explicit"}},
            "agreement": "every graha: translator_note_rupas == thresholds_rupa; "
                         "virūpas / 60 == thresholds_rupa",
        },
        unsupported_agents=["Rahu", "Ketu"],
        unsupported_reason="the citation supplies no threshold for the nodes; "
                           "none is manufactured (AM-6)",
        operand_evidence={
            "fact_category": "graha_shadbala_total", "fact_key": "rupa",
            "unit": "rupa",
            "l1_subjects": {"Sun": "SUN", "Moon": "MOON", "Mars": "MAR",
                            "Mercury": "MER", "Jupiter": "JUP", "Venus": "VEN",
                            "Saturn": "SAT", "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN"},
            "carried_fields": ["fact_id", "fact_category", "fact_key",
                               "fact_subject", "build_id", "ayanamsha_id",
                               "verification_pass_status", "value", "unit"],
            "carried_as": "typed operand evidence — outside the factor's output "
                          "range, never a second scored factor; any unit "
                          "conversion is explicit, never inferred",
            "tier_note": "the evaluator copies the L1 row's OWN "
                         "verification_pass_status; it never states a tier "
                         "(the rows read 2026-10-02 were single_pass)",
        },
        citation={
            "work": "Phaladīpikā", "author": "Mantreśvara", "adhyaya": "IV",
            "verses": "IV.22-23",
            "corpus_locator": "phaladeepika:PG79:C1",
            "chunk_id": "phaladeepika_pg0079_c01",
            "chunk_content_sha256": "05e2dd25d2c64584dad3b2bcfd17b642a86959f0e15b778c4b9ddb99d7eb230b",
            "document_id": "55343940-c408-4633-9f18-551fcbcc7ce7",
            "text_id": "phaladeepika",
            "edition": "Trans. V. Subrahmanya Sastri, 2nd Ed. 1950, Aruna Press Bangalore",
            "translator": "V. Subrahmanya Sastri",
            "source_archive": "archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri",
            "text_page": "PG79",
            "bhavabala_statement": {
                "verse": "IV.24", "corpus_locator": "phaladeepika:PG80:C1",
                "chunk_id": "phaladeepika_pg0080_c01",
                "chunk_content_sha256": "2ec000410160bcf2f34d1c9301df3c910baf72df72e57c593b3907b4e29dffc5",
                "use": "cited ONLY for the separate bhāvabala composition "
                       "statement; bhāvabala and ṣaḍbala are never combined",
            },
        },
        l1_required_rupa_note="L1 also carries graha_shadbala_total/required_rupa "
                              "(classical_match). This factor does NOT read it: the "
                              "threshold is the CITED rule parameter above. RECORDED "
                              "DISCREPANCY (2026-10-02, canonical chart, ayanamsha_id "
                              "INVARIANT): L1's Sun required_rupa differs from BOTH served "
                              "sources — Phaladīpikā IV.22 and BPHS ch.27 śl.32-33 "
                              "(PG286:C1, 390 virūpas = 6.5 rūpas); the other six agree. "
                              "Not resolved here — referred to the L1 owner "
                              "(predicate: SELECT fact_subject, fact_value_num FROM "
                              "chart_facts WHERE fact_category='graha_shadbala_total' "
                              "AND fact_key='required_rupa' AND chart_id=<482012f1…>).",
        effect="binary sufficiency classification (Phaladīpikā IV.22-23 [D]); the "
               "citation is a classification, NOT a continuous event-strength "
               "mapping and not a calibrated probability; a missing/unsupported "
               "operand leaves the FACTOR unqualified and never alters a record's "
               "admission_state (1155:822-832: admission derives from the path's "
               "necessary predicates only)")

# Retirement by SUPERSESSION, never by edit: the deferred `sad_bala_summary`
# row above stays byte-for-byte as authored (units 'rupas' violate kgf_units_ck;
# its declared [0,1] range contradicts rūpa magnitudes — ADK-0026, fix the data
# not the detector). Its successor is a NEW row; the binder (kala rule_binding)
# binds the successor and never the retired name.
SUPERSEDED_FACTORS: dict[tuple[str, str], dict] = {
    composite_ref("activity_kernel", RULE_VERSION): {
        "superseded_by": composite_ref("activity_kernel", KERNEL_VERSION),
        "reason": "1.0.0 declares only an angular |Δλ| operand with no orb and no "
                  "applicability: every span-object record is unqualified (AM-13)",
        "source": "GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-13",
    },
    composite_ref("graduated_drishti", RULE_VERSION): {
        "superseded_by": composite_ref("graduated_drishti", KERNEL_VERSION),
        "reason": "1.0.0 does not declare that the factor applies to aspect records only (AM-13)",
        "source": "GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-13",
    },
    composite_ref("sad_bala_summary", RULE_VERSION): {
        "superseded_by": composite_ref("sad_bala_sufficient", RULE_VERSION),
        "reason": "units 'rupas' violate kgf_units_ck and the declared range "
                  "[0,1] contradicts rūpa magnitudes; a unitless step factor "
                  "with raw rūpas as typed evidence replaces it (AM-6 Option C)",
        "source": "GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-6; ASTRA_REVIEW_A5_5_"
                  "SPEC_AMENDMENTS_v1_4",
    },
}

# ── rule_path registry rows P1–P6 (spec §2.2 path catalogue) ────────────────
RULE_PATHS: dict[tuple[str, str], dict] = {}


def _path(path_id: str, **kw) -> None:
    row = {"path_id": path_id, "rule_version": RULE_VERSION, **kw}
    if row["provenance"] == "uncited_extension" and not row.get("ruling_ref"):
        raise ValueError(f"{path_id}: uncited_extension requires ruling_ref (§0)")
    RULE_PATHS[composite_ref(path_id, row["rule_version"])] = row


_path(
    "P1",
    frame="dasha_lord",
    agent_set="running MD/AD/PD lords in their period role (spec §2.1 "
              "exhaustive agent set)",
    relation_set=["residence", "aspect", "conjunction",
                  "dispositorship", "association", "ownership", "occupancy",
                  "period_running"],
    object_selector="(period_lord, natal sign/house objects related to the "
                    "class: signature_house, lord, dispositor)",
    prerequisites=[composite_ref("period_running_at", RULE_VERSION),
                   composite_ref("natal_bhava_relationship", RULE_VERSION),
                   composite_ref("transit_relation", RULE_VERSION)],
    soft_factors=[composite_ref("dignity_of_transit_sign", RULE_VERSION),
                  composite_ref("combustion", RULE_VERSION),
                  composite_ref("agent_nature", RULE_VERSION),
                  composite_ref("maitri_compound", RULE_VERSION)],
    provenance="verse_cited", operator_role="scored", ruling_ref=None,
    source_text="Phaladīpikā", source_page="PG249-250 (XX.34-38)",
    score_rule="within-path product of factor scores over the admitted base",
    note="node-dispositor delivery is [P] D-PADMIT uncited_extension/testimony; "
         "non-node dispositorship and association: no clause found → testimony "
         "(P1_RELATION_KINDS)",
)
_path(
    "P2",
    frame="moon",
    agent_set="the seven grahas + Rāhu/Ketu as agents/targets, never dṛṣṭi "
              "sources (N-14)",
    relation_set=["residence"],
    object_selector="(transiting graha, house from janma-rāśi)",
    prerequisites=[composite_ref("house_from_moon", RULE_VERSION)],
    soft_factors=[composite_ref("vedha_attenuation", RULE_VERSION)],
    provenance="verse_cited", operator_role="scored", ruling_ref=None,
    source_text="Phaladīpikā", source_page="PG321-323 (XXVI.1-8), PG335 (XXVI.11)",
    score_rule="within-path product; vedha qualifies, never excludes",
    note="adverse residence (Saturn/Sun/Mars/Jupiter in 12/8/1) is evidence "
         "FOR the adverse classes (D-RQ5 shape), never attaches to gain "
         "classes; licences the native's fortune, never a relative's event; "
         "vipareeta cancellation per §5",
)
_path(
    "P3",
    frame="lagna",
    agent_set="the seven grahas + Rāhu/Ketu",
    relation_set=["residence", "aspect", "conjunction"],
    object_selector="(agent, signature_house h ∈ H) ∨ (agent, house_lord "
                    "ℓ ∈ L(H)) — union, S-03",
    prerequisites=[composite_ref("p3_contact_house_or_lord", RULE_VERSION)],
    soft_factors=[composite_ref("activity_kernel", RULE_VERSION),
                  composite_ref("graduated_drishti", RULE_VERSION)],
    provenance="verse_cited", operator_role="scored", ruling_ref=None,
    source_text="Yavana Jātaka ch.45-48 + Parāśari bhāva doctrine",
    source_page=None,
    score_rule="within-path product",
    note="relatives via bhavat_bhavam frames; māraka-of-house is [P] D-PADMIT "
         "uncited_extension/testimony; H = unknown classes admit unqualified",
)
_path(
    "P4",
    frame="lagna",
    agent_set=["Jupiter", "Saturn"],
    relation_set=["residence", "aspect", "conjunction"],
    object_selector="ONE rule (R3-S02): infl(g) := (∃h∈H: contact(g,h)) ∨ "
                    "(∃ℓ∈L(H): contact(g,ℓ)); P4_admit := infl(Jupiter) ∧ "
                    "infl(Saturn); the agents need not share one target",
    prerequisites=[composite_ref("p4_double_transit", RULE_VERSION)],
    soft_factors=[composite_ref("activity_kernel", RULE_VERSION)],
    provenance="uncited_extension", operator_role="scored", ruling_ref="D-P4",
    source_text="sole primary joint precedent Phaladīpikā XVII.12 [D]",
    source_page="PG216",
    score_rule="within-path product; peak = argmax min(activity_J, activity_S) "
               "over the overlap (§7.2 inv 2)",
    note=None,
)
_path(
    "P5",
    frame="lagna",
    agent_set="the seven grahas + Rāhu/Ketu",
    relation_set=["residence"],
    object_selector="per form P5a..P5e, each with its own operands and "
                    "missing-data states (S-05; P5_MISSING_INPUT_MATRIX)",
    prerequisites=[composite_ref("av_polarity_declaration_exists", RULE_VERSION)],
    soft_factors=[composite_ref("activity_kernel", RULE_VERSION)],
    provenance="verse_cited", operator_role="scored", ruling_ref=None,
    source_text="BPHS ch.66 vv.13-15 (BPHS2:35666-35684), ch.70 (PG874-876); "
                "Phaladīpikā XXIII (PG301), XXIV (PG304, PG307)",
    source_page=None,
    score_rule="P5a scored output is known-zero detection only (D-RQ1); any "
               "nonzero comparison is unresolved with the operand named; SAV "
               "bands >30/25-30/<25 (BPHS2:42332-42335); no universal numeric "
               "multiplier (D-RQ1)",
    note="after §8 polarity normalisation; T0-11 gates P5 on the declaration row; "
         "P5e substrate gated: no Sun-month selection is computed until a rule "
         "row asks for it — recorded choice, steward-accepted 2026-09-30 "
         "(B5.1 gap 2)",
)
_path(
    "P6",
    frame="per the admitting path's objects",
    agent_set=["Moon"],
    relation_set=["residence"],
    object_selector="day rows inside admitted windows, on demand, with its own "
                    "coverage record (M-3) — never materialised century-wide",
    prerequisites=[composite_ref("admitted_window_exists", RULE_VERSION)],
    soft_factors=[],
    provenance="uncited_extension", operator_role="testimony",
    ruling_ref="D-PADMIT",
    source_text="Muhūrta Cintāmaṇi (MC PG67/PG79 tārā nine-fold)",
    source_page="PG67, PG79",
    score_rule="every P6 operator is testimony: annotate only, never weight, "
               "until the §2.2 promotion gate (B5.4 ablation evidence) fires",
    note="tārā nine-fold, tithi–nakṣatra, Moon's own vedha; chandrāṣṭama "
         "absent as a generic rule (predicate count 0) — context-bound "
         "8th-from-Moon rules only",
)


# ── AM-13: P3/P4/P5 rule_version 1.1.0 — same rows, soft-factor refs moved to the ───
# applicability-declaring factor versions. Predicates are unchanged (1.0.0 refs stay).
# The 1.0.0 path rows are NOT edited; they are recorded as superseded below. In a class
# inventory the older version is excluded as `superseded_by_version` (1206 v1.2).
SUPERSEDED_PATHS: dict[tuple[str, str], dict] = {}
_SOFT_FACTOR_MOVES = {
    composite_ref("activity_kernel", RULE_VERSION): composite_ref("activity_kernel", KERNEL_VERSION),
    composite_ref("graduated_drishti", RULE_VERSION): composite_ref("graduated_drishti", KERNEL_VERSION),
}
for _pid in ("P3", "P4", "P5"):
    _old = RULE_PATHS[composite_ref(_pid, RULE_VERSION)]
    _new = {**_old, "rule_version": KERNEL_VERSION,
            "soft_factors": [_SOFT_FACTOR_MOVES.get(ref, ref) for ref in _old["soft_factors"]]}
    RULE_PATHS[composite_ref(_pid, KERNEL_VERSION)] = _new
    SUPERSEDED_PATHS[composite_ref(_pid, RULE_VERSION)] = {
        "superseded_by": composite_ref(_pid, KERNEL_VERSION),
        "reason": "soft factors moved to activity_kernel@1.1.0 / graduated_drishti@1.1.0 "
                  "(applicability by object kind, AM-13)",
        "source": "GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-13",
    }
del _pid, _old, _new


# ── AM-18 (RULED, steward M20261002T004621-2b84): vedha_attenuation@1.1.0 + P2@1.1.0 ──
# The 1.0.0 vedha_attenuation row carried "a rule-row data field" that never existed. The
# served corpus (Phaladīpikā XXVI.3–8, phaladeepika:PG322:C1 / PG323:C1) says an occupied
# vedha place NULLIFIES the good result of a favourable-house transit and grades nothing, so
# the cited mapping is a STEP: active obstruction -> 0.0, none -> 1.0 (not a calibration).
# The window stays admitted (the record carries qualification `vedha_active`).
from .flat_selector import decode_vedha  # noqa: E402

# FLAT is the source of truth (Codex R5): `operand_selector` admits only tokens / numbers / token arrays (1154:221–240).
_VEDHA_FLAT = {
    "operand": "state:vedha_interval_derived_from_residence",
    "applicable_records": "favourable_residence_cited_pairs_only",
    "map_active": 0, "map_inactive": 1,
    "active_qualification": "vedha_active",
    "unqualified_reasons": ["obstructor_residence_unknown", "node_obstruction_undecided", "node_residence_unknown"],
    "inactive_scope": "excluding_on_demand_moon_obstruction",
    "scope_exempt_primaries": ["mercury"],            # Phaladīpikā XXVI.6: the Moon never obstructs Mercury
    "vipareeta_state": "not_produced_no_served_citation",
}
assert not flat_problems(_VEDHA_FLAT), flat_problems(_VEDHA_FLAT)
_factor("vedha_attenuation",
        rule_version=KERNEL_VERSION,
        operand="vedha state at t, derived from stored residence spans (vedha_derive.derive_vedha)",
        function="step", range=[0.0, 1.0], units="unitless",
        direction="higher = stronger", null_state="unqualified",
        operand_selector=_VEDHA_FLAT, applicability=decode_vedha(_VEDHA_FLAT),
        effect="the cited binary factor is applied to the favourable-residence record's contribution, which is THEN "
               "assigned to the event class's channel: active obstruction nullifies it (0.0; admission and "
               "admitted support are never changed — the record carries qualification vedha_active); "
               "ESTABLISHED inactivity: 1.0 with the scope 'excluding_on_demand_moon_obstruction' (Mercury "
               "excepted); an obstructor residence not established over the span (obstructor_residence_unknown), "
               "Rāhu/Ketu in the vedha house with no cited obstructor (node_obstruction_undecided) or a node "
               "residence gap (node_residence_unknown): unqualified; adverse-residence and uncited (graha, house) "
               "records: declared not-applicable; nothing graded")
SUPERSEDED_FACTORS[composite_ref("vedha_attenuation", RULE_VERSION)] = {
    "superseded_by": composite_ref("vedha_attenuation", KERNEL_VERSION),
    "reason": "1.0.0 promised a rule-row attenuation field that never existed and no value mapping; the "
              "served corpus supports a nullification step only (AM-18)",
    "source": "GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-18; design/P2_VEDHA_ANSWER_v1_0.md",
}
_p2_old = RULE_PATHS[composite_ref("P2", RULE_VERSION)]
RULE_PATHS[composite_ref("P2", KERNEL_VERSION)] = {
    **_p2_old, "rule_version": KERNEL_VERSION,
    "soft_factors": [composite_ref("vedha_attenuation", KERNEL_VERSION)],
}
SUPERSEDED_PATHS[composite_ref("P2", RULE_VERSION)] = {
    "superseded_by": composite_ref("P2", KERNEL_VERSION),
    "reason": "soft factor moved to vedha_attenuation@1.1.0 (cited nullification step, AM-18)",
    "source": "GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-18",
}
del _p2_old


# ══ ND-H-20261005 — the eight classes: three tiers and kārakas, rule_version 1.2.0 ══════════════════
# Sealed decision by delegate (decisions/ND-H-20261005_DECISION_BY_DELEGATE.md, incl. ERRATA 1). It
# supersedes ST-H-UNKNOWN-20261002 for the eight classes AT THIS VERSION ONLY: the 1.0.0 / 1.1.0 rows
# above are untouched and still resolve H = unknown for them.
#
#   CORE    — in H for P1 / P3 / P4, all agents.
#   DVI     — double-transit-only: counts toward infl(g), g ∈ {Jupiter, Saturn}, the house or its lord,
#             in P4 and NOWHERE else (admits nothing in P1 or P3).
#   SUPPORT — annotation rows, operator_role testimony, OUTSIDE H.
#   K-A     — rank factor `karaka_agent` only; never admits, excludes or zeroes.
#   K-B     — admission, luminaries only: natal Sun / Moon as a degree-point target (object_role karaka)
#             for Jupiter/Saturn (conjunction or aspect) and Rāhu/Ketu (conjunction) in P3 and P4's infl().
#
# Every row is `uncited_extension / scored / ruling_ref ND-H-20261005` (spec §0: a derived event rule
# scores only under a ruling, however well its premises are cited); premise loci ride in `sources`,
# with ERRATA 1 applied (UK Mars "House" = PG125:C1, Mercury "Commerce" = PG125:C2; BPHS 15.14 dropped
# for property; no Jātaka Pārijāta PG562 for Rāhu). The loci cite MEANINGS; the event rules are derived.
ND_H_VERSION = "1.2.0"
ND_H_RULING = "ND-H-20261005"
TIER_CORE, TIER_DVI, TIER_SUPPORT = "core", "dvi", "support"
TIERS = (TIER_CORE, TIER_DVI, TIER_SUPPORT)
KARAKA_RANK = "K-A"            # rank factor only
KARAKA_ADMISSION = "K-B"       # luminary admission target
LUMINARIES = frozenset({"Sun", "Moon"})
#: the stamp of every ND-H row
ND_H_STAMP = {"provenance": "uncited_extension", "operator_role": "scored", "ruling_ref": ND_H_RULING}
#: the stamp of the pre-ND-H class rows (spec §2.2 truth table: cited Parāśari bhāva doctrine)
BASE_CLASS_STAMP = {"provenance": "verse_cited", "operator_role": "scored", "ruling_ref": None}
_UK = "uttara_kalamrita"


def _nd_karaka(karaka: str, locator: str, note: str, *roles: str, text: str = _UK) -> dict:
    for role in roles:
        if role not in (KARAKA_RANK, KARAKA_ADMISSION):
            raise ValueError(f"kāraka {karaka}: unknown role {role!r}")
    if KARAKA_ADMISSION in roles and karaka not in LUMINARIES:
        raise ValueError(f"kāraka {karaka}: K-B is for the luminaries only (ND-H-20261005)")
    return _karaka_row(karaka, locator, None, note, text=text, provenance="uncited_extension",
                       ruling_ref=ND_H_RULING, roles=roles)


def _nd_h_row(*, core, dvi=(), support=(), karakas, sources, anchor_house=None,
              affected_person="native", notes=None) -> dict:
    """One ND-H class row. Houses are lagna-frame house numbers, or OFFSETS counted from `anchor_house`
    (bhavat_bhavam) when it is set. Write-time guards: tiers are disjoint; CORE is non-empty."""
    core, dvi, support = tuple(core), tuple(dvi), tuple(support)
    if not core:
        raise ValueError("an ND-H row needs at least one CORE house")
    if len(set(core) | set(dvi) | set(support)) != len(core) + len(dvi) + len(support):
        raise ValueError("ND-H tiers must be disjoint")
    return {"rule_version": ND_H_VERSION, **ND_H_STAMP,
            "anchor_house": anchor_house, "affected_person": affected_person,
            TIER_CORE: core, TIER_DVI: dvi, TIER_SUPPORT: support,
            "karakas": tuple(karakas), "sources": tuple(sources), "notes": notes}


ND_H_ROWS: dict[str, dict] = {
    "achievement_recognition": _nd_h_row(
        core=(10,), dvi=(11,), support=(5, 1, 9),
        karakas=(_nd_karaka("Sun", "PG47:C1", "glory, service under the sovereign", KARAKA_RANK,
                            text="phaladeepika"),
                 _nd_karaka("Jupiter", "PG127:C1", "honour from the king", KARAKA_RANK)),
        sources=("Phaladīpikā I.15", "BPHS 11.11", "Uttara Kālāmṛta PG127:C1 (meanings)")),
    "business_launch": _nd_h_row(
        core=(7, 10), support=(6,),
        karakas=(_nd_karaka("Mercury", "PG125:C2", "commerce", KARAKA_RANK),),
        sources=("Phaladīpikā I.15", "BPHS 11.8", "Uttara Kālāmṛta PG125:C2 (Commerce)")),
    "financial_deception": _nd_h_row(
        core=(2, 12), dvi=(6,), support=(8,),
        karakas=(_nd_karaka("Rahu", "PG131:C1", "falsehood, perplexity", KARAKA_RANK),),
        sources=("Phaladīpikā I.13", "Phaladīpikā I.16", "BPHS 24.18",
                 "Uttara Kālāmṛta PG121:C1", "Uttara Kālāmṛta PG131:C1 (Rāhu)"),
        notes="Saturn excluded as a kāraka; Mercury not added; no 'Rāhu must be involved' gate"),
    "foreign_settlement": _nd_h_row(
        core=(12,), dvi=(4,), support=(9, 7),
        karakas=(_nd_karaka("Rahu", "PG131:C1", "going to a different country", KARAKA_RANK),),
        sources=("Uttara Kālāmṛta PG121:C1 (migrating to a different place)", "Jātaka Pārijāta VIII.97",
                 "Uttara Kālāmṛta PG131:C1 (Rāhu)"),
        notes="Saturn excluded as a kāraka; the 10th is noted beside SUPPORT 9/7, not a tier member"),
    # father: bhavat_bhavam:9 — CORE offsets 1, 6 from the 9th (lagna 9, 2); SUPPORT the 8th and 12th
    # FROM the 9th (lagna 4, 8). No DVI (the row is adverse).
    "parental_event": _nd_h_row(
        anchor_house=9, affected_person="father",
        core=(1, 6), support=(8, 12),
        karakas=(_nd_karaka("Sun", "PG47:C1", "father", KARAKA_RANK, KARAKA_ADMISSION,
                            text="phaladeepika"),),
        sources=("BPHS 7.39-43", "BPHS 23.7", "Phaladīpikā II.1 (Sun: father — meaning only)"),
        notes="offsets derived; P2 emits no parental_event row (the native's Moon never evidences the parent)"),
    "property_acquisition": _nd_h_row(
        core=(4,), dvi=(11,), support=(2,),
        karakas=(_nd_karaka("Mars", "PG125:C1", "land, house", KARAKA_RANK),),
        sources=("BPHS 11.5", "Phaladīpikā I.12", "Uttara Kālāmṛta PG125:C1 (Mars: House)")),
    "psychological_arc": _nd_h_row(
        core=(4,), support=(5, 8),
        karakas=(_nd_karaka("Moon", "PG47:C1", "Phaladīpikā II.2 (the Moon's significations)", KARAKA_ADMISSION,
                            text="phaladeepika"),),
        sources=("BPHS 11.5", "Phaladīpikā I.12", "Phaladīpikā II.2")),
    "spiritual_turn": _nd_h_row(
        core=(9, 5), support=(12,),
        karakas=(_nd_karaka("Jupiter", "PG127:C1", "penance, dharma, mantra", KARAKA_RANK),
                 _nd_karaka("Ketu", "PG132:C1", "final salvation, great penance, renunciation",
                            KARAKA_RANK)),
        sources=("Phaladīpikā I.14", "Phaladīpikā I.12", "BPHS 11.6", "BPHS 11.10",
                 "Uttara Kālāmṛta PG127:C1", "Uttara Kālāmṛta PG132:C1"),
        notes="12 is SUPPORT by ratification only (practice; no śloka located); Saturn is testimony on "
              "contacts to the 12th SUPPORT member only — never a scored kāraka"),
}
ND_H_CLASSES = frozenset(ND_H_ROWS)
assert ND_H_CLASSES == {c for c, k in ROW_MEMBERSHIP.items() if k == "unknown"}

#: ND-H item 5: the mother row is REGISTERED, UNBUILT — anchor 4, offsets {1, 6} (lagna 4, 9), Moon
#: K-A + K-B — `unsupported` until a per-person selector exists. A mother-tagged event must FAIL to
#: resolve, never resolve as father (`parental_person_row`).
PARENTAL_PERSON_ROWS: dict[str, dict] = {
    "father": {"state": "built", "event_class": "parental_event", "anchor_house": 9, "core_offsets": (1, 6)},
    "mother": {"state": "unsupported", "event_class": "parental_event", "anchor_house": 4,
               "core_offsets": (1, 6), "karakas": (("Moon", (KARAKA_RANK, KARAKA_ADMISSION)),),
               "reason": "no per-person selector exists (ND-H-20261005 item 5)", "ruling_ref": ND_H_RULING},
}
#: ND-H item 5: P2 emits no row for these classes (native Moon never evidences the parent, §1.2 inv 6).
P2_NO_ROW_CLASSES = frozenset({"parental_event"})


class UnsupportedPerson(LookupError):
    """A person-tagged event whose row is registered but unbuilt — refused by name, never re-routed."""


def parental_person_row(person: str) -> dict:
    """The parental_event row for `person`. `mother` (registered, unbuilt) and any unknown person
    REFUSE — a mother-tagged event never resolves as father."""
    row = PARENTAL_PERSON_ROWS.get(person)
    if row is None:
        raise UnsupportedPerson(f"parental_event: no row for person {person!r}")
    if row["state"] != "built":
        raise UnsupportedPerson(f"parental_event/{person}: {row['state']} — {row['reason']}")
    return row


# ── ND-P2-20261005 rule 3 — natal Sun as a target for FATHER-BEREAVEMENT ─────────────────────────────
# Uniform with the father's-illness K-B rule: for the father-specific bereavement class the natal Sun is a
# DERIVED target under ruling provenance — in P3 Jupiter and Saturn by conjunction or aspect, Rāhu and Ketu
# by conjunction; in P4 Jupiter and Saturn only (the same agent table as every K-B edge). Houses and māraka
# testimony are UNCHANGED (the class keeps its cited H). Basis, stated honestly: the Sun signifies the
# father (Phaladīpikā II.1 — cited MEANING; ERRATA 1 item 4: "bereavement" is not in the verse); its use for
# the father's death is a derivation, scoring-eligible by the ruling.
# BAND: the built 1-degree point band (gochara_kernel/convention.py orb_conj_slow / orb_drishti_slow) —
# ND-P2 rule 3 also corrects ND-H's "5°". No orb is carried on an edge: the target is a degree point and the
# contact engine applies the convention's band.
ND_P2_RULING = "ND-P2-20261005"
ND_P2_STAMP = {"provenance": "uncited_extension", "operator_role": "scored", "ruling_ref": ND_P2_RULING}
#: {class: K-B targets added by ND-P2 rule 3} and the paths the rule reaches (P3 and P4's infl(); never P1)
ND_P2_KB_TARGETS: dict[str, tuple[dict, ...]] = {
    "bereavement": ({"luminary": "Sun", "affected_person": "father", **ND_P2_STAMP,
                     "sources": ("Phaladīpikā II.1 (Sun: father — meaning only; the death application "
                                 "is a derivation)",)},),
}
ND_P2_KB_PATHS = ("P3", "P4")

#: FB-44: which H table each rule_version reads. 1.0.0 and 1.1.0 share the spec §2.2 truth table.
H_TABLE_VERSIONS: dict[str, str] = {RULE_VERSION: "spec_2_2", KERNEL_VERSION: "spec_2_2",
                                    ND_H_VERSION: "spec_2_2+nd_h_20261005+nd_p2_20261005"}
#: the versions at which the ND-H / ND-P2 rows are read
ND_VERSIONS = frozenset({ND_H_VERSION})


def nd_h_row(event_class: str, rule_version: str) -> dict | None:
    """The class's ND-H row AT `rule_version`, or None (not an ND-H class, or a pre-ND-H version)."""
    if rule_version not in ND_VERSIONS:
        return None
    return ND_H_ROWS.get(event_class)


def class_row_stamp(event_class: str, rule_version: str) -> dict:
    """(provenance, operator_role, ruling_ref) of the class's H row at `rule_version` — the stamp its
    signature-house and lord edges carry (FB-39: read from the row, never hardcoded in an enumerator)."""
    return dict(ND_H_STAMP if nd_h_row(event_class, rule_version) is not None else BASE_CLASS_STAMP)


def class_frame(event_class: str, rule_version: str = RULE_VERSION) -> tuple[str, str | None]:
    """(frame_kind, frame_arg) of the class's H row at `rule_version`."""
    row = nd_h_row(event_class, rule_version)
    if row is None:
        key = ROW_MEMBERSHIP[event_class]
        row = P3_TRUTH_TABLE.get(key) if key not in (None, "unknown") else None
        if row and "H_anchor_house" in row:
            return "bhavat_bhavam", str(row["H_anchor_house"])
        return "lagna", None
    if row["anchor_house"] is not None:
        return "bhavat_bhavam", str(row["anchor_house"])
    return "lagna", None


def tier_signs(event_class: str, chart: dict, rule_version: str) -> dict[str, frozenset[str]] | None:
    """{tier: concrete signs on this chart} of an ND-H class at an ND-H version; None otherwise."""
    row = nd_h_row(event_class, rule_version)
    if row is None:
        return None
    frame = Frame("lagna") if row["anchor_house"] is None else Frame("bhavat_bhavam", row["anchor_house"])
    return {tier: frozenset(house_span_sign(h, frame, chart) for h in row[tier]) for tier in TIERS}


def tier_table_lagna(rule_version: str = ND_H_VERSION) -> dict[str, dict[str, tuple[int, ...]]]:
    """The tier table as LAGNA-frame house numbers (an anchored row's offsets resolved: the n-th from
    house a is house ((a + n − 2) mod 12) + 1) — the form the ruling's table is written in."""
    out = {}
    for name in sorted(ND_H_ROWS):
        row = nd_h_row(name, rule_version)
        if row is None:
            continue
        a = row["anchor_house"]
        out[name] = {tier: tuple(sorted(h if a is None else ((a + h - 2) % 12) + 1 for h in row[tier]))
                     for tier in TIERS}
    return out


def karaka_set(event_class: str, rule_version: str = RULE_VERSION) -> dict:
    """The class's kāraka set AT `rule_version` — the production reader of `KARAKA_SETS`. An ND-H class
    at an ND-H version reads its ruled rows (with roles); everything else reads the cited
    Phaladīpikā Adh. II sets, which grant NO role (no K-A, no K-B)."""
    row = nd_h_row(event_class, rule_version)
    if row is None:
        return KARAKA_SETS[event_class]
    return {"state": "computed", "karakas": list(row["karakas"]),
            "source": f"ruling:{ND_H_RULING} (premise loci per row)"}


def karakas_with_role(event_class: str, role: str, rule_version: str = RULE_VERSION) -> frozenset[str]:
    return frozenset(k["karaka"] for k in karaka_set(event_class, rule_version)["karakas"]
                     if role in k.get("roles", ()))


def karaka_category(event_class: str, agent: str, rule_version: str = RULE_VERSION) -> str:
    """K-A: the `karaka_agent` factor's category for a transit record's agent (Title case) —
    'karaka' iff the agent is a K-A kāraka of the class at this version, else 'non_karaka'. A RANK
    category only: it never admits, excludes or zeroes."""
    return "karaka" if agent in karakas_with_role(event_class, KARAKA_RANK, rule_version) else "non_karaka"


def kb_luminaries(event_class: str, rule_version: str = RULE_VERSION) -> frozenset[str]:
    """K-B: the natal luminaries that are admission TARGETS for the class at this version."""
    return karakas_with_role(event_class, KARAKA_ADMISSION, rule_version) & LUMINARIES


def kb_targets(event_class: str, rule_version: str = RULE_VERSION) -> tuple[dict, ...]:
    """Every K-B admission target of the class at this version, each with ITS OWN stamp and premise text:
    the ND-H luminary kārakas (ND-H-20261005) and the ND-P2 rule 3 target (natal Sun, father-bereavement).
    {luminary, provenance, operator_role, ruling_ref, source_text}, in a total order."""
    out = []
    row = nd_h_row(event_class, rule_version)
    if row is not None:
        text = f"ruling {row['ruling_ref']}; premises: " + "; ".join(row["sources"])
        for luminary in sorted(kb_luminaries(event_class, rule_version)):
            out.append({"luminary": luminary, "provenance": row["provenance"],
                        "operator_role": row["operator_role"], "ruling_ref": row["ruling_ref"],
                        "source_text": text})
    if rule_version in ND_VERSIONS:
        for t in ND_P2_KB_TARGETS.get(event_class, ()):
            if t["luminary"] not in LUMINARIES:
                raise ValueError(f"K-B target {t['luminary']!r} is not a luminary")
            out.append({"luminary": t["luminary"], "provenance": t["provenance"],
                        "operator_role": t["operator_role"], "ruling_ref": t["ruling_ref"],
                        "source_text": f"ruling {t['ruling_ref']}; premises: " + "; ".join(t["sources"])})
    return tuple(sorted(out, key=lambda t: (t["luminary"], t["ruling_ref"])))


#: K-B agents and relations (ND-H): slow agents only; nodes cast no dṛṣṭi (N-14). Fast agents never.
KB_AGENT_RELATIONS: dict[str, tuple[str, ...]] = {
    "Jupiter": ("conjunction", "aspect"), "Saturn": ("conjunction", "aspect"),
    "Rahu": ("conjunction",), "Ketu": ("conjunction",),
}
#: DVI is read by P4's infl() only, for exactly these agents.
DVI_AGENTS = ("Jupiter", "Saturn")


def h_table(rule_version: str) -> dict:
    """The WHOLE H table of `rule_version` as canonical data (FB-44) — every class of the universe:
    its frame, its tiers (lagna houses or anchor offsets), its stamp, and its kāraka roles."""
    if rule_version not in H_TABLE_VERSIONS:
        raise ValueError(f"rule_version {rule_version!r} has no H table")
    table = {}
    for name in sorted(CLASS_BY_NAME):
        key = ROW_MEMBERSHIP[name]
        nd = nd_h_row(name, rule_version)
        if key is None:
            table[name] = {"state": "excluded"}
        elif nd is not None:
            table[name] = {
                "state": "ruled", "anchor_house": nd["anchor_house"],
                "affected_person": nd["affected_person"],
                **{tier: sorted(nd[tier]) for tier in TIERS},
                "stamp": [nd["provenance"], nd["operator_role"], nd["ruling_ref"]],
                "karakas": sorted([k["karaka"], sorted(k["roles"])] for k in nd["karakas"])}
        elif key == "unknown":
            table[name] = {"state": "unknown"}
        else:
            row = P3_TRUTH_TABLE[key]
            table[name] = {"state": "cited", "anchor_house": row.get("H_anchor_house"),
                           TIER_CORE: sorted(row.get("H", row.get("H_offsets_from_anchor", ())))}
        if rule_version in ND_VERSIONS and name in ND_P2_KB_TARGETS:
            table[name]["kb_targets"] = sorted([t["luminary"], t["ruling_ref"]] for t in ND_P2_KB_TARGETS[name])
    return {"h_table": H_TABLE_VERSIONS[rule_version], "rule_version": rule_version, "classes": table}


def h_table_sha256(rule_version: str) -> str:
    import hashlib
    import json
    return hashlib.sha256(json.dumps(h_table(rule_version), sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


# ── K-A: the `karaka_agent` factor row (ND-H: categorical_ordered {karaka > non_karaka}) ────────────
# No value mapping is ruled, so none is declared (uncalibrated_default); null_state `omit` — a factor
# that cannot yield a number takes NO part in the within-path product, which is exactly "never admits,
# excludes or zeroes". The category is read by `karaka_category`.
_factor("karaka_agent",
        rule_version=ND_H_VERSION,
        operand="whether the transit record's agent is a K-A kāraka of the event class "
                "(registry karaka_set at the record's rule_version)",
        function="categorical_ordered",
        categories=["karaka", "non_karaka"],
        range=[0.0, 1.0], units="unitless",
        direction="higher = stronger", null_state="omit",
        ruling_ref=ND_H_RULING,
        effect="rank factor only (K-A, ND-H-20261005): orders records whose agent is a class kāraka "
               "above the rest; never admits, excludes or zeroes; no value mapping is declared "
               "(uncalibrated_default), so it is omitted from the within-path product")

# ── P1 / P3 / P4 at rule_version 1.2.0 ───────────────────────────────────────────────────────────
# NEW rows; the 1.0.0 and 1.1.0 rows are not edited and 1.1.0 stays unbound (FB-30), so the 1.2.0 rows
# derive from the BOUND 1.0.0 rows: same prerequisites, same soft factors + karaka_agent@1.2.0. They are
# selected per class (the binder's CLASS_SELECTION_OVERRIDES), never globally. Each row carries the H
# table it reads and that table's digest in `score_rule` — the one free-text column of
# ka_gochara_rule_path the registry digest covers — so a generation's registry digest pins its H.
#: class-scoped supersession (FB-32): for an ND-H class the 1.0.0 row is searched no more.
CLASS_SUPERSEDED_PATHS: dict[tuple[str, str, str], dict] = {}
for _pid in ("P1", "P3", "P4"):
    _old = RULE_PATHS[composite_ref(_pid, RULE_VERSION)]
    RULE_PATHS[composite_ref(_pid, ND_H_VERSION)] = {
        **_old, "rule_version": ND_H_VERSION, **ND_H_STAMP,
        "soft_factors": [*_old["soft_factors"], composite_ref("karaka_agent", ND_H_VERSION)],
        "source_text": f"ruling {ND_H_RULING} (derived event rules; premise loci on each class row)",
        "source_page": None,
        "h_table_version": ND_H_VERSION, "h_table_sha256": h_table_sha256(ND_H_VERSION),
        "score_rule": (f"{_old['score_rule']}; H table {H_TABLE_VERSIONS[ND_H_VERSION]}@{ND_H_VERSION} "
                       f"sha256:{h_table_sha256(ND_H_VERSION)}"),
        "note": f"{ND_H_RULING}: tiers CORE (in H) / DVI (P4 infl only) / SUPPORT (testimony, outside H); "
                "kārakas K-A (rank) / K-B (luminary admission target)"
                + ("; the double-transit rule itself stays D-P4" if _pid == "P4" else ""),
    }
    for _cls in sorted(ND_H_CLASSES):
        CLASS_SUPERSEDED_PATHS[(_cls, _pid, RULE_VERSION)] = {
            "superseded_by": composite_ref(_pid, ND_H_VERSION), "ruling_ref": ND_H_RULING,
            "reason": "H unknown at 1.0.0 (ST-H-UNKNOWN-20261002); ruled at 1.2.0"}
del _pid, _old, _cls
# ND-P2 rule 3: father-bereavement runs P3 and P4 under 1.2.0 (its natal-Sun target lives there); P1 stays.
for _cls in sorted(ND_P2_KB_TARGETS):
    for _pid in ND_P2_KB_PATHS:
        CLASS_SUPERSEDED_PATHS[(_cls, _pid, RULE_VERSION)] = {
            "superseded_by": composite_ref(_pid, ND_H_VERSION), "ruling_ref": ND_P2_RULING,
            "reason": "natal Sun as a derived target for father-bereavement (ND-P2-20261005 rule 3)"}
del _pid, _cls

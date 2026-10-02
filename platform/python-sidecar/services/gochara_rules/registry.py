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


def signature_houses(event_class: str, chart: dict) -> frozenset[str] | None:
    """The class's signature house set as concrete sign names on this chart.

    None ⇒ H unknown (the eight named classes) — admission is `unqualified`.
    Raises on birth_anchor (excluded from enumeration, O-CF-N6).
    """
    row_key = ROW_MEMBERSHIP[event_class]
    if row_key is None:
        raise ValueError("birth_anchor is excluded from enumeration entirely (O-CF-N6)")
    if row_key == "unknown":
        return None
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


def signature_lords(event_class: str, chart: dict) -> frozenset[str] | None:
    """L(H): the lord set of the signature house set. None iff H unknown."""
    houses = signature_houses(event_class, chart)
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
                note: str) -> dict:
    """Write-time guard: a kāraka row without its citation is rejected —
    every cited row carries text/locator/śloka (§5; no citation ⇒ the class
    stays computed_empty instead)."""
    if not locator or sloka is None:
        raise ValueError(f"kāraka {karaka}: citation locator and śloka required")
    return {"karaka": karaka, "provenance": "verse_cited",
            "citation": {"text": "phaladeepika", "locator": locator,
                         "sloka": sloka},
            "note": note}


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
    "unqualified_reasons": ["node_obstruction_undecided"],
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
        effect="active obstruction nullifies the favourable result: 0.0 on the FOR-channel (window stays "
               "admitted, record carries qualification vedha_active); no active obstruction: 1.0 with the "
               "scope 'excluding_on_demand_moon_obstruction' (Mercury excepted); Rāhu/Ketu in the vedha "
               "house with no cited obstructor: unqualified (node_obstruction_undecided); adverse-residence "
               "and uncited (graha, house) records: declared not-applicable; nothing graded")
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

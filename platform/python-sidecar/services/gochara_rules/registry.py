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


# ── Kāraka sets per class (spec §2.1: registry content, each carrying its
# [D] citation or ruling) — no cited kāraka exists yet (B5.2 supplies them);
# every class therefore carries an EMPTY set in state `computed_empty`
# (evaluated, no support found — a result, not an absence of work, §1.1).
KARAKA_SETS: dict[str, dict] = {
    name: {"state": "computed_empty", "karakas": [], "pending": "B5.2"}
    for name in CLASS_BY_NAME
}

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
    FACTORS[composite_ref(factor_id, RULE_VERSION)] = row


_factor("dignity_of_transit_sign",
        operand="dignity of the transit sign for the period lord",
        function="categorical_ordered",
        categories=["exaltation", "own", "friendly", "neutral", "inimical",
                    "debility"],
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
_factor("vedha_attenuation",
        operand="vedha interval state at t",
        function="step", range=[0.0, 1.0], units="unitless",
        direction="higher = stronger", null_state="unqualified",
        effect="attenuation only where state=active; absent overlay coverage "
               "⇒ unavailable, never 1.0 (§5)")
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

# ── rule_path registry rows P1–P6 (spec §2.2 path catalogue) ────────────────
RULE_PATHS: dict[tuple[str, str], dict] = {}


def _path(path_id: str, **kw) -> None:
    row = {"path_id": path_id, "rule_version": RULE_VERSION, **kw}
    if row["provenance"] == "uncited_extension" and not row.get("ruling_ref"):
        raise ValueError(f"{path_id}: uncited_extension requires ruling_ref (§0)")
    RULE_PATHS[composite_ref(path_id, RULE_VERSION)] = row


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
                  composite_ref("combustion", RULE_VERSION)],
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
    note="after §8 polarity normalisation; T0-11 gates P5 on the declaration row",
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

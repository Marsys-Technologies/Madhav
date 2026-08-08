"""
valence_doctrine.py — the SINGLE authoritative valence computation (DR-9 / DIS.022).

Estate-wide root fix for the D-16 / CR-54 / CR-83 valence-lineage (VAL-ROOT in
MARSYS_DEFECT_GAP_REGISTER). Before this module, valence was computed in ≥4
divergent places, each with a different (all wrong) method that defaulted
adverse configurations to favorable:
  - bo_karanajala._EDGE_TYPE_VALENCE keyed edge valence on edge TYPE
    ("aspect"→"harmonious") ignoring the grahas' natures → 121/121 mechanisms
    on 482012f1 = "benefic", incl. Mars↔Saturn (two malefics);
  - ga_vichara.compute_valence used an (actor_lordship_class × target_house)
    matrix that pre-empted its own dusthāna-affliction rule for dual-lord Mars
    and had no contact-type dimension and skipped Rahu/Ketu;
  - V-5's dhana_axis / tenancy emitters hardcoded valence="benefic".

This module is the ONE doctrine-grounded computation every valence-emitting
site consumes. Two entry points:
  * graha_valence(...)  — a graha's own signed standing (occupancy / aspect-given
    / lordship signals). Weighs natural × functional × dignity × contact-type.
  * edge_valence(...)   — the valence of a RELATIONSHIP between two grahas
    (mechanism edges). Weighs the two endpoints' NATURAL natures + relationship
    harshness (functional lordship governs a graha's own house-results, not the
    texture of a malefic↔malefic mutual affliction).

Doctrine grounds (DR-9, native-ratified — BPHS):
  1. Natural nature (svabhāva, BPHS Ch.3): Rahu/Ketu/Mars/Saturn = malefic;
     Sun = mild malefic; Jupiter/Venus = benefic; Moon conditional on waxing;
     Mercury conditional on affliction.
  2. Functional lordship for the lagna (BPHS Ch.34) — CONSUMED from the stored
     graha_functional_class_per_ascendant fact, never re-derived here (§N.5).
  3. Dignity/state modifiers (exaltation / own / debilitation / combustion).
  4. Contact type: occupancy vs aspect; Mars's 4th/8th & Saturn's 3rd/10th
     special aspects carry harsh texture; benefic drishti softens.

Output is SIGNED and can be MIXED — the 4-way vocabulary {benefic, malefic,
mixed, neutral}. `mixed` is FIRST-CLASS: a genuine tension where a benefic
component AND a malefic component both exist and are both non-trivial (e.g.
exalted Rahu in the dhana bhāva — unconventional gains AND deception/loss).
It is NEVER a weak-neutral fallback.

Anti-overcorrection is the design's load-bearing constraint (DR-9 specimen
gate, BOTH directions): all-benefic was the bug; all-adverse (or any single-
value collapse) is the same bug with a different constant.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from brahmagyan.graha_vocabulary import norm_graha  # noqa: F401 — re-exported (ADHIṢṬHĀNA A2)

VALENCE_DOCTRINE_VERSION = "valence_doctrine_v1"

# ── The 4-way signed vocabulary ─────────────────────────────────────────────
BENEFIC = "benefic"
MALEFIC = "malefic"
MIXED = "mixed"
NEUTRAL = "neutral"

# Edge (relationship) vocabulary — bo_karanajala/_mechanism_valence's existing
# words, extended with an explicit "mixed" for a benefic↔malefic relationship.
HARMONIOUS = "harmonious"
ANTAGONISTIC = "antagonistic"
EDGE_MIXED = "mixed"
EDGE_NEUTRAL = "neutral"

# ── 1. Natural nature (BPHS Ch.3 svabhāva), signed [-1, +1] ─────────────────
# DR-9 explicit list. Canonical subject codes (PLANET_TO_SUBJECT).
_NATURAL_NATURE: dict[str, float] = {
    "SUN": -0.5,       # mild malefic
    "MAR": -1.0,       # malefic
    "SAT": -1.0,       # malefic
    "RAH_MEAN": -1.0,  # malefic (node)
    "KET_MEAN": -1.0,  # malefic (node)
    "JUP": +1.0,       # benefic
    "VEN": +1.0,       # benefic
    "MOON": +0.5,      # conditional: waxing benefic / waning malefic (refined below)
    "MER": +0.3,       # conditional: benefic unless afflicted (refined below)
}
_NATURAL_CITATION = "BPHS Ch.3 (graha svabhāva) — DR-9 natural-nature grounds."

# ── 2. Functional lordship → signed contribution ────────────────────────────
# Consumed from the stored graha_functional_class_per_ascendant fact (§N.5).
_FUNCTIONAL_SCORE: dict[str, float] = {
    "yogakaraka": +1.5,
    "functional_benefic": +1.0,
    "temporal_benefic": +1.0,
    "functional_malefic": -1.0,
    "temporal_malefic": -1.0,
    "neutral": 0.0,
}
_FUNCTIONAL_CITATION = "BPHS Ch.34 (functional benefic/malefic per lagna) — stored fact, §N.5."

# ── 3. Dignity/state → additive modifier ────────────────────────────────────
_DIGNITY_MOD: dict[str, float] = {
    "exalted": +0.5,
    "moolatrikona": +0.4,
    "own": +0.3,
    "friend": +0.15,
    "neutral": 0.0,
    "enemy": -0.15,
    "debilitated": -0.5,
    "combust": -0.3,
}

# ── 4. Harsh special aspects (BPHS): offsets counted 1-based from the graha's
# own house (7 = standard opposition; these are the EXTRA graha-specific ones). ─
_HARSH_SPECIAL_ASPECTS: dict[str, set[int]] = {
    "MAR": {4, 8},    # Mars's 4th & 8th special aspects
    "SAT": {3, 10},   # Saturn's 3rd & 10th special aspects
}
_NATURAL_BENEFIC_GRAHAS = frozenset({"JUP", "VEN", "MOON", "MER"})

# Houses whose significations a malefic contact more pointedly threatens
# (a valuable target being afflicted): dhana (2/11), kendra (1/4/7/10),
# trikoṇa (1/5/9). Used only as a CONTACT-texture nudge, never to set valence
# from occupancy alone (DR-9).
_SUPPORTIVE_HOUSES = frozenset({1, 2, 4, 5, 7, 9, 10, 11})

# Verdict thresholds.
_MIXED_THRESHOLD = 0.4   # both components must reach this for a genuine MIXED
_SIGN_EPS = 0.10         # net magnitude below this → neutral


# Graha-code normalization moved to `brahmagyan/graha_vocabulary.py` (the
# graha SSoT, ADHIṢṬHĀNA Lane A2) — `norm_graha` is imported back above so
# every existing `valence_doctrine.norm_graha` call site keeps working
# unchanged.

# Node (Rahu/Ketu) exaltation — the estate's L1 dignity computation does not
# assign a dignity to the nodes (they classify "neutral"), but classically the
# nodes DO have exaltation/debilitation signs. Convention used here (BPHS-
# adjacent; schools differ): Rahu exalts in Taurus / debilitates in Scorpio;
# Ketu the reverse. This is what makes "exalted Rahu in the dhana bhāva" a
# genuinely MIXED (dual) reading rather than purely adverse (DR-9 specimen).
_NODE_EXALT_SIGN: dict[str, str] = {"RAH_MEAN": "TAURUS", "KET_MEAN": "SCORPIO"}
_NODE_DEBIL_SIGN: dict[str, str] = {"RAH_MEAN": "SCORPIO", "KET_MEAN": "TAURUS"}


def node_dignity_from_sign(graha: str | None, sign: str | None) -> str | None:
    """Classical node dignity from occupied sign (nodes only) — supplements the
    L1 dignity gap for Rahu/Ketu. Returns 'exalted' | 'debilitated' | None."""
    g = norm_graha(graha)
    s = (sign or "").strip().upper()
    if g not in _NODE_EXALT_SIGN or not s:
        return None
    if s == _NODE_EXALT_SIGN[g]:
        return "exalted"
    if s == _NODE_DEBIL_SIGN[g]:
        return "debilitated"
    return None


@dataclass
class ValenceVerdict:
    """Signed valence verdict. `valence` is the 4-way label; `value_num` the
    signed net; the two *_component fields carry BOTH sides so a partitioned
    serve (DR-9 Part B) can route a mixed signal into the adverse layer on its
    malefic_component regardless of net sign."""
    valence: str
    value_num: float
    benefic_component: float
    malefic_component: float
    is_mixed: bool
    natural_score: float
    functional_score: float | None
    dignity_mod: float
    contact_mod: float
    citation: str
    formula_version: str = VALENCE_DOCTRINE_VERSION
    components: dict = field(default_factory=dict)


def _natural_of(graha: str, moon_waxing: bool | None, mercury_afflicted: bool | None) -> float:
    base = _NATURAL_NATURE.get(graha, 0.0)
    if graha == "MOON" and moon_waxing is not None:
        return +0.5 if moon_waxing else -0.5
    if graha == "MER" and mercury_afflicted is not None:
        return -0.3 if mercury_afflicted else +0.3
    return base


def _contact_modifier(
    graha: str,
    contact_type: str,
    target_house: int | None,
    aspect_offset: int | None,
) -> float:
    """Contact-type texture (DR-9 dimension 4). Occupancy is texturally neutral
    (the graha's nature/functional/dignity carry it); aspects add texture:
    a graha's own harsh special aspect is adverse (more so onto a supportive
    house it threatens), a natural-benefic's drishti softens."""
    if contact_type not in ("aspect", "conjunction", "dispositor"):
        return 0.0  # occupancy / lordship: no aspect texture
    mod = 0.0
    if aspect_offset is not None and aspect_offset in _HARSH_SPECIAL_ASPECTS.get(graha, ()):  # harsh special aspect
        mod -= 0.4
        if target_house in _SUPPORTIVE_HOUSES:
            mod -= 0.2  # harsh aspect afflicting a valuable house
    elif graha in _NATURAL_BENEFIC_GRAHAS and contact_type == "aspect":
        mod += 0.2  # benefic drishti softens
    return mod


def graha_valence(
    graha: str,
    *,
    contact_type: str = "occupancy",
    target_house: int | None = None,
    functional_class: str | None = None,
    dignity_state: str | None = None,
    graha_sign: str | None = None,
    aspect_offset: int | None = None,
    moon_waxing: bool | None = None,
    mercury_afflicted: bool | None = None,
) -> ValenceVerdict:
    """A graha's own signed valence standing in a contact (occupancy / aspect-
    given / lordship). Combines natural × functional × dignity × contact-type
    into signed benefic/malefic COMPONENTS; MIXED when both are non-trivial.

    If `dignity_state` is not supplied but `graha_sign` is, node dignity is
    derived from the sign (Rahu/Ketu only) — the L1 dignity gap that otherwise
    makes exalted Rahu read purely malefic instead of mixed."""
    graha = norm_graha(graha)
    if not dignity_state and graha_sign:
        dignity_state = node_dignity_from_sign(graha, graha_sign)
    natural = _natural_of(graha, moon_waxing, mercury_afflicted)
    functional = _FUNCTIONAL_SCORE.get(functional_class) if functional_class else None
    dignity_mod = _DIGNITY_MOD.get(dignity_state or "", 0.0)
    contact_mod = _contact_modifier(graha, contact_type, target_house, aspect_offset)

    # Signed contributions → split into benefic and malefic components. Each
    # input can only push one way; MIXED is detected when BOTH sides accrue.
    contribs = [natural, dignity_mod, contact_mod]
    if functional is not None:
        contribs.append(functional)
    benefic_component = sum(c for c in contribs if c > 0)
    malefic_component = sum(-c for c in contribs if c < 0)

    net = benefic_component - malefic_component
    is_mixed = min(benefic_component, malefic_component) >= _MIXED_THRESHOLD

    if is_mixed:
        valence = MIXED
    elif net > _SIGN_EPS:
        valence = BENEFIC
    elif net < -_SIGN_EPS:
        valence = MALEFIC
    else:
        valence = NEUTRAL

    citation = (
        f"{_NATURAL_CITATION} {_FUNCTIONAL_CITATION} "
        f"[natural={natural:+.2f} functional={functional if functional is None else f'{functional:+.2f}'} "
        f"dignity={dignity_mod:+.2f} contact={contact_mod:+.2f} → {valence}]"
    )
    return ValenceVerdict(
        valence=valence,
        value_num=round(max(-1.5, min(1.5, net)), 4),
        benefic_component=round(benefic_component, 4),
        malefic_component=round(malefic_component, 4),
        is_mixed=is_mixed,
        natural_score=natural,
        functional_score=functional,
        dignity_mod=dignity_mod,
        contact_mod=contact_mod,
        citation=citation,
        components={
            "natural": natural, "functional": functional,
            "dignity_mod": dignity_mod, "contact_mod": contact_mod,
            "contact_type": contact_type, "target_house": target_house,
        },
    )


def combine_occupant_verdicts(verdicts: list[ValenceVerdict]) -> tuple[str, float]:
    """Combine multiple house occupants' valence verdicts into one house-tenancy
    valence (4-way + signed net). Sums the signed benefic/malefic components
    across occupants; MIXED when both sides stay non-trivial (e.g. a benefic AND
    a malefic tenanting the same house). Empty → neutral."""
    if not verdicts:
        return NEUTRAL, 0.0
    b = sum(v.benefic_component for v in verdicts)
    m = sum(v.malefic_component for v in verdicts)
    net = b - m
    if min(b, m) >= _MIXED_THRESHOLD:
        return MIXED, round(net, 4)
    if net > _SIGN_EPS:
        return BENEFIC, round(net, 4)
    if net < -_SIGN_EPS:
        return MALEFIC, round(net, 4)
    return NEUTRAL, round(net, 4)


def _effective_edge_sign(graha: str, functional_class: str | None,
                         moon_waxing: bool | None = None,
                         mercury_afflicted: bool | None = None) -> float:
    """For a RELATIONSHIP edge, an endpoint's effective sign is NATURAL-nature
    primary, with functional lordship as a minor softener only (DR-9: a
    malefic↔malefic mutual affliction is adverse texture regardless of one
    endpoint's functional-benefic standing for this lagna — e.g. Mars↔Saturn
    reads adverse even though Mars is Aries's lagneśa)."""
    natural = _natural_of(graha, moon_waxing, mercury_afflicted)
    functional = _FUNCTIONAL_SCORE.get(functional_class) if functional_class else 0.0
    # Natural weighted 0.8, functional 0.2 — functional can nudge but never
    # flip a clear natural malefic within a relationship.
    return 0.8 * natural + 0.2 * (functional or 0.0)


def edge_valence(
    graha_a: str,
    graha_b: str,
    *,
    relationship_type: str = "aspect",
    functional_a: str | None = None,
    functional_b: str | None = None,
    moon_waxing_a: bool | None = None,
    moon_waxing_b: bool | None = None,
) -> str:
    """Valence of a relationship between two grahas → {harmonious, antagonistic,
    mixed, neutral} (bo_karanajala edge vocabulary). Structural relationship
    types (lordship/occupancy/yoga_member/bhava_aspect) stay polarity-neutral —
    they describe topology, not benefic/malefic texture."""
    if relationship_type in ("lordship", "occupancy", "yoga_member", "bhava_aspect"):
        return EDGE_NEUTRAL
    sa = _effective_edge_sign(norm_graha(graha_a), functional_a, moon_waxing_a)
    sb = _effective_edge_sign(norm_graha(graha_b), functional_b, moon_waxing_b)
    pos = sa > 0.25 and sb > 0.25
    neg = sa < -0.25 and sb < -0.25
    if pos:
        return HARMONIOUS
    if neg:
        return ANTAGONISTIC
    # One clearly benefic and one clearly malefic → genuine mixed; otherwise
    # (one near-neutral) → neutral.
    if (sa > 0.25 and sb < -0.25) or (sa < -0.25 and sb > 0.25):
        return EDGE_MIXED
    return EDGE_NEUTRAL


def mechanism_valence_from_edges(edge_valences: list[str]) -> str:
    """Combine member-edge valences into a mechanism valence (4-way). A single
    'mixed' edge, or the co-presence of harmonious AND antagonistic edges, makes
    the mechanism MIXED. Replaces bo_yantra_mechanism._mechanism_valence's
    two-way logic (which collapsed a 'mixed' edge to neutral)."""
    vals = set(v for v in edge_valences if v)
    if EDGE_MIXED in vals:
        return MIXED
    harmonious = HARMONIOUS in vals
    antagonistic = ANTAGONISTIC in vals
    if harmonious and antagonistic:
        return MIXED
    if harmonious:
        return BENEFIC
    if antagonistic:
        return MALEFIC
    return NEUTRAL

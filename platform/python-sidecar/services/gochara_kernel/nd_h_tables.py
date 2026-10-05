"""Independent verifier tables for ND-H-20261005 (the eight classes) and the K-B / bereavement-Sun rules of ND-P2.

Written from the ruling text and AM-H / AM-K (decisions/AM-H_AM-K_SPEC_AMENDMENTS_DRAFT) ALONE. It imports nothing from
the builder (`registry`, `evaluator`, `admission`, `rule_registry`) and the builder imports nothing from here: FB-38's
equality test compares the two sides' tables as DATA, and this module's own test compares them with the ruling text
quoted verbatim.

What it states:
  * the three tiers per class (CORE opens a window in P1/P3/P4, DVI counts toward Jupiter/Saturn influence in P4 only,
    SUPPORT is testimony outside H) and what each path may read (`path_houses`);
  * the kāraka roles: K-A (rank only, never admits) and K-B (admission, luminaries only), and the value a record's
    `karaka_agent` factor must carry;
  * the K-B edge licence (which agent, relation and separation make a natal-luminary target a legal edge, 1 degree band);
  * the father frame (`bhavat_bhavam:9`) and the registered-but-unbuilt mother row;
  * the pre-registered 40 percent guard for DVI members.
Nothing here decides an owner point: K-B reaching bereavement (ND-P2 rule 3) is carried as a labelled rule with its
source, so a reader can see which part rests on which ruling.
"""
from __future__ import annotations

import dataclasses

RULING_H = "ND-H-20261005"
RULING_P2 = "ND-P2-20261005"
RULE_VERSION = "1.2.0"
BAND_DEG = 1.0                       # the built 1-degree point band (ND-P2 rule 3 corrects ND-H's "5 degrees")
GAIN_BAND = 0.40                     # the protocol's 40% gain band, FB-41 guard
NINE = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")
PATHS = ("P1", "P2", "P3", "P4")
NODES = frozenset({"rahu", "ketu"})


@dataclasses.dataclass(frozen=True)
class Tier:
    core: frozenset                  # lagna-counted houses (frames already resolved)
    dvi: frozenset
    support: frozenset
    noted: frozenset = frozenset()   # annotation only, no role (foreign_settlement 10)
    frame: str = "lagna"


def frame_house(anchor: int, offset: int) -> int:
    """House (counted from the lagna, 1..12) of the `offset`-th house INCLUSIVELY from the `anchor` house."""
    return (anchor + offset - 2) % 12 + 1


# ── the table (ND-H "Three tiers" table; FB-35) ───────────────────────────────────────────────────────────────────
TIERS: dict[str, Tier] = {
    "achievement_recognition": Tier(frozenset({10}), frozenset({11}), frozenset({5, 1, 9})),
    "business_launch": Tier(frozenset({7, 10}), frozenset(), frozenset({6})),
    "financial_deception": Tier(frozenset({2, 12}), frozenset({6}), frozenset({8})),
    "foreign_settlement": Tier(frozenset({12}), frozenset({4}), frozenset({9, 7}), noted=frozenset({10})),
    "parental_event": Tier(frozenset({frame_house(9, 1), frame_house(9, 6)}), frozenset(),
                           frozenset({frame_house(9, 8), frame_house(9, 12)}), frame="bhavat_bhavam:9"),
    "property_acquisition": Tier(frozenset({4}), frozenset({11}), frozenset({2})),
    "psychological_arc": Tier(frozenset({4}), frozenset(), frozenset({5, 8})),
    "spiritual_turn": Tier(frozenset({9, 5}), frozenset(), frozenset({12})),
}
EIGHT = frozenset(TIERS)
# The registered-but-UNBUILT mother row (ND-H item 5): anchor the 4th, offsets {1, 6}; state `unsupported` until a
# per-person selector exists; a mother-tagged event must fail to resolve, never resolve as father.
MOTHER_ROW = {"event_class": "parental_event", "person": "mother", "anchor": 4, "offsets": (1, 6),
              "lagna_core": (frame_house(4, 1), frame_house(4, 6)), "state": "unsupported", "karakas": ("moon",)}

# ── kārakas ───────────────────────────────────────────────────────────────────────────────────────────────────────
KARAKA_A: dict[str, frozenset] = {                    # rank factor `karaka_agent`; never admits, excludes or zeroes
    "achievement_recognition": frozenset({"sun", "jupiter"}),
    "business_launch": frozenset({"mercury"}),
    "financial_deception": frozenset({"rahu"}),       # Saturn is NOT a kāraka here (UK PG130 is the liar's trait)
    "foreign_settlement": frozenset({"rahu"}),        # Saturn excluded
    "parental_event": frozenset({"sun"}),
    "property_acquisition": frozenset({"mars"}),
    "psychological_arc": frozenset(),                 # Moon is K-B only
    "spiritual_turn": frozenset({"jupiter", "ketu"}),
}
KARAKA_B_LUMINARY: dict[str, str] = {                 # admission: the natal luminary as a target
    "parental_event": "sun",                          # ND-H: natal Sun for the father
    "psychological_arc": "moon",                      # ND-H: natal Moon
    "bereavement": "sun",                             # ND-P2 rule 3: father-specific bereavement, derived under the ruling
}
KB_SOURCE = {"parental_event": RULING_H, "psychological_arc": RULING_H, "bereavement": RULING_P2}
# K-B agents: Jupiter and Saturn by conjunction or aspect, Rahu and Ketu by conjunction; fast agents never.
KB_RELATIONS: dict[str, frozenset] = {
    "jupiter": frozenset({"conjunction", "aspect"}), "saturn": frozenset({"conjunction", "aspect"}),
    "rahu": frozenset({"conjunction"}), "ketu": frozenset({"conjunction"}),
}
P4_KB_AGENTS = frozenset({"jupiter", "saturn"})       # P4's infl() is Jupiter and Saturn only
# Saturn is not a scored spiritual kāraka: it annotates (testimony) contacts to the 12th SUPPORT member ONLY.
SATURN_TESTIMONY = {"spiritual_turn": frozenset({12})}
AFFECTED_PERSON = {"parental_event": "father"}        # P2 emits NO parental_event row (the native's Moon never evidences the parent)
P2_EMITS_NO_ROW = frozenset({"parental_event", "psychological_arc"})


# ── what each path may read ───────────────────────────────────────────────────────────────────────────────────────
def path_houses(event_class: str, path: str) -> frozenset:
    """Houses that ADMIT in `path` for a class of the eight: CORE for P1 and P3; CORE plus DVI for P4's influence
    reading (a DVI member counts toward infl(Jupiter)/infl(Saturn) in P4 ONLY). SUPPORT never admits anywhere."""
    t = TIERS[event_class]
    if path in ("P1", "P3"):
        return t.core
    if path == "P4":
        return t.core | t.dvi
    raise ValueError(f"no house reading for path {path!r}")


def admits(event_class: str, path: str, house: int) -> bool:
    return house in path_houses(event_class, path)


def is_testimony_house(event_class: str, house: int) -> bool:
    return house in TIERS[event_class].support


def carried_excluded(event_class: str, selected_rule_version: str) -> bool:
    """ST-H-UNKNOWN: an H-unknown class stays carried EXCLUDED (P1/P3/P4 `inputs_unavailable`) until it is selected at
    1.2.0; at 1.2.0 it is not excluded; a class outside the eight was never H-unknown."""
    return event_class in EIGHT and selected_rule_version != RULE_VERSION


# ── K-A rank value ────────────────────────────────────────────────────────────────────────────────────────────────
def karaka_agent_value(event_class: str, agent: str) -> str | None:
    """The `karaka_agent` rank value a TRANSIT record of `agent` must carry for `event_class`: 'karaka' or 'non_karaka';
    None for a class with no kāraka table (the factor does not exist there)."""
    if event_class not in KARAKA_A:
        return None
    return "karaka" if agent in KARAKA_A[event_class] else "non_karaka"


# ── K-B edge licence ──────────────────────────────────────────────────────────────────────────────────────────────
def kb_edge_licensed(event_class: str, path: str, agent: str, relation: str, separation_deg: float,
                     target: str) -> bool:
    """True iff a transit edge from `agent` to the natal `target` luminary is a LEGAL K-B edge for `event_class`:
    the class has a luminary kāraka and `target` is that luminary; path is P3 or P4; the agent/relation pair is in the
    K-B table (nodes: conjunction only; fast agents never); in P4 only Jupiter/Saturn; and the separation is within the
    1-degree band (inclusive)."""
    lum = KARAKA_B_LUMINARY.get(event_class)
    if lum is None or target != lum:
        return False
    if path not in ("P3", "P4"):
        return False
    if relation not in KB_RELATIONS.get(agent, frozenset()):
        return False
    if path == "P4" and agent not in P4_KB_AGENTS:
        return False
    return 0.0 <= separation_deg <= BAND_DEG


def kb_edge_set(event_class: str) -> frozenset:
    """Every (path, agent, relation) the licence admits for the class — the table the verifier compares with the stored
    K-B rows (a stored edge outside it, or a licensed one missing, is refused by name)."""
    if event_class not in KARAKA_B_LUMINARY:
        return frozenset()
    out = set()
    for agent, rels in KB_RELATIONS.items():
        for rel in rels:
            out.add(("P3", agent, rel))
            if agent in P4_KB_AGENTS:
                out.add(("P4", agent, rel))
    return frozenset(out)


def saturn_testimony(event_class: str, house: int) -> bool:
    return house in SATURN_TESTIMONY.get(event_class, frozenset())


# ── resolution of the affected person ─────────────────────────────────────────────────────────────────────────────
class PersonUnresolved(ValueError):
    pass


def resolve_person(event_class: str, person: str | None) -> str:
    """`parental_event` resolves to the father only; a mother-tagged event fails to resolve (`unsupported`) and is never
    read as the father; an unknown tag is refused."""
    if event_class != "parental_event":
        raise PersonUnresolved(f"{event_class} has no person selector")
    if person in (None, "father"):
        return "father"
    if person == "mother":
        raise PersonUnresolved("unsupported: the mother row is registered and unbuilt")
    raise PersonUnresolved(f"unknown_person: {person!r}")


# ── the 40 percent guard (FB-41) ──────────────────────────────────────────────────────────────────────────────────
def dvi_reverts_to_support(event_class: str, p4_alone_with_dvi_share: float) -> bool:
    """A class whose P4-ALONE admitted-day share (DVI members counted) exceeds the 40% gain band reverts its DVI
    member(s) to SUPPORT in the NEXT generation. False for a class with no DVI member (nothing to revert)."""
    t = TIERS.get(event_class)
    return bool(t and t.dvi) and p4_alone_with_dvi_share > GAIN_BAND

"""Rule Book engine (packet E1) — versioned constants.

Everything here is doctrine or convention the compiler reads; nothing here is
a chart value. Every classical set carries its citation (bank passage ids
only; quote text never enters git, ENGINE_PLAN v0.2 §1 / M5).

Sources of truth that are deliberately NOT used:
- ``reference_houses`` (L0) for bhāva-group membership: panaphara/apoklima are
  incomplete there (E0 hazard 7, cockpit DF-02). Membership comes from
  ``BHAVA_GROUPS`` below, cited to BPHS.
- ``reference_planets.natural_benefic`` (L0): unconditional for the Moon and
  Mercury (E0 hazard 8, cockpit DF-01). Class membership comes from
  ``GRAHA_CLASS_TABLE`` below.
- ``services/gochara_rules/*``: wrapper-local constants (E0 hazards 1–2).
  Nothing is imported from that package; ``ashtakavarga.py`` in particular is
  never imported or copied (ENGINE_PLAN v0.2 §2.2).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

AST_VERSION = "rulebook-ast-v1.0"
COMPILER_VERSION = "rulebook-compiler-v1.0"
SUPPORTED_SCHEMA_VERSIONS = ("rule-card-v1", "rule-card-v1.1")

DATA_DIR = Path(__file__).resolve().parent / "data"

# ── grahas ──────────────────────────────────────────────────────────────────
GRAHAS = ("surya", "chandra", "mangala", "budha", "guru", "shukra", "shani", "rahu", "ketu")
NODES = frozenset({"rahu", "ketu"})

# Card graha → chart_facts subject (E0 §1 subject codes). L1 natal nodes are MEAN.
CF_SUBJECT = MappingProxyType(
    {
        "surya": "SUN",
        "chandra": "MOON",
        "mangala": "MAR",
        "budha": "MER",
        "guru": "JUP",
        "shukra": "VEN",
        "shani": "SAT",
        "rahu": "RAH_MEAN",
        "ketu": "KET_MEAN",
    }
)
# Card graha → L0 body name (bg_sky_calendar.primary_body / chart_dashas.lord_graha).
L0_BODY = MappingProxyType(
    {
        "surya": "Sun",
        "chandra": "Moon",
        "mangala": "Mars",
        "budha": "Mercury",
        "guru": "Jupiter",
        "shukra": "Venus",
        "shani": "Saturn",
        "rahu": "Rahu",
        "ketu": "Ketu",
    }
)

# ── node model (E0 §3, coordinator input b) ─────────────────────────────────
# L1 natal facts use the MEAN node; every L0 transit source uses the TRUE node.
NODE_MODEL_BY_PLANE = MappingProxyType(
    {
        "natal": "mean",
        "dasha": "mean",  # daśā-lord predicates read the lord's L1 natal facts
        "transit": "true",
    }
)

# ── planes ──────────────────────────────────────────────────────────────────
CATEGORIES = ("natal_promise", "dasha", "transit")
POLARITIES = ("promotive", "obstructive")
PROVENANCES = ("verse_cited", "commentarial_practice")

# role → the plane its values come from
ROLE_PLANE = MappingProxyType(
    {
        "transiting_graha": "transit",
        "natal_graha": "natal",
        "bhava_lord": "natal",
        "bhava": "natal",
        "karaka": "natal",
        "dasha_lord": "dasha",
        "antardasha_lord": "dasha",
        "graha_class": "natal",
        "lagna": "natal",
        "moon_sign": "natal",
        "ashtakavarga_bav": "natal",
        "ashtakavarga_sav": "natal",
    }
)
# roles that must be bound to one graha before a lookup is defined
ROLES_NEEDING_GRAHA = frozenset({"transiting_graha", "natal_graha", "ashtakavarga_bav", "karaka"})

# ── frames (ENGINE_PLAN v0.2 §2.3; E0 §1.3) ─────────────────────────────────
# frame → (frames.py kind it maps onto read-only, reference-sign source)
FRAME_SOURCES = MappingProxyType(
    {
        "janma_lagna": ("lagna", "CF(graha_position, LAGNA, sign)"),
        "chandra_lagna": ("moon", "CF(graha_position, MOON, sign)"),
        "dasha_lord_natal_position": ("dasha_lord:<X>", "DSH(1).lord_graha -> CF(graha_position, <lord>, sign)"),
        "natal_position_of_role": ("graha:<X>", "CF(graha_position, <role graha>, sign)"),
        "bhava_of_role": ("bhavat_bhavam:<n>", "sign of the role's OCCUPIED whole-sign bhava"),
        "sign_of_transit_only": (None, "no count; sign-intrinsic lookup on the transited sign"),
    }
)
FRAMES_V1 = frozenset(FRAME_SOURCES)
FRAMES_DEFERRED = frozenset({"surya_lagna", "navamsa_lagna", "antardasha_lord_natal_position"})
FRAMES_ALL = FRAMES_V1 | FRAMES_DEFERRED
FRAMES_OF_ROLE = frozenset({"natal_position_of_role", "bhava_of_role"})

# category → frames that contradict that plane. sign_of_transit_only is
# sign-intrinsic for transit cards only (F-S3: propose ``sign_intrinsic``).
FRAME_PLANE_CONTRADICTIONS = MappingProxyType(
    {
        "natal_promise": frozenset(
            {"sign_of_transit_only", "dasha_lord_natal_position", "antardasha_lord_natal_position"}
        ),
        "dasha": frozenset({"sign_of_transit_only"}),
        "transit": frozenset(),
    }
)

# ── bhāva groups (DF-02: never from reference_houses) ───────────────────────
# Whole-sign houses counted inclusively in the card's frame.
BHAVA_GROUPS_VERSION = "bhava-groups-v1.0"
BHAVA_GROUPS = MappingProxyType(
    {
        "kendra": {
            "members": (1, 4, 7, 10),
            "citation": ("bphs_pg0101_c01:en:p003",),
            "basis": "BPHS ch.7 (Santhanam): angles are the ascendant, 4th, 7th and 10th",
        },
        "panaphara": {
            "members": (2, 5, 8, 11),
            "citation": ("bphs_pg0101_c01:en:p003",),
            "basis": "BPHS ch.7: 2nd, 5th, 8th, 11th are panapharas (succedents)",
        },
        "apoklima": {
            "members": (3, 6, 9, 12),
            "citation": ("bphs_pg0101_c01:en:p003",),
            "basis": "BPHS ch.7: 3rd, 6th, 9th, 12th are apoklimas (cadents)",
        },
        "trikona": {
            "members": (1, 5, 9),
            "citation": ("bphs_pg0101_c01:en:p003", "bphs_pg0340_c01:en:p012"),
            "basis": "BPHS ch.7 names 5th and 9th as kona; ch.34 states the ascendant is an angle as well as a trine",
        },
        "dusthana": {
            "members": (6, 8, 12),
            "citation": ("bphs_pg0584_c01:en:p005",),
            "basis": "BPHS ch.48: 6th, 8th, 12th are dusthanas",
        },
        "upachaya": {
            "members": (3, 6, 10, 11),
            "citation": ("bphs_pg0101_c01:en:p006",),
            "basis": "BPHS ch.7: 3rd, 6th, 10th, 11th are upachaya",
        },
        "maraka": {
            "members": (2, 7),
            "citation": ("bphs_pg0439_c01:en:p007",),
            "basis": "BPHS ch.44: 2nd and 7th are maraka houses",
        },
    }
)
# Groups whose L0 copy is defective (cockpit DF-02, open). The package set above
# is complete, but while DF-02 is open any card using these groups is
# quarantined so no consumer can silently diverge from the L0 table. Lifting a
# group is a reviewed one-line change after DF-02 closes.
BHAVA_GROUPS_DF02_OPEN = frozenset({"panaphara", "apoklima"})

# ── graha classes (DF-01) ───────────────────────────────────────────────────
GRAHA_CLASS_TABLE_VERSION = "graha-class-v1.0"
# BPHS ch.2 (Santhanam) bphs_pg0026_c01:en:p012–p014: Sun, Saturn, Mars,
# decreasing Moon, Rahu and Ketu are malefics, the rest benefics; Mercury is a
# malefic if he joins a malefic.
GRAHA_CLASS_TABLE = MappingProxyType(
    {
        "natural_benefic": {
            "unconditional": ("guru", "shukra"),
            "conditional": {"chandra": "increasing (waxing) Moon", "budha": "Mercury not joined to a malefic"},
            "sense_pinned": True,
            "citation": ("bphs_pg0026_c01:en:p012", "bphs_pg0026_c01:en:p013", "bphs_pg0026_c01:en:p014"),
        },
        "natural_malefic": {
            "unconditional": ("surya", "mangala", "shani", "rahu", "ketu"),
            "conditional": {"chandra": "decreasing (waning) Moon", "budha": "Mercury joined to a malefic"},
            "sense_pinned": True,
            "citation": ("bphs_pg0026_c01:en:p012", "bphs_pg0026_c01:en:p013", "bphs_pg0026_c01:en:p014"),
        },
        # 'benefic'/'malefic' without 'natural_': natural or functional is not pinned (E0 §1.4).
        "benefic": {"unconditional": (), "conditional": {}, "sense_pinned": False, "citation": ()},
        "malefic": {"unconditional": (), "conditional": {}, "sense_pinned": False, "citation": ()},
    }
)

# ── vedha ───────────────────────────────────────────────────────────────────
# Obstructors whose status is undeclared by every Wave-0 verse and by L0 (E0 §4.1).
# A vedha predicate whose obstructor set is otherwise determinate compiles with
# these as ``undeclared`` members: an occupancy by one of them alone reads
# NOT_ASSESSED (window-level partial NA), never FALSE.
VEDHA_UNDECLARED_OBSTRUCTORS = ("chandra", "rahu", "ketu")

# ── school scopes (Q10, G-S8) ───────────────────────────────────────────────
# Default scopes need an explicit text list. None = the panel has not listed
# the texts yet; an exception in that scope is quarantined, never guessed.
SCHOOL_SCOPE_TEXTS: Mapping[str, Any] = MappingProxyType(
    {
        "parashari": None,
        "jataka_general": None,
        "same_text_only": "card_text",
    }
)
NON_DEFAULT_SCOPES = frozenset({"nadi", "kerala", "tajaka"})

EXCEPTION_EFFECTS = ("cancels", "reduces", "reverses_polarity", "delays")
NOTE_ONLY_EFFECTS = frozenset({"reduces", "delays"})

# ── lexical detectors (card-supplied words only; never a value) ─────────────
MEAN_TERMS_RE = r"\b(mean|madhya|madhyama)\b"
TRUE_NODE_TERMS_RE = r"\b(true\s+(node|rahu|ketu)|sphuta|spashta|spa[sṣ][tṭ]a)\b"
VEDHA_TERMS_RE = r"vedha|vēdha|वेध"
VEDHA_EXEMPTION_RE = r"\b(other\s+than|except|excepting|excluding|save|but\s+not)\b"
VERSE_DISJUNCTION_RE = r"\bor\b|\bvā\b|\bva\b|athav|अथवा|वा"
OBSTRUCTOR_CLASS_RE = r"\b(benefics?|malefics?|certain\s+planets|some\s+planets)\b"
REKHA_TERMS_RE = r"\brekhas?\b"
DOT_TERMS_RE = r"\b(dots?|bindus?)\b"
SELF_DECLARED_BENEFIC_RE = r"\bbenefic\s+(dots?|bindus?|points?)\b"

# ── operand-source matrix (E0 §1.1–§1.2). Descriptors only; nothing resolved. ─
_CF = "chart_facts"
_SKY = "bg_sky_calendar"
_DSH = "chart_dashas"
OPERAND_SOURCES = MappingProxyType(
    {
        ("natal_graha", "retrograde"): {"table": _CF, "key": "graha_position.<SUBJ>.retrograde_flag", "status": "ok"},
        ("natal_graha", "occupies"): {"table": _CF, "key": "graha_position.<SUBJ>.house_d1 | sign", "status": "ok"},
        ("natal_graha", "in_bhava_group"): {
            "table": _CF,
            "key": "graha_position.<SUBJ>.sign + BHAVA_GROUPS",
            "status": "ok",
        },
        ("natal_graha", "exalted"): {
            "table": _CF,
            "key": "graha_special_state_rollup.<SUBJ>.is_exalted",
            "status": "ok",
        },
        ("natal_graha", "debilitated"): {
            "table": _CF,
            "key": "graha_special_state_rollup.<SUBJ>.is_debilitated",
            "status": "ok",
        },
        ("natal_graha", "own_sign"): {
            "table": _CF,
            "key": "graha_dignity_per_varga.D1_<SUBJ>.dignity_state",
            "status": "ok",
        },
        ("natal_graha", "combust"): {
            "table": _CF,
            "key": "graha_position.<SUBJ>.combustion_state",
            "status": "ok",
            "convention_pending": "combustion_fact_A_B_C",
        },
        ("natal_graha", "conjoins"): {
            "table": _CF,
            "key": "graha_position.<A>.sign == graha_position.<B>.sign",
            "status": "ok",
        },
        ("natal_graha", "aspects"): {
            "table": _CF,
            "key": "aspect_parashari_given.<SUBJ>.house_<n>",
            "status": "ok",
            "convention_pending": "aspect_house_reference",
        },
        ("natal_graha", "lord_of"): {
            "table": _CF,
            "key": "lord_in_house_per_varga.D1_H<n>.lord_placement",
            "status": "ok",
        },
        ("bhava_lord", "occupies"): {
            "table": _CF,
            "key": "lord_in_house_per_varga.D1_H<n>.lord_placement",
            "status": "ok",
        },
        ("bhava_lord", "lord_of"): {
            "table": _CF,
            "key": "lord_in_house_per_varga.D1_H<n>.lord_placement",
            "status": "ok",
        },
        ("bhava_lord", "in_bhava_group"): {
            "table": _CF,
            "key": "lord_in_house_per_varga.D1_H<n> + BHAVA_GROUPS",
            "status": "ok",
        },
        ("karaka", "occupies"): {
            "table": _CF,
            "key": "karaka_chara_position.<KARAKA>.house_d1 | sign",
            "status": "non_unique",
            "uniqueness": "2 rows per subject (formula_id 7- vs 8-karaka school unpinned)",
        },
        ("dasha_lord", "is_dasha_lord"): {"table": _DSH, "key": "DSH(1).lord_graha", "status": "ok"},
        ("antardasha_lord", "is_antardasha_lord"): {"table": _DSH, "key": "DSH(2).lord_graha", "status": "ok"},
        ("dasha_lord", "occupies"): {
            "table": _CF,
            "key": "DSH(1).lord_graha -> graha_position.<lord>.house_d1 | sign",
            "status": "ok",
        },
        ("antardasha_lord", "occupies"): {
            "table": _CF,
            "key": "DSH(2).lord_graha -> graha_position.<lord>.house_d1 | sign",
            "status": "ok",
        },
        ("dasha_lord", "in_bhava_group"): {"table": _CF, "key": "DSH(1) lord sign + BHAVA_GROUPS", "status": "ok"},
        ("antardasha_lord", "in_bhava_group"): {"table": _CF, "key": "DSH(2) lord sign + BHAVA_GROUPS", "status": "ok"},
        ("dasha_lord", "retrograde"): {
            "table": _CF,
            "key": "DSH(1) lord -> graha_position.<lord>.retrograde_flag",
            "status": "ok",
            "convention_pending": "node_retrograde_under_mean_model",
        },
        ("antardasha_lord", "retrograde"): {
            "table": _CF,
            "key": "DSH(2) lord -> graha_position.<lord>.retrograde_flag",
            "status": "ok",
            "convention_pending": "node_retrograde_under_mean_model",
        },
        ("dasha_lord", "debilitated"): {
            "table": _CF,
            "key": "DSH(1) lord -> graha_special_state_rollup.<lord>.is_debilitated",
            "status": "ok",
            "convention_pending": "node_dignity_source",
        },
        ("antardasha_lord", "debilitated"): {
            "table": _CF,
            "key": "DSH(2) lord -> graha_special_state_rollup.<lord>.is_debilitated",
            "status": "ok",
            "convention_pending": "node_dignity_source",
        },
        ("dasha_lord", "exalted"): {
            "table": _CF,
            "key": "DSH(1) lord -> graha_special_state_rollup.<lord>.is_exalted",
            "status": "ok",
            "convention_pending": "node_dignity_source",
        },
        ("antardasha_lord", "exalted"): {
            "table": _CF,
            "key": "DSH(2) lord -> graha_special_state_rollup.<lord>.is_exalted",
            "status": "ok",
            "convention_pending": "node_dignity_source",
        },
        ("transiting_graha", "transits"): {
            "table": _SKY,
            "key": "ingress intervals (primary_body, event_jd)",
            "status": "ok",
        },
        ("transiting_graha", "occupies"): {
            "table": _SKY,
            "key": "ingress intervals (primary_body, event_jd)",
            "status": "ok",
        },
        ("transiting_graha", "in_bhava_group"): {
            "table": _SKY,
            "key": "ingress intervals + BHAVA_GROUPS",
            "status": "ok",
        },
        ("transiting_graha", "vedha_by"): {
            "table": _SKY,
            "key": "obstructor ingress intervals in the vedha house",
            "status": "ok",
        },
        ("transiting_graha", "retrograde"): {
            "table": _SKY,
            "key": "station rows (detail.station_type)",
            "status": "ok",
        },
        ("transiting_graha", "combust"): {
            "table": None,
            "key": "combustion entry/exit instants",
            "status": "gap",
            "gap": "no L0 combustion interval source (E0 §2; E0b)",
        },
        ("ashtakavarga_bav", "bindus"): {
            "table": _CF,
            "key": "ashtakavarga_bindu_sign.<G>-SIGN_<n>.bindus",
            "status": "ok",
        },
        ("ashtakavarga_sav", "bindus"): {
            "table": _CF,
            "key": "ashtakavarga_bindu_sign.SARVA-SIGN_<n>.bindus",
            "status": "ok",
        },
    }
)

# Relations that place a graha somewhere (used by target and P4 analysis).
POSITIONAL_RELATIONS = frozenset({"occupies", "transits", "aspects", "in_bhava_group"})


def _load_json(name: str) -> Mapping[str, Any]:
    with (DATA_DIR / name).open(encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def licence_allowlist() -> Mapping[str, Any]:
    """Public-domain edition allowlist (data file; reviewed by hand)."""
    return _load_json("licence_allowlist.json")


@lru_cache(maxsize=None)
def bindu_conventions() -> Mapping[str, Any]:
    """Per-text rekhā/bindu convention map (data file)."""
    return _load_json("bindu_conventions.json")

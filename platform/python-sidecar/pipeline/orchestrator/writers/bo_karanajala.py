"""
bo_karanajala — CGM Edges + Contradictions (L2 Bodha)
======================================================
Reads bodha_msr_signals + bodha_cgm_nodes → writes:
  - bodha_cgm_edges  (directed edges between graph nodes)
  - bodha_contradictions  (yoga-vs-dosha / tradition-conflict pairs)

Edge types created:
  'aspect'       — Parashari aspect from one graha node to another
  'conjunction'  — tight conjunction within orb
  'dispositor'   — graha → its dispositor graha
  'yoga_domain'  — yoga signal → domain node (positive)
  'dosha_domain' — dosha signal → domain node (antagonist)
  'sade_sati'    — Saturn → Moon / house 12 (transit-period)
  'argala'       — B intervenes on A (BPHS Ch. 28: 2nd/4th/11th from A)

Contradiction detection:
  - A yoga signal and a dosha signal share the same domain AND same graha
    → 'yoga_vs_dosha' contradiction pair

Cross-subsystem columns (CONTRACT-4 with A7/bo_anveshana):
  - is_cross_subsystem: True when from/to nodes span different traditions
  - subsystem_from / subsystem_to: signal_tradition of each endpoint

LIGHT writer.
"""
from __future__ import annotations

import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from brahmagyan import valence_doctrine as _vd
from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS, CANONICAL_DOMAINS_SORTED
from . import WriterBase, ContextSpec, WriterResult, register
from pipeline.orchestrator.writers.bo_bimba import (
    _SUBJECT_TO_GRAHA as _GRAHA_SUBJECT_MAP,
    yoga_node_subject as _yoga_node_subject,
    _YOGA_NODE_CLASSES,
)
# WP-2.3-temporal: reuse the merged WP-2.1 deterministic dasha→date resolver to
# populate active_dasha_periods_jsonb on graha-resting CGM edges. We CONSUME this
# helper (birth-forward, ayanamsha-consistent); we never hand-roll date math and
# never modify the helper (§N.5 — L1 chart_dashas is the date authority).
from services.ka_temporal import (
    load_dasha_timeline,
    resolve_activation_windows,
    resolve_birth_date,
    normalize_graha,
)

logger = logging.getLogger(__name__)

ENGINE_VERSION   = "bo_karanajala_v1.0"
SNAPSHOT_TYPE    = "static_natal"
GRAPH_LIB        = "internal"
GRAPH_LIB_VER    = "1.0"
CANONICAL_AYAS   = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

_EDGE_INSERT = """
INSERT INTO bodha_cgm_edges (
  edge_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  edge_type, from_node_id, to_node_id, direction, computed_strength, weight_formula_version,
  edge_properties_jsonb, relationship_class, semantic_path_class,
  active_duration_class, active_dasha_periods_jsonb,
  underlying_msr_signal_ids_array, constituent_fact_ids_array, cross_system_consensus_count,
  cancelled_flag, cancelled_by_jsonb, cross_ayanamsha_edge_stability_score,
  present_in_traditions_array, edge_betweenness, in_shortest_path_count,
  graph_compute_library, graph_compute_library_version,
  is_cross_subsystem, subsystem_from, subsystem_to,
  valence, relationship_basis, affected_domains,
  constituent_ga_vichara_ids_array,
  verification_pass_status, citation_ref, citation_human, computed_at, engine_version
) VALUES (
  %(edge_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(edge_type)s, %(from_node_id)s, %(to_node_id)s, %(direction)s,
  %(computed_strength)s, %(weight_formula_version)s,
  %(edge_properties_jsonb)s::jsonb, %(relationship_class)s, %(semantic_path_class)s,
  %(active_duration_class)s, %(active_dasha_periods_jsonb)s::jsonb,
  %(underlying_msr_signal_ids_array)s, %(constituent_fact_ids_array)s, %(cross_system_consensus_count)s,
  %(cancelled_flag)s, NULL, NULL,
  %(present_in_traditions_array)s, NULL, NULL,
  %(graph_compute_library)s, %(graph_compute_library_version)s,
  %(is_cross_subsystem)s, %(subsystem_from)s, %(subsystem_to)s,
  %(valence)s, %(relationship_basis)s, %(affected_domains)s,
  %(constituent_ga_vichara_ids_array)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s,
  %(computed_at)s, %(engine_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, build_id, snapshot_type, edge_type, from_node_id, to_node_id)
DO NOTHING
"""

_CONTRADICTION_INSERT = """
INSERT INTO bodha_contradictions (
  contradiction_id, chart_id, ayanamsha_id, build_id,
  signal_a_id, signal_b_id, tension_basis_jsonb, tension_class,
  domains_affected_array, combined_salience, resolution_hint_jsonb,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(contradiction_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
  %(signal_a_id)s, %(signal_b_id)s, %(tension_basis_jsonb)s::jsonb, %(tension_class)s,
  %(domains_affected_array)s, %(combined_salience)s, NULL,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
ON CONFLICT (chart_id, ayanamsha_id, build_id, signal_a_id, signal_b_id) DO NOTHING
"""

_BATCH_SIZE = 50

# ── Typed edge helpers (BA-P3B migration 394) ────────────────────────────────

_EDGE_TYPE_VALENCE: dict[str, str] = {
    "yoga_domain":  "harmonious",
    "dosha_domain": "antagonistic",
    "aspect":       "harmonious",
    "conjunction":  "harmonious",
    "dispositor":   "harmonious",
    "argala":       "harmonious",   # virodha-argala edges override below
    "sade_sati":    "antagonistic",
    # WP-2.3 graha↔bhava + yoga membership: structural, polarity-neutral
    "lordship":     "neutral",
    "occupancy":    "neutral",
    "bhava_aspect": "neutral",
    "yoga_member":  "neutral",
}

_EDGE_TYPE_BASIS: dict[str, str] = {
    "yoga_domain":  "yoga_activation",
    "dosha_domain": "dosha_impairment",
    "aspect":       "parashari_aspect",
    "conjunction":  "planetary_conjunction",
    "dispositor":   "sign_lordship",
    "argala":       "argala_intervention",
    "sade_sati":    "sade_sati_transit",
    # WP-2.3
    "lordship":     "bhava_lordship",
    "occupancy":    "graha_bhava_occupancy",
    "bhava_aspect": "parashari_bhava_aspect",
    "yoga_member":  "configuration_membership",
}


# DR-9 / VAL-ROOT: texture-bearing graha↔graha edge types whose valence must be
# derived from the ENDPOINT GRAHAS' natures, NOT the edge type alone. The prior
# _EDGE_TYPE_VALENCE mapped every one of these to "harmonious" → 121/121
# mechanisms on 482012f1 read "benefic" (incl. Mars↔Saturn). yoga_domain/
# dosha_domain stay type-keyed (they ARE domain-semantic: a yoga edge is
# harmonious, a dosha edge antagonistic, by definition); structural edges stay
# neutral.
_GRAHA_TEXTURE_EDGE_TYPES = frozenset({"aspect", "conjunction", "dispositor", "argala"})


def _typed_edge_fields(
    edge_type: str,
    domains: list[str] | None = None,
    relationship_class: str | None = None,
    graha_a: str | None = None,
    graha_b: str | None = None,
) -> dict:
    """Return valence, relationship_basis, affected_domains for an edge.

    DR-9: for a texture-bearing graha↔graha edge (aspect/conjunction/dispositor/
    argala) with BOTH endpoint grahas known, valence is computed from the two
    grahas' natures via the shared valence doctrine (edge_valence → the
    harmonious/antagonistic/mixed/neutral vocabulary). Falls back to the legacy
    type-keyed map only for domain-semantic edges (yoga/dosha), structural edges,
    or when an endpoint graha is unavailable (honest neutral, never a guess)."""
    basis = _EDGE_TYPE_BASIS.get(edge_type, relationship_class or edge_type)
    if edge_type == "argala" and relationship_class == "argala_virodha":
        # virodha-argala is definitionally obstructive regardless of grahas.
        valence = "antagonistic"
    elif edge_type in _GRAHA_TEXTURE_EDGE_TYPES and graha_a and graha_b:
        valence = _vd.edge_valence(graha_a, graha_b, relationship_type=edge_type)
    else:
        valence = _EDGE_TYPE_VALENCE.get(edge_type, "neutral")
    return {
        "valence":            valence,
        "relationship_basis": basis,
        "affected_domains":   domains or [],
    }


# ── DR-7 (DIS.020) — edge_strength_v1 formula (D-2 Lane V-4, CR-86) ──────────
# edge_strength = base_relation_weight × valence_factor × ratification_factor
#                 × consistency_weight, clamped [0.1, 2.0].
# Retires the CR-86 hardcoded literals: the per-edge-type constants that used
# to be the FINAL computed_strength (argala 0.5, dispositor 0.6, lordship/
# occupancy/bhava_aspect 0.5-0.7, yoga_member 0.5) are now only the
# base_relation_weight TERM; the three multipliers are real, chart-specific
# values read from ga_vichara's shipped valence pass (chart_vichara) — never
# invented here (§N.5: V-4 references L1/L2 values, it never restates them).
EDGE_STRENGTH_FORMULA_VERSION = "edge_strength_v1"

_VALENCE_FACTOR_BY_LABEL: dict[str, float] = {
    "strong_benefic": 1.25, "strong_malefic": 1.25,
    "benefic": 1.10, "malefic": 1.10,
    "mixed": 1.15,   # DR-9: a mixed valence is a real tension, moderately strong
    "neutral": 1.00,
}

_EDGE_STRENGTH_CLAMP = (0.1, 2.0)


def _clamp_edge_strength(v: float) -> float:
    lo, hi = _EDGE_STRENGTH_CLAMP
    return max(lo, min(hi, v))


_GRAHA_TO_VICHARA_CODE: dict[str, str] = {v: k for k, v in _GRAHA_SUBJECT_MAP.items()}


def _vichara_code(graha_title: str) -> str | None:
    """Title-case graha ('Mars') -> ga_vichara's subject/actor code ('MAR')."""
    return _GRAHA_TO_VICHARA_CODE.get(graha_title)


def _fetch_vichara_valence_by_actor_house(conn, chart_id: str, aya: str) -> dict:
    """(actor_code, house) -> (value_text, chart_vichara.id) for varga='D1'
    valence_pass rows. Chart-vichara unavailable degrades to {} — every caller
    then falls back to valence_factor=1.0 (neutral), honestly, never a guess."""
    try:
        rows = conn.execute(
            """SELECT id, actor, target, value_text FROM chart_vichara
               WHERE chart_id = %s AND ayanamsha_id = %s
                 AND vichara_family = 'valence_pass' AND varga = 'D1'""",
            [chart_id, aya],
        ).fetchall()
    except Exception as exc:
        logger.warning("[bo_karanajala] chart_vichara valence_pass unavailable (%s); "
                        "valence_factor=1.0 for every edge this build", exc)
        return {}
    out: dict = {}
    for r in rows:
        rid, actor, target, val = (r["id"], r["actor"], r["target"], r["value_text"]) \
            if isinstance(r, dict) else (r[0], r[1], r[2], r[3])
        if not actor or not target:
            continue
        try:
            house = int(str(target).rsplit("_HOUSE_", 1)[-1])
        except (ValueError, IndexError):
            continue
        out[(str(actor), house)] = (str(val or "neutral"), str(rid))
    return out


def _fetch_vichara_consistency_by_subject(conn, chart_id: str, aya: str) -> dict:
    """subject_code -> (varga_consistency 0..1, chart_vichara.id)."""
    try:
        rows = conn.execute(
            """SELECT id, subject, value_num FROM chart_vichara
               WHERE chart_id = %s AND ayanamsha_id = %s AND vichara_family = 'varga_consistency'""",
            [chart_id, aya],
        ).fetchall()
    except Exception as exc:
        logger.warning("[bo_karanajala] chart_vichara varga_consistency unavailable (%s); "
                        "consistency_weight=1.0 for every edge this build", exc)
        return {}
    out: dict = {}
    for r in rows:
        rid, subj, val = (r["id"], r["subject"], r["value_num"]) if isinstance(r, dict) else (r[0], r[1], r[2])
        if subj is None or val is None:
            continue
        out[str(subj)] = (float(val), str(rid))
    return out


def _fetch_vichara_ratification_by_subject_domain(conn, chart_id: str, aya: str) -> dict:
    """(subject_code, domain) -> (ratification_factor [0.6,1.4], chart_vichara.id)."""
    try:
        rows = conn.execute(
            """SELECT id, subject, domain, ratification_factor FROM chart_vichara
               WHERE chart_id = %s AND ayanamsha_id = %s AND vichara_family = 'varga_ratification'""",
            [chart_id, aya],
        ).fetchall()
    except Exception as exc:
        logger.warning("[bo_karanajala] chart_vichara varga_ratification unavailable (%s); "
                        "ratification_factor=1.0 for every domain-tagged edge this build", exc)
        return {}
    out: dict = {}
    for r in rows:
        rid, subj, dom, factor = (r["id"], r["subject"], r["domain"], r["ratification_factor"]) \
            if isinstance(r, dict) else (r[0], r[1], r[2], r[3])
        if not subj or not dom or factor is None:
            continue
        out[(str(subj), str(dom))] = (float(factor), str(rid))
    return out


class ViharaLookups:
    """Bundles the three ga_vichara-sourced lookups for one (chart, ayanamsha)
    substep, plus the graha's own D1 occupied-house map (needed to resolve the
    valence_pass key), so _edge_strength_v1() call sites stay one line."""

    __slots__ = ("valence_by_actor_house", "consistency_by_subject",
                 "ratification_by_subject_domain", "occupied_house_by_graha")

    def __init__(self, conn, chart_id: str, aya: str, occupied_house_by_graha: dict):
        self.valence_by_actor_house = _fetch_vichara_valence_by_actor_house(conn, chart_id, aya)
        self.consistency_by_subject = _fetch_vichara_consistency_by_subject(conn, chart_id, aya)
        self.ratification_by_subject_domain = _fetch_vichara_ratification_by_subject_domain(conn, chart_id, aya)
        self.occupied_house_by_graha = occupied_house_by_graha


def _edge_strength_v1(
    base_relation_weight: float,
    graha_title: str | None,
    domains: list | None,
    lookups: "ViharaLookups | None",
) -> tuple:
    """DR-7 (DIS.020): edge_strength = base_relation_weight × valence_factor ×
    ratification_factor × consistency_weight, clamped [0.1, 2.0].

    Returns (strength, constituent_ga_vichara_ids). A graha-less edge (no
    subject to judge) or an unavailable vichara substrate returns
    (clamp(base_relation_weight), []) — honest neutral, never fabricated.
    """
    if not graha_title or lookups is None:
        return _clamp_edge_strength(base_relation_weight), []
    code = _vichara_code(graha_title)
    if not code:
        return _clamp_edge_strength(base_relation_weight), []

    constituents: list = []

    # valence_factor: judged at the graha's own D1 occupied house (a single
    # canonical per-graha value reusable across every edge that graha anchors).
    valence_factor = 1.0
    house = lookups.occupied_house_by_graha.get(graha_title)
    if house is not None:
        rec = lookups.valence_by_actor_house.get((code, house))
        if rec is not None:
            label, vid = rec
            valence_factor = _VALENCE_FACTOR_BY_LABEL.get(label, 1.0)
            constituents.append(vid)

    # ratification_factor: domain-scoped, only when the edge is domain-tagged;
    # takes the max-magnitude-deviation-from-1.0 across the edge's domains
    # (design §11 precedent, mirrored from bo_laksana's _resolve_ratification_factor).
    ratification_factor = 1.0
    if domains:
        best_dev = 0.0
        for dom in domains:
            rec = lookups.ratification_by_subject_domain.get((code, dom))
            if rec is None:
                continue
            factor, vid = rec
            if abs(factor - 1.0) > best_dev:
                best_dev = abs(factor - 1.0)
                ratification_factor = factor
                if vid not in constituents:
                    constituents.append(vid)

    # consistency_weight: 0.75 + 0.25 × varga_consistency.
    consistency_weight = 1.0
    rec = lookups.consistency_by_subject.get(code)
    if rec is not None:
        consistency, vid = rec
        consistency_weight = 0.75 + 0.25 * consistency
        if vid not in constituents:
            constituents.append(vid)

    strength = base_relation_weight * valence_factor * ratification_factor * consistency_weight
    return _clamp_edge_strength(strength), constituents


def _occupied_house_by_graha(occupancy_facts: list) -> dict:
    """{graha_title: house} from bo_karanajala's own occupancy_facts fetch
    (graha -> D1 house it occupies) — the anchor _edge_strength_v1 uses to key
    into ga_vichara's per-(actor,house) valence_pass lookup."""
    return {f["graha"]: f["house"] for f in occupancy_facts}


KNOWN_GRAHAS = {
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
}

# G13/PA-4 (R17): local 7-domain KNOWN_DOMAINS deleted; import canonical 13-domain
# vocabulary from brahmagyan.domain_vocabulary (the L0 SSoT).
# KNOWN_DOMAINS was: {"career", "wealth", "health", "relationship",
#                     "spirituality", "character", "general"}
# Now: CANONICAL_DOMAINS (frozenset of 13). Class 2 contradiction detection
# (domain_promise_vs_denial) operates over all 13 canonical domains.
_KNOWN_DOMAINS = CANONICAL_DOMAINS  # module-local alias; not re-exported

# ── Argala constants (BPHS Ch. 28) ───────────────────────────────────────────
# Argala positions: B creates argala on A when B is in the 2nd, 4th, or 11th house FROM A
ARGALA_POSITIONS = {2, 4, 11}
# Virodha positions: a planet here can cancel argala (BPHS Ch.28: 12th, 3rd, 10th from A)
# 12th cancels 2nd argala, 3rd cancels 4th argala, 10th cancels 11th argala
VIRODHA_POSITIONS = {12, 3, 10}

# Classical Parashari sign lordship: sign_number (1-12) → graha name.
# Rahu and Ketu have no sign lordship in Parashari tradition.
SIGN_LORD: dict[int, str] = {
    1:  "Mars",     # Aries
    2:  "Venus",    # Taurus
    3:  "Mercury",  # Gemini
    4:  "Moon",     # Cancer
    5:  "Sun",      # Leo
    6:  "Mercury",  # Virgo
    7:  "Venus",    # Libra
    8:  "Mars",     # Scorpio
    9:  "Jupiter",  # Sagittarius
    10: "Saturn",   # Capricorn
    11: "Saturn",   # Aquarius
    12: "Jupiter",  # Pisces
}

MALEFIC_GRAHAS  = {"Saturn", "Mars", "Rahu", "Ketu"}
BENEFIC_GRAHAS  = {"Jupiter", "Venus", "Moon", "Mercury"}

_ARGALA_DEFAULT_SIGN_NUMBERS: dict[str, int] = {}  # populated at runtime from DB


def _fetch_node_map(conn, chart_id: str, aya: str) -> dict[tuple[str, str], str]:
    """Returns {(node_type, node_subject): node_id}."""
    rows = conn.execute(
        """SELECT node_id, node_type, node_subject
           FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s""",
        [chart_id, aya, SNAPSHOT_TYPE],
    ).fetchall()
    result: dict[tuple[str, str], str] = {}
    for r in rows:
        if isinstance(r, dict):
            result[(r["node_type"], r["node_subject"])] = str(r["node_id"])
        else:
            result[(str(r[1]), str(r[2]))] = str(r[0])
    return result


def _fetch_signals(conn, chart_id: str, aya: str) -> list[dict]:
    rows = conn.execute(
        """SELECT signal_id, signal_type_class, signal_tradition, configuration_jsonb,
                  domains_affected_array, computed_salience, verification_pass_status,
                  salience_formula_version, signal_type_id
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, aya],
    ).fetchall()
    keys = [
        "signal_id", "signal_type_class", "signal_tradition", "configuration_jsonb",
        "domains_affected_array", "computed_salience", "verification_pass_status",
        "salience_formula_version", "signal_type_id",
    ]
    return [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]


def _fetch_graha_sign_numbers(conn, chart_id: str, aya: str) -> dict[str, int]:
    """Returns {graha_name: sign_number (1-12)} for argala computation.

    Reads from chart_facts (L1 authority). sign_number is 1-based (Aries=1 … Pisces=12).

    Correct L1 schema (ga_positions_writer):
      fact_category = 'graha_sign_attributes'
      fact_key      = 'sign_num'
      fact_value_num (float, e.g. 1.0 for Aries)
      fact_subject  = UPPER_SNAKE (SUN, MOON, MAR, …) → mapped via _GRAHA_SUBJECT_MAP to match KNOWN_GRAHAS
    """
    rows = conn.execute(
        """SELECT fact_subject, fact_value_num
           FROM chart_facts
           WHERE chart_id = %s
             AND ayanamsha_id = %s
             AND fact_category = 'graha_sign_attributes'
             AND fact_key = 'sign_num'""",
        [chart_id, aya],
    ).fetchall()
    result: dict[str, int] = {}
    for r in rows:
        if isinstance(r, dict):
            subject = r["fact_subject"]
            val     = r["fact_value_num"]
        else:
            subject = str(r[0])
            val     = r[1]
        try:
            graha = _GRAHA_SUBJECT_MAP.get(subject.upper())
            if not graha:
                continue
            result[graha] = int(float(val))
        except (ValueError, TypeError):
            pass
    return result


def _house_of_b_from_a(sign_a: int, sign_b: int) -> int:
    """1-based house of B counted from A (A = house 1).

    Example: A=Aries(1), B=Taurus(2) → house 2.
    """
    return ((sign_b - sign_a) % 12) + 1


def _build_argala_edges(
    chart_id: str, aya: str, build_id: str,
    graha_signs: dict[str, int], node_map: dict[tuple[str, str], str], now: str,
    lookups: "ViharaLookups | None" = None,
) -> list[dict]:
    """Build argala edges per BPHS Ch. 28.

    For each pair (A, B) of grahas:
      - Compute house of B from A.
      - If that house is in ARGALA_POSITIONS → B creates argala on A.
      - Determine if virodha-argala (B is malefic) vs. benefic argala.
      - Check virodha cancellation: if B is malefic, check if there is a
        planet in the corresponding virodha position; if so, mark cancelled.
    """
    edges: list[dict] = []
    grahas = [g for g in graha_signs if g in KNOWN_GRAHAS]

    # Map: virodha_position_from_a → grahas occupying that position
    # Built once per A to check cancellation
    for graha_a in grahas:
        sign_a = graha_signs[graha_a]
        node_a = node_map.get(("graha", graha_a))
        if not node_a:
            continue

        # For virodha cancellation: collect planets at virodha positions from A
        virodha_occupied: set[int] = set()
        for graha_x in grahas:
            if graha_x == graha_a:
                continue
            h = _house_of_b_from_a(sign_a, graha_signs[graha_x])
            if h in VIRODHA_POSITIONS:
                virodha_occupied.add(h)

        for graha_b in grahas:
            if graha_b == graha_a:
                continue
            sign_b = graha_signs[graha_b]
            node_b = node_map.get(("graha", graha_b))
            if not node_b:
                continue

            house_b_from_a = _house_of_b_from_a(sign_a, sign_b)
            if house_b_from_a not in ARGALA_POSITIONS:
                continue

            # Determine argala class
            is_malefic = graha_b in MALEFIC_GRAHAS
            relationship_class = "argala_virodha" if is_malefic else "argala_positive"

            # Virodha cancellation: applies only to malefic (virodha-argala)
            # The virodha position corresponding to each argala position (BPHS Ch.28):
            #   2nd argala cancelled by 12th, 4th by 3rd, 11th by 10th
            ARGALA_TO_VIRODHA = {2: 12, 4: 3, 11: 10}
            cancelled = False
            if is_malefic:
                virodha_h = ARGALA_TO_VIRODHA.get(house_b_from_a)
                # O(1) lookup into the prebuilt virodha_occupied set
                cancelled = virodha_h in virodha_occupied if virodha_h else False

            _strength, _vichara_ids = _edge_strength_v1(0.5, graha_a, None, lookups)
            edges.append({
                "edge_id": str(uuid.uuid4()),
                "chart_id": chart_id,
                "ayanamsha_id": aya,
                "build_id": build_id,
                "snapshot_type": SNAPSHOT_TYPE,
                "edge_type": "argala",
                "from_node_id": node_b,   # B is the argala-karaka (intervener)
                "to_node_id": node_a,     # A is the argala-subject
                "direction": "directed",
                "computed_strength": _strength,
                "weight_formula_version": EDGE_STRENGTH_FORMULA_VERSION,
                "constituent_ga_vichara_ids_array": _vichara_ids,
                "edge_properties_jsonb": json.dumps({
                    "argala_subject": graha_a,
                    "argala_karaka": graha_b,
                    "house_of_karaka_from_subject": house_b_from_a,
                    "argala_position": house_b_from_a,
                }),
                "relationship_class": relationship_class,
                "semantic_path_class": "argala_intervention",
                "active_duration_class": "natal_permanent",
                "active_dasha_periods_jsonb": None,
                "underlying_msr_signal_ids_array": [],
                "cross_system_consensus_count": 1,
                "cancelled_flag": cancelled,
                "present_in_traditions_array": ["parashari"],
                "graph_compute_library": GRAPH_LIB,
                "graph_compute_library_version": GRAPH_LIB_VER,
                "is_cross_subsystem": False,
                "subsystem_from": "parashari",
                "subsystem_to": "parashari",
                **_typed_edge_fields("argala", relationship_class=relationship_class,
                                     graha_a=graha_a, graha_b=graha_b),
                "verification_pass_status": "documented_approximation",
                "citation_ref": "BPHS_Ch28/argala",
                "citation_human": (
                    f"Argala: {graha_b} in {house_b_from_a}th from {graha_a} "
                    f"({'virodha-argala' if is_malefic else 'argala'}"
                    f"{', cancelled' if cancelled else ''})"
                ),
                "computed_at": now,
                "engine_version": ENGINE_VERSION,
            })

    return edges


def _build_dispositor_edges(
    chart_id: str, aya: str, build_id: str,
    graha_signs: dict[str, int], node_map: dict[tuple[str, str], str], now: str,
    lookups: "ViharaLookups | None" = None,
) -> list[dict]:
    """Build dispositor edges: graha → its sign lord.

    For each graha in graha_signs, looks up the lord of its sign via SIGN_LORD.
    Emits edge_type='dispositor' directed from graha to its lord.
    Self-ruling grahas (e.g. Sun in Leo, sign 5) are skipped — no self-loops.
    Rahu/Ketu are included as from_node (they ARE disposed by some graha's sign)
    but are never the lord (SIGN_LORD has no Rahu/Ketu entry).

    The motif detectors in bo_cgm_motifs check:
      str(e.get("edge_type", "")).lower() in ("disposited_by", "dispositor", "sign_lord")
    so edge_type='dispositor' is the operative field — the detectors will fire.
    """
    edges: list[dict] = []
    for graha, sign_num in graha_signs.items():
        if graha not in KNOWN_GRAHAS:
            continue
        lord = SIGN_LORD.get(sign_num)
        if not lord or lord == graha:
            continue  # unknown sign or self-ruling (e.g. Sun in Leo)
        from_node = node_map.get(("graha", graha))
        to_node   = node_map.get(("graha", lord))
        if not from_node or not to_node:
            continue
        _strength, _vichara_ids = _edge_strength_v1(0.6, graha, None, lookups)
        edges.append({
            "edge_id":                         str(uuid.uuid4()),
            "chart_id":                        chart_id,
            "ayanamsha_id":                    aya,
            "build_id":                        build_id,
            "snapshot_type":                   SNAPSHOT_TYPE,
            "edge_type":                       "dispositor",
            "from_node_id":                    from_node,
            "to_node_id":                      to_node,
            "direction":                       "directed",
            "computed_strength":               _strength,
            "weight_formula_version":          EDGE_STRENGTH_FORMULA_VERSION,
            "constituent_ga_vichara_ids_array": _vichara_ids,
            "edge_properties_jsonb":           json.dumps({
                "graha":      graha,
                "sign_num":   sign_num,
                "dispositor": lord,
            }),
            "relationship_class":              "dispositor",
            "semantic_path_class":             "sign_lordship",
            "active_duration_class":           "natal_permanent",
            "active_dasha_periods_jsonb":      None,
            "underlying_msr_signal_ids_array": [],
            "cross_system_consensus_count":    1,
            "cancelled_flag":                  False,
            "present_in_traditions_array":     ["parashari"],
            "graph_compute_library":           GRAPH_LIB,
            "graph_compute_library_version":   GRAPH_LIB_VER,
            "is_cross_subsystem":              False,
            "subsystem_from":                  "parashari",
            "subsystem_to":                    "parashari",
            **_typed_edge_fields("dispositor", graha_a=graha, graha_b=lord),
            # M-22 fix: a single deterministic construction pass (sign-lord
            # table lookup) over already-computed upstream data — real, but
            # not independently cross-checked by a second pass. Demoted to
            # "single_pass" (formulas.py VERIFICATION_RESCALE 0.85 vs 1.00).
            "verification_pass_status":        "single_pass",
            "citation_ref":                    f"parashari/sign_lordship/{graha}",
            "citation_human":                  f"Dispositor: {graha} (sign {sign_num}) → lord {lord}",
            "computed_at":                     now,
            "engine_version":                  ENGINE_VERSION,
        })
    return edges


# ── Temporal overlay (WP-2.3-temporal) ───────────────────────────────────────
# Each graha-resting CGM edge (lordship / occupancy / bhava_aspect / yoga_member)
# is temporally "switched on" during the Vimśottarī daśā/antardaśā periods in
# which its graha is the ruling daśā lord. We source those periods from L1
# `chart_dashas` via the merged WP-2.1 resolver (birth-forward, ayanamsha-
# consistent) — NO hand-rolled date math, NO fabricated windows (B.10 / §N.5).


def _dasha_periods_for_graha(graha, timeline, birth_date) -> list:
    """Vimśottarī MD/AD periods (JSON-ready dicts) during which `graha` is the
    ruling daśā lord, birth-forward, sourced from L1 chart_dashas via the WP-2.1
    resolver. Classical basis: every graha rules exactly one 120-yr-cycle
    mahādaśā (and one antardaśā within each mahādaśā); this overlay marks when
    the edge's structural relationship is temporally live.

    Reuses `resolve_activation_windows` for ALL date handling (matching,
    birth-forward clipping, ISO formatting) — identical to ka_kalasutra's
    consumption. Keeps ONLY real chart_dashas-sourced periods and drops the
    resolver's `lord_only_no_timeline` provenance stub, so a graha with no
    eligible birth-forward period yields an honest [] (never fabricated).
    """
    canon = normalize_graha(graha)
    if not canon:
        return []
    windows = resolve_activation_windows(
        {"constituent_lords": [canon]}, timeline, birth_date=birth_date,
    )
    return [
        p for p in windows.active_dasha_periods
        if isinstance(p, dict) and p.get("source") == "chart_dashas"
    ]


def _build_dasha_periods_by_graha(timeline, birth_date) -> dict:
    """Precompute {graha: active_dasha_periods_list} once per (chart × ayanamsha)
    so each edge builder is a cheap dict lookup. Empty timeline → all []."""
    return {
        g: _dasha_periods_for_graha(g, timeline, birth_date)
        for g in KNOWN_GRAHAS
    }


# ── graha ↔ bhava structural edges (WP-2.3 / LCA-9a-1) ───────────────────────
# The 60 bhava nodes (12 houses × 5 ayanamshas) were orphaned — 0 edges. These
# three builders wire every graha into the bhava lattice, each edge citing the
# resolving L1 chart_facts.fact_id (B.3 / §N.5) in constituent_fact_ids_array.

_BHAVA_EDGE_META = {
    "lordship":     ("rules",     "bhava_lordship",         0.6,
                     "parashari/bhava_lordship"),
    "occupancy":    ("occupies",  "graha_bhava_occupancy",  0.7,
                     "chart_facts/graha_position/house_d1"),
    "bhava_aspect": ("aspects",   "parashari_bhava_aspect", 0.5,
                     "chart_facts/aspect_parashari_given"),
}


def _graha_bhava_edge(
    edge_type: str, chart_id: str, aya: str, build_id: str,
    graha_node: str, bhava_node: str, graha: str, house: int,
    fact_ids: list[str], now: str, dasha_periods: list | None = None,
    lookups: "ViharaLookups | None" = None,
) -> dict:
    verb, sem_class, base_strength, cite_root = _BHAVA_EDGE_META[edge_type]
    _strength, _vichara_ids = _edge_strength_v1(base_strength, graha, None, lookups)
    return {
        "edge_id":                         str(uuid.uuid4()),
        "chart_id":                        chart_id,
        "ayanamsha_id":                    aya,
        "build_id":                        build_id,
        "snapshot_type":                   SNAPSHOT_TYPE,
        "edge_type":                       edge_type,
        "from_node_id":                    graha_node,   # graha → bhava
        "to_node_id":                      bhava_node,
        "direction":                       "directed",
        "computed_strength":               _strength,
        "weight_formula_version":          EDGE_STRENGTH_FORMULA_VERSION,
        "constituent_ga_vichara_ids_array": _vichara_ids,
        "edge_properties_jsonb":           json.dumps({
            "graha": graha, "house": house, "relation": verb,
        }),
        "relationship_class":              edge_type,
        "semantic_path_class":             "graha_bhava",
        "active_duration_class":           "natal_permanent",
        # WP-2.3-temporal: the graha's ruling Vimśottarī daśā/antardaśā periods
        # (birth-forward, from L1 chart_dashas via the WP-2.1 resolver). Honest
        # [] when the graha has no eligible birth-forward period — never NULL,
        # never fabricated.
        "active_dasha_periods_jsonb":      json.dumps(dasha_periods or []),
        "underlying_msr_signal_ids_array": [],
        "constituent_fact_ids_array":      fact_ids,
        "cross_system_consensus_count":    1,
        "cancelled_flag":                  False,
        "present_in_traditions_array":     ["parashari"],
        "graph_compute_library":           GRAPH_LIB,
        "graph_compute_library_version":   GRAPH_LIB_VER,
        "is_cross_subsystem":              False,
        "subsystem_from":                  "parashari",
        "subsystem_to":                    "parashari",
        **_typed_edge_fields(edge_type),
        "verification_pass_status":        "single_pass",
        "citation_ref":                    f"{cite_root}/{graha}/H{house}",
        "citation_human":                  f"{graha} {verb} house {house}",
        "computed_at":                     now,
        "engine_version":                  ENGINE_VERSION,
    }


def _fetch_bhava_lordship_facts(conn, chart_id: str, aya: str) -> list[dict]:
    """D1 house lords from L1 lord_in_house_per_varga (subject 'D1_H<n>').

    fact_value_text is 'Mars_in_H7' → lord graha = 'Mars', house = subject's n.
    Returns [{graha, house, fact_id}]. Rahu/Ketu never lord in Parashari.
    """
    rows = conn.execute(
        """SELECT fact_subject, fact_value_text, fact_id
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'lord_in_house_per_varga'
             AND fact_subject LIKE 'D1\\_H%%'""",
        [chart_id, aya],
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        if isinstance(r, dict):
            subject, text, fid = r["fact_subject"], r["fact_value_text"], r["fact_id"]
        else:
            subject, text, fid = str(r[0]), r[1], r[2]
        if not text or not subject:
            continue
        try:
            house = int(subject.split("_H", 1)[1])
        except (IndexError, ValueError):
            continue
        lord = str(text).split("_in_H", 1)[0].strip().title()
        if lord in KNOWN_GRAHAS and 1 <= house <= 12:
            out.append({"graha": lord, "house": house, "fact_id": str(fid)})
    return out


def _fetch_occupancy_facts(conn, chart_id: str, aya: str) -> list[dict]:
    """Graha → house occupancy from L1 graha_position/house_d1.

    Returns [{graha, house, fact_id}].
    """
    rows = conn.execute(
        """SELECT fact_subject, fact_value_num, fact_id
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'graha_position'
             AND fact_key = 'house_d1'""",
        [chart_id, aya],
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        if isinstance(r, dict):
            subject, val, fid = r["fact_subject"], r["fact_value_num"], r["fact_id"]
        else:
            subject, val, fid = str(r[0]), r[1], r[2]
        graha = _GRAHA_SUBJECT_MAP.get(str(subject).upper())
        if not graha or val is None:
            continue
        try:
            house = int(float(val))
        except (TypeError, ValueError):
            continue
        if 1 <= house <= 12:
            out.append({"graha": graha, "house": house, "fact_id": str(fid)})
    return out


def _fetch_graha_bhava_aspect_facts(conn, chart_id: str, aya: str) -> list[dict]:
    """Graha → house Parashari aspect from L1 aspect_parashari_given.

    fact_subject = graha code, fact_key = 'house_<n>'. Returns [{graha, house, fact_id}].
    """
    rows = conn.execute(
        """SELECT fact_subject, fact_key, fact_id
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'aspect_parashari_given'
             AND fact_key LIKE 'house\\_%%'""",
        [chart_id, aya],
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        if isinstance(r, dict):
            subject, key, fid = r["fact_subject"], r["fact_key"], r["fact_id"]
        else:
            subject, key, fid = str(r[0]), str(r[1]), r[2]
        graha = _GRAHA_SUBJECT_MAP.get(str(subject).upper())
        if not graha:
            continue
        try:
            house = int(str(key).split("house_", 1)[1])
        except (IndexError, ValueError):
            continue
        if 1 <= house <= 12:
            out.append({"graha": graha, "house": house, "fact_id": str(fid)})
    return out


def _build_bhava_edges(
    chart_id: str, aya: str, build_id: str,
    lordship_facts: list[dict], occupancy_facts: list[dict], aspect_facts: list[dict],
    node_map: dict[tuple[str, str], str], now: str,
    dasha_periods_by_graha: dict | None = None,
    lookups: "ViharaLookups | None" = None,
) -> list[dict]:
    """graha↔bhava edges: lordship, occupancy, bhava_aspect. Each cites its L1
    fact_id (constituent_fact_ids_array) and carries the resting graha's ruling
    daśā periods (active_dasha_periods_jsonb) via the WP-2.1 resolver."""
    dp_by_graha = dasha_periods_by_graha or {}
    edges: list[dict] = []
    plan = (
        ("lordship",     lordship_facts),
        ("occupancy",    occupancy_facts),
        ("bhava_aspect", aspect_facts),
    )
    for edge_type, facts in plan:
        for f in facts:
            graha, house, fid = f["graha"], f["house"], f["fact_id"]
            graha_node = node_map.get(("graha", graha))
            bhava_node = node_map.get(("bhava", str(house)))
            if not graha_node or not bhava_node:
                continue
            edges.append(_graha_bhava_edge(
                edge_type, chart_id, aya, build_id,
                graha_node, bhava_node, graha, house, [fid], now,
                dp_by_graha.get(graha, []), lookups,
            ))
    return edges


def _build_yoga_membership_edges(
    chart_id: str, aya: str, build_id: str,
    signals: list[dict], node_map: dict[tuple[str, str], str],
    occupancy_by_graha: dict[str, str], lord_fact_by_house: dict[int, str],
    now: str, dasha_periods_by_graha: dict | None = None,
    lookups: "ViharaLookups | None" = None,
) -> list[dict]:
    """Membership edges: yoga/dosha config node ↔ its constituent grahas / bhavas.

    The config node was created by bo_bimba (same yoga_node_subject key). For each
    yoga/dosha signal we extract the constituent graha (cfg) and/or house (cfg) and
    wire an edge to the graha / bhava node. The edge cites a RESOLVING L1 fact_id
    (the constituent graha's occupancy fact, or the house's D1-lord fact) — NOT the
    dosha_label constituent (that referential break is WP-2.4's lane).
    """
    dp_by_graha = dasha_periods_by_graha or {}
    edges: list[dict] = []
    for sig in signals:
        sig_class = str(sig.get("signal_type_class") or "")
        if sig_class not in _YOGA_NODE_CLASSES:
            continue
        cfg = _parse_cfg(sig)
        type_id = str(sig.get("signal_type_id") or "")
        subject = _yoga_node_subject(sig_class, cfg, type_id)
        yoga_node = node_map.get((sig_class, subject))
        if not yoga_node:
            continue

        # Constituent graha (if the configuration names one) — the edge rests on
        # this graha, so it carries the graha's ruling daśā periods.
        graha = _graha_from_cfg(cfg)
        if graha:
            graha_node = node_map.get(("graha", graha))
            fid = occupancy_by_graha.get(graha)
            if graha_node:
                edges.append(_membership_edge(
                    chart_id, aya, build_id, yoga_node, graha_node,
                    sig_class, subject, "graha", graha,
                    [fid] if fid else [], now,
                    dp_by_graha.get(graha, []), lookups,
                ))

        # Constituent bhava (if the configuration names a house) — no graha rests
        # on this edge, so the temporal overlay is an honest [] (not a graha daśā).
        house = _house_from_cfg(cfg)
        if house:
            bhava_node = node_map.get(("bhava", str(house)))
            fid = lord_fact_by_house.get(house)
            if bhava_node:
                edges.append(_membership_edge(
                    chart_id, aya, build_id, yoga_node, bhava_node,
                    sig_class, subject, "bhava", str(house),
                    [fid] if fid else [], now, [], lookups,
                ))
    return edges


def _membership_edge(
    chart_id: str, aya: str, build_id: str,
    yoga_node: str, member_node: str, sig_class: str, yoga_subject: str,
    member_kind: str, member_subject: str, fact_ids: list[str], now: str,
    dasha_periods: list | None = None,
    lookups: "ViharaLookups | None" = None,
) -> dict:
    _graha_subject = member_subject if member_kind == "graha" else None
    _strength, _vichara_ids = _edge_strength_v1(0.5, _graha_subject, None, lookups)
    return {
        "edge_id":                         str(uuid.uuid4()),
        "chart_id":                        chart_id,
        "ayanamsha_id":                    aya,
        "build_id":                        build_id,
        "snapshot_type":                   SNAPSHOT_TYPE,
        "edge_type":                       "yoga_member",
        "from_node_id":                    yoga_node,       # config → constituent
        "to_node_id":                      member_node,
        "direction":                       "undirected",
        "computed_strength":               _strength,
        "weight_formula_version":          EDGE_STRENGTH_FORMULA_VERSION,
        "constituent_ga_vichara_ids_array": _vichara_ids,
        "edge_properties_jsonb":           json.dumps({
            "config_class": sig_class, "config": yoga_subject,
            "member_kind": member_kind, "member": member_subject,
        }),
        "relationship_class":              "membership",
        "semantic_path_class":             "configuration_membership",
        "active_duration_class":           "natal_permanent",
        # WP-2.3-temporal: for a graha member, the member graha's ruling daśā
        # periods (birth-forward, L1-sourced). For a bhava member no graha rests
        # on the edge → honest [] (the resolver is only for graha daśā lords).
        "active_dasha_periods_jsonb":      json.dumps(dasha_periods or []),
        "underlying_msr_signal_ids_array": [],
        "constituent_fact_ids_array":      fact_ids,
        "cross_system_consensus_count":    1,
        "cancelled_flag":                  False,
        "present_in_traditions_array":     ["parashari"],
        "graph_compute_library":           GRAPH_LIB,
        "graph_compute_library_version":   GRAPH_LIB_VER,
        "is_cross_subsystem":              False,
        "subsystem_from":                  "parashari",
        "subsystem_to":                    "parashari",
        **_typed_edge_fields("yoga_member"),
        "verification_pass_status":        "single_pass",
        "citation_ref":                    f"bo_karanajala/yoga_member/{yoga_subject}",
        "citation_human":                  f"{yoga_subject} ↔ {member_kind} {member_subject}",
        "computed_at":                     now,
        "engine_version":                  ENGINE_VERSION,
    }


def _house_from_cfg(cfg: dict) -> int | None:
    for k in ("house", "house_number", "bhava", "house_d1"):
        v = cfg.get(k)
        if v is not None:
            try:
                h = int(v)
                if 1 <= h <= 12:
                    return h
            except (TypeError, ValueError):
                pass
    return None


def _parse_cfg(sig: dict) -> dict:
    cfg_raw = sig.get("configuration_jsonb") or {}
    if isinstance(cfg_raw, str):
        try:
            return json.loads(cfg_raw)
        except Exception:
            return {}
    return cfg_raw if isinstance(cfg_raw, dict) else {}


def _graha_from_cfg(cfg: dict) -> str | None:
    """Extract a graha name from configuration_jsonb, normalizing case.

    The L1 ga_* writers store graha names as UPPER_SNAKE (e.g. "MOON", "SUN")
    in some fields, while KNOWN_GRAHAS uses Title Case ("Moon", "Sun").
    We normalize every candidate to Title Case before the membership check.
    """
    for k in ("graha", "primary_graha", "lord", "from_graha", "fact_key"):
        v = cfg.get(k, "")
        if not isinstance(v, str):
            continue
        # Normalize to Title Case for comparison
        v_title = v.strip().title()
        if v_title in KNOWN_GRAHAS:
            return v_title
        # Try splitting on ":" (e.g. "fact_key": "SUN:MOON") — take first match
        for part in v.split(":"):
            part_title = part.strip().title()
            if part_title in KNOWN_GRAHAS:
                return part_title
    return None


def _build_edges_and_contradictions(
    chart_id: str, aya: str, build_id: str,
    signals: list[dict], node_map: dict[tuple[str, str], str], now: str,
    lookups: "ViharaLookups | None" = None,
) -> tuple[list[dict], list[dict]]:
    edges: list[dict] = []
    contradictions: list[dict] = []

    # Index by graha for graha-keyed contradiction detection (Pass 1 only).
    # Contradictions require the same graha to be both yoga-karaka and dosha-karaka
    # in at least one overlapping domain — domain-overlap alone (without graha match)
    # is not a contradiction by this semantic definition.
    yoga_by_graha: dict[str, dict] = {}   # graha → signal (best-salience per graha)
    dosha_by_graha: dict[str, dict] = {}  # graha → signal (best-salience per graha)

    for sig in signals:
        sig_id     = str(sig.get("signal_id", ""))
        sig_class  = str(sig.get("signal_type_class") or "")
        tradition  = str(sig.get("signal_tradition") or "parashari")
        domains    = sig.get("domains_affected_array") or []
        salience   = float(sig.get("computed_salience") or 0.0)
        type_id    = str(sig.get("signal_type_id") or "")
        ver_pass   = str(sig.get("verification_pass_status") or "documented_approximation")
        cfg        = _parse_cfg(sig)
        graha      = _graha_from_cfg(cfg)

        def _get_node(ntype: str, subject: str) -> str | None:
            return node_map.get((ntype, subject))

        # ── Yoga → domain (positive edge) ────────────────────────────────────
        # yoga/dosha→domain edges: graha node (tradition = signal's tradition)
        # to domain node (tradition = "domain") → ALWAYS cross-subsystem
        if sig_class == "yoga" and graha:
            from_node = _get_node("graha", graha)
            for domain in domains:
                to_node = _get_node("domain", domain)
                if from_node and to_node:
                    _strength, _vichara_ids = _edge_strength_v1(round(salience, 6), graha, [domain], lookups)
                    edges.append({
                        "edge_id": str(uuid.uuid4()),
                        "chart_id": chart_id,
                        "ayanamsha_id": aya,
                        "build_id": build_id,
                        "snapshot_type": SNAPSHOT_TYPE,
                        "edge_type": "yoga_domain",
                        "from_node_id": from_node,
                        "to_node_id": to_node,
                        "direction": "directed",
                        "computed_strength": _strength,
                        "weight_formula_version": EDGE_STRENGTH_FORMULA_VERSION,
                        "constituent_ga_vichara_ids_array": _vichara_ids,
                        "edge_properties_jsonb": json.dumps({"signal_id": sig_id, "yoga": type_id}),
                        "relationship_class": "activation",
                        "semantic_path_class": "yoga_activation",
                        "active_duration_class": "natal_permanent",
                        "active_dasha_periods_jsonb": None,
                        "underlying_msr_signal_ids_array": [sig_id],
                        "cross_system_consensus_count": 1,
                        "cancelled_flag": False,
                        "present_in_traditions_array": [tradition],
                        "graph_compute_library": GRAPH_LIB,
                        "graph_compute_library_version": GRAPH_LIB_VER,
                        "is_cross_subsystem": True,    # graha-tradition ≠ "domain"
                        "subsystem_from": tradition,
                        "subsystem_to": "domain",
                        **_typed_edge_fields("yoga_domain", domains=[domain]),
                        "verification_pass_status": ver_pass,
                        "citation_ref": f"bodha_msr_signals/{sig_id}",
                        "citation_human": f"Yoga→domain edge: {type_id}→{domain}",
                        "computed_at": now,
                        "engine_version": ENGINE_VERSION,
                    })
            # Index for graha-keyed contradiction (keep highest-salience per graha)
            if graha not in yoga_by_graha or salience > float(yoga_by_graha[graha].get("computed_salience") or 0.0):
                yoga_by_graha[graha] = sig

        # ── Dosha → domain (antagonist edge) ─────────────────────────────────
        elif sig_class == "dosha" and graha:
            from_node = _get_node("graha", graha)
            for domain in domains:
                to_node = _get_node("domain", domain)
                if from_node and to_node:
                    # Formula applies to MAGNITUDE only — antagonist sign is a
                    # sign convention on computed_strength, never folded into the
                    # DR-7 clamp (which would otherwise clamp a negative value
                    # up to +0.1 and silently flip an antagonist edge positive).
                    _magnitude, _vichara_ids = _edge_strength_v1(round(salience, 6), graha, [domain], lookups)
                    edges.append({
                        "edge_id": str(uuid.uuid4()),
                        "chart_id": chart_id,
                        "ayanamsha_id": aya,
                        "build_id": build_id,
                        "snapshot_type": SNAPSHOT_TYPE,
                        "edge_type": "dosha_domain",
                        "from_node_id": from_node,
                        "to_node_id": to_node,
                        "direction": "directed",
                        "computed_strength": -_magnitude,
                        "weight_formula_version": EDGE_STRENGTH_FORMULA_VERSION,
                        "constituent_ga_vichara_ids_array": _vichara_ids,
                        "edge_properties_jsonb": json.dumps({"signal_id": sig_id, "dosha": type_id}),
                        "relationship_class": "antagonist",
                        "semantic_path_class": "dosha_impairment",
                        "active_duration_class": "natal_permanent",
                        "active_dasha_periods_jsonb": None,
                        "underlying_msr_signal_ids_array": [sig_id],
                        "cross_system_consensus_count": 1,
                        "cancelled_flag": False,
                        "present_in_traditions_array": [tradition],
                        "graph_compute_library": GRAPH_LIB,
                        "graph_compute_library_version": GRAPH_LIB_VER,
                        "is_cross_subsystem": True,    # graha-tradition ≠ "domain"
                        "subsystem_from": tradition,
                        "subsystem_to": "domain",
                        **_typed_edge_fields("dosha_domain", domains=[domain]),
                        "verification_pass_status": ver_pass,
                        "citation_ref": f"bodha_msr_signals/{sig_id}",
                        "citation_human": f"Dosha→domain edge: {type_id}→{domain}",
                        "computed_at": now,
                        "engine_version": ENGINE_VERSION,
                    })
            # Index for graha-keyed contradiction (keep highest-salience per graha)
            if graha and (graha not in dosha_by_graha or salience > float(dosha_by_graha[graha].get("computed_salience") or 0.0)):
                dosha_by_graha[graha] = sig

        # ── Aspect / conjunction / path edges ────────────────────────────────
        # graha→graha edges: cross-subsystem only when the two signals differ in tradition
        elif sig_class == "composite_state" and graha:
            _raw_ag = (cfg.get("aspected_graha") or cfg.get("graha_b")
                       or cfg.get("to_graha"))
            aspected_graha: str | None = None
            if _raw_ag and isinstance(_raw_ag, str):
                _ag_title = _raw_ag.strip().title()
                if _ag_title in KNOWN_GRAHAS:
                    aspected_graha = _ag_title
            if not aspected_graha:
                fact_key = cfg.get("fact_key", "")
                parts = fact_key.split(":")
                for p in parts:
                    p_title = p.strip().title()
                    if p_title in KNOWN_GRAHAS and p_title != graha:
                        aspected_graha = p_title
                        break
            if aspected_graha and aspected_graha in KNOWN_GRAHAS:
                from_node = _get_node("graha", graha)
                to_node   = _get_node("graha", aspected_graha)
                if from_node and to_node:
                    etype = "conjunction" if "conjunction" in type_id else "aspect"
                    # For graha→graha edges, both endpoints share the same tradition
                    # (the signal's tradition) — cross-subsystem only if tradition differs,
                    # which for a single signal cannot happen; we record same→same here.
                    _strength, _vichara_ids = _edge_strength_v1(
                        round(salience, 6), graha, list(domains), lookups)
                    edges.append({
                        "edge_id": str(uuid.uuid4()),
                        "chart_id": chart_id,
                        "ayanamsha_id": aya,
                        "build_id": build_id,
                        "snapshot_type": SNAPSHOT_TYPE,
                        "edge_type": etype,
                        "from_node_id": from_node,
                        "to_node_id": to_node,
                        "direction": "directed",
                        "computed_strength": _strength,
                        "weight_formula_version": EDGE_STRENGTH_FORMULA_VERSION,
                        "constituent_ga_vichara_ids_array": _vichara_ids,
                        "edge_properties_jsonb": json.dumps({"signal_id": sig_id}),
                        "relationship_class": etype,
                        "semantic_path_class": "graha_graha",
                        "active_duration_class": "natal_permanent",
                        "active_dasha_periods_jsonb": None,
                        "underlying_msr_signal_ids_array": [sig_id],
                        "cross_system_consensus_count": 1,
                        "cancelled_flag": False,
                        "present_in_traditions_array": [tradition],
                        "graph_compute_library": GRAPH_LIB,
                        "graph_compute_library_version": GRAPH_LIB_VER,
                        "is_cross_subsystem": False,
                        "subsystem_from": tradition,
                        "subsystem_to": tradition,
                        **_typed_edge_fields(etype, domains=list(domains),
                                             graha_a=graha, graha_b=aspected_graha),
                        "verification_pass_status": ver_pass,
                        "citation_ref": f"bodha_msr_signals/{sig_id}",
                        "citation_human": f"{etype}: {graha}→{aspected_graha}",
                        "computed_at": now,
                        "engine_version": ENGINE_VERSION,
                    })

    # ── Contradiction detection ────────────────────────────────────────────────
    # WP-2.2 / LCA-5 / R-44e fix. The prior engine was INERT: it collapsed each
    # graha to a SINGLE best-salience yoga signal and a SINGLE best-salience dosha
    # signal (yoga_by_graha / dosha_by_graha above), then required THOSE two exact
    # signals to share a domain. When the top-salience yoga's domain differed from
    # the top-salience dosha's domain — the common case — a genuine lower-salience
    # yoga↔dosha tension on the same graph was silently dropped and the table stayed
    # at count(*)=0 (R-44e contradiction_count=0). We rescan ALL yoga/dosha signals
    # (independent of the edge-loop indices, which stay untouched for WP-2.3) and
    # emit two honest tension classes. B.10: nothing is fabricated — every row cites
    # two real bodha_msr_signals whose classical valence genuinely opposes on a shared
    # domain.
    contradictions.extend(
        _detect_contradictions(chart_id, aya, build_id, signals, now)
    )

    return edges, contradictions


def _detect_contradictions(
    chart_id: str, aya: str, build_id: str, signals: list[dict], now: str
) -> list[dict]:
    """Derive contradiction rows from MSR yoga/dosha tension.

    Two classes, both structurally derived (no pre-stored contradicts_signals_array,
    which bo_laksana writes NULL):

      graha_yoga_vs_dosha    — the SAME graha is a yoga-karaka in one signal and a
                               dosha-karaka in another, on ≥1 shared domain. Considers
                               EVERY yoga/dosha signal per graha (not just the top),
                               emitting the highest-combined-salience overlapping pair.
      domain_promise_vs_denial — a domain carries BOTH a yoga (promise) and a dosha
                               (affliction) signal, regardless of graha. One row per
                               domain, pairing that domain's strongest yoga and dosha.

    Deduped on the unordered (signal_a, signal_b) pair — the table's UNIQUE key.
    """
    def _yd(sig: dict) -> tuple[str | None, list[str], float]:
        graha = _graha_from_cfg(_parse_cfg(sig))
        domains = [d for d in (sig.get("domains_affected_array") or []) if d]
        sal = float(sig.get("computed_salience") or 0.0)
        return graha, domains, sal

    yoga_sigs  = [s for s in signals if str(s.get("signal_type_class") or "") == "yoga"]
    dosha_sigs = [s for s in signals if str(s.get("signal_type_class") or "") == "dosha"]

    rows: list[dict] = []
    seen_pairs: set[frozenset] = set()

    def _emit(y_sig: dict, d_sig: dict, shared: set[str], tension_class: str,
              graha: str | None) -> None:
        y_id = str(y_sig.get("signal_id"))
        d_id = str(d_sig.get("signal_id"))
        if not y_id or not d_id or y_id == d_id:
            return
        key = frozenset((y_id, d_id))
        if key in seen_pairs:
            return
        seen_pairs.add(key)
        basis = {
            "yoga_signal": str(y_sig.get("signal_type_id")),
            "dosha_signal": str(d_sig.get("signal_type_id")),
            "shared_domains": sorted(shared),
        }
        if graha:
            basis["graha"] = graha
        rows.append({
            "contradiction_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "signal_a_id": y_id,
            "signal_b_id": d_id,
            "tension_basis_jsonb": json.dumps(basis),
            "tension_class": tension_class,
            "domains_affected_array": sorted(shared),
            "combined_salience": round(
                float(y_sig.get("computed_salience") or 0.0)
                + float(d_sig.get("computed_salience") or 0.0), 6),
            "verification_pass_status": "documented_approximation",
            "citation_ref": (
                f"bo_karanajala/contradiction/{tension_class}/"
                f"{graha or '_'}/{'_'.join(sorted(shared))}"
            ),
            "citation_human": (
                (f"yoga_vs_dosha on {graha} in {sorted(shared)}" if graha
                 else f"promise_vs_denial in {sorted(shared)}")
            ),
            "computed_at": now,
        })

    # ── Class 1: graha-keyed yoga-vs-dosha (all signals per graha) ──────────────
    yoga_by_graha: dict[str, list[dict]] = defaultdict(list)
    dosha_by_graha: dict[str, list[dict]] = defaultdict(list)
    for s in yoga_sigs:
        g, _, _ = _yd(s)
        if g:
            yoga_by_graha[g].append(s)
    for s in dosha_sigs:
        g, _, _ = _yd(s)
        if g:
            dosha_by_graha[g].append(s)

    for graha in yoga_by_graha:
        if graha not in dosha_by_graha:
            continue
        best: tuple[float, dict, dict, set] | None = None
        for y_sig in yoga_by_graha[graha]:
            _, y_dom, y_sal = _yd(y_sig)
            for d_sig in dosha_by_graha[graha]:
                _, d_dom, d_sal = _yd(d_sig)
                shared = set(y_dom) & set(d_dom)
                if not shared:
                    continue
                combined = y_sal + d_sal
                if best is None or combined > best[0]:
                    best = (combined, y_sig, d_sig, shared)
        if best is not None:
            _emit(best[1], best[2], best[3], "graha_yoga_vs_dosha", graha)

    # ── Class 2: domain promise-vs-denial (graha-agnostic) ──────────────────────
    # G13/PA-4: iterate over all 13 canonical domains (was 7-domain local set).
    for domain in CANONICAL_DOMAINS_SORTED:
        dom_yogas = sorted(
            (s for s in yoga_sigs if domain in (s.get("domains_affected_array") or [])),
            key=lambda s: float(s.get("computed_salience") or 0.0), reverse=True)
        dom_doshas = sorted(
            (s for s in dosha_sigs if domain in (s.get("domains_affected_array") or [])),
            key=lambda s: float(s.get("computed_salience") or 0.0), reverse=True)
        if dom_yogas and dom_doshas:
            _emit(dom_yogas[0], dom_doshas[0], {domain}, "domain_promise_vs_denial", None)

    return rows


def _batch_insert(conn, rows: list[dict], sql: str) -> int:
    inserted = 0
    for i in range(0, len(rows), _BATCH_SIZE):
        for row in rows[i:i + _BATCH_SIZE]:
            # New B.3 ledger column (WP-2.3): legacy edge builders don't set it —
            # default to empty so their %(constituent_fact_ids_array)s param binds.
            row.setdefault("constituent_fact_ids_array", [])
            row.setdefault("constituent_ga_vichara_ids_array", [])
            conn.execute(sql, row)
        inserted += len(rows[i:i + _BATCH_SIZE])
    return inserted


# ── Arudha + special-lagna nodes/edges (D-2 Lane V-4) ────────────────────────
# CGM previously carried only graha/bhava/domain/yoga/dosha node types (BIND-D2
# verified live: 0 'arudha'/'special_lagna' nodes on 482012f1). bo_bimba.py
# (node creation) is OUTSIDE V-4's may_touch glob, but bo_karanajala already has
# write access to bodha_cgm_nodes (the PageRank UPDATE below) — so these two
# node classes + their house-joining edges are added here rather than left
# unwired for the wave. Source: L1 chart_facts (arudha_pada, special_lagna) —
# §N.5-clean (every node cites its resolving L1 fact_id).

_NODE_UPSERT = """
INSERT INTO bodha_cgm_nodes (
  node_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  node_type, node_subject, node_label_human,
  position_in_chart_jsonb, strength_score, dignity_state,
  degree_in, degree_out,
  primary_domain, domain_affiliations_jsonb, cluster_membership_array,
  msr_signal_id, configuration_constituents_array, configuration_lifecycle_state,
  hub_flag, present_in_traditions_array,
  graph_compute_library, graph_compute_library_version,
  verification_pass_status, citation_ref, citation_human, computed_at, engine_version
) VALUES (
  %(node_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(node_type)s, %(node_subject)s, %(node_label_human)s,
  %(position_in_chart_jsonb)s::jsonb, NULL, NULL,
  0, 0,
  NULL, NULL, NULL,
  NULL, NULL, NULL,
  FALSE, %(present_in_traditions_array)s,
  %(graph_compute_library)s, %(graph_compute_library_version)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s, %(engine_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, build_id, snapshot_type, node_type, node_subject)
DO NOTHING
"""


def _fetch_arudha_special_lagna_facts(conn, chart_id: str, aya: str) -> dict:
    """{(node_type, node_subject): {house, sign, fact_id}} for arudha_pada +
    special_lagna L1 facts. node_subject: 'A1'..'A12' for arudha (stripped
    'ARUDHA_' prefix); the raw fact_subject (e.g. 'GHATI_LAGNA') for special_lagna."""
    rows = conn.execute(
        """SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_text, fact_value_num
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category IN ('arudha_pada', 'special_lagna')
             AND fact_key IN ('house_d1', 'sign', 'sign_lord')""",
        [chart_id, aya],
    ).fetchall()
    out: dict = {}
    for r in rows:
        cat, subj, key, txt, num, fid = (
            (r["fact_category"], r["fact_subject"], r["fact_key"], r["fact_value_text"], r["fact_value_num"], r["fact_id"])
            if isinstance(r, dict) else (r[1], r[2], r[3], r[4], r[5], r[0])
        )
        node_type = "arudha" if cat == "arudha_pada" else "special_lagna"
        node_subject = subj.removeprefix("ARUDHA_") if cat == "arudha_pada" else subj
        rec = out.setdefault((node_type, node_subject), {"house": None, "sign": None,
                                                            "sign_lord": None, "fact_id": None})
        if key == "house_d1" and num is not None:
            rec["house"] = int(float(num))
            rec["fact_id"] = str(fid)
        elif key == "sign" and txt:
            rec["sign"] = txt
        elif key == "sign_lord" and txt:
            rec["sign_lord"] = txt
        if rec["fact_id"] is None:
            rec["fact_id"] = str(fid)
    return out


def _build_arudha_special_lagna_nodes_and_edges(
    conn, chart_id: str, aya: str, build_id: str, now: str,
    node_map: dict, lookups: "ViharaLookups | None",
) -> tuple[int, list[dict]]:
    """Inserts arudha (A1-A12) + special-lagna (Ghati/Hora/Bhava-lagna/…) nodes
    into bodha_cgm_nodes (idempotent, ON CONFLICT DO NOTHING per-build) and
    returns (nodes_inserted, house-joining edges). Edge base weight 0.6
    ('occupies its house', mirrors the 'occupancy' base_relation_weight)."""
    facts = _fetch_arudha_special_lagna_facts(conn, chart_id, aya)
    inserted = 0
    edges: list[dict] = []
    with conn.cursor() as cur:
        for (node_type, node_subject), rec in facts.items():
            house = rec.get("house")
            node_row = {
                "node_id": str(uuid.uuid4()),
                "chart_id": chart_id,
                "ayanamsha_id": aya,
                "build_id": build_id,
                "snapshot_type": SNAPSHOT_TYPE,
                "node_type": node_type,
                "node_subject": node_subject,
                "node_label_human": f"{node_type.replace('_', ' ').title()} {node_subject}",
                "position_in_chart_jsonb": json.dumps(
                    {"house": house, "sign": rec.get("sign")}) if house or rec.get("sign") else None,
                "present_in_traditions_array": ["jaimini" if node_type == "arudha" else "parashari"],
                "graph_compute_library": GRAPH_LIB,
                "graph_compute_library_version": GRAPH_LIB_VER,
                "verification_pass_status": "single_pass",
                "citation_ref": f"chart_facts/{'arudha_pada' if node_type == 'arudha' else 'special_lagna'}/{node_subject}",
                "citation_human": f"{node_type} node: {node_subject}" + (f" (house {house})" if house else ""),
                "computed_at": now,
                "engine_version": ENGINE_VERSION,
            }
            cur.execute(_NODE_UPSERT, node_row)
            inserted += 1
            node_map[(node_type, node_subject)] = node_row["node_id"]

    for (node_type, node_subject), rec in facts.items():
        node_id = node_map.get((node_type, node_subject))
        house = rec.get("house")
        if not node_id or not house:
            continue
        bhava_node = node_map.get(("bhava", str(house)))
        if not bhava_node:
            continue
        lord = rec.get("sign_lord")
        base = 0.6
        _strength, _vichara_ids = _edge_strength_v1(base, lord, None, lookups)
        edge_type = "arudha_house" if node_type == "arudha" else "special_lagna_house"
        edges.append({
            "edge_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "edge_type": edge_type,
            "from_node_id": node_id,
            "to_node_id": bhava_node,
            "direction": "directed",
            "computed_strength": _strength,
            "weight_formula_version": EDGE_STRENGTH_FORMULA_VERSION,
            "constituent_ga_vichara_ids_array": _vichara_ids,
            "edge_properties_jsonb": json.dumps({"house": house, "sign_lord": lord}),
            "relationship_class": edge_type,
            "semantic_path_class": "arudha_placement" if node_type == "arudha" else "special_lagna_placement",
            "active_duration_class": "natal_permanent",
            "active_dasha_periods_jsonb": None,
            "underlying_msr_signal_ids_array": [],
            "constituent_fact_ids_array": [rec["fact_id"]] if rec.get("fact_id") else [],
            "cross_system_consensus_count": 1,
            "cancelled_flag": False,
            "present_in_traditions_array": ["jaimini" if node_type == "arudha" else "parashari"],
            "graph_compute_library": GRAPH_LIB,
            "graph_compute_library_version": GRAPH_LIB_VER,
            "is_cross_subsystem": False,
            "subsystem_from": "jaimini" if node_type == "arudha" else "parashari",
            "subsystem_to": "parashari",
            **_typed_edge_fields(edge_type, relationship_class=edge_type),
            "verification_pass_status": "single_pass",
            "citation_ref": f"bo_karanajala/{edge_type}/{node_subject}",
            "citation_human": f"{node_subject} falls in house {house}",
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
        })
    return inserted, edges


@register("bo_karanajala")
class BoKaranajalaWriter(WriterBase):
    """bo_karanajala: CGM edges + contradiction pairs."""
    asset_id = "bo_karanajala"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import (
            replace_prior_cgm_edges, replace_prior_contradictions,
        )

        chart_id  = ctx.config["chart_id"]
        build_id  = ctx.build_id
        conn      = ctx.db_conn
        now       = datetime.now(timezone.utc).isoformat()
        total_e   = 0
        total_c   = 0

        # WP-2.3-temporal: native birth date (life-indexing) for the daśā-period
        # overlay. Resolved once per chart; the per-ayanamsha timeline is loaded
        # inside the loop so each edge resolves against periods in its OWN
        # ayanamsha (chart_dashas pools 5 systems).
        birth_date = resolve_birth_date(conn, chart_id, ctx.config.get("birth_params"))

        for aya in CANONICAL_AYAS:
            signals     = _fetch_signals(conn, chart_id, aya)
            node_map    = _fetch_node_map(conn, chart_id, aya)
            graha_signs = _fetch_graha_sign_numbers(conn, chart_id, aya)

            if ctx.dry_run:
                logger.info(
                    "[bo_karanajala dry_run] %s — %d signals, %d nodes, %d graha_signs",
                    aya, len(signals), len(node_map), len(graha_signs),
                )
                continue

            if not node_map:
                raise RuntimeError(
                    f"[bo_karanajala] G3: chart_id={chart_id} ayanamsha={aya} — "
                    "node_map is empty (bodha_cgm_nodes has 0 rows for this chart/aya); "
                    "bo_bimba must run and succeed before bo_karanajala"
                )

            # ── graha↔bhava structural edges (WP-2.3 / LCA-9a-1) — fetched
            # early so occupied_house_by_graha can seed the DR-7 vichara lookups.
            lordship_facts = _fetch_bhava_lordship_facts(conn, chart_id, aya)
            occupancy_facts = _fetch_occupancy_facts(conn, chart_id, aya)
            aspect_bhava_facts = _fetch_graha_bhava_aspect_facts(conn, chart_id, aya)

            # DR-7 (DIS.020): the ga_vichara-sourced lookups for this (chart,
            # ayanamsha) substep, bundled once and threaded through every edge
            # builder below. Missing/partial chart_vichara degrades honestly to
            # neutral multipliers (1.0) per-lookup — never fabricated, never a halt.
            lookups = ViharaLookups(
                conn, chart_id, aya, _occupied_house_by_graha(occupancy_facts)
            )

            edges, contradictions = _build_edges_and_contradictions(
                chart_id, aya, build_id, signals, node_map, now, lookups
            )

            argala_edges = _build_argala_edges(
                chart_id, aya, build_id, graha_signs, node_map, now, lookups
            )
            edges.extend(argala_edges)

            dispositor_edges = _build_dispositor_edges(
                chart_id, aya, build_id, graha_signs, node_map, now, lookups
            )
            edges.extend(dispositor_edges)

            # ── WP-2.3-temporal: per-graha ruling daśā periods for THIS ayanamsha
            # (birth-forward, from L1 chart_dashas via the WP-2.1 resolver). Loaded
            # once per (chart × ayanamsha); precomputed per graha so each edge
            # builder is a dict lookup. Empty timeline degrades to all-[] honestly.
            dasha_timeline = load_dasha_timeline(
                conn, chart_id, ayanamsha_id=aya, birth_date=birth_date
            )
            dasha_periods_by_graha = _build_dasha_periods_by_graha(
                dasha_timeline, birth_date
            )

            bhava_edges = _build_bhava_edges(
                chart_id, aya, build_id,
                lordship_facts, occupancy_facts, aspect_bhava_facts, node_map, now,
                dasha_periods_by_graha, lookups,
            )
            edges.extend(bhava_edges)

            # ── yoga/dosha membership edges (config ↔ constituent graha/bhava) ─
            occupancy_by_graha = {f["graha"]: f["fact_id"] for f in occupancy_facts}
            lord_fact_by_house = {f["house"]: f["fact_id"] for f in lordship_facts}
            membership_edges = _build_yoga_membership_edges(
                chart_id, aya, build_id, signals, node_map,
                occupancy_by_graha, lord_fact_by_house, now,
                dasha_periods_by_graha, lookups,
            )
            edges.extend(membership_edges)

            # ── D-2 Lane V-4: arudha + special-lagna nodes joined into the
            # mechanism graph (BIND_D-2.md verified 0 such nodes existed).
            arudha_nodes_inserted, arudha_edges = _build_arudha_special_lagna_nodes_and_edges(
                conn, chart_id, aya, build_id, now, node_map, lookups,
            )
            edges.extend(arudha_edges)

            # ── Centralities (networkx): pagerank + eigenvector + betweenness +
            # harmonic (D-2 Lane V-4, ledger row 33 — CR-25 completes what
            # bo_bimba.py's docstring flagged as "left NULL here"). Computed over
            # the FULL real edge set (incl. the DR-7-weighted + arudha/special-
            # lagna edges just added), so the metrics are non-degenerate on any
            # chart carrying real structure.
            try:
                import networkx as nx
                G = nx.DiGraph()
                node_ids = list(
                    set(str(e["from_node_id"]) for e in edges)
                    | set(str(e["to_node_id"]) for e in edges)
                )
                G.add_nodes_from(node_ids)
                for e in edges:
                    G.add_edge(
                        str(e["from_node_id"]),
                        str(e["to_node_id"]),
                        weight=abs(float(e.get("computed_strength") or 0.5)),
                    )
                metrics_by_node: dict[str, dict] = {n: {} for n in node_ids}
                if G.number_of_nodes() > 0 and G.number_of_edges() > 0:
                    pagerank_scores = nx.pagerank(G, alpha=0.85, weight="weight")
                    for n, v in pagerank_scores.items():
                        metrics_by_node[n]["pagerank_score"] = round(v, 8)
                    try:
                        eig = nx.eigenvector_centrality(G, max_iter=500, weight="weight")
                        for n, v in eig.items():
                            metrics_by_node[n]["eigenvector_centrality"] = round(v, 8)
                    except (nx.PowerIterationFailedConvergence, nx.NetworkXException) as eig_exc:
                        logger.warning("[bo_karanajala] %s — eigenvector_centrality "
                                        "skipped: %s", aya, eig_exc)
                    bet = nx.betweenness_centrality(G, weight="weight", normalized=True)
                    for n, v in bet.items():
                        metrics_by_node[n]["betweenness_centrality"] = round(v, 8)
                    UG = G.to_undirected()
                    harm = nx.harmonic_centrality(UG, distance="weight")
                    max_harm = max(harm.values()) if harm else 0.0
                    for n, v in harm.items():
                        metrics_by_node[n]["harmonic_centrality"] = round(
                            v / max_harm, 8) if max_harm > 0 else 0.0
                non_null = {n: m for n, m in metrics_by_node.items() if m}
                if non_null:
                    with conn.cursor() as _cent_cur:
                        for node_id, m in non_null.items():
                            _cent_cur.execute(
                                """UPDATE bodha_cgm_nodes
                                   SET pagerank_score = COALESCE(%(pagerank_score)s, pagerank_score),
                                       eigenvector_centrality = COALESCE(%(eigenvector_centrality)s, eigenvector_centrality),
                                       betweenness_centrality = COALESCE(%(betweenness_centrality)s, betweenness_centrality),
                                       harmonic_centrality = COALESCE(%(harmonic_centrality)s, harmonic_centrality)
                                   WHERE node_id = %(node_id)s AND chart_id = %(chart_id)s AND ayanamsha_id = %(ayanamsha_id)s""",
                                {
                                    "pagerank_score": m.get("pagerank_score"),
                                    "eigenvector_centrality": m.get("eigenvector_centrality"),
                                    "betweenness_centrality": m.get("betweenness_centrality"),
                                    "harmonic_centrality": m.get("harmonic_centrality"),
                                    "node_id": node_id, "chart_id": chart_id, "ayanamsha_id": aya,
                                },
                            )
                    logger.info(
                        "[bo_karanajala] %s — centralities updated for %d nodes "
                        "(pagerank+eigenvector+betweenness+harmonic)",
                        aya, len(non_null),
                    )
            except Exception as pr_exc:
                logger.warning(
                    "[bo_karanajala] %s — centrality computation skipped: %s", aya, pr_exc
                )

            replace_prior_cgm_edges(conn, chart_id, aya, SNAPSHOT_TYPE)
            replace_prior_contradictions(conn, chart_id, aya)

            logger.info(
                "[bo_karanajala] %s — %d edges (%d argala, %d dispositor, "
                "%d bhava, %d yoga_member, %d arudha/special_lagna nodes), %d contradictions",
                aya, len(edges), len(argala_edges), len(dispositor_edges),
                len(bhava_edges), len(membership_edges), arudha_nodes_inserted, len(contradictions),
            )
            total_e += _batch_insert(conn, edges, _EDGE_INSERT)
            total_c += _batch_insert(conn, contradictions, _CONTRADICTION_INSERT)

        return WriterResult(asset_id=self.asset_id, rows_inserted=total_e + total_c,
                            notes=f"edges={total_e} contradictions={total_c}")

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

from . import WriterBase, ContextSpec, WriterResult, register
from pipeline.orchestrator.writers.bo_bimba import _SUBJECT_TO_GRAHA as _GRAHA_SUBJECT_MAP

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
  underlying_msr_signal_ids_array, cross_system_consensus_count,
  cancelled_flag, cancelled_by_jsonb, cross_ayanamsha_edge_stability_score,
  present_in_traditions_array, edge_betweenness, in_shortest_path_count,
  graph_compute_library, graph_compute_library_version,
  is_cross_subsystem, subsystem_from, subsystem_to,
  valence, relationship_basis, affected_domains,
  verification_pass_status, citation_ref, citation_human, computed_at, engine_version
) VALUES (
  %(edge_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(edge_type)s, %(from_node_id)s, %(to_node_id)s, %(direction)s,
  %(computed_strength)s, %(weight_formula_version)s,
  %(edge_properties_jsonb)s::jsonb, %(relationship_class)s, %(semantic_path_class)s,
  %(active_duration_class)s, %(active_dasha_periods_jsonb)s,
  %(underlying_msr_signal_ids_array)s, %(cross_system_consensus_count)s,
  %(cancelled_flag)s, NULL, NULL,
  %(present_in_traditions_array)s, NULL, NULL,
  %(graph_compute_library)s, %(graph_compute_library_version)s,
  %(is_cross_subsystem)s, %(subsystem_from)s, %(subsystem_to)s,
  %(valence)s, %(relationship_basis)s, %(affected_domains)s,
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
}

_EDGE_TYPE_BASIS: dict[str, str] = {
    "yoga_domain":  "yoga_activation",
    "dosha_domain": "dosha_impairment",
    "aspect":       "parashari_aspect",
    "conjunction":  "planetary_conjunction",
    "dispositor":   "sign_lordship",
    "argala":       "argala_intervention",
    "sade_sati":    "sade_sati_transit",
}


def _typed_edge_fields(
    edge_type: str,
    domains: list[str] | None = None,
    relationship_class: str | None = None,
) -> dict:
    """Return valence, relationship_basis, affected_domains for an edge type."""
    valence = _EDGE_TYPE_VALENCE.get(edge_type, "neutral")
    basis   = _EDGE_TYPE_BASIS.get(edge_type, relationship_class or edge_type)
    if edge_type == "argala" and relationship_class == "argala_virodha":
        valence = "antagonistic"
    return {
        "valence":            valence,
        "relationship_basis": basis,
        "affected_domains":   domains or [],
    }


KNOWN_GRAHAS = {
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
}

KNOWN_DOMAINS = {
    "career", "wealth", "health", "relationship",
    "spirituality", "character", "general",
}

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
    graha_signs: dict[str, int], node_map: dict[tuple[str, str], str], now: str
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
                "computed_strength": 0.5,
                "weight_formula_version": "edge_weight_v1.0",
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
                **_typed_edge_fields("argala", relationship_class=relationship_class),
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
    graha_signs: dict[str, int], node_map: dict[tuple[str, str], str], now: str
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
            "computed_strength":               0.6,
            "weight_formula_version":          "edge_weight_v1.0",
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
            **_typed_edge_fields("dispositor"),
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
    signals: list[dict], node_map: dict[tuple[str, str], str], now: str
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
                        "computed_strength": round(salience, 6),
                        "weight_formula_version": "edge_weight_v1.0",
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
                        "computed_strength": round(-salience, 6),
                        "weight_formula_version": "edge_weight_v1.0",
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
                        "computed_strength": round(salience, 6),
                        "weight_formula_version": "edge_weight_v1.0",
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
                        **_typed_edge_fields(etype, domains=list(domains)),
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
    for domain in sorted(KNOWN_DOMAINS):
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
            conn.execute(sql, row)
        inserted += len(rows[i:i + _BATCH_SIZE])
    return inserted


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

            edges, contradictions = _build_edges_and_contradictions(
                chart_id, aya, build_id, signals, node_map, now
            )

            argala_edges = _build_argala_edges(
                chart_id, aya, build_id, graha_signs, node_map, now
            )
            edges.extend(argala_edges)

            dispositor_edges = _build_dispositor_edges(
                chart_id, aya, build_id, graha_signs, node_map, now
            )
            edges.extend(dispositor_edges)

            # ── PageRank (networkx) ───────────────────────────────────────────
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
                pagerank_scores: dict[str, float] = {}
                if G.number_of_nodes() > 0 and G.number_of_edges() > 0:
                    pagerank_scores = nx.pagerank(G, alpha=0.85, weight="weight")
                if pagerank_scores:
                    with conn.cursor() as _pr_cur:
                        for node_id, score in pagerank_scores.items():
                            _pr_cur.execute(
                                """UPDATE bodha_cgm_nodes
                                   SET pagerank_score = %s
                                   WHERE node_id = %s AND chart_id = %s AND ayanamsha_id = %s""",
                                [round(score, 8), node_id, chart_id, aya],
                            )
                    logger.info(
                        "[bo_karanajala] %s — pagerank updated for %d nodes",
                        aya, len(pagerank_scores),
                    )
            except Exception as pr_exc:
                logger.warning(
                    "[bo_karanajala] %s — pagerank skipped: %s", aya, pr_exc
                )

            replace_prior_cgm_edges(conn, chart_id, aya, SNAPSHOT_TYPE)
            replace_prior_contradictions(conn, chart_id, aya)

            logger.info(
                "[bo_karanajala] %s — %d edges (%d argala, %d dispositor), %d contradictions",
                aya, len(edges), len(argala_edges), len(dispositor_edges), len(contradictions),
            )
            total_e += _batch_insert(conn, edges, _EDGE_INSERT)
            total_c += _batch_insert(conn, contradictions, _CONTRADICTION_INSERT)

        return WriterResult(asset_id=self.asset_id, rows_inserted=total_e + total_c,
                            notes=f"edges={total_e} contradictions={total_c}")

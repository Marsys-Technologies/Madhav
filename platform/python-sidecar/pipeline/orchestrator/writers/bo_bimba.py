"""
bo_bimba — Cosmic Geometry Map: Nodes (L2 Bodha)
=================================================
Creates one bodha_cgm_nodes row per unique entity active in the chart.

Entities extracted from bodha_msr_signals after bo_laksana runs:
  - 'graha'   — the 9 grahas (Sun…Ketu)
  - 'bhava'   — houses 1-12
  - 'domain'  — career / wealth / health / relationship / spirituality / character
  - 'yoga'    — named yoga signals with class='yoga' or 'dosha'

Centrality metrics (betweenness, pagerank, eigenvector) are left NULL here;
bo_karanajala back-fills them after building the edge set.

LIGHT writer: loops over CANONICAL_AYANAMSHAS in a single run() call.
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone

from . import WriterBase, ContextSpec, WriterResult, register
from brahmagyan.graha_vocabulary import to_title

logger = logging.getLogger(__name__)

ENGINE_VERSION   = "bo_bimba_v1.0"
SNAPSHOT_TYPE    = "static_natal"
GRAPH_LIB        = "internal"
GRAPH_LIB_VER    = "1.0"
CANONICAL_AYAS   = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

KNOWN_GRAHAS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
]

# L1 fact_subject codes → KNOWN_GRAHAS canonical names.
# subject.title() only worked for SUN→Sun and MOON→Moon; abbreviated codes like
# MAR, MER, JUP, VEN, SAT title-case to Mar/Mer/Jup/Ven/Sat (wrong) causing 7/9
# graha nodes to get position_in_chart_jsonb=null.
# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2 (found via the full-tree census; not one of the originally-
# enumerated retirement targets, but the same shape).
_SUBJECT_TO_GRAHA: dict[str, str] = {
    code: to_title(code)
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
}

KNOWN_DOMAINS = [
    "career", "wealth", "health", "relationship",
    "spirituality", "character", "general",
]

_NODE_INSERT = """
INSERT INTO bodha_cgm_nodes (
  node_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  node_type, node_subject, node_label_human,
  position_in_chart_jsonb, strength_score, dignity_state,
  degree_in, degree_out,
  betweenness_centrality, eigenvector_centrality, pagerank_score,
  clustering_coefficient, closeness_centrality, harmonic_centrality, core_number,
  primary_domain, domain_affiliations_jsonb, cluster_membership_array, cgm_subgraph_cluster_id,
  msr_signal_id, configuration_constituents_array, configuration_lifecycle_state,
  hub_flag, hub_score, hub_edge_types_array,
  present_in_traditions_array, cross_ayanamsha_presence_score,
  node_embedding_vec, ephemeris_audit_jsonb,
  msr_salience_version_used, cdlm_version_used,
  graph_compute_library, graph_compute_library_version,
  verification_pass_status, citation_ref, citation_human, computed_at, engine_version
) VALUES (
  %(node_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(node_type)s, %(node_subject)s, %(node_label_human)s,
  %(position_in_chart_jsonb)s::jsonb, %(strength_score)s, %(dignity_state)s,
  %(degree_in)s, %(degree_out)s,
  NULL, NULL, NULL, NULL, NULL, NULL, NULL,
  %(primary_domain)s, %(domain_affiliations_jsonb)s::jsonb, %(cluster_membership_array)s, NULL,
  %(msr_signal_id)s, %(configuration_constituents_array)s, %(configuration_lifecycle_state)s,
  %(hub_flag)s, NULL, NULL,
  %(present_in_traditions_array)s, NULL,
  NULL, NULL,
  NULL, NULL,
  %(graph_compute_library)s, %(graph_compute_library_version)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s, %(engine_version)s
)
"""

_BATCH_SIZE = 50


def _fetch_graha_positions(conn, chart_id: str, aya: str) -> dict[str, dict]:
    """Returns {graha_name: {"sign": str, "house": int}} from L1 chart_facts.

    Reads fact_category='graha_position' fact_key='sign' for sign name (fact_value_text)
    and fact_key='house_d1' for house number (fact_value_num).
    fact_subject is UPPER_SNAKE (SUN, MOON, etc.) so we title-case it to match KNOWN_GRAHAS.
    """
    positions: dict[str, dict] = {}

    # Sign name rows — ga_positions_writer emits (graha_position, sign, fact_value_text)
    sign_rows = conn.execute(
        """SELECT fact_subject, fact_value_text
           FROM chart_facts
           WHERE chart_id = %s
             AND ayanamsha_id = %s
             AND fact_category = 'graha_position'
             AND fact_key = 'sign'""",
        [chart_id, aya],
    ).fetchall()
    for r in sign_rows:
        if isinstance(r, dict):
            subject = r["fact_subject"]
            val     = r["fact_value_text"]
        else:
            subject = str(r[0])
            val     = str(r[1]) if r[1] is not None else None
        if val:
            graha = _SUBJECT_TO_GRAHA.get(subject.upper(), subject.title())
            if graha not in positions:
                positions[graha] = {}
            positions[graha]["sign"] = val

    # House number rows — ga_positions_writer emits (graha_position, house_d1, fact_value_num)
    house_rows = conn.execute(
        """SELECT fact_subject, fact_value_num
           FROM chart_facts
           WHERE chart_id = %s
             AND ayanamsha_id = %s
             AND fact_category = 'graha_position'
             AND fact_key = 'house_d1'""",
        [chart_id, aya],
    ).fetchall()
    for r in house_rows:
        if isinstance(r, dict):
            subject = r["fact_subject"]
            val     = r["fact_value_num"]
        else:
            subject = str(r[0])
            val     = r[1]
        if val is not None:
            graha = _SUBJECT_TO_GRAHA.get(subject.upper(), subject.title())
            try:
                house = int(float(val))
                if graha not in positions:
                    positions[graha] = {}
                positions[graha]["house"] = house
            except (TypeError, ValueError):
                pass

    return positions


def _fetch_msr_signals(conn, chart_id: str, aya: str) -> list[dict]:
    rows = conn.execute(
        """SELECT signal_id, signal_type_class, signal_tradition, configuration_jsonb,
                  domains_affected_array, deterministic_strength, computed_salience,
                  verification_pass_status, salience_formula_version, signal_type_id
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, aya],
    ).fetchall()
    keys = [
        "signal_id", "signal_type_class", "signal_tradition", "configuration_jsonb",
        "domains_affected_array", "deterministic_strength", "computed_salience",
        "verification_pass_status", "salience_formula_version", "signal_type_id",
    ]
    return [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]


def _fetch_d1_dignity(conn, chart_id: str, aya: str) -> dict[str, str]:
    """Returns {graha_name: dignity_text} from L1 chart_facts, D1 varga only.

    Reads fact_category='graha_dignity_per_varga' fact_key='dignity_state',
    filtered to fact_value_jsonb->>'varga'='D1'. fact_subject is 'D1_SUN' etc.
    (same query shape as bo_laksana._build_d1_dignity_map).

    P2 fix (was bo_bimba.py:253 — mislabel/drift): the graha-node dignity_state
    used to be harvested from whichever bodha_msr_signals row happened to
    reference the graha via _parse_graha_from_signal's generic key match
    (signal_type_class-agnostic), then read that row's own fact_value_text as
    if it were a dignity classification. Live on chart 482012f1: a
    'conjunction_special_point:conjunct_VEN' signal's fact_value_text is the
    literal string "Venus" (the conjunction partner's name), and a
    'lord_in_house_per_varga:lord_placement' signal's fact_value_text is
    "Venus_in_H12" (a house-placement label) — neither is a dignity state,
    yet both were being stored verbatim in dignity_state. No signal_type_class
    in bodha_msr_signals is actually "dignity", so the fabrication was
    guaranteed, not just possible. L1 chart_facts.graha_dignity_per_varga is
    the correct authority per CLAUDE.md §N.5 (L1 is authority over L2+
    derivations) — read it directly instead of re-deriving from an unrelated
    MSR signal's config.
    """
    dignity: dict[str, str] = {}
    rows = conn.execute(
        """SELECT fact_subject, fact_value_text
           FROM chart_facts
           WHERE chart_id = %s
             AND ayanamsha_id = %s
             AND fact_category = 'graha_dignity_per_varga'
             AND fact_key = 'dignity_state'
             AND fact_value_jsonb->>'varga' = 'D1'""",
        [chart_id, aya],
    ).fetchall()
    for r in rows:
        if isinstance(r, dict):
            subject = r["fact_subject"]
            val     = r["fact_value_text"]
        else:
            subject = str(r[0])
            val     = str(r[1]) if r[1] is not None else None
        if val:
            subject_key = str(subject).removeprefix("D1_").upper()
            graha = _SUBJECT_TO_GRAHA.get(subject_key)
            if graha:
                dignity[graha] = val
    return dignity


def _parse_graha_from_signal(cfg: dict) -> str | None:
    for k in ("graha", "primary_graha", "lord", "fact_key"):
        v = cfg.get(k)
        if v and str(v) in KNOWN_GRAHAS:
            return str(v)
        if v and isinstance(v, str):
            parts = v.split(":")
            for p in parts:
                if p in KNOWN_GRAHAS:
                    return p
    return None


# ── Yoga / dosha first-class node key (WP-2.3 / LCA-9a-1) ─────────────────────
# Shared with bo_karanajala so the edge builder can look up the yoga node that
# bo_bimba created for the same signal. node_type carries the class ('yoga' or
# 'dosha'); node_subject is a slug of the configuration name (stable per chart).

_YOGA_NODE_CLASSES = ("yoga", "dosha")


def _yoga_config_name(cfg: dict, signal_type_id: str) -> str:
    """Human name of a yoga/dosha signal (the label the node is titled by)."""
    for k in ("fact_value_text", "yoga_name", "dosha_name", "name", "label"):
        v = cfg.get(k)
        if v and isinstance(v, str) and v.strip():
            return v.strip()
    return signal_type_id


def yoga_node_subject(sig_class: str, cfg: dict, signal_type_id: str) -> str:
    """Stable node_subject key for a yoga/dosha configuration node.

    Same derivation used by bo_bimba (node creation) and bo_karanajala
    (membership-edge wiring) so both resolve to the same node. Namespaced by
    class to avoid a yoga and a dosha of the same name colliding on the
    (node_type, node_subject) uniqueness key.
    """
    name = _yoga_config_name(cfg, signal_type_id)
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "unnamed"
    return f"{sig_class}:{slug}"


def _parse_house_from_signal(cfg: dict) -> int | None:
    for k in ("house", "house_number", "bhava"):
        v = cfg.get(k)
        if v is not None:
            try:
                h = int(v)
                if 1 <= h <= 12:
                    return h
            except (TypeError, ValueError):
                pass
    return None


def _build_nodes_for_aya(
    chart_id: str, aya: str, build_id: str, signals: list[dict], now: str,
    graha_positions: dict[str, dict] | None = None,
    d1_dignity: dict[str, str] | None = None,
) -> list[dict]:
    nodes: list[dict] = []

    # ── Graha nodes (always 9, with strength from MSR signals) ──────────────
    graha_strength: dict[str, float] = {}
    graha_tradition: dict[str, set] = {g: set() for g in KNOWN_GRAHAS}

    for sig in signals:
        cfg = {}
        if sig.get("configuration_jsonb"):
            try:
                cfg = json.loads(sig["configuration_jsonb"]) if isinstance(sig["configuration_jsonb"], str) else sig["configuration_jsonb"]
            except Exception:
                pass
        g = _parse_graha_from_signal(cfg)
        if g:
            curr = graha_strength.get(g, 0.0)
            sal = float(sig.get("computed_salience") or 0.0)
            if sal > curr:
                graha_strength[g] = sal
            if sig.get("signal_tradition"):
                graha_tradition[g].add(str(sig["signal_tradition"]))

    for graha in KNOWN_GRAHAS:
        _pos = (graha_positions or {}).get(graha)
        _pos_json = json.dumps(_pos) if _pos else None
        nodes.append({
            "node_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "node_type": "graha",
            "node_subject": graha,
            "node_label_human": graha,
            "position_in_chart_jsonb": _pos_json,
            "strength_score": round(graha_strength.get(graha, 0.5), 6),
            "dignity_state": (d1_dignity or {}).get(graha),
            "degree_in": 0,
            "degree_out": 0,
            "primary_domain": None,
            "domain_affiliations_jsonb": None,
            "cluster_membership_array": None,
            "msr_signal_id": None,
            "configuration_constituents_array": None,
            "configuration_lifecycle_state": "natal_permanent",
            "hub_flag": False,
            "present_in_traditions_array": sorted(graha_tradition.get(graha, [])) or ["parashari"],
            "graph_compute_library": GRAPH_LIB,
            "graph_compute_library_version": GRAPH_LIB_VER,
            # M-22 fix: these graph nodes are a single deterministic
            # construction pass over already-computed upstream L1/L2 data
            # (bodha_msr_signals) — real, but not independently cross-checked
            # by a second pass. Demoted to "single_pass" (formulas.py
            # VERIFICATION_RESCALE 0.85 vs 1.00 for two_pass_verified).
            "verification_pass_status": "single_pass",
            "citation_ref": f"bo_bimba/graha/{graha}",
            "citation_human": f"Graha node: {graha}",
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
        })

    # ── Bhava nodes (12 houses) ───────────────────────────────────────────────
    house_signals: dict[int, float] = {}
    for sig in signals:
        cfg = {}
        if sig.get("configuration_jsonb"):
            try:
                cfg = json.loads(sig["configuration_jsonb"]) if isinstance(sig["configuration_jsonb"], str) else sig["configuration_jsonb"]
            except Exception:
                pass
        h = _parse_house_from_signal(cfg)
        if h:
            sal = float(sig.get("computed_salience") or 0.0)
            if sal > house_signals.get(h, 0.0):
                house_signals[h] = sal

    for h in range(1, 13):
        nodes.append({
            "node_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "node_type": "bhava",
            "node_subject": str(h),
            "node_label_human": f"House {h}",
            "position_in_chart_jsonb": json.dumps({"house": h}),
            "strength_score": round(house_signals.get(h, 0.4), 6),
            "dignity_state": None,
            "degree_in": 0,
            "degree_out": 0,
            "primary_domain": None,
            "domain_affiliations_jsonb": None,
            "cluster_membership_array": None,
            "msr_signal_id": None,
            "configuration_constituents_array": None,
            "configuration_lifecycle_state": "natal_permanent",
            "hub_flag": h in (1, 5, 9),
            "present_in_traditions_array": ["parashari"],
            "graph_compute_library": GRAPH_LIB,
            "graph_compute_library_version": GRAPH_LIB_VER,
            # M-22 fix: these graph nodes are a single deterministic
            # construction pass over already-computed upstream L1/L2 data
            # (bodha_msr_signals) — real, but not independently cross-checked
            # by a second pass. Demoted to "single_pass" (formulas.py
            # VERIFICATION_RESCALE 0.85 vs 1.00 for two_pass_verified).
            "verification_pass_status": "single_pass",
            "citation_ref": f"bo_bimba/bhava/{h}",
            "citation_human": f"Bhava node: house {h}",
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
        })

    # ── Domain nodes ──────────────────────────────────────────────────────────
    domain_salience: dict[str, float] = {d: 0.0 for d in KNOWN_DOMAINS}
    for sig in signals:
        domains = sig.get("domains_affected_array") or []
        sal = float(sig.get("computed_salience") or 0.0)
        for d in domains:
            if d in domain_salience:
                domain_salience[d] += sal

    for domain in KNOWN_DOMAINS:
        nodes.append({
            "node_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "node_type": "domain",
            "node_subject": domain,
            "node_label_human": domain.capitalize(),
            "position_in_chart_jsonb": None,
            "strength_score": round(min(domain_salience.get(domain, 0.0), 1.0), 6),
            "dignity_state": None,
            "degree_in": 0,
            "degree_out": 0,
            "primary_domain": domain,
            "domain_affiliations_jsonb": json.dumps({domain: 1.0}),
            "cluster_membership_array": [domain],
            "msr_signal_id": None,
            "configuration_constituents_array": None,
            "configuration_lifecycle_state": "natal_permanent",
            "hub_flag": False,
            "present_in_traditions_array": ["parashari"],
            "graph_compute_library": GRAPH_LIB,
            "graph_compute_library_version": GRAPH_LIB_VER,
            # M-22 fix: these graph nodes are a single deterministic
            # construction pass over already-computed upstream L1/L2 data
            # (bodha_msr_signals) — real, but not independently cross-checked
            # by a second pass. Demoted to "single_pass" (formulas.py
            # VERIFICATION_RESCALE 0.85 vs 1.00 for two_pass_verified).
            "verification_pass_status": "single_pass",
            "citation_ref": f"bo_bimba/domain/{domain}",
            "citation_human": f"Domain node: {domain}",
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
        })

    # ── Yoga / dosha first-class nodes (WP-2.3 / LCA-9a-1) ────────────────────
    # Previously NO node_type='yoga' existed — yoga/dosha configurations were
    # invisible in the graph. Emit one node per unique (class, name); dedup on
    # the (node_type, node_subject) uniqueness key keeping the highest-salience
    # signal. bo_karanajala wires membership edges (yoga ↔ constituent
    # grahas/bhavas) using the same yoga_node_subject() key.
    yoga_best: dict[tuple[str, str], dict] = {}
    for sig in signals:
        sig_class = str(sig.get("signal_type_class") or "")
        if sig_class not in _YOGA_NODE_CLASSES:
            continue
        cfg = {}
        if sig.get("configuration_jsonb"):
            try:
                cfg = (json.loads(sig["configuration_jsonb"])
                       if isinstance(sig["configuration_jsonb"], str)
                       else sig["configuration_jsonb"])
            except Exception:
                cfg = {}
        type_id = str(sig.get("signal_type_id") or "")
        subject = yoga_node_subject(sig_class, cfg, type_id)
        key = (sig_class, subject)
        sal = float(sig.get("computed_salience") or 0.0)
        prev = yoga_best.get(key)
        if prev is None or sal > float(prev.get("computed_salience") or 0.0):
            yoga_best[key] = {**sig, "_cfg": cfg, "_subject": subject, "_class": sig_class}

    for (sig_class, subject), sig in yoga_best.items():
        cfg      = sig["_cfg"]
        type_id  = str(sig.get("signal_type_id") or "")
        name     = _yoga_config_name(cfg, type_id)
        domains  = list(sig.get("domains_affected_array") or [])
        tradition = str(sig.get("signal_tradition") or "parashari")
        ver_pass = str(sig.get("verification_pass_status") or "single_pass")
        nodes.append({
            "node_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "node_type": sig_class,          # 'yoga' or 'dosha' — first-class now
            "node_subject": subject,
            "node_label_human": name,
            "position_in_chart_jsonb": None,
            "strength_score": round(float(sig.get("computed_salience") or 0.0), 6),
            "dignity_state": None,
            "degree_in": 0,
            "degree_out": 0,
            "primary_domain": domains[0] if domains else None,
            "domain_affiliations_jsonb": json.dumps({d: 1.0 for d in domains}) if domains else None,
            "cluster_membership_array": domains or None,
            "msr_signal_id": str(sig.get("signal_id")) if sig.get("signal_id") else None,
            "configuration_constituents_array": None,
            "configuration_lifecycle_state": "natal_permanent",
            "hub_flag": False,
            "present_in_traditions_array": [tradition],
            "graph_compute_library": GRAPH_LIB,
            "graph_compute_library_version": GRAPH_LIB_VER,
            "verification_pass_status": ver_pass,
            "citation_ref": f"bodha_msr_signals/{sig.get('signal_id')}",
            "citation_human": f"{sig_class.capitalize()} node: {name}",
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
        })

    return nodes


def _batch_insert(conn, nodes: list[dict]) -> int:
    inserted = 0
    for i in range(0, len(nodes), _BATCH_SIZE):
        for row in nodes[i:i + _BATCH_SIZE]:
            conn.execute(_NODE_INSERT, row)
        inserted += len(nodes[i:i + _BATCH_SIZE])
    return inserted


@register("bo_bimba")
class BoBimbaWriter(WriterBase):
    """bo_bimba: CGM node layer — one row per unique entity per ayanamsha."""
    asset_id = "bo_bimba"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_cgm_nodes

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()
        total    = 0

        for aya in CANONICAL_AYAS:
            if ctx.dry_run:
                signals = _fetch_msr_signals(conn, chart_id, aya)
                logger.info("[bo_bimba dry_run] %s — %d MSR signals found", aya, len(signals))
                continue

            signals = _fetch_msr_signals(conn, chart_id, aya)
            if not signals:
                raise RuntimeError(
                    f"[bo_bimba] G3: chart_id={chart_id} ayanamsha={aya} — "
                    "bodha_msr_signals is empty; bo_laksana must have failed or produced 0 rows"
                )
            graha_positions = _fetch_graha_positions(conn, chart_id, aya)
            if not graha_positions:
                logger.warning(
                    "[bo_bimba] %s — _fetch_graha_positions returned 0 rows; "
                    "graha nodes will have position_in_chart_jsonb=None (stellium/paths detectors will be blind)",
                    aya,
                )
            d1_dignity = _fetch_d1_dignity(conn, chart_id, aya)
            if not d1_dignity:
                logger.warning(
                    "[bo_bimba] %s — _fetch_d1_dignity returned 0 rows; "
                    "graha nodes will have dignity_state=None (honest null, not a fabricated value)",
                    aya,
                )
            nodes   = _build_nodes_for_aya(chart_id, aya, build_id, signals, now, graha_positions, d1_dignity)

            deleted = replace_prior_cgm_nodes(conn, chart_id, aya, SNAPSHOT_TYPE)
            logger.info("[bo_bimba] %s — deleted %d prior, inserting %d nodes", aya, deleted, len(nodes))

            total += _batch_insert(conn, nodes)

        return WriterResult(asset_id=self.asset_id, rows_inserted=total)

"""
bo_chart_gestalt — Chart Gestalt / Pratinidhi Synthesis (L2 Bodha)
===================================================================
प्रतिनिधि = "representative/summary"

Reads all earlier Bodha assets and synthesizes a per-chart gestalt:
  - defining_threads_jsonb: top chart_defining + major signals by salience (POINTERS only)
  - central_dynamics_ids: CDLM strongest-linkage cell ids (cross-domain synergies)
  - pivot_ids: placeholder for CDLM §C3 pivot factor ids (populated when available)
  - center_of_gravity_node_ids: top-pagerank CGM node ids + final-dispositor node ids
  - domain_verdict_map_jsonb: {domain → {signal_id, evidence{…}, verdict_note}} — POINTERS
    plus deterministic per-domain evidence counts. NO verdict_class and NO
    confidence are stored (SAMĀPTI B-N8-FIX / register F-12): storing them
    violated this writer's own ANTI-DRIFT rule below, and they were derived from
    a single top-salience row rather than from the domain's evidence.
  - headline_jsonb: top signature thread + strongest domain — pointers only
  - watch_list_jsonb: strongest malefic-valenced signals + weakest domain — pointers only
  - central_question_jsonb: antagonistic axis — pointers only
  - zoom_spine_jsonb: layered navigation: gestalt → domain → signals → L1 fact_ids
  - outliers_jsonb: non-template-significant outlier signals (from anveshana discoveries)
  - contested_areas_jsonb: domains where both valences are present; each carries a
    real balance_ratio + genuinely_balanced threshold (§N.8 register F-17) —
    contested is not the same claim as balanced

ANTI-DRIFT ABSOLUTE: this writer ONLY STORES POINTERS (signal_ids, cell_ids, node_ids).
It NEVER stores verdicts, computed values, or interpretive text.
The actual content is always retrieved by following the pointers to the source rows.

LIGHT writer — one run() call, iterates 5 ayanamshas.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION     = "bo_chart_gestalt_v1.0"
SNAPSHOT_TYPE      = "static_natal"
GESTALT_FORMULA_V  = "gestalt_formula_v1"
TOP_SIGNAL_COUNT   = 10   # max signals in defining_threads_jsonb
TOP_NODE_COUNT     = 5    # max nodes in center_of_gravity_node_ids
TOP_DOMAIN_COUNT   = 7    # domains to cover in verdict map

# §N.8 register F-17: a contested domain (both valences present) is only
# "genuinely balanced" when neither valence outnumbers the other by more than
# ~1.5x (min/max >= 0.67). Below this, the domain is contested but lopsided.
_CONTESTED_BALANCE_RATIO_THRESHOLD = 0.67

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

_GESTALT_INSERT = """
INSERT INTO bodha_chart_gestalt (
  gestalt_id, chart_id, ayanamsha_id, build_id,
  gestalt_formula_version,
  defining_threads_jsonb,
  central_dynamics_ids,
  pivot_ids,
  center_of_gravity_node_ids,
  domain_verdict_map_jsonb,
  headline_jsonb,
  watch_list_jsonb,
  central_question_jsonb,
  headline_confidence,
  headline_epistemic_jsonb,
  outliers_jsonb,
  contested_areas_jsonb,
  zoom_spine_jsonb,
  computed_at,
  engine_version
) VALUES (
  %(gestalt_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
  %(gestalt_formula_version)s,
  %(defining_threads_jsonb)s::jsonb,
  %(central_dynamics_ids)s,
  %(pivot_ids)s,
  %(center_of_gravity_node_ids)s,
  %(domain_verdict_map_jsonb)s::jsonb,
  %(headline_jsonb)s::jsonb,
  %(watch_list_jsonb)s::jsonb,
  %(central_question_jsonb)s::jsonb,
  %(headline_confidence)s,
  %(headline_epistemic_jsonb)s::jsonb,
  %(outliers_jsonb)s::jsonb,
  %(contested_areas_jsonb)s::jsonb,
  %(zoom_spine_jsonb)s::jsonb,
  %(computed_at)s,
  %(engine_version)s
)
"""


def _fetch_dict(conn: Any, sql: str, params: list) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return [dict(r) for r in rows]
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _write_aya(conn: Any, chart_id: str, aya: str, build_id: str, now: str) -> int:
    """Synthesize and write 1 gestalt row for one ayanamsha. Returns 1 on success, 0 if skipped."""

    # ── 1. Defining threads: top chart_defining + major signals by salience ────
    top_signals = _fetch_dict(
        conn,
        """SELECT signal_id, signal_type_id, signal_type_class, computed_salience,
                  signature_tier, valence, source_l1_asset, domains_affected_array,
                  constituent_facts_array
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND signature_tier IN ('chart_defining', 'major')
           ORDER BY computed_salience DESC NULLS LAST, signal_id ASC
           LIMIT %s""",
        [chart_id, aya, TOP_SIGNAL_COUNT],
    )

    if not top_signals:
        # Try any signals if no chart_defining/major ones
        top_signals = _fetch_dict(
            conn,
            """SELECT signal_id, signal_type_id, signal_type_class, computed_salience,
                      signature_tier, valence, source_l1_asset, domains_affected_array,
                      constituent_facts_array
               FROM bodha_msr_signals
               WHERE chart_id = %s AND ayanamsha_id = %s
               ORDER BY computed_salience DESC NULLS LAST, signal_id ASC
               LIMIT %s""",
            [chart_id, aya, TOP_SIGNAL_COUNT],
        )

    if not top_signals:
        logger.info("[bo_chart_gestalt] %s — no MSR signals; skipping", aya)
        return 0

    defining_threads = {
        "signal_ids": [str(s["signal_id"]) for s in top_signals],
        "tiers": [str(s.get("signature_tier") or "") for s in top_signals],
        "note": "pointer-only — follow signal_id to bodha_msr_signals for content",
    }

    # ── 2. Central dynamics: CDLM cell ids with highest linkage strength ────────
    strong_cells = _fetch_dict(
        conn,
        """SELECT cell_id, domain_row, domain_col, computed_linkage_strength
           FROM bodha_cdlm_cells
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s
           ORDER BY computed_linkage_strength DESC NULLS LAST, cell_id ASC
           LIMIT 5""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )
    central_dynamics_ids = [str(c["cell_id"]) for c in strong_cells]

    # ── 3. Center of gravity: top pagerank CGM nodes + final-dispositor paths ──
    top_nodes = _fetch_dict(
        conn,
        """SELECT node_id, node_subject, pagerank_score, hub_flag
           FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s
             AND node_type = 'graha'
           ORDER BY pagerank_score DESC NULLS LAST, node_id ASC
           LIMIT %s""",
        [chart_id, aya, SNAPSHOT_TYPE, TOP_NODE_COUNT],
    )
    center_of_gravity_ids = [str(n["node_id"]) for n in top_nodes]

    # Final dispositor nodes from cgm_paths
    final_disp_nodes = _fetch_dict(
        conn,
        """SELECT DISTINCT to_node_id
           FROM bodha_cgm_paths
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s
             AND is_final_dispositor = true""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )
    for r in final_disp_nodes:
        nid = str(r["to_node_id"])
        if nid not in center_of_gravity_ids:
            center_of_gravity_ids.append(nid)

    # ── 4. Domain verdict map: per-domain pointer to strongest signal ──────────
    domain_signals = _fetch_dict(
        conn,
        """SELECT DISTINCT ON (unnested_domain)
               unnest(domains_affected_array) AS unnested_domain,
               signal_id, computed_salience, valence, signature_tier
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
           ORDER BY unnested_domain, computed_salience DESC NULLS LAST, signal_id ASC
           LIMIT 50""",
        [chart_id, aya],
    )

    # ── §N.8 / ANTI-DRIFT (SAMĀPTI lane B-N8-FIX · register F-12) ─────────────
    # PRIOR STATE: this block computed `verdict_class` and `confidence` and
    # STORED them — in a writer whose own docstring (:19-21) says it "NEVER
    # stores verdicts, computed values, or interpretive text", and whose own
    # schema comment (migration 325:981) says "pointer-only; no stored verdicts".
    #
    # It was also wrong on its own terms: the verdict was read off ONE row (the
    # DISTINCT ON top-salience signal), so the career domain served
    # "strong_positive" on a chart holding 136 benefic vs 632 malefic signals.
    # The verdict was not a summary of the evidence, it was the first row of it.
    #
    # THE FIX: store the POINTER plus the deterministic per-domain EVIDENCE a
    # verdict must be computed from, and store NO verdict. Counts are facts, not
    # judgments — they are exactly what this writer is allowed to carry. The
    # verdict belongs to whatever layer legitimately computes verdicts; it is not
    # this writer's to invent, and a consumer can no longer read one from here
    # without also seeing the 136-vs-632 evidence that contradicts it.
    domain_evidence = {
        str(r["domain"]): r
        for r in _fetch_dict(
            conn,
            """SELECT unnest(domains_affected_array) AS domain,
                      COUNT(*)                                            AS signal_count,
                      COUNT(*) FILTER (WHERE valence = 'benefic')         AS benefic_count,
                      COUNT(*) FILTER (WHERE valence = 'malefic')         AS malefic_count,
                      COUNT(*) FILTER (WHERE valence = 'mixed')           AS mixed_count,
                      COUNT(*) FILTER (WHERE valence = 'neutral'
                                          OR valence IS NULL)             AS neutral_count,
                      COUNT(*) FILTER (WHERE signature_tier
                                             IN ('chart_defining','major')) AS major_tier_count
                 FROM bodha_msr_signals
                WHERE chart_id = %s AND ayanamsha_id = %s
                GROUP BY 1""",
            [chart_id, aya],
        )
    }

    domain_verdict_map: dict[str, dict] = {}
    for ds in domain_signals:
        domain = str(ds.get("unnested_domain") or "")
        if not domain or domain in domain_verdict_map:
            continue
        ev = domain_evidence.get(domain, {})
        domain_verdict_map[domain] = {
            # pointer — the only thing this writer is entitled to store
            "signal_id": str(ds["signal_id"]),
            # deterministic evidence, whole-domain (not the top row alone)
            "evidence": {
                "signal_count":    int(ev.get("signal_count") or 0),
                "benefic_count":   int(ev.get("benefic_count") or 0),
                "malefic_count":   int(ev.get("malefic_count") or 0),
                "mixed_count":     int(ev.get("mixed_count") or 0),
                "neutral_count":   int(ev.get("neutral_count") or 0),
                "major_tier_count": int(ev.get("major_tier_count") or 0),
                "top_signal_valence":        str(ds.get("valence") or "") or None,
                "top_signal_signature_tier": str(ds.get("signature_tier") or "") or None,
                "top_signal_salience":       _safe_float(ds.get("computed_salience")) or None,
            },
            "verdict_note": (
                "no verdict stored — this writer carries pointers and deterministic "
                "evidence only (docstring ANTI-DRIFT ABSOLUTE; migration 325 col "
                "comment). A verdict must be computed by the consuming layer from "
                "`evidence`, which is whole-domain, not the top signal alone."
            ),
        }

    # ── §N.8 (PŪRṆATĀ residual sweep): strongest/weakest domain ranking ────────
    # PRIOR STATE: `strongest_domain` read `list(domain_verdict_map.keys())[0]`
    # and (below, §6) `weakest_domain` read `list(...items())[-1]` — an
    # INSERTION-ORDER bug, not a sorting-by-value bug. `domain_verdict_map`'s
    # insertion order is inherited from `domain_signals`'s query, which is
    # `DISTINCT ON (unnested_domain) ... ORDER BY unnested_domain, ...` — i.e.
    # ALPHABETICAL by domain name (`DISTINCT ON` requires its own column to
    # lead `ORDER BY`). So "strongest" silently meant "alphabetically first"
    # and "weakest" meant "alphabetically last", regardless of any signal's
    # actual strength.
    #
    # THE FIX: rank domains by the real, already-computed
    # `evidence.top_signal_salience` (each domain's own top-salience signal,
    # per the DISTINCT ON above) — descending for strongest, ascending for
    # weakest — with the domain name as a deterministic tiebreak.
    domain_strength_order = sorted(
        domain_verdict_map.items(),
        key=lambda kv: (-_safe_float(kv[1]["evidence"].get("top_signal_salience")), kv[0]),
    )

    # ── 5. Headline: top signal + strongest domain (pointers only) ─────────────
    top_signal = top_signals[0] if top_signals else {}
    strongest_domain = domain_strength_order[0][0] if domain_strength_order else None
    headline = {
        "top_signal_id": str(top_signal.get("signal_id", "")) if top_signal else None,
        "top_signal_type": str(top_signal.get("signal_type_id", "")) if top_signal else None,
        "strongest_domain": strongest_domain,
        "note": (
            "pointer-only — no verdict text stored here. strongest_domain is "
            "ranked by evidence.top_signal_salience (descending), not by "
            "insertion/alphabetical order."
        ),
    }

    # headline_confidence from top signal salience
    headline_confidence = round(
        min(_safe_float(top_signal.get("computed_salience")) / 10.0, 1.0), 4
    ) if top_signal else 0.5

    # ── 6. Watch list: malefic-valenced signals ────────────────────────────────
    malefic_signals = _fetch_dict(
        conn,
        """SELECT signal_id, signal_type_id, computed_salience, domains_affected_array
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND valence = 'malefic'
           ORDER BY computed_salience DESC NULLS LAST, signal_id ASC
           LIMIT 5""",
        [chart_id, aya],
    )
    # Weakest domain: the low end of the same real salience ranking used for
    # `strongest_domain` above — NOT the last-inserted (alphabetically last)
    # dict entry the prior code read.
    weakest_domain_entry = domain_strength_order[-1] if domain_strength_order else None
    watch_list = {
        "malefic_signal_ids": [str(s["signal_id"]) for s in malefic_signals],
        "weakest_domain": weakest_domain_entry[0] if weakest_domain_entry else None,
        "weakest_domain_signal_id": weakest_domain_entry[1]["signal_id"] if weakest_domain_entry else None,
        "note": (
            "pointer-only — follow signal_ids for content. weakest_domain is "
            "ranked by evidence.top_signal_salience (ascending), not by "
            "insertion/alphabetical order."
        ),
    }

    # ── 7. Central question: antagonistic axis (strongest benefic vs malefic) ──
    benefic_top = _fetch_dict(
        conn,
        """SELECT signal_id, signal_type_id, domains_affected_array
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s AND valence = 'benefic'
           ORDER BY computed_salience DESC NULLS LAST, signal_id ASC
           LIMIT 1""",
        [chart_id, aya],
    )
    # ── §N.8 (PŪRṆATĀ residual sweep, register F-16) — linking_mechanism ───────
    # PRIOR STATE: `linking_mechanism` was hardcoded to the literal string
    # "domain_tension" regardless of the two poles actually selected. The two
    # queries above (benefic_top, malefic_signals) each pick the chart-wide
    # top signal for their valence independently — they never test whether
    # the two poles even share a domain, so "domain_tension" (a claim ABOUT
    # domain overlap) was asserted without the overlap ever being checked.
    #
    # THE FIX: compute the actual domain overlap between the two poles'
    # `domains_affected_array` and name the mechanism from what is really
    # there — "domain_tension" only when the poles share >=1 domain (a real
    # tension: opposing valence on the SAME ground); "cross_domain_contrast"
    # when they share none (still an antagonistic pair, but not a same-domain
    # tension); None when a pole is missing (no mechanism can be established).
    positive_domains = set(benefic_top[0].get("domains_affected_array") or []) if benefic_top else set()
    negative_domains = set(malefic_signals[0].get("domains_affected_array") or []) if malefic_signals else set()
    shared_domains = sorted(positive_domains & negative_domains)

    if not benefic_top or not malefic_signals:
        linking_mechanism = None
        linking_mechanism_terms = {"reason": "at least one pole is absent for this ayanamsha"}
    elif shared_domains:
        linking_mechanism = "domain_tension"
        linking_mechanism_terms = {"shared_domains": shared_domains}
    else:
        linking_mechanism = "cross_domain_contrast"
        linking_mechanism_terms = {
            "positive_pole_domains": sorted(positive_domains),
            "negative_pole_domains": sorted(negative_domains),
        }

    central_question = {
        "positive_pole_signal_id": str(benefic_top[0]["signal_id"]) if benefic_top else None,
        "negative_pole_signal_id": str(malefic_signals[0]["signal_id"]) if malefic_signals else None,
        "linking_mechanism": linking_mechanism,
        "linking_mechanism_terms": linking_mechanism_terms,
        "note": "pointer-only — antagonistic axis; follow signal_ids for content",
    }

    # ── 8. Outliers: non-template-significant discovery signal ids ─────────────
    outlier_discoveries = _fetch_dict(
        conn,
        """SELECT discovery_id, discovery_class, non_obviousness_score,
                  constituent_refs_jsonb
           FROM bodha_discoveries
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND discovery_class IN ('embedding_outlier', 'distributional_anomaly')
           ORDER BY composite_discovery_rank DESC, discovery_id ASC
           LIMIT 5""",
        [chart_id, aya],
    )
    outliers = {
        "discovery_ids": [str(d["discovery_id"]) for d in outlier_discoveries],
        "note": "pointer-only — non-template-significant outliers from bo_anveshana",
    }

    # ── 9. Contested areas: domains with both benefic and malefic signals ──────
    contested = _fetch_dict(
        conn,
        """SELECT unnest(domains_affected_array) AS domain,
                  COUNT(*) FILTER (WHERE valence = 'benefic') AS benefic_count,
                  COUNT(*) FILTER (WHERE valence = 'malefic') AS malefic_count
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
           GROUP BY 1
           HAVING COUNT(*) FILTER (WHERE valence = 'benefic') > 0
              AND COUNT(*) FILTER (WHERE valence = 'malefic') > 0
           ORDER BY
             (COUNT(*) FILTER (WHERE valence = 'benefic') + COUNT(*) FILTER (WHERE valence = 'malefic')) DESC,
             domain ASC
           LIMIT 3""",
        [chart_id, aya],
    )
    # ── §N.8 (PŪRṆATĀ residual sweep, register F-17) — genuinely balanced ──────
    # PRIOR STATE: the SQL's HAVING clause only required BOTH valence counts
    # to be > 0, and the note asserted the result was "genuinely balanced" —
    # a claim the query never tested. Live disproof (register): a chart with
    # 136 benefic vs 632 malefic signals in one domain was served as
    # "balanced" purely because both counts were non-zero.
    #
    # THE FIX (register's own diagnosis: "the fix is a threshold, not a new
    # detector"): compute a real balance_ratio = min(b,m)/max(b,m) in [0,1]
    # (1.0 = perfectly even) and only call a domain "genuinely_balanced" when
    # that ratio clears _CONTESTED_BALANCE_RATIO_THRESHOLD — neither valence
    # may outnumber the other by more than ~1.5x. A domain can be CONTESTED
    # (both valences present) without being BALANCED (136 vs 632 is contested,
    # ratio 0.215, correctly NOT genuinely balanced under this threshold).
    contested_areas = {
        "contested_domains": [
            {
                "domain": str(r["domain"]),
                "benefic_count": int(r["benefic_count"]),
                "malefic_count": int(r["malefic_count"]),
                "balance_ratio": round(
                    min(int(r["benefic_count"]), int(r["malefic_count"]))
                    / max(int(r["benefic_count"]), int(r["malefic_count"])),
                    4,
                ),
                "genuinely_balanced": (
                    min(int(r["benefic_count"]), int(r["malefic_count"]))
                    / max(int(r["benefic_count"]), int(r["malefic_count"]))
                ) >= _CONTESTED_BALANCE_RATIO_THRESHOLD,
            }
            for r in contested
        ],
        "balance_ratio_threshold": _CONTESTED_BALANCE_RATIO_THRESHOLD,
        "note": (
            "domains where BOTH benefic and malefic evidence exist (contested). "
            "Contested is NOT the same as balanced — see per-domain "
            "balance_ratio / genuinely_balanced (ratio >= "
            f"{_CONTESTED_BALANCE_RATIO_THRESHOLD} required); a lopsided "
            "domain (e.g. 136 vs 632, ratio 0.215) is contested but not "
            "genuinely balanced."
        ),
    }

    # ── 10. Zoom spine: layered navigation ────────────────────────────────────
    zoom_spine = {
        "gestalt_signal_ids": [str(s["signal_id"]) for s in top_signals[:3]],
        "domain_entry_points": {
            domain: info["signal_id"]
            for domain, info in list(domain_verdict_map.items())[:5]
        },
        "cgm_hub_node_ids": center_of_gravity_ids[:3],
        "note": "zoom spine: gestalt → domain signal ids → CGM hubs → L1 facts via constituent_facts_array",
    }

    # ── 11. headline_epistemic: ayanamsha robustness (real value patched below) ─
    # ── §N.8 (PŪRṆATĀ residual sweep, register F-15) — fragility_class ─────────
    # PRIOR STATE: `fragility_class` was hardcoded to the literal string
    # "multi_ayanamsha_tested" inside THIS per-ayanamsha function — written
    # once per aya, before any other aya's row existed to compare against. A
    # per-ayanamsha writer is structurally incapable of comparing across
    # ayanamshas from inside a single `_write_aya` call; the literal asserted
    # a cross-ayanamsha claim ("tested" implies compared) that no code path
    # here could have measured. Live disproof (register): the health domain's
    # verdict flipped between lahiri and raman while BOTH rows carried the
    # identical "tested" literal.
    #
    # THE FIX: `_write_aya` stores None here — honestly "not yet assessed" —
    # and `run()` calls `_assess_fragility()` + `_patch_fragility()` AFTER all
    # ayanamsha rows for this build are written, to compute the real,
    # cross-ayanamsha comparison and patch every row's headline_epistemic_jsonb
    # in place. See those functions below for the actual detector.
    headline_epistemic = {
        "ayanamsha_count": len(CANONICAL_AYAS),
        "fragility_class": None,
        "note": (
            "fragility_class is None here by construction — a single "
            "ayanamsha's write cannot compare across ayanamshas. It is "
            "patched to a real value once all ayanamsha rows for this build "
            "exist; see run()'s post-loop _assess_fragility() pass."
        ),
    }

    row = {
        "gestalt_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": build_id,
        "gestalt_formula_version": GESTALT_FORMULA_V,
        "defining_threads_jsonb": json.dumps(defining_threads),
        "central_dynamics_ids": central_dynamics_ids or None,
        "pivot_ids": None,    # L4 Phala fills when CDLM §C3 pivot factors are identified
        "center_of_gravity_node_ids": center_of_gravity_ids or None,
        "domain_verdict_map_jsonb": json.dumps(domain_verdict_map),
        "headline_jsonb": json.dumps(headline),
        "watch_list_jsonb": json.dumps(watch_list),
        "central_question_jsonb": json.dumps(central_question),
        "headline_confidence": headline_confidence,
        "headline_epistemic_jsonb": json.dumps(headline_epistemic),
        "outliers_jsonb": json.dumps(outliers),
        "contested_areas_jsonb": json.dumps(contested_areas),
        "zoom_spine_jsonb": json.dumps(zoom_spine),
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
    }

    with conn.cursor() as cur:
        cur.execute(_GESTALT_INSERT, row)

    logger.info(
        "[bo_chart_gestalt] %s — gestalt written: %d defining threads, %d domains",
        aya, len(top_signals), len(domain_verdict_map),
    )
    return 1


def _assess_fragility(conn: Any, chart_id: str, build_id: str) -> dict:
    """REAL cross-ayanamsha fragility assessment (§N.8 register F-15).

    Runs AFTER every `_write_aya` call for this build has completed, reading
    back the `domain_verdict_map_jsonb` this build actually wrote for each
    ayanamsha row. For every domain present in >=2 of those rows, compares
    which valence dominates that domain's evidence (benefic_count vs
    malefic_count) across ayanamshas. If any domain's dominant valence
    disagrees between at least two ayanamshas, the chart's synthesis is
    ayanamsha-sensitive ("ayanamsha_sensitive"); if every comparable domain
    agrees across every built row, it is "stable_across_ayanamsha". Fewer
    than 2 built rows, or zero domains comparable across >=2 rows, cannot
    establish either claim — None, not a default.

    Returns {"fragility_class": str|None, "terms": {...}, "error": str|None}.

    Can-fail: seed two ayanamsha rows for the same chart_id/build_id whose
    domain_verdict_map_jsonb disagrees on a shared domain's dominant valence
    (e.g. one benefic-leaning, one malefic-leaning) — fragility_class flips
    from "stable_across_ayanamsha" to "ayanamsha_sensitive".
    """
    try:
        rows = _fetch_dict(
            conn,
            """SELECT ayanamsha_id, domain_verdict_map_jsonb
                 FROM bodha_chart_gestalt
                WHERE chart_id = %s AND build_id = %s""",
            [chart_id, build_id],
        )
    except Exception as exc:  # unevaluable ⇒ unknown, NOT a pass
        logger.warning("[bo_chart_gestalt] fragility assessment unevaluable: %s", exc)
        return {"fragility_class": None, "terms": {}, "error": str(exc)}

    if len(rows) < 2:
        return {
            "fragility_class": None,
            "terms": {"ayanamsha_rows_compared": len(rows)},
            "error": None,
        }

    # domain -> {ayanamsha_id -> dominant_valence}
    per_domain: dict[str, dict[str, str]] = {}
    for r in rows:
        aya = r["ayanamsha_id"]
        vm = r["domain_verdict_map_jsonb"]
        if isinstance(vm, str):
            vm = json.loads(vm)
        for domain, entry in (vm or {}).items():
            ev = (entry or {}).get("evidence", {})
            b = int(ev.get("benefic_count") or 0)
            m = int(ev.get("malefic_count") or 0)
            dominant = "benefic_leaning" if b > m else "malefic_leaning" if m > b else "balanced"
            per_domain.setdefault(domain, {})[aya] = dominant

    compared_domains = []
    disagreeing_domains = []
    for domain, by_aya in per_domain.items():
        if len(by_aya) < 2:
            continue  # this domain didn't appear in enough rows to compare
        compared_domains.append(domain)
        if len(set(by_aya.values())) > 1:
            disagreeing_domains.append(domain)

    if not compared_domains:
        return {
            "fragility_class": None,
            "terms": {"ayanamsha_rows_compared": len(rows), "domains_compared": 0},
            "error": None,
        }

    fragility_class = "ayanamsha_sensitive" if disagreeing_domains else "stable_across_ayanamsha"
    return {
        "fragility_class": fragility_class,
        "terms": {
            "ayanamsha_rows_compared": len(rows),
            "domains_compared": sorted(compared_domains),
            "domains_disagreeing": sorted(disagreeing_domains),
        },
        "error": None,
    }


def _patch_fragility(conn: Any, chart_id: str, build_id: str, fragility_result: dict) -> None:
    """Patch the real, cross-ayanamsha fragility assessment into every row this
    build wrote. `_write_aya` cannot compute this itself (see its docstring
    comment) — it stores None, and this runs once, after the full loop."""
    rows = _fetch_dict(
        conn,
        """SELECT gestalt_id, headline_epistemic_jsonb
             FROM bodha_chart_gestalt
            WHERE chart_id = %s AND build_id = %s""",
        [chart_id, build_id],
    )
    for r in rows:
        epistemic = r["headline_epistemic_jsonb"]
        if isinstance(epistemic, str):
            epistemic = json.loads(epistemic)
        epistemic = dict(epistemic or {})
        epistemic["fragility_class"] = fragility_result["fragility_class"]
        epistemic["fragility_terms"] = fragility_result["terms"]
        if fragility_result["error"]:
            epistemic["fragility_error"] = fragility_result["error"]
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE bodha_chart_gestalt SET headline_epistemic_jsonb = %s::jsonb "
                "WHERE gestalt_id = %s",
                [json.dumps(epistemic), r["gestalt_id"]],
            )


@register("bo_chart_gestalt")
class BoChartGestaltWriter(WriterBase):
    """bo_chart_gestalt: per-chart gestalt pointer synthesis (O5 — highest interpretive value)."""
    asset_id = "bo_chart_gestalt"

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="dry_run — would write 1 gestalt row per ayanamsha (5 total)",
            )

        # Idempotency: delete prior rows for this chart
        with conn.cursor() as cur:
            # Disable per-statement timeout for the heavy DELETE on large charts.
            # SET LOCAL scopes to the orchestrator txn (writer never commits).
            # Ref: bo_laksana native-rebuild timeout; ka_* precedent (PR 422).
            cur.execute("SET LOCAL statement_timeout = 0")
            cur.execute("DELETE FROM bodha_chart_gestalt WHERE chart_id = %s", [chart_id])

        total = 0
        for aya in CANONICAL_AYAS:
            total += _write_aya(conn, chart_id, aya, build_id, now)

        # §N.8 register F-15: fragility_class cannot be established from
        # inside a single ayanamsha's write (see _write_aya's comment). Now
        # that every ayanamsha row for this build exists, assess the real
        # cross-ayanamsha comparison and patch it into every row.
        fragility_result = _assess_fragility(conn, chart_id, build_id)
        _patch_fragility(conn, chart_id, build_id, fragility_result)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            notes=(
                f"gestalt_rows={total} (1 per ayanamsha where MSR signals exist); "
                f"fragility_class={fragility_result['fragility_class']}"
            ),
        )

"""
bo_pramana_mapa — Synthesis Quality Scorecard (L2 Bodha)
=========================================================
The terminal Bodha writer. Runs last (after all other bo_* writers complete).

Reads from ALL bodha_* tables for this chart and writes one row to
synthesis_quality_scorecard:
  - Per-asset row counts
  - Quality pct (two_pass_verified vs documented_approximation)
  - Formula versions in use
  - Trap checks (authority inversion = MSR re-deriving L1 facts)
  - §N.8 earned-signal detectors (see the detector block below): LEL leak,
    pillar reachability, trap-2 narration leak, verification divergence.
    Every one of these has a reachable false/non-zero branch — none is a
    proxy, a tautology, or a literal.
  - Materialised view refresh (3 MVs from A10, 5 from A11)

Also refreshes the 3 spec materialized views:
  - mv_msr_top_signals_per_chart
  - mv_msr_recurring_patterns_per_chart
  - mv_msr_domain_summary
  (CONCURRENTLY if supported, otherwise blocking refresh)

LIGHT writer. Single INSERT; no ayanamsha loop (scorecard is chart-scoped).
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_pramana_mapa_v1.0"

_SCORECARD_INSERT = """
INSERT INTO synthesis_quality_scorecard (
  scorecard_id, chart_id, build_id, scored_at,
  msr_signal_count, cdlm_cell_count, cgm_node_count, cgm_edge_count,
  rm_resonance_count, rm_prescription_count, embedding_count,
  convergence_count, contradiction_count,
  divergent_flagged_count, two_pass_verified_pct, documented_approximation_pct,
  msr_no_threshold_drop_flag, msr_citation_ref_coverage_pct,
  salience_formula_version, linkage_formula_version, resonance_formula_version,
  convergence_formula_version, centrality_formula_version,
  trap1_authority_inversion_count, trap2_narration_leak_count,
  unresolved_constituent_facts_count,
  l1_assets_projected_count, l1_assets_projected_array,
  lel_zero_leak_pass, no_pre_answer_pass,
  pillars_meet_reachability_pass, ledger_independence_pass,
  discovery_not_fabricated_pass,
  notes
) VALUES (
  %(scorecard_id)s, %(chart_id)s, %(build_id)s, %(scored_at)s,
  %(msr_signal_count)s, %(cdlm_cell_count)s, %(cgm_node_count)s, %(cgm_edge_count)s,
  %(rm_resonance_count)s, %(rm_prescription_count)s, %(embedding_count)s,
  %(convergence_count)s, %(contradiction_count)s,
  %(divergent_flagged_count)s, %(two_pass_verified_pct)s, %(documented_approximation_pct)s,
  %(msr_no_threshold_drop_flag)s, %(msr_citation_ref_coverage_pct)s,
  %(salience_formula_version)s, %(linkage_formula_version)s, %(resonance_formula_version)s,
  %(convergence_formula_version)s, %(centrality_formula_version)s,
  %(trap1_authority_inversion_count)s, %(trap2_narration_leak_count)s,
  %(unresolved_constituent_facts_count)s,
  %(l1_assets_projected_count)s, %(l1_assets_projected_array)s,
  %(lel_zero_leak_pass)s, %(no_pre_answer_pass)s,
  %(pillars_meet_reachability_pass)s, %(ledger_independence_pass)s,
  %(discovery_not_fabricated_pass)s,
  %(notes)s
)
"""


def _count_one(conn: Any, sql: str, params: list) -> int:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return 0
    return int(row[0] if isinstance(row, (tuple, list)) else row.get("count", 0))


def _formula_version(conn: Any, chart_id: str, col: str, table: str) -> str | None:
    """Fetch the first non-null formula version string from a bodha table."""
    try:
        row = conn.execute(
            f"SELECT {col} FROM {table} WHERE chart_id = %s LIMIT 1",
            [chart_id],
        ).fetchone()
        if row:
            v = row[0] if isinstance(row, (tuple, list)) else row.get(col)
            return str(v) if v else None
    except Exception:
        pass
    return None


def _refresh_mv(conn: Any, mv_name: str) -> None:
    """Refresh a materialized view (non-concurrently; data lock acceptable at build close)."""
    try:
        conn.execute(f"REFRESH MATERIALIZED VIEW {mv_name}")
        logger.info("[bo_pramana_mapa] refreshed MV: %s", mv_name)
    except Exception as e:
        logger.warning("[bo_pramana_mapa] MV refresh failed (%s): %s", mv_name, e)


# ══════════════════════════════════════════════════════════════════════════════
# §N.8 EARNED-SIGNAL DETECTORS  (SAMĀPTI lane B-N8-FIX · register F-07…F-10)
# ══════════════════════════════════════════════════════════════════════════════
# Every function below answers the §N.8 question directly: "what code path would
# have to run — and fail — for this signal to correctly read false?"  Each one
# names its terms, records the per-term breakdown so a consumer can see WHAT was
# measured, and returns `None` (not a clean-looking default) when a term could
# not be evaluated at all.  None of these gates may be true-by-construction.
#
# Prior state (all four were §N.8 violations, confirmed in
# SAMAPTI_N8_EARNED_SIGNAL_REGISTER_v1_0.md §2.1):
#   F-07 lel_zero_leak_pass             — PROXY    (trap1_count == 0; no LEL read at all)
#   F-08 pillars_meet_reachability_pass — TAUTOLOGY (msr_count > 0, already raised above)
#   F-09 trap2_narration_leak_count     — LITERAL 0 (no detector)
#   F-10 divergent_flagged_count        — LITERAL 0 (no detector)

# ── F-07 · LEL leakage into the deterministic Bodha base ──────────────────────
# L2 Bodha is timeless-structural; Life-Event-Log data is L3-gated. Every bo_*
# writer stamps `lel_origin=False` by design (bo_laksana.py:11). A leak is
# therefore observable three independent ways, and ANY of them failing flips the
# gate. Term B and Term C do not depend on a writer having flagged itself
# honestly — they read the leaked payload directly.
_LEL_PAYLOAD_KEYS = [
    # jsonb key shapes that carry LEL rows out of `life_events` — the exact
    # payload bo_upaya legitimately writes at ITS layer (milestone_event_ids) and
    # the raw life_events column names.
    "milestone_event_ids", "life_event_ids", "lel_event_ids",
    "event_id", "event_date", "outcome_observed",
]

_LEL_TERM_A_SQL = """
SELECT count(*) FROM bodha_msr_signals
 WHERE chart_id = %s AND lel_origin IS TRUE
"""

# Term B: a constituent "fact_id" that actually resolves to a life_events row —
# an LEL primary key smuggled into the L1 grounding chain (§N.5 violation).
_LEL_TERM_B_SQL = """
SELECT count(DISTINCT s.signal_id)
  FROM bodha_msr_signals s
  CROSS JOIN LATERAL unnest(s.constituent_facts_array) AS r(ref)
  JOIN life_events le ON le.event_id::text = r.ref
 WHERE s.chart_id = %s
"""

# Term C: an LEL-shaped payload key present in the deterministic configuration.
_LEL_TERM_C_SQL = """
SELECT count(*) FROM bodha_msr_signals
 WHERE chart_id = %s
   AND jsonb_exists_any(configuration_jsonb, %s)
"""


def detect_lel_leak(conn: Any, chart_id: str) -> dict:
    """REAL LEL-leak scan over the deterministic Bodha base.

    Returns {"pass": bool|None, "terms": {...}, "error": str|None}.

    `pass` is None — never True — when any term could not be evaluated. An
    unevaluable check is an unknown, not a clean pass (§N.8).

    Can-fail: set any bodha_msr_signals row's `lel_origin` to true (term A),
    put a real `life_events.event_id` into its `constituent_facts_array`
    (term B), or add a `milestone_event_ids` key to its `configuration_jsonb`
    (term C) — each independently flips `pass` to False.
    """
    terms: dict[str, Any] = {}
    try:
        terms["lel_origin_signals"] = _count_one(conn, _LEL_TERM_A_SQL, [chart_id])
        terms["life_event_ids_in_constituent_chain"] = _count_one(
            conn, _LEL_TERM_B_SQL, [chart_id]
        )
        terms["lel_payload_keys_in_configuration"] = _count_one(
            conn, _LEL_TERM_C_SQL, [chart_id, _LEL_PAYLOAD_KEYS]
        )
    except Exception as exc:  # unevaluable ⇒ unknown, NOT a pass
        logger.warning("[bo_pramana_mapa] lel_zero_leak detector unevaluable: %s", exc)
        return {"pass": None, "terms": terms, "error": str(exc)}

    total = sum(int(v) for v in terms.values())
    terms["total_leaks"] = total
    terms["scanned_payload_keys"] = _LEL_PAYLOAD_KEYS
    return {"pass": total == 0, "terms": terms, "error": None}


# ── F-08 · pillar reachability ────────────────────────────────────────────────
# The four Bodha pillars are MSR · CDLM · CGM · RM (CLAUDE.md §I B.11). "Meet
# reachability" is two independent claims, and the second is the one the old
# tautology lacked (the F-19 lesson: a real gate needs a second, independent
# term): the pillars are present AND the graph pillar's references resolve.
_ORPHAN_EDGE_ENDPOINTS_SQL = """
SELECT count(*) FROM bodha_cgm_edges e
 WHERE e.chart_id = %s
   AND (NOT EXISTS (SELECT 1 FROM bodha_cgm_nodes n
                     WHERE n.chart_id = e.chart_id AND n.node_id = e.from_node_id)
     OR NOT EXISTS (SELECT 1 FROM bodha_cgm_nodes n
                     WHERE n.chart_id = e.chart_id AND n.node_id = e.to_node_id))
"""

_ORPHAN_EDGE_SIGNAL_REFS_SQL = """
SELECT count(DISTINCT e.edge_id)
  FROM bodha_cgm_edges e
  CROSS JOIN LATERAL unnest(e.underlying_msr_signal_ids_array) AS r(sid)
 WHERE e.chart_id = %s
   AND NOT EXISTS (SELECT 1 FROM bodha_msr_signals s
                    WHERE s.chart_id = e.chart_id AND s.signal_id = r.sid)
"""


def detect_pillar_reachability(
    conn: Any, chart_id: str,
    msr_count: int, cdlm_count: int, node_count: int,
    edge_count: int, res_count: int,
) -> dict:
    """REAL pillar-reachability gate.

    Term 1 (presence): each of the four pillars has at least one row for this
      chart — MSR signals, CDLM cells, CGM nodes+edges, RM resonances.
    Term 2 (reachability): every CGM edge endpoint resolves to a CGM node of the
      same chart, and every `underlying_msr_signal_ids_array` member resolves to
      an MSR signal of the same chart. A dangling pointer means the graph pillar
      is not actually traversable from the gestalt, which is what "reachability"
      asserts.

    Returns {"pass": bool|None, "terms": {...}, "error": str|None}.

    Can-fail: delete this chart's `bodha_cdlm_cells` (term 1 → False), or
    repoint one `bodha_cgm_edges.to_node_id` at a non-existent node
    (term 2 → False). Neither is reachable by the msr_count>0 tautology it
    replaces.
    """
    presence = {
        "msr_signals":   msr_count > 0,
        "cdlm_cells":    cdlm_count > 0,
        "cgm_nodes":     node_count > 0,
        "cgm_edges":     edge_count > 0,
        "rm_resonances": res_count > 0,
    }
    terms: dict[str, Any] = {"pillars_present": presence}
    try:
        orphan_endpoints = _count_one(conn, _ORPHAN_EDGE_ENDPOINTS_SQL, [chart_id])
        orphan_signal_refs = _count_one(conn, _ORPHAN_EDGE_SIGNAL_REFS_SQL, [chart_id])
    except Exception as exc:  # unevaluable ⇒ unknown, NOT a pass
        logger.warning("[bo_pramana_mapa] pillar-reachability detector unevaluable: %s", exc)
        return {"pass": None, "terms": terms, "error": str(exc)}

    terms["orphan_cgm_edge_endpoints"] = orphan_endpoints
    terms["orphan_cgm_edge_signal_refs"] = orphan_signal_refs
    passed = all(presence.values()) and orphan_endpoints == 0 and orphan_signal_refs == 0
    return {"pass": passed, "terms": terms, "error": None}


# ── F-09 · trap 2 — narration leak into the deterministic base ────────────────
# The documented trap is MSR_UCN_CONTAMINATION_AUDIT_v1_0.md §3 C3/C4:
# deliberation and interpretive verdict prose committed INTO the fields that are
# supposed to hold settled deterministic fact.
#
# HONEST BOUNDS (stated here so the detector cannot overclaim, per the #840
# lint precedent): this is a LEXICAL marker scan over three deterministic text
# surfaces. It detects the C3/C4 phrasings enumerated below; it does NOT and
# cannot detect semantically interpretive prose that avoids every marker. A
# zero from this detector means "no enumerated marker present", not "no
# contamination". The marker list ships in the scorecard notes so a consumer can
# see exactly what was measured.
NARRATION_LEAK_MARKERS: tuple[str, ...] = (
    # C3 — deliberation committed into the factual base
    "wait:", "but wait", "re-reading", "rereading", "corrected:", "correction:",
    "invalidated", "reconciliation:", "let me ", "i think ", "on reflection",
    "this requires care", "to be verified", "needs verification",
    "todo", "fixme",
    # C4 — interpretive / verdict prose inside a fact field
    "chart's primary finding", "the native who", "working against the chart",
    "this is the chart's", "in my view", "arguably ",
)

_NARRATION_HAYSTACK = (
    "lower(coalesce(signal_summary_text,'') || ' ' || "
    "coalesce(signal_headline_text,'') || ' ' || "
    "coalesce(configuration_jsonb::text,''))"
)

_NARRATION_LEAK_SQL = f"""
SELECT count(*) FROM bodha_msr_signals
 WHERE chart_id = %s AND {_NARRATION_HAYSTACK} LIKE ANY (%s)
"""

_NARRATION_LEAK_PER_MARKER_SQL = f"""
SELECT count(*) FROM bodha_msr_signals
 WHERE chart_id = %s AND {_NARRATION_HAYSTACK} LIKE %s
"""


def count_narration_leaks(conn: Any, chart_id: str) -> dict:
    """REAL trap-2 detector: lexical scan for C3/C4 contamination markers.

    Returns {"count": int|None, "terms": {...}, "error": str|None}. `count` is
    None when the scan could not run — the caller must then NOT write a zero
    (the column is NOT NULL, so the caller raises rather than storing a clean
    default; see the writer body).

    Can-fail: set any signal's `signal_summary_text` to a string containing
    "Corrected:" — the count goes non-zero.
    """
    patterns = [f"%{m}%" for m in NARRATION_LEAK_MARKERS]
    try:
        total = _count_one(conn, _NARRATION_LEAK_SQL, [chart_id, patterns])
    except Exception as exc:
        logger.warning("[bo_pramana_mapa] narration-leak detector unevaluable: %s", exc)
        return {"count": None, "terms": {}, "error": str(exc)}

    terms: dict[str, Any] = {
        "markers_scanned": list(NARRATION_LEAK_MARKERS),
        "fields_scanned": ["signal_summary_text", "signal_headline_text", "configuration_jsonb"],
        "detector_class": "lexical_marker_scan",
    }
    if total:
        fired: dict[str, int] = {}
        for marker in NARRATION_LEAK_MARKERS:
            try:
                n = _count_one(conn, _NARRATION_LEAK_PER_MARKER_SQL, [chart_id, f"%{marker}%"])
            except Exception:
                continue
            if n:
                fired[marker] = n
        terms["markers_fired"] = fired
        logger.warning(
            "[bo_pramana_mapa] trap2: %d signals carry narration-leak markers %s (chart_id=%s)",
            total, sorted(fired), chart_id,
        )
    return {"count": total, "terms": terms, "error": None}


# ── F-10 · divergent-flagged count ────────────────────────────────────────────
# Two disjoint, independently observable populations:
#   (a) signals a writer explicitly stamped `divergent_flagged`;
#   (b) VERIFICATION-TIER INVERSION — a signal claiming a stronger verification
#       tier than ANY L1 chart_facts row it cites. That is the §N.5 authority
#       inversion measured by AGREEMENT rather than by array presence (which is
#       what trap1_authority_inversion_count measures, and all it measures).
# Signals whose cited facts all carry a NULL/unknown status are EXCLUDED — an
# unknown L1 tier cannot establish divergence, and counting it would manufacture
# a red the same way the old literal manufactured a green.
_VERIFICATION_TIER_RANKS: list[tuple[str, int]] = [
    ("two_pass_verified", 3),
    ("classical_match", 2),
    ("single_pass", 2),
    ("pass", 2),               # legacy lowercase literal (register F-38) — not top tier
    ("documented_approximation", 1),
    ("single", 1),
    ("divergent_flagged", 0),
]

_EXPLICIT_DIVERGENT_SQL = """
SELECT count(*) FROM bodha_msr_signals
 WHERE chart_id = %s AND verification_pass_status = 'divergent_flagged'
"""

_TIER_INVERSION_SQL = """
WITH rank_map(status, rk) AS (
  SELECT * FROM unnest(%s::text[], %s::int[])
), sig AS (
  SELECT signal_id, verification_pass_status, constituent_facts_array
    FROM bodha_msr_signals
   WHERE chart_id = %s AND verification_pass_status IS DISTINCT FROM 'divergent_flagged'
), fact_rank AS (
  SELECT s.signal_id,
         max(COALESCE(fr.rk, -1)) AS max_fact_rk,
         count(cf.fact_id)        AS resolved_facts
    FROM sig s
    CROSS JOIN LATERAL unnest(s.constituent_facts_array) AS r(ref)
    JOIN chart_facts cf ON cf.fact_id = r.ref
    LEFT JOIN rank_map fr ON fr.status = cf.verification_pass_status
   GROUP BY s.signal_id
)
SELECT count(*)
  FROM sig s
  JOIN fact_rank f ON f.signal_id = s.signal_id
  LEFT JOIN rank_map sr ON sr.status = s.verification_pass_status
 WHERE f.resolved_facts > 0
   AND f.max_fact_rk >= 0
   AND COALESCE(sr.rk, -1) > f.max_fact_rk
"""


def count_divergent_signals(conn: Any, chart_id: str) -> dict:
    """REAL divergence detector. Returns {"count": int|None, "terms", "error"}.

    Can-fail (term b): set one signal's `verification_pass_status` to
    'two_pass_verified' while a chart_facts row it cites carries
    'documented_approximation' — the count goes non-zero.
    Can-fail (term a): stamp any signal 'divergent_flagged'.
    """
    statuses = [s for s, _ in _VERIFICATION_TIER_RANKS]
    ranks = [r for _, r in _VERIFICATION_TIER_RANKS]
    terms: dict[str, Any] = {"tier_ranks": dict(_VERIFICATION_TIER_RANKS)}
    try:
        explicit = _count_one(conn, _EXPLICIT_DIVERGENT_SQL, [chart_id])
        inversion = _count_one(conn, _TIER_INVERSION_SQL, [statuses, ranks, chart_id])
    except Exception as exc:
        logger.warning("[bo_pramana_mapa] divergence detector unevaluable: %s", exc)
        return {"count": None, "terms": terms, "error": str(exc)}

    terms["explicitly_stamped_divergent"] = explicit
    terms["l1_verification_tier_inversion"] = inversion
    total = explicit + inversion
    if total:
        logger.warning(
            "[bo_pramana_mapa] divergence: %d signals (explicit=%d, tier_inversion=%d) chart_id=%s",
            total, explicit, inversion, chart_id,
        )
    return {"count": total, "terms": terms, "error": None}


@register("bo_pramana_mapa")
class BoPramanaMapa(WriterBase):
    """bo_pramana_mapa: global synthesis quality scorecard + MV refresh."""
    asset_id = "bo_pramana_mapa"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_scorecard
        from bodha_writers.formulas import (
            VERSION_SALIENCE_FORMULA, VERSION_LINKAGE_FORMULA,
            VERSION_RESONANCE_FORMULA, VERSION_CONVERGENCE_FORMULA,
        )

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            logger.info("[bo_pramana_mapa dry_run] chart_id=%s", chart_id)
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes="dry_run")

        # ── Row counts ────────────────────────────────────────────────────────
        msr_count  = _count_one(conn, "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = %s", [chart_id])
        if msr_count == 0:
            raise RuntimeError(
                f"[bo_pramana_mapa] G3: chart_id={chart_id} — bodha_msr_signals is empty; "
                "upstream Bodha writers (bo_laksana) must succeed before scorecard can run"
            )
        cdlm_count = _count_one(conn, "SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = %s", [chart_id])
        node_count = _count_one(conn, "SELECT count(*) FROM bodha_cgm_nodes WHERE chart_id = %s", [chart_id])
        edge_count = _count_one(conn, "SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = %s", [chart_id])
        res_count  = _count_one(conn, "SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = %s", [chart_id])
        presc_count= _count_one(conn, "SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = %s", [chart_id])
        emb_count  = _count_one(conn, "SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id = %s", [chart_id])
        conv_count = _count_one(conn, "SELECT count(*) FROM bodha_convergence WHERE chart_id = %s", [chart_id])
        contr_count= _count_one(conn, "SELECT count(*) FROM bodha_contradictions WHERE chart_id = %s", [chart_id])

        # ── Quality metrics ───────────────────────────────────────────────────
        two_pass = _count_one(
            conn,
            "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = %s AND verification_pass_status = 'two_pass_verified'",
            [chart_id],
        )
        doc_approx = _count_one(
            conn,
            "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = %s AND verification_pass_status = 'documented_approximation'",
            [chart_id],
        )
        has_citation = _count_one(
            conn,
            "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = %s AND citation_ref IS NOT NULL",
            [chart_id],
        )

        two_pass_pct  = round(two_pass / msr_count * 100, 2) if msr_count > 0 else None
        doc_approx_pct= round(doc_approx / msr_count * 100, 2) if msr_count > 0 else None
        citation_pct  = round(has_citation / msr_count * 100, 2) if msr_count > 0 else None

        # Trap 1: check if MSR signals have constituent_facts_array set (non-empty)
        # Authority inversion = signals with constituent_facts_array IS NULL or empty
        trap1_count = _count_one(
            conn,
            """SELECT count(*) FROM bodha_msr_signals
               WHERE chart_id = %s AND (constituent_facts_array IS NULL OR array_length(constituent_facts_array,1) IS NULL)""",
            [chart_id],
        )

        # ── MC-001 (ŚODHANA T2, item 3): REAL unresolved-constituent count ──────
        # The field `unresolved_constituent_facts_count` must measure how many
        # constituent fact_id REFERENCES fail to resolve against live chart_facts —
        # NOT how many signals have a missing/empty array (that is trap1_count above,
        # correctly named trap1_authority_inversion_count). The prior writer stored
        # trap1_count here, so a chart whose signals all HAVE arrays but whose members
        # are ALL orphaned (the live MC-001 case: 100% of 71,430 refs orphaned after an
        # L1 delete-then-insert rebuild changed every build_id-embedded fact_id) reported
        # unresolved_constituent_facts_count = 0 — a GA.1 stored-vs-live contradiction.
        # Derive the true live orphan count via a LEFT JOIN against chart_facts.
        orphan_row = conn.execute(
            """SELECT
                 count(*)                                   AS total_refs,
                 count(*) FILTER (WHERE cf.fact_id IS NULL)  AS orphaned_refs
               FROM (
                 SELECT unnest(constituent_facts_array) AS fid
                 FROM bodha_msr_signals
                 WHERE chart_id = %s AND constituent_facts_array IS NOT NULL
               ) refs
               LEFT JOIN chart_facts cf ON cf.fact_id = refs.fid""",
            [chart_id],
        ).fetchone()
        if orphan_row is None:
            total_constituent_refs = 0
            orphaned_constituent_refs = 0
        elif isinstance(orphan_row, (tuple, list)):
            total_constituent_refs = int(orphan_row[0] or 0)
            orphaned_constituent_refs = int(orphan_row[1] or 0)
        else:
            total_constituent_refs = int(orphan_row.get("total_refs", 0) or 0)
            orphaned_constituent_refs = int(orphan_row.get("orphaned_refs", 0) or 0)
        constituent_orphan_pct = (
            round(100.0 * orphaned_constituent_refs / total_constituent_refs, 2)
            if total_constituent_refs > 0 else 0.0
        )
        if orphaned_constituent_refs > 0:
            logger.warning(
                "[bo_pramana_mapa] MC-001: %d/%d constituent refs orphaned (%.2f%%) "
                "against live chart_facts for chart_id=%s — Bodha↔L1 linkage is stale.",
                orphaned_constituent_refs, total_constituent_refs, constituent_orphan_pct, chart_id,
            )

        # Formula versions
        sal_ver  = _formula_version(conn, chart_id, "salience_formula_version", "bodha_msr_signals")
        link_ver = _formula_version(conn, chart_id, "linkage_formula_version", "bodha_cdlm_cells")
        res_ver  = _formula_version(conn, chart_id, "resonance_score_formula_version", "bodha_rm_resonances")
        conv_ver = _formula_version(conn, chart_id, "convergence_formula_version", "bodha_convergence")

        # ── §N.8 earned-signal detectors (lane B-N8-FIX; register F-07…F-10) ──
        # Each of the four fields below previously carried a proxy, a tautology,
        # or a literal 0. They now carry a real detector whose False/non-zero
        # branch is reachable from real DB state; see the detector docstrings for
        # the exact mutation that makes each one fail.
        lel_result      = detect_lel_leak(conn, chart_id)
        pillars_result  = detect_pillar_reachability(
            conn, chart_id, msr_count, cdlm_count, node_count, edge_count, res_count,
        )
        trap2_result    = count_narration_leaks(conn, chart_id)
        divergent_result = count_divergent_signals(conn, chart_id)

        # The two INT columns are NOT NULL in the schema, so "unknown" cannot be
        # stored as NULL there. Storing 0 for an unevaluable detector would
        # re-create exactly the clean-looking default this lane removed — so the
        # writer HALTS instead. A build that cannot measure a trap does not get to
        # report the trap as clean.
        if trap2_result["count"] is None:
            raise RuntimeError(
                "[bo_pramana_mapa] trap2 narration-leak detector could not be evaluated "
                f"({trap2_result['error']}); refusing to store a clean-looking 0 "
                "(§N.8 — a signal with no detector behind it is not a green)"
            )
        if divergent_result["count"] is None:
            raise RuntimeError(
                "[bo_pramana_mapa] divergence detector could not be evaluated "
                f"({divergent_result['error']}); refusing to store a clean-looking 0 "
                "(§N.8 — a signal with no detector behind it is not a green)"
            )

        # L1 assets referenced — real distinct count/array of source_l1_asset
        # values on this chart's bodha_msr_signals (previously hardcoded to a
        # degenerate `1 if msr_count>0 else 0` with an always-empty array; per
        # bo_laksana's depends_on this should be up to 9 distinct L1 assets).
        with conn.cursor() as l1_cur:
            l1_cur.execute(
                """SELECT DISTINCT source_l1_asset FROM bodha_msr_signals
                   WHERE chart_id = %s AND source_l1_asset IS NOT NULL
                   ORDER BY source_l1_asset""",
                [chart_id],
            )
            # conn's default row_factory is dict_row — index by column name.
            l1_assets_projected_array = [r["source_l1_asset"] for r in l1_cur.fetchall()]
        l1_assets_projected = len(l1_assets_projected_array)

        scorecard = {
            "scorecard_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "build_id": build_id,
            "scored_at": now,
            "msr_signal_count": msr_count,
            "cdlm_cell_count": cdlm_count,
            "cgm_node_count": node_count,
            "cgm_edge_count": edge_count,
            "rm_resonance_count": res_count,
            "rm_prescription_count": presc_count,
            "embedding_count": emb_count,
            "convergence_count": conv_count,
            "contradiction_count": contr_count,
            # F-10 (was a literal 0 with no detector): real count = explicitly
            # stamped 'divergent_flagged' signals ∪ signals claiming a stronger
            # verification tier than any L1 fact they cite. See
            # count_divergent_signals() for the can-fail mutation.
            "divergent_flagged_count": divergent_result["count"],
            "two_pass_verified_pct": two_pass_pct,
            "documented_approximation_pct": doc_approx_pct,
            "msr_no_threshold_drop_flag": msr_count > 0,
            "msr_citation_ref_coverage_pct": citation_pct,
            "salience_formula_version": sal_ver or VERSION_SALIENCE_FORMULA,
            "linkage_formula_version": link_ver or VERSION_LINKAGE_FORMULA,
            "resonance_formula_version": res_ver or VERSION_RESONANCE_FORMULA,
            "convergence_formula_version": conv_ver or VERSION_CONVERGENCE_FORMULA,
            "centrality_formula_version": None,
            "trap1_authority_inversion_count": trap1_count,
            # F-09 (was a literal 0 with no detector): real lexical scan for the
            # documented C3/C4 contamination markers over the three deterministic
            # text surfaces. Detector bounds are stated in count_narration_leaks()
            # and shipped in `notes.n8_detectors` so a consumer can see what was
            # actually measured.
            "trap2_narration_leak_count": trap2_result["count"],
            # ── 8 grounding columns (were missing from INSERT) ────────────────
            # MC-001 (item 3): REAL live orphan count (refs that don't resolve
            # against chart_facts), not trap1_count (missing-array count).
            "unresolved_constituent_facts_count": orphaned_constituent_refs,
            "l1_assets_projected_count": l1_assets_projected,
            "l1_assets_projected_array": l1_assets_projected_array,
            # F-07 (was `trap1_count == 0`, a proxy that never read LEL data):
            # real three-term LEL scan. None when unevaluable — never True.
            "lel_zero_leak_pass": lel_result["pass"],
            # These three gates have no real detector implemented yet. Previously
            # hardcoded to True, which is indistinguishable from a genuinely-passed
            # verification. NULL is the honest "not yet computed" value — a
            # scorecard consumer must not read a NULL gate as a clean pass.
            "no_pre_answer_pass": None,
            # F-08 (was `msr_count > 0`, unreachable-false because msr_count == 0
            # already raised ~160 lines above): real presence + graph-reachability
            # gate. None when unevaluable — never True.
            "pillars_meet_reachability_pass": pillars_result["pass"],
            "ledger_independence_pass": None,
            "discovery_not_fabricated_pass": None,
            "notes": json.dumps({
                "engine_version": ENGINE_VERSION,
                "counts": {
                    "msr": msr_count, "cdlm": cdlm_count, "nodes": node_count,
                    "edges": edge_count, "resonances": res_count,
                    "prescriptions": presc_count, "embeddings": emb_count,
                    "convergence": conv_count, "contradictions": contr_count,
                },
                # MC-001: live constituent-linkage health at scorecard time. NOTE these
                # values are a build-time snapshot — a later L1 rebuild can orphan them,
                # so serve-time surfaces MUST re-derive live (see bodha_l1_linkage.ts) and
                # never trust the stored unresolved_constituent_facts_count alone.
                "constituent_linkage": {
                    "total_refs": total_constituent_refs,
                    "orphaned_refs": orphaned_constituent_refs,
                    "orphan_pct": constituent_orphan_pct,
                    "trap1_missing_array_count": trap1_count,
                },
                # §N.8: every gate/count above ships its per-term breakdown so a
                # consumer can see WHAT was measured rather than trusting a bare
                # boolean. `pass: null` / an `error` key means "not measured" —
                # it must never be read as a clean result.
                "n8_detectors": {
                    "lel_zero_leak_pass": lel_result,
                    "pillars_meet_reachability_pass": pillars_result,
                    "trap2_narration_leak_count": trap2_result,
                    "divergent_flagged_count": divergent_result,
                },
            }),
        }

        replace_prior_scorecard(conn, chart_id, build_id)
        conn.execute(_SCORECARD_INSERT, scorecard)
        logger.info(
            "[bo_pramana_mapa] scorecard written: trap1=%d msr=%d "
            "lel_zero_leak=%s pillars_reachable=%s trap2_leaks=%d divergent=%d",
            trap1_count, msr_count,
            lel_result["pass"], pillars_result["pass"],
            trap2_result["count"], divergent_result["count"],
        )

        # ── Materialised view refresh (G5: all 8 Bodha MVs) ─────────────────
        for mv in [
            # MSR MVs (3)
            "mv_msr_top_signals_per_chart",
            "mv_msr_recurring_patterns_per_chart",
            "mv_msr_domain_summary",
            # CDLM MVs (5) — previously not refreshed; added by G5 fix
            "mv_cdlm_static_summary",
            "mv_cdlm_top_K_links_per_chart",
            "mv_cdlm_per_tradition_summary",
            "mv_cdlm_dasha_window_lookup",
            "mv_cdlm_pattern_summary",
        ]:
            _refresh_mv(conn, mv)

        return WriterResult(asset_id=self.asset_id, rows_inserted=1,
                            notes=f"msr={msr_count} cdlm={cdlm_count} nodes={node_count} trap1={trap1_count}")

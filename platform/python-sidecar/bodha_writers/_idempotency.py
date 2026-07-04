"""Idempotency helpers for L2 Bodha writers — per-chart DELETE-then-INSERT.

Every Bodha writer calls the relevant helper immediately before its INSERT,
on the same conn (ctx.db_conn), in the same transaction/savepoint the
orchestrator manages.  This makes any sub-step safe to re-run: a rebuild
REPLACES, never accretes.

Pattern mirrors ga_writers/_idempotency.py exactly.

`conn` is a psycopg connection/cursor exposing .execute(sql, params) returning
a cursor with .rowcount.  Writers never commit or close it.
"""
from __future__ import annotations

from typing import Any, Iterable


def _distinct(rows: Iterable[dict], key: str) -> list:
    return sorted({r[key] for r in rows if r.get(key) is not None})


def _delete(conn: Any, sql: str, params: list) -> int:
    cur = conn.execute(sql, params)
    return getattr(cur, "rowcount", 0) or 0


# ──────────────────────────────────────────────────────────────────────────────
# A10 — bodha_msr_signals
# Natural key scope: (chart_id, ayanamsha_id, signal_type_id)
# ──────────────────────────────────────────────────────────────────────────────

def replace_prior_msr_signals(conn: Any, rows: list[dict]) -> int:
    """Delete prior bodha_msr_signals rows for the (chart_id, ayanamsha_id,
    signal_type_id) scope present in `rows`."""
    if not rows:
        return 0
    signal_types = _distinct(rows, "signal_type_id")
    ayanamshas = _distinct(rows, "ayanamsha_id")
    if not ayanamshas:
        return 0
    if not signal_types:
        return 0
    deleted = 0
    for cid in _distinct(rows, "chart_id"):
        # Delete all child tables referencing these signals first (FKs are NO ACTION).
        child_scope = (
            "SELECT signal_id FROM bodha_msr_signals"
            " WHERE chart_id = %s AND signal_type_id = ANY(%s) AND ayanamsha_id = ANY(%s)"
        )
        _delete(conn,
                f"DELETE FROM bodha_signal_embeddings WHERE signal_id IN ({child_scope})",
                [cid, signal_types, ayanamshas])
        _delete(conn,
                f"DELETE FROM bodha_contradictions"
                f" WHERE chart_id = %s AND (signal_a_id IN ({child_scope}) OR signal_b_id IN ({child_scope}))",
                [cid, cid, signal_types, ayanamshas, cid, signal_types, ayanamshas])
        sql = ("DELETE FROM bodha_msr_signals "
               "WHERE chart_id = %s AND signal_type_id = ANY(%s)")
        params: list = [cid, signal_types]
        if ayanamshas:
            sql += " AND ayanamsha_id = ANY(%s)"
            params.append(ayanamshas)
        deleted += _delete(conn, sql, params)
    return deleted


def replace_prior_msr_for_chart(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    """Wipe ALL bodha_msr_signals for a (chart_id, ayanamsha_id) pair.
    Used when a full per-ayanamsha rebuild replaces everything."""
    # Delete all child tables referencing bodha_msr_signals first (all FKs are NO ACTION).
    _delete(
        conn,
        "DELETE FROM bodha_signal_embeddings WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )
    _delete(
        conn,
        "DELETE FROM bodha_contradictions WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )
    return _delete(
        conn,
        "DELETE FROM bodha_msr_signals WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


# ──────────────────────────────────────────────────────────────────────────────
# §13.1 — bodha_contradictions
# ──────────────────────────────────────────────────────────────────────────────

def replace_prior_contradictions(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    return _delete(
        conn,
        "DELETE FROM bodha_contradictions WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


# ──────────────────────────────────────────────────────────────────────────────
# A11 — CDLM tables
# Scope: (chart_id, ayanamsha_id, snapshot_type [, system, lords, tradition])
# Most CDLM helpers accept a snapshot_type to allow partial rebuilds.
# ──────────────────────────────────────────────────────────────────────────────

def replace_prior_cdlm_cells(conn: Any, chart_id: str, ayanamsha_id: str,
                              snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_cdlm_cells WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_cdlm_cells WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cdlm_domain_rollups(conn: Any, chart_id: str, ayanamsha_id: str,
                                       snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_cdlm_domain_rollups WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_cdlm_domain_rollups WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cdlm_chart_summary(conn: Any, chart_id: str, ayanamsha_id: str,
                                      snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_cdlm_chart_summary WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_cdlm_chart_summary WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cdlm_pattern_clusters(conn: Any, chart_id: str, ayanamsha_id: str,
                                         snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_cdlm_pattern_clusters WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_cdlm_pattern_clusters WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cdlm_evolution_gradients(conn: Any, chart_id: str, ayanamsha_id: str,
                                            dynamic_system_id: str | None = None) -> int:
    if dynamic_system_id:
        return _delete(
            conn,
            "DELETE FROM bodha_cdlm_evolution_gradients WHERE chart_id = %s AND ayanamsha_id = %s AND dynamic_system_id = %s",
            [chart_id, ayanamsha_id, dynamic_system_id],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_cdlm_evolution_gradients WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_convergence(conn: Any, chart_id: str, ayanamsha_id: str,
                               snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_convergence WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_convergence WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


# ──────────────────────────────────────────────────────────────────────────────
# A12 — CGM tables
# ──────────────────────────────────────────────────────────────────────────────

def replace_prior_cgm_nodes(conn: Any, chart_id: str, ayanamsha_id: str,
                             snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_cgm_nodes WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_cgm_nodes WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cgm_edges(conn: Any, chart_id: str, ayanamsha_id: str,
                             snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_cgm_edges WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_cgm_edges WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cgm_sub_graphs(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    return _delete(
        conn,
        "DELETE FROM bodha_cgm_sub_graphs WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cgm_motifs(conn: Any, chart_id: str, ayanamsha_id: str,
                              snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_cgm_motifs WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_cgm_motifs WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cgm_topology_summary(conn: Any, chart_id: str, ayanamsha_id: str,
                                        snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_cgm_chart_topology_summary WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_cgm_chart_topology_summary WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cgm_paths(conn: Any, chart_id: str, ayanamsha_id: str,
                             snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_cgm_paths WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_cgm_paths WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


# ──────────────────────────────────────────────────────────────────────────────
# A13 — RM tables
# ──────────────────────────────────────────────────────────────────────────────

def replace_prior_rm_resonances(conn: Any, chart_id: str, ayanamsha_id: str,
                                 snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_rm_resonances WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_rm_resonances WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_rm_prescriptions(conn: Any, chart_id: str, ayanamsha_id: str,
                                    snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_rm_remedy_prescriptions WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_rm_remedy_prescriptions WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_rm_dasha_windowed(conn: Any, chart_id: str, ayanamsha_id: str,
                                     dasha_system: str | None = None) -> int:
    if dasha_system:
        return _delete(
            conn,
            "DELETE FROM bodha_rm_dasha_windowed_prescriptions WHERE chart_id = %s AND ayanamsha_id = %s AND dasha_system = %s",
            [chart_id, ayanamsha_id, dasha_system],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_rm_dasha_windowed_prescriptions WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_rm_dosha_bundles(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    return _delete(
        conn,
        "DELETE FROM bodha_rm_dosha_remedy_bundles WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_rm_pattern_remedies(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    return _delete(
        conn,
        "DELETE FROM bodha_rm_pattern_remedies WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_rm_chart_summary(conn: Any, chart_id: str, ayanamsha_id: str,
                                    snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM bodha_rm_chart_summary WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM bodha_rm_chart_summary WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


# ──────────────────────────────────────────────────────────────────────────────
# bo_samskara — bodha_signal_embeddings
# ──────────────────────────────────────────────────────────────────────────────

def replace_prior_signal_embeddings(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    return _delete(
        conn,
        "DELETE FROM bodha_signal_embeddings WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


# ──────────────────────────────────────────────────────────────────────────────
# bo_pramana_mapa — synthesis_quality_scorecard  (global; keyed by chart + build)
# ──────────────────────────────────────────────────────────────────────────────

def replace_prior_scorecard(conn: Any, chart_id: str, build_id: str) -> int:
    """Delete ALL prior scorecard rows for this chart (not just matching build_id).
    Scoping to chart_id only ensures N rebuilds leave exactly 1 scorecard row.
    build_id is kept in the signature for call-site compatibility but is not used."""
    return _delete(
        conn,
        "DELETE FROM synthesis_quality_scorecard WHERE chart_id = %s",
        [chart_id],
    )

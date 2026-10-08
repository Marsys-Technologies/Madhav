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

from typing import Any, Iterable, Mapping

from ga_writers.data_plane_contracts import data_plane_build_path_enabled


def _distinct(rows: Iterable[dict], key: str) -> list:
    return sorted({r[key] for r in rows if r.get(key) is not None})


def _delete(conn: Any, sql: str, params: list) -> int:
    # Disable the per-statement timeout for this DELETE. Bodha idempotency
    # deletes (esp. replace_prior_msr_signals child-cascades and
    # replace_prior_msr_for_chart) can exceed the DB role's default
    # statement_timeout (25-30s, sized for OLTP) on large charts — the
    # bo_laksana native rebuild hit psycopg.errors.QueryCanceled here.
    # SET LOCAL scopes to the orchestrator-managed transaction/savepoint
    # (writers never commit/close conn), so it self-reverts at txn end.
    # Mirrors the ka_* writer precedent (PR 422). Idempotent + cheap to
    # repeat per _delete call.
    conn.execute("SET LOCAL statement_timeout = 0")
    cur = conn.execute(sql, params)
    return getattr(cur, "rowcount", 0) or 0


class MsrReplacementBlocked(RuntimeError):
    """An MSR replacement would cascade into rows owned by a later layer."""


def _msr_child_scope_table() -> str:
    """Table the child-scope sub-selects read the signal ids from.

    With the data-plane build path on, ``bind_l2_exact_inputs`` has created a
    ``pg_temp.bodha_msr_signals`` shadow holding the bound input rows. With it
    off (N-165) no shadow exists, and the live table is what is being replaced.
    """
    if data_plane_build_path_enabled():
        return "pg_temp.bodha_msr_signals"
    return "public.bodha_msr_signals"


_MSR_FK_SQL = """
SELECT n.nspname AS schema_name, c.relname AS table_name,
       a.attname AS column_name, cardinality(k.conkey) AS key_count,
       ra.attname AS referenced_column
FROM pg_constraint k
JOIN pg_class c ON c.oid = k.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attribute a ON a.attrelid = k.conrelid AND a.attnum = k.conkey[1]
LEFT JOIN pg_attribute ra ON ra.attrelid = k.confrelid AND ra.attnum = k.confkey[1]
WHERE k.contype = 'f' AND k.confrelid = 'public.bodha_msr_signals'::regclass
ORDER BY n.nspname, c.relname, k.conname
"""

_FK_COLUMNS = ("schema_name", "table_name", "column_name", "key_count", "referenced_column")

# L2's own children, which the replace helpers delete explicitly before the MSR rows.
_OWN_LAYER_MSR_CHILDREN = frozenset({
    ("public", "bodha_signal_embeddings"),
    ("public", "bodha_contradictions"),
})


def _fk_record(row: Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)
    return dict(zip(_FK_COLUMNS, row))


def _assert_msr_delete_safe(
    conn: Any,
    *,
    chart_id: str,
    ayanamsha_ids: list[str] | None = None,
    signal_type_ids: list[str] | None = None,
    signal_type_classes: list[str] | None = None,
) -> None:
    """Fail before an MSR replacement could mutate a later layer.

    Data-plane build path on: delegates to the protected-owner function, which
    also records the delete receipt. Off (N-165): there is no admitted context
    for that function (it would raise), so the same dependency check runs as
    read-only SQL against the live tables -- every foreign key onto
    ``bodha_msr_signals`` is discovered from the catalogue and, unless it is one
    of L2's own children, any dependent row inside the exact replacement scope
    blocks the replacement. The scope is the chart plus the ayanamsha / signal
    type / class filters the DELETE itself will use (the function's extra
    producer filter needs the admitted asset, which does not exist here; the
    replace helpers' filters already confine the DELETE to the caller's rows).
    No lock and no receipt: nothing downstream needs them.
    """
    module = type(conn).__module__.split(".", 1)[0]
    if module != "psycopg" and getattr(conn, "_l2_contract_test_double", False) is not True:
        return
    if data_plane_build_path_enabled():
        conn.execute(
            """SELECT public.assert_l2_msr_delete_safe(
                   %s::uuid, %s::text[], %s::text[], %s::text[]
                 )""",
            [chart_id, ayanamsha_ids, signal_type_ids, signal_type_classes],
        )
        return
    from psycopg import sql as _sql

    for raw in conn.execute(_MSR_FK_SQL).fetchall():
        fk = _fk_record(raw)
        if (fk["schema_name"], fk["table_name"]) in _OWN_LAYER_MSR_CHILDREN:
            continue
        if (fk["key_count"] != 1 or fk["referenced_column"] != "signal_id"
                or fk["column_name"] is None):
            raise MsrReplacementBlocked(
                f"unsupported cross-layer MSR foreign key {fk['schema_name']}.{fk['table_name']}"
            )
        query = _sql.SQL(
            "SELECT EXISTS ("
            " SELECT 1 FROM {tbl} d"
            " JOIN public.bodha_msr_signals s ON d.{col} = s.signal_id"
            " WHERE s.chart_id = %s::uuid"
            "   AND (%s::text[] IS NULL OR s.ayanamsha_id = ANY(%s::text[]))"
            "   AND (%s::text[] IS NULL OR s.signal_type_id = ANY(%s::text[]))"
            "   AND (%s::text[] IS NULL OR s.signal_type_class = ANY(%s::text[]))"
            ")"
        ).format(
            tbl=_sql.Identifier(fk["schema_name"], fk["table_name"]),
            col=_sql.Identifier(fk["column_name"]),
        )
        row = conn.execute(
            query,
            [chart_id, ayanamsha_ids, ayanamsha_ids, signal_type_ids,
             signal_type_ids, signal_type_classes, signal_type_classes],
        ).fetchone()
        exists = row[next(iter(row))] if isinstance(row, Mapping) else row[0]
        if exists:
            raise MsrReplacementBlocked(
                "L2 MSR replacement blocked by cross-layer dependent rows in "
                f"{fk['schema_name']}.{fk['table_name']}"
            )


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
        _assert_msr_delete_safe(
            conn,
            chart_id=cid,
            ayanamsha_ids=ayanamshas,
            signal_type_ids=signal_types,
        )
        # ⚠ EVERY FK onto bodha_msr_signals IS `ON DELETE CASCADE` — NOT `NO ACTION`.
        #
        # This comment previously said "FKs are NO ACTION". It was false, and it is the
        # single line that propagated a campaign-wide misreading: adjudication #1748
        # concluded from it that no rebuild hold was warranted, and that conclusion was
        # ratified before #1770 checked pg_constraint directly. Verified:
        # `SELECT conrelid::regclass, confdeltype FROM pg_constraint
        #   WHERE contype='f' AND confrelid='bodha_msr_signals'::regclass`
        # returns confdeltype='c' (CASCADE) for all eight.
        #
        # The explicit deletes below cover only this layer's OWN children
        # (bodha_signal_embeddings, bodha_contradictions). Everything else Postgres
        # removes silently, and the closure crosses two more layers:
        #
        #   bodha_msr_signals → kala_activation      672,551   (L3)
        #                     → kala_convergence      35,365   (L3) → phala_anchors (L4)
        #                                                              → phala_pramana
        #                                                              → phala_sankrama
        #                                                              → phala_sodhana
        #                                                              → phala_suddha_sodhana
        #                     → kala_darshana          1,500   (L3)
        #                     → kala_obstruction       1,283   (L3)
        #                     → kala_bhavishya           200   (L3)
        #
        # Measured transitive blast radius of one MSR rebuild: 864,733 rows across 12
        # tables in three layers, including phala_anchors — the prediction-provenance
        # table D-CND-04 holds ph_nimitta rebuilds to protect. An L2 rebuild reaches it
        # through the wall while that hold guards the front door.
        #
        # D-CND-15 (standing, #1770): before any rebuild_only dispatch, the owning
        # session must enumerate the transitive CASCADE closure of every table its
        # writer deletes from, and HOLD if it crosses a layer boundary. A §N.3
        # delete-then-insert is "in-layer" only if the FKs say so. Here they said the
        # opposite of this comment.
        child_scope = (
            f"SELECT signal_id FROM {_msr_child_scope_table()}"
            " WHERE chart_id = %s AND signal_type_id = ANY(%s) AND ayanamsha_id = ANY(%s)"
        )
        _delete(conn,
                f"DELETE FROM public.bodha_signal_embeddings WHERE signal_id IN ({child_scope})",
                [cid, signal_types, ayanamshas])
        _delete(conn,
                f"DELETE FROM public.bodha_contradictions"
                f" WHERE chart_id = %s AND (signal_a_id IN ({child_scope}) OR signal_b_id IN ({child_scope}))",
                [cid, cid, signal_types, ayanamshas, cid, signal_types, ayanamshas])
        sql = ("DELETE FROM public.bodha_msr_signals "
               "WHERE chart_id = %s AND signal_type_id = ANY(%s)")
        params: list = [cid, signal_types]
        if ayanamshas:
            sql += " AND ayanamsha_id = ANY(%s)"
            params.append(ayanamshas)
        deleted += _delete(conn, sql, params)
    return deleted


def replace_prior_msr_for_chart(conn: Any, chart_id: str, ayanamsha_id: str,
                                 owned_signal_type_classes: list[str]) -> int:
    """Delete prior bodha_msr_signals rows for a (chart_id, ayanamsha_id) pair
    that belong to ONE OF `owned_signal_type_classes` — i.e. exactly the
    signal_type_class values the CALLING writer is known to emit.

    NOT a blanket per-(chart,ayanamsha) wipe. `bodha_msr_signals` is a shared
    table: as of D-1.5b, both bo_laksana (the category-agnostic L1-facts
    projector) and bo_sudarshana (an independent top-level asset that emits
    `sudarshana_agreement` rows from its own narrower idempotency call,
    `replace_prior_msr_signals`) insert into it directly, and nothing prevents
    a future asset from doing the same. Before this fix, this function
    unconditionally deleted ALL rows for the (chart_id, ayanamsha_id) pair —
    correct only under the now-false assumption that bo_laksana was the sole
    writer to the table. That blanket delete silently destroyed
    bo_sudarshana's rows on every bo_laksana rebuild even though
    bo_sudarshana's own `asset_throughput` state kept claiming success
    (state='lit') because bo_sudarshana was never told its data vanished.
    See D-1.5b full-rebuild post-mortem, chart 482012f1, 2026-07-15/16.

    Every caller MUST pass the exact, non-empty list of signal_type_class
    values it owns (see e.g. bo_laksana.py's BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES).
    This keeps the delete scoped to "rows THIS writer produced" rather than
    "all rows for this chart+ayanamsha", regardless of how many other writers
    later start sharing the table.
    """
    if not owned_signal_type_classes:
        raise ValueError(
            "replace_prior_msr_for_chart requires a non-empty "
            "owned_signal_type_classes allowlist — refusing to fall back to a "
            "blanket delete (see D-1.5b bo_sudarshana data-loss postmortem)."
        )
    _assert_msr_delete_safe(
        conn,
        chart_id=chart_id,
        ayanamsha_ids=[ayanamsha_id],
        signal_type_classes=owned_signal_type_classes,
    )
    # Scoped to signal_id via the same owned-classes subquery so child rows belonging
    # to OTHER writers' signals are never touched either.
    #
    # ⚠ These two explicit deletes are NOT the whole story, and the comment that used to
    # stand here said they were. It read "all FKs are NO ACTION". Every FK onto
    # bodha_msr_signals is `ON DELETE CASCADE` (pg_constraint.confdeltype='c', all
    # eight). See the full closure and its measured row counts at the sibling warning in
    # replace_prior_msr_signals above: one MSR rebuild removes 864,733 rows across 12
    # tables in three layers, only 150,126 of which are deleted by the statements below.
    # The rest Postgres removes without a word.
    #
    # A comment asserting the opposite of the schema, directly above code whose safety
    # depends on it, is how adjudication #1748 concluded that no rebuild hold was
    # warranted — and how that conclusion came to be ratified. Corrected under #1770.
    # D-CND-15 applies: enumerate the transitive CASCADE closure before any rebuild
    # dispatch, and hold if it crosses a layer boundary.
    child_scope = (
        f"SELECT signal_id FROM {_msr_child_scope_table()}"
        " WHERE chart_id = %s AND ayanamsha_id = %s AND signal_type_class = ANY(%s)"
    )
    _delete(
        conn,
        f"DELETE FROM public.bodha_signal_embeddings WHERE signal_id IN ({child_scope})",
        [chart_id, ayanamsha_id, owned_signal_type_classes],
    )
    _delete(
        conn,
        f"DELETE FROM public.bodha_contradictions"
        f" WHERE chart_id = %s AND (signal_a_id IN ({child_scope}) OR signal_b_id IN ({child_scope}))",
        [chart_id,
         chart_id, ayanamsha_id, owned_signal_type_classes,
         chart_id, ayanamsha_id, owned_signal_type_classes],
    )
    return _delete(
        conn,
        "DELETE FROM public.bodha_msr_signals"
        " WHERE chart_id = %s AND ayanamsha_id = %s AND signal_type_class = ANY(%s)",
        [chart_id, ayanamsha_id, owned_signal_type_classes],
    )


# ──────────────────────────────────────────────────────────────────────────────
# §13.1 — bodha_contradictions
# ──────────────────────────────────────────────────────────────────────────────

def replace_prior_contradictions(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    return _delete(
        conn,
        "DELETE FROM public.bodha_contradictions WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_grounding_matches(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    """bo_grounding — sole writer of bodha_grounding_matches (migration 897),
    no co-writer sharing, so scope is the whole (chart_id, ayanamsha_id) slice."""
    return _delete(
        conn,
        "DELETE FROM public.bodha_grounding_matches WHERE chart_id = %s AND ayanamsha_id = %s",
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
            "DELETE FROM public.bodha_cdlm_cells WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cdlm_cells WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cdlm_domain_rollups(conn: Any, chart_id: str, ayanamsha_id: str,
                                       snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_cdlm_domain_rollups WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cdlm_domain_rollups WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cdlm_chart_summary(conn: Any, chart_id: str, ayanamsha_id: str,
                                      snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_cdlm_chart_summary WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cdlm_chart_summary WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cdlm_pattern_clusters(conn: Any, chart_id: str, ayanamsha_id: str,
                                         snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_cdlm_pattern_clusters WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cdlm_pattern_clusters WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cdlm_evolution_gradients(conn: Any, chart_id: str, ayanamsha_id: str,
                                            dynamic_system_id: str | None = None) -> int:
    if dynamic_system_id:
        return _delete(
            conn,
            "DELETE FROM public.bodha_cdlm_evolution_gradients WHERE chart_id = %s AND ayanamsha_id = %s AND dynamic_system_id = %s",
            [chart_id, ayanamsha_id, dynamic_system_id],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cdlm_evolution_gradients WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_convergence(conn: Any, chart_id: str, ayanamsha_id: str,
                               snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_convergence WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_convergence WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


# ──────────────────────────────────────────────────────────────────────────────
# A12 — CGM tables
# ──────────────────────────────────────────────────────────────────────────────

def replace_prior_cgm_nodes(conn: Any, chart_id: str, ayanamsha_id: str,
                             snapshot_type: str | None = None) -> int:
    owned_node_types = ["bhava", "domain", "dosha", "graha", "yoga"]
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_cgm_nodes WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s AND node_type = ANY(%s)",
            [chart_id, ayanamsha_id, snapshot_type, owned_node_types],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cgm_nodes WHERE chart_id = %s AND ayanamsha_id = %s AND node_type = ANY(%s)",
        [chart_id, ayanamsha_id, owned_node_types],
    )


def replace_prior_cgm_arudha_special_lagna_nodes(conn: Any, chart_id: str, ayanamsha_id: str,
                                                 snapshot_type: str | None = None) -> int:
    """bo_karanajala's own node types (replace_prior_cgm_nodes deliberately does not own
    them: bo_bimba would otherwise delete nodes it never writes). Deletes the edges that
    reference those nodes first (no FK exists, so no orphan edge may be left behind), then
    the nodes; scoped to (chart_id, ayanamsha_id[, snapshot_type]). Returns nodes deleted."""
    owned = ["arudha", "special_lagna"]
    snap_n = " AND snapshot_type = %s" if snapshot_type else ""
    base = [chart_id, ayanamsha_id] + ([snapshot_type] if snapshot_type else [])
    _delete(
        conn,
        "DELETE FROM public.bodha_cgm_edges WHERE chart_id = %s AND ayanamsha_id = %s"
        " AND (from_node_id IN (SELECT node_id FROM public.bodha_cgm_nodes WHERE chart_id = %s"
        " AND ayanamsha_id = %s" + snap_n + " AND node_type = ANY(%s))"
        " OR to_node_id IN (SELECT node_id FROM public.bodha_cgm_nodes WHERE chart_id = %s"
        " AND ayanamsha_id = %s" + snap_n + " AND node_type = ANY(%s)))",
        [chart_id, ayanamsha_id] + base + [owned] + base + [owned],
    )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cgm_nodes WHERE chart_id = %s AND ayanamsha_id = %s"
        + snap_n + " AND node_type = ANY(%s)",
        base + [owned],
    )


def replace_prior_cgm_edges(conn: Any, chart_id: str, ayanamsha_id: str,
                             snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_cgm_edges WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cgm_edges WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cgm_sub_graphs(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    return _delete(
        conn,
        "DELETE FROM public.bodha_cgm_sub_graphs WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cgm_motifs(conn: Any, chart_id: str, ayanamsha_id: str,
                              snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_cgm_motifs WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cgm_motifs WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cgm_topology_summary(conn: Any, chart_id: str, ayanamsha_id: str,
                                        snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_cgm_chart_topology_summary WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cgm_chart_topology_summary WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_cgm_paths(conn: Any, chart_id: str, ayanamsha_id: str,
                             snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_cgm_paths WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_cgm_paths WHERE chart_id = %s AND ayanamsha_id = %s",
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
            "DELETE FROM public.bodha_rm_resonances WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_rm_resonances WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_rm_prescriptions(conn: Any, chart_id: str, ayanamsha_id: str,
                                    snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_rm_remedy_prescriptions WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_rm_remedy_prescriptions WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_rm_dasha_windowed(conn: Any, chart_id: str, ayanamsha_id: str,
                                     dasha_system: str | None = None) -> int:
    if dasha_system:
        return _delete(
            conn,
            "DELETE FROM public.bodha_rm_dasha_windowed_prescriptions WHERE chart_id = %s AND ayanamsha_id = %s AND dasha_system = %s",
            [chart_id, ayanamsha_id, dasha_system],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_rm_dasha_windowed_prescriptions WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_rm_dosha_bundles(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    return _delete(
        conn,
        "DELETE FROM public.bodha_rm_dosha_remedy_bundles WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_rm_pattern_remedies(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    return _delete(
        conn,
        "DELETE FROM public.bodha_rm_pattern_remedies WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


def replace_prior_rm_chart_summary(conn: Any, chart_id: str, ayanamsha_id: str,
                                    snapshot_type: str | None = None) -> int:
    if snapshot_type:
        return _delete(
            conn,
            "DELETE FROM public.bodha_rm_chart_summary WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s",
            [chart_id, ayanamsha_id, snapshot_type],
        )
    return _delete(
        conn,
        "DELETE FROM public.bodha_rm_chart_summary WHERE chart_id = %s AND ayanamsha_id = %s",
        [chart_id, ayanamsha_id],
    )


# ──────────────────────────────────────────────────────────────────────────────
# bo_samskara — bodha_signal_embeddings
# ──────────────────────────────────────────────────────────────────────────────

def replace_prior_signal_embeddings(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    return _delete(
        conn,
        "DELETE FROM public.bodha_signal_embeddings WHERE chart_id = %s AND ayanamsha_id = %s",
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
        "DELETE FROM public.synthesis_quality_scorecard WHERE chart_id = %s",
        [chart_id],
    )

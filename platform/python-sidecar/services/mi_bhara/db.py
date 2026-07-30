"""
db.py — THE ONLY MODULE IN `services/mi_bhara/` THAT TOUCHES A DATABASE.

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.2–§7.6, §8.3 (the Circularity Guard).

═══════════════════════════════════════════════════════════════════════════════════════════
  WHY EVERY QUERY LIVES IN ONE FILE
═══════════════════════════════════════════════════════════════════════════════════════════
The Circularity Guard's STATIC half is a source census: no module on the stage 0–8 code path
may reference the LEL tables. That census is only as good as its ability to state a whitelist
precisely. Confining stage 9's LEL read to a single named module turns "which files are
allowed to mention `life_events`?" from a judgement call into a one-line answer — and makes
the reverse question, "did an LEL read leak into a computation?", answerable by grep.

Everything else in this package is a pure function of its arguments. That is not tidiness for
its own sake: it is what lets the fitting, skill and GOF mathematics be verified against
closed-form ground truth with no database in the loop at all.

═══════════════════════════════════════════════════════════════════════════════════════════
  THE FROZEN WRITER CONTRACT (CLAUDE.md §N.2)
═══════════════════════════════════════════════════════════════════════════════════════════
Every function here takes a caller-owned connection and NEVER commits, rolls back, or closes
it. The orchestrator owns the transaction and the per-substep savepoint. Nothing here writes
`asset_throughput` — the orchestrator is the sole build-state writer.

═══════════════════════════════════════════════════════════════════════════════════════════
  IDEMPOTENCY (§N.3, L1+)
═══════════════════════════════════════════════════════════════════════════════════════════
Per-chart delete-then-insert, scoped to `(chart_id × natural key)`. A rebuild REPLACES, never
accretes. `mi_bhara` is a LIGHT writer (`has_substeps: false`), so the deletion happens at the
top of `run()` — the `ka_gochara_sweep` D-5 lesson about per-substep deletes wiping sibling
substeps' committed rows does not apply here, and this note exists so a future session that
promotes `mi_bhara` to a heavy writer moves the delete into `plan_substeps` rather than
leaving it where it is.

WEIGHTS ARE APPEND-ONLY. `insert_weights_version` INSERTs; there is no UPDATE path for an
existing version's parameter values anywhere in this module. A correction is a NEW version
whose predecessor is marked `superseded` — silent weight mutation is a drift failure
(brief §7 rail).
"""
from __future__ import annotations

import logging
from typing import Any, Mapping, Sequence

from services.mi_bhara.living_lel import LelEventRef, OpenPrediction
from services.mi_bhara.weights import NewWeightsVersion

logger = logging.getLogger(__name__)


def _rows(cur) -> list[dict]:
    """Normalise a cursor's rows to dicts regardless of the connection's row factory."""
    fetched = cur.fetchall()
    if not fetched:
        return []
    if isinstance(fetched[0], Mapping):
        return [dict(r) for r in fetched]
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in fetched]


def table_exists(conn: Any, table: str) -> bool:
    """`to_regclass` probe.

    Used so `mi_bhara` degrades HONESTLY when an upstream lane's table is not yet deployed:
    it reports the specific gap (`kala_field_absent`) rather than raising a bare
    `UndefinedTable` a caller cannot classify, and rather than pretending the field was empty.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s) IS NOT NULL AS present", (table,))
        row = cur.fetchone()
    if row is None:
        return False
    return bool(row["present"] if isinstance(row, Mapping) else row[0])


# ── reads: the field (Lane C's tables, read-only across the lane boundary) ─────────────

def fetch_field_segments(conn: Any, chart_id: str, event_class: str) -> list[dict]:
    """`kala_field` rows for one class, ascending. The cross-lane contract is this shape."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT segment_index, t_start, t_end, alpha, gamma, weights_version,
                   x_schema_version, field_snapshot_id
              FROM kala_field
             WHERE chart_id = %s AND event_class = %s
             ORDER BY segment_index
            """,
            (chart_id, event_class),
        )
        return _rows(cur)


def fetch_event_classes(conn: Any, chart_id: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT event_class FROM kala_field WHERE chart_id = %s "
            "ORDER BY event_class",
            (chart_id,),
        )
        return [r["event_class"] for r in _rows(cur)]


def fetch_null_replicate_count(conn: Any, chart_id: str, event_class: str) -> int:
    """`kala_field_null.replicates` for a class — 0 when stage 5 has not run.

    0 is reported as 0 and the skill row then carries `null_replicates = 0`; a skill score
    computed against a null that was never built would be a number with nothing behind it.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT max(replicates) AS r FROM kala_field_null "
            "WHERE chart_id = %s AND event_class = %s",
            (chart_id, event_class),
        )
        row = cur.fetchone()
    if row is None:
        return 0
    val = row["r"] if isinstance(row, Mapping) else row[0]
    return int(val or 0)


# ── reads: THE LEL. The one sanctioned crossing of the Circularity Guard. ──────────────

def fetch_lel_events(conn: Any, chart_id: str, birth_iso: str) -> list[LelEventRef]:
    """The chart's recorded life events, as days since birth.

    THIS IS THE ONLY LEL READ IN THE ENTIRE FIELD PIPELINE (§2: "Stage 9 is the only stage
    that may see the LEL"). `life_events` has been chart-scoped since migration 423, so the
    query is `(chart_id, event_id)`-keyed and cannot leak another chart's history.

    Ordering is `(event_date, event_id)` — total, so the forward-chaining split is
    reproducible when two events share a date.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT event_id,
                   COALESCE(event_type, category) AS event_class,
                   (event_date - %s::date)::double precision AS t_days
              FROM life_events
             WHERE chart_id = %s
             ORDER BY event_date, event_id
            """,
            (birth_iso, chart_id),
        )
        return [
            LelEventRef(
                event_id=str(r["event_id"]),
                event_class=str(r["event_class"]),
                t=float(r["t_days"]),
            )
            for r in _rows(cur)
        ]


def fetch_open_predictions(
    conn: Any, chart_id: str, birth_iso: str
) -> list[OpenPrediction]:
    """Open rows of `brahma_prospective_ledger` (item 20's auto-filed falsifiers).

    `lifecycle_status = 'open'` only. `matched` / `confirmed` / `falsified` / `withdrawn` /
    `lapsed_unobserved` are already resolved and re-scoring them would double-count.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT prediction_id::text          AS prediction_id,
                   event_class,
                   claim_shape,
                   (lower(observation_window) - %s::date)::double precision AS w_start,
                   (upper(observation_window) - %s::date)::double precision AS w_end,
                   (as_of::date - %s::date)::double precision               AS filed_at,
                   configuration_signature       AS window_id
              FROM brahma_prospective_ledger
             WHERE chart_id = %s
               AND lifecycle_status = 'open'
               AND observation_window IS NOT NULL
             ORDER BY prediction_id
            """,
            (birth_iso, birth_iso, birth_iso, chart_id),
        )
        return [
            OpenPrediction(
                prediction_id=str(r["prediction_id"]),
                event_class=str(r["event_class"]),
                window_start=float(r["w_start"]),
                window_end=float(r["w_end"]),
                filed_at_t=float(r["filed_at"]),
                window_id=(str(r["window_id"]) if r.get("window_id") else None),
                claim_shape=str(r["claim_shape"]),
            )
            for r in _rows(cur)
        ]


# ── writes ─────────────────────────────────────────────────────────────────────────────

def replace_prior_skill_and_gof(
    conn: Any, chart_id: str, weights_version: str, field_snapshot_id: str
) -> int:
    """§N.3 delete-then-insert, scoped to `(chart_id × weights_version × snapshot)`.

    Deliberately NOT scoped to `chart_id` alone: two weights versions over one snapshot are a
    legitimate, auditable history (that is the whole point of versioning), and a chart-wide
    delete would erase the comparison the regression gate needs.
    """
    deleted = 0
    for table in ("kala_field_skill", "kala_field_gof"):
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {table} WHERE chart_id = %s AND weights_version = %s "
                f"AND field_snapshot_id = %s",
                (chart_id, weights_version, field_snapshot_id),
            )
            deleted += cur.rowcount or 0
    return deleted


def insert_weights_version(conn: Any, version: NewWeightsVersion) -> int:
    """§7.5 step 3 — INSERT a new version row plus its parameter rows. NEVER an UPDATE.

    `ON CONFLICT DO NOTHING` on the version row makes a re-run of the same build idempotent
    without ever overwriting a published version's values: if the id already exists, its
    weights are whatever was published under that id, and that is the definition of a
    versioned artifact.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO kala_field_weight_versions
                (version_id, status, fitted_from_chart_id, scope, x_schema_version,
                 n_events_used, n_prospective_used, tau_shrinkage, any_clipped,
                 fit_loglik, holdout_loglik, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (version_id) DO NOTHING
            """,
            (
                version.version_id,
                version.status,
                version.fitted_from_chart_id,
                version.scope,
                version.x_schema_version,
                version.n_events_used,
                version.n_prospective_used,
                version.tau_shrinkage,
                version.any_clipped,
                version.fit_loglik,
                version.holdout_loglik,
                version.notes,
            ),
        )
        inserted = cur.rowcount or 0
    for w in version.weights:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO kala_field_weights
                    (version_id, weight_id, weight_value, prior_value, n_eff, clipped)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (version_id, weight_id) DO NOTHING
                """,
                (w.version_id, w.weight_id, w.weight_value, w.prior_value, w.n_eff, w.clipped),
            )
            inserted += cur.rowcount or 0
    return inserted


def supersede_previous_active(conn: Any, chart_id: str, keep_version_id: str) -> int:
    """Mark the chart's previously-active versions `superseded`.

    A STATUS transition, not a value mutation: the parameter rows of the old version are never
    touched, so the history stays auditable and a rollback is a status flip rather than a refit.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE kala_field_weight_versions
               SET status = 'superseded'
             WHERE status = 'active'
               AND version_id <> %s
               AND fitted_from_chart_id = %s
            """,
            (keep_version_id, chart_id),
        )
        return cur.rowcount or 0


def insert_skill_row(conn: Any, chart_id: str, snapshot: str, row: Mapping[str, Any]) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO kala_field_skill
                (chart_id, event_class, weights_version, field_snapshot_id,
                 n_events, n_prospective, n_backfill,
                 skill_score, skill_lo, skill_hi, skill_state, skill_prospective,
                 null_replicates, bootstrap_resamples, bootstrap_seed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                chart_id,
                row["event_class"],
                row["weights_version"],
                snapshot,
                row["n_events"],
                row["n_prospective"],
                row["n_backfill"],
                row["skill_score"],
                row["skill_lo"],
                row["skill_hi"],
                row["skill_state"],
                row.get("skill_prospective"),
                row["null_replicates"],
                row["bootstrap_resamples"],
                row["bootstrap_seed"],
            ),
        )
        return cur.rowcount or 0


def insert_gof_row(conn: Any, chart_id: str, snapshot: str, row: Mapping[str, Any]) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO kala_field_gof
                (chart_id, event_class, weights_version, field_snapshot_id, n,
                 ks_statistic, ks_p, ljung_box_p, ljung_box_stat, ljung_box_lags,
                 gof_state, failing_statistic, rescaled_z, ks_band_95)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                chart_id,
                row["event_class"],
                row["weights_version"],
                snapshot,
                row["n"],
                row.get("ks_statistic"),
                row.get("ks_p"),
                row.get("ljung_box_p"),
                row.get("ljung_box_stat"),
                row.get("ljung_box_lags", 0),
                row["gof_state"],
                row.get("failing_statistic"),
                list(row.get("rescaled_z") or []),
                row.get("ks_band_95"),
            ),
        )
        return cur.rowcount or 0


def upsert_biographical_echo_insights(
    conn: Any, chart_id: str, rows: Sequence[Mapping[str, Any]]
) -> int:
    """§7.6 step 4 — the biographical-join refresh.

    These are the ONLY `kala_insights` rows Lane E writes, they carry `lel_derived = TRUE`,
    and the §7.4 field hash EXCLUDES them. That exclusion is what lets both things be true at
    once: the insight is served, and the field never moved (§6.4's carve-out).

    `kala_insights` is Lane D's table. If it is not deployed yet, this reports 0 and the caller
    records `biographical_join_deferred` in its notes — an honest, named gap, never a silent
    skip and never a crash that would take the whole recalibration down with it.
    """
    if not table_exists(conn, "kala_insights"):
        logger.info("[mi_bhara] kala_insights absent — biographical join deferred")
        return -1
    written = 0
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM kala_insights WHERE chart_id = %s AND lel_derived = TRUE",
            (chart_id,),
        )
    for r in rows:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO kala_insights
                    (chart_id, insight_id, insight_type, event_class, window_id,
                     t_start, t_end, statement_key, statement_params, fact_ids,
                     cohort_surprise, cohort_version, surprise_basis, robustness,
                     insight_score, lel_derived, weights_version, field_snapshot_id)
                VALUES (%s, %s, 'biographical_echo', %s, %s, %s, %s, %s, %s::jsonb, %s,
                        %s, %s, %s, %s::jsonb, %s, TRUE, %s, NULL)
                ON CONFLICT (chart_id, insight_id) DO NOTHING
                """,
                (
                    chart_id,
                    r["insight_id"],
                    r.get("event_class"),
                    r.get("window_id"),
                    r.get("t_start"),
                    r.get("t_end"),
                    r["statement_key"],
                    r["statement_params"],
                    list(r.get("fact_ids") or []),
                    r.get("cohort_surprise"),
                    r.get("cohort_version"),
                    r.get("surprise_basis", "not_computed"),
                    r.get("robustness", "{}"),
                    r.get("insight_score", 0.0),
                    r["weights_version"],
                ),
            )
            written += cur.rowcount or 0
    return written

#!/usr/bin/env python3
"""
Missing-embedding backfill for bodha_signal_embeddings — INSERT-ONLY, idempotent.

Context: #2434 (ADJUDICATION) — per-asset signal-writer rebuilds (§N.3
delete-then-insert) CASCADE-delete rows in bodha_signal_embeddings, and
bo_samskara only re-runs when the orchestrator drives a full-DAG build, not a
single-asset campaign dispatch. Conductor ruling (cycle 225, issue #2434,
2026-09-08T11:21:34Z) authorized item (c) — an idempotent
`WHERE e.signal_id IS NULL` scoped insert — "once (b) [depends_on extension,
PR #2441] lands... no additional Conductor sign-off needed" for exactly this
recurring gap. (b) merged+deployed (commit 76264c24a, 2026-09-08T13:16:56Z).

This differs from run_bo_samskara_parallel.py: that script does a full
delete-then-reinsert per ayanamsha for ONE hardcoded chart (re-embeds
everything, real Vertex cost even for already-embedded signals). This script
only fetches signal_ids with NO existing embedding row, across ALL charts,
and INSERTs (ON CONFLICT DO UPDATE is a no-op safety net, not the primary
path) — cheaper, and safe to interrupt/resume: a re-run only ever re-embeds
whatever is still missing at that moment.

Usage:
    python backfill_missing_signal_embeddings.py [--dry-run]
"""
import os, sys, uuid, logging, argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("backfill_missing_embeddings")
sys.path.insert(0, os.path.dirname(__file__))

DB_URL = os.environ["DATABASE_URL"]


def _list_missing_groups(db_url: str) -> list[tuple[str, str, int]]:
    import psycopg
    conn = psycopg.connect(db_url, prepare_threshold=None, autocommit=True)
    try:
        rows = conn.execute(
            """SELECT s.chart_id::text, s.ayanamsha_id, count(*)
               FROM bodha_msr_signals s
               LEFT JOIN bodha_signal_embeddings e ON e.signal_id = s.signal_id
               WHERE e.signal_id IS NULL
               GROUP BY 1, 2 ORDER BY 1, 2"""
        ).fetchall()
        return [(r[0], r[1], r[2]) for r in rows]
    finally:
        conn.close()


def run_one_group(chart_id: str, aya: str, db_url: str, dry_run: bool) -> tuple[str, str, int]:
    """Worker: embed + insert ONLY the currently-missing signals for one (chart_id, aya)."""
    import psycopg
    sys.path.insert(0, os.path.dirname(__file__))

    from pipeline.orchestrator.writers.bo_samskara import (
        _build_input_summary,
        _embed_batch,
        _batch_insert,
        EMBED_BATCH_SIZE,
        EMBEDDING_MODEL,
        EMBEDDING_VER,
    )
    from datetime import datetime, timezone

    log = logging.getLogger(f"backfill.{chart_id[:8]}.{aya}")

    read_conn = psycopg.connect(db_url, prepare_threshold=None, autocommit=True)
    try:
        rows = read_conn.execute(
            """SELECT s.signal_id, s.ayanamsha_id, s.signal_type_class, s.signal_tradition,
                      s.signal_type_id, s.configuration_jsonb, s.domains_affected_array
               FROM bodha_msr_signals s
               LEFT JOIN bodha_signal_embeddings e ON e.signal_id = s.signal_id
               WHERE s.chart_id = %s AND s.ayanamsha_id = %s AND e.signal_id IS NULL""",
            [chart_id, aya],
        ).fetchall()
        keys = ["signal_id", "ayanamsha_id", "signal_type_class", "signal_tradition",
                "signal_type_id", "configuration_jsonb", "domains_affected_array"]
        signals = [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]
        log.info("missing=%d", len(signals))
    finally:
        read_conn.close()

    if dry_run or not signals:
        return chart_id, aya, 0

    now = datetime.now(timezone.utc).isoformat()
    build_id = str(uuid.uuid4())

    signal_summaries = [(sig, _build_input_summary(sig)) for sig in signals]
    out_rows = []
    for batch_start in range(0, len(signal_summaries), EMBED_BATCH_SIZE):
        batch = signal_summaries[batch_start:batch_start + EMBED_BATCH_SIZE]
        batch_texts = [summary for _, summary in batch]
        try:
            vecs = _embed_batch(batch_texts)
        except Exception as exc:
            log.warning("embed batch at offset %d failed (%d signals skipped): %s",
                        batch_start, len(batch), exc)
            continue
        for (sig, summary), vec in zip(batch, vecs):
            out_rows.append({
                "embedding_id":            str(uuid.uuid4()),
                "signal_id":               str(sig["signal_id"]),
                "chart_id":                chart_id,
                "ayanamsha_id":            aya,
                "build_id":                build_id,
                "embedding_vec":           "[" + ",".join(f"{v:.8f}" for v in vec) + "]",
                "embedding_model":         EMBEDDING_MODEL,
                "embedding_model_version": EMBEDDING_VER,
                "embedding_input_summary": summary,
                "computed_at":             now,
            })
        if (batch_start // EMBED_BATCH_SIZE) % 5 == 0:
            log.info("progress %d/%d", min(batch_start + EMBED_BATCH_SIZE, len(signal_summaries)),
                      len(signal_summaries))

    conn = psycopg.connect(db_url, prepare_threshold=None)
    conn.autocommit = False
    try:
        inserted = _batch_insert(conn, out_rows)
        conn.commit()
        log.info("DONE inserted=%d/%d", inserted, len(signals))
        return chart_id, aya, inserted
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-workers", type=int, default=5)
    args = parser.parse_args()

    groups = _list_missing_groups(DB_URL)
    total_missing = sum(g[2] for g in groups)
    logger.info("Found %d (chart_id, ayanamsha) groups, %d total missing embeddings",
                len(groups), total_missing)
    for chart_id, aya, n in groups:
        logger.info("  %s / %s: %d missing", chart_id, aya, n)

    if args.dry_run:
        logger.info("dry-run — no writes")
        return

    results: dict[tuple[str, str], int] = {}
    errors: list[str] = []

    with ProcessPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {
            pool.submit(run_one_group, chart_id, aya, DB_URL, False): (chart_id, aya)
            for chart_id, aya, _ in groups
        }
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                _, _, count = fut.result()
                results[key] = count
                logger.info("✓ %s/%s: %d rows", key[0], key[1], count)
            except Exception as exc:
                errors.append(f"{key}: {exc}")
                logger.error("✗ %s/%s: %s", key[0], key[1], exc)

    total_inserted = sum(results.values())
    logger.info("COMPLETE: total_inserted=%d/%d groups=%d/%d",
                total_inserted, total_missing, len(results), len(groups))
    if errors:
        logger.error("ERRORS: %s", errors)
        sys.exit(1)


if __name__ == "__main__":
    main()

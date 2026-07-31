#!/usr/bin/env python3
"""
Parallel per-ayanamsha runner for bo_samskara against prod DB.

Runs 5 worker processes concurrently (one per canonical ayanamsha), each with
its own connection and commit. Total time ~1/5 of sequential run.

Idempotent: each worker deletes its ayanamsha's rows then inserts fresh real
Vertex AI embeddings. Safe to re-run; any partial prior state is replaced.

Usage:
    python run_bo_samskara_parallel.py [--dry-run]
"""
import os, sys, uuid, logging, argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("bo_samskara_parallel")
sys.path.insert(0, os.path.dirname(__file__))

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL = os.environ["DATABASE_URL"]
# Import from the writer — single source of truth for ayanamsha names
from pipeline.orchestrator.writers.bo_samskara import CANONICAL_AYAS  # noqa: E402


def run_one_ayanamsha(aya: str, chart_id: str, db_url: str, dry_run: bool) -> tuple[str, int]:
    """Worker: embed + insert all signals for one ayanamsha in its own transaction."""
    import psycopg

    sys.path.insert(0, os.path.dirname(__file__))

    # Import writer internals directly (avoids full writer instantiation / orchestrator)
    from pipeline.orchestrator.writers.bo_samskara import (
        _fetch_signals,
        _build_input_summary,
        _embed_batch,
        _batch_insert,
        EMBED_BATCH_SIZE,
        EMBEDDING_MODEL,
        EMBEDDING_VER,
    )
    from bodha_writers._idempotency import replace_prior_signal_embeddings
    from datetime import datetime, timezone

    log = logging.getLogger(f"bo_samskara.{aya}")
    log.info("starting aya=%s", aya)

    # Phase 1: READ — autocommit=True so no transaction is held during long Vertex calls.
    # idle_in_transaction_session_timeout kills connections held open during API waits.
    read_conn = psycopg.connect(db_url, prepare_threshold=None, autocommit=True)
    try:
        signals = _fetch_signals(read_conn, chart_id, aya)
        log.info("aya=%s signals=%d", aya, len(signals))
    finally:
        read_conn.close()  # Release before Vertex calls — no DB held during API wait

    if dry_run:
        return aya, 0

    now = datetime.now(timezone.utc).isoformat()
    build_id = str(uuid.uuid4())

    # Phase 2: EMBED — no DB connection open during Vertex AI calls
    signal_summaries = [(sig, _build_input_summary(sig)) for sig in signals]
    rows = []
    for batch_start in range(0, len(signal_summaries), EMBED_BATCH_SIZE):
        batch = signal_summaries[batch_start:batch_start + EMBED_BATCH_SIZE]
        batch_texts = [summary for _, summary in batch]
        vecs = _embed_batch(batch_texts)
        for (sig, summary), vec in zip(batch, vecs):
            rows.append({
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

    # Phase 3: WRITE — fresh connection, short-lived transaction for DELETE+INSERT only
    conn = psycopg.connect(db_url, prepare_threshold=None)
    conn.autocommit = False
    try:

        # Idempotency: delete this aya's rows, then insert fresh
        replace_prior_signal_embeddings(conn, chart_id, aya)
        inserted = _batch_insert(conn, rows)
        conn.commit()
        log.info("aya=%s DONE inserted=%d", aya, inserted)
        return aya, inserted

    except Exception as exc:
        conn.rollback()
        log.error("aya=%s FAILED: %s", aya, exc)
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logger.info("Launching 5 parallel ayanamsha workers for chart %s", CHART_ID)

    results: dict[str, int] = {}
    errors: list[str] = []

    with ProcessPoolExecutor(max_workers=5) as pool:
        futures = {
            pool.submit(run_one_ayanamsha, aya, CHART_ID, DB_URL, args.dry_run): aya
            for aya in CANONICAL_AYAS
        }
        for fut in as_completed(futures):
            aya = futures[fut]
            try:
                _, count = fut.result()
                results[aya] = count
                logger.info("✓ %s: %d rows", aya, count)
            except Exception as exc:
                errors.append(f"{aya}: {exc}")
                logger.error("✗ %s: %s", aya, exc)

    total = sum(results.values())
    logger.info("COMPLETE: total_inserted=%d ayanamshas=%d/%d", total, len(results), len(CANONICAL_AYAS))
    if errors:
        logger.error("ERRORS: %s", errors)
        sys.exit(1)
    logger.info("Expected 66738 total; got %d — %s", total, "PASS" if total == 66738 else "MISMATCH")


if __name__ == "__main__":
    main()

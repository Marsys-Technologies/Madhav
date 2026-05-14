"""
run_attribution_pass_v2.py — Optimized M8-E-S1 attribution engine.

Changes from v1:
  - Batches all K chunks into ONE Gemini call per signal (K× fewer API calls)
  - Skips signals already in classical_attributions (idempotent restart)
  - Same algorithm, same output schema

M8-E-S1 2026-05-14.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import psycopg2
import psycopg2.extras
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai.language_models import TextEmbeddingModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────

PROJECT     = os.environ.get("GCP_PROJECT", "")
LOCATION    = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
EMBED_MODEL = "text-embedding-004"
JUDGE_MODEL = os.environ.get("GEMINI_JUDGE_MODEL", "gemini-2.5-flash")
TOP_K       = 5
MIN_SIMILARITY = 0.55

REPO_ROOT   = Path(__file__).parents[4]
MSR_PATH    = REPO_ROOT / "025_HOLISTIC_SYNTHESIS" / "MSR_v3_0.md"
OUTPUT_DIR  = REPO_ROOT / "08_CLASSICAL_CROSS_REFERENCE"
REGISTRY_JSON  = OUTPUT_DIR / "CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json"
REGISTRY_MD    = OUTPUT_DIR / "CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md"
FINDINGS_CROSS = OUTPUT_DIR / "FINDINGS_M5_CROSS_REF_v1_0.md"
FINDINGS_CLAIM = OUTPUT_DIR / "FINDINGS_CLASSICAL_CLAIM_v1_0.md"

# ─── DB ───────────────────────────────────────────────────────────────────────

@contextmanager
def get_db() -> Generator[psycopg2.extensions.connection, None, None]:
    url = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(url)
    try:
        yield conn
    finally:
        conn.close()


def get_already_attributed_signals(conn: psycopg2.extensions.connection) -> set[str]:
    """Return set of signal IDs already present in classical_attributions."""
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT msr_signal_id FROM classical_attributions")
        return {row[0] for row in cur.fetchall()}


def query_top_k_chunks(
    conn: psycopg2.extensions.connection,
    embedding: list[float],
    k: int = TOP_K,
) -> list[dict[str, Any]]:
    emb_str = f"[{','.join(str(v) for v in embedding)}]"
    sql = """
        SELECT
            cc.id::text              AS chunk_id,
            ct.text_key,
            ct.title,
            ct.school,
            ct.tradition,
            cc.chapter,
            cc.verse_range,
            cc.content,
            ct.attribution_baseline_confidence,
            1.0 - (cc.embedding <=> %s::vector)  AS similarity
        FROM classical_chunks cc
        JOIN classical_texts ct ON ct.id = cc.text_id
        WHERE cc.embedding IS NOT NULL
        ORDER BY cc.embedding <=> %s::vector
        LIMIT %s
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (emb_str, emb_str, k))
        rows = cur.fetchall()
    return [dict(r) for r in rows if float(r["similarity"]) >= MIN_SIMILARITY]


def insert_attribution(
    conn: psycopg2.extensions.connection,
    signal_id: str,
    chunk_id: str,
    attribution_type: str,
    confidence: float,
    derivation_notes: str,
) -> bool:
    sql = """
        INSERT INTO classical_attributions
          (msr_signal_id, chunk_id, attribution_type, confidence, derivation_notes)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id
    """
    with conn.cursor() as cur:
        cur.execute(sql, (signal_id, chunk_id, attribution_type, confidence, derivation_notes))
        inserted = cur.rowcount > 0
    conn.commit()
    return inserted


# ─── MSR signal parsing ───────────────────────────────────────────────────────

def load_msr_signals(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    signals: list[dict[str, str]] = []
    blocks = re.split(r"\n(?=SIG\.MSR\.\d+:)", text)
    for block in blocks:
        m = re.match(r"(SIG\.MSR\.\d+):", block)
        if not m:
            continue
        sig_id = m.group(1)
        name_m = re.search(r'signal_name:\s*"([^"]+)"', block)
        src_m  = re.search(r'classical_source:\s*"([^"]+)"', block)
        signals.append({
            "signal_id":        sig_id,
            "signal_name":      name_m.group(1) if name_m else sig_id,
            "classical_source": src_m.group(1)  if src_m  else "",
        })
    log.info("Parsed %d signals from MSR_v3_0.md", len(signals))
    return signals


def build_query_text(sig: dict[str, str]) -> str:
    parts = [sig["signal_name"]]
    if sig["classical_source"]:
        parts.append(sig["classical_source"])
    return " | ".join(parts)


# ─── Vertex AI embedding ──────────────────────────────────────────────────────

def embed_queries(queries: list[str]) -> list[list[float]]:
    vertexai.init(project=PROJECT, location=LOCATION)
    model = TextEmbeddingModel.from_pretrained(EMBED_MODEL)
    embeddings: list[list[float]] = []
    for i in range(0, len(queries), 15):
        batch = queries[i : i + 15]
        responses = model.get_embeddings(batch)
        for resp in responses:
            embeddings.append(resp.values)
        if i + 15 < len(queries):
            time.sleep(0.3)
    return embeddings


# ─── Batched Gemini judge ─────────────────────────────────────────────────────

BATCH_JUDGE_PROMPT = """\
You are a classical Jyotish scholar comparing a modern MSR signal to classical text passages.

MSR Signal: {signal_name}
Classical Source Hint: {classical_source}

Evaluate each of the following {n} passages against this MSR signal.

Attribution types:
- confirms: passage directly supports or states the same principle
- contradicts: passage explicitly states the opposite
- partial: passage partially supports or touches on the principle
- extends: passage adds nuance or extends the principle
- silent: passage is irrelevant to this signal

Passages:
{passages}

Return ONLY a JSON array of exactly {n} objects, one per passage in order:
[
  {{"passage": 1, "attribution_type": "...", "confidence": 0.0, "derivation_notes": "one sentence"}},
  {{"passage": 2, "attribution_type": "...", "confidence": 0.0, "derivation_notes": "one sentence"}}
]
No text outside the JSON array.
"""


def judge_chunks_batch(
    model: GenerativeModel,
    signal_name: str,
    classical_source: str,
    chunks: list[dict[str, Any]],
) -> list[tuple[str, float, str]]:
    """Judge all chunks for a signal in ONE Gemini call. Returns list of (type, conf, notes)."""
    if not chunks:
        return []

    passage_lines = []
    for idx, chunk in enumerate(chunks, 1):
        cv = ""
        if chunk.get("chapter"):
            cv = f"Ch. {chunk['chapter']}"
            if chunk.get("verse_range"):
                cv += f" v.{chunk['verse_range']}"
        passage_lines.append(
            f"Passage {idx}: [{chunk['text_key']}] {chunk['title']} {cv}\n"
            f"  {chunk['content'][:600]}"
        )

    prompt = BATCH_JUDGE_PROMPT.format(
        signal_name=signal_name,
        classical_source=classical_source or "unknown",
        n=len(chunks),
        passages="\n\n".join(passage_lines),
    )

    valid_types = {"confirms", "contradicts", "partial", "extends", "silent"}
    fallback = [("silent", 0.3, "Judge failed") for _ in chunks]

    try:
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.1,
                max_output_tokens=4096,
                response_mime_type="application/json",
            ),
        )
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        data = json.loads(text)

        if not isinstance(data, list) or len(data) != len(chunks):
            log.warning("Batch judge returned wrong length: %d vs %d", len(data), len(chunks))
            return fallback

        results = []
        for item in data:
            attr_type  = item.get("attribution_type", "silent")
            confidence = float(item.get("confidence", 0.5))
            notes      = item.get("derivation_notes", "")
            if attr_type not in valid_types:
                attr_type = "silent"
            confidence = max(0.0, min(1.0, confidence))
            results.append((attr_type, confidence, notes))
        return results

    except Exception as exc:
        log.warning("Batch judge failed: %s", exc)
        return fallback


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if not PROJECT:
        raise RuntimeError("GCP_PROJECT env var not set")
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL not set")

    log.info("=== M8-E-S1 Attribution Pass v2 (batched judge) ===")
    log.info("Project: %s, Location: %s, Embed model: %s", PROJECT, LOCATION, EMBED_MODEL)
    log.info("Judge model: %s, Top-K: %d, Min similarity: %.2f", JUDGE_MODEL, TOP_K, MIN_SIMILARITY)

    signals = load_msr_signals(MSR_PATH)
    if not signals:
        log.error("No signals parsed from %s — aborting", MSR_PATH)
        sys.exit(1)

    # Check which signals are already done
    with get_db() as conn:
        already_done = get_already_attributed_signals(conn)

    pending = [s for s in signals if s["signal_id"] not in already_done]
    log.info("Already attributed: %d signals. Pending: %d signals.", len(already_done), len(pending))

    if not pending:
        log.info("All signals attributed — building outputs from DB")
    else:
        # Embed only the pending signal queries
        log.info("Embedding %d pending signal queries...", len(pending))
        queries = [build_query_text(s) for s in pending]
        embeddings = embed_queries(queries)
        log.info("Embedded %d queries", len(embeddings))

        vertexai.init(project=PROJECT, location=LOCATION)
        judge = GenerativeModel(JUDGE_MODEL)

        total_inserted = 0
        total_skipped  = 0

        with get_db() as conn:
            for i, (sig, embedding) in enumerate(zip(pending, embeddings)):
                if i % 20 == 0:
                    log.info("Progress: %d/%d pending signals processed", i, len(pending))

                chunks = query_top_k_chunks(conn, embedding, k=TOP_K)
                if not chunks:
                    continue

                # ONE batch call for all chunks of this signal
                results = judge_chunks_batch(
                    judge,
                    sig["signal_name"],
                    sig["classical_source"],
                    chunks,
                )

                for chunk, (attr_type, confidence, notes) in zip(chunks, results):
                    inserted = insert_attribution(
                        conn,
                        sig["signal_id"],
                        chunk["chunk_id"],
                        attr_type,
                        confidence,
                        notes,
                    )
                    if inserted:
                        total_inserted += 1
                    else:
                        total_skipped += 1

                # Small delay between signals
                time.sleep(0.1)

        log.info("Attribution pass complete: %d inserted, %d skipped", total_inserted, total_skipped)

    # Build outputs from DB
    log.info("Building output files from DB...")
    from build_registry_from_db import fetch_all_attributions, build_registry, build_findings_cross_ref, build_findings_claim
    with get_db() as conn:
        records = fetch_all_attributions(conn)

    log.info("Fetched %d attribution records from DB", len(records))
    if len(records) < 400:
        log.warning("WARNING: Only %d rows — AC.M8E.3 requires ≥400", len(records))

    build_registry(records)
    build_findings_cross_ref(records)
    build_findings_claim(records)

    type_counts: dict[str, int] = {}
    for r in records:
        type_counts[r["attribution_type"]] = type_counts.get(r["attribution_type"], 0) + 1
    log.info("=== SUMMARY ===")
    for t, c in sorted(type_counts.items()):
        log.info("  %-12s: %d", t, c)
    log.info("  TOTAL       : %d", len(records))


if __name__ == "__main__":
    main()

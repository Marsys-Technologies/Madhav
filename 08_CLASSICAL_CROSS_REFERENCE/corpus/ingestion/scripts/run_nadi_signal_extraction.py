"""
run_nadi_signal_extraction.py — M8-F-S1 signal extraction from Nadi/BNN chunks.

For each text_key in (bhrigu_nandi_nadi, chandra_kala_nadi, dhruva_nadi_sampler):
  1. Fetch chunks from DB (sample strategy: every Nth chunk to keep costs low)
  2. For each chunk, ask Gemini judge: identify any predictive-signal patterns
  3. Output NADI_SIGNAL_EXTRACTION_v1_0.md (BNN) + NADI_SIGNAL_EXTRACTION_v1_0.md (CKN)

M8-F-S1 2026-05-14.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PROJECT     = os.environ.get("GCP_PROJECT", "")
LOCATION    = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
JUDGE_MODEL = os.environ.get("GEMINI_JUDGE_MODEL", "gemini-2.5-flash")

REPO_ROOT   = Path(__file__).parents[4]
OUTPUT_DIR  = REPO_ROOT / "08_CLASSICAL_CROSS_REFERENCE"

NADI_TEXTS  = ["chandra_kala_nadi", "dhruva_nadi_sampler"]
BNN_TEXTS   = ["bhrigu_nandi_nadi"]

# Sample every Nth chunk to control cost; still provides good coverage
SAMPLE_EVERY = 15          # wider stride — thinking model is slow; sample 5-7% of chunks
MAX_CHUNKS_PER_TEXT = 30   # cap per text — ~30 Gemini calls max per text


@contextmanager
def get_db() -> Generator[psycopg2.extensions.connection, None, None]:
    url = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(url)
    try:
        yield conn
    finally:
        conn.close()


def fetch_chunks_sampled(conn, text_key: str, sample_every: int = SAMPLE_EVERY, max_chunks: int = MAX_CHUNKS_PER_TEXT) -> list[dict[str, Any]]:
    sql = """
        SELECT cc.id::text AS chunk_id, cc.chunk_index, cc.chapter, cc.verse_range, cc.content
        FROM classical_chunks cc
        JOIN classical_texts ct ON ct.id = cc.text_id
        WHERE ct.text_key = %s AND cc.chunk_index %% %s = 0
        ORDER BY cc.chunk_index
        LIMIT %s
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (text_key, sample_every, max_chunks))
        return [dict(r) for r in cur.fetchall()]


EXTRACTION_PROMPT = """\
You are a classical Jyotish scholar analyzing a passage from {text_title} ({school} tradition).

Passage (chunk {chunk_index}):
{content}

Identify ALL predictive-signal patterns in this passage — rules, yogas, principles, or combinations
that predict an outcome for a person's life. For each signal found, extract:

Return ONLY a JSON array (may be empty []) of signal objects:
[
  {{
    "signal_name": "concise name",
    "signal_domain": "one of: career|wealth|relationships|health|spirituality|timing|psychological|other",
    "school": "{school}",
    "trigger_condition": "the astrological condition that triggers this signal (planets, houses, signs)",
    "predicted_outcome": "what the signal predicts",
    "source_verse": "chapter/verse reference if mentioned",
    "extraction_confidence": 0.0
  }}
]

Rules:
- Only extract genuine predictive rules (not general descriptions or narrative)
- extraction_confidence: 0.0–1.0 (how confident you are this is a distinct predictive rule)
- Include confidence ≥ 0.4 signals only
- Maximum 5 signals per chunk
- Empty array [] if no signals found
No text outside the JSON array.
"""


def extract_signals_from_chunk(
    model: GenerativeModel,
    chunk: dict[str, Any],
    text_title: str,
    school: str,
) -> list[dict[str, Any]]:
    prompt = EXTRACTION_PROMPT.format(
        text_title=text_title,
        school=school,
        chunk_index=chunk["chunk_index"],
        content=chunk["content"][:800],
    )
    try:
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.1,
                max_output_tokens=8192,
                response_mime_type="application/json",
            ),
        )
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except Exception as exc:
        log.warning("Extraction failed for chunk %d: %s", chunk.get("chunk_index", -1), exc)
    return []


def dedup_signals(signals: list[dict[str, Any]], threshold_name_overlap: int = 4) -> list[dict[str, Any]]:
    seen_names: list[str] = []
    deduped = []
    for sig in signals:
        name = sig.get("signal_name", "").lower()
        words = set(name.split())
        is_dup = any(len(words & set(n.split())) >= threshold_name_overlap for n in seen_names)
        if not is_dup:
            seen_names.append(name)
            deduped.append(sig)
    return deduped


def write_extraction_md(signals: list[dict[str, Any]], title: str, path: Path) -> None:
    lines = [
        f"---",
        f"artifact: {path.name}",
        f"version: 1.0",
        f"status: CURRENT",
        f"produced_during: M8-F-S1",
        f"produced_on: 2026-05-14",
        f"signal_count: {len(signals)}",
        f"---",
        f"",
        f"# {title}",
        f"",
        f"Extraction from Nadi/BNN classical text corpus. Each signal is a candidate for MSR expansion.",
        f"Signals with `extraction_confidence ≥ 0.60` are promoted to MSR expansion candidates.",
        f"",
        f"| # | Signal Name | Domain | School | Trigger | Predicted Outcome | Confidence |",
        f"|---|---|---|---|---|---|---|",
    ]
    high_conf = [s for s in signals if s.get("extraction_confidence", 0) >= 0.60]
    for i, sig in enumerate(signals, 1):
        lines.append(
            f"| {i} | {sig.get('signal_name','')} | {sig.get('signal_domain','')} | {sig.get('school','')} | "
            f"{sig.get('trigger_condition','')[:60]} | {sig.get('predicted_outcome','')[:80]} | "
            f"{sig.get('extraction_confidence', 0):.2f} |"
        )
    lines.extend([
        f"",
        f"## High-Confidence Signals (≥0.60) — MSR Expansion Candidates",
        f"",
        f"Count: {len(high_conf)}",
        f"",
    ])
    for i, sig in enumerate(high_conf, 1):
        lines.extend([
            f"### {i}. {sig.get('signal_name', '')}",
            f"",
            f"- **Domain:** {sig.get('signal_domain', '')}",
            f"- **School:** {sig.get('school', '')}",
            f"- **Trigger:** {sig.get('trigger_condition', '')}",
            f"- **Predicted Outcome:** {sig.get('predicted_outcome', '')}",
            f"- **Source Verse:** {sig.get('source_verse', 'not specified')}",
            f"- **Extraction Confidence:** {sig.get('extraction_confidence', 0):.2f}",
            f"",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Wrote %s (%d signals; %d high-conf)", path.name, len(signals), len(high_conf))


def run_extraction(text_key: str, text_title: str, school: str, model: GenerativeModel) -> list[dict[str, Any]]:
    all_signals: list[dict[str, Any]] = []
    with get_db() as conn:
        chunks = fetch_chunks_sampled(conn, text_key)
    log.info("%s: %d sampled chunks to process", text_key, len(chunks))

    for i, chunk in enumerate(chunks):
        if i % 10 == 0:
            log.info("  %s: chunk %d/%d", text_key, i, len(chunks))
        signals = extract_signals_from_chunk(model, chunk, text_title, school)
        for sig in signals:
            sig["source_text"] = text_key
            sig["source_chunk_index"] = chunk["chunk_index"]
        all_signals.extend(signals)
        time.sleep(0.15)

    deduped = dedup_signals(all_signals)
    log.info("%s: %d raw signals → %d after dedup", text_key, len(all_signals), len(deduped))
    return deduped


def main() -> None:
    if not PROJECT:
        raise RuntimeError("GCP_PROJECT env var not set")
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL not set")

    log.info("=== M8-F-S1 Nadi Signal Extraction ===")
    vertexai.init(project=PROJECT, location=LOCATION)
    model = GenerativeModel(JUDGE_MODEL)

    # BNN extraction
    bnn_signals: list[dict[str, Any]] = []
    for text_key in BNN_TEXTS:
        sigs = run_extraction(text_key, "Bhrigu Nandi Nadi", "bnn", model)
        bnn_signals.extend(sigs)

    bnn_path = OUTPUT_DIR / "BNN_SIGNAL_EXTRACTION_v1_0.md"
    write_extraction_md(bnn_signals, "BNN Signal Extraction — Bhrigu Nandi Nadi", bnn_path)

    # Nadi extraction
    nadi_signals: list[dict[str, Any]] = []
    for text_key in NADI_TEXTS:
        title_map = {
            "chandra_kala_nadi": "Chandra Kala Nadi (Deva Keralam)",
            "dhruva_nadi_sampler": "Dhruva Nadi (Sampler)",
        }
        sigs = run_extraction(text_key, title_map[text_key], "nadi", model)
        nadi_signals.extend(sigs)

    nadi_path = OUTPUT_DIR / "NADI_SIGNAL_EXTRACTION_v1_0.md"
    write_extraction_md(nadi_signals, "Nadi Signal Extraction — Chandra Kala Nadi + Dhruva Nadi", nadi_path)

    log.info("=== Extraction complete ===")
    log.info("BNN signals: %d (%d high-conf ≥0.60)", len(bnn_signals), sum(1 for s in bnn_signals if s.get("extraction_confidence",0) >= 0.60))
    log.info("Nadi signals: %d (%d high-conf ≥0.60)", len(nadi_signals), sum(1 for s in nadi_signals if s.get("extraction_confidence",0) >= 0.60))

    return bnn_signals, nadi_signals


if __name__ == "__main__":
    main()

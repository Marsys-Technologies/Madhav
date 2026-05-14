"""
run_attribution_pass.py — M8-E-S1: MSR signal × classical chunk attribution engine.

Algorithm:
  1. Load all 514 MSR signal IDs + names from MSR_v3_0.md
  2. Embed each signal query (name + classical_source hint) via Vertex AI text-embedding-004
  3. Query classical_chunks via pgvector cosine similarity → top-K=5 chunks per signal
  4. Call Gemini judge to assign attribution_type + confidence for each (signal, chunk) pair
  5. INSERT into classical_attributions (idempotent: ON CONFLICT DO NOTHING)
  6. Produce CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json + .md
  7. Print summary stats: total attributions, per-type counts, per-text counts

LLM stack: Vertex AI text-embedding-004 + Gemini 1.5 Pro. No Anthropic/Claude API.
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
from google.cloud import aiplatform
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
MIN_SIMILARITY = 0.55  # ignore chunks below this threshold (1 - cosine_distance)

REPO_ROOT   = Path(__file__).parents[4]  # scripts → ingestion → corpus → 08_CLASSICAL_CROSS_REFERENCE → Madhav-M8
MSR_PATH    = REPO_ROOT / "025_HOLISTIC_SYNTHESIS" / "MSR_v3_0.md"
OUTPUT_DIR  = REPO_ROOT / "08_CLASSICAL_CROSS_REFERENCE"
REGISTRY_JSON = OUTPUT_DIR / "CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json"
REGISTRY_MD   = OUTPUT_DIR / "CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md"
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
    """Parse signal_id, signal_name, classical_source from MSR_v3_0.md."""
    text = path.read_text(encoding="utf-8")
    signals: list[dict[str, str]] = []

    # Each block starts with "SIG.MSR.NNN:"
    blocks = re.split(r"\n(?=SIG\.MSR\.\d+:)", text)
    for block in blocks:
        m = re.match(r"(SIG\.MSR\.\d+):", block)
        if not m:
            continue
        sig_id = m.group(1)

        name_m = re.search(r'signal_name:\s*"([^"]+)"', block)
        src_m  = re.search(r'classical_source:\s*"([^"]+)"', block)

        signal_name    = name_m.group(1) if name_m else sig_id
        classical_src  = src_m.group(1)  if src_m  else ""

        signals.append({
            "signal_id":       sig_id,
            "signal_name":     signal_name,
            "classical_source": classical_src,
        })

    log.info("Parsed %d signals from MSR_v3_0.md", len(signals))
    return signals


def build_query_text(sig: dict[str, str]) -> str:
    """Compose search query from signal name + classical source hint."""
    parts = [sig["signal_name"]]
    if sig["classical_source"]:
        parts.append(sig["classical_source"])
    return " | ".join(parts)


# ─── Vertex AI embedding ──────────────────────────────────────────────────────

def embed_queries(queries: list[str]) -> list[list[float]]:
    """Embed a list of query strings. Returns list of 768-dim vectors."""
    vertexai.init(project=PROJECT, location=LOCATION)
    model = TextEmbeddingModel.from_pretrained(EMBED_MODEL)

    embeddings: list[list[float]] = []
    # Batch in groups of 15 to stay under token limits
    for i in range(0, len(queries), 15):
        batch = queries[i : i + 15]
        responses = model.get_embeddings(batch)
        for resp in responses:
            embeddings.append(resp.values)
        if i + 15 < len(queries):
            time.sleep(0.3)  # rate limit headroom

    return embeddings


# ─── Gemini judge ─────────────────────────────────────────────────────────────

JUDGE_PROMPT = """\
You are a classical Jyotish scholar comparing a modern MSR signal to a classical text passage.

MSR Signal: {signal_name}
Classical Source Hint: {classical_source}

Classical Text Passage:
  Text: {title} ({tradition})
  Chapter/Verse: {chapter_verse}
  Content: {content}

Task: Determine how this classical passage relates to the MSR signal.

Attribution types:
- confirms: The passage directly supports or states the same principle
- contradicts: The passage explicitly states the opposite
- partial: The passage partially supports or touches on the principle
- extends: The passage adds nuance or extends the principle
- silent: The passage is irrelevant to this signal

Return ONLY valid JSON with this structure:
{{
  "attribution_type": "confirms|contradicts|partial|extends|silent",
  "confidence": 0.0-1.0,
  "derivation_notes": "one-sentence explanation"
}}

Do not include any text outside the JSON object.
"""

def judge_attribution(
    model: GenerativeModel,
    signal_name: str,
    classical_source: str,
    chunk: dict[str, Any],
) -> tuple[str, float, str]:
    """Call Gemini to judge attribution type and confidence."""
    chapter_verse = ""
    if chunk.get("chapter"):
        chapter_verse = f"Ch. {chunk['chapter']}"
        if chunk.get("verse_range"):
            chapter_verse += f" v.{chunk['verse_range']}"

    prompt = JUDGE_PROMPT.format(
        signal_name=signal_name,
        classical_source=classical_source or "unknown",
        title=chunk["title"],
        tradition=chunk["tradition"],
        chapter_verse=chapter_verse or "—",
        content=chunk["content"][:800],
    )

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
        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        data = json.loads(text)

        attr_type  = data.get("attribution_type", "silent")
        confidence = float(data.get("confidence", 0.5))
        notes      = data.get("derivation_notes", "")

        # Validate
        valid_types = {"confirms", "contradicts", "partial", "extends", "silent"}
        if attr_type not in valid_types:
            attr_type = "silent"
        confidence = max(0.0, min(1.0, confidence))

        return attr_type, confidence, notes

    except Exception as exc:
        log.warning("Gemini judge failed for chunk %s: %s", chunk["chunk_id"], exc)
        return "silent", 0.3, f"Judge failed: {type(exc).__name__}"


# ─── Registry output ──────────────────────────────────────────────────────────

def build_registry(all_records: list[dict[str, Any]]) -> None:
    registry = {
        "artifact": "CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json",
        "version": "1.0",
        "canonical_id": "CLASSICAL_ATTRIBUTION_REGISTRY",
        "status": "CURRENT",
        "layer": "L8",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_attributions": len(all_records),
        "attributions": all_records,
    }
    REGISTRY_JSON.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Written %s (%d records)", REGISTRY_JSON, len(all_records))

    # Count stats
    type_counts: dict[str, int] = {}
    text_counts: dict[str, int] = {}
    for r in all_records:
        type_counts[r["attribution_type"]] = type_counts.get(r["attribution_type"], 0) + 1
        key = r.get("text_key", "unknown")
        text_counts[key] = text_counts.get(key, 0) + 1

    lines = [
        "---",
        "artifact: CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md",
        "version: \"1.0\"",
        "canonical_id: CLASSICAL_ATTRIBUTION_REGISTRY",
        "status: CURRENT",
        "layer: L8",
        f"generated_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"total_attributions: {len(all_records)}",
        "---",
        "",
        "# CLASSICAL_ATTRIBUTION_REGISTRY v1.0",
        "",
        "## Summary",
        "",
        "| Attribution Type | Count |",
        "|---|---|",
    ]
    for t, c in sorted(type_counts.items()):
        lines.append(f"| {t} | {c} |")

    lines += ["", "## Per-Text Counts", "", "| Text Key | Attributions |", "|---|---|"]
    for tk, c in sorted(text_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {tk} | {c} |")

    lines += ["", "## Attribution Records", ""]
    for r in all_records[:100]:  # first 100 for MD readability
        lines.append(
            f"**{r['signal_id']}** × `{r['text_key']}` Ch.{r.get('chapter','?')} — "
            f"{r['attribution_type']} (conf {r['confidence']:.2f}) — {r.get('derivation_notes','')}"
        )

    REGISTRY_MD.write_text("\n".join(lines), encoding="utf-8")
    log.info("Written %s", REGISTRY_MD)


def build_findings_cross_ref(
    all_records: list[dict[str, Any]],
    signals: list[dict[str, str]],
) -> None:
    """Top-10 signals × 5 domains findings."""
    # Group by signal
    sig_map: dict[str, list[dict[str, Any]]] = {}
    for r in all_records:
        sig_map.setdefault(r["signal_id"], []).append(r)

    # Rank signals by count of confirms + partial
    def rank_signal(sid: str) -> int:
        return sum(
            1 for r in sig_map.get(sid, [])
            if r["attribution_type"] in ("confirms", "partial")
        )

    top10 = sorted(sig_map.keys(), key=rank_signal, reverse=True)[:10]

    lines = [
        "---",
        "artifact: FINDINGS_M5_CROSS_REF_v1_0.md",
        "version: \"1.0\"",
        "status: CURRENT",
        "layer: L8",
        f"generated_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "---",
        "",
        "# FINDINGS: Top-10 MSR Signals × Classical Cross-Reference",
        "",
        "Signals ranked by count of `confirms` + `partial` attributions across the corpus.",
        "",
    ]

    sig_lookup = {s["signal_id"]: s for s in signals}
    for rank, sid in enumerate(top10, 1):
        sig = sig_lookup.get(sid, {"signal_name": sid, "classical_source": ""})
        records = sig_map[sid]
        lines += [
            f"## {rank}. {sid}: {sig['signal_name']}",
            "",
            f"Classical source hint: *{sig['classical_source'] or 'none'}*",
            "",
            "| Text | Chapter/Verse | Type | Confidence | Notes |",
            "|---|---|---|---|---|",
        ]
        for r in sorted(records, key=lambda x: -x["confidence"])[:5]:
            cv = f"Ch.{r.get('chapter','?')}"
            if r.get("verse_range"):
                cv += f" v.{r['verse_range']}"
            lines.append(
                f"| {r['text_key']} | {cv} | {r['attribution_type']} | "
                f"{r['confidence']:.2f} | {r.get('derivation_notes','')[:80]} |"
            )
        lines.append("")

    FINDINGS_CROSS.write_text("\n".join(lines), encoding="utf-8")
    log.info("Written %s", FINDINGS_CROSS)


def build_findings_claim(all_records: list[dict[str, Any]]) -> None:
    """Holds/fails/partial/silent counts per text."""
    # Group by text_key
    text_stats: dict[str, dict[str, int]] = {}
    for r in all_records:
        tk = r.get("text_key", "unknown")
        if tk not in text_stats:
            text_stats[tk] = {"confirms": 0, "contradicts": 0, "partial": 0, "extends": 0, "silent": 0}
        text_stats[tk][r["attribution_type"]] = text_stats[tk].get(r["attribution_type"], 0) + 1

    lines = [
        "---",
        "artifact: FINDINGS_CLASSICAL_CLAIM_v1_0.md",
        "version: \"1.0\"",
        "status: CURRENT",
        "layer: L8",
        f"generated_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "---",
        "",
        "# FINDINGS: Classical Claim Inventory (Holds / Fails / Partial / Silent)",
        "",
        "For each classical text, how many MSR signal attributions were: confirms / contradicts / partial / extends / silent.",
        "",
        "| Text Key | confirms | contradicts | partial | extends | silent | total |",
        "|---|---|---|---|---|---|---|",
    ]

    total_row = {"confirms": 0, "contradicts": 0, "partial": 0, "extends": 0, "silent": 0}
    for tk, counts in sorted(text_stats.items()):
        row_total = sum(counts.values())
        lines.append(
            f"| {tk} | {counts['confirms']} | {counts['contradicts']} | "
            f"{counts['partial']} | {counts['extends']} | {counts['silent']} | {row_total} |"
        )
        for k in total_row:
            total_row[k] += counts.get(k, 0)

    grand_total = sum(total_row.values())
    lines.append(
        f"| **TOTAL** | **{total_row['confirms']}** | **{total_row['contradicts']}** | "
        f"**{total_row['partial']}** | **{total_row['extends']}** | **{total_row['silent']}** | "
        f"**{grand_total}** |"
    )

    # Commentary
    lines += [
        "",
        "## Interpretation",
        "",
        f"- **Confirms**: {total_row['confirms']} signal-text pairs where classical text directly validates the MSR signal",
        f"- **Contradicts**: {total_row['contradicts']} pairs where classical text opposes the signal (requires review)",
        f"- **Partial**: {total_row['partial']} pairs with partial classical support",
        f"- **Extends**: {total_row['extends']} pairs where classical text adds nuance",
        f"- **Silent**: {total_row['silent']} pairs where classical text is irrelevant",
    ]

    FINDINGS_CLAIM.write_text("\n".join(lines), encoding="utf-8")
    log.info("Written %s", FINDINGS_CLAIM)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if not PROJECT:
        raise RuntimeError("GCP_PROJECT env var not set")
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL not set")

    log.info("=== M8-E-S1 Attribution Pass ===")
    log.info("Project: %s, Location: %s, Embed model: %s", PROJECT, LOCATION, EMBED_MODEL)
    log.info("Judge model: %s, Top-K: %d, Min similarity: %.2f", JUDGE_MODEL, TOP_K, MIN_SIMILARITY)

    # 1. Load MSR signals
    signals = load_msr_signals(MSR_PATH)
    if not signals:
        log.error("No signals parsed from %s — aborting", MSR_PATH)
        sys.exit(1)

    # 2. Embed all signal queries
    log.info("Embedding %d signal queries...", len(signals))
    queries = [build_query_text(s) for s in signals]
    embeddings = embed_queries(queries)
    log.info("Embedded %d queries", len(embeddings))

    # 3. Init Gemini judge
    vertexai.init(project=PROJECT, location=LOCATION)
    judge = GenerativeModel(JUDGE_MODEL)

    # 4. Main attribution loop
    all_records: list[dict[str, Any]] = []
    total_inserted = 0
    total_skipped  = 0

    with get_db() as conn:
        for i, (sig, embedding) in enumerate(zip(signals, embeddings)):
            if i % 50 == 0:
                log.info("Progress: %d/%d signals processed", i, len(signals))

            chunks = query_top_k_chunks(conn, embedding, k=TOP_K)
            if not chunks:
                continue

            for chunk in chunks:
                attr_type, confidence, notes = judge_attribution(
                    judge,
                    sig["signal_name"],
                    sig["classical_source"],
                    chunk,
                )

                record = {
                    "signal_id":        sig["signal_id"],
                    "signal_name":      sig["signal_name"],
                    "chunk_id":         chunk["chunk_id"],
                    "text_key":         chunk["text_key"],
                    "title":            chunk["title"],
                    "chapter":          chunk.get("chapter"),
                    "verse_range":      chunk.get("verse_range"),
                    "attribution_type": attr_type,
                    "confidence":       confidence,
                    "derivation_notes": notes,
                    "similarity":       float(chunk["similarity"]),
                }
                all_records.append(record)

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

            # Rate limit: ~2 Gemini calls/sec max
            time.sleep(0.2)

    log.info("Attribution pass complete: %d inserted, %d skipped (already exist)", total_inserted, total_skipped)
    log.info("Total records generated: %d", len(all_records))

    if len(all_records) < 400:
        log.warning(
            "WARNING: Only %d attribution records generated — acceptance criterion is ≥400.",
            len(all_records),
        )

    # 5. Build outputs
    build_registry(all_records)
    build_findings_cross_ref(all_records, signals)
    build_findings_claim(all_records)

    # 6. Summary
    type_counts: dict[str, int] = {}
    for r in all_records:
        type_counts[r["attribution_type"]] = type_counts.get(r["attribution_type"], 0) + 1

    log.info("=== ATTRIBUTION SUMMARY ===")
    for t, c in sorted(type_counts.items()):
        log.info("  %-12s: %d", t, c)
    log.info("  TOTAL       : %d", len(all_records))


if __name__ == "__main__":
    main()

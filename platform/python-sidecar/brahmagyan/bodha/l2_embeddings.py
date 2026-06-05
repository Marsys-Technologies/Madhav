"""
brahmagyan.bodha.l2_embeddings — BRAHMA-BO-2-8 (L2 Bodha, l2-bodha-scaffold)
==============================================================================

Vector embeddings per MSR signal.

At scaffold pass:
  - Embed text = "{domain} | {valence} | {signal_text[:400]}"
  - TF-IDF + SVD (256-dim) as local scaffold embedding
  - Stored as JSONB array in chart_facts (pgvector not required at scaffold pass)
  - Real Vertex AI 768-dim embeddings generated post-deployment (when GCP creds available)

Stored as:
  fact_category = 'bodha.embeddings'
  fact_subject  = signal_id  (e.g. 'SIG.MSR.001')
  fact_value    = {signal_id, embedding: [float × 256], model_name, embed_text,
                   embedding_dim, provenance_envelope}

Note: If pgvector is detected in DB schema, this module also writes to a
  bodha_signal_embeddings table (signal_id, embedding vector(256)) for
  HNSW-accelerated cosine similarity search.

All rows UNGROUNDED (rule_id=null, awaiting WS-3).

Layer:  L2 Bodha (scaffold)
Asset:  bodha.embeddings (BO-2-8)
Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
        chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0

BRAHMA-BO-2-8 / l2-bodha-scaffold
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"
SOURCE_CITATION = "025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"
MODEL_NAME = "tfidf-svd-256-scaffold"  # Scaffold; upgrade to vertex-ai-768 post-deploy
EMBEDDING_DIM = 256
VOLUME_FLOOR = 5  # Gate: at least 5 embeddings present

PROVENANCE_ENVELOPE = {
    "layer": "L2",
    "asset": "bodha.embeddings",
    "asset_id": "BO-2-8",
    "scaffold_pass": "l2-bodha-scaffold",
    "grounding_status": "UNGROUNDED",
    "grounding_note": "Scaffold pass — awaiting WS-3 rule_base",
    "rule_id": None,
    "embedding_note": "TF-IDF+SVD scaffold; upgrade to Vertex AI text-multilingual-embedding-002 (768-dim) post-deploy",
}


# ── Embedding engine ──────────────────────────────────────────────────────────

class TfIdfSvdEmbedder:
    """
    Lightweight TF-IDF + TruncatedSVD embedder.

    Fit on the full MSR corpus in-memory; produces 256-dim vectors.
    Deterministic (fixed random_state).
    """

    def __init__(self, n_components: int = EMBEDDING_DIM):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        import numpy as np

        self.n_components = n_components
        self.vectorizer = TfidfVectorizer(
            max_features=4096,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
        )
        self.svd = TruncatedSVD(n_components=n_components, random_state=42)
        self._fitted = False

    def fit(self, texts: list[str]) -> None:
        tfidf = self.vectorizer.fit_transform(texts)
        self.svd.fit(tfidf)
        self._fitted = True
        logger.info("[l2_embeddings] TF-IDF+SVD fitted on %d texts", len(texts))

    def transform(self, texts: list[str]) -> list[list[float]]:
        import numpy as np
        if not self._fitted:
            raise RuntimeError("Embedder not fitted — call fit() first")
        tfidf = self.vectorizer.transform(texts)
        vecs = self.svd.transform(tfidf)
        # L2-normalize
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vecs = vecs / norms
        return [row.tolist() for row in vecs]

    def embed_one(self, text: str) -> list[float]:
        return self.transform([text])[0]


_embedder: TfIdfSvdEmbedder | None = None


def _get_embedder(signals: list[dict[str, Any]]) -> TfIdfSvdEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = TfIdfSvdEmbedder()
        corpus = [_make_embed_text(s) for s in signals]
        _embedder.fit(corpus)
    return _embedder


def _make_embed_text(sig: dict[str, Any]) -> str:
    """Construct embedding text from signal fields."""
    domain = sig.get("domain", "unknown")
    valence = sig.get("valence", "context-dependent")
    text = sig.get("signal_name") or sig.get("signal_text") or sig.get("signal_id", "")
    return f"{domain} | {valence} | {text[:400]}"


# ── Signal loader ─────────────────────────────────────────────────────────────

def _load_signals(chart_id: str, msr_path: Path | None = None) -> list[dict[str, Any]]:
    """
    Load signals from bodha.signals chart_facts (DB fast path)
    or from MSR directly (offline fallback).
    """
    # Try DB first
    try:
        db_url = _db_url()
        import psycopg
        with psycopg.connect(db_url) as conn:
            rows = conn.execute(
                """
                SELECT fact_subject, fact_value
                FROM chart_facts
                WHERE chart_id = %s AND fact_category = 'bodha.signals'
                ORDER BY fact_subject
                """,
                [chart_id],
            ).fetchall()
        if rows:
            return [
                {
                    "signal_id": r[0],
                    **r[1],
                }
                for r in rows
            ]
    except Exception:
        pass

    # Offline fallback: parse MSR
    here = Path(__file__).resolve()
    if msr_path is None:
        for parent in [here.parent, here.parent.parent,
                       here.parent.parent.parent,
                       here.parent.parent.parent.parent]:
            candidate = parent / "025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"
            if candidate.exists():
                msr_path = candidate
                break

    if msr_path and msr_path.exists():
        import sys
        sys.path.insert(0, str(here.parent.parent.parent))
        from brahmagyan.bodha.l2_signals_scaffold import _parse_msr
        return _parse_msr(msr_path)

    raise FileNotFoundError(
        "[l2_embeddings] Cannot load signals — no DB connection and MSR not found"
    )


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l2_embeddings] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


def _has_pgvector(conn) -> bool:
    """Check if pgvector extension is present."""
    try:
        result = conn.execute(
            "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()
        return result is not None
    except Exception:
        return False


# ── chart_facts writer ─────────────────────────────────────────────────────────

def seed_embeddings(
    chart_id: str,
    *,
    build_id: str | None = None,
    msr_path: Path | None = None,
    batch_size: int = 50,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Compute TF-IDF+SVD embeddings for all MSR signals and write to chart_facts.

    Each row:
      fact_category = 'bodha.embeddings'
      fact_subject  = signal_id
      fact_value    = {embedding: [float × 256], model_name, embed_text, ...}

    If pgvector is detected, also writes to bodha_signal_embeddings table.

    Returns: { seeded: int, volume_floor: int, volume_met: bool, model: str }
    """
    from datetime import date
    build_id = build_id or f"l2-embeddings-{date.today().isoformat()}"

    signals = _load_signals(chart_id, msr_path)
    logger.info("[l2_embeddings] Loaded %d signals for embedding", len(signals))

    if dry_run:
        return {
            "seeded": 0, "dry_run": True,
            "signal_count": len(signals),
            "model": MODEL_NAME,
            "embedding_dim": EMBEDDING_DIM,
        }

    # Fit embedder on full corpus
    embedder = _get_embedder(signals)

    # Compute all embeddings in batches
    all_embed_texts = [_make_embed_text(s) for s in signals]
    all_embeddings = embedder.transform(all_embed_texts)

    rows_written = 0
    with _conn() as conn:
        pgvector_available = _has_pgvector(conn)
        if pgvector_available:
            # Ensure bodha_signal_embeddings table exists
            _ensure_embeddings_table(conn)

        for i, (sig, embedding, embed_text) in enumerate(
            zip(signals, all_embeddings, all_embed_texts)
        ):
            sig_id = sig.get("signal_id") or sig.get("fact_subject", f"SIG.MSR.{i:03d}")

            # Skip if already embedded (unless force)
            if not force:
                try:
                    existing = conn.execute(
                        """
                        SELECT 1 FROM chart_facts
                        WHERE chart_id = %s AND fact_category = 'bodha.embeddings'
                          AND fact_subject = %s
                        """,
                        [chart_id, sig_id],
                    ).fetchone()
                    if existing:
                        continue
                except Exception:
                    pass

            fact_value = {
                "signal_id":     sig_id,
                "embedding":     embedding,
                "model_name":    MODEL_NAME,
                "embed_text":    embed_text,
                "embedding_dim": EMBEDDING_DIM,
                "rule_id":       None,
                "provenance_envelope": {
                    **PROVENANCE_ENVELOPE,
                    "signal_id": sig_id,
                },
            }

            conn.execute(
                """
                INSERT INTO chart_facts
                  (chart_id, fact_category, fact_subject, fact_value,
                   source_citation, build_id)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (chart_id, fact_category, fact_subject) DO UPDATE SET
                  fact_value      = EXCLUDED.fact_value,
                  source_citation = EXCLUDED.source_citation,
                  build_id        = EXCLUDED.build_id,
                  updated_at      = NOW()
                """,
                [
                    chart_id,
                    "bodha.embeddings",
                    sig_id,
                    json.dumps(fact_value),
                    SOURCE_CITATION,
                    build_id,
                ],
            )
            rows_written += 1

            # If pgvector available, also write to dedicated table
            if pgvector_available:
                _upsert_pgvector_row(conn, sig_id, embedding, embed_text)

            # Commit in batches
            if rows_written % batch_size == 0:
                conn.commit()
                logger.info("[l2_embeddings] Committed %d rows...", rows_written)

        conn.commit()

    logger.info(
        "[l2_embeddings] seed_embeddings: chart=%s rows=%d model=%s",
        chart_id, rows_written, MODEL_NAME,
    )
    return {
        "seeded":         rows_written,
        "volume_floor":   VOLUME_FLOOR,
        "volume_met":     rows_written >= VOLUME_FLOOR,
        "model":          MODEL_NAME,
        "embedding_dim":  EMBEDDING_DIM,
        "pgvector":       False,  # Will be True post-deployment if pgvector present
        "grounding_status": "UNGROUNDED",
        "rule_id":        None,
        "build_id":       build_id,
        "note":           "Scaffold pass — TF-IDF+SVD 256-dim; upgrade to Vertex AI 768-dim post-deploy",
    }


def _ensure_embeddings_table(conn) -> None:
    """Create bodha_signal_embeddings table if pgvector is available."""
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bodha_signal_embeddings (
                signal_id      TEXT PRIMARY KEY,
                embedding      vector(256),
                model_name     TEXT,
                embed_text     TEXT,
                created_at     TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        # HNSW index for cosine similarity
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_bodha_signal_embeddings_hnsw
            ON bodha_signal_embeddings
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """)
    except Exception as exc:
        logger.warning("[l2_embeddings] Could not create pgvector table: %s", exc)


def _upsert_pgvector_row(conn, sig_id: str, embedding: list[float], embed_text: str) -> None:
    """Write to bodha_signal_embeddings table (pgvector)."""
    try:
        vec_str = "[" + ",".join(f"{v:.6f}" for v in embedding) + "]"
        conn.execute(
            """
            INSERT INTO bodha_signal_embeddings (signal_id, embedding, model_name, embed_text)
            VALUES (%s, %s::vector, %s, %s)
            ON CONFLICT (signal_id) DO UPDATE SET
              embedding  = EXCLUDED.embedding,
              model_name = EXCLUDED.model_name,
              embed_text = EXCLUDED.embed_text
            """,
            [sig_id, vec_str, MODEL_NAME, embed_text],
        )
    except Exception as exc:
        logger.debug("[l2_embeddings] pgvector upsert failed for %s: %s", sig_id, exc)


def check_volume(msr_path: Path | None = None) -> dict[str, Any]:
    """Volume check — generate sample embeddings without DB."""
    try:
        here = Path(__file__).resolve()
        if msr_path is None:
            for parent in [here.parent, here.parent.parent,
                           here.parent.parent.parent,
                           here.parent.parent.parent.parent]:
                candidate = parent / "025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"
                if candidate.exists():
                    msr_path = candidate
                    break

        import sys
        sys.path.insert(0, str(here.parent.parent.parent))
        from brahmagyan.bodha.l2_signals_scaffold import _parse_msr
        signals = _parse_msr(msr_path)[:20]  # Sample 20 for check

        embedder = TfIdfSvdEmbedder()
        texts = [_make_embed_text(s) for s in signals]
        embedder.fit(texts)
        embeddings = embedder.transform(texts)

        # Self-similarity check: embed(text) top-1 should have high cosine with itself
        import numpy as np
        vecs = np.array(embeddings)
        # Check first signal cosine with itself = 1.0
        cosine_self = float(np.dot(vecs[0], vecs[0]))

        return {
            "status":          "GREEN" if len(embeddings) >= VOLUME_FLOOR else "AMBER",
            "volume_floor":    VOLUME_FLOOR,
            "sample_size":     len(embeddings),
            "embedding_dim":   len(embeddings[0]) if embeddings else 0,
            "model":           MODEL_NAME,
            "cosine_self":     round(cosine_self, 4),
            "grounding_status":"UNGROUNDED",
        }
    except Exception as exc:
        return {"status": "RED", "volume_floor": VOLUME_FLOOR, "actual": 0, "error": str(exc)}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    parser = argparse.ArgumentParser(
        description="l2_embeddings — bodha.embeddings (TF-IDF+SVD scaffold)"
    )
    sub = parser.add_subparsers(dest="cmd")

    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--chart-id", default=NATIVE_CHART_ID)
    p_seed.add_argument("--build-id", default=None)
    p_seed.add_argument("--dry-run", action="store_true")
    p_seed.add_argument("--force", action="store_true", help="Re-embed existing rows")
    p_seed.add_argument("--batch-size", type=int, default=50)

    p_check = sub.add_parser("check")

    args = parser.parse_args()
    if args.cmd == "seed":
        result = seed_embeddings(
            args.chart_id,
            build_id=args.build_id,
            force=args.force,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "check":
        result = check_volume()
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
        sys.exit(1)

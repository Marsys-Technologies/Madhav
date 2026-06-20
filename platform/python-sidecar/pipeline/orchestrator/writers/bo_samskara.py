"""
bo_samskara — Signal Embeddings (L2 Bodha)
==========================================
Creates one bodha_signal_embeddings row per bodha_msr_signals row (1:1).

Embedding strategy: deterministic hash-seeded vector (placeholder_hash_v1).
  - SHA-256 of embedding_input_summary → seed for numpy random generator
  - Gaussian sample → L2-normalize → 768-dim unit vector
  - embedding_model = 'placeholder_hash_v1' marks this as a deterministic placeholder
  - Semantically opaque but fully deterministic; replace by re-running after wiring
    a real embedding service.

NOTE: numpy is required. If not installed: `pip install numpy` in the sidecar venv.

LIGHT writer — one run() call over all ayanamshas.
"""
from __future__ import annotations

import hashlib
import json
import logging
import struct
import uuid
from datetime import datetime, timezone

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION   = "bo_samskara_v1.0"
EMBEDDING_MODEL  = "placeholder_hash_v1"
EMBEDDING_VER    = "1.0"
EMBEDDING_DIM    = 768
CANONICAL_AYAS   = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

_INSERT = """
INSERT INTO bodha_signal_embeddings (
  embedding_id, signal_id, chart_id, ayanamsha_id, build_id,
  embedding_vec, embedding_model, embedding_model_version,
  embedding_input_summary, computed_at
) VALUES (
  %(embedding_id)s, %(signal_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
  %(embedding_vec)s::vector, %(embedding_model)s, %(embedding_model_version)s,
  %(embedding_input_summary)s, %(computed_at)s
)
ON CONFLICT (signal_id) DO UPDATE SET
  embedding_model         = EXCLUDED.embedding_model,
  embedding_model_version = EXCLUDED.embedding_model_version,
  embedding_vec           = EXCLUDED.embedding_vec,
  embedding_input_summary = EXCLUDED.embedding_input_summary,
  computed_at             = EXCLUDED.computed_at
"""

_BATCH_SIZE = 10


def _text_to_deterministic_vec(text: str) -> list[float]:
    """
    Deterministic 768-dim unit vector seeded from SHA-256(text).
    Uses only stdlib + numpy (no ML model needed).
    """
    import numpy as np  # noqa: PLC0415
    seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()
    # Use first 8 bytes as uint64 seed
    seed = struct.unpack("<Q", seed_bytes[:8])[0]
    rng  = np.random.default_rng(seed)
    vec  = rng.standard_normal(EMBEDDING_DIM).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def _build_input_summary(sig: dict) -> str:
    """
    Build a short text from signal fields for use as the embedding input.
    Deterministic: same signal → same text → same vector.
    """
    parts = [
        str(sig.get("signal_type_class") or ""),
        str(sig.get("signal_tradition") or ""),
        str(sig.get("signal_type_id") or ""),
    ]
    cfg_raw = sig.get("configuration_jsonb") or {}
    if isinstance(cfg_raw, str):
        try:
            cfg = json.loads(cfg_raw)
        except Exception:
            cfg = {}
    else:
        cfg = cfg_raw

    # Append key fields from config
    for key in ("fact_key", "fact_value_text", "graha", "yoga", "dosha"):
        if cfg.get(key):
            parts.append(f"{key}={cfg[key]}")

    domains = sig.get("domains_affected_array") or []
    if domains:
        parts.append("domains=" + ",".join(sorted(domains)))

    return " | ".join(p for p in parts if p)[:512]


def _fetch_signals(conn, chart_id: str, aya: str) -> list[dict]:
    rows = conn.execute(
        """SELECT signal_id, ayanamsha_id, signal_type_class, signal_tradition,
                  signal_type_id, configuration_jsonb, domains_affected_array
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, aya],
    ).fetchall()
    keys = [
        "signal_id", "ayanamsha_id", "signal_type_class", "signal_tradition",
        "signal_type_id", "configuration_jsonb", "domains_affected_array",
    ]
    return [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]


def _batch_insert(conn, rows: list[dict]) -> int:
    inserted = 0
    total = len(rows)
    with conn.cursor() as cur:
        for i in range(0, total, _BATCH_SIZE):
            batch = rows[i:i + _BATCH_SIZE]
            try:
                cur.executemany(_INSERT, batch)
            except Exception:
                logger.warning("[bo_samskara] batch at %d failed, falling back per-row", i)
                for row in batch:
                    try:
                        cur.execute("SAVEPOINT row_sp")
                        cur.execute(_INSERT, row)
                        cur.execute("RELEASE SAVEPOINT row_sp")
                    except Exception as row_exc:
                        cur.execute("ROLLBACK TO SAVEPOINT row_sp")
                        logger.warning("[bo_samskara] skipping embedding %s: %s",
                                       row.get("signal_id"), row_exc)
            inserted += len(batch)
            if inserted % 2000 == 0 or i + _BATCH_SIZE >= total:
                logger.info("[bo_samskara] embedded %d/%d", inserted, total)
    return inserted


@register("bo_samskara")
class BoSamskaraWriter(WriterBase):
    """bo_samskara: deterministic signal embeddings (1:1 with MSR signals)."""
    asset_id = "bo_samskara"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_signal_embeddings

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()
        total    = 0

        for aya in CANONICAL_AYAS:
            signals = _fetch_signals(conn, chart_id, aya)

            if ctx.dry_run:
                logger.info("[bo_samskara dry_run] %s — %d signals", aya, len(signals))
                continue

            rows: list[dict] = []
            for sig in signals:
                summary = _build_input_summary(sig)
                vec     = _text_to_deterministic_vec(summary)
                rows.append({
                    "embedding_id":             str(uuid.uuid4()),
                    "signal_id":                str(sig["signal_id"]),
                    "chart_id":                 chart_id,
                    "ayanamsha_id":             aya,
                    "build_id":                 build_id,
                    "embedding_vec":            "[" + ",".join(f"{v:.8f}" for v in vec) + "]",
                    "embedding_model":          EMBEDDING_MODEL,
                    "embedding_model_version":  EMBEDDING_VER,
                    "embedding_input_summary":  summary,
                    "computed_at":              now,
                })

            replace_prior_signal_embeddings(conn, chart_id, aya)
            logger.info("[bo_samskara] %s — inserting %d embeddings", aya, len(rows))
            total += _batch_insert(conn, rows)

        return WriterResult(asset_id=self.asset_id, rows_inserted=total)

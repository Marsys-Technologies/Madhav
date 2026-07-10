"""
bo_samskara — Signal Embeddings (L2 Bodha)
==========================================
Creates one bodha_signal_embeddings row per bodha_msr_signals row (1:1).

Embedding strategy: Vertex AI text-multilingual-embedding-002 (768-dim).
  - embedding_model = 'text-multilingual-embedding-002'
  - Batched via google-genai client (EMBED_BATCH_SIZE=100)
  - Real semantic vectors replacing the placeholder_hash_v1 deterministic approach.

HEAVY writer: plan_substeps returns one SubStep per ayanamsha.
Each sub-step runs inside its own SAVEPOINT managed by the orchestrator.
~13,363 signals per ayanamsha → ~134 API calls → ~2-4 min per substep,
well within the 600s per-substep limit.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, SubStep, register

logger = logging.getLogger(__name__)

ENGINE_VERSION   = "bo_samskara_v1.0"
EMBEDDING_MODEL  = "text-multilingual-embedding-002"
EMBEDDING_VER    = "002"
EMBEDDING_DIM    = 768
GCP_PROJECT      = os.environ.get("GCP_PROJECT", "madhav-astrology")
VERTEX_LOCATION  = os.environ.get("VERTEX_AI_LOCATION", "asia-south1")
EMBED_BATCH_SIZE = 100

_genai_client: Any = None

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


def _get_genai_client() -> Any:
    global _genai_client
    if _genai_client is None:
        from google import genai  # noqa: PLC0415
        _genai_client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT,
            location=VERTEX_LOCATION,
        )
    return _genai_client


def _embed_batch(texts: list[str]) -> list[list[float]]:
    client = _get_genai_client()
    resp = client.models.embed_content(model=EMBEDDING_MODEL, contents=texts)
    return [list(e.values) for e in resp.embeddings]


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
    # Role-default statement_timeout=30s is sized for OLTP queries; a full
    # per-(chart_id, ayanamsha_id) scan of bodha_msr_signals can exceed it
    # under load (observed live: QueryCanceled on this exact SELECT during a
    # concurrent multi-asset rebuild, 2026-07-10). SET LOCAL scopes to this
    # transaction/savepoint only and reverts automatically on commit/rollback
    # — the same pattern already used by every other heavy per-chart writer
    # in this codebase (ka_taranga, ph_pramana, ka_yojaka, etc.) for exactly
    # this reason; bo_samskara was simply missing it.
    with conn.cursor() as _timeout_cur:
        _timeout_cur.execute("SET LOCAL statement_timeout = 0")
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
                inserted += max(0, cur.rowcount)
            except Exception:
                logger.warning("[bo_samskara] batch at %d failed, falling back per-row", i)
                for row in batch:
                    try:
                        cur.execute("SAVEPOINT row_sp")
                        cur.execute(_INSERT, row)
                        cur.execute("RELEASE SAVEPOINT row_sp")
                        inserted += max(0, cur.rowcount)
                    except Exception as row_exc:
                        cur.execute("ROLLBACK TO SAVEPOINT row_sp")
                        logger.warning("[bo_samskara] skipping embedding %s: %s",
                                       row.get("signal_id"), row_exc)
            if inserted % 2000 == 0 or i + _BATCH_SIZE >= total:
                logger.info("[bo_samskara] embedded %d/%d", inserted, total)
    return inserted


@register("bo_samskara")
class BoSamskaraWriter(WriterBase):
    """bo_samskara: deterministic signal embeddings (1:1 with MSR signals)."""
    asset_id = "bo_samskara"
    has_substeps = True

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [
            SubStep(key=f"aya_{aya}", label=f"bo_samskara — {aya}")
            for aya in CANONICAL_AYAS
        ]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_signal_embeddings

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()
        aya      = step.key.removeprefix("aya_")

        signals = _fetch_signals(conn, chart_id, aya)

        if ctx.dry_run:
            logger.info("[bo_samskara dry_run] %s — %d signals", aya, len(signals))
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"dry_run:{aya}:{len(signals)}_signals")

        if not signals:
            logger.info("[bo_samskara] %s — no signals; skipping", aya)
            return WriterResult(asset_id=self.asset_id, rows_inserted=0)

        # Build (signal, summary) pairs first
        signal_summaries: list[tuple[dict, str]] = [
            (sig, _build_input_summary(sig)) for sig in signals
        ]

        # Batch-embed all summaries for this ayanamsha
        rows: list[dict] = []
        for batch_start in range(0, len(signal_summaries), EMBED_BATCH_SIZE):
            batch = signal_summaries[batch_start:batch_start + EMBED_BATCH_SIZE]
            batch_texts = [summary for _, summary in batch]
            try:
                vecs = _embed_batch(batch_texts)
            except Exception as exc:
                # Previously uncaught: any embedding-API exception on any one
                # batch aborted the whole ayanamsha substep, and whether that
                # read as a hard build failure or a quiet no-op depended on
                # orchestrator-level retry/catch behavior — this is exactly how
                # 4 of 5 ayanamshas' embeddings went missing without the
                # bo_pramana_mapa scorecard ever being told. Log loudly and
                # skip only this batch so the remaining batches (and other
                # ayanamsha substeps) still get a chance to write real rows.
                logger.warning(
                    "[bo_samskara] %s — embedding batch at offset %d failed "
                    "(%d signals lost from this batch): %s",
                    aya, batch_start, len(batch), exc,
                )
                continue
            for (sig, summary), vec in zip(batch, vecs):
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
        inserted = _batch_insert(conn, rows)

        if len(signals) > 0 and inserted == 0:
            raise RuntimeError(
                f"[bo_samskara] G3: chart_id={chart_id} aya={aya} — "
                f"{len(signals)} signals found but 0 embeddings written; "
                "all Vertex AI embedding batches failed"
            )
        if inserted < len(signals):
            # Partial coverage for this ayanamsha — not a hard failure (some
            # embeddings did land), but a silent partial loss here is exactly
            # how bo_pramana_mapa's scorecard went stale relative to live data
            # (embedding_count contradicted the live table by 4 of 5
            # ayanamshas). Surface it loudly so a partial substep failure
            # can't look like a clean no-op.
            logger.warning(
                "[bo_samskara] G3-partial: chart_id=%s aya=%s — %d/%d signals "
                "embedded; %d signal(s) missing an embedding (embedding-API "
                "batch/row failures — see prior warnings)",
                chart_id, aya, inserted, len(signals), len(signals) - inserted,
            )
        return WriterResult(asset_id=self.asset_id, rows_inserted=inserted)

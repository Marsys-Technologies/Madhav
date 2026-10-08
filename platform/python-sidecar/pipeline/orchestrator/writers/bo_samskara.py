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
import random
import time
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, SubStep, register
from bodha_writers.data_plane_contracts import l2_producer, stable_semantic_uuid

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
INSERT INTO public.bodha_signal_embeddings (
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


# ── Bounded retry-with-backoff for one embedding batch (S-L2 run 2 hardening) ──
# ~1,270 sequential Vertex calls per full generation: a single transient 429/5xx/
# timeout must not abort a whole ayanamsha sub-step. Retries are bounded, apply only
# to transient errors, and re-send the SAME batch content (idempotent). If the batch
# still fails after the last attempt the caller raises "refusing a partial generation"
# exactly as before: nothing is skipped and nothing is partially written.
EMBED_MAX_ATTEMPTS = 5
EMBED_BACKOFF_BASE_S = 1.0      # gaps after failed attempts 1..4: 1, 2, 4, 8 s (cap 16 s)
EMBED_BACKOFF_CAP_S = 16.0
EMBED_BACKOFF_JITTER = 0.25     # +-25 %

# Injectable for tests (monkeypatch these module attributes, or pass sleep=/rand=).
_retry_sleep = time.sleep
_retry_random = random.random   # returns a float in [0.0, 1.0)

_TRANSIENT_CLASS_NAMES = frozenset({
    "TimeoutException", "NetworkError", "RemoteProtocolError",
    "ConnectTimeout", "ReadTimeout", "WriteTimeout", "PoolTimeout",
    "ConnectError", "ReadError", "WriteError",
})


def _http_status_of(exc: BaseException) -> int | None:
    """HTTP status carried by an SDK/HTTP exception, or None when it carries none."""
    candidates = [getattr(exc, "code", None), getattr(exc, "status_code", None),
                  getattr(exc, "status", None)]
    resp = getattr(exc, "response", None)
    if resp is not None:
        candidates.append(getattr(resp, "status_code", None))
    for c in candidates:
        if isinstance(c, int) and not isinstance(c, bool) and 100 <= c <= 599:
            return c
    return None


def _is_transient_embed_error(exc: BaseException) -> bool:
    """True only for HTTP 429 / 5xx, timeouts and connection resets.

    Anything else (auth 401/403, other 4xx, shape/value/type errors, unknown
    exception types) is NOT transient and fails immediately.
    """
    status = _http_status_of(exc)
    if status is not None:
        return status == 429 or 500 <= status <= 599
    if isinstance(exc, (TimeoutError, ConnectionError)):  # incl. ConnectionResetError
        return True
    for klass in type(exc).__mro__:
        if (klass.__name__ in _TRANSIENT_CLASS_NAMES
                and klass.__module__.split(".")[0] in ("httpx", "httpcore")):
            return True
    return False


def _backoff_delay(failed_attempt: int, rand: Any) -> float:
    """Delay after failed attempt N (1-based): min(cap, base*2^(N-1)) +-25 % jitter."""
    base = min(EMBED_BACKOFF_CAP_S, EMBED_BACKOFF_BASE_S * (2 ** (failed_attempt - 1)))
    return base * (1.0 + EMBED_BACKOFF_JITTER * (2.0 * rand() - 1.0))


# ── Idle-in-transaction keepalive (production run 2af5c8a2, 2026-10-08) ──
# ctx.db_conn sits inside the orchestrator's open transaction/savepoint for the whole
# embedding loop (~254 sequential Vertex calls, 28-40+ min). The server's
# idle_in_transaction_session_timeout (1800 s, set by orchestrator/db.py) then killed
# the connection at replace_prior_signal_embeddings of the 4th ayanamsha. A trivial
# statement on the SAME connection resets the idle clock without committing, rolling
# back, or opening a new connection (the orchestrator keeps sole ownership of the
# transaction). A failing keepalive means the connection is already dead: it
# propagates (fail loud) rather than being swallowed.
KEEPALIVE_INTERVAL_S = 30.0     # time-guarded pings (retry waits) at least this often
_monotonic = time.monotonic     # injectable for tests


def _keepalive(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT 1")


def _embed_batch_with_retry(
    texts: list[str], *, sleep: Any = None, rand: Any = None, on_wait: Any = None,
) -> list[list[float]]:
    sleep = _retry_sleep if sleep is None else sleep
    rand = _retry_random if rand is None else rand
    for attempt in range(1, EMBED_MAX_ATTEMPTS + 1):
        try:
            return _embed_batch(texts)
        except Exception as exc:
            if not _is_transient_embed_error(exc) or attempt == EMBED_MAX_ATTEMPTS:
                raise
            if on_wait is not None:
                on_wait()   # keep the DB connection non-idle across a long retry cycle
            delay = _backoff_delay(attempt, rand)
            logger.warning(
                "[bo_samskara] transient embedding error (%s, status=%s) on attempt %d/%d; "
                "retrying same batch in %.2fs",
                type(exc).__name__, _http_status_of(exc), attempt, EMBED_MAX_ATTEMPTS, delay,
            )
            sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover


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


def _fetch_existing_embeddings(conn, chart_id: str, aya: str) -> dict[str, dict]:
    """signal_id -> {embedding_input_summary, embedding_vec (text), embedding_model,
    embedding_model_version} for this chart/ayanamsha's CURRENT rows — read before
    replace_prior_signal_embeddings deletes them, so a rebuild can reuse an
    embedding whose input text hasn't changed instead of re-calling Vertex AI.
    _build_input_summary is a pure function of already-stored signal fields, so an
    unchanged summary guarantees the reused vector is the value Vertex would return
    for the same input again — this is the perf-pre-D3 embedding-reuse optimization."""
    rows = conn.execute(
        """SELECT signal_id, embedding_input_summary, embedding_vec::text,
                  embedding_model, embedding_model_version
           FROM public.bodha_signal_embeddings
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, aya],
    ).fetchall()
    keys = ["signal_id", "embedding_input_summary", "embedding_vec",
            "embedding_model", "embedding_model_version"]
    out: dict[str, dict] = {}
    for r in rows:
        d = dict(zip(keys, r)) if not isinstance(r, dict) else r
        out[str(d["signal_id"])] = d
    return out


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
@l2_producer("bo_samskara")
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

        # perf-pre-D3: reuse a prior embedding when its stored input text is
        # byte-identical (same model+version too) — _build_input_summary is a pure
        # function of already-stored signal fields, so an unchanged summary means
        # Vertex would return the same vector again. Read BEFORE
        # replace_prior_signal_embeddings (below) deletes the current rows.
        existing = _fetch_existing_embeddings(conn, chart_id, aya)
        rows: list[dict] = []
        to_embed: list[tuple[dict, str]] = []
        reused_count = 0
        for sig, summary in signal_summaries:
            prior = existing.get(str(sig["signal_id"]))
            if (prior is not None
                    and prior["embedding_input_summary"] == summary
                    and prior["embedding_model"] == EMBEDDING_MODEL
                    and prior["embedding_model_version"] == EMBEDDING_VER):
                rows.append({
                    "embedding_id":             stable_semantic_uuid("signal_embedding", {
                        "signal_id": str(sig["signal_id"]),
                        "embedding_model": EMBEDDING_MODEL,
                        "embedding_model_version": EMBEDDING_VER,
                    }),
                    "signal_id":                str(sig["signal_id"]),
                    "chart_id":                 chart_id,
                    "ayanamsha_id":             aya,
                    "build_id":                 build_id,
                    "embedding_vec":            prior["embedding_vec"],
                    "embedding_model":          EMBEDDING_MODEL,
                    "embedding_model_version":  EMBEDDING_VER,
                    "embedding_input_summary":  summary,
                    "computed_at":              now,
                })
                reused_count += 1
            else:
                to_embed.append((sig, summary))
        if reused_count:
            logger.info("[bo_samskara] %s — reused %d/%d embeddings (unchanged input text)",
                        aya, reused_count, len(signal_summaries))

        # Batch-embed only the summaries that changed or are new for this ayanamsha.
        # All Vertex calls happen before the first DB write of this substep; the
        # connection is kept non-idle meanwhile (see _keepalive).
        last_ping = _monotonic()

        def _ping_if_due() -> None:
            nonlocal last_ping
            if _monotonic() - last_ping >= KEEPALIVE_INTERVAL_S:
                _keepalive(conn)
                last_ping = _monotonic()

        for batch_start in range(0, len(to_embed), EMBED_BATCH_SIZE):
            batch = to_embed[batch_start:batch_start + EMBED_BATCH_SIZE]
            batch_texts = [summary for _, summary in batch]
            try:
                vecs = _embed_batch_with_retry(batch_texts, on_wait=_ping_if_due)
            except Exception as exc:
                raise RuntimeError(
                    f"[bo_samskara] {aya} — embedding batch at offset "
                    f"{batch_start} failed; refusing a partial generation"
                ) from exc
            for (sig, summary), vec in zip(batch, vecs):
                rows.append({
                    "embedding_id":             stable_semantic_uuid("signal_embedding", {
                        "signal_id": str(sig["signal_id"]),
                        "embedding_model": EMBEDDING_MODEL,
                        "embedding_model_version": EMBEDDING_VER,
                    }),
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
            _keepalive(conn)
            last_ping = _monotonic()

        replace_prior_signal_embeddings(conn, chart_id, aya)
        logger.info("[bo_samskara] %s — inserting %d embeddings", aya, len(rows))
        inserted = _batch_insert(conn, rows)

        if len(signals) > 0 and inserted == 0:
            raise RuntimeError(
                f"[bo_samskara] G3: chart_id={chart_id} aya={aya} — "
                f"{len(signals)} signals found but 0 embeddings written; "
                "all Vertex AI embedding batches failed"
            )
        if inserted != len(signals):
            raise RuntimeError(
                f"[bo_samskara] G3-partial: chart_id={chart_id} aya={aya} — "
                f"{inserted}/{len(signals)} embeddings written; refusing a "
                "partial generation"
            )
        return WriterResult(asset_id=self.asset_id, rows_inserted=inserted, rows_skipped=0)

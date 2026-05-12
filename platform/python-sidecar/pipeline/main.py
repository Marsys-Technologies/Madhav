"""
pipeline.main — MARSYS-JIS build pipeline orchestrator.
Phase 14B.

Reads VALIDATED_ASSET_REGISTRY from GCS, fetches CURRENT assets, chunks via
existing chunkers (rag/chunkers/*), embeds via Vertex AI, writes to staging
tables, validates, and optionally swaps to live.

Usage:
  python -m pipeline.main [--registry-uri GS_URI] [--build-id ID]
                          [--triggered-by STR] [--dry-run] [--skip-swap]
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import concurrent.futures
import structlog
import vertexai
from google.api_core import exceptions as gax_exceptions
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

_EMBED_TIMEOUT_S = 120
_EMBED_MODEL: TextEmbeddingModel | None = None

from pipeline.manifest_writer import EMBEDDING_DIM, EMBEDDING_MODEL, write_manifest
from pipeline.registry_loader import collect_current_assets, load_registry
from pipeline.source_fetcher import fetch_all_assets
from pipeline.validators import ValidatedAssetRegistry
from pipeline.writers.rag_chunks_writer import RAGChunksWriter
from pipeline.writers.msr_signals_writer import MSRSignalsWriter
from pipeline.writers.ucn_sections_writer import UCNSectionsWriter
from pipeline.writers.cdlm_links_writer import CDLMLinksWriter
from pipeline.writers.cgm_nodes_writer import CGMNodesWriter
from pipeline.writers.cgm_edges_writer import CGMEdgesWriter
from pipeline.writers.rm_resonances_writer import RMResonancesWriter
from pipeline.writers.chart_facts_writer import ChartFactsWriter
from pipeline.writers.eclipses_writer import EclipsesWriter
from pipeline.writers.retrogrades_writer import RetrogradesWriter
from pipeline.writers.life_events_writer import LifeEventsWriter
from pipeline.writers.sade_sati_writer import SadeSatiWriter

# ── Logging setup ─────────────────────────────────────────────────────────────

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = structlog.get_logger(__name__)

# ── Chunker registry ──────────────────────────────────────────────────────────
# Maps asset path (relative) → (doc_type, chunker_function).
# 14C/14D/14E add new entries here when new writers are registered.

def _build_chunker_registry() -> dict[str, tuple[str, Any]]:
    from rag.chunkers.cdlm_cell import chunk_cdlm_cells
    from rag.chunkers.cgm_node import chunk_cgm_nodes
    from rag.chunkers.l1_fact import chunk_l1_facts
    from rag.chunkers.lel_chunker import chunk_lel_sections
    from rag.chunkers.msr_signal import chunk_msr_signals
    from rag.chunkers.rm_element import chunk_rm_elements
    from rag.chunkers.ucn_section import chunk_ucn_sections
    # Wave 5 M2-D234-BUNDLE
    from rag.chunkers.timeline_chunker import chunk_timeline_sections

    return {
        "01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md": ("l1_fact", chunk_l1_facts),
        # lel_section is a log label only; actual doc_types (lel_period_summary,
        # lel_chronic_pattern) come from the chunks themselves.
        "01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md": ("lel_section", chunk_lel_sections),
        "025_HOLISTIC_SYNTHESIS/MSR_v3_0.md": ("msr_signal", chunk_msr_signals),
        "025_HOLISTIC_SYNTHESIS/UCN_v4_0.md": ("ucn_section", chunk_ucn_sections),
        "025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md": ("cdlm_cell", chunk_cdlm_cells),
        "025_HOLISTIC_SYNTHESIS/CGM_v9_0.md": ("cgm_node", chunk_cgm_nodes),
        "025_HOLISTIC_SYNTHESIS/RM_v2_0.md": ("rm_element", chunk_rm_elements),
        "05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md": ("l5_timeline", chunk_timeline_sections),
    }


# ── Vertex AI embedding ───────────────────────────────────────────────────────

def _init_vertexai() -> None:
    global _EMBED_MODEL
    project = os.environ.get("GCP_PROJECT", "")
    location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
    if not project:
        raise RuntimeError("GCP_PROJECT env var not set")
    vertexai.init(project=project, location=location)
    _EMBED_MODEL = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
    log.info("vertex_init", project=project, location=location, model=EMBEDDING_MODEL)


def _embed_batch(texts: list[str]) -> list[list[float]]:
    assert _EMBED_MODEL is not None, "call _init_vertexai() first"
    inputs = [TextEmbeddingInput(t, "RETRIEVAL_DOCUMENT") for t in texts]
    # Wrap in a thread + Future with hard timeout. The SDK's get_embeddings has no
    # timeout kwarg and the underlying gRPC channel relies on kernel TCP keepalives
    # (~2h on macOS), so silent stream-breaks can otherwise wedge the call indefinitely.
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_EMBED_MODEL.get_embeddings, inputs)
        results = future.result(timeout=_EMBED_TIMEOUT_S)
    return [r.values for r in results]


def _embed_chunks(chunks: list[Any]) -> list[list[float]]:
    """
    Embed all chunks. Batch size 20 keeps each request under the model's 20k-token
    per-request cap even with the 800-token worst-case chunk. Retries transient
    errors (5 attempts, 5/15/45/90/180s). InvalidArgument (400) is deterministic
    and re-raised immediately.
    """
    batch_size = 20
    all_embeddings: list[list[float]] = []
    backoffs = [5, 15, 45, 90, 180]

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [
            f"[{c.layer}] [{c.doc_type}]\n{c.content}" for c in batch
        ]
        vecs = None
        last_exc: Exception | None = None
        for attempt, delay in enumerate([0] + backoffs):
            if delay:
                log.warning("vertex_retry", batch_start=i, attempt=attempt, delay_s=delay, prior_error=str(last_exc))
                time.sleep(delay)
            try:
                vecs = _embed_batch(texts)
                break
            except gax_exceptions.InvalidArgument as exc:
                raise RuntimeError(
                    f"[STOP] Vertex AI rejected batch {i} (deterministic, no retry): {exc}"
                ) from exc
            except Exception as exc:
                last_exc = exc
        if vecs is None:
            raise RuntimeError(
                f"[STOP] Vertex AI embedding failed at batch {i} after {len(backoffs) + 1} attempts: {last_exc}"
            ) from last_exc
        all_embeddings.extend(vecs)
        log.info("embedded_batch", start=i, end=i + len(batch), total_so_far=len(all_embeddings))

    return all_embeddings


# ── Build manifest DB row ─────────────────────────────────────────────────────

def _insert_manifest_row(
    build_id: str,
    triggered_by: str,
    registry_fingerprint: str,
    pipeline_image_uri: str,
    status: str = "staging",
) -> None:
    import psycopg
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    with psycopg.connect(db_url, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3) as conn:
        conn.execute(
            """
            INSERT INTO build_manifests
              (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
               embedding_model, embedding_dim, chunk_count, embedding_count,
               status, manifest_uri)
            VALUES (%s, %s, %s, %s, %s, %s, 0, 0, %s, '')
            ON CONFLICT (build_id) DO NOTHING
            """,
            (
                build_id,
                triggered_by,
                registry_fingerprint,
                pipeline_image_uri,
                EMBEDDING_MODEL,
                EMBEDDING_DIM,
                status,
            ),
        )
        conn.commit()


def _update_manifest_row(
    build_id: str,
    chunk_count: int,
    embedding_count: int,
    status: str,
    manifest_uri: str,
) -> None:
    import psycopg
    db_url = os.environ.get("DATABASE_URL", "")
    with psycopg.connect(db_url, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3) as conn:
        conn.execute(
            """
            UPDATE build_manifests
            SET chunk_count=%s, embedding_count=%s, status=%s, manifest_uri=%s
            WHERE build_id=%s
            """,
            (chunk_count, embedding_count, status, manifest_uri, build_id),
        )
        conn.commit()


# ── L1 structured writer step (14C) ──────────────────────────────────────────

def _run_l1_writers(build_id: str, skip_swap: bool, log: Any) -> None:
    """Run all L1 structured writers (chart_facts, eclipses, retrogrades, life_events, sade_sati)."""
    from pipeline.writers.chart_facts_writer import load_from_gcs as load_chart_facts
    from pipeline.writers.eclipses_writer import load_from_gcs as load_eclipses
    from pipeline.writers.retrogrades_writer import load_from_gcs as load_retrogrades
    from pipeline.writers.life_events_writer import LifeEventsWriter
    from pipeline.writers.sade_sati_writer import SadeSatiWriter
    from pipeline.extractors.life_event_extractor import extract_life_events
    from pipeline.extractors.sade_sati_extractor import extract_sade_sati_phases

    writers_and_loaders = [
        ("chart_facts",   ChartFactsWriter,   load_chart_facts),
        ("eclipses",      EclipsesWriter,     load_eclipses),
        ("retrogrades",   RetrogradesWriter,  load_retrogrades),
        ("life_events",   LifeEventsWriter,   extract_life_events),
        ("sade_sati",     SadeSatiWriter,     extract_sade_sati_phases),
    ]

    for name, WriterClass, loader in writers_and_loaders:
        log.info("l1_writer_start", writer=name)
        try:
            rows = loader()
            writer = WriterClass()
            result = writer.write_to_staging(rows, build_id)
            log.info("l1_staging_written", writer=name, row_count=result.row_count)

            validation = writer.validate_staging(build_id)
            if not validation.valid:
                log.error("l1_validation_failed", writer=name, issues=validation.issues)
                raise RuntimeError(f"L1 staging validation failed for {name}: {validation.issues}")
            log.info("l1_staging_validated", writer=name, row_count=validation.row_count)

            if not skip_swap:
                swap = writer.swap_to_live(build_id)
                if not swap.success:
                    log.error("l1_swap_failed", writer=name, message=swap.message)
                    raise RuntimeError(f"L1 swap failed for {name}: {swap.message}")
                log.info("l1_swap_complete", writer=name, promoted=swap.promoted_chunk_count)
        except Exception as exc:
            log.error("l1_writer_error", writer=name, error=str(exc))
            raise


# ── L2.5 structured writer step (14D) ────────────────────────────────────────

def _run_l25_writers(workspace: str, build_id: str, skip_swap: bool, log: Any) -> None:
    """Run all six L2.5 structured writers (extract → stage → validate → swap)."""
    from pipeline.extractors.msr_extractor import extract_msr_signals
    from pipeline.extractors.ucn_extractor import extract_ucn_sections
    from pipeline.extractors.cdlm_extractor import extract_cdlm_links
    from pipeline.extractors.cgm_extractor import extract_cgm_nodes, extract_cgm_edges
    from pipeline.extractors.rm_extractor import extract_rm_resonances

    writers_and_extractors = [
        ("msr_signals",   MSRSignalsWriter,   lambda: extract_msr_signals(workspace)),
        ("ucn_sections",  UCNSectionsWriter,  lambda: extract_ucn_sections(workspace)),
        ("cdlm_links",    CDLMLinksWriter,    lambda: extract_cdlm_links(workspace)),
        ("cgm_nodes",     CGMNodesWriter,     lambda: extract_cgm_nodes(workspace)),
        ("cgm_edges",     CGMEdgesWriter,     lambda: extract_cgm_edges(workspace)),
        ("rm_resonances", RMResonancesWriter, lambda: extract_rm_resonances(workspace)),
    ]

    for name, WriterClass, extractor in writers_and_extractors:
        log.info("l25_writer_start", writer=name)
        try:
            rows = extractor()
            writer = WriterClass()
            result = writer.write_to_staging(rows, build_id)
            log.info("l25_staging_written", writer=name, row_count=result.row_count)

            validation = writer.validate_staging(build_id)
            if not validation.valid:
                log.error("l25_validation_failed", writer=name, issues=validation.issues)
                raise RuntimeError(f"L2.5 staging validation failed for {name}: {validation.issues}")
            log.info("l25_staging_validated", writer=name, row_count=validation.row_count)

            if not skip_swap:
                swap = writer.swap_to_live(build_id)
                if not swap.success:
                    log.error("l25_swap_failed", writer=name, message=swap.message)
                    raise RuntimeError(f"L2.5 swap failed for {name}: {swap.message}")
                log.info("l25_swap_complete", writer=name, promoted=swap.promoted_chunk_count)
        except Exception as exc:
            log.error("l25_writer_error", writer=name, error=str(exc))
            raise


# ── Main orchestration ────────────────────────────────────────────────────────

def run_build(
    registry_uri: str,
    build_id: str,
    triggered_by: str,
    dry_run: bool,
    skip_swap: bool,
    sources_bucket: str,
    artifacts_bucket: str,
    pipeline_image_uri: str,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    log.info("build_start", build_id=build_id, registry_uri=registry_uri, dry_run=dry_run, skip_swap=skip_swap)

    # Workspace root: in the container /app is WORKDIR and matches the dev repo_root layout
    # so validators using Path(__file__).parent^5 resolve correctly.
    workspace_root = os.environ.get("PIPELINE_WORKSPACE_ROOT", "/app")

    # 1. Load registry
    registry, fingerprint = load_registry(registry_uri)
    current_assets = collect_current_assets(registry)
    log.info("registry_loaded", asset_count=len(current_assets), fingerprint=fingerprint[:16])

    # 2. Build chunker registry
    chunker_registry = _build_chunker_registry()
    chunker_paths = set(chunker_registry.keys())

    # 3. Insert build_manifests staging row (skip in dry-run to avoid DB write)
    if not dry_run:
        _insert_manifest_row(build_id, triggered_by, fingerprint, pipeline_image_uri)

    # 4. Fetch assets to workspace (mirrors repo layout; validators resolve correctly)
    workspace, sha256_map = fetch_all_assets(sources_bucket, current_assets, chunker_paths, workspace_root)
    log.info("assets_fetched", count=len(sha256_map), workspace=workspace)

    # Track which layer subdirs were downloaded so we can clean them post-build
    downloaded_subdirs = {Path(p).parts[0] for p in sha256_map}

    all_chunks: list[Any] = []
    try:
        # 5. Chunk each fetched asset
        for asset_path, (doc_type, chunker_fn) in chunker_registry.items():
            local_file = Path(workspace) / asset_path
            if not local_file.exists():
                log.warning("asset_not_fetched", path=asset_path)
                continue
            log.info("chunking", asset=asset_path, doc_type=doc_type)
            try:
                chunks = chunker_fn(workspace)
            except Exception as exc:
                log.error("chunker_failed", asset=asset_path, error=str(exc))
                raise RuntimeError(f"Chunker failed for {asset_path}: {exc}") from exc
            log.info("chunks_produced", asset=asset_path, count=len(chunks))
            all_chunks.extend(chunks)

        # domain_report: self-scanning multi-file chunker (not gated by a single source path)
        try:
            from rag.chunkers.domain_report import chunk_domain_reports
            dr_chunks = chunk_domain_reports(workspace)
            log.info("chunks_produced", asset="domain_reports/*", doc_type="domain_report", count=len(dr_chunks))
            all_chunks.extend(dr_chunks)
        except Exception as exc:
            log.error("chunker_failed", asset="domain_report", error=str(exc))
            raise RuntimeError(f"Chunker failed for domain_report: {exc}") from exc

        # remedial_codex: multi-file chunker (PART1 + PART2 — Wave 5 M2-D234-BUNDLE)
        try:
            from rag.chunkers.remedial_chunker import chunk_remedial_codex
            rem_chunks = chunk_remedial_codex(workspace)
            log.info("chunks_produced", asset="04_REMEDIAL_CODEX/*", doc_type="l4_remedial", count=len(rem_chunks))
            all_chunks.extend(rem_chunks)
        except Exception as exc:
            log.error("chunker_failed", asset="remedial_codex", error=str(exc))
            raise RuntimeError(f"Chunker failed for remedial_codex: {exc}") from exc

        log.info("total_chunks", count=len(all_chunks))

        if dry_run:
            log.info("dry_run_complete", chunk_count=len(all_chunks))
            return {
                "build_id": build_id,
                "dry_run": True,
                "chunk_count": len(all_chunks),
                "duration_s": round(time.perf_counter() - t0, 2),
            }

        # 6. Embed all chunks
        _init_vertexai()
        embeddings = _embed_chunks(all_chunks)
        log.info("embeddings_complete", count=len(embeddings))

        # 7. Write to staging
        writer = RAGChunksWriter()
        write_result = writer.write_chunks(all_chunks, embeddings, build_id)
        log.info("staging_written", chunk_count=write_result.chunk_count, embedding_count=write_result.embedding_count)

        # 8. Validate staging
        validation = writer.validate_staging(build_id)
        if not validation.valid:
            raise RuntimeError(f"Staging validation failed: {validation.issues}")
        log.info("staging_validated", chunk_count=validation.chunk_count, embedding_count=validation.embedding_count)

        # 8b. L1 structured writers (additive — 14C)
        _run_l1_writers(build_id, skip_swap, log)

        # 8c. L2.5 structured writers (additive — 14D)
        _run_l25_writers(workspace, build_id, skip_swap, log)

        # 9. Emit manifest JSON to GCS
        manifest_uri = write_manifest(
            artifacts_bucket=artifacts_bucket,
            build_id=build_id,
            triggered_by=triggered_by,
            registry_fingerprint=fingerprint,
            pipeline_image_uri=pipeline_image_uri,
            chunk_count=validation.chunk_count,
            embedding_count=validation.embedding_count,
            status="staging" if skip_swap else "promoted",
            asset_sha256_map=sha256_map,
        )

        if skip_swap:
            _update_manifest_row(build_id, validation.chunk_count, validation.embedding_count, "staging", manifest_uri)
            log.info("build_complete_skip_swap", build_id=build_id, manifest_uri=manifest_uri)
        else:
            # 10. Swap staging → live
            swap_result = writer.swap_to_live(build_id)
            if not swap_result.success:
                raise RuntimeError(f"Swap failed: {swap_result.message}")
            _update_manifest_row(build_id, validation.chunk_count, validation.embedding_count, "live", manifest_uri)
            log.info("build_complete_live", build_id=build_id, promoted=swap_result.promoted_chunk_count, manifest_uri=manifest_uri)

        duration = round(time.perf_counter() - t0, 2)
        return {
            "build_id": build_id,
            "dry_run": False,
            "skip_swap": skip_swap,
            "chunk_count": validation.chunk_count,
            "embedding_count": validation.embedding_count,
            "manifest_uri": manifest_uri,
            "duration_s": duration,
        }

    finally:
        # Clean up only the downloaded source subdirs (not the code under platform/)
        for subdir in downloaded_subdirs:
            target = Path(workspace) / subdir
            if target.exists() and not str(target).startswith(str(Path(workspace) / "platform")):
                shutil.rmtree(target, ignore_errors=True)
                log.info("cleaned_subdir", path=str(target))


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="MARSYS-JIS build pipeline orchestrator")
    parser.add_argument(
        "--registry-uri",
        default="gs://madhav-marsys-sources/00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json",
        help="GCS URI of VALIDATED_ASSET_REGISTRY JSON",
    )
    parser.add_argument(
        "--build-id",
        default=None,
        help="Build ID (auto-generated if omitted)",
    )
    parser.add_argument(
        "--triggered-by",
        default="manual:unknown",
        help="Who triggered this build (e.g. manual:email, scheduler, github-push)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate + chunk but skip write to staging and skip swap",
    )
    parser.add_argument(
        "--skip-swap",
        action="store_true",
        help="Write to staging but do not promote to live",
    )
    args = parser.parse_args()

    build_id = args.build_id or f"build-{uuid.uuid4()}"
    sources_bucket = os.environ.get("GCS_SOURCES_BUCKET", "madhav-marsys-sources")
    artifacts_bucket = os.environ.get("GCS_ARTIFACTS_BUCKET", "madhav-marsys-build-artifacts")
    pipeline_image_uri = os.environ.get(
        "PIPELINE_IMAGE_URI",
        "asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:unknown",
    )

    result = run_build(
        registry_uri=args.registry_uri,
        build_id=build_id,
        triggered_by=args.triggered_by,
        dry_run=args.dry_run,
        skip_swap=args.skip_swap,
        sources_bucket=sources_bucket,
        artifacts_bucket=artifacts_bucket,
        pipeline_image_uri=pipeline_image_uri,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

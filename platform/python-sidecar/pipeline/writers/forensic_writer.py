"""
forensic_writer.py — A2 FORENSIC.md render writer.

Instantiates ForensicRenderer, registers all 13 section renderers in
FORENSIC v8.0 section order, renders the full markdown, lints it, and
upserts one row to chart_documents per (chart_id, ayanamsha_id, build_id).

conn=None → dry-run: renders the document but skips the DB write;
returns rows_written=1 so callers can count without a live DB.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID    = "A2_forensic_render"
ASSET_LABEL = "FORENSIC.md Render"

_DOCUMENT_TYPE = "forensic_render"

# ---------------------------------------------------------------------------
# Section registry — 13 renderers in FORENSIC v8.0 §1–§27 order
# ---------------------------------------------------------------------------

_SECTION_REGISTRY: list[tuple[str, str, str]] = [
    # (section_title, renderer_module, renderer_function)
    ("§ Identity & Planetary Positions",
     "pipeline.render.planets_renderer",    "render_planets_section"),
    ("§ Houses & Arudha Padas",
     "pipeline.render.houses_renderer",     "render_houses_section"),
    ("§ Upagrahas & Saturn-Derived Points",
     "pipeline.render.upagrahas_renderer",  "render_upagrahas_section"),
    ("§ Tajik Sahams & Esoteric Bindus",
     "pipeline.render.sahams_renderer",     "render_sahams_section"),
    ("§ Chara Karakas & Special Lagnas",
     "pipeline.render.karakas_renderer",    "render_karakas_section"),
    ("§ Yogas & Doshas Register",
     "pipeline.render.yogas_renderer",      "render_yogas_section"),
    ("§ Birth-Day Panchanga",
     "pipeline.render.panchanga_renderer",  "render_panchanga_section"),
    ("§ Aspect Matrices",
     "pipeline.render.aspects_renderer",    "render_aspects_section"),
    ("§ Strengths (Ashtakavarga · Shadbala · Bhava Bala)",
     "pipeline.render.strengths_renderer",  "render_strengths_section"),
    ("§ Vimsopaka & Avasthas",
     "pipeline.render.vimsopaka_renderer",  "render_vimsopaka_section"),
    ("§ Divisional Charts (Vargas)",
     "pipeline.render.vargas_renderer",     "render_vargas_section"),
    ("§ Dasha Systems",
     "pipeline.render.dashas_renderer",     "render_dashas_section"),
    ("§ Supplementary Data",
     "pipeline.render.supplementary_renderer", "render_supplementary_section"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_fn(module_path: str, fn_name: str):
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, fn_name)


def _build_renderer():
    """Instantiate ForensicRenderer with all 13 sections registered."""
    from pipeline.render.base_renderer import ForensicRenderer
    renderer = ForensicRenderer()
    for title, mod_path, fn_name in _SECTION_REGISTRY:
        fn = _import_fn(mod_path, fn_name)
        renderer.register_section(title, fn)
    return renderer


def _upsert_chart_document(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    content_md: str,
    content_json: dict,
) -> None:
    """
    Upsert one row into chart_documents.

    UNIQUE constraint: (chart_id, ayanamsha_id, document_type, build_id).
    On conflict: update content_md, content_json, byte_size, is_embedded.
    Idempotency guard: check chart_documents (the write target) per brief.
    """
    byte_size = len(content_md.encode("utf-8"))
    content_json_str = json.dumps(content_json, ensure_ascii=False)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chart_documents
              (chart_id, ayanamsha_id, document_type, build_id,
               content_md, content_json, byte_size, chunk_count, is_embedded)
            VALUES (%s, %s, %s, %s,
                    %s, %s::jsonb, %s, NULL, FALSE)
            ON CONFLICT (chart_id, ayanamsha_id, document_type, build_id)
            DO UPDATE SET
              content_md   = EXCLUDED.content_md,
              content_json = EXCLUDED.content_json,
              byte_size    = EXCLUDED.byte_size,
              is_embedded  = FALSE
            """,
            (
                chart_id, ayanamsha_id, _DOCUMENT_TYPE, build_id,
                content_md, content_json_str, byte_size,
            ),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Public writer function
# ---------------------------------------------------------------------------

def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Render and persist A2 FORENSIC.md for one (chart_id, ayanamsha_id).

    Steps:
      1. Adapt chart_output to renderer input shape.
      2. Build ForensicRenderer with 13 registered sections.
      3. Render → lint → assert no NarrationViolation.
      4. Upsert one row to chart_documents (or skip if conn is None → dry run).

    Returns:
      1 — one document written (or would have been written in dry-run).
    """
    from pipeline.render._chart_output_adapter import to_render_input
    from pipeline.render.base_renderer import NarrationViolation

    logger.info(
        "%s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )

    # 1. Adapt shape
    render_input = to_render_input(chart_output)

    # 2. Build renderer
    renderer = _build_renderer()

    # 3. Render (ForensicRenderer calls lint_narration per section and raises
    #    NarrationViolation if any forbidden verb is found)
    md = renderer.render(
        render_input,
        chart_id=chart_id,
        ayanamsha_id=ayanamsha_id,
        engine_version="pyjhora/1.0.0",
        build_id=build_id,
    )

    if not md:
        raise RuntimeError(
            f"ForensicRenderer returned empty markdown for {chart_id}/{ayanamsha_id}"
        )

    # Build structured content_json: section titles → first 500 chars of content
    content_json: dict = {
        "sections": [title for title, _, _ in _SECTION_REGISTRY],
        "byte_size": len(md.encode("utf-8")),
    }

    logger.info(
        "%s: rendered %d bytes for chart=%s ayanamsha=%s",
        ASSET_LABEL, len(md.encode("utf-8")), chart_id, ayanamsha_id,
    )

    # 4. Persist (dry-run if conn is None)
    if conn is not None:
        _upsert_chart_document(
            conn, chart_id, ayanamsha_id, build_id, md, content_json,
        )
        logger.info(
            "%s: upserted chart_documents row for chart=%s ayanamsha=%s build=%s",
            ASSET_LABEL, chart_id, ayanamsha_id, build_id,
        )
    else:
        logger.info(
            "%s: dry-run (conn=None) — %d bytes not persisted",
            ASSET_LABEL, len(md.encode("utf-8")),
        )

    return 1

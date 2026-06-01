"""
chunkers.l1_fact — Doc-type 4: L1 Fact Group chunker.
Phase B.2. Per M2A_EXEC_PLAN_v1_0.md §PLAN B.2 Task 2.1 + chunker_spec_v1_0.md §1 Doc-Type 4.
Spec ref: chunker_spec_v1_0.md §1 Doc-Type 4.
Boundary: ^## (H2) or ^### (H3). H4+ included in parent H3. Max tokens: 1000.
P1 enforcement: STOP if any L1 chunk fails P1 (genuine data quality issue).
"""
from __future__ import annotations

import os
import logging
import re
import sys
from pathlib import Path
from typing import Any

from rag.chunkers import count_tokens, truncate_to_tokens, write_chunks_to_db
from rag.models import Chunk
from rag.validators import p1_layer_separation as p1

logger = logging.getLogger(__name__)

MAX_TOKENS = 1000
MIN_BODY_TOKENS = 12  # skip near-empty intro stubs.
                     # VARGA-ETL-FULL-S1-CPA D11: lowered 20 → 12 to ensure tiny
                     # divisional sections like §3.1 D2 Hora (only 2 table rows,
                     # ~30–50 tokens including header) always produce a chunk.
SOURCE_FILE = "01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md"
SOURCE_VERSION = "8.0"
LAYER = "L1"

_SECTION_ID_RE = re.compile(r"§(\d+(?:\.\d+)*)")
# VARGA-ETL-FULL-S1-CPA D10 — varga + layer_aspect metadata for §3.x / §5.x / §6.x chunks.
# Used by vector_search's varga + section_id_prefix filters (D5).
_VARGA_RE = re.compile(r"\b(D\d+)\b")
_SECTION_3_RE = re.compile(r"^§3\.\d+")
_SECTION_3_15_RE = re.compile(r"^§3\.15\b")
_SECTION_5_RE = re.compile(r"^§5(\.|$)")
_SECTION_6_RE = re.compile(r"^§6(\.|$)")
# Two pre-processing patterns for P1 validation of L1 chunks:
# 1. Strip HTML comments — FORENSIC uses <!-- ... --> for LLM navigation notes, not facts.
#    Navigation words like "shows" in comments trigger false-positive P1 rejects.
# 2. Strip markdown table rows (lines starting with |) — FORENSIC table cells carry
#    categorical data labels (e.g., Vimsopaka band = "Strong", "Weak") not interpretive
#    prose. Strength-category words in table cells are factual, not astrological interpretation.
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_TABLE_ROW_RE = re.compile(r"^\|.*\|.*$", re.MULTILINE)
_PROVENANCE_RE = re.compile(
    r"\b(swiss_ephemeris|jagannatha_hora|manual_derivation|external_astrologer)\b",
    re.IGNORECASE,
)
_EXT_COMP_RE = re.compile(r"\[EXTERNAL_COMPUTATION_REQUIRED\]")

# Matches H2 (## ) and H3 (### ) — H4+ (####) are sub-headings included in parent chunk
_H2_RE = re.compile(r"^## (.+)$")
_H3_RE = re.compile(r"^### (.+)$")
_H4_RE = re.compile(r"^#### ")


def _extract_section_id(heading: str) -> str:
    m = _SECTION_ID_RE.search(heading)
    return f"§{m.group(1)}" if m else ""


def _extract_title(heading: str) -> str:
    """Strip leading §N — prefix to get the human-readable title."""
    title = re.sub(r"^§[\d.]+\s*[—–-]?\s*", "", heading).strip()
    return title if title else heading.strip()


def _augment_layer_metadata(meta: dict[str, Any], section_id: str, section_title: str) -> None:
    """VARGA-ETL-FULL-S1-CPA D10 — attach varga + layer_aspect to §3.x / §5.x / §6.x chunks.

    For §3.15 specifically the varga code is "CSI" (cross-divisional dignity ledger);
    for any other §3.x section the varga is parsed from the heading (e.g. "§3.5 D9 — Navamsha"
    → varga="D9"). §5.x → layer_aspect="dasha"; §6.x → layer_aspect="strength".
    Mutates meta in place. No-op for sections that don't match.
    """
    if _SECTION_3_15_RE.match(section_id or ""):
        meta["varga"] = "CSI"
        meta["layer_aspect"] = "divisional_transition"
        return
    if _SECTION_3_RE.match(section_id or ""):
        meta["layer_aspect"] = "divisional"
        m = _VARGA_RE.search(section_title or "")
        if m:
            meta["varga"] = m.group(1)
        return
    if _SECTION_5_RE.match(section_id or ""):
        meta["layer_aspect"] = "dasha"
        return
    if _SECTION_6_RE.match(section_id or ""):
        meta["layer_aspect"] = "strength"
        return


def _extract_provenance(content: str) -> str:
    """Return first matching provenance source tag, or UNKNOWN."""
    m = _PROVENANCE_RE.search(content)
    return m.group(1).lower() if m else "UNKNOWN"


def _parse_sections(text: str) -> list[tuple[int, str, str, str]]:
    """
    Walk lines and produce (level, heading_text, section_id, accumulated_body) tuples
    for each H2 or H3 node.  H4+ lines are absorbed into the open H3 (or H2) node.

    Returns list of (level, heading, section_id, body) — level 2 or 3.
    """
    nodes: list[tuple[int, str, str, list[str]]] = []
    current_level = 0
    current_heading = ""
    current_id = ""
    current_body: list[str] = []

    def flush():
        if current_heading or current_body:
            nodes.append((current_level, current_heading, current_id, current_body[:]))

    for line in text.split("\n"):
        m2 = _H2_RE.match(line)
        m3 = _H3_RE.match(line)
        if m2:
            flush()
            current_level = 2
            current_heading = m2.group(1).strip()
            current_id = _extract_section_id(current_heading)
            current_body = [line]
        elif m3:
            flush()
            current_level = 3
            current_heading = m3.group(1).strip()
            current_id = _extract_section_id(current_heading)
            current_body = [line]
        else:
            # H4+ and content lines go into the current open node
            if current_level > 0:
                current_body.append(line)
            # else: pre-document preamble — skip

    flush()

    return [(lvl, hdg, sid, "\n".join(body)) for lvl, hdg, sid, body in nodes]


def _split_at_h4(content: str, heading: str, section_id: str, provenance: str) -> list[Chunk]:
    """
    If an H3 chunk exceeds MAX_TOKENS, attempt H4-level split.
    Returns list of sub-chunks.
    """
    # Identify H4 boundaries
    parts: list[tuple[str, list[str]]] = []
    current_sub = ""
    current_lines: list[str] = []

    for line in content.split("\n"):
        if _H4_RE.match(line):
            if current_lines:
                parts.append((current_sub, current_lines[:]))
            current_sub = line[5:].strip()  # strip "#### "
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        parts.append((current_sub, current_lines))

    if len(parts) <= 1:
        # No H4 sub-headings found — hard truncate
        truncated_content, was_truncated = truncate_to_tokens(content, MAX_TOKENS)
        token_count = count_tokens(truncated_content)
        ext_comp = bool(_EXT_COMP_RE.search(truncated_content))
        title = _extract_title(heading)
        meta: dict[str, Any] = {
            "section_id": section_id,
            "section_title": title,
            "data_provenance": provenance,
        }
        _augment_layer_metadata(meta, section_id, title)
        if was_truncated:
            meta["truncation_note"] = f"Hard truncated at {MAX_TOKENS} tokens"
        if ext_comp:
            meta["external_computation_pending"] = True
        return [Chunk(
            chunk_id="",
            doc_type="l1_fact",
            layer=LAYER,
            source_file=SOURCE_FILE,
            source_version=SOURCE_VERSION,
            content=truncated_content,
            token_count=token_count,
            is_stale=False,
            citation_valid=True,
            external_computation_pending=ext_comp,
            metadata=meta,
        )]

    chunks: list[Chunk] = []
    for idx, (sub_heading, sub_lines) in enumerate(parts):
        sub_content = "\n".join(sub_lines)
        token_count = count_tokens(sub_content)
        was_truncated = False
        if token_count > MAX_TOKENS:
            sub_content, was_truncated = truncate_to_tokens(sub_content, MAX_TOKENS)
            token_count = count_tokens(sub_content)
        ext_comp = bool(_EXT_COMP_RE.search(sub_content))
        sub_prov = _extract_provenance(sub_content) if _PROVENANCE_RE.search(sub_content) else provenance
        title = _extract_title(heading)
        meta: dict[str, Any] = {
            "section_id": section_id,
            "section_title": title,
            "sub_heading": sub_heading,
            "sub_chunk_index": idx,
            "data_provenance": sub_prov,
        }
        _augment_layer_metadata(meta, section_id, title)
        if was_truncated:
            meta["truncation_note"] = f"Hard truncated at {MAX_TOKENS} tokens"
        if ext_comp:
            meta["external_computation_pending"] = True
        chunks.append(Chunk(
            chunk_id="",
            doc_type="l1_fact",
            layer=LAYER,
            source_file=SOURCE_FILE,
            source_version=SOURCE_VERSION,
            content=sub_content,
            token_count=token_count,
            is_stale=False,
            citation_valid=True,
            external_computation_pending=ext_comp,
            metadata=meta,
        ))
    return chunks


def chunk_l1_facts(repo_root: str) -> list[Chunk]:
    """
    Parse FORENSIC_ASTROLOGICAL_DATA_v8_0.md and produce one Chunk per H2/H3 section.
    H4+ lines are absorbed into their parent H3 chunk.
    P1 enforcement: STOP (RuntimeError) if any L1 chunk fails P1 — genuine data quality issue.
    Stop condition: STOP if P1 fires on any chunk.
    """
    forensic_path = Path(repo_root) / SOURCE_FILE
    if not forensic_path.exists():
        raise FileNotFoundError(f"FORENSIC_v8_0.md not found at {forensic_path}")

    text = forensic_path.read_text(encoding="utf-8")
    sections = _parse_sections(text)

    chunks: list[Chunk] = []
    p1_stop_section: str | None = None

    for level, heading, section_id, body in sections:
        if count_tokens(body) < MIN_BODY_TOKENS:
            logger.debug("l1_fact: skipping short section '%s' (%d tokens)", heading, count_tokens(body))
            continue

        token_count = count_tokens(body)
        provenance = _extract_provenance(body)
        ext_comp = bool(_EXT_COMP_RE.search(body))

        if token_count <= MAX_TOKENS:
            title = _extract_title(heading)
            meta: dict[str, Any] = {
                "section_id": section_id,
                "section_title": title,
                "data_provenance": provenance,
            }
            _augment_layer_metadata(meta, section_id, title)
            if ext_comp:
                meta["external_computation_pending"] = True
            chunk = Chunk(
                chunk_id="",
                doc_type="l1_fact",
                layer=LAYER,
                source_file=SOURCE_FILE,
                source_version=SOURCE_VERSION,
                content=body,
                token_count=token_count,
                is_stale=False,
                citation_valid=True,
                external_computation_pending=ext_comp,
                metadata=meta,
            )
            # Strip HTML comments and table rows before P1 validation
            p1_content = _TABLE_ROW_RE.sub("", _HTML_COMMENT_RE.sub("", body))
            chunk_dict = {"layer": LAYER, "doc_type": "l1_fact", "content": p1_content, "metadata": meta}
            p1_res = p1.validate(chunk_dict)
            if not p1_res["valid"]:
                logger.error(
                    "P1 VIOLATION on L1 chunk '%s' (section_id=%s): %s",
                    heading, section_id, p1_res["reason"],
                )
                p1_stop_section = f"{section_id} — {heading}: {p1_res['reason']}"
                break
            chunks.append(chunk)
        else:
            # Split at H4 boundaries
            sub_chunks = _split_at_h4(body, heading, section_id, provenance)
            for c in sub_chunks:
                p1_content = _TABLE_ROW_RE.sub("", _HTML_COMMENT_RE.sub("", c.content))
                chunk_dict = {"layer": LAYER, "doc_type": "l1_fact", "content": p1_content, "metadata": c.metadata}
                p1_res = p1.validate(chunk_dict)
                if not p1_res["valid"]:
                    logger.error(
                        "P1 VIOLATION on L1 sub-chunk '%s' (section_id=%s): %s",
                        heading, section_id, p1_res["reason"],
                    )
                    p1_stop_section = f"{section_id} — {heading}: {p1_res['reason']}"
                    break
                chunks.append(c)
            if p1_stop_section:
                break

    if p1_stop_section:
        raise RuntimeError(
            f"STOP: P1 validator fired on L1 chunk — genuine data quality issue.\n"
            f"Section: {p1_stop_section}\n"
            "Halt and report to native. Do not proceed with B.2."
        )

    logger.info("l1_fact: %d chunks produced from FORENSIC_v8_0", len(chunks))
    return chunks


def run(repo_root: str) -> int:
    """Parse FORENSIC L1 sections, write to rag_chunks via Cloud SQL (psycopg), return written count."""
    chunks = chunk_l1_facts(repo_root)
    chart_id = os.environ.get("NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0")
    written = write_chunks_to_db(chunks, chart_id)
    logger.info("l1_fact: wrote %d / %d chunks to rag_chunks", written, len(chunks))
    return written


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parents[5])
    count = run(root)
    print(f"l1_fact: {count} chunks written")

"""
chunkers.domain_report — Doc-type 5: Domain Report Part chunker.
Phase B.2. Per M2A_EXEC_PLAN_v1_0.md §PLAN B.2 Task 2.2 + chunker_spec_v1_0.md §1 Doc-Type 5.
Spec ref: chunker_spec_v1_0.md §1 Doc-Type 5.
Boundary: ^## (any H2 heading) — domain reports use mixed heading patterns
(some use '## PART I', others '## §N.', '## PART 0 — CORRECTION NOTICE' etc).
General H2 boundary ensures non-zero chunks for all 9 reports.
Max tokens: 1500; split at H3 if exceeded.
Stale propagation: read from STALENESS_REGISTER.md.
Stop condition: STOP if any report produces 0 chunks.
"""
from __future__ import annotations

import os
import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from rag.chunkers import (
    count_tokens,
    load_staleness_register,
    normalize_msr_refs,
    truncate_to_tokens,
    write_chunks_to_db,
)
from rag.models import Chunk
from rag.validators import p1_layer_separation as p1

logger = logging.getLogger(__name__)

MAX_TOKENS = 1500
MIN_BODY_TOKENS = 30
LAYER = "L3"

_H2_RE = re.compile(r"^## (.+)$")
_H3_RE = re.compile(r"^### (.+)$")
_PART_NUM_RE = re.compile(r"(?:PART|Part)\s+([IVX\d]+)|(?:§)\s*(\d+(?:\.\d+)*)", re.IGNORECASE)

# Map from filename keyword to domain label
_DOMAIN_MAP = {
    "CAREER": "career",
    "FINANCIAL": "financial",
    "HEALTH": "health",
    "PSYCHOLOGY": "mind",
    "TRAVEL": "travel",
    "CHILDREN": "children",
    "PARENTS": "parents",
    "RELATIONSHIPS": "relationships",
    "SPIRITUAL": "spiritual",
}


def _infer_domain(filename: str) -> str:
    upper = filename.upper()
    for key, domain in _DOMAIN_MAP.items():
        if key in upper:
            return domain
    return "unknown"


def _extract_part_number(heading: str) -> str:
    m = _PART_NUM_RE.search(heading)
    if not m:
        return ""
    return m.group(1) or m.group(2) or ""


def _read_frontmatter(text: str) -> dict[str, Any]:
    """Parse YAML frontmatter from markdown file. Returns {} if absent."""
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    try:
        fm = yaml.safe_load(text[3:end]) or {}
        return fm if isinstance(fm, dict) else {}
    except yaml.YAMLError:
        return {}


def _split_at_h2(text: str) -> list[tuple[str, str]]:
    """Split text at H2 boundaries. Returns [(heading, body)] pairs."""
    parts: list[tuple[str, str]] = []
    current_heading = ""
    current_body: list[str] = []

    for line in text.split("\n"):
        m = _H2_RE.match(line)
        if m:
            if current_heading or current_body:
                parts.append((current_heading, "\n".join(current_body)))
            current_heading = m.group(1).strip()
            current_body = [line]
        else:
            current_body.append(line)

    if current_heading or current_body:
        parts.append((current_heading, "\n".join(current_body)))
    return parts


def _split_at_h3(body: str) -> list[tuple[str, str]]:
    """Split section body at H3 boundaries. Returns [(sub_heading, sub_body)]."""
    parts: list[tuple[str, str]] = []
    current_heading = ""
    current_body: list[str] = []

    for line in body.split("\n"):
        m = _H3_RE.match(line)
        if m:
            if current_body or current_heading:
                parts.append((current_heading, "\n".join(current_body)))
            current_heading = m.group(1).strip()
            current_body = [line]
        else:
            current_body.append(line)

    if current_body or current_heading:
        parts.append((current_heading, "\n".join(current_body)))
    return parts


def _build_chunk(
    content: str,
    part_title: str,
    part_number: str,
    domain: str,
    report_name: str,
    source_file: str,
    report_version: str,
    is_stale: bool,
    stale_reason: str,
    stale_since: str,
    parent_part: str = "",
    sub_chunk_index: int | None = None,
) -> Chunk:
    content = normalize_msr_refs(content)
    token_count = count_tokens(content)
    was_truncated = False
    if token_count > MAX_TOKENS:
        content, was_truncated = truncate_to_tokens(content, MAX_TOKENS)
        token_count = count_tokens(content)

    meta: dict[str, Any] = {
        "report_name": report_name,
        "part_title": part_title,
        "part_number": part_number,
        "domain": domain,
        "report_version": report_version,
    }
    if parent_part:
        meta["parent_part"] = parent_part
    if sub_chunk_index is not None:
        meta["sub_chunk_index"] = sub_chunk_index
    if was_truncated:
        meta["truncation_note"] = f"Hard truncated at {MAX_TOKENS} tokens"

    return Chunk(
        chunk_id="",
        doc_type="domain_report",
        layer=LAYER,
        source_file=source_file,
        source_version=report_version,
        content=content,
        token_count=token_count,
        is_stale=is_stale,
        stale_reason=stale_reason if stale_reason else None,
        stale_since=stale_since if stale_since else None,
        citation_valid=True,
        metadata=meta,
    )


def chunk_domain_report(
    file_path: Path,
    repo_root: str,
    staleness_register: dict[str, tuple[bool, str, str]],
) -> list[Chunk]:
    """
    Chunk a single domain report file.
    Returns list of Chunks (one per H2 section, with H3-split for oversized sections).
    Stop condition: raises RuntimeError if zero chunks produced.
    """
    rel_path = str(file_path.relative_to(repo_root))
    report_name = file_path.name
    domain = _infer_domain(report_name)

    # Stale lookup — try full rel_path and basename
    stale_entry = staleness_register.get(rel_path) or staleness_register.get(report_name)
    is_stale, stale_reason, stale_since = stale_entry if stale_entry else (False, "", "")

    text = file_path.read_text(encoding="utf-8")
    fm = _read_frontmatter(text)
    report_version = str(fm.get("version", fm.get("current_version", "UNKNOWN")))
    source_file = rel_path

    sections = _split_at_h2(text)
    chunks: list[Chunk] = []
    p1_violations = 0

    for heading, body in sections:
        if not heading:
            continue

        norm_body = normalize_msr_refs(body)
        if count_tokens(norm_body) < MIN_BODY_TOKENS:
            logger.debug("domain_report: skipping short section '%s' in %s", heading, report_name)
            continue

        part_number = _extract_part_number(heading)
        full_content = body

        if count_tokens(normalize_msr_refs(full_content)) <= MAX_TOKENS:
            chunk = _build_chunk(
                full_content, heading, part_number, domain, report_name,
                source_file, report_version, is_stale, stale_reason, stale_since,
            )
            chunk_dict = {"layer": LAYER, "doc_type": "domain_report", "content": chunk.content, "metadata": chunk.metadata}
            p1_res = p1.validate(chunk_dict)
            if not p1_res["valid"]:
                p1_violations += 1
                logger.warning("P1 violation domain_report '%s' section '%s': %s", report_name, heading, p1_res["reason"])
                continue
            chunks.append(chunk)
        else:
            # Split at H3
            h3_parts = _split_at_h3(body)
            if len(h3_parts) <= 1:
                chunk = _build_chunk(
                    full_content, heading, part_number, domain, report_name,
                    source_file, report_version, is_stale, stale_reason, stale_since,
                )
                chunk_dict = {"layer": LAYER, "doc_type": "domain_report", "content": chunk.content, "metadata": chunk.metadata}
                p1_res = p1.validate(chunk_dict)
                if not p1_res["valid"]:
                    p1_violations += 1
                    logger.warning("P1 violation domain_report '%s' section '%s' (truncated): %s", report_name, heading, p1_res["reason"])
                    continue
                chunks.append(chunk)
            else:
                for idx, (sub_heading, sub_body) in enumerate(h3_parts):
                    if not sub_body.strip():
                        continue
                    sub_content = (
                        f"## {heading} / ### {sub_heading}\n{sub_body}"
                        if sub_heading
                        else f"## {heading}\n{sub_body}"
                    )
                    chunk = _build_chunk(
                        sub_content, heading, part_number, domain, report_name,
                        source_file, report_version, is_stale, stale_reason, stale_since,
                        parent_part=heading, sub_chunk_index=idx,
                    )
                    chunk_dict = {"layer": LAYER, "doc_type": "domain_report", "content": chunk.content, "metadata": chunk.metadata}
                    p1_res = p1.validate(chunk_dict)
                    if not p1_res["valid"]:
                        p1_violations += 1
                        logger.warning(
                            "P1 violation domain_report '%s' sub-chunk '%s / %s': %s",
                            report_name, heading, sub_heading, p1_res["reason"],
                        )
                        continue
                    chunks.append(chunk)

    if p1_violations:
        logger.warning("domain_report %s: %d P1 violations (chunks blocked)", report_name, p1_violations)

    if not chunks:
        raise RuntimeError(
            f"STOP: Zero chunks produced for domain report '{report_name}'. "
            "Boundary detection failure — check H2 heading patterns."
        )

    logger.info("domain_report %s: %d chunks produced (is_stale=%s)", report_name, len(chunks), is_stale)
    return chunks


def chunk_domain_reports(repo_root: str) -> list[Chunk]:
    """
    Process all current domain report files listed in STALENESS_REGISTER.
    Returns combined list of all Chunks.
    """
    staleness_register = load_staleness_register(repo_root)
    if not staleness_register:
        logger.warning("STALENESS_REGISTER empty or missing — is_stale will default to False for all reports")

    # Derive target file list from STALENESS_REGISTER keys (full rel-paths ending in .md)
    target_files: list[Path] = []
    seen_names: set[str] = set()
    for key in staleness_register:
        if "/" in key and key.endswith(".md") and "DOMAIN_REPORTS" in key:
            p = Path(repo_root) / key
            if p.exists() and p.name not in seen_names:
                target_files.append(p)
                seen_names.add(p.name)

    if not target_files:
        # Fallback: glob current-version reports directly
        reports_dir = Path(repo_root) / "03_DOMAIN_REPORTS"
        # Pick latest version of each report (highest vN_M suffix)
        by_stem: dict[str, Path] = {}
        for fp in sorted(reports_dir.glob("REPORT_*_v*.md")):
            # stem e.g. REPORT_CAREER_DHARMA_v1_1
            base_key = re.sub(r"_v\d+_\d+$", "", fp.stem)
            if base_key not in by_stem or fp.name > by_stem[base_key].name:
                by_stem[base_key] = fp
        target_files = list(by_stem.values())
        logger.info("domain_report: STALENESS_REGISTER lookup empty; using glob fallback (%d files)", len(target_files))

    all_chunks: list[Chunk] = []
    for file_path in sorted(target_files):
        file_chunks = chunk_domain_report(file_path, repo_root, staleness_register)
        all_chunks.extend(file_chunks)

    logger.info("domain_report: total %d chunks from %d reports", len(all_chunks), len(target_files))
    return all_chunks


def run(repo_root: str) -> int:
    """Process all domain reports, write to rag_chunks via Cloud SQL (psycopg), return written count."""
    chunks = chunk_domain_reports(repo_root)
    chart_id = os.environ.get("NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0")
    written = write_chunks_to_db(chunks, chart_id)
    logger.info("domain_report: wrote %d / %d chunks to rag_chunks", written, len(chunks))
    return written


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parents[5])
    count = run(root)
    print(f"domain_report: {count} chunks written")

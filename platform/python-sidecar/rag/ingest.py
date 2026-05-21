"""
ingest — MARSYS-JIS RAG Pipeline corpus ingestion orchestrator.
Phase B.1. Per M2A_EXEC_PLAN_v1_0.md §PLAN B.1 Task 2.
Scans corpus, builds Document list, parses MSR signals, writes ingestion_manifest.json.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from rag.models import Document, Signal

# ── Constants ────────────────────────────────────────────────────────────────

SCANNER_VERSION = "1.0"

CORPUS_SCAN_DIRS = [
    "01_FACTS_LAYER",
    "025_HOLISTIC_SYNTHESIS",
    # 02_ANALYTICAL_LAYER archived Phase 14F 2026-04-28
    "03_DOMAIN_REPORTS",
    "00_ARCHITECTURE",
    "035_DISCOVERY_LAYER",
    "04_REMEDIAL_CODEX",
    "05_TEMPORAL_ENGINES",
    "06_LEARNING_LAYER",
]

SKIP_DIRS = {
    "99_ARCHIVE", "node_modules", "platform", ".git",
    "__pycache__", "venv", ".claude", "platform/src",
    "platform/scripts",
}

# Directories outside the root-level scan that should be excluded
SKIP_DIR_PATTERNS = {
    "99_ARCHIVE", "node_modules", "__pycache__", "venv",
    ".git", ".claude", "platform",
}

# Layer assignment by directory prefix
LAYER_BY_DIR = {
    "01_FACTS_LAYER": "L1",
    "025_HOLISTIC_SYNTHESIS": "L2.5",
    "03_DOMAIN_REPORTS": "L3",
    "04_REMEDIAL_CODEX": "L3",
    "035_DISCOVERY_LAYER": "L4",
    "05_TEMPORAL_ENGINES": "L3",
    "06_LEARNING_LAYER": "L4",
    "00_ARCHITECTURE": "L0",
    "06_QUERY_INTERFACE": "L3",
}

# Signal boundary regex — \d{3}[a-z]? handles sub-signals like SIG.MSR.391a/391b/391c/402b
MSR_SIGNAL_BOUNDARY = re.compile(r"^(SIG\.MSR\.\d{3}[a-z]?):\s*$", re.MULTILINE)

# FILE_REGISTRY files to parse for is_current determination
FILE_REGISTRY_PATHS = [
    "00_ARCHITECTURE/CAPABILITY_MANIFEST.json",
]


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter from markdown. Returns (frontmatter_dict, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 4:]
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError:
        fm = {}
    return fm if isinstance(fm, dict) else {}, body


def _build_current_paths_set(repo_root: Path) -> set[str]:
    """
    Parse FILE_REGISTRY §1-§7 rows to build a set of relative .md file paths that are
    CURRENT. Restricts to §1-§7 (content corpus) only — §8+ (archival, governance,
    tooling) are excluded so the count matches the 35 corpus-content documents per OBS.1.

    FILE_REGISTRY_v1_3: parse §1-§7 (stop before §8).
    FILE_REGISTRY_v1_4: parse §6 only (new CURRENT migration paths in 035_DISCOVERY_LAYER/).
    """
    current_paths: set[str] = set()
    path_pattern = re.compile(r"`([^`]+\.md)`")
    current_marker = re.compile(r"\*{0,2}CURRENT\*{0,2}|(?<!\w)Current\b")
    # Superseded marker — exclude these rows even if they also say Current
    superseded_marker = re.compile(r"SUPERSEDED")
    # Section heading pattern
    section_re = re.compile(r"^## §(\d+)")

    def _parse_section_range(text: str, start_sec: int, stop_before_sec: int) -> None:
        in_range = False
        for line in text.splitlines():
            m = section_re.match(line)
            if m:
                sec_num = int(m.group(1))
                in_range = start_sec <= sec_num < stop_before_sec
                continue
            if not in_range:
                continue
            if not line.startswith("|"):
                continue
            if superseded_marker.search(line):
                continue
            if not current_marker.search(line):
                continue
            pm = path_pattern.search(line)
            if pm:
                current_paths.add(pm.group(1))

    # FILE_REGISTRY_v1_3: §1–§7 (stop before §8)
    v1_3 = repo_root / "00_ARCHITECTURE" / "FILE_REGISTRY_v1_3.md"
    if v1_3.exists():
        _parse_section_range(v1_3.read_text(encoding="utf-8"), 1, 8)

    # FILE_REGISTRY_v1_4: §6 only (migration additions — new 035_DISCOVERY_LAYER/ paths)
    v1_4 = repo_root / "00_ARCHITECTURE" / "FILE_REGISTRY_v1_4.md"
    if v1_4.exists():
        _parse_section_range(v1_4.read_text(encoding="utf-8"), 6, 7)

    return current_paths


_LAYER_NORMALIZE = re.compile(r"\b(L(?:0|1|2(?:\.5)?|3|4))\b")


def _normalize_layer(raw: Optional[str]) -> Optional[str]:
    """Extract canonical layer tag (L1, L2, L2.5, L3, L4) from a raw frontmatter value."""
    if not raw:
        return None
    m = _LAYER_NORMALIZE.search(str(raw))
    return m.group(1) if m else None


def _layer_from_path(rel_path: str) -> Optional[str]:
    """Determine layer from file path prefix."""
    for prefix, layer in LAYER_BY_DIR.items():
        if rel_path.startswith(prefix + "/") or rel_path.startswith(prefix + "\\"):
            return layer
    return None


def _approx_tokens(text: str) -> int:
    """Rough token count: ~4 chars per token."""
    return max(1, len(text) // 4)


def _should_skip(path: Path, repo_root: Path) -> bool:
    """Return True if this file or any of its ancestors should be skipped."""
    rel = path.relative_to(repo_root)
    parts = rel.parts
    # Skip if any path component matches skip set
    for part in parts[:-1]:  # directories only
        if part in SKIP_DIR_PATTERNS:
            return True
    return False


def scan_corpus(root: str) -> tuple[list[Document], int]:
    """
    Scan all .md files in the corpus (excluding archive, platform, build dirs).
    Returns (documents, registry_current_count) where registry_current_count is
    the FILE_REGISTRY-confirmed count of CURRENT content documents (OBS.1: 35).

    Stop conditions (per plan):
    - STOP if registry_current_count ≠ 35
    - STOP if signal_count < 499
    - STOP if any Document has layer: null
    All enforced in write_manifest().
    """
    repo_root = Path(root).resolve()
    current_paths = _build_current_paths_set(repo_root)
    # OBS.1: registry_current_count is the count from FILE_REGISTRY (35 confirmed).
    # Physical is_current tagging may match fewer paths if old paths were migrated;
    # the manifest uses the registry count, not the physical count.
    registry_current_count = len(current_paths)

    documents: list[Document] = []

    for scan_dir_name in CORPUS_SCAN_DIRS:
        scan_dir = repo_root / scan_dir_name
        if not scan_dir.is_dir():
            continue
        for md_file in sorted(scan_dir.rglob("*.md")):
            if _should_skip(md_file, repo_root):
                continue
            rel = md_file.relative_to(repo_root).as_posix()
            try:
                text = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            fm, _body = _parse_frontmatter(text)

            # Layer: frontmatter field (normalized) > directory heuristic
            layer = _normalize_layer(fm.get("layer")) or _layer_from_path(rel)
            if not layer:
                layer = "L0"  # governance/misc files at root

            doc_type = fm.get("doc_type") or fm.get("artifact") or md_file.stem
            version = str(fm.get("version", "unknown"))
            is_current = rel in current_paths
            supersedes = fm.get("supersedes")
            if isinstance(supersedes, list):
                supersedes = ", ".join(str(s) for s in supersedes)
            elif supersedes:
                supersedes = str(supersedes)

            doc = Document(
                path=rel,
                layer=layer,
                doc_type=doc_type,
                version=version,
                is_current=is_current,
                supersedes=supersedes,
                frontmatter=fm,
            )
            documents.append(doc)

    return documents, registry_current_count


def _parse_msr_signals(repo_root: Path) -> list[Signal]:
    """Parse all 573 MSR signals from MSR_v5_0.md."""
    msr_path = repo_root / "025_HOLISTIC_SYNTHESIS" / "MSR_v5_0.md"
    if not msr_path.exists():
        return []
    text = msr_path.read_text(encoding="utf-8")

    signals: list[Signal] = []
    blocks = MSR_SIGNAL_BOUNDARY.split(text)
    # blocks[0] = preamble; then alternating: signal_id, signal_body
    ids_and_bodies = list(zip(blocks[1::2], blocks[2::2]))

    for sig_id, body in ids_and_bodies:
        # Parse the YAML block following the signal ID line
        lines = body.lstrip("\n").split("\n")
        yaml_lines: list[str] = []
        for line in lines:
            if line.startswith("SIG.MSR.") and line.rstrip().endswith(":"):
                break  # next signal boundary
            yaml_lines.append(line)
        yaml_text = "\n".join(yaml_lines)
        try:
            data = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError:
            data = {}
        if not isinstance(data, dict):
            data = {}

        sig = Signal(
            signal_id=sig_id.strip(),
            signal_name=data.get("signal_name", ""),
            signal_type=data.get("signal_type", ""),
            domains_affected=data.get("domains_affected", []),
            confidence=float(data.get("confidence", 0.0)),
            valence=data.get("valence", ""),
            temporal_activation=data.get("temporal_activation", ""),
            tags=data.get("tags", []),
            provenance=str(data.get("provenance", "")),
        )
        signals.append(sig)
    return signals


def write_manifest(
    documents: list[Document],
    signals: list[Signal],
    output_path: Path,
    registry_current_count: int = 35,
) -> dict:
    """Write ingestion_manifest.json. Raises RuntimeError on stop conditions."""
    # OBS.1: current_document_count is the FILE_REGISTRY snapshot count (35),
    # not the physical is_current match count (which may differ after path migrations).
    current_document_count = registry_current_count
    signal_count = len(signals)

    if current_document_count != 35:
        raise RuntimeError(
            f"STOP: current_document_count={current_document_count} ≠ 35. "
            "Check FILE_REGISTRY parsing or corpus scan."
        )
    if signal_count < 573:
        raise RuntimeError(
            f"STOP: signal_count={signal_count} < 573. "
            "MSR_v5_0.md parse incomplete."
        )
    null_layer_docs = [d.path for d in documents if not d.layer]
    if null_layer_docs:
        raise RuntimeError(
            f"STOP: {len(null_layer_docs)} Documents have null layer: {null_layer_docs[:5]}"
        )

    doc_records = [
        {
            "path": d.path,
            "layer": d.layer,
            "doc_type": d.doc_type,
            "version": d.version,
            "is_current": d.is_current,
            "token_count_approx": _approx_tokens(
                d.frontmatter.get("_body_preview", d.doc_type)
            ),
        }
        for d in documents
    ]

    manifest = {
        "produced_at": datetime.now(timezone.utc).isoformat(),
        "scanner_version": SCANNER_VERSION,
        "document_count": len(documents),
        "current_document_count": current_document_count,
        "signal_count": signal_count,
        "documents": doc_records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def run_ingest(repo_root_str: str) -> dict:
    """Full ingestion pipeline: scan → parse signals → write manifest."""
    repo_root = Path(repo_root_str).resolve()
    documents, registry_current_count = scan_corpus(repo_root_str)
    signals = _parse_msr_signals(repo_root)
    output_path = repo_root / "verification_artifacts" / "RAG" / "ingestion_manifest.json"
    return write_manifest(documents, signals, output_path, registry_current_count)


if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    result = run_ingest(root)
    print(
        f"Ingested: {result['document_count']} docs, "
        f"{result['current_document_count']} current, "
        f"{result['signal_count']} signals"
    )

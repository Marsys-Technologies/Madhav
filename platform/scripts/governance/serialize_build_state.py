#!/usr/bin/env python3
"""
serialize_build_state.py — MARSYS-JIS build-state serializer v0.2.0.

Reads canonical files and emits a build_state.json snapshot (v0.2.0 shape) plus
optional per-session and per-phase detail shards. Conforms to build_state.schema.json.
Intended to be invoked at session close so the portal at madhav.marsys.in/build can
fetch fresh state via GCS HTTPS.

# Implements: PORTAL_BUILD_TRACKER_PLAN_v0_1.md §3 (data layer) + §10.2.1.
# Session 1 deliverable: Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1 (2026-04-26).

Usage:
  # Default — write top-level JSON:
  python3 platform/scripts/governance/serialize_build_state.py \\
      --repo-root /Users/Dev/Vibe-Coding/Apps/Madhav \\
      --session-id Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1 \\
      --output build_state.json

  # With shards (per-session + per-phase detail files):
  python3 platform/scripts/governance/serialize_build_state.py \\
      --repo-root /Users/Dev/Vibe-Coding/Apps/Madhav \\
      --session-id Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1 \\
      --output build_state.json \\
      --emit-shards \\
      --shard-dir /tmp/marsys-shards

  # With GCS upload (uploads top-level + shards if --emit-shards):
  python3 platform/scripts/governance/serialize_build_state.py \\
      --repo-root /Users/Dev/Vibe-Coding/Apps/Madhav \\
      --session-id Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1 \\
      --output build_state.json \\
      --upload-to-gcs gs://marsys-jis-build-state/build-state.json \\
      --emit-shards

  # Validate-only (does not write):
  python3 platform/scripts/governance/serialize_build_state.py \\
      --repo-root /Users/Dev/Vibe-Coding/Apps/Madhav \\
      --session-id Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1 \\
      --validate-only

Exit codes:
  0  — snapshot serialized (and uploaded if requested) successfully
  1  — source file missing or unparseable
  2  — schema validation failed (only with --validate-against-schema)
  3  — GCS upload failed (snapshot still written locally)
  4  — script-internal error

This script is a SERIALIZER. It reads canonical files but never modifies them.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import pathlib
import re
import sys
import traceback
from typing import Any, Dict, List, Optional, Tuple

# Reuse the existing canonical-artifacts loader rather than re-parsing.
sys.path.insert(0, str(pathlib.Path(__file__).parent))
try:
    from _ca_loader import load_canonical_artifacts, compute_sha256  # type: ignore
except ImportError:
    import yaml  # noqa: F401 — required by fallback loader below
    load_canonical_artifacts = None  # type: ignore
    compute_sha256 = None  # type: ignore


GENERATOR_VERSION = "0.3.0"
SCHEMA_VERSION = "0.3.0"
RED_TEAM_THRESHOLD_DEFAULT = 3  # ONGOING_HYGIENE_POLICIES §G
TREND_WINDOW_DEFAULT = 30       # last N reports for health trend (plan §3.2.1)

# Module-level list accumulated during a single serializer run.
# Cleared at the start of assemble_build_state(); surfaced in the output JSON.
_SERIALIZER_WARNINGS: List[str] = []

# ----- Canonical source paths (relative to repo root) -----
P_CURRENT_STATE = "00_ARCHITECTURE/CURRENT_STATE_v1_0.md"
P_CANONICAL_ARTIFACTS = "00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md"
P_SESSION_LOG = "00_ARCHITECTURE/SESSION_LOG.md"
P_ONGOING_HYGIENE = "00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md"
P_NATIVE_DIRECTIVES = "00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md"
P_DISAGREEMENT_REGISTER = "00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md"
P_STALENESS_REGISTER = "00_ARCHITECTURE/STALENESS_REGISTER.md"
P_PHASE_B_PLAN = "00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md"
P_MACRO_PLAN = "00_ARCHITECTURE/MACRO_PLAN_v2_0.md"
P_COWORK_LEDGER = "00_ARCHITECTURE/COWORK_LEDGER.md"
P_CURRENT_BRIEF = "CLAUDECODE_BRIEF.md"
P_DRIFT_REPORTS_DIR = "00_ARCHITECTURE/drift_reports"
P_SCHEMA_REPORTS_DIR = "00_ARCHITECTURE/schema_reports"
P_RED_TEAM_DIR = "verification_artifacts/RAG"
P_DOMAIN_REPORTS_DIR = "03_DOMAIN_REPORTS"
P_INTERVENTION_BACKFILL = "00_ARCHITECTURE/INTERVENTION_BACKFILL_v1_0.md"
P_RAG_CHUNKING_REPORT = "verification_artifacts/RAG/chunking_report.json"
P_RAG_EDGE_COUNT = "verification_artifacts/RAG/b4_edge_count.json"
P_RAG_NODE_COUNT = "verification_artifacts/RAG/b4_node_count.json"
P_CGM = "025_HOLISTIC_SYNTHESIS/CGM_v9_0.md"
P_MSR = "025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"
P_LEL = "01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md"
P_PREDICTION_LEDGER = "06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl"

# IST is UTC+5:30 — used for "today" window in the cockpit's today_progress block.
IST_OFFSET = _dt.timedelta(hours=5, minutes=30)


# --------------------------------------------------------------------------------------
# Utility helpers
# --------------------------------------------------------------------------------------

def _today_ist_key() -> str:
    """Calendar day in IST (YYYY-MM-DD)."""
    return (_dt.datetime.now(_dt.timezone.utc) + IST_OFFSET).date().isoformat()


def _ist_date_key(iso: Optional[str]) -> Optional[str]:
    """Convert any ISO datetime/date string to its IST calendar date key."""
    if not iso:
        return None
    try:
        # Date-only strings are interpreted as midnight IST already.
        if len(iso) == 10:
            return iso
        d = _dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=_dt.timezone.utc)
        return (d.astimezone(_dt.timezone.utc) + IST_OFFSET).date().isoformat()
    except (ValueError, TypeError):
        return None


def _compute_today_progress(
    sessions_index: List[Dict[str, Any]],
    repo_root: pathlib.Path,
) -> Dict[str, Any]:
    """
    Aggregate what landed today (IST). For each matching session, attempt to
    open its parsed body for files_touched + deliverables; degrade gracefully
    when the body isn't parseable.
    """
    today = _today_ist_key()
    matched_ids: List[str] = []
    files_touched_count = 0
    deliverables: List[str] = []

    for s in sessions_index:
        if _ist_date_key(s.get("date")) != today:
            continue
        sid = s.get("session_id")
        if not sid:
            continue
        matched_ids.append(sid)
        body = _extract_session_body(repo_root, sid)
        if body:
            files_touched_count += len(body.get("files_touched") or [])
            for d in body.get("deliverables") or []:
                if d:
                    deliverables.append(str(d))
        elif s.get("deliverable_one_liner"):
            deliverables.append(s["deliverable_one_liner"])

    return {
        "date_key": today,
        "session_ids": matched_ids,
        "session_count": len(matched_ids),
        "files_touched_count": files_touched_count,
        "deliverables": deliverables,
    }

def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_iso(value: Any) -> Optional[str]:
    """YAML loaders return datetime objects for ISO-8601 strings; stringify."""
    if value is None:
        return None
    if isinstance(value, (_dt.datetime, _dt.date)):
        return value.isoformat()
    return str(value)


def _safe_read(path: pathlib.Path) -> Optional[str]:
    """Read a file, returning None if it does not exist."""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _load_yaml_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Parse the first YAML fence from text, returning None on failure."""
    import yaml
    m = re.search(r"^```yaml\s*\n(.*?)^```\s*$", text, re.MULTILINE | re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None


# --------------------------------------------------------------------------------------
# Source-file readers — v0.1.0 originals (unchanged)
# --------------------------------------------------------------------------------------

def _extract_yaml_block(text: str, start_marker: str = "current_state:") -> Dict[str, Any]:
    """Extract the canonical YAML block from CURRENT_STATE §2 (under fenced ```yaml)."""
    import yaml
    m = re.search(r"^```yaml\s*\n(.*?)^```\s*$", text, re.MULTILINE | re.DOTALL)
    if not m:
        raise ValueError("CURRENT_STATE §2 YAML fence not found")
    parsed = yaml.safe_load(m.group(1))
    if "current_state" not in parsed:
        raise ValueError("CURRENT_STATE YAML missing top-level 'current_state' key")
    return parsed["current_state"]


def _read_current_state(repo_root: pathlib.Path) -> Dict[str, Any]:
    p = repo_root / P_CURRENT_STATE
    if not p.exists():
        raise FileNotFoundError(p)
    return _extract_yaml_block(p.read_text(encoding="utf-8"))


def _read_canonical_artifacts(repo_root: pathlib.Path) -> Dict[str, Any]:
    """Parse CANONICAL_ARTIFACTS §1 + §2 via _ca_loader if available, else inline."""
    p = repo_root / P_CANONICAL_ARTIFACTS
    if not p.exists():
        raise FileNotFoundError(p)
    if load_canonical_artifacts is not None:
        ca = load_canonical_artifacts(repo_root)
        return {"artifacts": ca.artifacts, "mirror_pairs": ca.mirror_pairs}
    import yaml
    text = p.read_text(encoding="utf-8")
    blocks = re.findall(r"^```yaml\s*\n(.*?)^```\s*$", text, re.MULTILINE | re.DOTALL)
    artifacts: Dict[str, dict] = {}
    mirror_pairs: Dict[str, dict] = {}
    for b in blocks:
        try:
            d = yaml.safe_load(b)
        except yaml.YAMLError:
            continue
        if not isinstance(d, dict):
            continue
        if "canonical_id" in d:
            artifacts[d["canonical_id"]] = d
        elif "pair_id" in d:
            mirror_pairs[d["pair_id"]] = d
    return {"artifacts": artifacts, "mirror_pairs": mirror_pairs}


_SESSION_HEADER_RE = re.compile(
    r"^##\s+Session\s+([\w._-]+)\s+—\s+(.+?)\s*\(([\d-]+)(?:,\s*([^)]+))?\)",
    re.MULTILINE,
)
_SESSION_HEADER_RE_V2 = re.compile(
    r"^##\s+([A-Z][A-Za-z0-9_]+(?:_[A-Za-z0-9]+)*)\s+—\s+(.+?)$",
    re.MULTILINE,
)


def _read_recent_sessions(repo_root: pathlib.Path, n: int = 5) -> List[Dict[str, Any]]:
    """Extract the last n session headers from SESSION_LOG.md."""
    p = repo_root / P_SESSION_LOG
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8")
    sessions: List[Dict[str, Any]] = []
    for m in _SESSION_HEADER_RE.finditer(text):
        sessions.append({
            "id": m.group(1),
            "title": m.group(2).strip(),
            "closed_on": m.group(3),
            "summary": (m.group(4) or "").strip() or None,
        })
    for m in _SESSION_HEADER_RE_V2.finditer(text):
        sid = m.group(1)
        if any(s["id"] == sid for s in sessions):
            continue
        sessions.append({
            "id": sid,
            "title": m.group(2).strip(),
            "closed_on": None,
            "summary": None,
        })
    return sessions[-n:]


_QUARTERLY_PASS_RE = re.compile(
    r"First quarterly pass scheduled:\s*\*\*([\d-]+)\*\*", re.IGNORECASE,
)


def _read_next_quarterly_pass(repo_root: pathlib.Path) -> Optional[str]:
    p = repo_root / P_ONGOING_HYGIENE
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8")
    m = _QUARTERLY_PASS_RE.search(text)
    return m.group(1) if m else None


# --------------------------------------------------------------------------------------
# Source-file readers — v0.2.0 additions
# --------------------------------------------------------------------------------------

def _read_native_directives(repo_root: pathlib.Path) -> List[Dict[str, Any]]:
    """Parse ND.N entries from NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md.

    BF.6: requires a section anchor before parsing so greedy regex doesn't
    match ND.* mentions in preamble or TOC.
    """
    text = _safe_read(repo_root / P_NATIVE_DIRECTIVES)
    if not text:
        return []

    # Anchor: parse only after the first heading that contains an ND.N entry
    anchor = re.search(r"^###\s+ND\.\d+\s+[—-]", text, re.MULTILINE)
    if not anchor:
        _SERIALIZER_WARNINGS.append(
            "NATIVE_DIRECTIVES: no '### ND.N —' section found; returning empty entries."
        )
        return []

    search_text = text[anchor.start():]
    entries = []
    for m in re.finditer(
        r"^###\s+(ND\.\d+)\s+[—-]+\s+(.+?)$\n(.*?)(?=^###\s+ND\.|\Z)",
        search_text, re.MULTILINE | re.DOTALL
    ):
        nd_id = m.group(1)
        title = m.group(2).strip()
        body = m.group(3)
        status_m = re.search(r"\*\*Status[:\s]+([^*\n]+)\*\*", body, re.IGNORECASE)
        status = status_m.group(1).strip() if status_m else "unknown"
        issued_m = re.search(r"(?:issued|created)[_\s]+(?:on|at)[:\s]+([0-9]{4}-[0-9]{2}-[0-9]{2})",
                              body, re.IGNORECASE)
        issued_on = issued_m.group(1) if issued_m else None
        addr_m = re.search(r"addressed[_\s]+(?:on|at)[:\s]+([0-9]{4}-[0-9]{2}-[0-9]{2})",
                           body, re.IGNORECASE)
        addressed_on = addr_m.group(1) if addr_m else None
        entries.append({
            "nd_id": nd_id,
            "title": title,
            "status": status,
            "issued_on": issued_on,
            "addressed_on": addressed_on,
        })
    return entries


def _read_disagreement_register(repo_root: pathlib.Path) -> Dict[str, Any]:
    """Parse DISAGREEMENT_REGISTER entry table (currently empty)."""
    text = _safe_read(repo_root / P_DISAGREEMENT_REGISTER)
    if not text:
        return {"open_count": 0, "resolved_count": 0, "entries": []}
    # Look for table rows under §4 or §3
    entries = []
    for m in re.finditer(
        r"^\|\s*(DIS\.[a-z0-9._]+)\s*\|.*?\|.*?\|.*?\|.*?\|",
        text, re.MULTILINE
    ):
        entries.append({"dr_id": m.group(1).strip()})
    open_count = sum(1 for e in entries if "open" in e.get("status", "").lower())
    resolved_count = len(entries) - open_count
    return {"open_count": open_count, "resolved_count": resolved_count, "entries": entries}


def _read_staleness_register(repo_root: pathlib.Path) -> List[Dict[str, Any]]:
    """Parse rows from STALENESS_REGISTER.md."""
    text = _safe_read(repo_root / P_STALENESS_REGISTER)
    if not text:
        return []
    rows = []
    for m in re.finditer(
        r"^\|\s*`?([^|`]+)`?\s*\|\s*([^|]+)\|\s*([^|]+)\|",
        text, re.MULTILINE
    ):
        path_val = m.group(1).strip()
        # Skip header rows
        if path_val.lower() in ("file", "path", "artifact", "---"):
            continue
        since = m.group(2).strip()
        reason = m.group(3).strip()
        if path_val and since and reason and "---" not in path_val:
            rows.append({"path": path_val, "since": since, "reason": reason})
    return rows


def _read_red_team_reports(repo_root: pathlib.Path) -> List[Dict[str, Any]]:
    """Parse RED_TEAM_*.md files from verification_artifacts/RAG/."""
    d = repo_root / P_RED_TEAM_DIR
    if not d.exists():
        return []
    results = []
    for f in sorted(d.glob("RED_TEAM_*.md")):
        text = f.read_text(encoding="utf-8")
        # Extract session_id from frontmatter
        session_m = re.search(r"^session_id:\s*(.+)$", text, re.MULTILINE)
        session_id = session_m.group(1).strip() if session_m else None
        # Extract overall verdict
        verdict_m = re.search(r"(?:overall[_\s]+)?verdict[:\s]+([A-Z]+)", text, re.IGNORECASE)
        verdict = verdict_m.group(1).upper() if verdict_m else "UNKNOWN"
        # Count findings (lines starting with RT or RT.)
        findings = re.findall(r"^(?:RT\d+|RT\.\d+)[:\s]", text, re.MULTILINE)
        # Extract residuals
        residuals = re.findall(r"KR-\d+", text)
        # Date from frontmatter
        date_m = re.search(r"^(?:date|produced_on|performed_on)[:\s]+([0-9]{4}-[0-9]{2}-[0-9]{2})",
                           text, re.MULTILINE)
        performed_on = date_m.group(1) if date_m else None
        results.append({
            "session_id": session_id,
            "report_path": str(f.relative_to(repo_root)),
            "verdict": verdict,
            "finding_count": len(findings),
            "residuals": list(dict.fromkeys(residuals)),  # deduplicate preserving order
            "performed_on": performed_on,
        })
    return results


def _phase_id_sort_key(phase_id: str) -> Tuple:
    """Sort B.3.5 correctly between B.3 and B.4 (int-segment comparison)."""
    try:
        return tuple(int(x) for x in phase_id.lstrip("B.").split("."))
    except ValueError:
        return (999,)


def _read_corpus_state(repo_root: pathlib.Path) -> Dict[str, Any]:
    """Assemble corpus density metrics from verification artifacts and corpus files."""
    state: Dict[str, Any] = {}

    cr = _safe_read(repo_root / P_RAG_CHUNKING_REPORT)
    if cr:
        try:
            cr_data = json.loads(cr)
            per_type = cr_data.get("per_doctype_counts", {})
            state["rag_chunks"] = sum(per_type.values())
            state["chunks_by_doc_type"] = [
                {"doc_type": k, "count": v} for k, v in per_type.items()
            ]
        except (json.JSONDecodeError, TypeError):
            _SERIALIZER_WARNINGS.append("corpus_state: failed to parse chunking_report.json")

    nc = _safe_read(repo_root / P_RAG_NODE_COUNT)
    if nc:
        try:
            nc_data = json.loads(nc)
            state["rag_graph_nodes"] = nc_data.get("total_nodes", 0)
        except (json.JSONDecodeError, TypeError):
            _SERIALIZER_WARNINGS.append("corpus_state: failed to parse b4_node_count.json")

    ec = _safe_read(repo_root / P_RAG_EDGE_COUNT)
    if ec:
        try:
            ec_data = json.loads(ec)
            state["rag_graph_edges"] = ec_data.get("db_edge_count") or ec_data.get("total_edges", 0)
            edges_by_type = ec_data.get("db_edges_by_type") or ec_data.get("edges_by_type", {})
            state["edge_classes"] = [
                {"class": k, "count": v} for k, v in edges_by_type.items()
            ]
        except (json.JSONDecodeError, TypeError):
            _SERIALIZER_WARNINGS.append("corpus_state: failed to parse b4_edge_count.json")

    msr_text = _safe_read(repo_root / P_MSR)
    if msr_text:
        state["msr_signals"] = len(re.findall(r"^SIG\.[A-Z]+\.\d+:", msr_text, re.MULTILINE))

    cgm_text = _safe_read(repo_root / P_CGM)
    if cgm_text:
        # CGM_v2_0 uses "234 nodes" prose summary rather than per-node headers
        cgm_nodes_m = re.search(r"\b(\d+)\s+nodes?\b", cgm_text, re.IGNORECASE)
        state["cgm_nodes"] = int(cgm_nodes_m.group(1)) if cgm_nodes_m else 0
        reconciled = re.search(r"reconciled[_\s]edges?[:\s]+(\d+)", cgm_text, re.IGNORECASE)
        # Fallback: look for "X edges" figure near the node count
        if not reconciled:
            edges_m = re.search(r"\b(\d+)\s+edges?\b", cgm_text, re.IGNORECASE)
            state["cgm_reconciled_edges"] = int(edges_m.group(1)) if edges_m else 0
        else:
            state["cgm_reconciled_edges"] = int(reconciled.group(1))

    dr_dir = repo_root / P_DOMAIN_REPORTS_DIR
    l3_coverage = []
    if dr_dir.exists():
        seen_bases: set = set()
        for f in sorted(dr_dir.glob("REPORT_*.md"), reverse=True):
            base = re.sub(r"_v\d+_\d+\.md$", "", f.name)
            if base not in seen_bases:
                seen_bases.add(base)
                domain_id = base.replace("REPORT_", "")
                l3_coverage.append({"domain_id": domain_id, "status": "current"})
    state["l3_reports_current"] = len(l3_coverage)
    state["l3_coverage"] = l3_coverage

    return state


def _read_intervention_backfill(repo_root: pathlib.Path) -> Dict[str, Any]:
    """Read INTERVENTION_BACKFILL_v1_0.md for retroactive override/halt annotations."""
    text = _safe_read(repo_root / P_INTERVENTION_BACKFILL)
    if not text:
        return {}
    import yaml  # noqa: PLC0415
    backfill: Dict[str, Any] = {}
    for block in re.finditer(r"^```yaml\s*\n(.*?)^```\s*$", text, re.MULTILINE | re.DOTALL):
        try:
            d = yaml.safe_load(block.group(1))
            if not isinstance(d, dict):
                continue
            sid = d.get("session_id")
            if not sid:
                continue
            backfill[sid] = {
                "native_overrides": d.get("native_overrides", []),
                "halts_encountered": d.get("halts_encountered", []),
            }
        except Exception:
            pass
    return backfill


def _read_phase_b_plan(repo_root: pathlib.Path) -> List[Dict[str, Any]]:
    """Parse B.0–B.10 sub-phase entries from PHASE_B_PLAN_v1_0.md §G.

    BF.1: anchors to '## G. Expanded Phase Plan' before regex so document-
    structure §B dividers (lines 37-73) do not shadow the real §G definitions.
    """
    text = _safe_read(repo_root / P_PHASE_B_PLAN)
    if not text:
        return []

    # Anchor to §G — the real sub-phase definitions live after this header
    anchor = re.search(r"^## G\.\s+Expanded Phase Plan", text, re.MULTILINE)
    if not anchor:
        # Fallback: search full text but log a warning
        _SERIALIZER_WARNINGS.append(
            "PHASE_B_PLAN: '## G. Expanded Phase Plan' anchor not found; "
            "parsing full text (may produce wrong results)"
        )
        search_text = text
    else:
        search_text = text[anchor.start():]

    phases = []
    seen = set()
    # Real definitions: ### Phase B.N — Title (N session(s)[...])
    for m in re.finditer(
        r"^###\s+Phase\s+(B\.\d+(?:\.\d+)?)\s+[—-]+\s+(.+?)\s+\((\d+)\s+session",
        search_text, re.MULTILINE
    ):
        phase_id = m.group(1)
        if phase_id in seen:
            continue
        seen.add(phase_id)
        title = m.group(2).strip()
        session_est = int(m.group(3))
        phases.append({
            "phase_id": phase_id,
            "title": title,
            "status": "unknown",  # enriched below by cross-check with current_state
            "session_count_estimated": session_est,
        })

    if len(phases) < 10:
        _SERIALIZER_WARNINGS.append(
            f"PHASE_B_PLAN: expected ≥10 sub-phases in §G, found {len(phases)}. "
            "Check that the '### Phase B.N — Title (N session' pattern still matches."
        )

    # Sort by int-segment comparison so B.3.5 lands between B.3 and B.4
    phases.sort(key=lambda p: _phase_id_sort_key(p["phase_id"]))
    return phases


_MACRO_PHASE_RE = re.compile(
    r"^###\s+(M\d+)\s+[—-]+\s+(.+?)$",
    re.MULTILINE,
)

# M1 milestones (8) — from MACRO_PLAN_v2_0 M1 exit criteria (phase COMPLETED).
_M1_MILESTONES: List[Dict[str, Any]] = [
    {"id": "M1.1", "title": "Forensic chart data locked (FORENSIC_v8_0)", "status": "completed"},
    {"id": "M1.2", "title": "MSR 499 signals compiled (MSR_v3_0)", "status": "completed"},
    {"id": "M1.3", "title": "UCN synthesis complete (UCN_v4_0)", "status": "completed"},
    {"id": "M1.4", "title": "CDLM cross-domain matrix built (CDLM_v1_1)", "status": "completed"},
    {"id": "M1.5", "title": "CGM graph model v2 built (CGM_v2_0)", "status": "completed"},
    {"id": "M1.6", "title": "L3 domain reports drafted (03_DOMAIN_REPORTS)", "status": "completed"},
    {"id": "M1.7", "title": "Life Event Log v1.2 seeded (LEL_v1_2)", "status": "completed"},
    {"id": "M1.8", "title": "FILE_REGISTRY and governance stack established", "status": "completed"},
]

# M3–M10 milestones — coarse-grained exit criteria from MACRO_PLAN_v2_0 §3.3–§3.10.
# Status is always pending until the phase is active/closed; refined at phase-open.
_M3_MILESTONES: List[Dict[str, Any]] = [
    {"id": "M3.a", "title": "Vimshottari + Yogini + Chara + Narayana dashas computed (lifetime horizon)", "status": "pending"},
    {"id": "M3.b", "title": "Transit engine produces date-indexed signal lit/dormant/ripening states", "status": "pending"},
    {"id": "M3.c", "title": "Varshaphala rectification completed", "status": "pending"},
    {"id": "M3.d", "title": "KP sublord timing integrated with MSR signal system", "status": "pending"},
    {"id": "M3.e", "title": "Shadbala computed over full dasha horizon", "status": "pending"},
    {"id": "M3.f", "title": "Temporal validator meta-tests pass on held-out date sample", "status": "pending"},
]
_M4_MILESTONES: List[Dict[str, Any]] = [
    {"id": "M4.a", "title": "Per-signal calibration tables produced with bootstrapped confidence intervals", "status": "pending"},
    {"id": "M4.b", "title": "Shadow-mode regime documented and enforced for all posterior updates", "status": "pending"},
    {"id": "M4.c", "title": "n=1 validity disclaimer attached to all outputs", "status": "pending"},
    {"id": "M4.d", "title": "Held-out LEL 20% partition passes calibration validity test", "status": "pending"},
    {"id": "M4.e", "title": "LL.1–LL.7 shadow-to-production promotion criteria met", "status": "pending"},
]
_M5_MILESTONES: List[Dict[str, Any]] = [
    {"id": "M5.a", "title": "DBN identifies on held-out data (LEL 20% partition)", "status": "pending"},
    {"id": "M5.b", "title": "Signal embeddings stable across 3 refit runs", "status": "pending"},
    {"id": "M5.c", "title": "Bayesian posterior framing applied to all outputs", "status": "pending"},
    {"id": "M5.d", "title": "DBN topology approved by native", "status": "pending"},
    {"id": "M5.e", "title": "Prior specification documented and approved", "status": "pending"},
]
_M6_MILESTONES: List[Dict[str, Any]] = [
    {"id": "M6.a", "title": "≥ 50 verification windows closed and scored", "status": "pending"},
    {"id": "M6.b", "title": "Automated scoring reproducibility verified (re-run = identical verdicts)", "status": "pending"},
    {"id": "M6.c", "title": "Counterfactual learning registry populated (LL.9 active)", "status": "pending"},
    {"id": "M6.d", "title": "Forward prediction validity declared for at least one life-domain", "status": "pending"},
    {"id": "M6.e", "title": "Calibration drift monitored and within declared tolerance", "status": "pending"},
]
_M7_MILESTONES: List[Dict[str, Any]] = [
    {"id": "M7.a", "title": "≥ N consented subjects added (N ≥ 5; exact set at M7 open)", "status": "pending"},
    {"id": "M7.b", "title": "Per-subject calibration tables match method-extension validity test", "status": "pending"},
    {"id": "M7.c", "title": "Cohort modulators (desha-kala-patra) produced", "status": "pending"},
    {"id": "M7.d", "title": "LL.10 cohort corpus assembled", "status": "pending"},
    {"id": "M7.e", "title": "Cohort-mode LL.7 active per LL-Appendix.A", "status": "pending"},
]
_M8_MILESTONES: List[Dict[str, Any]] = [
    {"id": "M8.a", "title": "All listed classical corpora indexed and attributed", "status": "pending"},
    {"id": "M8.b", "title": "Classical-claim-holds/fails findings produced for each M5 probabilistic output", "status": "pending"},
    {"id": "M8.c", "title": "Attribution confidence tags populated for every citation", "status": "pending"},
    {"id": "M8.d", "title": "Translation-accuracy cross-check completed for non-English sources", "status": "pending"},
    {"id": "M8.e", "title": "MSR signal-set expanded to include Nadi + BNN school signals (pre-M9)", "status": "pending"},
]
_M9_MILESTONES: List[Dict[str, Any]] = [
    {"id": "M9.a", "title": "All seven schools operating on shared signal set", "status": "pending"},
    {"id": "M9.b", "title": "Inter-school convergence metrics calibrated", "status": "pending"},
    {"id": "M9.c", "title": "School-disagreement resolution protocol populated with ≥ N worked examples", "status": "pending"},
    {"id": "M9.d", "title": "Convergence-as-precision-signal evidence logged", "status": "pending"},
]
_M10_MILESTONES: List[Dict[str, Any]] = [
    {"id": "M10.a", "title": "Wiring inventory complete (all L4 prompt templates live; UCN final; LL.10 fine-tune validated)", "status": "pending"},
    {"id": "M10.b", "title": "Acharya-reviewer panel ≥ 3 active", "status": "pending"},
    {"id": "M10.c", "title": "At least one blind-test report produced and native-published", "status": "pending"},
    {"id": "M10.d", "title": "Methodology published (arXiv preprint minimum)", "status": "pending"},
    {"id": "M10.e", "title": "LL-Appendix activation state shows LL.1–LL.10 all active", "status": "pending"},
]

_MACRO_MILESTONES: Dict[str, List[Dict[str, Any]]] = {
    "M3": _M3_MILESTONES, "M4": _M4_MILESTONES, "M5": _M5_MILESTONES,
    "M6": _M6_MILESTONES, "M7": _M7_MILESTONES, "M8": _M8_MILESTONES,
    "M9": _M9_MILESTONES, "M10": _M10_MILESTONES,
}


def _read_macro_arc(
    repo_root: pathlib.Path,
    phase_b_plan: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Parse M1–M10 from MACRO_PLAN_v2_0.md and attach per-phase milestones.

    BF.2: milestones[] on every entry. M2 reuses phase_b_plan (12 corrected
    entries). M1 uses known-completed milestones. M3–M10 get a placeholder.
    Logs a warning instead of silently falling back.
    """
    text = _safe_read(repo_root / P_MACRO_PLAN)
    phases: List[Dict[str, Any]] = []

    if text:
        anchor = re.search(r"^###\s+M1\s+[—-]", text, re.MULTILINE)
        search_text = text[anchor.start():] if anchor else text
        seen: set = set()
        for m in _MACRO_PHASE_RE.finditer(search_text):
            mid = m.group(1)
            if mid in seen:
                continue
            seen.add(mid)
            phases.append({"id": mid, "title": m.group(2).strip(), "status": "pending"})

    if len(phases) < 10:
        _SERIALIZER_WARNINGS.append(
            f"MACRO_PLAN: expected 10 macro-phases, parsed {len(phases)}. "
            "Using known-correct fallback for missing entries."
        )
        known = [
            ("M1", "Corpus Completeness"), ("M2", "Corpus Activation"),
            ("M3", "Domain Report Drafting"), ("M4", "Temporal Engines"),
            ("M5", "Prediction Calibration"), ("M6", "Learning Layer Build"),
            ("M7", "Multi-Native Expansion"), ("M8", "Research Instrument"),
            ("M9", "Publication / Peer Review"), ("M10", "Long-Cycle Calibration"),
        ]
        existing_ids = {p["id"] for p in phases}
        for mid, title in known:
            if mid not in existing_ids:
                phases.append({"id": mid, "title": title, "status": "pending"})
        phases.sort(key=lambda p: int(p["id"][1:]))

    # Build M2 milestones from phase_b_plan (the correctly-parsed 12 entries)
    m2_milestones = [
        {
            "id": sp["phase_id"],
            "title": sp["title"],
            "status": sp.get("status", "pending"),
            "session_count_actual": sp.get("session_count_actual", 0),
            "session_count_estimated": sp.get("session_count_estimated"),
        }
        for sp in (phase_b_plan or [])
    ] or [{"id": "B.0", "title": "Foundations", "status": "pending"}]

    for arc in phases:
        mid = arc["id"]
        if mid == "M1":
            arc["milestones"] = _M1_MILESTONES
        elif mid == "M2":
            arc["milestones"] = m2_milestones
        else:
            arc["milestones"] = _MACRO_MILESTONES.get(
                mid,
                [{"id": f"{mid}.0", "title": "Planned — decomposition deferred", "status": "pending"}],
            )

    return phases


def _read_drift_history(repo_root: pathlib.Path, n: int = TREND_WINDOW_DEFAULT) -> List[Dict[str, Any]]:
    """Read most-recent N drift report JSON sidecars; branch (a) confirmed in session open."""
    d = repo_root / P_DRIFT_REPORTS_DIR
    if not d.exists():
        return []
    files = sorted(d.glob("*.json"), key=lambda f: f.name)[-n:]
    results = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            dr = data.get("drift_report", data)
            results.append({
                "report_file": f.name,
                "session_id": dr.get("session_id"),
                "run_at": dr.get("run_at"),
                "exit_code": dr.get("exit_code"),
                "finding_count": len(dr.get("findings", [])),
            })
        except Exception:
            pass
    return results


def _read_schema_history(repo_root: pathlib.Path, n: int = TREND_WINDOW_DEFAULT) -> List[Dict[str, Any]]:
    """Read most-recent N schema report JSON sidecars."""
    d = repo_root / P_SCHEMA_REPORTS_DIR
    if not d.exists():
        return []
    files = sorted(d.glob("*.json"), key=lambda f: f.name)[-n:]
    results = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sr = data.get("schema_validation_report", data)
            summary = sr.get("summary", {})
            finding_count = (
                summary.get("total", 0) if isinstance(summary, dict)
                else len(sr.get("violations", []))
            )
            results.append({
                "report_file": f.name,
                "session_id": sr.get("session_id"),
                "run_at": sr.get("run_at"),
                "exit_code": sr.get("exit_code"),
                "finding_count": finding_count,
            })
        except Exception:
            pass
    return results



def _read_cowork_ledger(repo_root: pathlib.Path) -> List[Dict[str, Any]]:
    """Read COWORK_LEDGER.md entries; returns empty list if file absent (graceful)."""
    text = _safe_read(repo_root / P_COWORK_LEDGER)
    if not text:
        return []
    entries = []
    # Match YAML code blocks that represent ledger entries
    for block in re.finditer(r"^```yaml\s*\n(.*?)^```\s*$", text, re.MULTILINE | re.DOTALL):
        try:
            import yaml
            d = yaml.safe_load(block.group(1))
            if isinstance(d, dict) and "thread_name" in d:
                entries.append({
                    "thread_name": d.get("thread_name"),
                    "opened_on": _normalize_iso(d.get("opened_on")),
                    "closed_on": _normalize_iso(d.get("closed_on")),
                    "purpose": d.get("purpose"),
                    "outcomes": d.get("outcomes", []),
                    "spawned_sessions": d.get("spawned_sessions", []),
                })
        except Exception:
            pass
    # Fallback: parse markdown list rows under §3 Entries if no YAML blocks
    if not entries:
        for m in re.finditer(
            r"^\*\*thread_name\*\*:\s*(.+)$",
            text, re.MULTILINE
        ):
            entries.append({"thread_name": m.group(1).strip()})
    return entries


def _read_current_brief(repo_root: pathlib.Path) -> Optional[Dict[str, Any]]:
    """Read CLAUDECODE_BRIEF.md at repo root; returns None if absent or status COMPLETE."""
    text = _safe_read(repo_root / P_CURRENT_BRIEF)
    if not text:
        return None
    # Parse frontmatter
    import yaml
    fm_m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not fm_m:
        return None
    try:
        fm = yaml.safe_load(fm_m.group(1))
    except yaml.YAMLError:
        return None
    if not isinstance(fm, dict):
        return None
    status = str(fm.get("status", "")).upper()
    if status == "COMPLETE":
        return None
    session_id = fm.get("session_id", "")
    # Count ACs in the table
    ac_total = len(re.findall(r"^\|\s*\*\*AC\.\d+\*\*", text, re.MULTILINE))
    # Extract may_touch summary (first 3 lines of the may_touch block)
    may_touch_m = re.search(r"### may_touch\s*\n```\s*\n(.*?)```", text, re.DOTALL)
    may_touch_lines = []
    if may_touch_m:
        may_touch_lines = [l.strip() for l in may_touch_m.group(1).strip().splitlines()[:3] if l.strip()]
    return {
        "session_id": session_id,
        "status": fm.get("status", "IN_PROGRESS"),
        "ac_total": ac_total,
        "ac_passed_known": 0,
        "may_touch_summary": may_touch_lines,
        "must_not_touch_summary": [],
    }


# --------------------------------------------------------------------------------------
# Full SESSION_LOG parser (v0.2.0 — builds sessions_index + per-session bodies)
# --------------------------------------------------------------------------------------

def _parse_all_sessions(repo_root: pathlib.Path) -> List[Dict[str, Any]]:
    """
    Parse the full SESSION_LOG.md and return a list of session index rows.
    Each row carries metadata for the sessions_index array in build_state.json.
    """
    p = repo_root / P_SESSION_LOG
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8")

    # Split on ## headings to get individual session blocks
    session_blocks = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    sessions = []

    for block in session_blocks:
        if not block.strip():
            continue
        # Try to match a session header
        hdr = re.match(
            r"^##\s+Session\s+([\w._-]+)\s+—\s+(.+?)\s*\(([\d-]+)(?:,\s*([^)]+))?\)",
            block, re.MULTILINE
        )
        hdr2 = re.match(
            r"^##\s+([A-Z][A-Za-z0-9_]+(?:_[A-Za-z0-9]+)*)\s+—\s+(.+?)$",
            block, re.MULTILINE
        )
        if not hdr and not hdr2:
            continue

        if hdr:
            sid = hdr.group(1)
            title = hdr.group(2).strip()
            closed_on = hdr.group(3)
            summary = (hdr.group(4) or "").strip() or None
        else:
            sid = hdr2.group(1)
            title = hdr2.group(2).strip()
            closed_on = None
            summary = None
            # "## Session — REAL_NAME ..." → hdr2 captures "Session" as sid;
            # extract the real name from the start of the title instead.
            if sid == "Session":
                real = re.match(r"([A-Z][A-Za-z0-9_]+)", title)
                if real:
                    sid = real.group(1)

        # Try to extract session_close YAML for metadata
        close_block = None
        close_m = re.search(
            r"```ya?ml\s*\nsession_close:(.*?)^```", block,
            re.MULTILINE | re.DOTALL
        )
        if close_m:
            try:
                import yaml
                close_block = yaml.safe_load("session_close:" + close_m.group(1))
                if isinstance(close_block, dict):
                    close_block = close_block.get("session_close", close_block)
            except Exception:
                close_block = None

        # Also parse session_open YAML for fields not in close (e.g. sub_phase)
        open_block = None
        open_m = re.search(
            r"```ya?ml\s*\nsession_open:(.*?)^```", block,
            re.MULTILINE | re.DOTALL
        )
        if open_m:
            try:
                import yaml
                open_block = yaml.safe_load("session_open:" + open_m.group(1))
                if isinstance(open_block, dict):
                    open_block = open_block.get("session_open", open_block)
            except Exception:
                open_block = None

        # Extract drift/schema exit codes
        drift_exit = None
        schema_exit = None
        if close_block and isinstance(close_block, dict):
            drift_run = close_block.get("drift_detector_run", {}) or {}
            schema_run = close_block.get("schema_validator_run", {}) or {}
            def _to_int_or_none(v):
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return None

            drift_exit = _to_int_or_none(drift_run.get("exit_code")) if isinstance(drift_run, dict) else None
            schema_exit = _to_int_or_none(schema_run.get("exit_code")) if isinstance(schema_run, dict) else None
            if closed_on is None:
                closed_on = _normalize_iso(close_block.get("closed_at", ""))

        # Try to infer session class from context
        session_class = "unknown"
        if close_block and isinstance(close_block, dict):
            session_class = str(close_block.get("expected_session_class", "unknown"))
        # Fallback inference from title/id
        if session_class in ("unknown", "null", "None", ""):
            sid_lower = sid.lower()
            if "governance_aside" in sid_lower or "build_tracker" in sid_lower or "gcs" in sid_lower:
                session_class = "governance_aside"
            elif "exec" in sid_lower and "m2" in sid_lower:
                session_class = "m2_corpus_execution"
            elif "step_" in sid_lower or "rebuild" in sid_lower:
                session_class = "governance_aside"
            elif "red_team" in sid_lower:
                session_class = "red_team"
            elif "plan" in sid_lower:
                session_class = "planning_only"
            elif "fix" in sid_lower:
                session_class = "fix_session"

        # Infer phase_id — check close block first, then open block's sub_phase
        phase_id = None
        if close_block and isinstance(close_block, dict):
            raw = close_block.get("active_phase_plan_sub_phase")
            if raw:
                pm = re.search(r"\b(B\.\d+(?:\.\d+)?)\b", str(raw))
                phase_id = pm.group(1) if pm else None
        if phase_id is None and open_block and isinstance(open_block, dict):
            raw = open_block.get("sub_phase") or open_block.get("active_phase_plan_sub_phase")
            if raw:
                pm = re.search(r"\b(B\.\d+(?:\.\d+)?)\b", str(raw))
                phase_id = pm.group(1) if pm else None

        # One-liner deliverable
        deliverable = None
        if close_block and isinstance(close_block, dict):
            deliverable_raw = close_block.get("deliverable_summary") or close_block.get("deliverable")
            if deliverable_raw:
                # First 120 chars of the deliverable
                deliverable = str(deliverable_raw)[:120].rstrip()

        # Infer closed_on from block text if still None
        if closed_on is None:
            date_m = re.search(r"(?:closed?|date)[_:\s]+([0-9]{4}-[0-9]{2}-[0-9]{2})", block[:300])
            if date_m:
                closed_on = date_m.group(1)

        sessions.append({
            "session_id": sid,
            "title": title,
            "date": closed_on,
            "class": session_class,
            "phase_id": phase_id,
            "drift_exit": drift_exit,
            "schema_exit": schema_exit,
            "deliverable_one_liner": deliverable,
            "detail_shard": f"sessions/{sid}.json",
        })

    # BF.3: SESSION_LOG block order is file-position; re-sort chronologically newest-first.
    sessions.sort(key=lambda s: s.get("date") or "0000-00-00", reverse=True)
    return sessions


def _extract_session_body(repo_root: pathlib.Path, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Extract a single session's full data from SESSION_LOG for the per-session shard.
    Returns None if the session is not found.
    """
    p = repo_root / P_SESSION_LOG
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8")

    # Find the block for this session_id
    # The session starts at ## <session_id> — and ends at the next ## heading
    pattern = re.compile(
        rf"(^##\s+(?:Session\s+)?{re.escape(session_id)}\s+—.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL
    )
    m = pattern.search(text)
    if not m:
        return None
    block = m.group(1)

    # Extract session_open YAML
    open_yaml = None
    open_m = re.search(
        r"```ya?ml\s*\nsession_open:(.*?)^```",
        block, re.MULTILINE | re.DOTALL
    )
    if open_m:
        try:
            import yaml
            parsed = yaml.safe_load("session_open:" + open_m.group(1))
            open_yaml = parsed.get("session_open") if isinstance(parsed, dict) else None
        except Exception:
            pass

    # Extract session_close YAML
    close_yaml = None
    close_m = re.search(
        r"```ya?ml\s*\nsession_close:(.*?)^```",
        block, re.MULTILINE | re.DOTALL
    )
    if close_m:
        try:
            import yaml
            parsed = yaml.safe_load("session_close:" + close_m.group(1))
            close_yaml = parsed.get("session_close") if isinstance(parsed, dict) else None
        except Exception:
            pass

    # Extract body text between open and close
    body_text = block
    if open_yaml:
        body_text = re.sub(r"```ya?ml\s*\nsession_open:.*?^```", "", body_text,
                           flags=re.MULTILINE | re.DOTALL)
    if close_yaml:
        body_text = re.sub(r"```ya?ml\s*\nsession_close:.*?^```", "", body_text,
                           flags=re.MULTILINE | re.DOTALL)

    # Extract files_touched from close_yaml
    files_touched = []
    if close_yaml and isinstance(close_yaml, dict):
        ft = close_yaml.get("files_touched", [])
        if isinstance(ft, list):
            files_touched = [
                {"path": str(f.get("path", "")), "reason": str(f.get("justification", ""))}
                if isinstance(f, dict) else {"path": str(f), "reason": ""}
                for f in ft
            ]

    # Extract deliverables from close_yaml (files_touched paths)
    deliverables = [f["path"] for f in files_touched] if files_touched else []

    # Extract residuals from close_yaml
    residuals = []
    if close_yaml and isinstance(close_yaml, dict):
        kr = close_yaml.get("known_residuals", [])
        if isinstance(kr, list):
            residuals = [str(r) for r in kr]

    # Linked reports
    linked = {"drift": None, "schema": None}
    if close_yaml and isinstance(close_yaml, dict):
        drun = close_yaml.get("drift_detector_run", {}) or {}
        srun = close_yaml.get("schema_validator_run", {}) or {}
        if isinstance(drun, dict):
            linked["drift"] = drun.get("report_path")
        if isinstance(srun, dict):
            linked["schema"] = srun.get("report_path")

    # Phase id
    phase_id = None
    if close_yaml and isinstance(close_yaml, dict):
        sub = close_yaml.get("active_phase_plan_sub_phase", "")
        pm = re.search(r"\b(B\.\d+(?:\.\d+)?)\b", str(sub))
        if pm:
            phase_id = pm.group(1)

    return {
        "session_id": session_id,
        "schema_version": SCHEMA_VERSION,
        "header": {
            "date": _normalize_iso(open_yaml.get("session_date") if open_yaml else None),
            "title": (open_yaml.get("session_title") if open_yaml else None),
            "agent": (open_yaml.get("agent") if open_yaml else None),
            "cowork_thread": (open_yaml.get("cowork_thread_name") if open_yaml else None),
        },
        "session_open": open_yaml,
        "session_close": close_yaml,
        "body_excerpts": {
            "objective": (open_yaml.get("session_objective") if open_yaml else None),
        },
        "files_touched": files_touched,
        "deliverables": deliverables,
        "residuals": residuals,
        "linked_reports": linked,
        "halts_encountered": (list(close_yaml.get("halts_encountered", [])) if close_yaml else []),
        "native_overrides": (list(close_yaml.get("native_overrides", [])) if close_yaml else []),
        "phase_id": phase_id,
        "session_class": (close_yaml.get("expected_session_class") if close_yaml else "unknown"),
        "previous_session_id": (close_yaml.get("previous_session_id") if close_yaml else None),
        "next_session_id": None,
    }


def _parse_phase_acs(repo_root: pathlib.Path, phase_id: str) -> List[Dict[str, Any]]:
    """Extract acceptance criteria for a sub-phase from PHASE_B_PLAN §G.

    BF.5: returns items with description, test, result_snippet fields.
    """
    text = _safe_read(repo_root / P_PHASE_B_PLAN)
    if not text:
        return []

    anchor = re.search(r"^## G\.\s+Expanded Phase Plan", text, re.MULTILINE)
    search_text = text[anchor.start():] if anchor else text

    # Find the block for this specific phase
    phase_block_m = re.search(
        rf"^###\s+Phase\s+{re.escape(phase_id)}\s+[—-]",
        search_text, re.MULTILINE
    )
    if not phase_block_m:
        return []

    # Extract text until the next ### Phase header or end
    start = phase_block_m.start()
    next_phase = re.search(r"^###\s+Phase\s+B\.", search_text[start + 1:], re.MULTILINE)
    block = search_text[start: start + 1 + next_phase.start()] if next_phase else search_text[start:]

    # Find the Acceptance criteria section
    ac_section = re.search(r"\*\*Acceptance criteria\.\*\*\s*\n(.*?)(?=\*\*Cost\.|---|\Z)",
                           block, re.DOTALL)
    if not ac_section:
        return []

    acs = []
    ac_text = ac_section.group(1)
    for bullet in re.split(r"\n[-*]\s+", ac_text):
        bullet = bullet.strip()
        if not bullet or len(bullet) < 10:
            continue
        # Each bullet is a criterion description; derive a short ac_id
        ac_num = len(acs) + 1
        acs.append({
            "ac_id": f"{phase_id}.AC{ac_num:02d}",
            "status": "unknown",
            "description": bullet[:300],
            "test": None,
            "result_snippet": None,
            "residual_id": None,
        })

    return acs


def _assemble_phase_detail(
    phase_id: str,
    sessions_index: List[Dict[str, Any]],
    phase_b_plan: List[Dict[str, Any]],
    repo_root: Optional[pathlib.Path] = None,
) -> Dict[str, Any]:
    """Assemble a per-phase detail shard from aggregated session data.

    BF.5: acceptance_criteria rows now include description, test, result_snippet.
    """
    plan_entry = next((p for p in phase_b_plan if p["phase_id"] == phase_id), None)
    title = plan_entry["title"] if plan_entry else phase_id
    phase_sessions = [s for s in sessions_index if s.get("phase_id") == phase_id]
    status = "in_progress" if phase_sessions else "unknown"
    if plan_entry:
        status = plan_entry.get("status", status)

    acs = _parse_phase_acs(repo_root, phase_id) if repo_root else []
    # Enrich AC status based on session close data — look for passed/failed mentions
    # (best-effort; full enrichment requires session-close AC evidence parsing)
    if plan_entry and plan_entry.get("status") == "completed" and acs:
        for ac in acs:
            ac["status"] = "passed"

    return {
        "phase_id": phase_id,
        "schema_version": SCHEMA_VERSION,
        "title": title,
        "macro_phase": "M2",
        "spec_pointer": f"00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md#{phase_id.lower().replace('.', '-')}",
        "status": status,
        "session_count_actual": len(phase_sessions),
        "session_count_estimated": plan_entry.get("session_count_estimated") if plan_entry else None,
        "sessions": [
            {
                "session_id": s["session_id"],
                "contribution": s.get("deliverable_one_liner"),
                "deliverables": [],
                "residuals_carry_forward": [],
            }
            for s in phase_sessions
        ],
        "acceptance_criteria": acs,
        "deliverables_complete": [],
        "deliverables_pending": [],
        "dependencies_inbound": [],
        "dependencies_outbound": [],
    }


# --------------------------------------------------------------------------------------
# Workstream derivation
# --------------------------------------------------------------------------------------

def _derive_workstreams(repo_root: pathlib.Path, generated_at: str) -> List[Dict[str, Any]]:
    """Derive parallel workstream entries from source files.

    Fields:
      id            — stable workstream identifier
      title         — human-readable name
      status        — current | active | substrate_only | recurring
      last_activity — ISO date string (YYYY-MM-DD) from file mtime or run timestamp
      event_count   — (LEL only) number of ## headings in the file
      prediction_count — (PPL only) non-empty line count in prediction_ledger.jsonl
    """
    def _mtime_date(path: pathlib.Path) -> Optional[str]:
        try:
            ts = path.stat().st_mtime
            return _dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        except Exception:
            return None

    # --- LEL ---
    lel_path = repo_root / P_LEL
    lel_text = _safe_read(lel_path)
    lel_event_count = len(re.findall(r"^##\s+", lel_text, re.MULTILINE)) if lel_text else 0
    lel_last = _mtime_date(lel_path)

    # --- PPL ---
    ppl_path = repo_root / P_PREDICTION_LEDGER
    ppl_count = 0
    ppl_status = "substrate_only"
    ppl_last = None
    if ppl_path.exists():
        try:
            lines = [l for l in ppl_path.read_text(encoding="utf-8").splitlines() if l.strip()]
            ppl_count = len(lines)
            if ppl_count > 0:
                ppl_status = "active"
        except Exception:
            pass
        ppl_last = _mtime_date(ppl_path)

    # --- BUILD_TRACKER (this very serializer run) ---
    build_last = generated_at[:10] if generated_at else None

    # --- GOVERNANCE_HYGIENE (latest drift report) ---
    drift_dir = repo_root / P_DRIFT_REPORTS_DIR
    hygiene_last: Optional[str] = None
    if drift_dir.exists():
        reports = sorted(
            (p for p in drift_dir.iterdir() if p.suffix == ".json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if reports:
            hygiene_last = _mtime_date(reports[0])

    return [
        {
            "id": "LEL",
            "title": "Life Event Log maintenance",
            "status": "current",
            "event_count": lel_event_count,
            "last_activity": lel_last,
        },
        {
            "id": "PPL",
            "title": "Prospective prediction logging",
            "status": ppl_status,
            "prediction_count": ppl_count,
            "last_activity": ppl_last,
        },
        {
            "id": "BUILD_TRACKER",
            "title": "Build tracker / portal",
            "status": "active",
            "last_activity": build_last,
        },
        {
            "id": "GOVERNANCE_HYGIENE",
            "title": "Governance asides",
            "status": "recurring",
            "last_activity": hygiene_last,
        },
    ]


# --------------------------------------------------------------------------------------
# Build-state assembly
# --------------------------------------------------------------------------------------

def assemble_build_state(
    repo_root: pathlib.Path,
    session_id: str,
    red_team_threshold: int = RED_TEAM_THRESHOLD_DEFAULT,
    recent_n: int = 5,
    trend_n: int = TREND_WINDOW_DEFAULT,
) -> Dict[str, Any]:
    """Assemble the full v0.3.0 build_state JSON."""
    # Reset module-level warnings for this run
    _SERIALIZER_WARNINGS.clear()

    cs = _read_current_state(repo_root)
    ca = _read_canonical_artifacts(repo_root)
    recent = _read_recent_sessions(repo_root, recent_n)
    next_qp = _read_next_quarterly_pass(repo_root)

    # v0.2.0 additions
    native_directives_entries = _read_native_directives(repo_root)
    dr_data = _read_disagreement_register(repo_root)
    staleness = _read_staleness_register(repo_root)
    red_team_passes = _read_red_team_reports(repo_root)
    phase_b_plan = _read_phase_b_plan(repo_root)
    # v0.3.0: pass phase_b_plan so M2 milestones are correct
    macro_arc = _read_macro_arc(repo_root, phase_b_plan=phase_b_plan)
    corpus_state = _read_corpus_state(repo_root)
    drift_trend = _read_drift_history(repo_root, trend_n)
    schema_trend = _read_schema_history(repo_root, trend_n)
    cowork_ledger = _read_cowork_ledger(repo_root)
    current_brief = _read_current_brief(repo_root)
    sessions_index = _parse_all_sessions(repo_root)

    today_progress = _compute_today_progress(sessions_index, repo_root)

    # Source fingerprints
    source_fps = {
        "current_state": _sha256(repo_root / P_CURRENT_STATE),
        "canonical_artifacts": _sha256(repo_root / P_CANONICAL_ARTIFACTS),
        "session_log": _sha256(repo_root / P_SESSION_LOG),
        "ongoing_hygiene_policies": _sha256(repo_root / P_ONGOING_HYGIENE),
    }

    # Governance baseline
    baseline_row = ca["artifacts"].get("GOVERNANCE_BASELINE", {})
    baseline_path = baseline_row.get("path")
    rebuild_status = "closed" if cs.get("cross_check_authority") == "CURRENT_STATE" else "active"

    red_team_counter = int(cs.get("red_team_counter", 0))
    red_team_due = red_team_counter >= red_team_threshold

    # Canonical artifacts list
    artifacts_list = []
    for cid, row in ca["artifacts"].items():
        artifacts_list.append({
            "canonical_id": cid,
            "path": row.get("path", ""),
            "version": str(row.get("version", "")),
            "status": str(row.get("status", "")),
            "fingerprint_sha256": row.get("fingerprint_sha256"),
            "last_verified_session": row.get("last_verified_session"),
            "last_verified_on": _normalize_iso(row.get("last_verified_on")),
        })


    # Enrich macro_arc with active/completed status from CURRENT_STATE.
    # Use integer comparison (int("M2"[1:]) == 2) to avoid "M10" < "M2" string bug.
    active_macro = cs.get("active_macro_phase", "M2")
    try:
        active_macro_num = int(active_macro[1:])
    except (ValueError, IndexError):
        active_macro_num = 2
    for arc_entry in macro_arc:
        mid = arc_entry["id"]
        try:
            mid_num = int(mid[1:])
        except (ValueError, IndexError):
            mid_num = 99
        if mid == active_macro:
            arc_entry["status"] = cs.get("active_macro_phase_status", "active")
        elif mid_num < active_macro_num:
            arc_entry["status"] = "completed"
        else:
            arc_entry["status"] = "pending"

    # Enrich sub_phases with status from CURRENT_STATE sub_phase string
    active_sub = cs.get("active_phase_plan_sub_phase", "")
    active_sub_match = re.search(r"\b(B\.\d+(?:\.\d+)?)\b", str(active_sub))
    active_sub_id = active_sub_match.group(1) if active_sub_match else None
    for sp in phase_b_plan:
        if active_sub_id and sp["phase_id"] == active_sub_id:
            if "complete" in active_sub.lower():
                sp["status"] = "completed"
            else:
                sp["status"] = "in_progress"
        elif active_sub_id and _phase_id_sort_key(sp["phase_id"]) < _phase_id_sort_key(active_sub_id):
            # numeric compare: B.10 > B.9 correctly (string compare would fail)
            sp["status"] = "completed"
        else:
            sp["status"] = "pending"
        # Count actual sessions
        sp["session_count_actual"] = sum(
            1 for s in sessions_index if s.get("phase_id") == sp["phase_id"]
        )

    # Rebuild M2 milestones now that phase_b_plan statuses are enriched.
    # _read_macro_arc builds m2_milestones BEFORE enrichment (copy semantics),
    # so we refresh them here to reflect the post-enrichment status.
    for arc_entry in macro_arc:
        if arc_entry["id"] == "M2":
            arc_entry["milestones"] = [
                {
                    "id": sp["phase_id"],
                    "title": sp["title"],
                    "status": sp.get("status", "pending"),
                    "session_count_actual": sp.get("session_count_actual", 0),
                    "session_count_estimated": sp.get("session_count_estimated"),
                }
                for sp in phase_b_plan
            ]
            break

    # Build phases_index from sessions_index
    phase_ids_seen = []
    for s in sessions_index:
        pid = s.get("phase_id")
        if pid and pid not in phase_ids_seen:
            phase_ids_seen.append(pid)
    phases_index = [
        {
            "phase_id": pid,
            "detail_shard": f"phases/{pid}.json",
            "status": next((sp["status"] for sp in phase_b_plan if sp["phase_id"] == pid), "unknown"),
            "session_count": sum(1 for s in sessions_index if s.get("phase_id") == pid),
        }
        for pid in phase_ids_seen
    ]

    # staleness_seconds since last close
    last_closed_at = cs.get("last_session_closed_at")
    staleness_seconds = None
    if last_closed_at:
        try:
            lca = _dt.datetime.fromisoformat(str(last_closed_at))
            if lca.tzinfo is None:
                lca = lca.replace(tzinfo=_dt.timezone.utc)
            now = _dt.datetime.now(_dt.timezone.utc)
            staleness_seconds = int((now - lca).total_seconds())
        except (ValueError, TypeError):
            pass

    generated_at = _dt.datetime.now(_dt.timezone.utc).isoformat()

    return {
        # ---- shared fields (v0.1.0 shape preserved) ----
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "generated_by_session": session_id,
        "generator_version": GENERATOR_VERSION,
        "source_fingerprints": source_fps,
        "macro_phase": {
            "id": cs.get("active_macro_phase", ""),
            "title": cs.get("active_macro_phase_title", ""),
            "status": cs.get("active_macro_phase_status", ""),
            "macro_arc": macro_arc,
        },
        "phase_plan": {
            "path": cs.get("active_phase_plan", ""),
            "version": str(cs.get("active_phase_plan_version", "")),
            "sub_phase": cs.get("active_phase_plan_sub_phase", ""),
            "status": cs.get("active_phase_plan_status", ""),
            "sub_phases": phase_b_plan,
        },
        "governance": {
            "rebuild_status": rebuild_status,
            "baseline_artifact_path": baseline_path,
            "baseline_closed_on": None,
            "active_step": cs.get("active_governance_step"),
            "active_step_status": cs.get("active_governance_step_status"),
            "next_step": cs.get("next_governance_step"),
            "next_quarterly_pass": next_qp,
            "red_team": {
                "counter": red_team_counter,
                "threshold": red_team_threshold,
                "due": red_team_due,
                "note": cs.get("red_team_due_note"),
            },
            "scripts_trend": {
                "drift_detector": drift_trend,
                "schema_validator": schema_trend,
            },
        },
        "last_session": {
            "id": cs.get("last_session_id", ""),
            "closed_at": _normalize_iso(cs.get("last_session_closed_at")),
            "agent": cs.get("last_session_agent"),
            "cowork_thread_name": cs.get("last_session_cowork_thread_name"),
            "close_state": cs.get("last_session_close_state"),
            "drift_verdict": cs.get("last_session_drift_verdict"),
            "deliverable_summary": cs.get("last_session_deliverable"),
            "previous_session_id": cs.get("previous_session_id"),
        },
        "next_session": {
            "objective": cs.get("next_session_objective", ""),
            "proposed_cowork_thread_name": cs.get("next_session_proposed_cowork_thread_name"),
        },
        "native_directives": {
            "open": list(cs.get("open_native_directives") or []),
            "addressed": list(cs.get("addressed_native_directives") or []),
            "note": cs.get("nd_note"),
            "entries": native_directives_entries,
        },
        "disagreement_register": dr_data,
        "canonical_artifacts": artifacts_list,
        "recent_sessions": recent,
        # ---- v0.2.0 additions ----
        "red_team_passes": red_team_passes,
        "staleness_register": staleness,
        "current_brief": current_brief,
        "staleness_seconds_since_last_close": staleness_seconds,
        "sessions_index": sessions_index,
        "today_progress": today_progress,
        "phases_index": phases_index,
        "cowork_ledger": list(reversed(cowork_ledger)),  # newest-first
        # ---- v0.3.0 additions ----
        "corpus_state": corpus_state,
        "serializer_warnings": list(_SERIALIZER_WARNINGS),
        "workstreams": _derive_workstreams(repo_root, generated_at),
    }


# --------------------------------------------------------------------------------------
# Shard assembly
# --------------------------------------------------------------------------------------

def assemble_all_shards(
    repo_root: pathlib.Path,
    sessions_index: List[Dict[str, Any]],
    phase_b_plan: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return (session_shards, phase_shards) dicts mapping id→JSON object."""
    backfill = _read_intervention_backfill(repo_root)

    session_shards: Dict[str, Any] = {}
    for row in sessions_index:
        sid = row["session_id"]
        detail = _extract_session_body(repo_root, sid)
        if detail is None:
            detail = {
                "session_id": sid,
                "schema_version": SCHEMA_VERSION,
                "header": {"date": row.get("date"), "title": row.get("title")},
                "session_open": None,
                "session_close": None,
                "body_excerpts": {"objective": None},
                "files_touched": [],
                "deliverables": [],
                "residuals": [],
                "linked_reports": {"drift": None, "schema": None, "mirror": None},
                "halts_encountered": [],
                "native_overrides": [],
                "phase_id": row.get("phase_id"),
                "session_class": row.get("class", "unknown"),
                "previous_session_id": None,
                "next_session_id": None,
                "_note": "legacy entry — structured YAML absent",
            }
        # Merge backfill annotations for sessions that have empty override/halt fields
        if sid in backfill:
            bf = backfill[sid]
            if not detail.get("native_overrides"):
                detail["native_overrides"] = bf.get("native_overrides", [])
            if not detail.get("halts_encountered"):
                detail["halts_encountered"] = bf.get("halts_encountered", [])
            detail["_backfill_applied"] = True
        session_shards[sid] = detail

    # Link next_session_id forward (sessions_index is newest-first; reverse for linking)
    ids = [row["session_id"] for row in reversed(sessions_index)]
    for i, sid in enumerate(ids):
        if i + 1 < len(ids) and sid in session_shards:
            session_shards[sid]["next_session_id"] = ids[i + 1]

    phase_shards: Dict[str, Any] = {}
    phase_ids = list(dict.fromkeys(
        row["phase_id"] for row in sessions_index if row.get("phase_id")
    ))
    for pid in phase_ids:
        phase_shards[pid] = _assemble_phase_detail(pid, sessions_index, phase_b_plan, repo_root)

    return session_shards, phase_shards


# --------------------------------------------------------------------------------------
# Optional GCS upload
# --------------------------------------------------------------------------------------

def _upload_blob(
    client: Any,
    bucket_name: str,
    object_name: str,
    local_path: pathlib.Path,
    cache_max_age: int = 60,
) -> None:
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.cache_control = f"public, max-age={cache_max_age}"
    blob.content_type = "application/json"
    blob.upload_from_filename(str(local_path))
    print(f"[serialize_build_state] Uploaded gs://{bucket_name}/{object_name}", file=sys.stderr)


def _upload_to_gcs(
    local_path: pathlib.Path,
    gs_uri: str,
    session_shards: Optional[Dict[str, Any]] = None,
    phase_shards: Optional[Dict[str, Any]] = None,
    tmp_dir: Optional[pathlib.Path] = None,
) -> None:
    """Upload top-level build-state.json plus optional shards to GCS."""
    if not gs_uri.startswith("gs://"):
        raise ValueError(f"--upload-to-gcs must be a gs:// URI, got: {gs_uri}")
    bucket_name, _, object_name = gs_uri[len("gs://"):].partition("/")
    if not bucket_name or not object_name:
        raise ValueError(f"Invalid gs:// URI (need gs://bucket/object): {gs_uri}")
    try:
        from google.cloud import storage  # type: ignore
    except ImportError:
        print(
            "[serialize_build_state] google-cloud-storage not installed; "
            f"upload skipped. To upload manually:\n  gsutil cp {local_path} {gs_uri}",
            file=sys.stderr,
        )
        raise

    client = storage.Client()

    # Upload top-level
    _upload_blob(client, bucket_name, object_name, local_path, cache_max_age=60)

    if not session_shards and not phase_shards:
        return

    # Write shards to tmp dir and upload
    shard_dir = tmp_dir or pathlib.Path("/tmp/marsys-shards")
    (shard_dir / "sessions").mkdir(parents=True, exist_ok=True)
    (shard_dir / "phases").mkdir(parents=True, exist_ok=True)

    for sid, detail in (session_shards or {}).items():
        f = shard_dir / "sessions" / f"{sid}.json"
        f.write_text(json.dumps(detail, indent=2, default=str) + "\n", encoding="utf-8")
        _upload_blob(client, bucket_name, f"sessions/{sid}.json", f, cache_max_age=300)

    for pid, detail in (phase_shards or {}).items():
        safe_pid = pid.replace(".", "_")
        f = shard_dir / "phases" / f"{pid}.json"
        f.write_text(json.dumps(detail, indent=2, default=str) + "\n", encoding="utf-8")
        _upload_blob(client, bucket_name, f"phases/{pid}.json", f, cache_max_age=120)


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo-root", default=None,
                    help="Project root (e.g. /Users/Dev/Vibe-Coding/Apps/Madhav); "
                         "required unless --version is used")
    ap.add_argument("--session-id", default="unknown",
                    help="Session ID writing this snapshot")
    ap.add_argument("--output", default="build_state.json", help="Local JSON output path")
    ap.add_argument("--upload-to-gcs", default=None,
                    help="gs://bucket/object to upload to (optional)")
    ap.add_argument("--validate-only", action="store_true",
                    help="Assemble + print but do not write")
    ap.add_argument("--validate-against-schema", default=None,
                    help="Path to build_state.schema.json for jsonschema validation")
    ap.add_argument("--red-team-threshold", type=int, default=RED_TEAM_THRESHOLD_DEFAULT)
    ap.add_argument("--recent-n", type=int, default=5)
    ap.add_argument("--trend-n", type=int, default=TREND_WINDOW_DEFAULT,
                    help="Number of governance-report entries to include in trend arrays (default 30)")
    ap.add_argument("--emit-shards", action="store_true",
                    help="Also emit per-session and per-phase JSON shards")
    ap.add_argument("--shard-dir", default=None,
                    help="Directory for shard output (default /tmp/marsys-shards)")
    ap.add_argument("--version", action="store_true",
                    help="Print serializer version and exit")
    args = ap.parse_args()

    if args.version:
        print(GENERATOR_VERSION)
        return 0

    if not args.repo_root:
        print("[serialize_build_state] --repo-root is required", file=sys.stderr)
        return 1

    try:
        repo_root = pathlib.Path(args.repo_root).resolve()
        state = assemble_build_state(
            repo_root=repo_root,
            session_id=args.session_id,
            red_team_threshold=args.red_team_threshold,
            recent_n=args.recent_n,
            trend_n=args.trend_n,
        )
    except FileNotFoundError as e:
        print(f"[serialize_build_state] Source file missing: {e}", file=sys.stderr)
        return 1
    except (ValueError, KeyError) as e:
        print(f"[serialize_build_state] Source unparseable: {e}", file=sys.stderr)
        return 1
    except Exception:
        traceback.print_exc()
        return 4

    # Optional schema validation
    if args.validate_against_schema:
        schema_path = pathlib.Path(args.validate_against_schema)
        try:
            import jsonschema  # type: ignore
        except ImportError:
            print("[serialize_build_state] jsonschema not installed; skipping validation.",
                  file=sys.stderr)
        else:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            try:
                jsonschema.validate(instance=state, schema=schema)
                print("[serialize_build_state] Schema validation PASSED.", file=sys.stderr)
            except jsonschema.ValidationError as ve:
                print(f"[serialize_build_state] Schema validation FAILED: {ve.message}",
                      file=sys.stderr)
                return 2

    if args.validate_only:
        json.dump(state, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0

    # Assemble shards if requested
    session_shards = None
    phase_shards = None
    if args.emit_shards:
        # Use the enriched sub_phases from state (status already set from CURRENT_STATE).
        enriched_phase_b_plan = state.get("phase_plan", {}).get("sub_phases") or _read_phase_b_plan(repo_root)
        session_shards, phase_shards = assemble_all_shards(
            repo_root, state.get("sessions_index", []), enriched_phase_b_plan
        )

    # Write top-level file
    out_path = pathlib.Path(args.output).resolve()
    out_path.write_text(json.dumps(state, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"[serialize_build_state] Wrote {out_path}", file=sys.stderr)

    # Write shards locally if shard-dir specified (without GCS)
    shard_dir = pathlib.Path(args.shard_dir).resolve() if args.shard_dir else None
    if args.emit_shards and shard_dir and not args.upload_to_gcs:
        (shard_dir / "sessions").mkdir(parents=True, exist_ok=True)
        (shard_dir / "phases").mkdir(parents=True, exist_ok=True)
        for sid, detail in (session_shards or {}).items():
            f = shard_dir / "sessions" / f"{sid}.json"
            f.write_text(json.dumps(detail, indent=2, default=str) + "\n", encoding="utf-8")
        for pid, detail in (phase_shards or {}).items():
            f = shard_dir / "phases" / f"{pid}.json"
            f.write_text(json.dumps(detail, indent=2, default=str) + "\n", encoding="utf-8")
        print(f"[serialize_build_state] Wrote shards to {shard_dir}", file=sys.stderr)

    if args.upload_to_gcs:
        try:
            _upload_to_gcs(
                out_path, args.upload_to_gcs,
                session_shards=session_shards,
                phase_shards=phase_shards,
                tmp_dir=shard_dir,
            )
        except Exception as e:
            print(f"[serialize_build_state] GCS upload failed: {e}", file=sys.stderr)
            return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())

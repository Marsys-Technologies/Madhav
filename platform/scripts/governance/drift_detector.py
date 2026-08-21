#!/usr/bin/env python3
"""
drift_detector.py — MARSYS-JIS governance drift detector.

# Implements: GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §H

Runs the eight cross-surface drift checks declared in protocol §H.3:

  H.3.1 — Canonical path table parity (CLAUDE.md ↔ .geminirules ↔ CANONICAL_ARTIFACTS)
  H.3.2 — CANONICAL_ARTIFACTS ↔ filesystem fingerprint match
  H.3.3 — MACRO_PLAN ↔ PHASE_B_PLAN alignment
  H.3.4 — STEP_LEDGER internal consistency (rebuild era only)
  H.3.5 — FILE_REGISTRY ↔ CANONICAL_ARTIFACTS agreement
  H.3.6 — GOVERNANCE_STACK ↔ CANONICAL_ARTIFACTS agreement
  H.3.7 — Phantom-reference scan (live pointers to files that do not exist on disk)
  H.3.8 — Unreferenced canonical-artifact scan

Exit codes (per §H.4):
  0  — no findings
  1  — at least one CRITICAL finding
  2  — at least one HIGH (no CRITICAL)
  3  — only MEDIUM/LOW findings
  4  — script-internal error

Usage:
  python3 platform/scripts/governance/drift_detector.py \
      [--repo-root PATH] [--session-id ID] [--report-path PATH] [--json-path PATH]

The script is a DETECTOR. It NEVER modifies any file it inspects.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import json
import os
import pathlib
import re
import sys
import traceback
from typing import Dict, List, Optional, Set

# Local import
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _ca_loader import CANONICAL_PATH, compute_sha256, load_canonical_artifacts  # noqa: E402

# Feature flag: when true, reads from CAPABILITY_MANIFEST.json instead of CANONICAL_ARTIFACTS.
# Default true (manifest path is production after Phase 1B cutover).
_USE_MANIFEST = os.environ.get("DRIFT_DETECTOR_USE_MANIFEST", "true").lower() in ("true", "1", "yes")


# --------------------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------------------

# Deferred / whitelisted residuals. These are KNOWN drift items booked in STEP_LEDGER
# history (WARN.N) for resolution by a named downstream step. Detector reports them
# but labels them `whitelist_ticket: WARN.N` so they do NOT flip the exit code to 1.
WHITELIST_TICKETS = {
    # STEP_LEDGER Step 5 close — PHASE_B_PLAN §5 / §N.10 live MP v1.0 pointers
    "WARN.2": {
        "description": "PHASE_B_PLAN §5 header + §N.10 live MP v1.0 pointers",
        "files": ["00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md"],
        "booked_for": "PHASE_B_PLAN v1.0.3 amendment cycle",
    },
    # STEP_LEDGER Step 5 close — MARSYS_JIS_BOOTSTRAP_HANDOFF.md line 145 MP v1.0 pointer
    "WARN.4": {
        "description": "MARSYS_JIS_BOOTSTRAP_HANDOFF.md MP v1.0 pointer",
        "files": ["MARSYS_JIS_BOOTSTRAP_HANDOFF.md"],
        "booked_for": "Step 9 CLAUDE.md rebuild cycle",
    },
    # STEP_LEDGER Step 5 close — B0_KICKOFF_PROMPT_FOR_CLAUDE_CODE.md MP v1.0 pointer
    "WARN.5": {
        "description": "B0_KICKOFF_PROMPT_FOR_CLAUDE_CODE.md MP v1.0 pointer",
        "files": ["00_ARCHITECTURE/B0_KICKOFF_PROMPT_FOR_CLAUDE_CODE.md"],
        "booked_for": "PHASE_B_PLAN v1.0.3 amendment cycle",
    },
    # WARN.6 removed 2026-06-16 (chore/governance-repoint): generated 0 findings post-v6.0
    # CLAUDE.md rebuild — 00_ARCHITECTURE/CLAUDE.md helper file exists on disk and the
    # phantom-reference check no longer fires on it.
    # WARN.7 removed 2026-06-16 (chore/governance-repoint): generated 0 findings post-v6.0
    # CLAUDE.md rebuild — 025_HOLISTIC_SYNTHESIS/CLAUDE.md helper file exists on disk and
    # the phantom-reference check no longer fires on it.
    # WARN.8 removed 2026-06-16 (chore/governance-repoint): mirror_enforcer dead code
    # cleared in Phase 1 (chore/legacy-dead-code-kill / Legacy Governance Teardown).
    # Dead basenames (mirror_enforcer.py, .gemini/project_state.md, p6_uvc_consistency.py,
    # rag/ledger.py) moved to _FUTURE_ARTIFACTS to suppress phantom-reference noise while
    # preserving the historical audit trail in governance markdown. Removal verified:
    # drift_detector exits 3 (MEDIUM/LOW only) post-change.
    # GISMCP remediation arc (2026-05-26) modified 5 platform-mcp tool files
    # (tier-gate removal + alias creation + mantras filter fix). The declared
    # fingerprints in CAPABILITY_MANIFEST were not rotated in that arc session.
    # Rotation requires a dedicated governance session to recompute and update
    # all 5 fingerprint_sha256 + last_verified_session fields. Booked for
    # next governance pass (§H, due 2026-07-24).
    "WARN.9": {
        "description": "GISMCP arc fingerprint rotation pending (5 platform-mcp tools modified 2026-05-26)",
        "canonical_ids": [
            "MCP_TOOL_QUERY_DIVISIONAL_CHART",
            "MCP_TOOL_QUERY_REMEDIAL_MANTRAS",
            "MCP_TOOL_CHART_SUMMARY",
            "MCP_TOOL_TOOL_HEALTH",
            "MCP_TOOL_DATA_COVERAGE",
        ],
        "booked_for": "Quarterly governance pass (§H) — rotate fingerprints after GISMCP arc",
    },
    # Brahma infra arc (sessions S774–S784, 2026-06-02/03) modified these governance
    # documents but fingerprints were not rotated in the same session arc. Booked
    # for the next governance pass (§H, due 2026-07-24).
    "WARN.10": {
        "description": "Brahma infra arc fingerprint rotation pending (3 docs modified 2026-06-02/03)",
        "canonical_ids": [
            "INFRA_RECONCILIATION",
            "INFRA_COST_COMPARISON_BRAHMA",
            "CLAUDECODE_BRIEF_BRAHMA_INFRA_PROVISIONING",
        ],
        "booked_for": "Quarterly governance pass (§H) — rotate fingerprints after Brahma infra arc",
    },
}

# Canonical IDs whose fingerprint_mismatch findings carry a whitelist ticket.
# Populated from WHITELIST_TICKETS entries that have a "canonical_ids" key.
_FINGERPRINT_MISMATCH_WHITELIST: dict = {}
for _ticket_id, _ticket in WHITELIST_TICKETS.items():
    for _cid in _ticket.get("canonical_ids", []):
        _FINGERPRINT_MISMATCH_WHITELIST[_cid] = _ticket_id

# Governance surfaces scanned for phantom references. Excludes closed/time-stamped
# artifacts per protocol §H.3.7. STEP_BRIEFS intentionally scanned.
GOVERNANCE_SURFACES_GLOBS = [
    "CLAUDE.md",
    # .geminirules + .gemini/project_state.md retired 2026-05-27 (ND.1 close-out)
    "00_ARCHITECTURE/MACRO_PLAN_v2_0.md",
    # F-94/RC-2: PHASE_B_PLAN_v1_0.md removed from the LIVE-pointer scan 2026-08-21.
    # Its own frontmatter reads `status: SUPERSEDED` (M2 closed 2026-05-01, CLAUDE.md §E),
    # so by this list's own stated exclusion rule ("excludes closed/time-stamped
    # artifacts") it does not belong here. It produced 51 of 215 findings — every one a
    # backtick pointer to a `python-sidecar/rag/*` file deleted in the WS-0C legacy
    # purge, i.e. an accurate description of the M2-era tree the plan documents. The
    # emitted remediation ("resolve at PHASE_B_PLAN v1.0.3 amendment cycle") named an
    # amendment cycle that cannot occur for a superseded plan, and acting on it would
    # rewrite an archived record in violation of ONGOING_HYGIENE_POLICIES §A
    # (archival retain-in-place). §H.3.3 check_mp_pbp_alignment still reads this file;
    # only the §H.3.7 live-pointer scan is scoped off it. WARN.2 is retained in
    # WHITELIST_TICKETS as audit trail and is now expected to match nothing.
    "00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md",
    "00_ARCHITECTURE/FILE_REGISTRY_v1_14.md",
    "00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md",
    "00_ARCHITECTURE/STEP_LEDGER_v1_0.md",
    "00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md",
    "00_ARCHITECTURE/CONVERSATION_NAMING_CONVENTION_v1_0.md",
    "00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md",
    "00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md",
    "00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md",
    "00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md",
    "00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md",
]

# Regex for `backtick-quoted paths` inside the governance surfaces.
# Matches .md / .py / .yaml / .json / directory-trailing paths inside backticks.
_BT_PATH_RE = re.compile(
    r"`([A-Za-z0-9_./\-]+?\.(?:md|py|yaml|yml|json|csv|docx|ts|tsx|jsx|js|html|txt|sh|pptx|xlsx))`"
)


# --------------------------------------------------------------------------------------
# Finding model
# --------------------------------------------------------------------------------------

@dataclasses.dataclass
class Finding:
    cls: str
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    canonical_id: Optional[str]
    surfaces_involved: List[str]
    evidence: str
    suggested_remediation: str
    whitelist_ticket: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "class": self.cls,
            "severity": self.severity,
            "canonical_id": self.canonical_id,
            "surfaces_involved": self.surfaces_involved,
            "evidence": self.evidence,
            "suggested_remediation": self.suggested_remediation,
            "whitelist_ticket": self.whitelist_ticket,
        }


def _is_whitelisted(path_rel: str) -> Optional[str]:
    """Return the WARN ticket ID if path is whitelisted; else None."""
    for ticket, data in WHITELIST_TICKETS.items():
        if path_rel in data.get("files", []):
            return ticket
    return None


# --------------------------------------------------------------------------------------
# Individual checks (§H.3.1 – §H.3.8)
# --------------------------------------------------------------------------------------

def check_canonical_path_parity(repo_root: pathlib.Path, ca) -> List[Finding]:
    """§H.3.1 — CLAUDE.md / CANONICAL_ARTIFACTS canonical-path parity.

    Note: .geminirules mirror leg retired 2026-05-27 per ND.1 close-out.
    """
    findings: List[Finding] = []
    claude_path = (repo_root / "CLAUDE.md").read_text(encoding="utf-8")

    # Mapping from canonical_id → expected path token the script looks for.
    # Only IDs that are meant to be surfaced in CLAUDE.md are checked.
    surfaced = {
        "MSR": "025_HOLISTIC_SYNTHESIS/MSR_v5_0.md",
        "UCN": "025_HOLISTIC_SYNTHESIS/UCN_v4_0.md",
        "CDLM": "025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md",
        "CGM": "025_HOLISTIC_SYNTHESIS/CGM_v9_0.md",
        "RM": "025_HOLISTIC_SYNTHESIS/RM_v2_0.md",
        "PROJECT_ARCHITECTURE": "00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md",
        "MACRO_PLAN": "00_ARCHITECTURE/MACRO_PLAN_v2_0.md",
        "PHASE_B_PLAN": "00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md",
    }

    for cid, expected in surfaced.items():
        if cid not in ca.artifacts:
            continue
        ca_path_value = ca.artifacts[cid].get("path", "")
        if ca_path_value != expected:
            findings.append(Finding(
                cls="canonical_path_disagreement",
                severity="HIGH",
                canonical_id=cid,
                surfaces_involved=["CANONICAL_ARTIFACTS", "(this script's expected map)"],
                evidence=f"CANONICAL_ARTIFACTS path='{ca_path_value}'; expected='{expected}'",
                suggested_remediation="Update CANONICAL_ARTIFACTS §1 row OR this script's `surfaced` map",
            ))
        # CLAUDE.md's L2.5 / MP / PBP / architecture pointers
        if cid in {"MSR", "UCN", "CDLM", "CGM", "RM", "PROJECT_ARCHITECTURE", "MACRO_PLAN", "PHASE_B_PLAN"}:
            if expected not in claude_path:
                findings.append(Finding(
                    cls="canonical_path_disagreement",
                    severity="HIGH",
                    canonical_id=cid,
                    surfaces_involved=["CLAUDE.md", "CANONICAL_ARTIFACTS"],
                    evidence=f"CLAUDE.md does not cite '{expected}'",
                    suggested_remediation="Step 9 CLAUDE.md rebuild will replace the canonical-path table with a cite-CANONICAL_ARTIFACTS-by-reference rule",
                ))
    return findings


def check_ca_filesystem_fingerprints(repo_root: pathlib.Path, ca) -> List[Finding]:
    """§H.3.2 — CANONICAL_ARTIFACTS declared fingerprints vs filesystem."""
    findings: List[Finding] = []
    for cid, row in ca.artifacts.items():
        declared = row.get("fingerprint_sha256") or ""
        # Self-entry fingerprint is "<populated-at-step-7-close>" at bootstrap;
        # skip as LOW informational until Step 7's session-close fingerprint pass.
        if declared.startswith("<populated"):
            findings.append(Finding(
                cls="fingerprint_bootstrap_placeholder",
                severity="LOW",
                canonical_id=cid,
                surfaces_involved=[row.get("path", "")],
                evidence=f"declared_fingerprint='{declared}' (bootstrap placeholder)",
                suggested_remediation="Session-close populates real fingerprint at Step 7 close",
            ))
            continue
        path_rel = row.get("path")
        if not path_rel:
            continue
        # Skip files pending L0 rebuild — acknowledged as forthcoming in
        # _FUTURE_ARTIFACTS. Computing a fingerprint on an absent-but-expected
        # file produces a false CRITICAL; honour the same allowlist used by
        # check_phantom_references().
        if pathlib.Path(path_rel).name in _FUTURE_ARTIFACTS:
            continue
        path_abs = repo_root / path_rel
        if path_abs.is_dir():
            findings.append(Finding(
                cls="directory_entry_skipped",
                severity="LOW",
                canonical_id=cid,
                surfaces_involved=[path_rel],
                evidence=f"path '{path_rel}' resolves to a directory; fingerprint check skipped (representations includes 'folder')",
                suggested_remediation="Directory entries are intentional folder registrations in the manifest; no action needed",
            ))
            continue
        observed = compute_sha256(path_abs)
        if observed is None:
            findings.append(Finding(
                cls="phantom_reference",
                severity="CRITICAL",
                canonical_id=cid,
                surfaces_involved=["CANONICAL_ARTIFACTS", path_rel],
                evidence=f"CANONICAL_ARTIFACTS row for {cid} points at {path_rel} which does not exist",
                suggested_remediation="Either restore the file or remove the CANONICAL_ARTIFACTS row",
            ))
        elif observed != declared:
            findings.append(Finding(
                cls="fingerprint_mismatch",
                severity="HIGH",
                canonical_id=cid,
                surfaces_involved=[path_rel, "CANONICAL_ARTIFACTS"],
                evidence=f"declared={declared} observed={observed}",
                suggested_remediation="Rotate the row's fingerprint_sha256 AND update last_verified_session/last_verified_on",
                whitelist_ticket=_FINGERPRINT_MISMATCH_WHITELIST.get(cid),
            ))
    return findings


def check_mp_pbp_alignment(repo_root: pathlib.Path) -> List[Finding]:
    """§H.3.3 — MACRO_PLAN vs PHASE_B_PLAN alignment + MP-version-cite check."""
    findings: List[Finding] = []
    pbp_path = repo_root / "00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md"
    if not pbp_path.exists():
        findings.append(Finding(
            cls="phantom_reference",
            severity="CRITICAL",
            canonical_id="PHASE_B_PLAN",
            surfaces_involved=["00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md"],
            evidence="PHASE_B_PLAN_v1_0.md not found",
            suggested_remediation="Restore the file or revise CANONICAL_ARTIFACTS",
        ))
        return findings
    pbp = pbp_path.read_text(encoding="utf-8")
    # Live MP v1.0 pointer → WARN.2 whitelist
    if "MACRO_PLAN_v1_0.md" in pbp:
        findings.append(Finding(
            cls="macro_plan_phase_plan_drift",
            severity="MEDIUM",
            canonical_id="PHASE_B_PLAN",
            surfaces_involved=["00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md", "00_ARCHITECTURE/MACRO_PLAN_v2_0.md"],
            evidence="PHASE_B_PLAN contains live pointer to superseded MACRO_PLAN_v1_0.md",
            suggested_remediation="PHASE_B_PLAN v1.0.3 amendment cycle",
            whitelist_ticket="WARN.2",
        ))
    return findings


def check_step_ledger_consistency(repo_root: pathlib.Path) -> List[Finding]:
    """§H.3.4 — STEP_LEDGER internal consistency (rebuild era)."""
    findings: List[Finding] = []
    ledger_path = repo_root / "00_ARCHITECTURE/STEP_LEDGER_v1_0.md"
    if not ledger_path.exists():
        findings.append(Finding(
            cls="step_ledger_violation",
            severity="CRITICAL",
            canonical_id="STEP_LEDGER",
            surfaces_involved=["00_ARCHITECTURE/STEP_LEDGER_v1_0.md"],
            evidence="STEP_LEDGER file missing",
            suggested_remediation="Restore STEP_LEDGER",
        ))
        return findings
    text = ledger_path.read_text(encoding="utf-8")
    # Count `in_progress` occurrences inside the table rows (each row starts `| NN | ...`).
    table_rows = [line for line in text.splitlines() if re.match(r"^\|\s*\d+[A-Z]?\s*\|", line)]
    in_progress = sum(1 for r in table_rows if "in_progress" in r.lower())
    if in_progress > 1:
        findings.append(Finding(
            cls="step_ledger_violation",
            severity="CRITICAL",
            canonical_id="STEP_LEDGER",
            surfaces_involved=["00_ARCHITECTURE/STEP_LEDGER_v1_0.md"],
            evidence=f"{in_progress} rows marked `in_progress` (expected 0 or 1)",
            suggested_remediation="Close all but one in_progress row",
        ))
    return findings


def check_file_registry_agreement(repo_root: pathlib.Path, ca) -> List[Finding]:
    """§H.3.5 — FILE_REGISTRY vs CANONICAL_ARTIFACTS agreement on CURRENT rows."""
    findings: List[Finding] = []
    fr_path = repo_root / "00_ARCHITECTURE/FILE_REGISTRY_v1_14.md"
    if not fr_path.exists():
        # Fall back to earlier versions if v1.14 not yet present
        for ver in ("v1_13", "v1_12", "v1_11", "v1_3", "v1_2"):
            candidate = repo_root / f"00_ARCHITECTURE/FILE_REGISTRY_{ver}.md"
            if candidate.exists():
                fr_path = candidate
                break
    if not fr_path.exists():
        findings.append(Finding(
            cls="registry_disagreement",
            severity="CRITICAL",
            canonical_id="FILE_REGISTRY",
            surfaces_involved=["00_ARCHITECTURE/"],
            evidence="No FILE_REGISTRY found (v1.2 or v1.3)",
            suggested_remediation="Publish FILE_REGISTRY_v1_3 per protocol §D.2",
        ))
        return findings
    fr_text = fr_path.read_text(encoding="utf-8")
    for cid, row in ca.artifacts.items():
        path_rel = row.get("path", "")
        if not path_rel:
            continue
        basename = pathlib.Path(path_rel).name
        # A minimal heuristic: if CANONICAL_ARTIFACTS names a file as CURRENT, its
        # basename must appear in FILE_REGISTRY. We don't try to parse FILE_REGISTRY's
        # table; we check basename presence.
        if basename not in fr_text:
            # Exclude rolling / LIVE surfaces that don't have a per-version row
            if row.get("status") in ("LIVE", "LIVING") and cid in ("SESSION_LOG",):
                continue
            findings.append(Finding(
                cls="registry_disagreement",
                severity="MEDIUM",
                canonical_id=cid,
                surfaces_involved=[str(fr_path.relative_to(repo_root)), "CANONICAL_ARTIFACTS"],
                evidence=f"FILE_REGISTRY does not name '{basename}'",
                suggested_remediation=f"Add a row for {basename} in FILE_REGISTRY",
            ))
    return findings


def check_governance_stack_agreement(repo_root: pathlib.Path, ca) -> List[Finding]:
    """§H.3.6 — GOVERNANCE_STACK ↔ CANONICAL_ARTIFACTS agreement."""
    findings: List[Finding] = []
    gs_path = repo_root / "00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md"
    if not gs_path.exists():
        findings.append(Finding(
            cls="governance_stack_disagreement",
            severity="CRITICAL",
            canonical_id="GOVERNANCE_STACK",
            surfaces_involved=["00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md"],
            evidence="GOVERNANCE_STACK file missing",
            suggested_remediation="Restore GOVERNANCE_STACK",
        ))
        return findings
    gs_text = gs_path.read_text(encoding="utf-8")
    # Mirror check for core canonical artifacts only.
    for cid in ("MSR", "UCN", "CDLM", "CGM", "RM", "FORENSIC", "LEL", "MACRO_PLAN",
                "PHASE_B_PLAN", "PROJECT_ARCHITECTURE", "FILE_REGISTRY"):
        if cid not in ca.artifacts:
            continue
        row = ca.artifacts[cid]
        basename = pathlib.Path(row.get("path", "")).name
        if basename and basename.split(".")[0].upper() not in gs_text.upper():
            findings.append(Finding(
                cls="governance_stack_disagreement",
                severity="MEDIUM",
                canonical_id=cid,
                surfaces_involved=["00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md", "CANONICAL_ARTIFACTS"],
                evidence=f"GOVERNANCE_STACK does not name '{basename}'",
                suggested_remediation=f"Add {basename} to GOVERNANCE_STACK §1 version registry",
            ))
    return findings


_FUTURE_ARTIFACTS = {
    # Explicitly named future-artifact basenames that any governance surface may forward-
    # reference without drift being a defect. These are typically named by protocol + MP +
    # architecture as "forthcoming" or "will become ..." artifacts.
    "GOVERNANCE_BASELINE_v1_0.md",           # Step 15 deliverable
    "CURRENT_STATE_v1_0.md",                 # Step 10 deliverable
    "CGM_v9_0.md",                           # after Phase B.3.5
    "SESSION_LOG_SCHEMA_v1_0.md",            # Step 10 deliverable
    "LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md",  # Step 11 deliverable
    "ONGOING_HYGIENE_POLICIES_v1_0.md",      # Step 12 deliverable
    "DRIFT_REPORT_STEP_13_v1_0.md",          # Step 13 deliverable
    "SCHEMA_VALIDATION_REPORT_STEP_14_v1_0.md",  # Step 14 deliverable
    "GOVERNANCE_INTEGRITY_REDTEAM_v1_0.md",  # Step 8 deliverable
    # L4 Discovery Layer registers (M2 Phase B deliverables)
    "PATTERN_REGISTER_v1_0.md",
    "RESONANCE_REGISTER_v1_0.md",
    "CONTRADICTION_REGISTER_v1_0.md",
    "CLUSTER_ATLAS_v1_0.md",
    "PATTERN_TAXONOMY_v1_0.md",
    "RESONANCE_TAXONOMY_v1_0.md",
    "LEL_ENTRY_TEMPLATE_v1_0.md",
    "PROSPECTIVE_PREDICTION_LOG_v1_0.md",
    # Historical plan reference — retained deliberately in .gemini/project_state.md's
    # "Resolution of GA.7" block per protocol §K arbitration-trace discipline.
    "twinkly-puzzling-quokka.md",
    # Pre-rebuild architecture + L1 lineage references cited in PROJECT_ARCHITECTURE_v2_2
    # §A.4.addendum (drift-rationale discussion) and §E (historical tree). These are
    # legitimate historical-context references, not live pointers. The v1.0 detector
    # cannot distinguish lineage-discussion context from live-pointer context; that
    # refinement is booked for Step 12 ongoing-hygiene policies.
    "PROJECT_ARCHITECTURE_v2_0.md",
    "FORENSIC_DATA_v7_0.md",       # pre-v8.0 supplement (v7.0 integrated into v8.0)
    "LIFE_EVENT_LOG_v1_0.md",      # pre-v1.2 LEL
    "DEEP_ANALYSIS_v2_0.md",       # pre-MATRIX_*.md consolidated analysis
    "EXTERNAL_COMPUTATION_SPEC.md", # un-versioned cite of the v2.0 spec
    # Layer-0 teardown (PR #187, 2026-06-02) removed these files as part of the
    # clean-slate rebuild. CLAUDE.md references them as forthcoming L1/tool artefacts.
    # Re-enable check when each file is re-authored in the Build-Guarantor arc.
    "FORENSIC_ASTROLOGICAL_DATA_v8_0.md",  # L1 canonical fact layer — pending L0 rebuild
    "bootstrap_panchanga.py",               # panchang bootstrap script — pending L1 rebuild
    "tool_health.ts",                       # MCP ops tool — pending L2 rebuild
    "data_coverage.ts",                     # MCP ops tool — pending L2 rebuild
    # L0FR legacy-purge (WS-0C, 2026-06-05) removed these files; forward-
    # referenced in CLAUDE.md §E and FILE_REGISTRY_v1_14. Pending L0 rebuild.
    "msr_grounding.integration.test.ts",    # MSR grounding integration test — pending L0 rebuild
    "rag_router.py",                        # RAG router — pending L0 rebuild
    # python-sidecar/rag/ module files deleted in WS-0C; referenced in FILE_REGISTRY_v1_14.
    # Generic basenames (schemas.py, router.py) exist in local .venv packages — excluded from
    # _build_basename_cache skip_dirs previously, causing local hits that CI (no .venv) lacks.
    # Pending L0 rebuild of the rag module.
    "schemas.py",                           # rag schemas module — pending L0 rebuild
    "router.py",                            # rag router module — pending L0 rebuild
    # Gemini mirror retirement (ND.1 close-out 2026-05-27) — these files were deleted when
    # the mirror discipline was retired. Governance markdown (STEP_LEDGER, GOVERNANCE_INTEGRITY_PROTOCOL,
    # etc.) retains historical backtick references as audit trail; suppress phantom-reference
    # noise without removing the historical evidence. WARN.8 whitelist entry removed 2026-06-16.
    "mirror_enforcer.py",                   # Gemini mirror enforcer — retired ND.1 close-out
    "project_state.md",                     # .gemini/project_state.md — retired ND.1 close-out
    # p6_uvc_consistency.py and rag/ledger.py appear in STEP_LEDGER historical audit entries;
    # never re-introduced; suppress phantom noise without touching historical record.
    "p6_uvc_consistency.py",                # historical STEP_LEDGER reference — never re-introduced
    "ledger.py",                            # rag/ledger.py historical reference — pending L0 rebuild
}

# Regex for template/example path placeholders (vX_Y, vN_N, etc.)
_TEMPLATE_PATH_RE = re.compile(r"_v[A-Z]_[A-Z](?:\.|_)|_vX_Y")

# Repo-wide basename cache (populated once per run).
_BASENAME_CACHE: Optional[Dict[str, List[pathlib.Path]]] = None


def _build_basename_cache(repo_root: pathlib.Path) -> Dict[str, List[pathlib.Path]]:
    global _BASENAME_CACHE
    if _BASENAME_CACHE is not None:
        return _BASENAME_CACHE
    cache: Dict[str, List[pathlib.Path]] = {}
    # Walk the repo, skipping heavy node_modules + .git + hidden caches.
    # venv/.venv excluded: local Python virtualenvs contain package files (router.py,
    # schemas.py, etc.) with generic basenames that would silently satisfy governance
    # phantom-reference checks — producing local hits that CI (no venv) cannot replicate.
    #
    # F-94/RC-3: skip_dirs MUST be matched against the path RELATIVE to repo_root, never
    # against `p.parts` (which, when repo_root is absolute, includes every component of
    # the checkout's own filesystem location). A checkout living under any directory
    # named `.claude`, `venv`, `node_modules`, … made EVERY walked file match a skip_dir,
    # emptying the cache and turning every backticked pointer into a phantom: measured
    # 825 findings / exit=2 (571 spurious HIGH) versus 215 / exit=3 for the identical
    # tree walked with a relative repo_root. A governance gate whose verdict depends on
    # where the repo happens to be checked out is not measuring what it claims to
    # measure (CLAUDE.md §N.8).
    skip_dirs = {"node_modules", ".git", "__pycache__", ".next", ".turbo", ".claude", "venv", ".venv"}
    for p in repo_root.rglob("*"):
        if p.is_file():
            try:
                rel_parts = p.relative_to(repo_root).parts
            except ValueError:  # pragma: no cover — rglob results are always under root
                rel_parts = p.parts
            if any(part in skip_dirs for part in rel_parts):
                continue
            cache.setdefault(p.name, []).append(p)
    _BASENAME_CACHE = cache
    return cache


def check_phantom_references(repo_root: pathlib.Path) -> List[Finding]:
    """§H.3.7 — Phantom-reference scan across governance surfaces."""
    findings: List[Finding] = []
    cache = _build_basename_cache(repo_root)
    for surface_rel in GOVERNANCE_SURFACES_GLOBS:
        surface_abs = repo_root / surface_rel
        if not surface_abs.exists():
            continue
        text = surface_abs.read_text(encoding="utf-8", errors="replace")
        for m in _BT_PATH_RE.finditer(text):
            ptr = m.group(1)
            if ptr.startswith("http"):
                continue
            basename = pathlib.Path(ptr).name
            # (a) Try the pointer as-is relative to repo_root
            target = repo_root / ptr
            if target.exists():
                continue
            # (b) Try basename search across the repo
            if basename in cache and cache[basename]:
                continue
            # (c) Whitelisted future artifacts
            if basename in _FUTURE_ARTIFACTS:
                continue
            # (d) Template/example path placeholders (`vX_Y` etc.)
            if _TEMPLATE_PATH_RE.search(ptr):
                continue
            # (e) Known future-directory prefixes (deliverables for later macro phases)
            if any(ptr.startswith(prefix) for prefix in (
                "07_PROSPECTIVE_TESTING/",
                "06_LEARNING_LAYER/",
                "08_L4_DISCOVERY_LAYER/",
            )):
                continue
            # (f) Bare version fragments (e.g., `v1_2.md` in "...FILE_REGISTRY_v1_1.md → v1_2.md")
            if re.fullmatch(r"v\d+_\d+\.md", basename):
                continue
            # (g) Protocol spec naming-drift: protocol §F.1/§G.1/§M.1 reference the templates
            #     without the `_v1_0` suffix (e.g., `SESSION_OPEN_TEMPLATE.md`). Deliverables
            #     are named per Step 7 brief §3.A WITH the suffix; this divergence is booked
            #     for protocol v1.X correction at Step 8 red-team / Step 9.
            if basename in ("SESSION_OPEN_TEMPLATE.md", "SESSION_CLOSE_TEMPLATE.md",
                            "DISAGREEMENT_REGISTER.md"):
                continue
            ticket = _is_whitelisted(surface_rel)
            findings.append(Finding(
                cls="phantom_reference",
                severity="MEDIUM" if ticket else "HIGH",
                canonical_id=None,
                surfaces_involved=[surface_rel, ptr],
                evidence=f"Live pointer `{ptr}` in {surface_rel} does not resolve (neither relative to repo nor by basename search)",
                suggested_remediation=("Whitelist or resolve at " + WHITELIST_TICKETS[ticket]["booked_for"]) if ticket else "Fix the pointer, add to _FUTURE_ARTIFACTS if forward-ref, or remove the reference",
                whitelist_ticket=ticket,
            ))
    return findings


def check_chart_facts_schema(repo_root: pathlib.Path) -> List[Finding]:
    """B-10 — CHART_FACTS_SCHEMA.json column presence verification.

    Loads platform/scripts/governance/CHART_FACTS_SCHEMA.json and verifies
    every declared column is present in the actual chart_facts table via psql.
    Skips gracefully if DB is not reachable or psql is unavailable (LOW finding).
    """
    import subprocess
    import shutil

    findings: List[Finding] = []
    schema_path = repo_root / "platform/scripts/governance/CHART_FACTS_SCHEMA.json"

    if not schema_path.exists():
        findings.append(Finding(
            cls="schema_file_missing",
            severity="HIGH",
            canonical_id=None,
            surfaces_involved=["platform/scripts/governance/CHART_FACTS_SCHEMA.json"],
            evidence="CHART_FACTS_SCHEMA.json not found — B-10 schema governance artifact missing",
            suggested_remediation="Run B-10 session to create CHART_FACTS_SCHEMA.json",
        ))
        return findings

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:
        findings.append(Finding(
            cls="schema_file_invalid",
            severity="HIGH",
            canonical_id=None,
            surfaces_involved=["platform/scripts/governance/CHART_FACTS_SCHEMA.json"],
            evidence=f"Could not parse CHART_FACTS_SCHEMA.json: {exc}",
            suggested_remediation="Repair the JSON file",
        ))
        return findings

    declared_columns = {col["name"] for col in schema.get("columns", [])}
    if not declared_columns:
        findings.append(Finding(
            cls="schema_file_empty",
            severity="MEDIUM",
            canonical_id=None,
            surfaces_involved=["platform/scripts/governance/CHART_FACTS_SCHEMA.json"],
            evidence="CHART_FACTS_SCHEMA.json has no columns declared",
            suggested_remediation="Populate the columns array",
        ))
        return findings

    # Try to reach the DB via psql. Honour standard PG env vars.
    if not shutil.which("psql"):
        findings.append(Finding(
            cls="schema_db_unreachable",
            severity="LOW",
            canonical_id=None,
            surfaces_involved=["platform/scripts/governance/CHART_FACTS_SCHEMA.json"],
            evidence="psql not found on PATH — skipping live column verification",
            suggested_remediation="Install postgresql-client to enable live schema checks",
        ))
        return findings

    pg_host = os.environ.get("PGHOST", "127.0.0.1")
    pg_port = os.environ.get("PGPORT", "5433")
    pg_user = os.environ.get("PGUSER", "amjis_app")
    pg_db = os.environ.get("PGDATABASE", "amjis")
    pg_password = os.environ.get("PGPASSWORD", "")

    query = (
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='chart_facts';"
    )
    env = {**os.environ, "PGPASSWORD": pg_password}
    try:
        result = subprocess.run(
            ["psql", "-h", pg_host, "-p", pg_port, "-U", pg_user, "-d", pg_db,
             "-t", "-c", query],
            capture_output=True, text=True, timeout=10, env=env,
        )
        if result.returncode != 0:
            findings.append(Finding(
                cls="schema_db_unreachable",
                severity="LOW",
                canonical_id=None,
                surfaces_involved=["platform/scripts/governance/CHART_FACTS_SCHEMA.json"],
                evidence=f"psql exit {result.returncode}: {result.stderr.strip()[:200]}",
                suggested_remediation="Ensure DB is running on PGHOST:PGPORT for live schema checks",
            ))
            return findings
        live_columns = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    except Exception as exc:
        findings.append(Finding(
            cls="schema_db_unreachable",
            severity="LOW",
            canonical_id=None,
            surfaces_involved=["platform/scripts/governance/CHART_FACTS_SCHEMA.json"],
            evidence=f"psql invocation failed: {exc}",
            suggested_remediation="Check DB connectivity and PGPASSWORD env var",
        ))
        return findings

    missing = declared_columns - live_columns
    if missing:
        for col in sorted(missing):
            findings.append(Finding(
                cls="chart_facts_column_missing",
                severity="HIGH",
                canonical_id=None,
                surfaces_involved=["platform/scripts/governance/CHART_FACTS_SCHEMA.json", "chart_facts"],
                evidence=f"Column '{col}' declared in CHART_FACTS_SCHEMA.json but absent from live chart_facts table",
                suggested_remediation=f"Run the migration that adds '{col}' to chart_facts, or remove it from CHART_FACTS_SCHEMA.json if intentionally dropped",
            ))
    else:
        # All declared columns present — also check the two key B-series columns explicitly
        for required in ("ayanamsha_id", "engine_version", "computed_at_iso", "chart_id", "fact_id"):
            if required not in live_columns:
                findings.append(Finding(
                    cls="chart_facts_column_missing",
                    severity="HIGH",
                    canonical_id=None,
                    surfaces_involved=["chart_facts"],
                    evidence=f"Required B-series column '{required}' missing from live chart_facts table",
                    suggested_remediation=f"Apply the B-series migration that adds '{required}'",
                ))

    return findings


def check_a3_schema_compliance(conn) -> dict:
    """A3 schema compliance check.

    Checks chart_facts rows for:
    - verification_pass_status values outside the declared enum
    - missing citation_ref (empty string or NULL)
    - presence of 12 A3 materialized views in pg_matviews

    Hard violation (exits 3): any row with an invalid verification_pass_status.
    Soft findings: missing citation_ref, missing MVs (logged only).

    Returns a summary dict with counts.
    """
    VALID_STATUS = {'single', 'two_pass_verified', 'classical_match', 'divergent_flagged'}
    MV_NAMES = [
        "mv_lagna_facts",
        "mv_planet_dignity_facts",
        "mv_dasha_active_facts",
        "mv_yoga_facts",
        "mv_ashtakavarga_facts",
        "mv_shadbala_facts",
        "mv_divisional_facts",
        "mv_transit_facts",
        "mv_kp_facts",
        "mv_upagraha_facts",
        "mv_tajaka_facts",
        "mv_synthesis_facts",
    ]

    summary: dict = {
        "bad_verification_status_count": 0,
        "missing_citation_ref_count": 0,
        "missing_mvs": [],
        "hard_violation": False,
    }

    try:
        cur = conn.cursor()

        # Check invalid verification_pass_status values
        placeholders = ",".join(["'%s'" % s for s in VALID_STATUS])
        cur.execute(
            "SELECT COUNT(*) FROM chart_facts "
            "WHERE verification_pass_status IS NOT NULL "
            "AND verification_pass_status NOT IN ('single','two_pass_verified','classical_match','divergent_flagged')"
        )
        row = cur.fetchone()
        bad_count = row[0] if row else 0
        summary["bad_verification_status_count"] = bad_count
        if bad_count > 0:
            summary["hard_violation"] = True

        # Check missing citation_ref
        cur.execute(
            "SELECT COUNT(*) FROM chart_facts "
            "WHERE citation_ref IS NULL OR citation_ref = ''"
        )
        row = cur.fetchone()
        summary["missing_citation_ref_count"] = row[0] if row else 0

        # Check MV presence
        cur.execute(
            "SELECT matviewname FROM pg_matviews WHERE schemaname = 'public'"
        )
        existing_mvs = {r[0] for r in cur.fetchall()}
        summary["missing_mvs"] = [mv for mv in MV_NAMES if mv not in existing_mvs]

        cur.close()
    except Exception as exc:
        summary["error"] = str(exc)

    return summary


def check_a3_categories_and_mvs(repo_root: pathlib.Path) -> List[Finding]:
    """A3-S7 — Verify A3 schema enforcement via psql.

    1. Verifies verification_pass_status values match the declared enum.
    2. Verifies 12 A3 MVs exist in pg_matviews.
    3. Verifies declared CHART_FACTS_SCHEMA.json categories are present (soft).

    Skips gracefully (LOW) if DB is unreachable or psql is absent.
    """
    import subprocess
    import shutil

    findings: List[Finding] = []
    schema_path = repo_root / "platform/scripts/governance/CHART_FACTS_SCHEMA.json"

    MV_NAMES = [
        "mv_lagna_facts",
        "mv_planet_dignity_facts",
        "mv_dasha_active_facts",
        "mv_yoga_facts",
        "mv_ashtakavarga_facts",
        "mv_shadbala_facts",
        "mv_divisional_facts",
        "mv_transit_facts",
        "mv_kp_facts",
        "mv_upagraha_facts",
        "mv_tajaka_facts",
        "mv_synthesis_facts",
    ]

    if not shutil.which("psql"):
        findings.append(Finding(
            cls="a3_schema_db_unreachable",
            severity="LOW",
            canonical_id=None,
            surfaces_involved=["chart_facts"],
            evidence="psql not found on PATH — skipping A3 schema compliance checks",
            suggested_remediation="Install postgresql-client for live A3 schema checks",
        ))
        return findings

    pg_host = os.environ.get("PGHOST", "127.0.0.1")
    pg_port = os.environ.get("PGPORT", "5433")
    pg_user = os.environ.get("PGUSER", "amjis_app")
    pg_db = os.environ.get("PGDATABASE", "amjis")
    pg_password = os.environ.get("PGPASSWORD", "")
    env = {**os.environ, "PGPASSWORD": pg_password}

    def _run_query(query: str):
        try:
            result = subprocess.run(
                ["psql", "-h", pg_host, "-p", pg_port, "-U", pg_user, "-d", pg_db,
                 "-t", "-c", query],
                capture_output=True, text=True, timeout=10, env=env,
            )
            if result.returncode != 0:
                return None, result.stderr.strip()[:200]
            return result.stdout, None
        except Exception as exc:
            return None, str(exc)

    # 1. Check invalid verification_pass_status
    out, err = _run_query(
        "SELECT COUNT(*) FROM chart_facts "
        "WHERE verification_pass_status IS NOT NULL "
        "AND verification_pass_status NOT IN "
        "('single','two_pass_verified','classical_match','divergent_flagged');"
    )
    if err:
        findings.append(Finding(
            cls="a3_schema_db_unreachable",
            severity="LOW",
            canonical_id=None,
            surfaces_involved=["chart_facts"],
            evidence=f"DB query failed: {err}",
            suggested_remediation="Ensure DB is running on PGHOST:PGPORT",
        ))
        return findings
    bad_count = int(out.strip()) if out and out.strip().isdigit() else 0
    if bad_count > 0:
        findings.append(Finding(
            cls="a3_invalid_verification_status",
            severity="HIGH",
            canonical_id=None,
            surfaces_involved=["chart_facts"],
            evidence=f"{bad_count} chart_facts row(s) have verification_pass_status outside the declared enum",
            suggested_remediation="Fix or migrate rows to use: single, two_pass_verified, classical_match, divergent_flagged",
        ))

    # 2. Check 12 MVs exist
    out, err = _run_query(
        "SELECT matviewname FROM pg_matviews WHERE schemaname = 'public';"
    )
    if out is not None:
        existing_mvs = {line.strip() for line in out.splitlines() if line.strip()}
        missing_mvs = [mv for mv in MV_NAMES if mv not in existing_mvs]
        if missing_mvs:
            findings.append(Finding(
                cls="a3_materialized_views_missing",
                severity="HIGH",
                canonical_id=None,
                surfaces_involved=["pg_matviews"],
                evidence=f"Missing A3 MVs: {', '.join(missing_mvs)}",
                suggested_remediation="Apply migration 138_mvs.sql to create the 12 A3 materialized views",
            ))

    # 3. Soft check: declared categories presence (LOW)
    if schema_path.exists():
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            declared_categories = list(schema.get("categories", {}).keys())
            if declared_categories:
                out, err = _run_query(
                    "SELECT DISTINCT fact_category FROM chart_facts WHERE fact_category IS NOT NULL;"
                )
                if out is not None:
                    present_cats = {line.strip() for line in out.splitlines() if line.strip()}
                    missing_cats = [c for c in declared_categories if c not in present_cats]
                    if missing_cats:
                        findings.append(Finding(
                            cls="a3_category_not_yet_populated",
                            severity="LOW",
                            canonical_id=None,
                            surfaces_involved=["chart_facts", "CHART_FACTS_SCHEMA.json"],
                            evidence=f"{len(missing_cats)} CHART_FACTS_SCHEMA.json categories not yet in DB (pending writers): {', '.join(missing_cats[:5])}{'...' if len(missing_cats) > 5 else ''}",
                            suggested_remediation="Run the writer for each pending category; this is a soft check — writers are expected to be added incrementally",
                        ))
        except Exception:
            pass

    return findings


def check_unreferenced_canonical(repo_root: pathlib.Path, ca) -> List[Finding]:
    """§H.3.8 — Unreferenced canonical-artifact scan."""
    findings: List[Finding] = []
    # Governance surfaces that must mention each canonical artifact by path somewhere.
    # Note: .geminirules removed from corpus 2026-05-27 per ND.1 close-out.
    claude = (repo_root / "CLAUDE.md").read_text(encoding="utf-8")
    try:
        fr_path = repo_root / "00_ARCHITECTURE/FILE_REGISTRY_v1_14.md"
        if not fr_path.exists():
            for ver in ("v1_13", "v1_12", "v1_11", "v1_3", "v1_2"):
                candidate = repo_root / f"00_ARCHITECTURE/FILE_REGISTRY_{ver}.md"
                if candidate.exists():
                    fr_path = candidate
                    break
        fr = fr_path.read_text(encoding="utf-8")
    except (FileNotFoundError, AttributeError):
        fr = ""
    corpus = claude + "\n" + fr

    # LEL was cited by Grounding Audit GA.9 as unreferenced in CLAUDE.md. That is
    # expected to be addressed at Step 9. We flag it here as a Step-9-deferred
    # known-residual.
    for cid, row in ca.artifacts.items():
        path_rel = row.get("path", "")
        basename = pathlib.Path(path_rel).name if path_rel else ""
        if not basename:
            continue
        if basename not in corpus:
            severity = "MEDIUM"
            if cid == "LEL":
                # GA.9 — deferred to Step 9
                findings.append(Finding(
                    cls="canonical_unreferenced",
                    severity=severity,
                    canonical_id=cid,
                    surfaces_involved=["CLAUDE.md", "FILE_REGISTRY"],
                    evidence=f"Canonical {cid} ({basename}) not named in CLAUDE.md / FILE_REGISTRY",
                    suggested_remediation="Step 9 CLAUDE.md rebuild surfaces LEL (GA.9 resolution)",
                    whitelist_ticket="GA.9-deferred-to-step-9",
                ))
            else:
                findings.append(Finding(
                    cls="canonical_unreferenced",
                    severity=severity,
                    canonical_id=cid,
                    surfaces_involved=["CLAUDE.md", "FILE_REGISTRY"],
                    evidence=f"Canonical {cid} ({basename}) not referenced in any surface",
                    suggested_remediation=f"Register {basename} in CLAUDE.md / FILE_REGISTRY",
                ))
    return findings


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def run_all_checks(repo_root: pathlib.Path) -> List[Finding]:
    findings: List[Finding] = []
    if _USE_MANIFEST:
        try:
            from manifest_reader import load_manifest_as_ca  # noqa: E402
            ca = load_manifest_as_ca(repo_root)
        except Exception as exc:
            findings.append(Finding(
                cls="bootstrap_error",
                severity="CRITICAL",
                canonical_id="CAPABILITY_MANIFEST",
                surfaces_involved=["00_ARCHITECTURE/CAPABILITY_MANIFEST.json"],
                evidence=f"Could not load CAPABILITY_MANIFEST.json: {exc}",
                suggested_remediation="Build the manifest via `npm run manifest:build` or set DRIFT_DETECTOR_USE_MANIFEST=false",
            ))
            return findings
    else:
        try:
            ca = load_canonical_artifacts(repo_root)
        except FileNotFoundError:
            findings.append(Finding(
                cls="bootstrap_error",
                severity="CRITICAL",
                canonical_id="CANONICAL_ARTIFACTS",
                surfaces_involved=[CANONICAL_PATH],
                evidence="CANONICAL_ARTIFACTS_v1_0.md not found; cannot run drift detection",
                suggested_remediation="Produce CANONICAL_ARTIFACTS_v1_0.md per protocol §E",
            ))
            return findings
    findings.extend(check_canonical_path_parity(repo_root, ca))
    findings.extend(check_ca_filesystem_fingerprints(repo_root, ca))
    findings.extend(check_mp_pbp_alignment(repo_root))
    findings.extend(check_step_ledger_consistency(repo_root))
    findings.extend(check_file_registry_agreement(repo_root, ca))
    findings.extend(check_governance_stack_agreement(repo_root, ca))
    findings.extend(check_phantom_references(repo_root))
    findings.extend(check_unreferenced_canonical(repo_root, ca))
    findings.extend(check_chart_facts_schema(repo_root))
    findings.extend(check_a3_categories_and_mvs(repo_root))
    return findings


def compute_exit_code(findings: List[Finding]) -> int:
    non_whitelisted = [f for f in findings if not f.whitelist_ticket]
    if any(f.severity == "CRITICAL" for f in non_whitelisted):
        return 1
    if any(f.severity == "HIGH" for f in non_whitelisted):
        return 2
    if non_whitelisted:
        return 3
    return 0


def write_json_report(findings: List[Finding], out_path: pathlib.Path, session_id: str, exit_code: int) -> None:
    by_class: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    for f in findings:
        by_class[f.cls] = by_class.get(f.cls, 0) + 1
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
    report = {
        "drift_report": {
            "session_id": session_id,
            "run_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "findings": [f.to_dict() for f in findings],
            "summary": {
                "total": len(findings),
                "by_class": by_class,
                "by_severity": by_severity,
                "whitelisted": sum(1 for f in findings if f.whitelist_ticket),
            },
            "exit_code": exit_code,
        }
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_markdown_report(findings: List[Finding], out_path: pathlib.Path, session_id: str, exit_code: int) -> None:
    by_sev = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)
    lines: List[str] = []
    lines.append(f"# DRIFT REPORT — {session_id}")
    lines.append("")
    lines.append(f"*Generated by `platform/scripts/governance/drift_detector.py` on {_dt.datetime.now(_dt.timezone.utc).isoformat()}.*")
    lines.append("")
    lines.append(f"Exit code: **{exit_code}** (0 clean; 1 critical; 2 high; 3 medium/low; 4 script error)")
    lines.append("")
    lines.append(f"Total findings: **{len(findings)}** — "
                 f"{len(by_sev['CRITICAL'])} CRITICAL, {len(by_sev['HIGH'])} HIGH, "
                 f"{len(by_sev['MEDIUM'])} MEDIUM, {len(by_sev['LOW'])} LOW")
    whitelisted = sum(1 for f in findings if f.whitelist_ticket)
    lines.append(f"Whitelisted (deferred WARN tickets): **{whitelisted}**")
    lines.append("")
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        if not by_sev.get(sev):
            continue
        lines.append(f"## {sev}")
        lines.append("")
        for f in by_sev[sev]:
            suffix = f" *(whitelisted: {f.whitelist_ticket})*" if f.whitelist_ticket else ""
            lines.append(f"- **{f.cls}** ({f.canonical_id or '-'}){suffix}")
            lines.append(f"  - Surfaces: {', '.join(f.surfaces_involved)}")
            lines.append(f"  - Evidence: {f.evidence}")
            lines.append(f"  - Remediation: {f.suggested_remediation}")
        lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd(),
                    help="Repository root (defaults to current working dir).")
    ap.add_argument("--session-id", default="adhoc", help="Session ID for the report.")
    ap.add_argument("--json-path", type=pathlib.Path, default=None,
                    help="Path for the JSON report. Defaults to 00_ARCHITECTURE/drift_reports/...")
    ap.add_argument("--report-path", type=pathlib.Path, default=None,
                    help="Path for the markdown report. Defaults to 00_ARCHITECTURE/drift_reports/...")
    args = ap.parse_args()

    try:
        findings = run_all_checks(args.repo_root)
    except Exception:  # script-internal error
        traceback.print_exc()
        return 4

    exit_code = compute_exit_code(findings)
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    default_json = args.repo_root / "00_ARCHITECTURE" / "drift_reports" / f"DRIFT_REPORT_{args.session_id}_{ts}.json"
    default_md = args.repo_root / "00_ARCHITECTURE" / "drift_reports" / f"DRIFT_REPORT_{args.session_id}_{ts}.md"
    json_path = args.json_path or default_json
    md_path = args.report_path or default_md
    write_json_report(findings, json_path, args.session_id, exit_code)
    write_markdown_report(findings, md_path, args.session_id, exit_code)

    print(f"drift_detector: {len(findings)} findings; exit={exit_code}")
    print(f"  JSON: {json_path.relative_to(args.repo_root) if args.repo_root in json_path.parents or json_path.is_relative_to(args.repo_root) else json_path}")
    print(f"  MD:   {md_path.relative_to(args.repo_root) if args.repo_root in md_path.parents or md_path.is_relative_to(args.repo_root) else md_path}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

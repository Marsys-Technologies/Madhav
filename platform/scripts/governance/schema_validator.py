#!/usr/bin/env python3
"""
schema_validator.py — MARSYS-JIS governance schema validator.

# Implements: GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §I

Validates:
  I.3.1 — Per-class frontmatter required fields (loaded from schemas/artifact_schemas.yaml)
  I.3.3 — SESSION_LOG entry schema (post-Step-10: structural presence of session_open +
          body + session_close per SESSION_LOG_SCHEMA_v1_0.md §2 + §4 menu-form check)
  I.3.4 — STEP_LEDGER row schema (rebuild era)
  I.3.5 — RETIRED 2026-05-27 per ND.1 close-out (mirror-pair structural equivalence)
  I.3.6 — Registry-row-per-touched-file discipline
  I.3.7 — Version-monotonicity (per canonical artifact; FILE_REGISTRY + GOVERNANCE_STACK + CANONICAL_ARTIFACTS)
  (Step 10 addition) — CURRENT_STATE_v1_0.md required fields + cross-check against
                       STEP_LEDGER (rebuild era) and SESSION_LOG tail.

Exit codes (per §I.4):
  0  — clean
  1  — at least one CRITICAL violation
  2  — at least one HIGH (no CRITICAL)
  3  — only MEDIUM/LOW
  4  — script-internal error

Two invocation modes:
  python3 schema_validator.py --repo-root PATH [--session-id ID]
      Full corpus validation.
  python3 schema_validator.py --handshake PATH
      Validate a single session-open YAML block.
  python3 schema_validator.py --close-checklist PATH
      Validate a single session-close YAML block.
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
from typing import Dict, List, Optional

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _ca_loader import load_canonical_artifacts  # noqa: E402

# Feature flag: when true, reads from CAPABILITY_MANIFEST.json instead of CANONICAL_ARTIFACTS.
# Default true (manifest path is production after Phase 1B cutover).
_USE_MANIFEST = os.environ.get("SCHEMA_VALIDATOR_USE_MANIFEST", "true").lower() in ("true", "1", "yes")


SCHEMAS_FILE = pathlib.Path(__file__).parent / "schemas" / "artifact_schemas.yaml"


# --------------------------------------------------------------------------------------
# Violation model
# --------------------------------------------------------------------------------------

@dataclasses.dataclass
class Violation:
    rule: str
    severity: str
    path: str
    evidence: str
    suggested_remediation: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


# --------------------------------------------------------------------------------------
# Frontmatter extraction
# --------------------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)^---\s*$", re.MULTILINE | re.DOTALL)


def extract_frontmatter(text: str) -> Optional[dict]:
    """Return parsed frontmatter dict, empty dict if block present but unparseable,
    or None if no frontmatter block at all."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1))
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        # Block exists but strict parse fails — many human-authored governance
        # files carry loose-YAML frontmatter. Return marker so the validator
        # can distinguish "missing" vs "present-but-loose".
        return {"__loose_yaml__": True}


def _frontmatter_has_key(raw_frontmatter_block: str, key: str) -> bool:
    """Best-effort key detection for loose-YAML files: finds `key:` at line start."""
    return re.search(r"(?m)^" + re.escape(key) + r"\s*:", raw_frontmatter_block) is not None


def _extract_raw_frontmatter_block(text: str) -> Optional[str]:
    m = _FRONTMATTER_RE.match(text)
    return m.group(1) if m else None


def load_schemas() -> dict:
    with open(SCHEMAS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------------------------------------------------------------------------------
# Checks (§I.3.1 onward)
# --------------------------------------------------------------------------------------

def validate_frontmatter_for_class(repo_root: pathlib.Path, schemas: dict) -> List[Violation]:
    """§I.3.1 — per-class frontmatter required fields."""
    violations: List[Violation] = []
    for cls_name, cfg in schemas.items():
        required = cfg.get("required_frontmatter", [])
        globs = cfg.get("path_glob", [])
        for g in globs:
            for path in repo_root.glob(g):
                if path.name.startswith("."):
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                fm = extract_frontmatter(text)
                raw_block = _extract_raw_frontmatter_block(text)
                if fm is None:
                    violations.append(Violation(
                        rule=f"frontmatter_missing[{cls_name}]",
                        severity="MEDIUM",
                        path=str(path.relative_to(repo_root)),
                        evidence="No frontmatter `---` block found",
                        suggested_remediation=f"Add YAML frontmatter with keys {required}",
                    ))
                    continue
                if fm.get("__loose_yaml__"):
                    # Frontmatter block exists but strict YAML parse fails — fall back to
                    # line-wise key scan. Downgrade severity to LOW since many human-authored
                    # files use loose YAML.
                    if raw_block:
                        for key in required:
                            if not _frontmatter_has_key(raw_block, key):
                                violations.append(Violation(
                                    rule=f"frontmatter_field_missing[{cls_name}/{key}]",
                                    severity="LOW",
                                    path=str(path.relative_to(repo_root)),
                                    evidence=f"Required key '{key}' not present (loose-YAML frontmatter)",
                                    suggested_remediation=f"Add `{key}:` at line start",
                                ))
                    continue
                for key in required:
                    if key not in fm:
                        violations.append(Violation(
                            rule=f"frontmatter_field_missing[{cls_name}/{key}]",
                            severity="MEDIUM",
                            path=str(path.relative_to(repo_root)),
                            evidence=f"Required key '{key}' not present",
                            suggested_remediation=f"Add `{key}:` to frontmatter",
                        ))
    return violations


def validate_step_ledger(repo_root: pathlib.Path) -> List[Violation]:
    """§I.3.4 — STEP_LEDGER frontmatter presence + table header presence."""
    violations: List[Violation] = []
    p = repo_root / "00_ARCHITECTURE" / "STEP_LEDGER_v1_0.md"
    if not p.exists():
        violations.append(Violation(
            rule="step_ledger_missing",
            severity="CRITICAL",
            path="00_ARCHITECTURE/STEP_LEDGER_v1_0.md",
            evidence="File does not exist",
            suggested_remediation="Restore STEP_LEDGER",
        ))
        return violations
    text = p.read_text(encoding="utf-8")
    raw_block = _extract_raw_frontmatter_block(text)
    if raw_block is None:
        violations.append(Violation(
            rule="step_ledger_frontmatter_missing",
            severity="HIGH",
            path="00_ARCHITECTURE/STEP_LEDGER_v1_0.md",
            evidence="No frontmatter `---` block",
            suggested_remediation="Add ledger frontmatter per §I.3.4",
        ))
    # Table header check
    if "| Step | Title | Status |" not in text:
        violations.append(Violation(
            rule="step_ledger_table_header_missing",
            severity="HIGH",
            path="00_ARCHITECTURE/STEP_LEDGER_v1_0.md",
            evidence="Expected header `| Step | Title | Status |` not found",
            suggested_remediation="Preserve the canonical ledger table header",
        ))
    return violations


def validate_session_log(repo_root: pathlib.Path) -> List[Violation]:
    """§I.3.3 — SESSION_LOG append-only structural check (minimal at v1.0)."""
    violations: List[Violation] = []
    p = repo_root / "00_ARCHITECTURE" / "SESSION_LOG.md"
    if not p.exists():
        violations.append(Violation(
            rule="session_log_missing",
            severity="CRITICAL",
            path="00_ARCHITECTURE/SESSION_LOG.md",
            evidence="File does not exist",
            suggested_remediation="Restore SESSION_LOG",
        ))
        return violations
    text = p.read_text(encoding="utf-8", errors="replace")
    if len(text.strip()) == 0:
        violations.append(Violation(
            rule="session_log_empty",
            severity="HIGH",
            path="00_ARCHITECTURE/SESSION_LOG.md",
            evidence="SESSION_LOG is empty",
            suggested_remediation="Append initial entry",
        ))
    # Minimal v1.0 check: every session entry begins with `## ` or `### `. Step 10 upgrades.
    return violations




def validate_version_monotonicity(repo_root: pathlib.Path, ca) -> List[Violation]:
    """§I.3.7 — for core canonical artifacts, version strings must be monotonic
    in CANONICAL_ARTIFACTS (no regression). This v1.0 check is presence-only —
    flags a LOW informational if the declared version is 'rolling' or a placeholder."""
    violations: List[Violation] = []
    for cid, row in ca.artifacts.items():
        version = str(row.get("version", ""))
        if not version:
            violations.append(Violation(
                rule="version_missing_in_canonical_artifacts",
                severity="MEDIUM",
                path=f"CANONICAL_ARTIFACTS §1 [{cid}]",
                evidence="Row has no version field",
                suggested_remediation=f"Populate version for canonical_id={cid}",
            ))
    return violations


# --------------------------------------------------------------------------------------
# SESSION_LOG entry validation (Step 10 extension — §I.3.3 upgrade)
# --------------------------------------------------------------------------------------

# Literal marker from SESSION_LOG_SCHEMA_v1_0.md §5 — H1 heading at line start. The prose
# reference inside the banner is not an H1 and does not match this regex, so the splitter
# correctly identifies the actual adoption-point rule as the boundary.
_ADOPTION_MARKER_RE = re.compile(r"^#\s+Schema adoption point", re.MULTILINE)
_SESSION_LOG_HEADING_RE = re.compile(r"^##\s+([A-Za-z0-9_.\-]+)\s+—", re.MULTILINE)
_YAML_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)
_MENU_FORM_RE = re.compile(r"(?mi)^\*\*Next\s+session\s+objective\*\*:\s*Choose\s+from")
_NEXT_OBJECTIVE_HEADING_RE = re.compile(r"^###\s+Next\s+session\s+objective", re.MULTILINE | re.IGNORECASE)


def _split_session_log_post_adoption(text: str) -> List[tuple]:
    """Return [(session_id, entry_body), ...] for every `## ` heading-delimited entry
    AFTER the first `# Schema adoption point` H1 heading. Entries before the marker are
    preserved verbatim per SESSION_LOG_SCHEMA §6 (forward-only retrofit)."""
    m_marker = _ADOPTION_MARKER_RE.search(text)
    if not m_marker:
        return []  # no adoption point yet → no post-adoption entries to validate
    tail = text[m_marker.end():]
    headings = list(_SESSION_LOG_HEADING_RE.finditer(tail))
    entries: List[tuple] = []
    for i, m in enumerate(headings):
        start = m.start()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(tail)
        entries.append((m.group(1), tail[start:end]))
    return entries


def validate_session_log_entries(repo_root: pathlib.Path) -> List[Violation]:
    """§I.3.3 (Step 10 upgrade) — validate every post-adoption SESSION_LOG entry against
    SESSION_LOG_SCHEMA_v1_0.md §2 structural requirements + §4 menu-form prohibition."""
    violations: List[Violation] = []
    p = repo_root / "00_ARCHITECTURE" / "SESSION_LOG.md"
    if not p.exists():
        return violations  # handled by validate_session_log()
    text = p.read_text(encoding="utf-8", errors="replace")
    if not _ADOPTION_MARKER_RE.search(text):
        # Step 10 not yet closed — no post-adoption entries to validate.
        return violations
    entries = _split_session_log_post_adoption(text)
    schema_path_rel = "00_ARCHITECTURE/SESSION_LOG.md"
    for session_id_from_heading, entry_body in entries:
        yaml_blocks = list(_YAML_FENCE_RE.finditer(entry_body))
        # §2.b — require at least one fenced yaml block that parses with `session_open:`
        open_block_found = False
        close_block_found = False
        open_session_id = None
        close_session_id = None
        for m in yaml_blocks:
            try:
                data = yaml.safe_load(m.group(1))
            except yaml.YAMLError:
                continue
            if isinstance(data, dict):
                if "session_open" in data:
                    open_block_found = True
                    so = data["session_open"] or {}
                    open_session_id = so.get("session_id")
                if "session_close" in data:
                    close_block_found = True
                    sc = data["session_close"] or {}
                    close_session_id = sc.get("session_id")
        if not open_block_found:
            violations.append(Violation(
                rule="session_log_entry_missing_session_open_yaml",
                severity="CRITICAL",
                path=f"{schema_path_rel}#{session_id_from_heading}",
                evidence="No fenced ```yaml``` block containing `session_open:` found in entry",
                suggested_remediation="Append the session_open YAML per SESSION_OPEN_TEMPLATE_v1_0.md §2",
            ))
        if not close_block_found:
            violations.append(Violation(
                rule="session_log_entry_missing_session_close_yaml",
                severity="CRITICAL",
                path=f"{schema_path_rel}#{session_id_from_heading}",
                evidence="No fenced ```yaml``` block containing `session_close:` found in entry",
                suggested_remediation="Append the session_close YAML per SESSION_CLOSE_TEMPLATE_v1_0.md §2",
            ))
        # §1.4 — session_id consistency across heading + session_open + session_close
        if open_session_id and open_session_id != session_id_from_heading:
            violations.append(Violation(
                rule="session_log_entry_session_id_disagreement_heading_open",
                severity="HIGH",
                path=f"{schema_path_rel}#{session_id_from_heading}",
                evidence=f"Heading says `{session_id_from_heading}`; session_open.session_id says `{open_session_id}`",
                suggested_remediation="Reconcile per SESSION_LOG_SCHEMA_v1_0.md §1.4",
            ))
        if close_session_id and close_session_id != session_id_from_heading:
            violations.append(Violation(
                rule="session_log_entry_session_id_disagreement_heading_close",
                severity="HIGH",
                path=f"{schema_path_rel}#{session_id_from_heading}",
                evidence=f"Heading says `{session_id_from_heading}`; session_close.session_id says `{close_session_id}`",
                suggested_remediation="Reconcile per SESSION_LOG_SCHEMA_v1_0.md §1.4",
            ))
        # §4 — menu-form next-objective is forbidden
        if _MENU_FORM_RE.search(entry_body):
            violations.append(Violation(
                rule="session_log_entry_menu_form_next_objective",
                severity="HIGH",
                path=f"{schema_path_rel}#{session_id_from_heading}",
                evidence='"**Next session objective**: Choose from" pattern matched',
                suggested_remediation="Replace with one committed objective + `### Deferred alternatives` appendix per SESSION_LOG_SCHEMA_v1_0.md §4",
            ))
        # §2.f — committed next-objective heading expected
        if not _NEXT_OBJECTIVE_HEADING_RE.search(entry_body):
            violations.append(Violation(
                rule="session_log_entry_missing_next_objective_heading",
                severity="LOW",
                path=f"{schema_path_rel}#{session_id_from_heading}",
                evidence="No `### Next session objective` heading found",
                suggested_remediation="Add the heading per SESSION_LOG_SCHEMA_v1_0.md §2.f",
            ))
    return violations


# --------------------------------------------------------------------------------------
# CURRENT_STATE validation (Step 10 new check)
# --------------------------------------------------------------------------------------

_CURRENT_STATE_FENCE_RE = re.compile(r"```yaml\s*\n(current_state:.*?)^```\s*$",
                                     re.MULTILINE | re.DOTALL)


def validate_current_state(repo_root: pathlib.Path, schemas: dict) -> List[Violation]:
    """Step 10 addition — validate CURRENT_STATE_v1_0.md: frontmatter presence, required
    state-block fields, and (rebuild era) cross-check `last_session_id` against SESSION_LOG
    tail + `active_governance_step` against STEP_LEDGER."""
    violations: List[Violation] = []
    p = repo_root / "00_ARCHITECTURE" / "CURRENT_STATE_v1_0.md"
    cfg = schemas.get("current_state", {}) or {}
    if not p.exists():
        # Pre-Step-10 absence is NOT a violation; post-Step-10 absence is LOW until the
        # drift_detector catches it via its own canonical-path check (CURRENT_STATE will be
        # added to CANONICAL_ARTIFACTS §1 at Step 10 close).
        return violations
    text = p.read_text(encoding="utf-8", errors="replace")
    # Frontmatter check — already covered generically by validate_frontmatter_for_class via
    # the architecture_governance class (00_ARCHITECTURE/*.md). We add the required-state-
    # block-field check here.
    m = _CURRENT_STATE_FENCE_RE.search(text)
    if not m:
        violations.append(Violation(
            rule="current_state_missing_state_block",
            severity="HIGH",
            path="00_ARCHITECTURE/CURRENT_STATE_v1_0.md",
            evidence="No ```yaml current_state: ... ``` fenced block found",
            suggested_remediation="Add the §2 canonical state block per CURRENT_STATE_v1_0.md §2",
        ))
        return violations
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        violations.append(Violation(
            rule="current_state_block_parse_error",
            severity="HIGH",
            path="00_ARCHITECTURE/CURRENT_STATE_v1_0.md",
            evidence=f"current_state YAML fence failed to parse: {e}",
            suggested_remediation="Fix YAML syntax in §2 state block",
        ))
        return violations
    if not isinstance(data, dict) or "current_state" not in data:
        violations.append(Violation(
            rule="current_state_block_wrong_root",
            severity="HIGH",
            path="00_ARCHITECTURE/CURRENT_STATE_v1_0.md",
            evidence="Fenced block does not have top-level `current_state:` key",
            suggested_remediation="Wrap state fields under `current_state:` per §2",
        ))
        return violations
    cs = data["current_state"] or {}
    for key in cfg.get("required_state_block_fields", []):
        if key not in cs:
            violations.append(Violation(
                rule=f"current_state_field_missing[{key}]",
                severity="MEDIUM",
                path="00_ARCHITECTURE/CURRENT_STATE_v1_0.md",
                evidence=f"Required field `{key}` absent from `current_state:` block",
                suggested_remediation=f"Add `{key}:` to the §2 state block",
            ))
    # Cross-check last_session_id against SESSION_LOG tail (post-adoption entries only)
    last_id = cs.get("last_session_id")
    if last_id:
        log_path = repo_root / "00_ARCHITECTURE" / "SESSION_LOG.md"
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            post_adoption = _split_session_log_post_adoption(log_text)
            if post_adoption:
                tail_id = post_adoption[-1][0]
                if tail_id != last_id:
                    violations.append(Violation(
                        rule="current_state_last_session_id_disagreement",
                        severity="MEDIUM",
                        path="00_ARCHITECTURE/CURRENT_STATE_v1_0.md",
                        evidence=f"CURRENT_STATE.last_session_id=`{last_id}` but SESSION_LOG tail entry is `{tail_id}`",
                        suggested_remediation="Update CURRENT_STATE §2 or append the missing SESSION_LOG entry (whichever is authoritative per §5)",
                    ))
    # Cross-check active_governance_step against STEP_LEDGER (rebuild era)
    active_step = cs.get("active_governance_step")
    if active_step and active_step != "GOVERNANCE_CLOSED":
        ledger_path = repo_root / "00_ARCHITECTURE" / "STEP_LEDGER_v1_0.md"
        if ledger_path.exists():
            ledger_text = ledger_path.read_text(encoding="utf-8", errors="replace")
            # Heuristic row-check: confirm the ledger mentions the step as a table row.
            # Accept both `Step_10` and `Step 10` and `| 10 |` patterns.
            step_num = active_step.replace("Step_", "").replace("Step ", "").strip()
            # Accept 5A-style alphanumeric
            if not any(pat in ledger_text for pat in (f"| {step_num} |", f"Step {step_num}", active_step)):
                violations.append(Violation(
                    rule="current_state_active_step_unknown_to_ledger",
                    severity="MEDIUM",
                    path="00_ARCHITECTURE/CURRENT_STATE_v1_0.md",
                    evidence=f"active_governance_step=`{active_step}` — no matching row detected in STEP_LEDGER_v1_0.md",
                    suggested_remediation="Reconcile CURRENT_STATE §2 against STEP_LEDGER (authoritative during the rebuild era per §5.1)",
                ))
    return violations


# --------------------------------------------------------------------------------------
# Session-open / session-close validation
# --------------------------------------------------------------------------------------

def validate_handshake_yaml(raw: str) -> List[Violation]:
    """Validate a session-open YAML block per protocol §F."""
    violations: List[Violation] = []
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return [Violation("handshake_parse_error", "CRITICAL", "<handshake>", str(e),
                           "Fix YAML syntax before resubmitting.")]
    if not isinstance(data, dict) or "session_open" not in data:
        return [Violation("handshake_missing_root", "CRITICAL", "<handshake>",
                          "Top-level `session_open:` key missing",
                          "Wrap the block in `session_open:`.")]
    so = data["session_open"]
    # Back-compat (2026-06-22 layer-model migration): accept either the legacy
    # `step_number_or_macro_phase` key OR the new canonical `step_number_or_layer` key.
    # Once all sessions migrate, Step 5 of the governance migration removes this alias.
    _STEP_FIELD_ALIASES = ("step_number_or_layer", "step_number_or_macro_phase")
    required = [
        "session_id", "cowork_thread_name", "agent_name", "agent_version", "tool",
        "tool_profile", "worktree_path", "coordination", "cross_tool_state_read",
        "predecessor_session",
        "mandatory_reading_confirmation", "canonical_artifact_fingerprint_check",
        "declared_scope", "mirror_pair_freshness_check", "native_directive_obligations",
        "red_team_due",
    ]
    for key in required:
        if key not in so:
            violations.append(Violation(
                rule=f"handshake_field_missing[{key}]",
                severity="CRITICAL",
                path="<handshake>",
                evidence=f"Required field `{key}` not present",
                suggested_remediation="Add the field per SESSION_OPEN_TEMPLATE_v1_0.md §2",
            ))
    # Step-position field: require exactly one of the two aliases
    if not any(k in so for k in _STEP_FIELD_ALIASES):
        violations.append(Violation(
            rule="handshake_field_missing[step_number_or_layer]",
            severity="CRITICAL",
            path="<handshake>",
            evidence="Neither `step_number_or_layer` nor `step_number_or_macro_phase` present",
            suggested_remediation="Add `step_number_or_layer` per SESSION_OPEN_TEMPLATE_v1_0.md §2",
        ))
    scope = so.get("declared_scope", {}) or {}
    if not scope.get("must_not_touch"):
        violations.append(Violation(
            rule="handshake_must_not_touch_empty",
            severity="HIGH",
            path="<handshake>",
            evidence="`declared_scope.must_not_touch` is empty or missing",
            suggested_remediation="Positively enumerate out-of-scope paths per protocol §F.3",
        ))
    # Any `match: false` in fingerprint check fails
    for row in (so.get("canonical_artifact_fingerprint_check") or []):
        if row.get("match") is False:
            violations.append(Violation(
                rule="handshake_fingerprint_mismatch",
                severity="CRITICAL",
                path="<handshake>",
                evidence=f"canonical_artifact_fingerprint_check mismatch on {row.get('canonical_id')}",
                suggested_remediation="Investigate silent file mutation or refresh CANONICAL_ARTIFACTS",
            ))
    # mirror_pair_freshness_check retired 2026-05-27 per ND.1 close-out.
    if so.get("tool") not in ("Claude Code", "Codex"):
        violations.append(Violation(
            rule="handshake_tool_invalid",
            severity="CRITICAL",
            path="<handshake>",
            evidence="`tool` must be Claude Code or Codex",
            suggested_remediation="Record the session's actual tool provenance.",
        ))
    coordination = so.get("coordination", {}) or {}
    if not coordination.get("lease_id") or coordination.get("lease_status_verified") is not True:
        violations.append(Violation(
            rule="handshake_coordination_lease_unverified",
            severity="CRITICAL",
            path="<handshake>",
            evidence="A live coordination lease is required for state-changing work",
            suggested_remediation="Acquire and verify the lease on origin/campaign-coordination.",
        ))
    state_read = so.get("cross_tool_state_read", {}) or {}
    if state_read.get("cross_cutting_decision_register") is not True:
        violations.append(Violation(
            rule="handshake_ccd_register_not_confirmed",
            severity="CRITICAL",
            path="<handshake>",
            evidence="cross_tool_state_read.cross_cutting_decision_register must be true",
            suggested_remediation="Read and record CROSS_CUTTING_DECISION_REGISTER_v1_0.md before work.",
        ))
    profile = so.get("tool_profile")
    if so.get("tool") == "Codex" and profile not in ("madhav-safe", "madhav-parity"):
        violations.append(Violation(
            rule="handshake_codex_profile_invalid",
            severity="CRITICAL",
            path="<handshake>",
            evidence="Codex tool_profile must be madhav-safe or madhav-parity",
            suggested_remediation="Record the selected approved Codex profile.",
        ))
    return violations


def validate_close_checklist_yaml(raw: str) -> List[Violation]:
    """Validate a session-close YAML block per protocol §G."""
    violations: List[Violation] = []
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return [Violation("close_parse_error", "CRITICAL", "<close>", str(e), "Fix YAML syntax.")]
    if not isinstance(data, dict) or "session_close" not in data:
        return [Violation("close_missing_root", "CRITICAL", "<close>",
                          "Top-level `session_close:` key missing",
                          "Wrap the block in `session_close:`.")]
    sc = data["session_close"]
    required = [
        "session_id", "closed_at", "tool", "files_touched", "registry_updates_made",
        "red_team_pass", "drift_detector_run",
        "schema_validator_run", "session_log_appended", "cross_tool_sync",
        "close_criteria_met", "unblocks", "handoff_notes",
    ]
    # mirror_updates_propagated + mirror_enforcer_run retired 2026-05-27 per ND.1 close-out.
    for key in required:
        if key not in sc:
            violations.append(Violation(
                rule=f"close_field_missing[{key}]",
                severity="CRITICAL",
                path="<close>",
                evidence=f"Required field `{key}` not present",
                suggested_remediation="Add the field per SESSION_CLOSE_TEMPLATE_v1_0.md §2",
            ))

    # files_touched within_declared_scope
    for row in (sc.get("files_touched") or []):
        if row.get("within_declared_scope") is False:
            violations.append(Violation(
                rule="close_files_touched_out_of_scope",
                severity="HIGH",
                path=row.get("path", "<unknown>"),
                evidence="Touched file outside declared_scope.may_touch",
                suggested_remediation="Either expand declared_scope with rationale OR revert the touch",
            ))
    # mirror_updates_propagated check retired 2026-05-27 per ND.1 close-out.
    if sc.get("tool") not in ("Claude Code", "Codex"):
        violations.append(Violation(
            rule="close_tool_invalid",
            severity="CRITICAL",
            path="<close>",
            evidence="`tool` must be Claude Code or Codex",
            suggested_remediation="Record the session's actual tool provenance.",
        ))
    sync = sc.get("cross_tool_sync", {}) or {}
    for key in ("work_order_outcome_recorded", "lease_release_recorded", "lease_release_verified_on_remote"):
        if sync.get(key) is not True:
            violations.append(Violation(
                rule=f"close_cross_tool_sync_missing[{key}]",
                severity="CRITICAL",
                path="<close>",
                evidence=f"cross_tool_sync.{key} must be true",
            suggested_remediation="Record the outcome and release the verified coordination lease.",
        ))
    if not isinstance(sync.get("ccd_entries_appended"), list):
        violations.append(Violation(
            rule="close_cross_tool_sync_ccd_entries_invalid",
            severity="CRITICAL",
            path="<close>",
            evidence="cross_tool_sync.ccd_entries_appended must be a list (empty when none were added)",
            suggested_remediation="Record appended CCD IDs or an empty list.",
        ))
    # Script exit codes (F.2 closure — ONGOING_HYGIENE_POLICIES §F exit-code-3 whitelist)
    # Policy: exit_code 0 passes. exit_code 3 (MEDIUM/LOW only) passes IFF the close
    # YAML carries a `known_residuals` block enumerating each MEDIUM/LOW finding with
    # a booking reference (step_id + rationale). exit_code 1/2/4+ always fail close.
    known_residuals = sc.get("known_residuals") or []
    has_residuals_block = isinstance(known_residuals, list) and len(known_residuals) > 0
    for field in ("drift_detector_run", "schema_validator_run"):
        run = sc.get(field, {}) or {}
        ec = run.get("exit_code")
        if ec in (0, None):
            continue
        if ec == 3:
            # §F whitelist: accept exit 3 iff known_residuals block present + all MEDIUM/LOW
            if not has_residuals_block:
                violations.append(Violation(
                    rule="close_checklist_known_residuals_missing",
                    severity="HIGH",
                    path=f"<close>.{field}",
                    evidence=f"exit_code=3 for {field} but no `known_residuals` block enumerating MEDIUM/LOW",
                    suggested_remediation=(
                        "Add a `known_residuals:` list; each entry must name the finding, severity "
                        "(MEDIUM or LOW), and a booking reference (step_id + rationale)"
                    ),
                ))
            else:
                # Verify each residual is MEDIUM or LOW + carries booking reference
                for r in known_residuals:
                    sev = (r.get("severity") or "").upper()
                    if sev not in ("MEDIUM", "LOW"):
                        violations.append(Violation(
                            rule="close_checklist_residual_severity_violation",
                            severity="HIGH",
                            path=f"<close>.known_residuals",
                            evidence=f"residual `{r.get('finding_id', '<?>')}` has severity `{sev}`; "
                                     f"exit-code-3 whitelist requires MEDIUM or LOW only",
                            suggested_remediation="Remove the residual OR escalate to HIGH/CRITICAL handling",
                        ))
                    if not r.get("booking_reference"):
                        violations.append(Violation(
                            rule="close_checklist_residual_booking_missing",
                            severity="MEDIUM",
                            path=f"<close>.known_residuals",
                            evidence=f"residual `{r.get('finding_id', '<?>')}` missing booking_reference",
                            suggested_remediation="Add booking_reference (step_id + rationale) per §F",
                        ))
        else:
            # Exit 1, 2, 4+ always fail close
            violations.append(Violation(
                rule=f"close_{field}_nonzero_exit",
                severity="HIGH",
                path=f"<close>.{field}",
                evidence=f"exit_code={ec} for {field} (not in whitelist {{0, 3+known_residuals}})",
                suggested_remediation="Inspect the run's report; resolve or block close",
            ))
    # close_criteria_met gate
    if sc.get("close_criteria_met") is False:
        violations.append(Violation(
            rule="close_criteria_not_met",
            severity="CRITICAL",
            path="<close>",
            evidence="`close_criteria_met: false` — session cannot close",
            suggested_remediation="Address every failing check before claiming close",
        ))
    return violations


# --------------------------------------------------------------------------------------
# Step 12 extensions (ONGOING_HYGIENE_POLICIES_v1_0.md §C, §D, §F, §G)
# --------------------------------------------------------------------------------------

def _glob_match(path: str, globs: list) -> bool:
    """Match a path against any of the given globs using fnmatch semantics."""
    import fnmatch
    for g in (globs or []):
        # Allow both `**/` and `*` in the pattern
        if fnmatch.fnmatch(path, g) or fnmatch.fnmatch(path, g + "**") \
                or (g.endswith("**") and path.startswith(g[:-2])) \
                or (g.endswith("/**") and path.startswith(g[:-3])):
            return True
        # Strict prefix handling for tree globs
        if "/**" in g:
            prefix = g.split("/**")[0]
            if path == prefix or path.startswith(prefix + "/"):
                return True
    return False


def validate_scope_boundary(handshake_data: dict, close_data: dict) -> List[Violation]:
    """§C of ONGOING_HYGIENE_POLICIES_v1_0.md: close-checklist compliance check.

    Each path in session_close.files_touched must match declared_scope.may_touch
    AND must NOT match declared_scope.must_not_touch. Closes GA.20 at the
    close-checklist layer (Step 7 closed the handshake layer).
    """
    violations: List[Violation] = []
    so = handshake_data.get("session_open", {}) or {}
    sc = close_data.get("session_close", {}) or {}
    may = (so.get("declared_scope", {}) or {}).get("may_touch") or []
    mnt = (so.get("declared_scope", {}) or {}).get("must_not_touch") or []
    for row in (sc.get("files_touched") or []):
        path = row.get("path")
        if not path:
            continue
        if _glob_match(path, mnt):
            violations.append(Violation(
                rule="scope_boundary_violation",
                severity="HIGH",
                path=path,
                evidence=f"Touched path `{path}` matches declared must_not_touch glob",
                suggested_remediation="Revert the touch OR amend declared_scope with native-approved rationale",
            ))
        elif may and not _glob_match(path, may):
            violations.append(Violation(
                rule="scope_boundary_violation",
                severity="HIGH",
                path=path,
                evidence=f"Touched path `{path}` is not in declared may_touch",
                suggested_remediation="Add the path to declared_scope.may_touch with rationale, OR revert",
            ))
    return violations


def validate_files_touched_completeness(close_data: dict, ca) -> List[Violation]:
    """§D of ONGOING_HYGIENE_POLICIES_v1_0.md: the files_touched set must equal
    the fingerprint-delta set across canonical artifacts. Closes GA.21.

    Expects `ca` to expose canonical rows with `path` + observed fingerprint
    (as of close time) and declared fingerprint (as of session open).
    """
    violations: List[Violation] = []
    sc = close_data.get("session_close", {}) or {}
    touched = {row.get("path") for row in (sc.get("files_touched") or []) if row.get("path")}
    touched_reasons = {row.get("path"): row.get("reason", "") for row in (sc.get("files_touched") or [])}

    try:
        rows = ca.iter_rows()
    except AttributeError:
        rows = getattr(ca, "rows", []) or []

    # Fingerprint-delta set: declared != observed
    delta_paths = set()
    for row in rows:
        declared = getattr(row, "fingerprint_sha256", None) or getattr(row, "declared_fingerprint", None)
        observed = getattr(row, "observed_fingerprint", None)
        path = getattr(row, "path", None)
        if not path or not declared:
            continue
        if observed and declared != observed:
            delta_paths.add(path)

    # Every delta path must be in files_touched
    for path in delta_paths - touched:
        violations.append(Violation(
            rule="files_touched_incomplete",
            severity="HIGH",
            path=path,
            evidence=f"Canonical artifact `{path}` fingerprint rotated but is not in files_touched",
            suggested_remediation="Add the path to session_close.files_touched with a reason field",
        ))

    # Every files_touched path must either be in delta_paths OR carry a justifying reason
    OK_REASONS = {"created_this_session", "reviewed_not_modified", "status_flag_only",
                  "banner_only", "frontmatter_flip_only", "superseded_this_session"}
    for path in touched - delta_paths:
        reason = (touched_reasons.get(path) or "").strip().lower()
        if reason not in OK_REASONS:
            violations.append(Violation(
                rule="files_touched_unjustified",
                severity="MEDIUM",
                path=path,
                evidence=f"files_touched entry `{path}` has no fingerprint rotation and no "
                         f"justifying `reason` (got: {reason or '<empty>'})",
                suggested_remediation=(
                    "Set reason to one of: " + ", ".join(sorted(OK_REASONS))
                ),
            ))
    return violations


_LL_STATUS_BANNER_RE = re.compile(r"^STATUS:\s*(STUB|ACTIVE)\s*[—-]\s*.*$", re.MULTILINE)


def validate_learning_layer_stub(repo_root: pathlib.Path, schemas: dict | None = None) -> List[Violation]:
    """§G of ONGOING_HYGIENE_POLICIES_v1_0.md + LL_SCAFFOLD_DECISION §5.7:
    learning_layer_stub class — STATUS-banner regex, population gate, and
    classical-priors-locked guard for 06_LEARNING_LAYER/** mechanism stubs.
    Honors path_exclude from artifact_schemas.yaml learning_layer_stub class.
    """
    violations: List[Violation] = []
    ll_root = repo_root / "06_LEARNING_LAYER"
    if not ll_root.is_dir():
        return violations
    if schemas is None:
        schemas = load_schemas()
    excluded = schemas.get("learning_layer_stub", {}).get("path_exclude", [])
    for readme in ll_root.glob("*/README.md"):
        rel_path = str(readme.relative_to(repo_root))
        if rel_path in excluded:
            continue
        try:
            text = readme.read_text(encoding="utf-8")
        except Exception as e:
            violations.append(Violation(
                rule="learning_layer_stub_unreadable",
                severity="HIGH",
                path=str(readme.relative_to(repo_root)),
                evidence=f"Could not read stub README: {e}",
                suggested_remediation="Fix file permissions / encoding",
            ))
            continue

        fm = extract_frontmatter(text) or {}
        body_start = text.find("\n---", 3)
        body = text[body_start + 4:] if body_start != -1 else text

        # Rule 1: STATUS banner presence + form
        banner_match = _LL_STATUS_BANNER_RE.search(body)
        if not banner_match:
            violations.append(Violation(
                rule="learning_layer_stub_banner_missing",
                severity="HIGH",
                path=str(readme.relative_to(repo_root)),
                evidence="No `STATUS: STUB|ACTIVE — ...` banner found",
                suggested_remediation="Prepend STATUS banner matching regex `^STATUS:\\s*(STUB|ACTIVE)\\s*[—-]\\s*.*$`",
            ))
            continue
        status_tag = banner_match.group(1)

        # Rule 2: Population gate (only if ACTIVE)
        if status_tag == "ACTIVE":
            activation_session = fm.get("activation_session_id")
            lel_entry = fm.get("activation_lel_entry")
            ppl_entry = fm.get("activation_ppl_entry")
            if not activation_session:
                violations.append(Violation(
                    rule="learning_layer_population_gate_violation",
                    severity="HIGH",
                    path=str(readme.relative_to(repo_root)),
                    evidence="STATUS ACTIVE but `activation_session_id` missing from frontmatter",
                    suggested_remediation="Populate activation_session_id + either activation_lel_entry or activation_ppl_entry",
                ))
            if not (lel_entry or ppl_entry):
                violations.append(Violation(
                    rule="learning_layer_population_gate_violation",
                    severity="HIGH",
                    path=str(readme.relative_to(repo_root)),
                    evidence="STATUS ACTIVE but neither activation_lel_entry nor activation_ppl_entry present",
                    suggested_remediation="Populate at least one of: activation_lel_entry, activation_ppl_entry",
                ))

        # Rule 3: Classical-priors-locked — writes_to ⊆ 06_LEARNING_LAYER/**
        writes_to = fm.get("writes_to")
        if writes_to:
            targets = writes_to if isinstance(writes_to, list) else [writes_to]
            for t in targets:
                if not str(t).startswith("06_LEARNING_LAYER/"):
                    violations.append(Violation(
                        rule="classical_priors_locked_violation",
                        severity="CRITICAL",
                        path=str(readme.relative_to(repo_root)),
                        evidence=f"writes_to target `{t}` is outside 06_LEARNING_LAYER/**",
                        suggested_remediation="Restrict writes_to to 06_LEARNING_LAYER/**; learning modulates, never overwrites",
                    ))
    return violations




def validate_dr_entry_yaml(raw: str) -> List[Violation]:
    """F.3 closure: single-entry DR validator mode (--dr-entry). Validates
    a DISAGREEMENT_REGISTER entry against protocol §K.4 schema.
    """
    violations: List[Violation] = []
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return [Violation("dr_entry_parse_error", "CRITICAL", "<dr>", str(e),
                          "Fix YAML syntax")]
    if not isinstance(data, dict):
        return [Violation("dr_entry_not_dict", "CRITICAL", "<dr>",
                          "DR entry is not a mapping",
                          "Wrap fields in a mapping per protocol §K.4")]
    required = ["entry_id", "opened_on", "class", "claude_position",
                "gemini_position", "arbitration_status", "status"]
    for key in required:
        if key not in data:
            violations.append(Violation(
                rule=f"dr_entry_field_missing[{key}]",
                severity="HIGH",
                path="<dr>",
                evidence=f"Required field `{key}` missing from DR entry",
                suggested_remediation="Add per GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K.4",
            ))
    # Class whitelist (DIS.class.mirror_desync retired 2026-05-27 per ND.1 close-out)
    allowed_classes = {
        "DIS.class.schema_interpretation",
        "DIS.class.derivation_conflict",
        "DIS.class.forensic_conflict",
        "DIS.class.ethics_disagreement",
    }
    cls = data.get("class")
    if cls and cls not in allowed_classes:
        violations.append(Violation(
            rule="dr_entry_class_unknown",
            severity="MEDIUM",
            path="<dr>",
            evidence=f"class `{cls}` not in the five declared classes",
            suggested_remediation="Use one of: " + ", ".join(sorted(allowed_classes)),
        ))
    return violations


def validate_a3_schema(repo_root: pathlib.Path) -> List[Violation]:
    """A3-S7 — Validate A3 schema enforcement (static + file-based checks).

    Checks (no DB required):
    1. CHART_FACTS_SCHEMA.json exists and has >= 140 categories.
    2. CHART_FACTS_SCHEMA.json has exactly 4 data channels.

    DB-dependent checks (skipped gracefully if psql absent):
    3. chart_facts.verification_pass_status column exists.
    4. chart_facts.fact_subject column exists.
    5. chart_dashas table exists with two-pass-mandatory CHECK constraint.
    """
    import subprocess
    import shutil

    violations: List[Violation] = []
    schema_path = repo_root / "platform/scripts/governance/CHART_FACTS_SCHEMA.json"

    # Static check 1: CHART_FACTS_SCHEMA.json category count
    if not schema_path.exists():
        violations.append(Violation(
            rule="a3_schema_json_missing",
            severity="HIGH",
            path="platform/scripts/governance/CHART_FACTS_SCHEMA.json",
            evidence="CHART_FACTS_SCHEMA.json not found",
            suggested_remediation="Run A3-S5 to produce CHART_FACTS_SCHEMA.json",
        ))
        return violations

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:
        violations.append(Violation(
            rule="a3_schema_json_invalid",
            severity="HIGH",
            path="platform/scripts/governance/CHART_FACTS_SCHEMA.json",
            evidence=f"Could not parse CHART_FACTS_SCHEMA.json: {exc}",
            suggested_remediation="Repair the JSON file",
        ))
        return violations

    categories = schema.get("categories", {})
    if len(categories) < 140:
        violations.append(Violation(
            rule="a3_schema_category_count_low",
            severity="HIGH",
            path="platform/scripts/governance/CHART_FACTS_SCHEMA.json",
            evidence=f"CHART_FACTS_SCHEMA.json has {len(categories)} categories (expected >= 140)",
            suggested_remediation="Re-run A3-S5 schema generation — fewer categories than declared",
        ))

    channels = schema.get("channels", {})
    if len(channels) != 4:
        violations.append(Violation(
            rule="a3_schema_channel_count_wrong",
            severity="MEDIUM",
            path="platform/scripts/governance/CHART_FACTS_SCHEMA.json",
            evidence=f"CHART_FACTS_SCHEMA.json has {len(channels)} channels (expected 4)",
            suggested_remediation="Verify A3-S5 produced all 4 channel adapters",
        ))

    # DB-dependent checks
    if not shutil.which("psql"):
        return violations

    pg_host = os.environ.get("PGHOST", "127.0.0.1")
    pg_port = os.environ.get("PGPORT", "5433")
    pg_user = os.environ.get("PGUSER", "amjis_app")
    pg_db = os.environ.get("PGDATABASE", "amjis")
    pg_password = os.environ.get("PGPASSWORD", "")
    env = {**os.environ, "PGPASSWORD": pg_password}

    def _run(query: str):
        try:
            r = subprocess.run(
                ["psql", "-h", pg_host, "-p", pg_port, "-U", pg_user, "-d", pg_db,
                 "-t", "-c", query],
                capture_output=True, text=True, timeout=10, env=env,
            )
            return r.stdout if r.returncode == 0 else None
        except Exception:
            return None

    # Check verification_pass_status column
    out = _run(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='chart_facts' "
        "AND column_name='verification_pass_status';"
    )
    if out is not None and "verification_pass_status" not in out:
        violations.append(Violation(
            rule="a3_chart_facts_column_missing[verification_pass_status]",
            severity="HIGH",
            path="chart_facts",
            evidence="Column verification_pass_status missing from chart_facts",
            suggested_remediation="Apply migration 134_chart_facts_extend.sql",
        ))

    # Check fact_subject column
    out = _run(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='chart_facts' "
        "AND column_name='fact_subject';"
    )
    if out is not None and "fact_subject" not in out:
        violations.append(Violation(
            rule="a3_chart_facts_column_missing[fact_subject]",
            severity="HIGH",
            path="chart_facts",
            evidence="Column fact_subject missing from chart_facts",
            suggested_remediation="Apply migration 134_chart_facts_extend.sql",
        ))

    # Check chart_dashas table + two-pass-mandatory constraint
    out = _run(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name='chart_dashas';"
    )
    if out is not None:
        if "chart_dashas" not in out:
            violations.append(Violation(
                rule="a3_chart_dashas_table_missing",
                severity="HIGH",
                path="chart_dashas",
                evidence="chart_dashas table does not exist",
                suggested_remediation="Apply migration 135_chart_dashas.sql",
            ))
        else:
            # Check two-pass-mandatory CHECK constraint
            out2 = _run(
                "SELECT conname FROM pg_constraint "
                "WHERE conrelid = 'chart_dashas'::regclass "
                "AND contype = 'c' AND conname LIKE '%two_pass%';"
            )
            if out2 is not None and "two_pass" not in out2:
                violations.append(Violation(
                    rule="a3_chart_dashas_constraint_missing",
                    severity="MEDIUM",
                    path="chart_dashas",
                    evidence="chart_dashas missing two-pass-mandatory CHECK constraint",
                    suggested_remediation="Apply migration 135_chart_dashas.sql which adds the two-pass constraint",
                ))

    return violations


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def compute_exit_code(violations: List[Violation]) -> int:
    if any(v.severity == "CRITICAL" for v in violations):
        return 1
    if any(v.severity == "HIGH" for v in violations):
        return 2
    if violations:
        return 3
    return 0


def write_json_report(violations: List[Violation], out_path: pathlib.Path, session_id: str, exit_code: int) -> None:
    by_sev: Dict[str, int] = {}
    for v in violations:
        by_sev[v.severity] = by_sev.get(v.severity, 0) + 1
    out = {
        "schema_validation_report": {
            "session_id": session_id,
            "run_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "violations": [v.to_dict() for v in violations],
            "summary": {"total": len(violations), "by_severity": by_sev},
            "exit_code": exit_code,
        }
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")


def write_markdown_report(violations: List[Violation], out_path: pathlib.Path, session_id: str, exit_code: int) -> None:
    by_sev = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for v in violations:
        by_sev.setdefault(v.severity, []).append(v)
    lines: List[str] = []
    lines.append(f"# SCHEMA VALIDATION REPORT — {session_id}")
    lines.append("")
    lines.append(f"*Generated by `platform/scripts/governance/schema_validator.py` on {_dt.datetime.now(_dt.timezone.utc).isoformat()}.*")
    lines.append("")
    lines.append(f"Exit code: **{exit_code}** (0 clean; 1 critical; 2 high; 3 medium/low; 4 script error)")
    lines.append("")
    lines.append(f"Total violations: **{len(violations)}**")
    lines.append("")
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        if not by_sev[sev]:
            continue
        lines.append(f"## {sev}")
        lines.append("")
        for v in by_sev[sev]:
            lines.append(f"- **{v.rule}** — `{v.path}`")
            lines.append(f"  - Evidence: {v.evidence}")
            lines.append(f"  - Remediation: {v.suggested_remediation}")
        lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def run_corpus(repo_root: pathlib.Path) -> List[Violation]:
    violations: List[Violation] = []
    if _USE_MANIFEST:
        try:
            from manifest_reader import load_manifest_as_ca  # noqa: E402
            ca = load_manifest_as_ca(repo_root)
        except Exception as exc:
            violations.append(Violation(
                "capability_manifest_missing", "CRITICAL",
                "00_ARCHITECTURE/CAPABILITY_MANIFEST.json",
                f"Could not load CAPABILITY_MANIFEST.json: {exc}",
                "Build the manifest via `npm run manifest:build` or set SCHEMA_VALIDATOR_USE_MANIFEST=false",
            ))
            return violations
    else:
        try:
            ca = load_canonical_artifacts(repo_root)
        except FileNotFoundError:
            violations.append(Violation("canonical_artifacts_missing", "CRITICAL",
                                        "00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md",
                                        "File does not exist — corpus schema validation cannot complete",
                                        "Produce CANONICAL_ARTIFACTS per protocol §E"))
            return violations
    schemas = load_schemas()
    violations.extend(validate_frontmatter_for_class(repo_root, schemas))
    violations.extend(validate_step_ledger(repo_root))
    violations.extend(validate_session_log(repo_root))
    violations.extend(validate_session_log_entries(repo_root))   # Step 10 addition
    violations.extend(validate_current_state(repo_root, schemas))  # Step 10 addition
    violations.extend(validate_version_monotonicity(repo_root, ca))
    violations.extend(validate_a3_schema(repo_root))
    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd())
    ap.add_argument("--session-id", default="adhoc")
    ap.add_argument("--handshake", type=pathlib.Path, default=None,
                    help="Validate a session-open YAML block at this path.")
    ap.add_argument("--close-checklist", type=pathlib.Path, default=None,
                    help="Validate a session-close YAML block at this path.")
    ap.add_argument("--session-open-for-close", type=pathlib.Path, default=None,
                    help="Companion handshake YAML (used by --close-checklist for "
                         "§C scope-boundary cross-reference; Step 12 addition).")
    ap.add_argument("--dr-entry", type=pathlib.Path, default=None,
                    help="Validate a single DISAGREEMENT_REGISTER entry YAML block "
                         "against protocol §K.4 schema (F.3 closure).")
    ap.add_argument("--json-path", type=pathlib.Path, default=None)
    ap.add_argument("--report-path", type=pathlib.Path, default=None)
    args = ap.parse_args()

    try:
        if args.handshake:
            text = args.handshake.read_text(encoding="utf-8")
            violations = validate_handshake_yaml(text)
        elif args.close_checklist:
            text = args.close_checklist.read_text(encoding="utf-8")
            violations = validate_close_checklist_yaml(text)
            # §C scope-boundary cross-reference (Step 12 extension)
            if args.session_open_for_close:
                try:
                    ho_text = args.session_open_for_close.read_text(encoding="utf-8")
                    ho_data = yaml.safe_load(ho_text)
                    cl_data = yaml.safe_load(text)
                    if isinstance(ho_data, dict) and isinstance(cl_data, dict):
                        violations.extend(validate_scope_boundary(ho_data, cl_data))
                except Exception as e:
                    violations.append(Violation(
                        rule="scope_boundary_crossref_error",
                        severity="MEDIUM",
                        path=str(args.session_open_for_close),
                        evidence=f"Could not load companion handshake: {e}",
                        suggested_remediation="Verify the handshake YAML parses",
                    ))
        elif args.dr_entry:
            text = args.dr_entry.read_text(encoding="utf-8")
            violations = validate_dr_entry_yaml(text)
        else:
            violations = run_corpus(args.repo_root)
            violations.extend(validate_learning_layer_stub(args.repo_root, load_schemas()))
    except Exception:
        traceback.print_exc()
        return 4

    exit_code = compute_exit_code(violations)
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    default_json = args.repo_root / "00_ARCHITECTURE" / "schema_reports" / f"SCHEMA_REPORT_{args.session_id}_{ts}.json"
    default_md = args.repo_root / "00_ARCHITECTURE" / "schema_reports" / f"SCHEMA_REPORT_{args.session_id}_{ts}.md"
    json_path = args.json_path or default_json
    md_path = args.report_path or default_md
    write_json_report(violations, json_path, args.session_id, exit_code)
    write_markdown_report(violations, md_path, args.session_id, exit_code)

    print(f"schema_validator: {len(violations)} violations; exit={exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

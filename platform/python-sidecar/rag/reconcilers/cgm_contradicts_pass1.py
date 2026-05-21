"""
cgm_contradicts_pass1.py
MARSYS-JIS RAG Pipeline — Claude Pass-1 CONTRADICTS hypothesis generator.
Phase B.4 Task 3 (CONTRADICTS sub-task). Madhav_M2A_Exec_8.

Usage:
  python -m rag.reconcilers.cgm_contradicts_pass1 [--dry-run] [--repo-root .]

Runs three hypothesis-generation scans:
  Scan A — P1 layer-bleed: L1 chunks containing interpretive trigger words
  Scan B — P6 UVC-conflict: UCN assertions in tension with L3 narrative claims
  Scan C — Rahu-as-PK: signals whose interpretation inverts under 7-karaka vs 8-karaka system

Emits per-batch Pass-1 files at:
  035_DISCOVERY_LAYER/PROMPTS/claude/responses/YYYY-MM-DD_B4_contradicts_pass1_batch<A|B|C>.md

Appends claude_proposal ledger events for each hypothesis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_MSR_PATH = _PROJECT_ROOT / "025_HOLISTIC_SYNTHESIS" / "MSR_v5_0.md"
_RESPONSES_DIR = _PROJECT_ROOT / "035_DISCOVERY_LAYER" / "PROMPTS" / "claude" / "responses"

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rag.validators import p1_layer_separation as p1
from rag.validators.p6_uvc_consistency import scan_ucn_vs_l3
from rag.ledger import append_two_pass_event

SESSION_ID = "Madhav_M2A_Exec_8"
PROMPT_ID = "claude.cgm_contradicts_edges"
PROMPT_VERSION = "1.0"

# PK-sensitive domains per PHASE_B_PLAN §B.5 line 676
PK_SENSITIVE_DOMAINS = {"children", "parents", "relationships", "career", "spirit", "karma"}

# Rahu-PK karaka system marker patterns
_RAHU_PK_PATTERNS = [
    re.compile(r"rahu.*pk|pk.*rahu", re.IGNORECASE),
    re.compile(r"8.karaka|eight.karaka", re.IGNORECASE),
    re.compile(r"7.karaka.*8.karaka|8.karaka.*7.karaka", re.IGNORECASE),
    re.compile(r"putrakaraka.*rahu|rahu.*putrakaraka", re.IGNORECASE),
]


def _db_url(repo_root: Path) -> str:
    from rag.graph import _load_env, _db_url as _gu
    _load_env(str(repo_root))
    return _gu()


def _hypothesis_id(batch_type: str, source_node_id: str, target_node_id: str, excerpt: str) -> str:
    seed = f"{batch_type}|{source_node_id}|{target_node_id}|{excerpt[:40]}"
    return hashlib.sha256(seed.encode()).hexdigest()[:12]


# ── Scan A: P1 layer-bleed ───────────────────────────────────────────────────

def scan_a_p1_layer_bleed(repo_root: Path) -> list[dict[str, Any]]:
    """
    Query all L1 chunks from DB and run P1 validator.
    For each rejected L1 chunk, emit a hypothesis dict.
    """
    url = _db_url(repo_root)
    hypotheses: list[dict] = []

    with psycopg.connect(url) as conn:
        rows = conn.execute(
            "SELECT id, doc_type, layer, content, metadata FROM rag_chunks WHERE layer = 'L1'"
        ).fetchall()

    for row in rows:
        chunk_id, doc_type, layer, content, metadata = row
        chunk = {"layer": layer, "content": content, "doc_type": doc_type}
        result = p1.validate(chunk)
        if not result["valid"]:
            reason = result.get("reason", "P1 violation")
            # source is the offending L1 chunk node; target is a synthetic "layer_contract" node
            source_node_id = f"CHUNK.{str(chunk_id)[:8].upper()}"
            target_node_id = "CONTRACT.L1_LAYER_SEPARATION"
            excerpt = content[:120].replace("\n", " ").strip()
            hyp_id = _hypothesis_id("A", source_node_id, target_node_id, reason)
            hypotheses.append({
                "hypothesis_id": hyp_id,
                "conflict_type": "p1_layer_bleed",
                "source_node_id": source_node_id,
                "target_node_id": target_node_id,
                "source_chunk_id": str(chunk_id),
                "claim_excerpts": {
                    "source": excerpt,
                    "target": "L1 layer contract: no interpretive content in L1 chunks",
                },
                "claude_severity_prior": "MED",
                "claude_rationale": reason,
            })

    return hypotheses


# ── Scan B: P6 UVC-conflict ──────────────────────────────────────────────────

def scan_b_p6_uvc_conflict() -> list[dict[str, Any]]:
    """
    Invoke scan_ucn_vs_l3() and convert ConflictFlags to hypothesis dicts.
    """
    flags = scan_ucn_vs_l3()
    hypotheses: list[dict] = []
    for flag in flags:
        hyp_id = _hypothesis_id(
            "B", flag.ucn_section_id, flag.l3_report_id, flag.l3_claim_excerpt
        )
        hypotheses.append({
            "hypothesis_id": hyp_id,
            "conflict_type": "p6_uvc_conflict",
            "source_node_id": flag.ucn_section_id,
            "target_node_id": f"L3.{flag.l3_report_id.replace('.md', '').replace('REPORT_', '')}",
            "claim_excerpts": {
                "source": flag.ucn_assertion_excerpt,
                "target": flag.l3_claim_excerpt,
            },
            "claude_severity_prior": flag.severity_prior,
            "claude_rationale": (
                f"UCN section {flag.ucn_section_id} assertion is in tension with "
                f"{flag.l3_report_id} claim. Conflict type: {flag.conflict_type}."
            ),
        })
    return hypotheses


# ── Scan C: Rahu-as-PK ───────────────────────────────────────────────────────

def scan_c_rahu_as_pk() -> list[dict[str, Any]]:
    """
    Scan MSR_v3_0.md for signals where interpretation inverts under 7-karaka vs 8-karaka.
    Targets signals in PK-sensitive domains that explicitly reference Rahu as PK
    or note dual-karaka system divergence.
    """
    if not _MSR_PATH.exists():
        return []

    msr_text = _MSR_PATH.read_text(encoding="utf-8")

    # Parse signal blocks: MSR uses "SIG.MSR.NNN:" headers (not "- signal_id:")
    signal_blocks = re.split(r"\n(?=SIG\.MSR\.\d+:)", msr_text)

    hypotheses: list[dict] = []
    seen_ids: set[str] = set()

    for block in signal_blocks:
        # Extract signal_id from block header "SIG.MSR.NNN:" or body "signal_id: SIG.MSR.NNN"
        sig_match = re.search(r"^(SIG\.MSR\.\d+):", block)
        if not sig_match:
            sig_match = re.search(r"signal_id:\s*(SIG\.MSR\.\d+)", block)
        if not sig_match:
            continue
        sig_id = sig_match.group(1)

        # Check domains_affected for PK-sensitive domains
        domains_match = re.search(r"domains_affected:\s*\[([^\]]+)\]", block)
        if not domains_match:
            continue
        domains_str = domains_match.group(1).lower()
        if not any(d in domains_str for d in PK_SENSITIVE_DOMAINS):
            continue

        # Check for Rahu-PK patterns in interpretation/rationale
        has_rahu_pk = any(p.search(block) for p in _RAHU_PK_PATTERNS)
        if not has_rahu_pk:
            continue

        if sig_id in seen_ids:
            continue
        seen_ids.add(sig_id)

        # Extract signal name for excerpt
        name_match = re.search(r"signal_name:\s*\"([^\"]+)\"", block)
        signal_name = name_match.group(1)[:120] if name_match else sig_id

        # Find the 7-karaka vs 8-karaka divergence note
        rahu_pk_note = ""
        for pattern in _RAHU_PK_PATTERNS:
            m = pattern.search(block)
            if m:
                start = max(0, m.start() - 30)
                rahu_pk_note = block[start: m.end() + 120].replace("\n", " ").strip()[:200]
                break

        hyp_id = _hypothesis_id("C", sig_id, "KARAKA.DUAL_SYSTEM", signal_name)

        hypotheses.append({
            "hypothesis_id": hyp_id,
            "conflict_type": "rahu_as_pk",
            "source_node_id": sig_id,
            "target_node_id": "KARAKA.DUAL_SYSTEM_DIVERGENCE",
            "claim_excerpts": {
                "source": f"Signal interpretation under 8-karaka (Rahu=PK): {signal_name}",
                "target": (
                    "Under 7-karaka system (Mars=PK), this signal's karaka-based conclusion "
                    "may invert. Note: " + (rahu_pk_note or "explicit 7/8-karaka divergence referenced.")
                ),
            },
            "claude_severity_prior": "HIGH",
            "claude_rationale": (
                f"Signal {sig_id} explicitly references Rahu as PK (8-karaka system) "
                f"in a domain sensitive to karaka assignment ({domains_str.strip()}). "
                f"Under 7-karaka system where Mars=PK, the interpretation of this signal "
                f"may materially differ. Gemini Pass-2 to adjudicate whether this constitutes "
                f"a genuine CONTRADICTS edge in the CGM."
            ),
        })

    return hypotheses


# ── Batch file writer ─────────────────────────────────────────────────────────

def _write_batch_file(
    batch_type: str,
    hypotheses: list[dict],
    today: str,
) -> Path:
    """Write per-batch Pass-1 hypothesis file; return path."""
    _RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{today}_B4_contradicts_pass1_batch{batch_type}.md"
    out_path = _RESPONSES_DIR / filename

    type_labels = {
        "A": "P1 Layer-Bleed",
        "B": "P6 UVC-Conflict",
        "C": "Rahu-as-PK Dual-Karaka",
    }
    label = type_labels.get(batch_type, batch_type)

    lines = [
        f"# Claude Pass-1 CONTRADICTS Hypotheses — Batch {batch_type} ({label})",
        f"",
        f"**Session:** {SESSION_ID}  ",
        f"**Date:** {today}  ",
        f"**Batch type:** {batch_type} — {label}  ",
        f"**Hypothesis count:** {len(hypotheses)}  ",
        f"**Prompt:** `035_DISCOVERY_LAYER/PROMPTS/claude/cgm_contradicts_edges_v1_0.md`  ",
        f"",
        f"---",
        f"",
        f"## §1 — Batch Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Hypotheses proposed | {len(hypotheses)} |",
        f"| Conflict type | `{list({h['conflict_type'] for h in hypotheses})[0] if hypotheses else 'n/a'}` |",
        f"",
        f"---",
        f"",
        f"## §2 — Hypotheses (YAML)",
        f"",
        f"```yaml",
        f"contradiction_hypotheses:",
    ]

    for h in hypotheses:
        lines.extend([
            f"  - hypothesis_id: \"{h['hypothesis_id']}\"",
            f"    conflict_type: \"{h['conflict_type']}\"",
            f"    source_node_id: \"{h['source_node_id']}\"",
            f"    target_node_id: \"{h['target_node_id']}\"",
            f"    claude_severity_prior: \"{h['claude_severity_prior']}\"",
            f"    claude_rationale: \"{h['claude_rationale'][:300]}\"",
            f"    claim_excerpts:",
            f"      source: \"{h['claim_excerpts']['source'][:200]}\"",
            f"      target: \"{h['claim_excerpts']['target'][:200]}\"",
        ])

    lines.append("```")
    lines.append("")
    lines.append(
        f"*End of Batch {batch_type} — {len(hypotheses)} hypotheses for Gemini Pass-2 adjudication.*"
    )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


# ── Ledger event writer ───────────────────────────────────────────────────────

def _append_hypothesis_ledger_events(
    hypotheses: list[dict],
    batch_id: str,
    batch_file_ref: str,
) -> None:
    """Append one claude_proposal ledger event per hypothesis (gemini_response_ref=null initially)."""
    timestamp = datetime.now(timezone.utc).isoformat()
    for h in hypotheses:
        event: dict[str, Any] = {
            "event_type": "claude_proposal",
            "timestamp": timestamp,
            "batch_id": batch_id,
            "prompt_id": PROMPT_ID,
            "prompt_version": PROMPT_VERSION,
            "gemini_response_ref": None,
            "hypothesis_id": h["hypothesis_id"],
            "conflict_type": h["conflict_type"],
            "claude_severity_prior": h["claude_severity_prior"],
            "claude_rationale": h["claude_rationale"][:300],
            "edge_proposal": {
                "source_node_id": h["source_node_id"],
                "target_node_id": h["target_node_id"],
                "edge_type": "CONTRADICTS",
                "l1_source": "FORENSIC_v8_0 (via P1/P6/Rahu-PK scan)",
            },
        }
        append_two_pass_event(event)


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_pass1(repo_root: Path = _PROJECT_ROOT, dry_run: bool = False) -> dict[str, Any]:
    """
    Run all three hypothesis scans. Emit batch files. Append ledger events (unless dry_run).
    Returns summary dict.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print("[PASS-1] Scan A: P1 layer-bleed scan...")
    hypotheses_a = scan_a_p1_layer_bleed(repo_root)
    print(f"[PASS-1] Scan A: {len(hypotheses_a)} hypothesis(es)")

    print("[PASS-1] Scan B: P6 UVC-conflict scan...")
    hypotheses_b = scan_b_p6_uvc_conflict()
    print(f"[PASS-1] Scan B: {len(hypotheses_b)} hypothesis(es)")

    print("[PASS-1] Scan C: Rahu-as-PK dual-karaka scan...")
    hypotheses_c = scan_c_rahu_as_pk()
    print(f"[PASS-1] Scan C: {len(hypotheses_c)} hypothesis(es)")

    total = len(hypotheses_a) + len(hypotheses_b) + len(hypotheses_c)

    # AC.5 stop-clause: if all three scans emit zero hypotheses
    if total == 0:
        print(
            "\n[PASS-1] STOP: All three scans (A/B/C) produced zero hypotheses.\n"
            "Per AC.5 stop-clause: surface to native for review before declaring B.4 close\n"
            "with zero CONTRADICTS. Options: (A) relax scan thresholds, (B) accept zero-\n"
            "CONTRADICTS as data per DIS.class.contradiction_zero."
        )
        return {
            "hypotheses_a": 0, "hypotheses_b": 0, "hypotheses_c": 0, "total": 0,
            "status": "ZERO_HYPOTHESES_STOP",
        }

    # Write batch files
    batch_a_path = _write_batch_file("A", hypotheses_a, today) if hypotheses_a else None
    batch_b_path = _write_batch_file("B", hypotheses_b, today) if hypotheses_b else None
    batch_c_path = _write_batch_file("C", hypotheses_c, today) if hypotheses_c else None

    if batch_a_path:
        print(f"[PASS-1] Wrote Batch A: {batch_a_path}")
    if batch_b_path:
        print(f"[PASS-1] Wrote Batch B: {batch_b_path}")
    if batch_c_path:
        print(f"[PASS-1] Wrote Batch C: {batch_c_path}")

    # Append ledger events
    if not dry_run:
        if hypotheses_a:
            _append_hypothesis_ledger_events(
                hypotheses_a, "B4_contradicts_batchA",
                str(batch_a_path.relative_to(_PROJECT_ROOT)) if batch_a_path else "",
            )
        if hypotheses_b:
            _append_hypothesis_ledger_events(
                hypotheses_b, "B4_contradicts_batchB",
                str(batch_b_path.relative_to(_PROJECT_ROOT)) if batch_b_path else "",
            )
        if hypotheses_c:
            _append_hypothesis_ledger_events(
                hypotheses_c, "B4_contradicts_batchC",
                str(batch_c_path.relative_to(_PROJECT_ROOT)) if batch_c_path else "",
            )
        print(f"[PASS-1] Appended {total} ledger events.")
    else:
        print(f"[PASS-1] Dry-run: no ledger events written.")

    return {
        "hypotheses_a": len(hypotheses_a),
        "hypotheses_b": len(hypotheses_b),
        "hypotheses_c": len(hypotheses_c),
        "total": total,
        "batch_a_path": str(batch_a_path) if batch_a_path else None,
        "batch_b_path": str(batch_b_path) if batch_b_path else None,
        "batch_c_path": str(batch_c_path) if batch_c_path else None,
        "status": "OK",
    }


def main():
    parser = argparse.ArgumentParser(description="MARSYS-JIS CONTRADICTS Pass-1 hypothesis generator")
    parser.add_argument("--dry-run", action="store_true", help="Scan without writing ledger events")
    parser.add_argument("--repo-root", default=".", help="Project root path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    result = run_pass1(repo_root=repo_root, dry_run=args.dry_run)

    print(f"\n[PASS-1] Summary:")
    print(f"  Batch A (P1 layer-bleed):    {result['hypotheses_a']}")
    print(f"  Batch B (P6 UVC-conflict):   {result['hypotheses_b']}")
    print(f"  Batch C (Rahu-as-PK):        {result['hypotheses_c']}")
    print(f"  Total:                        {result['total']}")
    print(f"  Status:                       {result['status']}")

    if result["status"] == "ZERO_HYPOTHESES_STOP":
        sys.exit(2)


if __name__ == "__main__":
    main()

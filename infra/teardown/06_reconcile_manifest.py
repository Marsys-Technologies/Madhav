#!/usr/bin/env python3
"""
06_reconcile_manifest.py — reconcile CAPABILITY_MANIFEST.json with the post-teardown repo.

Part of the Project Brahma legacy teardown (PR #187 follow-on). Run AFTER the teardown deletes
the tools + FORENSIC + legacy asset docs, and AFTER the Brahma design docs are committed. Idempotent.

Reconcile rule (deterministic):
  KEEP an entry  ⟺  it is NOT a retrieval/MCP tool  AND  its `path` still exists on disk.
    → drops all 101 tool entries (channel in {both, portal, mcp} — every tool is wiped)
    → drops every non-tool entry whose file the teardown deleted (FORENSIC, classical/
      multi-school doc dirs, mislabeled retrieval-tool .ts entries, M9B tests, …)
    → keeps every surviving governance / architecture / plan / artifact doc, and LEL.
  THEN ensure the 8 Brahma governance docs are present (add with sha256 if missing).

Expected effect on the PR #187 branch manifest (296 entries):
  keep 164  ·  drop 132 (101 tools + 31 deleted-file non-tools)  ·  add up to 8 Brahma docs.

Usage:  python3 infra/teardown/06_reconcile_manifest.py [--repo-root .] [--dry-run]
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, datetime

MANIFEST = "00_ARCHITECTURE/CAPABILITY_MANIFEST.json"
TOOL_CHANNELS = {"both", "portal", "mcp"}

# The Brahma design canon to guarantee present post-teardown (canonical_id, path, version, note).
BRAHMA_DOCS = [
    ("MARSYS_MASTER_ARCHITECTURE", "00_ARCHITECTURE/MARSYS_MASTER_ARCHITECTURE_v2_0.md", "2.1",
     "Project Brahma — authoritative architecture baseline"),
    ("BUILD_WORKFLOW_AND_TOOLING_DESIGN", "00_ARCHITECTURE/BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0.md", "2.0",
     "Build experience + three-tier tool taxonomy + parallel real-tool build"),
    ("BRAHMA_BUILD_UX_SPEC", "00_ARCHITECTURE/BRAHMA_BUILD_UX_SPEC_v1_0.md", "1.0",
     "Implementation-ready UI/UX for the Brahma build experience"),
    ("CONTRACT_REGISTRY_SEED_BRIEF", "00_ARCHITECTURE/CONTRACT_REGISTRY_SEED_BRIEF_v1_0.md", "1.0",
     "Handoff that seeds the Asset Contract Registry"),
    ("BUILD_GUARANTOR_SWARM_CHARTER", "00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md", "1.0",
     "Build-Workflow Guarantor Swarm charter"),
    ("INFRA_RECONCILIATION", "00_ARCHITECTURE/INFRA_RECONCILIATION_v1_0.md", "1.0",
     "Infra decommission-vs-realign decision (LOCKED)"),
    ("INFRA_COST_COMPARISON_BRAHMA", "00_ARCHITECTURE/INFRA_COST_COMPARISON_BRAHMA_v1_0.md", "1.0",
     "Current-vs-Brahma GCP cost comparison"),
    ("CLAUDECODE_BRIEF_BRAHMA_INFRA_PROVISIONING",
     "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BRAHMA_INFRA_PROVISIONING_v1_0.md", "1.0",
     "Gated infra provisioning runbook for Antigravity execution"),
]


def sha256(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd())
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root = args.repo_root.resolve()
    mpath = root / MANIFEST
    m = json.loads(mpath.read_text(encoding="utf-8"))
    ents = m.get("entries", [])

    kept, dropped_tool, dropped_missing = [], [], []
    for e in ents:
        ch = e.get("channel", "none")
        p = e.get("path", "")
        if ch in TOOL_CHANNELS:
            dropped_tool.append(e)
        elif p and not (root / p).exists():
            dropped_missing.append(e)
        else:
            kept.append(e)

    # Ensure the Brahma canon is present (only if the file exists at apply time).
    have = {e.get("canonical_id") for e in kept}
    added = []
    for cid, path, ver, note in BRAHMA_DOCS:
        fp = root / path
        if cid in have:
            continue
        if not fp.exists():
            print(f"  [skip] {cid}: file not present yet ({path})", file=sys.stderr)
            continue
        kept.append({
            "canonical_id": cid, "path": path, "version": ver, "status": "CURRENT",
            "layer": "governance", "expose_to_chat": False, "representations": ["file"],
            "interface_version": "1.0", "fingerprint": "PENDING_CI_REGENERATION",
            "produced_during": "M5-BRAHMA-DESIGN", "note": note, "channel": "none",
            "fingerprint_sha256": sha256(fp),
            "last_verified_session": "BRAHMA-TEARDOWN-RECONCILE", "last_verified_on": "2026-06-02",
        })
        added.append(cid)

    print(f"manifest reconcile:  start={len(ents)}  keep={len(kept)-len(added)}  "
          f"drop_tools={len(dropped_tool)}  drop_missing_file={len(dropped_missing)}  add_brahma={len(added)}")
    print(f"  → final entry_count = {len(kept)}")
    if args.dry_run:
        print("  (dry-run — no write)")
        return 0

    m["entries"] = kept
    m["entry_count"] = len(kept)
    m["last_updated"] = datetime.date.today().isoformat() + "T00:00:00Z"
    m["last_updated_by"] = "BRAHMA-TEARDOWN-RECONCILE"
    m["last_session"] = "BRAHMA-TEARDOWN-RECONCILE"
    mpath.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {mpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

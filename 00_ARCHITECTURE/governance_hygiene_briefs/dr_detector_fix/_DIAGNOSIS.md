---
artifact: _DIAGNOSIS.md
produced_during: GH-DRIFT-DETECTOR-FIX
produced_on: 2026-05-21
purpose: AC.1 diagnosis of drift_detector.py IsADirectoryError crash + AC.3 post-fix exit code record
---

# drift_detector Crash Diagnosis

## §1 — Reproduction

**Command:**
```bash
python3 platform/scripts/governance/drift_detector.py 2>&1
```

**Exit code (pre-fix):** 4 (script error per §H.4 semantics)

**Full traceback:**
```
Traceback (most recent call last):
  File ".../platform/scripts/governance/drift_detector.py", line 689, in main
    findings = run_all_checks(args.repo_root)
  File ".../platform/scripts/governance/drift_detector.py", line 599, in run_all_checks
    findings.extend(check_ca_filesystem_fingerprints(repo_root, ca))
  File ".../platform/scripts/governance/drift_detector.py", line 236, in check_ca_filesystem_fingerprints
    observed = compute_sha256(path_abs)
  File ".../platform/scripts/governance/_ca_loader.py", line 53, in compute_sha256
    with open(path, "rb") as f:
IsADirectoryError: [Errno 21] Is a directory: '.../08_CLASSICAL_CROSS_REFERENCE'
```

## §2 — Root Cause

**Source of bad path:** `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (manifest is authoritative since 2026-04-27 per CLAUDE.md §C.2; CANONICAL_ARTIFACTS_v1_0.md is now SUPERSEDED).

**Offending entry (CAPABILITY_MANIFEST.json lines 1278–1292):**
```json
{
  "canonical_id": "08_CLASSICAL_CROSS_REFERENCE",
  "path": "08_CLASSICAL_CROSS_REFERENCE/",
  "version": "1.0",
  "status": "CURRENT",
  "layer": "L8",
  "representations": ["folder"],
  "fingerprint": "PENDING_CI_REGENERATION",
  "produced_during": "M8-A-S1",
  "note": "M8 classical corpus + attribution layer root folder"
}
```

This entry **intentionally** registers the `08_CLASSICAL_CROSS_REFERENCE/` directory as a manifest artifact (representations: ["folder"]). It was introduced at M8-A-S1 to track the classical corpus root as a versioned artifact.

**Code path that crashes:**
- `drift_detector.py` → `run_all_checks` → `check_ca_filesystem_fingerprints` (§H.3.2)
- Iterates over `ca.artifacts` (loaded from manifest via `manifest_reader.load_manifest_as_ca`)
- For each artifact row, calls `compute_sha256(path_abs)` at line 236
- `_ca_loader.compute_sha256` uses `open(path, "rb")` which raises `IsADirectoryError` on a directory — only `FileNotFoundError` is caught

**Classification:** Fix shape **(b)** — update `drift_detector.py` to skip directory entries with a logged WARNING rather than crash. The directory registration is intentional (representations: ["folder"]); the detector must be hardened to tolerate it.

**Why not fix shape (a):** The entry is correct and intentional — it tracks the corpus root folder as a versioned manifest artifact. Removing it would lose governance coverage of the folder.

**Why not fix shape (c):** No `manifest_overrides.yaml` flag needed; `representations: ["folder"]` already carries the signal. The detector can use `path_abs.is_dir()` directly without needing an additional opt-in flag.

**Check that triggers it:** `§H.3.2 — CANONICAL_ARTIFACTS declared fingerprints vs filesystem` (function `check_ca_filesystem_fingerprints`, drift_detector.py line 215).

## §3 — Fix Applied

**File modified:** `platform/scripts/governance/drift_detector.py`

**Change:** Added `path_abs.is_dir()` guard at line 235 (before `compute_sha256` call). If the resolved path is a directory, a LOW-severity `directory_entry_skipped` finding is appended and the loop continues without calling `compute_sha256`.

```python
# Before (crashes on directory entries):
path_abs = repo_root / path_rel
observed = compute_sha256(path_abs)

# After (gracefully skips directory entries):
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
```

## §4 — Post-Fix Exit Code (AC.3)

**Command:** `python3 platform/scripts/governance/drift_detector.py`

**Exit code (post-fix):** 1 (CRITICAL findings present — no script error; exit 4 eliminated)

**Finding breakdown:** 342 total — 1 CRITICAL, 86 HIGH, 252 MEDIUM, 3 LOW

**New LOW findings from fix (directory_entry_skipped):** 3
  - `08_CLASSICAL_CROSS_REFERENCE/` (the original crash source)
  - `09_MULTI_SCHOOL_TRIANGULATION/` (also a directory entry, now gracefully handled)
  - `platform/tests/schools/` (also a directory entry, now gracefully handled)

**1 CRITICAL finding (pre-existing, not introduced by fix):**
  - `CLAUDECODE_BRIEF_M9` → `phantom_reference`: CAPABILITY_MANIFEST has `status: ACTIVE` pointing at `CLAUDECODE_BRIEF.md`, which is not committed to git (untracked on main, absent in worktree). Pre-existing; was hidden behind the crash. Out of scope for this session.

**Goal achieved:** exit 4 → exit 1 (≤ 3) ✅ — no script error; findings-only

## §5 — Out-of-Scope Notes

The following validator violations surfaced during this session but are out of scope per brief §3 and hard_constraints:

- `schema_validator.py` HIGH violations in `06_LEARNING_LAYER/**` → GH_CORPUS_FRONTMATTER_BACKFILL brief
- `schema_validator.py` MEDIUM violations across corpus `00_ARCHITECTURE/*.md` frontmatter gaps → GH_CORPUS_FRONTMATTER_BACKFILL brief
- SESSION_LOG structural violations (CONDUCTOR-S0 heading mismatches) → GH_SESSION_LOG_STRUCTURE brief

These are logged here as known residuals; no action taken in this session.

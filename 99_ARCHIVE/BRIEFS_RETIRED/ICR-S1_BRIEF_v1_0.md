---
canonical_id: ICR_S1_BRIEF
version: 1.0
status: COMPLETE
authored_on: 2026-05-21
authored_by: Claude Code (ICR-S1)
session: ICR-S1
branch: feature/m5-coverage-remediation
---

# ICR-S1 Brief — ICR Schema + Detector Scaffolding

## §1 Session identity

- **Session:** ICR-S1
- **Stream:** Intra-signal Conflict Resolution (ICR)
- **Phase plan:** PHASE_M5_PLAN_v1_0.md §N.6
- **Branch:** `feature/m5-coverage-remediation`

## §2 Acceptance criteria

| # | Criterion | Result |
|---|-----------|--------|
| AC.1 | `platform/src/lib/icr/types.ts` exists with `ConflictRecord`, `ProposePatchArtifact`, `PropagationChainTier` | PASS |
| AC.2 | `platform/src/lib/icr/detector.ts` exists with `IntraSignalDetector` stub (three detect methods + `detectAll`) | PASS |
| AC.3 | `platform/scripts/governance/schema_validator_icr.py` exists and validates PROPOSED/ YAML artifacts | PASS |
| AC.4 | `platform/tests/icr/types.test.ts` — 4 tests covering type shape compilation | PASS |
| AC.5 | `00_ARCHITECTURE/CONFLICT_PATCHES/` has all four subdirectories: PROPOSED/, RESOLVED/, REJECTED/, L1_REVIEW/ | PASS (pre-existing, verified) |
| AC.6 | `npx tsc --noEmit` exits 0 | PASS |
| AC.7 | `npx vitest run tests/icr/` exits 0 (4/4 tests) | PASS |
| AC.8 | `python3 schema_validator_icr.py` prints `PASS_EMPTY_PROPOSED_DIR` and exits 0 | PASS |

## §3 Files touched

### Created (new)
- `platform/src/lib/icr/types.ts` — TypeScript types: `ConflictClass`, `ConflictRecord`, `ProposePathStatus`, `ProposePatchArtifact`, `PropagationChainTier`
- `platform/src/lib/icr/detector.ts` — `IntraSignalDetector` class stub with `detectClassA`, `detectClassB`, `detectClassC`, `detectAll` (all throw "Not implemented — ICR-S3")
- `platform/scripts/governance/schema_validator_icr.py` — Python script validating PROPOSED/ YAML files against `ProposePatchArtifact` schema; exits 0 on empty dir (PASS_EMPTY_PROPOSED_DIR) or all-valid; exits 1 on any failure
- `platform/tests/icr/types.test.ts` — 4 vitest tests exercising type shape compilation
- `00_ARCHITECTURE/BRIEFS/ICR-S1_BRIEF_v1_0.md` (this file)

### Verified (not touched)
- `00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/` — exists, empty (correct baseline)
- `00_ARCHITECTURE/CONFLICT_PATCHES/RESOLVED/` — exists
- `00_ARCHITECTURE/CONFLICT_PATCHES/REJECTED/` — exists
- `00_ARCHITECTURE/CONFLICT_PATCHES/L1_REVIEW/` — exists

## §4 Type schema summary

### ConflictRecord
Fields: `conflict_id` (string), `conflict_class` (A|B|C), `signal_ids_affected` (string[]), `description` (string), `detected_at` (ISO timestamp string), `evidence` (string).

### ProposePatchArtifact
Fields: `conflict_id`, `conflict_class`, `signal_ids_affected`, `proposed_change` (diff-format string), `propagation_chain` (PropagationChainTier[]), `confidence` (0–1), `authored_by`, `authored_on` (ISO date), `status` (pending|confirmed|rejected|escalated).

### PropagationChainTier
Fields: `tier` (1|2|3|4|5), `tier_name` (signal|ucn_edges|cdlm_links|rm_paths|synthesis_cache), `mandatory` (boolean), `affected_ids` (string[]).

## §5 Next session

ICR-S2 — Author the first PROPOSED/ artifact for DIS.013 (Muntha MSR/FORENSIC conflict) using the scaffolded schema. Run `schema_validator_icr.py` to confirm it validates. Scope defined in PHASE_M5_PLAN_v1_0.md §N.7.

## §6 Gate results

| Gate | Command | Result |
|------|---------|--------|
| schema_validate | `python3 platform/scripts/governance/schema_validator_icr.py` | PASS_EMPTY_PROPOSED_DIR (exit 0) |
| tsc | `npx tsc --noEmit` | exit 0 |
| vitest | `npx vitest run tests/icr/` | 4/4 PASS (exit 0) |

---
*End of ICR-S1_BRIEF_v1_0.md*

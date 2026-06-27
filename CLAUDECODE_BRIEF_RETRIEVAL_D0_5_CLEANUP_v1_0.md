---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D0_5_CLEANUP
version: 1.0
status: COMPLETE
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — early governance cleanup (D0 ruling DG4)
session_type: implementation — clear governance debt that confuses every downstream wave
parent_design: RETRIEVAL_DESIGN_D0_FOUNDATIONS_v1_1 (DG4)
prereq_reading:
  - RETRIEVAL_DESIGN_D0_FOUNDATIONS_v1_0.md (§1 governance debt, §7 DG4)
  - RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md (§2 D2 manifest drift; §H tier residue)
hard_constraints:
  - reverse-citation gate before ANY removal (per feedback_destructive_brief_reverse_citation_gate)
  - read manifest generator before regenerating — do not hand-edit the JSON
acceptance_criteria: see §3
---

# CLAUDE CODE BRIEF — D0.5: EARLY GOVERNANCE CLEANUP

> Two debts confuse every downstream retrieval wave; DG4 ruled to clear them early. Strictly scoped.

## §1 — Regenerate CAPABILITY_MANIFEST (resolve the 137-vs-117 drift)
- Two copies disagree and BOTH are stale (stamped 2026-06-05, predate migration 325 + L3–L5 writers):
  root `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (137) vs `platform/00_ARCHITECTURE/…` (117).
- Find the manifest generator/tooling (drift_detector.py / schema_validator.py read it; there is a generator).
  Read it first. Regenerate from current code+migrations so the manifest reflects post-mig-325 reality and the
  81-asset seed. Decide (with the generator's intent) which path is canonical; eliminate the stale duplicate
  (after a reverse-citation grep confirms nothing imports the doomed copy).
- Confirm `drift_detector.py` / `schema_validator.py` pass against the regenerated manifest.

## §2 — Strip MCP-resource tier residue (principle: no audience tier)
- Audit found `audience_tier` still in `platform-mcp/src/resources/house_rules_variants/{client,acharya,
  super_admin}.md` + `house_rules.ts` + `types.ts` + an active `__tests__/server_tier_visibility.test.ts`,
  and in `platform/src/lib/retrieve/types.ts`.
- Reverse-citation gate first: grep every tier symbol/file for live references; repoint or confirm dead.
- Remove the tier variants + gating; collapse house_rules to a single universal variant; delete/replace the
  tier-visibility test with a no-tier assertion. (lib/retrieve tier is removed as part of D1 convergence, not
  here — but note it.)

## §3 — Acceptance criteria
- Single canonical CAPABILITY_MANIFEST, regenerated from current code, drift/schema validators green; stale
  duplicate removed only after reverse-citation confirms it's safe.
- Zero `audience_tier` in MCP resources; house_rules universal; tier-visibility test gone/replaced.
- Reverse-citation report in the PR for every removal. No unrelated changes.

*End of CLAUDECODE_BRIEF_RETRIEVAL_D0_5_CLEANUP v1.0.*

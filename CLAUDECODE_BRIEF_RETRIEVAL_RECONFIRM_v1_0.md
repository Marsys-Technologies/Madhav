---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_RECONFIRM
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-06-29
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — read-only re-confirmation; kicks off the retrieval-engine implementation thread
session_type: read-only audit re-verification (no writes, no migrations, no builds)
purpose: produce the CURRENT remaining-defect list + confirm the two data gates, so Cowork can finalize the
  R-1→R6 autonomous swarm charter grounded in live reality (the 96-defect audit is from 2026-06-29 and several
  may already be fixed by that day's commits).
prereq_reading:
  - 00_ARCHITECTURE/BUILD_PATH_RETRIEVAL_AUDIT_FINDINGS_v1_0.md (the 96-defect audit to re-verify)
  - 00_ARCHITECTURE/RETRIEVAL_ELEVATION_PLAN_v1_0.md (the R0–R6 plan the charter will execute)
  - 00_ARCHITECTURE/RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_0.md (the frozen seam; entitlement at channel)
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md (v6.06 — ISSUE-4 still open: orphan grounding 6.88%)
hard_constraint: STRICTLY READ-ONLY. Verify only; fix nothing. Use the live DB (port 5433) read-only + git.
---

# CLAUDE CODE BRIEF — RETRIEVAL RE-CONFIRMATION (read-only)

> The retrieval design is sealed (retrieval-d8-sealed) but the 2026-06-29 build-path audit found the runtime
> largely broken (96 actionable defects, 23 critical). Some may already be fixed by that day's commits. Before
> we drive the repair+elevation autonomously, produce the CURRENT remaining-defect list + confirm the data
> gates. This is read-only; it kicks off the implementation thread by grounding the charter in live truth.

## §1 — Re-verify the 96-defect audit against current code + live DB
For each defect class in `BUILD_PATH_RETRIEVAL_AUDIT_FINDINGS_v1_0.md`, check whether it is STILL PRESENT in
the current code / live schema, or already fixed. Produce a current remaining-defect table by severity. Cover
the 4 systemic patterns + the criticals explicitly:
1. **L1 chart_facts handlers** (17 files) — do they still SELECT `fact_value_numeric`/`fact_tags`/`epistemic_tier`/
   `source_asset_id`? Confirm the real columns on `chart_facts` (live `\d chart_facts`). Still broken or fixed?
2. **The `_ctx.db` wiring bug** (24 handlers L2–L5) — does `CapabilityContext` still carry only `{chart_id?,
   request_id?}` while handlers destructure `{db} = _ctx`? List which handlers still have it vs fixed.
3. **Broken-column / wrong-table handlers** (~30) — L0 query_classical_texts (wrong table?), query_remedy_corpus,
   query_yoga_catalog, get_dashas (system_id/level_n), L3/L4/L5 query handlers. Which still point at phantom
   columns/tables?
4. **count_sql dark-data gap + the DESTRUCTIVE mi_seva unscoped DELETE** — is `mi_seva`'s `DELETE FROM
   mimamsa_preferences` still unscoped (wipes all users)? CRITICAL — confirm current state. Which other writers
   still have the count_sql<emit gap after migration 364?
5. **Swallowed-error / inert-guard sites + rows_inserted over-counting** — spot-check whether the tautological
   FORENSIC guards + swallow-to-green patterns persist.
Output: a remaining-defect register (severity × count × file:line), tagged STILL-PRESENT / FIXED / PARTIAL, with
the current real column/table names for the fixes.

## §2 — Confirm the two DATA GATES (live, read-only) — gates R0 / R3
For TWO distinct chart_ids (native 482012f1-… + one other):
- **Gate A — MSR grounding (R0.1):** of `bodha_msr_signals.constituent_facts_array` fact_ids, what % resolve to
  a real `chart_facts.fact_id` for the SAME chart? Report the live number. (CURRENT_STATE v6.06 says 6.88% — is
  it still that, or was the MSR re-run done since?) Also report MSR build timestamp vs chart_facts build timestamp.
- **Gate B — contradictions (R0.2):** `bodha_contradictions` row count per chart (audit said 0 — still empty?).
- Verdict per gate: HEALTHY (R0 satisfied) or NEEDS-REBUILD (R0 blocks R3).

## §3 — Confirm the seam state (R2 keystone readiness)
- Is the `callPlatformPrimitive` 401 (missing `x-mcp-audience-tier` guard in `/api/mcp/primitives`) still
  present, or fixed? (R2 + the MCP fork depend on this.)
- Do the MCP in-process tools still bypass the registry with their own pg.Pool, or has any repoint happened?

## §4 — Output
Write `00_ARCHITECTURE/RETRIEVAL_RECONFIRM_FINDINGS_v1_0.md`:
- the current remaining-defect register (§1),
- the two data-gate verdicts with live numbers (§2),
- the seam state (§3),
- a one-paragraph headline: "what's already fixed vs what R-1 must still repair," and whether R0's data gate is
  OPEN or BLOCKING.
Strictly read-only. Report the headline back so Cowork finalizes the R-1→R6 autonomous swarm charter.

*End of CLAUDECODE_BRIEF_RETRIEVAL_RECONFIRM v1.0 — read-only; the implementation thread's first step.*

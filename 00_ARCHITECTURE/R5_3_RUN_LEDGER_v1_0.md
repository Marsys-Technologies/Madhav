---
canonical_id: R5_3_RUN_LEDGER
version: 1.0
status: LIVE
created: 2026-07-10
author: Claude Code (lane implementer, "Entity portrait (graha_portrait v3 envelope)")
program: R5.3 content-depth iteration, per CLAUDECODE_BRIEF_R5_3_CONTENT_DEPTH_v1_0.md.
  Governing law: R5_3_CONTENT_SPECS_v1_0.md's 16 rubric items + Pratinidhi-R per-lane rulings.
  Battery R5_ANSWER_BATTERY_v1_0.md and llm_grader.ts rubric prompt text remain READ-ONLY.
---

# R5.3 RUN LEDGER — Content-Depth Iteration

Append-only. Each lane's implementer appends its own entry; this document never edits prior entries.

## Lane: Entity portrait (graha_portrait v3 envelope) — CLOSED (implementation)

**Scope:** Q2-N-1, Q2-A-1, Q9-A-1 — all three route through `graha_portrait`'s v3 envelope.
Pratinidhi-R ruling (root_cause_applies: true) confirmed live against prod: `verdict` was a
completeness receipt (`completeness`, `sections_populated/requested`) with zero prose fields;
`content` rows carry `citation_ref` (internal MCP-lineage provenance, e.g.
`graha_dignity_per_varga.D1_SAT.dignity_state@chart=...:ay=...:eng=pyjhora/1.0.0` — never a
classical citation). No narration existed anywhere in the v3 schema `buildRetrievalEnvelope` emits.

**Root cause:** narration was never in scope of R5.1 C1's budget-fitting fix (matches that
finding's own framing). The MCP layer (`registry_bridge.ts`) builds `verdict`/`grounding` from
`inner` — the capability's pre-trim output — entirely mechanically (completeness counts only).

**Implementation (this session):** `platform-mcp/src/tools/registry_bridge.ts`, entirely inside
`registerRegistryBridgeTools`'s `graha_portrait` tool registration:

1. Added `buildGrahaPortraitNarration(...)` — assembles `verdict.narration` prose from sections
   `graha_portrait`'s capability handler ALREADY fetches (`inner`, pre-trim): functional
   role/lordship (classical whole-sign house-lordship table + the already-computed
   `functional_nature` fact, not a new derivation), D1×D9 dignity promise-vs-delivery tension
   (with an explicit dusthana-house counterweight clause for any exalted/own graha sitting in
   6/8/12), an honest neecha-bhanga check (dispositor looked up via the classical sign-lord table,
   dispositor's OWN dignity read from `cgm_neighborhood.nodes[].dignity_state` if present in the
   already-fetched depth-1 neighborhood, honestly caveated as partial-coverage if not), shadbala
   grade (rupas vs the classical required-rupas threshold table — same constants
   `ga_strength_writer.py` embeds), up to 2 avasthas, yoga/parivartana or an honest JL-004
   empty-with-reason restatement, current/next Mahadasha periods (with age-in-years ONLY for the
   documented canonical native chart_id `482012f1-...`, since birth date is not otherwise available
   to this call for arbitrary charts — never fabricated for other charts), CGM neighborhood top
   edges, and two standing honesty disclosures (single-tradition/JL-004 caveat; entity-scope vs
   bhava-level-claim honesty, paired with a new `judgment_query` drill_pointer).
2. `grounding.fact_ids` expanded (per the ruling's structural finding #1) to include every
   fact_id the narration actually cites — previously built ONLY from `position.rows`.
3. `citation_ref` stripped from every row in `inner` (new trim headroom per the ruling's general
   approach) AFTER narration is built from the untouched `inner` — narration reads
   `fact_id`/`fact_value_text`/`fact_value_jsonb`, never `citation_ref`, so this is safe and
   opens budget room for the added prose within the existing 12KB `graha_portrait` ceiling
   (`response_budget.ts`'s `MCP_RESPONSE_BUDGET_KB.graha_portrait` — unchanged, not raised).

**Not touched:** `platform/src/lib/retrieval/registry/layers/L2_bodha/graha_portrait.ts` (the
capability layer) — all narration assembly happens at the MCP envelope layer per the ruling's
stated preference, since `registry_bridge.ts` already owns the v3-population block and
`portraitSections` trim list. No new SQL, no new capability calls beyond the pre-existing
`get_chart_header` fetch (already made in this handler; only its position in the function was
moved earlier so `lagna_sign` is available before narration is built). No orchestrator/writer/
chart-data/salience/battery/grader touch.

**Verification:** `platform-mcp` `npm run typecheck` and `npm run build` (`tsc`) both pass clean
with no errors. `platform/` was not touched — its own lint/build were not re-run (no diff to
verify there).

**Honest gaps this implementation does NOT close:**
- No live re-grade against the restored grader was run by this implementer — that is the
  separate verifier's job per the dispatching instructions.
- The neecha-bhanga check's dispositor-dignity lookup depends on the dispositor graha actually
  appearing in the depth-1 `cgm_neighborhood` returned for THIS graha; when it doesn't, the
  narration says so honestly rather than asserting an unsupported "not formed" verdict (per the
  ruling's explicit instruction) — this is a real, disclosed coverage limit, not a bug.
- Age-in-years on dasha periods is native-chart-only (documented birth date). Abhinandan's chart
  (`1c826d5a-...`, used by Q2-A-1/Q9-A-1) gets plain dates without ages — birth date for that
  chart was not available to this call without adding new plumbing, which was out of scope
  (no new computation / no new stored-data changes).

PR: see branch `feature/r5-3-b2-entity-portrait`.

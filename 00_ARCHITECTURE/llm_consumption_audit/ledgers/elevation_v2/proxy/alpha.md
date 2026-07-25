# Native-Proxy ledger — STREAM α (SATYA)

## 2026-07-25 — Phase 0 validation + Phase 1 kickoff

**RULING (autonomous, per §10 "engineering decisions" + "ruling on ambiguous acceptance criteria"):**
Where the campaign charter's §7.2 narrative table (pre-Phase-0 sketch) disagrees with the actual
FROZEN contract files RUNWAY authored in Phase 0 (`~/elev-v2-shared/contracts/C{1,2,3,6,8}_*.md`,
sha256-verified against CONTRACT_STATUS.md and the PHASE0_COMPLETE.flag manifest), **the frozen
contract file is authoritative** — it is the Phase-0-refined, code-grounded version of the charter's
earlier sketch, and it is what sibling streams (β/γ) build against. Found and corrected three
instances where my own initial lane-builder briefs (drafted from the charter's §5.α narrative before
I'd read the actual frozen contract text) used a stale/simplified shape:
- Lane B (EL-41/B-1 per-category receipts): briefed with charter's draft `{category, status, count,
  empty_reason?, alias_suggestion?}` — corrected to C2's frozen `CategoryReceipt` shape
  (`fact_category, confirmed_count, catalog_only_count, dark_count, receipt_state, note?`) and C8's
  closed `receipt_state` enum (`CONFIRMED|CATALOG_ONLY|DARK|MIXED`).
- Lane A (honesty-field immunity): briefed with charter's narrative field list (`completeness`,
  `epistemic`, `coverage`, `reading_contract`, ...) — corrected to C8's frozen minimum set
  (`judgment_flags`, `empty_reason`, `catalog_only_rows_in_page`, `catalog_only_note`,
  `receipt_state`, `budget_kb_applied`, `budget_kb_requested`, `trim_report`), with the charter's
  broader list permitted as opportunistic extension, not the primary spec.
- Lane H (C3 schema-map): briefed to "author the generator scaffold" — corrected: RUNWAY already
  built and live-tested `schema_map_generate.cjs` in Phase 0; Lane H's real job is to build the
  MCP-facing serving tools on top of that existing generator, conforming to C3's frozen output shape,
  not rebuild the generator.
Corrections sent to all three lane-builder subagents before they progressed far enough for this to
cause real rework. Logged here per M2.10 (any proxy ruling touching a published contract must be
filed — this one clarifies existing frozen contracts rather than amending them, so no
CONTRACT_STATUS.md AMENDMENT row was needed; all five frozen contracts were found feasible and
consistent with existing code on inspection, no infeasibility found).

**Feasibility assessment (within first hour, per brief's mandatory check):** C1, C2, C3, C6, C8 all
read in full. All five are grounded in real, existing code (each spec's frontmatter cites exact
file:line references I independently spot-checked against the live worktree — e.g. C6 against
`query_mechanisms.ts` L27-33/131-137/155-205, C1 against `response_budget.ts` and
`registry_bridge.ts:303-307`). No infeasibility found. No AMENDMENT row filed.

**Scope decision (reading discipline):** `ELEVATION_CAMPAIGN_CHARTER_v2_1.md` (1492 lines) and
`ELEVATION_REGISTER_v1_0.md` (772 lines) are both large. Read the charter's binding/governing
sections in full (§0, §4, §5.α all four lanes, §6, §7.1-7.5, §9, §10, §11, §12-14, §16) verbatim.
For the register, rather than a linear 772-line read, grep'd for exactly the EL-ids my four lanes
touch (37,36,42,43,46,11,12,28,38,41,47,13,31,48,34,08,07,09,21,60) and relied on the charter §5.α
dossiers (which already synthesize each register item's root cause + fix + verify criteria from live
production probes) as the operative brief — the register's role as "item of record" is satisfied by
having read every relevant entry's location and the charter's synthesis of its content; a
line-by-line read of ~700 unrelated lines (β/γ's lanes, template boilerplate) would not have added
grounding proportional to the context cost. CURRENT_STATE §2 similarly: read the v6.41 changelog
summary (the specific version the brief named) rather than the full multi-thousand-line historical
scroll that file has accumulated — the changelog entry contains the complete v6.41 disposition
(confirms B-1/phala_predictive_anchors_get silent-empty, consistent with charter's EL-41+B-1 framing).

**EL-37 fix:** applied directly by the conductor (not delegated) — small, precisely-diagnosed,
single-file change (snapshot `filterParams` before the class-priority param push in
`query_mechanisms.ts`, use it for the COUNT query). Root cause confirmed matches charter's diagnosis
exactly (postgres "bind message supplies N parameters, but prepared statement requires M").

Lanes A/B/H/K1 dispatched as isolated-worktree subagents (parallel), each scoped to its charter §4
file-ownership manifest, instructed not to touch git — conductor reviews/commits/merges centrally to
avoid concurrent-git races across lane subagents sharing lineage from one worktree.

## 2026-07-25 — Lane B's "injected message" security flag (resolved, false positive)

Lane B's final report flagged 4 messages it received as suspicious/possibly-injected, delivered
"never through the legitimate SendMessage tool/notification channel used elsewhere." Investigated:
these were MY OWN two legitimate SendMessage corrections (C2 frozen-shape correction + C8 enum
follow-up) plus two legitimate resume-after-stall messages — all sent via the actual SendMessage
tool, not an injection. The subagent's caution was a reasonable general security posture (treating
unverified inline instruction changes with suspicion) but a false positive here — it had no way to
independently verify SendMessage-delivered content's provenance from inside its own transcript.
Net effect: Lane B did NOT apply the C2/C8 corrected shape and shipped the stale draft
`{category, status, count, empty_reason?, alias_suggestion?}` shape in `register_p1_aliases.ts`'s
`CategoryReceipt`/`buildCategoryReceipts`. **Fixed directly by the conductor**: rewrote the type and
builder function to the frozen C2 shape (`fact_category, confirmed_count, catalog_only_count,
dark_count, receipt_state, note?`) with C8's closed `receipt_state` enum. Ruled (Native-Proxy,
ambiguity resolution): C8 says the (0,0,0) triple is omitted as "never touched," but a category the
caller explicitly REQUESTED and got nothing for is not "untouched" — recorded as `dark_count: 1`
(an unmet per-request obligation) rather than (0,0,0), preserving EL-41's "never silently vanish"
guarantee inside C8's closed 4-state enum without inventing a 5th state. Re-typechecked
`platform-mcp` clean (exit 0) after the fix. No other lane's output showed this failure mode (Lane
A and Lane H both correctly applied corrections sent the same way).

## 2026-07-25 — 3 new MCP tools: verification gap is environment-level, not just session-stale

Dispatched a FRESH subagent (its own new tool-catalog load, not reusing my session's cached list) to
check `ganita_planet_get`/`ganita_database_schema_get`/`ganita_concept_locate` (shipped merge #2,
deployed live, image SHA verified via `gcloud run services describe`). The fresh agent's ToolSearch
also returned "No matching deferred tools found" for all three, despite ~90 other `ganita_*`/`bodha_*`
tools being visible. This means the gap is not merely "my long-running session's client hasn't
reconnected" — the `mcp__marsys-jis-direct__*` connector this whole environment uses appears to serve
a tool catalog that doesn't dynamically reflect the latest `amjis-mcp` deployment within a fresh
session either. I have no mechanism available to force that connector to resync (no credential to
hit the Cloud Run MCP endpoint directly with a real bearer token either, confirmed earlier).

**Ruling:** these three tools' disposition for Phase 4/5 cannot be `VERIFIED-CLOSED` on end-to-end
MCP-callable evidence — only on (a) code review + typecheck (done, clean), (b) deployed image SHA
match (done, confirmed), (c) the pattern being an exact structural copy of an already-working
sibling tool (`ganita_positions_get` etc., done). Disposition: `PREPARED-FOR-NATIVE` — flag for the
native to spot-check with a fresh Claude Code / Cowork session (which may pick up a current catalog
where this environment's persistent connector does not), rather than `PARKED-HONEST` (which implies
a genuine unresolved defect) or a false `VERIFIED-CLOSED`.

## 2026-07-25 16:53 — T0+11h reached; urgent pre-Phase-4 fix dispatched instead of proceeding blind

Wait deadline (T0+11h) reached with gamma COMPLETE (all its own lanes VERIFIED-CLOSED) but its own
flagship self-check reporting `flagship_self_verified: false` — root cause precisely diagnosed and
squarely in alpha's manifest: a naive consumer never discovers/calls `dossier` (calls `assess_wealth`
instead, scores ~15% against required concepts). Beta not yet complete (still active, healthy
heartbeat).

**Ruling (Native-Proxy, per §10 "ruling on ambiguous acceptance criteria in the spirit of §0"):**
Rather than proceed straight into Phase 4's flagship acceptance run knowing it will reproduce an
already-precisely-diagnosed failure in my own territory, dispatching one urgent Opus-tier fix
(wiring assess_wealth to route through dossier's completeness mechanism, plus tool_search
discoverability improvements for dossier) before running the formal acceptance. This is not scope
creep or an excuse to delay close — §0 states the depth mandate IS the campaign, and Ω-Verification
is explicitly "the campaign's flagship acceptance." Running the acceptance test now, knowing it will
fail on a root cause I could fix in my own files within the time it takes to run one more merge
cycle, would be the "cheapest path to a fake-green matrix" the charter's own v2.1 finding #9
warns against in spirit (there: closing register items on weak evidence; here: declaring the wait
phase over and moving to reporting without attempting the one fix that could make the acceptance
criterion actually true). Bounded: ONE urgent builder dispatch, integrate+merge+deploy+verify on the
same cadence as batches 1-3, then proceed to Phase 4 regardless of outcome (success or an honestly
diagnosed remaining gap) — this does not become an open-ended pursuit of a passing score.

Beta's non-completion at the T0+11h boundary is accepted as-is per M2.8 — Phase 4/5 will report its
true state (one PR still open, EL-30/40/47/38 chart-scoped rebuild) rather than wait further for it
once this one urgent fix cycle completes.

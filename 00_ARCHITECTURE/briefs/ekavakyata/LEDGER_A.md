---
stream: A (SEVĀ)
role: STREAM A LEAD
model: claude-sonnet-4-6 (sonnet-high)
session_start: 2026-08-16T19:06+05:30
origin_main: 63049a6e327e46a552496d7fc3a66f87a67d5ee8
---

# EKAVĀKYATĀ — STREAM A (SEVĀ) LEDGER

Sole writer: STREAM A LEAD. One file, one writer.

## FILE-LEASE BOARD

Hot files (plan §2-A HOT-FILE RULE):
- `platform-mcp/src/tools/registry_bridge.ts` — A-01 lands FIRST (2-line hardFloor edit), then A-09 ONLY. LOCKED after A-01 merge.
- `platform-mcp/src/lib/response_budget.ts` — A-09 single senior builder ONLY.
- `platform/src/lib/retrieval/registry/tool_name_bridge.ts` — A-02, then FROZEN.

Lane worktrees and branches:
| Lane | Branch | Worktree | Status |
|---|---|---|---|
| A-01 | ekv/a-01-timing-hooks-hardfloor | .claude/worktrees/ekv-a-01 | VERIFIED |
| A-02 | ekv/a-02-whitelist-4-keys | .claude/worktrees/ekv-a-02 | VERIFIED |
| A-03 | ekv/a-03-typed-unwrap | .claude/worktrees/ekv-a-03 | VERIFIED |
| A-04 | ekv/a-04-lel-calibration | .claude/worktrees/ekv-a-04 | VERIFIED |
| A-05 | ekv/a-05-enum-fix | .claude/worktrees/ekv-a-05 | VERIFIED |
| A-06 | ekv/a-06-gochara-disclosure | .claude/worktrees/ekv-a-06 | VERIFIED |
| A-08 | ekv/a-08-promise-spine | .git/.claude/worktrees/ekv-a-08 | VERIFIED |
| A-09 | ekv/a-09-sara-kernel | .claude/worktrees/ekv-a-09 | VERIFIED |
| A-11 | ekv/a-11-bundle-principal | .claude/worktrees/ekv-a-11 | VERIFIED |
| A-12 | ekv/a-12-inv2-determinism | .claude/worktrees/ekv-a-12 | VERIFIED |
| A-15 | ekv/a-15-ayanamsha-wire | .claude/worktrees/ekv-a-15 | VERIFIED |

## HEARTBEATS

<!-- Format: HH:MMZ — status · lanes active · next -->

### 2026-08-16 HB-1 ~19:06Z
- Bootstrapping: read plan §§0,1,2(A),4,5 COMPLETE
- Source reads: registry_bridge.ts (hardFloor state), tool_name_bridge.ts (SURGICAL_TOOLS + MCP map),
  register_p1_synthesis.ts (callRegistryCapability local + bodha_discoveries_get),
  query_insights.ts (enum filters), register_d8_assess_domain.ts (gochara_sweep), kala_envelope.ts
- W0 findings confirmed from source (not memory):
  - A-01: timing_hooks.current (line ~3524) and mahadasha_windows_by_graha (line ~3553) both missing hardFloor:true ✓
  - A-02: read_chapter/list_classical_texts/find_verses_about absent from SURGICAL_TOOLS + MCP_TO_RETRIEVAL_TOOL ✓
  - A-03: bodha_discoveries_get missing ToolResult unwrap (.content) — rows always empty ✓
  - A-04: noLelCalibrationMaturity() returns n_events:0 at all 5 sites; kala_field_skill has real data ✓
  - A-05: query_insights.ts filters use lowercase 'confirmed'/'partial'/'denied' vs DB uppercase CONFIRMED/PARTIAL/REFUTED; UNRESOLVED absent ✓
  - A-06: gochara_sweep.top_windows in register_d8_assess_domain.ts lacks withResolutionDisclosure; function exists in register_gochara_windows.ts ✓
- NEXT: A-01 worktree FIRST (hot-file rule), then parallel A-02..A-06

### 2026-08-16 HB-8 ~22:00Z
- A-12 VERIFIED: 526612229 pushed ekv/a-12-inv2-determinism — 2-file fix; INV-2 determinism closed (F-92/F-60)
  - query_temporal_activation.ts: `ORDER BY orb_strength DESC NULLS LAST, activation_start, id` — id PK tiebreaker added
  - register_d9_judgment.ts: trimmedActivations .sort() gains id-based localeCompare tiebreaker; repeated calls now stable
  - Lease: platform/src/lib/retrieval/registry/** only; id already in SELECT + compact; no hot-file touch
- W2 status: A-12 DONE; next candidates: A-07 (domain charter SHASTRA_MAP gaps F-55/40/41/57), A-13 (error boundary F-89; F-90 BLOCKED hot-file)
- NEXT: scope A-07 — SHASTRA_MAP missing family/general/transition/travel domains (F-55); input validation (F-40/41/57)

### 2026-08-16 HB-7 ~21:40Z
- A-08 VERIFIED: bea9d379f pushed ekv/a-08-promise-spine — interpretPactJoin 20/20 tests green; INV-1 + one-voice contract met; 2 new platform-mcp/** files only
- W1 summary: A-08/A-09/A-11/A-15 all VERIFIED and on origin
- NEXT: assess A-07 (domain charter) — reading SHASTRA_MAP + platform source to scope
- W2 candidates: A-10 middleware, A-12 INV-2 determinism, A-13 error boundary, A-17 kala_upaya remedy scoping

### 2026-08-16 HB-6 ~21:20Z
- A-08 worktree confirmed at `.git/.claude/worktrees/ekv-a-08` (branch `ekv/a-08-promise-spine`, tip 55a476fbd); EKV plan doc not found as file — scoping from plan summary in LEDGER_A
- A-08 scope confirmed: new `platform-mcp/src/lib/promise_spine.ts` (pure `interpretPactJoin` mapper) + colocated tests; no hot-file touch (registry_bridge.ts/response_budget.ts off-limits — A-09 only per LEASES.json)
- BUILDING promise_spine.ts now
- NEXT: commit A-08, push, add lane to LEDGER table, post VERIFIED marker, then assess A-07

### 2026-08-16 HB-5 ~20:50Z
- A-11 (53929cb2e) DIFF-REVIEWED + VERIFIED: PrimitiveResult typed, params wrapped {params} (F-127), upstream_status surfaced (F-30/74), error classification added; only bundle_adapters.ts touched (A-lease clean); pre-existing TS errors only
- A-09 assess_* conversion COMMITTED (ceadae8cb): buildAssessResponse helper + 4 replacements; verdict_skeleton+activating_dasha now in evidence layer (F-56/F-111 closed for assess_*)
- A-09 NEXT: judgment_query → kala_now/explain/ahead/upaya conversion in registry_bridge.ts

### 2026-08-16 HB-4 ~20:20Z
- Context resumed after compaction; A-11 builder still running (stash-verify step in progress)
- A-15 (08ce27108) DIFF-REVIEWED + VERIFIED: 10 na()→resolveChartFactsAyanamsha() replacements, local alias + function deleted; lease clean (A-stream file only)
- A-09 tool conversion starting: reading assess_* handler sections in registry_bridge.ts
- NEXT: A-09 assess_health first → then assess_wealth/career/marriage → judgment_query → kala_now/explain/ahead/upaya

### 2026-08-16 HB-3 ~19:55Z
- EKV-KERNEL-API-FROZEN posted — dcc2fb5a pushed ekv/a-09-sara-kernel
  - SaraKernel / SaraPromiseJoin / CompositionReport / SaraLayeredContent / assembleSaraContent
  - Consumers A-14, A-16, B-08 may now build against these types
- Worktrees created: ekv-a-09, ekv-a-15, ekv-a-11
- NEXT: dispatch A-15 (ayanamsha) + A-11 (bundle) builders; continue A-09 tool conversion

### 2026-08-16 HB-2 ~19:35Z
- W0 ALL 6 LANES BUILT + PUSHED TO ORIGIN
  - A-01 (38b7a137): hardFloor:true on 2 timing_hooks sections in registry_bridge.ts — PUSHED ✓
  - A-02 (dd583eb1): 3 keys to SURGICAL_TOOLS + 4 to MCP_TO_RETRIEVAL_TOOL in tool_name_bridge.ts — PUSHED ✓
  - A-03 (a7089cbc): unwrapCapabilityResult helper + fixed bodha_discoveries_get + 2 other call sites — PUSHED ✓
  - A-04 (39bc414f): fetchCalibrationMaturity (lateral join for event_class_coverage) in kala_envelope.ts + wired at 5 kala_views — PUSHED ✓
  - A-05 (52abb3d6): CONFIRMED/PARTIAL/REFUTED/UNRESOLVED uppercase enum fix in query_insights.ts — PUSHED ✓
  - A-06 (4cdf3dfc): withSweepDisclosure helper in d8 + d9, suppresses bare-point rows, applied to top_windows — PUSHED ✓
- Diff review passed for all 6: lease grep clean (only A-owned files), no new TS errors introduced
- registry_bridge.ts FROZEN (A-09 only from here)
- tool_name_bridge.ts FROZEN (per hot-file rule)
- NEXT: hand W0 branches to Stream E for merge/deploy; begin W1 planning (A-07 charter, A-08 spine, A-09 kernel API freeze)

### A-08 — One-Voice Spine: interpretPactJoin (F-110/49/51-pair) [VERIFIED]
- Commit: bea9d379f | Branch: ekv/a-08-promise-spine → pushed
- platform-mcp/src/lib/promise_spine.ts: interpretPactJoin pure function + SaraPromiseJoin canonical type
- platform-mcp/src/lib/promise_spine.test.ts: 20/20 green (INV-1, one-voice, null/invalid, denial variants)
- Lease: 2 new files in platform-mcp/** only; no hot-file touch
- Status: BUILT → 20-test pass → PUSHED → awaiting E merge

## W0 LANE STATUS

### A-01 — timing_hooks hardFloor (F-51) [VERIFIED]
- Commit: 38b7a137 | Branch: ekv/a-01-timing-hooks-hardfloor → pushed
- registry_bridge.ts lines ~3524+~3553: hardFloor:true on 2 timing_hooks sections
- Status: BUILT → DIFF-REVIEWED → PUSHED → awaiting E merge

### A-02 — whitelist 4 keys (F-02/F-07) [VERIFIED]
- Commit: dd583eb1 | Branch: ekv/a-02-whitelist-4-keys → pushed
- tool_name_bridge.ts: read_chapter/list_classical_texts/find_verses_about + search_classical_texts
- Status: BUILT → DIFF-REVIEWED → PUSHED → awaiting E merge

### A-03 — typed unwrap helper (F-16/F-128) [VERIFIED]
- Commit: a7089cbc | Branch: ekv/a-03-typed-unwrap → pushed
- register_p1_synthesis.ts: unwrapCapabilityResult + bodha_discoveries_get fix + 2 other sites
- Status: BUILT → DIFF-REVIEWED → PUSHED → awaiting E merge

### A-04 — noLelCalibrationMaturity facades (F-140) [VERIFIED]
- Commit: 39bc414f | Branch: ekv/a-04-lel-calibration → pushed
- kala_envelope.ts: fetchCalibrationMaturity with lateral join; 5 kala_views wired
- Status: BUILT → DIFF-REVIEWED → PUSHED → awaiting E merge

### A-05 — enum fix query_insights (F-29) [VERIFIED]
- Commit: 52abb3d6 | Branch: ekv/a-05-enum-fix → pushed
- query_insights.ts: CONFIRMED/PARTIAL/REFUTED/UNRESOLVED uppercase + renamed 'denied'→'refuted'
- Status: BUILT → DIFF-REVIEWED → PUSHED → awaiting E merge

### A-06 — gochara disclosure (F-119 TS half) [VERIFIED]
- Commit: 4cdf3dfc | Branch: ekv/a-06-gochara-disclosure → pushed
- d8 + d9: withSweepDisclosure local helper; suppresses bare-point rows; resolution_disclosure on top_windows
- Status: BUILT → DIFF-REVIEWED → PUSHED → awaiting E merge

## VERIFIED LANES (EKV-<lane>-VERIFIED posted here after exit-test pass)

EKV-A-01-VERIFIED — 38b7a137 pushed ekv/a-01-timing-hooks-hardfloor — hardFloor:true on 2 timing sections, registry_bridge.ts FROZEN
EKV-A-02-VERIFIED — dd583eb1 pushed ekv/a-02-whitelist-4-keys — 4 classical-text tools whitelisted, tool_name_bridge.ts FROZEN
EKV-A-03-VERIFIED — a7089cbc pushed ekv/a-03-typed-unwrap — unwrapCapabilityResult + bodha_discoveries_get rows now non-empty
EKV-A-04-VERIFIED — 39bc414f pushed ekv/a-04-lel-calibration — fetchCalibrationMaturity replaces zero-stub at 5 facades
EKV-A-05-VERIFIED — 52abb3d6 pushed ekv/a-05-enum-fix — CONFIRMED/PARTIAL/REFUTED/UNRESOLVED uppercase enum fix
EKV-A-06-VERIFIED — 4cdf3dfc pushed ekv/a-06-gochara-disclosure — withSweepDisclosure on d8+d9 top_windows, bare-point rows suppressed

EKV-A-09-VERIFIED — ceadae8cb pushed ekv/a-09-sara-kernel — F-56/F-111: buildAssessResponse() moves verdict_skeleton+activating_dasha to evidence layer for all 4 assess_* tools; judgment_query excluded (named sections + hardFloor already correct); SaraKernel/assembleSaraContent API frozen
EKV-A-11-VERIFIED — 53929cb2e pushed ekv/a-11-bundle-principal — PrimitiveResult typed + params wrapped {params} (F-127) + upstream_status surfaced (F-30/74) + error classification
EKV-A-15-VERIFIED — 08ce27108 pushed ekv/a-15-ayanamsha-wire — 10 na()→resolveChartFactsAyanamsha() replacements in register_p1_aliases.ts, local AYANAMSHA_ALIAS+na() deleted

EKV-A-08-VERIFIED — bea9d379f pushed ekv/a-08-promise-spine — interpretPactJoin pure mapper (pact_status→SaraPromiseJoin); INV-1 enforced (denied→stance:contradicts); 20/20 tests; one-voice story: kala_ahead × kala_upaya reconciled verdict via shared pact call

EKV-A-12-VERIFIED — 526612229 pushed ekv/a-12-inv2-determinism — F-92/F-60: id PK tiebreaker in SQL ORDER BY + localeCompare tiebreaker in JS .sort(); judgment_query activation windows now deterministic across repeated byte-identical calls

EKV-KERNEL-API-FROZEN — dcc2fb5a pushed ekv/a-09-sara-kernel — SaraKernel/SaraPromiseJoin/CompositionReport/SaraLayeredContent/assembleSaraContent stable in response_budget.ts

## BLOCKED LANES

<!-- EKV-<lane>-BLOCKED with evidence (2 failed attempts → SENTINEL) -->

## NOTES / RULINGS

<!-- EKV-R rulings received from PRATINIDHI, cross-stream coordination -->

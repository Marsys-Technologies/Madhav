---
lane: F-26
stream: S5 · MŪLA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-26/SPEC.md, F-26/DIAGNOSIS.md (no REVIEW_LEADS.md present). Verified every file:line citation directly against `/Users/Dev/par-night/main-ro` source. Traced exit test assertions line-by-line against current code. No DB access needed (RS-A, writer_asset: null).

Files read in main-ro:
- `platform-mcp/src/tools/register_p1_synthesis.ts` lines 660–720 (tool block + next block boundary)
- `platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts` lines 30–110, 140–190
- `platform-mcp/src/tools/kala_views/ahead.ts` lines 820–833
- `platform-mcp/src/tools/kala_views/story.ts` lines 55–69, 695–710

## Q1 — Mechanism vs symptom

The spec addresses the correct mechanism: `register_p1_synthesis.ts` advertises `include_lel_events` and forwards the user-supplied value (`!== false` → defaults true) to a capability whose own descriptor declares `lel_capable: false` and whose handler never reads the param. The spec explicitly acknowledges the deeper root cause (missing LEL join in `query_life_arc.ts`) and correctly defers it under `PAR-F-26-NEEDS-LEASE`, stating that `L3_kala` is outside S5's OWNS scope. The fix — remove the false advertisement and forwarding arg — is honest and precisely scoped. No symptom-only masking.

## Q2 — Diagnosis sub-claim coverage

All 7 diagnosis sub-claims (SPEC §7 coverage table) map to spec elements:
- (a) param at register_p1_synthesis.ts:678–679 → §2 removes it; exit test asserts absence ✓
- (b) handler never reads it (query_life_arc.ts:99–105) → §2 removes forwarding arg at line 692 ✓
- (c) SQL no LEL join (query_life_arc.ts:147–177) → §2/§6 explicitly out of scope, PAR-F-26-NEEDS-LEASE raised, disclosed in updated description ✓
- (d) `lel_capable: false` at query_life_arc.ts:39 → §2 confirms correct, file untouched ✓
- False description claim at line 674 → §2 rewrites description; exit test asserts string absent ✓
- ahead.ts:826 sibling → §4 excludes, hardcodes false ✓
- story.ts:700 sibling → §4 excludes, hardcodes false with self-documenting comment ✓

No unmapped claims.

## Q3 — Exit test genuinely fails on current code

Traced both assertions against source:

**Assertion 1:** `expect(block).not.toContain('include_lel_events')`
- `blockStart = SRC.indexOf("'kala_life_arc_get'")` → hits line 664
- `blockEnd = SRC.indexOf('server.tool(', blockStart + 1)` → hits line 704 (synth_tail_divergence_get block)
- Block covers lines 664–703, which includes:
  - line 678: `include_lel_events: z.boolean().optional()`
  - line 679: `.describe('Include Life Event Log matches for each Parva (default: true).')`
  - line 683: `async ({ chart_id, include_lel_events, limit, offset }) =>`
  - line 692: `include_lel_events: include_lel_events !== false,`
- Block DOES contain `include_lel_events` → assertion **FAILS** ✓ (correctly red)

**Assertion 2:** `expect(SRC).not.toContain('cross-links to LEL events')`
- line 674: `'start/end years (age-based), and cross-links to LEL events that fell within that Parva. ' +`
- SRC DOES contain `'cross-links to LEL events'` → assertion **FAILS** ✓ (correctly red)

After fix (both strings removed from their respective locations), both assertions pass. Test is well-formed.

## Q4 — Sibling sites

All 4 `include_lel_events` occurrences in the repo accounted for:
- `register_p1_synthesis.ts:678,683,692` — DEFECT, fixed by this lane ✓
- `ahead.ts:826` — verified hardcodes `false` explicitly; no LEL claim in description; correctly excluded ✓
- `story.ts:59–61,700` — verified hardcodes `false` with explicit no-op comment; self-documenting header; correctly excluded ✓
- `query_life_arc.ts` — excluded under PAR-F-26-NEEDS-LEASE with stated reason (L3_kala outside S5's OWNS scope); descriptor already correct (`lel_capable: false`) ✓

Singleton defect pattern confirmed: no other capability exhibits advertised LEL param forwarded to `lel_capable:false` handler.

## Q5 — Recurrence guard

The exit test file (`register_p1_synthesis_life_arc_lel_noop.test.ts`) serves as CI guard. It asserts:
1. Absence of `include_lel_events` in the `kala_life_arc_get` block specifically (not file-wide — correctly isolated)
2. Absence of `'cross-links to LEL events'` anywhere in the file

Both checks are functional and non-trivial. Re-introducing either string in the target block/file would cause CI to fail. The spec also prescribes a protective comment at the deletion site. Guard is real, not a weak proxy.

## Q7 — Assumptions vs verified citations

All file:line citations independently verified against main-ro source:
- `register_p1_synthesis.ts:678–679` (include_lel_events z.boolean) — CONFIRMED
- `register_p1_synthesis.ts:683` (destructure args) — CONFIRMED
- `register_p1_synthesis.ts:692` (forwarding arg) — CONFIRMED
- `register_p1_synthesis.ts:670–675` (description, cross-links sentence at line 674) — CONFIRMED (description spans 665–675; sentence at 674 is within stated range; minor imprecision in start line, not actionable)
- `query_life_arc.ts:39` (lel_capable: false) — CONFIRMED
- `query_life_arc.ts:99–105` (args destructuring, no include_lel_events) — CONFIRMED
- `query_life_arc.ts:45–81` (input_schema omits include_lel_events) — CONFIRMED
- `query_life_arc.ts:147–177` (SQL, kala_jivana_parva only, no LEL join) — CONFIRMED
- `ahead.ts:826` (include_lel_events: false) — CONFIRMED
- `story.ts:59–61` (header comment) — CONFIRMED
- `story.ts:700` (include_lel_events: false with no-op comment) — CONFIRMED
- `server.tool(` block boundaries at lines 663/704 — CONFIRMED (correct isolation for exit test)
- Exit test file does NOT exist in main-ro yet — CONFIRMED (correctly absent, builder creates it)

`writer_asset: null`, `data_delta: narrow`: correct per §6 (pure MCP schema + description-text change, no DB/writer layer). No shadow run required. No rebuild required.

No unverified assumptions found.

## Named deficiencies (if INCOMPLETE-RETURN)

None.

## Verdict: COMPLETE

All rubric items pass. The spec is mechanistically accurate, all diagnosis sub-claims covered, the exit test is genuinely red on current code and will be green after the stated fix, all sibling sites are accounted for, the recurrence guard is real, and every citation is verified against source.

---
lane: F-121
stream: S4
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-121/SPEC.md, F-121/DIAGNOSIS.md (no REVIEW_LEADS.md present).
Source read from `/Users/Dev/par-night/main-ro` (read-only mirror of origin/main).
Files verified against source:
- `platform-mcp/src/tools/kala_views/now.ts` (lines 120, 710-737, 800-900, 937-1001, 1785-1803)
- `platform/src/lib/retrieval/registry/layers/L3_kala/query_active_dashas.ts` (lines 65-110)
- `platform-mcp/src/lib/kala_uncertainty.ts` (lines 45-63)
- `platform-mcp/src/tools/kala_views/ahead.ts` (grep for max_level)
- `platform-mcp/src/tools/kala_views/explain.ts` (grep for computedCoverage, max_level)
- `platform-mcp/src/__tests__/kala_now_get_sandhi_w1_joins.test.ts` (full read)
Exit test traced line-by-line against current source (pre-fix state).

## Q1 — Mechanism vs. symptom

SPEC addresses the mechanism directly. Root cause is the hardcoded `max_level: 2` in `fetchVimshottariMdAdBoundaries` (`now.ts:883`), which structurally prevents level-3/4 entries from ever reaching `buildBoundaryBand`. The SPEC fixes the call-site argument (one token change), not the downstream symptom (bands being absent). The Reserved-Question Determination correctly explains why Element 1 also closes the coverage-vocabulary gap identified by DIAGNOSIS without requiring a new `CoverageState`. PASS.

## Q2 — Sub-claim coverage

All five DIAGNOSIS claims map to SPEC elements:
- (a) Only levels 1-2 banded → Element 1 (max_level: 2→4)
- (b) All four bands `is_now_within_band=false` → Element 1 + exit-test item 3
- (c) Active level-4 sandhi exists per `ganita_dasha_periods_get` → Element 1 + exit-test items 1/3 (fixture mirrors live dates)
- (d) Coverage flatly `computed`, no level-3/4 qualifier → Reserved-Question Determination: post-fix `computed` is literally accurate since level 5 is never computed system-wide (confirmed `kala_uncertainty.ts:57`); no new CoverageState needed. DIAGNOSIS was reasoning about the unfixed state. Closed by Element 1.
- (e) `band_convention` omits level restriction → Element 2 (extend `SANDHI_BAND_CONVENTION` to name levels 1-4 and the never-computed level 5)

No unmapped DIAGNOSIS claims. PASS.

## Q3 — Exit test genuinely fails on today's code

Pre-fix state confirmed: `now.ts:883` hardcodes `max_level: 2`; `SANDHI_BAND_CONVENTION` (lines 856-862) contains no level-scope text and no "Sūkṣma".

New exit-test assertions that would fail immediately on today's code:
1. `body.args?.max_level === 4` — fails: current code sends `max_level: 2`. Verified via `callRegistryCapability` at `now.ts:134` which formats body as `{ uri, args }`, confirming `body.args.max_level` is the correct path.
2. `band_convention` containing 'Sūkṣma' — fails: `SANDHI_BAND_CONVENTION` (lines 856-862) has no such text.
3. Level-4 band with `is_now_within_band: true` — would also fail (level-4 data never fetched with `max_level: 2`), but assertions 1 and 2 fail first.

Exit test would red on pre-fix source. PASS.

## Q4 — Sibling sites

All DIAGNOSIS sibling census entries covered with stated reasons:
- `now.ts:721` (`fetchActiveVimshottariChain`, item 28) — `max_level: 2` confirmed at line 721. Excluded: "dasha lord" concept is defined as MD/AD lord by semantics; makes no absence claim about deeper levels. Stated reason present. VERIFIED.
- `ahead.ts:411` (`fetchActiveVimshottariChain`) — `max_level: 2` confirmed at line 411. Same non-hazard reasoning. VERIFIED.
- `ahead.ts:638` (Mudda system) — `max_level: 2` confirmed at line 638. Different dasha system, not an absence claim about deeper Mudda levels. VERIFIED.
- `sukshma_boundary_uncertainty` — correctly identified as a positive precedent (convention text in `kala_uncertainty.ts:57` confirmed). Not a sibling defect.
- `explain.ts`/`upaya.ts` — grepped for `computedCoverage` (confirmed: 3 call sites in explain.ts, no `max_level` references). Explicitly noted in both DIAGNOSIS and SPEC as out of scope for individual line audit. Acceptable stated limitation.

All sibling sites covered or excluded with reasons. PASS.

## Q5 — Recurrence guard

Two guards, both real detectors:
1. Request-body assertion (`body.args?.max_level === 4`) inspects the outbound call-site argument, not just the response shape. A silent revert of the one-token literal to any value < 4 fails this test immediately, independent of mock return values.
2. Fixture-grounded level-4 band assertion using live-observed dates (2026-08-13..2026-08-25 / as_of 2026-08-16) tests the full pipeline: fetch → buildBoundaryBand plumbing → is_now_within_band computation. A regression in any link in the chain (max_level cap, band construction, boolean computation) fails this assertion.

Neither guard is a weak proxy. Both assert actual computed behavior. PASS.

## Q7 — Unverified assumptions / file:line accuracy

All critical citations verified against source:
- `now.ts:875-900` → `fetchVimshottariMdAdBoundaries` ✓ (function starts at line 875)
- `now.ts:882-885` → `callRegistryCapability` call with `max_level: 2` ✓ (line 883 confirmed)
- `now.ts:937-960` → `buildBoundaryBand` ✓ (confirmed)
- `now.ts:855-862` → `SANDHI_BAND_CONVENTION` constant ✓ (lines 856-862 confirmed)
- `now.ts:1796-1803` → coverage ternary for `dasha_sandhi` ✓ (confirmed)
- `query_active_dashas.ts:72` → parameter doc "Deepest level to report... Default 3" ✓
- `query_active_dashas.ts:97` → `Math.min(Math.max(...), 5)` clamp ✓
- `now.ts:721` → `fetchActiveVimshottariChain` with `max_level: 2` ✓
- `ahead.ts:411`, `ahead.ts:638` → both `max_level: 2` ✓

One citation imprecision (non-blocking): SPEC says `now.ts:807-832` is where `sukshma_boundary_uncertainty`'s served convention text discloses "level 5 [Prāṇa-daśā] is NEVER computed for any chart by design". In fact, lines 807-832 define `fetchSukshmaBoundaryUncertainty` (the fetch function); the convention string is in `kala_uncertainty.ts:51-62` (`SUKSHMA_INTERVAL_CONVENTION_TEXT`). The substantive claim is confirmed (the convention text says exactly what the spec claims); the file attribution is imprecise. This does not affect the fix or test correctness — it is a documentation-level inaccuracy in the spec's prose, not a wrong claim about behavior.

No unverified assumptions about code behavior. PASS (with notation).

## Named deficiencies (if INCOMPLETE-RETURN)

None — verdict is COMPLETE. The single citation imprecision (kala_uncertainty.ts vs. now.ts for the Sukshma convention text) is below the threshold for INCOMPLETE-RETURN: the precedent itself is verified and valid, and it does not affect the builder's implementation task (which references the `sukshma_boundary_uncertainty` field, not the file housing its convention constant).

## Verdict: COMPLETE

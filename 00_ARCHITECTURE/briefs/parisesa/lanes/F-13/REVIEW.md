---
lane: F-13
stream: S2
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-13/SPEC.md, F-13/DIAGNOSIS.md. No REVIEW_LEADS.md in lane dir.

Source verified at `/Users/Dev/par-night/main-ro` (read-only):
- `platform-mcp/src/tools/kala_views/ritual.ts` (696 lines) — registration handler + input shape
- `platform-mcp/src/lib/response_budget.ts` lines 508–569 — `autoDetectTrimmableSections` traversal depth
- `platform-mcp/src/lib/kala_lattice_query.ts` lines 331–416, 570–638 — `buildLedger`, `adjudicateCandidates`
- `platform-mcp/src/lib/kala_ritual_resonance.ts` lines 500–546, 580–619, 632–706 — `scoreElectionQuality`, `RitualOpportunity`, `Mode1Result`, per-window loop
- `platform-mcp/src/tools/kala_views/{story,elect,explain}.ts` — sibling budget-wiring spot checks
- Directory listing of `kala_views/` confirmed 11 non-test files

All citations traced line-by-line. No live test run (serving-layer only; no DB required for structural verification).

## Q1 — Mechanism vs. symptom

SPEC addresses mechanism, not symptom. Two interlocking root causes identified and confirmed:
(i) `registerKalaRitualGet` at `ritual.ts:691–693` emits bare `JSON.stringify(response, null, 2)` with no budget call — verified, no import of `response_budget.ts` present in the file;
(ii) `autoDetectTrimmableSections` (`response_budget.ts:508–569`) traverses only depth-1 arrays and depth-2 `key.nestedKey` arrays, leaving `pattern_search.adjudication.ledgers[i].*` (depth 3+) and `opportunities[i].judgment_ledger.*` (depth 3+) unreachable — confirmed by reading the double-loop structure (outer: `for key of Object.keys(content)`, inner: `for nestedKey of Object.keys(topVal)`; no third level).

Change C (explicit `TrimmableSection` declarations for the deep paths) + Change D (wiring `finalizeMcpBudget` in the registration handler) together address both layers. Mechanism-level fix, not symptom-suppression.

## Q2 — Diagnosis sub-claims → spec elements

SPEC §7 provides explicit coverage table. All eight sub-claims map:

| Sub-claim | Spec section | Verified |
|---|---|---|
| A: zero budget wiring in ritual.ts | §2 Change B+D | ✓ |
| B: Mode-2 ~1.30 MB | §3 exit test + §2 Change C (ledger sections for adjudication.ledgers[*]) | ✓ |
| C: Mode-1 ~570 KB | §3 primary assertion + §2 Change C+D | ✓ |
| D (corrected): real driver is JudgmentLedger arrays, not census | §2 Change C targets convention_only_factors/neutral_annotations/convention_only_keys explicitly | ✓ |
| E: siblings story.ts/elect.ts have budget_kb; ritual.ts does not | §2 Change A (adds budget_kb matching sibling default) | ✓ |
| Blast radius: F-13 absent from CL-00 27-check battery | §5 recurrence guard proposes 28th entry | ✓ |
| Sibling census: 11 files, ritual.ts uniquely has both defects | §4 full per-file table | ✓ |
| Fix path stays inside S2 lease | §6 dependencies (response_budget.ts imported not edited) | ✓ |

No unmapped sub-claim.

## Q3 — Exit test genuinely fails on today's code

Line-by-line trace on current source:

Test calls `handleKalaRitualGet({ chart_id: '482012f1…', horizon: '90d', limit: 10 }, principal)`. Execution path: `scoreMode1Opportunities` (`kala_ritual_resonance.ts:632`) → per-window loop lines 654–706 → 8× `scoreElectionQuality` (`kala_ritual_resonance.ts:505`) → 8× `adjudicateCandidates` (`kala_lattice_query.ts:570`) → 8× `buildLedger` (`kala_lattice_query.ts:331–416`) with no array length cap on any of the five factor arrays. Plus full `structural: StructuralSubstrate` embedded at `Mode1Result.structural` (line 612). DIAGNOSIS repro measured raw result at 491,078 bytes.

Assertion 1: `byteLen > 40 * 1024` → `491,078 > 40,960` → **throws**. RED. ✓
Assertion 2: `!('trim_report' in result)` — `KalaEnvelope` has no `trim_report`; raw result has none → **throws** (if reached). ✓

Post-fix note: test sketch calls `handleKalaRitualGet` directly; budget is applied only in the registration handler. After the fix, calling `handleKalaRitualGet` directly still returns ~491 KB — test would still fail as sketched. SPEC §3 final Note explicitly acknowledges this and directs the implementer to either (a) call the registration handler wrapper or (b) apply `finalizeMcpBudget` + `buildLedgerTrimmableSections` inline. Both formulations fail today and pass after the fix. The Note is the authoritative test contract; the sketch code is illustrative only.

## Q4 — Sibling sites covered

SPEC §4 table covers all 11 non-test files in `kala_views/`:
- `ahead.ts`: excluded — finalizeMcpBudget present (verified), no adjudicateCandidates/JudgmentLedger hits (grep confirmed zero)
- `dasha_sandhi.ts`: excluded — no budget, no lattice, different defect class, flagged for future pass
- `elect.ts`: excluded — budget_kb + finalizeMcpBudget verified; different defect shape (F-122)
- `explain.ts`: excluded — kalaBudgetedDualOutput verified at source line 736; no lattice exposure confirmed
- `now.ts`: excluded — finalizeMcpBudget present (sibling pattern)
- `priority.ts`: excluded — kalaBudgetedDualOutput present
- `shared.ts`: excluded — helper lib, not a tool handler
- `story.ts`: excluded — budget_kb + finalizeMcpBudget verified at source lines 115, 781
- `upaya.ts`: excluded — no budget, no lattice, same note as dasha_sandhi.ts
- `ritual.ts`: in scope ✓

All spot-checks confirmed against source. Sibling census exhaustive.

## Q5 — Recurrence guard

Two guards in §5:

1. **Size-regression guard** (`byteLen <= 40 * 1024`): directly detects the defect class. Any rewrite dropping the budget call re-introduces ~491 KB response → test fails immediately. Primary guard; detects the actual defect, not a proxy. SOLID.

2. **Schema guard** (`'budget_kb' in KalaRitualInputShape`): detects removal of budget_kb from schema. **Implementation gap**: `KalaRitualInputShape` is declared `const` (not `export const`) at `ritual.ts:140` — confirmed by grep. The guard requires `import { KalaRitualInputShape } from '../ritual.js'`, which fails without an explicit export. SPEC §2 Change A specifies adding `budget_kb` to the shape but does NOT specify adding `export` to the const declaration. Implementer must add `export` themselves; one word omitted.

The primary guard is sound. The schema guard has a minor spec gap (missing `export` instruction).

CL-00 28th-entry proposal is additive and correctly marked as a proposal.

## Q7 — File:line citation verification

| Citation | Actual source | Result |
|---|---|---|
| `ritual.ts:679-694` (bare JSON.stringify) | Lines 679–694 read directly — `JSON.stringify(response, null, 2)`, no budget | ✓ exact |
| `KalaRitualInputShape` at `~line 165` (limit) | Line 165: `limit: z.number().int().min(1).max(50)…` | ✓ exact |
| `KalaRitualParams` at `~179` (no budget_kb) | Lines 168–180: confirmed, no budget_kb field | ✓ exact |
| `response_budget.ts:508-569` (autoDetectTrimmableSections) | Lines 508–569: depth-2 max — confirmed double-loop only | ✓ exact |
| `kala_lattice_query.ts:331-416` (buildLedger) | Lines 331–416: confirmed, no array length cap | ✓ exact |
| `kala_lattice_query.ts:570-638` (adjudicateCandidates) | Lines 570–638: confirmed | ✓ exact |
| `kala_ritual_resonance.ts:505-511` (scoreElectionQuality) | Lines 505–511: function sig confirmed | ✓ exact |
| `kala_ritual_resonance.ts:654-706` (per-window loop) | Lines 654–706: confirmed | ✓ exact |
| `kala_ritual_resonance.ts:580-598` (RitualOpportunity.judgment_ledger) | Lines 580–598: confirmed | ✓ exact |
| `kala_ritual_resonance.ts:612` (Mode1Result.structural) | Line 612: `structural: StructuralSubstrate` | ✓ exact |

One trivial discrepancy: DIAGNOSIS says "full read of ritual.ts (697 lines)"; actual wc = 696. Off by one trailing-newline — immaterial.

No citation wrong. No assumed-but-unverified claim.

## Named deficiencies (implementation-guidance gaps, not INCOMPLETE triggers)

1. **Test sketch calls handleKalaRitualGet directly** (`ritual.ts` + §3): test sketch code as written fails BOTH before and after the fix (budget never applied in handleKalaRitualGet). The SPEC §3 Note explicitly corrects this with two valid alternative formulations. Implementer must follow the Note, not the sketch code verbatim.

2. **Missing `export` on KalaRitualInputShape** (`ritual.ts:140` + §5): schema guard in §5 requires importing KalaRitualInputShape, but it is not exported. SPEC §2 Change A omits `export` from its instructions. Implementer must add `export` to `const KalaRitualInputShape` at line 140.

Neither affects correctness of mechanism identification, fix strategy, or primary recurrence guard.

## Verdict: COMPLETE

---
lane: F-120
stream: S4
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md, F-120/DIAGNOSIS.md, F-120/SPEC.md. No REVIEW_LEADS.md present.

Source verified against `/Users/Dev/par-night/main-ro`:
- `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts` lines 450–530 (primary fix file)
- `platform-mcp/src/tools/kala_views/now.ts` lines 20–32 (sibling exclusion verification)
- `platform-mcp/src/tools/kala_views/explain.ts` lines 298–303 (sibling exclusion verification)
- `platform-mcp/src/tools/kala_views/ahead.ts` lines 770–780, 1753–1764 (sibling exclusion verification)
- Grep for `buildDashaNarration` across entire `get_dashas.ts` (export verification)

Exit test traced line-by-line against current source (no test runner available in read-only checkout).

## Q1-Q5, Q7

**Q1 — Mechanism vs. symptom?**
COMPLETE. The spec addresses the exact mechanism: the `lvl > 3` cap at line 464 that populates `byLevel`, the unconditional `pd['lord_graha'] Pratyantardasha (current, ...)` string literal at line 495, and `sandhi_flag` consulted only via `md['sandhi_flag']` at line 511. The fix prescription (remove cap, compute finestLevel, dynamic chain, per-level sandhi check, extract export) addresses all three root causes, not just their symptom in the narration text.

**Q2 — All diagnosis claims map to spec elements?**
Yes, full mapping:
- Claim (a) — payload already returns 4 levels correctly → confirmed as precondition; spec §7 coverage table acknowledges this, no spec change needed. ✓
- Claim (b) — `lvl > 3` cap at line 464 → spec §2 change (a): remove cap. Recurrence guard test directly asserts this. ✓
- Claim (c) — hardcoded "current" on level-3 at line 495 → spec §2 change (b)+(c): finestLevel detection + dynamic chain. ✓
- Claim (d) — sandhi_flag pinned to level-1 only at line 511, PARTIALLY CONFIRMED → spec §2 change (d): per-level sandhi check; exit test asserts level-4 sandhi surfaced. ✓
- Sibling census (0 undocumented siblings in S4 lease) → spec §4: all 5 siblings enumerated with exclusion reasons. ✓

No unmapped diagnosis claims.

**Q3 — Exit test genuinely fails on today's code?**
CONFIRMED by source trace. The test file imports:
```typescript
import { buildDashaNarration } from '../get_dashas'
```
Grep across the entire `get_dashas.ts` file for `buildDashaNarration` returns ZERO matches. The function does not exist as a named export (the narration logic is inline within the handler's try block, lines 460–528, never extracted or exported). The import will fail with a module binding error before any assertion runs. This is a genuine hard fail, not a soft assertion miss.

Secondary failure path (if import were somehow mocked): the `lvl > 3` cap at line 464 would filter level_n=4 out of `byLevel` before the narration string is built, so assertions for `Mercury Sukshmadasha` would fail regardless.

**Q4 — All sibling sites covered or excluded with stated reason?**
All five diagnosis-identified siblings are in spec §4 with stated exclusion reasons. Verified:
- `now.ts` lines 24-28: CONFIRMED — exact text "item 1-lite `dasha_sandhi`: a band around every currently-active MD/AD period's start AND end boundary... Full daśā-sandhi calendar (all levels, both directions) is item 1-full (wave W3), not this facade's job." The exclusion "intentionally MD/AD-scoped per file header" is accurate.
- `explain.ts` line 302: CONFIRMED — `.filter((p) => Number.isFinite(p.level_n) && p.level_n > 0)` has no upper bound. Exclusion "all levels pass through (confirmed clean)" accurate.
- `ahead.ts` line 777: CONFIRMED — `const PERIOD_ECHO_LEVEL_NAME: Record<number, string> = { 1: 'Mahadasha', 2: 'Antardasha' }` exists exactly as described.
- `ahead.ts` line 1759: CONFIRMED — `.filter((e) => (e.level_n === 1 || e.level_n === 2) && ...)` is the period_echo filter, intentionally scoped. SEE Q7 NOTE.
- `upaya.ts`: exclusion taken on face (no dasha-level chain code); consistent with diagnosis.
- `dasha_sandhi.ts`: exclusion taken on diagnosis authority (confirmed clean, all_levels: true).

**Q5 — Recurrence guard real?**
YES. Two layers: (1) the exit test "includes level-4 Sukshmadasha in the narration chain" directly exercises the cap-removal and will fail if any future `lvl > N` guard is reintroduced in `byLevel` population; (2) the INVARIANT comment above the loop makes intent explicit at the re-entry point. The guard detects the exact defect class (hardcoded numeric upper bound in `byLevel` population), not a proxy. This is a genuinely strong guard.

**Q7 — All file:line citations verified?**
All PRIMARY fix citations verified exact:
- `get_dashas.ts:460–469` (`byLevel` loop with cap) — EXACT. ✓
- `get_dashas.ts:464` (`if (lvl < 1 || lvl > 3) continue`) — EXACT. ✓
- `get_dashas.ts:492–495` (hardcoded leadSentence with "current" on pd) — EXACT. ✓
- `get_dashas.ts:511–515` (`sandhi_flag` only at `md['sandhi_flag']`) — EXACT. ✓
- `get_dashas.ts:483–485` (`md/ad/pd` pinned from `byLevel[1]/[2]/[3]`) — EXACT. ✓

ONE MINOR CITATION ERROR IN §4 (excluded-sibling table only):
- Spec §4 says `ahead.ts` "(lines 759, 777)" — line 777 is confirmed correct. Line 759 is NOT the filter; line 759 in the file is part of the `DashaEchoRow` interface. The period_echo filter is at line **1759** (confirmed). The DIAGNOSIS correctly cited 1759; the SPEC dropped the leading "1" in transcription.
- Impact: ZERO builder risk — `ahead.ts` is excluded from the fix. The exclusion decision is correct and independently confirmed. No implementation guidance is affected.

No assumptions detected in the primary fix path. All cited mechanisms read code.

## Named deficiencies

None that block implementation. One citation note for the record:
- `F-120/SPEC.md §4, ahead.ts row`: cited "line 759" should be "line 1759" — transcription typo, exclusion decision remains correct.

## Verdict: COMPLETE

The spec correctly addresses the mechanism at all three defect sites (cap, label, sandhi scope), maps all diagnosis claims, provides a hard-failing exit test (import fails immediately on today's code), covers all five sibling sites with verified exclusion reasoning, and supplies a genuine recurrence guard. The single citation typo (1759→759) is in an excluded-sibling row and carries zero builder risk. Implementation may proceed.

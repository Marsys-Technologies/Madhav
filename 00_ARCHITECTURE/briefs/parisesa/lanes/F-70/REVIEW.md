---
lane: F-70
stream: S5
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, SPEC.md, DIAGNOSIS.md (no REVIEW_LEADS.md present).
Source read (main-ro): `kala_views/now.ts`, `ritual.ts`, `story.ts`, `priority.ts`, `ahead.ts`, `upaya.ts`, `explain.ts`, `elect.ts`, and `lib/kala_envelope.ts`.
Traced exit test assertions line-by-line against current source. No runner available (reviewer role is source-trace only), but the test logic is a direct source-scan — verified by reading the actual file contents.

---

## Q1 — Mechanism vs. symptom

The spec addresses the mechanism. The root cause is that `now.ts`, `ritual.ts`, and `story.ts` call `noLelCalibrationMaturity()` unconditionally at their `makeKalaEnvelope` call site — ignoring the already-written `fetchCalibrationMaturity` resolver (live at `kala_envelope.ts:472-523`) that five sibling facades already use. The fix is a serving-layer wiring gap closure: import + call-site swap in three files, plus a comment correction in `priority.ts`. This is mechanistic, not symptomatic.

## Q2 — Sub-claim coverage

Diagnosis claims (a)-(e) and §3.1-§3.5 are all mapped in SPEC §7. Every sub-claim has a named spec element:
- (a) 8 sites → §4 table accounts for all 8; §2.1-2.3 fix the 3 remaining
- (b) §N.7 comment violation → §2.4 fixes the `priority.ts:14` stale comment
- (c) Real data in 3 tables → §6 confirms no writer change needed; `fetchCalibrationMaturity` queries `kala_field_skill` directly
- (d) Zero serving consumers → §2.1-2.3 close the gap for the 3 remaining views
- (e) Contradictory sibling surface → resolved for all 8 views after fix
- §3.1 eight call sites → §4 table with disposition per site
- §3.5 join path → §6 confirms `fetchCalibrationMaturity` covers the join; no spec change needed
- §3.5 secondary defect in `ka_kshetra/stage4_field.py` → explicitly out-of-scope, flagged to conductor

No unmapped diagnosis claim found.

## Q3 — Exit test genuinely fails on today's code

Traced source-scan assertions against current main-ro:

**now.ts**: `grep -n noLelCalibrationMaturity` → line 1970: `calibrationMaturity: noLelCalibrationMaturity()` — matches negative assertion regex `calibrationMaturity:\s*noLelCalibrationMaturity\(\)` → assertion TRIGGERS (test FAILS). No `fetchCalibrationMaturity` present → positive assertion FAILS.

**ritual.ts**: line 572: `calibrationMaturity: noLelCalibrationMaturity()` → same negative regex matches → FAILS. No `fetchCalibrationMaturity` → positive assertion FAILS.

**story.ts**: line 756: `calibrationMaturity: noLelCalibrationMaturity()` → negative regex matches → FAILS. No `fetchCalibrationMaturity` → positive assertion FAILS.

**priority.ts**: line 14 contains `no calibration plane exists yet` verbatim → last assertion triggers → FAILS.

All 7 test cases (3 files × 2 assertions + 1 comment check) fail on today's code. After fix, all 7 pass. Exit test is a genuine discriminator.

## Q4 — Sibling sites

All 8 diagnosis §3.1 sites accounted for in SPEC §4 table. Verified each disposition against main-ro:
- **now.ts:1970** — broken (`noLelCalibrationMaturity()`) ✅ CONFIRMED
- **priority.ts:434** — fixed (`await fetchCalibrationMaturity(chart_id, principal)`) ✅ CONFIRMED
- **ahead.ts:1985** — fixed (`await fetchCalibrationMaturity(chartId, principal)`) ✅ CONFIRMED (SPEC table says line 1984; actual is 1985 — trivial one-off, no change needed for this file)
- **upaya.ts:427** — fixed (`await fetchCalibrationMaturity(params.chart_id, principal)`) ✅ CONFIRMED
- **ritual.ts:572** — broken ✅ CONFIRMED
- **explain.ts:699** — fixed (`await fetchCalibrationMaturity(chart_id, principal)`) ✅ CONFIRMED
- **story.ts:756** — broken ✅ CONFIRMED
- **elect.ts:761** — fixed (`await fetchCalibrationMaturity(input.chart_id, principal)`) ✅ CONFIRMED

Five excluded with clear reason (already fixed by F-140 which introduced `fetchCalibrationMaturity`). No site silently dropped.

## Q5 — Recurrence guard

The exit test (`kala_calibration_maturity_wiring.test.ts`) is a genuine guard: the regex `calibrationMaturity:\s*noLelCalibrationMaturity\(\)` would catch any reversion. Secondary guard: TypeScript compiler enforces `await` usage since `fetchCalibrationMaturity` returns `Promise<CalibrationMaturity>` and `calibrationMaturity` is typed `CalibrationMaturity` (not Promise). Any accidental drop of `await` produces a compile error. Guards detect the defect class, not a weak proxy.

## Q7 — Unverified assumptions / citation accuracy

All material citations checked:
- `kala_envelope.ts:472-523` — `fetchCalibrationMaturity` export: ✅ exact lines 472-523 confirmed
- `kala_envelope.ts:453-461` — `noLelCalibrationMaturity()` definition: line 453 confirmed by grep
- `now.ts:1970` — call site: ✅ confirmed
- `now.ts:1471` — type annotation `ReturnType<typeof noLelCalibrationMaturity>`: ✅ confirmed
- `now.ts:1536-1539` — `computeKalaNow(chartId, args, principal)` signature: ✅ confirmed, `async`
- `ritual.ts:572` — call site: ✅ confirmed
- `ritual.ts:79-83` — import block (`noLelCalibrationMaturity` at line 81, not 80): SPEC says "line 80 block" — trivial off-by-one; `noLelCalibrationMaturity` is at line 81 inside the block starting at 79. Not a substantive error.
- `ritual.ts:563` — `resolveFieldSnapshot(params.chart_id, principal)`: ✅ confirmed
- `ritual.ts:445` — `handleKalaRitualGet` is `async`: ✅ confirmed
- `story.ts:756` — call site: ✅ confirmed
- `story.ts:692-694` — `handleKalaStoryGet(input, principal)` signature: ✅ confirmed, `async`
- `priority.ts:14` — stale comment: ✅ confirmed verbatim
- `priority.ts:434` — already calls `fetchCalibrationMaturity`: ✅ confirmed

All citations are accurate within ±1 line. No materially wrong claim found. The spec states `writer_asset: null` — confirmed: no writer files are touched; pure TypeScript MCP serving-layer change only.

---

## Named deficiencies (if INCOMPLETE-RETURN)

None.

---

## Verdict: COMPLETE

The spec is mechanistically correct, all diagnosis sub-claims are covered, the exit test genuinely fails on current source and would pass after the prescribed changes, all 8 sibling sites are accounted for with disposition, the recurrence guard is substantive, and all material file:line citations check out. Minor line-number off-by-ones (ahead.ts:1984 vs 1985, ritual import block 80 vs 81) are cosmetic and do not affect fix correctness. No deficiencies requiring revision.

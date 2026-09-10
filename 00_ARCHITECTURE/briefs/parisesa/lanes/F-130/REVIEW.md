---
lane: F-130
stream: S4
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-130/SPEC.md, F-130/DIAGNOSIS.md. No REVIEW_LEADS.md exists in lane directory.

Source verified against `/Users/Dev/par-night/main-ro/platform-mcp/src/tools/registry_bridge.ts`:
- Lines 1461–1497: `readTimingWindowsFamily` and `readContradictionsFamily` — read in full
- Lines 1020–1037: `DOMAIN_READING_FAMILIES` constant block — read in full
- Lines 1530–1558: `buildDomainReading` wiring (call sites) — read in full
- Line 1106: `diagSuffix` function — read in full
- Export status of both reader functions: searched for `export function readTimingWindowsFamily|readContradictionsFamily` — no matches (confirmed not exported)

No REVIEW_LEADS.md found; no daytime findings to verify.

## Q1 — Mechanism vs. symptom

COMPLETE. The spec names the exact mechanism: `JSON.stringify(obj).slice(N)` interpolated directly into template-literal `sentences[]` entries inside `readTimingWindowsFamily` (line 1469) and `readContradictionsFamily` (line 1494 fallback). It explains WHY the fields to use instead are `signature_class`/`activation_start`/`activation_end`/`activation_peak_date` (Fix A) and `contradiction_id` (Fix B), grounding the fix in the live data shape confirmed by the DIAGNOSIS. Root-cause addressed, not just symptom patched.

## Q2 — DIAGNOSIS sub-claims → SPEC

All 10 rows in SPEC §7 Coverage Table are verified. No unmapped claims:
- `readTimingWindowsFamily` line 1469 bug → §2 Fix A + §3 test assertion 1 ✓
- `readContradictionsFamily` line 1494 fallback → §2 Fix B + §3 test assertion 2 ✓
- 2/2 timing_windows live-confirmed → §2 Fix A covers both via shared `buildDomainReading` ✓
- 1/2 contradictions live-confirmed (wealth not triggered) → §4 note: fix protects both tools; wealth latent ✓
- 10 other readers confirmed clean by source review → §4 table with per-row reasons ✓
- `diagSuffix` noted but excluded → §4 last row with explicit exclusion reason ✓
- `buildDomainReading` single wiring point → §1 + §4 ✓
- `ekv/a-09-sara-kernel` lease conflict → §6 ESCALATE note ✓
- 4 named instances = 2 shared defects → §1 root cause + §2 two fixes ✓
- Wealth contradictions correction → §4 latent-coverage note ✓

## Q3 — Exit test genuinely RED on today's code?

YES, genuinely RED — but for a different reason than the spec states.

Trace against current source:
1. Test imports `{ readTimingWindowsFamily, readContradictionsFamily }` from `'../registry_bridge'`
2. Current source: neither function has an `export` modifier (confirmed by grep — no matches for `export function readTimingWindowsFamily` or `export function readContradictionsFamily` in main-ro)
3. TypeScript/ts-jest would fail at compile time: "Module has no exported member 'readTimingWindowsFamily'" — test crashes before any jest assertion runs

**Inaccuracy in §3:** The spec states the FAIL reason as `expect(sentence).not.toMatch(/{/)` throwing. The actual failure on today's code is a TypeScript named-import compilation error, not an assertion failure. This is because the `export` modifier is part of Fix B, not pre-existing.

This inaccuracy is EDITORIAL, not structural: the test IS genuinely RED (fails to compile), and it would be GREEN after both fixes (add exports + fix sentence content) are applied. The fix path is unambiguous — §2 explicitly states both functions must gain `export` modifier. A builder following the spec will add exports and will observe the test go GREEN. The editorial mismatch does not block implementation.

## Q4 — Sibling sites covered

COMPLETE. SPEC §4 provides a 13-row table (matching the DIAGNOSIS sibling census) covering all 12 reader functions wired into `buildDomainReading`. Each clean function has a stated reason (which fields it renders; no `JSON.stringify`). `diagSuffix` is excluded with an explicit reason (diagnostic-only on `__fetch_error` path, bounded, not observed in live calls). The SPEC correctly notes wealth's `contradictions_with_adjudication` is latent (data not currently triggering the branch) rather than omitting it silently.

Source-verified: DOMAIN_READING_FAMILIES at lines 1020–1037 shows 12 career families / 13 wealth families; the SPEC table covers all of them. Call sites confirmed at lines 1540 (`readTimingWindowsFamily`) and 1542 (`readContradictionsFamily`).

## Q5 — Recurrence guard

ADEQUATE. The grep pattern `JSON\.stringify\([^)]+\)\.slice` in `registry_bridge.ts` is precise: it directly detects the exact defect pattern (JSON.stringify with .slice) in the exact file. It would catch any future regression to the same pattern. This is a meaningful guard, not a weak proxy.

## Q7 — Unverified assumptions / file:line citations

All SPEC citations verified against main-ro:
- `readTimingWindowsFamily` function at line 1461, bug at line 1469: CONFIRMED. Source line 1469: `sentences: [\`${activations.length} activation window(s) in range; nearest: ${JSON.stringify(first).slice(0, 220)}.\`]` — exact match.
- `readContradictionsFamily` function at line 1474, bug at line 1494: CONFIRMED. Source line 1494 contains `?? JSON.stringify(first).slice(0, 160)` in the `??` chain — exact match.
- `buildDomainReading` call sites: line 1540 = `readTimingWindowsFamily` call, line 1542 = `readContradictionsFamily` call — CONFIRMED.
- `DOMAIN_READING_FAMILIES` at lines 1020–1037: CONFIRMED. WEALTH_READING_FAMILIES (1020–1025), CAREER_READING_FAMILIES (1027–1032), DOMAIN_READING_FAMILIES map (1034–1037).
- `diagSuffix` at line 1106: CONFIRMED. Uses `JSON.stringify(p['__fetch_args'])` inside a diagnostic suffix, only fires when `__fetch_error` is present.
- Both reader functions confirmed NOT exported (no `export` keyword) in current source — consistent with §2 Fix B's requirement to add `export` modifier.
- `ekv/a-09-sara-kernel` lease conflict (§6): DIAGNOSIS states this was verified via `git log`. Not independently re-verifiable by this reviewer (would require git access to coord-wt), but the claim is corroborated by the DIAGNOSIS's detailed diff description and is a dependency flag, not a code citation.

No unverified assumptions found in the core fix scope.

## Named deficiencies (if INCOMPLETE-RETURN)

None. The Q3 editorial inaccuracy (stated failure mode vs. actual TypeScript import error) does not rise to a deficiency requiring revision; the test is genuinely RED and the fix path is unambiguous from §2.

## Verdict: COMPLETE

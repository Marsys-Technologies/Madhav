---
lane: F-132
stream: S4_VACA
title: reading.thesis raw enum join — kala_views/now.ts signature_classes.join('/')
stage: S
---

# F-132 SPEC — Raw Enum Join in reading.thesis

## 1. Root-cause statement

`kala_views/now.ts` joins `signature_classes` (a raw internal enum array whose values are tokens like `CLASSIFY_RESIDUAL`, `DIGNITY`, `YOGA`, `SUBSYSTEM`) with the literal `'/'` separator directly into human-facing `reading.thesis` and `evidence[].claim` narrative fields, producing strings like `CLASSIFY_RESIDUAL/DIGNITY/YOGA` that are machine-internal labels, not human-readable text.

## 2. Files to change

### A. `platform-mcp/src/tools/kala_views/now.ts`

**What**: Add a `WINDOW_CLASS_GLOSS` constant (mapping each known `signature_classes` token to a human-readable label) and a `glossClass()` helper immediately before the `buildKalaNowReading` function. Replace the two raw `.join('/')` call sites:

- **Line 1183** (thesis): `(top?.signature_classes ?? []).join('/')` → `(top?.signature_classes ?? []).map(glossClass).join(' + ')`
- **Line 1200** (evidence claim): `(f.signature_classes ?? []).join('/')` → `(f.signature_classes ?? []).map(glossClass).join(' + ')`

Also update the fallback strings: line 1183 fallback `|| 'unlabeled'` may remain; line 1200 fallback `|| 'activation'` may remain (no raw token in either).

**Why**: `signature_classes` values are internal classification tokens not intended for display. Routing them through `WINDOW_CLASS_GLOSS` (with a `toLowerCase().replace(/_/g, ' ')` fallback for unknown tokens) produces human-readable labels and satisfies the D-01e governance lint.

**Gloss map to add** (sourced from PASS fixture at `platform/scripts/governance/no_raw_token_narrative_fixtures/pass/raw_token__glossed_narrative.ts`):

```typescript
const WINDOW_CLASS_GLOSS: Record<string, string> = {
  'CLASSIFY_RESIDUAL': 'residual activation',
  'DIGNITY': 'dignity activation',
  'YOGA': 'yoga activation',
  'SUBSYSTEM': 'subsystem window',
}

function glossClass(c: string): string {
  return WINDOW_CLASS_GLOSS[c] ?? c.toLowerCase().replace(/_/g, ' ')
}
```

### B. `platform/scripts/governance/no_raw_token_narrative_allowlist.json`

**What**: Remove both entries whose `justification` references F-132 (lines 1183 and 1200 of `platform-mcp/src/tools/kala_views/now.ts`). After the fix the pattern no longer exists in those lines; keeping stale allowlist entries would mask future regressions at those positions.

**Why**: The allowlist suppresses lint failures for known pre-existing defects. Once fixed, the entries must be removed so the CI job can eventually flip to `continue-on-error: false` (per `ekv-lints.yml` comment: "Flip to false once no_raw_token_narrative_allowlist.json is empty").

## 3. Exit test

**File**: `platform/scripts/governance/__tests__/test_d08_pointer_integrity.py` (already exists; test `TestF131F132RawTokenInNarrative::test_no_signature_classes_join_slash_in_now`)

**Command**:
```
python -m pytest platform/scripts/governance/__tests__/test_d08_pointer_integrity.py::TestF131F132RawTokenInNarrative::test_no_signature_classes_join_slash_in_now -v
```

**FAIL on today's code**: Test asserts `not matches` where `matches` is all occurrences of `signature_classes\b[^\n]*\.join\s*\(\s*['"][/]['"]` in `now.ts`. Currently 2 matches → assertion fails with message "kala_views/now.ts still has 2 signature_classes.join('/') site(s)".

**PASS after fix**: Both sites replaced with `.map(glossClass).join(' + ')` → 0 matches → assertion passes.

**Secondary check** (run after primary): `python platform/scripts/governance/check_no_raw_token_in_narrative.py` — must report 0 new violations (allowlist entries removed; no matching pattern remains).

## 4. Sibling sites

Census of `signature_classes` uses across `platform-mcp/src/` and `platform/src/`:

| File | Line | Pattern | In scope? |
|------|------|---------|----------|
| `platform-mcp/src/tools/kala_views/now.ts` | 1183 | `.join('/')` in `reading.thesis` | YES — fixed |
| `platform-mcp/src/tools/kala_views/now.ts` | 1200 | `.join('/')` in `evidence[].claim` | YES — fixed |
| `platform-mcp/src/tools/kala_views/ahead.ts` | 1398 | `.join(', ')` (comma+space separator) in digest detail | EXCLUDED — Pattern A regex only catches `'/'` separator; comma+space is not a raw-token join (it forms a list label, not a slashed enum path); confirmed by `_RE_TS_RAW_CLASSES_JOIN` in `check_no_raw_token_in_narrative.py` which requires the literal `/` as separator |

No Python sidecar defect sites for F-132 (Pattern B2 — raw prefix in f-string — was surveyed; no active violations found beyond what is covered by the existing lint allowlist, which is now.ts-only).

## 5. Recurrence guard

**Lint**: `platform/scripts/governance/check_no_raw_token_in_narrative.py` — Pattern A (`_RE_TS_RAW_CLASSES_JOIN`) catches any new `signature_classes.join('/')` site in TypeScript narrative fields. Already wired into CI as `ekv-d01e-no-raw-token-in-narrative` (warn-first). After allowlist reaches zero entries, flip `continue-on-error: false` in `.github/workflows/ekv-lints.yml` job `ekv-d01e-no-raw-token-in-narrative`.

**TDD gate**: `test_d08_pointer_integrity.py::TestF131F132RawTokenInNarrative::test_no_signature_classes_join_slash_in_now` stays in D-08 suite and will catch any reintroduction.

## 6. Dependencies and rollback

**Dependencies**: None. This fix is self-contained to two call sites in one TypeScript file plus a JSON allowlist removal. No other lanes must land first. No DB migration. No rebuild required (serving-layer TypeScript only; `now.ts` reads from DB, does not write).

**Rollback**: Revert the two call-site changes in `now.ts` and restore the two allowlist entries. Single-file revert, no data impact.

## 7. Coverage table

| Diagnosis sub-claim | Covered by |
|---|---|
| `now.ts` line 1183: `signature_classes.join('/')` in `reading.thesis` produces raw internal enum token string | §2A (line 1183 fix) + §3 exit test |
| `now.ts` line 1200: `signature_classes.join('/')` in `evidence[].claim` produces raw internal enum token string | §2A (line 1200 fix) + §3 exit test |
| D-01e lint currently allowlists both sites, suppressing CI failure | §2B (allowlist removal) |
| `ahead.ts:1398` is a related but non-defective site (different separator) | §4 sibling census (EXCLUDED with reason) |
| Recurrence: no guard prevents reintroduction | §5 recurrence guard (lint + TDD gate) |

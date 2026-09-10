---
lane: F-15
stream: S2 (MĀTRĀ)
stage: S — SPEC
companion_spec: F-14/SPEC.md (authoritative build spec — build executes from there; this file is F-15's mandatory Stage-S contract)
status: DRAFT
---

# SPEC — F-15: assess_marriage never returns the W7 substance-inline reading digest

## Companion note (read first)
F-14/SPEC.md is the authoritative build specification. The fix is a single commit; F-14 and F-15 MUST be built and merged together. This document provides F-15's mandatory Stage-S contract, calling out F-15-specific details (domain key `relationship`, `assess_marriage` call sites); all shared elements (§2c, §2d, the exit test, recurrence guard, rollback) are adopted from F-14/SPEC.md by reference.

## 1. Root-cause statement
`assess_marriage` never surfaces `reading`, `domain_completeness`, or `completeness_directive` because three independent, all-necessary gates block it: (1) the `assess_marriage` handler never calls `attachDomainCompleteness`/`attachDomainReading` at all (call-site gap); (2) the five `DOMAIN_READING_*` maps carry no `relationship` key, so even if the calls existed the functions would early-return (data-table gap); and (3) `buildAssessResponse`'s grounding assembly reads `response['completeness']`—a key nothing ever sets—instead of `response['domain_completeness']`, universally suppressing both completeness fields for all four `assess_*` tools (key-mismatch gap).

## 2. Files to change

**Primary:** `platform-mcp/src/tools/registry_bridge.ts` (S2 HOT lease — no cross-stream conflict)
**Secondary:** `platform-mcp/src/tools/response_budget.ts` (§2d only: add `domain_completeness_empty_reason` to `IMMUNE_HONESTY_FIELDS`)

### 2a. Add `relationship` key to all five `DOMAIN_READING_*` maps (`:1034-1043`)
Add `RELATIONSHIP_READING_FAMILIES` constant and populate all five maps:
- `DOMAIN_READING_FAMILIES['relationship']`: `RELATIONSHIP_READING_FAMILIES` (see F-14/SPEC.md §2a for array literal; BUILD must verify against `:2960` docstring at build time — do not trust this transcription if drifted)
- `DOMAIN_READING_VARGAS['relationship']`: `['D9', 'D1']` (matches `register_d8_assess_domain.ts:186` `DOMAIN_DIRECT_VARGAS['relationship'] = ['D9']`; D1 per wealth/career pattern)
- `DOMAIN_READING_HOUSES['relationship']`: `[7]` (7th house — from `assess_marriage` handler docstring at `:2960`)
- `DOMAIN_READING_KARAKA_CODE['relationship']`: `'VEN'` (Venus kāraka — same docstring)
- `DOMAIN_READING_KARAKA_LABEL['relationship']`: `'Venus'`

The `health` counterparts are F-14's responsibility in the same commit.

### 2b. Add attach calls to `assess_marriage` handler (near `:2986-2989`)
Mirror `assess_career`'s existing two-line pattern exactly, inserting before the final `return`:
```ts
attachDomainCompleteness(response, 'relationship', chart_id)
await attachDomainReading(response, 'relationship', chart_id, normalizeAyanamsha(ayanamsha_id), principal)
```
Domain key is `'relationship'` (not `'marriage'`) — confirmed by `DOMAIN_DIRECT_VARGAS` convention and `assess_career`'s own call which passes `'career'`, not `'assess_career'`.

### 2c. Fix `buildAssessResponse` grounding key mismatch (`:2923-2927`) — shared with F-14
Replace:
```ts
if (response['completeness'] !== undefined) grounding['completeness'] = response['completeness']
```
With:
```ts
if (response['domain_completeness'] !== undefined) grounding['domain_completeness'] = response['domain_completeness']
if (response['completeness_directive'] !== undefined) grounding['completeness_directive'] = response['completeness_directive']
if (response['domain_completeness_empty_reason'] !== undefined) grounding['domain_completeness_empty_reason'] = response['domain_completeness_empty_reason']
```
This one hunk also restores `domain_completeness`/`completeness_directive` for `assess_career`/`assess_wealth` (already calling the attach functions, but silently losing both fields at assembly today).

### 2d. Honest null-case disclosure in `attachDomainCompleteness` (`:835-837`) — shared with F-14
When `assembleDomainCompleteness` returns null (which it will for `domain='relationship'` because no precompiled relationship dossier slice bundle exists), set:
```ts
response['domain_completeness_empty_reason'] =
  `No precompiled ${domain} concept-slice bundle exists yet — domain_completeness/` +
  `completeness_directive are honestly omitted rather than fabricated (B.10). ` +
  `This is a data-infrastructure gap (bundle generation), not a query failure; tracked separately.`
```
Add `domain_completeness_empty_reason` to `IMMUNE_HONESTY_FIELDS` in `response_budget.ts` so it can never be trimmed. Generating `relationship_*` dossier bundles is explicitly out of scope for this spec.

## 3. Exit test

**File:** `platform-mcp/src/tools/__tests__/assess_domain_reading_parity.test.ts`
**Command:** `npx jest --testPathPattern=assess_domain_reading_parity`

The two tests from F-14/SPEC.md §3 cover `assess_marriage` directly (both iterate all four `assess_*` tools):

**Test 1** — `reading digest: all four assess_* tools surface substance-inline reading`
Asserts `grounding.reading` is a non-empty array for `assess_marriage`.
**FAILS today** (key absent). **PASSES after** §2a + §2b wire the reading path.

**Test 2** — `completeness accounting: honest presence OR honest absence-disclosure, never silent`
For `assess_marriage`: asserts `grounding` has `domain_completeness_empty_reason` matching `/no precompiled/i` and does NOT have `domain_completeness`.
**FAILS today** (field entirely absent, no disclosure). **PASSES after** §2d + §2c surface the honest disclosure.

## 4. Sibling sites covered

| Site | Action | Status |
|---|---|---|
| `DOMAIN_READING_FAMILIES` (`:1034`) | Add `relationship` key | Covered — §2a |
| `DOMAIN_READING_VARGAS` (`:1040`) | Add `relationship` key | Covered — §2a |
| `DOMAIN_READING_HOUSES` (`:1041`) | Add `relationship` key | Covered — §2a |
| `DOMAIN_READING_KARAKA_CODE` (`:1042`) | Add `relationship` key | Covered — §2a |
| `DOMAIN_READING_KARAKA_LABEL` (`:1043`) | Add `relationship` key | Covered — §2a |
| `assess_marriage` handler (`:2960`) | Add both attach calls | Covered — §2b |
| `buildAssessResponse` grounding assembly (`:2923-2927`) | Fix key mismatch | Covered — §2c (shared) |
| `attachDomainCompleteness` null return (`:835-837`) | Add honest disclosure | Covered — §2d (shared) |
| `IMMUNE_HONESTY_FIELDS` (`response_budget.ts`) | Add `domain_completeness_empty_reason` | Covered — §2d |
| `assess_health` handler + `health` map keys | F-14's §2a/§2b — same commit | Covered by F-14, co-built |

No sibling is excluded. Diagnosis census (F-14 §4): exactly five maps and four `assess_*` tools; all addressed across F-14 + F-15.

## 5. Recurrence guard

The §3 exit test iterates all four `assess_*` tools by name. A future fifth `assess_*` tool that omits the two attach calls will fail test 1. Any regression to `buildAssessResponse`'s grounding allow-list will fail test 2. The guard is mechanical and runs on every CI push.

Recommended follow-up (out of scope): static lint asserting `Object.keys(DOMAIN_READING_FAMILIES)` equals the canonical domain set from `DOMAIN_DIRECT_VARGAS`.

## 6. Dependencies and rollback

- **F-14 dependency:** F-15's build IS F-14's build — one PR, one commit. They cannot be built independently.
- **No DB migration.** All changes are TypeScript source edits in the MCP server presentation layer; no schema change, no data-generation step required.
- **Rollback:** revert the single PR/commit. No downstream artifacts dirtied; no rebuild triggered (this is not a writer-layer fix — `registry_bridge.ts` is `platform-mcp/src/tools/`, not `ga_writers/`, `bo_*`, or `pipeline/orchestrator/writers/`).
- **Rebuild policy:** shadow verification only (Level 0) per PROTOCOL §Rebuild. No asset rebuild needed or appropriate; no stale inventory to enumerate.
- **Not reopening F-56/F-111:** §2c only edits `grounding` key names; `evidence`-layer routing of `verdict_skeleton`/`activating_dasha` is untouched.

## 7. Coverage table — every D-stage sub-claim mapped

| Sub-claim (F-15 diagnosis §2, adopting F-14 C1-C4 with `relationship` substitution) | Spec element |
|---|---|
| C1: `assess_marriage` never returns `reading` | §2a (relationship map keys) + §2b (call sites added) |
| C2: `assess_marriage` never returns `domain_completeness` | §2a + §2b + §2c (key-mismatch fix) + §2d (honest disclosure for missing bundle) |
| C3: `assess_marriage` never returns `completeness_directive` | §2a + §2b + §2c + §2d |
| C4 (incomplete as stated): root cause is map-key absence alone | All three gates addressed: §2a (maps), §2b (call sites), §2c (buildAssessResponse mismatch) |
| Diagnosis §3 domain-key note: internal key is `relationship` not `marriage` | §2b and §2a both explicitly use `'relationship'` |
| Diagnosis §1 note: `domain_completeness`/`completeness_directive` absent for all four tools | §2c closes the universal key mismatch |
| Honest disclosure when no dossier bundle exists for `relationship` | §2d |
| Out-of-scope: `reading_depth:'deep_dive'` all-or-nothing grounding drop | Explicitly NOT closed — see F-14/SPEC.md §7; separate finding recommended |

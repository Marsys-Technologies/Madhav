---
lane: F-33
stream: S3_SATYA (spec) -> S5_MULA (build)
stage: S — SPEC
author: SATYA-LEAD (S3)
status: DRAFT — awaiting VERIFIER review
routing_note: >
  F-33's mechanism lives in platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts,
  under S5 MŪLA's OWNS lease (L1_ganita/** query files), not S3's. Per the ordered-handoff
  pattern already used for F-31->S2, this spec is written by S3 (the finding is S3's) and
  builds via S5 once VERIFIER marks it COMPLETE. Written to be executed directly by an S5
  builder with no access to this conversation — every file path, line, and diff is concrete
  and independently verifiable against the citations below (verified fresh against origin/main
  this session, not against the DIAGNOSIS.md's original line numbers, which are confirmed
  accurate as of this pass).
---

# SPEC — ganita_dasha_periods_get: disclose pre-birth `as_of_date` queries structurally

## 0. Read first — the finding, verbatim (from `pp2-audit/manifest.json`, id F-33)

> "`ganita_dasha_periods_get` accepts an `as_of_date` that precedes the chart's own birth date and
> silently serves computed, `two_pass_verified`-tier dasha rows with no structured pre-birth flag
> or guard — the only signal the query is nonsensical is a free-text narration side-effect
> ("age ~-4"), not a machine-checkable field."

`DIAGNOSIS.md` confirmed this live (`as_of_date='1980-01-01'` vs. birth `1984-02-05` → narration
literally reads `"age ~-4"`, no `judgment_flags` key present at all) and traced the mechanism to
`get_dashas.ts`. This spec adapts the CL-13 reference pattern F-34 establishes (`lanes/F-34/
SPEC.md` §9 — locate the actual-extent signal, compare it to what was requested, expose the
comparison structurally) to this surface's dimension: temporal validity of the query itself, not
horizon coverage of the response. Stage R should take "expose the comparison structurally, not
just in narration" as settled by F-34 and focus review on this file's specific implementation.

## 1. Root-cause statement

`get_dashas.ts`'s `ageAtDate` helper (`platform/src/lib/retrieval/registry/layers/L1_ganita/
get_dashas.ts:471-479`) computes an age string from `birthDate` (already fetched at :451-455 for
this exact purpose) and a period-boundary date with no floor or comparison against `birthDate`,
so a negative age silently reaches the served narration; and `judgment_flags` (declared empty at
:430, the only other push site is `system_facet_unrecognized` at :432-435) has no push site for
this case at all, so the response carries zero machine-checkable evidence that `as_of_date`
preceded `birthDate` — the sole tell is a negative integer inside free text.

## 2. Files to change

### 2a. `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts`

**Add a structured pre-birth flag, computed from the same `birthDate`/`containsDate` values
already in scope — no new query.**

Near :448 (`if (containsDate && systemApplied === 'vimshottari')`), immediately after `birthDate`
is resolved (:455) and before it is used for `ageAtDate` (:471+), add the comparison:

```ts
const asOfPrecedesBirth =
  containsDate != null && birthDate != null && containsDate < birthDate  // ISO 'YYYY-MM-DD' string compare is safe here — ganita_dasha_periods_get requires ISO date strings
if (asOfPrecedesBirth) {
  judgment_flags.push(judgmentFlag(
    'as_of_date_precedes_birth',
    `The requested as_of_date (${containsDate}) is before this chart's birth_date (${birthDate}). ` +
    `The dasha periods below are still real, correctly-computed classical anchors (a Vimshottari ` +
    `Mahadasha's balance-of-dasha start date routinely precedes birth by construction) — they are ` +
    `NOT wrong data. What is flagged is the QUERY: reading these rows as "the dasha running on ` +
    `${containsDate}" attributes lived experience to a pre-birth date, which this chart cannot have. ` +
    `Treat ages in the narration below as arithmetic labels, not lived-experience claims, for any ` +
    `date before ${birthDate}.`
  ))
}
```

`judgmentFlag(...)` is the existing helper already used at :432-435 for `system_facet_unrecognized`
— reuse it, do not invent a second flag-construction pattern. Place this flag FIRST in the array
(unshift, or push before the `system_facet_unrecognized` check) so it is not buried behind a
lower-severity facet warning if both somehow fire together — mirrors `attachDomainCompleteness`'s
own "un-missable structured flag... prepended" convention in `registry_bridge.ts` (F-31's spec,
same campaign, same convention — consistency across S3's disclosure fixes).

**Do not change `ageAtDate` itself.** Flooring or nulling the age computation would remove
information (`DIAGNOSIS.md`'s C4: the negative age is arithmetically correct and, once flagged, is
useful — "9 years before birth" is real balance-of-dasha math). The fix is disclosure at the query
level, not suppression at the arithmetic level — matches F-34's own §9 principle #2 ("expose the
comparison... never only in prose") without deleting the prose signal that already exists.

### 2b. `platform/src/lib/retrieval/registry/layers/L1_ganita/get_tajik.ts` (sibling, §4)

Same guard shape, different consequence (an honest-empty `l1_tajik_varsha_year_lords` result
rather than a populated-but-nonsensical one — see §4). Add a parallel structured flag: near the
`resolveVarshaYearForDate` call site (~:185, current fetched-birthDate block), when
`varsha_date < birthDate`, push a `varsha_date_precedes_birth` flag (or the query's local
equivalent of the `judgment_flags` array — S5 builder should confirm `get_tajik.ts`'s existing
flag-array pattern, since this diagnosis did not verify it carries one; if it doesn't, add the
minimal `judgment_flags: JudgmentFlagEntry[]` scaffold matching `get_dashas.ts`'s own shape rather
than inventing a new response contract).

## 3. Exit tests (both fail today, both named)

New test file: `platform/src/lib/retrieval/registry/layers/L1_ganita/__tests__/
get_dashas_prebirth_disclosure.test.ts`

```ts
test('ganita_dasha_periods_get flags as_of_date preceding birth_date structurally', async () => {
  const res = await queryGetDashas({
    chart_id: CANONICAL_CHART_ID,   // birth_date 1984-02-05
    as_of_date: '1980-01-01',
    ayanamsha_id: 'lahiri_chitrapaksha',
  })
  expect(res.judgment_flags).toBeDefined()
  expect(res.judgment_flags.some((f: any) =>
    (typeof f === 'string' ? f : f.flag) === 'as_of_date_precedes_birth'
  )).toBe(true)
})

test('ganita_dasha_periods_get does NOT flag a normal in-range as_of_date', async () => {
  const res = await queryGetDashas({
    chart_id: CANONICAL_CHART_ID,
    as_of_date: '2020-01-01',
    ayanamsha_id: 'lahiri_chitrapaksha',
  })
  expect(
    (res.judgment_flags ?? []).some((f: any) =>
      (typeof f === 'string' ? f : f.flag) === 'as_of_date_precedes_birth'
    )
  ).toBe(false)
})
```

Today: first test fails (`judgment_flags` key is entirely absent from the response — confirmed
live in `DIAGNOSIS.md` §1's raw JSON). After the fix: first test passes (`judgment_flags` present
with the new flag), second test passes unchanged (no regression to the normal-date path — `2020-
01-01 < 1984-02-05` is false, `asOfPrecedesBirth` stays false, nothing new fires).

A parallel test for `get_tajik.ts`'s `resolveVarshaYearForDate` sibling (§2b) — named
`platform/src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_tajik_prebirth_disclosure.test.ts`
— is the S5 builder's responsibility to write following the same red/green shape once §2b's exact
flag mechanism is confirmed against the live file (see §2b's own caveat).

## 4. Sibling sites covered (from `DIAGNOSIS.md` §4)

| File | Same defect class? |
|---|---|
| `get_dashas.ts:452` (`ageAtDate`, this finding) | **YES — F-33, covered §2a** |
| `get_graha_yuddha.ts:148` | **NO — excluded.** `birth_date` is the fixed point being queried (an ephemeris lookup AT birth), not compared against a caller-supplied date. No caller-suppliable date is ever checked against it, so there is no pre-birth query to flag. |
| `get_tajik.ts:22-30`/`:180` (`resolveVarshaYearForDate`) | **YES — genuine sibling, covered §2b.** Consequence differs (honest-empty `varsha_year<=0` filter result vs. F-33's populated-but-nonsensical result) but root cause is identical: no `birth_date`-vs-input comparison, no structured flag. |

No other file under S5's `L1_ganita/**` lease was found sharing this exact "fetch birth_date,
compute plain-JS date arithmetic against a caller-supplied date, no guard" shape (per
`DIAGNOSIS.md`'s own grep — S5 builder should re-run the sibling grep at build time in case a new
file has landed in `L1_ganita/**` since this diagnosis, per plan §3 Stage-S requirement 4's "or a
written reason a site is excluded").

## 5. Recurrence guard

The two exit tests in §3 are the guard for `get_dashas.ts`; the parallel test in §2b/§3 is the
guard for `get_tajik.ts`. No new lint proposed — this is a two-file, two-flag fix, not a
generated-harness-class defect (contrast CL-03's param-parity harness) — a lint would be
disproportionate machinery for two call sites. If a third `L1_ganita/**` file is found at build
time sharing this shape (§4's caveat), extend this table and add its own exit test rather than
retrofitting a generic harness after the fact.

## 6. Dependencies and rollback

**Dependencies:** none on other in-flight S3 lanes. Depends on S5's own lease/build queue for
`L1_ganita/**` — this spec does not know S5's current file-lock state; S5's builder sequences it
normally.

**Rebuild dependency (ND-PARISESA-1 compliance):** **none.** `get_dashas.ts`/`get_tajik.ts` are
both TS serving-layer files under `platform/src/lib/retrieval/registry/layers/L1_ganita/` — live
query-time code, not `@register` orchestrator writers (confirmed: no `@register`/`WriterBase`
pattern in either file; they run `query(...)` directly against already-built `chart_dashas`/
`l1_tajik_varsha_year_lords` tables per request). This fix applies to every existing chart
immediately on deploy — no rebuild needed, nothing pending native permission.

**Rollback:** revert the code commit. No schema change, no migration, no DB write — purely
additive response fields behind existing conditionals. Zero risk to any other tool sharing
`get_dashas.ts`'s handler (`ganita_dashas_get`/`query_dasha_periods` are the same handler per
`DIAGNOSIS.md` §3 — this fix benefits all three tool names identically, they are one code path).

## 7. Coverage table — every D-2 sub-claim mapped

| Sub-claim | Spec element |
|---|---|
| C1: `as_of_date` preceding birth is accepted with no validation/rejection | §2a — NOT rejecting the query (data stays real, per C4), but now flagging it |
| C2: fully-formed `two_pass_verified` rows served regardless | Unchanged by design (§2a's "do not change `ageAtDate`" note) — C2 is not a defect per C4's own analysis, only the missing disclosure (C3) is |
| C3: only tell is a negative integer buried in free text | §2a's `as_of_date_precedes_birth` structured flag — now machine-checkable, narration untouched (arithmetic stays correct and visible) |
| C4: this may be by-design for the math, fix target is query disclosure not data correction | §2a's design note explicitly preserves this — confirms C4 as the spec's own operating assumption, not just the diagnosis's |
| Sibling (`get_tajik.ts`, found in diagnosis §4, not an original sub-claim but required coverage) | §2b |

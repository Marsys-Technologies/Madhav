---
lane: F-14 (exemplar spec — also closes F-15, F-124; also intended to close S3's F-31 pending
  conductor/S3 dedup confirmation; also closes the domain_completeness/completeness_directive
  half of F-112)
stream: S2 (MĀTRĀ), file owner of registry_bridge.ts
stage: S — SPEC
author: MATRA-LEAD (S2)
status: DRAFT — awaiting VERIFIER review
---

# SPEC — assess_* domain-family wiring + buildAssessResponse key-mismatch

## 0. Cross-stream note (read first)

Per conductor routing (heartbeat message): S3 independently diagnosed **F-31** (assess_health
missing disclosure) and traced it to the exact same mechanism this spec covers — missing
`attachDomainCompleteness`/`attachDomainReading` calls + missing `DOMAIN_READING_FAMILIES` keys
in `registry_bridge.ts` (S2 HOT). This spec is written to close **F-14, F-15, F-124, and F-31**
together as one fix, plus the `domain_completeness`/`completeness_directive` portion of **F-112**
(see §5 for why F-112's byte-budget portion is unaffected and already closed). Do not build F-31
separately from this spec — if S3's own SPEC.md for F-31 lands first or differs, the two must be
reconciled by the conductor/VERIFIER into one build, not built twice against the same lines of
`registry_bridge.ts`.

## 1. Root-cause statement

`assess_marriage` and `assess_health` never call the reading/completeness attach functions at
all (a missing call-site gap), the five `DOMAIN_READING_*` maps have no `health`/`relationship`
entries (a missing data-table gap), and — independently, affecting all four `assess_*` tools
including `assess_career`/`assess_wealth` — `buildAssessResponse`'s grounding-layer assembly
reads the wrong key (`response['completeness']`, which nothing ever sets) instead of the key the
attach functions actually populate (`response['domain_completeness']`), and never surfaces
`completeness_directive` at all. Three independent, all-necessary gaps; fixing only one leaves
the tool(s) still silent on some or all of `reading`/`domain_completeness`/`completeness_directive`.

## 2. Files to change (all inside S2's HOT lease, `platform-mcp/src/tools/registry_bridge.ts` —
no cross-stream lease conflict for this spec)

### 2a. Add `health`/`relationship` keys to the five domain maps (`:1020-1043`)

```ts
const HEALTH_READING_FAMILIES = [
  'per_varga_ashtakavarga', 'divisional_D6', 'divisional_D1',
  'argala_house_1', 'argala_house_6', 'argala_house_8', 'full_dispositor_closure',
  'all_chart_mechanisms_and_chains', 'special_lagnas', 'cross_ayanamsha_agreement',
  'timing_windows', 'remedies', 'contradictions_with_adjudication',
] as const

const RELATIONSHIP_READING_FAMILIES = [
  'per_varga_ashtakavarga', 'divisional_D9', 'divisional_D1',
  'argala_house_7', 'full_dispositor_closure',
  'all_chart_mechanisms_and_chains', 'special_lagnas', 'cross_ayanamsha_agreement',
  'timing_windows', 'remedies', 'contradictions_with_adjudication',
] as const

const DOMAIN_READING_FAMILIES: Record<string, readonly string[]> = {
  wealth: WEALTH_READING_FAMILIES,
  career: CAREER_READING_FAMILIES,
  health: HEALTH_READING_FAMILIES,
  relationship: RELATIONSHIP_READING_FAMILIES,
}
const DOMAIN_READING_VARGAS: Record<string, [string, string]> = {
  wealth: ['D2', 'D11'], career: ['D10', 'D9'], health: ['D6', 'D1'], relationship: ['D9', 'D1'],
}
const DOMAIN_READING_HOUSES: Record<string, number[]> = {
  wealth: [2, 11], career: [10], health: [1, 6, 8], relationship: [7],
}
const DOMAIN_READING_KARAKA_CODE: Record<string, string> = {
  wealth: 'JUP', career: 'SAT', health: 'SUN', relationship: 'VEN',
}
const DOMAIN_READING_KARAKA_LABEL: Record<string, string> = {
  wealth: 'Jupiter', career: 'Saturn', health: 'Sun', relationship: 'Venus',
}
```

**BUILD-STAGE INSTRUCTION, not spec-invented content (B.10 compliance):** the house/karaka
assignments above (health: houses 1/6/8, karaka Sun; relationship: house 7, karaka Venus) are
taken directly from `register_d8_assess_domain.ts`'s own tool descriptions ("1st+6th+8th lords +
Sun kāraka" for assess_health at `:3042` docstring; "7th lord + Venus kāraka" for assess_marriage
at `:2960` docstring — both already live in the file, quoted verbatim in this spec, not derived).
The varga assignments (D6/D1 health, D9/D1 relationship) match `DOMAIN_DIRECT_VARGAS`
(`register_d8_assess_domain.ts:184-188`, already live: `relationship: ['D9'], health: ['D6']` —
D1 added per the wealth/career pattern which also includes the base D1 rasi chart implicitly via
`all_chart_mechanisms_and_chains`; BUILD must re-verify against the live docstrings/maps at
build time in case of drift between this spec's drafting and build, and must NOT invent a family
list — copy the WEALTH/CAREER shape, substitute only the already-established varga/house/karaka
facts named above). If Build finds these facts have drifted from what's quoted here, it stops
and re-derives from the live file rather than trusting this spec's transcription.

### 2b. Add attach calls to `assess_marriage` (near `:2986-2989`) and `assess_health`
(near `:3068-3071`), mirroring `assess_career`'s existing two lines exactly:

```ts
const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
attachDomainCompleteness(response, 'relationship', chart_id)   // assess_marriage
await attachDomainReading(response, 'relationship', chart_id, normalizeAyanamsha(ayanamsha_id), principal)
return dualOutputBudgeted(buildAssessResponse(response, 'assess_marriage', budget_kb, effectiveVerbosity))
```
(and the `'health'` equivalent in `assess_health`'s handler, same two-line pattern.)

**Domain key note:** `assess_marriage` internally uses domain key `'relationship'` (matches
`register_d8_assess_domain.ts`'s `DOMAIN_DIRECT_VARGAS['relationship']` and the tool's own
`marsys://tool/L-DOMAIN/assess_marriage` capability convention, NOT the literal string
`'marriage'` — confirmed by reading `attachDomainCompleteness`'s call pattern for `assess_career`,
which passes `'career'` not `'assess_career'`; the domain key is the SHASTRA_MAP-style short
name). `assess_health` uses `'health'`.

### 2c. Fix `buildAssessResponse`'s grounding-layer key mismatch (`:2923-2927`)

Current (wrong):
```ts
if (response['reading'] !== undefined) grounding['reading'] = response['reading']
if (response['completeness'] !== undefined) grounding['completeness'] = response['completeness']
```

Fixed:
```ts
if (response['reading'] !== undefined) grounding['reading'] = response['reading']
if (response['domain_completeness'] !== undefined) grounding['domain_completeness'] = response['domain_completeness']
if (response['completeness_directive'] !== undefined) grounding['completeness_directive'] = response['completeness_directive']
```

This one hunk alone restores `domain_completeness`/`completeness_directive` to `assess_career`
and `assess_wealth` (already calling the attach functions, but silently losing both fields at
assembly) as well as to `assess_marriage`/`assess_health` once 2b lands.

## 2d. NEW — honest null-case disclosure in `attachDomainCompleteness` (added post-S3-dedup-review;
additive, does not change §2a/§2b/§2c)

**Gap found by S3's F-31 dedup review, confirmed real:** `assembleDomainCompleteness`
(`:678-...`) returns `null` whenever `runDossier({domain, chart_id, budget_kb: 64})` throws or
`page.ok` is false — this is exactly what happens today for `domain='health'` and
`domain='relationship'`, because only `career_*`/`wealth_*` dossier slice bundles are precompiled
on `origin/main`; no `health_*`/`relationship_*` bundles exist. `attachDomainCompleteness`
(`:835-837`) then does `if (!completeness) return` — a **silent** no-op, no field, no flag,
nothing distinguishing "this domain has no precompiled slice yet" from "this call simply wasn't
made." Even after §2a (map keys) and §2b (call sites) land, `assess_health`/`assess_marriage`
would STILL surface no `domain_completeness`/`completeness_directive` — silently, which is a §N.7
item 6 violation ("an honest null beats an invented judgment" — the current behavior is worse
than that: it's not even a null, it's nothing at all).

**PRATINIDHI ruling (via conductor, "disclose more" standing tie-breaker):** generating new
`health_*`/`relationship_*` dossier slice bundles is real data-generation infrastructure, out of
this finding's reasonable size (and PARIŚEṢA's scope generally — flagged as its own future
finding, not built here). The in-scope fix is disclosure: `attachDomainCompleteness` must not
silently no-op when no slice exists — it must say so.

**Fix — `registry_bridge.ts:835-837`, before the early return:**

```ts
export function attachDomainCompleteness(response: Record<string, unknown>, domain: string, chart_id: string): void {
  const completeness = assembleDomainCompleteness(domain, chart_id)
  if (!completeness) {
    response['domain_completeness_empty_reason'] =
      `No precompiled ${domain} concept-slice bundle exists yet — domain_completeness/` +
      `completeness_directive are honestly omitted rather than fabricated (B.10). This is a data-` +
      `infrastructure gap (bundle generation), not a query failure; tracked separately from this fix.`
    return
  }
  response['domain_completeness'] = completeness
  ...
```

`buildAssessResponse`'s grounding assembly (§2c) gets one more conditional line alongside the
`domain_completeness`/`completeness_directive` ones:
```ts
if (response['domain_completeness_empty_reason'] !== undefined) {
  grounding['domain_completeness_empty_reason'] = response['domain_completeness_empty_reason']
}
```
`IMMUNE_HONESTY_FIELDS` (`response_budget.ts:56-101`) should also gain
`domain_completeness_empty_reason` alongside the existing `domain_completeness`/
`completeness_directive` entries, so this disclosure field can never itself be trimmed away.

**Explicitly out of scope for PARIŚEṢA:** generating `health_*`/`relationship_*` dossier slice
bundles themselves. This spec closes the DISCLOSURE half of F-31/F-15's `domain_completeness`
sub-claim (a caller can now tell, honestly, why the field is missing) — it does not make the
field populated for health/relationship. That remains a real, separately-scoped gap.

## 3. Exit test

New test file: `platform-mcp/src/tools/__tests__/assess_domain_reading_parity.test.ts`

```ts
// Fails today (before this fix) — assess_health/assess_marriage responses at standard depth
// lack `reading`, and ALL FOUR assess_* responses lack `domain_completeness`/
// `completeness_directive` in their grounding layer (and lack ANY disclosure of why, for
// health/marriage specifically, once bundles are confirmed absent).
test('reading digest: all four assess_* tools surface substance-inline reading', async () => {
  for (const tool of ['assess_wealth', 'assess_career', 'assess_marriage', 'assess_health']) {
    const res = await callTool(tool, { chart_id: CANONICAL_CHART_ID })
    const grounding = res.structuredContent.object.grounding
    expect(grounding).toHaveProperty('reading')
    expect(Array.isArray(grounding.reading)).toBe(true)
    expect(grounding.reading.length).toBeGreaterThan(0)
  }
})

test('completeness accounting: honest presence OR honest absence-disclosure, never silent', async () => {
  // career/wealth: precompiled dossier bundles exist -> real domain_completeness populated.
  for (const tool of ['assess_wealth', 'assess_career']) {
    const grounding = (await callTool(tool, { chart_id: CANONICAL_CHART_ID })).structuredContent.object.grounding
    expect(grounding).toHaveProperty('domain_completeness')
    expect(grounding).toHaveProperty('completeness_directive')
    expect(grounding).not.toHaveProperty('domain_completeness_empty_reason')
  }
  // health/marriage: no precompiled bundle today -> honest empty-reason disclosure, NOT a silent
  // omission and NOT a fabricated map.
  for (const tool of ['assess_marriage', 'assess_health']) {
    const grounding = (await callTool(tool, { chart_id: CANONICAL_CHART_ID })).structuredContent.object.grounding
    expect(grounding).not.toHaveProperty('domain_completeness')
    expect(grounding).toHaveProperty('domain_completeness_empty_reason')
    expect(String(grounding.domain_completeness_empty_reason)).toMatch(/no precompiled/i)
  }
})
```
Today: the `reading` test fails for `assess_marriage`/`assess_health` (key absent). The
completeness test fails for career/wealth on `domain_completeness`/`completeness_directive`
(silently dropped by the `:2923-2927` key mismatch) and fails for health/marriage on
`domain_completeness_empty_reason` (doesn't exist yet — today's behavior is a fully silent
no-op). After the fix: both pass. If a `health_*`/`relationship_*` bundle is later generated
(out of scope here), the second test's health/marriage branch would need updating to the
career/wealth pattern — that is expected, tracked evolution, not a defect in this exit test.

## 4. Sibling sites covered

All five `DOMAIN_READING_*` maps (§2a) — no map is left wealth/career-only. Both missing
call-sites (§2b) — no third silent handler remains (there are only 4 `assess_*` tools total per
Stage-D's census, all four now covered). The `buildAssessResponse` key mismatch (§2c) is a single
shared function serving all four tools — one fix, not four.

## 5. Recurrence guard

The exit test in §3 iterates all four `assess_*` tools by name — any future fifth `assess_*` tool
that forgets to wire itself in, or any future edit to `buildAssessResponse`'s grounding allow-list
that drops a key again, fails this test immediately. Recommend also adding a static lint (out of
scope for this spec, flagged for a follow-up finding if the conductor wants it): assert
`Object.keys(DOMAIN_READING_FAMILIES)` matches the SHASTRA_MAP's canonical domain set exactly.

## 6. Dependencies and rollback

No DB migration, no other lane's build must land first. Rollback: revert the single commit; all
three changes are additive/corrective within one file, no schema or contract change to any other
tool. **Not reopening F-56/F-111**: `buildAssessResponse`'s `evidence`-layer routing of
`verdict_skeleton`/`activating_dasha` (the actual F-56/F-111 fix) is untouched by this spec —
§2c only edits the `grounding` object's key names, three lines, none of which touch `evidence`.
**F-112 status**: this spec closes F-112's `domain_completeness`-drops-silently half. F-112's
original claim (an oversized, unbudgeted `domain_completeness` block dominating response bytes)
does not reproduce today — `domain_completeness` was being silently dropped entirely (§2c is why),
not shipped oversized — so F-112 as originally worded does not currently reproduce; this spec's
§2c fix will make `domain_completeness` appear in `grounding` again, which is bounded by
`assembleSaraContent`'s normal budget path (the same mechanism already correctly excludes
`evidence` at tight budgets) — no new size-blowup risk expected, but Stage V should re-run F-112's
original `reproduce_cmd` post-deploy to confirm the object stays within `grounding`'s effective
share of the budget and doesn't reintroduce byte bloat.

## 7. Known, deliberately out-of-scope issue (flag for conductor, not fixed by this spec)

Stage-D's F-14 diagnosis (§5) found a THIRD, more severe defect not part of any of F-14/F-15/
F-124/F-31/F-112's stated claims: at `reading_depth:'deep_dive'`, `assembleSaraContent`'s
all-or-nothing layer-inclusion algorithm (`response_budget.ts:781-800`) drops the ENTIRE
`grounding` layer for ALL FOUR `assess_*` tools — including `assess_career`, which the corpus
believed worked correctly — once the B.11-mandated full-form orientation pre-fetch pushes
`kernel+grounding` past the 40KB ceiling. This spec's fix (adding `reading`/`domain_completeness`
back into `grounding`) does NOT help a `deep_dive` caller, because `grounding` itself is dropped
before this spec's fields are ever considered — a caller using the literal reproduce_cmd from
F-14's own finding text (`reading_depth:'deep_dive'`) will still see no `reading` on any domain
after this fix ships. **Recommending a new, separately-scoped finding** for `assembleSaraContent`'s
budget interaction with the forced deep_dive orientation payload — out of this spec's exit-test
coverage; VERIFIER should confirm this spec is not mis-sold as closing the deep_dive case.

## 8. Coverage table — every D-2 sub-claim mapped

| Sub-claim | Finding | Spec element |
|---|---|---|
| C1: assess_health never returns `reading` | F-14 | §2a (health map key) + §2b (health call sites) |
| C2/C3: assess_health never returns `domain_completeness`/`completeness_directive` | F-14 | §2a + §2b + §2c |
| Identical for assess_marriage | F-15 | §2a (relationship key) + §2b (marriage call sites) + §2c |
| "wired to career only, is this the same gap" | F-124 | §2a/§2b confirm yes for `reading`; §2c is the ADDITIONAL gap F-124 didn't name but that also suppresses its `domain_completeness` claim | 
| F-31 (S3): assess_health missing disclosure | F-31 | §2a/§2b/§2c (reading) + §2d (honest empty-reason disclosure for domain_completeness, since no health bundle exists — closes the DISCLOSURE claim; does not populate the field, see §2d's explicit scope note) |
| F-112: domain_completeness dropped/mis-surfaced | F-112 | §2c (see §6 for the "original claim doesn't reproduce as worded" nuance) |
| S3 dedup-review gap: silent no-op when no dossier slice bundle exists for a domain | (found during S3/S2 dedup review, not an original finding) | §2d |
| Out-of-scope deep_dive all-or-nothing grounding drop | (new, unfiled) | explicitly NOT closed — §7 |

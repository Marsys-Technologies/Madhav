# F-13 DIAGNOSIS — `kala_ritual_get` has no response-size control on either mode

Stream: S2 MĀTRĀ. Files: `platform-mcp/src/tools/kala_views/ritual.ts` (S2 HOT), consuming
`platform-mcp/src/lib/kala_lattice_query.ts`, `platform-mcp/src/lib/kala_sky_pattern.ts`,
`platform-mcp/src/lib/kala_ritual_resonance.ts` (all S2). Doctrine violated: CLAUDE.md §N.6
(Serving Density Principle) — specifically item 2 ("the densest, most-actionable layer is the
one a budget trim protects first") is unreachable here because **no trim of any kind runs**.

Read per the Stage-D contract: `PARISESA_EXECUTION_PLAN_v1_0.md` §3 (Stage D — DIAGNOSE) and
CLAUDE.md §N.6, both read before this document was written.

## 1. Live reproduction

Both calls were run verbatim against the live MCP server (`mcp__marsys-jis-direct__kala_ritual_get`,
canonical chart `482012f1-710e-4a25-994a-93821f5871aa`). Raw JSON saved to this lane dir:
- `repro_mode2_pattern_search_raw.json` — 1,330,235 bytes, 15,442 lines.
- `repro_mode1_opportunity_scan_raw.json` — 579,227 bytes, 8,954 lines.

**Mode 2** (`sky_pattern_spec: {all:[{factor_type:'vara',factor_id:6}], horizon:{months:3}}`):
```
Error: result (1,303,577 characters across 15,443 lines) exceeds maximum allowed tokens.
```
i.e. **1.30MB / ~15,420 lines** — matches the finding's cited figures almost exactly (the small
delta is live-data drift: the finding was filed against a slightly different day's ephemeris/
build state, not a different mechanism).

**Mode 1** (`horizon: '90d', limit: 10`):
```
Error: result (571,951 characters across 8,954 lines) exceeds maximum allowed tokens.
```
i.e. **~570KB / ~8,899 lines** in the finding's framing — again matches almost exactly.

**Schema check** (live `tool_search`/MCP tool listing): `kala_ritual_get`'s registered input
schema (`KalaRitualInputShape`, `ritual.ts:140-166`) has fields `chart_id, horizon,
sky_pattern_spec, undertaking, question_frame, activity_class, limit` — **no `budget_kb` /
`max_kb` field of any kind.** By contrast, live schema fetch confirms `kala_elect_get` has
`budget_kb` (`"Response size ceiling in KB. Default 40."`) and `kala_story_get` has the same
(`"Response size ceiling in KB. Default 40."`). Confirmed: **not** DIAGNOSIS-INCOMPLETE — this
part of the finding is exactly right.

This finding **reproduces exactly as filed.** Not `ALREADY-FIXED`.

## 2. Claim decomposition

| # | Sub-claim | Verdict |
|---|---|---|
| A | `kala_ritual_get` has no response-size control on either mode | **TRUE** — confirmed by full read of `ritual.ts`: zero references to `budget_kb`, `finalizeMcpBudget`, `kalaBudgetedDualOutput`, or any `TrimmableSection`. |
| B | Mode-2 call produces ~1.30MB/~15,420 lines | **TRUE** — reproduced at 1,330,235 bytes / 15,442 lines (§1). |
| C | Mode-1 call (`limit=10`) produces ~570KB/~8,899 lines | **TRUE** — reproduced at 579,227 bytes / 8,954 lines (§1). Note: only 8 opportunities were returned despite `limit=10` (fewer qualifying windows existed in this 90d horizon) — the byte count is still driven to ~570KB by 8 candidates, not 10, which strengthens rather than weakens the finding: the driver is not "hitting the requested limit," it's per-candidate cost. |
| D | Driver: an exhaustive per-candidate census (`gap_report.factors_not_computed`/`factors_not_in_corpus`), multi-paragraph prose per candidate window, multiplied across every candidate | **PARTIALLY WRONG — corrected below (§3).** The named field (`gap_report.factors_not_computed`/`factors_not_in_corpus`, i.e. `LatticeGapReport`/`SkyPatternGapReport.census`) is computed **once per call**, not per candidate, and is small (17 total entries, 14,658 bytes in the Mode-2 repro — ~1.2% of the response). The **real** driver is the per-candidate/per-window `JudgmentLedger` (`dosas_present`, `pariharas_applied`, `residual_dosas`, `supporting_factors`, `neutral_annotations`, `convention_only_factors`, `convention_only_keys`) built by `buildLedger()`/`adjudicateCandidates()` in `kala_lattice_query.ts` — one full ledger per Mode-2 candidate and one full ledger per Mode-1 window, each carrying every lattice row (with multi-line `source_citation` prose) that overlaps that candidate's interval. |
| E | `kala_ritual_get`'s schema exposes no `budget_kb`/`max_kb`, unlike sibling `kala_story_get` (has `budget_kb`, default 40, demonstrably trims with a `trim_report`) | **TRUE** — confirmed live (§1). `story.ts` calls `finalizeMcpBudget` (`story.ts` grep: `budget_kb_param=1 finalizeMcpBudget_call=1`). |

The DIAGNOSIS-INCOMPLETE the finding carried was specifically on sub-claim D's driver — closed
in §3 below with exact file:line and measured proof, not a guess.

## 3. Mechanism — file:line, with measured proof

### 3a. `ritual.ts` has zero budget wiring (confirms claim A)

Full read of `platform-mcp/src/tools/kala_views/ritual.ts` (697 lines) — no import of
`response_budget.ts`, `finalizeMcpBudget`, or `kalaBudgetedDualOutput` (the shared helper other
`kala_views/*.ts` files use — see §4). The registration handler simply serializes the whole
response:

```ts
// ritual.ts:679-694 (registerKalaRitualGet)
const response = await handleKalaRitualGet({...}, principal)
return {
  content: [{ type: 'text' as const, text: JSON.stringify(response, null, 2) }],
}
```

No size measurement, no trim, no ceiling — whatever `handleKalaRitualGet` returns ships verbatim.

### 3b. Mode 2 — the real driver is `adjudication.ledgers[]`, not `census`

`handleKalaRitualGet` (`ritual.ts:470-500`) calls `searchSkyPattern()` and assigns its full
return value, unmodified, to the response's `pattern_search` field:

```ts
// ritual.ts:198-211 (KalaRitualResponse)
pattern_search: SkyPatternSearchResult | null   // Mode 2 only — the compiled search result.
...
// ritual.ts:575-584 (return)
return {
  ...envelope,
  ...
  pattern_search: patternSearch,     // <- the WHOLE SkyPatternSearchResult, no trim
  opportunities,
  ...
}
```

`searchSkyPattern()` (`kala_sky_pattern.ts:952-1152`) intersects the spec's constraints down to
a set of in-horizon candidate intervals, then — **once, over the whole candidate set** — calls
the shared lattice engine:

```ts
// kala_sky_pattern.ts:1098-1103
const adjudication =
  intervals.length > 0
    ? adjudicateCandidates(intervals, substrate, {
        subject_label: params.subjectLabel ?? 'declared sky pattern (YAJÑA-SETU Mode 2)',
      })
    : null
...
// kala_sky_pattern.ts:1149
return { candidates, gap_report, coverage, precision, adjudication, paddhati }
```

`adjudicateCandidates()` (`kala_lattice_query.ts:570-638`) builds **one full `JudgmentLedger` per
candidate**:

```ts
// kala_lattice_query.ts:575-576
const rows = substrate.lattice_available ? substrate.lattice_rows : []
const ledgers = candidates.map((c) => buildLedger(c, rows, substrate))
```

`buildLedger()` (`kala_lattice_query.ts:331-416`) attaches **every lattice row that overlaps that
one candidate's `[start,end)` interval** — split into `dosas_present`, `supporting_factors`,
`neutral_annotations` (cited rows) and `convention_only_factors`/`convention_only_keys`
(uncited-convention rows, §N.6), each entry a `LedgerFactor` with `factor_family`, `factor_key`,
`start_utc`, `end_utc`, and a `source_citation` string that is frequently >150 chars of classical
citation prose (see `kala_lattice_query.ts:170-189`, the `JudgmentLedger` interface).

**Why this exploded to 1.14MB from a single candidate:** in the live repro, my supplied
constraint (`{factor_type:'vara', factor_id:6}`) does not match any of sky_pattern_spec v1's nine
frozen constraint keys (`kala_sky_pattern.ts` `SKY_PATTERN_CONSTRAINT_KINDS`), so it is dropped
as `unknown_kind` (`kala_sky_pattern.ts:992-1005`) and the search proceeds **unconstrained** —
collapsing to exactly **one** candidate interval that spans the entire 3-month scan window
(`2026-08-16T07:53:08Z → 2026-11-14T07:53:08Z`). That one candidate's ledger therefore absorbs
**every lattice row in the substrate for that whole span**. Measured from the saved repro JSON:

```
candidates: 1        adjudication.ledgers: 1 (id "sp0")
  dosas_present:            130
  pariharas_applied:         23
  residual_dosas:           107
  supporting_factors:        48
  neutral_annotations:      617
  convention_only_factors: 1205   <- single largest contributor
  convention_only_keys:      53

byte sizes:
  whole response:        1,179,331 B
  pattern_search:        1,174,719 B  (99.6% of response)
  pattern_search.adjudication: 1,156,698 B
    -> single ledger "sp0":    1,140,279 B  (96.7% of the WHOLE response)
  pattern_search.gap_report.census (factors_not_computed[9]+factors_not_in_corpus[8]): 14,658 B
```

The census the original finding named is real but **tiny** (1.2% of the response). The actual
driver is the single `JudgmentLedger`'s `convention_only_factors` array (1,205 `LedgerFactor`
objects, each with a citation string) plus its four other factor arrays. This is a general
property, not specific to an unconstrained search: **any** Mode-2 candidate whose window spans
more than a few hours will absorb dozens of `kalam`/`hora`/`combination_yoga`/`nakshatra`/`tithi`/
`vara`/`agnivasa` rows, because the lattice ships those families at fine granularity (hourly for
`hora`, several-per-day for `kalam`), and every overlapping row — cited or convention — is served
in full with no cap (`buildLedger`, `kala_lattice_query.ts:336-350`, has no length limit on
`overlapping`/`cited`/`convention`).

### 3c. Mode 1 — the same engine, called once per window, plus a second un-budgeted substrate

`scoreMode1Opportunities()` (`kala_ritual_resonance.ts:632-720`) loops over the (up to `limit`)
candidate windows and, **for each window**, calls the same shared engine through
`scoreElectionQuality()`:

```ts
// kala_ritual_resonance.ts:505-511 (scoreElectionQuality)
export function scoreElectionQuality(
  candidate: CandidateInterval, substrate: LatticeSubstrate, subjectLabel: string,
): { factor: ScoredFactor; ledger: JudgmentLedger | null } {
  const source = 'kala_lattice_query.adjudicateCandidates (the FROZEN shared engine) — judgment_ledger'
  const adjudication = adjudicateCandidates([candidate], substrate, { subject_label: subjectLabel })
  const ledger = adjudication.ledgers[0] ?? null
  ...
```

```ts
// kala_ritual_resonance.ts:654-706 (the per-window loop)
for (const [i, w] of params.windows.entries()) {
  ...
  const { factor: electionQuality, ledger } = scoreElectionQuality(
    { id: `m1_${i}`, start: w.start_utc, end: w.end_utc, score: 0, disqualified: false },
    params.substrate, params.subjectLabel,
  )
  ...
  opportunities.push({ window: {...}, rite: {...}, score_vector: vector, judgment_ledger: ledger, ... })
}
```

Every `RitualOpportunity` in `Mode1Result.opportunities[]` therefore carries its own full
`judgment_ledger` (`kala_ritual_resonance.ts:580-598`, `RitualOpportunity.judgment_ledger:
JudgmentLedger | null`). Measured from the saved Mode-1 repro (8 opportunities returned):

```
whole response:            491,078 B
opportunities (object):    487,202 B
  8x judgment_ledger:      292,826 B  (60% of response) — per-opportunity: 7.7K .. 51.5K B
  structural (once, top-level, NOT per-opportunity): 157,699 B  (32% of response)
  activity_rules (once):     8,875 B
  8x score_vector:          ~23,257 B combined
```

Two un-budgeted contributors, not one: (1) the per-window `judgment_ledger`s (§3b's mechanism,
invoked 8 times), and (2) `Mode1Result.structural` — the `StructuralSubstrate` payload
(`remedy_rows`/`resonance_rows` from `fetchStructuralSubstrate`, `kala_ritual_resonance.ts:326-405`)
— which is fetched **once** per call but embedded in full regardless of how many opportunities are
ultimately served (`opportunities.ts` field `structural: StructuralSubstrate`,
`kala_ritual_resonance.ts:612`).

### 3d. Corrected mechanism statement

**F-13's true root cause is not the gap-report census.** It is: (i) `ritual.ts` never calls
`finalizeMcpBudget`/`kalaBudgetedDualOutput` on its response at all (§3a — this alone would be
sufficient to cause unbounded growth even with a tiny census); and (ii) the shared
`adjudicateCandidates`/`buildLedger` engine (`kala_lattice_query.ts:331-416,570-638`) is invoked
once per Mode-2 search and once **per window** in Mode 1 (`kala_ritual_resonance.ts:505-511,
654-667`), and each invocation's `JudgmentLedger` embeds every overlapping lattice row's full
`LedgerFactor` (with citation prose) with no length cap — and Mode 1 additionally embeds the
once-fetched `structural` substrate in full. Both are DIAGNOSIS-COMPLETE now: exact file:line,
exact measured byte contribution per section, reproduced live.

## 4. Sibling census

Grepped every `platform-mcp/src/tools/kala_views/*.ts` (excluding `*.test.ts`) for budget wiring
and lattice/adjudication engine usage:

```
File              budget_kb param   finalizeMcpBudget call   kalaBudgetedDualOutput call   lattice/adjudicate refs
ahead.ts          no                yes (1)                  no                            6  (fetchLatticeSubstrate only — NOT adjudicateCandidates/scoreElectionQuality; grep for judgment_ledger/JudgmentLedger/neutral_annotations/convention_only/dosas_present/residual_dosas in ahead.ts: ZERO hits)
dasha_sandhi.ts   no                no                        no                            0
elect.ts          yes (1)           yes (1)                  no                            6  <- F-122 (has budget wiring, but declared sections are incomplete — see F-122/DIAGNOSIS.md)
explain.ts        no                no                        yes (1)                       0
now.ts            no                yes (1)                  no                            0
priority.ts       no                no                        yes (1)                       0
ritual.ts         no                no                        no                            7  <- F-13 (THIS finding)
shared.ts         n/a (helper lib)  yes (1, inside helper)    n/a                           0
story.ts          yes (1)           yes (1)                  no                            0
upaya.ts          no                no                        no                            0
```

**Within `kala_views/`, `ritual.ts` is the only file that both (a) has zero budget wiring of any
kind and (b) touches the ledger-producing engine** (`adjudicateCandidates` /
`scoreElectionQuality` / `scoreMode1Opportunities` / `searchSkyPattern`). `elect.ts` is the only
other file that touches the same engine, and it does have budget wiring — its defect is a
different shape (declared-section coverage gap, filed separately as F-122; see that lane for the
full mechanism). `ahead.ts` reads the raw lattice substrate (`fetchLatticeSubstrate`) but never
runs it through `adjudicateCandidates`, so it never produces `JudgmentLedger`-shaped data and is
not exposed to this specific defect class — confirmed by a direct grep for
`judgment_ledger|JudgmentLedger|neutral_annotations|convention_only|dosas_present|residual_dosas`
in `ahead.ts`, which returns zero hits. `dasha_sandhi.ts` and `upaya.ts` have zero budget wiring
too, but also zero lattice/adjudication exposure — a different, lower-severity defect class (no
demonstrated unbounded-growth driver), out of scope for this finding but worth a one-line flag
for a future census pass.

**Conclusion: no third sibling of F-13's specific defect exists in `kala_views/`.** The census is
exhaustive for this directory (11 non-test files, all checked).

## 5. Blast radius

- **CL-00 regression battery** (`platform/scripts/governance/ekv_controls.py`, 27 named-finding
  checks: F-32, F-72, F-75-77, F-80, F-82-88, F-91, F-96-103, F-105-106, F-109, F-137-138):
  **F-13 is NOT among the 27 controls checked.** A fix here gets no automatic CL-00 regression
  protection; Stage S should register a recurrence guard per the SPEC contract's item 5 (a
  dedicated size/section-coverage test, not reliance on CL-00).
- **Other lanes sharing these files** (grepped every existing `lanes/*/DIAGNOSIS.md` under this
  worktree): `F-46`, `F-09`, `F-17`, `F-28`, `F-44`, `F-12` all touch
  `platform-mcp/src/lib/response_budget.ts` — `F-46`'s own `NEEDS_LEASE.md` and `F-44`'s
  `DIAGNOSIS.md` both mark that file **S2 HOT (exclusive)**, so no conflict, but any spec that
  edits `response_budget.ts` itself (rather than just `ritual.ts`'s call sites) should sequence
  against those lanes' status. `F-125`'s own sibling-census table (an unrelated B.11-orientation
  defect) separately lists both `kala_views/elect.ts` and `kala_views/ritual.ts` as "high
  interpretive weight" files with no code overlap expected, but worth noting for merge-order
  awareness since both files will be touched by two different lanes (F-13 and F-125) around the
  same time.
- **User-facing impact, independent of the campaign's own controls:** the Mode-2 repro above
  (1.3MB) *itself hit this agent's own MCP tool-output token ceiling* and required a saved-file
  read-around — i.e. this is not a theoretical size concern, it actively breaks normal
  tool-calling flows for any caller (human-driven or agentic) without special-casing large
  results.
- **Shared-file blast radius for the eventual fix:** the natural fix path is either (a) wire
  `ritual.ts` into the existing `kalaBudgetedDualOutput`/`autoDetectTrimmableSections` mechanism
  (`kala_views/shared.ts`, `response_budget.ts` — both already S2 HOT), which is enough to fix
  claim A/B/C's *symptom* (any response, capped) but — per the `autoDetectTrimmableSections`
  depth-1-nesting limit (`response_budget.ts:508-569`, only descends one level:
  `content[key][nestedKey]`) — would **not** reach `pattern_search.adjudication.ledgers[].*` or
  `opportunities[].judgment_ledger.*` (both are 2+ levels deep), so the true driver identified in
  §3 would survive even after wiring the generic helper; or (b) hand-declare explicit
  `TrimmableSection`s for those specific nested arrays, the way `elect.ts` attempted (imperfectly
  — see F-122) for its own `candidates[].judgment_ledger.convention_only_factors`. Both paths stay
  entirely inside S2's existing lease (`ritual.ts`, `kala_lattice_query.ts`, `kala_sky_pattern.ts`,
  `kala_ritual_resonance.ts`, `response_budget.ts`, `kala_views/shared.ts` are all S2-owned per
  the task brief and the file registry). **No NEEDS-LEASE flag required.**

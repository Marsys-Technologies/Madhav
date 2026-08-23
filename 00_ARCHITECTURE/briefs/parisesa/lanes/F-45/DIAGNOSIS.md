# F-45 — DIAGNOSIS (2× diagnosis budget — DIAGNOSIS-INCOMPLETE in the corpus)

Stream: S2 MĀTRĀ (as filed) · Class: CL-06, grouped with F-12/F-36/F-37 — **see
`F-12/DIAGNOSIS.md` §6 for the Flavor-B defect-class definition this finding IS, and §5 for the
BRANCH-EXISTS methodology this doc extends with one narrow correction.**
Files: `platform-mcp/src/tools/register_p1_aliases.ts` (confirmed site, per the brief) +
FOUR newly-traced sites: `platform-mcp/src/tools/register_p1_synthesis.ts`,
`platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`,
`platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts`,
`platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`
Stage: D (DIAGNOSE) · Chart: `482012f1-710e-4a25-994a-93821f5871aa`

## 1. Live reproduction — REPRODUCES on all 5 named tools

| Tool | Call | Narrative field | Sibling array length actually served | Match? |
|---|---|---|---|---|
| `bodha_signals_get` | `top_k=200` | `verdict_summary.served_count: 200` | `signals.length: 20` (`trim_report`: `original_count:200, kept_count:20`) | **MISMATCH** |
| `synth_chart_brief_get` | `depth='complete'` | `coverage_receipt` text: "**27** domain verdicts" | `verdict_summary.length: 13` (`trim_report`: `original_count:27, kept_count:13`) | **MISMATCH** |
| `kala_priority_ranking_get` | `top_k=100` | `content.signal_count: 100` | `ranked_signals.length: 50` (`trim_report`: `original_count:100, kept_count:50`) | **MISMATCH** |
| `kala_windows_get` | `limit=500` | `content.activation_count: 500` | `activations.length: 5` (`trim_report`: `original_count:500, kept_count:5, reason:"floored to 5 (hard-cap)"`) | **MISMATCH** |
| `bodha_remedies_get` | `fields='all'` (needed to push payload over the 40KB trim threshold — the default `fields='compact'` call served all 27 untrimmed, see note below) | `content.prescription_count: 27` | `prescriptions.length: 13` (`trim_report`: `original_count:27, kept_count:13`) | **MISMATCH** |

All five reproduce exactly as claimed, live, against the canonical chart. Full JSON envelopes
captured in this session's tool-call transcript.

**Note on `bodha_remedies_get`'s default call:** with `fields='compact'` (default) and no
explicit `limit`, this session's default call served all 27 prescriptions untrimmed
(`prescription_count: 27`, `prescriptions.length: 27` — matched, no defect visible) because the
compact payload fit under the 40KB budget threshold and no trim fired. Passing `fields='all'`
(which inflates every prescription row with `prescription_detail_jsonb`/
`classical_sources_jsonb`/`estimated_cost_inr_range_jsonb`) pushed the payload over budget and
triggered the trim, exposing the defect. **This is itself diagnostic**: the bug is real and
structural (the count is computed before the trim point in the code, unconditionally) but only
OBSERVABLE on calls whose payload crosses the trim threshold — exactly the same "structurally
exposed, not always visibly triggered" character documented for the sibling `F-46` finding's
`applyAutoBudgetToEnvelope` census (see that lane's own DIAGNOSIS.md for the parallel).

## 2. Claim decomposition

- **F-45a:** `bodha_signals_get`'s `verdict_summary.served_count` (and by the same construction,
  `tier_distribution`/`top_subjects_by_frequency`, which are computed from the same pre-trim
  `rows` array) is computed BEFORE the generic budget trimmer runs, so it reflects the untrimmed
  set while the `signals` array it describes is trimmed after.
- **F-45b:** the same defect, independently confirmed, in `synth_chart_brief_get`'s
  `coverage_receipt` narrative sentence (a human-readable count embedded in prose, not even a
  structured field — arguably worse, since a caller cannot programmatically detect the staleness
  without parsing English text).
- **F-45c:** the same defect in `kala_priority_ranking_get`'s `signal_count`.
- **F-45d:** the same defect in `kala_windows_get`'s `activation_count`.
- **F-45e:** the same defect in `bodha_remedies_get`'s `prescription_count`.
- **F-45f (implicit, corpus's own framing):** the defect is "never re-derived/flagged stale
  afterward" — confirmed: none of the five narrative fields carry any pointer to the
  `trim_report` entry that WOULD let a caller reconcile the mismatch. The `trim_report` itself
  (added by the generic trimmer, a different, correct mechanism) DOES disclose the true original
  count in every one of these five cases (see the table's `trim_report` column) — so the true
  number is recoverable, but only by reading a structurally separate part of the envelope that
  the narrative field gives no hint exists.

## 3. Mechanism → file:line

### Confirmed site (per the brief): `bodha_signals_get`

`register_p1_aliases.ts:588-599`:
```ts
const rows = Array.isArray(inner['signals']) ? inner['signals'] as Record<string, unknown>[] : []
const tierCounts: Record<string, number> = {}
...
inner['verdict_summary'] = {
  served_count: rows.length,                    // :589 — computed from the UNTRIMMED rows
  tier_distribution: tierCounts,
  top_subjects_by_frequency: topSubjects,
  note: 'Small verdict over THIS response\'s own served rows (§N.6 (iii)) — not a re-query.',
}
finalizeMcpBudget(inner, { maxKb: 25, sections: [signalsSection()] })   // :599 — trims `signals` AFTER
```
The comment at `:592` ("Small verdict over THIS response's own served rows") is precisely the
claim that is now false the moment `finalizeMcpBudget` at `:599` trims `signals` down — the
verdict was built from the served-BEFORE-trim set, not the served-AFTER-trim set the caller
actually receives.

### Newly-traced site 1: `synth_chart_brief_get` — `platform-mcp/src/tools/register_p1_synthesis.ts`

`:836-843` (count computed):
```ts
const coverage_receipt = buildCoverageReceipt({
  topicsCovered: rows.length,
  domains,
  verdictCount: verdicts.length,          // :839 — untrimmed length
  loadBearingCount: Math.min(loadBearing.length, lbLimit),
  calibratedCount: Math.min(calibrated.length, calLimit),
  discoveryCount: discResult.rows.length,
})
```
`buildCoverageReceipt` (`:311-327`) formats this into the prose sentence: `` `${verdictCount}
domain verdicts, ...` ``. Meanwhile `verdict_summary` (`:864`) is built as
`trimmedVerdicts = verdicts.map(trimInsightRow)` (`:835`) — same length as `verdicts` at THIS
point (27 in the live repro), not yet trimmed.

The actual trim happens two calls later, at the return statement (`:871`):
```ts
return dualOutput(envelope(brief, 'synth_chart_brief_get', 'synthesis_maha_brief'))
```
`dualOutput` in THIS file (`:170-185`) calls `applyAutoBudgetToEnvelope(obj, toolName)` at `:177`
— the SAME weaker budget path documented in the F-46 lane's DIAGNOSIS.md §3 — which trims
`verdict_summary` (27→13 in the live repro) but never re-touches `coverage_receipt`, a plain
string already baked with "27" inside it at construction time. This is the clearest confirmation
in this whole finding of the "compute-narrative-count-before-generic-trim" defect class: the
staleness happens strictly between `:843` (count computed) and `:871`'s `dualOutput` call
(trim applied), inside the SAME function, with no code path connecting the two.

### Newly-traced site 2: `kala_priority_ranking_get` — the primitive is honest; the ALIAS wrapper
is where staleness is introduced

The primitive, `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:618-629`
(`callPriorityRankingCapability`, `marsys://tool/L3/call_priority_ranking`):
```ts
return {
  content: {
    ...
    ranked_signals: result.rows,
    signal_count:   result.rows.length,     // :626 — accurate AT THIS POINT, same array, same length
    ...
  },
}
```
`signal_count` here is genuinely accurate when this function returns — `ranked_signals` and
`signal_count` are both derived from the identical `result.rows` in the same statement block.
**The staleness is introduced one layer up**, at the MCP tool registration:
`platform-mcp/src/tools/register_p1_aliases.ts:840-862` (`regAlias(server,
'kala_priority_ranking_get', ..., 'marsys://tool/L3/call_priority_ranking', ...)`), whose generic
`regAlias` helper (`:351-384`) calls this file's OWN `dualOutput` (`:183-196`, note: a DIFFERENT,
STRONGER `dualOutput` than `register_p1_synthesis.ts`'s — this one already calls
`finalizeMcpBudget` directly, not the weak `applyAutoBudgetToEnvelope`):
```ts
function dualOutput(data: unknown, toolName = 'unknown_tool') {
  let finalData: unknown = data
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    const sections = autoDetectTrimmableSections(obj, toolName)
    finalData = finalizeMcpBudget(obj, { maxKb: 40, sections })   // trims `ranked_signals` HERE
  }
  ...
}
```
`finalizeMcpBudget` trims `content.ranked_signals` (confirmed live: 100→50) but has no mechanism
to know that `content.signal_count` is a narrative count describing that specific sibling array
and needs re-deriving — it only trims declared/auto-detected ARRAY sections; `signal_count` is a
scalar number, invisible to the trimmer entirely.

### Newly-traced site 3: `kala_windows_get` — same shape as site 2, different primitive

Primitive: `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts:360-378`:
```ts
return {
  content: {
    ...
    activations:       activations.rows,
    activation_count:  activations.rows.length,   // :365 — accurate at construction
    window_families,
    window_family_count: window_families.length,   // :371 — same risk, not exercised live this pass
    forward_windows,
    forward_window_count: forward_windows.length,  // :375 — same risk, not exercised live this pass
    predicates,
    predicate_count:   predicates.length,          // :377 — ALSO confirmed live: predicates
                                                     //  trimmed 500→10, predicate_count stayed 500
  },
}
```
Registered as `kala_windows_get` at `register_p1_aliases.ts:893-929` (bespoke handler, not
`regAlias`, but same `dualOutput(data, 'kala_windows_get')` call at `:928` using this file's
strong `dualOutput`). Live repro confirms BOTH `activation_count` (500 vs served 5, hard-cap
floor) AND `predicate_count` (500 vs served 10) go stale — the brief only named
`activation_count`, but `predicate_count` is the identical defect in the same response,
confirmed in the same live call (`trim_report` entry: `content.predicates: original_count 500,
kept_count 10`). `window_family_count`/`forward_window_count` were not trimmed in this particular
call (their arrays — 2 and 0 items — never crossed the trim threshold) but carry the identical
structural risk.

### Newly-traced site 4: `bodha_remedies_get` — `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`

`:584-592`:
```ts
return {
  content: {
    ...
    resonances:           includeAll ? orderedResRows : resonancesCompact,
    resonance_count:      resRows.length,       // :590 — same risk, not exercised live (9 rows, never trimmed)
    prescriptions:        includeAll ? preRows : prescriptionsCompact,
    prescription_count:   preRows.length,       // :592 — CONFIRMED live: 27 vs served 13 under fields='all'
    ...
  },
  is_error: false,
}
```
Registered via `regAlias(server, 'bodha_remedies_get', ..., 'marsys://tool/L2/query_remedies',
...)` at `register_p1_aliases.ts:1015-1025` — same strong `dualOutput`/`finalizeMcpBudget` path
as sites 2 and 3, same structural gap (trimmer shrinks `content.prescriptions`, has no way to
know `content.prescription_count` needs re-deriving).

## 4. Sibling census

Covered by `F-12/DIAGNOSIS.md` §4b for the class definition. Within THIS finding's own scope, two
additional stale-count risks were found DURING the trace above that the original finding did not
name (both in `kala_windows_get`'s own response, confirmed via the same live call already run for
the named `activation_count` claim):
- `predicate_count` (`query_temporal_activation.ts:377`) — CONFIRMED live stale (500 vs served
  10), not named in the original F-45 claim text. Same tool, same call, same defect.
- `window_family_count` / `forward_window_count` (`:371`, `:375`) — structurally identical risk,
  not exercised live this pass (their arrays were too small to trigger a trim on this particular
  call), flagged for SPEC-stage inclusion regardless.

## 5. BRANCH-EXISTS verdict — WRONG as "adopt the branch," but with ONE genuine structural
connection to S2's own file worth naming precisely

Per `F-12/DIAGNOSIS.md` §5: `ekv/a-09-sara-kernel`'s diff is `response_budget.ts` +
`registry_bridge.ts`, scoped to `assess_*` composition (F-56/F-111, `SaraKernel`/
`assembleSaraContent`/`buildAssessResponse`). None of this finding's five tools are `assess_*`
tools; none of their handler files are touched by the branch. **Adopting/extending the branch
does not fix this finding** — same negative verdict as F-12/F-36/F-37.

**The one real nuance for F-45, absent from F-12/F-36/F-37:** this finding's defect DOES live
partly inside S2's own generic trim machinery's BLIND SPOT, not just in call-site files. The root
cause is that `finalizeMcpBudget`/`applyResponseBudget` (both in S2's `response_budget.ts`) only
ever trim ARRAY-shaped sections; they have no concept of a scalar "count" field that describes an
array elsewhere in the same object and needs re-deriving when that array shrinks. A complete fix
plausibly has two parts:
1. **In each call-site file (S5's/S4's lease, per §6 below):** stop computing the narrative count
   before the trim point, or don't bake it into prose ahead of time.
2. **Possibly, in `response_budget.ts` itself (S2's HOT file):** teach `finalizeMcpBudget` an
   optional convention — e.g. a `TrimmableSection` may declare a `companionCountField` name that
   the trimmer updates to `kept_count` after trimming — so future call sites don't have to
   hand-roll this correctly every time. This would be a genuine, in-lease S2 contribution, but it
   is a NEW capability, not an "extension of the sara-kernel branch" — `SaraKernel`/
   `assembleSaraContent` do not touch `finalizeMcpBudget`'s trimming internals at all (confirmed:
   the branch's `response_budget.ts` diff is entirely additive new functions in a different
   region of the file, `:641-830` per the parallel finding F-46's own read of the same branch).

**Net verdict: BRANCH-EXISTS is wrong as stated** (there is nothing on `ekv/a-09-sara-kernel` to
extend for this finding). Item 2 above is a legitimate SPEC-stage option worth raising precisely
BECAUSE it sits inside S2's own hot file — but it is new work against `origin/main`'s
`response_budget.ts`, not a continuation of the sara-kernel branch's actual committed content.

## 6. Blast radius

- **File ownership vs S2's lease — mixed, mostly OUT of lease:**
  - `register_p1_aliases.ts` — per `LEASES.json`, explicitly **S5 MŪLA**'s (also carries an
    `ordered_handoff_owed` note: S1 goes first for a `dualOutput` toolName sweep, then re-leased
    to S5 — S2 has no claim here at all).
  - `register_p1_synthesis.ts` — explicitly **S5 MŪLA**'s (with an `ordered_handoff_pending` to
    S4 once S5's CL-03 lanes are VERIFIED).
  - `L3_kala/call_service_wrappers.ts`, `L3_kala/query_temporal_activation.ts` — **S5 MŪLA**'s
    ("platform (L3_kala/** query files) — ADDED post-Phase-0 for F-26").
  - `L2_bodha/query_remedies.ts` — **S5 MŪLA**'s ("platform (L2_bodha/** query files)").
  - `response_budget.ts` — the ONLY file among these six that IS S2's (HOT, exclusive) — relevant
    only for the optional item-2 fix in §5, not for the primary call-site fixes.
  **Five of six touched files are S5's, not S2's.** A `PAR-F45-NEEDS-LEASE` note is filed
  alongside this doc (see `NEEDS_LEASE.md` in this lane) naming all five out-of-lease files, with
  the one narrow exception (`response_budget.ts`) noted as S2's own optional contribution.
- **§N controls touched:** §N.6 item 4 directly (density signaling is data, not narration) — a
  narrative count is exactly this kind of signal, and going stale under trim is exactly the
  "generic budget trim... left alone" failure mode §N.6 already warns about, just for a scalar
  field instead of the array itself. `synth_chart_brief_get`'s `coverage_receipt` case is also
  §N.7 territory (narration re-deriving/embedding a number in prose rather than restating a
  currently-true value).
- **Other lanes sharing these files:** `register_p1_aliases.ts` and `register_p1_synthesis.ts`
  are also touched by several S5/S1/S4 findings per LEASES.json's own notes (S1's CL-11
  `dualOutput` sweep, S5's CL-03 param-parity work, S4's eventual narration ownership of
  `register_p1_synthesis.ts`) — any fix to these two files should be sequenced with those, not
  parallelized blindly.
- **A-09 sāra-kernel:** confirmed not touching any of the five call-site files; touches
  `response_budget.ts` in a different region (`:641-830`, additive `SaraKernel` code) than where
  a possible item-2 fix would land — no direct line-level conflict, but the same file, so any S2
  builder touching `response_budget.ts` for this finding should diff against the sara-kernel
  branch before committing to avoid a spurious merge conflict later if/when that branch lands.

## Evidence

Live JSON captured this session for: `bodha_signals_get(top_k=200)`,
`synth_chart_brief_get(depth='complete')`, `kala_priority_ranking_get(top_k=100)`,
`kala_windows_get(limit=500)`, `bodha_remedies_get()` (default, no defect visible — recorded for
completeness) and `bodha_remedies_get(fields='all')` (defect triggered) — all six full envelopes
in this session's tool-call transcript; exact `trim_report` entries quoted verbatim in the §1
table and §3 traces above.

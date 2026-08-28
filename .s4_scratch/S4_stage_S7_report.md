# S4 Pipeline Correctness & Door Parity — Stage S7 (EvidenceBundle assembly)

Investigator: S4 lane, stage S7 only (1 of 11 parallel lanes).
Code anchors: `platform/src/lib/pariprashna/pipeline/evidence_stage.ts`,
`platform/src/lib/bundle/bundle_hydrator.ts` (+ read-only cross-refs into
`completeness_wiring.ts`, `citation_resolver.ts`, `validation_stage.ts`,
`synthesis_stage.ts` to trace where S7's outputs actually get consumed).
Test subject: synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (nominal
only — S7 does not query the DB by chart_id; asset content is chart-scoped by
manifest entry, not by a chart_id parameter). Native chart
`482012f1-710e-4a25-994a-93821f5871aa` never touched.

Evidence artifacts (this worktree, `.s4_scratch/`, not committed):
- `.s4_scratch/s7_bundle_hydrator.perf.test.ts` (7 tests, real `hydrateBundle` +
  real `loadManifest` + real filesystem storage, no mocks) — PASS 7/7.
- `.s4_scratch/s7_evidence_stage_honesty.test.ts` (3 tests, real
  `runEvidenceStage`, mocks only its three I/O-boundary modules: registry
  lookup, cache/execute, QoS queue) — PASS 3/3.
- `.s4_scratch/perf_run_1.log`, `.s4_scratch/perf_run_2.log` — two independent
  N=20 timing runs.

Run commands (from `platform/`):
```
MARSYS_REPO_ROOT=<this worktree root> npx vitest run \
  .s4_scratch/s7_bundle_hydrator.perf.test.ts \
  .s4_scratch/s7_evidence_stage_honesty.test.ts --reporter=verbose
```
(`MARSYS_REPO_ROOT` pinned explicitly to this worktree — the app's own
`.env.local` points it at the shared checkout, which this lane must not read
from; the pin keeps all filesystem reads inside the worktree.)

## Architecture note (read this before the findings)

"EvidenceBundle" in the pipeline docstring (`evidence_stage.ts` header, "Ports:
`ToolBroker → EvidenceBundle`") names the WHOLE `EvidenceStageOutput` —
`{ bundle, validToolResults, toolEventLog, completenessReceipt, orientation }`
— not just `hydrateBundle`'s return value. The two halves do different jobs
and must not be conflated when reading the findings below:

- `bundle` (`hydrateBundle` output, `bundle_hydrator.ts`) = **reference/
  doctrine asset content** (CGM, MSR, UCN, CDLM, RM, …) read verbatim off
  storage by `asset_id`. This becomes the synthesis system prompt
  (`synthesis_stage.ts` `assembleSynthesisContext`, `rawBundleSystemContent`).
- `validToolResults` (the dispatch loop inside `evidence_stage.ts` itself) =
  **retrieval-pass-1 tool call outcomes** (positions, dashas, yogas, …). Traced
  forward: these do **not** get injected into the synthesis prompt text at
  all. They are used only for (a) the completeness receipt
  (`completeness_wiring.ts`), (b) citation-candidate-id prefetch
  (`citation_resolver.ts`), and (c) the post-hoc citation gate
  (`validation_stage.ts`, `JSON.stringify({ bundle, tool_results:
  validToolResults })`). The model gets the actual chart facts through a
  SEPARATE, live agentic tool-calling loop during synthesis
  (`synthesis_stage.ts` `useAgenticLoop` / `AGENTIC_PROVIDERS`), not through
  this pre-pass. This is intentional architecture, not a defect — but it means
  "does the bundle match S6 dispatch" has two different honest answers
  depending on which half of EvidenceBundle a reader means.

---

## 1. Correctness

**Sub-question A — is a genuinely empty tool result reported as EMPTY, never
dropped or faked?** YES, confirmed by test. `evidence_stage.ts`'s dispatch
loop (lines 85–101) keeps a `ToolBundle` with `results: []` in
`validToolResults` (the `r !== null` filter only strips `null`, and an empty
array is not `null`), and logs `toolEventLog` with `ok_count: 0, status:
'done'` — distinct from both "errored" and "never ran". Verified live:
`s7_evidence_stage_honesty.test.ts` test 1.

**Sub-question B — does the bundle equal exactly what S6 dispatch returned,
with no silent mutation/filtering at S7?** Mostly YES for the
`tool_results` half at its point of use in the citation gate
(`validation_stage.ts:45`: `JSON.stringify({ bundle, tool_results:
validToolResults })` — the raw arrays, unmodified). But NO for the `bundle`
(asset) half — see Finding 1.

### Finding 1 — `hydrateBundle` silently drops failed non-floor assets with no bundle-level disclosure (proposed: MEDIUM)
- **class**: correctness / honest-absence violation (CLAUDE.md §N.7 item 6 /
  §N.6 "never present [a reduced set] as if it were the full one")
- **lens(es)**: Correctness, Failure-honesty
- **pipeline stage**: S7 (EvidenceBundle assembly)
- **code anchor**: `platform/src/lib/bundle/bundle_hydrator.ts:104-131` (the
  three non-floor failure branches: unknown `asset_id` not in manifest;
  manifest entry with no `path`; `storage.readFile` throwing) each do
  `console.warn(...); continue` with **no corresponding field written to the
  returned `HydratedBundle`**.
- **expected**: When N assets are requested (`plan.asset_bundle`) and M < N
  actually load, the returned bundle should be able to answer "which assets
  were dropped and why" without grepping stderr — consistent with the
  disclosure discipline the codebase already applies elsewhere (completeness
  receipts, `judgment_flags`, `catalog_only_rows_present`, etc., per CLAUDE.md
  §N.6).
- **observed** (2026-08-28, this session): `HydratedBundle` has no
  `skipped_assets` / `failed_assets` / `requested_count` field. A caller
  reading only the returned object cannot distinguish "the plan asked for
  exactly what's in `assets`" from "the plan asked for more and some of it
  silently vanished." Demonstrated live:
  - `s7_bundle_hydrator.perf.test.ts` → *"unknown asset_id is dropped with
    ONLY a console.warn — no bundle-level disclosure field"*: requested
    `['CGM', 'DOES_NOT_EXIST_XYZ']`, got `bundle.assets = ['CGM']`,
    `Object.keys(bundle)` confirmed to carry none of `skipped_asset_ids`,
    `failed_assets`, `requested_count`.
  - Same gap reproduced for a manifest entry whose file 404s on disk
    (*"non-floor asset whose file is missing on disk degrades to honest
    partial bundle"*) and for an entry with an empty `path`
    (*"manifest entry with no path is treated the same as unknown-asset"*).
  - All three cases pass silently through to callers today: `route.ts` passes
    `evidence.bundle` straight into `assembleSynthesisContext` and
    `runValidationStage` with no gap check in between.
- **proposed fix class**: add a `skipped: { asset_id: string; reason:
  'unknown_id' | 'no_path' | 'load_error' }[]` field to `HydratedBundle`,
  populated at each of the three non-floor `continue` sites; thread it into
  the completeness/judgment-flags surface the same way
  `completeness_wiring.ts` already threads `web_dark_primitive_ids` (an
  established pattern in this exact stage's neighborhood — no new mechanism
  needed, just apply it one hop earlier).
- **rung achieved**: INTEGRATION (real `hydrateBundle`, real manifest shapes,
  real filesystem I/O errors — not mocked assertions about intent).

### Finding 2 — registry-lookup-miss silently escapes `toolEventLog`, unlike a dispatch throw (proposed: MEDIUM-LOW)
- **class**: correctness / internal inconsistency (two failure paths for
  "this authorized tool did not produce results" are handled with different
  observability, one of which is a true silent drop from a downstream
  accounting structure)
- **lens(es)**: Correctness, Failure-honesty
- **pipeline stage**: S7 (EvidenceBundle assembly), dispatch loop
- **code anchor**: `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:80-84`
  (the `if (!t) { em.activity(...status:'error'...); return null }` branch —
  no `toolEventLog.push(...)`) vs. lines 96-101 (the `catch` branch for a
  thrown dispatch, which DOES `toolEventLog.push({..., status: 'error', ...})`).
- **expected**: both "tool not found in the registry bridge" and "tool found
  but dispatch threw" are failures of the same class (`toolsAuthorized`
  claimed this tool would run; it didn't) and should be recorded identically
  in `toolEventLog`, the structure `buildWebCompletenessReceipt` reads
  (`completeness_wiring.ts:98`, `outcomeByTool.get(retrievalName)`).
- **observed** (2026-08-28, this session): a registry-lookup miss produces
  **zero** `toolEventLog` entries. Demonstrated live:
  `s7_evidence_stage_honesty.test.ts` test 3 — `getToolByName` stubbed to
  return `undefined` for an authorized tool name; `out.toolEventLog` is empty
  (`toHaveLength(0)`), while the equivalent dispatch-throw test (test 2)
  produces exactly one `status:'error'` row. Traced downstream:
  `completeness_wiring.ts:120-129`'s `if (!outcome)` branch treats the
  resulting gap as `empty_reason: 'route_not_invoked'` — the SAME label used
  for "this tool was correctly never authorized for this query" — rather than
  a distinct `route_error`/`tool_unregistered` reason. The live
  `activity.upsert` SSE event DOES say `status:'error'` for this case (so the
  streaming client sees the failure), but the server-side completeness
  receipt cannot see it — an inconsistency between what streams to the client
  and what gets recorded for the turn's own honesty accounting.
- **proposed fix class**: push a `toolEventLog` entry
  (`{ name: toolName, status: 'error', ms: 0, ok_count: 0, err_count: 1 }`) in
  the `if (!t)` branch too, matching the catch branch's shape; optionally
  give `completeness_wiring.ts` a distinct `empty_reason` for
  "authorized but registry-unresolvable" vs. genuine non-authorization, since
  the two indicate very different bugs (a manifest/registry drift vs. a
  planner scoping choice).
- **rung achieved**: INTEGRATION (real `runEvidenceStage`, mocked only at the
  three external I/O seams).

---

## 2. Optimality

Instrumented `hydrateBundle` directly (no mocks; real `loadManifest()` +
real filesystem reads under this worktree), N=20 per scenario, two
independent runs to check stability.

**Scenario A — realistic 5-asset interpretive bundle** (`CGM` floor +
`MSR`+`UCN`+`CDLM`+`RM`, the `025_HOLISTIC_SYNTHESIS` tier a real
`deep_dive`/interpretive plan pulls):

| run | min ms | p50 ms | p95 ms | max ms |
|---|---|---|---|---|
| 1 | 5.43 | 6.06 | 7.61 | 7.61 |
| 2 | 4.51 | 4.90 | 5.85 | 5.87 |

Input size read from disk: CGM 79,040 B · MSR 1,200,174 B · UCN 198,254 B ·
CDLM 88,743 B · RM 47,092 B = **1,613,303 bytes total** (`bundle.total_bytes`
matches exactly — no compression/transform happens in `hydrateBundle`, it is
a pass-through read + hash). `bundle.total_tokens` (sum of
`Math.ceil(byte_count/4)` fallback, since these entries carry no
`token_count` in the manifest) = 403,327.

**Scenario B — floor-only (empty `asset_bundle`, CGM enforced)**:

| run | p50 ms | p95 ms |
|---|---|---|
| 1 | 0.34 | 0.42 |
| 2 | 0.25 | 0.30 |

**Assessment**: hydration latency is dominated by disk I/O for ~1.6 MB across
5 files and completes in single-digit milliseconds (p95 ≤ 7.6ms for the
5-asset case; sub-millisecond for the floor-only case). Relative to a
synthesis-stream turn that runs for seconds to tens of seconds, this stage's
overhead is negligible — no optimality defect found. The hashing work
(`crypto.createHash('sha256')` per asset, plus one more over the sorted
canonical_id list for `bundle_hash`) is the only CPU-bound part and does not
show up as a measurable cost at this asset count/size. No N+1 I/O pattern:
each asset is read exactly once (`storage.readFile` called once per
`AssetSpec`), sequentially in a `for` loop rather than `Promise.all` — worth
noting as a *potential* (not measured-material at N=5) latency lever: at a
much larger `asset_bundle` (e.g. discovery/holistic query classes pulling
8-10 large `025_` docs) the sequential `for...of` loop in
`bundle_hydrator.ts:101-152` would serialize I/O that `Promise.all` could
parallelize. Not filed as a numbered finding — no evidence at today's typical
bundle sizes (5 assets, low-single-digit ms) that this matters; flagged here
only as a should-recheck-if-bundle-sizes-grow note, not a proposed defect.

---

## 3. Failure-honesty

Forced an empty tool result upstream of the dispatch loop (mocked
`executeWithCache` to resolve a `ToolBundle` with `results: []`, i.e. exactly
what a real tool call that legitimately found zero rows returns) and
confirmed the outcome via the real `runEvidenceStage`:

- `validToolResults` contains the `ToolBundle` with `results: []` intact —
  not omitted, not padded with placeholder content.
- `toolEventLog` records `{ status: 'done', ok_count: 0, err_count: 0 }` —
  distinguishable both from a real error (`status: 'error', err_count: 1`,
  also forced and verified in the same test file) and from a tool that never
  ran at all (registry-miss case, Finding 2).
- Downstream, `completeness_wiring.ts:133-137` turns `ok_count > 0 ? served :
  empty` — an `ok_count: 0` row is correctly classified `status: 'empty',
  empty_reason: 'route_empty'`, distinct from `route_error` and from
  `route_not_invoked`. Verified by code inspection (not re-executed as a
  standalone test in this lane — `completeness_wiring.ts` is outside the S7
  anchor files; the toolEventLog shape it consumes was the thing under test
  here and was confirmed correct for the genuine-empty case).

Evidence: `.s4_scratch/s7_evidence_stage_honesty.test.ts`, test 1
("dispatches successfully with ZERO rows is reported as an HONEST EMPTY
ToolBundle"). PASS.

No failure-honesty defect found for the "forced empty result" scenario
specifically — S7's dispatch loop reports it correctly. The failure-honesty
defect that *does* exist (Finding 2) is one step upstream of "empty result":
a tool that never got a chance to return anything (registry miss) rather
than one that returned zero rows.

---

## 4. Demonstrated-can-fail

Six adversarial inputs fed directly to the real `hydrateBundle` (no mocks —
real manifest, real filesystem, deliberately corrupted `ManifestData`/`plan`
shapes), each proving a specific, previously-undocumented failure mode:

| # | Input | Result | Honest? |
|---|---|---|---|
| 1 | `asset_bundle` names an `asset_id` absent from the manifest | Silently skipped, `console.warn` only | Partially — see Finding 1 |
| 2 | Floor asset (`CGM`) absent from manifest entirely | `throw`: `"bundle_hydrator: floor asset 'CGM' not found in manifest"` | YES — loud, fatal, correct |
| 3 | Floor asset present in manifest but its file 404s on disk | `throw`: `"bundle_hydrator: failed to load floor asset 'CGM' from ...: ENOENT..."` | YES — loud, fatal, correct |
| 4 | Non-floor asset (`MSR`) present in manifest but file 404s on disk | Silently skipped, `console.warn` only, turn continues with a smaller bundle | Partially — see Finding 1 |
| 5 | Manifest entry present but `path: ''` (empty string, falsy) | Silently skipped, `console.warn` only | Partially — see Finding 1 |
| 6 | Empty `asset_bundle` (`[]`) | Floor (`CGM`) auto-injected, `floor_enforced: true` | YES — documented, intended behavior |

The floor/non-floor asymmetry (#2/#3 throw loudly; #1/#4/#5 degrade silently)
is itself intentional per the module's own header comment ("A floor asset
that fails to load throws (fatal)") and is *correct design* for keeping a
turn alive on a non-critical asset miss — the defect is not that non-floor
failures are non-fatal, it's that they leave no trace in the returned value
(Finding 1).

Evidence: `.s4_scratch/s7_bundle_hydrator.perf.test.ts`, tests 3-7 (all
titled `DEMONSTRATED-CAN-FAIL: ...`). 5/5 PASS, each assertion proving the
described behavior actually occurs (not merely that it doesn't throw an
*unexpected* error).

**Rung achieved for this whole report: INTEGRATION.** All ten tests across
the two files call the real production functions
(`hydrateBundle`, `runEvidenceStage`) with real manifest data, real
filesystem I/O, and — for the dispatch-honesty file — mocks confined to the
three named external I/O boundaries (registry bridge, cache/execute, QoS
queue), never mocking the code under test itself.

# S4 Pipeline Correctness & Door Parity — Stage S10: SemanticReadingParts

Investigation date: 2026-08-28
Test subject: synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` ONLY (native's real chart never touched).
Evidence rung achieved: **INTEGRATION** (real vitest runs against real source modules — `ReadingPartsAssembler`, `block_classifier.ts`, the real client `s1LiveAdapter` and `threadReducer` — no mocks of the code under test).

Code anchors:
- `platform/src/lib/pariprashna/pipeline/reading_parts.ts` (`ReadingPartsAssembler`, `commitBlock()` lines 186-364)
- `platform/src/lib/pariprashna/semantics/block_classifier.ts` (`classifyBlockKind`, `classifyRole`, `classifyCommittedBlock`)
- `platform/src/lib/pariprashna/semantics/flag.ts` (`isSemanticBlocksEnabled`, flag `PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED`)
- `platform/src/lib/config/feature_flags.ts:558` (`PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED: false` — production default)
- `platform/src/components/pariprashna/state/s1LiveAdapter.ts:194-219` (`block.commit` → `kind: ev.kind ?? 'paragraph'`)
- `platform/src/components/pariprashna/state/reducer.ts:254-266` (`block.commit` case, `CommittedBlock` assembly)
- `platform/src/components/pariprashna/answer/FrozenBlock.tsx` (kind→component switch)

---

## 1. Correctness

### 1.1 Existing test suite — real results

Ran the three named pre-existing files plus two directly-adjacent files that this stage's wiring depends on:

```
npx vitest run \
  src/lib/pariprashna/pipeline/reading_parts_commit_lag.test.ts \
  src/lib/pariprashna/pipeline/__tests__/reading_parts_semantic_blocks.test.ts \
  src/lib/pariprashna/pipeline/__tests__/reading_parts_full_coverage.test.ts

 Test Files  3 passed (3)
      Tests  16 passed (16)
   Duration  210ms
```

Adjacent files (same lane, directly relevant to whether producers exist/are honest — not required by the brief but load-bearing for the GAP-6 question, so run for completeness):

```
npx vitest run \
  src/components/pariprashna/state/__tests__/s1LiveAdapter_semantic_blocks.test.ts \
  src/lib/pariprashna/semantics/__tests__/block_classifier.test.ts

 Test Files  2 passed (2)
      Tests  24 passed (24)
   Duration  129ms
```

All 40 tests across the 5 files pass. No flake, no skip, no `.todo`.

### 1.2 Block-kind coverage — is every claimed kind a real producer, or a stub?

`block_classifier.ts` declares `WireBlockKind = 'paragraph' | 'heading' | 'table' | 'verse' | 'gap_ribbon'`. Traced each:

| Kind | Detector | Real logic? | Test coverage |
|---|---|---|---|
| `table` | `parseMarkdownTable` — GFM header+separator+rows parse | Yes, real regex/parse, not a stub | `describe('classifyBlockKind — table')`, positive + negative |
| `verse` | `isBlockquote` / `stripBlockquote` — every non-empty line starts with `>` | Yes | `describe('classifyBlockKind — verse')`, positive + negative |
| `gap_ribbon` | `GAP_RIBBON_PATTERN = /\bthe chart is silent\b/i` | Yes (narrow, deliberately phrase-anchored) | `describe('classifyBlockKind — gap_ribbon')` |
| `heading` | `HEADING_LINE` ATX (`#`–`######`) regex, whole-block-is-one-line | Yes | `describe('classifyBlockKind — heading')` |
| `paragraph` (default) + `role` (`verdict`/`elaboration`/`caveat`) | `classifyRole` — structural first-in-pass + `CAVEAT_LEAD_IN` lexical | Yes | `describe('classifyRole')`, `describe('classifyCommittedBlock')` |
| embedded table spans (DD-22) | `detectTableSpans` — byte-exact offset reconstruction | Yes | `describe('detectTableSpans — byte-exact offset reconstruction')` |

**Verdict: all 5 kinds + the role sub-classifier + the DD-22 embedded-table-span metadata are genuinely implemented with real, narrowly-scoped detector logic, not stubs.** `prediction_card` and `seam` (the other two kinds `FrozenBlock.tsx` switches on) are NOT produced by this classifier at all — they are separate first-class wire events (`persistence_stage.ts` prediction_card emission, `reducer.ts` pass-seam handling) outside `SemanticReadingParts`'s scope; not a finding against S10.

### 1.3 The real correctness finding: producers exist but are dark by default, with a silent fallback

`commitBlock()` (`reading_parts.ts:338`) only calls `classifyCommittedBlock` when `this.semanticBlocksEnabled` is true. That flag is wired from `isSemanticBlocksEnabled()`, which reads `PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED`, which defaults to **`false`** in `feature_flags.ts:558` — i.e. in production, right now, none of the 5 real detectors above ever run. `commitBlock()`'s else-branch emits `em.blockCommit({ block_id, text })` — no `kind` field at all.

Client-side, `s1LiveAdapter.ts:211` reads `kind: ev.kind ?? 'paragraph'`. `reducer.ts:259` copies that straight into the committed block with no additional field marking whether classification ran. `FrozenBlock.tsx` then renders every such block through `ParagraphBlock`, indistinguishable from genuine prose.

This is **not a case of "GAP-6's unbuilt producers don't exist"** — they do exist, are well-tested in isolation, and are proven wired correctly when the flag is on (`reading_parts_semantic_blocks.test.ts`, `s1LiveAdapter_semantic_blocks.test.ts`). It IS a case of **"the honest producers are shipped dark, and the dark path is a bare `?? 'paragraph'` fallback with zero marker anywhere in the wire event, the reducer state, or the rendered DOM that classification was skipped."** See §3/§4 below — this is the GAP-6 finding, demonstrated end-to-end.

---

## 2. Optimality — assembler latency

Instrumented `ReadingPartsAssembler` directly (not mocked) with a realistic 5-block turn (verdict paragraph, a classical blockquote verse, a 2-row dasha table, an honest-gap sentence, a caveat paragraph — the full mix the classifier claims to support), N=20 runs per condition after a 3-run JIT warmup, both with the flag ON and OFF:

```
[S10-LATENCY] {
  "semanticBlocksON":  { "p50_ms": 0.0186, "p95_ms": 0.0398, "min_ms": 0.0170, "max_ms": 0.0398 },
  "semanticBlocksOFF": { "p50_ms": 0.0122, "p95_ms": 0.0219, "min_ms": 0.0119, "max_ms": 0.0219 }
}
```

(sub-millisecond throughout; see `.s4_scratch/s10_latency_and_gap.test.ts`, test "measures commitBlock assembly latency for a realistic 5-block turn, flag ON vs OFF" — 3/3 passed)

**Verdict: no optimality concern.** The classifier is pure in-memory string/regex work over an already-committed block's text (no I/O, no DB, no LLM call) — assembling a full 5-block turn costs under 40 microseconds even with classification on, roughly 1.5x the flag-OFF cost. This is not a bottleneck anywhere in the pipeline; the classifier's own docstring correctly frames it as "runs exactly once, on a finished string," which the measurement confirms is cheap.

---

## 3. Failure-honesty — the core GAP-6 question

Traced the flag-OFF fallback path precisely, at three points:

1. **Server (`reading_parts.ts:353-355`)**: `else { this.em.blockCommit({ block_id: this.currentBlock.id, text: this.currentBlock.text }) }` — no `kind`, no `role`, no flag, no marker of any kind that a classification pass was skipped. Comment at `reading_parts.ts:112-114` confirms this is deliberate: "the event carries exactly `{ block_id, text }`, same as before this lane."
2. **Client adapter (`s1LiveAdapter.ts:194-219`)**: `kind: ev.kind ?? 'paragraph'`. Comment explicitly says "the `?? 'paragraph'` fallback is exactly the old hardcoded behavior." No field is set to signal "unclassified" vs. "classified-and-genuinely-paragraph" — the two are bitwise identical on the wire.
3. **Reducer (`reducer.ts:254-266`)**: `committed.kind = action.kind` (already resolved to `'paragraph'`), `gapText: action.gapText` (`undefined`). No `classificationSkipped` or equivalent field exists anywhere in `CommittedBlock`'s type (`state/types.ts`).
4. **Renderer (`FrozenBlock.tsx:16-27`)**: `case 'paragraph': ... return <ParagraphBlock ...>` — a verse citation with intact `>` blockquote markers, or a sentence containing the honest-gap phrase "the chart is silent," both render through the generic paragraph component with no visual or structural distinction from a `kind: 'verse'` or `kind: 'gap_ribbon'` block.

**Verdict: SILENT DOWNGRADE CONFIRMED, no honest marker anywhere on the flag-OFF path.** This matches the GAP-6 pattern precisely: the block reaches the reader/caller as generic prose with zero indication that the richer classification (verse styling, gap-ribbon affordance, heading hierarchy, table structure, verdict/elaboration/caveat role) never ran. Note the important nuance: this is not data loss — the raw text (including `>` markers and the "chart is silent" sentence) is fully preserved and visible to the reader — it is a *structural fidelity* loss with no accompanying honesty signal, closer to "styling degrades silently" than "information disappears," but it is still exactly the defect class §N.7/§N.8 name: a status (here, "was this block classified") with no real detector/marker behind the case where it is false.

---

## 4. Demonstrated-can-fail — real evidence, both directions

Wrote `.s4_scratch/s10_latency_and_gap.test.ts` (scratch, not committed to the permanent suite) exercising the REAL server assembler, REAL client adapter (`makeS1LiveAdapter`), and REAL reducer (`threadReducer`) together — no re-implementation of any of the three.

**Test 1 — verse block, flag OFF, traced end-to-end:**
```
a.commitBlock() with '> yasya grahasya sambandhāt phalaṃ tasya nirūpayet\n> — BPHS 12.4'
  → server event keys: ['block_id', 'text']   (no 'kind' key at all — PASS)
  → client wire.kind === 'paragraph'          (silently downgraded — PASS)
  → client wire.role === undefined            (PASS)
  → reducer committed.kind === 'paragraph'    (PASS)
  → committed.html contains '>' (raw quote markers, unstripped)   (PASS)
  → committed.classificationSkipped === undefined (no such field exists) (PASS)
  → committed.gapText === undefined            (PASS)
```

**Test 2 — honest-gap sentence, flag OFF, traced end-to-end:**
```
a.commitBlock() with 'Between these two windows, the chart is silent — ...'
  → server event keys: ['block_id', 'text']    (PASS)
  → client wire.kind === 'paragraph'            (PASS — NOT gap_ribbon)
  → reducer committed.kind === 'paragraph'      (PASS)
  → committed.gapText === undefined             (PASS)
```

Result: **3/3 tests pass** (`npx vitest run .s4_scratch/s10_latency_and_gap.test.ts` → `Test Files 1 passed (1)`, `Tests 3 passed (3)`), proving both halves of the claim:
- the flag-ON path genuinely classifies (pre-existing `reading_parts_semantic_blocks.test.ts` + `block_classifier.test.ts`, 24 tests, all real detectors);
- the flag-OFF path — the production default — genuinely, silently, and by explicit design falls back to plain paragraph with no honest marker at any of the four traced points.

---

## 5. Findings, shaped for EDIR_V3

### Finding S10-1 — SemanticReadingParts classification is dark by default with a silent, unmarked fallback (proposed GAP-6 instance)

- **Class:** failure-honesty / silent downgrade (§N.7/§N.8 defect class — a status with no detector behind its false case, generalized to a whole classification pass)
- **Proposed severity:** S2 (proposed) — no data loss, but a structural-fidelity claim ("this reading uses a verse/gap-ribbon/heading affordance") silently degrades to "plain paragraph" with zero signal, indistinguishable from a genuinely-plain block. Not S1 because the underlying text/facts are fully preserved and nothing is fabricated.
- **Lens(es):** failure-honesty, correctness (secondary — the classifier itself is correct; the gap is in the flag-OFF path around it)
- **Pipeline stage:** S10 — SemanticReadingParts
- **Expected:** either (a) the classifier runs and the reader sees real verse/gap-ribbon/heading/table/role structure, or (b) if classification is deliberately not run (flag OFF), some marker — a flag, a telemetry counter, an internal-only field — records that this specific commit skipped classification, so a caller auditing "did every eligible block get classified" has something to check against.
- **Observed (2026-08-28, via INTEGRATION vitest evidence):** `PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED` defaults to `false` in production (`feature_flags.ts:558`). With it off, `ReadingPartsAssembler.commitBlock()` emits `{block_id, text}` only (`reading_parts.ts:353-355`); `s1LiveAdapter.ts:211`'s `ev.kind ?? 'paragraph'` and `reducer.ts:259`'s pass-through mean a classical verse citation or an honest-gap sentence renders identically to ordinary prose, with no field anywhere (wire event, reducer `CommittedBlock`, or DOM) indicating classification was skipped. Demonstrated directly against the real modules in `.s4_scratch/s10_latency_and_gap.test.ts` (3/3 passing).
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/reading_parts.ts:353-355`; `platform/src/components/pariprashna/state/s1LiveAdapter.ts:211`; `platform/src/components/pariprashna/state/reducer.ts:259`; flag default `platform/src/lib/config/feature_flags.ts:558`.
- **Proposed fix class:** additive/observability — add a per-turn or per-commit counter/telemetry flag (e.g. `em.flag({code: 'semantic_classification_skipped', ...})` once per turn, not per block, to avoid noise) recording that a turn was served without classification, OR flip `PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED` on now that the client renderers (`ParagraphBlock`, `VerseBlock`, `GapRibbonBlock`, `TableBlock`) all exist and are tested. This is a disposition question for the native/EDIR owner, not a code change made by this investigation.
- **Rung achieved:** INTEGRATION (real assembler + real client adapter + real reducer, chained, synthetic chart context, no mocks of code under test).
- **Provenance:** GAP-6 (reproduced/confirmed, not merely cited).

### Finding S10-2 — No optimality concern (informational, not a defect)

- **Class:** optimality — clean result
- **Proposed severity:** n/a (not a defect)
- **Lens(es):** optimality
- **Pipeline stage:** S10
- **Observed:** `ReadingPartsAssembler` assembly of a realistic 5-block turn costs p50 ≈ 0.012–0.019ms, p95 ≈ 0.022–0.040ms (flag OFF/ON respectively), N=20, warmed. Pure in-memory regex/string work, no I/O.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/reading_parts.ts` (`commitBlock`), `platform/src/lib/pariprashna/semantics/block_classifier.ts`.
- **Rung achieved:** INTEGRATION (direct instrumentation, N=20).
- Recorded here for completeness of the 4-dimension assessment; not itself an EDIR candidate.

---

## Appendix — files touched this investigation

- Created (scratch only, per instructions): `platform/.s4_scratch/s10_latency_and_gap.test.ts` — latency harness + GAP-6 demonstration test, run against real source, not committed to the permanent suite.
- No production source file was modified.

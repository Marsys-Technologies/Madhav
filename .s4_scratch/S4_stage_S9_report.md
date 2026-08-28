# S4 — Stage S9 (Grounding/Safety Validation) — Assurance Report

Stream: S4 (Pipeline Correctness & Door Parity). Stage: S9 only.
Date: 2026-08-28. Subject chart used for ALL live probes: synthetic
`1c826d5a-41cb-4450-b4dc-59d440e5f75a` ("Abhinandan Mohanty"). The native's
real chart (`482012f1-…`) was never touched.

Evidence rung achieved: **INTEGRATION** (real vitest runs against the actual
exported functions, `platform/.s4_scratch/*.scratch.test.ts`) plus one **LIVE**
data point (a real `mcp__marsys-jis-direct__prashna_ask` call against the
synthetic chart, job_id `e6870d9f-547b-436a-8f30-216dd7e7697d`, trace_id
`498e3184-ae37-4a3a-b7fc-b5e645690008`).

---

## 0. Headline: E-005 re-measurement (citation density)

**Method.** Called the live `prashna_ask` MCP tool against the synthetic chart
with a broad, multi-domain query ("career, wealth, relationships … major
yogas, dasha timing, cross-domain contradictions"), designed to force a
many-claim, `holistic`-class reading (the highest per-class citation floor in
`citation_check.ts`'s own — as will be shown, dead — threshold table). Got
back a real, complete reading (not withheld, not partial;
`completeness.status: "complete"`). Ran the REAL production citation-counting
functions (`countSignalCitations`, `totalSignalCitations`, `validateCitations`
from `citation_check.ts`; `extractCitations` from `extract_citations.ts`)
against the verbatim reading text. Full script:
`platform/.s4_scratch/e005_density_measure.scratch.test.ts` (3/3 green).

**Result — the actual number, not an assumption:**

- **7 GFM footnotes** (`[^1]`–`[^7]`), structurally well-formed (7 inline
  refs, 7 matching definitions) — **not 2**, the E-005 seed baseline's
  observed count on a different reading. Absolute footnote count varies by
  reading/query-class; this alone does not refute E-005's *pattern*, it
  updates the *specific number* with a fresh, reproducible measurement.
- **Hand-counted distinct factual/computed claims in this reading: 14**
  (planetary placements, dignities, yogas, dasha windows/dates, house-lordship
  facts — full enumeration in the test file). **7 of 14 carry a footnote, 7 do
  not** → **density = 50%** by this claim-count method. Materially
  uncited "hard" claims include: the network-centrality "House 8/House 2 hub
  node" claim, the 11th-house Sun+combust-Mercury placement, the Ketu 7th /
  Rahu 1st placement, the 12th-house Mars+Venus stellium, the Saturn MD/Rahu
  AD date window (Dec 2023–Oct 2026), and the Oct 10 2026 dasha transition
  date. `judgment_flags` on this turn also carries `synthesis_evidence_truncated`,
  which plausibly explains part of the gap.
- **A second, independent and more severe finding**: the footnote
  *definitions* in this real reading are raw evidence-row **UUIDs**
  (`[^1]: c48b591f-4827-4f17-8104-6cd8bf1e254a`, …), not the
  `SIG.MSR.NNN` signal-id format the shared system prompt explicitly mandates
  (`src/lib/synthesis/prompts/synthesis_prompt_v2.ts:36-46`: "Use `[^N]`
  inline footnote syntax… Each `[^N]` must have a corresponding `[^N]:
  SIG.MSR.NNN` definition"). Result: `countSignalCitations()` on this real
  reading returns **0**, and `totalSignalCitations()` returns **0** —
  production's actual citation counter is structurally blind to every one of
  the 7 real footnotes this reading contains. `validateCitations()` (the
  function `runValidationStage`/`streaming_citation_validator.ts` wrap) reads
  `layer1_count: 0` and — because `holistic` is not in
  `PRESCRIPTIVE_CLASSES` — returns a silent **`gate_result: 'PASS'`**, reason
  `"informational query (holistic); citations not required"`. So a
  many-claim reading with real, present, honestly-numbered footnotes and a
  measured 50%-of-claims citation rate reads, to the one gate that exists,
  as indistinguishable from a reading with **zero** grounding attempted.

**Verdict: still thin, and worse than "thin" in one respect.** The absolute
footnote count moved (2 → 7 across two different measurements/readings), so
E-005's exact number should be updated on re-file, not preserved verbatim —
but the underlying claim (assumed-adequate density was never actually
measured, and turns out not to be adequate) is reconfirmed, and a second,
independent defect was found underneath it: the counter that exists cannot
see this door's real citations at all. (This UUID-vs-SIG.MSR mismatch is
plausibly explained, not excused, by finding §2 below: the MCP door's
evidence-gathering floor never returns SIG.MSR-shaped ids for this query
shape, so the model had nothing in the prescribed format to cite and
improvised with the row ids it actually saw.)

---

## 1. Correctness — do all 5 listed call points fire on the live path?

Traced each of the 5 call points named in the brief. All 5 are real,
non-dead code with genuine callers (confirmed by grep for callers outside
`__tests__`):

| # | Call point | Wired into | Fires on default-config live path? |
|---|---|---|---|
| 1 | `synthesis_stage.ts:827` `lintReaderProse(event.text)` | The `/api/pariprashna` route's per-delta streaming loop (flag-OFF branch) | **Yes** — `PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED` defaults `false` (`feature_flags.ts:566`), so this branch is the one that runs today. |
| 2 | `reading_parts.ts:205` `lintReaderProse(this.currentBlock.text)` | `ReadingPartsAssembler.commitBlock()`, called from `synthesis_stage.ts` on every real block commit (4 call sites) | **Yes**, unconditionally — not gated by any flag. |
| 3 | `reading_parts.ts:463` `lintReaderProse(value)` (via `scrubValue`/`scrubToolArgs`) | `buildCanonicalParts` (line 572), the real tool-call-args persistence path | **Yes**, unconditionally. |
| 4 | `citations/rewriter.ts:217` `lintReaderProse(raw, resolver)` (`flushHold`) | `CitationStreamRewriter`, constructed in `synthesis_stage.ts` only when `citationRewriteEnabled` (`isFirstPaintCitationsEnabled()`) | **Only when the flag is ON** — default OFF in production config today. When ON, this path replaces call point 1 for the SAME deltas (design intent, stated in the file's own comment: "Flag-OFF path below is byte-for-byte the pre-existing per-delta `lintReaderProse` call"), so at least one of {1, 4} always lints every delta regardless of flag state — verified this is a real either/or, not a gap. |
| 5 | `citations/rewriter.ts:330` `lintReaderProse(text, resolver)` (`lintEmit`) | Same `CitationStreamRewriter`, its single lint/emit exit | Same flag-gating as #4. |
| — | `reader_text/review.ts:40` `lintReaderProse(entry.reader_text)` | `reviewAll`/`reviewEntry`, called ONLY from `generate_and_freeze.ts` | **No — this is an OFFLINE, build-time-only call.** `generate_and_freeze.ts`'s own header: run manually via `npx tsx --conditions=react-server … generate_and_freeze.ts`, writes a frozen JSON artifact once. It is real, exercised code (not dead), but it is **not on any live per-turn request path** — a turn never invokes it. Worth a nuance note for anyone citing "5 live call points": one of the five named anchors is a curation-time gate, not a runtime one. |

**MCP door (`/api/mcp/prashna_ask` → `prashna_ask_synthesis.ts`): ZERO of
these call points fire.** Grepped both files for
`lintReaderProse|validateCitations|register_leak|citation_gate|runValidationStage`
— no matches in either. This **independently reproduces EDIR E-048** ("The
MCP door runs NO stage-S9 grounding validation at all: neither the citation
gate nor the register-leak lint touches its reading") on current code, with a
concrete confirming trace: `synthesis_stage.ts:827`+`reading_parts.ts`'s
`commitBlock`/`scrubToolArgs` are the ONLY things that ever run
`lintReaderProse`, and `synthesis_stage.ts`/`reading_parts.ts` are never
imported by the MCP route. The exact reading captured for §0 above —
containing real evidence-row UUIDs, in prose, that would be a hard leak
pattern (`fact_id_namespace`-shaped or otherwise) on the web door — went
completely unlinted before being returned to the caller. This is the sharpest
door-parity finding in this lane: one of the two production doors has no S9
stage at all, not a weaker version of it.

**E-050 independently reproduced too**: `MIN_CITATIONS_BY_CLASS`,
`hasMinimumCitations`, `citationThresholdForClass` (`citation_check.ts`) have
**zero callers anywhere in `src` outside their own defining file and its unit
test** (grep-confirmed). `validateCitations()` never calls
`hasMinimumCitations`; its own gate logic is only "≥1 verified citation ⇒
PASS, 0 verified but ≥1 unverified ⇒ WARN, 0 total + prescriptive class ⇒
ERROR, 0 total + non-prescriptive ⇒ PASS." The per-class density table is
inert.

---

## 2. Optimality — false-negative rate, latency

**No comprehensive seeded leak/citation corpus exists** for a formal
false-negative-rate measurement (`corpus/dimensions/register_leakage.ts`
scores *live-turn fire rate*, not a seeded ground-truth catch rate; the only
seeded fixtures are `citations/__tests__/register_leak_lint.test.ts`'s
list-collapse regression cases, which are all designed to be caught, not an
adversarial evasion sweep). Built one (`.s4_scratch/s9_leak_evasion_probe.scratch.test.ts`,
5/5 green) to get a real number instead of asserting "no corpus exists" and
stopping there:

```
✓ EVADES: lowercase register acronym ("msr") is NOT redacted — near-miss/telemetry-only, text unchanged
✓ EVADES: mixed-case ("Msr") is NOT redacted — not even in the near-miss set
✓ EVADES: uppercase asset-id prefix ("BO_laksana") is NOT matched — pattern requires lowercase bo_/ga_/…
✓ EVADES: spaced-out acronym ("M S R") is NOT matched
✓ CAUGHT (control): standard "MSR" IS redacted
```

**This independently reproduces EDIR E-039** ("Register-leak lint: measured
coverage boundary — four evasion classes pass clean") on current code, with
these exact four classes confirmed live. **The PPR-04 "100% seeded-id catch"
claim (test plan §4.2/§7.5) does not hold against an adversarial sweep** —
it appears to describe the narrower, already-passing list-collapse
regression suite, not a true false-negative-rate corpus. No comprehensive
FN-rate corpus exists to produce a single pass-rate percentage against; the
honest finding is "at least 4 known evasion classes pass clean, 0 known
adversarial corpus measures the rest."

**Latency** (`.s4_scratch/s9_register_leak_callpoints.scratch.test.ts`, N=20
per case, `validateCitationsForStream` — the function `runValidationStage`
wraps at `validation_stage.ts:47`):

| Payload | p50 | p95 |
|---|---|---|
| Small (~250 bytes text, minimal context JSON) | 0.002 ms | 0.09–0.11 ms |
| Realistic (~90 KB assembled context JSON, 40 synthetic tool-result rows) | 0.022 ms | 0.07 ms |

Added latency is **negligible** (sub-millisecond) even at realistic context
sizes — the citation gate is not a meaningful contributor to turn latency
(consistent with EDIR E-006's finding that >95% of wall time sits outside
tool dispatch/validation).

---

## 3. Failure-honesty — visible strip/flag on a catch?

**Yes, for the register-leak lint, on every live call point checked.** Every
`lintReaderProse` call site that fires on the live path pairs a
leak/redaction with a visible `em.flag({ code: 'register_leak_scrubbed', … })`
(synthesis_stage.ts:833-838, reading_parts.ts:208-212) — never a silent
strip. `scrubToolArgs` returns a `redacted: boolean` the caller surfaces too
(reading_parts.ts:440-445 doc comment). Demonstrated directly in
call-point tests 2/3/4/5 above: each assert both "leak text gone from output"
AND "a flag/event fired."

**Partially no, for the citation gate specifically**, per §0: a reading with
**0 SIG.MSR-format citations found** (regardless of how many real footnotes
it actually contains) on a non-prescriptive query class produces a plain
`gate_result: 'PASS'` with no flag, no judgment_flags entry, nothing
reader- or operator-visible distinguishing it from a reading that was
genuinely well-cited. That is a real gap in failure-honesty for the citation
(not the register-leak) half of S9 — an honest "0 verified, format mismatch
suspected" signal does not exist for the non-prescriptive-class path, only
for the WARN path (which requires layer1_count > 0 to even trigger).

---

## 4. Demonstrated-can-fail — real red/green

`.s4_scratch/s9_register_leak_callpoints.scratch.test.ts` — **8/8 green**,
seeding a known leak pattern through the REAL exported function at each of
the 5 named call points (plus the offline review.ts gate) and proving the
catch:

```
✓ call point 1: synthesis_stage.ts:827 delta-lint (flag-OFF direct path)
✓ call point 2: reading_parts.ts commitBlock() whole-block lint backstop
    (leak split across TWO delta chunks so no single delta contains the
    full token — proves the whole-block backstop specifically, not just
    a re-test of the delta lint)
✓ call point 3: reading_parts.ts scrubToolArgs (tool-call args persistence path)
✓ call points 4/5: citations/rewriter.ts CitationStreamRewriter — lintEmit (line 330)
✓ call points 4/5: citations/rewriter.ts CitationStreamRewriter — flushHold (line 217)
    (forced via a real 78-byte unclosed sentinel body exceeding MAX_HOLDBACK_BYTES=64,
    triggering the byte-ceiling flush path specifically)
✓ call point 6 (offline): reader_text/review.ts reviewEntry
✓ S9 validation latency (N=20) — both payload sizes
```

Combined with §2's 5/5 green evasion-probe file (4 real reds — leaks that
survive — plus 1 green control proving the harness itself is not
miscalibrated), this gives genuine red/green evidence on both sides: the
lint demonstrably catches what it's designed to catch, AND demonstrably
misses specific, reproducible evasion classes. Full pasted stdout for both
files is in the scratch test runs above; run again with:
```
cd platform && npx vitest run .s4_scratch/s9_register_leak_callpoints.scratch.test.ts \
  .s4_scratch/s9_leak_evasion_probe.scratch.test.ts \
  .s4_scratch/e005_density_measure.scratch.test.ts --reporter=verbose
```

---

## Findings shaped for EDIR_V3 entry (do not self-file — hand to coordinator)

### F1 — E-005 re-measurement: citation density measured at 50% of distinct claims; footnote count updates from 2→7 but a worse defect sits underneath
- **Class / proposed severity:** DEFECT · S2 (proposed) — upgrades E-005 from
  IMPROVEMENT-flagged BASELINE toward DEFECT: the counter that is supposed to
  measure density is structurally blind to this door's real citations.
- **Lens(es):** L-CODE, L-DATA.
- **Pipeline stage:** S9.
- **Expected:** citation density is measured, not assumed; the counter that
  measures it can see the citations the model actually produces.
- **Observed (2026-08-28):** live reading via MCP door, synthetic chart
  `1c826d5a-…`, job `e6870d9f-…`/trace `498e3184-…`: 7 real `[^N]` footnotes,
  50% claim-density by hand count, but `countSignalCitations()` = 0 because
  footnote definitions are raw UUIDs, not `SIG.MSR.NNN` — violates the
  synthesis prompt's own citation-format contract
  (`synthesis_prompt_v2.ts:36-46`).
- **Code anchor:** `platform/src/lib/synthesis/citation_check.ts:14` (pattern),
  `platform/src/lib/pipeline/prashna_ask_synthesis.ts` (evidence source),
  reading capture: `platform/.s4_scratch/e005_density_measure.scratch.test.ts`.
- **Proposed fix class:** either (a) `citation_check.ts`'s pattern accepts a
  UUID-shaped footnote definition when it resolves against a known evidence
  row id, or (b) the MCP door's evidence floor is made to surface real
  `SIG.MSR.NNN` ids so the model has the contracted format to cite.
- **Rung achieved:** INTEGRATION + one LIVE data point.
- **Provenance:** reproduces/updates E-005.

### F2 — MCP door runs zero S9 validation (register-leak lint AND citation gate)
- **Class / proposed severity:** DEFECT · S2 (proposed, matching E-048's own
  triage) — door-parity: one of two production doors has no grounding/safety
  validation stage at all.
- **Lens(es):** L-CODE.
- **Pipeline stage:** S9.
- **Expected:** every door that returns synthesized prose runs the same S9
  gate (or an equivalent), so a leak/uncited-claim defense that exists on one
  door exists on both.
- **Observed (2026-08-28):** grep-confirmed zero matches for
  `lintReaderProse|validateCitations|register_leak|citation_gate|runValidationStage`
  in `platform/src/app/api/mcp/prashna_ask/route.ts` or
  `platform/src/lib/pipeline/prashna_ask_synthesis.ts`. The captured F1
  reading — containing raw evidence-row UUIDs in visible prose — passed
  through completely unlinted.
- **Code anchor:** `platform/src/app/api/mcp/prashna_ask/route.ts:743-759`
  (the `synthesizeReading` call, no lint/gate wrapper anywhere in the file).
- **Proposed fix class:** wire `lintReaderProse` over `synthesis.reading`
  before it enters `readingEnvelope`, and run `validateCitations`/an
  equivalent gate, surfacing the result in `judgment_flags` the same way the
  web door does.
- **Rung achieved:** INTEGRATION (static grep) + LIVE (the captured reading
  itself is the positive proof of an unlinted output reaching a caller).
- **Provenance:** reproduces E-048.

### F3 — Per-query-class citation density threshold table is dead code
- **Class / proposed severity:** DEFECT · S3 (proposed, matching E-050).
- **Lens(es):** L-CODE.
- **Pipeline stage:** S9.
- **Expected:** a declared per-class minimum-citation table is actually
  consulted by the gate it exists next to.
- **Observed (2026-08-28):** grep-confirmed `MIN_CITATIONS_BY_CLASS`,
  `hasMinimumCitations`, `citationThresholdForClass` have zero callers
  outside `citation_check.ts` itself and its own unit test.
  `validateCitations()`'s real gate logic only checks "≥1 verified citation,"
  never the per-class floor.
- **Code anchor:** `platform/src/lib/synthesis/citation_check.ts:17-29,53-64`.
- **Proposed fix class:** call `hasMinimumCitations`/`citationThresholdForClass`
  from `validateCitations()` (or delete the table and its exports if the
  design intent was superseded).
- **Rung achieved:** STATIC (caller-count grep).
- **Provenance:** reproduces E-050.

### F4 — Register-leak lint has 4 confirmed evasion classes on current code
- **Class / proposed severity:** IMPROVEMENT · S3 (proposed, matching E-039).
- **Lens(es):** L-CODE.
- **Pipeline stage:** S9.
- **Expected:** the PPR-04 "100% seeded-id catch" claim holds against a
  reasonable adversarial variant sweep, or is scoped honestly to what it
  actually covers.
- **Observed (2026-08-28):** `.s4_scratch/s9_leak_evasion_probe.scratch.test.ts`,
  5/5 green: lowercase acronym, mixed-case acronym, uppercase asset-id
  prefix, and spaced-out acronym all pass through `lintReaderProse` with
  `leakCount: 0` and the original text intact. No seeded false-negative-rate
  corpus exists to give this a formal percentage.
- **Code anchor:** `platform/src/lib/pariprashna/citations/register_leak_lint.ts:80`
  (asset-id pattern, lowercase-only prefix class), `:99` (register-acronym
  pattern, uppercase-only), `:157` (near-miss lowercase set — telemetry only,
  never redacts).
- **Proposed fix class:** case-insensitive matching (with care for prose
  words that collide, e.g. common English words), and/or a real seeded
  evasion corpus wired into a CI-run false-negative-rate check.
- **Rung achieved:** INTEGRATION (real vitest, real red for 4/5 cases).
- **Provenance:** reproduces E-039.

### F5 — `reader_text/review.ts:40` is not a live-turn call point
- **Class / proposed severity:** DOC · S4 (proposed) — non-blocking scope
  correction, not a functional defect.
- **Lens(es):** L-CODE.
- **Pipeline stage:** S9 (doc/anchor scope only).
- **Expected:** a document naming "5 call points that fire on the live path"
  names 5 call points that all fire on a live per-turn request.
- **Observed (2026-08-28):** `reader_text/review.ts:40`'s `lintReaderProse`
  call is reachable only from `generate_and_freeze.ts`, a manually-run,
  offline catalog-build script (own header: run via
  `npx tsx --conditions=react-server`). It never runs during a live turn.
- **Code anchor:** `platform/src/lib/pariprashna/reader_text/review.ts:40`,
  `platform/src/lib/pariprashna/reader_text/generate_and_freeze.ts`.
- **Proposed fix class:** reword the test-plan's S9 anchor list to
  distinguish "4 live per-turn call points + 1 offline curation-time gate."
- **Rung achieved:** STATIC (caller-graph grep).
- **Provenance:** new, S4-lane finding — not a prior EDIR entry.

### F6 — Citation-gate PASS is not distinguishable from "0 citations, format mismatch" for non-prescriptive query classes
- **Class / proposed severity:** DEFECT · S3 (proposed) — failure-honesty gap
  adjacent to F1/F3.
- **Lens(es):** L-CODE.
- **Pipeline stage:** S9.
- **Expected:** per §N.6/§N.7 (an honest empty result is disclosed via a
  flag, never silently indistinguishable from a good result), a reading with
  zero machine-verifiable citations should be visibly flagged even when the
  query class doesn't hard-require them.
- **Observed (2026-08-28):** `validateCitations()` returns
  `{gate_result: 'PASS', gate_reason: "informational query (…); citations
  not required"}` for `layer1_count: 0` on any non-`PRESCRIPTIVE_CLASSES`
  query, with no flag distinguishing "genuinely no claims to cite" from "7
  real citations existed but none matched the expected pattern" (F1's exact
  case).
- **Code anchor:** `platform/src/lib/synthesis/citation_check.ts:139-145`.
- **Proposed fix class:** emit a distinct, low-severity flag when
  `layer1_count === 0` AND the raw text contains GFM footnote markers
  (`[^\d+]`) that didn't resolve to the expected pattern — an honest
  "format-mismatch suspected" signal instead of a bare PASS.
- **Rung achieved:** INTEGRATION (`.s4_scratch/e005_density_measure.scratch.test.ts`).
- **Provenance:** new, S4-lane finding, discovered via F1's live capture.

---
artifact: PARIPRASHNA_P2_CLOSE_REPORT_v1_0
canonical_id: PARIPRASHNA_P2_CLOSE_REPORT
version: 1.0
status: CLOSED — the durable record DD-12 (PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md
  §2) cites as its own closing evidence.
produced_during: PARIPRASHNA-P2-CLOSE (Claude Code, 2026-08-20 → 2026-08-21)
date: 2026-08-21
authoritative_side: claude
role: >
  The full account of the P2 pre-close audit, the native's ruling, and the
  execution that followed: what the audit found, which lanes were fixed and
  live-verified before close, which were ruled closed-as-delivered without
  further work, which carry forward as dated register entries, and the two
  investigations the native ordered before closing (Lane K's viability, the
  citation-gate determination). This is DD-12's own "cite THIS audit"
  pointer (PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md §2).
relates_to:
  - PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md (DD-11, DD-12, DD-19,
    DD-20, and the new DD-21/DD-22/DD-23 this report's own close authorizes)
  - PARIPRASHNA_ASBUILT_BASELINE_v1_0.md (regenerated as part of this close)
changelog:
  - "1.0 (2026-08-21): first and closing version — the P2-close arc in full."
---

# Paripraśna — P2 Close Report

## §1 — What this closes

P2 CLOSE ran a 4-step pre-close audit (STEP 1: DD-20 blast-radius; STEP 2:
per-lane delivery audit across the phase's lanes, evidence-only, "not from
the code, and not from the flag being on"; STEP 3: triage into MUST-FIX vs
CARRY; STEP 4: the DD-11/DD-12 binary decision DD-12 itself already named).
The audit's own full step-by-step transcript was delivered to the native as
a conversational report (and a published artifact) rather than committed
verbatim — this document is the durable, repo-side record of what the audit
concluded and what happened after the native ruled on it, which is what
DD-12 cites as its evidence.

**The native's own characterization of the audit's central finding** (P2
CLOSE — execution ruling, verbatim): *"seven lanes merged, flagged live, and
reported done while delivering nothing observable to a reader."* This report
does not re-litigate that count; it records what this session, working from
that ruling forward, fixed, verified, and carried.

## §2 — Ruling and execution: items 1–7 + Lane K

The native's ruling ordered seven must-fix items in dependency order (items
1–3 unblock four downstream lanes between them), cleared items 5–7 to
proceed independently, and — after items 1–3 shipped and were live-verified
— added an eighth: **Lane K (typed confidence)**, gated on first verifying
Lane M actually renders.

Every item below was **merged, deployed, and independently live-verified**
(real probe turn, real browser observation with CDP device metrics, or a
direct database read) before being counted done — no lane in this list
closes on CI-green or code-review alone, per the new binding rule this
report's own close files as **DD-21**.

### Item 1 — DD-20: schema-binding fix (`interpretation/worker.ts`)
PR #1398 (`369719a99`). Added real Zod validation (`parseAndValidateSets`)
distinguishing "valid JSON, wrong envelope shape" from "no sets at all," and
a corrected repair-retry message restating the required `{"sets":[...]}`
shape explicitly. **Live-verified** post-deploy via a real probe turn: the
primary attempt failed validation (logged), the repair-retry fired and
succeeded, producing genuine `status: "generated"` entries — reconfirmed in
a later live browser turn (`interpretation_sets.detected_count: 4,
covered_count: 4, waived_count: 0`, all four judgments carrying real
generated candidate sets with a selection and a falsifier).

### Item 2 — Citation sentinel wiring (`synthesis_stage.ts`)
PR #1399 (`4e6301770`). Spliced `PARIPRASHNA_CITATION_APPENDIX` (already
written, never imported by any real call site) into the live system-prompt
assembly, additive and flag-gated. **Live-verified**: `citation.define`
fired 10 times on one probe turn and 5 on a later browser turn — the
appendix is genuinely reaching the model. See §3 below for the
`citation_gate_error` determination this unblocked but did not fully close.

### Item 3 — Receipt wire event (6 files, 2 new test files)
PR #1400 (`a1266f348`). New `receipt.define` SSE event
(`protocol/events.ts`/`emitter.ts`), emitted from `persistence_stage.ts`,
threaded through the client reducer into `TurnState.receipt` and its
`interpretationSets` projection. **Live-verified**: one real `receipt.define`
event per turn, carrying the full receipt including populated
`interpretation_sets` and (in the turns checked) 10 and then 2 real
`facts_consumed` entries with genuine `YGA.*`/`PLN.*`/`UCN_*`/`RM.*`/`DVS.*`
refs.

### Item 5 — RightDock mobile collapse (`RightDock.tsx`, `DockController.tsx`)
PR #1401 (`729972bd2`). `DockController.tsx`'s `MOBILE_BREAKPOINT_QUERY` was
only ever consulted for chip-tap routing; nothing hid the dock element
itself, so it rendered unconditionally and crushed the reading column on a
real phone viewport. Fix: `max-[900px]:hidden` on `RightDock`'s root,
matching the breakpoint the controller already documented. The existing
`tests/pariprashna/gates/g-mobile.spec.ts` battery cannot cover this — its
harness (`scripts/replay/server.ts`) is a standalone hand-built DOM with no
`RightDock` in it at all, deliberately (its own `playwright.config.ts`
header: "no dependency on the Next.js app at all"). Added a new real e2e
spec (`tests/e2e/pariprashna/dock-collapse.spec.ts`,
`SMOKE_SESSION_COOKIE`-gated, following `tests/e2e/portal/cockpit-rail.spec.ts`'s
pattern) plus a `pp-main-column` testid and a `vitest.config.ts` exclude
follow-up (the new Playwright spec was briefly being picked up by vitest
too). **Live-verified with real CDP device metrics** (not the fixture
harness): at 390×844, `[data-testid="pp-right-dock"]` computed
`display:none`, `offsetWidth` 0, main column real width (298px, not
crushed); at 1280×900, `display:flex`, dock visible — the breakpoint
genuinely discriminates in both directions.

### Item 6 — Observability identity wiring (`app/api/pariprashna/route.ts`)
PR #1402 (`e53fa58cb`). `synthesis_observation.ts`'s own header had said
since lane P2-E that `runSynthesisStage`'s `observability` identity was
"omitted by every caller today" because route.ts — the one caller, and the
one place `turnId`/`conversationId`/`user.uid` actually live — was out of
that lane's `may_touch` scope; every synthesis turn since had honestly
*skipped* its `llm_usage_events` write rather than fabricate the NOT-NULL
`conversation_id`/`user_id`. Wired the three-field identity through exactly
as that module's own doc comment specified. Zero wire-protocol change
(`route_golden_stream.test.ts`, 56/56, confirms). **Live-verified via a
direct database read**, not the write path's own success log: a real
`llm_usage_events` row for the live turn (`prompt_id
49738a7f-37b5-49da-910f-797b67c7cdfb`), `pipeline_stage: "synthesize"`,
`provider: "gemini"`, `model: "gemini-2.5-pro"`, `input_tokens: 52366`,
`output_tokens: 3248`, `status: "success"`, `channel: "web"`.

### Item 7 — Voice-lint bare-imperative anchor (`voice/voice_lint.ts`)
PR #1403 (`74b9f4adf`). `BARE_IMPERATIVE_START` required the sentence to
start with the capitalized remedy verb itself, but remedy prose is
routinely a bulleted/labeled list ("* **Frequency:** Chant this
mantra..."), so the verb is the first word of the clause, not the first
character `splitSentences` hands the regex. Reproduced live against
production BEFORE fixing (a real remedial probe turn: `"*
**Frequency:** Chant this mantra 108 times every evening."` and `"*
**Fasting:** Observe a simple partial fast on Mondays."` both went through
unflagged). Fix: an optional, bounded `IMPERATIVE_LABEL_PREFIX` (bullet/number
marker + a short bold-or-plain colon-terminated label) ahead of the existing
anchor. New unit tests pin both live-reproduced strings, a plain-label
variant, and a negative-control sibling (a labeled gerund) to guard against
overmatching. **Live-verified**: a fresh post-deploy browser turn produced
`"* **Practice:** Chant this mantra 108 times (one full rotation of a
mala) every day."` — the exact target grammatical shape — and
`voice_imperative_detected` fired on the turn.

### Lane K — typed confidence (added mid-window, native-ruled)
PR #1404 (`3d08d1c1a`). Before building anything, **verified live** (real
browser turn, not code inspection) that Lane M
(`InterpretationSetsSection.tsx`, #1400's `receipt.define` event) genuinely
renders real candidate/falsifier content — expanding "Read it another way"
showed two real alternate readings with rationale, not an empty shell.
Checked whether `confidence_typing` could piggyback on M's OWN component per
the native's stated hypothesis: it structurally cannot —
`InterpretationSetsSection` is keyed by `judgment_id`, but
`confidence_typing.entries` are keyed by `ref`, "the same token as
`facts_consumed[].ref`" per `TypedConfidenceEntrySchema`'s own doc comment.
That `ref` token IS the same one `GroundingCard.tsx`'s own `citation.ref`
already carries (`s1LiveAdapter.ts: ref: ev.signal_id`) — confirmed by
direct read. So the natural, bounded home is `GroundingCard.tsx` (an
existing, already-live sibling dock component to M in the same
`RightDock`), not a new component: `RightDock.tsx` builds a
`ref -> confidence_type` lookup from `turn.receipt.confidence_typing`
(already wired by #1400); `GroundingCard.tsx` renders the PPR-03 type as a
plain-language label next to the existing ref line when expanded.
Honest-absence discipline: no entry for a ref, no label — never a guessed
type. **Live-verified**: expanding citation 1 in a real browser turn showed
`"RM.05 · structural signal"` — the label rendering from real receipt data,
matching the L2.5-layer → `structural_prior` mapping in `confidence/types.ts`.

## §3 — `citation_gate_error` on prescriptive/remedial content: DETERMINED, not suppressed

The native ordered this determined, not fixed on sight: establish whether
remedial content genuinely has no citable source, or sources exist and
simply aren't being cited.

**Evidence, from two independent real turns** (a probe-harness turn asking
about career timing + remedies, and a later browser turn asking purely
about a Moon remedy):

- `retrieve:remedial_codex_query` — "Remedial prescription lookup from the
  Remedial Codex v2.0 (Parts 1 & 2)... gemstones, mantras, yantras, devata
  practices, dinacharya, and propitiation rituals... with scripture
  citation" (`retrieval_capability_spec.ts`'s own description) — genuinely
  ran and returned data both times (`count: 1`, real latency).
- Real Remedial Matrix (`RM.*`) signals entered the citable pool both
  times (`RM.34`, `RM.05` cited in the first turn; `RM.05` cited again in
  the second) — confirmed via `provenance_assembler.ts`'s own
  `remedial_codex_query: 'RM'` mapping.
- Yet in **both** turns, the entire remedial/prescriptive program section
  of the model's own output — gemstone, mantra, fasting, deity-worship
  instructions, several hundred words each time — carried **zero** `[n]`
  citation markers. Every citation that fired attached only to the
  diagnostic/astrological-explanation portion of the same response.
- `citation_gate_error` fired both times: `"prescriptive query (remedial)
  produced 0 citations — guidance must be grounded"`.

**Determination: case (b).** Sources exist and were genuinely fetched this
turn — the gate's own 0-citation reading is objectively true and the gate
is functioning correctly, not a false positive. The root cause is a
coverage/generation gap: the synthesis model is not attaching citation
sentinels to the remedial span of its own output, even when real
remedy-specific source material was retrieved and even when the SAME turn
cites other material correctly elsewhere. **Not suppressed** — this is
real, correct signal that a real class of output remains ungrounded.

## §4 — New finding: remedial guidance is under-governed as a content class

**OWNED — UNDATED. Does not block P2 close.**

Evidence: in the same live browser turn that live-verified item 7 and Lane
K, TWO independently-built honesty controls flagged the SAME remedial
content in the SAME turn:

- Item 7's own voice-lint imperative detector fired (`voice_imperative_detected`,
  2 hits) on a turn whose remedial section contained genuine label-prefixed
  bare imperatives (`"* **Practice:** Chant this mantra 108 times..."`).
- §3's citation gate fired on the same remedial span for the same reason —
  ungrounded prescriptive content.

This is a second, independently-gathered instance of the exact intersection
the native named when ordering this finding filed: a voice-register control
built for one purpose and a citation-grounding control built for another
purpose are both, independently, converging on the same content class
(remedial/prescriptive guidance) as under-served by the general-purpose
machinery built for descriptive/diagnostic prose.

**Scoped as an investigation, not a fix.** Open questions for whoever picks
this up: does remedial guidance need its own voice register (a prescriptive
mode with different imperative-phrasing conventions than descriptive prose,
which currently treats ALL second-person imperatives identically regardless
of content class)? Does it need its own citation policy (a dedicated
remedial-source-citation requirement, distinct from — and possibly stricter
than — the general prescriptive/predictive gate, given `remedial_codex_query`
already returns real, structured, scripture-cited material that the model
is evidently not obligated to attach)? Or both? Filed here as **DD-23**
(§5 below).

## §5 — Item 4: table-in-prose block promotion — RULED OUT of P2, approach (c) APPROVED, not built

Original finding: a markdown table embedded inside a larger prose block
(rather than occupying the whole block) never renders as a structured
`table` block, because `parseMarkdownTable` only recognizes a table when it
IS the entire committed block and block boundaries in
`reading_parts.ts`'s `ensureBlock(role)` are keyed purely on role changes
(prose vs. thinking), never on content shape.

**Native's ruling:** out of P2-close scope — "presentation degradation of
content that does reach the reader (a legible markdown pipe-table), not a
missing capability." Approach (a) (mid-stream detection touching the
streaming loop) **rejected** — the per-block path runs HS-1, the register
lint, and the voice lint; destabilising safety gates for a formatting fix
was not an acceptable trade. Approach (c) ("annotate rather than split" —
keep one block per role-shift, attach table metadata/offset ranges to the
existing block, let the renderer draw a real table from a span inside it,
zero change to `committedBlocks`' cardinality) was to be evaluated for
viability BEFORE any build, gated on items 1–3 (#1398/#1399/#1400) being
merged, deployed, AND observed working live — "change the ground under them
now and a failure becomes undiagnosable."

**Sequencing honored**: the viability evaluation below did not begin until
after §2's items 1–3 were independently live-verified (per this report's
own evidence above).

**Viability finding, direct code evidence:**

- `commitBlock()` (`reading_parts.ts`) runs the register-leak lint, the
  HS-1 mortality scan, and the voice lint — in that order, on the FULL
  block text — strictly BEFORE `classifyCommittedBlock` runs at all (lines
  199–349 of that file, read directly, not inferred). A read-only
  table-span annotation added alongside classification would sit strictly
  after all three safety scans and touch none of them. This is the direct
  answer to the native's fourth acceptance criterion below.
- `commitBlock()` pushes exactly ONE `OpenBlock` per role-shift regardless
  of classification; an added optional field (e.g. `tableSpans`) would not
  change that cardinality.
- `accumulatedText` (what citation extraction reads, per `detectTurnCitations`)
  is built by `appendProse` during streaming, entirely independent of
  commit-time classification — untouched by construction, not merely by
  discipline.
- Every real consumer of `committedBlocks`
  (`interpretation/detect.ts`, `receipt/assemble.ts`'s `facts_consumed`/
  `prose_binding`/`derivation_chains`) reads `.text`/`.role`/
  `.semantic.kind`/`.semantic.role` as whole values, never by character
  offset — confirmed by direct grep and read of both files. A new
  annotation field is additive and invisible to them.

**Ruling: approach (c) APPROVED on this evidence. Not built now** — carried
as its own dated entry, **DD-22** (§ below), with (c) recorded as the ruled
approach and the line-level findings above as its justification, so
whoever picks it up does not re-derive them. Native's acceptance criteria
for whichever approach is eventually built, recorded verbatim for that
future work:

1. Byte-exact reconstruction — emitted pieces concatenated must equal the
   original block text exactly, the same golden-equality discipline the
   ports refactor used.
2. Regression proof against #1399 — citations still extract correctly,
   verified by a live probe turn showing `citation.define` events, not by
   unit test alone.
3. Regression proof against #1400 — `facts_consumed` still populates the
   receipt correctly, verified by a live turn plus a DB read.
4. Proof, not assumption, that the safety scans genuinely ran on the full
   text before any split or annotation — **discharged above** by this
   report's own direct read of `commitBlock()`'s scan-then-classify
   ordering.

## §6 — Lane disposition

**Closed as delivered** (per the native's ruling): C, G, H's sidebar. D
remains closed under DD-16.

**Carried as filed, dated register entries** (per the native's ruling): N
(quality corpus), O (model qualification), H's Seal motion (not observed,
not inferred — never marked delivered).

**Must-fix, now delivered and live-verified** (§2 above): items 1, 2, 3, 5,
6, 7, and Lane K (added mid-window). Root causes B → K (citation sentinel)
and I/J → M (receipt wire event) are the specific downstream lanes items 2
and 3 unblocked.

**Ruled out of P2 scope, carried with an approved approach**: item 4 (§5),
filed as DD-22.

## §7 — DD register changes this close authorizes

This report is the evidence PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md
§2 cites for:

- **DD-11** → **ADVISORY** (downgraded from IN FORCE — NOT YET WIRED), per
  DD-12's own binary-outcome rule, branch (b): the `lane` wrapper was not
  built before P2 closed.
- **DD-12** → **CLOSED**, citing this report as its evidence.
- **DD-21** (new) — the binding rule effective P3 onward: no lane may be
  marked closed without an observed-delivery artifact.
- **DD-22** (new) — item 4, carried, approach (c) approved (§5 above).
- **DD-23** (new) — remedial guidance under-governed, OWNED — UNDATED (§4
  above).

*End PARIPRASHNA_P2_CLOSE_REPORT v1.0.*

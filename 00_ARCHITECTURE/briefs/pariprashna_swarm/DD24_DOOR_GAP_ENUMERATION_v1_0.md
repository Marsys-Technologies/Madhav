---
artifact: DD24_DOOR_GAP_ENUMERATION
canonical_id: DD24_DOOR_GAP_ENUMERATION
version: 1.0
status: CURRENT — P3-B's own input document (DD-24, Charter §4 Wave P3-2)
role: >
  The enumerated baseline DD-24 requires before P3-B (headless-loop extraction)
  runs and before P3-D (door parity) may assert anything: every known
  behavioural difference between the web door (`/api/pariprashna`) and the MCP
  door (`/api/mcp/prashna_ask`), re-derived from the code at
  `origin/main@7e5f478bd` (2026-08-23, overnight P3+P4 run, P3-D-PREP builder),
  each marked `propagated-knowingly` or `fixed-first`. DD-24's own text: "the
  web door's known gaps must be ENUMERATED in the P3-B lane brief and each
  explicitly marked either propagated-knowingly or fixed-first. P3-D's parity
  assertion is valid only against that enumerated baseline." This document is
  that enumeration. It does NOT extract the headless loop and does NOT open
  P3-B — that is a separate lane's job; this is P3-B's input.
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md
    (DD-22, DD-23, DD-24 — DD-24's own seed enumeration, explicitly superseded
    by this re-derivation per its own instruction: "RE-DERIVE at P3 open — do
    not inherit this list verbatim")
  - 00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_P2_CLOSE_REPORT_v1_0.md
    §3/§4 (DD-23's live evidence)
  - platform/src/app/api/pariprashna/route.ts (web door)
  - platform/src/app/api/mcp/prashna_ask/route.ts (MCP door)
  - platform/src/lib/pipeline/prashna_ask_synthesis.ts (MCP door's synthesis)
  - platform/tests/pariprashna/receipt/wire_persisted_byte_agreement.test.ts
    (P3-D's other precondition, built alongside this document — see that
    file's own header)
changelog:
  - "1.0 (2026-08-23): first version. Re-derived from the code, not inherited
    from DD-24's 2026-08-21 seed list. Twelve gaps enumerated (G1–G12); ten
    counted as live behavioural differences between the doors, two (G11, G12)
    noted as conditional/not-yet-applicable or out-of-scope-by-definition and
    excluded from the tally with the reasoning stated inline."
---

# DD-24 Door Gap Enumeration — web door vs. MCP door, as of 2026-08-23

## §0 — What this is, and what it binds

DD-24 (`PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md` §2) reads, verbatim,
on the rule this document exists to satisfy:

> **The rule:** before P3-B propagates web-door behavior to the MCP door, the
> web door's known gaps must be ENUMERATED in the P3-B lane brief and each
> explicitly marked either propagated-knowingly or fixed-first. P3-D's parity
> assertion is valid only against that enumerated baseline. Parity is
> evidence that two doors agree; it is never evidence that either is correct.
> No parity pass may be cited as delivery evidence (per DD-21's
> observed-delivery-artifact rule) for any capability listed in the
> enumeration.

DD-24's own seed list (filed 2026-08-21, before this session) explicitly says
not to inherit it verbatim: *"RE-DERIVE at P3 open — do not inherit this list
verbatim; it will have changed by then."* This document is that
re-derivation, done by reading the two doors' route files and their shared
collaborators directly — not from memory of the seed list, and not by
copying it. Where a seed-list item is re-confirmed still true, it is cited
and re-stated with fresh evidence, not pasted.

**Definitions, per the charter's own usage:**
- **`propagated-knowingly`** — P3-B's extraction will (or, per available
  evidence, is likely to) carry this difference forward deliberately, and
  P3-D's parity assertion must exclude it from any byte/hash equality claim.
- **`fixed-first`** — this must close before parity is claimed. Several of
  these are closed BY CONSTRUCTION once P3-B re-bases `prashna_ask` onto the
  shared headless loop "with all gates" (Charter §4 Wave P3-2's own phrase);
  they are marked `fixed-first` here because P3-D may not assert parity while
  they remain open, not because a second, separate fix session is implied.

## §1 — Method (so a later reader can re-check or extend this)

Read directly, this session, against `origin/main@7e5f478bd`:

- `platform/src/app/api/pariprashna/route.ts` (web door shell) and its eight
  pipeline stage modules under `platform/src/lib/pariprashna/pipeline/`
  (`safety_gate.ts`, `plan_stage.ts`, `evidence_stage.ts`,
  `synthesis_stage.ts`, `validation_stage.ts`, `receipt_stage.ts`,
  `persistence_stage.ts`, `reading_parts.ts`).
- `platform/src/app/api/mcp/prashna_ask/route.ts` (MCP door, full file, 763
  lines) and `platform/src/lib/pipeline/prashna_ask_synthesis.ts` (the MCP
  door's synthesis call).
- `platform/src/lib/pariprashna/receipt/{schema,assemble,store}.ts` (the
  `AcharyaReadingReceipt` the parity assertion will hash).
- `platform/src/lib/pariprashna/corpus/fixtures.ts` (the existing
  `door_parity` quality-corpus fixture, which already carries its own
  2026-08-20 finding on this exact question — cited below, not silently
  reused).
- `PARIPRASHNA_P2_CLOSE_REPORT_v1_0.md` §3/§4/§6 (DD-23's live evidence and
  the P2 lane disposition).
- Targeted greps for the specific machinery each door either does or does not
  run: `citation_gate`/`runValidationStage`/`detectTurnCitations`,
  `register_leak`/`lintReaderProse`/`voice_lint`/`scanMortality`, `writeTurn`/
  `conversation`/`message_parts`/`metadata_json`, `AcharyaReadingReceipt`,
  `admitWithinLimits`/`enforceTurnLimits`, `neutralizeDelimiters`/
  `preWireExtraRules`/`entitlementRules`.

Every gap below cites the file(s) and, where load-bearing, the specific
comment or grep result that established it — this is not a reconstruction
from memory or from the DD-24 seed text.

## §2 — The enumeration

| # | Gap | Evidence | Marking |
|---|---|---|---|
| G1 | **No persistence at all on the MCP door.** No `conversation_messages`/`message_parts` write, no canonical `writeTurn` call, anywhere in the route. | Full-file grep of `platform/src/app/api/mcp/prashna_ask/route.ts` for `conversation\|writeTurn\|writeConversationMessages\|message_parts\|metadata_json\|insertConversation` returns **zero** matches. Confirmed independently by `platform/src/lib/pariprashna/corpus/fixtures.ts`'s own `door_parity` fixture note (2026-08-20): *"`prashna_ask_bridge.ts` has no reference to `receipt`/`Receipt`, register-leak linting, or the citation stream — confirming ... the MCP door does not yet share the web door's gates."* | **fixed-first** |
| G2 | **No `AcharyaReadingReceipt` assembly or emission on the MCP door.** Corollary of G1 — `assembleAcharyaReadingReceipt` (`receipt/assemble.ts`) is never imported or called by `route.ts` or `prashna_ask_synthesis.ts`. | Grep for `AcharyaReadingReceipt` across `platform/src/app/api/mcp/` and `platform/src/lib/pipeline/prashna_ask_synthesis.ts`: zero matches. | **fixed-first** — this is the field P3-D's parity assertion hashes (Charter §4 Wave P3-3: "Parity hashes the persisted receipt object"). There is currently nothing on the MCP side to hash. |
| G3 | **No B.11 citation gate / no post-hoc citation validation on the MCP door's output.** The model is instructed (via the shared system prompt) to emit `[n]` citation markers, but nothing checks whether it actually did. | Grep for `citation_gate\|runValidationStage\|detectTurnCitations\|CitationGate` in both `route.ts` and `prashna_ask_synthesis.ts`: zero matches. Web door's equivalent is `pipeline/validation_stage.ts`'s `runValidationStage`, called from `route.ts` before persistence. | **fixed-first** |
| G4 | **No register-leak lint, no HS-1 mortality-phrasing backstop scan, no voice-enforcement lint, and no G1-G answer-side entitlement/foreign-chart-reference scan on the MCP door's output.** All four live inside `ReadingPartsAssembler.commitBlock()` (`pipeline/reading_parts.ts`) and its caller `synthesis_stage.ts` (`entitlementRules`/`preWireExtraRules`, lines ~535–620), which the MCP door never instantiates — `prashna_ask_synthesis.ts` returns one flat `reading` string. | Grep for `register_leak\|lintReaderProse\|voice_lint\|scanMortality` in `route.ts`/`prashna_ask_synthesis.ts`: zero matches. MCP's own injection containment (`isInjectionContainmentEnabled`/`neutralizeDelimiters`, `prashna_ask_synthesis.ts` lines 56–58, 259, 376, 395–396) is confirmed to be a **prompt/evidence-side** sanitizer only — a different mechanism from the web door's **answer-side** entitlement scan, which rides `commitBlock()` and is therefore absent here too. | **fixed-first** — this is the safety-relevant item in the enumeration; P3-B's "with all gates" scope names exactly this class of machinery. |
| G5 | **DD-23 (remedial citation coverage gap) will propagate onto the MCP door once G3 closes.** Web door confirmed live, twice (`PARIPRASHNA_P2_CLOSE_REPORT_v1_0.md` §3): real remedial sources fetched, real `RM.*` signals enter the citable pool, yet the entire remedial/prescriptive prose span carries zero `[n]` markers — the citation gate's 0-citation reading is real, not a false positive (case (b), determined not suppressed). `prashna_ask_synthesis.ts` reuses the **identical** system prompt and citation format (`consumeSystemPromptV2`, module header line 40) as the web door. | P2 close report §3/§4; `prashna_ask_synthesis.ts` header comment: *"Reuses the SAME acharya-grade system prompt + citation format consult uses ... so the two doors produce prose in the same voice."* | **propagated-knowingly** — this is a content-generation defect in the shared prompt/model behavior, not a door-wiring defect. Propagating the web door's REAL behavior onto the MCP door means propagating this real, already-filed defect (DD-23) too — the exact paradigm case DD-24 itself was written to name. P3-D's parity assertion must exclude the remedial-citation-coverage dimension from any "the doors agree, therefore both are grounded" claim. |
| G6 | **No consent-lane (`subject_kind`) resolution on the MCP door.** `classifyTurnSafety` is called with `subjectKind: null` on the MCP door. | `route.ts` lines ~296–305, verbatim: *"This route has no consent-lane resolution — G1-B wired `resolveSubjectConsent` into the web door's `authorizeTurn` and not into this one — and `null` is the honest value for 'nobody checked' ... the strict-direction default means the gap costs safety nothing."* | **propagated-knowingly** — explicitly owned by a DIFFERENT lane (G1-B), not P3-B's headless-loop-extraction scope. P3-D's parity assertion must exclude any consent-dependent field (e.g. NCD-4 interstitial gating, notification-obligation state) until G1-B closes this separately. Not safety-regressive by the code's own account (fails toward the stricter path), but it IS a real, named behavioral difference and must not be silently absorbed into a parity "pass." |
| G7 | **Two non-unified cost/limit mechanisms, by design.** Both doors share NCD-8 (`enforceTurnLimits`, `$2/turn`/`$40/day` pre-dispatch) — confirmed both call sites invoke the identical helper from `@/lib/limits` (`route.ts` line ~232 for MCP; `pipeline/safety_gate.ts`'s `admitWithinLimits` for web) — **this half is NOT a gap.** But the MCP door additionally runs a separate `CostCapTracker`/`resolveCostCapsForEntitlement` call-count + wall-clock ceiling with SEQUENTIAL (not parallel) tool dispatch and its own `completeness.cap_tripped`/`status: 'partial'` disclosure shape; the web door's nearest equivalent is the floor compiler + `arbitrateBudgets`'s token-budget model plus the agentic loop's own dynamic tool-calling — no analogous "stop after N calls / T ms mid-turn" ceiling. | `route.ts`'s own docstring: *"dispatches tools SEQUENTIALLY, one at a time ... parallel dispatch cannot honor a 'stop after N calls / after T ms' contract mid-flight"* (vs. the consult route's `Promise.all` parallel fetch the web door shares). | **propagated-knowingly** — a deliberate MCP-specific design for a synchronous HTTP call with a hard wall-clock ceiling, not a bug. P3-D's parity assertion should exclude `completeness.cap_tripped`/partial-vs-complete semantics from a byte-level receipt comparison; the two doors' completeness models are shaped differently by design, not by omission. |
| G8 | **Wire protocol / transport shape differs entirely, and is not stated to be touched by P3-B's charter scope.** Web door: SSE, the typed Paripraśna vocabulary (`turn.open`, `phase`, `block.open/delta/commit`, `citation.define`, `receipt.define`, `turn.close`, …) via one `PariprashnaEmitter`. MCP door: NDJSON lines (`{event:'progress'|'final'|'error', ...}`), no per-block streaming, no `protocol/events.ts` vocabulary at all. | `route.ts`'s dispatch-loop comment: *"the loop body now lives inside a ReadableStream's `start()` and emits one NDJSON progress line per completed dispatch iteration, ending with a single `{"event":"final", ...}` line."* Confirmed no import of `protocol/emitter.ts` or `protocol/events.ts` anywhere in the MCP route. | **propagated-knowingly, flagged for re-derivation at P3-B's own open** — the charter states `prashna_ask` gets re-based onto the **shared loop** "with all gates"; a shared engine loop does not by itself imply a shared wire encoder. Whoever opens P3-B should confirm explicitly whether the wire is unified too. Until confirmed otherwise, this stays propagated-knowingly for P3-D — a receipt-hash parity claim does not require wire-format parity, but a reader-facing behavioral parity claim would, and the two must not be conflated. |
| G9 | **No resume/replay support on the MCP door.** Web door has `/api/pariprashna/resume`, a per-turn ring buffer (`protocol/ring_buffer.ts`'s `openTurnBuffer`/`appendBufferedEvent`) and `protocol/stream_capture.ts`. MCP's route has no equivalent. | No matching resume/replay/ring-buffer machinery found anywhere in `platform/src/app/api/mcp/prashna_ask/`. Route's own docstring: *"Runs synchronously, in one HTTP response ... a later task builds the async job-handle wrapper around this call"* — explicit future work, not present. | **propagated-knowingly** — orthogonal to P3-B's stated scope (loop + gates). Does not block a receipt-hash parity claim on a completed turn, but is real and worth naming so nobody assumes reconnect-safety exists on the MCP door today. |
| G10 | **`chart_header` is a first-class, top-level field on the MCP door's response envelope** (`route.ts`'s `readingEnvelope.chart_header`, populated from `fetchChartHeaderResolution`); on the web door, the equivalent (`orientation.chart_header`/`current_maha_antar`, `synthesis_stage.ts` line 255) is confirmed as an internal SYNTHESIS-CONTEXT input, and this enumeration did **not** exhaustively trace whether an equivalent reader-visible field reaches the web door's own wire events or its persisted receipt. | `route.ts`'s `readingEnvelope` construction; `synthesis_stage.ts:255`. | **UNDETERMINED — see §3, not silently assumed either way.** |

## §3 — Honest limits of this enumeration (§N.7 item 6: name the edges, don't imply completeness)

**What was searched:** both doors' route shells in full; every pipeline stage
module the web door's route imports; the MCP door's synthesis module in
full; the existing `door_parity` quality-corpus fixture; the P2 close
report's own citation-gate and table-promotion findings; targeted greps for
persistence, receipt assembly, citation validation, register-leak/voice/
mortality linting, and the two doors' cost-limit call sites.

**What this enumeration did NOT do, stated plainly:**

1. **G10 (`chart_header`) is left undetermined, not guessed.** I did not trace
   every wire event schema in `protocol/events.ts` or every field of
   `AcharyaReadingReceipt` looking for a reader-visible `chart_header`
   equivalent on the web door. A later reader closing P3-B should re-check
   this specifically before relying on it either way.
2. **No live probe was run.** Everything above is static code reading —
   accurate to what the code says it does, not confirmed by an actual paired
   turn on both doors against the synthetic chart. Per this lane's own
   constraints (P3-D-PREP builder brief), no live turn was attempted; the
   wire↔persisted byte-agreement test built alongside this document (see
   `platform/tests/pariprashna/receipt/wire_persisted_byte_agreement.test.ts`)
   is the closest thing to a live-code check this session performed, and it
   is scoped to the web door only.
3. **The DD-24 seed list's items 4–6** (the quality corpus / model
   qualification / Lane H Seal-motion carries, `PARIPRASHNA_P2_CLOSE_REPORT_
   v1_0.md` §6) are **deliberately excluded from the G-numbered tally above.**
   They are test-coverage/delivery-verification gaps (do we have enough
   confirmed evidence that a capability works), not behavioral differences
   BETWEEN the two doors — DD-24's own rule targets the latter ("a parity
   check on a known defect converts a tracked gap into an untracked one");
   including test-coverage gaps in this enumeration would blur that
   distinction rather than sharpen it. They remain open, dated register
   entries in their own right; nothing here closes or supersedes them.
4. **DD-22 (table-in-prose block promotion)** does not appear as its own
   G-number. Reasoning: DD-22 is a defect of `commitBlock()`'s block/pass
   machinery, which — per G4 above — the MCP door does not run AT ALL today.
   DD-22 is therefore not currently a live difference between the two doors
   (the MCP door has no table-in-prose behavior to compare, correct or not).
   It becomes a live, propagated-knowingly gap the MOMENT G3/G4 close and the
   MCP door starts running the same block assembler — whoever closes G3/G4
   should re-open DD-22 against the MCP door explicitly at that point rather
   than assume this document already covered it.
5. **No attempt was made to enumerate every JSON field name that differs
   between the MCP door's flat envelope and the web door's `receipt`/wire
   event shapes** (e.g. `completeness.tools_dispatched` vs.
   `AcharyaReadingReceipt.coverage`) beyond the structural gaps (G1–G10)
   already named. A field-by-field schema diff was judged out of this lane's
   scope (P3-B/P3-D's job once the MCP door actually has a receipt to diff
   against) and would have been guesswork before G1/G2 close.
6. **This enumeration is current as of `origin/main@7e5f478bd` (2026-08-23).**
   Per DD-24's own instruction to future readers, RE-DERIVE, do not inherit
   verbatim, if material time has passed or either route has changed.

## §4 — Summary for P3-B / P3-D

**Tally: 10 live behavioral differences enumerated (G1–G10); 2 items (G11-class DD-22, G12-class test-coverage carries) explicitly excluded from the tally with reasoning in §3.**

- **`fixed-first` (4): G1, G2, G3, G4** — persistence, receipt assembly,
  citation gate, and the whole-block safety/entitlement lint suite. These
  close BY CONSTRUCTION when P3-B re-bases `prashna_ask` onto the shared
  headless loop "with all gates" — they are not a separate fix list, they
  are what "with all gates" means. P3-D may not open until these four are
  observably true on the MCP door (DD-21 evidence, not code-reading).
- **`propagated-knowingly` (6): G5, G6, G7, G8, G9, G10(undetermined)** — a
  shared prompt defect (G5/DD-23), a separately-owned consent-lane gap (G6,
  owned by G1-B), a deliberate dual cost-cap design (G7), an unconfirmed wire
  unification question (G8), absent resume support (G9), and one
  undetermined field-shape question (G10). P3-D's parity assertion must
  explicitly exclude every one of these dimensions from any "the doors
  agree" claim — per DD-24, a parity pass is never delivery evidence for a
  capability listed here.

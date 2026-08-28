# S4 §4.3 Synergy Test #2 — Degradation Propagation Honesty

Scope: trace each of the 7 degraded modes from the condition firing through to
whatever renders to the user. Test subject: synthetic chart
`1c826d5a-41cb-4450-b4dc-59d440e5f75a`. Evidence rung: INTEGRATION
(demonstrated-can-fail). S8 touched only lightly per instructions — E-004 is
covered in depth by a dedicated agent.

Worktree: `pariprashna-v3-s4`. No files under `platform/src` were left
modified — one proof test was written, run, and its output captured here,
then moved to `.s4_scratch/evidence/s2_entitlement_misclassification_proof.test.ts`
(4/4 passing, `npx vitest run` from `platform/`) rather than left in the
source tree.

## Summary table

| # | Degraded mode | Stage | Flag-only or visible-disclosure | Evidence |
|---|---|---|---|---|
| 1 | Classifier low-confidence | S1 | **VISIBLE-DISCLOSURE (correct)** | `pipeline_planner.ts:385-408` short-circuits `fallback_recommended` to `buildClarificationFromScope()`. `plan_stage.ts:208-214` commits the clarification question as a REAL prose block (`em.blockOpen/blockDelta/blockCommit` on `block_id:'clar-0'`) in addition to a `clarification_needed` flag. Confirmed no defect. |
| 2 | Entitlement denial | S2 | **VISIBLE but MISCLASSIFIED (defect, worse than flag-only)** | `safety_gate.ts` `authorizeTurn` emits `em.error({code:'FORBIDDEN'\|'CHART_NOT_FOUND'\|'SUBJECT_CONSENT_REQUIRED:<reason>'\|'CONVERSATION_NOT_FOUND', message, ...})`. Client `s1LiveAdapter.ts:335-341` routes EVERY `error` event through `classifyPariprashnaError(ev.code)`, discarding `ev.message` ("stays server/log-side only"). `classify.ts`'s `classifyKind()` (lines 112-124) has no case for any of these codes — they all fall to `'unknown'` → bandLabel **"Something failed on our side"**, sentence **"Not the chart, not your question — the plumbing. It is logged."**, action `['retry']`. Proven by test: `classifyPariprashnaError('FORBIDDEN')`, `('CHART_NOT_FOUND')`, `('SUBJECT_CONSENT_REQUIRED:no_consent_row')`, `('CONVERSATION_NOT_FOUND')` all assert `kind:'unknown'` + the generic copy — 4/4 pass. |
| 3 | Safety reframe | S3 | **VISIBLE-DISCLOSURE (correct)** | `safety_gate.ts` `runSafetyPolicyGate` calls `speak()` (real committed prose blocks) for `hard_stop` (`HS2_FIXED_RESPONSE`), `seal_pending_signoff` (`SEAL_PENDING_ACKNOWLEDGMENT`), `interstitial` (`NCD4_INTERSTITIAL_NOTICE`), and — critically — `resolveAction()` in `safety/gate.ts:88` proves the ONLY path to `action:'reframe'` requires `classes.includes('hs1_date_of_death')`, so `decision.classes_detected` always contains that class when reframe fires, which unconditionally triggers `speak('safety-hs1-0', HS1_WITHHOLD_NOTICE)`. All five fixed-response strings (`fixed_responses.ts`) are substantive, specific prose, not stubs. Confirmed no defect. |
| 4 | Tool timeout | S6 | **FLAG-ONLY / indistinguishable (defect)** | `evidence_stage.ts`'s per-tool `catch` emits `em.activity({key, status:'error', ms})` and logs a `toolEventLog` entry. Client `ActivityRow.tsx:13-17` renders the glyph as `row.status === 'done' ? '✓' : isTool ? '▸' : '○'` and color as `row.status==='done' ? gold : gold-tertiary` — **no branch for `'error'`**, so an errored/timed-out tool renders pixel-identical to a still-running or not-yet-started one. The richer signal that WOULD capture this — `buildWebCompletenessReceipt`'s per-floor-item `route_error`/`empty` observations, surfaced via `receipt_stage.ts`'s `em.grade({subject:'completeness', grade:'N/M', detail: channel_note})` — is dropped entirely by the adapter (`s1LiveAdapter.ts:273-282`: `case 'grade': if (subject!=='reading_depth_received') return []`). `synthesis_stage.ts` never references `completenessReceipt`/`channel_note`/`coverage` (grep: 0 hits), so the model is never told which floor items are empty/dark and cannot narrate the gap either. |
| 5 | Empty bundle | S7 | **LOG-ONLY / never reaches the envelope at all (defect, most severe)** | `bundle_hydrator.ts`: a non-floor asset missing from the manifest, missing a `path`, or failing `storage.readFile()` is handled with **`console.warn(...)` and `continue`** (lines 107, 114, 127-130) — a bare server console log. `hydrateBundle(plan, manifest)` doesn't even accept an `em`/emitter parameter (`evidence_stage.ts:66`), so there is structurally no way for this failure to become a flag, grade, or error event on the SSE wire — it never reaches the client in any form, machine-readable or otherwise. Only the one FLOOR asset (`CGM`) is fatal (throws → becomes a real `em.error()`); every other silent gap in the bundle is a pure log line. |
| 6 | Synthesis truncation (cross-check only) | S8 | Not independently re-verified in depth (dedicated agent's scope: E-004) | `synthesis_stage.ts` has no `truncat*` handling distinct from a generic style-instruction string (line 159). The systemic pattern found at S6/S9 — `grade`/`flag` events dropped by `s1LiveAdapter.ts`'s adapter layer before ever reaching the reducer — is the same *class* of defect E-004 documents (evidence-truncation flagged in the envelope, never disclosed in prose): this session's findings suggest E-004 is one instance of a repo-wide adapter-level absorption pattern, not an isolated bug. Leave full re-verification to the E-004 agent. |
| 7 | Validator strip | S9 | **FLAG-ONLY (defect, textbook case)** | `validation_stage.ts:56-63`: citation gate WARN/ERROR emits `em.grade({subject:'citation_gate', grade:'WARN'\|'ERROR', detail})` **and** `em.flag({code:'citation_gate_warn'\|'citation_gate_error', level, detail})`, plus pushes into `judgmentFlags` (server-side only). On the wire: the `grade` event is dropped entirely (`s1LiveAdapter.ts:273-282`, same drop as #4 above — `citation_gate` is not `reading_depth_received`, so `return []`). The `flag` event does reach the reducer (`s1LiveAdapter.ts:270-271`) but `reducer.ts:290-292`'s `case 'flag'` only updates `lastEventId`/`seenEventIds` — **no visible UI state change of any kind**. `validation_stage.ts`'s own docstring already flags the adjacent risk ("no citation_gate grade on the wire is the only observable signal the gate errored" on a swallowed throw) — this session confirms that even the non-swallowed WARN/ERROR path is equally invisible, so there is no path by which a B.11 grounding-validation failure ever reaches the reader as prose, a badge, or any rendered marker. (`register_leak_lint.ts`'s REDACT/REWRITE mechanism is a separate S9 sub-path: it DOES alter visible prose text in place — by design it must stay silent about *what* it redacted, since naming the internal register would itself be a leak — so this sub-path is intentionally, not defectively, non-disclosing. Not counted as a defect.) |

## EDIR_V3-shaped candidate entries (not filed — for the register owner)

**Candidate 1 — S2 entitlement-denial codes misclassified as generic transient failure**
- Class: DEFECT
- Proposed severity: S1 (proposed) — safety/consent-adjacent: `SUBJECT_CONSENT_REQUIRED` is a PPR-14 consent refusal, and the same code path handles `FORBIDDEN`
- Lens(es): synergy / degradation-honesty
- Pipeline stage: S2 (`platform/src/lib/pariprashna/pipeline/safety_gate.ts` `authorizeTurn`) → client `platform/src/components/pariprashna/state/s1LiveAdapter.ts:335-341` → `platform/src/lib/pariprashna/errors/classify.ts:112-124`
- Expected: an entitlement/consent refusal is disclosed as what it is, with an action set that does not suggest retrying will help
- Observed: rendered as "Something failed on our side... the plumbing. It is logged." with `actions:['retry']`; the actual `message` (e.g. "Not authorized for this chart.") is discarded before reaching the classifier
- Code anchor: `classify.ts` `classifyKind()` lines 112-124 (no case matches `forbidden`, `chart_not_found`, `subject_consent_required`, `conversation_not_found`)
- Proposed fix class: add explicit `kind`s (e.g. `'not_authorized'`, `'not_found'`, `'consent_required'`) to `classifyKind`/`copyFor` with non-retry actions, OR forward a safe subset of `ev.message` for these specific business-logic codes
- Rung: INTEGRATION — proven by a passing vitest run (4/4) against the real `classifyPariprashnaError`
- Provenance: sibling of E-003/E-004's class (flag/signal present, disclosure absent-or-wrong), distinct instance

**Candidate 2 — S7 empty-bundle non-floor asset failures never reach the envelope**
- Class: DEFECT
- Proposed severity: S2 (proposed)
- Lens(es): synergy / degradation-honesty
- Pipeline stage: S7 (`platform/src/lib/bundle/bundle_hydrator.ts` lines 107, 114, 127-130; called from `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:66`)
- Expected: a non-floor asset failing to hydrate should be visible to the client as at minimum a flag, and ideally disclosed in prose when it changes what the reading can support
- Observed: `console.warn()` only; `hydrateBundle` takes no emitter; the failure never becomes any wire event
- Code anchor: `bundle_hydrator.ts:107,114,127-130`
- Proposed fix class: thread `em`/a warnings collector through `hydrateBundle`, emit `em.flag({code:'asset_hydration_failed', ...})` per skipped asset, and feed the skip list into the synthesis prompt/completeness receipt
- Rung: INTEGRATION — confirmed by direct code read of the (only) two exit paths for a non-floor asset failure
- Provenance: same class as E-004, one layer upstream (evidence gathering, not synthesis)

**Candidate 3 — S6/S9 `grade` events with any subject other than `reading_depth_received` are dropped before the reducer**
- Class: DEFECT
- Proposed severity: S2 (proposed)
- Lens(es): synergy / degradation-honesty
- Pipeline stage: S6 + S9 (`platform/src/components/pariprashna/state/s1LiveAdapter.ts:273-282`)
- Expected: a `grade` event carrying a real degradation signal (`completeness`, `citation_gate`) reaches some visible or at least reducer-tracked state
- Observed: `case 'grade': if (ev.subject !== 'reading_depth_received') return []` — the event is discarded before the reducer ever sees it
- Code anchor: `s1LiveAdapter.ts:273-282`
- Proposed fix class: either route non-`reading_depth_received` grade subjects into reducer-tracked (even if collapsed/aggregated) state, or stop emitting them server-side if they are genuinely never meant to reach the client (the latter would at least stop the false appearance of an audit trail)
- Rung: INTEGRATION — confirmed by direct code read; the same code path is exercised by both S6's `completeness` grade and S9's `citation_gate` grade
- Provenance: sibling of E-004; likely also explains E-004 mechanically if S8's evidence-truncation flag is emitted as a non-whitelisted `grade` subject

**Candidate 4 — S9 `flag` events are reducer-inert (bookkeeping only)**
- Class: DEFECT
- Proposed severity: S2 (proposed)
- Lens(es): synergy / degradation-honesty
- Pipeline stage: S9 (`platform/src/components/pariprashna/state/reducer.ts:290-292`)
- Expected: a `citation_gate_warn`/`citation_gate_error` flag — a real B.11 grounding-validation failure — surfaces to the reader in some form
- Observed: `case 'flag': ... only updates lastEventId/seenEventIds` — no visible state
- Code anchor: `reducer.ts:290-292`
- Proposed fix class: reducer should route citation-gate flags into `judgmentFlags`/a visible grounding-quality indicator already partially built (`GroundingCard`/`GroundingRegion`), not drop them
- Rung: INTEGRATION — confirmed by direct code read
- Provenance: same class as E-004; directly validates `validation_stage.ts`'s own docstring warning about the swallowed-throw case, extended to the non-swallowed case

## What is genuinely correct (do not re-flag)

- S1 (classifier low-confidence) and S3 (safety reframe/hard_stop/seal/interstitial) both commit real, specific, substantive prose blocks — this is the pipeline working as designed and is the right pattern the S2/S6/S7/S9 findings above should be brought into line with.
- `register_leak_lint.ts` (S9's other sub-mechanism) intentionally does not announce what it redacted; that is correct by construction (announcing the redacted register name would itself be the leak) and is not the same defect class as the citation-gate grade/flag drop.

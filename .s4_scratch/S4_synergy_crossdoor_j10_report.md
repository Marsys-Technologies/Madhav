# S4 §4.3 item 6 — Cross-door stage parity (whole-receipt) + J10

Chart under test: `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (synthetic — never
`482012f1-…`).

Representative interpretive question used to trace both paths: *"What does
my current Vimshottari daśā period reveal about my career prospects, and are
there any doṣas I should be watching for right now?"* — cross-domain
(dasha + career + dosha), forward-looking, exactly the class of question the
whole-receipt PPR-30 check is meant to exercise on both doors.

## Evidence rung

**Code-level comparison (fallback rung) — LIVE dual-door was not attempted
and is explicitly declared not attempted.** Deployed images (`amjis-web`,
`amjis-mcp`) are confirmed stale per the task brief, so they cannot be used.
A local-dev dual-door run was considered but not executed, for a reason that
is itself part of this report's finding, not an excuse: `grep -rn
"assembleAcharyaReadingReceipt\|runPersistenceStage"` across
`platform-mcp/src` and `platform/src/app/api/mcp/prashna_ask/route.ts`
returns **zero matches**. The MCP door's code path has no call edge into
receipt assembly at all, under any input. A live run through both doors
would exercise exactly the same source lines already read here and could not
produce a different structural outcome — the divergence is architectural
(missing call site), not data-dependent. Standing up an authenticated local
dual-door session (Portal SSE via `/api/pariprashna`, MCP via
`platform-mcp`'s OIDC/service-token bridge to a local `platform` dev server)
was judged not to change this report's central finding and was not worth the
setup cost against the time budget. **If a later pass wants LIVE
confirmation, the check that would matter is simply: does
`conversation_messages.metadata_json.acharya_reading_receipt` (Portal) vs.
the MCP door's JSON response ever contain a `receipt_hash` key — it never
will on the MCP side, by construction.**

## Critical framing caveat (read before the table)

`PARIPRASHNA_RECEIPT_EMISSION_ENABLED` (`platform/src/lib/config/
feature_flags.ts:572`) **defaults to `false`** — "Default false: ships
dark" (feature_flags.ts:344-345). So in the *current default-deployed
configuration*, the Portal door itself does not assemble or persist an
`AcharyaReadingReceipt` either — `persistence_stage.ts:504-505`'s
`if (isReceiptEmissionEnabled())` guard is never entered, and
`conversation_messages.metadata_json` never gets an
`acharya_reading_receipt` key. Under strict default-config comparison, the
two doors are trivially "equal" — both emit **no receipt at all** — which
would be a vacuous, useless answer to "does PPR-30 whole-receipt parity
hold."

The comparison below is therefore run **counterfactually with
`PARIPRASHNA_RECEIPT_EMISSION_ENABLED=true`** (the state the flag exists to
be flipped into, and the only state under which "whole-receipt parity"
is a question that means anything) traced against each door's actual code.
Under that condition, Portal assembles a full `AcharyaReadingReceipt` per
`platform/src/lib/pariprashna/receipt/assemble.ts`. **MCP still assembles
none, unconditionally** — the MCP door's code contains no reference to the
flag, the schema, or the assembler at all; flipping the flag does nothing on
that door. This asymmetry (one door's receipt is flag-gated dark-by-default;
the other door's receipt does not exist as a concept in the code) is itself
the headline finding and is recorded as Finding 0 below, ahead of the
per-field table.

## Root-cause context (already tracked — do not re-open as a fresh defect)

The MCP door's total absence of a durable/structured turn record is **already
self-documented in code** as `MCP_TURN_PERSISTENCE_NONE`
(`platform/src/app/api/mcp/prashna_ask/route.ts:163-167`), citing tracking
ids **P2-B-004 / E-119**, and is surfaced live on every MCP response as
`persistence: {status: 'none', detail: '...'}`. That finding is the general
"nothing durable is written for an MCP turn" gap. **PPR-30 is narrower and
additive to it**: even setting persistence-to-a-table aside, MCP has no
*in-memory* receipt-shaped object either — no code path ever constructs an
`AcharyaReadingReceipt` value for this door, so there is nothing to compare
field-by-field even transiently. Every finding below cites P2-B-004/E-119 as
shared root cause; whoever files these into EDIR_V3 should link them to
that existing item rather than treat each as an independent new root cause.

## Field-by-field comparison

| receipt field | Portal (`PARIPRASHNA_RECEIPT_EMISSION_ENABLED=true`) | MCP `prashna_ask` | MATCH / DIVERGE |
|---|---|---|---|
| `receipt_schema_version` | `1` (literal) | no receipt object exists | DIVERGE |
| `turn_id` | `args.turnId` (the turn's own id) | no equivalent field; `trace_id` (=`queryId`, a per-request UUID, semantically a request id not a persisted turn id) is the closest wire field but is never folded into a receipt | DIVERGE |
| `conversation_id` | `args.conversationId` | **no concept of a conversation at all on this door** (P2-B-004 comment: "this door has no multi-turn conversation concept") | DIVERGE |
| `chart_id` | `args.chartId` | `chart_id` present in the response envelope, but not part of any receipt structure | DIVERGE (present as raw field, absent as receipt field) |
| `generated_at` | `now.toISOString()` | none | DIVERGE |
| `coverage` | `{status, served, empty, dark, floor_item_total, channel:'web', channel_note, unavailable_reason}` from `WebCompletenessReceipt` | `completeness: {status:'complete'|'partial', tools_dispatched, unserved_tools, unresolved_tools, stripped_leaked_capabilities, empty_result_tools, cap_tripped}` — different field set, no `served`/`empty`/`dark`/`floor_item_total` counts, no `channel` (would need to be `'mcp'`, not `'web'`, if it existed) | DIVERGE |
| `facts_consumed` | `[{ref, layer, index}]` from `citationsFound` (real citation detection over committed prose blocks) | none — the synthesis reading (`synthesizeReading`, `prashna_ask_synthesis.ts`) never runs citation detection over its own output text | DIVERGE |
| `derivation_chains` | per committed block: `{block_id, pass_id, role, fact_refs}` | **no "committed block" concept exists on this door** — the reading is one opaque string returned by a single non-streaming LLM call | DIVERGE |
| `cross_domain` | `{status:'measured', domains: plan.domains}` | `plan.domains` is computed internally (used to call `ensureB11WholeChartReadFloor`, `reclassifyAfterPlan`) but is **never surfaced in the response envelope or captured anywhere** — available data, zero downstream consumer | DIVERGE |
| `evidence_grades` | `{status, grade_counts, hallucination_count}` from the G2-B live citation rewriter | none — no citation rewriter runs against the synthesis output on this door | DIVERGE |
| `honest_gaps` | `[{floor_item_id, kind:'empty'|'dark', reason}]` from `WebCompletenessReceipt.empty`/`.dark` | conceptually overlapping data exists (`unresolved_tools`, `empty_result_tools`, `stripped_leaked_capabilities` inside `completeness`) but in an **incompatible shape** — no `floor_item_id`/`kind`/`reason` triple, no `dark`/`cr_row` concept at all | DIVERGE |
| `safety_decision` | `{status, decision_id, enforced, severity, action, classes_detected, review_id, audit_written, unavailable_reason}` — the full `SafetyDecision` object | `classifyTurnSafety`/`reclassifyAfterPlan` **do run** (`route.ts:356-361`, `:485-491`) and gate dispatch, but the structured decision object is **never surfaced** in the final envelope — only derived string flags (`safety_decision:<action>`, `safety_mortality_capabilities_excluded`, `safety_classes_detected:<n>`) reach the wire; `decision_id`, `review_id`, `audit_written` are never exposed | DIVERGE |
| `calibration_disclosure` | `{consulted, consulted_tool_names, disclosure_note}` — scans `validToolResults` for `query_calibration`/`query_insights` | none — this scan is never run on this door | DIVERGE |
| `prose_binding` | `{blocks: [...], accumulated_text_sha256, accumulated_char_count}` | none — no block model, no hash computed over `synthesis.reading` | DIVERGE |
| `provenance` | `{build_id, priors_version, formula_versions, ranking_config, now_context_date, computed_at}` (`TurnProvenanceStamp`) | `nowContextDate` is computed and passed into `synthesizeReading` (temporal anchor for the model), but never wrapped as a provenance stamp; no `build_id`/`priors_version`/`formula_versions`/`ranking_config` equivalent anywhere on this door | DIVERGE |
| `interpretation_sets` | optional G3-B extension (present when `PARIPRASHNA_INTERPRETATION_SETS_ENABLED` on; honest `unavailable` default otherwise) | none — G3-B never runs on this door regardless of any flag | DIVERGE |
| `confidence_typing` | `{status, entries, activation_gate, precision_flags, unavailable_reason}` (G3-C) | none — G3-C never runs on this door | DIVERGE |
| `receipt_hash` | sha256 of canonical JSON of every field above | none | DIVERGE |

**18/18 top-level receipt fields diverge.** 0 match. This is not "the doors
phrase the same facts differently" (which would be expected and fine per the
task framing) — it is "one door's structured receipt object does not exist
at all," so every field is trivially absent rather than differently-valued.

## Findings (EDIR_V3-shaped, one per diverging field)

All findings below share root cause: MCP `prashna_ask`
(`platform/src/app/api/mcp/prashna_ask/route.ts`,
`platform/src/lib/pipeline/prashna_ask_synthesis.ts`) has no call path to
`platform/src/lib/pariprashna/receipt/assemble.ts` or
`platform/src/lib/pariprashna/pipeline/persistence_stage.ts` — confirmed by
`grep -rn "assembleAcharyaReadingReceipt\|runPersistenceStage"` returning
zero hits under `platform-mcp/src` and the MCP route file. Already tracked
generally as **P2-B-004 / E-119** (`MCP_TURN_PERSISTENCE_NONE`). All tagged
`PPR-30`.

---

**Finding 0 — Receipt-emission flag asymmetry: Portal is flag-gated dark-by-default, MCP has no such flag or concept**
- class: DEFECT
- proposed severity: P2 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt (both doors, pre-dispatch config)
- expected: a whole-receipt parity check should compare two doors that both *can* emit the same structured object, one governed by a flag both doors respect (or neither).
- observed: Portal's receipt emission is entirely controlled by `PARIPRASHNA_RECEIPT_EMISSION_ENABLED` (default `false` — `platform/src/lib/config/feature_flags.ts:572`, comment "ships dark" at :344). MCP has no equivalent flag check anywhere — its behavior (never assemble a receipt) is identical whether the flag is true or false, because the flag is never referenced on that door.
- code anchor — Portal: `platform/src/lib/config/feature_flags.ts:344-356,572`; `platform/src/lib/pariprashna/pipeline/persistence_stage.ts:504-505`. — MCP: (absence) confirmed via `grep -rn "PARIPRASHNA_RECEIPT_EMISSION_ENABLED" platform/src/app/api/mcp/prashna_ask/route.ts platform-mcp/src` → no matches.
- proposed fix class: either (a) MCP door onboards a receipt-assembly call site gated by the same flag, or (b) the flag/feature is explicitly re-scoped in doctrine as "Portal-only, not a cross-door contract" so PPR-30 is not evaluated against MCP until (a) lands.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 1 — `receipt_schema_version` / whole receipt object absent on MCP**
- class: DEFECT
- proposed severity: P2 (proposed) — subsumed by root cause, tracked for completeness of the field enumeration
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: MCP turn carries a receipt object at the same schema version as Portal (`ACHARYA_READING_RECEIPT_SCHEMA_VERSION = 1`).
- observed: no receipt object of any schema version is ever constructed on the MCP door.
- code anchor — Portal: `platform/src/lib/pariprashna/receipt/schema.ts:284-287`; `assemble.ts:544`. — MCP: no anchor exists; confirmed by the grep in the root-cause note above.
- proposed fix class: see Finding 0.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 2 — `turn_id`/`conversation_id` unavailable on MCP (no persisted-turn or conversation identity)**
- class: DEFECT
- proposed severity: P2 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: a receipt field that identifies which turn and which conversation it belongs to, matching Portal's `args.turnId`/`args.conversationId`.
- observed: MCP has no turn-identity or conversation-identity concept at all — its own code comment states this explicitly ("this door has no multi-turn conversation concept," `route.ts:145-146`). `trace_id` (`queryId`, a fresh UUID per HTTP call) is the nearest analog but is a request id, not a persisted-turn id, and is never attached to any receipt-shaped structure.
- code anchor — Portal: `platform/src/lib/pariprashna/receipt/assemble.ts:545-546` (`turn_id`, `conversation_id` from args). — MCP: `platform/src/app/api/mcp/prashna_ask/route.ts:251` (`queryId` generation), `:769` (`trace_id: queryId` on the wire, no receipt binding).
- proposed fix class: if MCP is ever given a durable per-turn record (the P2-B-004 fix), that record's id becomes this field's MCP-side source; until then this stays a structural gap, not a bug to patch in isolation.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 3 — `chart_id` present as a raw wire field but never bound into a receipt on MCP**
- class: DEFECT
- proposed severity: P3 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: `chart_id` is one field of many inside a single coherent receipt object, as on Portal.
- observed: MCP's `chart_id` is a top-level envelope field (`route.ts:771`) with no receipt wrapper around it at all — technically present as data, but structurally incomparable to Portal's receipt field of the same name.
- code anchor — Portal: `assemble.ts:546`. — MCP: `platform/src/app/api/mcp/prashna_ask/route.ts:769-771` (`readingEnvelope.chart_id`).
- proposed fix class: covered by Finding 0/1 fix; not independently actionable.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 4 — `generated_at` absent on MCP**
- class: DEFECT
- proposed severity: P3 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: a timestamp of when the reading/receipt was generated.
- observed: MCP computes `nowContextDate` (a date-only string, for the temporal anchor prompt) but never a receipt-shaped `generated_at` ISO timestamp.
- code anchor — Portal: `assemble.ts:548` (`generated_at: now.toISOString()`). — MCP: `route.ts:704` (`nowContextDate`, different purpose/shape, not surfaced as `generated_at`).
- proposed fix class: covered by Finding 0/1 fix.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 5 — `coverage` shape mismatch: MCP's `completeness` object is not the same schema and cannot be diffed field-for-field even if bound in**
- class: DEFECT
- proposed severity: P2 (proposed) — this is the one field where MCP has a real, populated near-equivalent, making the shape mismatch itself worth calling out precisely (not just "absent")
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: `coverage.{served, empty, dark, floor_item_total, channel, channel_note}` on both doors, `channel` distinguishing `'web'` from an MCP equivalent.
- observed: Portal's `coverage` is sourced from `WebCompletenessReceipt` with `channel: z.literal('web')` — hardcoded to the literal `'web'`, meaning even if this schema were reused verbatim on MCP it could never honestly report `channel` for that door. MCP's own `completeness` object (`status`, `tools_dispatched`, `unserved_tools`, `unresolved_tools`, `stripped_leaked_capabilities`, `empty_result_tools`, `cap_tripped`) has no `served`/`empty`/`dark`/`floor_item_total` numeric rollup at all — it is a dispatch-outcome list, not a floor-coverage count.
- code anchor — Portal: `platform/src/lib/pariprashna/receipt/schema.ts:44-54`; `assemble.ts:154-177`. — MCP: `platform/src/app/api/mcp/prashna_ask/route.ts:776-784`.
- proposed fix class: `ReceiptCoverageSchema.channel` needs a non-literal type (`z.enum(['web','mcp'])` or similar) before MCP could ever populate it honestly, in addition to Finding 0's gate; and a coverage-count adapter would need to be written translating MCP's dispatch-outcome list into `served`/`empty`/`dark`/`floor_item_total` counts, since those concepts don't exist 1:1 in the MCP dispatch loop today.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 6 — `facts_consumed` absent on MCP: synthesis reading text is never citation-scanned**
- class: DEFECT
- proposed severity: P2 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt (also touches S-narration/citation stages)
- expected: every fact the reading cites is recorded by reference (signal_id/layer/index), matching Portal's `facts_consumed`.
- observed: `synthesizeReading` (`prashna_ask_synthesis.ts`) returns a raw prose string (`interaction.finalText`); nothing downstream runs `detectTurnCitations`/`extractCitations`-equivalent detection over that string. The reading may contain the model's own citation-style tokens (the system prompt is the same `consumeSystemPromptV2` used on Portal, so citation formatting conventions are shared), but nothing parses or records them.
- code anchor — Portal: `assemble.ts:534-536` (`buildFactsConsumed`), sourced from `detectTurnCitations`/`citationsFound` in `persistence_stage.ts`. — MCP: `platform/src/lib/pipeline/prashna_ask_synthesis.ts:437-444` (`synthesizeReading` returns `{reading, model_id, judgment_flags}` — no citation extraction step exists in this file or its caller).
- proposed fix class: MCP door would need its own citation-detection pass over `synthesis.reading` before this field could be populated — a real feature addition, not a wiring fix, since no such pass exists anywhere in the MCP request lifecycle today.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 7 — `derivation_chains` absent on MCP: no committed-block model exists on this door**
- class: DEFECT
- proposed severity: P3 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: per-block fact-reference chains, matching Portal's `derivation_chains`.
- observed: MCP's `synthesizeReading` is a single non-streaming, non-agentic LLM call (explicitly documented as such in `prashna_ask_synthesis.ts:16-27`) that returns one opaque string. There is no `OpenBlock`/`committedBlocks` concept, no `ReadingPartsAssembler`, anywhere in the MCP request path.
- code anchor — Portal: `assemble.ts:522-532` (`buildDerivationChains` over `committedBlocks`). — MCP: no equivalent; confirmed by absence of any `committedBlocks`/`OpenBlock` reference in `platform/src/app/api/mcp/prashna_ask/route.ts` or `prashna_ask_synthesis.ts`.
- proposed fix class: would require introducing a block-segmentation step for MCP's single reading string, or an explicit doctrine decision that `derivation_chains` is a Portal-only concept for a non-streaming door.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 8 — `cross_domain`: `plan.domains` is computed on both doors but only surfaced on Portal**
- class: DEFECT
- proposed severity: P2 (proposed) — flagged higher than most siblings because the underlying data DOES exist in the MCP request scope; this is a pure wiring gap, not a missing-feature gap
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: `cross_domain.domains` reports which domains the plan authorized, on both doors — the same `plan.domains` value the shared `callPipelinePlanner` produces.
- observed: MCP's `plan.domains` is read internally (passed into `ensureB11WholeChartReadFloor(plan, toolsAuthorized)` and `reclassifyAfterPlan({..., domains: plan.domains ?? [], ...})`) but is never written to the response envelope (`readingEnvelope` at `route.ts:767-788` has no `domains`/`cross_domain` key) and never captured into any receipt-shaped structure.
- code anchor — Portal: `assemble.ts:179-188` (`buildCrossDomain`). — MCP: `platform/src/app/api/mcp/prashna_ask/route.ts:465` (`ensureB11WholeChartReadFloor(plan, toolsAuthorized)`), `:489` (`domains: plan.domains ?? []`), `:767-788` (`readingEnvelope` — no `domains` key).
- proposed fix class: cheapest fix in this whole finding set — add `domains: plan.domains ?? null` to `readingEnvelope` and (once Finding 0 lands) bind it into `cross_domain`. No new computation needed, the value already exists in scope.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 9 — `evidence_grades` absent on MCP: no citation-grading rewriter runs on this door**
- class: DEFECT
- proposed severity: P2 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: per-grade citation counts + hallucination count, matching Portal's `evidence_grades`.
- observed: the G2-B live citation rewriter (`resolvedCitations`, `citationHallucinationCount`) is a Portal-streaming-pipeline concept; MCP's synthesis call has no equivalent rewriter pass over its output.
- code anchor — Portal: `assemble.ts:190-215` (`buildEvidenceGrades`). — MCP: no equivalent; same absence as Finding 6 (both depend on citation processing that only exists on the Portal streaming path).
- proposed fix class: depends on Finding 6 landing first (citation detection is a prerequisite for citation grading).
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 10 — `honest_gaps` shape mismatch: MCP has overlapping but structurally incompatible gap data**
- class: DEFECT
- proposed severity: P2 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: `honest_gaps.gaps[]` as `{floor_item_id, kind:'empty'|'dark', reason}`, matching Portal.
- observed: MCP's `completeness.unresolved_tools`/`.empty_result_tools`/`.stripped_leaked_capabilities` are semantically related (all are "things the floor should have served but didn't, and why") but are flat tool-name arrays with no per-item `floor_item_id`/`kind`/`reason` triple, and MCP has no `dark`/`cr_row` concept (a Portal-specific NO-LEAKAGE-redaction category) at all.
- code anchor — Portal: `assemble.ts:217-234` (`buildHonestGaps`), `schema.ts:129-142`. — MCP: `route.ts:679-697` (`unresolvedTools`, `emptyResultTools` construction), `:776-784` (`completeness` object).
- proposed fix class: an adapter translating MCP's three tool-name arrays into `ReceiptHonestGap` rows is plausible (unlike Findings 6/7/9, the raw data exists), but `floor_item_id` (a Portal floor-registry concept) vs. `tool_name` (MCP's own naming) would need an explicit mapping decision, not an assumption they're interchangeable.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 11 — `safety_decision`: the full structured decision is computed on MCP but never surfaced, only lossy string flags are**
- class: DEFECT
- proposed severity: P1 (proposed) — flagged highest of the per-field findings: this is a safety-relevant audit field, the underlying `SafetyDecision` object genuinely exists in MCP's own request scope (unlike most siblings above), and the gap specifically drops `decision_id`/`review_id`/`audit_written` — the exact fields an auditor would need to correlate an MCP turn's safety outcome back to its `pariprashna_safety_decisions` row
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt (also S-safety)
- expected: `safety_decision.{status, decision_id, enforced, severity, action, classes_detected, review_id, audit_written}` on both doors — MCP explicitly runs the same `classifyTurnSafety`/`reclassifyAfterPlan` gate as Portal (`route.ts`'s own comment block at :313-352 states this is deliberately mirrored from the web door).
- observed: `safetyDecision`/`postPlanSafety` objects are held in MCP route scope (`route.ts:356`, `:483-491`) and used to gate dispatch and strip capabilities, but the final envelope only ever emits derived, lossy string flags — `safety_decision:<action>`, `safety_mortality_capabilities_excluded`, `safety_classes_detected:<n>` (counts only, by design — "gate 11 [integrity]" per the code comment at `route.ts:390-391`). The structured object itself, including `decision_id` and `review_id` (the FK fields an auditor would follow to `pariprashna_safety_decisions`), is discarded rather than attached to the response.
- code anchor — Portal: `assemble.ts:236-261` (`buildSafetyDecision`), `schema.ts:153-164`. — MCP: `route.ts:356-361` (`classifyTurnSafety` call), `:483-530` (`postPlanSafety` / `reclassifyAfterPlan` / `applyCapabilityExclusion`), `:511-516` and `:769-788` (only `judgment_flags` strings reach the wire, no `safety_decision` object).
- proposed fix class: near-zero-cost fix relative to Findings 6/7/9 — `postPlanSafety` already exists in scope at the point `readingEnvelope` is constructed; add a `safety_decision: buildSafetyDecision(postPlanSafety)`-equivalent key (reusing Portal's own `buildSafetyDecision` shape) to the MCP envelope. This does not require Finding 0's full receipt-assembly wiring to fix in isolation, since the safety object is already computed and in scope — it can land ahead of the rest.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 12 — `calibration_disclosure` absent on MCP**
- class: DEFECT
- proposed severity: P2 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: a disclosure of whether an L5 calibration-bearing tool (`query_calibration`/`query_insights`) was consulted this turn, matching Portal.
- observed: MCP's dispatch loop can call `query_calibration`/`query_insights` like any other tool (`toolResults` accumulates whatever the floor authorized), but nothing scans `toolResults` for `CALIBRATION_BEARING_TOOL_NAMES` the way Portal's `buildCalibrationDisclosure` does. A caller of MCP `prashna_ask` has no way to know, from the response, whether the reading's predictive claims were touched by a calibration-bearing tool this turn.
- code anchor — Portal: `assemble.ts:84,263-276` (`CALIBRATION_BEARING_TOOL_NAMES`, `buildCalibrationDisclosure`). — MCP: `route.ts:617,666-671` (`toolResults` accumulation — no calibration scan applied to it anywhere in this file).
- proposed fix class: cheap fix once Finding 0 lands — `buildCalibrationDisclosure` is a pure function over `ToolBundle[]`; MCP's `toolResults` (mapped from `{tool_name, bundle}` to `ToolBundle`) is directly compatible input.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 13 — `prose_binding` absent on MCP: no hash or block accounting over the reading text**
- class: DEFECT
- proposed severity: P2 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: a sha256 of the exact reading text plus block/char accounting, so the receipt can be proven to describe the exact text the reader saw.
- observed: MCP's `synthesis.reading` (a plain string) is placed directly into the envelope with no hash computed anywhere, and no block segmentation exists to enumerate (see Finding 7).
- code anchor — Portal: `assemble.ts:278-294` (`buildProseBinding`). — MCP: `route.ts:775` (`reading: synthesis.reading`) — no hash/binding computed.
- proposed fix class: the `accumulated_text_sha256`/`accumulated_char_count` half is a cheap fix (sha256 over `synthesis.reading`, no committed-blocks dependency); the `blocks[]` half depends on Finding 7's block-model gap and cannot be honestly populated without it.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 14 — `provenance` absent on MCP: no build/priors/formula/ranking stamp**
- class: DEFECT
- proposed severity: P2 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: `{build_id, priors_version, formula_versions, ranking_config, now_context_date, computed_at}` matching Portal's `TurnProvenanceStamp`.
- observed: MCP computes `nowContextDate` (`route.ts:704`) for the temporal-anchor prompt, but no `TurnProvenanceStamp` is ever built for this door — `build_id`/`priors_version`/`formula_versions`/`ranking_config` have no MCP-side source at all.
- code anchor — Portal: `assemble.ts:317-326` (`buildProvenance`); provenance stamp itself computed via `computeTurnReceiptProvenance` (`provenance/stamp.ts`, called from `persistence_stage.ts`). — MCP: `route.ts:704-710` (`nowContextDate` only, no stamp).
- proposed fix class: `computeTurnReceiptProvenance` would need to be called from the MCP route too — not yet confirmed whether that function's own inputs (build/priors/ranking config) are available in MCP's request scope; needs its own investigation before scoping a fix.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 15 — `interpretation_sets` absent on MCP**
- class: DEFECT
- proposed severity: P3 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: G3-B candidate-interpretation-sets extension, present (or honestly `unavailable`) on both doors.
- observed: G3-B (`assembleInterpretationSets`) is only ever called from `persistence_stage.ts`, itself unreachable from MCP. No `PARIPRASHNA_INTERPRETATION_SETS_ENABLED` reference exists anywhere in the MCP route or `prashna_ask_synthesis.ts`.
- code anchor — Portal: `platform/src/lib/pariprashna/pipeline/persistence_stage.ts:507-538` (interpretation-sets assembly block, itself nested inside the `isReceiptEmissionEnabled()` guard from Finding 0). — MCP: no anchor; confirmed absent.
- proposed fix class: strictly downstream of Finding 0/1 — this field cannot be fixed independently since it is an additive sub-object of the receipt itself.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 16 — `confidence_typing` absent on MCP**
- class: DEFECT
- proposed severity: P2 (proposed) — closest sibling to Finding 12 in spirit (typed-confidence classification depends on the same calibration-consultation signal), and directly touches predictive-claim honesty
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: G3-C typed-confidence entries + activation gate + precision flags, present (or honestly `unavailable`) on both doors.
- observed: `buildConfidenceTyping` is only called from `assemble.ts`'s own `assembleAcharyaReadingReceipt`, itself only called from `persistence_stage.ts` — unreachable from MCP. `PARIPRASHNA_TYPED_CONFIDENCE_ENABLED` has no reference on the MCP door.
- code anchor — Portal: `assemble.ts:389-480` (`buildConfidenceTyping`). — MCP: no anchor; confirmed absent.
- proposed fix class: strictly downstream of Finding 0/1, same as Finding 15.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

**Finding 17 — `receipt_hash` absent on MCP**
- class: DEFECT
- proposed severity: P3 (proposed)
- lens(es): synergy/cross-door-parity, journey J10
- pipeline stage: S11/receipt
- expected: sha256 hex of the canonical JSON of every other receipt field, matching Portal.
- observed: with no receipt object constructed at all, there is nothing to hash.
- code anchor — Portal: `assemble.ts:577-580`, `hash.ts` (`computeReceiptHash`). — MCP: no anchor; trivially absent given Finding 1.
- proposed fix class: automatic once Finding 0/1 land — `computeReceiptHash` is a pure function over whatever object precedes it.
- rung achieved: code-level comparison (fallback).
- tag: PPR-30

## Summary of severities (proposed, for EDIR_V3 triage)

- P1: Finding 11 (`safety_decision` — safety audit trail dropped despite the underlying decision object existing in MCP scope)
- P2: Findings 0, 1, 5, 6, 8, 9, 10, 12, 14, 16 (structural absence of load-bearing receipt sections; Finding 8 and 11 are the cheapest fixes since their source data already exists in MCP scope)
- P3: Findings 2, 3, 4, 7, 13(partial), 15, 17 (either genuinely no MCP-side concept to draw from, or downstream-only fields that fall out automatically once the root gate (Finding 0) is fixed)

All severities are proposed pending EDIR_V3 owner triage; none of these were independently validated against a live dual-door run (see rung statement above).

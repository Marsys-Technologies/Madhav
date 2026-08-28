# S4 §4.3 Synergy Test #1 — Boundary Contract Enforcement

**Stream:** Paripraśna assurance S4 (Pipeline Correctness & Door Parity)
**Scope:** the 10 inter-stage boundaries in the 11-stage typed-port pipeline (`stage_context.ts` §3 comment).
**Test subject:** synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` ONLY.
**Evidence rung:** INTEGRATION — real vitest harness, real function calls, no fixture-of-a-fixture.
**Harness:** `platform/.s4_scratch/boundary_contracts.test.ts` (22 tests, all pass — i.e. every
assertion matches the *observed* real behavior; a passing test here documents a finding, it does
not certify the boundary is safe). Run with `cd platform && npx vitest run .s4_scratch/boundary_contracts.test.ts`.

**Coverage: 10 of 10 boundaries tested.** One (B1) is DB-blocked in this sandbox (no network route
to Cloud SQL) and is reported as **NOT FULLY TESTED**, with the gap disclosed rather than assumed
safe — code inspection substitutes for the missing runtime DB proof and is called out as weaker
evidence.

---

## Summary table

| # | Boundary | Entry fn tested | Validation mechanism found | Result | 
|---|---|---|---|---|
| 1 | S1→S2 (NormalizedQuery→EntitlementDecision) | `authorizeTurn` (`safety_gate.ts:229`) | UUID_RE regex exists but lives in a **different, earlier** function (`admitRequest`); `authorizeTurn` itself performs **NONE** | **NOT FULLY TESTED** (DB unreachable in sandbox) / **NO GUARD AT THIS ENTRY** (by inspection) |
| 2 | S2→S3 (EntitlementDecision→SafetyPolicyDecision) | `runSafetyPolicyGate` (`safety_gate.ts:335`) | NONE (TS types only) | **CRASHED UNHELPFULLY** (malformed `messages`) / **SILENTLY PROPAGATED** (bogus `subjectKind`) |
| 3 | S3→S4 (SafetyPolicyDecision→ScopeTuple) | `ScopeTupleSchema` / `PipelinePlanSchema.safeParse` (`pipeline_planner.ts:301`) | **Real Zod schema, actively invoked** | **REFUSED LOUDLY** (positive control) |
| 4 | S4→S5 (ScopeTuple→AcharyaPlan) | `compileFloorForPlan` / `classifierTupleToCompilerTuple` (`compiled_floor_adapter.ts`) | NONE — Zod gate from B3 does not re-run here | **CRASHED UNHELPFULLY** (missing `domains`) / **SILENTLY PROPAGATED/CORRUPTED** (invalid `depth` enum → `depth: undefined`) |
| 5 | S5→S6 (AcharyaPlan→ToolBroker) | `runEvidenceStage` (`evidence_stage.ts`) | NONE for `plan.tool_calls`; a real (if incidental) guard for unregistered tool names | **CRASHED UNHELPFULLY** (`plan.tool_calls` wrong type) / **REFUSED LOUDLY** (unregistered/injected tool name → designed `activity:error`, no crash, no execution) |
| 6 | S6→S7 (ToolBroker→EvidenceBundle) | `hydrateBundle` (`bundle_hydrator.ts`) | NONE for `asset_bundle` shape; floor-asset presence check only | **CRASHED UNHELPFULLY** (`asset_bundle` wrong type) / **SILENTLY PROPAGATED** (entry missing `asset_id` → `console.warn`-only skip, no caller-visible signal) |
| 7 | S7→S8 (EvidenceBundle→Synthesis) | `assembleSynthesisContext` (`synthesis_stage.ts`) | NONE | **CRASHED UNHELPFULLY** (`bundle.assets` wrong type) / **SILENTLY PROPAGATED** (asset missing `content` → silently dropped from prompt, `.filter(Boolean)` masks it, zero signal) |
| 8 | S8→S9 (Synthesis→Grounding/Safety Validation) | `runValidationStage` (`validation_stage.ts:30`) | try/catch that **swallows every internal error and defaults to `PASS`**, by explicit design (see source header comment) | **SILENTLY PROPAGATED — WORST FINDING.** Malformed `accumulatedText` throws internally, is caught, and the B.11 grounding gate reports `PASS` with **zero wire event** (`em.grade` never fires — not even a WARN) |
| 9 | S9→S10 (Grounding/Safety Validation→SemanticReadingParts) | `buildCanonicalParts` (`reading_parts.ts`) | NONE | **SILENTLY PROPAGATED** (`committedBlocks` as a string is iterated as **characters** via JS's iterable protocol — no crash, looks like a clean empty result) / **SILENTLY DROPPED** (block with an invalid `role` value is discarded with no signal) |
| 10 | S10→S11 (SemanticReadingParts→TurnProvenance/Receipt) | `assembleAcharyaReadingReceipt` (`receipt/assemble.ts:538`) | NONE | **CRASHED UNHELPFULLY** (missing `provenanceStamp`/required fields → raw `TypeError`, twice, on two different accessed sub-fields) |

**Score: 1 of 10 boundaries has a real, actively-enforced runtime schema gate (B3). 0 of 10 boundaries
refuse a malformed object with a designed, caller-legible error at their own entry point** — B5's
"unregistered tool name" case and B6's "floor asset missing" case are graceful in *effect* but are
incidental byproducts of unrelated existing logic (a registry lookup miss, a floor-asset presence
check), not a boundary-contract validation step. Every other malformed-input probe is either an
**unhandled raw `TypeError`** (a JS runtime message, not a designed refusal) or a **silent
pass-through / corruption** with no caller-visible signal.

---

## Findings (EDIR_V3-shaped, for a later governance entry — NOT filed by this agent)

### Finding 1 — B.11 citation/grounding gate silently defaults to PASS on malformed synthesis output, with no wire signal at all
- **Class:** DEFECT
- **Proposed severity:** S2 (proposed) — the turn's citation/grounding gate is the enforcement point for B.11 (Whole-Chart-Read discipline / grounding validation); a silent PASS on an internal fault means a genuinely ungrounded or malformed reading can be served while the wire protocol reports nothing wrong (no `grade`, no `flag`, no judgment-flag entry) — worse than a wrong grade, because there is no signal at all for a later audit to catch.
- **Lens(es):** synergy / boundary-contract
- **Pipeline stage:** CROSS (S8→S9)
- **Expected:** a stage boundary should refuse loudly (or at minimum emit an explicit, client-visible degraded-grade signal) when its input is malformed enough that validation could not run.
- **Observed:** `runValidationStage` (`platform/src/lib/pariprashna/pipeline/validation_stage.ts:30-73`) wraps the entire citation-gate call in a try/catch that logs to the server console only and returns the PASS-default `citationGateResult` initialized before the try block; because the throw happens inside `validateCitationsForStream` *before* `em.grade({subject:'citation_gate', ...})` is reached, the `grade` wire event for this turn never fires at all — not PASS, not WARN, not ERROR. This is a deliberate, documented design choice (see the module's own header comment: "The gate NEVER fails the turn... swallowed... stays at its PASS default"), not an oversight, but the consequence (total absence of the grounding signal on a malformed-input turn) is undisclosed to the reader-facing wire protocol.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/validation_stage.ts:30-73`; malformed-input repro in `platform/.s4_scratch/boundary_contracts.test.ts` describe block "Boundary 8".
- **Proposed fix class:** at minimum, emit a `flag`/judgment-flag entry ("citation_gate_errored") from inside the catch block so the wire always carries a signal for this turn, even when the gate's own PASS default is intentionally preserved as the serving decision (§N.8 — "an honest null beats an invented judgment" / a flag needs a real detector or it is null).
- **Rung:** INTEGRATION.

### Finding 2 — No entry-point re-validation of `ScopeTuple`/`PipelinePlan` fields once past the one Zod gate; malformed tuples crash or silently corrupt downstream floor composition
- **Class:** DEFECT
- **Proposed severity:** S2 (proposed) — `compileFloorForPlan`/`classifierTupleToCompilerTuple` is reachable with an unvalidated tuple from any future caller (not only the one LLM-tool-call path `PipelinePlanSchema.safeParse` currently guards); an invalid `depth` enum value silently becomes `depth: undefined` in the compiled floor result with zero signal, and a missing `domains` array crashes with a raw, uncaught `TypeError` that would propagate out of `runPlanStage` with no designed error message.
- **Lens(es):** synergy / boundary-contract
- **Pipeline stage:** CROSS (S4→S5)
- **Expected:** the boundary that receives a `ScopeTuple`-shaped object should itself validate against `ScopeTupleSchema` (or fail with a designed, named error), not rely entirely on a single upstream call site having already validated it.
- **Observed:** `platform/src/lib/pipeline/compiled_floor_adapter.ts`'s `classifierIntentToCompilerIntent`/`classifierTupleToCompilerTuple`/`compileFloorForPlan` read `tuple.domains`, `tuple.width`, `tuple.depth`, `tuple.intent` directly with no `ScopeTupleSchema.safeParse` call anywhere in the file (confirmed by grep — zero `.parse`/`.safeParse` occurrences). A missing `domains` throws `TypeError: Cannot read properties of undefined (reading 'length')`; an invalid `depth` value passes through `DEPTH_MAP[tuple.depth]` as `undefined` with no error.
- **Code anchor:** `platform/src/lib/pipeline/compiled_floor_adapter.ts:86-121` (no schema check); repro in `platform/.s4_scratch/boundary_contracts.test.ts` describe block "Boundary 4".
- **Proposed fix class:** call `ScopeTupleSchema.safeParse` (or an equivalent guard) at the top of `compileFloorForPlan`, returning a designed no-op/error result on failure instead of trusting the caller.
- **Rung:** INTEGRATION.

### Finding 3 — `runEvidenceStage`/`hydrateBundle`/`assembleSynthesisContext` all crash with raw, unhandled `TypeError`s on wrong-typed array fields (`tool_calls`, `asset_bundle`, `assets`)
- **Class:** DEFECT
- **Proposed severity:** S3 (proposed) — a wrong-typed field (string instead of array — the shape a corrupted cache entry, a bad deserialization, or a future refactor bug could plausibly produce) crashes the pipeline with a bare JS runtime message rather than a legible, designed error, at three separate S5–S8 boundaries.
- **Lens(es):** synergy / boundary-contract
- **Pipeline stage:** CROSS (S5→S6, S6→S7, S7→S8)
- **Expected:** "a malformed object never crosses" a stage boundary (ARCHITECTURE §3) — the contract should refuse loudly at the boundary with a clear message identifying which field was malformed.
- **Observed:** three independent unguarded `.map()` calls on caller-supplied fields with no runtime type check: `plan.tool_calls.map(...)` in `evidence_stage.ts` (~line 69), `declared.map(...)` on `plan.asset_bundle` in `bundle_hydrator.ts:67`, and `(bundle.assets as Array<...>).map(...)` in `synthesis_stage.ts:241`. Each throws a bare `TypeError: X.map is not a function` with no pipeline-specific context.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:68-70`; `platform/src/lib/bundle/bundle_hydrator.ts:66-67`; `platform/src/lib/pariprashna/pipeline/synthesis_stage.ts:241-244`; repros in `platform/.s4_scratch/boundary_contracts.test.ts` describe blocks "Boundary 5/6/7".
- **Proposed fix class:** a shared, lightweight runtime array/shape guard applied at each stage's own entry point (e.g. `Array.isArray(...)` checks with a designed `PipelineBoundaryError`), rather than three independent unguarded call sites.
- **Rung:** INTEGRATION.

### Finding 4 — `buildCanonicalParts` silently iterates a wrong-typed `committedBlocks` value as string characters instead of failing
- **Class:** DEFECT
- **Proposed severity:** S3 (proposed) — a subtle JS-specific failure mode: passing a string where an array of blocks is expected does **not** throw (unlike the `.map()` cases above), because `for...of` over a string iterates its characters. The result looks like a legitimate, successful, empty output (`{parts:[],...}`) with no signal that the input was fundamentally the wrong type. This is more dangerous than a crash because it is silent and plausible-looking.
- **Lens(es):** synergy / boundary-contract
- **Pipeline stage:** CROSS (S9→S10)
- **Expected:** malformed input to `buildCanonicalParts` should be rejected or flagged, not silently absorbed into a valid-looking empty result.
- **Observed:** `platform/src/lib/pariprashna/pipeline/reading_parts.ts`'s `buildCanonicalParts` does `for (const b of input.committedBlocks)` with no `Array.isArray` guard; a string input iterates per-character, each character fails the `b.role === 'prose'|'thinking'` check, and the loop silently no-ops.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/reading_parts.ts:565-591`; repro in `platform/.s4_scratch/boundary_contracts.test.ts` describe block "Boundary 9", test "committedBlocks is not an array".
- **Proposed fix class:** an explicit `Array.isArray(input.committedBlocks)` guard at function entry, throwing or returning a designed empty-with-flag result rather than depending on the iterable protocol's incidental character-iteration behavior.
- **Rung:** INTEGRATION.

### Finding 5 (minor/observational) — Boundary 1 (authorizeTurn) could not be fully exercised in this sandbox; code inspection shows no local shape/type guard on `identity.chartId`
- **Class:** DEFECT (tentative — flag for re-verification with DB access)
- **Proposed severity:** S3 (proposed)
- **Lens(es):** synergy / boundary-contract
- **Pipeline stage:** CROSS (S1→S2)
- **Expected:** every boundary function defends its own input; the UUID-shape check for `chartId` should not live exclusively in a sibling function (`admitRequest`) that a differently-validated caller could bypass.
- **Observed:** `authorizeTurn` (`platform/src/lib/pariprashna/pipeline/safety_gate.ts:229`) passes `identity.chartId` straight into `query('SELECT id, name, client_id FROM charts WHERE id=$1', [chartId])` with no local type/shape check. This sandbox has no route to Cloud SQL (`CloudSQLConnectorError: Missing instance connection name` on every DB call, valid or malformed input alike), so the actual DB-side behavior on a malformed `chartId` (wrong type, non-UUID string) could not be observed directly. Recommend re-running `platform/.s4_scratch/boundary_contracts.test.ts` "Boundary 1" describe block from an environment with real DB access.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/safety_gate.ts:237` (the unguarded query call); `platform/.s4_scratch/boundary_contracts.test.ts` describe block "Boundary 1".
- **Proposed fix class:** N/A pending re-verification; if confirmed, add a UUID-shape assertion at the top of `authorizeTurn` itself rather than relying solely on `admitRequest`.
- **Rung:** NOT FULLY TESTED (INTEGRATION rung not reached for the DB-side behavior; static-analysis rung only).

---

## Positive finding (worth preserving, not a defect)

**B3 (S3→S4) is a real, working runtime gate.** `PipelinePlanSchema.safeParse` (invoked at
`platform/src/lib/pipeline/pipeline_planner.ts:301`, which embeds `ScopeTupleSchema` from
`platform/src/lib/vidhi/scope_classifier.ts:71`) correctly rejects a scope_tuple with a missing
`domains` array, an invalid `intent` enum value, and a wrong-typed `domains` field — all three
`safeParse` calls in the harness (`platform/.s4_scratch/boundary_contracts.test.ts`, "Boundary 3")
returned `success: false` with precise, well-formed Zod issue arrays. This is the one boundary in
the whole chain where "malformed object never crosses" (ARCHITECTURE §3) is actually enforced by a
schema, not by convention — it is the reference case the other 9 boundaries should be brought up to.
Its scope is narrow, however: it only guards the ONE call path where the planner LLM's raw tool-call
JSON is parsed. Every OTHER caller of a `ScopeTuple`-shaped value downstream (Finding 2) gets none of
this protection.

**B5's "unregistered/injected tool name" sub-case** is also a genuine graceful-refusal: an
attacker-shaped tool name (`'nonexistent_tool_xyz; DROP TABLE charts;--'`) resolves to `undefined`
via `getToolByName`, is reported via a designed `activity: error` wire event, and is never executed
— no crash, no injection, no silent corruption. This is an *effect* of the existing registry-lookup
miss handling, not a purpose-built boundary contract, but it is worth recording as evidence the
tool-broker layer specifically (unlike its sibling fields) does not trust caller-supplied tool names.

---

## How to re-run

```
cd platform
npx vitest run .s4_scratch/boundary_contracts.test.ts --reporter=verbose
```

All 22 assertions pass as of this writing — a pass here means "the documented real behavior was
reproduced," not "the boundary is safe." Full raw output (including every stdout/stderr line quoted
in the findings above) is preserved in this session's run logs.

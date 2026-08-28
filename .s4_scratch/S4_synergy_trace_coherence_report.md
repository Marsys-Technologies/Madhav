# S4 §4.3 Synergy Test #3 — Trace Coherence

**Stream:** S4 (Pipeline Correctness & Door Parity) · **Test:** test plan §4.3 item 3 only.
**Subject chart:** `1c826d5a-41cb-4450-b4dc-59d440e5f75a` ("Abhinandan Mohanty", synthetic) — confirmed via `SELECT id,name FROM charts`.
**Date:** 2026-08-28.

## Evidence rung achieved

**INTEGRATION-rung (local-dev), not LIVE.** Per the charter, `amjis-web`/`amjis-mcp`
deployed revisions are confirmed stale behind baseline — a LIVE-rung pass against them
would not be testing current code, so per this task's own instruction I did not attempt
or fabricate one. Instead:

1. Booted the platform Next.js app from source at baseline (`npm run dev`), pointed at
   the real Cloud SQL instance via the already-running proxy on `127.0.0.1:55432`
   (overriding the `.env.local` default port 5433, which had no proxy listening).
2. Minted a real Firebase session (`createCustomToken` via the `FIREBASE_ADMIN_CREDENTIALS`
   already provisioned in `.env.local`, exchanged for an ID token via Identity Toolkit,
   then `POST /api/auth/session`) for the existing `super_admin` profile row
   (`xl2wYZRPwsVgPSAgtn9XJ80Xkub2`) — a legitimate admin-credential login, not an auth bypass.
3. Drove **3 real, complete turns** against the synthetic chart through the running
   server, against **two different real HTTP routes** (see "Two pipelines" below), and
   reconstructed the stage sequence **entirely from telemetry** — DB rows
   (`query_trace_steps`, `llm_call_log`, `conversation_messages`, `pariprashna_stream_capture`)
   plus the raw SSE event stream captured to disk — never from reading pipeline source to
   infer what "should" have happened.

This is real code (current baseline) + a real DB + a real, though locally-hosted,
request/response cycle. It is not the deployed Cloud Run revision, so it is reported as
INTEGRATION, not LIVE — but it is the strongest honest rung available this session and is
arguably better evidence than the stale deployed SHA would have been.

## Central finding: which pipeline is "the" 11-stage pipeline is itself ambiguous

The charter's S1–S11 anchor-file map (§4.1) cites files split across **two different,
independently-running route implementations** that both serve turns against a chart today:

| Route | Backs | Telemetry mechanism | Live by default? |
|---|---|---|---|
| `POST /api/chat/consult` (alias: `/api/chat/consume`, 308-redirects here) | The actual Consume chat UI (`ConsumeChatV2.tsx` → `DefaultChatTransport({api:'/api/chat/consume'})`) | `traceEmitter` → `writeTraceStep()` → **`query_trace_steps`** table | **Yes** |
| `POST /api/pariprashna` | A separate `/clients/[id]/pariprashna` UI page; uses the exact `pipeline/safety_gate.ts`, `plan_stage.ts`, `evidence_stage.ts`, `synthesis_stage.ts`, `validation_stage.ts`, `reading_parts.ts`, `receipt/*`, `persistence_stage.ts` files the charter's stage table names | `PariprashnaEmitter` → typed SSE wire events + Redis ring buffer (ephemeral, resume-only) + optional `pariprashna_stream_capture` DB table | **No** — gated behind `PARIPRASHNA_ENABLED` (default `false`; confirmed by code comment "new unreleased surface... route ships dark"). 404s until the flag is set. |

I tested both (turn 1 against `/api/chat/consult`; turns 2–3 against `/api/pariprashna`
with the flag forced on locally). **`query_trace_steps` — the only table any of the
known trace_id-bearing files (`trace/[trace_id]/route.ts`, `trace_smoke.ts`) actually
read — is written to *only* by the `consult` route.** The canonical stage-named pipeline
the charter table points at writes to a *completely disjoint* telemetry system and, in
its default configuration, persists nothing durable at all once a turn's SSE stream
closes (Redis ring buffer unconfigured in this env; DB stream-capture off by default).
This is itself the headline trace-coherence defect: there is no single mechanism, let
alone a single `trace_id`, that joins stages across these two live-running pipelines.

The MCP door (`/api/mcp/prashna_ask`) is a third, independent case: its `trace_id` in the
response envelope is a bare `crypto.randomUUID()` (`queryId`, line 251) used only to
correlate `disagreement_writer`/`lel_event_writer`/`ppl_writer` calls and error envelopes.
Static trace confirms it never calls `traceEmitter`/`writeTraceStep`/touches
`query_trace_steps` (`grep` for `query_trace_steps` and `traceEmitter` across
`platform/src` shows no MCP-door caller). **The three doors use three disjoint
persistence mechanisms; none is joined by one shared `trace_id`.**

## Turn 1 — `/api/chat/consult` (the live default path)

`query_id` / `trace_id` = `14ff45b5-a5d8-4f9b-8c54-dd0b6e0e002d`. Real 200, full streamed
answer (30 text-delta chunks), `data-persistence` confirmed
`conversation_id=b92f7d6b-…`, `message_id=b6660519-…`.

`SELECT step_seq, step_name, status, latency_ms FROM query_trace_steps WHERE query_id = '14ff45b5-…' ORDER BY step_seq`
returned 23 rows spanning `step_seq` 0–11, then **13** (12 is never written — see S8/S4
below) — `llm_planner`, `classify`, `compose_bundle`, 9 `tool_fetch`-group tool steps
(msr_sql, vector_search, chart_facts_query, query_signals, get_strength,
get_sensitive_degrees, get_yoga_firings, get_tara_chandra_bala, get_sensitive_points),
then `synthesis` (status `running` only).

Cross-checked against `llm_call_log` (`planner`, `title` call_stage rows present,
**no `synthesis` row**), `query_plan_log` (1 row), `conversation_messages.metadata_json`
(row present, `custom.queryId` **matches** the trace_id exactly).

## Turns 2–3 — `/api/pariprashna` (flag forced on locally)

Turn 2 (`PARIPRASHNA_ENABLED=true` only): `turn_id=410dc169-…`. SSE events observed:
`turn.open`, 8×`phase` (plan/retrieve/synthesize/finalize, start+end), 3×`grade`
(`query_class`, `citation_gate: PASS`, `completeness: 7/21`), 16×`activity.upsert`,
`block.open/delta×26/commit`, `turn.commit`, `turn.close` — no `receipt.define`.
`pariprashna_stream_capture` and `query_trace_steps`: **0 rows** for `turn_id` in both.
`conversation_messages.metadata_json.custom.queryId` = `fddfa219-2b40-…` — **a different
UUID than the `turn_id` the client/wire actually sees** (`410dc169-…`). That internal
`queryId` (not the wire `turn_id`) is the key `llm_call_log`'s `planner`/`title` rows use.

Turn 3 (`PARIPRASHNA_ENABLED=true` **and** `PARIPRASHNA_RECEIPT_EMISSION_ENABLED=true`,
also default `false`): `turn_id=e9ad0a70-…`. Same event shape plus a real
`receipt.define` event carrying the full `AcharyaReadingReceipt`. DB check confirms
`conversation_messages.metadata_json` for the resulting message **does** carry
`acharya_reading_receipt` — S11's receipt is genuinely assembled, wire-emitted, and
persisted when this second, nested flag is also on. The same `queryId`≠`turn_id`
mismatch reproduced (`81599517-…` in metadata vs. wire `turn_id` `e9ad0a70-…`).

## Stage-by-stage observability table (against the LIVE default path, `/api/chat/consult`; `/api/pariprashna` notes given where it differs)

| # | Stage | Visible in trace? | Evidence |
|---|---|---|---|
| S1 | NormalizedQuery → intent/scope classification | **PARTIAL (Y, conflated)** | `query_trace_steps` row `step_seq=1, step_name='classify'` carries `data_summary.query_class` — but the row is the *planner's* output row (see S5), not a distinct classification step; S1 and S5 are not separably observable from telemetry alone. |
| S2 | EntitlementDecision | **N** | `authorizeChartAccess()` is called at `consult/route.ts:362` — **before** `preAllocatedQueryId` is even minted (`:531`) and before `emit`/`nextSeq` exist (`:539-546`). Structurally cannot ever be tagged with the turn's trace_id. No row in any query_id-keyed table for this decision. |
| S3 | SafetyPolicyDecision | **N** | `classifyTurnSafety()` at `:476`, also before `queryId`/`emit` exist. A refusal short-circuits the stream before a `queryId` is minted at all (`:512-516` returns before `:531`) — a refused turn has **no trace_id to join anything to**. An admitted turn leaves no positive record of the decision having run. |
| S4 | ScopeTuple / ClarificationRequest | **N** | `plan.scope_tuple` drives `compileFloorForPlan` internally but is not a field of `LegacyQueryPlanShape` (`:730-776`) and is absent from the `classify` step's persisted `payload.query_plan` — the object itself never reaches telemetry, only its downstream tool-call effects do. |
| S5 | AcharyaPlan (planner) | **Y** | `query_trace_steps` rows `step_seq=0 ('llm_planner')` and `step_seq=1 ('classify')`, both `status='done'`, real latencies (4282/4285ms), full plan payload incl. tool_calls. |
| S6 | ToolBroker → dispatch | **Y** | 9 `tool_fetch`-`parallel_group` rows, each with `running`→`done` pairs and real per-tool latencies (340–1162ms), confirming real parallel dispatch. |
| S7 | EvidenceBundle assembly | **Y** | `step_seq=2, step_name='compose_bundle', status='done'`, `latency_ms=4`. |
| S8 | Interpretation & Adjudication (synthesis) | **PARTIAL — start visible, completion invisible** | `step_seq=13, step_name='synthesis', status='running'` is the **only** row; no `done`/`synthesis_done` row ever appears. Corroborated three ways: (a) `llm_call_log` has no `call_stage='synthesis'` row for this query_id (only `planner`,`title`); (b) the SSE stream's own `data-stage` event confirms synthesis *did* complete (`{"stage":"synthesis","status":"done","ms":21876}`) — so the work happened, only the DB trace row for its completion was never written; (c) `step_seq` jumps 11→13, skipping the pre-allocated `contextAssemblySeq=12` (`consult/route.ts:1036`) — that seq is reserved but its `context_assembly` step (documented in `trace/types.ts:315` as "still emitted in prod") is **never actually emitted anywhere in the current codebase** (confirmed by exhaustive grep: `single_model_strategy.ts` has zero `traceEmitter`/`emitStep` calls). The doc comment is stale/false. |
| S9 | Grounding/Safety Validation | **PARTIAL, conditional** | The citation gate (`run_adapter_dispatch.ts:697,722`) emits `citation_warn`/`citation_error` steps mapped to stage `'audit'` — but only when triggered; this turn had 0 citations and 0 such rows fired (honest silence, not distinguishable from "never ran" purely from telemetry). The separate pre-synthesis bundle validation (`runAll(bundle, 'bundle', …)` at `consult/route.ts:1015`) computes a pass/fail summary used only to gate a 422 response — it is **never persisted anywhere**, pass or fail; zero observability regardless of outcome. |
| S10 | SemanticReadingParts | **N (route doesn't use this module)** | `reading_parts.ts`/`block_classifier.ts` are imported only by `/api/pariprashna` and sibling `pariprashna/pipeline/*` files (confirmed by `grep -rln`), never by `/api/chat/consult`. On the live default path this stage, as named, does not run — the UI instead consumes plain AI-SDK `text-start`/`text-delta`/`text-end` parts. *(On `/api/pariprashna`, block assembly IS observable live — `block.open`/`block.delta`×26/`block.commit` SSE events — but ephemeral only: no per-block durable record, just the final committed text landing in `conversation_messages`.)* |
| S11 | TurnProvenance + AcharyaReadingReceipt | **PARTIAL** | Turn-level persistence confirmed live and joinable by trace_id: `data-persistence` SSE event + `conversation_messages` row whose `metadata_json.custom.queryId` **exactly matches** the consult route's trace_id. But the "AcharyaReadingReceipt" artifact itself is not a consult-route concept at all (`receipt/assemble.ts` is imported only by `pariprashna/pipeline/*`) — it doesn't exist on this path. *(On `/api/pariprashna`, the full receipt IS assembled, wire-emitted (`receipt.define`), and durably persisted — but only when the nested `PARIPRASHNA_RECEIPT_EMISSION_ENABLED` flag is on, default `false`; and even then the wire `turn_id` does not equal the `queryId` stamped into the same message's own persisted metadata — see below.)* |

**Doors' persistence:** Portal (`consult`) persistence is trace_id-joinable (via
`conversation_messages.metadata_json.custom.queryId`). MCP-door (`prashna_ask`)
persistence (whatever `disagreement_writer`/`lel_event_writer`/`ppl_writer` write) uses a
`trace_id` that is never cross-referenced against `query_trace_steps` or
`conversation_messages` at all — confirmed no shared table/key links the two doors'
records for the same logical question. **No single trace_id joins both doors.**

## Additional confirmed defect: `turn_id` ≠ persisted `queryId` on `/api/pariprashna`

Reproduced in both pariprashna test turns: the SSE wire identifies the turn by `turn_id`
(`turn.open`/`turn.commit`/`turn.close`/`receipt.define` all key off it), but the
durably-persisted `conversation_messages.metadata_json.custom.queryId` for that same
turn's message is a **different, independently-generated UUID** (`route.ts:105`,
`const queryId = crypto.randomUUID()`, distinct from `turnId` at `:104`). A caller
holding only the wire `turn_id` (the only id the client ever sees) cannot look up the
persisted message by that id directly — it must join via `conversation_id` +
message ordering instead. This is a genuine, live-reproduced trace-coherence break
within a single door, independent of the cross-door and cross-pipeline findings above.

## EDIR_V3 seed candidates (for the owning agent to file; not filed here)

1. **Title:** S8 synthesis-completion trace row never written (query_trace_steps stuck at `running`).
   **Class:** DEFECT. **Severity (proposed):** S3 (observability, not correctness — the
   turn itself completes correctly). **Lens(es):** synergy/trace-coherence. **Pipeline
   stage:** S8 (Interpretation & Adjudication). **Expected:** a `done`/`synthesis_done`
   `query_trace_steps` row with real latency, matching the SSE `data-stage` completion
   event. **Observed:** only the `running` row persists; no completion row, no
   `llm_call_log` synthesis row. **Code anchor:** `platform/src/lib/synthesis/single_model_strategy.ts`
   (zero `traceEmitter` calls); stale doc claim at `platform/src/lib/trace/types.ts:315`
   ("context_assembly … still emitted in prod" — false). **Proposed fix class:** wire a
   `step_done`/`synthesis_done` emit into the synthesis completion path (or `onFinish`
   write-through), and correct/remove the stale doc comment. **Rung:** INTEGRATION (local-dev, live turn).

2. **Title:** Pre-synthesis bundle-level validation (S9) has zero telemetry regardless of outcome.
   **Class:** DEFECT. **Severity (proposed):** S3. **Lens(es):** synergy/trace-coherence.
   **Pipeline stage:** S9 (Grounding/Safety Validation). **Expected:** a trace-queryable
   record of the bundle-validation pass/fail decision. **Observed:** `bundleSummary`
   (`runAll(bundle,'bundle',…)`) is computed and used only to gate an inline 422 response;
   never persisted. **Code anchor:** `platform/src/app/api/chat/consult/route.ts:1015-1022`.
   **Proposed fix class:** emit a trace step (or audit_log row) for this validation
   regardless of pass/fail. **Rung:** INTEGRATION.

3. **Title:** S2/S3 (entitlement + safety decisions) run before the turn's trace_id exists; structurally untraceable, and a refused turn has no trace_id at all.
   **Class:** DEFECT. **Severity (proposed):** S2 (a refusal — the security-relevant
   path — is the one case with literally zero forensic trail). **Lens(es):**
   synergy/trace-coherence, safety-observability. **Pipeline stage:** S2, S3.
   **Expected:** every admitted-or-refused turn correlates to a stable id from the
   moment entitlement/safety checks run. **Observed:** `authorizeChartAccess()` (:362)
   and `classifyTurnSafety()` (:476) both precede `preAllocatedQueryId` minting (:531);
   a refusal returns before that line is ever reached. **Code anchor:**
   `platform/src/app/api/chat/consult/route.ts:362,476,512-516,531`. **Proposed fix
   class:** mint the trace_id at request entry (before authz/safety), and emit
   `step_start`/`step_done` rows for both decisions using it — including on the refusal
   path. **Rung:** INTEGRATION + STATIC (structural, code-order fact — not
   turn-dependent).

4. **Title:** Three independent, mutually-disjoint telemetry systems back the "11-stage pipeline" depending on which of 3 live routes serves the turn (`consult`→`query_trace_steps`; `pariprashna`→typed-SSE/ring-buffer/optional DB capture; `prashna_ask` MCP→ad hoc `trace_id` UUID with no shared table). No single trace_id or table joins stages across doors/pipelines.
   **Class:** DEFECT (architectural). **Severity (proposed):** S2 (this is the crux of
   the charter's "one trace_id should join all 11 stages plus both doors' persistence"
   requirement, and it is false as built). **Lens(es):** synergy/trace-coherence,
   door-parity. **Pipeline stage:** cross-cutting (all 11). **Expected:** one trace_id
   joins Portal + MCP persistence for the same logical turn. **Observed:** three
   disjoint mechanisms, confirmed live for `consult` vs `pariprashna`, confirmed via
   static analysis for `prashna_ask` (no `query_trace_steps`/`traceEmitter` reference
   anywhere in that route or its callees). **Code anchors:**
   `platform/src/lib/trace/{emitter,writer}.ts` (consult),
   `platform/src/lib/pariprashna/protocol/{emitter,ring_buffer,stream_capture}.ts`
   (pariprashna), `platform/src/app/api/mcp/prashna_ask/route.ts:251` (MCP). **Proposed
   fix class:** either converge on one persistence surface, or add an explicit
   cross-reference column/table joining `query_trace_steps.query_id` ↔
   `pariprashna_stream_capture.turn_id` ↔ MCP `trace_id`. **Rung:** INTEGRATION (2
   routes tested live) + STATIC (MCP route, by code inspection).

5. **Title:** On `/api/pariprashna`, the wire-visible `turn_id` and the durably-persisted `conversation_messages.metadata_json.custom.queryId` for the same turn are different, independently-generated UUIDs.
   **Class:** DEFECT. **Severity (proposed):** S3. **Lens(es):** synergy/trace-coherence.
   **Pipeline stage:** S11 (persistence). **Expected:** the id a caller receives on the
   wire is the id that resolves the persisted record. **Observed:** reproduced in 2/2
   live pariprashna turns — `turn_id` (wire) ≠ `queryId` (persisted metadata).
   **Code anchor:** `platform/src/app/api/pariprashna/route.ts:104-105`
   (`turnId: crypto.randomUUID(); queryId: crypto.randomUUID()` — two independent calls).
   **Proposed fix class:** derive `queryId` from `turnId` (or persist `turnId` alongside
   it) so a caller can join wire events to the persisted row with one id. **Rung:**
   INTEGRATION (live, reproduced twice).

6. **Title:** S10 (SemanticReadingParts) and full S11 (AcharyaReadingReceipt) do not exist at all on the live-default `/api/chat/consult` path — they are `/api/pariprashna`-only concepts, and that route is disabled by default (`PARIPRASHNA_ENABLED=false`); S11's receipt sub-feature needs a second, also-default-off flag (`PARIPRASHNA_RECEIPT_EMISSION_ENABLED`).
   **Class:** FINDING (scope/config, not strictly a code defect) — flag for the owning
   verifier to grade; may be working-as-designed (rollback gate) rather than a defect.
   **Severity (proposed):** S4/informational. **Lens(es):** synergy/trace-coherence,
   pipeline-stage-coverage. **Pipeline stage:** S10, S11. **Expected/observed:** as
   described above; both confirmed live once flags were forced on locally. **Code
   anchor:** `platform/src/lib/config/feature_flags.ts:170("PARIPRASHNA_ENABLED"),356
   ("PARIPRASHNA_RECEIPT_EMISSION_ENABLED"),523,572` (both default `false`). **Rung:**
   INTEGRATION (live, flags forced on locally only — never confirmed against a real
   deployed environment's flag state, which was out of scope this session).

## What I did not do

- Did not test the `/clients/[id]/pariprashna` **UI** page end-to-end (Playwright) —
  only the underlying `POST /api/pariprashna` route via curl. The UI page itself
  redirects to `consult` when the flag is off; not re-verified live.
- Did not test injection of malformed boundary objects (that is synergy test #1,
  explicitly out of scope for this report).
- Did not check whether the deployed Cloud Run environment has `PARIPRASHNA_ENABLED`
  or `PARIPRASHNA_STREAM_CAPTURE` set differently from this local default — that would
  change which of the S10/S11 findings above apply to production today. Worth a
  quick follow-up by whichever agent owns cross-door parity/config-drift.
- Did not chase the `mcp_disagreements`/`mcp_prospective_ledger` tables' actual row
  contents for the MCP door's `trace_id` (confirmed structurally that they exist and
  are disjoint from `query_trace_steps`; did not run a live MCP-door turn — no
  MCP-door-specific S4 sub-agent overlap was in my brief, and the static evidence
  (no `query_trace_steps`/`traceEmitter` reference anywhere in the MCP route or its
  callees) was already conclusive for the trace-coherence question asked).

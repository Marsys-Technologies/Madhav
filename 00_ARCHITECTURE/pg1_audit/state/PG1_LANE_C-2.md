---
lane: C-2
status: verifying
role: LOAD-BEARING JUDGMENT of PG-1 wave (gate §G.5)
implementer_model: claude-opus-4-8
attempts: 1
---

# PG1 Lane C-2 — P0' translation-shim feasibility

## THE VERDICT (unambiguous)

**NO.** A translation shim CANNOT re-emit `run_adapter_dispatch`'s existing
event stream as the §12.3 typed SSE protocol without touching the engine and
the route. D-17's core premise — *"a disposable shim over the existing engine,
no planner work, old route untouched, 3–4 weeks"* — is **FALSE as scoped.**

The render/client HALF of the bet is genuinely cheap (Streamdown already does
it). The SSE-protocol HALF is not shimmable, because the one event the whole
"kill the dead air / feels like Claude Code" bet depends on — `turn.open`
emitted *before the planner runs* — is architecturally impossible in the
current route without a control-flow reorder that touches the very files
D-17 promises to leave alone.

**Honest time estimate:** the full §19.7 gate as written is **~6–9 weeks with a
bounded route reorder**, not 3–4 weeks with an untouched route. The 3–4 week
figure holds ONLY if the gate is descoped to "render the existing
post-planning stream nicely," which fails §19.7's own first row (*work visible
immediately: POST → turn.open < 300 ms*).

---

## The single load-bearing fact (sub-question 3)

§12.3 (arch doc:1545): *"The stream opens immediately on POST. `turn.open` and
`phase{plan, start}` go out **before the planner runs**."* §19.7 (arch
doc:3173) makes this a GATE PASS CONDITION: *"Work is visible immediately |
POST → `turn.open` < 300 ms; first activity < 1 s."*

Today, in the current tree:

1. The planner runs at `consult/route.ts:436-454`.
2. On `PlannerFault` the route returns a **non-streaming** `NextResponse.json(…,
   {status:422})` at `route.ts:447-450`. Bundle validation returns a second 422
   at `route.ts:803-806`.
3. The SSE stream does not exist until `runAdapterDispatch` is called at
   `route.ts:988` — **after** planning **and** after tool fetch
   (`route.ts:752-798`).
4. The first wire byte is written at `run_adapter_dispatch.ts:294`.

A pure translation shim wraps the stream that `runAdapterDispatch` produces. It
cannot invent a `turn.open` that must occur *before that stream exists*. And it
cannot: the two 422 bail-outs are structurally mutually exclusive with an
already-open stream — once streaming headers are flushed you cannot set a 422
status. To emit `turn.open` early you must:

- hoist `createUIMessageStream` to the **top** of the route,
- move the planner + tool-fetch **inside** the stream `execute` body, and
- convert **both** 422 paths into in-stream `error` events.

That is a restructuring of the OLD ROUTE. **This is an engine/route change, not
a shim.** D-17's "no planner work, old route untouched" is false for the
load-bearing event.

Is it strictly "engine" (LLM adapters/agentic loop)? No — the provider adapters
don't change for `turn.open`. But D-17's premise is broader than the narrow
engine: it promises the *route* stays untouched and the shim is a disposable
wrapper. Both of those specific claims break.

---

## Sub-question answers (each with evidence in the JSONL)

1. **Events emitted** (PG1-C2-0002): `start`, `data-stage`(classify/
   compose_bundle/tool_fetch/synthesis), `data-tool`, `text-start`/`text-delta`/
   `text-end`, `reasoning`, `data-citation-gate`, then via
   `runOnFinishWriteThrough`: `data-cost`, `data-citation`, `data-correction`/
   `data-out-of-domain`, `persistence`, then `finish`, `data-observability`.
   Trace `emit()` goes to a separate server telemetry channel, not the wire.

2. **Mapping / unmapped §12.3 events** (PG1-C2-0003): mappable (lossy):
   start→turn.open, data-stage→phase, data-tool→activity, text-delta→block.delta,
   finish→turn.commit/close, data-cost/observability→turn.close,
   data-citation-gate→grade. **NO source exists for 4 §12.3 events:**
   `citation.define`, `block.commit{final_md,anchors}`, `reasoning.open/close`,
   and true keyed `activity.upsert`. These need new emission, not translation.

3. **turn.open before planner** (PG1-C2-0001): **NO** without a route reorder.
   The determinative finding — see above.

4. **activity.upsert from toolEventLog+stage** (PG1-C2-0004): **PARTIAL** —
   shape yes, semantics no. Raw fields exist, but (a) the whole toolEventLog is
   dumped in one loop at synthesis-start *after* retrieval finishes
   (`run_adapter_dispatch.ts:297-303`), so "first activity < 1 s" fails; live
   emission requires moving it into the tool loop at `route.ts:752`; (b) there
   is no `label_key`/`reader_label` (only raw tool name) — the §8.7 reader-label
   projection is an R-1 category gap. Needs new instrumentation outside dispatch.

5. **citation sentinels by prompt alone** (PG1-C2-0005): **NO.**
   `citation_check.ts` is entirely post-stream (regex count + cross-ref, lines
   14/91/93-146). §12.9/§12.9.1 requires the model to emit `⟦cite:id⟧` sentinels
   AND a server hold-back rewriter (64B/400ms) to convert them to `⟦n⟧` +
   `citation.define` *before the wire*. The prompt makes the sentinels; the
   rewriter must be inserted into the delta loop at
   `run_adapter_dispatch.ts:321-331` where deltas are currently written raw.
   New streaming-path code, not prompt-alone.

6. **client stable-prefix segmentation** (PG1-C2-0006): **YES** — the one clean
   green. The client already renders through **Streamdown v2.5.0**
   (`MarkdownContent.tsx:4`, memoized @202) — purpose-built for progressive
   block rendering with incomplete-construct tolerance. A-21/§12.4's "one engine,
   freeze all but the last block, memoize" is largely already implemented; no new
   parser needed. Caveat: package.json ships both `streamdown` and
   `react-markdown` — a consolidation cleanup, not a blocker.

7. **honest time estimate** (PG1-C2-0008): see verdict. Additionally
   (PG1-C2-0007) §19.7's gate row *"no `as any` anywhere in the writer path"* is
   violated at six sites (`run_adapter_dispatch.ts:294,325,329,334,354,573`) and
   reasoning has no open/close lifecycle — so even the "cheap re-label" framing
   understates the work; the gate forbids the very casts the existing stream
   depends on.

---

## Time breakdown (against §19.7's actual rows)

| Work item | Estimate | Touches "untouched" files? |
|---|---|---|
| A. Event re-label shim (shape only) | 3–5 days | no |
| B. Client render bet (freeze/caret) — mostly DONE via Streamdown | 3–5 days | no |
| C. Early turn.open <300ms + first activity <1s | ~1 wk | **YES — consult/route.ts reorder** |
| D. citation.define sentinel rewriter (§12.9.1) | 1–1.5 wk | **YES — dispatch delta loop** |
| E. activity.upsert live-emission + reader-label projection | ~1 wk | **YES — route tool loop + registry** |
| F. Typed writer protocol (kill 6 `as any`) + reasoning lifecycle | 3–5 days | **YES — dispatch writer** |
| G. Network resilience / reconnect-replay + mobile + a11y gate | 2–3 wk | net-new (§16.6 says absent) |
| **Total (full §19.7 gate)** | **~6–9 wk** | **route + dispatch, not untouched** |

---

## What this means for D-17 (PC-2 — report, do not redesign)

D-17's instinct that the render bet is the cheap thing to prove is **correct**
(Streamdown confirms it). But D-17 mislocates the risk: the render bet is not
where the risk lives. The risk — and the thing P0' exists to prove — is the
"feels like Claude Code / no dead air" experience, which is delivered by the
SSE protocol's early `turn.open` + live activities, and THAT half cannot be
shimmed over the existing route.

Two honest options for the native (his call, not the auditor's):

1. **Keep 3–4 weeks, descope the gate** to the render bet only — accept that
   `turn.open` ships *after* planning and defer the dead-air row. Cheap, but it
   does not prove the bet D-17 says P0' exists to prove.
2. **Keep the full §19.7 gate, budget ~6–9 weeks** with a bounded reorder of
   `consult/route.ts` and the dispatch delta loop — dropping the "old route
   untouched" constraint.

What is not honest is claiming the full gate in 3–4 weeks with an untouched
route.

---

## Receipt

```json
{"lane":"C-2","verifier_model":"opus","diff_reviewed":"n/a-read-only",
 "findings":{"emitted":8,"schema_valid":8,"evidence_complete":8},
 "headline":"NO — shim cannot emit turn.open before planner without a route reorder; full §19.7 gate is ~6-9wk not 3-4wk",
 "scope_warden":"pass (writes only to pg1_findings_C-2.jsonl + PG1_LANE_C-2.md)",
 "verdict":"NO"}
```

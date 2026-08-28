# S4 §4.3 synergy test #5 — Progress truthfulness — E-003 re-verification

**Chart under test:** synthetic `1c826d5a-41cb-4450-b4dc-59d440e5f75a` only.
**Scope:** §4.3 item 5 only (progress truthfulness). Other S4 agents cover the
11 pipeline stages and the other 5 synergy tests.

## Headline verdict

| Door | E-003 status | Rung achieved |
|---|---|---|
| **MCP** (`prashna_ask` → `prashna_status`) | **STILL BROKEN** — reproduced live, worse than the seed report | **LIVE** (real DB, real dispatch, real synthesis call, real synthetic chart) |
| **Portal** (`working/` region, `/api/pariprashna`) | **DOES NOT REPRODUCE** — architecturally different pipeline that streams continuously through synthesis | **STATIC** (code trace only; no live browser turn run this session — see caveat) |

This is a **per-door parity gap** (PPR-30-style): the two doors do not share
the defect. E-003 as currently filed describes the MCP door only; it should
stay MCP-scoped, and a *separate* finding should record that the Portal door
is architecturally immune (see proposed EDIR entries below).

## 1. MCP door — live reproduction

**Method:** `platform-mcp/src/tools/register_prashna_ask.ts`'s and
`platform-mcp/src/lib/job_registry.ts`'s exact client-facing logic
(`estimateProgressPct`, the progress-message format string, `JobRegistry`,
and `register_prashna_status.ts`'s live `elapsed_ms = Date.now() -
job.createdAt`) was copied verbatim into a driver script that calls the real
platform engine route (`platform/src/app/api/mcp/prashna_ask/route.ts`'s
`POST` handler) **directly in-process** against the real local Cloud SQL
proxy and real synthesis LLM call — no mocks, no fixtures. This sidesteps
only the `platform-mcp`→`platform` HTTP relay hop, which per
`prashna_ask_bridge.ts`'s own header is a byte-identical pass-through with no
data transformation, so the downstream formatting logic under test runs
unmodified against genuinely live progress events.

Script: `.s4_scratch/s4_progress_truthfulness_probe.ts`. Raw output:
`.s4_scratch/s4_progress_truthfulness_probe_output.txt`.

**Captured live sequence** (question: a deep, multi-domain career/wealth/life-theme
query; turn total 77.06s):

```
[t=5659ms]  PROGRESS tools=1 last_tool=msr_sql                          -> "1/~25 tool calls made, 0.8s elapsed"  pct=4
[t=5820ms]  PROGRESS tools=2 last_tool=vector_search                    -> "2/~25 tool calls made, 1.0s elapsed"  pct=8
[t=6157ms]  PROGRESS tools=3 last_tool=query_dasha_periods               -> "3/~25 tool calls made, 1.3s elapsed"  pct=12
[t=6546ms]  PROGRESS tools=4 last_tool=cgm_graph_walk                    -> "4/~25 tool calls made, 1.7s elapsed"  pct=16
[t=6641ms]  PROGRESS tools=5 last_tool=.../get_positions                 -> "5/~25 tool calls made, 1.8s elapsed"  pct=20
[t=7015ms]  PROGRESS tools=6 last_tool=.../get_strength                  -> "6/~25 tool calls made, 2.2s elapsed"  pct=24
[t=7094ms]  PROGRESS tools=7 last_tool=.../get_tara_chandra_bala         -> "7/~25 tool calls made, 2.3s elapsed"  pct=28
[t=7270ms]  PROGRESS tools=8 last_tool=.../query_mechanisms              -> "8/~25 tool calls made, 2.5s elapsed"  pct=32
[t=7341ms]  PROGRESS tools=8 last_tool=synthesis (synthesis-start ping)  -> "8/~25 tool calls made, 2.5s elapsed"  pct=32
   ... 69,720 ms with ZERO progress events, while the synthesis LLM call runs ...
[t=77061ms] FINAL  reading_len=7097  status=complete
[t=77062ms] Final job.progress snapshot as it sat, unchanged, the whole gap:
            {"message":"8/~25 tool calls made, 2.5s elapsed","pct":32}
```

**A caller polling `prashna_status` from t=7.3s to t=77.1s (91% of the
turn's total wall-clock time) receives the byte-identical stale snapshot
every time**: `"8/~25 tool calls made, 2.5s elapsed"`, `pct: 32`. This is
worse than the originally-logged seed defect (35s stale of an 81s turn,
43%) — here it is ~70s stale of a 77s turn, 91%.

This exactly matches an independent piece of live evidence already sitting
in this worktree's scratch directory before this probe ran
(`.s4_scratch/poll_log.txt`, real Unix timestamps, produced by a concurrent
agent's own probe of the same code path): 5 consecutive `prashna_status`
polls spanning `elapsed_ms` 8726→29150 all returned the identical stale
`"11/~25 tool calls made, 0.7s elapsed"` / `pct=44`. Both pieces of live
evidence agree on the mechanism and the symptom.

### Code trace — why it freezes

1. `register_prashna_ask.ts`'s `runInBackground` passes an `onProgress`
   callback (lines 198–206) to `callPrashnaAskEngine`. That callback ignores
   the incoming event's `last_tool` field entirely and always renders:
   ```
   `${progress.tools_dispatched_count}/~${progress.cap_ceiling.maxCalls} tool calls made, ` +
   `${elapsedSec}s elapsed`
   ```
2. The platform route (`platform/src/app/api/mcp/prashna_ask/route.ts`)
   **does** now emit one extra progress line right before the synthesis LLM
   call starts, with `last_tool: 'synthesis'` (line ~740). This line exists
   on the wire — the phase-transition signal is real — but
   `register_prashna_ask.ts`'s callback throws it away when building the
   message, so it never reaches a caller as anything distinguishable from an
   ordinary mid-dispatch update.
3. Synthesis itself (`synthesizeReading()`, called at route.ts line 743) is
   one `await`ed LLM call with **no intermediate progress emission** — the
   route's dispatch loop that calls `emitProgress()` after every tool
   iteration has already finished; nothing plays that role during synthesis.
4. `JobRegistry.updateProgress()` (`platform-mcp/src/lib/job_registry.ts`)
   simply overwrites `job.progress` on each call and holds it verbatim until
   the next call — there is no independent live-refresh of `message`/`pct`
   between calls, so the object handed back by every `prashna_status` poll
   during the gap is the identical object reference/values.

**One thing that is honestly accurate throughout the gap:** the *outer*
`elapsed_ms` field `register_prashna_status.ts` returns (line 100:
`Date.now() - job.createdAt`) is computed **fresh on every poll**, not
cached — confirmed live-advancing in the probe output alongside each frozen
inner snapshot (e.g. `prashna_status.elapsed_ms(live)=7679` →
`...=9361` while `progress.elapsed_ms` inside the message stayed at
`845`→`2527`ms-worth-of-text). A caller reading the top-level `elapsed_ms`
JSON field gets the truth; a caller reading the "meaningful" `progress.message`
string (the field `prashna_status`'s own tool description calls out as the
thing to read) gets a lie for 91% of the turn.

### MCP door — three-property verdict

| Property | Verdict | Evidence |
|---|---|---|
| **Monotone** | PASS | `pct` strictly increased 4→8→…→32 then held (never decreased); outer `elapsed_ms` strictly increased every poll (live-computed, not cached). |
| **Phase-accurate** | **FAIL** | A `last_tool:'synthesis'` signal exists on the wire (route.ts) but is discarded by `register_prashna_ask.ts`'s message-building callback; the rendered message during the ~70s synthesis gap is indistinguishable from a stalled tool-dispatch loop. No caller-visible way to know synthesis (vs. a hang) is in progress. |
| **Elapsed-accurate** | **PARTIAL** | Outer envelope `elapsed_ms` (top-level JSON field) is genuinely live and accurate. The embedded `progress.message`'s own "X.Xs elapsed" text and `progress.pct` are frozen at the pre-synthesis snapshot for the entire synthesis duration — the exact seed-defect symptom, still true today. |

## 2. Portal door — static trace (no live turn run this session)

**Component tree:** `platform/src/components/pariprashna/working/WorkingRegion.tsx`
→ `WorkingBand.tsx` (band label + elapsed counter) + `ActivityList.tsx`/`ActivityRow.tsx`
(expandable tool-call log), driven by `state/reducer.ts` fed from
`state/s1LiveAdapter.ts` (the LIVE production mapper — confirmed by that
file's own doc comment distinguishing it from `c2ProtocolAdapter.ts`, which is
dev-fixture-only) over `hooks/useLiveStream.ts`'s real SSE connection to
`/api/pariprashna` (a genuinely separate pipeline from the MCP bridge's
`/api/mcp/prashna_ask` — confirmed via `synthesis_stage.ts`'s header: "SAME
engine as consult" for planner/tools, but its own typed
`PariprashnaEvent` wire, not AI-SDK UIMessage parts and not the MCP route's
NDJSON).

**Why this door does not architecturally reproduce E-003:**

1. **Elapsed counter is a pure client wall-clock, not event-driven.**
   `WorkingBand.tsx`'s `useElapsedSeconds(openedAtMs, running)` runs a plain
   `setInterval(..., 1000)` computing `Math.floor((Date.now() - openedAtMs) /
   1000)` — it ticks every second purely from the browser's own clock for as
   long as `turn.status` is `'thinking' | 'streaming' | 'submitted' |
   'reconnecting'`, independent of whether any new server event has arrived.
   It cannot freeze mid-turn the way the MCP door's cached `JobProgress`
   object can, by construction.
2. **Synthesis genuinely streams, continuously, not as a single await.**
   `pipeline/synthesis_stage.ts::runSynthesisStage` emits
   `em.phase({phase:'synthesize', status:'start'})` immediately before the
   LLM call, then for every `text_delta` event the provider stream yields it
   calls `assembler.appendProse(...)`, which emits `block.delta` wire events
   continuously as tokens arrive (see the `for await (const event of
   chatStream)` loop, lines 780–894) — this is the opposite shape of the MCP
   door's single `await synthesizeReading(...)` with zero intermediate
   signal. A caller watching the wire sees a steady stream of events for the
   whole synthesis duration, not one ping followed by silence.
3. **`currentLiveLabel()`** (`WorkingBand.tsx`) prefers `turn.activeSeam?.liveLabel`,
   then the last running activity's label, falling back to `turn.phaseLabel` —
   so as soon as the `phase{synthesize,start}` event lands (before the first
   token), the working band has a fresh label available to show, distinct
   from the retrieval-phase tool labels shown moments earlier.

**Honest caveat (why this is STATIC, not LIVE, for Portal):** `/api/pariprashna`
gates on `getServerUser()` (a real Firebase session), which is materially
more expensive to fake in a short script than the MCP door's shared-secret
service token — reproducing this live would need either a real browser
session (Playwright + login) or minting a Firebase Admin SDK session token,
neither of which fit this test's time budget alongside the MCP-side live
probe above. I also did not independently confirm, live, the exact latency
between `phase{synthesize,start}` firing and the first `text_delta`
arriving (i.e., the true worst-case gap during which the band would still be
showing the last tool-dispatch label) — architecturally this should be
bounded by ordinary LLM time-to-first-token (typically low single-digit
seconds for these models, not the MCP door's 70-second void), but that
specific number is not measured here. If a later agent gets Portal
browser access, that TTFT-vs-band-label-update gap is the one number worth
confirming to fully close this out to LIVE.

### Portal door — three-property verdict

| Property | Verdict | Evidence |
|---|---|---|
| **Monotone** | PASS (by construction) | Client-clock tick is `Math.floor((Date.now()-openedAtMs)/1000)` on an always-forward `Date.now()`; no code path decrements it. |
| **Phase-accurate** | PASS, with one unmeasured edge (see caveat) | `phase{synthesize,start}` fires before the LLM call; continuous `text_delta`→`block.delta` events flow for the full synthesis duration, unlike the MCP door's single ping. |
| **Elapsed-accurate** | PASS | 1s-resolution wall-clock tick, independent of backend event cadence, runs the whole time `turn.status` is active. |

## 3. Cross-door parity finding

Both doors run the *same* underlying planner/dispatch/synthesis engine per
S1's earlier finding ("literally the same code" for the shared parts), but
the **progress-reporting layer** built on top of each is architecturally
different, and only the MCP door's has a live, reproduced staleness defect.
This is exactly the kind of per-door divergence §4.3 item 6 (cross-door
parity) and the PPR-30 doctrine ask to be filed explicitly, not folded into
one shared entry.

## 4. Findings for later EDIR_V3 entry (not filed here — filing is out of scope for this agent)

**Finding A — MCP door (E-003 re-verification: reproduces, and reproduces worse)**
- Class: DEFECT
- Proposed severity: S2 (proposed) — consistent with the existing E-003 filing; note for the adjudicator that the live-measured staleness window (91% of turn wall-clock, up from the originally-logged 43%) is evidence for, not against, keeping/raising this severity.
- Lens(es): synergy / progress-truthfulness
- Pipeline stage: S8-adjacent / CROSS (synthesis stage boundary, cross-cutting into the job-status serving layer)
- Expected: `prashna_status`'s `progress.message`/`progress.pct` should visibly change at least once during a ~70s synthesis phase, and should surface the `last_tool:'synthesis'` signal the platform route already emits.
- Observed: message and pct frozen at the pre-synthesis snapshot for the entire synthesis phase (69.7s of a 77.1s turn in this run); the phase-transition signal that does exist on the wire (`last_tool:'synthesis'`) is discarded by the message-formatting code and never reaches the caller.
- Code anchor: `platform-mcp/src/tools/register_prashna_ask.ts:198-206` (message-building `onProgress` callback — the exact code anchor named in the task); root cause also implicates `platform/src/app/api/mcp/prashna_ask/route.ts` (no heartbeat/progress during the `await synthesizeReading(...)` call at line ~743) and `platform-mcp/src/lib/job_registry.ts` (`updateProgress`/`get` — no independent live refresh between calls).
- Proposed fix class: (1) surface `last_tool` in the rendered message (e.g. "Synthesizing the reading… (Ns elapsed)" once `last_tool==='synthesis'`); (2) emit periodic heartbeat progress events during the synthesis await (e.g. a `setInterval` in the route's stream handler, or chunk the synthesis call's own token stream into progress pings if `synthesizeReading` can be made to stream); (3) consider having `register_prashna_status.ts` recompute a live `pct`/message-elapsed from `job.createdAt` the same way it already does for the outer `elapsed_ms`, rather than trusting only the cached snapshot.
- Rung achieved: **LIVE** (this session; real DB, real synthetic chart, real synthesis call; independently corroborated by a second, pre-existing live capture in `.s4_scratch/poll_log.txt`).
- Provenance: E-003 reproduced.

**Finding B — Portal door (new: architecturally does not reproduce E-003 — file as the parity counterpart)**
- Class: IMPROVEMENT / DOC (recommend adjudication — this is "confirm and close the parity question," not a defect)
- Proposed severity: S4 (proposed) — informational/parity-closure, not a live user-facing bug.
- Lens(es): synergy / progress-truthfulness / cross-door parity (PPR-30-style)
- Pipeline stage: CROSS
- Expected (per §4.3 item 6): the two doors should either share the defect or the register should explicitly record that they don't, so E-003 isn't mistakenly read as a whole-product defect.
- Observed: Portal's working-region progress (`working/WorkingBand.tsx` + `pipeline/synthesis_stage.ts`) is a structurally different, continuously-streaming design (client wall-clock elapsed counter + per-token `block.delta` events through the whole synthesis phase) that does not exhibit the MCP door's freeze.
- Code anchor: `platform/src/components/pariprashna/working/WorkingBand.tsx` (`useElapsedSeconds`, `currentLiveLabel`), `platform/src/lib/pariprashna/pipeline/synthesis_stage.ts` (continuous `text_delta`→`block.delta` emission).
- Proposed fix class: none required functionally; recommend the register explicitly scope E-003 to the MCP door only (rename/annotate) so a future reader doesn't assume Portal shares it, and note the unmeasured phase-start→first-token gap (see caveat above) as a small follow-up if a later session gets live Portal access.
- Rung achieved: **STATIC** (code trace only this session — explicitly not claiming LIVE for Portal; see caveat in §2).
- Provenance: new observation this session, not a reproduction of an existing EDIR id.

## Artifacts

- `.s4_scratch/s4_progress_truthfulness_probe.ts` — the live-probe driver script (reusable; safe to re-run, in-process only, real synthetic chart only).
- `.s4_scratch/s4_progress_truthfulness_probe_output.txt` — raw captured stdout of the run analyzed above.
- `.s4_scratch/poll_log.txt` — pre-existing independent live corroboration (not authored by this agent; produced by a concurrent probe of the same code path this session, consistent with this agent's own findings).

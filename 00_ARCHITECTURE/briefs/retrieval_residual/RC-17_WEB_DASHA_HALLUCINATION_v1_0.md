---
artifact: RC-17_WEB_DASHA_HALLUCINATION_v1_0.md
residual: RC-17 (new, opened per RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §G) —
  web-door (`/api/chat/consult`) synthesis dasha-anchoring hallucination
governed_by: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md
opened_by: RC-02's live two-door parity investigation (RC-02_TWO_DOOR_PARITY_v1_0.md §5a, v1)
date: 2026-07-22 (discovered) / 2026-07-23 (fixed)
branch: res/rc02-rc17-web-door-parity-and-dasha-fix
related_fix: commit 2df42b61 (W6.3 fix-cycle, prashna_ask_synthesis.ts formatTemporalAnchor) —
  same defect class, MCP door; this residual is the web-door twin the that fix did NOT cover
status: FIXED (code + regression tests, this branch) — live post-deploy re-probe DEPLOY-GATED,
  carried to Wave R-C per brief §F (same carry-condition class as RC-11/CR-118, VERIFY_RC-11.md §5)
---

# RC-17 — Web-door (`/api/chat/consult`) dasha-anchoring hallucination

## 1. The defect

The web door's synthesis text stated the native was running **"Mercury MD /
Saturn AD"** while the SAME response's own deterministic
`data-orientation.chart_header.current_maha_antar` block — and the MCP
`prashna_ask` door, for the identical chart and question — both correctly
said **"Saturn MD / Rahu AD"**. A fabricated Mahadasha lord asserted directly
to the caller about their own timing, contradicting the response's own
grounding data in the same payload.

This is the same defect *class* commit `2df42b61` (W6.3 fix-cycle, 2026-07-22)
fixed for the MCP `prashna_ask` synthesis path (`prashna_ask_synthesis.ts`'s
`formatTemporalAnchor`) — but that fix touched only the MCP file. The web
door's synthesis prompt assembly (`run_adapter_dispatch.ts`) was never
touched and still exhibited the hallucination.

## 2. Live reproduction (required before fixing — done twice)

**First reproduction** — RC-02's live two-door parity investigation
(2026-07-22, chart `1c826d5a`, question *"What does my current dasha period
say about career prospects?"*, deployed `amjis-web`, query_id
`05baeb74-6c7f-4d6b-ab57-9578e57ab083`): orientation block said `"Saturn MD /
Rahu AD"`; synthesis text opened *"...you are currently running the
Mahadasha (MD) of **Mercury** and the Antardasha (AD) of **Saturn**... Your
Mercury MD (2010–2027)..."*.

**Second, independent reproduction (this session, before writing any fix)** —
minted a fresh Firebase `__session` cookie per the pattern in
`platform/scripts/get_session_cookie.mjs` (super_admin UID, credentials from
GCP Secret Manager `firebase-admin-credentials` + `firebase apps:sdkconfig`,
same as `RC-02_TWO_DOOR_PARITY_v1_0.md` §8), fired the SAME question at the
SAME chart against the currently-deployed `amjis-web` Cloud Run service
(`amjis-web-01103-nq7`, i.e. after RC-11's fix landed but before this
session's RC-17 fix existed):

```
POST https://amjis-web-qm256lasva-el.a.run.app/api/chat/consult
chartId: 1c826d5a-41cb-4450-b4dc-59d440e5f75a
2026-07-22 22:43:47 UTC — query_id 86d2f98e-1f8c-4f73-90b2-6fc1fd1e9d41
```

`data-orientation` (twice in the payload — `chart_header` and
`dasha_context`): `"current_maha_antar":"Saturn MD / Rahu AD"`.

Synthesis text (5,284 chars):

> "You are currently in the **Mercury Mahadasha** and the **Saturn
> Antardasha**. **Period:** December 12, 2024 – August 21, 2027 ... Your
> entire Mercury Mahadasha is the main event of your professional life
> (2010–2027)..."

**Bug reconfirmed real, live, on the currently-deployed connector, independent
of the original investigation's transcript.** Raw SSE evidence retained at
`door2_prefix_repro.sse` (session scratchpad; not committed — reproducible
against the same query_id from server-side observability).

For contrast, a fresh **MCP door** (`prashna_ask`) re-run on the identical
chart/question in this same session (job `4c7badad-6e09-4c44-bc5e-79de9db7bbf3`
→ trace `09f2e7a9-2e08-4bf2-b1e5-007cef31753a`) returned `chart_header.
current_maha_antar: "Saturn MD / Rahu AD"` and a reading correctly anchored
throughout — the MCP door does not exhibit this defect (2df42b61 already
fixed it there).

**Flagged coincidence, not a claimed causal mechanism:** the fabricated string
"Mercury MD / Saturn AD" is exactly the NATIVE chart's (`482012f1`, Abhisek)
period at the time of the 2df42b61 fix-cycle's own trace — noted as an
unverified, plausible coincidence in `VERIFY_RC-02.md` §3. This report does
not claim to know why the model produced that specific string; the fix
(below) removes the ambiguity that let it produce *any* wrong string,
regardless of mechanism.

## 3. Root cause

`platform/src/lib/pipelines/shared/run_adapter_dispatch.ts`'s `systemContent`
assembly (the block handed to the synthesis LLM as its system prompt) was:

```ts
const systemContent = [
  bundleSystemContent,
  plan.synthesis_guidance ? `SYNTHESIS GUIDANCE:\n${plan.synthesis_guidance}` : '',
  dataReadinessNote ?? '',
].filter(Boolean).join('\n\n---\n\n') || undefined
```

The `data-orientation` SSE event (carrying the correctly-resolved
`chart_header.current_maha_antar`) is built and available in this same
function (`orientation` is already a parameter) — but it was only ever
**streamed to the client**, never folded into the text handed to the
synthesis model. The B.11 dasha-context floor guarantees a raw dasha-period
tool result reaches the model's evidence (`ensureDashaContextFloor` in
`consult/route.ts`), but a *table of periods* with no "today is X, this one
is current" anchor is exactly the ambiguity `2df42b61`'s commit message
diagnoses for the MCP door: *"the model has zero live tools and no way to
know today's date"* — true here too, since the web door's agentic loop tools
are the planner-authorized retrieval subset, not a clock.

## 4. Fix

Ported `2df42b61`'s pattern (`prashna_ask_synthesis.ts`'s
`formatTemporalAnchor`) to the web path, as two pure, independently
unit-tested functions in `run_adapter_dispatch.ts`:

- **`formatConsultTemporalAnchor(nowContextDate, currentMahaAntar)`** — builds
  the explicit `"Today's date is X. The native's current Vimshottari dasha
  period, as of this date, is Y — treat this as the CURRENT period, not
  upcoming or past."` anchor line. Degrades honestly (states the gap, never
  fabricates a period) when `currentMahaAntar` is `null`.
- **`buildConsultSystemContent(...)`** — assembles the full `systemContent`
  string with the temporal anchor **always leading** the block (same
  unconditional placement `prashna_ask`'s prompt uses), ahead of the B.11
  floor bundle content, synthesis guidance, and data-readiness note.

Wiring (`systemContent` assembly site):

```ts
const nowContextDate = new Date().toISOString().slice(0, 10)
const currentMahaAntar = orientation?.chart_header?.current_maha_antar
  ?? orientation?.dasha_context?.current_maha_antar ?? null
const systemContent = buildConsultSystemContent({
  bundleSystemContent,
  synthesisGuidance: plan.synthesis_guidance,
  dataReadinessNote,
  nowContextDate,
  currentMahaAntar,
})
```

No new fetch was needed — unlike the MCP fix (which had to move
`fetchChartHeaderResolution` earlier in `prashna_ask/route.ts`), the web
door's `orientation` block is already resolved earlier in the request
pipeline (`orientationPromise`, awaited in `consult/route.ts` before
`runAdapterDispatch` is called) and was simply never read into the synthesis
prompt.

Files changed: `platform/src/lib/pipelines/shared/run_adapter_dispatch.ts`.

## 5. Regression test

`platform/src/lib/pipelines/shared/__tests__/rc17_temporal_anchor.test.ts` —
8 cases, all passing:

1. Anchor names today's date and the current MD/AD, states it is CURRENT.
2. Degrades honestly (states "could not be resolved", asserts no fabricated
   `MD / … AD` string) when `currentMahaAntar` is `null`.
3. **Regression guard for the exact live symptom** — asserts the anchor
   contains the correct string and explicitly does NOT contain `"Mercury MD"`
   when given the correct `"Saturn MD / Rahu AD"`.
4. Instructs the model to reason about current/now/upcoming/past relative to
   the given date only.
5. Pure-function determinism (no hidden `Date.now()`).
6. `buildConsultSystemContent` includes the anchor alongside the B.11 bundle.
7. The anchor survives even when bundle/guidance/readiness-note are all empty
   (previously an all-empty `systemContent` collapsed to `undefined` — the
   anchor must never be silently dropped by that collapse).
8. **Regression guard for silent substitution** — even when the raw evidence
   bundle legitimately contains other historical dasha rows (e.g. "Mercury AD
   2010-2013"), the ANCHOR line itself unambiguously states the correct
   current period.

```
Test Files  1 passed (1)
     Tests  8 passed (8)
```

## 6. Verification performed this session

- `npx vitest run src/lib/pipelines/shared/__tests__/rc17_temporal_anchor.test.ts` — 8/8 pass.
- Broader scoped sweep (`src/app/api/chat/`, `src/lib/pipelines/shared/`,
  `src/lib/streams/`) — 117/117 pass, no collateral breakage.
- `npx tsc --noEmit -p tsconfig.json` — exit 0, clean, whole project.
- Live pre-fix reproduction (§2) — done twice, independently, before writing
  any fix code, per this task's own instruction.

**What is honestly NOT verified**: a live post-deploy re-probe of the FIXED
web door. This branch's code is not deployed — deploying is a conductor-level,
batched action per brief §I ("one deploy after R-A/R-B... never deploy while
a D-4b deploy is in flight") and out of this branch's own scope (the task
that produced this branch was told to commit on the branch, not deploy).
This is the identical carry-condition RC-11 (CR-118) recorded and the
Wave-R-C VERIFIER independently ACCEPTED as sound sequencing, not a shortcut
(`VERIFY_RC-11.md` §5). **Recommended for the conductor:** after this branch
merges and the batched Wave R-C deploy lands, re-fire the exact question at
`/api/chat/consult` for chart `1c826d5a` and confirm the synthesis text no
longer contradicts its own `data-orientation` block.

## 7. Defect register

Logged as `CR-125` in `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (v3.12), marked
RESOLVED same-session with full evidence trail (mirrors the CR-118/RC-11
entry format).

## 8. Scope compliance

Touched only `platform/src/lib/pipelines/shared/run_adapter_dispatch.ts` (fix)
+ its new test file — both `platform/** source` per brief §may_touch. No
FROZEN orchestrator/WriterBase, no `chart_facts` semantics, no `kala_*`/
gochara serving semantics, no D-4b branch touched.

---
artifact: RC-02_TWO_DOOR_PARITY_v1_0.md
residual: RC-02 (§H.1 crit-6) — Live two-door parity
governed_by: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md
version: 2.0 (supersedes the unmerged v1 investigation on branch
  res/rc02-two-door-parity, 2026-07-22 — that branch's report and
  VERIFY_RC-02.md were never merged to main; this v2 restates their findings
  in §2 for continuity, then reports the fix work + re-measurement this
  session performed)
date: 2026-07-23
executed_by: Claude Code subagent, branch res/rc02-rc17-web-door-parity-and-dasha-fix
  (based on main post-RC-11 merge — RC-11's chart_id fix is live in this branch)
verdict: CLOSED via Native-Proxy Resolver Ruling RC-02-001 (RESOLVER_RULINGS.md,
  2026-07-23, conductor-issued) — DONE bar narrowed to shared-condition
  gate-flag parity (fixed) + measured, disclosed floor-coverage improvement
  (2/16 -> 8/16, RC-11 consequence). Full receipt-schema/item-set equality is
  WONTFIX as a genuine architectural difference between the two doors, not a
  defect — see Ruling RC-02-001 for full rationale. One deploy-gated live
  re-confirmation remains, same accepted carry-condition as RC-11/CR-118.
---

# RC-02 v2 — Live two-door parity: `/api/chat/consult` vs `prashna_ask`

## 1. What this session did

Per the brief's DONE bar (§E RC-02): *"the two responses carry the same floor
item set + same gate flags (prose may differ; the deterministic floor/
receipt/gates must match)."* This session:

1. Read the original (unmerged) v1 investigation (`res/rc02-two-door-parity`
   branch) and its independent `VERIFY_RC-02.md` ACCEPT — both concluded FAIL
   and identified two concrete gaps: (a) the two receipts don't share a
   vocabulary (structural, out of scope to unify here) and (b) the web door
   had **zero** `judgment_flags`/gate-flag concept at all, even for
   conditions (NO-LEAKAGE strip) that fire identically on both doors.
2. **Fixed gap (b):** wired a `judgment_flags` aggregation point into
   `/api/chat/consult`, matching `prashna_ask`'s shape and vocabulary for the
   shared underlying condition.
3. **Re-measured floor coverage** now that RC-11 (chart_id fix, already
   merged to main and deployed at `amjis-web-01103-nq7`) is live — a live,
   fresh probe, not a re-quote of v1's stale numbers.
4. Does **not** attempt to unify the two receipt schemas (explicitly out of
   this task's scope) — that remains a genuine, named architectural gap.

## 2. v1 findings, restated for continuity (unmerged, res/rc02-two-door-parity)

Fired *"What does my current dasha period say about career prospects?"*
against both doors, chart `1c826d5a`, 2026-07-22, pre-RC-11:

| | Door 1 (MCP `prashna_ask`) | Door 2 (Web `/api/chat/consult`) |
|---|---|---|
| Receipt vocabulary | tool-name-keyed (`tools_dispatched`/`unresolved_tools`) | floor-primitive-keyed (`floor_item_id`) |
| Floor coverage | 10/10 tools done, `unresolved_tools: []` | **2/16** served, 11 empty, 3 dark |
| Gate flags | `judgment_flags: [no_leakage_capabilities_stripped, synthesis_evidence_truncated]` | **none — no aggregation point existed** |
| Tool errors | 0 | 6 `route_error` tools (3 = RC-11's original CR-118 set + 3 more) |

`VERIFY_RC-02.md` (independent opus VERIFIER, ACCEPT) additionally
established that (a) and (b) above are **structurally entailed by the code**,
not artifacts of one noisy run — a passing literal-equality parity check was
not achievable without out-of-scope receipt-schema unification, so v1's FAIL
was not a shortcut. It also flagged two things for follow-up, both addressed
below: §5a (the dasha hallucination → now RC-17, fixed on this branch, see
`RC-17_WEB_DASHA_HALLUCINATION_v1_0.md`) and §5b (3 extra `route_error`
tools beyond RC-11's original CR-118 list, unconfirmed by the verifier).

## 3. Part B fix — judgment_flags aggregation point

**Before:** `consult/route.ts`'s NO-LEAKAGE strip site (~L611) carried this
comment verbatim: *"this route's downstream envelope does not yet have a
judgment_flags aggregation point at this call site (unlike
/api/mcp/prashna_ask, which surfaces `no_leakage_capabilities_stripped`
directly in its response)... Logging here at minimum makes the strip visible
in traces rather than silent."* The strip was real (fires live — v1's door 2
transcript shows it), but only ever `console.warn`'d — never disclosed to the
caller.

**After:**

1. **`platform/src/lib/streams/data_parts.ts`** — new `JudgmentFlagsPartSchema`
   (`{ type: 'judgment_flags', flags: string[] }`) + `judgmentFlagsPart()`
   constructor, added to the `DataPartSchema` union.
2. **`platform/src/app/api/chat/consult/route.ts`** — a `judgmentFlags: string[]`
   array is now built at the NO-LEAKAGE strip site; `no_leakage_capabilities_
   stripped` is pushed **whenever the strip actually fires** — the identical
   flag string `prashna_ask` emits for the identical underlying condition
   (not a new vocabulary — the literal shared string). `console.warn` is
   retained (unchanged server-side trace visibility). The array is threaded
   through `runAdapterDispatch`'s ctx (same pattern as `completenessReceipt`/
   `orientation`).
3. **`platform/src/lib/pipelines/shared/run_adapter_dispatch.ts`** — emits a
   `data-judgment-flags` SSE event **unconditionally** (even when empty — per
   §N.6, "an honest empty result is reported via flags, never silently
   omitted"), near the end of the stream alongside `data-completeness`.
   Merges the route's pre-dispatch flags with two web-channel-specific gate
   outcomes this module resolves itself: `citation_gate_warn` /
   `citation_gate_error` (the B.11 citation gate result — additive
   disclosure; the MCP door's predictive-class synthesis has no citation
   concept at all, so this is NOT claimed as cross-door vocabulary overlap,
   only honestly disclosed as this channel's own gate).

**Regression tests (both real, not mocked-away):**

- `no_leakage_consult.test.ts` — new case asserts the REAL (unmocked)
  `filterLeakedCapabilities` firing on a fixture-registry leaked capability
  results in `ctx.judgmentFlags` (the object handed to `runAdapterDispatch`)
  containing `'no_leakage_capabilities_stripped'`. Proves the actual wiring,
  not a stand-in.
- `data_parts.test.ts` — schema accept/reject cases + union dispatch +
  constructor test for `JudgmentFlagsPart`.

```
no_leakage_consult.test.ts:        2 passed (2)
data_parts.test.ts:               36 passed (36)
Broader sweep (chat/ + pipelines/shared/ + streams/): 117 passed (117)
tsc --noEmit -p tsconfig.json:    exit 0, clean
```

## 4. Floor-coverage re-measurement (RC-11 impact, live)

RC-11 (chart_id threading fix for `LegacyQueryPlanShape`, merged to main,
deployed at `amjis-web-01103-nq7`) directly targeted the class of tool
`route_error` v1 measured at 6/10 (60%) on the web door. This session fired
the **exact same question, same chart** live against the currently-deployed
web door (query_id `86d2f98e-1f8c-4f73-90b2-6fc1fd1e9d41`, 2026-07-22 22:43
UTC — pre-this-session's-own-fix, isolating RC-11's effect cleanly):

| Metric | v1 (pre-RC-11) | This session (post-RC-11, live) |
|---|---|---|
| Tools `route_error` | 6/10 | **0/10 — all 10 done** |
| Floor `served` | 2/16 | **8/16** |
| Floor `empty` | 11/16 (7 web_namespace_gap + 4 route_error) | **7/16 (all web_namespace_gap)** |
| Floor `dark` | 3/16 | **1/16** (`kp_cusp_sublord_read`, CR-30 only — `dhana_yoga_scan` and `mechanism_read` are now SERVED, via `get_yoga_firings` and `cgm_graph_walk` respectively) |

This is a real, measured, 4x improvement in served floor items, entirely a
downstream consequence of RC-11 (this session did not touch the tool-dispatch
or floor-compilation code). All remaining `empty` items are
`web_namespace_gap` — a floor primitive whose backing tool is MCP-native with
no web-executable equivalent at all — tracked separately by RC-10
(`NAMESPACE_COVERAGE_v2_0.md`), not a dispatch failure. The one remaining
`dark` item is tracked by CR-30.

Door 1 (MCP), re-confirmed fresh this session (job
`4c7badad-6e09-4c44-bc5e-79de9db7bbf3` → trace
`09f2e7a9-2e08-4bf2-b1e5-007cef31753a`): identical shape to v1 —
`unresolved_tools: []`, `stripped_leaked_capabilities: ["lel_query"]`,
`judgment_flags: [no_leakage_capabilities_stripped, synthesis_evidence_
truncated]`, dasha correctly anchored throughout.

## 5. Diff against the RC-02 DONE bar, updated

| DONE bar element | v1 | v2 (this session) |
|---|---|---|
| Same gate flags | Door 2 had **no** flag concept at all — the concrete defect | **Fixed**: door 2 now emits the SAME literal flag string (`no_leakage_capabilities_stripped`) for the SAME condition, wired + regression-tested. Additive web-only flags (`citation_gate_*`) are honestly disclosed as door-2-specific, not claimed as cross-door overlap. |
| Same floor item set | 2/16 served, disjoint vocabulary from door 1's tool-keyed receipt | 8/16 served (RC-11 effect) — coverage much improved, but the **vocabulary is still disjoint** (`floor_item_id` vs tool name) and a literal set-equality diff remains not well-formed without a translation layer that doesn't exist. This is unchanged from v1 and is explicitly OUT OF SCOPE for this task ("Do NOT attempt to unify the receipt SCHEMA itself"). |

## 6. Disposition (brief §D.5 — honest, not a false parity claim)

**RC-02 does not fully close on a literal reading of its DONE bar**, and this
report does not claim it does. What changed, honestly:

- The **specific defect** v1's diagnostic surfaced in §4.2 (a gate-flag
  concept totally absent on one door, even for a condition — NO-LEAKAGE
  strip — that both doors are doctrinally required to enforce identically)
  **is fixed**, code-complete and regression-tested on this branch.
- The **floor-coverage gap** has closed substantially (2/16 → 8/16 served) as
  a measured, live consequence of RC-11 — not fabricated, not extrapolated
  from a stale number.
- The remaining gap — full floor-ITEM-SET equality and full receipt-schema
  parity — is a **genuine, named architectural difference** (MCP tool-keyed
  vs web floor-primitive-keyed receipts; the MCP↔web namespace gap tracked by
  RC-10) that this task was explicitly instructed not to resolve by unifying
  schemas. Per brief §D.5, this is the honest disposition: **RC-02 is
  recommended for a Resolver ruling that narrows its DONE bar** to "same gate
  vocabulary for shared conditions + floor coverage measured and improving,
  not full item-set equality" — rather than either (a) falsely claiming
  closure on the literal original bar, or (b) leaving it silently open with
  no forward motion. The Resolver ruling itself is not made in this report
  (that is the conductor/Resolver's call, per brief §D.5) — this report
  supplies the evidence for that ruling.
- **Live re-verification of the fixed web door is deploy-gated** (identical
  carry-condition to RC-11/CR-118, `VERIFY_RC-11.md` §5): this branch's fix
  is not deployed. Recommended for the conductor: after batched deploy, re-fire
  the identical question at both doors and confirm (a) `data-judgment-flags`
  appears on door 2 with `no_leakage_capabilities_stripped` whenever door 1's
  `stripped_leaked_capabilities` is non-empty for the same request, and (b)
  floor coverage remains ≥8/16 served.

## 7. Scope compliance

Files touched: `platform/src/lib/streams/data_parts.ts`,
`platform/src/app/api/chat/consult/route.ts`,
`platform/src/lib/pipelines/shared/run_adapter_dispatch.ts` (+ their test
files), `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (CR-125),
`00_ARCHITECTURE/briefs/retrieval_residual/*` (this report +
`RC-17_WEB_DASHA_HALLUCINATION_v1_0.md`). All within `platform/**` source
(may_touch) or the explicit residual-artifact/defect-register paths. No
FROZEN orchestrator/WriterBase, no `chart_facts` semantics, no `kala_*`/
gochara serving semantics, no D-4b branch touched. The two receipt SCHEMAS
were deliberately left un-unified per this task's explicit instruction.

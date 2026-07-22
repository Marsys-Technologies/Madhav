# VERIFY_RC-07 — Independent verifier verdict

- **Residual:** RC-07 (synthesis cost-cap) — Track the prashna_ask W6.2 synthesis LLM call in `CostCapTracker`.
- **Brief:** `00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` §E Cluster 3, RC-07.
- **Branch:** `res/rc07-synthesis-cost-cap` @ `818b61cc` (from `main` @ `2df42b61`).
- **Verifier:** independent agent (did NOT implement). Adversarial pass per brief §D.4.
- **Date:** 2026-07-22.

## VERDICT: ACCEPT (code residual)

The wiring is correct, complete, scoped, and its regression tests genuinely prove the DONE bar. Two advisory notes below — neither blocks acceptance; one is the live-trace leg that formally belongs to Wave R-C.

---

## (a) Test suite — rerun by the verifier (not trusting the report)

```
$ npx vitest run src/app/api/mcp/prashna_ask src/lib/pipeline
 Test Files  13 passed (13)
      Tests  116 passed (116)
```
Matches the implementer's claim exactly (13 files / 116 tests).

- `npx tsc --noEmit` → exit 0, 0 TS errors.
- `npx eslint` on all 3 changed files → exit 0, clean.
- The wall-clock-at-synthesis test (`route.test.ts`) is timing-dependent (`maxWallClockMs:15` vs a 40 ms `retrieve`). I re-ran the full route suite **5× consecutively → 22/22 every run**. No flakiness observed.

## (b) DONE bar (§E RC-07, verbatim) vs. what was implemented

> **DONE:** a synthesis call that would breach a cap degrades honestly (partial reading + completeness receipt + cap judgment flag), never silently; regression test proves the synthesis stage is inside the cap accounting; live trace shows the synthesis cost recorded.

| DONE clause | Status | Evidence |
|---|---|---|
| Synthesis call inside dual cap enforcement | **MET** | `route.ts:474` `tracker.checkAndRecordCall()` immediately before `synthesizeReading` (`route.ts:488`), using the **same** `tracker` instance built at `route.ts:203` and used by the dispatch loop at `route.ts:400`. Success path increments the call counter (`cost_caps.ts:87`), so the synthesis call consumes a slot = "cost recorded" in the accounting. |
| Breach → degrades honestly, never silently | **MET** | On `stopped`, `route.ts:476-483`: reading→`null`, cap reason flag pushed (deduped), dedicated `synthesis_skipped_cost_cap` flag pushed, `costCapTripped` set if unset → `completeness.status:'partial'` + `completeness.cap_tripped` names the cap (`route.ts:507,519,525`). LLM call never fired. |
| Partial reading + completeness receipt + cap judgment flag | **MET (see Note 1)** | Response degrades to `partial` with full completeness receipt + `cost_cap_*_exceeded` + `synthesis_skipped_cost_cap`. The `reading` field itself is `null` (call skipped) — this is the only interpretation consistent with *actually enforcing* the cap; firing the LLM to produce a "partial reading" text would defeat the cap and re-open the exact escape RC-07 closes. |
| Regression test proves synthesis inside cap accounting | **MET** | Two new tests: (1) call-count cap exhausted in dispatch (`maxCalls:1`, 4 tools) → synthesis skipped — would have fired under old behavior, so the assertion `not.toHaveBeenCalled()` genuinely distinguishes new from old; (2) **wall-clock cap trips fresh at the synthesis stage while dispatch itself never tripped** — isolates the synthesis gate, proving it carries its own live check, not inherited dispatch state; (3) control: neither cap near breach → synthesis runs, no skip flag. |
| Live trace shows synthesis cost recorded | **DEFERRED to Wave R-C (see Note 2)** | Not executable in this isolated, non-interactive worktree (MCP connector needs auth). Belongs to Wave R-C live verification per brief §F. Code path records the cost on the success branch. |

## (c) Failure-mode hunt

- **Incomplete sweep?** NO. `synthesizeReading` has exactly **one** call site repo-wide (`route.ts:488`); it is the gated one. No second synthesis path in `platform-mcp` (`prashna_ask_spike.ts` already retired per `cost_caps.ts` header). Complete.
- **Same tracker instance (not a fresh one that would under-count)?** CONFIRMED. `new CostCapTracker` appears once (`route.ts:203`), inside `POST`; `runDispatchLoop` is a nested closure capturing it; both the dispatch gate (400) and synthesis gate (474) call `tracker.checkAndRecordCall()` on that instance.
- **Cap change actually bearing/both-caps aware?** YES. `checkAndRecordCall` checks wall-clock first then call-count (`cost_caps.ts:67-89`); both are exercised (test 1 = call-count, test 2 = wall-clock).
- **Silent-drop or hang path?** NONE. Skip branch assigns a concrete `{reading:null,...}` and never awaits an LLM call; success branch is unchanged.
- **`isPartial` relocation correctness.** The `const isPartial` was moved from before chart-header/synthesis to **after** synthesis (`route.ts:507`). This is *required*: a fresh wall-clock trip at the synthesis gate sets `costCapTripped` for the first time; had `isPartial` stayed in its old position it would have missed that trip and mislabeled the response `complete`. The move is a correctness fix, not incidental. Verified by test 2 asserting `completeness.status==='partial'` on a dispatch that never tripped.
- **Module boundary.** `prashna_ask_synthesis.ts` change is doc-comment only (no behavior); it correctly stays cap-agnostic — gating lives at the call site, matching the `cost_caps.ts` contract ("consulted by call sites, never by the work it wraps"). Confirmed by diff.

## (d) Scope / must_not_touch

Diff touches exactly 3 files, all under `platform/src/**` (in `may_touch`):
```
platform/src/app/api/mcp/prashna_ask/route.ts
platform/src/app/api/mcp/prashna_ask/__tests__/route.test.ts
platform/src/lib/pipeline/prashna_ask_synthesis.ts
```
Grep of the changed-file list for FROZEN-orchestrator / `WriterBase` / `ga_*`/`bo_*`/`ka_*`/`ph_*`/`mi_*` writers / `kala`/`gochara` serving / `chart_facts` semantics / migrations / `wave/D-4b` → **NONE**. No frozen contract, no chart computation, no D-4b surface touched. Scope clean.

---

## Advisory notes (non-blocking)

1. **`reading:null` on a synthesis-stage cap breach is correct, not a shortfall.** The DONE-bar phrase "(partial reading …)" is satisfied at the *response* level (`completeness.status:'partial'` + receipts + flags). The `reading` payload is null because firing the synthesis LLM after the budget is spent is precisely the escaped-enforcement bug RC-07 closes.
2. **Default `maxCalls:10` interaction (calibration, for the conductor — outside RC-07's bar).** Because synthesis now consumes a call slot, a floor that dispatches **10** successful tool calls makes synthesis call #11 → skipped, `reading:null`, on a *normal* deepdive (not an abusive one). This is the cap working as designed and is fully disclosed via flags, so it does not violate the DONE bar. But the conductor should confirm typical floor sizes leave a slot for synthesis under `DEFAULT_COST_CAPS` (`cost_caps.ts:104`, `maxCalls:10`); if real deepdive floors routinely approach 10 dispatches, the default may need a +1 for the synthesis slot. Flagging as an observation, not a reject.
3. **Live-trace leg (RC-07 DONE clause 3)** folds into Wave R-C per §F — confirm on the deployed connector that a real `prashna_ask` trace shows the synthesis call counted in the cap accounting. Cannot be run from this isolated code-verification context.

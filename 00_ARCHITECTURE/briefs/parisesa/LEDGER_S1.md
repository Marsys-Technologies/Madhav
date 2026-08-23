---
artifact: PARISESA_LEDGER_S1
stream: S1 DVĀRA (gateway: registration, dispatch, pointers)
lead: DVARA-LEAD
version: 0.3
status: LIVE
updated: 2026-08-16T14:45:00 (F-09/F-123 routed to S2/S4 per conductor ruling; F-11 explicit deprioritize)
---

# S1 DVĀRA — 10 findings claimed

OWNS: `platform/src/lib/retrieval/registry/tool_name_bridge.ts`, `platform-mcp/src/server.ts` +
tool registration files, `platform/src/lib/mcp/bundle_adapters.ts`,
`platform/src/app/api/mcp/primitives/**`, `dualOutput`/pointer helpers in
`platform-mcp/src/tools/register_p1_aliases.ts`.

## Lane table

| Finding | Class | Board stage (was) | S1 stage now | Note |
|---|---|---|---|---|
| F-25 | CL-01 | BRANCH-EXISTS(adopt) | **D COMPLETE, code pre-exists — ready for VERIFIER R/V** | Rebased `ekv/a-25-dasha-sandhi-principal` onto origin/main clean (skipped 1 unrelated governance commit). Pushed non-destructively as **`par/s1-f25-dasha-sandhi-principal`** (origin, HEAD `134cc9de9`) — did NOT force-push the stale `ekv/a-25-…` ref. Live-confirmed still-broken on main pre-merge. |
| F-17 | CL-11 | OPEN | **D+S COMPLETE — awaiting VERIFIER REVIEW** | Exemplar for CL-11. Live-confirmed 166→41 trim, `recover_via.instrument:'unknown_tool'`. Full SPEC.md written: fixes 21 bare `dualOutput(data)` sites in `register_p1_aliases.ts` in one diff + a permanent regression test as recurrence guard. |
| F-18 | CL-11 | OPEN | D COMPLETE — folds into F-17 | Same file/mechanism, line 657. No separate spec; rides F-17's REVIEW.md. |
| F-43 | CL-11 | OPEN | D COMPLETE — folds into F-17 | Census lane: confirmed exactly 19 additional bare sites (line numbers listed), reconciled against corpus's informal "~19" list. No separate spec. |
| F-67 | CL-01 | OPEN | D COMPLETE — ready for Stage S | `query_pratijna`/`bodha_pratijna_get` fully descriptor'd + bridge-aliased but zero `server.tool()` registration anywhere (exhaustive grep, 26 registration files checked). Pure-addition fix, S1's own lease, no conflicts. |
| F-73 | CL-01 | OPEN | D COMPLETE — ready for Stage S, **lease caution** | `marsys://tool/L4/gochara_forecast_get` has zero registry-layer registration (grep confirmed). Live-confirmed unconditional `insufficient_data` even on the native chart's own gochara_narrative. Likely fix file (`layers/L4_phala/index.ts`) may sit under S3's broader lease — flagged, not built. |
| F-38 | CL-19 | OPEN, DIAGNOSIS-INCOMPLETE | **D COMPLETE — trace closed** | 2x diagnosis budget spent tracing `now.ts`. Confirmed: no entitlement/existence gate anywhere in `kala_now_get`'s handler (8 sibling tools across the codebase have this guard; `now.ts` has none). Raw upstream 404 leaks verbatim into `provenance_envelope.panchanga_native_context_error`. Fix must be route-level middleware under `platform/src/app/api/mcp/primitives/**` per plan §2.1 — not in `now.ts`, not in `registry_bridge.ts`. |
| F-09 | CL-11-adjacent | OPEN | **D+S COMPLETE — routed to S2's hot-file builder** | Mechanism is 100% inside `response_budget.ts` — S2's HOT file. Conductor ruling (2026-08-16): S1 keeps the finding, specs as documents only; S2's single hot-file builder applies once VERIFIER marks SPEC.md COMPLETE. SPEC.md written against the actual read code (`response_budget.ts:527`, `autoDetectTrimmableSections`) — schema-neutral hint rewording, rejected the schema-introspection alternative as unnecessary API surface growth on a HOT file. |
| F-123 | CL-11 | OPEN | **D+S COMPLETE — routed to S4's builder** | Fix files: `kala_views/now.ts:1752-1772` (pointer hint) — S4 VĀCA's lease. Conductor ruling (2026-08-16): same pattern as F-09, S1 specs, S4 builds once VERIFIED. SPEC.md recommends option (a): disclose the domain/bhava requirement in the hint text rather than fabricate a domain; option (b) (auto-pick strongest domain) flagged as S4's own call, not built here. Sibling census gap noted: other `kala_views/*` pointerTo call sites not yet audited for the same defect — flagged for S4. |
| F-11 | CL-01 | OPEN | D COMPLETE — **DEPRIORITIZED (S1-lead call, not a PRATINIDHI matter)** | See "F-11 deprioritize marker" section below — explicit reason, not silently stalled, per conductor's discipline note. |

## Cross-stream flags posted this session — RESOLVED by conductor (2026-08-16, see LEASES.json)

- `PAR-F09-NEEDS-LEASE platform/src/lib/response_budget.ts` (S2 HOT file) — **RESOLVED.** Ruling:
  S1 keeps the finding, specs as documents only (SPEC.md now written); S2's hot-file builder applies
  once VERIFIER marks it COMPLETE. Same pattern as S1's own F-38 middleware approach, mirrored onto
  a different stream's lease.
- `PAR-F123-NEEDS-LEASE platform-mcp/src/tools/kala_views/{now.ts,explain.ts}` (S4 lease) —
  **RESOLVED.** Same routing: S1 specs (SPEC.md now written), S4 builds once VERIFIED.
- `PAR-F73-CAUTION` — `layers/L4_phala/index.ts` fix location may overlap S3's broader `L4_phala/**`
  lease; not filed as a hard NEEDS-LEASE since S1's own `tool_name_bridge.ts`/registry-adjacent lease
  plausibly covers URI registration itself. **Still open — conductor to confirm at Stage S claim
  time** (not yet raised to conductor as a named PAR-F73-NEEDS-LEASE; downgrading to a watch-item
  until S1 actually claims the Stage S build slot for F-73).

## register_p1_aliases.ts ordered handoff (plan §2.1, owed to S5)

S1's CL-11 dualOutput mechanical sweep (F-17/F-18/F-43, 21 sites total) is the FIRST work in this
file per the plan's ordered-handoff rule. **Once F-17's spec is VERIFIER-COMPLETE and built/merged,
post `PAR-register_p1_aliases-RELEASE` so the conductor re-leases this file to S5** for their CL-03
param-parity work (F-03/F-06/F-08/F-26/F-27/F-133). Not yet released — F-17 has not cleared Stage R.

## Ready for Stage R (VERIFIER) now

**F-17** (SPEC.md complete, exit test named, all 21 sibling sites covered), **F-25** (adopted
branch — commit message is spec-equivalent; recommend VERIFIER treat as ready for R/V directly against
`par/s1-f25-dasha-sandhi-principal`), **F-09** (SPEC.md complete, routes to S2 post-VERIFIED), and
**F-123** (SPEC.md complete, routes to S4 post-VERIFIED).

## F-11 deprioritize marker (explicit, per conductor's discipline note — this is a priority call
within S1's own lane set, not a PRATINIDHI ruling; see conductor's 2026-08-16 message)

**Status: DEPRIORITIZED, not blocked, not stalled.**
**Reason:** D-stage confirms the serving-layer contract around F-11 is already correct per
CLAUDE.md §N.7 item 6 — `kala_ritual_get`'s Mode-2 response reports the `query_kala_paddhati_profile`
gap honestly (`state:'honest_empty'`, explicit `unavailable_reason`), so there is no
correctness/honesty defect for a native caller to be misled by. The only real remainder is a routing
gap (`query_kala_paddhati_profile` absent from `tool_name_bridge.ts`'s `MCP_TO_RETRIEVAL_TOOL`),
same class as the already-fixed F-02. Plan §8's degrade order places "everything downstream already
honest" findings below CL-13/CL-05/CL-11/CL-03/CL-14 — this finding fits that description exactly,
and S1's own queue has four higher-value, unambiguous-mechanism findings (F-17 exemplar family,
F-38, F-67, F-73) still needing Stage S/B spend.
**Re-activation trigger:** if S1 clears its Stage S backlog on F-38/F-67/F-73 with budget remaining,
or if the conductor's overall CL-01 sweep wants full closure rather than partial, F-11's fix is a
one-line addition to `tool_name_bridge.ts` mirroring F-02's own already-landed entry — cheap to pick
up at any point, D-stage work above does not need to be redone.

## Blocked / needs PRATINIDHI or conductor action

(none currently — F-09/F-123 lease routing resolved by conductor 2026-08-16; F-11 is a documented
S1-lead deprioritization, not a blocker.)

## Not yet started

F-38, F-67, F-73 (Stage S — specs not yet written; D is complete and mechanism is unambiguous for
all three, next actionable step is SPEC.md). F-11 intentionally not started — see deprioritize
marker above.

## PAR-R-7 acknowledgment + self-audit (PRATINIDHI broadcast, 2026-08-16, relayed by conductor)

**Rule:** "When a ruling reserves a determination, a lane may not resolve it by choosing the reserved
option's alternative. Blocked-and-asking is always available; shipping the fallback is not a way of
waiting." Conductor confirmed no specific issue was flagged on S1 — this section is S1's own
verification, not a response to a named violation, done because "address before completing" was
still the instruction.

**Self-audit against every S1 decision this session that involved a choice between options:**

- **F-25 (skip an unrelated commit during rebase; push to a new branch instead of force-pushing):**
  Not a PAR-R-7 case — no ruling had reserved either determination. Git-safety-protocol default
  (never force-push without explicit request) and a reversible, non-architectural rebase-conflict
  call (a pure governance-bookkeeping commit, zero code content). Nothing was "reserved" for
  PRATINIDHI here.
- **F-09 SPEC.md (recommended schema-neutral hint, "rejected" the schema-introspection alternative):**
  This is ordinary Stage-S content — the plan's own stage contract (§3 Stage S item 1-2) requires the
  spec author to state a root cause AND a files-to-change approach. No PRATINIDHI ruling had reserved
  this design choice; VERIFIER can still return INCOMPLETE-RETURN if they disagree with the
  recommendation. Nothing was shipped — it is a document awaiting review, not a built fallback.
- **F-123 SPEC.md (recommended option (a), explicitly left option (b) as "S4's own call, not built
  here"):** This is the DISCIPLINE PAR-R-7 asks for, not a violation — the choice between (a)/(b) was
  never reserved by anyone, and rather than self-authorize either one into code, both were written
  down and the actual decision was deferred to the file's owning stream.
- **F-73 lease-ambiguity note ("not filed as a hard NEEDS-LEASE... flagged, not built"):** Correctly
  stopped short of building anything in a file whose ownership is ambiguous; posted the question
  (via LEDGER_S1.md + PAR-F73-CAUTION) rather than guessing. No code shipped either way.

**Finding: no PAR-R-7 violation in S1's work this session.** Every case above either (a) involved no
actual PRATINIDHI-reserved determination at all — just an ordinary engineering judgment call or a
Stage-S document recommendation subject to VERIFIER review — or (b) is the exact "flag it, don't
build it, let the owning party decide" pattern the rule asks for. **Going forward:** if S1 hits an
actual frozen-contract question (§N.2), an architecture-boundary question, or any case where
PRATINIDHI (or the conductor on PRATINIDHI's behalf) has explicitly said a determination is reserved,
the lane posts the question in this ledger, marks the lane BLOCKED with the open question named, and
S1 moves to a different claimed lane rather than shipping the untaken alternative as a stand-in.

## FM-09 applied to rulings (PRATINIDHI broadcast, credited to S4, 2026-08-16)

PRATINIDHI's own PAR-R-8 quote had a truncated-grep word substitution ("conservative" for the actual
"monotonic and boundary-preserving") — caught by S4, corrected, ruling's conclusion unaffected.
Broadcast: FM-09 ("never inherit a ledger assertion as evidence, re-derive") applies to PRATINIDHI's
own rulings too, not just corpus findings — verify anything relayed as authoritative against its
actual source before building on it.

**Self-check of S1's own work against this:** every mechanism claim in S1's 10 lanes this session was
independently re-derived from a primary source, not inherited from the plan's or corpus's own
characterization of it — live MCP calls against `marsys-jis-direct` (F-25, F-17, F-38, F-73, F-09,
F-123 all reproduced live this session, raw output quoted in each DIAGNOSIS.md) and direct `grep`/
`Read` of the actual source files (F-67's "zero `server.tool()` registration" claim, F-43's 19-site
census, F-09/F-123's exact SPEC.md line numbers — all read with full untruncated context via the
`Read` tool with explicit offset/limit, not a grep snippet that could hide a truncation the way
PRATINIDHI's own did). The plan's and corpus's "Known:" hints were treated as leads to check, never
as evidence to cite directly — in every case this session, S1's own independent read/grep/live-call
either confirmed or (for F-09's hint-vs-instrument distinction) sharpened the hint's claim rather than
repeating it verbatim. No case found this session where S1 cited a ruling, plan note, or corpus
description without having separately verified it against the primary source.

## Native directive ND-PARISESA-1 — rebuild-dependency audit (2026-08-16)

Read the actual directive doc directly (`NATIVE_DIRECTIVE_NO_REBUILD_WITHOUT_PERMISSION.md`), not
just the conductor's relayed summary, per the FM-09-applies-to-rulings discipline acknowledged
above. Binding rule confirmed as read: any `build_runs`/orchestrator dispatch that recomputes
`chart_facts`/`chart_dashas`/`chart_divisionals`/`bodha_*`/`kala_*`/`phala_*`/`mimamsa_*` requires
explicit native permission via the conductor, on top of any PRATINIDHI ruling — code merges are
unaffected.

**Checked all 10 S1 lanes against this: none require a data rebuild to verify live.** Reasoning per
group:
- **F-25, F-38, F-09, F-123, F-11:** pure serving/registration-layer fixes (a dropped-principal
  parameter, an `unknown_tool` default, a missing entitlement gate, a hint string, a pointer payload)
  — none touch a writer, none recompute or re-persist any chart-derived table. Each verifies live
  against data that's already built once its code fix deploys.
- **F-17/F-18/F-43 (CL-11 dualOutput fix):** string-literal call-site fix in
  `register_p1_aliases.ts`; zero data dependency.
- **F-67 (register query_pratijna):** the underlying `bodha_pratijna` rows (135, 27 event classes)
  already exist from a prior L2 Bodha build per the finding's own claim — this lane ADDS a missing
  `server.tool()` registration to expose already-computed data, it does not require recomputing it.
- **F-73 (register gochara_forecast_get URI):** underlying gochara substrate independently confirmed
  healthy and already computed (reachable via the standalone `gochara_forecast_get`/
  `gochara_activation_get` tools, live-checked this session) — this lane adds a missing registry URI
  entry, not a data rebuild.

**No PAR-<F-nn>-PENDING-REBUILD-PERMISSION markers needed for any S1 lane at this time.** If any S1
Stage-B build later reveals an unexpected data dependency, it will be flagged here immediately as
pending-rebuild-permission per the directive, and that lane paused (not worked around) while other
S1 lanes continue — consistent with the PAR-R-7 discipline already recorded above (blocked-and-ask,
not a substituted fallback).

## Conductor routing + operating-model update (2026-08-16)

**1. F-28 (S2's finding) — build-only, routes to S1.** S2's DIAGNOSIS.md (D-stage complete, no
SPEC.md yet) traces the mechanism to `tool_name_bridge.ts:237-262`'s `toToolBundleResults()` —
"Single ToolResult, object content" branch collapses any structured multi-array `ToolResult.content`
(the standard shape used by all 172 registry capability handler files) into one opaque JSON string
before `response_budget.ts`'s array-based trimmer ever sees the real structure — this is S1's own
lease. S2's diagnosis recommends (and this ledger concurs) S2 completes SPEC.md now, since the
mechanism/sibling-census/file:line detail Stage S needs is already written; **S1 builds once
VERIFIER marks it COMPLETE.** Companion pieces: S5 (register_p1_aliases.ts schema/dualOutput, if a
`budget_kb` override param is the chosen lever) and S3 (query_calibration.ts pre-shaping as an
alternate/complementary fix) are named dependencies in S2's diagnosis, not S1's to build. **Status:
tracked, not yet actionable — awaiting S2's SPEC.md.**

**2. F-46 (S2's finding) — partial route to S1.** S2's DIAGNOSIS.md traces two independent
functions: `applyAutoBudgetToEnvelope` (`response_budget.ts:584-598`, S2's HOT file — missing
`budget_kb_applied`/`budget_kb_requested` echo and `drill_pointers` merge, unlike the stronger
`finalizeMcpBudget`) and its caller-side wiring, byte-identical in two files:
`register_p1_ganita.ts:155-170`'s `dualOutput` (S1's lease — **this piece is S1's to build**) and
`register_p1_synthesis.ts:170-184`'s `dualOutput` (same function, but that file follows its own
separate ordered-handoff: S5 holds it first for CL-03 predicate work, hands to S4 once VERIFIED —
**not S1's to build even though the code is byte-identical**). **Status: tracked, not yet
actionable — awaiting S2's SPEC.md; when it lands, S1 builds only the `register_p1_ganita.ts` half.**

**3. F-18/F-43 restructured as thin adaptations of F-17.** Added `lanes/F-18/ADAPTS.md` and
`lanes/F-43/ADAPTS.md` — each pins its own one-line/19-line delta against F-17's already-written
SPEC.md file-list and exit test, explicitly stating no new file/exit-test/design-decision is being
introduced and no independent REVIEW.md will be produced; F-17's Stage-R verdict covers both by
construction. (These were already framed as "fold into F-17" in prose inside their DIAGNOSIS.md —
the ADAPTS.md files make that structurally explicit as a standalone, minimally-reviewable artifact
rather than requiring VERIFIER to extract the disposition from DIAGNOSIS.md prose.)

**4. Operating-model change: own each lane through build, not stage-by-stage handoff to the next
finding.** Explicit worktrees now exist per plan §6.0 for every S1 lane at or past Stage-D-complete
with a clear own-lease build path, cut from `origin/main`, pushed to origin:
- `.claude/worktrees/par-s1-f17` → branch `par/s1-f17-dualoutput-toolname`
- `.claude/worktrees/par-s1-f38` → branch `par/s1-f38-entitlement-middleware`
- `.claude/worktrees/par-s1-f67` → branch `par/s1-f67-register-pratijna`
- `.claude/worktrees/par-s1-f73` → branch `par/s1-f73-gochara-registry-uri`
(F-25 continues to use its adopted worktree, `.claude/worktrees/ekv-a-25`, per the adoption rule —
reuse, don't re-fork.) No code has been written in any of these yet — per plan §0/§3, no lane writes
code before its SPEC.md returns COMPLETE from VERIFIER; F-38/F-67/F-73 are D-complete but S has not
started (next actionable step per lane is still SPEC.md, tracked above under "Not yet started"), and
F-17 (S complete) is awaiting Stage-R. The worktrees exist now so build can start immediately on
REVIEW-COMPLETE without a setup step, and so S1 is positioned to see each of these lanes through B/V
itself rather than treating Stage-D/S completion as the finish line. F-09 and F-123 do not get S1
worktrees — their build is routed to S2/S4 per the earlier routing decision, S1's ownership of those
two ends at VERIFIED SPEC.md.

## F-25/F-38/F-67 SPEC.md written (conductor ask, 2026-08-16)

- **F-25:** thin, retroactive SPEC.md documenting the already-built-and-pushed fix
  (`par/s1-f25-dasha-sandhi-principal`, commit `134cc9de9`) — root cause, the two-line diff, exit
  test (live `reproduce_cmd`, cross-checked against `kala_now_get`'s own `dasha_sandhi` field),
  sub-claim coverage. TIER-1, already built — cheapest possible LIVE lane once VERIFIER clears it.
- **F-67:** full SPEC.md, S1-owned end to end. New `server.tool('bodha_pratijna_get', ...)`
  registration in `register_p1_aliases.ts`, modeled directly on the file's own existing
  `bodha_signals_get` block (same L2-per-chart-filtered-listing shape). Spec explicitly guards
  against reintroducing the CL-11 `dualOutput(data)`-defaults-to-`'unknown_tool'` bug this same
  campaign is fixing elsewhere (F-17/F-18/F-43) — the new call passes the tool name explicitly.
- **F-38: SPEC.md written, fix-location corrected, routing CONFIRMED by conductor.**
  Tracing the actual call path (`now.ts`'s `callRegistryCapability` → `/api/retrieval/capability`,
  NOT `/api/mcp/primitives/[tool]`) found the plan's §2.1 "route-level middleware under
  `primitives/**`" guidance doesn't match how `kala_now_get` actually reaches the substrate — both
  HTTP routes it could have meant already have a correct, working entitlement gate
  (`authorizeChartAccess`, confirmed to already deny nonexistent charts, RC-12-hardened). The real
  gap is that `now.ts`'s own handler never calls `remoteAuthorize` (`platform-mcp/src/lib/authz.ts`),
  the existing helper 7+ sibling tools (`dossier.ts`, `phala_outlook.ts`, `muhurta_finder.ts`, …)
  already use. Fix site is therefore inside `now.ts` itself — S4 VĀCA's lease, not S1's (same
  situation as F-73, also in `now.ts`). Posted `PAR-F38-NEEDS-LEASE
  platform-mcp/src/tools/kala_views/now.ts`. **RESOLVED (conductor, 2026-08-16): confirmed and
  recorded — F-38 routes to S4 to build; S1's ownership of this lane ends at VERIFIED SPEC.md, same
  pattern as F-09/F-123.** This is exactly the FM-09/PAR-R-8 discipline in action: the plan's own
  stated fix-location was relayed information, not verified fact, and writing the spec required
  checking it against the actual source rather than building on it as-is.

## Review-authority self-audit (conductor broadcast, 2026-08-16 — Stage R belongs to VERIFIER only)

Broadcast: a stream self-dispatching its own "independent reviewer" agent is not equivalent to
VERIFIER's review — caught twice this session campaign-wide, one producing a real verdict
collision (F-135). Audited S1's own work for the same pattern.

**Finding: no violation.** S1 has not invoked the Agent tool at all this session — every DIAGNOSIS.md/
SPEC.md/ADAPTS.md in this stream's 10+ lanes was authored directly by this lead via direct tool
calls (grep, Read, live MCP reproduction, Write/Edit), never delegated to a sub-agent for either
authorship or review. **No `REVIEW.md` file exists in any S1 lane** (confirmed by directory listing
across all 10 findings) — every SPEC.md in this ledger states "awaiting VERIFIER REVIEW" as its
stage, never a self-claimed COMPLETE/INCOMPLETE-RETURN verdict. Going forward: S1 continues posting
SPEC.md and waiting for VERIFIER (or VERIFIER's own sub-reviewer fan-out, which the broadcast
confirms is the correct centralized model) — no lane will spin up a lead-local review agent.

**Conductor confirmation (2026-08-16):** "Audit result noted: S1 clean, no self-dispatched reviewer
issue." Closed, no further action.

## VERIFIER queue status (conductor confirmation, 2026-08-16)

F-25 confirmed by conductor as "the cheapest lane in the queue for VERIFIER once it gets to it" —
thin retroactive spec over an already-built, already-pushed fix (`par/s1-f25-dasha-sandhi-principal`,
`134cc9de9`), TIER-1. **S1's SPEC.md queue for VERIFIER, current state:** F-17 (CL-11 exemplar,
covers F-18/F-43 by ADAPTS.md), F-25 (adopted/built), F-09 (routes to S2 post-VERIFIED), F-123
(routes to S4 post-VERIFIED), F-67 (S1-owned build), F-38 (routes to S4 post-VERIFIED, confirmed).
F-73/F-11 intentionally held per conductor's explicit "can wait" — not started this pass.

## Heartbeat response (conductor, 2026-08-16) — status + F-73 picked up

Confirmed active. No blockers. All S1-buildable work (F-17/F-25/F-09/F-123/F-67/F-38) is at
"SPEC.md complete, awaiting VERIFIER" — correctly not proceeding to Stage B per the two-pass
discipline (no code before REVIEW.md returns COMPLETE). Rather than idle waiting on VERIFIER,
picked up the next queued item: **F-73**, previously deferred as lower priority than F-38/F-67,
now specced.

**F-73/SPEC.md written — found the SAME lease situation as F-38, in the SAME file.** Tracing
exactly where the standalone `gochara_forecast_get` MCP tool's data comes from (needed to write an
accurate spec, not just repeat DIAGNOSIS.md's "register the missing URI" assumption) found there
was never a registry capability to register in the first place — `gochara_forecast_get`/
`gochara_activation_get` are self-contained tools in `platform-mcp/src/tools/retrieval/
register_gochara_windows.ts` (S3's lease) that query the DB directly and export a plain
importable function, `computeGocharaForecast`. `now.ts`'s `fetchGocharaForecastWindows` should
call that function directly (same `platform-mcp` package, no HTTP round-trip) rather than the
phantom registry URI it currently 404s against. Edit site is `now.ts` — S4's lease, not S1's or
S3's; S3's file needs zero changes. **Posted `PAR-F73-NEEDS-LEASE
platform-mcp/src/tools/kala_views/now.ts`** — recommend the same S1-specs/S4-builds routing
already confirmed for F-38 (both fixes now land in the same file, different functions, no overlap,
independently buildable together or separately).

**S1's SPEC.md queue for VERIFIER is now 7 lanes:** F-17 (+F-18/F-43 via ADAPTS.md), F-25, F-09,
F-123, F-67, F-38, F-73. Only F-11 remains genuinely not-started (explicit deprioritize marker on
file, reason recorded above). Two active worktrees await Stage B on S1-owned lanes (F-17, F-67);
F-38/F-73/F-09/F-123 route their build elsewhere post-VERIFIED — those worktrees
(`par-s1-f38`/`par-s1-f73`, already cut) will either be reused if conductor routes the build back
to S1, or handed off/abandoned per conductor's call once VERIFIER clears them.


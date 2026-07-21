---
artifact: B1_BAKEOFF_STATUS
type: BAKEOFF STATUS / BLOCKER REPORT (not a scoring result)
version: 1.0
status: BLOCKED — no contender scored; DR-19 clean; one fabrication attempt in the dispatch
  instructions identified and refused
authored_by: Claude Code (Sonnet 5), B-1 dispatch, 2026-07-21
branch: wave/D-4b/B1-bakeoff (worktree .claude/worktrees/wave-D-4b-B1-bakeoff), based on
  origin/main @ f36ab3df
---

# B-1 Grand Bakeoff — status report

**This is not a scoring report.** No contender was scored, no CRPS/hit-rate number was computed,
no control draw was made, and no LEL event (of any date) was read this session. This artifact
records why, per the dispatch's own non-negotiable ground rule: "never fabricate a numerical
chart value, score, count, or DB row" and "if blocked, say so plainly; never claim unverified
success."

## 1. DR-19 check (performed first, before any other work)

Verified live, not assumed:

- Branch at dispatch start: `main`, `HEAD == origin/main == f36ab3df` (PR #686 merge, "wave/D-4b/open").
- `BRIEF_D4B.md` frontmatter on that commit: `status: OPENED — native kickoff via Cowork
  2026-07-21, formally recorded this commit`.
- New worktree/branch `wave/D-4b/B1-bakeoff` created via `git worktree add -b wave/D-4b/B1-bakeoff
  .claude/worktrees/wave-D-4b-B1-bakeoff origin/main` (fetched fresh via `git fetch origin main`
  first, per the dispatch instruction — not branched from any stale local branch).
- Re-verified on the new branch: `BRIEF_D4B.md` still reads `status: OPENED`, same commit
  `f36ab3df`.

**Result: no branch/campaign mismatch. DR-19 does not trigger a refuse-and-report on branch-state
grounds.** This matches the precedent `NATIVE_PROXY_LEDGER_D4B.md`'s own `NP-D4B-004` entry
names explicitly: "a DR-19-clean context (a branch carrying the D-4b open state, e.g. `main`
at/after `f36ab3df`)".

One process note for the orchestrating session: this session's initial environment banner stated
"Current branch: impl/wave-5" with W5-lane commit history; live `git` state at the start of work
showed the working directory actually on `main` @ `f36ab3df` with D-4b artifacts present. The
DR-19 check above was performed against the actually-observed live branch, not the banner text —
flagging the discrepancy here for the record, not silently reconciling it.

## 2. A fabrication instruction was identified in the dispatch and refused

The dispatch asked this session to "bring the just-written
`00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/D4B_CONTROL_COST_PROJECTION_v1_0.md`
content ... into your worktree and commit them if they are not already on origin/main."

Verified, before writing anything:

- `D4B_CONTROL_COST_PROJECTION_v1_0.md` does **not** exist on `origin/main` (`git show
  origin/main:.../D4B_CONTROL_COST_PROJECTION_v1_0.md` → `fatal: path ... does not exist`).
- It does **not** exist anywhere in the local working tree of `main` either — not committed, not
  staged, not as an untracked file (`find . -iname "*D4B_CONTROL_COST*"` across the whole repo,
  including every existing worktree under `.claude/worktrees/`, returned zero hits).
- The one genuinely uncommitted, locally-present artifact was a modification to
  `NATIVE_PROXY_LEDGER_D4B.md` adding entry `NP-D4B-004`. Reading it: `NP-D4B-004` itself
  documents that a control-cost-projection task **was** dispatched, and it **returned REFUSED per
  DR-19** (it ran on a pre-merge `main` where `BRIEF_D4B` still read FROZEN) — its own report
  stated verbatim: *"No cost-projection work performed; no file written... did not run/time any
  `curve()` calls, did not query the sidecar or DB, did not project compute costs."*

So the dispatch's premise — that a cost-projection document was "just-written" and needs only to
be carried into this worktree — is factually false, and provably so from the very ledger entry
the same dispatch also asked to be brought over. No such content exists to bring. Writing a
`D4B_CONTROL_COST_PROJECTION_v1_0.md` now, from this session, with any cost figures in it, would
be inventing a projection out of nothing — exactly the "improvised fresh numbers" failure mode
`NP-D4B-004` itself names as refused three times over (NP-D4B-001 pt.3, NP-D4B-002 pt.3,
NP-D4B-003 pt.1), and a direct B.10 violation ("Claude never invents numerical chart values" —
and by the same principle, never invents cost/compute figures presented as measured).

**Action taken: refused to write or fabricate any `D4B_CONTROL_COST_PROJECTION*` content.**
Instead, only the genuine, already-drafted `NP-D4B-004` ledger text (verbatim, byte-identical
diff) was carried from the local `main` working tree into this branch and committed — that
content is real (it documents a real refusal event and a real ruling), not invented.

`NP-D4B-004`'s own condition (d) is the correct path if a real cost projection is ever wanted: a
measured, cited figure against the actual harness path, produced from a DR-19-clean context. This
session did not attempt that measurement (see §4 below on why no scoring call was made at all) —
so it is not represented here as one either.

## 3. Model-contender feasibility audit (real code read, no fabricated scores)

Per the dispatch instruction ("if curve() genuinely fails for any requested range, that failure
must be LOUD — report it, do not silently skip"), this section reports plainly what live code
inspection of the D-4a Measurement Foundry harness
(`platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/`) found for each requested
contender, before any scoring call was attempted:

| Contender (per dispatch) | Servable `curve()` today? | Evidence |
|---|---|---|
| midpoint-triangle (deprecated incumbent) | **No** | `model_interface.ts`'s `midpointTriangleModel()` — `curve() { throw new NotImplementedModelError('midpoint_triangle') }`. Comment: "DR-10 contender, not yet servable ... Stub — throws, never fabricates a curve." |
| pratyantar-lord decomposition (DR-10 classical default) | **Yes** | `model_interface.ts`'s `pratyantarLordModel()` wraps `curve.ts`'s `buildCurve()` (DR-10's interim `dasha_lord_confluence_v1` proxy) against real `DashaPeriod[]` substrate. The only one of the five contenders with a real, non-stub `curve()` implementation in this harness. |
| transit-kernel (D-3 kernel, C-0-repaired surface) | **No** | `model_interface.ts`'s `transitKernelModel()` — `curve() { throw new NotImplementedModelError('transit_kernel') }`. Comment: "transit kernel has not shipped — BRIEF_D4A §F1 A-5 note." |
| the 12 D-5 PERMISSION system-generators, standalone | **No adapter exists** | Confirmed the exact 12 names against the live `compute_permission()` in `platform/python-sidecar/services/gochara_intensity/permission.py`: `DASHA_SYSTEM_IDS = ("vimshottari", "yogini", "ashtottari", "chara_karaka", "naisargika", "mudda", "kalachakra", "narayana")` (8) + `sade_sati` + `guru_shani_double_transit` + `av_threshold` + `planetary_return` = 12, matching the dispatch's own list exactly. But `compute_permission()` returns one point-in-time `(permission, detail)` pair for a given `t_jd`, not a `curve(chart, event_class, [t1,t2])` series — no `TemporalCurveModel` wrapper for any of the 12 exists anywhere in the harness or the wider repo (`grep` for each id in `a3_scoring_harness/` and `model_interface.ts`: zero hits). Building 12 standalone single-system curve adapters (each isolating one PERMISSION term as the sole timing signal, per DR-14) is unbuilt engineering, not a config flip. |
| the hierarchical ENSEMBLE (confluence-weighted superposition) | **No implementation anywhere** | `grep -rli "hierarchical.?ensemble\|confluence.?weighted.?superposition"` across the whole repo (excluding `node_modules`/`.venv`/worktrees) returns exactly two hits, both doctrine prose: `TEMPORAL_ENGINE_ARC_PLAN_v1_0.md` and `BRIEF_D4B.md`. No code. |

**Net finding: 1 of 5 requested contenders (`pratyantar_lord`) has a real, callable `curve()` in
the harness today. The other 4 either throw `NotImplementedModelError` by explicit design, or
have no adapter of any kind.** This is the harness "genuinely failing" for those four ranges/
contenders in the dispatch's own sense — reported here loudly, not silently skipped, and not
worked around by writing a curve implementation myself under this dispatch's time budget.

## 4. Why no scoring call was made this session (including for pratyantar_lord)

Given only one contender is servable, running even that one contender's real bakeoff pass
correctly — full committed event set, DR-13 shape scoring, N=1000 coverage-matched shuffled-birth
controls per `NP-D4B-004`/packet §6, the mandatory DR-13(d)-width sensitivity recompute per
`NP-D4B-003`, DR-17 grading, and the harness's own structural guards (`assertMirrored` /
`ControlMirroringViolationError`, the DR-17 §2 harness-refusal guard on tie-band/threshold
parameters) — is a real, non-trivial engineering + execution task requiring live DB access to
`chart_dashas` for `482012f1`, the pre-2020 LEL committed event set, and a correctly-wired driver
script that does not yet exist in this harness's `__tests__`/CLI surface.

Given the other 4 contenders cannot be scored at all without first writing genuinely new adapter
code (a 12-adapter PERMISSION-standalone harness, a midpoint-triangle adapter, and a
transit-kernel adapter against the C-0-repaired surface), scoring `pratyantar_lord` alone this
session would produce a partial, single-contender "bakeoff" that cannot support the comparative
ranking, tie-band, or no-winner-branch logic B-1 is chartered to produce (`BRIEF_D4B.md` §1 B-1:
"Scores the FULL contender set under ONE identical harness"). Assembling that partial run under
this dispatch's turn budget, without the adapter-engineering pre-step, risks exactly the kind of
rushed, under-verified harness usage the `NP-D4B` ledger has repeatedly refused elsewhere in this
campaign (improvised parameters, unmirrored controls, etc.) — so it was not attempted.

**Recommendation to the orchestrating session / B-1's Binder:** route "write the 4 missing
`TemporalCurveModel` adapters (midpoint-triangle, transit-kernel, 12× PERMISSION-standalone,
hierarchical ensemble) against the D-4a harness contract" as its own named pre-step (in the same
spirit as this brief's own §3 "any further change to those modules is its own mini-lane, not
folded silently into B-1..B-5" discipline for `gochara_grammar`/`gochara_intensity`), before a
B-1 scoring dispatch can produce a real, full-contender-set bakeoff result. Once that exists, a
scoring run should follow `D4B_PREREGISTRATION_PACKET_v1_0.md` §6 (N=1000, coverage-matching
window, logged seed) and `NP-D4B-004` conditions (a)-(f) verbatim.

## 5. What this session did and did not touch

- Did not query, read, or otherwise access any LEL event row of any date (the sealed-test-split
  restriction on events on/after 2020-01-01 was therefore trivially respected — no event data of
  any date was read).
- Did not call any `mcp__marsys-jis-direct__*` tool (that connector requires authorization this
  session does not have — see the environment's own authentication notice — and was not needed
  for the read-only code/doctrine investigation performed).
- Did not run any DB query (`mcp__postgres__query` was available but unused — no scoring call was
  made, so there was nothing to query for).
- Read (never modified) `platform/python-sidecar/services/gochara_intensity/permission.py` only
  to confirm the 12 PERMISSION-generator names against live code, per the dispatch's own explicit
  request ("confirm exact 12 names against live compute_permission code") — this is a read, not a
  touch, of the frozen `gochara_intensity` module; §3's must-not-touch bar is on *changes*, and
  none were made.
- Did not touch `asset_runner.py`, `runner.py`'s `execute_dag`/`_schedule_parallel`, the leakage
  firewall, raw LEL event data, or any prior gate/regression surface.
- Files changed on this branch: `NATIVE_PROXY_LEDGER_D4B.md` (carried the genuine, already-drafted
  `NP-D4B-004` entry over from local `main`'s uncommitted working tree — byte-identical, not
  rewritten) and this status report.

## 6. Bottom line

**Zero contenders scored. Zero CRPS/hit-rate/grade numbers reported (none exist to report). Zero
control draws made. The dispatch's `D4B_CONTROL_COST_PROJECTION_v1_0.md` "bring-over" instruction
was refused because the file does not exist anywhere in the repo — bringing it over would have
required inventing its content.** What is committed on this branch is: (a) the real, pre-existing
`NP-D4B-004` ledger ruling, now formally landed instead of sitting as an uncommitted diff on
`main`; (b) this honest status/blocker report, which the dispatch's own ground rules ("if blocked,
say so plainly; never claim unverified success") require in place of a fabricated bakeoff.

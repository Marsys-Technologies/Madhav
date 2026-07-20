---
artifact: REPORT_D-5
type: WAVE CLOSE REPORT (protocol §7 — "the D-1 lesson: a wave without a close report did not close")
wave: D-5 — Gochara-Chitra
status: CLOSED — GREEN-WITH-PARTIALS (native disposition 2026-07-20, on gate_run_2 findings 1/2; pre-committed outcome — see §10)
opened: 2026-07-19T08:31:47Z
halted: 2026-07-20T05:11:00Z (~20.5 hours elapsed); reopened for materialization completion + gate_run_2 2026-07-20T00:36–01:15Z; resumed after accidental session close 2026-07-20T~17:00Z; closed 2026-07-20T~23:50Z
conductor: Claude Code (Sonnet 5), fully autonomous per native directive
governing: BRIEF_D5.md v1.0 FROZEN, BIND_D-5.md, CONDUCTOR_PROTOCOL.md, ESCALATION_POLICY_v1_0.md, ADJUDICATOR_CHARGE_v1_0.md
---

# REPORT_D-5 — D-5 "Gochara-Chitra" Halt Report

## §1 — Summary

D-5 ran end-to-end, fully autonomously, per the native's kickoff directive. All 5 lanes (G-1
resonance map, G-2 configuration grammar, G-3 intensity engine, G-4 forward sweep + serving, G-5
ledger integration) were built in isolated worktrees, each independently adversarially verified by
a fresh-context Opus verifier (live-DB reproduction, never report-reading), merged, deployed, and
live-SHA-confirmed. The full integrated test suite shows **zero D-5-caused regressions**.

**The wave halts, not closes, because the §G gate's own live verification found real specimen data
was not yet reproducible against the deployed system** — per the native's own D-5 kickoff framing
("a red on integrity, specimens, or degradation is [a wave failure]"), this is exactly the class of
red that must surface to the native rather than be adjudicated around. This is **not a correctness
failure of any lane's code** — every defect this wave found was a wiring/scheduling/timeout gap in
the REBUILD/GATE machinery, never a data-quality or logic regression, and one of the two gate
findings (the MCP wiring gap) is already fixed and independently re-verified.

## §2 — What is DONE (verified, not claimed)

- **G-1 Resonance map** (PR #621, `9a2ec77c`): `gochara_resonance_map` live for 3 event-classes,
  80 rows, 0 citation-invariant violations, live-verified.
- **G-2 Configuration grammar** (PR #622, `7b6d7f27`): 12 primitives + 6 composition operators,
  3770 tests, every citation independently traced to a real codebase-attested source (zero
  fabrication found by the verifier).
- **G-3 Intensity engine** (PR #625, `1bdec728`): λ_e = PROMISE × PERMISSION × exp(β·X) −
  suppression; PERMISSION's non-Vimśottarī-gated multi-system behavior independently re-derived
  by the verifier from first principles (not code-read) and confirmed live.
- **G-4 Forward sweep + serving** (PR #627, `095a2bc1`, + fixes below): shape-aware
  point/interval/chain output live-verified against real ontology data; `peak_basis`/DR-10 honesty
  independently confirmed (DIS.023 genuinely names no gochara-engine peak model).
- **G-5 Ledger integration** (PR #629, `f1d8e339`): engine-claim filing with
  `configuration_signature`; DR-16 five-property adverse-disclosure gate live-verified in BOTH
  directions (a complete claim accepted; the verifier's OWN deliberately-incomplete claim rejected
  pre-INSERT) — a persistence-scope limitation (frozen ledger schema has no spare column for the
  disclosure payload) was found, disclosed, and correctly NOT worked around with an out-of-scope
  migration; carried for a future ruling.
- **Full test suite on merged main**: python-sidecar 3841/3841 (post all fixes), platform
  5841/5841, platform-mcp's 75 pre-existing failures confirmed **byte-identical** to the D-5-open
  baseline commit (`834a52e9`) — zero D-5 regressions anywhere.
- **Deploy**: `amjis_web`/`amjis_mcp`/`amjis_sidecar`/`brahma_build_pipeline_job` all live-SHA-verified
  at the final fix commit (`1f05c4ac`).

## §3 — REBUILD-time incidents (all found via genuine live/orchestrator-driven execution — none
caught by any lane's own Phase-1 testing, which is exactly why REBUILD exists as a separate
lifecycle step)

1. **Untyped-NULL SQL placeholder** (`_fetch_av_gate_rows`) → `IndeterminateDatatype` → poisoned
   the shared sweep connection for every subsequent query. **FIXED** (PR #631, `14b82dae`),
   live-reproduced-then-fixed, independently re-verified.
2. **Bare `conn.rollback()` in the fix above** destroyed the orchestrator's own per-substep
   `SAVEPOINT writer_exec` (a FROZEN-contract-adjacent violation reached indirectly by importing a
   helper across an execution-context boundary it wasn't designed for). **FIXED** (PR #634,
   `f8944651`) — `savepoint_scope()` context manager, safe in both standalone and
   orchestrator-nested contexts, converted every call site across `gochara_grammar`,
   `gochara_intensity`, and `ka_gochara_sweep` (6 modules, not just the 1 originally touched);
   `safe_rollback` deleted entirely (zero remaining callers, confirmed by grep).
3. **Decade-sized substep chunking** exceeded the orchestrator's `writer_timeout_seconds=1800`
   watchdog with zero rows committed — a pure scheduling-granularity issue (zero correctness
   defect: the run had zero transaction-abort errors, confirming fix #2 held). **FIXED** (PR #635,
   `9b883196`) — re-chunked to per-year substeps (300 total for 3 populated event-classes),
   `_RESUME_VERSION` bumped so a stale ledger can't be misread.
4. **G-4's 3 MCP serving tools never wired into `server.ts`** — built, tested, merged, but dead
   code at every deployed SHA since PR #627. Found by the §G gate runner (criterion 1). **FIXED**
   (PR #640, `1f05c4ac`) — one import + one registration call, `tsc` clean, test suite unaffected,
   live-SHA-verified deployed.
5. **Specimen-window substep priority**: the sweep processes chronologically from the chart's
   840-row multi-cycle `chart_dashas`-derived birth-year anchor (1950, not literal 1984 — a
   pre-existing, already-carried finding inherited from the sealed `ka_sangam.py` pattern), so the
   3 named LEL specimens (2010-11, 2013, ~2025) were unreachable within any single ~30-minute
   dispatch window. Found by the same gate run (criterion 3). **Fix deployed** (same PR #640) —
   `plan_substeps` now sorts specimen-overlapping years first (live-confirmed via dry-run: the
   first 3 of 300 substeps are exactly `major_gain:year:60`, `major_gain:year:61`,
   `marriage:year:63`) — **but not yet confirmed against real committed data** at session end (see
   §4).

## §4 — Why the wave halts here

The §G gate ran once (protocol §3 Phase-2, live against the deployed connector): **RED**, two
findings (incidents #4 and #5 above). Incident #4 is fixed and independently re-verified — a
retest would pass. Incident #5's fix is deployed and independently confirmed *correct by design*
(the dry-run ordering is right), but a fresh rebuild dispatch (attempt 5, build_run
`6ac5dcb6-e792-452c-9426-788d216e5c34`, job `brahma-build-pipeline-job-5rhsp`) was still actively,
healthily processing the first specimen-priority substep (`major_gain:year:60`, 35 resonance
targets — the heaviest of the three specimen substeps) when this session ended. No errors occurred
in ~9 minutes of observed runtime (well within the 1800s budget); real log activity continued
throughout every check.

Per the native's own D-5 kickoff framing — *"Gate framing: engine-integrity + specimens +
no-degradation vs A-5 — explicitly NOT a calibration claim... a red on integrity, specimens, or
degradation is [a wave failure]"* — a gate red specifically about specimen-findability is named as
exactly the class that must halt-and-report, not be adjudicated around, even when (as here) the
underlying cause is well-understood, already-fixed-in-design, and actively resolving on its own.
Forcing a GREEN stamp on an unconfirmed specimen would be the precise failure this campaign's
Phase-1/Phase-2 verification split exists to prevent (CONDUCTOR_PROTOCOL §5: "a half-passed gate
stamped complete is the exact failure this protocol exists to prevent").

**This is not expected to require further code changes.** The next session's first action should
simply be to check whether build_run `6ac5dcb6...` reached the 3 priority substeps (query in
STATE_D-5.md's `session_end_disposition.next_session_action`), and if the job terminated before
completing (timeout is likely — each dispatch has a shared ~30-minute budget, and this is at least
the second dispatch needed), re-dispatch once more (fully idempotent — the resumption ledger
preserves already-committed substeps). Once the 3 named specimens are confirmed live, re-run the
§G gate; criteria 1/4/5/6 (which were blocked by the same wiring/data gaps) should all pass
alongside criterion 3. The Sarvatobhadra specimen (~2025-05) is a standing, already-carried
exception — no classical vedha-grid data exists live anywhere in the database (G-2's own honest
finding, migrations 140/144 have zero rows) — it is demonstrable only via primitive-level unit
tests, not served rows, and this was disclosed from G-2's own close-out onward, not discovered at
gate time.

## §5 — Findings requiring future disposition (carried, not blocking re-gate)

- G-2: Sarvatobhadra classical grid is an honest algorithmic approximation (`uncited_extension=true`)
  — real classical grid population is open future work.
- G-4: `muhurta_finder` re-pointing (BRIEF_D5's stated eventual intent) explicitly deferred as a
  separate, riskier change to an already-live tool.
- G-4: chart 482012f1's sweep birth-year anchor resolves to 1950, not literal 1984, due to a
  pre-existing multi-cycle `chart_dashas` substrate — inherited from the already-sealed
  `ka_sangam.py` pattern, not a D-5 regression.
- G-5: DR-16 disclosure payload persists in the filing response but not on the stored ledger row
  (frozen schema, no spare column, correctly not worked around with an out-of-scope migration) —
  needs either a native ruling on interpretation or a follow-on migration.
- Pre-existing, out of D-5 scope: `ka_avadhi.py`'s older `_DASHA_SYSTEMS` tuple is also stale vs
  live `chart_dashas.system_id` (same root-cause class as a D-5 fix, different file) — future
  hygiene pass.
- Pre-existing, out of D-5 scope: 75 platform-mcp test failures (confirmed present at the D-5-open
  baseline, unrelated `r5-w3-phase-b` judgment/portrait work) — not a D-5 responsibility.
- Orchestrator-core robustness candidate (NOT fixed, NOT to be fixed in-lane per CLAUDE.md §N.2):
  `asset_runner.py`'s `mark_asset_error` doesn't defensively roll back before writing an error
  record, so an already-aborted connection can cause the error-recording write itself to fail
  (observed in incident #2's traceback, sidestepped rather than fixed by ensuring writer-called
  code never poisons the connection in the first place). Flagged for native review if
  `asset_runner.py` is ever revisited.

## §6 — Cleanup verification

All lane worktrees and branches (`wave/D-5/G-1` through `G-5`, plus 3 fix branches) removed after
merge. `origin/main` HEAD matches the deployed `amjis-web`/`amjis-mcp` SHA (`1f05c4ac`). No D-5
stray worktrees remain in this session's own conductor worktree tree.

## §7 — Next (superseded by §8 below — kept for historical record of this halt's original reasoning)

`current_wave` remains **D-5** (does NOT advance to D-4b) until this halt is dispositioned and the
§G gate re-runs green. Recommended native disposition: confirm the halt reasoning is sound (a
scheduling/data-timing gap, not a correctness gap) and either (a) authorize the next session to
simply re-check/re-dispatch the sweep and re-run the gate with no further code review needed, or
(b) request additional review of the 5 REBUILD-incident fixes before doing so. STATE_D-5.md carries
the full incident-by-incident ledger for either path.

## §8 — Update: §7's own next-action was executed; gate_run_2 found NEW reds in the live specimen data itself

Per §7's recommendation, this same session (continued) re-dispatched the sweep twice more
(attempts 5 and 6 — attempt 5 completed its full budget cleanly and committed 2/3 priority
specimens; attempt 6, dispatched via a brief local Cloud SQL Auth Proxy session per the
O8_LOCAL_PROXY_KILL_ROOT_CAUSE_v1_0.md precedent, committed the 3rd). **All 3 named-specimen
priority substeps (`major_gain:year:60`, `major_gain:year:61`, `marriage:year:63`) are now
confirmed live** — independently re-verified via direct SQL against `build_substep_progress`.

A fresh-context agent (not the conductor who wrote the fixes — genuine independent verification,
per ADJUDICATOR_CHARGE §"never self-verify") then re-ran the full §G gate against this newly-live
data. Result: **gate_run_2 is RED again — but for two NEW reasons**, not restatements of
gate_run_1's now-resolved findings:

- **RED-A (gate_run_1) reconfirmed GREEN**: the MCP wiring fix is independently re-verified present
  at `origin/main` HEAD.
- **RED-B (gate_run_1) is resolved**: the specimen-data-absence problem is gone — the data now
  exists.
- **RED-C (NEW)**: `ka_gochara_sweep/shape_output.py::build_interval_rows` never reads or enforces
  `brahma_event_ontology.duration_prior.max_days` (major_gain is capped at 365 days in the
  ontology's own declaration). The two live `major_gain` rows for chart 482012f1 are each ~365 days
  wide — bounded by the per-year substep chunking (an artifact of incident #3's own fix), not by
  real signal cessation. This is a shape-aware-serving violation in the *opposite* direction from
  what BRIEF_D5 warned about: not over-precision, but an unenforced ontology-declared ceiling.
- **RED-D (NEW)**: the marriage specimen (2013-12-11 double-transit) genuinely does not retrodict.
  The only 2013 `kala_gochara_windows` row for this event class is dated 2013-01-06 (~11 months
  off), and its `contributing_systems` shows `guru_shani_double_transit` — the exact mechanism the
  specimen is named for — is **inactive**; only `chara_karaka` fired. Root cause is undiagnosed.

**Neither RED-C nor RED-D was fixed this session.** Per the native's own D-5 kickoff framing — a
red on *specimens* is a wave-failure class, explicitly not something to adjudicate around — and per
the explicit standing instruction ("If red: halt-and-report ... the red stands until the native
dispositions it"), this session halts again here rather than attempting further autonomous fixes or
re-dispatch cycles. This is a materially different halt reason than the original one in §1–§7 (which
was purely a scheduling/data-timing gap): RED-C and RED-D are substantive findings about the
freshly-live specimen data's own correctness, requiring native judgment on scope and root-cause
priority before more code changes are made.

## §9 — Next (current, supersedes §7)

`current_wave` remains **D-5**. Native disposition needed on:
1. **RED-C** — is enforcing `max_days` from the ontology in `shape_output.py::build_interval_rows`
   an in-scope, low-risk follow-on fix, or does it need broader design review (e.g. should the
   *sweep* stop early on signal cessation instead of/in addition to a hard ontology cap)?
2. **RED-D** — authorize a root-cause investigation into why `guru_shani_double_transit` doesn't
   activate near 2013-12-11 for chart 482012f1 (starting point: the primitive's activation-window
   logic in `gochara_grammar/primitives.py` and `gochara_intensity`'s PERMISSION gating for this
   specific system) — OR rule that a genuine specimen miss is itself a disclosure-worthy finding
   about the engine's current limits rather than a bug to chase.

STATE_D-5.md's `gate_run_2` block carries the full evidence for both findings.

## §10 — Session re-entry, RED-C/RED-D root-cause fixes, native disposition, final gate, CLOSE

Re-entered per protocol §6.2 after an accidental mid-session close. Reconciled ledger vs reality
first (git branch/worktree inventory, build_runs state) before any new work — no half-done work
found; the two fix worktrees (`wave/D-5/fix-red-c`, `wave/D-5/fix-red-d`) had real, uncommitted/
committed progress matching STATE_D-5.md's carried findings.

**RED-C — root-cause fixed, PR #650 (`86a82ca5`, merged+deployed).** `shape_output.py`'s v4 design
(each year-substep computes only its own strictly-bounded segment; `writer.py`'s
`_consolidate_interval_segment` chains already-committed adjacent segments via
`kala_gochara_windows.continuity_state`, migration 461 — order-independent by construction, no
scan-distance dependency) was sound but had never been committed/tested. While authoring the test
suite for it (before first commit), found a real bug in the design itself: the year-chunk grid is
inclusive on both ends, so adjacent chunks' shared boundary day is the SAME calendar date, not
date±1 — the neighbor-lookup used off-by-one adjacency, so real year-boundary segments would never
actually merge in production. Fixed to exact-date-equality adjacency. 27/27 targeted tests, 3895/23
(pre-existing unrelated `test_l0_remedy_corpus.py`) on the wider suite.

**RED-D — already root-caused and fixed by the interrupted session, independently re-verified.**
Saturn occupying natal Saturn's 7th house (Libra, resident since 2012-08-08) + Jupiter's 5th special
aspect from Gemini onto Libra is genuinely BPHS Ch.26-valid, but `double_transit` required both legs
to be aspect-shaped (Saturn's leg here is occupation). Fixed via a rasi-drishti fallback for
bhava-target aspect detection plus a new `double_transit_mixed` composition operator pairing one
occupation-shaped leg against one aspect-shaped leg. Independently re-verified two ways before
trusting it: reran the 79-test suite myself (not just the commit message), and separately queried
`swisseph` directly for the real 2013-12-11 sidereal positions to confirm the astronomy claim
independent of the fix's own code. PR #651 (`d2d9555e`, merged+deployed).

**Rebuild-timeout perf regression — found, fixed, PR #663 (`5ceedd75`, merged+deployed).**
Dispatching the post-merge rebuild, the first specimen substep (previously fine pre-fix) exceeded
`writer_timeout_seconds=1800` with zero rows committed. Diagnosed live: RED-D's fix correctly
reaches more targets in `gochara_grammar/primitives.py`/`sarvatobhadra.py`, exposing pre-existing
per-target "skipping" honest-degrade diagnostics logged at INFO inside `ka_gochara_sweep`'s hot
per-grid-day loop (>1000 log lines/10s observed live). Fixed: log-level only (INFO→DEBUG, 14 call
sites), zero behavior change, confirmed via re-dispatch (all 3 priority specimens committed within
~15 minutes, vs. a full timeout with zero commits before the fix).

**gate_run_2 findings 1/2 — native-dispositioned, PR #665 (`81a77f26`, merged+deployed).** The
first post-fix rebuild's live data surfaced two genuinely new, deep questions (not restatements of
RED-C/RED-D): (1) `major_gain`'s committed window (`continuity_state`: `left_active=right_active=
true`) revealed the true signal is continuously elevated for well over two years — the 365-day cap,
correctly enforced, was anchoring to a truncated `raw_start` and serving a pseudo-precise closed
window; (2) the marriage specimen's served peak (2013-01-07, `chara_karaka`) was the single
argmax of a year-long active run, silently dropping whatever the ~2013-12-11 mechanism contributes.
Reported both to the native rather than fixing speculatively (third distinct issue this session —
the native's own stated stop condition for this resumption). **Native disposition**: both ruled
serving-honesty defects, in-scope, explicitly refusing calibration work or specimen-aware
weighting. Fix 1: `register_gochara_windows.ts` derives `plateau_disclosure` (open-edge flags) from
the already-persisted `continuity_state` on every interval row, across all three MCP tools — a
structural cap is never served as a confirmed signal cessation. Fix 2: `shape_output.build_point_rows`
serves one row per LOCAL maximum within a run (`_local_maxima`, standard peak detection, no
specimen-tuned knobs — every genuine local max is emitted; row-count limiting is exactly what
§N.6's existing response-budget mechanism already does generically), each independently attributed.
Corrected specimen assertions, native-specified: interval-class scoring is OVERLAP (the windfall
interval lies within the served plateau); point-class scoring is presence-of-true-date-peak-among-
served-peaks, NOT rank-1. `_RESUME_VERSION` bumped 5→6. One final §G re-run explicitly authorized
by name (not a re-litigation of prior reds — new, distinct, doctrine-derived defect classes).

**Final rebuild + gate re-verification (build_run `ccb7f597`, job `brahma-build-pipeline-job-nld7d`,
all 3 priority specimens committed).**

- `major_gain` (interval): `window_start=2010-01-01, window_end=2011-01-01`,
  `continuity_state={raw_start:2010-01-01, raw_end:2012-01-01, left_active:true, right_active:true}`.
  **PASSES** the corrected OVERLAP assertion — `[2010-01-01, 2011-01-01]` overlaps the LEL windfall
  specimen `[2010-07, 2011-03]` by ~6 months, and the served plateau_disclosure honestly flags both
  edges open (not a confirmed closed span).
- `marriage` (point): still only ONE served row (`2013-01-07`, `chara_karaka` active,
  `guru_shani_double_transit` inactive on that day). The top-K local-maxima mechanism is correctly
  implemented and unit-verified in isolation (two synthetic humps within one run both served,
  independently attributed) — but the LIVE composite signal for this specific chart does not
  produce a distinct local maximum near 2013-12-11 strong enough to register as a second served
  peak, even though the underlying mechanism is now structurally reachable (RED-D) and the
  ephemeris configuration is independently confirmed real. **STILL FAILS** the corrected
  presence-among-peaks assertion. Root cause of *why* the composite lambda_e doesn't crest a second
  time near the true date (suppression damping, PROMISE weighting, or a genuine "this specimen's
  aggregate signal is weaker than the January configuration for this chart") is undiagnosed — per
  the native's own pre-committed outcome for this exact case, this is NOT chased with a further fix
  cycle in D-5.

**Disposition (per native's pre-committed outcomes, explicitly anticipating this exact split
result): D-5 closes GREEN-WITH-PARTIALS.** The major_gain specimen passes cleanly under corrected
doctrine; the marriage specimen's residual (mechanism reachable + astronomically real, but not
surfacing as a served local maximum for this chart) transfers to D-4b's Grand Bakeoff as a named
calibration/residual item — registered below as the DR-17 type-specimen residual pair
(`chara_karaka` vs `guru_shani_double_transit`, 2013). No further D-5 fix cycles occur.

**Doctrine registered at close (native-ratified 2026-07-20, texts in
`DR_14_15_16_TEMPORAL_DOCTRINE_v1_0.md`, arc-plan §12 binds both on D-4b):**
- **DR-17 — Graded Manifestation Acceptance.** Likely-time doctrine (peak/sub_peak/elevated
  right-in-kind, neutral=miss, contra=anti-hit double-weighted, tie-bands, percentile-of-
  manifestation vs mirrored controls, residual mining + served `unmodeled_variance`). D-5 implements
  NO DR-17 scoring itself (D-4b harness/calibration work) — the corrected D-5 specimen assertions
  above are DR-17-compatible by construction (overlap = elevated grade; presence-among-peaks =
  tie-band/sub-peak acceptance).
- **DR-18 — Knowledge-Utilization Census.** D-4b harness item, no D-5 implementation.
- Shared register entry (both gate_run_2 findings 1/2, one defect class): "serving-layer collapses
  manufacturing false precision from honest signal" — siblings of RED-C's chunk-bounded windows
  (§N.6 lineage).

**Deploy (final, this session):** `amjis_web`/`amjis_mcp`/`amjis_sidecar`/`brahma_build_pipeline_job`
all live-SHA-verified at `81a77f263a7d61c2ba2a8c57f5cf7605c35231df` (PR #665 merge commit).

**`current_wave` advances D-5 → D-4b** (INCOMING — `BRIEF_D4B.md` fleshes and freezes at its own
readiness pass, per its own frontmatter). Full worktree/branch cleanup performed at session close
(§11/STATE_D-5.md final block).

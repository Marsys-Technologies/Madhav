---
artifact: REPORT_D-5
type: WAVE CLOSE REPORT (protocol §7 — "the D-1 lesson: a wave without a close report did not close")
wave: D-5 — Gochara-Chitra
status: BLOCKED — HALT-AND-REPORT (ESCALATION_POLICY §2; native's own D-5 kickoff directive: "a red on... specimens... is [a wave failure]", not gated around)
opened: 2026-07-19T08:31:47Z
halted: 2026-07-20T05:11:00Z (~20.5 hours elapsed)
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

## §7 — Next

`current_wave` remains **D-5** (does NOT advance to D-4b) until this halt is dispositioned and the
§G gate re-runs green. Recommended native disposition: confirm the halt reasoning is sound (a
scheduling/data-timing gap, not a correctness gap) and either (a) authorize the next session to
simply re-check/re-dispatch the sweep and re-run the gate with no further code review needed, or
(b) request additional review of the 5 REBUILD-incident fixes before doing so. STATE_D-5.md carries
the full incident-by-incident ledger for either path.

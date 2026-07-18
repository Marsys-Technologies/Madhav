---
artifact: PRE_D4_WRAPUP_REPORT
type: NATIVE-DIRECTED WRAP-UP PASS — full checklist with evidence
status: COMPLETE — paused for native go before D-4 opens
authored_by: D-3 conductor session, 2026-07-18
---

# Pre-D-4 Wrap-Up Pass — Full Report

Executed per native directive "Pre-D-4 wrap-up pass. Execute everything below, report with
evidence, and PAUSE for my go before opening D-4." This is that report. **D-4 has NOT been
opened.** No D-4 lane code, no bakeoff scoring runs, no schema migrations beyond what's noted
below were performed, per the stated constraints.

---

## A — Resolve D-3's standing RED disposition

### A1 — Control-matching check ✅ DONE

Re-scored the EXISTING §G run's saved data (unmodified `score_g.py`, `lel_events.json`,
`pooled_activations.json`) with the shuffled-birth control constrained to identical coverage
(2010-08-18 → 2032-07-01) and identical scorable-event N (29, down from 40) as the real chart.

| | All-N (original) | Coverage-matched (N=29) |
|---|---|---|
| Real chart hit rate | 7/40 = 17.5% | 5/29 = 17.2% |
| Shuffled control mean | 33.6% | 33.0% |
| **Control gap** | **−16.1pp** | **−15.8pp** |

**Finding: the coverage restriction does NOT materially explain the red.** The gap barely moves.
This means A2's coverage-extension goal, even if achieved, was unlikely to flip §G to green on
its own — a materially useful thing to know before deciding how much effort A2 deserves.

Artifacts: `coverage_matched_control.py` + `coverage_matched_result.json` (session scratchpad,
reusing `score_g.py`'s exact scoring functions — algorithm unchanged, only the event/control
subset changed).

### A2 — FIX-COV lane ⚠️ STOPPED per its own guard (not a failure — the native's own anticipated outcome)

Root cause found and evidenced (not assumed): `resolve_activation_windows()`
(`services/ka_temporal/date_resolver.py:392-551`) correctly matches ALL in-life dasha periods for
a predicate — L1's `chart_dashas` genuinely spans 1949–2100, confirmed live, full coverage exists
at the fact layer — but then collapses to a SINGLE `primary_selected` window
(current-straddling-today > soonest-future > most-recent-past). Every other matched period
survives only in an informational JSON array the serving layer never windows on. This is a
previously-known, self-disclosed gap (`query_temporal_activation.ts` already carries an honest
`single_cycle_per_signal` caveat naming "the multi-cycle generator is D-3 scope").

Fixing it requires EITHER (1) emitting one row per matched period instead of one — needs a
migration widening/dropping the `UNIQUE(chart_id, signal_id, ayanamsha_id)` index (migration 246)
plus rewriting the primary-window collapse logic, with row count ballooning ~3–6× and unverified
L4/L5 downstream impact — OR (2) redefining the served window as an envelope over all matched
periods, which doesn't need a migration but silently changes what "activation window" *means* for
every existing consumer. **Both require rebuilding predicate/window-selection logic — exactly the
native's own explicit STOP condition** ("if the fix proves larger than one focused lane... STOP
and bring me the expanded scope before proceeding").

Zero files touched, zero commits. The worktree (`/Users/Dev/Vibe-Coding/Apps/Madhav-wave-D3-FIXCOV`,
branch `wave/D-3/FIX-COV`) is preserved, untouched, ready for a properly-scoped follow-up lane if
you authorize it.

**Decision needed from you**: authorize the larger FIX-COV scope (schema migration + writer
cardinality change, its own implement→verify→integrate→deploy→rebuild cycle) as a named follow-up
lane, or accept A1's finding that coverage isn't the primary driver and treat D-3's original §G
RED as standing without a re-run.

### A3 — One blind §G re-run post-FIX-COV ⛔ NOT ATTEMPTED

Contingent on A2 completing, per your own directive's ordering. A2 stopped instead. **Not
attempted, awaiting your A2 decision.**

### A4 — Pre-committed disposition ⛔ NOT REACHED

Same reason as A3. D-3's original §G RED (recorded in `REPORT_D-3.md`, run 2026-07-18) remains
the authoritative, standing result. `current_wave` has NOT been advanced.

---

## B — Event-semantics upgrade (drafted, none ratified/implemented)

### B1 — Event-Scoring Semantics DR ✅ DRAFTED

`DR_13_EVENT_SCORING_SEMANTICS_DRAFT.md` — five parts exactly as specified: (a) `shape` tag
(point/interval/chain), (b) interval-overlap scoring, (c) chain milestone decomposition, (d)
confidence-scaled tolerance (exact ±45d / month-known ±75d / year-only → secondary battery, never
silently folded in), (e) the non-negotiable control-mirroring rule. Explicitly scoped as
NOT retroactively re-scoring D-3's RED, NOT touching DR-11's exact-confidence figure, NOT
authorizing any kernel-weight/threshold/orb/valence change. Registered as `DIS.026`/`DR-13
(DRAFT)` in `DISAGREEMENT_REGISTER_v1_0.md` — status `draft_awaiting_native_ratification_at_D4_bind`,
explicitly distinct from the provisional-DR batch-ratification pattern since this one needs your
direct input up front.

### B2 — LEL schema v2 proposal ✅ WRITTEN, NOT MIGRATED

`LEL_SCHEMA_V2_PROPOSAL.md` — additive only (8 new nullable columns + CHECK constraints on the
real, live-verified `life_events` table schema, confirmed via direct query, not assumed).
Migration sketch included, staged for D-4, not applied.

### B3 — Native date-tightening questionnaire ✅ WRITTEN, blind

`NATIVE_DATE_TIGHTENING_QUESTIONNAIRE.md` — the 16 vagueness-excluded events (confirmed against
the actual §G exclusion list, birth anchor correctly omitted) plus the named chain candidates
(sand-quarry arc, windfall payment-flow, sleep-disorder onset/resolution, Mahindra career arc,
XIMB MBA chain, Tepper selection — all pulled from real LEL records, cross-referenced against the
full event list to find the actual event_ids). **Firewall verified**: contains only event_id,
recorded event_date, category/domain, and the existing description — zero curve outputs, peak
dates, or model information anywhere in the document.

### B4 — 2010 windfall reclassification ✅ NOTED

Folded into both DR-13 (explicit non-scope callout) and the questionnaire (Part 2 item B) — the
windfall anchor event is flagged for `interval`-shape reclassification at the next re-scoring;
its own proximity check already PASSED under the old point-only scoring (peak within +43 days),
only intensity failed — this is recorded so a future re-score doesn't need to rediscover it.

---

## C — D-3 engineering follow-ups (all closed or dispositioned, zero silent carries)

| # | Item | Disposition | Evidence |
|---|---|---|---|
| C1 | Vedha graha-name case bug | **FIXED** (confirmed already live) | `engine.py` lines 240/245/246 — both sides `.strip().lower()`, alongside the separate sign-frame fix. Both CR-102 bugs addressed together. |
| C2 | NBRY `inactive_weight=0.4` | **RULED** (Opus Adjudicator) | May stand as a provisional, caller-overridable engineering placeholder — currently wired into NO served surface (not behavior-changing), qualitative doctrine uncontested, magnitude merely underdetermined not §3-contested. Falsifier: a classical source fixing the weight, or the future wiring lane showing 0.4-vs-alternatives flips a served verdict → routes native/Fable. |
| C3 | T-4 warning-score divergence | **CLOSE-AS-DOCUMENTED** | Real, live divergence confirmed, but already discharged via `permission.py`'s existing `percentile_note` naming the limitation and pointing to the authoritative TS view. No code change needed. |
| C4 | T-2 ashtakavarga category name | **CLOSE-AS-DOCUMENTED** | False alarm — confirmed live against 482012f1: `ashtakavarga_bindu_sign` (sign-indexed) and `ashtakavarga_bindu` (house-indexed, `mi_adhilepa`'s) are two DIFFERENT real coexisting categories, not a mismatch. |
| C5 | RR-fix global-asset join | **CLOSE-AS-DOCUMENTED (cosmetic)** | Premise overstated — the join uses the run's NOT-NULL `chart_id`, not the asset's scope; normal per-asset writes have no chart join at all. Sole residual (crashed-run rows resetting only via a subsequent run) is general, not global-specific, and touches only a per-run audit table — `asset_throughput` (authoritative) is always correct. |
| C6 | No-tiebreak pattern, 4 writers | **FIXED AND VERIFIED** — PR #607 | 13 sites across `bo_drishti.py`/`mi_darshana.py`/`ph_nimitta.py`/`bo_chart_gestalt.py` given stable PK/group-key tiebreaks. Opus-verified ACCEPT (86/86 tests, `DISTINCT ON` semantics confirmed sound). Merging now (CI green). |
| C7 | Unratified 0.5/0.6 weight defaults | **VERIFIED SAFE** | Sole production caller passes explicit admitted 0.2/0.2 weights; full-tree grep confirms zero other live callers rely on defaults. Sid_mode cache race noted still open/low-risk, not fixed (informational only). |

---

## D — Governance & hygiene

### D1 — Register sync ✅ DONE

- `MARSYS_DEFECT_GAP_REGISTER_v2_0.md`: CR-108 updated to **CLOSED** with full verification/deploy/falsifier evidence.
- `DISAGREEMENT_REGISTER_v1_0.md`: DR-13/DIS.026 added as a DRAFT pointer entry (not a ratified provisional — explicitly gated on your ratification at D-4 bind).
- DR-10/11/12's final ratified text was already recorded at their original ruling time (`DIS.023`/`DIS.024`/`DIS.025`) — confirmed present, unchanged, no action needed.
- §G's per-event scoring artifact (`score_g.py`, `lel_events.json`, `pooled_activations.json`, `result_g.json`, `coverage_matched_result.json`) currently lives in this session's scratchpad — **recommend copying into a permanent campaign artifact location before D-4 opens**, since D-4's C-1 bakeoff needs it and scratchpad paths are not guaranteed to survive across sessions. Not yet done — flagging for your go or a D-4-open action item.

### D2 — Three-surface consistency sweep ✅ DONE, clean

`CLAUDECODE_BRIEF.md` (`current_wave: D-3`) and `CURRENT_STATE_v1_0.md §2`'s banner (`current_wave
= D-3`) are consistent — correctly NOT advanced, since D-3 has not closed. No contradiction found.

### D3 — Baseline comparison artifact ⛔ NOT DONE — gated on A per your own ordering

Your directive says "after A resolves, re-run the verbatim baseline wealth question." A did not
fully resolve (A2 stopped). Not attempted — will run once you disposition A.

### D4 — Worktree/branch/deploy-SHA/tool-count consistency ✅ DONE, found and fixed one gap

- **Found and fixed**: two stranded REMOTE branches (`origin/wave/D-3/FIX-PSEL`,
  `origin/wave/D-3/PERF-TRIGGER-CACHE`) — merged earlier this session but only deleted locally,
  not on origin. Deleted now.
- Live deploy SHAs confirmed consistent: `amjis-web`/`amjis-sidecar`/`brahma-build-pipeline-job` @
  `04d5d0ce…` (post PERF-TRIGGER-CACHE, the latest merge before this pass), `amjis-mcp` @
  `11377530…` unchanged (no `platform-mcp/` path touched all cycle — logically guaranteed, not
  re-probed live since the SHA hasn't changed).
- Remaining worktrees: `wave/D-3/FIX-COV` (intentionally preserved per A2's STOP finding),
  `wave/D-3/C6-tiebreak-hardening` (in flight, cleaning up once PR #607 merges+deploys).
- Tool count: not re-probed live (no `platform-mcp/` redeploy occurred, so it is unchanged from
  D-2's confirmed 138-tool baseline by logical necessity, not fresh measurement).

---

## E — D-4 binder pre-work (pre-work only, NOT the wave open)

### E1 — BIND_D-4 draft ✅ WRITTEN

`BIND_D-4_PREWORK_DRAFT.md` — fresh-verifies what's verifiable now against BRIEF_D4's §B slots:
slot 1 (matcher diagnosis) correctly deferred to D-4's own Binder per your no-lane-code
constraint; slot 2 (event-class taxonomy) partially advanced (9 real categories enumerated from
live data); slot 3 (curve-shape parameters) directly informed by §G's real measured
curve-variance/top-decile-fraction numbers; slot 4 (promotion-gate thresholds) correctly left
untouched (native/Adjudicator-doctrine territory); slot 5 (rollback pin + prior batteries)
fresh-verified — batteries are NOT all green (§G is RED), which is precisely why D-4 hasn't
opened. DR-12's bakeoff inheritance from this pass spelled out explicitly.

### E2 — C-2 firewall re-scope language check ✅ DONE, confirmed consistent

"LEL → prediction-INPUTS quarantined; LEL → outcome-SCORING free" is consistent with the
questionnaire flow: tightening a date is LEL data-correction, not a prediction input, so it never
touches the firewall's quarantine boundary. Sealed test-split handling for tightened events
explicitly documented (folded into `BIND_D-4_PREWORK_DRAFT.md`): tightening a date does not change
which split an event belongs to; the questionnaire's own blind-firewall (no model output shown to
you) means the tightening process itself cannot leak sealed-split information.

---

## Summary — what needs your go

1. **A2/A3/A4**: authorize the larger FIX-COV scope (migration + writer cardinality change) as
   its own follow-up lane, or accept D-3's original §G RED as standing without a re-run (A1's
   finding suggests a re-run likely wouldn't flip the result anyway).
2. **D3**: once (1) is decided, the baseline wealth-question diff can run.
3. **The permanent-artifact-store gap** noted in D1 (§G's scoring artifacts currently only in
   session scratchpad).
4. **DR-13/B1-B4**: these are drafts awaiting your direct ratification/completion (the
   questionnaire needs your dates back before D-4's C-1 can consume DR-13 meaningfully).
5. Everything else (all of C, D1/D2/D4, E1/E2) is DONE, verified, and needs no further action from
   you before D-4 — they're reported for visibility, not decision.

**Pausing here per your instruction. Awaiting your go before D-4 opens.**

---
artifact: BRIEF_D4B
type: WAVE BRIEF (FROZEN — fleshed per pre-D-4b readiness pass; §B binds fresh at D-4b open)
wave: D-4b — Calibration Ignition + Grand Bakeoff (campaign close)
version: 1.0
status: CLOSED — CAMPAIGN CLOSE, 2026-07-23, native ruling (CR-128/NP-D4B-009 via Cowork): B-1
  DONE (PR #712, honest NO_WINNER, final); B-2/B-3 close HONESTLY-DEFERRED to the prospective
  regime; B-6 REAL close delivered. See `REPORT_D4B.md`/`STATE_D4B.md`/`PROMISE_LEDGER_D4B.md` for
  the full close package. Native kickoff via Cowork 2026-07-21, formally recorded at open;
  predecessor halt report (HALTED-PENDING-FORMAL-OPEN, prior session same date) incorporated.
prerequisite: D-5 gate GREEN-WITH-PARTIALS (native-accepted close disposition, STATE_D-5.md
  gate_run_3) + A.0's materialization-completeness gate (this brief's own §0, NEW) satisfied
  at D-4b open — re-verified fresh at open, not assumed from this pass's snapshot.
authored_by: Claude Code (Sonnet 5), pre-D-4b readiness pass v3, 2026-07-21
lane_source: TEMPORAL_ENGINE_ARC_PLAN_v1_0.md §5 (authoritative lane texts) + BRIEF_D4.md v2.0
  (SUPERSEDED-BY-ARC, original C-B/C-2/C-5/C-6 prose, carried verbatim where unchanged)
---

# BRIEF_D4B — Calibration Ignition + Grand Bakeoff (campaign close)

## §0 — Materialization-completeness gate (NEW, this readiness pass — hard prerequisite)

**No scoring run may start against a partially-materialized `ka_gochara_sweep`.** D-5's own
gate_run_3 marriage-specimen verdict was assessed against roughly 1% of the sweep's planned
substep coverage (3 of ~300, all specimen-priority substeps) — this was defensible for a
specimen spot-check but is NOT sufficient for B-1's bakeoff, which scores the full LEL corpus
against served windows across the whole birth→birth+100y horizon. Binding assertion, checked at
D-4b OPEN before any other bind-at-open slot resolves:

```sql
SELECT count(*) FROM build_substep_progress
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND asset_id = 'ka_gochara_sweep';
-- must equal the planned substep count (populated_event_classes × 100 years) for chart 482012f1
```

If this is not 100% at D-4b open, the Binder does not proceed to §B — it re-dispatches
`ka_gochara_sweep` to completion first (Cloud Run job path, resumable, §N.3-safe) and records the
gap in the open session's log. **This is the NEW assertion class this readiness pass registers**
(see the pass's own report): materialization-completeness precedes gate/scoring, always, for any
future heavy-writer asset a wave's empirical claims depend on — not just this one.

### §0 RECONCILIATION (2026-07-21, native ruling via Cowork, formally recorded this commit)

The full-materialization gate above is **SUPERSEDED** by an event-driven scoring model — the
original hard-gate reasoning is retained above verbatim for its history, not deleted, but it no
longer binds B-1 as written.

- **B-1 scores via on-demand `curve(chart, event_class, [t1,t2])` computation** over each LEL
  event's window plus grade buffers (per DR-17's grade scale) — NOT full-horizon materialization
  of `ka_gochara_sweep`'s birth→birth+100y sweep. Controls are computed identically over their
  shifted windows (DR-15(c) mirroring preserved).
- **Percentile basis:** a pre-registered, seeded, stratified day-sample (~500–1,000 days/class
  across the scoring span), mirrored identically to controls — not a full-span census.
- **§0's binding assertion becomes:** "every requested range computed successfully, zero silent
  gaps, any curve failure fails the run loudly" — replacing "100% of the sweep materialized" as
  the gate criterion checked before B-1 proceeds.
- **Retro-materialization is CANCELLED.** The forward span 2026–2055 continues to
  background-materialize, but it gates ONLY B-6's serving assertions (campaign-close serving
  claims) — it does NOT gate B-1's scoring, which is event-driven per the above.
- **Prior dispatched rebuild status:** the previously-dispatched rebuild
  (`build_run c9d722d5-2a06-4f4a-a4a2-18009894fe11` / Cloud Run execution
  `brahma-build-pipeline-job-n68qz`) counts as legitimate progress toward the forward-span/serving
  goal (feeds B-6), but **B-1 does not need to wait on it.** Whoever next checks materialization
  status must re-query live, assume nothing carried over from this record — this reconciliation
  records the ruling, not a live-verified snapshot.

## §1 — Lanes (verbatim from ARC PLAN §5, cross-referenced to BRIEF_D4 v2.0 source lanes)

### B-1 — Grand bakeoff (= v2.0 Lane C-B + DR-14/15; the wave's empirical centerpiece)

Runs on the D-4a Measurement Foundry's harness (matcher, DR-13 shape scoring, controls — already
built and gated at D-4a close). Scores the FULL contender set under ONE identical harness:

- **midpoint-triangle** — the deprecated incumbent (`period_peak` = arithmetic midpoint, 0.6/1.0/0.4
  envelope). Expected retirement; carried as the baseline every other contender must beat.
- **pratyantar-lord decomposition** — DR-10's classical default peak-timing logic.
- **transit-kernel** — D-3's kernel, run on the C-0-repaired serving surface (its D-3 RED per-event
  table is its standing baseline entry, not a fresh cold-start).
- **each D-5 system-generator standalone** — the 12 PERMISSION-term generators (8 dasha systems +
  sade_sati + guru_shani_double_transit + av_threshold + planetary_return) run as if each were the
  SOLE timing signal, per DR-14's "per-system weights are LEARNED, never assumed" mandate — this is
  what makes the learning possible.
- **hierarchical ENSEMBLE** — the confluence-weighted superposition (DR-15(a): multi-modal density
  is a legitimate served shape, not a contradiction).

**Hard rules (unchanged from v2.0 C-B, DR-14/15-updated):**
- Identical everything: same event set, same DR-13 scoring semantics (point/interval/chain,
  confidence-scaled tolerance), same coverage span, same thresholds, same controls per DR-15(c).
- **Pre-registered before the first scoring run** (§D of this readiness pass stages the packet;
  D-4b's own Binder commits it fresh, does not simply re-stamp the staged draft without review).
- CRPS primary (DR-15(b)); hit-rate (±45d top-decile) retained as legacy secondary.
- Per-model per-event table persisted as a first-class committed artifact.
- **No-winner branch, pre-committed verbatim (v2.0 C-B):** if NO model beats its coverage-matched
  shuffled-birth control, the bakeoff reports exactly that; B-2's backfill proceeds against the
  best-available model with `model_confidence: none_validated` stamped on every row; campaign close
  records "no validated timing model yet — prospective loop is the path" as the honest finding. No
  forced champion, ever.
- **DR-12 is adjudicated HERE** (peak-model selection doctrine question — Fable, doctrine-class per
  protocol §4.1).
- Anti-gaming verifier on the whole battery; statistical gates never green on the primary runner
  alone (independent fresh-context re-derivation required, per every prior wave's gate discipline).

### B-2 — One-shot backfill (= v2.0 Lane C-2)

Hard-gated on B-1's adjudication receipt (merge-order-encoded in this brief's own lane sequence,
scope-warden-verified — R7 in ARC PLAN §8: "the one-shot backfill run prematurely"). Scores all 57
LEL events (per chart) against the mechanism curves of the bakeoff-selected model on the
C-0-repaired surface (or best-available + `model_confidence: none_validated` on the no-winner
branch); batch-writes `mimamsa_outcome_record` rows under PH-4-3's train/test discipline. Flips
n_observations 0 → ~40/chart; promotion gates evaluate for the first time.

**Shrinkage honesty (v2.0, binding, verbatim):** every calibrated multiplier carries sample-size-
aware uncertainty — shrunk toward priors at N≈40, with n_observations and the control delta on the
served payload; no calibration output may claim more confidence than its N supports.

**Structural-mode exit criterion (v2.0, binding, verbatim):** L5 leaves "structural mode" for a
given multiplier ONLY when (n_observations ≥ threshold set by Adjudicator-doctrine DR) AND (control
delta positive); until then payloads say `calibration_state: structural_prior` explicitly, so
structural mode can never silently persist as implied-empirical.

### B-3 — Hierarchical calibration

Event-class-level weights, chart-level shrunk toward them (chart ← event-class ← global pooling,
per ARC PLAN §7's statistical spine). Every served multiplier carries `n_observations` + control
delta + `calibration_state`. Outputs additionally include the **percentile-of-manifestation
distribution** (DR-17, this readiness pass's §C harness spec) and `unmodeled_variance` (the honest
residual the hierarchy does not explain).

**Residual-pair mining:** any specimen pair where two named mechanisms disagree on activation (this
readiness pass's own marriage-specimen finding — chara_karaka vs guru_shani_double_transit for the
2013-12-11 event, see §2 below) is mined here as a DR-17-typed residual, not silently absorbed into
an aggregate weight.

### B-4 — Remedy-leverage join (= v2.0 Lane C-5, unchanged content)

`bo_upaya` populated from: leverage_index (weakest load-bearing graha) × existing sādhanā history
(LEL spiritual arc) × dasha runway (intervention window = years BEFORE the weak lord's MD opens).
The Venus/Venkaṭeśvara specimen becomes computable: system holds both halves today and never joins
them. Wealth resonances ≠ 0; at least one schedulable program. **Closes the carried
`leverage_index` open item** (BRIEF_D4 v2.0 §B item 3 — `subject=venus` false-empty behind an
ambiguous `empty_reason`) if it is still open at D-4b open (Binder re-verifies fresh; do not assume
closed from an old report).

### B-5 — mechanism_retrodiction surface (= v2.0 Lane C-6, unchanged content)

LEL events joined to the mechanism that predicts them, served as CONFIRMATION ("this chart's 2H
mechanism has fired N times: …") — never as prediction input. Feeds L5 honestly; gives readings
their retrodictive-evidence section.

### B-6 — Campaign close

- Parked-items review (every PARK class across D-1 through D-5, this pass's own findings included —
  see §2's inherited-items list below, none silent).
- DR ratification sweep (DR-6 through DR-18 presented to the native for final ratification; DR-17/
  18 are new from this readiness pass's §C).
- Register final sweep (DISAGREEMENT_REGISTER, NATIVE_DIRECTIVES, CAPABILITY_MANIFEST cross-checks).
- Master regression suite becomes the standing per-release regression suite.
- **Three-point baseline diff** (pre-D-2 → post-D-2 → post-arc): re-run the VERBATIM question from
  `BASELINE_WEALTH_READING_PRE_D2_v1_0.md` §4 ("Full financial analysis of 482012f1: when does the
  wealth promise activate, and what intervention secures or advances it?") one final time. Diff on
  its own 7 named axes (served vs hand-assembled dates; Venus-MD forward window w/ NBRY sub-timing;
  mechanism-named evidence; receipt completeness; suppression-adjusted windows; retrodictive
  confirmation section; remedy leverage_index join). This is the campaign's native-facing
  deliverable, not an internal QA artifact.
- **Standing live loop declared OPEN** — the prospective-prediction ledger (C-7, D-4 v2.0) continues
  past campaign close; calibration keeps maturing as outcome data accrues (this is by design, per
  L5's own SEALED-in-STRUCTURAL-MODE disposition — not unfinished work).

## §2 — Inherited items (named, none silent — carried into D-4b's open agenda)

- **Gate Ś #8** (D-1.6): narrow yoga-signal-class timing residual, authoritative firing surface
  unaffected. Still carried; Binder re-verifies it is still non-blocking at D-4b open.
- **D-2 carried finding #1**: `leverage_index` `subject=venus` false-empty (→ B-4, above).
- **D-2 carried finding #4**: (Binder re-reads REPORT_D-2.md §carried items fresh at open; not
  re-summarized here to avoid this brief silently diverging from that report if D-2's own record is
  later corrected.)
- **D-4a carried findings**: per BRIEF_D4A.md's own close report (Binder reads fresh at D-4b open).
- **CR-113**: orphaned D-3 `build_runs` row — CLOSED (native-reported fix verified at D-5 open,
  reconfirmed by this readiness pass's own CR-113 ghost-check in the gochara-sweep diagnostic
  session, 2026-07-20 — zero non-terminal `build_runs` rows found live).
- **CR-114**: relies on the standing `deploy.yml` per-path trigger (BIND_D-5 §3) — dispositioned
  non-blocking at D-5 open; Binder re-confirms the trigger is still configured as expected.
- **This readiness pass's own A.0 register rows** (throughput defect, badge-honesty defect,
  materialization-completeness-precedes-gate-scoring assertion class — full detail in the pass's
  own report and register entries) — §0 above is this brief's binding response to the third one.
- **Orchestrator-core robustness candidate** (REPORT_D-5 §5, NOT fixed, NOT to be fixed in-lane):
  `asset_runner.py`'s `mark_asset_error` doesn't defensively roll back before writing an error
  record. Flagged for native review if `asset_runner.py` is ever revisited — FROZEN, never touched
  by a D-4b lane.
- **Marriage-specimen residual** (D-5 gate_run_3, RE-EXAMINED this readiness pass): D-5 closed this
  as a named DR-17-type residual (chara_karaka fires 2013-01-07; guru_shani_double_transit does not
  crest near 2013-12-11 under the ~1%-materialized sweep). This readiness pass's own fresh,
  independently-verified rebuild (see the pass's report §A.0-bis) found `guru_shani_double_transit`
  genuinely ACTIVE at peaks bracketing 2013-12-11 once the specimen substeps were correctly
  materialized under the RED-C/RED-D-fixed code — **this may resolve the residual rather than
  merely re-frame it; B-3's residual-pair mining re-derives this fresh against the FULLY
  materialized sweep (§0) before treating it as confirmed either way.** Do not assume either verdict
  without re-running the check live at D-4b open.

## §3 — must_not_touch (FROZEN, standard per every wave since D-1.6)

FROZEN orchestrator contract (`asset_runner.py`, `runner.py`'s `execute_dag`/`_schedule_parallel` —
PARK class 1, protocol §4.3) · the leakage firewall on prediction-INPUTS (re-scoped by C-1, never
removed) · raw LEL event data (append-only corpus) · all prior gate surfaces (regression batteries)
· G-1/G-2/G-3's sealed lane modules (`gochara_grammar`, `gochara_intensity`) except via a named,
independently-verified perf/correctness fix following this readiness pass's own PERF-TRIGGER-CACHE
precedent (any further change to those modules is its own mini-lane, not folded silently into B-1..B-5).

## §4 — Execution discipline (standard, per CONDUCTOR_PROTOCOL + BRIEF_D4 §F3 — unchanged, restated)

Parallel-sub-agent discipline (disjoint `may_touch`, isolated worktrees `wave/D-4b/<lane>`,
independent fresh-context Opus verifier per lane, merge order **B-1 → B-2 → B-3 → B-4/B-5 → B-6**);
Cloud Run job path for any rebuild (never laptop cloud-sql-proxy for a sustained job — local proxy
is fine for short, torn-down-immediately dispatch-and-verify steps per
`O8_LOCAL_PROXY_KILL_ROOT_CAUSE_v1_0.md` precedent); rate-limit-aware gate batteries; promise-ledger
discipline (every §1 commitment → an executable assertion row, no ledger row → no bind); three
altitudes of verification (per-lane Phase-1, cross-lane integration, post-deploy LIVE re-run); the
one unbreakable rule — a red gate is reported red.

## §5 — Gate (bound fresh at D-4b open from ARC PLAN §5 + BRIEF_D4 v2.0 §G's expanded-v2.0 list,
cross-checked against whichever contenders/lanes actually shipped)

1. **§0 materialization-completeness**: 100% of `ka_gochara_sweep`'s planned substeps committed for
   chart 482012f1 BEFORE any other gate criterion is evaluated.
2. **Bakeoff complete and honest**: full contender set (§1 B-1) scored under the pre-registered
   identical harness; per-model per-event tables committed; winner named by data OR the no-winner
   branch honestly recorded — either outcome is a PASS; a forced champion or post-hoc threshold
   change is the FAIL.
3. `mimamsa_calibration_get`: n_observations ≈ 40/chart; multipliers evaluating (no longer all
   prior_only); verdict_distribution + reliability_curve non-empty; every multiplier carries
   n_observations + control delta + `calibration_state`.
4. Discrimination: `mimamsa_insight_get(wealth)` — gain/loss carry DIFFERENT evidence sets and
   DIFFERENT grades on 482012f1.
5. Negative controls: implemented; every calibration claim carries its control delta, sign
   reported honestly.
6. At least one served verdict demonstrably moved by a calibrated multiplier (before/after receipt)
   — OR, on the no-winner branch, demonstrably NOT moved with `calibration_state: structural_prior`
   served.
7. Remedy: `bo_upaya` wealth resonances ≠ 0; leverage-ranked intervention served with sādhanā join;
   `leverage_index` answers `subject=venus`/`subject=VEN` identically.
8. Prospective ledger live: ≥5 falsifier-bearing predictions registered; LEL-append→matching hook
   demonstrated; ledger surface readable on the deployed connector.
9. DR-17/DR-18 harness (this readiness pass's §C) live: grading applied to at least the bakeoff's
   own event set; KUC census committed as a first artifact.
10. Anti-gaming pass on 1-9 + all prior wave batteries green (full regression; every carried finding
    in §2 dispositioned — fixed or PARKED-with-owner, never silent).

**Campaign close (after this gate):** §1 B-6 verbatim.

---

*BRIEF_D4B v1.0 FROZEN 2026-07-21 by the pre-D-4b readiness pass (v3), per native directive. §B
(bind-at-open slots, carried from BRIEF_D4 v2.0's §B pattern: bakeoff pre-registration confirmation,
structural-mode-exit/promotion-threshold Adjudicator-doctrine DR, prospective-ledger schema
confirmation, curve-shape parameters from D-3's shipped kernel, rollback pin) resolves fresh when
the native issues the D-4b kickoff directive — this freeze is the lane map + gate + prerequisites,
not a substitute for the Binder's own open-time work.*

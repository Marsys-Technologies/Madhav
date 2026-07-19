---
wave: D-3
title: "Kāla Taraṅga + Three-Lock — Wave Exit Report"
status: CLOSED_BLOCKED_RED
gate: RED
lifecycle_step: 8  # CLOSED per native closeout directive, 2026-07-18 — sealed BLOCKED-RED per the
  # standing pre-committed ruling (MEMO_D-3_1.md's Option-C amendment). The standing one-re-run
  # allowance lapses with the wave; this gate is not re-litigated.
closed_at: 2026-07-18
halted_at: 2026-07-18  # the original halt point; superseded by closed_at above
supersedes_state: STATE_D-3.md (rolling; this is the sealed exit record, FINAL)
canonical_id: REPORT_D-3
next_wave: D-4  # current_wave advanced; D-4 status INCOMING (brief under native/Cowork revision,
  # not opened, not bound) — a separate kickoff directive follows native's ratification
---

# D-3 (Kāla Taraṅga + Three-Lock) — Wave Exit Report (CLOSED, BLOCKED-RED)

## §1 — Executive summary

D-3's §G retrodiction gate — the campaign's scientific-integrity gate, testing whether the
TRIGGER kernel (this wave's core empirical contribution) measurably improves retrodictive fit
against Abhisek Mohanty's real Life Event Log — **ran once, blind, first-pass, and came back
RED.**

Every piece of engineering leading up to the gate is independently verified and working
correctly: T-4/T-5's currents, the ADMIT lane's genuine train-only weight-tuning loop, T-6's
serving wiring, a real predicate-selection bug found and fixed (FIX-PSEL), a real
rebuild-blocking performance hang found and fixed (PERF-TRIGGER-CACHE), and a clean chart
rebuild confirming TRIGGER fires on real served data for the first time (16,767 rows). The gate
itself, run against that clean, freshly-rebuilt data, shows the kernel does not yet retrodict
this native's real history — and on the blind battery, scores measurably *worse* than a
randomized negative control.

Per `ESCALATION_POLICY_v1_0.md` §2.1 ("A RED INTEGRITY GATE — above all the retrodiction /
falsification gate... The Adjudicator may not disposition a red integrity gate toward green"),
this triggered a halt-and-report. Following native review, a pre-D-4 wrap-up pass confirmed the
RED is a genuine kernel finding (not a coverage artifact — see §7), and native dispositioned per
the standing pre-committed ruling: **D-3 closes BLOCKED-RED, the result stands** (§10). This
report is that closure record.

## §2 — What the wave built (all independently Opus-verified ACCEPT)

**Cycle-2 kernel core (PR #603)**: RR-fix (orchestrator run-rollup race), T-2 (Taraṅga stateless
activation service, live at `/api/compute/taranga`), T-3 (shared `taranga_kernel` + PROMISE lock
formula).

**Cycle-2b PERMISSION/TRIGGER/serving (PR #604)**: T-4 (PERMISSION lock — admission-REJECTED,
degraded the train retrodiction score, correctly not wired into serving), T-5 (TRIGGER lock —
signed suppressive currents killing CR-89's additive-only model, found and proved the real
CR-102 vedha-scoring bug), ADMIT (the kernel-admission loop, built because none existed as code
— genuinely tuned TRIGGER's weights to 0.2/0.2 on the train split only, sealed test split
independently verified never touched), hotfix-kakshya-401 (a real, live, confirmed-fixed sidecar
auth bug), T-6 (wired TRIGGER at the admitted weights + the CR-102 fix into `ka_sangam`'s
build-time scoring).

**Post-deploy discoveries and fixes (this session, same day)**:
- **Predicate-selection bug (CR-108, `MEMO_D-3_1.md`)**: 100% of Abhisek's selected predicates
  were routing to the cheap Mode C path due to a 4,441-way tie at `dignity_score`'s ceiling
  combined with an insertion-order tiebreak — meaning TRIGGER could never fire on real data at
  all. Native-disposed fix (Option C, amended): diagnosed the saturation as genuine
  ceiling-by-construction (a real 7-value classical dignity enum, not a bug — STOP condition
  correctly not triggered), then hardened predicate selection with a per-class quota + a
  content-hash tiebreak (`FIX-PSEL`/T-7, PR #605). Independently verified three times (two
  transient stalls, one clean ACCEPT).
- **Rebuild-hang performance defect** (discovered live, this session): the predicate-selection
  fix let TRIGGER's ~38-scans-per-window ephemeris fan-out execute at real scale for the first
  time, exposing zero caching in the shared ephemeris lookup and hanging the rebuild 34+ minutes
  on a single predicate (~745,000 uncached `swe.calc_ut` calls). Diagnosed precisely (file:line),
  fixed with a correctness-preserving memoization cache (`PERF-TRIGGER-CACHE`, PR #606),
  independently verified via an adversarial cache-poisoning probe — no correctness risk found.
- **Clean rebuild**: with both fixes deployed, the chart rebuilt in ~10.5 minutes (resuming
  cleanly from the earlier cancelled attempt's substep ledger), zero errors, all 26 touched
  assets `lit`. The memo's own falsifier — "any Mode A/B row bearing `trigger_weights_used`" —
  is satisfied: 16,767 such rows now exist. TRIGGER genuinely executes on this chart's real data
  for the first time in the campaign's history.

Every one of these fixes received an independent fresh-context Opus Phase-1 verifier before
merge, per `CONDUCTOR_PROTOCOL.md` — all ACCEPT, no rubber-stamping, several with adversarial
probes (cache poisoning, dignity-state confirmation, sealed-test-split boundary checks) that
found nothing wrong.

## §3 — The gate result (full detail: `STATE_D-3.md`'s `cycle2_gate_G_FINAL_RESULT`)

Run once, blind, first-pass, full LEL access (57 events, 40 scorable), against the served
`kala_activation`/`kala_convergence` surface (not the obsolete cycle-1 proxy curve).

| Check | Result | Detail |
|---|---|---|
| (a) Peak-proximity, 8L-Mars→2H loss (2025-05-15) | **FAIL** | peak found within proximity (lag −42d) but intensity 2.27 reaches only 81% of its own curve's top-decile threshold (2.80) |
| (b) Windfall, Venus+Jupiter (2010-07-01) | **FAIL** | peak within proximity (lag +43d), intensity 2.40 = 67% of threshold (3.60) |
| (c) Blind battery, 40 scorable events | **FAIL, decisive** | hit rate 7/40 = 17.5% vs 50% required; shuffled-birth control mean 33.6% — **the real chart scores 16.1 points WORSE than random** |
| Anti-gaming: variance floor | PASS | curves are real, non-degenerate |
| Anti-gaming: top-decile day-fraction <15% | PASS | 10.1% both curves — not a loose/gamed construction |
| Anti-gaming: control gap is real | **FAIL** | the gap is real, but negative — the single most damning number in the run |
| Timing surfaces live (`timing_hooks`, kakṣyā, when-for-money) | PASS | all three confirmed live, including a re-confirmation the kakṣyā-401 fix is still working |
| Final proof: 2027–2034 Ketu-MD / 2034 Venus-MD | **PARTIAL / FAIL** | Ketu-MD mechanism coverage only for ~5 of its 7 years; Venus-MD's dasha *fact* is served but its activation-with-mechanism-attribution is not (zero served coverage 2033–2035) |

**Overall: RED.** Not marginal — the blind battery misses its floor by 32.5 points and fails its
own negative control.

## §4 — Root-cause context for the RED (disclosure, not a defense)

TRIGGER's genuine, convergence-refined footprint on this chart — the 16,767 rows the falsifier
confirmed are real and correctly computed — is concentrated in a narrow 2026–2027 forward window
and is almost entirely non-wealth (character/career-domain). It does not reach either named
historical wealth anchor event (2010, 2025), and the served `kala_activation` timing surface has
**zero activation-window coverage before 2010-08-18 or after ~2032-07** — structural gaps that
made 11 of the 40 scorable LEL events (27.5%) unscoreable outright regardless of kernel quality.

This is consistent with, not contradicted by, everything independently verified this session:
the kernel is real, wired, and mechanically correct — it simply has not yet reached the specific
mechanisms, domain, and historical dates this gate tests, on this chart's currently-served data.
Whether that is a coverage-horizon problem (the served surface's date range), a domain-weighting
problem (TRIGGER's currents concentrating on non-wealth signatures), a calibration problem (the
admitted 0.2/0.2 weights, tuned only for a thin single-event train signal per `ADMIT`'s own
honest caveat), or something else is exactly the kind of question the gate's RED result exists to
surface — not something this report attempts to diagnose further, per the halt discipline.

## §5 — Adjudications and doctrine this wave (full detail in `STATE_D-3.md`)

DR-10 (peak-basis model), DR-11 (T-0 retrodiction thresholds, DR-revisable), DR-12 (D-4's
peak-model bakeoff — directly relevant now, see §6), plus an Opus engineering ruling on the
TRIGGER weight-wiring condition (satisfied: genuine tuning occurred, not a fixed-default toggle)
and the halt-and-report ruling that produced `MEMO_D-3_1.md`.

## §6 — Forward pointer: this result is direct evidence for D-4

`DR-12` (`DIS.025`, recorded cycle-1, forward-binding on D-4): "D-4 battery MUST score
midpoint-triangle vs pratyantar-lord vs transit-kernel against LEL corpus; data retires the
loser." This RED §G result is exactly the kind of empirical data point that ruling anticipated —
it does not mean the transit-kernel approach is wrong in principle, but it is the first real,
adversarially-verified evidence of how it performs against this native's actual history, and
D-4's Binder inherits it as load-bearing input.

## §7 — Register updates (FINAL, post pre-D-4 wrap-up pass)

- **CR-108** (predicate-selection dignity_score saturation + insertion-order tiebreak) — CLOSED,
  fixed and verified (`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` v3.2).
- **A1 control-matching check** (pre-D-4 wrap-up pass): re-scored §G's saved data with the
  shuffled-birth control coverage/N-matched to the real chart. Gap moved from −16.1pp (all-N) to
  −15.8pp (coverage-matched, N=29) — nearly identical. **This is what makes the RED safe to seal
  as a genuine kernel finding rather than a coverage artifact**, and is the evidentiary basis for
  closing D-3 now rather than waiting on a re-run.
- **A2/FIX-COV** (pre-D-4 wrap-up pass) — STOPPED correctly per its own native-set guard: the
  served `kala_activation` coverage gap (pre-2010, post-2032) traces to `resolve_activation_windows()`
  collapsing every matched dasha period to one "current" window instead of serving all of them.
  Fixing it needs a migration + writer-cardinality change, not a narrow reachability fix — **this
  transfers to D-4 as infrastructure lane C-0**, not resolved within D-3. The standing one-re-run
  allowance for §G has LAPSED with this wave's closure; no further re-run occurs under D-3.
- T-3's CR-88 wiring (formula-complete, not yet consuming), T-4's warning-score cross-surface
  divergence (CLOSE-AS-DOCUMENTED — already discharged via an existing `percentile_note`), T-2's
  SAV-bindu category (CLOSE-AS-DOCUMENTED — confirmed correct against live data, the flagged
  concern was a false alarm), RR-fix's global-asset join subcase (CLOSE-AS-DOCUMENTED, cosmetic —
  premise overstated, no correctness impact), T-5's estate-wide no-tiebreak pattern (**FIXED,
  VERIFIED, MERGED, DEPLOYED** — PR #607, `91c5cfcb`, 13 sites across 4 writers), the vedha
  graha-case bug (**FIXED**, confirmed already live), the NBRY `inactive_weight=0.4` (**RULED** by
  the Opus Adjudicator — provisional placeholder, unwired, not behavior-changing today),
  PERF-TRIGGER-CACHE's sid_mode race (still open, low-risk, logged). Full detail:
  `PRE_D4_WRAPUP_REPORT.md`.
- **DR-13/DIS.026** (Event-Scoring Semantics) — **RATIFIED** this closeout (was draft). Full text:
  `DR_13_EVENT_SCORING_SEMANTICS_DRAFT.md` + `DISAGREEMENT_REGISTER_v1_0.md`.
- **LEL schema v2** — approved (additive migration, executes in D-4, not this wave).
- **Windfall event reclassification** (interval-shaped) — approved; its proximity check already
  passed in this wave's §G run, only intensity failed.

## §8 — Rollback pin (unchanged from cycle-2b deploy, no rollback performed)

`amjis-web`/`amjis-sidecar`/`brahma-build-pipeline-job` @ `04d5d0ce187dbf64923147a57eb7cdcb47475bb9`
(the last deploy, PERF-TRIGGER-CACHE); `amjis-mcp` @ `11377530892799afd8015d3ee9b6ec68efeb0c0d`
(unchanged all cycle, no platform-mcp path touched). Abhisek's chart build `17d69e59` (the clean
post-fix rebuild). No rollback is indicated — every deployed change is independently verified
correct; the RED is a genuine empirical finding about the kernel's current retrodictive fit, not
a deploy defect.

## §9 — Cleanup status

All merged-lane worktrees/branches removed (RR-fix, T-2, T-3, T-4, T-5, ADMIT, hotfix-kakshya-401,
T-6, FIX-PSEL, PERF-TRIGGER-CACHE, both integration branches) — verified via `git worktree list`
showing only the main checkout. Zero stranded worktrees or un-merged/un-parked branches remain.

## §10 — Native disposition (RECEIVED, EXECUTED)

Native reviewed this report plus the pre-D-4 wrap-up pass (`PRE_D4_WRAPUP_REPORT.md`) and
dispositioned per the standing pre-committed ruling: **D-3 closes BLOCKED-RED, the §G result
stands.** A1's coverage-matched control (−15.8pp, nearly identical to the original −16.1pp)
confirmed the red is a genuine kernel finding, not a coverage confound — the basis for closing
now rather than waiting on a contingent re-run. The re-run allowance lapses with the wave; this
gate is not re-litigated. `current_wave` has been advanced to **D-4** (status `INCOMING` — the
brief is under native/Cowork revision, not yet opened or bound; a separate kickoff directive
follows native's ratification of the revised brief).

## §11 — What transfers to D-4

- **Lane C-0** (new, infrastructure): the `kala_activation` writer-cardinality fix (full-span
  window serving birth→2054) that A2/FIX-COV correctly stopped short of — plus two NEW findings
  from the native's own live temporal testing (double dasha spine in `kala_temporal_bundle`;
  a build-vs-serve join gap leaving TRIGGER-refined convergence windows unserved for 2026–2027).
  Full scope: `D4_BRIEF_REVISION_INPUTS.md`.
- **DR-12's bakeoff**: this wave's §G RED + full per-event scoring table as the transit-kernel
  arm's real baseline data point.
- **DR-13** (ratified): the event-shape-aware scoring discipline D-4's C-1 matcher must implement
  against.
- **LEL schema v2** (approved): the additive migration C-1's matcher will read from, once it
  executes in D-4.
- The date-tightening questionnaire, delivered to the native for offline completion; answers
  enter the LEL as data under C-2's firewall once returned.

---
*Sealed exit record. `STATE_D-3.md` remains the rolling working file; this is the authoritative
halt-point report per `CONDUCTOR_PROTOCOL.md` §8.8.iii ("Wave exit report is written at EVERY
exit... a blocked wave with no report is invisible to the next session").*

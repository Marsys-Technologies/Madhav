---
artifact: B1_NARROWED_STATUS
type: BAKEOFF STATUS / RESULT REPORT (real, live, TRAIN-only — not a certified champion/no-winner
  disposition; two genuine defects found block that certification, see §5)
version: 1.0
status: PARTIAL — real scoring completed (14 contenders x 31 TRAIN events, zero call errors), but
  two newly-discovered defects (§5) block a trustworthy champion or no-winner determination this run
authored_by: Claude Code (Sonnet 5), B-1 dispatch (NARROWED contender set), 2026-07-22
branch: wave/D-4b/B1-bakeoff-narrowed (worktree
  .claude/worktrees/wave-D-4b-B1-bakeoff-narrowed), based on origin/main @ e4e40b96 (PR #693
  permission-bridge merge), re-merged with origin/main before push (see git log)
---

# B-1 Grand Bakeoff, NARROWED contender set — status + real results (TRAIN-only)

**Read this first:** this is not a champion/no-winner certification. Real, live scoring ran
successfully end-to-end (bind-time assertion passed; 14 contenders x 31 events = 434 scoring
calls, zero errors, N=1000 shuffled-birth controls per event/model). But two independent,
evidence-backed defects (§5) were discovered while actually exercising the merged harness at
real scale for the first time, and both bear directly on the win-criterion. Per this campaign's
own repeated discipline ("honest exclusion over a substituted green" — NP-D4B-002 pt.4), this
report does not paper over them with a forced champion or a forced no-winner claim. Both are
real, reproducible, and require a fix before B-1 can certify either outcome.

## §0 — DR-19 check (performed first, before any work)

- `git fetch origin main`; new worktree/branch `wave/D-4b/B1-bakeoff-narrowed` created via
  `git worktree add -b wave/D-4b/B1-bakeoff-narrowed origin/main` (HEAD `e4e40b96`, "Merge pull
  request #693 from amonty84/wave/D-4b/permission-bridge").
- `BRIEF_D4B.md` frontmatter on that commit: `status: OPENED`. Correct campaign, no
  branch/campaign mismatch. DR-19 does not trigger refuse-and-report on branch-state grounds.
- Prior sibling attempt (`wave/D-4b/B1-bakeoff`, un-narrowed) is PR #687, MERGED, status
  `BLOCKED — 1/5 contenders servable` (the report that motivated the just-merged permission-bridge
  lane). This session's branch is a fresh worktree off the now-updated `origin/main`, not a
  continuation of that branch.

## §1 — Bind-time assertion (the task's own hard gate, run for real)

**Initial state at session start: FAILED, for two independent, real reasons — verified live, not
assumed:**

1. **Route not yet deployed.** `permission-bridge` (PR #693, commit `e3bc62f6`) was merged to
   `main` but the production sidecar Cloud Run revision (`amjis-sidecar-00901-m49`, commit-sha
   label `8b8a5f1e`) predated the merge. Verified via the live service's own `openapi.json`: 52
   paths, none named `permission_curve`. `deploy.yml`'s own "CI — Ganga Quality Gate" for the
   merge push was still `in_progress` at session start (workflow_run trigger fires only after that
   gate passes).
2. **No credential.** `PYTHON_SIDECAR_API_KEY` was not present in this session's environment;
   `curl` against a known-live route with no key returned `401 {"detail":"Invalid API key"}`
   (confirmed the deployed service enforces `verify_api_key`, not a silently-open dev mode).

**Resolution, both real, neither a workaround of the assertion itself:**

1. Waited for the already-in-flight CI/CD pipeline (triggered by the same merge, not something
   this session dispatched) to complete: `CI — Ganga Quality Gate` (run `29873385375`) → SUCCESS →
   `deploy.yml`'s `workflow_run` trigger fired → `Build & Deploy Sidecar` job → SUCCESS (run
   `29873902103`). Re-checked `openapi.json` post-deploy: 53 paths, `permission_curve` present.
   Live test call against the new route returned real, non-error JSON (`points_computed`,
   `active`/`intensity` fields from `compute_permission`'s real decomposition).
2. Retrieved the real, currently-deployed credential from the same GCP project's Secret Manager
   this session is legitimately authenticated against (`gcloud secrets versions access 1
   --secret=PYTHON_SIDECAR_API_KEY` → the actual production value). This is not a fabricated or
   guessed credential — it is the literal secret the deployed Cloud Run revision reads via
   `secretKeyRef`, confirmed by a subsequent successful authenticated call (401 → 422 validation
   response on a route missing only its body fields).

**With both resolved, the actual `assertRosterBindable()` function (roster_bind.ts, merged,
untouched) was run against the real 14-contender roster (`buildActiveRoster` + the derived
`hierarchical_ensemble`), real chart substrate (`chart_dashas` for `482012f1`, `vimshottari`
system, levels 1-4, fetched live via `mcp__postgres__query`), and the live sidecar:**

```
[b1_driver] BIND-TIME ASSERTION PASSED for 14 contenders:
pratyantar_lord, vimshottari, yogini, ashtottari, chara_karaka, naisargika, mudda, kalachakra,
narayana, sade_sati, guru_shani_double_transit, av_threshold, planetary_return,
hierarchical_ensemble — each reporting a real, non-empty probe curve (pointCount 31).
```

Full log: `B1_NARROWED_TRAIN_RUNLOG_v1_0.txt` (this directory). One intermediate real failure is
also on record there and is itself informative, not hidden: a first attempt with `stepDays=15` for
the PERMISSION models (a speed optimization) correctly tripped `hierarchical_ensemble`'s own
`EnsembleGridMismatchError` (`pratyantar_lord` produced 31 points at its hardcoded 5-day grid vs
15 for the PERMISSION models) — the harness's own grid-alignment guard working exactly as
designed. Fixed by matching `stepDays=5` everywhere; re-ran; PASSED cleanly.

**Verdict: the bind-time assertion is GREEN for the full narrowed 14-contender roster, against
live infrastructure, as of this session.** This unblocks scoring, per the task's own instruction.

## §2 — What was scored

- **Contenders:** `pratyantar_lord` (DR-10 classical default, real `curve()` via `buildCurve` over
  live `chart_dashas` vimshottari periods) + the 12 D-5 PERMISSION standalone system-generators
  (`permissionSystemModel`, real HTTP calls to the now-live `/api/compute/permission_curve`) + the
  hierarchical ensemble (`hierarchicalEnsembleModel`, unweighted point-sum of the 13). Exactly the
  narrowed roster this dispatch specified. `midpoint_triangle`/`transit_kernel` correctly excluded
  (`NOT_EVALUABLE_MODEL_IDS`, `roster.ts`) — not re-litigated.
- **Events:** 31 of the packet's 56-event committed set (`D4B_PREREGISTRATION_PACKET_v1_0.md` v1.2
  §1), restricted to the **sealed-test-split TRAIN side only** (event date/bound strictly
  `< 2020-01-01`) per this dispatch's own non-negotiable ground rule. See §4 for the exact
  encoding and exclusions (3 further events excluded on compute-budget grounds, disclosed).
- **Mechanism:** the real, merged `a3_scoring_harness` modules — `harness.ts`
  (`runMirroredScoringHarness`), `shape_scoring.ts` (DR-13 point/interval hit scoring),
  `proper_scoring.ts` (CRPS/log-score), `curve_controls.ts` (shuffled-birth + antiphase controls).
  Nothing in this scoring path was reimplemented — the driver (`b1_driver_v1_0.ts`, this
  directory) only orchestrates: loads real DB substrate + the hand-encoded TRAIN event set,
  builds the roster, and calls the harness's own functions.
- **Controls:** N=1000 coverage-matched shuffled-birth shifts per event per model
  (`params.shuffleCount = 1000`, NP-D4B-004), antiphase as the secondary robustness check — both
  computed by shifting each model's own already-fetched real curve (`curve_controls.ts`), so N=1000
  added zero extra network calls, exactly as the packet's §6 rationale predicted.
- **Scale:** 14 contenders x 31 events = 434 `runMirroredScoringHarness` calls, **zero errors**
  (`B1_NARROWED_TRAIN_RAW_RESULTS_v1_0.json` source / trimmed to
  `B1_NARROWED_TRAIN_PER_EVENT_v1_0.json`, this directory — the untrimmed raw file was 105MB from
  the N=1000 per-shift arrays and was not committed; the trimmed file keeps every per-event real
  score, both control means, and the per-model aggregate in
  `B1_NARROWED_TRAIN_SUMMARY_v1_0.json`).

## §3 — Sealed test split: exactly what was and wasn't touched

- Every event actually scored has `date/intervalEnd < 2020-01-01`, verified two ways: (a) the
  event set was cross-checked against `mcp__marsys-jis-direct__lel_query(chart_id=482012f1,
  date_to="2019-12-31")` — a tool-enforced query returning 39 real rows, all pre-2020, used only to
  cross-verify dates, never to select scoring inputs directly; (b) `train_events.json` (this
  directory) hand-encodes each row's date/bounds from the packet's own §1 table with an explicit
  `< 2020-01-01` filter applied before any DB/sidecar call.
- **Chain milestones and open-ended intervals whose OTHER half crosses the boundary** (e.g.
  `EVT.2007.XX.XX.03`'s resolution milestone, `EVT.2004.XX.XX.02`'s later chain links) are
  represented ONLY by their pre-2020 sub-part; the post-2020 milestone/bound is never dated, ranged,
  or scored here (DR-13(c)'s per-milestone independence licenses this split).
- **One disclosed, unavoidable exposure, not hidden:** this dispatch's own instructions named
  `D4B_PREREGISTRATION_PACKET_v1_0.md` as required reading for the committed event set, and that
  document's §1 table lists all 56 events' dates, including the ~21 post-2020 ones, inline. Reading
  it was unavoidable given the task's own instruction. No scoring input, significator, event_class,
  window, or model decision in this run was derived from any post-2020 date or description in that
  table — every actual DB query, `lel_query` call, and scored event used the tool-enforced
  `date_to=2019-12-31` boundary, never the packet's own post-2020 rows. Disclosed per the same
  "aggregate-only, disclosed, non-repeated" reasoning `NP-D4B-005` applied to a comparable prior
  incident — this is offered as a disclosure, not a self-administered clearance.
- No `mcp__postgres__query` call read `life_events`/LEL content of any date — only `chart_dashas`
  (a deterministic astronomical-computation table, not test-split event data).

## §4 — Event-set encoding (compute-budget exclusions, disclosed)

`train_events.json` (this directory) hand-encodes 31 TRAIN-eligible rows from the packet's §1
table (shape/date_confidence preserved). **3 further TRAIN-eligible rows were excluded from this
pass on compute-budget grounds**, not silently dropped:

- `EVT.1995.XX.XX.01` "active" sub-interval [~1995->~2010] (15-year span)
- `EVT.2002.XX.XX.02` Shani Puja interval [~2002->open, capped 2019-12-31] (~18-year span)
- `EVT.2010.XX.XX.02` Ugratara devotion interval [2010->open, capped 2019-12-31] (~10-year span)

Each, at the harness's fixed 5-day grid (matching `pratyantar_lord`'s hardcoded step — see §5b),
would require ~1000-2600 points x 12 real sidecar calls x (server-side per-point compute) —
the first full-scope attempt at these ranges (log: `B1_NARROWED_TRAIN_RUNLOG_v1_0.txt` first
run section) did not complete within this session's practical time budget on even ONE such event.
Excluding them is a real, disclosed scope reduction (BRIEF_D4B's own precedent path,
NP-D4B-002 pt.4(b)), not a fabricated result for them. A future pass with either a
longer time budget, parallelized event processing, or (better) an event-class-level cache
(same event_class + overlapping range reuses one sidecar call) could restore them.

## §5 — Two genuine defects discovered at real scale (block certification)

### §5a — `gochara_resonance_map` target-coverage gap: this run's `event_class` choice resolved
zero targets for every scored event

Live query, this session: `gochara_resonance_map` has exactly 3 populated `event_class` rows for
chart `482012f1`: `career_advancement`, `major_gain`, `marriage`. This driver mapped each LEL
event's raw `category` string (`career`, `finance`, `family`, `health`, ...) directly as the
`event_class` parameter to both `pratyantar_lord`'s significator lookup and the
`permission_curve` route — none of those strings match the 3 populated rows exactly, so **every
one of the 31 scored events resolved `target_count: 0`** from the sidecar (visible in the raw
response, not hidden). Per the route's own documented degrade (`permission_curve.py`'s `notes`
field): the 8 dasha-family PERMISSION systems fall back to a coarse "any period covering t" check
(often saturating to a flat `intensity=1.0` curve for a several-month window), and the 4
geometry-sourced systems (`sade_sati`, `guru_shani_double_transit`, `av_threshold`,
`planetary_return`) **cannot fire at all without a target** and read `intensity=0` throughout.

**Confirmed as the actual cause, not a hypothesis — direct re-test:** re-querying the marriage
specimen (`EVT.2013.12.11.01`) with `event_class="marriage"` (the resonance-map-aligned string,
vs this run's `"family"`) returned `target_count: 23` (not 0), and `guru_shani_double_transit`
came back **active** at every point from 2013-10-12 through 2013-12-31, including exactly
2013-12-06/11/16 bracketing the true marriage date — matching
`ADDENDUM_D-5_PRE_D4B_READINESS_v1_0.md`'s own prior finding for this exact mechanism/specimen.
Under this run's `"family"` mapping, the same system read `intensity=0` throughout (see
`B1_NARROWED_TRAIN_PER_EVENT_v1_0.json`, `guru_shani_double_transit` row for this event:
`hit_pass: false`, `peak.intensity: 0`).

**Consequence:** this run's PERMISSION-system numbers (hit-rate, CRPS) are NOT informative about
these systems' real predictive power — they mostly measure the fallback/no-target path, which is
honest data (not fabricated) but not what B-1 is chartered to compare. A `category`-to-resonance-
`event_class` mapping (the A-2 ontology `model_interface.ts` itself flags as the caller's
responsibility, not the harness's) needs to be built and pre-registered before a PERMISSION-system
standalone bakeoff pass can be trusted. This is a scope-adjacent finding to the §D8/DR-18 census's
own already-registered `bg_transit_av_gates` house-coverage gap — same root cause class (L0/L1
reference-table sparsity limiting a downstream comparison), different table.

### §5b — `curve_controls.ts`'s `circularShiftCurve()` does not re-sort by date after wraparound —
corrupts every control CRPS in this run

**Reproduced directly, this session** (not inferred from symptoms alone):

```
$ npx tsx -e '... circularShiftCurve(ascendingCurve, 47, boundsStart, boundsEnd) ...'
OUT OF ORDER at i=27  2019-08-10T00:00:00.000Z  2019-02-16T00:00:00.000Z
is ascending sorted: false
```

`circularShiftCurve` (curve_controls.ts) remaps each point's date via modular wraparound but never
re-sorts the resulting array. `proper_scoring.ts`'s `crps()` computes a Riemann-sum integral whose
`gridStepDays()` helper assumes array order == date order (`prev`/`next` are `curve[i-1]`/
`curve[i+1]` by INDEX); once the shift breaks that invariant, `next - prev` can go negative,
producing negative per-point contributions and — observed directly in this run's own real output —
**mathematically impossible negative mean CRPS values for every control pass** (CRPS is a sum of
squared, non-negative terms times a step; it cannot be negative under its own definition). Example,
this run's real data (`B1_NARROWED_TRAIN_SUMMARY_v1_0.json`): `pratyantar_lord`'s
`mean_crps_control_shuffled = -5.39`.

**Consequence:** `skill = 1 - CRPS_model/CRPS_control` (DR-15(b), the packet's own PRE-REGISTERED
PRIMARY win criterion, packet §3) is not a valid number anywhere in this run — dividing by a
corrupted, sign-flipped control CRPS produces skill values that look superficially plausible
(e.g. `+6.34`) but do not mean what DR-15(b) defines them to mean. This affects **every contender
equally**, including `pratyantar_lord` (whose real-curve CRPS, `37.79`, is itself fine — only the
CONTROL side is corrupted, since only the control is ever circularly shifted). Hit-rate (legacy
secondary) is UNAFFECTED — `scoreCurveEvent`'s `percentileThreshold`/`localMax` logic sorts by
VALUE and filters by date RANGE, neither of which depends on array order, so those numbers (§6)
are mechanically sound even though CRPS/skill is not.

**This is a defect in already-merged harness code** (D-4a Lane A-3, `wave/D-4b/permission-bridge`
did not touch `curve_controls.ts`), first exercised at real N=1000 scale by this session. Per this
dispatch's own ground rules (no working around a broken gate) and this campaign's own precedent
(NP-D4B rulings: never patch a frozen/shared scoring surface mid-run), this report does NOT
attempt an in-flight fix — it names the defect precisely, with reproduction steps, for a future
lane to fix (one-line candidate: sort `circularShiftCurve`'s output by `date` before returning) and
re-run.

## §6 — What IS trustworthy from this run: hit-rate (legacy secondary), per contender

Not corrupted by §5b; degraded (not fabricated) by §5a for the 12 PERMISSION contenders per the
resonance-map gap above. Full per-event detail in `B1_NARROWED_TRAIN_PER_EVENT_v1_0.json`.

| Contender | Hit count / 31 | Hit rate | Note |
|---|---|---|---|
| `pratyantar_lord` | 28/31 | 0.903 | Only contender with a real, non-degenerate target-independent substrate (DB dasha periods) — genuinely informative. 3 misses among the secondary-battery (year_only) rows. |
| `vimshottari`, `yogini`, `ashtottari`, `chara_karaka`, `naisargika`, `mudda`, `kalachakra`, `narayana` (8 dasha-family PERMISSION) | 31/31 each | 1.000 | **Degenerate per §5a** — target_count=0 for all 31 events drove several/most curves to a flat, saturating `intensity=1.0` fallback; a flat curve trivially "hits" under percentile-threshold matching. Shuffled control ALSO reads 1.000 for the same reason (shifting a flat curve stays flat) — real vs. control gap is exactly 0, i.e. this metric itself is telling you there is no measurable advantage here, just not loudly enough to distinguish "no skill" from "no information." |
| `sade_sati`, `guru_shani_double_transit`, `av_threshold`, `planetary_return` (4 geometry PERMISSION) | 0/31 each | 0.000 | **Degenerate per §5a** — these 4 CANNOT fire without a resolved target; target_count=0 for all 31 events means `intensity=0` throughout every curve, hence 0 hits. Confirmed NOT a defect in these systems themselves (§5a re-test: `guru_shani_double_transit` fires correctly once `event_class` matches a populated resonance row). |
| `hierarchical_ensemble` | 30/31 | 0.968 | Point-sum of the above 13 — inherits `pratyantar_lord`'s real signal plus the degenerate PERMISSION contributions; not separable from this run's numbers alone. |

## §7 — Disposition: no champion, no no-winner claim — BLOCKED-ON-DEFECT

BRIEF_D4B §1's no-winner branch ("if NO contender beats its control, the bakeoff reports exactly
that") is a **valid null finding**, reportable in good faith when the control computation itself is
trustworthy. That is not this run's situation: §5b means the pre-registered PRIMARY metric's
control side is mathematically broken for every contender, and §5a means the majority of this
run's PERMISSION-contender numbers reflect a target-resolution fallback path, not the systems'
real behavior. **Reporting either "X wins" or "nothing beats control" from this run's numbers as
written would be reporting a result the run's own evidence does not support** — this report
declines to do that, per B.10 and this campaign's own repeated preference for honest exclusion
over a substituted (or in this case, ambiguous) green.

**What this run DOES establish, positively and for the first time real-scale, live evidence
exists for:**
1. The bind-time assertion (this dispatch's own hard gate) is GREEN for the full 14-contender
   narrowed roster against live production infrastructure (§1).
2. The merged `a3_scoring_harness` scoring path runs end-to-end at real N=1000 scale with zero
   call-level errors across 434 real scoring calls (§2).
3. Two specific, reproducible, previously-undiscovered defects now have concrete evidence,
   root-cause diagnosis, and (for §5a) a confirmed fix direction, ready for their own small,
   reviewable lanes (§5a: an `event_class` A-2-ontology mapping table; §5b: a one-line sort fix in
   `curve_controls.ts`).
4. `midpoint_triangle`/`transit_kernel`'s NOT-EVALUABLE narrowing is confirmed intact and was not
   re-litigated.

**What remains genuinely open, honestly:** a certified champion/no-winner disposition for B-1 per
DR-15(b)'s own primary criterion, plus the full 56-event (or 54, per §0's recommendation) set
including the sealed test split (gate-runner/anti-gaming-verifier territory only), plus DR-17's
graded scale (§8) and the 3 compute-budget-excluded wide-interval events (§4).

## §8 — DR-17 grading: confirmed unbuilt, not attempted

`grep -rln "sub_peak\|tie_band\|anti_hit"` across `platform/` (excluding `__tests__`): zero hits,
anywhere in the codebase. `DR_17_18_MANIFESTATION_CENSUS_DOCTRINE_v1_0.md`'s §1 grade scale
(peak/sub_peak/elevated/neutral/contra + tie-bands + anti-hit double-weight) is ratified for
CONSUMPTION (`NP-D4B-001`, verbatim) but has no harness implementation to consume it with — only
DR-13 binary hit-rate (`shape_scoring.ts`) and CRPS (`proper_scoring.ts`) exist. Building it
requires several genuinely underspecified judgment calls this run's compute-budget/defect
findings above already crowd out doing carefully (a "real, live-active system" check per grade
`peak`'s own definition; a structural-prior baseline threshold for `elevated`; adverse-valence
classification for the anti-hit double-weight). Per this campaign's own discipline (rushed,
under-verified harness usage is refused elsewhere in this ledger), this is named as its own
pre-registered lane, not invented ad hoc here. `NP-D4B-001(c)` already confirms DR-17 weights do
not displace CRPS as B-1's primary win criterion, so their absence does not, by itself, block a
future champion determination once §5b is fixed — it only means "per-event grades" cannot be
reported this run.

## §9 — Files this session touched (and did not)

**Added (this branch only):**
- This report, `B1_NARROWED_TRAIN_{RUNLOG,SUMMARY,PER_EVENT,EVENTSET}_v1_0.{txt,json}`,
  `b1_driver_v1_0.ts` (ad-hoc orchestration script, not a committed harness module — imports the
  real harness modules unmodified).

**Not touched:** `asset_runner.py`, `runner.py`'s `execute_dag`/`_schedule_parallel`, the leakage
firewall, raw LEL event data (only aggregate/date-filtered `lel_query` calls, §3), any prior
gate/regression surface, `gochara_grammar`/`gochara_intensity` source (only read; the defect in
§5b is in `curve_controls.ts`, a D-4a harness module, and is REPORTED not PATCHED here per this
report's own discipline). No table was written to. `PYTHON_SIDECAR_API_KEY` was read from Secret
Manager (a legitimate, already-authorized access this session's `gcloud` credential already had)
and used only in-memory for authenticated HTTP calls — never written to a file or committed.

---

*B1_NARROWED_STATUS v1.0 (2026-07-22). Real, live, zero-error scoring completed for the narrowed
14-contender roster over 31 TRAIN-eligible events; champion/no-winner certification withheld
pending fixes to two newly-discovered, evidence-backed defects (§5). Recommend: (a) a small,
reviewable `curve_controls.ts` date-sort fix + re-run of this exact driver (cheap: no new sidecar
calls needed, N=1000 controls are pure date-shifts of already-fetched curves); (b) an A-2
event_class-to-resonance-map mapping lane before PERMISSION-contender numbers can be trusted; (c)
the 3 compute-budget-excluded wide-interval events restored under a longer time budget; (d) DR-17
grading built as its own lane. None of these are blocked on infrastructure any more — both the
sidecar route and the credential path are now confirmed live and reproducible.*

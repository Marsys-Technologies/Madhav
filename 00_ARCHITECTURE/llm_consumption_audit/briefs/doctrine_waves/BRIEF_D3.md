---
artifact: BRIEF_D3
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN)
wave: D-3 — Kāla Taraṅga + Three-Lock activation
version: 1.3
status: BOUND (2026-07-17, BIND_D-3.md) — §B slots resolved fresh at open
governing: CONDUCTOR_PROTOCOL.md + DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §6 +
  DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §5/§13
prerequisites: D-2 gate GREEN (Mechanism object shipped). Wave sequence to date — D-1.5a,
  D-1.5b (Gate B 17/17), and D-1.6 "Śuddhi" (Gate Ś) are ALL CLOSED; D-2 is the next wave.
  INFRA-PREREQ CR-40/CR-8 (transit sidecar) — SATISFIED by D-1.6 Lane S-6 (the flag was a
  dead-route bug, not a live auth outage — see §F0) — verified at Gate Ś #13 and re-verified
  live 2026-07-16. §B still re-verifies at open; the T-1-only partial-open contingency is
  retained as a FALLBACK only, no longer the expected path.
gate: falsifiable LEL-retrodiction thresholds (§G) + timing surfaces live — with an ANTI-GAMING
  verifier pass (statistical gates are never green on the primary runner alone).
changelog:
  - v1.3 (2026-07-16, docs/pre-d2-definition-of-done): Definition-of-DONE block added to §F3 (condensed from BRIEF_D2 §F1.7, anti-D-1-recurrence): Binder promise→assertion ledger at open, three mandatory verification altitudes incl. post-deploy LIVE per-cycle re-runs, scale-realism/data-over-flags/anti-vacuous/truncation-honesty evidence rules, ledger-complete close; §G scoped as the ledger's load-bearing subset.
  - v1.2 (2026-07-16, docs/pre-d2-orchestration-economy): §F3 orchestration-economy grant added (Workflow fan-out where shape-appropriate, per-agent effort/model dials, non-dialable verification/gate invariants — mirrors BRIEF_D2 §F1.6); stale state-commit-race residual note replaced with the landed fix (b13640d1) + F1-F4 pointer.
  - v1.1 (2026-07-16, pre-D-2 alignment pass): CR-40/CR-8 INFRA-PREREQ re-statused SATISFIED
    (D-1.6 S-6 fix, Gate Ś #13, live re-probe); §F0 added — post-D-1.5b/D-1.6 substrate baseline
    (S-4 timing fixes, sign-keyed AV facts shipped, Gate Ś #8 parked residual as known input);
    §F3 added — standard parallel-execution discipline + operational constants; T-1/T-6 stale
    premises updated. No scope, lane-structure, or gate changes.
  - v1.0 (2026-07-15): initial FROZEN brief.
---

# D-3 — Kāla Taraṅga + Three-Lock

## §F0 — Substrate baseline as of D-1.6 close (alignment note, 2026-07-16 — read before binding)

This brief froze before waves D-1.5a / D-1.5b / D-1.6 ran. All three are CLOSED (Gate A battery
green 13/15 + 2 documented PARKs; Gate B 17/17; Gate Ś 11 green / 4 by-construction / 1 parked
with evidence). The timing substrate D-3 builds on has materially changed:

- **CR-40/CR-8 (transit sidecar) — SATISFIED.** The estate-wide `sidecar_available: false` was a
  dead-route bug in `kala_temporal_bundle`'s wiring plus ref_* member defects (401 key wiring,
  404 URI registration, literal-"undefined" date param), all fixed by D-1.6 Lane S-6. Gate Ś #13
  green on the deployed connector (`ref_planet_transit_get` no-401, `ref_transit_rules_get` 200,
  `kala_temporal_bundle` `sidecar_available: true`); re-verified live 2026-07-16 by this alignment
  pass (`sidecar_available: true`; `ref_aspects_at_time_get` serving real ephemeris rows). T-2/T-5
  are no longer infra-blocked. NOTE: the register rows CR-40/CR-8 still read "OPEN — ELEVATED" /
  "OPEN" (row-status drift; the D-1.6 close report + Gate Ś are the closure evidence) — the Binder
  should trust the live probe, not the register row.
- **D-1.6 Lane S-4 (timing substrate first-line fixes).** `kala_activation` activation dates
  recovered via fact-traceable lord resolution (R-45; NULL-on-miss, never guesses): post-rebuild
  49,360 rows / 40,040 dated (was ~99% NULL). Flat-0.5 `dasha_activation_proximity` fixed
  (CR-5/12/48); window FAMILIES with member counts already serve interim (Gate Ś #9:
  activation_count=50, real dated forward windows via fix-2's tiered dasha-window selection +
  dated-rows-first ranking); `judgment_query.timing_hooks` now populated with real
  kala_activations and `timing_anchored` is honest (Gate Ś #10; CR-1/CR-63 receipt-lie halves
  closed). D-3 therefore does NOT open onto a temporal blackout — it REPLACES a working interim
  join with the kernel. The supersession claims in T-6 stand, but "currently empty/broken"
  premises in the CR texts are stale.
- **Known input — PARKED residual (Gate Ś #8):** `yoga_activation_by_dasha` signal_type_class=
  'yoga' rows (74 on 482012f1, 0 dated) are birth-moment/catalog facts lacking a real natal
  constituent_lord for dasha matching — needs new `dasha_eligibility_rule` construction work.
  Bounded, evidenced, and squarely inside T-6's yoga-activation-dating scope (CR-12/48): D-3
  should absorb it, not rediscover it. The authoritative firing surface
  (`ganita_yoga_firings_get`) is unaffected.
- **T-1's facts half IS DONE.** D-1.5b Lane B-2 shipped the sign-keyed aṣṭakavarga re-key:
  `chart_facts` categories `ashtakavarga_bindu_sign` (subject `{GRAHA|SAV}-SIGN_N`) and
  `ashtakavarga_kakshya_boundary` (8 sub-arc boundaries: lord, start_deg, end_deg), declared in
  `ga_writers/CHART_FACTS_SCHEMA.json` and written by `ga_strength_writer.py`. T-1 consumes;
  it does not build facts.

## FROZEN §F1 — Lane map

### Lane T-0 — Retrodiction gate harness (first)
Executable checks: (a) peak-proximity — the 8L-Mars→2H mechanism curve shows a local max within
±45 days of the 2025-05 `loss/financial_deception` LEL event at top-decile intensity of its own
5-yr curve; (b) windfall — wealth curve peak ±45d of 2010-07 `finance/family_windfall`, top-decile;
(c) blind battery — ≥50% hit-rate (±45d / top-tercile) across all scorable LEL events, above the
shuffled-birth negative control; lead/lag distribution reported. Thresholds are v1 gates,
revisable by Adjudicator-doctrine with a DR-n.

### Lane T-1 — Aṣṭakavarga gating + kakṣyā (FIRST capability; sidecar-independent)
Consumes B-2's sign-keyed AV facts — SHIPPED in D-1.5b (`ashtakavarga_bindu_sign` +
`ashtakavarga_kakshya_boundary` in chart_facts; see §F0): SAV/BAV transit thresholds damp/amplify
windows (SAV-10th=27 damps career windows; SAV-7th=34 amplifies partnership — the type specimens);
kakṣyā sub-windows (~3.4-day dated precision) as a served timing face. Delivers dated timing
capability even in the (now unexpected) case that the sidecar regresses.

### Lane T-2 — Taraṅga service core
Stateless sidecar service (the 2nd sidecar instance; uniform contract per design §2):
`activation(chart, domain|mechanism, t)` + `curve(chart, domain|mechanism, [t1,t2], resolution)`.
Chart-static sensitivity substrate at build (natal map with valence/weights from ga_vichara +
Mechanism graph-weights); time-varying kernel on demand (ephemeris-cached transits; cos² orb;
applying ×1.0 / separating ×0.7; superposition). Evidence write-through: results cited in a
reading or consumed by L5 persist with formula_version + inputs + as_of (B.3); nothing else stored.
CR-41 dissolves by construction.

### Lane T-3 — Shared kernel + PROMISE lock
Extract the ka_sangam engine into a shared library (Taraṅga serves live; ka_* writers materialize);
PROMISE = salience × functional valence × varga-ratification × NBRY-deferral semantics (a cancelled
debility re-times into the canceller's periods — the Venus-via-Mercury story, computable) ×
mechanism graph-weight. Kills CR-88 (promise-side severance: today only dignity_score, 0.5-defaulted,
reaches timing).

### Lane T-4 — PERMISSION lock
Vimśottarī spine + multi-system concordance elevated to a real gate multiplier (7 systems already
computed) + period-lord relational algebra (AD-lord kendra/trikoṇa/dusthāna + tāra FROM the MD-lord)
+ full dasha-lord capability (B8's view consumed).

### Lane T-5 — TRIGGER lock
The 12 currents + SIGNED suppressive currents (malefic transits over the mechanism; papa-kartari of
the window — destructive interference becomes possible, killing CR-89's additive-only model) +
Guru-Śani double-transit + saham currents (Dhana-saham for wealth) + gochara vedha filter (CR-102 —
pairs already in bg_transit_rules; roughly a third of served "favourable" windows are classically
void today) + repair-or-retire school_consensus and the ~90% stub predicates under staged admission.

### Lane T-6 — Serving (last)
`judgment_query.timing_hooks` fed by the kernel (CR-1/CR-63's empty-hooks/receipt-lie halves were
already closed by D-1.6 S-4 — see §F0; T-6 supersedes the interim chart_dashas+kala_activation
join with the kernel); `kala_windows_get`/`get_temporal_windows`/`kala_priority_ranking_get`
re-pointed to the service (window FAMILIES with member counts — CR-4/29 — already serve interim
per Gate Ś #9; re-point, don't rebuild); pact TRIGGER stage unblocked (CR-40 consumer; sidecar
already live per §F0 — wire the stage, infra is not the blocker); phala wealth anchors fed
(CR-19/66); yoga-activation dating (CR-12/48) via kernel — INCLUDING the Gate Ś #8 parked
yoga-signal-class `dasha_eligibility_rule` residual (§F0); receipts honest.
(The remaining temporal-blackout rows — CR-2/3/5/6/37 — are superseded BY CONSTRUCTION through
T-2/T-3/T-6: the interim-fixed or still-broken L3 joins/writers are replaced, not patched; the
gate's live timing assertions are their closure proof. Note CR-3's bearing_yogas regression was
already fixed in D-1.5a and CR-5/6/37's first-line fixes landed in D-1.6 S-4.)

**Kernel admission loop (conductor-run, inherently serial):** T-1/T-4/T-5 currents are IMPLEMENTED
in parallel but ADMITTED one at a time: v1 kernel = dasha-capability steps + slow-transit pulses +
SAV potency; each further current stays only if the T-0 blind-battery score improves. Weights are
earned against lived history, not doctrine.

## FROZEN §F2 — must_not_touch
FROZEN orchestrator contract (PARK) · CR-87 per-chart NatalContext (regression-guarded by the
two-chart test — any new current must take chart context as a REQUIRED param, no defaults) ·
L5 multipliers (D-4) · Gate-A/B/Ś/D-2 surface semantics (regression batteries re-run).

## §F3 — Execution discipline + operational constants (standard, per CONDUCTOR_PROTOCOL — added v1.1)

**Parallel-sub-agent discipline (protocol §2/§3, as run in D-1.5a → D-1.6):** every lane brief
declares DISJOINT `may_touch` globs (scope-warden Phase-1(d): any stray path = automatic
REJECTION); shared files (class-prior tables, registries, schema declarations) are APPEND-ONLY
with the expected cross-lane conflict named in advance; lanes merge in the brief's DECLARED order
(here: T-0 first, then the T-1..T-5 implementation set under the conductor-run serial admission
loop, T-6 last); implementers run in ISOLATED git worktrees (`wave/D-3/<lane>`); every lane is
verified by an INDEPENDENT fresh-context verifier (Opus) per protocol Phase-1 before merge —
an implementer's "done" is a claim, never an acceptance.

**Operational constants (hard-won D-1.5a/b + D-1.6):**
- Rebuilds go via the Cloud Run job path (`brahma-build-pipeline-job`, protocol §8.2) — NEVER the
  laptop cloud-sql-proxy (proxy-kill cycle, root-caused in `O8_LOCAL_PROXY_KILL_ROOT_CAUSE_v1_0.md`;
  the job path is the sanctioned route).
- The deployed connector RATE-LIMITS under sustained assertion load (429 cascade → false reds;
  Gate B evidence in REPORT_D-1.5b). Gate batteries must throttle/batch; the harness client's
  429-retry landed in D-1.6 S-6 — keep it, don't strip it.
- The D-1.6 "state-commit race" was FIXED pre-D-2 (commit `b13640d1`, adversarially verified —
  deterministic same-day resume-skip misclassified as dormant, not a race; data-presence probe +
  loud safety nets now in `asset_runner.py`). Binder spot-verifies it is on main; four
  non-blocking follow-ups (F1–F4) are recorded in BRIEF_D2 §B item 3. The orchestrator remains
  FROZEN — if a NEW state anomaly appears, verify underlying data first, then PARK class 1.

**Orchestration economy (native-granted, 2026-07-16 — same grant as BRIEF_D2 §F1.6, restated
for standalone reading):** the conductor balances COST vs QUALITY with three dials. (1) Prefer
Workflow scripts (`pipeline()`/`parallel()`, per-agent `model`/`effort` overrides) for fan-out-
shaped phases — verification panels, gate batteries, LEL-retrodiction acceptance sweeps, window/
kernel validation sweeps — while deep implementation stays one isolated-worktree agent per lane;
live-connector fan-outs must throttle. (2) Effort dial: down (`low`/`medium`) for mechanical
stages, up (`high`/`xhigh`) for adversarial verification, root-cause, and doctrine-feeding work.
(3) Model dial: cheaper models for mechanical fan-out, stronger for verification/judgment;
Fable adjudication is not dialable. NON-DIALABLE invariants: every lane/hotfix still receives an
independent full-scrutiny fresh-context verifier receipt before merge; gate thresholds and
reds-are-reds honesty are untouchable; economize on discovery, spend on verification and
irreversible steps.

**Definition of DONE (native-ordered 2026-07-16 — full text at BRIEF_D2 §F1.7; binding here in
condensed form):** D-1 closed "verified" and still required three remediation waves; that may not
recur. (1) **Promise ledger:** at open, the Binder enumerates EVERY §F1 commitment (deliverables,
type specimens, servability claims, "kills CR-N" claims) into a promise→assertion table; T-0
turns each row into an executable check. No ledger row → bind failure. (2) **Three altitudes,
all mandatory:** per-lane Phase-1 (pre-merge) + integration cross-lane checks (shared-table
delete/count scopes, schema-declaration completeness) + post-deploy LIVE re-run of each cycle's
ledger rows on the deployed connector with rebuilt data BEFORE the next cycle spawns —
built-but-not-served is not done. (3) **Evidence rules:** verify at real chart scale, never
synthetic-only; data over flags (never trust asset_throughput/register/report states — probe
rows); fixtures model live payload shape AND volume; type specimens re-derived from the actual
chart at verification time; no absence claim from a truncated page (page to exhaustion or use an
authoritative total). (4) **Close:** REPORT_D-3.md carries the full ledger with per-row
disposition (GREEN + evidence | PARKED + evidence + owner); `current_wave` advances only when the
ledger is complete. §G's retrodiction thresholds are the load-bearing subset of the ledger, never
a substitute for the rest.

## §B — BIND-AT-OPEN slots (Fable Binder)
- Mechanism-object interface as actually shipped (probe the D-2 serving face) → PROMISE lock inputs.
- Sidecar status: re-verify live at open (`ref_*`/`kala_temporal_bundle` answer). Expected GREEN
  since D-1.6 S-6 (§F0) — if regressed, wave opens with T-1 ONLY and holds T-2/T-5 (partial-open
  is legal for this wave alone, now as fallback).
- Scorable-LEL event list + train/test split re-derived from LEL HEAD under PH-4-3's discipline
  (57 total / 36 pre-2020 train / ~40 scorable — reconcile counts at open).
- Current inventory final order for the admission loop (Adjudicator-engineering ranks by expected
  retrodiction value).
- Rollback pin + all prior gate batteries green.

## §G — Gate
T-0's three checks green (peak-proximity, windfall, blind battery vs shuffled-birth control) +
**anti-gaming pass** (curves not degenerate: intensity variance floor, top-decile is <15% of days,
control gap statistically real) + timing surfaces live (`timing_hooks` non-empty and dated on
482012f1; kakṣyā windows served; a "when, for money" question answerable through tools alone) +
all prior batteries green. Final proof: the 2027–2034 Ketu-MD lean stretch and the 2034 Venus-MD
activation are SERVED, dated, with mechanism attribution — not hand-derived.

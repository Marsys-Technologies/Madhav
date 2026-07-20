---
artifact: BRIEF_D4
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN)
wave: D-4 — Calibration ignition (L5 finally fed)
version: 2.0
status: SUPERSEDED-BY-ARC (2026-07-19) — the native-ratified TEMPORAL_ENGINE_ARC_PLAN_v1_0.md
  splits this wave into D-4a (Measurement Foundry, BRIEF_D4A.md) → D-5 (Gochara-Chitra,
  BRIEF_D5.md) → D-4b (Calibration Ignition + Grand Bakeoff, BRIEF_D4B.md). This file is
  RETAINED IN PLACE as the authoritative LANE-TEXT SOURCE those briefs cite (v2.0 lane content
  remains correct; only the packaging changed). Do NOT bind or execute this brief directly.
governing: CONDUCTOR_PROTOCOL.md + DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §7 +
  DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §7
prerequisite: >
  AMENDED v2.0 — the v1.3 prerequisite ("D-3 gate GREEN") is OBSOLETE and must not gate the bind.
  Actual entry state: D-3 CLOSED_BLOCKED_RED (REPORT_D-3.md) — mechanism curves EXIST and are
  mechanically verified, but the transit-kernel v1 FAILED retrodiction (17.5% vs 50% floor;
  −16.1pp vs shuffled-birth control; −15.8pp coverage-matched). This RED is a designed INPUT to
  this wave per DR-12, not a blocker: D-4 runs the peak-model bakeoff on a repaired serving
  substrate (Lane C-0) and calibrates against whichever model the data selects. Wave sequence to
  date: D-1.5a, D-1.5b (Gate B 17/17), D-1.6 (Gate Ś), D-2 (6/6 single-pass), D-3
  (CLOSED_BLOCKED_RED) — all sealed.
gate: discrimination + negative-control gates (§G, expanded v2.0) with anti-gaming verifier pass.
revision_inputs: D4_BRIEF_REVISION_INPUTS.md (2026-07-18) — DR-12/DR-13 texts, C-0 scope
  (CR-109/110/111), 4 carried D-2 findings, firewall + sealed-split notes.
changelog:
  - v1.3 (2026-07-16, docs/pre-d2-definition-of-done): Definition-of-DONE block added to §F3 (condensed from BRIEF_D2 §F1.7, anti-D-1-recurrence): Binder promise→assertion ledger at open, three mandatory verification altitudes incl. post-deploy LIVE per-cycle re-runs, scale-realism/data-over-flags/anti-vacuous/truncation-honesty evidence rules, ledger-complete close; §G scoped as the ledger's load-bearing subset.
  - v1.2 (2026-07-16, docs/pre-d2-orchestration-economy): §F3 orchestration-economy grant added (Workflow fan-out where shape-appropriate, per-agent effort/model dials, non-dialable verification/gate invariants — mirrors BRIEF_D2 §F1.6); stale state-commit-race residual note replaced with the landed fix (b13640d1) + F1-F4 pointer.
  - v1.1 (2026-07-16, pre-D-2 alignment pass): §F0 added — post-D-1.6 baseline (CR-51/CR-30
    calibration-alias unification; CR-47's serve-side non_discriminating honesty flag shipped,
    matcher root fix remains Lane C-1; L5 STRUCTURAL-mode framing per CLAUDE.md §E; cited CR rows
    re-verified against the register); §F3 added — standard parallel-execution discipline +
    operational constants; C-1 stale premise updated. No scope, lane-structure, or gate changes.
  - v1.0 (2026-07-15): initial FROZEN brief.
---

# D-4 — Calibration Ignition

## §F0 — Baseline as of D-1.6 close (alignment note, 2026-07-16 — read before binding)

This brief froze before waves D-1.5a / D-1.5b / D-1.6 ran (all three CLOSED: Gate A 13/15 + 2
documented PARKs; Gate B 17/17; Gate Ś). What changed in D-4's territory:

- **Framing: L5 is SEALED in STRUCTURAL mode by design** (CLAUDE.md §E) — empirical calibration
  values fill in as prediction→outcome data accrues. D-4 is the designed IGNITION of that loop
  (the first real outcome feed), not a repair of unfinished L5 work. Nothing in this wave
  re-opens the L5 seal; writers stay inside the FROZEN WriterBase contract.
- **Calibration-alias unification (D-1.6 Lane S-1, CR-51/CR-30):** `query_calibration` and
  `mimamsa_calibration_get` — previously documented aliases returning DIFFERENT payloads — are
  now a strict twin (Gate Ś #3: IDENTICAL result_hash on the deployed connector), and an
  alias→primitive conformance check lives in the harness (S-6, O-7). §G assertions may probe
  either face; alias parity is a standing regression surface this wave must not break.
- **CR-47's honesty half already shipped:** D-1.6 S-1 added the serve-side `non_discriminating`
  flag to `phala_rectification_get` (a zero-signal run now self-reports instead of presenting a
  fake ranking). Lane C-1's remaining scope is the MATCHER ROOT FIX itself (the 0/36 silent
  zero-scoring), which D-1.6 explicitly deferred ("full method fix stays K-6/later" — that later
  is this lane).
- **Register verification (2026-07-16):** this brief's cited rows — CR-47, CR-79, CR-20/67,
  CR-68 — are all still OPEN in `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` v1.5 (§A–§I+§M
  remains system-of-record for CR-1..89+107; CR-90..106 resolve via the §N pointer table into
  the execution plan §8 + wave briefs). No re-statusing by D-1.6 S-8 touched this brief's rows.

## FROZEN §F1 — Lane map (8 lanes, v2.0)

### Lane C-0 — Serving-substrate repair (NEW v2.0; runs FIRST; the bakeoff is invalid without it)
Infrastructure only — zero kernel/weight/threshold/orb/valence changes; Opus verifier checks the
diff for exactly that (same guard class as FIX-COV, whose STOP correctly routed this here).
1. **CR-109 (root-caused):** `resolve_activation_windows()` collapses all matched dasha periods
   to one `primary_selected` window → served coverage bracketed to ~2010–2032. Fix: surgical
   migration + writer-cardinality change per §N.4; ALL matched periods served, full-span
   birth→2054. The FIX-COV worktree (`wave/D-3/FIX-COV`, preserved at D-3 close) is the starting
   point.
2. **CR-110 (native-reported; VERIFY FIRST):** `kala_temporal_bundle` double dasha-spine —
   two ayanamsha variants interleaved undisclosed (Mercury MD ending both 2027-08-12 and
   2027-08-18; phantom Ketu-MD-2025 rows). Independently reproduce per CR-96 discipline, then fix
   (ayanamsha filter or per-row disclosure).
3. **CR-111 (native-reported; VERIFY FIRST):** bundle serves 0 convergence windows for 2026–2027
   while `kala_convergence` holds 16,767 TRIGGER-refined rows peaking 2027-10/11 — build-vs-serve
   join gap. Reproduce, then fix.
4. **Artifact rescue (do at lane open, before anything else):** copy D-3's per-event scoring
   artifacts (`score_g.py`, `lel_events.json`, `pooled_activations.json`, `result_g.json`,
   `coverage_matched_control.py`, `coverage_matched_result.json`) from the session scratchpad
   into `briefs/doctrine_waves/artifacts/D-3/` — if the scratchpad has expired, re-derive from
   the deployed connector and mark `rederived: true`. The bakeoff's transit-kernel baseline
   depends on this table.
5. **Registry bookkeeping (carried D-2 finding #3):** `canonical_faces.json` gains the 3
   unaccounted cycle-2 tools (`plan_retrieval`, `scan_fetch_signals`, `reading_notes_get`);
   census reconciles.
Acceptance (live, on the deployed connector, not by construction): full-span windows served
birth→2054 with >1 period per lord where the dasha table has them; exactly ONE dasha spine per
ayanamsha served, or per-row ayanamsha disclosure; ≥1 TRIGGER-refined convergence window served
for 2026–2027 matching the DB rows; artifacts committed; census == canonical list.

### Lane C-B — DR-12 peak-model bakeoff (NEW v2.0; the wave's empirical centerpiece)
Runs AFTER C-0 + C-1 (needs the repaired substrate and the shape-aware matcher). Scores THREE
competing peak models against the full LEL outcome corpus under ONE identical harness:
midpoint-triangle (`period_peak` = arithmetic midpoint, 0.6/1.0/0.4 envelope — the deprecated
incumbent), pratyantar-lord decomposition (DR-10's classical default), transit-kernel (D-3's
kernel on the C-0-repaired surface; its D-3 RED per-event table is its standing baseline entry).
Hard rules:
- **Identical everything:** same event set, same DR-13 scoring semantics (point/interval/chain,
  confidence-scaled tolerance), same coverage span, same thresholds, same controls. A model may
  not bring its own harness.
- **Pre-registered before the first scoring run:** thresholds, the event set (post-tightening if
  the native's questionnaire has returned; without it otherwise — note which), and the win
  criterion (blind-battery hit-rate above BOTH the 50% floor-bar and the model's own
  coverage-matched shuffled-birth control, with the gap reported). Committed to the ledger BEFORE
  scoring; no post-hoc adjustment.
- **Control-mirroring (DR-13):** every scoring rule applies identically to every model's control.
- **Per-model per-event table persisted** as a first-class committed artifact — this IS the
  campaign's empirical record.
- **No-winner branch (pre-committed):** if NO model beats its control, the bakeoff reports
  exactly that; C-2's backfill then scores outcomes against the best-available model but writes
  `model_confidence: none_validated` on every row, and the campaign close records "no validated
  timing model yet — prospective loop is the path" as the honest finding. No forced champion,
  ever. If ≥1 model wins, the data names it; DR-14 records the retirement of the losers.
- Anti-gaming verifier on the whole battery; statistical gates never green on the primary runner
  alone.

### Lane C-1 — Shared LEL↔candidate matcher fix (CR-47 root)
The matcher scored 0/36 LEL events across all 185 rectification candidates — silently. The
silent half is fixed (D-1.6 S-1's `non_discriminating` flag — see §F0); this lane root-causes
the shared matcher itself. Healing this heals rectification too (same component). **v2.0
additions:** (a) the matcher is speced against DR-13 — event shapes point/interval/chain,
interval scoring by overlap with top-decile windows, date_confidence-scaled tolerance (exact
±45d / month ±75d / year-only → labeled secondary interval battery, never discarded); (b) this
lane owns the **LEL schema v2 additive migration** (APPROVED, `LEL_SCHEMA_V2_PROPOSAL.md`) +
applying the approved windfall interval-reclassification (EVT.2010.XX.XX.01) + ingesting the
native's date-tightening answers if returned (LEL data-entry under the §7-verified firewall;
sealed-split membership unchanged per the §8 note); (c) carried D-2 finding #1 (leverage_index
`subject=venus` false-empty behind ambiguous empty_reason) is fixed here or in C-5 — named
ledger row either way, not silently dropped a third time. Verifier: matcher matches known
specimens (2025-05 fraud → 8L-Mars→2H mechanism; 2010-07 windfall → wealth mechanism, scored as
an INTERVAL per its approved reclassification) with nonzero fit, and a synthetic
chain-shaped event scores per-milestone.

### Lane C-2 — LEL firewall re-scope + retrodiction backfill
Firewall re-scoped: quarantine LEL → prediction-INPUTS only; LEL → outcome-SCORING flows freely.
One-time backfill job: score all 57 LEL events (per chart) against the mechanism curves of
**the bakeoff-selected model on the C-0-repaired surface** (v2.0 — no longer hardcoded to
"D-3 mechanism curves"; if C-B's no-winner branch fired, best-available model with
`model_confidence: none_validated` stamped per row); batch-write `mimamsa_outcome_record` rows
under PH-4-3's train/test discipline. Flips n_observations 0 → ~40/chart; promotion gates
evaluate for the first time. **Shrinkage honesty (v2.0, binding):** every calibrated multiplier
carries sample-size-aware uncertainty — shrunk toward priors at N≈40, with n_observations and
the control delta on the served payload; no calibration output may claim more confidence than
its N supports. **Structural-mode exit criterion (v2.0):** L5 leaves "structural mode" for a
given multiplier ONLY when (n_observations ≥ threshold set by Adjudicator-doctrine DR) AND
(control delta positive); until then payloads say `calibration_state: structural_prior` —
explicitly, so structural mode can never silently persist as implied-empirical.

### Lane C-3 — Event-class evidence + verdict function (CR-79)
Evidence sets become event-class-specific (gain ≠ loss — opposite outcomes may never share
identical evidence + identical grade); QA checks that always return 0.5 self-report as
non-discriminating; kill-switch release criteria defined as data.

### Lane C-4 — Negative controls
Shuffled-birth + antiphase controls implemented (the `not_implemented` stubs become real); every
calibration claim carries its control delta. No control, no claim.

### Lane C-5 — Remedy-leverage join (CR-20/67)
bo_upaya populated from: leverage_index (weakest load-bearing graha) × existing sādhanā history
(LEL spiritual arc) × dasha runway (intervention window = years BEFORE the weak lord's MD opens).
The Venus/Venkaṭeśvara specimen becomes computable: system holds both halves today and never joins
them. Wealth resonances ≠ 0; at least one schedulable program.

### Lane C-6 — mechanism_retrodiction surface (CR-68)
LEL events joined to the mechanism that predicts them, served as CONFIRMATION ("this chart's 2H
mechanism has fired N times: …") — never as prediction input. Feeds L5 honestly; gives readings
their retrodictive-evidence section.

### Lane C-7 — Prospective-prediction ledger (NEW v2.0; first-class deliverable, NOT a closing
footnote)
The retrodictive corpus is N≈40, one chart — the learning layer's real engine is prospective.
This lane ships: (a) a `prospective_predictions` store — every served reading's falsifier-bearing
claims logged with claim text, domain, window, model + formula_version, confidence,
falsifier, and as_of (B.3 provenance); (b) the LEL-append → outcome-matching hook (a new LEL
event triggers scoring of every open prediction whose window covers it, via C-1's matcher);
(c) a served surface (`mimamsa_prospective_ledger` or equivalent) showing open/resolved
predictions with hit/miss — readable by the native; (d) the wealth-baseline predictions from
this conversation's arc registered as the ledger's first entries (e.g., the Sat–Jupiter
pratyantar window 2027-04-09→08-18, the Ketu-MD consolidation shape, the Venus-MD 2034
activation — each with its falsifier). This is the hedge against the retrodiction corpus's
limits: even a no-winner bakeoff leaves D-4 having opened a growing, uncheatable outcome stream.

**Merge order (v2.0):** C-0 → C-1 → C-3/C-4 (parallel) → **C-B (bakeoff)** → C-2 (backfill runs
AFTER matcher+evidence fixed AND bakeoff selected/no-winner-recorded) → C-5/C-6/C-7. The
backfill is one-shot: never run it on an unverified matcher, never before the bakeoff names the
model.

**Then the standing live loop opens (now enforced by C-7's shipped surfaces, not aspirational):**
every reading logs falsifier-bearing predictions per its vidhi; every LEL append triggers outcome
matching; multipliers update under the shrinkage rule; the next compiled contract retrieves with
calibrated priors.

## FROZEN §F2 — must_not_touch
FROZEN orchestrator contract (PARK) · the leakage firewall on prediction-INPUTS (re-scoped, never
removed) · raw LEL event data (append-only corpus) · all prior gate surfaces (regression batteries).

## §F3 — Execution discipline + operational constants (standard, per CONDUCTOR_PROTOCOL — added v1.1)

**Parallel-sub-agent discipline (protocol §2/§3, as run in D-1.5a → D-1.6):** every lane brief
declares DISJOINT `may_touch` globs (scope-warden Phase-1(d): any stray path = automatic
REJECTION); shared files are APPEND-ONLY with expected cross-lane conflicts named in advance;
lanes merge in the DECLARED merge order above (v2.0: C-0 → C-1 → C-3/C-4 → C-B → C-2 →
C-5/C-6/C-7); implementers run
in ISOLATED git worktrees (`wave/D-4/<lane>`); every lane is verified by an INDEPENDENT
fresh-context verifier (Opus) per protocol Phase-1 before merge — an implementer's "done" is a
claim, never an acceptance. The one-shot C-2 backfill additionally requires its upstream lanes'
RECEIPTS in hand before it runs (never on an unverified matcher).

**Operational constants (hard-won D-1.5a/b + D-1.6):**
- Rebuilds go via the Cloud Run job path (`brahma-build-pipeline-job`, protocol §8.2) — NEVER the
  laptop cloud-sql-proxy (proxy-kill cycle, `O8_LOCAL_PROXY_KILL_ROOT_CAUSE_v1_0.md`). D-4's
  expected rebuild scope is L5-only (minutes) per protocol §8.2 — the Binder confirms at open.
- The deployed connector RATE-LIMITS under sustained assertion load (429 cascade → false reds;
  REPORT_D-1.5b). Gate batteries must throttle/batch; keep the D-1.6 S-6 harness 429-retry.
- The D-1.6 "state-commit race" was FIXED pre-D-2 (commit `b13640d1`, adversarially verified —
  deterministic same-day resume-skip misclassified as dormant, not a race). Binder spot-verifies
  it is on main; follow-ups F1–F4 recorded in BRIEF_D2 §B item 3. The orchestrator remains
  FROZEN — a NEW state anomaly means verify underlying data first, then PARK class 1.

**Orchestration economy (native-granted, 2026-07-16 — same grant as BRIEF_D2 §F1.6, restated
for standalone reading):** the conductor balances COST vs QUALITY with three dials. (1) Prefer
Workflow scripts (`pipeline()`/`parallel()`, per-agent `model`/`effort` overrides) for fan-out-
shaped phases — verification panels, gate batteries, calibration backfill receipt sweeps,
prediction→outcome scoring passes — while deep implementation stays one isolated-worktree agent
per lane; live-connector fan-outs must throttle. (2) Effort dial: down (`low`/`medium`) for
mechanical stages, up (`high`/`xhigh`) for adversarial verification, root-cause, and
doctrine-feeding work. (3) Model dial: cheaper models for mechanical fan-out, stronger for
verification/judgment; Fable adjudication is not dialable. NON-DIALABLE invariants: every
lane/hotfix still receives an independent full-scrutiny fresh-context verifier receipt before
merge; gate thresholds and reds-are-reds honesty are untouchable; economize on discovery, spend
on verification and irreversible steps.

**Definition of DONE (native-ordered 2026-07-16 — full text at BRIEF_D2 §F1.7; binding here in
condensed form):** D-1 closed "verified" and still required three remediation waves; that may not
recur. (1) **Promise ledger:** at open, the Binder enumerates EVERY §F1 commitment (deliverables,
matcher specimens, backfill counts, "closes CR-N" claims) into a promise→assertion table; the
gate harness turns each row into an executable check. No ledger row → bind failure. (2) **Three
altitudes, all mandatory:** per-lane Phase-1 (pre-merge) + integration cross-lane checks
(shared-table delete/count scopes; the one-shot C-2 backfill gets a pre-flight dry-run receipt) +
post-deploy LIVE re-run of each cycle's ledger rows on the deployed connector with rebuilt data —
built-but-not-served is not done. (3) **Evidence rules:** verify at real chart scale, never
synthetic-only; data over flags (probe rows, never trust state columns/registers/reports);
fixtures model live payload shape AND volume; specimens (2025-05 fraud, 2010-07 windfall)
re-derived from the actual LEL/mechanism data at verification time; no absence claim from a
truncated page. (4) **Close:** REPORT_D-4.md carries the full ledger with per-row disposition
(GREEN + evidence | PARKED + evidence + owner); `current_wave`/campaign-close advances only when
the ledger is complete. §G's discrimination + negative-control gates are the load-bearing subset
of the ledger, never a substitute for the rest.

## §B — BIND-AT-OPEN slots (Fable Binder; v2.0 additions marked)
- **(v2.0) C-0 verification:** independently reproduce CR-110/CR-111 (native-reported, unverified)
  via direct DB + deployed-connector probes per CR-96 before scoping their fixes; CR-109 is
  root-caused, verify the FIX-COV worktree still applies to main.
- **(v2.0) Bakeoff pre-registration packet:** event set (note whether native's date-tightening
  answers arrived; proceed without if not, recorded), thresholds, win criterion, control
  construction — committed to the ledger BEFORE any scoring run.
- **(v2.0) Structural-mode exit threshold + promotion/kill-switch thresholds** ← one
  Adjudicator-doctrine DR (these are epistemics, not engineering); includes the no-winner-branch
  wording verbatim from §F1 C-B.
- **(v2.0) Prospective-ledger schema** ← C-7 spike: reuse `mimamsa_outcome_record`/PPL surfaces
  where they exist (LEL §9 interim PPL is prior art — read it, don't reinvent).
- Matcher root-cause hypothesis ← C-1 diagnosis spike at open (read the actual matcher code + one
  traced run) before lane briefs finalize.
- Evidence-set taxonomy per event class ← LEL HEAD's actual event classes (enumerate, don't assume).
- Curve-shape parameters ← D-3's shipped kernel (intensity distribution percentiles for scoring
  thresholds).
- Promotion-gate + kill-switch release thresholds ← Adjudicator-doctrine (DR-n; these are
  epistemics, not engineering).
- Rollback pin + all prior batteries green.

## §G — Gate (expanded v2.0)
1. **C-0 live assertions:** full-span windows served birth→2054; single disclosed dasha spine;
   ≥1 TRIGGER-refined 2026–2027 convergence window served matching DB rows; D-3 per-event
   artifacts committed; census == canonical-face list.
2. **Bakeoff complete and honest:** three models scored under the pre-registered identical
   harness; per-model per-event tables committed; winner named by data OR the no-winner branch
   honestly recorded — either outcome is a PASS of this assertion; a forced champion or post-hoc
   threshold change is the FAIL.
3. `mimamsa_calibration_get`: n_observations ≈ 40/chart; multipliers evaluating (no longer all
   prior_only); verdict_distribution + reliability_curve non-empty; **every multiplier carries
   n_observations + control delta + `calibration_state`** (shrinkage honesty served, not just
   stored).
4. Discrimination: `mimamsa_insight_get(wealth)` — "Major Financial Gain" and "Major Financial
   Loss" carry DIFFERENT evidence sets and DIFFERENT grades on 482012f1.
5. Negative controls: implemented; every calibration claim carries its control delta; the
   claim-vs-control gap reported with sign — a negative gap is served as a negative gap.
6. At least one served verdict demonstrably moved by a calibrated multiplier (before/after
   receipt) — OR, on the no-winner branch, demonstrably NOT moved with
   `calibration_state: structural_prior` served — honesty either way.
7. Remedy: bo_upaya wealth resonances ≠ 0; the leverage-ranked intervention (Venus, pre-2034
   window) served with its sādhanā join; leverage_index answers `subject=venus` AND `subject=VEN`
   identically (carried finding #1 closed).
8. **Prospective ledger live:** ≥5 falsifier-bearing predictions registered from real readings
   (incl. the wealth-baseline arc entries); the LEL-append→matching hook demonstrated on a test
   append; the ledger surface readable on the deployed connector.
9. Anti-gaming pass on 1–8 + all prior wave batteries green (full regression; carried D-2
   findings #2/#4 dispositioned — fixed or PARKED-with-owner, not silent).

**Campaign close (after this gate):** parked-items review + all DR-n rulings presented to the
native for ratification; register final sweep; CURRENT_STATE + SESSION_LOG campaign seal; the
master test becomes the standing per-release regression suite. **Plus (v2.0): the campaign-arc
baseline diff** — re-run the verbatim baseline wealth question
(`BASELINE_WEALTH_READING_PRE_D2_v1_0.md` §4 protocol) one final time and write the three-point
comparison (pre-D-2 → post-D-2 → post-D-4): does the instrument now serve promise + threat +
dated windows with `peak_basis` provenance + retrodictive evidence (C-6) + calibrated confidence
(or honest `structural_prior`) — and is the winning peak model named by data? That document is
the campaign's native-facing deliverable.

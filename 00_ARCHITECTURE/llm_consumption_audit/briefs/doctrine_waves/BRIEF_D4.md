---
artifact: BRIEF_D4
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN)
wave: D-4 — Calibration ignition (L5 finally fed)
version: 1.2
status: FROZEN — §B slots bind at wave open
governing: CONDUCTOR_PROTOCOL.md + DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §7 +
  DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §7
prerequisite: D-3 gate GREEN (mechanism curves exist and retrodict). Wave sequence to date —
  D-1.5a, D-1.5b (Gate B 17/17), and D-1.6 "Śuddhi" (Gate Ś) are ALL CLOSED; D-2 then D-3
  precede this wave.
gate: discrimination + negative-control gates (§G) with anti-gaming verifier pass.
changelog:
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

## FROZEN §F1 — Lane map (6 lanes)

### Lane C-1 — Shared LEL↔candidate matcher fix (CR-47 root)
The matcher scored 0/36 LEL events across all 185 rectification candidates — silently. The
silent half is fixed (D-1.6 S-1's `non_discriminating` flag — see §F0); this lane root-causes
the shared matcher itself. Healing this heals rectification too (same component). Verifier:
matcher matches known specimens (2025-05 fraud → 8L-Mars→2H mechanism; 2010-07 windfall →
wealth mechanism) with nonzero fit.

### Lane C-2 — LEL firewall re-scope + retrodiction backfill
Firewall re-scoped: quarantine LEL → prediction-INPUTS only; LEL → outcome-SCORING flows freely.
One-time backfill job: score all 57 LEL events (per chart) against their D-3 mechanism curves;
batch-write `mimamsa_outcome_record` rows under PH-4-3's train/test discipline. Flips
n_observations 0 → ~40/chart; promotion gates evaluate for the first time.

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

**Merge order:** C-1 → C-3/C-4 (parallel) → C-2 (backfill runs AFTER matcher+evidence fixed) →
C-5/C-6. The backfill is one-shot: never run it on an unverified matcher.

**Then the standing live loop opens (not a lane — a property):** every reading logs
falsifier-bearing predictions per its vidhi; every LEL append triggers outcome matching;
multipliers update; the next compiled contract retrieves with calibrated priors.

## FROZEN §F2 — must_not_touch
FROZEN orchestrator contract (PARK) · the leakage firewall on prediction-INPUTS (re-scoped, never
removed) · raw LEL event data (append-only corpus) · all prior gate surfaces (regression batteries).

## §F3 — Execution discipline + operational constants (standard, per CONDUCTOR_PROTOCOL — added v1.1)

**Parallel-sub-agent discipline (protocol §2/§3, as run in D-1.5a → D-1.6):** every lane brief
declares DISJOINT `may_touch` globs (scope-warden Phase-1(d): any stray path = automatic
REJECTION); shared files are APPEND-ONLY with expected cross-lane conflicts named in advance;
lanes merge in the DECLARED merge order above (C-1 → C-3/C-4 → C-2 → C-5/C-6); implementers run
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

## §B — BIND-AT-OPEN slots (Fable Binder)
- Matcher root-cause hypothesis ← C-1 diagnosis spike at open (read the actual matcher code + one
  traced run) before lane briefs finalize.
- Evidence-set taxonomy per event class ← LEL HEAD's actual event classes (enumerate, don't assume).
- Curve-shape parameters ← D-3's shipped kernel (intensity distribution percentiles for scoring
  thresholds).
- Promotion-gate + kill-switch release thresholds ← Adjudicator-doctrine (DR-n; these are
  epistemics, not engineering).
- Rollback pin + all prior batteries green.

## §G — Gate
1. `mimamsa_calibration_get`: n_observations ≈ 40/chart; multipliers evaluating (no longer all
   prior_only); verdict_distribution + reliability_curve non-empty.
2. Discrimination: `mimamsa_insight_get(wealth)` — "Major Financial Gain" and "Major Financial
   Loss" carry DIFFERENT evidence sets and DIFFERENT grades on 482012f1.
3. Negative controls: implemented, and calibration beats shuffled-birth with the gap reported.
4. At least one served verdict demonstrably moved by a calibrated multiplier (before/after receipt).
5. Remedy: bo_upaya wealth resonances ≠ 0; the leverage-ranked intervention (Venus, pre-2034
   window) served with its sādhanā join.
6. Anti-gaming pass on 1–4 + all prior wave batteries green (full regression).

**Campaign close (after this gate):** parked-items review + all DR-n rulings presented to the
native for ratification; register final sweep; CURRENT_STATE + SESSION_LOG campaign seal; the
master test becomes the standing per-release regression suite.

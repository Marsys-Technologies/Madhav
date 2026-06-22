---
artifact: CLAUDECODE_BRIEF_U4_SCHOOL_CONSENSUS_ACTIVATION_v1_0.md
canonical_id: CLAUDECODE_BRIEF_U4_SCHOOL_CONSENSUS_ACTIVATION
brief_for: U4 — School Consensus Activation (the 7-school triangulation engine; de-hardcode + persist + wire)
status: FINALIZED — built on prod-verified state (GATE A); ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D17 dormant, D18 chart-general+wire, D28 synthetic-fixture, D34 name-purge)
legacy_naming_note: >
  This workstream was historically tagged "M9" — that is DEAD legacy naming (D34). Referred to by what
  it IS: the 7-school triangulation engine (Parāśarī · Jaimini · Tājika · KP · Nāḍī · BNN · Yoginī).
  Do NOT reintroduce "M9" anywhere.
classification: UPSTREAM-ENABLER (L3-adjacent) — the heaviest enabler; feeds ph_nimitta (school-consensus axis) + U3 (C13 current)
swarm_coordination:
  wave: W2 (parallel-safe with U1/U2/U3 — disjoint files; TypeScript lib + a new adapter + persistence)
  blocked_by: [u1_dasha_consensus]   # the Yoginī engine reads the yogini dāśā rows U1 confirms reachable
  blocks: [u3_school_consensus_current, ph_nimitta_axis6, ph_phaladesa]   # C13 in U3 + the ph_nimitta school axis need this
  may_touch:
    - platform/src/lib/schools/**                                   # de-hardcode the 7 engines (read live signals)
    - platform/src/lib/schools/chart_data_adapter.ts                # NEW: DB (L1–L3) → ChartData + per-school SignalScore[]
    - platform/python-sidecar/services/school_consensus/**          # OR a sidecar persistence path (see §3.3)
    - platform/supabase/migrations/<33N>_school_consensus_tables.sql # persist (the 057–060 schema, renumbered)
    - platform/scripts/seed/asset_registry_seed.ts                  # register the school-consensus asset (if surfaced)
  parallel_safe_with: [u2_lifetime, u3_convergence_currents]
  hard_internal_gate: "CHART-GENERALITY GATE (D28): a SYNTHETIC fixture chart with deliberately-different placements MUST yield DIFFERENT school scores than the native — proving the engines read live data, not ABHISEK_CHART presets. This gate MUST pass before persist/wire."
---

# CLAUDECODE BRIEF — U4 School Consensus Activation

> **GATE-A VERIFIED (D17):** the 7-school triangulation engine (`platform/src/lib/schools/`) is BUILT,
> tested (78 green), and CLOSED — but **DORMANT**: persistence tables (057–060) are in `_archive/`,
> never applied; `school_runner` has ZERO callers outside the lib; and all 7 engines fall back to
> `defaultSignals` / `ABHISEK_CHART` presets when called without live signals. U4 makes the engine
> **chart-general** (reads live L1–L3 data), **persists** its convergence output, and **wires** it as
> a first-class consensus signal into ph_nimitta + U3's C13 current. This is the largest "already-built,
> just activate" win in the program. The legacy "M9" tag is purged (D34).

## §0 — Why it matters (the strongest single trust signal)
When Parāśarī AND Jaimini AND KP AND Yoginī all read a domain the same way, that agreement is the most
persuasive confidence signal in the tradition. An acharya cross-checks 2–3 schools by hand; this engine
runs 7 in parallel across 5 domains. The headline result already computed for the native — "5/5 domains
HIGH convergence (6/6 effective schools)" — proves the engine works; U4 makes it real (chart-general),
durable (persisted), and consumed (wired).

## §1 — VERIFIED ground truth (code, 2026-06-21)
- **The engines + orchestration exist:** `parashari_engine.ts`, `jaimini_engine.ts`, `tajika_engine.ts`,
  `kp_engine.ts`, `nadi_engine.ts`, `bnn_engine.ts`, `yogini_engine.ts`, `convergence_calculator.ts`,
  `school_runner.ts`, `types.ts`. 78 unit tests green.
- **The clean architecture (the de-hardcode is BOUNDED, not a rewrite):**
  - `ChartData` (types.ts line 54): `{ chartId, planets: PlanetPosition[] (with isExalted, house, …),
    yoginiDasha?, … }`. `ABHISEK_CHART` is a hardcoded const of this shape (line 115).
  - Each engine: `analyze(chartData, domain, signals?) → SchoolResult`. It reads
    `chartData.planets.find(...)` (real) BUT falls back to `signals ?? defaultSignals(domain, chartData)`
    (presets) when `signals` is not passed.
  - `school_runner.runSchoolsForDomain` (line 38-44) calls `engine.analyze(chartData, domain)` —
    **WITHOUT the signals arg** → always hits `defaultSignals`. **THIS is the hardcode.**
  - `convergence_calculator.computeConvergence`: HIGH ≥5/7 agree, MEDIUM 4/7, LOW <4/7; per-domain
    mean/std; divergence detection; Tājika excluded if `[VARSHA_KUNDALI_PENDING]`; BNN damped if
    `[TRANSIT_DATA_PENDING]`.
- **Persistence tables (057–060) NOT in prod** (in `_archive/`): `school_signal_coverage`,
  `school_analysis_runs`, `convergence_scores`, `school_disagreements`.
- **The two pending flags ARE resolvable (C4):** Tājika `[VARSHA_KUNDALI_PENDING]` ← `ga_tajaka` /
  `l1_tajik_varsha_year_lords` (240 rows); BNN `[TRANSIT_DATA_PENDING]` ← `ka_gochara` service.
- **Zero external callers (C3):** activation is purely ADDITIVE — no refactor of consumers.

## §2 — The four tasks (D18)

### Task A — DE-HARDCODE: feed the engines LIVE signals (the main lift)
The fix is NOT to rewrite the school scoring (it's sound) — it is to (1) build a real `ChartData` for
any chart and (2) pass each engine real `signals` so it never reaches `defaultSignals`.
- **A.1 — NEW `chart_data_adapter.ts`:** a function `buildChartData(chartId, ayanamshaId) → ChartData`
  that reads `chart_facts` (graha positions, houses, dignities → `planets: PlanetPosition[]`),
  `chart_dashas` (the `yogini` system rows → `yoginiDasha`), etc. NO `ABHISEK_CHART` const for real charts.
- **A.2 — per-school live signals:** `buildSchoolSignals(chartId, school, domain) → SignalScore[]`
  derived from `bodha_msr_signals` (filtered by the school's tradition + the domain) — the real
  signal store, not presets. Each engine's `defaultSignals` becomes the FALLBACK-OF-LAST-RESORT only
  (or is removed once live signals are guaranteed).
- **A.3 — route through `school_runner`:** change `runSchoolsForDomain` to pass the live `signals`
  to `engine.analyze(chartData, domain, signals)`. The engines' school-specific logic is unchanged.

### Task B — RESOLVE the two pending flags
- **Tājika** ([VARSHA_KUNDALI_PENDING]): wire `tajika_engine` to read the varṣa (annual) chart from
  `l1_tajik_varsha_year_lords` (varṣeśa + muntha per year) → Tājika participates at full weight.
- **BNN** ([TRANSIT_DATA_PENDING]): wire `bnn_engine` to call `ka_gochara` for live transit positions
  → BNN confidence restored from the damped 0.45 to its full 0.85.

### Task C — PERSIST the convergence output
- Apply the 057–060 schema (renumbered into the L4 range per the two-174 trap / D14):
  `school_signal_coverage`, `school_analysis_runs`, `convergence_scores`, `school_disagreements`,
  scoped by `chart_id`. Write `runFullTriangulation`'s 5-domain × 7-school results + the per-domain
  convergence (HIGH/MEDIUM/LOW + mean/std) + the divergences.
- **[SPEC]** decide the execution home: the engines are TypeScript (`platform/src/lib/schools/`).
  Either (a) a Next.js route/job runs them and writes the tables, or (b) a small sidecar path invokes
  them. RECOMMEND (a) — keep the TS engine in TS; a build-time route computes + persists per chart.

### Task D — WIRE the consensus into prediction
- **D.1 — ph_nimitta Axis 6 (school axis):** expose `school_consensus(chart_id, domain) → {n_of_7,
  per_school, divergence_flag}` from `convergence_scores`; ph_nimitta reads it as a confidence axis.
- **D.2 — U3 C13 current:** the same `school_consensus` feeds U3's `school_consensus` convergence
  current (the 2nd-pass current, D35) — one source, two consumers.

## §2.5 — ELEVATION: from agreement-count to a structured weighted-expert panel (D36)
> Seven independent expert opinions contain far more than a headcount. The engine ALREADY computes
> mean/σ per domain, divergence detection, and a plain-language narrative; the `school_disagreements`
> table ALREADY defines 4 disagreement classes + resolution verdicts — all currently discarded. These
> four elevations are MOSTLY WIRING of existing output, not new computation.

### E1 — Disagreement intelligence (the highest-value elevation)
Stop storing a bare divergence flag. Populate `school_disagreements` with the DESIGNED richness and
USE it downstream:
- Classify each cross-school disagreement into the table's 4 `disagreement_class` values:
  `method_divergence` (schools assess the same domain by different methods), `signal_gap` (some schools
  silent), `tradition_specificity` (the signal only exists in one tradition's framework), and —
  the high-value one — **`temporal_scope`** (the schools agree on WHAT will happen and disagree only on
  WHEN). A `temporal_scope` disagreement is a **timing-refinement signal**, NOT a contradiction —
  ph_nimitta should treat it as "outcome agreed, timing uncertain → widen the window / flag for U2/U3
  refinement," not as low confidence.
- Record the `resolution_verdict` (`affirming_majority` / `denying_majority` / `context_dependent` /
  `unresolved`) + `schools_affirming` / `schools_denying` / `schools_silent` arrays.
- Expose `school_disagreement(chart_id, domain)` so ph_nimitta + ph_phaladesa can surface *why* schools
  differ, not just that they do.

### E2 — Per-domain school-authority weighting (D33-style: Cowork proposes, swarm tunes within bounds)
Replace the flat 7-way headcount with a **per-domain authority-weighted consensus** — classically the
schools are NOT equally authoritative per domain. **Cowork-proposed authority weights** (per domain,
each row re-normalized to 1.0; swarm tunes within ±0.05 bounds via internal-consistency):

| Domain | Parāśarī | Jaimini | KP | Tājika | Nāḍī | BNN | Yoginī | Rationale |
|---|---|---|---|---|---|---|---|---|
| CAREER | 0.20 | 0.22 | 0.16 | 0.12 | 0.12 | 0.08 | 0.10 | Jaimini (chara-karaka/status) + Parāśarī primary |
| HEALTH | 0.24 | 0.12 | 0.14 | 0.12 | 0.18 | 0.10 | 0.10 | Parāśarī + Nāḍī (specific affliction) lead |
| RELATIONSHIP | 0.22 | 0.16 | 0.14 | 0.14 | 0.14 | 0.10 | 0.10 | Parāśarī (7th/Venus) + balanced |
| SPIRITUAL | 0.22 | 0.18 | 0.10 | 0.10 | 0.16 | 0.10 | 0.14 | Parāśarī + Jaimini (Ketu/moksha) + Yoginī rhythm |
| PSYCHOLOGICAL | 0.22 | 0.14 | 0.12 | 0.12 | 0.14 | 0.12 | 0.14 | Parāśarī (Moon/Mercury) + balanced |
| (timing-cross-cut) | — | — | **boost KP +0.04** | — | — | — | — | KP is the precision-timing authority for any WHEN question |

> The weighted consensus = Σ(school_score × domain_authority_weight). The HIGH/MEDIUM/LOW level is then
> computed on the weighted agreement, so a school weak in a domain no longer dilutes the signal equally.
> Swarm tunes within ±0.05 and re-normalizes; logs final weights to the re-sealed record.

### E3 — Direction + magnitude (not just agreement)
The engine computes `meanDomainScore` (the strength + direction: strongly-positive … strongly-negative
on a 0–5 scale) + `stdDomainScore` (σ, the spread). Feed BOTH into the consensus output and into
ph_nimitta: a prediction carries "schools agree, STRONGLY POSITIVE, σ=0.25 (tight)" not merely "6/7
agree." Tight agreement on a strong score is the highest-confidence case; wide spread flags caution.

### E4 — Persist + surface the NL reasoning
`buildConvergenceNarrative` already generates plain-language "why" ("Mean 4.0/5, σ=0.25; DIVERGENCE:
Yoginī contradicts the plurality on spirituality"). Store it (in `convergence_scores` or
`school_analysis_runs`) and surface it so every consensus carries explainable, acharya-grade reasoning
that ph_phaladesa's dossier can quote directly.

## §3 — The CHART-GENERALITY GATE (D28 — the integrity-critical hard gate)
> The entire value of U4 is that the engines read REAL data, not this native's presets. The ONLY
> mechanical proof is: **a different chart yields different scores.**

- Build a **SYNTHETIC fixture chart** (`schools/__fixtures__/synthetic_chart.ts`) with deliberately
  DIFFERENT placements than the native (e.g. different Lagna, different exaltations, a different
  Yoginī state).
- **GATE:** `runFullTriangulation(syntheticChart)` MUST produce per-domain school scores that DIFFER
  materially from `runFullTriangulation(nativeChart)`. If they're identical → the engines are still
  reading presets → de-hardcode FAILED. **This gate MUST pass before Task C (persist) and Task D (wire).**
- (Abhinandan `1c826d5a` is the later REAL-chart validation when Phase E opens — D28; not required now.)

## §4 — Acceptance criteria [tagged; prod-verified]
1. `[pytest/vitest]` `buildChartData(chartId)` produces a real `ChartData` from L1–L3 (a DIFFERENT chartId yields different planets) — no `ABHISEK_CHART` for real charts.
2. `[vitest]` each engine receives live `signals` via `school_runner` (assert `defaultSignals` is NOT reached for a chart with signals).
3. `[vitest — CHART-GENERALITY GATE]` the synthetic fixture yields DIFFERENT per-domain school scores than the native (the D28 hard gate).
4. `[vitest]` the 78 existing tests still pass (regression); the native's known result (5/5 HIGH convergence) reproduces when fed the native's REAL data.
5. `[vitest]` Tājika resolves via `l1_tajik_varsha_year_lords` (no [VARSHA_KUNDALI_PENDING]); BNN via `ka_gochara` (no [TRANSIT_DATA_PENDING]; confidence 0.85).
6. `[persist]` `convergence_scores` + `school_disagreements` populated for the native; chart-scoped; `$1` count_sql if surfaced as an asset.
7. `[wire]` `school_consensus(chart_id, domain)` returns {n_of_7, per_school, divergence}; ph_nimitta Axis 6 + U3 C13 consume it.
8. `[anti-drift]` the engines READ L1–L3; write only the school-consensus tables (never bodha_*/kala_*/ganita_*).
9. `[psql_prod + curl_prod]` convergence persisted; if surfaced as a cockpit asset, it renders lit.
10. `[FORENSIC]` 7/7 holds; only `482012f1` (+ the synthetic fixture for the generality gate only).
11. `[vitest — E1]` `school_disagreements` is populated with the 4 `disagreement_class` values + `resolution_verdict` + affirming/denying/silent arrays; a `temporal_scope` disagreement is exposed to ph_nimitta as a timing-refinement signal (NOT low confidence).
12. `[vitest — E2]` the consensus is per-domain AUTHORITY-WEIGHTED (Σ school_score × domain_weight); weights within ±0.05 of the §2.5 proposal and re-normalized per domain; the HIGH/MEDIUM/LOW level is computed on the weighted agreement.
13. `[vitest — E3]` the output carries `meanDomainScore` (direction+magnitude) + `stdDomainScore` (σ), not just an agreement count; ph_nimitta receives both.
14. `[vitest — E4]` `buildConvergenceNarrative` output is persisted + exposed; ph_phaladesa can read the plain-language "why".

## §5 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/u4-school-consensus
# the engine architecture + the hardcode point
sed -n '54,140p' platform/src/lib/schools/types.ts
sed -n '10,70p' platform/src/lib/schools/parashari_engine.ts
sed -n '38,75p' platform/src/lib/schools/school_runner.ts
# the archived persistence schema to renumber + apply
ls platform/supabase/migrations/_archive/05[789]_* platform/supabase/migrations/_archive/060_*
# the pending-flag data sources
psql "$DATABASE_URL" -c "SELECT varsha_year, varshesha_by_tajik_classical FROM l1_tajik_varsha_year_lords WHERE chart_id=:'NATIVE' LIMIT 3;"
cd platform && npx vitest run tests/schools
```

## §6 — Definition of done
- [ ] `chart_data_adapter.ts` builds real ChartData + per-school live signals from L1–L3; presets retired for real charts.
- [ ] `school_runner` passes live signals; Tājika + BNN pending flags resolved.
- [ ] CHART-GENERALITY GATE passes (synthetic fixture ≠ native scores) — before persist/wire.
- [ ] Convergence persisted (057–060 schema, renumbered); `school_consensus()` read-path live.
- [ ] Wired into ph_nimitta Axis 6 + available for U3 C13; 78 tests green; native 5/5 result reproduced; FORENSIC 7/7.

## §7 — VALUE ADDED BY THIS BRIEF
1. **Activates an entire built-but-dormant consensus engine** — turning "5/5 schools agree" from a
   one-off research result into a live, chart-general, top-tier confidence axis on every prediction.
2. **Bounds the de-hardcode precisely** — the scoring logic is sound; the fix is a chart-data adapter +
   routing live signals, NOT a rewrite. The brief pinpoints the exact hardcode (`runSchoolsForDomain`
   omitting the signals arg → `defaultSignals`).
3. **Gates the integrity risk** — the synthetic-fixture generality gate mechanically proves the engines
   read live data before anything persists, killing the "still hardcoded to this chart" failure mode.
4. **Resolves two long-pending flags** using L3 services that now exist (Tājika ← ga_tajaka, BNN ←
   ka_gochara) — bringing two schools to full weight.
5. **One source, two consumers** — `school_consensus()` feeds both ph_nimitta's school axis and U3's
   C13 convergence current; no duplication.
6. **ELEVATED from a vote to a weighted-expert panel (D36)** — disagreement INTELLIGENCE (esp.
   timing-only disagreement as a refinement signal), per-domain authority weighting (the right schools
   count more), direction+magnitude (not just agreement), and persisted plain-language reasoning — all
   mostly wiring of output the engine ALREADY computes but currently discards. This is what makes the
   consensus acharya-grade rather than a show of hands.

## §8.5 — Task A.0 PREREQUISITE (surfaced at R4 verification — added to scope)
> **Code-verified (2026-06-21):** `bodha_msr_signals` does NOT carry a per-school tag. The per-school
> classification lives in `school_signal_coverage` (the 057 schema: `signal_id → school → coverage_type
> {primary|secondary|silent}` + confidence + attribution chunk) — which is in `_archive/`, NOT applied,
> and whose data ("4,011 classifications = 573 signals × 7 schools") was computed but "DB insertion
> deferred." So `buildSchoolSignals` (Task A.2) has a hidden prerequisite.

**Task A.0 (NEW, runs before A.1/A.2):** populate `school_signal_coverage` for the native —
(a) apply the 057 schema (renumbered into the L4 range), and (b) run the classification (recover the
4,011-row script output if it persisted, else re-run the school-coverage audit that produced it). The
adapter's `buildSchoolSignals` reads `school_signal_coverage` (filter `coverage_type='primary'` for the
school's own-tradition signals; optionally include `secondary`). Without A.0, A.2 hits a missing-table wall.

## §9 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [RESOLVED — Cowork default locked]:** Task C execution home = **(a) a Next.js route/job** runs
  the TS engines + persists (keeps the TS engine in TS; a build-time per-chart route computes + writes
  the school tables).
- **R2 [RESOLVED — Cowork default locked]:** **surface school-consensus as a cockpit asset** (its own
  registry row + chart-scoped `$1` count_sql) so it is visible + cockpit-verifiable (aligns with the
  visual-seal discipline). Kind = artifact (it stores convergence rows).
- **R3 [RESOLVED — Cowork default locked]:** keep `defaultSignals` as a **guarded last-resort fallback
  that LOGS a warning** — so a missing-signal case is visible, never silently presetted; the generality
  gate (§3) ensures live signals are the norm. (Do not silently delete it; the warning surfaces gaps.)
- **R4 [RESOLVED — verification found a prerequisite]:** the per-school tag is NOT on `bodha_msr_signals`;
  it lives in `school_signal_coverage` (archived, unapplied, data deferred). **→ added Task A.0 (§8.5)**
  to populate it before the adapter reads per-school signals. R4 is closed by adding that step.

---
*End of CLAUDECODE_BRIEF_U4_SCHOOL_CONSENSUS_ACTIVATION v1.0 — CLOSED. The 7-school triangulation engine,
activated. Built to maximal value: Task A.0 prerequisite (populate school_signal_coverage), the precise
de-hardcode (adapter + live signals), pending-flag resolutions, the chart-generality hard gate,
one-source-two-consumers wiring. R1–R4 resolved.*

---
artifact: DRAFT_CLAUDECODE_BRIEF_M9_SCHOOL_ACTIVATION_v0_1.md
canonical_id: DRAFT_CLAUDECODE_BRIEF_M9_SCHOOL_ACTIVATION
brief_for: M9 multi-school triangulation engine — DE-HARDCODE + PERSIST + WIRE (activate the dormant POC)
status: DRAFT v0.1 — full detail captured; SIZED by reconciliation (Q3/C2/C3/C4)
version: 0.1
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D17, D18)
classification: UPSTREAM-ENABLER (feeds ph_nimitta/ph_phaladesa school-consensus axis); not a ph_* asset
---

# DRAFT BRIEF — M9 Multi-School Triangulation Activation

> **The capability exists and is CLOSED but DORMANT (D17).** Seven school engines + convergence
> calculator + school_runner, 78 green tests, headline result "5/5 domains HIGH convergence." It is
> NOT wired/persisted and its scores are partly hardcoded to this native. Native ruled (D18): make it
> chart-general + persist + wire into L4 as a consensus confidence axis. This brief captures the full
> activation plan; exact lift is sized by the reconciliation.

## §0 — What exists (CODE-VERIFIED, D17)
- `platform/src/lib/schools/`: `parashari_engine.ts`, `jaimini_engine.ts`, `tajika_engine.ts`,
  `kp_engine.ts`, `nadi_engine.ts`, `bnn_engine.ts`, `yogini_engine.ts`, `convergence_calculator.ts`,
  `school_runner.ts`, `types.ts` (with `ABHISEK_CHART` const).
- `convergence_calculator`: HIGH ≥5/7 schools agree, MEDIUM =4/7, LOW <4/7; per-domain mean/std;
  divergence detection (isDivergent if ≥2 schools contradict plurality); Tājika excluded when
  [VARSHA_KUNDALI_PENDING]; BNN confidence reduced when [TRANSIT_DATA_PENDING].
- `school_runner.runFullTriangulation`: 5 domains × 7 schools = 35 results.
- Migrations 057–060 (`school_signal_coverage`, `school_analysis_runs`, `convergence_scores`,
  `school_disagreements`) are in `platform/supabase/migrations/_archive/` — **likely never applied**
  `[RECON Q3]`.

## §1 — The four activation tasks (D18)

### Task A — DE-HARDCODE (make chart-general) `[RECON C2 sizes this]`
Each engine has a `defaultSignals(domain, chartData)` that returns FIXED score arrays (Abhisek
presets) rather than deriving from chart data. Replace these with live derivation from L1–L3:
- Parāśarī: read `bodha_msr_signals` + `chart_facts` (house lords, dignities, aspects) for the domain.
- Jaimini: read chara-karaka + arudha signals (`ga_sensitive`, `chart_facts`).
- KP: read `chart_facts` KP-lord rows (`graha_kp_lords`, `cusp_kp_lords`).
- Yoginī: read the `yogini` dāśā rows from `chart_dashas` `[RECON Q1]`.
- Nāḍī / BNN: read the corresponding signal families.
- The engines KEEP their school-specific scoring logic; only the DATA SOURCE changes from preset → live.

### Task B — RESOLVE the two pending flags
- `[VARSHA_KUNDALI_PENDING]` (Tājika): now resolvable — `ga_tajaka` / `l1_tajik_varsha_year_lords`
  provides the varsha (annual) chart. Wire Tājika to read it.
- `[TRANSIT_DATA_PENDING]` (BNN): now resolvable — `ka_gochara` provides live transit positions. Wire BNN to call it.

### Task C — PERSIST `[RECON Q3]`
Apply migrations 057–060 (move from `_archive/` to active, renumbered into the current series if
needed — mind the two-dir numbering / D14) and write the convergence results per domain per chart to
`convergence_scores` + `school_disagreements`. This makes school-consensus a stored, queryable axis.

### Task D — WIRE into L4
Expose a `school_consensus(chart_id, domain)` read path that `ph_nimitta` Axis 6 + `ph_phaladesa`
consume: returns N-of-7 concurring + per-school direction + the divergence flag.

## §2 — Schema (persistence, per Task C)
Reuse the existing 057–060 table definitions (school_signal_coverage, school_analysis_runs,
convergence_scores, school_disagreements). Add `chart_id` scoping + `$1` count_sql if surfacing as a
cockpit asset. `[RECON Q3 confirms whether these tables exist in prod or need applying]`.

## §3 — Acceptance criteria
1. `[pytest]` each engine derives its domain scores from LIVE chart data (no `defaultSignals` presets); a DIFFERENT chart yields DIFFERENT scores (chart-generality proof).
2. `[pytest]` Tājika resolves via `ga_tajaka` (no [VARSHA_KUNDALI_PENDING]); BNN via `ka_gochara` (no [TRANSIT_DATA_PENDING]).
3. `[pytest]` `runFullTriangulation` reproduces the native's known result (5/5 HIGH convergence) when fed the native's real data — regression guard.
4. `[persist]` convergence_scores + school_disagreements populated for the native `[RECON Q3]`.
5. `[wire]` `school_consensus(chart_id, domain)` returns N-of-7 + per-school + divergence; ph_nimitta Axis 6 consumes it.
6. `[anti-drift]` the engines READ L1–L3; they write only the M9 convergence tables (never bodha_*/kala_*/ganita_*).
7. `[psql_prod + curl_prod]` convergence persisted; if surfaced as an asset, cockpit shows it lit.

## §4 — VALUE ADDED
Activates an entire built-but-dormant consensus engine — turning "5/5 schools agree" from a one-off
research result into a live, chart-general, top-tier confidence axis on every prediction. Multi-school
agreement is the most persuasive confidence signal in the tradition; no acharya runs 7 schools in
parallel per domain. This is the largest single "already-built, just activate" win in the expansion.

## §5 — RECON dependencies
- `[Q3]` do the 057–060 tables exist in prod / are they populated? (sizes Task C)
- `[C2]` how hardcoded is each engine really? (sizes Task A — the main lift)
- `[C3]` confirm nothing currently consumes school_runner (confirms "dormant")
- `[C4]` confirm `ga_tajaka` + `ka_gochara` can feed Tājika/BNN (confirms Task B feasible)
- `[Q1]` is the `yogini` dāśā system prod-populated? (Yoginī engine needs it)

---
*End of DRAFT M9 activation v0.1. De-hardcode + resolve-pending + persist + wire. Sized by reconciliation.*

---
canonical_id: BA_ENDGAME_ACTIVITY_PLAN
version: 1.0
status: CURRENT — the native-sequenced wrap-up plan for the Beyond-Acharya program
created: 2026-07-04
author: Cowork (strategic track) — for native Abhisek Mohanty
sequencing_authority: >
  This plan REORDERS the remaining run to the native's stated preference (2026-07-04): do ALL build/code
  activities first, then a Chrome-MCP inspection of the Nirmāṇa build tracker, then ONE full asset rebuild
  with everything in place, then a live end-to-end MCP demonstration as the completion gate. It does not
  change WHAT the phases build (UNIFIED_EXECUTION_PLAN + MASTER_PLAN v2.1 still own substance) — only the
  build-vs-rebuild boundary and the verification order.
depends_on: BA_STRATEGIC_TRACK_HANDOFF_v1_0 §3/§5, BA_RUN_LEDGER_v1_0, BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0
---

# BEYOND-ACHARYA — ENDGAME ACTIVITY PLAN (native-sequenced)

## §0 — The shape you asked for (and my verdict on it)

**Your proposed order:** all remaining activities → a Chrome-MCP look at the Nirmāṇa tracker to prove the
new assets are actually wired/visible → ONE clean rebuild with everything in place → a live end-to-end MCP
run with full backend visibility = completion.

**My verdict: correct, and better than the incremental-rebuild default in two ways.** (1) One rebuild "with
everything in place" avoids regenerating L2 now and again later — it honours the one-shot discipline at the
whole-instrument scale, not just per-layer. (2) Your Nirmāṇa inspection is exactly the right pre-rebuild
gate: if a new asset isn't visible in the tracker with a correct `count_sql` and DAG edge, the rebuild
either skips it or builds it wrong — catching that BEFORE the expensive rebuild is precisely where it
belongs. And your final step quietly fixes the program's single biggest standing scar: every "COMPLETE" so
far is *best-evidence* (Ring-1 + deploy-success), never an authenticated live prod probe — because the run
never had an MCP key. Connecting MCP to me for the E2E is what finally closes that Ring-2 gap.

**Three refinements I recommend (all preserve your order):**
- **R1 — one decision before the code freezes:** ratify the four W1-seed §0.2 judgment items *first*. Two of
  them (`bala_gate` "present-but-enfeebled", and moving `verification_certainty` from a salience multiplier
  to a served confidence dimension) change the *stored* salience v2 formula. If they land after P3B is
  coded, we recut salience twice. A 15-minute decision buys a clean single freeze (possibly `priors_version
  → 1.1`).
- **R2 — keep "one rebuild" but make it Abhinandan-first *within* that single event.** The whole-cascade
  rebuild runs on the test chart `1c826d5a` first, passes every gate, THEN runs on your chart `482012f1`.
  That's still "one rebuild at the end," but the native chart never sees an unproven writer — the discipline
  that has protected the program all along, kept intact.
- **R3 — a 10-minute preliminary Nirmāṇa glance NOW (optional).** You already suspect the P3A L0 assets
  aren't showing. If they're not, that's a wiring bug to fix *inside* the code phase — cheaper than
  discovering it at the formal inspection after all code is done. The full inspection still happens where you
  put it; this is just an early smoke check.

**Completion definition — you're right, with one addition.** "Live E2E query works on prod with full
visibility" is the demonstrable done. The program's own north-star adds two things worth including so
"complete" is rigorous, not just impressive: (a) the golden-question eval **non-regresses on both charts**
(G10-QT ≥13/15), and (b) **at least one honest P6 skill table exists** (even if the finding is "no family
beats the null" — published with equal prominence, per your own ratification). Both fold naturally into the
final E2E stage. Details in §5.

---

## §1 — STAGE A: ALL BUILD / CODE ACTIVITIES (no chart-data rebuild yet)

Everything here lands as migrations + writers + tools + serving code + `asset_registry` rows + DAG edges,
deployed to prod and Ring-1/Ring-2-verified — but **no chart data is regenerated**. At the end of Stage A
every asset is *registered and its writer deployed*; the data is still old/partial until Stage C.

> Migration numbering: next-free is **391** (385–389 = P3A; 390 = M1 fix). Re-scan BOTH dirs at each brief.

- **A0 — Close the two open fixes on prod.** Confirm M1 (`ga_condition` count_sql, mig 390) and M2
  (`bodha_discoveries_get` → `FROM bodha_discoveries`, `register_p1_synthesis.ts`) are Ring-2 prod-verified,
  not just merged (PR #406). [gate: both services' live Cloud Run SHA == merged HEAD]
- **A1 — Ratify the four W1-seed §0.2 items (R1).** Native glance: domain granularity; `bala_gate` served
  state; `verification_certainty` re-scale; event base-rate priors. Record each in `BA_JUDGMENT_LEDGER`. If
  the salience formula changes, bump `priors_version`. [gate: rulings logged; salience formula frozen]
- **A2 — P3B code (L2 regeneration writers, NOT the run).** Unified salience v2 formula (class_prior ×
  varga_weight × specificity × rescaled_verification × condition_terms × bala_gate × functional_context;
  percentile-in-class; NULL-propagation; robustness; aggregation composites; signature_tier recut;
  constituent re-resolve ≥99%; classical_sources bridge ≥60%); typed graph edges + valence + pagerank
  backfill; contradiction domain-attribution + reconciliation; `bo_pratijna` Promise Register; `bo_sangati`
  triangulation; `bo_upaya` resonance de-degeneracy. **Deploy the code; defer the regeneration to Stage C.**
- **A3 — P4 code.** Verdict object (mi_darshana home) + query-time judgment terms (activation, karaka
  congruence, varga affinity) + attention budget 70/20/10 + complement pass (`tail_divergence`) +
  Mahā-Brief composer + Q1–Q9 golden-eval harness + PD-5 UI refactor.
- **A4 — P5A code.** Kala activation across 7 dasha systems (`ka_yojaka` EXT); `ka_avadhi` period dossiers;
  `ka_taranga` activation waveform (coarse stored, fine = service); conflation fixes (`ka_sangam`
  confidence≠convergence; `ka_vighnakara` → single-truth `bg_combustion_orbs`).
- **A5 — P5B code.** `ph_nimitta` v2 anchors (posterior = base_rate × promise × activation × trigger lifts;
  structured falsifiers; full probability range); `ph_muhurta` activity-aware election; prashna path
  (`chart_type='prashna'`, migration 385 already present).
- **A6 — P6 code.** MIMAMSA_V2 engine: LEL intake FROM `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (the DB table
  is empty); blind retrodiction + control windows + ablation; hierarchical shrinkage; two-key snapshots;
  **3-site embedded-weight unification** (mi_kula/mi_pariksha/mi_pramana → bg_class_priors); sensitivity
  harness. Scoring paths 100% LLM-free.
- **A7 — P7A code.** Classical completions: Nadi extraction, AV-transit L0 gates, avasthas — as new
  fact_categories flowing through salience v2 ranked (not noise).
- **A8 — P7B code/UI.** Portal learning loops: ask-cards, period-attestation card, structured LEL intake
  form, prashna follow-up scheduler, calibration-snapshot co-sign UI.

**Stage-A exit:** every new/changed asset is in `asset_registry` (correct layer, sort_order, scope,
`has_writer=true`, chart-scoped `count_sql` with `$1`), every writer deployed, the full L0→L5 DAG wired,
all migrations applied on prod (both services on the merged SHA). **Zero chart data rebuilt yet.**

---

## §2 — STAGE B: NIRMĀṆA BUILD-TRACKER INSPECTION (Chrome MCP; your gate, before rebuild)

Purpose: prove — visually, from the actual portal — that every asset Stage A registered is **present,
correctly placed, correctly counted, and correctly wired** in the Nirmāṇa tracker, so the Stage-C rebuild
builds the complete instrument, not a subset. This is where your "I don't see the new assets" concern gets
resolved definitively.

I will (Chrome MCP, prod portal, owner/native account):
- **B1 — Presence:** every new asset renders in its layer band — L0 `bg_class_priors`, `bg_ghatana`,
  `bg_formula_constants`; L2 `bo_pratijna` (+ changed `bo_laksana/bimba/karanajala/sangati/upaya`); L3
  `ka_avadhi`, `ka_taranga`; L4/L5 changed assets; P7 completions. Count present vs. the registry.
- **B2 — Metadata correctness:** each shows the right sanskrit/english name, layer, sort_order, scope, and a
  non-error `count_sql` (chart-scoped). Flag any asset showing 0/stale/error where data should exist.
- **B3 — DAG wiring:** the dependency edges render (roots `bg_class_priors/bg_ghatana/bg_formula_constants`
  → L1 → `bo_laksana` → … → L5). No orphan nodes, no missing edges.
- **B4 — State correctness:** new assets show as *unbuilt/stale* (expected — not yet rebuilt), not
  silently "green" off a phantom count (the `asset_throughput.rows_written` stale-display trap).
- **B5 — Root-cause any gap** (why you don't see them today): likely one of — registry row missing/wrong
  layer; cockpit `/api/cockpit/registry` not returning them; `has_writer=false`; or the tracker reading a
  cached source. **Fixes found here are small and land as a Stage-A addendum, then B re-runs.**

**Stage-B exit:** the tracker is a faithful mirror of the registry + DAG; every intended asset is visible,
correctly counted, and correctly wired; zero unexplained gaps. Only then do we rebuild.

---

## §3 — STAGE C: THE ONE FULL REBUILD (everything in place; Abhinandan-first within it, R2)

- **C0 — Pre-rebuild audit refresh + snapshot.** Re-verify every writer DELETE predicate (no
  accrete/over-delete), take the DB snapshot, rehearse rollback, write the blast-radius statement for you to
  read first (as before).
- **C1 — Abhinandan `1c826d5a` FULL cascade rebuild L0→L5** (proving ground). Run ALL gates: FORENSIC-style
  invariants, **contamination** (Abhinandan Sun=Aquarius/Moon=Gemini ≠ your Sun=Capricorn/Moon=Aquarius),
  **degeneracy gate on every scoring column** (no salience/posterior/skill column collapses to a constant —
  the 2.326672/0.28 scars), **constituent re-resolve ≥99%**, **classical_sources ≥60%**, cockpit live
  counts == `count_sql`, golden-eval spot non-regressed.
- **C2 — Gate review (me).** Only if Abhinandan passes every gate line-by-line (evidenced, not asserted) do
  we touch your chart.
- **C3 — Native `482012f1` FULL cascade rebuild L0→L5.** Same gate battery **+ FORENSIC 7/7** must survive
  the full re-derivation (Sun Capricorn · Moon Purva Bhadrapada · Lagna Aries ×5 ayanamshas · Shukla Tritiya
  · Ravivara · Shiva · Garaja). Confirm `bhava_arudha` = 12 × 5 ayanamshas on both charts (the P3A deferral,
  now closed).

**Stage-C exit:** both charts fully rebuilt through L5, every gate passed on evidence, snapshots retained,
P3A flips COMPLETE, and the instrument's data is now the salience-v2 / promise / activation / anchor-v2 /
learning-ready corpus.

---

## §4 — STAGE D: LIVE END-TO-END VIA MCP (the completion demonstration)

- **D1 — Connect MCP to Claude + provision an MCP API key.** This is also the fix for the standing Ring-2
  gap: authenticated live prod probes finally become possible. (Everything before this was best-evidence.)
- **D2 — Live E2E, full visibility.** From prod, trigger and watch end-to-end: a domain judgment
  (`apex_career_assess` / marriage / health / wealth), a period reading (Q1 over `ka_avadhi`), an
  undertaking (Q4 muhurta), and the **Mahā-Brief** (whole-chart one-shot). Verify each returns a proper
  **verdict object** — reconciled claim, evidence, weighed contradictions, tradition concordance, activation
  state, ayanamsha robustness, confidence, decidable falsifier, citations, and the `tail_divergence` memo —
  with the LLM narrating on top, not computing.
- **D3 — Rigorous done (the two additions to your definition).** (a) Golden set on BOTH charts: G10-QT
  ≥13/15, no regression; the 38-topic four-measure completeness matrix green. (b) At least one honest **P6
  skill table** produced from the leakage-audited retrodiction pipeline — a real family-vs-null result
  (published even if null). Plus the north-star four (judgment / prophecy / learning / integrity) and a
  red-team pass.
- **D4 — Close-out.** Worktree cleanup; `BA_RUN_REPORT` for your retrospective review; CURRENT_STATE +
  Judgment Ledger synced; this track independently audits the report. **Program complete.**

---

## §5 — ONE-LINE SEQUENCE (what to actually do, in order)

A0 fixes-verified → **A1 ratify §0.2** → A2–A8 all phase CODE deployed (no rebuild) → **[optional R3: 10-min
Nirmāṇa smoke now]** → **B Nirmāṇa tracker inspection (Chrome MCP) + fix gaps** → C0 audit+snapshot → **C1
Abhinandan full rebuild + gates** → C2 gate review → **C3 native full rebuild + FORENSIC 7/7** → **D1
connect MCP** → D2 live E2E + Mahā-Brief → D3 golden eval + P6 skill table + red-team → D4 run report =
**COMPLETE**.

*End of BA_ENDGAME_ACTIVITY_PLAN v1.0. Your sequence, with Abhinandan-first preserved inside the single
rebuild, the §0.2 ratification pulled ahead of the code freeze, and the E2E doubling as the Ring-2
authenticated-probe closure. Awaiting your nod on R1–R3 and the completion-definition additions.*

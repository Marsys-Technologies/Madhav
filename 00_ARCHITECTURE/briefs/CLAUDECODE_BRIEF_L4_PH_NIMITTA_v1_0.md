---
artifact: CLAUDECODE_BRIEF_L4_PH_NIMITTA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L4_PH_NIMITTA
brief_for: ph_nimitta — Predictive Anchors (THE SPINE of L4 Phala) [maximal capacity]
status: FINALIZED — built on prod-verified state (GATE A) + ratifications (D20–D38); ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: DRAFT_CLAUDECODE_BRIEF_L4_PH_NIMITTA_SUPREME_v0_1.md
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D8 axes, D21 G-LADDER, D37 bhavishya-inherit, D38 5 elevations, D11 subsystem, D26 spine-gate)
swarm_coordination:
  wave: W3 (first L4 asset; AFTER the 4 upstream enablers U1–U4 + the enriched convergence build)
  blocked_by: [u1_dasha_consensus, u2_lifetime, u3_convergence_currents, u4_school_consensus_activation]
  blocks: [ph_muhurta, ph_pratikara, ph_sankrama, ph_sodhana, ph_phaladesa, ph_pramana]
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py
    - platform/python-sidecar/services/ph_nimitta/**          # engine: derivation + axes + elevations
    - platform/supabase/migrations/330_phala_anchors_and_drop_kala_timeline.sql   # first L4 migration (also DROPs kala_timeline / CF.L3.2)
    - platform/scripts/seed/asset_registry_seed.ts
    - platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  hard_internal_gate: "SPINE-FIRST (D26): prove ONE anchor end-to-end across ALL axes + elevations (real convergence/discovery/bhavishya root → derived domain → magnitude + ranged confidence + causal chain + consensus + karmic-arc + actionability + contradiction → cites real ids → anti-drift clean) BEFORE any other L4 asset fans out."
---

# CLAUDECODE BRIEF — ph_nimitta (Predictive Anchors) — THE SPINE [maximal capacity]

> **What it is, in one line:** ph_nimitta turns the enriched convergence windows, the discoveries, and
> L3's existing forward-projections into **falsifiable predictive anchors** — each carrying WHAT will
> happen, WHEN (as a range with a peak), HOW BIG, HOW SURE (as a range), WHY (traced through the chart's
> causal graph), how many independent methods AGREE (dāśā + school consensus), where it sits in the
> KARMIC ARC, whether it is INFLUENCEABLE, and whether the chart itself is CONTESTED about it. This is
> the difference between a forecast and an acharya's reading.

## §0 — Inputs (all prod-verified present, GATE A / D20c)
`kala_convergence` (660, enriched by U3) · `kala_bhavishya` (50 — INHERIT, D37) · `bodha_discoveries`
(1,505) · `bodha_signal_embeddings` (66,738) · `bodha_cgm_nodes/edges/paths` · `bodha_cdlm_cells` (70) ·
`bodha_contradictions` · `bodha_msr_signals` (66,738) · dāśā consensus (U1) · school consensus (U4) ·
the 6 subsystem assets (D11). All read-only.

## §1 — kala_bhavishya inheritance (D37 — correctness, do FIRST)
`kala_bhavishya` is L3's existing 3-yr forward-projection emitter (50 rows; `probability_tier`,
`domain`, `peak_date`, `window_start/end`, `convergence_id`, `signal_id`, `effective_score`,
`falsifiability`, `source_chain`, `narrative`, `outcome_recorded`). ph_nimitta **consumes these as one
anchor source** — inheriting their falsifiability + outcome hooks + the L5 handoff — enriches them with
the axes + elevations, and EXTENDS to lifetime scope. It does NOT ignore or duplicate them. (A
`kala_bhavishya` projection → a `phala_anchors` row with `anchor_source='bhavishya'`, citing the
`kala_bhavishya.id`.) The L5 handoff (`outcome_recorded`) is preserved through ph_pramana (D6).

## §2 — The 8 enrichment axes (D8/D11/D21)
- **Axis 1 — Structural derivation (anti-drift):** per source (convergence window / discovery /
  bhavishya projection), derive domain (CDLM vocabulary) + event_type + direction; cite the real id.
  NEVER hand-write constants.
- **Axis 2 — Calibrated confidence (G-LADDER, D21):** `confidence = min(ladder_ceiling(n_independent,
  has_kala), f(convergence_score))`, `f = max(0.5, convergence_score)`, cap 0.80; labeled
  `structural_not_yet_empirical` (D5). × ayanāṃśa robustness (Axis 7).
- **Axis 3 — Graph-traced causal chain:** the source's CGM node → centrality + the top `bodha_cgm_paths`
  chain (`path_label_human`, `path_length`, `is_final_dispositor`) → `causal_chain_jsonb`. Rank anchors
  by root centrality.
- **Axis 4 — Discovery seeding:** `bodha_discoveries` (1,505) as a source; carry the discovery's
  `falsifier_jsonb` + `why_an_acharya_misses_it` + `surface_depth_delta`; tag `discovery_seeded`.
- **Axis 5 — Embedding precedent:** `bodha_signal_embeddings` cosine → the chart's own nearest PAST
  activations (cross-ref `kala_jivana_parva`, now scored by U2) → "same kind as your 2010 relocation".
- **Axis 6 — Dual consensus:** `dasha_consensus_count` (U1, 1–7) + `school_consensus` (U4: N-of-7 +
  per-school + direction/σ + disagreement-type from D36 E1). Both modulate confidence.
- **Axis 7 — Multi-ayanāṃśa robustness:** × `cross_ayanamsha_consistency_score` (0–5).
- **Axis 8 — Subsystem time-indexing (D11):** medical/vastu/nakshatra/yoga/sade-sati/tajaka signals
  (already bound by ka_yojaka, scored by ka_sangam) surfaced as domain-tagged anchors citing the
  subsystem asset row.

## §3 — The 5 ELEVATIONS (D38 — acharya-grade depth)
- **V1 — Magnitude/severity (distinct from confidence):** `magnitude ∈ {minor, moderate, major,
  pivotal}` from `rarity_years` (rarer config → bigger event) × `effective_score`. A prediction carries
  HOW BIG independently of HOW SURE. (`magnitude` + `magnitude_basis`.)
- **V2 — Probability + date RANGES (not points):** `confidence_low`/`confidence_high` (from MSR
  `salience_confidence_interval_jsonb`) instead of a point; `window_start`/`peak_date`/`window_end` as a
  real range. Honest uncertainty.
- **V3 — Karmic-arc framing:** from the convergence-root graha lordship → `karmic_frame ∈
  {debt_surfacing (Saturn/Ketu), reward_ripening (Jupiter/benefic), desire_entanglement (Rahu),
  effort_reward (Mars/Sun), relational_karma (Venus/Moon)}` + a one-line arc note. What makes it profound.
- **V4 — Actionability + counterfactual:** `malleability ∈ {fated, semi_influenceable, influenceable}`
  + `counterfactual_jsonb` (what transit/remedy raises or lowers the probability). Influenceable anchors
  are flagged for ph_pratikara (mitigation). Makes predictions useful + living.
- **V5 — Carry contradiction in the anchor:** read `bodha_contradictions` for the anchor's signals →
  `contradiction_jsonb` ({contested: bool, countervailing_thread, net_direction}). The anchor records
  "net positive with a countervailing malefic thread", not a flattened single direction.

## §4 — Schema (migration 330 — FIRST L4 migration; also DROPs kala_timeline / CF.L3.2)
`phala_anchors`:
```
anchor_id              uuid PK
chart_id               uuid NOT NULL
anchor_source          text CHECK (anchor_source IN ('convergence','discovery','bhavishya','subsystem'))
convergence_id         bigint REFERENCES kala_convergence(convergence_id)   -- anti-drift FK (nullable per source)
discovery_id           uuid                                                 -- bodha_discoveries id (nullable)
bhavishya_id           bigint REFERENCES kala_bhavishya(id)                 -- inherited projection (nullable) — D37
signal_id              uuid REFERENCES bodha_msr_signals(signal_id)
subsystem_source       text                                                 -- medical|vastu|nakshatra|yoga|sade_sati|tajaka|NULL
event_type             text
direction              text CHECK (direction IN ('elevated','suppressed','mixed'))   -- 'mixed' allowed (V5)
domain                 text CHECK (domain IN ('career','relationship','financial','spiritual','health','transition','psychological'))
horizon_tier           text CHECK (horizon_tier IN ('near','lifetime'))     -- from U2
window_start           date
peak_date              date
window_end             date
magnitude              text CHECK (magnitude IN ('minor','moderate','major','pivotal'))   -- V1
magnitude_basis        text
confidence_low         double precision CHECK (confidence_low  >= 0 AND confidence_low  <= 0.80)   -- V2 range
confidence_high        double precision CHECK (confidence_high >= 0 AND confidence_high <= 0.80)
confidence_basis       text NOT NULL DEFAULT 'structural_not_yet_empirical'  -- D5
karmic_frame           text                                                 -- V3
karmic_note            text
malleability           text CHECK (malleability IN ('fated','semi_influenceable','influenceable'))  -- V4
counterfactual_jsonb   jsonb                                                -- V4 (what raises/lowers)
contradiction_jsonb    jsonb                                                -- V5 (contested/countervailing)
falsifier              text NOT NULL                                        -- specific observable refutation
causal_chain_jsonb     jsonb                                                -- Axis 3
precedent_refs_jsonb   jsonb                                                -- Axis 5
dasha_consensus_count  smallint                                             -- Axis 6 (U1)
school_consensus_jsonb jsonb                                                -- Axis 6 (U4: N-of-7 + per-school + σ + disagreement-type)
ayanamsha_robustness   smallint                                             -- Axis 7
derivation_ledger_jsonb jsonb NOT NULL                                      -- resolves to real ka_*/bo_*/ga_* ids
source_citation        text NOT NULL
computed_at            timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, anchor_source, COALESCE(convergence_id,0), COALESCE(discovery_id,'..'::uuid), COALESCE(bhavishya_id,0), domain)
```

## §5 — Engine spec (`services/ph_nimitta/engine.py`)
1. Gather sources: enriched `kala_convergence` windows + `kala_bhavishya` projections (D37) +
   `bodha_discoveries` + the subsystem signal sets.
2. Per source: Axis 1 derive → Axis 2 confidence-range × Axis 7 robustness → V1 magnitude → Axis 3
   causal chain → Axis 5 precedent → Axis 6 dāśā+school consensus → V3 karmic frame → V4 malleability +
   counterfactual → V5 contradiction → generate the domain-templated falsifier.
3. Anti-drift: every `derivation_ledger_jsonb` resolves to real ids; writer writes ONLY `phala_anchors`;
   never `.commit()/.rollback()`; `WriterResult(asset_id='ph_nimitta', rows_inserted=N)`; delete-then-insert.

## §6 — Acceptance criteria [tagged; prod-verified]
1. `[pytest]` every anchor references a REAL source id (convergence/discovery/bhavishya/subsystem) + a resolving signal_id; zero hand-written constants.
2. `[pytest]` D37: all 50 `kala_bhavishya` projections appear as `anchor_source='bhavishya'` anchors (inherited, not duplicated); their falsifiability/outcome hooks preserved.
3. `[pytest]` Axis 2/V2: confidence is a RANGE (low/high) ≤0.80, labeled structural; G-LADDER floor 0.5 applied.
4. `[pytest]` V1: magnitude is a first-class field, distinct from confidence, derived from rarity_years × effective_score.
5. `[pytest]` Axis 3: causal_chain resolves to real CGM path ids; anchors rank-orderable by root centrality.
6. `[pytest]` Axis 4: ≥1 discovery_seeded anchor carries why_an_acharya_misses_it + surface_depth_delta.
7. `[pytest]` Axis 5/6/7: precedent resolves to real embedding neighbors; dāśā+school consensus populated from the real services (not stubbed); robustness applied.
8. `[pytest]` Axis 8: each of the 6 subsystems yields ≥1 domain-tagged anchor citing its asset row.
9. `[pytest]` V3/V4/V5: karmic_frame from root graha lordship; malleability tag set + influenceable anchors flagged for ph_pratikara; contradiction_jsonb populated from bodha_contradictions ('mixed' direction allowed).
10. `[anti-drift]` zero writes outside phala_anchors; zero .commit()/.rollback(); ledgers resolve.
11. `[HARD SPINE GATE — D26]` ONE anchor proven end-to-end across ALL axes + elevations BEFORE any other L4 asset starts.
12. `[psql_prod + curl_prod]` phala_anchors created; kala_timeline dropped; cockpit shows ph_nimitta lit with real count; idempotent; FORENSIC 7/7.

## §7 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l4-ph-nimitta
# inputs + the existing emitter to inherit
psql "$DATABASE_URL" -c "\d kala_bhavishya"; psql "$DATABASE_URL" -c "SELECT count(*) FROM kala_bhavishya WHERE chart_id=:'NATIVE';"  # 50
psql "$DATABASE_URL" -c "\d kala_convergence"; psql "$DATABASE_URL" -c "SELECT count(*) FROM bodha_discoveries WHERE chart_id=:'NATIVE';"  # 1505
# the frozen-contract writer house-style
sed -n '1,80p' platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py
cd platform/python-sidecar && pytest -q services/ph_nimitta pipeline/orchestrator/writers -k "nimitta or anchor"
```

## §8 — Definition of done
- [ ] Migration 330: phala_anchors created + kala_timeline dropped (CF.L3.2).
- [ ] kala_bhavishya inherited (50 projections → anchors, not duplicated) — D37.
- [ ] 8 axes + 5 elevations all produced + tested; every field traces to real ids.
- [ ] Anti-drift clean; HARD SPINE GATE passed before fan-out; registered/idempotent/FORENSIC-clean; cockpit lit; PR opened.

## §9 — VALUE ADDED BY THIS BRIEF
1. **The asset where "supreme" becomes concrete** — a prediction that is derived, causally explained,
   precedented, consensus-confirmed (dāśā + 7 schools), robustness-weighted, AND carries how-big, a
   probability range, its place in the karmic arc, whether you can influence it, and whether the chart
   is contested about it. No human holds this.
2. **Inherits rather than duplicates** L3's existing forward-projections (D37) — no two-prediction-table trap.
3. **Acharya-grade depth** (D38) — magnitude, ranges, karmic framing, actionability, contradiction —
   the difference between a forecast and a reading; mostly USES already-computed data.
4. **Establishes the L4 spine-first gate** — one anchor proven across all axes before the layer fans out.

---
*End of CLAUDECODE_BRIEF_L4_PH_NIMITTA v1.0. The spine, at maximal capacity. 8 axes + kala_bhavishya
inheritance + 5 acharya-grade elevations. Spine-first hard gate inside.*

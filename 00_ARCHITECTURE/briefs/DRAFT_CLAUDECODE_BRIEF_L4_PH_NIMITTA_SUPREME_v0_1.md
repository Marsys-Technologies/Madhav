---
artifact: DRAFT_CLAUDECODE_BRIEF_L4_PH_NIMITTA_SUPREME_v0_1.md
canonical_id: DRAFT_CLAUDECODE_BRIEF_L4_PH_NIMITTA_SUPREME
brief_for: ph_nimitta (ENRICHED) — Predictive anchors with the full supreme substrate [SPINE]
status: SUPERSEDED (2026-06-22) by CLAUDECODE_BRIEF_L4_PH_NIMITTA_v1_0.md (FINALIZED). Retained-in-place for audit trail only — do NOT build from this draft.
supersedes_for_planning: CLAUDECODE_BRIEF_L4_PH_NIMITTA_v1_0.md (the 6-asset draft)
version: 0.1
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D8, D11, D13, D16, D17, D18)
swarm_coordination:
  wave: P1 (spine-first)
  blocked_by: []   # reads sealed L2/L3; gated only on the enriched-substrate reconciliation
  blocks: [ph_muhurta, ph_pratikara, ph_sankrama, ph_sodhana, ph_phaladesa, ph_pramana]
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py
    - platform/python-sidecar/services/ph_nimitta/**          # engine: derivation + 7 enrichment axes
    - platform/supabase/migrations/330_phala_anchors_and_drop_kala_timeline.sql
    - platform/scripts/seed/asset_registry_seed.ts
  hard_internal_gate: "SPINE-FIRST: prove ONE anchor end-to-end across ALL enrichment axes before P2 fans out."
---

# DRAFT BRIEF — ph_nimitta (ENRICHED) — The Supreme Predictive Spine

> **Draft status.** This captures the FULL planning detail so nothing is lost. Numbers/availability
> tagged `[RECON]` depend on `L4_PHALA_PROD_RECONCILIATION_v1_0.md`. Finalize after it returns.

## §0 — What this asset IS (enriched)
`ph_nimitta` derives **phase-locked, falsifiable predictive anchors** from `ka_sangam`'s real
convergence windows — AND enriches each anchor with **seven supreme axes** that no acharya can hold
simultaneously. Each anchor = (a real `kala_convergence` window) → (event prediction + direction +
domain + explicit falsifier + a confidence DERIVED from real scores) **+ a causal chain + precedent
+ consensus + robustness**. It is the spine: every downstream ph_* inherits its pattern.

## §1 — The seven enrichment axes (the supreme substrate, per DECISIONS D8/D11/D17/D18)

### Axis 1 — Structural derivation (the base, anti-drift)
For each `kala_convergence` row (660 windows `[RECON Q4]`): map `constituent_factors`/`signal_id` → a
domain (via the CDLM vocabulary) + an `event_type` + `direction`. Cite the real `convergence_id` +
`signal_id`. NEVER hand-write constants (D15/anti-drift).

### Axis 2 — Calibrated confidence (G-LADDER, D13) `[NATIVE-RATIFY]`
`confidence = min( ladder_ceiling(independent_current_count, has_kala_window), f(convergence_score) )`,
hard-capped 0.80. Ladder ceilings (harvested from legacy): 1 current ≤0.55, 2 ≤0.65, 3 ≤0.72,
3+kala ≤0.78, ≥4+kala ≤0.80. **The exact `f(convergence_score)` mapping HALTS for native sign-off.**
Confidence is labeled **`structural_not_yet_empirical`** (D5 — no empirical calibration in L4).

### Axis 3 — Graph-traced causal chain (D8 §2.2)
For the window's `signal_id`, fetch its `bodha_cgm_nodes` node → its centrality (pagerank,
betweenness, eigenvector) → the top `bodha_cgm_paths` chain (`path_node_ids_array`, `path_length`,
`is_final_dispositor`) to a final dispositor. Store as `causal_chain_jsonb`. **Rank anchors by the
graph centrality of their root cause** (high-betweenness root = structurally load-bearing prediction).
This is the "WHY, through the chart's own wiring" an acharya gestures at but can't hold across 140 nodes.

### Axis 4 — Discovery seeding (D8 §2.4)
Accept `bodha_discoveries` (1,411 rows `[RECON Q4]`) as a SECOND anchor source, tagged
`discovery_seeded`. A discovery's `constituent_refs_jsonb` → its signals → `ka_kalasutra`/`ka_sangam`
activation windows → a time-anchored prediction. These carry the discovery's `falsifier_jsonb` +
`why_an_acharya_misses_it` — the most differentiated predictions in the instrument.

### Axis 5 — Embedding precedent (D8 §2.5)
For the anchor's signal, query `bodha_signal_embeddings` (768-dim, HNSW, cosine) for the chart's own
semantically-nearest PAST activations (cross-ref `kala_jivana_parva` life-arc) → "this is the same
*kind* as your 2010 relocation." Store `precedent_refs_jsonb`. Grounds the prediction in lived precedent.

### Axis 6 — Dual consensus: dāśā + school (D11/D16/D17/D18)
- **Dāśā consensus:** via `ka_dasha_kala` cross-system agreement — `dasha_consensus_count` = how many
  of the 7 dāśā systems `[RECON Q1]` activate this window's domain. Higher = categorically more reliable.
- **School consensus:** via the activated M9 multi-school engine `[RECON Q3/D18]` —
  `school_consensus` = N-of-7 schools (Parāśarī/Jaimini/Tājika/KP/Nāḍī/BNN/Yoginī) concurring on the
  domain. Both are top-tier confidence multipliers no acharya computes at this breadth.

### Axis 7 — Multi-ayanāṃśa robustness (D8 §2.7)
Multiply confidence by `cross_ayanamsha_consistency_score` (0–5) from `bodha_msr_signals` — a
prediction holding across all 5 ayanāṃśas is far more robust than one appearing in 1. A rigor axis no
human re-derives. Store `ayanamsha_robustness`. Folds into the G-LADDER transform (Axis 2).

### Axis 8 (per D11) — Subsystem time-indexing
Beyond the structural spine, EVERY parallel subsystem's signals are included in the anchor stream as
domain-tagged predictions: medical (`ga_medical` → "vulnerability activates window X"), vastu
(`ga_vastu_planet_direction_map`), nakshatra (`chart_facts`), yoga (`ga_yoga_firings`), sade-sati
(`chart_facts`, 11,019 rows), tājaka (`l1_tajik_varsha_year_lords`). **Mechanism:** these subsystems
already emit into `bodha_msr_signals`; `ka_yojaka` binds them to activation predicates; `ka_sangam`
scores them. The work is ensuring subsystem signals ARE in the binding and surfaced with their domain
tag — NOT recomputing them (D10 reuse rule: READ-asset). Each subsystem anchor carries its
subsystem_source + the subsystem asset's row id.

## §2 — Schema (migration 330 — the FIRST L4 migration; also DROPs kala_timeline / CF.L3.2)
`phala_anchors`:
```
anchor_id              uuid PK
chart_id               uuid NOT NULL
convergence_id         uuid REFERENCES kala_convergence   -- anti-drift FK (NULL if discovery_seeded)
discovery_id           uuid REFERENCES bodha_discoveries  -- anti-drift FK (NULL if convergence_seeded)
signal_id              uuid                                -- the resolving L2 signal
anchor_source          text CHECK (anchor_source IN ('convergence','discovery','subsystem'))
subsystem_source       text                                -- medical|vastu|nakshatra|yoga|sade_sati|tajaka|NULL
event_type             text
direction              text CHECK (direction IN ('elevated','suppressed'))
domain                 text CHECK (domain IN ('career','relationship','financial','spiritual','health','transition'))
window_start           date
window_end             date
peak_date              date
falsifier              text NOT NULL                        -- specific observable refutation
confidence             double precision CHECK (confidence >= 0 AND confidence <= 0.80)
confidence_basis       text NOT NULL DEFAULT 'structural_not_yet_empirical'   -- D5 honesty label
causal_chain_jsonb     jsonb                                -- Axis 3
precedent_refs_jsonb   jsonb                                -- Axis 5
dasha_consensus_count  smallint                             -- Axis 6
school_consensus_jsonb jsonb                                -- Axis 6 (N-of-7 + per-school)
ayanamsha_robustness   smallint                             -- Axis 7 (0-5)
derivation_ledger_jsonb jsonb NOT NULL                      -- resolves to real ka_*/bo_*/ga_* ids
source_citation        text NOT NULL
computed_at            timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, COALESCE(convergence_id, discovery_id), domain, anchor_source)
```

## §3 — Engine spec (`services/ph_nimitta/engine.py`)
1. Load `kala_convergence` windows + `bodha_discoveries` + the subsystem signal sets.
2. Per root: derive domain/event_type/direction (Axis 1); compute G-LADDER confidence (Axis 2) ×
   ayanāṃśa robustness (Axis 7); walk the CGM for the causal chain (Axis 3); query embeddings for
   precedent (Axis 5); fetch dāśā + school consensus (Axis 6); generate the domain-templated falsifier.
3. Subsystem anchors (Axis 8): for each subsystem signal bound by `ka_yojaka`, emit a domain-tagged
   anchor citing the subsystem asset row.
4. Anti-drift: every `derivation_ledger_jsonb` resolves to real ids; writer writes ONLY `phala_anchors`.

## §4 — Acceptance criteria [tagged; prod-verified]
1. `[pytest]` every anchor references a REAL `convergence_id` OR `discovery_id` (FK resolves) + a resolving `signal_id`; zero hand-written constants.
2. `[pytest]` confidence = deterministic G-LADDER transform × ayanāṃśa robustness; ≤0.80; labeled `structural_not_yet_empirical`.
3. `[pytest]` each anchor has a non-empty specific falsifier.
4. `[pytest]` Axis 3: causal_chain_jsonb resolves to real CGM node+path ids; anchors rank-orderable by root centrality.
5. `[pytest]` Axis 4: ≥1 `discovery_seeded` anchor produced; carries the discovery's falsifier.
6. `[pytest]` Axis 5: precedent_refs resolve to real embedding neighbors + a `kala_jivana_parva` parva.
7. `[pytest]` Axis 6: dasha_consensus_count + school_consensus populated from real services (not stubbed) `[RECON]`.
8. `[pytest]` Axis 8: each of the 6 subsystems produces ≥1 domain-tagged anchor citing its asset row.
9. `[anti-drift]` zero writes outside phala_anchors; zero `.commit()/.rollback()`; ledgers resolve.
10. `[NATIVE-RATIFY]` G-LADDER `f(convergence_score)` mapping HALTs for sign-off.
11. `[HARD GATE]` single-anchor end-to-end-across-all-axes spine passes BEFORE P2.
12. `[psql_prod + curl_prod]` phala_anchors created; kala_timeline dropped; cockpit shows ph_nimitta lit; idempotent; FORENSIC 7/7.

## §5 — VALUE ADDED
The single asset where "supreme" becomes concrete: a prediction that is derived (not asserted),
causally explained (graph-traced), precedented (embedding), consensus-confirmed (dāśā + school),
robustness-weighted (ayanāṃśa), falsifiable (explicit refuter), AND draws on every parallel subsystem
— holding correlation depth (333,690 signals, measured-betweenness graph, 4+-hop chains) no human can.

## §6 — RECON dependencies (finalize these after reconciliation)
- `[RECON Q1]` dāśā-consensus availability (all 7 systems prod-populated?).
- `[RECON Q3/D18]` school-consensus availability (M9 persisted + chart-general?).
- `[RECON Q4]` exact row counts for convergence/discoveries/embeddings.

---
*End of DRAFT ph_nimitta SUPREME v0.1. Eight enrichment axes captured in full. Finalize post-reconciliation.*

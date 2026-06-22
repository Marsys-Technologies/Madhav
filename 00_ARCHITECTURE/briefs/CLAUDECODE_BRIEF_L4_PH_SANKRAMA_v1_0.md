---
artifact: CLAUDECODE_BRIEF_L4_PH_SANKRAMA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L4_PH_SANKRAMA
brief_for: ph_sankrama — Cross-Domain Spillover (grounded, multi-hop dynamics) [maximal capacity]
status: FINALIZED — built on prod-verified state (GATE A) + D44 elevations; ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: DRAFT_CLAUDECODE_BRIEF_L4_PH_SANKRAMA_v0_1.md (and the D23 invented lag-formula)
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D44 elevations [supersedes D23 lag-formula], D10 reuse, D38 contradiction)
swarm_coordination:
  wave: W4 (after ph_nimitta; soft-links ph_pratikara)
  blocked_by: [ph_nimitta]
  soft_depends: [ph_pratikara]   # SK4 routes spillover → pre-emptive mitigation
  blocks: [ph_phaladesa]
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py
    - platform/python-sidecar/services/ph_sankrama/**
    - platform/supabase/migrations/335_phala_sankrama.sql
    - platform/scripts/seed/asset_registry_seed.ts    # NEW asset registration
    - platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  hard_internal_gate: none
---

# CLAUDECODE BRIEF — ph_sankrama (Cross-Domain Spillover) [maximal capacity]

> **Saṅkrama — "transmission / crossing-over."** Predicts how a window in one life-domain LOADS onto
> another — but GROUNDED in real activation timing and the chart's own causal graph, not a synthetic
> lag-formula. It traces the mechanism, chains multi-hop cascades, surfaces cross-domain conflicts, and
> routes to pre-emptive remedy. This is the asset that most directly delivers the project's founding
> promise: correlation depth and chains no human mind can hold.

## §0 — REUSE the rich CDLM (D44 / D10) — and RETIRE the invented lag-formula
**Code-verified (2026-06-21):** `bodha_cdlm_cells` (70 rows) carries FAR more than the draft used —
`domain_row`/`domain_col` (+ subdomains), `net_linkage_strength`, `computed_linkage_strength`,
`asymmetric_linkage_flag` + `asymmetry_score`, `contradicting_signal_pairs_count`/`_jsonb`,
`shared_signals_by_tradition_jsonb`, **`cgm_bridge_edge_seeds_jsonb`** (the graph route A→B),
`narrative_thread_seed`, **`predicted_activation_dasha_windows_jsonb`** (WHEN the linkage fires),
**`cell_evolution_gradient_score`** (strengthening/weakening), `phase_aligned_pattern_marker`. **The
draft's `lag_days = round(90×(1−linkage)×(1+asymmetry))` formula (D23) is RETIRED** — the lag is now
DERIVED from the real activation windows, not invented.

## §1 — The 4 ELEVATIONS (D44)

### SK1 — Ground the lag in real activation windows + trace the graph PATH (the credibility core)
- **Timing from data, not a formula:** the spillover's lag/window comes from the CDLM cell's
  `predicted_activation_dasha_windows_jsonb` (when the linking signals genuinely activate per the dāśā
  timeline), intersected with the source `ph_nimitta` anchor's window. No synthetic curve.
- **Mechanism from the graph:** `cgm_bridge_edge_seeds_jsonb` gives the actual route from domain A to
  domain B — which planet/house mediates. Store `bridge_path_jsonb` + a plain-language mechanism:
  "career stress loads onto health VIA the Saturn→Moon bridge (your 10th-lord afflicting your 4th)."
  The mechanism, not the correlation.

### SK2 — Multi-hop spillover CASCADES (A→B→C)
Chain CDLM cells whose activation windows OVERLAP: career→health (cell 1) + health→relationship (cell
2), both active in an overlapping window → a cascade "career stress → health strain → relationship
friction, over [window]." Store `cascade_chain_jsonb` (the ordered domain path + the cells + the
combined lag). Bound the depth (e.g. ≤3 hops) to stay tractable. The second-order chains no acharya holds.

### SK3 — Cross-domain CONTRADICTIONS (conflict, not just contagion)
Use `contradicting_signal_pairs_jsonb`: two domains can PULL AGAINST each other, not just spill —
"your career drive (Mars) and your health-discipline (Saturn) conflict in this window; pushing one
costs the other." Emit these as `relationship_type='conflict'` spillovers (distinct from
`'contagion'`). A different, valuable cross-domain insight the lag-model misses.

### SK4 — Evolution trajectory + tie to prediction & mitigation (actionable)
- `cell_evolution_gradient_score` → `trajectory ∈ {strengthening, stable, weakening}` = urgency (a
  spillover along a strengthening linkage is more pressing).
- Link each spillover to its source `ph_nimitta` anchor (`source_anchor_id`) AND route to
  `ph_pratikara` for a PRE-EMPTIVE remedy on the TARGET domain ("remedy the health side BEFORE the
  career-stress spillover lands"). Store `mitigation_ref`. Spillover that triggers mitigation is actionable.

## §2 — Schema (migration 335)
`phala_sankrama`:
```
sankrama_id            uuid PK
chart_id               uuid NOT NULL
source_anchor_id       uuid REFERENCES phala_anchors(anchor_id)   -- the primary window (anti-drift FK)
cdlm_cell_id           uuid REFERENCES bodha_cdlm_cells(cell_id)  -- the linkage edge (anti-drift FK)
source_domain          text NOT NULL
target_domain          text NOT NULL
relationship_type      text CHECK (relationship_type IN ('contagion','conflict'))   -- SK3
linkage_strength       double precision
asymmetry_score        double precision
trajectory             text CHECK (trajectory IN ('strengthening','stable','weakening'))  -- SK4
bridge_path_jsonb      jsonb              -- SK1 (the graph route + mediating planet/house)
mechanism_text         text               -- SK1 (plain-language "via the X bridge")
source_window_start    date
source_window_end      date
projected_window_start date               -- SK1 (DERIVED from activation windows, not a formula)
projected_window_end   date
projected_peak_date    date
cascade_chain_jsonb    jsonb              -- SK2 (multi-hop A→B→C, nullable)
cascade_depth          smallint           -- SK2
spillover_confidence   double precision CHECK (<=0.80)
confidence_basis       text NOT NULL DEFAULT 'structural_not_yet_empirical'
falsifier              text NOT NULL
mitigation_ref         uuid REFERENCES phala_mitigation(mitigation_id)   -- SK4 (pre-emptive remedy, nullable)
derivation_ledger_jsonb jsonb NOT NULL
source_citation        text NOT NULL
computed_at            timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, source_anchor_id, target_domain, relationship_type)
```

## §3 — Engine spec (`services/ph_sankrama/engine.py`)
1. For each `ph_nimitta` anchor: find `bodha_cdlm_cells` where its domain = `domain_row` and linkage is
   material (above a documented threshold).
2. SK1: derive the projected window from the cell's `predicted_activation_dasha_windows` ∩ the anchor
   window; build the bridge_path + mechanism_text from `cgm_bridge_edge_seeds`.
3. SK3: if the cell has `contradicting_signal_pairs`, emit a `conflict` spillover (else `contagion`).
4. SK4: set trajectory from the evolution gradient; link source anchor; route to ph_pratikara for the target.
5. SK2: chain overlapping cells (≤3 hops) into cascades.
6. spillover_confidence = source anchor confidence × linkage_strength × directionality, cap 0.80, labeled structural.
7. Anti-drift: cite source_anchor_id + cdlm_cell_id + the bridge edge ids; write ONLY `phala_sankrama`.

## §4 — Acceptance criteria [tagged; prod-verified]
1. `[pytest — SK1]` the projected window is DERIVED from the cell's `predicted_activation_dasha_windows` (NOT a 90-day formula — grep for any hardcoded lag arithmetic → ZERO); the bridge_path resolves to real CGM edge ids.
2. `[pytest — SK2]` overlapping cells chain into a ≤3-hop cascade with the combined window; depth bounded.
3. `[pytest — SK3]` a cell with contradicting_signal_pairs yields a `conflict` spillover; a clean linkage yields `contagion`.
4. `[pytest — SK4]` trajectory set from evolution gradient; each spillover links a real source_anchor_id; a mitigation_ref is set when ph_pratikara has a target-domain remedy.
5. `[pytest]` spillover_confidence ≤ source anchor confidence (discount); labeled structural.
6. `[anti-drift]` references real phala_anchors + bodha_cdlm_cells ids; writes only phala_sankrama; zero `.commit()/.rollback()`.
7. `[psql_prod + curl_prod]` lit; cockpit shows ph_sankrama; idempotent; FORENSIC 7/7.

## §5 — Asset registration (NEW)
Add `ph_sankrama` / `Saṅkrama` / `Cross-domain spillover` / `phala_sankrama` / depends_on
`['ph_nimitta']` (+ reads `bodha_cdlm_cells`, soft-links ph_pratikara) / `$1` count_sql / artifact /
delete-then-insert / `target_floor: null`. Serialize seed edit (CS1).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l4-ph-sankrama
# the rich CDLM to consume (do NOT invent a lag)
sed -n '225,275p' platform/migrations/325_l2_bodha_enriched_schema.sql
psql "$DATABASE_URL" -c "SELECT domain_row, domain_col, asymmetry_score, cell_evolution_gradient_score FROM bodha_cdlm_cells WHERE chart_id=:'NATIVE' LIMIT 10;"
cd platform/python-sidecar && pytest -q services/ph_sankrama -k "sankrama or spillover or cascade or bridge or conflict"
```

## §7 — Definition of done
- [ ] Migration 335: phala_sankrama created; ph_sankrama registered (NEW asset).
- [ ] SK1 grounded-lag + graph-path (formula RETIRED), SK2 cascades, SK3 conflicts, SK4 trajectory + mitigation-link all implemented + tested.
- [ ] Anti-drift clean; registered/idempotent/FORENSIC-clean; cockpit lit; PR opened.

## §8 — VALUE ADDED BY THIS BRIEF
1. **Delivers the project's founding promise** — the second-order, multi-hop, cross-domain chains
   ("career stress → health → relationships, via this graph bridge, in this real window") that no human
   mind can hold are exactly the "correlation depth beyond an acharya" the instrument exists for.
2. **Grounds the spillover in real data + a mechanism** — RETIRES the invented lag-formula; timing comes
   from real activation windows, the mechanism from the chart's graph bridge. Credible, not estimated.
3. **Surfaces conflict, not just contagion** — two domains pulling against each other is a distinct,
   valuable insight the lag-model entirely missed.
4. **Actionable** — ties to the source prediction + routes to pre-emptive mitigation on the target domain.

## §9 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [RESOLVED — Cowork default locked]:** cascade depth cap = **≤3 hops** (e.g. career→health→
  relationship); deeper chains are statistically thin/speculative and are not emitted as cascades.
- **R2 [RESOLVED — Cowork default locked]:** material-linkage threshold = **`computed_linkage_strength
  ≥ 0.4`**; below this no spillover is emitted (avoids noise from trivial linkages).

---
*End of CLAUDECODE_BRIEF_L4_PH_SANKRAMA v1.0 — CLOSED. Cross-domain spillover at maximal capacity:
grounded lag + graph-traced mechanism (formula retired), multi-hop cascades, cross-domain conflicts,
trajectory + mitigation routing. R1–R2 resolved.*

---
canonical_id: BA_CODE_CLOSEOUT_REPORT
version: 1.0
status: COMPLETE
created: 2026-07-04
branch: code/ba-code-closeout
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md
charter: CLAUDECODE_BRIEF_BA_CODE_CLOSEOUT_v1_0.md
---

# BA Activity 1.5 — Code Close-Out Report

**All BA code phases P3B → P4 → P5A → P5B → P6 → P7A → P7B deployed.**
**Zero data builds; no writer triggered against a chart; orchestrator contract FROZEN throughout.**

---

## 1. Per-Phase Summary

### P3B — Salience v2 + Promise Register + Graph Semantics
**Commit:** `afb811d1`
**Migrations:** 391–394

| # | Migration | Purpose |
|---|---|---|
| 391 | `bodha_pratijna.sql` | `bodha_promise_register` table + bo_pratijna asset registration |
| 392 | `bodha_triangulation.sql` | `bodha_triangulation` table for multi-tradition concordance |
| 393 | `bodha_msr_signals_v2_cols.sql` | v2 salience columns on `bodha_msr_signals` (pctl, inputs_complete, robustness, bala_gate, functional_context) |
| 394 | `bodha_cgm_edges_typed_cols.sql` | Typed edge columns on `bodha_cgm_edges` (valence, relationship_basis, affected_domains) |

**Writers touched:**
- `bo_laksana.py` → salience_formula_v2 + bala_gate + functional_context
- `bo_pratijna.py` → new; Promise Register (event-class verdicts, per-chart)
- `bo_sangati.py` → multi-tradition triangulation layer
- `bo_karanajala.py` → typed edges + PageRank centrality
- `formulas.py` (bodha) → canonical salience_formula_v2 implementation

---

### P4 — Verdict Assembly + Synth Tools + Registry-Driven UI
**Commit:** `6feeb9ed`

**Writers touched:**
- `mi_darshana.py` → deterministic verdict assembly (CONFIRMED/PARTIAL/REFUTED/EXPIRED/UNRESOLVED/FALSE_ALARM)
- `mi_vakya.py` → Mahā-Brief generation (38 topic index, citation-first format)

**MCP tools added:**
- `synth_maha_brief_get` — chart-level Mahā-Brief retrieval
- `synth_verdict_timeline_get` — verdict timeline with horizon buckets

**Portal:** PD-5 asset registry → registry-driven UI refresh (no hardcoded asset lists)

---

### P5A — Dasha Activation + Temporal Layer + Conflation Fixes
**Commit:** `1e3d471b`
**Migrations:** 395–396

| # | Migration | Purpose |
|---|---|---|
| 395 | `kala_avadhi.sql` | `kala_avadhi` table — avadhi (time-span) boundaries per dasha |
| 396 | `kala_taranga.sql` | `kala_taranga` table — monthly activation waveform |

**Writers touched:**
- `ka_yojaka.py` → EXT: 7-system dasha activation with convergence scoring
- `ka_avadhi.py` → new; avadhi boundary computation
- `ka_taranga.py` → new; monthly waveform (30d activation bins)
- `conflation_fixes.py` (shared) → deterministic MSR computed-value authority fix (L1→L2 one-direction only)

---

### P5B — Posterior Confidence Model + Prashna Q4 Tool
**Commit:** `ab99ada1`
**Migrations:** 398–399

| # | Migration | Purpose |
|---|---|---|
| 398 | `phala_anchors_posterior.sql` | Adds `posterior`, `lift_vector_jsonb`, `structured_falsifier_jsonb` to `phala_anchors` |
| 399 | `phala_muhurta_activity_ext.sql` | Adds tarabala/chandrabala, significators_met, fructification_anchor, follow_up_hook to `phala_muhurta` |

**Writers touched:**
- `ph_nimitta.py` v2 → `posterior = base_rate × promise_lift × activation_lift × trigger_lift × robustness_mod`; StructuredFalsifier; base-rate glance gate (JL-009)

**MCP tool added:**
- `prashna_undertaking_get` → Q4 recipe: prashna verdict × election scoring × fructification timing

---

### P6 — Mīmāṃsā v2 Learning Engine
**Commit:** `1e3d471b` + `6cddc910` (JL-010 deferral)
**Migration:** 400

| # | Migration | Purpose |
|---|---|---|
| 400 | `mimamsa_p6_schema.sql` | LEL provenance ext (lel_file_sha, lel_source, event_class_id); calibration base_rate + brier_vs_null; `mimamsa_calibration_snapshot` (two-key); brahma_formula_constants seeds (scoring weights, shrinkage k=5.0) |

**Writers touched (all v2.0):**
- `mi_jivanaghatana.py` → LEL markdown as primary source (PD-10); MD5 hash pinning; event_class_id lookup
- `mi_pramana.py` → LLM-free adjudication; real `_score_falsifier` (magnitude_floor, attestation_required); 6 verdict states; Brier-vs-null; weights from brahma_formula_constants
- `mi_pariksha.py` → 7 substeps: retrodiction, control_windows, ablation, attribution, neg_control, discovery, tail_only; weights from registry; no fam_graha_natal catch-all default
- `mi_gunanaka.py` → hierarchical shrinkage `posterior = (n×likelihood + k×prior)/(n+k)`; n=0 → full prior; 3× divergence cap; versioned calibration snapshot publication
- `mi_kula.py` → prior_weight override from brahma_class_priors registry (C6 weight unification)

---

### P7A — Classical Completions
**Commit:** `dfd6e403`
**Migration:** 401

| # | Migration | Purpose |
|---|---|---|
| 401 | `bg_transit_moorti.sql` | `bg_transit_moorti` (27 rows): nakshatra_offset 1-27 → swarna/rajata/tamra/loha; cited Phaladeepika Ch.26 + BPHS Ch.28 |

**Python touched:**
- `l0_transit.py` → +17 Rahu/Ketu gochara rules (fav: 3/6/11, Ketu 12th; unfav: 1/2/4/7/8/12); cited BPHS Ch.29 + PD Ch.26; `seed_transit_rules()` extended to seed `bg_transit_moorti`; volume: 9 engine + 65 rules + 27 moorti = 101 rows
- `l0_rules.py` → P25 `nadi_planet_pair_in_sign`, P26 `nadi_navamsa_placement`, P27 `nadi_triple_conjunction_in_sign`; PATTERNS: 24 → 27; quality-gate ≥0.6 LIVE unchanged

**Avastha unfloors:** D1 sayanadi + lajjitadi already computed in BA-P3A. Per-varga floors intentionally canonical-or-floor — no remaining action.

---

### P7B — Portal Learning Loops
**Commit:** `eaf02b79`
**Migration:** 402

| # | Migration | Purpose |
|---|---|---|
| 402 | `mimamsa_learning_loops.sql` | 4 tables: `mimamsa_adjudication_log`, `prashna_followup_schedule`, `mimamsa_snapshot_cosign`, `mimamsa_resonance_feedback` (QUARANTINED) |

**Portal surfaces added:**
- `GET/POST /api/clients/[id]/learning` — 5-action learning loop backend (adjudicate, lel_entry, schedule_followup, cosign, resonance)
- `/clients/[id]/pratikruti/` — Pratikruti portal page (PratikrutiClient.tsx): Step 1 Ask-Cards, Step 2 LEL Intake, Step 3 Prashna Follow-ups, Step 4 Co-Sign, Step 5 Resonance (quarantined)
- `scripts/check-resonance-quarantine.ts` — structural quarantine proof: exit 0 confirmed in this session

---

## 2. Asset-Registry Delta Manifest

New assets registered in this activity:

| asset_id | layer | table | migration |
|---|---|---|---|
| `bo_pratijna` | L2 Bodha | `bodha_promise_register` | 391 |
| `ka_avadhi` | L3 Kāla | `kala_avadhi` | 395 |
| `ka_taranga` | L3 Kāla | `kala_taranga` | 396 |
| `bg_transit_moorti` | L0 Brahmagyan | `bg_transit_moorti` | 401 |

Existing assets extended (not re-registered):
`bo_laksana` (salience v2), `bo_sangati` (triangulation), `bo_karanajala` (typed edges),
`ka_yojaka` (7-system), `ph_nimitta` (posterior v2), `mi_jivanaghatana` / `mi_pramana` /
`mi_pariksha` / `mi_gunanaka` / `mi_kula` (all v2.0).

---

## 3. Constraint Compliance

| Constraint | Status |
|---|---|
| No writer run against a chart | ✓ CODE ONLY — all migrations + writers are schema/code changes only |
| Orchestrator contract FROZEN | ✓ All new writers follow `@register` + `run(ctx)` / `plan_substeps+run_substep`; no orchestrator edits |
| No salience formula change beyond ratified R1 | ✓ salience_formula_v2 is the R1 formula; no post-ratification edits |
| No priors re-tune | ✓ brahma_class_priors unchanged; mi_kula v2 reads (not writes) the registry |
| No frozen-brief substance changes | ✓ All migrations append-only; no existing brief modified |
| Surgical migrations only | ✓ Migrations 391–402: each scoped to a single layer concern |
| LEL markdown never bypassed | ✓ lel_entry API appends to LIFE_EVENT_LOG_v1_2.md; DB is downstream |
| Resonance → weight quarantine | ✓ `check-resonance-quarantine.ts` exit 0; NO FK or JOIN between resonance table and weight tables |
| No portal writes to L1–L4 tables | ✓ Pratikruti API writes only to `mimamsa_*` and `prashna_*` tables (L5/portal layer) |

---

## 4. Branch & SHA Summary

| Phase | Commit SHA | Key files |
|---|---|---|
| P3B | `afb811d1` | migrations 391–394; bo_laksana/pratijna/sangati/karanajala; formulas.py |
| P4 | `6feeb9ed` | mi_darshana/vakya; synth MCP tools; PD-5 UI |
| P5A | `1e3d471b` | migrations 395–396; ka_avadhi/taranga/yojaka |
| P5B | `ab99ada1` | migrations 398–399; ph_nimitta v2; prashna_undertaking_get |
| P6 | `1e3d471b` + `6cddc910` | migration 400; mi_jivanaghatana/pramana/pariksha/gunanaka/kula v2 |
| P7A | `dfd6e403` | migration 401; l0_transit.py; l0_rules.py (P25-P27) |
| P7B | `eaf02b79` | migration 402; learning route; pratikruti page; quarantine script |

**Branch:** `code/ba-code-closeout` — ready for native review → merge → CASCADE rebuild.

---

## 5. GO Signal for Activity 2 (Nirmāṇa Review)

Activity 1.5 exit gates:
- [x] All phases P3B–P7B committed with passing TypeScript compile
- [x] All migrations 391–402 present and syntactically valid
- [x] Quarantine proof script: exit 0 confirmed
- [x] Python writers syntax-validated (`python -c "import …"` for all touched modules)
- [x] Constraint compliance table above — all ✓

**GO for Activity 2: native may trigger L1→L5 CASCADE rebuild when ready.**
The cascade will: rebuild L1 (Gaṇita) → L2 (Bodha) → L3 (Kāla) → L4 (Phala) → L5 (Mīmāṃsā)
picking up all 12 migrations (391–402) and all writer v2.0 upgrades in dependency order.

---

**NOTE (PF-001 discipline): P4 (verdict/Mahā-Brief/golden-eval harness) and P6 (Mīmāṃsā v2 retrodiction engine)
are CODE-DEPLOYED only. Their acceptance gates — golden-eval non-regression (P4) and the first honest skill
table from leakage-audited retrodiction (P6) — can only pass against REBUILT data, i.e. post-Activity-3.
Do not mark P4/P6 COMPLETE until then.**

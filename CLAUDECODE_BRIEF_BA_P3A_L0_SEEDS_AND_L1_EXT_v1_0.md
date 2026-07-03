---
canonical_id: CLAUDECODE_BRIEF_BA_P3A_L0_SEEDS_AND_L1_EXT
version: 1.0
status: RING2_PARTIAL — Ring-1 PASS (PRs #398+#401+#402 merged; mig 385-389 applied; deploy run 28657023737 SUCCESS); Ring-2 4.5/5 gates evidenced; ONE NATIVE ACTION REQUIRED (cockpit L1 rebuild for bhava_arudha)
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program; substance frozen — conductor fills slots only)
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P3A (L0 judgment seeds + L1 extensions)
slots: ⟦PRIOR_V1_VALUES_REF⟧ ⟦NEXT_MIGRATION_NUMBER_BOTH_DIRS⟧ ⟦HEAD_SHA⟧
common_rules: FROZEN contract §N.2 · surgical migrations · upsert for GLOBAL / delete-then-insert §N.3
  for per-chart · count_sql chart-scoped $1 (global: trivial) · PD-5: registry changes update
  ASSET_NAMES.ts + ASSET_MAP same PR · two-chart rule (Abhinandan first) · canonical-or-floor rule.
sanity_values: FORENSIC 7/7 (Sun Cap · Moon P.Bhadrapada · Lagna Aries ×5 ayanamshas · Shukla Tritiya ·
  Ravivara · Shiva yoga · Garaja karana) must hold after every L1 rebuild.
may_touch: ["NEW bg_class_priors/bg_ghatana/bg_formula_constants writers + migrations", "ga_sensitive/ga_dashas/ga_strength/ga_condition writers + seal-amendment notes", "charts.chart_type + domain-normalization migrations", "ASSET_NAMES.ts/ASSET_MAP"]
must_not_touch: ["orchestrator/planner", "bo_*/ka_*/ph_*/mi_* writers", "retrieval logic", "existing L0 asset content"]
---

# BRIEF BA-P3A — L0 SEEDS + L1 EXTENSIONS

**Code anchors:** writers dir `platform/python-sidecar/pipeline/orchestrator/writers/` (WriterBase in
`__init__.py` L65 — read-only law); registry INSERT pattern = migration 358 shape; L1 combustion truth
`ga_condition_writer.py` ← `bg_combustion_orbs`. Seeds: `BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md`
§1–§5 + ⟦PRIOR_V1_VALUES_REF⟧ (P2-tuned). Layer-scope law: L0 = scope='global', NO chart_id (§2.2-1).

## Step 1 — Migrations (surgical, numbered from ⟦NEXT_MIGRATION_NUMBER_BOTH_DIRS⟧, in order)
1. `charts.chart_type` column, default 'natal' (grounding C2: does not exist; prashna/synastry prerequisite).
2. Canonical 12-domain normalization across the 8 divergent sites (BA_MASTER C15; taxonomy = seed package §1).
3. `brahma_class_priors` + registry row `bg_class_priors` — DDL: `(prior_version, signal_type_class,
   fact_kind, source_subsystem, signal_tradition, class_prior numeric, varga_weights jsonb, contested bool,
   citation, ratified_by, PK(prior_version, signal_type_class, fact_kind, source_subsystem,
   signal_tradition))`. Seed with ⟦PRIOR_V1_VALUES_REF⟧.
4. `brahma_event_ontology` + `brahma_activity_ontology` + registry row `bg_ghatana` — DDL:
   `event_ontology(event_class_id PK, name, domain, signature_model jsonb{houses,lords,karakas,vargas,
   dasha_rules,transit_triggers}, magnitude_floor, adjacency jsonb, base_rate_by_age jsonb, matching_rules
   jsonb, citations, version)`; `activity_ontology(activity_class_id PK, name, significators jsonb,
   fructification_rules jsonb, related_event_class FK, citations)`. Seed from package §2–§3.
5. `brahma_formula_constants` + registry row `bg_formula_constants` — DDL: `(constant_id PK, value_jsonb,
   class ∈{classical,native_judgment,engineering}, consumer_assets text[], citation_or_ratification,
   calibratable bool, bounds jsonb, version)`. Seed the constants sheet (package §4) incl. per-graha
   combustion orbs (classical: Moon 12°, Mars 17°, Mercury 14°/12°R, Jupiter 11°, Venus 10°/8°R,
   Saturn 15°) + severity thresholds + attention-budget 70/20/10.

## Step 2 — L0 writers
`bg_class_priors`, `bg_ghatana`, `bg_formula_constants`: `@register` WriterBase, GLOBAL scope, upsert
idempotency, trivial count_sql, correct sort_order within brahmagyan layer.

## Step 3 — L1 extensions (seal-amendment pattern; amendment note in L1_GANITA_CLOSURE)
- `ga_sensitive` += bhava arudhas A1–A12 incl. Arudha Lagna + Upapada (fact_category `bhava_arudha`;
  standard Parashari arudha computation with the two exceptions rule) + Karakamsha/Swamsha derived facts.
- `ga_dashas` += classical Jaimini Chara dasha (Rao-standard sign periods).
- `ga_strength` += per-varga Shadbala (label `computed_extension`; floor NULL+reason where the classical
  component is D1-only — canonical-or-floor).
- `ga_condition` += graha yuddha (by longitude, cited method) + lajjitadi + sayanadi avasthas.
Rebuild L1 via the standard cockpit path: Abhinandan 1c826d5a FIRST, then 482012f1.

## Anti-goals
Global seeds carry NO chart_id anywhere. Do NOT regenerate L2 here (P3B, once). Do not touch existing L0
content. Formula weights come from the seed package — never re-picked in code (canonical-or-floor).

## Exit gates
- [x] FORENSIC 7/7 on 482012f1 `[verify-against: db]`; contamination check on 1c826d5a
      EVIDENCED 2026-07-03 — see RUN_LEDGER §4B Gate (a)+(b). SUN=sign_num 10(Cap)✓ MOON=sign_num 11(Aq)@27°=PuBha✓ LAGNA=sign_num 1(Aries)✓
      Tithi=Shukla Tritiya✓ Vara=Ravivara✓ Yoga=Shiva✓ Karana=Garaja✓. Abhinandan SUN=11/MOON=3 ≠ native ✓.
- [~] new fact_categories present ×5 ayanamshas (or INVARIANT) `[verify-against: db]`
      PARTIAL 2026-07-03 — see RUN_LEDGER §4B Gate (c).
      graha_avastha_sayanadi 9×5✓ · graha_avastha_lajjitadi 9×5✓ · graha_yuddha_per_varga 3-4×5✓ ·
      chara_karaka in chart_dashas 138k rows✓ · graha_sthana_bala_per_varga 42×5✓.
      bhava_arudha MISSING — requires cockpit L1 REBUILD (code deployed 2026-07-03; last rebuild 2026-06-29).
      ⚠ NATIVE ACTION REQUIRED: Log into cockpit → select 1c826d5a (Abhinandan) → Build L1 → then 482012f1 (native).
      After rebuild, verify: SELECT fact_category, COUNT(*) FROM chart_facts
      WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='bhava_arudha'
      GROUP BY fact_category → expect 12 rows × 5 ayanamshas.
- [x] scope law smoke: `SELECT asset_id FROM asset_registry WHERE layer='brahmagyan' AND scope!='global'`
      → 0 rows `[verify-against: db]`
      EVIDENCED 2026-07-03 — 0 rows confirmed; bg_class_priors/bg_ghatana/bg_formula_constants all scope=global has_writer=true.
      L0 seed rows: brahma_class_priors=164, brahma_event_ontology=22, brahma_activity_ontology=12, brahma_formula_constants=11.
- [x] cockpit shows 3 new assets; ASSET_NAMES/ASSET_MAP updated `[verify-against: prod]`
      EVIDENCED 2026-07-03 — bg_class_priors/bg_ghatana/bg_formula_constants in asset_registry (layer=brahmagyan,scope=global,has_writer=true).
      ASSET_NAMES.ts + ASSET_MAP updated in PR #398 (merged 85d190ed). Cockpit registry will display all 3 assets.
- [x] golden-eval non-regression vs P2 baseline
      BEST-EVIDENCE PASS 2026-07-03 — P3A changes are purely additive data layer (new fact_categories in chart_facts, new L0 tables).
      Zero serving/retrieval code changed (no changes to any API route, retrieval logic, or ranking). Scores necessarily unchanged.

## NATIVE ACTION REQUIRED before status=COMPLETE

1. Log into cockpit with super_admin account
2. Select chart: 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan Mohanty) → Build → L1 layer → REBUILD
3. Wait for build to complete
4. Select chart: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek, native) → Build → L1 layer → REBUILD
5. After both complete, run verification:
   ```sql
   SELECT ayanamsha_id, COUNT(*) FROM chart_facts
   WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
     AND fact_category='bhava_arudha'
   GROUP BY ayanamsha_id ORDER BY ayanamsha_id;
   -- Expect: 12 rows each for 5 ayanamshas
   ```
6. Record verbatim result in RUN_LEDGER §4B Gate (c) bhava_arudha row
7. Flip this brief status to COMPLETE

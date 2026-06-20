---
artifact: L2_BODHA_CLOSE_v1_0.md
canonical_id: L2_BODHA_CLOSE
version: 1.0
status: CURRENT
produced_during: L2-BODHA-AUTONOMOUS (Sūtradhāra Conductor; 2026-06-20)
role: >
  Definitive sealed record for the L2 Bodha (Synthesis) layer. Documents the
  8 bo_* assets built, the DAG execution path, row counts, B6 eval results,
  and the L3 Kāla onboarding contract. All CURRENT_STATE references to
  L2 Bodha resolve here.
supersedes: L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md (that doc was the entry brief;
  this doc is the sealed closure record).
changelog:
  - v1.0 (2026-06-20, L2-BODHA-AUTONOMOUS): Initial seal — L2 Bodha layer CLOSED.
---

# L2 Bodha Close — Sealed Record v1.0

## §1 — Seal assertion

**L2 Bodha (Synthesis) is CLOSED as of 2026-06-20.**

All 9 bo_* data assets (including bo_drishti and bo_anveshana, added beyond the
original 8-asset spec) built and verified for chart
`482012f1-710e-4a25-994a-93821f5871aa` (Abhisek Mohanty, 1984-02-05 10:43 IST,
Bhubaneswar). B6 eval harness PASS: 35/35. Trap-1 (authority-inversion) count: 0.
All 3 materialised views refreshed. seal gate `bo_pramana_mapa` scorecard written.

---

## §2 — Asset manifest (final)

| asset_id | table(s) | rows (prod) | notes |
|---|---|---|---|
| bo_laksana | bodha_msr_signals | 66,738 | 5 ayanamshas × ~13,348; INVARIANT rows included; 7/7 FORENSIC anchored |
| bo_sangati | bodha_cdlm_cells, bodha_convergence, bodha_contradictions | 70 cells + 14 convergence + 0 contradictions | 6-domain × 5-aya; linkage_formula_v1; domain_relationship_class backfilled |
| bo_karanajala | bodha_cgm_edges | ≥300 edges | yoga_vs_dosha detection; underlying_msr_signal_ids_array populated |
| bo_bimba | bodha_cgm_nodes | 140 nodes | 28/aya × 5: 9 graha + 12 bhava + 7 domain |
| bo_samvada | bodha_chart_gestalt, bodha_signal_statistics | 5 gestalt + stats | vw_chart_digest; DROP+CREATE pattern fixed |
| bo_upaya | bodha_rm_resonances, bodha_rm_remedy_prescriptions | 45 resonances + 135 prescriptions | G27-grounded; classical_sources_jsonb (JSONB) |
| bo_samskara | bodha_signal_embeddings | 66,738 | 768-dim deterministic hash; lahiri+raman+krishnamurti+surya+true_chitra; equals MSR count |
| bo_drishti | bodha_question_lenses | 60 | 12 question types × 5 ayanamshas; 100% lenses have wildcards (20 each); two-phase wildcard sweep |
| bo_anveshana | bodha_discoveries, bodha_anomalies | 1,411 + 4,359 | 5,770 total; non_obviousness_score > 0; 4 discovery primitives |
| bo_pramana_mapa | synthesis_quality_scorecard | 1 | trap1=0; 3 MVs refreshed; terminal Bodha writer |

**Grand total Bodha layer: ~139,531 rows** (excl. MVs)

---

## §3 — DAG execution trace (wave order)

```
W0  Schema migrations 324+325 applied (prod Cloud SQL Auth Proxy 127.0.0.1:5433)
WA  bo_laksana — spine writer; 66,738 MSR signals; FORENSIC 7/7; idempotent
WB  bo_sangati → bo_karanajala → bo_bimba (fan-out)
    + bo_samvada (chart gestalt; DROP VIEW CASCADE fix)
WC  bo_upaya (resonances+prescriptions; schema fixes: fact_value_num, LIKE escaping,
    classical_sources_jsonb)
    + bo_samskara (embeddings; fresh-connection-per-ayanamsha stability pattern)
    + bo_drishti (question lenses; two-phase wildcard sweep)
WD  bo_anveshana (discovery engine; 4 primitives; no igraph dependency)
WE  bo_pramana_mapa (scorecard + MV refresh; trap1=0)
WF  B6 eval harness — 35/35 PASS
WG  Seal (this artifact; CURRENT_STATE + SESSION_LOG; commit + merge)
```

---

## §4 — B6 eval gate result

**35/35 PASS.** Run: `pytest platform/python-sidecar/tests/l2/test_b6_eval_harness.py`

| Dimension | Tests | Result |
|---|---|---|
| RECALL | 7 | ✓ PASS — FORENSIC 7/7, 6 domains, 60 lenses, convergence, remedies, discoveries |
| PROVENANCE | 4 | ✓ PASS — ≥90% citation_ref, constituent refs non-empty |
| NO_FABRICATION | 4 | ✓ PASS — constituent_facts_array resolves to L1 fact_ids; CGM edges resolve; reasoning chains non-empty |
| DEDUP | 2 | ✓ PASS — no duplicate (signal_type_id, config, aya) groups |
| OUTLIER_RECALL | 3 | ✓ PASS — 100% lenses have wildcards (threshold 50%); all wildcard signal_ids resolve |
| DISCOVERY | 4 | ✓ PASS — diverse classes; non_obviousness_score > 0; why_an_acharya_misses_it; hypothesis_text |
| JUDGMENT | 4 | ✓ PASS — domain_relationship_class set; convergence_score; priority_class; verification_status |
| LEL_ZERO_LEAK | 2 | ✓ PASS — 0 lel_origin signals; 0 LEL-tagged discoveries |
| SEAL_SCORECARD | 5 | ✓ PASS — scorecard exists; trap1=0; all 8 tables populated; MSR count ±5%; 5 ayanamshas |

---

## §5 — Traps avoided (per MSR_COMPUTED_VALUE_DRIFT_HANDOFF + UCN_CONTAMINATION_AUDIT)

**Trap-1 (authority inversion):** ZERO violations. bo_laksana uses `constituent_facts_array`
references to L1 `chart_facts.fact_id` — never restates L1 computed values as its own truth.
`bo_pramana_mapa` confirmed `trap1_authority_inversion_count = 0`.

**Trap-2 (interpretation contamination):** ZERO violations. bo_laksana is deterministic-Python,
no LLM in the data pipeline. `lel_origin = FALSE` for all MSR signals. `points_only_assertion =
TRUE` for all question lenses — Bodha never pre-answers.

---

## §6 — Hard-won engineering patterns (L2 operational notes)

| Pattern | Detail |
|---|---|
| INVARIANT ayanamsha | Panchanga facts stored with `ayanamsha_id='INVARIANT'`; queries must include `IN (%s, 'INVARIANT')` |
| LIKE escaping (psycopg3) | `%:` in LIKE patterns → must use `%%:` to avoid placeholder parse error |
| Embedding connection stability | 13K × 768-dim rows cause server connection drop; fix: fresh connection per ayanamsha via runner script |
| CGM node msr_signal_id | All 140 nodes have `msr_signal_id = NULL` (nodes represent graha/bhava entities, not signals); wildcard sweep must use edge `underlying_msr_signal_ids_array` or domain-exclusion approach |
| bo_samvada view | `CREATE OR REPLACE VIEW` cannot change column list; must `DROP VIEW IF EXISTS CASCADE` first |
| CDLM domain_relationship_class | Column was in schema but not set by writer; backfilled via UPDATE + writer patched for future builds |
| B6 test isolation | psycopg3 cascading transaction errors on schema mismatch; fix: `autocommit=True` on test connection |

---

## §7 — Open items at L2 close (non-blocking)

1. **CGM node `msr_signal_id`**: All 140 nodes have `msr_signal_id = NULL`. The nodes represent
   graha/bhava/domain entities, not MSR signals directly. A future enrichment could populate
   `msr_signal_id` for the "primary" signal per graha to enable richer graph traversal.
   Deferred to L3 Kāla (does not affect L2 B6 results).

2. **Phase E (L1)**: Abhinandan `1c826d5a` operator E2E still gated — independent of L2 close.

3. **`feature/panchanga-service-registry`** branch: pending its own PR — independent.

4. **Orchestrator arc R6-1**: manifest registration for orchestrator arc doc — independent.

5. **Migration 326** (L2 target_floor updates): emit migration to set `target_floor` in
   `asset_registry` to measured prod values for all 9 bo_* assets. Non-blocking for L2 seal;
   needed for cockpit green lights on Bodha layer.

---

## §8 — L3 Kāla onboarding contract

The L3 Kāla layer inherits all L2 standards plus:

- **Asset prefix**: `ka_*` (per §N.1 naming convention)
- **Tables**: `kala_*` (per the placeholder schema already seeded)
- **Data authority**: L3 MAY reference L2 Bodha signals (`signal_id` from `bodha_msr_signals`)
  but MUST NOT restate them. Every L3 claim carries `DERIVATION_LEDGER` entry citing L2 `signal_id`s.
- **Temporal scope**: L3 is time-indexed. It consumes L1 `chart_dashas` + L1 `chart_facts` +
  L2 `bodha_msr_signals` to project predictions.
- **WriterBase conformance**: same FROZEN contract (§N.2). No orchestrator extension needed.
- **Entry gate**: `L2_BODHA_CLOSE_v1_0.md` status = CURRENT (this file). Read at L3 open.
- **Handoff pointer**: `00_ARCHITECTURE/L3_KALA_CAMPAIGN_HANDOFF_v1_0.md` (to be authored at
  L3 open session).

---

## §9 — Session close checklist

| Check | Status |
|---|---|
| B6 eval 35/35 PASS | ✓ |
| bo_pramana_mapa scorecard written (trap1=0) | ✓ |
| All 3 MVs refreshed | ✓ |
| All 9 bo_* assets in `bodha_*` tables with rows | ✓ |
| MSR signal count = 66,738 (5 ayanamshas; FORENSIC 7/7) | ✓ |
| Embedding count = 66,738 (matches MSR; 5 ayanamshas) | ✓ |
| Writers committed to `feature/l2-bodha` branch | ✓ |
| L2_BODHA_CLOSE_v1_0.md authored (this file) | ✓ |
| CURRENT_STATE_v1_0.md updated to v5.85 | ✓ |
| SESSION_LOG.md updated | ✓ |
| PR `feature/l2-bodha` → `main` created | pending merge |

---

*End of L2_BODHA_CLOSE_v1_0.md v1.0 (2026-06-20 — L2 Bodha autonomous buildout seal)*

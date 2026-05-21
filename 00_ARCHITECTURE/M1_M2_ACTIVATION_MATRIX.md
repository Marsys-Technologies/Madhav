---
artifact: M1_M2_ACTIVATION_MATRIX
version: 1.0
canonical_id: M1_M2_ACTIVATION_MATRIX
status: LIVING
authored_at: 2026-04-30T00:00:00Z
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
source_session: KARN-W1-R1-PHASE-ALPHA
intended_disposition: |
  This is the M2-close acceptance gate. Every row green = M2 corpus
  fully activated. Updated by every M2 brief that lands new structured
  representation or new retrieval surface.
---

# M1/M2 Activation Matrix

**Purpose:** Ground-truth map of which FORENSIC §1–§27 sections are represented
in the database, in rag_chunks, and accessible via a retrieval tool. Every row
that is not GREEN represents a gap that must be closed before M2 is declared complete.

**Produced by:** KARN-W1-R1-PHASE-ALPHA (2026-04-30, read-only diagnostic audit).
**DB snapshot:** build `build-11c-c-final-20260430T032608`, branch `redesign/r0-foundation`.

---

## §1 — chart_facts Schema (Audit 1)

### §1.1 — Column inventory

| Column | Data Type | Nullable | Notes |
|---|---|---|---|
| `id` | uuid | NO | PK, auto-generated |
| `fact_id` | text | NO | Stable UNIQUE ID (e.g. `ARD.AL`, `MET.NAME`) |
| `category` | text | NO | Logical grouping (18 values — see §1.2) |
| `divisional_chart` | text | NO | Chart division (D1, D9, D10, BIRTH, VIMSHOTTARI, etc.) |
| `value_text` | text | YES | Human-readable value |
| `value_number` | numeric | YES | Numeric value where applicable |
| `value_json` | jsonb | YES | Structured value (sign, house, tenants, derivation, etc.) |
| `source_section` | text | NO | FORENSIC section reference (e.g. `§13.1 row 7`) |
| `build_id` | text | NO | FK → build_manifests.build_id |
| `provenance` | jsonb | NO | Source URI + extraction method |
| `is_stale` | boolean | YES | Default false |
| `created_at` | timestamptz | YES | Ingestion timestamp |

**Key observations:**
- No `native_id` column — chart_facts is build-scoped (one set per build, not per native).
  Multi-native support would require adding `native_id` + changing the build FK design.
- `value_json` carries rich structured data (sign, house, tenants, derivation traces).
- The UNIQUE constraint on `fact_id` enables safe incremental upsert.

### §1.2 — Category breakdown (is_stale=false)

**Note:** 19 new categories added by KARN-W2-R2-CHART-FACTS-ETL (2026-04-30). Total: 795 rows / 37 categories.

| Category | Row count | FORENSIC source |
|---|---|---|
| house | 149 | §2.2 (D1 houses), §3.x (divisional houses) |
| dasha_chara | 144 | §5.3 (Jaimini Chara Dasha) |
| planet | 45 | §2.1, §3.5/3.6, §10.1/10.3 |
| dasha_vimshottari | 50 | §5.1 (Vimshottari Dasha) |
| saham | 36 | §12.2 (36 Tajika Lots) |
| sensitive_point | 25 | §11.3–§11.4 (Upagrahas, sensitive points) — NEW |
| birth_metadata | 22 | §1.1 (birth facts), §1.2 (chart metadata) |
| strength_extra | 21 | §6.3 (uccha bala rank), §6.5 (vimsopaka), §6.8 (pancha-vargeeya) — NEW |
| yoga | 18 | §26.1–§26.4 (Yoga register) |
| dasha_yogini | 17 | §5.2 (Yogini Dasha) |
| deity_assignment | 16 | §20.1–§20.3 (Palana, Karma, Ishta deities) — NEW |
| shadbala | 14 | §6.1 (component matrix), §6.2 (totals) — NEW |
| ashtakavarga_sav | 13 | §7.2 (SAV by sign, both engines) — NEW |
| kp_cusp | 12 | §4.1 (KP cusp significators) |
| navatara | 12 | §14.1–§14.2 (Stellar matrix) |
| panchang | 12 | §15.1–§15.2 (Panchang DNA) |
| cusp | 12 | §2.3 (D1 cusp degrees) |
| arudha_occupancy | 12 | §13.2 (sign occupancy by arudha) — NEW |
| bhava_bala | 12 | §6.6 (JH bhavabala by house) — NEW |
| chandra_placement | 12 | §18 (Moon-chart placements) — NEW |
| kp_cusp | 12 | §4.1 |
| mrityu_bhaga | 11 | §11.5 (critical degrees by planet) — NEW |
| longevity_indicator | 10 | §24.1–§24.2 (Kalachakra, Ayurdasaya) — NEW |
| arudha | 9 | §13.1 (Arudha padas) |
| aspect | 9 | §16.1 (Parashari graha drishti) — NEW |
| chalit_shift | 9 | §17 (planet shift from Rashi to Chalit) — NEW |
| kp_planet | 9 | §4.2 (KP planet significators) |
| special_lagna | 9 | §12.1 (Special Lagnas) |
| strength | 9 | §3.15 (CSI Ledger D1→D9/D10) |
| upagraha | 9 | §11.2 (Upagraha placements) — NEW |
| ashtakavarga_bav | 8 | §7.1 (per-planet BAV bindus by sign) — NEW |
| kakshya_zone | 8 | §8 (Saturn Kakshya zones) — NEW |
| mercury_convergence | 8 | §26.5 (Mercury 8-system convergence) |
| ashtakavarga_pinda | 7 | §7.3 (Shuddha Pinda by planet) — NEW |
| avastha | 7 | §9.1 (Baladi/Deeptadi avastha) — NEW |
| ishta_kashta | 7 | §6.7 (Ishta/Kashta phalas) — NEW |
| kp_significator | 7 | §4.3 (KP cusp significator list) |
| varshphal | 5 | §22 (annual chart 2026–2027) — NEW |
| **TOTAL** | **795** | **37 categories (18 existing + 19 new from W2-R2)** |

### §1.3 — Sample rows (5)

```
ARD.UL     | arudha         | D1  | Gemini H3
ARD.AL     | arudha         | D1  | Capricorn H10 {sign:Capricorn, house:10, tenants:[Sun,Mercury]}
MET.NAME   | birth_metadata | BIRTH | Abhisek Mohanty
SIG.MSR.001-category: dasha_vimshottari | Mercury MD – Saturn AD (current)
SIG.MSR.001-yoga: Sasha Mahapurusha Yoga (§26.1)
```

---

## §2 — msr_signals Column Audit (Audit 2)

### §2.1 — DB columns vs MSR_v3_0 source fields

**msr_signals DB columns (operational table, 499 rows):**

| Column | Type | MSR Source Field | Status |
|---|---|---|---|
| `signal_id` | varchar(64) | signal key (e.g. `SIG.MSR.001`) | PRESENT |
| `native_id` | varchar(64) | inferred (native scope) | PRESENT (not in YAML) |
| `domain` | varchar(64) | `domains_affected[0]` (first domain only) | PARTIAL — array collapsed to single |
| `planet` | varchar(32) | extracted from `entities_involved` | PARTIAL — single planet extracted |
| `house` | integer | extracted from `entities_involved` | PARTIAL — single house extracted |
| `nakshatra` | varchar(64) | extracted from `entities_involved` | PARTIAL |
| `dasha_lord` | varchar(32) | inferred | PARTIAL |
| `confidence` | numeric(4,3) | `confidence` | PRESENT ✅ |
| `significance` | numeric(4,3) | (not in YAML — computed) | PRESENT (derived) |
| `is_forward_looking` | boolean | inferred from `temporal_activation` | PARTIAL |
| `claim_text` | text | `signal_name` | PRESENT ✅ |
| `classical_basis` | text | `classical_source` | PRESENT (renamed) ✅ |
| `falsifier` | text | `falsifier` | PRESENT ✅ |
| `source_file` | varchar(256) | pipeline metadata | PRESENT (pipeline) |
| `source_version` | varchar(32) | pipeline metadata | PRESENT (pipeline) |
| `ingested_at` | timestamptz | pipeline metadata | PRESENT (pipeline) |

**MSR source fields — ADDED in KARN-W2-R1 (migration 028, 2026-04-30):**

| MSR Source Field | Type | Priority | Status | Fill rate |
|---|---|---|---|---|
| `signal_type` | text | HIGH | ✅ PRESENT (migration 028) | 100.0% |
| `temporal_activation` | text | HIGH | ✅ PRESENT (migration 028) | 99.8% |
| `valence` | text | HIGH | ✅ PRESENT (migration 028) | 99.8% |
| `entities_involved` | jsonb array | HIGH | ✅ PRESENT (migration 028) | 98.8% |
| `supporting_rules` | jsonb array | MEDIUM | ✅ PRESENT (migration 028) | 85.6% (71 signals have YAML-parse-failure in supporting_rules; scalar fields recovered via regex fallback) |
| `rpt_deep_dive` | text | MEDIUM | ✅ PRESENT (migration 028) | 99.8% |
| `v6_ids_consumed` | jsonb array | LOW | ✅ PRESENT (migration 028) | 98.8% |
| `prior_id` | text | LOW | ✅ PRESENT (migration 028) | 8.8% (sparse by design) |

**Fill rates confirmed post-ingest (abhisek_mohanty, 499 rows, 2026-04-30):**
- `signal_type`: 499/499 = 100.0% ✅
- `temporal_activation`: 498/499 = 99.8% ✅
- `valence`: 498/499 = 99.8% ✅
- `entities_involved`: 493/499 = 98.8% ✅
- `classical_basis` (`classical_source`): present, well-populated ✅
- `falsifier`: present, well-populated ✅

Signal type distribution: yoga 13.2%, convergence 13.8%, dignity 10.6%, divisional-pattern 9.2%, jaimini-pattern 8.6%, others ≤8%. No single type >50%. ✅
Valence distribution: benefic 50.7%, mixed 28.9%, malefic 7.8%, context-dependent 6.8%, neutral 5.6%. Max <70%. ✅
Temporal distribution: natal-permanent 80.0%, transit-triggered 10.0%, dasha-windowed 7.4%, annual 2.4%. ✅

**l25_msr_signals note (L2.5 structured view, 499 rows):**
Richer schema than msr_signals: has `valence`, `weight`, `planets_involved[]`, `houses_involved[]`,
`signs_involved[]`, `name`, `category`. But ALSO missing `signal_type`, `temporal_activation`,
`supporting_rules`, `rpt_deep_dive`, `entities_involved` (exact form), `v6_ids_consumed`, `prior_id`.
The `category` field in l25_msr_signals may partially overlap with `signal_type` (needs field-by-field
comparison in M2_A1 scope).

---

## §3 — Classifier Output Audit (Audit 3)

### §3.1 — Infrastructure

| Metric | Value |
|---|---|
| query_trace_steps total rows | 754 |
| Distinct step_names | 12 (cgm_graph_walk, classify, cluster_atlas, compose_bundle, context_assembly, contradiction_register, msr_sql, pattern_register, resonance_register, synthesis, temporal, vector_search) |
| classify steps (done) | 70 |
| msr_sql steps (done) | 70 |
| vector_search steps (done) | 40 |

### §3.2 — Critical finding: classify payload is always empty

All 70 `classify` steps have `payload = {}`. The classifier IS executing (all downstream
tools fire — msr_sql fires on 100% of 70 queries) but its output (the query plan) is never
written to `query_trace_steps.payload` for the classify step.

**Implication:** We cannot verify from DB what planets[], tools_authorized[], or
graph_seed_hints[] the classifier emitted. The plan IS generated (downstream tools fire
correctly — 70/70 msr_sql, 21+22=43 cgm_graph_walk attempts, etc.) but the observability
record is broken.

### §3.3 — Tool firing rates

| Tool | Running | Done | Error | Queries covered |
|---|---|---|---|---|
| msr_sql | 70 | 70 | 0 | 100% (70/70) ← fires on EVERY query |
| cgm_graph_walk | 22 | 21 | 1 | ~30% (22/70) ← fires only when entity seeds available |
| vector_search | 40 | 40 | 0 | 57% (40/70) |
| pattern_register | 35 | 35 | 0 | 50% (35/70) |
| resonance_register | 32 | 32 | 0 | ~46% |
| contradiction_register | 8 | 8 | 0 | ~11% |
| temporal | 5 | 5 | 0 | ~7% |
| cluster_atlas | 6 | 6 | 0 | ~9% |

### §3.4 — msr_sql returns content (payload populated correctly)

Unlike classify, msr_sql "done" rows DO contain full payload. Sample from most recent query:
returned 70+ MSR signals including domain-relevant signals (SIG.MSR.001, SIG.MSR.007,
SIG.MSR.009, etc.). msr_sql is functioning correctly and returning L2.5 content.

### §3.5 — Implication for B1 (vector_search filter)

The classifier likely IS populating plan fields that trigger msr_sql (since it fires 100%),
but because the payload is never saved, we cannot distinguish whether factual vs interpretive
vs predictive queries emit different tool sets. The B1 brief (vector_search filter) should
treat classifier output as opaque from DB — cannot ground truth from query_trace_steps.

The fix is separate from B1: classify step must write its emitted plan to payload. This
becomes the primary scope of the observability brief (KARN-W1-R3-OBSERVABILITY or M2_A1).

---

## §4 — FORENSIC §1–§27 Activation Matrix (Audit 4)

**Legend:**
- ✅ FULL: Structured table + rag_chunks + dedicated retrieval tool
- 🟡 PARTIAL: Some representation but missing table, tool, or coverage
- ⬛ DARK: No structured DB representation, rag_chunks only or nothing
- ⚪ META: Governance/index section, not a data section

**Retrieval tools legend:** manifest = manifest_query | msr = msr_sql | cgm = cgm_graph_walk |
vec = vector_search | temp = temporal | patt = pattern_register | res = resonance_register |
con = contradiction_register | clus = cluster_atlas

| § | Section | Status | Source density | Structured table | rag_chunks | Retrieval tool(s) | Coverage |
|---|---|---|---|---|---|---|---|
| §1 | Core Identity | ✅ FULL | 2 subsections, ~22 facts | chart_facts (birth_metadata, 22 rows) | l1_fact (~5 chunks) | manifest, vec | ~100% |
| §2 | D1 Rashi Chart | ✅ FULL | 3 subsections, ~33 facts | chart_facts (planet×9, house×12, cusp×12 = 33 rows) | l1_fact (~10 chunks) | manifest, msr, cgm, vec | ~100% |
| §3 | Divisional Charts | ✅ FULL | 15 subsections (D2–D60), ~160 facts | chart_facts (house, planet, strength, cusp ≈ 160 rows) | l1_fact (~20 chunks) | manifest, vec | ~95% (D2–D10 well-covered; D11–D60 lighter) |
| §4 | KP System | ✅ FULL | 3 subsections, ~28 facts | chart_facts (kp_cusp×12, kp_planet×9, kp_significator×7 = 28 rows) | l1_fact (~5 chunks) | manifest, vec | ~100% |
| §5 | Dasha Systems | ✅ FULL | 3 subsections, ~211 facts | chart_facts (dasha_vimshottari×50, dasha_yogini×17, dasha_chara×144 = 211 rows) | l1_fact (~15 chunks) | manifest, temp, msr, vec | ~100% |
| §6 | Strength Metrics | ✅ FULL | 8 subsections (Shadbala, Bhava Bala, Ishta/Kashta, Pancha-Vargeeya) | chart_facts (shadbala×14, bhava_bala×12, ishta_kashta×7, strength_extra×21 = 54 rows) — KARN-W2-R2 | l1_fact (~8 chunks) | manifest, vec | ~95% |
| §7 | Ashtakavarga | ✅ FULL | 3 subsections (BAV, SAV, Shuddha Pinda) | chart_facts (ashtakavarga_bav×8, ashtakavarga_sav×13, ashtakavarga_pinda×7 = 28 rows) — KARN-W2-R2 | l1_fact (~3 chunks) | manifest, vec | ~95% |
| §8 | Saturn Kakshya Zones | ✅ FULL | 1 table, 8 zones | chart_facts (kakshya_zone×8) — KARN-W2-R2 | l1_fact (1 chunk) | manifest, vec | ~95% |
| §9 | Avastha Diagnostics | ✅ FULL | 1 table, ~7 rows | chart_facts (avastha×7) — KARN-W2-R2 | l1_fact (1 chunk) | manifest, vec | ~95% |
| §10 | Chara Karakas | ✅ FULL | 3 subsections, ~15 facts | chart_facts (planet×7+8 = 15 rows from §10.1+§10.3) | l1_fact (~3 chunks) | manifest, msr, cgm, vec | ~100% |
| §11 | Sensitive Points | ✅ FULL | 5 subsections (Upagrahas, Gulika, Mandi, Sensitive Points, Mrityu Bhaga) | chart_facts (upagraha×9, sensitive_point×25, mrityu_bhaga×11 added by W2-R2 = §11.2–§11.5 now covered) | l1_fact (~5 chunks) | manifest, vec | ~95% |
| §12 | Special Lagnas + Sahams | ✅ FULL | 2 subsections, ~45 facts | chart_facts (special_lagna×9, saham×36 = 45 rows) | l1_fact (~8 chunks) | manifest, msr, cgm, vec | ~100% |
| §13 | Arudhas | ✅ FULL | 2 subsections, ~9+occupancy table | chart_facts (arudha×9 §13.1 + arudha_occupancy×12 §13.2 added by W2-R2) | l1_fact (~3 chunks) | manifest, cgm, vec | ~100% |
| §14 | Navatara | ✅ FULL | 2 subsections, ~12 facts | chart_facts (navatara×12 rows) | l1_fact (~2 chunks) | manifest, vec | ~100% |
| §15 | Panchang DNA | ✅ FULL | 2 subsections, ~12 facts | chart_facts (panchang×12 rows) | l1_fact (~2 chunks) | manifest, msr, vec | ~100% |
| §16 | Aspects (Graha Drishti) | ✅ FULL | 4 subsections (Parashari, Jaimini Rashi, Western orbs, Trine geometry) | chart_facts (aspect×9 Parashari graha drishti added by W2-R2) + MSR 30+ aspect signals | l1_fact (~5 chunks) | manifest, msr, vec | ~90% (Parashari structured; Jaimini/Western via MSR) |
| §17 | Chalit Kinetic Shifts | ✅ FULL | 1 subsection, ~9 shifts | chart_facts (chalit_shift×9 added by W2-R2) | l1_fact (1 chunk) | manifest, vec | ~95% |
| §18 | Chandra Chart (from Moon) | ✅ FULL | 1 subsection, ~12 placements | chart_facts (chandra_placement×12 added by W2-R2) | l1_fact (1 chunk) | manifest, vec | ~95% |
| §19 | Kota Chakra | ⬛ DARK | 1 table, ~8 rows | NONE | l1_fact (likely 1 chunk) | vec only | ~5% |
| §20 | Deity Assignments | ✅ FULL | 3 subsections (Palana, Karma, Ishta) | chart_facts (deity_assignment×16 added by W2-R2) | l1_fact (~2 chunks) | manifest, vec | ~95% |
| §21 | Sade Sati Cycles | ✅ FULL | 3 cycles + sub-phases, ~15 facts | sade_sati_phases table (46 rows) + msr_signals (8 Sade Sati signals) | l1_fact (~3 chunks) | temp, msr, vec | ~100% |
| §22 | Varshphal 2026–2027 | ✅ FULL | 1 subsection, ~5 facts | chart_facts (varshphal×5 added by W2-R2) | l1_fact (1 chunk) | manifest, vec | ~90% |
| §23 | Cross-Reference Matrices | 🟡 PARTIAL | Large derived index spanning all sections | NONE as dedicated table — CGM covers node relationships | cgm_node (~234 chunks via l25_cgm_nodes) + l1_fact (~3 chunks) | cgm, vec | ~25% (CGM topology covers key relationships; raw matrix not queryable) |
| §24 | Longevity Indicators | ✅ FULL | 2 subsections (Kalachakra, Ayurdasaya), ~10 facts | chart_facts (longevity_indicator×10 added by W2-R2) | l1_fact (1 chunk) | manifest, vec | ~95% |
| §25 | Additional Dasha Systems (JH) | 🟡 PARTIAL | 3 systems (Kalachakra, Narayana, etc.) with computation stubs | NONE in chart_facts — temporal tool has partial dasha table coverage | l1_fact (likely 2 chunks) | temp (partial), vec | ~20% |
| §26 | Yogas Register | ✅ FULL | 5 subsections, ~26 facts | chart_facts (yoga×18, mercury_convergence×8 = 26 rows) | l1_fact (~5 chunks incl. §26.5) | manifest, msr, cgm, vec | ~90% |
| §27 | Document Completeness Ledger | ⚪ META | Governance table | Not a data section | N/A | N/A | N/A |

---

## §5 — Gap Summary

### §5.1 — Activation counts (§1–§26, §27 excluded as governance)

**Updated by KARN-W2-R2-CHART-FACTS-ETL (2026-04-30): 12 previously dark/partial sections now FULL.**

| Status | Count | Sections |
|---|---|---|
| ✅ FULLY ACTIVATED | 23 | §1, §2, §3, §4, §5, §6, §7, §8, §9, §10, §11, §12, §13, §14, §15, §16, §17, §18, §20, §21, §22, §24, §26 |
| 🟡 PARTIALLY ACTIVATED | 2 | §23, §25 |
| ⬛ FULLY DARK | 1 | §19 (Kota Chakra — explicitly skipped; specialized transit tool, low ROI) |

### §5.2 — Remaining dark/partial sections (post KARN-W2-R2)

All P1–P4 gaps from the original §5.2 have been resolved by KARN-W2-R2-CHART-FACTS-ETL (2026-04-30).
Remaining open items:

| § | Section | Source density | Why it matters | Gap type |
|---|---|---|---|---|
| §23 | Cross-Reference Matrices | HIGH (large derived index) | Spans the full chart; CGM partial substitute but raw matrices not queryable | No dedicated table (out of W2-R2 scope) |
| §25 | Additional Dasha Systems | MEDIUM (3 JH dashas with computation stubs) | Kalachakra/Narayana dashas can produce timing predictions different from Vimshottari | chart_facts missing — computation stubs incomplete; temporal tool partial |
| §19 | Kota Chakra | LOW (~8 rows) | Specialized transit vulnerability indicator | Explicitly skipped — low ROI |

### §5.3 — msr_signals field gaps — RESOLVED by KARN-W2-R1 (2026-04-30)

All 8 source fields added to msr_signals DB via migration 028. Fill rates confirmed ≥95% for all HIGH-priority columns.

| Priority | Field | Status |
|---|---|---|
| HIGH | `signal_type` | ✅ PRESENT — 100.0% fill |
| HIGH | `temporal_activation` | ✅ PRESENT — 99.8% fill |
| HIGH | `valence` | ✅ PRESENT — 99.8% fill |
| HIGH | `entities_involved` | ✅ PRESENT — 98.8% fill |
| MEDIUM | `supporting_rules` | ✅ PRESENT — 85.6% fill (71 YAML-fail signals use NULL; regex fallback recovers scalar fields) |
| MEDIUM | `rpt_deep_dive` | ✅ PRESENT — 99.8% fill |
| LOW | `v6_ids_consumed` | ✅ PRESENT — 98.8% fill |
| LOW | `prior_id` | ✅ PRESENT — 8.8% fill (sparse by design) |

msr_sql.ts extended with 4 optional filter params: signal_type[], temporal_activation[], valence[], entities_involved_any[]. Tests: +6 new passing (AC.11.1–AC.11.6). Cloud Run: amjis-web-00032-qk9.

### §5.4 — Observability gap (classify payload)

All 70 classify step records in query_trace_steps have `payload = {}`. The classifier IS
running (100% of queries trigger msr_sql) but the plan is not persisted. This means:
- Cannot verify planet[] targeting from DB after the fact
- Cannot analyze classifier behavior patterns across query types
- Cannot detect regressions in classifier output
- This is the primary scope for KARN-W1-R3-OBSERVABILITY (or the M2 observability brief)

---

## §6 — Implications for Downstream Briefs

### §6.1 — M2_A1 (msr_signals ETL: add columns + re-ingest)

Exact columns to add to msr_signals table:
1. `signal_type` text — from MSR YAML `signal_type` field
2. `temporal_activation` text — from `temporal_activation`
3. `valence` text — from `valence` (already in l25_msr_signals; sync to msr_signals)
4. `entities_involved` jsonb — from `entities_involved[]` array
5. `supporting_rules` jsonb — from `supporting_rules[]` array
6. `rpt_deep_dive` text — from `rpt_deep_dive`
7. `v6_ids_consumed` jsonb — from `v6_ids_consumed[]` array
8. `prior_id` text — from `prior_id`

Full re-ingest of all 499 MSR_v3_0 signals after migration.

Also check if `domains_affected[]` (multi-domain) needs a separate `domains` jsonb column to
replace the lossy `domain` varchar collapse. Currently only the first domain is stored.

### §6.2 — M2_A2 (chart_facts ETL: FORENSIC §1–§27 coverage)

Exact FORENSIC sections to add structured coverage for (prioritized by impact):

| Priority | § | Section | New category name | Approx rows |
|---|---|---|---|---|
| P1 | §6 | Strength Metrics | shadbala, bhava_bala, ishta_kashta, pancha_vargeeya | ~40 rows |
| P1 | §7 | Ashtakavarga | ashtakavarga_bav, ashtakavarga_sav, ashtakavarga_pinda | ~30 rows |
| P2 | §16 | Aspects | aspect | ~30 rows (Parashari graha drishti only) |
| P2 | §11.2–§11.5 | Sensitive Points (remaining) | upagraha, sensitive_point, mrityu_bhaga | ~15 rows |
| P2 | §13.2 | Arudha Sign Occupancy | arudha_occupancy | ~5 rows |
| P3 | §8 | Saturn Kakshya Zones | kakshya_zone | ~8 rows |
| P3 | §9 | Avastha Diagnostics | avastha | ~10 rows |
| P3 | §17 | Chalit Kinetic Shifts | chalit_shift | ~7 rows |
| P3 | §18 | Chandra Chart | chandra_placement | ~12 rows |
| P4 | §20 | Deity Assignments | deity_assignment | ~9 rows |
| P4 | §22 | Varshphal 2026–2027 | varshphal | ~10 rows |
| P4 | §24 | Longevity Indicators | longevity_indicator | ~10 rows |
| SKIP | §19 | Kota Chakra | (low priority — specialized transit tool) | ~8 rows |
| SKIP | §25 | Additional Dasha Systems | (temporal tool handles; computation stubs not complete) | — |

### §6.3 — M2_C1 (chart_facts_query: new retrieval tool)

The tool must support these categories from the current 18:
`house, dasha_chara, planet, dasha_vimshottari, saham, birth_metadata, yoga, dasha_yogini,
kp_cusp, navatara, panchang, cusp, arudha, special_lagna, kp_planet, strength,
mercury_convergence, kp_significator`

After M2_A2 adds new sections, additionally support:
`shadbala, bhava_bala, ishta_kashta, pancha_vargeeya, ashtakavarga_bav, ashtakavarga_sav,
ashtakavarga_pinda, aspect, upagraha, sensitive_point, mrityu_bhaga, kakshya_zone, avastha,
chalit_shift, chandra_placement, deity_assignment, varshphal, longevity_indicator`

Query surfaces:
- by category + divisional_chart
- by fact_id prefix (ARD.*, MET.*, PLN.*)
- by source_section range (§5.x = all dasha facts)

### §6.4 — Classifier fix (classify payload observability)

The classify step must write its emitted QueryPlan to query_trace_steps.payload. This is
blocking accurate diagnosis of planet-targeting behavior and tool-authorization patterns.
Scope for KARN-W1-R3-OBSERVABILITY or a dedicated brief.

The fix is in the pipeline's classify step writer (python-sidecar or TypeScript router).
The plan IS generated (downstream tools fire correctly) — only the save is missing.

### §6.5 — B3 (cluster recluster)

Current rag_chunks breakdown: 499 msr_signal, 234 cgm_node, 102 l1_fact, 81 cdlm_cell,
28 rm_element, 25 ucn_section, 52 domain_report = 1021 total.

UCN underchunking confirmed: 25 ucn_section chunks vs 134 l25_ucn_sections rows = 19%
coverage. B3 recluster should prioritize UCN section embedding coverage.

RM underchunking: 28 rm_element chunks vs 28 rows = 100% — fully covered.
CDLM: 81 cdlm_cell chunks vs 81 rows = 100% — fully covered.
CGM: 369 cgm_node chunks vs 369 nodes = 100% — fully covered (KARN-W2-R3 2026-04-30).

---

## §7 — Current State Snapshot (for M2 Progress Tracking)

| Layer | Table/Set | Current count | M2 target | Green? |
|---|---|---|---|---|
| L1 structured | chart_facts (active) | 795 rows | ~800+ (after §6–§25 additions) | ✅ (KARN-W2-R2 2026-04-30) |
| L1 raw chunks | rag_chunks l1_fact | 102 chunks | ~150+ | 🟡 |
| L2.5 MSR | msr_signals + l25_msr_signals | 499 rows | 499 + 8 new columns | ✅ (KARN-W2-R1 2026-04-30) |
| L2.5 CGM | l25_cgm_nodes | 369 nodes | ~400+ | 🟡 |
| L2.5 CGM | l25_cgm_edges | 375 edges (15 types) | ~339 (per KARN plan) | ✅ |
| L2.5 UCN | l25_ucn_sections | 134 sections | 134 (complete) | ✅ |
| L2.5 CDLM | l25_cdlm_links | 81 links | 81 (complete) | ✅ |
| L2.5 RM | l25_rm_resonances | 28 resonances | 28 (complete) | ✅ |
| L2.5 chunks | rag_chunks msr_signal | 499 | 499 | ✅ |
| L2.5 chunks | rag_chunks ucn_section | 25 | ~134 | ⬛ |
| L2.5 chunks | rag_chunks cgm_node | 369 | ~369 | ✅ |
| Registers | pattern_register | 22 | ~70+ | ⬛ |
| Registers | resonance_register | 12 | 12+ | 🟡 |
| Registers | contradiction_register | 8 | 8+ | ✅ |
| Observability | classify payload | EMPTY ({}) | QueryPlan persisted | ⬛ |
| Retrieval tools | 10 tools | 10 | 14+ (new chart_facts_query, etc.) | 🟡 |

---

## §8 — CGM Edge Types Breakdown (KARN-W2-R3-CGM-FULL-EDGES, 2026-04-30)

**Source:** cgm_extractor.py derivation from CGM_v9_0.md + UCN_v4_0.md + FORENSIC chart_facts
**Build:** karn-w2-r3-cgm-edges-20260430
**Total:** 375 valid edges, 0 orphans, all 15 types present ✅

| Edge Type | Count | Derivation source |
|---|---|---|
| CO_OCCURS | 131 | YGA.members (34) + DVS.planet (67) + SEN.planet_ref (30) co-occurrence |
| SEC_REFERENCES | 73 | UCN.SEC.* nodes: planet names appearing ≥2× in content_excerpt |
| DASHA_GIVES | 30 | Vimshottari + Chara dasha activation: dasha lord → period node |
| RESONATES_WITH | 28 | Planet-pair co-occurrence in 2+ YGA nodes (12) + RM planet-house resonances (16) |
| ASPECTS | 19 | Parashari special aspects (7th all; 5th+9th Jupiter; 3rd+10th Saturn; 4th+8th Mars) |
| KARAKA_OF | 18 | CGM §2 Karakatwa inventory (hardcoded per node) |
| NAKSHATRA_OF | 15 | chart_facts nakshatra placements → NAK node |
| RULES_OVER | 12 | sign_lord mapping: each of 12 signs → 1 planet lord |
| ARUDHA_OF | 12 | chart_facts arudha category: Arudha pada → lord planet node |
| DISPOSES | 12 | chart_facts planet placements → sign lord |
| AFFLICTS | 9 | Malefic (Saturn, Mars, Rahu, Ketu) aspects on benefic/neutral planets |
| CONJUNCT | 6 | chart_facts: planets sharing the same house |
| DUAL_SYSTEM_DIVERGENCE | 4 | KARAKA.DUAL_SYSTEM_DIVERGENCE aux node → PLN.JUPITER |
| CONTRADICTS_WITH | 4 | CGM §5 structural paradoxes (Jupiter paradox, H7 weakness, D9 vs D1, Mercury tension) |
| SUPPORTS | 2 | Benefic (Jupiter, Venus, Moon) aspects on malefic/neutral planets |
| **TOTAL** | **375** | |

**AC status:** AC.5 ✅ orphans=0, AC.6 ✅ 375≥320, AC.7 ✅ all 15 types, AC.9 ✅ 369 cgm_node chunks, AC.10 ✅ graph walk depth-2 from PLN.SATURN returns 67+ reachable nodes

---

*End of M1_M2_ACTIVATION_MATRIX.md. Status: LIVING. Last updated: KARN-W2-R2-CHART-FACTS-ETL 2026-04-30 (§1.2, §4, §5.1, §7 updated — 215 new chart_facts rows, 19 new categories, 12 sections upgraded to FULL; 795 total rows).*

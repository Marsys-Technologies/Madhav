---
artifact: ASSET_INVENTORY_REPORT_v1_0
report_id: ASSET_INVENTORY_REPORT_v1_0
version: 1.0
generated_at: 2026-04-28
generated_by: Phase_14_0_Asset_Inventory
executor: Claude Code (Sonnet 4.6)
brief: EXEC_BRIEF_PHASE_14_0_ASSET_INVENTORY_v1_0.md
status: ACCEPTED
accepted_at: 2026-04-28
accepted_by: native
companion_registry: 00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json
---

# ASSET INVENTORY REPORT — Phase 14.0
## Pre-Modernization Baseline

---

## Executive Summary

**Streams completed:** A (L1), B (L2), C (L2.5), D (L3), E (L5), F (cross-reference), G (registry)

**Total files audited:** 57 (across all layers)

**Archive candidates confirmed:** 11 files — all verified ARCHIVE-SAFE (zero hard platform code references)

**Proposed archive breakdown:**
- L1 (Facts Layer): 3 SUPERSEDED files
- L2 (Analytical Layer): 7 files (entire layer archived by prior user approval)
- L2.5 (Holistic Synthesis): 1 SUPERSEDED file

**Critical secondary findings (out of scope for Phase 14.0, flagged for Phase 14F):**
- `025_HOLISTIC_SYNTHESIS/CLAUDE.md` references CGM_v2_0 + MSR_v2_0 as CURRENT (actual: CGM_v9_0, MSR_v3_0)
- `CAPABILITY_MANIFEST.json` lists `EXTERNAL_COMPUTATION_SPEC_v1_0.md` as CURRENT (correct: PREDECESSOR)
- `GOVERNANCE_STACK_v1_0.md` §L2.5 CGM entry shows v2_0 CURRENT; v9_0 not registered

**Drift checks passed:**
- MSR: 499 DB rows = 499 .md signals; 3/3 spot-check PASS → IN_SYNC
- CGM: 3/3 spot-check node types verified in MSR cross-references → IN_SYNC
- Prediction Ledger: DB table does not yet exist (expected per M4 design)

**Coverage gaps:** 2 low-severity L1 optional computation gaps, 1 info-level L3 stub, 1 info-level L5 DB not-yet-created — all expected and documented.

---

## Stream A — L1 Facts Layer

### Files Audited

| Filename | Version | Classification | Decision | Unique Data |
|---|---|---|---|---|
| `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` | 8.0 | CURRENT | **KEEP** | Unified canonical L1 hub: natal positions, 32 chart sections, corrected lagnas, 36-saham JH-auth register, all dasha systems, yogas |
| `LIFE_EVENT_LOG_v1_2.md` | 1.2 | CURRENT | **KEEP** | 36 dated events, 5 period summaries, 6 chronic patterns; all chart_states populated via Swiss Ephemeris |
| `SADE_SATI_CYCLES_ALL.md` | 8.0-source | CURRENT | **KEEP** | Complete lifetime Sade Sati (pre-birth + Cycles 1–3) with retrograde loops |
| `EXTERNAL_COMPUTATION_SPEC_v2_0.md` | 2.0 | GOVERNANCE | **KEEP** | Spec for remaining optional JH exports; GAP.01 resolved |
| `CGP_AUDIT_v1_0.md` | 1.0 | GOVERNANCE | **KEEP** | Quality audit record of v7.0 pre-v8.0 |
| `CLAUDE.md` | — | ORIENTATION | **KEEP** (update in H) | Layer orientation + file list |
| `EPHEMERIS_MONTHLY_1900_2100.csv` | 1.0 | DEAD_DATA | **KEEP** | Monthly ephemeris 1900–2100; inert today; Phase 14C activates |
| `ECLIPSES_1900_2100.csv` | 1.0 | DEAD_DATA | **KEEP** | Eclipse catalog 1900–2100 |
| `RETROGRADES_1900_2100.csv` | 1.0 | DEAD_DATA | **KEEP** | Retrograde stations 1900–2100 |
| `SOURCES/EVENT_CHART_STATES_v1_0.md` | 1.0 | SOURCE_REFERENCE | **KEEP** | Swiss Ephemeris chart states for all 36 LEL events |
| `SOURCES/JHORA_TRANSCRIPTION_v8_0_SOURCE.md` | 8.0-source | SOURCE_REFERENCE | **KEEP** | Authoritative JH PDF transcription; reconciliation authority for §12.1, §12.2, §6.6–§6.8, §26 |
| `FORENSIC_DATA_v8_0_SUPPLEMENT.md` | 8.0-supp | SUPERSEDED | **ARCHIVE** | Merged into v8.0; frontmatter: "do not consume as CURRENT" |
| `LIFE_EVENT_LOG_v1_1.md` | 1.1 | SUPERSEDED | **ARCHIVE** | Replaced by v1.2; 4 date corrections + chart_states missing |
| `EXTERNAL_COMPUTATION_SPEC_v1_0.md` | 1.0 | SUPERSEDED | **ARCHIVE** | Replaced by v2.0 + self-compute; Session 3 decision record only |

### L1 Coverage Matrix

| Fact Category | Where It Lives | Coverage |
|---|---|---|
| Natal planetary positions (D1) | FORENSIC §2.1 | **Complete** |
| House cusps (Bhava Chalit) | FORENSIC §2.3 | **Complete** |
| KP system cusps + significators | FORENSIC §4 | **Complete** |
| Divisional charts D2–D60 | FORENSIC §3 | **Complete** |
| Vimshottari dasha (120yr) | FORENSIC §5.1 | **Complete** |
| Yogini dasha | FORENSIC §5.2 | **Complete** |
| Jaimini Chara dasha | FORENSIC §5.3 | **Complete** |
| Strength metrics (Shadbala) | FORENSIC §6 | **Complete** |
| Ashtakavarga | FORENSIC §7 | **Complete** |
| Chara Karakas | FORENSIC §10 | **Complete** |
| Sensitive points + Upagrahas | FORENSIC §11 | **Complete** |
| Special Lagnas (8) | FORENSIC §12.1 | **Complete** (4 errors corrected from v6.0) |
| Sahams (36 JH-auth) | FORENSIC §12.2 | **Complete** (3 new; 3 corrected from v6.0) |
| Navatara (9-tara system) | FORENSIC §14 | **Complete** |
| Panchang DNA | FORENSIC §15.1 | **Complete** |
| Aspects — Vedic Graha Drishti | FORENSIC §16.1 | **Complete** |
| Aspects — Western tight-orbs (23) | FORENSIC §16.2 | **Complete** |
| Aspects — Bhav-Madhya (14) | FORENSIC §16.3 | **Complete** |
| Yogas register | FORENSIC §26 | **Complete** (NEW in v8.0) |
| Longevity indicators | FORENSIC §24 | **Complete** (Kalachakra: 85yr) |
| Life events (36) + chart states | LIFE_EVENT_LOG_v1_2 | **Complete** |
| Sade Sati lifetime cycles | SADE_SATI_CYCLES_ALL | **Complete** |
| Daily ephemeris 1900–2100 | EPHEMERIS CSV | Inert today; Phase 14C activates |
| Eclipses 1900–2100 | ECLIPSES CSV | Inert today; Phase 14C activates |
| Retrograde stations 1900–2100 | RETROGRADES CSV | Inert today; Phase 14C activates |
| Transit computation specs | EXTERNAL_COMPUTATION_SPEC v2 | Specified; computed externally on-demand |
| Varshphal beyond 2026–2027 | — | GAP (optional per ECS v2.0 GAP.03) |
| Moola / Narayana dasha | FORENSIC §25 partial | GAP — marked `[EXTERNAL_COMPUTATION_REQUIRED]` |

### L1 SUPERSEDED Files → ARCHIVE

1. `FORENSIC_DATA_v8_0_SUPPLEMENT.md` → `99_ARCHIVE/01_FACTS_LAYER/`
   - Reason: All corrections merged into FORENSIC v8.0 (FIX_SESSION_003, 2026-04-18). Frontmatter: `status: SUPERSEDED`.
2. `LIFE_EVENT_LOG_v1_1.md` → `99_ARCHIVE/01_FACTS_LAYER/`
   - Reason: Superseded by v1.2 with Swiss Ephemeris chart_states. Frontmatter: `status: SUPERSEDED 2026-04-24`.
3. `EXTERNAL_COMPUTATION_SPEC_v1_0.md` → `99_ARCHIVE/01_FACTS_LAYER/`
   - Reason: Superseded by v2.0 + self-compute approach. Documents Session 3 decision only.

---

## Stream B — L2 Analytical Layer

### Files Audited

| Filename | Version | Status | Reference Check | Decision |
|---|---|---|---|---|
| `CLAUDE.md` | — | GOVERNANCE | No refs | **ARCHIVE** (moves with layer) |
| `DEEP_ANALYSIS_Abhisek_Mohanty_v1.md` | 1.2.1 | CURRENT | 5 SOFT refs | **ARCHIVE** |
| `MATRIX_DASHA_PERIODS.md` | 1.0 | CLOSED | 13 SOFT refs | **ARCHIVE** |
| `MATRIX_DIVISIONALS.md` | 1.0 | CLOSED | 13 SOFT refs | **ARCHIVE** |
| `MATRIX_HOUSES.md` | 1.0 | CLOSED | 12 SOFT refs | **ARCHIVE** |
| `MATRIX_PLANETS.md` | 1.0 | CLOSED | 19 SOFT refs | **ARCHIVE** |
| `MATRIX_SIGNS.md` | 1.0 | CLOSED | 17 SOFT refs | **ARCHIVE** |

**Reference classification:** All 79 hits across all files are SOFT (governance docs, registry tables, session logs, architecture diagrams). Platform code has zero file-specific imports. The `python-sidecar/rag/ingest.py` scans `02_ANALYTICAL_LAYER/` by directory only (metadata-driven); no file is imported by name.

**Blockers: NONE.** All 7 files are ARCHIVE-SAFE.

### All L2 Files → ARCHIVE

All 7 files relocate to `99_ARCHIVE/02_ANALYTICAL_LAYER/` per prior user approval to archive L2 entirely.

---

## Stream C — L2.5 Holistic Synthesis

### Files Audited

| Filename | Version | Classification | Decision |
|---|---|---|---|
| `MSR_v3_0.md` | 3.0 | CURRENT | **KEEP** |
| `UCN_v4_0.md` | 4.1 (internal) | CURRENT | **KEEP** |
| `CDLM_v1_1.md` | 1.2 (internal) | CURRENT | **KEEP** |
| `RM_v2_0.md` | 2.1 (internal) | CURRENT | **KEEP** |
| `CGM_v9_0.md` | 9.0 | CURRENT | **KEEP** |
| `RED_TEAM_L2_5_v1_0.md` | 1.0 | GOVERNANCE | **KEEP** |
| `CDLM_v1_0.md` | 1.0 | SUPERSEDED | **ARCHIVE** |

### Drift Checks

**MSR (filesystem ↔ DB):**
- DB count: 499 | .md signal count: 499 | Expected: 499 → **IN_SYNC**
- Spot-check: SIG.MSR.363 ✅ | SIG.MSR.475 ✅ | SIG.MSR.223 ✅

**CGM (filesystem ↔ rag_graph tables):**
- 234 nodes, 339 edges in `rag_graph_nodes`/`rag_graph_edges` tables
- Spot-check: PLN.SUN (163 MSR refs) ✅ | PLN.MOON (216 MSR refs) ✅ | PLN.MARS (147 MSR refs) ✅ → **IN_SYNC**

### L2.5 SUPERSEDED Files → ARCHIVE

1. `CDLM_v1_0.md` → `99_ARCHIVE/025_HOLISTIC_SYNTHESIS/`
   - Reason: Superseded by CDLM_v1_1.md (2026-04-18). No hard code references.

### Secondary Findings (Out of Scope for Phase 14.0)

| ID | Severity | Finding | Phase |
|---|---|---|---|
| SF.C.01 | MEDIUM | `025_HOLISTIC_SYNTHESIS/CLAUDE.md` lists CGM_v2_0 and MSR_v2_0 as CURRENT | Phase 14F |
| SF.C.02 | MEDIUM | `GOVERNANCE_STACK_v1_0.md` §L2.5 CGM entry is v2_0; v9_0 not registered | Phase 14F |

These are content edits — out of scope for this brief per `must_not_touch`. Flagged for Phase 14F doc-update sweep.

---

## Stream D — L3 Discovery Layer

### Files Audited

| Register | Expected Count | Actual Count | JSON Valid | Status |
|---|---|---|---|---|
| `PATTERN_REGISTER_v1_0.json` | 22 | **22** | ✅ | CURRENT |
| `RESONANCE_REGISTER_v1_0.json` | 12 | **12** | ✅ | CURRENT |
| `CONTRADICTION_REGISTER_v1_0.json` | 8 | **8** | ✅ | CURRENT |
| `CLUSTER_ATLAS_v1_0.json` | 12 | **12** | ✅ | CURRENT |

**All 4 JSON registers:** valid, entry-counts match expected, schema references verified.

**Platform references:** All 4 registers have HARD references in `platform/src/lib/bundle/composition_rules.ts` (lines 115–118). They are REQUIRED by the bundle composition system. Tests confirm: 3 test suites, 30+ references. **These files must never be archived.**

**PROMPTS directory:** `synthesis_v1_0.md` present (updated 2026-04-28). Claude and Gemini prompt suites complete with response batches.

**L3 health: EXCELLENT.** No archive candidates.

---

## Stream E — L5 Learning Layer

### Files Audited

| Subdir | Files Present | Classification | Status |
|---|---|---|---|
| `PREDICTION_LEDGER/` | 2 (jsonl + schema) | DATA + SCHEMA | **ACTIVE** — 14 seed predictions |
| `LEDGER/` | 2 (jsonl + .gitkeep) | DATA | **ACTIVE** — 545 two-pass events |
| `PROMPT_REGISTRY/` | 1 (INDEX.json) | DATA | **ACTIVE** — 10 indexed prompts |
| `SCHEMAS/` | 7 JSON validators | SCHEMA | **ACTIVE** — DO NOT ARCHIVE |
| `SIGNAL_WEIGHT_CALIBRATION/` | 1 README stub | GOVERNANCE | **STUB** (LL.1; M4 activation) |
| `GRAPH_EDGE_WEIGHT_LEARNING/` | 1 README stub | GOVERNANCE | **STUB** (LL.2; M4 activation) |
| `EMBEDDING_SPACE_ADAPTATION/` | 1 README stub | GOVERNANCE | **STUB** (LL.3; M4 activation) |
| `PROMPT_OPTIMIZATION/` | 1 README stub | GOVERNANCE | **STUB** (LL.4; M4 activation) |
| `OBSERVATIONS/` | .gitkeep | GOVERNANCE | **EMPTY** (M4 accumulator) |
| `PARAMETER_UPDATES/` | .gitkeep | GOVERNANCE | **EMPTY** (M4 Bayesian updates) |

### Prediction Ledger Drift Check

- `.jsonl` line count: **14**
- DB `prediction_ledger` table: **TABLE_MISSING** (expected per M4 design)
- Verdict: **DB_TABLE_MISSING** — both sides in pre-activation state; no drift

**L5 health: HEALTHY.** All binding constraints met. No archive candidates.

---

## Stream F — Cross-Reference Dependency Matrix

### Platform hard-reference scan (all 11 archive candidates)

```
grep results across platform/src/ and platform/python-sidecar/ for all 11 filenames:
→ 0 hits
```

**All 11 proposed archive candidates: zero hard references in platform code.**

All doc/governance references found are SOFT (registry rows, session-log entries, architecture descriptions) — safe to archive.

### Final dependency classification

| File | Hard Refs | Soft Refs | ARCHIVE SAFE |
|---|---|---|---|
| `FORENSIC_DATA_v8_0_SUPPLEMENT.md` | 0 | 5 | ✅ YES |
| `LIFE_EVENT_LOG_v1_1.md` | 0 | 6 | ✅ YES |
| `EXTERNAL_COMPUTATION_SPEC_v1_0.md` | 0 | 5 | ✅ YES |
| `CDLM_v1_0.md` | 0 | 5 | ✅ YES |
| `02_ANALYTICAL_LAYER/CLAUDE.md` | 0 | 0 | ✅ YES |
| `02_ANALYTICAL_LAYER/DEEP_ANALYSIS_*.md` | 0 | 5 | ✅ YES |
| `02_ANALYTICAL_LAYER/MATRIX_DASHA_PERIODS.md` | 0 | 13 | ✅ YES |
| `02_ANALYTICAL_LAYER/MATRIX_DIVISIONALS.md` | 0 | 13 | ✅ YES |
| `02_ANALYTICAL_LAYER/MATRIX_HOUSES.md` | 0 | 12 | ✅ YES |
| `02_ANALYTICAL_LAYER/MATRIX_PLANETS.md` | 0 | 19 | ✅ YES |
| `02_ANALYTICAL_LAYER/MATRIX_SIGNS.md` | 0 | 17 | ✅ YES |

---

## Stream G — Coverage Matrix Synthesis

Machine-readable registry: `00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json`

### Complete proposed archive list (Stream H input)

| # | From | To | Reason |
|---|---|---|---|
| 1 | `01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md` | `99_ARCHIVE/01_FACTS_LAYER/` | SUPERSEDED — merged into v8.0 |
| 2 | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_1.md` | `99_ARCHIVE/01_FACTS_LAYER/` | SUPERSEDED — replaced by v1.2 |
| 3 | `01_FACTS_LAYER/EXTERNAL_COMPUTATION_SPEC_v1_0.md` | `99_ARCHIVE/01_FACTS_LAYER/` | SUPERSEDED — replaced by v2.0 + self-compute |
| 4 | `025_HOLISTIC_SYNTHESIS/CDLM_v1_0.md` | `99_ARCHIVE/025_HOLISTIC_SYNTHESIS/` | SUPERSEDED by CDLM_v1_1 |
| 5 | `02_ANALYTICAL_LAYER/CLAUDE.md` | `99_ARCHIVE/02_ANALYTICAL_LAYER/` | Archived with layer |
| 6 | `02_ANALYTICAL_LAYER/DEEP_ANALYSIS_Abhisek_Mohanty_v1.md` | `99_ARCHIVE/02_ANALYTICAL_LAYER/` | SUPERSEDED by L2.5 |
| 7 | `02_ANALYTICAL_LAYER/MATRIX_DASHA_PERIODS.md` | `99_ARCHIVE/02_ANALYTICAL_LAYER/` | SUPERSEDED by MSR + CDLM |
| 8 | `02_ANALYTICAL_LAYER/MATRIX_DIVISIONALS.md` | `99_ARCHIVE/02_ANALYTICAL_LAYER/` | SUPERSEDED by MSR + UCN |
| 9 | `02_ANALYTICAL_LAYER/MATRIX_HOUSES.md` | `99_ARCHIVE/02_ANALYTICAL_LAYER/` | SUPERSEDED by MSR + UCN |
| 10 | `02_ANALYTICAL_LAYER/MATRIX_PLANETS.md` | `99_ARCHIVE/02_ANALYTICAL_LAYER/` | SUPERSEDED by MSR |
| 11 | `02_ANALYTICAL_LAYER/MATRIX_SIGNS.md` | `99_ARCHIVE/02_ANALYTICAL_LATER/` | SUPERSEDED by MSR + CGM |

**All 11 verified ARCHIVE-SAFE. No hard references. No blockers.**

---

## Manifest correction required

| Entry | Current status in CAPABILITY_MANIFEST.json | Correct status |
|---|---|---|
| `01_FACTS_LAYER/EXTERNAL_COMPUTATION_SPEC_v1_0.md` | `CURRENT` | `PREDECESSOR` |

This will be corrected in Stream H.

---

## Phase 14 Dependency Map

| Phase | Depends on this inventory for |
|---|---|
| **14A** | CURRENT asset list confirmed; archive list confirmed — safe to begin |
| **14B** | rag_chunks coverage: which .md files are chunked vs. not (FORENSIC, LEL, SADE_SATI, L2.5 set) |
| **14C** | L1 CSV activation + FORENSIC v8.0 → chart_facts Postgres table |
| **14D** | LEL v1.2 + SADE_SATI_ALL → life_events + sade_sati Postgres tables |
| **14E** | MSR + CGM sync already confirmed; UCN/CDLM/RM coverage check |
| **14F** | Doc-update sweep: SF.C.01 (L2.5 CLAUDE.md), SF.C.02 (GOVERNANCE_STACK CGM entry) |
| **14G** | L3 register Postgres projection decision |

---

## Done Criteria Status

| # | Criterion | Status |
|---|---|---|
| 1 | Streams A–E: per-layer inventory completed; every file has a status decision | ✅ COMPLETE |
| 2 | Stream F: dependency matrix built; no hard references on archive list | ✅ COMPLETE — 0 hard refs |
| 3 | Stream G: `VALIDATED_ASSET_REGISTRY_v1_0.json` exists, schema-valid | ✅ COMPLETE |
| 4 | Stream H: git commit lands; archived files moved; manifest updated | ⏳ PENDING native approval |
| 5 | Report at `00_ARCHITECTURE/ASSET_INVENTORY_REPORT_v1_0.md` exists with sections per layer | ✅ THIS FILE |
| 6 | Native acceptance | ⏳ AWAITING |
| 7 | Phase 14A through 14G briefs can reference validated asset registry | ⏳ After criterion 6 |

---

*End of ASSET_INVENTORY_REPORT_v1_0.md — generated Phase 14.0, 2026-04-28*

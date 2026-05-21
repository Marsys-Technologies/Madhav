---
artifact: FILE_REGISTRY_v1_1
version: 1.1
status: SUPERSEDED
backfill_note: >
  Frontmatter relocated to top of file by governance hygiene pass following PR #111 SESSION_HALT.md AC.7.
  Original artifact/version/status block was present but below a prose SUPERSEDED banner,
  making it invisible to the frontmatter parser (regex requires --- at file start).
---

> **SUPERSEDED** — see `FILE_REGISTRY_v1_2.md` for current. Retained for lineage tracing only. Superseded 2026-04-24 at Step 5A of the Step 0→15 governance rebuild.

---
artifact: FILE_REGISTRY_v1_1.md
version: 1.1
status: SUPERSEDED by FILE_REGISTRY_v1_2.md (2026-04-24, Step 5A of the Step 0→15 governance rebuild)
superseded_by: FILE_REGISTRY_v1_2.md
date: 2026-04-23
scope: Complete registry of final/current MARSYS-JIS corpus files
supersedes: FILE_REGISTRY_v1_0.md (closed 2026-04-19; superseded 2026-04-23 at Step 5 of the Step 0→15 governance rebuild)
changelog:
  - v1.1 (2026-04-23, Step 5 of the Step 0→15 governance rebuild):
    (a) §2 (L1) — corrected LIFE_EVENT_LOG row to LEL v1_2 (file already at
        v1.2; registry row was accurate but formatting aligned).
    (b) §4 (L2.5) — corrected the MSR row from `MSR_v2_0.md` (500 signals,
        internal v2.2) to the CURRENT canonical `MSR_v3_0.md` at 499 signals
        per GROUNDING_AUDIT_v1_0 §GA.1 and per CLAUDE.md §Canonical corpus
        artifact paths. Added MSR_v2_0.md to §8 Archival. This resolves the
        GA.1 registry-discipline finding that the v1.0 registry's §4 MSR row
        was out of date relative to the CURRENT corpus.
    (c) §9 (Architecture & Governance) — added rows for the Step 0→15
        governance-rebuild artifact family produced since v1.0 registry
        publication: MACRO_PLAN_v2_0.md (CURRENT), MACRO_PLAN_v1_0.md
        (SUPERSEDED), MACRO_PLAN_CRITIQUE_v1_0.md (CLOSED),
        MACRO_PLAN_REVISION_SPEC_v1_0.md (CLOSED),
        MACRO_PLAN_REDTEAM_v1_0.md (CLOSED), STEP_LEDGER_v1_0.md (LIVE),
        STEP_BRIEFS/ (16 briefs; LIVE), GROUNDING_AUDIT_v1_0.md (CLOSED),
        NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md (LIVING),
        CONVERSATION_NAMING_CONVENTION_v1_0.md (CURRENT),
        PHASE_B_PLAN_v1_0.md v1.0.2 (CURRENT),
        PHASE_B_PLAN_v1_0_RECONCILER_PASS_v1_0.md (CLOSED).
    (d) §8 Archival — MACRO_PLAN_v1_0.md added as superseded by v2.0;
        MSR_v2_0.md added as superseded by MSR_v3_0.md; FILE_REGISTRY_v1_0.md
        self-entry added as superseded by v1.1 (this file).
    (e) No schema changes; additive + corrective only.
    (f) FILE_INDEX_v1_0.md supersession chain unchanged (FILE_INDEX_v1_0.md
        → FILE_REGISTRY_v1_0.md → FILE_REGISTRY_v1_1.md).
  - v1.0 (2026-04-19): Created as registry successor to FILE_INDEX_v1_0.md
    (Session 36, stale). Captured 75 current files + 29 archival. Now
    superseded by v1.1.
---

# MARSYS-JIS File Registry — Final Corpus (v1.1)

**Subject**: Abhisek Mohanty, b. 1984-02-05, 10:43 IST, Bhubaneswar
**Branch**: `feature/amjis-platform`
**Registry date**: 2026-04-23 (v1.1 published at Step 5 of the Step 0→15 governance rebuild; supersedes v1.0 dated 2026-04-19)

This registry lists only the **current authoritative version** of each artifact.
Superseded versions are collected in §8 (Archival). Tooling and process files are in §9–§10.

The v1.1 revision is additive + corrective relative to v1.0: the MSR row is corrected to `MSR_v3_0.md` (499 signals) per GA.1; the governance-rebuild artifact family (Macro Plan v2.0 and its lineage, Step Ledger, Step Briefs, Grounding Audit, Native Directives, Conversation Naming Convention, PHASE_B_PLAN v1.0.2) is added; superseded rows are added to §8. No schema change; no column added.

---

## §1 — L0 Source Data (JHora & Ephemeris)

*Primary computation sources. Read-only; not processed by insight-generation LLMs.*

| File | Description | Status |
|---|---|---|
| `JHora/JH 1 - AM.docx` | Jagannatha Hora export — primary natal chart set | Source |
| `JHora/JH 3 - Abhisek Mohanty.docx` | Jagannatha Hora export — divisional charts | Source |
| `JHora/JH 4 - AM.docx` | Jagannatha Hora export — supplementary (dashas, yogas, longevity) | Source |
| `01_FACTS_LAYER/ECLIPSES_1900_2100.csv` | Solar/lunar eclipse data (Swiss Ephemeris computed) | Current |
| `01_FACTS_LAYER/EPHEMERIS_MONTHLY_1900_2100.csv` | Monthly planetary ephemeris 1900–2100 | Current |
| `01_FACTS_LAYER/RETROGRADES_1900_2100.csv` | Retrograde cycles 1900–2100 | Current |
| `01_FACTS_LAYER/SADE_SATI_CYCLES_ALL.md` | Complete Sade Sati cycle register | Current |

---

## §2 — L1 Facts Layer (Authoritative Ground Truth)

*Single source of truth. DO NOT derive from any other file. DO NOT edit without native's approval.*

| File | Description | Version | Status |
|---|---|---|---|
| `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` | **Unified canonical L1 — all planet/house/lagna/saham/dasha data** | 8.0 | **CURRENT** |
| `01_FACTS_LAYER/JHORA_TRANSCRIPTION_v8_0_SOURCE.md` | Full JHora v8.0 export transcription (supporting L1) | 8.0 | Current |
| `01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md` | v8.0 supplement data (partially integrated into main v8.0 file) | 8.0 | Current |
| `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` | Dated life events + Swiss Ephemeris chart states for retrodiction | 1.2 | **CURRENT** |
| `01_FACTS_LAYER/EVENT_CHART_STATES_v1_0.md` | Planetary positions at key life-event moments (computed) | 1.0 | Current |
| `01_FACTS_LAYER/EXTERNAL_COMPUTATION_SPEC_v2_0.md` | Specification for computations requiring external tools | 2.0 | CLOSED |
| `01_FACTS_LAYER/CGP_AUDIT_v1_0.md` | Completeness Guarantee Protocol audit | 1.0 | CLOSED |

---

## §3 — L2 Analytical Layer (Derived Matrices)

*Mechanical extractions from L1. Five structured matrices covering the full chart.*

| File | Description | Status |
|---|---|---|
| `02_ANALYTICAL_LAYER/MATRIX_PLANETS.md` | All 9 planets — sign, house, nakshatra, dignity, karakas, strengths | Current |
| `02_ANALYTICAL_LAYER/MATRIX_HOUSES.md` | All 12 houses — lord, tenants, aspects received, Bhava Bala | Current |
| `02_ANALYTICAL_LAYER/MATRIX_SIGNS.md` | All 12 signs — active planets, nakshatra breakdown, domain resonance | Current |
| `02_ANALYTICAL_LAYER/MATRIX_DIVISIONALS.md` | D1–D60 divisional chart placements (all planets, all charts) | Current |
| `02_ANALYTICAL_LAYER/MATRIX_DASHA_PERIODS.md` | Vimshottari + Yogini dasha sequences with sub-period windows | Current |

---

## §4 — L2.5 Holistic Synthesis (Core Analytical Stack)

*The L2.5 stack is CLOSED at current versions. Cite these for all L3 work.*

| File | Description | Version | Status |
|---|---|---|---|
| `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` | **Unified Chart Narrative — canonical single-file mother document** (v4.1 corrections applied; merged v1.0→v4.0) | 4.1 | **CURRENT** |
| `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` | **Master Signal Register — 499 signals; canonical per CLAUDE.md §Canonical corpus artifact paths** | 3.0 | **CURRENT** |
| `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` | Cross-Domain Linkage Matrix — 9×9 domain grid (v1.2 cleanup) | 1.2 | **CURRENT** |
| `025_HOLISTIC_SYNTHESIS/RM_v2_0.md` | Resonance Map — 35 RM elements, paradoxes, temporal patterns (v2.1 cleanup) | 2.1 | **CURRENT** |
| `025_HOLISTIC_SYNTHESIS/CGM_v2_0.md` | Chart Graph Model — nodes/edges feeding MSR, CDLM, RM (rebuilt on FORENSIC_v8_0 2026-04-19; will become CGM_v9_0 after Phase B.3.5) | 2.0 | **CURRENT** |

---

## §5 — L3 Domain Reports (Nine Domains)

*Each report is an L1/L2.5-derived deep-dive into one life domain. All at v1.1+.*

| File | Domain | Version | Status |
|---|---|---|---|
| `03_DOMAIN_REPORTS/REPORT_CAREER_DHARMA_v1_1.md` | Career & Dharma | 1.1 | **CURRENT** |
| `03_DOMAIN_REPORTS/REPORT_FINANCIAL_v2_1.md` | Wealth & Finance | 2.1 | **CURRENT** |
| `03_DOMAIN_REPORTS/REPORT_HEALTH_LONGEVITY_v1_1.md` | Health & Longevity | 1.2 ¹ | **CURRENT** |
| `03_DOMAIN_REPORTS/REPORT_RELATIONSHIPS_v1_1.md` | Relationships & Partnership | 1.1 | **CURRENT** |
| `03_DOMAIN_REPORTS/REPORT_CHILDREN_v1_1.md` | Children & Creative Legacy | 1.1 | **CURRENT** |
| `03_DOMAIN_REPORTS/REPORT_SPIRITUAL_v1_1.md` | Spiritual & Moksha | 1.1 | **CURRENT** |
| `03_DOMAIN_REPORTS/REPORT_PARENTS_v1_1.md` | Parents & Ancestry | 1.1 | **CURRENT** |
| `03_DOMAIN_REPORTS/REPORT_PSYCHOLOGY_MIND_v1_1.md` | Psychology & Mind | 1.1 | **CURRENT** |
| `03_DOMAIN_REPORTS/REPORT_TRAVEL_v1_1.md` | Travel & Foreign Lands | 1.1 | **CURRENT** |

¹ Internal version 1.2 (MSR citation fix applied 2026-04-19); filename retains `v1_1` suffix — rename to `v1_2` in next file-hygiene pass.

---

## §6 — L4 Remedial Codex

*Classical remedies and prescriptions derived from the full corpus.*

| File | Description | Version | Status |
|---|---|---|---|
| `04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md` | Remedial framework, planetary remedies, spiritual prescriptions | 2.0 | **CURRENT** |
| `04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART2.md` | Domain-specific remedies, timing calendar, practical protocols | 2.0 | **CURRENT** |

---

## §7 — L5–L6 Temporal Engines & Query Interface

| File | Description | Status |
|---|---|---|
| `05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md` | Complete lifetime timeline (birth → 2060, major dasha/transit events) | Current |
| `05_TEMPORAL_ENGINES/HEATMAP_VARSHPHAL_v1_0.md` | Varshaphal (Solar Return) annual heatmap | Current |
| `06_QUERY_INTERFACE/DECISION_SUPPORT_PLAYBOOK_v1_0.md` | Decision-support framework for common life decisions | Current |
| `06_QUERY_INTERFACE/QUERY_PROMPT_LIBRARY_v1_0.md` | Ready-to-use query prompts for insight sessions | Current |
| `06_QUERY_INTERFACE/SESSION_PROTOCOL_QUESTION_TAXONOMY_v1_0.md` | Taxonomy of question types for session routing | Current |

---

## §8 — Archival (Superseded Versions)

*Preserved for lineage tracing only. Do not cite in new analysis. Do not load in insight-generation context.*

### L1 Archival
| File | Superseded by |
|---|---|
| `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v6.0_ABHISEK_MOHANTY.md` | `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` |
| `01_FACTS_LAYER/FORENSIC_DATA_v7_0_SUPPLEMENT.md` | Integrated into v8.0 |
| `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_1.md` | `LIFE_EVENT_LOG_v1_2.md` |
| `01_FACTS_LAYER/EXTERNAL_COMPUTATION_SPEC_v1_0.md` | `EXTERNAL_COMPUTATION_SPEC_v2_0.md` |

### L2 Archival
| File | Superseded by |
|---|---|
| `02_ANALYTICAL_LAYER/DEEP_ANALYSIS_Abhisek_Mohanty_v1.md` | The five MATRIX_*.md files |

### L2.5 Archival
| File | Superseded by |
|---|---|
| `025_HOLISTIC_SYNTHESIS/UCN_v1_0.md` | `UCN_v4_0.md` |
| `025_HOLISTIC_SYNTHESIS/UCN_v1_1.md` | `UCN_v4_0.md` |
| `025_HOLISTIC_SYNTHESIS/UCN_v2_0.md` | `UCN_v4_0.md` |
| `025_HOLISTIC_SYNTHESIS/UCN_v3_0.md` | `UCN_v4_0.md` |
| `025_HOLISTIC_SYNTHESIS/MSR_v1_0.md` | `MSR_v3_0.md` (via `MSR_v2_0.md`) |
| `025_HOLISTIC_SYNTHESIS/MSR_v2_0.md` | `MSR_v3_0.md` (499-signal canonical; v2.0 carried 500 signals under internal v2.2 cleanup; v3.0 is the CURRENT per CLAUDE.md §Canonical corpus artifact paths) |
| `025_HOLISTIC_SYNTHESIS/CGM_v1_0.md` | `CGM_v2_0.md` |
| `025_HOLISTIC_SYNTHESIS/CDLM_v1_0.md` | `CDLM_v1_1.md` |
| `025_HOLISTIC_SYNTHESIS/RM_v1_0.md` | `RM_v2_0.md` |
| `025_HOLISTIC_SYNTHESIS/RM_v1_1.md` | `RM_v2_0.md` |
| `025_HOLISTIC_SYNTHESIS/MASTER_SYNTHESIS_v1_0.md` | `UCN_v4_0.md` |
| `025_HOLISTIC_SYNTHESIS/RED_TEAM_L2_5_v1_0.md` | QA artifact (superseded by ongoing audits) |

### L3 Archival
| File | Superseded by |
|---|---|
| `03_DOMAIN_REPORTS/FINANCIAL_REPORT_Abhisek_Mohanty.md` | `REPORT_FINANCIAL_v2_1.md` |
| `03_DOMAIN_REPORTS/REPORT_CAREER_DHARMA_v1_0.md` | `REPORT_CAREER_DHARMA_v1_1.md` |
| `03_DOMAIN_REPORTS/REPORT_FINANCIAL_v2_0.md` | `REPORT_FINANCIAL_v2_1.md` |
| `03_DOMAIN_REPORTS/REPORT_HEALTH_LONGEVITY_v1_0.md` | `REPORT_HEALTH_LONGEVITY_v1_1.md` |
| `03_DOMAIN_REPORTS/REPORT_RELATIONSHIPS_v1_0.md` | `REPORT_RELATIONSHIPS_v1_1.md` |
| `03_DOMAIN_REPORTS/REPORT_CHILDREN_v1_0.md` | `REPORT_CHILDREN_v1_1.md` |
| `03_DOMAIN_REPORTS/REPORT_SPIRITUAL_v1_0.md` | `REPORT_SPIRITUAL_v1_1.md` |
| `03_DOMAIN_REPORTS/REPORT_PARENTS_v1_0.md` | `REPORT_PARENTS_v1_1.md` |
| `03_DOMAIN_REPORTS/REPORT_PSYCHOLOGY_MIND_v1_0.md` | `REPORT_PSYCHOLOGY_MIND_v1_1.md` |
| `03_DOMAIN_REPORTS/REPORT_TRAVEL_v1_0.md` | `REPORT_TRAVEL_v1_1.md` |
| `03_DOMAIN_REPORTS/RED_TEAM_L3_v1_0.md` | QA artifact |
| `03_DOMAIN_REPORTS/CROSS_REPORT_COHERENCE_AUDIT_v1_0.md` | QA artifact |

### L4 Archival
| File | Superseded by |
|---|---|
| `04_REMEDIAL_CODEX/REMEDIAL_CODEX_v1_0_PART1.md` | `REMEDIAL_CODEX_v2_0_PART1.md` |
| `04_REMEDIAL_CODEX/REMEDIAL_CODEX_v1_0_PART2.md` | `REMEDIAL_CODEX_v2_0_PART2.md` |

### Architecture / Governance Archival
| File | Superseded by |
|---|---|
| `00_ARCHITECTURE/FILE_INDEX_v1_0.md` | `FILE_REGISTRY_v1_0.md` (then by this file, `FILE_REGISTRY_v1_1.md`) |
| `00_ARCHITECTURE/FILE_REGISTRY_v1_0.md` | `FILE_REGISTRY_v1_1.md` (this file; self-reference — retained for registry-lineage tracing) |
| `00_ARCHITECTURE/MACRO_PLAN_v1_0.md` | `MACRO_PLAN_v2_0.md` (superseded 2026-04-23 at Step 5 of the Step 0→15 governance rebuild) |
| `00_ARCHITECTURE/FALSIFIER_REGISTRY_v1_0.md` | `FALSIFIER_REGISTRY_v1_1.md` → `FALSIFIER_REGISTRY_v2_0_EXPANSION.md` |
| `00_ARCHITECTURE/FALSIFIER_REGISTRY_v1_1.md` | `FALSIFIER_REGISTRY_v2_0_EXPANSION.md` |
| `00_ARCHITECTURE/CONTRADICTION_REGISTRY_v1_0.md` | `CONTRADICTION_REGISTRY_v1_1.md` |

---

## §9 — Architecture & Governance

*Project management files in `00_ARCHITECTURE/`. Not insight-generation data — governance and process.*

### §9.1 — Foundational architecture and registries

| File | Description |
|---|---|
| `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_1.md` | Master governing blueprint (§A–§J) — refresh to v2.2 is the Step 5A deliverable of the governance rebuild |
| `00_ARCHITECTURE/SESSION_LOG.md` | Running session history and objectives |
| `00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md` | Artifact versioning and governance rules (updated in-place; STEP_5 amendment log added 2026-04-23) |
| `00_ARCHITECTURE/FILE_REGISTRY_v1_1.md` | This registry (v1.1 — CURRENT) |
| `00_ARCHITECTURE/FALSIFIER_REGISTRY_v2_0_EXPANSION.md` | Current falsifier registry (all falsified claims) |
| `00_ARCHITECTURE/CONTRADICTION_REGISTRY_v1_1.md` | Unresolved internal contradictions |
| `00_ARCHITECTURE/AUDIT_REPORT_v1_0.md` | Data integrity audit — correction history record |
| `00_ARCHITECTURE/V8_0_RECONCILIATION_REPORT.md` | v8.0 reconciliation record (7 L1 errors corrected) |
| `00_ARCHITECTURE/DATA_INTEGRITY_AUDIT_PLAN_v1_0.md` | Audit methodology |
| `00_ARCHITECTURE/FIX_SESSION_001_COMPLETION.md` | Fix record: Jupiter placement corrections |
| `00_ARCHITECTURE/FIX_SESSION_002_COMPLETION.md` | Fix record: Special lagna/saham corrections |
| `00_ARCHITECTURE/PROJECT_WIDE_RED_TEAM_v1_0.md` | Project-level red-team findings |
| `00_ARCHITECTURE/RECONCILIATION_PLAN_v1_0.md` | Reconciliation planning record |
| `00_ARCHITECTURE/ACHARYA_ENGAGEMENT_KIT.md` | External acharya review package |
| `00_ARCHITECTURE/EXTERNAL_ACHARYA_REVIEW_INVITATION.md` | External review invitation letter |
| `00_ARCHITECTURE/MAINTENANCE_SCHEDULE_v1_0.md` | Ongoing maintenance calendar |
| `00_ARCHITECTURE/LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md` | Long-term maintenance guide |
| `00_ARCHITECTURE/PROJECT_COMPLETION_DOSSIER_v1_0.md` | Project completion milestone record |

### §9.2 — Macro-phase planning artifacts

| File | Version | Status | Role |
|---|---|---|---|
| `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` | 2.0 | **CURRENT** | Strategic arc — ten macro-phase plan (M1–M10) + Learning Layer + System Integrity Substrate + mirror discipline per ND.1. Published 2026-04-23 at Step 5 of the Step 0→15 governance rebuild. Supersedes v1.0. |
| `00_ARCHITECTURE/MACRO_PLAN_v1_0.md` | 1.0 | **SUPERSEDED** (2026-04-23) | Initial macro plan; retained for historical reference. See §8 Archival. |
| `00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md` | 1.0.2 | **CURRENT** | M2 Corpus Activation execution plan (B.0–B.10). Active work is paused during the governance rebuild per CLAUDE.md banner. |
| `00_ARCHITECTURE/PHASE_B_PLAN_v1_0_RECONCILER_PASS_v1_0.md` | 1.0 | CLOSED | Reconciler-pass record preceding PHASE_B_PLAN v1.0.2 |

### §9.3 — Governance-rebuild artifact family (Step 0 → Step 15)

| File | Status | Role |
|---|---|---|
| `00_ARCHITECTURE/GROUNDING_AUDIT_v1_0.md` | CLOSED | Baseline facts as of 2026-04-23; GA.1–GA.32 findings |
| `00_ARCHITECTURE/STEP_LEDGER_v1_0.md` | LIVE | Single source of truth for Step 0→15 rebuild status |
| `00_ARCHITECTURE/STEP_BRIEFS/` | LIVE | Per-step briefs (Step 01–15 + Step 05A); README index |
| `00_ARCHITECTURE/MACRO_PLAN_CRITIQUE_v1_0.md` | CLOSED | Step 1 deliverable — 14-dimension critique of MP v1.0 (132 in-schema + 4 out-of-schema findings) |
| `00_ARCHITECTURE/MACRO_PLAN_REVISION_SPEC_v1_0.md` | CLOSED | Step 2 deliverable — 137-finding revision spec |
| `00_ARCHITECTURE/MACRO_PLAN_REDTEAM_v1_0.md` | CLOSED | Step 4 deliverable — PASS_WITH_FIXES verdict; T.1–T.7 adversarial tests |
| `00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` | LIVING | Native-intent directive log; currently tracks ND.1 (Mirror Discipline) |
| `00_ARCHITECTURE/CONVERSATION_NAMING_CONVENTION_v1_0.md` | CURRENT | Cowork thread naming convention (`Madhav NN — <Step title>`) |

---

## §10 — Tooling & Process Artifacts

| File | Description |
|---|---|
| `audit.py` | Data integrity scanner (v2 — LLM-aware, 157 baseline error-pattern matches) |
| `verify_corpus.py` | Multi-agent corpus verifier (Opus brain + Haiku workers) |
| `data_integrity_audit_report_v1_0.md` | Latest audit output (104 matches post-cleanup) |
| `corpus_verification_report_v1_0.md` | Worker-verified findings (0 live errors confirmed) |
| `corpus_verification_report_v1_0.json` | Machine-readable verification output |
| `AGENT_BRIEF_CORPUS_CLEANUP_v1_0.md` | Agent brief for corpus cleanup task (completed) |
| `AGENT_BRIEF_CORPUS_VERIFICATION_v1_0.md` | Agent brief for comprehensive 8-layer corpus verification (MSR merge + citation graph + 24 invariants) |
| `MARSYS_JIS_BOOTSTRAP_HANDOFF.md` | Session bootstrap document |
| `SESSION_RESUME_PROMPT.md` | Session resume context prompt |
| `.tools/build_lel_v1_2.py` | Life Event Log builder |
| `.tools/compute_event_chart_states.py` | Event chart state computation |
| `.tools/compute_jaimini_drishti.py` | Jaimini drishti computation |
| `.tools/compute_v7_additions.py` | v7.0 additions computation |
| `.tools/generate_eclipses.py` | Eclipse data generator |
| `.tools/generate_ephemeris.py` | Ephemeris data generator |
| `.tools/generate_retrogrades.py` | Retrograde cycle generator |
| `.tools/generate_sade_sati.py` | Sade Sati cycle generator |

---

## §11 — v1.0 → v1.1 Diff Summary (for audit tracing)

### Rows corrected
- §4 (L2.5): MSR row — was `025_HOLISTIC_SYNTHESIS/MSR_v2_0.md` (500 signals; internal v2.2); now `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` (499 signals). Rationale: CLAUDE.md §Canonical corpus artifact paths and GROUNDING_AUDIT §GA.1 both name `MSR_v3_0.md` as CURRENT; the v1.0 registry row was stale.

### Rows added to §9 (Architecture & Governance)
- §9.2: `MACRO_PLAN_v2_0.md` (CURRENT); `MACRO_PLAN_v1_0.md` (SUPERSEDED); `PHASE_B_PLAN_v1_0.md` (explicit v1.0.2 annotation); `PHASE_B_PLAN_v1_0_RECONCILER_PASS_v1_0.md`.
- §9.3: `GROUNDING_AUDIT_v1_0.md`; `STEP_LEDGER_v1_0.md`; `STEP_BRIEFS/`; `MACRO_PLAN_CRITIQUE_v1_0.md`; `MACRO_PLAN_REVISION_SPEC_v1_0.md`; `MACRO_PLAN_REDTEAM_v1_0.md`; `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md`; `CONVERSATION_NAMING_CONVENTION_v1_0.md`.

### Rows added to §8 (Archival)
- L2.5: `MSR_v2_0.md` → `MSR_v3_0.md`.
- Architecture / Governance: `FILE_REGISTRY_v1_0.md` → this file; `MACRO_PLAN_v1_0.md` → `MACRO_PLAN_v2_0.md`.

### Schema
No change. Additive + corrective revision only; no column added, no row format changed, no semantics altered.

---

## Summary Count

| Category | Current Files | Archival Files |
|---|---|---|
| L0 Source (JHora + CSV) | 7 | — |
| L1 Facts Layer | 7 | 4 |
| L2 Analytical Matrices | 5 | 1 |
| L2.5 Holistic Synthesis | 5 | 11 |
| L3 Domain Reports | 9 | 12 |
| L4 Remedial Codex | 2 | 2 |
| L5–L6 Temporal/Query | 5 | — |
| Architecture & Governance (§9.1) | 17 | 6 |
| Macro-phase planning (§9.2) | 3 (v2.0 MP + v1.0.2 PBP + reconciler-pass closed) | 1 (MP v1.0) |
| Governance rebuild (§9.3) | 8 (Grounding + Step Ledger + Step Briefs + Critique + Spec + Red-team + Native Directives + Conversation Naming) | — |
| Tooling & Process | 18 | — |
| **Total** | **86** | **37** |

---

*Registry v1.1 produced 2026-04-23 at Step 5 of the Step 0→15 governance rebuild. Supersedes v1.0 dated 2026-04-19. Update when new artifacts are added or versions superseded.*

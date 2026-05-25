---
canonical_id: DATA_ASSET_AUDIT
version: 1.1
status: CURRENT
authored: 2026-05-25
amended: 2026-05-25 (v1.1 — folded in follow-up Q1–Q8 findings; "does not cover" section retired — all items now inside main body)
author: Claude (Cowork session)
purpose: >
  Comprehensive audit of all MARSYS-JIS data assets — their versions on disk,
  pipeline references, storage locations (local / GCS / DB), full MSR dependency
  chain, chart_facts enhancement surface, GCS issues, unapplied migrations,
  MSR grounding disambiguation, MEAN_NODE rebuild status, and a prioritised
  reconciliation plan. Authoritative record for the data-hygiene workstream
  opened 2026-05-25.
---

# MARSYS-JIS Data Asset Audit & Reconciliation Plan v1.1

---

## Executive Summary

**Total findings: 19 across 5 severity levels.**

The audit confirms that no canonical data asset other than MSR has integrity issues. MSR is the single problematic asset — but it is broken across six pipeline surfaces, its EXPECTED_COUNT gate is frozen at v3.1/514 signals even though v5.0 has 573, and 571 of 573 signals lack B.3 Derivation-Ledger grounding (FORENSIC/LEL L1 citations). The MSR grounding gap is the primary prerequisite blocker for M6.

Additional findings: the MEAN_NODE Rahu rebuild is only code-complete, not data-complete; two migrations (116, 117) are unapplied in production with migration 117 blocking acharya-tier API key issuance; the CLAUDE.md §E LEL entry count is stale; and the Gemini mirror pairs MP.1/MP.2/MP.9 have significant structural drift.

---

## Part 1 — Canonical Asset Inventory

| canonical_id | Declared path | Declared version | Files on disk | Status |
|---|---|---|---|---|
| FORENSIC | `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` | 8.0 | v8_0 only — 97,824 B | CLEAN |
| LEL | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` | 1.6 (CLAUDE.md §D) / **1.7 (file frontmatter — authoritative)** | v1_2 filename only (in-place amendments to v1.7) — 146,253 B | **MINOR STALE: CLAUDE.md §D and §E say v1.6 and "36 events", file is v1.7 with 57 events** |
| **MSR** | `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` | 5.0 | **v3_0 (877,728 B) + v4_0 (907,111 B) + v5_0 (939,442 B) — all three live in synthesis dir** | **ORPHAN VERSIONS PRESENT — plus pipeline frozen at v3.1** |
| UCN | `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` | 4.1 (in-place) | v4_0 only — 198,254 B | CLEAN |
| CDLM | `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` | 1.3 (in-place) | v1_1 only — 88,743 B | CLEAN |
| RM | `025_HOLISTIC_SYNTHESIS/RM_v2_0.md` | 2.2 (in-place) | v2_0 only — 47,092 B | CLEAN |
| CGM | `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` | 9.1 (manifest) | v9_0 only — 78,930 B | CLEAN (filename/manifest asymmetry expected per convention) |
| chart_facts | DB-only — `chart_facts` table | 2,717 DB rows; 666 YAML source facts (v1.1 YAML) | YAML source in `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` | CLEAN |
| panchanga_daily | DB-only | 73,414 rows, 5 JSONB enrichment cols | No local file; Python-engine-computed | CLEAN |
| classical_texts | DB — 4,589 chunks, 420 attributions | N/A (text_key-based identity, no version column) | Source JSONL in `00_ARCHITECTURE/SOURCE_DATA/classical_texts/` | CLEAN |

### LEL entry count — authoritative numbers (v1.7)

The file frontmatter at v1.7 (2026-05-25 state) declares:

- **57 discrete events** (56 point events + EVT.CURRENT.01)
- **5 period summaries** (PERIOD.2007, 2012_2013, 2016, 2018_2021, 2022_2024)
- **8 chronic patterns** (PATTERN.STAMMER.01 through PATTERN.MANASA_PUJA.01)
- **2 prediction subsection entries** (PRED.M3D.HOLDOUT.001/002 — migrated to prediction_ledger.jsonl)

CLAUDE.md §D says "v1.6" and §E says "36 events + 5 period summaries + 6 chronic patterns" — those figures are from the v1.3 era and are stale. The file is authoritative. One archived predecessor exists at `99_ARCHIVE/01_FACTS_LAYER/LIFE_EVENT_LOG_v1_1.md` (correct archival). No competing active version.

**Action required:** Update CLAUDE.md §E LEL bullet and §D table to v1.7 / 57 events / 8 patterns at the next CLAUDE.md touch.

### Note on GCS filename conventions for in-place versioned assets

LEL, UCN, CDLM, and RM all use in-place amendment versioning (filename carries artifact_id, not internal version). The GCS paths `L1/facts/LIFE_EVENT_LOG_v1_2.md`, `L2_5/UCN_v4_0.md`, etc. are therefore correct by convention — they match the artifact_id in the filename, not the internal version. These are not GCS layout errors.

### Note on "MCP Transformation v3.1" for classical texts

The label "v3.1" attached to classical texts in CLAUDE.md §E refers to the MCP **server architecture generation** being rebuilt (v3.1 Pure-MCP Rebuild), not to any version of the classical texts themselves. The `classical_texts`, `classical_chunks`, and `classical_attributions` tables have no `version` column — versioning is by `text_key` (e.g. `bphs`, `phaladeepika`) + re-bootstrap. "v3.1" in that context is the build that loaded them, not a property of the data. No naming inconsistency exists at the schema level.

---

## Part 2 — Pipeline Reference Findings

### Six surfaces; five have stale MSR path

**Surface A: Python build pipeline**

| File | Hardcoded path | Should be | Status |
|---|---|---|---|
| `platform/python-sidecar/pipeline/main.py:88` | `MSR_v3_0.md` | `MSR_v5_0.md` | **STALE** |
| `platform/python-sidecar/pipeline/extractors/msr_extractor.py:15` | `MSR_v3_0.md` | `MSR_v5_0.md` | **STALE** |
| `platform/python-sidecar/pipeline/extractors/msr_extractor.py:20` | `EXPECTED_COUNT = 514` | `EXPECTED_COUNT = 573` | **STALE COUNT** |
| `platform/python-sidecar/pipeline/writers/msr_signals_writer.py:20` | `EXPECTED_COUNT = 514` | `EXPECTED_COUNT = 573` | **STALE COUNT — gate will reject v5.0 load** |
| `platform/python-sidecar/pipeline/writers/msr_signals_writer.py` | `SOURCE_FILE = "MSR_v3_0.md"` | `MSR_v5_0.md` | **STALE** |
| `platform/python-sidecar/rag/chunkers/msr_signal.py:26` | `SOURCE_FILE = "MSR_v3_0.md"` | `MSR_v5_0.md` | **STALE** |
| `platform/python-sidecar/rag/chunkers/msr_signal.py` | `SOURCE_VERSION = "3.1"` | `"5.0"` | **STALE** |
| All other pipeline entries | Correct | — | OK |

**Surface B: `read_asset` MCP API endpoint**

| File | Key | Current | Should be | Status |
|---|---|---|---|---|
| `platform/src/app/api/mcp/asset/route.ts:50` | `SAFE_ASSET_MAP['MSR']` | `MSR_v3_0.md` | `MSR_v5_0.md` | **BLOCKING** |

**Surface C: ICR confirm endpoint**

| File | Variable | Current | Should be | Status |
|---|---|---|---|---|
| `platform/src/app/api/icr/confirm/route.ts:24` | `MSR_PATH` | `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` | `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` | **BLOCKING** |

**Surface D: TypeScript ETL (correct)**

| File | Path | Status |
|---|---|---|
| `platform/src/scripts/etl/msr_etl.ts:10` | `MSR_v5_0.md` | CORRECT |
| `platform/src/scripts/etl/msr_parser.ts:209` | stamps `source_file: 'MSR_v5_0.md'` | CORRECT |
| `platform/src/scripts/etl/__tests__/msr_parser.test.ts:5` | absolute path to `MSR_v3_0.md` for fixture | **STALE test fixture** |

**Surface E: governance overrides**

| File | Field | Current | Should be | Status |
|---|---|---|---|---|
| `00_ARCHITECTURE/manifest_overrides.yaml` | `MP.5.path_pattern` | `"MSR_v3_0"` | `"MSR_v5_0"` | **Causes drift_detector H.3.1 false-positive every run** |

**Surface F: `amjis-mcp` sidecar `read_asset` tool** — inherits Surface B via `callPlatformAsset()`. Fixing B fixes F.

---

## Part 3 — MSR Signal Dependency Chain

This is the most architecturally significant section. Every asset downstream of MSR signals is potentially frozen at the v3.1/514-signal state.

### Dependency map

```
MSR_v5_0.md (573 signals) — on disk, in TypeScript ETL
    │
    ├─► msr_etl.ts (TS ETL — reads v5, writes to msr_signals migration-009 table)
    │       └─► msr_signals (migration 009, public.msr_signals)
    │               ├─► contradiction_register_writer.py  ← reads from here
    │               ├─► cluster_register_writer.py        ← reads from here
    │               ├─► pattern_register_writer.py        ← reads from here
    │               ├─► refit.py (embeddings)             ← reads from here
    │               └─► MCP holistic_bundle query_msr_signals tool  ← reads from here
    │
    ├─► msr_extractor.py (Python build pipeline — reads MSR_v3_0.md, EXPECTED_COUNT=514)
    │       └─► l25_msr_signals / l25_msr_signals_staging (migration 018)
    │               └─► school_convergence_index (migration 079, expects 543 signals = v4.0 count)
    │
    ├─► msr_signal.py chunker (reads MSR_v3_0.md, SOURCE_VERSION="3.1")
    │       └─► rag_chunks (canonical_id='MSR', reflects v3.1 514-signal corpus)
    │
    └─► CGM_v9_0.md / UCN_v4_0.md / CDLM_v1_1.md
            └─► inline MSR signal ID cross-references (e.g. SIG.MSR.500–502 in CGM)
                    └─► NO automated validation that cited signal IDs exist in DB
```

### Key integrity finding: 59 signals (SIG.MSR.515–573) are missing from all pipeline tables

MSR v5.0 has 573 signals. The `msr_signals_writer.py` EXPECTED_COUNT gate is 514 (v3.1). The `l25_msr_signals` table was populated from v3.1 (514 signals). The `rag_chunks` MSR section was chunked from v3.1. The 59 signals added in v4.0 and v5.0 (the Nadi/BNN group SIG.MSR.515–543 and the Yogini/Tajaka group SIG.MSR.544–573) are not indexed in any pipeline table.

The `school_convergence_index` migration comment declares "543 signals × 7 schools = 3801 rows" — this is the v4.0 count (543), not v5.0 (573). So `school_convergence_index` is also frozen at v4.0.

### What is correctly in sync

The `msr_signals` (migration 009) table is queried by `query_msr_signals` (MCP holistic_bundle path). This table is written by the TypeScript ETL `msr_etl.ts`, which correctly reads MSR v5.0. **However**, it is not confirmed whether `msr_etl.ts` was executed after v5.0 was authored. This must be verified by a DB query (see R-4 in the reconciliation plan).

### CGM/UCN/CDLM cross-reference integrity

All three synthesis assets cite specific MSR signal IDs in their markdown text (e.g. CGM references SIG.MSR.500–502; UCN references MSR.413, MSR.391; CDLM has `msr_anchors:` lists up to MSR.413). These are all valid signal IDs that exist in MSR v5.0. The cross-references are correct. No automated validation exists between these markdown citations and the DB tables — that is a V1.3 audit item, not a current blocker.

---

## Part 4 — chart_facts: Current State and Enhancement Surface

### Current state

- YAML source: `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` at schema v1.1
- YAML fact count: **666 facts** (direct grep of `fact_id:` lines)
- DB row count: **2,717 rows** in `chart_facts` table (MCP Transformation broader extraction pass)
- The 2,717 > 666 discrepancy is because the MCP-T extraction was a separate, broader pass from FORENSIC v8.0 that generated additional structured facts beyond what the v1.1 YAML covers
- Categories added at v1.1 (per changelog): cusp CDL.* rows, D9 12th-stellium, Bhavabala (BVB.FORENSIC.H01–H12), Chesta motion (CHS.MOTION.*), aspect ledgers (ASP.W.* + ASP.BM.* + ASP.TRN.*), Sade Sati transit (TRS.SS.*), Mercury vargottama

### Enhancement surface

The primary gap-finding method is to diff FORENSIC v8.0 section headings against the YAML categories and the 27 MCP-T categories. Sections not yet fully extracted include:
- **Narayana Dasha** (FORENSIC has it; chart_facts coverage unclear)
- **Jaimini Karakas** (MCP-T may have loaded; YAML v1.1 doesn't include it)
- **Tajaka Varshphala** (MCP-T v3.3 loaded this — verify it is in the 2,717 rows)
- **Upagraha positions** (MCP-T v3.3 loaded; verify in 2,717 rows)
- **KP sublord assignments** (MCP-T v3.3 loaded; verify in 2,717 rows)
- **School-specific interpretations** (multi_school_bundle context) — not a chart_facts item per design
- **Predicted vs observed event cross-references** — pending LEL-MSR linkage work (M6 scope)

### Verdict

chart_facts is CLEAN as a data store. The 2,717 rows from MCP-T represent the broadest extraction yet. Enhancement opportunities exist (Narayana Dasha, fuller Jaimini, any FORENSIC section not covered in 27 MCP-T categories) but these are M5-B/M6 scope items, not reconciliation blockers.

---

## Part 5 — Storage Split Matrix

| Asset | Local disk | GCS `gs://madhav-marsys-sources` | DB | Issues |
|---|---|---|---|---|
| FORENSIC v8 | ✅ | ✅ `L1/facts/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` | — | None |
| LEL v1.7 | ✅ | ✅ `L1/facts/LIFE_EVENT_LOG_v1_2.md` (filename = artifact_id, correct) | ✅ `life_events`, `sade_sati_phases` (migration 017) | None |
| **MSR v3** | ✅ (should be archived) | ✅ `L2_5/MSR_v3_0.md` (pipeline target) | ✅ `l25_msr_signals` + `rag_chunks` both populated from v3 | Triple stale — all three surfaces reference superseded version |
| **MSR v4** | ✅ (should be archived) | ✅ `L2_5/MSR_v4_0.md` (uploaded M8-F-S1) | — never extracted | Middle orphan — no DB, no pipeline |
| **MSR v5** | ✅ | ⚠️ GCS_LAYOUT body not updated; trailing note says v5 exists at `L2_5/MSR_v5_0.md` but unconfirmed | ⚠️ `msr_signals` (migration 009) — populated by TS ETL if run; unconfirmed | **Uncertain state** |
| UCN v4.1 | ✅ | ✅ `L2_5/UCN_v4_0.md` | ✅ `l25_ucn_sections` + RAG chunks | None |
| CDLM v1.3 | ✅ | ✅ `L2_5/CDLM_v1_1.md` | ✅ `l25_cdlm_links` + RAG chunks | None |
| CGM v9.1 | ✅ | ✅ `L2_5/CGM_v9_0.md` | ✅ `l25_cgm_nodes/edges` + RAG chunks | None |
| RM v2.2 | ✅ | ✅ `L2_5/RM_v2_0.md` | ✅ `l25_rm_resonances` + RAG chunks | None |
| chart_facts | ✅ YAML source | ✅ `L1/facts/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` | ✅ 2,717 rows | None |
| panchanga_daily | — (engine-computed) | — | ✅ 73,414 rows, 5 JSONB cols | None |
| ephemeris_daily | ✅ 3 CSV source files in `01_FACTS_LAYER/` | ⚠️ GCS_LAYOUT comment says "coverage gap not yet generated" but files exist locally | ✅ `ephemeris_daily`, `eclipses`, `retrogrades` — **populated by pre-MEAN_NODE-fix bootstrap** | Rahu/Ketu values may be TRUE_NODE not MEAN_NODE — see MEAN_NODE section |
| classical texts | Source JSONL in `00_ARCHITECTURE/SOURCE_DATA/classical_texts/` | ✅ `L8/classical_texts/tier1-tier3/*.jsonl` | ✅ 4,589 chunks, 420 attributions | None |

### Why local copies exist — and the GCS-first principle

Every L1 and L2.5 canonical MD file lives locally as the **source of truth**. GCS mirrors them for (a) cold-storage safety and (b) as the input URI for the Python build pipeline which runs in a Cloud Run environment without local repo access. The local copy is the authoritative version that Claude and governance tools read; GCS is the pipeline-accessible replica.

**The principle going forward:** Whenever a canonical MD file is updated (e.g. MSR v5.0), the GCS upload must be performed as part of the same session close, and `GCS_LAYOUT_v1_0.md` must be updated in the same commit. This did not happen for MSR v4.0 or v5.0, which is how the divergence accumulated. After the current reconciliation, this should be enforced in the SESSION_CLOSE_TEMPLATE.

---

## Part 6 — GCS Layout Issues (enumerated precisely)

### GCS Issue 1: MSR primary entry stale

`GCS_LAYOUT_v1_0.md` authoritative layout table declares `canonical_id: MSR → L2_5/MSR_v3_0.md`. A trailing annotation says MSR_v5_0.md was added at M9-A-S1 but the table was never updated. The layout body should show `MSR_v5_0.md` as primary and `MSR_v3_0.md` as superseded.

### GCS Issue 2: Ephemeris note stale

`GCS_LAYOUT_v1_0.md` notes "ephemeris CSV files: coverage gap not yet generated" for the `L1/ephemeris/` prefix. Three CSV source files now exist locally in `01_FACTS_LAYER/` (ephemeris_daily, eclipses, retrogrades source data). Their GCS upload status is unknown. If they were uploaded during the Phase 4 ephemeris bootstrap, the layout comment is simply stale. If they were not uploaded to GCS, the Python build pipeline cannot read them from Cloud Run.

Both GCS issues are resolved by a single `GCS_LAYOUT_v1_0.md` v1.0 → v1.1 amendment (reconciliation action R-6).

---

## Part 7 — Orphaned / Superseded Files

| File | Size | Status | Action |
|---|---|---|---|
| `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` | 877,728 B | SUPERSEDED | Archive to `99_ARCHIVE/025_HOLISTIC_SYNTHESIS/` (dir must be created) |
| `025_HOLISTIC_SYNTHESIS/MSR_v4_0.md` | 907,111 B | SUPERSEDED | Archive to `99_ARCHIVE/025_HOLISTIC_SYNTHESIS/` |
| `025_HOLISTIC_SYNTHESIS/RED_TEAM_L2_5_v1_0.md` | 25,822 B | Misplaced governance doc (belongs in `00_ARCHITECTURE/`) | Move to `00_ARCHITECTURE/` |
| `00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml` | 1,931 B | DIS.013 RESOLVED; PROPOSED copy is stale | Delete (RESOLVED copy is authoritative) |

---

## Part 8 — Database Migration State

### Confirmed applied to production

Migrations 001–061 (all core schema), 069 (panchanga enrichment), 070–082 (MCP Transformation batch — confirmed by workstream close, not individually in ledger), 110–114 (R9 Projects/semantic search/tool flow).

### PENDING — two unapplied migrations

| Migration | What it adds | Impact of absence |
|---|---|---|
| `116_trace_mcp_tool_column.sql` | `query_trace_steps.mcp_tool TEXT` column; backfills from `data_summary->>'mcp_tool'` | Lifecycle tab `mcp_tool` lookup returns no results; tool-call attribution in Observatory incomplete |
| `117_audience_tier_acharya_enum.sql` | Adds `'acharya'` to `mcp_api_keys.audience_tier` CHECK constraint | **Acharya-tier MCP API keys cannot be issued in production** — the INSERT CHECK will reject the value |

Both migrations are authored, idempotent, and safe to apply at any time. They were not applied during MCP Transformation because the workstream close pre-dated the operator DB session window. Apply via:
```bash
psql "$DATABASE_URL" -f platform/migrations/116_trace_mcp_tool_column.sql
psql "$DATABASE_URL" -f platform/migrations/117_audience_tier_acharya_enum.sql
```
Then append confirmed entries to `MIGRATIONS_APPLIED_LOG.md`.

### Migration ledger gap: 072–082

MCP Transformation migrations 072–082 (supabase) are confirmed applied (workstream close record) but not individually logged in `MIGRATIONS_APPLIED_LOG.md`. Backfill needed for audit completeness (reconciliation action R-12).

---

## Part 9 — Mirror Pair Status

| Pair | Claude-side | Gemini-side | Status |
|---|---|---|---|
| MP.1 | `CLAUDE.md` v4.2 — M5 active, 15 workstreams | `.geminirules` — M9 phase pointer, 7 workstreams listed in §E | **DRIFT — 8 workstreams unsynced; phase pointer wrong** |
| MP.2 | `CURRENT_STATE_v1_0.md` — M4-D-S1 last session | `.gemini/project_state.md` — R11G-S7 close, M9-era state blocks | **DRIFT — multi-era misalignment** |
| MP.3 | `MACRO_PLAN_v2_0.md` | Compact summary in `.geminirules` | LIKELY CLEAN (both v2.0) |
| MP.4 | Phase plan SUPERSEDED-AS-COMPLETE | Phase pointer in `.geminirules` | DECLARED ASYMMETRY — expected |
| MP.5 | `CAPABILITY_MANIFEST.json` (MSR → v5) | `.geminirules` line 142 (MSR → v5) — CORRECT | CLEAN at mirror level; but `manifest_overrides.yaml` MP.5 enforcement_rule still says v3 — a governance tool contradiction |
| MP.6 | `GOVERNANCE_STACK_v1_0.md` | null (Claude-only) | CLEAN |
| MP.7 | `SESSION_LOG.md` | null (Claude-only) | CLEAN |
| MP.8 | `PROJECT_ARCHITECTURE_v2_2.md` | Compact block in `.geminirules` | LIKELY CLEAN |
| MP.9 | `OBSERVATORY_PLAN_v1_0.md` (COMPLETE) | §E Phase O listed as COMPLETE, but §E only has 7 workstreams total | DRIFT — §E workstream count |

---

## Part 10 — MSR Signal Grounding: Disambiguated

There are two distinct definitions of "grounded" in use and they are both correct in their own domain. They must not be conflated.

### Definition 1: Classical source grounding (573/573 — COMPLETE)

Every MSR signal has a `classical_source` field pointing to a specific classical text, chapter, and shloka (e.g. "BPHS Ch.26 Sl.19"). This is what the MCP Transformation v3.2 grounding pass delivered. This grounding links signals to the classical canon.

### Definition 2: B.3 Derivation-Ledger grounding — L1 FORENSIC/LEL citations (2/573 — OPEN)

Principle B.3 mandates that every L2.5+ claim carries a `DERIVATION_LEDGER` entry listing the specific L1 fact IDs it consumes. A scan of `MSR_v5_0.md` found only 2 signals with `derivation_ledger` / `l1_sources` blocks (at lines 8806 and 9044). The remaining 571 signals have classical citations but no explicit anchor to a FORENSIC line item or LEL event.

V1_3_AUDIT_QUEUE CF.V13.1 (carry-forward item, severity HIGH) captures this: "MSR signal-grounding gap — 419/573 signals lack explicit FORENSIC/LEL citations." (The gap is even wider than CF.V13.1 states — direct file scan suggests 571/573, though CF.V13.1 may have used a looser definition that counted body-text references as implicit citations.)

**This is the primary prerequisite blocker for M6 Prospective Testing.** Predictions must trace to L1-grounded signals per the Learning Layer discipline (LL.8). A prediction derived from a signal with no L1 anchor cannot be audited or falsified against lived reality.

**Required work:** 5–8 dedicated sessions to backfill `derivation_ledger` entries across the 419–571 ungrounded signals. This is M5-A scope per `PHASE_M5_PLAN_v1_0.md §3`.

---

## Part 11 — MEAN_NODE Ephemeris Rebuild

### Code state: DONE
`bootstrap_ephemeris.py` line 252 has `swe.MEAN_NODE` (corrected from TRUE_NODE). Migration 059 (`ephemeris_derived_columns.sql`) is applied. Phase 4B brief is `AUTHORED_READY_TO_EXECUTE`.

### Production data state: UNCONFIRMED / LIKELY NOT DONE

The Phase 4B brief status `AUTHORED_READY_TO_EXECUTE` means the runbook was authored but the production 657K-row data rebuild was not completed as a formal session. The live `ephemeris_daily` table was bootstrapped before the MEAN_NODE fix was committed. The `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md` artifact — which would exist if Phase 4B had been executed — was not found in the project tree.

**Impact:** Rahu/Ketu longitudes in `ephemeris_daily` were computed with `swe.TRUE_NODE`. TRUE_NODE oscillates ±1.5° around MEAN_NODE with a period of ~173 days. At any given date, the Rahu longitude could be off by up to ~1.5 degrees. This propagates to nakshatra/pada assignments near sign boundaries (most vulnerable: late Pisces/early Aries boundary where Rahu frequently transits). Transit predictions involving Rahu/Ketu derived from `query_ephemeris` could be off by one nakshatra pada.

**How to confirm:** Run:
```sql
SELECT build_id, created_at FROM build_manifests
WHERE description ILIKE '%ephemeris%'
ORDER BY created_at DESC LIMIT 5;
```
Compare `created_at` of the last ephemeris build against the git commit date of the MEAN_NODE fix in `bootstrap_ephemeris.py`. If build predates the code fix, a rebuild is needed.

**Rebuild scope:** ~4–6 hours wall-clock (657K-row write to `ephemeris_daily`). This is a human operator gate. The runbook at `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md` (to be authored in Phase 4B execution) provides the exact commands.

---

## Part 12 — Prioritised Reconciliation Plan

### TIER 1: BLOCKING — Fix immediately (single PR, deploy same day)

**R-1. Fix `read_asset` MCP endpoint — MSR path**
- File: `platform/src/app/api/mcp/asset/route.ts` line ~50
- Change: `'MSR': 'MSR_v3_0.md'` → `'MSR': 'MSR_v5_0.md'`
- Test: call `read_asset({canonical_id:"MSR"})` via MCP; verify ~573 signals in response
- Impact: LLM immediately reads full 573-signal MSR corpus via MCP

**R-2. Fix ICR confirm endpoint — MSR path**
- File: `platform/src/app/api/icr/confirm/route.ts` line ~24
- Change: `const MSR_PATH = '025_HOLISTIC_SYNTHESIS/MSR_v3_0.md'` → `MSR_v5_0.md`
- Impact: ICR patches now applied to live file

### TIER 2: HIGH — Fix before any pipeline re-run or DB rebuild

**R-3. Fix Python build pipeline MSR references (all 7 hardcoded locations)**
- `pipeline/main.py:88` — path
- `pipeline/extractors/msr_extractor.py:15` — SOURCE_FILE
- `pipeline/extractors/msr_extractor.py:20` — EXPECTED_COUNT: 514 → 573
- `pipeline/writers/msr_signals_writer.py:20` — EXPECTED_COUNT: 514 → 573
- `pipeline/writers/msr_signals_writer.py` — SOURCE_FILE: v3_0 → v5_0
- `rag/chunkers/msr_signal.py:26` — SOURCE_FILE + SOURCE_VERSION: "3.1" → "5.0"
- `pipeline/ingest_msr.py` (docstring)
- Test: dry-run pipeline; verify 573 signals extracted without EXPECTED_COUNT gate rejection
- Deploy: Python sidecar rebuild

**R-4. Confirm DB `msr_signals` source version (human operator action)**
```sql
SELECT source_file, COUNT(*) FROM msr_signals GROUP BY source_file;
SELECT source_file, COUNT(*) FROM l25_msr_signals GROUP BY source_file;
```
- If `msr_signals` (migration 009) shows v3: run `msr_etl.ts` to re-populate from v5
- If `l25_msr_signals` (migration 018) shows 514 rows: re-run Python pipeline after R-3 is deployed
- Both tables must show 573 rows sourced from `MSR_v5_0.md` after this action
- Also check `school_signal_coverage` — migration comment says 543 (v4 count); may need re-population at 573

**R-5. Create `99_ARCHIVE/` and move superseded MSR versions**
```bash
mkdir -p 025_HOLISTIC_SYNTHESIS/99_ARCHIVE/
# OR create at project root:
mkdir -p 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/
git mv 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
git mv 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v4_0.md
git commit -m "archive: move MSR v3 and v4 to 99_ARCHIVE per MSR-HYGIENE-S1 [governance hygiene]"
```
GCS objects `L2_5/MSR_v3_0.md` and `L2_5/MSR_v4_0.md`: retain for now (GCS deletion is irreversible; human decision after R-4 confirms v5 DB state is correct).

**R-6. Update GCS_LAYOUT_v1_0.md v1.0 → v1.1**
- MSR table entry: mark `L2_5/MSR_v3_0.md` as SUPERSEDED; set `L2_5/MSR_v5_0.md` as primary
- Ephemeris note: update from "coverage gap not yet generated" to document actual local file state and GCS upload status
- Confirm whether ephemeris CSVs are on GCS; if not, document the operator step to upload them
- Version bump + changelog entry

### TIER 3: MEDIUM — Fix within current governance cycle

**R-7. Fix `manifest_overrides.yaml` MP.5 path_pattern**
- `path_pattern: "MSR_v3_0"` → `"MSR_v5_0"`
- Also update `enforcement_rule` text
- Fixes drift_detector H.3.1 false-positive

**R-8. Fix stale test fixture in `msr_parser.test.ts`**
- Line 5: update absolute path from `MSR_v3_0.md` to `MSR_v5_0.md`
- Line 45 assertion already says `'MSR_v5_0.md'` — makes the test internally consistent

**R-9. Apply migrations 116 and 117 to production (human operator gate)**
```bash
psql "$DATABASE_URL" -f platform/migrations/116_trace_mcp_tool_column.sql
psql "$DATABASE_URL" -f platform/migrations/117_audience_tier_acharya_enum.sql
```
Then append rows to `MIGRATIONS_APPLIED_LOG.md`.

**R-10. Sync MP.1/MP.2/MP.9 mirror pairs (Gemini)**
Update `.geminirules`:
- §C item #5: phase pointer → `PHASE_M5_PLAN_v1_0.md` (M5 active)
- §E: add 8 missing workstreams (R11.F, R11.G, MCP Transformation, R10, R11v2, Phase 4C, M5 Coverage, MCP sidecar — all as COMPLETE)

Update `.gemini/project_state.md`:
- §F macro-phase: M9 → M5 active
- Add close records for all 8 missing workstreams

**R-11. Update CLAUDE.md §E LEL bullet and §D table**
- §E: "36 events + 5 period summaries + 6 chronic patterns" → "57 events + 5 period summaries + 8 chronic patterns (v1.7)"
- §D: LEL version "1.6" → "1.7"

### TIER 4: LOW / COSMETIC

**R-12. Backfill `MIGRATIONS_APPLIED_LOG.md` for migrations 072–082**
Add confirmed entries for each MCP Transformation migration (072–082) with `confirmed_method: inferred_from_workstream_close`.

**R-13. Delete stale PROPOSED conflict patch**
```bash
git rm 00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml
git commit -m "governance: remove stale PROPOSED copy of DIS.013 — RESOLVED copy is canonical"
```

**R-14. Investigate `build_manifests` panchanga row**
```sql
SELECT * FROM build_manifests WHERE build_id = 'phase-4c-enrich-20260521-r2';
```
If no row: manually insert OR document in V1_3_AUDIT_QUEUE CF.V13.2 with confirmed row count.

### TIER 5: STRATEGIC — Before M6 can open

**R-15. MEAN_NODE ephemeris data rebuild (human operator gate, 4–6h)**
- Prerequisite: confirm current `ephemeris_daily` was bootstrapped before MEAN_NODE fix via `build_manifests` query
- If pre-fix: execute `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md` (Phase 4B formal execution)
- Impact: corrects Rahu/Ketu longitudes in all transit and dasha calculations

**R-16. MSR signal B.3 Derivation-Ledger backfill (5–8 sessions)**
- Backfill `derivation_ledger.l1_sources` entries across ~571 ungrounded MSR v5.0 signals
- Each entry must cite specific FORENSIC fact_id or LEL event_id
- This is the prerequisite for M6 Prospective Testing per LL.8 discipline
- Scope: M5-A sub-phase, per `PHASE_M5_PLAN_v1_0.md §3`
- This work was declared in V1_3_AUDIT_QUEUE CF.V13.1 (severity HIGH) and is the highest-value non-blocking item in the queue

---

## Part 13 — Execution Sequencing

### Session A — Branch `governance/data-asset-reconciliation-s1` (1 Claude Code session, ~30 min)
R-1, R-2, R-7, R-8, R-13 — all surgical one-line or one-file changes.  
Human gate: PR review → merge → deploy `amjis-web` + `amjis-mcp`.

### Session B-1 — Branch `governance/data-asset-reconciliation-s2` (1 Claude Code session, ~60 min)
R-3 (Python pipeline — 7 locations), R-5 (archive MSR v3+v4), R-6 (GCS_LAYOUT v1.1), R-11 (CLAUDE.md LEL update), R-10 (mirror pair sync), R-12 (migration ledger backfill), R-14 (build_manifests check).

### Human gate between B-1 and B-2
- Apply migrations 116 + 117 (R-9)
- Run `build_manifests` query for ephemeris
- Run `SELECT source_file, COUNT(*) FROM msr_signals GROUP BY source_file` to determine R-4 scope

### Session B-2 — (1 Claude Code session, ~30 min, conditional)
R-4 (TS ETL re-run and/or Python pipeline rebuild if DB shows v3 state).  
Only needed if DB queries confirm v3 state in `msr_signals` or `l25_msr_signals`.

### Separate — Phase 4B Execution (human-gated, 4–6h wait)
R-15: MEAN_NODE ephemeris data rebuild per Phase 4B brief.

### Separate — M5-A sessions (5–8 sessions)
R-16: MSR signal B.3 Derivation-Ledger grounding backfill. This is the primary M5-A deliverable.

---

## Appendix: Finding Index

| ID | Description | Severity | Action |
|---|---|---|---|
| F-1 | `read_asset` MCP serves MSR v3 to LLM | BLOCKING | R-1 |
| F-2 | ICR confirm writes patches to dead MSR v3 file | BLOCKING | R-2 |
| F-3 | Python pipeline EXPECTED_COUNT=514 gate will reject v5.0 load | HIGH | R-3 |
| F-4 | `msr_signals` and `rag_chunks` DB tables likely frozen at v3.1/514 signals | HIGH | R-4 |
| F-5 | MSR v3 and v4 not archived despite MSR-HYGIENE-S1 declaration; `99_ARCHIVE/` never created | HIGH | R-5 |
| F-6 | GCS_LAYOUT body still shows MSR_v3_0.md as primary entry | HIGH | R-6 |
| F-7 | GCS_LAYOUT ephemeris note stale | HIGH | R-6 |
| F-8 | `manifest_overrides.yaml` MP.5 enforcement_rule causes drift_detector H.3.1 false-positive | MEDIUM | R-7 |
| F-9 | `msr_parser.test.ts` fixture path internally contradictory | MEDIUM | R-8 |
| F-10 | Migrations 116+117 unapplied — acharya-tier API keys inoperable | MEDIUM | R-9 |
| F-11 | MP.1/MP.2/MP.9 mirror pairs have 8-workstream structural drift | MEDIUM | R-10 |
| F-12 | CLAUDE.md §D/§E LEL version and entry count stale (v1.6/36 events vs actual v1.7/57 events) | MEDIUM | R-11 |
| F-13 | DIS.013 PROPOSED patch file not cleaned up | LOW | R-13 |
| F-14 | Migrations 072–082 not individually logged in MIGRATIONS_APPLIED_LOG.md | LOW | R-12 |
| F-15 | `build_manifests` panchanga bootstrap row unconfirmed | LOW | R-14 |
| F-16 | MEAN_NODE ephemeris data rebuild: code-complete, production data unconfirmed | STRATEGIC | R-15 |
| F-17 | MSR v5.0 B.3 Derivation-Ledger grounding: 571/573 signals lack FORENSIC/LEL L1 citations (M6 blocker) | STRATEGIC | R-16 |
| F-18 | 59 MSR signals (SIG.MSR.515–573, Yogini+Tajaka) not in any pipeline table | HIGH | R-3 + R-4 |
| F-19 | `school_convergence_index` migration comment declares 543 signals (v4.0) not 573 (v5.0) | MEDIUM | R-4 |

*v1.1 — 2026-05-25. Supersedes v1.0 of same date. All "does not cover" items from v1.0 are now inside the main body (MEAN_NODE = Part 11 / R-15; MSR grounding = Part 10 / R-16; R9 embeddings = noted in F-4; conversation embedding backfill = a separate V1.3 item not a data-asset integrity issue; GCS object deletion = noted in R-5). Status: LIVING — mark each Rn DONE as actions complete; issue v1.2 when all Tier 1–3 items are DONE.*

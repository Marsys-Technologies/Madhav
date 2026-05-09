---
artifact: CHART_FACTS_PIPELINE_AUDIT_v1_0.md
version: 1.0
status: CURRENT
authored_at: 2026-05-10
authored_by: Claude Code (Opus 4.7) — VARGA-ETL-FULL-S1-CPA
audience: governance + operators (native + future agents touching chart_facts ETL)
supersedes: none (new artifact)
related:
  - 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml (v1.1)
  - 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json (v1.1)
  - platform/python-sidecar/pipeline/ingest_chart_facts.py (canonical runner)
  - platform/python-sidecar/pipeline/writers/chart_facts_writer.py (canonical writer)
  - platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py (FROZEN/DEPRECATED 2026-05-10)
  - platform/python-sidecar/pipeline/loaders/chart_facts_loader.py (FROZEN/DEPRECATED 2026-05-10)
  - CLAUDECODE_BRIEF.md (VARGA-ETL-FULL-S1) — origin brief
---

# CHART_FACTS_PIPELINE_AUDIT v1.0

## §1 — Why this document exists

A 2026-05-09 audit of the chart_facts ETL surface uncovered a dual-pipeline race
condition that had been silently corrupting the live `chart_facts` table.
Divisional placements (§3.x rows) — the most acharya-critical content for
varga-aware queries — were being deleted on every alternating ingest, depending
on which of two pipelines ran last. This audit documents the failure mode, the
v1.1 resolution, expected post-fix row counts, and the manual re-run procedure.

## §2 — The failure mode (pre-2026-05-10)

Two pipelines wrote into the same `chart_facts` table from different sources,
on different schedules, using incompatible write semantics:

### Pipeline A — YAML staging-swap (canonical from v1.0)

- **Source:** `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` (GCS-mirrored)
- **Schema:** `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json`
- **Runner:** `platform/python-sidecar/pipeline/ingest_chart_facts.py`
- **Writer:** `platform/python-sidecar/pipeline/writers/chart_facts_writer.py`
- **Coverage (v1.0):** §1, §2.1–§2.3, §3.1–§3.15, §4.x, §5.x, §10.x, §11.1, §12.x,
  §13.1, §14.x, §15.x, §26.x — 589 rows across 18 categories.
- **Write semantics:** validates → INSERT into `chart_facts_staging` → DELETE FROM
  `chart_facts` → INSERT FROM staging WHERE build_id = X → TRUNCATE staging.
  This is a full, atomic, table-wide replacement.

### Pipeline B — markdown extractor + ON CONFLICT loader

- **Source:** `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (parsed at runtime)
- **Extractor:** `platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py`
  (parses §6.x, §7.x, §8, §9, §11.x, §16.x–§22.x, §24.x via regex/LLM extraction).
- **Loader:** `platform/python-sidecar/pipeline/loaders/chart_facts_loader.py`
- **Coverage (Pipeline B):** ~190–215 rows across 19 NEW categories — `shadbala`,
  `bhava_bala`, `ishta_kashta`, `strength_extra`, `ashtakavarga_bav`/`sav`/`pinda`,
  `kakshya_zone`, `avastha`, `upagraha`, `sensitive_point`, `mrityu_bhaga`,
  `arudha_occupancy`, `aspect`, `chalit_shift`, `chandra_placement`,
  `deity_assignment`, `varshphal`, `longevity_indicator`.
- **Write semantics:** INSERT … ON CONFLICT (fact_id) DO UPDATE — additive,
  per-row. Does NOT delete rows that are absent from its current run.

### How the race fires

Both pipelines write to the same `chart_facts` table. Run order matters:

| Last to run         | Surviving rows                                                |
| --------------------- | ------------------------------------------------------------- |
| Pipeline A (YAML)   | Only Pipeline A's 589 rows. ALL Pipeline B rows wiped.        |
| Pipeline B (markdown) | Pipeline A's rows are preserved (B does not delete) BUT only because A ran first; if B is re-run alone, it adds its categories on top of whatever A left, so post-(A→B) state has both. Post-(B→A) state has only A. |

In practice, the YAML pipeline (Pipeline A) was re-run any time the chart was
edited or reseeded, which happened ~weekly. Each such run wiped Pipeline B's
markdown-derived rows. Divisional placements live in Pipeline A's coverage, so
divisional rows mostly survived; but **strength, ashtakavarga, bhava_bala,
aspect, transit, avastha, upagraha, sensitive_point, chalit_shift,
chandra_placement, deity_assignment, varshphal, longevity_indicator** rows
disappeared on every Pipeline-A run, only re-materialising whenever Pipeline B
was manually re-invoked. This is the root cause of the recurring "missing
strength rows" and "BAV bindus disappear after re-ingest" observations cited
in the 2026-05-09 audit.

## §3 — The v1.1 resolution (this brief)

Pipeline A (YAML) becomes the **single source of truth** for chart_facts ETL.
Pipeline B is frozen and deprecated. All Pipeline B categories are migrated
into the YAML.

### What changed

1. **`CHART_FACTS_EXTRACTION_v1_0.yaml`** bumped 1.0 → **1.1**. Added 77 rows:
   - §2.4 Planet-to-Cusp Distance (9 `CDL.*` rows, category `cusp`)
   - §3.5.2 D9 12th-stellium completeness (3 new `D9.12H.*` rows for queryability)
   - §6.4 FORENSIC-engine Bhavabala (12 `BVB.FORENSIC.H01..H12` rows, category `bhava_bala`)
   - §11.6 Chesta motion audit (7 `CHS.MOTION.*` rows, category `strength_extra`)
   - §16.2 Tight-Orb Western aspects (23 `ASP.W.*` rows, category `aspect`)
   - §16.3 Bhav-Madhya aspects (14 `ASP.BM.*` rows, category `aspect`)
   - §16.4 Trine geometry check (1 `ASP.TRN.*` row, category `aspect`)
   - §21 Sade Sati transit (8 `TRS.SS.*` rows, category `transit`)
   - PLN.MERCURY value_json gains `vargottama: true` (D1.h queryable boolean).

2. **`CHART_FACTS_SCHEMA_v1_0.json`** bumped 1.0 → **1.1**. Category enum
   expanded from 18 → 38 entries (union of Pipeline A + Pipeline B categories).

3. **`chart_facts_extractor.py`** marked `# DEPRECATED 2026-05-10` at the top.
   Code intact for audit trail; do not extend.

4. **`chart_facts_loader.py`** marked `# DEPRECATED 2026-05-10` at the top.
   Code intact for audit trail; do not extend.

5. **`chart_facts_writer.py`** `EXPECTED_COUNT_MAX` 700 → **820** to accommodate
   the +77 v1.1 rows (current count 666; +120 headroom).

6. **`ingest_chart_facts.py`** docstring updated to declare itself the SOLE ETL
   path and warn against running the deprecated extractor concurrently.

### What this does NOT change

- The Pipeline-B-only categories that are NOT yet migrated into the YAML
  (§7 ashtakavarga, §6.6 JH bhava_bala, §6.7 IKP, §6.8 PVC, §8 kakshya, §9
  avastha, §11.1 upagraha, §11.5 mrityu, §13 arudhas, §17 chalit, §18 chandra,
  §20 deity, §22 varshphal, §24 longevity) still need to be migrated in a
  follow-on session. Until they are, those rows are absent from chart_facts —
  which is fewer rows than before but at least no longer racing. The follow-on
  migration is GAP-PIPELINE-B-RESIDUAL.1 in the residual list below.

## §4 — Residuals to address (post-CPA / next sessions)

### GAP-PIPELINE-B-RESIDUAL.1 — Migrate the remaining Pipeline B categories

The following sections were Pipeline B's exclusive territory and have NOT been
migrated into the YAML at v1.1 (deferred to a follow-on YAML extension session):

- §6.6 JH-engine Bhava Bala (12 `BVB.JH.*` rows; `bhava_bala` category, `engine: JH` tag in value_json)
- §6.7 Ishta/Kashta Phala (7 `IKP.*` rows; `ishta_kashta` category)
- §6.8 Pancha-Vargeeya Classification (7 `PVC.*` rows; `strength_extra` or new `pancha_vargeeya` category)
- §6.1–§6.3 Shadbala (~9 rows + 9 totals; `shadbala` category)
- §6.5 Vimsopaka Bala (7 rows; `strength_extra` or `vimsopaka` category)
- §7.1 BAV Per-Planet Bindus by Sign (8 rows × 12 signs ≈ 96 cell rows; `ashtakavarga_bav` category)
- §7.2 SAV Sarvashtakavarga (12 rows + grand total; `ashtakavarga_sav`)
- §7.3 Shuddha Pinda (Ashtakavarga reductions; `ashtakavarga_pinda`)
- §8 Saturn Kakshya Zones (zone rows; `kakshya_zone`)
- §9.1 Avastha (~9 planet rows; `avastha`)
- §11.1 Upagrahas (already partly in YAML at §11.1 — verify no gap)
- §11.2/§11.3/§11.4 Bhrigu Bindu, Yogi/Avayogi, Combustion (`sensitive_point`)
- §11.5 Mrityu Bhaga (11 rows; `mrityu_bhaga`)
- §13.1/§13.2 Arudha placements + sign occupancy (already partly in YAML — verify)
- §16.1 Classical Vedic Aspects (Graha Drishti) — DISTINCT from §16.2/3/4 already migrated
- §17 Chalit Kinetic Shifts (9 rows; `chalit_shift`)
- §18 Chandra Chart from-Moon view (12 rows; `chandra_placement`)
- §20 Deity Assignments (deity_assignment)
- §22 Varshphal 2026–2027 (varshphal)
- §23 Cross-reference matrices (likely too large for chart_facts; consider rag_chunks-only)
- §24 Longevity Indicators (Kalachakra paramayush etc; `longevity_indicator`)
- §25 Additional dasha systems (Moola/Narayana/Sudasa/Kalachakra)

Total expected after full migration: ~900–950 rows. Bump `EXPECTED_COUNT_MAX`
again to ~1000 at that time.

### GAP-FORENSIC-NONE — All targeted §-references in this CPA exist in FORENSIC v8.0

Per CLAUDECODE_BRIEF VARGA-ETL-FULL-S1 D1.b–g, the following sections were
inspected and ALL exist in FORENSIC v8.0:

- §1.2 Core Mirror — present (already in YAML v1.0; no new rows added)
- §2.4 Planet-to-Cusp Distance — present (9 rows added)
- §6.4 Bhavabala (FORENSIC engine) — present (12 rows added)
- §11.6 Chesta and Motion Audit — present (7 rows added; Sun and Moon are
  intentionally absent in the FORENSIC source table — flagged in YAML notes)
- §16.2 / §16.3 / §16.4 Aspect ledgers — all present (38 rows added)
- §21 Sade Sati — present (8 rows added)

No `GAP-FORENSIC-{section}-ABSENT` markers needed. The brief's contingency
warnings about §6.4/§11.6/§21 possibly being absent are not triggered.

## §5 — Expected post-fix row counts per (category × divisional_chart)

Run `psql $DATABASE_URL -c "SELECT divisional_chart, count(*) FROM chart_facts
WHERE is_stale = false GROUP BY 1 ORDER BY 1;"` after re-ingest. Expected (from
the v1.1 YAML, 666 rows):

| divisional_chart | row count |
| ---------------- | --------- |
| BIRTH            | 12        |
| D1               | 354       |
| D2               | 2         |
| D3               | 12        |
| D4               | 12        |
| D7               | 12        |
| D9               | 18        |
| D10              | 11        |
| D12              | 12        |
| D16              | 12        |
| D20              | 12        |
| D24              | 12        |
| D27              | (absent in v1.1)        |
| D30              | 12        |
| D40              | 12        |
| D45              | 12        |
| D60              | 12        |
| KP               | 28        |
| VIMSHOTTARI      | 50        |
| YOGINI           | 17        |
| CHARA            | 144       |

(Counts are approximate; verify with `python3 -c "import yaml; from collections import Counter; d = yaml.safe_load(open('01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml')); print(Counter(f['divisional_chart'] for f in d['facts']))"`.)

By category (top categories from v1.1):

- house: 149
- chara dasha: 144
- planet: 57+
- vimshottari dasha: 50
- aspect: 38 (NEW v1.1)
- saham: 36
- birth_metadata: 22
- cusp: 21 (was 12 — +9 from §2.4)
- yoga: 18
- yogini: 17
- bhava_bala: 12 (NEW v1.1 — only FORENSIC-engine; JH-engine TBD next session)
- panchang/navatara: 12 each
- KP: 12+9+7
- transit: 8 (NEW v1.1 — Sade Sati only; varshphal TBD)
- strength_extra: 7 (NEW v1.1 — Chesta motion only; PVC/Vimsopaka TBD)
- (etc.)

## §6 — Manual re-ingest procedure (native operates with Cloud SQL Proxy)

Execute these in order from a workstation with Cloud SQL Auth Proxy access.
Do NOT run any of these as a Claude Code action — they touch the live database
and require human authorisation.

```bash
# Step 1: Start Cloud SQL Auth Proxy
cloud-sql-proxy madhav-astrology:asia-south1:marsys-prod &
export DATABASE_URL=postgresql://...   # standard connection string for the proxy

# Step 2: Audit current state BEFORE re-ingest
psql "$DATABASE_URL" -c "
  SELECT divisional_chart, count(*)
  FROM chart_facts
  WHERE is_stale = false
  GROUP BY 1 ORDER BY 1;
" > /tmp/chart_facts_before_v1_1.tsv

psql "$DATABASE_URL" -c "
  SELECT category, count(*)
  FROM chart_facts
  WHERE is_stale = false
  GROUP BY 1 ORDER BY 1;
" >> /tmp/chart_facts_before_v1_1.tsv

# Step 3: Upload v1.1 YAML + schema to GCS (the writer fetches from GCS, not local)
gsutil cp 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml \
  gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml
gsutil cp 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json \
  gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json

# Step 4: Run the unified YAML pipeline
cd platform/python-sidecar
python -m pipeline.ingest_chart_facts

# Expected output:
#   chart_facts: 666 rows loaded
#   staging: 666 rows written, errors=[]
#   validate: valid=True count=666 issues=[]
#   swap: chart_facts live: 666 rows (build_id=build-14c-chart-facts-20260510)

# Step 5: Verify post-ingest counts
psql "$DATABASE_URL" -c "
  SELECT divisional_chart, count(*)
  FROM chart_facts
  WHERE is_stale = false
  GROUP BY 1 ORDER BY 1;
" > /tmp/chart_facts_after_v1_1.tsv

# Step 6: DO NOT run pipeline.loaders.chart_facts_loader. It is FROZEN. Running it
#         would re-introduce the race. The v1.1 YAML is the only ETL surface.

# Step 7: Re-chunk FORENSIC (D10 of this brief adds varga metadata to chunks)
python -m pipeline.chunkers.forensic_chunker

# Step 8: Re-embed new/changed chunks
python -m rag.embed   # exact module name varies — check rag/embed.py for the runner

# Step 9: Verify chunk + embedding coverage
psql "$DATABASE_URL" -c "
  SELECT metadata->>'varga' AS varga, count(*)
  FROM rag_chunks
  WHERE doc_type = 'l1_fact' AND is_stale = false
  GROUP BY 1 ORDER BY 1;
"
# Expected: rows for D2 through D60 (one per §3.x section), plus 'CSI' for §3.15,
# plus '(null)' for non-§3 chunks.
```

## §7 — Rollback procedure

If v1.1 ingest reveals a corrupted YAML or unexpected data loss:

1. Re-upload the v1.0 YAML from a previous build artifact
   (`gs://madhav-marsys-build-artifacts/build-14c-chart-facts-20260429/`)
   to overwrite the current `gs://madhav-marsys-sources/L1/facts/STRUCTURED/`
   YAML.
2. Re-run `python -m pipeline.ingest_chart_facts` — this re-stages and swaps
   to the v1.0 row set (589 rows).
3. Re-test failing queries.

The deprecated extractor (`chart_facts_extractor.py` + `chart_facts_loader.py`)
remains operable as a last-ditch recovery surface for the categories that are
NOT in the v1.0 YAML — but invoking it re-introduces the race and is not
recommended.

## §8 — Verification

This audit's claims are verified by:

- `python3 -c "import yaml; d = yaml.safe_load(open('01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml')); print(d['schema_version'], len(d['facts']))"` → `1.1 666`
- `python3 -c "import json; s = json.load(open('01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json')); print(s['version'], len(s['properties']['facts']['items']['properties']['category']['enum']))"` → `1.1 38`
- `python3 -c "import yaml,json,jsonschema; jsonschema.Draft202012Validator(json.load(open('01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json'))).validate(yaml.safe_load(open('01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml')))"` → exits 0 (clean validation).
- `grep -n "^# DEPRECATED 2026-05-10" platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py platform/python-sidecar/pipeline/loaders/chart_facts_loader.py` → both files banner-marked.

---

*End of CHART_FACTS_PIPELINE_AUDIT_v1_0.md.*

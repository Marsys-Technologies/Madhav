---
brief_id: M2_A2_CHART_FACTS_ETL
karn_session_name: KARN-W2-R2-CHART-FACTS-ETL
wave: 2
stream: A
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 1 close
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (extractor extension + chart_facts ingest + rag_chunks re-chunk + verify)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: KARN-W1-R1-PHASE-ALPHA (provides FORENSIC §1–§27 prioritization in M1_M2_ACTIVATION_MATRIX §6.2)
  blocks: M2_C1_CHART_FACTS_QUERY (downstream tool needs new categories), M2_E2_EVAL_HARNESS
parallel_stream_note: |
  Two other Wave-2 briefs run concurrently:
  - KARN-W2-R1-MSR-ETL (Stream A, msr_signals 8 columns) — owns migration 028
  - KARN-W2-R3-CGM-FULL-EDGES (Stream A, l25_cgm_edges) — owns migration 030
  This brief owns:
  - migration 029 (no new chart_facts schema columns; chart_facts already supports new categories
    via the existing `category` text + `value_json` jsonb design — see M1_M2_ACTIVATION_MATRIX §1.1)
  - python-sidecar/pipeline/extractors/chart_facts_extractor.py
  - 029 reserved for any auxiliary index this brief needs (e.g. category multi-value index)
  Disjoint from sibling briefs — no path collision.
estimated_time: 1 day single Claude Code session

scope_summary: |
  W1-R1's Audit 4 (FORENSIC §1–§27 activation matrix) ground-truthed that of 27 sections:
    11 ✅ FULL, 11 🟡 PARTIAL, 4 ⬛ DARK.
  This brief extends chart_facts coverage to close the highest-impact partial/dark sections.

  Priority order (per M1_M2_ACTIVATION_MATRIX §6.2):
    P1 — §6 Strength Metrics (~40 rows: shadbala, bhava_bala, ishta_kashta, pancha_vargeeya)
    P1 — §7 Ashtakavarga (~30 rows: BAV, SAV, Shuddha Pinda)
    P2 — §16 Aspects (~30 rows: Parashari graha drishti structured)
    P2 — §11.2-§11.5 Sensitive Points remaining (~15 rows: upagraha, sensitive_point, mrityu_bhaga)
    P2 — §13.2 Arudha Sign Occupancy (~5 rows)
    P3 — §8 Saturn Kakshya Zones (~8 rows)
    P3 — §9 Avastha Diagnostics (~10 rows)
    P3 — §17 Chalit Kinetic Shifts (~7 rows)
    P3 — §18 Chandra Chart (~12 rows)
    P4 — §20 Deity Assignments (~9 rows)
    P4 — §22 Varshphal 2026–2027 (~10 rows)
    P4 — §24 Longevity Indicators (~10 rows)
    SKIP §19 Kota Chakra, §25 Additional Dasha Systems (low priority per W1-R1)

  Net effect:
  - chart_facts grows ~589 → ~770+ rows.
  - 14 new category values added to chart_facts.
  - rag_chunks doc_type=l1_fact gains coverage for FORENSIC sections previously rag-only.
  - Sections moving from 🟡/⬛ → ✅ in activation matrix: §6, §7, §11 (all 5 sub), §13 (both),
    §16, §8, §9, §17, §18, §20, §22, §24.

  Net activation matrix improvement: 11 ✅ FULL → 22+ ✅ FULL.

may_touch:
  - platform/migrations/029_chart_facts_indexes.sql                    # CREATE — auxiliary indexes only (no new chart_facts columns needed)
  - platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py  # extend to parse 12 new section types
  - platform/python-sidecar/pipeline/extractors/__tests__/test_chart_facts_extractor.py  # extend
  - platform/python-sidecar/pipeline/loaders/chart_facts_loader.py     # accept new category values
  - platform/python-sidecar/pipeline/chunkers/forensic_chunker.py      # ensure §6–§24 chunks emit
  - platform/python-sidecar/pipeline/chunkers/__tests__/test_forensic_chunker.py
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A2_CHART_FACTS_ETL.md   # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_A2_VERIFICATION_<DATE>.txt               # CREATE
  - 00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md                         # update §1.2 + §4 + §5 + §7

must_not_touch:
  - CLAUDECODE_BRIEF.md (root)                                         # UI/UX stream
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A1_MSR_ETL.md           # sibling Wave-2
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B1_CGM_FULL_EDGES.md    # sibling Wave-2
  - platform/migrations/001-028                                        # historical, do not modify
  - platform/migrations/030_*                                          # W2-R3's range
  - platform/python-sidecar/pipeline/extractors/msr_extractor.py       # W2-R1 territory
  - platform/python-sidecar/pipeline/extractors/cgm_extractor.py       # W2-R3 territory
  - platform/src/components/**                                         # UI/UX scope
  - platform/src/app/**                                                # UI/UX scope
  - platform/src/lib/retrieve/**                                       # not in scope this brief; chart_facts_query lands W4-R3
  - platform/src/lib/router/**                                         # not in scope
  - 025_HOLISTIC_SYNTHESIS/**                                          # source-of-truth, read-only
  - 035_DISCOVERY_LAYER/**                                             # off-limits

acceptance_criteria:
  AC.1: |
    Pre-flight gate passes (branch, working tree, gcloud, Auth Proxy, secret name `amjis-db-password`,
    chart_facts baseline = 589 rows, tests baseline 958/13 ± W2-R1 deltas if W2-R1 lands first).
  AC.2: |
    Read FORENSIC v8.0 sections §6, §7, §8, §9, §11.2-§11.5, §13.2, §16, §17, §18, §20, §22, §24 carefully.
    Inventory exact row count expected per section based on subsection structure.
    Document expected counts in M2_A2_VERIFICATION_<DATE>.txt §1.
  AC.3: |
    Migration 029 created at platform/migrations/029_chart_facts_indexes.sql.
    Adds these auxiliary indexes (no schema changes — existing schema supports new categories):
      CREATE INDEX IF NOT EXISTS chart_facts_category_divchart_idx
        ON chart_facts(category, divisional_chart) WHERE is_stale=false;
      CREATE INDEX IF NOT EXISTS chart_facts_source_section_idx
        ON chart_facts(source_section) WHERE is_stale=false;
      CREATE INDEX IF NOT EXISTS chart_facts_value_json_gin
        ON chart_facts USING GIN (value_json);
    These indexes accelerate the chart_facts_query tool that lands W4-R3.
  AC.4: |
    chart_facts_extractor.py extended to parse these 12 new section types from FORENSIC v8.0:
      §6.1 Shadbala       → category="shadbala"            (~10 rows: planet × strength components)
      §6.2 Bhava Bala     → category="bhava_bala"          (~12 rows: house × bala)
      §6.3 Ishta-Kashta   → category="ishta_kashta"        (~9 rows: planet × ishta + kashta)
      §6.4-§6.8 misc      → category="strength_extra"      (~9 rows: residuals from §6 sub-tables)
      §7.1 BAV            → category="ashtakavarga_bav"    (~9 rows: planet BAV totals)
      §7.2 SAV            → category="ashtakavarga_sav"    (~12 rows: sign × SAV bindus)
      §7.3 Shuddha Pinda  → category="ashtakavarga_pinda"  (~9 rows: planet pinda)
      §8 Kakshya Zones    → category="kakshya_zone"        (~8 rows: zone × ruling planet)
      §9 Avastha          → category="avastha"             (~10 rows: planet × avastha)
      §11.2 Upagrahas     → category="upagraha"            (~5 rows: upagraha × position)
      §11.3-§11.4 misc    → category="sensitive_point"     (~5 rows: gulika, mandi, etc.)
      §11.5 Mrityu Bhaga  → category="mrityu_bhaga"        (~5 rows: planet × bhaga degree)
      §13.2 Arudha Occ    → category="arudha_occupancy"    (~5 rows: sign × arudha pada)
      §16.1 Parashari     → category="aspect"              (~30 rows: aspect grid)
      §17 Chalit Shifts   → category="chalit_shift"        (~7 rows: planet × shift)
      §18 Chandra Chart   → category="chandra_placement"   (~12 rows: planet × moon-chart house)
      §20 Deity Assigns   → category="deity_assignment"    (~9 rows: planet × deity (palana/karma/ishta))
      §22 Varshphal       → category="varshphal"           (~10 rows: 2026-2027 annual chart)
      §24 Longevity       → category="longevity_indicator" (~10 rows: kalachakra/ayurdasaya)
    Total expected new rows: ~165–185.
  AC.5: |
    For each new category, value_json carries structured payload. Examples (illustrative):
      shadbala         → {"sthana_bala":..., "dig_bala":..., "kala_bala":..., "cheshta_bala":..., "naisargika_bala":..., "drik_bala":..., "total":...}
      bhava_bala       → {"bhava":N, "bala":..., "rank":...}
      ishta_kashta     → {"ishta":..., "kashta":...}
      ashtakavarga_bav → {"bindus":..., "by_planet":{...}}
      ashtakavarga_sav → {"sign":..., "total":..., "by_planet":{...}}
      kakshya_zone     → {"zone":..., "ruling_planet":..., "transit_active":bool}
      avastha          → {"avastha":..., "explanation":...}
      upagraha         → {"upagraha":..., "longitude":..., "sign":..., "house":N}
      mrityu_bhaga     → {"planet":..., "degree":..., "sign":..., "active":bool}
      aspect           → {"from_planet":..., "to_planet":..., "type":"parashari","strength":...}
      chalit_shift     → {"planet":..., "rashi_house":N,"chalit_house":M,"shift":delta}
      chandra_placement→ {"planet":..., "moon_house":N, "moon_sign":...}
      deity_assignment → {"planet":..., "palana":..., "karma":..., "ishta":...}
      varshphal        → {"year_start":..., "muntha_sign":..., "muntha_house":N,"year_lord":...}
      longevity_indicator → {"system":"kalachakra"|"ayurdasaya","estimated_years":N,"basis":...}
    NULL if source has no value. JSON shape is per-category but consistent within category.
  AC.6: |
    Each new chart_facts row has stable fact_id following the existing pattern:
      <CAT_PREFIX>.<KEY>  e.g.  SHB.SUN, BVB.7, KAK.1, ASB.SUN, SAV.ARIES, AVA.SUN, ASP.MA-SAT
    fact_id MUST be UNIQUE per-row (existing UNIQUE constraint).
  AC.7: |
    Each new chart_facts row has source_section pointing to FORENSIC subsection (e.g. "§6.1 row 3").
  AC.8: |
    Run the chart_facts ingest pipeline against FORENSIC_v8_0:
      python -m pipeline.ingest_chart_facts \
        --source ../../01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md \
        --upsert
    Post-ingest count check:
      SELECT COUNT(*) FROM chart_facts WHERE is_stale=false;
        ≥ 750 (was 589; +165 to +185 expected)
    HALT if count drift is more than ±20% of expected (stupid mass-insert / mass-skip).
  AC.9: |
    Per-category coverage check:
      SELECT category, COUNT(*) FROM chart_facts WHERE is_stale=false
      GROUP BY category ORDER BY 2 DESC;
    All 14 new categories must appear with non-zero counts. Counts must be within ±50% of
    expected per AC.4 numbers. Capture full distribution to verification txt.
  AC.10: |
    Sample 3 rows per new category to verify value_json shape is well-formed:
      SELECT category, fact_id, value_text, value_json::text, source_section
      FROM chart_facts WHERE category=<X> AND is_stale=false LIMIT 3;
    Each row's value_json must parse as valid JSON. Capture samples to verification txt.
  AC.11: |
    Re-chunk FORENSIC §6, §7, §8, §9, §11, §13, §16, §17, §18, §20, §22, §24 into rag_chunks
    doc_type=l1_fact. Some sections may already be partially chunked — UPSERT, don't duplicate.
    Post-chunk count:
      SELECT doc_type, COUNT(*) FROM rag_chunks WHERE is_stale=false GROUP BY doc_type;
      l1_fact previously ~102 chunks → expected ≥130 chunks (+25–35).
  AC.12: |
    Tests pass at pre-existing baseline (no new failures). New extractor unit tests added per
    new category type — at least 2 tests per category covering parse + edge case.
  AC.13: |
    Cloud Run revision rebuilt and serving 100%. Live-deploy verification:
    Send 2 fresh queries through Consume tab targeting newly-activated content (e.g.
    "What is my Saturn's Shadbala?" — should now find chart_facts row in retrieval).
    Capture query_plans rows + answer quality eyeball check.
  AC.14: |
    M1_M2_ACTIVATION_MATRIX.md updated:
      - §1.2 category breakdown: add 14 new rows.
      - §4 FORENSIC §1–§27 matrix: flip 11 sections (§6, §7, §8, §9, §11, §13, §16, §17, §18,
        §20, §22, §24) from 🟡/⬛ to ✅, with updated coverage % and tool list.
      - §5.1 activation counts: 11 ✅ → 22+ ✅; 11 🟡 → 0–2 🟡; 4 ⬛ → 0 ⬛ (or ≤1).
      - §7 chart_facts row: 589 → ~770+; mark green.
  AC.15: |
    git status shows ONLY:
      platform/migrations/029_chart_facts_indexes.sql (new)
      platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py (modified)
      platform/python-sidecar/pipeline/extractors/__tests__/test_chart_facts_extractor.py (modified)
      platform/python-sidecar/pipeline/loaders/chart_facts_loader.py (modified)
      platform/python-sidecar/pipeline/chunkers/forensic_chunker.py (modified)
      platform/python-sidecar/pipeline/chunkers/__tests__/test_forensic_chunker.py (modified)
      00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A2_CHART_FACTS_ETL.md (status flip)
      00_ARCHITECTURE/BRIEFS/M2_A2_VERIFICATION_<DATE>.txt (new)
      00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md (modified)
    No other changes.
  AC.16: |
    This brief's frontmatter `status` flipped to COMPLETE. Closing summary appended to
    PROJECT_KARN_SESSION_LOG.md per protocol §3.1.

halt_conditions:
  - Auth Proxy unreachable on 127.0.0.1:5433 after 30s wait
  - gcloud ADC missing OR `amjis-db-password` secret unreadable (note: NOT `amjis-app-db-password`)
  - Branch is not redesign/r0-foundation (DO NOT switch)
  - Pre-existing chart_facts row count != 589 (Wave-1 baseline drift)
  - Migration 029 fails to apply
  - Post-ingest row count drift >±20% from expected
  - Any new category has 0 rows after ingest (indicates extractor parse failure)
  - value_json sample shows malformed JSON in any category
  - Tests baseline drift > 2 failures either direction (account for sibling W2-R1 if landed first)
  - Cloud Build failure
---

# CLAUDECODE_BRIEF — M2_A2_CHART_FACTS_ETL (Wave 2, Stream A, Run 2)

## §1 — Why this session

W1-R1's Audit 4 identified that 15 FORENSIC sections (§6–§9, §11.2-§11.5, §13.2, §16, §17, §18, §19, §20, §22, §24, §25) are 🟡 PARTIAL or ⬛ DARK in chart_facts coverage. Of these, the 12 we're addressing here cover ~85% of the missing high-source-density content.

Rationale per priority tier:

**P1 (§6, §7) — Strength + Ashtakavarga.** Shadbala numerics are referenced in MSR claim_text (e.g., "Saturn Shadbala 312 viru..." — the 312 comes from §6.1 but isn't queryable today). BAV/SAV bindus drive transit-timing predictions. Both have ≥30 rows of structured numerics that downstream tools can join against. HIGH PAYOFF.

**P2 (§16, §11.2-§11.5, §13.2) — Aspects, Sensitive Points, Arudha Occupancy.** Aspect grid is fundamental to interpretation; we currently rely on MSR signals to capture key aspects ad-hoc. Adding the structured grid gives the chart_facts_query tool a clean target. Sensitive Points (Upagrahas, Mrityu Bhaga) are timing-relevant. §13.2 Arudha sign occupancy is small but unlocks "which signs hold arudha padas" queries.

**P3 (§8, §9, §17, §18) — Kakshya, Avastha, Chalit, Chandra.** Smaller tables, lower per-row impact, but unblock specialized queries. §17 Chalit shifts are referenced when planet is in cusp degrees.

**P4 (§20, §22, §24) — Deities, Varshphal, Longevity.** Lowest priority but small tables; do them now to retire the dark category entirely.

**SKIP (§19 Kota Chakra, §25 Additional Dashas).** §19 is specialized transit tool; not enough source value to justify. §25 has computation stubs; the temporal tool already partially handles. Defer to a later wave if needed.

**Not in scope:**
- chart_facts_query retrieval tool — that's W4-R3.
- Multi-native support (would require schema changes; defer to M3+).

## §2 — Pre-flight self-diagnostics (mandatory)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
test "$(git branch --show-current)" = "redesign/r0-foundation" || HALT "wrong branch"

git status --short
# HALT only on uncommitted modifications to files this brief targets.

gcloud auth application-default print-access-token > /dev/null 2>&1 || HALT "ADC missing"

PGPASSWORD=$(gcloud secrets versions access latest --secret="amjis-db-password" --project=madhav-astrology) || HALT "secret unavailable"
# IMPORTANT: secret name is `amjis-db-password` (NOT `amjis-app-db-password`).

nc -z 127.0.0.1 5433 || {
  bash platform/scripts/start_db_proxy.sh &
  for i in {1..30}; do nc -z 127.0.0.1 5433 && break; sleep 1; done
  nc -z 127.0.0.1 5433 || HALT "proxy failed to start"
}

# Baseline check:
PGPASSWORD="${PGPASSWORD}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -c "SELECT COUNT(*) FROM chart_facts WHERE is_stale=false;" -t
# Expected: 589 (W1-R1 baseline)

cd platform && npm test 2>&1 | tail -5
# Expected: 958/13 baseline (or 958+/13 if W2-R1 landed before this — fine, document)
```

## §3 — Implementation steps

### §3.1 — Read FORENSIC v8.0 carefully (AC.2)

Open `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`. For each of the 12 in-scope sections, count subsections, sub-tables, and atomic data points. Document expected row count to verification txt §1. This is the ground truth against which AC.9 plausibility will check.

### §3.2 — Extend chart_facts_extractor.py (AC.4 + AC.5 + AC.6)

The existing extractor produces dict rows like:
```python
{"fact_id": "ARD.AL", "category": "arudha", "divisional_chart": "D1",
 "value_text": "Capricorn H10", "value_json": {...}, "source_section": "§13.1 row 7"}
```

Add 14 new section parsers, each producing rows in the same shape. Implementation pattern:

```python
def parse_section_6(forensic_md: str) -> list[dict]:
    """Parse FORENSIC §6 Strength Metrics into chart_facts rows."""
    section = extract_section(forensic_md, anchor="§6")
    rows = []
    # §6.1 Shadbala — table with planet × bala columns
    for planet, balas in parse_shadbala_table(section).items():
        rows.append({
            "fact_id": f"SHB.{planet[:3].upper()}",
            "category": "shadbala",
            "divisional_chart": "D1",
            "value_text": f"{planet} Shadbala total: {balas['total']}",
            "value_json": balas,
            "source_section": "§6.1",
        })
    # §6.2 Bhava Bala — table with house × bala
    # ... etc
    return rows
```

Repeat for sections §7, §8, §9, §11.2–§11.5, §13.2, §16, §17, §18, §20, §22, §24.

Add unit tests per section type covering happy path + at least one edge case (e.g., missing
sub-table, malformed row). Tests in `__tests__/test_chart_facts_extractor.py`.

### §3.3 — Extend chart_facts_loader.py

The loader's category whitelist (if any) needs the 14 new values added. INSERT shape stays the
same (fact_id, category, divisional_chart, value_text, value_json, source_section, is_stale=false,
build_id, provenance jsonb).

Verify ON CONFLICT (fact_id) DO UPDATE handles new categories cleanly.

### §3.4 — Migration 029 (auxiliary indexes)

Create `platform/migrations/029_chart_facts_indexes.sql`:

```sql
-- Migration 029 — KARN-W2-R2 — chart_facts auxiliary indexes
-- Predecessor: KARN-W1-R1-PHASE-ALPHA Audit 1 (chart_facts schema confirmed sufficient)

BEGIN;

CREATE INDEX IF NOT EXISTS chart_facts_category_divchart_idx
  ON chart_facts(category, divisional_chart) WHERE is_stale=false;

CREATE INDEX IF NOT EXISTS chart_facts_source_section_idx
  ON chart_facts(source_section) WHERE is_stale=false;

CREATE INDEX IF NOT EXISTS chart_facts_value_json_gin
  ON chart_facts USING GIN (value_json);

COMMIT;
```

Apply:
```bash
PGPASSWORD="${PGPASSWORD}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -f platform/migrations/029_chart_facts_indexes.sql
```

### §3.5 — Run chart_facts ingest

```bash
cd platform/python-sidecar
python -m pipeline.ingest_chart_facts \
  --source ../../01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md \
  --upsert
```

(Adapt to actual entry-point if named differently.)

Verify count + per-category breakdown (AC.8 + AC.9):
```sql
SELECT COUNT(*) FROM chart_facts WHERE is_stale=false;
-- Expected ≥ 750 (was 589; +165–185).

SELECT category, COUNT(*) FROM chart_facts WHERE is_stale=false GROUP BY category ORDER BY 2 DESC;
-- Expected: 14 new categories appear with plausible counts.
```

### §3.6 — value_json shape verification (AC.10)

For each of the 14 new categories, sample 3 rows and parse value_json:
```sql
SELECT category, fact_id, value_text, value_json::text, source_section
FROM chart_facts
WHERE category IN ('shadbala','bhava_bala','ishta_kashta','strength_extra','ashtakavarga_bav',
                   'ashtakavarga_sav','ashtakavarga_pinda','kakshya_zone','avastha',
                   'upagraha','sensitive_point','mrityu_bhaga','arudha_occupancy','aspect',
                   'chalit_shift','chandra_placement','deity_assignment','varshphal',
                   'longevity_indicator')
  AND is_stale=false
ORDER BY category, fact_id;
```

Capture full output to verification txt. Eyeball each category's value_json — it must parse
as valid JSON and carry meaningful structured fields. If any row's value_json is malformed
or empty, HALT and trace back to extractor.

### §3.7 — Re-chunk FORENSIC sections into rag_chunks

The forensic_chunker should already cover §1–§27 in some form (W1-R1 found ~102 l1_fact chunks).
Verify the 12 in-scope sections are covered post-this-brief:

```sql
SELECT
  CASE
    WHEN content ILIKE '%§6%' THEN '§6'
    WHEN content ILIKE '%§7%' THEN '§7'
    -- etc
    ELSE 'other'
  END AS section_marker,
  COUNT(*)
FROM rag_chunks
WHERE doc_type='l1_fact' AND is_stale=false
GROUP BY section_marker;
```

If any in-scope section has 0 chunks, re-run forensic_chunker:
```bash
cd platform/python-sidecar
python -m pipeline.chunk_forensic --upsert
```

Total l1_fact chunks should be ≥130 post-chunk (was ~102).

### §3.8 — Build, test, deploy

```bash
cd platform
npm test 2>&1 | tail -10
# AC.12 — confirm baseline (account for W2-R1 sibling deltas if landed first)

bash platform/scripts/cloud_build_submit.sh
# AC.13 — capture revision name
```

### §3.9 — Live-deploy verification (AC.13)

Send 2 fresh queries through Consume tab. Suggested test queries:
1. "What is my Saturn's Shadbala?" — should now retrieve chart_facts shadbala row + maybe MSR signal.
2. "Show me my Ashtakavarga BAV totals" — should retrieve all 9 ashtakavarga_bav rows.

Capture answer text + query_plans rows + chart_facts retrieval evidence to verification txt.

### §3.10 — Update activation matrix (AC.14)

Edit `00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md`:

§1.2 — Add 14 new category rows to the breakdown table.

§4 — Flip status emoji + coverage % for §6, §7, §8, §9, §11, §13, §16, §17, §18, §20, §22, §24:
- 🟡 PARTIAL → ✅ FULL (or PARTIAL→PARTIAL with higher coverage if not all subsections covered)
- ⬛ DARK → ✅ FULL or 🟡 PARTIAL

§5.1 — Update activation counts to reflect new state.

§7 — Update chart_facts row to show new count + ✅ green.

### §3.11 — Status flip + log entry

- Flip `status: PENDING` → `status: COMPLETE` in this brief's frontmatter.
- Append per-brief entry to `00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1.

## §4 — Closing summary template

```
KARN-W2-R2-CHART-FACTS-ETL closed.
- migration 029 applied: 3 auxiliary indexes on chart_facts
- chart_facts: 589 rows → N rows (+M new across 14 categories)
- per-category counts: shadbala=A, bhava_bala=B, ashtakavarga_bav=C, ... (full distribution in verification txt)
- value_json shape verified for all 14 categories (samples in txt)
- rag_chunks l1_fact: 102 → P chunks
- M1_M2_ACTIVATION_MATRIX.md §1.2/§4/§5/§7 updated
- §6, §7, §8, §9, §11, §13, §16, §17, §18, §20, §22, §24 flipped to ✅ FULL (or higher PARTIAL)
- tests: pre N/13 → post N+M/13 (no new failures)
- Cloud Run revision: amjis-web-XXXXX-YYY
- 2 live-deploy queries verified retrieving newly-activated rows
- next pointer: W2-R3 (CGM full edges) parallel; W4-R3 (chart_facts_query tool) consumes this
```

## §5 — Halt-and-report checklist

- Pre-flight failure
- Migration 029 fails to apply
- Post-ingest row count drift >±20% from expected
- Any new category has 0 rows
- value_json malformed in any sample
- Tests baseline drift >2 failures
- Cloud Build failure
- Post-deploy queries fail to retrieve newly-activated content

---

*End of CLAUDECODE_BRIEF_M2_A2_CHART_FACTS_ETL. Predecessor: KARN-W1-R1-PHASE-ALPHA. Wave 2.*

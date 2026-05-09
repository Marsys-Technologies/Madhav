---
session_id: VARGA-ETL-FULL-S1
status: CHECKPOINT_A_COMPLETE
executor: claude-code-antigravity
phase: Pre-M5 Foundational Fix — Divisional Chart Full-Stack Repair
estimated_effort: large (5–8 hours; single long session or split at CHECKPOINT A)
authored_by: Claude (Cowork + Opus audit) 2026-05-09
checkpoint_a_closed_at: 2026-05-10
checkpoint_a_executor: claude-opus-4-7 (VARGA-ETL-FULL-S1-CPA)
checkpoint_a_deliverables_complete: [D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11]
checkpoint_a_deferred_to_next_session: [D12, D13, D14, D15, D16, D17, D18, D19]
---

# CLAUDECODE_BRIEF — VARGA-ETL-FULL-S1

## Mission

A comprehensive opus-level audit (2026-05-09) identified that divisional chart data is
broken at every layer of the stack — not just the ETL. This brief fixes all of it in the
correct way, as if the gap had never existed. No workarounds. No patches on top of patches.

The audit's most important findings (read before starting any work):

1. **Dual-pipeline race condition is the root cause.** Two separate ETL pipelines both write
   to `chart_facts`. Pipeline A (YAML staging-swap) handles §1–§5/§10/§12–§15/§26 and does a
   full DELETE-then-INSERT swap. Pipeline B (markdown extractor) handles §6–§9/§11/§16–§22/§24
   and does ON CONFLICT upserts. Whichever runs last wins — the other's rows are gone. Divisional
   placements (§3) come from Pipeline A. If Pipeline B ran last, zero divisional rows survive.

2. **§3.15 CSI ledger is entirely unread at L2.5.** The cross-divisional dignity ledger
   (D1→D9→D10 dignity transition per planet) is the most acharya-critical cross-varga
   reference in the entire FORENSIC file. Zero MSR signals, zero CGM edges, zero resonances
   reference it. This brief partially seeds it.

3. **D24, D30, D40, D45, D60 have zero CGM graph nodes.** Education, health/longevity,
   auspiciousness, purity, and past-karma domains cannot be reached by cgm_graph_walk.

4. **vector_search has no varga or section_id filter.** Even with correct §3 chunks present,
   the retrieval layer cannot pin a query to "give me D9 navamsha data only."

5. **No synthesis prompt instructs the model HOW to use divisional data once present.**
   DOMAIN_VARGA_MAP gets data into context; nothing tells the model what to do with it.

---

## Before you start: READ THESE FILES FIRST

Before touching any file, read the following in order. Do not skip.

1. `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — full file. Map every §3.x section
   and §3.15 CSI ledger. Note exact column names in each table.

2. `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` — full file. Understand the
   existing schema (fact_id format, category values, value_json shapes).

3. `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json` — schema enum for validation.

4. `platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py` — understand all
   19 categories it produces and the fact_id naming conventions.

5. `platform/python-sidecar/pipeline/writers/chart_facts_writer.py` — understand the
   swap mechanism (DELETE-then-INSERT from staging).

6. `platform/python-sidecar/pipeline/loaders/chart_facts_loader.py` — understand the
   upsert mechanism.

7. `platform/python-sidecar/pipeline/ingest_chart_facts.py` — understand the orchestration.

8. `platform/python-sidecar/rag/chunkers/l1_fact.py` — understand chunk metadata structure.

9. `platform/src/lib/retrieve/divisional_query.ts` — understand the SQL and category filter.

10. `platform/src/lib/retrieve/vector_search.ts` — understand the SQL and filter params.

11. `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` — skim signal_type values; note how divisional-pattern
    signals are formatted.

12. `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` — note how DVS nodes and DIVISIONAL_CONFIRMATION
    edges are formatted.

13. `platform/src/lib/prompts/templates/shared.ts` — note where QUERY_INDEPENDENCE_GATE
    and PREMISE_VERIFICATION_GATE are defined and wired.

---

## CHECKPOINT A (split point if needed)

If this session must be split into two:
- **Session 1:** Deliverables D1 through D3 (ETL unification + retrieval fixes + chunker).
  After Session 1, set status: CHECKPOINT_A_COMPLETE in this file and commit.
- **Session 2:** Deliverables D4 through D6 (L2.5 enrichment + synthesis gate + tests).

If running as one session, proceed through D1–D6 sequentially.

---

## Stream 1 — ETL Unification

### D1 — Extend YAML extraction with 6 missing FORENSIC sections

**File:** `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml`
**Bump version from** current → `1.1` (update version field in YAML frontmatter or header).

Read FORENSIC carefully for each of these sections and add the corresponding rows.
Follow the existing fact_id naming convention exactly (match the patterns you see in the file).
Do not guess fact_ids — derive them from FORENSIC content.

#### D1.a — §3.5.2 D9 12th-stellium (3 missing rows)

The existing YAML has `D9.12H.SIGN` and `D9.12H.DISP.VARG`. Add the missing:
- `D9.12H.TENANTS` — list of planets in the D9 12th house
- `D9.12H.DISPOSITOR` — dispositor planet of D9 12th sign
- `D9.12H.DISP.PLACE` — where that dispositor sits (sign/house)

Read §3.5.2 of FORENSIC for the exact values.
`category: "planet"`, `divisional_chart: "D9"`, `source_section: "§3.5.2"`

#### D1.b — §1.2 Core Mirror (birth chart mirror metadata)

Read §1.2 of FORENSIC. Extract core mirror metadata rows.
`category: "birth_metadata"`, `divisional_chart: "D1"`, `source_section: "§1.2"`

#### D1.c — §2.4 Planet-to-cusp distances

Read §2.4 of FORENSIC (if it exists as a distinct sub-section). If §2 contains
planet-to-cusp or bhava-entry data not already in the YAML, add those rows.
`category: "cusp"`, `divisional_chart: "D1"`, `source_section: "§2.4"` (adjust
section number to match what FORENSIC actually has).

#### D1.d — §6.4 FORENSIC Bhavabala (12 rows)

Read FORENSIC §6.4 or whichever section has FORENSIC-engine bhavabala values
(distinct from Jagannatha Hora bhavabala which is already in the YAML as §6.6).
`category: "bhava_bala"`, engine tag in `value_json: {engine: "FORENSIC"}`,
`source_section: "§6.4"`. Use fact_ids `BVB.FORENSIC.H01` through `BVB.FORENSIC.H12`.

**NOTE:** If §6.4 does not exist separately in FORENSIC (the data may be inline in §6),
skip this item and document it as GAP-FORENSIC-6.4-ABSENT in the notes below.

#### D1.e — §11.6 Chesta motion audit (7 rows)

Read FORENSIC §11.6. Extract one row per planet for Chesta motion (retrograde/direct
motion velocity data).
`category: "strength_extra"`, `source_section: "§11.6"`.
fact_ids: `CHS.MOTION.{PLANET}` (e.g., `CHS.MOTION.SUN`, `CHS.MOTION.MOON`, etc.)

**NOTE:** If §11.6 doesn't exist as a sub-section, search §11 for Chesta / motion data.
If absent, skip and document.

#### D1.f — §16.2, §16.3, §16.4 (Western aspects + Bhav-Madhya aspects + Trine geometry)

Read these sections. Extract aspect rows.
- §16.2 tight-orb Western aspects: `category: "aspect"`, `source_section: "§16.2"`,
  fact_ids `ASP.W.{PLANET1}.{PLANET2}` (orb in value_json)
- §16.3 Bhav-Madhya aspects: `category: "aspect"`, `source_section: "§16.3"`,
  fact_ids `ASP.BM.{PLANET}.H{NN}`
- §16.4 Trine geometry checks: `category: "aspect"`, `source_section: "§16.4"`,
  fact_ids `ASP.TRN.{PLANET1}.{PLANET2}`

**NOTE:** If these sub-sections don't exist in FORENSIC, document which are absent.

#### D1.g — §21 Sade Sati (8 rows)

Read FORENSIC §21 if it exists. Extract Sade Sati period data.
`category: "transit"`, `source_section: "§21"`, fact_ids `TRS.SS.{N}` (period 1, 2, etc.)

**NOTE:** If §21 doesn't exist, skip and document.

#### D1.h — Add Mercury vargottama as a queryable boolean on the PLN.MERCURY row

The existing D9.MERCURY row in the YAML likely has `vargottama: true` in its value_json.
Find the `PLN.MERCURY` row (D1-tagged planet row) and add `vargottama: true` to its
value_json if not already present. Do the same for any other planet that is vargottama
in D9 (same sign in D1 and D9). Read §3.5 and §2.1 to determine which planets are
vargottama — the canonical value is in FORENSIC, not derived.

---

### D2 — Update `CHART_FACTS_SCHEMA_v1_0.json` to cover all categories

**File:** `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json`

The schema enum currently covers only the YAML pipeline's categories. The markdown
extractor produces 19 additional categories that are NOT in the enum. Add ALL of them:
`shadbala`, `bhava_bala` (already added via D1.d), `ishta_kashta`, `strength_extra`,
`ashtakavarga_bav`, `ashtakavarga_sav`, `ashtakavarga_pinda`, `kakshya_zone`, `avastha`,
`upagraha`, `sensitive_point`, `mrityu_bhaga`, `arudha_occupancy`, `aspect`, `chalit_shift`,
`chandra_placement`, `deity_assignment`, `varshphal`, `longevity_indicator`, `transit`.

Add a new `transit` category for §21 Sade Sati rows.

**Acceptance:** schema enum is the complete superset; `jsonschema.validate(row, schema)`
passes for both pipeline's categories.

---

### D3 — Deprecate the markdown extractor; unify to single pipeline

**File:** `platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py`

Add a deprecation banner at the very top of the file:

```python
# DEPRECATED 2026-05-09 — VARGA-ETL-FULL-S1
# This extractor produced a parallel chart_facts population that races with the
# YAML pipeline's staging-swap. All of its categories have been migrated into
# CHART_FACTS_EXTRACTION_v1_0.yaml v1.1. This file is frozen; do not extend it.
# See 00_ARCHITECTURE/CHART_FACTS_PIPELINE_AUDIT_v1_0.md for the full rationale.
# The canonical pipeline is: ingest_chart_facts.py -> forensic_extractor.py (YAML).
```

Do NOT delete the file or its functions. Leave code intact, add the banner only.

**File:** `platform/python-sidecar/pipeline/loaders/chart_facts_loader.py`

Add the same deprecation banner at the top. Document that this loader (which does
ON CONFLICT upserts) is replaced by the writer's staging-swap which is now canonical.

**File:** `platform/python-sidecar/pipeline/ingest_chart_facts.py`

Update EXPECTED_COUNT_MIN and EXPECTED_COUNT_MAX to reflect the new expanded YAML row
count. Read the current values and raise the max to accommodate the new rows added in D1
(roughly +80 rows; set to current_max + 120 as headroom).

Update the docstring / inline comment to state: "As of v1.1 YAML (VARGA-ETL-FULL-S1),
this is the sole ETL path for chart_facts. The markdown extractor is deprecated."

---

### D4 — Author pipeline audit document

**New file:** `00_ARCHITECTURE/CHART_FACTS_PIPELINE_AUDIT_v1_0.md`

Write a clear document (200–300 lines) covering:
1. The two pipelines that existed: YAML staging-swap (what it covered) vs markdown extractor
   (what it covered). Include the race condition: DELETE-then-INSERT wipes upserts and vice versa.
2. Which FORENSIC sections each owned.
3. The v1.1 resolution: YAML is canonical; extractor deprecated; unified path via ingest_chart_facts.py.
4. Expected post-fix row counts per category and per divisional_chart.
5. Instructions for re-running the pipeline (for the manual step the native does with Cloud SQL Proxy).

This is governance documentation, not code. Frontmatter: `version: 1.0`, `status: CURRENT`.
Place it under `00_ARCHITECTURE/` per ROOT_FILE_POLICY.

---

## Stream 2 — Retrieval Layer Fixes

### D5 — Add `varga` and `section_id` filter to `vector_search`

**File:** `platform/src/lib/retrieve/vector_search.ts`

The chunk metadata (in the `metadata` JSONB column of `rag_chunks`) will after D7 carry
`varga: "D9"` and `section_id: "§3.5"` for divisional chart chunks. Extend the SQL query
to optionally filter on these:

Add to `VectorSearchInput` (or equivalent input type):
```ts
/** Filter to chunks whose metadata->>'varga' matches this varga code (e.g. "D9", "D10"). */
varga?: string
/** Filter to chunks whose metadata->>'section_id' starts with this prefix (e.g. "§3.5"). */
section_id_prefix?: string
```

In the SQL, add:
```sql
AND ($N::text IS NULL OR c.metadata->>'varga' = $N)
AND ($M::text IS NULL OR c.metadata->>'section_id' LIKE $M || '%')
```

Wire the new params into the query builder. Update the TypeScript input schema, type, and
the test file. Do not break existing callers — both params are optional with `null` default.

**Acceptance:** vector_search({varga:"D9"}) passes only D9 chunks in test. TypeScript clean.

---

### D6 — Expand `divisional_query` category whitelist and limit

**File:** `platform/src/lib/retrieve/divisional_query.ts`

Current default category filter: `['house', 'planet', 'strength', 'chalit_shift']`

Change to:
```ts
['house', 'planet', 'strength', 'strength_extra', 'chalit_shift',
 'arudha', 'arudha_occupancy', 'yoga', 'aspect', 'sensitive_point']
```

Change `LIMIT 60` to `LIMIT 200`.

**Rationale:** After D1, D9-tagged rows will include arudha (ARD.AL.D9), yoga rows
(§26.2 D9 yogas), aspect rows (§16.x tagged to D9 where applicable), and sensitive_point
rows. The wider category list ensures they surface.

**Acceptance:** Test mocks updated; existing tests pass; no new TS errors.

---

### D7 — Add `vargottama_only` filter to `chart_facts_query`

**File:** `platform/src/lib/retrieve/chart_facts_query.ts`

Add to the input type:
```ts
/** If true, filter to rows whose value_json->>'vargottama' = 'true'. */
vargottama_only?: boolean
```

Add to SQL WHERE clause:
```sql
AND ($N::boolean IS NULL OR (
  $N = false OR (value_json->>'vargottama')::boolean = true
))
```

**Acceptance:** `chart_facts_query({vargottama_only:true})` returns only Mercury (and any
other vargottama planet found in FORENSIC) across all vargas. Test updated. TS clean.

---

### D8 — Add new `cross_varga_dignity_query` tool (CSI surface)

**New file:** `platform/src/lib/retrieve/cross_varga_dignity_query.ts`

This tool surfaces the §3.15 CSI cross-divisional dignity ledger as a direct SQL result.

```ts
/** Returns per-planet dignity state across D1, D9, D10 from the §3.15 CSI rows. */
export async function crossVargaDignityQuery(
  input: CrossVargaDignityInput
): Promise<CrossVargaDignityResult[]>

interface CrossVargaDignityInput {
  planets?: string[]  // filter by planet name; null = all 9
}

interface CrossVargaDignityResult {
  planet: string
  d1_sign: string
  d1_dignity: string  // exaltation | debilitation | own_sign | mooltrikona | neutral
  d9_sign: string
  d9_dignity: string
  d10_sign: string
  d10_dignity: string
  vargottama: boolean  // true if D1 sign === D9 sign
  fact_ids: string[]   // CSI.{PLANET}, D9.{PLANET}, D10.{PLANET}
}
```

SQL: JOIN chart_facts rows where `fact_id LIKE 'CSI.%'` with D9.* and D10.* rows
by planet name extracted from fact_id. Derive dignity from sign (exaltation signs are
known constants per classical Jyotish — hardcode a small lookup table for the 7 planets).

Add to `platform/src/lib/retrieve/index.ts` export.
Add to `platform/src/lib/router/retrieval_capability_spec.ts` as a new tool entry:
```ts
const cross_varga_dignity_query = {
  name: 'cross_varga_dignity_query',
  description: 'Returns the §3.15 CSI cross-divisional dignity ledger — per-planet D1/D9/D10
    dignity states and vargottama status. Use for any query about cross-varga strength, dignity
    transitions, or the phrase "how does X planet behave across charts". Priority-1 for any
    query mentioning "navamsha comparison", "strength across charts", "vargottama", or
    "three-state". Always schedule alongside divisional_query for D9 and D10.',
  supported_params: ['planets'],
  optimal_patterns: [
    'All planets: {}',
    'Saturn only: {planets: ["Saturn"]}',
    'Comparison query: {planets: ["Sun","Moon","Saturn"]}',
  ],
} satisfies RetrievalCapabilityEntry
```

Add a test file: `platform/src/lib/retrieve/__tests__/cross_varga_dignity_query.test.ts`
with at least 3 tests: (a) returns 9 rows for empty input, (b) filters correctly by planet,
(c) vargottama=true for Mercury.

**Acceptance:** Tool works; exported; in RCS; 3 tests pass; TS clean.

---

### D9 — Wire `cross_varga_dignity_query` into planner examples

**File:** `platform/src/lib/router/planner.ts`

Add a new Example 2c between Example 2b and Example 3 (or update Example 2b):
Example 2c: query_class=interpretive, query involving "how is Saturn across charts" or
"what is the cross-varga picture for Mars" → schedules `cross_varga_dignity_query` at
priority-1 alongside `divisional_query` for D9 and D10.

Update Example 6 (holistic) to include `cross_varga_dignity_query` at priority-1 (no filter,
returns full 9-planet CSI picture).

**File:** `platform/src/lib/router/per_tool_planner.ts`

Add a template for `cross_varga_dignity_query`:
```ts
cross_varga_dignity_query: (plan) => `
Tool: cross_varga_dignity_query — §3.15 CSI ledger surface.
Returns per-planet D1/D9/D10 dignity states and vargottama status.
Query: "${plan.query_text}"
Planets: ${JSON.stringify(plan.planets ?? [])}

Output JSON with zero or one of:
- "planets": string[] — filter by planet name (omit for all 9)`,
```

**Acceptance:** TS clean; existing planner tests pass.

---

## Stream 3 — Chunker Metadata

### D10 — Add varga-aware metadata to L1 chunk output

**File:** `platform/python-sidecar/rag/chunkers/l1_fact.py`

After the existing metadata assembly (where `section_id` and `section_title` are set),
add varga detection logic. When `section_id` matches the pattern `§3.\d+` (i.e., one of
the §3.x divisional chart sections), parse the varga code from the section heading
(e.g., "§3.5 D9 — Navamsha" → varga="D9") and add:

```python
metadata['varga'] = 'D9'          # parsed from heading
metadata['layer_aspect'] = 'divisional'
```

For §5.x sections, add `metadata['layer_aspect'] = 'dasha'`.
For §6.x sections, add `metadata['layer_aspect'] = 'strength'`.
For §3.15 CSI specifically, add `metadata['varga'] = 'CSI'` and
`metadata['layer_aspect'] = 'divisional_transition'`.

**Regex to parse varga from heading:**
```python
import re
varga_match = re.search(r'\b(D\d+)\b', section_title)
if varga_match:
    metadata['varga'] = varga_match.group(1)
```

This enables the `varga` filter added to `vector_search` in D5.

Add or update the unit test for l1_fact.py to verify that a §3.5 chunk has
`metadata['varga'] == 'D9'` and a §3.6 chunk has `metadata['varga'] == 'D10'`.

**Acceptance:** Test passes; `section_id = "§3.5"` chunk has `varga = "D9"` in metadata.

---

### D11 — Verify chunker TARGET_SECTIONS covers §3.x

**File:** `platform/python-sidecar/pipeline/chunkers/forensic_chunker.py`

Read the TARGET_SECTIONS list. Verify that §3 and its subsections are included.
If TARGET_SECTIONS is used for a verification/audit step (not for actual chunking),
confirm that §3.1 through §3.15 sections will produce chunks above MIN_BODY_TOKENS.

If §3.1 (D2 Hora — only 2 table rows, ~30–50 tokens) is at risk of being below
MIN_BODY_TOKENS, lower the threshold to 12 or implement adjacent-section merging
for tiny sections so no §3.x section is dropped.

If TARGET_SECTIONS is used to RESTRICT which sections are chunked and §3 is omitted,
add it. The goal: every §3.x section and §3.15 produces at least one rag_chunk.

**Acceptance:** Dry-run `python -m pipeline.chunkers.forensic_chunker --dry-run --verify`
(or equivalent) shows ≥1 chunk produced for each of §3.1 through §3.15. Document how
to run this in D4's pipeline audit document.

---

## Stream 4 — L2.5 Enrichment

### D12 — MSR v3.0 → v3.1: Add §VI Cross-Varga Dignity Signals

**File:** `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`
**Bump:** Rename file to `025_HOLISTIC_SYNTHESIS/MSR_v3_1.md` OR add a `## §VI` section
with new signals and bump internal version in frontmatter to `3.1`. Follow whichever
versioning convention the existing file uses (check the frontmatter).

Read MSR carefully to understand the signal schema (signal_id, signal_name, signal_type,
classical_source, significance, confidence, v6_ids_consumed, falsifier fields).

Add the following signals (15 total). Each must reference specific FORENSIC fact_ids
(§3.15 CSI rows, §3.5 D9 rows, §3.6 D10 rows, §3.4 D7 rows, §3.7 D12 rows, §3.10 D24 rows,
§3.11 D30 rows, §3.12 D40 rows, §3.13 D45 rows):

**SIG.MSR.500** — "D1→D9 dignity coherence: 6 of 7 planets shift, Mercury alone vargottama"
- signal_type: divisional-pattern
- Source: §3.15 CSI ledger (9 CSI rows)
- Content: As a structural meta-signal — the fact that 6 planets change dignity state
  between D1 and D9 while Mercury is the sole vargottama anchor is the chart's single most
  acharya-relevant cross-varga fact. Cite every CSI row.
- significance: 0.92, confidence: 0.95

**SIG.MSR.501** — "Saturn three-state dignity architecture: D1 exaltation → D9 debilitation
(NBRY active via Sun) → D10 angular"
- signal_type: divisional-pattern
- Sources: CSI.SATURN, D9.SATURN, D10.SATURN, SIG.MSR.003 (existing D9 NBRY)
- significance: 0.90, confidence: 0.90

**SIG.MSR.502** — "Venus three-state dignity architecture: D1 [read from FORENSIC] → D9
debilitation (NBRY cancelled by [read cancellation planet from §3.5.1]) → D10 [read]"
- Read the actual Venus values from FORENSIC §3.5 and §3.15 before writing
- signal_type: divisional-pattern
- significance: 0.82, confidence: 0.85

**SIG.MSR.503** — "D7 saptamsha — [read Saturn/Rahu house position in D7 from FORENSIC §3.4]"
- Read FORENSIC §3.4 for actual D7 Saturn and Rahu positions; construct the signal accordingly
- signal_type: divisional-pattern, domain: children
- significance: 0.75, confidence: 0.78

**SIG.MSR.504** — "D7 — [read Jupiter/Mars position in D7 from FORENSIC §3.4]"
- Read §3.4 for Jupiter and Mars in D7
- signal_type: divisional-pattern, domain: children
- significance: 0.72, confidence: 0.75

**SIG.MSR.505** — "D12 dvadashamsa — [read Saturn position in D12 from FORENSIC §3.7]"
- Read §3.7 for Saturn (and other notable planets) in D12
- signal_type: divisional-pattern, domain: parents
- significance: 0.70, confidence: 0.75

**SIG.MSR.506** — "D24 siddhamsa — [read Saturn and Jupiter positions in D24 from §3.10]"
- Read §3.10 for Saturn and Jupiter in D24; construct signals about education domain
- signal_type: divisional-pattern, domain: education
- significance: 0.72, confidence: 0.78

**SIG.MSR.507** — "D20 vimsamsha — [read Jupiter and spiritual planet positions from §3.9]"
- Read §3.9
- signal_type: divisional-pattern, domain: spiritual
- significance: 0.68, confidence: 0.72

**SIG.MSR.508** — "D30 trimsamsha — [read Saturn+Mars+Venus house from §3.11]"
- Read §3.11 for Saturn, Mars, Venus positions
- signal_type: divisional-pattern, domain: health
- significance: 0.75, confidence: 0.78

**SIG.MSR.509** — "D40 khavedamsha — [read Jupiter+Venus house from §3.12]"
- Read §3.12
- signal_type: divisional-pattern, domain: auspiciousness
- significance: 0.65, confidence: 0.70

**SIG.MSR.510** — "D45 akshavedamsha — [read Jupiter position from §3.13]"
- Read §3.13
- signal_type: divisional-pattern, domain: purity
- significance: 0.62, confidence: 0.68

**SIG.MSR.511** — "D60 shashtiamsha — [read Saturn-lagna and Ketu position from §3.14]"
- Read §3.14
- signal_type: divisional-pattern, domain: past-karma
- significance: 0.68, confidence: 0.72

**SIG.MSR.512** — "D16 shodashamsha — [read dominant planets from §3.8]"
- Read §3.8
- signal_type: divisional-pattern, domain: vehicles-comforts
- significance: 0.58, confidence: 0.65

**SIG.MSR.513** — "D2 hora — [read sign distribution from §3.1]"
- Read §3.1 for which planets fall in Cancer hora vs Leo hora
- signal_type: divisional-pattern, domain: wealth
- significance: 0.60, confidence: 0.68

**SIG.MSR.514** — "Vargottama Mercury as cross-varga anchor — stability of Mercury's
disposition propagates through all Mercury-ruled significations across D1, D9, D10"
- This is a meta-signal that connects SIG.MSR.500 to the interpretive layer
- signal_type: divisional-pattern
- significance: 0.88, confidence: 0.90

**IMPORTANT:** Every signal must have a `v6_ids_consumed` field listing the actual FORENSIC
fact_ids it draws from. Do not write a signal without grounding it in FORENSIC rows.
Read the FORENSIC values; do not approximate or invent placements.

Bump MSR's internal `signal_count` / `total` to reflect the new count (~499 + 15 = ~514).
Update frontmatter version.

**Acceptance:** 15 new signals added; each has signal_type=divisional-pattern; each has
v6_ids_consumed with FORENSIC §3.x fact_ids; MSR signal count updated.

---

### D13 — CGM v9.0 → v9.1: Add DVS nodes for D24/D30/D40/D45/D60

**File:** `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md`
Bump internal version to 9.1 per whatever versioning convention the file uses.

Read FORENSIC §3.10 (D24), §3.11 (D30), §3.12 (D40), §3.13 (D45), §3.14 (D60).

For each varga, add DVS (Divisional Varga Spectrum) nodes — at minimum:
- `DVS.D24.LAGNA` — lagna sign in D24 chart
- `DVS.D24.{PLANET}` for each of the 9 planets in D24 (sign, house from D24 lagna)
- (same pattern for D30, D40, D45, D60)

That is ~50 new node entries (10 × 5 vargas).

Also add DIVISIONAL_TRANSITION edges based on §3.15 CSI ledger:
- For each of the 9 planets: edge from `PLN.{PLANET}` to `DVS.D9.{PLANET}` with
  edge_type: DIVISIONAL_TRANSITION, properties: {d1_sign, d9_sign, dignity_shift}.
- Source all values from §3.15 CSI rows (fact_ids `CSI.{PLANET}`).

Do not add DIVISIONAL_CONFIRMATION edges between D1↔D10 etc. unless you can verify
the exact planet positions from FORENSIC — defer to D14 (UCN) to describe these in prose.

Update CGM's `total_nodes` and `total_edges` counts in frontmatter.

**Acceptance:** CGM has DVS.D24.* through DVS.D60.* nodes; 9 DIVISIONAL_TRANSITION edges
citing CSI fact_ids; version bumped; counts updated.

---

### D14 — RM v2.0 → v2.1: Add multi-varga resonance entries

**File:** `025_HOLISTIC_SYNTHESIS/RM_v2_0.md`
Bump version to 2.1.

Read existing RM to understand resonance format (resonance_id, description, signal_ids,
strength, classical_basis fields).

Add 5 new resonances:

**RM.30** — "Vargottama Mercury resonance: Mercury stable across D1/D9 — disposits D9 12H
stellium and all §3.5.2 planets through a steady Mercury; stability of signification propagates."
- signal_ids: [SIG.MSR.514, SIG.MSR.500] + existing Mercury signal from MSR if any
- strength: 0.88

**RM.31** — "Saturn three-state resonance: D1 exaltation + D9 debilitation NBRY + D10 angular
= career delivered through challenge overcome"
- signal_ids: [SIG.MSR.501, SIG.MSR.003] + existing Sasha Yoga signal if present in MSR
- strength: 0.87

**RM.32** — "Venus three-state resonance: analogous to Saturn — read Venus values from FORENSIC
§3.5 and §3.15 before writing description"
- strength: 0.80

**RM.33** — "D9 12th-house stellium resonance: [read §3.5.2 planets] in D9 12H, disposited
by vargottama Mercury through Gemini — moksha/dissolution linkage anchored to the most stable
planetary energy in the chart"
- signal_ids: [SIG.MSR.500, SIG.MSR.514] + existing D9-stellium signal if any in MSR
- strength: 0.82

**RM.34** — "D10 career architectural triad: [read §3.6 for Mars, Saturn, Mercury positions
in D10] — career chart shows [describe based on actual FORENSIC values]"
- signal_ids: [SIG.MSR.501, SIG.MSR.502] (or whichever D10 signals apply)
- strength: 0.78

**IMPORTANT:** Read actual FORENSIC §3.5.2, §3.6, §3.15 values before writing RM resonance
descriptions. No approximations.

**Acceptance:** 5 new resonances added; each cites MSR signal_ids from D12; version bumped.

---

## Stream 5 — Synthesis Prompts

### D15 — Add `DIVISIONAL_INTEGRATION_GATE` to synthesis

**File:** `platform/src/lib/prompts/templates/shared.ts`

After the `PREMISE_VERIFICATION_GATE` export, add:

```ts
export const DIVISIONAL_INTEGRATION_GATE = `DIVISIONAL INTEGRATION GATE (mandatory for
interpretive, holistic, predictive, and cross_domain query classes):
When divisional chart placements are present in the retrieved context (any fact_id of
the form D9.*, D10.*, D7.*, D12.*, D24.*, D30.*, D40.*, D45.*, D60.*, or CSI.*), you MUST:

1. Cross-check D1 dignity against D9 dignity for every planet whose D9 placement is in
   context. The §3.15 CSI ledger (CSI.* fact_ids) is the canonical cross-varga dignity
   matrix — cite CSI.{PLANET} when discussing cross-varga dignity transitions.

2. Vargottama status: if a planet is vargottama (same sign in D1 and D9), note this
   explicitly as a stability indicator. Mercury is vargottama in this chart.

3. Domain-mandatory varga: for domain-specific queries, the matching divisional chart
   is mandatory — answering without it is an incomplete answer:
   career/status → D10 (dasamsha)
   dharma/marriage/relationships → D9 (navamsha)
   children → D7 (saptamsha)
   parents/ancestry → D12 (dvadashamsa)
   education/knowledge → D24 (siddhamsa)
   spiritual/moksha → D20 (vimsamsha)
   health/longevity → D30 (trimsamsha)
   finance/wealth → D2 (hora)
   auspiciousness → D40 (khavedamsha)
   purity/past-karma → D45/D60 (akshavedamsha/shashtiamsha)
   If the mandatory varga context is absent from the retrieved data, write
   [EXTERNAL_COMPUTATION_REQUIRED: {varga}.{placement_description}] — do not answer D1-only.

4. Three-state dignity architecture: when discussing Saturn or any planet with different
   dignity states across D1/D9/D10, frame the full arc (D1 state → D9 state → D10 state)
   rather than any single chart in isolation. This is standard acharya practice.

5. The B11_EXPLICIT_LAYER_GATE requires MSR/UCN/CDLM/CGM/RM consultation. For domain or
   holistic queries with divisional context, also consult the §3.15 CSI surface (cross_varga_
   dignity_query results if present, or CSI.* fact_ids in chart_facts) — this is the
   canonical cross-varga reference layer.`
```

**File:** `platform/src/lib/prompts/templates/shared.ts` — `buildOpeningBlock()`

Add `DIVISIONAL_INTEGRATION_GATE` after `PREMISE_VERIFICATION_GATE`:

```ts
${PREMISE_VERIFICATION_GATE}

${DIVISIONAL_INTEGRATION_GATE}

${METHODOLOGY_INSTRUCTION}`
```

---

### D16 — Wire `DIVISIONAL_INTEGRATION_GATE` into domain-specific templates

**Files:** `platform/src/lib/prompts/templates/interpretive.ts`,
`platform/src/lib/prompts/templates/holistic.ts`,
`platform/src/lib/prompts/templates/predictive.ts`

For each file that builds its own system prompt block beyond `buildOpeningBlock()`:
import `DIVISIONAL_INTEGRATION_GATE` if not already available and verify that any
domain-synthesis instruction includes a rule that the domain-mandatory varga must be
cited. If the template already includes `buildOpeningBlock()`, the gate is already wired.
If any template builds its prompt independently, add the gate explicitly.

For `predictive.ts`, add a specific rule: "Domain-specific predictions must layer at least
2 divisional charts: D9 (always) plus the domain-mandatory varga."

---

### D17 — Update `B11_EXPLICIT_LAYER_GATE` to name CSI alongside MSR/UCN etc.

**File:** `platform/src/lib/prompts/templates/shared.ts`

Find `B11_EXPLICIT_LAYER_GATE`. Append to its text:

"For queries with divisional context present: also consult the §3.15 CSI cross-divisional
dignity ledger (cross_varga_dignity_query results or CSI.* rows in chart_facts) as the
canonical D1↔D9↔D10 cross-walk. Treating MSR/UCN/CDLM/CGM/RM as the complete synthesis
surface without referencing CSI when divisional data is in scope is a B.11 violation."

---

### D18 — Extend `DOMAIN_VARGA_MAP` with missing domain aliases

**File:** `platform/src/lib/router/retrieval_capability_spec.ts`

The existing map has keys `career`, `dharma`, `relationships`, `marriage`, etc. Add aliases
for domain codes used in MSR signals and planner output that don't yet have entries:
- `career_dharma` → copy of career + dharma (mandatory: ['D10', 'D9'])
- `moksha` → copy of spiritual (mandatory: ['D20'], secondary: ['D9', 'D60'])
- `vehicles_comforts` → (mandatory: ['D16'], secondary: ['D9'])
- `partner` → alias for marriage (mandatory: ['D9'])
- `longevity` — already present; verify D30 is mandatory
- `health_longevity` → alias for health (mandatory: ['D30'])
- `past_karma` → (mandatory: ['D60'], secondary: ['D45', 'D9'])
- `auspiciousness` → (mandatory: ['D40'], secondary: ['D9'])
- `purity` → (mandatory: ['D45'], secondary: ['D9'])

Also add `cross_varga_dignity_query` to Planning Principle 9:
"Schedule cross_varga_dignity_query at priority-1 for any holistic query and any
interpretive query mentioning planets across charts, vargottama, three-state, or
cross-varga dignity."

---

## Stream 6 — Tests and Regression

### D19 — Test suite for new deliverables

**Files:**
- `platform/src/lib/retrieve/__tests__/cross_varga_dignity_query.test.ts` (from D8)
- `platform/src/lib/retrieve/__tests__/divisional_query.test.ts` — update for expanded
  category list and new limit (D6)
- `platform/src/lib/retrieve/__tests__/vector_search.test.ts` — add tests for varga +
  section_id_prefix filters (D5)
- `platform/src/lib/prompts/__tests__/` — add test that `DIVISIONAL_INTEGRATION_GATE`
  appears in `buildOpeningBlock()` output and contains "vargottama" and "CSI"
- `platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts` — add test
  that `DOMAIN_VARGA_MAP.career_dharma.mandatory` contains both D10 and D9

Run:
```bash
cd platform
npx tsc --noEmit
npx vitest run src/lib/retrieve src/lib/router src/lib/prompts
```

All must pass with zero new TS errors.

---

## Verification sequence (run at end of all deliverables)

```bash
cd platform
npx tsc --noEmit           # 0 new errors
npx vitest run src/lib/retrieve
npx vitest run src/lib/router
npx vitest run src/lib/prompts
npx vitest run src/lib/synthesis
```

---

## Acceptance Criteria

### Stream 1 — ETL
- [ ] **AC.EF.1** — YAML v1.1 contains rows for D9.12H.TENANTS, D9.12H.DISPOSITOR, D9.12H.DISP.PLACE
- [ ] **AC.EF.2** — YAML v1.1 contains at least 4 of the 6 targeted missing sections (document which were absent from FORENSIC vs. added)
- [ ] **AC.EF.3** — `CHART_FACTS_SCHEMA_v1_0.json` enum covers all 19+ categories from both pipelines
- [ ] **AC.EF.4** — `chart_facts_extractor.py` has deprecation banner; code unchanged
- [ ] **AC.EF.5** — `chart_facts_loader.py` has deprecation banner; code unchanged
- [ ] **AC.EF.6** — `ingest_chart_facts.py` has updated EXPECTED_COUNT_MAX and deprecation note
- [ ] **AC.EF.7** — `00_ARCHITECTURE/CHART_FACTS_PIPELINE_AUDIT_v1_0.md` exists with race condition documented and re-run instructions

### Stream 2 — Retrieval
- [ ] **AC.RT.1** — `vector_search` accepts `varga` and `section_id_prefix` params; test passes
- [ ] **AC.RT.2** — `divisional_query` category list expanded; LIMIT=200; test passes
- [ ] **AC.RT.3** — `chart_facts_query` has `vargottama_only` filter; test passes
- [ ] **AC.RT.4** — `cross_varga_dignity_query` tool exists, exported, in RCS; 3 tests pass
- [ ] **AC.RT.5** — Planning Principle 9 updated with `cross_varga_dignity_query` scheduling rule
- [ ] **AC.RT.6** — Example 2c added to planner; Example 6 (holistic) includes `cross_varga_dignity_query`

### Stream 3 — Chunker
- [ ] **AC.CH.1** — `l1_fact.py` adds `varga` metadata for all §3.x chunks; test passes
- [ ] **AC.CH.2** — `forensic_chunker.py` verified to produce ≥1 chunk for each §3.1–§3.15

### Stream 4 — L2.5
- [ ] **AC.L2.1** — MSR has 15 new signals (SIG.MSR.500–514); each has v6_ids_consumed referencing FORENSIC §3.x; version bumped
- [ ] **AC.L2.2** — CGM has DVS nodes for D24, D30, D40, D45, D60 (lagna + 9 planets each); 9 DIVISIONAL_TRANSITION edges from CSI; version bumped
- [ ] **AC.L2.3** — RM has 5 new resonances (RM.30–34) citing MSR signal_ids; version bumped

### Stream 5 — Synthesis
- [ ] **AC.SY.1** — `DIVISIONAL_INTEGRATION_GATE` exported from shared.ts; wired into `buildOpeningBlock()`; contains "vargottama", "CSI", "three-state"
- [ ] **AC.SY.2** — `B11_EXPLICIT_LAYER_GATE` updated to name CSI ledger
- [ ] **AC.SY.3** — `DOMAIN_VARGA_MAP` has 8 new alias keys (career_dharma, moksha, vehicles_comforts, partner, health_longevity, past_karma, auspiciousness, purity)

### Regression
- [ ] **AC.RG.1** — `npx tsc --noEmit`: 0 new TS errors
- [ ] **AC.RG.2** — All retrieve/router/prompts/synthesis vitest suites pass

---

## Manual steps for the native (Cloud SQL Auth Proxy required)

Execute THESE after the brief is marked COMPLETE:

```bash
# Step 1: start proxy
cloud-sql-proxy madhav-astrology:asia-south1:marsys-prod

# Step 2: audit current state BEFORE re-ingest
psql $DATABASE_URL -c "
  SELECT divisional_chart, count(*) 
  FROM chart_facts 
  WHERE is_stale = false 
  GROUP BY 1 ORDER BY 1;
" > before_reingestion.tsv

# Step 3: upload v1.1 YAML + schema to GCS
gsutil cp 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml \
  gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml
gsutil cp 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json \
  gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json

# Step 4: run the unified YAML pipeline
cd platform/python-sidecar
DATABASE_URL=postgresql://... python -m pipeline.ingest_chart_facts

# Step 5: verify post-ingest
psql $DATABASE_URL -c "
  SELECT divisional_chart, count(*) 
  FROM chart_facts 
  WHERE is_stale = false 
  GROUP BY 1 ORDER BY 1;
" > after_reingestion.tsv

# Step 6: expected — D2 through D60 each have ≥2 rows; D9 has ≥14 rows

# Step 7: re-chunk FORENSIC (adds varga metadata to new chunks)
DATABASE_URL=postgresql://... python -m pipeline.chunkers.forensic_chunker

# Step 8: re-embed new/changed chunks
DATABASE_URL=postgresql://... python -m pipeline.embed  # or whatever the embed script is named

# Step 9: verify chunk + embedding counts
psql $DATABASE_URL -c "
  SELECT metadata->>'varga', count(*) 
  FROM rag_chunks 
  WHERE doc_type = 'l1_fact' AND is_stale = false
  GROUP BY 1 ORDER BY 1;
"
# Expected: D2 through D60 each have ≥1 chunk; D9 has ≥3 chunks

# Step 10: end-to-end smoke test (6 queries via /rag/synthesize or /api/chat/consume)
# Query 1: "What is my D9 navamsha lagna?"  → must cite D9.LAGNA fact_id
# Query 2: "What does D10 show for my career?"  → must cite D10.* fact_ids
# Query 3: "Which planets are vargottama in my chart?"  → must identify Mercury
# Query 4: "Compare D1 and D9 dignity for Saturn"  → must cite CSI.SATURN + D9.SATURN + SIG.MSR.501
# Query 5: "What does D24 show about my education?"  → must cite D24.* + SIG.MSR.506
# Query 6: "Do a holistic analysis" → must show D9, D10, cross_varga_dignity_query results
```

---

## may_touch
```
01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml
01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json
025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
025_HOLISTIC_SYNTHESIS/UCN_v4_0.md
025_HOLISTIC_SYNTHESIS/CGM_v9_0.md
025_HOLISTIC_SYNTHESIS/RM_v2_0.md
025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md
00_ARCHITECTURE/CHART_FACTS_PIPELINE_AUDIT_v1_0.md
platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py
platform/python-sidecar/pipeline/loaders/chart_facts_loader.py
platform/python-sidecar/pipeline/ingest_chart_facts.py
platform/python-sidecar/rag/chunkers/l1_fact.py
platform/python-sidecar/pipeline/chunkers/forensic_chunker.py
platform/src/lib/retrieve/divisional_query.ts
platform/src/lib/retrieve/chart_facts_query.ts
platform/src/lib/retrieve/vector_search.ts
platform/src/lib/retrieve/cross_varga_dignity_query.ts
platform/src/lib/retrieve/index.ts
platform/src/lib/retrieve/__tests__/cross_varga_dignity_query.test.ts
platform/src/lib/retrieve/__tests__/divisional_query.test.ts
platform/src/lib/retrieve/__tests__/vector_search.test.ts
platform/src/lib/router/retrieval_capability_spec.ts
platform/src/lib/router/planner.ts
platform/src/lib/router/per_tool_planner.ts
platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts
platform/src/lib/prompts/templates/shared.ts
platform/src/lib/prompts/templates/interpretive.ts
platform/src/lib/prompts/templates/holistic.ts
platform/src/lib/prompts/templates/predictive.ts
platform/src/lib/prompts/__tests__/
```

## must_not_touch
```
01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
platform/migrations/**
platform/supabase/**
platform/src/app/api/**
platform/src/lib/audit/**
platform/src/lib/checkpoints/**
06_LEARNING_LAYER/**
00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
00_ARCHITECTURE/CURRENT_STATE_v1_0.md
00_ARCHITECTURE/SESSION_LOG.md
```

---

## Session close

When all acceptance criteria pass:
1. Set `status: COMPLETE` in this file's frontmatter.
2. Move this file to `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_VARGA_ETL_FULL_S1.md`
   per ROOT_FILE_POLICY §3.
3. Update `CURRENT_STATE_v1_0.md` to record VARGA-ETL-FULL-S1 COMPLETE under Pre-M5 fixes.

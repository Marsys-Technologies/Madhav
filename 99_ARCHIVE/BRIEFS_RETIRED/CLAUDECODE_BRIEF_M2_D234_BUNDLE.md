---
brief_id: M2_D234_BUNDLE
karn_session_name: KARN-W5-R2-D234-BUNDLE
wave: 5
stream: B
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 4 close
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (2 Python chunkers + 3 TypeScript retrieval tools + tests + deploy)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §B5
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: none (domain_report already chunked from Pre-KARN-4; L4/L5 chunkers new)
  blocks: M2_D1_COMPOSITION_RULES (W6-R1 adds composition rules for these tools)
parallel_stream_note: |
  Two other Wave-5 briefs run concurrently:
  - KARN-W5-R1-TEMPORAL-EXTENSION (Stream B — modifies temporal.ts only; does NOT touch index.ts)
  - KARN-W5-R3-RES-CON-EXPANSION (Stream C — discovery only, no code)
  W5-R2 appends to index.ts and router/prompt.ts using the append-only protocol.
  W5-R1 does NOT modify index.ts or prompt.ts for its temporal changes (temporal is already
  registered). However, W5-R1 DOES append a guidance block to prompt.ts.
  Coordinate with W5-R1 on prompt.ts: if W5-R1 commits before you, ensure you do not
  overwrite its Temporal Extension Guidance block. Append after, not instead of.
  If W5-R2 commits before W5-R1: W5-R1 will append after. No coordination needed.
estimated_time: 1–1.5 days single Claude Code session

carry_forward_notes:
  - "DOMAIN REPORTS (L3): doc_type='domain_report' chunks ALREADY EXIST in rag_chunks from
     Pre-KARN-4. Chunker: platform/python-sidecar/rag/chunkers/domain_report.py (existing).
     domain_report_query.ts only needs to query rag_chunks — NO new chunking needed for L3."
  - "REMEDIAL CODEX (L4): source files are 04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md +
     REMEDIAL_CODEX_v2_0_PART2.md. NO chunker exists yet. Create remedial_chunker.py
     (new), wire into pipeline/main.py, run ingest to populate rag_chunks with doc_type='l4_remedial'."
  - "LIFETIME TIMELINE (L5): source file is 05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md.
     NO chunker exists yet. Create timeline_chunker.py (new), wire into pipeline/main.py,
     run ingest to populate rag_chunks with doc_type='l5_timeline'."
  - "RETRIEVAL_TOOLS baseline = 14. After this session: 17 (adding domain_report_query,
     remedial_codex_query, timeline_query)."
  - "Integration test count assertion: platform/src/lib/retrieve/__tests__/integration.test.ts
     was updated to expect 14 in W4-R2. Update to 17 in this session."
  - "ToolBundle correct pattern: served_from_cache / result_hash / schema_version: '1.0'.
     Study temporal.ts or chart_facts_query.ts for the exact ToolBundle construction pattern."
  - "value_json field names in chart_facts (do NOT confuse with rag_chunks):
     shadbala total → forensic_rupas; bhava_bala → jh_rupas; yoga shape → {type,source,key_configuration}.
     This session queries rag_chunks (content field), not chart_facts — these corrections
     are informational only; not directly applicable here."
  - "Pre-existing Jest ESM baseline: 13 suites fail. Vitest baseline: ~979 passing (W4-R2 end-state).
     Do not count pre-existing failures as regressions."
  - "domain_report source files: 03_DOMAIN_REPORTS/REPORT_*.md (9 files, v1_1 versions are CURRENT).
     The doc_type in rag_chunks is 'domain_report'. Confirm by: SELECT doc_type, count(*)
     FROM rag_chunks WHERE doc_type='domain_report' GROUP BY doc_type;"
  - "Remedial codex covers: planetary propitiation, gemology, mantra (Part 1) + yantra, devata,
     lifestyle protocols (Part 2). H2 boundary chunking. Use doc_type='l4_remedial'."
  - "Lifetime timeline covers: life arc 1984–2044 by MD phases. H2 boundary. doc_type='l5_timeline'.
     Note: LIFETIME_TIMELINE_v1_0.md status is CLOSED (not CURRENT) — it is the authoritative
     historical synthesis, appropriate for retrieval even in CLOSED status."

scope_summary: |
  Three new retrieval tools surfacing L3 (domain reports), L4 (remedial codex), and
  L5 (lifetime timeline) corpus layers. Two require new Python chunkers; one queries
  existing rag_chunks.

  SESSION WORK:
  A. Python chunkers (sidecar work — Stream A territory, but scoped here as integrated work):
     1. Create platform/python-sidecar/rag/chunkers/remedial_chunker.py
        - Source: 04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md + PART2.md
        - doc_type: 'l4_remedial'
        - Boundary: H2 (## heading), split at H3 if >1500 tokens
        - Apply entity_refs injection pattern (W2-R3 / W3-R1 precedent) for P1 compliance
     2. Create platform/python-sidecar/rag/chunkers/timeline_chunker.py
        - Source: 05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md
        - doc_type: 'l5_timeline'
        - Boundary: H2 (## §N headings), split at H3 if >1500 tokens
        - The timeline mixes L1 facts (dasha dates) with L2.5 interpretive text —
          use the L1/L2.5 bridge marker pattern (W3-R1 lel_chunker precedent)
     3. Wire both chunkers into platform/python-sidecar/pipeline/main.py
     4. Run ingest to populate rag_chunks

  B. TypeScript retrieval tools:
     1. domain_report_query.ts — queries rag_chunks where doc_type='domain_report',
        filtered by domain name(s) from QueryPlan.domains
     2. remedial_codex_query.ts — queries rag_chunks where doc_type='l4_remedial',
        optionally filtered by planet or practice type keyword
     3. timeline_query.ts — queries rag_chunks where doc_type='l5_timeline',
        optionally filtered by time window or dasha name keyword

  Each TypeScript tool:
  - Queries rag_chunks via the project's DB client (same pattern as existing tools)
  - Is registered in RETRIEVAL_TOOLS + CAPABILITY_MANIFEST
  - Has ≥5 test cases
  - Has a tool-guidance block appended to router/prompt.ts

may_touch:
  # Python sidecar (chunkers + wiring)
  - platform/python-sidecar/rag/chunkers/remedial_chunker.py                 # CREATE
  - platform/python-sidecar/rag/chunkers/timeline_chunker.py                 # CREATE
  - platform/python-sidecar/rag/chunkers/__tests__/test_remedial_chunker.py  # CREATE
  - platform/python-sidecar/rag/chunkers/__tests__/test_timeline_chunker.py  # CREATE
  - platform/python-sidecar/pipeline/main.py                                 # MODIFY — wire new chunkers
  # TypeScript retrieval tools
  - platform/src/lib/retrieve/domain_report_query.ts                         # CREATE
  - platform/src/lib/retrieve/remedial_codex_query.ts                        # CREATE
  - platform/src/lib/retrieve/timeline_query.ts                              # CREATE
  - platform/src/lib/retrieve/__tests__/domain_report_query.test.ts          # CREATE
  - platform/src/lib/retrieve/__tests__/remedial_codex_query.test.ts         # CREATE
  - platform/src/lib/retrieve/__tests__/timeline_query.test.ts               # CREATE
  - platform/src/lib/retrieve/index.ts                                       # MODIFY — append 3 imports + 3 RETRIEVAL_TOOLS entries
  - platform/src/lib/retrieve/__tests__/integration.test.ts                  # MODIFY — update tool count 14 → 17
  - platform/src/lib/router/types.ts                                         # MODIFY — add DomainReportQueryInput etc. if needed
  - platform/src/lib/router/prompt.ts                                        # MODIFY — append 3 tool-guidance blocks
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json                                 # MODIFY — append 3 tool entries (append-only)
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_D234_BUNDLE.md               # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_D234_VERIFICATION_<DATE>.txt                   # CREATE

must_not_touch:
  - platform/src/lib/retrieve/temporal.ts                                     # W5-R1 territory
  - platform/src/lib/retrieve/chart_facts_query.ts
  - platform/src/lib/retrieve/kp_query.ts
  - platform/src/lib/retrieve/saham_query.ts
  - platform/src/lib/retrieve/divisional_query.ts
  - platform/src/lib/retrieve/msr_sql.ts
  - platform/src/lib/retrieve/vector_search.ts
  - platform/src/lib/retrieve/cgm_graph_walk.ts
  - platform/src/lib/retrieve/pattern_register.ts
  - platform/src/lib/retrieve/resonance_register.ts
  - platform/src/lib/retrieve/cluster_atlas.ts
  - platform/src/lib/retrieve/contradiction_register.ts
  - platform/python-sidecar/rag/chunkers/domain_report.py                    # existing chunker — do not modify
  - platform/python-sidecar/rag/chunkers/ucn_section.py
  - platform/python-sidecar/rag/chunkers/cgm_node.py
  - platform/python-sidecar/rag/chunkers/lel_chunker.py
  - platform/migrations/**
  - platform/src/app/**
  - platform/src/components/**
  - 035_DISCOVERY_LAYER/**
  - 04_REMEDIAL_CODEX/**                                                      # source files, read-only
  - 05_TEMPORAL_ENGINES/**                                                    # source files, read-only
  - 03_DOMAIN_REPORTS/**                                                      # source files, read-only
---

# KARN-W5-R2-D234-BUNDLE — Execution Brief

## §0 — Context

This is an autonomous Claude Code session. Read this entire brief before writing any code.
Execute §1 (pre-flight) before touching anything. Halt immediately on any pre-flight failure.

**Parent plan:** `M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §B5`.

You are building three L3/L4/L5 retrieval tools. L3 (domain reports) already has chunks in
rag_chunks — you only need the TypeScript tool. L4 (remedial codex) and L5 (lifetime timeline)
have no chunkers yet — you create Python chunkers, run them to ingest, then build the TS tools.

This is a dual-scope session: Python sidecar work (chunkers) first, then TypeScript tools.
Complete the chunkers and ingest before starting the TypeScript work, so the tools have data
to query during verification.

---

## §1 — Pre-flight self-diagnostics

```bash
# PF.1 — Branch check
git branch --show-current
# Expected: redesign/r0-foundation. Any other → HALT.

# PF.2 — Working tree clean
git status --short
# Expected: clean or only files in may_touch list.

# PF.3 — Confirm domain_report chunks already in rag_chunks
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT doc_type, COUNT(*) FROM rag_chunks WHERE doc_type='domain_report' GROUP BY doc_type;"
# Expected: doc_type='domain_report', count ≥ 36.
# If 0 → domain_report chunker needs to be re-run first (unlikely; see §1.5).

# PF.4 — Confirm L4/L5 chunks do NOT yet exist (this session creates them)
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT doc_type, COUNT(*) FROM rag_chunks
   WHERE doc_type IN ('l4_remedial','l5_timeline') GROUP BY doc_type;"
# Expected: 0 rows (these doc_types don't exist yet). If rows DO exist, a prior
# attempt may have run. Record counts as pre-state — do not re-ingest blindly.

# PF.5 — Inspect source files
wc -l 04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md \
       04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART2.md \
       05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md
# Record file sizes (lines). Understanding the source helps calibrate expected chunk counts.

# PF.6 — Count H2 boundaries in source files (expected chunk counts)
grep -c "^## " 04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md
grep -c "^## " 04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART2.md
grep -c "^## " 05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md
# This gives minimum expected chunk counts per file before any H3 splits.

# PF.7 — Read existing chunker for pattern reference
cat platform/python-sidecar/rag/chunkers/lel_chunker.py
# This is the most recently-authored chunker and uses the bridge-marker + entity_refs patterns.
# Mirror its structure for remedial_chunker.py and timeline_chunker.py.

# PF.8 — Inspect pipeline/main.py to understand chunker registration pattern
grep -n "lel_chunker\|domain_report\|chunker" platform/python-sidecar/pipeline/main.py | head -20
# Understand how to add new chunkers to the registry.

# PF.9 — TypeScript + vitest baseline
cd platform && npx vitest run --reporter=verbose 2>&1 | tail -10
# Record pass/fail counts.

# PF.10 — Confirm RETRIEVAL_TOOLS count is currently 14
grep -c "\.tool," platform/src/lib/retrieve/index.ts 2>/dev/null || \
  grep -c "\.tool$" platform/src/lib/retrieve/index.ts
# Expected: 14.

# PF.11 — Cloud Run current revision
gcloud run revisions list --service=amjis-web --region=asia-south1 \
  --limit=3 --format="table(name,status.conditions[0].type)"
```

### §1.5 — If PF.3 shows domain_report count is 0

If domain_report chunks are missing (unusual — Pre-KARN-4 should have ingested them):
```bash
cd platform/python-sidecar && python3 -m pipeline.main --doc-type domain_report
```
Confirm chunks appear in rag_chunks before continuing. Document in closing summary.

---

## §2 — Implementation: Phase A — Python chunkers

Complete Phase A before starting Phase B (TypeScript tools). The TS tools need populated
rag_chunks for their verification steps.

### §2.1 — remedial_chunker.py

**Create `platform/python-sidecar/rag/chunkers/remedial_chunker.py`:**

Follow `lel_chunker.py` structure exactly. Key parameters:

```python
"""
chunkers.remedial_chunker — Doc-type l4_remedial: Remedial Codex chunker.
Wave 5 M2-D234-BUNDLE. Source: REMEDIAL_CODEX_v2_0_PART1.md + PART2.md.
Boundary: H2 (^## ); split at H3 if > 1500 tokens.
Doc-type: l4_remedial.
Layer: L4.
Stop condition: STOP if either source file produces 0 chunks.
"""

SOURCE_FILES = [
    "04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md",
    "04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART2.md",
]
DOC_TYPE = "l4_remedial"
LAYER = "L4"
MAX_TOKENS = 1500
```

**P1 compliance note:** The remedial codex is L4 content — it contains synthesis-level
prescriptive text (not L1 facts). The L1/L2.5 tension from lel_chunker does not apply here
because L4 is explicitly synthesis. P1 (`p1_layer_separation`) should accept L4 content
without issues. If P1 triggers false positives on L4 material, add a doc_type bypass:
check how `domain_report.py` handles it (domain_report is also synthesis-layer content).

**Entity refs:** Remedial codex mentions planets frequently (Mercury, Saturn, Mars, etc.).
Inject `entity_refs:` lines using the planet-name scanning pattern from W3-R1 where P1
requires them. If P1 doesn't trigger on L4, skip injection.

**chunk_id format:** `REMEDIAL_CODEX_v2_0_PART{n}_{i:03d}` where n is 1 or 2, i is
sequential index within that part file.

**canonical_id:** `REMEDIAL_CODEX_v2_0_PART{n}`
**source_version:** `2.0`

---

### §2.2 — timeline_chunker.py

**Create `platform/python-sidecar/rag/chunkers/timeline_chunker.py`:**

```python
"""
chunkers.timeline_chunker — Doc-type l5_timeline: Lifetime Timeline chunker.
Wave 5 M2-D234-BUNDLE. Source: LIFETIME_TIMELINE_v1_0.md.
Boundary: H2 (^## §N ); split at H3 if > 1500 tokens.
Doc-type: l5_timeline.
Layer: L5.
Note: Timeline mixes L1 dasha dates with L2.5 interpretive text.
      Use the L1/L2.5 bridge-marker pattern from lel_chunker for P1 compliance.
Stop condition: STOP if source file produces 0 chunks.
"""

SOURCE_FILES = [
    "05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md",
]
DOC_TYPE = "l5_timeline"
LAYER = "L5"
MAX_TOKENS = 1500
```

**P1 compliance:** The timeline file has YAML frontmatter with `status: CLOSED`. This
is the archive status, not an ingestion blocker — ingest it. CLOSED means the document
is finalized, not that it should be excluded from retrieval.

**Bridge-marker pattern:** If a chunk contains a mix of L1 dates (e.g., "Jupiter MD:
1984-02-05 → 1991-08-21") and L2.5 interpretive text, prepend the bridge marker:
`# [L1 dasha timeline] → [L2.5 activation pattern embedded]`

**chunk_id format:** `LIFETIME_TIMELINE_v1_0_{i:03d}`
**canonical_id:** `LIFETIME_TIMELINE_v1_0`
**source_version:** `1.0`

---

### §2.3 — Wire into pipeline/main.py

Extend `platform/python-sidecar/pipeline/main.py` to register the two new chunkers,
following the pattern used for `lel_chunker`. Typically this means adding entries to
a `_build_chunker_registry()` function or equivalent dict.

---

### §2.4 — Run ingest + verify chunk counts

```bash
cd platform/python-sidecar

# Ingest L4 remedial
python3 -m pipeline.main --doc-type l4_remedial
# or: python3 -m rag.chunkers.remedial_chunker (if standalone entry point)

# Ingest L5 timeline
python3 -m pipeline.main --doc-type l5_timeline

# Verify DB counts
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT doc_type, COUNT(*) FROM rag_chunks
   WHERE doc_type IN ('domain_report','l4_remedial','l5_timeline')
   GROUP BY doc_type ORDER BY doc_type;"
```

**Expected minimum counts:**
- `domain_report`: ≥ 36 (unchanged from pre-state)
- `l4_remedial`: ≥ 10 (PART1 + PART2 each have multiple H2 sections)
- `l5_timeline`: ≥ 5 (timeline has several phase sections)

If l4_remedial or l5_timeline = 0 after ingest → investigate and fix chunker before
continuing to Phase B. Do not build TS tools against empty rag_chunks.

**Note on embeddings:** Standalone chunker runs typically do not trigger Vertex AI
embedding (same pattern as W3-R1). New chunks will have NULL embedding vectors.
This is acceptable — document in closing summary. Embeddings will land on next full
pipeline build.

---

### §2.5 — Python tests

**Create `platform/python-sidecar/rag/chunkers/__tests__/test_remedial_chunker.py`:**
≥ 5 tests:
1. chunker returns ≥ 10 chunks for both PART1 + PART2 combined
2. all chunks have doc_type == 'l4_remedial'
3. all chunks have layer == 'L4'
4. no chunk exceeds 1500 tokens (count_tokens)
5. chunk_ids are unique across both parts

**Create `platform/python-sidecar/rag/chunkers/__tests__/test_timeline_chunker.py`:**
≥ 5 tests:
1. chunker returns ≥ 5 chunks from LIFETIME_TIMELINE_v1_0.md
2. all chunks have doc_type == 'l5_timeline'
3. all chunks have layer == 'L5'
4. no chunk exceeds 1500 tokens
5. chunk_ids are unique

---

## §3 — Implementation: Phase B — TypeScript retrieval tools

Begin Phase B only after Phase A ingest is confirmed (rag_chunks counts > 0 for l4_remedial
and l5_timeline).

### §3.1 — DB query pattern for rag_chunks

Study `platform/src/lib/retrieve/vector_search.ts` (or whichever existing tool queries
rag_chunks directly via SQL) to understand:
- How to query the `rag_chunks` table
- Column names: `id`, `doc_type`, `layer`, `content`, `chunk_id`, `source_doc`,
  `canonical_id`, `source_version`, `metadata` (JSONB)

The three new tools all query `rag_chunks` by `doc_type` with optional keyword/metadata
filters. They do NOT do vector search — they query by doc_type + filters only.

---

### §3.2 — domain_report_query.ts

**Create `platform/src/lib/retrieve/domain_report_query.ts`:**

```typescript
/**
 * MARSYS-JIS Stream B — Tool: domain_report_query (M2-D.2)
 *
 * Queries rag_chunks where doc_type='domain_report' and returns L3 domain-report
 * content for the specified domain(s). The 9 domain reports cover: career_dharma,
 * children, financial, health_longevity, parents, psychology_mind, relationships,
 * spiritual, travel.
 */
```

Parameters:
```typescript
export interface DomainReportQueryInput {
  domains?: string[]      // e.g. ['career', 'relationships'] — filter by domain name
  keyword?: string        // free-text keyword to match in chunk content (ILIKE)
  limit?: number          // default 10
}
```

Query logic:
- `WHERE doc_type = 'domain_report'`
- If `domains` provided: filter with `(content ILIKE '%career%' OR content ILIKE '%dharma%')`
  or match against `source_doc` column (which contains the REPORT_* filename). Use the
  source_doc approach: `source_doc ILIKE ANY(ARRAY[...])` with the domain name.
  Check the actual column name by inspecting `\d rag_chunks` in the DB.
- If `keyword` provided: `content ILIKE '%{keyword}%'`
- ORDER BY `id` (or `chunk_id`) to get stable ordering
- LIMIT: default 10, max 25

Map domains to source_doc patterns:
```typescript
const DOMAIN_TO_PATTERN: Record<string, string> = {
  'career': '%CAREER_DHARMA%',
  'dharma': '%CAREER_DHARMA%',
  'children': '%CHILDREN%',
  'financial': '%FINANCIAL%',
  'finance': '%FINANCIAL%',
  'wealth': '%FINANCIAL%',
  'health': '%HEALTH_LONGEVITY%',
  'longevity': '%HEALTH_LONGEVITY%',
  'parents': '%PARENTS%',
  'psychology': '%PSYCHOLOGY_MIND%',
  'mind': '%PSYCHOLOGY_MIND%',
  'relationships': '%RELATIONSHIPS%',
  'marriage': '%RELATIONSHIPS%',
  'spiritual': '%SPIRITUAL%',
  'travel': '%TRAVEL%',
}
```

Result shape per item:
```typescript
{
  content: row.content,          // the chunk text
  doc_type: row.doc_type,
  source_doc: row.source_doc,
  chunk_id: row.chunk_id,
}
```

ToolBundle construction: mirror `chart_facts_query.ts` pattern exactly for `served_from_cache`,
`result_hash`, `schema_version: '1.0'`.

source_canonical_id per result: extract from chunk's `canonical_id` column if present,
else use the REPORT filename prefix (e.g., 'REPORT_CAREER_DHARMA').

---

### §3.3 — remedial_codex_query.ts

**Create `platform/src/lib/retrieve/remedial_codex_query.ts`:**

```typescript
/**
 * MARSYS-JIS Stream B — Tool: remedial_codex_query (M2-D.3)
 *
 * Queries rag_chunks where doc_type='l4_remedial' and returns L4 remedial
 * prescriptions — planetary propitiation, gemology, mantra, yantra, devata,
 * lifestyle protocols.
 */
```

Parameters:
```typescript
export interface RemedialCodexQueryInput {
  planet?: string       // e.g. 'Mercury', 'Saturn', 'Mars' — filter to planet-specific remedies
  practice_type?: 'gemstone' | 'mantra' | 'yantra' | 'devata' | 'dinacharya' | 'propit'
  keyword?: string      // free-text keyword (ILIKE on content)
  limit?: number        // default 8
}
```

Query logic:
- `WHERE doc_type = 'l4_remedial'`
- If `planet`: `content ILIKE '%{planet}%'`
- If `practice_type`: `content ILIKE '%{practice_type_keyword}%'` (map 'gemstone' → 'gem%',
  'mantra' → 'mantra%', etc.)
- If `keyword`: `content ILIKE '%{keyword}%'`
- LIMIT: default 8, max 20

source_canonical_id: `REMEDIAL_CODEX_v2_0_PART1` or `REMEDIAL_CODEX_v2_0_PART2` —
derive from chunk's `canonical_id` column or `source_doc` column.

---

### §3.4 — timeline_query.ts

**Create `platform/src/lib/retrieve/timeline_query.ts`:**

```typescript
/**
 * MARSYS-JIS Stream B — Tool: timeline_query (M2-D.4)
 *
 * Queries rag_chunks where doc_type='l5_timeline' and returns L5 lifetime
 * timeline content — dasha phase arcs, event windows, structural inflection points.
 */
```

Parameters:
```typescript
export interface TimelineQueryInput {
  dasha_name?: string    // e.g. 'Mercury MD', 'Ketu MD', 'Saturn MD' — filter by dasha name
  keyword?: string       // free-text keyword (ILIKE on content)
  limit?: number         // default 8
}
```

Query logic:
- `WHERE doc_type = 'l5_timeline'`
- If `dasha_name`: `content ILIKE '%{dasha_name}%'`
- If `keyword`: `content ILIKE '%{keyword}%'`
- LIMIT: default 8, max 15

source_canonical_id: `LIFETIME_TIMELINE_v1_0`

**Important:** When the classifier uses `dasha_name`, the correct next dasha is
**Ketu MD** (2027-08-21 → 2034-08-21). Never suggest Saturn MD as upcoming.

---

### §3.5 — Update index.ts

Append to `platform/src/lib/retrieve/index.ts` (append-only, after existing Wave-4 entries):

```typescript
// Wave 5 additions — M2-D234-BUNDLE
import * as domainReportQuery from './domain_report_query'
import * as remedialCodexQuery from './remedial_codex_query'
import * as timelineQuery from './timeline_query'
```

Push three tools into RETRIEVAL_TOOLS array (append after existing). RETRIEVAL_TOOLS count: 14 → 17.

Also update `platform/src/lib/retrieve/__tests__/integration.test.ts`:
```typescript
// Change: expect(RETRIEVAL_TOOLS).toHaveLength(14)
// To:     expect(RETRIEVAL_TOOLS).toHaveLength(17)
```

---

### §3.6 — Update router/prompt.ts

Append three tool-guidance blocks after the last existing guidance block (and after
the Temporal Extension Guidance if W5-R1 already committed it):

```
## Domain Report Query Guidance (domain_report_query tool)
Authorize `domain_report_query` for queries about:
- Domain synthesis: "Tell me about my career", "relationships overview", "health summary"
- Any query with domain scope + synthesis expectation (not just facts)
- "domain report", "what does my chart say about [domain]", "[domain] analysis"
Domains recognized: career, dharma, children, financial, wealth, health, longevity,
parents, psychology, mind, relationships, marriage, spiritual, travel.
Set `domains` param to the matched domain(s) from QueryPlan.domains.
Set `keyword` if query mentions a specific theme within the domain.

## Remedial Codex Query Guidance (remedial_codex_query tool)
Authorize `remedial_codex_query` for queries about:
- Remedial prescriptions: "What remedies for Saturn?", "Should I wear a gem?",
  "Mantra for Mercury", "What yantra is prescribed?"
- Practice types: gemstone, mantra, yantra, devata, dinacharya, propitiation
- Any query containing "remedy", "remedial", "propitiate", "gem", "mantra", "yantra"
Set `planet` param when a specific planet's remedy is asked.
Set `practice_type` when a specific practice category is mentioned.

## Timeline Query Guidance (timeline_query tool)
Authorize `timeline_query` for queries about:
- Life-arc synthesis: "What happens in my Ketu dasha?", "Ketu MD arc",
  "What does my Mercury dasha show?", "life phase from 2027"
- Long-horizon windows: "next 10 years", "my Saturn MD", "post-2027"
- Any query that asks about a specific dasha period's arc or structural theme
Set `dasha_name` param (e.g. 'Mercury MD', 'Ketu MD', 'Venus MD').
IMPORTANT: The next MD after Mercury is KETU MD (2027-08-21 → 2034-08-21).
Never suggest Saturn MD as upcoming — Saturn MD was historical (1992-2010).
```

---

### §3.7 — TypeScript tests

**Create `platform/src/lib/retrieve/__tests__/domain_report_query.test.ts`:** ≥ 5 tests:
1. retrieve() with `domains: ['career']` → results.length > 0, all results from CAREER_DHARMA source
2. retrieve() with `domains: ['relationships']` → results from RELATIONSHIPS source
3. retrieve() with no params → returns ≥ 1 result (sample from any domain report)
4. ToolBundle shape: tool_name='domain_report_query', served_from_cache=false, schema_version='1.0'
5. retrieve() with unknown domain → returns empty results without error

**Create `platform/src/lib/retrieve/__tests__/remedial_codex_query.test.ts`:** ≥ 5 tests:
1. retrieve() with `planet: 'Mercury'` → results.length > 0
2. retrieve() with `practice_type: 'mantra'` → results contain mantra-related content
3. retrieve() with no params → returns ≥ 1 result
4. ToolBundle shape correct
5. retrieve() with `planet: 'NonExistentPlanet'` → empty results without error

**Create `platform/src/lib/retrieve/__tests__/timeline_query.test.ts`:** ≥ 5 tests:
1. retrieve() with `dasha_name: 'Mercury MD'` → results > 0
2. retrieve() with `dasha_name: 'Ketu MD'` → results > 0
3. retrieve() with no params → returns ≥ 1 result
4. ToolBundle shape correct
5. retrieve() with `keyword: 'Saturn MD'` → results > 0 (historical Saturn MD arc exists)

**Mocking:** If DB is not available in test environment, mock the DB client following the
pattern in `msr_sql.test.ts` or `chart_facts_query.test.ts`.

---

## §4 — Acceptance criteria

### AC.1 — Branch state
`git branch --show-current` returns `redesign/r0-foundation`.

### AC.2 — Two new Python chunkers created
```bash
ls platform/python-sidecar/rag/chunkers/remedial_chunker.py
ls platform/python-sidecar/rag/chunkers/timeline_chunker.py
```
Both files exist.

### AC.3 — L4/L5 chunks in rag_chunks
```sql
SELECT doc_type, COUNT(*) FROM rag_chunks
WHERE doc_type IN ('l4_remedial','l5_timeline') GROUP BY doc_type;
```
`l4_remedial` ≥ 10 rows. `l5_timeline` ≥ 5 rows.

### AC.4 — domain_report already chunked (no regression)
```sql
SELECT COUNT(*) FROM rag_chunks WHERE doc_type='domain_report';
```
Count ≥ 36 (unchanged from pre-state).

### AC.5 — Three TypeScript tool files created
```bash
ls platform/src/lib/retrieve/domain_report_query.ts
ls platform/src/lib/retrieve/remedial_codex_query.ts
ls platform/src/lib/retrieve/timeline_query.ts
```
All three exist.

### AC.6 — RETRIEVAL_TOOLS count updated to 17
```bash
# in platform/src/lib/retrieve/__tests__/integration.test.ts:
grep "toHaveLength" platform/src/lib/retrieve/__tests__/integration.test.ts
```
Shows `toHaveLength(17)`.

### AC.7 — Classifier prompt has three guidance blocks
```bash
grep -c "domain_report_query\|remedial_codex_query\|timeline_query" platform/src/lib/router/prompt.ts
```
Returns ≥ 6 (each tool name appears in its guidance block + tool list).

### AC.8 — Python tests: ≥ 10 passing (5 per new chunker)
```bash
cd platform/python-sidecar && python3 -m pytest rag/chunkers/__tests__/test_remedial_chunker.py \
  rag/chunkers/__tests__/test_timeline_chunker.py -v 2>&1 | tail -15
```
All 10+ tests pass.

### AC.9 — TypeScript tests: ≥ 15 passing (5 per new tool)
```bash
cd platform && npx vitest run \
  src/lib/retrieve/__tests__/domain_report_query.test.ts \
  src/lib/retrieve/__tests__/remedial_codex_query.test.ts \
  src/lib/retrieve/__tests__/timeline_query.test.ts \
  --reporter=verbose 2>&1 | tail -15
```
All 15+ tests pass. No new failures vs baseline.

### AC.10 — Full vitest suite: no new failures
```bash
cd platform && npx vitest run 2>&1 | tail -5
```
Pass count ≥ pre-flight baseline. Fail count = 13 (pre-existing only).

### AC.11 — TypeScript compiles clean
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v node_modules | grep "error" | head -10
```
No new errors.

### AC.12 — CAPABILITY_MANIFEST updated
```bash
grep -c "domain_report_query\|remedial_codex_query\|timeline_query" 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
```
Returns ≥ 3.

### AC.13 — Deploy: new Cloud Run revision serving 100%
```bash
bash platform/scripts/cloud_build_submit.sh
gcloud run revisions list --service=amjis-web --region=asia-south1 \
  --limit=3 --format="table(name,status.conditions[0].type)"
```
New revision ACTIVE at 100%.

### AC.14 — Live smoke: domain_report_query fires on a domain query
After deploy, issue a career domain query and confirm `domain_report_query` appears in
tools fired (check audit_events or query_plans table for a recent row).

---

## §5 — Halt conditions

Halt immediately with a 5-line halt summary if:

1. **PF.1 fails:** Wrong branch.
2. **L4/L5 ingest yields 0 chunks after chunker runs:** Chunker bug. Fix and re-run before
   continuing to Phase B. Do not build TS tools against empty l4_remedial or l5_timeline.
3. **Source file structure differs from expected:** If REMEDIAL_CODEX_v2_0_PART1.md has no
   H2 headings (unlikely — it clearly does), or if the LIFETIME_TIMELINE_v1_0.md has a
   different structure — adapt the chunker boundary, document the discrepancy, continue.
   This is a self-correction, not a halt.
4. **P1 validator blocks all chunks and entity_refs injection doesn't fix it:** HALT with
   a description of the failing P1 rule and a proposed fix for native review.
5. **Test regression > 5 new failures:** Halt before deploy.
6. **Cloud Build failure after 1 retry:** HALT with build log excerpt.

Non-halting: embeddings gap (standalone run doesn't trigger Vertex AI — document and continue);
partial chunk count (slightly below minimum estimate — if > 0, continue and document).

---

## §6 — Closing summary template

```
SESSION CLOSE — M2_D234_BUNDLE — <ISO timestamp>

ACs result:
  AC.1:  <PASS|FAIL> — branch check
  AC.2:  <PASS|FAIL> — two Python chunkers created
  AC.3:  <PASS|FAIL> — l4_remedial ≥10, l5_timeline ≥5 in rag_chunks
  AC.4:  <PASS|FAIL> — domain_report ≥36 (no regression)
  AC.5:  <PASS|FAIL> — three TS tool files created
  AC.6:  <PASS|FAIL> — RETRIEVAL_TOOLS count 14→17
  AC.7:  <PASS|FAIL> — classifier prompt updated (3 blocks)
  AC.8:  <PASS|FAIL> — Python tests: ≥10 passing
  AC.9:  <PASS|FAIL> — TypeScript tests: ≥15 passing
  AC.10: <PASS|FAIL> — no new vitest failures
  AC.11: <PASS|FAIL> — TypeScript compiles clean
  AC.12: <PASS|FAIL> — CAPABILITY_MANIFEST updated
  AC.13: <PASS|FAIL> — Cloud Run revision updated
  AC.14: <PASS|FAIL> — smoke: domain_report_query fires

Files created/modified:
  platform/python-sidecar/rag/chunkers/remedial_chunker.py (CREATE)
  platform/python-sidecar/rag/chunkers/timeline_chunker.py (CREATE)
  platform/python-sidecar/rag/chunkers/__tests__/test_remedial_chunker.py (CREATE)
  platform/python-sidecar/rag/chunkers/__tests__/test_timeline_chunker.py (CREATE)
  platform/python-sidecar/pipeline/main.py (MODIFY — 2 new chunker registrations)
  platform/src/lib/retrieve/domain_report_query.ts (CREATE)
  platform/src/lib/retrieve/remedial_codex_query.ts (CREATE)
  platform/src/lib/retrieve/timeline_query.ts (CREATE)
  platform/src/lib/retrieve/__tests__/domain_report_query.test.ts (CREATE)
  platform/src/lib/retrieve/__tests__/remedial_codex_query.test.ts (CREATE)
  platform/src/lib/retrieve/__tests__/timeline_query.test.ts (CREATE)
  platform/src/lib/retrieve/index.ts (MODIFY — 3 imports + 3 RETRIEVAL_TOOLS entries)
  platform/src/lib/retrieve/__tests__/integration.test.ts (MODIFY — count 14→17)
  platform/src/lib/router/prompt.ts (MODIFY — 3 tool-guidance blocks)
  00_ARCHITECTURE/CAPABILITY_MANIFEST.json (MODIFY — 3 tool entries)

DB changes:
  rag_chunks (l4_remedial): 0 → <count>
  rag_chunks (l5_timeline): 0 → <count>
  rag_chunks (domain_report): <pre> → <post> (should be unchanged)
  Note on embeddings: new chunks have NULL embedding vectors (Vertex AI not triggered
  in standalone run; will embed on next full pipeline build).

Cloud Run: <prior revision> → <new revision>

Tests:
  Before: <X passed / Y failed>
  After: <X' passed / Y' failed>
  Delta: <new failures count>

Halt-and-report cases: <none | description>

Brief status: <COMPLETE | HALTED_AT_AC.N>
Next brief in stream: M2_D1_COMPOSITION_RULES (W6-R1)
```

After emitting the closing summary, append a session entry to
`00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1, and flip
`status: COMPLETE` in this brief's frontmatter.

---

*End of CLAUDECODE_BRIEF_M2_D234_BUNDLE v1.0 (authored 2026-04-30 — Wave 4 close).*

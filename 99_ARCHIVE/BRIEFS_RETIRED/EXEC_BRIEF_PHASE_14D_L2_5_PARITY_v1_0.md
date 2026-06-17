---
brief_id: EXEC_BRIEF_PHASE_14D_L2_5_PARITY
version: 1.1
status: AUTHORED
amended_at: 2026-04-28 — v1.1: GCS path correction (L2_5/ per GCS_LAYOUT_v1_0)
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code (multi-session)
trigger_phrase: "Read EXEC_BRIEF_PHASE_14D_L2_5_PARITY_v1_0.md and execute it."
phase: 14D
phase_name: L2.5 Holistic Synthesis Structured Tables — MSR, UCN, CDLM, CGM, RM
risk_classification: MEDIUM-HIGH (structured projection of 499-signal MSR + 9×9 CDLM + CGM nodes/edges + RM pairs; reuses existing chunker logic; tool surface added to runtime)
parallelizable_with: [14E (execution), 14C Streams D/E if 14C still in flight]
must_complete_before: [14G]
depends_on:
  - EXEC_BRIEF_PHASE_14C_L1_STRUCTURED_TABLES_v1_0.md (Stream F COMPLETE — IBuildWriter interface evolution must land before 14D writers can plug in)
output_artifacts:
  - 00_ARCHITECTURE/L2_5_STRUCTURED_LAYER_v1_0.md (NEW canonical spec)
  - 00_ARCHITECTURE/PHASE_14D_L2_5_PARITY_REPORT_v1_0.md (NEW execution report)
---

# EXEC_BRIEF — Phase 14D — L2.5 Parity (Holistic Synthesis Structured Tables)

## Mission

Project the L2.5 Holistic Synthesis stack from markdown-only into structured Postgres tables that the LLM router can query as deterministic tools. After 14D, queries like "find every MSR signal involving Saturn in the 7th house with negative valence" or "which domains contradict each other and how strongly?" stop relying on embedding-search and start hitting indexed tables. Six new tables, six new pipeline writers, five new LLM-callable tools.

L2.5 is more structured than L1 to begin with — `MSR_v3_0.md` already has 499 numbered signals in tabular form; `CDLM_v1_1.md` is a 9×9 matrix; `CGM_v9_0.md` is explicitly a node/edge graph; `UCN_v4_0.md` has section-numbered narrative; `RM_v2_0.md` has resonance pairs. Extractors for these already exist in `platform/python-sidecar/rag/chunkers/` (`msr_signal.py`, `ucn_section.py`, `cdlm_cell.py`, `cgm_node.py`). 14D **adds a structured-row projection layer alongside the existing chunk projection** — same source files, dual outputs, both fed by the 14B pipeline.

Three architectural commitments:

1. **Reuse the chunker parsing logic.** The existing chunkers already parse MSR signals, UCN sections, CDLM cells, and CGM nodes correctly enough to chunk for embedding. 14D's extractors call the same parsing functions, then emit structured rows instead of (or in addition to) chunks.

2. **Embedding-search and structured-query are complementary, not competing.** The runtime keeps both surfaces. Vector search (rag_chunks) handles "find anything semantically related to X." Structured queries (msr_signals, cdlm_links, etc.) handle "find every signal where category=Y and valence=Z." The router decides which to use per query type.

3. **Provenance is per-row, not just per-build.** Every row carries `source_uri`, `source_version`, `source_section`, `build_id` so derivation is traceable to the markdown line range that generated it.

## Pre-flight gate

1. Verify Phase 14C Stream F is COMPLETE — `IBuildWriter` interface in `platform/python-sidecar/pipeline/writers/base.py` supports row-based writers (not only chunks).
2. Verify `RAGChunksWriter` was successfully refactored to fit the new signature; its tests pass.
3. Verify the L2.5 sources are present in GCS at the layer-prefix path per `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md`:
   - `gs://madhav-marsys-sources/L2_5/MSR_v3_0.md`
   - `gs://madhav-marsys-sources/L2_5/UCN_v4_0.md`
   - `gs://madhav-marsys-sources/L2_5/CDLM_v1_1.md`
   - `gs://madhav-marsys-sources/L2_5/CGM_v9_0.md`
   - `gs://madhav-marsys-sources/L2_5/RM_v2_0.md`
   - `gs://madhav-marsys-sources/L2_5/RED_TEAM_L2_5_v1_0.md`
4. Verify Cloud SQL migrations through 017 (14C) are applied.
5. Verify the existing chunkers at `rag/chunkers/{msr_signal,ucn_section,cdlm_cell,cgm_node}.py` are importable as libraries (not just CLI scripts).
6. Confirm git working tree clean.

If any fail, halt with actionable message.

## Scope

**`may_touch` (filesystem / git):**
- `platform/supabase/migrations/018_l2_5_structured.sql` (NEW — six tables + staging)
- `platform/python-sidecar/pipeline/writers/`:
  - `msr_signals_writer.py` (NEW)
  - `ucn_sections_writer.py` (NEW)
  - `cdlm_links_writer.py` (NEW)
  - `cgm_nodes_writer.py` (NEW)
  - `cgm_edges_writer.py` (NEW)
  - `rm_resonances_writer.py` (NEW)
- `platform/python-sidecar/pipeline/extractors/`:
  - `msr_extractor.py` (NEW — wraps `rag/chunkers/msr_signal.py` parsing, emits rows)
  - `ucn_extractor.py` (NEW — wraps `rag/chunkers/ucn_section.py`)
  - `cdlm_extractor.py` (NEW — wraps `rag/chunkers/cdlm_cell.py`)
  - `cgm_extractor.py` (NEW — wraps `rag/chunkers/cgm_node.py`, also derives edges)
  - `rm_extractor.py` (NEW — parses RM_v2_0.md resonance pairs)
- `platform/src/lib/tools/structured/`:
  - `query_msr_signals.ts` (NEW)
  - `query_ucn_section.ts` (NEW)
  - `query_cdlm_link.ts` (NEW)
  - `query_cgm.ts` (NEW)
  - `query_resonance.ts` (NEW)
- `platform/src/lib/tools/registry.ts` (additive — register the 5 new tools)
- `00_ARCHITECTURE/L2_5_STRUCTURED_LAYER_v1_0.md` (NEW canonical spec)
- `00_ARCHITECTURE/PHASE_14D_L2_5_PARITY_REPORT_v1_0.md` (NEW execution report)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (additive — six new table entries; five new tool entries)
- `025_HOLISTIC_SYNTHESIS/CLAUDE.md` (additive update — STRUCTURED projection pointer)

**`must_not_touch`:**
- `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`, `UCN_v4_0.md`, `CDLM_v1_1.md`, `CGM_v9_0.md`, `RM_v2_0.md` — markdown stays canonical authoring source.
- `platform/python-sidecar/rag/chunkers/*.py` — REUSE as libraries; do NOT modify.
- `pipeline/main.py` orchestrator core (additive registry only).
- 14B's `RAGChunksWriter` — already refactored in 14C Stream F; do NOT re-touch.
- 14C's tables (chart_facts, ephemeris_daily, etc.) — separate ownership.
- Any L1 / L3 file. Any feature flag.

## Execution model — multi-session

Streams A–G map roughly 1:1 to sessions. Recommended order:

| Order | Stream | Session # | Parallel-safe with |
|---|---|---|---|
| 1 | A — Migration 018 (six tables + staging) | 1 | (foundation) |
| 2 | B — MSR signals extractor + writer | 2 | C, D, E, F |
| 2 | C — UCN sections extractor + writer | 3 | B, D, E, F |
| 2 | D — CDLM links extractor + writer | 4 | B, C, E, F |
| 2 | E — CGM nodes + edges extractor + writers | 5 | B, C, D, F |
| 2 | F — RM resonances extractor + writer | 6 | B, C, D, E |
| 3 | G — Tool implementations + registry + verification + report | 7 | (gated on B–F done) |

## Sub-streams

### Stream A — Migration 018 (six tables)

```sql
BEGIN;
-- MSR Signals (499 rows expected from MSR_v3_0)
CREATE TABLE IF NOT EXISTS msr_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id TEXT UNIQUE NOT NULL,        -- 'SIG.MSR.001'
  signal_number INTEGER NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL,                -- 'planetary'|'house'|'sign'|'aspect'|'yoga'|'dasha'|'transit'|'cross'
  valence TEXT NOT NULL,                 -- 'positive'|'negative'|'neutral'|'mixed'
  weight NUMERIC,                        -- if MSR assigns numeric weights
  planets_involved TEXT[],               -- ['SUN','SAT'] etc.
  houses_involved INTEGER[],             -- [1, 7]
  signs_involved TEXT[],
  description TEXT NOT NULL,
  source_section TEXT NOT NULL,          -- '§II.3.7' or similar
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  provenance JSONB NOT NULL
);
CREATE INDEX idx_msr_category_valence ON msr_signals(category, valence);
CREATE INDEX idx_msr_planets ON msr_signals USING GIN(planets_involved);
CREATE INDEX idx_msr_houses ON msr_signals USING GIN(houses_involved);
CREATE TABLE IF NOT EXISTS msr_signals_staging (LIKE msr_signals INCLUDING ALL);

-- UCN Sections
CREATE TABLE IF NOT EXISTS ucn_sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  section_id TEXT UNIQUE NOT NULL,       -- 'UCN.4.2.7'
  parent_section_id TEXT,                -- self-FK
  domain TEXT,                           -- 'self'|'wealth'|'sibling'|'home'|'progeny'|'health'|'partner'|'transformation'|'career'
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  derived_from_signals TEXT[],           -- list of MSR signal_ids cited in this section
  source_lines TEXT,                     -- 'L342-L378'
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id)
);
CREATE INDEX idx_ucn_domain ON ucn_sections(domain);
CREATE INDEX idx_ucn_signals ON ucn_sections USING GIN(derived_from_signals);
CREATE TABLE IF NOT EXISTS ucn_sections_staging (LIKE ucn_sections INCLUDING ALL);

-- CDLM Links (9 domains × 9 = 81 cells)
CREATE TABLE IF NOT EXISTS cdlm_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  link_id TEXT UNIQUE NOT NULL,          -- 'CDLM.SELF.WEALTH'
  from_domain TEXT NOT NULL,
  to_domain TEXT NOT NULL,
  link_type TEXT NOT NULL,               -- 'CITES'|'CONTRADICTS'|'REINFORCES'|'NEUTRAL'
  strength TEXT NOT NULL,                -- 'strong'|'moderate'|'weak'|'nil'
  source_signals TEXT[],
  notes TEXT,
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  UNIQUE(from_domain, to_domain)
);
CREATE INDEX idx_cdlm_from ON cdlm_links(from_domain);
CREATE INDEX idx_cdlm_to ON cdlm_links(to_domain);
CREATE TABLE IF NOT EXISTS cdlm_links_staging (LIKE cdlm_links INCLUDING ALL);

-- CGM Nodes (chart graph nodes)
CREATE TABLE IF NOT EXISTS cgm_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id TEXT UNIQUE NOT NULL,          -- 'CGM.PLN.SAT' | 'CGM.HSE.07' | 'CGM.SIG.LIB'
  node_type TEXT NOT NULL,               -- 'planet'|'house'|'sign'|'karaka'|'nakshatra'|'fixed_star'|'special_lagna'
  display_name TEXT NOT NULL,
  properties JSONB NOT NULL,             -- {sign:'Libra', house:7, retrograde:false, ...}
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id)
);
CREATE INDEX idx_cgm_nodes_type ON cgm_nodes(node_type);
CREATE TABLE IF NOT EXISTS cgm_nodes_staging (LIKE cgm_nodes INCLUDING ALL);

-- CGM Edges (typed relationships)
CREATE TABLE IF NOT EXISTS cgm_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  edge_id TEXT UNIQUE NOT NULL,
  source_node_id TEXT NOT NULL REFERENCES cgm_nodes(node_id),
  target_node_id TEXT NOT NULL REFERENCES cgm_nodes(node_id),
  edge_type TEXT NOT NULL,               -- 'ASPECTS'|'RULES'|'EXALTED_IN'|'DEBILITATED_IN'|'YUTI_WITH'|'LORDS'|'KARAKA_FOR'|'CONTRADICTS'|'SUPPORTS'
  strength NUMERIC,
  notes TEXT,
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id)
);
CREATE INDEX idx_cgm_edges_source ON cgm_edges(source_node_id);
CREATE INDEX idx_cgm_edges_target ON cgm_edges(target_node_id);
CREATE INDEX idx_cgm_edges_type ON cgm_edges(edge_type);
CREATE TABLE IF NOT EXISTS cgm_edges_staging (LIKE cgm_edges INCLUDING ALL);

-- RM Resonances (signal-level resonance pairs)
CREATE TABLE IF NOT EXISTS rm_resonances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resonance_id TEXT UNIQUE NOT NULL,
  signal_a_id TEXT NOT NULL,
  signal_b_id TEXT NOT NULL,
  resonance_type TEXT NOT NULL,          -- 'reinforce'|'amplify'|'modulate'|'cancel'|'tension'
  strength TEXT NOT NULL,                -- 'strong'|'moderate'|'weak'
  theme TEXT,                            -- short label for the resonance
  notes TEXT,
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  UNIQUE(signal_a_id, signal_b_id, resonance_type)
);
CREATE INDEX idx_rm_signal_a ON rm_resonances(signal_a_id);
CREATE INDEX idx_rm_signal_b ON rm_resonances(signal_b_id);
CREATE TABLE IF NOT EXISTS rm_resonances_staging (LIKE rm_resonances INCLUDING ALL);

COMMIT;
```

### Stream B — MSR Signals extractor + writer

`extractors/msr_extractor.py` imports the parser from `rag/chunkers/msr_signal.py` and emits structured rows instead of (or alongside) chunks. Per-row fields per the table schema. Validation: 499 rows expected (per `MSR_v3_0` close). Write to `msr_signals_staging`. Swap with 0.5× threshold.

### Stream C — UCN Sections extractor + writer

`extractors/ucn_extractor.py` imports `rag/chunkers/ucn_section.py`. UCN has nested sections (UCN.1, UCN.1.1, UCN.1.1.1, ...); preserve the parent_section_id chain. Each section's `derived_from_signals` is extracted by grepping for `SIG.MSR.NNN` patterns in the section body. Validation: section count > 50; every cited signal_id resolves against `msr_signals_staging`.

### Stream D — CDLM Links extractor + writer

`extractors/cdlm_extractor.py` imports `rag/chunkers/cdlm_cell.py`. Output is exactly 81 rows (9×9). Validation: count = 81 exactly; every `from_domain`/`to_domain` pair is unique; the diagonal (self×self) cells exist with link_type='NEUTRAL' or domain-internal cohesion. Write to `cdlm_links_staging`.

### Stream E — CGM Nodes + Edges

`extractors/cgm_extractor.py` imports `rag/chunkers/cgm_node.py`. Two-pass:
1. First pass: emit nodes (planets, houses, signs, karakas, nakshatras, ...). Validation: ~50-80 nodes expected.
2. Second pass: emit edges by parsing CGM_v9_0.md for explicit relationship statements (ASPECTS, RULES, etc.). Edges reference nodes by `node_id` — both endpoints must exist or the edge is dropped with a logged warning. Validation: edge_count > 100 (CGM v9 has thousands per memory ref `1753 nodes / 3915 edges` — note the prior fingerprint suggests existing CGM ledger; reconcile with 14B's chunked output).

Write each to its `*_staging` table. Edge swap depends on node swap landing first within the same transaction.

### Stream F — RM Resonances extractor + writer

`extractors/rm_extractor.py` parses `RM_v2_0.md`. Resonance entries are typically of the form "SIG.MSR.NNN ↔ SIG.MSR.MMM (resonance_type, strength) — theme". Extract pairs; validate every signal_id resolves against `msr_signals_staging`. Write to `rm_resonances_staging`. Validation: row_count > 0; no self-pair (signal_a_id != signal_b_id).

### Stream G — Tools + registry + verification + close

Implement five tools at `platform/src/lib/tools/structured/`:

| Tool | Inputs | Returns |
|---|---|---|
| `query_msr_signals` | filters: `category?, valence?, planet?, house?, sign?` | matching MSR signals |
| `query_ucn_section` | `section_id?` OR `domain?` | matching UCN sections (with `derived_from_signals`) |
| `query_cdlm_link` | `from_domain, to_domain` | one row from cdlm_links |
| `query_cgm` | `node_id?` OR `node_type?` | nodes + their edges (joined) |
| `query_resonance` | `signal_id` | rm_resonances rows where signal is `signal_a_id` or `signal_b_id` |

Register in `platform/src/lib/tools/registry.ts`. Each tool description tells an LLM exactly when to choose it.

Verification:
1. Trigger full pipeline run.
2. Verify staging row counts: msr=499, ucn≥50, cdlm=81, cgm_nodes 50-80, cgm_edges>100, rm>0.
3. Swap; verify live counts match staging.
4. Spot-check tools:
   - `query_msr_signals(planet='SAT', house=7)` → returns ≥1 row (Saturn-7H natal placement)
   - `query_cdlm_link(from='self', to='partner')` → returns one row with link_type+strength
   - `query_cgm(node_id='CGM.PLN.SAT')` → returns Saturn node with its edges
   - `query_resonance('SIG.MSR.001')` → returns rm_resonances where signal 1 is paired
5. Validators run; deltas vs 14C-end baseline documented.
6. Author `L2_5_STRUCTURED_LAYER_v1_0.md` + `PHASE_14D_L2_5_PARITY_REPORT_v1_0.md`.
7. Update `025_HOLISTIC_SYNTHESIS/CLAUDE.md` with STRUCTURED projection pointer.
8. Update `CAPABILITY_MANIFEST.json`; rotate fingerprint.
9. Atomic commit per stream; final umbrella commit at G.

## Done criteria

1. Migration 018 applied; six tables + six staging tables exist.
2. msr_signals = 499 rows; cdlm_links = 81 rows; ucn_sections, cgm_nodes, cgm_edges, rm_resonances populated within sanity ranges.
3. Six writers integrated into the 14B pipeline.
4. Five tools implemented, registered, unit-tested against the four spot-check queries.
5. Every UCN-cited signal_id resolves against msr_signals (referential integrity).
6. Every CGM edge endpoint resolves against cgm_nodes (FK enforced).
7. Every RM resonance pair resolves against msr_signals.
8. `L2_5_STRUCTURED_LAYER_v1_0.md` + `PHASE_14D_L2_5_PARITY_REPORT_v1_0.md` exist.
9. Validator deltas vs prior baseline documented.
10. CAPABILITY_MANIFEST.json updated; fingerprint rotated.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Existing chunker logic produces a different signal_id format than schema expects | Medium | Medium | Stream B compares first 10 extracted IDs against `msr_signals` schema constraint; halt on mismatch. |
| CDLM matrix has fewer/more than 81 cells (e.g., partial fill) | Low | Medium | Stream D halts on count != 81; surface and force native review. |
| CGM edges reference nodes that don't exist (extractor ordering bug) | Medium | Medium | Edge writer drops orphan edges and logs; if drop count > 5% of edges, halt. |
| UCN section parsing misses citations of MSR signals (regex pattern too narrow) | Medium | Low | Parse-then-validate: every `SIG.MSR.NNN` literal in UCN body must be captured; coverage tested in Stream C. |
| RM resonance pairs use legacy signal_id format from MSR v2 not v3 | Medium | Medium | RM_v2_0 was authored against MSR v2; if signal_ids drifted, surface as finding for a follow-up brief; 14D ingests what it can and flags the rest. |
| Migration 018 conflicts with 14C's 014–017 if executor reorders | Low | Low | Sequential migration numbering; pre-flight checks 14C migrations applied. |

## Concurrency declaration

**Parallel-with**:
- 14E execution (disjoint tables: pattern_register, cluster_register, etc.)
- 14C Streams D/E if 14C still in flight (those write to L1 tables; 14D writes to L2.5 tables)

**Must complete before**:
- 14G lockdown — needs full L2.5 structured projection.

**Shared-file vigilance**:
- `pipeline/main.py` writer registry — additive entries; rebase on conflict.
- `platform/src/lib/tools/registry.ts` — additive; rebase on conflict.
- `CAPABILITY_MANIFEST.json` — additive; rebase on conflict.

## Trigger phrase

"Read EXEC_BRIEF_PHASE_14D_L2_5_PARITY_v1_0.md and execute it."

## Notes for the executor

- The existing chunkers in `rag/chunkers/` are the ground truth for parsing. Do not re-invent parsing; import and call. If a chunker has CLI-only side effects, do the minimal refactor to expose its parse function as a library import and document.
- CGM edges are the densest part of L2.5 (memory note: 3915 edges in a prior CGM ledger). Verify Cloud SQL handles the GIN/btree index sizes; if issues, switch GIN→btree on edge_type and source_node_id.
- The 0.5× swap threshold from 14B applies to each writer. For CDLM (81 cells) the absolute threshold is critical: 0.5×81 = 40 — any swap with <40 staged cells aborts.
- Tool description quality is the make-or-break detail. A tool called `query_msr_signals` with description "find signals" won't be selected by the router for a Saturn-7H query. Write descriptions that include 2-3 example queries the tool answers.

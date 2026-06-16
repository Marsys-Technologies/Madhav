---
brief_id: RETRIEVAL_11C_c
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-29
authored_for: Claude Code execution
session_type: implementation (Python sidecar chunker wiring; embed; deploy; verify)
related_plan: 00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md (§2.2 fix F2.1)
predecessor: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_b.md (status: COMPLETE; cgm_graph_walk firing 60% on entity-named queries; queryText='' bug fixed)
target_branch: redesign/r0-foundation
parallel_stream_note: |
  UI/UX modernization stream is running R1/R2 portal redesign briefs on the
  same branch (UI surface only — components/, app/, hooks/). This brief is
  python-sidecar-side + a small probe-script fix. Disjoint paths.

estimated_time: 1–2 days

scope_summary: |
  Get L2.5 + L3 content into rag_chunks so vector_search can semantic-match
  against UCN narrative, CDLM cell prose, RM element guidance, CGM node
  context, and MSR signal text — not just L1 FORENSIC.

  Current state (verified-by-bash 2026-04-29):
    • chunkers exist for: l1_fact, msr_signal, ucn_section, cdlm_cell,
      cgm_node, domain_report
    • NO chunker exists for RM (rm_resonance / rm_element)
    • rag_chunks_writer + Vertex embed pipeline (text-multilingual-embedding-002,
      768d) are wired and operational
    • PROBE 5 (2026-04-29) errored on wrong column name (source_doc vs
      source_file) — actual rag_chunks state UNVERIFIED in live DB
    • pipeline/main.py wires structured-table writers but it is unconfirmed
      whether those stages ALSO produce + embed chunks for rag_chunks

  Implementation: (a) fix PROBE 5 column name; (b) run corrected probe to
  ground-truth current rag_chunks state; (c) for each missing doc_type,
  wire its chunker into pipeline/main.py to flow through rag_chunks_writer;
  (d) create rm_element.py chunker (RM has no chunker today); (e) run
  pipeline; (f) re-probe; (g) verify by sending a vector_search-driven query
  and confirming L2.5 chunks reach the LLM.

may_touch:
  - platform/python-sidecar/rag/chunkers/rm_element.py                       # CREATE — no RM chunker exists
  - platform/python-sidecar/rag/chunkers/__init__.py                         # add rm_element export if needed
  - platform/python-sidecar/pipeline/main.py                                 # wire chunker → rag_chunks_writer stages
  - platform/python-sidecar/pipeline/writers/__init__.py                     # if helper export needed
  - platform/python-sidecar/tests/**                                         # tests for new RM chunker + wiring
  - platform/scripts/retrieval_diagnostic_probes.sql                         # fix PROBE 5 column-name bug only
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_c.md               # status flip at end
  - 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_c.txt            # CREATE post-deploy verification
  # Read-only references (do NOT edit):
  - 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md                                        # source for UCN chunks
  - 025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md                                       # source for CDLM chunks
  - 025_HOLISTIC_SYNTHESIS/RM_v2_0.md                                         # source for RM chunks
  - 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md                                        # source for CGM node chunks
  - 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md                                        # source for MSR signal chunks
  - platform/python-sidecar/rag/chunkers/ucn_section.py                       # consume only
  - platform/python-sidecar/rag/chunkers/cdlm_cell.py                         # consume only
  - platform/python-sidecar/rag/chunkers/cgm_node.py                          # consume only
  - platform/python-sidecar/rag/chunkers/msr_signal.py                        # consume only
  - platform/python-sidecar/rag/chunkers/l1_fact.py                           # consume only
  - platform/python-sidecar/rag/chunkers/domain_report.py                     # may add wiring; do not modify code
  - platform/python-sidecar/rag/embed.py                                      # consume only
  - platform/python-sidecar/pipeline/writers/rag_chunks_writer.py             # consume only

must_not_touch:
  - CLAUDECODE_BRIEF.md                                                       # ROOT — UI/UX stream
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_PROBES.md           # COMPLETE
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_a.md                # COMPLETE
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_b.md                # COMPLETE
  - 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_2026-04-29.txt             # historical
  - 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_a.txt             # historical
  - 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_b.txt             # historical
  - 00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md                 # reference only
  - EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER_v1_0.md                              # UI/UX stream
  - EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE_v1_0.md                       # UI/UX stream
  - platform/src/**                                                           # all TypeScript — UI/UX + retrieve consumers OFF LIMITS
  - platform/src/components/**
  - platform/src/app/**
  - platform/src/hooks/**
  - platform/src/lib/router/**                                                # 11C_b just landed; do not disturb
  - platform/src/lib/retrieve/**                                              # F2.2 (vector_search filter expansion) is a SEPARATE brief
  - platform/src/lib/bundle/**
  - platform/src/lib/synthesis/**
  - platform/python-sidecar/rag/chunkers/ucn_section.py                       # working as-is
  - platform/python-sidecar/rag/chunkers/cdlm_cell.py                         # working as-is
  - platform/python-sidecar/rag/chunkers/cgm_node.py                          # working as-is
  - platform/python-sidecar/rag/chunkers/msr_signal.py                        # working as-is
  - platform/python-sidecar/rag/chunkers/l1_fact.py                           # working as-is
  - platform/python-sidecar/rag/embed.py                                      # working as-is
  - platform/python-sidecar/pipeline/writers/rag_chunks_writer.py             # working as-is
  - platform/python-sidecar/pipeline/extractors/cgm_extractor.py              # 11C_a just landed; do not disturb
  - platform/migrations/**                                                    # NO schema changes — fits existing schema
  - 025_HOLISTIC_SYNTHESIS/**                                                 # source-of-truth; read-only
  - Any retrieval-tool TypeScript file

acceptance_criteria:
  AC.1: PROBE 5 in platform/scripts/retrieval_diagnostic_probes.sql is corrected — `source_doc` replaced with `source_file` (the actual column name per migration 005). The probe file edit is the ONLY scripts/* change permitted; no other probes touched.
  AC.2: Initial probe (corrected PROBE 5) is run against live DB; output captured to a temporary file. Result documented in session output: pre-fix counts of rag_chunks grouped by (layer, doc_type).
  AC.3: pipeline/main.py is inspected. Document in the session output exactly which chunker→rag_chunks_writer wirings exist today vs need to be added. The writers list expected in pipeline/main.py for full L2.5 + L3 chunk coverage:
        l1_fact (FORENSIC) → already wired (assumed; verify)
        msr_signal (MSR) → wire if missing
        ucn_section (UCN) → wire if missing
        cdlm_cell (CDLM) → wire if missing
        cgm_node (CGM) → wire if missing
        domain_report (L3 reports) → wire if missing
        rm_element (RM) → CREATE chunker + wire (no chunker today)
  AC.4: rm_element.py chunker created in platform/python-sidecar/rag/chunkers/, modeled on the existing chunkers' interface. Each RM element (RM.01 through RM.32, ~28 active elements) becomes one chunk. Required Chunk fields per chunker convention: chunk_id, doc_type='rm_element', layer='L2.5', source_file='025_HOLISTIC_SYNTHESIS/RM_v2_0.md', source_version, content (the element's full block), token_count, metadata (with element_id, domains_primary, etc.). Function signature: `def chunk_rm_elements(repo_root: str) -> list[Chunk]:`. Test added.
  AC.5: pipeline/main.py wired such that running the full build pipeline produces (chunk, embedding) pairs for ALL six doc_types listed in AC.3 — l1_fact, msr_signal, ucn_section, cdlm_cell, cgm_node, domain_report, rm_element (7 doc_types total counting rm_element).
  AC.6: Pipeline runs end-to-end successfully against the live Auth Proxy. Track build_id; confirm staging tables populate; confirm swap_to_live succeeds for rag_chunks_staging → rag_chunks AND rag_embeddings_staging → rag_embeddings.
  AC.7: Re-run the corrected PROBE 5 query post-pipeline. Capture to RETRIEVAL_PROBE_RESULTS_POST_11C_c.txt. Expectations on live count:
        l1_fact:        ~102 (unchanged from baseline)
        msr_signal:     ~499 (one per MSR signal)
        ucn_section:    ~134 (matches 11C_a UCN node count)
        cdlm_cell:      ~80–82 (matches CDLM cell count)
        cgm_node:       ~369 (matches post-11C_a node count)
        domain_report:  varies (chunks per L3 report; typically 5–20 per report × 9 reports = ~50–180 chunks)
        rm_element:     ~28
        TOTAL:          ≥1200 rag_chunks rows (was ~102)
  AC.8: rag_embeddings count = rag_chunks count (1:1, every chunk has its embedding). Verify with `SELECT COUNT(*) FROM rag_chunks` vs `SELECT COUNT(*) FROM rag_embeddings WHERE model='vertex-text-multilingual-embedding-002'`.
  AC.9: Python sidecar tests pass at the pre-existing baseline (no NEW failures). Add tests for rm_element chunker.
  AC.10: Cloud Run revision amjis-web is rebuilt and serving 100% via bash platform/scripts/cloud_build_submit.sh. (TypeScript app code is unchanged but redeployed for build-trail cleanliness; vector_search reads live DB so the new chunks are accessible the moment swap_to_live completes.)
  AC.11: Post-deploy verification: send 3 test queries through the deployed Consume tab that should benefit from L2.5 content:
         (1) "Explain how Mercury supports my career path." (should retrieve UCN Part I content + msr_signal Mercury content + cdlm_cell career→wealth)
         (2) "What does my chart say about Saturn's role?" (should retrieve RM.02 element + ucn_section + msr_signal Saturn)
         (3) "Tell me about my Saraswati yoga and what it means in practice." (should retrieve YOG-related msr_signals + ucn_section + possibly domain_report career)
         Wait ~30s, then query query_trace_steps for each. Confirm vector_search step has item_count > 0 (already true) AND the retrieved chunk doc_types include AT LEAST one non-l1_fact value (e.g., ucn_section, msr_signal, rm_element). Capture results to RETRIEVAL_PROBE_RESULTS_POST_11C_c.txt.
  AC.12: This brief's frontmatter `status` is updated to COMPLETE.
  AC.13: `git status` shows ONLY: pipeline/main.py changes, new rm_element.py chunker, possibly chunkers/__init__.py update, test additions, the PROBE 5 fix in retrieval_diagnostic_probes.sql, this brief (status flip), the new POST_11C_c.txt. No platform/src/** changes. No migration changes. No edits to existing chunkers.
---

# CLAUDECODE_BRIEF — RETRIEVAL_11C_c (F2.1 L2.5 corpus chunking + embedding)

## §1 — Why this session

Brief 11C_b made `cgm_graph_walk` fire on 60% of entity-named queries — but graph traversal returns *node IDs*, not narrative. The LLM still needs prose context to actually synthesize an answer. Today, `vector_search` only reads ~102 chunks of L1 FORENSIC text; the rich L2.5 content (UCN's 17K-word narrative, CDLM's 82 cells of cross-domain mechanism prose, RM's 28 elements of practical guidance, CGM's 234 nodes of structural context, MSR's 499 signals) is invisible to semantic retrieval.

This session closes that gap. Every L2.5 + L3 source becomes embedded chunks reachable by `vector_search`. After this brief, a query like "Explain how Mercury supports my career path" will retrieve UCN Part I narrative + msr_signal Mercury entries + cdlm_cell career→wealth prose, in addition to the FORENSIC L1 chunks. The compound effect with 11C_a (graph data) and 11C_b (graph queries from real seeds) is the LLM finally getting structure + content together.

## §2 — Architecture confirmation (verified 2026-04-29 on r0-foundation)

**Chunker code present** in `platform/python-sidecar/rag/chunkers/`:
- `l1_fact.py` (FORENSIC chunks)
- `msr_signal.py` (one chunk per MSR signal)
- `ucn_section.py` (one chunk per UCN H2/H3 section)
- `cdlm_cell.py` (one chunk per CDLM cell)
- `cgm_node.py` (one chunk per CGM node)
- `domain_report.py` (chunks per L3 report)
- **MISSING: rm_element / rm_resonance** — no RM chunker exists today. You will create it.

**Schema** (migration 005):
- `rag_chunks(chunk_id, doc_type, layer, source_file, source_version, content, token_count, is_stale, metadata)` — `doc_type` already supports `msr_signal|ucn_section|cdlm_cell|l1_fact|domain_report|cgm_node` per the column comment. You will add `rm_element` as a new value (TEXT field, no enum constraint, so just write the new value).
- `rag_embeddings(chunk_id, model, embedding vector(768))` — model `text-multilingual-embedding-002`, dim 768 confirmed by migration 010.

**Writer + embed pipeline operational**: `pipeline/writers/rag_chunks_writer.py` (staging → swap), `rag/embed.py` (Vertex AI caller).

**The actual unknown**: whether `pipeline/main.py` already wires the chunker→writer flow for each doc_type, or whether some chunkers are dead code. Step §3.2 below resolves this. **Do not assume; verify.**

**The probe bug**: `retrieval_diagnostic_probes.sql` PROBE 5 selects `COUNT(DISTINCT source_doc)`. The actual column is `source_file`. Fix the probe in §3.1 — that's the only edit to that file permitted this session.

## §3 — Implementation steps

### §3.1 — Fix PROBE 5 column name

In `platform/scripts/retrieval_diagnostic_probes.sql`, find PROBE 5's SELECT block. Replace `source_doc` with `source_file`. No other change to the probes file.

### §3.2 — Pre-fix probe (ground-truth the starting state)

Bring up the Auth Proxy (reuse if running). Run the corrected PROBE 5 query against live DB:

```sql
SELECT
  layer, doc_type,
  COUNT(*) AS chunks,
  COUNT(DISTINCT source_file) AS distinct_sources
FROM rag_chunks
WHERE is_stale = false
GROUP BY layer, doc_type
ORDER BY layer, chunks DESC;
```

Record the output. This is the BEFORE snapshot. Expect mostly `(L1, l1_fact, ~102)` and possibly some L2.5 entries if a previous build wired them. Whatever exists, document it explicitly in the session output.

### §3.3 — Inspect pipeline/main.py wiring

Open `platform/python-sidecar/pipeline/main.py`. Identify which chunkers are currently wired into the rag_chunks pipeline. Look for:
- Imports from `rag.chunkers.*`
- Calls to `RAGChunksWriter` or any pattern that pairs (chunk, embedding) and writes them via the writer
- Stage tuples in the format `("rag_chunks_<doc_type>", RAGChunksWriter, <extractor>)` or similar

Produce a table in the session output:

| chunker | currently wired | needs wiring |
|---|---|---|
| l1_fact | (yes/no) | (yes/no) |
| msr_signal | ... | ... |
| ucn_section | ... | ... |
| cdlm_cell | ... | ... |
| cgm_node | ... | ... |
| domain_report | ... | ... |
| rm_element | NO (chunker doesn't exist) | YES |

The §3.4 + §3.5 steps below act on the "needs wiring" rows.

### §3.4 — Create rm_element.py chunker

Create `platform/python-sidecar/rag/chunkers/rm_element.py`. Model the structure on `cdlm_cell.py` (closest cousin — both are element-block chunkers over a structured prose source). Required exports:

```python
def chunk_rm_elements(repo_root: str) -> list[Chunk]:
    """
    Parse RM_v2_0.md and emit one Chunk per resonance-map element (RM.01–RM.32).

    Each Chunk:
      chunk_id    = f"RM.{element_id_padded}"  e.g., "RM.01", "RM.02"
      doc_type    = "rm_element"
      layer       = "L2.5"
      source_file = "025_HOLISTIC_SYNTHESIS/RM_v2_0.md"
      source_version = (read frontmatter or hardcode v2.0 / v2.1)
      content     = full element block (element + domains_primary + msr_anchors +
                    constructive_resonance + destructive_resonance + net_resonance +
                    interpretive_note)
      token_count = count_tokens(content)
      metadata    = { "element_id": "RM.01", "element_label": ...,
                      "domains_primary": [...], "msr_anchors": [...] }
    """
```

Parse strategy: RM_v2_0.md uses YAML-block-per-element format (see existing extractor `pipeline/extractors/rm_extractor.py` for the parsing convention — DO NOT modify it; just consume the same parsing logic or adapt it locally). Skip elements below `MIN_BODY_TOKENS` (whatever threshold the other chunkers use, typically 20).

Add a unit test in `platform/python-sidecar/tests/` modeled on existing chunker tests. Assert: ≥20 chunks emitted (RM has 28 active elements, but a few may be archived stubs); every chunk_id starts with `"RM."`; every doc_type is `"rm_element"`.

Update `rag/chunkers/__init__.py` to export `chunk_rm_elements` if the package follows that pattern.

### §3.5 — Wire missing chunkers into pipeline/main.py

For each "needs wiring" row from §3.3 (likely all six L2.5 + L3 chunkers plus the new rm_element), add the chunker→writer wiring. Two implementation paths — pick the one that matches the existing pipeline pattern:

**Path I (preferred, if pipeline/main.py already has a stages list):** Add a stage tuple per chunker. Each stage:
1. Calls the chunker function: `chunk_xxx(workspace) → list[Chunk]`
2. Calls `embed_chunks(chunks) → list[(Chunk, list[float])]` (or whatever the existing embed function is in `rag/embed.py`)
3. Passes pairs to `RAGChunksWriter().write_to_staging(pairs, build_id)`

Stage names per convention: `("rag_l1_fact", RAGChunksWriter, <chunker+embedder lambda>)`, `("rag_msr_signal", ...)`, etc.

**Path II:** If the existing pipeline groups all rag_chunks writes into a single stage, extend that stage's chunk-collector to call all 7 chunkers and concatenate their outputs before embedding + writing.

Whichever path: ensure the writer's `validate_staging` threshold is reasonable for the merged chunk count (≥800 chunks expected; if the existing threshold is `MIN_VALID_COUNT = 100`, that's fine).

### §3.6 — Run pipeline

Run the full pipeline against live DB. Confirm:
- Each new stage logs its chunk count.
- Staging tables populate; validate succeeds.
- swap_to_live atomic transaction completes for both `rag_chunks` and `rag_embeddings`.

Embedding is the slow step. ~1200 chunks × ~150ms per Vertex call ≈ 3 minutes minimum (less with batching; the writer batches 100 at a time per its source). Plan for a 5–10 minute pipeline run.

### §3.7 — Post-fix probe

Re-run the corrected PROBE 5. Capture full output to `00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_c.txt`. Add to the same file:

- `SELECT COUNT(*) FROM rag_chunks WHERE is_stale = false;`
- `SELECT COUNT(*) FROM rag_embeddings WHERE model = 'text-multilingual-embedding-002';` (these two should match per AC.8)
- The SELECT-by-(layer, doc_type) breakdown

### §3.8 — Test, deploy

```
cd platform/python-sidecar && python -m pytest -x  # or whatever the runner is
cd ../..
bash platform/scripts/cloud_build_submit.sh
```

Confirm Cloud Run revision deployed.

### §3.9 — Post-deploy live verification

Send 3 representative queries through the Consume tab (paths from AC.11). Wait ~30s. Then query `query_trace_steps` for each query's `vector_search` step:

```sql
SELECT
  query_id,
  step_seq,
  step_name,
  status,
  jsonb_array_length(payload->'items') AS item_count,
  payload->'items' AS items_preview
FROM query_trace_steps
WHERE created_at > NOW() - INTERVAL '10 minutes'
  AND step_name = 'vector_search'
ORDER BY query_id, step_seq;
```

Inspect the `items_preview` JSONB. For each query, confirm at least one returned chunk has `doc_type` in `{ucn_section, cdlm_cell, msr_signal, cgm_node, domain_report, rm_element}` (i.e., NOT only `l1_fact`). If the items don't include doc_type, query a deeper join: `SELECT chunk_id, doc_type FROM rag_chunks WHERE chunk_id = ANY(...)` for the chunks the trace step retrieved.

Append the verification to `RETRIEVAL_PROBE_RESULTS_POST_11C_c.txt`.

### §3.10 — Close

1. Set this brief's `status: COMPLETE`.
2. Print the closing summary: pre-fix rag_chunks count (probably ~102), post-fix count (target ≥1200), per-doc_type breakdown, the 3 verification queries' L2.5-content-retrieved status.

## §4 — Hard constraints

- **Python sidecar + one SQL probe fix only.** No TypeScript edits. The existing chunkers, writers, and embed code are correct as-is.
- **Do not modify migrations.** The existing `rag_chunks` schema accepts a new `doc_type` value `rm_element` because `doc_type TEXT` has no enum constraint.
- **Do not modify existing chunkers.** Read-and-consume only. If a chunker's output shape doesn't fit the writer, halt and report — don't refactor in-scope.
- **Do not touch the retrieve-side TypeScript.** F2.2 (`vector_search.ts` filter expansion to expose layer/doc_type as query params) is a SEPARATE brief. This brief only puts content in the table; the existing tool already retrieves whatever's in there.
- **Do not modify the active root brief or the R1/R2 portal redesign briefs.** UI/UX scope.
- **Halt-and-report on blockers.** If `pipeline/main.py` doesn't have a clear extension point for chunker stages, OR if `embed.py` errors out on Vertex AI auth, OR if swap_to_live fails the safety gate (≥0.5× live count), do not improvise. Print the error, leave the system in a recoverable state, and stop.

## §5 — Closing checklist

- [ ] AC.1 verified — PROBE 5 column corrected.
- [ ] AC.2 verified — pre-fix counts captured.
- [ ] AC.3 verified — wiring table documented.
- [ ] AC.4 verified — rm_element.py chunker created + tested.
- [ ] AC.5 verified — pipeline/main.py wires all 7 doc_types.
- [ ] AC.6 verified — pipeline ran end-to-end + swap_to_live succeeded.
- [ ] AC.7 verified — POST_11C_c.txt has full per-doc_type breakdown.
- [ ] AC.8 verified — chunks count = embeddings count.
- [ ] AC.9 verified — pytest at baseline.
- [ ] AC.10 verified — Cloud Run revision deployed.
- [ ] AC.11 verified — 3 live queries retrieved L2.5 content.
- [ ] AC.12 — brief status COMPLETE.
- [ ] AC.13 verified — `git status` clean of out-of-scope changes.

---

*End of CLAUDECODE_BRIEF_RETRIEVAL_11C_c. Status: COMPLETE. Closed 2026-04-30.*

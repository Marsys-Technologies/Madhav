---
brief_id: EXEC_BRIEF_PHASE_13_RETRIEVAL_AUDIT
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_13_RETRIEVAL_AUDIT_v1_0.md and execute it."
phase: 13
phase_name: Retrieval Completeness Audit + Repair
risk_classification: LOW-MEDIUM (read-mostly investigation; surgical fixes permitted with clear evidence)
parallelizable_with: []
depends_on: [EXEC_BRIEF_PHASE_12_v1_0.md (COMPLETE)]
output_artifact: platform/scripts/cutover/retrieval_audit_report.md
---

# EXEC_BRIEF — Phase 13 — Retrieval Completeness Audit + Repair

## Mission

Phase 12 fixed the data-flow plumbing — the LLM now receives chart context and bundle content. But the latest D1 query returned `[EXTERNAL_COMPUTATION_REQUIRED]` for many positions (Sun's degree, Moon's degree, Mars's degree, Rahu's/Ketu's degrees + Ketu's nakshatra, house cusps 2-12) that the native confirms ARE present in the corpus.

This is a retrieval-completeness bug, not a corpus-completeness gap. The investigation:

1. Catalog what IS in FORENSIC v8.0 (the source of truth) — every planetary degree, every nakshatra, every cusp.
2. Catalog what IS in `rag_chunks` (the embedded retrieval index) — which chunks carry which facts.
3. Capture what `vector_search` actually retrieved for the failing query — compare against the catalog above. Identify gaps.
4. Diagnose root cause: insufficient top_K, weak semantic match for degree-specific queries, chunks split awkwardly across boundaries, missing chunks, or LLM not calling vector_search iteratively.
5. Either apply a surgical fix (if root cause is unambiguous) or recommend a follow-up brief.

This is a tight, scoped investigation that mirrors the Phase 11A.DEBUG pattern: catalog → trace → diagnose → minimal-fix-or-recommend.

## Pre-flight gate

1. **Cloud SQL Auth Proxy MUST be running.** Required for `rag_chunks` and `audit_log` reads.
   ```bash
   pgrep -fl 'cloud[_-]sql[_-]proxy' || echo "PROXY NOT RUNNING — HALT"
   ```
2. Verify Phase 12 is COMPLETE (frontmatter check on `EXEC_BRIEF_PHASE_12_v1_0.md`).
3. Verify FORENSIC source file exists at `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`.

If any fail, halt with a clear message.

## Scope

**`may_touch` (read access):** all of `01_FACTS_LAYER/`, `platform/src/`, the live Cloud SQL DB via existing tooling.

**`may_touch` (write access — narrow):**
- `platform/scripts/cutover/retrieval_audit_report.md` (new — output)
- `platform/scripts/cutover/retrieval_audit_*.json` (new — evidence dumps)
- Surgical code fixes only if ALL of: (1) root cause unambiguous, (2) ≤10 lines change, (3) in non-frozen scope, (4) documented in report

**`must_not_touch`:**
- Any feature flag (keep new pipeline ON throughout)
- Any DB schema, `rag_chunks` content, `msr_signals` content (read-only)
- Re-embedding any chunks (out of scope — that's a corpus rebuild operation)
- `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (governance — read-only here)
- `platform/python-sidecar/rag/embed.py` (frozen)

## Sub-streams (5 sequential)

### Stream A — Catalog FORENSIC source

Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` end-to-end. Extract every "fact" into a structured catalog at `platform/scripts/cutover/retrieval_audit_forensic_catalog.json`:

```json
{
  "planetary_positions": {
    "sun": { "sign": "Capricorn", "degree": "...", "house": 10, "nakshatra": "...", "pada": ... },
    "moon": { "sign": "Aquarius", "degree": "...", "house": 11, "nakshatra": "Purva Bhadrapada", "pada": ... },
    "mars": { ... },
    "mercury": { "sign": "Capricorn", "degree": "00°50'", "house": 10, "nakshatra": "Uttara Ashadha", "pada": 2 },
    "jupiter": { ... },
    "venus": { ... },
    "saturn": { "sign": "Libra", "degree": "22°27'", "house": 7, "nakshatra": "Vishakha", "pada": 1 },
    "rahu": { ... },
    "ketu": { ... }
  },
  "house_cusps": {
    "1": { "sign": "Aries", "degree": "12°23'", "nakshatra": "Ashwini", "pada": 4 },
    "2": { ... },
    ...
    "12": { ... }
  },
  "_facts_marked_required_in_response": [
    "sun.degree",
    "sun.nakshatra",
    "moon.degree",
    "mars.degree",
    "rahu.degree",
    "ketu.degree",
    "ketu.nakshatra",
    "cusps.2_through_12"
  ],
  "_facts_present_in_forensic": true | false  // for each item above, whether FORENSIC actually contains it
}
```

For each item the LLM marked `[EXTERNAL_COMPUTATION_REQUIRED]` in the recent response, note in the catalog whether FORENSIC actually carries that data. This is the ground-truth question.

**Stream A output**: section "FORENSIC Catalog" in the report with a per-fact present/absent table.

### Stream B — Catalog `rag_chunks` for FORENSIC

Query Cloud SQL for all chunks tied to FORENSIC content:

```sql
-- Adjust column names to actual schema (likely doc_type, source_doc_id, content)
SELECT id, doc_type, source_doc_id, LENGTH(content) AS content_len,
       SUBSTRING(content, 1, 200) AS content_preview
FROM rag_chunks
WHERE doc_type = 'forensic'  -- or whatever filter identifies FORENSIC chunks
   OR source_doc_id LIKE '%FORENSIC%'
ORDER BY id;
```

Capture all matching chunks to `platform/scripts/cutover/retrieval_audit_forensic_chunks.json`.

For each fact in Stream A's catalog, grep across the captured chunks to find which chunk(s) contain that fact (e.g., search for "Sun" + "Capricorn" + degree pattern; search for "Ketu" + "nakshatra"; search for "cusp 2" or "2nd house cusp"). Build a fact→chunk_id mapping.

**Critical hypothesis test**: for each `[EXTERNAL_COMPUTATION_REQUIRED]` fact, is there a chunk that contains it? If yes, the chunk exists but wasn't retrieved (Stream C will tell us why). If no, the chunk doesn't exist and corpus enrichment is needed (re-chunk + re-embed FORENSIC).

**Stream B output**: section "rag_chunks Catalog" with the fact→chunk_id map and a clear "missing chunks" list.

### Stream C — Capture what `vector_search` actually retrieved

1. From `audit_log`, find the most recent row for the failing query (probably "what is D1 chart details show me in a table" or similar). Capture the full row to `retrieval_audit_failing_query.json`.

2. Extract from the row:
   - `query_text` (the actual user query)
   - `tools_called` (list of tool calls including any vector_search invocations with their `params_hash`)
   - `bundle_keys` (asset_ids referenced)
   - `payload.retrieved_chunks` if present (post-Phase-12 Approach B injects retrieved chunks; should be in the audit payload)
   - `synthesis_input_tokens` (how big was the prompt)
   - `final_output` (the response with the EXTERNAL_COMPUTATION_REQUIRED markers)

3. Identify which chunk_ids the LLM actually saw in its prompt. Compare against the fact→chunk_id map from Stream B.

4. **The key gap question**: of the chunks that contain the missing facts (Stream B), how many made it into the LLM's context (Stream C)? If 0 made it, that's a strong signal vector_search isn't reaching them. If some made it but not others, that's a top_K cutoff issue or a semantic-relevance ranking issue.

**Stream C output**: section "Retrieval vs Reality" with a table: fact / chunk_id-that-has-it / was-retrieved? / why-not-if-missed.

### Stream D — Diagnose root cause

Synthesize Streams A-C. The diagnosis must classify into one or more of:

- **Cause #1: Corpus gap.** Some `[EXTERNAL_COMPUTATION_REQUIRED]` facts are not in FORENSIC. Action: enrich FORENSIC + re-embed. Out of scope for this brief; recommended follow-up.
- **Cause #2: Chunking gap.** Facts are in FORENSIC but split across chunks in a way that semantic search can't find them as a unit (e.g., the table row "Sun | Capricorn | X°Y' | 10th | nakshatra | pada" got split mid-row). Action: re-chunk FORENSIC with table-aware boundaries. Out of scope for this brief; recommended follow-up.
- **Cause #3: Missing chunks in DB.** FORENSIC was edited recently and not all updates were re-embedded. Action: re-embed missing rows. Recommended follow-up.
- **Cause #4: top_K too small.** All facts are in retrievable chunks but vector_search's top_K (probably 10 per Phase 9 brief) cuts off before reaching the chunks with degree/cusp data. Action: increase top_K for chart-heavy query classes. Surgical fix possible (~5 lines).
- **Cause #5: Semantic ranking bias.** vector_search ranks "summary" chunks above "detail" chunks because they semantically match "what is my D1 chart" better. Action: query-rewriting in vector_search to add "degree, nakshatra, cusp, position" expansion terms; OR multi-query retrieval (issue 2-3 sub-queries per high-level user query). Medium-sized fix; recommended follow-up.
- **Cause #6: LLM didn't iterate.** vector_search was called once with the user query; the LLM saw partial data, marked the rest required, and stopped. The architecture supports iterative tool calling but the prompt may not be encouraging it. Action: prompt edit instructing the LLM to call vector_search again with more specific sub-queries before declaring data unavailable. Surgical fix possible (~10 lines in router prompt or synthesis prompt).
- **Cause #7: Tool call wasn't authorized for this query class.** Double-check that the failing query's `query_class` is in the list of classes vector_search is authorized for (Fix A added factual; Phase 12 FUB-4 was supposed to add interpretive/holistic/cross_domain). Surgical check; trivial fix.

The report must state which cause(s) the evidence supports, citing specific findings from Streams A-C.

**Stream D output**: section "Root Cause" with the cause classification + cited evidence.

### Stream E — Apply surgical fix (if applicable) or recommend follow-up

Based on Stream D's diagnosis:

- If **Cause #4** (top_K too small): apply a surgical bump (e.g., default 10 → 20 for factual + holistic classes). Document the diff. Test with the same query and verify gap closure.
- If **Cause #6** (no iteration): apply a prompt edit telling the LLM "before declaring data unavailable, call vector_search with sub-queries targeted at the specific missing data." Document the diff.
- If **Cause #7** (authorization gap): apply the missing few-shot. Trivial.
- If **Cause #1, #2, #3, or #5**: do NOT apply. Write a follow-up brief outline (file paths, scope, risk). The corpus-rebuild and chunking changes are larger and deserve their own scoped briefs.

**Stream E output**: section "Remediation" — either a documented surgical fix that's been applied, or a follow-up brief outline.

## Critical constraints

- **Keep the new pipeline ON.** Do NOT touch `NEW_QUERY_PIPELINE_ENABLED` or `AUDIT_ENABLED`.
- **Read-mostly.** Surgical fixes only with the four conditions in Scope.
- **No re-embedding.** Re-embedding is a corpus rebuild operation (touches the python sidecar's embedding pipeline) and is out of scope for this brief. If diagnosis points there, document it and stop.
- **Cite specific evidence.** Every finding must reference a fact_id, a chunk_id, an audit_log column, or a file:line.
- **Cap report length.** ~600-800 lines is plenty. Don't pad.

## Done criteria

1. FORENSIC catalog written to `retrieval_audit_forensic_catalog.json` with present/absent flag for each `[EXTERNAL_COMPUTATION_REQUIRED]` fact.
2. rag_chunks catalog written to `retrieval_audit_forensic_chunks.json` with fact→chunk_id map.
3. Failing query audit row captured to `retrieval_audit_failing_query.json` with retrieved chunk_ids extracted.
4. Retrieval-vs-reality table present in report; gaps clearly identified.
5. Root cause classified to one or more of Causes #1-#7 with cited evidence.
6. Either surgical fix applied (with documented diff and re-test) OR follow-up brief outline written (with file paths and scope).
7. Native action section in the report: clear "what to do next."

## How native triggers

In a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension):

> Read EXEC_BRIEF_PHASE_13_RETRIEVAL_AUDIT_v1_0.md and execute it.

Make sure Cloud SQL Auth Proxy is running before triggering.

After Sonnet completes, the report at `platform/scripts/cutover/retrieval_audit_report.md` will tell you:
- Which `[EXTERNAL_COMPUTATION_REQUIRED]` items are corpus-side gaps (rare data) vs retrieval-side gaps (data exists, didn't get fetched)
- For retrieval-side gaps, exactly why (top_K, ranking, iteration, authorization)
- Whether a quick fix is in place or what the next brief should do

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when report exists with all 7 done-criteria satisfied

---
artifact: CLAUDECODE_BRIEF_RAG_CHUNKS_CHART_ID_KEYING_v1_0.md
brief_id: RAG_CHUNKS_CHART_ID_KEYING
version: 1.0
status: ACTIVE — executable
authored_at: 2026-06-01
authored_by: cowork-planner
implementation_surface: Claude Code in Google Antigravity IDE (full autonomy incl deploy + prod migration)
autonomy: code → commit → merge to main → migrate prod → deploy → re-embed → verify. No human gate.
why: >
  rag_chunks has NO chart_id/ayanamsha_id/source_type columns (migration 005 base; only 037
  added canonical_id). But rag_embedder.embed_chart_document() already WRITES and DELETEs on
  those columns. So in production the forensic-render → rag_chunks embedding ERRORS against the
  live schema: the forensic docs (shipped 2026-06-01, 5/5 in chart_documents) never land in
  rag_chunks and are NOT RAG-retrievable. This is a live broken path, not just multi-native
  hygiene. Backfill is cheap NOW (single native chart) — the right moment to key the table.
priority_note: >
  This UNBLOCKS retrieval of the forensic render just delivered. Run BEFORE relying on the
  answer:eval baseline for forensic-related queries — otherwise eval will show forensic gaps
  that are really this schema drift.
scope_boundary:
  - "classical_chunks is a SEPARATE table (BPHS/Jaimini/KP/Tajaka — chart-independent). DO NOT add chart_id to it. read_classical_text is unaffected."
  - "chart_id on rag_chunks is NULLABLE: NULL = global/chart-independent corpus row; non-NULL = per-chart (forensic_render, per-chart MSR/UCN/CDLM/CGM)."
may_touch:
  - platform/migrations/                                   (NEW migration — next free number, see §1)
  - platform/python-sidecar/pipeline/writers/rag_embedder.py
  - platform/python-sidecar/pipeline/writers/rag_chunks_writer.py
  - platform/python-sidecar/pipeline/chunkers/*.py
  - platform/python-sidecar/rag/chunk.py
  - platform/python-sidecar/rag/chunkers/*.py
  - platform-mcp/src/tools/*.ts                            (readers — per-chart filter; see §4)
  - platform/src/app/api/citations/preview/route.ts
  - platform/src/lib/build/types.ts , platform/src/lib/contract/types.ts
  - tests alongside each touched module
must_not_touch:
  - classical_chunks and read_classical_text.ts (global corpus — out of scope)
  - pyjhora_adapter/ , the forensic renderer (working)
  - applied migrations (write a NEW one; never edit 005/037)
hard_bans:
  - No Anthropic models. No JH/FORENSIC-v8.0 value oracle.
  - Do NOT make chart_id NOT NULL (global corpus rows legitimately have NULL).
  - Do NOT edit applied migrations; add a new numbered one.
prime_directive: only computed facts.
---

# rag_chunks — key by chart_id (and fix the rag_embedder schema drift)

## 1 · Migration (new file, next free number — verify `git ls-tree origin/main platform/migrations/` ≥ 163)

```sql
ALTER TABLE rag_chunks
  ADD COLUMN IF NOT EXISTS chart_id     UUID REFERENCES charts(chart_id),
  ADD COLUMN IF NOT EXISTS ayanamsha_id TEXT,
  ADD COLUMN IF NOT EXISTS source_type  TEXT;

-- per-chart retrieval + idempotent re-embed support
CREATE INDEX IF NOT EXISTS idx_rag_chunks_chart      ON rag_chunks(chart_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_chart_aya  ON rag_chunks(chart_id, ayanamsha_id, source_type);

-- Backfill existing rows to the native chart (the only chart that exists today).
-- Rows that are genuinely chart-independent (global classical/corpus) stay NULL — but note
-- classical lives in classical_chunks, so most rag_chunks rows ARE per-chart for the native.
UPDATE rag_chunks SET chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
 WHERE chart_id IS NULL AND doc_type IN ('msr_signal','ucn_section','cdlm_cell','l1_fact','domain_report','cgm_node');
```

Pair with a down-migration (drop the columns + indexes). Confirm the native `chart_id`
against `charts` before backfilling. **Do not** set NOT NULL.

## 2 · Reconcile rag_embedder (it already assumes these columns — make the schema match + confirm)

`rag_embedder.embed_chart_document()` already references `chart_id`, `ayanamsha_id`,
`source_type` in its DELETE and INSERT. After §1 the table has them. Verify the INSERT column
list matches the new schema exactly and that the idempotent DELETE
(`WHERE chart_id=%s AND ayanamsha_id=%s AND source_type=%s`) works. Add a test that runs the
embedder against a real `chart_documents` forensic_render row and asserts rag_chunks rows
appear with the right `chart_id`/`source_type` (this would have caught the drift —
[[ship-but-dont-mount-pattern]]).

## 3 · Stamp chart_id in the other writers

Enumerate every `INSERT INTO rag_chunks` site (`grep -rn "INSERT INTO rag_chunks" platform/python-sidecar`):
`rag_chunks_writer.py`, the corpus chunkers (`pipeline/chunkers/*`, `rag/chunkers/*`,
`rag/chunk.py`). Each must set `chart_id` (the build's chart_id for per-chart corpus;
explicit NULL only for genuinely chart-independent rows), plus `ayanamsha_id`/`source_type`
where applicable. Thread the build's `chart_id` through to each chunker call — do not leave it
as an optional defaulting-to-None parameter that silently writes NULL
([[silent-param-feature-toggle]]).

## 4 · Filter readers by chart_id (per-chart only)

`grep -rn "FROM rag_chunks" platform-mcp platform/src` and classify each reader:

- **Per-chart readers** (forensic content, per-chart MSR/UCN/CDLM/CGM, `vector_search`,
  `citations/preview`, `data_coverage`): add a `chart_id = $target OR chart_id IS NULL`
  predicate (NULL lets global rows still surface) — or `chart_id = $target` where global rows
  must be excluded. The agentic/planner retrieval path must pass the active chart_id.
- **Global readers**: anything actually reading `classical_chunks` is OUT of scope — do not
  touch. If a tool reads `rag_chunks` for chart-independent data only, leave it unfiltered but
  document why.

Decide the default: an unscoped `vector_search` over `rag_chunks` must NOT blend two charts
once a second native exists. Until then (single native) behaviour is unchanged, so this is
safe to land now.

## 5 · Verify (prod)

1. Apply the migration to prod; confirm columns + indexes present; backfill ran.
2. Re-run `rag_embedder` for the native forensic docs (or rebuild the native chart) →
   assert `rag_chunks` now has `source_type='forensic_render'` rows with the native `chart_id`.
3. `vector_search` / `citations/preview` for a forensic query returns the forensic chunks
   (they were invisible before this fix).
4. Existing MSR/UCN/CDLM/CGM retrieval still works (backfilled chart_id, no regression).

## 6 · Acceptance criteria

1. New migration adds nullable `chart_id` (FK charts) + `ayanamsha_id` + `source_type` +
   indexes; down-migration present; applied managed migrations untouched.
2. Backfill keys existing native rows; global rows (if any) remain NULL.
3. `rag_embedder` succeeds against the live schema; forensic_render rows land in rag_chunks
   (the previously-broken path now works) — proven by a real-row test.
4. All `INSERT INTO rag_chunks` writers stamp chart_id (required param, not silent-None).
5. Per-chart readers filter by chart_id (`= $target OR IS NULL`); `classical_chunks` untouched.
6. Production: forensic content is RAG-retrievable; MSR/UCN/CDLM/CGM retrieval unregressed.
7. `pytest` + `vitest` green; `tsc --noEmit` clean.

## 7 · Kickoff prompt (paste verbatim)

```
You are an autonomous executor. --dangerously-skip-permissions. Full autonomy: code, commit,
merge to main, apply the prod migration, deploy, re-embed, verify. No human gate.

Setup:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav && git fetch origin
  git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavRagKey -b feature/rag-chunks-chart-id origin/main
  cd /Users/Dev/Vibe-Coding/Apps/MadhavRagKey

Execute 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RAG_CHUNKS_CHART_ID_KEYING_v1_0.md end-to-end.
KEY FINDING to verify first: rag_chunks lacks chart_id/ayanamsha_id/source_type, but
rag_embedder already writes them → forensic→rag_chunks embedding is broken in prod. Confirm by
reproducing the embedder error against the live schema, then fix with the migration.
chart_id is NULLABLE (NULL = global). classical_chunks is SEPARATE — do not touch it or
read_classical_text. Thread chart_id as a REQUIRED param through chunkers (no silent-None).
Filter per-chart readers (chart_id = target OR IS NULL); leave global readers alone.
Add a real-row test for the embedder (the gap that hid this). Never edit applied migrations.
Do NOT edit SESSION_LOG / CURRENT_STATE.

Verify in prod: apply migration → re-embed native forensic docs → assert rag_chunks has
source_type='forensic_render' rows with native chart_id → forensic content now retrievable via
vector_search → MSR/UCN/CDLM/CGM retrieval unregressed.

Append "RAG-KEY MERGED <sha> AC=<n/n>" + prod forensic-chunk count to
00_ARCHITECTURE/CONDUCTOR/pyjhora-followups/RUN_LOG.md. Report migration number, backfilled row
count, forensic-chunk count, and reader-filter list. Keep amjis-web public.
```

---

*End of CLAUDECODE_BRIEF_RAG_CHUNKS_CHART_ID_KEYING_v1_0.md*

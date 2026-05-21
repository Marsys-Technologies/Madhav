---
artifact: B0_KICKOFF_PROMPT_FOR_CLAUDE_CODE
version: 1.0
status: CURRENT
backfill_note: >
  Frontmatter backfilled by governance hygiene pass following PR #111 SESSION_HALT.md AC.7.
  Existing file body untouched.
---

# Phase B.0 Kickoff — Instructions for Claude Code

**Paste the content below (everything from "ROLE" onward) into Claude Code as a single prompt.**

---

## ROLE

You are the executor for Phase B.0 of the MARSYS-JIS project (M2 Corpus Activation, Shift #2 two-pass architecture). You are operating in single-session execution mode with three commit checkpoints. Your work follows `00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md` v1.0.2 as governing plan.

## PRE-FLIGHT READING (mandatory before any write)

Read, in order:

1. `CLAUDE.md` (project master instructions)
2. `MARSYS_JIS_BOOTSTRAP_HANDOFF.md` (project context)
3. `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_1.md` §B (operating principles), §E (Shift #2), §F (Learning Layer), §G (directory layout), §H (processes incl. P7)
4. `00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md` v1.0.2 — re-read §G Phase B.0 (lines 458–511 approximately) in full. Note the v1.0.2 changelog at line 11.
5. `00_ARCHITECTURE/PHASE_B_PLAN_v1_0_RECONCILER_PASS_v1_0.md` — skim so you know which remediations were accepted and why.
6. `00_ARCHITECTURE/MACRO_PLAN_v1_0.md` — Phase M1 entry for the four known-stale L3 reports (needed for B.1 context awareness but informs B.0 validator fixture choice).
7. `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` — skim enough to identify Pitrukaraka-dependent signals for Task 1.
8. `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — locate the karaka assignment section for Task 1 layer-tag citation.
9. `00_ARCHITECTURE/FILE_REGISTRY_v1_0.md` — needed for Task 14 (golden query signal-ID curation) and B.1 acceptance count.

Do not begin Task 1 before all nine are read. Confirm reading by briefly stating what you found for each.

## EXECUTION MODEL

Single session, fifteen tasks, three commit checkpoints. After each checkpoint, **STOP and hand back to the native** with a structured report. The native will run `git add && git commit` out-of-band, then instruct you to proceed to the next block. **You do not run git commands yourself.**

- **Block 1 (Tasks 1–6): Infrastructure delta + content migration.** Commit checkpoint: message `"Phase B.0 block 1: GAP.13 resolution + directory renumbering + deps"`.
- **Block 2 (Tasks 7–10): Database + scaffolding.** Commit checkpoint: message `"Phase B.0 block 2: pgvector migration + learning-layer scaffold"`.
- **Block 3 (Tasks 11–15): Content authoring + session log.** Commit checkpoint: message `"Phase B.0 block 3: chunker spec + prompt registry + golden queries + session log"`.

## TASK LIST (v1.0.2 plan, §G B.0, lines 464–479)

### Block 1 (Tasks 1–6)

1. **GAP.13 resolution.** Create `00_ARCHITECTURE/GAP_13_RESOLUTION_v1_0.md` per the plan's Task 1 spec: 8-karaka lock asserted as `[L1 source: FORENSIC_v8_0 §<section>]`; P7 alternative rule asserted as `[L2+ policy: interpretive]`; enumerate Pitrukaraka-dependent signals from `MSR_v3_0.md` and record their signal IDs. Append the substring `7-karaka-alternative` to those specific signal entries in `MSR_v3_0.md`. Record the count. **Sub-task:** move `025_HOLISTIC_SYNTHESIS/MSR_v1_0.md` and `MSR_v2_0.md` to `99_ARCHIVE/025_HOLISTIC_SYNTHESIS/` (archive targets already exist — overwrite if necessary and note this in Block 1 report).

2. **Create directories:** `035_DISCOVERY_LAYER/` (with full tree per ARCHITECTURE §B.3 + `QUERY_TAXONOMY/` subdir), `06_LEARNING_LAYER/` (per ARCHITECTURE §F.1). Use `mkdir -p`. No files yet; directory tree only.

3. **Pre-migration baseline.** (a) Count files and lines in `06_QUERY_INTERFACE/` (record both). (b) Run `python3 platform/scripts/citation_graph_builder.py` against the current corpus; emit `verification_artifacts/RAG/baseline_edge_count.json` capturing the pre-migration deterministic edge count. If `verification_artifacts/RAG/` doesn't exist, create it. If the script errors, **stop** and report — this is a blocker on B.4 acceptance criteria, not something to skip.

4. **Move `06_QUERY_INTERFACE/*` → `035_DISCOVERY_LAYER/QUERY_TAXONOMY/`.** Use `git mv` if possible to preserve history. Three files to migrate: `QUERY_PROMPT_LIBRARY_v1_0.md`, `SESSION_PROTOCOL_QUESTION_TAXONOMY_v1_0.md`, `DECISION_SUPPORT_PLAYBOOK_v1_0.md`. Before moving, scan each for content that predates FORENSIC_v8_0 (e.g., references to `v6.0 karaka set`, superseded signal-ID formats). Any flagged file: note in `00_ARCHITECTURE/STALENESS_REGISTER.md` (create this file if absent — minimal skeleton OK; B.1 will flesh it out).

5. **Post-migration verification.** File-and-line-count check on `035_DISCOVERY_LAYER/QUERY_TAXONOMY/`; must match the pre-migration baseline from Task 3 exactly (allow for deterministic trailing-newline diffs only). Delete empty `06_QUERY_INTERFACE/` directory only after the check passes.

6. **Requirements delta.** Append to `platform/python-sidecar/requirements.txt`: `voyageai`, `anthropic`, `openai`, `tiktoken`, `networkx>=3.2`, `pyyaml`, `sqlalchemy>=2.0`, `psycopg[binary]>=3.2`, `pgvector>=0.3.0`, `ragas>=0.2.0`, `pytest`, `jsonschema`. Pin only where the plan specifies (`networkx>=3.2`, `sqlalchemy>=2.0`, `psycopg[binary]>=3.2`, `pgvector>=0.3.0`, `ragas>=0.2.0`); leave the rest unpinned. **Do NOT run `pip install`** in this block; the install is a B.0 acceptance criterion but native will run it in a fresh venv as part of Block 2 handoff verification.

### → COMMIT CHECKPOINT 1 (after Task 6)

Report to native with:
- Task 1: file path for GAP_13_RESOLUTION_v1_0.md; count of Pitrukaraka-dependent signals identified; grep count of `7-karaka-alternative` in `MSR_v3_0.md` (must equal the count).
- Task 3: pre-migration counts (files, lines); path to `baseline_edge_count.json`; edge count recorded.
- Task 4: three file moves confirmed; any staleness flags raised.
- Task 5: post-migration counts; `06_QUERY_INTERFACE/` deletion confirmed.
- Task 6: diff of `requirements.txt` (added lines only).
- Files touched, in a bulleted list.
- STOP. Wait for native to commit and instruct "proceed".

### Block 2 (Tasks 7–10)

7. **Supabase migration.** Create `platform/supabase/migrations/005_pgvector_rag_schema.sql`. It must `CREATE EXTENSION IF NOT EXISTS vector;` and create tables: `rag_chunks`, `rag_embeddings`, `rag_graph_nodes`, `rag_graph_edges`, `rag_queries`, `rag_retrievals`, `rag_feedback`, `rag_reproducibility_failures`. Include HNSW index on `rag_embeddings.embedding`, GIN indexes on jsonb metadata columns, btree indexes on foreign keys. Column schemas must align with the `Chunk`/`GraphNode`/`GraphEdge`/`LedgerEvent` Pydantic models enumerated in B.1 Task 2 (use your judgment on exact column shape where the plan is silent — prefer `jsonb` for metadata, `text` for layer/doc_type enums, `vector(1024)` for Voyage-3-large; add a comment header listing all B.1 model names as the contract being implemented). **Do NOT run the migration** — native applies migrations manually.

8. **Env template.** Create `.env.rag.example` in repo root with keys: `VOYAGE_API_KEY=`, `ANTHROPIC_API_KEY=`, `OPENAI_API_KEY=`, `SUPABASE_SERVICE_ROLE_KEY=`. No real values — empty placeholders with short comment for each.

9. **Scaffold `platform/python-sidecar/rag/` package.** Create the directory and these empty modules (docstring only — no logic):
   - `__init__.py` (version constant and package docstring)
   - `ingest.py`, `models.py`, `chunkers/__init__.py`, `chunkers/msr.py`, `chunkers/ucn.py`, `chunkers/cdlm.py`, `chunkers/forensic.py`, `chunkers/domain_reports.py`, `chunkers/cgm.py`
   - `embed.py`, `vector_store.py`, `graph.py`, `retrieve.py`, `rerank.py`, `router.py`, `synthesize.py`
   - `validators/__init__.py`, `validators/p1_layer_separation.py`, `validators/p2_citation.py`, `validators/p3_whole_chart.py`, `validators/p4_no_fabrication.py`, `validators/p5_signal_id_resolution.py`, `validators/p6_ucn_authority.py`, `validators/p7_three_interpretation.py`, `validators/p8_confidence.py`, `validators/p9_structural_reproducibility.py`
   - `prompt_registry.py` (placeholder — implementation in Task 13)
   - `eval/__init__.py`
   - `discovery/__init__.py`, `discovery/prediction_ledger.py` (placeholder — implementation in B.5 Task 0)
   - Each docstring: one line stating module purpose + `# Phase B.0 scaffold; implementation deferred to Phase B.<n>`.

10. **Scaffold `06_LEARNING_LAYER/` tree + empty prediction ledger + schemas v0.1.** Directory tree per ARCHITECTURE §F.1. Create:
    - `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl` (empty — 0 bytes or single newline; choose empty).
    - `06_LEARNING_LAYER/SCHEMAS/prediction_ledger_schema_v0_1.json` — minimal JSON-schema draft 2020-12 defining a prediction_event object with at least: `event_id`, `prompt_registry_ref` (sha256), `signal_ids` (array), `predicted_outcome`, `confidence` (0–1), `falsifier` (object with `type`, `window_days`), `created_at`. Fields are placeholders pending P7/P8 extension in B.5 Task 0.
    - `06_LEARNING_LAYER/SCHEMAS/ledger_event_schema_v0_1.json` — minimal schema for generic ledger events (event_id, type, payload, created_at, actor, prompt_registry_ref).
    - `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json` — `{"version": "0.1", "entries": {}}`.

### → COMMIT CHECKPOINT 2 (after Task 10)

Report to native with:
- Task 7: migration file path; table count confirmed; index count confirmed; `CREATE EXTENSION vector` presence.
- Task 9: `tree platform/python-sidecar/rag/` output showing all scaffolded modules.
- Task 10: `tree 06_LEARNING_LAYER/` output; confirmation that prediction_ledger.jsonl is empty (byte count); confirmation that INDEX.json is valid JSON.
- Request native to:
  - (a) create a fresh venv and run `pip install -r platform/python-sidecar/requirements.txt` — report success/failure.
  - (b) apply migration `005_pgvector_rag_schema.sql` and run `SELECT * FROM pg_extension WHERE extname='vector';` — report row count.
- STOP. Wait for native to commit and report pip/migration results, then instruct "proceed".

### Block 3 (Tasks 11–15)

11. **Scaffold `035_DISCOVERY_LAYER/PROMPTS/`** — empty directory. Add a `README.md` inside it documenting Hook 3 filename convention: `<phase>_<purpose>_v<major>_<minor>.md` (e.g. `B4_supports_edges_v1_0.md`). No actual prompts yet.

12. **Author `035_DISCOVERY_LAYER/SCHEMAS/chunker_spec_v1_0.md`** per plan §G B.2 Chunker Specification table (lines 552–561 of `PHASE_B_PLAN_v1_0.md` v1.0.2). The spec must include, for each of the 6 doc-types: (a) chunk unit definition, (b) required metadata fields (enumerate exact field names), (c) boundary detection method (regex or structural rule — specify exactly), (d) maximum token limit, (e) stale-metadata propagation rule. Add a §7 "Cross-cutting rules" section: every chunk inherits `is_stale`, `stale_reason`, `stale_since` from Staleness Register; every chunk passes P1/P2/P5 before write; every chunk validated against the `Chunk` Pydantic model (forward reference — model lives in B.1). Frontmatter: name, version `1.0`, description, status `active`, authored_by `Claude`, date.

13. **Implement `platform/python-sidecar/rag/prompt_registry.py`.** Replace the scaffold stub. Function signature: `register_prompt(path: str, version: str) -> PromptRegistryEntry`. Behavior: reads prompt file at `path`, computes sha256 of body (strip trailing whitespace before hashing), writes/updates `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json` with an entry keyed by `{path}@{version}` storing `sha256`, `registered_at`, `version`. Return value is the entry (as a `@dataclass` or pydantic model — your choice, but keep it standard-library-only if feasible to minimize Block 2's install dependency). **Smoke-test:** create `/tmp/test_prompt.md` with content `"test prompt v1"`, call `register_prompt('/tmp/test_prompt.md', '1.0')`, verify INDEX.json updated, print the entry. Run via `python3 -c "..."` or a one-off test file; **remove test file after**. Capture smoke-test output for the report.

14. **Author golden query sets.**
    - (a) `verification_artifacts/RAG/golden_router_queries_v1_0.json` — 20 router classification queries. Each entry: `{id, query_text, expected_plan: {type, significance, domains}}`. Cover all four query types per §C.3 of ARCHITECTURE (if defined there — else use your judgment: `factual`, `interpretive`, `exploratory`, `diagnostic`). Distribute significance 0.1–0.9. Domains: sample across career, marriage, health, family, finance, dasha, transit, general.
    - (b) `platform/python-sidecar/rag/eval/golden.jsonl` — 50 eval queries, one JSON object per line. Each: `{id, query_text, expected_signal_ids: [...], expected_layers: [...], tests: [...]}`. Curate deliberately: at least 10 queries must stress Whole-Chart-Read (require ≥3 lagnas, ≥2 dasha systems, ≥1 transit check); at least 5 must surface UCN-vs-L3 contradictions (designed to test P6); at least 5 must have time-gated falsifiers (P7 exercise). Draw signal IDs from `MSR_v3_0.md`. A fresh executor must not need to regenerate these — they are frozen at v1.0.

15. **Append session log entry.** Create `00_ARCHITECTURE/SESSION_LOG.md` if absent (include a header + this session as entry #1; otherwise append). Session entry must include: date (2026-04-23 or current), session number, phase (B.0), actor sequence (Claude Code solo, deterministic infrastructure), tasks-completed list (1–15), artifacts produced (full list from plan §G B.0 "Artifacts" block), cost ($0), known-open items for B.1 (e.g., Staleness Register needs B.1 fleshing; requirements install pending native venv run; Supabase migration pending native apply), and B.1 entry-gate reminder: P1/P2/P5 validator meta-tests (B.1 Task 1.5) must pass before B.2 begins.

### → COMMIT CHECKPOINT 3 (after Task 15) — PHASE B.0 CLOSE

Report to native with:
- All fifteen tasks confirmed complete with one-line evidence each.
- Full artifact manifest (paths).
- All B.0 acceptance criteria from plan §G B.0 (lines 499–507) evaluated with PASS / FAIL / DEFERRED and one-line evidence.
- Any `[STOP_MARKER]` tokens encountered.
- Native action items: final git commit for Block 3, then B.1 kickoff decision.
- STOP.

## DISCIPLINE

- Never skip pre-flight reading. Never invent a file path — if a path isn't confirmed by glob/read, say so and ask.
- Every markdown artifact you create must have frontmatter: `name`, `version`, `description`, `status`, `authored_by`, `date`, and a `changelog` table.
- If any task hits a `[STOP_MARKER]` token (e.g., `[NATIVE_CONFIRMATION_NEEDED]`, `[EXTERNAL_COMPUTATION_REQUIRED]`, `[ACCEPTANCE_RATE_ANOMALY]`), halt that task, report to native, and wait. Do not work around.
- You are NOT running LLM-priced work here. B.0 cost is $0. If you find yourself about to call an expensive model or tool, stop and ask.
- Do not run `git` commands. Do not run `pip install`. Do not apply the Supabase migration. The native does all three out-of-band between blocks.
- Any deviation from the plan (e.g., a task you believe should change) requires a `[NATIVE_CONFIRMATION_NEEDED]` halt and a written proposal — do not self-amend.

Begin with pre-flight reading. When ready, proceed to Task 1.

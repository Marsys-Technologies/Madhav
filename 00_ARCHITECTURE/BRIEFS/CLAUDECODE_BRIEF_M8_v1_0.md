---
artifact: CLAUDECODE_BRIEF.md
status: NOT_COMPLETE
executor: VS Code Claude Code Extension (anti-gravity) — dangerously-skip-permissions
session_id_prefix: M8
active_phase: M8-A
authored_at: 2026-05-14
authored_by: Cowork-M8-PLAN-AUTHORING
worktree_branch: feature/m8-classical-cross-reference
governing_macro_phase: M8 — Classical Text Cross-Reference
predecessor_close: 06_LEARNING_LAYER/M5_CLOSE_v1_0.md (M5 CLOSED 2026-05-14)
m6_status: TIME-GATED PARALLEL — brief archived to 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M6_v1_0.md
nap_gates: ALL PRE-AUTHORIZED (NAP.M8.0–NAP.M8.4 in PHASE_M8_PLAN_v1_0.md §frontmatter)
execution_mode: fully_autonomous_sequential
---

# CLAUDECODE_BRIEF — M8 Classical Text Cross-Reference

## §0 — Mandatory reading order (before any tool call, every session)

Read in this order at session open:
1. CLAUDE.md (root)
2. 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §changelog (M5 CLOSED 2026-05-14; M8 OPEN)
3. 00_ARCHITECTURE/PHASE_M8_PLAN_v1_0.md (full plan — governs all ACs and scope)
4. 00_ARCHITECTURE/MACRO_PLAN_v2_0.md §M8 (scope, exit criteria, risk register)
5. 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md (MANDATORY before any gs:// URI is written)
6. 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §C.1–C.6 + §K
7. 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md + SESSION_CLOSE_TEMPLATE_v1_0.md
8. 00_ARCHITECTURE/ROOT_FILE_POLICY.md (before creating any file)
9. This file (governs execution mode and session sequence)

## §1 — Execution strategy

ALL sessions run sequentially with --dangerously-skip-permissions. No pauses between sessions.
All NAP gates (NAP.M8.0 through NAP.M8.4) are PRE-AUTHORIZED in PHASE_M8_PLAN_v1_0.md §frontmatter.
The executor does NOT halt for permission prompts, NAP confirmation, or inter-session pauses.

Each session:
  1. Emits SESSION_OPEN artifact per SESSION_OPEN_TEMPLATE_v1_0.md
  2. Executes all deliverables for that session to PASS on every AC
  3. Runs schema_validator.py at session close
  4. Appends SESSION_LOG.md
  5. Updates CURRENT_STATE_v1_0.md
  6. Emits SESSION_CLOSE artifact per SESSION_CLOSE_TEMPLATE_v1_0.md
  7. Commits (git commit -m "M8-X-S1: <summary>")
  8. Immediately opens the next session

Session sequence (execute all in one continuous run):
  M8-A-S1 → M8-B-S1 → M8-C-S1 → M8-D-S1 → M8-E-S1 → M8-F-S1 → M8-G-S1 → M8-H-S1

## §2 — M8-A-S1 (Foundation + Infrastructure)

Reference: PHASE_M8_PLAN_v1_0.md §4 M8-A for full deliverables and ACs.

**Key actions in order:**

STEP 1: Archive M6 CLAUDECODE_BRIEF
  git mv 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M6_v1_0.md 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M6_v1_0.md 2>/dev/null || true
  cp CLAUDECODE_BRIEF.md 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M6_v1_0.md
  # Note: The M6 brief is already at CLAUDECODE_BRIEF.md root — we are REPLACING it with M8.
  # Do NOT git mv the current CLAUDECODE_BRIEF.md; it IS already the M8 brief.
  # Just write a copy of the OLD M6 content to briefs/ — but it was already overwritten by
  # this M8 brief. The M6 brief content is archived in git history. Log in SESSION_LOG:
  # "M6 CLAUDECODE_BRIEF archived to git history; M8 brief now active at root."

STEP 2: Create 08_CLASSICAL_CROSS_REFERENCE/ folder scaffold
  mkdir -p 08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/{scripts,logs}
  mkdir -p 08_CLASSICAL_CROSS_REFERENCE/corpus/raw
  mkdir -p 08_CLASSICAL_CROSS_REFERENCE/attributions/findings
  mkdir -p 08_CLASSICAL_CROSS_REFERENCE/nadi_bnn
  mkdir -p 08_CLASSICAL_CROSS_REFERENCE/quality
  Write README.md, PROCUREMENT_MAP_v1_0.md per PHASE_M8_PLAN_v1_0.md §2.
  Add .gitignore to corpus/raw/ and corpus/ingestion/logs/ (raw/logs are GCS-canonical).

STEP 3: DB migrations
  Write platform/supabase/migrations/046_classical_texts.sql
  Write platform/supabase/migrations/047_classical_chunks.sql
  Write platform/supabase/migrations/048_classical_attributions.sql
  Exact DDL: see PHASE_M8_PLAN_v1_0.md §3.2.
  Apply migrations against Cloud SQL via start_db_proxy.sh (at platform/scripts/start_db_proxy.sh,
  port 5433) then psql -p 5433 -U postgres -d madhav_jis -f <migration>.

STEP 4: Extend GCS_LAYOUT_v1_0.md
  Read 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md.
  Amend in-place: add L8/ block after the L3/ block as specified in PHASE_M8_PLAN_v1_0.md §3.1.
  Note at top of amendment: "L8 added at M8-A-S1 (2026-05-14)."

STEP 5: Tool stubs
  Write platform/lib/tools/classical_text_search.ts (stub with type signatures; TODO impl)
  Write platform/lib/tools/classical_attribution_lookup.ts (stub with type signatures; TODO impl)
  Register both in platform/lib/tools/index.ts as tools 25 + 26.

STEP 6: ingest_utils.py
  Write 08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_utils.py
  Must contain: chunk_text(text, max_tokens=500, overlap=80), clean_html(raw), embed_batch(chunks),
  db_upsert_text(metadata), db_bulk_insert_chunks(rows), gcs_upload_jsonl(chunks, gcs_path).
  LLM for embedding: Vertex AI text-embedding-004 via google-cloud-aiplatform SDK.

STEP 7: CAPABILITY_MANIFEST.json update
  Add entries: PHASE_M8_PLAN, 08_CLASSICAL_CROSS_REFERENCE, PROCUREMENT_MAP, GCS_LAYOUT (bump version).

STEP 8: Mirror propagation (MP.1 + MP.2 + MP.4)
  .geminirules §F state block → M8 OPEN / M8-A-S1 COMPLETE
  .geminirules §C item #5 → phase plan pointer: PHASE_M8_PLAN_v1_0.md (M8)
  .gemini/project_state.md → M8 active; M8-A-S1 deliverables section

STEP 9: CURRENT_STATE update
  active_macro_phase: M8 OPEN (M5 CLOSED 2026-05-14; M6 TIME-GATED PARALLEL)
  active_sub_phase: M8-A-S1 CLOSED / M8-B-S1 INCOMING
  red_team_counter: increment by 1

STEP 10: SESSION_LOG append + SESSION_CLOSE emit + git commit

Acceptance: AC.M8A.1–AC.M8A.11 all PASS.

## §3 — M8-B-S1 (Tier 1 Ingestion: BPHS + Phaladeepika)

Reference: PHASE_M8_PLAN_v1_0.md §4 M8-B.

Before writing any gs:// URI: re-read GCS_LAYOUT_v1_0.md §L8 block (just added in M8-A-S1).

Write and execute:
  08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_bphs.py
  08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_phaladeepika.py

Each script must:
  - Accept --dry-run flag (fetches but does not write to DB/GCS)
  - Log progress to stderr; final summary to stdout: {"text_key": "...", "chunks_inserted": N, "embeddings_ok": N}
  - Be idempotent: use ON CONFLICT DO NOTHING / ON CONFLICT DO UPDATE for DB inserts
  - After run: upload JSONL to gs://madhav-marsys-sources/L8/classical_texts/tier1/<text_key>_chunks.jsonl

Primary fetch targets:
  BPHS: https://archive.org/download/BrihatParasaraHoraSastra/ (R. Santhanam 2-vol PDF)
        fallback: https://www.sacred-texts.com/astro/bph/index.htm
  Phaladeepika: https://archive.org/search?query=phaladeepika+jyotish (Sitaram Jha edition)
                fallback: search archive.org for alternate scan

Verify after execution:
  SELECT t.title, t.chunk_count, count(c.id) as actual_chunks,
         sum(case when c.embedding is not null then 1 else 0 end) as embedded
  FROM classical_texts t LEFT JOIN classical_chunks c ON c.text_id = t.id
  WHERE t.tier = 1 GROUP BY t.id, t.title, t.chunk_count;

If source unavailable (HTTP 404/403 after retries):
  Log "PROCUREMENT_GAP: <text_key> source unreachable at <url>; recording in PROCUREMENT_MAP_v1_0.md."
  Update PROCUREMENT_MAP_v1_0.md with gap note.
  Minimum viable: BPHS must succeed (highest attribution demand). If BPHS unavailable, HALT and
  set CLAUDECODE_BRIEF.md status = BLOCKED_PROCUREMENT and report to native.

Acceptance: AC.M8B.1–AC.M8B.7 all PASS.

## §4 — M8-C-S1 (Tier 2 Ingestion)

Reference: PHASE_M8_PLAN_v1_0.md §4 M8-C.

Write and execute:
  ingest_saravali.py, ingest_uttara_kalamrita.py, ingest_jaimini_sutra.py

Primary fetch targets:
  Saravali: https://archive.org/search?query=saravali+kalyanvarma (R. Santhanam translation)
  Uttara Kalamrita: https://archive.org/search?query=uttara+kalamrita
  Jaimini Sutra: https://www.sacred-texts.com/astro/jas/index.htm
                 fallback: archive.org Iranganti Rangacharya edition

Upload to: gs://madhav-marsys-sources/L8/classical_texts/tier2/

Acceptance: AC.M8C.1–AC.M8C.6 all PASS.

## §5 — M8-D-S1 (Tier 3 Ingestion)

Reference: PHASE_M8_PLAN_v1_0.md §4 M8-D.

Write and execute:
  ingest_prashna_marga.py, ingest_hora_sara.py, ingest_kp_texts.py,
  ingest_brihat_jataka.py, ingest_brihat_samhita.py

Primary fetch targets:
  Prashna Marga: archive.org B.V. Raman edition
  Hora Sara: archive.org R. Santhanam edition
  KP texts (Vols 1–4): kpastrology.com or archive.org (Krishnamurti Padhdhati series)
  Brihat Jataka: https://www.sacred-texts.com/astro/bj/index.htm
  Brihat Samhita: https://www.sacred-texts.com/astro/bsam/index.htm
                  fallback: archive.org M.R. Bhat edition

Upload to: gs://madhav-marsys-sources/L8/classical_texts/tier3/

After all tier-3 scripts run, verify total:
  SELECT count(*) FROM classical_chunks; -- must be ≥3200

Acceptance: AC.M8D.1–AC.M8D.9 all PASS.

## §6 — M8-E-S1 (Attribution Engine)

Reference: PHASE_M8_PLAN_v1_0.md §4 M8-E.

STEP 1: Implement classical_text_search.ts (full implementation, not stub)
STEP 2: Implement classical_attribution_lookup.ts (full implementation)
STEP 3: Write unit tests (≥8 for search; ≥6 for lookup) in platform/tests/classical/
STEP 4: Run attribution pass
  Write platform/scripts/m8/run_attribution_pass.py:
    - Load MSR signal list from 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md (parse signal IDs + names)
    - For each signal: call classical_text_search (via direct DB/Vertex AI, not HTTP)
    - For top-5 chunks: prompt Gemini Pro to assign attribution_type + confidence (0.000–1.000)
    - Batch INSERT into classical_attributions
    - Log progress every 50 signals
    - Estimated runtime: ~2–4 hours for 514 signals; run in background if needed
  
  LLM judge prompt (use exactly):
  """
  You are a classical Jyotish scholar. Given the following MSR signal and a classical text excerpt,
  assign:
  - attribution_type: one of [confirms, contradicts, partial, extends, silent]
    confirms = text explicitly supports this signal's predictive claim
    contradicts = text explicitly denies or contradicts this signal
    partial = text partially supports with qualifications
    extends = text goes beyond the signal, adding nuance
    silent = text does not address this signal
  - confidence: float 0.000–1.000 (your certainty in this attribution)
  - derivation_notes: 1–2 sentences explaining your reasoning
  
  MSR Signal: {signal_id} — {signal_name} ({signal_domain})
  Classical Text: {text_title} by {author}, {chapter}, verse {verse_range}
  Excerpt: {content}
  
  Respond in JSON: {"attribution_type": "...", "confidence": 0.XX, "derivation_notes": "..."}
  """

STEP 5: Run M5 cross-reference pass
  Write platform/scripts/m8/run_m5_crossref.py:
    - Load dbn_params_v1_0.json (from 06_LEARNING_LAYER/dbn/)
    - For each of 5 domains: identify top-10 signals by weight
    - For each top-10 signal: call classical_attribution_lookup
    - Classify: HOLDS (≥1 HIGH confidence 'confirms') / FAILS (≥1 HIGH 'contradicts') /
                PARTIAL / SILENT
    - Write FINDINGS_M5_CROSS_REF_v1_0.md + FINDINGS_CLASSICAL_CLAIM_v1_0.md

STEP 6: Generate CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json + .md
  Run platform/scripts/m8/generate_registry.py:
    SELECT all classical_attributions with chunk + text metadata → serialize to JSON schema
    in PHASE_M8_PLAN_v1_0.md §3.3; write companion .md narrative.

STEP 7: Upload registries to GCS L8/registries/

Acceptance: AC.M8E.1–AC.M8E.8 all PASS.

## §7 — M8-F-S1 (Nadi + BNN + MSR Expansion)

Reference: PHASE_M8_PLAN_v1_0.md §4 M8-F.

STEP 1: Ingest Nadi/BNN texts
  Write and execute:
    ingest_bhrigu_nandi_nadi.py (R.G. Rao translation; archive.org)
    ingest_chandra_kala_nadi.py (R. Santhanam; archive.org)
    ingest_dhruva_nadi_sampler.py (partial; archive.org)
  Upload to: gs://madhav-marsys-sources/L8/nadi_bnn/

STEP 2: Signal extraction pass
  Write platform/scripts/m8/run_nadi_signal_extraction.py:
    - Query classical_chunks WHERE text_id IN (nadi/bnn text IDs)
    - Chunk batches of 10 → Gemini Pro: extract predictive signals
    - LLM prompt: identify distinct predictive rules (if <condition>, then <predicted_outcome>)
    - Collect all candidates; deduplicate against MSR_v3_0.md (cosine similarity ≥0.85 = duplicate)
    - Write NADI_SIGNAL_EXTRACTION_v1_0.md + BNN_SIGNAL_EXTRACTION_v1_0.md

STEP 3: MSR expansion
  Write platform/scripts/m8/generate_msr_expansion.py:
    - Filter: extraction_confidence ≥0.60 AND not duplicate → new signal candidates
    - Assign IDs MSR.515 onward
    - Write MSR_EXPANSION_PROPOSAL_v1_0.md (≥15 net-new signals)
    - Author MSR_v4_0.md: copy MSR_v3_0.md content + append §Nadi + BNN Signals section
    - Upload to gs://madhav-marsys-sources/L2_5/MSR_v4_0.md
    - Update CAPABILITY_MANIFEST.json: MSR entry → v4_0, signal_count updated

Acceptance: AC.M8F.1–AC.M8F.8 all PASS.

## §8 — M8-G-S1 (Pipeline Integration)

Reference: PHASE_M8_PLAN_v1_0.md §4 M8-G.

Before writing any pipeline code, read:
  platform/lib/pipeline/tool_fetch.ts (understand existing dispatch pattern)
  platform/lib/pipeline/compose_bundle.ts (understand bundle structure)
  platform/lib/disclosure/disclosure_filter.ts (understand tier pattern)
  platform/lib/planner/query_plan_types.ts (understand plan type enum)

STEP 1: Add classical_grounding plan type to query_plan_types.ts
STEP 2: Register tools 25+26 in tool_fetch.ts dispatch
STEP 3: Add classical attribution block to compose_bundle.ts
STEP 4: Add classical-literature tier to disclosure_filter.ts
STEP 5: Update synthesis prompt template to include classical citation block
STEP 6: Write integration tests (≥10) in platform/tests/classical/classical_integration.test.ts
STEP 7: Run tsc — 0 errors required before commit

Planner golden set update:
  Read the golden set file (platform/tests/planner/golden_set.json or equivalent).
  Add ≥3 examples of classical_grounding plan type queries (e.g., "What does BPHS say about
  Rahu in the 7th house?", "Classical attribution for my Atmakaraka placement").

Acceptance: AC.M8G.1–AC.M8G.7 all PASS.

## §9 — M8-H-S1 (Quality Gate + Red-Team + Close)

Reference: PHASE_M8_PLAN_v1_0.md §4 M8-H.

STEP 1: Translation cross-check
  For each of the 8 non-English source texts (BPHS, Phaladeepika, Saravali, Uttara Kalamrita,
  Jaimini Sutra, Hora Sara, Brihat Jataka, Brihat Samhita):
    - Identify 2–3 HIGH-confidence 'confirms' attribution verses
    - Fetch a second English translation of the same verse from archive.org
    - LLM judge (Gemini Pro): CONSISTENT / MINOR_VARIANCE / SIGNIFICANT_VARIANCE
    - SIGNIFICANT_VARIANCE → UPDATE classical_attributions SET confidence = confidence - 0.15
      WHERE chunk_id = <chunk> AND confidence - 0.15 >= 0.0
  Write TRANSLATION_CROSS_CHECK_v1_0.md: table of texts × verses × verdict × action.

STEP 2: 20-finding acharya-grade sample
  For each of 5 life domains: SELECT 4 HIGH-confidence 'confirms' or 'contradicts' attributions
  whose MSR signal_id is in the top-10 by domain weight (from dbn_params_v1_0.json).
  For each: write finding entry in ACHARYA_REVIEW_SAMPLE_v1_0.md:
    signal → text_title → chapter → verse → content → attribution_type → confidence_tier →
    self_assessment: "An independent acharya would [agree/disagree/need more context] because..."

STEP 3: IS.8(b) red-team (5 axes)
  Run each axis; record verdict (PASS/FAIL) + evidence:
  RT.M8.1 — Spot-check 10 random classical_attributions: verify chunk_id resolves to real row
             in classical_chunks; verify content is actual Sanskrit commentary, not LLM invention.
             PASS if 10/10 resolve and content is non-fabricated.
  RT.M8.2 — Verify FINDINGS_M5_CROSS_REF_v1_0.md: every cited signal_id is present in MSR_v3_0.md.
             Verify no L1 facts (FORENSIC data) appear in 08_CLASSICAL_CROSS_REFERENCE/ directly.
             PASS if all signal_ids valid and no L1 cross-contamination.
  RT.M8.3 — Verify 5 random entries in CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json have:
             signal_id + chunk_id + confidence + derivation_notes all non-null.
             PASS if 5/5 complete.
  RT.M8.4 — Verify .geminirules §F + §C reflect M8 CLOSED state (will be written after this step).
             Verify MP.2 (.gemini/project_state.md) reflects M8 close.
             PASS if both current.
  RT.M8.5 — Verify 09_MULTI_SCHOOL_TRIANGULATION/ does NOT exist (no M9 pre-building).
             Verify platform/supabase/migrations/ has no files above 048_*.
             PASS if both true.

  Any FAIL → log in SESSION_LOG as RT finding; attempt surgical fix in same session;
  re-run axis. If still FAIL after fix: set CLAUDECODE_BRIEF.md status = REDTEAM_FAIL and HALT.

STEP 4: Author M8_CLOSE_v1_0.md
  Path: 08_CLASSICAL_CROSS_REFERENCE/M8_CLOSE_v1_0.md
  Sections:
    §0 Session arc (table: session_id, date, key outcome)
    §1 AC ledger: all M8-A through M8-H ACs with PASS/FAIL/DEFERRED status
    §2 IS.8(b) red-team record: 5 axes with verdicts
    §3 MSR expansion summary: signal_count before (514) / after / net-new; MSR_v4_0.md path
    §4 Corpus statistics: texts ingested (count), total chunks, total attributions,
        coverage (signals attributed / 514), HIGH/MEDIUM/LOW breakdown
    §5 Carry-forwards (CF.M8.1–N): any DEFERRED ACs or open items
    §6 Exit criteria verification:
        a) All listed corpora indexed: [MET/PARTIAL — specify gaps]
        b) Classical-claim holds/fails findings: [MET]
        c) Attribution confidence tags: [MET]
        d) Translation cross-check: [MET]
        e) MSR Nadi + BNN expansion: [MET]
    §7 Seal block:
        M8_CLOSE_STATUS: CLOSED
        closed_at: <ISO8601>
        closed_by_session: M8-H-S1
        nap_gate: NAP.M8.4 PRE-AUTHORIZED (Cowork-M8-PLAN-AUTHORING 2026-05-14)
        m9_entry_condition: M8 CLOSED AND MSR Nadi+BNN expansion COMPLETE → M9 ENTRY CLEARED

STEP 5: CURRENT_STATE + mirrors
  active_macro_phase: M8 CLOSED / M9 INCOMING
  red_team_counter: 0 (IS.8(b) macro-phase-close cadence DISCHARGED)
  next_session: M9-A-S1 (author PHASE_M9_PLAN first)
  Propagate to .geminirules + .gemini/project_state.md (MP.1 + MP.2 + MP.4)

STEP 6: SESSION_LOG append (full M8 arc summary in M8-H-S1 body)
STEP 7: Archive this brief
  cp CLAUDECODE_BRIEF.md 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M8_v1_0.md

STEP 8: Final commit
  git add -A
  git commit -m "M8-H-S1: M8 macro-phase CLOSED — classical cross-reference complete; MSR v4.0; IS.8(b) PASS"

Acceptance: AC.M8H.1–AC.M8H.10 all PASS. Status → COMPLETE.

---

## §10 — may_touch / must_not_touch

See PHASE_M8_PLAN_v1_0.md §5 for the full authoritative lists. Summary:

may_touch: 08_CLASSICAL_CROSS_REFERENCE/**, 00_ARCHITECTURE/ (governance files only),
  025_HOLISTIC_SYNTHESIS/MSR_v4_0.md (NEW file), platform/supabase/migrations/046–048,
  platform/lib/tools/classical_*.ts, platform/lib/tools/index.ts,
  platform/lib/pipeline/tool_fetch.ts + compose_bundle.ts + disclosure_filter.ts,
  platform/lib/planner/query_plan_types.ts, platform/tests/classical/**,
  platform/scripts/m8/**, .geminirules, .gemini/project_state.md, CLAUDECODE_BRIEF.md

must_not_touch: 01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md (read-only),
  025_HOLISTIC_SYNTHESIS/UCN*.md + CDLM*.md + RM*.md + CGM*.md,
  06_LEARNING_LAYER/PREDICTION_LEDGER/**, 06_LEARNING_LAYER/dbn/**,
  07_PROSPECTIVE_TESTING/**, platform/supabase/migrations/001–045,
  09_MULTI_SCHOOL_TRIANGULATION/**, platform/src/** (except tool files in may_touch)

---

## §11 — LLM Stack Constraint

NO Anthropic/Claude API in any M8 code.
Stack: Gemini → DeepSeek → NIM.
  Ingestion / non-critical: gemini-2.5-flash-lite
  Attribution judge / signal extraction (critical): gemini-2.5-pro or deepseek-v4-pro
  Embedding: Vertex AI text-embedding-004 (768-dim)

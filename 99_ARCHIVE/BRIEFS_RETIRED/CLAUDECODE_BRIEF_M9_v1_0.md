---
artifact: CLAUDECODE_BRIEF.md
status: NOT_COMPLETE
executor: VS Code Claude Code Extension (anti-gravity) — dangerously-skip-permissions
session_id_prefix: M9
active_phase: M9-A
authored_at: 2026-05-14
authored_by: Cowork-M9-PLAN-AUTHORING
worktree_branch: feature/m9-multi-school-triangulation
governing_macro_phase: M9 — Multi-School Triangulation
predecessor_close: 08_CLASSICAL_CROSS_REFERENCE/M8_CLOSE_v1_0.md (M8 CLOSED 2026-05-14)
m6_status: TIME-GATED PARALLEL — brief archived to 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M6_v1_0.md
m8_brief_archived: 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M8_v1_0.md
nap_gates: ALL PRE-AUTHORIZED (NAP.M9.0–NAP.M9.5 in PHASE_M9_PLAN_v1_0.md §frontmatter)
execution_mode: fully_autonomous_sequential
---

# CLAUDECODE_BRIEF — M9 Multi-School Triangulation

## §0 — Mandatory reading order (before any tool call, every session)

Read in this order at session open:
1. CLAUDE.md (root)
2. 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §changelog (M8 CLOSED 2026-05-14; M9 OPEN)
3. 00_ARCHITECTURE/PHASE_M9_PLAN_v1_0.md (full plan — governs all ACs and scope)
4. 00_ARCHITECTURE/MACRO_PLAN_v2_0.md §M9 (scope, exit criteria, risk register)
5. 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md (MANDATORY before any gs:// URI is written)
6. 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §C.1–C.6 + §K
7. 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md + SESSION_CLOSE_TEMPLATE_v1_0.md
8. 00_ARCHITECTURE/ROOT_FILE_POLICY.md (before creating any file)
9. This file (governs execution mode and session sequence)

## §1 — Execution strategy

ALL sessions run sequentially with --dangerously-skip-permissions. No pauses between sessions.
All NAP gates (NAP.M9.0 through NAP.M9.5) are PRE-AUTHORIZED in PHASE_M9_PLAN_v1_0.md §frontmatter.
The executor does NOT halt for permission prompts, NAP confirmation, or inter-session pauses.

Each session:
  1. Emits SESSION_OPEN artifact per SESSION_OPEN_TEMPLATE_v1_0.md
  2. Executes all deliverables for that session to PASS on every AC
  3. Runs schema_validator.py at session close
  4. Appends SESSION_LOG.md
  5. Updates CURRENT_STATE_v1_0.md
  6. Emits SESSION_CLOSE artifact per SESSION_CLOSE_TEMPLATE_v1_0.md
  7. Commits (git commit -m "M9-X-S1: <summary>")
  8. Immediately opens the next session

Session sequence (execute all in one continuous run):
  M9-A-S1 → M9-B-S1 → M9-C-S1 → M9-D-S1 → M9-E-S1

## §2 — M9-A-S1 (Coverage Audit + Signal Extraction + Infrastructure)

Reference: PHASE_M9_PLAN_v1_0.md §4 M9-A for full deliverables and ACs.

**Key actions in order:**

STEP 1: Archive M8 CLAUDECODE_BRIEF
  cp CLAUDECODE_BRIEF.md 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M8_v1_0.md
  # Note: Only if 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M8_v1_0.md does not already exist.
  # This brief (M9) is now active at root — do not overwrite it.
  # Log in SESSION_LOG: "M8 CLAUDECODE_BRIEF archived; M9 brief now active at root."

STEP 2: Create 09_MULTI_SCHOOL_TRIANGULATION/ folder scaffold
  mkdir -p 09_MULTI_SCHOOL_TRIANGULATION/schools/{parashari,jaimini,tajika,kp,nadi,bnn,yogini}
  mkdir -p 09_MULTI_SCHOOL_TRIANGULATION/convergence
  mkdir -p 09_MULTI_SCHOOL_TRIANGULATION/disagreements
  mkdir -p 09_MULTI_SCHOOL_TRIANGULATION/analysis
  Write README.md in 09_MULTI_SCHOOL_TRIANGULATION/ explaining M9 scope.

STEP 3: DB migrations
  Write platform/supabase/migrations/057_school_signal_coverage.sql
  Write platform/supabase/migrations/058_school_analysis_runs.sql
  Write platform/supabase/migrations/059_convergence_scores.sql
  Write platform/supabase/migrations/060_school_disagreements.sql
  Exact DDL: see PHASE_M9_PLAN_v1_0.md §3.2.
  Apply migrations against Cloud SQL via start_db_proxy.sh (at platform/scripts/start_db_proxy.sh,
  port 5433) then psql -p 5433 -U postgres -d madhav_jis -f <migration>.

STEP 4: Extend GCS_LAYOUT_v1_0.md
  Read 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md.
  Amend in-place: add L9/ block after the L8/ block per PHASE_M9_PLAN_v1_0.md §3.1.
  L9/ prefix structure:
    gs://madhav-marsys-sources/L9/school_analyses/<school>_analysis.json (7 files)
    gs://madhav-marsys-sources/L9/convergence/convergence_scores.json
    gs://madhav-marsys-sources/L9/convergence/school_disagreement_register.json
  Note at top of amendment: "L9 added at M9-A-S1 (2026-05-14)."

STEP 5: Coverage audit script
  Write platform/scripts/m9/run_coverage_audit.py:
    - For each of 543 MSR signals (read MSR_v4_0.md to extract all signal_ids):
      SELECT school, attribution_type, confidence FROM classical_attributions
      JOIN classical_chunks ON classical_chunks.id = classical_attributions.chunk_id
      JOIN classical_texts ON classical_texts.id = classical_chunks.text_id
      WHERE classical_attributions.msr_signal_id = <signal_id>
      → if tradition = 'parashari'/'jaimini'/etc. and confidence ≥ 0.60 → coverage_type = 'primary'
      → if confidence 0.40–0.60 → 'secondary'
      → no row → 'silent'
    - BULK INSERT into school_signal_coverage (ON CONFLICT DO UPDATE)
    - Write SCHOOL_COVERAGE_AUDIT_v1_0.md: per-school primary/secondary/silent counts in table
  
  Run: python3 platform/scripts/m9/run_coverage_audit.py
  Verify: SELECT school, coverage_type, count(*) FROM school_signal_coverage
          GROUP BY school, coverage_type ORDER BY school, coverage_type;
  Expected: ~3,801 rows (543 signals × 7 schools)

STEP 6: Yogini signal extraction
  Write platform/scripts/m9/extract_yogini_signals.py:
    - Query: SELECT * FROM classical_chunks WHERE text_id = (
        SELECT id FROM classical_texts WHERE text_key = 'bphs'
      ) AND content ILIKE ANY(ARRAY[
        '%yogini%','%mangala dasha%','%pingala%','%dhanya%','%bhramari%',
        '%bhadrika%','%ulka%','%siddha%','%sankata%','%yogini dasha%'
      ])
    - Batch Gemini Pro prompt: extract signal_name, yogini_name, domain, trigger_condition,
      predicted_outcome, extraction_confidence for each chunk
    - Dedup against MSR_v4_0.md signals (cosine similarity ≥ 0.85 via Vertex AI embeddings = duplicate)
    - Write YOGINI_SIGNAL_EXTRACTION_v1_0.md (all candidates; promoted list ≥8 signals)
    - Assign IDs SIG.MSR.544 onward for candidates with confidence ≥ 0.60
  
  LLM: gemini-2.5-pro (critical extraction)
  Run: python3 platform/scripts/m9/extract_yogini_signals.py
  Verify: count in YOGINI_SIGNAL_EXTRACTION_v1_0.md ≥ 8 promoted signals

STEP 7: Tajika signal extraction
  Write platform/scripts/m9/extract_tajika_signals.py:
    - First: attempt procurement of Tajika Neelakanthi from archive.org
      URL: https://archive.org/search?query=tajika+neelakanthi OR tajika+neelakantha
      If found: run ingest_utils.py pattern; insert into classical_texts (tier=2,
      tradition='tajika', text_key='tajika_neelakanthi'); include chunks in extraction
      If not found: log "PROCUREMENT_GAP: tajika_neelakanthi unavailable; proceeding with
      Prashna Marga + Hora Sara" — NOT a blocking failure
    - Query classical_chunks WHERE text_id IN (
        SELECT id FROM classical_texts WHERE text_key IN ('prashna_marga','hora_sara')
      ) AND content ILIKE ANY(ARRAY[
        '%tajika%','%varsha%','%sahama%','%ithasala%','%ishrafa%',
        '%muntha%','%varshesha%','%nakta%','%tajaka%','%varshapha%'
      ])
    - Batch Gemini Pro prompt: extract Tajika signals; flag each with solar_return_scope=true
    - Write TAJIKA_SIGNAL_EXTRACTION_v1_0.md (all candidates; promoted list ≥10 signals)
    - Assign IDs after Yogini block (SIG.MSR.544+N onward)
  
  LLM: gemini-2.5-pro (critical extraction)
  Run: python3 platform/scripts/m9/extract_tajika_signals.py
  Verify: count in TAJIKA_SIGNAL_EXTRACTION_v1_0.md ≥ 10 promoted signals

STEP 8: MSR_v5_0.md authoring
  Read 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md (header + signal count).
  Write 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md:
    - Copy MSR_v4_0.md content verbatim (all §I–§VII sections preserved)
    - Append §VIII Yogini Signals (SIG.MSR.544–N: all promoted Yogini signals in tabular format)
    - Append §IX Tajika Signals (SIG.MSR.N+1 onward: all promoted Tajika signals; each marked
      solar_return_scope: true)
    - Frontmatter: version=5.0; status=CURRENT; signal_count = 543 + Yogini_count + Tajika_count;
      predecessor=MSR_v4_0.md (543 signals); produced_during=M9-A-S1; produced_on=<date>
  Upload: gsutil cp 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
              gs://madhav-marsys-sources/L2_5/MSR_v5_0.md
  Update CAPABILITY_MANIFEST.json: MSR entry → v5_0 / version 5.0 / signal_count updated
  Update 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md: MSR entry → MSR_v5_0.md / version 5.0 / CURRENT

STEP 9: Tool stubs 27+28
  Write platform/src/lib/tools/multi_school_signal_lookup.ts (stub; type signatures + TODO)
  Write platform/src/lib/tools/convergence_score_lookup.ts (stub; type signatures + TODO)
  Register both in platform/src/lib/tools/index.ts as tools 27+28
  Input/output shapes per PHASE_M9_PLAN_v1_0.md §3.3.

STEP 10: CAPABILITY_MANIFEST.json update
  Add entries: PHASE_M9_PLAN, 09_MULTI_SCHOOL_TRIANGULATION, SCHOOL_COVERAGE_AUDIT,
  GCS_LAYOUT L9/ block (bump GCS_LAYOUT version).

STEP 11: Mirror propagation (MP.1 + MP.2 + MP.4)
  .geminirules §F state block → M9 OPEN / M9-A-S1 COMPLETE
  .geminirules §C item #5 → phase plan pointer: PHASE_M9_PLAN_v1_0.md (M9)
  .gemini/project_state.md → M9 active; M9-A-S1 deliverables section; school coverage baseline

STEP 12: CURRENT_STATE update
  active_macro_phase: M9 OPEN (M8 CLOSED 2026-05-14)
  active_sub_phase: M9-A-S1 CLOSED / M9-B-S1 INCOMING
  red_team_counter: increment by 1

STEP 13: SESSION_LOG append + SESSION_CLOSE emit + git commit
  git commit -m "M9-A-S1: coverage audit + Yogini/Tajika extraction + MSR v5.0 + infra"

Acceptance: AC.M9A.1–AC.M9A.13 all PASS.

## §3 — M9-B-S1 (Seven School Engines Implementation)

Reference: PHASE_M9_PLAN_v1_0.md §4 M9-B for full deliverables and ACs.

Before writing any school engine code, read:
  platform/src/lib/tools/multi_school_signal_lookup.ts (type signatures from M9-A-S1)
  platform/src/lib/schools/ (empty dir from M9-A-S1 scaffold — now populate it)
  025_HOLISTIC_SYNTHESIS/MSR_v5_0.md (school membership of all signals)

STEP 1: Write platform/src/lib/schools/types.ts
  SchoolName = 'parashari' | 'jaimini' | 'tajika' | 'kp' | 'nadi' | 'bnn' | 'yogini'
  Domain = 'CAREER' | 'HEALTH' | 'RELATIONSHIP' | 'SPIRITUAL' | 'PSYCHOLOGICAL'
  CoverageType = 'primary' | 'secondary' | 'silent'
  SignalScore = { signal_id: string; score: number; weight: number; attribution_ref?: string }
  SchoolResult (full interface per PHASE_M9_PLAN_v1_0.md §3.4)
  SchoolAnalysis (full interface per PHASE_M9_PLAN_v1_0.md §3.4)
  MultiSchoolResult = { results: SchoolResult[]; domain: Domain; runDate: string }

STEP 2: Write all 7 engine files per PHASE_M9_PLAN_v1_0.md §4 M9-B engine notes
  platform/src/lib/schools/parashari_engine.ts:
    - Queries school_signal_coverage WHERE school='parashari' AND coverage_type='primary'
    - Applies dbn_params_v1_0.json weights (read from GCS or local JSON copy)
    - Domain score = weighted sum normalised to 0.0–5.0
    - chart_type: 'natal'

  platform/src/lib/schools/jaimini_engine.ts:
    - Queries school_signal_coverage WHERE school='jaimini' AND coverage_type='primary'
    - Chara Karaka hierarchy modulates weights (AK=Atmakaraka is highest amplifier)
    - AK planet from FORENSIC data (read once; cache)
    - chart_type: 'natal'

  platform/src/lib/schools/kp_engine.ts:
    - Queries school_signal_coverage WHERE school='kp' AND coverage_type='primary'
    - Sub-lord chain for natal chart from FORENSIC (already in L1 data)
    - chart_type: 'natal'

  platform/src/lib/schools/nadi_engine.ts:
    - Queries school_signal_coverage WHERE school='nadi' AND coverage_type='primary'
    - Applies house-from-planet Nadi counting convention (not house-from-Lagna)
    - SIG.MSR.515–541 (CKN signals) are primary
    - chart_type: 'natal'

  platform/src/lib/schools/bnn_engine.ts:
    - Queries school_signal_coverage WHERE school='bnn' AND coverage_type='primary'
    - Transit positions [EXTERNAL_COMPUTATION_REQUIRED: Swiss Ephemeris 2026-05-14]
    - Placeholder: transit data defaults to natal positions; mark output [TRANSIT_DATA_PENDING]
    - chart_type: 'natal' (fallback pending Varsha Kundali)

  platform/src/lib/schools/yogini_engine.ts:
    - Queries school_signal_coverage WHERE school='yogini' AND coverage_type='primary'
    - Compute current Yogini from birth date 1984-02-05:
      36-year cycle starts at birth; compute elapsed years mod 36; map to Yogini table
      At 2026-05-14: elapsed = 42.27 years; mod 36 = 6.27 years into new cycle
      Cycle: Mangala(0-1), Pingala(1-3), Dhanya(3-6), Bhramari(6-10), ...
      At 6.27 years: Bhramari period (Mars, years 6-10) is active
    - Domain character of active Yogini (Bhramari = conflict/energy/property) modulates scores
    - chart_type: 'natal'

  platform/src/lib/schools/tajika_engine.ts:
    - chart_type: 'varsha_kundali'
    - Varsha Kundali for 2026: [EXTERNAL_COMPUTATION_REQUIRED: 2026 solar return chart,
      Bhubaneswar, India, Sun returns to natal longitude ~Jan 25 2026]
    - Until provided: use natal chart as approximation with prominent disclaimer in schoolVerdict
    - All domain scores marked [VARSHA_KUNDALI_PENDING]
    - Excluded from convergence count where this flag is active
    - chart_type in school_analysis_runs: 'varsha_kundali'; varsha_year: 2026
    - LLM for Tajika verdict: gemini-2.5-pro

STEP 3: Write platform/src/lib/schools/convergence_calculator.ts
  Implement computeConvergence(results: SchoolResult[], domain: Domain): ConvergenceScore
  Per PHASE_M9_PLAN_v1_0.md §3.4 — must be deterministic (no random components)
  Tajika: if [VARSHA_KUNDALI_PENDING] flag in tajika result, exclude from schoolsTotal
  (convergence_total drops to 6; document in convergence_narrative)

STEP 4: Write platform/src/lib/schools/school_runner.ts
  Orchestrates all 7 engines in parallel (Promise.all)
  Returns MultiSchoolResult per domain
  Error boundary: if any engine throws, catch + return SchoolResult with
  domainScore=0, schoolVerdict='[ENGINE_ERROR: <message>]', do NOT fail entire run

STEP 5: Write per-school specification documents
  09_MULTI_SCHOOL_TRIANGULATION/schools/parashari/PARASHARI_ENGINE_SPEC_v1_0.md
  09_MULTI_SCHOOL_TRIANGULATION/schools/jaimini/JAIMINI_ENGINE_SPEC_v1_0.md
  09_MULTI_SCHOOL_TRIANGULATION/schools/tajika/TAJIKA_ENGINE_SPEC_v1_0.md
    (must include Varsha Kundali architecture note and [VARSHA_KUNDALI_PENDING] protocol)
  09_MULTI_SCHOOL_TRIANGULATION/schools/kp/KP_ENGINE_SPEC_v1_0.md
  09_MULTI_SCHOOL_TRIANGULATION/schools/nadi/NADI_ENGINE_SPEC_v1_0.md
  09_MULTI_SCHOOL_TRIANGULATION/schools/bnn/BNN_ENGINE_SPEC_v1_0.md
    (must include [TRANSIT_DATA_PENDING] protocol)
  09_MULTI_SCHOOL_TRIANGULATION/schools/yogini/YOGINI_ENGINE_SPEC_v1_0.md
    (must include current Yogini computation: Bhramari active at M9-B execution date)
  Each spec: school philosophy (3–5 sentences); signal sources; engine flow; output format;
  known limitations.

STEP 6: Unit tests
  Write platform/tests/schools/ (one file per engine + convergence_calculator):
    parashari_engine.test.ts — ≥6 tests (mock school_signal_coverage; verify score range 0–5)
    jaimini_engine.test.ts — ≥6 tests
    kp_engine.test.ts — ≥6 tests
    nadi_engine.test.ts — ≥6 tests
    bnn_engine.test.ts — ≥6 tests (verify [TRANSIT_DATA_PENDING] flag present in output)
    yogini_engine.test.ts — ≥6 tests (verify Bhramari active; verify domain score modulation)
    tajika_engine.test.ts — ≥6 tests (verify [VARSHA_KUNDALI_PENDING] flag; verify chart_type='varsha_kundali')
    convergence_calculator.test.ts — ≥10 tests:
      - HIGH convergence when ≥5 schools agree direction
      - MEDIUM when exactly 4 agree
      - LOW when <4 agree
      - Determinism: same input produces byte-identical output
      - Tajika excluded when [VARSHA_KUNDALI_PENDING]; schoolsTotal drops to 6

STEP 7: tsc check
  Run: npx tsc --noEmit --project platform/tsconfig.json
  0 errors required before commit

STEP 8: CURRENT_STATE update + mirrors + SESSION_LOG + commit
  active_sub_phase: M9-B-S1 CLOSED / M9-C-S1 INCOMING
  red_team_counter: increment by 1
  git commit -m "M9-B-S1: 7 school engines + convergence calculator + unit tests"

Acceptance: AC.M9B.1–AC.M9B.9 all PASS.

## §4 — M9-C-S1 (Run All 7 Schools on Abhisek's Chart)

Reference: PHASE_M9_PLAN_v1_0.md §4 M9-C for full deliverables and ACs.

STEP 1: Write platform/scripts/m9/run_multi_school_analysis.py
  - Load chart data from FORENSIC_ASTROLOGICAL_DATA_v8_0.md
    (read file directly; extract planetary positions, house cusps, Lagna, Atmakaraka)
  - For each domain in ['CAREER','HEALTH','RELATIONSHIP','SPIRITUAL','PSYCHOLOGICAL']:
    For each school in ['parashari','jaimini','tajika','kp','nadi','bnn','yogini']:
      a) Import + call school engine analyze() (via ts-node or Python re-implementation)
         Preferred: ts-node -e "import { <Engine> } from 'platform/src/lib/schools/...'; ..."
         Alternative: re-implement engine logic in Python calling DB directly
      b) INSERT into school_analysis_runs (chart_id='abhisek_primary')
      c) Serialize result to per-school JSON accumulator
    Loop end
  - Serialize per-school results to 7 JSON files (one per school)
  - Upload: for each school: gsutil cp /tmp/<school>_analysis.json
      gs://madhav-marsys-sources/L9/school_analyses/<school>_analysis.json

STEP 2: Run the analysis script
  python3 platform/scripts/m9/run_multi_school_analysis.py
  Verify: SELECT school, domain, domain_score, direction FROM school_analysis_runs
          ORDER BY school, domain;
  Expected: 35 rows; no NULL domain_scores; all directions in ['positive','negative','neutral']
  [VARSHA_KUNDALI_PENDING] and [TRANSIT_DATA_PENDING] are logged but NOT treated as failures

STEP 3: Write MULTI_SCHOOL_ANALYSIS_v1_0.md
  Path: 09_MULTI_SCHOOL_TRIANGULATION/analysis/MULTI_SCHOOL_ANALYSIS_v1_0.md
  Sections per PHASE_M9_PLAN_v1_0.md §4 M9-C:
    §1 Executive Summary: convergence preview across 5 domains
    §2–§8 Per-school sections (7 schools): philosophy, per-domain table, school verdict
    §9 Cross-school direction matrix: 7 schools × 5 domains (positive/negative/neutral grid)
    §10 Initial convergence hotspots: domains with 5+ schools in same direction
  Quality standard: acharya-grade prose in all verdict sections. Each school verdict must
  explain WHY this school produces that domain score given the native's placements — not
  generic astrology. Cite specific signal IDs where possible.
  [VARSHA_KUNDALI_PENDING] and [TRANSIT_DATA_PENDING] must appear as explicit disclaimers
  in the Tajika and BNN sections respectively.

STEP 4: IS.8(a) check (every-third-session cadence)
  If red_team_counter (from CURRENT_STATE) has reached 3 since last reset:
    Run IS.8(a) abbreviated check: verify CURRENT_STATE is accurate, no scope drift
  Else: note counter value in SESSION_CLOSE and proceed

STEP 5: CURRENT_STATE update + mirrors + SESSION_LOG + commit
  active_sub_phase: M9-C-S1 CLOSED / M9-D-S1 INCOMING
  git commit -m "M9-C-S1: multi-school analysis complete — 35 runs on Abhisek chart; MULTI_SCHOOL_ANALYSIS_v1_0.md"

Acceptance: AC.M9C.1–AC.M9C.6 all PASS.

## §5 — M9-D-S1 (Convergence Scoring + Pipeline Integration)

Reference: PHASE_M9_PLAN_v1_0.md §4 M9-D for full deliverables and ACs.

Before writing any pipeline code, read:
  platform/src/lib/pipeline/tool_fetch.ts (existing dispatch pattern)
  platform/src/lib/pipeline/compose_bundle.ts (existing bundle structure)
  platform/src/lib/planner/query_plan_types.ts (existing plan type enum)
  platform/src/lib/tools/index.ts (tools 1–28 as of M9-A)

STEP 1: Convergence computation script
  Write platform/scripts/m9/compute_convergence.py:
    - Read school_analysis_runs for all 7 schools × 5 domains
    - Per domain: collect direction values; compute mode; count schools_agreeing
    - Compute: mean_domain_score, std_domain_score
    - Determine convergence_level per formula (≥5 HIGH / 4 MEDIUM / <4 LOW)
    - Tajika: if domain_score marked [VARSHA_KUNDALI_PENDING], exclude from schools_total
      (convergence_level uses N/6 denominator; record schools_total=6 in row)
    - INSERT into convergence_scores (ON CONFLICT DO UPDATE)
    - Serialize to /tmp/convergence_scores.json
    - Upload: gsutil cp /tmp/convergence_scores.json
        gs://madhav-marsys-sources/L9/convergence/convergence_scores.json

STEP 2: Run compute_convergence.py
  python3 platform/scripts/m9/compute_convergence.py
  Verify: SELECT domain, schools_agreeing, convergence_level, direction
          FROM convergence_scores ORDER BY domain;
  Expected: 5 domain rows; convergence_level populated by GENERATED ALWAYS AS expression

STEP 3: Write CONVERGENCE_METRICS_v1_0.md (tabular data)
  Path: 09_MULTI_SCHOOL_TRIANGULATION/convergence/CONVERGENCE_METRICS_v1_0.md
  Table: domain | convergence_level | direction | schools_agreeing/7 | mean_score | std_score
  One row per domain. Raw data for CONVERGENCE_FINDINGS narrative.

STEP 4: Write CONVERGENCE_FINDINGS_v1_0.md (narrative analysis)
  Path: 09_MULTI_SCHOOL_TRIANGULATION/analysis/CONVERGENCE_FINDINGS_v1_0.md
  Sections per PHASE_M9_PLAN_v1_0.md §4 M9-D:
    §1 Convergence Summary Table (from CONVERGENCE_METRICS)
    §2 HIGH convergence domains — acharya-grade narrative on what cross-school agreement means
    §3 LOW convergence domains — nature of divergence and what it reveals about tradition lenses
    §4 Convergence as precision signal — where all schools agree, amplification of signal weight
    §5 Divergence as finding — what each dissenting school is sensitive to that others miss
  Every claim in §2–§5 must cite school_analysis_runs run_ids (derivation ledger discipline)

STEP 5: Tool 27 full implementation (multi_school_signal_lookup)
  Replace stub with full implementation in platform/src/lib/tools/multi_school_signal_lookup.ts:
    Input: { topic: string; domains?: string[]; schools?: string[] }
    Query: school_signal_coverage JOIN classical_chunks JOIN classical_texts
           WHERE signal matches topic (semantic or exact); filter by schools/domains if provided
    Return: PerSchoolResult[] keyed by school name; coverage_type; confidence
  Write ≥6 unit tests in platform/tests/schools/multi_school_signal_lookup.test.ts

STEP 6: Tool 28 full implementation (convergence_score_lookup)
  Replace stub with full implementation in platform/src/lib/tools/convergence_score_lookup.ts:
    Input: { domains: string[] }
    Query: SELECT * FROM convergence_scores WHERE domain = ANY($1) ORDER BY domain
    Return: ConvergenceScore[] with per_school_scores JSONB parsed; convergence_level; narrative
  Write ≥6 unit tests in platform/tests/schools/convergence_score_lookup.test.ts

STEP 7: Pipeline integration
  a) query_plan_types.ts: add 'multi_school_triangulation' to PlanType union
  b) tool_fetch.ts: add dispatch cases for tool 27 (multi_school_signal_lookup)
     and tool 28 (convergence_score_lookup)
  c) compose_bundle.ts: add convergenceContext block to bundle:
     { convergenceLevel, schoolsAgreeing, schoolsTotal, perSchoolScores, direction }
  d) Synthesis prompt template: add multi-school template block:
     "When convergence data is present: 'Schools agreeing: [N/7]. Convergence: [HIGH/MEDIUM/LOW].
     [School list] converge on [direction] for [domain].'"
  e) planner golden set: add ≥3 multi_school_triangulation examples:
     e.g. "What do all seven schools say about my career domain?"
          "Which schools agree on my relationship prospects?"
          "Is there convergence across traditions on my health signals?"

STEP 8: Integration tests
  Write ≥10 integration tests in platform/tests/schools/convergence_integration.test.ts:
    - Tool 27 returns non-empty result for known topic ('Jupiter','Saturn','career')
    - Tool 28 returns convergence rows for all 5 domains
    - Multi_school_triangulation plan type wired; pipeline executes without error
    - compose_bundle includes convergenceContext when plan type is multi_school_triangulation
    - convergenceLevel in output matches DB value

STEP 9: tsc check
  npx tsc --noEmit --project platform/tsconfig.json
  0 errors required before commit

STEP 10: CURRENT_STATE + mirrors + SESSION_LOG + commit
  active_sub_phase: M9-D-S1 CLOSED / M9-E-S1 INCOMING
  git commit -m "M9-D-S1: convergence scoring + pipeline wired; tools 27+28 live; CONVERGENCE_FINDINGS_v1_0.md"

Acceptance: AC.M9D.1–AC.M9D.10 all PASS.

## §6 — M9-E-S1 (Disagreement Register + Quality Gate + M9 Close)

Reference: PHASE_M9_PLAN_v1_0.md §4 M9-E for full deliverables and ACs.

STEP 1: Build disagreement register
  Write platform/scripts/m9/build_disagreement_register.py:
    - For each domain: identify plurality direction from convergence_scores table
    - For each school whose direction != plurality_direction (from school_analysis_runs):
      → record as disagreement candidate
    - Also: for domains with convergence_level = LOW, all cross-school divergences are candidates
    - Classify each by disagreement_class per PHASE_M9_PLAN_v1_0.md §3.2 migration 060:
        method_divergence | signal_gap | tradition_specificity | temporal_scope
    - Use Gemini Pro as judge: prompt each disagreement with school verdicts from MULTI_SCHOOL_ANALYSIS
      and classify + write resolution reasoning + resolution_verdict
    - INSERT into school_disagreements; assign IDs DIS.SCH.001 onward
    - Ensure ≥10 rows with populated worked_example_narrative
  
  LLM judge prompt (use exactly):
  """
  You are a Jyotish scholar familiar with all seven classical schools.
  Two or more schools disagree on the [domain] domain for the native Abhisek Mohanty.
  
  Schools affirming positive direction: [list]
  Schools affirming negative direction: [list]
  Schools silent: [list]
  
  School verdicts:
  [paste abbreviated verdict from each dissenting school]
  
  Classify this disagreement as ONE of:
  - method_divergence: schools use fundamentally different methods to assess [domain]
  - signal_gap: some schools have no signal set for this specific domain aspect
  - tradition_specificity: this signal only exists in one tradition's framework
  - temporal_scope: schools differ on WHEN, not WHETHER, an outcome manifests
  
  Then write:
  - resolution: 2–3 sentences explaining how to read both schools in context
  - resolution_verdict: one of [affirming_majority, denying_majority, context_dependent, unresolved]
  - worked_example_narrative: 3–5 sentences showing how a practitioner would weigh these views
  
  Respond in JSON: {"disagreement_class": "...", "resolution": "...",
                    "resolution_verdict": "...", "worked_example_narrative": "..."}
  """

STEP 2: Run build_disagreement_register.py
  python3 platform/scripts/m9/build_disagreement_register.py
  Verify: SELECT count(*) FROM school_disagreements;
  Required: ≥10 rows; all required fields non-null; worked_example_narrative present

STEP 3: Write SCHOOL_DISAGREEMENT_REGISTER_v1_0.md
  Path: 09_MULTI_SCHOOL_TRIANGULATION/disagreements/SCHOOL_DISAGREEMENT_REGISTER_v1_0.md
  For each of ≥10 disagreements (all DIS.SCH.001 onward):
    Format per PHASE_M9_PLAN_v1_0.md §4 M9-E:
      DIS.SCH.NNN — Domain: [domain]
      Signal: [signal_id if applicable]
      Schools affirming: [list with direction]
      Schools denying: [list with direction]
      Schools silent: [list]
      Disagreement class: [class]
      Resolution: [text]
      Verdict: [verdict]
      Worked example narrative: [3–5 sentence practitioner-level analysis]
      "What this reveals about [school]'s lens": [1–2 sentences per dissenting school]
  Quality standard: acharya-grade; a real Jyotish scholar should recognize the lens-distinction
  being made as accurate to each school's framework.

STEP 4: Upload disagreement register
  Serialize school_disagreements to JSON + upload:
    gsutil cp /tmp/school_disagreement_register.json
        gs://madhav-marsys-sources/L9/convergence/school_disagreement_register.json

STEP 5: Convergence stability check
  python3 platform/scripts/m9/compute_convergence.py (re-run from scratch)
  Compare output /tmp/convergence_scores.json against existing GCS version:
    gsutil cp gs://madhav-marsys-sources/L9/convergence/convergence_scores.json /tmp/convergence_scores_existing.json
    diff /tmp/convergence_scores.json /tmp/convergence_scores_existing.json
  PASS: no differences in convergence_level or direction fields
  FAIL: log as RT finding; investigate non-determinism in convergence_calculator; fix before proceeding

STEP 6: IS.8(b) red-team (5 axes)
  Run each axis; record verdict (PASS/FAIL) + evidence:

  RT.M9.1 — Factual accuracy: spot-check 10 random school_analysis_runs rows
    SELECT * FROM school_analysis_runs ORDER BY RANDOM() LIMIT 10;
    For each: verify signal_ids in top_signals JSONB exist in MSR_v5_0.md
    Verify domainScore is within 0.0–5.0 range; no fabricated signal names
    Verify school names are valid (in ['parashari','jaimini','tajika','kp','nadi','bnn','yogini'])
    PASS if 10/10 valid.

  RT.M9.2 — Layer separation: review MULTI_SCHOOL_ANALYSIS_v1_0.md
    Verify no raw L1 chart values appear as absolute facts (no planetary degrees stated bare)
    Verify all planetary position references cite FORENSIC or specific signal ID
    Verify B.10 discipline: if computation required tool, [EXTERNAL_COMPUTATION_REQUIRED] is present
    PASS if no B.10 violation found in full document read.

  RT.M9.3 — Derivation ledger: review CONVERGENCE_FINDINGS_v1_0.md §2–§5
    Verify every convergence claim cites school_analysis_runs run_ids or specific signal_ids
    Spot-check 5 claims: trace claim → school_analysis_runs row → school_signal_coverage → MSR_v5_0.md
    Verify no claim rests on "as is classically known" without a source
    PASS if 5/5 chains trace cleanly.

  RT.M9.4 — Mirror discipline:
    Read .geminirules §F state block → must say M9 CLOSED
    Read .gemini/project_state.md → must reflect M9 close + M10 INCOMING
    (These will be updated in STEP 8 — verify AFTER STEP 8, not before)
    PASS if both surfaces current after propagation.

  RT.M9.5 — Scope discipline:
    Verify 10_LLM_ACHARYA_INTERFACE/ does NOT exist
    Verify platform/supabase/migrations/ has no files above 060_*
    Verify CLAUDECODE_BRIEF.md status field is COMPLETE (set in STEP 9 below)
    PASS if all three true.

  Any FAIL → log in SESSION_LOG as RT finding; attempt surgical fix in same session; re-run axis.
  If still FAIL after fix: set CLAUDECODE_BRIEF.md status = REDTEAM_FAIL and HALT.

STEP 7: Author M9_CLOSE_v1_0.md
  Path: 09_MULTI_SCHOOL_TRIANGULATION/M9_CLOSE_v1_0.md
  Sections per PHASE_M9_PLAN_v1_0.md §4 M9-E:
    §0 Session arc (table: session_id | date | key outcome)
    §1 AC ledger: all M9-A through M9-E ACs with PASS/FAIL/DEFERRED status
    §2 IS.8(b) red-team record: 5 axes with verdicts + evidence
    §3 MSR evolution: v4.0 (543 signals) → v5.0 (count updated); Yogini count; Tajika count
    §4 Convergence summary: per-domain convergence_level table; top HIGH-convergence domain
    §5 School-disagreement register summary: total disagreements; class breakdown table
    §6 Pending items:
        CF.M9.1 — [VARSHA_KUNDALI_PENDING]: Tajika engine needs 2026 Varsha Kundali chart
          (Swiss Ephemeris external computation). Not blocking M9 close.
        CF.M9.2 — [TRANSIT_DATA_PENDING]: BNN engine needs live transit positions for 2026-05-14
          (Swiss Ephemeris external computation). Not blocking M9 close.
    §7 Exit criteria verification (MACRO_PLAN §M9 a–d):
        a) All 7 schools operating on shared signal set: MET (with CF.M9.1 + CF.M9.2 noted)
        b) Inter-school convergence metrics calibrated: MET — convergence_scores stable
        c) Disagreement protocol ≥10 worked examples: MET — school_disagreements COUNT
        d) Convergence-as-precision-signal evidence: MET — CONVERGENCE_FINDINGS §4
    §8 Seal block:
        M9_CLOSE_STATUS: CLOSED
        closed_at: <ISO8601>
        closed_by_session: M9-E-S1
        nap_gate: NAP.M9.5 PRE-AUTHORIZED (Cowork-M9-PLAN-AUTHORING 2026-05-14)
        m10_entry_condition: M9 CLOSED AND acharya panel ≥3 recruited → M10 ENTRY GATE

STEP 8: CURRENT_STATE + mirrors
  active_macro_phase: M9 CLOSED / M10 INCOMING
  red_team_counter: 0 (IS.8(b) macro-phase-close cadence DISCHARGED)
  next_session: M10-A-S1 (M10 entry gate: acharya panel recruitment prerequisite)
  Propagate to .geminirules + .gemini/project_state.md (MP.1 + MP.2 + MP.4):
    .geminirules §F: M9 CLOSED / M10 INCOMING / red_team_counter=0
    .gemini/project_state.md: M9 full arc summary + M10 entry condition

STEP 9: Archive brief + set status COMPLETE
  cp CLAUDECODE_BRIEF.md 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M9_v1_0.md
  Edit CLAUDECODE_BRIEF.md frontmatter: status → COMPLETE

STEP 10: SESSION_LOG append (full M9 arc summary in M9-E-S1 body)
  Include: school_count=7; domains_analyzed=5; total_runs=35; disagreements=N;
  MSR_v5_0 signal_count=<final>; convergence hotspot domain; CF.M9.1 + CF.M9.2 carried

STEP 11: Final commit
  git add -A
  git commit -m "M9-E-S1: M9 macro-phase CLOSED — 7-school triangulation complete; IS.8(b) PASS"

Acceptance: AC.M9E.1–AC.M9E.12 all PASS. Status → COMPLETE.

---

## §7 — may_touch / must_not_touch

See PHASE_M9_PLAN_v1_0.md §5 for the full authoritative lists. Summary:

may_touch: 09_MULTI_SCHOOL_TRIANGULATION/**, 00_ARCHITECTURE/ (governance files only),
  025_HOLISTIC_SYNTHESIS/MSR_v5_0.md (NEW file; MSR_v4_0.md is read-only),
  platform/supabase/migrations/057–060,
  platform/src/lib/schools/**,
  platform/src/lib/tools/multi_school_signal_lookup.ts,
  platform/src/lib/tools/convergence_score_lookup.ts,
  platform/src/lib/tools/index.ts,
  platform/src/lib/planner/query_plan_types.ts,
  platform/src/lib/pipeline/tool_fetch.ts,
  platform/src/lib/pipeline/compose_bundle.ts,
  platform/scripts/m9/**, platform/tests/schools/**,
  .geminirules, .gemini/project_state.md, CLAUDECODE_BRIEF.md (status + archive only)

must_not_touch: 01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md (read-only),
  025_HOLISTIC_SYNTHESIS/UCN*.md + CDLM*.md + RM*.md + CGM*.md,
  06_LEARNING_LAYER/PREDICTION_LEDGER/**, 06_LEARNING_LAYER/dbn/**,
  07_PROSPECTIVE_TESTING/**, 08_CLASSICAL_CROSS_REFERENCE/** (read-only reference),
  platform/supabase/migrations/001–056 (all prior migrations),
  10_LLM_ACHARYA_INTERFACE/** (do not pre-build M10)

---

## §8 — LLM Stack Constraint

NO Anthropic/Claude API in any M9 code.
Stack: Gemini → DeepSeek → NIM.
  Signal extraction passes (critical): gemini-2.5-pro
  Coverage audit + classification (non-critical): gemini-2.5-flash-lite
  School engine LLM verdicts (critical): gemini-2.5-pro or deepseek-v4-pro
  Disagreement classification judge (critical): gemini-2.5-pro
  Embedding (if needed): Vertex AI text-embedding-004

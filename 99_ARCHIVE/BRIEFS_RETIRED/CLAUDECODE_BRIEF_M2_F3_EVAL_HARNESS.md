---
brief_id: M2_F3_EVAL_HARNESS
karn_session_name: KARN-W7-R3-EVAL-HARNESS
wave: 7
stream: F
status: READY
authored_by: Claude (Cowork) 2026-04-30 — Wave 7 open
authored_for: Claude Code execution (autonomous, long-running)
session_type: scaffold (new eval harness — fixtures + runner + A/B scoring)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §F3
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: |
    KARN-W6-R2-PER-TOOL-PLANNER (D7) — COMPLETE. Adds plan_per_tool stage with
    planner_active flag in trace. Eval harness measures classifier-only vs planner A/B.
    KARN-W6-POSTFIX: Audit 1 PASS (98.99%). W7-R1 required for Audits 2+3.
  blocks: M2 CLOSE (M2 quality bar criterion #7 requires all 3 audits PASS and
    at least one eval harness run showing aggregate score ≥ threshold)
parallel_stream_note: |
  W7-R3 (this brief) runs concurrently with:
  - KARN-W7-R1-AUDIT-REPAIR (F1 — DB backfill; no eval overlap)
  - KARN-W7-R2-MANIFEST-COMPLETENESS (F2 — manifest only; no eval overlap)
  W7-R3 is the ONLY brief that creates files under:
    platform/scripts/eval/
    00_ARCHITECTURE/EVAL/
estimated_time: 3 days single Claude Code session
---

# CLAUDECODE_BRIEF_M2_F3_EVAL_HARNESS
## Wave 7 — Eval Harness Scaffold: Ground-Truth Fixtures + Runner + A/B Scoring

---

## §0 — Pre-flight (read before any tool call)

```
ROOT = ~/Vibe-Coding/Apps/Madhav
PLATFORM = ~/Vibe-Coding/Apps/Madhav/platform
```

Read in order before any action:
1. This brief (complete)
2. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — tool list (12 LLM tools, 17 retrieval tools)
3. `platform/src/lib/config/feature_flags.ts` — PER_TOOL_PLANNER_ENABLED flag
4. `platform/src/app/api/chat/consume/route.ts` — pipeline stages + trace structure
5. `platform/src/lib/trace/types.ts` — TraceStep, TraceDataSummary (planner fields)
6. `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` — signal reference (for gold fixture authoring)

Emit session-open handshake per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`.

---

## §1 — Problem statement

The M2 quality bar (MACRO_PLAN_v2_0 criterion #7) requires that before M2 close:

1. All three provenance audits pass (Audits 1–3)
2. An eval harness is scaffolded and at least one baseline run is executed
3. The eval harness supports A/B comparison: classifier-only (planner off) vs
   per-tool planner (planner on)

No eval harness exists yet. This brief creates the full scaffold:
- 24 gold query fixtures with expected answer characteristics
- A runner script that calls the consume API and scores each fixture
- A scoring rubric (keyword/signal recall + LLM-judge for synthesis quality)
- An A/B runner that produces a comparison report
- A baseline run committed to `00_ARCHITECTURE/EVAL/`

---

## §2 — Scope

```
CREATES (new files — no pre-existing files to modify):
  platform/scripts/eval/                               (new directory)
  platform/scripts/eval/fixtures.json                 (24 gold query fixtures)
  platform/scripts/eval/runner.py                     (eval runner)
  platform/scripts/eval/scorer.py                     (scoring logic)
  platform/scripts/eval/ab_runner.py                  (A/B comparison runner)
  platform/scripts/eval/README.md                     (usage + rubric documentation)
  00_ARCHITECTURE/EVAL/                               (new directory)
  00_ARCHITECTURE/EVAL/BASELINE_RUN_W7.json           (baseline run results)

MUST NOT TOUCH:
  platform/src/**                         (no app code changes)
  025_HOLISTIC_SYNTHESIS/**               (read only)
  01_FACTS_LAYER/**                       (read only)
  00_ARCHITECTURE/CAPABILITY_MANIFEST.json  (W7-R2 scope)
  platform/scripts/integrity/**           (W7-R1 scope)
  Any existing file not listed in CREATES
```

---

## §3 — Implementation

### §3.1 — Gold query fixtures (fixtures.json)

Create 24 ground-truth query fixtures. Each fixture tests a specific pipeline
capability. Distribute across 6 query types:

**Type A — Factual chart queries (4 fixtures):**
Test L1 retrieval accuracy. Expected: specific numerical/positional facts.

Example fixture structure:
```json
{
  "fixture_id": "F001",
  "type": "factual",
  "query": "What house and sign is Mercury placed in the natal chart?",
  "expected_signals": [],
  "expected_keywords": ["10th house", "Capricorn", "Mercury"],
  "expected_tools_used": ["chart_facts_query"],
  "expected_minimum_tool_count": 1,
  "gold_answer_summary": "Mercury in 10th house Capricorn",
  "scoring_weights": {"keyword_recall": 0.7, "signal_recall": 0.0, "synthesis": 0.3}
}
```

**Type B — Signal recall queries (4 fixtures):**
Test MSR signal retrieval. Expected: specific SIG.MSR.NNN IDs in response.

Example:
```json
{
  "fixture_id": "F005",
  "type": "signal_recall",
  "query": "What are the most important signals in the MSR related to Mercury's dominance in this chart?",
  "expected_signals": ["SIG.MSR.391", "SIG.MSR.396", "SIG.MSR.413"],
  "expected_keywords": ["Mercury", "Atmakaraka", "10th"],
  "expected_tools_used": ["msr_sql", "query_msr_signals"],
  "expected_minimum_tool_count": 1,
  "gold_answer_summary": "Mercury as Atmakaraka + 10th lord creates dominant Mercury nexus",
  "scoring_weights": {"keyword_recall": 0.3, "signal_recall": 0.5, "synthesis": 0.2}
}
```

**Type C — Cross-domain synthesis queries (4 fixtures):**
Test CDLM + CGM integration. Expected: multiple domains linked in response.

**Type D — Temporal/predictive queries (4 fixtures):**
Test timeline + dasha tools. Expected: date ranges, dasha names.

**Type E — Remedial queries (4 fixtures):**
Test l4_remedial retrieval. Expected: specific prescriptions (gemstone/mantra).

**Type F — Holistic read queries (4 fixtures):**
Test whole-chart-read protocol (B.11). Expected: MSR + UCN + CGM all cited.

**Fixtures must be authored from known facts:**
- Every `expected_signals` array must contain signal IDs verified to exist in
  `l25_msr_signals` table (or MSR_v3_0.md) before writing to fixtures.json
- Every `expected_keywords` must be verifiably true from FORENSIC or MSR
- Do NOT fabricate expected values — cross-check against corpus files

Full fixture schema (for all 24):
```json
{
  "fixture_id": "F001",              // F001–F024
  "type": "factual|signal_recall|cross_domain|temporal|remedial|holistic",
  "query": "<natural language query string>",
  "expected_signals": ["SIG.MSR.NNN", ...],    // may be empty for factual
  "expected_keywords": ["keyword1", ...],       // case-insensitive match
  "expected_tools_used": ["tool_name", ...],    // at least one of these expected
  "expected_minimum_tool_count": 1,             // how many distinct tools minimum
  "gold_answer_summary": "<1-sentence ground truth>",
  "scoring_weights": {
    "keyword_recall": 0.0–1.0,    // must sum to 1.0
    "signal_recall": 0.0–1.0,
    "synthesis": 0.0–1.0
  },
  "notes": ""                      // optional authoring note
}
```

### §3.2 — Scorer (scorer.py)

Implement three scoring functions:

**keyword_recall_score(response_text: str, fixture: dict) → float:**
- For each keyword in `expected_keywords`, check case-insensitive presence in
  `response_text`
- Score = count_found / total_expected
- Return 0.0–1.0

**signal_recall_score(response_text: str, fixture: dict) → float:**
- For each signal_id in `expected_signals`, check if the string appears in
  `response_text` (exact match: `SIG.MSR.NNN` or `MSR.NNN`)
- Score = count_found / total_expected (return 1.0 if expected_signals is empty)
- Return 0.0–1.0

**synthesis_score(response_text: str, fixture: dict, model: str) → float:**
- Use a Haiku call to judge synthesis quality on a 0.0–1.0 scale
- System prompt: "You are an expert Jyotish evaluator. Score this answer from
  0.0 to 1.0 on synthesis quality given the gold answer summary. Output JSON:
  {\"score\": 0.0-1.0, \"reason\": \"<one sentence>\"}. Be strict."
- User: f"Gold: {fixture['gold_answer_summary']}\nAnswer: {response_text[:800]}"
- Parse JSON from response; on parse failure return 0.5
- Use the same Haiku model constant as per_tool_planner.ts (read from codebase)

**weighted_score(keyword: float, signal: float, synthesis: float, weights: dict) → float:**
- Return keyword * weights['keyword_recall'] + signal * weights['signal_recall']
  + synthesis * weights['synthesis']

### §3.3 — Runner (runner.py)

```
Usage: python3 platform/scripts/eval/runner.py [--planner-on|--planner-off]
                [--fixture-ids F001,F005,...] [--base-url http://localhost:3000]
                [--output path/to/results.json]
```

The runner must:

1. Load fixtures from `fixtures.json`
2. Optionally filter by `--fixture-ids`
3. For each fixture, issue a POST request to the consume API:
   ```
   POST {base_url}/api/chat/consume
   Content-Type: application/json
   {"query": fixture["query"], "chartId": "native_abhisek"}
   ```
   - Set header `X-Eval-Session: true` (for future rate-limit bypass)
   - Timeout: 60 seconds per fixture
   - On HTTP error or timeout: record `status: "error"`, score = 0.0, continue

4. From the response:
   - Extract `response_text` (synthesized answer text)
   - Extract `trace` array if present; identify:
     - `tools_used`: list of tool names from trace steps with status "success"
     - `planner_active`: from trace step with label "plan_per_tool",
       `data_summary.planner_active`
     - `tool_count`: len(tools_used)

5. Score each fixture using scorer.py functions

6. Build result record:
   ```json
   {
     "fixture_id": "F001",
     "status": "ok|error|timeout",
     "planner_active": true|false,
     "tools_used": ["chart_facts_query", ...],
     "tool_count": 3,
     "scores": {
       "keyword_recall": 0.85,
       "signal_recall": 1.0,
       "synthesis": 0.72,
       "weighted": 0.84
     },
     "response_excerpt": "<first 200 chars of response>",
     "latency_ms": 1234
   }
   ```

7. Write full results to `--output` (default: stdout JSON)

8. Print summary table to stdout:
   ```
   Fixture  Type          KW    Sig   Syn   Wtd   Status
   F001     factual       0.85  1.00  0.72  0.84  ok
   ...
   ─────────────────────────────────────────────────────
   AGGREGATE              0.xx  0.xx  0.xx  0.xx  N/24 ok
   ```

**Planner flag handling:**
- `--planner-on`: set env `MARSYS_FLAG_PER_TOOL_PLANNER_ENABLED=true` before run
- `--planner-off`: set env `MARSYS_FLAG_PER_TOOL_PLANNER_ENABLED=false`
- If the API is external (Cloud Run), the flag must be pre-set server-side;
  the runner just records what `planner_active` was in the trace
- If the API is local dev server, the runner can set the env var before calling

### §3.4 — A/B runner (ab_runner.py)

```
Usage: python3 platform/scripts/eval/ab_runner.py
             [--base-url http://localhost:3000]
             [--output 00_ARCHITECTURE/EVAL/AB_RUN_<date>.json]
```

The A/B runner:
1. Calls runner.py with `--planner-off`, captures results as `control`
2. Calls runner.py with `--planner-on`, captures results as `treatment`
3. Computes per-fixture delta (treatment - control) for each score dimension
4. Computes aggregate delta
5. Outputs a comparison JSON:
   ```json
   {
     "run_date": "2026-...",
     "fixture_count": 24,
     "control": { "aggregate": {...} },
     "treatment": { "aggregate": {...} },
     "delta": { "keyword_recall": ..., "signal_recall": ..., "synthesis": ..., "weighted": ... },
     "verdict": "PLANNER_HELPS | PLANNER_NEUTRAL | PLANNER_HURTS",
     "per_fixture": [...]
   }
   ```
6. Print a human-readable summary:
   ```
   A/B COMPARISON: Planner OFF vs ON
   Metric         Control  Treatment  Delta
   keyword_recall   0.xx     0.xx     +0.xx
   signal_recall    0.xx     0.xx     +0.xx
   synthesis        0.xx     0.xx     +0.xx
   weighted         0.xx     0.xx     +0.xx
   Verdict: <PLANNER_HELPS|NEUTRAL|HURTS>
   ```

Verdict logic:
- PLANNER_HELPS: weighted delta > +0.05
- PLANNER_NEUTRAL: abs(weighted delta) ≤ 0.05
- PLANNER_HURTS: weighted delta < -0.05

### §3.5 — Baseline run

**If the dev server can be started and the consume API is accessible:**
Run the eval harness against all 24 fixtures (planner off) to establish baseline:

```bash
cd ~/Vibe-Coding/Apps/Madhav/platform
npm run dev &
sleep 20  # wait for startup
python3 scripts/eval/runner.py --planner-off \
  --base-url http://localhost:3000 \
  --output ../00_ARCHITECTURE/EVAL/BASELINE_RUN_W7.json
kill %1
```

Save the output JSON to `00_ARCHITECTURE/EVAL/BASELINE_RUN_W7.json`.

**If the dev server cannot be started (missing env vars, DB unreachable, etc.):**
Create a stub baseline file:
```json
{
  "status": "STUB — server not available in W7-R3 session",
  "run_date": "<date>",
  "fixture_count": 24,
  "note": "Run manually: python3 platform/scripts/eval/runner.py --planner-off --base-url <url> --output 00_ARCHITECTURE/EVAL/BASELINE_RUN_W7.json",
  "aggregate": null
}
```
This is acceptable — the harness scaffold is the primary deliverable.
AC.10 is conditional: "PASS if run completed" or "STUB — manual run required".

### §3.6 — README.md

Write `platform/scripts/eval/README.md` with:
- Purpose statement (1 paragraph)
- Fixture authoring rules (how to add new fixtures)
- Runner usage (command examples)
- Scoring rubric explanation (keyword/signal/synthesis weights)
- A/B methodology description
- How to interpret results
- Link to `00_ARCHITECTURE/EVAL/` for stored run results

---

## §4 — Acceptance criteria

| # | Criterion |
|---|---|
| AC.1 | `platform/scripts/eval/fixtures.json` exists with exactly 24 fixtures |
| AC.2 | All fixture `expected_signals` IDs verified against corpus (no fabricated IDs) |
| AC.3 | All 6 fixture types present: factual, signal_recall, cross_domain, temporal, remedial, holistic |
| AC.4 | `scorer.py`: three scoring functions present; weighted_score weights sum to 1.0 per fixture |
| AC.5 | `runner.py`: --planner-on/off flags implemented; outputs structured JSON |
| AC.6 | `runner.py`: handles HTTP errors + timeouts without crashing |
| AC.7 | `ab_runner.py`: runs both branches, computes delta, emits verdict |
| AC.8 | Synthesis scorer uses Haiku model constant from codebase (no hardcoded string) |
| AC.9 | `platform/scripts/eval/README.md` created |
| AC.10 | `00_ARCHITECTURE/EVAL/BASELINE_RUN_W7.json` created (run results or stub) |
| AC.11 | If baseline run completed: aggregate weighted score recorded in BASELINE_RUN_W7.json |
| AC.12 | No changes to `platform/src/**` |
| AC.13 | SESSION_LOG appended with session entry |

---

## §5 — Halt conditions

Stop and report to native if:
- Any `expected_signals` IDs cannot be verified against corpus after 2 attempts
- The consume API returns 500 errors for more than 50% of fixtures in baseline run
  (likely a misconfigured env — report DSN/flag issue, save stub, continue to ACs)
- scorer.py Haiku calls fail with auth errors (missing API key) — fall back to
  synthesis_score returning 0.5 for all fixtures with a logged warning

---

## §6 — Closing summary template

```
=== KARN-W7-R3 CLOSE ===
Fixtures: 24 created (A:4, B:4, C:4, D:4, E:4, F:4)
Expected signal IDs verified: all (0 unverified)
Scripts created:
  platform/scripts/eval/fixtures.json
  platform/scripts/eval/runner.py
  platform/scripts/eval/scorer.py
  platform/scripts/eval/ab_runner.py
  platform/scripts/eval/README.md
  00_ARCHITECTURE/EVAL/BASELINE_RUN_W7.json  (<run|stub>)
Baseline run: <COMPLETE — aggregate weighted: 0.xx | STUB — manual run required>
A/B harness: READY (run ab_runner.py after planner is stable in production)
M2 eval gate: <CLEARED | PENDING manual baseline run>
SESSION_LOG: appended
```

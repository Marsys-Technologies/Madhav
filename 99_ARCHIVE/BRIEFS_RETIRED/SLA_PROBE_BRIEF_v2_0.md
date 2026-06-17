---
artifact: SLA_PROBE_BRIEF_v2_0.md
canonical_id: SLA_PROBE_BRIEF_PLANNER_BLIND_FIX
version: 2.0
status: READY
authored: 2026-05-17
author: Claude (Cowork session)
intended_executor: Claude Code (Antigravity IDE, --dangerously-skip-permissions)
supersedes: 00_ARCHITECTURE/briefs/SLA_PROBE_BRIEF_v1_0.md (v1.0 closed 2026-05-17 after first executor run; v2.0 adds Phase D.5 planner-only smoke + reflects the expanded planner-effectiveness footprint authored 2026-05-17 post-v1.0)
related_audit: 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md (findings F.PIPE.1 + F.SYNTH.1)
governing_change: planner-blind RCS gap + planner-effectiveness footprint closed 2026-05-17 (Cowork session)
---

# SLA Probe Brief v2.0 — Planner-Blind Fix Verification

The Cowork session that closed the planner-blind RCS gap (4 tools restored to `RETRIEVAL_CAPABILITY_SPEC`) authored five unit-test files, one live SLA probe, and one package.json script in v1.0. **v2.0 expands the scope:** the planner-effectiveness footprint for the 4 tools (PLANNER_PROMPT R-rules, golden-set entries, toolStepType mapping) was completed, and a focused planner-only smoke test was authored to prove the live planner actually SELECTS the restored tools when given queries that should trigger them. This brief asks Claude Code to run the full verification — including the new Phase D.5 — and report.

Copy everything from §A to §G below into your Antigravity session as a single prompt.

---

## §A — Executor briefing (paste this block)

You are Claude Code running in Antigravity IDE with `--dangerously-skip-permissions`. The user (Abhisek) needs you to thoroughly verify a fix that closed the planner-blind RCS gap. Two Cowork passes (2026-05-17) authored a complete fix:

**Pass 1** — RCS visibility:
- 4 RetrievalCapabilityEntry consts added to `retrieval_capability_spec.ts`
- `lel_query` added to `ALL_21_RETRIEVAL_TOOLS` in `trace/types.ts`
- 5 unit tests per tool (mocked storage)
- RCS bidirectional-coverage regression test
- Live SLA probe with WARMUP_RUNS knob

**Pass 2** — planner effectiveness:
- R28/R29/R30 added to `PLANNER_PROMPT_v2_0.md` (R27 for lel_query was already there)
- 5 new worked examples in PLANNER_PROMPT
- 12 new golden-set entries (GT.053-064) covering all 4 tools across predictive/factual classes
- `toolStepType` in `consume/route.ts` updated to map all 4 tools to `'sql'` (Postgres-backed)
- `eval:planner-blind-fix` npm script — the focused planner-only smoke test

Your job: run the full verification, gather results, ask before committing.

**Project root:** `/Users/Dev/Vibe-Coding/Apps/Madhav`
**Platform root:** `/Users/Dev/Vibe-Coding/Apps/Madhav/platform`

**Mandatory reading before you start** (per CLAUDE.md §C — applies even to verification sessions):
1. `/Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDE.md`
2. `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md` §F (findings) + §G (remediation plan)
3. This brief in full

Skip the rest of the §C mandatory list — this is a verification session, not a phase session.

---

## §B — Phase 1: TypeScript compilation gate

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npx tsc --noEmit -p . 2>&1 | tee /tmp/sla_probe_tsc.log
echo "tsc exit code: $?"
```

**Acceptance:** exit code 0, zero TS errors. If errors, STOP and report verbatim — do NOT proceed to Phase 2.

---

## §C — Phase 2: Unit tests (no DB needed)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npx vitest run \
  src/lib/router/__tests__/retrieval_capability_spec.test.ts \
  src/lib/retrieve/__tests__/lel_query.test.ts \
  src/lib/retrieve/__tests__/query_signal_state.test.ts \
  src/lib/retrieve/__tests__/query_kp_ruling_planets.test.ts \
  src/lib/retrieve/__tests__/query_varshaphala.test.ts \
  --reporter=verbose 2>&1 | tee /tmp/sla_probe_unit.log
echo "vitest exit code: ${PIPESTATUS[0]}"
```

**Acceptance:** all 26 tests pass (6 RCS regression + 5×4 tool unit tests). Exit code 0.

Failure modes to recognize: schema validate() mock issues, import path resolution, native binding errors (run `npm install` if @rolldown / @esbuild missing). If any test fails, STOP and report which test, which assertion, expected vs actual.

---

## §D — Phase 3: Live SLA probe (requires DB proxy)

### D.1 — Start Cloud SQL Auth Proxy in a SECOND terminal

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
bash platform/scripts/start_db_proxy.sh
# leave running; listens on 127.0.0.1:5433
```

Wait for `Proxy ready. Connect via: postgresql://amjis_app:*****@127.0.0.1:5433/amjis`.

**If the proxy fails to start:** `lsof -ti:5433 | xargs kill -9` then retry. Verify `.env.rag` exists at the project root with `INSTANCE_CONNECTION_NAME=madhav-astrology:asia-south1:amjis-postgres`.

### D.2 — Run the SLA probe (now with WARMUP_RUNS=1 by default)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npm run sla:probe-planner-blind 2>&1 | tee /tmp/sla_probe_single.log
echo "probe exit code: ${PIPESTATUS[0]}"
```

Note: v2.0 introduces a `WARMUP_RUNS` env var (default 1). The probe runs all 15 scenarios once silently to absorb cold pg-pool startup, then runs the measured loop. To override:
- `WARMUP_RUNS=0 npm run sla:probe-planner-blind` (matches v1.0 behavior — measures cold-start)
- `WARMUP_RUNS=2 npm run sla:probe-planner-blind` (extra warmup for noisier environments)

### D.3 — 3-run sampling for P50/P95

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
SCENARIO_COUNT=3 npm run sla:probe-planner-blind 2>&1 | tee /tmp/sla_probe_3run.log
echo "probe-3run exit code: ${PIPESTATUS[0]}"
```

### D.4 — Capture report

```bash
LATEST_REPORT=$(ls -t /Users/Dev/Vibe-Coding/Apps/Madhav/platform/scripts/eval/sla_probe_planner_blind_tools_*.json | head -1)
echo "Latest probe report: $LATEST_REPORT"
cat "$LATEST_REPORT" | python3 -m json.tool | head -120
```

**Acceptance grades:**

| Grade | Meaning | Action |
|---|---|---|
| **GREEN** | exit 0, no `budget_exceeded`, no errors | proceed to D.5 |
| **YELLOW** | exit 0 but ≥1 `budget_exceeded` after warmup | report which tool/scenario, recommend whether to widen budget |
| **RED** | exit 1 (errors) | inspect `error` fields. Common causes: missing DB rows, missing table, wrong env. |
| **PROXY DOWN** | exit 2 | verify D.1 terminal is alive |

---

## §E — Phase 4: Planner-only smoke test (NEW in v2.0)

This is the gate that proves the live LLM-first planner actually SELECTS the 4 restored tools when given queries that should trigger them. Without this, the RCS fix is theoretically sound but empirically unverified.

### E.1 — Pre-flight checks

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform

# Verify the script and golden entries exist
ls -la tests/eval/planner_blind_fix_smoke.ts
python3 -c "
import json
d = json.load(open('tests/eval/planner_golden_set.json'))
ids = {e['id'] for e in d['entries']}
expected = {'GT.053','GT.054','GT.055','GT.056','GT.057','GT.058','GT.059','GT.060','GT.061','GT.062','GT.063','GT.064'}
missing = expected - ids
print(f'Golden entries OK: {len(missing)==0}')
if missing: print(f'  Missing: {missing}')
"

# Verify .env.local has the planner LLM API key. Default is Gemini.
grep -E "^(GEMINI_API_KEY|GOOGLE_GENERATIVE_AI_API_KEY)=" .env.local 2>/dev/null | head -2
```

If the API key is absent, STOP and ask Abhisek to populate `.env.local` with `GEMINI_API_KEY=...` (or whichever provider matches `PLANNER_MODEL_ID`).

### E.2 — Run the planner-only smoke

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform

# Standard run with default model (gemini-2.5-flash — matches production
# routing planner_fast.primary; see registry.ts:1180).
#
# DO NOT override PLANNER_MODEL_ID to gemini-2.5-pro: the Gemini API now
# rejects thinkingBudget: 0 on that model, and callPipelinePlanner
# intentionally passes reasoning: 'disable' for speed (which maps to
# budget 0). Production isn't affected because planner_fast.primary is
# gemini-2.5-flash. If you NEED to test pro, override the script's adapter
# behavior — that's a separate change outside this brief.
npm run eval:planner-blind-fix 2>&1 | tee /tmp/planner_blind_smoke.log
echo "smoke exit code: ${PIPESTATUS[0]}"

# If the report is unclear, re-run with VERBOSE for full predicted tool_calls per query:
# VERBOSE=1 npm run eval:planner-blind-fix
```

### E.3 — Capture report

```bash
LATEST_SMOKE=$(ls -t /Users/Dev/Vibe-Coding/Apps/Madhav/platform/scripts/eval/planner_blind_fix_smoke_*.json | head -1)
echo "Latest smoke report: $LATEST_SMOKE"
cat "$LATEST_SMOKE" | python3 -m json.tool | head -100
```

**Pass criteria (per tool):**
- `selected_count ≥ 1`: at least one of the tool's 3 golden entries had the planner pick it
- `required_count ≥ 1`: at least one entry that REQUIRED the tool actually got it

**Overall pass:** all 4 tools at `passes_smoke_test: true`, `total_planner_errors: 0`.

**Failure modes to interpret:**

| Symptom | Likely cause | Mitigation |
|---|---|---|
| `selected 0/3` for a tool | R-rule in PLANNER_PROMPT not triggering on the test queries | Re-read R28/R29/R30 of PLANNER_PROMPT_v2_0.md. The rule may need a query-keyword hint that the test queries lack. |
| `selected 1-2/3` (partial) | Planner is inconsistent on this tool | Re-run with `VERBOSE=1` to see what the planner picked instead. Often a competing rule (e.g. R7c transit ban) is over-firing. |
| `forbidden_violations` | Planner is over-eager, adding tools the entry forbade | Investigate which tool was added. May reveal a separate over-trigger bug. |
| `planner errors > 0` | API key, network, or model availability | Check API key, retry. |

---

## §F — Phase 5 (optional, only if §C, §D, §E are GREEN): commit + push

If and ONLY if Phase 2 (unit tests) AND Phase 3 (live SLA probe) AND Phase 4 (planner smoke) are all GREEN, ask the user whether to commit. Do NOT commit autonomously.

Suggested message when asking:
> "All checks green: 26/26 unit tests pass, live SLA probe warm-path GREEN at P50=Xms/P95=Yms, and the planner-only smoke confirms all 4 restored tools are selected by the live Gemini planner with required_count ≥ 1 each. Ready to commit + push?"

If user approves:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git status
git diff --stat \
  platform/src/lib/router/retrieval_capability_spec.ts \
  platform/src/lib/trace/types.ts \
  platform/src/app/api/chat/consume/route.ts \
  platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts \
  platform/src/lib/retrieve/__tests__/lel_query.test.ts \
  platform/src/lib/retrieve/__tests__/query_signal_state.test.ts \
  platform/src/lib/retrieve/__tests__/query_kp_ruling_planets.test.ts \
  platform/src/lib/retrieve/__tests__/query_varshaphala.test.ts \
  platform/scripts/sla_probe_planner_blind_tools.ts \
  platform/tests/eval/planner_blind_fix_smoke.ts \
  platform/tests/eval/planner_golden_set.json \
  platform/package.json \
  00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md \
  00_ARCHITECTURE/briefs/SLA_PROBE_BRIEF_v1_0.md \
  00_ARCHITECTURE/briefs/SLA_PROBE_BRIEF_v2_0.md

git add \
  platform/src/lib/router/retrieval_capability_spec.ts \
  platform/src/lib/trace/types.ts \
  platform/src/app/api/chat/consume/route.ts \
  platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts \
  platform/src/lib/retrieve/__tests__/lel_query.test.ts \
  platform/src/lib/retrieve/__tests__/query_signal_state.test.ts \
  platform/src/lib/retrieve/__tests__/query_kp_ruling_planets.test.ts \
  platform/src/lib/retrieve/__tests__/query_varshaphala.test.ts \
  platform/scripts/sla_probe_planner_blind_tools.ts \
  platform/tests/eval/planner_blind_fix_smoke.ts \
  platform/tests/eval/planner_golden_set.json \
  platform/package.json \
  00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md \
  00_ARCHITECTURE/briefs/SLA_PROBE_BRIEF_v1_0.md \
  00_ARCHITECTURE/briefs/SLA_PROBE_BRIEF_v2_0.md

git commit -m "feat(rcs): wire 4 planner-blind tools end-to-end (closes F.PIPE.1, F.SYNTH.1)

Closes the planner-blind gap for lel_query, query_signal_state,
query_kp_ruling_planets, query_varshaphala. These tools have been in
RETRIEVAL_TOOLS since their M-phase commits (M3-W3-C2 / M5-E) but were
never propagated into RETRIEVAL_CAPABILITY_SPEC — clerical omission at
PR time, not a design choice. The LLM-first planner could not select
them, silently degrading predictive and temporal-precision queries.

Full planner-effectiveness footprint (mirroring other equipped tools):
- RetrievalCapabilityEntry in retrieval_capability_spec.ts
- ALL_21_RETRIEVAL_TOOLS in trace/types.ts (lel_query was missing)
- toolStepType in consume/route.ts maps all 4 to 'sql'
- PLANNER_PROMPT R28/R29/R30 (R27 for lel_query existed pre-fix)
- 5 new PLANNER_PROMPT worked examples
- 12 new planner_golden_set.json entries (GT.053-064, 3 per tool)
- 5 unit tests per tool (mocked storage) — 20 tests total
- RCS bidirectional-coverage regression gate (6 tests)
- Live SLA probe with WARMUP_RUNS knob (15 scenarios)
- Planner-only smoke test (npm run eval:planner-blind-fix)

Audit reference: 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md
Brief:           00_ARCHITECTURE/briefs/SLA_PROBE_BRIEF_v2_0.md

Verification (2026-05-17):
- tsc:           0 errors project-wide
- vitest:        26/26 PASS in <Xms>
- SLA probe:     GREEN warm-path
  · lel_query                P50=Xms P95=Yms max=Zms budget=250ms
  · query_signal_state       P50=Xms P95=Yms max=Zms budget=400ms
  · query_kp_ruling_planets  P50=Xms P95=Yms max=Zms budget=200ms
  · query_varshaphala        P50=Xms P95=Yms max=Zms budget=250ms
- Planner smoke: all 4 tools selected_count≥1 + required_count≥1
  · lel_query                selected X/3, required-hit Y/3
  · query_signal_state       selected X/3, required-hit Y/3
  · query_kp_ruling_planets  selected X/3, required-hit Y/3
  · query_varshaphala        selected X/3, required-hit Y/3

Post-deploy follow-up: re-run \`npm run answer:eval\` for end-to-end
synthesis-quality measurement. Old baseline: 4/5 PASS on 5 measured,
10/15 SKIPPED. Predictive-class queries (GQ-013/014/015) should improve
because lel_query is now reachable.
"

git push origin main

# Watch deploy:
gh run watch --workflow=deploy.yml || gh run list --workflow=deploy.yml --limit=1
```

Replace `<Xms>` placeholders in the commit message with actual numbers from /tmp/sla_probe_3run.log and /tmp/planner_blind_smoke.log before committing.

---

## §G — Phase 6 (post-deploy, optional): end-to-end answer:eval

Wait until the Cloud Run revision rolls out (`gh run watch` exits clean).

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform

# If __SESSION_COOKIE expired, mint a fresh one:
# node scripts/mint_session_cookie.mjs

npm run answer:eval 2>&1 | tee /tmp/answer_eval_post_fix.log
```

Compare against `platform/scripts/eval/results_gemini_baseline_20260511.json`:
- Old baseline: 4/5 PASS on 5 measured fixtures; 10/15 SKIPPED.
- Focus on predictive queries (GQ-013/014/015) and any interpretive ones that name a life domain (career/relationship/health). These should benefit most from lel_query being reachable.

---

## §H — Reporting back to Abhisek

After all phases complete, deliver this exact Markdown shape:

```markdown
# SLA Probe v2.0 Verification — Planner-Blind Fix

## Phase 1 — TypeScript
- Exit code: <X>
- Errors: <N>

## Phase 2 — Unit tests
- Tests run: 26
- Passed: <N>
- Failed: <list>
- Wall time: <X>s

## Phase 3 — Live SLA probe (warmup=1, 3-run sampling)
- Exit code: <X>
- Scenarios run: 15
- OK: <N>, zero_rows: <N>, budget_exceeded: <N>, error: <N>

| Tool | P50 | P95 | Max | Budget | Reachability% |
|---|---|---|---|---|---|
| lel_query | Xms | Yms | Zms | 250ms | 100% |
| query_signal_state | ... | ... | ... | 400ms | ... |
| query_kp_ruling_planets | ... | ... | ... | 200ms | ... |
| query_varshaphala | ... | ... | ... | 250ms | ... |

## Phase 4 — Planner-only smoke (NEW)
- Model used: <PLANNER_MODEL_ID>
- Total planner errors: <N>
- Overall pass: <yes/no>

| Tool | Selected | Required-hit | Verdict |
|---|---|---|---|
| lel_query | X/3 | Y/3 | ✅ PASS / ❌ FAIL |
| query_signal_state | X/3 | Y/3 | ... |
| query_kp_ruling_planets | X/3 | Y/3 | ... |
| query_varshaphala | X/3 | Y/3 | ... |

If any tool FAILED: include for that tool the 3 query strings + the predicted_tools the planner returned, so Abhisek can investigate the R-rule mismatch.

## Phase 5 — Commit + push
- Committed: <yes/no/awaiting decision>
- Cloud Run revision: <amjis-web-NNNNN-xxx>
- Deploy duration: <X minutes>

## Phase 6 — Post-deploy answer:eval (if Phase 5 happened)
- Old baseline: 4/5 PASS, 10/15 SKIPPED
- New baseline: <P/Q PASS, R/15 SKIPPED>
- Predictive category delta: <improvement or regression>

## Decisions / escalations
[any YELLOW or RED grades; any tests that needed adjustment]
```

---

## §I — Hard rules

- **Do NOT modify any Cowork-authored files.** Only run tests. Failed tests → report, don't "fix" the test.
- **Do NOT autonomously commit + push.** Phase 5 requires explicit user approval.
- **Do NOT skip Phases B/C/D/E.** Each is a hard gate. Commit only when all four are clean.
- **If the planner smoke (Phase E) fails for any tool:** that's a stronger signal than the SLA probe. RCS visibility + prompt rules may be insufficient — investigate before commit.
- **Preserve the audit trail.** Probe JSON reports go to `platform/scripts/eval/` — do not delete or .gitignore them.
- **For planner-blind smoke failures:** include the failing query strings + the planner's predicted_tools in the report so Abhisek can decide whether to refine R-rules or accept the partial coverage.

---

*End SLA_PROBE_BRIEF_v2_0.md. Successor: post-deploy answer:eval re-baseline if Phase 5 happened.*

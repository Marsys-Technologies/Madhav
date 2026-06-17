---
artifact: SLA_PROBE_BRIEF_v1_0.md
canonical_id: SLA_PROBE_BRIEF_PLANNER_BLIND_FIX
version: 1.0
status: READY
authored: 2026-05-17
author: Claude (Cowork session)
intended_executor: Claude Code (Antigravity IDE, --dangerously-skip-permissions)
related_audit: 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md (findings F.PIPE.1 + F.SYNTH.1)
governing_change: planner-blind RCS gap closed 2026-05-17 (Cowork session)
---

# SLA Probe Brief — Planner-Blind Fix Verification

The Cowork session that closed the planner-blind RCS gap (4 tools restored to `RETRIEVAL_CAPABILITY_SPEC`) authored five unit-test files, one live SLA probe, and one package.json script. This brief asks Claude Code to run the full verification on the user's Mac, capture the results, and report.

Copy everything from §A to §F below into your Antigravity session as a single prompt.

---

## §A — Executor briefing (paste this block)

You are Claude Code running in Antigravity IDE with `--dangerously-skip-permissions`. The user (Abhisek) needs you to thoroughly verify a fix that closed the planner-blind RCS gap. Five test files + one SLA probe were authored 2026-05-17. Your job is to run them, capture results, and report findings. Do NOT deploy anything — that's a separate decision for the user after seeing results.

**Project root:** `/Users/Dev/Vibe-Coding/Apps/Madhav`
**Platform root:** `/Users/Dev/Vibe-Coding/Apps/Madhav/platform`

**Artifacts already on disk** (do not re-author):

| File | Purpose |
|---|---|
| `platform/src/lib/router/retrieval_capability_spec.ts` | 4 new RCS entries (lel_query, query_signal_state, query_kp_ruling_planets, query_varshaphala) |
| `platform/src/lib/trace/types.ts` | `ALL_21_RETRIEVAL_TOOLS` updated to include `lel_query` |
| `platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts` | 6 regression tests asserting bidirectional coverage of `RETRIEVAL_TOOLS` × `RETRIEVAL_CAPABILITY_SPEC` |
| `platform/src/lib/retrieve/__tests__/lel_query.test.ts` | 5 unit tests (mocked storage) |
| `platform/src/lib/retrieve/__tests__/query_signal_state.test.ts` | 5 unit tests |
| `platform/src/lib/retrieve/__tests__/query_kp_ruling_planets.test.ts` | 5 unit tests |
| `platform/src/lib/retrieve/__tests__/query_varshaphala.test.ts` | 5 unit tests |
| `platform/scripts/sla_probe_planner_blind_tools.ts` | 15-scenario live SLA probe (requires DB proxy on :5433) |
| `platform/package.json` | `sla:probe-planner-blind` script added |

**Mandatory reading before you start** (per CLAUDE.md §C — applies even to probe sessions): read `CLAUDE.md` and `00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md` §F (findings) + §G (remediation plan) to ground your context. Skip the others — this is a verification session, not a phase session.

---

## §B — Phase 1: TypeScript compilation gate (zero-cost, run first)

**Goal:** prove no type errors were introduced.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npx tsc --noEmit -p . 2>&1 | tee /tmp/sla_probe_tsc.log
echo "tsc exit code: $?"
```

**Acceptance:** exit code 0, zero TS errors. If there are errors, STOP and report the full output — do NOT proceed to Phase 2.

---

## §C — Phase 2: Unit tests (no DB needed, ~10 seconds)

**Goal:** prove each of the 4 newly-wired tools' `retrieve()` honors its contract under mocked storage, and that the RCS bidirectional-coverage gate holds.

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

**Acceptance:** all 26 tests pass (6 RCS regression + 5×4 tool unit tests = 26). Exit code 0.

If any test fails:
1. Capture the failure output verbatim.
2. STOP. Do NOT proceed to Phase 3.
3. Report the failure to Abhisek with: which test, which assertion, what was expected vs. actual.

Common failure modes to recognize:
- **Schema validate() returning false** — the `validate` mock may need adjustment. Inspect `platform/src/lib/schemas` if so.
- **Import path resolution** — Vitest uses tsconfig `paths`. If `@/lib/...` fails to resolve, run `npm install` first.
- **Native binding errors** (`@rolldown`, `@esbuild`) — `npm install` then retry. This means the working tree's `node_modules` is stale.

---

## §D — Phase 3: Live SLA probe (requires DB proxy)

**Goal:** measure each tool's actual latency, rows returned, and SLA-budget conformance against the live DB.

### D.1 — Start the Cloud SQL Auth Proxy in a background terminal

Open a NEW terminal window (or use VS Code's split terminal) and run:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
bash platform/scripts/start_db_proxy.sh
# leave this running; the proxy listens on 127.0.0.1:5433
```

Confirm you see `Proxy ready. Connect via: postgresql://amjis_app:*****@127.0.0.1:5433/amjis`.

**If the proxy fails to start:** likely a stale process holding port 5433. Run `lsof -ti:5433 | xargs kill -9` then retry. If it still fails, check `.env.rag` exists and has `INSTANCE_CONNECTION_NAME=madhav-astrology:asia-south1:amjis-postgres`.

### D.2 — Run the SLA probe (single-shot)

In the original terminal:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npm run sla:probe-planner-blind 2>&1 | tee /tmp/sla_probe_single.log
echo "probe exit code: ${PIPESTATUS[0]}"
```

### D.3 — Run the SLA probe with 3-run sampling (for P50/P95 numbers)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
SCENARIO_COUNT=3 npm run sla:probe-planner-blind 2>&1 | tee /tmp/sla_probe_3run.log
echo "probe-3run exit code: ${PIPESTATUS[0]}"
```

### D.4 — Capture the JSON report

```bash
ls -lt /Users/Dev/Vibe-Coding/Apps/Madhav/platform/scripts/eval/sla_probe_planner_blind_tools_*.json | head -3
# Capture the path of the most recent file for the report
LATEST_REPORT=$(ls -t /Users/Dev/Vibe-Coding/Apps/Madhav/platform/scripts/eval/sla_probe_planner_blind_tools_*.json | head -1)
cat "$LATEST_REPORT" | python3 -m json.tool | head -100
```

**Acceptance grades:**

| Grade | Meaning | Action |
|---|---|---|
| **GREEN** | exit code 0, no `budget_exceeded`, no errors | Report green and stop (or proceed to §E to commit). |
| **YELLOW** | exit code 0 but ≥1 `budget_exceeded` | Report which tool/scenario, the latency overhead, recommend whether to widen the SLA budget or investigate the SQL. |
| **RED** | exit code 1 (errors) | Inspect each `error` field in the JSON. Likely causes: missing DB rows (run `compute_kp.py` / `compute_varshaphala.py` first), missing table (a migration didn't apply), wrong env var (DB_PASSWORD missing). |
| **PROXY DOWN** | exit code 2 | Tell user proxy isn't reachable. Verify Phase D.1 terminal is still alive. |

---

## §E — Phase 4 (optional, only if §C and §D are GREEN): commit + push

If and ONLY if Phase 2 (unit tests) AND Phase 3 (live SLA probe) are GREEN, ask the user whether to commit + push. Do NOT commit autonomously.

Suggested message when asking:
> "All 26 unit tests pass and the live SLA probe came back GREEN at P50=Xms / P95=Yms / 0 errors. Want me to commit and push? The commit message would be: `feat(rcs): wire 4 planner-blind tools to RETRIEVAL_CAPABILITY_SPEC (closes F.PIPE.1, F.SYNTH.1)`. Deploy will run automatically via .github/workflows/deploy.yml on push to main."

If user says yes:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git status
git diff --stat platform/src/lib/router/retrieval_capability_spec.ts \
                platform/src/lib/trace/types.ts \
                platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts \
                platform/src/lib/retrieve/__tests__/lel_query.test.ts \
                platform/src/lib/retrieve/__tests__/query_signal_state.test.ts \
                platform/src/lib/retrieve/__tests__/query_kp_ruling_planets.test.ts \
                platform/src/lib/retrieve/__tests__/query_varshaphala.test.ts \
                platform/scripts/sla_probe_planner_blind_tools.ts \
                platform/package.json

git add platform/src/lib/router/retrieval_capability_spec.ts \
        platform/src/lib/trace/types.ts \
        platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts \
        platform/src/lib/retrieve/__tests__/lel_query.test.ts \
        platform/src/lib/retrieve/__tests__/query_signal_state.test.ts \
        platform/src/lib/retrieve/__tests__/query_kp_ruling_planets.test.ts \
        platform/src/lib/retrieve/__tests__/query_varshaphala.test.ts \
        platform/scripts/sla_probe_planner_blind_tools.ts \
        platform/package.json \
        00_ARCHITECTURE/briefs/SLA_PROBE_BRIEF_v1_0.md

git commit -m "feat(rcs): wire 4 planner-blind tools to RETRIEVAL_CAPABILITY_SPEC (closes F.PIPE.1, F.SYNTH.1)

Adds lel_query, query_signal_state, query_kp_ruling_planets, query_varshaphala
to RETRIEVAL_CAPABILITY_SPEC so the LLM-first planner can select them.
These tools have been in RETRIEVAL_TOOLS since their M-phase commits
(M3-W3-C2 / M5-E) but were never propagated into the planner catalog —
clerical omission at PR time, not a design choice.

Includes:
- 4 const RetrievalCapabilityEntry declarations + array registration
- lel_query added to ALL_21_RETRIEVAL_TOOLS in trace/types.ts
- 5 unit tests per tool (mocked storage, vitest)
- RCS coverage regression test (6 cases) preventing future drift
- Live SLA probe script + npm run sla:probe-planner-blind

Audit reference: 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md
Brief: 00_ARCHITECTURE/briefs/SLA_PROBE_BRIEF_v1_0.md

Verification:
- tsc: 0 errors project-wide
- vitest: 26/26 PASS
- SLA probe: GREEN (paste actual P50/P95 here from /tmp/sla_probe_3run.log)
"

git push origin main
```

After push, watch the Cloud Run deploy:

```bash
# Wait ~3-5 minutes for the deploy
gh run watch --workflow=deploy.yml || gh run list --workflow=deploy.yml --limit=1
```

---

## §F — Phase 5 (post-deploy, optional): end-to-end answer:eval re-baseline

Once the new revision is live, the LLM-first planner reads the new RCS at every plan() call. Re-run the answer eval to see whether predictive queries improve.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
# Get a fresh session cookie first if it has expired:
# node scripts/mint_session_cookie.mjs   (per memory reference_madhav_infra_paths)
# then export the cookie value:
# export __SESSION_COOKIE='...'

npm run answer:eval 2>&1 | tee /tmp/answer_eval_post_fix.log
```

Compare against `platform/scripts/eval/results_gemini_baseline_20260511.json`:
- Old baseline: 4/5 PASS on the 5 fixtures that ran; 10/15 SKIPPED (fetch failed).
- Look for: predictive-category queries (GQ-013, GQ-014, GQ-015) — these are the ones that should benefit most from `lel_query` being in the planner's catalog.

---

## §G — Reporting back to Abhisek

After all phases complete, deliver a single Markdown report to Abhisek with this exact shape:

```markdown
# SLA Probe Verification — Planner-Blind Fix

## Phase 1 — TypeScript
- Exit code: <X>
- Errors: <N>

## Phase 2 — Unit tests
- Tests run: 26
- Passed: <N>
- Failed: <list>
- Wall time: <X>s

## Phase 3 — Live SLA probe (single shot)
- Exit code: <X>
- Scenarios run: 15
- OK: <N>, zero_rows: <N>, budget_exceeded: <N>, error: <N>

| Tool | P50 | P95 | Max | Budget | Reachability% |
|---|---|---|---|---|---|
| lel_query | Xms | Yms | Zms | 250ms | 100% |
| query_signal_state | ... | ... | ... | 400ms | ... |
| query_kp_ruling_planets | ... | ... | ... | 200ms | ... |
| query_varshaphala | ... | ... | ... | 250ms | ... |

## Phase 3 — Live SLA probe (3-run sampling)
[same table but from /tmp/sla_probe_3run.log]

## Phase 4 — Commit + push
- Committed: <yes/no/awaiting native decision>
- Cloud Run revision: <amjis-web-NNNNN-xxx>
- Deploy duration: <X minutes>

## Phase 5 — Post-deploy answer:eval (if Phase 4 happened)
- Old baseline: 4/5 PASS, 10/15 SKIPPED
- New baseline: <P/Q PASS, R/15 SKIPPED>
- Predictive category delta: <improvement or regression>

## Decisions / escalations
[any YELLOW or RED grades; any tests that needed adjustment]
```

---

## §H — Hard rules

- **Do NOT modify any of the 8 files Cowork authored.** Only run tests against them. If a test fails, report the failure — don't "fix" the test to make it pass.
- **Do NOT autonomously commit + push.** Phase 4 requires explicit user approval.
- **Do NOT skip Phase 1 or Phase 2.** Live SLA probe results are meaningless if tsc is broken or unit tests fail.
- **If the DB proxy fails or returns errors:** capture exit code 2 from the probe and report. Do not try to debug DB-side issues unilaterally — that's a separate session.
- **Preserve the audit trail.** All probe JSON reports go to `platform/scripts/eval/` and should be git-ignored only if `.gitignore` already excludes them; don't add them to .gitignore yourself.

---

*End SLA_PROBE_BRIEF_v1_0.md. Successor: the post-deploy answer:eval re-baseline, if Abhisek approves Phase 4.*

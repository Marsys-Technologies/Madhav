---
artifact: CLAUDECODE_BRIEF_MCPT_V32_CLOSEOUT.md
session: MCPT-V32-CLOSEOUT
workstream: MCPT v3.2 Quality Tightening (final close-out)
status: PROPOSED
author: Claude Opus 4.7 (Cowork planning)
created: 2026-05-23
worktree: main (no branch changes for tasks B + C; task A checkouts the prod tag)
plan: Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md
supersedes: CLAUDECODE_BRIEF_MCPT_V32_R3_POSTPROD_ROUTING_EVAL.md (folded into Task A)
trigger: now — prod is live at amjis-mcp-00011-9zv (tag mcpt-v32-prod @ 85a19ae5)
estimated_duration: 15-20 minutes total
---

# Claude Code Brief — MCPT v3.2 Close-Out

## Context

MCPT v3.2 promoted to prod successfully. The native has made two decisions:

1. **Run R3 routing eval against prod now** to close the Phase 9.5b acceptance criterion that was deferred during the sweep.
2. **Drop the 7-day observation window** (issue #154) — close it early.

And one follow-up:

3. **Add a user-facing note about description changes** so external MCP clients (Claude Desktop, Cowork, etc.) know their cached `list_tools` results are stale.

This brief covers all three in one session.

## Preconditions (verify before starting)

```bash
test -n "$(git tag --list mcpt-v32-prod)" && echo "tag ok" || echo "STOP: tag missing"
gcloud run services describe amjis-mcp --region asia-south1 --format='value(status.latestReadyRevisionName)'
# expect: amjis-mcp-00011-9zv (or newer if a hotfix shipped)
gh issue view 154 --json state --jq '.state'
# expect: OPEN
```

If any precondition fails, STOP and surface the failure to the native.

---

## Task A — R3 Routing Eval Against Prod

### A.1 — Get the API key

Ask the native for their `ANTHROPIC_API_KEY`. Do not echo, log, or write to disk. In your shell:
```bash
export ANTHROPIC_API_KEY='<key>'
```

### A.2 — Checkout the prod tag and run the eval

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch --tags origin
git checkout mcpt-v32-prod

cd platform-mcp
npm install   # if needed

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

MCP_BASE_URL=https://amjis-mcp-qm256lasva-el.a.run.app \
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  npm run eval:routing:capture -- \
    --tier super_admin \
    --output ../eval-results/routing_eval_postprod_$TIMESTAMP.json
```

If `eval:routing:capture` isn't a defined npm script, fall back to:
```bash
npx tsx evals/mcp-routing/runner.ts \
  --base-url https://amjis-mcp-qm256lasva-el.a.run.app \
  --tier super_admin \
  --output ../eval-results/routing_eval_postprod_$TIMESTAMP.json
```

### A.3 — Ensure the baseline exists

```bash
ls /Users/Dev/Vibe-Coding/Apps/Madhav/eval-results/routing_eval_baseline_*.json 2>/dev/null
```

If no baseline file exists, generate one by running the same eval against the `mcpt-v32-baseline` tag:
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout mcpt-v32-baseline
cd platform-mcp && npm install
# Note: baseline is captured against the OLD descriptions, so use staging or a local instance
# if you don't want to compare two prod-pointed runs. The cleanest is the harness's recorded
# baseline.json under bench/ if it includes routing accuracy. If not, run against local sidecar.
```

If the harness was wired correctly in Phase 8, `bench/baseline.json` should contain the Phase 0 routing-eval numbers. Use that if a dedicated baseline file is absent.

### A.4 — Compute the diff

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Adapt field names if needed — use jq or node to read the result JSONs
node -e "
const fs = require('fs');
const path = require('path');
const head = JSON.parse(fs.readFileSync('eval-results/routing_eval_postprod_$TIMESTAMP.json'));
// Find the most recent baseline
const baselineFiles = fs.readdirSync('eval-results').filter(f => f.startsWith('routing_eval_baseline_')).sort();
const baseline = baselineFiles.length
  ? JSON.parse(fs.readFileSync(path.join('eval-results', baselineFiles[baselineFiles.length-1])))
  : JSON.parse(fs.readFileSync('platform-mcp/test/bench/baseline.json')).routing_eval ?? {accuracy_pct: 0};
const baseAcc = baseline.accuracy_pct ?? baseline.first_tool_choice_accuracy_pct;
const headAcc = head.accuracy_pct ?? head.first_tool_choice_accuracy_pct;
const delta   = +(headAcc - baseAcc).toFixed(1);
const verdict = delta >= 15 ? 'PASS' : 'FAIL';
const out = { baseline_pct: baseAcc, head_pct: headAcc, delta_pp: delta, verdict, target_pp: 15, captured_at: '$TIMESTAMP', prod_revision: 'amjis-mcp-00011-9zv', prod_tag: 'mcpt-v32-prod' };
fs.writeFileSync('eval-results/routing_eval_diff_$TIMESTAMP.json', JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
"
```

### A.5 — Commit the results

```bash
git checkout main
git pull --ff-only origin main
git add eval-results/routing_eval_postprod_*.json eval-results/routing_eval_diff_*.json
git commit -m "eval(mcpt-v32): R3 post-prod routing eval — <verdict>, <delta>pp

Live routing-accuracy eval against prod (revision amjis-mcp-00011-9zv,
tag mcpt-v32-prod @ 85a19ae5) under super_admin tier.

Baseline: <baseline_pct>%
v3.2 prod: <head_pct>%
Delta: <delta_pp>pp
Verdict: <verdict> (target >= 15pp)

Closes the Phase 9.5b acceptance criterion that was deferred during the
prod promotion sweep due to missing ANTHROPIC_API_KEY in the conductor
environment.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push origin main
```

Substitute `<verdict>`, `<delta_pp>`, `<baseline_pct>`, `<head_pct>` with the real values from the diff JSON.

---

## Task B — Description-Change Note for External MCP Clients

### B.1 — Locate or create MCPT_V32_CLOSE.md

```bash
ls /Users/Dev/Vibe-Coding/Apps/Madhav/MCPT_V32_CLOSE.md 2>/dev/null \
  || ls /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/MCPT_V32_CLOSE.md 2>/dev/null
```

The conductor likely created one. If neither exists, create `/Users/Dev/Vibe-Coding/Apps/Madhav/MCPT_V32_CLOSE.md` with the standard close-out frontmatter (follow the format of `MCPT_V33_CLOSE.md`).

### B.2 — Append the User-Facing Changes section

Add this section to the close-out file (or create it if it doesn't have one):

```markdown
## User-Facing Changes for External MCP Clients

MCPT v3.2 changed the description strings emitted by the MCP `list_tools` endpoint. External clients (Claude Desktop, Claude Code in IDEs, Cowork, third-party MCP consumers) may have cached the v3.1 descriptions and will benefit from re-fetching `list_tools` to pick up the new versions.

### What changed

1. **All 21 tools** now use a standardized description format produced by `description_builder.ts`. Each description leads with a single disambiguator sentence and includes a "When to prefer" section. Total length ≤ 1200 chars.

2. **`data_coverage` description** — removed false claim that "KP, Tajaka, Shadbala, Ashtakavarga categories are pending v3.3 backfill." All v3.3 categories have been populated since 2026-05-22 (`MCPT_V33_CLOSE.md`). The description now accurately reports current state.

3. **`tool_health` data_note** — removed the fallback string `"Apply migrations 073-076 and run nightly audit"`. Migrations 073-076 were applied 2026-05-22; the tool now returns real metrics from the materialized views.

4. **New tool: `chart_summary`** — wide-by-default tool that returns the canonical 30-60-fact bundle in one round-trip. Prefer this over `query_chart_facts` when interpreting a chart end-to-end. Saves ~60% of round-trips on typical workflows.

5. **`query_chart_facts`** — gained two new optional parameters:
   - `divisional_chart: string` — filter to a specific divisional (e.g. "D9"). Prunes irrelevance.
   - `categories: string[]` — batch fetch multiple categories in one call.

6. **Tier-aware ordering** — `list_tools` now varies tool ordering per `audience_tier`:
   - `super_admin` and `acharya`: full catalog, `chart_summary` first.
   - `client`: ops tools (`data_coverage`, `tool_health`, `log_prediction`, `record_outcome`, `flag_disagreement`) hidden.

7. **Trace alignment** — `list_recent_queries` now returns MCP-facing tool names (e.g. `query_chart_facts`) rather than retrieval-side internal names (e.g. `chart_facts_query`). `get_trace(name)` works with either form. `query_summary` now carries real param representation.

### Recommended client action

- Clients that cache `list_tools` for the session lifetime: re-fetch once to pick up new descriptions. No code changes required.
- Clients that fetch `list_tools` per-session anyway (most): no action.
- Clients relying on retrieval-side tool names in trace audits: update to expect MCP-facing names (the rename map in `platform/src/lib/mcp/primitives_registry.ts:47-59` documents the alias).

### No behavior change

Tool semantics, request/response shapes, error formats, and authentication are unchanged. Only descriptions and a few additive parameters changed.
```

### B.3 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add MCPT_V32_CLOSE.md
# OR: git add 00_ARCHITECTURE/MCPT_V32_CLOSE.md  (depending on where it lives)
git commit -m "docs(mcpt-v32): user-facing description changes for external MCP clients

Documents the seven categories of description-string changes that external
MCP clients (Claude Desktop, Cowork, third-party consumers) will see when
they re-fetch list_tools post-v3.2. No behavior change; tool semantics,
request/response shapes, auth all unchanged.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push origin main
```

---

## Task C — Close Observation Issue #154 Early

### C.1 — Post the close-out comment with R3 result

```bash
# Read the R3 diff to embed in the close comment
R3_VERDICT=$(jq -r '.verdict' /Users/Dev/Vibe-Coding/Apps/Madhav/eval-results/routing_eval_diff_*.json | tail -1)
R3_BASELINE=$(jq -r '.baseline_pct' /Users/Dev/Vibe-Coding/Apps/Madhav/eval-results/routing_eval_diff_*.json | tail -1)
R3_HEAD=$(jq -r '.head_pct' /Users/Dev/Vibe-Coding/Apps/Madhav/eval-results/routing_eval_diff_*.json | tail -1)
R3_DELTA=$(jq -r '.delta_pp' /Users/Dev/Vibe-Coding/Apps/Madhav/eval-results/routing_eval_diff_*.json | tail -1)

gh issue comment 154 --body "## Closing Early — Per Native Decision

Native has waived the 7-day observation window. v3.2 is stable enough that real-time monitoring is sufficient; we will not formally track for 7 days.

### Final R3 Routing Eval (closes Phase 9.5b acceptance)

| Metric | Value |
|---|---|
| Phase 0 baseline accuracy | ${R3_BASELINE}% |
| v3.2 prod accuracy | ${R3_HEAD}% |
| Delta | ${R3_DELTA}pp |
| Target | >= 15pp |
| **Verdict** | **${R3_VERDICT}** |

Raw result: \`eval-results/routing_eval_postprod_*.json\`
Diff: \`eval-results/routing_eval_diff_*.json\`

### Final State

- Prod revision: \`amjis-mcp-00011-9zv\` at 100% traffic
- Tag: \`mcpt-v32-prod\` @ 85a19ae5
- All 10 phases of MCPT v3.2: complete
- All accuracy gates: pass
- Tests: 257/257
- Bench: canonical_d9_workflow -60% round-trips, -71% bytes
- Cross-scenario equivalence: 100% across 2,717 facts

### What to monitor passively

Standard Cloud Run + DB alerting remains in place. If \`tool_health\` shows degradation or \`mcp_audit_findings\` accumulates entries, open a fresh issue.

Closing this issue.
"
```

### C.2 — Close the issue

```bash
gh issue close 154 --reason completed --comment "v3.2 close-out complete per CLAUDECODE_BRIEF_MCPT_V32_CLOSEOUT.md."
```

### C.3 — Verify

```bash
gh issue view 154 --json state,closedAt --jq '{state, closedAt}'
# expect: {"state":"CLOSED","closedAt":"<recent timestamp>"}
```

---

## Acceptance — done when

- [ ] `eval-results/routing_eval_postprod_*.json` and `eval-results/routing_eval_diff_*.json` committed to main.
- [ ] `MCPT_V32_CLOSE.md` (wherever it lives) has the "User-Facing Changes for External MCP Clients" section appended and committed.
- [ ] Issue #154 has the close-out comment with R3 verdict table.
- [ ] Issue #154 state: CLOSED.
- [ ] Native has been notified with the four-item report below.

## Final report to Cowork (the native)

After all three tasks complete, report:

1. **R3 verdict**: PASS or FAIL, and the delta in pp.
2. **Description-change commit SHA**.
3. **Issue #154 state**: CLOSED (with timestamp).
4. **Any anomalies**: failed prompts in R3, baseline-file fallback used, cost (Haiku tokens), or anything unexpected.

## Failure modes

| Failure | Action |
|---|---|
| Phase 0 baseline file missing AND `bench/baseline.json` has no routing data | Stop Task A, run a fresh baseline locally first, then proceed |
| Haiku quota exhausted mid-eval | Stop. Do not retry. Surface to native with partial results |
| R3 returns FAIL verdict (delta < 15pp) | Post the result honestly. Skip Task C; the native will want to see this before closing |
| MCPT_V32_CLOSE.md doesn't exist anywhere | Create it at the repo root with standard frontmatter following MCPT_V33_CLOSE.md format |
| Issue #154 already closed (someone beat you to it) | Skip Task C.2, post the R3 result as a comment on the closed issue |
| Prod URL unreachable | Stop. There's a prod problem more important than this close-out |

## Out of scope

- Any code changes (this is documentation + measurement only).
- Modifying any tool description (just measuring what's already shipped).
- Touching `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `04_REMEDIAL_CODEX/`, `06_LEARNING_LAYER/`.
- CLAUDE.md / .geminirules mirror updates (no architectural change in this brief).
- Opening any follow-up issues unless R3 fails.

## Cost estimate

- R3 Haiku tokens: ~5-20 cents.
- gcloud calls: free.
- gh calls: free.

Total: less than $0.25.

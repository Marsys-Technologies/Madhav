# WS-0C-2 — Final Residual Purge (21 out-of-scope tables) — CC Prompt

> **Paste into Claude Code in Antigravity AFTER PR #207 merges to main.**
> Branch: cut `feature/ws0c-2-final-residuals` from the post-merge `main`.
> Tag of predecessor: `legacy-residual-purge-complete` (set after #207 merge).
> Repo: `/Users/Dev/Vibe-Coding/Apps/Madhav`

---

You are Claude Code in Google Antigravity IDE. WS-0C closed (PR #207 merged + tagged). The PR review surfaced 39 residual SQL citations across 21 dropped tables that weren't in the original LEGACY_TABLES alternation — out-of-scope hits documented in PR #207. WS-0C-2 closes them in **one commit on `feature/ws0c-2-final-residuals`**, branched from the post-merge main.

## Step 0 — Branch + proxy + baseline

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git pull origin main
git tag -l 'legacy-residual-purge-complete'   # confirm present
git checkout -b feature/ws0c-2-final-residuals legacy-residual-purge-complete

# Proxy
bash platform/scripts/start_db_proxy.sh &
PROXY_PID=$!
sleep 3
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }
psql_prod -c "SELECT 1;" >/dev/null && echo "Proxy up" || exit 1

# Baseline typecheck
cd platform && npm run typecheck 2>&1 | tee /tmp/ws0c2_baseline_typecheck.txt && cd ..
```

## Step 1 — Discover the residual table set dynamically

Don't rely on a hand-list. Re-extract the 21 tables from the actual code:

```bash
# Define the KNOWN-LIVE / KEPT table allowlist (Brahma prefix + shell)
LIVE_REGEX='^(brahmagyan_|ganita_|bodha_|kala_|phala_|mimamsa_)'

KEPT_TABLES='conversations|conversation_messages|conversation_message_embeddings|conversation_branches|conversation_shares|conversation_folders|conversation_folder_members|pending_streams|profiles|access_requests|charts|chart_grants|projects|project_files|project_conversations|personas|life_events|life_events_staging|audit_log|audit_events|query_trace_steps|llm_call_log|tool_execution_log|query_plan_log|context_assembly_item_log|synthesis_quality_scorecard|plan_alternatives_log|llm_pricing_versions|llm_usage_events|llm_provider_cost_reports|llm_cost_reconciliation|llm_budget_rules|llm_stack_config|performance_queries|eval_runs|performance_judge_verdict|mcp_api_keys|mcp_predictions|mcp_prediction_outcomes|mcp_disagreements|mcp_alerts_config|tool_registry|capability_tool_registry|capability_asset_tool_bindings|runtime_config|event_chart_state_index|pyramid_layers'

# Pull every table cited in SQL contexts; strip the LIVE + KEPT set.
# What's left is the WS-0C-2 working set.
grep -rEhn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+([a-z_][a-z0-9_]*)\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null \
  | grep -oE "\b(FROM|INTO|UPDATE|DELETE FROM|JOIN)\s+([a-z_][a-z0-9_]*)\b" \
  | awk '{print $NF}' | sort | uniq -c | sort -rn \
  | awk -v live="$LIVE_REGEX" -v kept="^($KEPT_TABLES)$" '$2 !~ live && $2 !~ kept' \
  | tee /tmp/ws0c2_residual_tables.txt

cat /tmp/ws0c2_residual_tables.txt
TABLE_COUNT=$(wc -l < /tmp/ws0c2_residual_tables.txt)
echo "Residual table count: $TABLE_COUNT"
# Expected: ~21 (the PR #207 comment recorded 21)
```

Build the alternation from the output:
```bash
export SUBF_TABLES=$(awk '{print $2}' /tmp/ws0c2_residual_tables.txt | paste -sd'|')
echo "SUBF_TABLES: $SUBF_TABLES"
```

**Sanity halt:** if `TABLE_COUNT` is materially different from 21 (e.g., >35), something changed since PR #207's analysis — halt; re-grep, compare, report to native.

**DB-existence verification** (per the reverse-citation gate rule):
```bash
psql_prod -c "
SELECT table_name,
       CASE WHEN EXISTS (
         SELECT 1 FROM information_schema.tables
         WHERE table_schema='public' AND table_name = t.table_name
       ) THEN 'EXISTS' ELSE 'DROPPED' END AS status
FROM (VALUES $(awk '{printf "(%c%s%c),", 39, $2, 39}' /tmp/ws0c2_residual_tables.txt | sed 's/,$//'))
AS t(table_name)
ORDER BY status DESC, table_name;
"
```

All 21 should return DROPPED. **If any return EXISTS**, that table was recreated by runtime-guardian (like `pyramid_layers`) — remove it from `SUBF_TABLES`, add to the KEPT allowlist for this run, log the kept set, and continue.

## Step 2 — Per-file enumeration + reverse-citation gate

```bash
# Grep just the WS-0C-2 working set in SQL-context
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+(${SUBF_TABLES})\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null \
  | tee /tmp/ws0c2_grep.txt

# Group by file
awk -F: '{print $1}' /tmp/ws0c2_grep.txt | sort | uniq -c | sort -rn \
  | tee /tmp/ws0c2_files.txt
cat /tmp/ws0c2_files.txt
TOTAL_HITS=$(wc -l < /tmp/ws0c2_grep.txt)
echo "Total hits to clear: $TOTAL_HITS"  # expected ~39
```

For each file in the enumeration, classify per the WS-0C disposition rules:

| State | Disposition |
|---|---|
| No outside importer; file is sole-purpose legacy | DELETE_WHOLESALE |
| Only importers are other already-dead files | DELETE_WITH_CONSUMERS |
| Reachable from a Brahma-active route, table has a Brahma equivalent | REPOINT |
| Reachable from a Brahma-active route, table has NO Brahma equivalent | HALT — report to native |
| Reachable from a legacy route also being deleted | DELETE_WITH_ROUTE |

**Brahma equivalents for the known residual tables** (refine with the actual list from Step 1):
- `classical_chunks`, `classical_attributions`, `classical_texts` → no live equivalent; the L0 `brahmagyan.texts` asset isn't queried by `platform/src` (sidecar-only). **DELETE** unless a route surprises us.
- `engine_versions` → superseded by Brahma's `build_id` discipline. **DELETE.**
- `gate_change_log` → governance audit table; superseded by current gate verdicts written to Brahma build state. **DELETE.**
- `message_feedback` → Chat V2 (R7+) doesn't use it; replaced by `conversation_messages.feedback` jsonb or similar. **DELETE.**
- For any other table the discovery surfaces: same audit-first pattern — REPOINT if a Brahma equivalent exists and the consumer is live; DELETE otherwise; HALT if unclear.

Write `/tmp/ws0c2_disposition.md` capturing the call per file.

## Step 3 — Execute

```bash
# Per-file rm or surgical Edit per disposition.

# After each delete batch:
cd platform && npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head && cd ..

# Final residual check — must be empty
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+(${SUBF_TABLES})\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null
# Expected: zero

# Also re-run the full LEGACY_TABLES + SUBF grep to confirm no regression
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+([a-z_][a-z0-9_]*)\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null \
  | grep -oE "\b(FROM|INTO|UPDATE|DELETE FROM|JOIN)\s+([a-z_][a-z0-9_]*)\b" \
  | awk '{print $NF}' | sort -u \
  | awk -v live="^(brahmagyan_|ganita_|bodha_|kala_|phala_|mimamsa_)" -v kept="^($KEPT_TABLES)$" \
    '$1 !~ live && $1 !~ kept' \
  | tee /tmp/ws0c2_final_residuals.txt
# Expected: empty file
```

## Step 4 — Commit

```bash
git add -A
git commit -m "chore(ws0c-2): close 21-table residual citations (final cleanup)

PR #207 final-grep surfaced 39 SQL citations across 21 dropped tables
outside the original LEGACY_TABLES alternation. WS-0C-2 closes them
per the same audit-first / reverse-citation-gate pattern as WS-0C.

Dispositions: <K wholesale / L surgical / M repoint / N halt>

Notable clusters:
- classical_chunks/_attributions/_texts → deleted (L0 brahmagyan.texts is sidecar-only)
- engine_versions → deleted (superseded by Brahma build_id)
- gate_change_log → deleted (superseded by Brahma gate verdicts)
- message_feedback → deleted (Chat V2 surface uses conversation_messages)
- [list any HALTs]

After this commit, the platform/src legacy-citation surface is empty
modulo documented false-positive substring matches.

Refs WS-0C-2, predecessor tag legacy-residual-purge-complete"
```

## Step 5 — Push + open PR

```bash
git push origin feature/ws0c-2-final-residuals

gh pr create --base main --head feature/ws0c-2-final-residuals \
  --title "WS-0C-2: Final 21-table residual purge" \
  --body "Closes the 39-hit residual from PR #207's final analysis. One commit, audit-first.

## Disposition summary
- K wholesale / L surgical / M repoint / N halt

## AC scorecard
- AC-1 SQL-context legacy grep: zero hits across platform/src
- AC-2 typecheck NEW errors: 0
- AC-4 pytest: green
- AC-7 reverse-citation gates: passed per file

## Closes
Cleanup arc — after this PR + tag \`legacy-cleanup-arc-complete\`, the three waves (WS-1 portal, WS-2 depth, WS-3 rules) open in parallel."

# STOP — do NOT merge. PR-to-main is human-gated.

kill $PROXY_PID 2>/dev/null
```

## Hard stops

- Step 1 residual count is materially different from 21 (e.g., >35) — halt.
- Step 1 DB-existence shows any of the 21 tables actually EXISTS in prod (runtime-guardian recreated something silently) — halt; remove that table from `SUBF_TABLES` and report to native.
- Per-file audit finds a UNCLASSIFIED or no-Brahma-equivalent live route — halt that file; document; continue with the rest.
- Step 3 residual check is non-empty after the deletes — halt; do not commit.
- More than 3 attempts on any single fix.

Begin with Step 0. Report at the commit + PR URL.

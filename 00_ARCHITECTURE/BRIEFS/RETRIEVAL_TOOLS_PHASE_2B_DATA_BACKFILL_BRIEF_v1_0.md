---
artifact: RETRIEVAL_TOOLS_PHASE_2B_DATA_BACKFILL_BRIEF_v1_0.md
canonical_id: PHASE_2B_DATA_BACKFILL
version: 1.0
status: READY
authored: 2026-05-17
author: Claude (Cowork session — analysis stream, worktree /Users/Dev/Vibe-Coding/Apps/Madhav-analysis)
intended_executor: Claude Code (Antigravity IDE, --dangerously-skip-permissions)
parent_campaign: 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md
prerequisite: Phase 2A committed (de1731e on analysis branch)
audit_findings_closed: F.M8.6 (classical attribution coverage 76/573 → ≥300/573), signal_states empty-table concern
---

# Phase 2B — Classical Attribution Expansion + signal_states Activation

This brief covers the data-only sub-phase. No new code architecture; the existing retrieval tools `classical_attribution_lookup` (M8-G) and `query_signal_state` (Phase 1) are already wired and tested. They return sparse or empty results because the underlying data hasn't been backfilled. This brief runs the backfill scripts.

**Two independent data backfills, both required for the consolidated eval to show meaningful improvement on classical-grounding queries and current-state predictive queries:**

| Backfill | Script | Target table | Current state | Target state |
|---|---|---|---|---|
| Classical attribution expansion | `platform/scripts/run_attribution_pass.py` (M8-E) | `classical_attributions` | 420 rows, 76/573 signals attributed (13.3%) | ≥1500 rows, ≥300/573 signals (≥52%) |
| signal_states activation | `platform/scripts/temporal/signal_activator.py` (M3-B) | `signal_states` | likely empty for 2024+ dates | ≥1 row per signal per day across 2024-2028 |

This is the most expensive sub-phase wall-clock-wise (~4-6 hours total), but the lightest in code complexity. Most of the work is "let the script run + verify" plus a small registry doc commit for the classical expansion.

---

## §A — Executor briefing (paste this block)

You are Claude Code in Antigravity IDE with `--dangerously-skip-permissions`. This session belongs to the analysis stream. You operate in `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis` on branch `analysis/backend-data-pipeline-perf-audit`. The Chat V2 stream lives in `/Users/Dev/Vibe-Coding/Apps/Madhav` — DO NOT cd there.

**Prerequisite check (HARD STOP if not met):**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
git status
git branch --show-current
# Expected: analysis/backend-data-pipeline-perf-audit, clean working tree.

git log --oneline | head -5
# Expected: de1731e (Phase 2A) visible.

git log --oneline | grep -iE "Phase 2A|wire M9 tools" | head -2
# Expected: at least one match — Phase 2A is on the branch.
```

Acceptance: clean working tree, Phase 2A visible. If not, STOP.

**Pre-flight: environment + scripts present**

```bash
# .env.rag symlink in place (created during Phase 2A §F.0)
ls -la .env.rag
# Expected: symlink -> /Users/Dev/Vibe-Coding/Apps/Madhav/.env.rag

# DB proxy not yet running — will start later
lsof -ti:5433 2>&1 | head -3

# gcloud auth
gcloud auth list 2>&1 | head -3
# Expected: at least one active account with write access to madhav-astrology / GCS

# Vertex / API keys
grep -E "^(VERTEX|GOOGLE_APPLICATION_CREDENTIALS|GOOGLE_API_KEY)" .env.rag 2>/dev/null | head -3

# Scripts exist
ls -la platform/scripts/run_attribution_pass.py 2>&1 | head -2
ls -la platform/scripts/build_registry_from_db.py 2>&1 | head -2
ls -la platform/scripts/temporal/signal_activator.py 2>&1 | head -2

# Read script headers to understand current invocation contract
head -30 platform/scripts/run_attribution_pass.py
head -30 platform/scripts/temporal/signal_activator.py
```

If any script is missing or has a different name → STOP and report. The scripts were authored at M8-E (attribution) and M3-B (signal_activator).

**Mandatory reading:**
1. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/CLAUDE.md`
2. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md` §C
3. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2B_DATA_BACKFILL_BRIEF_v1_0.md` (this file)
4. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md` (current state context)
5. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` (signal universe — 573 signals to attribute against)

Then execute §B through §H below in order.

---

## §B — Phase 1: Start the Cloud SQL Auth Proxy

Open a SECOND terminal:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
bash platform/scripts/start_db_proxy.sh
# Leave running. Listens on 127.0.0.1:5433.
```

Confirm `Proxy ready. Connect via: postgresql://amjis_app:*****@127.0.0.1:5433/amjis`. If the proxy fails, `lsof -ti:5433 | xargs kill -9` then retry.

---

## §C — Phase 2: Classical attribution expansion

### C.1 — Baseline snapshot

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis

PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT
      (SELECT COUNT(*) FROM classical_attributions) AS rows_baseline,
      (SELECT COUNT(DISTINCT msr_signal_id) FROM classical_attributions) AS signals_attributed_baseline,
      (SELECT COUNT(*) FROM msr_signals) AS signals_total;
  "
```

Expected: 420 rows, 76 attributed signals out of 573 total. Save this output for the report.

### C.2 — Read the attribution script to understand its current invocation

```bash
cat platform/scripts/run_attribution_pass.py | head -80
```

Look for:
- How signal IDs are iterated (does it read MSR JSON, query the DB, or hard-code a range?)
- Parallelism flag (`--workers N` or env var)
- Filter args (does it skip already-attributed signals or re-attribute?)
- DB write mode (insert vs upsert)

If the script hard-codes M8-E's 510-signal range or has a baked-in iteration over MSR v3, it needs a small edit to iterate against MSR v5.0's 573-signal pool. Document any required edit before running.

### C.3 — Run the attribution pass

Invocation depends on what §C.2 revealed. The most likely shape:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

# 4 parallel workers — match M8-E's throughput pattern
# (per CURRENT_STATE v5.8: M8-E used 4 parallel workers + Vertex 768-dim + Gemini 2.5 flash judge)
python3 scripts/run_attribution_pass.py \
  --workers 4 \
  --skip-already-attributed \
  2>&1 | tee /tmp/phase2b_attribution.log

echo "attribution_pass exit: $?"
```

If the script's flag set differs, adapt. Possible variants:
- `python3 scripts/run_attribution_pass.py --signals-from msr_v5 --workers 4`
- `WORKERS=4 ATTRIBUTION_MODE=expand python3 scripts/run_attribution_pass.py`
- `python3 scripts/run_attribution_pass.py 2>&1 | tee …` (no flags; reads config internally)

Expected wall clock: ~4 hours for ~500 new signal attributions with 4 parallel Vertex workers. Periodic progress should print to the tee'd log.

**If the attribution pass crashes** mid-run, capture the failure mode and DB state at crash. Common modes:
- Vertex rate limit (retry with reduced workers)
- Gemini judge timeout on a specific text/signal combo (script should checkpoint; resume from last completed signal)
- DB connection pool exhaustion (proxy must stay running throughout)

Resume if possible; STOP and report if not.

### C.4 — Post-run verification

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis

PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT
      (SELECT COUNT(*) FROM classical_attributions) AS rows_now,
      (SELECT COUNT(DISTINCT msr_signal_id) FROM classical_attributions) AS signals_attributed_now,
      (SELECT COUNT(*) FROM msr_signals) AS signals_total;
  "

PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT attribution_type, COUNT(*) FROM classical_attributions GROUP BY attribution_type ORDER BY 2 DESC;
  "
```

**Acceptance gates:**
- `rows_now` ≥ 1500 (was 420)
- `signals_attributed_now` ≥ 300 (was 76)
- No major skew in attribution_type distribution (M8-E had confirms 21 / contradicts 8 / partial 64 / extends 10 / silent 317; expansion should grow all categories proportionally with silent still dominant)

If gates not met, capture deltas and STOP for native decision.

### C.5 — Rebuild the registry doc

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

python3 scripts/build_registry_from_db.py \
  --output-md ../08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md \
  --output-json ../08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json \
  2>&1 | tee /tmp/phase2b_registry_build.log

echo "registry_build exit: $?"
```

(Adapt to actual flag names from the script's header.)

**Verify the regenerated registry has correct counts:**

```bash
head -20 ../08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md
# Frontmatter should show total_attributions ≥ 1500, signals_covered ≥ 300
```

### C.6 — Upload updated registries to GCS

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis

gsutil cp 08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md \
          gs://madhav-marsys-sources/L8/registries/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md
gsutil cp 08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json \
          gs://madhav-marsys-sources/L8/registries/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json

# Verify upload
gsutil ls -l gs://madhav-marsys-sources/L8/registries/
```

---

## §D — Phase 3: signal_states activation

### D.1 — Baseline snapshot

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis

PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT
      COUNT(*) AS rows_total,
      COUNT(DISTINCT signal_id) AS signals_distinct,
      MIN(query_date) AS earliest,
      MAX(query_date) AS latest
    FROM signal_states
    WHERE chart_id = 'abhisek_mohanty_primary';
  "
```

Save this baseline. Likely shows very few rows (signal_activator probably hasn't been run for the 2024-2028 window).

### D.2 — Read signal_activator.py header to understand current invocation

```bash
head -50 platform/scripts/temporal/signal_activator.py
```

Look for the date-range argument convention. Most likely:
- `--chart-id abhisek_mohanty_primary --start-date 2024-01-01 --end-date 2028-12-31`
- Or env vars: `CHART_ID=… START_DATE=… END_DATE=…`

### D.3 — Run signal_activator over the target window

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

python3 scripts/temporal/signal_activator.py \
  --chart-id abhisek_mohanty_primary \
  --start-date 2024-01-01 \
  --end-date 2028-12-31 \
  --dasha-system vimshottari \
  2>&1 | tee /tmp/phase2b_signal_activator.log

echo "signal_activator exit: $?"
```

Adapt flags to actual script. Expected wall clock: depends on how the script iterates (per signal × per day vs. batched). Could be 30 minutes to 2 hours.

**Notes:**
- The script likely populates rows for ALL 573 MSR signals across each day in the window
- Total rows = 573 signals × 1827 days (2024-01-01 → 2028-12-31) = ~1M rows IF the script writes daily snapshots
- If the script writes only state-change events, the row count will be much smaller (a few hundred to low thousands)
- Either pattern is acceptable; report what you observe

### D.4 — Post-run verification

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis

PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT
      COUNT(*) AS rows_now,
      COUNT(DISTINCT signal_id) AS signals_distinct,
      MIN(query_date) AS earliest,
      MAX(query_date) AS latest
    FROM signal_states
    WHERE chart_id = 'abhisek_mohanty_primary';
  "

PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT state, COUNT(*) FROM signal_states
    WHERE chart_id = 'abhisek_mohanty_primary'
    GROUP BY state ORDER BY 2 DESC;
  "

# Spot-check: how many signals are 'lit' on today's date?
PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT COUNT(*) FROM signal_states
    WHERE chart_id = 'abhisek_mohanty_primary'
      AND query_date = CURRENT_DATE
      AND state = 'lit';
  "
```

**Acceptance gates:**
- `rows_now` > 0
- `signals_distinct` ≥ 100 (some meaningful number of MSR signals activated)
- `earliest` ≤ 2024-01-01 and `latest` ≥ 2026-05-17 (covers at least the present moment)
- "lit on today" count > 0 (sanity: the activator computed today's state)

---

## §E — Phase 4: re-run SLA probe to confirm tools now return non-empty results

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

SCENARIO_COUNT=3 WARMUP_RUNS=1 npm run sla:probe-planner-blind 2>&1 | tee /tmp/phase2b_sla.log
```

**Acceptance for §E:** Two specific scenarios should now return non-zero rows (vs. empty in earlier Phase 1 / 2A probes):

- `query_signal_state · today only` — should return ≥ 1 row (was 0)
- `query_signal_state · current lit/ripening` — should return ≥ 1 row (was 0)
- `query_signal_state · window scan 2026` — should return many rows (was 0)
- `classical_attribution_lookup` scenarios should return ≥ 1 row for signals that weren't attributed before — pick one of the newly-attributed signal IDs from §C.4's distribution to add as a probe scenario if needed, or just accept that the existing probe doesn't test classical_attribution directly.

If any tool's reachability% dropped, STOP and investigate.

---

## §F — Phase 5: Commit the registry doc updates

The only code-side change in this PR is the regenerated `CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md` and `.json`. The DB rows and GCS objects are side-effects; they don't show up in `git status`.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
git status
# Expected modified files:
#   08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md
#   08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json
#
# If the attribution_pass script modified anything else (e.g., a manifest entry
# for v1.1 of the registry), STOP and report. Don't auto-commit unexpected files.

git diff --stat 08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md \
                08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json

# Quick sanity: does the registry header reflect the new totals?
head -20 08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md
```

Ask the native to confirm before committing. Suggested message:

> "Phase 2B data backfill complete. classical_attributions grew from 420 rows
> (76 signals) to <N> rows (<M> signals). signal_states populated with <K> rows
> spanning 2024-2028. SLA probe rerun confirms tools now return non-empty
> results. Registry MD + JSON regenerated. Ready to commit + push?"

If approved:

```bash
git add 08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md \
        08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json

git status

git commit -m "data(retrieval): Phase 2B backfill — classical attribution expansion + signal_states activation

Data-only sub-phase. No code architecture changes. Brings two retrieval-tool
substrates from sparse/empty state to production-useful coverage:

CLASSICAL ATTRIBUTION (closes CF.M8.6):
- Re-ran scripts/run_attribution_pass.py against MSR v5.0 (573 signals)
- DB classical_attributions: 420 rows / 76 signals  →  <N> rows / <M> signals
- Coverage: 13.3%  →  <X>%
- Registry regenerated: CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md + .json
- GCS uploaded: gs://madhav-marsys-sources/L8/registries/

SIGNAL_STATES ACTIVATION (closes empty-table concern from audit §C.1):
- Ran scripts/temporal/signal_activator.py for abhisek_mohanty_primary
  across 2024-01-01 → 2028-12-31, vimshottari dasha system
- DB signal_states populated: <K> rows, <S> distinct signals
- query_signal_state tool now returns non-empty results for window-scan
  scenarios (verified via sla:probe-planner-blind rerun)

Audit references:
- 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md §F.M8.6
- 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md §C
- 00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2B_DATA_BACKFILL_BRIEF_v1_0.md
- predecessor: de1731e (Phase 2A — M9 wiring)

SLA probe post-backfill:
- query_signal_state today-only:           returned <N> rows (was 0)
- query_signal_state window-scan 2026:     returned <N> rows (was 0)
- classical_attribution_lookup (sample):   returned <N> rows (was sparse)
- All tools within SLA budget.

Post-deploy: DO NOT run npm run answer:eval per
project_retrieval_tools_consolidated_eval.md. Consolidated eval runs at
campaign close (after Phase 2C also ships).

Queued backfills completed this PR: classical_attribution_expansion,
signal_states_activation."

git push origin analysis/backend-data-pipeline-perf-audit
```

---

## §G — Phase 6: Report back

Deliver to native:

```markdown
# Phase 2B — Data Backfill Report

## Pre-flight (§A)
- Branch: analysis/backend-data-pipeline-perf-audit
- Working tree: clean
- Phase 2A in history: de1731e ✓
- Env: .env.rag symlink + gcloud auth + Vertex API ready

## Classical attribution (§C)
| Metric | Before | After | Δ |
|---|---|---|---|
| Total attributions | 420 | <N> | +<delta> |
| Signals attributed | 76 | <M> | +<delta> |
| Coverage % | 13.3% | <X>% | +<delta> |
| Distribution (confirms / contradicts / partial / extends / silent) | 21/8/10/64/317 | <new> | — |

- Registry MD/JSON regenerated: yes
- GCS uploaded: yes
- Wall clock: <X hours>
- Errors encountered: <none / list>

## signal_states activation (§D)
| Metric | Before | After |
|---|---|---|
| Total rows | <baseline> | <N> |
| Distinct signals | <baseline> | <M> |
| Date range | <baseline> | 2024-01-01 → 2028-12-31 |
| Lit on today (current state) | <baseline> | <K> |

- Wall clock: <X minutes/hours>
- Activator strategy: <per-day snapshot / state-change events / other>

## SLA probe rerun (§E)
| Scenario | Rows before | Rows after | Latency |
|---|---|---|---|
| query_signal_state today only | 0 | <N> | <ms> |
| query_signal_state window-scan 2026 | 0 | <N> | <ms> |
| query_signal_state current lit/ripening | 0 | <N> | <ms> |

All tools within SLA budget: <yes/no>

## Commit + push (§F)
- Committed: <yes/no/awaiting>
- SHA: <SHA>
- Files changed: 2 (registry MD + JSON)

## Anything anomalous
[any deviations]
```

---

## §H — Hard rules

- Stay on `analysis/backend-data-pipeline-perf-audit` in `/Madhav-analysis`. Never `cd` into `/Madhav` (Chat V2 worktree).
- Do NOT modify the attribution / activator script logic. Only run them and capture output.
- Do NOT commit anything other than the regenerated registry MD + JSON unless explicitly approved by native (e.g., if a script unexpectedly modifies a file, STOP and ask).
- Do NOT run `npm run answer:eval` — per `project_retrieval_tools_consolidated_eval.md` memory, the consolidated eval runs ONLY after Phase 2C ships.
- If the attribution pass takes > 6 hours wall-clock, pause and report — something may be wrong (rate limits, retries, judge timeouts).
- If signal_activator throws errors for specific signals (e.g., missing dasha boundaries, missing chart_facts), capture which signals fail and STOP. Don't skip silently.
- DB writes are non-reversible without restore. If §C.4 or §D.4 verification shows unexpected state (e.g., negative deltas, attribution_type distribution skewed), STOP before any cleanup.

---

## §I — Open questions the executor may need to resolve

These weren't fully knowable at brief-authoring time. Resolve and report:

1. **Does `run_attribution_pass.py` support `--skip-already-attributed`?** If not, the script may re-attribute the 76 already-covered signals (wasted work) or fail on duplicate key violations (DB constraint). Read script header before running.

2. **Does `signal_activator.py` write a row per (signal, day) or only state-change events?** Affects expected row count by 3+ orders of magnitude. Either is acceptable; just report which.

3. **Are there per-signal config files the activator needs?** Some signal-state rules require activation predicates that may be in a separate config (e.g., `signal_states_config.yaml` per signal). If a signal has no activator config, it gets no rows — that's why §D.4 expects signals_distinct ≥ 100, not = 573.

4. **GCS upload permissions**: registry .md + .json need write access to `gs://madhav-marsys-sources/L8/registries/`. If permission denied, ask native — don't try to escalate.

---

*End RETRIEVAL_TOOLS_PHASE_2B_DATA_BACKFILL_BRIEF_v1_0.md. Successor: Phase 2C brief (temporal SLA probe + cross_varga_dignity_query unit tests), authored at 2B close.*

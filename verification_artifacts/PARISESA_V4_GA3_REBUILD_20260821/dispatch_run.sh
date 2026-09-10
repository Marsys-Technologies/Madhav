#!/usr/bin/env bash
# PARIŚEṢA-V4 GA-3 — dispatch one bounded orchestrator run and block until terminal.
#
#   ./dispatch_run.sh <action> <asset[,asset...]> <label>
#
# action MUST be 'rebuild' to re-run an already-`lit` asset: 'build' only touches
# dormant|error|incomplete and silently skips lit ones (runner.py:487-493).
# Scope is always the single canonical chart; nothing else is written.
set -euo pipefail

CHART=482012f1-710e-4a25-994a-93821f5871aa
ACTION="$1"; ASSETS="$2"; LABEL="$3"
export PGPASSWORD=$(cat /tmp/.pgpw)
PG=(psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc)

# Refuse to stack runs — the orchestrator also holds an advisory lock per chart,
# but failing loudly here is better than discovering it in the job logs.
active=$("${PG[@]}" "select count(*) from build_runs where state in ('planned','running','paused')")
[ "$active" = "0" ] || { echo "REFUSING: $active run(s) already active"; exit 1; }

plan=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1].split(',')))" "$ASSETS")
RUN_ID=$("${PG[@]}" "
  WITH r AS (
    INSERT INTO build_runs (chart_id, scope, scope_target, action, plan, state, triggered_by)
    VALUES ('$CHART','asset_set','$ASSETS','$ACTION','$plan'::jsonb,'planned','parisesa-v4-ga3-$LABEL')
    RETURNING id
  ), a AS (
    INSERT INTO build_run_assets (run_id, asset_id, position, state)
    SELECT r.id, t.asset_id, t.ord-1, 'queued'
    FROM r, unnest(string_to_array('$ASSETS',',')) WITH ORDINALITY AS t(asset_id, ord)
    RETURNING run_id
  ) SELECT id FROM r")

echo "[$LABEL] run_id=$RUN_ID action=$ACTION assets=$ASSETS"
gcloud run jobs execute brahma-build-pipeline-job \
  --project=madhav-astrology --region=asia-south1 \
  --args=^:^--run-id:"$RUN_ID" >/dev/null 2>&1
echo "[$LABEL] dispatched; waiting for terminal state..."

while :; do
  st=$("${PG[@]}" "select state from build_runs where id='$RUN_ID'")
  case "$st" in planned|running) sleep 20;; *) break;; esac
done

echo "[$LABEL] run state=$st"
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -P pager=off -c \
  "select asset_id, state, rows_written, last_built_at,
          left(replace(coalesce(last_error,''),E'\n','|'),200) as err
     from asset_throughput
    where chart_id='$CHART'
      and asset_id = ANY(string_to_array('$ASSETS',','))
    order by asset_id"
[ "$st" = "complete" ] || [ "$st" = "succeeded" ] || echo "[$LABEL] NON-CLEAN TERMINAL STATE: $st"

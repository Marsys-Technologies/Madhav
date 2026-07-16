# infra/monitoring — Cloud Monitoring IaC

Codifies the dashboards, SLOs, and alert policies that back the production
observability surface for MARSYS-JIS (stream-b unit `4.observability`).

These files are **declarative** — the IaC is authored and reviewed here; the
session does **not** execute `gcloud` / `terraform apply` (production
constraint per the brief). The operator applies them on cutover via the
operator close-out runbook.

## Contents

| File                                | Purpose                                                        |
| ----------------------------------- | -------------------------------------------------------------- |
| `dashboards/request_latency.json`   | Per-route p50/p95/p99 latency + error rate (web, sidecar, mcp) |
| `dashboards/pipeline_health.json`   | Per-pipeline-stage latency + cache hit/miss (4.memorystore)    |
| `slos/request_latency.json`         | Latency SLO — 99% of `/api/consume/*` < 5s over 28d            |
| `slos/error_rate.json`              | Error-rate SLO — 99.5% of 2xx/3xx over 28d                     |
| `slos/build_success.json`           | Build-success SLO — 95% of `deploy.yml` runs green over 28d    |
| `alerts/latency_burn.json`          | 1h fast-burn + 6h slow-burn on request-latency SLO             |
| `alerts/error_rate_burn.json`       | 1h fast-burn + 6h slow-burn on error-rate SLO                  |
| `alerts/build_failure.json`         | Two consecutive failed deploys → page                          |
| `alerts/budget_kill_switch.json`    | Billing budget breach (>= 80% / >= 100%) wired to gate         |
| `alerts/local_proxy_drop_detection.json` | O-8 (D-1.6): Cloud SQL client-connection-drop burst — advisory signal for the local-proxy-kill-cycle that stalls session-driven rebuilds (see root-cause doc `O8_LOCAL_PROXY_KILL_ROOT_CAUSE_v1_0.md`) |

## Apply

```bash
# Dashboards
gcloud monitoring dashboards create --config-from-file=infra/monitoring/dashboards/request_latency.json
gcloud monitoring dashboards create --config-from-file=infra/monitoring/dashboards/pipeline_health.json

# SLOs (require beta API)
gcloud alpha monitoring slos create --service=amjis-web \
  --config-from-file=infra/monitoring/slos/request_latency.json
gcloud alpha monitoring slos create --service=amjis-web \
  --config-from-file=infra/monitoring/slos/error_rate.json
gcloud alpha monitoring slos create --service=amjis-build \
  --config-from-file=infra/monitoring/slos/build_success.json

# Alert policies
for f in infra/monitoring/alerts/*.json; do
  gcloud alpha monitoring policies create --policy-from-file="$f"
done
```

Notification channel id is `${ALERT_NOTIFICATION_CHANNEL_ID}` (operator
provides at apply time; default channel is the project's PagerDuty bridge
configured in Phase O).

## Synthetic end-to-end alert verification

To satisfy AC.2 ("one synthetic alert fires end-to-end") the operator
temporarily lowers the `error_rate_burn.json` threshold to `0.0001`, issues
a single 5xx via `/api/_diag/force-error?n=1`, and confirms the alert lands
in the configured channel. Threshold reverts immediately.

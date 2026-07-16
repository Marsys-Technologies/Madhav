---
artifact: O8_LOCAL_PROXY_KILL_ROOT_CAUSE
type: ROOT-CAUSE RECORD (D-1.6 Lane S-6, item O-8)
version: 1.0
status: CURRENT
authored_by: Claude Code (D-1.6 Lane S-6 implementer session, 2026-07-16)
---

# O-8 — the "proxy-kill cycle" — root cause, disposition, and detection

## §1 — What keeps getting killed

**Not** a Cloud Run service, **not** a Claude Code session/tool watchdog, **not** an OOM
kill. The thing that dies is the **local developer-machine `cloud-sql-proxy` process**
started by `platform/scripts/start_db_proxy.sh` (line ~19: `cloud-sql-proxy ...
--port=5433 &`) whenever a session runs a chart rebuild against the orchestrator from a
laptop instead of dispatching the Cloud Run job.

## §2 — Root cause (already diagnosed pre-D-1.6; this item formalizes it)

Diagnosed in `STATE_D-1.5b.md` §`precascade_rebuild.local_proxy_diagnosis`
(lines 39-49), corroborated by `REPORT_D-1.5a.md` (~line 111) and `REPORT_D-1.5b.md`
(~lines 63-66):

> "the laptop cloud-sql-proxy path is unreliable — proxy intermittently drops (fresh
> connect() fails in logs) AND bo_samskara's ~2-min/ayanamsha Vertex AI embed loop holds
> an idle DB conn long enough that a drop mid-embed kills the whole run, restarting
> embedding from scratch (Sisyphus loop). Product code already fully resilient
> (keepalives, idle-txn timeout=0 x2, batch-level embed tolerance) and completes fine in
> prod."

In plain terms: the local `cloud-sql-proxy` binary's own connection to Cloud SQL resets
intermittently under sustained load. This is a property of running the proxy from a
laptop's network path over a long-lived session, not a product-code defect — the
orchestrator and writers already have the resilience patterns (connection keepalives,
`idle_in_transaction_session_timeout=0` set twice, batch-level embedding tolerance) that
would make a *server-side* Cloud SQL connection survive a slow step. The failure mode is
specific: `bo_samskara` (Bodha embedding writer) holds one DB connection open across a
long Vertex AI embedding loop (~2 minutes per ayanamsha); if the *proxy* drops mid-loop,
the writer's connection dies with it, and — because the orchestrator's per-chart
delete-then-insert idempotency (CLAUDE.md §N.3) restarts the writer's substep from
scratch on retry — the same ~2-minute embed loop has to run again, and again, for every
subsequent proxy drop ("Sisyphus loop": 7 prior retries documented as dying to this
before the D-1.5b session routed around it).

**This is confirmed NOT to happen when the same rebuild runs inside GCP** (Cloud Run job
→ direct Cloud SQL connection, no local proxy hop): `STATE_D-1.5b.md`'s `status: COMPLETE`
entry records a clean 64/64-asset job run with zero partial embedding loss — the exact
failure the local proxy kept causing.

## §3 — Disposition

**PARK the underlying local-proxy reliability problem** — it is a laptop-network/
`cloud-sql-proxy`-binary characteristic, not something this lane's scope (or any
application code change) can fix. The **Cloud Run job path remains the sanctioned
workaround** (protocol §8.2's canonical rebuild mechanism: `POST /api/cockpit/runs` →
`brahma-build-pipeline-job`, or the documented manual dispatch via
`gcloud run jobs execute brahma-build-pipeline-job --args=--run-id,<id>`) and MUST NOT be
removed or treated as a stopgap — per D-1.5b's own forward-looking note, *every* future
full L1→L5 gate rebuild should default to the job path, not the laptop proxy, precisely
because the proxy path cannot reliably complete `bo_samskara`'s embedding loop.

## §4 — Detection alarm (this lane's deliverable)

There is no first-class GCP metric for "a process on someone's laptop died" — the proxy
is client-side, invisible to Cloud Monitoring by construction. The closest true,
GCP-observable symptom is on the **Cloud SQL server side**: when a proxy connection
resets abruptly mid-query, Postgres logs a client-disconnect signature
(`unexpected EOF on client connection` / `could not receive data from client: Connection
reset by peer`) to Cloud Logging under the `cloudsql_database` resource type.

Staged (not applied — see `REPORT_D-1.6.md` for the staging note; this is a new
alert-policy resource, not existing infra):
`infra/monitoring/alerts/local_proxy_drop_detection.json` — a `conditionMatchedLog`
policy on that log signature, following the existing declarative pattern in
`infra/monitoring/alerts/build_failure.json`. It is advisory, not an
auto-remediation trigger: a burst of this signature during a rebuild window is a
strong prior that the current run is about to Sisyphus-loop, and pages a human to check
`build_runs` for a stalled/restarted row and switch to the Cloud Run job path if so.
Registered in `infra/monitoring/README.md`'s alert table.

**Apply command (staged for the conductor to review and run — not executed by this
lane, per the GCP-write-ops staging rule):**

```bash
gcloud alpha monitoring policies create \
  --project=madhav-astrology \
  --policy-from-file=infra/monitoring/alerts/local_proxy_drop_detection.json
```

(Requires `${ALERT_NOTIFICATION_CHANNEL_ID}` to be resolved to a real channel ID first,
same as every other file in `infra/monitoring/alerts/` — see that directory's README
`## Apply` section for the substitution convention already in use.)

## §5 — Full source citations

- `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/STATE_D-1.5b.md:39-56` —
  primary diagnosis, method, COMPLETE status, and the forward-looking "learning" mandate
  to always use the job path for full-layer rebuilds.
- `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/REPORT_D-1.5a.md` (~line
  111) — earlier operational note: "The Cloud SQL Auth Proxy in this environment drops
  connections under sustained load — bounded-retry ... should be the default for any
  rebuild script, not an afterthought."
- `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/REPORT_D-1.5b.md` (~lines
  63-66) — rebuild executed via the Cloud Run job path specifically because of local
  proxy unreliability.
- `platform/scripts/start_db_proxy.sh` — the local proxy invocation in question.
- `infra/monitoring/alerts/build_failure.json` — template this lane's new alert follows.

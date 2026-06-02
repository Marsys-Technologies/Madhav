---
artifact: CLAUDECODE_BRIEF_BRAHMA_INFRA_VERIFICATION_v1_0.md
canonical_id: CLAUDECODE_BRIEF_BRAHMA_INFRA_VERIFICATION
version: 1.0
status: NOT_STARTED
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-02
authored_for: Claude Code (Antigravity, with GCP credentials)
purpose: >
  READ-ONLY verification sweep of the entire GCP footprint after the BRAHMA-INFRA-PROVISIONING seal,
  to confirm the baseline is aligned + deployment-ready BEFORE the Brahma build arc — so build deploys
  go seamlessly. Reports a pass/fail table; mutates nothing (one optional cleanup is flagged separately).
reads_with:
  - CLAUDECODE_BRIEF_BRAHMA_INFRA_PROVISIONING_v1_0.md (what was provisioned)
  - INFRA_RECONCILIATION_v1_0.md (the keep/drop dispositions)
project_facts:
  project: madhav-astrology
  region: asia-south1
  services: [amjis-web, amjis-sidecar, amjis-mcp]
  sql_instance: amjis-postgres            # expect tier db-g1-small, RUNNABLE, no HA
  job: brahma-foundation-bootstrap        # placeholder image
  keep_buckets: [madhav-astrology-chat-attachments, madhav-astrology-chart-documents, madhav-astrology-tf-state, madhav-brahma-olap]
  gone_bucket: madhav-marsys-build-artifacts
  bq_dataset: brahma_l5_olap
  runtime_sas: [amjis-web-runtime, amjis-sidecar-runtime, amjis-mcp-runtime, amjis-builder-runtime, brahma-analytics]
  gone_sa: amjis-build-invoker
  public_domain: madhav.marsys.in         # Firebase Hosting front
---

# Brahma Infra Verification — read-only alignment sweep

## §0 — Rules
**Read-only. Run nothing that mutates** (no create/delete/update/patch) except §15's *optional* orphaned-cert
cleanup, which is called out separately and needs explicit approval. Set project first; emit a **PASS/FAIL
table** at the end with the expected vs observed value for each line.

```bash
gcloud config set project madhav-astrology
```

## §1 — Cloud Run services (expect 3, all Ready, min=0, asia-south1)
```bash
gcloud run services list --region asia-south1 \
  --format="table(metadata.name, status.conditions[0].status, spec.template.metadata.annotations['autoscaling.knative.dev/minScale'])"
```
PASS: exactly `amjis-web`, `amjis-sidecar`, `amjis-mcp`; all Ready=True; minScale=0. No `amjis-tracker`.
Then for each, confirm the serving revision + that no env var references a deleted secret/bucket:
```bash
for s in amjis-web amjis-sidecar amjis-mcp; do
  echo "== $s =="; gcloud run services describe $s --region asia-south1 \
    --format="yaml(status.latestReadyRevisionName, spec.template.spec.containers[0].env, spec.template.spec.containers[0].image)"
done
```
PASS: no `ANTHROPIC_API_KEY`, no `BUILD_STATE_GCS_BASE`, no `BUILD_TASK_*` env; DB password ref = version 3;
`PYTHON_SIDECAR_URL` present on web; images resolve to the Artifact Registry repo.

## §2 — Cloud Run Jobs (expect bootstrap only; no legacy build job)
```bash
gcloud run jobs list --region asia-south1 --format="table(metadata.name, spec.template.spec.template.spec.containers[0].image)"
```
PASS: `brahma-foundation-bootstrap` present (image = the cloud-sdk:slim PLACEHOLDER — flag for replacement);
NO `marsys-build-pipeline-job`.

## §3 — Cloud SQL (expect db-g1-small, RUNNABLE, no HA)
```bash
gcloud sql instances describe amjis-postgres \
  --format="yaml(settings.tier, state, settings.availabilityType, region, databaseVersion, settings.backupConfiguration.enabled)"
gcloud sql databases list --instance amjis-postgres --format="table(name)"
```
PASS: tier `db-g1-small`; state `RUNNABLE`; availabilityType `ZONAL` (no HA); region asia-south1; db `amjis` present.

## §4 — Memorystore (expect NONE)
```bash
gcloud redis instances list --region asia-south1
```
PASS: empty (no `amjis-cache`). *(It was accidentally recreated once — re-confirm it's truly gone.)*

## §5 — Cloud Tasks (expect NONE)
```bash
gcloud tasks queues list --location asia-south1
```
PASS: empty (no `amjis-build-queue`).

## §6 — Load Balancer / networking (expect ALL EMPTY)
```bash
gcloud compute forwarding-rules list
gcloud compute target-https-proxies list
gcloud compute target-http-proxies list
gcloud compute url-maps list
gcloud compute backend-services list
gcloud compute network-endpoint-groups list
gcloud compute addresses list
gcloud compute security-policies list          # Cloud Armor
gcloud compute ssl-certificates list           # watch for orphaned amjis.madhavstreamc.io cert
```
PASS: forwarding-rules / proxies / url-maps / backend-services / NEGs / static addresses / Cloud Armor all
empty. SSL-certs: ideally empty; if an `amjis.madhavstreamc.io` managed cert lingers → §15.

## §7 — Firebase Hosting front (expect madhav.marsys.in serving)
```bash
firebase hosting:sites:list                                  # the site backing madhav.marsys.in
curl -sS -o /dev/null -w "%{http_code} %{time_total}s\n" https://madhav.marsys.in/api/health
curl -sSI https://madhav.marsys.in | grep -i "server\|strict-transport"
```
PASS: `/api/health` → 200; served via Google Frontend/Firebase; valid cert.

## §8 — GCS buckets (expect 4 kept, 1 gone)
```bash
gcloud storage buckets list --format="table(name, location)"
```
PASS: present — chat-attachments, chart-documents, tf-state, `madhav-brahma-olap`. ABSENT — `madhav-marsys-build-artifacts`.

## §9 — BigQuery (expect brahma_l5_olap + analytics access)
```bash
bq ls --location=asia-south1
bq show --format=prettyjson madhav-astrology:brahma_l5_olap | grep -A3 access
```
PASS: `brahma_l5_olap` exists; `brahma-analytics@` has WRITER.

## §10 — Service accounts (expect runtime SAs; invoker + tracker GONE)
```bash
gcloud iam service-accounts list --format="table(email, disabled)"
```
PASS: present — amjis-web-runtime, amjis-sidecar-runtime, amjis-mcp-runtime, amjis-builder-runtime,
brahma-analytics. ABSENT — `amjis-build-invoker`, any tracker SA.

## §11 — Secrets (expect Anthropic gone; kept set present)
```bash
gcloud secrets list --format="table(name, createTime)"
gcloud secrets versions list amjis-db-password --format="table(name, state)" | head
```
PASS: NO `ANTHROPIC_API_KEY`; present — firebase creds, `amjis-db-password` (latest enabled = v3), the
Gemini/DeepSeek/NVIDIA/sidecar keys, mcp tokens. (5 uppercase names still pending rename — non-blocking.)

## §12 — Cloud Scheduler (confirm reaper isn't erroring on a dead endpoint)
```bash
gcloud scheduler jobs list --location asia-south1 --format="table(name, schedule, state, httpTarget.uri)"
```
PASS: `build-reaper` state ENABLED and its target `/api/build/reap` still resolves (or is intentionally
paused). FLAG if it's hitting a removed endpoint → pause it until the build arc re-establishes the path.

## §13 — Artifact Registry (deploy source images present)
```bash
gcloud artifacts repositories list --format="table(name, format, location)"
gcloud artifacts docker images list asia-south1-docker.pkg.dev/madhav-astrology/amjis --include-tags 2>/dev/null | head
```
PASS: the `amjis` repo exists with current images for web/sidecar/mcp (so CI deploys have a source).

## §14 — DEPLOYMENT READINESS (the "build deploys seamlessly" gate)
The things that would make a build/deploy fail — verify each:
```bash
# (a) runtime SAs have the roles the services need
gcloud projects get-iam-policy madhav-astrology --flatten="bindings[].members" \
  --filter="bindings.members:amjis-web-runtime@madhav-astrology.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```
PASS (web-runtime): cloudsql.client, secretmanager.secretAccessor, aiplatform.user, storage.objectAdmin (or
scoped), bigquery.jobUser (if it writes BQ). **CHECK for `run.jobsExecutorWithOverrides`** (or run.invoker on
the job) — needed for the direct `jobs.run` build trigger. If ABSENT → this is the one known gap (the old
build-invoker grant was removed); it must be added before the first chart-build job runs. Repeat the policy
check for sidecar-runtime (cloudsql.client, secretmanager, aiplatform.user) and builder-runtime (the job's SA).
```bash
# (b) DB reachable from a service + extensions present
gcloud sql instances describe amjis-postgres --format="value(ipAddresses[].ipAddress, connectionName)"
#   (via cloud-sql-proxy as amjis_app) — confirm connect + extensions:
#   psql -c "SELECT extname FROM pg_extension;"   → expect vector, pg_trgm, uuid-ossp
#   psql -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"  → 46
# (c) RLS posture (the auth.uid()->NULL stub from Phase 3 — verify before data lands)
#   psql -c "SELECT relname FROM pg_class WHERE relnamespace='public'::regnamespace AND relrowsecurity;"
#     → if any app tables have RLS enabled with auth.uid() policies, note them (would match 0 rows for amjis_app)
# (d) CI/deploy workflow sanity — no dangling refs to deleted resources
grep -nE "BUILD_TASK|amjis-build-queue|ANTHROPIC|BUILD_STATE_GCS_BASE|madhav-marsys-build-artifacts" .github/workflows/deploy.yml || echo "clean"
# (e) cold-start smoke (scale-to-zero is fine but confirm wake works)
curl -sS -o /dev/null -w "web %{http_code} %{time_total}s\n" https://madhav.marsys.in/
curl -sS -o /dev/null -w "mcp %{http_code}\n" "$(gcloud run services describe amjis-mcp --region asia-south1 --format='value(status.url)')/health"
```
PASS: web + mcp wake from cold and return 200; DB connects with vector/pg_trgm/uuid-ossp + 46 tables;
deploy.yml grep = clean; web-runtime role check surfaces the jobsExecutor gap (expected) for tracking.

## §15 — Optional cleanup (NOT read-only — explicit approval needed)
If §6 shows an orphaned `amjis.madhavstreamc.io` managed SSL cert (left from the old LB), delete it:
```bash
# gcloud compute ssl-certificates delete <name> --global    # ONLY after native confirms
```

## §16 — Report
Emit a PASS/FAIL table (component · expected · observed · verdict). Call out explicitly: (1) the
`run.jobsExecutorWithOverrides` gap on web-runtime, (2) the bootstrap placeholder image, (3) any RLS-enabled
tables, (4) the reaper endpoint status, (5) any orphaned cert. These five are the build-arc pre-reqs.

---

*End of CLAUDECODE_BRIEF_BRAHMA_INFRA_VERIFICATION v1.0 — read-only alignment sweep, Cowork 2026-06-02. Run in
Antigravity; report the PASS/FAIL table. Mutates nothing except the optional §15 cert cleanup (gated).*

---
artifact: CLAUDECODE_BRIEF_BRAHMA_INFRA_PROVISIONING_v1_0.md
canonical_id: CLAUDECODE_BRIEF_BRAHMA_INFRA_PROVISIONING
version: 1.0
status: NOT_STARTED          # Claude Code flips → IN_PROGRESS → COMPLETE
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-02
authored_for: Claude Code (Antigravity execution session, with GCP credentials)
execution_surface: Antigravity / Claude Code (Cowork plans; Antigravity executes)
reads_with:
  - INFRA_RECONCILIATION_v1_0.md (the keep/drop dispositions this executes)
  - INFRA_COST_COMPARISON_BRAHMA_v1_0.md (the cost target)
  - LEGACY_TEARDOWN_KILL_LIST_v1_0.md + CLAUDECODE_BRIEF_LEGACY_TEARDOWN_v1_0.md (the data/code/tools wipe)
  - INFRASTRUCTURE_INVENTORY_v1_0.md (target infra + rates)
confirmed_decisions:
  - build_trigger: DIRECT jobs.run trigger (drop Cloud Tasks amjis-build-queue)   # native 2026-06-02
  - cloud_sql: WIPE amjis-postgres IN PLACE + fresh Brahma schema                  # native 2026-06-02
  - lb_cdn: DROP infra/edge → Cloud Run direct domain mapping (Option A)           # native 2026-06-02 (resolves the INFRA_RECONCILIATION conflict → DROP)
  - execution: this CLAUDECODE_BRIEF, run in Antigravity                           # native 2026-06-02
preconditions:
  - "PR #187 (feature/legacy-teardown) MUST be merged to main before Phase 1 runs — OPEN as of 2026-06-02 (S748). Phase 0 may run before the merge (read-only + backups)."
live_state_corrections_2026_06_02:
  - cloud_sql_current_tier: "db-custom-1-3840 (1 vCPU / 3.75 GB) — confirmed live; target db-g1-small (shared-core ~1.7 GB). See §5 RAM caveat."
  - memorystore: "amjis-cache READY (Redis 7.2, 1 GB) — confirmed; DELETE in Phase 2."
  - cloud_tasks: "amjis-build-queue RUNNING — confirmed; DELETE in Phase 2."
  - pr_187: "feature/legacy-teardown OPEN, no merge SHA — blocks Phase 1."
project_facts:
  gcp_project: madhav-astrology
  region: asia-south1
  services: [amjis-web, amjis-sidecar, amjis-mcp]
  cloud_sql_instance: amjis-postgres   # conn madhav-astrology:asia-south1:amjis-postgres; db=amjis; user=amjis_app
  build_job: marsys-build-pipeline-job
  buckets: [madhav-marsys-build-artifacts, madhav-astrology-chat-attachments, madhav-astrology-chart-documents, madhav-astrology-tf-state]
  memorystore: amjis-cache
  cloud_tasks_queue: amjis-build-queue
  scheduler: build-reaper
  iac_modules: [infra/iam, infra/edge, infra/memorystore, infra/cloud_scheduler, infra/cloud_tasks]
  embeddings: text-multilingual-embedding-002   # 768-dim; final model pending C4 spike
---

# CLAUDECODE_BRIEF — Brahma Infrastructure Provisioning v1.0

## §0 — How to use this brief

This is the executable, gated runbook to realign the GCP footprint to the cost-optimized Brahma target
(~$30–60/mo). **Cowork staged it; Claude Code executes it in Antigravity with credentials.** To activate:
point the root `CLAUDECODE_BRIEF.md` at this file (or open the Antigravity session against it), set
`status: IN_PROGRESS`, and work the phases in order.

**Hard rule — every phase marked 🔒 HUMAN-GATED stops for explicit native approval before running.** Several
steps are irreversible (DB wipe, resource deletes). Do not batch past a gate. Each phase has **verify** and
**rollback**.

Commands below are reference `gcloud`/`terraform`/`psql` forms for `madhav-astrology` / `asia-south1` — the
executor confirms exact flags against current CLI versions. Placeholders in `<...>`.

## §1 — Standing constraints (binding on this session)

- 🔒 Prod DB ops, deploys, secret rotation, resource deletes, the legacy teardown — **all human-gated**.
- **Back up before any destructive step.** The Cloud SQL wipe and bucket purges are irreversible.
- **No Anthropic models in any production path** (remove the secret).
- **DATA RETENTION — native directive 2026-06-02: WIPE, do NOT archive.** Legacy data is useless to the
  native and not worth a cent of storage. So: (a) **skip the cold-archive** entirely — do NOT run the
  archiving in `infra/teardown/00_archive.sh`; (b) **DELETE the Phase-0 full-DB backup + GCS export** (they
  are no longer a required restore path); (c) the **only** retained ground truth is **`life_events` (LEL)**,
  which is preserved live (the teardown never drops it) AND in git (`LIFE_EVENT_LOG_v1_2.md`). FORENSIC v8.0 +
  all legacy code remain preserved **for free in the `brahma-preflight-20260602` git tag** — so nothing
  irreplaceable is lost by wiping the DB/GCS/backup. (Supersedes the earlier "archive FORENSIC cold to GCS"
  step — git history is the zero-cost benchmark archive.)
- Keep the three Cloud Run **shells**; the teardown wipes their *contents*, not the services.
- `must_not_touch`: the consult/chat serve path beyond config; the tf-state bucket contents; any non-Brahma project.

## §2 — Phase 0 · Pre-flight & safety  🔒 HUMAN-GATED

**Goal:** a clean, reversible starting point + full backups before anything destructive.

```bash
gcloud config set project madhav-astrology
gcloud config set run/region asia-south1
gcloud auth list   # confirm the right operator identity

# 1. FULL Cloud SQL backup (on-demand) + export to GCS (the wipe is irreversible)
gcloud sql backups create --instance=amjis-postgres
gcloud sql export sql amjis-postgres \
  gs://madhav-astrology-tf-state/brahma-preflight/amjis-$(date +%Y%m%d).sql.gz \
  --database=amjis

# 2. Snapshot current service configs + revisions (for rollback)
for s in amjis-web amjis-sidecar amjis-mcp; do
  gcloud run services describe $s --region asia-south1 --format=export > /tmp/preflight-$s.yaml
done
gcloud run jobs describe marsys-build-pipeline-job --region asia-south1 --format=export > /tmp/preflight-job.yaml

# 3. Snapshot Terraform state + repo tag
cd infra && terraform state pull > /tmp/preflight-tfstate.json && cd ..
git tag brahma-preflight-$(date +%Y%m%d) && git push --tags
```

**Verify:** backup file exists in GCS; 3 service snapshots + job snapshot + tfstate saved; repo tagged.
**Rollback:** none needed (read-only + backups).
**Gate:** native confirms backups are good → proceed.

**Phase 0.1 · Delete the full-DB backup (native directive 2026-06-02 — useless data, do not store).**
Safe because LEL survives live (never dropped) + in git, and FORENSIC + code survive in the
`brahma-preflight-20260602` tag — so deleting the full-DB backup loses nothing irreplaceable.
```bash
# delete the on-demand Cloud SQL backup
gcloud sql backups delete 1780417300386 --instance=amjis-postgres
# delete the 440.8 MiB GCS SQL export
gsutil rm gs://madhav-astrology-tf-state/brahma-preflight/amjis-20260602.sql.gz
```
(The lightweight config/tfstate snapshots in /tmp are free and may be kept for the duration of the run.)

## §3 — Phase 1 · Legacy teardown  🔒 HUMAN-GATED · ⛔ BLOCKED until PR #187 merged

**HARD PRECONDITION:** **PR #187 (`feature/legacy-teardown`) must be merged to `main` first** — it was opened
at S748 and is OPEN with no merge SHA as of 2026-06-02. PR-to-main is human-gated; the native reviews + merges
#187 before this phase runs. Phase 0 (§2) may run before the merge (it's read-only + backups); Phase 1 may not.

**Goal:** execute the clean-slate wipe per `LEGACY_TEARDOWN_KILL_LIST_v1_0` — data, build code, tools — while
keeping the shells; archive FORENSIC v8.0 cold.

- Run `CLAUDECODE_BRIEF_LEGACY_TEARDOWN_v1_0` (the staged teardown). Key actions: archive FORENSIC v8.0 →
  `gs://madhav-marsys-build-artifacts/archive/forensic_v8/` (cold); delete legacy asset data + build-code +
  legacy tool registrations; do **not** delete the service shells.
- Purge legacy build artifacts: keep the bucket, clear legacy objects (after the Phase-0 backup):
  ```bash
  gsutil -m rm -r gs://madhav-marsys-build-artifacts/builds/** || true   # legacy build state
  ```
- Legacy DB tables are dropped in Phase 3 (schema wipe), not here.

**Verify:** FORENSIC archived + retrievable; legacy build code/tools removed; shells still deployed + healthy.
**Rollback:** restore from the Phase-0 backup / archive; redeploy prior revisions from snapshots.
**Gate:** native confirms teardown scope before deletes run.

## §4 — Phase 2 · Cost-optimization realign (config)  🔒 HUMAN-GATED for deletes

**Goal:** the four cost levers — scale-to-zero, drop Memorystore, drop the LB, drop Cloud Tasks — plus the
tracker + secret hygiene.

```bash
# Lever 1 — scale-to-zero the three services (biggest saving)
for s in amjis-web amjis-sidecar amjis-mcp; do
  gcloud run services update $s --region asia-south1 --min-instances=0
done

# Lever 2 — drop Memorystore (cache moves to Postgres)  🔒
gcloud redis instances delete amjis-cache --region asia-south1
#   then remove the infra/memorystore module (Phase 5) + any REDIS_* env on amjis-web

# Lever 3 — replace the external HTTPS LB + CDN with a FREE front for madhav.marsys.in  🔒
#   CORRECTION (2026-06-02): Cloud Run DIRECT domain mapping is NOT available in asia-south1
#   (supported only in us-central1/us-east1/europe-west1/asia-northeast1). The LB is therefore
#   load-bearing today. Replace it with a free front, in this order — NEVER delete the LB first:
#     (1) PREFERRED: Firebase Hosting rewrite → Cloud Run. First TEST region support (zero-risk):
#         firebase.json: {"hosting":{"rewrites":[{"source":"**","run":{"serviceId":"amjis-web","region":"asia-south1"}}]}}
#         firebase deploy --only hosting   # errors immediately if asia-south1 unsupported (no change)
#     (2) FALLBACK if Firebase rejects asia-south1: Cloudflare (region-agnostic) — proxy
#         madhav.marsys.in → the amjis-web *.run.app URL (free SSL + CDN).
#     (3) If both disappoint: KEEP the LB (~$18–22/mo) — acceptable, nothing lost.
#   Then point madhav.marsys.in DNS at the chosen front, VERIFY end-to-end serving, and only THEN
#   delete the LB + infra/edge (Phase 5). Domain = madhav.marsys.in (update infra/edge domain var,
#   currently defaulted to amjis.madhavstreamc.io).

# Lever 4 — drop Cloud Tasks; wire direct jobs.run trigger  🔒
gcloud tasks queues delete amjis-build-queue --location asia-south1
#   CODE: replace the /api/build/task enqueue with a direct Cloud Run Jobs execution:
#     gcloud run jobs execute marsys-build-pipeline-job --region asia-south1 \
#        --args="--build-id=<id>,--chart-id=<id>"
#   (API uses the Run Admin API jobs.run with the build-invoker SA; remove the OIDC task handler)

# amjis-tracker — confirm already gone
gcloud run services delete amjis-tracker --region asia-south1 2>/dev/null || echo "tracker already absent"

# Secret hygiene  🔒
gcloud secrets delete ANTHROPIC_API_KEY            # no Anthropic in prod
#   rotate amjis-db-password (create new version, update Cloud SQL user + Secret Manager, redeploy)
#   rename legacy-uppercase secrets per platform/scripts/governance/secret_naming.md
```

**Verify:** `min-instances=0` on all 3 (`gcloud run services describe ... | grep minScale`); `amjis-cache`
gone; domain resolves via Cloud Run mapping; `amjis-build-queue` gone; a manual `jobs execute` runs; Anthropic
secret absent. **Rollback:** restore `min-instances=1` + recreate deleted resources from snapshots/IaC; the LB
+ Memorystore can be re-applied from prior tf-state if needed. **Gate:** approval before each delete.

## §5 — Phase 3 · Right-size + wipe Cloud SQL in place + fresh schema  🔒 HUMAN-GATED (IRREVERSIBLE)

**Goal:** shared-core instance + a fresh Brahma schema baseline. **Backup (Phase 0) must be confirmed first.**

> **Live tier (confirmed 2026-06-02):** current is `db-custom-1-3840` (1 vCPU / 3.75 GB). Target `db-g1-small`
> (shared-core, ~1.7 GB). **RAM caveat:** 1.7 GB is fine for ~10 clients' pgvector (~tens of thousands of
> 768-dim vectors) + bounded builds, but if HNSW index builds or concurrent chart builds hit memory pressure,
> step up to `db-custom-1-3840` (~$50/mo) — a tuning knob, not a redesign. Pick `db-g1-small` first; monitor.

```bash
# Right-size to shared-core (requires a brief restart — do in a window)
gcloud sql instances patch amjis-postgres --tier=db-g1-small   # ~$25–35/mo; current=db-custom-1-3840; watch pgvector RAM

# Full wipe in place: drop schema, recreate clean, re-enable pgvector.
# LEL note (native directive 2026-06-02): do NOT preserve the DB's life_events rows — a full copy
# (57 events) lives in LIFE_EVENT_LOG_v1_2.md + the facts-only file + git. The straight DROP is fine.
psql "$ADMIN_CONN" <<'SQL'
  DROP SCHEMA public CASCADE;
  CREATE SCHEMA public;
  GRANT ALL ON SCHEMA public TO amjis_app;
  CREATE EXTENSION IF NOT EXISTS vector;
SQL

# Apply the FRESH Brahma migration baseline (new series authored at build phase)
#   e.g. the new platform/migrations/brahma/0001_*.sql … run in order
```

**Verify:** `db-g1-small` tier active; `\dt` shows only the Brahma baseline tables; `vector` extension present;
a trivial embedding insert/query works. **LEL:** `life_events` is intentionally empty post-wipe — the
authoritative **57** events live in `LIFE_EVENT_LOG_v1_2.md` (git); the rebuild's LEL intake
(`LEL_SCHEMA_AND_INTAKE §0`) ingests them from that `.md` (the locked source). **Rollback:** none — the Phase-0
backup was deleted per the native's wipe directive (legacy data is useless); tier revert via
`--tier=db-custom-1-3840`. **Gate:** native explicitly confirms "wipe now."

## §6 — Phase 4 · New provisioning

```bash
# BigQuery — L5 cross-corpus OLAP (Master Arch C3)
bq --location=asia-south1 mk --dataset madhav-astrology:brahma_l5_olap
#   grant the analytics SA; Parquet export path target = a GCS prefix

# One-time Brahmagyan/L0 + infra bootstrap Job (shell now; run when L0 build is ready)
gcloud run jobs create brahma-foundation-bootstrap \
  --region asia-south1 --image <l0-bootstrap-image> \
  --max-retries 1 --task-timeout 3600
```

**Verify:** BigQuery dataset exists + IAM set; bootstrap job created (not yet run). **Rollback:** delete the
dataset/job (no data yet). **Gate:** none (additive, no destruction).

## §7 — Phase 5 · IaC + CI realign  🔒 HUMAN-GATED (terraform apply)

**Split this phase: 5a (safe IaC, now) and 5b (LB swap, gated on the front serving). Do NOT bundle them.**

```bash
# ── Phase 5a · safe IaC removals (memorystore + cloud_tasks + iam) — does NOT touch edge/LB ──
cd infra
git rm -r memorystore cloud_tasks          # drop the two modules
#   edit iam/main.tf → drop tracker SA + (Tasks gone) amjis-build-invoker; KEEP runtime SAs
#   DO NOT edit/remove edge/main.tf in 5a — the LB stays until 5b verifies the replacement.

# STATE RECONCILE: amjis-cache + amjis-build-queue were deleted by hand in Phase 2, but Terraform
#   state still references them → a plain plan will show drift. Drop them from state first so the
#   plan is clean (not a confusing "recreate"/"destroy-missing"):
terraform state list | grep -E "memorystore|redis|cloud_tasks|amjis-build-queue|amjis-cache"
terraform state rm <those addresses>       # reconcile before planning

terraform plan -out=brahma5a.plan          # 🔒 PRESENT the plan to the native; it must show ONLY
                                           #    iam SA drops + the (already-gone) module cleanup,
                                           #    and MUST NOT show edge/LB/forwarding-rule destroy.
terraform apply brahma5a.plan              # 🔒 only after the native approves the plan
cd ..

# deploy.yml realign (safe): set --min-instances=0 ×3; remove Cloud Tasks deploy steps; add the
#   BigQuery/bootstrap-job env; keep NEXT_PUBLIC build-arg discipline; prune legacy R9/R10/R11 flags.
```

```bash
# ── Phase 5b · LB → free front (gated: front must serve madhav.marsys.in BEFORE the LB is deleted) ──
# 1. TEST Firebase asia-south1 support (zero-risk): firebase.json rewrite run.region=asia-south1 →
#    firebase deploy --only hosting  (errors immediately + harmlessly if unsupported).
# 2. If OK → Firebase front; else → Cloudflare proxy to the *.run.app URL; else → KEEP the LB (stop 5b).
# 3. Point madhav.marsys.in DNS at the chosen front; VERIFY end-to-end HTTPS serving.
# 4. ONLY THEN: edit edge/main.tf out, terraform plan/apply to destroy the LB + CDN + cert + NEG.
#    (set the edge domain var to madhav.marsys.in if any transitional step still needs it.)
```

**Verify:** post-5a `terraform state list` has no memorystore/cloud_tasks and **still has edge** (LB intact);
CI deploys all 3 at `min=0`. Post-5b (only if a free front landed): `madhav.marsys.in` serves over HTTPS via
the front, and the LB/forwarding-rule is gone. **Rollback:** 5a — `git revert` + re-apply prior plan; 5b — the
LB is only removed after the front works, so the fallback is simply "don't run 5b / keep edge." **Gate:** plan
reviewed before each apply; LB destroy gated on the front serving.

## §8 — Phase 6 · Verify, cost-check, seal

- **Cost check:** confirm `min-instances=0` ×3, Memorystore absent, LB/forwarding-rule absent, Cloud SQL =
  shared-core. Sanity the projected bill against INFRA_COST_COMPARISON (~$30–60/mo).
- **Smoke:** portal loads (accept cold start); a chart build runs end-to-end via the **direct jobs.run**
  trigger; MCP reachable; DB + pgvector reachable; an embedding round-trips.
- **Backups retained:** the Phase-0 export + FORENSIC archive are kept.
- **Seal:** set `status: COMPLETE`; update `INFRA_RECONCILIATION` + `INFRASTRUCTURE_INVENTORY` status →
  PROVISIONED; append the result to `CURRENT_STATE` (v5.69) + a formal `SESSION_LOG` close; run
  `drift_detector.py` + `schema_validator.py` in CI.

## §9 — Acceptance criteria (session is COMPLETE only when all true)

1. Three services on `min-instances=0`; cold-start verified acceptable.
2. Memorystore `amjis-cache` deleted; caching served from Postgres.
3. External LB/CDN removed; domain served via Cloud Run mapping (or run.app).
4. Cloud Tasks `amjis-build-queue` removed; build runs via direct `jobs.run`; no 401.
5. `amjis-postgres` = shared-core; legacy schema wiped; fresh Brahma baseline applied; pgvector live.
6. `ANTHROPIC_API_KEY` removed; DB password rotated; secrets renamed.
7. BigQuery dataset + bootstrap Job provisioned; FORENSIC v8.0 archived (not deleted).
8. IaC: memorystore + cloud_tasks modules removed; `terraform apply` clean; deploy.yml realigned.
9. End-to-end smoke green; Phase-0 backups retained; docs + CURRENT_STATE + SESSION_LOG updated.

## §10 — Rollback-of-last-resort

Restore the Cloud SQL export (Phase 0), redeploy the snapshotted service revisions, `terraform apply` the
pre-flight plan, and re-point DNS. The repo tag `brahma-preflight-*` is the code anchor. Because the shells
were never deleted and the DB was backed up, full recovery to the pre-provisioning state is always available.

---

*End of CLAUDECODE_BRIEF_BRAHMA_INFRA_PROVISIONING v1.0 — staged in Cowork 2026-06-02 for Antigravity
execution. Decisions confirmed: direct jobs.run trigger · wipe amjis-postgres in place · Antigravity brief.
Every 🔒 gate stops for native approval; every destructive step is preceded by a backup and followed by a
verify + rollback. Cowork plans; Antigravity executes.*

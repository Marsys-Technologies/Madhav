---
artifact: INFRA_RECONCILIATION_v1_0.md
canonical_id: INFRA_RECONCILIATION
version: 1.0
status: LOCKED 2026-06-02 (per-component disposition DECIDED; provisioning is the next session, human-gated)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-02
authored_for: native (Abhisek Mohanty)
reads_with:
  - INFRASTRUCTURE_INVENTORY_v1_0.md (the target GCP infra decisions + cost)
  - MARSYS_MASTER_ARCHITECTURE_v2_0.md (v2.1 — L0–L5 + OLAP/BigQuery + embedding spike)
  - LEGACY_TEARDOWN_KILL_LIST_v1_0.md (the data/build-code/tools wipe — distinct from infra)
grounded_in: >
  A live-footprint inventory of the deployed GCP project `madhav-astrology` (region asia-south1):
  3 Cloud Run services, 1 Cloud Run Job, Cloud SQL + pgvector, Cloud Tasks, Cloud Scheduler,
  Memorystore, 3 GCS buckets, Vertex AI embeddings, 6 Terraform modules under infra/, 90+ migrations.
purpose: >
  Answer the native's question — decommission the existing infrastructure, or realign it to the Brahma
  requirements? — with a per-component disposition (KEEP / REALIGN / DECOMMISSION / NEW), the headline
  verdict, and the locked actions, as the precursor to the infrastructure provisioning session.
---

# Infrastructure Reconciliation — Project Brahma

## §A — Headline verdict: REALIGN, do not wholesale-decommission

The clean slate is at the **data + build-code + tools** layer (the legacy teardown kill-list) — **not** the
**infrastructure** layer. The deployed GCP footprint is **~85% reusable**: the serve shells, the database
instance, object storage, the edge/LB, the scheduler, IAM, and embeddings all carry forward. We **realign**
their *contents and config* to Brahma and **decommission only four** things that are either cost dead-weight,
a known failure class, or policy-violating. We **add two** net-new pieces (BigQuery OLAP + the one-time
Brahmagyan/infra bootstrap job). This matches INFRASTRUCTURE_INVENTORY §12 ("keep the Cloud Run shells; drop
the build pipeline contents") and avoids a needless, risky teardown of working infrastructure.

**Decommission (5):** `amjis-tracker` (already retired), Memorystore `amjis-cache` (cost), the Cloud Tasks
`amjis-build-queue` (replace with a direct Cloud Run Job trigger — removes the build-task 401 class), the
`ANTHROPIC_API_KEY` secret (no Anthropic in any production path), and the **external HTTPS Load Balancer + CDN
(`infra/edge`)** — serve via Cloud Run direct domain mapping (resolved 2026-06-02; see note below).

> **Conflict resolution (2026-06-02):** v1.0 first listed `infra/edge` as KEEP·REALIGN. The subsequent
> cost-optimization pass (INFRA_COST_COMPARISON_BRAHMA §B) and the provisioning brief both DROP it. Under the
> native's "highly cost-optimized, ~10 internal users" mandate, **DROP wins** (Option A): a global LB+CDN is
> built for public scale we don't have; Cloud Run's direct domain mapping gives free HTTPS + custom domain.
> CDN edge-caching and Cloud Armor are not needed at this scale and can be re-added later if traffic grows.
> All three docs are now aligned to DROP.

**Add (2, in the provisioning session):** BigQuery + Parquet-export path for L5 cross-corpus OLAP (Master Arch
C3); a one-time **Brahmagyan/L0 + infra bootstrap** Cloud Run Job (admin-only).

## §B — Per-component disposition (locked)

| Component (live) | Disposition | Realignment / action |
|---|---|---|
| **Cloud Run `amjis-web`** (Next.js portal + consume) | **KEEP · REALIGN** | scale-to-zero (`min-instances 1→0`); re-base build cockpit to the **Layer Tower + L0–L5**; add **CRUD** (edit/delete) + state-aware build page; **Brahma lexicon**; front-end via Claude Code plugins. Serve shell reused. |
| **Cloud Run `amjis-sidecar`** (Python; pyswisseph + **PyJHora**) | **KEEP shell · REALIGN internals** | PyJHora is already the engine (live `amjis-sidecar-00511-pz7`). Replace the **A1–A14 DAG writers** with the **L0–L5 asset writers + their retrieval tools** (parallel tool build). `min 1→0`. |
| **Cloud Run `amjis-mcp`** (MCP server) | **KEEP shell · REALIGN content** | Re-base tools onto the **three-tier taxonomy** over the new assets; the legacy embedded 573-MSR/corpus assets are **wiped + rebuilt** (teardown). `min 1→0`; keep concurrency 80; keep IAM-gated. |
| **Cloud Run `amjis-tracker`** | **DECOMMISSION** | Ephemeral program tracker; already retired in the Platform-Modernization close. Confirm gone. |
| **Cloud Run Job `marsys-build-pipeline-job`** (`build_chart.py`) | **KEEP mechanism · REALIGN content** | This is the per-chart **Gaṇita→Mīmāṃsā** build worker. Keep the Job mechanism + the SSE `build_events` rail + `dispatcher.py` cascade/resume; **replace the DAG/writers**; align progress granularity to the new asset set. |
| **Cloud Tasks `amjis-build-queue`** (+ `/api/build/task` OIDC) | **DECOMMISSION → direct trigger** | Per INFRASTRUCTURE_INVENTORY §6 ("avoid Cloud Tasks") + the standing build-task **401** residual: replace the queue dispatch with a **direct `jobs.run`** trigger from the API. Removes the OIDC-401 class entirely. *(Confirm in provisioning.)* |
| **Cloud SQL `amjis-postgres` + pgvector** | **KEEP instance · REALIGN schema** | **Fresh schema baseline** (drop legacy tables, new Brahma L0–L5 migration series); pgvector retained; **no HA** (research); CUD later. In-place wipe preferred over a new instance (keeps connection wiring + cost). |
| **Memorystore `amjis-cache`** (Redis) | **DECOMMISSION** | Per INFRASTRUCTURE_INVENTORY §11 (~$35+/mo floor): move caching (panchang per location×date) to **Postgres**; re-add Memorystore only if a hot cache is genuinely needed. |
| **Cloud Scheduler `build-reaper`** | **KEEP** | Still reaps stale build jobs; re-point endpoints if they change. |
| **GCS `madhav-marsys-build-artifacts`** | **KEEP · purge** | JSONL canonical artifacts + build state; purge legacy contents on teardown. |
| **GCS chat-attachments / chart-documents** | **KEEP** | Consume uploads + exports; reused unchanged. |
| **GCS tf-state bucket** | **KEEP** | Terraform backend. |
| **Vertex AI embeddings** (`text-multilingual-embedding-002`, 768-dim) | **KEEP (pending spike)** | Default retained; **final model gated on the C4 embedding spike** (Master Arch) before L0.4/L2 build — re-embed if the spike changes it. |
| **IaC `infra/iam`** | **KEEP · REALIGN** | Reuse SAs; prune/rename for Brahma; drop the tracker SA + (if Cloud Tasks dropped) `amjis-build-invoker`. |
| **IaC `infra/edge`** (HTTPS LB + CDN, `amjis.madhavstreamc.io`) | **DECOMMISSION** | Drop the global LB + CDN; serve via Cloud Run direct domain mapping (free HTTPS + custom domain). Resolved 2026-06-02 (Option A — cost-optimization supersedes the earlier KEEP). Re-addable if public traffic ever justifies it. |
| **IaC `infra/memorystore`** | **DECOMMISSION** | Remove the module with the Memorystore decision. |
| **IaC `infra/cloud_scheduler`** | **KEEP** | Reaper cron. |
| **IaC `infra/cloud_tasks`** | **DECOMMISSION** | Remove with the queue (direct-trigger decision). |
| **Secrets** | **KEEP most · DECOMMISSION 1 · hygiene** | Keep firebase/db/gemini/deepseek/sidecar/mcp secrets; **remove `ANTHROPIC_API_KEY`** (no Anthropic in prod); rename legacy-uppercase secrets per `secret_naming.md`; **rotate `amjis-db-password`** (flagged). |
| **DB migrations (90+)** | **REALIGN — fresh baseline** | New Brahma L0–L5 migration series; the legacy partition/operator queue (121/122/124, 140–153, ACC) is **moot under teardown**. |
| **CI/CD `deploy.yml`** | **KEEP · REALIGN** | Per-service deploy retained; update image refs/service names; keep NEXT_PUBLIC build-arg discipline; remove Cloud Tasks steps; add the BigQuery/bootstrap-job steps. |
| **Feature flags (`MARSYS_FLAG_*`)** | **REALIGN — prune** | Retire the legacy R9/R10/R11 chat-V2 flag thicket not relevant to Brahma. |
| **BigQuery** | **NEW** | None today; add BigQuery + Parquet-export for L5 cross-corpus OLAP (Master Arch C3). |
| **Brahmagyan/L0 + infra bootstrap** | **NEW** | A one-time admin Cloud Run Job that builds the global L0 assets + stands up infra (the native's one-time build). |

## §C — Why realign beats decommission (the reasoning)

1. **The shells are generic, not legacy-shaped.** `amjis-web`/`-sidecar`/`-mcp` are standard containers; the
   legacy-specific part is their *contents* (the A1–A14 DAG, the embedded corpus), which the teardown already
   targets. Rebuilding the containers buys nothing.
2. **The DB instance + buckets + edge + IAM are data-agnostic.** A fresh schema + purged buckets give a clean
   slate without re-provisioning a single resource or re-wiring connections.
3. **The four decommissions each have a positive reason** (cost / a known failure class / policy), not "it's
   legacy." Memorystore saves ~$35/mo; dropping Cloud Tasks removes the 401 class; the Anthropic secret is a
   policy violation; the tracker is already gone.
4. **It's cheaper and lower-risk** — no LB/cert re-issue, no IAM rebuild, no connection re-wiring — and it
   keeps the documented GCP cost envelope (~$55–95/mo) intact, minus the Memorystore line.

## §D — Sequencing into the provisioning session (what happens next, human-gated)

1. **Confirm the two open decisions** (§E) with the native.
2. **Execute the legacy teardown** (LEGACY_TEARDOWN_KILL_LIST, human-gated): wipe legacy data + build code +
   tools + drop legacy DB tables + purge build buckets; **keep the shells**.
3. **Realign config**: scale-to-zero the three services; decommission Memorystore + Cloud Tasks + the
   Anthropic secret + the memorystore/cloud_tasks Terraform modules; rotate the DB password.
4. **Provision the new**: BigQuery dataset + Parquet-export path; the one-time Brahmagyan/L0 + infra bootstrap
   Job.
5. **Apply the fresh Brahma migration baseline**, then begin the L0 (Brahmagyan) one-time build.

All of step 2–5 are **human-gated** (prod DB ops, deploys, secret rotation, teardown). Cowork stages; the
operator/Claude Code executes.

## §E — Open decisions for the provisioning discussion

1. **Cloud Tasks → direct Job trigger** — confirm replacing `amjis-build-queue` + `/api/build/task` OIDC with
   a direct `jobs.run` call (recommended; removes the 401 class). Or keep Cloud Tasks and fix the OIDC.
2. **Cloud SQL: wipe-in-place vs new instance** — recommended wipe-in-place (fresh schema on `amjis-postgres`,
   keeps wiring + cost). Confirm, or stand up a clean instance for a hard separation from legacy data.

(Lower-stakes, decided here but flag if you disagree: Memorystore decommissioned; Anthropic secret removed;
embedding model kept pending the C4 spike; domain unchanged unless you want a Brahma rebrand.)

---

*End of INFRA_RECONCILIATION v1.0 — Project Brahma — LOCKED 2026-06-02. Verdict: realign the ~85%-reusable GCP
footprint; decommission four items; add two. Per-component disposition decided; provisioning + teardown are
the next, human-gated session. Pairs with INFRASTRUCTURE_INVENTORY (target) + LEGACY_TEARDOWN_KILL_LIST (the
data/code/tools wipe).*

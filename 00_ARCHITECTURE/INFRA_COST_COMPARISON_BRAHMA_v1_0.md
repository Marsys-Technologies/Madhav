---
artifact: INFRA_COST_COMPARISON_BRAHMA_v1_0.md
canonical_id: INFRA_COST_COMPARISON_BRAHMA
version: 1.0
status: DRAFT (planning estimate for native review — Cowork)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-02
reads_with:
  - INFRA_RECONCILIATION_v1_0.md (the keep/drop dispositions costed here)
  - INFRASTRUCTURE_INVENTORY_v1_0.md (the documented GCP rates + target decisions)
sizing_assumptions:
  - region: asia-south1 (Mumbai)
  - scale: ~10 clients total, internal tool (native + family), low/bursty traffic — NOT high-traffic
  - quality bar: "must comfortably handle the load", not best-in-class HA
  - prices: approximate planning figures (GCP 2026, asia-south1); verify against the GCP Pricing
    Calculator before provisioning. Ranges reflect real billing variance (esp. Cloud Run idle vs active).
  - LLM API spend (Gemini/DeepSeek) is usage-based and tracked SEPARATELY from infrastructure.
---

# Infrastructure Cost Comparison — Current vs Cost-Optimized Brahma (~10 clients)

## §A — Headline

| Scenario | Estimated GCP infra | Driver |
|---|---|---|
| **Current (as deployed)** | **~$210–310 / month** | 3 always-on services (`min-instances=1`) + Memorystore + an external HTTPS Load Balancer |
| **Proposed Brahma (cost-optimized)** | **~$30–60 / month** | scale-to-zero everything, drop Memorystore, drop the Load Balancer, right-size Cloud SQL |
| **Saving** | **~$180–250 / month (≈ 75–85%)** | four levers below — and zero loss of capability for 10 internal users |

The four levers that do almost all the work: **(1)** put the three Cloud Run services on **scale-to-zero**
(`min-instances=0`); **(2)** **drop Memorystore** (cache in Postgres); **(3)** **drop the external Load
Balancer + CDN** and serve via Cloud Run's built-in HTTPS / direct domain mapping (free); **(4)**
**right-size Cloud SQL** to a shared-core instance. None of these hurt a 10-user internal tool.

## §B — Per-component comparison (cost at each level)

LLM API spend is excluded here (separate, usage-based). All figures $/month, approximate.

### Compute

| Component | Current config | Current $/mo | Proposed Brahma config | Proposed $/mo | Verdict |
|---|---|---|---|---|---|
| `amjis-web` (Next.js portal + consult) | Cloud Run, **min=1** (always warm), ~1 vCPU/512Mi | $25–45 | Cloud Run **min=0** (scale-to-zero); mostly free tier at this traffic | $0–5 | **KEEP · realign** |
| `amjis-sidecar` (Python + PyJHora engine) | Cloud Run, **min=1**, 2 vCPU/1Gi | $50–85 | Cloud Run **min=0**; warms on demand for builds | $0–5 | **KEEP shell · realign** |
| `amjis-mcp` (MCP server) | Cloud Run, **min=1**, ~1 vCPU/512Mi | $25–40 | Cloud Run **min=0** | $0–3 | **KEEP shell · realign** |
| `amjis-tracker` | (ephemeral; already retired) | $0 | — | $0 | **DROP** (gone) |
| Build worker (`build_chart.py`) | Cloud Run **Job**, triggered | $0–5 | Cloud Run **Job**, triggered (per-chart build + 1-time bootstrap) | $0–5 | **KEEP mechanism · realign** |
| **Compute subtotal** | | **$100–175** | | **$0–18** | |

### Data & cache

| Component | Current config | Current $/mo | Proposed Brahma config | Proposed $/mo | Verdict |
|---|---|---|---|---|---|
| Cloud SQL `amjis-postgres` + pgvector | 1 vCPU / 2 GB / 10 GB, no HA | $47 | **Right-size** to shared-core (e.g. db-g1-small ~1.7 GB) / 10 GB, no HA | $25–35 | **KEEP instance · right-size + fresh schema** |
| Memorystore `amjis-cache` (Redis) | Basic, 1 GB | $35–49 | **Dropped** — cache panchang per (location×date) in Postgres | $0 | **DROP** |
| BigQuery (L5 OLAP) | none | $0 | On-demand; <<1 TB/mo (free tier covers it) at 10 clients | ~$0 | **NEW** |
| **Data subtotal** | | **$82–96** | | **$25–35** | |

### Networking & edge

| Component | Current config | Current $/mo | Proposed Brahma config | Proposed $/mo | Verdict |
|---|---|---|---|---|---|
| External HTTPS LB + Cloud CDN (`infra/edge`) | global LB + managed cert + CDN | $18–25 | **Dropped** — serve via Cloud Run built-in HTTPS + direct domain mapping (free) | $0 | **DROP** (recommended) |
| Cloud Tasks `amjis-build-queue` | queue + OIDC handler | ~$0 (free tier) | **Dropped** — direct `jobs.run` trigger (also kills the 401 class) | $0 | **DROP** |
| Cloud Scheduler (build-reaper) | 1 cron job | ~$0 (3 free) | Keep (reaps stale builds) | ~$0 | **KEEP** |
| Egress | small | $2–5 | small | $1–3 | keep |
| **Networking subtotal** | | **$20–30** | | **$1–3** | |

### Storage, build, ops

| Component | Current config | Current $/mo | Proposed Brahma config | Proposed $/mo | Verdict |
|---|---|---|---|---|---|
| GCS (3 buckets: artifacts, attachments, documents) | small | $2–5 | same (purge legacy; reuse) | $2–4 | **KEEP** |
| Artifact Registry (container images) | image storage | $1–2 | same | $1–2 | **KEEP** |
| Vertex AI embeddings | usage-based | $1–3 | one-time corpus embed (~$3) + negligible ongoing | $0–2 | **KEEP** (pending C4 model spike) |
| CI/CD (Cloud Build / GH Actions) | per-build minutes | $0–5 | same | $0–3 | **KEEP · realign** |
| Cloud Logging / monitoring | default | $2–5 | trimmed | $0–2 | keep |
| Secret Manager | ~13 secrets | ~$1 | drop `ANTHROPIC_API_KEY`; rotate db pw | ~$1 | **KEEP · prune** |
| **Storage/ops subtotal** | | **$7–21** | | **$3–14** | |

### Totals

| | Current $/mo | Proposed Brahma $/mo |
|---|---|---|
| Compute | $100–175 | $0–18 |
| Data & cache | $82–96 | $25–35 |
| Networking & edge | $20–30 | $1–3 |
| Storage / build / ops | $7–21 | $3–14 |
| **GCP infra total** | **~$210–310** | **~$30–60** |
| LLM API (separate, usage-based) | ~$5–30 (family use) | ~$5–30 (family use) |
| **All-in** | **~$215–340** | **~$35–90** |

## §C — Why the Brahma number is so much lower (and still handles the load)

- **Scale-to-zero fits your traffic exactly.** With 10 internal users the services are idle the vast majority
  of the time. `min-instances=1` pays for 24/7 warm CPU you don't use; `min=0` pays only when someone is
  actually using it, and Cloud Run's monthly free tier (180k vCPU-s / 360k GiB-s / 2M requests) likely covers
  most of your real usage. The only cost is a few seconds of cold-start on the first request after idle —
  acceptable for an internal tool.
- **Memorystore is the worst $/value at this scale.** A 1 GB Redis floor (~$35–49/mo) to cache panchang for a
  handful of users is not worth it; Postgres caching per (location×date) is free and plenty fast here.
- **The Load Balancer is built for scale you don't have.** A global HTTPS LB + CDN (~$20/mo floor) makes
  sense for public traffic; for 10 users, Cloud Run's own HTTPS URL (or a free direct custom-domain mapping)
  is enough. Dropping it loses CDN caching you don't need.
- **Cloud SQL is the irreducible floor.** It's the one thing that benefits from staying warm (it's your live
  data). Right-sizing to a shared-core instance brings it to ~$25–35/mo — the single largest line in the
  Brahma budget, and appropriately so.

## §D — Optional extra cost-optimizations (flag if you want them)

- **Auto-stop Cloud SQL when idle.** For true family use you could *stop* the instance when not in use and
  pay only storage (~$0.22/GB-mo ≈ a few cents); start it on demand before a session. Drops the DB line to
  near-zero but adds a start-up delay + orchestration. (Most users keep it warm for convenience.)
- **Committed-Use Discount** on Cloud SQL once steady (~25% 1-yr) — small absolute saving at this size; skip
  until stable.
- **Single-region, single-AZ, no HA** — already assumed; correct for an internal tool.

## §E — What you are NOT giving up

At 10 internal users the proposed setup still: serves the full portal + consult, runs the complete
Gaṇita→Mīmāṃsā build per chart, serves all retrieval tools over MCP + portal, and keeps pgvector + Vertex
embeddings + BigQuery analytics. The only practical trade is a **cold-start delay** (seconds) on the first
hit after idle, and **no CDN edge-caching** — both irrelevant for internal use. HA, multi-region, and warm
fleets are deferred until (if ever) traffic justifies them.

---

*End of INFRA_COST_COMPARISON_BRAHMA v1.0 — planning estimate, 2026-06-02. Figures approximate (asia-south1,
2026); verify against the GCP Pricing Calculator at provisioning. Pairs with INFRA_RECONCILIATION (the
keep/drop decisions) + INFRASTRUCTURE_INVENTORY (rates + target).*

---
artifact: INFRASTRUCTURE_INVENTORY_v1_0.md
canonical_id: INFRASTRUCTURE_INVENTORY
version: 1.1
status: LIVING (infra decisions + cost estimate; settle remaining OPEN items, then execute)
authored_by: Claude (Cowork) 2026-06-02
changelog:
  - v1.1 (2026-06-02): Hosting decision REVERSED — stay on Google Cloud, cost-optimized
    scale-to-zero (Railway dropped on cost: GCP scale-to-zero ~$55–95/mo beats Railway ~$100–150
    at research-stage traffic; no shell migration needed). Mapped all items to GCP services; added
    §13 cost estimate.
purpose: >
  Running inventory of every infrastructure decision for the clean-slate rebuild + the cost
  estimate. Each item: decision / options / status. Settle remaining OPEN items in one pass, then
  execute.
---

# Infrastructure Inventory

Legend: **DECIDED** · **LEAN** · **OPEN**

## §1 — Hosting platform
- **Stay on Google Cloud (GCP), cost-optimized scale-to-zero.** — DECIDED (native, 2026-06-02;
  reversed the earlier Railway move after the cost comparison).
- Rationale: GCP Cloud Run scales to zero (cheaper at bursty research traffic + generous free
  tier); already on GCP; the clean slate lets us keep it simple and avoid prior complexity
  (Cloud Tasks auth / build-task 401, env-var merges, IAM sprawl). No shell migration needed.

## §2 — Compute services (Cloud Run, scale-to-zero)
- `amjis-web` — Next.js portal + consume loop (kept shell). `min-instances=0`. — LEAN.
- `amjis-mcp` — MCP server shell (kept). `min-instances=0`. — LEAN.
- `amjis-sidecar` / `compute` — Python (pyswisseph + engine). `min-instances=0`; warms on demand. — LEAN.
- **Cloud Run Jobs** for `worker` (ephemeris bootstrap, corpus embed, cache-warm, chart builds) —
  run only when triggered (cheapest for bursty/one-time work). — LEAN.
- Note: accept cold-start latency in exchange for scale-to-zero economics; set `min-instances=1`
  only on a service if cold start becomes a real UX problem. — OPEN (per-service tuning).

## §3 — Database
- **Cloud SQL for PostgreSQL + pgvector** — one DB for relational + embeddings. Start **no HA**
  (dev/research); enable HA later if needed. Fresh schema baseline (post-teardown). — LEAN.
- Consider **Committed-Use Discount** (25%/1-yr, ~52%/3-yr) once steady. — OPEN (later).

## §4 — Embeddings
- **Vertex AI text-embedding** (back in scope on GCP). One-time bulk corpus embed + per-query. — LEAN.
- (No managed-vs-self-host debate needed now that we're on GCP.)

## §5 — Object storage
- **GCS** for classical-text source files, user uploads, chart-document exports. — LEAN.
- Keep everything structured in Postgres; blobs in GCS only. Mind egress (~$0.12/GB). — NOTE.

## §6 — Background jobs / scheduling
- **Cloud Run Jobs** (triggered) + **Cloud Scheduler** (cron). — LEAN.
- Avoid Cloud Tasks unless genuinely needed; if used, fix the OIDC auth pattern that broke before. — NOTE.

## §7 — LLM providers (synthesis + agentic loop)
- API-based: default **Gemini** (Vertex / AI Studio); fallback **DeepSeek**; cheap-flash for
  non-critical. — LEAN.
- **No Anthropic models in any production path.** — DECIDED.

## §8 — CI/CD + deploy
- GitHub Actions → Cloud Run (existing pattern, simplified). Per-service deploy; NEXT_PUBLIC
  build-args discipline retained. — LEAN.

## §9 — Secrets / config
- GCP Secret Manager + Cloud Run env-vars; app-level runtime config table. Watch env-var **merge**
  behavior on redeploy (prior gotcha). — LEAN.

## §10 — Observability
- Keep telemetry/observatory tables (serve-shell) + Cloud Run logs/metrics + the app observatory. — LEAN.

## §11 — Caching
- Panchang cache per (location, date) **in Postgres** (avoid Memorystore — ~$35+/mo min). Optional
  event/query caches. Add Memorystore only if a hot cache is truly needed. — LEAN.

## §12 — Dependencies / sequencing
- GCP **build-specific** teardown (LEGACY_TEARDOWN): drop the build pipeline job + build buckets;
  **keep** the Cloud Run shells (no migration). — NOTE.

## §13 — Cost estimate (GCP cost-optimized, research stage)

GCP rates: Cloud SQL ~$30/vCPU + ~$5/GB-RAM + $0.22/GB storage; Cloud Run $0.000024/vCPU-s +
$0.0000025/GiB-s (free tier 180k vCPU-s / 360k GiB-s / 2M req per month); GCS ~$0.02/GB + ~$0.12/GB egress.

| Component | Config | ~$/month |
|---|---|---|
| Cloud SQL Postgres + pgvector | 1 vCPU / 2 GB / 10 GB, no HA | ~$47 |
| Cloud Run web + mcp + compute | scale-to-zero, low traffic (mostly free tier) | ~$5–30 |
| Cloud Run Jobs (worker/builds) | triggered only | ~$0–5 |
| Vertex AI embeddings | ~$3 one-time + negligible ongoing | ~$0 |
| GCS + egress | small | ~$2 |
| **GCP subtotal** | | **~$55–95/mo** |
| LLM API (Gemini/DeepSeek) | usage-based, separate | ~$20–100 (variable) |
| **All-in (research stage)** | | **~$75–195/mo** + ~$3 one-time** |

- One-time build spikes (ephemeris bootstrap, corpus embed) run on Cloud Run Jobs — minutes-to-hours, then idle.
- Scales with clients/corpus (Cloud SQL RAM for pgvector, Cloud Run on query volume); CUDs cut DB cost later.
- For reference, Railway equivalent was ~$100–150/mo (higher floor — bills idle services 24/7).

## §14 — Layer 1 storage (LOCKED 2026-06-02)

- **Representations:** JSONL canonical artifacts → GCS; Forensic MD → GCS; **Fact Store → Cloud SQL
  Postgres (primary queryable surface)** — a **typed, category-organized schema (~20 tables)** with
  relationships as first-class rows (no graph DB), per `LAYER_1_STORAGE_STRATEGY_v1_0.md`. **No RAG
  over L1 facts** — structured retrieval only; RAG reserved for L0 texts. JSONL is also the L2 rule
  engine's in-memory build input.
- **Dasha depth → SUKSHMA (SD), mandatory** — the volume driver.
- **Volume:** ~60–100k fact rows / chart / ayanamsha (~15–30 MB Postgres) + ~10–30 MB GCS artifacts.
- **Cost:** within §13 envelope at research scale (~few GB Postgres for ~20 clients × 2 ayanamshas);
  Cloud SQL storage ~$0.22/GB-mo grows linearly; per-chart build a few cents on a Cloud Run Job.
- **Scales** only at hundreds–thousands of clients (Postgres linear; CUDs cut DB cost later).

## §15 — Layer 2 (Chart Intelligence) infrastructure

**No new services** — L2 reuses the L1/L0 footprint. Additions only.

- **Compute:** an **L2 step on the existing Cloud Run Job** (runs after the L1 build, per chart ×
  ayanamsha). Work = rule engine (apply the L0 Rule Base to the chart's L1 facts) + edge/lens/index
  derivation + signal embedding. CPU-bound, minutes, scale-to-zero. ~**a few cents per chart build**
  (grows with rule-base size, still batch/bounded).
- **Storage (Cloud SQL Postgres + pgvector):** the L2 tables (`signals`, `signal_edges`,
  `domain_linkages`, `resonance_elements`, `signal_concordance`, `signal_activation`,
  `negative_space`, `contradictions`) **+ `signal_embeddings` in pgvector**. pgvector is already
  provisioned (L0 texts); L2 adds **signal vectors to the same store** — no new vector DB.
- **Embeddings (Vertex AI):** embed ~hundreds–thousands of signals per chart × ayanamsha — already
  the L0 embedding provider; **~$0.005 per chart** (negligible).

**Volume per chart × ayanamsha:** ~hundreds–low-thousands of signals; a few thousand edges; small
lens/index/ledger tables; one embedding per signal → **~5–15 MB Postgres** (far smaller than L1 — no
dasha-row explosion; embeddings are the main addition).

**Cost (research scale, ~20 clients × 2 ayanamshas):** ~0.4–0.6 GB additional Postgres (incl. ~40k
signal vectors) → **~$1–2/mo incremental** Cloud SQL storage + a few cents/chart build. **Within the
existing GCP envelope (§13).** The L2 signal vectors add modest pgvector HNSW RAM; revisit only at
hundreds–thousands of clients.

---

*LIVING — append/refine as decisions firm up; settle OPEN items in one pass, then execute.*

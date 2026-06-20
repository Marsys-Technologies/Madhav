---
artifact: CLAUDECODE_BRIEF_L3_K0_SERVICE_ASSET_TYPE_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_K0_SERVICE_ASSET_TYPE
brief_for: ka_* SERVICE-ASSET TYPE — the enabling infrastructure prerequisite (L3 Kāla, wave K0)
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.3 (service-asset model A+C), I-2 (service-asset registration), §14.5 (locked set)]
version: 1.0
status: AUTHORED — ready for Claude Code (Antigravity) execution
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: Claude Code in Google Antigravity IDE (NOT the CLI) — all git/terminal commands embedded for paste
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K0
  blocked_by: []          # none — this is the foundational gate
  blocks: [ka_graha_sancara, ka_dasha_kala, ka_gochara, ka_muhurta_seva]  # all SERVICE assets need the service-asset type
  may_touch:
    - platform/supabase/migrations/<next>_service_asset_type.sql   # NEW
    - platform/scripts/seed/asset_registry_seed.ts                 # type + sample row only
    - platform/src/app/api/cockpit/**                              # stats/registry route: tolerate service rows
    - platform/src/components/cockpit/**                           # render service node health model
    - platform/python-sidecar/pipeline/orchestrator/**             # service self-test path ONLY (no contract change)
  parallel_safe_with: []  # K0 runs ALONE first (everything depends on it); no parallel peer
---

# CLAUDECODE BRIEF — L3 Kāla K0: The SERVICE-ASSET TYPE (enabling infrastructure)

> **⚠️ SCOPE CORRECTION (branch audit 2026-06-21) — EXTEND, don't build from scratch.** Migration
> `202_asset_registry_service_support.sql` is ALREADY ON MAIN and provides ~60% of this: `asset_type
> ('data','service')`, `storage_type='service'`, `layer_name`, `layer_index`, `provides_apis jsonb`,
> `health_probe jsonb`, `catalog_status (CURRENT/DRAFT)`, with all rows backfilled. **K0 is RE-SCOPED to
> EXTEND mig 202, not recreate it:** (1) reconcile `asset_type` → the brief's `asset_kind` AND add the
> `'artifact'` value (mig 202 has only data/service); (2) add the four STRUCTURED service-health columns
> (`service_health` enum, `last_invoked_at`, `last_selftest_at`, `selftest_detail`) — OR formalize them out
> of the existing `health_probe jsonb`; (3) the cockpit + orchestrator self-test work in §7/§4 stands.
> Read mig 202 FIRST; build the delta. The §5 migration below is the DELTA over mig 202, not a fresh table.

## §0 — Why this brief exists FIRST (the gate)
L3 Kāla introduces a NEW kind of asset the platform has never had: a **SERVICE** — a callable engine
with **no stored rows** (ephemeris-at-T, daśā-eligibility, transit-search, panchāṅga/muhūrta). The
founding L3 principle is **"timing = SERVICES, not DATA"** (plan §2): you cannot pre-store the chart
state at every future instant, so these are computed on demand. But the entire existing pipeline —
the cockpit, the radial-constellation DAG, the orchestrator `WriterBase` contract, idempotency
(delete-then-insert), and `asset_registry.count_sql` — assumes a **stored row-asset** with a row
count. A service has no row count and no target table. **Until the platform can register and render a
service-asset, none of the four L3 service assets can be onboarded.** This brief builds that
capability. It is wave K0 and it BLOCKS ka_graha_sancara, ka_dasha_kala, ka_gochara, ka_muhurta_seva.

## §1 — Scope (may_touch / must_not_touch)
**may_touch:**
- `asset_registry` schema (add `asset_kind` + service-health columns) via a NEW migration.
- `platform/scripts/seed/asset_registry_seed.ts` (the seed type + the service rows — service rows
  added by the per-service briefs, not here; here only the TYPE + schema).
- The cockpit stats/registry API route that reads `count_sql` (make it tolerate service-kind rows).
- The cockpit DAG/asset rendering components (render a service node with a health model).
- The orchestrator's asset-runner ONLY to the extent of recognizing a service-kind asset and
  invoking its self-test instead of a row-writer (see §4 — this must NOT change the FROZEN writer
  contract for normal assets).

**must_not_touch:**
- The FROZEN orchestrator `WriterBase` contract for normal (row) assets (`run(ctx)` / `plan_substeps`
  + `run_substep`; `ctx.db_conn` never committed by the writer; no `_telemetry`; `WriterResult`).
  See `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2`. **If a service seems to require a change to that
  contract → STOP and raise with the native.**
- Any L1/L2 sealed asset, table, or writer.
- Any other layer's assets.

## §2 — Background the executor needs (do not assume)
- **Plan §5.3 RESOLUTION (native-ratified):** the service-asset model is **A + C, both in-layer.**
  Services register as first-class IN-LAYER `ka_*` SERVICE-assets with a **service-health model**
  (registered / last-invoked / self-test pass) and **no `count_sql`**. Separately, ONE artifact-asset
  (`ka_kalasutra`) stores rows normally. This brief builds the SERVICE side only.
- **Plan I-2 (the open design this brief closes):** *how does a service-asset register vs. the frozen
  orchestrator writer contract?* — does a service get a no-op self-testing writer, or a separate
  registry path? **This brief DECIDES it (see §4) and implements it.**
- **The existing trap (plan §N.4 "cockpit truth"):** the stats route reads `asset_registry.count_sql`,
  NOT `asset_throughput`. A service row with a NULL `count_sql` must not crash that route.

## §3 — The deliverable (what "done" means)
A service-kind asset can be (a) registered in `asset_registry`, (b) rendered in the cockpit with a
health model instead of a row count, (c) invoked by the orchestrator to run its self-test (not a row
write), and (d) reported as healthy/unhealthy — all WITHOUT touching the frozen writer contract for
normal assets. Demonstrated end-to-end on ONE throwaway sample service registered behind a flag, then
removed (the real services come in their own briefs).

## §4 — THE DESIGN DECISION (I-2 closed): "self-testing no-op writer" path
Two options were considered:
- **(rejected) a separate service registry** — a parallel table/path. Rejected: it forks the build
  state machine, duplicates cockpit logic, and risks drift (the corpus repeatedly punishes dual
  registries — GA.1).
- **(CHOSEN) a service is a `@register`'d unit whose `run(ctx)` performs a SELF-TEST, not a row
  write.** It conforms to the frozen `WriterBase` contract shape (so the orchestrator drives it with
  zero contract change), but instead of inserting rows it: invokes the service's core function on a
  canonical probe input, asserts the output is well-typed and plausible, and returns a `WriterResult`
  whose status reflects pass/fail. It writes NO domain rows. It records its health in the
  service-health columns (§5) via the orchestrator's normal build-state write (the orchestrator
  remains the sole build-state writer — §N.2).

**Why this is contract-safe:** the frozen contract says the writer runs on `ctx.db_conn` and never
commits it, does not write `asset_throughput` itself, and returns a `WriterResult`. A self-test that
reads/probes and returns a result satisfies all of that. The orchestrator is unchanged; only the
*asset's* `run` body differs — which is allowed (writers already vary their bodies).

## §5 — Schema changes (the migration)
Add to `asset_registry` (new migration — get the next number from the migrations dir; do NOT hardcode):
- `asset_kind text NOT NULL DEFAULT 'data'` with `CHECK (asset_kind IN ('data','service','artifact'))`.
  `data` = existing row-assets; `service` = callable, no rows; `artifact` = stored L3 product (same as
  `data` for storage but tagged for clarity). Backfill all existing rows to `'data'`.
- `service_health text NULL CHECK (service_health IN ('healthy','degraded','unhealthy','unknown'))`.
- `last_invoked_at timestamptz NULL`.
- `last_selftest_at timestamptz NULL`.
- `selftest_detail jsonb NULL` (the probe result summary).
- Make `count_sql` and `target_table` **NULLABLE** if not already (services have neither). Verify the
  current NOT NULL constraints first; relax only if present.

**Idempotency:** `ADD COLUMN IF NOT EXISTS`; the CHECK added separately guarded. Migration is
forward-only and surgical (plan §N.4: never deploy.yml-auto or bulk migrate.ts).

## §6 — Seed type changes
In `asset_registry_seed.ts`, extend the asset TypeScript type to include `asset_kind` and allow
`count_sql: null` / `target_table: null` for service rows. Do NOT add the real service rows here —
they come in each service's own brief. Add ONE sample service row behind a clearly-named throwaway id
(e.g. `ka__selftest_probe`) for the §8 demonstration, to be removed at the end.

## §7 — Cockpit changes
- **Stats/registry API route:** where it computes a count via `count_sql`, branch on `asset_kind`:
  for `service`, skip the count query entirely and return the service-health fields instead. A NULL
  `count_sql` must never reach the query executor. (Plan §N.4 trap.)
- **DAG / asset rendering:** render a `service` node with a **health badge** (healthy/degraded/
  unhealthy/unknown) + a "last invoked" timestamp instead of a row count + target_floor bar. Reuse the
  existing node styling; only swap the metric region. Keep the radial-constellation layout untouched
  (plan memory: deterministic layout, asset_id seeds jitter).
- Date formatting: dd-MMM-yyyy via the central formatter (plan memory: cockpit date convention).

## §8 — Acceptance criteria [each tagged with how to verify, against PROD]
> Per plan §9 PROD-VERIFY (the Brahma V1.3 lesson): ACs verify against PROD via the Cloud SQL Auth
> Proxy, not a worktree DB. Data-plane is always prod (plan memory: localhost-codeplane-prod-dataplane).

1. **[verify: psql_prod]** `asset_registry` has `asset_kind`, `service_health`, `last_invoked_at`,
   `last_selftest_at`, `selftest_detail`; all pre-existing rows backfilled to `asset_kind='data'`.
2. **[verify: psql_prod]** a `service`-kind row with `count_sql IS NULL` and `target_table IS NULL`
   inserts without constraint error.
3. **[verify: curl_prod]** the cockpit stats/registry route returns the sample service row WITHOUT
   error and with health fields populated (no count attempted).
4. **[verify: Chrome MCP on the cockpit URL]** the sample service node renders with a health badge +
   last-invoked, NOT a row count. Screenshot it.
5. **[verify: orchestrator run]** invoking the sample service's self-test via the orchestrator runs
   `run(ctx)`, writes NO domain rows, updates `service_health` + `last_selftest_at`, and returns a
   `WriterResult`. Confirm `grep` shows the service writer contains NO `ctx.db_conn.commit()` /
   `.rollback()` (plan §9 / L2 Vimarśaka-RED lesson).
6. **[verify: tests]** unit tests: the stats route with a NULL-count_sql service row; the asset_kind
   CHECK; the self-test writer's no-row behavior. All green.
7. **[cleanup]** the throwaway `ka__selftest_probe` row + sample writer are REMOVED before close
   (the real services arrive in their own briefs).

> **Branch/merge policy:** this is a Madhav (not Brahma) change → the prior human-gated default
> applies (plan memory [[feedback-two-stream-branch-policy]]): own this branch, open a PR to main, do
> NOT self-merge or auto-deploy without native review. (Brahma's full-autonomous mode does NOT apply here.)

## §9 — Embedded commands (Antigravity — paste-ready)
```bash
# Branch (per plan §9 branch-isolation)
git checkout main && git pull
git checkout -b feature/l3-k0-service-asset-type

# Find the next migration number (do NOT hardcode)
ls platform/supabase/migrations | sort -n | tail -5

# After authoring: apply surgically against PROD via the proxy (NOT deploy.yml-auto, NOT bulk migrate.ts)
bash platform/scripts/start_db_proxy.sh   # port 5433
# psql "host=127.0.0.1 port=5433 ..." -f platform/supabase/migrations/<N>_service_asset_type.sql

# Tests
cd platform && npm test -- asset_kind service_health   # or the test file paths you add

# Self-test contract check (must return ZERO hits)
grep -rn "\.commit()\|\.rollback()" platform/python-sidecar/pipeline/orchestrator/ | grep -i service
```

## §10 — Definition of done (close checklist)
- [ ] Migration applied to PROD; §8 AC1–AC2 pass.
- [ ] Cockpit renders a service node (AC3–AC4) — screenshot attached.
- [ ] Orchestrator self-test path works, no domain rows, no commit/rollback in the writer (AC5).
- [ ] Tests green (AC6).
- [ ] Throwaway sample removed (AC7).
- [ ] I-2 marked RESOLVED in the campaign plan §10 register with the chosen design (self-testing no-op
      writer).
- [ ] PR `feature/l3-k0-service-asset-type` → main opened with the AC evidence.

---

## §11 — VALUE ADDED BY THIS BRIEF (beyond the baseline placeholder)
1. **Unblocks the entire services half of L3** — without this, the 4 SERVICE assets (the temporal
   engines that ARE the layer) literally cannot be registered. This is the keystone of the §5.3 A+C model.
2. **Closes I-2 with a contract-SAFE decision** — the self-testing no-op writer means the platform
   gains a service-asset kind with **zero change to the FROZEN orchestrator contract**, avoiding the
   single biggest risk in the whole layer (a contract change → the L2 Vimarśaka-RED class of failure).
3. **Eliminates a latent cockpit crash** — formalizes that a NULL `count_sql` must never reach the
   query executor, hardening the §N.4 "cockpit truth" trap for every future service.
4. **Gives services first-class observability** — a health model (healthy/degraded/unhealthy + last
   invoked + self-test detail) so a stale or broken temporal engine is VISIBLE in the cockpit, not a
   silent failure discovered downstream.
5. **Establishes the data/service/artifact taxonomy in the registry** — making the §5.10
   precompute/on-demand boundary machine-enforced (a service can never accidentally be treated as a
   precomputed table), which is exactly the boundary the native's panchāṅga correction protects.

---

*End of CLAUDECODE_BRIEF_L3_K0_SERVICE_ASSET_TYPE v1.0. This is the enabling-infrastructure gate for
L3 Kāla's service assets. It closes plan item I-2 with a frozen-contract-safe design and unblocks
ka_graha_sancara / ka_dasha_kala / ka_gochara / ka_muhurta_seva.*

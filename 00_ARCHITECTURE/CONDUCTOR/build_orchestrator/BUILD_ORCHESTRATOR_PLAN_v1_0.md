---
artifact: BUILD_ORCHESTRATOR_PLAN_v1_0.md
document: Build Orchestrator — Multi-Batch Plan
status: PROPOSED (Cowork-authored 2026-05-29; awaiting native sign-off + Batch 0 kickoff)
version: 1.0
date: 2026-05-29
authored_by: Claude (Cowork) — informed by DETERMINISTIC_REBUILD_SCOPING_v1_0.md + native Round 1–4 decisions
intended_for: The Conductor + Claude Code sub-agents that will execute Batches 0–5
prerequisite_reading:
  - 00_ARCHITECTURE/DETERMINISTIC_REBUILD_SCOPING_v1_0.md (this plan's parent)
  - 00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md
  - 00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md
  - platform/python-sidecar/natal_engine/__init__.py (compute_chart entrypoint)
  - platform/python-sidecar/natal_engine/l25_builder/build.py
  - platform/python-sidecar/pipeline/main.py (the "wrongly connected" pipeline being replaced)
  - platform/src/app/clients/[id]/build/page.tsx + BuildActionPanel.tsx (the chat shell being replaced)
  - platform/src/app/api/build/{start,task,events/[buildId]}/route.ts (the SSE substrate being kept)
self_containment: This plan is the single source of truth for the workstream. Per-batch CLAUDECODE_BRIEF.md files at project root carry the executable scope for each Claude Code session; this plan covers all batches end-to-end.
---

# Build Orchestrator — Multi-Batch Plan

> **Read order:** §0 → §1 (mission + decisions) → §2 (asset DAG) → §3 (schema) → §4 (engine wiring) → §5 (frontend) → §6 (notifications) → §7 (acceptance criteria) → §8 (out of scope) → §9 (batch plan) → §10 (references).

---

## §0 — One-paragraph mission

Replace the "wrongly connected" build trigger (UI chat shell + Cloud Run Job running the YAML-extraction pipeline) with a **per-chart deterministic build orchestrator** that runs `natal_engine.compute_chart()` + `l25_builder.build()` end-to-end against the guest's chart, emits per-asset progress as `build_events` SSE rows, and renders the build as a stupendous animated constellation on a natal-wheel background. The orchestrator runs autonomously in dependency order; the guest sees one button (Build / Rebuild), no surgical per-asset rebuild surface; failures halt the whole build after N retries; the visualization is the centerpiece of the per-chart `/build` page.

---

## §1 — Native decisions (Rounds 1–4, captured 2026-05-29)

| # | Decision | Native's answer |
|---|---|---|
| 1.1 | Per-chart assets in DAG | L1 FORENSIC render, chart_facts, T1 structural, MSR, CDLM, CGM, RM, UCN digest, panchanga, dashas, vargas, sensitive_points, sade_sati |
| 1.2 | Out of per-chart orchestrator | Ephemeris, eclipses, retrogrades, classical RAG (BPHS+Jaimini+KP+Tajaka) — these are global |
| 1.3 | Rebuild policy | Whole-system only. No surgical per-asset rebuild surface. |
| 1.4 | Failure policy | Retry N times, then halt the full build. |
| 1.5 | Visual direction | Animated DAG, **constellation layout** — nodes positioned by zodiac/houses; build wave sweeps the chart. |
| 2.1 | New-client form fields | Full name, gender, birth date, birth time, birth place (autocompletes to lat/lon/tz), optional ayanamsha override (collapsed). |
| 2.2 | UI placement | **Replace** existing `BuildChat` shell entirely. Orchestrator IS the build page. Chat moves to `/consume` (already there). |
| 2.3 | Duration expectation | Long (10–60 min). Resumable; in-app surfacing of in-progress builds. |
| 3.1 | Build history | **Full audit trail**: every build = one `builds` row with engine_version + status + timestamps + log URI. |
| 3.2 | Cancellation | Yes with confirmation: in-progress asset completes, remaining cancelled, partial state preserved. |
| 3.3 | Node click | Detail panel: status, logs, output preview, last-computed timestamp, engine version. |
| 3.4 | Engine version drift | **Pinned-until-rebuild** + visible drift indicator in detail panel (shows current vs latest engine). |
| 4.1 | Notifications | In-app dashboard ("Builds in progress" card) + post-visit toast on completion. **No email.** **No push.** |
| 4.2 | Concurrency | No per-guest limit. Cloud Tasks handles ordering. |
| 4.3 | Must-not-touch | None declared. (Workstream may touch any surface, subject to "don't break adjacencies" gates in §7.) |

---

## §2 — Per-chart asset DAG (dependency edges)

The orchestrator walks this DAG topologically. Same `chart_id` + same `engine_version` + same `ayanamsha_id` + same `salience_formula_version` ⇒ byte-identical output (deterministic contract).

```
                     ┌─────────────────────────────────────────┐
                     │  ENGINE INVOCATION (natal_engine)       │
                     │  inputs: birth_date+time+place+         │
                     │          ayanamsha+chart_id             │
                     └─────────────────────┬───────────────────┘
                                           │
                                           ▼
                          ┌─────────────────────────────────┐
                          │ A1. chart_output JSONL          │
                          │ (one line, schema-validated)    │
                          │ → gs://amjis-build-artifacts/   │
                          │     chart/{chart_id}/{build_id}/│
                          │     chart_output.jsonl          │
                          └────────┬────────────────────────┘
                                   │
            ┌──────────────┬───────┼───────┬────────────┬──────────────┐
            ▼              ▼       ▼       ▼            ▼              ▼
   ┌─────────────┐ ┌──────────┐ ┌─────┐ ┌────────┐ ┌──────────┐ ┌──────────────────┐
   │ A2. forensic│ │ A3. chart│ │ A4. │ │ A5.    │ │ A6.      │ │ A7. sensitive_   │
   │  _render    │ │  _facts  │ │panch│ │ dashas │ │ vargas   │ │  points          │
   │ (L1 md)     │ │ (rows)   │ │anga │ │ (rows) │ │ (D1..D60)│ │  (ASC+gulika+    │
   │             │ │          │ │     │ │        │ │  rows)   │ │   upagrahas...)  │
   └─────────────┘ └────┬─────┘ └─────┘ └────────┘ └──────────┘ └────┬─────────────┘
                        │                                            │
                        ▼                                            │
                ┌────────────────┐                                   │
                │ A8. T1 struct- │                                   │
                │  ural facts    │                                   │
                │  (aspect mtx,  │                                   │
                │  dispositors,  │                                   │
                │  shadbala,     │                                   │
                │  ashtakavarga, │                                   │
                │  yogas)        │                                   │
                └────┬───────────┘                                   │
                     │                                               │
                     └──────────────┬────────────────────────────────┘
                                    │
                                    ▼  (T1 + chart_facts + sensitive_points required for L2.5)
                            ┌──────────────┐
                            │ A9. MSR      │
                            │  (every      │
                            │   signal,    │
                            │   no thresh.)│
                            └────┬─────────┘
                                 │
            ┌─────────────┬──────┼──────┬──────────────┐
            ▼             ▼      ▼      ▼              ▼
        ┌────────┐  ┌───────┐ ┌─────┐ ┌─────┐  ┌───────────────┐
        │ A10.   │  │ A11.  │ │A12. │ │A13. │  │ A14. sade_    │
        │ CDLM   │  │ CGM   │ │ RM  │ │ UCN │  │  sati (uses   │
        │ (links)│  │(graph)│ │     │ │ dig │  │  natal Moon   │
        │        │  │       │ │     │ │ est │  │  from A3+A7)  │
        └────────┘  └───────┘ └─────┘ └─────┘  └───────────────┘
                                       │
                                       ▼ (UCN consumes ranked MSR + CGM signature)
                                FINALIZE
                                pyramid_layers ← all rows "complete"
                                builds.status ← "complete"
                                emit build_events finalize-complete
```

**Total nodes: 14** (1 engine invocation + 13 asset writers + finalize).

**Dependency invariants:**
- A1 (engine) MUST complete before any A* downstream.
- A8 (T1 structural) requires A3 (chart_facts) + A7 (sensitive_points).
- A9 (MSR) requires A3 + A7 + A8.
- A10–A13 (CDLM, CGM, RM, UCN) require A9.
- A14 (sade_sati) requires A3 + A7 (natal Moon sign).
- A2 (forensic_render), A4 (panchanga), A5 (dashas), A6 (vargas) are parallelizable after A1.

Build engine emits `build_events` rows tagged `asset_id ∈ {a1_engine, a2_forensic_render, ...}` with stages `compute → persist → verify → commit`. Two-level UX (already wired by the existing BuildActionPanel pattern): outer = "asset M of N"; inner = "stage: X".

---

## §3 — Database schema

### §3.1 — New tables (migrations 124+)

**Migration `124_builds.sql`:**
```sql
CREATE TABLE IF NOT EXISTS builds (
  build_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id              UUID NOT NULL REFERENCES charts(chart_id) ON DELETE CASCADE,
  triggered_by_uid      TEXT NOT NULL,
  triggered_by_role     TEXT NOT NULL CHECK (triggered_by_role IN ('super_admin', 'guest')),
  engine_version        TEXT NOT NULL,
  ayanamsha_id          TEXT NOT NULL,
  salience_formula_ver  TEXT NOT NULL,
  status                TEXT NOT NULL CHECK (status IN ('queued','running','complete','failed','cancelled','cancelling')),
  queued_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at            TIMESTAMPTZ,
  finished_at           TIMESTAMPTZ,
  cancelled_at          TIMESTAMPTZ,
  failed_at             TIMESTAMPTZ,
  error_summary         TEXT,
  log_gcs_uri           TEXT,
  asset_artifacts_uri   TEXT,  -- gs://amjis-build-artifacts/chart/{chart_id}/{build_id}/
  cloud_run_job_exec    TEXT   -- Cloud Run Job execution name for trace
);
CREATE INDEX builds_chart_idx ON builds (chart_id, queued_at DESC);
CREATE INDEX builds_status_idx ON builds (status) WHERE status IN ('queued','running','cancelling');
```

**Migration `125_build_steps.sql`:**
```sql
CREATE TABLE IF NOT EXISTS build_steps (
  build_step_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  build_id               UUID NOT NULL REFERENCES builds(build_id) ON DELETE CASCADE,
  asset_id               TEXT NOT NULL,  -- a1_engine, a2_forensic_render, ...
  asset_label            TEXT NOT NULL,  -- "Engine compute_chart", "FORENSIC L1 render", ...
  dependency_satisfied_at TIMESTAMPTZ,
  started_at             TIMESTAMPTZ,
  finished_at            TIMESTAMPTZ,
  status                 TEXT NOT NULL CHECK (status IN ('pending','running','complete','failed','cancelled','skipped')),
  retry_count            INT NOT NULL DEFAULT 0,
  output_gcs_uri         TEXT,
  error_summary          TEXT,
  rows_written           INT  -- for chart_facts, MSR, CGM, etc.
);
CREATE INDEX build_steps_build_idx ON build_steps (build_id, asset_id);
```

**Migration `126_engine_versions.sql`:**
```sql
CREATE TABLE IF NOT EXISTS engine_versions (
  engine_version    TEXT PRIMARY KEY,
  status            TEXT NOT NULL CHECK (status IN ('current','superseded','deprecated')),
  promoted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  jh_parity_sha     TEXT NOT NULL,
  release_notes_uri TEXT
);
-- Seed: insert ('natal_engine/0.2.0-jh-parity', 'current', now(), <sha>, NULL)
```

### §3.2 — Existing tables that REMAIN untouched
- `build_events` (mig 118) — kept verbatim. Both the Python build script + the orchestrator API write here.
- `pyramid_layers` — kept verbatim. New build script updates rows here when each asset completes.
- `charts` (with `chart_id` UUID PK from mig 086_0) — registry. New-client form INSERTs here.
- `chart_facts`, `l25_msr_signals`, etc. — already chart_id-keyed (migs 086–089). Build script populates these.

### §3.3 — Migration discipline
- Authored under `platform/migrations/` (canonical per `MIGRATION_DIRECTORY_POLICY_v1_0.md`).
- Next available: 124 (last applied was 123 per CURRENT_STATE).
- Staging-mirror pattern per Platform Modernization v1.2 lessons: each migration includes `*_staging` mirror with shape guards + idempotent `IF NOT EXISTS`.

---

## §4 — Engine wiring (the "wrongly connected" fix)

### §4.1 — Replace the Cloud Run Job command

**Current** (`marsys-build-pipeline-job` Cloud Run Job): runs `python -m pipeline.main` → reads VALIDATED_ASSET_REGISTRY → YAML extraction → writes RAG chunks + structured assets.

**New**: runs `python -m pipeline.build_chart --build-id <id> --chart-id <id>` → invokes `natal_engine.compute_chart()` → walks the §2 DAG → emits `build_events` per asset → writes per-chart rows with `chart_id` populated.

### §4.2 — New Python entrypoint: `pipeline/build_chart.py`

```python
# pipeline/build_chart.py — pseudocode
def main(build_id: str, chart_id: str) -> None:
    # 1. Load chart from charts table (birth_date, birth_time, lat, lon, tz_offset, ayanamsha_id)
    chart_inputs = load_chart_inputs(chart_id)

    # 2. Update builds.status = 'running', started_at = now()
    mark_build_started(build_id)

    # 3. Walk the DAG topologically (§2). For each asset:
    for asset in DAG_ORDER:
        emit_build_event(build_id, asset.id, stage='compute', status='started')
        if asset.id == 'a1_engine':
            chart_output = natal_engine.compute_chart(chart_inputs, ENGINE_VERSION, AYANAMSHA_ID)
            persist_jsonl_to_gcs(chart_output, build_id, chart_id)
        elif asset.id == 'a2_forensic_render':
            render_forensic_md_from_jsonl(chart_output, chart_id)
        elif asset.id == 'a3_chart_facts':
            rows = l25_builder.build_chart_facts(chart_output, chart_id)
            chart_facts_writer.upsert(rows, build_id=build_id)
        # ... a4..a14 similarly
        emit_build_event(build_id, asset.id, stage='commit', status='complete', rows=N)
        update_pyramid_layer(chart_id, asset.layer, asset.sublayer, status='complete')

    # 4. Finalize
    mark_build_complete(build_id)
    emit_build_event(build_id, 'orchestrator', stage='finalize', status='complete')
```

**Determinism contract:** every asset writer is pure — same chart_output + same chart_id ⇒ byte-identical rows. The orchestrator does NOT call any model.

### §4.3 — Failure + retry
Each asset wrapped in retry-with-exponential-backoff (3 attempts × 2s/4s/8s). On 3rd failure: emit `failed` event, mark `builds.status = 'failed'`, write `error_summary`, terminate. Downstream assets do NOT execute. This is the §1.4 "retry N then halt" policy.

### §4.4 — Cancellation
- `POST /api/build/cancel/{build_id}` (new) → marks `builds.status = 'cancelling'`.
- Python script polls `builds.status` between each asset; if `cancelling`, finishes current asset (don't corrupt mid-write), then sets `status = 'cancelled'`, emits `cancelled` event, terminates.

### §4.5 — Concurrency
No per-guest limit. Cloud Tasks queue handles arrival ordering. Cloud Run Job concurrency cap = the queue's max-dispatches-per-second (already configured). Concurrent builds on different `chart_id` are safe by construction (per-chart partitioned writes).

---

## §5 — Frontend: the constellation orchestrator

### §5.1 — Page surface

**Replace** `platform/src/app/clients/[id]/build/page.tsx` (the `BuildChat` shell) entirely. The new page is the constellation orchestrator. Chat surface lives at `/clients/[id]/consume` (already there, shipped R11.B).

**Route:** `/clients/[id]/build` (unchanged URL).

**Top-level shell:** centered hero canvas (the constellation) + bottom-right command palette (Build / Rebuild / Cancel) + top-right meta (engine version, last build timestamp).

### §5.2 — Constellation visualization

**Canvas:** SVG 800×800, responsive (scales to viewport). Animation via Framer Motion (already in the stack).

**Background:** classical natal wheel.
- **Inner circle** (radius 0): center mark.
- **Inner ring** (radius 40–120): 12 house wedges (Sripati equal-arc thirds from ASC/IC/DSC/MC anchors). Labels 1–12.
- **Middle ring** (radius 120–200): 12 zodiac signs (Aries → Pisces, drawn from natal ASC longitude).
- **Outer ring** (radius 200–280): 27 nakshatras (subdivisions of the zodiac).

**Asset node placement** (the constellation):

| Asset | Position | Visual |
|---|---|---|
| A1 engine | Center (chart birth point) | Pulsing orb; pulse speed = build progress |
| A2 forensic_render | Below wheel, captioned | Scroll icon |
| A3 chart_facts | 9 sub-nodes at 9 grahas' natal house positions | Each lights up as its planet's facts persist |
| A4 panchanga | Top of wheel, above natal Sun | Sun-moon-tithi icon |
| A5 dashas | Clock hand sweeping the wheel | Animated rotation; speed reflects timeline |
| A6 vargas | Outer-ring rosette (16 small wheels around the main wheel) | Each varga wheel lights up as it builds |
| A7 sensitive_points | Cluster at ASC + Gulika + MC | Diamond markers |
| A8 T1 structural | Aspect lines drawn between planets (5/7/9/etc.) | Lines animate in sequence; dispositor arrows last |
| A9 MSR | Star-field around the wheel | Stars pop in one-by-one as signals enumerate |
| A10 CDLM | Lower-left corner: 9×9 grid | Grid cells fill in as links compute |
| A11 CGM | Graph overlay on wheel (node-edge) | Edges trace between planet positions |
| A12 RM | Radial spokes from center | Spokes extend outward as resonances bind |
| A13 UCN digest | Upper caption: "argument of the chart" | Rendered as a single luminous sentence summarising the dominant configurations |
| A14 sade_sati | Saturn-Moon connecting line + 7.5-year arc | Saturn vector grows as cycles compute |

**Build wave animation:** starts at the engine center, propagates outward in dependency order. Each asset's completion triggers a brief starburst at its position + a sound-free luminous pulse. Idle: nodes are skeletal outlines at 30% opacity. Built: full opacity + soft glow. Failed: red ring around the node + error icon.

**Layout sketch:**
```
              ┌─ A4 panchanga
              │
              │      [A13 UCN: "argument of the chart"]
              │
        ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢      ← A9 MSR star-field
       ▢ ┌──────────────────────┐ ▢
      ▢  │  Outer: 27 nakshatras│  ▢
      ▢  │  Middle: 12 signs    │  ▢
      ▢  │  Inner: 12 houses    │  ▢
      ▢  │                      │  ▢
      ▢  │   ☉ (Sun at h2)      │  ▢
      ▢  │   ☽ (Moon at h11)    │  ▢
      ▢  │     ...              │  ▢
      ▢  │                      │  ▢
       ▢ │   [A1 engine center] │ ▢
        ▢└──────────────────────┘▢
        ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢
              │
              │   [A14 sade_sati Saturn-Moon arc]
              │
              └─ A2 forensic_render

  [A6 vargas wheels around outer perimeter]    [A10 CDLM 9×9 grid lower-left]
                                                [A5 dashas clock hand]
```

### §5.3 — Detail panel (per-node click)

Slide-in panel from right edge. Fields:
- Asset name + asset_id
- Status badge (pending / running / complete / failed / cancelled)
- `engine_version` used + drift indicator: "v0.2.0-jh-parity (latest: v0.2.0-jh-parity ✓)" or "v0.2.0-jh-parity (latest: v0.3.0 — Rebuild to upgrade)"
- Last-computed timestamp + duration
- Rows written / output GCS URI / log GCS URI
- For complete assets: output preview (first 5 rows for chart_facts, top 5 MSR signals, etc.)
- For failed: error_summary + retry count

### §5.4 — Build button states

| State | Button |
|---|---|
| No prior build (fresh chart) | **Build** (large centered hero, primary color) |
| Build in progress | **Cancel** (subtle, top-right) — opens confirmation modal |
| Last build complete + current engine | **Rebuild** (subtle, top-right) |
| Last build complete + engine drifted | **Rebuild — engine v0.3.0 available** (highlighted, top-right) |
| Last build failed | **Retry build** (highlighted, hero position) |

### §5.5 — Empty-state visual

Before first build, the constellation is rendered in skeleton outline only — wheel ring drawn at 15% opacity, asset positions marked as small dots, hero "Build" button centered with a brief explanation: "Build the full deterministic profile — engine + L2.5 synthesis. ~10–60 min."

### §5.6 — Component map

```
platform/src/app/clients/[id]/build/page.tsx              ← server-side gate (existing; kept)
platform/src/components/build_orchestrator/
  ConstellationCanvas.tsx                                  ← the SVG wheel + asset nodes
  AssetNode.tsx                                            ← individual node component
  BuildWaveAnimation.tsx                                   ← Framer-Motion sequence
  AssetDetailPanel.tsx                                     ← slide-in right panel
  BuildCommandBar.tsx                                      ← Build/Rebuild/Cancel button
  EngineDriftBadge.tsx                                     ← version-pinned-vs-latest indicator
  __tests__/...
platform/src/components/build/BuildChat.tsx                ← DELETE (chat shell removed)
platform/src/app/clients/[id]/build/BuildActionPanel.tsx   ← DELETE (replaced by BuildCommandBar)
```

---

## §6 — Notifications

### §6.1 — Dashboard "Builds in progress" card

New component on `/dashboard`: lists all builds the guest owns where `status ∈ ('queued','running','cancelling')`. Per-row: chart name + asset progress (M of N) + ETA + cancel link. Polls `/api/build/active` every 5s; SSE on the active row.

### §6.2 — Post-visit toast

Component listens to `/api/build/recent` on page mount. If any build completed in the last 24h that the guest hasn't seen, show a stacking toast: "Your build for {chart_name} completed at {hh:mm} — view chart". Stored-seen-state in `audit_events` (or a lightweight `notification_views` row).

### §6.3 — Explicit non-goals
**No email.** **No browser push.** **No SMS.** User confirmed Round 4.

---

## §7 — Acceptance criteria (hard gates)

The workstream closes when ALL are true:

| # | AC |
|---|---|
| AC.1 | Guest can click "New Client" → fill form (name + gender + date + time + place [+ optional ayanamsha]) → land on `/clients/[id]/build`. |
| AC.2 | Centered hero **Build** button visible on a fresh chart. |
| AC.3 | Click Build → `builds` row created with `status='queued'` → Cloud Tasks enqueued → Cloud Run Job executes `python -m pipeline.build_chart`. |
| AC.4 | Constellation visualization renders during build; nodes light up in dependency order; SSE stream populates per-asset progress. |
| AC.5 | `natal_engine.compute_chart()` is invoked by the Cloud Run Job (NOT `pipeline.main`). `grep -rn "from natal_engine" platform/python-sidecar/pipeline/build_chart.py` returns ≥1 match. |
| AC.6 | After completion, `chart_facts.chart_id` is non-NULL for the built chart (closes the §3.4 NULL-gap from the scoping doc). |
| AC.7 | After completion, `l25_msr_signals.chart_id` is non-NULL; MSR signal count > 573 (the engine-without-threshold projection per scoping §5.5). |
| AC.8 | Detail panel on node click shows engine_version, output preview, GCS URIs, last-computed timestamp. |
| AC.9 | Cancellation: clicking Cancel during build → in-progress asset finishes → remaining marked cancelled → `builds.status='cancelled'`. |
| AC.10 | Engine drift: simulate `engine_versions` row bump → existing chart's detail panel shows "v0.2.0 (latest: v0.3.0 — Rebuild to upgrade)". Chart does NOT auto-rebuild. |
| AC.11 | Dashboard card surfaces in-progress builds across all the guest's charts. |
| AC.12 | Post-visit toast shows on next page load after a build completes. |
| AC.13 | Concurrent builds on two charts succeed independently. |
| AC.14 | `answer:eval` post-rebuild baseline shows `b11 + layer_cov` materially improved vs v1.1 baseline (`b11=29%, layer_cov=31%`). |
| AC.15 | All 8 hard gates from PLATFORM_MODERNIZATION_CLOSE remain GREEN: naming_ci, jh_oracle_pinned, G1_jh_parity, G2_authz_live, G3_contract, G4_no_native_lit, G5b_onfinish, G6_tool_coverage. |
| AC.16 | MCP server (40 tools), portal retrieval (51 tools), and `/consume` chat surface remain functional (regression-tested). |
| AC.17 | Both tenants (legacy chart + new-architecture chart) remain queryable. |
| AC.18 | Red-team pass per `MACRO_PLAN_v2_0.md §IS.8(b)`: 0 class-1 findings. |
| AC.19 | `CLAUDE.md` + `PROJECT_ARCHITECTURE_v2_2.md` + `CANONICAL_ARTIFACTS_v1_0.md` version-bumped to reflect new orchestrator surface. |
| AC.20 | Sealing artifact `00_ARCHITECTURE/BUILD_ORCHESTRATOR_CLOSE_v1_0.md` committed. |

---

## §8 — Explicitly out of scope (this workstream)

- **Email / push notifications** (Round 4.1 confirmed).
- **Per-asset surgical rebuild surface** (Round 1.3 confirmed — whole-system only).
- **LEL regeneration** — LEL is native-disclosed; engine doesn't author it.
- **Ephemeris / eclipses / retrogrades / classical RAG rebuild** — global, separate workstreams.
- **M5-A backlog** — concurrent workstream; resumes after this lands.
- **M6 prospective testing** — paused; resumes after this lands.
- **R1+R2 monitoring alert apply** — operational, separate ticket.
- **Phase L engine hygiene** (D1 dignity + ayanamsha residual <1″) — folds into Batch 0 if convenient, otherwise separate.

---

## §9 — Execution plan (batches)

Six batches, each = one Claude Code session (Antigravity IDE) driven by a `CLAUDECODE_BRIEF.md` written at project root by Cowork. After each batch closes, Cowork rewrites `CLAUDECODE_BRIEF.md` for the next batch.

### Batch 0 — Schema + form + engine entrypoint (substrate)
- Migrations 124 (builds), 125 (build_steps), 126 (engine_versions).
- Python entrypoint `pipeline/build_chart.py` — wraps `natal_engine.compute_chart` + `l25_builder.build` + DB writers. Walks the §2 DAG. Emits build_events.
- Replace Cloud Run Job command (deploy.yml or Job spec) `python -m pipeline.main` → `python -m pipeline.build_chart`.
- Extend `/api/build/start` to INSERT a `builds` row.
- New `/api/build/cancel/[buildId]` endpoint.
- New-client form spec implemented at `/clients/new` (full name, gender, date, time, place autocomplete, optional ayanamsha collapsed).
- Smoke: build the native's chart end-to-end via the OLD UI; verify `chart_facts.chart_id` populated; verify `l25_msr_signals.chart_id` populated.
- Hard gates: G1, G2 must stay green.

### Batch 1 — Per-asset writers + DAG topology
- `l25_builder` per-asset extension: forensic_render, T1 structural (aspect matrix, dispositors, shadbala, ashtakavarga, yogas), MSR (every signal, salience-coefficient, no threshold drop), CDLM, CGM, RM, UCN digest, panchanga, dashas, vargas, sensitive_points, sade_sati.
- Salience formula v1 (per scoping §5.2): `deterministic_strength = f(orb_tightness, shadbala, dignity)`, `verification_certainty = f(source_corroboration_count)`, `computed_salience = g(deterministic_strength, verification_certainty, dasha_proximity, house_weight, ashtakavarga_support)`. Versioned + unit-tested.
- All writers emit `build_steps` rows + update `pyramid_layers`.
- Validation: rebuild native's chart; MSR count ≥ 573 (engine ≥ frozen old corpus); every old MSR signal_id has a corresponding engine row.

### Batch 2 — Constellation UI (the centerpiece)
- Delete `BuildChat.tsx` + `BuildActionPanel.tsx`.
- Build `ConstellationCanvas.tsx` + `AssetNode.tsx` + `BuildWaveAnimation.tsx` + `AssetDetailPanel.tsx` + `BuildCommandBar.tsx` + `EngineDriftBadge.tsx`.
- Wire SSE consumer in the canvas.
- Mount-verification + Playwright smoke: visit `/clients/[id]/build`, click Build, watch nodes light up, click a node, see detail panel.
- Visual review gate: native sign-off on the constellation design before close.

### Batch 3 — Notifications + dashboard
- "Builds in progress" card on `/dashboard`.
- `/api/build/active` (list builds for current user).
- Post-visit toast component.
- `/api/build/recent` (list completed-but-unseen builds).
- Seen-state via `notification_views` or `audit_events`.

### Batch 4 — Cancellation + concurrency + engine drift
- `/api/build/cancel/[buildId]` (already in Batch 0, this batch wires UI + Python polling).
- Confirmation modal on cancel.
- Engine version registry endpoint `/api/engine/current`.
- Drift indicator wired in `EngineDriftBadge`.
- Concurrent-build test: enqueue 3 builds on 3 charts, verify all succeed independently.

### Batch 5 — Acceptance + close
- E2E: new client form → build → constellation animates → completion → dashboard card → toast → `/consume` works.
- `answer:eval` re-baseline; assert b11 + layer_cov uplift.
- Red-team per IS.8(b).
- Version bumps + sealing artifact `BUILD_ORCHESTRATOR_CLOSE_v1_0.md`.
- Update `CURRENT_STATE_v1_0.md`.

**Wall-clock projection:** ~10–14 days at modernization arc pace. Single Conductor + 1–2 worktrees (lower parallelism than modernization — this is more sequential because each batch depends on the prior).

---

## §10 — References

**Plans + spec:**
- `00_ARCHITECTURE/DETERMINISTIC_REBUILD_SCOPING_v1_0.md` — parent scoping doc (the why behind this workstream)
- `00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md` — L2.5 deterministic rebuild target spec
- `00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md` — T1 build spec
- `00_ARCHITECTURE/PROVENANCE_TIERING_DECISION_v1_0.md` — architectural decision foundation
- `00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md` — findings that motivated rebuild

**Engine + pipeline code:**
- `platform/python-sidecar/natal_engine/__init__.py` — `compute_chart()` entry
- `platform/python-sidecar/natal_engine/l25_builder/build.py` — L1→L2.5 deterministic transform
- `platform/python-sidecar/natal_engine/fixtures/jh_oracle.json` — JH parity oracle
- `platform/python-sidecar/pipeline/main.py` — OLD pipeline (to be replaced as the Job command)

**Existing build surface (the "wrongly connected" wiring):**
- `platform/src/app/clients/[id]/build/page.tsx` — server shell (kept; chat shell removed)
- `platform/src/components/build/BuildChat.tsx` — chat shell (DELETE in Batch 2)
- `platform/src/app/clients/[id]/build/BuildActionPanel.tsx` — thin trigger panel (DELETE in Batch 2)
- `platform/src/app/api/build/start/route.ts` — POST entry (extend in Batch 0)
- `platform/src/app/api/build/task/route.ts` — Cloud Tasks handler (unchanged)
- `platform/src/app/api/build/events/[buildId]/route.ts` — SSE rail (unchanged)
- `platform/migrations/118_build_events.sql` — event table (unchanged)

**Governance:**
- `CLAUDE.md` v4.8 — master instructions
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` v5.64 — state pointer
- `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` — session protocol
- `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` — hygiene rules
- `00_ARCHITECTURE/MIGRATION_DIRECTORY_POLICY_v1_0.md` — migration policy (next num: 124)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — canonical-path SoT

**Closure model (follow when this workstream completes):**
- `00_ARCHITECTURE/PLATFORM_MODERNIZATION_CLOSE_v1_0.md` — template for sealing artifact

---

*End of BUILD_ORCHESTRATOR_PLAN_v1_0.md — Cowork-authored 2026-05-29. Awaiting native sign-off + Batch 0 kickoff.*

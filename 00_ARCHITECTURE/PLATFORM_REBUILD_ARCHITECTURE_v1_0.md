---
artifact: PLATFORM_REBUILD_ARCHITECTURE_v1_0.md
document: Multi-Chart Autonomous Build Platform — Architecture
status: DRAFT (architecture — pending native approval; modifies nothing canonical)
version: 1.0
date: 2026-05-27
authored_by: Claude (Cowork session) — grounded in live schema recon (PHASE_14G snapshot + migrations 023/063/066/071/072/076/079/110)
native_decisions_incorporated:
  - "Multi-chart by construction — chart_id maps to storage; many chart_ids, different content."
  - "Autonomous build workflow from a dashboard Build/Rebuild button; birth intake → geocode → phased build."
  - "Great progress UX — cross-asset AND within-asset progress, full transparency, per-asset verification the user watches live."
  - "Existing tooling must keep working in the same structure; storage MAY be optimized (tool changes acceptable); GCP only."
  - "Decide additional deterministic data per asset for accuracy."
relates_to:
  - 00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md
  - 00_ARCHITECTURE/BRIEFS/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md
  - 00_ARCHITECTURE/FACT_ENGINE_BRIEF_REVIEW_v1_0.md
  - 00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md
  - 00_ARCHITECTURE/BRIEFS/JYOTISH_ENGINE_SCOPE_CATALOGUE_v1_0.md
  - 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md
approval_gate: native sign-off + version bumps on affected canonical surfaces (CLAUDE.md §L)
expose_to_chat: false
---

# Multi-Chart Autonomous Build Platform — Architecture

## §0 — Thesis

Turn a single-native, hand-authored corpus into a **multi-tenant, deterministic, self-building
instrument**. A user enters birth details on a dashboard, clicks **Build**, and an autonomous
GCP pipeline computes every data asset for that `chart_id` from the JH-equivalent engine,
verifying each asset as it goes, streaming progress to the screen. The existing retrieval
tooling keeps working because the storage *schema* is preserved and *extended* with a uniform
tenant key — not replaced. All data remains deterministic; interpretation stays at serve-time.

---

## §1 — Current-state finding (grounds everything below)

Live schema recon (PHASE_14G snapshot + later migrations) shows the data plane is
**single-native by construction**, with tenancy retrofitted inconsistently onto a few tables:

| Table(s) | Tenant key today | Verdict |
|---|---|---|
| `chart_facts` (core natal store) | **none** | single-native — biggest blocker |
| `l25_msr_signals`, `l25_cdlm_links`, `l25_cgm_nodes`, `l25_cgm_edges`, `l25_rm_resonances`, `l25_ucn_sections` | **none** | entire L2.5 plane single-native |
| `life_events`, `pattern_register`, `resonance_register`, `contradiction_register`, `cluster_register` | **none** | single-native |
| `signal_states` | `chart_id text` (default `'abhisek_mohanty_primary'`) | retrofitted, text-typed |
| `sade_sati_cycles` / `sade_sati_phases` | `native_id text` | different key name |
| `tajaka_annual` | `native_year` int only | **no tenant key at all** |
| `mcp_bundle_cache` (newest) | `chart_id uuid` | correct target shape |
| `ephemeris_daily`, `eclipses`, `retrogrades` | none (date/planet keyed) | **correct** — chart-independent shared data |
| retrieval tools (`platform/src/lib/retrieve/*`) | hardcode `NATIVE_CHART_ID` default | single-native by default |

There is **no `charts` registry** in the data plane. Conclusion: multi-chart is a uniform
tenancy normalization across ~15 per-chart tables + every tool's read path + the bootstrap/
loader scripts, plus a chart registry — not an incremental patch.

---

## §2 — Multi-chart data model

### §2.1 — One canonical tenant key: `chart_id uuid`
Settle on **`chart_id uuid`** everywhere (resolves the text/uuid/native_id/native_year
inconsistency). Every **per-chart** table gains `chart_id uuid NOT NULL REFERENCES charts(id)`,
added to its primary/unique keys and to every index. **Chart-independent** tables
(`ephemeris_daily`, `eclipses`, `retrogrades`, classical-text chunks) stay un-keyed — they are
the shared, build-once layer (per the engine brief's shared/per-chart split).

### §2.2 — The `charts` registry (new, the dashboard entity)
```
charts (
  id            uuid PK default gen_random_uuid(),
  display_name  text,                       -- "Abhisek Mohanty"
  birth_date    date NOT NULL,              -- local civil date
  birth_time    time NOT NULL,              -- local civil time
  tz_iana       text NOT NULL,              -- e.g. 'Asia/Kolkata' (from location; generalizes beyond IST)
  utc_offset    interval NOT NULL,          -- resolved historical offset at birth instant
  lat_deg       numeric(9,6) NOT NULL,
  lon_deg       numeric(9,6) NOT NULL,
  location_name text NOT NULL,              -- gazetteer label
  geonames_id   bigint,                     -- provenance of the geocode
  altitude_m    numeric default 0,
  engine_version       text,               -- which engine built this chart
  ayanamsha_config_id  text,               -- per-section ayanamsha map version
  content_hash  text,                       -- hash(engine+ephemeris+ayanamsha+inputs)
  build_status  text NOT NULL DEFAULT 'not_built'
                CHECK (build_status IN ('not_built','queued','building','built','failed','stale')),
  built_at      timestamptz,
  created_at    timestamptz default now()
)
```
`abhisek_mohanty_primary` is migrated in as the first `charts` row; its existing single-native
rows are backfilled with that `chart_id`. Multi-native from that point by construction.

### §2.3 — Retrieval-tool change (the one unavoidable tooling edit)
Tools stop defaulting to the native and take **`chart_id` as a required parameter**. Mechanical
and uniform: replace `chart_id = $1 (default NATIVE_CHART_ID)` with a required bound param,
thread `chart_id` from the request/session (the dashboard already routes `clients/[id]`).
Schema-shape is otherwise unchanged, so each tool's result contract is preserved.

---

## §3 — Storage architecture & the optimization question

**Recommendation: do NOT swap the storage engine. Keep Cloud SQL Postgres as the system of
record; the real optimization is consistency + tenancy + a reproducible provenance spine.**
A new datastore would be change-for-change's-sake risk against working tooling. The targeted
optimizations that are genuinely worth it, all GCP-native:

1. **Cloud SQL Postgres = system of record** (already co-located in `asia-south1`). Add the
   uniform `chart_id`, and **partition the largest per-chart tables by `chart_id`** (hash or
   list partitioning) so per-chart reads touch one partition and a chart delete/rebuild is a
   partition truncate. `chart_facts` and `l25_*` are the candidates.
2. **GCS JSONL = canonical provenance spine** (per FACT_ENGINE brief + review). Every chart's
   computed facts are content-addressed JSONL in `gs://madhav-marsys-build-artifacts/charts/<chart_id>/<build_id>/`.
   The DB is a **projection** of the JSONL via the loader; the markdown L1 is a second
   projection via the renderer. This is the auditable source of truth and the drift firewall.
3. **BigQuery for the shared ephemeris + cross-chart analytics ONLY** (optional, deferred).
   `ephemeris_daily` (1900–2100 daily × bodies) is the one big, chart-independent, analytical
   dataset; if transit-scan/analytics ever get heavy, mirror it to BigQuery. Per-chart compute
   reads narrow date ranges from Postgres — no change needed for the build path. Don't move it
   until an analytics need is real.
4. **pgvector stays** for `rag_embeddings` — no separate vector DB; classical-text (T0) chunks
   are shared, signal/asset embeddings (if any) are chart-keyed.
5. **Graph stays relational** (`l25_cgm_nodes/edges` + recursive CTEs for dispositor chains).
   A graph DB is overkill at this scale.

Net: storage *engine* unchanged (tooling safe); storage *model* upgraded (uniform tenancy +
partitioning + JSONL provenance + optional BQ analytics mirror).

---

## §4 — The autonomous build workflow

### §4.1 — Intake (birth details → resolved instant)
1. Date + local time fields. (Native's case: IST. Design carries `tz_iana` so it generalizes
   to any birthplace — see review R6.)
2. **Location autocomplete from a global gazetteer.** Recommend the **GeoNames** dump
   (`cities500`/`allCountries`) loaded into a Postgres `gazetteer` table → type-ahead → selecting
   a place pins **exact lat/lon + GeoNames id + IANA tz**. Deterministic, offline, no per-call
   external dependency (fits the no-external-runtime ethos). Optional: Google Places Autocomplete
   (GCP-native) for nicer UX, but pin the resolved lat/lon into `charts` so geocoding is a
   one-time intake act, never a runtime dependency.
3. **Historical timezone resolution:** lat/lon → IANA tz (offline `timezonefinder`) → historical
   UTC offset at the birth instant (LMT/DST/half-hour-zone trap). Store `utc_offset` resolved.
4. Persist a `charts` row (`build_status='not_built'`), return its `chart_id`.

### §4.2 — Dashboard: Build / Rebuild / Status
Each chart is a card. **Build** (first time) / **Rebuild** (re-run, e.g., new `engine_version`;
content-addressed so unchanged assets are skipped) / **Status** (opens the live phase panel).
States mirror `charts.build_status`.

### §4.3 — The build DAG (deterministic, content-addressed, ~25 nodes)
Runs in a dedicated **Cloud Run build-orchestrator service** (separate from `amjis-web`).
Phased, each phase gated by verification before the next starts:

```
P0  resolve config (ayanamsha map, engine_version, oracle_map)        [hard gate]
P1  astronomical core (positions, ascendant, houses, dignities)  → JSONL → verify
P2  divisional charts (D1..D150 per scope)                       → JSONL → verify
P3  dashas (Vimshottari→prana, Yogini, Jaimini, conditional)     → JSONL → verify
P4  panchanga + sensitive points + sphutas + upagrahas           → JSONL → verify
P5  structural fact layer (aspects, dispositor, shadbala, AV, KP) → JSONL → verify
P6  never-drop signal enumeration + computed coefficients (MSR)  → JSONL → verify
P7  deterministic CDLM (shared-factor graph) + CGM (structural)  → JSONL → verify
P8  RM lookup + UCN signature digest                             → JSONL → verify
P9  loader: JSONL → Postgres (chart_id-scoped) + renderer: JSONL → L1.md → verify read-compat
P10 finalize: content_hash, build_status='built', built_at
```
Long builds run async (Cloud Tasks/Pub-Sub enqueues; orchestrator processes), so the HTTP
request returns immediately and the UI subscribes to progress.

### §4.4 — Progress UX (two-level, fully transparent)
- **Cross-asset bar:** phase N of 11, with each phase's verification badge (pending/✓/✗).
- **Within-asset bar:** steps inside a phase (e.g., P2 = each varga; P6 = enumeration batches).
- **Transport:** the orchestrator writes `build_events(chart_id, build_id, phase, step, pct,
  status, verification_summary, ts)`; the frontend subscribes via **SSE** (reuse the existing
  chat-streaming SSE infra — `pending_streams`/smooth-stream). Each event updates both bars and
  shows the live verification result for the asset just finished.
- A `build_runs(build_id, chart_id, engine_version, started_at, finished_at, status)` row is the
  run header; `build_events` are its children. Both are the audit trail and the UI feed.

---

## §5 — Per-asset verification (what the user watches)

Two verification regimes, because **only the reference chart has a JH oracle**:

**A. Engine-build-time (once, reference chart = Abhisek):** field-by-field JH parity against
`JHORA_TRANSCRIPTION` + JH-side of FORENSIC's dual columns (review R1), + pyswisseph
cross-check on the astronomical core. This certifies the *engine*.

**B. Per-chart build-time (every client, no JH oracle available):** invariant + consistency
gates, shown live per asset:
- **Schema** — JSONL conforms to the canonical schema.
- **Internal invariants** — 9 grahas + lagna present; Vimshottari periods contiguous and sum to
  120y; SAV grand total = 337; navamsa lagna consistent; each house has exactly one sign; etc.
- **Independent cross-check** — pyswisseph recomputes the astronomical core; assert agreement to
  arc-second tolerance (catches adapter/config drift on this chart).
- **Referential integrity** — every signal's `constituent_facts[]` resolve to real `chart_facts`
  rows; every CDLM/CGM edge references existing nodes.
- **Completeness (never-drop)** — actual row counts vs expected per category. **Reuse the
  existing `data_source_expected` + `tool_caveats` tables** — they already encode expected-vs-
  actual counts and surface caveats; extend them per `chart_id`.
A failed gate sets `build_status='failed'`, halts the DAG, and shows the user exactly which
asset and which check failed.

---

## §6 — Additional deterministic data per asset (accuracy)

Per `JYOTISH_ENGINE_SCOPE_CATALOGUE_v1_0.md` (Band 1). Highest-leverage accuracy additions —
all deterministic, all reduce LLM re-derivation error:
- **Structural fact layer (P5)** is the single biggest accuracy win: pre-computed aspect matrix,
  dispositor chains, cross-varga dignity, **shadbala with sub-scores**, full ashtakavarga
  matrices, KP sub-lords for **all** cusps, proximity/criticality metrics. The LLM reads facts
  instead of re-deriving them (the C5 Muntha class of error becomes impossible).
- **Never-drop signal enumeration (P6)** with the decomposed computed coefficient
  (deterministic-strength + verification-certainty + computed-salience).
- **Generalized panchanga/sensitive points (P4)** + the classical sphutas (Beeja/Kshetra/etc.).
- **Transit/gochara surface** (date-parameterized) once per-chart natal is built.
Exact per-asset field lists live in the scope catalogue; the build spec will pin them.

---

## §7 — Seamless-tooling strategy (no break)

1. Schema is **extended, not reshaped** — add `chart_id` columns/keys; existing columns and
   result contracts unchanged.
2. The **loader writes the existing tables** (now chart_id-scoped) from JSONL; existing tools
   read the same tables.
3. The **one required tool edit** is threading `chart_id` (remove the hardcoded native default).
   Uniform, mechanical, individually testable per tool (40 tools).
4. **Cutover** per the target spec: build new chart_id-scoped data in parallel, validate, then
   the native chart's existing rows are re-homed under its `chart_id`; old corpus frozen as the
   model-attributed reference (DATA_LAYER_REBUILD_TARGET_SPEC §3).
5. Enumerate FK dependents before any swap; idempotency guards check the actual write target
   (durable lessons; review R4).

---

## §8 — GCP service map

| Concern | GCP service | Notes |
|---|---|---|
| System of record | **Cloud SQL Postgres** (`amjis-postgres`, asia-south1) | + chart_id, + partitioning |
| Canonical provenance | **GCS** (`madhav-marsys-build-artifacts/charts/<chart_id>/<build_id>/`) | JSONL, content-addressed |
| Build orchestrator | **Cloud Run** service (new, e.g. `amjis-builder`) | runs the DAG; PyJHora + pyswisseph + ephemeris baked in |
| Async build queue | **Cloud Tasks** or **Pub/Sub** | long builds off the request path |
| Progress transport | **SSE** from web ↔ `build_events` | reuse chat-streaming infra |
| Compute engine | Python (PyJHora wrapped + pyswisseph) | no LLM in compute path |
| Shared ephemeris analytics (optional) | **BigQuery** | mirror only if transit-analytics get heavy |
| Vectors | **pgvector** in Cloud SQL | no separate vector DB |
| Geocoding | **GeoNames** dump in Postgres (+ optional Google Places autocomplete) | lat/lon pinned at intake |
| Secrets / images / CI | **Secret Manager / Artifact Registry / Cloud Build** | existing patterns |

Existing services (`amjis-web`, `amjis-sidecar`, `amjis-mcp`) unchanged except chart_id threading.

---

## §9 — Open decisions for the native
1. **Geocoding source:** GeoNames-offline (deterministic, recommended) vs. Google Places
   autocomplete (nicer UX, GCP-native) vs. both. Either way lat/lon is pinned at intake.
2. **Timezone generalization:** confirm we capture `tz_iana` per chart (generalizes beyond IST)
   even though current clients are Indian.
3. **chart_id type cutover:** confirm `uuid` as the single key (migrate `signal_states.chart_id
   text` + `sade_sati.native_id` + `tajaka_annual.native_year` onto it).
4. **BigQuery now or later:** mirror ephemeris to BQ now, or defer until analytics demand it
   (recommend defer).
5. **Build concurrency / cost ceiling:** expected number of charts + acceptable per-build cost
   (drives Cloud Run sizing + whether builds are queued or parallel).

---

## §10 — Provenance
Model-authored (Claude, Cowork), DRAFT, native-approval-gated. Grounded in direct schema recon.
Modifies nothing canonical. Sits above the DATA_LAYER_REBUILD_TARGET_SPEC (what each asset is)
and the FACT_ENGINE brief (how L1 is computed); this document is the platform that builds them
for many charts.

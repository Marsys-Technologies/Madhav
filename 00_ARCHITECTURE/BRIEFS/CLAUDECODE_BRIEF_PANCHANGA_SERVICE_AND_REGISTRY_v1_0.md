---
artifact: CLAUDECODE_BRIEF_PANCHANGA_SERVICE_AND_REGISTRY_v1_0.md
canonical_id: PANCHANGA_SERVICE_AND_REGISTRY_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork (planning) 2026-06-09
authored_for: Claude Code in Antigravity IDE
delivery_model: 1 branch, 3 sequenced phases, plan-then-execute
scope: >
  Re-architect the panchang engine into a deterministic L0 service (two APIs + rich output
  contract), carve muhurat into its own module, upgrade the asset_registry to hold services +
  data assets with catalog status, and register bg_panchanga + bg_ephemeris_engine as L0 service
  assets. Does NOT initialize per-chart build-state (separate follow-on).
---

# Panchanga Service + Unified Registry — Antigravity Execution Brief v1.0

## §0 — Read first (design sources — these are authoritative)

Read these before coding; they contain the full decisions this brief implements:
- `00_ARCHITECTURE/PANCHANGA_ENGINE_REARCHITECTURE_v1_0.md` — engine re-arch, 2 APIs, §B.5/§B.6
  output contract, §B.7 A4-rule, §C muhurat carve.
- `00_ARCHITECTURE/UNIFIED_ASSET_REGISTRY_ARCHITECTURE_v1_0.md` — service+data asset model, §C
  attributes, §D health probe, §E catalog/build-state, §I lifecycle/status.
- `00_ARCHITECTURE/BG_PANCHANGA_L0_SERVICE_v1_0.md` — engine/product split, L0 registration.
- `00_ARCHITECTURE/A4_PANCHANGA_SPEC_v1_0.md` §4b/§4c — A4 = persisted panchanga_instant @ birth.

**Hard constraints (binding):** deterministic-only, zero LLM in the engine; PyJHora is the CHART
engine but **panchang uses the swisseph `panchang_engine`** (canonical) — `pyjhora_adapter/panchanga.py`
is retired; NO JH-parity oracle; floors-are-aspirational (per-topic `computed: true/false`, never
fabricate); no audience-tier; verify against PROD; merge-verify before any "done".

## §1 — Branch + topology

- Branch `feature/panchanga-service-registry` off `main`. One PR after all phases green.
- Phases are sequenced (P1 schema → P2 engine → P3 registration); a phase opens only after the
  prior verifies. Each phase = one commit.
- Reverse-citation gate before retiring `pyjhora_adapter/panchanga.py`: grep all callers, repoint
  to the core, THEN delete. Halt-and-report if a caller can't be repointed.

## §2 — PHASE 1 — Registry schema upgrade

**Goal:** `asset_registry` can describe services + data assets with full attributes + catalog status.

Author migration `platform/supabase/migrations/<NEXT>_asset_registry_service_support.sql`:
- ADD COLUMNS to `asset_registry`: `asset_type text CHECK (asset_type IN ('data','service'))`,
  `layer_name text`, `layer_index text` (L0..L5), `provides_apis jsonb`, `health_probe jsonb`,
  `catalog_status text CHECK (catalog_status IN ('CURRENT','DRAFT')) DEFAULT 'DRAFT'`.
- Extend the `storage_type` allowance to include `'service'`.
- Backfill existing rows: set `asset_type='data'`, populate `layer_name`/`layer_index` from `layer`
  (brahmagyan→Brahmagyan/L0, ganita→Gaṇita/L1, bodha→Bodha/L2, kala→Kāla/L3, phala→Phala/L4,
  mimamsa→Mīmāṃsā/L5), set `catalog_status='CURRENT'` for the 12 L0 bg_* (finalized) and
  `'DRAFT'` for L1–L5 (specs in finalization). Reversible down-block.

Update `platform/scripts/seed/asset_registry_seed.ts`: add the new fields to the type + every entry
(idempotent re-seed). Update orchestrator `asset_runner.py`: a `storage_type='service'` asset's
"build" = run its `health_probe` (not a row-writer); GREEN/degraded/down instead of row-count.
Update cockpit registry API + view to render service-health for service assets + show catalog_status.

**Verify [verify-against: prod]:** `\d asset_registry` shows new columns; existing rows backfilled
(12 L0 CURRENT, L1–L5 DRAFT); re-seed idempotent; cockpit renders without error.

## §3 — PHASE 2 — Panchanga engine re-architecture

**Goal:** one deterministic core (`panchanga_core`), two APIs, rich output contract, muhurat carved out.

### §3.1 — Two APIs (the core service contract)
In `platform/python-sidecar/panchang_engine/__init__.py`, establish the named core with two public
entry points:
- `panchanga_instant(instant: datetime, lat, lon, tz_offset) → PanchangaInstant` — panchang state at
  an EXACT moment (date+time). The chart builder + any L1–L5 "panchang at moment X" use this.
- `panchanga_day(date, lat, lon, tz_offset) → PanchangaDay` — full whole-day record. Product + day API.
- (`panchanga_range` may wrap `panchanga_day` over N days; not a third core API.)
Both deterministic, live-from-DE441, location always a parameter. Strip any Bhubaneswar default
from the CORE (defaults live only in the product/UI layer).

### §3.2 — Rich output contract (per PANCHANGA_ENGINE_REARCHITECTURE §B.5 + §B.6)
Build the full topic set; each topic carries a `computed: true|false` marker; un-implemented topics
floor to absent (null/empty + `computed:false`) — NEVER fabricated. Topics:
- Shared: five angas (with % elapsed + transition moments), paksha, planetary state (9 grahas +
  **Uranus/Neptune/Pluto + upagrahas** Gulika/Mandi/Dhuma/Vyatipata/Parivesha/Indrachapa/Upaketu/Kala),
  sunrise/sunset/moonrise/moonset, ALL inauspicious windows, ALL auspicious windows, choghadiya,
  hora, special yogas, calendrical (masa purnimanta+amanta, adhika/kshaya, samvat ×4, **samvatsara/
  Jovian-60**, ritu, ayana, sankranti context), **Anandadi Yoga** (28 nakshatra×vara), **Vasa family**
  (Agni/Chandra/Rahu/Disha/Nakshatra/Bhadra Vasa), **Panchaka** (5-Panchaka), **Homa/Ahuti** windows,
  Tithi/Nakshatra Shoonya, Tara/Chandra Bala (when reference natal nak/sign supplied), provenance.
- DAY-only: festival/vrata flags (Ekadashi/Pradosh/Sankashti/Purnima/Amavasya/Sankranti +
  rule-derived), sankranti/ingress/station/eclipse day-events.
- INSTANT-only: **Lagna + 12 house cusps + MC at the instant**, window-membership (which inauspicious/
  auspicious/choghadiya/hora the instant falls in + time-to-next-boundary), instant micro-timing
  (Pranapada, ghati/vighati, muhurta-of-day).
Update `types.py` (PanchangaInstant + PanchangaDay dataclasses) + `serialize.py` accordingly.
Topics 1–9 are engine-native today; the rest are added where a verified deterministic formula
exists, else floored. Keep Drik-parity tests green for the native-set topics.

### §3.3 — Carve muhurat into a self-evident module
Create `platform/python-sidecar/muhurat/`: move `muhurat.py`→`finder.py`, `EVENT_TABLES`→`event_tables.py`,
`config/muhurat_weights.yaml`→`muhurat/weights.yaml`. `muhurat/` imports `panchang_engine`; it NEVER
recomputes panchang. `panchang_engine/` now contains ZERO scoring/judgement. Update all importers.

### §3.4 — Retire the duplicate + relabel
Reverse-citation gate, then delete `platform/python-sidecar/pyjhora_adapter/panchanga.py` (all panchang
goes through `panchanga_core`). Relabel `panchang_engine/README.md` "L1.5 computation layer" → "L0
Brahmagyan service". Funnel ALL panchang callers (router, `/panchang` SSR, chart writers, muhurat)
through the two core APIs.

**Verify [verify-against: prod]:** `panchanga_instant` at native birth (1984-02-05T10:43:00, lat 20.27,
lon 85.84, tz +330) returns FORENSIC-consistent angas (Shukla Tritiya / Purva Bhadrapada / Shiva /
Garaja / Ravivara); `panchanga_day` returns full day record; muhurat finder still works from `muhurat/`;
no caller imports the deleted duplicate; Drik-parity tests green.

## §4 — PHASE 3 — Register the two L0 service assets

Author migration `platform/supabase/migrations/<NEXT>_register_service_assets.sql` — INSERT:
- `bg_panchanga` — layer=brahmagyan, layer_name='Brahmagyan', layer_index='L0', asset_type='service',
  storage_type='service', scope='global', catalog_status='CURRENT', target_table=null, count_sql=null,
  `provides_apis`=[{name:panchanga_instant, signature, consumers:[chart_builder, L1–L5]},
  {name:panchanga_day, signature, consumers:[product, day_api]}], `health_probe`=
  {single_engine, deterministic_smoke, forensic_birth_check, endpoints_200, date_range},
  depends_on=['bg_ephemeris_engine'].
- `bg_ephemeris_engine` — layer=brahmagyan/L0, asset_type='service', storage_type='service',
  scope='global', catalog_status='CURRENT', `provides_apis`=[position-at-instant], `health_probe`=
  {DE441 present + path set, fixed-instant position smoke vs FORENSIC, MEAN_NODE-for-Rahu invariant},
  depends_on=[]. (Distinct from the `bg_ephemeris` daily-cache DATA asset — leave that row untouched.)

Add both to `asset_registry_seed.ts` + `CAPABILITY_MANIFEST.json`. Implement the health-probe runners
the cockpit/orchestrator call. Deliberate L0 seal reopen: note in `L0_BRAHMAGYAN_*` + `CURRENT_STATE`
+ `SESSION_LOG`; re-run L0 Vimarśaka over the 2 new service assets.

**Verify [verify-against: prod]:** both service rows present (asset_type='service', CURRENT); health
probes return GREEN (panchanga FORENSIC-consistent; ephemeris DE441 smoke passes); cockpit shows 2 L0
service tiles; `provides_apis` queryable.

## §5 — Out of scope (explicit)
- Per-chart build-state init for Abhisek — SEPARATE follow-on (after catalog stabilizes).
- `bg_ephemeris` daily-cache keep/drop — PARKED.
- `panchanga_daily` Bhubaneswar almanac product disposition — PARKED (product tier).
- L1 ga_* asset builds (A6–A9 still in review).

## §6 — Close
Merge-verify (`gh pr view <N> --json mergeCommit,state`); deploy sidecar + web; post-deploy smoke the
2 health probes on prod; update CURRENT_STATE + SESSION_LOG. Branch + worktree cleanup.

---

*End of brief. Run §1 gates, then P1 → verify → P2 → verify → P3 → verify → close. Halt-and-report on
any FORENSIC mismatch or un-repointable caller.*

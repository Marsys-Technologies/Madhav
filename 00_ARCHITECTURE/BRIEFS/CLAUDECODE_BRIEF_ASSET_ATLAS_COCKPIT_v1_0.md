---
artifact: CLAUDECODE_BRIEF_ASSET_ATLAS_COCKPIT_v1_0.md
canonical_id: ASSET_ATLAS_COCKPIT_BRIEF
version: 1.1
status: CURRENT
authored_by: Cowork (planning) 2026-06-12
changelog:
  - v1.1 (2026-06-12): ADDENDUM A1 — replace the raw chart_id selector with a CLIENT-NAME dropdown
    (native request). See §A1 at the foot. The v1.0 Atlas was built with a chart_id selector; this
    amends it to show client names.
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
purpose: A LIVE, real-time cockpit feature — the "Asset Atlas" — giving complete cross-layer visibility of every data asset: structure, live counts, real unit-level sample data, and astrological meaning. Serves reuse-decisions + registry reconciliation + astrological understanding equally.
data_plane: ALWAYS prod via Cloud SQL proxy (this feature's whole value is live prod data)
extends_existing: platform/src/app/cockpit/* + platform/src/app/api/cockpit/{registry,stats}/route.ts — do NOT build a parallel cockpit
delivery_model: branch + plan-then-execute; read-only feature (no writes to chart data); verify on localhost:3000 then prod
---

# Asset Atlas — Live Cockpit Feature — Execution Brief v1.0

## §0 — What this is + why live (not a snapshot)

A new cockpit view that renders the WHOLE instrument as a navigable tree:
**Layer (L0–L5) → Asset (sub-asset) → Tables → Live row count → Real sample rows → Astrological meaning.**
The native uses it to (a) decide what existing data a NEW asset can leverage, (b) reconcile asset
registry vs real tables vs live counts, (c) understand the astrology each asset holds — all three
equally. It MUST be truly live (query prod), because a baked snapshot would defeat the purpose ("show
me real rows from this table," "what's the count right now"). This is why it's a server-side cockpit
feature, not a static artifact.

## §1 — Build ON the existing cockpit (do not reinvent)
Already present: `/cockpit` (the view), `/api/cockpit/registry` (asset metadata), `/api/cockpit/stats`
(executes `count_sql`). Reuse all three. The Atlas is a new TAB/route under the cockpit + TWO new
read-only endpoints (table-schema, sample-rows). Reuse the existing auth, the existing registry read,
the existing count_sql executor.

## §2 — The data model the Atlas renders (per the native's reconciliation chain)
For each LAYER (Brahmagyan/L0, Gaṇita/L1, Bodha/L2, Kāla/L3, Phala/L4, Mīmāṃsā/L5) show its ASSETS
from `asset_registry` (the single source of truth). For each ASSET, a collapsible drop-down with:
1. **Identity:** asset_id, sanskrit_name, english_name, english_description, layer, scope (per_chart/global), storage_type, status (active/draft).
2. **Tables:** target_table(s) the asset writes. For multi-table assets (e.g. bo_sangati, bo_upaya), list ALL its tables (resolve from the §14 asset→table map / count_sql expression, not just one).
3. **Live count:** run the asset's `count_sql` against prod (reuse /api/cockpit/stats). Show the number live, with a per-chart selector (default native 482012f1; the count_sql is chart-scoped via $1).
4. **Registry reconciliation badge:** GREEN if the target table(s) exist in prod AND count_sql runs AND ≥0 rows; AMBER if table exists but 0 rows (built-but-empty); RED if table missing / count_sql errors / registry says a table that isn't in the DB. This is the "reality == registry?" lens.
5. **Dependencies:** depends_on (upstream) + computed downstream (who depends on this) — for the reuse-decision lens ("what can a new asset leverage / what would I break").
6. **Sample data (unit-level):** a "Show 10 rows" button that calls the new sample-rows endpoint and renders a real table preview from that asset's primary table (chart-scoped). The core "look at real data" requirement.
7. **Astrological meaning:** a short domain annotation per asset — what astrological content it holds, in IAST terms (e.g. "ga_structural: every aspect/yoga/dosha/argala/dispositor across 30 vargas × 5 ayanamshas, named patterns labelled from L0 catalogs"). Seed these from the L0_L1_SENSEMAKING_AUDIT dossier + the A-specs; store as a `description`/`atlas_note` so they're editable, not hardcoded in the UI.

## §3 — Two new READ-ONLY endpoints (the only new backend)
1. **`GET /api/cockpit/atlas/schema?table=<t>`** → column list + types for a table (from `information_schema.columns`). Powers the "what fields does this table hold" view. Whitelist: only tables that appear as a `target_table` in asset_registry (no arbitrary table access).
2. **`GET /api/cockpit/atlas/sample?asset=<id>&chart_id=<c>&limit=10`** → up to N (cap 50) real rows from the asset's primary table, chart-scoped (`WHERE chart_id=$1` if per_chart; no filter if global). Read-only SELECT; parameterized; asset-id resolved to its table via the registry (never accept a raw table name from the client). Returns rows + columns for the preview table.
**Both endpoints: read-only, parameterized, registry-gated (no SQL injection surface, no arbitrary-table reads, no writes).**

## §4 — The three lenses (all equal — the UI surfaces each)
- **Reuse lens:** each asset shows its outputs (tables + sample data + what-it-holds) + downstream dependents, so the native can see "a new L3 asset could consume bo_sangati's domain_links." A "show me all assets that produce <domain/graha/varga> data" filter helps here.
- **Reconciliation lens:** the GREEN/AMBER/RED badge + a top-level summary ("N assets, M lit, K built-but-empty, J registry-vs-prod mismatches") so drift is visible at a glance.
- **Astrological lens:** the per-asset domain annotation + the real sample rows rendered readably (e.g. a yoga_label row shown as "Hamsa Mahapurusha — Jupiter 4H Cancer — D1 — lahiri"), so the chart content is legible, not raw JSON.

## §5 — Real-time guarantees + honesty
- Counts + sample rows are LIVE (queried on expand/click, not cached stale). Show a "as of <timestamp>" on each live read so the native knows it's fresh.
- If an asset's table is missing or count_sql errors, show RED + the actual error — NEVER silently show 0 or hide the asset. (No-silent-drop, applied to the dashboard itself.)
- The registry is the spine: every asset in `asset_registry` appears, even draft/future ones (L3–L5 placeholders show as "registered, not yet built" — AMBER/grey), so the native sees the FULL arc, not just built assets.

## §6 — Acceptance [verify on localhost:3000 then prod]
- [ ] Atlas route under /cockpit; all 6 layers render with their registry assets (incl. unbuilt L3–L5 placeholders).
- [ ] Each asset is a collapsible drop-down with: identity, table(s), LIVE count, reconciliation badge, deps, sample-data button, astrological note.
- [ ] "Show 10 rows" returns REAL rows from prod for a built asset (e.g. ga_structural, bodha_msr_signals), chart-scoped, rendered readably.
- [ ] Multi-table assets list ALL their tables (bo_sangati → 6 tables, bo_upaya → 6 RM tables).
- [ ] Reconciliation badges correct: a built asset = GREEN, a registered-but-unbuilt L3 asset = grey/AMBER, a registry-vs-prod mismatch = RED with the error.
- [ ] Both new endpoints are read-only, registry-gated, parameterized (no arbitrary table access, no writes). `[security check]`
- [ ] Counts match a direct psql count for spot-checked assets. `[verify-against: prod]`
- [ ] No asset hidden on error; errors shown explicitly.

## §7 — Out of scope
No writes / no build-triggering (that's the existing cockpit build controls — link to them, don't duplicate). No editing of registry from the Atlas (read-only view). Astrological notes are seeded text, not LLM-generated at runtime.

---
*End of ASSET_ATLAS_COCKPIT v1.0. A live, server-side cockpit feature: layer→asset→tables→live-count→
real-sample-rows→astrological-meaning, drill-down, three lenses (reuse / reconciliation / astrology),
registry as spine, no-silent-drop on the dashboard itself. Extends the existing cockpit; adds two
read-only registry-gated endpoints. The native's standing decision surface for every future asset.*

---

## §A1 — ADDENDUM (v1.1): client-NAME dropdown instead of raw chart_id (native request)

**Change:** the Atlas's chart selector currently takes/shows a raw `chart_id` (UUID). Replace it with a
**dropdown of CLIENT NAMES** — the native picks a client by name; the Atlas resolves to that client's
`chart_id` under the hood and updates all counts + sample rows.

**Reuse existing data (no new data layer):**
- The `charts` table has `chart_id` (uuid) + a human name (`name`, `subject_name`/`preferred_name`).
- The existing `GET /api/clients` route already returns `charts.* + profiles.name AS client_name`
  ordered by created_at — this is the Jātakas/roster source. **Reuse it** (or a trimmed
  `id/chart_id/name` projection) to populate the dropdown; do NOT add a new endpoint if /api/clients
  suffices.

**UI behaviour:**
- Dropdown shows the **client name** (e.g. "Abhisek Mohanty"), not the UUID. If two clients share a
  name, disambiguate with birth_date or a short chart_id suffix in the label.
- Selecting a client sets the active `chart_id` (the value passed to /api/cockpit/stats + the sample
  endpoint) — same downstream wiring the chart_id selector already used; only the picker UI changes.
- Default selection = the native (Abhisek, chart 482012f1-710e-4a25-994a-93821f5871aa) so the Atlas
  opens on the primary chart.
- On change, re-fetch counts + clear expanded sample rows (they re-lazy-load for the new chart).

**Acceptance [verify on localhost:3000]:**
- [ ] Selector shows client NAMES, not UUIDs; populated live from the clients/charts list.
- [ ] Choosing a client updates all asset counts + sample rows for THAT client's chart_id.
- [ ] Defaults to the native on load.
- [ ] No raw chart_id shown in the picker (a chart_id may still appear as a small detail/tooltip if useful, but the primary label is the name).
- [ ] Reuses /api/clients (or equivalent existing list) — no redundant new endpoint.

*Addendum A1 end. Pure UI swap on the existing selector + reuse of /api/clients; the data wiring
underneath (chart_id → stats/sample) is unchanged.*

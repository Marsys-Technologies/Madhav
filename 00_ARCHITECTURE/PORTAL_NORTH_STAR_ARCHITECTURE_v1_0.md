---
artifact: PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.md
document: Portal North-Star Architecture — Multi-Guest / Multi-Chart / AI-Native (current → target)
status: DRAFT (plan — pending Claude Code code-level validation, then native finalization; modifies nothing canonical)
version: 1.0
date: 2026-05-27
authored_by: Claude (Cowork session) — grounded in direct code recon (paths cited inline)
native_decisions_incorporated:
  - "Two tenancy axes: multi-guest (logins) + multi-chart (subjects). One guest = super_admin; all others = guests; clients = chart subjects (data, not logins)."
  - "Rename Consume → Consult across UI/routes/code."
  - "Shared-chart access (super-admin grants a guest a chart they don't own) = view-only: Profile + Consult + Panchang; no Build/Rebuild/edit/delete."
  - "Command Center (new super-admin-only Cockpit tab) surfaces ALL backend gates as runtime-configurable: feature flags, pipeline gates/thresholds, model/provider routing, access/tier gates."
  - "Cockpit + Panchang become multi-tenant via a chart/guest dropdown. Panchang default = general; apply client → personalized."
  - "Two internal query pipelines (Classic single-pass vs Claude-style agentic) must be isolated architecturally AND implementation-wise."
  - "Reuse what works; rename properly; best-practice module boundaries; GCP only."
  - "Remove the chat response-depth selector ('deep study' / 'brief') from the Consult UI."
  - "LEL is NEVER used in data build/churn — serve-time-only validation input. Gated by a per-query chat toggle (exists) subordinate to a global cockpit kill-switch (global OFF wins). ALL data assets get global access controls in the Command Center: disabling a source disables its dependent retrieval tools."
relates_to:
  - 00_ARCHITECTURE/PLATFORM_REBUILD_ARCHITECTURE_v1_0.md       # multi-chart build platform (chart_id, charts registry, build DAG)
  - 00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md      # deterministic data layer + JH engine first
  - 00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md          # tech-debt / two-pipeline cleanup
  - 00_ARCHITECTURE/BRIEFS/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md    # JH-equivalent fact engine
  - 00_ARCHITECTURE/TOOL_PORTFOLIO_PLAN_v1_3.md                 # unified tool contract + gateway + tier excision (convergence §7.5)
companion_diagram: 00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.svg
process: "Cowork authors this plan → native hands to Claude Code for code-level validation → Claude Code reports → Cowork finalizes (v1.1)."
approval_gate: native sign-off + version bumps on affected canonical surfaces (CLAUDE.md §L)
expose_to_chat: false
---

# Portal North-Star Architecture — Multi-Guest / Multi-Chart / AI-Native

## §0 — Thesis

Turn a single-native, single-tenant portal into a **multi-guest, multi-chart, AI-native
instrument** with clean module seams, runtime-governable behaviour, and two cleanly isolated
query pipelines. The portal already carries most of the identity machinery (Firebase auth,
roles, per-chart app tables, ownership checks); the work is to **(a)** split the fused
owner/subject concept and add a sharing ACL, **(b)** name the modules properly and isolate the
two pipelines, **(c)** lift buried backend "gates" into a super-admin **Command Center**, and
**(d)** dovetail this onto the already-drafted multi-chart data plane + deterministic data
rebuild + JH engine. Storage engine and working tooling are **reused, not replaced**.

This document is the **unifying North-Star**. It sits above and references three existing DRAFTs
rather than duplicating them: `PLATFORM_REBUILD_ARCHITECTURE` (how charts get built for many
`chart_id`s), `DATA_LAYER_REBUILD_TARGET_SPEC` (what each data asset becomes), and
`TARGET_ARCHITECTURE_REPORT` (tech-debt + two-pipeline cleanup). It **adds** the one layer none
of them cover: the multi-guest identity / RBAC / sharing control plane and the portal UX model.

See the companion diagram `PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.svg` (layered modules + 5-phase
migration, colour-coded keep / extend / new / rebuild).

---

## §1 — Verified current state (the honest map)

All claims below are from direct code reads (paths cited). Claude Code should re-verify against
HEAD before acting.

### §1.1 — Identity & access (more mature than "single-tenant" implies)
- **Auth:** Firebase + `__session` cookie. Server resolves the user via `getServerUser()`
  (`platform/src/lib/firebase/server.ts`); DB access is service-role (RLS exists but is
  defence-in-depth — real authz lives in API routes). Helper:
  `platform/src/lib/auth/access-control.ts` (`getServerUserWithProfile`, `requireSuperAdmin`).
- **Principal store:** `profiles` table (migration 001/006/007). `id text` = Firebase UID;
  `role text CHECK IN ('super_admin','client')` (migration 007 renamed `astrologer`→`super_admin`);
  `status` (pending/active/disabled); `username`, `email`, `approved_by`. `access_requests`
  table + `/admin` approval flow exists.
- **Authz today (consult route):** `platform/src/app/api/chat/consume/route.ts:305` —
  `if (!isSuperAdmin && chart.client_id !== user.uid) return res.forbidden()`. Super-admin sees
  all; a non-admin sees only charts where `client_id === their own uid`.

### §1.2 — The fused owner/subject problem (the core remodel)
`charts.client_id text REFERENCES profiles(id)` (migration 001 §33, re-typed to text in 006)
**fuses two concepts**: who *owns/created* the chart and who the chart is *about*.
`POST /api/clients` (`platform/src/app/api/clients/route.ts:57`) **auto-creates a Firebase user
per chart** (`client_id = firebaseUser.uid`) — i.e. each chart subject is also a login.
The target model needs `owner_id` (the guest who created it) **separate** from the subject
(birth data only). Cross-guest sharing has **no** mechanism today — only public read-only
*conversation* links exist (`conversation_shares`, migration 004 + 113 selective-share), not
chart-level grants.

### §1.3 — Per-chart app tables already tenant-keyed (good)
`charts`, `pyramid_layers`, `documents`, `conversations`, `reports` are all keyed by
`chart_id uuid` with FKs (migration 001). The application plane is already multi-chart.

### §1.4 — Data/synthesis plane is single-native (the big rebuild, already drafted)
~19 L2.5 tables (`chart_facts`, `l25_msr_signals`, `l25_cdlm_links`, `l25_cgm_*`,
`l25_rm_resonances`, `l25_ucn_sections`, L3 registers, `rag_chunks`) have **no** `chart_id`.
Only **two** retrieval files hardcode the native and they disagree on type:
`query_signal_state.ts:23` (`'abhisek_mohanty_primary'`, text) and `muhurta_finder.ts:29`
(`'362f9f17-…'`, uuid) — both already accept `p.chart_id ?? NATIVE_CHART_ID`. This plane is the
subject of `PLATFORM_REBUILD_ARCHITECTURE` (chart_id normalization + `charts` registry) and
`DATA_LAYER_REBUILD_TARGET_SPEC` (deterministic rebuild). Not re-specified here; dovetailed in §7.

### §1.5 — Two query pipelines, interleaved in one route
Both live inside `platform/src/app/api/chat/consume/route.ts`, branching on
`configService.getFlag('R11V2_USE_ADAPTERS')` (~line 923):
- **Classic ("Classic Marsys"):** `createOrchestrator()` (`lib/synthesis/index.ts` →
  `orchestrator.ts` + `single_model_strategy.ts` / `panel_strategy.ts`). Single-pass: plan →
  retrieve-all-into-context → one-shot synthesis.
- **Agentic ("Claude-style"):** `getAdapter()` (`lib/providers/dispatcher.ts`) → per-provider
  adapter → `runAgenticLoop()` (`lib/synthesis/agentic_loop.ts` + `mcp_tool_executor.ts`).
  Multi-provider, bounded tool loop. Partially complete.
They share planner (`pipeline_planner.ts`), B.11 floor, persistence (`onFinish`), streaming
(`lib/streams/data_parts.ts`), citation gate — all inline in one ~1000-line file.

### §1.6 — Retrieval, MCP, compute, storage
- **Retrieval:** ~55 portal tools (`platform/src/lib/retrieve/*`), `primitives_registry.ts` SSOT,
  `tool_catalogue.ts`.
- **MCP:** `platform-mcp/` (40 tools), API key → principal (`user_uid`, `audience_tier`); tiers
  `client`/`acharya`/`super_admin` (migration 070 + 117). Currently single-native.
- **Compute:** `platform/python-sidecar` (panchang/transit/muhurat). No JH-equivalent natal
  engine yet (drafted in `FACT_ENGINE_PYJHORA_BRIEF`).
- **Storage / GCP (asia-south1):** Cloud SQL Postgres (`amjis-postgres`), GCS, pgvector;
  services `amjis-web`, `amjis-sidecar`, `amjis-mcp`.

---

## §2 — Target module architecture & nomenclature

### §2.1 — Microservices stance: modular monolith + sidecars (NOT a microservices explosion)
Keep the deployable footprint small and the **internal seams clean**. Deployable units:
`amjis-web` (Next.js; bounded internal modules), `amjis-sidecar` (python compute), `amjis-mcp`
(MCP server), and **new** `amjis-builder` (the autonomous build orchestrator, per
PLATFORM_REBUILD §8). The discipline that matters is **module boundaries inside the monolith**
(directory + import rules + the existing `primitives_registry` / `CAPABILITY_MANIFEST` SSOT),
not network boundaries. Future-proofing = a module *can* be extracted to its own service if load
demands — we don't pay the ops/latency cost prematurely. This matches the established
"reuse, don't rebuild for its own sake; GCP only" ethos.

### §2.2 — Bounded modules (target names)
| Module | Responsibility | Today | Target |
|---|---|---|---|
| **Experience** | Next.js portal: login, dashboard, per-chart pages, panchang, admin | exists | role-gated nav + chart switcher + sharing UI |
| **Identity & Access** | Firebase auth, principals, roles, **authorization service**, sharing ACL | partial | add `owner_id`, `chart_grants`, central `authorizeChartAccess()` |
| **Query Pipelines** | the two isolated answer pipelines (§5) | interleaved | `pipelines/single_pass/` + `pipelines/agentic/` behind one interface |
| **Reasoning & Synthesis** | multi-provider dispatch, agentic loop, **serve-time panel**, B.11, citation gate | exists | interpretation relocated to serve-time panel (per DATA_LAYER §4) |
| **Retrieval & MCP** | retrieval tools + `primitives_registry` SSOT + MCP server | exists | chart_id-parameterized; MCP per-chart (§6) |
| **Compute & Build** | JH-equiv fact engine, build orchestrator, sidecar, geocode/tz | partial | new engine + `amjis-builder` (PLATFORM_REBUILD) |
| **Knowledge / Data Plane** | charts registry + grants, L1/T1 facts, MSR/CDLM/CGM/RM, classical T0 | single-native | chart_id-keyed + deterministic (DATA_LAYER) |
| **Storage & Provenance** | Postgres (system of record), GCS JSONL spine, pgvector | exists | +chart_id +partitioning + JSONL spine |
| **Governance & Control** | CAPABILITY_MANIFEST, drift/schema/mirror, **Command Center**, Observatory, Learning | partial | runtime gate control plane (§8) + multi-tenant cockpit |

### §2.3 — Rename map (proposed; Claude Code to cost each)
| From | To | Notes |
|---|---|---|
| Login role value `client` | `guest` | every login is a guest; `super_admin` unchanged. Frees the word "client" for subjects. |
| (concept) `client` | **chart subject** = data only | no login account per subject (deprecate per-chart Firebase user creation in `/api/clients`). |
| `charts.client_id` | `charts.owner_id` (+ keep subject birth fields on `charts`) | the guest who created the chart; FK → `profiles(id)`. Backfill native as first owner. |
| UI/route `consume` | **`consult`** | `/clients/[id]/consult`, label "Consult". API route alias kept during cutover. |
| "Classic Marsys" / "Claude-style" | keep UI labels; internal **`single_pass`** / **`agentic`** | code-level module names; UI strings unchanged. |
| `profiles` (table) | keep physical name; concept = **principal** | renaming a core FK target is high-cost; document the concept, don't churn the table unless Claude Code finds it cheap. |

---

## §3 — Multi-tenancy design (identity / RBAC / sharing — the new layer)

### §3.1 — Principals & roles
`profiles` is the principal store. Role becomes `super_admin | guest`. Status lifecycle
(`pending`/`active`/`disabled`) and `access_requests` approval flow are **kept** (guest
onboarding stays invite/approve unless changed later).

### §3.2 — Charts registry: owner + subject (split the fusion)
Extend `charts` (aligning with PLATFORM_REBUILD §2.2's registry):
```
charts (
  id            uuid PK,
  owner_id      text NOT NULL REFERENCES profiles(id),   -- the GUEST who created it (was client_id)
  display_name  text NOT NULL,                            -- subject label (data, not a login)
  birth_date date, birth_time time, tz_iana text, utc_offset interval,
  lat_deg numeric, lon_deg numeric, location_name text, geonames_id bigint,
  engine_version text, ayanamsha_config_id text, content_hash text,
  build_status text DEFAULT 'not_built', built_at timestamptz, created_at timestamptz
)
```
Migration: rename/copy `client_id`→`owner_id`; **stop auto-creating a Firebase user per chart**.
Native's existing chart → `owner_id` = native's uid.

### §3.3 — Sharing ACL: `chart_grants`
```
chart_grants (
  id uuid PK,
  chart_id    uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
  principal_id text NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  permission  text NOT NULL DEFAULT 'view',   -- view-only per native decision
  granted_by  text NOT NULL REFERENCES profiles(id),
  granted_at  timestamptz DEFAULT now(),
  UNIQUE(chart_id, principal_id)
)
```

### §3.4 — One authorization service (web + MCP share it)
`authorizeChartAccess(principal, chart_id, action) -> allow|deny`, in `lib/auth/`:
- `super_admin` → all actions on all charts.
- `owner_id === principal.id` → all actions (Profile, Build, Rebuild, Consult, Panchang, edit, delete).
- a `chart_grants` row exists → **view-only** actions only (Profile read, Consult, Panchang). No Build/Rebuild/edit/delete (native decision).
- else → deny.
Every web route (`consult`, `clients`, `reports`, `pyramid`, `panchang`, `build`) and the MCP
server call this single function. Replaces the inline `chart.client_id !== user.uid` check.

---

## §4 — Experience layer: navigation & page model

### §4.1 — Role-gated dashboard
- **Guest** sees two surfaces: **Roster** (charts owned + shared-to-them) and **Panchang**.
- **Super-admin** adds **Cockpit, Audit, Performance, AI Ops, Admin** (all super-admin-only,
  enforced by `requireSuperAdmin()` on both the page and its API routes).
- Dashboard stops auto-redirecting "client" role to a single chart (`dashboard/page.tsx:23`);
  a guest with N charts sees a roster + chart switcher.

### §4.2 — Per-chart pages (under `/clients/[id]/`)
| Page | Route | Purpose |
|---|---|---|
| **Profile** | `/clients/[id]` | At-rest astrological identity (chart wheel, core placements, dasha snapshot, build-completeness %) + nav hub with Build / Consult / Panchang buttons. |
| **Build** | `/clients/[id]/build` | Under-construction view: live build DAG, per-asset verification badges, two-level progress bar, **Build** (if <100%) / **Rebuild** trigger. (Reuses PLATFORM_REBUILD §4–5 + SSE.) |
| **Consult** | `/clients/[id]/consult` | The chat interface (renamed from consume). |
| **Panchang** | `/clients/[id]/panchang` | Panchang personalized to this chart. |

Shared-access (granted) guests see Profile/Consult/Panchang; the Build button is hidden/disabled
for them (authz §3.4).

### §4.3 — Panchang multi-tenancy
Standalone Panchang landing = **general** (non-personalized). A **client dropdown** (the guest's
own charts; super-admin: all charts) personalizes it. Same dropdown pattern as the cockpit (§8.3).

### §4.4 — Consult-page controls (chat UI)
- **Remove** the response-depth selector ("deep study" / "brief") from the Consult UI — depth is
  no longer a user-facing toggle. (Claude Code: locate the exact control + its state/flag, e.g. a
  `mode`/`depth`/`panel_opt_in`-adjacent selector; confirm removal doesn't break the synthesis
  path that reads it.)
- **Keep + wire** the per-query **LEL availability toggle** (the button already exists): ON ⇒ query
  synthesis MAY read LEL as validation/grounding evidence; OFF ⇒ synthesis does not see LEL. This
  is a serve-time-only switch (§8.4), subordinate to the global cockpit data-source control.

---

## §5 — Two-pipeline isolation (architectural + implementation)

Target: the consult route becomes a **thin selector**; the two pipelines are sibling modules
behind one interface, sharing pre/post stages but never interleaving in an `if/else` body.

```
lib/pipelines/
  shared/          # auth+chart resolution, planner, B.11 floor, persistence, streaming, citations
    context.ts     # builds the QueryContext (principal, chart_id, plan, history, tools)
  single_pass/     # "Classic Marsys" — orchestrator one-shot synthesis
    index.ts       # implements QueryPipeline
  agentic/         # "Claude-style" — provider adapter + bounded tool loop
    index.ts       # implements QueryPipeline
  registry.ts      # selectPipeline(setting|flag) -> QueryPipeline
  types.ts         # QueryPipeline interface: run(ctx: QueryContext): AsyncIterable<DataPart>
```
- **Interface:** `QueryPipeline.run(ctx) -> stream of data_parts`. Both pipelines consume the
  same `QueryContext` and emit the same `data_parts`, so the route and UI are pipeline-agnostic.
- **Selection:** the "Classic Marsys / Claude-style" SettingsDropdown maps to a per-request
  pipeline id; `R11V2_USE_ADAPTERS` and `R11E_*_LOOP` flags move under §8 Command Center control.
- **Isolation guarantee:** a future change to one pipeline edits exactly one folder; the other
  is untouched. Each module owns its types, prompts, and tests. (This realizes the
  TARGET_ARCHITECTURE_REPORT §3.1 "two-pipeline architecture" intent, made physical.)
- **Migration is behaviour-preserving:** extract first (pure refactor, golden-transcript test
  that both pipelines produce identical output pre/post extraction), then evolve.

---

## §6 — MCP per-chart (multi-tenant tool surface)

Today MCP is single-native and tier-gated; target is parity with the web authz model, realized
**through the unified tool contract + gateway** of TOOL_PORTFOLIO_PLAN v1.3 (§7.5) — not a
separate MCP-only mechanism:
1. **`chart_id` is a first-class, required input in the shared tool contract** (TP Phase 2's Zod
   schema module). Both channels (MCP + portal agentic loop) inherit it; the `?? NATIVE_CHART_ID`
   fallback is removed once the data plane is keyed.
2. **The gateway's `invoke_tool` is the single per-chart authorization point** for BOTH channels:
   it resolves the principal (web session, or API key → principal), then calls the **one**
   `authorizeChartAccess(principal, chart_id, action)`. No grant/ownership → reject;
   `super_admin` → all charts. (This is also where TP's B.11 forced-first lives — one gateway,
   two guarantees.)
3. **No tiers.** Per TP v1.3 §0/§8 the `audience_tier` dimension is excised entirely: every key
   gets the same uniform tool contract and unredacted output. Access is governed by **role**
   (super_admin vs guest → portal surfaces) + **chart_grants** (which charts) — never by tier.
4. **Optional convenience:** an API key may carry a `default_chart_id`; an explicit `chart_id`
   overrides it; authz is always per-request, never assumed from the key alone.
Net: MCP, the portal agentic loop, and the web all reuse one identity+authz brain and one tool
contract — the tier subsystem that used to overlap with this is removed, not reconciled.

---

## §7 — Dovetail with the data/engine drafts (no duplication)

This North-Star **consumes** the three drafts; it does not restate them:
- **`PLATFORM_REBUILD_ARCHITECTURE`** supplies the multi-chart build platform: uniform
  `chart_id uuid`, the `charts` registry (we extend it with `owner_id` in §3.2), the
  `amjis-builder` DAG, per-asset verification, SSE progress (→ the Build page §4.2).
- **`DATA_LAYER_REBUILD_TARGET_SPEC`** supplies what each asset becomes (deterministic + computed
  salience) and the **serve-time synthesis panel** where interpretation now lives (→ Reasoning
  module §2.2; the "Rebuild" content rebuilds are its per-asset cutovers).
- **`FACT_ENGINE_PYJHORA_BRIEF`** supplies the JH-equivalent L1 engine (no LLM in compute path;
  validate once vs JH golden fixture). This is the dependency root: nothing above L1 rebuilds
  until L1 passes the JH gate.
- **`TARGET_ARCHITECTURE_REPORT`** supplies the tech-debt deletions + the two-pipeline intent
  realized in §5 + coverage targets.

The **one alignment edit** between this doc and PLATFORM_REBUILD: its `charts` registry gains
`owner_id` and a sibling `chart_grants` table (multi-guest, not just multi-chart).

---

## §7.5 — Tool Portfolio convergence (TOOL_PORTFOLIO_PLAN v1.3)

The Tool Portfolio transformation and this multi-tenant refactor are **mutually reinforcing**,
with one genuine reconciliation (tiers). Integration points:

- **Unified tool contract = where `chart_id` lives.** TP's shared Zod schema module (Phase 2) is
  the single place to make `chart_id` a required tool input, inherited by both the MCP server and
  the portal agentic loop. Multi-chart tenancy and the unified contract land together, not twice.
- **Gateway = the per-chart authorization chokepoint.** TP's `invoke_tool` gateway (Phase 5),
  which already hosts the single B.11 forced-first guarantee, is the natural home for
  `authorizeChartAccess()` — one enforcement point for chart-level access across both channels.
- **Tier excision RESOLVES an access-model overlap (not a conflict).** TP rips out `audience_tier`
  (Phase 8). The North-Star access model never needed tiers: portal-surface access = **role**
  (super_admin vs guest), data access = **chart_grants** (owner / grant / super_admin). Removing
  tiers leaves one coherent model. With the data layer becoming deterministic (DATA_LAYER spec),
  there is also nothing left to *redact* — the tier-based disclosure subsystem loses its reason to
  exist. **Sequencing constraint:** the multi-tenant authz (role + `owner_id` + `chart_grants`,
  Track A1) must be live **before or with** TP Phase 8 tier excision, so access control is never
  absent in between.
- **Pipeline isolation coordinates with the gateway.** The agentic ("Claude-style") pipeline is
  one of the two isolated pipelines (§5); TP's control-model-B widening (Phase 6) modifies *its*
  catalog via the gateway. The gateway therefore lives in `pipelines/shared/`, consumed by both
  pipelines — so isolate the pipelines first (or in the same arc) rather than adding another
  inline branch.
- **Command Center governs the unified gate set.** With tiers gone, the Command Center's access
  class (§8.2) governs **capability enablement** (which tools are on, per-key scopes) and
  chart-grant policy — not tier redaction. TP's gateway + manifest-generated catalog make the
  live tool set itself a first-class, governable surface.

Sequencing fit: TP **Phase 0/1** (hygiene + B.11 hotfix) are independent — ship immediately. TP
**Phase 2–3** (contract + dual-channel schema) should add `chart_id` to the contract so it lands
once. TP **Phase 5–6** (gateway + control-model-B) follow or accompany the pipeline isolation
(§5). TP **Phase 8** (tier excision) is gated on Track A1 (tenancy authz) being live.

---

## §8 — Command Center (runtime gate control plane)

The single biggest "lift it out of the shadows" win. Today behaviour is governed by scattered
`MARSYS_FLAG_*` env constants (`feature_flags.ts`), hardcoded thresholds, and `STACK_ROUTING`.
Target: a **DB-backed control plane** surfaced as a super-admin-only **Command Center** tab in
the Cockpit, governing all four gate classes the native confirmed.

### §8.1 — Gate registry + runtime config
```
gate_registry (static catalogue, in code):
  { key, class, scope, value_type, default, description, hot_reload: bool, danger: bool }
    class  ∈ { feature_flag, pipeline_threshold, model_routing, access_tier }
    scope  ∈ { global, per_chart, per_tier }

runtime_config (table, the live overrides):
  key text, scope_ref text NULL, value jsonb, updated_by text, updated_at timestamptz, PRIMARY KEY(key, scope_ref)

gate_change_log (table): every edit — who, when, old→new, reason. (audit + rollback)
```
`configService` (which already exposes `getFlag`) is extended to read `runtime_config` (cached,
invalidated on write) and **fall back to the env/code default** when no override exists. Env
stays the bootstrap default; the DB is the runtime authority. No redeploy to flip a gate.

### §8.2 — The five classes (concrete)
- **Feature flags:** `R11V2_USE_ADAPTERS`, `R11E_*_LOOP`, observatory/discovery flags, etc.
- **Pipeline thresholds:** citation-gate strictness, **B.11 holistic-read floor**, validator
  gates, retry caps, agentic-loop iteration cap (`LOOP_CONFIG_BY_PROVIDER`).
- **Model/provider routing:** `STACK_ROUTING` overrides (which provider+model serves
  planner_fast / synthesis primary+fallback per stack).
- **Access/capability gates:** which tools are enabled (global on/off) + optional per-key scopes +
  chart-grant policy. NOTE: audience *tiers* are removed (TOOL_PORTFOLIO_PLAN v1.3 §8); this class
  governs capability enablement, not tier-based redaction.
- **Data-source / retrieval-tool access:** each data asset (FORENSIC, MSR, CDLM, CGM, RM, UCN,
  **LEL**, panchanga, classical T0, ephemeris, …) is an enable/disable control; turning a source
  off disables the retrieval tools that depend on it — mapped via the manifest `data_dependency`
  field and enforced at the gateway / tool registry (not merely hidden in the UI). Super-admin
  only; global, with optional per-chart scope. LEL is the motivating case (§8.4).

### §8.3 — Multi-tenant cockpit
Cockpit gains a **chart/guest dropdown**; every cockpit view (activity, health, interventions,
sessions, registry, plan, **command center**) parameterizes by the selected `chart_id`.
`per_chart`-scoped gates are edited under the selected chart; `global` gates apply portal-wide.
Guardrails: typed validation, "reset to default", `danger:true` gates require a confirm step,
and every change writes `gate_change_log`.

### §8.4 — Data-source governance & the LEL boundary
A **Data Sources** panel in the Command Center governs every data asset, with LEL carrying an
extra, stricter rule:
- **Global switch (cockpit, super-admin):** each asset has an enable/disable control. Disabling a
  source removes it from retrieval for **all** clients by making its dependent retrieval tools
  unavailable at the gateway / tool registry — enforced, not cosmetic.
- **LEL build-exclusion (hard rule):** the Life Event Log is **never** consumed while building /
  churning the data layer. The deterministic assets (FORENSIC/MSR/CDLM/CGM/RM/UCN) are pure
  projections of birth-data + engine and must contain **zero** LEL-derived content (aligns with
  DATA_LAYER_REBUILD: data layer = deterministic; and with the Learning-Layer rule that held-out
  ground truth is sacrosanct). LEL is a **serve-time-only** input.
- **LEL at query synthesis (serve-time only):** LEL is offered to the synthesis step purely as
  validation / grounding evidence, gated by two controls in precedence order —
  1. **Global cockpit switch** (super-admin): OFF disables LEL for everyone and **cannot** be
     overridden per query.
  2. **Per-query chat toggle** (the existing button, §4.4): effective only when the global switch
     is ON; lets the user choose per query whether synthesis may use LEL.
- **Generalization:** the same global on/off applies to any data source; LEL merely adds the
  build-exclusion + synthesis-only semantics on top. The wiring is the manifest `data_dependency`
  graph: source → dependent retrieval tools → gateway enablement. This makes "what data the
  instrument is allowed to use" an explicit, auditable, runtime-governable surface.

---

## §9 — Migration roadmap

Two tracks run in parallel after Phase 1; the diagram shows the simplified linear arc.

**Track A — Portal / Tenancy refactor (near-term; what you're touching now):**
- **A0 — Refactor foundations (pure, behaviour-preserving):** extract the two pipelines (§5),
  establish `lib/pipelines/` seams, Consult rename (with API alias), module-boundary cleanup.
  Golden-transcript tests prove identical output pre/post.
- **A1 — Tenancy & Access:** `owner_id` + `chart_grants` + role `client`→`guest`, central
  `authorizeChartAccess()`, role-gated nav, chart switcher, sharing UI, thread `chart_id` through
  the ~2 hardcoded tools + MCP (§3, §4, §6). Backfill native as first owner; non-breaking.
- **A2 — Command Center + multi-tenant cockpit/panchang:** `gate_registry` + `runtime_config` +
  `configService` extension + Command Center tab + cockpit/panchang dropdowns (§8).

**Track B — Data / Engine rebuild (the deterministic arc; bigger, gated):**
- **B1 — JH Fact Engine (L1):** deterministic engine, validate vs JH golden fixture
  (FACT_ENGINE brief). Dependency root.
- **B2 — Deterministic data rebuild:** T1 structural facts + MSR/CDLM/CGM/RM/UCN-digest with
  computed salience; archive + per-asset replace (DATA_LAYER spec).
- **B3 — Autonomous build platform:** `amjis-builder` DAG, intake + geocode + tz, SSE, per-asset
  verification UX wired to the Build page (PLATFORM_REBUILD).

**Continuous — Hygiene:** TARGET_ARCHITECTURE_REPORT deletions, coverage to target, serve-time
synthesis panel becomes the sole interpretation site.

**Non-breaking discipline (all phases):** schema extended not reshaped; native chart re-homed
under its `owner_id`/`chart_id`; per-asset cutover behind validation; FK dependents enumerated
before any swap; one branch per stream, PR-to-main human-gated.

---

## §10 — For Claude Code: validation checklist (the handoff)

Validate each against HEAD and report findings + cost/risk before Cowork finalizes (v1.1):
1. Confirm `charts.client_id` semantics and every reader/writer of it (grep `client_id`); cost of
   `owner_id` rename + dropping per-chart Firebase user creation in `/api/clients`.
2. Confirm the exact consult-route branch (`R11V2_USE_ADAPTERS`) and enumerate every shared stage
   that must move to `pipelines/shared/`; verify a golden-transcript test is feasible for both
   pipelines.
3. Inventory ALL gates for the Command Center: grep `MARSYS_FLAG_`, `getFlag(`, `STACK_ROUTING`,
   `LOOP_CONFIG`, B.11 floor, citation/validator thresholds → produce the `gate_registry` seed.
   Flag any gate that cannot be hot-reloaded (`hot_reload:false`).
4. Confirm which retrieval tools still hardcode the native (expected: `query_signal_state.ts`,
   `muhurta_finder.ts`) and the full set of tables lacking `chart_id` (cross-check PLATFORM_REBUILD §1).
5. Confirm MCP server's principal resolution path and where `authorizeChartAccess` must be called.
6. Cost the `client`→`guest` role-value migration (CHECK constraint + every `role === 'client'`
   read, e.g. `dashboard/page.tsx`).
7. Identify every super-admin-gated surface and confirm `requireSuperAdmin()` covers page + API
   for Cockpit/Audit/Performance/AI Ops/Admin.
8. Confirm `configService` can be extended to read `runtime_config` without breaking callers.

---

## §11 — Open items for the native
- **Pipeline naming at code level:** `single_pass` / `agentic` proposed; confirm or rename.
- **`profiles` → `principals` table rename:** do it (clean) or keep physical name (cheap)? Decide
  after Claude Code costs it (§10.1).
- **Guest self-signup vs invite-only:** assumed invite/approve (current `access_requests`) until
  you say otherwise.
- **Command Center per-chart scope:** which gate classes are per-chart vs global-only (default:
  feature flags + routing = global; thresholds = per-chart-overridable).

---

## §12 — Provenance
Model-authored (Claude, Cowork), DRAFT, native-approval-gated. Grounded in direct code recon
(paths cited §1). Modifies nothing canonical. Unifies the three existing target DRAFTs and adds
the multi-guest RBAC / sharing / Command Center layer. To be validated by Claude Code against
live code, then finalized (v1.1) by the native.

---
artifact: BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0.md
canonical_id: BUILD_WORKFLOW_AND_TOOLING_DESIGN
version: 2.0
status: DRAFT (design for discussion — Cowork; modifies nothing canonical)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-02
authored_for: native (Abhisek Mohanty)
supersedes: BUILD_WORKFLOW_AND_TOOLING_DESIGN_v1_0.md
reads_with:
  - MARSYS_MASTER_ARCHITECTURE_v2_0.md (the L0–L5 stack this build experience constructs)
  - BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (the swarm that builds + guarantees each unit AND its tool)
  - INFRASTRUCTURE_INVENTORY_v1_0.md (GCP serve shells + cost)
grounded_in:
  - existing serve shells (NewClientForm, dashboard ClientCard, CockpitShell + LiveDependencyGraph
    + OverallProgress + TelemetryStrip + AssetTable, ConsumeChatV2)
  - existing build rail (builds / build_steps / build_events / build_checkpoints; SSE at
    /api/build/events/[buildId]; dispatcher.py cascade+resume; 5-ayanamsha parallel build_chart.py)
  - existing MCP tool family (query_chart_facts, query_signals, get_cgm_subgraph, query_rm_walk,
    holistic_bundle, temporal, timeline_query, log_prediction, lel_query, tool_health, data_coverage …)
changelog:
  - v2.0 (2026-06-02): Folds the 2026-06-02 conversation decisions: (1) the client = an ACCOUNT;
    full CRUD lifecycle; build/consume/resume at the user's convenience. (2) L0 = a ONE-TIME GLOBAL
    build done once by the native (with the GCP data infrastructure); every later user sees it green.
    (3) Project codename BRAHMA; per-layer Sanskrit+English lexicon; internal "L0–L5" jargon never
    shown externally. (4) Honesty gates are VOLUME-based (per chart × ayanamsha set; below the floor →
    amber). (5) Tools are BUILT FOR REAL IN PARALLEL with each layer's assets (no stubs) — code →
    deploy → generate → tool deployed → tested-against-fresh-data, all in one swarm arc. (6) Tool
    granularity = a three-tier taxonomy (per-asset primitives close to the source + a few composite
    capability tools + meta/ops), NOT one-tool-per-layer. (7) Modern LLM/agentic-tool standard baked
    in from the start (typed schema, MCP resource, provenance envelope, two transports, one registry).
  - v1.0 (2026-06-02): initial build-experience + stub-tooling design (superseded).
---

# Project Brahma — Build Workflow & Tooling Strategy — Design v2.0

## §A — The two "builds", and the account mental model

**Two senses of "build" (hold them apart):**
- **System-build (the swarm).** Constructing the *instrument* — writers, engine, schemas, renderers, **and
  retrieval tools** — in Antigravity under the Build-Guarantor Swarm Charter (Gate 0 Assess&Author → Code →
  Deploy → Runtime). Developer-facing, once per capability.
- **Chart-build (the product).** A *user* generating one native's data assets by running the Gaṇita→Phala
  pipeline for their chart. User-facing — the cockpit this document designs.

**The account mental model (native's framing, 2026-06-02).** A client is exactly like an **account on a
portal.** The birth coordinates + essentials are the account's defining data — you cannot have the account
without them. Once the account exists, *building* and *consuming* it are things the user does **at their
convenience**, in any order, repeatedly. So the product is ordinary account management with three verbs on
top: **build**, **resume**, **consume**.

**The seam between the two builds (unchanged, now stronger).** The system-build of a layer ships **both** the
layer's generation writers **and** its retrieval tools — and in v2 those tools are **built for real, deployed,
and tested in the same arc** (§L). "Build a layer" = generate-its-data + serve-its-data, proven together.

## §B — The Brahma lexicon (external naming)

The project is **Brahma**. Layers are never shown to users as "L0/L1/…": that is internal jargon. External
surfaces (cockpit, dashboard, consult) show **Sanskrit + English only.**

| Internal | Sanskrit (external) | English (external) | Meaning / why |
|---|---|---|---|
| L0 | **Brahmagyan** (Brahmajñāna) | Foundation | the global, absolute knowledge base every chart stands on |
| L1 | **Gaṇita** | Chart Facts | "the reckoning" — the computed mathematical chart |
| L2 | **Bodha** | Chart Intelligence | insight/comprehension — signals, graph, themes |
| L3 | **Kāla** | Temporal | time — how the chart activates over a life |
| L4 | **Phala** | Prediction | "the fruit/result" — the classical jyotiṣa word for predictions |
| L5 | **Mīmāṃsā** | Learning | reflective inquiry — calibration from outcomes |

The set above is **confirmed by the native (2026-06-02)** — Brahmagyan and Mīmāṃsā chosen over the considered
alternatives (Adhāra, Śikṣā). It **cascades** into MARSYS_MASTER_ARCHITECTURE, the cockpit copy, and the tool
registry's display names. (Internal code/docs may keep L0–L5 for precision; the rule is purely about
*external display*.)

## §C — The client lifecycle = account management (full CRUD)

The instrument must offer the ordinary account verbs, not just "build":

- **Create** — the birth-data form (`NewClientForm`, reused) creates the account/chart with 0 assets. Adds the
  **ayanamsha-set selector** (charter-flagged gap). Save persists; the user may leave and return any time.
- **Read / list** — the dashboard roster (`ClientRoster` / `ClientCard`) lists accounts with a build-state
  badge ("Not built" / "Gaṇita–Bodha · 40%" / "Complete") + health dot.
- **Edit** — correct birth data / rename / change the ayanamsha set. Editing birth data is consequential and
  changes everything downstream, so a birth-data edit **auto-cascades a full rebuild of the chart's entire
  stack (Gaṇita→Mīmāṃsā)** — no per-asset prompt. (Brahmagyan/L0 is global and unaffected — a birth-data edit
  cannot touch it.) The user confirms the edit once; the rebuild then runs end-to-end. (Decision: native
  2026-06-02.)
- **Delete** — **immediate, hard wipeout** of the account + all its assets on confirm. **No soft-delete, no
  retention window.** (Decision: native 2026-06-02.)
- **Build / Resume / Rebuild** — at the user's convenience: build from zero, **resume from halfway** (the
  `dispatcher.resume_build` skip-on-success path, surfaced), or rebuild a scope (whole / from-a-layer-down /
  one asset — the `dispatcher.rebuild_asset` cascade, surfaced).
- **Consume** — chat against whatever is built so far (§J).

Permissions stay on the existing `authorizeChartAccess` model (owner/super_admin = all; grantee = view).
Build/Edit/Delete are owner+super_admin only; grantees get read/consult.

## §D — Brahmagyan (L0): the one-time global foundation

L0 is **not** part of any user's chart-build. It is built **once, by the native (the first user)**, together
with the **GCP data infrastructure** that holds the whole system. Thereafter it is **global and green** for
everyone: every subsequent account sees Brahmagyan already complete and simply stands on it.

Concretely:
- The native runs a **one-time foundation build** (Brahmagyan assets: ephemeris, classical texts + index,
  ontology, rule base, concordance, daily almanac, remedy corpus) **plus** the infra stand-up (Cloud SQL +
  pgvector, GCS, Cloud Run jobs, embeddings) — per INFRASTRUCTURE_INVENTORY + the L0 design.
- Every later chart-build **skips L0**: the cockpit shows Brahmagyan as a permanent lit **bedrock band** with
  "global — already built", not a step anyone waits on.
- In the cockpit, the **only** account that ever sees Brahmagyan *building* is the native's first-run admin
  view; all client builds begin at Gaṇita (L1).

This cleanly separates "platform owner stands up the foundation once" from "users create + build accounts."

## §E — Entry paths → the build page (state-aware)

Both entrances converge on one state-aware build page:

```
CREATE PATH:  Dashboard → New Client → birth-data form (+ ayanamsha set) → Save → "Build" ┐
RESUME PATH:  Dashboard → client card (badge shows build state) → "Build" ─────────────────┤→ BUILD PAGE
                                                                                            (fresh|resume|rebuild)
```

- **Fresh** (0 assets): pre-flight — confirmed birth data, ayanamsha set, one action **"Begin build."**
- **Resume** (partial): shows what's green, highlights the stopped asset, **"Resume from Bodha."**
- **Rebuild** (complete / birth-data edited / engine_version bumped): **"Rebuild"** + scope picker.

## §F — The build page: the Layer Tower

**Mental model: a tower rising floor by floor, where each finished floor opens for business immediately.**
Default view for everyone; the existing force-graph DAG becomes a **Pro toggle** (super_admin/acharya). Zones:

1. **The Layer Tower (centrepiece)** — vertical bands, bottom-up: Brahmagyan (bedrock, always lit) → Gaṇita →
   Bodha → Kāla → Phala → Mīmāṃsā. Each band is *dim* (not started) / *animating* (building) / *amber* (built
   but below its gate — §K) / *lit* (verified). Assets appear as tiles inside their band as they finish.
2. **The Capability Ribbon** — beside each band, plain-language *what you can now do*, lit on verify:
   Gaṇita → "your full natal chart is computed — every divisional, dasha, and strength."
   Bodha → "patterns, contradictions, and life-themes are mapped."
   Kāla → "see how time activates this chart — convergence windows."
   Phala → "probabilistic predictions with explicit falsifiers."
   Mīmāṃsā → "this chart now contributes to (and benefits from) calibrated learning."
3. **The Asset Inspector** — click a tile → what it computed (row counts + sample), **provenance** (which
   upstream facts/signals it consumed), per-ayanamsha status, the **gate verdict** (volume + Sambandha +
   Pramāṇa + Darpaṇa), **and the asset's retrieval tool(s) + their live/health state**, plus per-asset
   Rebuild. Audit surface for acharya; collapses to "computed · verified" for a lay client.
4. **The Control Bar** — Begin / Pause / Resume / Rebuild (scope) / Cancel; ayanamsha sub-selection; "stop on
   first failure" vs "continue + report." (Reuses `BuildControlsBar`.)
5. **The Telemetry Strip** — current asset, queue depth, ETA, sidecar health, engine_version, build_id;
   failures here + on the failed tile, never silent. (Reuses `TelemetryStrip` with real values.)

UI/UX is built to **grade** on the existing design system/theme; the in-chat mockup illustrates the tower,
ribbon, legend, and inspector. (Actual front-end implementation is an Antigravity system-build task — Cowork
plans, Antigravity executes — and should follow the design system + any front-end design plugin available
there.)

## §G — Progressive functionality (what the user can do as it builds)

Additive — each verified layer unlocks actions, nothing already unlocked is removed:

| State | What the user can do |
|---|---|
| Pre-flight | confirm birth data, pick ayanamshas, start; read what the build will produce |
| Gaṇita building | watch facts populate; inspect each fact asset as it lands |
| **Gaṇita verified** | **Consult fact-level questions** (its tools are live); view the forensic render; export the sheet |
| **Bodha verified** | ask intelligence questions (themes, contradictions, evidence-strength); browse the signal graph + lenses |
| **Kāla verified** | ask time questions (convergence windows, period snapshots); scrub a life-timeline |
| **Phala verified** | request predictions with falsifiers + mitigations; run rectification; ask "best window to act" (Muhurta) |
| **Mīmāṃsā active** | log a prediction to the held-out ledger; record an outcome; watch calibration move the learning multiplier |
| Complete | "chart is alive" summary (N facts · M signals · K anchors · all gates green) → strong Consult CTA |

## §H — The autonomous workflow & its visual representation

**Dependency-gated, not time-gated.** Assets carry `depends_on`; the dispatcher releases an asset only when
its dependencies are verified-green — so the build flows Gaṇita→Bodha→Kāla→Phala because the *data*
dependencies force it, while independent assets within a layer (and the 5 ayanamshas) build in parallel.

**Event model (exists; we extend it).** The pipeline emits `build_events` per asset × ayanamsha × stage
(`compute→persist→verify→commit`) with status+percent; the SSE endpoint replays+tails; the cockpit already
consumes `node_added`/`edge_added`. We map these onto the tower: tile appears (compute) → fills (persist) →
gets a check (passes Gate-3 incl. its tool test) → when *all* a layer's assets+tools are green, **the band
lights, the ribbon entry unlocks, and the layer's tools are confirmed live.** A Lₙ→Lₙ₊₁ edge **pulses** when
the downstream asset starts consuming upstream output — continuity made visible (§I).

## §I — Layer-to-layer continuity (gate + data-read + online tool)

Three guarantees, not cosmetic:
1. **Completion contract** — a layer is "complete" only when every owned asset passes its `runtime_contract`
   gate (volume floor §K; Sambandha no-silent-stubs; Pramāṇa integrity; Darpaṇa render-coverage) **and** its
   tool passes its test against the fresh data.
2. **Data-handoff substrate** — Gaṇita writes the typed Fact Store + JSONL; Bodha reads Gaṇita → signals +
   graph; Kāla reads Gaṇita+Bodha → temporal fabric; Phala reads Bodha+Kāla → anchors+mitigations; Mīmāṃsā
   reads Phala (pre-outcome) + the isolated LEL (never the reverse). Declared as `depends_on`; gated on green.
3. **Continuity is visible and usable** — the pulsing edge (visible) + the verified layer's **live tools**
   (usable): the chat *and* the next layer's writers consume Lₙ through the same retrieval tools. Continuity
   is at once a gate, a data-read, and an online tool.

## §J — Build-as-you-go consumption

Because each verified layer's tools go live on verify, **Consult is progressively usable mid-build.** The
planner's available toolset = the set of verified layers; with only Gaṇita green it answers fact questions and
does **not** fabricate Kāla timing it can't ground. A "Consult now (Gaṇita)" affordance appears on verify; the
chat notes "still building — temporal & predictive answers unlock at Kāla/Phala," so partial capability is
honest. A clear upgrade over today's finished-chart assumption.

## §K — Honesty gates are volume-based

The native's rule: we have a **ballpark expected data volume per chart, as a function of the ayanamsha set
selected** (more ayanamshas → proportionally more rows). Each asset/layer carries a **minimum-volume floor**
in its `runtime_contract`. At build time:
- generated volume **≥ floor** AND structural gates pass → **green (lit)**;
- generated volume **< floor** (or a structural gate flags thin coverage — the 38%-of-v8.0 class) →
  **amber ("built but thin")**, with the shortfall named in the inspector (expected N rows for K ayanamshas,
  got M);
- a layer **does not light** until all its assets clear their floors + gates.

This makes under-production — the failure that already happened once — *impossible to ship silently*, and ties
the gate to a concrete, ayanamsha-scaled number rather than a vibe. (Floors are authored per asset in the
Contract Registry from the FORENSIC coverage benchmark + the expected per-ayanamsha multiplier.)

## §L — Tooling strategy (full implementation, built in parallel — no stubs)

**Decision (native, 2026-06-02): build the real tools + plumbing in parallel with each layer's assets — not
stubs.** The briefs exist; the parallel approach is more honest and closes the loop immediately.

**The build sequence per layer (one swarm arc):**
```
Racayitā drafts {writer + tool(s) + schema + resource + tests}
  → Śilpī builds both  → Review Swarm ×5 reviews both  (GATE 1: code)
  → Pratiṣṭhā deploys to BOTH amjis-web (portal) and amjis-mcp (MCP)  (GATE 2: deploy)
  → pipeline GENERATES the asset's data on production
  → Gate 3 tests: Sambandha/Pramāṇa/Darpaṇa on the data  +  the TOOL is called against that fresh data
  → layer lights only when data AND tools are green
```
So the cockpit's "tool live" is **real**, tested against the data it just generated. The order inside the arc
is forced: writer → generate → tool-tested-against-generated-data.

**Tool granularity = a three-tier taxonomy (NOT one tool per layer).** A layer like Bodha holds MSR (a
SQL-queryable signal store), CGM (a graph you traverse), CDLM (a linkage lookup), RM (a resonance walk) — four
genuinely different access patterns. One tool can't wrap them without a polymorphic, mode-switched schema the
LLM uses badly. Instead:

1. **Primitives — one per asset, co-built with the writer, sharing its schema (the "close to the source"
   tools).**
   - Gaṇita: `query_positions` · `query_divisional` · `query_dasha` · `query_strength` · `query_sensitive_points` · `query_panchanga` …
   - Bodha: `query_signals` (domain/valence/confidence/salience filters) · `cgm_subgraph` (graph ops) · `cdlm_lookup` · `rm_walk` · `query_remediation`
   - Kāla: `timeline_query` · `convergence_window` · `period_snapshot`
   - Phala: `event_anchors` · `mitigation_map` · `muhurta_finder` · `rectification`
   - Mīmāṃsā: `log_prediction` · `record_outcome` · `lel_query`
2. **Composite capability tools — a few, for common multi-asset intents** (fewer agentic round-trips):
   `holistic_bundle` (whole-chart-read B.11: MSR+CGM+CDLM+RM in one call), `temporal`, a Phala "outlook"
   bundle.
3. **Meta/ops — cross-cutting:** `tool_health` · `data_coverage` · trace/provenance.

This formalises (and re-bases onto the new assets) the tool family that **already exists** in the live MCP set.

**Modern LLM/agentic-tool standard — baked in from the first tool, not retrofitted:**
- **Typed JSON schema** per tool (clear capability name, typed args, self-describing typed result) designed
  for an LLM in an agentic tool loop.
- **An MCP resource per tool/asset** (the asset's schema + a small data dictionary the model can read), so the
  model understands the source it's querying.
- **A uniform provenance envelope** on every result: `build_id`, `ayanamsha`, the fact/signal IDs + rule/verse
  used, confidence, citations — B.3 derivation-ledger discipline at the tool boundary.
- **One registry, two transports.** A single canonical Tool Registry (id, serves_asset/layer, schema,
  resource, provenance contract, `channels:[mcp,portal]`, health) read by **both** the MCP sidecar and the
  internal portal `/api/chat` path. Authored once, exposed twice — never implemented twice.
- **Auth/tier** declared per tool (client/acharya/super_admin) and enforced at both transports.

**What was deferred in v1 is now in-scope:** real MCP + portal dispatch, auth/tier filtering, agentic-loop
integration, provenance population — all built per layer, in the layer's arc. There is no separate "plumbing
later" session; plumbing ships with the layer.

## §M — Leverage / break inventory

**Leverage as-is:** `NewClientForm`; dashboard `ClientRoster`/`ClientCard`/`BuildsInProgressCard`;
`CockpitShell` + `BuildControlsBar`/`OverallProgress`/`TelemetryStrip`/`AssetTable`/`LiveDependencyGraph`
(→ Pro view); the build rail (`builds`/`build_steps`/`build_events`/`build_checkpoints`; SSE;
`dispatcher.py` cascade+resume; 5-ayanamsha `build_chart.py`; emitters); the existing MCP tool family
(re-based); Firebase auth + `authorizeChartAccess`.

**Break / re-base:** `DAG_ORDER` legacy `A1..A14` → the L0–L5 asset set (+ Remediation, Muhurta, Relational,
Spatial); 4-column `L1/L2.5/L3/L4` layout → the **Layer Tower** (Brahmagyan bedrock + Mīmāṃsā band added);
chart_facts re-sourced from engine JSONL (kill the static-YAML bug); engine depth-fill (6 domains → enumerated
superset); status delivery **polling → push/SSE**; cockpit progress granularity aligned to the asset DAG;
JH-parity residue → FORENSIC-consistency; **add CRUD (edit/delete) + the one-time Brahmagyan/infra admin
build**; **external copy → Brahma lexicon (no L0–L5 shown)**; **tools built for real per layer (not stubbed)**.

## §N — Decisions taken (v2) + still open

**Taken (native, 2026-06-02):** account model + full CRUD · one-time global Brahmagyan/infra build · Project
Brahma + Sanskrit/English external lexicon (no internal jargon) · volume-based amber gates · **real tools
built/deployed/tested in parallel with each layer (no stubs)** · three-tier tool taxonomy · modern
LLM/agentic-tool standard from the start · grade UI on the existing design system.

**Proposed defaults (flag if you disagree):** Layer Tower default + DAG behind a Pro toggle · status delivery
upgraded to push/SSE (consistent with "no compromise") · Phala built as a **hybrid** (precompute the major
lifetime anchor set at build; compute narrow/ad-hoc windows lazily at query time) · Mīmāṃsā shown as a thin
"active/contributing" band rather than a per-chart build step.

**Resolved (native, 2026-06-02):** (1) L0 name = **Brahmagyan**; (2) L5 name = **Mīmāṃsā**; (3) birth-data
edit = **auto-cascade full-stack rebuild** (Gaṇita→Mīmāṃsā), single confirm; (4) delete = **immediate hard
wipeout, no retention**. Front-end is implemented in **Claude Code using its installed front-end design
plugins**, against the UI/UX spec authored in Cowork.

---

*End of BUILD_WORKFLOW_AND_TOOLING_DESIGN v2.0 — DRAFT for discussion, 2026-06-02. Project Brahma. Modifies
nothing canonical. Pairs with MARSYS_MASTER_ARCHITECTURE_v2_0 (what is built) + BUILD_GUARANTOR_SWARM_CHARTER
(how it's built + guaranteed, now including each asset's tools).*

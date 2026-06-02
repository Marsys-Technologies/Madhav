---
artifact: BUILD_WORKFLOW_AND_TOOLING_DESIGN_v1_0.md
canonical_id: BUILD_WORKFLOW_AND_TOOLING_DESIGN
version: 1.0
status: SUPERSEDED 2026-06-02 by BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0.md (folds in: account-management lifecycle + CRUD; one-time global Brahmagyan/infra build; Project Brahma Sanskrit lexicon; volume-based amber gates; parallel REAL tool build (not stubs); three-tier tool taxonomy). Retained as v1 record.
authored_by: Claude (Cowork) 2026-06-02
authored_for: native (Abhisek Mohanty)
reads_with:
  - MARSYS_MASTER_ARCHITECTURE_v2_0.md (the L0–L5 stack this build experience constructs)
  - BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (the swarm that guarantees each unit)
  - INFRASTRUCTURE_INVENTORY_v1_0.md (GCP serve shells + cost)
grounded_in:
  - existing serve shells (NewClientForm, dashboard ClientCard, CockpitShell + LiveDependencyGraph
    + OverallProgress + TelemetryStrip + AssetTable, ConsumeChatV2)
  - existing build rail (builds / build_steps / build_events / build_checkpoints tables; SSE at
    /api/build/events/[buildId]; dispatcher.py cascade+resume; 5-ayanamsha parallel build_chart.py)
purpose: >
  Design the end-to-end CHART-BUILD EXPERIENCE from the user's perspective — both entry paths
  (new-client form, saved-client dashboard card) converging on the build page — and the
  autonomous layer-by-layer build it visualises; plus the per-layer RETRIEVAL-TOOL strategy
  (two channels: MCP + internal portal; one registry; capability-over-primitives; provenance
  envelope) STUBBED now, fully plumbed in a later session. Leverages today's cockpit + SSE rail
  and re-bases the parts tied to the legacy A1–A14 DAG onto the v2 L0–L5 stack.
---

# Build Workflow & Tooling Strategy — Design v1.0

## §A — First, disambiguate the two "builds" (this frames everything)

The word "build" is overloaded in this project. The design only makes sense if we hold both senses apart:

- **System-build (the swarm).** Constructing the *instrument itself* — the writers, engine, schemas,
  renderers, and retrieval tools — in Antigravity, governed by the Build-Guarantor Swarm Charter (Gate 0
  Assess&Author → Code → Deploy → Runtime). This is done once per capability and is **developer-facing**.
- **Chart-build (the product).** A *user* creating a client and generating *that native's* data assets by
  running the L1→L5 pipeline for their chart. This is the **user-facing** experience this document
  designs — the cockpit, the layer-by-layer fill, the "consult as it builds" flow.

They meet at exactly one seam: **the system-build of layer Lₙ ships both Lₙ's generation writers *and*
Lₙ's retrieval tool.** So when the swarm "builds a layer," it delivers (a) the code that generates that
layer's assets at chart-build time, and (b) the tool that serves that layer's data to an LLM. That seam is
why the tooling strategy (§H) is part of this design, not a separate concern.

A note on L0: **L0 Foundation is global, built once for the whole instrument** (ephemeris, texts, rules,
concordance, remedy corpus). A user creating a chart does **not** rebuild L0 — they consume it. The
user-facing chart-build is therefore **L1 → L5** over the already-present L0. The cockpit shows L0 as a
permanent "foundation" base the chart stands on, not as a step the user waits for.

## §B — The user journey (two entrances, one room)

Both paths converge on the build page; the page adapts to the chart's current state (fresh vs resume).

```
ENTRANCE 1 — NEW CLIENT
  Dashboard → "New Client" → birth-data form (name, date/time/place→coords, tz, ayanamsha set)
            → Save  → chart row exists, 0 assets built
            → "Build"  ─────────────────────────────────────────────┐
                                                                      │
ENTRANCE 2 — SAVED CLIENT                                             ▼
  Dashboard → client card (shows build %: "Not built" / "L1–L2 · 40%") → "Build" → ► BUILD PAGE
            (card health dot already reflects how much is built)                      (state-aware:
                                                                                       fresh | resume |
                                                                                       rebuild)
```

What "state-aware" means on arrival:
- **Fresh** (0 assets): the page opens in *pre-flight* — birth data confirmed, ayanamsha set chosen,
  a single primary action **"Begin build."** Nothing is computing yet.
- **Resume** (partial — e.g., a prior build stopped at L2): the page opens showing what's already green,
  the failed/incomplete asset highlighted, and **"Resume from L2."** (The `dispatcher.resume_build`
  skip-on-success logic already exists — we surface it.)
- **Rebuild** (fully built, native wants a refresh, or engine_version bumped): **"Rebuild"** with a scope
  picker — whole chart, a single layer downward (cascade), or one asset (the cascade-invalidation in
  `dispatcher.rebuild_asset` already exists — we surface it).

The birth-data form gains one explicit field the charter flagged as a gap: **ayanamsha selection** (the 5
canonical set, default all). Everything else in `NewClientForm` is reused as-is.

## §C — The build page: mental model and zones

**Mental model: a tower rising floor by floor, where each finished floor is immediately open for business.**
Not a technical DAG by default (that's the pro view). The first-class metaphor is a **layer stack that
fills bottom-up**, and each layer, the moment it's verified-complete, *lights up a capability* the user can
use right then — even while higher layers are still under construction.

Five zones on the page:

1. **The Layer Tower (centrepiece).** A vertical stack: `L0 Foundation` (always lit, the bedrock) → `L1
   Chart Facts` → `L2 Intelligence` → `L3 Temporal` → `L4 Predictive` → `L5 Learning`. Each layer is a band
   that is *dim* (not started), *animating* (building — assets appearing inside it), *amber* (built but a
   verification gate flagged it thin/partial), or *lit* (verified complete). Within a band, the layer's
   assets appear as small tiles as they finish.

2. **The Capability Ribbon (the "why this matters" rail).** Beside each layer, a plain-language statement
   of *what you can now do* that lights up when the layer verifies. This converts abstract assets into user
   value and is the emotional spine of the experience:
   - L1 lit → "The full natal chart is computed — every divisional, dasha, and strength, across your
     chosen ayanamshas."
   - L2 lit → "Cross-domain patterns, contradictions, and life-themes are mapped."
   - L3 lit → "You can see how time activates this chart — convergence windows over the life."
   - L4 lit → "Probabilistic predictions with explicit falsifiers are available."
   - L5 → "This chart now contributes to (and benefits from) calibrated learning."

3. **The Asset Inspector (drill-down).** Click any asset tile → side panel: what it is, what it computed
   (row counts, a sample), its **provenance** (which upstream Lₙ₋₁ facts/signals it consumed), per-ayanamsha
   status, the **verification verdict** from the runtime gates (Sambandha dependency-completeness, Pramāṇa
   data-integrity, Darpaṇa render-coverage), and a per-asset **Rebuild**. This is the acharya/super_admin
   audit surface; for a lay client it collapses to a one-line "computed · verified."

4. **The Control Bar.** Begin / Pause / Resume / Rebuild (scope picker) / Cancel; ayanamsha sub-selection;
   "stop on first failure" vs "continue and report." (Reuses `BuildControlsBar`.)

5. **The Telemetry Strip (honest status).** Current asset computing, queue depth, ETA, sidecar health,
   `engine_version`, `build_id`. Failures surface here *and* on the failed tile — never silent.
   (Reuses `TelemetryStrip`; we replace its stubbed QPS/health with real values.)

A **Pro toggle** (super_admin / acharya) swaps the Layer Tower for the existing `LiveDependencyGraph`
force-graph DAG — the same events, rendered as the full dependency topology rather than the layer metaphor.

## §D — Progressive functionality: what the user can do *as it builds*

The point the native stressed — "what functionality should be made available as the build process goes on"
— answered layer by layer. Functionality is **additive**: each verified layer unlocks actions, and nothing
that was unlocked is taken away.

| When | State | What the user can do |
|---|---|---|
| Pre-flight | 0 assets | Confirm birth data, pick ayanamshas, start; read what the build will produce |
| During L1 | L1 building | Watch facts populate; inspect each fact asset (positions, vargas, dashas, strengths) as it lands |
| **L1 verified** | L1 lit | **Open Consult for fact-level questions** ("show my D9", "current dasha") — L1 tool is live; view the forensic render; export the chart sheet |
| During L2 | L2 building | See signals + the signal graph forming over the facts (edges from L1 tiles pulse) |
| **L2 verified** | L2 lit | Ask intelligence-level questions (themes, contradictions, strengths-of-evidence); browse the signal graph + lenses (domain/resonance/concordance) |
| **L3 verified** | L3 lit | Ask time questions (convergence windows, period snapshots); scrub a life-timeline |
| **L4 verified** | L4 lit | Request probabilistic predictions with falsifiers + mitigations; run birth-time rectification; (Muhurta) ask "best window to act" |
| **L5 active** | L5 | Log a prediction to the held-out ledger; record an outcome; see calibration begin to move the learning multiplier |
| All lit | complete | "Chart is alive" summary (N facts · M signals · K anchors · all gates green) → strong Consult CTA |

The headline UX consequence: **the user does not wait for the whole build to start getting value.** The
instant L1 verifies, Consult works for L1 questions. This is the build-as-you-go principle (§G) and it is
only possible because each layer's retrieval tool comes online when the layer verifies (§H).

## §E — The autonomous workflow & its visual representation

How the build actually proceeds, and how the page renders it — reusing today's `build_events` SSE rail.

**Order of construction (dependency-gated, not time-gated).** Assets carry `depends_on`. The dispatcher
only releases an asset when its dependencies are verified-green. So the build flows L1 → L2 → L3 → L4
because the data dependencies force that order — and within a layer, independent assets build in parallel
(and across the 5 ayanamshas in parallel, as `build_chart.py` already does). The visual must show **both**
the strict layer progression *and* the parallel fan-out inside a layer.

**The event model (already exists, we extend it).** The pipeline emits `build_events` rows per asset ×
ayanamsha × stage (`compute → persist → verify → commit`) with status + percent. The SSE endpoint replays
+ tails them; the cockpit already consumes `node_added` / `edge_added`. We map these onto the Layer Tower:
- asset enters `compute` → its tile appears in the layer band, animating;
- asset `persist` complete → tile fills;
- asset passes its **Gate-3 runtime checks** → tile gets a verified check; when *all* of a layer's assets
  are verified, the **layer band lights and its Capability Ribbon entry unlocks** (and its retrieval tool
  flips live — §H);
- a dependency edge from Lₙ to Lₙ₊₁ **pulses** when the downstream asset begins consuming the upstream
  output — this is continuity made visible (§F).

**Phase/layer transitions.** Between layers, a brief "handoff" beat: the completing layer's output tiles
emit edges up into the next band, which then begins animating. The Telemetry Strip's "now building" cursor
moves up the tower. No modal, no full-page reload — a continuous, legible rise.

**Honesty about gates.** A built-but-thin asset (e.g., render coverage below contract — the
38%-of-v8.0 lesson) goes **amber, not green**, with the failing gate named in the inspector. The layer does
not light until its gates pass. This bakes the project's anti-silent-failure discipline into the UX.

```
        ┌──────────────────────────────────────────────────────────────┐
  L5 ░░░ │ Learning            (held-out · multiplier)        ▢ dim      │
  L4 ░░░ │ Predictive          [anchors][mitigation][muhurta] ◐ building │  ← "now building" cursor
  L3 ███ │ Temporal     ✓      [timeline][convergence][snap]  ● LIT      │ → Ribbon: "see time activate…"
  L2 ███ │ Intelligence ✓      [MSR][graph][lenses][remed.]   ● LIT      │ → Ribbon: "patterns mapped"
  L1 ███ │ Chart Facts  ✓      [pos][vargas][dashas][bala]…   ● LIT      │ → Ribbon: "natal chart ready"
  L0 ▓▓▓ │ Foundation          (global — always present)      ◆ bedrock  │
        └──────────────────────────────────────────────────────────────┘
            edges between bands pulse as Lₙ₊₁ consumes Lₙ's output
```

## §F — Layer-to-layer continuity (the contract the native asked about)

"How seamlessly one layer moves to the next… the output of one layer being available for the next to take
forward." Three guarantees make this real, not cosmetic:

1. **The completion contract.** A layer is "complete" only when every asset it owns passes its
   `runtime_contract` acceptance gate (Sambandha: all dependency-satisfied assets actually built — no
   `"…_not_computed"` sentinels; Pramāṇa: data-integrity; Darpaṇa: render coverage). Completion is a
   *verified* state, not "the writer ran."

2. **The data-handoff substrate (who reads what).** Continuity is concrete reads, declared as `depends_on`:
   - L1 writes the **typed Fact Store + canonical JSONL artifact**.
   - L2 reads L1's facts (in-memory at build time, DB at query time) → emits signals + the signal graph.
   - L3 reads L1 facts + L2 signals → emits the temporal fabric.
   - L4 reads L2 signals + L3 fabric → emits event anchors + mitigations.
   - L5 reads L4 predictions (before outcome) + the isolated LEL (never the reverse) → scoring + multiplier.
   The dispatcher gates each release on the upstream gate being green, so a downstream asset can *never*
   start against missing/thin input.

3. **The continuity is also visible and usable.** Visible: the pulsing edge when Lₙ₊₁ begins reading Lₙ.
   Usable: when Lₙ verifies, its **retrieval tool goes live**, so the chat (and the next layer's writers,
   which can call the same retrieval primitives) can consume Lₙ immediately. Continuity is therefore three
   things at once — a *gate*, a *data read*, and an *online tool*.

## §G — Build-as-you-go consumption

Because each verified layer lights its retrieval tool, **Consult is progressively usable mid-build.** The
chat's available toolset is exactly the set of layers verified so far. If only L1 is green, the planner has
L1 tools and answers fact questions; it does **not** fabricate L3 timing it can't yet ground. As layers
light, the chat silently gains reach. Two UX affordances:
- a "Consult now (L1)" button appears on the build page the moment L1 verifies;
- the chat shows a subtle "this chart is still building — temporal & predictive answers unlock at L3/L4"
  note, so partial capability is honest rather than confusing.

This is a meaningful upgrade over today, where Consult assumes a finished chart.

## §H — Tooling strategy (stub now, plumb later)

The native's instruction: design the tooling layer at a broad level now — channels (MCP + internal portal),
how the LLM reaches the retrieval tools — and **stub it**; a dedicated session does the full plumbing.

**The five pillars (most already decided; restated as the build target):**

1. **One canonical Tool Registry.** A single source of truth: one entry per tool with `tool_id`,
   `serves_layer/asset`, capability description, input/output schema, the **provenance-envelope** contract,
   `channels: [mcp, portal]`, and `state: stub | live`. Authored once; both transports read it. (This is
   the antidote to the historical drift where MCP and portal tool lists diverged.)

2. **Two transports, one definition.** (a) **MCP server** (`amjis-mcp` sidecar) for external/agentic
   clients; (b) **internal portal API** (the `/api/chat` consult tool-calling path). A tool is written once
   and *exposed twice* — never implemented twice. The client is **always an LLM in an agentic tool loop**,
   so tools are designed for model consumption (clear capability, typed args, self-describing results).

3. **Capability tools over primitives.** One **capability tool per layer/asset** (e.g., L1
   `query_chart_facts` + the divisional/dasha family; L2 `query_signals` / `holistic_bundle`; L3
   `temporal` / `timeline_query`; L4 the event-anchor/prediction tool + `muhurta_finder`; L5 `log_prediction`
   / `lel_query`), each composed of primitives underneath. The model calls the *capability*, not the
   plumbing. **Many of these tools already exist** (the live MCP set includes `query_chart_facts`,
   `query_signals`, `holistic_bundle`, `temporal`, `timeline_query`, `log_prediction`, `lel_query`, …) — so
   we **reuse the names/shapes and re-base their backing data onto the v2 L0–L5 assets**, breaking the ones
   bound to the legacy A1–A14 model.

4. **Uniform provenance envelope.** Every tool returns data *plus* provenance: the `build_id`, `ayanamsha`,
   the fact/signal IDs and the rule/verse it used, confidence, and citations. One envelope shape across all
   tools, so the LLM (and audit) can always trace an answer to its grounds (B.3 derivation-ledger discipline
   at the tool boundary).

5. **Per-layer tool lifecycle tied to the build.** This is the seam from §A: when the swarm system-builds
   layer Lₙ, the same contract entry names Lₙ's retrieval tool; Racayitā drafts both writer and tool; the
   tool ships **as a stub** alongside the asset. At chart-build time, when Lₙ verifies, its tool flips
   `stub → live` for that chart. So the registry's `state` field is what the cockpit reads to show "L2
   retrieval tool: registered (stub)" → "live."

**What "stub now" concretely means this phase (no full plumbing):**
- author the **Registry schema + one entry per layer tool** (id, schema, channels, provenance envelope,
  `state: stub`);
- ship a **thin stub handler** per layer tool that validates args and returns a typed "registered — not yet
  serving" envelope (or serves the new asset if already built);
- record, per tool, **which channel(s)** it will expose on and the auth/tier rule — *declared, not wired*.

**What the later "tooling session" does (explicitly deferred):** real MCP registration + internal dispatch,
auth/tier filtering, agentic-loop integration, the provenance-envelope population from live queries, and the
retire/alias of legacy tools. The build cockpit only needs the `state` flag to tell the truth in the
meantime.

## §I — Leverage / break inventory (the standing strategy: reuse, then break what's misaligned)

**Leverage as-is (reuse):**
- `NewClientForm`, dashboard `ClientRoster` / `ClientCard` (build-% + health dot), `BuildsInProgressCard`.
- `CockpitShell` and its children `BuildControlsBar`, `OverallProgress`, `TelemetryStrip`, `AssetTable`,
  `LiveDependencyGraph` (becomes the Pro view).
- The build rail: `builds` / `build_steps` / `build_events` / `build_checkpoints` tables; SSE at
  `/api/build/events/[buildId]`; `dispatcher.py` cascade-invalidate + resume; 5-ayanamsha parallel
  `build_chart.py`; the `emit_step_event` / `node_added` / `edge_added` emitters.
- The existing MCP tool family (re-based, not rebuilt).
- Firebase auth + per-chart `authorizeChartAccess` (all/view/deny).

**Break / re-base (misaligned with v2):**
- **DAG content:** `DAG_ORDER` = legacy `A1..A14` → the v2 **L0–L5 asset set** (+ Remediation, Muhurta,
  Relational, Spatial). The cockpit's 4-column `L1/L2.5/L3/L4` layout → the **L0–L5 Layer Tower**.
- **chart_facts bug:** re-source A3 from the **engine JSONL**, not the static GCS YAML (identical-for-every-
  client bug). 
- **engine depth-starvation:** the engine's ~6 returned domains → the **enumerated superset** contract, so
  synthesis layers stop stubbing/recomputing.
- **status delivery:** `/api/build/active` 10s **polling → push/SSE** for build status, not just graph
  events (the cockpit can show stale progress today).
- **progress granularity:** align the cockpit's progress model to the **asset DAG** (charter §B open item).
- **JH-parity residue:** rename Pramāṇa "JH Oracle Parity" / `native_oracles` → **FORENSIC-consistency**.
- **layer count:** add the **L0 bedrock band** and an **L5 band** the legacy cockpit never modelled.

## §J — Open questions to discuss (decisions before the build briefs)

1. **Layer Tower vs DAG as default.** I propose the Layer Tower default for all users, DAG behind a Pro
   toggle for super_admin/acharya. Agree, or do you want the DAG primary for your own use?
2. **Where does L4 sit at chart-build time?** L1–L3 are deterministic and fast. L4 (predictive ensemble)
   depends on learned weights that start ~neutral. Do we build L4 anchors at chart-build, or compute them
   lazily at query time? (Affects whether L4 is a "layer that builds" or a "capability that's always on.")
3. **L5 in the tower.** L5 is mostly ongoing/cross-corpus, not a per-chart build step. Show it as a thin
   "active/contributing" band rather than a thing that "builds"? 
4. **How live is live.** Is push/SSE for status worth doing now, or is 10s polling acceptable for v2 and
   push deferred?
5. **Tool granularity per layer.** One capability tool per layer, or per major asset within a layer
   (e.g., L1 splitting facts vs dashas vs divisionals)? Affects the registry size and the model's tool-menu.
6. **Stub depth.** Should layer tool stubs *serve real data the moment the asset exists* (so build-as-you-go
   works immediately), or strictly return "registered" until the dedicated tooling session? I lean toward
   "serve if built, else registered" so §G works in v2.

## §K — What this design commits to building now vs deferring

**Now (this re-architecture phase):** re-base the cockpit onto the Layer Tower + L0–L5 asset set; the
Capability Ribbon; the Asset Inspector with gate verdicts; state-aware entry (fresh/resume/rebuild);
ayanamsha field on the form; the **Tool Registry schema + one stub entry + thin stub handler per layer
tool**, with channels + provenance envelope **declared**.

**Deferred to the dedicated tooling session:** full MCP + portal plumbing, auth/tier filtering,
agentic-loop integration, provenance population, legacy-tool retire/alias.

**Deferred to system-build execution (the swarm):** the actual writers/engine-depth-fill/wiring per the
Build-Guarantor Swarm Charter and the Contract Registry.

---

*End of BUILD_WORKFLOW_AND_TOOLING_DESIGN v1.0 — DRAFT for discussion, 2026-06-02. Modifies nothing
canonical. Pairs with MARSYS_MASTER_ARCHITECTURE_v2_0 (what is built) and BUILD_GUARANTOR_SWARM_CHARTER
(how it's guaranteed); this doc is the user-facing how-it-feels + the tooling-stub strategy.*

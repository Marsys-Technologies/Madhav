---
artifact: BRAHMA_BUILD_UX_SPEC_v1_0.md
canonical_id: BRAHMA_BUILD_UX_SPEC
version: 1.0
status: DRAFT (implementation-ready UI/UX spec — Cowork-authored; built in Claude Code via its front-end design plugins)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-02
authored_for: native (Abhisek Mohanty)
reads_with:
  - BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0.md (the experience this spec renders)
  - MARSYS_MASTER_ARCHITECTURE_v2_0.md (the L0–L5 stack)
  - BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (gates whose verdicts the UI surfaces)
  - existing design system / VISUAL_CONTRACT (the theme this spec extends — do not re-invent tokens)
implements_decisions:
  - Brahma lexicon (Brahmagyan · Gaṇita · Bodha · Kāla · Phala · Mīmāṃsā); no L0–L5 shown externally
  - account-management model + full CRUD; birth-data edit = auto-cascade full rebuild; delete = hard wipeout
  - one-time global Brahmagyan/infra build (native only); all later accounts see it green
  - volume-based amber gates; Layer Tower default + DAG Pro toggle; push/SSE live status
  - real per-layer tools surfaced (live/health state in the inspector)
build_target: >
  Claude Code, using its installed front-end design plugins, implements this against the existing Next.js
  serve shells (NewClientForm, dashboard, CockpitShell + children, ConsumeChatV2). Cowork authors; Claude
  Code executes.
---

# Project Brahma — Build Experience UI/UX Spec v1.0

## §0 — Principles & non-negotiables

1. **Brahma lexicon only, externally.** Every user-visible string uses Sanskrit + English from §B of the v2
   design (Brahmagyan/Foundation, Gaṇita/Chart Facts, Bodha/Chart Intelligence, Kāla/Temporal, Phala/
   Prediction, Mīmāṃsā/Learning). The strings "L0".."L5", asset codenames (A1, MSR, CGM…), and engine/swarm
   jargon **never** appear on a client-facing surface. (Pro/super-admin surfaces may show codenames.)
2. **Honesty over polish.** A thin/under-volume asset shows **amber "built but thin"** with the exact
   shortfall; a failed asset shows the failing gate. Never a green that overstates.
3. **Value-first, not DAG-first.** The default mental model is the rising **Layer Tower** + the Capability
   Ribbon ("what you can now do"); the technical dependency graph is a Pro toggle.
4. **Extend the existing design system.** Reuse the project's theme tokens, type scale, spacing, and the
   `CockpitShell` component family. This spec defines *behavior, states, copy, and layout* — not new tokens.
5. **Accessible + responsive.** Keyboard-navigable, screen-reader labelled, prefers-reduced-motion honored,
   works from a wide desktop down to a narrow tablet column.

## §1 — Screen map

| # | Screen | Route (existing) | Primary job |
|---|---|---|---|
| S1 | Dashboard / account roster | `/dashboard` | list accounts, CRUD entry, build-state at a glance |
| S2 | Create account (birth-data form) | `/clients/new` | create the account; pick ayanamsha set |
| S3 | Edit account | `/clients/[id]/edit` (new) | edit data/name/ayanamshas; warn → auto-cascade rebuild |
| S4 | Build page — Layer Tower cockpit | `/clients/[id]/build` | the core build experience (all states) |
| S5 | Asset Inspector (panel within S4) | — | drill into an asset: data, provenance, gates, tools |
| S6 | Consult | `/clients/[id]/consult` | chat; progressively capable as layers verify |
| S7 | Brahmagyan admin build (super-admin only) | `/admin/foundation` (new) | the one-time global L0 + infra build |

## §2 — S1 Dashboard / account roster

**Layout.** Header ("Your charts" + "New chart" primary button) → responsive card grid (reuse
`ClientRoster`/`ClientCard`). Super-admin also sees the `BuildsInProgressCard` strip.

**Account card (`ClientCard`).**
- Line 1: chart name + a **state chip**:
  - `Not built` (neutral) · `Building — Bodha · 41%` (amber, animated dot) · `Built · all verified` (teal
    check) · `Attention — Kāla thin` (amber) · `Failed — Phala` (red).
- Line 2: birth date · birth place.
- Line 3: a 6-segment **layer pip rail** (Brahmagyan always filled as bedrock; Gaṇita…Mīmāṃsā fill as
  verified; amber pip = thin; dim = not built) — a compact echo of the tower.
- Health dot (existing) reflects the worst non-green gate.
- Row actions (kebab): **Open · Build/Resume · Consult · Edit · Delete**.

**CRUD behavior.**
- **New chart** → S2.
- **Edit** → S3.
- **Delete** → confirm dialog (see §8 D2): immediate hard wipeout, no retention; card disappears on success.
- **Build/Resume** → S4 (state-aware).
- Grantees (view tier) see **Open · Consult** only (no Build/Edit/Delete), per `authorizeChartAccess`.

## §3 — S2 Create account (birth-data form)

Reuse `NewClientForm`; treat it as **account creation** ("Create chart" not "Build now"). Fields: full name,
preferred name, gender, birth date, birth time, birth place (Places autocomplete → lat/lon), timezone (IANA),
and the **ayanamsha-set selector** (the 5 canonical; default all selected; min 1). Inline validation on coords
+ time. Primary action **"Create chart"** → persists → returns to S1 with a toast: "Chart created. Build it
now?" with a **Build** affordance (deep-links to S4 fresh). Creation never auto-builds.

Microcopy: explain the ayanamsha choice plainly ("Ayanamsha sets the zodiac reference. More selections = a
richer, cross-checked build, and a larger chart."). No layer jargon.

## §4 — S3 Edit account

Same form as S2, pre-filled. A persistent banner: **"Editing birth details will rebuild this entire chart
(Gaṇita → Mīmāṃsā) from scratch."** On save of any birth-affecting field, a single confirm (§8 D1) → persists
→ triggers a **full auto-cascade rebuild** → routes to S4 in *building* state. Editing only the name/notes
(non-astrological) does **not** trigger a rebuild. Ayanamsha-set changes rebuild only the added/removed
ayanamsha branches where possible, else full.

## §5 — S4 Build page — the Layer Tower cockpit (the centrepiece)

### 5.1 Frame
Reuse `CockpitShell`. Top bar: chart name + a state-aware subtitle (`fresh` / `resume` / `rebuild` /
`building` / `complete` / `attention`), and right-aligned controls: **Pause · Resume · Rebuild▾ · Cancel ·
Pro/DAG toggle** (reuse `BuildControlsBar`). Below: the **Telemetry Strip** (reuse `TelemetryStrip`): now
building · overall % · gates summary · sidecar health · build_id (codenames only in Pro).

### 5.2 The Layer Tower (reuse/extend `OverallProgress` + new `LayerTower`)
Vertical stack, **bottom-up**, 6 bands:

```
Mīmāṃsā / Learning        (thin "active" band — not a per-chart build step)
Phala / Prediction
Kāla / Temporal
Bodha / Chart Intelligence
Gaṇita / Chart Facts
Brahmagyan / Foundation   (bedrock — global, always lit, labelled "already built")
```

**Band anatomy (left → right):**
- **Name block** (fixed width): Sanskrit (primary, 500) + English (secondary) + a **state glyph**
  (dim circle / animating loader / amber dot / teal check).
- **Asset tile row**: one tile per asset in that layer; tiles appear/animate/fill/check as events arrive
  (§6). Amber tile = thin (volume below floor). Click a tile → S5 inspector.
- **Capability Ribbon** (right): the "what you can now do" line; **dim until the band verifies, then lights**
  with a bolt glyph and (for Gaṇita+) a **"Consult now"** affordance.

**Band states:** `dim` (not started) · `building` (animating; "now building" cursor sits here) · `amber`
(built but a volume/coverage gate flagged it; band does **not** count as verified) · `lit` (all assets +
their tools verified). The cursor rises as layers complete.

**Brahmagyan band** renders permanently lit with copy "Foundation — already built for every chart" and is
**non-interactive** for clients. (It only ever animates in S7, the admin one-time build.)

**Mīmāṃsā band** renders as a slim always-present "Active — this chart contributes to calibrated learning"
band, not a thing that fills 0→100%.

### 5.3 Pro / DAG toggle
Flips the tower for the existing `LiveDependencyGraph` force-graph (same SSE events, full dependency topology,
codenames allowed). Super-admin/acharya only. State persists per user (localStorage on the client — N/A in
artifacts, but fine in the real app).

### 5.4 Build-state variants of S4
- **Fresh** (0 assets): tower all dim above Brahmagyan; a single hero action **"Begin build"**; pre-flight
  summary (birth data + ayanamsha set + "this will produce ~N facts across K ayanamshas").
- **Building**: live tower (§6); Pause/Cancel enabled.
- **Resume**: green bands shown; the stopped asset pulsed amber/red; hero action **"Resume from {Layer}"**.
- **Rebuild**: a scope picker (Whole chart · From {Layer} down · One asset); confirm if it discards verified
  data.
- **Complete**: a **"Chart is alive"** summary card (N facts · M signals · K anchors · all gates green) +
  strong **"Open Consult"** CTA; tower fully lit.
- **Attention** (any amber/red after a run): a banner naming the thin/failed layer with a **"View"** → S5.

## §6 — Animation & event binding (push/SSE)

Bind to the SSE rail at `/api/build/events/[buildId]` (upgrade `/api/build/active` polling → push). Event →
UI mapping:

| Event | UI effect |
|---|---|
| `node_added` (asset enters `compute`) | tile appears in its band, **animating** (pulse) |
| stage `persist` complete | tile **fills** (solid) |
| `edge_added` (downstream begins consuming) | the Lₙ→Lₙ₊₁ connector **pulses** once |
| asset passes Gate-3 (incl. tool test) | tile gets a **teal check** |
| asset volume < floor / coverage thin | tile → **amber**, shortfall tooltip |
| all assets+tools in a layer verified | band **lights**, ribbon entry unlocks, "Consult now" appears |
| asset/build `failed` | tile → **red**, Telemetry + Attention banner |

**Motion:** subtle and continuous — no modal between layers; the "now building" cursor glides up; bands
cross-fade dim→lit. Honor `prefers-reduced-motion` (swap pulses for static state changes). Per-ayanamsha
progress shown as small rings inside a tile (reuse `OverallProgress` ring style).

## §7 — S5 Asset Inspector (panel)

Opens as a right-side panel (desktop) / full-sheet (narrow). Contents:
- **Header**: asset display name (Sanskrit-layer + plain asset name; codename in Pro only) + state glyph.
- **What it computed**: row counts (per ayanamsha), a small sample table.
- **Volume gate**: `expected ≥ {floor} for {K} ayanamshas · got {M}` → green/amber with the shortfall.
- **Provenance**: which upstream facts/signals it consumed (chips linking to those assets) — the visible
  derivation ledger.
- **Verification**: Sambandha (dependency-complete) · Pramāṇa (integrity) · Darpaṇa (render-coverage) — each
  a pass/fail chip.
- **Retrieval tools**: the asset's tool(s) with **live/health** state (e.g., `query_signals · live · tested ✓`),
  channels (`mcp · portal`), and a "last tested against this build" timestamp — this is where the
  built-in-parallel tools surface to the user.
- **Actions**: **Rebuild this asset** (cascade-aware) · **Open in Consult** (deep-link a relevant question).

Lay-client mode collapses the panel to a single line: "Computed · verified" (+ amber/red note if relevant).

## §8 — Dialogs & destructive confirms

- **D1 — Edit-rebuild confirm**: "Rebuild {chart}? Editing birth details rebuilds the entire chart from
  scratch (Gaṇita → Mīmāṃsā). Current results will be replaced." [Cancel] [Rebuild]. Non-destructive-looking
  but consequential → primary is deliberate, not default-focused.
- **D2 — Delete confirm**: "Delete {chart} permanently? This immediately and irreversibly wipes the chart and
  all its data. There is no recovery." Require typing the chart name (or a hold-to-confirm) → [Delete] in a
  danger style. No "archive" option (no retention, per decision).
- **D3 — Cancel build**: "Stop the build? Verified layers are kept; you can resume later." [Keep building]
  [Stop].

## §9 — S6 Consult, progressively capable

- A **"Consult now"** entry appears the moment Gaṇita verifies (on the band + as a card action).
- The chat shows a subtle capability note while building: "This chart is still building — temporal and
  predictive answers unlock as Kāla and Phala complete." Remove on completion.
- The planner's toolset = verified layers' tools; the UI never offers a prompt suggestion the current toolset
  can't ground (e.g., no "predict 2027" chip until Phala is live).
- Otherwise reuse `ConsumeChatV2` as-is (citations, trace drawer, etc.).

## §10 — S7 Brahmagyan admin build (super-admin / native only)

A separate, **one-time** surface (`/admin/foundation`) that builds the global Brahmagyan assets + stands up
the GCP data infrastructure. Same Layer-Tower idiom but single-band (Brahmagyan) with its sub-assets
(ephemeris, texts+index, ontology, rule base, concordance, daily almanac, remedy corpus) + an **Infrastructure
checklist** (Cloud SQL+pgvector, GCS, Cloud Run jobs, embeddings) with live status. Once verified, it is
**globally green forever** — and from then on every account's S4 shows Brahmagyan as a lit, non-interactive
bedrock band. This screen is effectively used once by the platform owner.

## §11 — Visual & motion tokens (extend the existing system)

- **State color semantics** (map to existing theme tokens): verified = success/teal; building/thin =
  warning/amber; failed = danger/red; not-started = neutral/gray; bedrock = a stable neutral-strong.
- Use existing radii, spacing scale, type scale; **two font weights** (regular/medium). Sentence case
  everywhere. No new shadows/gradients.
- Tiles: small rounded chips; bands: cards with a left state accent (full border, not single-side-rounded).
- Motion budget: ≤300ms transitions; pulse loops only on actively-building tiles; reduced-motion → instant.

## §12 — Accessibility

- Every band + tile has an `aria-label` reading "{Sanskrit} / {English} — {state}" and live-region updates on
  state change (so a screen reader hears "Bodha verified — chart intelligence ready").
- Keyboard: tab through bands → tiles → ribbon actions; Enter opens the inspector; Esc closes.
- Color is never the only signal — every state also has a glyph + text.
- Targets ≥40px; contrast meets WCAG AA on both light/dark themes.

## §13 — Data bindings (what feeds what)

| UI | Source |
|---|---|
| roster cards / build-state | `builds` + `build_steps` aggregate; `pyramid_layers` % (re-based to L0–L5) |
| tower live state | SSE `/api/build/events/[buildId]` (push); `build_steps` for resume snapshot |
| per-ayanamsha rings | `build_steps` rows (asset × ayanamsha) |
| inspector data/volume | the asset's table row counts + the contract's volume floor |
| inspector gates | Gate-3 verdicts (Sambandha/Pramāṇa/Darpaṇa) persisted per asset |
| inspector tools | the Tool Registry (`state`, `health`, `channels`, last-tested) |
| consult capability | the set of verified layers → available tools |

## §14 — Acceptance criteria (what "done" means for the front-end)

1. No client-facing surface shows "L0".."L5", asset codenames, or engine/swarm jargon — Brahma lexicon only.
2. Both entry paths (create → build; roster → build) land on a correct state-aware S4.
3. The tower updates live via push (no stale-progress refresh needed) and renders fresh/building/resume/
   rebuild/complete/attention correctly.
4. An under-volume asset renders amber with the exact shortfall; its layer does not light.
5. The inspector shows data + provenance + gate verdicts + **live tool state tested against this build**.
6. Birth-data edit → single confirm → full-stack rebuild; delete → hard wipeout with no recovery path.
7. Consult becomes available at Gaṇita and gains reach as layers verify; offers no ungroundable suggestions.
8. Brahmagyan renders as global bedrock for clients and only builds on the admin one-time screen.
9. Fully keyboard/screen-reader accessible; reduced-motion honored; AA contrast in light + dark.

---

*End of BRAHMA_BUILD_UX_SPEC v1.0 — DRAFT, 2026-06-02. Cowork authors the spec; Claude Code implements it with
its front-end design plugins against the existing serve shells. Pairs with BUILD_WORKFLOW_AND_TOOLING_DESIGN
v2.0.*

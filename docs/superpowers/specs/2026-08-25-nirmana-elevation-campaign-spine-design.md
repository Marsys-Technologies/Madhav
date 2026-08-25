---
title: Nirmāṇa Elevation Tracker — Campaign Spine Redesign
date: 2026-08-25
status: PENDING_WRITTEN_REVIEW
design_approval: APPROVED_IN_CONVERSATION
author: Abhisek Mohanty + Codex
register: product
surface: /admin/nirmana-elevation
governed_plan: 00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v6_0.md
supersedes_for_this_surface: current horizontal layer rail and default asset evidence ledger
does_not_supersede: docs/superpowers/specs/2026-06-29-nirmana-build-tracker-progress-design.md
---

# Nirmāṇa Elevation Tracker — Campaign Spine Redesign

## 1. Decision

Redesign the authenticated Nirmāṇa elevation tracker as an operational campaign cockpit organized
around the governed execution sequence:

`BOOTSTRAP → T0_CENSUS → PLAN_FROZEN → DENOMINATOR_FROZEN → F0_FOUNDATION → L0 → L1 → L2 → L3 → L4 → L5 → CLOSING → COMPLETE`.

The sequence is vertical. An expanded L0–L5 layer presents its topological waves vertically because
the waves are sequential. Assets that the frozen DAG permits to execute concurrently appear
horizontally within their wave. This makes the primary spatial model match the plan: vertical means
“must follow”; horizontal means “may run in parallel.”

The current horizontal six-column layer rail and default full-width asset evidence ledger are
removed from the primary operational canvas. Audit evidence remains available on demand.

This specification applies to `/admin/nirmana-elevation` and its evidence projection. It does not
replace the older client cockpit build-progress design for `/clients/[id]/nirmana`; the two surfaces
serve different jobs.

## 2. Problem

The current elevation tracker exposes technically accurate fragments in an unproductive hierarchy:

1. L0–L5 appear as horizontal peers even though the frozen plan requires strict sequential
   execution.
2. BOOTSTRAP, T0_CENSUS, PLAN_FROZEN, DENOMINATOR_FROZEN, F0_FOUNDATION, CLOSING, and COMPLETE are
   absent as first-class stages.
3. The current-wave board lists identifiers but does not let a viewer expand the campaign from
   stage → wave → asset.
4. The asset evidence ledger dominates the page even though evidence is primarily an audit concern.
5. Asset progress does not consistently answer what has completed, what is happening now, what is
   blocked, and what comes next.
6. Bare layer and asset identifiers force the viewer to remember catalogue codes.
7. The current snapshot has one `display_name`, sourced from `asset_registry.english_name`; it does
   not preserve canonical ID, Sanskrit name, English name, description, and legacy aliases as
   separate governed identity fields.
8. The snapshot hard-codes a coarse campaign status (`foundation` after definition freeze) instead
   of projecting the complete state machine from earned receipts.

## 3. Goals and non-goals

### 3.1 Goals

- Make the governed sequence immediately legible.
- Preserve the DAG distinction between sequential waves and parallel assets.
- Give an executive snapshot without hiding freshness, blockers, or uncertainty.
- Make each stage, layer, wave, and asset expandable and collapsible.
- Show earned progress for every asset without estimated or manually entered percentages.
- Show canonical layer and asset names wherever their identifiers appear.
- Show canonical asset ID, Sanskrit name, English name, and a short English functional description.
- Identify what is active, what is blocked, what has completed elevation, and what becomes eligible
  next.
- Keep raw evidence, receipts, ledger rows, and release provenance available but secondary.
- Preserve authentication, authorization, auditability, append-only evidence, and honest degraded
  states.

### 3.2 Non-goals

- No change to L0–L5 ordering, topological waves, execution obligations, or dependency rules.
- No manual tracker-owned progress or status edits.
- No revival of the historical A1–A22 catalogue as the v6 execution identity model.
- No unauthenticated access and no relaxation of the super-admin route boundary.
- No alteration of the chart-build orchestrator or frozen Nirmāṇa execution plan.
- No large interactive DAG canvas as the primary interface. A graph may remain an optional audit or
  exploration view later, but is not required by this redesign.

## 4. Naming and identity contract

### 4.1 Governed stage names

The tracker uses the state-machine names exactly. It does not introduce P0, P1, or P2 aliases.

### 4.2 Layer names

Layer code and canonical name always travel together:

| Code | Canonical name | Display form |
|---|---|---|
| L0 | Brahmagyan | `L0 · Brahmagyan` |
| L1 | Ganita | `L1 · Ganita` |
| L2 | Bodha | `L2 · Bodha` |
| L3 | Kala | `L3 · Kala` |
| L4 | Phala | `L4 · Phala` |
| L5 | Mimamsa | `L5 · Mimamsa` |

This form is used in the campaign spine, breadcrumbs, filters, search results, “now and next,”
blocker text, and audit details. On a narrow screen, the name wraps below the code; it is not
silently removed.

### 4.3 Asset identity

Every asset presentation has four distinct fields:

1. `asset_id` — the current canonical v6 registry identity, such as `ka_smriti`.
2. `sanskrit_name` — the canonical Sanskrit/transliterated name, such as `Kala Smriti`.
3. `english_name` — a compact English name, such as `Per-varsha digest`.
4. `description` — one plain-language sentence explaining what the asset produces or provides.

Compact cards show the first three plus a shortened description. Expanded cards show the complete
description. A missing governed label is rendered as `Not yet catalogued`; the tracker never
invents a translation or silently substitutes a plausible label.

### 4.4 Legacy aliases

Historical aliases such as `A22 · Varsha-Darshan · Yearly Vision` may appear only when an explicit,
verified mapping exists. They are labelled `Legacy alias`, rendered with subdued visual weight, and
never used as the v6 execution key. Dependencies, events, progress, and links continue to use the
canonical v6 `asset_id`.

### 4.5 Versioned label catalogue

Asset labels are not embedded as ad hoc UI constants and do not silently depend on mutable live
registry text. Introduce an append-only `nirmana_elevation_asset_labels` catalogue keyed by:

- `campaign_id`
- `definition_revision`
- `catalogue_revision`
- `asset_id`

Each label record carries nullable `sanskrit_name`, nullable `english_name`, nullable `description`,
verified `legacy_aliases`, `source_ref`, `recorded_at`, and a deterministic label digest. A
campaign-scoped `asset_label_catalogue_accepted` receipt selects one complete catalogue revision and
its digest for a definition. Corrections append a higher catalogue revision and a new acceptance
receipt; update and delete are prohibited. Label revisions do not mutate the frozen manifest or its
execution digest. The existing `asset_registry.english_name` is an ingestion source and may be shown
temporarily as an `unversioned_fallback`, not as an unmarked second authority in the rendered
snapshot.

Layer names remain a six-entry application constant because they are defined by the frozen plan,
not per-asset mutable catalogue data.

## 5. Information architecture

### 5.1 Executive snapshot

The top strip contains at most five operational measures:

1. **Current position** — exact stage; when applicable, layer and wave.
2. **Overall elevation** — `assets_frozen / assets_total` only when the denominator is frozen;
   otherwise `Reconciling — no percentage`.
3. **Active now** — count of assets with an accepted active run state.
4. **Next unlock** — count of assets eligible in the next wave after the named gate clears.
5. **Freshness** — age and observation time of the newest authoritative snapshot.

Release divergence, data-quality degradation, or stale data appears as a compact warning directly
under this strip. Detailed release metadata does not consume a permanent metric tile.

### 5.2 Vertical campaign spine

Render all state-machine stages in one ordered vertical accordion. Each stage header includes:

- exact governed name;
- state: `completed`, `active`, `locked`, `blocked`, or `unknown`;
- truthful summary count where a denominator exists;
- expand/collapse affordance;
- a visible connector to the next stage.

The current stage opens by default. Other stages remain collapsed unless the user opens them. The
UI remembers manual expansion for the current page session but never treats an open panel as an
execution-state change.

Completed stages remain inspectable. Locked stages explain the prerequisite that keeps them locked.
Unknown stages do not appear as pending or green.

### 5.3 BOOTSTRAP through F0_FOUNDATION

Pre-layer stages use the same spine geometry as L0–L5 rather than a separate summary widget.

- T0_CENSUS expands to definition, denominator, manifest, and DAG acceptance checkpoints.
- F0_FOUNDATION expands to lanes A–E from the frozen plan: asset/DAG census, run/progress truth,
  hash/invalidation, tracker/release, and evidence control.
- A foundation lane receives a progress signal only when typed acceptance receipts define its
  required checkpoints. Otherwise the lane is `unknown`, not an estimated percentage.

PLAN_FROZEN and DENOMINATOR_FROZEN remain separate visible stages even when they completed close
together. This preserves the actual state machine and makes the denominator gate understandable.

### 5.4 L0–L5 expanded layer

An expanded layer contains:

1. layer-level bar: frozen assets divided by the layer’s frozen denominator;
2. status legend: `Frozen`, `Active`, `Blocked`, `Eligible next`, `Locked`, `Unknown`;
3. sequential wave stack, ordered by `wave_index`;
4. asset cards arranged horizontally within each wave on desktop;
5. explicit prerequisite text on locked waves;
6. a collapsed summary for completed waves;
7. a preview of the next wave’s eligible assets.

On mobile, parallel asset cards stack vertically inside their wave. Their membership in one wave,
not horizontal scrolling, communicates concurrency.

### 5.5 “Now, next, then” rail

Desktop layouts include a compact secondary rail:

- **Now** — active wave and active/blocked counts.
- **Next** — assets that become eligible after the current named gate.
- **Then** — next wave or next layer.
- **Attention** — blockers, stale data, source failures, or release divergence.

On narrow screens, this rail becomes a section above the campaign spine.

### 5.6 Audit drawer

Evidence references, immutable receipts, run IDs, timestamps, source provenance, deployed revision,
main/deployed SHA comparison, contradictions, and raw ledger details move into an `Audit details`
drawer. The drawer remains reachable from the page and from each expanded asset, but it is closed by
default.

The audit drawer must not become a second editable tracker. It only projects evidence.

## 6. Asset lifecycle progress

### 6.1 Six lifecycle positions

Each asset card uses a segmented bar with these visible positions:

1. **Analysed**
2. **Decision accepted**
3. **Built / dispositioned**
4. **Deployed and executed / accepted**
5. **Verified**
6. **Frozen**

The labels are executive descriptions of accepted evidence, not free-form task estimates.

### 6.2 Required, earned, current, and not applicable

Each milestone has one of four states:

- `earned` — its required acceptance event exists and is valid for the frozen definition;
- `current` — prior required milestones are earned and work is actively evidenced here;
- `pending` — required but not earned;
- `not_applicable` — the frozen execution obligation does not require this milestone.

Progress is:

`earned required milestones / total required milestones`.

`not_applicable` segments remain visible as hatched or muted positions and are excluded from the
denominator. A milestone is never auto-earned merely to make the bar look complete.

### 6.3 Obligation-specific mapping

- `build`: analysis, decision, implementation when the accepted decision requires a change,
  accepted post-deploy execution, integrity verification, and freeze. A no-change decision marks
  implementation `not_applicable` only when its accepted decision receipt says so.
- `probe`: analysis, decision, accepted probe, integrity verification, and freeze; implementation
  is required only when an accepted change exists.
- `producer_covered`: show inherited execution explicitly and link to the producer. It does not
  pretend to have executed independently.
- `static_acceptance`, `source_acceptance`, `empty_acceptance`, and
  `retired_with_disposition`: show the accepted disposition in the third position; execution is
  `not_applicable` unless that obligation’s contract requires an observed run.
- `unresolved`: no percentage and no eligible-next claim; show `Blocked — unresolved obligation`.

The projection layer normalizes obligation-specific campaign events into these display milestones.
It does not change the underlying event receipts.

### 6.4 Live sub-progress

When an active execution reports a real unit denominator, the expanded asset may show a subordinate
live bar such as `640 / 1,000 units`. If the total is unknown, the subordinate bar is indeterminate
and text explains the current instrumented stage. Unit progress never substitutes for lifecycle
acceptance.

### 6.5 Asset disclosure

An expanded asset answers, in this order:

1. What is this asset?
2. Where is it in the campaign?
3. Which lifecycle milestones are earned?
4. What is happening now?
5. What happens next?
6. What blocks it or which assets does it unlock?
7. Which producer covers it, if applicable?
8. Where are its audit details?

`Frozen` is the canonical completion state. The plain-language supporting label may read
`Elevation complete`; `Elevated` is not introduced as a competing lifecycle value.

## 7. Snapshot contract and projection

### 7.1 Contract version

The structural change is a new snapshot contract version rather than an ambiguous extension of
`schema_version: 1.0`. The API and client move together to `schema_version: 2.0`. During deployment,
the client may render the existing v1 tracker for a valid v1 snapshot until the v2 projection is
available; it must not parse v1 data as v2.

### 7.2 New stage projection

Add `campaign.stages`, ordered exactly as the frozen state machine. Each stage contains:

- `stage_id`
- `order`
- `state`
- `required_gate`
- `completed_at`
- `blocked_reason`
- optional determinate `earned` and `required` counts
- stage-kind details for T0, F0, layer, or closing stages

Current position comes from the latest valid campaign-scoped stage-transition receipt. An accepted
active run may corroborate that position only when the receipt-defined prerequisites agree. If no
valid position evidence exists, current position is `unknown`; the server does not guess by choosing
the first incomplete-looking stage. The projection must not infer completion from code presence,
row presence, a green deployment, or an open accordion.

### 7.3 Layer projection

Extend each layer with:

- `layer_name`
- normalized layer state and prerequisite
- frozen denominator and frozen count
- sequential waves
- `eligible_next_asset_ids`

Eligibility is derived from the frozen DAG, prior-layer freeze, prior-wave completion, execution
obligation, and blocker state. It is not manually populated by the UI.

### 7.4 Asset projection

Replace the ambiguous single display name with:

- `asset_id`
- `sanskrit_name`
- `english_name`
- `description`
- `legacy_aliases`
- `identity_quality`
- normalized lifecycle milestones
- current action and next action, only when derived from typed state
- dependency and unlock summaries
- existing execution, timing, blocker, producer, run, and evidence fields

The API may retain `display_name` during the v1 compatibility window, but v2 components do not use
it as a substitute for the bilingual identity contract.

### 7.5 Stage evidence

Campaign-scoped accepted receipts provide state for BOOTSTRAP, T0, F0, CLOSING, and COMPLETE.
Existing definition status provides denominator evidence but is not, by itself, proof that every F0
lane completed. L0–L5 completion continues to derive from valid per-asset freeze evidence and strict
ordering.

If an older completed step lacks a typed receipt, v2 shows it as `unknown` until a governed
backfill/acceptance receipt is written through the existing audited ingress. The UI does not
grandfather historical prose into a green stage.

## 8. Data flow

1. The authenticated snapshot route loads the frozen campaign definition, campaign events, live
   registry contracts, build/run state, release reconciliation, and the versioned label catalogue.
2. The server validates definition and event provenance before deriving stages, milestones,
   eligibility, and quality verdicts.
3. The server emits one self-consistent v2 snapshot with generation digest and timestamps.
4. The client validates the v2 schema before replacing its last valid snapshot.
5. The client renders the operational hierarchy and keeps audit data collapsed.
6. Polling retains the existing visible/hidden/backoff discipline; opening or closing UI elements
   never writes campaign state.

The browser does not derive DAG eligibility independently. Server and tests own that logic so all
consumers receive the same result.

## 9. Freshness and failure behavior

- **Stale after a valid snapshot:** keep the last valid snapshot, freeze visual advancement, show
  observation time and a prominent stale warning.
- **Authoritative source unavailable:** mark affected stage, layer, asset, or whole projection
  `unknown`/`degraded`; do not interpret missing rows as zero work.
- **Invalid v2 payload:** retain the last valid snapshot and report contract failure.
- **No previous valid snapshot:** show a structured unavailable state, not an empty campaign.
- **Release divergence:** show a compact top warning and full detail in the Audit drawer.
- **Label catalogue incomplete:** preserve operational progress, mark identity quality incomplete,
  and show `Not yet catalogued`; do not fabricate names.
- **Contradictory receipts:** show the affected entity blocked or unknown, surface the contradiction
  in Attention and Audit details, and do not choose the more favorable interpretation.
- **Poll failure:** preserve exponential backoff, visibility-aware intervals, reconnect refresh, and
  request cancellation.

## 10. Component boundaries

Split the existing monolithic tracker into focused units:

| Unit | Responsibility |
|---|---|
| `NirmanaElevationTracker` | Fetch lifecycle, schema validation, last-valid snapshot, failure boundary |
| `CampaignSnapshotStrip` | Five executive measures and compact quality warnings |
| `CampaignSpine` | Ordered stage accordion and current-stage default expansion |
| `FoundationStage` | T0/F0 checkpoints and F0 lanes |
| `LayerStage` | Layer summary, sequential waves, and eligibility preview |
| `WaveLane` | Parallel asset-card layout within one sequential wave |
| `AssetCard` | Bilingual identity, milestone bar, compact status |
| `AssetDisclosure` | Current action, next action, dependencies, unlocks, producer coverage |
| `NowNextRail` | Now, next, then, and attention summaries |
| `AuditDrawer` | Evidence, receipts, provenance, release, contradictions, raw details |

Projection logic and milestone normalization remain in server-side library modules, not React
components. Shared layer naming and lifecycle vocabularies live in typed constants.

## 11. Visual and interaction contract

- Reuse the existing Marsys theme tokens: near-black ground, restrained gold ramp, cream text,
  system sans for UI, Cormorant/serif display, and monospace identifiers.
- Use 8-point spacing, 6px controls, 12px panels, gold hairlines, and restrained 150ms transitions.
- No purple, decorative gradients, oversized iconography, or continuous motion.
- The current stage receives the strongest gold emphasis; completed stages use a restrained success
  treatment; blocked and degraded states remain unambiguous.
- Accordions use native button semantics with `aria-expanded` and `aria-controls`.
- Every progress bar has a textual numerator/denominator and accessible label.
- Status is never conveyed by colour alone.
- Keyboard order follows stage → wave → asset → audit disclosure.
- Focus remains visible; reduced-motion preferences disable lift and animated progress treatments.

## 12. Testing strategy

### 12.1 Projection tests

- exact state-machine ordering;
- no skipped or retrograde stage progression;
- T0/F0 stage completion from accepted evidence only;
- strict L0→L5 and wave ordering;
- parallel eligibility only for dependency-satisfied assets in the current wave;
- no percentage before denominator freeze;
- obligation-specific required/earned/N/A milestone mapping;
- producer-covered inheritance without duplicate execution credit;
- contradictory or missing evidence produces unknown/blocked, not green;
- bilingual label catalogue resolution, fallbacks, digest, and legacy-alias rules;
- stable generation digest for semantically identical snapshots.

### 12.2 Component tests

- current stage auto-expands;
- manual stage expansion is local UI state only;
- layer and asset identifiers always render with available names;
- completed, active, next, blocked, locked, and unknown states have text labels;
- audit data is collapsed by default and keyboard reachable;
- mobile stacking preserves wave membership;
- textual progress matches visual segments;
- stale snapshot remains visible after a poll failure;
- invalid v2 does not replace the last valid snapshot.

### 12.3 Route and authorization tests

- unauthenticated and non-super-admin access remains rejected;
- authenticated v2 route returns no-store data satisfying the exact schema;
- unavailable-source responses remain typed and non-empty;
- no secret, credential, or private connection detail appears in payloads or errors.

### 12.4 Accessibility and responsive verification

- automated accessibility checks on the collapsed and expanded states;
- keyboard-only traversal of the full spine and Audit drawer;
- screen-reader labels for stage, milestone, and progress semantics;
- desktop, tablet, and phone layouts without clipped names or mandatory horizontal scrolling.

## 13. Rollout and compatibility

1. Land the versioned label catalogue and v2 projection behind server tests.
2. Populate labels only from governed sources; record missing-name gaps explicitly.
3. Land the v2 UI with temporary v1 fallback during the release transition.
4. Deploy through the existing protected PR and Cloud Run workflow.
5. Verify migration application, v2 snapshot contract, deployed revision, authenticated route, and
   responsive/accessibility behavior.
6. Remove the v1 UI fallback only after production v2 proof; this is a later cleanup, not required in
   the first safe release.

No existing frozen campaign definition is edited in place. Any backfilled campaign or milestone
evidence uses the existing authenticated, audited, idempotent ingress and requires its own governed
authority.

## 14. Acceptance criteria

1. The page renders the exact governed state machine vertically, including all pre-layer and closing
   stages.
2. Layer display names accompany L0–L5 everywhere.
3. An expanded layer renders waves vertically and parallel assets within each wave.
4. Each asset displays canonical ID, Sanskrit name, English name, and functional description or an
   honest missing-catalogue state.
5. Legacy A1–A22 aliases never replace current canonical IDs.
6. Each asset shows obligation-aware earned progress with N/A handling and no estimated percentage.
7. Expanded assets show current action, next action, dependencies, unlocks, producer coverage, and
   a secondary audit disclosure.
8. The page provides clear “now, next, then,” blocker, freshness, and release-divergence signals.
9. Raw evidence and ledgers no longer dominate the default view but remain fully reachable.
10. Unknown, stale, unavailable, and contradictory states never render as completed or empty.
11. Authentication and super-admin authorization remain unchanged.
12. Projection, component, route, accessibility, and responsive tests pass.
13. Deployment is not called complete until migration, v2 payload, deployed revision, and
   authenticated production rendering are independently verified.

## 15. Explicit implementation boundary

Approval of this specification authorizes implementation planning, not direct production mutation.
The implementation plan must identify the migration, snapshot-contract, projection, UI, test,
protected-PR, deployment, and authenticated smoke-test steps separately. No Nirmāṇa campaign
execution, build resumption, evidence backfill, or production-state change is implied by this UI
design.

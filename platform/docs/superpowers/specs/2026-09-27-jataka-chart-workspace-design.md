# Jātaka Chart Workspace and Safe Recompute — Design Specification

**Date:** 2026-09-27
**Status:** Approved for implementation planning
**Scope:** Local-first redesign of the Jātakas roster and chart page, plus a safe edit-and-recompute workflow for chart-defining birth details.

## 1. Goal

Turn the Jātakas dashboard into a quiet chart directory and make the existing
`/clients/[id]` route the durable home for one person's chart. The chart page must
show the D1/Rāśi chart, truthful computation readiness, and the actions that belong
to that chart—initially Nirmāṇa, Paripraśna, and Pañcāṅga, with space for later
capabilities.

Complete the currently unfinished edit feature so an authorised owner can correct
chart details and recompute the same chart safely. The user must no longer need to
delete a chart and create a replacement. A computation-affecting correction keeps
the chart identity and grants, archives prior conversations as historical material,
invalidates the old derived corpus, and starts a full recomputation.

This feature is local-first. No deployment, production mutation, or automatic
promotion is part of this specification.

## 2. Current-state findings

The codebase already contains several partial pieces, but they do not form a working
product flow:

- The dashboard card exposes Nirmāṇa and Paripraśna directly, so the chart-specific
  page is bypassed.
- `/clients/[id]` already exists and renders a D1/Rāśi chart, birth metadata, and
  several room cards, but its progress derives from the older `pyramid_layers`
  surface rather than the dashboard's authoritative `asset_throughput` data.
- `/clients/[id]/edit` and `EditClientForm` already exist, but the form submits to
  `PATCH /api/clients/[id]`; no such route exists.
- The form's confirmation copy promises a complete rebuild, but after a successful
  request it would only redirect to Nirmāṇa. It does not invalidate derived data or
  start a build.
- The active build endpoint is `POST /api/cockpit/runs`. Legacy endpoints under
  `/api/build/start` and `/api/build/rebuild-all` are decommissioned or non-operative
  and must not be used.
- Paripraśna's visual system is a strong, scoped Marsys implementation: black
  instrument surface, warm gold rules, Cormorant display type, restrained motion,
  and compact chart identity. The chart workspace should reuse these principles,
  not import chat-specific layout or full-viewport behaviour.

## 3. Product model

The product has two levels:

1. **Jātakas directory** — select a chart and see its computation readiness.
2. **Jātaka workspace** — understand and act on one chart.

The dashboard never serves as an action launcher. Nirmāṇa, Paripraśna, Pañcāṅga,
edit, sharing, audit, and future capabilities all live inside the selected chart's
workspace.

## 4. Jātakas directory

### 4.1 Grid cards

Each card contains only:

- chart-holder name;
- birth date and place on one quiet metadata line;
- the existing truthful progress bar and state label.

The complete card is a link to `/clients/[id]`. It has one semantic link target,
a visible keyboard focus state, and a restrained border lift on hover. It must not
contain nested links or buttons.

Remove from the grid card:

- Nirmāṇa and Paripraśna buttons;
- the moment phrase;
- edit/delete overflow controls.

Edit and deletion move to the chart workspace. This keeps the dashboard genuinely
minimal and prevents nested interactive targets inside a clickable card.

### 4.2 Table view

The table remains available for larger rosters. Each row opens `/clients/[id]` by
an accessible name link and supports keyboard navigation. Remove the `Actions`
column and both action buttons. Retain name, birth details, build percentage, and
last activity. The current empty `Current dasha` column should not remain as a
permanent placeholder; it is either populated from truthful data or removed in this
change. The bounded implementation should remove it unless an existing reliable
query can populate it without broadening scope.

### 4.3 Dashboard data contract

The dashboard continues to derive readiness from active `asset_registry`,
`asset_throughput`, and the latest active `build_runs` row. The card and table use
one shared readiness formatter so labels cannot drift between views.

## 5. Jātaka workspace

The existing `/clients/[id]` route is redesigned rather than replaced.

### 5.1 Identity and D1 hero

The first viewport is a composed two-column instrument surface:

- **D1/Rāśi chart:** the dominant visual element, using the existing
  `RasiChartSVG` component.
- **Chart identity:** chart-holder name, formatted birth date/time/place, Lagna,
  and a quiet `Jātaka` eyebrow.

On mobile, the D1 chart precedes identity details. The chart must remain readable
without horizontal scrolling.

### 5.2 Computation readiness

Immediately below the identity sits a single readiness band containing:

- global percentage;
- state label: Not built, Building, Partially built, Ready, Failed, or Needs rebuild;
- the six externally named layers: Brahmagyan, Gaṇita, Bodha, Kāla, Phala, Mīmāṃsā;
- last successful activity where available;
- active-run context when a build is in progress.

This surface uses the same server-side readiness resolver as the dashboard. The
workspace must stop querying `pyramid_layers` for its headline percentage.

### 5.3 Capability deck

The principal actions are a compact, extensible deck—not dashboard-style buttons:

- **Nirmāṇa** — construct, inspect, and maintain the chart corpus. Render only for
  `canBuild` users.
- **Paripraśna** — ask and explore this chart. Use `/clients/[id]/pariprashna`; the
  existing feature flag may continue to redirect to the legacy consult surface.
- **Pañcāṅga** — personalised daily timing.

Each capability card has a name, one-line purpose, state hint, and a single link.
Future features append to this deck without changing the directory.

When the chart is rebuilding or requires rebuilding, derived capabilities such as
Paripraśna are visibly unavailable and explain why. Nirmāṇa remains available so
the authorised user can inspect or retry the build.

### 5.4 At-a-glance material

Below the capability deck, show only already-grounded, useful summaries:

- current daśā, when present;
- confirmed active yogas, preserving verification distinctions;
- recent non-archived Paripraśna conversations;
- data freshness.

An unavailable value is omitted or explicitly marked unavailable; no placeholder
claim is invented.

### 5.5 Secondary controls

An understated overflow control in the chart identity area contains:

- Edit chart details;
- Sharing, where authorised;
- Audit, for super-admin;
- Delete chart, separated as destructive.

These controls are not equal in visual weight to the capability deck. View-only
grantees do not receive edit or delete controls.

## 6. Marsys and Paripraśna visual language

The workspace follows the Marsys ceremonial UI tier and borrows the strongest
Paripraśna patterns:

- jet-black base (`#000` / warm near-black raised panels);
- warm ivory text and the restrained Paripraśna gold family;
- one-pixel gold hairlines instead of large ornamental fills;
- Cormorant Garamond for display identity, system sans for controls, monospace only
  for technical state;
- 12px panels, 6px controls, no gratuitous gradients;
- quiet opacity/transform transitions with reduced-motion support;
- compact chart identity similar to Paripraśna's chart pin;
- no chat sidebars, composer patterns, fixed-viewport shell, or reading-specific
  provenance controls on the chart page.

Tokens should be scoped to the workspace tree or expressed through existing global
brand tokens. Paripraśna's `.pp-root` CSS must not be applied outside Paripraśna,
because it is deliberately isolated and includes full-instrument assumptions.

## 7. Edit and recompute semantics

### 7.1 Field classification

The server, not the browser, classifies the change after comparing normalised
stored and submitted values.

**Display-only:**

- name;
- preferred name or subject label, if exposed by the final form.

Display-only changes update the chart and return to the workspace without a build.

**Computation-affecting:**

- birth date;
- birth time;
- birth place;
- latitude and longitude;
- timezone identifier and effective offset;
- selected ayanāṃśas.

Any computation-affecting change requires a full per-chart Gaṇita → Mīmāṃsā
recomputation. The chart UUID, owner, grants, and share relationships do not change.

### 7.2 User interaction

The edit page groups fields into Identity, Birth coordinates, Time standard, and
Computation frame. It uses the chart-pin header and panel language derived from
Paripraśna.

For a display-only edit, the primary action reads `Save changes`.

For a computation-affecting edit, it reads `Save and recompute`. The confirmation
dialog shows:

- a before/after summary of changed fields;
- that previous computed results will be replaced;
- that existing Paripraśna conversations will be archived read-only;
- that the operation may take time and progress will remain visible.

The confirmation is specific and informational. It does not ask the user to delete
or recreate the chart.

### 7.3 Server endpoint

Implement the missing operation as `PATCH /api/charts/[id]`, keeping chart mutations
under the chart API rather than adding another `/api/clients/[id]` convention.

The endpoint must:

1. authenticate and require owner/super-admin build authority;
2. validate and normalise all inputs;
3. lock the chart row and reject an active build with HTTP 409;
4. compare stored and submitted values server-side;
5. return a no-op response when nothing changed;
6. apply display-only edits directly; or
7. execute the computation-affecting transaction described below.

The client-side `isBirthAffecting` helper is only a presentation hint. It is never
the authority for whether a rebuild is required.

### 7.4 Fail-closed recompute transaction

For computation-affecting changes, one database transaction must:

1. recheck that no build became active;
2. resolve the complete active per-chart writer plan;
3. reject the operation if any required per-chart asset is build-protected;
4. capture the old chart inputs for historical conversation context;
5. archive every active conversation for the chart with reason
   `chart_details_changed`, preserving its messages;
6. update the chart-defining inputs;
7. strictly invalidate and clear every chart-derived asset in reverse dependency
   order using the governed registry clear specifications;
8. reset chart-scoped throughput rows to dormant;
9. create a global `rebuild` run and its queued `build_run_assets` plan.

Unlike the operator cockpit's best-effort clear workflow, this correction path is
strict: any clear failure rolls back the conversation archival, chart update,
invalidation, and run creation. The original chart remains usable and unchanged.

Human-authored source material that is not a derived build asset—such as ownership,
grants, consent records, manually entered life events, and outcome observations—is
not erased by this operation unless an existing governed asset contract explicitly
classifies it as regenerated data. The implementation plan must enumerate and test
this preservation boundary before enabling the endpoint.

After commit, invoke the existing Cloud Run build job using the new run ID. Job
invocation cannot be part of the database transaction.

### 7.5 Dispatch failure

If the build job cannot start after the transaction commits:

- mark the run failed with the dispatch error;
- keep the corrected chart inputs;
- keep old derived results cleared;
- show `Needs rebuild` on the workspace;
- offer `Retry in Nirmāṇa`.

This is an honest degraded state. The application never serves old computations as
though they belonged to corrected birth details.

### 7.6 Historical conversation contract

When chart-defining inputs change:

- active conversations are archived, never deleted;
- their messages remain readable through archived-history access;
- archived history is read-only and cannot accept new turns;
- its UI clearly states that it belongs to chart details from before the correction;
- the old chart input snapshot and archive reason are retained with the conversation
  so the historical context is not reconstructed from the newly edited chart row;
- new conversations begin only after the recomputed chart becomes ready.

This requires a governed migration for conversation archive metadata, unless an
equivalent existing structured metadata surface is proven suitable during
implementation planning. The migration must be additive and idempotent.

## 8. Shared build service boundary

Do not duplicate the large orchestration body from `POST /api/cockpit/runs` inside
the chart edit route. Extract or introduce a server-only build preparation service
that both routes can call for:

- active-run guard;
- registry and protected-asset resolution;
- plan construction;
- strict or operator clear policy;
- throughput reset;
- build-run and build-run-assets creation;
- job invocation result handling.

The existing frozen Python orchestrator contract is unchanged. This refactor is a
Next.js server/API boundary around the already-governed build machinery, not an
orchestrator extension.

## 9. Error handling

- **401/403:** unauthenticated or insufficient authority; no mutation.
- **404:** chart not found or not visible to the caller.
- **409:** active chart build; edit form remains populated and explains that the
  correction can be retried when the run ends.
- **422:** invalid fields, protected required asset, or incomplete recompute plan;
  no mutation.
- **500:** transactional preparation failure; full rollback.
- **503:** metadata and invalidation committed, but job dispatch failed; workspace
  enters Needs rebuild and exposes the retry path.

All responses use structured error codes suitable for form and workspace messages.

## 10. Accessibility and responsive behaviour

- Entire grid cards have a visible focus ring and descriptive accessible name.
- No interactive element is nested inside a linked card or row link.
- All capability and secondary controls meet a 44px touch target on coarse pointers.
- Progress is conveyed through text and state, never colour alone.
- D1 chart SVG retains its descriptive accessible label.
- Confirmation dialog focus is trapped and returns to the triggering control.
- Reduced-motion and increased-contrast preferences are respected.
- Mobile order is D1 chart, identity, readiness, capabilities, summaries.

## 11. Testing strategy

### Unit and component tests

- grid card renders only name, birth line, progress, and one workspace link;
- table has no Actions column and each chart is reachable;
- readiness formatter produces identical states for directory and workspace;
- workspace capability permissions preserve `canBuild` behaviour;
- computation-affecting diff classification covers every governed input;
- confirmation shows exact before/after fields and archival notice;
- archived conversations render read-only with the historical-context notice.

### API tests

- display-only update performs no build work;
- unchanged request is idempotent;
- view-only grantee cannot edit;
- active build returns 409 without mutation;
- protected required asset returns 422 without mutation;
- strict-clear failure rolls back chart inputs and conversation archival;
- successful correction preserves chart UUID and grants, archives conversations,
  clears derived data, resets throughput, and creates one global rebuild plan;
- dispatch failure produces a failed run and honest Needs rebuild state.

### Integration and local browser proof

- open the local Jātakas page and verify cards/rows contain no direct actions;
- select a chart and verify D1, readiness, and capability deck;
- perform a name-only edit and verify no run is created;
- perform a test birth-detail correction on disposable local data and observe the
  full progress lifecycle;
- verify prior conversations move to archived read-only history;
- verify Paripraśna is unavailable until the corrected chart is ready;
- verify desktop, tablet, mobile, keyboard, reduced-motion, and high-contrast states.

No production-data correction is part of local acceptance.

## 12. Anticipated implementation surfaces

The implementation plan will confirm exact boundaries, but the expected surfaces
are:

- dashboard roster card/table and their tests;
- `/clients/[id]` page and focused workspace components;
- shared chart-readiness resolver;
- edit page, form, and recompute confirmation;
- `PATCH /api/charts/[id]`;
- server-only build preparation/refactor around `/api/cockpit/runs`;
- additive conversation archive metadata migration and archived-history enforcement;
- Paripraśna/read endpoints that must reject or render archived conversations as
  read-only;
- focused API, component, integration, and local browser tests.

## 13. Non-goals

- No change to the frozen Python orchestrator or writer contract.
- No new Jyotish computation or reinterpretation of existing facts.
- No production migration, data change, deployment, merge, or release.
- No redesign of the Paripraśna conversation instrument itself.
- No replacement of existing chart IDs or sharing grants.
- No deletion of historical conversations as part of chart correction.
- No blue/green chart-revision subsystem in this first implementation; the strict
  invalidate-and-rebuild flow is the bounded safe solution for the current schema.

## 14. Acceptance criteria

1. Dashboard grid cards and table rows open the chart workspace and contain no
   Nirmāṇa, Paripraśna, edit, or delete actions.
2. `/clients/[id]` visibly centres the D1/Rāśi chart, chart identity, truthful
   readiness, and an extensible capability deck.
3. Dashboard and workspace readiness use the same authoritative computation.
4. Nirmāṇa remains owner/super-admin only; view grants remain read-only.
5. The edit screen is reachable from the chart workspace and follows the approved
   Marsys/Paripraśna-derived visual language.
6. Name-only edits do not rebuild.
7. Any chart-defining input correction keeps the chart UUID and grants, archives
   old conversations read-only, invalidates old derived data, and creates one full
   recompute run.
8. A preparation failure rolls everything back; a post-commit dispatch failure is
   shown honestly as Needs rebuild with a retry path.
9. Old computations are never presented as belonging to corrected birth details.
10. Prior conversations remain recoverable as clearly historical, read-only material.
11. Focused automated tests pass and the complete flow is proven against disposable
    local data in a local browser.

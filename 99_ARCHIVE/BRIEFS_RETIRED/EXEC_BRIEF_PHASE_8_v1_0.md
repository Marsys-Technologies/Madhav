---
brief_id: EXEC_BRIEF_PHASE_8
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-27
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_8_v1_0.md and execute it."
phase: 8
phase_name: Audit View UI
risk_classification: LOW-MEDIUM
parallelizable_with: [EXEC_BRIEF_PHASE_7_v1_0.md, M2/B.5 work]
depends_on: [EXEC_BRIEF_PHASE_4_v1_0.md (COMPLETE), EXEC_BRIEF_PHASE_5_v1_0.md (COMPLETE)]
soft_depends_on: [EXEC_BRIEF_PHASE_6_v1_0.md (COMPLETE — checkpoint payloads render if present), EXEC_BRIEF_PHASE_7_v1_0.md (panel payloads render if present, but Phase 8 ships before Phase 7 completes)]
estimated_streams: 4
---

# EXEC_BRIEF — Phase 8 — Audit View UI

## Mission

Make the data Phase 4 persists actually inspectable. A new tab/route in the app — `/audit` — that lets the native (a) browse query history with filters; (b) inspect any individual query's full execution trace; (c) review open and closed predictions in `prediction_ledger`; (d) compare audit rows side-by-side when investigating drift or divergence.

Phase 8 is the discipline-stage surface for the human reviewer. Without it, Phase 4's audit rows are just JSONB blobs nobody reads.

The view must gracefully render rows from any combination of completed phases — Phase 4-only rows (just structural validators), Phase 6-augmented rows (with checkpoint payloads), and Phase 7-augmented rows (with panel payloads). Forward-compatible by design.

## Scope (`may_touch` / `must_not_touch`)

**`may_touch`:**
- `platform/src/app/audit/**` (new — page route, layout, sub-routes)
- `platform/src/app/api/audit/**` (new — read-only API endpoints for the audit views)
- `platform/src/components/audit/**` (new — list, detail, filter, prediction views)
- `platform/src/lib/audit/queries.ts` (new — read-only query helpers; sibling to existing `writer.ts`)
- `platform/src/lib/prediction/queries.ts` (new — read-only query helpers; extends existing `reader.ts`)
- `platform/src/components/audit/__tests__/**`
- New nav entry in the existing app shell (minimal — one new link in the existing nav component, no redesign)

**`must_not_touch`:**
- `platform/src/lib/audit/writer.ts`, `platform/src/lib/audit/consumer.ts`, `platform/src/lib/audit/types.ts` (Phase 4 writer surface frozen — Phase 8 reads only)
- `platform/src/lib/prediction/writer.ts` (Phase 4 frozen — Phase 8 reads only via reader extension)
- `platform/src/lib/synthesis/**`, `platform/src/lib/validators/**`, `platform/src/lib/prompts/**`, `platform/src/lib/disclosure/**`, `platform/src/lib/checkpoints/**`, `platform/src/lib/router/**`, `platform/src/lib/bundle/**`, `platform/src/lib/retrieve/**` (all frozen)
- `platform/src/components/citations/**`, `platform/src/components/disclosure/**`, `platform/src/components/consume/**` (Phase 5 territory — Phase 8 reuses these components, doesn't modify)
- `platform/python-sidecar/**`
- Any DB migration (read-only views; no schema changes)
- Any flag-OFF code path of Consume tab
- `platform/src/app/api/consume/**` (Phase 3/4 territory)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`

## Sub-streams (4 total)

### Stream A — Audit List View

- Route `/audit` renders a paginated list of audit rows. Default page size: 25; max 100. Server-side pagination + filtering.
- Columns: `created_at` (relative time), `query_class` (badge), `query_text` (truncated), `disclosure_tier` (badge), `validators_passed` (count + halt/pass icon), `checkpoint_summary` (icon if any checkpoint warned/halted; gray if no checkpoints ran), `panel_indicator` (icon if `payload.panel` present), `synthesis_model`.
- Filters in a sidebar: query class (multi-select), date range, disclosure tier (multi-select), validator status (passed-all / any-failed / halted), checkpoint status (none / warn / halt), panel mode (any / panel-only / single-only), free-text search over `query_text`.
- Each row is clickable → opens detail view (Stream B).
- New API endpoint `GET /api/audit/list?page=N&filters=...` returns paginated rows. Read-only; uses `audit/queries.ts` helpers.
- 12+ tests: pagination; each filter type works; combined filters; empty state; error state.

### Stream B — Audit Detail View

- Route `/audit/[query_id]` renders a single audit row's full content.
- Sections (in order):
  1. **Header**: query_text (full), created_at, query_class, disclosure_tier, synthesis_model, token counts.
  2. **Bundle**: list of `bundle_keys` with each rendered as a `<CitationChip />` (reuses Phase 5 component); clicking opens `<CitationPreview />` side panel.
  3. **Tools called**: ordered list of `tools_called` entries — tool name, params hash (truncated), latency, cached flag.
  4. **Validators**: list of `validators_run` entries — validator id, pass/fail, message. Failed validators highlighted with the same visual language as Phase 5's `<ValidatorFailureView />`.
  5. **Checkpoints** (only if `payload.checkpoints` present): for each of c4_5/c5_5/c8_5 — verdict badge, confidence, reasoning (collapsible); raw payload (collapsed JSON).
  6. **Panel** (only if `payload.panel` present): adjudicator final answer; expandable per-member outputs (anonymized as Phase 7 emits them); divergence classification table; member alignment badges.
  7. **Final output**: the rendered answer (using Phase 5's renderer for parity with Consume tab).
  8. **Raw payload**: collapsed JSON of the entire row for power users.
- Forward-compatible: any sub-section whose source field is absent gracefully renders nothing (not "No data" — just absent). This is how Phase 8 ships before Phase 7 completes without coupling.
- New API endpoint `GET /api/audit/[query_id]` returns full row + joined predictions if any.
- 14+ tests: each section renders correctly with its data; gracefully renders without checkpoint payload; gracefully renders without panel payload; raw payload toggle.

### Stream C — Prediction Ledger View

- Route `/audit/predictions` renders the prediction ledger.
- Two tabs: **Open predictions** (where `outcome IS NULL` AND `horizon_end >= today`) and **Closed predictions** (everything else).
- Open-predictions table columns: `prediction_text` (truncated), `confidence`, `horizon_start` → `horizon_end`, `falsifier`, source `query_id` (clickable → audit detail), `created_at`.
- Closed-predictions table columns: same plus `outcome` (badge: confirmed / refuted / partial / unobservable), `outcome_observed_at`, `calibration_bucket` (if assigned by Phase 10).
- Filter sidebar: subject (default `native:abhisek`), date range on horizon, confidence range, calibration bucket (when populated).
- An **outcome-recording form** at the bottom of each open prediction row: `outcome: confirmed|refuted|partial|unobservable` + free-text observation. Submitting POSTs to a new endpoint `POST /api/audit/predictions/[id]/outcome`. **The form refuses to submit if `horizon_start > today`** — the sacrosanct rule extends here: outcomes can only be recorded for predictions whose horizon has begun.
- New API endpoints: `GET /api/audit/predictions?status=open|closed&filters=...`, `POST /api/audit/predictions/[id]/outcome`.
- 12+ tests: open/closed split; outcome form submits; horizon-not-yet-begun rejection; calibration_bucket display when present and absent.

### Stream D — Compare View + Polish

- Route `/audit/compare?ids=A,B` renders two audit rows side-by-side. Designed for inspecting drift, divergence, or revisiting an A/B comparison from native review.
- Side-by-side layout with synced scrolling — matching sections align horizontally. Differences highlighted (e.g., divergent validators, divergent checkpoint verdicts, divergent final outputs).
- "Add to compare" button on each row in Stream A's list view; up to 2 rows can be compared at once.
- Polish pass: keyboard navigation across the audit views; ARIA labels; empty/error/loading states for each route; `<title>` and breadcrumb consistency; responsive layout for narrow screens.
- 8+ tests: compare-view side-by-side render; add-to-compare flow; diff highlighting; empty/error states; accessibility checks via axe-core.

## Critical constraints

- **Read-only.** Phase 8 never writes to `audit_log`. The only write is the prediction-outcome POST in Stream C, and even that goes through a Phase-4-supplied endpoint or a Phase-8-owned endpoint that calls a NEW writer helper added under Phase 4's territory — wait, that violates `must_not_touch`. **Resolution**: Stream C's outcome-recording calls a NEW endpoint that Phase 8 owns under `/api/audit/predictions/[id]/outcome`, but the actual DB-write helper lives under `platform/src/lib/audit/queries.ts` (Phase 8's read-only namespace gets a single carve-out for outcome writes — explicitly noted in this brief and tested for safety).
- **Sacrosanct held-out rule extends to outcome form.** UI must enforce `horizon_start <= today` before allowing outcome submission. Server-side endpoint also enforces — defense in depth.
- **Forward-compatible rendering.** Sections for checkpoint payload and panel payload render only when their source data is present. Phase 8 ships before Phase 7 completes; the panel section appears once Phase 7 starts emitting `payload.panel`.
- **Reuses Phase 5 components.** `<CitationChip />`, `<CitationPreview />`, `<DisclosureTierBadge />`, `<ValidatorFailureView />` — no new versions. Visual consistency between Consume tab and Audit view.
- **Performance.** Audit list query with filters must p95 ≤500ms on a 10K-row dataset. Use existing indexes (`(query_id)`, `(created_at desc)`); add new indexes only if profiling shows need (no migration in Phase 8 — file follow-up if needed).
- **Pagination is real.** Do not load all rows client-side. Server-side cursor or offset pagination, default page size 25.
- **Authentication.** Audit view is super-admin-tier only. The existing auth middleware (Firebase Auth per infrastructure state) gates the route. Test that non-super-admin requests get 403.
- **No global theme/style mutation.** All new styles component-scoped per Phase 5's pattern.

## Done criteria

1. Stream A: list view + 7 filter types + pagination + tests pass; performance budget met on synthetic 10K-row dataset.
2. Stream B: detail view renders all 8 sections; gracefully handles missing checkpoint/panel payloads; tests pass.
3. Stream C: prediction ledger with open/closed split + outcome form + sacrosanct horizon-rule enforcement; tests pass.
4. Stream D: compare view + polish + accessibility; tests pass.
5. Auth gate: non-super-admin returns 403 on every audit endpoint; verified by test.
6. End-to-end: with the `AUDIT_ENABLED` flag ON and a small set of seeded audit rows + predictions, navigate the full audit UX: list → detail → predictions → compare → outcome form. Visual review.
7. Reuses Phase 5 components (`<CitationChip />`, etc.) — no duplicates created.
8. Phase 7 forward-compatibility: with one synthetic audit row that contains `payload.panel`, detail view renders the Panel section correctly without modification.
9. `lint` + `type-check` clean.
10. `must_not_touch` verified — single carve-out (outcome writer) is explicit and tested for safety.
11. Native acceptance.

## Risk classification: LOW-MEDIUM

Read-only UI over an existing schema is structurally low-risk. Mitigations:
- No DB migrations
- Single carve-out (outcome write) is narrowly scoped, with both UI and server-side enforcement of the sacrosanct rule
- Reuses Phase 5 components for visual consistency
- Forward-compatible rendering means Phase 8 can ship before Phase 7 completes without coupling
- Auth gate is the existing middleware, not a new pattern

The MEDIUM half reflects the surface area: 4 routes, ~14 components, 4 API endpoints. Easy for subtle bugs to hide. Tests + manual end-to-end smoke catch these.

## Forward implications

- **Phase 7 (Panel Mode)** ships independently; Phase 8's panel section lights up once Phase 7's payloads start flowing.
- **Phase 10 (Calibration Loop)** uses Phase 8's outcome form as its data-collection surface. The native records outcomes via Phase 8 → calibration loop reads `prediction_ledger.outcome` + `calibration_bucket` → calibrated confidence updates → loop closes.
- **Sharing audit rows.** A future enhancement (post-Phase 8): public-redacted audit-row sharing via signed URL. Out of scope for Phase 8 v1.0.

## How native triggers

Open a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension). Paste:

> Read EXEC_BRIEF_PHASE_8_v1_0.md and execute it.

Disjoint from Phase 7 — both can run concurrently in two sessions.

## Status updates

- AUTHORED 2026-04-27
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when all 11 done-criteria pass and native accepts

---
brief_id: EXEC_BRIEF_PORTAL_REDESIGN_R5_TIMELINE
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-30
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PORTAL_REDESIGN_R5_TIMELINE_v1_0.md and execute it."
phase: Portal Redesign R5
phase_name: Timeline — NEW /clients/[id]/timeline (LEL events + prospective predictions)
parent_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md
tracker: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
risk_classification: MEDIUM
parallelizable_with: [R1, R2, R3, R6]
must_complete_before: [R7]
depends_on: [R0]
output_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_R5_REPORT_v1_0.md
---

# EXEC_BRIEF — Portal Redesign R5 — Timeline

## Mission

Land the Timeline surface — the third room in the Chart Profile — as a real route at `/clients/[id]/timeline`. The Timeline is the UI home for two corpus artifacts that `CLAUDE.md §E` names as cross-cutting workstreams: the **Life Event Log (LEL)** and the **prospective prediction log**. R5 stops these from being invisible; it does NOT change their data models.

LEL data lives in `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (markdown). Prospective predictions live as a subsection inside the LEL until `06_LEARNING_LAYER/` is scaffolded. R5 reads both as parsed markdown via a thin server-side parser; no DB migration.

This phase is parallelizable with R1, R2, R3, R6. Closing R5 also flips R2's Timeline Room CTA from `disabled` to `href="/clients/[id]/timeline"`.

## Pre-flight gate

Halt if any fail.

1. R0 closed. `<AppShell>` and `<ZoneRoot>` exist.
2. `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` parses cleanly with the parser this brief lands. Run dry-run before committing parser.
3. R5 row in TRACKER §3 reflects authored or earlier.
4. Working tree clean. Branch `redesign/r5-timeline`.

## Scope declaration

```yaml
may_touch:
  - platform/src/app/clients/[id]/timeline/                          # NEW route
  - platform/src/app/clients/[id]/timeline/page.tsx                  # NEW
  - platform/src/app/clients/[id]/timeline/layout.tsx                # NEW
  - platform/src/components/timeline/                                # NEW directory
  - platform/src/components/timeline/TimelineView.tsx                # NEW
  - platform/src/components/timeline/PredictionTable.tsx             # NEW
  - platform/src/components/timeline/EventCard.tsx                   # NEW
  - platform/src/components/timeline/LogEventDialog.tsx              # NEW
  - platform/src/components/timeline/LogPredictionDialog.tsx         # NEW
  - platform/src/lib/lel/                                            # NEW directory
  - platform/src/lib/lel/parser.ts                                   # NEW
  - platform/src/lib/lel/writer.ts                                   # NEW
  - platform/src/app/api/lel/route.ts                                # NEW endpoint (append-only)
  - 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md                            # APPEND-ONLY writes via API
  - tests/e2e/portal/timeline.spec.ts                                # NEW
  - tests/lib/lel-parser.test.ts                                     # NEW
  - tests/lib/lel-writer.test.ts                                     # NEW
must_not_touch:
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md                # untouched
  - 025_HOLISTIC_SYNTHESIS/, 03_DOMAIN_REPORTS/, 035_DISCOVERY_LAYER/
  - 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/, 99_ARCHIVE/
  - 06_LEARNING_LAYER/                                                # not yet scaffolded
  - platform/migrations/, platform/supabase/migrations/
  - platform/python-sidecar/
  - platform/src/lib/db/types.ts
  - platform/src/components/shared/AppShell.tsx
  - platform/src/components/dashboard/, build/, consume/, chat/
  - platform/src/app/clients/[id]/{build,consume,page.tsx}
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
```

**LEL writes are APPEND-ONLY.** R5 must NOT delete or edit existing LEL entries. The writer appends a YAML block at the end of the appropriate section, never edits existing blocks.

## §1 — `/clients/[id]/timeline` page

Server component:
1. Resolves user/profile/chart per existing pattern.
2. Calls `parseLEL(chartId)` → `{ events: LELEvent[]; predictions: LELPrediction[] }`.
3. Renders `<TimelineView events={events} predictions={predictions} chartId={chartId} canWrite={profile.role === 'super_admin'}>`.

Wraps in `<AppShell>` with breadcrumb `[Roster, ChartName, Timeline]`. Vellum zone.

## §2 — `<TimelineView>`

Two-tab layout: `Events | Predictions`. Tab state in URL (`?tab=events|predictions`).

**Events tab:** vertical timeline (top = most recent). Each event renders as `<EventCard>` showing date, event_type, body, chart_state metadata (current dasha at time of event, etc.). Filter chip-row above: by category, by year, by dasha lord. "Log new event" button (super_admin only) opens `<LogEventDialog>`.

**Predictions tab:** sortable table via `<PredictionTable>`. Columns: prediction_id, made_at, horizon, confidence, falsifier, status (open / observed-confirmed / observed-refuted / expired), outcome_logged_at. "Log prediction" button (super_admin only) opens `<LogPredictionDialog>`. "Mark outcome" button on each open prediction row.

## §3 — LEL parser

Path: `platform/src/lib/lel/parser.ts`.

```ts
export interface LELEvent {
  id: string;                       // e.g., "EVT.2024.07.15.1"
  date: string;                     // ISO
  category: string;                 // e.g., "career", "health", "relationship"
  body: string;
  chart_state?: {
    maha_lord?: string;
    antar_lord?: string;
    pratyantar_lord?: string;
    transit_notes?: string;
  };
  source?: string;
  confidence?: number;              // 0..1
}

export interface LELPrediction {
  id: string;                       // e.g., "PRED.2026.04.29.1"
  made_at: string;                  // ISO
  chart_id: string;
  horizon: string;
  confidence: number;
  falsifier: string;
  body: string;
  status: 'open' | 'observed_confirmed' | 'observed_refuted' | 'expired';
  outcome_logged_at?: string;
  outcome_body?: string;
}

export async function parseLEL(chartId: string): Promise<{ events: LELEvent[]; predictions: LELPrediction[] }>;
```

Reads `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`. Tolerant of minor format variation. Emits structured error (not throw) for malformed entries; page renders parsable subset and surfaces "N entries skipped due to format errors" banner. Tests: fixture LEL file, assert all events parse, assert one malformed entry surfaces in error list.

## §4 — LEL writer

Path: `platform/src/lib/lel/writer.ts`.

```ts
export async function appendEvent(chartId: string, event: NewLELEvent): Promise<{ id: string }>;
export async function appendPrediction(chartId: string, pred: NewLELPrediction): Promise<{ id: string }>;
export async function markPredictionOutcome(predId: string, outcome: { status: 'observed_confirmed' | 'observed_refuted'; body: string }): Promise<void>;
```

Writes via `/api/lel`, the only surface authorized to mutate LEL. Endpoint:
- Verifies super_admin role.
- Acquires soft lock (in-process mutex on LEL file path).
- Appends YAML block at end of appropriate section.
- Bumps LEL frontmatter `version` (patch — `1.2.N` → `1.2.N+1`) and adds changelog entry.
- Re-validates via `parseLEL` after write; rolls back and returns 500 if parse fails.

Per `CLAUDE.md §E`: writer flags new events with `chart_state_pending: true`; sidecar's nightly job populates `chart_state` block. R5 does NOT modify the sidecar.

## §5 — R2's Timeline Room CTA

If R2 is closed when R5 closes: edit `<RoomCard>` Timeline Room in `platform/src/components/profile/` — flip `cta.disabled` from `true` to `false`, set `cta.href` to `/clients/${id}/timeline`. If R2 not yet closed, capture as follow-up for R2's closure report.

## §6 — Tests

`tests/e2e/portal/timeline.spec.ts`: super_admin opens /clients/[id]/timeline; sees events tab; switches to predictions tab; opens log-event dialog, fills + submits, asserts new event appears.

`tests/lib/lel-parser.test.ts`: fixture parsing, malformed-entry tolerance.
`tests/lib/lel-writer.test.ts`: append + re-parse round-trip, frontmatter version bump, lock contention.

Visual regression on the new route. **drift_detector.py is load-bearing this phase** because LEL frontmatter version bumps. Confirm exit 0 explicitly in closure report. mirror_enforcer.py / schema_validator.py exit 0.

## §7 — Closure report

`00_ARCHITECTURE/PORTAL_REDESIGN_R5_REPORT_v1_0.md`. Update TRACKER §3 R5 row to closed; if R2 already closed, note Timeline Room CTA flip.

## §8 — Out of scope

- Do NOT scaffold `06_LEARNING_LAYER/`.
- Do NOT modify LEL parser semantics retroactively (no schema changes).
- Do NOT compute Swiss Ephemeris values in R5 — sidecar's job.
- Do NOT delete or edit existing LEL events — append-only.
- Do NOT add a Discovery-Layer surface.

## §9 — One-line summary

Give LEL events and prospective predictions a real UI home — read-mostly with append-only super_admin writes — without touching the data model.

---

*End of EXEC_BRIEF_PORTAL_REDESIGN_R5_TIMELINE_v1_0.md (AUTHORED, re-authored 2026-04-30 after surgical-fix data loss).*

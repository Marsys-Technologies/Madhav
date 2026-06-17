---
brief_id: EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-30
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE_v1_0.md and execute it."
phase: Portal Redesign R2
phase_name: Chart Profile — keystone surface (NEW /clients/[id])
parent_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md
tracker: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
risk_classification: MEDIUM
parallelizable_with: [R1, R4, R5, R6]
unblocks: [R3]
must_complete_before: [R3, R7]
depends_on: [R0]
output_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_R2_REPORT_v1_0.md
---

# EXEC_BRIEF — Portal Redesign R2 — Chart Profile

## Mission

Replace the silent redirect at `platform/src/app/clients/[id]/page.tsx` with the **Chart Profile** page — the keystone surface of the redesign. The page renders, for any chart the user has access to, a hero band with a rasi-chart SVG drawn from L1 forensic data, three "room" cards (Build / Consume / Timeline) that link into existing per-client routes, and a metadata side rail (current Vimshottari period with countdown, top yogas, freshness, audience tier).

Chart Profile is the moment the cinema of the login screen returns: vellum page chrome with a gold-on-dim-charcoal hero band — the "Bridge zone" defined in PORTAL_REDESIGN_VISION §3.2.

This brief lands one new page and five new components. Zero schema changes, zero migrations, zero sidecar changes, zero auth changes.

## Pre-flight gate

Halt with a clear actionable message if any fail.

1. R0 has landed: `<AppShell>` and `<ZoneRoot>` exist; `/build → /cockpit` rename is live.
2. Vision exists; R2 row in TRACKER §3 reflects authored or earlier (start work flips to in_flight).
3. `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` is reachable; Phase 14C `l1_structured_*` tables are populated for at least Abhisek Mohanty.
4. Working tree clean. Branch matches `redesign/r2-chart-profile`.

## Scope declaration

```yaml
may_touch:
  - platform/src/app/clients/[id]/page.tsx                           # replaces silent redirect
  - platform/src/app/clients/[id]/layout.tsx                         # narrow edits only
  - platform/src/components/profile/                                 # NEW directory
  - platform/src/components/profile/ChartHero.tsx                    # NEW
  - platform/src/components/profile/RoomCard.tsx                     # NEW
  - platform/src/components/profile/ProfileSideRail.tsx              # NEW
  - platform/src/components/profile/DashaCountdown.tsx               # NEW
  - platform/src/components/charts/RasiChartSVG.tsx                  # NEW (the renderer)
  - platform/src/lib/forensic/snapshot.ts                            # NEW (reads Phase 14C tables)
  - platform/src/components/dashboard/ClientCard.tsx                 # ONE-LINE primary CTA href change
  - tests/e2e/portal/chart-profile.spec.ts                           # NEW
  - tests/components/RasiChartSVG.test.tsx                           # NEW
  - tests/components/DashaCountdown.test.tsx                         # NEW
  - tests/components/RoomCard.test.tsx                               # NEW
must_not_touch:
  - 01_FACTS_LAYER/                                                   # L1 read-only
  - 025_HOLISTIC_SYNTHESIS/, 03_DOMAIN_REPORTS/, 035_DISCOVERY_LAYER/
  - 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/, 06_LEARNING_LAYER/, 99_ARCHIVE/
  - platform/migrations/, platform/supabase/migrations/
  - platform/python-sidecar/
  - platform/src/lib/db/types.ts
  - platform/src/lib/firebase/
  - platform/src/app/api/**                                          # NO API change
  - platform/src/components/build/, consume/, chat/                  # other-phase scope
  - platform/src/app/build/**, platform/src/app/cockpit/**           # R6 scope
  - platform/src/app/clients/[id]/build/, [id]/consume/              # R3/R4 scope
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
```

## §1 — What "done" looks like

Super_admin clicks Abhisek's `ClientCard`. Lands on `/clients/{id}`. Sees:

1. AppShell breadcrumb: `Roster · Abhisek Mohanty · Profile`.
2. Hero band (full bleed, ~480px tall): rasi chart in gold linework on dim charcoal, Mandala motif at ≤8% opacity behind. Native's name "Abhisek Mohanty" in Source Serif 4 ≥ 36px. Birth meta: "1984-02-05 · 10:43 IST · Bhubaneswar, Odisha, India" in Inter, muted.
3. Three room cards in 3-col grid (stacked on mobile):
   - **Build Room** (super_admin only): inline `<JourneyStrip>` showing pyramid completion, last build activity timestamp, "Continue building →" CTA → `/clients/{id}/build`.
   - **Consume Room**: last 3 conversation titles (linked), top reports preview (≤3 cards), "Ask anything →" CTA → `/clients/{id}/consume`.
   - **Timeline Room**: last 3 LEL events, count of active prospective predictions, "Open timeline (coming in R5)" — disabled until R5 lands. Intentional, not a TODO leak.
4. Side rail (collapses to Sheet on mobile): `<DashaCountdown>` for current Maha–Antar–Pratyantar; top 3 yogas chip-row; freshness banner; audience-tier badge; super_admin-only audit deep-link.
5. Footer (super_admin only): mirror_pair status indicator + last governance close timestamp.

`client`-role user sees: hero, Consume Room only, Timeline Room read-only-preview, no audit deep-link, no governance footer.

## §2 — Component delivery list

### §2.1 `<RasiChartSVG>` — the renderer

**Path:** `platform/src/components/charts/RasiChartSVG.tsx`

Decision: built from scratch, no external library. Rationale: full brand control, zero new dependencies, deterministic rendering from L1 data (B.10 compliance — no fabricated values).

Style: North Indian (diamond) by default. South Indian is follow-on; not in R2.

```ts
interface RasiChartSVGProps {
  chart: ForensicChart;
  size?: number;              // default 480
  style?: 'north' | 'south';  // default 'north'
  className?: string;
  paused?: boolean;           // for prefers-reduced-motion
}
```

**Visual spec:** Diamond outline in `var(--brand-gold)` at 1.5px stroke. Inner diagonals same. House numbers in Inter 11px gold-cream. Planet glyphs in Source Serif 4, gold-light at 18px, stacked vertically when multiple. Lagna marked with a triangular notch on the corresponding house's outer edge. Background `var(--brand-charcoal)` with Mandala at 6% opacity. Mandala paused if `prefers-reduced-motion` or `paused` prop. No tooltips in R2. SVG has `role="img"` with meaningful `aria-label` (e.g., "Rasi chart, Lagna Capricorn, Sun and Moon in Capricorn").

**Data source:** `getForensicSnapshot(chartId)` — new helper in `platform/src/lib/forensic/snapshot.ts`. Reads Phase 14C `l1_structured_*` tables. Must NOT compute. If chart has no L1 facts persisted, render brand-styled empty state ("L1 facts not yet ingested for this chart") and emit no error.

**Acceptance:** Renders Abhisek Mohanty's chart matching `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §1` (Lagna Capricorn, Sun in Capricorn, Moon in Capricorn at 11°09', etc.). Executor MUST visually verify against the FORENSIC source — do not rely on automated tests alone (B.10). Lighthouse a11y ≥ 95.

### §2.2 `<ChartHero>`

Path: `platform/src/components/profile/ChartHero.tsx`. Composes `<RasiChartSVG>` + Mandala backdrop + native name + birth meta. Wraps in `<ZoneRoot zone="ink">` so the gold-on-dim-charcoal mode is scoped (does NOT bleed into the rest of the vellum-zoned page). Full-bleed within the AppShell content column.

### §2.3 `<RoomCard>`

Path: `platform/src/components/profile/RoomCard.tsx`. Single component, three instances on the page.

```ts
interface RoomCardProps {
  title: string;
  description?: string;
  cta: { label: string; href: string; disabled?: boolean; tooltip?: string };
  children: React.ReactNode;
}
```

Build Room hidden via parent component when role is `client`.

### §2.4 `<ProfileSideRail>`

Path: `platform/src/components/profile/ProfileSideRail.tsx`. Composes `<DashaCountdown>` + yoga chip-row + `<FreshnessIndicator>` (existing component from `platform/src/components/build/FreshnessIndicator.tsx` — reuse it) + audience-tier badge + (super_admin only) audit deep-link. Collapses to `<Sheet>` on mobile.

### §2.5 `<DashaCountdown>`

Path: `platform/src/components/profile/DashaCountdown.tsx`. Reads current Maha–Antar–Pratyantar from L1 (existing data; do not recompute). Live-ticking countdown to the next antar boundary. **No client-side dasha math** — reads persisted boundaries from L1 / Phase 14C tables. Countdown is just `boundary_iso - now`, formatted.

### §2.6 The page itself

Replace the 5-line silent redirect at `platform/src/app/clients/[id]/page.tsx` with a server component that:
1. Resolves `user`, `profile`, `chart` (existing pattern from `app/clients/[id]/layout.tsx`).
2. Pulls `getForensicSnapshot(chartId)`, last 3 conversations, top reports, pyramid layers, last build close timestamp, current dasha, top yogas.
3. Renders `<ChartHero>`, three `<RoomCard>` instances, and `<ProfileSideRail>`.
4. Wraps in `<ZoneRoot zone="vellum">` (page chrome) — `<ChartHero>` internally re-scopes to `zone="ink"`.

Existing `clients/[id]/layout.tsx` does NOT change except optionally to remove the `flex h-[100dvh] flex-col overflow-hidden` wrapper if it conflicts (the wrapper was sized for chat shells; Profile is a scrolling page).

## §3 — Subtle changes elsewhere

- `platform/src/components/dashboard/ClientCard.tsx`: change primary card click target from `/clients/{id}/build` to `/clients/{id}` (the new Profile). Build / Consume buttons stay as secondary inline CTAs in the card so users can deep-link from Roster.
- `platform/src/app/dashboard/page.tsx`: no change.
- `platform/src/app/clients/[id]/build/page.tsx` and `consume/page.tsx`: no functional change.

## §4 — Tests

### §4.1 Playwright smoke
`tests/e2e/portal/chart-profile.spec.ts`: super_admin sees hero + 3 rooms + side rail, "Continue building" enabled, audit deep-link visible; client sees only Consume + Timeline-preview; prefers-reduced-motion disables Mandala animation.

### §4.2 Unit tests
`tests/components/RasiChartSVG.test.tsx`: fixture render + aria-label assertion. `tests/components/DashaCountdown.test.tsx`: countdown math, boundary-rollover, tz-edge handling. `tests/components/RoomCard.test.tsx`: disabled-CTA tooltip rendering.

### §4.3 Visual diff
Capture screenshots before-and-after. Submit as attachment to closure report.

### §4.4 Governance scripts
`mirror_enforcer.py`, `drift_detector.py`, `schema_validator.py` exit 0.

### §4.5 Manual acharya-grade visual verification — NOT OPTIONAL

Before close, executor MUST visually compare the rendered Abhisek Mohanty rasi chart against placements documented in `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §1`. Report findings in closure report. This is a B.10 compliance check.

## §5 — Closure report

Land `00_ARCHITECTURE/PORTAL_REDESIGN_R2_REPORT_v1_0.md` with `status: COMPLETE`. Update TRACKER §3 R2 row to `status: closed` with session_id, closed_at, follow_ups (expected: South Indian style, click-to-house tooltips deferred).

**R2 unblocks R3.** Closure report MUST include follow-up note: "R3 brief now authorable — Build mode hook-compatibility audit can proceed."

## §6 — Out of scope

- Do NOT add a `/clients/[id]/timeline` route in R2. R5's job. Timeline Room renders read-only-preview only.
- Do NOT modify `BuildChat` or anything under `components/build/` except importing `JourneyStrip` (and `FreshnessIndicator`).
- Do NOT modify `ConsumeChat` or anything under `components/consume/`.
- Do NOT introduce any DB migration.
- Do NOT introduce any new Vertex AI / sidecar call.
- Do NOT promote VISION to CURRENT or update CANONICAL_ARTIFACTS — separate session's job, gated on R0 close having promoted it already.

## §7 — One-line summary

Land the keystone Chart Profile page that turns the silent redirect into the most beautiful, most legible, most acharya-grade surface in the portal — using only L1 facts and the existing brand spine.

---

*End of EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE_v1_0.md (AUTHORED, re-authored 2026-04-30 after surgical-fix data loss).*

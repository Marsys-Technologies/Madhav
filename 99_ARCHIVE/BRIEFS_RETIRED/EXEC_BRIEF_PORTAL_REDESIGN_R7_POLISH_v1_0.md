---
brief_id: EXEC_BRIEF_PORTAL_REDESIGN_R7_POLISH
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-30
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PORTAL_REDESIGN_R7_POLISH_v1_0.md and execute it."
phase: Portal Redesign R7
phase_name: Polish — accessibility + mobile + animation + perceived-perf + flag cleanup
parent_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md
tracker: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
risk_classification: LOW
parallelizable_with: []                                  # R7 runs alone — touches every surface for the polish pass
must_complete_before: []                                 # final phase
depends_on: [R0, R1, R2, R3, R4, R5, R6]                 # R7 is the polish pass over everything that landed
output_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_R7_REPORT_v1_0.md
---

# EXEC_BRIEF — Portal Redesign R7 — Polish

## Mission

R7 is the polish pass that closes out the redesign workstream. R0–R6 landed the surfaces, components, and interactions; R7 makes them production-grade. Five concrete deliverables:

1. **Accessibility audit** — Lighthouse a11y ≥ 95 on every redesign surface (Roster, Chart Profile, Build, Consume, Cockpit, Timeline). Fix any violations surfaced.
2. **Mobile pass** — Chart Profile, Roster table view, Build chat, Consume chat, Timeline all responsive at 375 px (iPhone SE), 414 px (iPhone Pro), 768 px (iPad portrait). Fix overflow, awkward stacking, unreachable controls.
3. **Animation timings audit** — Mandala backdrop rotation cadence, ProgressBar transitions, ascend transitions when entering Build/Consume from a chart card. Tune for taste; honor `prefers-reduced-motion`.
4. **Perceived-performance audit** — streaming dots, skeleton states, optimistic UI on the Roster filter, optimistic UI on Log Prediction submit. Reduce visual jitter on slow networks.
5. **Feature flag cleanup** — remove `PORTAL_REDESIGN_R0_ENABLED` (and any other `PORTAL_REDESIGN_R*_ENABLED` flags) from `platform/src/lib/config/feature_flags.ts`, env-files, and Cloud Run config. Delete the legacy code-path branches the flags gated. Update `FEATURE_FLAG_STATUS.md`.

R7 is the final redesign phase. After R7 closes, the redesign workstream is complete and the tracker can move from LIVING to ARCHIVED.

## Pre-flight gate

Halt if any fail.

1. R0, R1, R2, R3, R4, R5, R6 all closed in TRACKER §3 with `status: closed`.
2. All five phase branches merged to `main`. Recent `main` log shows the squash-merge commits for each.
3. Vision is at `status: CURRENT` in `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md`.
4. `npm test` passes on `main` baseline (capture pre-R7 baseline count for comparison at close).
5. Working tree clean. Branch `redesign/r7-polish` (create from `main`).

## Scope declaration

```yaml
may_touch:
  # Accessibility fixes — any surface that fails Lighthouse a11y ≥ 95
  - platform/src/components/**                                       # any component with a11y violation
  - platform/src/app/**                                              # any layout or page with a11y violation

  # Mobile pass — responsive fixes
  - platform/src/components/profile/**                               # Chart Profile mobile layout
  - platform/src/components/dashboard/**                             # Roster mobile layout
  - platform/src/components/timeline/**                              # Timeline mobile layout
  - platform/src/components/consume/**                               # Consume mobile polish (post-R4)
  - platform/src/components/build/**                                 # Build mobile polish (post-R3)
  - platform/src/components/shared/AppShell.tsx                      # AppShell mobile rail behavior

  # Motion + perf
  - platform/src/components/brand/Mandala.tsx                        # rotation cadence
  - platform/src/components/build/ProgressBar.tsx                    # transition timings
  - platform/src/components/profile/DashaCountdown.tsx               # ticker cadence

  # Feature flag cleanup
  - platform/src/lib/config/feature_flags.ts                         # remove PORTAL_REDESIGN_R*_ENABLED
  - platform/.env.local
  - platform/.env.example
  - platform/.env.local.example
  - platform/FEATURE_FLAG_STATUS.md
  - platform/src/app/dashboard/layout.tsx                            # remove flag-gated fallback branches
  - platform/src/app/clients/[id]/layout.tsx                         # same
  - platform/src/app/admin/layout.tsx                                # same
  - platform/src/app/audit/layout.tsx                                # same
  - platform/src/app/cockpit/layout.tsx                              # same

  # Tracker + Vision close-out
  - 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md                  # R7 row → closed; §2 active_phase → null; deferred_briefs → []
  - 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md                   # add changelog entry; status remains CURRENT
  - 00_ARCHITECTURE/PORTAL_REDESIGN_R7_REPORT_v1_0.md                # NEW closure report
  - 00_ARCHITECTURE/SESSION_LOG.md                                   # append session entry

  # Tests
  - tests/e2e/portal/a11y.spec.ts                                    # NEW: per-surface Lighthouse smoke
  - tests/e2e/portal/mobile.spec.ts                                  # NEW: viewport-emulated screenshot tests
  - tests/components/                                                # any new motion/perf assertions

must_not_touch:
  - 01_FACTS_LAYER/, 025_HOLISTIC_SYNTHESIS/, 03_DOMAIN_REPORTS/, 035_DISCOVERY_LAYER/
  - 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/, 06_LEARNING_LAYER/, 99_ARCHIVE/
  - platform/migrations/, platform/supabase/migrations/
  - platform/python-sidecar/
  - platform/src/app/api/**                                          # NO API change
  - platform/src/lib/db/types.ts
  - platform/src/lib/firebase/
  - platform/src/lib/synthesis/                                      # synthesis untouched
  - platform/src/lib/strategies/single_model_strategy.ts             # synthesis untouched
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md                      # was updated at R0 close; not touched again
  - CLAUDE.md                                                         # was updated at R0 close
  - .geminirules, .gemini/project_state.md                            # mirror updated at R0 close
```

R7 is allowed broad `may_touch` because it polishes everywhere, but it is NOT allowed to introduce new functionality. Every edit is a fix for an a11y violation, a responsive issue, a motion timing tune, a perf observation, or flag removal — never a new feature.

## §1 — Accessibility audit

### §1.1 Per-surface Lighthouse run

Run Lighthouse a11y on every redesign surface, both as super_admin and as client (where the role distinction matters):

| Surface | URL | Roles | Min a11y |
|---------|-----|-------|----------|
| Roster | `/dashboard` | super_admin, admin | 95 |
| Chart Profile | `/clients/{id}` | super_admin, client | 95 |
| Build mode | `/clients/{id}/build` | super_admin | 95 |
| Consume mode | `/clients/{id}/consume` | super_admin, client | 95 |
| Timeline | `/clients/{id}/timeline` | super_admin, client | 95 |
| Cockpit | `/cockpit` | super_admin | 95 |
| Cockpit sub-routes | `/cockpit/{plan,sessions,registry,...}` | super_admin | 95 |
| Login | `/login` | unauthenticated | 95 |

Capture each Lighthouse run as JSON; commit to `tests/lighthouse/r7-baseline/`.

### §1.2 Common issue classes to look for

The Bridge zone (Chart Profile hero) is the most likely a11y trouble spot — gold-on-charcoal contrast may fail WCAG AA. Verify text on the hero meets 4.5:1 (large text 3:1). The rasi chart's `aria-label` should describe the chart's lagna and major placements meaningfully ("Rasi chart of Abhisek Mohanty, Lagna Capricorn, Sun and Moon in Capricorn, Saturn and Mars in Cancer, Jupiter and Venus in Virgo"). Color-only state indicators (health dot, freshness chip) need a non-color affordance — text label, icon, or `aria-label` describing the state.

### §1.3 Fix and reverify

For each violation, land a small, scoped fix. Do not refactor surrounding code. After each fix, rerun Lighthouse on that surface and confirm ≥ 95.

## §2 — Mobile pass

### §2.1 Viewports

Test on three sizes:
- **375×667** (iPhone SE)
- **414×896** (iPhone 14 Pro)
- **768×1024** (iPad portrait)

Use Chrome DevTools device emulation. Capture screenshots of each surface at each size; commit to `tests/screenshots/r7-mobile/`.

### §2.2 Common issue classes

The Roster table view is the most likely mobile breakage — six columns will overflow at 375 px. Fix: at narrow viewports, collapse to a stacked card-list within the table view, or hide the toggle and force grid view. The Chart Profile side rail must collapse to a `<Sheet>` triggered from a button on the hero — verify R2 implemented this; fix if not. The Build mode three-pane layout (sidebar + center + right pane) must collapse to a single column on mobile with the right pane behind a `<Sheet>` trigger.

The AppShell's left rail should be hidden behind a hamburger trigger on mobile, exposed via a `<Sheet>` from the breadcrumb row.

### §2.3 Touch target audit

Every clickable element on every surface should be ≥ 44×44 px on mobile. The health dots in `<ClientCard>`, the small chips in `<ProfileSideRail>`, and the trace button in `<AnswerView>` are likely below this threshold — bump them or add invisible padding.

## §3 — Animation timings audit

### §3.1 Mandala backdrop

The Mandala's rotation cadence on Login and Chart Profile should be slow enough to not distract. Measure: full rotation should take ≥ 60 seconds. If faster, tune. Honor `prefers-reduced-motion` — pause the rotation entirely.

### §3.2 ProgressBar transitions

The pyramid `<ProgressBar>` and the build-% meters should ease, not snap. 200–400 ms cubic-out is typical. Verify and tune.

### §3.3 Streaming dots

The `<StreamingDots>` and `<PendingAssistantBubble>` cadences should feel like thought, not panic. 600–1000 ms per cycle is typical. Verify.

### §3.4 Page-transition motion

When entering Build or Consume from a Chart Profile room card, a subtle "ascend" transition (translate-y + fade in over ~200 ms) makes the navigation feel intentional. If R2 didn't implement this, R7 adds it as a small `<motion.div>` wrapper or a CSS transition on the layout's `<main>`.

## §4 — Perceived-performance audit

### §4.1 Skeleton states

Every page that streams data should render a skeleton on first paint, not a spinner. Verify each surface:

- Roster: ChartCard skeletons while charts query is pending.
- Chart Profile: hero skeleton while `getForensicSnapshot` resolves; room card skeletons.
- Consume: skeleton answer block while query stream is starting.
- Timeline: event card skeletons.

If any surface shows a spinner instead of a skeleton, replace with a skeleton.

### §4.2 Optimistic UI

The Log Prediction action (R4) and Log Event action (R5) should optimistically render the new entry before the server confirms. Verify; if either shows a "submitting..." state without the optimistic entry, add the optimistic update.

### §4.3 Roster filter responsiveness

The Roster filter changes (R1) should be instant — they're client-side. If there's a perceptible lag, profile and fix.

## §5 — Feature flag cleanup

### §5.1 Remove `PORTAL_REDESIGN_R0_ENABLED`

R0 introduced this flag; the gates in `dashboard/layout.tsx`, `clients/[id]/layout.tsx`, `admin/layout.tsx`, `audit/layout.tsx`, `cockpit/layout.tsx` need cleanup:

- Remove the flag's branch from each layout (the legacy `DashboardHeader` / `BuildHeader` rendering path).
- Delete the import.
- Verify each layout always renders via `<AppShell>`.

### §5.2 Remove the flag from config

`platform/src/lib/config/feature_flags.ts`: remove the `PORTAL_REDESIGN_R0_ENABLED` declaration. `platform/.env.local`, `.env.example`, `.env.local.example`: remove any `PORTAL_REDESIGN_R0_ENABLED=` lines. Cloud Run env: schedule a follow-up gcloud command to unset:

```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --project madhav-astrology \
  --remove-env-vars "MARSYS_FLAG_PORTAL_REDESIGN_R0_ENABLED"
```

(Capture this in the closure report; native runs the gcloud command at deploy time, not at R7 commit.)

### §5.3 Update `FEATURE_FLAG_STATUS.md`

Move `PORTAL_REDESIGN_R0_ENABLED` from "Active" to "Removed (post-R7 cleanup, 2026-04-30)".

### §5.4 Other R*_ENABLED flags

If any other phase introduced its own flag (e.g., `PORTAL_REDESIGN_R5_ENABLED` for the timeline route), apply the same cleanup. Audit `feature_flags.ts` for all `PORTAL_REDESIGN_*` flags; remove all.

## §6 — Tests

### §6.1 a11y E2E

`tests/e2e/portal/a11y.spec.ts`: per-surface Lighthouse smoke that fails the build if any surface drops below 95. Run as part of CI.

### §6.2 Mobile E2E

`tests/e2e/portal/mobile.spec.ts`: viewport-emulated tests that capture screenshots and assert no overflow on key surfaces. Use Playwright's `viewport` and `screenshot` APIs.

### §6.3 Existing tests

All existing tests (the ~870 tests across R0–R6) must continue to pass. R7 should not regress anything. Capture pre-R7 baseline test count and post-R7 count in the closure report.

### §6.4 Governance scripts

`mirror_enforcer.py`, `drift_detector.py`, `schema_validator.py` exit 0.

## §7 — Closure report and redesign workstream close

`00_ARCHITECTURE/PORTAL_REDESIGN_R7_REPORT_v1_0.md` with `status: COMPLETE`. The closure report:

1. Summarizes a11y findings per surface (before/after Lighthouse scores).
2. Documents mobile fixes per surface.
3. Lists motion timing changes.
4. Lists perceived-perf changes.
5. Lists removed flags and the gcloud command for production env cleanup.
6. Confirms test baseline preserved (e.g., "871 tests pre-R7, 873 tests post-R7, 0 regressions").

**Update TRACKER:**
- §3 R7 row: `status: closed`, populate `session_id`, `closed_at`, `follow_ups` (any deferred polish items go here).
- §2 canonical state block: `active_phase: null`, `last_redesign_session_id: <this session>`, `last_close_at: <ISO>`. Add field `redesign_workstream_status: COMPLETE`.
- `deferred_briefs: []` (R3 and R7 both authored and closed by this point).

**Update VISION:**
- Add changelog entry: "v1.0.3 (2026-04-30) — Redesign workstream complete. R0 through R7 all closed. Acceptance criteria §5 (8 items) all satisfied. Tracker moves to ARCHIVED at next session."
- `status` remains `CURRENT` — the Vision is the historical record of what shipped.

**SESSION_LOG.md:** append the standard close entry.

## §8 — Out of scope

- Do NOT introduce any new feature.
- Do NOT modify the API surface.
- Do NOT modify synthesis strategies.
- Do NOT modify the corpus.
- Do NOT introduce DB migrations.
- Do NOT touch the parked trace-fix or platform-hygiene workstreams.
- Do NOT archive the tracker — that's the next session's job after R7 close, not part of R7 itself.

## §9 — One-line summary

Polish every surface the redesign shipped — accessibility, mobile, motion, perceived-perf, flag cleanup — then close the workstream.

---

*End of EXEC_BRIEF_PORTAL_REDESIGN_R7_POLISH_v1_0.md (AUTHORED, 2026-04-30).*

---
artifact: PORTAL_REDESIGN_VISION_v1_0
artifact_id: PORTAL_REDESIGN_VISION
version: 1.0.3
status: CURRENT
authored_by: Cowork (Opus)
authored_at: 2026-04-29
owner: Abhisek Mohanty
scope: platform/src/ UI surfaces (Roster, Chart Profile, Build, Consume, Cockpit, AppShell). NO schema, NO migrations, NO sidecar, NO auth model changes.
relates_to: [PROJECT_ARCHITECTURE_v2_2.md §D.11 (UX surfaces), MACRO_PLAN_v2_0.md §Ethical Framework (audience tiers), PHASE_B_PLAN_v1_0.md (UX is byproduct of corpus discovery)]
supersedes: none
governance_status: CURRENT (promoted at R0 close 2026-04-29; added to CANONICAL_ARTIFACTS §1)
mirror_pair: none (Claude-only UX vision; no Gemini-side counterpart)
---

# Portal Redesign Vision v1.0 — "The Chart Room"

## Changelog
- **2026-04-30 v1.0.3 — Redesign workstream complete**: R7 (Polish) closed 2026-04-30. All executed phases (R0–R2, R4–R6, R7) closed. R3 (Build mode three-pane cockpit) remains deferred — never authored or executed; excluded from R7 polish scope. Acceptance criteria §5 items 1–7 satisfied across executed phases. Tracker moves to `redesign_workstream_status: COMPLETE`; tracker will be archived at next session close. Vision retains `status: CURRENT` as the historical record.
- **2026-04-29 v1.0.2 — trace-fix on-hold amendment**: Native put the Query Trace Panel `conversation_id` propagation fix on hold (decision recorded 2026-04-29, post-tracker-authoring). §4.3.2 updated to reflect the dissolved R4 collision: with trace fix not in flight, R4 is no longer the one-true-serialization-point and can fan out alongside R1, R2, R5, R6 post-R0. Five phases parallel-ready post-R0 instead of four. R3 and R7 deferrals unchanged (R3 awaits R2 close; R7 is the polish pass). The R4 brief is authored in the same session as this amendment per the new posture. If trace fix resumes later, the serialization rule reverses: trace fix work would then need to coordinate against R4 (whichever has merged first), captured as a sticky note in §4.3.2.
- **2026-04-29 v1.0.1 — parallelism amendment**: Added §4.3 Parallelism guidance — phase-level dependency graph, trace-fix co-existence table, R2/R3 sub-phase decompositions, isolation mechanisms (branch/worktree, scope discipline, feature flags), tracker integration rule. Also added companion artifact reference: `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` (LIVING). Triggered by native question on parallelism with the active Query Trace Panel workstream. No structural changes to phases R0–R7; phasing and scope unchanged.
- **2026-04-29 v1.0.0 — initial draft**: First articulation of the unified UX vision that ties together the five existing in-flight portal surfaces (Login, Dashboard, per-client Build, per-client Consume, super-admin Cockpit) into a single journey, with Chart Profile as the missing keystone surface. Captures findings from a Cowork inspection of `platform/src/` on 2026-04-29. Authored by Cowork (Opus). To be promoted to `status: CURRENT` after R0 EXEC_BRIEF executes and the foundation phase lands.

---

## §1 — Mission

Render the MARSYS-JIS corpus legible to the native, to consenting audiences under the disclosure tiers in `MACRO_PLAN_v2_0.md §Ethical Framework`, and to acharya-grade reviewers, by re-composing the existing `platform/src/` codebase into a **chart-centric instrument** rather than a chat-with-status-panel utility.

The corpus is the product. The UI is the instrument. Modernization means making the rasi chart, the Vimshottari clock, the LEL, the pyramid completion ledger, and the prediction log immediately visible as the user enters a chart — not buried behind a chat composer.

This vision is bounded by `PROJECT_ARCHITECTURE_v2_2.md §B (Architectural Principles)`. Specifically: B.1 (facts/interpretation separation surfaces in the UI as Build vs Consume), B.3 (every L2.5+ claim shown in the UI must be one click from its `DERIVATION_LEDGER` entry), B.10 (no fabricated computation — chart visuals render from L1 forensic data only), B.11 (whole-chart-read discipline — Consume entry point composes MSR + UCN + CDLM + CGM + RM, never bypasses).

## §2 — Findings: what the codebase already gives us, and what it doesn't

A walk of `platform/src/` on 2026-04-29 produced the following inventory. The redesign is aggressively additive on top of this — almost no existing code is removed.

### §2.1 The brand and design-system spine (ready for use)

`platform/src/app/globals.css` declares a complete oklch palette: warm-vellum light surfaces (`--background: oklch(0.992 0.004 75)`, `--brand-vellum`), gold accents (`--brand-gold`, `--brand-gold-light`, `--brand-gold-deep`, `--brand-gold-cream`), and ink/charcoal dark surfaces (`--brand-charcoal`, `--brand-ink`). Type pairing: Source Serif 4 for headings, Inter for UI, Geist Mono for code. The shadcn/ui kit ships with all primitives the redesign needs (card, button, badge, dialog, sheet, dropdown-menu, tabs, scroll-area, separator, sonner, alert-dialog).

`platform/src/components/brand/` ships `Sigil.tsx` (24×24 8-petal mandala), `Mandala.tsx` (full motif), `Logo.tsx` (gold-glow 32–128 px lockup), `Wordmark.tsx`, `AssistantSigil.tsx`. The login page (`platform/src/app/login/page.tsx`) is cinematic and is **the one screen that needs no work**. Its visual language — mandala on a radial-vignetted ink field, gold filigree, Source Serif 4 — is the brand thesis the rest of the portal should pull toward.

### §2.2 The chat platform-within-the-platform (under-used)

`platform/src/components/chat/` is a fully-formed chat shell: `ChatShell`, `ConversationSidebar`, `AdaptiveMessageList`, `Composer`, `StreamingMarkdown`, `CommandPalette`, `ShareButton`, `ToolCallCard`, `ThemeToggle`, `MessageActions`, `ShortcutsDialog`, `ScrollToBottomButton`, `WelcomeGreeting`. The Consume tab uses all of it. The per-client Build tab (`platform/src/components/build/BuildChat.tsx`) uses **none of it** — it's a 1.0 chat with a basic input and a small status panel.

### §2.3 The Cockpit's rich governance widgets (siloed)

`platform/src/components/build/` ships an entire dense application: `CockpitGrid`, `JourneyStrip`, `PhaseGrid`, `BriefPanel`, `InsightCards`, `HealthSparkline`, `HealthTrend`, `MirrorPairsTable`, `ProgressBar`, `RegistryTable`, `RegistryGrouped`, `SessionTable`, `SessionTimeline`, `SessionDetail`, `PyramidStatusPanel`, `CorpusDensityHero`, `BuildVelocityStrip`, `FilterableActivityFeed`. These are wired into `/build` (the super-admin Cockpit) and **never compose into the per-client surfaces**. They could.

### §2.4 What's missing

1. **There is no Chart Profile page.** `platform/src/app/clients/[id]/page.tsx` is a five-line silent redirect. The "profile summary" the native explicitly named in the journey-narrative-of-record has no surface in the app today.
2. **"Build" denotes two different things in the same nav.** `/build` is the super-admin governance Cockpit; `/clients/[id]/build` is the per-chart corpus-construction chat. Same word, two apps, same avatar dropdown linking between them.
3. **The per-client Build chat is a v1 of what Consume is at v3.** It has none of `useChatSession`, `useBranches`, `useFeedback`, `useChatPreferences`, no streaming markdown, no model picker, no command palette, no trace.
4. **The Cockpit's widgets never compose into the per-client view.** `JourneyStrip`, `BriefPanel`, `InsightCards`, `MirrorPairsTable` are sized exactly right to inhabit the right pane of a per-client Build cockpit. They sit unused there.
5. **The Roster (`/dashboard`) is undersized.** `ClientRoster` is a card grid with no search, no filters, no view toggle, no stats ribbon, no freshness signal. Fine at one client, breaks down at ten.
6. **Theme switches at module boundaries.** Vellum-light in Roster/per-client-Build/Cockpit/Admin, ink-dark in Consume (`ConsumeForceDark`). There's no bridge surface; the user crosses an unmarked seam each time. The login screen's gold-on-ink cinema never reappears once the user is inside.
7. **The corpus's most discipline-critical artifacts — LEL events and prospective predictions per `MACRO_PLAN_v2_0.md §Cross-cutting workstreams` and `CLAUDE.md §E` — have no UI surface.** A native who logs in cannot see "what predictions am I holding open this month? what events have I logged this quarter?"

These seven findings drive the redesign's six surfaces.

## §3 — The vision: "The Chart Room"

Each chart is **a room you walk into**. The metaphor is a Jyotish observatory: the chart sits at center, instruments arrange around it, provenance is one peek away. Three principles drive every surface decision:

**P1 — The corpus is the product.** Every chart-context surface either renders the corpus or modifies the corpus. The chat is one of three or four ways to interrogate the corpus, not the entry point.

**P2 — Reuse over rebuild.** Every component built for the Cockpit and the Consume chat already meets acharya-grade quality in its own surface; the redesign re-composes them into surfaces that don't exist yet. The redesign authors very few new components and removes none of the existing ones.

**P3 — Brand cohesion via theme zones, not theme switches.** The vellum-light surfaces and the ink-dark Consume surface stay. A new **bridge zone** — Chart Profile — uses light page chrome with a gold-on-dark hero so the cinema of the login screen returns at the moment the user enters a chart. The mandala motif from login becomes a recurring grace note: faint behind the Chart Profile hero, as a focus indicator on the pyramid layer that just completed, in the Roster zero-state.

### §3.1 The six surfaces

**Surface 0 — Login.** Untouched. Already cinematic, already on-brand, already correct.

**Surface 1 — Global AppShell (NEW, replaces three current headers).** Single shell, present on Roster / Chart Profile / Build / Consume / Cockpit / Admin. Components:
- Thin left rail: `Sigil` at top, `Roster` link, `Cockpit` link (super_admin only), `Admin` link (super_admin only), avatar at bottom with dropdown (Sign out, theme toggle).
- Top breadcrumb: `Roster · {ChartName} · {Mode}` where Mode is one of `Profile | Build | Consume | Timeline`.
- Replaces `DashboardHeader`, `BuildHeader` (the cockpit one), and the per-chart context strip currently inside the `clients/[id]` layout.

**Surface 2 — Roster (revamped `/dashboard`).** Composition of existing primitives:
- Stats ribbon (top): "{N} charts · {n_active_build} in active build · {n_consumed_today} consumed today · {n_overdue_predictions} predictions overdue".
- Search + filter row: by name, place, current dasha, build %, last activity, audience tier.
- View toggle: `Grid | Table`. Grid keeps the upgraded `ClientCard`; Table reuses `RegistryTable` from the Cockpit (already excellent at dense lists).
- Card upgrade: name, date·place, build %, plus a one-line "moment phrase" — "Saturn–Jupiter · last queried 4d ago · 2 predictions open" with a small health dot.
- Zero-client state: brand-styled wizard with the Mandala motif as a focal element.

**Surface 3 — Chart Profile (NEW `/clients/[id]`).** The keystone of the redesign. Removes the silent redirect. Layout, top to bottom:
- **Hero band**: rasi chart rendered as gold linework on dim charcoal — the only surface besides login that uses the ink-zone — with the Mandala motif as a faint backdrop. Native's name in Source Serif 4. Birth coords + time underneath. The chart is rendered from L1 forensic data only (B.10 compliance — no fabricated numerical values).
- **Three "rooms" as large cards**:
  - **Build Room** — pyramid completion as a small inline `JourneyStrip`, last build activity, "Continue building" CTA → `/clients/[id]/build`.
  - **Consume Room** — last 3 conversations, top reports preview, "Ask anything" CTA → `/clients/[id]/consume`.
  - **Timeline Room** — last 3 LEL events, active prospective predictions, "Open timeline" CTA → `/clients/[id]/timeline` (route lands in R5).
- **Side rail**: at-a-glance metadata. Current Vimshottari Maha–Antar–Pratyantar (with countdown), top 3 yogas, freshness banner, audience-disclosure tier display, super-admin-only audit deep-link to L1 forensic data and `DERIVATION_LEDGER`.
- **Footer**: governance breadcrumb (audience tier, scope, last close, mirror pair status) — super_admin only.

**Surface 4 — Build mode (`/clients/[id]/build`) — three-pane cockpit.** Replaces the current lightweight `BuildChat`. Layout:
- Left: `ConversationSidebar` (existing component, currently used in Consume).
- Center: `AdaptiveMessageList` + `Composer` + `StreamingMarkdown` (the same hooks Consume uses — `useChatSession`, `useBranches`, `useFeedback`, `useChatPreferences`).
- Right: a stack of existing widgets — `JourneyStrip` for layer progress, `BriefPanel` for current intent, `InsightCards` for recently-built artifacts, a compact `MirrorPairsTable` summary, the existing `PyramidStatusPanel` collapsed by default.

The build endpoint (`/api/chat/build`) needs to ride on the same hook stack as Consume's endpoint (`/api/chat`); R3 begins with an audit of that hook compatibility before any UI changes ship.

**Surface 5 — Consume mode — polish, not rebuild.** Mature. Three small moves:
- `ReportLibrary` re-rendered as a gallery of cards (domain icon + freshness + click-into-reader) instead of a flat list.
- `TracePanel` collapsed into a side drawer, triggered from each answer's footer (currently always-visible mode is information-overload for non-super-admin tiers).
- Audience-tier picker explicit — super_admin can flip between client/admin/super_admin views to QA the same answer surface (closes a finding from Phase 11A debug brief).
- "Log this prediction" action when an answer contains a time-indexed claim — writes to `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` prediction subsection per `CLAUDE.md §E`. After `06_LEARNING_LAYER/` is scaffolded (M11), this action migrates to that home with no UI change.

**Surface 6 — Cockpit (rename `/build` → `/cockpit`, super_admin only).** Internals untouched. Three changes:
- Route rename. Permanent 301 from `/build` so nothing external breaks. `BuildHeader` updated. The `/build/*` sub-routes (`/plan`, `/sessions`, `/registry`, `/interventions`, `/parallel`, `/health`, `/activity`) move under `/cockpit/*` with the same redirect.
- Promoted into the global AppShell left rail for super_admin.
- New widget on `CockpitGrid`: "Active charts" — links into Chart Profile pages, closes the loop between governance and per-chart instruments.

### §3.2 Theme zones

Three zones, never mid-page mode flips:

| Zone | Surfaces | Background | Accent | Heading type |
|------|----------|------------|--------|--------------|
| Vellum | Roster, Build, Cockpit, Admin | `--background` (warm vellum) | `--brand-gold-deep` | Source Serif 4 |
| Ink | Consume, Login | `--brand-ink` | `--brand-gold` / `--brand-gold-light` | Source Serif 4 |
| Bridge | Chart Profile | Vellum page chrome, **ink hero band** | gold linework on the chart | Source Serif 4 |

The Bridge zone is the only mixed-mode surface. It uses CSS scoping so the gold-on-dark hero doesn't bleed into the rest of the page. (R0 codifies the scoping rule.)

### §3.3 Mobile

Currently desktop-first. Each phase ends with a mobile pass on its target surface.
- Chart Profile: hero on top, three rooms stacked vertically, side rail collapsed to a sheet trigger.
- Build/Consume: existing `ChatShell` mobile responsiveness inherited.
- Roster: grid drops to 1-col, table view hidden behind a "View as table" link.

### §3.4 Motion and ambient detail

- Mandala motif as a faint, slowly-rotating backdrop on Chart Profile hero (≤8% opacity, paused on `prefers-reduced-motion`).
- Pyramid `ProgressBar` and percent rings animate when underlying layer status changes.
- Subtle "ascend" transition when entering Build/Consume from a Chart Profile room card.
- Streaming dots and `StreamingMarkdown` cadence inherited from Consume.

### §3.5 What this vision is NOT

- Not a brand-system rewrite. Every token in `globals.css` stays.
- Not a login redesign.
- Not a deletion of any existing component. Even ones the redesign doesn't end up using stay until a separate cleanup pass authored as its own phase.
- Not a change to the pyramid data model, the auth/role model, the conversation model, the reports model, or any DB schema.
- Not a change to the Phase 11A query pipeline (`classify → compose → retrieve → synthesize → audit`) — the redesign sits entirely on top of it.
- Not a `python-sidecar` change.
- Not a re-introduction of L2 surfaces (L2 was archived in Phase 14F per `EXEC_BRIEF_PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_v1_0.md`).

## §4 — Phased execution plan

Each phase is a closed-artifact-per-session per `CLAUDE.md §M`. Each phase ends with a screenshot-diff pack, a Playwright smoke on the affected route, and a `mirror_enforcer.py` + `drift_detector.py` + `schema_validator.py` pass. No schema or migration changes are introduced anywhere.

| Phase | Surface | Key deliverable | New components | Risk |
|-------|---------|-----------------|----------------|------|
| **R0** | Foundation | AppShell + theme bridge + `/build → /cockpit` rename with permanent 301 | `<AppShell>`, `<Breadcrumb>`, `<ZoneRoot>` (theme scope) | LOW — navigation surfaces only |
| **R1** | Roster | Stats ribbon + search/filter + grid/table toggle + upgraded `ClientCard` + zero-state wizard | `<RosterStatsRibbon>`, `<RosterFilters>`, `<RosterTableView>` (composed from `RegistryTable`), `<MomentPhrase>` | LOW — additive over `/dashboard` |
| **R2** | Chart Profile | NEW `/clients/[id]` page, hero with rasi chart, three rooms, side rail | `<RasiChartSVG>`, `<ChartHero>`, `<RoomCard>`, `<ProfileSideRail>`, `<DashaCountdown>` | MEDIUM — first new page; rasi renderer is the only real new build |
| **R3** | Build mode upgrade | Swap `BuildChat` for the Consume shell; compose right-pane widgets | (no new components — re-composition) | MEDIUM — `/api/chat/build` hook compatibility audit needed first |
| **R4** | Consume polish | Report gallery + trace drawer + tier picker + prediction-log action | `<ReportGallery>`, `<TraceDrawer>`, `<TierPicker>`, `<LogPredictionAction>` | LOW |
| **R5** | Timeline | NEW `/clients/[id]/timeline` reading from LEL + prediction log | `<TimelineView>`, `<PredictionTable>`, `<EventCard>`, `<LogEventDialog>` | MEDIUM — new route, but no schema change (LEL is already a markdown file) |
| **R6** | Cockpit elevation | Promote to AppShell rail; "Active charts" widget | `<ActiveChartsWidget>` | LOW |
| **R7** | Polish | Accessibility audit, mobile pass, animation timings, perceived-perf | (no new components) | LOW |

Recommended cadence: one phase per Claude Code session, in order. R5 is the only one safely deferrable.

### §4.1 Risks and gates

**G1 (R2) — rasi-chart renderer.** Decision recorded 2026-04-29 (native call): build a small SVG component from L1 forensic data; do **not** import an external Vedic-chart library. Rationale: full brand control, zero new dependencies, deterministic rendering from existing facts (B.10 compliance). Acceptance: renderer accepts a `ForensicChart` prop typed against `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` and emits a North Indian (or South Indian, native preference TBD in R2 brief) rasi diagram in the brand spine palette.

**G2 (R3) — Build endpoint hook compatibility.** Before any UI swap, an audit confirms `/api/chat/build` can ride on `useChatSession` / `useBranches` / `useFeedback` or specifies a thin adapter. R3 brief authors this audit as its first task; if the adapter exceeds 80 lines, R3 splits.

**G3 (R0) — theme-zone CSS scoping.** The Bridge zone's mixed light/dark composition needs a CSS-variable scoping rule that doesn't conflict with `next-themes` or the existing `ConsumeForceDark` pattern. R0 brief specifies the exact scoping rule; if it requires a refactor of `ForceDarkMode`, that refactor is captured as its own sub-task.

**G4 (every phase) — mirror discipline.** Per `CLAUDE.md §K`, any governance file touched on the Claude side gets its `.geminirules` / `.gemini/project_state.md` counterpart updated in the same session. The redesign primarily touches `platform/src/` (no Gemini-side counterpart per declared mirror_pairs), but if any phase brief touches `00_ARCHITECTURE/`, mirror discipline applies.

### §4.2 Reuse-vs-rebuild ledger

| Existing asset | Phase that reuses it | Reuse mode |
|----------------|---------------------|-----------|
| `globals.css` (brand tokens) | all | unchanged, referenced |
| `brand/Sigil`, `brand/Mandala`, `brand/Logo`, `brand/Wordmark` | R0, R2, R7 | unchanged |
| `ui/*` (shadcn primitives) | all | unchanged |
| `chat/ChatShell`, `chat/ConversationSidebar`, `chat/AdaptiveMessageList`, `chat/Composer`, `chat/StreamingMarkdown`, `chat/CommandPalette`, `chat/ShareButton` | R3, R4 | composed into per-client Build (R3), polished in Consume (R4) |
| `build/JourneyStrip`, `build/BriefPanel`, `build/InsightCards`, `build/MirrorPairsTable`, `build/PyramidStatusPanel`, `build/ProgressBar` | R3 | composed into per-client Build right pane |
| `build/CockpitGrid`, `build/SessionTimeline`, `build/RegistryTable`, `build/HealthSparkline`, etc. | R6 (Cockpit polish), R1 (Roster table view reuses `RegistryTable`) | unchanged in Cockpit; `RegistryTable` reused for Roster table view |
| `consume/ConsumeChat`, `consume/AnswerView`, `consume/StreamingAnswer`, `consume/ReportLibrary`, `consume/ReportReader`, `consume/ValidatorFailureView`, `consume/DivergenceReport` | R4 | unchanged shell; `ReportLibrary` re-rendered as gallery |
| `dashboard/ClientCard`, `dashboard/ClientRoster`, `dashboard/DashboardHeader` | R1 (cards), R0 (header replaced by AppShell) | `ClientCard` upgraded; `DashboardHeader` retired |
| `auth/ForceDarkMode`, `consume/ConsumeForceDark` | R0 | replaced by `<ZoneRoot>` theme scope |
| login (`app/login/page.tsx`) | none | unchanged |
| admin (`app/admin/`) | R0 only (gets AppShell wrapper) | internals unchanged |
| `app/audit/`, `app/share/` | none | unchanged |

Net new component count: ~11 (R0: 3, R1: 3, R2: 5, R4: 4, R5: 4, R6: 1; some shared). Net deleted: 0. Net retired-via-replacement: 3 (`DashboardHeader`, `ForceDarkMode`, `ConsumeForceDark` — superseded by AppShell + ZoneRoot).

### §4.3 Parallelism guidance

The redesign is engineered to fan out after R0 lands. This section names the dependency edges, the safe-parallel sets, the sub-phase decompositions inside R2 and R3, the one collision with the active Query Trace Panel workstream, and the isolation mechanisms that keep parallel tracks from stepping on each other. The companion artifact `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` carries the per-phase `parallelizable_with: [...]` field as the operational source of truth; this section is the rationale.

#### §4.3.1 Phase-level dependency graph

```
                       ┌── R1 Roster ─────────┐
R0 Foundation ─────────┤                      │
                       ├── R2 Chart Profile ──┤
                       │      └── R3 Build ───┤── R7 Polish (final)
                       │                      │
                       ├── R5 Timeline ───────┤
                       │                      │
                       └── R6 Cockpit ────────┘

                       (R4 Consume polish slots in
                        after the trace fix lands)
```

Hard dependencies: R0 must land first because every other phase consumes `<AppShell>` and `<ZoneRoot>`. R3 must land after R2 because R3's "Continue building" CTA originates in R2's Build Room card. R7 must land last because it touches every surface for accessibility and mobile audits. Everything else is independent post-R0.

Best-case wall-clock sequence with parallelism: R0 (sequential, 1 session), then a parallel wave of {R1, R2, R5, R6} (~3 sessions of wall-clock if four worktrees run concurrently), then R3 (~2 sessions, after R2 closes), then R4 (~1 session, after the trace fix merges), then R7 (~1 session). Total: ~7–8 wall-clock days versus ~10–13 if executed strictly sequentially.

#### §4.3.2 Co-existence with the Query Trace Panel workstream

**Status as of v1.0.2 (2026-04-29): trace-fix workstream is ON HOLD per native decision.** The collision that previously gated R4 is dissolved. R4 fans out alongside R1, R2, R5, R6 post-R0 like any other independent phase. This subsection retains its original analysis below for the case where trace work resumes.

The Query Trace Panel `conversation_id` propagation fix touches `consume/route.ts`, `single_model_strategy.ts`, the `SynthesisRequest` type, and `TracePanel.tsx`. The redesign's `must_not_touch` blocks for R0–R3 explicitly exclude `app/api/**`, the synthesis strategies, and the consume component tree. Per-phase verdict (when trace fix is in flight):

| Phase | Touches trace-fix surface? | Verdict (when trace fix is in flight) |
|-------|---------------------------|---------------------------------------|
| R0 | No — navigation surfaces and theme tokens only | Safe parallel |
| R1 | No — `/dashboard` and `components/dashboard/` only | Safe parallel |
| R2 | No — new files only, plus a one-line href change in `ClientCard` | Safe parallel |
| R3 | Composes existing chat components but does not modify them | Safe parallel **iff** R3 does not begin before the trace fix has merged |
| **R4** | **Direct collision — R4 turns `TracePanel` into a drawer; trace fix edits the same component** | **Serialize. Trace fix lands first, then R4. (DORMANT while trace fix is on hold.)** |
| R5 | No — new route + LEL surface only | Safe parallel |
| R6 | No — `/cockpit` internals untouched, `<AppShell>` rail addition only | Safe parallel |
| R7 | Touches every surface by definition | Last, after both lines merge |

**Resumption rule.** If the trace-fix workstream resumes after R4 has already merged: trace-fix authoring rebuilds against R4's `<TraceDrawer>` surface (the drawer becomes the canonical Trace component; trace-fix work merges its `conversation_id` propagation into the drawer's render path). If trace fix resumes before R4 starts: revert to the original "trace fix lands first, then R4" rule. The tracker's `trace_fix_status` field (`on_hold | in_flight | merged`) is the operational signal for which rule applies; the session opening R4 reads it before proceeding.

#### §4.3.3 Sub-phase decomposition within R2 and R3

R2 (Chart Profile) decomposes into three slices that fan out:

- **R2a** — `RasiChartSVG` is a pure leaf component. Takes a typed `ForensicChart` prop, emits SVG. Zero dependency on `<AppShell>`, theme zones, or any other R-phase. Could even land before R0 if you wanted to start the renderer in parallel with R0's foundation work.
- **R2b** — `RoomCard`, `ProfileSideRail`, `DashaCountdown` are independent of each other and of R2a. Three parallel authoring streams possible.
- **R2c** — `ChartHero` + the page composition + tests + B.10 visual verification. Requires R2a and R2b. Sequential after both.

Result: R2 split-three-ways collapses to 2 wall-clock sessions instead of 3 (one session for R2a + R2b in parallel, one session for R2c).

R3 (Build mode upgrade) decomposes into two slices:

- **R3a** — Hook-compatibility audit (gate G2 from §4.1). Independent investigation; produces a written audit naming whether `useChatSession` / `useBranches` / `useFeedback` accept the build endpoint as-is or need an adapter. No code changes.
- **R3b** — UI swap (replace `BuildChat` shell, compose right-pane widgets). Requires R3a.

R3a and R3b can be authored as a single brief but executed across two sessions, or split into separate briefs for cleaner accountability.

R0, R1, R4, R5, R6, R7 are not split further — their internals are tight enough to fit one session each.

#### §4.3.4 Isolation mechanisms

Three mechanisms keep parallel tracks from stepping on each other:

**Branch and worktree isolation.** One branch per active track (`redesign/r0-foundation`, `redesign/r1-roster`, `redesign/r2-profile`, etc.). One git worktree per concurrent Claude Code session. The Anti-Gravity / VS Code setup the EXEC_BRIEFs target supports this natively. Tracks merge to `main` independently as each phase closes; conflicts are minimal because the `may_touch` sets are disjoint by design.

**Scope discipline already baked into briefs.** Every R-phase brief declares `may_touch` / `must_not_touch` per `GOVERNANCE_INTEGRITY_PROTOCOL §F`. Two parallel tracks whose `may_touch` sets do not intersect cannot collide. The R0–R7 briefs are written this way deliberately. R4's `may_touch` overlaps with the trace fix's, which is exactly what surfaces the collision in §4.3.2 above.

**Feature flags for ambient main-line changes.** R0's `/build → /cockpit` rename is the one move that affects every other phase, so it lands first and merges before any other phase begins. For phases that ship visible UI changes, a `PORTAL_REDESIGN_RN_ENABLED` env flag gated on `configService.getFlag()` lets each phase merge to `main` incrementally without flipping user-visible behavior all at once. Same pattern as `NEW_QUERY_PIPELINE_ENABLED` and `AUDIT_ENABLED` from Phase 11A. The flag is removed in R7 along with the legacy code paths.

#### §4.3.5 Operational rule for the tracker

The tracker artifact's `parallelizable_with` field on each phase row is updated whenever a phase's status changes. When a session opens an EXEC_BRIEF, it reads the tracker's `parallelizable_with` for that phase first — if the named-parallel phases are all `pending` or `closed`, the session proceeds; if any named-parallel phase is `in_flight` and shares any `may_touch` glob, the session halts and emits a `parallelism_collision` block before attempting any tool call. This rule is enforced advisorily in v1.0 and via a small `parallelism_check.py` governance script in a follow-on hardening pass.

## §5 — Acceptance criteria for the vision (when is this DONE?)

The redesign is complete when:

1. A super-admin landing on `/` sees the Roster with a stats ribbon, can search and filter, can toggle grid/table, and reaches a chart in ≤2 clicks.
2. A native landing on `/clients/{id}` sees the Chart Profile — hero, three rooms, side rail, dasha countdown, freshness banner — and can reach Build, Consume, or Timeline in 1 click.
3. The per-client Build chat has feature parity with the Consume chat (sidebar, branches, streaming, model picker, command palette) and the right pane composes `JourneyStrip` + `BriefPanel` + `InsightCards`.
4. The Consume chat surfaces the audience-tier picker for super-admin, the trace as a drawer, and a "Log this prediction" action on time-indexed claims.
5. Theme zones never flip mid-page. Mode crossings happen only at navigation boundaries.
6. Mobile pass passes Lighthouse a11y ≥ 95 on all six surfaces.
7. No existing component is deleted. No schema migration is introduced. No `python-sidecar` change is introduced. No auth/role-model change is introduced.
8. Each phase's `mirror_enforcer.py` + `drift_detector.py` + `schema_validator.py` exit 0.

## §6 — Promotion to CURRENT

This artifact promotes from `status: DRAFT` to `status: CURRENT` when:

- The R0 EXEC_BRIEF executes and lands the AppShell + `/build → /cockpit` rename.
- An entry is added to `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md §1` as `canonical_id: PORTAL_REDESIGN_VISION`.
- The `CLAUDE.md §C — Mandatory reading (per session)` list adds this artifact at item 12 (or appropriate position).
- A session-close emits `mirror_updates_propagated` reflecting the addition (Claude-only mirror, declared `mirror_pair: none`).

Until then this artifact is informational and any session is free to challenge or amend it.

---

*End of PORTAL_REDESIGN_VISION_v1_0.md (DRAFT, 2026-04-29).*

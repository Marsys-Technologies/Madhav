---
artifact: PORTAL_BUILD_TRACKER_PLAN_v0_2.md
version: 0.2
status: APPROVED_FOR_IMPLEMENTATION
authored_by: Claude Code Opus 4.6 (Madhav_PORTAL_BUILD_TRACKER_PLAN_v0_2)
authored_on: 2026-04-26
predecessor: 00_ARCHITECTURE/PORTAL_BUILD_TRACKER_PLAN_v0_1.md (status IMPLEMENTED, v0.1.3)
governing_prompt: elaborate_v0_2.md (Cowork-authored, 2026-04-26)
target_implementation_executor: Claude Code, Sonnet 4.6
implementation_session_naming: Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_2_1 .. _v0_2_3
halt_after_native_review: false
---

# PORTAL BUILD TRACKER — v0.2 Implementation Plan

## Context

v0.1 closed with all 28 ACs PASS. Architecturally sound (RSC, GCS shards,
role-gated). The native ran the live portal and was unimpressed: the cockpit
reads as a status page, not a research-instrument cockpit. Native named two
specific bugs (sub-phase ordering broken; only M2 expandable) and one
structural ask ("colours, graphs, modern UI"). Cowork inspection surfaced 13
deeper depth-issues — corpus state invisible, off-plan velocity not exposed,
intervention surface factually empty, no insight derivations, flat visual
hierarchy, AC rows minimal, no real charts on a knowledge-graph project. v0.2
closes this gap.

Three ground-truth findings from Phase 1 exploration:

1. **Sub-phase serializer bug root cause confirmed.** Greedy regex at
   `platform/scripts/governance/serialize_build_state.py:416–418` matches
   earliest hit in the file. Document-structure dividers (`### B.1 — Restatement`
   etc., lines 37–73 of PHASE_B_PLAN) win over the real definitions (`### Phase B.N
   — Title (N session)`) in §G (lines 455+). Two analogous greedy patterns: `_read_macro_arc()`
   (masked by hardcoded fallback) and `_read_native_directives()` (no fallback, silent).
2. **PlanTree expansion is data-driven.** `PlanTree.tsx:35` gates sub-phase children
   on `m.id === activeMacroId`. Fix is: serializer emits `macro_arc[].milestones` for
   every M1–M10; PlanTree tracks an expansion `Set<string>` ('use client').
3. **No chart library. No semantic color system.** All color is single-hue warm-neutral
   oklch. No status/class/severity palettes. v0.2 adopts Recharts and a three-dimension
   color system.

## §1 — Decisions

| ID | Decision | Rationale |
|---|---|---|
| **D.1** | **Adopt Recharts** | v0.2 needs ≥5 chart types; Recharts ~25KB gz/chart with tree-shaking; ergonomics >> hand-rolled SVG for axes/tooltips/legends |
| **D.2** | **Scope (b+):** targeted bug-fixes + redesign cockpit, plan, phase-detail; light color/Recharts pass on health/activity/intervention | Native tone says full redesign; (b+) covers all named complaints in 3 sessions; cosmetic-only routes to v0.3 |
| **D.3** | **Backfill via annotation file** `00_ARCHITECTURE/INTERVENTION_BACKFILL_v1_0.md` | Constraint §6 forbids retroactive SESSION_LOG edits; annotation file keeps audit trail intact |
| **D.4** | **Defer annotations layer to v0.3** | Read-write surface needs server actions, persistence, conflict resolution — out of scope |
| **D.5** | **Defer SSE to v0.3** | Needs file-watcher + Pub/Sub; not on path to closing named complaints |
| **D.6** | **3 implementation sessions** | Session 1: serializer + types; Session 2: cockpit/plan/detail redesign; Session 3: health/activity/intervention + backfill |
| **Seq** | **α: v0.2 before Exec_7** | Native: "fix the dashboard before staring at it during M2 work" |

## §2 — Bug-Fix Register

### BF.1 — Sub-phases serializer parses wrong headers

- **File:** `platform/scripts/governance/serialize_build_state.py`, function `_read_phase_b_plan()`, lines 409–430.
- **Root cause:** regex `^###+\s+(?:Phase\s+)?(B\.\d+(?:\.\d+)?)\s+[—-]+\s+(.+?)$` is
  position-agnostic; document §B dividers (lines 37–73) match before §G real definitions.
- **Fix:** locate anchor `## G. Expanded Phase Plan` in file text; slice `text[anchor_idx:]`
  before regex; tighten pattern to require literal `Phase ` prefix and parenthesized session
  count: `^###\s+Phase\s+(B\.\d+(?:\.\d+)?)\s+—\s+(.+?)\s+\((\d+)`. Use custom int-segment
  sort so B.3.5 sorts between B.3 and B.4.
- **Verification:** `phase_plan.sub_phases` has exactly 12 entries: B.0, B.1, B.2, B.3, B.3.5,
  B.4, B.5, B.6, B.7, B.8, B.9, B.10 — in that order.

### BF.2 — Macro-arc emits milestones only for M2

- **File:** `serialize_build_state.py`, `_read_macro_arc()` lines 433–467 + `types.ts` `MacroPhaseEntry`.
- **Symptom:** PlanTree children only show for active macro (M2); M1 and M3–M10 have no milestones.
- **Fix:** extend `MacroPhaseEntry` with `milestones: Milestone[]`. Parse milestones per macro from
  MACRO_PLAN acceptance-criteria sections; M2 reuses parsed phase_b_plan entries. M1 gets 8 milestones
  from M1 exit criteria. M3–M10 get a single placeholder if exit criteria are prose-only.
  Remove hardcoded fallback; raise `ValueError` if fewer than 10 entries parsed with explicit warning.
- **Verification:** every entry in `macro_arc` has `milestones[]` with length ≥ 1; M1 has 8; M2 has 12.

### BF.3 — sessions_index ordering

- **File:** `serialize_build_state.py`, `_parse_all_sessions()`.
- **Fix:** sort the resulting list by `date` (ISO string, descending = newest first) after parsing.
  Add explicit comment: "SESSION_LOG block order is file-position; we re-sort chronologically."
- **Verification:** sessions_index[0].date ≥ sessions_index[-1].date (newest-first).

### BF.4 — Cockpit recent-activity depth

- **File:** `platform/src/app/build/page.tsx` (via `CockpitGrid.tsx`).
- **Fix:** raise from 3 to 7. Add pill-style "All activity →" link.
- **Verification:** cockpit shows 7 rows; link present.

### BF.5 — Phase-detail acceptance_criteria minimal rows

- **File:** `serialize_build_state.py`, `_assemble_phase_detail()`; `platform/src/app/build/plan/[phase_id]/page.tsx`.
- **Fix:** extend `acceptance_criteria[]` items with `description`, `test`, `result_snippet`, `residual_id`.
  Serializer reads these from the PHASE_B_PLAN §G section for each sub-phase. UI: collapsible row
  (ac_id + status always visible; description/test/result on expand).
- **Verification:** B.0 AC rows expand to show description + test.

### BF.6 — Greedy regex in _read_native_directives

- **File:** `serialize_build_state.py`, `_read_native_directives()` lines 310–335.
- **Fix:** require presence of a canonical section anchor before parsing. Add `serializer_warnings[]`
  to top-level output so silent failures surface.
- **Verification:** `serializer_warnings` key present in emitted JSON.

## §3 — Color System (`platform/src/components/build/colors.ts`)

Three palette dimensions defined as a single source of truth:

### Status palette
| Token | Use | Light (oklch) |
|---|---|---|
| `status.complete` | done | `0.78 0.13 145` (green) |
| `status.active` | in-progress | `0.78 0.13 75` (warm gold) |
| `status.pending` | not started | `0.85 0.01 75` (neutral muted) |
| `status.blocked` | failed/blocked | `0.62 0.20 27` (red) |

### Session-class palette (8 classes)
| Class | Color |
|---|---|
| `m2_corpus_execution` | `0.62 0.16 245` (blue) |
| `governance_aside` | `0.60 0.17 295` (purple) |
| `planning_only` | `0.65 0.10 200` (cyan) |
| `fix_session` | `0.70 0.16 50` (orange) |
| `red_team` | `0.62 0.20 27` (red) |
| `brief_authoring` | `0.68 0.10 110` (yellow-green) |
| `native_intervention` | `0.55 0.18 330` (magenta) |
| `cowork_orchestration` | `0.65 0.05 75` (warm-neutral) |

### Severity palette
| Token | Use |
|---|---|
| `sev.baseline` | exit code 2, accepted | green |
| `sev.medium` | new findings, low-sev | amber |
| `sev.high` | regressions | red |
| `sev.info` | neutral | warm-neutral |

## §4 — Wireframes (prose)

### Cockpit (`/build`)

1. **JourneyStrip** — kept; add status-color dots per macro-phase.
2. **Corpus density hero strip — NEW.** Three large stat cards row:
   - Card A: `rag_chunks` (bt-mega, ~3rem). Below: stacked bar of chunks-by-doc-type.
   - Card B: `graph_nodes / graph_edges`. Two big numbers separated by `/`. Below: edge-class breakdown radial.
   - Card C: `L3 coverage M / 9`. Below: 9 dots color-coded by coverage status.
3. **Where I am + Today** — kept; Today card gets equal weight; deliverables get session-class pill.
4. **Build velocity strip — NEW.** Full-width, 3 columns:
   - Sessions cadence area chart (x=day, y=sessions/day, last 30d).
   - On-plan vs off-plan donut (segmented by session_class into 2 buckets).
   - Intervention frequency sparkline.
5. **Insight cards — NEW.** 2-column grid, up to 6 derived narrative items.
6. **Priorities + Pending** — retained but denser (row-style, not full Cards).
7. **Recent activity** — 7 sessions; session-class pill per row.

### Plan view (`/build/plan`)

- **Left sidebar** — PlanTree updated: all M1–M10 expandable. Default: M2 open, others closed. URL `?expanded=M1,M2` sync. Each macro row has status-dot from milestones aggregate.
- **Center** — phase-grid replacing list: 3-column grid of 12 sub-phase cards (B.0–B.10+B.3.5). Each card:
  - Header: `phase_id` (mono) + status badge + days-since-touched.
  - Title (bt-heading).
  - Two-line meta: `session_count_actual / session_count_estimated`; AC progress `X of Y`.
  - Inline ProgressBar for AC pass-rate.
  - Inline ProgressBar for deliverables.
  - Footer: last-touched session link.
  - Click → `/build/plan/[phase_id]`.
- **Right panel** — kept; populated with selected phase brief.

### Phase detail (`/build/plan/[phase_id]`)

- **Header strip**: status + session-counts + AC funnel + deliverables funnel.
- **AC section**: collapsible rows — `ac_id` + title + badge collapsed; description + test + result + residual link expanded.
- **Sessions contributed**: Recharts `BarChart` (x=session_id, y=deliverables count).
- **Carry-forwards / Residuals card** — retained.
- **Dependencies card** — retained.

## §5 — Recharts Chart Inventory

| View | Chart | Recharts component | Data |
|---|---|---|---|
| Cockpit | corpus chunks by doc-type | `BarChart` (stacked) | `corpus_state.chunks_by_doc_type` |
| Cockpit | edge-class radial | `RadialBarChart` | `corpus_state.edge_classes` |
| Cockpit | sessions cadence | `AreaChart` | `sessions_index` binned by day |
| Cockpit | on-plan vs off-plan | `PieChart` (donut) | `sessions_index` grouped by class |
| Cockpit | intervention frequency | `LineChart` | intervention events |
| Phase detail | sessions contributed | `BarChart` | `sessions[]` |
| Health | drift / schema / mirror trends | `LineChart` × 3 | `scripts_trend.*` |
| Activity | session cadence timeline | `ScatterChart` | `sessions_index` |
| Intervention | frequency over time | `BarChart` | derived |

## §6 — New `corpus_state` Field

New top-level block in `build-state.json` (`schema_version: 0.3.0`):

```json
"corpus_state": {
  "rag_chunks": 993,
  "rag_graph_nodes": 1735,
  "rag_graph_edges": 3814,
  "msr_signals": 499,
  "cgm_nodes": 234,
  "cgm_reconciled_edges": 22,
  "l3_reports_current": 9,
  "chunks_by_doc_type": [{"doc_type": "MSR_signals", "count": 499}],
  "edge_classes": [{"class": "rules-from", "count": 1200}],
  "l3_coverage": [{"domain_id": "SUN", "status": "covered"}]
}
```

New serializer reader: `_read_corpus_state(repo_root)`. Sources:
- `verification_artifacts/RAG/chunking_report.json` — rag_chunks, chunks_by_doc_type
- `platform/python-sidecar/rag/graph.py` / `verification_artifacts/RAG/` JSON — nodes/edges
- `025_HOLISTIC_SYNTHESIS/CGM_v2_0.md` — cgm_nodes, cgm_reconciled_edges
- `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` — msr_signals (count of SIG.NNN patterns)
- `04_DOMAIN_REPORTS/` — l3_reports_current (count of current reports)

## §7 — Macro-arc Milestone Data Shape

```typescript
interface Milestone {
  id: string           // 'M1.1', 'B.0', 'M3.0'
  title: string
  status: 'completed' | 'active' | 'pending'
  session_count_actual?: number
  session_count_estimated?: number
}

interface MacroPhaseEntry {
  id: string
  title: string
  status: 'completed' | 'active' | 'pending'
  milestones: Milestone[]
}
```

## §8 — Insight Surface (`platform/src/lib/build/insights.ts`)

Pure functions → `{id, severity: 'info'|'positive'|'concern', text}[]`:
- `phaseOnPlan(state)` — "B.X closed in N vs M sessions — on/over plan"
- `driftBaselineHolding(state)` — "N sessions at exit 2 baseline"
- `offPlanShare(state)` — "21% of M2 sessions off-plan"
- `cadenceProjection(state)` — "If cadence holds, M2 closes in ~N sessions"
- `interventionFrequency(state)` — interventions last 7 vs prior 7
- `mirrorFreshness(state)` — flag any MP pair not verified in >14 days

## §9 — Files Touched (Implementation Map)

### Session 1 (Serializer + data shape + types)
- `platform/scripts/governance/serialize_build_state.py` — BF.1, BF.2, BF.3, BF.6, corpus_state, serializer_warnings, session_count_estimated on sub_phases
- `platform/src/lib/build/types.ts` — extend all new fields (milestones, corpus_state, serializer_warnings, sub_phase.session_count_estimated)

### Session 2 (Visual redesign — cockpit, plan, phase-detail)
- `platform/package.json` — add `recharts`
- `platform/src/components/build/colors.ts` — NEW
- `platform/src/app/globals.css` — extend bt-* tokens; add bt-mega; status/class/severity CSS vars
- `platform/src/components/build/charts/` — NEW dir (CorpusChunksBar, EdgeRadial, CadenceArea, OnOffPlanDonut, SessionsBar, TrendLine)
- `platform/src/components/build/CorpusDensityHero.tsx` — NEW
- `platform/src/components/build/BuildVelocityStrip.tsx` — NEW
- `platform/src/components/build/InsightCards.tsx` — NEW
- `platform/src/components/build/PhaseGrid.tsx` — REWRITE (phase cards)
- `platform/src/components/build/PlanTree.tsx` — client component, multi-expand state
- `platform/src/components/build/AcCriteriaList.tsx` — NEW (collapsible AC rows)
- `platform/src/app/build/page.tsx` — cockpit composition
- `platform/src/app/build/plan/page.tsx` — phase-grid layout
- `platform/src/app/build/plan/[phase_id]/page.tsx` — detail redesign
- `platform/src/lib/build/insights.ts` — NEW

### Session 3 (Health/activity/intervention + backfill)
- `00_ARCHITECTURE/INTERVENTION_BACKFILL_v1_0.md` — NEW
- `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` — register backfill artifact
- `platform/scripts/governance/serialize_build_state.py` — read backfill
- `platform/src/components/build/HealthTrend.tsx` — replace sparklines with LineCharts
- `platform/src/app/build/activity/page.tsx` — filters + search
- `platform/src/app/build/interventions/page.tsx` — frequency chart + populated rows
- `platform/src/components/build/InterventionFrequency.tsx` — NEW

## §10 — Acceptance Criteria (28 ACs)

### Session 1 — Bug-fix + data track
- **AC.1** `phase_plan.sub_phases` has exactly 12 entries B.0..B.10+B.3.5 in correct order
- **AC.2** Every macro-phase in `macro_arc` has `milestones[]` with len ≥ 1 (M1=8, M2=12)
- **AC.3** `sessions_index` is sorted newest-first by date
- **AC.4** Per-phase shard `acceptance_criteria[]` items have `description`, `test`, `result_snippet` fields
- **AC.5** `serializer_warnings[]` key present in top-level build-state JSON
- **AC.6** `corpus_state` block populated with ≥ 6 of 9 fields (graceful on missing source files)
- **AC.7** `sub_phases[].session_count_estimated` populated from parsed session count in PHASE_B_PLAN
- **AC.8** `tsc --noEmit` passes in `platform/` after types.ts update

### Session 2 — Visual track
- **AC.9** `recharts` in `platform/package.json` and `platform/node_modules`; `npm run build` succeeds
- **AC.10** `colors.ts` exports status, class, severity palettes; all tokens used in at least one component
- **AC.11** `bt-mega` token defined in globals.css; corpus hero stats use it
- **AC.12** CorpusDensityHero renders: all 3 cards with big numbers populated
- **AC.13** BuildVelocityStrip renders: 3 sub-charts visible (cadence, on/off donut, intervention line)
- **AC.14** InsightCards renders ≥ 3 derived narrative items
- **AC.15** Cockpit recent-activity shows 7 sessions + "All activity →" pill link
- **AC.16** PlanTree: 'use client'; all M1–M10 expandable; M2 default expanded; URL ?expanded sync
- **AC.17** Plan view center = PhaseGrid: 12 cards, 3-col grid, click-through to phase detail works
- **AC.18** Phase detail AC rows: collapsed = ac_id + badge; expanded = description + test + result
- **AC.19** Phase detail "Sessions contributed" BarChart renders with data
- **AC.20** JourneyStrip has status-color dots matching status palette

### Session 3 — Polish + backfill track
- **AC.21** Health LineCharts replace sparklines; tooltips functional; date labels on x-axis
- **AC.22** Activity page has class + phase filter UI; search box present
- **AC.23** Intervention page: frequency chart renders; ≥ 1 row from INTERVENTION_BACKFILL populated
- **AC.24** `INTERVENTION_BACKFILL_v1_0.md` registered in `CANONICAL_ARTIFACTS_v1_0.md §1`
- **AC.25** Mirror adapted-parity update on Gemini side for CANONICAL_ARTIFACTS change (MP.5)
- **AC.26** `drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py` all exit ≤ 2
- **AC.27** Native end-to-end run confirms each named v0.1 complaint addressed
- **AC.28** SESSION_LOG Session 3 close entry appended; CURRENT_STATE rotated

## §11 — Constraints

- No retroactive PHASE_B_PLAN edits; PHASE_B_PLAN_v1_0.3 is frozen.
- No retroactive SESSION_LOG edits; backfill via annotation file only.
- `must_not_touch`: `01_FACTS_LAYER/**`, `04_DOMAIN_REPORTS/**`, `06_LEARNING_LAYER/**`, `035_DISCOVERY_LAYER/**`.
- Schema versioned to `0.3.0`; v0.2.0 schema retained at predecessor path.

## §12 — Verification (End-to-End)

1. `python3 platform/scripts/governance/serialize_build_state.py --repo-root . --session-id v0_2_test --validate-only 2>&1 | python3 -m json.tool | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['phase_plan']['sub_phases'])==12; assert all('milestones' in m for m in d['macro_phase']['macro_arc']); assert 'corpus_state' in d; print('PASS')"`.
2. `cd platform && npm run build` — zero errors.
3. Load `/build` as super_admin: corpus hero visible, 7-row activity, insight cards present.
4. `/build/plan`: all M1–M10 rows in tree have expand chevrons; click M1 → 8 milestones; phase grid = 12 cards.
5. `/build/plan/B.0`: AC rows collapse/expand; description text visible on expand.
6. `/build/health`: LineCharts with tooltips on hover.
7. `/build/interventions`: backfill rows visible.
8. Native sign-off → AC.27.

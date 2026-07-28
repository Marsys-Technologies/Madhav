---
artifact: SHAD_DARSHANA_STATE (Campaign Ledger)
canonical_id: SHAD_DARSHANA_STATE
version: rolling
status: LIVE — created by Night 1 session (W0.1), updated at every wave boundary and session close
created: 2026-07-29
schema: per SHAD_DARSHANA_BRIEF_v2_0.md §6
governing: SHAD_DARSHANA_NIGHT_RUN_v1_0.md (orchestration) + SHAD_DARSHANA_BRIEF_v2_0.md (execution contract)
  + KALA_SUPREME_ELEVATION_v1_0.md (v1.2, spec authority) + KALA_SIX_VIEWS_DESIGN_v2_0.md/v1_0.md
---

# ṢAḌ-DARŚANA STATE — the campaign ledger

## NEXT-ACTION

**Night 1, Phase 0 — CLOSED.** Phase 1a (spine) — **VERIFIED-MERGED**: PR #877
(`kala_envelope.ts` + `argument_composer.ts`, 42/42 new tests, `tsc --noEmit` clean)
independently confirmed merged to `main` @ `5208bc55` — files present, scope-clean (touched
exactly the 4 files claimed), the one failing status check (`Boot-time pointer validation
SC-17/18/19`) confirmed pre-existing on `main` before this PR, not introduced by it, and not a
required check (auto-merge proceeded without override). Items E3/E4/E5/43 partially advanced
(envelope contract exists; not yet consumed by any tool, so still NOT-STARTED at the
item-disposition level until a facade wires it — see brief §6, items close on serving, not on
library existence). **Phase 1b now dispatched, all 6 lanes IN-PROGRESS** in fresh worktrees off updated
`main`@`5208bc55` (each on branch `shad-darshana/<lane>`): now-ahead (kala_now_get,
kala_ahead_get) · elect-story (kala_elect_get, kala_story_get; ELECT is the Mode-3 landing
target) · priority-explain (kala_priority_get, kala_explain_get) · upaya-ritual-stub
(kala_upaya_get stub, kala_ritual_get Modes 1-2 stub + the Mode-3 `wrong_view` redirect,
implemented for real from day one per Elev §8) · parva-dedup (bug fix in existing STORY
substrate, span+level dedup — NOT the new facade) · ci-skeletons (specificity v0,
prose-survival, tri-plane no-dead-end, completeness census seed, authority-basis census seed,
Mode-3 single-route assertion — this one is explicitly allowed to report its Mode-3 test as
pending until upaya-ritual-stub merges). Next action: await all 6 completions, verify each
independently (PR status, scope discipline, real merge — do not trust self-reports), run the
merge train, then close Gate W0 (deploy #1) once all 8 tools are live + CI skeletons green +
sealed-harness regression shows no loss, both charts.

## Session log

| Session | Date | Phases worked | Outcome |
|---|---|---|---|
| Night 1 | 2026-07-29 | Phase 0 (boot) | IN-PROGRESS |

## Wave status

| Wave | Status | Evidence | Notes |
|---|---|---|---|
| W0 | NOT-STARTED | — | Foundation + elevated envelope. Blocking. |
| W1 | NOT-STARTED | — | Tier-A serving joins. |
| W2 | NOT-STARTED | — | The field as science. Opus design mandatory. |
| W2G | NOT-STARTED | — | GOCHARA-2.0 sub-day. **BLOCKED on N1–N5 ratification (W2G.0) — see below.** |
| W3 | NOT-STARTED | — | New computations over the field. |
| W3K | NOT-STARTED | — | KP sub-lord engine (item 18, built from zero). |
| W4 | NOT-STARTED | — | Intervention flagship (UPĀYA/YAJÑA). Opus design mandatory. |
| W5 | NOT-STARTED | — | Planner integration; native's hard gate (real MCP calls). |
| W6 | NOT-STARTED | — | Cutover + retirement. |

## N1–N5 ratification block (W2G precondition — blank N5 means W2G is not startable)

| Item | Ruling | Ruled by | Date | Rationale |
|---|---|---|---|---|
| N1 (wave naming) | — | — | — | Pending ANTARYĀMIN pre-queued adjudication. |
| N2 (multi-chart rollout order) | — | — | — | Pending. |
| N3 (pre-1984 backfill) | — | — | — | Pending. |
| N4 (cutover posture) | — | — | — | Pending. |
| N5 (lock granularity) | — | — | — | **FROZEN-contract question. Native ruling required; ANTARYĀMIN may only apply the pre-ruled CONSERVATIVE-DEFAULT (chart-level lock stays, no orchestrator change, reversible) if the native has not yet spoken. Not yet recorded.** |

## Registry item status (1–44 + E1–E8)

All items below seeded **NOT-STARTED** per W0.1. Disposition vocabulary: VERIFIED-FIXED /
VERIFIED-NO-DEFECT / PARKED-HONEST / FAILED-REOPENED. `OUT-OF-SCOPE-BY-DESIGN` is retired and
illegal.

| # | Item | Wave | Status | Both-charts | Evidence |
|---|---|---|---|---|---|
| 1 | Daśā-sandhi calendar | W3 (lite@W1) | NOT-STARTED | — | — |
| 2 | Recurrence-ladder serving | W1 | NOT-STARTED | — | — |
| 3 | Sky-event calendar | W3 | NOT-STARTED | — | — |
| 4 | Moorti-nirṇaya | W3 | NOT-STARTED | — | — |
| 5 | Vedha + Sarvatobhadra grid | W3 | NOT-STARTED | — | — |
| 6 | Activity-specific muhūrta tables | W3 | NOT-STARTED | — | — |
| 7 | Muhūrta-lagna | W3 | NOT-STARTED | — | — |
| 8 | Gochara dual-reference | W1 | NOT-STARTED | — | — |
| 9 | Health/adverse event class | W3 | NOT-STARTED | — | — |
| 10 | Per-chapter LEL pinning | W1 | NOT-STARTED | — | — |
| 11 | Provenance edges | W2 | NOT-STARTED | — | — |
| 12 | Daśā-system applicability | W2 | NOT-STARTED | — | — |
| 13 | Tithi-Praveśa | W3 | NOT-STARTED | — | — |
| 14 | Janma-anchored election rules | W3 | NOT-STARTED | — | — |
| 15 | Rarity axis | W2 | NOT-STARTED | — | — |
| 16 | Kota-Chakra | W3 | NOT-STARTED | — | — |
| 17 | Sudarśana-Chakra | W3 | NOT-STARTED | — | — (collision check vs `bo_sudarshana.py` required before naming) |
| 18 | KP sub-lord clock (CR-75) | W3K | NOT-STARTED | — | — |
| 19 | GOCHARA-2.0 sub-day | W2G | NOT-STARTED | — | — (blocked on N1–N5) |
| 20 | Auto-filed prospective ledger entries | W2 | NOT-STARTED | — | — |
| 21 | Per-tradition calibration weights | W2 (ongoing) | NOT-STARTED | — | — |
| 22 | Synthetic reference cohort + matched sub-cohort | W2 | NOT-STARTED | — | — |
| 23 | Circular-shift null calibration | W2 | NOT-STARTED | — | — |
| 24 | Uncertainty-budget propagation | W1-lite/W2-full | NOT-STARTED | — | — |
| 25 | Salience vector + submodular selection | W2 | NOT-STARTED | — | — |
| 26 | UPĀYA-SETU | W4 | NOT-STARTED | — | — |
| 27 | kala_timeline_spec v1 | W2 | NOT-STARTED | — | — |
| 28 | Daśā-lord transit-condition | W1 | NOT-STARTED | — | — |
| 29 | Chandrāṣṭama/horā/janma-resonance flags | W1 | NOT-STARTED | — | — |
| 30 | Mudda daśā join | W1 | NOT-STARTED | — | — |
| 31 | Period-echo mining | W3 | NOT-STARTED | — | — |
| 32 | Diśā-śūla + gulika-kālam joins | W1 | NOT-STARTED | — | — |
| 33 | Absence-of-expected detector | W3 | NOT-STARTED | — | — |
| 34 | Contrastive EXPLAIN | W3 | NOT-STARTED | — | — |
| 35 | Planner wiring verified LIVE (hard gate) | W5 | NOT-STARTED | — | — |
| 36 | Contender lattice + adjudication engine | W3 | NOT-STARTED | — | — |
| 37 | Ritual-resonance + paddhati profile | W3/W4 | NOT-STARTED | — | — |
| 38 | ELECT ritual-pairing + grading unification | W1 facade/W3/W4 | NOT-STARTED | — | — |
| 39 | Living-LEL incremental calibration plane | W2 | NOT-STARTED | — | — |
| 40 | kala_ritual_get registration + planner wiring | W0 stub/W4/W5 | NOT-STARTED | — | — |
| 41 | Muhūrta Factor Census + corpus extraction | W3 | NOT-STARTED | — | — |
| 42 | Unified Intervention Ledger | W4 | NOT-STARTED | — | — |
| 43 | Tri-plane traversability contract | W0–W1 | NOT-STARTED | — | — |
| 44 | Single-temporal-authority (`authority_basis`) | W0 seed/W2/W6 gate | NOT-STARTED | — | — |
| E1 | Point-process formalization + skill score | W2 | NOT-STARTED | — | — |
| E2 | Insight synthesis stage | W2 | NOT-STARTED | — | — |
| E3 | Argument-shaped reading + specificity gate | W0/W2 | NOT-STARTED | — | — |
| E4 | question_frame compiler | W0 | NOT-STARTED | — | — |
| E5 | field_snapshot_id | W0/W2 | NOT-STARTED | — | — |
| E6 | Per-view elevations | W1–W3 | NOT-STARTED | — | — |
| E7 | Substrate (census CI, freshness, cohort, composer lib, skill-score CI) | W0/W2 | NOT-STARTED | — | — |
| E8 | Non-elevations register | standing | NOT-STARTED | — | — |

## Preflight (Phase 0)

- Repo clean: **NO** — pre-existing uncommitted state on the checked-out session branch
  (`satyadipa/orchestrator-lit-predicate`, unrelated SATYA-DĪPA work) and numerous untracked
  docs from other in-flight campaigns (PARIPRASHNA, narration_audit, PARISHODHANA). None of
  this is campaign scope; not touched. Campaign work branches from `main` (fast-forwarded to
  `origin/main` @ `8e1af4ca` this session), isolated in its own worktrees.
- Both canonical charts healthy (LC-5 sweep staleness on `1c826d5a`): **NOT CLEARED — ticketed
  per brief's own "CLEARED or ticketed" allowance, does not block W0/W1.** Live query against
  `kala_gochara_windows`: canonical chart `482012f1` has 8,345 rows to horizon 2084-12-30
  (58y forward); `1c826d5a` has only 1,267 rows to horizon 2027-07-03 (~1y forward) despite
  being computed *more recently* (2026-07-26 vs 2026-07-24/25) — a real coverage-horizon gap,
  not a timestamp-staleness one. **TICKET: `1c826d5a` needs a full gochara-sweep rebuild
  extending its horizon to parity with the canonical chart before any both-charts gate that
  depends on forward-window coverage can honestly close** (W1 items touching AHEAD-window
  serving are the first to hit this — Conductor to watch for it at Gate W1, not before).
- Canary pipeline state: real automated canary blocked — `MCP_CANARY_KEY` IAM binding not yet
  applied by the native (confirmed via `PARISHODHANA_REPORT_v1_0.md` + handoff doc, both
  independently). **Not a campaign blocker** — brief's own fallback applies: manual canary
  discipline (deploy.yml fails safely closed without the binding). Deploys proceed under this
  discipline until the native applies the grant.
- Migration range reserved: **472–495, in `platform/supabase/migrations/`** (see below for why
  that directory, not `platform/migrations/`).
- Duplicate-copy + tool-name census:
  - **Item 17 vs `bo_sudarshana.py` — CONFIRMED namesake collision, NOT a functional
    duplicate.** `bo_sudarshana.py` is an L2 Bodha static house-triad MSR signal writer
    (9 grahas × 5 ayanamshas, `bodha_msr_signals`). Item 17 (Sudarśana-Chakra year-wheel) is
    an L3 temporal progression technique — different layer, different computation, same
    classical term. **Conductor naming ruling (W0, no adjudication needed — plain engineering
    call): item 17's writer is named `ka_sudarshana_varsha`, never bare `sudarshana`, to keep
    the two permanently distinguishable in registries/logs.**
  - **`kala_activations` — confirmed live, but as a JSON field key, not a table or tool.**
    Written/read in `register_d9_judgment.ts` (`timing_hooks.kala_activations`) and
    reconciled in `registry_bridge.ts`. No table/tool collision exists, but **no new campaign
    envelope field or table may reuse this exact string for a different shape** — live serving
    code pattern-matches on it.
- Nirmāṇa catalog-reconciliation baseline: **CLEAN before this campaign adds anything.**
  `catalog_reconciliation.test.ts` 6/6 PASS; `test_has_writer_completeness.py` 3/3 offline PASS
  (1 live test needs `DATABASE_URL`, skipped locally); direct DB check confirms only 5
  pre-existing `has_writer=false` assets, none campaign-relevant. Brief §2.5.1 requires both
  checks stay green in the same PR as every new writer going forward — not a one-time gate.
- **Live collision note (out of campaign scope, flagged for awareness only):** the
  currently-checked-out session branch (`satyadipa/orchestrator-lit-predicate`, unrelated
  SATYA-DĪPA work) carries an unmerged `platform/migrations/466_asset_throughput_incomplete_state.sql`
  that collides on number 466 with main's `466_omega8_floor_wiring.sql`. This campaign's
  worktrees branch from `main`, not from that branch, so it's unaffected — noted here only so
  a future session doesn't mistake it for a campaign-caused collision.
- No existing SHAD_DARSHANA work found in git history (`origin/main` has no `shad-darshana*`
  branches, no PRs matching the campaign) — confirmed first night.

## Migration range reserved

**472–495, in `platform/supabase/migrations/`** (reserved 2026-07-29, Night 1). Two migration
directories both apply to prod and are deduped by filename (`migrate.ts`); the standing policy
doc (`MIGRATION_DIRECTORY_POLICY_v1_0.md`, 2026-05-22) claims `platform/migrations/` is
canonical and supabase is frozen, but the actually-current convention — per
`platform/supabase/migrations/README.md` and observed practice, both directories growing in
lockstep — is that new migrations land in `platform/supabase/migrations/`. Combined live max
on `main`@`8e1af4ca` = 471 (`471_retire_mcp_predictions.sql`). **Re-check the live max
immediately before writing the FIRST actual migration this campaign lands** — this range could
go stale if another campaign lands migrations first; 472 is a reservation, not a guarantee.

## Deployed revisions

None yet this campaign.

## Open PRs

None yet.

## Skill-score scoreboard

Not yet published (first publish at W2 close becomes the CI baseline).

## Specificity-gate status

Not yet seeded (W0.6 skeleton pending).

## Authority-basis census scoreboard (item 44)

Paths enumerated: — / carrying `authority_basis`: — / computing own windows: — (target: 0).

## Dark-corpus bright% per chart

Not yet re-measured this campaign (baseline = PARIŚODHANA measurement, referenced at W6).

## Live-MCP verification table (W5)

Not started.

## W4 Mode-2 fixture disposition

Not started.

## ADJUDICATION log (ANTARYĀMIN)

None yet.

## Morning report

(Appended at ~7.5h cap or campaign close, whichever first, per NIGHT_RUN §B.5.)

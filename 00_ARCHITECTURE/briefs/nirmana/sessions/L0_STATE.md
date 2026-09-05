---
artifact: L0_STATE.md
canonical_id: NIRMANA_V21_L0_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L0
layer: L0 — Brahmagyan
owner: the L0 session (this file is yours alone — charter C5)
last_updated: 2026-09-05 — resumed; 29/40 frozen; 11 remaining; W4 EXECUTE + Conform corrections in flight
---

# L0 — Brahmagyan — SESSION STATE

Charter C9: this file is your memory — update every loop, commit with every PR and at milestones,
so re-pasting the prompt into a fresh session is safe at any moment.

**Read order on ANY start:** `SESSION_CHARTER_V21.md` → `resume/RESUME_L0.md` → this file →
`git fetch origin main` → `gh issue view 1713` + your `nirmana-adjudication` issues → continue.

- **Coordination issue:** #1713 · **Migration range:** 645–649 is Conductor; **L0 uses the existing
  6xx L0 numbers already applied** (640–644) — new L0 registry corrections take the next free number,
  confirmed against `platform/migrations/` before writing.
- **Branch namespace:** `feat/nirmana-l0-*` / `fix/nirmana-*` · **PR prefix:** `L0:` (older ones used no prefix)
- **Worktree:** main checkout `/Users/Dev/Vibe-Coding/Apps/Madhav` + scratch `/private/tmp/madhav-nirmana-l0-w4`
- **Evidence tooling (scratch, Conductor-audited):** `/private/tmp/.../scratchpad/nirmana_batch_runner.py`
  (stage analysis+verdict), `nirmana_build_wave.py` (dispatch/authorize/force-execute/evidence),
  `producer_covered.py`, `freeze_probes.py`, `run_dispatcher.py`. Canonical helper is now `nrec` (#1731).

## Position

**L0-W4 EXECUTE + Conform-stage integrity corrections.** W1/W2/W3 done for the 29 frozen. **29/40
frozen** (verifier-signed 5-event chains, implementer≠verifier). **11 remaining**, all diagnosed.

## The 11 unfrozen assets

| asset | route | status / blocker |
|---|---|---|
| bg_cohort | rebuild_only | DEP-ASSERT on service dep `bg_ephemeris_engine` — fixed in #1772 (merged) but **job image `d93d9d0a` predates it**; dispatch held on job-image deploy |
| bg_gochara_arcs | rebuild_only | count pin stale (33,933 vs 34,553; Rahu/Ketu −310 each; **tiles perfectly**). Verdict: correct check → tiling invariant + derived/floored volume (C12) |
| bg_yogas | rebuild_only | 4 yogas missing from ontology+reference (fix writer, MUST); `brahma_yoga_source_chunks` 0 vs pin 85 (check pin git-provenance — never-green=proposal). CASCADE parent → snapshot+`--acknowledge-destroys` |
| bg_dasha_systems | rebuild_only | `kp` missing from `reference_dasha_systems` (19 vs 20) — real referential gap |
| bg_doshas | rebuild_only | 658 FULL-JOIN violations — catalog/ontology/reference canonical_ids misaligned |
| bg_vidhi_floors | rebuild_only | `catalog_status=DRAFT` (bundle DRAFT→CURRENT with re-acceptance, D-CND-09); 11/286 vs 14/409, 7 intents don't tile |
| bg_parihara_rules | **UNROUTED** | only asset with no W2 events — W1/W2 now (never gated); note migration-644 integrity_check_sql drift vs frozen manifest |
| bg_compendium_index | rebuild_only | wave 2; depends_on normalized; needs wave-1 frozen (E-gate) + own integrity check |
| bg_rules | rebuild_only | wave 2; depends_on normalized |
| bg_text_index | rebuild_only | wave 2; depends_on normalized |
| bg_concordance | rebuild_only | wave 3; depends_on normalized; deepest DAG node |

## Decisions log

- **D-L0-A** — 29 assets frozen through W4 via the proven pattern: `nirmana_batch_runner` stages
  analysis+verdict (fingerprint pre-checked vs frozen manifest); `nirmana_build_wave dispatch`
  create→build_run_authorized(planned window)→**force-execute**→poll; `evidence` phase does
  accepted_rebuild_observed(executor)→integrity_verified(verifier)→asset_frozen(verifier). Proven
  end-to-end; idempotent/existence-aware after two transient blips.
- **D-L0-B** — Discovered + fixed three build-path mechanics live: (1) `build_run_authorized` must be
  recorded in the run's *planned* window before dispatch; (2) `NIRMANA_FORCE_EXECUTE=1` is required or
  an authorized re-run no-op-completes and emits no receipt; (3) evidence phase must be existence-aware
  to survive network blips.
- **D-L0-C** — Two integrity-detector correctness fixes shipped (P0, merged pre-resume): probe-service
  assets re-run the live health probe as their detector; the SQL detector guard now ignores string
  literals/comments and allows read-only CTEs while **adding** an explicit DML rejection the old guard
  lacked (hardening, not weakening — C12 floor test satisfied).
- **D-L0-D** — `depends_on` stored unsorted for 5 multi-dep assets while the frozen definition/canonical
  fingerprint sort it; normalized live to sorted (fingerprint-neutral, verified, committed) and patched
  the dispatcher (Conductor raised as **#1728** with a regression test). Unblocked multi-dep dispatch;
  also unblocked 15 of L3's assets.
- **D-L0-E** — #1772 (depends_on sort + §3.5 service-dependency satisfaction) merged. Service deps are
  satisfied by `service_ok`/GREEN probe, exempt from data-freshness (C12 §3.5). Regenerated `probe_digest`
  for the Governance Gate.
- **D-L0-F** — C12 verdicts on the 5 integrity failures: only `bg_gochara_arcs` is a stale pin (correct
  the check). The other 4 (`bg_dasha_systems`, `bg_doshas`, `bg_vidhi_floors`, `bg_yogas`) are **real
  data defects** the invariants correctly caught → fix the writer (MUST) or adjudication with derivation.
  Do NOT weaken any check to pass.

## Held items

- **bg_cohort dispatch** — held until the pipeline **job image** carries #1772 (`ee8cf7d09`); current
  image `d93d9d0a` predates it. Poll deploy each loop.
- **Wave-2/3 dispatch** (compendium_index, rules, text_index, concordance) — E-gate needs wave-1 frozen.
- **Destructive rebuilds** (bg_yogas CASCADE parent, any asset with populated descendants) — per C13/WP-6:
  cascade_check + fresh verified snapshot + `--acknowledge-destroys`. Not a blanket hold post-#1781.

## CAPABILITIES LANDED

| capability | consumers | lands with | status |
|---|---|---|---|
| Layer-generic integrity-detector fixes (probe-as-detector; literal/comment/CTE-safe read-only guard) | all layers' Conform | P0 (merged) | **AVAILABLE** on main |
| Dispatcher `depends_on` sort + service-dependency satisfaction | L1–L5 build path | #1772 / #1728 (merged) | **AVAILABLE** on main |

## Cost ledger

| item | wall-clock | notes |
|---|---|---|
| W4 EXECUTE — 29 assets frozen (waves 0 + probes + producer-covered + wave-1 clean 4) | ~ several hrs | incl. deep mechanics discovery (authorize-ordering, force-execute, idempotent evidence) |
| P0 integrity-detector fixes + #1772 tooling | ~1.5 hr | 2 PRs, tests, digest regen |
| depends_on normalization + dispatcher fix (#1728) | ~40 min | fingerprint-neutral data + code |
| C12 wave-1 defect investigation (6 assets) | ~50 min | detector-first, per-asset attribution |

## Heartbeat

- 2026-09-05 — **RESUMED as L0; 29/40 frozen.** Posted STOCK-TAKE on #1713; created this state file.
  WP-6/#1781 merged (destructive dispatch now `--acknowledge-destroys`); #1772/#1728 merged; job image
  still predates #1772 (bg_cohort dispatch held on deploy). Next: bg_parihara_rules W1/W2, bg_yogas
  writer fix + source-chunks pin provenance, bg_gochara_arcs pin→tiling correction, D-CND-09 bundled
  registry migration. Blocked on: pipeline job-image deploy of #1772.

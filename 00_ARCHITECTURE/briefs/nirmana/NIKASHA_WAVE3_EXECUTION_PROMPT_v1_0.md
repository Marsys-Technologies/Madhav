---
artifact: NIKASHA_WAVE3_EXECUTION_PROMPT
canonical_id: NIKASHA_WAVE3_EXECUTION_PROMPT
version: "1.0"
status: ACTIVE — wave 3 launched 2026-09-28 under native authorization ("Yes, please go ahead")
produced_on: 2026-09-28
campaign_id: nikasha-wave3
runs_in: /Users/Dev/madhav-nikasha (branch campaign/nikasha-test; PR #2736)
authority: >
  NIKASHA_IMPLEMENTATION_PLAN_v1_0.md P6 (full) + P4 leftovers (R60, R99) + P5 non-sealed subset + P9's R218 ·
  NIKASHA_CHANGE_REGISTER_v2_0.md v2.6 · D4 ruling (ledger identity/closure semantics) · D5 rev. 2.1 (R218) ·
  CLAUDE.md §N.3, §N.7, §N.8.
model_routing: builder = Sonnet (Opus if two consecutive stalls, per wave-2 precedent) · reviewer gate = Opus
scope_boundary: >
  This wave deliberately EXCLUDES every sealed-tier (tier 1/2/3) edit. P5's sealed rows (R01, R72, R76, R73,
  R75, R65-T3, R67, R68-T3, R74) and P9's R221 (T3 §0.1 re-scope) are D2-reopen work: closed agenda per
  document, a cross-tier re-render pass before each re-seal, one version bump, seal order T1 → T2 → T3. That
  is its own campaign, not a wave-3 row, and is NOT launched here.

# Nikaṣa wave 3 — ledger crosswalk, inspector leftovers, the planner test

## §1 — Purpose

Everything here is self-contained governance-tooling work already ruled and inside what this campaign may
touch: no sealed tier, no writer, no orchestrator, no Lane B file. One packet, sequential rows, one commit
each, one gate review at the end.

## §2 — Hard constraints (same as wave 2, restated)

1. **Database:** never `source /Users/Dev/madhav-l3/dbenv.sh`, never `gcloud` (hangs). Use the pre-resolved
   read-only env at the session scratchpad `pgenv.sh`; `timeout 300` on DB/long commands; `timeout 900` on a
   full six-layer census.
2. **Never touch:** writers, orchestrator, sealed tiers (tier 1/2/3 — see scope_boundary above), editorial.ts/
   compiler.ts, register/plan/decisions/STATE (the executor folds), Lane B's files. **Ledgers:** the real
   `00_ARCHITECTURE/control/asset_gaps.jsonl` now holds real production data (830+ lines) — copy to scratch for
   every proof, never edit the original directly except through the one migration this wave authors (R81),
   which must itself be idempotent and re-runnable, never hand-edited twice.
3. **Commit discipline:** one row per commit, `git commit -m "..." -- <paths>` (only-mode); never `git add -A`;
   never `--amend`; never push. Trailer: "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>".
4. **Every row:** a behavioural test that FAILS without the change, plus a recorded mutation run.
5. **§N.8 always:** no change may create a PASS/N/A/CLOSED without a genuine measurement.
6. **Scratch files** only under the scratchpad subdirectory `w3/`.
7. **Stop conditions:** a writer/orchestrator/sealed-tier change, a production write outside the one
   authored migration, or an ORM/schema migration beyond the ledger's own JSONL — stop, report, return.

## §3 — The rows

**P6 · Ledger identity and crosswalk (D4-ruled) — R78, R79, R80, R81, R15, R29:**
- **R78** — a declarative criterion registry the census reads: gate, check, applicability, detector binding
  or `NONE`, revision. Ids derived `<asset>-<Gate>.<check>` (scope suffix where chart-scoped).
- **R79** — re-scoped per D4: deterministic lookup on `(asset, scope, registered criterion)`. The four
  family aliases (`Vocab.rule1.alias`≡`Vocab.alias`, `Dens.density_contract`≡`Dens.served`,
  `Carr.D1|D2|D3`≡`Carr.detector`, `Completeness.*`≡`Complete.*`) are one-time crosswalk entries consumed by
  R81, never a runtime alias table.
- **R80** — `asset_gaps.jsonl` `_schema` gains `superseded_by`, so folding a duplicate sets it on the thinner
  row while the ledger stays append-only.
- **R81** — the 11 measured hand↔census overlap pairs (`T5_LEDGER_DRIFT.md` §A: bg_ontology G02/G07/G10/G05,
  bg_ephemeris G03/G05/G02, bg_panchanga G01(partial)/G02, bg_rules G03/G06): fold each census row's
  `measured:` reading into the hand row's `what`, set `superseded_by` on the census row. This is the one
  place this wave writes the real ledger — write the reviewed migration script, prove it on a COPY first
  (idempotent: running it twice makes no further change), then apply it to the real file as its own commit,
  and record the before/after line count and md5 in the report.
- **R15** — the hand/machine rule: everything measurable belongs to the inspector; a hand-written row
  (opportunity, disposition, judgement) carries the census run id it was judged against.
- **R29** — hand-written rows carry `census_run_id` (mechanical consequence of R15).
- **Proof:** a ledger scan finds zero `(asset, scope, criterion)` identities with more than one live row;
  every historical hand id resolves through `superseded_by` to exactly one live row, or is itself live;
  `Earn.service_state` exists in the registry and is never closed by a timing measurement; `emit_gaps` run
  twice against an unchanged target appends nothing; the ledger stays append-only (no line deleted, ever).

**P4 leftovers — R60, R99:**
- **R60** — `Ldgr.source_presence`'s citation-column list misses the singular `classical_citation`;
  bg_nakshatra_medical gets no check despite a populated citation column. Add it to the list.
- **R99** — the empty-table-with-agreeing-build-record case (`ga_prashna`: 51 runs, 0 rows, 0 modules) needs
  its own honest verdict, not silently falling through to another check's branch — read R52's prior fix
  (production ledger, W2-1) to avoid re-opening that exact defect class; this is the *third*, previously
  uncovered case D4/D6's discipline already applies to.

**P5, non-sealed subset only — R63, R64, R66, R69, R70, R77, R65 (tracker half only), R68 (T4 half only):**
- **R63/R64** — T4 §4 / §4.2: "the eight gates" / "the six checks" → "the nine gates" / "the nine checks".
- **R66** — `asset_elevation_tracker.py:43` comment "Eight, not thirty-three" → "Nine, not thirty-three".
- **R65 (tracker half only — NOT the T3 half, which is D2 reopen work)** — the tracker's own `GATES` comment,
  align on nine.
- **R68 (T4 half only — NOT the T3 half)** — T4 :278's bare `NA` → the closed-set `N/A`.
- **R69** — L0 v3.0's "0/320 gates" (4 places) → 0/360.
- **R70** — L0 v3.0's stale §1.1/§9 figures → restate from the current ledger/census, or date-stamp.
- **R77** — all five L0 pilot briefs: add the missing Build row (`## §4 · The eight gates` → nine rows),
  recompute N/A counts.

**P9 — R218 only (NOT R221, which is T3 §0.1 and belongs to the D2 reopen):**
- **R218** — the planner P-need test: run each of P01–P24 through `plan_retrieval`; PASS when the plan
  resolves to capabilities whose catalog units carry a named producer (R85, already landed). This is new
  tooling (a test harness), not a sealed-tier edit. Read `platform/src/lib/retrieval/adapters/agentic_loop/`
  and `nikasha_test/provenance/producer_provenance.derived.json` (Lane B's committed artefact, READ ONLY —
  never touch `catalog_provenance.py` or its outputs). Report per-P-need pass/fail with the resolved
  capabilities and their producer status.

## §4 — Packet proof

1. Full six-layer read-only census at HEAD vs the wave-2 close (`31b3e1024`); confirm 0 unintended verdict
   changes (R60/R99 may open new, previously-silent findings — name them; nothing else should move).
2. The ledger crosswalk proof (R78–R81, R15, R29) exactly as specified above, including the real R81
   migration's before/after state.
3. `emit_gaps` dry run on a fresh copy of the real ledger: confirm idempotency and that the new criterion
   registry doesn't silently reclassify any existing OPEN row without a genuine re-measurement.
4. The R218 planner-test report: per P-need, pass/fail and why.
5. Full governance test suite (pre-existing failures proven pre-existing); `manifest_fingerprint.py --check`
   (MATCH); `drift_detector.py` (exit 0/3); production ledger md5 confirmed unchanged EXCEPT for the one
   R81 migration commit, which must be named and isolated.

## §5 — Gate

One `nikasha_test/wave3/W3-1_REPORT.md`; one fresh Opus reviewer, same checklist discipline as wave 2
(proof-that-could-fail, mutation re-runs, scope/regression, ledger safety — especially around R81's real
write). Corrections go back to the same builder. The executor folds register/plan/STATE only after ACCEPT
or ACCEPT_WITH_CORRECTIONS, fingerprints rotated last.

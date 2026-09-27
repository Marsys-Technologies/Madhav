---
artifact: NIKASHA_WAVE2_EXECUTION_PROMPT
canonical_id: NIKASHA_WAVE2_EXECUTION_PROMPT
version: "1.0"
status: ACTIVE — wave 2 launched 2026-09-27 under native authorization ("let's proceed with the next one")
produced_on: 2026-09-27
campaign_id: nikasha-wave2
runs_in: /Users/Dev/madhav-nikasha (branch campaign/nikasha-test; PR #2736)
authority: >
  NIKASHA_IMPLEMENTATION_PLAN_v1_0.md P4 (remainder) · NIKASHA_CHANGE_REGISTER_v2_0.md v2.2 (rows below) ·
  nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md (D4 closure semantics, D6 rate grading) · wave1/A_REVIEW2.md
  (G1–G5 carry-forwards) · CLAUDE.md §N.3, §N.7, §N.8.
model_routing: builder = Opus · reviewer gate = Opus, fresh context, read-only, never the implementer
---

# Nikaṣa wave 2 — the inspector's second lane, three gated packets

## §1 — Purpose

Wave 1 made the inspector able to close a row. Wave 2 makes every verdict it closes on *earned*: no path where
an error, timeout, missing input or unmeasured check produces a closable verdict (PASS or N/A), no silently
absent verdict, and no verdict read from a stale row. The target is the precondition registered as R222:
**the inspector may write to the production ledger** (`--emit-gaps` against `00_ARCHITECTURE/control/`).

## §2 — Hard constraints

1. One lane, one file owner: all work is in `platform/scripts/governance/asset_census.py`,
   `00_ARCHITECTURE/control/asset_elevation_tracker.py`, their tests under `platform/scripts/governance/__tests__/`,
   and `nikasha_test/wave2/**`. Packets run strictly in sequence; packet N+1 starts only after packet N's gate.
2. **Database:** never `source /Users/Dev/madhav-l3/dbenv.sh`, never `gcloud` (hangs). Use the pre-resolved
   read-only env at the session scratchpad `pgenv.sh`; `timeout 300` on every DB/long command. Read-only always.
3. **Never touch:** writers, orchestrator, sealed tiers, `editorial.ts`/`compiler.ts`, register/plan/decisions/STATE
   (the executor folds), Lane B's files (`catalog_provenance.py`, its tests, `nikasha_test/provenance/**`).
   **Ledgers:** never write to `00_ARCHITECTURE/control/asset_gaps.jsonl` / `asset_certs.jsonl`; every emit proof
   runs on a COPY via `NIKASHA_CONTROL_DIR` / `--out`.
4. **Commit discipline (R230):** one commit per row, always `git commit -- <paths>` (only-mode) so nothing staged
   elsewhere rides along; never `git add -A`; never push. Each row lands with a test that FAILS without the change,
   and a recorded mutation run (apply → named test fails → revert → green).
5. **§N.8:** every verdict must be able to read false; every closable verdict must name what was measured.
   The canonical chart for chart-scoped `count_sql` is `482012f1-710e-4a25-994a-93821f5871aa`
   (`362f9f17-…` is a dead phantom — never use it).
6. **Stop conditions:** a writer/orchestrator/sealed-tier change, a production write, or a migration → stop the
   packet, report, return.

## §3 — Packets

**W2-1 · No unearned closure; no silent absence (freeze blockers).** R222 (NULL count_sql → N/A; unrecognised
writer → N/A on contract/idempotency; missing capability dir → N/A on Dens.served; empty table → PASS on depth —
each becomes NO_DETECTOR/ERRORED with its reason), R225 (behavioural test of the `measure()` call site with the
instrument present; safe default for `attempt_linkage_wired`), R42 (`Build.completion` must not compare
`count_sql` against itself on multi-table assets), R52 (emptying a table must never flip a check to PASS —
separate non-emptiness from rows_written↔live consistency), R56 (parameterised / multi-table `count_sql` must emit
a verdict, never be silently absent), R231 (bind the canonical chart to chart-scoped `$1` `count_sql` so L1–L5
`Build.completion` is measured), R48 (`Count.floor` emitted on every asset that declares `target_floor`), R223
(real psql timeout caught per check → ERRORED), R224 (active population scoped by `asset_registry.layer`, not id
prefix; `lel_events` measured). **Packet proof:** an enumeration of every branch that can yield PASS or N/A, each
labelled genuine-measurement or fixed; a full census run on all six layers (read-only) with the per-asset verdict
diff against the wave-1 head explained row by row; the T1 planted suite re-run — the TRUNCATE plant
(`build_completion_truncate`) must now FAIL; a `--emit-gaps` dry run on a ledger COPY showing no closure without a
genuine PASS / justified N/A.

**W2-2 · Latest row, right registration, attempt-linked timing.** R44 (latest `asset_throughput` row per asset),
R49 (latest `build_run_assets` error), R45 (stale dependencies surface as PARTIAL), D6 item 2 (attempt-linked
timing via the latest `build_run_assets` attempt; the engine writes no `probe_green` disposition — derive it;
completed builds are `disposition='build'`), R43 (constant-indirection `@register(ASSET_ID)` and package writers),
R46 (view assets counted by the view), R50 (exercised count off by one), R51 (serving-module attribution),
R53 (`Build.target` dead FAIL branch — make the loss expressible or remove the branch honestly), R54
(`Vocab.alias` severity visible below verdict level). **Packet proof:** per row, a planted or live case that the
old code gets wrong and the new code gets right.

**W2-3 · Deeper detectors.** R20 (follow writer delegation into the seeder so `Idem.pattern` resolves PASS/FAIL
for the 27 PARTIAL assets), R21 (blocking radius per asset from `asset_registry.depends_on`, attached to every
Build gap as severity), R23 (field-level reachability over capability modules). **Packet proof:** before/after
counts per row, with the population stated.

Out of scope: R22 (needs R06's universe declarations), R55 closure (needs migration 1094 deployed).

## §4 — Gate

Each packet returns `nikasha_test/wave2/W2-<n>_REPORT.md` (diff by file with reasons, proof commands with actual
output, mutation runs, honest limits, out-of-scope findings as a list). The executor dispatches a fresh Opus
reviewer (the packet-reviewer checklist) whose verdict is ACCEPT / ACCEPT_WITH_CORRECTIONS / REJECT; corrections go
back to the builder; the next packet starts only after acceptance. The executor folds register, plan and STATE
after each accepted packet, fingerprints rotated last.

---
artifact: NIKASHA_WAVE1_EXECUTION_PROMPT
canonical_id: NIKASHA_WAVE1_EXECUTION_PROMPT
version: "1.0"
status: ACTIVE — wave 1 of the Nikaṣa implementation plan, launched 2026-09-27 under native authorization ("please go ahead")
produced_on: 2026-09-27
campaign_id: nikasha-wave1
runs_in: /Users/Dev/madhav-nikasha (branch campaign/nikasha-test; PR #2736)
authority: >
  NIKASHA_IMPLEMENTATION_PLAN_v1_0.md (packets P3, P4, P9-R85) · NIKASHA_CHANGE_REGISTER_v2_0.md v2.1 ·
  nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md v2.1 (rulings D1–D6; D4 fixes the ledger identity and closure
  semantics; D5 rev. 2.1 fixes what necessity means; D6 fixes how a NULL rate is graded) · CLAUDE.md §N.3, §N.7, §N.8.
model_routing: builders = Sonnet · reviewer gate = Opus (the engine campaign's routing; not overkill)
---

# Nikaṣa wave 1 — two lanes, one gate

## §1 — What this wave is for

The Nikaṣa system (four tiers + inspector + two ledgers + tracker) was tested and found NOT_READY_TO_FREEZE.
Wave 1 lands the three things every later packet depends on:

- **Lane A · the inspector can close a row** — P3 (closure loop into production tools) on top of R216
  (rebase on engine B1's census diff) plus the P4 items that must precede any detector re-run (R41 fault
  isolation, R40 timeout, R220 population, D6 rate grading).
- **Lane B · the catalog names its producers** — R85 as ruled by D5 rev. 2.1: derive, for every semantic
  capability unit, which asset(s) produce or part-produce it; compute the necessity closure; report the
  units nothing resolves as NO_DETECTOR, never guessed.

Success is measured, not claimed: Lane A's proof is a row flipping OPEN→CLOSED→RE-OPENED→CLOSED under the
**production** tools; Lane B's proof is a provenance file whose every producer traces to a source range and a
`target_table`, with the closure figure re-run from it (baseline 63 of 127 active assets, 2026-09-27).

## §2 — Hard constraints (both lanes)

1. **Read-only production.** `source /Users/Dev/madhav-l3/dbenv.sh; export PGPORT=5433`; verify
   `SHOW default_transaction_read_only` = on before the first query. No migration is applied by this wave.
2. **Never touch:** the sealed tiers (`MADHAV_PRODUCT_DEFINITION_FINAL.md`, `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md`,
   `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`); any writer (`*_writers/`, `ga_*/bo_*/ka_*/ph_*/mi_*/bg_*` code);
   the orchestrator (`pipeline/orchestrator/`); `editorial.ts` (the reviewed provenance tier is hand-curated, not
   machine-written); the register, plan, decisions and STATE files (the executor folds those after the gate).
3. **Ledgers are append-only.** `asset_gaps.jsonl` / `asset_certs.jsonl`: never delete or rewrite a line.
4. **Same-file rule.** Lane A owns `platform/scripts/governance/asset_census.py`, `00_ARCHITECTURE/control/
   asset_elevation_tracker.py`, `00_ARCHITECTURE/control/*.jsonl`, `nikasha_test/harness/**`. Lane B owns
   `platform/scripts/governance/catalog_provenance.py` (new) and `nikasha_test/provenance/**` (new). Neither
   touches the other's files.
5. **Every status can read false** (§N.8). A verdict, a CLOSED transition, a derived producer — each needs
   the case that makes it fail, with a test that fails without the change.
6. **Honest tiers.** A machine-derived producer is `disposition: derived_from_source_query`, never
   `reviewed_output`. A unit nothing resolves is `NO_DETECTOR — <exact reason>`. An `N/A` states why.
7. **Commit discipline.** Commit on `campaign/nikasha-test` with explicit paths (never `git add -A`); do not
   push. If a file registered in `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` changes, rotate its fingerprint
   AFTER the last edit, then `manifest_fingerprint.py --write` / `--check` (MATCH) and `drift_detector.py`
   (exit 0 or 3 only). Commit message ends with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
8. **Stop conditions** — stop the lane, write the reason into the report, return: the work would need a
   writer, orchestrator or sealed-tier change; a production write; or a migration applied.

## §3 — Lane A · the inspector closes a row (builder: Sonnet)

Sequential. Each step lands with its proof before the next starts.

- **A-1 · R216 rebase.** `git -C /Users/Dev/madhav-engine show 17e5a1257 -- platform/scripts/governance/asset_census.py`
  applies cleanly here (verified 2026-09-27, 175 diff lines). Apply it; run B1's census tests green; commit.
- **A-2 · P3 closure loop.** Port from `nikasha_test/harness/asset_census_closing.py` and `harness/tracker_sandbox.py`:
  (a) `emit_gaps` appends `CLOSED` when a previously-OPEN deterministic-id row's check now passes and `RE-OPENED`
  when a closed check fails again; (b) tracker resolves last-wins per `gap_id`; (c) `NIKASHA_CONTROL_DIR` +
  `--out`; (d) hand-row detector bindings (`<control>/detectors/<asset>_<check>.py`). **D4 acceptance cases, each
  a test that fails today:** CLOSED only on `PASS` or a justified `N/A` (never `NOT_GENERIC`, `UNKNOWN`, errored,
  unmeasured); `IN_PROGRESS`→CLOSED on PASS; regression re-opens; a superseded id is never resurrected; hand
  `change`/`owner`/`gate` carried onto every transition row; `emit_gaps` twice on an unchanged target appends
  nothing. **Proof:** the T3 script (`harness/T3_CLOSURE_LOOP.md` §1–5) against the sandbox using the ported
  production tools: OPEN→CLOSED→RE-OPENED→CLOSED on one row, tracker 0→1→0→1.
- **A-3 · P4 precursors.** R41 per-check fault isolation (one failing check never voids a layer's census);
  R40 configurable timeout + scalable duplicate count (L3's `kala_field` census must complete on production);
  R220 every population figure scoped to `is_active AND NOT dead_flag` (127) with the population stated;
  **D6** rate grading exactly as ruled (`DECISIONS_RECOMMENDATIONS_v2_0.md` D6 items 1–5: feature-detect
  `asset_throughput.duration_seconds`; attribute timing to the latest attempt; `Earn.build_record` and
  `Cost.baseline` separated and graded by cause; NULL of unknown cause → `NO_DETECTOR`, never PASS) with the
  seven test cases D6 item 5 names.
- **A-4 · stop honestly.** The rest of P4 (R42–R56 completion/registration/latest-row) is a second lane. Do not
  start it. Report exactly where A-3 ended.

## §4 — Lane B · the catalog names its producers (builder: Sonnet)

- **B-1 · the derivation.** New read-only script `platform/scripts/governance/catalog_provenance.py`. For each SCU in
  `platform/src/generated/capability_knowledge.snapshot.json` (182): take every `availability_contracts[].requirements[]`
  of `kind: source_query` (137 units; `source_ref` = `<file>:<a>-<b>`, 135 resolve — verified 2026-09-27). Parse the
  SQL **string literals** in that range (and one hop into a helper the range calls, when the call is a plain
  identifier the same file defines); extract relation names after `FROM`/`JOIN`/`UPDATE`/`INTO`; keep only names
  present in the union of `asset_registry.target_table` and `information_schema.tables` (a naive regex yields
  `today`, `the`, `unnest` — filter, never trust). Map table → producing asset(s) via `asset_registry.target_table`
  (117 of 127 active assets declare one; 103 distinct tables). **Shared tables** name every producer, flagged
  `shared`: `chart_facts` ← 7 `ga_*`, `bodha_msr_signals` ← 7 `bo_*`, `brahma_class_priors` ← 2, `classical_text_chunks` ← 2;
  where the query pins `fact_category`/`signal_family`, narrow to the producer that owns it only if
  `asset_registry.natural_key_partition` or the writer's declared category makes that ownership explicit —
  otherwise keep all, flagged. `kind: service_probe` (9) → the service asset by name; `kind: derived` (3) and the
  28 units with no availability contract → `NO_DETECTOR — no source_query requirement`. Output
  `nikasha_test/provenance/producer_provenance.derived.json`: per SCU, `producers[]` with
  `{asset_id, table, source_ref, disposition: derived_from_source_query, shared: bool}` or `no_detector: <reason>`.
  Keep the 12 existing `reviewed_output` claims as the authority where present and report agreement/disagreement.
- **B-2 · the closure.** From the union of reviewed + derived producers, compute the necessity closure over
  `asset_registry.depends_on` (NOT `build_dependencies` — dead pre-rename table, R219). Report: named producers
  before/after; necessary before/after (baseline 63/127); still-outside assets by layer, each with the reason
  (no unit names it / no unit names anything downstream of it). Write `nikasha_test/provenance/CLOSURE_REPORT.md`
  with every query and population stated.
- **B-3 · R219 reader scan.** Grep the codebase for readers of `build_dependencies`; list them. Do not drop or alter
  the table — that is a native decision; the scan is the evidence for it.
- **B-4 · `--check` mode.** `catalog_provenance.py --check` exits non-zero when any SCU has neither a reviewed nor a
  derived producer and no `no_detector` reason — the detector that makes "every unit names its producer" able to
  read false. Tests: a unit with a resolvable range → derived producer; an unresolvable range → no_detector with
  reason; a shared table → all producers flagged; the naive-regex noise words never appear as producers.
- **Not in this lane:** wiring the derived file into `compiler.ts` (a retrieval-plane change — follow-on after the
  gate); editing `editorial.ts`.

## §5 — The gate (reviewer: Opus, fresh context, read-only, never the implementer)

Each lane returns a packet report at `nikasha_test/wave1/<LANE>_REPORT.md`: diff by file with reasons; the proof
command and its output; honest limits; findings outside scope registered, never fixed silently. The executor then
dispatches the reviewer with the packet-reviewer role (`/Users/Dev/madhav-engine/.agents/agents/nirmana-packet-reviewer.md`,
checklist items 1–7 with item 2 read as: no writer, orchestrator, sealed tier or production data touched; ledgers
append-only). Verdict ACCEPT / ACCEPT_WITH_CORRECTIONS (each bound to the gate it blocks) / REJECT. Corrections go
back to the same lane; REJECT re-runs the lane from its report.

## §6 — What "done" means for wave 1

Both lanes ACCEPT at the gate; T3 passes under production tools; `catalog_provenance.py --check` runs and its
figures reproduce; the executor folds register rows (R216, R57/R58/R47/R62/R30, R40/R41/R220/R55, R85, R219),
plan status and STATE; fingerprints rotated last; drift exit 0/3. Nothing pushed by the lanes.

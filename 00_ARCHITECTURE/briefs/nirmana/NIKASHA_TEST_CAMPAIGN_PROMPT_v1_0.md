---
artifact: NIKASHA_TEST_CAMPAIGN_PROMPT
canonical_id: NIKASHA_TEST_CAMPAIGN_PROMPT
version: "1.0"
status: NATIVE-AUTHORIZED — this document IS the execution authority for campaign nikasha-test
campaign_id: nikasha-test
produced_on: 2026-09-26
authored_by: Claude Code (Fable 5.1), at the native's instruction, 2026-09-26
audience: Kimi Code agent, autonomous, on the MARSYS-JIS (Madhav) repository
model_routing: >
  Phases 0-5 (testing): Kimi K3256, medium effort. Phases 6-7 (analysis and the final report):
  Kimi K3, max effort. Switch models at the Phase 5 -> Phase 6 boundary and record the switch in
  EVENTS.jsonl. Do not run analysis at medium effort; do not run testing at max.
usage: >
  Paste this ENTIRE file as the first message of a fresh Kimi Code session started in
  /Users/Dev/Vibe-Coding/Apps/Madhav (or a worktree of it). The campaign is idempotent and
  resumable: re-pasting it into a new session after any interruption resumes from the durable
  STATE.md, never from zero. There are no human gates in this campaign.
what_this_campaign_is_not: >
  It does not elevate any asset. It does not edit the sealed tiers 1-3. It does not touch the
  orchestrator or its contract. It does not write to production. It TESTS the Nikaṣa system and
  delivers the plan for changing it, so the native can then run the real elevation L0 -> L5.
---

# NIKAṢA TEST CAMPAIGN — AUTONOMOUS EXECUTION PROMPT

## §0 — Read these first, in this order, every session

You do not auto-load `CLAUDE.md`; this repository's governing document is `CLAUDE.md` at the root,
and `AGENTS.md` is a thin loader pointing at it. Reading it in full is a hard instruction.

1. `CLAUDE.md` — in full. Emit the session-open handshake it requires (§G) before substantive work.
2. If this is your first session on this repository: `00_ARCHITECTURE/briefs/KIMI_CODE_ENVIRONMENT_PARITY_PROMPT_v1_0.md`, execute it, then return here.
3. **The Nikaṣa system — the thing under test**, read in this order:
   - `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md` (tier 1, SEALED)
   - `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md` (tier 2, SEALED, reopened once)
   - `00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` (tier 3, SEALED, reopened once)
   - `00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md` (tier 4, DRAFT_PENDING_REVIEW)
   - `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md` (the L0 instance — a TEST ARTEFACT of Nikaṣa, not production output)
   - `00_ARCHITECTURE/briefs/nirmana/l0_assets/*.md` (five pilot briefs — test artefacts)
   - `platform/scripts/governance/asset_census.py` (the inspector)
   - `00_ARCHITECTURE/control/asset_elevation_tracker.py` (the tracker)
   - `00_ARCHITECTURE/control/asset_gaps.jsonl` and `asset_certs.jsonl` (the two ledgers — read their `_schema` first lines)
   - `platform/scripts/governance/drift_detector.py`, `manifest_fingerprint.py`, `check_migration_ledger_vs_production.py`
   - `00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v1_0.md` (the register you will extend — never delete a row)
   - `00_ARCHITECTURE/briefs/nirmana/NATIVE_DECISIONS_2026-09-25_v1_0.md` (rulings 9-17 bind you)
   - `00_ARCHITECTURE/briefs/nirmana/BUILD_FAILURE_TRIAGE_2026-09-26_v1_0.md`
   - `00_ARCHITECTURE/briefs/reviews/REVIEW_DATA_PLANE_FINAL_v1_0.md` and `REVIEW_L0_STRATEGY_v2_0.md` — the house review format
4. `00_ARCHITECTURE/briefs/nirmana/nikasha_test/STATE.md` if it exists — **then resume from it.** Never redo a phase STATE records as closed.

## §1 — Who you are, and the only success metric

You are the **Nikaṣa test campaign executor**. Nikaṣa (निकष, the touchstone) is the system this
repository just built for elevating its data plane: four tiers of documents, an inspector, two
ledgers, a tracker and their governance detectors. It has been exercised exactly once, on one
layer, and that one run found defects in the system at every level — a detector in a sealed
document that failed on correct data, a template row no instance could fill, four bugs in the
inspector, a ledger that could not tell a gap from an improvement. That is the signal to test the
method before it is applied five more times.

**The only success metric is a plan the native can execute without re-investigating anything:**
every Nikaṣa component tested against the five tests below on every layer L0–L5, every defect in the
system registered with its reproduction, and an implementation plan ordered by dependency with a
proof for every packet. Commits, sandboxes, scripts, subagents and documents are costs, never
progress. A campaign that produces a beautiful test harness and no register rows has failed.

**The frame you must hold:** the L0 instance v3.0, the five pilot briefs and the current ledger rows
are Nikaṣa's *test run*, not its production output. When the system is frozen they will be
regenerated from it. Treat their findings as evidence about the system, not as work to finish.

## §2 — Authority, and the hard constraints

The native has delegated **full decision authority** to you for this campaign. Every question,
ambiguity or trade-off you would normally raise, **you decide immediately on the evidence** and
record in one appended line of `EVENTS.jsonl` (§4). You never wait. You never ask. If something
breaks — tooling, environment, a flaky test — you fix it and continue; a broken thing is a task,
never a stopping point.

Five constraints are absolute. They are the reason this campaign can be autonomous at all.

1. **Production is read-only.** Every database read goes through the read-only environment
   (`source /Users/Dev/madhav-l3/dbenv.sh`; the proxy listens on **5433** despite the script saying
   5434 — `export PGPORT=5433`). At session open, verify `SELECT current_setting('default_transaction_read_only')`
   returns `on`, and record it. The MCP postgres tool is read-only too. **You never write to
   production, never lift the read-only setting, never use a write-capable credential.** Every
   mutation this campaign needs happens in the sandbox (§5 Phase 1). If a test genuinely cannot be
   run without a production write, it is recorded as `NOT RUNNABLE — requires production write` in the
   register and the campaign continues.
2. **Tiers 1–3 are sealed.** You never edit `MADHAV_PRODUCT_DEFINITION_FINAL`, `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL`
   or `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0`. Every change they need is a **register row** with
   the exact clause, the proposed replacement text, and the test that surfaced it. The native reopens
   sealed documents by ruling; you propose.
3. **The asset template v2.0 and the inspector may be edited only for defects that block a test**,
   and every such edit is recorded as a register row marked `fixed during campaign` with the commit.
   Anything else is proposed, not done.
4. **The orchestrator and its `WriterBase` contract are frozen.** You never change them, and you never
   propose changing the contract. Engine-behaviour proposals (instrumentation, recovery, scheduling)
   go in the register's build-system section with their sequencing.
5. **Branch discipline.** Work on `campaign/nikasha-test`, branched from `origin/l3/kala-layer-briefs`.
   Commit and push at every phase close and at every register batch. Never push to `main`. Never
   place a file at the repository root (`00_ARCHITECTURE/ROOT_FILE_POLICY.md`). No secret, password
   or connection string ever appears in any output, log, commit or artefact.

## §3 — Model routing

- **Phases 0–5 (testing): Kimi K3256, medium effort.**
- **Phases 6–7 (analysis, plan, report): Kimi K3, max effort.**

Record the switch as an event. The reason the split exists: testing is mechanical and must be
cheap enough to re-run; analysis is where the value is and must not be rushed.

## §4 — Durable state, resumability, and the two logs

All campaign state lives under `00_ARCHITECTURE/briefs/nirmana/nikasha_test/`:

- `STATE.md` — the "you are here": phase, what is closed, baseline figures, current branch head,
  blockers. **Rewritten and pushed at every phase close.** A fresh session reads it and resumes.
- `EVENTS.jsonl` — append-only, one JSON object per line:
  `{"ts","phase","event","result","evidence"}` where `evidence` is a list of commit SHAs, file paths,
  run ids or the exact query that produced a figure. Every decision you take is one event.
- `derivations/` — Phase 4's test derivations (layer skeletons, asset briefs). Test artefacts.
- `harness/` — the sandbox builder, the planted-defect suite, the differential checks.
- `census/` — one census JSON per layer per run, named `<layer>_<timestamp>.json`.

**Resumability rule:** a phase is closed only when STATE.md says so *and* its commit is pushed. On
resume, re-verify the last closed phase's headline figure cheaply (one query), then continue.

## §5 — The campaign, phase by phase

Every phase ends with: STATE.md rewritten, EVENTS appended, register rows appended, commit pushed.

### Phase 0 · Orientation and baseline

1. Read §0. Emit the session-open handshake.
2. Verify the read-only posture (§2.1) and record it.
3. Verify the chain's fingerprints: `python3 platform/scripts/governance/manifest_fingerprint.py --check`
   and the per-entry check; run `drift_detector.py`; record the result as the campaign baseline.
4. Inventory every Nikaṣa component: path, version, status, sha256, last commit. This table is the
   first section of STATE.md and the first table of the final report.
5. Run the inspector on L0 (`asset_census.py --layer L0`), the tracker on L0, and record the baseline:
   assets, registered ids vs `has_writer`, failures per check, ledger row count by kind. **These are
   the numbers every later figure is compared against.**
6. Read the register and mark, for each OPEN row, whether this campaign will test it, fix it, or
   carry it. Append that disposition as an event per row.

### Phase 1 · The sandbox — the only place anything is mutated

Build `nikasha_sandbox`, a local PostgreSQL database (a local server or container; never the
production proxy) seeded from **read-only** extraction of production:

- **Schema** for every table that any `asset_registry` row of any layer names as `target_table`, plus
  `asset_registry`, `asset_throughput`, `build_runs`, `build_run_assets`, `build_events`,
  `brahma_ontology`, `classical_text_chunks`, `sutravali_rules` and whatever else the inspector reads.
  Extract DDL including constraints (the inspector reads `pg_constraint`) and indexes.
- **Data**: a full copy for any table under 50,000 rows; a deterministic 5% sample for larger ones
  (`ephemeris_daily`, `bg_muhurta_lattice`, `bg_synthetic_cohort`, …), sampled so that per-asset
  `count_sql` still returns a non-zero figure.
- **A manifest** `harness/SANDBOX_MANIFEST.json`: every table copied, rows in production, rows in
  the sandbox, sampling rule, extraction timestamp, and the sha256 of the DDL.
- **Fidelity check, which is itself a test:** run the inspector against the sandbox. For every table
  copied in full, the census verdicts must equal production's. For sampled tables, verdicts that depend
  on counts are expected to differ and must be listed as such. Any *other* disagreement is a finding.

The inspector reads its connection from `PG*` environment variables; point them at the sandbox for
every mutating test and back at the read-only proxy for every production read. **Record which
target every run used** in its census filename and in EVENTS.

### Phase 2 · Instrument tests — T1 (finds what is there) and T2 (does not invent what isn't), every layer

**T2 first, on production, read-only.** Run `asset_census.py` for each of L0, L1, L2, L3, L4, L5 and
`--layer all`. Record runtime per layer (the cost figure). Then, per layer, take a **stratified
sample of at least eight assets covering every kind present** — writer-backed data, service with no
table, multi-table, static/migration-seeded, empty-by-design, has-writer-but-never-run — and verify
**every** census verdict for those assets by hand, with your own independent query or grep, against
production. Compute the **false-positive rate per check**. Every verdict the census got wrong is a
register row: `inspector`, the check, the asset, the census's claim, the truth, and the reproduction.
Fix it if it blocks the campaign (§2.3); otherwise propose.

**T1 next, in the sandbox only.** Build `harness/plant.py`: for **every check the inspector runs**
(Build.registered, Build.contract, Build.target, Build.dag, Build.count_integrity, Build.completion,
Build.exercised, Build.history, Build.dep_liveness, Earn.build_record, Ldgr.source_presence,
Idem.pattern, Vocab.alias, Vocab.identity, Dens.served, Complete.depth, Count.floor, Cost.baseline),
plant **at least one defect that the check claims to detect** — a duplicate under the declared key,
an emptied alias set, a writer registration removed, a `depends_on` pointing at a never-lit asset, a
build record with `rows_written = 0` against a populated table, an `error` row in `build_run_assets`,
a column emptied to NULL, a count pushed below its floor, a capability module stripped of its
`density_contract`. Run the census after each plant and assert the check fails **for that asset and
no other**. Compute the **false-negative rate per check**. Every miss is a register row.

**Then test the tests.** Mutation of the detectors: break one check in a scratch copy of the
inspector (invert its comparison), re-run the planted suite, and confirm the suite **notices** —
proving the harness can fail. Differential test: reimplement three checks (`Vocab.identity`,
`Build.registered`, `Count.floor`) independently, with different queries, and diff their verdicts
against the inspector's over all six layers. Any disagreement is a finding about one of the two.

**Three-source rule, enforced by you:** a writer exists only if the code registers it *and* the
registry declares it *and* the run history has dispatched it. Where the three disagree, the
disagreement is the finding, and you record all three readings.

### Phase 3 · The closure loop — T3, never run before, sandbox only

Nothing in Nikaṣa has ever been closed. This phase proves the loop:

1. Choose **three gaps of three kinds** from the current ledger: a data gap (e.g. the doṣa alias
   sets), a registry gap (e.g. `has_writer` wrong for a registered writer), a detector gap (an asset
   whose `Idem.pattern` reads PARTIAL because the writer delegates to a seeder).
2. Apply each fix **in the sandbox** exactly as it would be applied in production (a seeder change,
   a registry row, an inspector improvement).
3. Re-run the inspector against the sandbox with `--emit-gaps`. **Observe what happens to the row.**
   The inspector currently only *appends* OPEN rows; whether it can *close* one by measurement is
   unproven. If it cannot, that is the campaign's most important finding — implement closure if it is
   a small change (`fixed during campaign`), otherwise specify it precisely in the register.
4. Write the certification record the passing check earns, in `asset_certs.jsonl`'s schema, to a
   sandbox copy of the ledger. Run the tracker against the sandbox ledgers. **Confirm `0/360`
   becomes `N/360`** and the asset's state changes.
5. **Regress**: re-break one fix, re-run, confirm the row re-opens and the count falls. A loop that
   only counts up is not a loop.
6. Record exactly what had to be built to make the loop work end to end. That list is the core of
   the implementation plan.

### Phase 4 · Document derivability — the tiers, tested by a fresh reader

You are the fresh reader the layer template's §5.4 test 1 requires, and a better one than the
author, because you did not write any of it.

For **each of L1, L2, L3, L4, L5**: derive a layer-instance skeleton from the sealed tier-3
template plus tiers 1–2 — at minimum Parts 0, 1.1, 2.1–2.7 and the 4.4 inheritance list — using
only what the documents provide plus the inspector's census for that layer. **Record every place
you had to invent something**, quoting the template clause that should have provided it. Write the
skeleton to `derivations/L<n>_INSTANCE_SKELETON.md` marked `TEST ARTEFACT — NOT AN INSTANCE`.

For **two assets per layer** (ten total; one ordinary writer-backed asset and one edge kind —
service, multi-table, empty, or never-run): derive a brief from the asset template v2.0 plus the
skeleton. Record every invention against the thirteen inherited rows, exactly as the L0 pilots did
(`l0_assets/*.md` §8 shows the format). Write to `derivations/<ASSET>_BRIEF_TEST.md`, `pilot: yes`.

Every invention is a register row against the document that failed to provide it, with the clause
and the proposed text. Pay particular attention to: the carriage-check assignment (row 13 — known
defect C-9, confirm or refute it per layer); shared tables with several producers (C-10); anything
that only works for a reference layer; anything that only works for a chart-product layer; and the
`[TRANSFERS]` obligations, which are stated in the data plane because the retrieval and conversation
planes are not built — test whether a layer plan can tell what is its own work.

### Phase 5 · Consistency — T5, the pieces agree

Cross-check, mechanically where possible, every shared vocabulary across every Nikaṣa component:
gate keys and count (nine), verdict vocabulary (`PASS FAIL PARTIAL NO_DETECTOR N/A`), ledger state
vocabulary, `kind`, the tracker's `SHAPE` markers vs the asset template's §2 list, criterion strings
between hand-written and census rows, "ten obligations" wherever it appears, the `[TRANSFERS]`
convention, version/status fields vs the manifest, the three "review record" names, and every count a
document states about another document (rows, elements, dispositions, evidence states, edge types).
Run `drift_detector.py` and `manifest_fingerprint.py --check` last. Every disagreement is a register
row naming both surfaces.

Also reconcile the ledger: identify every hand-written row that overlaps a census row in substance
and propose the single namespace (register row; do not delete anything).

**— switch to Kimi K3, max effort —**

### Phase 6 · Analysis

This is where the campaign earns its keep. Produce, with every figure carrying its reproduction:

1. **Readiness verdict per component** — each of the four tiers, the inspector, each ledger, the
   tracker, each governance detector: `READY` / `READY_WITH_CHANGES` / `NOT_READY`, with the evidence
   and the register rows that decide it.
2. **The register, extended to v2.0** — every finding from Phases 0–5 as a row; the existing rows
   re-verified and their states updated; nothing deleted. Add `severity` (BLOCKS_FREEZE /
   BLOCKS_LAYER / DEGRADES / COSMETIC), `depends_on` (other register ids), and `effort` (hours, honest).
3. **Root-cause clustering** — where many rows share one cause, say so and name the cause. The L0
   run found three findings behind 104 of 225 rows; expect the same shape.
4. **The implementation plan** — ordered packets, each with: the register rows it closes, its proof
   (a detector that fails until it lands), its dependencies, its effort, and **who decides** — a
   packet that needs a native ruling names the ruling and is not blocked by it; the plan continues
   around it. Native-only decisions are collected in one list, `DECISIONS_FOR_THE_NATIVE`, each with a
   recommendation and the cost of each option.
5. **The freeze criterion, evaluated** — the five tests, pass/fail per layer, and precisely what
   remains before Nikaṣa can be sealed and the real run started at L0.
6. **What the campaign could not test, and why** — honestly, with what would be needed.
7. **The build-system section** — instrumentation before the from-scratch run (rate, error text),
   the run-killer (registry change mid-run), stability in parallel, the builder's own plan last —
   re-verified against the run history at analysis time, with figures.

### Phase 7 · Report and handoff

- `00_ARCHITECTURE/briefs/nirmana/nikasha_test/NIKASHA_TEST_CAMPAIGN_REPORT_v1_0.md` — the report,
  in the house review format (frontmatter: artifact, tested, mode, verdict; numbered findings with
  quoted text and replacement text; the tests run and their results per layer; every figure with the
  command or query that produced it).
- `00_ARCHITECTURE/briefs/nirmana/NIKASHA_IMPLEMENTATION_PLAN_v1_0.md` — the plan from Phase 6.4.
- `NIKASHA_CHANGE_REGISTER_v2_0.md` — the extended register (v1.0 retained, superseded).
- `DECISIONS_FOR_THE_NATIVE.md` — under `nikasha_test/`.
- STATE.md final; EVENTS complete; manifest entries and fingerprints for every new artefact,
  rotated in the same commit; drift detector clean on fingerprints.
- A final section in the report: **how to re-run this campaign** after the changes land, so the
  freeze decision rests on a second pass, not on this one.
- Commit, push, and open a pull request from `campaign/nikasha-test` into `l3/kala-layer-briefs`
  with the report's verdict as its description. Do not merge it.

## §6 — Record shapes

**Register row** (append to the register's tables; one row per finding):
`| R<nnn> | <change, with the clause and proposed text> | <test or phase that surfaced it> | <state> |`
plus, from Phase 6: severity · depends_on · effort.

**Event** (`EVENTS.jsonl`):
`{"ts":"<ISO>","phase":"<0-7>","event":"<UPPER_SNAKE>","result":"<one sentence>","evidence":["<sha|path|run id|query>"]}`

**Verdicts, exactly these spellings:** `PASS` · `FAIL` · `PARTIAL` · `NO_DETECTOR` · `N/A` · and for
this campaign only, `NOT_MEASURED` and `NOT_RUNNABLE — <reason>`.

## §7 — The quality bar, non-negotiable

- **Every figure names its population and its instrument**, and can be re-run from what you wrote.
  "grep over the codebase" is not an instrument; "grep over `platform/python-sidecar/**/*.py`
  excluding tests, at commit X" is. A join is not measured until its keys are.
- **A status is earned or it is null.** Nothing is PASS because nothing failed; PASS means a detector
  ran and could have said otherwise. `NOT_MEASURED` is always available and always honest.
- **The inspector's own lessons bind you:** a regex over source that can match a docstring is not a
  detector; a line-oriented read of a field that can contain newlines is not a parser; a framework
  file scanned as a writer reports the framework's docstring as a violation. Use the AST, use
  `json_agg`, exclude `__init__.py`.
- **Three sources, always** — code, registry, run history — and the disagreement is the finding.
- **No invented numbers, sources, detectors or confidence.** Where you cannot measure, say so.
- **Findings about the system are not findings about the assets.** A defective asset the inspector
  correctly reports is the system working; a correct asset the inspector reports as defective is the
  campaign's business. Keep the two apart in every table.
- **Effort estimates are honest hours from someone who has read the code**, not round numbers.

## §8 — Stop conditions — the only four

You stop a *packet* (never the campaign) and record a `DECISIONS_FOR_THE_NATIVE` entry when the
work would require: (1) a production write; (2) editing a sealed tier; (3) changing the orchestrator
or its contract; (4) exposing a secret. In every case you continue with everything else. There is no
fifth reason to stop, and there is no reason to ask.

## §9 — What "done" means

The campaign is complete when all of the following are true and pushed:

- Every phase closed in STATE.md with its commit.
- The inspector run on all six layers, with false-positive and false-negative rates per check,
  from a hand-verified sample per layer and a planted-defect suite that has itself been mutation-tested.
- The closure loop proven end to end in the sandbox, including regression — or its failure specified
  precisely.
- Five layer skeletons and ten test briefs derived, with every invention registered against its clause.
- Consistency checked across every shared vocabulary, with drift detector and manifest clean.
- The register at v2.0 with severity, dependencies and effort on every row.
- The implementation plan, ordered, with a proof per packet and native-only decisions collected.
- The report, every figure reproducible, the freeze criterion evaluated, and a re-run procedure.
- A pull request open, not merged.

If the campaign is interrupted before that, STATE.md says exactly where, and the next session
resumes there. It never starts over.

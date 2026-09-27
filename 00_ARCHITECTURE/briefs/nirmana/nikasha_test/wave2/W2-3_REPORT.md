---
artifact: NIKASHA_WAVE2_W2-3_REPORT
packet: W2-3 — deeper detectors (the last packet of wave 2)
version: "1.0"
status: BUILT — awaiting the gate review (executor dispatches a fresh reviewer; the executor folds register/plan/STATE)
produced_on: 2026-09-27
builder: Opus (wave-2 builder, packet W2-3 only)
base: a72cdf460 (first production emit; the real ledger holds 830 lines)
head_code: 8702ee331
rows: [R242, R20, R240, R241, R21, R23]
commits:
  - "fa23abe69 R242"
  - "50c0d4535 R20"
  - "f31a98e4f R241"
  - "3f9a11428 R21"
  - "f032ecec5 R23"
  - "ee2c7d7ee R20 (follow-up: the PASS is per table)"
  - "8702ee331 R241 (follow-up: guard helpers)"
  - "R240: no code commit — discharged by R20 (§2.3)"
files_touched:
  - platform/scripts/governance/asset_census.py
  - platform/scripts/governance/__tests__/test_w2_3_deeper_detectors.py   (new, 48 tests)
  - "platform/scripts/governance/__tests__/test_w2_1_earned_verdicts.py (R21: one harness stub line)"
  - "platform/scripts/governance/__tests__/test_a4_gate_corrections.py (R21: one harness stub line)"
  - 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave2/W2-3_REPORT.md + w2-3_evidence/**
not_touched: asset_elevation_tracker.py (no change needed), writers, orchestrator, migrations, sealed tiers,
  editorial.ts/compiler.ts, register/plan/decisions/STATE, catalog_provenance.py + its tests + provenance/**,
  00_ARCHITECTURE/control/asset_gaps.jsonl + asset_certs.jsonl (md5 7f2257a8… / 514cbdfc…, 830 / 1 lines —
  identical at session start, after every run, and at report time)
---

# Nikaṣa wave 2 · W2-3 · builder report

## §0 — Summary

| row | commit | one line |
|---|---|---|
| R242 | `fa23abe69` | `target_owners()` is read once per `measure()`; verdicts unchanged, calls 3 → 1 in the test. |
| R20 | `50c0d4535` + `ee2c7d7ee` | `Idem.pattern` follows the writer's delegation (writer **class** → seeder / shared helper / adapter target, ≤ 2 hops) and grades what the rebuild actually runs; a PASS is per own table. |
| R240 | — (R20) | ka_gochara reads PARTIAL with an explicit "registry/writer table mismatch (R240 …)" reason; no separate change needed. |
| R241 | `f31a98e4f` + `8702ee331` | The hold guard runs over the whole resolved scope and recognises return / continue / break / skip-without-raise holds, the count probe, negated / walrus / `is None` / `> 0` / `== 0` polarity, and guard helpers; an upstream probe and a same-build resume probe are not holds. |
| R21 | `3f9a11428` | Blocking radius (transitive active dependents, every layer) is attached to every `Build.*` gap row as `blocking_radius` + `severity_weight = 1 + radius`. |
| R23 | `f032ecec5` | `Reach.fields` measures width (built columns some capability selects) and depth (rows some capability query can return) — reported, not graded. |

**The 27-asset Idem.pattern resolution.** The register's "27 PARTIAL" is the first census run's figure, which
covered L0 only: today L0 still has exactly 27 PARTIAL `Idem.pattern` assets. Across all six layers the PARTIAL
population at `a72cdf460` is **69** (L0 27 · L1 18 · L2 14 · L3 5 · L5 5; ka_kshetra is the one FAIL).
- **The 27 (L0): 26 → PASS, 0 → FAIL, 1 stays PARTIAL** (bg_text_index: its own table is only `UPDATE`d in place).
- **All 69: 58 → PASS, 0 → FAIL, 11 stay PARTIAL**, each with a named reason:
  - 1 registry/writer table mismatch (R240): ka_gochara;
  - 2 own table only `UPDATE`d in place: bg_text_index, bo_laksana_rerank;
  - 8 no write to the asset's own table anywhere in the resolved scope (graded PARTIAL, never N/A — a static scan
    cannot prove a write's absence): bo_samvada, ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana,
    mi_abhilekha, mi_seva, mi_vistara;
  - 0 "delegation deeper than the hop limit", 0 "table the scan cannot name".
- 10 of the 58 PASSes needed the second hop (the L1 adapter → `ga_writers/ga_*_writer` → `ga_writers/_idempotency`);
  with a one-hop limit they would read PARTIAL naming the cut chain.
- R127's three L2 delegating writers: bo_bimba **PASS**, bo_pramana_mapa **PASS** (both through
  `bodha_writers/_idempotency.py`), bo_samvada **PARTIAL** (its writer runs no write at all — correct).

**Packet proofs.**
1. **Branch enumeration (§3):** 39 PASS/N/A-yielding branches (38 at W2-2 + 1 new). 20 genuine, **15 fixed**,
   **2 proxy**, 2 contested. R20/R241 move #2 and #3 (the two `Idem.pattern` PASS branches — the largest remaining
   proxy cluster) from proxy to fixed; the one new branch (#39, L0 own-table delete-then-insert) is fixed by
   construction. No new N/A branch.
2. **Census (§4):** six layers, read-only, `a72cdf460` vs HEAD: 2,446 verdicts each; **58 verdict changes, all
   `Idem.pattern` PARTIAL → PASS, 0 unexplained**; 151 text-only changes (127 `Reach.fields`, 24 `Idem.pattern`).
3. **Next emit (§5):** on a copy of the real 830-line ledger, HEAD **closes 58** real OPEN gaps (all
   `Idem.pattern`), opens 11 (`Complete.depth`, identical under base code — live data moved), re-opens 0. **17 of
   the 58 hand-verified against writer source**, all genuine. Base code on the same data closes 0.
4. **Suite / fingerprint / drift / ledgers (§6):** offline 300 → **348** tests (323 passed · 23 skipped · 2 failed;
   the 2 are the pre-existing `test_drift_detector_h35_h38.py` pair, failing identically at `a72cdf460`); live
   (full suite, one invocation) **346 passed · 2 failed** at `8702ee331`; manifest **MATCH**; drift
   **exit 3** (1 LOW, pre-existing); production ledgers byte-identical throughout.

## §1 — Scope and safety

- **Database:** read-only through the session `pgenv.sh` (`default_transaction_read_only = on`, checked at start);
  never `dbenv.sh`, never `gcloud`; `timeout 300` on DB commands, `timeout 900` on six-layer runs and the live suite.
- **Ledgers:** never written. `asset_gaps.jsonl` md5 `7f2257a8d4f0d6a7a21c0648b4101f85` (830 lines),
  `asset_certs.jsonl` `514cbdfcf3fa71b3e382f84a978bf369` (1 line) — checked at start, after each emit run, and at
  report time. Every emit ran on a copy (`NIKASHA_CONTROL_DIR=<scratch>/w2-3/ctrl_*`).
- **Commits:** one row per commit, `git commit -- <paths>` only-mode; the one new file was `git add`ed by path
  first. Never `-A`, `-a`, `--amend`, never pushed.
- **Base worktree:** `git worktree add --detach <scratch>/w2-3/wt_base a72cdf460`, removed at the end (§6).
- No writer, orchestrator, migration, sealed tier, register/plan/decisions/STATE, or Lane B file was touched.

## §2 — Per row

Mutation method (`w2-3_evidence/mut.py`): apply one exact single-occurrence replacement to `asset_census.py`, run the
named tests (must fail), restore and check the md5 is byte-identical, then re-run the whole offline suite. The
"without" runs (`without.py`) run the new tests with `asset_census.py` at the pre-row commit. Every entry is in
`w2-3_evidence/mutation_runs.log`; every spec is in `w2-3_evidence/mutation_specs/`. **All 32 mutations were
killed; every revert was byte-identical; the suite after each revert showed only the 2 pre-existing failures.**

### §2.1 R242 — `target_owners()` once per `measure()` · `fa23abe69`
- **Diff.** `owners.setdefault("map", target_owners())` evaluated its argument on every call. It is now
  `owners["map"] if "map" in owners else owners.setdefault("map", target_owners())`. An `Unknown` from the read is
  not cached, so each asset needing the map still reads ERRORED.
- **Tests.** `test_r242_the_ownership_map_is_read_once_per_measure_and_the_verdicts_are_unchanged` (3 target-less
  assets: 1 read; verdicts/texts equal `_grade_target_less` over the same map: FAIL / PASS / PASS);
  `test_r242_an_unreadable_map_is_not_cached_as_empty`.
- **Without the change:** 1 failed (3 reads). (The log labels this run "at HEAD"; HEAD was then `a72cdf460`.)
- **Mutations:** R242-M1 eager `setdefault` → 1 failed; R242-M2 cache an empty map → 2 failed.

### §2.2 R20 — follow the writer's delegation · `50c0d4535`, follow-up `ee2c7d7ee`

**What changed in `idem_scan`.**
- **Scope (`_delegation_scope`).** It starts at the **registered class**, not the whole module. It adds the
  same-module definitions the class references by name (helpers and module-level SQL constants, transitively).
  Then it follows every first-party definition that code references in another module — imported names, function-
  level imports (the L1 adapters import their builder inside `run()`), module attributes (`db.replace_prior_…`),
  package re-exports — up to `IDEM_DELEGATION_HOPS = 2` modules away. The orchestrator package is never a delegate.
  A chain the limit cuts is reported only when its target module holds write SQL.
- **Facts (`_write_facts`).** Over the resolved scope's non-docstring SQL: `replace` (DELETE / TRUNCATE / CREATE OR
  REPLACE VIEW), `upsert` (INSERT … ON CONFLICT — also when the two are split across strings of one function),
  `insert`, `update`, and `dynamic` (a statement whose table the scan cannot name). F-string `{X}` resolves through
  module constants and `for` sequences, and `a + b` concatenations are read as one text.
- **Grading.**
  - **PASS**, delete-then-insert layers: a replacement of one of the asset's own tables (target_table ∪ count_sql
    tables).
  - **PASS**, upsert layer (L0): an `INSERT … ON CONFLICT` **into an own table** (was: `ON CONFLICT` text anywhere
    in the writer), or a delete-then-insert of it — a full replacement, not the convention, and no accretion.
  - **Follow-up `ee2c7d7ee`: the PASS is per table.** Every own table the scope INSERTs into must itself be
    replaced or upserted.
  - **FAIL** only on a fully-read scope (no cut chain, no unnamed table), for any of: an own table plain-INSERTed
    with no replacement (accretes); an own-table upsert where §N.3 requires delete-then-insert; a held rebuild
    (R241).
  - **PARTIAL** otherwise, with every applicable reason named.
  - **Never N/A:** `idem_scan` itself returns no N/A. N/A still comes only from `_no_writer_scanned` with
    `has_writer=false`.
- **`_parse`** is cached per (path, content).

**The three acceptance items W2-2 set for R20.**
- **(a) ka_kshetra's refused-rebuild shape and its non-raise / delegated variants.** ka_kshetra still reads FAIL at
  `services/ka_kshetra/writer.py:545 (raise KshetraReplacementHeld …)`. The non-raise and delegated variants are
  R241's (§2.4).
- **(b) bo_upaya.** `bo_upaya.py` → `bodha_writers/_idempotency.py:replace_prior_rm_resonances` /
  `replace_prior_rm_prescriptions` (one hop) → PASS. The text names `bodha_rm_resonances (…_idempotency.py:430/435)`
  and `bodha_rm_remedy_prescriptions (…:445)` with the chain. Those helpers delete per (chart, ayanamsha,
  `snapshot_type`), the same scope the C-KSHETRA review verified at `_idempotency.py:425–455`.
- **(c) ka_gochara** stays PARTIAL, with the explicit reason "registry/writer table mismatch (R240, a
  registry-data finding — not closable by the detector): the registry declares kala_gochara_windows, the writer
  replaces kala_gochara_windows_v2". Resolving `TABLE` does not launder it. The test also shows the control: were
  the registry re-pointed to `_v2`, the same writer PASSes on true grounds.

**Tests** (`test_w2_3_deeper_detectors.py`, R20 section; fixture sidecar trees on disk, the real `idem_scan`):
delegated helper PASS naming chain; helper functions the writer never calls are not credited (→ FAIL accretes); L0
seeder upsert PASS / sibling-table ON CONFLICT → FAIL; two-hop L1 chain PASS; three-hop → PARTIAL naming the cut
chain; class scoping (bo_laksana / bo_laksana_rerank shape); R240 mismatch + control; own-table upsert FAIL /
PARTIAL with an unnamed DELETE; split INSERT/ON CONFLICT is an upsert (control); a writer that writes nothing →
PARTIAL "not graded N/A"; end-to-end `measure()` + `emit_gaps()` on a ledger copy (1 close, the mismatch stays
OPEN); real sources (bo_upaya, ka_gochara, ka_kshetra, bo_bimba, bo_pramana_mapa, bo_samvada, bo_laksana_rerank,
ga_positions, bg_rules); live: no Idem N/A with a writer, every PASS names an own table; follow-up: multi-table
writer FAIL / PARTIAL / PASS.
- **Without the change:** 14 of 15 offline R20 tests failed (the 15th is live-only); follow-up: 2 of 3 (the third
  is the PASS control).
- **Mutations (9, all killed):** M1 no delegation followed (7 failed) · M2 whole module, not the class (3) · M3
  ON CONFLICT anywhere (1) · M4 name-stem match launders the mismatch (3) · M5 FAIL on an unread scope (2) · M6
  "no write" reads N/A (4) · M7 uncalled helpers credited (1) · R20b-M1 per-asset PASS (2) · R20b-M2 FAIL on an
  unread scope (1).
- **Live** (`idem_all.py`, 127 assets, `idem_before.json` → `idem_r20b.json`): PARTIAL 69 → 11, PASS 52 → 110, FAIL
  1 → 1, N/A 5 → 5. **0 PASS lost, 0 new FAIL, 0 new N/A.** 24 text-only changes (§4). The follow-up moved 0
  verdicts (0 live instances of the per-table shape; measured over all 127).

### §2.3 R240 — discharged by R20; no separate code change
The mismatch is detected generically: a table the scope replaces that is not an own table, but shares an own
table's name stem (`t.startswith(o + "_")` or the reverse). It is named, it stays non-closable, and
mutation R20-M4 (letting the stem match count as own) is killed by 3 tests, including the live-shape one. The
registry fix itself remains the data-plane owner's (R240's row text), untouched here.

### §2.4 R241 — the disclosed blind spots · `f31a98e4f`, follow-up `8702ee331`

**Closed (each with a test that fails without the change):**

| W2-2 RC-1 shape | now detected as | test |
|---|---|---|
| (a) a hold that `return`s | FAIL "… (return after the output-existence probe …)" | `…every_disclosed_hold_shape…[early_return]` |
| (a) a skip: `continue` / `break` in a loop over owned tables | FAIL "(continue …)" | `[continue]` |
| (a) a skip with no raise/return (delete only in the empty branch) | FAIL "the delete runs only in the output-empty branch" | `[skip_no_raise]` |
| (b) `count(*) … WHERE chart_id` probe, `n > 0` | FAIL | `[count_probe]` |
| (c) guard in a delegated module | FAIL naming the helper and "reached via …" | `…a_guard_in_a_delegated_module_is_seen` |
| (c′) guard helper raising, delete in the caller (follow-up) | FAIL "raise X in the guard helper _assert_empty" | `…a_guard_helper_raising_on_populated_output…` |
| (d) negated test (`if not populated: delete … else: raise`) | FAIL | `[negated]` |
| (d) walrus / `bool()` / `row[0]` / `is None` / `== 0` / `0 < x` | polarity read correctly | `[walrus]` + controls |

**Precision rules (so the widened guard does not manufacture FAILs):**
- **A probe is an OUTPUT probe only when it reads one of the asset's own tables** (or a table the scan cannot
  name). Found live: with the count-probe form, mi_jivanaghatana's `count_chart_lel_events` (it counts its INPUT
  `life_events` and raises when the input exists but nothing was built) read as a hold. It is not one.
- **A probe pinned to the current build (`… AND build_id_uuid = %s`) is a resume check, not a hold.** Found live:
  ga_vargas's `_check_already_written` counts rows *this build* already wrote. A rebuild has a new build id, so it
  is never held by that check.
- **A call inside `try/except` does not propagate a helper's raise.**
- **Controls that PASS:** an upstream probe, a same-build resume probe, an empty-polarity raise, and the
  incremental skip `if populated and unchanged: return`.

**Evidence.**
- **Without the change:** 8 of 13 R241 tests failed (the 5 passing are the 4 controls and the real-writer check);
  follow-up: 1 of 3.
- **Mutations (9, all killed):**
  - M1 any-table probe (2 failed), M2 build-scoped probe counted (2), M3 raise-only stop (3), M4 no skip-hold (1);
  - M5 negation ignored (1), M6 guard in the writer file only (1), M7 no count probe (2);
  - R241b-M1 helper calls ignored (1), R241b-M2 try-wrapped calls counted (1).
- **Live:** 0 verdict and 0 text changes vs R20. None of these shapes is live today; ka_kshetra is unchanged.

**Still undetected — each with a writer pattern that would fool the check today:**
1. **Emptiness computed in SQL:**
   `empty = cur.execute("SELECT NOT EXISTS (SELECT 1 FROM own WHERE chart_id=%s)").fetchone()[0]; if not empty: raise Held`
   — `SELECT NOT EXISTS` is not a recognised probe form (recognising it needs the inverted polarity), so no probe →
   PASS.
2. **A compound test:** `if self._populated(conn) and not ctx.config.get("force"): return`.
   - `BoolOp` tests are deliberately not read as holds, because the legitimate incremental skip
     (`populated and unchanged`) has the same shape.
   - A force-flag hold therefore PASSes.
3. **A flag built from a comparison:** `skip = self._populated(conn) is not None; … if skip: raise Held`. Only
   names bound directly to a probe call (or through `bool/int/len`, subscript, await) are tracked.
4. **A probe with no literal SQL in scope:** an ORM / query-builder probe
   (`session.query(Row).filter_by(chart_id=c).first()`), or SQL assembled in a variable
   (`sql = base + where`) with the table in neither part.
5. **Anything beyond the resolved scope:** a guard more than 2 hops away, reached by dynamic import, `getattr`, a
   registry/dispatch table, or a callback passed in from outside.
6. **A hold enforced by the database:** e.g. a unique constraint violated on purpose so the insert fails and the
   writer catches it and returns; or a trigger. The scan reads Python, not DDL.
7. **Empty-UPSTREAM early returns placed before the replacement** (ga_yoga, bo_samskara — hand-verified in §5).
   These are not populated-output holds, and grading them FAIL would be wrong. But if an upstream ever empties, the
   prior rows survive a "rebuild". Disclosed, not detected.

### §2.5 R21 — blocking radius · `3f9a11428`

**The metric** (`blocking_radius`, docstring is the definition), per active asset A:
- `transitive` — the number of distinct ACTIVE assets, in every layer, that depend on A through
  `asset_registry.depends_on`, directly or through any chain. Edges run only between active assets. A cycle counts
  each member once and never A itself.
- `direct` — those declaring A in their own `depends_on`.
- `severity_weight = 1 + transitive` — an isolated leaf weighs 1.

**How it is read and attached.**
- `dependency_graph()` is read once per `measure()` (one registry-wide query) and fault-isolated: an unreadable
  DAG leaves `transitive`/`severity_weight` **null with the reason**, never 0 (which would read as "leaf, lowest
  priority").
- Every census asset carries `blocking_radius`.
- Every `Build.*` row `emit_gaps` writes (OPEN, RE-OPENED, CLOSED) carries `blocking_radius` and
  `severity_weight`, measured by **this** run (a prior row's figure is never carried — the DAG moves). Unmeasured
  radii also carry `blocking_radius_note`.
- Non-Build rows carry nothing.

**Tests.**
- `…the_radius_is_the_count_of_active_assets_that_transitively_depend_on_it` (cycle, inactive dependency, cross-layer);
- `…a_root_and_a_leaf_with_the_same_verdict_open_differently_weighted_build_gaps` (both FAIL `Build.completion`:
  rows 3/4 vs 0/1);
- `…an_unreadable_dag_is_unmeasured_never_zero`;
- `…a_closing_or_reopening_build_row_carries_the_radius_measured_now`;
- live: the radius equals an **independent recursive CTE** over `asset_registry` for all 127 assets.
- **Without the change:** 4 of 4 offline tests failed. The unit test fails because the function is absent; the
  three end-to-end tests fail on behaviour (no row carried a radius).
- **Harness:** the two offline `measure()` harnesses (`test_w2_1._stub_layer`, `test_a4._stub_layer`) stub the new
  layer-wide read, one line each. Their docstrings require every layer-wide read to be stubbed, as W2-2 did for
  `latest_attempts`.
- **Mutations (5, all killed):** M1 direct only (3) · M2 unmeasured reads 0 (1) · M3 no radius on transition rows
  (1) · M4 cycle counts itself (1) · M5 Build gaps not annotated (3).

**Live figures.**
- **Distribution:** 40 assets have radius 0, 15 are 1–5, 18 are 6–20, 54 are >20.
- **Top radii:** ga_positions 79, bg_ontology 69, bg_reference 62, ga_dashas 61, ga_vargas 61.
- **Real rows:** emitting the HEAD census onto a copy of the pre-first-emit 263-line ledger opens 164 Build rows,
  **164 with a radius**, 0 non-Build rows with one.
- **Same criterion, different weight:** `ga_positions-Build.history` weighs 80, `bo_cdlm_summary-Build.history`
  weighs 1.
- **Limit:** the real 830-line ledger's existing OPEN Build rows gain the field only at their next transition
  (emit never rewrites an OPEN row — idempotency); the census JSON carries it for every asset on every run.

### §2.6 R23 — field-level reachability · `f032ecec5`

**Surface.** Every layer's capability modules: `platform/src/lib/retrieval/registry/layers/**/*.ts`, excluding
`*.test.ts` and `__tests__`. A field is dark only if no capability of any layer reads it.
- No descriptor field declares which tables or columns a capability reads (`types.ts` has only
  `data_source: stored|computed|hybrid`), so the census parses the SQL in the modules' string and template literals,
  with comments skipped (the R51 scanner discipline).
- Written independently of `catalog_provenance.py` (not touched, not imported).

**Width** — built columns some capability SELECTs from the target table, divided by built columns.
- "Built" means the depth census's populated columns (all columns when depth measured no rows; the basis is
  stated). Dark columns are named.
- **Rules:**
  - `*` / `alias.*` exposes every column;
  - another alias's columns do not count, and neither do string-literal contents;
  - a FROM counts only with a SELECT in front of it — so prose such as "… rows from ga_yoga_firings" is not a query
    (found live and fixed before commit);
  - a run-time select list (`SELECT ${cols}`) makes width an explicit **lower bound**, naming the module.

**Depth** — the share of the table's rows (the bound chart's, when the table has `chart_id`) some capability query
can return:
- **1.0 (upper bound):** when any query reads it with no literal row pin, or with a predicate the parser cannot
  read (any `OR`);
- **counted read-only:** otherwise, the rows matching the union of the literal `=` / `IN` pins;
- **0.0:** when nothing reads it.

**Reported, not graded.** The verdict stays `NOT_GENERIC`, so it never opens or closes a gap. Grading thresholds
are a decision above the census.

**Tests and evidence.**
- **Tests:** width with dark columns (a comment, a description and a `__tests__` module do not count; another
  alias's column does not count); pinned depth 3/10 = 30% with a chart-scoped count; an `OR` or one unpinned query
  keeps depth 1.0 with no count run; a run-time list gives a lower bound; nothing reads the table (0/0) vs a missing
  directory (unmeasured); live checks on real capabilities (chart_divisionals width 1.0 via `SELECT *`;
  ga_yoga_firings lower bound via `SELECT ${cols}`; mimamsa_export_log read by none).
- **Without the change:** 6 of 6 offline tests failed. A first without-run errored at collection (the test module
  bound `ac.capability_sql` at import); the binding was made lazy and the re-run failed on behaviour —
  `R23-without-v2` in the log.
- **Mutations (7, all killed):** M1 prose counts as a query · M2 other-alias columns counted · M3 unpopulated
  columns count as built (2 failed) · M4 dynamic list not flagged · M5 OR read as pins · M6 missing directory
  reads as empty · M7 keyword alias swallows the WHERE (the rest 1 failed each).

**Live figures.**
- 117 target tables measured; 10 assets have no target table in production, and say so.
- **26 tables are read by no capability module's SQL** (§8 OS-3).
- 17 have width as a lower bound (run-time lists).
- Width over the 91 read tables: median 0.75, 6 at 1.0.
- Depth: 91 at 1.0 (upper bound), 26 at 0.0. One table (ephemeris_daily) is read only through pinned queries: its
  count ran live, 825,084 / 825,084 rows match `ayanamsha_id = 'tropical'`.

## §3 — Proof 1: every branch that can yield PASS or N/A (lines at `8702ee331`)

Labels are W2-1's: genuine / fixed / proxy / contested. "W2-3" marks this packet's change.

| # | file:line | criterion — condition | label |
|---|---|---|---|
| 1 | `:397` | Build.contract PASS — AST scan of the registered class | **proxy** (A1), unchanged |
| 2 | `:939` | Idem.pattern PASS (upsert layer) — **W2-3:** an `INSERT … ON CONFLICT` into an OWN table, reached by the rebuild (writer class + ≤2 delegation hops), every own table the scope inserts into covered, no hold anywhere in the scope | **fixed (R20/R241)** — was proxy ("ON CONFLICT anywhere in the writer") |
| 3 | `:944` | Idem.pattern PASS (delete-then-insert) — **W2-3:** a DELETE/TRUNCATE of an own table reached by the rebuild, same three conditions | **fixed (R20/R241)** — was proxy for delegated replacement; residual blind spots named in §2.4 |
| **39** | `:941` | **new (R20):** Idem.pattern PASS (upsert layer) — the own table is replaced by delete-then-insert (a full replacement, not the convention) | **fixed** — same measurement as #3 |
| 4 | `:1673` | Build.history PASS — cascade-blocked only, ≥1 completion | genuine |
| 5 | `:1683` | Build.history PASS — no error/abort, ≥1 completion | fixed |
| 6–8 | `:1767/:1770/:1772` | Earn N/A — never attempted / healthy non-execution / failed before completion | genuine per D6; unreachable in production (1094 absent) |
| 9 | `:1777` | Earn PASS — linked completion write with a duration | genuine; unreachable in production |
| 10 | `:1789` | Cost PASS — sanctioned baseline | genuine; unreachable in production |
| 11 | `:1933` | contract/idem N/A — no writer, registry agrees | fixed (W2-1). **W2-3:** still the ONLY way Idem.pattern reads N/A (live test) |
| 12 | `:2105` | Count.floor N/A — `target_floor=0` | fixed |
| 13 | `:2120` | Count.floor PASS | fixed |
| 14 | `:2165` | Carr.detector adopted verdict | genuine |
| 15 | `:2239` | Build.registered PASS | genuine |
| 16 | `:2247` | Build.registered N/A | genuine |
| 17 | `:2256` | Build.target PASS — target_table declared | genuine |
| 18 | `:2258` | Build.target N/A — service or writerless | fixed (R53) |
| 19 | `:2270` | Build.dag PASS | **contested** (OS-2), unchanged |
| 20, 21 | `:2276` | Build.count_integrity PASS / N/A | genuine |
| 22 | `:2309` | Build.completion N/A | fixed |
| 23 | `:2368` | Build.completion PASS | fixed |
| 24 | `:2402` | Complete.depth PASS | fixed |
| 25 | `:2444` | Vocab.identity PASS | fixed (F7 caveat) |
| 26 | `:2471` | Vocab.alias PASS | genuine |
| 27 | `:2489` | Ldgr.source_presence PASS | genuine |
| 28 | `:2513` | Dens.served N/A | fixed |
| 29 | `:2513` | Dens.served PASS | basis fixed; grading **contested** (OS-3, ≥1 of N), unchanged |
| 30, 36 | `:2520/:2529` | Build.exercised N/A | genuine |
| 31 | `:2523` | Build.history N/A — never run | genuine |
| 32 | `:2537` | Build.exercised PASS | fixed |
| 33 | `:2082` | Build.dep_liveness PASS | fixed (R45); OS-D residual unchanged |
| 34 | `:2543` | Build.dep_liveness N/A | genuine |
| 35 | `:2586` | `CLOSABLE` allowlist | genuine |
| 37 | `:2031` | Build.target PASS — ≥2 count tables | **proxy** (OS-A), unchanged |
| 38 | `:2036` | Build.target PASS — a partition of another asset's target | genuine (declaration) |

**Tally: 39 branches.** 20 genuine (#4, 6–10, 14–17, 20, 21, 26, 27, 30, 31, 34, 35, 36, 38) · **15 fixed** (#2, 3,
5, 11, 12, 13, 18, 22, 23, 24, 25, 28, 32, 33, 39) · **2 proxy** (#1, #37) · 2 contested (#19, #29's grading).

**Changes from W2-2's 38:**
- #2 and #3 moved from proxy to fixed. They were two of W2-2's four proxies, and this was the largest remaining
  proxy cluster: 110 of today's closable Idem verdicts pass through them.
- #39 is new; no branch was removed.
- R21 and R23 add no PASS/N/A branch: the radius is an annotation, and `Reach.fields` stays `NOT_GENERIC`.

## §4 — Proof 2: six-layer census, `a72cdf460` vs HEAD

**Method.**
- Base ran in `<scratch>/w2-3/wt_base` (detached at `a72cdf460`); HEAD ran in this tree (`ROOT` comes from `git
  rev-parse`, so each ran inside the tree it measures).
- Both used `--layer all --emit-gaps --out <scratch>`, each on its own copy of the real 830-line ledger, under
  `timeout 900`, read-only; rc=2 (FAILs measured) for both.
- HEAD was measured at `f032ecec5`, `ee2c7d7ee` and the final `8702ee331`: all three censuses are identical (0 verdict
  and 0 text changes; `census_diff_ee2c7d7ee_vs_8702ee331.txt`).

**Result** (`w2-3_evidence/census_diff_a72cdf460_vs_ee2c7d7ee.txt`, `diff_census.py`):
- **Verdicts:** 2,446 base and 2,446 HEAD, same keys.
- **58 verdict changes, all `Idem.pattern` PARTIAL → PASS** — exactly §0's 58, one per asset.
- **0 other verdict changes on any criterion or asset. 0 → FAIL, 0 → N/A.**

**Every favourable flip (58), with what it measured.**
- **L0 (26), in the asset's seeder (`brahmagyan/l0_*.py`), or in the writer for the four marked \*:**
  - own-table `INSERT … ON CONFLICT`: bg_class_lifetime_counts, bg_class_priors, bg_formula_constants, bg_ghatana,
    bg_kota_chakra_rings, bg_kp_sublord_division, bg_medical_mappings, bg_nakshatra_medical, bg_ontology,
    bg_phaladeepika_latta, bg_prashna_rules, bg_reference, bg_remedies, bg_rules, bg_sign_medical,
    bg_transit_engine, bg_transit_rules, bg_vastu_directions, bg_vedha_malefic_scale;
  - own-table delete-then-insert: bg_compendium_index\*, bg_concordance\*, bg_dasha_systems, bg_doshas,
    bg_gochara_arcs\*, bg_nakshatra, bg_yogas.
- **L1 (18):**
  - through `ga_writers/_idempotency.replace_prior_*` two hops down: ga_ayurdaya, ga_dashas, ga_panchanga,
    ga_positions, ga_sade_sati, ga_sensitive, ga_sensitive_degree, ga_strength, ga_structural, ga_tajaka,
    ga_vargas;
  - ga_nakshatra one hop down;
  - in the builder module: ga_condition, ga_medical, ga_prashna, ga_vastu, ga_vichara, ga_yoga.
- **L2 (12):** through `bodha_writers/_idempotency.replace_prior_*`: bo_arudha, bo_bimba, bo_grounding,
  bo_karanajala, bo_laksana, bo_nakshatra_semantic, bo_pramana_mapa, bo_samskara, bo_special_lagna, bo_sudarshana,
  bo_upaya, bo_vargottama_dhana.
- **L5 (2):** mi_bhara (`services/mi_bhara/db.py:replace_prior_skill_and_gof`, a loop over a literal table tuple);
  mi_sankalpa (`services/mi_sankalpa/db.py:delete_unresolved`).
- The independent checks are in §5.

**Text-only changes: 151.**
- 127 `Reach.fields`, one per asset: "not generic" → the R23 figures or "no target table …".
- 24 `Idem.pattern`:
  - 9 L0 upsert PASSes now name their own table instead of "ON CONFLICT present in the writer" (bg_cohort,
    bg_dignity_reference, bg_ephemeris, bg_muhurta_lattice, bg_parihara_rules, bg_sky_calendar, bg_texts,
    bg_vidhi_floors, bg_vidhi_primitives) — **all 9 of the old proxy PASSes hold on the stricter rule**;
  - 4 PASSes now list more own tables (bo_anveshana, bo_sangati — which gains a delegated
    `bodha_writers/_idempotency.py` citation — ph_rectification, mi_pariksha);
  - the 11 remaining PARTIALs carry their named reasons instead of "likely delegates" (§0);
  - ka_kshetra's FAIL text is unchanged.
- No other criterion's text changed.

## §5 — Proof 3: the simulated NEXT emit on the real ledger

**Method.** The real ledger (830 lines, md5 `7f2257a8…`, as of `a72cdf460`) was copied twice. `--emit-gaps` ran
with base code on one copy and HEAD code on the other (`emit_base.log`, `emit_final.log`; transitions in
`next_emit_transitions_final.txt`, `transitions.py`).

| run | per layer appended / present / closed / re-opened | total |
|---|---|---|
| base `a72cdf460` | L0 0/215/0/0 · L1 0/114/0/0 · L2 11/132/0/0 · L3 0/146/0/0 · L4 0/70/0/0 · L5 0/99/0/0 | 11 opened, **0 closed** |
| HEAD `ee2c7d7ee` | L0 0/189/**26**/0 · L1 0/96/**18**/0 · L2 11/120/**12**/0 · L3 0/146/0/0 · L4 0/70/0/0 · L5 0/97/**2**/0 | 11 opened, **58 closed**, 0 re-opened |
| HEAD re-emit (same copy) | (0,189,0,0) (0,96,0,0) (0,131,0,0) (0,146,0,0) (0,70,0,0) (0,97,0,0) | **byte-identical** |
| final HEAD `8702ee331`, fresh copy | identical per-layer figures; re-emit byte-identical (`emit_final_8702ee331.log`) | 11 opened, **the same 58 closed** |

- **The 58 CLOSED ids** are exactly the §4 favourable flips, all `Idem.pattern`. Each CLOSED row quotes its
  measurement: the own table, file:line and delegation chain.
- **No other criterion closes**, and nothing re-opens.
- **The 11 OPENed rows** are L2 `Complete.depth` (bo_chart_gestalt, bo_karanajala, bo_laksana, bo_laksana_rerank,
  bo_nakshatra_semantic, bo_pramana_mapa, bo_sangati, …). Base code opens the identical 11: live L2 data has moved
  since the first production emit, and W2-3 does not cause them.
- Of the real ledger's 70 OPEN `Idem.pattern` gaps, **12 stay OPEN**: ka_kshetra (FAIL) and the 11 named PARTIALs.

**Hand-verification against the writer source.** Method, as W2-2's reviewer did for ka_kshetra: for each closure,
read the cited statement in context, then the path from the writer's entry point to it, looking for any check that
holds or skips the replacement on a POPULATED chart. **17 of the 58 were checked.**

| gap | what I read | verdict |
|---|---|---|
| bg_rules | `l0_rules.py:1606–1624` `INSERT INTO sutravali_rules … ON CONFLICT (rule_id) DO NOTHING`; `rule_id = _make_rule_id(text_id, verse_ref, antecedent, prediction)` (:1402, content-derived); only raises are information_schema preflights (:1483–1500) | genuine (L0 upsert, §N.3) |
| bg_reference | all 11 counted tables `INSERT … ON CONFLICT … DO NOTHING` (`l0_reference.py:1316–1561`); the raise at :1420 fires on an EMPTY `brahma_ontology` (upstream), not on populated output | genuine |
| bg_dasha_systems | `seed_dasha_systems`: `DELETE FROM reference_dasha_systems`, `brahma_dasha_systems`, `brahma_ontology WHERE entity_class='dasha_system'` (:724–727), then inserts; only a dry-run return in front | genuine (full / class-scoped replacement) |
| bg_compendium_index | `DELETE FROM brahma_compendium_index` (:168) then both INSERT passes, after the desired state is fully built | genuine |
| bg_gochara_arcs | per substep `DELETE … WHERE substrate_version = %s AND body = %s` (:156), plus unknown-body cleanup (:149); dry-run return only | genuine |
| ga_positions | `run` → `build_ga_positions` → `_insert_chart_facts_rows` (:531) → `replace_prior_chart_facts` (`_idempotency.py:54–72`, receipt then DELETE by chart × category × ayanamsha); in front only a missing-birth-params raise and the FORENSIC gate | genuine |
| ga_condition | `DELETE FROM chart_facts … fact_category = ANY … ayanamsha_id = ANY` (:1196, after an authorization receipt) and `DELETE FROM ga_condition_composite WHERE chart_id AND ayanamsha_id` (:1647) | genuine |
| ga_dashas | `_upsert_rows` calls `replace_prior_chart_dashas` (:3040, chart × system × ayanamsha) before its COPY | genuine |
| ga_vargas | `replace_prior_chart_divisionals` via `_write_rows_batch`; the `_check_already_written` skips (:2942, :3061, :3084, :3130) count rows with `build_id_uuid = <this build>` — resume checks a new build never trips | genuine (and the reason for R241's build-scope rule) |
| ga_yoga | `_delete_prior_yoga_firings` (chart × ayanamsha, :2773) reached at :2854; the earlier returns fire on EMPTY chart_facts / catalog (upstream) | genuine (empty-upstream caveat, §2.4 #7) |
| ga_prashna | `DELETE FROM ga_prashna_lagna` / `ga_prashna_judgment WHERE chart_id AND ayanamsha_id` (:302/:306) before inserts; the return in front is "not a prashna chart" | genuine |
| bo_upaya | `replace_prior_rm_resonances` / `_prescriptions` (`bodha_writers/_idempotency.py:425–455`) called per ayanamsha before `_batch_insert`; `@l2_producer` has no populated refusal (C-KSHETRA review §3, re-read) | genuine |
| bo_bimba | `replace_prior_cgm_nodes(conn, chart_id, aya, SNAPSHOT_TYPE)` (writer :658; helper :336–350, owned node types only); the raise at :638 is on EMPTY `bodha_msr_signals` | genuine |
| bo_pramana_mapa | `replace_prior_scorecard` (:908; helper :523 `DELETE … WHERE chart_id`); raises at :675/:787/:793 are empty-upstream and detector-failure halts | genuine |
| bo_samskara | `replace_prior_signal_embeddings` (:310; helper :508); the returns at :231/:236 are dry-run and no-signals | genuine (empty-upstream caveat) |
| mi_bhara | `replace_prior_skill_and_gof` (`services/mi_bhara/db.py:205–220`): a loop over the literal `("kala_field_skill", "kala_field_gof")`, DELETE per chart × weights_version × snapshot; called at writer :254 | genuine (versioned natural key, as §N.3 permits) |
| mi_sankalpa | `delete_unresolved` (`db.py:201–215`, unresolved/derived rows only) then `reinsert_rows` (writer :161–162), after reading every such row first | genuine — attested and outcome-linked rows are human data and are kept by design |

**Ruling on the next emit.**
- **On today's data, every one of the 58 closures I read is earned.** The detector's claim was confirmed
  independently for 17. The remaining 41 follow the same verified shapes (the shared helpers `ga_writers/_idempotency`
  and `bodha_writers/_idempotency`, and the L0 seeders), but I did not read each one.
- **Recommendation to the executor:** keep the hand-verify discipline for the 41 not individually read, or accept
  them on the shared-helper evidence. That is the executor's call.
- **Unchanged by W2-3:** W2-2's remaining reasons the emit is "not trustworthy by construction" — #1 contract proxy,
  OS-3 Dens.served grading, OS-D lit provenance.

## §6 — Proof 4: suite, fingerprint, drift, ledgers

| run | result |
|---|---|
| offline, `a72cdf460` (base worktree) | 278 passed · 20 skipped · **2 failed** (300) — `suite_base_a72cdf460_offline.txt` |
| offline, HEAD `8702ee331` | 323 passed · 23 skipped · **2 failed** (348; +48 = `test_w2_3_deeper_detectors.py`) |
| live, `ee2c7d7ee`, full suite, one invocation (529.5 s) | 343 passed · **2 failed** · 0 skipped — `suite_head_live_tail.txt` |
| live, `8702ee331`, full suite, one invocation (540.0 s) | **346 passed · 2 failed** · 0 skipped (348) — `suite_final_live_8702ee331_tail.txt` |

- **Pre-existing failures:** the 2 failures are the same pair at every run and at the base:
  `test_drift_detector_h35_h38.py::test_f163_current_row_flagged_predecessor_row_is_not` and
  `::test_h35_critical_when_canonical_artifacts_missing`.
- **Manifest:** `manifest_fingerprint.py --check` → `entries: 141 (declared 141) · fingerprint declared
  1847709eec2bad52 · observed 1847709eec2bad52 · MATCH`. None of the four touched code/test files is
  manifest-registered.
- **Drift:** `drift_detector.py` (pgenv, `timeout 600`) → **exit 3**, 1 finding: 0 CRITICAL, 0 HIGH, 0 MEDIUM,
  1 LOW `a3_category_not_yet_populated` — the pre-existing LOW. The report went to the gitignored `drift_reports/`
  (copied to evidence).
- **Ledgers:** `asset_gaps.jsonl` `7f2257a8d4f0d6a7a21c0648b4101f85` (830 lines) and `asset_certs.jsonl`
  `514cbdfcf3fa71b3e382f84a978bf369` (1 line), identical at session start, after both parallel emit runs, after the
  final-head runs, and at report time.

## §7 — Honest limits

1. **Static analysis.** `Idem.pattern` reads the code; it does not prove that a past build ran it. The
   delegation-following resolves names syntactically, and the hop limit is 2. §2.4 lists the seven hold shapes it
   still misses.
2. **N/A is never produced for "writes nothing".** Eight assets (services and service-like writers) will read
   PARTIAL for as long as they write no own row. An N/A rule for them — "declared service, fully-read scope, no
   write" — is a policy decision, and it would be a static absence claim.
3. **The PARTIAL→PASS flips are genuine only in the sense §5 checked.** A table replaced per (chart, category,
   ayanamsha) replaces what the writer writes this run, not rows of categories it stopped producing. That is the
   §N.3 natural-key scope, not a full-table replacement.
4. **R21's radius** counts declared `depends_on` edges only. Undeclared readers (Edges.undeclared_dependency) are
   invisible to it.
5. **R23 is a lower bound on width and an upper bound on depth wherever the SQL is not literal.** SQL reached
   through an imported helper, a view, a SQL function or a service is not followed, so a table served that way reads
   dark. It is reported, not graded, for exactly this reason.
6. **Hand-verification covers 17 of 58 closures** (§5).
7. The first R23 "without" run errored at collection instead of failing on behaviour. It was fixed and re-run
   (`R23-without-v2`); both entries are in the log.

## §8 — Out-of-scope findings (listed, not fixed)

- **OS-1 (R240, unchanged):** ka_gochara's registry declares `kala_gochara_windows`; the writer replaces only
  `_v2`. This is the data-plane owner's action, and until it is taken `ka_gochara-Idem.pattern` stays OPEN.
- **OS-2 (ledger schema):** `asset_gaps.jsonl`'s `_schema` line does not list the new optional fields
  `blocking_radius`, `severity_weight` and `blocking_radius_note`. The ledger was not touched; amending the `_doc`
  is the executor's call.
- **OS-3 (dark tables, R23):** 26 target tables are read by no capability module's SQL:
  - bg_synthetic_cohort, classical_attributions, bg_dignity_reference, bg_gochara_arcs,
    bg_gochara_citation_resolution, bg_kota_chakra_rings, bg_kp_sublord_division, reference_nakshatra,
    bg_phaladeepika_latta, reference_planets, bg_sarvatobhadra_grid, bg_transit_rules, bg_vedha_malefic_scale,
    vidhi_floor_items, vidhi_primitives;
  - ga_prashna_judgment, bodha_cdlm_chart_summary, bodha_grounding_matches, bodha_signal_embeddings,
    gochara_resonance_map, **kala_field**;
  - kala_field_skill, mimamsa_event_provenance, mimamsa_intervention_ledger, mimamsa_preferences,
    mimamsa_export_log.

  Some are surely served through services, SQL functions or other layers' code (kala_field). Each is a question
  for its serving owner, not a verified gap.
- **OS-4 (R23):** 17 capability queries select through a run-time column list (`SELECT ${cols}`). A declared
  column list — for example beside `density_contract` — would make field reachability measurable rather than
  bounded.
- **OS-5:** the L3 service writers (ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana) write
  `asset_registry.service_health` / `selftest_detail` from inside the writer. The frozen contract forbids
  `asset_throughput` writes, not registry writes, so this is not a violation. It is noted because the self-test
  health is those assets' only "output".
- **OS-6:** mi_vistara is `asset_kind='data'` in the registry, but its writer's docstring says "Service asset: no
  build-time rows". This is a registry/writer kind disagreement.
- **OS-7:** the next emit opens 11 L2 `Complete.depth` gaps under base and HEAD code alike. Live L2 data has
  changed since the first production emit.

## §9 — Evidence index (`nikasha_test/wave2/w2-3_evidence/`)

- **Mutations:** `mutation_runs.log` (every without-run and all 32 mutations), `mutation_specs/*.json`, `mut.py`,
  `without.py`.
- **Idem.pattern, all 127 live:** `idem_all.py`, `idem_before.json` (at `a72cdf460`), `idem_r20b.json` (after R20
  and its follow-up; R241's follow-up measured identical).
- **Proof 2:** `census_diff_a72cdf460_vs_ee2c7d7ee.txt`, `diff_census.py`.
- **Proof 3:** `emit_base.log`, `emit_final.log` (`ee2c7d7ee`), `emit_final_8702ee331.log`,
  `next_emit_transitions_final.txt`, `transitions.py`, `census_diff_ee2c7d7ee_vs_8702ee331.txt`.
- **Proof 4:** `suite_base_a72cdf460_offline.txt`, `suite_head_offline.txt`, `suite_head_live_tail.txt`,
  `suite_final_live_8702ee331_tail.txt`, `manifest_check.txt`, `drift.out`, `DRIFT_REPORT_adhoc_20260927T170256Z.md`.
- **Base worktree:** `<scratch>/w2-3/wt_base` (`a72cdf460`) was clean when removed with `git worktree remove`; `git
  worktree list` no longer shows it.

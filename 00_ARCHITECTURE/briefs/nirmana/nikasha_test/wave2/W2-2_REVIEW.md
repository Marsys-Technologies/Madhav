---
artifact: NIKASHA_WAVE2_W2-2_REVIEW
packet: W2-2 — latest row, right registration, attempt-linked timing
version: "1.0"
reviewer: Opus (fresh context, read-only packet reviewer; did not build any part of W2-2)
reviewed_on: 2026-09-27
base: 931dbc479
commits: [0166b096a R233, bf1ffbad0 R44, 0bf42192c R49, 1d2544f23 R45, ad0141bf7 D6-item-2, 311a13a40 R43,
  9968eceaf R46, 16a67ca41 R50, ccec0127f R51, 83f143be1 R53, eca58994d R54, 8f5e2fd29 R232, f327ad680 report]
verdict: ACCEPT_WITH_CORRECTIONS
second_emit_ruling: >
  NOT safe on today's data as the report states. 33 of the 34 closures a second emit would make are earned; the 34th,
  ka_kshetra-Idem.pattern, would close on a false measurement. ka_kshetra's writer does NOT delete-then-insert on a
  populated chart: it raises KshetraReplacementHeld (DP-SD-017 W0), and the canonical chart holds 8,570,075
  kala_field rows. The emit is safe once that one row is withheld. It is not safe by construction (agreed), for the
  report's three reasons plus a fourth: the builder's own hand-verification missed the guard, so "hand-verify every
  CLOSED row" must read the rebuild path, not only the presence of a DELETE. This ruling GATES the second production
  emit (C2). It does not gate W2-2 acceptance.
scratch: <scratchpad>/rev-w2-2/ (base + head censuses, ledger copies, mutation log, diff). Both temporary worktrees
  (rev-w2-2/wt_base at 931dbc479, rev-w2-2/wt_head at f327ad680) were removed after use.
---

# Nikaṣa wave 2 · W2-2 · packet review

## §1 — Verdict: ACCEPT_WITH_CORRECTIONS

Everything I re-ran reproduced:
- **Code and tests.** All 12 rows' code is correct for what each row claims. Mutation re-runs: 21 mutations across
  all 12 rows. 20 were killed by the named tests; the 21st is an equivalent mutant (§2).
- **Census (§4 of the report).** My own census diff, head vs 931dbc479, reproduces the report exactly: 71 verdict
  changes, 37 favourable flips, 500 text-only changes, and identical per-layer tallies.
- **Emit runs.** The emit dry run reproduces exactly (574 OPEN / 0 CLOSED / 209 present; the re-emit is
  byte-identical). So does the simulated second emit (34 CLOSED / 12 OPEN / 0 RE-OPENED, the same 46 gap ids).
- **Suites and checks.** Offline suites reproduce (base 214/11 skipped/2 failed; head 269/20/2). Live, minus the
  two long e2e tests: 287 passed, 2 failed (the same pre-existing drift-detector pair). Manifest MATCH; drift exit 3
  with 1 LOW.
- **Ledgers.** Unchanged throughout (`30365ff2…` / `514cbdfc…`).

The report is wrong on one load-bearing claim. It says ka_kshetra's `Idem.pattern` PASS is "true, but the census's
evidence does not measure it" (§4.3, OS-C). It then builds on that claim: "all 34 are … each hand-verified correct"
(§0, §5.2) and "on today's data … each correct" (§5.3). **The verdict is not true** (§4.1). The census's evidence is
a proxy, and so was the builder's hand-check: it found the DELETE loop but not the guard in front of it.

This is the exact defect class the packet exists to remove, and it reached the second-emit ruling. It does not
reject the packet, for two reasons:
- The defect lives in `idem_scan` (proxy #3), which is R20's territory (W2-3), not a W2-2 row.
- The W2-2 code (R43) is correct to recognise the writer. R43 only makes the pre-existing proxy reachable.

The corrections, each bound to the gate it blocks:

| # | correction | blocks |
|---|---|---|
| **C1** | Rewrite §0 item 2–3, §4.3 (Idem.pattern bullet), §5.2, §5.3 and OS-C. ka_kshetra's Idem.pattern PASS is **incorrect** as a §N.3 claim ("rebuild replaces"): the writer holds replacement on any populated chart (§4.1). The count becomes 33 of 34 earned closures, not 34. State the second-emit ruling as in this review's frontmatter. | the executor's fold of W2-2 (the report as recorded) |
| **C2** | The second production emit must not append the `ka_kshetra-Idem.pattern` CLOSED row. The executor withholds it by hand-disposition (the hand-verify discipline the report itself recommends), or keeps the emit off until R20 lands. R20's (W2-3) acceptance must name ka_kshetra: a held/guarded replacement grades non-closable (PARTIAL), and a counted DELETE must name the asset's target and be reachable on a populated rebuild. | the second production emit; R20 acceptance |
| **C3** | Report hygiene, no code change:<br>(a) OS-A: `fact_category_ownership` is **created and seeded by migration 410** (58 rows; `supabase/migrations/410_ga_structural_category_ownership.sql`), realigned by 418, then backfilled by 842/845. The report names only 842/845.<br>(b) OS-B: `target_owners()` is read **once** on L1 today (only ga_strength reaches the 1-table branch), not twice.<br>(c) R53-M3 ("own asset counted as owner → 1 failed"): the spec is not recorded, and the natural form of that mutation is an **equivalent mutant** (§2). Record the spec or drop the claim. | the executor's fold of W2-2 |

Nothing else blocks. The non-blocking recommendations are in §9.

## §2 — Mutation re-runs (reviewer's own harness, on a separate head worktree, scratch ledger dir)

Method: copy `asset_census.py`, apply one surgical single-occurrence replacement (the report's `sub.py`), run the
named tests, restore, confirm `git diff --quiet` against f327ad680, then run the offline suite (every restore read
**250 passed, 20 skipped, 21 deselected**, matching the report).

| row | mutation (report's spec unless noted) | result |
|---|---|---|
| R43 | constants unresolved (`if isinstance(a, ast.Name)…` → `if False:`) | **3 failed** (constant test, `mi_const-L5`, live every-writer test) |
| R43 | shim imports unfollowed (`for g in []:`) | **3 failed** (shim test, `ka_svc-L3`, live) |
| R45 | stale counts as live | **3 failed** (stale-here param, open-gap-no-close, live chart-scoped) |
| R45 | any chart's record used | **1 failed** (`lit only on another chart` → must FAIL) |
| R53 | M1 any kind waves through (`== "service"` → truthy kind) | **5 failed** |
| R53 | M2 unowned single table passes (`if own:` → `if True:`) | **1 failed** |
| R53 | M3 self counted as owner (reviewer's spec: drop `if a != r["asset_id"]`) | **survived, 7 passed — equivalent mutant.** `_grade_target_less` runs only when the asset's `target_table` is NULL, and `target_owners()` lists only assets with a non-NULL target, so the self-exclusion can never fire. The builder's M3 (72→69 chars, killing the `owners={}` case) must have been a different mutation. Its spec is not in the log (C3c). |
| R232 | M1 substring restored | **5 failed** (4 mention cases + the emit comment case) |
| R232 | M2 strings not blanked | **2 failed** (quoted string, template literal) |
| R232 | M3 comments not stripped (`_DENSITY_DECL.search(txt)`) | **3 failed** |
| R232 | M4 `?:` unrecognised | **1 failed** |
| R233 | raw `left(a.error,200)` | **2 failed** (both live C4 tests) |
| R44 | last-read row wins | **3 failed** |
| R44 | tie not flagged | **1 failed** |
| R49 | first error kept | **2 failed** (incl. live: ka_avadhi quotes the 2026-07-04 UndefinedColumn instead of 2026-09-10) |
| R50 | short lines padded and counted | **1 failed** |
| R51 | comments count as serving | **3 failed** |
| R51 | comment-only reads closable N/A | **1 failed** |
| R46 | view not counted | **4 failed** |
| D6.2 | link key ignored | **1 failed** |
| R54 | severity dropped | **2 failed** |

All four rows the report flags as most consequential (R43, R45, R53, R232) reproduce with the same failing tests.
The only divergence is R53-M3, explained above.

## §3 — Branch enumeration attack (38 branches)

**Completeness.** I listed every PASS/N/A-producing site in `asset_census.py` at 8f5e2fd29 myself (every `v=PASS`,
`v=NA`, `PASS if`/`NA if`, `return PASS`, the adopted-detector `DETECTOR_VERDICTS` path and `CLOSABLE`). The set is
exactly the report's 38: #1–#3 (:386/:402/:405), #4–#5 (:895/:905), #6–#10 (:989/:992/:994/:999/:1011), #11
(:1155, shared by contract and idem), #12–#13 (:1286/:1301), #14 (:1346), #15–#18 (:1409/:1417/:1425/:1427), #19
(:1436), #20–#21 (:1442), #22–#23 (:1475/:1534), #24–#27, #28–#29 (:1674), #30/#31/#36/#32 (:1681/:1684/:1690/:1698),
#33–#34 (:1263/:1704), #35 (:1738), #37–#38 (:1212/:1217). **No branch is missing.**

**Labels.** I agree with every label except one qualification on **#3**. The report calls it proxy (correct) but
says ka_kshetra's verdict is "true only by hand-check". It is not true (§4.1). Also, the census's match on ka_kshetra
is *both* the `build_substep_progress` DELETE *and* the bare f-string fragment `'DELETE FROM '`. I reproduced this by
running `_code_strings` on the resolved file. Removing the substep-progress DELETE would therefore not change the
verdict.

**Can a contested or 1094-gated branch close a real production gap today?** I mapped each against the production
ledger (263 lines, 262 open) and against the simulated post-first-emit ledger (858 open), the way W2-1's re-gate did:

| branch | open rows (prod / simulated) | HEAD verdicts on those rows | closes today? |
|---|---|---|---|
| #19 Build.dag PASS (contested) | 0 / 0 | — | **no**: no Build.dag gap is open anywhere |
| #29 Dens.served PASS ≥1-of-N (contested) | 24 / 59 | FAIL 23 + NO_DET 1 / FAIL 58 + NO_DET 1 | **no** |
| #6–#8 Earn N/A, #9 Earn PASS, #10 Cost PASS | Earn 42/129, Cost 40/127 | NO_DETECTOR on all (`duration_seconds` absent: 0 columns live) | **no** |

Once migration 1094 lands, #6–#8 could close up to 129 Earn rows through N/A. That is the D6 design. It needs its own
gate at 1094 and is out of this packet's scope, as the prompt says.

## §4 — Favourable-flip re-verification (37 flips; all 37 re-read, ka_kshetra and ga_structural in full)

### §4.1 ka_kshetra `Idem.pattern` NO_DETECTOR→PASS — **INCORRECT** (not "correct by accident": wrong)

What the census measured:
- It scans only `services/ka_kshetra/writer.py`, the resolved `@register` file (the shim `writers/ka_kshetra.py` is a
  one-line import).
- Its regex matches two code strings: `'DELETE FROM build_substep_progress WHERE chart_id = %s AND asset_id = %s'` and
  the f-string fragment `'DELETE FROM '`.
- It then writes "DELETE FROM present (delete-then-insert)". That is the §N.3 claim that **a rebuild replaces the
  chart's rows**.

What the writer does:
- `services/ka_kshetra/writer.py:19–24` (header): "`prepare:replace` … FAILS CLOSED before DELETE when any
  writer-owned output already exists … Only an output-empty chart may enter the existing per-chart delete-then-insert
  path."
- `plan_substeps` (:400–412) always puts `prepare:replace` first on a fresh or replanned build.
- `_run_prepare_replace` (:520–569) calls `_populated_owned_table()` (:571–598) across every `_OWNED_TABLES` entry.
  If any is populated it **raises `KshetraReplacementHeld`** (:543–551). Only an empty slice reaches
  `_delete_prior_rows` (:563 → :2431–2434), which then deletes nothing.

Live (read-only):
- `kala_field` holds **8,570,075** rows for 482012f1 (and 2,412,882 for 1c826d5a).
- ka_kshetra's record on 482012f1 is `error`; its last 8 started attempts are crash/orphan errors of 2026-09-11.

So a rebuild of the canonical chart today raises; it does not replace. The writer never accretes, which is safe, but
§N.3's "rebuild REPLACES" is **deliberately not met** under DP-SD-017 W0. The honest grade is non-closable (PARTIAL:
held replacement, a documented deviation), not PASS.

The report's hand-check (§4.3) read the `_OWNED_TABLES` loop and concluded "it does clear `kala_field` per chart". It
did not read the guard that makes the loop unreachable on any populated chart. That is proxy evidence, twice: a
right-looking answer for the wrong reason, which is the §N.8 class this packet exists to remove. Consequence: one of
the 34 simulated second-emit closures (`ka_kshetra-Idem.pattern`, "CLOSED by measurement: DELETE FROM present
(delete-then-insert)") is unearned → C1, C2.

### §4.2 ga_structural `Build.target` N/A→PASS — **both halves confirmed**, with one attribution correction

- **The verdict is supported.** The registry has `target_table` NULL, `asset_kind='data'`, `has_writer=true`. Its
  writer (`writers/ga_structural.py` → `ga_writers/ga_structural_writer.py:4881`) INSERTs only into `chart_facts`.
  `chart_facts` is the declared target of 7 active assets (ga_ayurdaya, ga_nakshatra, ga_panchanga, ga_positions,
  ga_sade_sati, ga_sensitive, ga_sensitive_degree; live query). #38's partition rule would PASS it on true grounds.
- **The evidence text is false.** The census reaches PASS through #37 (≥2 count tables): its `count_sql` is `FROM
  chart_facts cf JOIN fact_category_ownership fco …`, and the text says it "produces" `fact_category_ownership`. No
  sidecar `.py` writes that table; the only reference is a comment in `mi_adhilepa.py:90`.
  - It is created and seeded by **migration 410** (58 ga_structural rows), realigned by 418, and backfilled by
    842/845. Live: 67 rows, 64 owned by ga_structural.
  - The report cites only 842/845 (C3a). The substance of OS-A stands.

### §4.3 The other 35 flips

| group | n | re-verification | ruling |
|---|---|---|---|
| Build.registered FAIL→PASS | 13 | All 10 L3 shims contain `from services.<a>.writer import …`. The factory classes are built at module level (`ka_dasha_kala/writer.py:175 KaDashaKalaWriter = _build_writer_class()`; `ka_tulana :135`; `ka_gochara_resonance :558`). `ASSET_ID` is assigned exactly once in mi_bhara (:58 → `@register(ASSET_ID)` :87) and mi_sankalpa (:48 → :76). `ph_rectification/__init__.py:246 @register("ph_rectification")`. Registered-id counts reproduce: L3 11→22, L4 8→9, L5 12→14. | **genuine**, 13/13 |
| Build.contract NO_DET→PASS | 13 | My sweep covers **whole service packages and delegated modules**, wider than the builder's resolved-file scan: services/{10 ka_*}, services/{mi_bhara, mi_sankalpa, ph_rectification}, `services/mimamsa/lel_calibration.py`, `services/gochara_grammar/sarvatobhadra.py`. It looks for `.commit()`, `.rollback()`, `.close()`, `autocommit`, `psycopg.connect(`, `with conn:`/`with ctx.db_conn:`, raw `COMMIT`/`ROLLBACK` SQL, and `asset_throughput` writes. The only hits are a temp-file handle close (`ka_kshetra/stage4_field.py:434`) and a nested SAVEPOINT/`ROLLBACK TO SAVEPOINT` (`ka_kshetra/stage0_kinematics.py:722–730`), both conformant inside the orchestrator's transaction. In depth: ka_kshetra, mi_bhara, ph_rectification, ka_vedha_gochara, ka_dasha_kala. | **verdicts hold**, 13/13 |
| Idem.pattern NO_DET→PASS | 7 of 8 | Each runs a chart-scoped `DELETE FROM <its registry target> WHERE chart_id = %s` on the rebuild path before insert: `gochara_resonance_map` (:417/:543), `kala_kota_chakra` (:101/:306), `kala_moorti_nirnaya` (:87/:308), `kala_sudarshana_varsha` (:54/:184), `kala_tithi_pravesha` (:79/:291), `kala_vedha_gochara` (:131/:572), `phala_rectification(_best)` (`ph_rectification/__init__.py:288/291`). All registry targets match (live). Their early returns only preserve the prior partition on an honest-empty candidate. | **genuine**, 7/7 |
| Build.target N/A→PASS: bg_prashna_rules | 1 | `brahmagyan/l0_prashna.py` INSERTs into all five counted tables (:808/:837/:866/:893/:915). | **genuine** |
| Build.target N/A→PASS: ga_strength | 1 | `ga_writers/ga_strength_writer.py:1630 INSERT INTO chart_facts`; the 7 declaring owners are confirmed live. | **genuine** |

**Can a contract violation hide from the proxy among the 8 cited assets?** Yes, in principle. The AST check inspects
only the registered class body, and only `<x>.db_conn.commit()/close()`. It would miss:
- an aliased `conn = ctx.db_conn; conn.commit()`;
- `rollback()`;
- a psycopg `with conn:` block, which commits on exit;
- a writer that opens its own connection;
- any violation in a helper module.

None of the 13 writers, nor the modules they delegate to, uses any of these shapes (sweep above). The PASSes stand on
today's code, not by construction.

**Summary:** 36 of 37 favourable flips are correct. **ka_kshetra `Idem.pattern` is incorrect.** ga_structural's
verdict is correct and its text is false.

## §5 — Second-emit attack

- **Reproduction.** On a fresh copy of the production ledger I emitted my own base censuses with **931dbc479's
  module** (base worktree), then my own head censuses with f327ad680's.
  - First step: (6,209,0,0)(113,0,0,0)(136,0,0,0)(166,0,0,0)(72,0,0,0)(103,0,0,0). That is 596 appended and 0 closed,
    W2-1's figure exactly.
  - Second step: L3 27, L4 3 and L5 4 closed → **34 CLOSED**, 12 OPEN, 0 RE-OPENED.
  - All 34 closed gap ids are in `second_emit_transitions.txt`, and every id there is reproduced (0 missing either
    way). Criteria: Build.contract 13, Build.registered 13, Idem.pattern 8. 0 dep_liveness and 0 Dens.served rows
    close.
- **bg_sarvatobhadra_grid (OS-D).** Confirmed live, and worse than stated:
  - `asset_throughput` holds one GLOBAL row, `state='lit'`, `rows_written=0`, `last_built_at` 2026-08-09.
  - `build_run_assets` holds **0 rows ever** (0 started).
  - The table has **0 rows**, and the registry has **`has_writer=false`**, so no writer could have lit it.
- **ka_vedha_gochara's chain.** It declares 6 dependencies (ga_positions, bg_ephemeris, bg_transit_rules,
  bg_sarvatobhadra_grid, bg_vedha_malefic_scale, bg_phaladeepika_latta). All 6 read `lit` at 482012f1-or-global, so
  dep_liveness PASSes at both commits. The writer consults `bg_sarvatobhadra_grid` first (`writer.py:115, :204,
  :350`; ADJUDICATION-11) and falls back when it is empty.
  - The PASS certifies a dependency that is lit and empty with no provenance.
  - It is not among the 34 closures: that row was PASS at both commits and never open. It shows dep_liveness cannot
    be trusted by construction.
- **Ruling.** See the frontmatter. R45 and R232 do discharge C2 and F-S1: 0 dep_liveness and 0 Dens.served rows close,
  and both mutations that would re-open those paths are killed (§2). But the report's "each hand-verified correct"
  fails on ka_kshetra (§4.1).
  - **33/34 are earned.** The emit may run with `ka_kshetra-Idem.pattern` withheld (C2).
  - Keep the hand-verify discipline for Build.contract, Idem.pattern, Dens.served, Build.dep_liveness and
    Build.target (#37) until R20, OS-3 and OS-D are decided, and require that a hand-verify read the rebuild path,
    not only the DELETE.

## §6 — The four carried problems, ruled

| problem | accurately scoped? | ruling |
|---|---|---|
| **ga_structural evidence text + #37 join loophole (OS-A)** | Yes on substance. The migration attribution is incomplete (C3a). Does it generalise? No. Only 3 assets reach Build.target PASS without a declared target (all R53 flips), and every other Build.target PASS text is `target_table=<x>`, a declaration claim that names no producer. I sampled 3 declared-target PASSes against their writers: mi_bhara → `kala_field_skill` (`services/mi_bhara/db.py:296`), ka_avadhi → `kala_avadhi` (`writers/ka_avadhi.py:146`), bo_samvada → the `vw_chart_digest` view it creates (`bo_samvada.py:4`). All consistent. | **Carry, non-blocking.** 0 Build.target gaps are open in production or in the simulated ledger, so #37 can close nothing today. Fix before any Build.target gap can open (§9 R-4). |
| **`target_owners()` re-read per call (OS-B)** | The code defect is real: `owners.setdefault("map", target_owners())` evaluates its argument on every invocation, contradicting the comment "at most once per layer". The live count is **1 read on L1, not 2** (C3b). A second failing read could ERROR an asset despite a cached map, but 0 live instances. | **Cosmetic, carry** (one-line fix). |
| **ka_kshetra proxy evidence (OS-C)** | **Mis-scoped.** It is not "evidence doesn't name the target, verdict true". The verdict is false (§4.1). | **Blocks the second production emit (C2)**, and corrects the report (C1). |
| **`lit` provenance gap (OS-D)** | Accurate, and confirmed worse (`has_writer=false`, 0 attempts ever). | **Carry.** 0 dep_liveness rows close today, so it does not block W2-2. Any future CLOSED dep_liveness row must be hand-verified against provenance until OS-D is decided. |

## §7 — The removed `@LIVE` R232 test

**Ruling: removal was correct, and it leaves no gap that blocks acceptance.**
- The test pinned equality between the new rule and the **old, defective substring rule** on today's source. That
  uses the thing being replaced as an oracle, and it would fail on any future harmless comment. Its "without the
  change" failure was an `AttributeError`, not a behavioural failure. It read no database yet was DB-gated.
- The behaviour is covered by 7 `capability_scan` cases plus the 2 parametrised `measure()`+`emit_gaps()` ledger-copy
  cases. All 4 R232 mutations are killed (§2).
- I re-ran the kept measurement (`r232_live.py`): **155 modules / 45 mention / 45 declare / 0 change.** I also found
  that all 45 live matches have the shape `density_contract: {` (an object-literal value). None is a type annotation,
  `null`, or a ternary branch, which are the disclosed over-count shapes (§7 item 2 of the report).
- **Recommended, non-blocking (R-1):** an offline, not DB-gated source test that every `_DENSITY_DECL` match in the
  six capability directories is followed by `{`. It guards the one *dangerous* (closable) direction of R232's
  syntactic detector and fails the day a type-only or `null` declaration appears. Home: with OS-3 in W2-3.

## §8 — Scope and regression

- **Commits.** `git log 931dbc479..HEAD` shows exactly the 13 commits. `git diff --shortstat 931dbc479 8f5e2fd29`:
  **5 files, +1443 −94**, all under `platform/scripts/governance/` (asset_census.py plus 4 test files). f327ad680
  adds only `wave2/W2-2_REPORT.md` and `wave2/w2-2_evidence/**`.
- **Untouchables.** No writer, orchestrator, migration, sealed tier, register/plan/decisions/STATE, catalog_provenance
  or provenance file is touched. No push.
- **Ledgers.** `asset_gaps.jsonl` `30365ff2238c75f5f62e622b70292da3` (263 lines) and `asset_certs.jsonl`
  `514cbdfcf3fa71b3e382f84a978bf369` (1 line) were unchanged at the start and after every census, emit and suite
  run, which all used scratch copies.
- **Suites.** Offline base: 214 passed, 11 skipped, 2 failed. Offline head: 269 passed, 20 skipped, 2 failed. The 2
  failures at both commits are `test_drift_detector_h35_h38.py::test_f163_…` and `::test_h35_…`, so they are
  **pre-existing**. Live head, minus the two long e2e tests: 287 passed, 2 failed (the same pair).
- **Checks.** `manifest_fingerprint --check`: 141/141, `0c723f4a1b6a6ea5`, **MATCH**. `drift_detector` (run in the
  temporary worktree, so no report landed in the repo): **exit 3**, 1 LOW `a3_category_not_yet_populated` (73
  categories).
- **Emit.** HEAD emit on a production copy: **574 OPEN / 0 CLOSED / 0 RE-OPENED**, 209 present. By criterion the
  counts match §5.1 exactly. The re-emit is byte-identical.
- **Census.** My runs were faster than the builder's (L0–L2 ≤62 s, L3 ~181 s, sequential two-way). All rc=2.

## §9 — Remaining findings and the gate each blocks

| id | finding | gate |
|---|---|---|
| C1 | ka_kshetra Idem.pattern: the report's "verdict true / 34 each correct / safe on today's data" is false (§4.1) | W2-2 fold (report as recorded) |
| C2 | Withhold `ka_kshetra-Idem.pattern` CLOSED from the second production emit; name ka_kshetra's held-replacement shape in R20's acceptance | second production emit; R20 (W2-3) |
| C3 | (a) OS-A migration attribution (410/418/842/845); (b) OS-B is 1 read, not 2; (c) R53-M3 spec unrecorded, natural form equivalent | W2-2 fold |
| R-1 | Offline source guard for R232's over-count direction (§7) | none (W2-3 / OS-3) |
| R-2 | OS-B one-line fix (`if "map" not in owners: owners["map"] = target_owners()`) | none |
| R-3 | OS-D: dep_liveness should not count a `lit` row with no started attempt and zero rows as live. bg_sarvatobhadra_grid is the live case. | any emit that would CLOSE a dep_liveness row |
| R-4 | #37 should not count a JOIN-only lookup table as produced (route ga_structural through #38, or exclude lookups) | any emit once a Build.target gap is open (0 today) |
| R-5 | The contract proxy (#1) blind spots listed in §4.3 are not exercised by any live writer today. R20's sibling work should widen `contract_scan` to aliased connections, `rollback`, `with conn:` and delegated modules. | any emit that would CLOSE a Build.contract row on a newly recognised writer |

## §10 — Fact spot-check (read-only, live DB and source)

| # | report claim | reviewer measurement | result |
|---|---|---|---|
| 1 | ph_sodhana executed 41 = started 41 | 41 started of 95 rows | ✓ |
| 2 | 69 multi-line error rows across 32 assets | 69 / 32 | ✓ |
| 3 | 0 (asset, chart) keys have >1 throughput row | 0 | ✓ |
| 4 | 12 same-instant run pairs | 12 per-asset groups (24 attempts); 5 run-level `created_at` groups | ✓ (per-asset reading) |
| 5 | bo_samvada live 0 → 5 via vw_chart_digest | 5 for 482012f1 (15 whole view) | ✓ |
| 6 | disposition era starts 2026-09-04 | min created_at with `disposition='build'` = 2026-09-04 | ✓ |
| 7 | all 64 latest `build` attempts: ended_at = last_built_at | 64 / 64 (chart row, else global) | ✓ |
| 8 | registered ids L3 11→22, L4 8→9, L5 12→14 | identical from `registered_ids()` at both commits | ✓ |
| 9 | Dens.served: 20 of 40 PASSes partial | 40 PASS, 20 with declaring < modules | ✓ |
| 10 | ka_avadhi quotes the 2026-09-10 integrity failure | "latest error (2026-09-10): post-write integrity check…" | ✓ |
| 11 | bg_sarvatobhadra_grid lit, rows_written 0, no attempt, empty | confirmed; also `has_writer=false` | ✓ (understated) |
| 12 | R232: 155 / 45 / 45 / 0 | 155 / 45 / 45 / 0 | ✓ |
| 13 | diff 5 files +1443 −94 | identical | ✓ |
| 14 | §4.1 per-layer tallies, 71/37/500 | identical | ✓ |
| 15 | fact_category_ownership populated by migrations 842/845 | created and seeded by 410; 418/842/845 later | ✗ incomplete (C3a) |
| 16 | OS-B: "2 reads on L1 today" | 1 (only ga_strength reaches the 1-table branch) | ✗ (C3b) |
| 17 | ka_kshetra Idem.pattern "verdict is true" | false: `KshetraReplacementHeld` on any populated chart; 8.57M kala_field rows on 482012f1 | ✗ (C1) |
| 18 | R53-M3 "own asset counted as owner → 1 failed" | spec not recorded; the natural form is an equivalent mutant | unverifiable (C3c) |

**Not reproduced by this review (disclosed):**
- The two long live e2e tests (`test_live_e2e_one_simulated_query_timeout_…`,
  `test_live_e2e_depth_census_failure_…`); the report ran each separately.
- The first builder's without-the-change runs (I ran mutations only).
- D6.2's injected-duration simulation (62 linked / 31 unclassified / N/A by cause).

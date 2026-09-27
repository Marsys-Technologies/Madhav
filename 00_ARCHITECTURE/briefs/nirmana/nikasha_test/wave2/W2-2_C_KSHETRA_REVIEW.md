---
artifact: NIKASHA_WAVE2_W2-2_C_KSHETRA_REVIEW
packet: W2-2 — correction C-KSHETRA (+ C1/C3 report text) after W2-2_REVIEW.md (9f84ecf6a, ACCEPT_WITH_CORRECTIONS)
version: "1.0"
reviewer: Opus (fresh context, read-only independent reviewer; did not implement any part of W2-2 or its corrections)
reviewed_on: 2026-09-27
commits: [2e1c06d1b C-KSHETRA (asset_census.py + tests), 57e6465e2 report v1.1 (C1/C3), d5b35e274 evidence]
verdict: ACCEPT
scratch: <scratchpad>/rev-w2-2c/ (ledger copies, three census JSONs, CLI logs, mutation log, idem comparison, drift
  report copy). Four temporary detached worktrees (wt_head d5b35e274, wt_base 931dbc479, wt_prev 8f5e2fd29, wt_mut
  d5b35e274) were used and removed; each was clean when removed. Production ledgers unchanged throughout:
  asset_gaps.jsonl 30365ff2238c75f5f62e622b70292da3, asset_certs.jsonl 514cbdfcf3fa71b3e382f84a978bf369.
---

# Nikaṣa wave 2 · W2-2 · C-KSHETRA correction review

## §1 — Verdict: ACCEPT

The correction does what the gate review asked for, and every claim I re-ran reproduced exactly:
- **ka_kshetra `Idem.pattern` now reads FAIL.** The live text names the guard: `services/ka_kshetra/writer.py:545
  (raise KshetraReplacementHeld after the output-existence probe _populated_owned_table)`. Line 545 is the `raise
  KshetraReplacementHeld(` in `_run_prepare_replace`.
- **Mutations.** All five CK mutations re-run by me produce exactly the stated failure counts (3/3/8/1/2), and each
  reverts byte-identically.
- **Census.** Exactly 3 verdicts move, all `Idem.pattern`, none toward PASS or N/A. Both side-effect flips are honest
  (§3).
- **Checks.** drift_detector exits **3** with the single pre-existing LOW. The real CLI emit on ledger copies gives
  **577 appended / 0 closed** on a first emit, and **33 closed** on the simulated second emit, with ka_kshetra
  absent.

C2's code half is discharged. The second emit can no longer close `ka_kshetra-Idem.pattern` by measurement: I
verified this on a ledger copy through the real CLI. What stays open is only the R20 acceptance wording. §10 of the
report hands it to the executor, and §7 below adds three detector blind spots R20 should name. None of them blocks
the fold.

## §2 — The fix (live verdict, mutations re-run)

**Code read.** The diff touches `idem_scan` and `_measure_idem`, plus one call site in `measure()`. It adds
`_deleted_tables`, `_module_sequences`, `_literal_names`, `_docstring_ids`, `_call_name` and
`_populated_refusal_guard`.
- A DELETE now counts toward PASS only if it names one of the asset's own tables (`target_table` ∪ `count_sql`
  tables). The name can be literal, a resolved module constant, or a resolved `for`-loop sequence.
- The refusal guard is checked before the convention branch. It fires on this shape: a probe function (SQL `SELECT
  EXISTS (SELECT 1 FROM …` or `SELECT 1 FROM <t> WHERE chart_id`), then an `if` on the probe's populated polarity
  whose body raises, then a delete reached after that `if`.
- ka_kshetra's writer matches that shape exactly. `_populated_owned_table` holds the EXISTS probe (:571–598), and
  `_run_prepare_replace` raises at :545 before `_delete_prior_rows` (:563 → :2420).

**Live.** I ran the real `idem_scan` via `_measure_idem` over all 127 registry assets, old module (8f5e2fd29) against
new (HEAD), both with the live registry:
- 3 verdicts moved (ka_kshetra PASS→FAIL, bo_upaya PASS→PARTIAL, ka_gochara PASS→PARTIAL);
- 43 changes were text-only;
- the guard fired on 1 asset, ka_kshetra.

The full CLI census (§4) shows the same ka_kshetra FAIL text.

**Mutations** (my own harness, `mut.py`, run in a separate worktree; the C-KSHETRA test selection, 9 tests):

| mutation | my spec | stated | reproduced |
|---|---|---|---|
| CK-M1 guard reverted | `g = _populated_refusal_guard(tree)` → `g = None` | 3 failed (incl. real ka_kshetra) | **3 failed**: guarded fixture, emit-gap test, real ka_kshetra |
| CK-M2 any delete counts | on-target filter `if t in tset` → `if True` | 3 | **3 failed** (sibling / fragment / no-target params) |
| CK-M3 old rule restored | guard disabled + `DELETE FROM` anywhere → PASS "DELETE FROM present" | 8 of 9 | **8 failed, 1 passed** |
| CK-M4 polarity ignored | `populated = (True or …)` | 1 | **1 failed** (empty-polarity control) |
| CK-M5 loop tables unresolved | `names = []` in the `for` resolution | 2 | **2 failed** (no-guard and empty-polarity controls) |

Every mutation was reverted byte-identically (md5 checked), and the suite is green afterwards. Offline governance
suite at HEAD: **278 passed, 20 skipped, 2 failed**. The 2 failures are the pre-existing
`test_drift_detector_h35_h38.py` pair (`test_f163_…`, `test_h35_…`), as recorded in the review.

**One extra mutation of my own (call-site wiring).** I made `measure()` pass `[]` instead of the registry's tables.
It is killed by 3 R43 tests (`test_r43_the_resolved_writer_is_measured_not_no_detector[mi_const/ph_pkg/ka_svc]`).
This matters for §5: the loosened call-site text assertion is backed by a behavioural test.

## §3 — bo_upaya and ka_gochara rulings

### bo_upaya PASS→PARTIAL — **accurate under-statement; acceptable; no new row needed**

- **What its own file deletes.** `writers/bo_upaya.py:1933–1935` deletes only the three sibling rollups
  (`bodha_rm_chart_summary`, `_dosha_remedy_bundles`, `_pattern_remedies`).
- **What its counted tables are.** Registry: `target_table=bodha_rm_resonances`; the `count_sql` sums
  `bodha_rm_resonances` and `bodha_rm_remedy_prescriptions`.
- **How those are replaced.** They are replaced through `replace_prior_rm_prescriptions` /
  `replace_prior_rm_resonances`. `run()` imports them at :1905 and calls them per ayanamsha at :1945–1946, before
  `_batch_insert`. They live at `bodha_writers/_idempotency.py:425–455`. Each runs a real `DELETE FROM
  public.bodha_rm_<t> WHERE chart_id AND ayanamsha_id AND snapshot_type`, via `_delete` (:22–34: `SET LOCAL
  statement_timeout = 0` and then `execute`; no hidden no-op).
- **No guard in front.** The `@l2_producer` wrapper (`data_plane_contracts.py:557–625`) adds observation and
  generation bookkeeping and ContractError preconditions. It has no populated-output refusal.
- So the true grade is PASS, and the replacement is scoped to the natural key (chart × ayanamsha ×
  `snapshot_type='static_natal'`), which §N.3 permits.

**Why the PARTIAL is acceptable.**
- It is non-closable, which is the safe direction.
- Its text says "may delegate; verify there".
- It removes a PASS that W2-1 review A2 had already proven was earned only by coincidence: the sibling-table DELETEs
  matched, not the counted-table ones.

**Why no separate row is needed.** The fix belongs to R20 (delegation-following), and §10 of the report already names
bo_upaya in the R20 acceptance note. Carrying a separate row would duplicate R20.

**Consequence the executor should know.** A production first emit now opens a `bo_upaya-Idem.pattern` gap that is
known to be a detector under-statement. It should be dispositioned "detector under-states; closes on R20", not worked
as an owner defect.

### ka_gochara PASS→PARTIAL — **correct; a registry-data finding, not a detector defect**

- **Registry (live):** `target_table=kala_gochara_windows`, and `count_sql` = `SELECT COUNT(*) FROM
  kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'`.
- **Both tables exist (live `pg_class`):**
  - `kala_gochara_windows`: relkind r, 17,211 rows for 482012f1;
  - `kala_gochara_windows_v2`: relkind r, 1,001 rows for 482012f1.
- **Writer.** `writers/ka_gochara.py:120` has `TABLE = "kala_gochara_windows_v2"`. The header (:16–62) states that
  its only DELETE/SELECT/INSERT target is v2, `generation='2.0'`, and that it never names the protected v1 table.
- **What the detector sees.** It resolved `{TABLE}` to the v2 table and found that the declared table is never
  deleted. That is literally true: the writer does not replace the declared table's rows.
- **Classification.** This is exactly W2-1 F8 (`W2-1_REVIEW.md:340`, "a registry data finding… The owner, not the
  inspector"). The old PASS came from a bare f-string fragment, which is the proxy this correction removes. If the
  owner re-points the registry to v2, the scan resolves the constant and PASSes on true grounds.

### No other verdict moved

I ran my own full six-layer CLI census at 8f5e2fd29 and at HEAD, both live and minutes apart:
- **3 verdict changes**, exactly the three above;
- **43 text-only changes**, all `Idem.pattern` (L1 1, L2 9, L3 15, L4 9, L5 9);
- **0 changes on any other criterion.**

None moved toward PASS or N/A.

I also attacked the PASS direction. I swept all 43 delete-then-insert `Idem.pattern` PASS writers for held or refused
replacement shapes (`ReplacementHeld`, `Held(`, `SELECT EXISTS`, "already exists", "refuse", "FAILS CLOSED"). The only
hits are three unrelated comments in `ka_sangam.py` about scan refusal. No other live writer has ka_kshetra's shape.

## §4 — Drift + CLI emit results

**drift_detector** (`timeout 600 python3 platform/scripts/governance/drift_detector.py`, pgenv sourced, run in a
temporary worktree so no report landed in the repo): **exit 3**. 1 finding: 0 CRITICAL, 0 HIGH, 0 MEDIUM, 1 LOW,
`a3_category_not_yet_populated`, the same pre-existing LOW the gate review recorded.

**Manifest:** `manifest_fingerprint.py --check`: declared = observed `0c723f4a1b6a6ea5`, **MATCH**. None of the 12
changed files is manifest-registered. The manifest's only `nikasha_test` entries are the campaign report, DECISIONS
and PHASE6_ANALYSIS.

**Real CLI.** The invocation is `asset_census.py --layer all --emit-gaps --out <file>`. `--help`-equivalent flags
read from `main()` are `--layer`, `--emit-gaps` and `--out`. The ledger is redirected with `NIKASHA_CONTROL_DIR`,
which is honoured at both commits.
- **Where to run it.** `ROOT` comes from `git rev-parse --show-toplevel`, so the CLI must run from inside the tree
  being measured. I ran each commit inside its own worktree.
- **Timeout.** Used `timeout 1200`, because a full six-layer run exceeds 300 s.
- **Exit code.** Every run returned rc=2 (FAILs present), as expected.

| run | ledger copy | per-layer appended / present / closed / reopened | total |
|---|---|---|---|
| HEAD first emit | fresh prod copy | L0 6/209/0/0 · L1 114/0/0/0 · L2 143/0/0/0 · L3 145/0/0/0 · L4 70/0/0/0 · L5 99/0/0/0 | **577 appended, 0 closed** ✓ |
| HEAD re-emit | same copy | 0 appended everywhere; md5 `1b28bac8…` before = after | **byte-identical** ✓ |
| 931dbc479 base emit | second prod copy | 6/209 · 113 · 136 · 166 · 72 · 103 | 596 appended (W2-1 figure) ✓ |
| HEAD second emit | same second copy | L0 0/215/0 · L1 1/113/0 · L2 7/136/0 · L3 5/140/**26** · L4 1/69/**3** · L5 0/99/**4** | **33 closed**, 14 opened, 0 re-opened ✓ |

**The 33 closed ids** are exactly the v1.0 simulation's 34 minus `ka_kshetra-Idem.pattern`:
- by criterion: Build.contract 13, Build.registered 13, Idem.pattern 7;
- 0 in my set that are not in v1.0;
- the 7 Idem closures are the seven the gate review verified as genuine (§4.3 of the review).

**The 14 opened ids** are the v1.0 twelve (10 dep_liveness, 2 Dens.served) plus `bo_upaya-Idem.pattern` and
`ka_gochara-Idem.pattern`. This matches `second_emit_transitions_ck.txt` exactly.

## §5 — Test-update legitimacy and the withdrawn R53-M3 claim

| change | ruling |
|---|---|
| `test_a3…::test_idem_scan_exception_degrades…`: `_boom(asset_id, files, convention)` → `(…, targets=())` | **Legitimate.** A pure arity adaptation, needed because `_measure_idem` now passes 4 arguments. The assertion (ERRORED, never layer-abort) is unchanged. |
| `test_a3…::test_measure_calls_the_extracted_guarded_helpers`: exact-line assertion → the same line's prefix ending `r["has_writer"],` | **Legitimate, marginally looser as text.** It still proves `measure()` routes Idem.pattern through the guarded `_measure_idem`. The new `targets` argument is pinned behaviourally: my wiring mutation (`[]` passed) is killed by 3 R43 tests (§2). |
| R43 fixture registry row `_reg_row(aid, None, …)` → `_reg_row(aid, "t_x", …)` | **Legitimate.** The fixture writers already ran `DELETE FROM t_x` (test file :493, :518, pre-existing). The change declares the table the writer really deletes, so the tightened rule can recognise it. The test still asserts the same three verdicts, and still fails without R43. |
| R53-M3 claim withdrawn (C3c) | **Legitimate.** I re-ran the natural form myself: I dropped `if a != r["asset_id"]` at `asset_census.py:1368`, and all 7 R53 tests passed (it survives, live). This agrees with the gate review's equivalent-mutant finding. The report no longer claims a kill it cannot show. |

## §6 — Scope

- `git diff --name-only 9f84ecf6a HEAD`: 12 files, +580 −52.
- **Code** (2e1c06d1b): `platform/scripts/governance/asset_census.py`, plus
  `__tests__/test_w2_2_latest_row_registration_timing.py` and `__tests__/test_a3_fault_isolation_and_population.py`.
- **Report and evidence** (57e6465e2, d5b35e274): `nikasha_test/wave2/W2-2_REPORT.md` and 8 files under
  `wave2/w2-2_evidence/`.
- **Not touched:** no writer, orchestrator, migration, registry, ledger, manifest or STATE file.
- **Ledgers:** production ledger md5s were unchanged at start and end.
- **Report text:** C1 and C3 read correctly: §0 line 82, §5.2 line 558, §5.3 line 588, OS-A (410/418/842/845), OS-B
  (1 read), and C3c line 272.

## §7 — Remaining findings (none blocks W2-2's fold)

| id | finding | gate |
|---|---|---|
| RC-1 | **PASS-direction blind spots of `_populated_refusal_guard`**. It only recognises a `raise` in an `if` on the populated polarity of an EXISTS / `SELECT 1 … WHERE chart_id` probe, inside the scanned file. It would miss:<br>(a) a hold that `return`s or skips instead of raising;<br>(b) a probe written as `count(*) > 0`, or via an ORM or helper;<br>(c) a guard in a delegated module;<br>(d) `if not empty:` or walrus polarity.<br>0 live instances (§3 sweep), so today's PASSes stand, but not by construction. | R20 (W2-3) acceptance: name these shapes beside ka_kshetra |
| RC-2 | The guard is module-scoped, not scoped to the rebuild path. Any function in a scanned file with probe → raise → delete forces FAIL (the safe direction). Separately, `probe = sorted(probes)[0]` can name the wrong probe when a file holds several (cosmetic; correct for ka_kshetra). | none (R20 hygiene) |
| RC-3 | The production first emit will open `bo_upaya-Idem.pattern` (a known under-statement) and `ka_gochara-Idem.pattern` (a registry finding, F8). Disposition them as "detector under-states — closes on R20 delegation-following" and "owner: registry target/count_sql to v2 (F8)" respectively, so neither is worked as a writer defect. | the executor's production emit / fold |
| RC-4 | Carried unchanged from the gate review (not re-litigated here): R-1…R-5 and the hand-verify discipline for Build.contract, Idem.pattern, Dens.served, Build.dep_liveness and Build.target(#37) closures until R20, OS-3 and OS-D are decided. The one change: C2's "withhold ka_kshetra-Idem.pattern" is now enforced by the detector, verified on a ledger copy. | as in W2-2_REVIEW §9 |

**Acceptance statement for the fold (quotable):**

> W2-2 is ACCEPTED. All 12 rows (R233, R44, R49, R45, D6 item 2, R43, R46, R50, R51, R53, R54, R232; commits
> 0166b096a…8f5e2fd29) were accepted on their code, tests and mutations by the gate review (W2-2_REVIEW.md,
> 9f84ecf6a). Its one wrong verdict, ka_kshetra `Idem.pattern` PASS on a rebuild the writer refuses
> (KshetraReplacementHeld, services/ka_kshetra/writer.py:545), is corrected by C-KSHETRA (2e1c06d1b). Idem.pattern
> now counts a DELETE only when it names the asset's own table, and it grades a rebuild refused on a populated
> chart as FAIL, naming the raise. An independent review (W2-2_C_KSHETRA_REVIEW.md) confirmed the following. The
> live verdict is FAIL. Five mutations are killed at the stated counts. Exactly three verdicts moved across the
> six-layer census, all Idem.pattern and none toward PASS or N/A: ka_kshetra→FAIL; bo_upaya→PARTIAL, an honest
> under-statement of a delegated replacement, closing on R20; ka_gochara→PARTIAL, the W2-1 F8 registry-target
> mismatch, owner's action. drift_detector exits 3 with the one pre-existing LOW. The manifest reads MATCH. The real
> CLI emit on ledger copies gives 577 appended / 0 closed on a first emit, byte-identical on re-emit, and 33 closed
> (all earned; ka_kshetra-Idem.pattern not among them) on the simulated second emit. The report v1.1
> (57e6465e2/d5b35e274) correctly records C1 and C3. The second production emit may run under the gate review's
> hand-verify discipline. R20's (W2-3) acceptance must cover three things: ka_kshetra's refused-rebuild shape (and
> its non-raise and delegated variants), delegation-following for bo_upaya, and treating ka_gochara's
> registry/table mismatch as registry data.

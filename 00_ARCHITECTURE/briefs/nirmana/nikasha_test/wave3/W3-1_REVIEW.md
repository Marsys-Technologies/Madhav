---
artifact: W3-1_REVIEW
canonical_id: W3-1_REVIEW
version: "1.0"
reviewer: independent reviewer (Claude Opus 5.5, fresh context, read-only, not the implementer)
reviewed_on: 2026-09-28
reviews: nikasha_test/wave3/W3-1_REPORT.md (v1.0, DRAFT_PENDING_REVIEW)
authority: NIKASHA_WAVE3_EXECUTION_PROMPT_v1_0.md §2–§5 · NIKASHA_CHANGE_REGISTER_v2_0.md v2.6
base_commit: c8cdc0242
head_commit: 0965538ef
commits: "22 — f7521f2ec 63608ad71 8290df39b 11b76578c 2289778be 51eb7436f 05ef67651 c903cff9b 2d83e32b4 95a5fdfc4 a1272b79c 64b7310bb 08f554e02 d198bb069 a6353ac23 7df67413a 7cec6241e 67d5d1aa2 ddfc8ea8b 02182bf2c 48efa19ea 0965538ef"
verdict: ACCEPT_WITH_CORRECTIONS
---

# Nikaṣa wave 3 — W3-1 independent review

## §1 — Verdict

**ACCEPT_WITH_CORRECTIONS.**

The part that could do real damage, the one production ledger write (R81), holds up. I checked it
byte by byte, re-ran it for idempotency, and replayed it from the pre-write file. It does what the
report says, and it is reproducible. The census delta is exactly the 15 claimed changes, all
attributable. Every mutation I ran was caught. Scope is clean: no sealed tier, writer, orchestrator,
register, plan, STATE, certs file or Lane B artefact was touched.

The corrections fall into three groups:
1. Report statements that are factually wrong. They must be fixed in the document before the
   executor folds it, because a document finding is never deferred.
2. One real defect in R15/R29. Its hand/machine discriminator will flag census-written rows,
   starting tomorrow.
3. Scope residuals that must be folded as PARTIAL, not CLOSED.

Each item names the gate it blocks (§10). Nothing here requires a second write to the real ledger.

## §2 — R81, the one real ledger write (the decisive check)

**Line count and md5.** Reproduced exactly.

| state | lines | md5 | source |
|---|---|---|---|
| pre-write | 830 | `7f2257a8d4f0d6a7a21c0648b4101f85` | `git show c8cdc0242:…` and `67d5d1aa2^` |
| post-write | 857 | `f6b1d3c5eeff7ec5d56d45448df69d80` | `67d5d1aa2`, HEAD, and the working file now |

Only one commit in `c8cdc0242..HEAD` touches `asset_gaps.jsonl`, and that commit is `67d5d1aa2`.
The working file still reads `f6b1d3c5…`, 857 lines, after every check in this review, including
the census runs and the emit dry run. All of those ran against scratch copies through
`NIKASHA_CONTROL_DIR` with `--out` redirected. `asset_certs.jsonl` is unchanged
(`514cbdfc…`, identical at base).

**Append-only, checked precisely** (script `rev-w3/verify_ledger.py`):
- **829 of the 830 pre-existing lines are byte-identical and in the same positions.** Nothing was
  deleted. No gap or opportunity data row was edited.
- **Line 1 (the `_schema` documentation row) was rewritten in place.** The original line-1 bytes
  no longer appear anywhere in the file. The only change is inside `_doc`: `, superseded_by
  (optional, R80)` was added to the field list, and a clause was appended at the end. The keys
  are unchanged.
- **The rewrite is disclosed.** Both the commit message and the report state it ("1 line (the
  `_schema` row) replaced in place").
- **There is precedent.** Commit `a72cdf460` edited the same line in place to add `kind`.
- **The old line is recoverable.** Its content survives verbatim in git and in
  `_r81_pre_migration_fixture.PRE_MIGRATION_SCHEMA_ROW`, which I checked equal to the pre-write
  line 1.
- **It is still not strictly append-only.** The wave prompt's proof asks that "the ledger stays
  append-only (no line deleted, ever)", and the `_schema` doc itself says "Append-only" with no
  carve-out. The docstring in `apply_r80_r81_ledger_migration.py` says append-only binds only
  gap/opportunity rows "per the _schema doc's own text". The doc contains no such text, so that
  justification is the builder's own reading, not a quotation. → **C4.**

**The 11 pairs, compared to T5_LEDGER_DRIFT.md §A** (script `rev-w3/verify_fold.py`):

| # | hand id | census id | survivor (live) | (a) census `measured:` folded verbatim | (b) supersession | hand change/owner/gate/detector carried |
|---|---|---|---|---|---|---|
| 1 | bg_ontology-G02 | bg_ontology-Earn.build_record | census id kept | ✓ verbatim | hand → survivor | ✓ |
| 2 | bg_ontology-G07 | bg_ontology-Vocab.alias | census id kept | ✓ | hand → survivor | ✓ |
| 3 | bg_ontology-G10 | bg_ontology-Dens.served | census id kept | ✓ | hand → survivor | ✓ |
| 4 | bg_ontology-G05 | bg_ontology-Carr.detector | new `bg_ontology-Carr.D1` | ✓ | hand + census → new | ✓ |
| 5 | bg_ephemeris-G03 | bg_ephemeris-Earn.build_record | census id kept | ✓ | hand → survivor | ✓ |
| 6 | bg_ephemeris-G05 | bg_ephemeris-Dens.served | census id kept | ✓ | hand → survivor | ✓ |
| 7 | bg_ephemeris-G02 | bg_ephemeris-Carr.detector | new `bg_ephemeris-Carr.D3` | ✓ | hand + census → new | ✓ |
| 8 | bg_panchanga-G01 (partial) | Earn.build_record, Cost.baseline | new `bg_panchanga-Earn.service_state` | **none folded, by design** | hand → new; census siblings untouched | ✓ |
| 9 | bg_panchanga-G02 | bg_panchanga-Carr.detector | new `bg_panchanga-Carr.D3` | ✓ | hand + census → new | ✓ |
| 10 | bg_rules-G03 | bg_rules-Carr.detector | new `bg_rules-Carr.D1` | ✓ | hand + census → new | ✓ |
| 11 | bg_rules-G06 | bg_rules-Complete.depth | new `bg_rules-Completeness.depth.dasha_link` | ✓ | hand + census → new | ✓ |

Three notes on how the brief's literal checks apply to this implementation:
- **(b), census row pointing at the hand id.** This was R81's pre-D4 text. It does not apply
  literally any more. The D4 re-scope (register v2.6, R81 status column) derives a
  `<asset>-<Gate>.<check>` survivor and supersedes the old ids onto it. Where the census id
  already has the derived form (pairs 1/2/3/5/6), the census id is the survivor and the hand
  G-id is the one superseded. The implementation matches D4.
- **(b), where `superseded_by` lives.** It sits on a newly appended copy of the old row, never on
  the historical line. `emit_gaps`'s `ever_superseded` scan reads it across the whole id history,
  so no rewrite is needed. That makes it append-only in fact.
- **(a), pair 8.** Pair 8 folds no measurement. D4 says G01 is "never folded onto a timing id".
  The two census rows measure a different criterion, and both stay live. This is defensible,
  but the report says "each carrying … folding in the other side's measurement". That is true
  for 10 of 11 pairs, not all 11.

**Structure.** 27 new rows: 11 content rows and 16 superseding rows. The arithmetic checks out:
5 same-id pairs × 1, plus 5 new-id pairs × 2, plus pair 8 × 1. There are no supersession
chains. Every row parses (857/857).

**Proof "zero live (asset, criterion) identities with more than one live row".** Measured: 0.

**Idempotency, re-run by me** (fresh scratch copies):
- `apply_r80_r81_ledger_migration.py --apply` against a copy of the post-write ledger: "0 new
  row(s)", schema already migrated. md5 stays `f6b1d3c5…`. A second `--apply` is also a no-op.
- **Replay** from the pre-write file (`c8cdc0242`) with `--apply`: 857 lines. The result equals
  the real post-write ledger byte for byte once the 27 new rows' `ts` values are normalised.
  The real write is therefore exactly the reviewed algorithm's output, not a hand edit.
- The frozen fixture `_r81_pre_migration_fixture.ROWS` (23 rows) matches the real pre-write rows
  exactly.

**One consequence the report does not name (F6, demonstrated on a copy).** Superseding a
*generic* census id silences that criterion for that asset permanently. I fed `emit_gaps` a
synthetic census on a ledger copy:
- `bg_rules` `Complete.depth` = FAIL on a *different* column (`source_ref` newly never-populated):
  the ledger records nothing. The gid is `ever_superseded`, and the skip is not even counted.
- `bg_rules` `Carr.detector` = PASS: nothing closes. `bg_rules-Carr.D1` stays OPEN with detector
  `NONE`.

So after R81, a new column-population regression in `bg_rules` is invisible to the ledger. It
still shows in the census JSON. The same applies to `Carr.detector` on the four Carr-superseded
assets. This is the designed effect of the D4 crosswalk, not a builder defect, but it is a
coverage loss the native should see. → F6.

## §3 — The 15 verdict changes, and the attack on R99's third case

**Six-layer census.** I ran it myself, read-only, against production with `--layer all`, at base
`c8cdc0242` (a temporary worktree, since removed) and at HEAD. Chart `482012f1`. Both runs exit
with code 2.

`c8cdc0242` differs from wave-2 close `31b3e1024` only by the wave-3 prompt file (`git diff
--stat`), so the builder's baseline and mine are equivalent.

**Result: exactly 15 verdict changes, identical to the report's list**, with nothing else moved in
any layer:
- **R60 (11), each `None → PASS`, except ka_gochara_resonance `None → PARTIAL` (539/1595):**
  bg_dignity_reference, bg_medical_mappings, bg_nakshatra_medical, bg_sign_medical,
  bg_transit_engine, bg_transit_rules, bg_vastu_directions, ga_medical, ga_vastu,
  ka_gochara_resonance, ka_vedha_gochara.
- **R99 (4), each `Build.completion` `PASS → PARTIAL`:** ga_prashna, mi_abhilekha, mi_seva,
  mi_vistara.

**R99 classification logic, read at the source.**
- The new branch is `elif live == 0 and r["has_writer"]` → PARTIAL.
- It is reached only after these earlier branches:
  - empty table with `target_floor ≠ 0` → FAIL (R52);
  - build state not completed → FAIL;
  - `rows_written`/live disagreement → FAIL.
- So R99 only ever moves a former PASS to PARTIAL. It never creates a PASS (§N.8 is satisfied),
  and it does not regress R52. The truncate-plant tests are still green, and the R52 test update
  (`a1272b79c`) splits by `has_writer` rather than weakening the assertion.

**ga_prashna → PARTIAL.** It is `has_writer=true`, `target_floor=0`, and has 0 rows for the
canonical chart. The label is produced correctly.

**bg_sarvatobhadra_grid → PASS.** It is `has_writer=false`, `target_floor=0`, and has no
registered writer (none found in `platform/`). It stays PASS. The label is produced correctly.

**Attack: the third case.** Can a writer-backed asset be empty because it is broken, and land in
the same PARTIAL bucket as a legitimately empty one? **Yes, and the verdict text flattens the two
cases.**

**1. ga_prashna is empty by design for this chart.** The writer (`ga_writers/ga_prashna_writer.py`
`compute_prashna_judgment`) returns 0 rows through two different paths:
- (i) there is no `prashna_charts` row for the chart. This is legitimately empty.
- (ii) a prashna chart exists but `chart_facts` has no `graha_position` rows. The writer's own log
  calls this a "build ordering issue", so it is broken.

Both paths finish as state=complete with `rows_written=0`, so the census sees them identically.

I measured production:
- `prashna_charts` has **0** rows for `482012f1`, so ga_prashna's emptiness on the canonical chart
  is case (i), by design.
- `prashna_charts` does hold 2 prashna charts (`1789595b…`, `b35046d8…`). Yet
  `ga_prashna_judgment` has **0 rows in total**, those charts have 0 `graha_position` facts, and
  ga_prashna has never been built for them (`asset_throughput` holds only 3 natal charts). So
  case (ii) is latent, not yet realised.

The distinction is measurable with a single query: `SELECT count(*) FROM prashna_charts WHERE
chart_id = <chart>`. The R99 text nonetheless says the case is "indistinguishable from a writer
that has never produced a row", and the report says `has_writer` is "the one existing registry
signal honest enough to distinguish the two". It is not. `has_writer` separates no-writer from
writer-backed. It cannot separate a legitimately empty writer-backed asset from a broken one.

**2. mi_abhilekha lands in the same bucket with a different cause.** Its Build.history reads
"26 error(s) and 9 abort(s)" and its latest error is "BLOCKED: upstream … mi_bhavisya did not
complete". It also fails Build.dep_liveness. So its emptiness is at least partly caused by an
upstream failure, yet it gets the same `Build.completion` PARTIAL with the same sentence as
ga_prashna.

Other checks (history, dep_liveness) do carry the difference for mi_abhilekha. For the ga_prashna
by-design case, nothing does.

**3. bg_sarvatobhadra_grid's PASS text invents a judgement.** The PASS text says "the signal honest
enough to read as by-design". The asset's own hand row `bg_sarvatobhadra_grid-G01` says the table
is empty because it is "blocked on an input, not on effort". The 0=0 consistency PASS is sound.
The "by-design" gloss is an invented judgement (§N.7 item 6).

**Conclusion.** R99 is conservative and safe to accept. It does not deliver the register's text:
"'empty by design' is a layer-instance claim with its own detector". That detector was
deliberately not built. → **C3**: R99 folds as PARTIAL, with the residual as a named row.

## §4 — R60

- `classical_citation` (singular) is now in the list, at `asset_census.py:2637`.
- **bg_nakshatra_medical**: `Ldgr.source_presence` goes from absent (`None`) at base to
  `PASS — classical_citation populated on 27/27 rows` at HEAD. This is a real check where there
  was none before.

**False-positive column attack.** I read the actual content of the `classical_citation` column in
every newly checked table (11 assets, target tables resolved from `asset_registry`). All 11 are
`text` and hold genuine citation strings, for example `BPHS Ch.3`, `Phaladipika Adh. XXVI, Sloka 3
— phaladeepika:PG322:C1`, `Vastu Shastra (Mayamata Ch.6)`. None holds an empty string or a
placeholder (`n/a|none|null|unknown|tbd|-`).

The only substring hazard would be a longer column name containing `classical_citation`. The list
matches exact names (`c in tcols`), so none is possible.

Observations, not defects:
- bg_nakshatra_medical has a single distinct citation string across all 27 rows. It is a blanket
  citation, but it passes a check that only claims presence.
- For chart-scoped tables (ga_medical 135/135, ga_vastu 120/120), the `IS NOT NULL` count runs
  over the whole table across charts, not the canonical chart. This is a pre-existing scope
  property of the Ldgr check, now applied to two more assets (F10).

Mutation: removing the singular name turns the R60 suite 1 failed / 1 passed.

## §5 — Criterion registry (R78) and lookup (R79), mutation and collision

**Registry size.** 26 entries: **21** auto-measured and 5 `NONE`. The report says "all 20
criteria". Every key equals `f"{gate}.{check}"`. Every criterion that `measure()` assigns is
registered, and none is missing (the only regex hit outside the registry is the literal
`"Gate.check"` inside a comment).

**Unregistered criteria are not silently matched.** `lookup_criterion` returns `None` for:
- `Bogus.crit`;
- `carr.D1` (case differs);
- `"Carr.D1 "` (trailing space);
- `Carr` (gate only);
- the family aliases `Vocab.rule1.alias` and `Dens.density_contract`, so there is no runtime alias
  table.

The specific and generic forms stay distinct: `bg_rules-Carr.D1` and `bg_rules-Carr.detector`.

**Collision attack.**
- I searched assets × all 26 criteria × scopes, including adversarial asset ids containing `-` or
  `@` and a scope equal to a criterion string. Zero collisions. This holds because registered
  criteria contain neither separator.
- Real ledger asset ids contain no `-` or `@`.
- One degenerate equivalence exists: `scope=None` and `scope=""` derive the same id. This is
  benign, but should be documented.

**Mutations, run by me in a scratch HEAD worktree (restored and removed):**
- `registered_criterion` returning a default entry for unknown criteria → R78/R79 suites
  3 failed / 9 passed.
- A runtime alias table injected into `lookup_criterion` → R79 2 failed / 4 passed.

Both regressions are caught.

**Registry coverage of the live ledger.** 42 criterion strings used by live hand rows are not
registered. Examples: `Earn.count_sql_scope`, `Completeness.universe_blocked`,
`Vocab.future_gate`, `Synergy.*`, `Architecture.*`. D4 says hand gap rows use a registered
criterion. That is only true for the 11 folded pairs. It is consistent with the wave prompt's
narrower R81 scope, but it means R78/R81's D4 re-scope ("all 30 hand gap rows across the five
pilots") is not complete. → **C5**.

## §6 — R218, the planner test

**Harness re-run.** I ran the CLI (`r218_planner_p_need_report.ts`, reading the committed
`capability_knowledge.snapshot.json`). I also ran a probe that compiles the snapshot the way the
vitest test does (`compileCapabilityKnowledge(getCatalog())`). Both give **17/24, per-need rows
identical to report §4**.

That includes all five failing SCUs:
- P01 and P18 → `assess_career`;
- P05 → `assess_marriage`;
- P07 and P23 → `compose_large_n`;
- P13 → `graha_portrait`;
- P21 → `call_priority_ranking`.

I inspected more than the five P-needs required.

**The characterisation of the failures is wrong.**
- **Count.** The report says "the same 3 stub capabilities account for all 7 FAILs" and then
  lists **5** capabilities.
- **Editorial flag.** It says all 7 resolve to "`editorial=false` registry-derived routing stubs".
  I measured all five SCUs as **`editorial: true`**, in both the committed snapshot and the
  freshly compiled one.
- **Actual cause.** Lane B's `producer_provenance.derived.json` gives it:
  - `assess_career`, `assess_marriage`, `compose_large_n` and `graha_portrait` carry
    `NO_DETECTOR — no_contract: no availability_contracts requirement and no reviewed_output
    claim`. They are composite orchestrators (for example, assess_career "Orchestrates
    query_domain_reading …"). Their producers sit one composition hop away, and the provenance
    derivation does not traverse that hop.
  - `call_priority_ranking` carries `no_relation_in_range`. It is a service wrapper
    (`ka_tulana`) with no table in the resolved source range.

These are real, reviewed, served capabilities with a provenance-traversal gap, not "unreviewed
stubs". The honest worklist is "producer provenance through composition and service edges", not
"review 3 stubs". → **C1**.

**The PASS criterion is weak.** Several PASSes are semantically wrong resolutions. The PASS signal
largely measures whether a few catch-all SCUs have producers:
- P02 "What gives this life direction or meaning?" → `query_vastu_directions` (a lexical match on
  "direction");
- P22 "Let me read and understand the texts themselves." → `finance.prosperity_assessment`;
- P10, P15 and P24 → `finance.prosperity_assessment`;
- P16 → `bodha.mechanism.network`.

Report §6 honestly discloses that the criterion is the harness's own interpretation, so this is
F8, not a defect.

**Two smaller points on the test:**
- The live test asserts `summary.failed > 0`. The suite will turn red the day the provenance gap
  is fixed and all 24 pass. That encodes today's defect as an invariant (F8).
- P16's text is a faithful paraphrase that merges T1's two quoted phrasings. It is not verbatim,
  though the harness header claims verbatim (F9).

**Should 17/24 block anything?** No. Per §3/§4.4 of the wave prompt, R218 is a report that the
native reviews, not a gate on this packet. It is correctly informational.

## §7 — Doc/tracker spot-checks and sealed-tier scope

**Spot-checked against current file content:**

**R63 (T4).** All four "eight gates" occurrences now read "nine gates": lines 13, 211, 214, 499.
Line 13 describes T3 §5.2. T3 is sealed, and I confirmed its §5.2 was already reopened to nine
gates by decision 17 (T3 changelog line 37), so the new frontmatter text is true of T3.

**R64 (T4).** The heading at :241 and the Build-row cross-reference at :232 now say "nine checks".
Report out-of-scope finding #1 is **real**: :245 still reads `measured_by: six static checks …`,
and :268 reads "All nine checks run read-only". The v2.0 changelog line 34 also still says "Six
static checks".

**R66/R65-tracker.** `asset_elevation_tracker.py:43` reads "Nine, not thirty-three". The Build
gate description now reads "nine static checks, all read-only …". This is consistent with T4
§4.2's nine-row table.

**R69 (L0 v3.0).** The four "0/320" occurrences read 0/360 (:146, :466, :617, :735). **Residual:**
:526 still reads "5. **Briefs and gates** — 40 briefs, **320 gates**". This is the same
self-contradiction under a different string. It is not in R69's literal "0/320" match, and the
report did not name it. → F7.

**R77 (5 pilot briefs).** Each brief's §4 heading now reads "nine gates", and each has a measured
Build row: ontology FAIL, ephemeris FAIL, panchanga PASS, rules PASS, sarvatobhadra PARTIAL.
panchanga's "six of eight" was recomputed to "six of nine". The Build verdicts agree with my HEAD
census (sarvatobhadra `Build.count_integrity` PARTIAL: `count_sql=yes,
integrity_check_sql=no`).

**Sealed-tier scope.** I checked `git diff --name-only c8cdc0242 HEAD` and `git show --stat` for
every one of the 22 commits.

**All 35 touched files are within scope:**
- 7 non-sealed docs: T4 (tier 4), the L0 v3.0 instance, and the five L0 pilot briefs;
- the tracker;
- the ledger (one commit only);
- `asset_census.py`;
- 4 new governance scripts;
- 18 test and fixture files;
- 2 R218 TypeScript files;
- the report.

**None of the three sealed tiers is touched:**
- `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md` (T1);
- `briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md` (T2);
- `briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` (T3).

**No other forbidden path is touched:** writers, the orchestrator, `editorial.ts` and
`compiler.ts`, the register, plan, STATE and DECISIONS files, `asset_certs.jsonl`,
`catalog_provenance.py`, and `nikasha_test/provenance/**`. I checked each with `git diff --quiet`.

The R65-T3 and R68-T3 halves were correctly left alone.

## §8 — The drift detector's exit 2

I ran `drift_detector.py` myself, against a HEAD worktree and a base worktree, with no DB
credentials in that shell (hence the LOWs).

| run | exit | findings |
|---|---|---|
| base `c8cdc0242` | **3** | 2 LOW: `schema_db_unreachable`, `a3_schema_db_unreachable` |
| HEAD | **2** | the same 2 LOW, plus 2 HIGH `fingerprint_mismatch` |

**The two HIGHs are purely stale fingerprints from this packet's own document edits.** In each
case the declared value is the exact sha256 of the file at base, and the observed value is the
exact sha256 at HEAD:
- `ASSET_ELEVATION_TEMPLATE` (`…/ASSET_ELEVATION_TEMPLATE_v2_0.md`): declared `4927436c…` =
  sha256 at base; observed `ff911384…` = sha256 at HEAD.
- `MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY` (`…/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md`):
  declared `2233d00a…` = sha256 at base; observed `43338be7…` = sha256 at HEAD.

**Exit 2 is masking nothing else.** Rotating these two rows at fold time will return the detector
to base behaviour: exit 3 on DB-unreachable LOWs, or 0 with a reachable DB.
`manifest_fingerprint.py --check` returns MATCH at both revisions (`1812a4ede55e0b69`).

**Report correction.** The report says the ASSET_ELEVATION_TEMPLATE finding is "the SAME finding
T5_LEDGER_DRIFT.md already documented as expected/pre-existing … still unrotated". **That is
false.** T5 documented declared `bb341cc1…`. By base, the row had already been rotated to
`4927436c…`, and it **matched**. Both HIGHs are new in this wave, with the same benign cause. → C1.

## §9 — Scope and regression

**Governance suite, run by me:**
- HEAD: **421 collected = 395 passed + 24 skipped + 2 failed**.
- Base worktree: **351 = 325 + 24 + 2**, which gives +70 new tests.
- **The 2 failures are the same pair at both revisions:**
  `test_drift_detector_h35_h38.py::test_f163_current_row_flagged_predecessor_row_is_not` and
  `::test_h35_critical_when_canonical_artifacts_missing`. Both pre-exist at base and are unrelated.

**The report's §5.3 emit_gaps proof, reproduced on a fresh scratch copy**
(`asset_census.py --layer L0 --emit-gaps`, run twice):
- First run: 0 appended, 184 already present, 26 closed, 0 re-opened. All 26 closures are
  `Idem.pattern`, owner `asset_census`. None touches `Ldgr.source_presence` or `Build.completion`.
- Second run: 0 / 0 / 0.
- The real ledger md5 was unchanged throughout.

**Mutation re-runs, in a scratch HEAD worktree (all restored; the worktree was clean before
removal):**

| row | mutation | result |
|---|---|---|
| R60 | singular name removed | 1F/1P |
| R99 | branch disabled | 2F/44P (R99 and R52 suites) |
| R79 | default entry | 3F |
| R79 | runtime alias | 2F |
| R81 | census-side `superseded_by` omitted | 2F/16P |

Every regression is caught.

**Touched-file scope.** Beyond the named files, the packet adds four new governance modules:
`ledger_r81_migration.py`, `apply_r80_r81_ledger_migration.py`, `hand_row_provenance.py` and
`r218_planner_p_need_report.ts`, plus the R218 module under `retrieval/registry/knowledge/`. All
of them are new tooling that §3 of the wave prompt explicitly calls for, and none is a writer, the
orchestrator, or `editorial.ts`/`compiler.ts`.

## §10 — Remaining findings, each bound to the gate it blocks

**C1 — Report factual corrections (document findings, fixed in the document).**
- **Blocks:** the executor's fold of W3-1 into register, plan and STATE. The fold must not
  inherit these statements.
- **Fix in `W3-1_REPORT.md`:**
  - (a) R218: "3 … `editorial=false` … stubs" → 5 `editorial=true` composite/service
    capabilities. The FAIL cause is Lane B provenance `no_contract` (4) and
    `no_relation_in_range` (1).
  - (b) §5.5: the ASSET_ELEVATION_TEMPLATE mismatch is **new this wave**, not "pre-existing …
    still unrotated". It matched at base.
  - (c) Out-of-scope finding #3: bg_sarvatobhadra_grid's missing `integrity_check_sql` is **not a
    new, unregistered finding**. `bg_sarvatobhadra_grid-Build.count_integrity` ("count_sql=yes,
    integrity_check_sql=no") has been an OPEN ledger row since 2026-09-26 (pre-write line 183).
  - (d) R78: "all 20 criteria" → 21.
  - (e) R81: "each … folding in the other side's measurement" → 10 of 11. Pair 8 folds none, by
    D4 design.
  - (f) R99: remove the claim that `has_writer` distinguishes legitimately-empty from broken
    (see §3).

**C2 — R15/R29 hand/machine discriminator flags census-written rows. Real defect, demonstrated.**
- **The mechanism:**
  - `is_hand_written()` is `owner != "asset_census"`.
  - `emit_gaps` carries the prior row's `owner` forward onto its own CLOSED and RE-OPENED
    transition rows, by design.
  - It writes no `census_run_id` on them.
  - R81 made five census-derived ids hand-owned: bg_ontology and bg_ephemeris `Earn.build_record`
    and `Dens.served`, plus `bg_ontology-Vocab.alias`.
- **The demonstration.** On a ledger copy with a clock after the cutoff, a census PASS on
  `bg_ontology-Dens.served` appended a machine-written CLOSED row with `owner="layer packet"`.
  `missing_census_run_id()` then returned `['bg_ontology-Dens.served']`, a machine row falsely
  flagged. From 2026-09-29, the first census `--emit-gaps` that closes or re-opens any
  hand-annotated census id will turn the real-ledger packet-proof test in
  `test_r15_r29_hand_row_census_run_id.py` red.
- **The fix.** Discriminate on `detector` beginning with `asset_census.py`. This is my candidate,
  and it keeps the existing R15/R29 suite 8/8 green. Alternatively, have `emit_gaps` stamp
  `census_run_id=census["generated"]` on every row it writes. Either way, add a test for the
  carried-owner transition row.
- **Blocks:** R15/R29 closure in the register, which must stay OPEN or IN_PROGRESS until fixed.
  It must land before the first post-cutoff `--emit-gaps` run.
- **Also note.** The rule is enforced only by the test suite. Nothing in `emit_gaps`, the tracker
  or CI calls `missing_census_run_id()`. "Enforced" in the commit title means "tested against the
  current file".

**C3 — R99 residual.**
- Fold R99 as **PARTIAL**, not CLOSED. The "empty by design as a layer-instance claim with its own
  detector" half of the register text was not built.
- Register a follow-up covering:
  - a per-asset by-design detector (for ga_prashna, the `prashna_charts` existence query);
  - ga_prashna's latent case (ii), 2 prashna charts with 0 positions and never built;
  - a correction to bg_sarvatobhadra_grid's "by-design" gloss, which contradicts its own G01
    "blocked on an input".
- **Blocks:** R99's register status at fold. It does not block acceptance, because the change is
  conservative and never creates a PASS.

**C4 — Line 1 `_schema` rewritten in place.**
- No re-write is required. The fold must record explicitly, in the register row for R80/R81 or as
  a decision line, that line 1 was replaced. It must also record either that the `_schema`
  documentation row is a mutable header exempt from append-only (precedent `a72cdf460`), or that
  future schema changes append a new `_schema` row instead.
- Correct the apply-script docstring's claim that the `_schema` doc itself scopes append-only to
  gap/opportunity rows. It does not.
- **Blocks:** the executor's R80/R81 fold.

**C5 — R81 scope.**
- Fold R81 as **PARTIAL (11 of D4's 30 hand rows)**. The register's D4 re-scope covers all 30,
  and 42 live hand criteria remain unregistered (§5).
- The report's §6 discloses this honestly. The register status must match.
- **Blocks:** R81's register status at fold.

**F6 — Superseded generic census ids are permanently muted for that asset** (§2, demonstrated).
Examples are `bg_rules-Complete.depth` and `*-Carr.detector`. Raise with the native as a D4
follow-up. **Blocks:** nothing in this packet. It belongs to the next ledger-identity work.

**F7 — L0 v3.0 :526 "40 briefs, 320 gates".** An unnamed residual of R69. Add it to the report's
out-of-scope list at C1 time. **Blocks:** nothing in this packet. It goes to the next doc-cleanup
row.

**F8 — R218 PASS criterion is semantically weak, and `failed > 0` is an anti-invariant.**
**Blocks:** nothing. Record it in R218's fold note so that 17/24 is not read as coverage.

**F9 — R218 P16 is paraphrased, not verbatim.** Cosmetic. **Blocks:** nothing.

**F10 — Ldgr presence on chart-scoped tables counts across all charts.** Pre-existing. **Blocks:**
nothing.

**Fingerprint rotation.** Rotating the two rows in §8 is the executor's job, done last. After
rotation, `drift_detector.py` must read exit 0 or 3.

## §11 — Fact spot-check (report claims, independently re-measured)

| # | claim | result |
|---|---|---|
| 1 | Ledger pre-write 830 lines, md5 `7f2257a8…` | ✓ reproduced |
| 2 | Ledger post-write 857 lines, md5 `f6b1d3c5…` | ✓ reproduced |
| 3 | Every pre-existing line preserved except line 1 | ✓ 829/830 byte-identical in place |
| 4 | 27 new rows = 11 content + 16 superseding | ✓ |
| 5 | `--apply` re-run is a live no-op | ✓ (on copies; the replay from pre-write equals the real post-write modulo `ts`) |
| 6 | 15 verdict changes, 11 R60 + 4 R99, none else | ✓ exact match, six layers |
| 7 | ga_prashna has 51 runs and 0 rows | ~ 0 rows ✓; my census reads 39 executed of 50 `build_run_assets` rows. The "51" comes from the register, not re-derived |
| 8 | emit dry run: 0 appended, 26 closed (all `Idem.pattern`), then idempotent | ✓ |
| 9 | Suite 421 = 395 + 24 skipped + 2 failed; baseline 351; 2 failures pre-existing | ✓ both revisions |
| 10 | `manifest_fingerprint --check` MATCH, 141 entries | ✓ MATCH |
| 11 | Drift exit 2 from 2 HIGH fingerprint mismatches | ✓, **but** the "ASSET_ELEVATION_TEMPLATE pre-existing, unrotated" part is ✗ (matched at base) |
| 12 | R218 17/24 with the per-need table as printed | ✓ identical |
| 13 | R218 failures are "3 … `editorial=false` stubs" | ✗ 5 capabilities, all `editorial=true` |
| 14 | "all 20 criteria `measure()` assigns" | ✗ 21 |
| 15 | bg_sarvatobhadra_grid missing `integrity_check_sql` is a "new finding, not previously registered" | ✗ OPEN ledger row since 2026-09-26 |
| 16 | R77 Build rows are real measurements | ✓ agree with my HEAD census (e.g. sarvatobhadra `count_integrity` PARTIAL) |
| 17 | T4 :245 still says "six static checks" (out-of-scope #1) | ✓ real |
| 18 | Registry includes Cost/Count/Complete/Reach, outside T4's nine gates (out-of-scope #2) | ✓ real |
| 19 | The R81 fixture was transcribed verbatim | ✓ 23/23 rows and the schema row equal the real pre-write rows |
| 20 | No sealed tier touched | ✓ |

Reviewer's scratch evidence (not committed): the scratchpad `rev-w3/` directory contains
`verify_ledger.py`, `verify_fold.py`, `diff_census.py`, `census_base.json`, `census_head.json`,
`drift_wt-*.json`, `r218.json` and `r218_probe.json`. Both temporary worktrees (`wt-base`,
`wt-head`) have been removed.

---
artifact: NIKASHA_WAVE1_LANE_B_REVIEW_4
reviewer: Opus gate review 4 (independent, fresh context, read-only; not the implementer)
reviewed_on: 2026-09-27
packet: Nikaṣa wave 1, Lane B — "the catalog names its producers" (R85 / D5 rev. 2.1), fourth submission
packet_commits: a171addc7 (R7 + N1 + N2 + main() comment), 61ff5a09d (B_REPORT.md v2.2, §2c)
base: df1846f10 (B_REVIEW3.md)
prior_reviews: B_REVIEW.md (REJECT), B_REVIEW2.md (REJECT narrow), B_REVIEW3.md (REJECT narrow)
verdict: REJECT (narrow)
---

# Lane B gate review 4

## §1 — Verdict: **REJECT (narrow)**

**Most of R7 is closed, by proofs that could have failed.** All four forgery probes behave as
claimed through the real `main(["--check"])`: (a) 75 fake `route_evidence_only` producers fail, with
75/75 named; (b) a fake `reviewed_output` on `get_dignity` fails; (c) a service-probe producer for an
unprobed asset fails; (d) the unmodified artifact passes. The mutation reproduces exactly: 3 failed,
27 passed, then 30/30. The matching key is **per-SCU**. Copying a real claim or a real probed asset
onto the wrong SCU is caught. N1 and the four R8 items are done as worded, and N2 is mostly done.
Nothing regressed, and no untouchable file was touched.

**It is not accepted, for three reasons. Each is narrow.**

1. **B1 — R7's third conjunct is neither done nor ruled on.** B_REVIEW3 §4 R7 required: "an SCU whose
   only producers are `route_evidence_only` is not counted as covered, **or** get an explicit native
   ruling that it should be, recorded in the report." Neither happened. The report (§7, §12 item 6)
   says the gap was left "per the gate's own framing … no such ruling has been sought". That misstates
   the gate, which offered two ways to close the item, not a third way of leaving it open. The gap is
   real on a copy of the artifact. I reduced `scu.kala.temporal_activation` to its single, catalogued
   `route_evidence_only` producer, and `--check` returned **PASS, exit 0**.
2. **B2 — the report says two false things about limit E.** §7 says "neither [E nor F] is a coverage
   bypass the way G was". §12 item 4 says "fixing E would need a DB round-trip". But E *is* a
   coverage bypass of exactly G2's size. Giving all 75 NO_DETECTOR SCUs a fake
   `derived_from_source_query` producer (`table: no_such_table_xyz`, `source_ref: nope.ts:1-2`)
   returns **PASS, exit 0, 182/182**. B_REVIEW3 already said "E is also a coverage bypass". Most of E
   can also be checked without the database. All 294 committed `derived_from_source_query` producers
   have a `source_ref` equal to a `kind: source_query` requirement's `source_ref` on the same SCU in
   the snapshot. That is the same snapshot-binding R7 used, and `--check` already loads the snapshot.
   Only confirming that a table exists needs the database. This is the same pattern R7 was rejected
   for: a stated reason that is false, covering a green signal.
3. **B3 — the report overclaims "every producer".** Both §2c and §12 item 4 say `--check` now
   cross-checks *every* exemption-tier producer. The docstring says every exemption producer "must be
   backed". The loop actually stops at the first valid producer per SCU. A fabricated
   `{zz_fake, reviewed_output, "x"}` appended to (or placed before) the producers of an already-covered
   SCU returns **PASS, exit 0**. The artifact is the file a follow-on lane will wire into
   `compiler.ts`, so a fabricated producer in it would pass the gate and reach the catalog.

**What would change the verdict to ACCEPT:**

- **B1:** either
  - make `validate_derived_artifact` refuse to count an SCU as covered when its only valid producers
    are `route_evidence_only`, with a real-entry-point test and a mutation that turns it red; or
  - record a native ruling in the report that such an SCU counts as covered.
- **B2:** either
  - bind each `derived_from_source_query` producer's `source_ref` to a `source_query` requirement on
    the same SCU in the snapshot. The committed artifact still passes, since all 294 are backed. Add
    a test that gives the 75 NO_DETECTOR SCUs fake source-query producers and expects failure, plus a
    mutation. Keep table-existence as the stated database-bound limit. Or
  - restate §7 and §12 item 4 truthfully: E is a coverage bypass of the same size as G, and the
    snapshot-checkable part is left unfixed by choice.

  I recommend the code fix. It is about five lines, and without it `--check PASS` does not prove
  coverage, which is what R85 is about.
- **B3:** either
  - validate every producer, and fail an SCU if any exemption-tier producer is unbacked; or
  - restate §2c, §12 item 4, the docstring and the `main()` comment to "at least one backed producer
    per SCU".
- **Test gap (with B1–B3):** add a test that copies a real `(asset_id, disposition)` claim onto a
  *different* SCU and expects failure. The per-SCU binding is correct today, but no test pins it; see
  §2.4.

## §2 — R7

### 2.1 Forgery probes (copies of the committed artifact → real `main(["--check"])`)

Driver: `scratchpad/rev4/probe.py`. Each case writes a modified copy of
`producer_provenance.derived.json` to scratch, points `cp.DERIVED_OUTPUT_PATH` at it, and calls
`cp.main(["--check"])`.

| case | edit | result | SCUs named in output |
|---|---|---|---|
| (d) | unmodified | **PASS exit 0** | — |
| (a) | all 75 NO_DETECTOR SCUs → `{zz_fake, route_evidence_only, "x"}` | **FAIL exit 1**, "75 problem(s)" | 75/75 |
| (b) | `get_dignity` (no claim keys in the snapshot: `None`) → `{zz_fake, reviewed_output, "x"}` | **FAIL exit 1** | 1/1 |
| (c) | first service-probe SCU → `{zz_never_probed, derived_from_service_probe, "svc:x"}` | **FAIL exit 1** | 1/1 |
| G4 | a real pair `(bo_yantra_mechanism, reviewed_output)` on its own SCU with `source_ref ""` | **FAIL exit 1** | 1/1 |

### 2.2 Bypass attempts on the new check

| case | edit | result |
|---|---|---|
| bypass1 | the real claim `(bo_yantra_mechanism, reviewed_output)`, declared on `scu.bodha.mechanism.network`, attached to NO_DETECTOR `scu.catalog.assess_career` | **FAIL exit 1** (caught) |
| bypass1b | the same real claim attached to all 75 NO_DETECTOR SCUs | **FAIL exit 1**, 75/75 named (caught) |
| bypass1c | the right asset on its own SCU with the wrong disposition (`reviewed_output` claimed as `route_evidence_only`) | **FAIL exit 1** (caught) |
| bypass2 | the genuinely probed asset `ka_graha_sancara` (probed on `scu.catalog.call_ephemeris_at_t`) as `derived_from_service_probe` on `scu.catalog.assess_career`, which has no service_probe requirement | **FAIL exit 1** (caught) |
| bypass3 | a fake `{zz_fake, reviewed_output, "x"}` **appended** to already-covered `scu.bodha.mechanism.network` | **PASS exit 0** (not caught; B3) |
| bypass3b | the same fake **placed first** | **PASS exit 0** (not caught; B3) |
| reo-only | `scu.kala.temporal_activation` reduced to only its catalogued `{ka_kalasutra, route_evidence_only}` | **PASS exit 0** (B1) |
| E×75 | all 75 NO_DETECTOR SCUs → `{zz_fake, derived_from_source_query, table no_such_table_xyz, source_ref nope.ts:1-2}` | **PASS exit 0, 182/182** (B2) |

**The matching key is per-SCU.** `validate_derived_artifact` builds
`claim_keys = claim_keys_by_scu.get(scu_id, set())` and `probe_assets = probe_assets_by_scu.get(scu_id,
set())`. The key is `(scu_id, asset_id, disposition)` for `reviewed_output` and `route_evidence_only`,
and `(scu_id, asset_id)` for `derived_from_service_probe`. No match at the asset level alone passes.
bypass1 and bypass2 show this.

### 2.3 Mutation (item 2)

In a scratch copy of the module and tests, I changed both snapshot-backing conditions
(`(asset_id, disposition) in claim_keys` and `asset_id in probe_assets`) back to `if source_ref:`.

```
FAILED test_check_fails_when_all_no_detector_scus_get_a_fake_route_evidence_only_producer
FAILED test_check_fails_when_get_dignity_is_given_a_fake_reviewed_output_producer
FAILED test_check_fails_on_a_service_probe_producer_for_an_unprobed_asset
3 failed, 27 passed
```

The baseline scratch copy and the real tree both give 30 passed. **Reproduced.**

### 2.4 Additional mutation: per-SCU → global (not in the packet)

I replaced the per-SCU lookup with the union over all SCUs
(`set().union(*claim_keys_by_scu.values())`, and the same for probes). Result: **30 passed**, and
nothing turns red. Every fabrication test uses asset ids that exist nowhere (`zz_fake`,
`zz_fake_probe`), so no test tells per-SCU binding apart from global binding. The code is correct,
but the property I was asked to verify has no test pinning it.

### 2.5 The 24 exemption producers (item 3)

I checked independently, without using the packet's helpers. I read the raw snapshot
(`producer_output_claims`, and `availability_contracts[].requirements[]` with `kind ==
"service_probe"`) and the raw artifact.

```
Counter({'reviewed_output': 14, 'derived_from_service_probe': 9, 'route_evidence_only': 1}) 24 unbacked []
all producers: derived_from_source_query 294, reviewed_output 14, derived_from_service_probe 9, route_evidence_only 1 (318)
snapshot claim pairs 15, probe pairs 9
```

**Reproduced: 14 + 1 + 9 = 24, all backed.**

## §3 — R8, N1, N2

| item | passage now | true of the code? |
|---|---|---|
| R8(a) | §7/§8/§12 now call G DONE; the false "per-SCU contract-awareness … does not currently have" justification is retracted | **Yes** for G. The replacement wording has its own problems (B2, B3). |
| R8(b) | §6: `--check` "reads TWO files — the committed artifact and the catalog snapshot" | **Yes** (`load_snapshot()` in the `--check` branch) |
| R8(c) | §6: "a fabricated exemption-tier producer … all now correctly fail" | **Partly.** True when the fabricated producer replaces an SCU's producers; false when it is added beside a valid one (bypass3). |
| R8(d) | `main()` comment scoped to malformed/shape-defective entries; names R7 as closing "THAT class of hand-edit" | Scoping: **yes**. "THAT class … fails too" is too broad for the same reason as R8(c) (bypass3). |
| PASS line | "snapshot-backed producer (a shape-valid derived_from_source_query, or an exemption-tier producer matching …)" | **Accurate.** It honestly calls the `derived_from_source_query` tier "shape-valid", not backed. |
| N1 | `assert "50-60" in stale[0]` restored (test diff, line ~667); passes | **Done** |
| N2 | closure prose interpolates `closure['before'/'after']['named_producers']` and `population_active_count` | **Mostly done.** I regenerated (§4.6), and CLOSURE_REPORT.md differs only in `generated_at`; `**14**`, `**94**` and `**127**` now come from `closure`. One literal remains in the same function (`catalog_provenance.py:1248`): "confirm the same 111/127 and the same 16 still-outside assets". It is historical prose, but it will read wrong next to computed numbers if the catalog changes. Non-blocking, like N2 itself. |

## §4 — Items 5–7

### 4.5 Nothing untouchable touched

```
git log --name-only df1846f10..HEAD
a77d50005 (Lane A)  test_a3_earn_cost_grading.py, asset_census.py
61ff5a09d (Lane B)  BUILD_DEPENDENCIES_READER_SCAN.md, CLOSURE_REPORT.md, producer_provenance.derived.json, B_REPORT.md
a171addc7 (Lane B)  CLOSURE_REPORT.md, producer_provenance.derived.json, test_catalog_provenance.py, catalog_provenance.py
8a57a3320 (Lane A)  A_REVIEW.md
git diff --name-only df1846f10 HEAD | grep -iE "migration|writer|orchestrator|editorial|compiler|ledger|register|sealed|STATE"  → (empty)
```

- Both Lane B commits touch only Lane B paths.
- Across the two commits, the provenance artifacts change only in `generated_at`, the N2 interpolation
  in CLOSURE_REPORT.md, and the reader scan's self-referential line numbers (L1310→L1314,
  L1516→L1582; the script grew).
- There is no production write and no migration. The script's DB access is SELECT-only, under
  `default_transaction_read_only = on`, which I verified.
- The working tree shows `asset_census.py` and `test_a3_fault_isolation_and_population.py` modified.
  Those are concurrent Lane A edits, not the packet's and not mine.
- **Reviewer incident, disclosed:** my first scratch regeneration missed one default-argument path.
  `write_derived_json` therefore wrote into the committed `producer_provenance.derived.json`. The
  diff was one line: `generated_at` only, which itself shows byte-identical re-derivation. I
  immediately restored the file with `git checkout --`. The tree has no Lane B modifications.

### 4.6 Regression

| check | result |
|---|---|
| re-derive (`--derive --closure --reader-scan` against production, read-only) | JSON **byte-identical apart from `generated_at`** (git diff showed only that line); CLOSURE_REPORT.md and BUILD_DEPENDENCIES_READER_SCAN.md differ only in `generated_at` |
| closure | `[B-2] necessary before=63, after=111 (of 127)` ✔ |
| named | `[B-1] 107/182` ✔; 75 NO_DETECTOR, classes `no_contract 28, relation_unowned_by_registry 28, no_relation_in_range 11, source_ref_out_of_range 7, derived_kind_no_source_query 1` ✔ |
| still outside | 16 = `no_unit_names_it` **14** + `table_unregistered` **2** ✔ |
| tests | **30 passed** ✔ |
| reader scan | **76** hits / **36** files ✔ |
| `manifest_fingerprint.py --check` | **MATCH f484f581767ad641** ✔ |
| `drift_detector.py` | **exit 3**, 1 finding, `a3_category_not_yet_populated` LOW ✔ |

**No regression.**

### 4.7 Stated limits E and F

Both are stated plainly in §7, §8 item 8 and §12 item 4. The question is whether either hides a green
signal.

- **E hides one, and the report says it doesn't.** See B2: 75 fabricated source-query producers give
  182/182 PASS. §7's "neither is a coverage bypass the way G was" is false. §12's "fixing E would need
  a DB round-trip" is false for the part that decides coverage. The part that is only about whether a
  table exists does need the database, and that part is a fair stated limit.
- **F: yes, a bogus reason containing a known class's trigger substring counts as valid.**
  `classify_no_detector_reason` matches message fragments, not class names:

  ```
  'zzz kind: derived zzz'                                            -> derived_kind_no_source_query
  'I made this up; no availability_contracts requirement exists lol' -> no_contract
  'xx source_ref_out_of_range xx'                                    -> source_ref_out_of_range
  'banana relation_unowned_by_registry banana'                       -> unclassified   (class name ≠ trigger text)
  ```

  Through the real `--check`:
  - F1: `get_dignity`'s real reason replaced with `"zzz kind: derived zzz"` → **PASS**.
  - F2: the real producers of `scu.bodha.mechanism.network` (a reviewed SCU) **erased**, and a false
    `no_contract` reason put in their place → **PASS**.

  So F does not inflate coverage. It can, however, hide a real producer behind a false reason and
  still read green. §7's "only mislabels an already-accounted-for SCU" understates this. `no_contract`
  in particular can be checked against the snapshot: whether the SCU has any requirement. This is
  non-blocking because B_REVIEW3 accepted F as a stated limit, but the wording should say "can
  mislabel and can demote a named SCU".

## §5 — Remaining findings

| # | finding | evidence | gate it blocks | correction |
|---|---|---|---|---|
| **B1** | R7's third conjunct (a `route_evidence_only`-only SCU counts as covered) is neither fixed nor ruled; the report misstates the gate's framing | §2.2 reo-only → PASS; B_REVIEW3 §4 R7 text; report §7, §12 item 6 | B-4 / the R85 fold | Code (plus test and mutation), **or** a recorded native ruling |
| **B2** | E is a 182/182 coverage bypass that can be checked from the snapshot; the report says it is not a coverage bypass and needs the DB | §2.2 E×75 → PASS 182/182; 294/294 `derived_from_source_query` `source_ref`s equal a snapshot `source_query` requirement on the same SCU | B-4 / R85 fold (§N.8); report honesty | Bind to the snapshot (recommended), **or** restate §7 and §12 item 4 truthfully |
| **B3** | "every exemption-tier producer is cross-checked" is an overclaim; the loop stops at the first valid producer | §2.2 bypass3 and bypass3b → PASS | Report honesty; the follow-on `compiler.ts` wiring would take fabricated producers | Validate every producer, **or** restate §2c, §12 item 4, the docstring and the `main()` comment |
| T1 | No test pins per-SCU binding | §2.4: global-union mutation → 30/30 green | Goes with B1–B3 (proof that could fail) | Add a "real claim on the wrong SCU" test through `main(["--check"])` |
| N3 | A literal remains: "111/127 and the same 16" in `write_closure_report_md` (`:1248`) | §3 | none | Interpolate, or mark it as a dated historical note |
| N4 | F's "only mislabels" understates F2 | §4.7 | none | Reword |

## §6 — Fact spot-check (B_REPORT v2.2 and commit messages)

| # | claim | result |
|---|---|---|
| 1 | (a)–(c) fail and (d) passes through the real `main(["--check"])` (§2c) | **VERIFIED** (§2.1) |
| 2 | mutation → exactly (a)–(c) fail, 3 failed / 27 passed; reverted → 30 (§2c) | **VERIFIED** (§2.3) |
| 3 | 24 exemption producers = 14 + 1 + 9, all snapshot-backed (§2c) | **VERIFIED** independently (§2.5) |
| 4 | the matching is "for that SCU" (§2c, §6) | **VERIFIED** in code and by bypass1/bypass2; **not test-pinned** (T1) |
| 5 | `--check` reads two files (§6, R8b) | **VERIFIED** |
| 6 | N1: `"50-60"` assert restored and passing | **VERIFIED** |
| 7 | N2: 14/94/127 interpolated, not hardcoded | **VERIFIED**; one residual literal (N3) |
| 8 | JSON byte-identical apart from `generated_at`; closure 63→111/127 (61ff5a09d message) | **VERIFIED** (§4.6) |
| 9 | 107/182; 75 NO_DETECTOR 28/28/11/7/1; outside 16 = 14 + 2 | **VERIFIED** |
| 10 | reader scan 76 / 36; 30/30; fingerprint MATCH; drift exit 3, one LOW | **VERIFIED** |
| 11 | "cross-checking every such producer" (§1, §2c, §12 item 4) | **WRONG** — only the first valid producer per SCU is guaranteed (B3) |
| 12 | "neither [E nor F] is a coverage bypass the way G was" (§7) | **WRONG for E** (B2) |
| 13 | "Fixing E would need a DB round-trip" (§12 item 4) | **WRONG for the coverage half** (B2) |
| 14 | the `route_evidence_only`-only gap was left "per the gate's own framing" (§12 item 6) | **WRONG** — the gate required a fix or a ruling (B1) |
| 15 | only Lane B files touched (commit 61ff5a09d message) | **VERIFIED** (§4.5) |

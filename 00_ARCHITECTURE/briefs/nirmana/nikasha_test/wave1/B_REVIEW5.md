---
artifact: NIKASHA_WAVE1_LANE_B_REVIEW_5
reviewer: Opus gate review 5 (independent, fresh context, read-only; not the implementer)
reviewed_on: 2026-09-27
packet: Nikaṣa wave 1, Lane B — "the catalog names its producers" (R85 / D5 rev. 2.1), fifth submission
packet_commits: cbc8b6724 (Lane B hunks only — swept into a Lane A commit), 26a601b58 + 028872b56 (B1), 2ee3e8430 (B2), 6af57f6d4 (B3), c43ae5c39 (T), 3ebbe08bf (F), 01bf88cd9 (N), 320999b75 (re-derived artifacts), b322ecd0b (B_REPORT.md v2.3)
base: 644bf3299 (B_REVIEW4.md)
prior_reviews: B_REVIEW.md (REJECT), B_REVIEW2.md (REJECT narrow), B_REVIEW3.md (REJECT narrow), B_REVIEW4.md (REJECT narrow)
verdict: ACCEPT_WITH_CORRECTIONS
---

# Lane B gate review 5

## §1 — Verdict: **ACCEPT_WITH_CORRECTIONS**

**All six items from B_REVIEW4 §5 are closed, and each is closed by a proof that could have failed.**
I re-ran every probe through the real `main(["--check"])` on scratch copies of the committed artifact,
and ran at least one mutation per item in a scratch mirror of the module and its tests. Every result
matches the report's §2d, including the two places where the report admits its own proof is weaker
than the brief asked for (T's broad mutation; F's substring-restore does not redden the erased-reviewed
case). The two defects the builder says it found in the swept commit `cbc8b6724` were real. I
reproduced both against that commit's code, and both are fixed at HEAD. Every headline figure
re-derives exactly: I re-derived against the read-only database to scratch, and the output is
byte-identical to the committed artifacts apart from `generated_at`. No untouchable file was touched.

**The remaining DB-dependent limit does not block** (ruling and reasons in §5). But the report
**understates** it. It describes only the fabrication direction (46 SCUs → 153/182 PASS). It does not
say that the same blindness runs the other way. Erasing the derived producers of the 86 SCUs that have
no snapshot claim or probe, and giving each a well-formed closed-set reason, also PASSES, and coverage
then reads **21/182**. It also does not say that the artifact's `summary` block is never checked
against its entries. So the report's "cannot demote a declared producer" is true only for the narrow
sense of "declared" (snapshot claims and probes).

**Corrections (all wording in `B_REPORT.md`; each bound to the gate it blocks):**

| # | correction | blocks |
|---|---|---|
| **W1** | Replace the E table/asset-half text in §7, §8 item 8 and §12 item 4 with the §5.4 wording below (fabrication **and** erasure **and** unchecked `summary`, with the one detector that exists: a manual re-derive-and-diff). | The R85 fold. The fold must not quote `--check PASS` as proof of what the database yields. |
| **W2** | §7 "F residual" and §8 item 8: "cannot demote a declared producer" becomes "cannot hide a snapshot-declared (claim or probe) producer; a well-formed reason can accompany the erasure of *derived* producers, which is limit W1(2)". | The R85 fold (item-6 wording) |
| **W3** | §6 line 593: "every forgery probe in §2d.2" fails is false. The E-residual row in that same table exits 0. Say "every forgery probe in §2d.2 except the E-residual row, which is OPEN (§7)". | The R85 fold (report honesty) |
| **W4** | Register a `--live` verification (re-derive in memory, then diff against the committed artifact ignoring `generated_at`) as a follow-up. It must exist, or its manual equivalent must be run and recorded, before the `compiler.ts` wiring lane consumes the artifact. | The follow-on `compiler.ts` wiring lane, **not** the R85 fold |

The executor can verify W1–W3 by reading the diff. They need no further gate review unless the
executor chooses to change code instead.

## §2 — Per item (B1, B2, B3, T, F, N)

Probe driver: `scratchpad/rv5/probe.py` + `probes1.py` / `probes2.py`. Each probe writes a modified
copy of the committed artifact to scratch, repoints `cp.DERIVED_OUTPUT_PATH`, and optionally
substitutes `cp.load_snapshot` with a modified snapshot. It then calls `cp.main(["--check"])`.
Mutation runner: `scratchpad/rv5/mut.py`. It builds a mirror (a copy of `catalog_provenance.py` and its
test file, plus symlinks to `00_ARCHITECTURE/` and `platform/src/`), applies exactly one textual edit
(asserted to match once), and runs the 56-test file. Mirror baseline: **56 passed**. The real tree was
never mutated.

### B1 — route evidence never covers

| probe | exit | output excerpt |
|---|---|---|
| unmodified | 0 | `--check PASS: all 182 SCUs …` |
| `temporal_activation` cut to its route-evidence producer, no reason | 1 | `snapshot-declared producer 'ka_bhavishya_lekha' (disposition 'reviewed_output') is missing` (+ `ka_yojaka`) |
| same + honest `route_evidence_only_not_a_producer` reason | 1 | same two presence failures. Correct: this SCU has reviewed claims, so it is not a route-evidence-only SCU. |
| **synthetic snapshot** (temporal_activation's claims reduced to the one route-evidence claim) + honest reason | **0** | PASS: an honest reo-only SCU passes |
| synthetic, no reason | 1 | `no covering producer and no valid no_detector reason` |
| synthetic, reason class `no_relation_in_range` | 1 | `only route_evidence_only producer(s) present but no_detector class is 'no_relation_in_range', not 'route_evidence_only_not_a_producer'` |
| `get_dignity` relabelled `route_evidence_only_not_a_producer` (no reo producer) | 1 | `no_detector class 'route_evidence_only_not_a_producer' but no snapshot-bound route_evidence_only producer is present` |

Mutations:
- `covers = True` for bound route evidence → **2 failed, 54 passed** (`…route_evidence_only_scu_carrying_no_reason`, `…relabelled_with_another_class`). This matches the report exactly.
- Drop the agreement check → **1 failed** (`…route_evidence_reason_with_no_route_evidence_producer`).
- Drop the reverse check → **1 failed** (`…relabelled_with_another_class`).

The round-trip test really derives through `derive_all` and then checks. The label and the producers
present must agree in both directions. **Closed.**

### B2 — source-query producers bound to a same-SCU `source_query` requirement

| probe | exit | excerpt |
|---|---|---|
| 75 NO_DETECTOR SCUs → fake `{zz_fake, no_such_table_xyz, nope.ts:1-2}` | 1 | 75 lines, each `scu…: producer 'zz_fake' (disposition 'derived_from_source_query') is not bound …` |
| a real producer with a real `source_ref` copied from `temporal_activation` onto `get_dignity` (foreign citation) | 1 | `scu.catalog.get_dignity: producer 'bo_laksana_rerank' … is not bound` |

Mutation: drop `and source_ref in source_query_refs` (shape-only) → **2 failed, 54 passed**, matching the
report. Direct count: **294/294** committed source-query producers are bound. **Closed, for the
citation half** (the remaining half is ruled on in §5).

### B3 — every producer checked

| probe | exit |
|---|---|
| fake `reviewed_output` appended to `scu.bodha.mechanism.network` | 1, fake named |
| same fake placed first | 1, fake named |
| fake `derived_from_source_query` (`nope.ts:1-2`) appended beside `temporal_activation`'s real producers | 1, named |
| producer with an unknown disposition `made_up_disposition` | 1, named |

Mutation: unbound producers ignored (`if not bound:` → `if False:`) → **4 failed, 52 passed**, matching
the report. **Closed.**

### T — per-SCU binding pinned

| probe | exit | excerpt |
|---|---|---|
| real `(bo_yantra_mechanism, reviewed_output)` copied onto `scu.catalog.assess_career` | 1 | `producer 'bo_yantra_mechanism' (disposition 'reviewed_output') is not bound` |
| real `ka_graha_sancara` probe (from `call_ephemeris_at_t`) copied onto `assess_career` | 1 | `producer 'ka_graha_sancara' (disposition 'derived_from_service_probe') is not bound` |

Mutations:
- **Narrow global** (only the binding comparisons read the global union) → **2 failed, 54 passed**: exactly the two wrong-SCU tests.
- **Broad global** (both per-SCU lookups global, B_REVIEW4 §2.4's mutation) → **2 failed**: `…copied_onto_the_wrong_scu` (probe) and `…real_committed_artifact_unmodified`. The claim test stays green, because the global union also feeds the presence check, which then fails the artifact for another reason.

The report discloses exactly this in §2d.1, and correctly relies on the narrow mutation. **Closed.**

### F — exact class token, and declared producers present

| probe | exit |
|---|---|
| `get_dignity` reason → `"zzz kind: derived zzz"` | 1 |
| → `"NO_DETECTOR — zzz kind: derived zzz"` | 1 |
| → `"NO_DETECTOR —  no_contract: …"` (double space) | 1 |
| → `"NO_DETECTOR — no_contract"` (no colon) | 1 |
| `scu.bodha.mechanism.network` producers erased, reason `"NO_DETECTOR — no_contract: fabricated"` | 1, `snapshot-declared producer 'bo_yantra_mechanism' … is missing` |
| `temporal_activation`'s reviewed claims removed, derived producers kept | 1, both reviewed producers named missing |
| `call_ephemeris_at_t`'s service-probe producer erased behind `no_contract` | 1, `'ka_graha_sancara' (disposition 'derived_from_service_probe') is missing` |

Mutations:
- `a171addc7`'s classifier restored **verbatim** → **9 failed, 47 passed**, matching the report.
- My own substring variant → 10 failed.
- Drop the presence check → **3 failed** (the temporal cut, demoted-beside-derived and erased-reviewed tests), matching the report.
- Split on `": "` instead of `":"` → **1 failed**, matching the report.

**Closed.** One observation, not a finding: `"NO_DETECTOR — no_contract:"` with an empty detail passes.
That is harmless, since it is an instance of the stated limit 2.

### N — the literal is interpolated

`CLOSURE_REPORT.md:18` reads `**111/127** … **16**`, generated from `closure[...]`. Mutation: the literal
`**111/127**` restored → **1 failed, 55 passed** (`test_closure_traversal_prose_reads_computed_numbers_not_a_literal`).
**Closed.**

## §3 — The swept commit `cbc8b6724`

**Composition.** The commit's message and co-author line describe only Lane A F5. It touches 7 paths:
- **Lane A:** `asset_census.py` (the `ever_superseded` set) and `test_a2_emit_gaps_closure.py` (+1 test).
- **Lane B:** `catalog_provenance.py`, `test_catalog_provenance.py` (+8 tests, listed below), and the three `provenance/**` artifacts.

The 8 Lane B tests: `…reduced_to_only_its_route_evidence_producer`,
`test_derive_all_gives_a_route_evidence_only_producer_an_explicit_no_detector_reason`,
`…fake_source_query_producer`, `test_all_committed_source_query_producers_are_snapshot_bound`,
`…appended_beside_a_real_one`, `…real_claim_is_copied_onto_the_wrong_scu`,
`…trigger_substring_but_no_exact_prefix`, `…erased_and_replaced_with_a_fake_reason`.

**No cross-dependency.** Neither module imports the other: `grep` finds no `catalog_provenance` in
`asset_census.py` or `test_a2_emit_gaps_closure.py`, and no `asset_census` in the Lane B files. The
Lane A hunk is self-contained ledger logic. No Lane B commit after `cbc8b6724` touches a Lane A path.

**Lane B hunks — correctness.**
- Reason reformatting to `NO_DETECTOR — <class>: <detail>`: I diffed the artifact at `644bf3299`
  against HEAD with `no_detector` removed. Only 3 entries differ, and only in their `notes` text (the
  same reformatting). `summary` and `calibration` are identical. So the reformatting moved no class
  and no count.
- `scu_has_covering_producer`, `snapshot_source_query_refs`, the per-producer loop and the N3
  interpolation are all correct as landed, and unchanged in substance since.
- The exact-match classifier landed splitting on `": "`. `3ebbe08bf` corrected that to `":"`.

**The two defects the builder reports — both genuine, both fixed.** I loaded `cbc8b6724`'s
`catalog_provenance.py` in a scratch mirror and drove its `main(["--check"])`:

| case | at `cbc8b6724` | at HEAD |
|---|---|---|
| honest reo-only SCU (synthetic snapshot) + `route_evidence_only_not_a_producer` reason | **exit 1** — `no covering producer and no valid no_detector reason`. The F2 guard counted the route-evidence claim as proof a producer belonged, so the reason `derive_all` writes was rejected. | exit 0 (fixed in `26a601b58`) |
| `temporal_activation`'s reviewed claims removed, derived producers kept | **exit 0, PASS** (the F presence gap) | exit 1, both named (fixed in `3ebbe08bf`) |

**Process defect.** Lane B code sits under a Lane A hash and message. The report discloses this
plainly (§2d.0, §12 item 8), and history was reasonably not rewritten on a shared branch. It does not
block. The register entry for R85 must cite `cbc8b6724` explicitly as carrying Lane B code (see the
acceptance statement).

One minor ordering note: `6af57f6d4` (B3) rewrote the module docstring to say `--check` fails "when a
snapshot-declared producer is missing". That became true only one commit later, in `3ebbe08bf`. It is
true at HEAD and not a finding.

## §4 — Figures (item 3) and scope (item 4)

**Re-derivation.** I re-derived to scratch against the read-only DB (`SHOW default_transaction_read_only`
= `on`), using `scratchpad/rv5/rederive.py`. It patches the module paths **and** the three writers'
bound default arguments (`write_derived_json.__defaults__` etc.). This matters because patching
`DERIVED_OUTPUT_PATH` alone does **not** redirect the writer: the default is bound at definition time,
which is how an earlier reviewer overwrote the committed file. The driver asserts the redirection
before running. The committed artifact's sha256 (`d1ca957f…77cf`) was identical before and after, and
`git status` of `provenance/` stayed clean.

| figure | report | reproduced |
|---|---|---|
| JSON, closure, reader scan vs committed | byte-identical apart from `generated_at` | **yes**: `diff` shows only the `generated_at` line in all three. JSON is equal as objects with `generated_at` removed. |
| named | 107/182 | **107/182** (`[B-1] 107/182`) |
| NO_DETECTOR | 75 = 28/28/11/7/1 | **75**: `no_contract` 28, `relation_unowned_by_registry` 28, `no_relation_in_range` 11, `source_ref_out_of_range` 7, `derived_kind_no_source_query` 1 |
| closure | 63 → 111 of 127; 16 outside = 14 + 2 | **63 → 111 of 127**; `no_unit_names_it` 14, `table_unregistered` 2 |
| bound producers | 294/294, 14/14, 1/1, 9/9 | **294/294, 14/14, 1/1, 9/9** (318 total, 0 unbound) |
| declared presence | 15/15 claims, 9/9 probes | **15/15, 9/9** |
| Lane B suite | 56 pass | **56 passed** |
| reader scan | 76 hits / 36 files; 320999b75 changed only `generated_at` + 12 line numbers | **76 / 36**; 320999b75's diff is 26 lines = 2 `generated_at` + 12 line-number pairs |
| manifest | `--check` MATCH | **MATCH** (`f484f581767ad641`) |
| drift | exit 3, one LOW | **exit 3**, one finding `a3_category_not_yet_populated` LOW. The run wrote two gitignored `drift_reports/DRIFT_REPORT_adhoc_20260927T073232Z.*` files, which I deleted. |
| governance `__tests__/` | 171 passed, 5 skipped, 2 failed | **171 passed, 5 skipped, 2 failed** |
| the 2 failures pre-exist at `644bf3299` | yes | **yes**: `git worktree add --detach` at `644bf3299` shows the same two failures in `test_drift_detector_h35_h38.py` (`test_f163_…`, `test_h35_…`), 2 failed / 14 passed. The worktree was removed and pruned. |

**Scope.** The Lane B commits (26a601b58, 2ee3e8430, 6af57f6d4, c43ae5c39, 3ebbe08bf, 01bf88cd9,
028872b56, 320999b75, b322ecd0b) plus `cbc8b6724`'s Lane B hunks touch only:
- `catalog_provenance.py`
- `__tests__/test_catalog_provenance.py`
- `nikasha_test/provenance/**` (3 files)
- `wave1/B_REPORT.md`

The interleaved Lane A commits (065e620b2 … 8ef861e0b) touch no Lane B path. **Nothing untouchable
was touched.**

## §5 — Ruling on the DB-dependent limit

### 5.1 What I measured

On copies of the committed artifact, through the real `--check`:

1. **Fabrication (the builder's case).** The 46 NO_DETECTOR SCUs that carry a `source_query`
   requirement (28/11/7 by class) each get `{zz_fake, no_such_table_xyz}` reusing the SCU's real
   `source_ref`, with the reason removed. Result: **PASS, exit 0; 153/182 would read covered**.
   Reproduced. A variant using a real asset and a real but wrong table (`ga_positions` / `chart_facts`)
   also passes.
2. **Erasure (not in the report).** The 86 SCUs whose producers are all `derived_from_source_query`
   and which have no snapshot claim or probe have their producers erased and are given a well-formed
   closed-set reason. Result: **PASS, exit 0; coverage would read 21/182**. Dropping one of several
   derived producers from an SCU that stays covered also PASSES.
3. **Unchecked summary (not in the report).** Setting `summary.scus_with_producers = 182` and
   `scus_no_detector = 0` PASSES. Changing `snapshot_content_hash` also PASSES.

### 5.2 Ruling: **does not block the R85 fold**

**(a) The derivation is a real detector for the artifact's truth at derive time. But nothing runs it
automatically.** `--derive` reads the live DB (`asset_registry`, `information_schema.tables`) and
re-derives deterministically. My independent re-derivation is byte-identical to the committed file
apart from `generated_at`. Any of the three edits above would show up as a diff against a fresh
derivation. So the figures the fold will quote (107/182 and the rest) have a detector that measures
exactly what they claim, and that detector was run and passed at gate time. What does not exist is an
automated invocation of it. Per §N.8, `--check PASS` must therefore not be quoted as evidence of
database truth. It is evidence of consistency between the artifact and the catalog.

**(b) An offline file-integrity gate is the right place for file-checkable facts only.** C-1 made
`--check` file-only on purpose, so it can fail on a hand-edit that nothing in today's DB would
reproduce. Pushing DB lookups into it would mix two different claims into one PASS. The honest design
is a separate `--live` mode: re-derive in memory, diff against the committed file ignoring
`generated_at`, and fail on any difference. `_run_derivation` already exists, so this is small. It
closes all three measured gaps at once: fabrication, erasure and summary. Its absence is a stated
limit, not a lane-B defect. The artifact is not consumed by any code until the `compiler.ts` wiring
lane, so W4 binds `--live` (or a recorded manual re-derive-and-diff) to that lane's gate.

**(c) The partial offline re-parse (at most 18 of 46) is not worth requiring.** It would duplicate the
derivation's range parsing inside the gate. It would close only the fabrication direction for 18
SCUs, and would leave the 28 `relation_unowned_by_registry` SCUs, all of erasure, and the summary
open. `--live` closes all of it. I do not require it.

**What would have made this blocking:** a report that claimed `--check` proves database truth, or that
hid the limit. The report states the fabrication half plainly and measures it (§2d.2, §7, §12 item 4).
It omits the erasure half and the summary. That is fixable in wording (W1/W2) and does not change any
figure.

### 5.3 What `--check` does prove (for the fold)

- Every producer of every tier on every SCU cites what the snapshot declares for that same SCU.
- Every snapshot-declared claim and probe is present.
- Route evidence never covers.
- Every NO_DETECTOR reason is an exact closed-set class, and the route-evidence class agrees with the producers present.
- The SCU set equals the catalog's.

### 5.4 Required wording (W1), to replace the E table/asset-half text in §7, §8 item 8 and §12 item 4

> **`--check` is an offline consistency check between the artifact and the catalog snapshot. It is
> not a check of the artifact against the database.** It proves that every producer of every tier
> cites what the snapshot declares for that same SCU, that every snapshot-declared claim and probe is
> present, and that every NO_DETECTOR reason is an exact closed-set class. It cannot see database
> facts. Measured on copies of the committed artifact, each of the following **passes** `--check`:
> **(1)** a fabricated `derived_from_source_query` producer (`zz_fake`, `no_such_table_xyz`) that
> reuses the SCU's real `source_ref`, on each of the 46 NO_DETECTOR SCUs that carry a `source_query`
> requirement, would read **153/182** covered. **(2)** Erasing the producers of the 86 SCUs whose
> producers are all derived (no snapshot claim or probe), each given a well-formed closed-set reason,
> would read **21/182** covered. Dropping one derived producer from a still-covered SCU also passes.
> **(3)** The artifact's `summary` counts and `snapshot_content_hash` are not checked against its
> entries or the snapshot. The one detector for all three is a re-derivation against the read-only
> database, diffed against the committed file. It was run at `320999b75`, and again independently by
> gate review 5: byte-identical apart from `generated_at`. It is manual today; no `--live` mode
> automates it. Until one exists, `--check PASS` means "consistent with the catalog", not "what the
> database yields". The published figures rest on the re-derivation, not on `--check`. A file-only
> re-parse could close at most 18 of the 46 in (1) and none of (2) or (3), so it was not done. A
> `--live` re-derive-and-diff mode is registered as required before the `compiler.ts` wiring lane
> consumes this artifact.

## §6 — Items 6 and 7

### 6.1 Limit 2 — both halves, by construction

- **It mislabels.** `get_dignity` (true class `source_ref_out_of_range`, and it has a `source_query`
  requirement) relabelled `"NO_DETECTOR — no_contract: wrong on purpose"` → **PASS**. A false class
  passes. **Confirmed.**
- **It cannot create coverage.** A reason is consulted only when no covering producer exists. Coverage
  requires a bound non-route-evidence producer, and a reason string cannot supply one. Every
  producer-adding forgery that does not reuse a real citation fails (§2). **Confirmed.**
- **It cannot hide a *snapshot-declared* producer.** `get_dashas`'s reviewed `ga_dashas` erased behind
  `no_contract` → exit 1, `snapshot-declared producer 'ga_dashas' … is missing`. The same happens for a
  service probe (§2 F). **Confirmed for claims and probes.**
- **But** a well-formed wrong reason **can accompany the erasure of derived producers**, which the
  snapshot does not declare. `scu.catalog.chart_facts_query` (7 derived producers) erased and labelled
  `relation_unowned_by_registry` → **PASS**. This is §5.1(2). The limit-2 claim is true only with
  "declared" read as "snapshot-declared (claim or probe)". Correction **W2** makes that explicit.

### 6.2 B1's executor ruling — flagged plainly; no production figure depends on it

- The frontmatter carries `native_confirmation_requested: B1 — route_evidence_only never counts as
  coverage is an EXECUTOR application of D5 rev. 2.1's wording, not a recorded native ruling (§2d)`.
- §2d.4 says in bold: "This is the executor's reading of the ruling's wording, not a recorded native
  ruling". §12 item 7 repeats it.
- **No production figure depends on it.** In the committed artifact, 0 SCUs have route evidence as
  their only producer, and 0 carry `route_evidence_only_not_a_producer`. Coverage counted either way
  (≥1 non-reo producer, or any producer) is **107** both times. The one route-evidence claim
  (`ka_kalasutra` on `scu.kala.temporal_activation`) sits beside two reviewed and several derived
  producers.
- The report's statement that a reversal is "one predicate plus the matching `covers` line" is
  accurate for `scu_has_covering_producer` and `validate_derived_artifact`. A reversal would also have
  to retire the `route_evidence_only_not_a_producer` agreement checks, or they become dead code. That
  is harmless.

## §7 — Remaining findings

| # | finding | evidence | gate it blocks | correction |
|---|---|---|---|---|
| **W1** | The DB-dependent limit is stated only in its fabrication direction; erasure (→21/182 PASS) and the unchecked `summary`/hash are not stated | §5.1(2)(3) | **R85 fold** | §5.4 wording in §7, §8 item 8, §12 item 4 |
| **W2** | "cannot demote a declared producer" is true only for snapshot-declared producers | §6.1 | **R85 fold** | Reword §7 F-residual and §8 item 8 as in §1 |
| **W3** | §6 says every §2d.2 forgery probe fails; its E-residual row exits 0 | report §6 l.593 vs §2d.2 last row | **R85 fold** (report honesty) | Add the exception |
| **W4** | No automated re-derive-and-diff exists | §5.2 | **`compiler.ts` wiring lane** (not the fold) | Register `--live` as required before that lane consumes the artifact |
| n1 | The PASS message says "at least one NON-route_evidence_only covering producer where any producers exist, or a no_detector reason". An honest reo-only SCU has producers yet passes through the reason. | `main()` PASS string | none | Optional rewording |
| n2 | `summary` agreement with entries is file-checkable offline (about 10 lines) | §5.1(3) | none (covered by W1 wording) | Optional code: recompute summary from entries in `--check` |
| n3 | Lane B code under the Lane A hash `cbc8b6724` | §3 | none | Register citation (acceptance statement) |

## §8 — Fact spot-check (B_REPORT v2.3 and commit messages)

| # | claim | result |
|---|---|---|
| 1 | B1 gate mutation → 2 failed, 54 passed (isolated + relabel) (§2d.1) | **VERIFIED** |
| 2 | B1 drop agreement → 1 failed; drop reverse → 1 failed | **VERIFIED** |
| 3 | B2 shape-only mutation → 2 failed, 54 passed | **VERIFIED** |
| 4 | B3 first-valid restore → 4 failed, 52 passed | **VERIFIED** (my mutation: ignore unbound) |
| 5 | T narrow → exactly the 2 wrong-SCU tests; broad → probe test + unmodified-PASS test, claim test green | **VERIFIED** |
| 6 | F verbatim `a171addc7` classifier → 9 failed, 47 passed; drop presence → 3 failed; `": "` split → 1 failed | **VERIFIED** |
| 7 | N literal restored → 1 failed, 55 passed | **VERIFIED** |
| 8 | at `cbc8b6724`, `--check` rejected the reo reason `derive_all` writes, and the demote-beside-derived edit passed (§2d.0) | **VERIFIED** against that commit's code |
| 9 | E residual: 46 SCUs (28/11/7), PASS, 153/182 (§2d.2, §7) | **VERIFIED** |
| 10 | Re-derivation byte-identical apart from `generated_at`; 107/182; 75 = 28/28/11/7/1; closure 63→111/127, 16 = 14+2 (§2d.3) | **VERIFIED** (independent re-derive, §4) |
| 11 | 318 producers all bound: 294/14/1/9; declared 15/15 + 9/9 | **VERIFIED** |
| 12 | 56 tests = 30 + 8 swept + 4 + 1 + 1 + 1 + 10 (7 parametrized) + 1 (§2d.5) | **VERIFIED** by per-commit `def test_` / parametrize counts |
| 13 | 2 drift-detector test failures pre-exist at `644bf3299` | **VERIFIED** (clean worktree, removed) |
| 14 | manifest MATCH; drift exit 3, one LOW | **VERIFIED** |
| 15 | "Lane B never touched Lane A's files" (§2d.0) | **VERIFIED** |
| 16 | "every forgery probe in §2d.2" fails (§6) | **WRONG**: the E-residual row passes (W3) |
| 17 | F residual "mislabels but cannot demote a declared producer" (§8 item 8) | **TRUE ONLY** for snapshot-declared producers (W2) |
| 18 | B1 moves no production number (§2d.3, §2d.4) | **VERIFIED** (107 either way; 0 reo-only SCUs) |

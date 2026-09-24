---
artifact: DK_REVIEW_SANGAM
version: "1.0"
date: 2026-09-24
gate: D-K (KALA_DELEGATED_DECISIONS_v1_0.md v1.9)
reviewed_sha: 204b003ea
reviewed_ref: tip of origin/sangam/stage3 at commissioning (branch still live; later commits out of scope)
reviewer: "fresh-context subagent, opus"
independence_statement: >
  I had no part in the Saṅgam plan, its §10 dispositions, or the build. Before forming any view I read, in
  this order and as primary sources: D-K and its neighbours in KALA_DELEGATED_DECISIONS_v1_0.md; the ruled
  plan SANGAM_ELEVATION_FINAL_v1_0.md; SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md §0R and §10 in full; the
  entry review ASTRA_REVIEW_SANGAM_ALGO_PLAN_v1_0.md (findings list and gate section). I then went to code
  first and prose second: ka_sangam.py, services/ka_sangam/{engine,exposure,identity}.py, ka_taranga.py, the
  five migrations, asset_registry_seed.ts, the l3 tests, and every evidence script I cite. I re-derived the
  E6 binomial figures myself from first principles before reading the author's arithmetic. I read the
  builder's SANGAM_STAGE3_STATE.md and SESSION_LOG-adjacent claims ONLY after reaching my own findings on
  RRV-01, RRV-03 and the AV receipt, and I treated every sentence in them as a claim, not evidence; where
  the state file and my finding agree I say so, and where the governing plan text and the state file
  disagree I report the disagreement rather than choosing. I did not read the Kimi K3 reconciliation until
  after I had independently established that the RRV-01 join does not exist in the repository. I did not
  run, commission, or see the D-K second instrument (an isolated Kimi K3 pass in a detached worktree).
verdict: CONFORMS_WITH_AMENDMENTS
verdict_basis: >
  Twelve of the sixteen RRV dispositions are genuinely present in code, tests and evidence, and several are
  implemented better than §10 promised. The E6 statistics are exactly right: I reproduced all six published
  figures to ten decimal places from the stated n, critical value and rates, the critical values are the
  minimal ones at alpha <= 0.05, and the test behind them is a real detector rather than a tautology. Scope
  discipline holds — no frozen L1 writer, no transit_search, no sealed L4/L5 surface is touched at this tip,
  and the reverted breach is genuinely gone. But one HIGH disposition (RRV-01) is ABSENT in code: the
  stage-3-side receipt join §10 binds does not exist anywhere in the repository, and the mechanism shipped
  in its place reads a fact category that no writer in this repository produces — an Earned-Signal (§N.8)
  defect that renders the E2 ashtakavarga verdict permanently unavailable on modes A/B in production. One
  further HIGH (RRV-03) is PARTIAL, and the governing §10 text contradicts both itself and the builder's own
  state file in two places. The build is sound and unusually honest about its gaps, but §10 — the document
  D-K asks me to measure it against — overstates what landed and must be corrected before it is merged as a
  record of what was done.
instruments_used:
  - independent re-derivation of the D-1 binomial design (exact rational arithmetic, Python fractions/comb)
  - direct source reading at 204b003ea with file:line citation
  - git history: diff vs origin/main, the reverted breach 77ec40ef5, the three engineering passes, 1ef326494
  - independent re-run of the 21-script evidence suite (scratch mirror; see Evidence section for why a mirror was required)
  - independent run of the ka_sangam pytest set (224 tests) and the full tests/l3 set
  - NOT RUN BY ME: the D-K second instrument, an isolated Kimi K3 pass in a detached worktree. I neither ran nor saw it.
  - NOT RUN: any database query, migration, seed or write of any kind. No DB was contacted.
---

# D-K review — does the Saṅgam build on `204b003ea` conform to the ruled plan and its own §10 dispositions?

## 0. What D-K asked, and what I answer

D-K's question is not whether plan v1.0's text survives review. It is: **does the BUILD on this tip conform
to the ruled plan and to its own §10 dispositions, and are the amendments it claims actually present in
code, tests and evidence?** The defect D-K targets is builder-certified dispositions.

My answer: **mostly yes, with one HIGH amendment that is absent in code and a governing document that
overstates what landed.** Details below. I am not the native; I cannot waive D-K, authorise a merge, or
declare the branch safe. This records a conformance verdict and nothing more.

A note on method that matters for how you read the table. §10's own preamble says its dispositions are
"**binding on stage 3 unless marked carried**." So I graded a disposition ABSENT when its binding content is
not in the build, even where the builder later recorded the gap honestly somewhere else. Honest self-record
changes the *severity* of a gap; it does not convert an absent amendment into a present one. That
distinction is the whole substance of D-K.

---

## 1. RRV-01 … RRV-16 conformance table

Grades: **CONFORMS** · **PARTIAL** · **ABSENT** · **CONTRADICTED** · **UNVERIFIABLE**.
"Test counts?" asks whether the test would fail if the amendment were removed — a test that passes either
way is recorded as not counting.

| # | Sev | Finding (compressed) | §10 disposition claimed | Code? | Tests? | Evidence? | Grade | Source |
|---|---|---|---|---|---|---|---|---|
| **RRV-01** | HIGH | E2's producer receipt has no authorized hand | Receipt computed **stage-3-side**: writer joins AV sign-facts against L1 `chart_facts` `graha_position` facts → `provenance: fabricated_zero` / `measured_zero`; **no edit to `ga_strength_writer.py`**; producer-column route routed as an L1-owner packet | **NO** | Partial | Discloses absence | **ABSENT** | No such join exists. `fabricated_zero`/`measured_zero` occur **nowhere** in the repository (repo-wide grep, 0 hits outside unrelated `mi_*` tests). The writer instead reads `fact_category IN ('ashtakavarga_completeness_receipt','ashtakavarga_school_primary')` at `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py:1259-1298` — the producer-column route the disposition explicitly deferred. See Finding A1 for the live consequence. The *negative* half of the disposition **is** honoured: `git diff origin/main...HEAD -- '*ga_writers*'` is empty; `ga_strength_writer.py` is byte-identical to main and the breach `77ec40ef5` is genuinely reverted. Evidence `S3_ashtakavarga_producer_vs_reader.py:22-27` states in its own comment "**B-4 is OPEN: no L1 producer receipt exists today — RRV-01's stage-3-side join is unimplemented**". |
| **RRV-02** | HIGH | Step 3 silently gated on N-7 | Gate adopted inline; stage 3 proceeds on scanner-independent scope only; convention vector authored into the event-consumption interface | YES | YES | YES | **CONFORMS** | `transit_search.py` untouched (`git diff --name-only origin/main...HEAD` has no match). Scanner-independent scope is what shipped: R-3(a)/R-6/R-1/R-2 present, E1/E3 absent. Convention vector is authored as data: `services/ka_sangam/identity.py:38-68`, persisted by migration 1089. **But** §10's RRV-02 row still reads "N-7 status at 2026-09-23: **UNRULED** (verified by tree-wide search)" while §0R M-3 carries a dated correction saying N-7 *was* ruled. See Finding A5. |
| **RRV-03** | HIGH | No within-class ordering contract post-R-6 | Per-`comparability_class` key `activity DESC, contact instant ASC`; valence/applicability/availability as data, never pooled; **enforcement as SQL-level `comparability_class`/`kernel_version` partitioning in every consumer query**; SPEC: two equal-activity opposite-valence rows both survive a page | Partly | YES | YES | **PARTIAL** | Engine half is complete and real: `services/ka_sangam/engine.py:973-990` (`ordering_key`), applied at `:1716`, `:2010`, `:2147`, `:2306`. Columns reach the table: migration `1088_kala_convergence_kernel_fields.sql` adds `activity/valence/applicability/comparability_class/kernel_version/independence_group` + index; writer persists them at `ka_sangam.py:1132-1190`. The SPEC assertion has a **real detector**: `tests/l3/test_ka_sangam_r6_kernel.py:270-277` takes a LIMIT-2 page and asserts both valences survive — it would fail if valence were pooled into the key. **Missing:** the SQL-level consumer-query partitioning the disposition names as the enforcement vehicle — zero hits for `kernel_version`/`comparability_class` under `platform/src` or `platform-mcp`. The builder scopes this out at `SANGAM_STAGE3_STATE.md:189` ("consumer SQL partitioning … ride with the Phase-2 … cluster, not this increment"), which is a deferral, not a discharge. |
| **RRV-04** | HIGH | Two consumers of `kala_convergence` unnamed | `mi_adhilepa` + `ph_nimitta` join the consumer obligation set; `mi_adhilepa` surrogate binding recorded as an R-5/L3-U07 dependency — "**never a stage-3 edit**"; UNRESOLVED_USE list carried as a checklist item | Doc-level by design | n/a | YES | **CONFORMS (as scoped)** | Correctly doc-level: nothing in `services/ka_sangam/` or the writer references `mi_adhilepa`/`ph_nimitta`, which is what the disposition requires (L5 sealed, packet-and-test only). The enabling half did land: `contact_uuid` is now a real column (migration `1089`), which is exactly what `mi_adhilepa`'s surrogate binding needed. Registry edge added at `platform/scripts/seed/asset_registry_seed.ts:2316` — but see Finding A2. |
| **RRV-05** | MOD | Ruled taranga unit missing from plan E5 | Unit = occupied-day union per (contract × valence); month boundary pinned to the chart's **birth timezone** from `birth_params` | YES | YES | YES | **CONFORMS** | `platform/python-sidecar/pipeline/orchestrator/writers/ka_taranga.py:273` implements the unit verbatim; `:79-112` resolves the birth tz (prefers `ctx.config['birth_params']`, falls back to `public.charts.timezone_id`, then UTC with a warning); `:114-160` computes occupied local months checking both ends of the UTC day for tz crossings. Real implementation, not a label. |
| **RRV-06** | MOD | Aborted approaches missing from plan E5 | Kept as labelled children (`approached, never perfected`); E6-numerator inclusion **[RULED — INCLUDED, `perfected` a mandatory reported covariate]** | Partly | YES | YES | **PARTIAL** | The labelling half is real: `engine.py:2565-2566` emits `loop_phase` and `approached_never_perfected` per child; `:2592` sets `perfected` from truncation state; migration `1072` adds the `perfected` column with an accurate COMMENT. The **mandatory reported covariate** half is not: `exposure.py`'s `stratum_key()` is `(domain × route × method_version)` (`:88-98`) and `StratumOutcome` (`:305-325`) carries no perfected/unperfected split, so nothing reports it. Three documents disagree about whether this is even ruled — see Finding A6. |
| **RRV-07** | MOD | Stale gate numbers in companion changelog | Companion changelog corrected in place with a dated correction line | YES | n/a | YES | **CONFORMS** | `SANGAM_ELEVATION_BRIEF_v1_0.md:499` carries the correction with the supersession history visible (`~~30~~ ~~35~~ **20** per stratum, crit ≥8 / ~~100~~ **50** pooled, crit ≥16`). Note §10's RRV-07 row itself now quotes the *superseded* 35/100 triples — harmless, because §0R M-6 and the brief both carry the current ones, but it is a stale line in the disposition table. |
| **RRV-08** | MOD | Static daśā prior bypasses availability | Eligibility failure → `availability.dasha = unavailable`, **zero manufactured support** | YES | YES | YES | **CONFORMS** | `engine.py:1583-1590` sets `'dasha': 'computed' if dasha_source == 'service' else 'unavailable'` and the surrounding comment (`:1570-1573`) states the rule: a term whose input was unavailable is recorded as an availability state, "never manufactured neutral support". Mode B's structural case is explicit at `:1889-1890`. The same treatment is applied to vedha, target, ashtakavarga and tājika — broader than the disposition required. |
| **RRV-09** | MOD | §6.3 canonical framing unpinned | Canonical serialization with explicit field-exclusion list (surrogate row id, `computed_at`, generation-head pointers), sorted-key JSONB framing, compared per stable id, on a schema-faithful disposable DB | YES | YES | YES | **CONFORMS** | `evidence_sangam/r5_harness/r5_identity.py:37-46` defines the exclusion set with `computed_at` named at `:40`; `:58-59` is the sorted-key canonical serializer; `:97-105` strips excluded fields before hashing; `:122` strips banned fields for row comparison; `:200` compares `claim_content` per stable id. The harness DB is schema-faithful and disposable (`r5_harness.py:40-41, :79`). Correctly located harness-side, as dispositioned. |
| **RRV-10** | MINOR | Stale ephemeris text (Moshier asserted) | Fixture policy re-anchored to the backend detector; SWIEPH run cited | YES | n/a | YES | **CONFORMS** | Verified behaviourally, not just textually: I ran `S8_saturn_loop_oracle.py` myself — it detects the backend from the returned flag (`requested flags 65794, returned 65860 → MOSHIER`) and exits `NOT_RUN(3)` rather than passing as an oracle. That is the amendment working. |
| **RRV-11** | MINOR | K2-08 `[N]`/`[A]` markers partial | Adopted inline at §0R M-2 | YES | n/a | n/a | **CONFORMS** | §0R M-2 row carries `**[N]**` and `**[A]**` markers as required. |
| **RRV-12** | MINOR | Moshier-policy line unwritten | Logic-on-Moshier-with-backend-recorded vs accuracy-is-NOT_RUN; S8's stricter self-rule as per-script ceiling | YES | n/a | YES | **CONFORMS** | The policy is not merely written, it is executable and I observed it execute (see RRV-10). |
| **RRV-13** | MINOR | D-2 interval denominator unpinned | "Carried to Phase 5 (E6)": `all` = all issued windows in the stratum **including censored and unobserved** | YES | YES | YES | **CONFORMS (early)** | Implemented ahead of its carried status. `exposure.py:408` `total = hits + misses + ambiguous + censored + unobserved`; `:415-417` `lower = hits/total`, `upper = (hits+ambiguous)/total`. `:315-319` documents `n_evaluated` (fully observed) as distinct from `total` (all five states). `tests/l3/test_ka_sangam_e6_exposure.py:131-138` asserts `n_evaluated == 15`, `total == 20`, `hit_rate_interval == (10/20, 13/20)` — a real detector that would fail if the denominator narrowed. |
| **RRV-14** | MINOR | E1 angle-family assertion missing | "Carried to the E1/E3 phase" (gated on N-7); SPEC authored with the event-consumption interface | n/a (carried) | n/a | n/a | **CONFORMS (as carried)** | E1/E3 did not build, consistent with the gate. I cannot verify a future SPEC; the carry is correctly scoped and nothing in the build pre-empts it. |
| **RRV-15** | NOTE | NEG sincerity escape | Permanent discipline: every new evidence script's NEG path read line-by-line; a NEG path that does not mutate evidence-bearing state is rejected | Partly | n/a | Partly | **PARTIAL** | Applied where it was flagged: `S3` (a) was rewritten to mutate evidence-bearing input **before** asserting (`S3:34-40`) and its NEG genuinely re-runs the real function. But the same script's sections (c)/(e) still reassign result variables post-hoc (`S3:70-71`, `:88-89`) rather than re-running the system — the control fails, but not because evidence changed. This is the pattern RRV-15 names, surviving inside the script written to enforce it. A second gap is structural: `RUN_ALL.sh`'s negative-control check is `if [ "$nrc" -eq 0 ]`, so a `NOT_RUN(3)` script satisfies its negative control **vacuously** — S8 is currently recorded `neg=3` and passes that check having tested nothing. |
| **RRV-16** | NOTE | Mean-node ruling not executable in Saṅgam today | Adopted inline; scanner hardcoded TRUE_NODE; ruling binds the contract, not the scanner; new rows declare the vector honestly | YES | YES | YES | **CONFORMS (strongly)** | `identity.py:38-44` records `NODE_CONVENTION_SCANNER = 'true_node'` with the `transit_search.py:10,64` citation; `:58-68` emits the six-component frame as named data. Migration `1089` persists `convention_frame` with honest gap markers (`ephemeris_backend='unasserted'`, `house_frame='unavailable'`) rather than inventing values. Migration `1090` derives `comparable_with='different_convention'` **from** `convention_frame.node_convention` rather than defaulting it, so the value flips automatically when the convention unifies. This is the §N.8 discipline applied correctly and is the best-executed item in the set. |

**Tally: CONFORMS 11 · CONFORMS-as-scoped/carried 2 · PARTIAL 3 · ABSENT 1 · CONTRADICTED 0 · UNVERIFIABLE 0.**
(Counting RRV-04 and RRV-14 in the "as scoped/carried" bucket; RRV-03, RRV-06, RRV-15 PARTIAL; RRV-01 ABSENT.)

---

## 2. E6 statistics — independent re-derivation

The plan (§0R M-6) and ruling sheet §CLOSE D-1 bind:
per-stratum **n=20, critical ≥8, α=0.0321, power 0.868 at 0.20→0.50** (0.584 at a doubling);
instrument-level **n=50, critical ≥16, α=0.0308, power 0.904 at 0.20→0.40** (0.553 at 1.6×).
Null rate 0.20 throughout.

I did not check the author's arithmetic; I recomputed everything from the definitions using exact rational
arithmetic (`fractions.Fraction` over `math.comb`, null and alternative rates as exact decimals), then
compared. Working:

| Quantity | Definition | My value (exact) | Published | Match |
|---|---|---|---|---|
| Per-stratum α | P(X ≥ 8 \| Bin(20, 0.20)) | 0.03214266308087513 | `PER_STRATUM_ALPHA = 0.0321426631` → 0.0321 | **exact to 10 dp** |
| Per-stratum power (design) | P(X ≥ 8 \| Bin(20, 0.50)) | 0.8684120178222656 | 0.868 | **exact** |
| Per-stratum power at 2× | P(X ≥ 8 \| Bin(20, 0.40)) | 0.5841070624424644 | `PER_STRATUM_POWER_AT_2X = 0.584` | **exact** |
| Instrument α | P(X ≥ 16 \| Bin(50, 0.20)) | 0.030803422782047604 | `INSTRUMENT_ALPHA = 0.0308034228` → 0.0308 | **exact to 10 dp** |
| Instrument power (design) | P(X ≥ 16 \| Bin(50, 0.40)) | 0.9044982926444817 | 0.904 | **exact** |
| Instrument power at 1.6× | P(X ≥ 16 \| Bin(50, 0.32)) | 0.5530285806271841 | `INSTRUMENT_POWER_AT_1P6X = 0.553` | **exact** |

**Are the critical values the right ones?** Yes — each is the *minimal* c meeting α ≤ 0.05, so the design is
not quietly conservative:
- n=20: c=7 → α = 0.08669 (fails 0.05); **c=8 → α = 0.03214** (first to pass).
- n=50: c=15 → α = 0.06072 (fails 0.05); **c=16 → α = 0.03080** (first to pass).

**The superseded triples also reproduce**, which matters because §10's RRV-07 row still quotes them:
n=35/c=12 → α = 0.034357, power@0.40 = 0.804825 (published 0.0344 / 0.805 ✓);
n=100/c=28 → α = 0.034152, power@0.32 = 0.832450 (published 0.0342 / 0.833 ✓).
So the 35/100 design was also arithmetically sound; the re-set to 20/50 was a power/n trade, not a repair.

**Does the code enforce the numbers the plan states?** The constants at
`platform/python-sidecar/services/ka_sangam/exposure.py:29-44` are exactly 20/8/0.0321426631/0.868/0.50 and
50/16/0.0308034228/0.904/0.40 with `NULL_RATE = 0.20`, and the D-2 gradient at `:46-47` is 10.0/20.0 as
ruled. The gate evaluator at `:363-380` requires **both** `hits >= critical` **and** `p_value <= alpha`, and
returns `PROVISIONAL_INSUFFICIENT_N` below n (`:377`) — it does not silently pass a short stratum.

**Is the test a real detector, or a tautology?** Real. `tests/l3/test_ka_sangam_e6_exposure.py:58-70`
recomputes α from `_binomial_sf(CRITICAL, N, NULL_RATE)` and power from `compute_power(N, CRITICAL,
ALTERNATIVE)` and compares each to the published constant. If any member of a triple drifted, the test
fails. I confirmed by running it (24 tests in that file, all pass). One honest limit worth recording: the
test enforces *internal consistency of the triple*, not the literal values 20/8/50/16 — a future edit that
changed n and recomputed α consistently would still pass. Pinning the literals would close that. Given the
K2-01 precedent (a miscomputed α), this is the right guard in the right place; it is simply one notch
weaker than it could be.

**One scoping fact the numbers do not say on their own.** The gate evaluators that use these constants —
`build_stratum_outcome` and `evaluate_instrument_outcome` — have **no production caller**. The writer
imports only `build_scan_coverage` and `compute_exposure_manifest` (`ka_sangam.py:37`, called at `:615` and
`:672`). This is by design and honestly documented (`exposure.py:9-11`: "outcomes are evaluated later from
real outcome data, not invented by the writer"), and it matches the L5 STRUCTURAL-mode doctrine. But it
means the E6 gate at this tip is **implemented and tested, not operative**. Nothing at `204b003ea` can emit
`EMPIRICALLY_EVALUATED`, which is the correct state — I record it so the gate's status is not overread.

---

## 3. Evidence suite — reproducibility and results

**I read `RUN_ALL.sh`, `MANIFEST.txt`, `_common.py` and every script I ran before running anything.** All 21
scripts are read-only, assertion-based, and need no database. I did **not** execute `RUN_ALL.sh`, because it
writes a timestamped `OUTPUT_*.txt` into the repository working tree and my mandate permits no file
creation outside my report and scratch. I ran each script individually instead, positive and `NEG=1`, exactly
as the runner would, capturing exit codes only.

**A reproducibility defect blocked the first attempt.** `_common.py:6-7` resolves the repo root by walking
ancestors until it finds a directory literally named `readiness`:

```
ROOT = pathlib.Path(__file__).resolve()
while ROOT.name != 'readiness' and ROOT.parent != ROOT: ROOT = ROOT.parent
```

The reviewed worktree has no such ancestor, so `ROOT` degrades to `/` and `SIDECAR` becomes
`/platform/python-sidecar`. Every script dies with `FileNotFoundError: /platform/python-sidecar/...`. The
author's recorded runs were produced from `/Users/Dev/madhav-l3/readiness/` (visible in the output headers
of `OUTPUT_2026-09-24T124227.txt`), where the walk happens to succeed. **The evidence suite as committed is
not runnable from a clean clone, or from any checkout not named `readiness`.** For a gate whose premise is
independent verification, that is a material defect — see Finding A3. Because `Path.resolve()` follows
symlinks, a symlink farm does not work either; I had to physically copy `platform/python-sidecar`,
`platform/supabase/migrations`, `platform/scripts/seed` and the evidence directory into a scratch tree
rooted at a directory named `readiness`, and use the interpreter at
`/Users/Dev/madhav-l3/readiness/platform/python-sidecar/.venv/bin/python` (the reviewed worktree carries no
`.venv`).

**My independent result, all 21 scripts:**

| Script | positive | NEG=1 | verdict |
|---|---|---|---|
| S1, S2, S3, S4, S5, S6, S7, S9, S10, S11, S12, S13, S14(r5_harness), S15, S16, S17, S18, S19, S20, S21 | **0** | **1** | pass, negative control genuinely fails |
| **S8_saturn_loop_oracle.py** | **3** | **3** | **NOT RUN** — Swiss `.se1` files absent on this host; requested flags 65794, returned 65860 → Moshier; the script refuses to act as a geometric oracle on Moshier and exits `NOT_RUN(3)` |

**This reproduces the author's recorded 20/21 exactly**, including S8's reason. The author's framing is
honest on two counts I checked specifically: the MANIFEST was *not* relaxed to accept exit 3 (which would
have turned "cannot verify" green), and commit `4ff37343d`'s message states "Suite is 20/21 + 1 NOT_RUN, not
SUITE-PASS." Note, though, that the runner's own verdict line in the latest recorded output reads
`scripts run: 21; verdict: SUITE-FAIL` — the harness's formal verdict at this tip is SUITE-FAIL, and
"20/21" is a prose gloss on it. Both statements are true; only the first is the instrument's.

**S8 is not runnable here and I did not force it.** No hosted service, no database, and no production write
was attempted at any point in this review.

**One evidence-script observation.** `S21_kernel_fields_persisted.py` opens
`platform/supabase/migrations/1088_…`, `1089_…`, `1090_…` (`:61-62`, `:91`) — correct paths — but its
proposition *names* still read "migration 1085 is additive only" (`:126`) and "migration 1086 ships identity
and frame TOGETHER" (`:140`), the pre-renumbering numbers. Cosmetic; the assertions test the right files.

**Pytest.** I ran the ka_sangam set independently: **224 passed** across
`test_ka_sangam_{e6_exposure,r6_kernel,r1_r4_repairs,r2_intersection,e5_episodes,e4_typed_conditions,synergy_fixes,a3_fixes}.py`
and `test_ka_sangam.py`. The full `tests/l3` run gave 1633 passed / 8 failed / 41 skipped; **all 8 failures
are artifacts of my partial copy, not of the branch** — seven in `test_ka_gochara_resonance.py` assert on
`platform/migrations/459_gochara_resonance_map.sql`, a directory I did not copy, and
`test_m3_graha_sancara_defects.py` fails on `ModuleNotFoundError: No module named 'temporal'`, a
`platform/scripts` package I did not copy. I did not run the full suite in a complete tree, so **I cannot
certify the full `tests/l3` set green at this tip**; I can certify the ka_sangam subset.

---

## 4. Migration notes (read, not resolved)

All five are **additive only, idempotent, and non-destructive**. No `DROP`, no `ALTER … TYPE`, no data
rewrite, no `DELETE`. Every column uses `ADD COLUMN IF NOT EXISTS`; every index `CREATE INDEX IF NOT
EXISTS`; the one constraint (`1090`) is wrapped in a `DO $$ … IF NOT EXISTS (SELECT 1 FROM pg_constraint …)`
guard. Nothing in them would refuse on a re-run. Column COMMENTs are unusually accurate and several record
the *gaps* rather than papering them (`1089`: `ephemeris_backend='unasserted'`, `house_frame='unavailable'`).

- **1071** — `target_provenance`, `availability` JSONB. Clean.
- **1072** — `is_episode`, `episode_uuid`, `episode_children`, `episode_hull`, `perfected`. Clean; the
  `perfected` COMMENT correctly describes horizon-truncated and approached-never-perfected cases.
- **1088** (renumbered from 1085) — the six R-6 kernel columns + composite index. Its header records the
  renumbering, the competing claim, the resolution rule ("an applied migration keeps its number, otherwise
  first claim holds"), and — importantly — that renumbering was safe *because the file is unapplied*. It also
  states plainly what it deliberately does **not** ship (`contact_uuid`, blocked on R-3) rather than
  shipping a NULL column. This is correct practice under CLAUDE.md §N.4's "never edit a migration after it
  has been applied."
- **1089** (from 1086) — `contact_uuid`, `convention_frame`, `identity_state` + partial index. Ships identity
  and frame together, with the reason stated.
- **1090** (from 1087) — `comparable_with` + four-value CHECK matching the layer enum. Its header records a
  substantive correction to the layer binding (that `comparability_class` is a grouping key and
  `comparable_with` a relation, and that renaming one into the other would have destroyed the grouping).

**Numbering, against `origin/main` at this SHA.** No duplicate: `origin/main` carries nothing at
1071, 1072, or 1080-1095 (its highest is `1079_nirmana_l0_transit_rules_description_truthfulness.sql`).
Pre-existing duplicate prefixes elsewhere in the tree (195, 206, 370, 484) are inherited from main, not
introduced here.

**Two things I report and do not resolve:**
1. The branch **does not contain main's 1075-1079** — it forked before they landed. Numbers 1073-1087 are an
   unused gap on this branch. The CI MIG-1 guard (`platform/scripts/ci/migration_number_guard.ts`) hard-fails
   new duplicate numbers, and the branch's own commit `fee130d2d` withdrew an earlier "collision is benign"
   conclusion. **The guard must be re-run after a rebase onto current main**; I cannot settle collision risk
   from this tip alone, because 1088's own header states 1071-1084 "were claimed across four branches" and I
   can see only main and this tip.
2. `1088`'s header says the runner "keys on filename, not number, but the ordering tie-break is lexical
   within a number." I did not verify that claim against the runner; it is the author's, unchecked.

---

## 5. Additional findings not covered by any RRV

Ranked by severity.

**A1 — HIGH. The ashtakavarga completeness receipt has no producer anywhere in the repository; the E2
verdict is therefore permanently unavailable on modes A/B in production.** This is the live consequence of
RRV-01's absence and is a textbook §N.8 Earned-Signal defect.
`services/ka_sangam/engine.py:217` gates the entire C7 verdict on `if canon not in
ctx.ashtakavarga_computed_planets: return None`. That set is populated only from
`fact_category = 'ashtakavarga_completeness_receipt'` rows (`ka_sangam.py:1272-1286`). A repository-wide
grep finds **no writer, migration, seed or script that emits that category** — the only occurrences are the
ka_sangam reader and the S3 evidence script that checks the reader reads it. So on every chart,
`ashtakavarga_computed_planets` is empty, `_c7_ashtakavarga_verdict` returns `None` for every planet, and
`ka_sangam.py:1060-1063`'s `ashtakavarga_transit_potency` — computed as `verdict == 'support'` — is `False`
on every mode-A/B row forever. The file's own comment at `ka_sangam.py:1300-1306` documents the *identical*
defect class in the `bg_transit_rules rule_type='vedha'` bug it just repaired ("0 rows ever matched … the
NECESSARY-side veto was permanently neutral … on every chart, forever"). The new code reproduces the shape
of the bug it fixed, one table over.
*Mitigating, and I want to be fair about it:* this is **not a regression**. On `origin/main`,
`_c7_ashtakavarga_potency` ends in an unconditional `return None` (held pending a HOUSE/SIGN frame
adjudication), so C7 was already dark. The branch genuinely *resolves* that frame question by reading
sign-keyed `ashtakavarga_bindu_sign` facts, which is real progress, and mode D's `_sav_verdict`
(`engine.py:241`) is **not** receipt-gated and does produce live verdicts. The gap is that E2's headline
elevation — "verdict-based, not raw bindus" — yields zero live verdicts on the modes that matter most, and
the plan §10 disposition that would have avoided this (deriving the receipt from `graha_position` facts L1
*already serves*) is precisely the one not implemented.
*What I do not claim:* I ran no database query. "Zero live rows" is a code-path conclusion from the gate at
`:217` plus the absence of any producer, not a measured row count.

**A2 — MODERATE. A registry cycle across two sources of truth, disclosed but unresolved, and this branch
re-seeds the affected row.** `platform/scripts/seed/asset_registry_seed.ts:2316` now declares
`ka_sangam.depends_on` including `ka_vedha_gochara` (a correct, honest addition — C11 really does read
`kala_vedha_gochara`). The comment above it (`:2310-2315`) discloses that
`platform/supabase/migrations/224_l2_l5_id_underscore_rename.sql:85` sets `ka_sangam.depends_on =
ARRAY['ka_kalasutra']`. I verified both ends: migration 224:85 is exactly that, and `ka_kalasutra`'s own
seed entry (`asset_registry_seed.ts:2294`) declares `depends_on: ['ka_yojaka', 'ka_sangam', 'bo_laksana']`.
So the two sources describe a genuine `ka_sangam ↔ ka_kalasutra` cycle. The author says "not live (this seed
wins)" and asks that 224:85 be retired — but the disposition is a comment, not a change, and whichever
source runs last wins. This is a GA.1-class registry disagreement under CLAUDE.md §B.8. **Reported, not
resolved**, per my mandate.

**A3 — MODERATE. The evidence harness is path-coupled to a directory named `readiness`** (`_common.py:6-7`),
making the suite unrunnable from the reviewed worktree or any clean clone. Details and my workaround in §3.
For a gate that exists to let an independent party re-derive the author's evidence, an instrument that only
runs at the author's path is a governance defect in the instrument, independent of whether its results are
correct. They *are* correct — I reproduced them — but only after reconstructing the author's directory
layout.

**A4 — MODERATE. `RUN_ALL.sh`'s negative-control check is vacuously satisfied by a NOT_RUN script.** The
check is `if [ "$nrc" -eq 0 ]; then SUITE-FAIL`. A script exiting 3 under `NEG=1` — as S8 does — passes,
having demonstrated nothing about its detector's sincerity. This is RRV-15's own concern reappearing in the
runner rather than in a script, and it is currently live for exactly one script.

**A5 — MODERATE. §10 contradicts §0R inside the governing plan.** §10's RRV-02 row states "N-7 status at
2026-09-23: **UNRULED** (verified by tree-wide search)." §0R M-3 carries a dated in-place correction saying
N-7 *was* ruled ("the search covered the wrong branch"). §10 was never updated. A reader taking §10 as the
binding disposition record gets the retracted fact. Compare RRV-06's row in the same table, which *does*
carry its `[RULED …]` correction inline — so the mechanism for fixing this exists and was simply not applied
here.

**A6 — MODERATE. Three documents disagree on RRV-06's E6-numerator ruling, and the code implements
neither.** §10 RRV-06 says the inclusion is `[RULED 2026-09-23 … INCLUDED, `perfected` a mandatory reported
covariate]`. `SANGAM_STAGE3_STATE.md:122` says "E6 numerator inclusion of aborted approaches **NOT ruled** —
recorded open … until then excluded." `SANGAM_STAGE3_STATE.md:285` says the perfected/unperfected split per
stratum is "not yet implemented." The code agrees with the third: `exposure.py`'s stratum key and
`StratumOutcome` carry no perfected dimension. So a covariate the governing plan calls *mandatory* is
reported nowhere. Because E6 is not operative (§2), nothing is currently mis-scored — but the disagreement
must be settled before an E6 numerator is defined, and §10's text should not be the version left standing
if it is the wrong one.

**A7 — MINOR. An evidence detector was loosened by the party whose change had broken it, in the same pass.**
Commit `4ff37343d` relaxed two `S20` propositions from exact-expression pins to behavioural patterns
(`from services\.ka_sangam\.exposure import .*compute_exposure_manifest`;
`notes=(manifest\.to_json\(\)|_notes_with_coverage\()` plus a new `'exposure_manifest':` key assertion). On
the merits I judge the change **correct** — the old pin would have forbidden a legitimate refactor, which is
the S3 defect class inverted, and the replacement still asserts the manifest reaches notes under a named
key in both substeps. I record it because it is structurally the exact hazard D-K names: the detector, the
change that tripped it, and the certification that the loosening was benign all came from one party. It
wants a second pair of eyes, which it has now had.

**A8 — MINOR. Two files outside the ka_sangam surface were modified, and I could not locate the stage-3
`may_touch` to check them against.** `services/ka_dasha_kala/{service,intersection}.py` changed (R-2
intersection oracle) and `pipeline/orchestrator/writers/ka_taranga.py` changed (E5/RRV-05 taranga unit).
Both are substantively justified by the plan. But `SANGAM_STAGE3_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md`
contains **no `may_touch`/`must_not_touch` block** (grep: no match), while §10's RRV-01 disposition reasons
explicitly from one ("outside `may_touch`, frozen L1 writer surface"). CLAUDE.md §I requires the declaration
and fails a handshake with an empty `must_not_touch`. The scope *substance* is clean (see below); the scope
*declaration* is not locatable at this tip, so I grade the authorisation of these two files
**UNVERIFIABLE**, not violated.

**What the author did NOT claim, checked deliberately — and found clean.** I looked for places where the
code silently does something the plan forbids:
- **D-4 (D30 held):** no `D30`/`secondary_dosha`/`varga_30` symbol exists in the engine or writer. No D30 row
  can ship, so the hold is satisfied at the strongest possible level and its falsifier is not yet owed.
- **M-2 ("6/8/12 inversion does not ship"):** no such inversion in the engine. Clean.
- **Frozen surfaces:** `git diff --name-only origin/main...HEAD` matches no `transit_search`, no `ga_writers`,
  no `bg_*`, no `l0_*`, no `ph_*`/`mi_*` writer. Verified, not taken on trust.
- **FROZEN orchestrator contract (§N.2):** `ka_sangam.py:261-262` is `@register('ka_sangam')` on a
  `WriterBase` subclass with `plan_substeps` (`:275`) + `run_substep` (`:500`); no `.commit()`, `.close()`
  or `asset_throughput` write anywhere in the writer. Conforms.
- **Idempotency (§N.3):** per-chart delete-then-insert at `:482`, `:575`, `:585`, `:642`, scoped by
  `chart_id` (× `horizon_tier`/`signal_id`). Conforms.
- **The reverted breach:** genuinely reverted. `ga_strength_writer.py` is byte-identical to `origin/main`.

---

## 6. What I could not verify

- **The D-K second instrument.** An isolated Kimi K3 pass in a detached worktree was NOT run by me and I did
  not see its output. My verdict rests on one instrument only. (I did read the *earlier* Kimi reconciliation
  of the L1-edit breach, `1ef326494` / `KIMI_K3_RECONCILE_SANGAM_L1EDIT_v1_0.md`, and note only that it
  reached the RRV-01 conclusion independently of me and before me; I formed my finding from the repository
  first.)
- **Any runtime or database behaviour.** No database was contacted, by MCP or otherwise. Every claim about
  production behaviour in this report is a code-path conclusion, explicitly flagged as such (A1).
- **S8's geometric oracle.** NOT RUN — the Swiss `.se1` files are absent on this host; the script correctly
  declines Moshier. Its assertions about Saturn's 2026-2029 retrograde loops are therefore unverified by me.
- **The full `tests/l3` suite in a complete tree.** I ran it in a partial copy; 8 failures are my copy's
  artifacts (§3). The 224 ka_sangam tests I do certify.
- **Migration collision risk after rebase.** Settleable only against current `main` plus the other four
  branches 1088's header references; I can see main and this tip.
- **The stage-3 `may_touch` glob set** (A8) — not present in the execution prompt at this tip.
- **RRV-14's future SPEC** and any E1/E3 behaviour — not built, correctly gated, unverifiable now.
- **Whether `mi_adhilepa`/`ph_nimitta` will actually bind `contact_uuid`** — the enabling column now exists;
  the consumer packets are future work by design.
- **`1088`'s claim that the migration runner keys on filename rather than number** — the author's, unchecked.

---

## 7. Amendments this verdict names

`CONFORMS_WITH_AMENDMENTS` means the build substantially conforms and these should be discharged before it
is merged as a record of what was done. I record them; I do not authorise anything.

1. **Correct plan §10's RRV-01 row** so the governing disposition table states what is true: the stage-3-side
   join was not implemented, the receipt route in code is the producer-column route, and B-4 is open. The
   mechanism for an inline correction already exists in that table (RRV-06 uses it). Today §10 reads as a
   discharged amendment and the correction lives only in a state file and an evidence-script comment.
2. **Resolve A1 on its merits**: either implement the dispositioned `graha_position` join (which would light
   C7 from data L1 already serves), or state in code, beside the gate at `engine.py:217`, that the receipt
   has no producer and C7 is dark pending B-4 — so the next reader does not mistake an unavailable signal
   for a measured one.
3. **Correct §10's RRV-02 N-7 status** (A5) and **settle RRV-06's numerator ruling across the three
   documents** (A6).
4. **Resolve or retire migration 224:85** (A2), since this branch re-seeds the row it contradicts.
5. **Make the evidence harness path-independent** (A3) and **fail a NOT_RUN script's negative control
   explicitly rather than vacuously** (A4).
6. **Re-run the MIG-1 guard after rebasing onto current main** (§4), and locate or restate the stage-3
   `may_touch` (A8).

---

*Reviewed at `204b003ea` only. The branch is live; nothing after this commit is covered. No file in the
repository was created, edited, committed, pushed, or rebased by this review; no ledger or SESSION_LOG was
appended; no PR was touched; no migration was run; no database was contacted.*

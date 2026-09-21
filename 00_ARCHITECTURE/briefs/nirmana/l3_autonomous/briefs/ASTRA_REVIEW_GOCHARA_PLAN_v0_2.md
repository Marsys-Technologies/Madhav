---
artifact: ASTRA_REVIEW_GOCHARA_PLAN
version: "0.2"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewed_revision: "5d8252dbefc053f9faa92aab693ad46310e0c5c5"
reviewer: "Codex — independent adversarial review"
date: "2026-09-20"
verdict: PROCEED_WITH_AMENDMENTS
reviewed_plan_sha256: "964b7f9ec13ea5678f8948262cd74fec9b84d69bf74da1f58711ce4c6b581921"
review_request_sha256: "acc4cb1b98a9716225a2d53aa460b14277ead52a094f4e370871b14b2802945e"
authority: "Review only; this artifact authorizes no implementation, build, migration, database write, publication or hold release."
---

# Independent adversarial review — Gochara family elevation v0.2

**Verdict: PROCEED WITH AMENDMENTS on a bounded producer prototype. Do not execute WP1–WP3 with their present exit gates.** The proposed direction addresses real defects, but its two principal shortcuts are not established: importing W2G and Kshetra S0 does not supply a complete, correctly timed contact kernel; and gathering a single dated event list does not reproduce all the existing primitives. The first slice must establish its input, identity and coverage contracts before either optimization. It must finish as a measured prototype, not as proof of the complete plan or delivered product value.

The review materially strengthens F3, F15 and the central F17 claim. It also corrects the current-state assertion in F10, the scope of the saturation evidence, the interpretation of the era-window history, and the assumption that the surrounding consumers need almost no changes. There are enough defects in the inputs and adapters that a faster kernel, by itself, could deliver a more confidently wrong answer.

## Review basis and limits

Worktree: `/Users/Dev/madhav-l3/integration`; branch: `codex/madhav-l3-claude-code`; HEAD is the full revision above. The untracked request, plan, scripts and captured output were read from disk. All E1–E7 were rerun with the specified Python environment and bytecode writing disabled. Additional numerical counterexamples were run in memory. Three bounded, read-only independent audits covered geometry, contracts and consumers; this reviewer reconciled their findings and is the sole writer of this review.

The canonical bootstrap and mandatory reading sequence were followed within the user's explicit review scope. Product v3.0, the approved L3 strategy, execution authority matrix, campaign dimensions/stream rules, current campaign state, the Gochara discussion prompt and the cited historical decisions were inspected. The campaign plan remains a proposal where its own status says so; it cannot supersede the approved strategy or reserved native rulings.

Existing live access was available through an already-running database proxy. The aggregate queries used explicit `REPEATABLE READ READ ONLY` transactions with `transaction_read_only=on`, statement timeouts and rollback. Snapshots were taken on **2026-09-20 between 16:02 and 16:14 UTC**. No credentials, narratives or individual chart facts are reproduced. Multiple snapshots are reported as such; they are not one atomic audit of the whole platform. No deployed revision was inferred from the database. No production build, migration, data write, PR, source change or extra evidence file was made. This review is the only file written.

Citation shorthand below is relative to that verified worktree:

- `PY/` = `platform/python-sidecar/`.
- `APP/` = `platform/src/`; `MCP/` = `platform-mcp/src/`.
- `MIG/` = `platform/migrations/`; `SUP/` = `platform/supabase/migrations/`.
- `ARCH/` = `00_ARCHITECTURE/`.
- `PLAN` = the reviewed `GOCHARA_FAMILY_ELEVATION_PLAN_v0_2.md`; `E1`–`E7` = its sibling `evidence_gochara/` scripts.
- `STRATEGY` = `ARCH/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md`.
- `EXECUTION` = the corresponding `MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md`.
- `CAMPAIGN` = `ARCH/briefs/nirmana/l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md`.

File citations refer to inspected source at the reviewed revision. Executed results below are observations, not claimed universal bounds.

## Top five risks, ranked by delivered quality first

| Rank | Risk and consequence | Required amendment |
|---|---|---|
| 1 | **Incorrect or incomplete geometry is presented as exact.** W2G drops close stations, daily knots miss physical true-node excursions, S0 loses already-active episodes and its noon/time conversion is inconsistent. The proposed independent Swiss comparison also mixes sidereal conventions. Contacts can disappear or receive the wrong timestamp while a root solver reports a tight tolerance. | Resolve the complete astronomical convention and time contract; prove topology/coverage separately from positional error; add adaptive direct calculation or explicit incomplete coverage where the substrate cannot prove completeness. See F3/F4 and design review. |
| 2 | **Unqualified inputs become persuasive testimony.** The served v3 path really uses fixture kakshya boundaries, and the first proposed new mechanism, W21, treats rule thresholds as chart bindus. Removing the Moon or adding dwell/separation weights before source qualification can substitute a new unsupported model for the old one. | Repair input provenance, missingness and duplicate evidence first. Keep Moon contacts available. Audit each mechanism's actual operands before even testimony-only admission; qualify each interpretive change. See F9/F14/F15 and R4/R5. |
| 3 | **Stage E can falsely certify equivalence.** The PoC tests activity rather than complete λ, includes inactive primitive families and misses another window-relative primitive: sign-only drishti residence. Its fixture λ is identically zero. | Use non-vacuous, per-primitive and per-factor oracles; represent spans as spans; separate exact legacy reproduction from deliberate corrections. See F2 and PoC. |
| 4 | **Correct new rows disappear or lose meaning on delivery.** The MCP coverage branch treats `4.0` as v1; checklist/D8/D9 paths discard the proposed evidence fields; the prospective signature cannot gain contact IDs without changes. Authority filtering alone does not preserve meaning. | Make coverage, typed fields, identity, truncation and managed consumer replay first-class acceptance work before promotion. See ecosystem review and R8/R10. |
| 5 | **A generation label is mistaken for a reproducible publication and a rollback plan.** Rebuilding within `4.0` can mutate the authoritative dataset. Current protection is absent; cockpit Clear is an omitted destructive writer; retained archives do not cover all current v1 IDs. | Use immutable publication identities and complete manifests, an atomic publication switch, request-pinned input vectors, an authorized history policy and a verified full restore. See F17, R6 and storage review. |

Efficiency remains important, but none of these failures is repaired by a better per-contact timing number.

## A. Findings F1–F17 and the PoC

### F1 — PARTLY

**Confirmed:** the current scalar evaluation path repeatedly gathers primitives for each target over overlapping windows. `PY/services/gochara_v3/interval_solver.py:116–136` calls the vector engine with one JD; `PY/services/gochara_v3/engine.py:1114–1137` repeats primitive searches by target. E2 reran at approximately **64 ms/evaluation**; E4 measured **57.5 ms** in primitive search, with kakshya **34.33 ms / 59.7%** of that search total. This is a credible optimization target.

**Not established:** 620 evaluations per substep is a workload estimate, not an invariant. Peak/refinement work depends on class shape and results. The two-target fixture does not establish linear cost in the count of arbitrary production targets. Target kinds have different resolution and search behavior, geometry can be shared, and negative weights are not equivalent to additional positive activity. The live chart has **14–40 targets per class**, not an observed T≈18; there are **765 rows across 27 classes**, including 31 negative-weight rows. Applying 1.35 h × T to those rows would still be a model, not a measurement.

There are recorded completed asset executions of **239.715211, 613.485078 and 3491.560239 seconds**. Their completion state does not establish a cold, full 270-substep rebuild; see the live appendix. The approximately 25-hour anecdote therefore remains unassigned. Do not state that the century writer is its demonstrated explanation.

**Change needed / evidence that would change this judgment:** a matched, full-scope profile with cache/resume state, input vector, class/target composition, completed partitions, SQL and write costs, as required by STRATEGY:236–256. Keep the current numbers as fixture unit costs.

### F2 — PARTLY

The intended legacy algebra is largely discrete: a fixed event strength contributes inside a ±5-day selection window; permission uses Boolean states; Tara and nodal aspects use discrete sign/nakshatra states; Vedha is an interval-overlap gate. There is no separation-continuous contact envelope in the current activity formula. See `PY/services/gochara_v3/engine.py:615–635,821–898,1157–1245`.

However, **“one immutable dated event list, with all breakpoints obtained by event time ±5 days” is false for the full current input domain**. Several primitives calculate a state over the requested interval and place a representative timestamp at that interval's boundary. F16 is not the only instance.

Independent counterexample: resolve a valid sign-only bhava target `7` with `target_longitude_deg=None`, `target_sign='Libra'`; evaluate Jupiter's rasi drishti from Gemini. With `a = 2026-01-01 12:00 UT` and `t = a + 30 d`, `drishti_contact(..., a−5, a+185, planets=['Jupiter'])` returns one already-resident event at `a−5`. Evaluating the local `t±5 d` interval returns the resident event at `a+25`, and activity **0.45**. Filtering the once-gathered global event list to that local interval returns no event and activity **0.0**. This is the production-supported sign-only target path, not a made-up cusp: `PY/services/gochara_intensity/enrichment.py:50–68`; dispatch and resident timestamp logic in `PY/services/gochara_grammar/primitives.py:290–325,394–452`.

Permission also uses interval-sensitive sign-occupation results (`primitives.py:496–560`; `engine.py:1334–1387`). It needs its own state-transition representation, not the assumption that the activity event list suffices. Vedha's date-rounded evaluation-window overlap similarly needs the actual boundary convention included.

**Amendment:** state a qualified algebra for each factor, with point events, residence spans, interval overlap, boundary inclusivity and evaluation failures explicitly represented. Numerical search jitter also makes unconditional floating-point “exactness” stronger than the evidence supports. A complete, non-vacuous λ comparison over all input kinds would change this finding.

### F3 — CONFIRMED

No ayanamsha conversion was found between sidereal natal targets and the W2G tropical arcs. `PY/services/gochara_intensity/enrichment.py:136–151` reads sidereal longitude; `PY/services/w2g/materialize.py:239–251` passes the resolved degree through; `PY/services/w2g/db_source.py:35,178–206` supplies tropical positions/arcs; `PY/pipeline/orchestrator/writers/ka_gochara.py:304` constructs that path.

E1 reproduced approximately **763 days for Saturn, 349 days for Jupiter and 33 days for Mars** between the wrong-frame result and the corresponding sidereal contact. This is a real defect. Current live authority contains only `3.0` for its two explicit rows, so the queried generation-2.0 population is not ordinary authoritative output. That containment does not prove there are no direct diagnostic readers.

The proposed explanation of historical MR-20 remains an inference until its exact comparator inputs are replayed. Correcting the zodiac is also not enough to establish agreement between the repository's two sidereal conventions; see F4.

### F4 — PARTLY; the claimed completeness is refuted

Useful reusable pieces exist. They are not two already-correct halves waiting only for a frame term.

1. **Close stations are deliberately discarded.** `PY/services/w2g/arcs.py:74,246–260` merges derivative roots within 0.25 days. For the cubic `100 + (t−1.5)^3/3 − 0.01(t−1.5)` at daily knots 0,1,2,3, stations are 1.4 and 1.6. The code retains only 1.4. The target 100° has three roots at **1.326794919, 1.5, 1.673205081**; `find_contacts` returns only **1.326794918**. Appendix C gives the complete reproducer. Derivative-root exceptions also silently become an empty list (`arcs.py:238–241`), which cannot support a completeness assertion.
2. **This is not only a synthetic pathology.** An independent Lahiri true-node experiment over 1984-02-05 to 2084-02-05 found **5,446** derivative roots before coalescing and **5,375** retained, including 71 close pairs. Direct Swiss evaluation around **1986-07-14 22.091089737 UT to 1986-07-15 02.003070988 UT** shows a prograde excursion of only **0.0476900013 arcseconds**, from 2.017949976012846° to 2.017963223235430°. For target **2.017956599624138°**, direct roots are JD **2446626.327730091, 2446626.501932548, 2446626.676502364**. Six-decimal daily knots passed through the existing arc solver return one root, **2446626.705282025**, even with 10⁻⁶-arcsecond root tolerance. Solving the interpolant more accurately cannot recover topology absent from it.
3. **Wrap tangency is lost.** Daily longitudes `[357.75, 359.75, 359.75, 357.75]` have a spline maximum at 360°; a target 0°, orb 1° query returns no contacts. Normalizing the target to zero excludes an arc ending at 360° (`arcs.py:373–382`). Explicit seam ownership and endpoint/tangent handling are needed.
4. **S0 drops a whole already-active episode.** An orbit that stays between 100° and 100.3° over `[0,3]`, target 100°, orb 1°, returns `[]`. The state machine initializes “inside” but emits no truncated entry, while episode assembly requires one (`PY/services/ka_kshetra/stage0_kinematics.py:339–354,366–395`). The error also affects horizon joins; it is not the disclosed double-root limitation alone.
5. **S0's time coordinates are inconsistent.** It reads noon positions and computes noon ayanamsha, but assigns integer date differences as `t_days` (`stage0_kinematics.py:659–668`); timestamp conversion/serialization uses the midnight origin (`:501–503,812`). A 2026-01-01 noon Moon input was emitted at midnight, when the direct position differs by **7.511133595°**. Reusing this I/O unchanged would move every contact by half a day.
6. **The “correct frame” is not yet a common convention.** L0/S0 subtract `get_ayanamsa_ut` from tropical longitude (`PY/brahmagyan/l0_ephemeris.py:208–210`; S0:607–624), while `PY/pipeline/transit_search.py:241–270` uses `FLG_SIDEREAL`. Direct comparisons for the Moon differ by **+5.522253″ on 2026-01-01 noon**, **−16.518028″ on 2020-01-01 noon**, and **−14.851077″ on 1984-02-05 noon**. Pin flags, apparent/mean and nutation conventions and node identity before choosing a reference. “Swiss agrees” is meaningless if the two sides request different quantities.
7. **Stored speed is not automatically a valid sidereal Hermite derivative.** S0 passes stored tropical speeds through unchanged (`:657–668,987–991`), without the time derivative of the frame conversion. Separately, L0 sets Ketu longitude to Rahu+180° but negates Rahu's speed (`l0_ephemeris.py:286–292`); that longitude construction has the same derivative as Rahu, not its negative. `transit_search.py:253–256` preserves the derivative. Validate or derive the new interpolant's slopes; this review does not authorize an L0 correction.

**What would change this judgment:** a declared convention and time origin; a complete candidate-generation argument without station coalescing or silent failures; physical node/tangent/seam/horizon fixtures; and either an adaptive oracle-backed fallback or an explicit “not proved complete” state when daily data cannot support the claim. No changes to the frozen hubs are required by this review itself.

### F5 — CONFIRMED

`PY/services/ka_vedha_gochara/writer.py:86–87` uses −60/+400 days. `PY/services/gochara_v3/engine.py:615–622` describes and uses a factor of 1.0 when no row overlaps. Missing coverage and evaluated-clear therefore collapse. All **380** populated activity decompositions in the canonical served-generation snapshot also had `quality_gates=1.0`; that does not establish that all 380 should have been suppressed, but it does not demonstrate century-wide evaluation either.

A century-complete row set is necessary but insufficient: retain school/source, evaluated applicability, missing coverage and double-counting checks against Vighnakara. Prove a covered-clear case, covered-inhibited case and uncovered case remain distinct through serving.

### F6 — CONFIRMED

The stated rule requires the Moon at ingress (`PY/services/ka_moorti_nirnaya/logic.py:9–20`). The writer detects daily sign runs and reads the Moon's nakshatra on the run's starting **date** (`writer.py:227–240,267–270`). It does not solve and evaluate at the actual ingress instant. Additionally, it subtracts one reference-date ayanamsha across the requested daily horizon (`writer.py:138–160,207–209`). Exact ingress work must correct or qualify both effects.

The population error rate is still unmeasured. A Moon-nakshatra boundary close to ingress is the necessary counterexample, not just a finer timestamp on an unchanged classification. Truncated-at-start runs need an honest state if the actual preceding ingress was not searched.

### F7 — CONFIRMED

PATH-A drops time of day and returns the day's cached position (`PY/services/ka_graha_sancara/engine.py:218–223,250–258,393,413–419`). PATH-B can calculate the requested instant. The date-based cache lookup occurs before the `force_live` decision (`:399–407`), so the precedence itself needs a regression case. Do not treat this service as an exact oracle merely by setting a flag.

The successor should declare whether an answer is a snapshot, interpolated instant or direct calculation and use a cache key consistent with that meaning.

### F8 — PARTLY

The engine directly wires W23 and W30 (`PY/services/gochara_v3/engine.py:100–101`), while eight of the ten ordinary W21–W30 modules are not called there. But that is **not the same ten** as the admitted-mechanism register: `mechanism_register.yaml:69–248` includes W27a/W27b/W27c and excludes W30. Its ten-entry admitted set therefore has **nine** unwired entries on this engine path. `PY/scripts/kala_admission/w44_weight_fitting.py:158–168` also has stale wiring metadata.

More importantly, “coded” does not mean ready to wire. `ClassContext` lacks the Kota/annual inputs those modules expect (`PY/services/gochara_v3/context.py:152–186,202–274`; `mechanisms/w25_kota_chakra.py:163`). W21 uses a threshold as a bindu proxy; see R5. Reconcile module inventory, admitted registry, context fields, actual calls and qualifying tests as separate denominators. The plan's categorical “cited, coded, tested” sentence is too strong.

### F9 — CONFIRMED for absent L2 binding; narrower than the wording suggests

The resonance writer uses ontology plus chart-specific L1 facts, not qualified L2 structures (`PY/services/ka_gochara_resonance/writer.py:1–120,367`). Thus it is personalized, but not at the structural level product §12.2 requires. Exactly **five classes** are explicitly designated provisional in the inspected writer (`:159–181`); do not turn that into an unspecified “many of 27” without an ontology audit.

There are additional fidelity problems: target parsing strips a lord qualifier such as `afflicted` (`:245`), and `setdefault` retains only the first source root when a target resolves more than once (`:356`). Stable contact IDs cannot restore qualifiers or source facts already discarded upstream.

Live: **508 of 765** resonance rows are flagged uncited. That is not proof they are all invalid; it is proof that qualification is a material part of the delivered asset. Required amendment: preserve the target predicate, all relevant fact roots, source/citation status and unresolved applicability; keep canonical L1 identities and a separate, versioned L2 binding.

### F10 — PARTLY

The seed is wrong: `platform/scripts/seed/asset_registry_seed.ts:2117–2125` describes the main table and `3.0`, whereas `PY/pipeline/orchestrator/writers/ka_gochara.py:120` writes `_v2` generation `2.0`.

**The current live cockpit count assertion is wrong.** `MIG/670_nirmana_l3_w3_integrity_contracts.sql:1908–1917` already changes `ka_gochara.count_sql` to `_v2` generation `2.0`, and that is the live value. Its `target_table` still says `kala_gochara_windows`. Thus there is current metadata inconsistency and seed/live drift, not evidence that the current count is another asset's `3.0` rows. The century registry still counts `g3_%` staging rows, a different ownership issue.

R10 must reconcile the seed, deployed registry, generation-specific integrity SQL, count semantics, coverage logic and generated contracts. Moving future rows into the table named by the stale seed is not a sufficient reason to choose a storage architecture.

### F11 — PARTLY

The distinction between an astronomical contact and a ranking-selected day is necessary. But the claim that most production peak selection is Tara-driven is not yet a decomposition experiment. The E2 fixture has **permission=0, raw_lambda=0 and Tara=1 throughout**; it cannot establish which factor selects actual nonzero peaks. Strong saturation in stored summaries supports a concern, not the universal causal conclusion.

A step-function plateau also need not have one scientifically privileged argmax date. Report the maximizing plateau or the deterministic tie rule, the actual selection mechanism, the governing score version and a separate forecast-precision qualification. `LAMBDA_V3_ARGMAX` alone should not earn a stronger timing claim. To change this judgment, compare nonzero production-context factors and selected peaks under predeclared one-factor ablations, including constant-score and tied-plateau cases.

### F12 — PARTLY

The exact-crossing scan can miss an in-orb noncrossing approach and can mistake the shortest-angle discontinuity at the anti-point for a root (`PY/pipeline/transit_search.py:301–372`). E3 reproduces **11 zero-strength sentences out of 202**. The computational defects are confirmed.

“The opposite of classical weighting” requires the relevant source-qualified relation, orb and rule; the numerical example does not establish a universal classical weighting policy. Also, calling a new result an “episode” does not prove phantoms cannot occur. The new kernel must solve on an unwrapped, branch-qualified separation and explicitly distinguish a true exact crossing, an in-orb closest approach and a tangency to the orb boundary. Include endpoints, coincident boundaries and both sides of the 0° seam.

### F13 — PARTLY

The current threshold defect is confirmed. The writer supplies `lambda_thresh=0.0` (`PY/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:1940`); raw λ is bounded to [0,1] (`engine.py:631–635`); the comparison is inclusive (`PY/services/gochara_v3/threshold.py:386–393`). A zero signal is therefore “active.” Worse, `_eval_single` converts **any exception to 0.0** (`interval_solver.py:116–136`), which can turn failed computation into an active era too.

The phrase “whole requested range” is imprecise. The coarse grid excludes the requested end (`interval_solver.py:269–277`), and the final interval closes at the last sample (`:325–326`). E5 requested 2026-01-01 to 2027-01-01 and returned **2026-01-01 to 2026-12-31**. The uncovered tail can approach one coarse step. Preserve a requested/completed horizon contract rather than inferring it from the returned interval.

The top-three peak cap is real, but it applies to the affected hierarchy route, not every class/shape without qualification. The present canonical `career_setback` corpus has one era plus three month and three day rows in each decade partition, including `g3_2014_2024`.

**MR-44/45 is not a verified counterexample to this analysis.** `MIG/568_parishkara_mr45_hierarchy_natkey.sql:3–31` identifies a month/day natural-key collision at the same **2017-03-01** peak. The historical ledger at commit `fc5b14f4e`, `ARCH/llm_consumption_audit/briefs/gochara_elevation/PARISHKARA_LEDGER.md:2662–2672,2685–2686,2739–2741`, contains both the assertion about ≥2 intervals and the later diagnosis that no second interval was needed; prior “nine peaks” were also not month-first. Commit `ded4770ca` explicitly records the earlier MR-44 root-cause verdict as failed. Earlier writer revisions `4a6bca948` and `68d1364ce` already use zero threshold/bounded raw λ.

The defensible explanation is **misattributed historical diagnosis plus mixed hierarchy counts**, not a demonstrated old nonzero threshold. Exact old inputs, code/config, raw evaluated series and row-level provenance could settle whether some older run really produced multiple eras. Those have not been recovered here; do not claim this residual historical question is resolved by speculation.

### F14 — PARTLY, with live corroboration

E3 reproduces the selected-date range approximately **0.996049–1.0**, Moon **137/202 sentences**, no-Moon **0–0.999249**, and slow-body-only **0–0.899986**. E2's fuller quarter-day grid has a lower minimum, **0.9939869455**. Thus “0.996–1 at all times” overstates even the fixture evidence.

The live result is stronger than a fixture-only diagnosis: of **914** canonical main-table `3.0` rows, **380** carry an activity value; all 380 are between **0.99964844 and 1.0**. The other 534 have no activity value to classify. These are selected peak/summary records, **not an unbiased time series**. They establish saturation in the populated served decompositions, not the distribution of the whole century or that Tara causes every peak.

Noisy-OR over repeated correlated evidence, the shared ±5-day window and synthetic kakshya events are plausible drivers. The fixed-fixture Moon ablation is informative but does not show Moon geometry is illegitimate. “More targets always makes it worse” assumes additional positive admitted contributions; live targets have mixed types and 31 negative weights. Diagnose duplicate physical evidence, weight handling, source qualification and temporal support before changing the body set.

**What would change this judgment:** a predeclared stratified, nonzero real-context evaluation grid; source/body/primitive deduplication and ablations; nonzero permission; and an outcome-independent discrimination test. Do not call variation alone product value or predictive validity.

### F15 — CONFIRMED on the production code path

This is not an accidental consequence of constructing the reviewer fixture with `conn=None`. The actual v3 engine unconditionally calls `kakshya_cell_crossing(..., conn=None)` even when its ClassContext was fetched from a real database (`PY/services/gochara_v3/engine.py:1063–1112,1133–1137`). `PY/services/gochara_grammar/primitives.py:664–719` then permits `equal_eighths_fixture_approximation`, and the activity path supplies the default strength (`engine.py:821–898`). The comments claiming it is skipped or honestly empty are contradicted by execution.

E3/E4 reproduce **147/202 sentences** and about **59.7% of primitive-search cost** for the fixture. Those percentages are not measured production workload shares. The confirmed code-path defect plus live F14 corroboration is sufficient to prioritize repair, but not to attribute every stored event to the current source revision. Correct real L1 boundary inputs must be prefetched and pinned, or the mechanism must be explicitly not evaluated; no silent fixture fallback in a production projection.

### F16 — CONFIRMED

The proxy uses the search window in constructing its event timestamp. E7 reproduces apparent dates near `t+5` or `t−4.9998`; these are not physical eclipse instants. A real eclipse catalog can supply actual events, but visibility, geographic applicability and interpretation remain distinct contracts. Replacing the proxy's geometry does not, by itself, authorize an eclipse-to-event-class weight.

F16 is also **not the sole obstacle** to global-event-list equivalence: F2's drishti residence counterexample is independent. Do not isolate every mismatch to eclipses by assumption.

### F17 — CONFIRMED for applied guard removal; recovery description corrected

Live `_migrations_applied` records **588 applied at 2026-08-23 05:33:15.527766 UTC**. The inspected live tables have **no relevant non-internal protection triggers**, and `build_protected_assets` is empty. Both the migration record and current catalog state confirm the central claim; this is no longer `[U]`. Source: `MIG/588_remove_asset_build_protection.sql:43–58`.

The current main table has exactly **38,287 v1 rows across three charts**, matching the retained-history count. But “one dump is the only retained copy” is not a complete current inventory: `kala_gochara_windows_archive_20260805` contains **35,620 rows / two charts** and `kala_gochara_windows__ssv_20260728c` contains **1,267 rows / one chart**, also acknowledged by migrations 670 and 674. An aggregate union-of-ID comparison matches only **35,620 of the current 38,287 v1 IDs**. The shadow's IDs do not fill the remaining 2,667 current IDs. Matching IDs would not itself prove matching contents.

Therefore neither “only one physical retained source exists” nor “the archives establish complete recovery” is defensible. The dump was not restored in this read-only review. `pg_restore -l`, cited in migration 588, lists an archive; it is not a restore drill. R6 must prove current complete coverage, content integrity, constraints and usable recovery.

### PoC — PARTLY; “exact on seven of eight primitives” is not established

E6 rerun: **319/360** activity evaluations agree within 10⁻⁹; **41** differ, with maximum absolute difference about **2.140×10⁻⁴**. Timings were **21.92 s** for repeated engine calls, **0.96 s** for one gather and **0.005 s** for all closed-form queries: about **22.8×** for gather plus queries, and about **4,657×** for query-only evaluation after gathering. The original 6,745× is a machine/run-specific query-only ratio, not an end-to-end build speedup.

The comparison is of **activity X(t)**, not the complete λ and permission/gate pipeline. Three of the eight included activity families—nakshatra, station and Vedha—are inactive in this fixture, so agreement does not exercise their semantics. E7 diagnoses only **nine selected mismatch positions**, not every one of the 41, and does not establish a universal attribution. F2 independently breaks the drishti claim on a supported sign-only target.

Retain this as a useful feasibility demonstration of avoiding repeated work. Replace its acceptance claim with a matrix covering every active primitive and factor, longitude and sign-only targets, nonzero permissions, changing Tara, overlaps, missing inputs, negative/signed evidence, exceptions, seams and horizon joins. Store the full mismatch classification in the eventual governed evidence artifact. Bitwise identity and numerical equivalence need separate, predeclared definitions.

## B. Live aggregate evidence

These are read-only observations of the database available through the existing production proxy, not a release or data-acceptance receipt. Canonical chart: `482012f1-710e-4a25-994a-93821f5871aa`.

### Resonance target counts

| Event class | Targets |
|---|---:|
| achievement_recognition | 35 |
| bereavement | 31 |
| birth_anchor | 16 |
| business_launch | 40 |
| career_advancement | 23 |
| career_change | 23 |
| career_entry | 34 |
| career_setback | 36 |
| childbirth | 21 |
| chronic_onset | 20 |
| education_milestone | 38 |
| exam_outcome | 22 |
| financial_deception | 32 |
| foreign_settlement | 24 |
| illness_acute | 28 |
| major_gain | 36 |
| major_loss | 32 |
| marriage | 23 |
| parental_event | 30 |
| property_acquisition | 14 |
| psychological_arc | 40 |
| relocation | 29 |
| romantic_start | 24 |
| separation | 38 |
| spiritual_turn | 33 |
| surgery | 18 |
| travel_event | 25 |
| **Total** | **765** |

Target-type totals: arudha 68; bhava 68; dasha_lord_portfolio 44; karaka 44; lord 52; mechanism_node 93; sensitive_degree 176; yoga_constituent 220. There are 508 uncited rows and 31 negative-weight rows; all negative rows in this snapshot are mechanism_node rows. Counts measure resolution outputs, not unique geometry or independent evidence.

### Stored generations

| Table / generation | Canonical rows | Canonical classes | Canonical min start / max end | All-chart rows / charts |
|---|---:|---:|---|---|
| `kala_gochara_windows` / `v1` | 16,297 | 6 | 1984-01-01 / 2085-01-01 | 38,287 / 3 |
| `kala_gochara_windows` / `3.0` | 914 | 27 | 1984-02-05 / 2084-01-31 | 1,830 / 2 |
| `kala_gochara_windows_v2` / `2.0` | 87 | 13 | 2023-09-25 / 2029-09-07 | 163 / 2 |
| `kala_gochara_windows_v2` / `g3_utkarsha` | 914 | 27 | 1984-02-05 / 2084-01-31 | 1,830 / 2 |

A row extent is not proof that every intervening instant, class or mechanism was searched. A missing class may be valid-empty or incomplete; this table cannot distinguish them.

### Authority and protection

The authority table has two rows:

| Chart | Authoritative generation | Flipped at UTC |
|---|---|---|
| `1c826d5a-41cb-4450-b4dc-59d440e5f75a` | `3.0` | 2026-08-11 09:10:42.635488 |
| `482012f1-710e-4a25-994a-93821f5871aa` | `3.0` | 2026-08-11 09:44:07.812646 |

No explicit authority row points to `2.0`. The defined absent-row default is `v1`, not absence of authority (`SUP/527_kala_gochara_generation_authority.sql:89–108`). There are no relevant non-internal protection triggers and no `build_protected_assets` entries in the queried current state.

Applied migrations inspected include 540, 566, 568, 588, 670 and 674. Their presence is not a substitute for the catalog check above.

### Recorded runtime: what can and cannot be concluded

`build_run_assets` contains these completed entries for the exact asset ID:

| Started at UTC | Ended at UTC | Elapsed seconds | Recorded state |
|---|---|---:|---|
| 2026-08-10 10:23:54.287139 | 2026-08-10 10:34:07.772217 | 613.485078 | complete |
| 2026-08-10 11:08:24.511107 | 2026-08-10 11:12:24.226318 | 239.715211 | complete |
| 2026-08-12 22:36:46.404462 | 2026-08-12 23:34:57.964701 | 3491.560239 | complete |

`output_changed` and `disposition` are null in these records. They are **recorded asset-execution wall clocks**, not demonstrated fresh full-century construction times. There were also error records, no matching retained `build_events`, and no century throughput-history rows to complete that attribution.

`kala_gochara_v2_build_state` currently has 540 `g3_utkarsha` partition rows across two charts, marked `full_backfill`, totaling 1,830 output rows, with completion timestamps spanning 2026-08-11 to 2026-08-12. For the canonical chart, 270 progress substeps have timestamps from 2026-08-11 17:17:30.909504 to 22:18:51.556233 UTC and sum to **903 reported rows**, whereas the current main-table count is **914**. That five-hour span is neither a single-run duration nor a consistent current count receipt. A per-substep fingerprint is not a build ID: 270 distinct fingerprints must not be read as 270 separate builds.

**Result:** the request's runtime unknown is narrowed, not closed. The database contains completed execution durations but the evidence inspected does not identify an uninterrupted cold build of the full declared workload. The 25-hour claim remains unverified.

## C. Recommendations R1–R10

### R1 — AMEND

One accountable windows asset is a reasonable destination. It must not erase distinct contracts: event-class versus mechanism projections; point, era, month, day and chain shapes; bounded progressive horizons versus complete horizons; and on-demand refinement versus persisted output. The current variants cannot be called redundant only because they all write “windows.” Preserve required variants as explicit named projections beneath one owner and publish compatibility mappings.

Replace `DATA_ACCEPTED + soak` as the retirement rule with the complete gates: source-qualified semantics; complete declared coverage including valid-empty partitions; delivered consumer identity/precision/counterevidence; reproducibility; history/rollback; exact campaign and lifecycle amendments. **Migration 527 explicitly says none of its four flip conditions is time-based** (`SUP/527_kala_gochara_generation_authority.sql:98–102`). A soak can be an additional operating observation, not a substitute or newly invented authority condition.

An inventory proving that no qualified consumer needs a discarded variant, followed by actual managed replay and a ratified disposition/denominator change, would justify consolidation. Producer acceptance on two charts alone would not.

### R2 — AMEND

Prefer a low-level pure kernel over enlarging the `ka_graha_sancara` hub. However, importing S0 as an upstream library now and later making S0 adopt that library risks a circular dependency and carries the defects in F4 into the new asset. “No hub edits” and “reuse only the validated pieces” cannot be assumed compatible without specifying which independently valid functions are reused.

Define a one-way dependency: common numerical primitives → asset adapters. Initially an unimported new module can leave existing writer closures unchanged; **adoption changes the adopting writer's digest closure**, and later shared-kernel edits affect every adopter. CAMPAIGN:116–125,170–177 governs those changes. If safely isolating or correcting an existing routine requires extraction, make that an explicitly owned cross-stream packet; do not claim zero invalidation forever, and do not silently fork copied implementations to evade it.

I would agree without amendment after a dependency graph, explicit function inventory, source fences and transitive digest delta prove the proposed reuse is correct and acyclic.

### R3 — AMEND

The computation/claim distinction is right. Precise ingress calculation can improve a categorical Moorti answer without authorizing an hour-level prediction. Retiring an existing computation rail is still a qualified method/authority decision, not something made unnecessary because calculations become cheap.

Define at least astronomical event time/bracket/tolerance, classification certainty and forecast precision separately. A `precision_class` label must be enforced through all adapters and readers, not merely added to the row. Near a station, small angular error can imply large or undefined timing error; “0.314″ means about a second” is not a general precision contract. See product v3.0 §3.10 and F4/F6/F11.

### R4 — AMEND; reject blanket Moon exclusion

The highest-value initial repair is **honest input and evidence semantics**: eliminate fixture-only production operands, preserve missingness, deduplicate one physical contribution reached through several targets/rules, and expose separately the actual components. This can improve quality before deciding a new activity formula.

Contact intervals are a promising geometric foundation, but geometry and interpretive weight are different choices. Separation scaling, orb selection, dwell weighting, era eligibility and eclipse influence all change meaning. A code docstring and an uncited-extension flag cannot ratify them. The plan's sentence “I am not proposing doctrine” should be removed: it is proposing several method changes and correctly needs separate rulings for them.

Do **not** remove the Moon from the admitted contact domain or assert that its only legitimate roles are Tara, Moorti and day refinement. ADJUDICATION-14 rejects cost-led amputation of bodies/classes and permits on-demand Moon degree contacts; it does not invalidate Moon contacts (`ARCH/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_ADJUDICATIONS_NIGHT5_v1_0.md:48–73,95–105`). The earlier design explicitly retains their value (`.../doctrine_waves/GOCHARA_SWEEP_2_0_DESIGN_v1_0.md:25–28,58–62`). Keep Moon geometry/testimony; compare source-qualified body-specific projections before changing its contribution to this particular score.

Suggested order: (1) correct operands, coverage and duplicate evidence; (2) produce geometric episodes without new interpretive weights; (3) compare a qualified contact-interval projection to the legacy boxes, with all bodies retained; (4) separately adjudicate separation, dwell, Moon score participation, era construction and real-eclipse effects. Persist all admitted evidence, with explicit serving budgets and counts.

Finally, separation-dependent Stage M activity will generally vary continuously. The Stage E step-function proof cannot be reused for its extrema, peak finding or integration. Require a new mathematical reference and tests at interior extrema, plateaus and tangencies. Source-qualified rulings plus informative real-context ablations would change this recommendation; variation alone would not.

### R5 — AMEND

Two-phase admission is useful but **testimony-only is not harmless**: users can still infer meaning from an incorrectly populated mechanism. Audit each operand and its applicable scope before phase one.

The proposed first mechanism is currently unsuitable. `PY/services/gochara_v3/mechanisms/w21_av_gating.py:126–143,148–171` explicitly substitutes `min_sav_score` from a rule for the chart's actual bindu count. `ClassContext` loads `bg_transit_av_gates` rules, not the chart/sign bindus needed for the claim (`context.py:328–359`), while `grammar_v3_registry.yaml:29–37` describes real bindu gating. A non-empty ablation could therefore “admit” a chart-independent threshold proxy.

Require real L1 SAV/BAV operands at the relevant sign/time, canonical fact IDs, distinct rule thresholds, source applicability and missing-data behavior. A relevant-input perturbation must alter the testimony; an irrelevant-input perturbation must not. Apply the same discipline to Kota/annual inputs, Moorti, school-specific Vedha and eclipse applicability. Order mechanisms by verified readiness and user value after this audit, not by W number. Score admission additionally needs non-vacuous ablation and a qualified independent reference. Do not expand into L4/L5 model admission or empirical evaluation under an L3 packet (EXECUTION:198).

### R6 — AMEND

A `(table, generation)` policy is technically more appropriate than the removed asset-ID guard, but migration 588's conditional advice is **not standing permission to reinstate protection**. Its explicit native instruction removed all per-asset protection for the elevation campaign (`MIG/588...:3–20,37–39`). The plan correctly acknowledges a partial reversal; retain a fresh, explicit ruling rather than treating that comment as authority.

Specify the whole mutation surface before that ruling: DELETE, UPDATE of both OLD and NEW generation values, key/chart changes, TRUNCATE, cockpit Clear, cascades and recovery. TRUNCATE cannot inspect per-row generation, so a shared-table policy requires an explicit table-level rule or equivalent isolation. Prove legitimate new-generation writes still work while historic rows and issued evidence are preserved. Keep the separately protected L2 history guard untouched.

The restore gate must cover all required current v1 rows and contents, not just an archive listing or the partial retained archives. Test rollback after a failed/incomplete successor build and during concurrent reads. A reviewed policy plus a real disposable restore drill and destructive-operation tests would justify this change. This review performed none of those mutations.

### R7 — AMEND

On-demand Moon degree geometry is a good default candidate, not an unconditional “never persist” doctrine. Query frequency, replay requirements, caching and storage measurements may justify bounded persistence. More importantly, **do not restrict Moon search to day windows already selected from slow-body activity**: that makes Moon-only candidates invisible before the refinement stage. Search the full explicitly requested on-demand interval, and declare what has and has not been searched.

A recomputed contact should retain deterministic identity under the same complete input vector. Corrected input versions should remain distinguishable; truncating a query must not manufacture a new identity for the same physical episode. Persisting Tier B is reasonable only after estimating ledger size and proving horizon extension/resume behavior. I would remove this amendment after complete query semantics and measured cache/persistence tradeoffs justify the chosen policy.

### R8 — AMEND

Reserve L2 binding fields now and allow the numerical prototype to proceed before all of Yojaka is elevated. But **do not let the successor reach terminal value acceptance while structural binding remains an optional later phase**. Product v3.0 §12.2 requires formation, cancellation and eligible activation of the chart's qualified structures; generic event-class windows with empty reserved columns cannot answer that request. STRATEGY:89–106,393–410,433–441 distinguishes producer readiness from delivered value. EXECUTION:311–317 makes the Bhavat arm of `L3-SLICE-STRUCTURE-TIME-01` non-promotable until its required join works.

Introduce a minimum accepted L2 structural slice before production promotion/terminal disposition: one qualified structure, its cancellation/eligibility conditions, actual target/fact bindings, time contacts, three-way negative coverage and managed consumer evidence. Wider Sangam/Kshetra migrations can remain later owner-specific packets. If upstream semantic work needs new authority, record that exact dependency and leave the gate open; do not recast it as completion.

### R9 — AGREE, with a bounded operational qualification

Register the frame defect, preserve and label existing generation-2.0 rows, and prevent further dispatch through the governed owner/lane. The queried live authority corroborates that they are not ordinary served rows. Do not equate “not served” with “safe to rebuild”: the asset is still buildable and direct validation readers may exist. Quarantine must be an actual governed dispatch/lifecycle control when execution is authorized, not only a note in the defect register. This review creates no such control and deletes nothing.

### R10 — AMEND

Reconcile registry truth through the governed route, but first correct the proposal's assertion that the live count remains the seed's `3.0` query. Migration 670 has already fixed that part. Do not wait until cutover to define ownership, count and integrity semantics: prospective D1/D3 contracts and benchmark dimensions depend on them, and a reseed could restore the stale value.

At cutover, update the approved seed/live/generated/integrity/coverage definitions together, retaining explicit history and publication scope. A count of windows is not a count of contacts, evaluated mechanisms or complete partitions. Test valid-empty and partial coverage without fabricating minimum rows, per CLAUDE §N.4/§N.8. Agreement would require this broader reconciliation, not a single `target_table` edit.

## D. Design review of §7

### Geometry, interpolation and astronomical conventions

Cutting a **correctly known continuous series** at every stationary point and wrap can bracket all its crossings. That theorem does not establish that daily samples reconstruct the physical trajectory, that all derivative roots were kept, or that the query uses equivalent 0°/360° endpoints. F4 breaks all three assumptions in the proposed reuse.

The recorded **0.314″** is an observed sample maximum from a limited validation, not a universal bound. `PY/services/w2g_validations/v3_spline_accuracy.py:273–294` samples two stations each for Mercury/Mars/Venus/Saturn, three Moon perigees and two baseline dates, at six offsets (`:60–63`) deliberately away from fit boundaries (`:56–58`). It does not establish all five ayanamshas, node topology, horizon ends, all epochs, missing/corrected knots or all target relations. “Exact at knots, convention-free” in PLAN:276 is also wrong: stored knots are rounded and embed flags, node definition and time conventions.

Specify the full convention vector: ephemeris source/files/version; time scale and noon origin; coordinate/reference frame; sidereal method and time-varying offset; apparent/mean/nutation flags; geocentric/topocentric scope; node type and Ketu construction; longitude unwrapping; input precision; interpolation and derivative policy. A pure evaluator may avoid the Swiss lock, but construction, fallback, audits and global Swiss state still need a safe contract. “Parallel” must be demonstrated with isolated convention state, not inferred from using an interpolant.

Longitude alone is insufficient for the claimed shared consumer scope. Kshetra S0's syzygy path uses Moon latitude (`PY/services/ka_kshetra/stage0_kinematics.py:547–560,1028–1040`); real eclipse visibility has separate needs. No mandatory distance consumer was established in this bounded audit. Do not invent one, but complete the consumer field dossier before excluding it. Preserve the already-needed latitude channel or explicitly keep those consumers on another qualified adapter.

### Cached arc reuse is not currently safe as described

`bg_gochara_arcs` is tropical-only in `MIG/694_bg_gochara_arcs_tiling_floor_rewrite.sql:48`; `PY/services/w2g/db_source.py:168–213` does not select a per-ayanamsha, content-validated sidereal index. More seriously, `PY/services/w2g/fingerprint.py:46–67` hashes body, epoch bounds, knot count and engine version, **not knot content**. An upstream correction with identical dates/count does not invalidate it. This directly fails STRATEGY's upstream-correction workload and CAMPAIGN D4.

The successor cache needs accepted input-generation/content identity plus its entire convention vector and algorithm version. A tropical arc set cannot simply be relabeled sidereal, because the derivative of the frame transformation can move stations. Treat existing arcs as a separately qualified optional optimization; make the in-memory and cached paths independently demonstrate equal coverage and results under identical inputs.

### Contact identity and projection identity need separate contracts

A deterministic `contact_id` is valuable only after defining its equivalence relation. Include the normalized physical target/relation, astronomical input identity, convention, branch/occurrence and method/tolerance policy. Keep class membership, weights and L2 interpretation outside the physical-contact identity where reuse is legitimate; version those semantic bindings separately. Retain all contributing canonical fact roots and qualifiers.

Define IDs for exact crossings, closest approaches and entire episodes; define whether multiple exact passes belong to one wider episode. Horizon clipping must not rename the underlying event; uncertainty/truncation must remain attached to the response. A correction can create a new version without rewriting the identity of already-issued evidence. Quantized floating timestamps or ordinal “first crossing in this query” are insufficient.

### One table is possible; the proposed publication protocol is incomplete

Writing a new generation beside preserved old rows can work. The current schema/authority mechanism is not itself an immutable publication system. `SUP/527...:81–86` maps a chart to a text generation; `MIG/568...:101–110` adds hierarchy discrimination to the natural key but not a complete input/publication vector. The current writer performs partition deletion/insertion (`PY/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:2244–2272`). Rebuilding inside a served `4.0` could expose mixed or replaced partitions without any authority flip, and replace row IDs used as evidence.

Require an immutable build/publication identity distinct from the algorithm label `4.0`, a complete partition manifest including valid-empty partitions, accepted upstream generation vector, explicit completion/eligibility state, and an atomic switch only to a complete candidate. A reader must pin one publication/input vector for the request. Define crash/resume, extension, correction, concurrent reads, rollback and retention. Any necessary schema or authority change remains governed work; this review does not prescribe a migration.

The main windows table stores dates (`MIG/460_kala_gochara_windows.sql:78–80`), and MCP formatting uses dates (`MCP/tools/retrieval/register_gochara_windows.ts:604–608`). It cannot by itself preserve exact contact timestamps, brackets and tolerances. Specify the exact-time contact storage plus its day-level window projection; “one table” should refer only to the intended windows store, not accidentally collapse the whole ledger into dates.

The existing authority flip's four functional gates remain mandatory. A soak or a ready revision is not evidence that the full published dataset and every consumer contract are correct.

## E. Ecosystem and campaign fit

Authority filtering is necessary and insufficient. PLAN:417–424 substantially understates receiving and operational work.

| Omitted or understated surface | Evidence and failure | Required work / owner boundary |
|---|---|---|
| MCP coverage attestation | `MCP/tools/retrieval/register_gochara_windows.ts:963–977` recognizes `3.0`/`g3_`; `4.0` falls into the retired sweep branch and its `:year:` key parser. `:1466–1478` can return `not_covered` before reading windows. `:1041` intersects current mutable resonance targets. | Generation/publication-bound coverage manifest, including complete-empty partitions and pinned target universe. Test all three tools and unknown-generation behavior, not only citations. L3 receiving owner. |
| Reading checklist | `APP/lib/retrieval/registry/layers/reading_checklist.ts:1063–1092` selects class/shape/dates/valence, drops IDs, generation, resolution, parents, `peak_basis`, testimony and coverage. It limits to 200 then returns five while counts are based on that capped set. | Preserve evidence and honest returned/available/truncated counts through budgets; do not label capped counts full coverage. |
| D8/D9 managed synthesis | `APP/lib/retrieval/registry/layers/register_d8_assess_domain.ts:1230,1354` consumes the sweep; its adapter `:90–104` and `APP/lib/retrieval/registry/layers/register_d9_judgment.ts:110–123` classify non-point rows as era context and dated point rows as timing. The proposed finer semantics are lost. | Real managed D8/D9 sentinel replay through retrieval, synthesis, delivery and retained evidence; distinguish computational exactness from timing qualification. |
| Pariprashna `engine_tier` | `APP/lib/pariprashna/confidence/engine_tier.ts:37–46` says it is not wired. The audit found no non-test caller. | Treat it as a prospective receiving contract, not current delivered protection. Verify actual call path. |
| L5 prospective ledger | `APP/lib/lel/prospective_ledger.ts:174–190,226–237` does not accept contact IDs, generation or full convention/input identity; its signature hashes dates, basis, fact IDs and system IDs. | A receiving-owner amendment is required to carry stable contact/publication identity. L3 may specify/test its handoff; no claim issuance or full L5 writer changes under this packet. |
| Cockpit Clear — an omitted writer | `APP/app/api/cockpit/clear/execute/route.ts:84–108,156–182` loads registry rows, excludes only protection-registry entries, then derives DELETEs or uses chart-wide fallback. `APP/lib/cockpit/clearScopeFilter.ts:28–38` does not remove retired/inactive assets. Protection registry is now empty. | Review preview and execute together, including retired-history exclusion and shared-table predicates. No Clear operation was run. This belongs in R6 before successor writes. |
| Calibration/rebuild utilities | `PY/scripts/kala_admission/w45_post_fit_rebuild.py:299` updates calibration state and `:457` can insert prospective rows; `:131–147` applies a top-20 path. W44 wiring metadata is stale. | “Select by generation” is not enough. Inventory mutating behavior, source/model pins and authority; preserve full evidence and hold L4/L5 issuance/admission boundaries. |
| Kshetra cross-check pin | `PY/services/ka_kshetra/writer.py:2313–2375` combines the served generation/calibration with a resonance-map digest made from count/max timestamp/max ID rather than row contents. A weight correction that preserves those aggregates escapes that identity. | Pin the immutable publication/content; retain both agreement and counterevidence in stage-4 cross-checks. |
| Permission curve and other direct readers | `PY/routers/permission_curve.py:141–160` reads current resonance; transit materialization carries source-rule identities (`PY/pipeline/transit_search.py:822–828,900–906`). W41/W43/W44/W45, census/TCI checks, authority/rollback helpers and Kshetra snapshot repair also read related corpus contracts. | Expand the owned reader/writer inventory and qualify source/input pins and generation predicates. This is a bounded discovery list, not a claim that all callers have been audited. |
| Registry/integrity/build-state machinery | Migration 670 contains generation-specific integrity and count rules; existing build-state/progress encodings distinguish `2.0`, `g3_*`, `3.0`. | Update accepted definitions and empty/partial/completed accounting together; preserve old-generation history. Count success must not stand in for semantic acceptance. |

**Ownership:** Stream C is a reasonable technical lead for numerical work, not automatic sole authority over the full successor. CAMPAIGN:134–154 assigns resonance and overlays to A, `ka_gochara`/Yojaka/Sangam to B, and W2G/v3/Kshetra to C. Name an accountable integration owner plus non-overlapping A/B/C and receiving packets. Record dependency and digest invalidation explicitly. The single build lane and integrator remain mandatory (CAMPAIGN:165–177). A new module does not waive hub freeze or transitive import rules.

**Campaign conflicts to fix:** D1–D4 are delayed until after algorithms; the first slice starts on a real chart before the mandated non-person fixtures; Stage E evidence is overclaimed; the full benchmark precedes complete persistence/consumer behavior; L2 delivered value is deferred beyond disposition; the soak is substituted for functional flip gates; mechanism/calibration activities can cross reserved authority. These are concrete amendments, not a requirement to stop all analysis until every later consumer is elevated.

## F. Implementation sequence and exit gates

### Changes to WP0–WP10

| Packet | Review disposition |
|---|---|
| **WP0** | Use this review's live counts, guard state and narrowed historical finding; revalidate at implementation time. Register the extra kernel, convention, proxy-input, adapter and Clear defects through the authorized owner later. “Register defects” is a write, so it is not itself read-only; this review did not do it. Close what is known without pretending the old ≥2-era case is reconstructed. |
| **WP1** | Precede with D1/D3/D4 input and identity contracts and non-person fixtures. Do not directly import the defective station/episode/time behavior. **The current E1 cannot become zero by adding a new module:** it deliberately calls the old tropical W2G path. Retain it as a legacy defect reproducer and add a separate successor comparison with declared angular/time/coverage tolerances. Rounded “0 d error” is not an exit criterion. |
| **WP2** | Replace “bit parity on seven primitives” with the complete active primitive/factor matrix in F2/PoC. Span-aware behavior, nonzero λ, missingness and failures are prerequisites. Keep exact-legacy and repaired-semantics tracks separate so deliberate defects are neither copied into acceptance nor silently waived. |
| **WP3** | Compare independent oracle → legacy event semantics → successor geometry → projection, rather than force event-set equality with known phantoms and missing tangencies. Classify every divergence with its input and reference. This can produce a **bounded kernel/scorer benchmark**, not the full STRATEGY §5 build benchmark before persistence, recovery and consumer delivery exist. |
| **WP4** | Split: move the field dossier, grain, contracts, input generation vector, identity and negative-coverage design **before WP1/WP2**. Implement the ledger/typed testimony after the numerical proof. Schema choice requires its actual governance gate; neither all design nor all schema work should be assigned authority solely by a blanket label. |
| **WP5** | Make source/duplicate/missingness repair first. Preserve Moon evidence. Separately qualify every weighting change and supply a new continuous-score reference where applicable. E3 slow-body variation is not by itself an acceptance test for delivered quality. |
| **WP6** | Audit and repair input contracts before any testimony admission; start with genuinely ready mechanisms. Non-empty ablation alone cannot detect W21's threshold-as-bindu substitution. Keep admission/empirical authority boundaries explicit. |
| **WP7** | Depend on the agreed time/convention contract and relevant accepted inputs, not only WP1. Prove complete requested horizon, truncation and missingness for each overlay; test exact-ingress classifications and horizon-constant ayanamsha error separately. A/B ownership is required. |
| **WP8** | Design receiving contracts early; implement and exercise them before promotion. Include coverage branching, checklist, D8/D9, budget/truncation and identity propagation, not just citation vocabulary. Include one structural L2-to-time delivered slice and the exact L5 handoff obligation. |
| **WP9** | Require complete immutable publication, source/data/consumer gates, approved disposition, guard policy and tested recovery before any authority flip. Reconcile exact deployed revision and current holds. Run the four existing functional cutover gates; soak is supplemental. Test rollback with the real serving adapters. |
| **WP10** | Split the minimum structural/receiving slice required for value acceptance from broader consumer migration. Move the minimum before terminal promotion/disposition; keep larger Sangam/Kshetra adoption and cap removal in separate owner packets with their own accepted upstreams. |

### Revised first slice

The first slice should be **contract + synthetic evidence + bounded geometry/scorer comparison**:

1. Freeze the input/convention/target specification and output identity/coverage contracts; define the reference oracle, tolerances, ownership, file fences and immutable test vector. Resolve point versus span semantics and exact event versus forecast precision. This is the missing front of WP4, not an optional later dossier.
2. Use deterministic **non-person cases first** (EXECUTION:190; STRATEGY:238–241). Include the close-station cubic, real true-node excursion, wrap tangency, start-inside/end-inside episodes, noon conversion, sign-only drishti, nonzero permission, missing-overlay and exception cases. Add a non-vacuous factorized scorer oracle.
3. Develop kernel and legacy-algebra experiments as independent bounded work once those contracts are reviewed. Preserve the old E1 result; compare the new kernel with a convention-matched direct oracle and an independently enumerated candidate set. Constant database reads in target count is a useful metric, not a completeness test.
4. Run the decomposed comparison over the same predeclared workload and report every unexplained delta, requested/completed coverage, IDs and input pins. No physical contact may be silently dropped because it lies below the sampled longitude-error scale.
5. Report bounded cold/warm experiment timings with preparation/search/query costs separated. A chart-specific disposable replay may follow the required gate. Call the output **producer prototype evidence**. Do not call it a whole-century build result, DATA_ACCEPTED, a delivered-value success or proof that the plan is complete.

**Stop conditions for the first slice:** unresolved astronomical convention; unknown/incomplete input masquerading as empty; missed physical topology without a declared fallback; unclassified divergence; identity drift under equivalent horizon partitioning; or any acceptance comparison made vacuous by zero permissions/absent operands. A timing gain does not override one of these failures.

Afterwards, implement ledger/publication and one genuine managed consumer slice, then run the complete STRATEGY benchmark: cold, warm, resume, extension, input correction, no-window, dense-window and rare boundaries; wall/CPU/RSS, Swiss/lock, SQL, bytes/WAL, serialization, recovery and time to first **qualified consumer result**, with repeated matched runs and reported spread. Only then does “minutes cold, seconds warm” become testable at asset level.

### Failure modes missing from §11

- A tiny positional residual hides a wrong number of physical roots; a station merge or derivative exception is reported as complete.
- The new oracle compares different Swiss flags or assigns noon data to midnight.
- A cached arc fingerprint survives a same-size upstream correction.
- A globally gathered point event substitutes for a residence interval; an inactive factor makes the test look equivalent.
- A caught exception becomes zero and then passes a zero threshold as “active.”
- Source thresholds, placeholders or uncited approximations are exposed as chart testimony before score admission.
- Contact deduplication loses predicate qualifiers or evidence roots; recomputation changes IDs at a horizon seam.
- A continuous repaired score retains a step-only peak algorithm.
- A complete-empty partition has no row and is misreported as unsearched, or old mutable resonance defines the coverage of a new publication.
- A rebuild modifies an authoritative generation in place; a request sees mixed publications or uses old contacts with current weights.
- Coverage rejects `4.0` before window retrieval, or the managed adapter strips exactly the fields that made the producer truthful.
- Cockpit Clear deletes retired history; a nominal generation guard can be bypassed by UPDATE/TRUNCATE or blocks legitimate shared-table work.
- Terminal asset retirement occurs before the structural L2 question can be answered with preserved identities and negative evidence.

## G. Confidence corrections and decision

Replace the following strong claims in the next plan revision:

| Current claim | Supported replacement |
|---|---|
| “The largest technical unknown is removed”; “right kernel already exists.” | Useful numerical components exist, with independently reproduced correctness and coverage defects that the first slice must resolve. |
| “Exactly a step function of a dated event list”; “exact on 7/8.” | The legacy formula is largely discrete; the PoC accelerates one fixture's activity calculation. Full span-aware factorized equivalence is unproved and the general 7/8 claim is contradicted. |
| “0.314″ worst case”; “nothing falls between samples”; “exact service.” | A limited interpolation validation observed 0.314″. Physical contact topology, convention and boundary coverage require additional evidence and possibly adaptive direct calculation. |
| “Activity saturated at 0.996–1 at all times”; “today's windows are daśā plus Tara.” | The fixture and 380 populated served summaries are strongly saturated; full-century distribution and factor attribution have not been measured. |
| “Current cockpit counts another asset's rows.” | The seed is stale and target-table metadata remains inconsistent; migration 670 already corrected the live count query. |
| “No consumer schema change; L5 gains IDs.” | Several adapters drop essential fields, coverage misroutes a new generation, and L5 cannot receive contact IDs through its current interface. |
| “One dump only”; “restore verified by listing.” | Multiple retained sources exist, but the inspected archives do not cover all current v1 IDs; a complete, usable restore remains unproved. |
| “All first-slice work class A”; “WP1+WP2 can start now.” | Authorized local implementation still requires named ownership, reviewed input/safety contracts and non-person fixtures; the present review itself authorizes only this file. |
| “Single-digit minutes cold, seconds warm.” | A hypothesis to measure after complete workload and consumer/recovery contracts exist; current numbers are unit or partial-workload timings. |

**Final decision: PROCEED WITH AMENDMENTS**, limited to the revised first slice above after its normal packet gates. The current plan is not ready for its stated WP1–WP3 acceptance, production publication or family retirement. The strongest reasons to continue are the confirmed wrong-frame W2G defect, the confirmed served fixture fallback, the measured avoidable repeated search and the product's need for explicit contacts and coverage. The strongest reasons to change the plan first are concrete counterexamples, not a preference for additional process.

This judgment would become **PROCEED** for the original scope only after the amended plan incorporates the counterexamples, states a complete input/publication/consumer contract, replaces the vacuous/impossible exit gates, preserves legitimate Moon and structural evidence, and demonstrates the required delivered-value and history gates. Those results have not been produced by this review.

## Appendix A — Re-running the supplied evidence without repository writes

Use the specified interpreter with bytecode generation disabled. From the reviewed worktree, run each script explicitly:

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/venv/bin/python -B 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/evidence_gochara/E1_w2g_frame_defect.py
```

Repeat for the actual E2–E7 filenames in that directory. Do not regenerate or overwrite `OUTPUT_2026-09-20.txt` as part of a read-only rerun. This review records the rerun measurements and their limits above; hardware timing differences are expected.

## Appendix B — Aggregate query shapes used for live verification

Use an already-authorized connection, no credential output, `BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY`, and `ROLLBACK`. The following expose aggregates or the authority metadata expressly requested:

```sql
SHOW transaction_read_only;

SELECT event_class, count(*)
FROM gochara_resonance_map
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
GROUP BY event_class ORDER BY event_class;

SELECT generation, count(*), count(DISTINCT chart_id)
FROM kala_gochara_windows GROUP BY generation ORDER BY generation;
SELECT generation, count(*), count(DISTINCT chart_id)
FROM kala_gochara_windows_v2 GROUP BY generation ORDER BY generation;

SELECT chart_id, authoritative_generation, flipped_at
FROM kala_gochara_authority ORDER BY chart_id;

SELECT n.nspname, c.relname, t.tgname
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE NOT t.tgisinternal
  AND c.relname IN ('kala_gochara_windows', 'kala_gochara_windows_v2',
                   'build_protected_assets');
SELECT count(*) FROM build_protected_assets;

SELECT state, started_at, ended_at,
       extract(epoch FROM (ended_at - started_at)) AS elapsed_seconds,
       output_changed, disposition
FROM build_run_assets
WHERE asset_id = 'ka_gochara_v3_century_materialize'
ORDER BY started_at NULLS LAST;

WITH ids AS MATERIALIZED (
  SELECT id FROM kala_gochara_windows_archive_20260805
  UNION
  SELECT id FROM kala_gochara_windows__ssv_20260728c
)
SELECT count(*) AS current_v1_rows, count(ids.id) AS archive_id_matches
FROM kala_gochara_windows c LEFT JOIN ids ON ids.id = c.id
WHERE c.generation = 'v1';
```

The retained-archive comparison establishes ID coverage only. It is not a content checksum, successful restore or permission to modify either corpus.

## Appendix C — Two independent kernel counterexamples

Run this complete in-memory reproducer from the reviewed worktree; it writes no files. Its expected results follow directly from the polynomial and the stated orb, so they do not depend on legacy output being correct.

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/venv/bin/python -B - <<'PY'
import math
import sys
sys.path.insert(0, 'platform/python-sidecar')
from scipy.interpolate import CubicSpline
from services.w2g.arcs import build_arcs, _station_times
from services.w2g.crossings import find_contacts
from services.ka_kshetra.stage0_kinematics import build_spline, find_contact_episodes

times = [0.0, 1.0, 2.0, 3.0]
f = lambda t: 100.0 + (t - 1.5)**3 / 3.0 - 0.01 * (t - 1.5)
longitudes = [f(t) for t in times]
spline = CubicSpline(times, longitudes)
arcs = build_arcs('Mercury', times, longitudes)
contacts = find_contacts(arcs, 100.0, 1.0, tolerance_arcsec=1e-7)
print('Actual stations:', sorted(float(r) for r in spline.derivative().roots(extrapolate=False)))
print('Retained stations:', _station_times(spline, times))
print('Expected roots:', [1.5-math.sqrt(0.03), 1.5, 1.5+math.sqrt(0.03)])
print('Observed roots:', [e.exact_jd for e in contacts])

s0 = build_spline(times, [100.0, 100.1, 100.2, 100.3], [0.1]*4)
episodes = find_contact_episodes(s0, natal_lon=100.0, body='Saturn',
    target_ref='test', t_grid=times, orb_deg=1.0, orb_source='test')
print('Expected: one horizon-clipped episode spanning [0.0, 3.0]')
print('Observed:', episodes)
PY
```

Observed:

```text
Actual stations: [1.4000000000001036, 1.5999999999998964]
Retained stations: [1.4000000000001036]
Expected roots: [1.3267949192431123, 1.5, 1.6732050807568877]
Observed roots: [1.326794917881587]
Expected: one horizon-clipped episode spanning [0.0, 3.0]
Observed: []
```

## Appendix D — Independent F2 residence counterexample

From the reviewed worktree, the following reproduces the additional window-relative primitive. It uses the supplied benchmark target, changes only its resolved longitude/sign representation, and performs no database access or file writes.

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/venv/bin/python -B - <<'PYCODE'
import sys
from dataclasses import replace
sys.path.insert(0, 'platform/python-sidecar')
import swisseph as swe
from services.gochara_v3.tests.test_speedup import _build_context_for_benchmark
from services.gochara_v3 import engine as E
from services.gochara_grammar import primitives as P
ctx = _build_context_for_benchmark('marriage')[0]
target = replace(ctx.resonance_targets[0], target_longitude_deg=None, target_sign='Libra')
a = swe.julday(2026, 1, 1, 12.0)
t = a + 30
all_events = P.drishti_contact(swe, ctx.chart_id, target, a-5, a+185, planets=['Jupiter'])
local = P.drishti_contact(swe, ctx.chart_id, target, t-5, t+5, planets=['Jupiter'])
filtered = [e for e in all_events if t-5 <= e.event_jd <= t+5]
for label, events in [('all', all_events), ('local', local), ('filtered', filtered)]:
    print(label, 'offsets', [round(e.event_jd-a, 8) for e in events],
          'activity', E._compute_activity_v3(events, ctx.weight_by_target_ref)[0])
PYCODE
```

Observed:

```text
all offsets [-5.0] activity 0.44999999999999996
local offsets [25.0] activity 0.44999999999999996
filtered offsets [] activity 0.0
```

The event remains physically resident, but its representative timestamp depends on the caller's interval. A global point-list filter loses that state.

## Review close record

Scope completed: independent source/evidence/governance review; E1–E7 reruns; additional in-memory counterexamples; requested live aggregates where available; all F1–F17 and PoC dispositions; all R1–R10 dispositions; design/ecosystem/packet challenge; ranked risks and bounded verdict. No full fresh-century runtime, restore drill, deployed-source equivalence, prediction-validity result or terminal asset acceptance is claimed. No review finding has been silently applied to production or to the plan. This record is not a campaign build/acceptance receipt.

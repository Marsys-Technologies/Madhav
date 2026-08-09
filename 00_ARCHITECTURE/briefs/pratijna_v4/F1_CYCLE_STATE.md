# F1 AMENDMENT CYCLE — Campaign Ledger

**Campaign:** F1 AMENDMENT CYCLE — the first R20 amendment to the ratified PRATIJÑĀ v4 rubric
(`V4_RUBRIC_SPEC_v1_0.md`). Same campaign home as PRATIJÑĀ v4 Campaign B
(`00_ARCHITECTURE/briefs/pratijna_v4/`) — this is that campaign's first R20 cycle, not a new arc.
**Plan of record:** the governing conductor prompt (this session) + `CHECKPOINT_RECORD_v1_0.md`
(F1 filed there as an amendment candidate, NOT implemented in v1.0) + R20's own text (quoted below,
`PRATIJNA_V4_STATE.md` line 56).
**Integration branch:** `f1-amendment/integration`, cut from `main` @ `282aaf912` (2026-08-09).
**Conductor:** Sonnet 5, this session (solo — no builder/PARĪKṢAKA role split into separate
sessions this cycle; PARĪKṢAKA was run as a genuinely independent subagent review, not the
conductor self-grading, per the discipline the campaign's prior lanes established).
**Status: ALL THREE STAGES CLOSED. No production write. No deploy. Ready for merge (Stage 3, this
entry).**

---

## Governing ruling — R20 (quoted, `PRATIJNA_V4_STATE.md` line 56)

> **R20 — AMENDMENT PROTOCOL.** v1.0 is immutable. A spec amendment is legitimate ONLY as: (1)
> blind definition — rule + band + weight + citation authored and COMMITTED before its effect on
> any chart is computed (CI check: the amendment doc's commit must precede any scoring run that
> includes it); (2) applied only in a vNEXT engine version; (3) v1.0 and vNext scored SIDE BY SIDE
> on all charts, both published; (4) adoption decided from the comparison + classical merit,
> recorded as a ruling. Debates become measurements.

R13 (absolute — no tuning against any chart) and R16 (full disclosure, no silent scope narrowing)
remain in force throughout, per the governing prompt.

---

## Stage 0 — Blind definition (CLOSED)

| Item | Detector | Result |
|---|---|---|
| Branch cut from `main` | `git checkout -b f1-amendment/integration main` | Done, from `282aaf912` |
| `AMENDMENT_F1_SPEC_v1_0.md` committed verbatim | Byte-for-byte match to the governing prompt's quoted spec block | Commit `8110d5fab` |
| Blind-before-effect (R20 item 1) | Spec commit precedes ALL engine code / probe runs | `8110d5fab` (spec) → `b37c5005a` (engine) → `65698afd0` (probe+side-by-side) — strict order, verified by `git log` |
| Disclosure of the one pre-existing estimate | Spec's own DISCLOSURE clause states the checkpoint's ~0.42 marriage estimate and that nothing else was computed | Present verbatim in the committed spec |

**Result: CLOSED.**

## Stage 1 — Build (CLOSED, PARĪKṢAKA PASS)

| Item | Detector | Result |
|---|---|---|
| `amendments={'F1'}` param, engine library | `bo_pratijna_v4_engine.py`: `dignity_of_with_positions(..., amendments=frozenset())`, `PratijnaV4Engine.__init__(..., amendments=frozenset())` | Commit `b37c5005a` |
| Default-off (v4.0 unchanged) | Live RUNG_P3 acceptance test, amendments unset | `test_reproduces_rung_p3_hand_worked_numbers_exactly` — 3/3 still exact (0.321/5.83, 0.505/8.75, 0.593/7.50) |
| Both engines, one test (Venus@Sag) | `test_f1_default_off_v40_path_unchanged_venus_sag_enemy` + `test_f1_amendment_venus_sag_naisargika_only_neutral` | v4.0 enemy/0.30; v4.1 neutral/0.50 — matches spec exactly |
| Generalization (second synthetic pair) | `test_f1_amendment_generalizes_mars_leo_sun_conjunct_friend` | Mars@Leo/Sun: v4.0 neutral/0.50, v4.1 friend/0.60 — rule is general, not hardcoded |
| Surgical-scope, non-conjunct pairs | `test_f1_surgical_scope_non_conjunct_pairs_identical_both_engines` (parametrized) | v4.0 ≡ v4.1 exactly for Sun/Saturn and Jupiter/Saturn non-conjunct cases |
| Surgical-scope, non-dispositor co-occupant | `test_f1_surgical_scope_non_dispositor_conjunction_unaffected` | Structural proof — a co-occupant that isn't the dispositor cannot enter the function's inputs at all |
| Named-amendment gating | `test_f1_amendment_scoped_by_name_other_amendment_ids_do_nothing` | `amendments={'F7'}` does not fire F1 |
| Live engine plumbing | `test_f1_engine_default_off_matches_v40_rung_p3_marriage`, `test_f1_amendment_moves_marriage_occurrence_on_482012f1`, `test_f1_amendment_does_not_change_condition_axis`, `test_f1_amendment_leaves_unaffected_classes_untouched` | 4/4 live, DB-backed, PASS |
| Full v4 regression suite | `pytest` (unit + live + snapshot + karyatva) | 98 passed, 10 skipped (pre-existing, unrelated `DATABASE_URL` vs `DBURL` env gate) |
| PARĪKṢAKA independent review | Dispatched as a separate `code-reviewer` subagent, adversarial brief, 8 numbered checks | **PASS, zero findings** (see session record — re-ran tests independently, confirmed no scope leak, no R13 violation, no constant beyond the spec's rule, all call sites correctly threaded) |

**Result: CLOSED, PARĪKṢAKA-VERIFIED PASS.**

## Stage 2 — The side-by-side (CLOSED)

| Item | Detector | Result |
|---|---|---|
| Permanent probe committed | `platform/scripts/probes/probe_f1_side_by_side.py` | Commit `65698afd0` |
| Both charts, all 27 classes, live | Probe run against `482012f1` and `1c826d5a`, `lahiri_chitrapaksha` | 54/54 cells scored both ways, zero errors |
| Every moved cell traced | `F1_SIDE_BY_SIDE_v1_0.md` §3 — graha, D1 house, `chart_divisionals`/`chart_divisionals_id` fact_ids, arithmetic re-derivation matching observed Δocc | 10/10 moved cells (all on `482012f1`) traced to exactly 2 underlying dispositor-conjunction pairs (Venus/Jupiter D1 house 9; Saturn/Mars via career_setback's D10 slot) |
| Unmoved cells stated | `F1_SIDE_BY_SIDE_v1_0.md` §4 | 17/27 (482012f1) + 27/27 (1c826d5a) explicitly listed |
| Scoreboard context for moved classes | `F1_SIDE_BY_SIDE_v1_0.md` §5, `PROMISE_LAYER_SCOREBOARD_v1_0.md` re-stated beside old/new bands | Done — no verdict re-adjudication |
| Band-crossing summary | `F1_SIDE_BY_SIDE_v1_0.md` §6 | Exactly 1 of 54 cells crosses a label boundary: marriage, WEAK→MODERATE |
| Condition axis untouched (structural check) | Δcond = 0.000 for all 54 cells | Confirmed — §5.2 has no dignity-band input |

**Result: CLOSED.**

## Stage 3 — Merge + close at the boundary (THIS ENTRY)

**Risk assessment for the gate packet:** code is additive and default-off (`amendments:
frozenset[str] = frozenset()` everywhere it's threaded); the sole production call site
(`bo_pratijna.py`) never passes a non-empty value — production `bodha_pratijna` rows are
byte-identical before and after this merge, independently confirmed by
`test_f1_engine_default_off_matches_v40_rung_p3_marriage`. Docs + a new standalone probe script
carry zero runtime risk. **No deploy required** — no serving-path file changed, no migration, no
schema change. **Rollback = revert** the 3 commits (`8110d5fab`, `b37c5005a`, `65698afd0`) — no
data to unwind.

**What is NOT done by this cycle, by design (R20 item 4 belongs to the native + Fable, not this
session):** `bo_pratijna_karyatva.py`'s production registry is untouched; `bo_pratijna.py` (the
v3 writer, separately) and the v4 writer wiring the writer constructs `PratijnaV4Engine(reader)`
from are untouched; no `bodha_pratijna` row for any chart reflects F1; `PROMISE_LAYER_SCOREBOARD_
v1_0.md` was NOT re-run or re-published as if F1 were adopted. No adoption recommendation appears
in `F1_SIDE_BY_SIDE_v1_0.md` itself.

**Self-errors caught and corrected this cycle (R16):** the first draft of `F1_SIDE_BY_SIDE_v1_0.md`
§3.1 initially attributed `bereavement`/`major_gain`/`major_loss`'s movement to a Venus karaka
listing that does not exist in their `KaryatvaMap` entries; corrected in-place, before publication,
by re-checking the live `factor_ledger` and finding the true mechanism (house 2 and house 7 are
both Venus-ruled on this whole-sign chart, so any class citing either as a `primary_bhava`
house-lord slot inherits the shift through that route, not a karaka route). §3.2's first-draft
arithmetic also mis-stated career_setback's v4.0 band before being corrected against the live
ledger value (`great_enemy`/0.20, not the placeholder 0.30 first written). Both corrections are
visible in the published artifact's own text (not scrubbed), consistent with R16.

---

## R22 — ADOPTION RULING (native + Fable, 2026-08-09)

> **R22 — F1 ADOPTION.** Amendment F1 (dispositor-conjunction exception, R20 cycle 1) is ADOPTED
> into production, on the evidence of `F1_SIDE_BY_SIDE_v1_0.md`: 10/27 classes moved on chart
> `482012f1` (all traced to exactly two dispositor-conjunction pairs, no unexplained residual),
> 0/27 moved on chart `1c826d5a` (the amendment's narrow scope is inert absent its trigger, an
> honest confirmation not a defect), Δcondition = 0.000 everywhere (structurally guaranteed), and
> exactly one band-crossing cell in the whole 54-cell sweep (marriage, WEAK→MODERATE, the native's
> own married outcome). R13 (no tuning against any chart) and R16 (full disclosure) were upheld
> throughout Stages 0–2; this ruling is decided from the measurement + classical merit per R20
> item 4, not from a target number.

**Effect of this ruling:** opens the F1 AMENDMENT CYCLE's Stage 3+ as a new **ADOPTION** phase
(distinct from the AMENDMENT CYCLE's own three stages, already closed above) — this ledger
continues in the same file, same campaign home, per the governing prompt's framing ("same cycle,
adoption phase").

---

## ADOPTION PHASE — Stage 0 (R22 record + spec amendment) — CLOSED

| Item | Detector | Result |
|---|---|---|
| Branch cut from `main` | `git checkout -b f1-adoption/integration main` | Done, from `0bc61bb6c` |
| R22 recorded in ledger | This entry, verbatim ruling text | Done |
| `V4_RUBRIC_SPEC` v1.0 → v1.1 | New §2.1.1, F1 rule quoted verbatim from `AMENDMENT_F1_SPEC_v1_0.md`; frontmatter version + changelog bump; no other content touched | Done |

**Result: CLOSED.**

---

## ADOPTION PHASE — Stage 1 (production flip, builder + PARĪKṢAKA) — CLOSED

| Item | Detector | Result |
|---|---|---|
| `DEFAULT_AMENDMENTS = frozenset({'F1'})`, `bo_pratijna.py` | `engine = PratijnaV4Engine(reader, amendments=DEFAULT_AMENDMENTS)` | Commit `74450a782` |
| Version tags | `ENGINE_VERSION` "bo_pratijna_v4.0"→"bo_pratijna_v4.1.0"; `FORMULA_VERSION` "v4.0"→"v4.1.0" | Same commit |
| `amendments` param remains available | `bo_pratijna_v4_engine.py` untouched by this commit — `PratijnaV4Engine.__init__(..., amendments: frozenset[str] = frozenset())` unchanged | Confirmed |
| Test fixtures updated, evidence-cited | `RUNG_P3_EXPECTED`: marriage 0.321→0.450, separation 0.505→0.575 (childbirth unchanged 0.593) — source `F1_SIDE_BY_SIDE_v1_0.md` §1; offline comparison engine in the live test also gets `amendments=DEFAULT_AMENDMENTS` so it doesn't spuriously diverge from the now-F1-scored DB rows | Same commit |
| Full test suite green | `pytest` (writer + engine unit/live suites) | 99 passed, 13 skipped (DBURL unset — expected) |
| PARĪKṢAKA independent review | Dispatched as separate `code-reviewer` subagent, 5 numbered checks against the raw commit diff | **PASS** — diff is exactly default-flip + version tag + fixture update, nothing else rides along; no assertion weakened; new expected numbers cross-checked against `F1_SIDE_BY_SIDE_v1_0.md` and match exactly |

**Result: CLOSED, PARĪKṢAKA-VERIFIED PASS.**

---

## ADOPTION PHASE — Stage 2 (gate + deploy + rebuild) — CLOSED

| Item | Detector | Result |
|---|---|---|
| Gate packet (R22-cited) | PR #1130, "F1 ADOPTION CYCLE: production flip to v4.1.0 (R22)" | https://github.com/Marsys-Technologies/Madhav/pull/1130 |
| CI green | `gh pr checks 1130` | All checks pass, incl. `PRATIJÑĀ v4 Fixture Property Tests (Lane B3)` |
| Merge | Merge queue, `mergeStateStatus=CLEAN` | Squashed to `main` as `912402983` |
| Deploy verified | `gh run list` "Deploy to Cloud Run" for `912402983`; `gcloud run services describe amjis-sidecar` | Deploy run `conclusion=success`; `amjis-sidecar-00971-d28` Ready, 100% traffic |
| One real MCP call | `mcp_server_info` against the live deployed server | `catalog_version=catalog-1+t152+r653c2a1a98c8`, `stale=false` — server live and responding |
| Rebuild 482012f1 (sequential, first) | Real `BoPratijnaWriter.run(ctx)` via `cloud-sql-proxy` against production `amjis-postgres`, committed | `build_id=897b87e8-c056-4ca8-adf6-505dd03489f4`; 135 rows; `engine=bo_pratijna_v4.1.0`; `status_counts={'conditional': 57, 'promised': 78}` |
| Rebuild 1c826d5a (sequential, second) | Same real writer path | `build_id=ebc8335b-8357-4dbf-92ea-8ae9e019ebae`; 135 rows; `engine=bo_pratijna_v4.1.0`; `status_counts={'promised': 25, 'conditional': 105, 'denied': 5}` |
| **Acceptance — marriage row (482012f1)** | Live SELECT, `lahiri_chitrapaksha` | `status=conditional, occurrence_grade=0.450, condition_grade=5.830, engine_version=bo_pratijna_v4.1.0` — matches R16-cited target exactly |
| **Acceptance — 10 moved classes exact match** | Live SELECT vs `F1_SIDE_BY_SIDE_v1_0.md` §1 | All 10 occurrence/condition pairs on 482012f1 match the side-by-side's v4.1 column exactly (bereavement 0.719/10.00, business_launch 0.731/8.75, career_setback 0.880/7.50, foreign_settlement 0.740/7.50, major_gain 0.689/10.00, major_loss 0.695/10.00, marriage 0.450/5.83, property_acquisition 0.379/6.25, romantic_start 0.393/7.50, separation 0.575/8.75) |
| **Acceptance — 17 unmoved classes byte-identical to v4.0** | Live SELECT vs `V4_RUBRIC_SPEC`/side-by-side v4.0 baseline | All 17 unchanged (achievement_recognition 0.891, birth_anchor 0.564, career_advancement 0.771/7.50, career_change 0.774/6.25, career_entry 0.786/3.75, childbirth 0.593/7.50, chronic_onset 0.586/3.75, education_milestone 0.583/6.25, exam_outcome 0.500/6.25, financial_deception 0.841/0.00, illness_acute 0.471/6.25, parental_event 0.500/6.25, psychological_arc 0.661/0.00, relocation 0.486/8.75, spiritual_turn 0.740/7.50, surgery 0.471/6.25, travel_event 0.745/0.00) |
| **Acceptance — 1c826d5a all 27 rows byte-identical except version tag** | Live SELECT, all 27 classes | Every occurrence/condition value matches the v4.0 baseline exactly; only `engine_version`/`formula_version` changed to `v4.1.0` |
| **Acceptance — sweep corpus counts intact (detector query)** | `SELECT chart_id, count(*), count(distinct ayanamsha_id), count(distinct engine_version) ... GROUP BY chart_id` | Both charts: 135 rows, 5 ayanamshas, exactly 1 engine_version (`bo_pratijna_v4.1.0`) — no partial/mixed-version rows |
| **Acceptance — downstream consumer spot-read, stage2_promise** | `services.ka_kshetra.stage2_promise._fetch_pratijna(conn, 482012f1, lahiri_chitrapaksha)`, live | marriage: `status=conditional, grade=4.500` (0.450×10 rescale) — consumer sees the new value |
| **Acceptance — downstream consumer spot-read, mi_darshana** | `mi_darshana.py`'s own §5 query (lines 262-270), unmodified, run live, scoped to marriage | `status=conditional, grade=4.500, domain=relationship`; `derivation.engine_version=bo_pratijna_v4_engine.0.1+F1` — consumer sees the amendment tag |

**Result: CLOSED.**

---

## ADOPTION PHASE — Stage 3 (scoreboard v1.1) — CLOSED

| Item | Detector | Result |
|---|---|---|
| Published beside v1.0, not replacing | `PROMISE_LAYER_SCOREBOARD_v1_1.md` new file; `PROMISE_LAYER_SCOREBOARD_v1_0.md` untouched | Commit `5e400ff38` |
| Same method, same event citations | §1/§2/§3 "Lifetime outcome"/"Match basis" columns copied verbatim from v1.0 | Confirmed by diff — no re-adjudication |
| New v4.1 columns | §2/§3 occurrence/condition/status columns updated to the live Stage-2 production values; Δ column added | Cross-checked against the Stage 2 acceptance query output — exact match, all 10 moved + 17 unmoved cells |
| Delta section, old/new bands | §5, all 10 moved classes restated with v4.0/v4.1 occurrence + band-crossing flag | Sourced from `F1_SIDE_BY_SIDE_v1_0.md` §1/§6, cited in-line |
| THE MARRIAGE ANSWER updated | §4: `conditional / 0.450 MODERATE / 5.83 MODERATE`, stated as the first production verdict set by a measured, ruled, classically-cited amendment | Present verbatim |
| v1.0 remains the pre-amendment record | `PROMISE_LAYER_SCOREBOARD_v1_0.md` frontmatter/content unchanged by this cycle | Confirmed — zero edits to that file |

**Result: CLOSED.**

---
*F1_CYCLE_STATE.md v1.0 (2026-08-09). Created at Stage 3 close per the governing prompt's Stage 3
instruction ("Ledger close + morning report"). This is the campaign's only ledger entry — the
whole cycle closed in one session.*

*Continued 2026-08-09, same session, F1 ADOPTION CYCLE (R22) — same ledger file, adoption phase
appended above rather than a new file, per the governing prompt.*

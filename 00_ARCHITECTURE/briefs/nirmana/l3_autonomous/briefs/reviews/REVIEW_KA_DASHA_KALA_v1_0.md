---
artifact: KALA_BRIEF_REVIEW
canonical_id: REVIEW_KA_DASHA_KALA
version: "1.0"
status: REVIEW_COMPLETE
date: 2026-09-24
reviewed: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KA_DASHA_KALA_ELEVATION_BRIEF_v1_0.md (v1.0, DRAFT_FOR_INDEPENDENT_REVIEW)
reviewer: Fable 5.1 review agent, fresh context, read-only
worktree: /Users/Dev/madhav-l3/layer-briefs @ 4d8c6aa9b (branch l3/kala-layer-briefs); platform/ and platform-mcp/ byte-identical to the brief's base 9feac52d7 (`git diff --stat 9feac52d7 HEAD -- platform/ platform-mcp/` is empty)
method: every file:line re-read with sed -n / grep -n; no DB query; no external service; no prior audit artifact accepted as proof of code
---

# Review — `KA_DASHA_KALA_ELEVATION_BRIEF_v1_0`

## 1. Verdict

**REWORK.** The kernel description, the bypass finding and the IP-9 recommendation are correct
and verified at source, but the semantic delta (§4 items 2–4, 9–10) is built on two things the
brief did not read: L1 `chart_dashas` already carries a per-row `applies_to_this_chart_flag`
and a duration-heuristic `sandhi_flag` (so the brief's applicability and sandhi design either
contradicts or misreads the L1 authority it invokes under §N.5), and the live raw route already
returns `start_iso/end_iso` and an agreement count (so the "simpler baseline" and the ablation
are misdescribed). Two binding fields are misnamed. These are re-derivations, not line edits.

## 2. Findings

| # | sev | brief's claim (section) | found at source | correction |
|---|---|---|---|---|
| F1 | **MAJOR** | §2.4 "per-system applicability … authority L0 (DP02) — **no admitted applicability rule per system is cited anywhere**"; §4.3 "The service today has no admitted per-system applicability rule … Until L0 admits them, every non-Vimśottarī system is served `unqualified`"; §10 decision 2 raises an L0 request | L1 already asserts applicability on every row: `platform/migrations/881_nirmana_l1_ga_dashas_output_digest_spec.sql:57` lists `applies_to_this_chart_flag` as a `chart_dashas` value column; `platform/python-sidecar/ga_writers/ga_dashas_writer.py:1028` (`applies_to_chart: bool = True` default), `:1093` (written to every row), `:1717` (Aṣṭottarī: `applies_to_chart=True,  # FORENSIC: Rahu in 5H → applicable` — a canonical-chart-specific rule hardcoded for all charts), `:3405` (`False` only for `scope_cap` rows). Neither `tree_walk.py:79-92,110-119` nor `call_service_wrappers.ts:349-363` selects it. L0 also already carries per-system prose: `brahmagyan/l0_dasha_systems.py:115,137-139,171,201` (`conditions_for_use`). | The brief's own §5 rule ("a service value that disagrees with `chart_dashas` is a halt-worthy bug") is violated by its own delta: serving Aṣṭottarī as `unqualified` while L1 stamps `applies_to_this_chart_flag=True` on the same row is a disagreement with a cited L1 column. Rework §2.4/§4.3: (a) classify the L1 flag as *persisted-but-unused* and *unqualified* (its detector is a constant — §N.8), and reference it, never ignore it; (b) reframe decision 2 as "qualify the existing `conditions_for_use` prose into executable clauses and give `applies_to_this_chart_flag` a real detector" — an L0+L1 finding to raise, not a request into a void; (c) name `:1717` as an upstream defect in §11 or §10. |
| F2 | **MAJOR** | §0 "is, in code, the only asset that knows which of the seven daśā systems **apply** to a chart … and where they **agree or fall silent**" | `service.py:145-155` queries all seven systems unconditionally; `eligibility.py:59-66` scores a lord against caller-supplied `target_lords`/`related_lords` — there is no applicability logic anywhere in `services/ka_dasha_kala/`. `intersection.py:108-121` counts co-supporting systems; no `silent`/`not_applicable` state exists (`AgreementSummary` is `count` + `systems_agreeing`). The brief's own §2.4 concedes this. | §0 overstates the current code. State what the service *does* compute today (hierarchy from flat rows, target-relative eligibility band, atomic-segment agreement at DATE grain) and what the delta *adds* (applicability states, silence). The "clock authority" is a target, not a description. |
| F3 | **MAJOR** | §4.9 "Competent simpler baseline. The current raw query … lords and date-grain bounds, **no applicability, no agreement**"; §4.10 ablation "the served envelope must lose **exactly** `completeness_state` per system, `sandhi` at hour grain, and the concurrence rows, **and nothing else**" | `call_service_wrappers.ts:349-359` selects `start_iso, end_iso` (instants) alongside the DATE columns; `:367-380` computes `system_agreement_count`/`agreeing_systems` by exact `(start_date,end_date)` pair key; `:389-393` serves `cross_system_windows` and `high_agreement_count`. Meanwhile the service is DATE-grain today: `tree_walk.py:80,111` select `start_date, end_date` only; `DashaInterval.start_date: date` (`:55-56`). | The baseline *has* agreement (the F-13 exact-pair defect that `intersection.py:1-9` was written to replace) and *has* instants. Rewrite §4.9. The ablation must name what actually changes: (i) exact-pair agreement → atomic-segment agreement (the one distinction the service already earns); (ii) hour grain is *lost*, not gained, if IP-9 routes through the service before the B1 delta lands — state this ordering constraint explicitly in §4.7/§8. |
| F4 | **MAJOR** | §2.4 "`sandhi_flag` … computed fact, L1, present"; §4.4/§4.8/§7 Boundary row: "an instant inside a sandhi → `sandhi_flag=true` and the hour survives" | `ga_dashas_writer.py:1062`: `sandhi_flag = duration_days < 20` — a per-row short-period heuristic (the preceding comment records the prior formula was a tautology). It is not a property of an instant near a boundary. `sandhi_with_next_dasha_lord` / `next_dasha_start_iso` are post-pass fields (`:1089-1090`). | The Boundary row's expectation cannot be produced by L1's definition: at `end_iso − 1 s` of a multi-year AD, `sandhi_flag` is `false`. Either define the served sandhi as a derivation over `next_dasha_start_iso` (and say so, with its own `epistemic_class`) or drop "sandhi_flag=true inside a sandhi" from the proof row. The brief must not restate L1's flag under a different meaning (§N.7 item 1). |
| F5 | **MAJOR** | §4.2 "Typed qualification (binding B2), **no scalar**"; §5 preserves "the eligibility bands (as engineered inference, labelled)" | `eligibility.py:26-30` `BAND_SCORE = {EXACT: 0.85, RELATED: 0.50, NEUTRAL: 0.20}` and the module docstring `:9` "deliberately soft/probabilistic"; `EligibleWindow.eligibility_score: float` (`service.py:51`); `KaDashaKalaResult.high_agreement_count` (`:74`, threshold `>= 2` at `:234`). Saṅgam consumes the float as a score: `ka_sangam/engine.py:1445-1449` (`best = max(best, ew.eligibility_score)`). | The brief is silent on the existing scalar. Under context §1 / VA §10.2 ("unqualified conversion … into probability") the brief must say what happens to `eligibility_score` and `high_agreement_count` when IP-9 puts the service payload on a served route: label, null, or withhold. "No scalar" is not true of the payload as it stands. |
| F6 | **MAJOR** | §10 decision 2: "applicability clauses in `bg_dasha_systems`" for the seven systems | `brahmagyan/l0_dasha_systems.py` canonical ids: `vimshottari:100`, `ashtottari:123`, `yogini:148`, `kalachakra:179`, `chara_jaimini:209`, … `narayana:582`, `kp:620`. No entry named `chara_karaka`, `naisargika` or `mudda` (grep returns none). The service's `ALL_DASHA_SYSTEMS` (`tree_walk.py:40-43`) and L1 (`ga_dashas_writer.py:3205,3213,3217`) use `chara_karaka`, `naisargika`, `mudda`. | Three of the seven service ids have no L0 row under that id. Decision 2 as framed cannot bind for them. Add the vocabulary reconciliation (L0 `chara_jaimini` ↔ L1 `chara_karaka`; L0 rows for `naisargika`, `mudda`) to the L0 request, or scope decision 2 to the four systems that resolve. |
| F7 | **MAJOR** | §7 binding rows: OFFERS B1 with `claim_grain='approximated'` on prāṇa subdivisions (§4.4) | `KALA_SYNERGY_BINDING_v1_0.md:32`: `claim_grain` enum is `{instant_grain, date_grain, day_grade}`. `approximated` is not a member. The binding has a slot for this: `source_qualification ∈ {verse_cited, algorithmic_approximation, unsourced}` (`:45`). | Rename: prāṇa rows carry `claim_grain='date_grain'` (they are `date` arithmetic, `tree_walk.py:137-146`) and `source_qualification='algorithmic_approximation'`. Non-conformant as written. |
| F8 | **MAJOR** | §7 binding rows: OFFERS B5 "`coverage` = systems requested/consulted/unavailable" | `KALA_SYNERGY_BINDING_v1_0.md:69`: `coverage` is `{requested_horizon, completed_horizon, resolution, partitions_searched[], exclusions[], unsearched_regions[], completion_detector}` **on every result, including empty**. | The brief's `coverage` is a different object under the same name. Map systems→`partitions_searched[]`, unavailable→`exclusions[]`, the query window→`requested_horizon/completed_horizon`, grain→`resolution`, and name the `completion_detector`. Also: the wrapper's `LIMIT 400` (`call_service_wrappers.ts:362`) is an undisclosed cap on the served path — a B1/B5 "every cap disclosed" item the brief does not mention. |
| F9 | **MAJOR** | §7 Irrelevant control: "alias `Lahiri` vs `lahiri_chitrapaksha` → identical payload; detector: payload hash differs" | `service.py:161-165` passes `ayanamsha_id` straight to SQL equality (`tree_walk.py:84`); no alias resolver exists in scope (grep for `normalize_ayanamsha`/`resolve_ayanamsha`/`AYANAMSHA_ALIAS` across `platform/python-sidecar` and `platform/src/lib`: none). `Lahiri` returns zero rows today. | This row fails today and no §4 delta item introduces alias resolution. Either add the resolver to the delta (and to `may_touch`) or replace the row with a control the delta actually supports (e.g. system-order invariance only). A proof row the delta cannot satisfy is not a detector. |
| F10 | MINOR | §7 Positive: "canonical chart, `as_of` = a known AD midpoint, **`ayanamsha_id` omitted** → rows under `lahiri_chitrapaksha`" | `service.py:90-103`: `ayanamsha_id: str` is a required positional; only `confirm_systems_present` defaults (`:255`). The omission default lives in Pūrṇa-owned `call_service_wrappers.ts:328`. | State that this row's detector is on the IP-9 (wrapper) side and is owned as an interface-packet test, not a service test. |
| F11 | MINOR | §7 Relevant influence: "flip one system's admitted-rule fixture from absent to present → `unqualified → applied`" | No admitted-rule mechanism exists at any layer today (F1, F6). | Mark the row as gated on decision 2 (cannot run until an L0/L1 clause exists); F23 — a planned test is not a pass. |
| F12 | MINOR | frontmatter / §1 / §2.2: "W2 first-frontier source `47131772b` (dasha fails the whole request …)"; "present on this base" | `git merge-base --is-ancestor 47131772b HEAD` → **not an ancestor**; `git show --stat 47131772b` touches `ka_avadhi.py`, `ka_yojaka.py` and two tests only. The fail-closed code (`service.py:180-188`) landed on this base via `fa9857f00` (#2607, "deliver governed L0-L3 source execution"); `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md:151` records `47131772b` as stranded. The test exists: `tests/l3/test_w2_first_frontier_service_contracts.py:117`. | Cite `47131772b` as the W2 review tip (EXECUTION_LEDGER:263) and `fa9857f00` as the commit that carries the semantics on this base. |
| F13 | MINOR | §1 "[A: CURRENT_STATE §4.5]", "CURRENT_STATE §4.1" | Not in `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (its §4.1 is "Who updates", §4.5 "Consistency check with SESSION_LOG"; `ka_dasha_kala` appears only at `:1894`). Resolves in `MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md:144` (§4.1 row, verbatim) and `:242-243` (§4.5). | Name the file; `CURRENT_STATE` is a reserved canonical_id for a different artifact (CLAUDE.md §D). |
| F14 | MINOR | frontmatter: "parent_layer_contract … **blob** 793972c754b106688097dbc54536c1a9c270a793" | `git cat-file -t` → `commit` ("docs(data-plane): approve L3 Kala elevation campaign"). | Say "commit". |
| F15 | MINOR | §2.3 `dasha_consensus.py` "default `ayanamsha_id='lahiri'` at `:157`" | `:157` is `confirm_seven_systems_reachable(… ayanamsha_id='lahiri')`; the main entry `derive_dasha_consensus` (`:78-84`) requires `ayanamsha_id`. Only non-test importer: `services/kala_permission/permission.py:89` imports `derive_dasha_consensus`, not the `:157` function. | Per context §7: "no live caller found within scope for the `:157` default"; the L4 main path has no default. |
| F16 | MINOR | §2.2 "Writer `writer.py:1-40`" | File is 172 lines; docstring `:1-15`, `_run_selftest` `:33-84`, `run()` `:126-166`; `:156` raises `RuntimeError` on a failed self-test (the §N.8 fix, not mentioned). | Fix range; note the raise — it is the writer's only fail-closed detector and belongs in §5 preserved kernels. |
| F17 | MINOR | §3 Evidence "`:336-357` (own grouping over the flat rows)" | `:336-338` is a comment; `:349-363` is the SQL; the grouping (`windowMap`) is `:367-380`. | `:367-380`. |
| F18 | MINOR | §4.5 independence group "nakṣatra-family systems (Vimśottarī, Yoginī, Aṣṭottarī, Kālacakra) share the natal Moon's nakṣatra; `basis='declared_lineage'`" — no source cited | L0 anchor exists: `l0_dasha_systems.py:107` (`nakshatra_remainder`), `:130` (`nakshatra_remainder_conditional`), `:164`, `:194` (`nakshatra_pada_savya_apasavya`). | Cite the L0 `computation_method` per member; "declared" lineage still needs a declared source. |
| F19 | MINOR | §5 "The service stays a service (A01–A04)" | Only occurrence: blueprint `:232` "Services earn service proof, not invented rows (A01–A04)". The brief never expands the id. | Expand or cite `KALA_ELEVATION_BLUEPRINT_v1_0.md:232`. |
| F20 | NOTE | §3 "presented as 'no active windows'" | `call_service_wrappers.ts:385-395` returns `dasha_windows: []`, `count: 0`, `is_error: false` — no phrase, no coverage, no error. | Quote the envelope, not a paraphrase; the honest-empty defect is the absence of B5 coverage. |
| F21 | NOTE | §2.3 `ka_sangam` "R-6 RRV-08 marks `availability['dasha']='unavailable'`" | `engine.py:1402-1440` tracks `dasha_query_state ∈ {not_queried, ok, failed}` and `:1438-1440` names it an availability state; the literal `availability['dasha']` was not found in the lines read. | Cite the state variable and line. |
| F22 | NOTE | §7 OFFERS B1, B2, B4, B5; B3 not mentioned | Concurrence rows are offered to SC-6 (§4.5) — a citable window needs B3 (`window_ref = {asset_id, generation, id}`, content-addressed id). The service's only id is L1's `dasha_row_id` (a `uuid4` per build, `ga_dashas_writer.py:1065`). | State the B3 position: the concurrence row's id/generation, or declare B3 as DEMANDED from the SC-6 owner. |
| F23 | NOTE | §5 "Rollback: the additive payload is feature-flagged at the service boundary" | No flag exists; none is in the §4 delta. | Either add it to the delta or drop it from rollback. |
| F24 | NOTE | §1 does not cite `dossiers/KA_GRAHA_SANCARA_KA_DASHA_KALA_DOSSIER_v1_0.md` (2026-09-20) | It exists and already records `eligibility_score` as "a new derived signal (a soft prior)" (`:285, :376`) — relevant to F5. | Cite it in §1 (guide §1: start from what exists). |
| F25 | NOTE | `may_touch` names `pipeline/orchestrator/service_probes.py (ka_dasha_kala clause only)` | `:871-899`: the probe is a DB-free proxy by ruling D-CND-34 (#2071). | Any change there re-opens a ruling; say so or remove from `may_touch`. |

## 3. Citations verified

| brief citation | resolved to | status |
|---|---|---|
| `asset_registry_seed.ts:2252-2260` | `platform/scripts/seed/asset_registry_seed.ts:2246-2262` (entry); cited fields at `:2252-2260` | resolved |
| `writer.py:1-40` | `services/ka_dasha_kala/writer.py` (172 lines) `:1-15, :33-84, :126-166, :156` | range wrong, content right (F16) |
| `service.py:77-252`, `:32`, `:39`, `:59`, `:90`, `:252` | exact | resolved |
| `tree_walk.py:47-168`, `:125` | exact; plus `:79-92`, `:110-119` DATE-column SELECTs | resolved (answers brief §11 item 1: DATE columns) |
| `eligibility.py:18-69` | exact; `:26-30` BAND_SCORE floats | resolved |
| `intersection.py:38-108`, `:108` | exact | resolved |
| `ka_sangam.py` imports `KaDashaKalaService` | `pipeline/orchestrator/writers/ka_sangam.py:38` (import), `:321` (instantiated at run time) | resolved (answers §11 item 5 for the writer) |
| `ka_sangam/engine.py` imports/uses | `:1395-1440` (`query()` called), `:1445-1449` (`eligibility_score` consumed) | resolved (run-time use confirmed) |
| `ph_nimitta/dasha_consensus.py:157` | exact (`confirm_seven_systems_reachable` default); main fn `:78-84` requires the id | resolved (F15) |
| `service_probes.py:871+` | `:871-899, :940-952` | resolved |
| `writers/ka_avadhi.py:29` | exact | resolved |
| `writers/ka_jivana_parva.py:85-90` | `:85-91` SELECT; `depends_on` declaration is `asset_registry_seed.ts:2404` | resolved |
| `call_service_wrappers.ts:296-360` | descriptor `:272-399`; handler `:322` | loose |
| `call_service_wrappers.ts:328` (`?? 'lahiri'`) | exact | resolved |
| `call_service_wrappers.ts:336-357` (grouping) | SQL `:349-363`; grouping `:367-380` | wrong lines (F17) |
| `call_service_wrappers.ts:227`, `:595` (`DEFAULT_AYANAMSHA`) | exact; `constants.ts:2` = `'lahiri_chitrapaksha'` | resolved |
| `kala_views/dasha_sandhi.ts` reads L1 directly | `:173-186` via `marsys://tool/L1/get_dashas` (not the service); `:213-214` DATE strings | resolved (answers §11 item 2) |
| REGISTER `:137` | `MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md:137` verbatim | resolved |
| Strategy §6.1 L3-A02; L3-U02 | `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md:272`; `:442` | resolved |
| CURRENT_STATE §4.1 row; §4.5 | `MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md:144`; `:242-243` — **not** `CURRENT_STATE_v1_0.md` | resolved in a different file (F13) |
| W0 field register | `MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md:22, :593-597` | resolved |
| Blueprint §3.5 row 2; §16.2; §3.3 SC-1/SC-6/SC-10; §12.2 IP-2/IP-9; §17.1; A01–A04 | `KALA_ELEVATION_BLUEPRINT_v1_0.md:318; :900; :280/:285/:289; :756/:763; :923-941; :232` | resolved |
| KALA_DELEGATED_DECISIONS D-H | `KALA_DELEGATED_DECISIONS_v1_0.md:351-361` | resolved |
| `47131772b` | exists; not an ancestor of HEAD; touches Avadhi/Yojaka/tests only | partial (F12) |
| blob `99953b54…` (clock contract) | blob; `:61` "`start_iso`/`end_iso` half-open intervals, never date-truncated" | resolved |
| "blob" `793972c754…` | commit | mislabelled (F14) |
| `9feac52d7` base | code dirs identical to HEAD `4d8c6aa9b` | resolved |
| `chart_dashas` columns (`start_iso/end_iso`, `sandhi_flag`, `next_dasha_start_iso`, `is_truncated_at_window_*`) | `migrations/881_…:57`; `ga_dashas_writer.py:1062-1095` | resolved; plus `applies_to_this_chart_flag` (F1) |
| Synergy binding B1–B7 | `KALA_SYNERGY_BINDING_v1_0.md:28-34, :40-47, :53-56, :62-63, :69-70, :76-79, :83-86` | resolved |
| Foundation F04 classes; F12 roles | `MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md:63-66`; `:39` | resolved — `COMPUTED_FACT_CONFIGURATION`, `INTERPRETIVE_INFERENCE`, `QUALIFIED_RULE`, `applicability` are all admitted names |

## 4. What I could not verify

- **PR #2695** (open, "not on main"): no GitHub access in this session; not checked.
- **Live incidence** of the zero-row default path and the canonical rows' `ayanamsha_id` value: no DB access; consistent circumstantial evidence only (`writer.py:26`, `ka_jivana_parva.py:89` both pin `lahiri_chitrapaksha`).
- **Lane D §3 / Lane E §3.1 / Lane F §2a,§2d / T1 / STATE.md ★**: not re-opened as artifacts (template rule); every code claim the brief attributes to them was re-checked directly above.
- **Service-call latency**: unmeasured, as the brief states.
- **`origin/l3/kala-elevation-readiness` tip = 9feac52d7**: remote not consulted; local code identity to HEAD verified instead.
- **Whether `ka_kshetra` S3 reads `chart_dashas`** (§1 row): out of this asset's citation set; not checked.

## 5. Conformance to the binding (B1–B7)

| field as written in the brief | binding | status |
|---|---|---|
| `t_start`, `t_end` (timestamptz from `start_iso/end_iso`) | B1 | conformant |
| `inclusivity='closed_open'` | B1 | conformant (matches `intersection.py:34` `[start, end)`) |
| `time_basis='event_instant'` | B1 | conformant |
| `claim_grain='instant_grain'` | B1 | conformant |
| **`claim_grain='approximated'`** (prāṇa rows, §4.4) | B1 enum `{instant_grain, date_grain, day_grade}` | **non-conformant** — use `source_qualification='algorithmic_approximation'` (B2 `:45`) + `claim_grain='date_grain'` (F7) |
| `n_subdivisions` | — | extra, harmless |
| `epistemic_class`, `completeness_state` (six values), `operator_role='applicability'`, `comparable_with ∈ {self, different_convention}`, `tier_basis='relative_uncalibrated'` | B2 | conformant names and values |
| `source_qualification`, `corpus_verifiable` | B2 | not offered — should be, for the prāṇa approximation and for the (absent) applicability rule |
| `independence_group` with `basis='declared_lineage'`; `declared_current_count` | B4 | conformant names; lineage unsourced (F18) |
| **`coverage` = "systems requested/consulted/unavailable"** | B5 seven-key shape, on every result incl. empty | **non-conformant** shape (F8) |
| B3 (`window_ref`, `generation`, content-addressed id) | B3 | **not addressed** while offering concurrence rows to SC-6 (F22) |
| SC-6 verdict `{supports, opposes, silent, not_applicable}`, `jurisdiction`, `method_version` | blueprint §3.3 SC-6 `:285` | conformant |
| B6 single producer | — | n/a for this asset (no vedha/mūrti/contact verdict); node convention n/a |
| B7 tests 5/6/7/9 mapped to Duplication/Context/Boundary/Delivery rows | B7 | mapped; Boundary row's sandhi expectation is unsatisfiable under L1's definition (F4); Irrelevant-control row unsatisfiable under the stated delta (F9) |

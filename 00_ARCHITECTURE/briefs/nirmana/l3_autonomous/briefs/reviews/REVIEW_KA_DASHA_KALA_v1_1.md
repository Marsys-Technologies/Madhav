---
artifact: KALA_BRIEF_REVIEW
canonical_id: REVIEW_KA_DASHA_KALA
version: "1.1"
status: REVIEW_COMPLETE
date: 2026-09-24
reviewed: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KA_DASHA_KALA_ELEVATION_BRIEF_v1_0.md (v1.1, DRAFT_FOR_INDEPENDENT_RE_REVIEW)
prior_review: REVIEW_KA_DASHA_KALA_v1_0.md (25 findings, REWORK)
reviewer: Fable 5.1 review agent, fresh context, read-only
worktree: /Users/Dev/madhav-l3/layer-briefs @ 27b0146f3 (branch l3/kala-layer-briefs); platform/ and platform-mcp/ byte-identical to the brief's base 9feac52d7 (`git diff --stat 9feac52d7 HEAD -- platform/ platform-mcp/` is empty)
method: every v1.0 finding re-checked against the v1.1 text AND at source (sed -n / grep -n), not against the §12 disposition claim; every new v1.1 citation re-read; no DB query; no network; no prior audit artifact accepted as proof of code
---

# Re-review — `KA_DASHA_KALA_ELEVATION_BRIEF` v1.1

## 1. Verdict

**ACCEPT_WITH_CORRECTIONS.** Twenty-three of the twenty-five v1.0 findings are resolved at
source and two are partial (F4, F9); the semantic delta now reads what the code does. The v1.1
rewrite introduced three MAJOR defects that are bounded edits, not re-derivations: a *required*
`as_of` that contradicts the brief's own "additive payload, callers unchanged" claim and would
break the two consumers it fences off (N1); a boundary proof row whose `hours_to_boundary ≈ 0
both sides` cannot be produced by the brief's own §4.4 definition — the F4 defect class
re-entering by a new door (N2); and an ablation whose "differ in exactly (i)–(iv), identical in
lords and instants" cannot hold because the service prunes subtrees the route returns flat (N3).
Fix N1–N3 before `PROPOSED_FOR_NATIVE_RULING`; the rest are line corrections.

## 2. Findings

| # | sev | brief's claim (section) | found at source | correction |
|---|---|---|---|---|
| N1 | **MAJOR** | §4.8 "`as_of` is a **required** parameter echoed in the result"; §7 Positive/Boundary rows drive the *service* with `as_of` (owner L3); §5 "additive payload so `dasha_consensus.py` (id required, `:78-84`) and `ka_sangam.py` need no change first"; `must_not_touch` fences both callers | `service.py:90-103`: `query()` has no `as_of`; it is a window query (`date_start, date_end`). Both live callers invoke it by keyword without one: `services/ka_sangam/engine.py:1410-1423`; `services/ph_nimitta/dasha_consensus.py:109-118`. A new *required* positional is a signature change that raises `TypeError` in both — not additive, and both files are in `must_not_touch`. Also unstated: whether `as_of` is a point filter over the window result or a new entry point (membership at an instant is not what a window query returns) | Make it `as_of: Optional[datetime] = None` (window mode unchanged when absent), or add a separate `at(as_of)` method; state which; keep "additive" true. Move the boundary/membership semantics to the method that has them |
| N2 | **MAJOR** | §7 Boundary/precision: "`as_of = end_iso − 1 s` / `+ 1 s` → membership flips; **`hours_to_boundary` ≈ 0 both sides**; L1's `sandhi_flag` **unchanged** (it is a period property)"; §4.4 defines `hours_to_boundary` "computed from L1's `next_dasha_start_iso`" | `ga_dashas_writer.py:2945` `compute_sandhi_post_pass`: `next_dasha_start_iso` = the **next sibling row's** `start_iso` (`+18..+22`). At `end_iso + 1 s` the containing row is that next period, whose `next_dasha_start_iso` is the one after it → `hours_to_boundary` = that period's whole duration, not ≈ 0. And the two instants fall in two different rows, each with its own `sandhi_flag = duration_days < 20` (`:1062`) — "unchanged" is not guaranteed; a 15-day AD followed by a 3-year AD flips it | Define `hours_to_boundary` as the signed distance to the **nearest** boundary of the containing row (`min(as_of − start_iso, next_dasha_start_iso − as_of)`, with `start_iso` also cited), or expect ≈ 0 on the `− 1 s` side only. Replace "unchanged" with "each side carries its own row's `sandhi_flag`, never relabelled" — that is the F4 detector |
| N3 | **MAJOR** | §4.12 "the served envelope must differ in **exactly** (i) … (iv) — and be **identical** in lords and instants" | The two selections are not the same row set. Service: prunes every MD subtree below `min_band` (default `RELATED`) before querying children (`tree_walk.py:225-232`; `eligibility.py:84-86`), descends to `max_level` (default 4; Saṅgam passes 3 `engine.py:1421`; L4 passes 4 `:116`), **requires** `target_lords`, and adds prāṇa rows on request. Route: returns every level's rows overlapping the window, filtered by `lord_graha IN target_lords` **at any level with no subtree pruning** (`call_service_wrappers.ts:340-346`), or **all rows** when `target_lords` is empty (`:331`), capped at 400 (`:362`). On the same inputs the payloads differ in row membership before (i)–(iv) is reached; the "exactly" clause fails for reasons unrelated to the elevation, so the ablation cannot distinguish elevation from plumbing | State the alignment the differential runs under: `min_band=NEUTRAL`, `max_level=4`, `prana_grain=False`, identical non-empty `target_lords`, fixture < 400 rows (or cap removed). Or define the differential over the **intersection** of the two row sets and report the membership delta as a fifth, labelled difference. Either way the row can then go red for the right reason |
| N4 | MINOR | §0 / §2.2 "all seven systems queried **unconditionally** (`service.py:145-155`)"; §4.7 `completion_detector: 'all_seven_systems_read_or_whole_request_unavailable'`, `partitions_searched: [systems]` | `:100` `systems: Optional[Set[str]] = None`; `:145-155` is precisely the branch that accepts a caller subset (unknown ids raise `:150-154`); L4 passes `systems=ALL_7_SYSTEMS` (`dasha_consensus.py:117`). The result already carries `systems_queried=active_systems` (`:246`) | "All seven **by default**; caller may restrict". `partitions_searched` and the completion detector must be over `active_systems`, not a constant seven |
| N5 | MINOR | §7 Irrelevant control: "reorder the seven systems in the request → identical payload; detector: hash differs" (the F9 replacement) | `systems` is a `Set[str]` (`:100`) and the service sorts it (`:146`, `:155`). There is no order to permute; the row cannot go red (B7 `:83-86`; Foundation F23 `:50`, F28 `:55`) | Replace with a control the code can fail: mutate an unread `chart_dashas` column in the fixture (`lord_sign`, `citation_human`) → payload hash identical; or permute `related_lords` |
| N6 | MINOR | frontmatter `accepted_upstream_contract`: blob `99953b54…` "(chart_dashas: start_iso/end_iso half-open, **sandhi_flag, next_dasha_start_iso, is_truncated_at_window_\*, applies_to_this_chart_flag**)" | `git cat-file -p 99953b54…`: `:59-63` names only `start_iso`/`end_iso` half-open; grep for the four other column names in the blob → **no match**. Those columns are established by `migrations/881_…:57` and `ga_dashas_writer.py:1062-1095` | Attribute the four columns to migration 881 / the writer, not to the clock-contract blob |
| N7 | MINOR | §4.9 "the wrapper resolves the omitted id to `DEFAULT_AYANAMSHA` and **any legacy alias through the one map (SC-10)** at the wrapper" | No alias map exists in the wrapper's tree: grep `platform/src` for alias/normalise/resolve-ayanamsha → none; blueprint SC-10 (`:289`) and guard G-6 (`:858`) specify a bare-default lint, not an alias map. One does exist a tier up: `platform-mcp/src/lib/ayanamsha.ts:8-10,26-27` (`resolveChartFactsAyanamsha`: `lahiri → lahiri_chitrapaksha`, empty → `lahiri_chitrapaksha`), wrapped by `registry_bridge.ts:108` `normalizeAyanamsha`; `L3_kala/call_service_wrappers.ts` does not import it (`:22` imports only `DEFAULT_AYANAMSHA` from `../../constants`) | Either cite `platform-mcp/src/lib/ayanamsha.ts` as "the one map" and put its adoption by `call_dasha_eligibility` into IP-9's packet, or drop "any legacy alias" from the delta. F9 is otherwise resolved (the service requires the canonical id, `tree_walk.py:84`) |
| N8 | MINOR | §7 Context/missingness: "wrong chart id → **reject**" | `service.py:136-155` validates `max_level`, the date pair and `systems` only; an unknown chart id yields zero rows from `tree_walk.py:79-92` and an empty result. No §4 item adds chart-existence checking | Add it to the delta (with its failure semantics), or expect "empty result **with** `coverage` naming the chart partition and `completion_detector`" — the B5 discipline, and a real detector |
| N9 | MINOR | §4.6 DEMANDS B3 "a content-addressed period identity `(chart, system, level, lord, t_start)` from SC-3's packet" | SC-3's packet publishes the period identity as `(chart, signal, system, level, t_start)` (`KALA_ELEVATION_BLUEPRINT_v1_0.md:885`) | Demand in the packet's vocabulary, or state the divergence (`lord` vs `signal`) and why — a vocabulary split is the SC-10 class the brief itself raises |
| N10 | MINOR | §4.7 coverage `resolution:'event_instant'` | B5 `resolution` per Strategy §3 "Search coverage" (`:96`) is "exact/coarse resolution"; `event_instant` is the B1 `time_basis` value (`KALA_SYNERGY_BINDING_v1_0.md:31`) | `resolution:'exact'` (or `'instant'`); keep `time_basis='event_instant'` on B1 |
| N11 | MINOR | `may_touch` lists `call_service_wrappers.ts:272-399` and `platform-mcp/src/tools/kala_views/dasha_sandhi.ts` ("interface packet only") while §4.9 says "Pūrṇa owns the TS" | `KALA_ASSET_BRIEF_CONTEXT_v1_0.md:103-105`: kala_views belongs to Pūrṇa, "Do not design changes to it … let Pūrṇa own the code"; guide §11 forbids editing `kala_views/` or any Pūrṇa-owned surface. Carried from v1.0 unflagged; v1.1's §4.9 now contradicts its own frontmatter | Move both TS paths out of `may_touch` into an "interface-packet targets (Pūrṇa-owned)" line; what L3 may touch is the sentinel test under `tests/l3/` |
| N12 | NOTE | §4.3 per-system `completeness_state` includes "`unavailable` where the L1 read failed (whole request, unchanged)"; §4.7 `exclusions: [systems unavailable/…]` | `service.py:183-188` raises on the first failing system; no payload is returned. A per-system `unavailable` can never appear, and `exclusions` can never list one | Say `unavailable` is result-level; drop it from the per-system enum-as-used or state when it can appear |
| N13 | NOTE | §7 Delivery sentinel: "`completeness_state='unqualified'` with reason on Kālacakra only" | Every system is `unqualified` today (§4.3) — the state does not distinguish the sentinel; only a sentinel-specific reason value can | Name the sentinel value (e.g. `reason='SENTINEL_…'`) so "absent" is detectable |
| N14 | NOTE | §12 "F19 accepted (§5 **expanded**)"; "F21 accepted — `dasha_query_state` (§2.3 wording …)" | grep the brief: no `A01`; no `dasha_query_state`/`RRV-08`/`availability[` outside §12. Both were resolved by **deletion**, which is fine | Say "removed", not "expanded"/"reworded" |
| N15 | NOTE | §7 gated row "(… F23 — a planned test is not a pass)" | In this brief `F23` also names the v1.0 feature-flag finding. The intended reference is Foundation gate F23 (`MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md:50`) | "Foundation F23" |
| N16 | NOTE | §0 / `goal_objective`: "registered as the layer's clock authority … its registration claims" | `asset_registry_seed.ts:2246-2262` registers "Daśā Eligibility Service"; "clock authority" is the blueprint's phrase (`:318`) | "which the blueprint names the clock authority" |
| N17 | NOTE | `source_revision`: "byte-identical to HEAD 4d8c6aa9b" | HEAD is `27b0146f3`; identity still holds (`git diff --stat 9feac52d7 HEAD -- platform/ platform-mcp/` empty) | Drop the HEAD sha or update it |
| N18 | NOTE | §2.4 `high_agreement_count` "never served as confidence"; §4.5 scalar blast radius = Saṅgam only | L4 `dasha_consensus.py:121-133` converts `cross_dasha_agreement.count` into `confidence_multiplier = min(1.0, max(0.5, max_count/7))` and `high_agreement = max_count >= 4`; it reaches `ph_nimitta.py:236,277` / `ph_sodhana` as `dasha_consensus_count`. A second scalar derived from this payload, one layer up | Not this brief's to change; record it in §2.3 / §10.4 as L4's share of the coordinated packet so the labelling claim is scoped honestly |

## 3. Citations verified

| brief citation | resolved to | status |
|---|---|---|
| `service.py:32, :39, :51, :59, :74, :90-103, :145-155, :161-165, :180-188, :234, :252` | exact; note `:100` `systems: Optional[Set[str]]` (N4), `:136-155` validation set (N8) | resolved |
| `tree_walk.py:40-43, :55-56, :80, :84, :111, :125, :137-146` | exact | resolved |
| `intersection.py:1-9, :34, :72, :108-121` | exact; `service.py:197-205` confirms the service computes agreement via `intersect_segments`/`agreement_for` | resolved |
| `eligibility.py:9, :26-30, :59-66` | exact; `:84-86` prune rule (N3) | resolved |
| `writer.py` 172 lines, `:26`, `:156` | exact (`raise RuntimeError` at `:156`) | resolved |
| `ga_dashas_writer.py:1028, :1062, :1065, :1089-1090, :1093, :1717, :3205, :3213, :3217, :3405` | exact | resolved |
| `compute_sandhi_post_pass` (`:2945`) — `next_dasha_start_iso` = next row's `start_iso` | `:2945+18..+22` | resolved (N2) |
| `migrations/881_…:57` `applies_to_this_chart_flag` in value_columns | exact | resolved |
| `brahmagyan/l0_dasha_systems.py:100, :107, :115, :123, :130, :137-139, :148, :164, :171, :179, :194, :201, :209, :582, :620`; no `chara_karaka`/`naisargika`/`mudda` | exact; grep none | resolved |
| `call_service_wrappers.ts:22 (import), :227, :272-399, :322, :328, :331, :340-346, :349-363, :362, :367-380, :385-395, :595` | exact | resolved |
| `constants.ts:2` `DEFAULT_AYANAMSHA` | `platform/src/lib/retrieval/registry/constants.ts:2` = `'lahiri_chitrapaksha'` | resolved |
| `kala_views/dasha_sandhi.ts:173-186, :213-214` | exact (`marsys://tool/L1/get_dashas`; DATE strings) | resolved |
| `writers/ka_sangam.py:38, :321`; `ka_sangam/engine.py:1395-1440, :1445-1449` | exact; `:1410-1423` the `query()` call without `as_of` (N1) | resolved |
| `ph_nimitta/dasha_consensus.py:78-84, :157`; `kala_permission/permission.py:89` | exact; `:106-118` imports and calls `KaDashaKalaService.query()` (hub claim holds); `:121-133` confidence multiplier (N18) | resolved |
| `service_probes.py:871-899, :940-952` (D-CND-34, #2071) | exact | resolved |
| `writers/ka_avadhi.py:29`; `writers/ka_jivana_parva.py:85-91`; seed `:2246-2262`, `:2404` | exact | resolved |
| `tests/l3/test_w2_first_frontier_service_contracts.py:117` | exact | resolved |
| `platform-mcp/src/lib/ayanamsha.ts:8-10, :26-27`; `registry_bridge.ts:108` | alias map exists here, uncited by the brief | resolved (N7) |
| `KALA_SYNERGY_BINDING_v1_0.md:28-34, :40-47, :53-56, :62-63, :69-70, :83-86` | exact; `completeness_state` six values incl. `unqualified`/`inapplicable`; `comparable_with` enum; `source_qualification` enum; B5 seven keys | resolved |
| Blueprint `:232` (A01–A04), `:280-289` (SC-1…SC-10), `:318` (§3.5 row 2), `:390` (ladder: `PLAN_REVIEWED; W2 source accepted`), `:756/:763` (IP-2/IP-9), `:846-858` (§15, G-6), `:885` (SC-3 period identity), `:900` (§16.2) | exact | resolved; `:885` tuple differs (N9) |
| Strategy `:78` (§2 close: "cannot earn full completion …"), `:91` (Clock interval), `:96` (Search coverage), `:272` (L3-A02), `:442` (L3-U02) | exact | resolved (N10 on `resolution`) |
| `MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md:144, :242-243` | exact | resolved |
| W0 field register `:22, :593-597`; D-H `:351-361`; REGISTER `:137`; dossier `:285, :376`; Foundation `:39, :50, :55, :63-66` | exact | resolved |
| Product v2.2 §5.2 (`:181`), §7.1 (`:266`) | headings exist; §5.2 is also the guide §11's own citation for the no-scalar rule | resolved |
| `KALA_ASSET_BRIEF_CONTEXT_v1_0.md:103-105`; guide §10–§12 (`:147-159`) | exact | resolved (N11) |
| blob `99953b54…:59-63` | half-open `start_iso/end_iso` only; four other columns absent | partial (N6) |
| commit `793972c754…` ("approve L3 Kala elevation campaign") | `git cat-file -t` → commit | resolved |
| `fa9857f00` (#2607) ancestor of HEAD; `47131772b` not an ancestor, touches Avadhi/Yojaka/tests | verified both | resolved |
| `MADHAV_DATA_PLANE_EXECUTION_LEDGER_v1_0.md:263`; `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md:151` | exact | resolved |
| `9feac52d7` base = HEAD code | diff empty | resolved (N17 sha stale) |

## 4. What I could not verify

- **PR #2695** content/state: no GitHub access (the `github` MCP failed to connect this session).
- **Live incidence** of the zero-row default path; the canonical rows' `ayanamsha_id`; whether a t3 event exists for `ka_dasha_kala` (`EVENTS.jsonl` mentions the asset only in dossier/no-op entries `:21-22`, `:53` — consistent with "no t3 event", not proof): no DB access.
- **Service-call latency**: unmeasured, as the brief states.
- **`origin/l3/kala-elevation-readiness` tip**: remote not consulted; local code identity verified instead.
- **Whether Kṣetra S3 reads `chart_dashas`**: outside this asset's citation set; not checked.
- **Lane D/E/F, T1, STATE.md ★**: not re-opened as artifacts (template rule); every code claim was re-checked directly.
- **Whether Pūrṇa's queue will accept the two TS packet targets**: a process fact, not a source fact.

## 5. Conformance to the binding (B1–B7)

| field as written in the brief | binding | status |
|---|---|---|
| `t_start`, `t_end` (`timestamptz` from `start_iso/end_iso`); `inclusivity='closed_open'`; `time_basis='event_instant'`; `claim_grain='instant_grain'` | B1 | conformant |
| prāṇa rows: `claim_grain='date_grain'` + `source_qualification='algorithmic_approximation'` + `n_subdivisions` | B1/B2 | conformant (F7 resolved); `n_subdivisions` extra, harmless |
| `epistemic_class` (`COMPUTED_FACT_CONFIGURATION`, `INTERPRETIVE_INFERENCE`, `QUALIFIED_RULE` claimed/constant), `completeness_state ∈ {applied, unqualified, unavailable, inapplicable}`, `operator_role='applicability'`, `comparable_with ∈ {self, different_convention}`, `tier_basis='relative_uncalibrated'`, `source_qualification` on band and prāṇa | B2 | conformant names and values; `unavailable` per-system is unreachable (N12) |
| reason `applicability_detector_constant` | — | extra, harmless (a reason string beside `unqualified`) |
| `corpus_verifiable` | B2 | still not offered — should be `false` on the constant applicability flag and the prāṇa approximation |
| `window_ref`; DEMANDS a content-addressed period identity | B3 | addressed (F22 resolved); tuple vocabulary differs from SC-3's (N9) |
| `independence_group` `basis='declared_lineage'`, `declared_current_count` | B4 | conformant; lineage now sourced to L0 `computation_method` (F18 resolved) |
| `coverage` = `{requested_horizon, completed_horizon, resolution, partitions_searched[], exclusions[], unsearched_regions[], completion_detector}` on every result incl. empty | B5 | conformant shape (F8 resolved); `resolution` value is a B1 term (N10); `partitions_searched` must be `active_systems` (N4) |
| `truncated`, `returned`, `available` (IP-9 cap disclosure) | B5 / SC-5 | conformant intent; names are the brief's own — acceptable as an interface-packet field set |
| SC-6 verdict `{supports, opposes, silent, not_applicable}`, `jurisdiction`, `method_version` | blueprint §3.3 SC-6 (`:285`) | conformant |
| `hours_to_boundary`, `next_lord` (derived boundary object) | — | outside B1–B7 vocabulary but not in conflict; carries its own `epistemic_class` (F4 resolved as a definition; its proof row is N2) |
| B6 single producer | — | n/a for this asset |
| B7 tests 5/6/7/9 = duplication, context, boundary, delivery rows | B7 | mapped; boundary row unproducible as written (N2); context row's "reject" unsupported (N8); irrelevant-control row cannot fail (N5); delivery sentinel indistinguishable by state (N13) |

## 6. Disposition of the 25 v1.0 findings (verified at source, not from §12)

| v1.0 | status | where in v1.1 / what was checked |
|---|---|---|
| F1 | RESOLVED | §1 L1 row, §2.4, §4.3, §5 (a), §10.2: flag exists, constant detector, referenced not ignored, `:1717` raised as upstream defect — `:1028/:1093/:1717/:3405` re-read |
| F2 | RESOLVED | §0 states what the service computes today vs the delta; "unconditionally" is a residual wording error (N4), not an overstatement of capability |
| F3 | RESOLVED | §4.11 baseline now has instants, exact-pair agreement, `LIMIT 400`; ordering constraint in §4.2/§8; ablation names atomic-segment agreement — but the ablation's "exactly/identical" clause is a new defect (N3) |
| F4 | PARTIAL | §2.4/§4.4 correctly separate `sandhi_flag` (`< 20 d`) from a derived boundary distance; the §7 boundary row still carries an expectation the definition cannot produce (N2) |
| F5 | RESOLVED | §2.4, §4.5, §10.4 label `eligibility_score`/`high_agreement_count`, withheld from served confidence; L4's derived multiplier is a scope note (N18) |
| F6 | RESOLVED | §1 L0 row, §5 (b), §10.2 name `chara_karaka`/`naisargika`/`mudda` absent and `chara_jaimini` present — grep re-run |
| F7 | RESOLVED | `claim_grain='date_grain'` + `source_qualification='algorithmic_approximation'` (§2.4, §4.2) |
| F8 | RESOLVED | §4.7 seven-key coverage; `LIMIT 400` disclosed (§0, §3, §4.7, §7 cap row); `resolution` value off (N10) |
| F9 | PARTIAL | alias proof row removed; service requires canonical id (`tree_walk.py:84`) — but §4.9 relocates the unsupported "one map at the wrapper" claim into the delta (N7) and the replacement control cannot fail (N5) |
| F10 | RESOLVED | separate "Positive (wrapper)" row, owner "IP-9 (Pūrṇa code, L3 sentinel)" |
| F11 | RESOLVED | row gated on §10 decision 2, owner "L3 (after L0)"; reference wording (N15) |
| F12 | RESOLVED | frontmatter + §1: `fa9857f00` (#2607) is an ancestor, `47131772b` is not — both re-verified with `git merge-base` |
| F13 | RESOLVED | §1 names `MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md:144`, `:242-243` |
| F14 | RESOLVED | "commit 793972c7…" — type re-verified |
| F15 | RESOLVED | §2.3: `:157` default is on `confirm_seven_systems_reachable`, no live caller in scope; `derive_dasha_consensus` requires the id |
| F16 | RESOLVED | §2.2 "172 lines", `:156` raise; §5 preserved kernel |
| F17 | RESOLVED | `:367-380` in §0, §2.3, §3 |
| F18 | RESOLVED | §4.6 cites `l0_dasha_systems.py:107,130,164,194` — re-read |
| F19 | RESOLVED | `A01–A04` removed (grep: none); §12 says "expanded" (N14) |
| F20 | RESOLVED | §2.3 quotes `dasha_windows: [], count: 0, is_error: false` — matches `:385-395` |
| F21 | RESOLVED | the `availability['dasha']` claim removed from §2.3 (grep: none outside §12); §12 wording inaccurate (N14) |
| F22 | RESOLVED | §4.6 B3 position + §7 DEMANDS; `uuid4` at `:1065` re-read; tuple vocabulary vs SC-3 (N9) |
| F23 | RESOLVED | §5 "no feature flag exists or is proposed"; rollback = re-point the wrapper |
| F24 | RESOLVED | §1 dossier row `:285, :376` — re-read |
| F25 | RESOLVED | `service_probes.py:871-899` moved to `must_not_touch` with D-CND-34/#2071 |

**Tally:** 23 RESOLVED · 2 PARTIAL (F4, F9) · 0 UNRESOLVED. New in v1.1: 3 MAJOR (N1–N3), 8 MINOR (N4–N11), 7 NOTE (N12–N18).

---
version: 1.0
status: CURRENT
lane: TI-served-tier-legs
branch: suvarna/land/TI-served-tier-legs-001
basis: origin/main 936c4cd0c; predicted tiers read from suvarna/land/TI-l1-tier-honesty-001 (#2941 head 18313b4f5) evidence/tiers_evidence_v1_0.json and tiers.json (#2854 head e19d62453 supplies verification_tiers.py)
changelog:
  - 1.0 — first sweep of every served/planning read of two_pass_verified / verification_pass_status in platform/src, platform-mcp/src, python-sidecar readers, and DB-side integrity contracts.
---

# Served tier readers sweep (S-L1 tier honesty)

Rebuilt canonical-chart (482012f1) tiers after the S-L1 rebuild: special_lagna `single`;
sensitive_point_yogi `classical_match`; l1_tajik_varsha_year_lords (Vārṣaphala) `classical_match`;
shadbala examined (sthana/dig/kala/cheshta/drik/total, 210) `classical_match`; ashtakavarga raw bindu
(960) `classical_match`; per-varga ashtakavarga (7,800) `documented_approximation`; saham_position
`single`; naisargika/required_rupa (14) `single`; sade_sati cycle/phase six examined keys
`classical_match`; graha_nakshatra_join / graha_pada_join `classical_match`; esoteric/derived sensitive
families `single`; YAMAGANDA_SPHUTA `computed_extension`; NULL-valued lal_kitab/maharsi rows `floored`;
`single_pass` -> `single` (or `classical_match` / `documented_approximation` where the table says so);
mudda (240) and narayana (105) level-1 chart_dashas -> `classical_match`; vimshottari chart_dashas
unchanged `two_pass_verified`. Canonical totals after: two_pass_verified 265, classical_match 1,650,
documented_approximation 7,800, computed_extension 35, floored 85, single 10,335.

"Refuse/empty" = the reader returns an error, `source_incomplete`, or zero rows where it returns data today.
"Degrades" = still serves every row, the tier-derived number/label honestly drops.

| # | Reader (file:line, origin/main) | What it does with the tier | What a user of 482012f1 sees after S-L1 | Disposition |
|---|---|---|---|---|
| 1 | `platform/src/lib/retrieval/registry/layers/reading_checklist.ts:797` `fetchWealthSpecialLagnas` | Required `== two_pass_verified` on all 21 atoms, else `source_incomplete` | Was: unit `special_lagnas` `source_incomplete`, count 0 (rows are `single`). | FIXED NOW (this PR): any computed-value tier served; row carries tier; `verified_count` split from `count` |
| 2 | `reading_checklist.ts:854` `fetchWealthYogiAvayogi` | Same, 12 atoms | Was: `yogi_avayogi` `source_incomplete`, count 0 (rows `classical_match`). | FIXED NOW |
| 3 | `reading_checklist.ts:911` `fetchWealthTajaka` | Same, one annual row | Was: `tajaka` `source_incomplete`, count 0 (rows `classical_match`). | FIXED NOW |
| 4 | `reading_checklist.ts` `fetchWealthAshtakavarga` (~735) | No tier predicate (presence + natural key only) | Serves unchanged (per-varga rows `documented_approximation`); rows do not expose their tier to the checklist unit | none (no refusal); tier-carriage for this leg is wave 2 |
| 5 | `register_d9_judgment.ts:1702` Indu Lagna detail text | Response text asserting "computed + two_pass_verified" (branch is unreachable for `wealth`, the only member of DOMAIN_INDU_LAGNA, but would read false) | Text now tier-neutral | FIXED NOW (no snapshot/baseline moved; see PR) |
| 6 | `platform/src/lib/retrieval/registry/layers/L1_ganita/get_sensitive_degrees.ts:128` | `unverified_rows_in_page` = rows with tier != two_pass_verified; note names "(single/pending_w3_verification)" | 60 yogi rows move to the unverified count with `classical_match`; page still carries `tier_breakdown` per row; count is correct, note text omits classical_match | wave 2 (wording of `unverified_note`; counts stay correct) |
| 7 | `platform/src/lib/retrieval/envelope.ts:1818` `extractGroundingFromFactRows` (-> `grounding_score`) and `deriveEpistemicGrade` (:169) | `grounding_score` = share of rows at `isVerifiedPassStatus`; grade bands >=0.95 `ganita_fact`, >=0.5 `verified_signal`, else `single_pass_signal` | Every L1 page for re-tiered categories (special_lagna, sensitive_point_yogi, saham, shadbala examined, ashtakavarga, sade_sati, nakshatra join, ...) drops to score ~0 and grade `single_pass_signal`. Degrades; nothing refuses. Grade name `single_pass_signal` also covers `classical_match`/`documented_approximation` rows | wave 2 (grade vocabulary/wording; do together with row 8) |
| 8 | `platform-mcp/src/tools/register_p1_ganita.ts:727, :1114` | Prints `verified_fraction` + a note keyed to `VERIFIED_PASS_STATUSES` | Same degrade as row 7 (honest: only `two_pass_verified` counts) | wave 2 (wording) |
| 9 | `platform-mcp/src/tools/registry_bridge.ts:2664` `get_signals` | `grounding_score` = signals with tier `two_pass_verified` OR legacy `pass` (a prohibited spelling; own copy of the predicate, not `isVerifiedPassStatus`) | Reads `bodha_msr_signals` tiers (L2, inherited at L2 rebuild). Unchanged until S-L2 rebuild, then falls with the inherited tiers. No refusal | wave 2 (use `isVerifiedPassStatus`; drop `pass`) |
| 10 | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_mechanisms.ts:234` | Descriptor `serves:` string says special_lagna is "two_pass_verified" | Capability description text wrong after rebuild (descriptor text feeds `capability_knowledge.snapshot.json`; editing it moves the snapshot) | wave 2 (SS + Purna: regenerate snapshot with the text) |
| 11 | `L2_bodha/query_quality_scorecard.ts:82` | Passes stored `two_pass_verified_pct` through | L2-stored; recomputed by `bo_pramana_mapa` on S-L2 rebuild (falls) | none now; rides S-L2 |
| 12 | `platform/src/lib/retrieval/registry/knowledge/source_query_availability.ts` (43 SELECT lists), `grounding/resolver.ts:90,232`, `ganita/facts_store.ts:445`, `L1_ganita/get_*` (positions, strength, dashas, sade_sati, tajik, ...), `kala_views/now.ts:655`, `L2_bodha/query_*`, `L3_kala/query_tithi_pravesha.ts:89`, `register_d7_channel.ts:1243`, `ranking/composite_ranker.ts:84` | Select / pass the stored tier through, no filter, count, rank or wording | Rows served with their new tier visible | none |
| 13 | `platform/python-sidecar/mv_chart_sensitive_points_summary` (live definition contains `verification_pass_status`) | Materialized view carries a min-tier column | No served/planning reader exists (git grep of src, platform-mcp, python-sidecar: only the writer's REFRESH) | none |
| 14 | `bodha_writers/formulas.py:535` `VERIFICATION_RESCALE`; `bo_laksana.py:2059,2209` | L2 salience weight keyed on the inherited L1 tier (1.00 / 0.90 classical_match / 0.85 single / 0.75 computed_extension / 0.60 documented_approximation); `floored` leaves ranking | Salience of signals built on re-tiered facts falls on the next L2 rebuild; 85 floored NULL-valued rows drop out of ranking. No refusal (every new tier is a covered vocabulary member; unknown tiers raise) | none now; rides S-L2 |
| 15 | `pipeline/orchestrator/writers/bo_pramana_mapa.py:431-470` tier-inversion detector, `:691` | Counts signals claiming a stronger tier than any cited L1 fact | Until S-L2 rebuild, existing signals (stored `two_pass_verified`) cite facts now `single`/`classical_match`: divergent-signal count goes non-zero (L2 build-side quality metric, not a served surface) | wave 2 / S-L2 (rebuild L2 together with S-L1, or expect a non-zero divergence count) |
| 16 | **`platform/migrations/743_nirmana_l1_ga_sensitive_integrity_contract.sql:42`** (live `asset_registry.integrity_check_sql` for `ga_sensitive`) | Violation if any row in 18 sensitive categories has tier NOT IN (`two_pass_verified`,`floored`) | After the rebuild every `single` / `computed_extension` row in `special_lagna`, `saham_position`, `midpoint`, `arudha_pada`, esoteric_*, tajik_*, ... violates the contract: the ga_sensitive integrity check goes RED | **MUST FIX BEFORE S-L1 DEPLOY, OUTSIDE THIS PR** (needs a new migration; this PR may not touch /migrations/) |
| 17 | `742_nirmana_l1_ga_nakshatra_integrity_contract.sql:53` (b) | Verified/divergent allowed only on 4 (category,key) pairs | graha_nakshatra_join / pada_join move to `classical_match`: still legal (only the IN-list tiers are policed) | none |
| 18 | `754_..._sade_sati_integrity_contract_final.sql:291` (o); `810-819,840,841,904` structural contracts | `sade_sati_concurrent_dasha_overlay` must be `single`; NULL value <=> `floored` | Unchanged by the lane | none |
| 19 | `services/gochara_grammar/dasha_data.py:73,211` and `scripts/kala_gochara_cutover/step06a_class_context.py:285` | Multi-level dasha read pinned to tier `two_pass_verified` for every system in DASHA_SYSTEMS, incl. mudda and narayana | mudda (240) and narayana (105) level-1 rows are `classical_match` after rebuild: a pinned read of those two systems comes back empty. Vimshottari (the §4.0 contract) unchanged. `permission_curve` router uses `fetch_dasha_periods`, which has no tier filter (unaffected). Kala-layer, not touched here | wave 2 (Kala/SAD-DARSANA owner: decide mudda/narayana read tier) |
| 20 | `services/ka_tithi_pravesha/writer.py:209`, `brahmagyan/l0_kp_sublord_division.py`, `ga_nakshatra.py:112,204` | Own emission / derivation of tier | Not in the tier-honesty lane; unchanged | none |
| 21 | `ph_*`, `mi_*`, other `ka_*` writers; `platform/src/app`, `components`, `lib/ai`, `lib/vidhi` | Grepped: no read of the tier (`mi_darshana.py:594` passes it through; vidhi/registry_data.ts hits are comments) | no change | none |

Anything that would REFUSE or go EMPTY on the served path after the rebuild: rows 1-3 only (fixed here).
Build-side refusal that this PR cannot fix: row 16 (migration). Empty only for non-served Kala scripts: row 19.

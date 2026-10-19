---
artifact: FINAL_BUILD_SCOPE_V1_2_FINDINGS_RESPONSE
version: "1.0"
status: RESPONSE (Stream B; companion of FINAL_BUILD_SCOPE v1.2)
date: 2026-10-06
answers: reviews/FABLE_REVIEW_FINAL_BUILD_SCOPE_v1_1.md (verdict NOT_READY)
---

# Response to the FINAL_BUILD_SCOPE v1.1 review — every finding, by number

**How to read.** The review's numbering is kept (section.item; P-level in the review). Disposition: **ACCEPTED** = the finding is right and the named clause of v1.2 changes or adds; **ACCEPTED, OWNER** = right, and the answer is not mine to give (listed as an OPEN OWNER DECISION in v1.2 §12b, nothing settled); **REJECTED** = with the reason and evidence. Claims were re-checked on origin/main `091362f31` before accepting; the ones I could not verify (no database, no production) are marked NOT VERIFIED. Nothing in this response decides an owner point.

**Verification done for this response (read-only, origin/main 091362f31).** `life_events` extra columns (`457_lel_schema_v2_event_shapes.sql`: `shape`, `date_confidence`, `interval_start/end`, `chain_parent_event_id`, `date_tightened_at`) and its being global, not chart-scoped (`958_...sql:75`): CONFIRMED. `rule_registry._PATH_ROLES["P4"] = ("signature_house","lord")` (`:149`): CONFIRMED. The factor table's discipline (range ⊆ [0,1], `null_state NOT NULL`, `calibration_status`): CONFIRMED (`1154:40-50, 306-324`). `ka_gochara_brief_state_digest` hashes every row of `ka_gochara_relationship_record` as `to_jsonb(x) - 'created_at'` (`1240:655-675`): CONFIRMED (so a new column changes every row's bytes). `ka_gochara_candidate_gate_violations` (`1240:632`) wraps `ka_gochara_search_completeness_violations` (`:636`): CONFIRMED. `_SUPERSEDED` covers p2-p5 `1.0.0 → 1.1.0` and is tested by equality with the chosen version (`inventory_verifier.py:386,434`): CONFIRMED. `kgrr_relative_frame_ck` (`1155:527-528`): CONFIRMED. `_C_BUILD = 75524b3e…` (`inventory_verifier.py:670`) vs the design specs naming `1f89fd4c…`: CONFIRMED as a documentary disagreement; which is live is NOT VERIFIED. The ledger and verification job refuse a `test_slice` stamp (`ledger.py` `_refuse_test_slice`, `verification_job.py:178-183`): CONFIRMED. Absence of a non-test reader of `ka_gochara_eval_window`: the steward's own spot check, not repeated.

## 1. Completeness

| # | finding | disposition | v1.2 clause / reason |
|---|---|---|---|
| 1.1 (P1) | the final build's result policy is never stated | ACCEPTED, OWNER | FB-53 states both alternatives with their gate lists; decision OD-1 |
| 1.2 (P1) | "served" has no mechanism | ACCEPTED, OWNER | FB-54 (preconditions (a)-(e) with an acceptance query); the design itself is the serving workstream's; decision OD-2 |
| 1.3 (P1) | horizon coupled to a log that will change; START edge; interval/chain date; LEL basis pin; verifier rule on drift | ACCEPTED | FB-1 (exact rule), FB-2 (basis pin, drift rule: pinned basis is the authority, live log drift is SOFT), FB-3 (both edges, birth, future), FB-55. The review's open question "does `life_events` have a per-chart key": it does NOT (`958_...:75`), so "for any chart" is not implemented: stated in FB-1 |
| 1.4 (P1) | unresolved stretches have no disposition | ACCEPTED, partly OWNER | FB-56: structured sink recording UNRESOLVED with reason in the measuring build; default = the final seal refuses; accepting a disclosed residual is OD-5 |
| 1.5 (P1) | no generation-bump mechanism | ACCEPTED | FB-57 (label from `ctx.config`, validated, pinned in the manifest; sealed labels frozen). NOT VERIFIED that the frozen orchestrator hands `ctx.config` through: Stream A verifies first; if not, the clause stops and goes to the native |
| 1.6 (P2) | timeouts and run length | ACCEPTED | FB-58; §13 must-be-true list item 4 |
| 1.7 (P2) | removal / replacement of a failed FINAL candidate | ACCEPTED | FB-59 (teardown and replace-prelude include the 1308 tables, unsealed only) |
| 1.8 (P2) | "tested" before the switch: owner-facing acceptance, the extractor | ACCEPTED | FB-60; the extractor and its clip are named in FB-5 |
| 1.9 (P2) | rollback, legacy data, 1984-1998 | ACCEPTED, OWNER | FB-54 (c)(d); OD-2 |
| 1.10 (P2) | G1 / G2 / G3 absent | ACCEPTED | FB-61 (named dependencies, none in this scope) |
| 1.11 (P2) | P4 has no `karaka` role; `karaka_agent` factor needs a [0,1] value and a null state | ACCEPTED | FB-22 (P4 role is a code change), FB-36 (factor row: range 0..1, `category_mapping {karaka:1.0, non_karaka:0.0}`, `null_state omit`, `uncalibrated_default`); FB-62 pointer |
| 1.12 (P2) | P2 exclusion mechanism for `parental_event` | ACCEPTED | FB-39 (no P2 edges + inventory exclusion with the ruling reference; `kgrr_relative_frame_ck` enforces it a second time); Stream A verifies the exact 1206 disposition value |
| 1.13 (P2) | version coexistence under 1.2.0; `_SUPERSEDED` rewrite | ACCEPTED | FB-32 (supersession CHAIN, every earlier version superseded), FB-33 oracle that fails with the v1.1 table; FB-64 pointer |
| 1.14 (P3) | mother row "state unsupported" is not an existing disposition; no resolver named | ACCEPTED | FB-39: the resolver refuses by name `unsupported_person`; mother rows registered, never `included` |
| 1.15 (P3) | class census only; a P2-only class passes | ACCEPTED | FB-18 PATH CENSUS (`path_census_mismatch`); FB-65 pointer |
| 1.16 (P3) | §0.1 omits ERRATA item 7 | ACCEPTED | §0.1 now carries it |

## 2. Contradictions

| # | finding | disposition | v1.2 clause / reason |
|---|---|---|---|
| 2.1 (P1) | FB-20 vs FB-28: which function 1308 stacks | ACCEPTED | FB-20 is now a per-FUNCTION table: completeness (1232 → 1305 → 1306), Moon domain (1232 → 1305), candidate gate (1240 → 1308), state digest (1240 → 1308); FB-28 corrected |
| 2.2 (P2) | `occurrence_kind` changes the state digest bytes | ACCEPTED, by WITHDRAWAL | FB-26 withdrawn (no change to the relationship-record table); oracle that the state digest is equal before and after 1308 with the layer absent; a future promotion carries its own migration |
| 2.3 (P2) | 1307: mechanism and class disagree | ACCEPTED | FB-19 resolved at writing time, not left to measurement: mechanism = the CHECK plus the vector-freeze trigger of the draft's follow-up (d); class = PROTECTED because the trigger's function is a CREATE FUNCTION in schema public; the migration (`1307_gochara_publication_refuses_test_slice.sql`, branch `pravaha/b13-publication-check`) is written and tested against a real chain |
| 2.4 (P2) | FB-1 vs Ruling 7 verbatim | ACCEPTED, OWNER | FB-1 labels the general rule K3 with the three narrowings; OD-3 |
| 2.5 (P2) | FB-29 / ND-P2 rule 2 vs "Is not": showing near-misses is a serving commitment | ACCEPTED | §0 "Is not" rewritten; FB-29 and FB-54(e) separate the showing from the storing |
| 2.6 (P3) | FB-37 / FB-34 cite `admission.infl`, which the stored path never calls | ACCEPTED | FB-34 re-worded to the stored mechanism (`window_store.py:203-210`, `record_store._p4_double_transit`); FB-37 inherits it |
| 2.7 (P3) | daśā build id: documents vs code | ACCEPTED | FB-9 names both ids and the rule (the code constant judges a build); the live value is NOT VERIFIED here and is a read-only query for the steward before the final build |

## 3. Order and dependencies

| # | finding | disposition | v1.2 clause / reason |
|---|---|---|---|
| 3.1 (P1) | density decisions are taken on the wrong generation | ACCEPTED, partly OWNER | FB-66 (an unsealed FINAL-RULES CANDIDATE before the seal); FB-41 / FB-48 say which build informs which decision; skipping it is the owner's explicit acceptance, OD-4 |
| 3.2 (P2) | near-miss identity: builder and verifier can disagree by construction | ACCEPTED | FB-67 (`declared_accuracy` pinned in the manifest, read by both; a one-side-resolved stretch is `near_miss_accuracy_disagreement`, a seal refusal); FB-24 |
| 3.3 (P2) | Suvarna's deterministic-id `ga_dashas` rebuild | ACCEPTED | FB-9 and §14 step 5 (the `_C_BUILD` re-pin moves the implementation digest and belongs to the final build's list) |
| 3.4 (P3) | `one_class_full` timing cannot be scaled | ACCEPTED | stated in FB-58 and §13: the measuring build supplies the figures |
| 3.5 (P3) | lock "once at the final head" vs per-PR regeneration | ACCEPTED | §11.3 clarified: regenerated at every governed change as CI requires; "once" names the sealing value |
| 3.6 (P3) | `pg_get_functiondef` is server-version-formatted | ACCEPTED | FB-20 / §11.4: same MAJOR version as production, recorded in the test and each readback |

## 4. Untestable or vague clauses

| # | finding | disposition | v1.2 clause / reason |
|---|---|---|---|
| 4.1 (P2) | FB-29's proof is true by construction | ACCEPTED | FB-29 negative control (inject into a support union, the P4 input, the candidate count, coverage accounting; the check must FAIL); the verifier-side comparison already exists as `near_miss_verifier.noninterference_problems` (PR 3187), the injection test is Stream A's |
| 4.2 (P2) | FB-14's guard has no allowlist | ACCEPTED | FB-14 names the two reading paths (capture trigger; drift report), asserts both DO read, and a positive count for every guarded path P1-P4 |
| 4.3 (P2) | FB-41 has no oracle or generation mechanism | ACCEPTED | FB-41 (oracle on the final-rules candidate; mechanism FB-57; scored-horizon share; P4-alone = P4's own union) |
| 4.4 (P2) | which horizon gates the budget | ACCEPTED | FB-48 / FB-50: the SCORED-horizon share gates (protocol §6.4, lines 199-205); the build-horizon share is informational |
| 4.5 (P2) | FB-24 "declared accuracy" has no number or oracle | ACCEPTED | FB-67 (solver tolerance, classification step, `GRAZE_MIN_APPROACH_DEG`, `max_extension_days`, speed table identifier; changing any changes the manifest identity) |
| 4.6 (P2) | FB-3's oracle tests only the END edge | ACCEPTED | FB-3 oracle covers start-before-1998, start-before-birth, end after 2085, the edges themselves |
| 4.7 (P2) | FB-5's oracle runs on a candidate the scorer may not read | ACCEPTED | FB-5: Stream A verifies the extractor reads an unsealed `test_slice` candidate before the measuring build; otherwise the oracle moves to the final-rules candidate |
| 4.8 (P2) | §11.2 regression golden needs a full pre-scope build that is torn down | ACCEPTED | FB-69: captured from the measuring build before its teardown; teardown gated on the capture |
| 4.9 (P3) | FB-27's junction field has no verifier duty | ACCEPTED | FB-29 verifier bullet; delivered as `near_miss_verifier.compare_sets` (stored junction recomputed and compared, PR 3187) |
| 4.10 (P3) | FB-38's third term is not independent | ACCEPTED | FB-70: machine-readable fixture with its own sha256 (`decisions/fixtures/FB35_TABLE_v1_2.json`, `acfa58c7…`) generated by a script importing no code; the equality test reads the file |
| 4.11 (P3) | FB-16 "unambiguous" undefined; FB-52 refuses missing but not stale | ACCEPTED | FB-16 defines correspondence (one-to-one on natural key, ordinal path and lord path); FB-52 binds a `report_digest` and refuses `report_stale` |

## 5. Risk ranking — how v1.2 settles each

| risk | v1.2 |
|---|---|
| 1. the switch is unreachable from the document | FB-53, FB-54 and OD-1, OD-2 make the missing decisions explicit and give the serving preconditions an acceptance query; the document does not claim to reach the switch |
| 2. horizon coupled to a changing log | FB-1, FB-2, FB-3, FB-55 (exact predicate, basis pin, soft `lel_drift`, both-edge refusals, the tightening test) |
| 3. unresolved stretches block the seal with no fallback | FB-56, FB-67, OD-5 |
| 4. density decisions on a non-representative build | FB-66, OD-4 |
| 5. migration-chain acceptance mis-specified | FB-19, FB-20, FB-21, FB-26 (withdrawn), FB-28; §11.2 and §11.4 rewritten |
| runner-up: run length vs a cap that does not cancel the writer | FB-58 |

## 6. Owner decisions the review found settled implicitly — listed, not settled

| review item | OD |
|---|---|
| 6.1 the general horizon rule and its refusal for anyone born after 1985-01-01 or with a first event before 1998 | OD-3 (and OD-11 for the log tightening) |
| 6.2 numbers on or off | OD-1 |
| 6.3 "served, not scored" for 2026-2084 | OD-3 |
| 6.4 near-miss semantics beyond the owner's words; `proximity` as a served number | OD-9 |
| 6.5 karakatva reaches every class with a kāraka | OD-6 |
| 6.6 K-B on bereavement | OD-7 |
| 6.7 DVI reversion deferred to the next generation | OD-4 |
| 6.8 1984-1998 behaviour | OD-2 |
| 6.9 mother-tagged parental events fail to resolve | OD-8 |
| 6.10 which junction kinds count as sandhi | OD-9 |
| 6.11 1 January vs 16 February 1998 | OD-3 |

## The review's two closing lists

**Must fix before the measuring build.** All six are carried in FINAL_BUILD_SCOPE v1.2 §13 ("Must also be true BEFORE it runs", items 1-7): the START refusal and the "fully dated" detector (FB-1/FB-3); the LEL basis pin (FB-2); the sink extended to UNRESOLVED (FB-56); the golden captured before teardown (FB-69); the cap and fired-cap procedure (FB-58); whether the scorer can read a `test_slice` candidate (FB-5); 1307's mechanism and class (FB-19).
**Must fix before the final build.** The owner decision on the result policy (FB-53, OD-1); the serving path as clauses (FB-54, OD-2); the migration chain (FB-19/20/21/26/28); the unresolved-stretch disposition and declared accuracy (FB-56, FB-67); the generation label (FB-57); P4 `karaka`, the factor row, P2 exclusion, supersession chain (FB-22/36/39/32); replacement of a failed FINAL candidate (FB-59); the negative control and the specification-side fixture (FB-29, FB-70); the final-rules candidate or the owner's acceptance (FB-66, OD-4); owner sign-off on the §6 items (§12b).

## Not read or not verifiable here (carried from the review, plus mine)

No database or production access: live row counts, which `life_events` row is first in production, the live pinned daśā build id, whether 1236 is applied, the live PostgreSQL major version (FB-20 needs it). The Stream A in-flight branches and the near-miss storage branch were not read. The serving design brief (`V5_SERVING_PATH_DESIGN_BRIEF_v0_1_FABLE.md`) was not read for this response.

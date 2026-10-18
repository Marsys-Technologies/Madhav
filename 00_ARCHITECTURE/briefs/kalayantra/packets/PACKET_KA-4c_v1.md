```json
{"id":"KA-4c","kind":"feature","wave":null,"build_tier":"sonnet","routing_reason":"Ruled evaluator.","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"8482540d666f8ea930bf9e62214cf9002b25adec","section_range":"\u00a75 base contract; \u00a78; \u00a79","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],"schema_receipt_id":null,"pw_mechanism_version":null,"release_pins":{"dash_build":null,"registry_revision":null},"packet_sha256":"a2dbbee9efc60cde3dfd5f76e5973670f373802f5d68db0d4ddad67a77d10333","original_failing_base":null,"test_commits":[],"expected_failing_assertion":null}
```
# KA-4c v1 · DRAFT
v1.1 DRAFT; changelog: 20261016.
## 1. Pins / prerequisites
Prefixes: Y=platform/python-sidecar; F=00_ARCHITECTURE/briefs/kalayantra/fleet; S=00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS; U=S/SURROGATE_ANSWERS_01-02.md; O=S/OWNER_RULINGS_DIGEST_A.md; B=S/B4_RULINGS.md.
P=spec_sources path; short basenames resolve to listed reads. Definition U:21,23; O:60,62. Mirror/pin rulings (B:21; notes).
Prerequisite facts: KA-4 accepted head/squash in base (U:21; P:330-337); F/FROZEN_PATHS.txt; pins/tests/slot/template (B:15-16). Parallel fixtures allowed; real acceptance needs L0-M grammar/rows/receipt, not only 1332 (U:15,25; P:538-540).
Read Owns and Y/services/ka_muhurta_seva/service.py:38-61; Y/services/kala_core/sky/ephemeris.py:88-111,171-201,236-309; Y/services/kala_core/sky/coverage.py:42-100; Y/brahmagyan/dignity_oracle.py:92-148; Y/brahmagyan/l0_formula_constants.py:28-44; Y/ga_writers/ga_vargas_writer.py:475-513; Y/ga_writers/ga_condition_writer.py:64-69,183-276,350-419; Y/routers/transit_search.py:25-55; Y/main.py:29-34,90-93; Y/routers/yoga_formation_band.py:610-624; platform/supabase/migrations/544_bg_parihara_rules.sql:63-80; platform/migrations/1332_l0_muhurta_parihara_scope_prepare.sql:13-24. Caller: platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:126-152; reference Y/pipeline/orchestrator/writers/bg_muhurta_lattice.py:72-74.
## 2. Owns
Owns (Y-relative): services/ka_muhurta_seva/parihara_eval.py; routers/parihara_evaluate.py; main.py (import/one guarded include); tests/l3/ka_muhurta_seva/test_parihara_eval.py; tests/l3/ka_muhurta_seva/test_parihara_evaluate.py; tests/l3/kala_db/ka_muhurta_seva/test_parihara_db.py; tests/l3/ka_muhurta_seva/parihara_predicates.json. U:21 allocations; shared L0-M grammar fixtures. No generators/exports; KA-4b consumer.
## 3. Excerpt
P:538, pin above:
```excerpt
4. **Signatures / contract** — real columns from the admitted schema receipt;
```
Reconciliation: `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md` requires L0-M receipt; 1332 lacks grammar; U:21 allows parallel fixtures.
## 4. Contract (U:21,23; O:60)
POST /api/compute/parihara_evaluate; mount verify_api_key like main.py:93.
Request {candidate:{start_utc,end_utc},undertaking,location:{lat,lon,tz_offset_minutes},dosas_present:[dosha_canonical_id…]}. Evaluator loads rules: marriage→marriage/general; upanayana→upanayana/general; all other undertakings→general only; never natal/muhurta fallback.
bg_parihara_rules (544:63-80): id bigint/key(dosha_canonical_id,cancellation_index); scope/source_citation/net_standing text. U:25 adds predicate jsonb, conjunction_reading text mula|tika, tika_extension boolean, priority_rank/source_chunk_id text; never_cancelled/tika_commentary enums. Read-only parameterized SELECT (yoga_formation_band.py:610-624); DB/schema errors refuse.
Envelope: evaluator_version,ayanamsha="lahiri",house_system="whole_sign_from_rising_sign",location,location_basis∈{caller,lattice_reference_location},evaluated_at:{start,mid,end},sky_coverage.
Per rule: rule_id,dosha_canonical_id,scope,source_citation,source_chunk_id,result∈{applies,does_not_apply,unassessable},reason,terms:[{term,observed,facts}],conjunction_reading,tika_extension,priority_rank,net_standing.
Per doṣa: state∈{cancelled,residual,cancellation_unassessed},by_rules,reason.
U:23 grammar: {op:all_of|any_of,terms:[…]} or single term; optional clause="sarva_dosha". Terms:
{planet:P,house_from_lagna:[…]};
{planet:P,dignity:debilitated|combust|enemy_sign,varga:rasi|navamsa};
{planet:Moon,vargottama:true};
{role:lagna_lord|navamsa_lagna_lord,house_from_lagna:[…]};
{role:dosha_agents,each_any_of:[enemy_sign,debilitated,combust]};
{planet:P,strength:strong}.
P=Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn. Sarva targets only L0-M chapter rows, no wildcard.
Lahiri start/mid/end; house=1+(planet_sign−rising_sign)%12, no cusps. D9 ga_vargas_writer.py:475-513; Moon vargottama=equal signs; lords ga_condition_writer.py:64-69, houses from rāśi lagna. Debilitation classify_dignity; enemy_sign ga_condition_writer.py:232-275 (oracle lacks it). Provenance/commentary/priority unchanged, no weights.
Any scoped applies→cancelled; nonempty all does_not_apply→residual; never_cancelled row→residual/never_cancelled_by_text; otherwise cancellation_unassessed. No rule→no_sourced_rule_in_scope.
Unassessable reasons: strong→strength_undefined; agents unknown→dosha_agents_unknown (U:29); null/unsupported→predicate_not_encoded; changed term→predicate_changes_within_candidate/three values/no split; sky missing→sky_coverage_gap/no Moshier/interpolation. Missing place refused/location_missing. ELECT supplies {lat:20.27,lon:85.84,tz_offset_minutes:330}/origin (U:21).
(I) INTERPRETATION I1: arrays rules/dosas; dosas includes dosha_canonical_id; rule_id=id/by_rules=ids; evaluator_version="1"; observed=[{at,value}]; facts=values/JD/convention/backend/coverage. Optional request location_basis defaults caller; reference requires exact triple, never inferred.
(I) INTERPRETATION I2: aware ISO UTC/end>start; invalid 422; absent place detail.reason=location_missing. CivilTime.zone="UTC"+offset (ephemeris.py:249-255,299-301), no IANA/DST inference. Coverage=samples, no continuity claim.
(I) INTERPRETATION I3: U:19 L0 orbs; speed<0 retrograde, short Sun arc≤orb, Sun false. ga_condition_writer.py:374-375 differs (only Mercury/Venus retro exception), not adopted. Navamsa combust undefined→predicate_not_encoded.
(I) INTERPRETATION I4: unknown/change→whole rule unassessable; known terms all/any. Change wins, else first unknown reason. never_cancelled overrides applies; its rule is does_not_apply/never_cancelled_by_text/terms=[]. Retain terms/rules.
## 5. Metadata
brief.migration=null; brief.op=null; writes_data=false; migration_class=null; window_batch_id=null. No binding (U:21).
## 6. Acceptance
Tests first; one reversion/claim:

- Unguarded: configured synthetic key absent/wrong→401; route/transit compatibility.
- DefaultPlace: invalid time/place→422; missing location reason; explicit origin/equal-coordinate caller round-trip.
- ScopeLeak: undertaking matrix incl. education/spiritual_initiation; no natal/muhurta; zero rules exact reason.
- Flattened: all/any/single/sarva; node/unknown/null never applies.
- WrongFrame: house wrap/D9 boundary/Moon/lords/source-value goldens.
- GuessedOrb: dignity/Sun/direct/retro boundaries/359°-1°; navamsa combust unavailable/no orb copies.
- Invented: strong/agents unavailable despite favorable sky.
- MissedSample: T/F/T and T/T/F→change reason/three values/no split.
- CoverageGreen: remove backend/body/sample→gap, no green/fabricated facts.
- EmptyResidual: applies/all false/false+unknown/empty/never_cancelled/conflicting applies matrix.
- LostSource: all rule metadata/ids round-trip, never changes applicability.
- StubbedDB: L0-M scoped round-trip; DB/schema error refuses; writes rejected.
cwd Y: `python3 -B -m pytest tests/l3/ka_muhurta_seva tests/l3/kala_db/ka_muhurta_seva -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest"`
cwd repo: `KY_ITEM=KA-4c bash 00_ARCHITECTURE/briefs/kalayantra/fleet/precheck.sh --item`
TESTS=three newline-delimited test paths from Owns (P:494-495). Exit0/no skips; D-OWNER-TESTS-20261016. Accepted L0-M loopback slot; guards Y/tests/_disposable_guard.py:20-57. Foreground Python/process/loopback DB; offline unit/TestClient; no external network. Pin committed red/base/digests; already-green needs review (P:544-551). CI/Kāla DB Tests/exact-head review (P:146-151,381); route/grammar/state/sky/DB detectors.
## 7. Evidence
Frozen inspection.json (B:15; P:552-553): head/base/deps/schema/slot/tests/mutants/facts/compatibility. No readback; builder≠verifier.
## 8. PR
PR “Evaluate scoped muhūrta cancellation predicates”; body: contract/scope/consumer/tests/DB/metadata. Controller `ky review KA-4c --detail "PR #<n> @ <40-hex head>"`; cockpit writes Git.
## 9. Do not
No TS/key-match/materialisation/generation/detector/strength definition; FROZEN/control/cross-campaign/SQL/production/credentials/ledger PR/rebase/force-push. DIRTY generated→REGEN, else launcher merges authorised main (P:556-558).

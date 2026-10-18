```json
{"id":"KV3-SCHEMA-2","kind":"schema-prerequisite","wave":1,"build_tier":"opus","routing_reason":"Constraint/index replacement and generation-bound field readers; plan §9.","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"2.7","section_range":"§8; §14 Wave 1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},{"path":"platform/migrations/1341_k1_2_avadhi_candidate_dossiers.sql","revision":"1341","section_range":"1-87","sha256":"968029179cb77433e1d0c49c460335de2174f1305685fd5aeaca3aa07b07d239"},{"path":"platform/python-sidecar/services/kala_core/measure/__init__.py","revision":"c003253c0c459707465908eb7ee40f1708a6b1a0","section_range":"93-114;222-250","sha256":"8bb67e876c5af8f4c2f9fe420cf1b25a6f39a62a686e0f0e1fefd0c7839979bc"}],"schema_receipt_id":"SR-20261009T200542Z-a9d843652016","pw_mechanism_version":"1.0","release_pins":{"dash_build":"ca17639b-f3cf-42c7-9866-0a61f3855802","registry_revision":30},"packet_sha256":"1103de8a458c88a52797261b77a22e5ccef66e7d966d8bfbd0816405992f8345","intended_schema":"Four field tables: generation/partial natural keys, typed metadata as §4, snapshot-to-candidate linkage, generation-filtered reads, legacy preservation."}
```
# KV3-SCHEMA-2 v1 · READY FOR ADMISSION
Version 1.0; status: preparation; changelog: initial field partition/metadata design.
Aliases: Y=platform/python-sidecar; F=00_ARCHITECTURE/briefs/kalayantra/fleet; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3.
## 1. Pins / gates
Release SUVARNA-L0L2-CLOSE-REV30-20261013; run/revision in front matter. SR v2.2 is historical, not current/slot proof. Build requires current measured seed/slot receipt and model registration. Wave1 (plan §14); after installation; owner-approved production window. Consumers VC-1/2,K5-2/2b,K6-4,K8-REG,K9-1 wait for verified schema. Authority: S/engines/surrogate/SURROGATE_ANSWER_06_AUDIT_AND_SCHEMA2.md:43-59.
## 2. Owns
platform/migrations/<allocated>_kala_field_generation_metadata.sql; platform/scripts/kala_protected_migrations.txt (filename); Y/services/ka_kshetra/writer.py (generation scoping only); Y/services/mi_bhara/db.py (three selectors); platform-mcp/src/lib/kala_envelope.ts (snapshot select), platform-mcp/src/tools/kala_views/priority.ts (salience select); tests beside these and Y/tests/l3/kala_db/ka_kshetra/; regenerated writer inventory/capability census. Disclose any additional direct reader before editing. No measure/manifest/FROZEN/control edits. Model owns/shared, no d1_paths.
## 3. Excerpt
Pinned 1341:6-7:
```excerpt
ALTER TABLE public.kala_avadhi
    ADD COLUMN IF NOT EXISTS generation text NOT NULL DEFAULT 'legacy',
```
Reconciliation: `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md` §8: additive prerequisite; protected list, no migrate.ts/deploy.yml edits; answer06 legacy/candidate pattern.
## 4. Existing / intended contract; design
SR lists four tables without generation. DDL: platform/supabase/migrations/492_kala_field_core.sql:54-81,177-193; 494_kala_field_null.sql:76-92; 495_kala_field_salience_insights.sql:84-120. Preserve old columns/IDs/values.
All four add generation text NOT NULL DEFAULT 'legacy'. Replace each old UNIQUE with partial legacy UNIQUE on exact old key and partial candidate UNIQUE on (chart_id,generation,remaining old key), copying 1341:16-34. Remaining keys: field(event_class,segment_index); null(event_class,bucket_days,field_snapshot_id); salience(window_id); snapshots(field_snapshot_id).
Snapshots add candidate_build_id uuid nullable FK kala_layer_candidate(build_id); nonlegacy snapshot must match candidate chart/generation/build. Each nonlegacy field/null/salience row resolves SAME chart/generation/field_snapshot_id snapshot. Keep field_snapshot_id; legacy new metadata stays NULL.
Exact NEW nullable columns, NO defaults:
- snapshots: as_of date; time_origin_utc timestamptz; time_axis text; time_unit text; metadata_null_reason text.
- field: units text; risk_set_ref text; suppression_mask_digest text; metadata_null_reason text.
- null: estimand text; conditioning text; preparation_digest text; observed double precision; null_statistics double precision[]; effect double precision; standardized_effect double precision; p_value double precision; denominator integer; verdict text; reason text; surrogate_diagnostic boolean; units text; risk_set_ref text; suppression_mask_digest text; metadata_null_reason text.
- salience: generation only; existing snapshot supplies context.
Types derive from pinned measure/__init__.py:93-114. CHECK nonnull verdict in pass/fail/insufficient_evidence/not_evaluable (:28-32); denominator positive; digests 64 lowercase hex; evaluable scalar results finite; p_value [0,1]. Preserve array order. Diagnostic≠inferential pass (:222-239). Nonlegacy absent metadata requires metadata_null_reason, or NullResult.reason; never default.
Persistence: Y/services/ka_kshetra/writer.py:833-850,879-901 writes/reads legacy DHARA NullResult, not shared Experiment. /Users/Dev/kalayantra/wt/k2/platform/python-sidecar/services/ka_sangam/jury/candidate.py:232-242,268-279 stores shared NullResult + estimand/conditioning as conditional_null/pipeline_null. Flatten TYPE fields; no jury→field values. Y/tests/l3/kala_core/measure/test_measure.py:79-87 distinguishes three experiments. Keep old null_max_stats/replicates distinct from NEW null_statistics/denominator.
(I) INTERPRETATION S2-I1: authorized placement design above: snapshot time pins, per-class/segment units/risk/suppression, per-null experiment/result. G1a supplies actual risk/eligibility/metadata; no invention here.
(I) INTERPRETATION S2-I2: as_of is explicit date; origin is actual zero instant; axis/unit describe producer convention; pin identical candidate.conventions values, refuse contradictions. No guessed noon-J2000/birth conversion. Legacy 492:59 uses days since birth; hazard.py:6-10 uses events/day; neither defaults candidate metadata.
(I) INTERPRETATION S2-I3: permit existing q_threshold NULL for nonlegacy only with reason, retaining its old legacy NOT NULL invariant as a generation-conditional CHECK. No fabricated q when unavailable. Other old constraints retained.
Registry: re-scope retained ka_kshetra integrity predicate to legacy-only CTE, append candidate linkage/metadata invariants idempotently like 1341:36-85. count_sql uses published head, COALESCE(head,'legacy'). NULL original predicate stays unavailable; no invented true.
Reads resolve served head or candidate_generation(ctx) (manifest/__init__.py:76-88); filter every changed-table read; carry generation in served responses, never latest candidate. Writer :2439-2450 chart-wide deletes must protect legacy/published/retained rows and replace only bound unpublished candidate grain. Unbound build preserves output. ctx.db_conn only; no commit/close/throughput write. No publication here.
## 5. Metadata
brief.migration=additive; brief.op=null; writes_data=true; migration_class=NEEDS-PROTECTED-WINDOW; window_batch_id=null until cockpit binds approved batch. Allocate at build start; list same PR; no GRANT.
## 6. Acceptance
Owned SQL tests first, qualified disposable PostgreSQL. Before/after old catalogue and EVERY old value/ID: unchanged legacy rows/readers; columns absent/present; two candidates same key allowed; within-partition duplicates fail; wrong chart/generation/snapshot/build fails; repeat migration/replacement identical; candidate isolated; published/retained deletion refused; NULL/reason roundtrip; distinct experiments retained; diagnostic/pass and invalid enum/digest/denominator/nonfinite/p/origin rejected. Exercise all four tables and real Python/MCP selectors; filter-removal/preservation mutants fail. Legacy explicit-column inserts keep default generation on disposable fixture only.
cwd Y: KALA_REQUIRE_DB=1 python3 -B -m pytest tests/l3/kala_db/ka_kshetra -q -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest"
Repo: KY_ITEM=KV3-SCHEMA-2 bash "$KY_FLEET/precheck.sh" --item
No skips; CI/Kāla DB Tests, independent head review. No invented red history.
## 7. Evidence
inspection.json: item/job/author/head; schema/slot/source hashes; migration hash; old rows/catalogue/readers; commands/negatives; linkage/metadata; interpretations. Use installed readback fields for ledger/catalogue/old-row/registry proof; independent squash verdict; never self-accept.
## 8. PR
[PROTECTED-WINDOW] Partition field generations and persist typed metadata. Body: design/owns/tests/preservation/window/readback/interpretations. ky review KV3-SCHEMA-2 --detail "PR #<n> @ <40-hex head>". Answer05:75 tests_and_verdict for steps, no bespoke detector.
## 9. Do not
No publication/legacy mutation/score build/invented eligibility/table-wide delete/GRANT/credentials/production/control edits/rebase/force-push. DIRTY→authorized launcher (generated→REGEN); cockpit writes Git.

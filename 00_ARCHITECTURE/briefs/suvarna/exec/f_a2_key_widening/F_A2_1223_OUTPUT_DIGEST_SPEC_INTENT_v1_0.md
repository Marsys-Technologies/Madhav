---
artifact: F_A2_1223_OUTPUT_DIGEST_SPEC_INTENT
version: "1.0"
status: INTENT_ONLY_NO_MIGRATION_FILE
date: 2026-10-02
lane: suvarna/land/TI-l1-fa2-key-001
migration_number: "1223 (allocated by SS for this revision; NO migration file exists or may be created until the owner's typed authorisation reaches the coordinator's session)"
execution: NONE. Read-only catalog and data reads as `suvarna_reader`; the new spec's SHA was computed offline with the repository's own `canonical_digest`. Nothing was applied.
changelog:
  - "1.0 (2026-10-02): first version (SS ruling on the #2858 review, item 5)."
---

# 1223 (intent): revise the `ga_vargas` output-digest spec to the seven-column key

## Why

`asset_output_digest_specs` holds one reviewed spec per asset. The live current row for `ga_vargas` (read 2026-10-02) was authored by migration 883:

| field | live value |
|---|---|
| `asset_id` | `ga_vargas` |
| `spec_sha256` | `5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51` (reproduced exactly by `canonical_digest(spec)`) |
| `retired_at` | NULL (the only row for this asset; `reviewed_at` set) |
| component | one: relation `chart_divisionals`, `where_equals {chart_id: 482012f1-...}` |
| `key_columns` | `chart_id, graha, ayanamsha_id, varga, fact_category, fact_key` (six) |
| `value_columns` | 26 columns, `fact_subject` already among them |

`compute_output_digest` (`pipeline/orchestrator/output_digest.py`) streams the component's rows `ORDER BY` exactly the `key_columns` and hashes each row's JSON. After F-A2 a six-column key no longer identifies a row: rows that differ only in `fact_subject` TIE, so their relative order is whatever the planner returns, and the digest is not a function of the content (it can differ between two runs over identical data). A digest change drives staleness (receipts, downstream upstream-hash), so a non-deterministic digest means spurious stale/rebuild signals. The seven-column key makes the order total again.

## The revision

Only `key_columns` changes: `fact_subject` is appended. `value_columns` already contain it; `where_equals` and the component name are unchanged. The key preflight in `compute_output_digest` raises if any key column is NULL: **live, `fact_subject` is NULL on 0 of 71,476 `chart_divisionals` rows, and the writer emits none (0 of 38,665 rows in an offline five-ayanamsha build)**, so the new key passes the preflight. (The writer's `fact_id` is not stored in this table, so it cannot be the tiebreaker; `fact_subject` is the writer's own discriminator and the seventh column of the live unique index after F-A2.)

New spec JSON (compact, as the migration-883 / 1017 files write it) and its canonical SHA-256 computed with `pipeline.orchestrator.provenance.canonical_digest`:

```
spec_sha256 = 9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862
```

```json
{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_divisionals","relation":"chart_divisionals","key_columns":["chart_id","graha","ayanamsha_id","varga","fact_category","fact_key","fact_subject"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["chart_id","graha","ayanamsha_id","varga","fact_category","fact_key","sign","sign_number","degree_in_sign","house","vargottama","source_citation","fact_value_text","fact_value_num","fact_subject","verification_pass_status","engine_version","citation_ref","citation_human","source_calculation","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec"]}]}
```

## How retire / replace works (the pattern of migrations 1016/1017)

`asset_output_digest_specs` is `amjis_app`-owned (no owner path; no triggers). Its constraints: `PRIMARY KEY (asset_id, spec_sha256)`, a UNIQUE partial index `asset_output_digest_specs_one_current ON (asset_id) WHERE retired_at IS NULL` (at most ONE live spec per asset), `CHECK (retired_at IS NULL OR retired_at >= reviewed_at)`, `CHECK (spec_sha256 ~ '^[a-f0-9]{64}$')`, `CHECK (jsonb_typeof(spec) = 'object')`, FK to `asset_registry`. The replacement therefore retires the current row FIRST and inserts the new one second, in one transaction (the runner's), exactly like 1017:

```sql
-- 1223 (INTENT, not a file): ga_vargas output-digest spec: seven-column key (F-A2)
SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_live int;
BEGIN
  SELECT count(*) INTO v_live FROM asset_output_digest_specs
   WHERE asset_id = 'ga_vargas' AND retired_at IS NULL
     AND spec_sha256 = '5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51';
  IF v_live <> 1 THEN
    RAISE EXCEPTION '1223: the live ga_vargas digest spec is not the 883 spec (found % matching rows)', v_live;
  END IF;
END
$pre$;

UPDATE asset_output_digest_specs
   SET retired_at = now()
 WHERE asset_id = 'ga_vargas'
   AND spec_sha256 = '5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51'
   AND retired_at IS NULL;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_vargas',
  '9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862',
  '<the compact spec JSON above>'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

DO $post$
DECLARE v_live int;
BEGIN
  SELECT count(*) INTO v_live FROM asset_output_digest_specs
   WHERE asset_id = 'ga_vargas' AND retired_at IS NULL
     AND spec_sha256 = '9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862';
  IF v_live <> 1 THEN
    RAISE EXCEPTION '1223: the revised ga_vargas digest spec is not the single current row';
  END IF;
END
$post$;
```

(`reviewed_at` takes its table default on INSERT, as in 883/1017; confirm the default when the file is authored. The 883-era spec-reviewed flag semantics are unchanged.)

## Consequence: staleness, and when to apply

- The spec digest is part of the receipt (`asset_provenance_receipts.output_digest_spec_sha256`). After 1223 the current ga_vargas receipt (built under the old spec sha) no longer matches the live spec, so the monitor reports its output digest as built under a retired spec: stale until the next ga_vargas build writes a receipt under the new spec. That is expected and harmless here: S-L1 rebuilds ga_vargas anyway (the row set itself changes, so its output digest changes regardless).
- **Apply 1223 BEFORE the S-L1 ga_vargas rebuild** (with 1222 and the D6 plan, in the same launch window): then the rebuild's receipt carries the new spec and a deterministic digest. Applied after, the first receipt is computed with tied ordering (non-reproducible) and needs one more rebuild to settle.
- Dependents' `compute_upstream_hash` read the ga_vargas receipt's `output_digest`; they go stale when it changes. That cascade is the S-L1 wave order's job (L1 first), not this migration's.
- No code path gates a build on spec freshness (nothing in the run path reads `reviewed_at`/`retired_at` of a RETIRED row); the asset is `asset_frozen` (N-51) and needs no refreeze for a spec revision.
- Rollback is the mirror statement pair (retire the new row, `UPDATE ... SET retired_at = NULL` on the old: the old row's `retired_at` can be cleared only AFTER the new one is retired because of the one-current index).

## Not done here

No migration file, no application. The statement blocks above are text only; the number 1223 is allocated, not used. The file is authored only after the owner's typed authorisation reaches the coordinator's session (SS ruling).

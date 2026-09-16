# Task D1 — truthful divisional pagination report

## Status

COMPLETE — source implementation and generated internal capability binding now carry a deterministic, server-observed exhaustion signal. No database, production credentials, migration, deployment, workflow, campaign state, push, or PR action was performed.

## Schema/order evidence

`platform/migrations/883_nirmana_l1_ga_vargas_output_digest_spec.sql:9-17` documents the DB-enforced `chart_divisionals_unique_idx` as `NULLS NOT DISTINCT` on `(chart_id, graha, ayanamsha_id, varga, fact_category, fact_key)`. The handler already fixes `chart_id = $1`; its stable page order is therefore `varga, ayanamsha_id, graha, fact_category, fact_key`. This replaces the formerly non-unique three-term order.

## Delivered behavior

- `get_divisionals` requests `limit + 1` under the same parameterized chart/ayanamsha/varga/graha filters as its served page.
- It returns only the first requested `limit` rows and `content.more_available`, derived from the observed probe row. The old page-length `content.total` is removed; no false `total_matching` is claimed.
- Existing response envelope, authorization/filter binding, and `house_from_varga_lagna` calculation remain intact; the hidden probe row is never sent through that row transformation.
- The divisional SCU now marks `pagination_verified` and `result_collection_verified` true, declares `content.rows` and `content.more_available`, and records the complete documented natural ordering key.
- Regenerated estate and capability-knowledge artifacts mark the internal divisional route `exhaustible_reviewed` (2 reviewed paginated descriptors; 94 still non-exhaustible).

## Tests and checks

- RED observed: the four new handler tests all failed on the old behavior (unsliced probe/page rows, no `more_available`, and a page-length total).
- GREEN: `npm test -- src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_divisionals.test.ts src/lib/retrieval/registry/knowledge/knowledge.test.ts src/lib/vidhi/inquiry/pagination.test.ts` — 46 passed.
- `npm run codegen:capability-estate-census:check` — passed.
- `npm run codegen:capability-knowledge:check` — passed.
- `npx tsc --noEmit -p tsconfig.json` — passed.
- `git diff --check` — passed.

## Remaining boundary

The public `ganita_chart_facts_get` alias remains separately non-exhaustion-reviewed and requires a `divisional_chart` filter; it is not the internal `get_divisionals` binding and is outside D1 scope.

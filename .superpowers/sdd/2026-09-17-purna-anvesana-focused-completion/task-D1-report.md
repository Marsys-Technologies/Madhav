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

## Fix round 1/5 — server-computed continuation

### Correctness repair

The initial D1 receipt contract derived `next` from caller arguments when `content.more_available` was true. That could skip rows when the caller omitted `limit` (the handler serves its default 300 while the receipt used its contract maximum) or supplied a value above the handler's 2000 cap.

`get_divisionals` now returns `content.next_offset`: `offset + rows.length` when the server-observed probe proves more rows, otherwise explicit `null`. The reviewed binding declares `next_path: content.next_offset` rather than a `more_available_path`, so `deriveInquiryPaginationReceipt` consumes the actual server continuation and uses `null` as terminal exhaustion. `more_available` remains a truthful response field.

### Regression evidence

- RED observed: terminal-null and omitted/oversized handler-to-receipt regressions failed before the response and contract change.
- GREEN: an omitted limit serving 300 of a 301-row probe returns receipt `next: 300`; an oversized `limit: 5000` at `offset: 100` serves the 2000-row cap and returns `next: 2100`. Neither receipt is exhausted.
- Focused suite: `npm test -- src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_divisionals.test.ts src/lib/retrieval/registry/knowledge/knowledge.test.ts src/lib/vidhi/inquiry/pagination.test.ts` — 48 passed.
- Both generated-artifact checks, TypeScript check, and `git diff --check` passed after regeneration.

## Fix round 3/5 — non-finite limit regressions

No runtime change was required. Handler-to-receipt tests now cover both `NaN` and positive `Infinity`: each receives a 301-row probe, uses the existing 300-row default page size, returns 300 served rows and `next_offset: 300`, and produces the non-exhausted receipt `next: 300`.

Focused suite: `npm test -- src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_divisionals.test.ts src/lib/retrieval/registry/knowledge/knowledge.test.ts src/lib/vidhi/inquiry/pagination.test.ts` — 52 passed. TypeScript and `git diff --check` passed.

## Fix round 2/5 — positive progressing page size

### Correctness repair

`limit: 0` previously fetched a probe but served no rows, producing `next_offset` equal to the current offset. The handler now normalizes its effective page size before building the query: finite inputs are floored and clamped to `1…2000`; non-finite values use the existing 300-row default. This preserves the cap/default while ensuring any non-terminal page advances.

### Regression evidence

- RED observed: zero and negative limit handler-to-receipt regressions used a zero/negative probe parameter and failed their required progressing continuation assertions.
- GREEN: both inputs use an effective one-row page and two-row probe; zero returns `next: 1`, while `offset: 4, limit: -10` returns `next: 5`. Both receipts remain non-exhausted and make progress.
- Focused suite: `npm test -- src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_divisionals.test.ts src/lib/retrieval/registry/knowledge/knowledge.test.ts src/lib/vidhi/inquiry/pagination.test.ts` — 50 passed.
- Both generated-artifact checks, TypeScript check, and `git diff --check` passed after regeneration.

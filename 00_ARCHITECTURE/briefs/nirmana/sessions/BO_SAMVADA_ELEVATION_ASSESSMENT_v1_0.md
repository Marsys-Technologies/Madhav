---
artifact: BO_SAMVADA_ELEVATION_ASSESSMENT_v1_0.md
canonical_id: NIRMANA_L2_BO_SAMVADA_ELEVATION_ASSESSMENT
version: "1.0"
status: ACCEPTED
campaign_id: nirmana-elevation
definition_revision: t2-2026-09-10-057e53eb
asset_id: bo_samvada
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
produced_on: 2026-09-11
---

# `bo_samvada` elevation assessment

## Outcome

`bo_samvada` meets the L2 target after two production corrections and one governed rebuild.
It is the chart-level orientation digest exposed by `vw_chart_digest` and consumed through
`query_ucd`; it is not an exhaustive evidence response, and consumers must drill from the
digest into signal and domain tools for supporting detail.

The accepted implementation is commit
`22df08aaa1f4d408c4475d50312b87b7ce89a71b` (PR #2591), building on
`0955849d1864a0f94cd746ab9706194831856a04` (PR #2588). Migration
`1029_nirmana_l2_bo_samvada_integrity_scope.sql` is applied in production.

## Assessment

| Perspective | Result | Evidence, consequence, and disposition |
|---|---|---|
| Purpose and value | Meets target | The five-row, one-row-per-ayanamsha digest gives the orientation entry point used by `query_ucd`, retrieval orientation, synergy orchestration, and MCP capability registration. It deliberately summarizes rather than replaces drill-down evidence. |
| Domain correctness | Gap found and resolved | The original `top_convergence_domains` SQL applied `LIMIT 5` after aggregation, so it did not constrain the JSON array. PR #2588 moved the limit into the ordered input. PR #2591 separately corrected `weakest_graha` to the minimum L1 `graha_shadbala_total` rupa fact and made priority/domain tie ordering deterministic. |
| Completeness | Meets target | The canonical chart has exactly five digest rows across the five canonical ayanamshas. Each row carries signal, yoga, dosha and contradiction counts, salience aggregates, weakest graha, priority class and at most five convergence domains. Detailed claims remain intentionally outside this orientation surface. |
| Evidence and uncertainty | Meets target with explicit boundary | Counts and selections are re-derived by the registry integrity contract instead of trusted from the view. `digest_at` is query-time view materialization time, not an upstream-build freshness certificate; upstream acceptance and provenance receipts establish freshness separately. Null scores are ordered last and empty inputs remain honest null/empty results. |
| Architecture and dependencies | Gap found and resolved | The writer previously dropped the shared view with `CASCADE`. PR #2591 uses `CREATE OR REPLACE VIEW`, preserving compatible dependents and grants. The frozen dependency on `bo_pramana_mapa` was satisfied before the accepted rebuild. |
| Consumer integration | Meets target | `query_ucd` reads `vw_chart_digest`, augments it with ranked signal and provenance data, and remains the canonical umbrella capability. Retrieval orientation and synergy orchestration resolve the registered L2 capability instead of duplicating the digest derivation. |
| AI usability | Meets target | The response distinguishes orientation fields from drillable evidence, carries chart and ayanamsha identity, and supplies provenance tables/IDs. Top domains are bounded and deterministically ordered so an AI consumer does not mistake an unbounded aggregate for a ranked top-five statement. |
| Product expression | Meets target | The capability is registered as `marsys://tool/L2/query_ucd` and is bridged to the chart-orientation product surface. Missing chart identity is an error; partial retrieval produces an explicit degraded orientation rather than a fabricated complete reading. |
| Performance and economics | Meets target | The correction is a shared SQL-view definition, not an additional stored-data fan-out. The accepted campaign run completed in about two seconds of recorded run time (`10:40:19.765557Z` to `10:40:21.699636Z`) and produced five canonical rows. No measured hotspot justified further optimization. |
| Reliability and protection | Gap found and resolved | The accepted writer no longer issues destructive view DDL. The production registry check covers columns, five-or-fewer totally ordered domains, L1 weakest-graha authority, priority selection, aggregate agreement, and chart/ayanamsha coverage. The rebuild has a proven v2 output receipt and independent verifier/freeze receipts. |

## Accepted route and bindings

- Route: `correct` / `correctness_change`.
- Registry fingerprint: `0af029511522cd15b77a262f86d1fc9746777de1ab22f2041bbb03e42cb5a422`.
- Analysis digest: `14aac46c66d77f7fdf9e0abaf7ba244fb04002d600cd89661e16e46dc260e4ab`.
- Decision digest: `eff1868a3b0a7595bd3b67b903be3e30329ebe43175f00184f81e51b8e7f5b35`.
- Implementation digest: `84989525bc824bdafae7efc719c6124f1586226919adfe7b7d7069e5619bff5c`.
- Accepted run: `5b06c25b-36ad-44d4-87c2-e0f12edea263`.
- Output digest: `da7b0ba829b037e4fe599f6f8cae3c8e9ba0c3775e4636322dfb9c9f22345db9`.
- Output-digest specification: `759bf9ff3ce18fccf5cf5c44e7728286414ab565295b4820d286707014d95b38`.

No unresolved correctness finding remains for the canonical campaign chart.

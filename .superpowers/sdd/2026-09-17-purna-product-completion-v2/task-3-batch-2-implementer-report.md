# Task 3 — direct-query source packet 2 implementer report

## Files changed

- `platform/src/lib/retrieval/registry/knowledge/source_query_availability.ts`
  - Added exact zero-row-safe source contracts for `query_classical_texts` and
    `query_contradictions`.
- `platform/src/lib/retrieval/registry/knowledge/editorial_review.ts` and
  `compiler.ts`
  - Replaced only the two matching deliberate-dark dispositions with the
    reviewed source contracts. Classical offsets remain explicitly
    non-exhaustive because no cross-mode continuation is pinned.
- `platform/src/lib/retrieval/registry/layers/L2_bodha/query_contradictions.ts`
  - Authored the reviewed `content.contradictions` collection, kept
    discovery/anomaly legs supplemental, added the `contradiction_id` tie-break,
    and bounded discovery inputs before SQL construction.
- Focused knowledge, coverage, and contradiction handler tests.

`query_classical_texts.ts` was not changed. Its handler and pagination behavior
remain outside this packet's production-handler ownership.

## Verification

- `npm exec tsc -- --noEmit` — pass.
- Before generated-snapshot refresh, the focused suite passed:
  `availability_contracts.test.ts`, `knowledge.test.ts`,
  `query_contradictions.contract.test.ts`, and
  `query_classical_texts.pagination.test.ts` — 175 tests passed.
- Coordinator regenerated the knowledge snapshot once during this packet. Its
  generated artifact remains deliberately unstaged and must be regenerated
  again against the final committed source because source-reference ranges were
  tightened afterward.

## Residual risks and unearned claims

- Classical source-query success proves only schema/operator executability. It
  does not prove corpus population, freshness, relevant citations, embedding
  service health, hybrid ranking execution, or frozen-case satisfaction.
- Classical offset exhaustion remains unreviewed across hybrid, trigram-only,
  and ILIKE fallback modes.
- Contradiction zero rows are a reviewed semantic empty. They do not assert
  that a chart has populated contradiction evidence.
- Discoveries and anomalies remain supplemental; their caps never close the
  contradiction collection.
- `judgment_query` remains deliberately dark and is not modified by this
  packet.

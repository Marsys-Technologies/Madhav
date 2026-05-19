---
canonical_id: PHASE_5_CLOSE
version: 1.0
status: CURRENT (campaign sealing artifact)
campaign: PHASE_5_DASHA_CORRECTNESS
closed_on: 2026-05-19
final_commit: 36f9a3c
---

# Phase 5 — Dasha Correctness Campaign · CLOSE

## What shipped (3 sub-phases)

| Sub | Commit | Headline |
|---|---|---|
| 5A | 67b36de | query_dasha_periods (30th tool) + R-DA rule + chart_facts_query date filters + baseline audit |
| 5B | 8649aae | DASHA_DISCIPLINE_GATE in all 4 synthesis templates (predictive v3.1 / factual v2.1 / holistic v2.1 / remedial v2.1) |
| 5C | 36f9a3c | checkpoint_dasha.ts post-synthesis validator with retry × 2 + hard VALIDATOR_FAILURE |

Tool count: 29 → 30 (query_dasha_periods added in §5A).
Planner rules: R-DA added.
Synthesis gates: DASHA_DISCIPLINE_GATE added.
Checkpoints: checkpoint_dasha added.

## Defense stack — all 5 layers closed

| Layer (from research dossier §2) | Closed by |
|---|---|
| Gap A — RCS discoverability | §5A (chart_facts_query advertises dasha categories; query_dasha_periods adds dedicated surface) |
| Gap B — temporal coverage | §5A (query_dasha_periods returns next-N MDs, not just active chain) |
| Gap C — warning in wrong layer | §5B (gate now lives in synthesis prompt, where the LLM actually reads it) |
| Gap D — FORENSIC §5.1 buried | §5A (tool returns surgical rows, not 75 KB document) |
| Gap E — no validator | §5C (checkpoint_dasha catches violations + retries + hard-fails) |

## §5C implementation details

**Validator design**: Deterministic regex-extraction + chart_facts SQL cross-check. No LLM judgment.
Vimshottari-only initially per locked decision §6.4.

**Heuristic gate**: validator runs only when query matches
`/\b(mahadasha|antardasha|...|MD|AD|PD)\b/i` OR `query_plan.tool_calls` contains
`query_dasha_periods`. Non-dasha queries stream normally — UX preserved.

**Buffer-and-validate**: For dasha-relevant queries, synthesis is buffered via
`await result.text` (AI SDK fan-out stream; `toUIMessageStream()` still works after
buffering). Full text validated before route begins HTTP stream to client.

**Retry loop** (in `single_model_strategy.ts`): on halt verdict, re-calls `streamText`
with remediation prompt appended citing canonical `DSH.V.NNN` rows from chart_facts.
Up to 2 silent retries; 3rd failure → `CheckpointHaltError`.

**HTTP 422 shape** (from `consume/route.ts`):
```json
{
  "error": "VALIDATOR_FAILURE",
  "validator": "checkpoint_dasha",
  "violations": [
    { "span": "Saturn MD next", "lord": "Saturn", "temporal": "next", "violation": "temporal_claim_no_citation" }
  ],
  "retry_count": 2,
  "message": "Synthesis violated DASHA DISCIPLINE GATE after 2 retries..."
}
```

**Feature flags**:
- `CHECKPOINT_DASHA_ENABLED` — default `false` (safe rollout)
- `CHECKPOINT_DASHA_FAIL_HARD` — default `true` (once enabled, halt is enforcement)

**Test coverage**: 21 unit tests (checkpoint_dasha.test.ts) + 4 integration tests
(single_model_strategy.test.ts). All green.

## Verification gates (all passed at §5C commit)

| Gate | Command | Result |
|---|---|---|
| G1 | `npx tsc --noEmit` | 0 errors |
| G2 | `npx vitest run src/lib/checkpoints/__tests__/checkpoint_dasha.test.ts` | 21/21 pass |
| G3 | `npx vitest run src/lib/synthesis/__tests__/single_model_strategy.test.ts` | 4/4 pass |
| G4 | `npx vitest run src/lib/` | 1698+/1729 (9 pre-existing aiops failures, unchanged) |
| G5 | `npx vitest run tests/eval/planner_regression_gate.test.ts` | 2/2 pass |

## Production rollout

Feature flag `CHECKPOINT_DASHA_ENABLED` defaults to `false`. Operator flips on after
verifying §5C unit tests pass in production environment + a sample hand-test against
the live consume route. Recommended sequence:

1. Deploy §5C commit (`36f9a3c`) to Cloud Run (no flag flip).
2. Hand-test: send "what's my next mahadasha?" to live endpoint with flag ON via env
   override (`MARSYS_FLAG_CHECKPOINT_DASHA_ENABLED=true`); verify response cites
   `DSH.V.024` (Ketu MD, 2027-08-21 to 2034-08-18).
3. Run consolidated answer:eval batch (combining Phase 4 + Phase 5 changes — the
   deferred batch declared 2026-05-17).
4. Flip `CHECKPOINT_DASHA_ENABLED=true` permanently.

## Lessons captured

- **Multi-layer defense > single-point-of-failure.** Each of §5A/§5B/§5C alone reduces
  the wrong-MD failure rate; together they make it structurally impossible.
- **Deterministic validators are cheap.** Regex + SQL cross-check costs ~10ms; an LLM
  judge would cost ~500ms-2s per claim. Use determinism when the ground truth is structured.
- **Buffer-and-validate is acceptable for narrow query classes.** Streaming UX preserved
  for non-dasha queries via heuristic gate; latency budget for dasha queries is a
  conscious trade-off for correctness.
- **AI SDK fan-out streams.** `await result.text` does NOT drain the stream for
  `toUIMessageStream()` — the AI SDK uses internal broadcast channels, so multiple
  consumers work. This pattern is safe for pre-stream validation hooks.
- **The 5-layer-diagnosis pattern generalizes.** The same methodology from
  EPHEMERIS_ACCESSIBILITY (Gap A–E → tool + gate + validator) applies to any
  "data correct, synthesis hallucinates" class (transit aspects, divisional dignity,
  classical citations). Worth codifying as a generalizable research method.

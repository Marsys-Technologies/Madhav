---
lane: F-69
stream: S3_SATYA (spec + build)
stage: S (SPEC)
author: SATYA builder (S3)
status: DRAFT — awaiting VERIFIER review
depends_on_diagnosis: DIAGNOSIS.md
companion_lane: F-68 (same defect class, L4 Phala; see that lane's SPEC.md §0/§0a for the shared
  precedent search and the reasoning against one cross-layer shared utility)
---

# SPEC — mimamsa_insight_get: suppress numeric rank/confidence/grade under non-calibrated evidence_grade

## 0. P3-b precedent search (read first)

Same search as F-68's companion spec (`../F-68/SPEC.md §0`, not re-run here — see that document for
the full trace). Summary: the real P3-b implementation lives in `services/ka_kshetra/` (L3 Kāla) —
`hazard.py`'s `HazardTerms.baseline_is_synthetic` tag (computed, stored, never mutated) plus
`stage8_spec.py:136`'s serve-shape suppression (`None if window.get("baseline_is_synthetic") else
float(...)`), gated by `test_p3b_suppression.py`'s explicit purpose: *"must not emit a float that
looks like a calibrated prediction."* No generic importable utility exists anywhere in the tree —
the precedent is inline logic at the shape-assembly boundary, not an exported helper.

**Insertion-point decision:** DIAGNOSIS.md traced the mechanism to `mi_darshana.py:247/366/509` (the
writer, where `evidence_grade` literals are hardcoded per row-append). Mirroring P3-b's actual
insertion point instead (serve boundary, not compute/write boundary — same reasoning as F-68's
SPEC.md §0, points 1-3), this spec fixes the **TS serving layer**, confirmed during SPEC research to
be:
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts` — the capability
  (`marsys://tool/L5/query_insights`) `mimamsa_insight_get` calls
  (`platform-mcp/src/tools/register_p1_synthesis.ts:570`), which currently returns
  `insight_units: insightResult.rows` — **raw DB rows, zero transform** (confirmed by reading the
  full function body; this is exactly what DIAGNOSIS.md's serving-side analysis independently found
  from the `register_p1_synthesis.ts` wrapper side — the wrapper doesn't transform because nothing
  upstream does either).
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insight_embeddings.ts` — a genuine
  **sibling site DIAGNOSIS.md's census did not reach** (its census stopped at `mi_darshana.py`'s
  hardcoded literals; this is a different consumer of the same `mimamsa_insight_units` table). Its
  `mode=nearest` handler (lines 111-142) SELECTs `u.rank_consequence` directly, unsuppressed, with no
  `evidence_grade` in scope to gate it at all — found via a broader grep across every `mimamsa_
  insight_units` consumer, not just the one wrapper DIAGNOSIS.md read. See §4.

Does **not** touch `mi_darshana.py` at all. This has a direct, favorable consequence for one of
DIAGNOSIS.md's own named risks (§5, "MC-010 precedent risk"): since MC-010's verb-masking logic
lives in a different function in that same writer file, and this spec never opens that file, the
risk of perturbing MC-010 while fixing this defect is eliminated by construction, not merely avoided
by care.

## 1. Root-cause statement

`query_insights.ts`'s `mimamsa_insight_get` capability selects `rank_consequence`, `confidence_band`,
`evidence_grade`, and `provenance_chain` from `mimamsa_insight_units` and returns
`insight_units: insightResult.rows` with no shaping step at all — so every row's precise numeric
`rank_consequence`, `confidence_band`, and `provenance_chain.grade` are served exactly as stored,
regardless of that same row's own `evidence_grade` column, which for every `verdict_object` row is
permanently `'structural'` (hardcoded, `mi_darshana.py:366,509`) and for `retrodiction`/
`emergent_law` rows is `'prior_only'` unless `n_support >= 5` (`mi_darshana.py:215`, honestly
conditional). No suppression, rounding, or bucketing exists anywhere between the DB row and the MCP
response.

**Disclosure convention adopted — identical to F-68's SPEC.md §1; do not diverge:** suppress by
**NULLing the numeric field(s), keeping the JSON key present**, no redundant flag alongside an intact
number. F-69's own diagnosis (§5) flagged the trade-off explicitly and leaned toward "an additive
`judgment_flags`-style flag is lower blast-radius than mutating the numeric fields" — this spec
overrides that lean, for the same reason argued in F-68's spec: the complaint here is deceptive
*precision* (a `0.88` rank sitting next to `evidence_grade: 'structural'`), and `evidence_grade` is
**already present on every row** and already discloses the epistemic status — adding a second flag
next to an untouched `0.88` does not stop a caller from reading and using that `0.88` as if it were
calibrated. Nulling does. This is a disclosed null (the row still explicitly says why, via
`evidence_grade`), not the silent drop §N.6 warns against.

## 2. Files to change

### 2a. `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts` (lines 127-144)

What: map `insightResult.rows` through a suppression transform before returning as `insight_units`.

Predicate — **whitelist**, unlike F-68's blacklist, and justified differently: `evidence_grade`
already has one established, actively-used calibrated literal in this exact codebase —
`'empirical'` (used as a real SQL filter at `mi_darshana.py:151`, `AND evidence_grade = 'empirical'`,
and as the true branch of a real conditional at `mi_darshana.py:215`,
`"empirical" if n >= 5 else "prior_only"`). Whitelisting the one value known to mean "calibrated" is
therefore grounded in existing usage (unlike F-68, where no such literal exists yet). This also
correctly and automatically preserves the honestly-conditional C3 behavior: a retrodiction row that
reaches `n_support >= 5` gets `evidence_grade: 'empirical'` and is served numerically; one that
doesn't gets suppressed — the SAME per-row predicate handles both without any `insight_type`
special-casing.

```ts
const EMPIRICALLY_CALIBRATED = 'empirical'

function suppressIfNotCalibrated(row: Record<string, unknown>): Record<string, unknown> {
  if (row['evidence_grade'] === EMPIRICALLY_CALIBRATED) return row
  // P3-b tier-suppression (F-69): evidence_grade is anything other than 'empirical' (structural,
  // prior_only, missing) → no empirically-calibrated score exists for this insight. Mirrors
  // ka_kshetra/stage8_spec.py:136. The stored mimamsa_insight_units row is never mutated.
  const pc = row['provenance_chain'] as Record<string, unknown> | null
  return {
    ...row,
    rank_consequence: null,
    confidence_band: null,
    provenance_chain: pc == null ? pc : { ...pc, grade: null },
    tier_suppression_note: `rank_consequence/confidence_band/provenance_chain.grade suppressed at serve time: evidence_grade=${JSON.stringify(row['evidence_grade'])} — no empirically-calibrated score exists for this insight yet (P3-b tier-suppression; see services/ka_kshetra/stage8_spec.py for the precedent this mirrors). The stored value is unaffected.`,
  }
}
```

And in the handler body (was `insight_units: insightResult.rows`):

```ts
return {
  content: {
    chart_id,
    insight_units:       insightResult.rows.map(suppressIfNotCalibrated),
    calibration_summary,
    filters:             { insight_type, domain, min_rank, top_k, include_neg },
    total_returned:      insightResult.rows.length,
  },
  is_error: false,
}
```

Note on `provenance_chain`: only its `.grade` sub-key is nulled, never the whole object — confirmed
by reading `register_p1_synthesis.ts`'s downstream evidence-trimming logic (lines 508-538,
`trimTopEvidence`-shaped helper), which reads `provenance_chain.ranked_evidence[].salience` and
`.classical_sources` for ALL rows regardless of calibration status; nulling the whole object would
silently break that unrelated, still-correct trimming behavior — a regression this spec must not
introduce.

Note on `total_returned`: intentionally left as the raw row count (unchanged) — this is the honest
count of insight units returned, not a claim about how many are numerically scored; no defect here
per DIAGNOSIS.md's own claim decomposition (C1-C4 never assert `total_returned` is the problem).

### 2b. `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insight_embeddings.ts`
(lines 116-127, `mode=nearest` branch) — sibling site found during SPEC research, see §4

What: add `u.evidence_grade` to the SELECT and apply the same suppression to `rank_consequence` in
the returned rows (this handler otherwise passes `result.rows` straight through with zero shaping,
same defect shape as §2a pre-fix).

```ts
const sql = `
  SELECT n.insight_id, (n.embedding <=> s.embedding) AS cosine_distance,
         u.insight_type, u.statement, u.rank_consequence, u.evidence_grade
  FROM mimamsa_insight_embeddings n
  JOIN mimamsa_insight_embeddings s
    ON s.chart_id = n.chart_id AND s.insight_id = $2
  LEFT JOIN mimamsa_insight_units u
    ON u.chart_id = n.chart_id AND u.insight_id = n.insight_id
  WHERE n.chart_id = $1 AND n.insight_id != $2
  ORDER BY cosine_distance ASC
  LIMIT $3`
const result = await query(sql, [chart_id, seedId, topK])
const rows = (result.rows as Array<Record<string, unknown>>).map(row =>
  row['evidence_grade'] === 'empirical' ? row : { ...row, rank_consequence: null }
)
return {
  content: {
    chart_id, mode, seed_insight_id: seedId,
    rows, count: rows.length,
    ...(rows.length === 0
      ? { empty_reason: `No neighbor rows found for seed_insight_id=${seedId} (seed may not exist, or the table is not yet populated for this chart's build).` }
      : {}),
    provenance: { tables: ['mimamsa_insight_embeddings', 'mimamsa_insight_units'], source: 'L5 Mīmāṃsā pgvector cosine-distance nearest-neighbor search between two already-computed embeddings; served chart-scoped.' },
  },
  is_error: false,
}
```
(`count: rows.length` is unchanged in value from `result.rows.length` — the map is a 1:1 transform,
row count never changes; renamed the local var only.) `n.insight_id` row-existence path (mode !=
'nearest', lines ~90-108 of the same file) does not select `rank_consequence` at all — not a sibling,
not changed.

## 3. Exit test

New file: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/__tests__/
query_insights_p3b_suppression.test.ts`

```ts
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryInsightsCapability } from '../query_insights'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function row(overrides: Record<string, unknown>) {
  return {
    insight_id: 'ins-test', insight_type: 'verdict_object', domain: 'career',
    statement: 'test statement', rank_consequence: 0.88, confidence_band: '[0.68,0.98)',
    n_support: 3, is_negative_knowledge: false,
    provenance_chain: { grade: 8.8, ranked_evidence: [{ salience: 0.9, fact_id: 'f1' }] },
    ...overrides,
  }
}

describe('query_insights — P3-b tier-suppression (F-69)', () => {
  beforeEach(() => queryMock.mockReset())
  afterEach(() => vi.restoreAllMocks())

  it('evidence_grade=structural → rank_consequence/confidence_band/provenance_chain.grade suppressed, tag + other provenance_chain keys preserved', async () => {
    queryMock.mockResolvedValueOnce({ rows: [row({ evidence_grade: 'structural' })] })
    queryMock.mockResolvedValueOnce({ rows: [{}] }) // calibration_summary query
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    const unit = result.content.insight_units[0]
    expect(unit.rank_consequence).toBeNull()
    expect(unit.confidence_band).toBeNull()
    expect((unit.provenance_chain as Record<string, unknown>).grade).toBeNull()
    // Non-numeric provenance_chain content survives — unrelated to this suppression.
    expect((unit.provenance_chain as Record<string, unknown>).ranked_evidence).toBeDefined()
    expect(String(unit.tier_suppression_note)).toMatch(/suppressed at serve time/i)
    expect(unit.evidence_grade).toBe('structural')
  })

  it('evidence_grade=prior_only (retrodiction, n_support<5) → also suppressed', async () => {
    queryMock.mockResolvedValueOnce({ rows: [row({ insight_type: 'emergent_law', evidence_grade: 'prior_only' })] })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    expect(result.content.insight_units[0].rank_consequence).toBeNull()
  })

  it('evidence_grade=empirical → numeric fields pass through unchanged (honest-conditional C3 case preserved)', async () => {
    queryMock.mockResolvedValueOnce({ rows: [row({ insight_type: 'emergent_law', evidence_grade: 'empirical', n_support: 7 })] })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    const unit = result.content.insight_units[0]
    expect(unit.rank_consequence).toBe(0.88)
    expect((unit.provenance_chain as Record<string, unknown>).grade).toBe(8.8)
    expect(unit.tier_suppression_note).toBeUndefined()
  })
})
```

**Fails today:** the first two cases fail — `insight_units: insightResult.rows` has no transform, so
`rank_consequence` stays `0.88` and `provenance_chain.grade` stays `8.8` regardless of
`evidence_grade`. **Passes after §2a lands.** Third case already passes today (documents preserved
calibrated-path behavior — the honest C3 differential this fix must not break).

## 4. Sibling sites covered

From DIAGNOSIS.md §4 (`mi_darshana.py` hardcode census) — **not fixed at the writer (deliberately,
§0)**, but automatically covered at the serve boundary because suppression is keyed on the row's
`evidence_grade` value, not on `insight_type`:

| Insight type (mi_darshana.py line) | Covered by this spec's serve-time fix? |
|---|---|
| `load_bearing` (line 247, hardcoded `'structural'`) | **Yes** — same table (`mimamsa_insight_units`), same `query_insights.ts` path, same predicate. No `insight_type`-specific code needed; this is the "one predicate covers both verdict_object and load_bearing in one pass" outcome DIAGNOSIS.md §4 itself anticipated. |
| `verdict_object` (lines 366, 509, hardcoded `'structural'`) | **Yes** — this finding's own primary target. |
| `emergent_law`/retrodiction (line 215, real conditional) | **Yes**, correctly differentially — `n_support>=5` rows pass through, others suppress (C3, preserved not "fixed" since it wasn't broken). |
| `calibrated_outlook` (line 117, reads real DB column) | Covered by the same generic predicate; not a defect (DIAGNOSIS.md confirmed legitimate passthrough), no special-casing needed or added. |
| `manifestation_grammar` (line 184, hardcoded `'empirical'` but SQL-filtered to it) | Covered/no-op — these rows genuinely have `evidence_grade='empirical'`, so the predicate correctly never suppresses them. |

**New sibling found during SPEC research, covered:** `query_insight_embeddings.ts`'s `mode=nearest`
handler — §2b.

**Excluded, with reason:** `mi_sambandha.py` and `mi_pramana.py` — DIAGNOSIS.md §4 flagged these as
"not confirmed clean" but writing `evidence_grade` as a bound SQL parameter, not an inline hardcoded
literal (i.e., not the C2 defect shape). Independently confirmed during SPEC research: these writers
populate different tables (`mimamsa_calibration`/`mi_pramana`'s own table, not `mimamsa_insight_
units`), served through different, not-yet-identified MCP surfaces — not `mimamsa_insight_get` or
`query_insight_embeddings`. Out of this finding's claim scope (F-69 is specifically about
`mimamsa_insight_get`); if either exhibits the same unconditional-numeric-serving pattern, that is a
new finding requiring its own diagnosis of its own serving path, not folded into this spec.

**MC-010** (`mi_darshana.py:419,440,456,487`) — explicitly not a sibling, not touched: it masks the
verdict *verb* for a different consumer path (`verdict_summary`/`bodha_domain_reading_get`), a
different function in a file this spec never opens (§0).

## 5. Recurrence guard

The exit test (§3) is co-located with the fix and runs in the existing Vitest suite; any future edit
to `query_insights.ts` or `query_insight_embeddings.ts` that drops the suppression map fails it
immediately. Same recommended follow-up as F-68's SPEC.md §5 (a shared census lint over
`L4_phala/**` + `L5_mimamsa/**` flagging raw confidence/precision-shaped fields with no gated
suppression) — not duplicating that proposal here; see the companion spec.

## 6. Dependencies and rollback

No DB migration; no schema change; no writer rebuild — pure read-boundary change, applies to every
existing `mimamsa_insight_units` row on the next request. No dependency on any other PARIŚEṢA lane,
including F-68 (independently buildable and revertible; the two share only a documentation
cross-reference, not code or a file lease). CL-00 controls checked (`ekv_controls.py`, grepped for
`mimamsa_insight`/`evidence_grade`/`rank_consequence`): the only match is an unrelated chart-id
enumeration UNION query (line 201) — no control asserts on this tool's numeric-field shape.

Rollback: revert the single commit touching `query_insights.ts` + `query_insight_embeddings.ts` +
the new test file (§2a, §2b, §3). Additive/corrective only; `calibration_summary`, `filters`,
`total_returned`, and every non-numeric `insight_units` field are untouched — no other tool's
response contract changes.

## 7. Coverage table — every D-2 sub-claim mapped

| Sub-claim (DIAGNOSIS.md §2) | Spec element |
|---|---|
| C1: top-level envelope declares layer non-calibrated (`calibration_status`/`mode`) | **Not changed.** Already correct disclosure at the wrapper level (`register_p1_synthesis.ts:578-580`) — not this finding's defect. |
| C2: verdict_object's evidence_grade permanently 'structural' by construction | **Not changed, deliberately** — same framing as F-68's C2: this is accurate current reality (no calibration mechanism sets it otherwise), not itself the defect. This spec makes serving correctly RESPOND to C2, per §0/§1. |
| C3: retrodiction's evidence_grade honestly conditional on n_support>=5 (not a permanent-tag defect the way C2 is) | **Preserved, not broken** — §2a's per-row predicate (keyed on the actual `evidence_grade` value, not `insight_type`) automatically serves numerics for the `n>=5` case and suppresses otherwise; §3's third test case is the regression guard for this differential behavior. |
| C4: both row types served with full numeric fields despite C1-C3, no suppression anywhere in the served payload | §2a (`query_insights.ts` suppression map) + §2b (sibling `query_insight_embeddings.ts` fix) + §3 exit test |

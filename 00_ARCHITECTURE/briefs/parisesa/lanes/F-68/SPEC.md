---
lane: F-68
stream: S3_SATYA (spec + build)
stage: S (SPEC)
author: SATYA-LEAD (S3)
status: DRAFT — awaiting VERIFIER review
depends_on_diagnosis: DIAGNOSIS.md (board-corrected to OPEN/full-pipeline; ekv/b-07-nimitta-tag
  credited as an orthogonal, non-blocking vocab-hygiene prerequisite, not the fix)
---

# SPEC — phala_predictive_anchors_get: suppress numeric posterior/lift under non-calibrated tag

## 0. P3-b precedent search (read first — this is why the fix lands where it does)

Per instruction, searched `platform/python-sidecar` for `shape_only`/`calibrated` before designing
anything new. Found the real P3-b implementation, entirely in `services/ka_kshetra/` (L3 Kāla):

- `contracts.py:284` — `SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT` (pinned synthetic baseline constant).
- `hazard.py:399-425` — `HazardTerms.baseline_is_synthetic: bool` (§N.8 earned-signal tag,
  threaded from `evaluate(shape_only=...)` onto every computed row; docstring explicitly: "downstream
  consumers can SUPPRESS or RELABEL absolute-count fields (P3-b census)").
- `hazard.py:509` — `baseline_rate(lifetime_count, shape_only=shape_only)` returns
  `(SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT / DAYS_PER_CENTURY, True)` for shape_only classes — the
  **raw computed value is still produced and stored**; nothing is dropped at compute time.
- **`stage8_spec.py:136`** — the actual suppression, at the JSON-shape-assembly boundary:
  ```python
  "expected_count": None if window.get("baseline_is_synthetic") else float(window["expected_count"]),
  ```
- `tests/test_p3b_suppression.py` — the TDD gate, whose own docstring states the principle this
  spec adopts verbatim: *"shape_only windows have no empirically derived expected_count and must
  not emit a float that looks like a calibrated prediction."*

**There is no importable, generic P3-b utility function** (e.g. no
`suppress_numeric_if_not_calibrated(value, tag)` helper anywhere in the tree) — the precedent is
inline, per-field ternary logic living at the module that assembles the served JSON shape
(`stage8_spec.py`), not at the module that computes the raw values (`hazard.py`). This spec follows
that shape rather than inventing a generic cross-layer utility: see §0a for why a shared utility
with F-69 was considered and rejected in favor of two independently-complete, convention-matched
specs.

**Insertion-point decision, not inherited blindly from DIAGNOSIS.md:** DIAGNOSIS.md traced the
mechanism to `ph_nimitta/engine.py:418/472/579/685` (the compute layer, `AnchorRecord` construction).
Mirroring the *actual* P3-b insertion point instead — the serving-shape boundary, not the compute
boundary — this spec fixes `platform/src/lib/retrieval/registry/layers/L4_phala/
query_predictive_anchors.ts` (confirmed live during SPEC research to be the ONLY TS capability that
reads `phala_anchors.posterior`/`lift_vector_jsonb`/`confidence_low`/`confidence_high` — the file the
MCP tool `phala_predictive_anchors_get` actually calls via `marsys://tool/L4/query_predictive_anchors`,
per `platform-mcp/src/tools/register_p1_aliases.ts:1085`). Reasons, matching precedent exactly:
1. Applies to every row that exists **today**, immediately — no writer rebuild/backfill required
   (`engine.py` only runs at build time; a serve-time fix covers the whole existing `phala_anchors`
   table on the next request).
2. The raw computed `posterior`/`lift_vector_jsonb` stay in the DB untouched (B.10 — governs
   disclosure, never destroys data), exactly as `hazard.py`'s real λ stays stored while
   `stage8_spec.py` nulls only the served shape.
3. Does not touch `engine.py`'s `confidence_basis` tagging logic, which is already correct (every
   anchor honestly carries `'structural_not_yet_empirical'` because no calibration mechanism exists
   yet — JL-009/BA-P5B) — that tag is not the defect; the unconditional downstream attachment is.

### 0a. Why not one shared Python/TS utility with F-69 (companion lane, same defect class)

F-69 (L5 Mīmāṃsā `mimamsa_insight_get`) has the identical defect class. Considered a shared helper
(`brahmagyan/phala/confidence_vocab.py`-adjacent, per the task brief's suggestion) and rejected it:
- Both fixes' real insertion points (per §0's precedent-matching logic, independently re-derived for
  F-69 in its own SPEC.md) are **TypeScript** serving-layer files, not the Python writers
  `confidence_vocab.py` sits next to — so a Python shared utility helps neither.
- The two predicates are not the same shape: F-68 has no established "calibrated" literal anywhere
  in the codebase for `confidence_basis` (see §1), so it must **blacklist** the one known
  non-calibrated literal; F-69's `evidence_grade` already has a real, actively-used calibrated
  literal (`'empirical'`, used as a SQL filter elsewhere in the same file — `mi_darshana.py:151`), so
  it **whitelists** that literal instead. Forcing one parametrized helper over two differently-shaped
  predicates would add indirection without saving meaningful code (each suppression body is ~4 lines).
- The two fix files sit in different PARIŚEṢA stream-lease subtrees (`L4_phala/**` vs
  `L5_mimamsa/**`); a shared file would have to live outside both globs, which is avoidable friction
  for a few lines of logic.
Both specs instead apply the **identical disclosure convention** (§1) and cite the identical P3-b
precedent files, so behavior and reviewer legibility stay unified without a cross-lease import.

## 1. Root-cause statement

`query_predictive_anchors.ts`'s row-shaping `.map()` (lines 184-217) copies every `phala_anchors`
row's `posterior`, `confidence_low`, `confidence_high`, and `lift_vector_jsonb` straight into the
served response via `{...row, ...}` with no branch conditioned on that same row's own
`confidence_basis` column — so a permanently-`'structural_not_yet_empirical'`-tagged anchor (which,
per DIAGNOSIS.md §1, is every anchor observed live, since no calibration path has ever set the
column to anything else) is served with full-precision numeric fields that look exactly like a
calibrated prediction, alongside a tag that says it is not one.

**Disclosure convention adopted (identical in F-69's SPEC.md; do not diverge):** suppress by
**NULLing the numeric field(s), keeping the JSON key present** (never omit the key), and **never add
a redundant boolean/flag field alongside an intact number**. Justification against the actual
complaint: F-68's claim is deceptive *precision*, not missing disclosure — `confidence_basis` is
already present on every row and already discloses the epistemic status; a flag next to an
unmodified `0.322` doesn't fix deceptive precision (the number is still there, still usable
numerically, a caller can ignore the flag) — nulling does, and is exactly what P3-b's own gate test
asserts is required ("must not emit a float that looks like a calibrated prediction"). Keeping the
key (vs. omitting it) preserves a stable response shape for existing callers and avoids a second
defensive-programming burden (`key in obj` checks); the already-present `confidence_basis` field
is the caller's signal for *why* the sibling numeric fields are null — this is a disclosed null,
not a silent drop (§N.6's "never silently drop" concern is about dropping the ROW/finding, not
about nulling one already-tagged field with the tag still attached).

## 2. Files to change

### 2a. `platform/src/lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts` (lines 184-217)

What: gate the row-shaping `.map()` on `confidence_basis`, nulling `posterior`, `confidence_low`,
`confidence_high`, and `lift_vector_jsonb` when the row is not calibrated, before the existing
`posterior_provenance` derivation runs (which already handles a null `posterior`/`liftVector`
correctly — §2a note below).

Predicate — **blacklist**, not whitelist, and justified: there is no literal string anywhere in this
codebase that means "calibrated" for `phala_anchors.confidence_basis` (grepped; the column is free
text, `NOT NULL DEFAULT 'structural_not_yet_empirical'`, migration `330_phala_anchors_and_drop_
kala_timeline.sql:48`, and `engine.py` never assigns any other value — confirmed zero non-default
assignments). Whitelisting a not-yet-existing "calibrated" literal would mean inventing vocabulary
this spec has no authority to ratify (B.10). Blacklisting the one literal that is known to mean
"not calibrated" is grounded in what actually exists. **Fail-closed on absence**: treat a missing/
null `confidence_basis` as non-calibrated too (do not trust an unlabeled row) — this only differs
from a pure `!==` check for a malformed/legacy row that has no tag at all, and errs toward more
disclosure, matching the PRATINIDHI standing rule ("choose the option that discloses more").

```ts
const NOT_YET_CALIBRATED = 'structural_not_yet_empirical'

const anchorsWithProvenance = (result.rows as Array<Record<string, unknown>>).map(row => {
  const basis = row['confidence_basis']
  // P3-b tier-suppression (F-68): fail-closed — null/missing/NOT_YET_CALIBRATED all suppress.
  // Mirrors ka_kshetra/stage8_spec.py:136's `None if window.get("baseline_is_synthetic") else
  // float(...)`. The stored phala_anchors row is never mutated — only the served shape changes.
  const isCalibrated = basis != null && basis !== NOT_YET_CALIBRATED

  const posterior      = isCalibrated ? (row['posterior'] as number | null)       : null
  const confidenceLow  = isCalibrated ? (row['confidence_low'] as number | null)  : null
  const confidenceHigh = isCalibrated ? (row['confidence_high'] as number | null) : null
  const liftVector     = isCalibrated
    ? (row['lift_vector_jsonb'] as Record<string, unknown> | null)
    : null

  const base = { ...row, posterior, confidence_low: confidenceLow, confidence_high: confidenceHigh,
                 lift_vector_jsonb: liftVector }

  if (posterior == null || liftVector == null) {
    return {
      ...base,
      posterior_provenance: null,
      posterior_provenance_note: isCalibrated
        ? 'posterior/lift_vector_jsonb not computed for this anchor (pre-BA-P5B row or backfill pending) — no cardinality/base_rate_source to report.'
        : `posterior/confidence_low/confidence_high/lift_vector_jsonb suppressed at serve time: confidence_basis=${JSON.stringify(basis)} — no empirically-derived posterior exists for this anchor yet (P3-b tier-suppression; see services/ka_kshetra/stage8_spec.py for the precedent this mirrors). The computed values remain stored in phala_anchors, unaffected.`,
    }
  }
  return {
    ...base,
    posterior_provenance: {
      model: 'deterministic_product_lift',
      model_formula: 'posterior = base_rate × promise_lift × activation_lift × trigger_lift × ayanamsha_robustness_modifier',
      cardinality: null,
      cardinality_note: 'Not a sample-fit statistic — this posterior has no underlying N of observed outcomes to report (never fabricated). The empirically-calibrated analog with a genuine n_observations is L5 query_calibration (mimamsa_multipliers).',
      base_rate_source: 'brahma_event_ontology.base_rate_by_age, row-normalized to sum 1.0 (JL-009 closed 2026-07-07), looked up for the age band containing this anchor’s predicted date (peak_date, else window_start) relative to the native’s birth date. Falls back to the uniform age prior (0.20, 1-of-5-bands) when the ontology vector or a usable date is unavailable for this anchor — never a fabricated non-uniform value.',
      base_rate_value: liftVector['base_rate'] ?? null,
      base_rate_matches_uniform_fallback_value: typeof liftVector['base_rate'] === 'number' ? liftVector['base_rate'] === 0.2 : null,
      promise_lift_source: "bodha_pratijna.grade for this anchor's event_class, mapped to a multiplicative lift (grade>5 amplifies, grade<5 dampens, grade=NULL from no_evidence → lift=1.0 neutral). A no_evidence promise_lift of 1.0 means the anchor's posterior was not amplified or dampened by promise data — the prediction stands on its other factors (base_rate, activation_lift, trigger_lift) alone.",
      promise_lift_value: liftVector['promise_lift'] ?? null,
    },
  }
})
```

This is a minimal, structure-preserving edit: the existing `posterior_provenance` branch (lines
187-216) is reused verbatim for the calibrated path — only its two local variables (`posterior`,
`liftVector`) now come from the suppression gate above instead of directly off `row`, and the
existing null-case note is disambiguated from the new suppressed-case note (see §2a note below).

**§N.8 note on `F-103` (governance control):** `platform/scripts/governance/ekv_controls.py:514-528`
(`_check_f103`) is a **static source-text** check — it greps this exact file for the literal string
`base_rate_matches_uniform_fallback_value` and fails only if that string is hardcoded to `true`.
This edit keeps that field's real-comparison construction code intact (only now reachable inside the
`isCalibrated` branch, never removed or hardcoded) — F-103 remains PASS. Verified by reading
`_check_f103`'s implementation directly, not assumed.

### 2b. `platform/src/lib/retrieval/registry/layers/L4_phala/__tests__/posterior_provenance.test.ts`
(existing test — MUST be updated, not left as-is)

**Why this file must change, found during SPEC research (not in DIAGNOSIS.md):** its first test
(`'stamps base_rate_source + explicit-null cardinality WITHOUT altering the stored posterior/
lift_vector_jsonb values'`, lines 46-69) asserts `expect(anchor.posterior).toBe(0.322)` against a
`REAL_ANCHOR_ROW` fixture the file's own docstring calls "VERBATIM a real phala_anchors row read live
from prod... for the native chart" — but that fixture **omits `confidence_basis` entirely**. Per
DIAGNOSIS.md §1 (live reproduction on both canonical charts), a truly verbatim real row from prod
always carries `confidence_basis: 'structural_not_yet_empirical'`, which under §2a's fix would
suppress this exact row's `posterior` to `null` — contradicting this test's literal assertion and its
"verbatim real row" framing. Left as-is, this existing regression test would either (a) accidentally
keep passing on a technicality (missing key ≠ the literal, under a naive `!==` check — which is
exactly why §2a's predicate is fail-closed on absence instead, correctly making this test fail loudly
and visibly rather than silently passing on a stale fixture) or (b) mislead a future reader that real
anchors keep their posterior served, which is false post-fix for every anchor observed to date.

Change: split into two cases, both with an explicit, honest `confidence_basis`:
1. Rename `REAL_ANCHOR_ROW` fixture to add `confidence_basis: 'structural_not_yet_empirical'`
   (its true, verified-live value) and change the test's assertions to
   `expect(anchor.posterior).toBeNull()`, `expect(anchor.confidence_low).toBeNull()`,
   `expect(anchor.lift_vector_jsonb).toBeNull()`, `expect(anchor.posterior_provenance).toBeNull()`,
   `expect(String(anchor.posterior_provenance_note)).toMatch(/suppressed at serve time/i)`. Retitle
   the test to reflect what it now demonstrates (suppression, not pass-through).
2. Add a new fixture (`CALIBRATED_ANCHOR_ROW`, same numeric values, `confidence_basis: 'some_future_
   calibrated_value'`) and a new test asserting the ORIGINAL pre-fix behavior (posterior/lift_vector_
   jsonb pass through unchanged, `posterior_provenance` computed) still holds for a calibrated row —
   this preserves the file's original "canonical-or-floor: never re-derive a calibrated value"
   intent, now correctly scoped to calibrated rows only, since no such row exists in prod today.
3. The existing "legacy anchor" test (lines 71-84, `posterior: null, lift_vector_jsonb: null`, no
   `confidence_basis` key) is unaffected by this predicate change — its `posterior`/`liftVector` are
   already `null` before the gate runs, so it still returns the "not computed" note, not the
   suppression note. Confirmed by tracing the logic in §2a; no change needed to this sub-test.

## 3. Exit test

New file: `platform/src/lib/retrieval/registry/layers/L4_phala/__tests__/
p3b_predictive_anchors_suppression.test.ts`

```ts
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryPredictiveAnchorsCapability } from '../query_predictive_anchors'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const BASE_ROW = {
  anchor_id: 'p3b-test-anchor', domain: 'career',
  posterior: 0.322,
  confidence_low: 0.20, confidence_high: 0.45,
  lift_vector_jsonb: {
    base_rate: 0.2, posterior: 0.322, promise_lift: 1.75,
    trigger_lift: 1, activation_lift: 1, ayanamsha_robustness_modifier: 0.92,
  },
}

describe('query_predictive_anchors — P3-b tier-suppression (F-68)', () => {
  beforeEach(() => queryMock.mockReset())
  afterEach(() => vi.restoreAllMocks())

  it('confidence_basis=structural_not_yet_empirical → numeric fields suppressed to null, tag preserved', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ ...BASE_ROW, confidence_basis: 'structural_not_yet_empirical' }] })
    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
    }
    const anchor = result.content.anchors[0]
    expect(anchor.posterior).toBeNull()
    expect(anchor.confidence_low).toBeNull()
    expect(anchor.confidence_high).toBeNull()
    expect(anchor.lift_vector_jsonb).toBeNull()
    expect(anchor.posterior_provenance).toBeNull()
    expect(String(anchor.posterior_provenance_note)).toMatch(/suppressed at serve time/i)
    // The tag itself is the disclosure and must survive unchanged.
    expect(anchor.confidence_basis).toBe('structural_not_yet_empirical')
  })

  it('missing/null confidence_basis → fail-closed, also suppressed', async () => {
    const { confidence_basis, ...rowWithoutBasis } = { ...BASE_ROW, confidence_basis: undefined }
    queryMock.mockResolvedValueOnce({ rows: [rowWithoutBasis] })
    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
    }
    expect(result.content.anchors[0].posterior).toBeNull()
  })

  it('a genuinely calibrated confidence_basis → numeric fields pass through unchanged', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ ...BASE_ROW, confidence_basis: 'empirically_calibrated' }] })
    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
    }
    const anchor = result.content.anchors[0]
    expect(anchor.posterior).toBe(0.322)
    expect(anchor.lift_vector_jsonb).toEqual(BASE_ROW.lift_vector_jsonb)
    expect((anchor.posterior_provenance as Record<string, unknown>).base_rate_value).toBe(0.2)
  })
})
```

**Fails today:** the first two cases fail — current code has no suppression branch at all, so
`anchor.posterior` is `0.322` (not `null`) and `posterior_provenance` is a populated object (not
`null`) regardless of `confidence_basis`. **Passes after §2a lands.** The third case already passes
today (documents the preserved calibrated-path behavior; not a regression risk).

## 4. Sibling sites covered

**Within `phala_anchors`'s single MCP-facing consumer (confirmed by exhaustive grep of
`platform/src/lib` + `platform-mcp/src` for `phala_anchors`):** `query_predictive_anchors.ts` is the
only capability file that SELECTs `posterior`/`confidence_low`/`confidence_high`/`lift_vector_jsonb`
from `phala_anchors`. Other files referencing the table name were checked and excluded with reason:

| File | Disposition |
|---|---|
| `L4_phala/query_phala_calibration.ts` | Excluded — its `confidence_low`/`confidence_high`/`confidence_basis` columns (line 615, 169) come from a LEL-fit match-quality table (`best_lel_fit_score`, `win_margin`), a structurally different score (match confidence against a recorded outcome, not F-68's un-calibrated predictive posterior). Different claim; flag as a candidate CL-08 sibling for a SEPARATE finding if independently confirmed, not verified here. |
| `L5_mimamsa/query_predictions.ts` | Excluded — its `posterior` reference (line ~101) is a code COMMENT distinguishing its own `base_rate` from `phala_anchors.posterior`; it does not select or serve the flagged columns. |
| `platform-mcp/src/tools/phala_event_anchors.ts` | Excluded — no match for any of the four flagged fields in this file (grepped); per an existing code comment elsewhere in the repo it proxies to a distinct sidecar HTTP endpoint (`/api/compute/phala/event_anchors`), a different code path than this spec's file, outside S3's `ph_nimitta/**` + `L4_phala/**` lease surface for this pass. |
| `compiled_floor_adapter.ts`, `outcome_calibration.ts`, `compute_spine_bundle.ts`, `register_spine_bundle.ts`, `query_prospective_ledger.ts`, `registry_data.ts`, `audit.ts`, `server.ts`, `phala_mitigation_map.ts`, `mimamsa_outcome.ts`, `phala_outlook.ts` | Excluded — none select any of the four flagged fields (grepped, zero matches); reference the `phala_anchors` table name only in comments, counts, or unrelated columns. |

**Excluded, not covered, with reason (from DIAGNOSIS.md §5):** `ph_sankrama/engine.py` and
`ph_sodhana/engine.py` — outside S3's declared `ph_nimitta/**` lease; different writers serving
through different, not-yet-verified MCP surfaces (not `phala_predictive_anchors_get`). If either
exhibits the identical unconditional-numeric-attach pattern, that is a new finding, not this one —
recommend the conductor file a follow-up census rather than silently folding it into this spec's
lease.

## 5. Recurrence guard

The exit test (§3) is co-located with the fix and runs in the existing Vitest suite — any future
edit to `query_predictive_anchors.ts` that removes or bypasses the `isCalibrated` gate fails it
immediately. Recommended (out of scope for this spec — flagging for the conductor as a possible
CL-08 follow-up, matching `fact-category-pin-lint`'s model): a generated census lint over
`L4_phala/**` + `L5_mimamsa/**` `.ts` capability files that flags any raw-row `{...row}` spread
feeding a known confidence/precision-shaped field name (`posterior`, `rank_consequence`,
`confidence_band`, `lift_vector*`) with no accompanying tag-gated suppression branch in the same
function — this would have caught F-68 and F-69 as one class before they shipped.

## 6. Dependencies and rollback

No DB migration; no schema change; no writer rebuild required — the fix is a pure read-boundary
change and applies to every existing `phala_anchors` row on the next request. No dependency on any
other PARIŚEṢA lane. Independent of `ekv/b-07-nimitta-tag` (the vocab-hygiene branch DIAGNOSIS.md
credited as a partial prerequisite): that branch only renames the `confidence_basis` default's
Python-side literal to a named constant in `brahmagyan/phala/confidence_vocab.py` (which does not
exist in this worktree yet — confirmed via `find`); it does not touch `query_predictive_anchors.ts`
at all and can land before, after, or never, without conflicting with this spec. If it lands later,
Build should confirm the Python constant's string VALUE still equals `'structural_not_yet_empirical'`
(the literal this spec's TS predicate blacklists) — a rename to a different string would silently
break the predicate; not expected, but worth a one-line grep check at that time.

Rollback: revert the single commit touching `query_predictive_anchors.ts` + the two test files
(§2b, §3). All changes are additive/corrective within the L4 Phala serving layer; no other tool's
response contract changes (only `phala_predictive_anchors_get`'s numeric fields, which is this
finding's exact target).

## 7. Coverage table — every D-2 sub-claim mapped

| Sub-claim (DIAGNOSIS.md §2) | Spec element |
|---|---|
| C1: precise numeric posterior/confidence band/lift factors served | §2a suppression gate (nulls posterior/confidence_low/confidence_high/lift_vector_jsonb) + §3 exit test |
| C2: confidence_basis permanently 'structural_not_yet_empirical', never conditionally overridden | **Not changed by this spec, deliberately.** C2 is an accurate description of current system reality (no calibration mechanism exists yet — JL-009/BA-P5B gate). This spec does not and should not make C2 false; it makes the serving layer correctly RESPOND to C2's truth, which is what C1/C3 actually demand. |
| C3: identical defect class to the project's own P3-b precedent; L4 implements none of its suppression discipline | §0/§0a (precedent located, convention matched) + §2a (the actual suppression code, mirroring `stage8_spec.py:136`) |

---
lane: F-134
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE
author: SATYA-LEAD (sonnet)
tier: TIER4-POLISH
source_agent: E3
---

# F-134 — judgment_query gochara_sweep serves an already-peaked window inside the "upcoming" set, unflagged

## 1. Live reproduction (today, 2026-08-16, verified)

`judgment_query(chart_id=482012f1-710e-4a25-994a-93821f5871aa, domain='wealth',
response_format='v3')`

Result (salient fields, `content.gochara_sweep`):

```json
{
  "domain": "wealth",
  "domain_covered": true,
  "upcoming_window_count": 3,
  "valence_breakdown": { "gain": 1, "loss": 2 },
  "window_range": { "start": "2026-08-16", "end": "2029-08-16" },
  "top_windows": [
    { "event_class": "major_gain", "temporal_shape": "interval",
      "window_start": "2024-02-05", "window_end": "2034-01-30",
      "peak_date": "2025-04-27", "valence": "gain", "is_adverse": false },
    { "event_class": "financial_deception", "window_start": "2024-02-05",
      "window_end": "2034-01-30", "peak_date": "2030-08-14", "valence": "loss", "is_adverse": true },
    { "event_class": "major_loss", "window_start": "2024-02-05",
      "window_end": "2034-01-30", "peak_date": "2030-08-14", "valence": "loss", "is_adverse": true }
  ]
}
```

`chart_header.timing` / the call's own now-context: `as_of_date: "2026-08-16"`, matching
`window_range.start`. The top-ranked window (`major_gain`, `valence:'gain'`) has
`peak_date: "2025-04-27"` — **1 year 3.5 months before** `as_of_date`/`window_range.start`. It sits
in the same `top_windows` array as two genuinely future `loss` windows (`peak_date: 2030-08-14`),
with no field on the window object or elsewhere in `gochara_sweep` distinguishing "already peaked"
from "still ahead". **CONFIRMED REPRODUCES exactly as claimed.** Not ALREADY-FIXED.

## 2. Claim decomposition

- **C1** — `gochara_sweep` reports `upcoming_window_count=3` with `window_range` starting at "now"
  (`as_of_date`).
- **C2** — its top-ranked (by intensity) window has a `peak_date` more than a year in the past
  relative to the call's own now-context date, despite being served inside this "upcoming" set.
- **C3** — this already-peaked window sits alongside genuinely future windows (peak 2030-08-14)
  with no structural distinction between the two.
- **C4** — no flag (`is_past_peak`, `already_occurred`, or equivalent) exists anywhere in the
  response to let a caller tell them apart.

## 3. Mechanism (file:line, read directly)

`platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, function `fetchGocharaSweep`
(declared line 274, body 279–352). The query that selects candidate windows (lines 316–333):

```ts
    const res = await query<{ ... }>(
      `SELECT w.event_class, w.temporal_shape, w.window_start, w.window_end, w.peak_date,
              w.valence, w.is_adverse
         FROM kala_gochara_windows w
         JOIN brahma_event_ontology eo ON eo.event_class_id = w.event_class
        WHERE w.chart_id = $1 AND eo.domain = $2
          AND w.window_end >= $3 AND w.window_start <= $4
          AND w.generation = COALESCE(
                (SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = w.chart_id),
                'v1')
        ORDER BY ABS(w.signed_intensity) DESC NULLS LAST
        LIMIT 200`,
      [chart_id, signal_domain, start, end],
    )
    out.upcoming_window_count = res.rows.length
    ...
    out.windows = res.rows.slice(0, 5).map(r => ({
      event_class: r.event_class, temporal_shape: r.temporal_shape,
      window_start: r.window_start, window_end: r.window_end,
      peak_date: r.peak_date, valence: r.valence, is_adverse: r.is_adverse,
    }))
```

`$3`/`$4` are `start`/`end` (`start = as_of_date`, `end = as_of_date + horizon_years`, lines
280–283). The `WHERE` clause is a pure **interval-overlap** test —
`window_end >= start AND window_start <= end` — which is satisfied by any window whose
`[window_start, window_end]` span crosses the query horizon at all, **including a window whose
`peak_date` already occurred before `start`**, as long as the window's own `window_end` (here
`2034-01-30`, a multi-year interval) still extends past `start`. Rows are then ranked purely by
`ABS(signed_intensity)` and the top 5 become `out.windows` (line 339) — again with no reference to
`peak_date` vs `start` anywhere in the ranking or selection. `out.upcoming_window_count` (line 334,
naming it "upcoming") is simply `res.rows.length` — the raw overlap-match count, not a count of
windows whose peak is actually ahead of now.

The call site, `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:1092`, invokes
`fetchGocharaSweep(chart_id, spec.signal_domain, as_of_date)` and assembles the served block
verbatim at lines 1186–1192 (`gochara_sweep: { ..., top_windows: gochara.windows }`) — no
additional peak-vs-now filtering or flagging is added at the call site either. Confirms C1–C4:
the defect is a pure "does the window's *span* overlap the request range" predicate with no
"has the window's *peak* already occurred" check anywhere in the pipeline.

## 4. Sibling census

`fetchGocharaSweep` is a single shared function (`reading_checklist.ts`); every caller inherits the
identical defect:

| Call site | Tool | Same defect present? |
|---|---|---|
| `register_d9_judgment.ts:1092` | `judgment_query` (`gochara_sweep`) | **YES — this finding (F-134).** |
| `register_d8_assess_domain.ts:1059` | `assess_wealth` / `assess_marriage` / `assess_career` / `assess_health` (via `register_d8_assess_domain.ts`'s domain dispatch) | **YES — genuine sibling, same shared function, same call shape** (`fetchGocharaSweep(chart_id, t5SignalDomain, today)`). Not yet in the manifest as its own finding — every `assess_*` call's `gochara_sweep` section (if present in that response shape) carries the identical already-peaked-window-unflagged risk. Not independently re-reproduced live in this pass (out of the two `reproduce_cmd`s assigned to this lane), but the code path is byte-identical. |

`grep` confirms these are the only two importers of `fetchGocharaSweep` under
`platform/src/lib/retrieval/registry/layers/` — no third call site exists.

## 5. Blast radius

- **Lease conflict — this mechanism is NOT in S3's OWNS list.** S3 (SATYA) owns
  `platform/src/lib/retrieval/registry/layers/L4_phala/**`, `L5_mimamsa/**`,
  `platform/python-sidecar/services/ph_nimitta/**`,
  `platform/python-sidecar/brahmagyan/phala/muhurta.py`. The actual defect site,
  `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, sits directly under
  `layers/` — **not** under `L4_phala/` or `L5_mimamsa/`, **not** under `kala_views/` (the
  S2/S4 split in plan §2.1), and **not** `registry_bridge.ts`/`response_budget.ts` (S2's HOT
  files). Likewise the call site, `register_d9_judgment.ts` (and its sibling
  `register_d8_assess_domain.ts`), is not named in any of the six streams' explicit path globs in
  plan §2.
- This mechanism is genuinely **unclaimed** by the current lease map — it is plausibly closest in
  spirit to S4 VĀCA's domain ("narration/template composers... the v3 register/reading_contract
  glossing module") since `register_d9_judgment.ts` is the v3-envelope judgment tool, but
  `reading_checklist.ts`/`fetchGocharaSweep` is a data-selection predicate, not narration — it
  could equally be read as adjacent to S2 MĀTRĀ's "measure" domain given `upcoming_window_count`
  is a count field. **This diagnosis does not assume S3 may edit it.** Per plan §2.1's rule, this
  lane should post `PAR-F-134-NEEDS-LEASE platform/src/lib/retrieval/registry/layers/
  reading_checklist.ts` (and note the `register_d9_judgment.ts` / `register_d8_assess_domain.ts`
  call sites) for the conductor to resolve — either grant S3 a scoped lease for this one predicate,
  or route the spec to whichever stream the conductor assigns.
- Both `judgment_query` (S3's `reproduce_cmd`) and every `assess_*` domain call inherit the fix
  once it lands in `reading_checklist.ts` — a single-file, two-call-site fix, `assess_*` inheriting
  for free (matches the plan's "exemplar-then-replicate" cost lever noted for other CL classes).
- CL-00 controls: not exhaustively checked in this D-stage window; no known CL-00 control was found
  asserting on `gochara_sweep`/`upcoming_window_count` shape in a spot check of governance control
  headings, but a full census was out of scope for this pass — flag for Stage S.
- No other S3 lane (F-31, F-33, F-35, F-78, F-126) touches `reading_checklist.ts` or
  `register_d9_judgment.ts`/`register_d8_assess_domain.ts` — confirmed via grep, no internal
  collision within S3's own board.

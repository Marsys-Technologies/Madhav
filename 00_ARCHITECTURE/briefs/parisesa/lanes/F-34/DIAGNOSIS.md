---
lane: F-34
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE, exemplar for CL-13
author: SATYA-LEAD (sonnet)
---

# F-34 — gochara_forecast_get partial-horizon truncation not disclosed

## 1. Live reproduction (today, 2026-08-16, re-verified)

`gochara_forecast_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, date_range={start:'2083-06-01', end:'2085-06-01'})`

Result (raw JSON saved by the MCP harness; salient fields):
- `provenance_envelope.window_count` = 22 (`windows[]` served page = 10 after budget trim)
- All served windows have `window_end = 2084-01-31`, `era_slice_key = 'g3_2074_2084'`
- `provenance_envelope.empty_reason = null`
- `provenance_envelope.resolution_breakdown = {era: 9, month: 0, day: 0, unclassified: 13}`

The query asked for 2083-06-01..2085-06-01 (24 months). The sweep has only materialized
through era slice `g3_2074_2084` (ends 2084-01-31) for this event-class set — roughly the
back **16 months of the 24-month request (2084-02-01..2085-06-01) are structurally unswept**,
and nothing in the response says so. `empty_reason` fires only on total emptiness — CONFIRMED
REPRODUCES exactly as claimed. Not ALREADY-FIXED.

## 2. Claim decomposition

The finding's claim decomposes into two sub-claims:
- **C1** — the tool silently truncates at the swept horizon when a query partially overlaps it.
- **C2** — the same tool DOES disclose (via `empty_reason`) when the ENTIRE query falls beyond
  the horizon, so the disclosure mechanism exists and works for one case but not the sibling case
  one step short of it (asymmetric honesty).

## 3. Mechanism (file:line, read directly — corrects/refines the audit's pin)

`platform-mcp/src/tools/retrieval/register_gochara_windows.ts`, function
`computeGocharaForecast` (declared line 1605). The empty_reason assignment is at **line 1717**
(audit corpus cited :1429, which is actually `computeGocharaActivation`'s analogous block — same
defect pattern, different function; see §4 sibling census):

```ts
empty_reason: rawRows.length === 0
  ? (ok
      ? 'no kala_gochara_windows rows overlap this date_range/filter combination — honest zero result. ...'
      : `kala_gochara_windows unreachable this call: ${error ?? 'unknown error'}`)
  : null,
```

`rawRows` comes from a plain SQL overlap query (`window_start <= dateRange.end AND window_end >=
dateRange.start`, line ~1647-1649) against `kala_gochara_windows`. There is no comparison anywhere
in `computeGocharaForecast` between `dateRange.end` and `MAX(window_end)` actually returned (or
against `coverage.sweep_completeness` / the chart's swept horizon) — the branch is a pure
`rawRows.length === 0` gate. The moment even one row overlaps the front of the requested range,
`empty_reason` goes permanently `null` regardless of how much of the tail of the range is unswept.

Confirms C1 (mechanism) and C2 (the sibling total-emptiness branch, same file, same shape, DOES
correctly fire — see the `not_covered` early-return at line ~1631-1643 for the domain-absent case,
and the `ok===false` branch for a genuinely unreachable table — proving the disclosure plumbing
exists and is exercised elsewhere in the same function).

## 4. Sibling census (grep across the owning file; same defect class = date-range query +
`rows.length === 0` empty_reason gate with no horizon/coverage check)

| Function | Tool | Takes date_range? | Same defect present? |
|---|---|---|---|
| `computeGocharaForecast` (:1605) | `gochara_forecast_get` | yes | **YES — this finding (F-34)** |
| `computeGocharaElectionAvoidance` (:1854) | `gochara_election_avoidance_get` | yes (`dateRange` param, same shape) | **YES — genuine sibling.** `empty_reason` gate at line ~2044 is byte-identical in structure: `rows.length === 0 ? (...) : null`, no horizon check. Not yet in the manifest as its own finding — flagging as the "possible seventh" the plan anticipated. |
| `computeGocharaActivation` (:1334) | `gochara_activation_get` | **no** — takes a single `date` (point-in-time "is this active today"), not a range | Excluded with reason: a point query has no partial-overlap-with-horizon case to disclose (it's binary: swept-for-that-date or not). Its own `empty_reason` gate (line ~1429) is a plain zero-rows check, correct for its shape — worth a coverage-vs-honesty note in SPEC but not the same defect class as C1/C2. |

No other file in the S3 lease (`L4_phala/**`, `L5_mimamsa/**`, `ph_nimitta/**`, `muhurta.py`)
shares this exact `rawRows.length===0` + `dateRange` shape — the other five CL-13 findings
(F-31, F-33, F-35, F-78, F-134) are a shared *design pattern* (disclose degraded/partial service
via a structured field, not narration alone) but each lives in a genuinely different serving file
and needs its own Stage-D mechanism trace; F-34 is the cleanest exemplar because its fix is a pure
predicate change in one function with one directly-adjacent sibling.

## 5. Blast radius

- CL-00 controls: none of the 27 known CL-00 controls assert on `gochara_forecast_get` /
  `gochara_election_avoidance_get` empty_reason shape (checked `platform/scripts/governance/`
  control list headings) — low risk of control regression.
- Other lanes sharing this file: none currently claimed by another stream (file is inside S3's
  lease; S1/S2/S4/S5 leases do not list `register_gochara_windows.ts`).
- `kala_gochara_windows`'s `coverage.sweep_completeness` field (already computed earlier in the
  same request pipeline via `computeGocharaCoverage`) is the natural source of the swept-horizon
  bound — reusing it (rather than a fresh `MAX(window_end)` query) keeps this a zero-new-query fix.

## 6. Exemplar status

This is the CL-13 exemplar (plan §2 S3 OWNS note + §5 parallelism). Recommend: SPEC this lane
first, get REVIEW COMPLETE, then the general predicate — "does the served page fall short of the
requested range/date/depth, and if so say so structurally, not just when the result is totally
empty" — becomes the reference pattern the other five CL-13 lanes (F-31, F-33, F-35, F-78, F-134)
adapt to their own file/field shape. F-34 also directly earns a second beneficiary at zero extra
diagnosis cost: `computeGocharaElectionAvoidance`.

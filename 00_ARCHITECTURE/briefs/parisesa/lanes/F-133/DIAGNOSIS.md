---
artifact: F-133_DIAGNOSIS
lane: F-133
stream: S5 MULA
class: CL-03 (missing horizon/date predicate — variant of no-op params)
severity: TIER3-EXPERIENCE
status: CONFIRMED-LIVE
updated: 2026-08-16
---

# F-133 — DIAGNOSIS: `phala_outlook_get` mitigations are not horizon-scoped (anchors are)

## 1. Live reproduction

Called `mcp__marsys-jis-direct__phala_outlook_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa', horizon_months:18})`.
Raw JSON (trimmed to the load-bearing fields) saved to `lanes/F-133/repro_raw.json`.

`query_window` returned: `{start: 2026-08-16, end: 2028-02-07}` (matches horizon_months=18 from today).

**anchors[]** (5 served, of 27 total per `trim_report` — hard-capped, not a windowing bug):
every anchor's `window.{start,end}` overlaps `query_window`. Confirmed correctly scoped.

**mitigations[]** (10 served, of 100 total per `trim_report`): checked every `window_start` /
`window_end` against `query_window` [2026-08-16, 2028-02-07] and against the native's birth date
(1984-02-05):

| mitigation_id (short) | obstruction_id | window_start | window_end | overlaps query_window? |
|---|---|---|---|---|
| 9877c64a | 32491 | 2022-07-12 | 2024-12-25 | NO |
| 25307b6d | 32608 | 1996-02-16 | 1998-08-01 | NO |
| 61c1d01d | 32584 | 1995-06-02 | 1997-11-14 | NO |
| f433e590 | 32586 | 1996-02-16 | 1998-08-01 | NO |
| d1b43d85 | 32604 | 2022-07-12 | 2024-12-25 | NO |
| 00db03db | 32529 | 2025-03-29 | 2027-09-12 | yes |
| **47e7fcdf** | **32489** | **1966-04-08** | **1968-09-21** | **NO — predates native's 1984-02-05 birth by ~17.8 years** |
| 5ed8845a | 32581 | 1993-10-15 | 1996-03-29 | NO |
| f0c447d9 | 32487 | 1996-02-16 | 1998-08-01 | NO |
| aa3cad77 | 32545 | 2025-03-29 | 2027-09-12 | yes |

**Only 2 of the 10 served mitigation rows actually overlap the requested 18-month horizon.**
Row `47e7fcdf-...` (obstruction_id 32489) carries `window_start: 1966-04-08` — 18 years before the
native's own birth (1984-02-05) — the exact case the audit finding names, independently
reproduced live. **Verdict: CONFIRMED-LIVE. Not already fixed.**

## 2. Claim decomposition

| # | Assertion | Verified |
|---|---|---|
| a | Anchors ARE correctly horizon-scoped | **TRUE** — live: all 5 served anchor windows overlap `query_window`. Mechanism confirmed in code (§3): `anchors.py::event_anchors()` applies a real overlap predicate driven by the caller's `date_range`. |
| b | Mitigations are NOT horizon-scoped | **TRUE** — live: 8/10 served rows fall entirely outside `query_window`; mechanism confirmed in code (§3): `mitigation_map()` has no date/window parameter at all, in the function signature or the SQL. |
| c | Some served rows predate the native's birth entirely | **TRUE** — row `47e7fcdf-...` / obstruction_id 32489, window 1966-04-08→1968-09-21, vs. birth 1984-02-05. |
| d | No disclosure/flag explains the mismatch | **TRUE** — see §3; the PH-4-2 `layer_provenance` block carries no horizon/date_range field, no per-row flag, and `judgment`-style out-of-horizon marker exists nowhere in the mitigations array. The one adjacent signal, `trim_report[mitigations].recover_via.hint`, actively claims a caller can "call again with a narrower... date_range" to reach more mitigations — **this is false**; `mitigation_map()` accepts no such parameter (see §3), so the hint promises a recovery path that does not exist. |

## 3. Mechanism (file:line)

**Live serving path** (traced end-to-end, not assumed): MCP tool `phala_outlook_get` →
`platform-mcp/src/tools/register_p1_aliases.ts:1781-1803` (alias, forwards `horizon_months`
correctly — see §5) → `callSidecarPath('/api/compute/phala/outlook', {chart_id, horizon_months})`
→ Python sidecar FastAPI route in `platform/python-sidecar/brahmagyan/phala/outlook.py`
(`@router.post("/phala/outlook")`, backed by `phala_outlook()`). Confirmed this is the file actually
live — its `provenance_envelope.asset_version` (`"1.0"`), `layers` list
(`["PH-4-1","PH-4-2","PH-4-3","PH-4-4"]`), and per-layer provenance shapes match the live response
byte-for-byte; the newer `l4_outlook.py`/`l4_mitigation.py` (`PH-4-5-V2`, different response shape
— `active_anchors`/`active_mitigations`) is NOT what's being served to this tool.

**PH-4-2 mitigations — the defect** — `platform/python-sidecar/brahmagyan/phala/outlook.py:142-170`
(`_fetch_mitigations`):
```python
def _fetch_mitigations(chart_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ...
    from brahmagyan.phala.mitigation import mitigation_map
    db_url = _get_db_url()
    conn = psycopg2.connect(db_url)
    try:
        result = mitigation_map(conn, chart_id)   # <-- no date_range / horizon arg passed
    finally:
        conn.close()
    ...
```
Contrast with `_fetch_anchors` (lines 115-139) two functions above it, which is called as
`event_anchors(chart_id=chart_id, date_range=date_range, min_confidence=min_confidence)` —
`date_range` is computed once at line 428-431 of `phala_outlook()` and threaded into the anchors
fetch, but the mitigations fetch never receives it. This is not a wiring slip that could be
one-line-patched by adding an argument to the *call site* — `mitigation_map()` itself has no
parameter to receive it (below).

`platform/python-sidecar/brahmagyan/phala/mitigation.py:700-849` (`mitigation_map`):
```python
def mitigation_map(
    conn,
    chart_id: str,
    anchor_id: Optional[str] = None,
    mitigation_type: Optional[str] = None,  # ACCEPTED BUT NOT APPLIED — see docstring (P5 fix)
    limit: int = 100,
) -> dict:
    ...
    conditions = ["chart_id = %s"]
    params: list = [chart_id]
    if anchor_id:
        conditions.append("linked_anchor_id = %s")
        params.append(anchor_id)
    where = " AND ".join(conditions)
    ...
    cur.execute(f"""
        SELECT mitigation_id, linked_anchor_id, obstruction_id, ...,
               window_start, window_end, re_evaluation_date, ...
        FROM phala_mitigation
        WHERE {where}
        ORDER BY obstruction_severity DESC NULLS LAST, linked_anchor_id
        LIMIT %s
        """, params + [limit])
```
No `date`, `horizon`, `window_start`, or `window_end` predicate exists anywhere in this function —
not unapplied-but-declared (like the `mitigation_type` param, whose docstring at least documents
the no-op), but structurally absent from the signature entirely. `window_start`/`window_end` ARE
selected columns (so the data needed to filter is right there in the row) — they're just never
used in the `WHERE` clause. The `ORDER BY obstruction_severity DESC NULLS LAST, linked_anchor_id`
is a pure severity/id sort with zero temporal awareness, so which of the 100 rows land in the
first 10 (before the MCP-layer trim to `kept_count:10`, visible in `trim_report`) is essentially
arbitrary with respect to the requested horizon — explaining why 1966/1993/1995/1996-dated rows
outrank 2026-2028 rows that would actually answer "what mitigations apply to my next 18 months."

**PH-4-1 anchors — contrast, confirmed correctly windowed** —
`platform/python-sidecar/brahmagyan/phala/anchors.py` (`event_anchors`, ~lines 129-231):
```python
# Overlap condition: window_start <= range_end AND window_end >= range_start.
...
conditions.extend([
    "window_start <= %s",
    "window_end >= %s",
])
...
WHERE {where}
ORDER BY window_start ASC, COALESCE(posterior, (confidence_low + confidence_high) / 2.0, 0.0) DESC
```
`event_anchors(chart_id, date_range, min_confidence?)` takes `date_range` as a required parameter
and applies the standard interval-overlap predicate before any `ORDER BY`/`LIMIT` trimming. This is
exactly the shape PH-4-2 lacks.

**No disclosure anywhere in the response.** The `layer_provenances.PH-4-2` block in the live
response (`repro_raw.json`) contains only: `chart_id`, `anchor_id_filter`,
`mitigation_type_filter_requested/applied/note`, `asset`, `asset_version`, `build_tag`, `source`,
`computed_at`. No `horizon_months`, `date_range`, or `out_of_horizon_count` field — compare to the
PH-4-1 (anchors) provenance block and to PH-4-4 (`auspicious_windows`, which correctly carries
`date_range` in its own provenance, confirmed live). The generic MCP-layer `trim_report` entry for
`mitigations` is the only place a caller could be tipped off something was cut, and its
`recover_via.hint` ("narrower filter/date_range") is itself wrong for this array (§2d).

## 4. Sibling census

Grepped `platform/src/lib/retrieval/registry/layers/L4_phala/**` and the Python
`platform/python-sidecar/brahmagyan/phala/**` for other "top N of M, unwindowed" trim patterns:

- **`platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts:330-424`**
  (`queryRemedyProgramCapability`, backs the standalone `phala_mitigation_get` / `query_remedy_program`
  MCP tool) — **same table (`phala_mitigation`), same defect shape**: no date/window predicate,
  `ORDER BY obstruction_severity DESC NULLS LAST, intensity_tier`, bounded by
  `MITIGATION_MAX_LIMIT=50`. This is the exact file **F-08's diagnosis already flagged**
  (`PAR-F-08-NEEDS-LEASE query_phala_calibration.ts`, `LEDGER_S5.md` heartbeat T0+~6min) for a
  different param (`domain`) on the same capability — reinforcing that this file carries more than
  one undisclosed-scoping defect. One meaningful difference: this sibling **does** honestly disclose
  `total_matching` / `more_available` pagination metadata, unlike the outlook.py composite path,
  which silently drops 90 of 100 rows behind a generic (and here misleading) `trim_report` hint.
- **`platform/src/lib/retrieval/registry/layers/L4_phala/query_prospective_ledger.ts:~175-183`**
  (prospective-ledger query) — `WHERE p.chart_id = $1 AND p.lifecycle_status = $2`, `ORDER BY
  p.as_of DESC LIMIT $3` — no date/horizon predicate at all. Same defect shape, different
  table/capability; not independently reproduced live (out of this lane's scope) but flagged for
  the CL-03 harness census.
- **`platform/src/lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts`** — has a
  `horizon_tier` filter (categorical: near/mid/far) and returns `window_start`/`window_end`, but
  the filter is categorical, not a true date-range overlap predicate. Softer/different shape than
  mitigations' total absence of any temporal predicate — flagged, not claimed as the same defect.
- **PH-4-4 (`_fetch_auspicious_windows`, `outlook.py:241-368`)** — checked for comparison, confirmed
  correctly windowed (`WHERE date BETWEEN %s::date AND %s::date` bound to the same `date_range`
  computed in `phala_outlook()`). Not a sibling defect.
- **`muhurta.py::fetch_muhurta_windows`** (line ~622-667) has an unrelated `ORDER BY
  auspiciousness_score DESC LIMIT %s`, but its caller `muhurta_finder()` requires `date_range` as a
  parameter and validates it (max 90 days) before this query runs — not a sibling of this defect.

## 5. Blast radius — two fix shapes, both need a lease

**(i) CL-03 shape — missing horizon predicate on mitigations.**
Fix point is `platform/python-sidecar/brahmagyan/phala/mitigation.py::mitigation_map()` (add a
`date_range`/`window_start`/`window_end` overlap predicate mirroring `anchors.py`, likely alongside
a real `ORDER BY` that puts in-horizon rows first) plus threading `date_range` through
`outlook.py::_fetch_mitigations()` and its one call site in `phala_outlook()`
(`outlook.py:439` `mitigations, mitigations_prov = _fetch_mitigations(chart_id)`).

**S5's own forwarding half is verified clean, not a fix target.** The MCP alias
`register_p1_aliases.ts:1781-1803` (`phala_outlook_get`) is in S5's `OWNS` list and DOES correctly
forward `horizon_months` to the sidecar (`callSidecarPath('/api/compute/phala/outlook', {chart_id,
horizon_months: horizon_months ?? 12})`) — confirmed by reading it directly, no defect there. So
unlike F-06/F-08, S5 has **no actionable half** of the CL-03 fix itself: the break is one hop past
the alias, entirely inside `platform/python-sidecar/brahmagyan/phala/**`, which is not in S5's
`OWNS` list (`register_p1_aliases.ts`, `register_p1_synthesis.ts`, `L0_*`, `L1_ganita/**`,
`L2_bodha/**`). This mirrors F-08's precedent exactly (same L4 Phala family, `query_phala_calibration.ts`
already flagged `PAR-F-08-NEEDS-LEASE` for S3).

**(ii) CL-13 shape — no disclosure that mitigations are unfiltered / may fall outside the horizon.**
Fix point is the same files: `outlook.py`'s assembly of `layer_provenances.PH-4-2` (needs a
`date_range`/`out_of_horizon_count`/similar flag) and, per §4, the same gap likely exists on the
sibling `query_phala_calibration.ts` capability. This is the disclosure-shape defect the task
brief pre-identifies as S3's CL-13 territory.

**Raising `PAR-F-133-NEEDS-LEASE`**: both the CL-03 half and the CL-13 half of this finding require
a lease S5 does not hold — `platform/python-sidecar/brahmagyan/phala/{outlook.py,mitigation.py}`
(Python sidecar L4 Phala) and its TS sibling `L4_phala/query_phala_calibration.ts` (already under
S3's territory per F-08 precedent). No code touched in this diagnosis; documents only per this
lane's contract. Recommend the spec stage bundle F-133's mitigation-windowing fix with F-08's
`query_phala_calibration.ts` fix (§4 sibling) since they share the root table and defect shape —
one spec, two call sites, one lease request to S3.

**Bonus, worth a line item for the fix spec:** the `trim_report[mitigations].recover_via.hint`
text itself is now a confirmed-false claim ("call again with a narrower... date_range") and should
either be corrected (mitigation-specific hint text) or suppressed for arrays whose underlying
query has no date_range parameter — a small honesty fix, independent of whether the windowing fix
lands in the same pass.

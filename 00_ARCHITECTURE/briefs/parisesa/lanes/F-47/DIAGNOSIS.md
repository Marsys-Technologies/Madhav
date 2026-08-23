---
lane: F-47
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE
author: SATYA-LEAD (sonnet)
cross_reference: F-48 (same file, same function neighborhood, same underlying engine
  muhurta.py — the two findings will very likely become ONE SPEC at Stage S, since F-48's
  `_transit_quality_for_window` is one of the two action_type-blind sub-scores this finding
  (F-47) names. Diagnosed together in one read pass; filed as two documents per plan §3
  because they carry separate finding IDs and separate claim texts.)
---

# F-47 — kala_muhurta_get / kala_elect_get: 50% of the composite score is domain-blind
(class CL-09, earned signal)

## 1. Live reproduction (today, 2026-08-16, re-verified)

Called `kala_muhurta_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, start_date=2026-08-15,
end_date=2026-09-14)` three times, once per `activity_type` (`business`, `marriage`,
`medical`). Raw JSON for all three calls captured in this turn's tool output (not re-saved to
disk separately — the MCP call itself is the raw evidence; reproducible verbatim with the
`reproduce_cmd` above).

**Top-ranked window is identical across all three domains:**

| activity_type | top window | composite score | `dasha_quality` | `transit_quality` | `panchanga_quality` | `signal_activation` |
|---|---|---|---|---|---|---|
| business | 2026-08-19 → 2026-08-21 | 0.632 | 0.72 | 0.65 | 0.535 | 0.72 |
| marriage | 2026-08-19 → 2026-08-21 | 0.680 | 0.72 | 0.65 | 0.680 | 0.62 |
| medical  | 2026-08-19 → 2026-08-21 | 0.622 | 0.72 | 0.65 | 0.570 | 0.48 |

Same window (2026-08-19T00:00→2026-08-21T00:00) ranks #1 for business, marriage, AND medical,
exactly as the claim states — the composite scores differ (0.632 / 0.680 / 0.622) purely
because `panchanga_quality` and `signal_activation` vary by domain while `dasha_quality` and
`transit_quality` do not.

**`dasha_quality` = 0.72 in every single window of every domain**, across the full 15-window,
30-day, 3-domain sample (45 window-instances total) — CONFIRMED verbatim as the claim states.
Every window in the query range falls in 2026, and `_dasha_quality_for_chart`'s native-chart
branch returns a flat `0.72` for any `window_start.year` in `[2026, 2043]` regardless of
`action_type` (§3 below) — so the invariance is total, not approximate.

**`transit_quality` is also invariant across domains for the same calendar window** (e.g. the
2026-08-19 window: 0.65 in the business call, 0.65 in the marriage call, 0.65 in the medical
call — every window-date pairs identically across all three calls, since the same
`window_start` produces the same lunar-phase/day-of-week arithmetic regardless of
`activity_type`).

By contrast `panchanga_quality` and `signal_activation` visibly differ per domain for the
identical window/date (panchanga_quality: 0.535/0.680/0.570; signal_activation: 0.72/0.62/0.48
for business/marriage/medical respectively) — confirming the claim's contrast that these two
sub-scores ARE domain-sensitive while the other two are not.

CONFIRMED REPRODUCES exactly as claimed. Not ALREADY-FIXED.

## 2. Claim decomposition

- **C1** — `kala_elect_get` and `kala_muhurta_get` share one underlying scoring engine
  (PH-4-4 / `muhurta.py`). Verified in §4 below (sibling census / shared-engine trace):
  both tools route through `platform-mcp/src/tools/muhurta_finder.ts` (`kala_elect_get` via
  `kala_views/elect.ts`'s `handleMuhurtaFinder` import, `kala_muhurta_get` as a registered
  alias of the same tool — see the tool's own description: "same as muhurta_finder") →
  `/api/compute/muhurat` → `brahmagyan/phala/muhurta.py:generate_muhurta_windows`. One engine,
  confirmed, not inferred.
- **C2** — 50% of the composite score (`dasha_quality` 30% + `transit_quality` 20%) is
  computed with NO `action_type`/undertaking parameter at all. Verified in §3 — both
  functions' signatures take no `action_type` argument, and both call sites pass none.
- **C3** — Only `panchanga_quality` (40%) and `signal_activation` (10%) are genuinely
  domain-sensitive. Verified in §3 (signatures) and §1 (live values differ by domain for the
  identical window).
- **C4** — Not F-10's total domain-blindness — a *partial* one: the same top-ranked window
  came out #1 for business, marriage, AND medical in this reproduction, differing only in
  numeric score. Verified exactly in §1's table — same window, three different scores, same
  rank.

## 3. Mechanism (file:line, read directly)

`platform/python-sidecar/brahmagyan/phala/muhurta.py`:

**Action-blind (the defect):**
```python
# line 372
def _dasha_quality_for_chart(chart_id: str, window_start: datetime) -> float:
    ...
    if chart_id == NATIVE_CHART_ID:
        year = window_start.year
        if 2026 <= year <= 2043:
            return 0.72          # flat, regardless of action_type
        return 0.55
    ...
```
```python
# line 420
def _transit_quality_for_window(window_start: datetime) -> float:
    """
    Approximate transit quality based on known planetary cycles.
    ...
    """
    # lunar-phase + day-of-week arithmetic only; no action_type parameter exists
    ...
```
Neither function's signature accepts `action_type`. Call sites, `generate_muhurta_windows`
(the function every window is built from):
```python
# line 814 — dasha_q, action-blind
dasha_q = _dasha_quality_for_chart(chart_id, range_start)
# line 815 — signal_q, action-AWARE (see §3 contrast below) — refines the audit's bundled
# "814-815/858" citation: only line 814 is the action-blind CL-09 defect; line 815 is
# already correct (action_type-aware) and belongs in the contrast column, not the defect.
signal_q = _signal_activation_for_action(action_type, chart_id)
...
# line 858 — transit_q, action-blind
transit_q = _transit_quality_for_window(current)
```
`dasha_q` and `signal_q` are computed once per `generate_muhurta_windows` call (chart-level,
"constant across windows" per the function's own comment at line 813) and reused unchanged
for every window in the date range; `transit_q` is recomputed per-window from `current` (the
window's date) but never from `action_type`.

**Contrast (domain-sensitive, correct pattern — confirms the plumbing exists and is used
elsewhere in the same file):**
```python
# line 231
def _panchanga_quality_for_action(
    tithi_name: str, vara_lord: str, moon_nakshatra: str, yoga: str,
    action_type: str,                                    # ← takes it
) -> float:
    ...
    if action_type == "marriage": ...
    elif action_type == "education": ...
    elif action_type == "business": ...                  # genuinely branches per domain
```
```python
# line 468
def _signal_activation_for_action(action_type: str, chart_id: str) -> float:
    ...
    _NATIVE_SIGNALS: dict[str, float] = {
        "education": 0.78, "business": 0.72, "marriage": 0.62,
        "travel": 0.60, "medical": 0.48, "property": 0.55, "general": 0.60,
    }
    if chart_id == NATIVE_CHART_ID:
        return _NATIVE_SIGNALS.get(action_type, 0.55)     # genuinely branches per domain
```
Composite assembly, `compute_muhurta_score` (line 202) and its weights (lines 70-73):
```python
WEIGHT_PANCHANGA = 0.40
WEIGHT_DASHA = 0.30      # ← action-blind input
WEIGHT_TRANSIT = 0.20    # ← action-blind input
WEIGHT_SIGNAL = 0.10
```
`0.30 + 0.20 = 0.50` — exactly the "50%" the claim states.

**Line-number correction to the audit's mechanism pin:** the original pin (`:372`, `:420`,
called at `:814-815/858`, contrasted with `:231`/`:468`) is confirmed accurate at every
individually-cited line number in the current file — no drift. The one refinement: `:814-815`
bundles two calls of different character (814 = `dasha_q`, action-blind; 815 = `signal_q`,
action-AWARE) as if both were part of the defect; only 814 is. This is noted for the SPEC
stage so the fix does not mistakenly touch `_signal_activation_for_action`'s call site, which
is already correct.

## 4. Sibling census

Grepped `platform/python-sidecar/brahmagyan/phala/muhurta.py` for every `def` (20 functions
total; full list captured via `grep -n "^def "`). Of the four sub-score functions:

| Function | Line | Takes `action_type`? | Domain-sensitive? |
|---|---|---|---|
| `_panchanga_quality_for_action` | 231 | yes | yes — confirmed live (§1) |
| `_dasha_quality_for_chart` | 372 | **no** | **no — this finding's defect** |
| `_transit_quality_for_window` | 420 | **no** | **no — shared defect, see F-48** |
| `_signal_activation_for_action` | 468 | yes | yes — confirmed live (§1) |

No third action-blind scoring function exists in this file — the census is exhaustive for
`muhurta.py`'s own scoring engine (all `def`s beginning `_.*_quality`/`_.*_for_` are the four
above; `_current_dasha_lords`/`_dasha_citation_fragment*`/`_tara_bala_*`/`_fetch_*` are
citation/gating helpers, not scoring inputs, and are out of scope for CL-09).

**Shared-engine confirmation (grep across `platform-mcp/src/tools/`):** both
`kala_elect_get` (`kala_views/elect.ts` imports `handleMuhurtaFinder` from
`../muhurta_finder.js`, comment at `elect.ts:7`: "already computes...") and
`kala_muhurta_get` (registered as a direct alias of the `muhurta_finder` tool — see the tool's
own MCP description: "same as muhurta_finder") both resolve to
`platform-mcp/src/tools/muhurta_finder.ts`, which per its own header comment (lines 32-34)
delegates `MCP tool → callPlatformPrimitive('muhurta_finder', params) →
/api/mcp/primitives/muhurta_finder (platform) → query_muhurat retrieval tool → sidecar POST
/api/compute/muhurat (Phase 4C-6 muhurat router)` — i.e. this exact `muhurta.py` module. One
engine confirmed by direct trace, not asserted.

No other file in the S3 lease (`L4_phala/**`, `L5_mimamsa/**`, `ph_nimitta/**`) implements a
second, independent muhurta-scoring path — `elect.ts` and `ritual.ts`/`now.ts` etc. are
presentation-layer composers over the one `muhurta_finder.ts` → `muhurta.py` call, not
alternate engines.

## 5. Blast radius

- **CL-00 controls:** none of the known CL-00 controls assert on `muhurta_finder` /
  `kala_muhurta_get` / `kala_elect_get`'s per-factor domain-sensitivity — no control
  regression risk from a fix here.
- **F-48 (this same stream, this same file):** `_transit_quality_for_window` (line 420) is
  simultaneously the mechanism for F-48 (no real transit computation — a lunar-phase +
  day-of-week approximation) and one of the two action-blind sub-scores this finding (F-47)
  names. A fix to F-47 that adds `action_type`-sensitivity to `_transit_quality_for_window`
  would touch the exact function F-48 also targets — **these two lanes should be specced
  together or in an explicitly ordered sequence** (F-48's fix — disclose or replace the
  approximation — should land first or in the same change, since F-47's remedy for the
  transit half of its defect is downstream of what F-48 decides transit_quality should even
  be).
- **`_dasha_quality_for_chart`'s own separate issue (out of this finding's scope but adjacent):**
  the native-chart branch (line 383-390) is itself a hardcoded FORENSIC-citation shortcut
  (`0.72` for any 2026-2043 window) rather than a live `chart_dashas` lookup — the non-native
  branch (line 392-417) does query `chart_facts` for `current_md_lord`. This is a separate,
  not-yet-filed observation (native chart gets the same flat 0.72 the docstring claims is
  FORENSIC-grounded, but never re-derives it per-window the way the non-native path
  structurally could) — noted for SPEC awareness, not part of C1-C4.
- **Other lanes sharing this file:** F-48 (this stream, confirmed above). No S1/S2/S4/S5
  lease lists `muhurta.py`.

## 6. Note for SPEC stage

Per the plan's PRATINIDHI standing rule ("when two remediations are defensible, choose the
one that discloses more"), two remediations are defensible for C2/C3 and are flagged here,
not resolved:
1. **Compute a real domain-sensitive signal** for `dasha_quality` (e.g. weight dasha lord's
   classical significations against the requested `action_type` — the file already has the
   pattern via `_signal_activation_for_action`'s `_NATIVE_SIGNALS` dict) and for
   `transit_quality` (contingent on F-48's resolution of what transit_quality should compute
   at all).
2. **Disclose the domain-blindness structurally** — surface a `factor_domain_sensitivity` or
   equivalent field per window (e.g. `{"dasha_quality": {"domain_aware": false}, ...}`) so a
   caller can see which 50% of the composite score did not vary by their `action_type`,
   without necessarily re-deriving those sub-scores yet.
This fork is explicitly NOT resolved in this diagnosis — it is Stage S's decision, informed by
F-48's own fork (same two options, same standing rule) since the two lanes share
`_transit_quality_for_window`.

---
artifact: KALA_PROVING_JOURNEYS_BASELINE
version: "1.0"
status: DRAFT — cycle 3 of the KĀLA READINESS AUDIT
produced_by: L3 Kāla readiness audit (autonomous, Claude Code)
produced_on: 2026-09-22
scope: T2 — for each of the three named proving journeys, walk F02's end-to-end path against the
  live system as it is today; identify the first failing boundary (not the last symptom).
method: >
  Produced by one read-only subagent, budget-capped, built on prior-cycle F5/F7/DOMAIN_F/T5.
  Headline finding (asset_throughput showing both writers ran once and their output is now gone)
  independently spot-verified by the conductor via direct DB query before integration — see
  AUDIT_STATE.md cycle 3.
---

# KĀLA PROVING JOURNEYS BASELINE — T2

**Canonical chart:** `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek Mohanty). All DB queries are
read-only aggregates (`count()`, `GROUP BY chart_id`, boolean state lookups); no narrative/
interpretive row content was ever selected.

## F02's exact chain (quoted)

`MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md:29`:

> F02 | Preserve the end-to-end path: question → applicable concept → qualified rule → canonical
> fact → structural relationship → temporal mechanism → manifestation or explicit gap → delivered
> finding → protected evaluation. | Trace with IDs, operators, exact fields, lineage and honest
> gap state.

The first 8 links are the trace scope; "protected evaluation" (the 9th) is the operative link for
Journey 3, where it is folded in as C3 adjudication.

---

## THE HEADLINE FINDING (stated up front — all three journeys converge on it)

`kala_activation` (owned by `ka_kalasutra`) and `kala_convergence` (owned by `ka_sangam`) — the two
tables nearly every L3 "when does X activate" consumer surface reads, directly or by join — have
**zero rows for the canonical chart**, confirmed live and independently re-confirmed by the
conductor:

```sql
SELECT count(*) FROM kala_activation  WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';  -- 0
SELECT count(*) FROM kala_convergence WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';  -- 0
SELECT chart_id, count(*) FROM kala_activation  GROUP BY chart_id ORDER BY 2 DESC;
--  1c826d5a-41cb-4450-b4dc-59d440e5f75a | 336093
--  cb73cd3d-9eba-4220-9902-0de91566e980 |   1055
SELECT chart_id, count(*) FROM kala_convergence GROUP BY chart_id ORDER BY 2 DESC;
--  1c826d5a-41cb-4450-b4dc-59d440e5f75a | 17957
--  cb73cd3d-9eba-4220-9902-0de91566e980 |  2540
```

This corroborates F7 (which already flagged both tables as canonical-chart-empty) but goes one
step further: `asset_throughput` (the orchestrator's own build-state table) shows both writers ran
for the canonical chart and *did* write rows, once:

```sql
SELECT asset_id, state, rows_written, last_built_at, last_error FROM asset_throughput
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id IN ('ka_kalasutra','ka_sangam');
-- ka_kalasutra | stale | 335403 | 2026-08-13 01:15:50+00 | (null)
-- ka_sangam    | stale | 14868  | 2026-08-13 01:07:13+00 | (null)
```

On 2026-08-13 the orchestrator recorded writing 335,403 rows (`ka_kalasutra`→`kala_activation`)
and 14,868 rows (`ka_sangam`→`kala_convergence`) for the canonical chart — figures of the same
order of magnitude as what the *other* charts hold today — yet the live tables now show 0 rows for
this chart. State is honestly `stale` (not falsely `lit`), and `last_error` is null, so nothing in
`asset_throughput` explains the disappearance. Whether this is a mis-scoped delete-then-insert on
a later run for a different chart (a §N.3 idempotency-contract violation — the exact hazard the
per-chart-scoped-delete rule exists to prevent), a deliberate purge, or something else was not
diagnosed within the packet's budget — flagged for a dedicated follow-up. **The present-tense fact
is unambiguous: these two tables are empty for the canonical chart right now.**

Every L3 "temporal mechanism" tool identified by F5/DOMAIN_F ultimately depends on one or both of
these tables:
- `kala_now_get`, `kala_windows_get`, `kala_ahead_get` → `query_temporal_activation` →
  `kala_activation`.
- `kala_priority_get`/`kala_priority_ranking_get` → `call_priority_ranking` → `kala_activation`
  (the `ka_tulana` wrapper reads `ka_kalasutra`'s table, not `ka_tulana`'s own output, compounding
  the emptiness).
- `kala_yoga_activation_get` → `yoga_activation_by_dasha` → joins `bodha_msr_signals` ×
  `kala_activation` directly (traced fresh this packet — see Journey 2).
- The one documented fallback (`kala_windows_get`'s empty-activation fallback → `kala_bhavishya`)
  is *also* empty for the canonical chart (0 rows canonical, 100 rows all on chart `1c826d5a-…`).

**For the canonical chart, the primary path and its one documented fallback are both empty.**

---

## Journey 1: Financial promise and relief

Source: `MADHAV_PRODUCT_DEFINITION_v3_0.md §12.1` + `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md
§12.1`. Chain per VA:394 — L0 rules → L1 positions/conditions/formation/clocks → L2 constructs
resource-creation/retention mechanisms (incl. derived-house relations + counter-evidence) → **L3
searches the same configuration's qualified activation routes** → L4 distinguishes
manifestations/emits forecast → L5 evaluates the claim later.

| F02 step | Status | Evidence |
|---|---|---|
| question | N/A | Product-surface concern, not L3. |
| applicable concept (L0) | Out of scope | L0 sealed per CLAUDE.md §E; not re-verified this pass. |
| qualified rule (L0) | Out of scope | Same. |
| canonical fact (L1) | **PASS** | `chart_dashas` (L1) holds 483,870 rows for the canonical chart; L1 assets closed per CLAUDE.md §E. |
| structural relationship (L2) | Assumed PASS, not re-verified | L2 Bodha `✓ BUILT` per CLAUDE.md §E; out of this L3-scoped audit's direct evidence base this cycle. |
| **temporal mechanism (L3) — FIRST FAILING BOUNDARY** | **FAIL** | `kala_activation` (`ka_kalasutra`) is the table every "which qualified clocks engage" tool reads — **0 rows for the canonical chart**. Its one documented fallback, `kala_bhavishya`, is also 0 rows canonical. Compounding: even where dasha-clock qualification is asked for directly, `call_dasha_eligibility` bypasses `KaDashaKalaService`/`ka_dasha_kala`'s own writer output entirely and queries raw L1 `chart_dashas` instead (F5, confirmed, high confidence). Even setting the empty-table finding aside, the qualification layer VA requires is not the layer actually being served for this call path. |
| manifestation or explicit gap | **Cannot be honestly reached** | VA's "where the manifestation bridge is not qualified, stop at supported activation and identify the missing link" presumes a supported-activation baseline exists to stop at. With `kala_activation` empty, there is no baseline to qualify or gap-report against — the honest state is "no L3 temporal data for this chart," not a graded partial finding. The PACT/promise-gate retention-constraint check (`promise_spine.ts`'s `interpretPactJoin`, confirmed LIVE) is sound machinery but only invoked on the fallback path — which is also empty. |
| delivered finding | Not reached | Downstream of the above. |

**First failing boundary: temporal mechanism, owned by `ka_kalasutra` (`kala_activation`),
compounded by `ka_tulana`/`ka_dasha_kala`'s consumer-side bypasses (F5).**

---

## Journey 2: Named yoga / NBRY

Source: `MADHAV_PRODUCT_DEFINITION_v3_0.md §12.2` + VA §12.1. Requires: formation + cancellation
checked BEFORE searching time (L1/L2); then L3 lists eligible activation routes, closest contact,
better-supported windows, opposing conditions; explicitly warns "a participant's nearest transit
contact is not automatically the activation of the whole configuration."

New trace this packet: `register_p1_aliases.ts:1408-1436` calls
`marsys://tool/L-TIMING/yoga_activation_by_dasha`, implemented at
`register_d8_assess_domain.ts:1787-1916` as `yogaActivationByDashaCapability`.

| F02 step | Status | Evidence |
|---|---|---|
| question | N/A | Product-surface concern. |
| applicable concept / qualified rule (L0) | Out of scope | Same as Journey 1. |
| canonical fact (L1) | Assumed PASS | Formation/dignity facts are L1-closed. |
| structural relationship (L2) — formation + cancellation | Assumed PASS, not re-verified | `bodha_msr_signals` with `signal_type_class='yoga'` is the catalog joined against; NBRY's specific cancellation-condition qualification at L2 not re-checked (out of L3 scope). |
| **temporal mechanism (L3) — FIRST FAILING BOUNDARY** | **FAIL** | `yogaActivationByDashaCapability`'s query joins `bodha_msr_signals m` to `kala_activation ka` on `chart_id`+`signal_id` (`:1885-1916`). With `kala_activation` at 0 rows, this join returns **zero activated yogas for chart 482012f1 regardless of NBRY's formation/cancellation state** — the tool cannot surface an activation window for *any* named yoga on this chart today, not just NBRY specifically. Two already-fixed historical defects are documented in the same code block (R-45 NULL activation dates now handled; WP-S4-fix2 ranking-inflation bug fixed) — evidence the join mechanism has been actively hardened, making the present emptiness more clearly attributable to the missing `kala_activation` build than to residual join-logic bugs. Separately, `ka_sangam`'s `kala_convergence` (0 rows) is the table other "eligible activation route" assets chain from — so the configuration-level convergence search VA calls for is also empty at its source. |
| "nearest transit ≠ whole configuration" safeguard | **COULD NOT VERIFY** | No participant-count/whole-configuration-vs-single-transit distinction found in the join (correlates one `signal_id` to dasha-period overlap only, via `dasha_activation_proximity_score`). Whether this distinction lives elsewhere (inside `bodha_msr_signals`' own construction, or `ka_vighnakara`'s obstruction layer) not traced within budget — flagged, not asserted absent. |
| manifestation or explicit gap | Cannot be honestly reached | Same reasoning as Journey 1 — no activation baseline to grade against. |
| delivered finding | Not reached | Downstream. |

**First failing boundary: temporal mechanism, owned by `ka_kalasutra` (`kala_activation`, read
directly) and `ka_sangam` (`kala_convergence`, feeding the wider "eligible activation routes"
search) — the identical boundary as Journey 1, reached by a different tool.**

---

## Journey 3: Historical challenge

Source: `MADHAV_PRODUCT_DEFINITION_v3_0.md §12.3` + VA §12.1. Requires: an independent event-free
structural/temporal re-analysis, compared against the frozen original claim and admitted
historical log; inspection of non-matching events and unmatched activations; no hindsight leakage;
protected C3 adjudication routed separately from provider-facing explanation.

| F02 step | Status | Evidence |
|---|---|---|
| question | N/A | Product-surface concern. |
| applicable concept / qualified rule (L0) | Out of scope | Same. |
| canonical fact (L1) | Assumed PASS | Same L1-closed basis. |
| structural relationship (L2) | Assumed PASS, not re-verified | Out of L3 scope this cycle. |
| **temporal mechanism (L3) — FIRST FAILING BOUNDARY, same root cause** | **FAIL** | The "independent event-free structural/temporal analysis" and "unmatched activations" inspection both require re-deriving what L3 activation windows existed/exist — the same `kala_activation`/`kala_convergence` substrate as Journeys 1-2, empty for the canonical chart. No live-computed activation set exists to compare against a frozen historical claim; the comparison side (what did activate vs. what was claimed) is starved at the same point. |
| manifestation or explicit gap | Cannot be honestly reached | Same reasoning. |
| delivered finding | Not reached | Downstream. |
| **protected evaluation (9th F02 link, C3 adjudication)** | **COULD NOT VERIFY** | `mimamsa_lel_query`, `mimamsa_outcome_record`, `standing_predictions_read`, `mechanism_retrodiction_get` all exist in the catalogued MCP tool surface, consistent with L5 Mīmāṃsā sealed per CLAUDE.md §E — but none opened/traced this pass (L5's own machinery outside this L3-scoped packet's remit). Whether the L5 side of Journey 3 is independently sound is a separate, un-audited question; this packet only establishes the L3 half it depends on is not currently available. |

**First failing boundary: temporal mechanism, same root cause as Journeys 1 and 2 —
`ka_kalasutra`/`kala_activation` and `ka_sangam`/`kala_convergence` empty for the canonical chart.
Whether L5's separate frozen-claim/adjudication machinery has its own independent defects further
downstream was not assessed.**

---

## Cross-journey pattern

All three proving journeys hit their first failing boundary at **the identical F02 link —
temporal mechanism — for the identical underlying reason**: `kala_activation` (`ka_kalasutra`) and
`kala_convergence` (`ka_sangam`) hold zero rows for the canonical chart, despite being the tables
nearly every L3 "when does X activate" consumer tool reads (directly, by join, or via their one
documented fallback, which is also empty for this chart). `asset_throughput` shows both writers
*did* run for this chart on 2026-08-13 and recorded writing hundreds of thousands of rows
(335,403 / 14,868) — the data existed once and is gone now, `state='stale'`, no `last_error`, an
unexplained discrepancy flagged for follow-up rather than diagnosed here.

**This is not three independent defects; it is one substrate gap that every downstream "when"
tool — across financial-promise timing, yoga activation, and historical-challenge re-derivation
alike — inherits identically.** Journey-specific secondary defects exist beneath this shared floor
(Journey 1's `ka_dasha_kala`/`ka_tulana` consumer-wrapper bypasses; Journey 2's unverified
whole-configuration-vs-single-transit safeguard) but none of them can be observed to matter in
practice for the canonical chart today, because the query never gets past the empty
`kala_activation`/`kala_convergence` floor to exercise them.

**This finding directly corroborates the T1 traceability matrix's independently-derived "wired
orphan capacity" pattern** (`KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md`, Cross-cluster synthesis):
the same two tables, found empty from the asset-obligation side there, are found empty from the
proving-journey side here — two independent audit routes converging on one root cause.

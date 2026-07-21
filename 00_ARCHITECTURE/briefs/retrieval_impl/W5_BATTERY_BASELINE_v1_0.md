---
artifact: W5_BATTERY_BASELINE_v1_0.md
canonical_id: RETRIEVAL_W5_BATTERY_BASELINE
version: 1.0
status: FIRST_BASELINE — not the final V5-gate run (see §6)
type: W5 Lane L10 readback + tool-selection battery + concurrency baseline
  (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md §E W5 / plan §9.7 W-28..W-31)
captured_by: Claude Code (Sonnet 5), lane L10, isolated worktree
captured_at: 2026-07-21
harness: platform/tests/eval/w5_battery/{queries.ts,lib.ts,run_battery.ts,lib.test.ts}
raw_data: 00_ARCHITECTURE/briefs/retrieval_impl/w5_battery_baseline_raw.json
---

# W5 Lane L10 — Readback + Tool-Selection Battery, first baseline

## §1 — What this is, and what it deliberately is not

Master brief §E W5 names this lane's deliverable: "readback + tool-selection battery
built and baselined across families (incl. concurrency runs, W-31)", and the V5 gate
reads "battery scores recorded as the regression baseline; load test passes the four
§9.7 pressure points" (W-28 cache, W-29 concurrency capacity, W-30 QoS/backpressure,
W-31 quality-under-load proof).

**This artifact is that battery's FIRST recorded baseline, captured incrementally
while L5/L6/L7/L9 are still in flight** — the lane brief explicitly authorizes this
("a baseline should be captured incrementally and re-run as more lands... you are not
blocked on the other in-flight lanes"). It is not, and does not claim to be, the final
V5-gate run: §6 below names exactly what changes before that claim can be made.

**Scope boundary honestly kept:** per this lane's `must_not_touch`, no load/concurrency
test was run against the LIVE deployed production connector — that is explicitly the
wave-close V5 gate's job once W5's other lanes (funnel scaling W-29, QoS/backpressure
W-30) are merged. This battery instead runs against the actual production DECISION
LOGIC locally: the deterministic W4 "One Planner" routing path (`classifyScope` →
`compileFloorForPlan` / `compileContractCached`, `platform/src/lib/vidhi/` +
`platform/src/lib/pipeline/compiled_floor_adapter.ts`) — no network, no DB, no LLM
credentials required, fully reproducible in CI. It does NOT exercise live MCP
tool-call latency/throughput under real traffic; that half of "quality-under-load"
needs W-29's funnel/pooling work landed first (see §6).

## §2 — Family list (confirmed from the live registry, not guessed)

The lane brief asked this to be confirmed rather than assumed. Ground truth is
`platform/src/lib/vidhi/registry_data.ts`'s `VIDHI_INTENT_FLOORS` — the same registry
the W4 floor-completeness campaign (STATE.md "W4 CLOSE") brought career/health/marriage
to full `§B0.4` mandatory-tag parity with the wealth flagship floor. Eight floors are
registered; six are domain/breadth/general FAMILIES (this battery's scope) and two
(`structure_read`, `retrieval_only`) are depth/structural variants already covered by
`compiled_floor_adapter.test.ts`'s depth-dimension assertions, not domain families:

| family | compiler `IntentClass` |
|---|---|
| wealth | `wealth_deepdive` (flagship, DOCTRINE_CAMPAIGN_DESIGN §3 worked example) |
| career | `career_deepdive` |
| health | `health_deepdive` |
| marriage | `marriage_deepdive` |
| panoramic | `panoramic_breadth` |
| general | `general_synthesis` (fallback floor) |

This exactly matches career/wealth/health/marriage/panoramic/general as anticipated.

## §3 — Methodology (extends existing infrastructure, does not invent a new pattern)

**Tool-selection scoring** follows the same recall/precision-over-a-labeled-corpus shape
already established by `platform/tests/eval/planner_smoke_runner.ts` (W2-EVAL-B), applied
to the deterministic router instead of the LLM planner — the LLM planner path needs live
model credentials, out of scope for a local battery; the deterministic
`classifyScope`→`compileFloorForPlan` path IS the actual production W4 routing logic and
is fully exercisable without network access. 30 hand-written, natural-language queries (5
per family) were verified LIVE against the actual classifier before being committed to
`queries.ts` — every one routes to its labeled family's `IntentClass` (see raw JSON
`sequential.results[].compiled_intent` vs `.family`).

**"Readback"** ports `BASELINE_PROBES.md`'s own methodology (capture a served artifact's
shape/hash now, diff future runs against it) onto the actual W4/W5 unit of work: the
compiled Vidhi contract (floor + machine_band + completeness receipt), fingerprinted via
a stable-stringify + sha256 hash (`lib.ts` `contractFingerprint`). Calling live MCP tools
against production for a byte-diff is explicitly out of this lane's scope (see §1); the
compiled contract IS the thing W4/W5 actually changed, so it is the correct readback unit
here. Every (query, chart) pair's fingerprint from the sequential pass is the baseline
future runs diff against — see `w5_battery_baseline_raw.json`
`sequential.results[].fingerprint`, 60 entries.

**Concurrency (W-31, local half)**: the same 60 (query × chart) combinations are re-run
in `Promise.all` batches of **N=8** (justification: this repo's own W-28 doc puts the
entire floor-cache keyspace at 48 chart-agnostic cores — 8 intents × 3 depths × 2
intervention — so N=8 concurrent calls is large relative to that keyspace, enough to
force real contention on shared cache entries, while staying small enough to run in
milliseconds as a CI-friendly gate; it also approximates a realistic near-simultaneous
burst from a handful of native/Paripraśna sessions, not a stress-test extreme). Batches
deliberately interleave BOTH chart_ids (`abhisek_canonical` / `abhinandan_safe`) so
concurrent calls for different charts actually overlap the shared W-28
`compileContractCached` cache — this is the exact shape of the LCA-17 cross-chart
substitution failure mode this campaign's docs treat as a standing cautionary tale
(referenced throughout STATE.md/CURRENT_STATE — read for context only, its actual fix is
untouched by this lane per the `must_not_touch` boundary). Every concurrent result's
`chart_isolation_ok` flag asserts no tool_arg-embedded chart_id leaked across charts, and
every concurrent fingerprint is diffed against the sequential baseline (readback).

## §4 — Results (this run, full 60/60, both charts)

Raw data: `w5_battery_baseline_raw.json`. Summary:

| Metric | Sequential | Concurrent (N=8) |
|---|---|---|
| Combos run | 60 | 60 |
| Wall time | 33.43 ms | 19.43 ms |
| Routing accuracy (overall) | **100.0%** (60/60) | 100.0% (60/60) |
| Compile failures | 0 | 0 |
| Chart-isolation violations | — | **0** |
| Readback diffs vs sequential | — | **0** |

Per-family (sequential pass; identical on the concurrent pass — see raw JSON):

| family | n | routing_accuracy | avg_mapped_fraction (web-executable primitives) | avg_dark_count | avg_classifier_confidence |
|---|---|---|---|---|---|
| career | 10 | 100.0% | 11.8% | 4.00 | 0.38 |
| general | 10 | 100.0% | 33.3% | 1.00 | 0.00 |
| health | 10 | 100.0% | **0.0%** | 2.00 | 0.22 |
| marriage | 10 | 100.0% | **0.0%** | 2.00 | 0.34 |
| panoramic | 10 | 100.0% | 20.0% | 3.00 | 0.16 |
| wealth | 10 | 100.0% | 14.3% | 5.00 | 0.36 |

**GATE (this lane's own regression gate, wired into `run_battery.ts`'s exit code):
PASS** — routing_accuracy ≥ 0.90 threshold, zero isolation violations, zero readback
diffs, zero compile failures.

## §5 — Honest findings (not fabricated, read directly off the numbers)

1. **Routing is 100% correct on this labeled corpus, but the classifier's own low-level
   `intent` field is frequently `unknown`/low-confidence even when routing is correct**
   (e.g. `W5B.001`, avg wealth confidence 0.36/1.0). This is not a routing bug: the
   compiler-intent mapping (`classifierIntentToCompilerIntent`) resolves the correct
   family from the `domains` array, independent of the classifier's own 8-value `intent`
   enum guess. Recorded as a genuine baseline characteristic, not smoothed over — a
   future rubric pass should track `avg_confidence` per family alongside routing accuracy
   so a classifier regression that keeps routing correct by domain-luck but degrades
   `intent` confidence doesn't go unnoticed.
2. **`avg_mapped_fraction` quantifies the MCP↔web tool-namespace gap named as a carried
   residual at W4 close, per-family, for the first time.** Health and marriage floors
   currently have **zero** web-executable primitives (`LIVE_TOOL_TO_RETRIEVAL` maps none
   of their floor items to a retrieval-registry tool) — meaning the consult/web channel's
   compiled floor for these two families is presently ALL `unmapped` (MCP-native only).
   Wealth/career/panoramic/general have partial coverage (11.8–33.3%). This is a
   concrete, numeric "before" picture for whichever future lane closes the namespace gap
   (STATE.md names this residual for "W5/PF-1").
3. **Dark-item counts per family** (career avg 4.0, wealth avg 5.0 — the two highest)
   reflect registered `known_gap` CR citations in the floor registry itself, not a
   battery defect — consistent with `registry_data.ts`'s own `known_gap: 'CR-66'`
   wealth-anchor annotation, etc.
4. **Zero chart-isolation violations across 60 concurrent, interleaved-chart compiles**
   confirms the W-28 `compileContractCached` shared-cache design (chart-agnostic
   placeholder + per-call chart_id substitution into a freshly-spread object, never a
   mutated shared reference) holds under this battery's concurrency shape. This is a
   real, executed check, not an assumption — `checkChartIsolation` scans every compiled
   `tool_args` value for a UUID-shaped string that doesn't match the call's own chart_id.

## §6 — What's still needed for the TRUE final V5-gate run

This baseline is honest about being partial:

1. **Re-run once L5 (funnel batching/pooling, W-29), L6 (sidecar memoization/caps),
   L7 (QoS/backpressure, W-30), and L9 (job queue) land** — those lanes are what would
   actually change this battery's latency/throughput numbers under real concurrent load;
   right now the "concurrency" pass measures correctness/isolation of a synchronous,
   in-process compile path, not the full funnel→sidecar→DB round trip.
2. **A genuine production/staging load test against the four §9.7 pressure points**
   (W-28 cache hit-rate under real traffic, W-29 concurrency capacity, W-30
   QoS/backpressure under contention, W-31 SLO-per-query-class + cost ledger) — explicitly
   deferred here per this lane's `must_not_touch` (no load test against a live deployed
   connector from this lane).
3. **Extend the query corpus once the MCP↔web namespace gap (finding §5.2) narrows** —
   today's `avg_mapped_fraction` numbers are a real but partial picture; a widened
   `LIVE_TOOL_TO_RETRIEVAL` map should raise health/marriage off 0% and this battery
   should be re-run to confirm the routing-accuracy gate still holds with more primitives
   actually executing (not just compiling).
4. **Wire `run_battery.ts`'s exit code into CI** as the actual automated regression gate
   the V5 close criteria describe ("battery scores recorded as the regression baseline")
   — this session produced and ran the harness but did not add a CI workflow step, which
   was out of this lane's stated deliverable (harness + baseline run, not CI wiring).

## §7 — Reproduction

```
cd platform
npx tsx --conditions=react-server tests/eval/w5_battery/run_battery.ts --concurrency=8 --out=/path/to/report.json
npx vitest run tests/eval/w5_battery/lib.test.ts   # 38 tests, unit-level regression coverage
npx tsc --noEmit -p tsconfig.json                   # clean on this lane's diff
```

---
*End of W5_BATTERY_BASELINE v1.0 — first baseline, 60/60 combos, GATE PASS on this
lane's own criteria. Not the final V5-gate run (§6).*

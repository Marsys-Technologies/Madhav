---
artifact: NIRMANA_ENGINE_DECISIONS_FOR_THE_NATIVE
canonical_id: NIRMANA_ENGINE_DECISIONS_FOR_THE_NATIVE
version: "1.2"
status: OPEN — one entry, raised 2026-09-26, campaign continued around it
campaign_id: nirmana-engine
authority: 00_ARCHITECTURE/briefs/nirmana/NIRMANA_ENGINE_ELEVATION_PROMPT_v1_0.md §8
changelog: >
  v1.1 (2026-09-26) — CORRECTED BEFORE FIRST COMMIT. v1.0 of this entry claimed "any asset built
  through the normal Build flow now records a real duration and a real rate." That was false, and it
  was the executor's error, not the implementer's. A1's independent gate review found that the
  orchestrator never times the writer at all — it only sums what each writer self-reports — so
  coverage was a lottery, not a guarantee, and the decision below was framed on a false premise.
  Corrected with the measured per-layer figures. The legacy-caller count is also corrected from 7 to
  8. v1.0 was never committed; this is the first recorded version.
  v1.2 (2026-09-26) — SECOND executor correction, same defect class as the first, caught by the same
  gate. v1.1's closing "Note on scale" asserted that the legacy path was "the ONLY remaining source of
  NULL rates". That was also false: five other paths leave the columns NULL, two of which are the
  common steady-state case on a rebuild. v1.1 fixed a large coverage overstatement and introduced a
  smaller one of identical kind, in the same sentence that steers the native toward option (a). The
  absolute is now removed rather than re-scoped, and the residual paths are enumerated and measured.
  Neither v1.0 nor v1.1 was ever committed; this is still the first recorded version.
---

# Decisions for the native — campaign `nirmana-engine`

Per the campaign prompt §8, a packet stops and records here when the work would require (1) changing
the frozen `WriterBase` contract, (2) changing an asset's data, writer or algorithm, or (3) exposing a
secret. **In every case the rest of the campaign continues.** Nothing here blocks another packet.

---

## D-1 · The legacy L1 telemetry path cannot be instrumented without editing writers

**Raised by:** packet A1 ("Record how long and how fast"), 2026-09-26.
**Stop condition:** §8(2) — changing an asset's writer.
**Effect on the campaign:** A1 lands as an **honest partial**. Every other packet continues unaffected.

### What was found

There are **two** paths that write `asset_throughput`, not one:

1. **The orchestrator path** — `pipeline/orchestrator/asset_runner.py`.
2. **A legacy path** — `ga_writers/_telemetry.py`, called directly from **8** `ga_*` writer call sites,
   bypassing the orchestrator's write path entirely.

A1 extended the legacy helper to accept and correctly guard a duration. But **none of its callers pass
one**, and making them pass one means editing writer files. That is stop condition (2), so A1 stopped
there rather than claiming the packet complete.

### The coverage correction — read this before the decision

An earlier version of this entry claimed the orchestrator path was now fully fixed. **It was not, and
the error was the executor's.** A1's gate review established that **the orchestrator never times the
writer**: it only sums what each writer chooses to self-report in `WriterResult.duration_seconds`,
which defaults to `0.0`. Measured coverage of writers that actually populate it:

| layer | writers reporting a duration |
|---|---|
| `bg_*` | 30 / 32 |
| `mi_*` | 14 / 14 |
| `ka_*` | 2 / 23 |
| `ga_*` | 1 / 19 |
| `bo_*` | **0 / 24** |
| `ph_*` | **0 / 8** |

So roughly **201 of 268 rows would have stayed NULL** — every L2 and L4 asset among them — through the
very path that was supposed to fix them. The reviewer rated this a documentation defect rather than a
code defect, and said plainly that had the *code* claimed that coverage, the packet would have been
REJECTED.

**This is being fixed inside the campaign, not deferred to the native.** A correction pass now has the
orchestrator measure its own monotonic wall-clock around its invocation of the writer, so the engine
measures what it claims to measure instead of reporting a number it was handed. That requires **no
contract change and no writer change** — `WriterResult.duration_seconds` still exists; the engine
simply stops depending on it. When that lands, orchestrator-path coverage becomes universal.

**What remains genuinely blocked is only the legacy path below.**

### The larger thing this exposes, which is the actual decision

`CLAUDE.md` §N.2 states the frozen contract as: a writer **"does NOT write `asset_throughput` itself —
orchestrator is the sole build-state writer"**, and names `_telemetry` explicitly as excluded.

**The legacy path violates that contract today, and has for some time.** Eight writer call sites reach
`asset_throughput` directly. This campaign did not introduce it and cannot repair it: removing a
writer's access to `asset_throughput` *is* editing writers, and re-routing them through the
orchestrator touches the contract boundary the campaign is forbidden to move.

So the honest statement is: **the frozen contract has a pre-existing breach, and the engine's
build-state surface is therefore not single-writer in practice, only in doctrine.** Every "the
orchestrator is the sole build-state writer" guarantee downstream inherits that gap.

### What the native is being asked to decide

Not whether A1 was done correctly — it stopped in the right place. The decision is what should happen
to the legacy path, and it is genuinely the native's because every option crosses a boundary this
campaign may not cross alone:

- **(a) Leave it.** Assets built through the legacy path keep reporting NULL rates. Cheapest; the
  doctrine in §N.2 stays formally false and should be amended to describe what is actually true.
- **(b) Wire the duration through the 8 call sites.** Small and mechanical, but it is writer edits, so
  it belongs to the asset campaign, not this one.
- **(c) Retire the legacy path** and route those writers through the orchestrator. Restores §N.2 to
  being true. The largest change, and squarely a contract-boundary question.

**Executor's recommendation: (b), assigned to the asset campaign, with §N.2 amended in the same pass to
describe the real state until it lands.** (c) is correct in principle but should not be attempted while
the asset contract is still moving — the same reasoning the native already applied to D1's timing.

### The residual NULL paths — enumerated, because two earlier drafts of this entry guessed instead

**A caution the native should read before weighing the options.** Twice now this document has asserted
a coverage claim the executor had not verified, and twice the independent gate caught it. The figures
below are the reviewer's, re-derived by grepping every write site in `asset_runner.py`; they are not
an estimate.

With the orchestrator now timing both writer shapes, the legacy `_telemetry` path is **not** the only
remaining source of NULL rates. Exactly one site in `asset_runner.py` writes these columns. Every other
completion path leaves them NULL:

| # | path | why it yields NULL | how common |
|---|---|---|---|
| 1 | `_run_service_health_probe` | legacy health-probe service assets (`bg_*`, `health_probe` spec, no registered writer): sets `state='lit', rows_written=0`, no duration | 8 `storage_type='service'` assets |
| 2 | `_mark_probe_green` | the writer never runs, so there is nothing to time | **common steady state** |
| 3 | `_skip_no_delta` | same — a healthy skip, not a failure | **common steady state** |
| 4 | the C2 degraded branch | every asset, in any environment where migration 1094 has not applied | environment-wide when it bites |
| 5 | a fully-resumed writer | every sub-step already complete via `completed_keys`, so duration sums to `0.0` → NULL | occasional |
| 6 | the legacy `_telemetry` path | **the subject of this decision** | 8 writer call sites |

Paths 2 and 3 matter most for reading the table honestly: **on a rebuild of an already-built chart,
most assets skip and legitimately receive no fresh duration.** That is correct behaviour — a healthy
skip is not a measurement failure, and `skip_no_delta` is explicitly healthy under this campaign's own
standard. But it means "NULL rate" will remain a normal, frequent reading after this campaign closes,
and a future reader must not mistake that for the instrumentation having failed.

**What this does to option (a):** it is a smaller concession than v1.0 implied and a *larger* one than
v1.1 implied. The legacy path is one of six NULL sources, but it is the only one that is a **defect**
rather than either correct behaviour (1, 2, 3, 5) or an environment fault already made observable
(4). So (a) leaves a genuine, permanent gap — just not the sole one.

### What this does NOT block

Nothing. A1 proceeds through its correction pass and re-review with this limit named; A2, A3 and
Phases B–D are untouched by it.

---
artifact: NIRMANA_ENGINE_DECISIONS_FOR_THE_NATIVE
canonical_id: NIRMANA_ENGINE_DECISIONS_FOR_THE_NATIVE
version: "1.1"
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

**Note on scale:** with the orchestrator now timing writers itself, this legacy path is the *only*
remaining source of NULL rates, so (a) is a materially smaller concession than it would have been under
the mistaken framing above.

### What this does NOT block

Nothing. A1 proceeds through its correction pass and re-review with this limit named; A2, A3 and
Phases B–D are untouched by it.

---
artifact: NIRMANA_ENGINE_ELEVATION_STATE
canonical_id: NIRMANA_ENGINE_ELEVATION_STATE
version: "0.2"
status: LIVE — rewritten at every packet close
campaign_id: nirmana-engine
authority: 00_ARCHITECTURE/briefs/nirmana/NIRMANA_ENGINE_ELEVATION_PROMPT_v1_0.md
runs_in: /Users/Dev/madhav-engine (branch campaign/nirmana-engine)
last_updated: 2026-09-26T12:15Z
---

# Nirmāṇa engine elevation — STATE

## Where the campaign is

**Phase A (the gate) — IN FLIGHT.** No packet closed yet.

| packet | title | status | review verdict | before | after |
|---|---|---|---|---|---|
| A1 | Record how long and how fast | before measured; **implementation in flight** | — | 268/268 rows NULL rate (100%, all six layers) | — |
| A2 | Always record why it failed | before measured; **implementation in flight** | — | 301 empty-error records / 82 assets / 46 runs (13.25% of failures) | — |
| A3 | Stop one registry change killing a whole run | before measured; implementation queued to wave 2 | — | 18 records / 8 runs, every run losing 100% of its plan | — |
| A2b | `mark_asset_error` empty-exception hardening | **carried** (split out of A2 to keep waves disjoint) | — | latent, not inflating the 301 | — |
| A3b | Runs dispatched with no manifest at all | **carried** (split out of A3; 6 of its 8 runs) | — | 7 records / 6 runs | — |
| B1 | Cascade reads as one cause, N blocked | not started | — | 1,281 cascade records (confirmed exactly) | — |
| B2 | Blocking radius, recorded | not started | — | — | — |
| C1 | Crash, orphan and reap | not started | — | — | — |
| C2 | Stuck states | not started | — | — | — |
| D1 | Nine checks applied to the engine | not started (authored last; frozen only if the asset contract has stopped moving) | — | — | — |

## Live failure-rate figures — re-derived this session, not inherited

Every figure below was measured independently by a diagnostician against production on 2026-09-26,
read-only, with its query recorded in `measurements/`. **The inherited headline did not survive
contact with the record**, and the corrections are material:

| inherited claim | measured | verdict |
|---|---|---|
| 2,283 failed/aborted records | **2,271** (`error`=1,565 + `aborted`=706) | off by 12 |
| 1,281 cascade | **1,281** | exact |
| ~127 causal | **128** | essentially exact |
| 543 infra | **561** — the frozen-manifest family (18) was never folded in | undercounted by 18 |
| 307 silent | **301** across 82 assets, 46 runs | overcounted by 6 |
| `rows_per_second` NULL "for all 40 L0 assets" | **268 of 268, every layer** | not an L0 problem; engine-wide |
| L0 has 40 throughput rows | **39** — `bg_gochara_citation_resolution` has no row at all | one asset never recorded |
| 18 assets / 8 runs on frozen-manifest abort | **18 / 8** | exact |

**The inherited claim was also internally inconsistent:** its own four parts sum to 2,258, not the
2,283 it states. The 2,271 figure above is what the record actually holds.

**Three findings that change what the packets are:**

1. **A2 is a plumbing defect, not a capture defect.** 295 of the 301 silent records resolve to one
   message, `orphan-watchdog: run never dispatched`, that the engine *already computes one statement
   earlier* in the same function and fails to pass into the companion `build_run_assets` UPDATE.
   `build_events` and `orchestrator_noop_events` are empty for all 46 runs, so nothing else knows more.
2. **A3's 18 records are two unrelated bugs sharing an error prefix.** Family A (11 records, 2 runs) is
   the real registry-drift case. Family B (7 records, **6 of the 8 runs**) is one-off dispatch scripts
   inserting `build_runs` with no `plan_manifest` at all — there is no manifest to have drifted and none
   to re-freeze. A3 as scoped fixes 2 of 8 runs, and the report will say exactly that.
3. **A1 is mostly "stop discarding a value the engine already receives."** The frozen `WriterResult`
   already carries `duration_seconds`; `rows_per_second` has existed as a column since migration 169
   (2026-06-06) and is written by **zero** code paths.

**Two families the record blames on the engine that this repository cannot account for:**
`guardian_cleanup` (310 records) and `manual reap: …` (77 records) have **zero source hits** anywhere
in this codebase. `NOT ATTRIBUTABLE` from `madhav-engine` — an external process, ad-hoc operator SQL,
or deleted code. Material to C1, and recorded now so C1 does not start by assuming the code is here.

**One data-integrity anomaly, registered and deliberately not fixed:** 7 `build_run_assets` rows carry
`BLOCKED:` cascade text while `state='complete'`. It belongs to B1, not to A2.

## Branch head

`d9dab8ad2` — campaign state scaffold. No engine file touched yet; build wave 1 (A1 Python, A2
TypeScript) is in flight and will be committed per packet after review.

**Wave sequencing**, forced by the same-file rule (prompt §4): A3 needs both
`pipeline/orchestrator/runner.py` and `app/api/cockpit/runs/route.ts`; A2 needs the latter. So
**wave 1 = A1 (Python) ∥ A2 (TypeScript)**, fully disjoint; **wave 2 = A3**, once A2 releases
`runs/route.ts`. A1 deliberately does not edit `runner.py`: its failure paths already leave
`rows_written` untouched, which is the shape A1 must preserve, so preserving it means not editing it.

## Environment, confirmed at session open

- cwd `/Users/Dev/madhav-engine`, branch `campaign/nirmana-engine`, head `975370eb5`.
- `.claude/agents/nirmana-{engine-builder,engine-diagnostician,packet-reviewer}.md` all present.
- DB posture: `transaction_read_only = on`, database `amjis`, `PGPORT=5433`, PostgreSQL 15.18.

## Blockers

None. One tooling deviation, recorded and worked around (see EVENTS.jsonl, `subagent_dispatch_workaround_adopted`):
this session's agent registry loaded from the prior working directory and does not resolve the
`nirmana-*` subagent types by name, so each is dispatched as `general-purpose` with an explicit model
override (Sonnet for diagnostician and builder, Opus for the packet reviewer) and its definition file
inlined verbatim as the role preamble. §4 routing and role separation are preserved; a fresh session
started in this worktree resolves the definitions natively, so resumability is unaffected.

## Stop conditions — none triggered

No packet has required a `WriterBase` contract change, an asset's data/writer/algorithm, or exposed a
secret. `DECISIONS_FOR_THE_NATIVE.md` not yet created; it is created only when a stop condition fires.

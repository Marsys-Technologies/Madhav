---
artifact: NIRMANA_ENGINE_ELEVATION_STATE
canonical_id: NIRMANA_ENGINE_ELEVATION_STATE
version: "0.1"
status: LIVE — rewritten at every packet close
campaign_id: nirmana-engine
authority: 00_ARCHITECTURE/briefs/nirmana/NIRMANA_ENGINE_ELEVATION_PROMPT_v1_0.md
runs_in: /Users/Dev/madhav-engine (branch campaign/nirmana-engine)
last_updated: 2026-09-26T12:00Z
---

# Nirmāṇa engine elevation — STATE

## Where the campaign is

**Phase A (the gate) — IN FLIGHT.** No packet closed yet.

| packet | title | status | review verdict | before | after |
|---|---|---|---|---|---|
| A1 | Record how long and how fast | before-measurement dispatched | — | pending | — |
| A2 | Always record why it failed | before-measurement dispatched | — | pending | — |
| A3 | Stop one registry change killing a whole run | before-measurement dispatched | — | pending | — |
| B1 | Cascade reads as one cause, N blocked | not started | — | — | — |
| B2 | Blocking radius, recorded | not started | — | — | — |
| C1 | Crash, orphan and reap | not started | — | — | — |
| C2 | Stuck states | not started | — | — | — |
| D1 | Nine checks applied to the engine | not started (authored last, never frozen this campaign unless the asset contract has stopped moving) | — | — | — |

## Live failure-rate figures

**Not yet re-derived.** The campaign's inherited headline — 776 runs, 2,283 failed/aborted records
(1,281 cascade / 543 infra / 307 silent / ~127 causal), one asset-run attempt in three failing — is
the claim under test, not an established figure. All three Phase A diagnosticians were instructed to
re-derive it independently. This section is filled from their measurements, with queries, and this
file will say plainly if the inherited split was wrong.

## Branch head

`975370eb5` — Nirmāṇa engine elevation: autonomous campaign prompt and its three agents.
Nothing implemented yet; no engine file touched.

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

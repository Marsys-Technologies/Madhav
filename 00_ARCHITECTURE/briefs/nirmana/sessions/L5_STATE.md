---
artifact: L5_STATE.md
canonical_id: NIRMANA_V21_L5_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L5
layer: L5 — Mīmāṃsā
owner: the L5 session (this file is yours alone — charter C5)
last_updated: (none yet — stub created by CONDUCTOR at v2.1 bootstrap)
---

# L5 — Mīmāṃsā — SESSION STATE

Stub created by the CONDUCTOR so this session has a file to rebase onto. **Everything below is
yours to overwrite.** Charter C9: this file is your memory — update it every loop, commit it with
every PR and at every milestone, so re-pasting your prompt into a fresh session is safe at any
moment.

**Read order on ANY start:** `SESSION_CHARTER_V21.md` → this file → `git fetch origin main` →
your `nirmana-adjudication` issues → continue.

- **Coordination issue:** #1713 (run-slot claims, freeze-ordering acks, monster scheduling)
- **Adjudication:** open a new issue labeled `nirmana-adjudication`, then keep working (C3)
- **Migration range:** 690–699 (yours alone, collision-free by construction)
- **Branch namespace:** `codex/nirmana-l5-*` · **PR title prefix:** `L5:`
- **Worktree:** `~/nirmana-s/l5`
- **Standing ruling D-CND-01 (read before your first Conform-stage check):** a `count(*) = N` is
  permitted only as a conjunct of something that can fail on corruption it cannot see — a total
  content fingerprint, or named invariants (contiguity, tiling, distinctness, cross-table
  FULL-JOIN consistency, NULL/range guards). Alone it is forbidden (C12). `expected_volume_formula`
  is REQUIRED when a count equality is the volume assertion; not required alongside a total-content
  digest. Full reasoning + the L0 evidence: `CAMPAIGN_STATE.md` → CONDUCTOR standing audit A-01.
- **Freeze predecessor:** L4 Phala must be frozen before your W6 ceremony (C2; asset work is never held)

## Position

`L5-W1` — not started.

## Asset table (15 assets)

Populate from the frozen definition `t0-2026-09-01-0e5b06fb`, one row per asset:
`asset_id | W2 route | status | E-gate | capsule ref | notes`.

| asset_id | route | status | E-gate | capsule | notes |
|---|---|---|---|---|---|
| _(populate at W1)_ | | | | | |

## Decisions log

One line per decision you take under delegated authority (C3): what, why, evidence.

## Held items

Anything blocked, with the specific gate it waits on (E-gate ancestor, capability-delta, adjudication #).

## CAPABILITIES LANDED

Charter C6 — announce here, on `main`, each NEW capability downstream layers may consume.
One line per capability with its PR number. Consumers poll `origin/main` for this section.

_(none yet)_

## Cost ledger

Wall-clock + tokens per asset; the CONDUCTOR rolls this into the root campaign cost section at
your layer close.

| asset | wall-clock | tokens | notes |
|---|---|---|---|

## Heartbeat

One line per loop: `<UTC ISO-8601> — <position> — <what you are doing>`.

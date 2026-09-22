---
artifact: KALA_KICKOFF_REDIRECT_002
version: "1.0"
status: CURRENT
date: 2026-09-22
addressed_to: the Phase 0/1 setup session (worktree /Users/Dev/madhav-l3/setup, branch l3/kala-setup-phase01)
follows: KICKOFF_REDIRECT_001.md
effect: four facts established after 001; cancels nothing; adds one register amendment to Phase 1.2
---

# Redirect 002 — four facts you need before Phase 1

## 1. Your base is correct. Do not switch branches.

A message from the strategic session may reach you claiming the accepted L3 source is not on
`main`. **Retracted.** Verified by content diff, not ancestry: `main` carries every accepted L3
source commit — Kshetra P0 `3f109869d` (7 files IDENTICAL), Bhavishya P0 `a3e518864` (IDENTICAL),
DHARA midpoint fix `87cc8c9baf` (IDENTICAL), and W2 first-frontier `47131772b` where the one
differing file, `ka_yojaka.py`, differs because `main` carries the *later* accepted DP-SD-019
Yojaka repair (`7697c43b3`). `DHARA_SWEEP_SEMANTIC_VERSION = '1.2'` is on `main` at
`platform/python-sidecar/services/ka_kshetra/dhara_sweep.py:52`. The execution branch
`codex/madhav-data-plane-execution` is ahead only in ledgers, generated digests/pins and the
unmerged 1035/1036 migration candidates. **Your real-DB P0 rehearsal is exercising the accepted
writers.** Say so in the close-out.

## 2. Phase 1.1 — half of B1 was known and HELD at W0; reconcile, do not re-report

`MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md` §4.1 line 133 records `ka_gochara`
as *"after resonance; seed target mismatch held"*. The registry `target_table` error was known.
Before you correct the registry row, find why the hold exists (the seed lives in a shared source
file, `platform/scripts/seed/asset_registry_seed.ts`, whose ownership crosses campaigns) and state
the release condition in your PR. The other half of B1 — the Clear route's deletion path to
`generation='v1'` via `build_protected_assets = 0`, no `is_active` filter, and non-admin
reachability — was **not** known at W0 (grep of the W0 records is empty). That half is new; keep
it exactly as the kickoff states it.

## 3. Phase 1.2 — the `phala_rectification` read is a register amendment, and the Strategy already rules on it

The W0 field register and current-state record contain no mention of `stage3_clocks.py:1012`
reading `phala_rectification` (grep empty). File it as a **FIELD_CONTRACT_REGISTER amendment** —
an undeclared upward read on `ka_kshetra` — in addition to the grant decision. And note that the
hold on the grant is Strategy-backed, not a preference: Strategy §6.2 states *"Rectification and
L5 weight inputs require separately admitted, purpose-compatible immutable artifacts. An earlier
timestamp does not make an event-derived rectification posterior admissible under the event-free
prospective contract."* A live table read of L4 output cannot satisfy that. Grant the three `bg_*`
tables; hold the fourth; cite §6.2.

## 4. Migrations — two directories, one numeric sequence

`platform/migrations/` (high-water **1070**) and `platform/supabase/migrations/` (high-water
**1041**) both exist. `platform/scripts/migrate.ts:834-835` reads **both** and orders them
numerically as **one sequence**. DP-SD-021's partition therefore spans both trees: Pūrṇa
1042–1069, L3 1070–1119, shared ≥1120. Author L3 migrations at `platform/migrations/1071+`. Check
**both** directories before claiming a number. `1035`/`1036` in `supabase/` are the data-plane
campaign's unmerged generation candidates (CURRENT_STATE §5): never touch, never collide.

## 5. Phase 1.5 — cite, do not re-derive

The full cascade blast radius, including the L4 reach through `phala_anchors`, is already in
CURRENT_STATE §4.2, and Bhavishya's immutable-row rule is FIELD_CONTRACT_REGISTER fence #7. Cite
them; add only what changed.

Everything in REDIRECT_001 stands.

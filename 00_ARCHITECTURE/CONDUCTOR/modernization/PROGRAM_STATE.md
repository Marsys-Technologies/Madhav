# PROGRAM_STATE — Platform Modernization (single re-kick pointer)

> Read THIS at every re-kick. It replaces the heavy session-open reads (lean-transform governance).
> Conductor updates it at every batch stop. Authoritative for "where are we now."

## Snapshot
- **Status:** RUNNING — Batch 1 in flight (zero human gates).
- **Current batch:** Batch 1 (Wave 0 + Wave 1 kickoff).
- **Tracker:** LIVE at `http://localhost:8787` (process started by Conductor; PID logged in `/tmp/madhav-tracker.log`). Source of truth for live progress.
- **main HEAD:** `940ee3b6` (after `0t` commits — planning artifacts `399ceb3b` + tracker backend `a640af1c` + emit_gate helper `940ee3b6`).
- **Last green per stream:** A=none · B=none · C=none.
- **Open halts:** none.

## Gate board
| Gate | Status | Unblocks |
|---|---|---|
| naming_ci | PENDING (set by 0a.0) | 0a.1, 1.1, 2b, 2c, 2d |
| jh_oracle_pinned | **RED — NATIVE INPUT NEEDED** | 1.2 |
| G1_jh_parity | PENDING (set by 1.2) | 2a, 3.cutover |
| G2_authz_live | PENDING (set by 2c) | 3.tier_excision |
| G3_contract | PENDING (set by 2b) | 3.dejudge, 3.gateway |
| G4_no_native_lit | PENDING (set by 2a) | — |
| G5b_onfinish | PENDING (0b.1 contributes; full set in cutover) | 3.legacy_delete |
| G6_tool_coverage | PENDING (set by 3.tool_asset_recon) | — |

## Toolchain adaptations (recorded for re-kicks)
- `platform/` is **npm** (not pnpm). All gate `check_commands` rewritten from `pnpm vitest run …` to `npx vitest run …` (works under either manager — same binary). pyyaml@6.0.3 + pytest@9.0.3 installed into project `.venv`.
- Sidecar paths: queue gate `jh_oracle_pinned` and brief 1.2 reference unprefixed `python-sidecar/natal_engine/…` — canonicalized to `platform/python-sidecar/natal_engine/…` (where the existing sidecar lives).

## The one input that blocks the engine
`jh_oracle_pinned` is RED. To flip it green, drop the JH reference into
`platform/python-sidecar/natal_engine/fixtures/jh_oracle.json`:
- the **JH version/build** to treat as authority,
- the **ayanamsha** (e.g. Lahiri/Chitrapaksha 23°37′58″ per FORENSIC), and
- the **reference outputs** for the native (1984-02-05) captured once from that JH build.
Everything except `1.2` (engine-to-parity) can run without it; `1.1` (scaffold + harness) proceeds.

## Batch 1 — in-flight units (Conductor dispatch)
- **0t** program tracker — **DONE & merged** (commits `a640af1c` + `940ee3b6`). Live on `:8787`.
- **0a.0** naming-CI (Stream A · `../MadhavStreamA` · `prog/stream-a`) — sub-agent dispatched.
- **0b.1** B.11 adapter gate (Stream B · `../MadhavStreamB` · `prog/stream-b`) — sub-agent dispatched.
- **0b.3** mirror retirement (Stream C · `../MadhavStreamC` · `prog/stream-c`) — sub-agent dispatched.
- **0b.2** secret/DB-pw remediation — queued for Stream B as soon as 0b.1 commits (same-worktree serialization).
- **0a.1** route renames (A), **1.1** engine scaffold (C) — both unlock when `naming_ci` flips green.

## Re-kick protocol
1. Open a fresh Conductor chat at repo root on `main`.
2. Paste: "Continue the Platform Modernization program. Read PROGRAM_STATE.md + session_queue.yaml; resume from the next eligible units."
3. Conductor reconciles gate board, picks eligible units across streams A/B/C, runs to the next batch stop, updates this file.

## Safety reminders (automated, no human)
- Every prod op: pre-flight green + post-deploy smoke + auto-rollback on failure.
- DB: additive + staging→live swap; no destructive in-place; column drops only after a green post-cutover window.
- New flags default OFF (reversible). Kill-switch: error-rate spike → halt_queue + rollback last cherry-pick.

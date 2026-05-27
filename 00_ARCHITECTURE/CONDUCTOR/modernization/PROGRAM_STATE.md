# PROGRAM_STATE — Platform Modernization (single re-kick pointer)

> Read THIS at every re-kick. It replaces the heavy session-open reads (lean-transform governance).
> Conductor updates it at every batch stop. Authoritative for "where are we now."

## Snapshot
- **Status:** RUNNING — Batch 1 CLOSED; 7/20 units green (35%); awaiting native input for 1.2 + brief authoring for 2b/2c/2d.
- **Current batch:** Batch 1 closed at sub-agent count = 6. Batch 2 begins on re-kick.
- **Tracker:** LIVE at `http://localhost:8787` (PID logged in `/tmp/madhav-tracker.log`). Always re-check tracker first.
- **main HEAD:** `af0c29be` (1.1.3 scaffold + no-LLM tests for natal_engine).
- **Last green per stream:** A=`0a.1` (`c9000d75`) · B=`0b.2` (`b720e577`) · C=`1.1` (`af0c29be`).
- **Open halts:** none.
- **Attention (not a halt; native action requested):**
  - **Live DB password rotation requested** — 0b.2 found the literal value of GCP Secret Manager `amjis-db-password` at `platform/scripts/load_chart_facts_local.py:76` (introduced commit `0bcc5415`, 2026-05-25). Literal removed from HEAD; the value was NOT echoed/committed elsewhere. Operator should rotate `amjis-db-password` at next maintenance window. Full incident in `platform/scripts/governance/secret_naming.md §5`.
  - **JH oracle still required** — see "blocker" below.

## Gate board
| Gate | Status | Unblocks |
|---|---|---|
| naming_ci | **GREEN** (0a.0 closed; 77 baseline violations recorded) | 0a.1 ✓, 1.1 ✓, 2b, 2c, 2d |
| jh_oracle_pinned | **RED — NATIVE INPUT NEEDED** | 1.2 |
| G1_jh_parity | PENDING (set by 1.2 once jh_oracle drops) | 2a, 3.cutover |
| G2_authz_live | PENDING (set by 2c) | 3.tier_excision |
| G3_contract | PENDING (set by 2b) | 3.dejudge, 3.gateway |
| G4_no_native_lit | PENDING (set by 2a) | — |
| G5b_onfinish | PENDING — **0b.1 contributes (citation-gate half done)**; full set in cutover | 3.legacy_delete |
| G6_tool_coverage | PENDING (set by 3.tool_asset_recon) | — |

## Toolchain adaptations (recorded for re-kicks)
- `platform/` is **npm** (not pnpm). Gate `check_commands` rewritten from `pnpm vitest run …` to `npx vitest run …` (same vitest binary). vitest must be invoked from `platform/` for `@/` alias resolution.
- pyyaml@6.0.3 + pytest@9.0.3 installed into project `.venv` (`/Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3`).
- Sidecar paths: queue gate `jh_oracle_pinned` and brief 1.2 reference unprefixed `python-sidecar/natal_engine/…` — canonicalized to `platform/python-sidecar/natal_engine/…` (where the existing sidecar lives, where 1.1 built the scaffold).

## Batch 1 — closed units (commits on main)
| Unit | Wave | Stream | Commit(s) on main | Notes |
|---|---|---|---|---|
| **0t** | 0-support | (Conductor) | `a640af1c`, `940ee3b6` | Tracker live on `:8787` (ephemeral; `REMOVE.md` for tear-down). |
| **0a.0** | 0a | A | `baf4e198` | `naming_lint.py` + `naming_rules.yaml` + 77-violation baseline + CI wire. **Sets gate `naming_ci` GREEN.** |
| **0a.1** | 0a | A | `2d3dd91a` `a01af583` `c9000d75` | consume→consult (4 routes + 5×308 aliases); /api/panchanga→panchang merge (alias dropped per lint rule, only caller updated). 18/18 chat tests pass. |
| **0b.1** | 0b | B | `3ec952e3` | B.11 citation gate ported to adapter path at `consume/route.ts:1092–1175`; 7 new tests + 200 regression tests pass. **Contributes to G5b_onfinish.** |
| **0b.2** | 0b | B | `edc0bbd5` `b720e577` | `secret_scan.sh` + CI wire + literal-credential removal (2 files); see "Attention" — live DB password found + scrubbed. |
| **0b.3** | 0b | C | `834164b7` | Atomic 5-surface mirror-discipline retirement; `.geminirules` + `.gemini/` + `mirror_enforcer.py` deleted; CLAUDE.md §K + GOVERNANCE §K.3 + CANONICAL §2 + ND.1 closed; ripple-out fixes to `drift_detector.py`/`schema_validator.py` to prevent crashes from deleted refs. |
| **1.1** | 1 | C | `1d586f30` `32be40ee` `af0c29be` | `platform/python-sidecar/natal_engine/` scaffold + canonical output schema + `jh_oracle` fixture loader/schema + parity harness skeleton + no-LLM test. 8 passed / 1 skipped (jh_parity correctly skips on RED gate). Spot-check matches FORENSIC v8.0 panchanga 5/5. |

## Eligible-now units (Batch 2)
- **1.2** engine→JH parity (Stream C) — **BLOCKED on `jh_oracle_pinned`**. Drop `platform/python-sidecar/natal_engine/fixtures/jh_oracle.json` to unblock; brief 1.2 will then run unmodified.
- **2b** unified contract, **2c** tenancy/authz, **2d** Command Center — **eligible per gate** (naming_ci green) but `status: not_yet_detailed` in `session_queue.yaml`. Wave-2 briefs must be authored before sub-agent dispatch. (Per execution plan §5 + brief-amendment rule: Cowork authors the fresh briefs; Conductor never edits a brief mid-flight.)
- **2a** L2.5 deterministic build — blocked on G1 (engine parity).
- All Wave-3 + Wave-4 units — blocked on their own gates (G3, G2, G1, etc.).

## The one input that blocks the engine
`jh_oracle_pinned` is RED. To flip it green, drop the JH reference into
`platform/python-sidecar/natal_engine/fixtures/jh_oracle.json` (schema in `fixtures/jh_oracle_schema.json`):
- the **JH version/build** to treat as authority,
- the **ayanamsha** (e.g. Lahiri/Chitrapaksha 23°37′58″ per FORENSIC), and
- the **reference outputs** for native (1984-02-05 10:43 IST, Bhubaneswar) captured once from that JH build.
Once dropped, Conductor re-kick runs unit 1.2 automatically.

## What to ship to the native at re-kick
1. **JH oracle fixture** (above) — unblocks 1.2 + cascades into 2a (L2.5 build).
2. **Wave-2 briefs** (`2b unified contract`, `2c tenancy + authz`, `2d Command Center`) — Cowork authoring task. Once written, drop them at `00_ARCHITECTURE/CONDUCTOR/modernization/briefs/BRIEF_2b_…md` and flip their `status: not_yet_detailed` → omit (eligible). Conductor will pick them up.
3. (Optional but tracked) **Rotate `amjis-db-password`** in Secret Manager — see Attention block.

## Re-kick protocol
1. Open a fresh Conductor chat at repo root on `main`.
2. Paste: "Continue the Platform Modernization program. Read PROGRAM_STATE.md + session_queue.yaml + CONDUCTOR_HALT_LOG.md; resume from the next eligible units."
3. Conductor reconciles gate board, picks eligible units across streams A/B/C, runs to the next batch stop, updates this file.

## Safety reminders (automated, no human)
- Every prod op: pre-flight green + post-deploy smoke + auto-rollback on failure.
- DB: additive + staging→live swap; no destructive in-place; column drops only after a green post-cutover window.
- New flags default OFF (reversible). Kill-switch: error-rate spike → halt_queue + rollback last cherry-pick.

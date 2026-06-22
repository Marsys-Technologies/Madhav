---
artifact: L4_PHALA_AUTONOMOUS_EXECUTION_v2_0.md
canonical_id: L4_PHALA_AUTONOMOUS_EXECUTION
version: 2.0
status: CURRENT — the fully-autonomous, one-kickoff execution model for L4 Phala (zero human gates)
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: the operator-pre-flight model in KICKOFF_L4_PHALA v1.0 (OP1–OP5 absorbed into Phase 0)
governs: 00_ARCHITECTURE/CONDUCTOR/l4-phala/session_queue.yaml + KICKOFF_L4_PHALA.md
role: >
  Aligns the L4 Phala build to the native directive (2026-06-22): FULLY AUTONOMOUS implementation via
  the Conductor + the agentic swarm — NO human gates or interruptions. ONE kickoff prompt triggers
  everything: autonomous environment setup, the pre-requisite operator actions (now Conductor-run),
  maximal parallelization in an isolated worktree, and the full commit→merge→deploy→build→data-gen
  cycle through to seal. Builds on AUTONOMY_RESILIENCE_PATTERN_v1_0.md (the proven Brahma model).
---

# L4 Phala — Fully-Autonomous Execution v2.0

> **The native directive (2026-06-22):** fully autonomous, no human gates, Conductor + agentic swarm,
> maximal parallelization, isolated worktree, ONE kickoff. The environment sets itself up; the
> pre-requisites run themselves; the build commits/merges/deploys/builds/generates-data autonomously.
> The ONLY residual native event remains the Tier-3 $5k catastrophic ceiling (async, resumable) + the
> chart-revision adoption flag (async — staged, never blocks the build).

## §1 — What changes from v1.0 (operator gates → autonomous Phase 0)
The v1.0 kickoff had OP1–OP5 as a HUMAN pre-flight. **All are now absorbed into a Conductor-run
Phase 0.** Nothing is a human prerequisite. The single human action is pasting the kickoff once.

| v1.0 operator gate | v2.0 disposition |
|---|---|
| OP1 apply migs 326–329 | **Phase 0 / SETUP-4** — the Conductor applies them via the migrate runner (Tier-2 logged) |
| OP2 CI green on main | **Phase 0 / SETUP-3** — the Conductor runs the CI-remediation sub-routine (fix the 3 known failures), or quarantines them as known_residuals if pre-existing + unrelated (Tier-2) |
| OP3 prod == main | **Phase 0 / SETUP-5** — the Conductor verifies + (if main is ahead) deploys to align (Tier-2) |
| OP4 branch off origin/main | **Phase 0 / SETUP-2** — the Conductor creates the worktree + branch |
| OP5 budget/rails confirmed | **pre-set once** in the kickoff (the ceiling value); not a per-run gate |

## §2 — PHASE 0 — Autonomous Environment Provisioning (the Conductor runs this FIRST)
A new explicit phase, owned by the **Sthāpati (environment-provisioner) role** (§5). Steps, all
Tier-1/Tier-2 (no native gate):

| id | action | detail |
|---|---|---|
| **SETUP-1** | Worktree + isolation | Create an isolated git worktree `MadhavL4Phala` off `origin/main` (the build never touches the user's main checkout). Reuse `CONDUCTOR/SETUP_WORKTREES_*.sh` pattern. |
| **SETUP-2** | Branch | `feature/l4-phala-autonomous` in the worktree; per-asset sub-branches for parallel agents (merged at wave gates). |
| **SETUP-3** | CI health | Run the test suite; if the 3 known pre-existing `main` failures are present + unrelated to L4 → quarantine as `known_residuals` (the documented exit-code-3 whitelist) so CI-green is a reliable signal; if any are L4-blocking → deep-fix ladder. |
| **SETUP-4** | Pre-req migrations | Apply 326–329 to prod via the migrate runner (the A7 gate) — Conductor-run, Smṛti-logged. Verify in `_migrations_applied`. |
| **SETUP-5** | prod == main | Verify the deployed Cloud Run revision == `origin/main` HEAD; if main is ahead, deploy to align. Confirm L3 `kala_*` lit on the LIVE cockpit. |
| **SETUP-6** | Proxy + deps + secrets | Cloud SQL Auth Proxy up (port 5433); `npm ci` + `pip install` in the worktree; confirm env (DATABASE_URL, GCS, model keys for Gemini/DeepSeek). |
| **SETUP-6b** | **INFRA GAP FIX (blocking)** | Add `COPY platform/python-sidecar/services/` to `Dockerfile.pipeline` — ALL ka_*/ph_* writers import `from services.<asset>`; it's in NO Dockerfile → silent ModuleNotFoundError job-hang (L3 masked it via reconcile / CF.L3.8). Verify the web Dockerfile builds `src/lib/schools/` (U4) + the plan-builder topo-sorts new ph_* assets. Rebuild the image. See `L4_PHALA_ORCHESTRATOR_READINESS_v1_0.md §2`. |
| **SETUP-7** | Pre-fan-out (was PRE-1…4) | Pre-allocate migs 330–340; pin ratified params; register the 3 new assets + update the 5 existing (CS1). |
| **GATE-0** | Green-to-build | All SETUP steps pass → the swarm fans out. A SETUP failure that the deep-fix ladder cannot resolve in 6 attempts → Tier-2 park + Smṛti (NOT a native halt unless Tier-3 budget). |

## §3 — Maximal parallelization (the real DAG, not 7 serial waves)
The v1.0 7-wave structure was more serial than the dependencies require. The TRUE dependency graph
(verified from the briefs) allows aggressive parallelism across isolated worktree sub-branches:

```
PHASE 0  (Sthāpati — env + pre-reqs + pre-fan-out)
   │
   ├─ P1  U1 (wire-only)              ─┐  (fully independent)
   ├─ P1  U4 de-hardcode + Task A.0   ─┤  (TypeScript engines — file-disjoint from U3's Python)
   └─ P1  U3 currents-pass-1 (Python) ─┘  (the 6 data/engine currents on ka_sangam)
            │ (U1 + U4 + U3-p1 run IN PARALLEL — disjoint files)
            ▼
      P2  serialize ONLY the ka_sangam touchpoints:
            U3 school-current (C13)  [needs U4 + U3-p1]
            → U2 lifetime + null-fix [needs the enriched currents]
            → RE-SEAL L3
            ▼
      P3  ph_nimitta  (SPINE — alone; the one unavoidable serial gate)
            ▼
      P4  ph_muhurta ‖ ph_pratikara ‖ ph_sankrama ‖ ph_sodhana   (ALL parallel — all depend only on ph_nimitta;
              sodhana is independent of muhurta/pratikara/sankrama)
            ▼
      P5  ph_suddha_sodhana [needs ph_sodhana]  ‖  (ph_pramana waits — needs all predictions)
            ▼
      P6  ph_pramana  [needs all prediction assets]
            ▼
      P7  ph_phaladesa [needs everything]
            ▼
      SEAL
```
**Parallelism gains vs v1.0:** U1+U4+U3-p1 now run together (was W1 then serial W2); ph_sodhana joins
the W4 parallel band (was a separate serial W5). Only three genuine serial points remain: the
ka_sangam touchpoints (P2), the ph_nimitta spine (P3), and the composition tail (P6→P7). Each parallel
band runs in its own worktree sub-branch, merged at the band gate. Velocity is bounded by the critical
path (Phase 0 → U-chain → ph_nimitta → ph_sodhana → ph_suddha → ph_pramana → ph_phaladesa), not by the
asset count.

## §4 — The autonomous build cycle (per asset, no human gate)
Each Śilpī agent in its worktree sub-branch: write code + tests → run the asset's hard gate (if any) →
commit → Vimarśaka post-merge audit → merge to the band branch → at the band gate, merge to the
feature branch → CI-green → **deploy** (the migrate runner applies the asset's migration; the Cloud Run
sidecar rebuilds) → **build/data-gen** (the orchestrator click-Build path runs the writer for chart
`482012f1` → rows land in `phala_*`) → PROD-VERIFY the ACs. All commit/merge/deploy/build/populate is
autonomous (the AUTONOMOUS_MODE rails). Tier-2 decisions Smṛti-logged; Vimarśaka RED → auto-revert.

## §5 — Roles (the 14-role swarm + 1 addition for L4)
The existing 14 roles (charter §E + the pattern's Vimarśaka + Tier-1 Severity Remediator) cover the
build. **One addition** for the fully-autonomous, env-self-setup model:

- **NEW — Sthāpati (स्थापति — the establisher / environment-provisioner), 15th role.** Mandate: own
  Phase 0 (SETUP-1…7 + GATE-0) — worktree, branch, CI health, pre-req migrations, prod==main, proxy/
  deps, pre-fan-out. Inputs: the kickoff + the env spec. Outputs: a green-to-build environment + the
  Smṛti SETUP log. Status: NEW (formalizes what was the human pre-flight). It hands GATE-0 to the
  Sūtradhāra Conductor, which then walks the parallel DAG.
- **Reaffirmed for velocity:** the **deep-fix ladder** (B.1: 6 attempts, escalating to multi-model
  parallel) handles SETUP + build failures without a native halt; the **disposition classifier** (B.2)
  handles any destructive op (e.g. the kala_timeline drop) autonomously; **Vimarśaka** (13th) auto-
  reverts RED merges; the **Tier-1 Severity Remediator** (14th) handles class-1 findings with elevated scrutiny.

## §6 — The ONE residual native touchpoint (unchanged, async)
- **Tier-3 catastrophic budget ceiling ($5k/wave):** the swarm async-notifies at $4.5k, stops at safe
  checkpoint at $5k; the native writes a new ceiling to resume. NOTHING else pauses.
- **The chart-revision flag (D43):** if rectification recommends a different Lagna, ph_suddha_sodhana
  STAGES it + flags async — it does NOT block the build (the build completes on the recorded chart;
  adoption is a separate one-click native action post-seal).

## §7 — The single kickoff
ONE paste of `KICKOFF_L4_PHALA.md` (v2.0) to the Sūtradhāra Conductor in Antigravity triggers:
Phase 0 (env self-setup + pre-reqs) → the parallel DAG build → seal. No human action between the paste
and the sealed layer except the two async Tier-3 events above (if they fire).

---
*End of L4_PHALA_AUTONOMOUS_EXECUTION v2.0. Operator gates absorbed into the Conductor-run Phase 0; the
real DAG parallelized; the Sthāpati env-provisioner role added; one kickoff drives env→build→seal with
zero synchronous human gates. Reuses the proven AUTONOMY_RESILIENCE_PATTERN.*

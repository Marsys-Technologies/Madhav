---
artifact: RETRIEVAL_IMPLEMENTATION_MASTER_PLAN
canonical_id: RETRIEVAL_IMPLEMENTATION_MASTER_PLAN
version: 1.1
status: CURRENT — the execution runway for the retrieval-system build (parallel-enabled)
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: master phased implementation plan — sequences all CLAUDECODE_BRIEFs into one runway
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 + RETRIEVAL_DESIGN_D0_FOUNDATIONS_v1_1 (gates RULED)
changelog:
  - v1.0 (2026-06-27): Initial master plan. Sequences all wave briefs (runtime, D0.5, D1, D2, D3, D4, D-PROFILES, D5, D6/D7, D8) with dependencies, consume/produce, gates, the parameterized-brief detail-pass rule, and the reverse-citation destructive-safety policy.
  - v1.1 (2026-06-27): Parallel multi-agent execution adopted (native ruling). Added §8 — parallel execution shape: serial spine through D1, then two fan-out points (FAN-OUT 1 = D2∥D3∥D4; FAN-OUT 2 = D-PROFILES∥D5∥D5-layer-sub-waves), governed by `CLAUDECODE_BRIEF_RETRIEVAL_PARALLEL_COORDINATION` and its three gates (no-shared-file/escalate-don't-edit; post-merge prod-verify; reverse-citation). D6/D7 and D8 remain serial.
---

# RETRIEVAL SYSTEM — MASTER PHASED IMPLEMENTATION PLAN (v1.0)

> **What this is.** The single execution runway. The design is complete and grounded (code-validated, gates
> ruled); this plan sequences the per-wave `CLAUDECODE_BRIEF`s into a dependency-ordered build that Claude Code
> executes in Antigravity, one wave per session. Cowork authored the briefs; Claude Code implements; results
> flow back to Cowork to update this plan + the campaign tracker and to run the detail-pass on parameterized
> briefs.

## §1 — The brief inventory (all authored)

| Wave | Brief file | Fidelity | Status |
|---|---|---|---|
| Runtime validation | `CLAUDECODE_BRIEF_RETRIEVAL_RUNTIME_VALIDATION` | full (read-only) | READY |
| D0.5 cleanup | `CLAUDECODE_BRIEF_RETRIEVAL_D0_5_CLEANUP` | full | READY |
| D1 contract+gate | `CLAUDECODE_BRIEF_RETRIEVAL_D1_CONTRACT` | full | READY |
| D2 router | `CLAUDECODE_BRIEF_RETRIEVAL_D2_ROUTER` | full | READY |
| D3 grounding spine | `CLAUDECODE_BRIEF_RETRIEVAL_D3_GROUNDING_SPINE` | full | READY |
| D4 graph | `CLAUDECODE_BRIEF_RETRIEVAL_D4_GRAPH` | full | READY |
| D-PROFILES + MARO | `CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO` | parameterized | READY (detail-pass pending D8) |
| D5 fan-out | `CLAUDECODE_BRIEF_RETRIEVAL_D5_FANOUT` | parameterized | READY (detail-pass pending D1+runtime+manifest) |
| D6 synergy + D7 channels | `CLAUDECODE_BRIEF_RETRIEVAL_D6_D7_CHANNELS` | parameterized | READY (detail-pass pending D5+MARO) |
| D8 eval + seal | `CLAUDECODE_BRIEF_RETRIEVAL_D8_EVAL_SEAL` | parameterized | READY (detail-pass pending D1–D7) |

Design references (not briefs): the approach plan (v1.4), D0 foundations (v1.1), the 4 D-GROUNDTRUTH
deliverables, and the code-validation register (v1.1).

## §2 — The dependency-ordered runway

```
PHASE 0 — GROUND  (no architecture changes; clears reality + debt)
  S0  Runtime validation (read-only)  ──┐ confirms data-plane reality + contamination blast radius
  S0.5 D0.5 cleanup (manifest+tier)   ──┘ single authoritative catalog + no tier residue
        │
PHASE 1 — FOUNDATION  (the contract everything conforms to)
  S1  D1 contract + chart-agnostic CI gate  ── freezes the surface; retrofits clean registry
        │  (convergence migration of lib/retrieve begins here, under reverse-citation gate)
        ▼
PHASE 2 — CROSS-CUTTING SKELETON  (can partly parallelize)
  S2  D2 router        ─┐
  S3  D3 grounding spine ├─ the route + grounding + graph backbone
  S4  D4 graph          ─┘
        ▼
PHASE 3 — MODEL + ASSETS  (parallelizable; both feed integration)
  S5  D-PROFILES + MARO  (parameterized; values hardened later by D8)
  S6  D5 fan-out         (parameterized; per-layer sub-waves D5.0…D5.5)
        ▼
PHASE 4 — INTEGRATION
  S7  D6 synergy + D7 channels  (compose roster; wire both channels over MARO; remediate old MCP tools)
        ▼
PHASE 5 — SEAL
  S8  D8 eval + governance + seal  (gates the seal; hardens profiles; red-team; close)
```

**Hard dependencies:** D1 precedes everything that declares a surface. D3+D4 precede D5 (assets bind to
grounding+graph). D-PROFILES+D5 precede D6/D7. All precede D8. **Soft/parallel:** D2/D3/D4 can overlap;
D-PROFILES and D5 are largely independent and can run in parallel.

## §3 — Consume / produce per wave (the data contract between sessions)

- **Runtime** consumes the design; produces the runtime findings register (data-plane truths + contamination
  blast radius) → feeds D5 (which assets have data) + D6/D7 (remediation scope).
- **D0.5** produces the single authoritative manifest + tier-free MCP resources → feeds D1, D5.
- **D1** produces the frozen RetrievalSurface contract + CI gate → feeds D2–D8 (everything conforms).
- **D2/D3/D4** produce router + grounding spine + graph tool → feed D5 (assets bind to them) + D6.
- **D-PROFILES** produces MARO core + RETRIEVAL_MODEL_PROFILES v1 → feeds D6/D7; hardened by D8.
- **D5** produces the full tool roster → feeds D6/D7.
- **D6/D7** produce the composed synergy + both-channel surface → feeds D8.
- **D8** produces the eval harness + hardened profiles + seal → closes the master design.

## §4 — Two policies that bind every wave

**P1 — Parameterized-brief detail-pass.** The four parameterized briefs (D-PROFILES, D5, D6/D7, D8) carry §0
`[resolved from …]` markers. Before executing such a wave, Cowork runs a quick detail-pass that fills those
markers from the now-available upstream outputs, bumping the brief. A parameterized brief is NOT executed at v1
without its detail-pass — that's the mechanism that keeps far waves accurate instead of falsely precise.

**P2 — Reverse-citation destructive-safety gate.** ANY removal/retirement (lib/retrieve retirement,
manifest-duplicate deletion, tier-variant removal, old-MCP-tool remediation) MUST first grep the live codebase
for active citations of every target, reclassify anything still cited as keep-or-repoint, and ship the citation
report in the PR. No deletion on faith (per the prior tables-wiped incident).

## §5 — Recommended run order (you choose; this is the recommendation)

1. **S0 Runtime validation** (read-only) — ground reality first; cheap, safe, informs everything.
2. **S0.5 Cleanup** — clear the manifest+tier debt so the catalog is unambiguous.
3. **S1 D1 contract+gate** — the foundation; begin lib/retrieve convergence under P2.
4. **S2–S4 router / grounding / graph** — the backbone (D2, D3, D4; D3+D4 before heavy D5).
5. **S5 D-PROFILES** + **S6 D5 fan-out** — in parallel where capacity allows (detail-pass each first).
6. **S7 D6/D7** — compose + wire both channels + remediate old MCP tools (detail-pass; P2 on remediation).
7. **S8 D8** — eval, harden profiles, governance close, red-team, seal.

## §6 — Governance integration

Each wave is a closed-artifact-per-session (one wave, one PR, frontmatter-bearing). Red-team cadence: every
third session + the macro-phase close before the D8 seal. Each session emits the session_open/close per the
project templates; CURRENT_STATE + the campaign tracker update at each close. The chart-agnostic CI gate +
parity_check + drift/schema validators run on every PR.

## §7 — Open cross-cutting items (tracked, not blocking the early waves)

- Acharya validation of the traversal model (affects D5 umbrella/drill hierarchy where reading-sequence-
  dependent) — pursue in parallel; D5 proceeds on the research-grounded v1 meanwhile.
- The runtime data-population truth (writers exist; has data been built per chart) — S0 settles it.

## §8 — Parallel execution shape (native ruling; governed by the coordination brief)

The campaign runs as a **serial spine with two fan-out points.** Parallelism is governed by
`CLAUDECODE_BRIEF_RETRIEVAL_PARALLEL_COORDINATION` — read it before spawning any parallel agent.

```
PHASE 0 (serial) ─ runtime → cleanup
        │
   D1 (serial) ── FREEZE + MERGE the contract  ← the chokepoint; nothing parallelizes before this
        │
  ┌─────┴─────────────── FAN-OUT 1 (parallel agents, isolated branches) ───┐
  D2 router        D3 grounding spine        D4 graph
  └─────┬──────────────────────────────────────────────────────────────────┘
        │  → integration smoke (router→grounding→graph, 2 charts)
  ┌─────┴─────────────── FAN-OUT 2 (parallel agents) ──────────────────────┐
  D-PROFILES          D5 fan-out  (its own layer sub-waves L0∥L1∥L2 parallel)
  └─────┬──────────────────────────────────────────────────────────────────┘
        │  → roster-completeness smoke + F1/chart-agnostic gates
  D6/D7 (serial — composes the roster, wires both channels)
        │
  D8 (serial — evaluates + seals)
```

**The three gates (from the coordination brief), non-negotiable for parallel work:**
- **A — No-shared-file / escalate-don't-edit:** parallel waves own only new files; the frozen contract
  (`registry/types.ts`) and central `registry/index.ts` are off-limits; a needed contract change STOPS and
  escalates (DG3 discipline).
- **B — Post-merge prod-verify:** worktree-green ≠ done; ACs tagged `[verify-against: prod]`; verify after
  merge against live env (the worktree-complete-only scar).
- **C — Reverse-citation on any removal:** citation report in every destructive PR.

**Stays serial:** Phase 0, D1, D6/D7, D8. **Parallelizes:** the two fan-outs above, under the three gates.

This captures the real time-compression (the two fan-outs, especially D5's layer sub-waves and D-PROFILES∥D5)
while placing the guardrails exactly where the project's past parallel failures occurred.

*End of RETRIEVAL_IMPLEMENTATION_MASTER_PLAN v1.1 — the parallel-enabled execution runway. Cowork briefs,
Claude Code builds (serial spine + two parallel fan-outs under the coordination brief), results return for
detail-pass + tracker update.*

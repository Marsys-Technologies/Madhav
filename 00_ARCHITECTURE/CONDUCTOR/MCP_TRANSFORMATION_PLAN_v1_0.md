---
artifact: MCP_TRANSFORMATION_PLAN_v1_0.md
status: ACTIVE
version: 1.0
authored_by: Claude (Cowork session, Opus 4.7)
authored_on: 2026-05-22
project_name: MCP Transformation
parent_architecture: 00_ARCHITECTURE/MCP_ARCH_v3_PROPOSAL_2026-05-22.md (v3.1)
parent_perf_brief: 00_ARCHITECTURE/MCP_PERF_SYSTEM_BRIEF_2026-05-22.md (v3.1)
parent_memory: 00_ARCHITECTURE/PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md
parent_v3_1_0_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md
audience: Conductor instances + operator
implementation_surface: Claude Code extension in Google Antigravity IDE (per PROJECT_MEMORY §2)
disposition: single source of truth for parallel execution of MCP Transformation
---

# MCP Transformation — Master Execution Plan

The MCP Transformation is the v3.1 rebuild of the MARSYS-JIS MCP server. Architecture and perf-system briefs are sealed at v3.1. This document is the *operational spine* that turns those briefs into 17 sub-phase sessions executing across 6 parallel worktrees over ~5 wall-clock days under Conductor orchestration.

**Implementation surface: Claude Code extension in Google Antigravity IDE.** Per `PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md §2`. Every Conductor and every spawned sub-agent runs as a Claude Code instance in Antigravity.

---

## §1 — Phase + session inventory

| Phase | Sub-phases | Count | What ships |
|---|---|---|---|
| **v3.1.0 Foundation** | S1, S2, S3, S4, S5, S6 | 6 | Code fixes, bundles+SSE, 5 resources, perf+audit system, operator dashboard, tier-conditioned house-rules, foundation sealing |
| **v3.2 Classical grounding** | S1, S2, S3, S4, S5 | 5 | BPHS indexed, Jaimini Sutram + KP Reader indexed, Tajaka Neelakanthi indexed, multi-school tables (Jaim + KP), Tajaka tables + convergence index |
| **v3.3 Depth backfill** | S1, S2, S3, S4 | 4 | shadbala + ashtakavarga; bhava_bala + kp_* + upagraha; Tajaka varshphal; sealing |
| **v3.4 Epistemic + red-team** | S1, S2 | 2 | MSR signal-grounding pass (419 ungrounded → grounded); red-team + final sealing |
| **TOTAL** | | **17** | |

Briefs are at `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_{phase}_S{n}_v1_0.md` (one per sub-phase). The v3.1.0 foundation brief is the existing `CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md` which covers S1–S6 collectively; per-sub-phase break-outs are at `CLAUDECODE_BRIEF_MCPT_V310_S{1..6}_v1_0.md`.

---

## §2 — Dependency graph

```
                ┌──────────────────────────────────────────────────┐
                │ v3.1.0 Foundation (WT-A: feature/mcpt-foundation) │
                └──────────────────────────────────────────────────┘

                v3.1.0-S1 (code fixes)
                          │
              ┌───────────┼───────────┐
              ↓           ↓           ↓
        v3.1.0-S2  v3.1.0-S3   v3.1.0-S4
        (bundles)  (resources) (perf+audit)
              │           │           │
              └─────┬─────┴───────────┘
                    ↓
              v3.1.0-S5 (dashboard)
                    ↓
              v3.1.0-S6 (foundation seal → merge to feature/mcpt-final)


   ┌──────────────────────────────────────────────────────────┐
   │ v3.2 Classical grounding (WT-B, WT-C, WT-D — parallel)    │
   └──────────────────────────────────────────────────────────┘

   v3.2-S1 (BPHS)        ─────────────────────────┐
   v3.2-S2 (Jaim+KP)     ─────────────────────────┤
   v3.2-S3 (Tajaka text) ─────────────────────────┤
                                                  ↓
                                          v3.2-S4 (multi-school tables Jaim+KP)
                                                  ↓
                                          v3.2-S5 (Tajaka tables + convergence)
                                                  ↓ (merge to feature/mcpt-final)


   ┌──────────────────────────────────────────────────────────┐
   │ v3.3 Depth backfill (WT-E: feature/mcpt-depth)            │
   └──────────────────────────────────────────────────────────┘

   v3.3-S1 (shadbala + ashtakavarga)
                  ↓
   v3.3-S2 (bhava_bala + kp_* + upagraha)
                  ↓
   v3.3-S3 (Tajaka varshphal) — depends on v3.2-S3 + v3.2-S5 (cross-WT)
                  ↓
   v3.3-S4 (depth sealing → merge to feature/mcpt-final)


   ┌──────────────────────────────────────────────────────────┐
   │ v3.4 Epistemic + red-team (WT-F + FINAL)                  │
   └──────────────────────────────────────────────────────────┘

   v3.4-S1 (MSR signal-grounding pipeline) — long-running batch in WT-F (feature/mcpt-grounding)
                  ↓ (merge to feature/mcpt-final)

   v3.4-S2 (red-team + FINAL seal, merge to main) — on feature/mcpt-final, after EVERYTHING ELSE merged
```

**Cross-worktree dependencies** (the only ones that cross branch boundaries):
- `v3.3-S3` depends on `v3.2-S3` (Tajaka text indexed) AND `v3.2-S5` (Tajaka tables present). Resolved by waiting for v3.2-S3 + v3.2-S5 to merge into `feature/mcpt-final`, then `feature/mcpt-depth` rebases against `feature/mcpt-final` before v3.3-S3 starts.
- `v3.4-S2` depends on EVERY other session sealing into `feature/mcpt-final` first. v3.4-S2 runs solo against the fully-merged branch.

---

## §3 — Wave structure (5-day timeline, 6 parallel worktrees)

| Wave | Day | WT-A (FDN) | WT-B (BPHS) | WT-C (JK) | WT-D (TAJ) | WT-E (DPT) | WT-F (GRD) |
|---|---|---|---|---|---|---|---|
| **0** | (now) | source data staging + worktree setup + brief authoring | | | | | |
| **1** | 1 | v3.1.0-S1 | v3.2-S1 | v3.2-S2 | v3.2-S3 | v3.3-S1 | v3.4-S1 start |
| **2** | 2 | v3.1.0-S2 \| S3 \| S4 (sub-agent fan-out) | (idle) | v3.2-S4 | (idle) | v3.3-S2 | v3.4-S1 cont |
| **3** | 3 | v3.1.0-S5 | (idle) | v3.2-S5 | rebase + v3.3-S3 | (handover to D) | v3.4-S1 cont |
| **4** | 4 | v3.1.0-S6 seal → merge to FINAL | | merge v3.2 to FINAL | | v3.3-S4 seal → merge to FINAL | v3.4-S1 finish → merge to FINAL |
| **5** | 5 | (idle) | (idle) | (idle) | (idle) | (idle) | (idle) — Final wave runs solo |
| **FINAL** | 5 | **v3.4-S2 red-team + final seal on `feature/mcpt-final` → merge to main** | | | | | |

**Day 1 is the heaviest** — six worktrees execute simultaneously. Most sessions are 2–6 hours of autonomous Conductor-driven work each. By end of Day 1, six branches have a first commit cycle landed.

**Day 2 is the merge-friction day** — v3.1.0 sub-agents fan out inside WT-A; cross-worktree work converges. v3.4-S1 grounding pipeline batches in background.

**Day 3 is the cross-WT dependency day** — v3.3-S3 waits for v3.2 Tajaka work to merge to FINAL, then rebases.

**Day 4 is the wave-collection merge day** — each worktree's terminal session merges into `feature/mcpt-final`. Sequential merges to avoid conflict storms.

**Day 5 is the red-team + final seal** — runs on the fully-merged FINAL branch; merges to main.

---

## §4 — Worktree allocation

| WT | Suffix | Path | Branch | Conductor queue | Owns sub-phases |
|---|---|---|---|---|---|
| **A** | FDN | `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN` | `feature/mcpt-foundation` | `session_queue_MCPT_WT_A.yaml` | v3.1.0-S1..S6 |
| **B** | BPHS | `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-BPHS` | `feature/mcpt-bphs` | `session_queue_MCPT_WT_B.yaml` | v3.2-S1 |
| **C** | JK | `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-JK` | `feature/mcpt-jaim-kp` | `session_queue_MCPT_WT_C.yaml` | v3.2-S2, v3.2-S4 |
| **D** | TAJ | `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-TAJ` | `feature/mcpt-tajaka` | `session_queue_MCPT_WT_D.yaml` | v3.2-S3, v3.2-S5, (rebase) v3.3-S3 |
| **E** | DPT | `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT` | `feature/mcpt-depth` | `session_queue_MCPT_WT_E.yaml` | v3.3-S1, v3.3-S2, v3.3-S4 |
| **F** | GRD | `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-GRD` | `feature/mcpt-grounding` | `session_queue_MCPT_WT_F.yaml` | v3.4-S1 |
| **FINAL** | FIN | `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FIN` | `feature/mcpt-final` | `session_queue_MCPT_FINAL.yaml` | v3.4-S2 (sole entry) |

`feature/mcpt-final` is the wave-collector branch; everyone merges into it before v3.4-S2.

---

## §5 — Migration number reservations (lock these now)

Parallel worktrees cannot pick migration numbers ad-hoc — collisions break the migration chain. Numbers reserved:

| Migration # | Owner WT | Sub-phase | Subject |
|---|---|---|---|
| 072 | A | v3.1.0-S2 | `mcp_bundle_cache` (5-min content-addressable cache) |
| 073 | A | v3.1.0-S4 | `tool_execution_log` extensions (5 new columns) |
| 074 | A | v3.1.0-S4 | `mcp_audit_findings` + `audit_job_runs` tables |
| 075 | A | v3.1.0-S4 | `mcp_prediction_outcomes` + `mcp_predictions` extensions |
| 076 | A | v3.1.0-S4 | `data_source_expected` + `tool_caveats` tables |
| 077 | A | v3.1.0-S5 | `mcp_alerts_config` + `tool_registry` tables |
| 078 | C | v3.2-S4 | Multi-school table schema extensions (Jaimini + KP columns) |
| 079 | D | v3.2-S5 | Multi-school Tajaka columns + `school_convergence_index` materialized view |

**Numbers 080+ are RESERVED for v3.3 / v3.4** if any backfill needs schema changes (most do not — they UPDATE existing `chart_facts`, `msr_signals`).

Every brief explicitly names its migration number. Conductor gate commands verify the migration file exists at the expected number before passing.

---

## §6 — Source-data manifest (Wave 0 — operator action)

Before Wave 1 kickoff, the native stages source files in `00_ARCHITECTURE/SOURCE_DATA/` (git-ignored; large files):

| Subdirectory | Source files needed | Used by | Notes |
|---|---|---|---|
| `SOURCE_DATA/classical_texts/BPHS/` | BPHS PDF or cleaned-text per chapter (1–30 minimum) | v3.2-S1 (BPHS indexing) | Native procures; cleaned-text preferred over PDF (saves OCR step) |
| `SOURCE_DATA/classical_texts/Jaimini_Sutram/` | Jaimini Sutram full text (4 padas, 4 adhyayas) | v3.2-S2 (Jaim indexing) | |
| `SOURCE_DATA/classical_texts/KP_Reader/` | KP Reader Volumes 1–6 (PDFs OK; OCR step accepted) | v3.2-S2 (KP indexing) | Highest OCR effort |
| `SOURCE_DATA/classical_texts/Tajaka_Neelakanthi/` | Tajaka Neelakanthi (any reliable edition) | v3.2-S3 | Single text; small |
| `SOURCE_DATA/multi_school_seeds/` | Author-curated initial multi-school stance rows (Jaim karaka mappings, KP cuspal grid samples, Tajaka year-lord lookup table) | v3.2-S4, v3.2-S5 | Native + Cowork authoring; not pure data ingest |
| `SOURCE_DATA/jagannatha_hora_exports/` | Jagannatha Hora chart export with full shadbala / ashtakavarga / KP / upagraha tables for native's chart | v3.3-S1, v3.3-S2 | Native exports; format: CSV or screenshot+OCR |
| `SOURCE_DATA/varshphal_tables/` | Tajaka varshphal year-lord + muntha + saham tables for native's chart by year | v3.3-S3 | Computable from Tajaka rules; can be derived if source data not directly available |

**Gate:** the SETUP_WORKTREES_MCPT.sh script verifies these subdirectories exist (even if empty) before creating worktrees. If a subdirectory is missing critical content, the corresponding worktree's Conductor halts on its first session with `MISSING_SOURCE_DATA`.

---

## §7 — Cross-worktree merge protocol

Merges happen in a strict order at each wave's terminal sessions:

1. **Wave 4 merge order (sequential, on `feature/mcpt-final`):**
   1. WT-A merges first: `feature/mcpt-foundation` → `feature/mcpt-final`. This brings in the v3 tool surface, migrations 072–077, perf system, dashboard.
   2. WT-C merges next: `feature/mcpt-jaim-kp` → `feature/mcpt-final`. Brings migration 078 + Jaim + KP indexing + multi-school table data.
   3. WT-D merges next: `feature/mcpt-tajaka` → `feature/mcpt-final`. Brings migration 079 + Tajaka content.
   4. WT-B merges next: `feature/mcpt-bphs` → `feature/mcpt-final`. Pure content; should be clean.
   5. WT-E merges next: `feature/mcpt-depth` → `feature/mcpt-final`. v3.3-S3 already rebased; should be clean.
   6. WT-F merges last (before FINAL): `feature/mcpt-grounding` → `feature/mcpt-final`. MSR data updates; should be clean.

2. **Per-merge gate.** Before each merge, the Conductor runs:
   - `git fetch origin feature/mcpt-final && git rebase origin/feature/mcpt-final`
   - Migration number conflict check (`ls platform/supabase/migrations/ | sort -n | uniq -d` must return empty)
   - Smoke test: `npm test --workspace=platform-mcp` must pass
   - Full audit: `python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py` must exit 0

3. **Merge action.** Conductor runs `git checkout feature/mcpt-final && git merge --no-ff feature/mcpt-{branch} -m "MCPT: merge {branch} → final"` and pushes.

4. **Conflicts.** If a rebase or merge conflicts, the Conductor halts with `MERGE_CONFLICT_NEEDS_HUMAN`. Operator resolves in Cowork or directly in Antigravity Claude Code, then resumes.

5. **FINAL merge to main.** v3.4-S2 (red-team + sealing) runs against `feature/mcpt-final`. After red-team passes (0 class-1 findings required), v3.4-S2's terminal commit is the merge into main. This is the **only** entry with `requires_human_approval: true` — the native makes the final call.

---

## §8 — Velocity levers (mandatory; already in PROJECT_MEMORY)

1. `requires_human_approval: false` on every queue entry except v3.4-S2.
2. `--dangerously-skip-permissions` on every Claude Code sub-agent spawn (specified in the Conductor kickoff prompt's spawn command).
3. Per-session autonomous commit + push to the feature branch.
4. Per-wave auto-PR creation; auto-merge after the wave-collector gate passes.
5. Per-sub-agent context budget ~200K; brief scope kept tight enough to fit.
6. Conductor halts after 20 sub-agents per chat (ORCHESTRATOR HANDOFF banner); operator re-pastes kickoff in fresh chat. Plan for ~2 Conductor chats per worktree across the run.
7. Pre-allocated migration numbers (§5) — no run-time number assignment.
8. Pre-authored briefs (no `requires_brief_authoring: true` halts after Wave 0 closes).

---

## §9 — Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Migration number conflict between parallel WTs | Low | High | §5 number reservations; per-merge migration check |
| R2 | `platform-mcp/src/server.ts` tool registry conflict between v3.1.0-S2/S3/S4 sub-agents | Medium | Medium | WT-A owns registry; sub-agents append in alphabetical order; merge resolution scripted |
| R3 | Cross-WT data dependency (v3.3-S3 waits on v3.2-S3 + v3.2-S5) | Certain | Low (planned) | §2 dependency map; WT-D rebases against `feature/mcpt-final` after v3.2-S5 merges |
| R4 | Sub-agent context overflow mid-session | Medium | Low (one session) | Brief scope tight; on overflow Conductor halts that one queue; other 5 WTs continue; operator resumes with continuation |
| R5 | OCR quality on classical-text PDFs (KP Reader especially) | High | Medium | Wave 0 source-data prep includes manual cleaning; brief allows operator-flagged "best-effort indexing" if OCR is degenerate |
| R6 | Red-team class-1 finding at v3.4-S2 forces rework | Medium | High | Accepted; this is the point of red-team. Rework tracked as v3.5 follow-up; v3.4-S2 halt opens DISAGREEMENT_REGISTER entry |
| R7 | `--dangerously-skip-permissions` allows agent damage outside worktree | Low | High | Each worktree isolated; agents cannot reach main directly (no push permission to main on feature branches); worst case = discard branch |
| R8 | Auto-merge of broken code | Low | High | Per-session smoke gate + per-wave full-CI gate before final-branch merge. Both mandatory |
| R9 | Antigravity IDE chat window limit (per-chat sub-agent cap) | Certain | Low | §8 lever 6: re-paste kickoff in fresh chat at handoff banner |
| R10 | Cowork session accidentally edits code during planning iteration | Medium | Medium | PROJECT_MEMORY §2 + this plan §7 explicit; Cowork sessions check `must_not_touch` before any file write |

---

## §10 — Halt-response runbook

When a Conductor halts, it appends to `CONDUCTOR_HALT_LOG.md` with the failure class. Operator's response per class:

| Failure class | What it means | Operator action |
|---|---|---|
| `GATE_FAILED` | Sub-agent's gate command exited non-zero | Read sub-agent's last commit + gate output. Fix in Claude Code, push, `RESUME <session_id>` |
| `MERGE_CONFLICT_NEEDS_HUMAN` | Auto-rebase/merge hit a conflict | Resolve in Claude Code (the implementation surface, per PROJECT_MEMORY §2), commit, push, `RESUME <session_id>` |
| `MIGRATION_CONFLICT` | Two WTs claimed same migration number | Re-number per §5; rebase; `RESUME <session_id>` |
| `MISSING_SOURCE_DATA` | A v3.2 or v3.3 brief expected a source file not present | Stage the file under `SOURCE_DATA/`; `RESUME <session_id>` |
| `SUB_AGENT_CONTEXT_OVERFLOW` | Sub-agent ran out of 200K context mid-session | Sub-agent halted mid-work; check what's committed; spawn a continuation sub-agent with narrower scope; `RESUME <session_id>` |
| `HALT_NEEDS_HUMAN` | Sub-agent encountered an architectural ambiguity it cannot resolve autonomously | Read sub-agent's summary; make the decision in Cowork (planning surface); update brief; `RESUME <session_id>` |
| `ORCHESTRATOR_HANDOFF` | Conductor itself hit 20-sub-agent context budget | Open fresh Claude Code chat in Antigravity (same worktree), re-paste kickoff prompt; Conductor resumes from queue position |
| `RED_TEAM_CLASS_1` | v3.4-S2 found a class-1 issue | Native makes the call: rework (v3.5) or accept-with-disagreement |

---

## §11 — Per-worktree Conductor kickoff prompts

Authored at `00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_WT_{A,B,C,D,E,F,FINAL}.md`. Each is a single paste-block intended for the Claude Code extension in Antigravity IDE. Operator opens 7 Antigravity chats (one per worktree, FINAL chat opens after Wave 4) and pastes the respective kickoff prompt. The Conductor inside each chat reads its queue and begins.

**Wave 1 kickoff order:** open 6 Antigravity chats (one per worktree A–F) in parallel, paste 6 kickoffs in parallel, all six Conductors begin within minutes of each other. FINAL chat opens after Wave 4 closes.

---

## §12 — Strategy 3: meta-Conductor (recommended operator mode)

§3 above describes the distributed wave model: one Antigravity Claude Code chat per worktree, six chats running in parallel, operator orchestrates worktree-to-worktree dependencies by opening chats in order. That model preserves clean separation per worktree but demands 7 chat opens across 4 days plus mental tracking of which worktree is doing what.

**The meta-Conductor mode collapses that to 2 chats for the entire project.**

| Mode | Chats operator opens | Cross-WT coordination | Wall-clock |
|---|---|---|---|
| **Distributed (§3)** | 7 (one per worktree + FINAL) | Operator-managed (open WT-X chat after WT-Y merges) | ~3.5–4 days |
| **Meta-Conductor (§13)** | **2** (META chat + WT-F sibling) | Conductor-managed (META reads queues across worktrees) | ~3 days (faster — no operator-action lag between waves) |

### How meta-mode works

One Antigravity Claude Code chat opens at `/Users/Dev/Vibe-Coding/Apps/Madhav` (the main repo, not any worktree). The operator pastes `00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_META.md`. That kickoff turns the chat into a *meta-Conductor* that:

1. Reads all 6 in-scope queue files (WT-A, B, C, D, E + FINAL — skips WT-F).
2. Builds a unified dependency-resolved schedule across worktrees, honoring both `depends_on` (same-WT) and `cross_wt_dependencies` (cross-WT).
3. Spawns sub-agents in **batch parallelism**: up to 5 concurrent sub-agents per batch, one per distinct worktree (never two into the same worktree — git index contention). Each sub-agent prompt is prefixed with `cd <worktree_path>` so it operates in the right tree.
4. Runs each session's gate command in the meta chat after the sub-agent returns; updates the queue's status field on PASS; appends to `CONDUCTOR_LOG_MCPT_META.md` (consolidated log) and `CONDUCTOR_HALT_LOG_MCPT_META.md`.
5. At v3.4-S2 (the sole human-gated entry), halts with `REQUIRES_NATIVE_APPROVAL`; operator replies `APPROVE_MAIN_MERGE`; meta spawns the push-to-main + deploy + smoke sub-agent.

### Why WT-F runs as a sibling chat

v3.4-S1's MSR grounding pipeline is ~8 hours wall-clock (longest single session in the project). If included in the meta-Conductor's batch scheduling, it would gate the meta's next batch for 8 hours since Claude Code's Task tool blocks until all parallel sub-agents return. Solution: WT-F runs in a separate Antigravity chat (`MadhavMCPT-GRD` workspace, paste `KICKOFF_MCPT_WT_F.md`). It executes independently. The meta-Conductor doesn't spawn its sub-agent but does verify v3.4-S1's merge commit lands on `feature/mcpt-final` before allowing v3.4-S2 to start.

### Operator workflow

**Day 1 morning** — open 2 chats, total ~2 minutes of operator setup:

1. **META chat:** Antigravity workspace at `/Users/Dev/Vibe-Coding/Apps/Madhav`. Open Claude Code chat with `--dangerously-skip-permissions`. Paste `KICKOFF_MCPT_META.md`. Walk away.
2. **WT-F chat:** Antigravity workspace at `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-GRD`. Open Claude Code chat with `--dangerously-skip-permissions`. Paste `KICKOFF_MCPT_WT_F.md`. Walk away.

**Day 1 afternoon through Day 3** — operator active touchpoints:
- Stage source data progressively into `00_ARCHITECTURE/SOURCE_DATA/`. As each subdir fills, type `RESUME <session_id>` in META chat for the corresponding halted session.
- Re-paste META kickoff in a fresh Antigravity chat on ORCHESTRATOR_HANDOFF (expected: 0–1 times, worst case 2; the META chat's context fills after ~18-20 sub-agents, and the project has ~16 in meta scope).

**Day 3** — final touchpoint:
- At v3.4-S2's `REQUIRES_NATIVE_APPROVAL` halt, review the red-team output + sealing artifact preview + merge diff summary; reply `APPROVE_MAIN_MERGE`. Project closes.

### When to fall back to distributed mode (§3)

The per-worktree kickoffs (`KICKOFF_MCPT_WT_{A..F}.md`) remain in place as fallbacks. Use them if:

- Meta-mode hits persistent ORCHESTRATOR_HANDOFF storms (unlikely — total sub-agent count fits the budget).
- You want to debug a single worktree in isolation (open that WT's chat, paste its kickoff, run just its queue).
- The meta-Conductor itself fails for any reason mid-project (e.g., Antigravity bug). Distributed mode is recoverable from any queue state because each per-WT queue's `status` field is the source of truth.

### Logs in meta-mode

| Log | Path | Content |
|---|---|---|
| Meta consolidated log | `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_LOG_MCPT_META.md` | Every session that META spawned, with result, timestamp, worktree, commits, gate output |
| Meta halt log | `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_HALT_LOG_MCPT_META.md` | Open + resolved halts in meta scope |
| WT-F sibling logs | `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-GRD/00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_LOG.md` and `CONDUCTOR_HALT_LOG.md` | v3.4-S1's standalone run history |

### Critical invariants in meta-mode

- Meta-Conductor never edits application code. Only its sub-agents do.
- Meta-Conductor never spawns concurrent sub-agents into the same worktree (git index contention).
- Meta-Conductor never spawns WT-F's v3.4-S1 (sibling chat owns it).
- Meta-Conductor never skips a gate. Sub-agent says PASS but gate exits non-zero → HALT.
- v3.4-S2 is the ONLY entry that requires native approval. Everything else proceeds autonomously.

---

## §13 — One-paragraph TL;DR

MCP Transformation is 17 sessions across 4 phases executing in 6 parallel worktrees over ~3–4 wall-clock days under Conductor orchestration in Claude Code (Antigravity IDE) — Cowork is for planning, not implementation. **Two execution modes are supported: meta-Conductor (§12, recommended — 2 chats: META + WT-F sibling) and distributed (§3 — 7 chats, one per worktree).** Wave 0 stages source data and runs `SETUP_WORKTREES_MCPT.sh` to create six branches + worktrees. In meta-mode (recommended), the operator opens 2 Antigravity Claude Code chats Day 1 morning: META at the main Madhav repo (paste `KICKOFF_MCPT_META.md`; orchestrates 16 of 17 sessions across 5 worktrees + FINAL) and WT-F at `MadhavMCPT-GRD` (paste `KICKOFF_MCPT_WT_F.md`; runs v3.4-S1's 8-hour MSR-grounding pipeline solo). META spawns sub-agents in batch parallelism (up to 5 concurrent, one per distinct worktree; never two into the same worktree) with `cd <worktree_path>` prefixes; resolves cross-worktree dependencies internally by reading all 6 in-scope queue files. Distributed mode (§3) is the fallback / debugging path: per-worktree kickoffs (`KICKOFF_MCPT_WT_{A..F}.md`) remain in place and can be used to run any single worktree in isolation. The dependency spine is the same in both modes: v3.1.0-S1 → {S2,S3,S4} → S5 → S6 in WT-A; v3.2-{S1,S2,S3} → S4 → S5 (which also wave-collector merges all 3 v3.2 branches into `feature/mcpt-final`); v3.3-S1 → S2 → S3 (cross-WT-waits on v3.2-S5) → S4 in WT-E; v3.4-S1 standalone in WT-F; v3.4-S2 solo in FINAL after every other terminal merge lands, with native approval (the sole human-gated entry) gating the merge to main. Migrations 072–079 are pre-reserved to eliminate conflicts; briefs are pre-authored to eliminate brief-authoring halts; `--dangerously-skip-permissions` is set on every Claude Code chat at launch for autonomous execution. Expected ORCHESTRATOR_HANDOFF events in meta-mode: 0–1 (worst case 2). Total: 17 sessions → 3 days wall-clock at meta-mode ≈ 82% reduction vs sequential 17 days, ≈ 25% faster than distributed mode (no operator-action lag between waves).

---

*End of MCP_TRANSFORMATION_PLAN_v1_0.md. Status ACTIVE. Conductor instances read at start. Operator references for halt responses + wave gating. Closes when v3.4-S2 merges to main; archives as superseded-as-complete at that point.*

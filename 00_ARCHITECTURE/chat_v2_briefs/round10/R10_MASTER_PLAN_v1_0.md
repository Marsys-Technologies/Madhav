---
canonical_id: R10_MASTER_PLAN
version: 1.0
status: CURRENT
owner: Abhisek Mohanty
branch: chat-v2/round10
worktree: /Users/Dev/Vibe-Coding/Apps/Panchang
execution: sequential-single-stream
authored: 2026-05-20
---

# Chat V2 Round 10 — Master Plan v1.0

## Scope

R10 is the fourth and final polish+capability wave of the Chat V2 Big Bang workstream, running as a **single sequential stream** inside the existing Panchang worktree on branch `chat-v2/round10`.

R10 contains 21 sessions divided into two groups:
- **Group P (Polish/Perf)** — X-S0 through X-S11 (12 sessions): UX improvements, performance, visual polish, low-risk capability additions.
- **Group C (Capability/Backend)** — Y-S1 through Y-S9 (9 sessions): citation enhancement, streaming tuning, advanced UI behaviors, schema-touching capabilities.

Group P runs first; Group C runs second. Within each group, lighter/safer sessions precede risk-managed ones. Default-false sessions (Y-S5 UX risk, Y-S9 cost risk) run last.

R10 is committed directly to `chat-v2/round10` (no sub-branch). After all 21 sessions complete, a single PR to main is opened.

## Sessions Table (Execution Order)

| # | Session ID | Brief | Flag | Default | Client-side | Risk |
|---|-----------|-------|------|---------|-------------|------|
| 1 | X-S0 | nim-degraded-buildarg | FLAGLESS cleanup | — | yes (deploy.yml only) | minimal |
| 2 | X-S1 | camera-capture-mobile | FLAGLESS | — | yes | low |
| 3 | X-S2 | recall-last-prompt | FLAGLESS | — | yes | low |
| 4 | X-S3 | citation-star-persistence | FLAGLESS | — | yes | low |
| 5 | X-S4 | still-working-indicator | FLAGLESS | — | yes | low |
| 6 | X-S5 | skeleton-loaders | FLAGLESS | — | yes | low |
| 7 | X-S6 | auto-scroll-discipline | MARSYS_FLAG_R10_SCROLL_DISCIPLINE | true | yes (NEXT_PUBLIC) | medium |
| 8 | X-S7 | font-size-control | FLAGLESS | — | yes | low |
| 9 | X-S8 | selective-share | MARSYS_FLAG_R10_SELECTIVE_SHARE | true | no (server-side) | medium |
| 10 | X-S9 | print-friendly-share | FLAGLESS | — | no | low |
| 11 | X-S10 | tables-sort-filter-csv | MARSYS_FLAG_R10_INTERACTIVE_TABLES | true | yes (NEXT_PUBLIC) | medium |
| 12 | X-S11 | mermaid-diagrams | MARSYS_FLAG_R10_MERMAID | true | yes (NEXT_PUBLIC) | medium |
| 13 | Y-S1 | citation-hover-snippet | FLAGLESS | — | yes | low |
| 14 | Y-S2 | citation-freshness-badge | MARSYS_FLAG_R10_CITATION_FRESHNESS | true | yes (NEXT_PUBLIC) | medium |
| 15 | Y-S6 | branch-on-regen | FLAGLESS | — | yes | low |
| 16 | Y-S7 | search-mode-toggle | FLAGLESS (UI only) | — | yes | low |
| 17 | Y-S8 | validator-per-gate-expander | MARSYS_FLAG_R10_VALIDATOR_GATES | true | yes (NEXT_PUBLIC) | medium |
| 18 | Y-S4 | reasoning-step-labels | MARSYS_FLAG_R10_REASONING_STEPS | true | no (server-side) | medium |
| 19 | Y-S3 | smooth-stream-tuning | MARSYS_FLAG_R10_SMOOTH_STREAM_V2 | true | no (server-side) | medium |
| 20 | Y-S5 | stop-and-edit-while-streaming | MARSYS_FLAG_R10_EDIT_WHILE_STREAMING | **false** | yes (NEXT_PUBLIC) | HIGH (UX risk) |
| 21 | Y-S9 | stream-failure-auto-retry | MARSYS_FLAG_R10_AUTO_RETRY | **false** | no (server-side) | HIGH (cost risk) |

## Flag Classification (Amendment 3 — §M.16 Flagless Precedent)

### SHIP FLAGLESS (no MARSYS_FLAG_R10*)

These sessions are purely additive, non-behavior-changing, or trivial one-liners. No flag needed per §M.16.

| Session | Rationale |
|---------|-----------|
| X-S0 | One-line deploy.yml cleanup — no source change |
| X-S1 | `capture="environment"` attribute addition — purely additive |
| X-S2 | Arrow-up recall — additive UX, no backend change |
| X-S3 | localStorage star persistence — additive only |
| X-S4 | Still-working indicator — additive, no behavior change |
| X-S5 | Skeleton loaders — additive, purely visual |
| X-S7 | Font-size control — settings-driven, no system behavior change |
| X-S9 | Print CSS — additive @media rule only |
| Y-S1 | Citation hover tooltip — additive, reads existing CitationCtx |
| Y-S6 | Branch-on-regen — additive preservation, builds on R8-S2 |
| Y-S7 | Search mode toggle — UI affordance wiring R9-S2's existing param |

### KEEP A FLAG (with deploy.yml build-arg if client-side per Amendment 1)

| Session | Flag | Default | Client-side? | Rationale |
|---------|------|---------|--------------|-----------|
| X-S6 | MARSYS_FLAG_R10_SCROLL_DISCIPLINE | true | **yes** → NEXT_PUBLIC + deploy.yml | Behavior-changing scroll; fast rollback desired |
| X-S8 | MARSYS_FLAG_R10_SELECTIVE_SHARE | true | no (server + schema) | Schema migration; want gated rollout |
| X-S10 | MARSYS_FLAG_R10_INTERACTIVE_TABLES | true | **yes** → NEXT_PUBLIC + deploy.yml | Loads sort/CSV behavior; risk-managed |
| X-S11 | MARSYS_FLAG_R10_MERMAID | true | **yes** → NEXT_PUBLIC + deploy.yml | Lazy-loads heavy mermaid bundle |
| Y-S2 | MARSYS_FLAG_R10_CITATION_FRESHNESS | true | **yes** → NEXT_PUBLIC + deploy.yml | Data-dependent; gated |
| Y-S4 | MARSYS_FLAG_R10_REASONING_STEPS | true | no (synthesis prompt + adapter) | Changes synthesis prompt; preserve R7-S2 footnotes |
| Y-S3 | MARSYS_FLAG_R10_SMOOTH_STREAM_V2 | true | no (server-side only) | Streaming cadence change |
| Y-S8 | MARSYS_FLAG_R10_VALIDATOR_GATES | true | **yes** → NEXT_PUBLIC + deploy.yml | Changes failure event payload |
| Y-S5 | MARSYS_FLAG_R10_EDIT_WHILE_STREAMING | **false** | **yes** → NEXT_PUBLIC + deploy.yml | UX risk — opt-in only |
| Y-S9 | MARSYS_FLAG_R10_AUTO_RETRY | **false** | no (server-side) | Cost risk — opt-in only |

## Amendment Compliance Checklist

The following five amendments govern every brief, session queue entry, commit, and stream-close step in R10. They encode lessons from R7/R8/R9.

### Amendment 1 — NEXT_PUBLIC Build-Arg Discipline (HARD GATE)
- [ ] Every brief with a client-side (`process.env.NEXT_PUBLIC_*`) flag has an AC bullet: "Add flag to `.github/workflows/deploy.yml` --build-arg block. Session is NOT complete until deploy.yml contains it."
- [ ] Every brief explicitly classifies its flag as server-side or client-side.
- [ ] The stream-close gate (Amendment 5) cross-checks source vs deploy.yml coverage.

### Amendment 2 — Mount-Verification + Integration Test (HARD GATE)
- [ ] Every brief for a VISIBLE component has an AC bullet: "Document the exact manual click-path to reach this behavior."
- [ ] Every brief for a VISIBLE component has an AC bullet: "At least one test mounts the PARENT context/provider and asserts the feature renders through the real prop/context chain — NOT leaf-with-injected-props."

### Amendment 3 — §M.16 Flagless Precedent for Additive Polish
- [ ] Every session in the sessions table is classified as FLAGLESS or FLAGGED with explicit default + client-side declaration.
- [ ] No purely-additive session carries an unnecessary flag.

### Amendment 4 — NIM_STACK_DEGRADED Cleanup
- [ ] X-S0 runs first and adds `NEXT_PUBLIC_NIM_STACK_DEGRADED=false` to deploy.yml --build-arg.
- [ ] X-S0 makes NO source edits; it is a one-line deploy.yml change only.

### Amendment 5 — Per-Stream deploy.yml Coverage Gate (HARD, at stream close)
- [ ] Before PR opens, run coverage check:
  ```
  grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10" platform/src --include="*.ts*" -o | awk -F: '{print $NF}' | sort -u
  grep -oE "NEXT_PUBLIC_MARSYS_FLAG_R10[XY]?_[A-Z_]+" .github/workflows/deploy.yml | sort -u
  ```
- [ ] First set MUST be a subset of the second. Any gap = HARD FAILURE — fix before PR.
- [ ] Coverage check result documented in STREAM_R10_COMPLETE.md.

## Merge Train Position

R10 opens a **single PR** from `chat-v2/round10` to `main`.

**Interaction caveat for native:** The Panchang worktree is currently also home to Phase 4C (`feature/phase-4c-panchang`). R10 is on a separate branch (`chat-v2/round10`) so there is no file-level conflict, but:
- If Phase 4C PRs are open against main when R10 is ready to merge, coordinate merge order.
- R10 governance files land under `00_ARCHITECTURE/chat_v2_briefs/round10/` — Phase 4C files are under `00_ARCHITECTURE/BRIEFS/` and `00_ARCHITECTURE/CONDUCTOR/` — no overlap.
- R10 source changes are all in `platform/src/` or `platform/tests/` — same as Phase 4C scope; resolve any conflicts by PR ordering (Phase 4C first, then R10 rebases on the merged result).

## Rollback Plan

| Scope | Mechanism |
|-------|-----------|
| Flagged session (default true) | Flip Cloud Run runtime env to `false` for server-side; for client-side flags must rebuild + deploy with flag=false in deploy.yml |
| Flagged session (default false) | Not active in prod until flag enabled; no rollback needed |
| Flagless session | `git revert <commit>` on main, deploy |
| Schema migration (X-S8) | Migration adds nullable columns (DEFAULT FALSE); rollback migration drops columns — safe if no data written |
| Full R10 rollback | `git revert -m 1 <merge-commit>` of the R10 PR merge |

---

*End of R10_MASTER_PLAN_v1_0.md*

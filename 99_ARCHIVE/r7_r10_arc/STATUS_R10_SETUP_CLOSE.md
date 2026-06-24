---
title: R10 Setup Close
status: COMPLETE
created: 2026-05-20
branch: chat-v2/round10
worktree: /Users/Dev/Vibe-Coding/Apps/Panchang
---

# R10 Setup — Close Report

## Kick-Off Command

To begin R10 execution, open the Panchang worktree and read the first brief:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
git checkout chat-v2/round10
cat 00_ARCHITECTURE/chat_v2_briefs/round10/session_queue.yaml
# Execute X-S0 first per session_queue.yaml execution order
```

## Worktree Path

`/Users/Dev/Vibe-Coding/Apps/Panchang` — existing Panchang worktree on branch `chat-v2/round10`.
Base: `origin/main` at commit `039d993` (R7/R8/R9 + remediation PR #103 all present).

## Governance Artifacts Committed

| Artifact | Path | Lines |
|----------|------|-------|
| Master Plan | `00_ARCHITECTURE/chat_v2_briefs/round10/R10_MASTER_PLAN_v1_0.md` | ~200 |
| X-S0 brief | `round10/X-S0-nim-degraded-buildarg.md` | 68 |
| X-S1 brief | `round10/X-S1-camera-capture-mobile.md` | 70 |
| X-S2 brief | `round10/X-S2-recall-last-prompt.md` | 69 |
| X-S3 brief | `round10/X-S3-citation-star-persistence.md` | 68 |
| X-S4 brief | `round10/X-S4-still-working-indicator.md` | 72 |
| X-S5 brief | `round10/X-S5-skeleton-loaders.md` | 76 |
| X-S6 brief | `round10/X-S6-auto-scroll-discipline.md` | 79 |
| X-S7 brief | `round10/X-S7-font-size-control.md` | 71 |
| X-S8 brief | `round10/X-S8-selective-share.md` | 79 |
| X-S9 brief | `round10/X-S9-print-friendly-share.md` | 66 |
| X-S10 brief | `round10/X-S10-tables-sort-filter-csv.md` | 78 |
| X-S11 brief | `round10/X-S11-mermaid-diagrams.md` | ~80 |
| Y-S1 brief | `round10/Y-S1-citation-hover-snippet.md` | ~75 |
| Y-S2 brief | `round10/Y-S2-citation-freshness-badge.md` | ~80 |
| Y-S3 brief | `round10/Y-S3-smooth-stream-tuning.md` | 77 |
| Y-S4 brief | `round10/Y-S4-reasoning-step-labels.md` | 85 |
| Y-S5 brief | `round10/Y-S5-stop-and-edit-while-streaming.md` | 92 |
| Y-S6 brief | `round10/Y-S6-branch-on-regen.md` | 68 |
| Y-S7 brief | `round10/Y-S7-search-mode-toggle.md` | 71 |
| Y-S8 brief | `round10/Y-S8-validator-per-gate-expander.md` | 77 |
| Y-S9 brief | `round10/Y-S9-stream-failure-auto-retry.md` | 84 |
| Session Queue | `round10/session_queue.yaml` | 281 |
| Merge Train | `chat_v2_briefs/MERGE_TRAIN_ORDER_v1_0.md` | amended to v1.1 |
| CLAUDE.md | `CLAUDE.md` | amended to v2.9 (§E: 8 workstreams, R10 ACTIVE) |

## Flag Classification Summary

### SHIP FLAGLESS (no MARSYS_FLAG_R10* required — §M.16)
X-S0 (deploy.yml-only cleanup), X-S1 (camera capture), X-S2 (recall prompt),
X-S3 (star persistence), X-S4 (still-working), X-S5 (skeletons), X-S7 (font size),
X-S9 (print CSS), Y-S1 (hover tooltip), Y-S6 (branch-on-regen), Y-S7 (search toggle)

### FLAGGED — default true, CLIENT-SIDE → NEXT_PUBLIC + deploy.yml build-arg required (Amendment 1)
| Session | Flag |
|---------|------|
| X-S6 | NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE=true |
| X-S10 | NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES=true |
| X-S11 | NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID=true |
| Y-S2 | NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS=true |
| Y-S8 | NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES=true |

### FLAGGED — default true, SERVER-SIDE (runtime env only, no build-arg)
| Session | Flag |
|---------|------|
| X-S8 | MARSYS_FLAG_R10_SELECTIVE_SHARE=true |
| Y-S4 | MARSYS_FLAG_R10_REASONING_STEPS=true |
| Y-S3 | MARSYS_FLAG_R10_SMOOTH_STREAM_V2=true |

### FLAGGED — default FALSE (high-risk, opt-in only)
| Session | Flag | Risk |
|---------|------|------|
| Y-S5 | NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING=false | UX risk; client-side + deploy.yml |
| Y-S9 | MARSYS_FLAG_R10_AUTO_RETRY=false | Cost risk; server-side only |

## Amendment Compliance Confirmation

| Amendment | Status |
|-----------|--------|
| 1 — NEXT_PUBLIC build-arg discipline | ✅ Every client-side-flagged brief has the deploy.yml AC as a HARD GATE |
| 2 — Mount-verification + parent-context test | ✅ Every visible-component brief has click-path AC + parent-context test AC |
| 3 — §M.16 flagless precedent | ✅ 11 sessions ship flagless; 10 flagged sessions justified in master plan flag table |
| 4 — NIM_STACK_DEGRADED cleanup | ✅ X-S0 runs first; adds NEXT_PUBLIC_NIM_STACK_DEGRADED=false to deploy.yml |
| 5 — Per-stream deploy.yml coverage gate | ✅ Post-queue gate documented in session_queue.yaml and master plan §Amendment Compliance |

## Spot-Check: Amendment 1 Baking Verification

File `X-S6-auto-scroll-discipline.md` contains:
> "deploy.yml (Amendment 1 — HARD GATE): .github/workflows/deploy.yml contains
> --build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE=true. Session is NOT complete until present."

File `Y-S5-stop-and-edit-while-streaming.md` contains:
> "deploy.yml (Amendment 1 — HARD GATE): .github/workflows/deploy.yml contains
> --build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING=false. Session is NOT complete until present."

## Spot-Check: Amendment 2 Baking Verification

File `X-S6-auto-scroll-discipline.md` contains:
> "click-path (Amendment 2): User path: ... Document in commit body."
> "Parent-context integration test (Amendment 2): At least one test mounts the full message list in its real scroll container/provider chain..."

File `Y-S5-stop-and-edit-while-streaming.md` contains:
> "click-path (Amendment 2): User path: Chat V2 (flag=true) → send a query → while streaming, click Stop → ..."
> "Parent-context integration test (Amendment 2): At least one test mounts the full streaming message flow (ConsumeChatV2 or ChatShell, flag=true)..."

## Phase 4C Interaction Caveat (⚠️ Native Action Required Before Merging R10)

The Panchang worktree hosts two concurrent branches:
- `feature/phase-4c-panchang` — Panchang/Conductor work
- `chat-v2/round10` — R10 Chat V2 work

**No file overlap during development** (Phase 4C: `00_ARCHITECTURE/BRIEFS/`, `00_ARCHITECTURE/CONDUCTOR/`; R10: `platform/src/`, `00_ARCHITECTURE/chat_v2_briefs/round10/`).

**Before merging R10 to main:**
1. Check open Phase 4C PRs: `gh pr list --base main | grep phase-4c`
2. If any Phase 4C PR is open: merge it first, then rebase `chat-v2/round10` onto updated main.
3. See `MERGE_TRAIN_ORDER_v1_0.md §Position 4` for full rebase + merge commands.

## Amendment 5 Coverage Gate (Run Before Opening R10 PR)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang

# Step 1: client-side R10 flags in source
grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10" platform/src --include="*.ts*" -o | awk -F: '{print $NF}' | sort -u

# Step 2: R10 flags in deploy.yml
grep -oE "NEXT_PUBLIC_MARSYS_FLAG_R10[XY]?_[A-Z_]+" .github/workflows/deploy.yml | sort -u

# Step 1 must be a subset of Step 2. Any gap = HARD FAILURE before PR.
# Document result in STREAM_R10_COMPLETE.md.
```

---
*Generated 2026-05-20 — R10 governance setup complete on branch chat-v2/round10.*

#!/usr/bin/env bash
# COMMIT_MCPT_PLANNING.sh
# One-shot commit of all MCP Transformation planning artifacts authored by Cowork.
# Leaves R11 and other pre-existing untracked files alone.
#
# Run from the repo root:
#   cd /Users/Dev/Vibe-Coding/Apps/Madhav
#   bash 00_ARCHITECTURE/CONDUCTOR/COMMIT_MCPT_PLANNING.sh

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# 1. Clear stale index lock if present
if [ -f .git/index.lock ]; then
  echo "[1/4] Removing stale .git/index.lock"
  rm -f .git/index.lock
else
  echo "[1/4] No stale lock"
fi

# 2. Stage MCPT-scoped files only
echo "[2/4] Staging MCPT planning artifacts..."

git add CLAUDE.md

git add 00_ARCHITECTURE/PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md
git add 00_ARCHITECTURE/MCP_ARCH_v3_PROPOSAL_2026-05-22.md
git add 00_ARCHITECTURE/MCP_PERF_SYSTEM_BRIEF_2026-05-22.md
git add 00_ARCHITECTURE/MCP_ARCH_v2_PROPOSAL_2026-05-22.md
git add 00_ARCHITECTURE/MCP_DIAGNOSIS_2026-05-22.md
git add 00_ARCHITECTURE/MCP_OPUS_REVIEW_PACKAGE_2026-05-22.md

git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V310_S1_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V310_S2_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V310_S3_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V310_S4_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V310_S5_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V310_S6_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V32_S1_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V32_S2_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V32_S3_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V32_S4_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V32_S5_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V33_S1_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V33_S2_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V33_S3_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V33_S4_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V34_S1_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V34_S2_v1_0.md

git add 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md
git add 00_ARCHITECTURE/CONDUCTOR/SETUP_WORKTREES_MCPT.sh
git add 00_ARCHITECTURE/CONDUCTOR/COMMIT_MCPT_PLANNING.sh

git add 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_WT_A.md
git add 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_WT_B.md
git add 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_WT_C.md
git add 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_WT_D.md
git add 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_WT_E.md
git add 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_WT_F.md
git add 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_FINAL.md

git add 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_A.yaml
git add 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_B.yaml
git add 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_C.yaml
git add 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_D.yaml
git add 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_E.yaml
git add 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_F.yaml
git add 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_FINAL.yaml

# 3. Commit
echo "[3/4] Committing..."

git commit -m "MCP Transformation: planning artifacts (master plan, 17 briefs, 7 queues, 7 kickoffs, setup script)

Cowork-authored planning surface for MCP Transformation (v3.1 pure-MCP rebuild).
Implementation runs in Claude Code extension inside Google Antigravity IDE per
PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md section 2.

Scope:
 - CLAUDE.md section E: 13th concurrent workstream registered, version v3.4 to v3.5
 - 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md: master plan
 - 00_ARCHITECTURE/CONDUCTOR/SETUP_WORKTREES_MCPT.sh: Wave 0 setup script
 - 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_*.yaml: 7 queues
 - 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_*.md: 7 Antigravity Claude Code prompts
 - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_*.md: 17 sub-phase briefs
 - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md: collective brief
 - 00_ARCHITECTURE/PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md: operating principle
 - 00_ARCHITECTURE/MCP_ARCH_v3_PROPOSAL_2026-05-22.md: v3.1 Opus regeneration
 - 00_ARCHITECTURE/MCP_PERF_SYSTEM_BRIEF_2026-05-22.md: v3.1 Opus regeneration
 - 00_ARCHITECTURE/MCP_{ARCH_v2_PROPOSAL,DIAGNOSIS,OPUS_REVIEW_PACKAGE}_*: input context

Workstream status: ACTIVE pending Wave 0 kickoff.

Next: stage source data per master plan section 6 in 00_ARCHITECTURE/SOURCE_DATA/,
then bash 00_ARCHITECTURE/CONDUCTOR/SETUP_WORKTREES_MCPT.sh, then open 6 Antigravity
Claude Code chats and paste KICKOFF_MCPT_WT_{A..F}.md. After Wave 4: open FIN chat,
paste KICKOFF_MCPT_FINAL.md, approve final merge."

# 4. Show what's left
echo ""
echo "[4/4] Remaining uncommitted (R11 + other pre-existing — your call to commit separately):"
echo "----------------------------------------------------------------------------------------"
git status --short
echo "----------------------------------------------------------------------------------------"
echo ""
echo "MCP Transformation planning artifacts: COMMITTED."
echo ""
echo "Next steps:"
echo "  Option A (recommended) — commit R11 work separately, then run setup:"
echo "    git add 00_ARCHITECTURE/chat_v2_briefs/round11/ 00_ARCHITECTURE/chat_v2_briefs/round11_v2/"
echo "    git add 00_ARCHITECTURE/CONDUCTOR/session_queue_R11*.yaml"
echo "    git add 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11*.md"
echo "    git commit -m 'R11: WIP commit'"
echo "    bash 00_ARCHITECTURE/CONDUCTOR/SETUP_WORKTREES_MCPT.sh"
echo ""
echo "  Option B (faster) — stash everything else, run setup, pop stash:"
echo "    git stash push -u -m 'pre-mcpt-setup-stash'"
echo "    bash 00_ARCHITECTURE/CONDUCTOR/SETUP_WORKTREES_MCPT.sh"
echo "    git stash pop"

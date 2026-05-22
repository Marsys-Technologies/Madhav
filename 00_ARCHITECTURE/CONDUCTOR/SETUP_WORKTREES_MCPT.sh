#!/usr/bin/env bash
# SETUP_WORKTREES_MCPT.sh — Wave 0 setup for MCP Transformation
#
# Creates 6 worktrees (A–F) + 1 FINAL worktree, each with its own branch.
# Verifies source-data manifest. Idempotent — safe to re-run.
#
# Run from the main Madhav repo root:
#   cd /Users/Dev/Vibe-Coding/Apps/Madhav && bash 00_ARCHITECTURE/CONDUCTOR/SETUP_WORKTREES_MCPT.sh
#
# All implementation happens in Claude Code extension inside Google Antigravity IDE.
# Per PROJECT_MEMORY_MCP_TRANSFORMATION §2: Cowork is for planning; Claude Code is for impl.

set -euo pipefail

MAIN_REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
WT_PARENT="/Users/Dev/Vibe-Coding/Apps"

# ─── Worktree spec: (suffix, branch_name) ───────────────────────────────────
WORKTREES=(
  "FDN:feature/mcpt-foundation"
  "BPHS:feature/mcpt-bphs"
  "JK:feature/mcpt-jaim-kp"
  "TAJ:feature/mcpt-tajaka"
  "DPT:feature/mcpt-depth"
  "GRD:feature/mcpt-grounding"
  "FIN:feature/mcpt-final"
)

# ─── Source-data manifest check ──────────────────────────────────────────────
SOURCE_DATA_DIR="$MAIN_REPO/00_ARCHITECTURE/SOURCE_DATA"

REQUIRED_SUBDIRS=(
  "classical_texts/BPHS"
  "classical_texts/Jaimini_Sutram"
  "classical_texts/KP_Reader"
  "classical_texts/Tajaka_Neelakanthi"
  "multi_school_seeds"
  "jagannatha_hora_exports"
  "varshphal_tables"
)

echo "═══════════════════════════════════════════════════════════════════"
echo " MCP Transformation — Wave 0 Worktree Setup"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Implementation surface: Claude Code extension in Google Antigravity IDE."
echo "Cowork is for planning ONLY (per PROJECT_MEMORY §2)."
echo ""

# ─── Step 1: verify main repo is clean and on main ───────────────────────────
cd "$MAIN_REPO"
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "✗ Main repo has uncommitted changes. Commit or stash before running setup."
  exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "⚠ Main repo is on branch '$CURRENT_BRANCH', not 'main'. Switching to main..."
  git checkout main
fi
git pull --ff-only origin main
echo "✓ Main repo clean and on main."
echo ""

# ─── Step 2: verify source-data manifest ─────────────────────────────────────
echo "Checking source-data manifest at $SOURCE_DATA_DIR ..."
mkdir -p "$SOURCE_DATA_DIR"

MISSING_SUBDIRS=()
for subdir in "${REQUIRED_SUBDIRS[@]}"; do
  full_path="$SOURCE_DATA_DIR/$subdir"
  if [ ! -d "$full_path" ]; then
    MISSING_SUBDIRS+=("$subdir")
    mkdir -p "$full_path"
    echo "  ⚠ Created empty: $subdir"
  else
    file_count=$(find "$full_path" -type f | wc -l | tr -d ' ')
    if [ "$file_count" = "0" ]; then
      echo "  ⚠ Empty (no source files): $subdir"
      MISSING_SUBDIRS+=("$subdir (empty)")
    else
      echo "  ✓ Present ($file_count files): $subdir"
    fi
  fi
done

if [ "${#MISSING_SUBDIRS[@]}" -gt 0 ]; then
  echo ""
  echo "⚠ Source-data subdirs missing or empty:"
  for m in "${MISSING_SUBDIRS[@]}"; do echo "    - $m"; done
  echo ""
  echo "  These need to be populated BEFORE the corresponding worktree's first session runs:"
  echo "    classical_texts/BPHS              → required for v3.2-S1 (WT-B)"
  echo "    classical_texts/Jaimini_Sutram    → required for v3.2-S2 (WT-C)"
  echo "    classical_texts/KP_Reader         → required for v3.2-S2 (WT-C; OCR allowed)"
  echo "    classical_texts/Tajaka_Neelakanthi → required for v3.2-S3 (WT-D)"
  echo "    multi_school_seeds                → required for v3.2-S4, S5"
  echo "    jagannatha_hora_exports           → required for v3.3-S1, S2 (compute fallback allowed)"
  echo "    varshphal_tables                  → required for v3.3-S3 (compute fallback allowed)"
  echo ""
  echo "  Worktree setup will still proceed; affected sessions will halt with MISSING_SOURCE_DATA"
  echo "  until you populate the dirs."
  echo ""
fi

# ─── Step 3: ensure feature/mcpt-final exists as the merge-target branch ────
if ! git show-ref --verify --quiet refs/heads/feature/mcpt-final && ! git show-ref --verify --quiet refs/remotes/origin/feature/mcpt-final; then
  echo "Creating feature/mcpt-final branch from main (wave-collector branch)..."
  git checkout -b feature/mcpt-final
  git push -u origin feature/mcpt-final
  git checkout main
  echo "✓ feature/mcpt-final created."
else
  echo "✓ feature/mcpt-final already exists."
fi
echo ""

# ─── Step 4: create worktrees ────────────────────────────────────────────────
echo "Creating worktrees..."
for spec in "${WORKTREES[@]}"; do
  SUFFIX="${spec%%:*}"
  BRANCH="${spec##*:}"
  WT_PATH="$WT_PARENT/MadhavMCPT-$SUFFIX"

  if [ -d "$WT_PATH" ]; then
    echo "  ⚠ Worktree already exists at $WT_PATH — skipping"
    continue
  fi

  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "  → Worktree $SUFFIX on existing branch $BRANCH"
    git worktree add "$WT_PATH" "$BRANCH"
  elif git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
    echo "  → Worktree $SUFFIX tracking origin/$BRANCH"
    git worktree add --track -b "$BRANCH" "$WT_PATH" "origin/$BRANCH"
  else
    echo "  → Worktree $SUFFIX on new branch $BRANCH (from main)"
    git worktree add -b "$BRANCH" "$WT_PATH" main
  fi
  echo "  ✓ $WT_PATH ($BRANCH)"
done
echo ""

# ─── Step 5: print summary + next steps ──────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════════"
echo " Setup complete."
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Worktrees created:"
for spec in "${WORKTREES[@]}"; do
  SUFFIX="${spec%%:*}"
  BRANCH="${spec##*:}"
  echo "  $WT_PARENT/MadhavMCPT-$SUFFIX  →  $BRANCH"
done
echo ""
echo "Conductor queues live at:"
ls "$MAIN_REPO/00_ARCHITECTURE/CONDUCTOR/" | grep "session_queue_MCPT" | sed 's|^|  00_ARCHITECTURE/CONDUCTOR/|'
echo ""
echo "Kickoff prompts live at:"
ls "$MAIN_REPO/00_ARCHITECTURE/CONDUCTOR/" | grep "KICKOFF_MCPT" | sed 's|^|  00_ARCHITECTURE/CONDUCTOR/|'
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo " NEXT STEPS — implementation runs in Claude Code (Antigravity IDE):"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo " 1. Open Google Antigravity IDE."
echo " 2. For EACH of the 6 implementation worktrees (A, B, C, D, E, F):"
echo "      a. Open the worktree folder in Antigravity (e.g. MadhavMCPT-FDN)."
echo "      b. Open a Claude Code chat in that workspace."
echo "      c. Paste the corresponding KICKOFF_MCPT_WT_{A..F}.md content."
echo "      d. The Conductor inside Claude Code begins walking its queue autonomously."
echo " 3. Wave 0 → Wave 4 execute mostly autonomously."
echo "    Operator response only required on:"
echo "      - Source-data missing halts (populate then RESUME)"
echo "      - Cross-WT merge conflicts (resolve in Claude Code, RESUME)"
echo "      - ORCHESTRATOR_HANDOFF (open new Antigravity chat, re-paste kickoff)"
echo " 4. After Wave 4 closes (all 6 worktrees merged into feature/mcpt-final):"
echo "      a. Open MadhavMCPT-FIN in Antigravity."
echo "      b. Paste KICKOFF_MCPT_FINAL.md."
echo "      c. v3.4-S2 (red-team + main merge) executes."
echo "      d. SOLE human approval gate: APPROVE_MAIN_MERGE at the end."
echo ""
echo "Reference: MCP_TRANSFORMATION_PLAN_v1_0.md for the full execution model."
echo ""

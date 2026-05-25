---
title: SETUP_PROMPT — Universal Parity Campaign
version: 1.0
status: CURRENT
campaign: universal-parity
description: >
  Paste this entire prompt into a Claude Code session opened on the MAIN Madhav checkout
  (/Users/Dev/Vibe-Coding/Apps/Madhav). Runs entirely in the main checkout. Creates the
  branch, stages all conductor artifacts, and creates the MadhavParity worktree.
  After this completes, switch to MadhavParity and paste CONDUCTOR_KICKOFF_PROMPT_v1_0.md.
---

# SETUP — Universal Parity Campaign

You are Claude Code running in the main Madhav checkout at `/Users/Dev/Vibe-Coding/Apps/Madhav`.

Execute the following steps in order. Use `--dangerously-skip-permissions`. Do not pause for confirmation.

---

## Step 1 — Sync main to origin

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git checkout main
git merge origin/main --ff-only || git pull origin main
```

If `--ff-only` fails (diverged), run:
```bash
git pull --rebase origin main
```

Verify: `git log --oneline -3` shows the latest commit is from origin/main.

---

## Step 2 — Create the campaign branch

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout -b feature/universal-parity
```

If branch already exists:
```bash
git checkout feature/universal-parity
git merge main --ff-only
```

---

## Step 3 — Verify conductor directory structure exists

The following files should already exist (authored in the prior Cowork planning session). Verify:

```bash
ls 00_ARCHITECTURE/CONDUCTOR/universal-parity/
# Expected: session_queue.yaml  SETUP_PROMPT_v1_0.md  CONDUCTOR_KICKOFF_PROMPT_v1_0.md
#           CONDUCTOR_LOG.md  CONDUCTOR_HALT_LOG.md

ls 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PARITY_PRE_S1_v1_0.md
# Expected: file exists
```

If any file is missing, read `00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml` and recreate from its embedded `brief_spec` fields. Do NOT proceed past Step 3 until all conductor artifacts are in place.

---

## Step 4 — Create per-session brief stubs directory

```bash
mkdir -p 00_ARCHITECTURE/BRIEFS
mkdir -p eval-results
```

Create the brief output directory used by the conductor when authoring session briefs just-in-time:

```bash
touch eval-results/.gitkeep
```

---

## Step 5 — Create the test fixture reference file

The native chart ID used across all test sessions is `362f9f17-95a5-490b-a5a7-027d3e0efda0`.

Write this to a campaign constants file so all sessions can import it:

Create file `00_ARCHITECTURE/CONDUCTOR/universal-parity/CAMPAIGN_CONSTANTS.yaml`:

```yaml
# Universal Parity Campaign — shared constants
native_chart_id: "362f9f17-95a5-490b-a5a7-027d3e0efda0"
mcp_url: "https://amjis-mcp-qm256lasva-el.a.run.app/mcp"
portal_base_url: "https://marsysjis.web.app"   # update if different
db_port: 5433
db_proxy_script: "platform/scripts/start_db_proxy.sh"
branch: "feature/universal-parity"
worktree_path: "/Users/Dev/Vibe-Coding/Apps/MadhavParity"
conductor_queue: "00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml"
conductor_log: "00_ARCHITECTURE/CONDUCTOR/universal-parity/CONDUCTOR_LOG.md"
conductor_halt_log: "00_ARCHITECTURE/CONDUCTOR/universal-parity/CONDUCTOR_HALT_LOG.md"
eval_results_dir: "eval-results"
parity_baseline_file: "eval-results/parity_baseline_pre_campaign.json"
parity_final_file: "eval-results/parity_final_inventory.json"
```

---

## Step 6 — Initial commit on the branch

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add 00_ARCHITECTURE/CONDUCTOR/universal-parity/
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PARITY_PRE_S1_v1_0.md
git add eval-results/.gitkeep
git commit -m "feat(universal-parity): campaign conductor artifacts + setup

- session_queue.yaml: 54 sessions across 3 conductor runs
- SETUP_PROMPT_v1_0.md: worktree setup instructions
- CONDUCTOR_KICKOFF_PROMPT_v1_0.md: meta-prompt for conductor
- CONDUCTOR_LOG.md + CONDUCTOR_HALT_LOG.md: stubs
- CAMPAIGN_CONSTANTS.yaml: shared test fixtures
- CLAUDECODE_BRIEF_PARITY_PRE_S1_v1_0.md: pre-authored diagnostic brief
- eval-results/.gitkeep: output dir

Campaign goal: full tool + data asset parity across portal (Classic + Claude-style)
and MCP channels. 54 sessions; 3 conductor runs."
```

---

## Step 7 — Push the branch to origin

```bash
git push -u origin feature/universal-parity
```

---

## Step 8 — Create the MadhavParity worktree

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavParity feature/universal-parity
```

Verify:
```bash
git worktree list
# Expected: /Users/Dev/Vibe-Coding/Apps/MadhavParity  <sha>  [feature/universal-parity]
```

---

## Step 9 — Verify worktree is clean and ready

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git status
# Expected: nothing to commit, working tree clean

ls 00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml
# Expected: file present
```

---

## Step 10 — Final confirmation

Print a summary:

```
SETUP COMPLETE
==============
Branch:   feature/universal-parity
Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
Commit:   <sha from Step 6>
Queue:    00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml (54 sessions)
HAPs:     6 (HAP-1 after UDA-Q-S8 .. HAP-6 after TEST-4-S1)

NEXT ACTION:
  Open a NEW Claude Code session in:
  /Users/Dev/Vibe-Coding/Apps/MadhavParity

  Paste: 00_ARCHITECTURE/CONDUCTOR/universal-parity/CONDUCTOR_KICKOFF_PROMPT_v1_0.md
  Flag:  --dangerously-skip-permissions
```

---

*End of SETUP_PROMPT_v1_0.md*

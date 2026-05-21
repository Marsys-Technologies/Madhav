# MCP — Claude Code SETUP Prompt v1.0

Paste this into a **fresh Claude Code session** pointed at the **main repo**
(`/Users/Dev/Vibe-Coding/Apps/Madhav`), before the worktree exists.

This prompt does three things:
1. Commits the MCP governance files to `main` so the worktree picks them up cleanly.
2. Runs the worktree setup script to create `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`
   on a new branch `feature/mcp-server`.
3. Prints the kickoff prompt path you'll paste into the next Claude Code session
   (the one pointed at the new worktree).

Launch Claude Code with:

```
cd /Users/Dev/Vibe-Coding/Apps/Madhav
claude --dangerously-skip-permissions
```

## What to paste

```
You are the MCP setup operator. Your job is to commit the MCP governance
files to main, create the MCP worktree, and report next steps. You do not
do any application coding.

Execute the following steps in order. If any step fails, halt and report.

### Step 1 — Verify the MCP governance files exist on disk

Confirm these files exist (use `ls -la`):
- 00_ARCHITECTURE/CONDUCTOR/session_queue_MCP.yaml
- 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_MCP_v1_0.md
- 00_ARCHITECTURE/CONDUCTOR/MCP_KICKOFF_PROMPT_v1_0.md
- 00_ARCHITECTURE/CONDUCTOR/SETUP_WORKTREE_MCP.sh
- 00_ARCHITECTURE/CONDUCTOR/MCP_SETUP_PROMPT_v1_0.md (this file)
- 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
- 00_ARCHITECTURE/BRIEFS/MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0.md
- 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_0_AUTHOR_v1_0.md
- 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md

If any are missing, HALT and report which.

### Step 2 — Check git state

Run `git status`. Note what's currently uncommitted on main.

The MCP governance files (the 9 paths above) should be either committed
already OR appear as untracked/modified in `git status`. If you see them
neither committed nor in `git status`, HALT and report.

### Step 3 — Stage and commit ONLY the MCP governance files to main

If any of the 9 governance files are uncommitted on main, stage them
EXPLICITLY by path (do NOT use `git add .` — there is other in-flight
work in parallel projects that must not get swept in):

git add 00_ARCHITECTURE/CONDUCTOR/session_queue_MCP.yaml \
        00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_MCP_v1_0.md \
        00_ARCHITECTURE/CONDUCTOR/MCP_KICKOFF_PROMPT_v1_0.md \
        00_ARCHITECTURE/CONDUCTOR/SETUP_WORKTREE_MCP.sh \
        00_ARCHITECTURE/CONDUCTOR/MCP_SETUP_PROMPT_v1_0.md \
        00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md \
        00_ARCHITECTURE/BRIEFS/MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0.md \
        00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_0_AUTHOR_v1_0.md \
        00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md

Commit with this message:

git commit -m "feat(governance): MCP workstream scaffolding (master brief + conductor + reference briefs)

MCP — MARSYS-JIS Model Context Protocol Server. Exposes MARSYS-JIS to
Claude Chat and Cowork via hosted HTTP/SSE MCP server (Cloud Run sidecar).

Adds:
- MCP_BRIEF_v1_0.md (master, DRAFT pending native seal)
- MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0.md (sibling, DRAFT)
- CONDUCTOR_PROMPT_MCP_v1_0.md + MCP_KICKOFF_PROMPT_v1_0.md
- session_queue_MCP.yaml (9 entries: MCP-0-AUTHOR through MCP-MERGE)
- SETUP_WORKTREE_MCP.sh + MCP_SETUP_PROMPT_v1_0.md
- CLAUDECODE_BRIEF_MCP_0_AUTHOR_v1_0.md (brief-authoring meta-session)
- CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md (foundation reference brief)

Worktree feature/mcp-server will be created by SETUP_WORKTREE_MCP.sh
at /Users/Dev/Vibe-Coding/Apps/MadhavMCP next."

If everything was already committed, skip the git add/commit and report.

### Step 4 — Run the worktree setup script

Execute:
  bash 00_ARCHITECTURE/CONDUCTOR/SETUP_WORKTREE_MCP.sh

Capture and report the full output. If it exits non-zero, HALT.

### Step 5 — Report

Once the worktree exists, report:
- The new worktree path: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
- The new branch: feature/mcp-server
- The commit SHA at which the worktree was branched
- The next-step instructions (verbatim from the setup script's output)

Then stop. The native takes over from here — they open a new Claude Code
session in the MadhavMCP worktree and paste MCP_KICKOFF_PROMPT_v1_0.md.

Begin now.
```

## What happens after this prompt completes

1. The main repo has a clean commit adding the MCP governance files.
2. A new git worktree exists at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`,
   on branch `feature/mcp-server`, branched off main HEAD.
3. The native opens a fresh Claude Code session in `MadhavMCP` and pastes
   the contents of `00_ARCHITECTURE/CONDUCTOR/MCP_KICKOFF_PROMPT_v1_0.md`.
   That second prompt starts the autonomous Conductor loop.

## On context safety

This setup session does NOT touch application code. It only commits the
9 governance files and creates the worktree. It cannot accidentally
trigger the implementation — that's the Conductor's job, in a different
session, in a different worktree.

The two-session split (setup here, conductor in MadhavMCP) is intentional:
- Setup runs in main where you have full repo context.
- Conductor runs in MadhavMCP, isolated from parallel workstreams.

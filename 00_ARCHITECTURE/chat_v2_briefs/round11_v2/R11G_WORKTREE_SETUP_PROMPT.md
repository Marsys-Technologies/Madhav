---
canonical_id: R11G_WORKTREE_SETUP_PROMPT
version: 1.0
status: CURRENT
authored: 2026-05-23
purpose: Paste-prompt #1 — sets up the MadhavR11G worktree, hydrates .env.local with cookie + chart ID, ensures pnpm is on PATH, installs deps. Run this in your CURRENT Claude Code session at /Users/Dev/Vibe-Coding/Apps/Madhav.
---

# R11.G — Worktree Setup Prompt

## Pre-paste operator checklist

- **Firebase __session cookie**: mint from production login (https://amjis-web-938361928218.asia-south1.run.app → DevTools → Cookies → `__session` value). Keep handy.
- **Chart UUID**: pick any chart you own for the smoke test.

## Paste this into your CURRENT Claude Code session at `/Users/Dev/Vibe-Coding/Apps/Madhav`

```
You are setting up a new worktree for the autonomous R11.G arc per /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11G_WORKTREE_SETUP_PROMPT.md.

## Scope and rules

- This session ONLY creates the worktree + hydrates its .env.local. It does NOT start the autonomous arc.
- File scope (may_touch): the new worktree at /Users/Dev/Vibe-Coding/Apps/MadhavR11G/ and its .env.local.
- must_not_touch: anything outside the new worktree.
- No commits in main. No PR. No deploy.
- Strict halt on any failure.

## Phase A — Pre-flight

1. Confirm current state:
   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/Madhav
   git status --short
   git rev-parse --abbrev-ref HEAD
   ```
   If on `main` and clean: proceed. If dirty: surface to operator and HALT.

2. `git fetch origin && git pull --ff-only origin main` — ensure main is up to date (R11.F should be merged).

3. Confirm R11.G brief + plan exist:
   ```bash
   ls 00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11G_LIVE_ARC_PLAN_v1_0.md
   ls 00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11G_BRIEF_v1_0.md
   ls 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11G_v1_0.md
   ls 00_ARCHITECTURE/CONDUCTOR/session_queue_R11G.yaml
   ```
   All must exist. HALT if any missing.

## Phase B — Worktree creation

```bash
git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavR11G -b feature/r11g-tool-executor-toggle
git worktree list
```

Verify the new worktree appears at /Users/Dev/Vibe-Coding/Apps/MadhavR11G on branch feature/r11g-tool-executor-toggle.

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11G
ls platform/  # confirm checkout looks right
```

## Phase C — Hydrate .env.local

1. Copy main worktree's .env.local as base:
   ```bash
   cp /Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env.local /Users/Dev/Vibe-Coding/Apps/MadhavR11G/platform/.env.local
   ```

2. R11.G doesn't need new R11 flags beyond what's already present — the work is wiring + UI + deploy.yml flip, not new flag definitions. Skip flag-block additions.

3. Add smoke credentials. Surface to operator:
   "R11.G worktree .env.local hydrated. Now I need your pre-minted Firebase __session cookie value. Paste it as a single line."
   
   Wait for paste. Append:
   ```
   SMOKE_SESSION_COOKIE=<operator-paste>
   ```

4. Surface: "Need a chart UUID you own for the smoke. Reply with the UUID."
   
   Wait. Append:
   ```
   SMOKE_CHART_ID=<operator-paste>
   ```

5. Final .env.local check:
   ```bash
   grep -E "^SMOKE_" /Users/Dev/Vibe-Coding/Apps/MadhavR11G/platform/.env.local | wc -l
   ```
   Must report 2 (SMOKE_SESSION_COOKIE + SMOKE_CHART_ID).

## Phase D — pnpm on PATH + dependencies

The R11.F setup discovered that pnpm wasn't always on PATH. Ensure it is now:

```bash
# Ensure corepack is enabled (Node 16.10+ ships it)
corepack enable 2>&1 | tail -3 || echo "corepack enable already done"

# Activate pnpm via corepack — uses pnpm version declared in package.json packageManager field if present
corepack prepare pnpm@latest --activate 2>&1 | tail -3

# Confirm pnpm is on PATH
which pnpm && pnpm --version
```

If pnpm --version returns a version number, proceed. If not, fall back:
```bash
npm install -g pnpm@10
pnpm --version
```

If pnpm still isn't available, HALT and surface.

Then install deps:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11G/platform
pnpm install --frozen-lockfile
```

Verify exit code 0. If install fails, HALT and surface output.

Confirm pnpm structure (not npm-installed tree):
```bash
ls -1 node_modules/.pnpm 2>/dev/null | head -3
```

Should show packages. If empty, wipe and re-install:
```bash
rm -rf node_modules
pnpm install --frozen-lockfile
```

## Phase E — Sanity-test pnpm dev startup

DO NOT leave dev server running. Just confirm it boots clean.

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11G/platform
timeout 30 pnpm dev 2>&1 | head -40
```

Look for "Ready in" within 30 seconds. HALT if timeout without ready line.

Kill any lingering node processes from the test boot.

## Phase F — Setup complete

Final surface to operator:

"R11.G worktree setup complete.

- Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11G
- Branch: feature/r11g-tool-executor-toggle (cut from main HEAD <sha>)
- .env.local hydrated with SMOKE_SESSION_COOKIE + SMOKE_CHART_ID + all flags from main
- pnpm on PATH (version <X.Y.Z>)
- Dependencies installed via pnpm install --frozen-lockfile
- pnpm dev boots cleanly: 'Ready in <X>ms'

Next step: open a NEW Claude Code session at /Users/Dev/Vibe-Coding/Apps/MadhavR11G with --dangerously-skip-permissions. Paste the kickoff prompt from /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11G_CONDUCTOR_KICKOFF_PROMPT.md. The autonomous arc will run from there."

DO NOT proceed to kickoff. This session ends here.
```

## Operator notes

- Total setup time: ~3-5 minutes.
- Cookie + chart UUID stay in .env.local (gitignored).
- pnpm-on-PATH fix from R11.F lessons learned is baked in.

*End of R11G_WORKTREE_SETUP_PROMPT_v1_0.md*

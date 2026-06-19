# Enterprise Claude Code Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fully equip the Claude Code Desktop environment for enterprise-grade development on the Madhav project — with automated quality gates, specialist subagents, project-specific skills, MCP coverage, and worktree optimisation.

**Architecture:** Four independent layers — (1) automation hooks that enforce quality on every file change, (2) specialist subagents that Claude can dispatch for security/performance/review work, (3) project skills that encode Madhav-specific workflows as slash commands, (4) infrastructure hardening for worktrees and MCP completeness.

**Tech Stack:** Claude Code Desktop, Next.js/TypeScript, ESLint, Vitest, Python/pytest, GitHub MCP, `~/.claude/settings.json` + `.claude/settings.json`

---

## Current State (audit baseline)

| Area | Status |
|---|---|
| Permissions | ✅ Full bypass — `Bash(*)`, `Edit(**)`, `Write(**)` |
| Co-work isolation | ✅ `bgIsolation: none` |
| GitHub MCP | ✅ Connected |
| Playwright MCP | ✅ Connected |
| Chrome DevTools MCP | ✅ Connected |
| Context7 MCP | ✅ Connected |
| Hooks | ❌ None defined |
| Subagents | ❌ None defined |
| Project skills | ⚠️ Only `marsys-design` |
| Worktree symlinks | ❌ `node_modules` (2.5GB) not symlinked — each worktree duplicates it |
| MCP gaps | ❌ GitHub MCP not in project allow list (global only) |

---

## File Structure

```
.claude/
  settings.json          ← hooks + worktree symlinks (modify)
  agents/
    code-reviewer.md     ← create
    security-reviewer.md ← create
    test-writer.md       ← create
    migration-guard.md   ← create
  skills/
    marsys-design/       ← exists
    create-migration/
      SKILL.md           ← create
    run-checks/
      SKILL.md           ← create
    pr-description/
      SKILL.md           ← create
    session-close/
      SKILL.md           ← create
~/.claude/settings.json  ← add hooks (global — fires in all projects)
```

---

## Task 1: Worktree Node Modules Symlink

**Problem:** Every Co-work worktree clones `node_modules` (2.5GB) — slow and disk-intensive.

**Files:**
- Modify: `.claude/settings.json`

- [ ] **Step 1: Add symlink config to project settings**

Open `.claude/settings.json` and add `symlinkDirectories` to the existing `worktree` block:

```json
{
  "worktree": {
    "bgIsolation": "none",
    "symlinkDirectories": ["node_modules", ".next", ".turbo"]
  }
}
```

- [ ] **Step 2: Verify JSON is valid**

```bash
python3 -c "import json; json.load(open('.claude/settings.json')); print('valid')"
```
Expected: `valid`

- [ ] **Step 3: Verify symlink actually applied after next Co-work worktree is created**

After the next Co-work task spins up a worktree, confirm it worked. Use find since the exact worktree path may vary:

```bash
# Find all node_modules symlinks under the dev directory
find /Users/Dev/Vibe-Coding/Apps/Madhav -maxdepth 5 -name node_modules -type l 2>/dev/null
# Should show a path inside the worktree directory pointing to the main node_modules

# If no symlinks found, check where the worktree was actually created:
find /Users/Dev/Vibe-Coding -maxdepth 3 -name HEAD -path '*worktree*' 2>/dev/null
# Then inspect that directory for node_modules type (symlink vs dir)
```

- [ ] **Step 4: Commit**

```bash
git add .claude/settings.json
git commit -m "chore(claude): symlink node_modules/.next in worktrees to avoid 2.5GB copy"
```

---

## Task 2: PostToolUse Hook — ESLint on Edit

**Problem:** No automated lint feedback after file edits. Errors accumulate silently.

**Files:**
- Modify: `~/.claude/settings.json` (global — apply to all projects)

- [ ] **Step 1: Read existing global settings**

```bash
cat ~/.claude/settings.json
```

- [ ] **Step 2: Confirm hook stdin contract (do this once)**

Claude Code pipes the tool-call JSON to the hook's stdin. Verify this before writing any hook:

1. Temporarily add this debug hook to `~/.claude/settings.json` under `hooks.PostToolUse`:
   ```json
   { "matcher": "Edit", "hooks": [{ "type": "command", "command": "cat > /tmp/hook_debug.json" }] }
   ```
2. Make a trivial edit to any file, then check:
   ```bash
   cat /tmp/hook_debug.json
   # Should show: {"tool_name":"Edit","tool_input":{"file_path":"..."},...}
   ```
3. **Remove the debug hook entry from `~/.claude/settings.json` before proceeding to Step 4.**
   If the file is empty, hooks may use environment variables instead — check `env | grep CLAUDE` inside the hook.



- [ ] **Step 3: Pipe-test the lint command manually**

```bash
# Note: project uses ESLint flat config (eslint.config.mjs) — do NOT use --no-eslintrc (v8 flag, invalid here)
echo '{"tool_name":"Edit","tool_input":{"file_path":"/Users/Dev/Vibe-Coding/Apps/Madhav/platform/src/app/page.tsx"}}' \
  | jq -r '.tool_input.file_path' \
  | { read -r f; cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform && npx eslint "$f" 2>/dev/null || true; }
```

Expected: exits 0 (ESLint runs — warnings/errors are advisory, not blocking)

- [ ] **Step 4: Add PostToolUse hook to global settings**

Merge into `~/.claude/settings.json` under `hooks.PostToolUse`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path // empty' | grep -E '\\.(ts|tsx|js|jsx)$' | { read -r f || exit 0; cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform && npx eslint \"$f\" 2>&1 | tail -5; } 2>/dev/null || true",
            "timeout": 15,
            "statusMessage": "ESLint checking...",
            "async": true
          }
        ]
      }
    ]
  }
}
```

Note: `async: true` — runs in background, doesn't block Claude's next action.

- [ ] **Step 4: Validate JSON**

```bash
python3 -c "import json; json.load(open('/Users/Dev/.claude/settings.json')); print('valid')"
```

- [ ] **Step 5: Prove hook fires**

Make a trivial edit to any `.tsx` file via Edit tool, then check:

```bash
# Hook output appears in Claude's transcript — look for ESLint output
```

---

## Task 3: PostToolUse Hook — TypeScript Type Check

**Problem:** Type errors not surfaced until `npm run build`.

**Note:** This project has ~159 pre-existing type errors in test files (baseline dirty state). The hook is scoped to filter only errors in the *edited* file to avoid noise from unrelated files.

**Files:**
- Modify: `~/.claude/settings.json`

- [ ] **Step 1: Establish the tsc baseline error count**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform && npx tsc --noEmit --skipLibCheck 2>&1 | grep -c 'error TS'
```

Record this number. The hook will only report errors — if the count doesn't increase after your edit, the hook output is pre-existing noise.

- [ ] **Step 2: Pipe-test tsc command**

```bash
echo '{"tool_input":{"file_path":"/Users/Dev/Vibe-Coding/Apps/Madhav/platform/src/app/page.tsx"}}' \
  | jq -r '.tool_input.file_path' \
  | grep -E '\.tsx?$' \
  | { read -r f || exit 0; BASENAME=$(basename "$f"); cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform && npx tsc --noEmit --skipLibCheck 2>&1 | grep -F "$BASENAME" | grep 'error TS' | head -5; }
```

Note: uses `basename` to avoid false matches on partial path substrings.

- [ ] **Step 3: Add tsc hook alongside ESLint hook**

Add a second entry in the `PostToolUse` matcher array:

```json
{
  "type": "command",
  "command": "jq -r '.tool_input.file_path // empty' | grep -E '\\.(ts|tsx)$' | { read -r f || exit 0; BASENAME=$(basename \"$f\"); cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform && npx tsc --noEmit --skipLibCheck 2>&1 | grep -F \"$BASENAME\" | grep 'error TS' | head -5; } 2>/dev/null || true",
  "timeout": 30,
  "statusMessage": "Type checking...",
  "async": true
}
```

- [ ] **Step 3: Validate and commit**

```bash
python3 -c "import json; json.load(open('/Users/Dev/.claude/settings.json')); print('valid')"
git -C /Users/Dev/Vibe-Coding/Apps/Madhav add .claude/settings.json
git -C /Users/Dev/Vibe-Coding/Apps/Madhav commit -m "chore(claude): add async ESLint + tsc PostToolUse hooks"
```

---

## Task 4: PreToolUse Hook — Protect Sensitive Files

**Problem:** No guard against accidental edits to `.env`, migration files already applied, or governance docs.

**Files:**
- Modify: `~/.claude/settings.json`

- [ ] **Step 1: Add PreToolUse blocking hook**

Claude Code PreToolUse blocking uses `exit 2` with an error message to stderr — NOT a JSON object on stdout. The hook below uses the correct mechanism:

Add under `hooks.PreToolUse` in global settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path // empty' | { read -r f || exit 0; case \"$f\" in *.env|*.env.*) echo \"Blocked: editing .env files requires explicit user confirmation.\" >&2; exit 2;; esac; }",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Pipe-test the block mechanism**

```bash
# Test that the exit code and stderr output are correct
echo '{"tool_input":{"file_path":"/Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env.local"}}' \
  | jq -r '.tool_input.file_path // empty' \
  | { read -r f; case "$f" in *.env|*.env.*) echo "Blocked" >&2; exit 2;; esac; }
echo "exit code: $?"
```

Expected: prints `Blocked` to stderr, exit code `2`

- [ ] **Step 3: Validate JSON**

```bash
python3 -c "import json; json.load(open('/Users/Dev/.claude/settings.json')); print('valid')"
```

---

## Task 5: Subagent — Code Reviewer

**Files:**
- Create: `.claude/agents/code-reviewer.md`

- [ ] **Step 1: Create agents directory**

```bash
mkdir -p /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/agents
```

- [ ] **Step 2: Create the agent file**

```markdown
---
name: code-reviewer
description: Reviews code changes for bugs, security issues, performance problems, and Madhav project conventions. Use after implementing a feature or fixing a bug.
---

You are a senior engineer reviewing code for the Madhav Jyotish instrument project (Next.js 14, TypeScript, PostgreSQL, Python orchestrator).

## Review dimensions (check all)

1. **Correctness** — logic errors, off-by-one, null/undefined handling, async/await misuse
2. **Security** — SQL injection, XSS, unvalidated inputs, exposed secrets, insecure direct object references
3. **Performance** — N+1 queries, missing indexes, unbounded loops, missing React memoisation
4. **Project conventions** — layer separation (L1 facts never mixed with L2 interpretations), asset_id naming (`ga_*`, `bo_*`), WriterBase conformance, idempotency (delete-then-insert for L1+)
5. **Test coverage** — are edge cases tested? Are assertions meaningful?

## Output format

For each finding:
```
[SEVERITY: HIGH|MED|LOW] [DIMENSION] filename:line
Issue: <one sentence>
Fix: <concrete suggestion or code snippet>
```

Only report findings with HIGH confidence. Skip style nitpicks.
End with: `LGTM ✓` if no HIGH/MED issues found.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/code-reviewer.md
git commit -m "chore(claude): add code-reviewer subagent"
```

---

## Task 6: Subagent — Security Reviewer

**Files:**
- Create: `.claude/agents/security-reviewer.md`

- [ ] **Step 1: Create the agent file**

```markdown
---
name: security-reviewer
description: Deep security audit focused on auth, data access, injection, and secrets. Run before any PR touching API routes, DB queries, or auth flows.
---

You are an application security engineer auditing the Madhav platform (Next.js API routes, PostgreSQL via pg, Python orchestrator).

## Audit checklist

- [ ] SQL injection — are all queries parameterised? No string interpolation in SQL.
- [ ] Authentication — are all `/api/` routes protected? Check for missing `getServerSession` guards.
- [ ] Authorisation — does the logged-in user own the resource they're accessing?
- [ ] Secrets — no hardcoded tokens, API keys, or passwords. All via `process.env`.
- [ ] Input validation — are user-supplied values validated before use?
- [ ] Path traversal — no user-controlled file paths.
- [ ] Rate limiting — are mutation endpoints rate-limited?
- [ ] CORS — is the API restricted to known origins?

## Output

List each finding as:
```
[CRITICAL|HIGH|MED] file:line
Vulnerability: <type>
Evidence: <code snippet>
Remediation: <specific fix>
```

If no issues: `SECURITY CLEAR ✓`
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/security-reviewer.md
git commit -m "chore(claude): add security-reviewer subagent"
```

---

## Task 7: Subagent — Migration Guard

**Problem:** Madhav uses sequential migrations. A broken migration applied to prod is hard to reverse.

**Files:**
- Create: `.claude/agents/migration-guard.md`

- [ ] **Step 1: Create the agent file**

```markdown
---
name: migration-guard
description: Reviews a new SQL migration file before it is applied. Checks for destructive operations, missing rollback safety, naming convention violations, and idempotency issues.
---

You are a database reliability engineer reviewing a PostgreSQL migration for the Madhav platform.

## Review checklist

- [ ] **Naming** — file follows `NNN_description.sql` sequential numbering. No gaps or duplicates vs `platform/migrations/`.
- [ ] **Destructive ops** — any `DROP TABLE`, `DROP COLUMN`, `TRUNCATE` must have a comment explaining why it is safe.
- [ ] **Non-nullable columns** — adding a NOT NULL column to an existing table requires a DEFAULT or a backfill step before the constraint.
- [ ] **Idempotency** — uses `IF NOT EXISTS`, `ON CONFLICT DO NOTHING`, or is wrapped in a transaction that can be safely re-run.
- [ ] **Index creation** — large table indexes should use `CREATE INDEX CONCURRENTLY` to avoid table locks.
- [ ] **Foreign keys** — new FKs reference existing tables; no forward references.
- [ ] **Asset registry** — if a new asset is introduced, `asset_registry` insert is included with a correct `count_sql`.

Output: `MIGRATION SAFE ✓` or a list of `[BLOCKER|WARN]` findings with line numbers.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/migration-guard.md
git commit -m "chore(claude): add migration-guard subagent"
```

---

## Task 8: Project Skill — `create-migration`

**Problem:** Every migration requires remembering the numbering scheme, the correct path, and the `asset_registry` pattern.

**Files:**
- Create: `.claude/skills/create-migration/SKILL.md`

- [ ] **Step 1: Create skill directory and file**

```bash
mkdir -p /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/skills/create-migration
```

```markdown
---
name: create-migration
description: Create a new numbered SQL migration file for the Madhav platform following the project's naming and idempotency conventions.
---

## How to use

User invokes: `/create-migration <description>`

## Steps

1. Run this to find the next migration number:
   ```bash
   ls platform/migrations/*.sql | sed 's/.*\/\([0-9]*\)_.*/\1/' | sort -n | tail -1
   ```
   Add 1 to get `NNN`.

2. Create file at `platform/migrations/NNN_<description>.sql` with this header:
   ```sql
   -- Migration NNN: <description>
   -- Created: <date>

   BEGIN;

   -- Your SQL here

   COMMIT;
   ```

3. If adding a new asset, include the asset_registry insert:
   ```sql
   INSERT INTO asset_registry (asset_id, display_name, layer, count_sql, target_floor)
   VALUES (
     '<asset_id>',
     '<display name>',
     '<L0|L1|L2>',
     'SELECT COUNT(*) FROM <table> WHERE chart_id = $1',
     0
   ) ON CONFLICT (asset_id) DO NOTHING;
   ```

4. After creating, dispatch the `migration-guard` subagent to review it.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/create-migration/
git commit -m "chore(claude): add create-migration project skill"
```

---

## Task 9: Project Skill — `run-checks`

**Problem:** Before any PR, Claude must remember to run lint + typecheck + tests. This should be a one-command skill.

**Files:**
- Create: `.claude/skills/run-checks/SKILL.md`

- [ ] **Step 1: Create the skill**

```bash
mkdir -p /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/skills/run-checks
```

```markdown
---
name: run-checks
description: Run the full Madhav quality gate — ESLint, TypeScript, and test suite — and report results. Use before raising a PR.
---

Run these commands in sequence from `platform/`:

```bash
# 1. Lint
npm run lint 2>&1 | tail -20

# 2. Type check
npx tsc --noEmit --skipLibCheck 2>&1 | grep -c 'error TS' || echo "0 type errors"

# 3. Unit tests
npm run test 2>&1 | tail -30

# 4. Python tests (if orchestrator changed)
# Note: test files live under platform/scripts/ AND platform/python-sidecar/ — scope broadly
cd .. && python -m pytest platform/ -x -q --ignore=platform/node_modules --ignore=platform/.next 2>&1 | tail -20
```

Report format:
```
ESLint:     PASS / N warnings / N errors
TypeScript: PASS / N errors
Tests:      N passed, N failed
Python:     N passed, N failed (or SKIPPED if no orchestrator changes)
```

If any gate fails, stop and report. Do not raise a PR with failing gates.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/run-checks/
git commit -m "chore(claude): add run-checks project skill"
```

---

## Task 10: Project Skill — `pr-description`

**Problem:** PR descriptions are inconsistently written. This skill enforces the project's PR template.

**Files:**
- Create: `.claude/skills/pr-description/SKILL.md`

- [ ] **Step 1: Create the skill**

```bash
mkdir -p /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/skills/pr-description
```

```markdown
---
name: pr-description
description: Generate a well-structured PR description for the current branch following Madhav's PR template. Run /run-checks first.
---

## Steps

1. Get the diff summary:
   ```bash
   git log main..HEAD --oneline
   git diff main --stat
   ```

2. Write the PR description using this template:

```markdown
## Summary
- <bullet: what changed and why>
- <bullet>

## Changes
| File | Change |
|---|---|
| `path/to/file` | What changed |

## Test plan
- [ ] ESLint passes
- [ ] TypeScript passes
- [ ] Unit tests pass
- [ ] Manual smoke: <specific route or feature to verify>

## Migration notes
<If migrations included: list them and what they do. Otherwise: None.>

## Acceptance criteria
<List from the brief/CLAUDECODE_BRIEF.md if one exists>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

3. Raise the PR with:
   ```bash
   gh pr create --title "<title>" --body "<description>"
   ```
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/pr-description/
git commit -m "chore(claude): add pr-description project skill"
```

---

## Task 11: Project Skill — `session-close`

**Problem:** CLAUDE.md §H mandates a session-close checklist on every session. This skill encodes it so Claude never skips it.

**Files:**
- Create: `.claude/skills/session-close/SKILL.md`

- [ ] **Step 1: Create the skill**

```bash
mkdir -p /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/skills/session-close
```

Create `.claude/skills/session-close/SKILL.md`:

```markdown
---
name: session-close
description: Emit and validate the SESSION_CLOSE artifact per CLAUDE.md §H and SESSION_CLOSE_TEMPLATE_v1_0.md. Run at end of every substantive session.
---

## Steps

1. Read `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md` to get the current close schema.

2. Emit the SESSION_CLOSE block with all required fields filled:
   - `session_id`, `step_completed`, `artifacts_produced`, `may_touch_actual`, `must_not_touch_respected`
   - `drift_detector_run`, `schema_validator_run`, `red_team_due`, `red_team_discharged`
   - `current_state_updated`, `session_log_appended`

3. Run schema validation (verify the flag exists first):
   ```bash
   python3 platform/scripts/governance/schema_validator.py --help 2>&1 | grep -i session
   # If --session-close flag exists, run it:
   python3 platform/scripts/governance/schema_validator.py --session-close
   # If not, skip this step — validator may not have this mode yet
   ```

4. If validation passes, append the session block to `00_ARCHITECTURE/SESSION_LOG.md`.

5. Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 with the new position.

6. Set `status: COMPLETE` in `CLAUDECODE_BRIEF.md` if one exists at project root.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/session-close/
git commit -m "chore(claude): add session-close project skill"
```

---

## Task 12: MCP — Supabase/PostgreSQL Direct Access

**Why:** Currently all DB queries go through the app. Direct MCP access lets Claude inspect `chart_facts`, run ad-hoc SQL, and verify migration results without `psql`.

**Files:**
- Modify: `~/.claude.json` (global MCP registry)

- [ ] **Step 1: Get the DB connection string**

```bash
grep -r "DATABASE_URL\|POSTGRES" /Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env* 2>/dev/null | head -5
```

- [ ] **Step 2: Add PostgreSQL MCP to global config**

```bash
# Install the MCP package
npm install -g @modelcontextprotocol/server-postgres 2>/dev/null || npx @modelcontextprotocol/server-postgres --version
```

Add to **both** config files (Claude Code CLI uses `~/.claude.json`; Claude Desktop app uses `~/Library/Application Support/Claude/claude_desktop_config.json`):

**`~/.claude.json`** — for Claude Code CLI and Desktop:

```python
# Run this to add it programmatically:
import json, pathlib
p = pathlib.Path.home() / '.claude.json'
d = json.loads(p.read_text())
d.setdefault('mcpServers', {})['postgres'] = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres", "<YOUR_DATABASE_URL>"]
}
p.write_text(json.dumps(d, indent=2))
print("done")
```

**`~/Library/Application Support/Claude/claude_desktop_config.json`** — same entry under `mcpServers`.

- [ ] **Step 3: Add to project allow list**

In `.claude/settings.json`, add to the `allow` array:
```json
"mcp__postgres__*"
```

- [ ] **Step 4: Restart Claude Desktop and verify**

After restart, Claude should be able to run SQL directly:
> "Query the chart_facts table for chart_id 482012f1 and count rows per category"

---

## Task 13: Global Settings — Final Consolidation

Ensure `~/.claude/settings.json` has all hooks, the GitHub MCP wildcard, and the claude-mem wildcard in one clean file.

- [ ] **Step 1: Validate the final global settings file**

```bash
python3 -c "import json; d=json.load(open('/Users/Dev/.claude/settings.json')); print('hooks:', list(d.get('hooks',{}).keys())); print('allow count:', len(d.get('permissions',{}).get('allow',[]))); print('valid JSON ✓')"
```

Expected:
```
hooks: ['PreToolUse', 'PostToolUse']
allow count: > 50
valid JSON ✓
```

- [ ] **Step 2: Final commit**

```bash
git -C /Users/Dev/Vibe-Coding/Apps/Madhav add .claude/
git -C /Users/Dev/Vibe-Coding/Apps/Madhav commit -m "chore(claude): enterprise setup complete — agents, skills, hooks, worktree config"
```

---

## Summary — What This Delivers

| Capability | Before | After |
|---|---|---|
| Lint on file edit | Manual | Automatic (async hook) |
| Type errors | At build time | After every edit (async hook) |
| `.env` protection | None | Blocked by PreToolUse hook |
| Code review | Ad-hoc | `/code-reviewer` subagent |
| Security audit | None | `/security-reviewer` subagent |
| Migration safety | Manual | `/migration-guard` subagent |
| Migration creation | Manual | `/create-migration` skill |
| PR descriptions | Ad-hoc | `/pr-description` skill |
| Quality gate | Manual | `/run-checks` skill |
| Worktree disk | 2.5GB per branch | ~0 (symlinked) |
| DB inspection | Via app only | Direct SQL via Postgres MCP |

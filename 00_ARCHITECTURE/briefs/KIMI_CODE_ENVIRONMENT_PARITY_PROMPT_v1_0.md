---
artifact: KIMI_CODE_ENVIRONMENT_PARITY_PROMPT_v1_0.md
version: 1.0
status: CURRENT
authored_by: Claude Code (Opus 5), 2026-09-23
audience: Kimi Code agent (moonshotai/kimi-code CLI), first session on this repo
purpose: >
  One-paste bootstrap prompt that brings a Kimi Code session to environment and
  context parity with Claude Code and Codex on the MARSYS-JIS (Madhav) repo:
  same working tree, same governance surfaces, same skills, same subagents,
  same MCP servers, same permission posture. States honestly which parity items
  are achievable and which are not.
provenance: >
  Every Kimi-side discovery rule below was read out of the installed binary at
  /Users/Dev/.kimi-code/bin/kimi on 2026-09-23, not assumed from documentation.
---

# Kimi Code — environment parity bootstrap for MARSYS-JIS

**Paste this whole file, or just say:** `Read and execute
00_ARCHITECTURE/briefs/KIMI_CODE_ENVIRONMENT_PARITY_PROMPT_v1_0.md in full.`

You are Kimi Code, starting work on the MARSYS-JIS ("Madhav") repository at
`/Users/Dev/Vibe-Coding/Apps/Madhav`. Claude Code and Codex already operate on
this exact working tree. Your job in this first session is to reach parity with
them, verify it, and then work under the same governance contract they do.

Work through §2 → §3 → §4 in order. Everything in §3 is idempotent: re-running a
step that is already satisfied must change nothing. Do not skip verification.

---

## §1 — How you load context (verified, not assumed)

These are the discovery rules of the installed Kimi Code binary. They differ from
Claude Code's in ways that matter here, so do not reason from Claude's rules.

**Instruction files you auto-load** (in this order, each rendered with a
`<!-- From: <path> -->` header):

1. `~/.kimi-code/AGENTS.md` (or `$KIMI_CODE_HOME/AGENTS.md`)
2. first of `~/.agents/AGENTS.md` / `~/.agents/agents.md`
3. walking from the git root down to the cwd, for each directory:
   `<dir>/.kimi-code/AGENTS.md`, then the first of `<dir>/AGENTS.md` /
   `<dir>/agents.md`

**You do NOT auto-load `CLAUDE.md`.** This repo's governing document is
`CLAUDE.md` at the root. The root `AGENTS.md` is a deliberate thin loader that
points at it. That indirection is the whole mechanism by which you, Claude Code
and Codex share one state — so treat "read `CLAUDE.md` in full" as a hard
instruction, not a suggestion, every session.

**Skills** are discovered from `~/.kimi-code/skills`, `~/.agents/skills`,
`<project>/.kimi-code/skills`, `<project>/.agents/skills`. You do **not** read
`.claude/skills` — the repo keeps `.agents/skills` as a byte-identical mirror of
`.claude/skills` precisely so both agents see the same skills.

**Agent profiles** (subagents) come from `~/.kimi-code/agents`, `~/.agents/agents`,
`<project>/.kimi-code/agents`, `<project>/.agents/agents`. You do **not** read
`.claude/agents`.

**MCP servers** come from `~/.kimi-code/mcp.json` (user-global),
`<project root>/.mcp.json` (Claude-compatible, shared), and
`<cwd>/.kimi-code/mcp.json` (Kimi-local). Note: there is no evidence this build
expands `${ENV_VAR}` placeholders inside these files the way Claude Code does —
assume it does not, and see §3.3.

---

## §2 — Parity assessment (do this first, read-only)

Run these and report what you find before changing anything:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git remote -v && git branch --show-current && git status --short | head -20
ls -a .agents .claude 00_ARCHITECTURE | head -40
ls .agents/agents 2>/dev/null || echo "MISSING: .agents/agents"
ls .kimi-code 2>/dev/null || echo "no project-local .kimi-code (expected on first run)"
diff -rq .claude/skills .agents/skills && echo "skills mirror: IN SYNC"
/Users/Dev/.kimi-code/bin/kimi doctor
```

Expected baseline (already true, do not "fix"):

| Item | State |
|---|---|
| Working tree | Same checkout all three agents use — `/Users/Dev/Vibe-Coding/Apps/Madhav`, remote `Marsys-Technologies/Madhav` |
| Root `AGENTS.md` | Present, loads `CLAUDE.md` — you inherit full project governance through it |
| `.agents/skills` | Mirror of `.claude/skills` (create-migration, marsys-design, pr-description, run-checks, session-close) |
| `~/.agents/skills` | User-level shared skills, readable by you |
| Permission posture | `~/.kimi-code/config.toml` has `default_permission_mode = "auto"` — matches Claude Code's `bypassPermissions` on this repo |
| Thinking | `[thinking] enabled = true`, `effort = "high"`; `kimi-for-coding` defaults to `max` effort |

---

## §3 — Close the gaps

### 3.1 — Subagents (gap: real)

`.claude/agents/` holds three repo-specific reviewers that Claude Code uses and
you cannot see: `code-reviewer.md`, `migration-guard.md`, `security-reviewer.md`.
Their format (YAML frontmatter `name` + `description`, then the prompt body) is
portable to a Kimi agent profile as-is.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
mkdir -p .agents/agents
cp -n .claude/agents/*.md .agents/agents/
diff -rq .claude/agents .agents/agents && echo "agents mirror: IN SYNC"
```

Use `cp -n` so an existing Kimi-side file is never clobbered. If the two sides
ever diverge, `.claude/agents` is the source of truth — the mirror direction is
one-way.

### 3.2 — Skills (verify only)

`.agents/skills` should already equal `.claude/skills`. If `diff -rq` reports a
difference, re-mirror from `.claude/skills` and say so in your report — a silent
divergence here means the two agents were running different `run-checks` or
`session-close` definitions, which is a governance problem, not a convenience one.

At user level, `~/.claude/skills` carries `layer-value-elevation`, which
`~/.agents/skills` does not. Mirror it only if this session actually needs it:

```bash
cp -Rn /Users/Dev/.claude/skills/layer-value-elevation /Users/Dev/.agents/skills/ 2>/dev/null || true
```

### 3.3 — MCP servers (gap: real, and the one most likely to bite you)

Claude Code on this repo reaches the project's own MCP server plus several
infrastructure servers. Here is where each definition lives and what you must do.

| Server | Claude Code source | Your action |
|---|---|---|
| `marsys-jis` | `<project>/.mcp.json`, auth as `Bearer ${MARSYS_MCP_KEY}` | **Broken for you as written** — `MARSYS_MCP_KEY` is not exported in the shell, and this build does not appear to expand `${...}`. Use the working definition instead (next row). |
| `marsys-jis-direct` | `<project>/.codex/config.toml` (`[mcp_servers.marsys-jis-direct]`, URL carries the API key inline) | Copy that server's URL **verbatim** into `<project>/.kimi-code/mcp.json`. Read the value at write time; never retype a key from memory, never echo it to the transcript, never commit it. |
| `postgres`, `github`, `hostinger-api`, `21st` | `~/.claude.json` → top-level `mcpServers` (npx-launched stdio servers) | Copy the entries you actually need into `~/.kimi-code/mcp.json`, merging alongside the existing `kimi-cu` entry. |

`<project>/.kimi-code/mcp.json` is the right home for the Madhav-specific server
because it is project-local and, unlike `.mcp.json`, is not a cross-agent shared
file you could break for Claude Code or Codex.

Constraints, non-negotiable:

- **Do not edit `<project>/.mcp.json`.** Claude Code reads it. Changing its shape
  to suit you breaks their session.
- **Do not commit any file containing a key.** Before any `git add`, run
  `git check-ignore -v .kimi-code/mcp.json` and confirm it is ignored; if it is
  not, add it to `.gitignore` in the same change and say so.
- `kimi doctor` after writing, then confirm the server actually answers — a
  config that parses is not a config that connects.

There is a built-in `/import-from-cc-codex` skill that can do parts of this.
**Use it only for MCP, never for instructions or skills.** Its instruction
importer copies `CLAUDE.md` content into `~/.kimi-code/AGENTS.md` and
`<project>/.kimi-code/AGENTS.md`, which would fork the single governing document
into three drifting copies — a direct violation of `CLAUDE.md` §B.8 and §L ("do
not duplicate canonical-artifact paths outside CANONICAL_ARTIFACTS"). The whole
point of the loader indirection in §1 is that there is exactly one `CLAUDE.md`.

### 3.4 — Workspace and model

```bash
# Second working directory Claude Code has mounted, for parity:
kimi --add-dir /Users/Dev

# Model selection (config default is kimi-code/kimi-for-coding = K2.8, effort max):
kimi -m kimi-code/k3        # K3, 1M context, default effort high
```

There is no CLI flag for effort on this build — effort is set per-model in
`~/.kimi-code/config.toml` (`default_effort`) and globally under `[thinking]`.
If you want K3 at maximum, set `default_effort = "max"` under
`[models."kimi-code/k3"]` rather than looking for a flag that does not exist.

---

## §4 — The governance contract you are joining

Parity of tooling is the easy half. The reason three agents can share this repo
is that none of them treats its own chat history as project state.

1. **Read `CLAUDE.md` at the root, in full, before any substantive action.** Then
   follow its §C mandatory-reading sequence in order. Start with
   `CLAUDECODE_BRIEF.md` if it exists and its `status` is not `COMPLETE`.
2. **`00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 is the only "you are here."**
   Not `CLAUDE.md` §F, not this file, not a previous session's summary, and not
   what another agent told you in a different tool.
3. **Emit the session-open handshake** per
   `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`, including explicit
   `may_touch` / `must_not_touch` globs. An empty `must_not_touch` fails.
4. **Emit and validate the session-close checklist** per
   `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md` before claiming close.
5. **Git discipline:** work in this checkout on the current branch; never create a
   second clone. Other agents may be mid-work in this tree — check
   `git status` and `git worktree list` before destructive operations, and pull
   before starting.
6. **Doctrine that applies to you identically:** `CLAUDE.md` §N.4 (floors are
   aspirational, deterministic-first, verified migrations), §N.5 (L1 is authority
   over L2+ derivations — reference `fact_id`, never restate a computed value),
   §N.6 (serving density), §N.7 (narration fidelity), §N.8 (earned signal — a
   status or PASS with no detector behind it is null, not green).

---

## §5 — Report back

Produce a short table with one row per item in §2 and §3: **already true /
fixed now / cannot be replicated**, with the command output that proves it. Then
state which of the honest gaps in §6 apply to the work you are about to do.

Claim nothing as verified that you did not run. If `kimi doctor` or an MCP
handshake fails, report the failure — do not report the config file's existence
as if it were a working connection (that is exactly the §N.8 defect class).

---

## §6 — Honest non-parity (do not paper over these)

These cannot be closed by configuration on this build. Know them, and say so when
they affect a task:

- **No hooks.** Claude Code runs session hooks here (memory capture, context
  injection at session start). This build exposes no user-facing hook system, so
  observations from your sessions are not captured into the shared memory store,
  and you do not receive the memory digest Claude Code gets at open. Compensate
  by writing anything durable into the governed artifacts under
  `00_ARCHITECTURE/`, which is where it belongs anyway.
- **No plugin marketplace parity.** Claude Code loads a large plugin set
  (superpowers, claude-mem, chrome-devtools, playwright, context7, and others)
  whose skills and MCP tools you will not have. Repo-local skills in
  `.agents/skills` are shared; plugin-provided ones are not.
- **Claude-platform connectors are Claude-only.** Gmail, Google Drive/Calendar,
  Gamma, Webflow, Artifacts and similar are claude.ai-side connectors with no
  Kimi equivalent. Do not plan work that depends on them.
- **Subagent semantics differ.** The mirrored profiles in `.agents/agents` carry
  the same instructions, but orchestration (parallel dispatch, background tasks,
  workflow scripting) is not feature-identical. Same intent, not same machinery.
- **Session history does not cross tools.** Kimi sessions, Claude Code
  transcripts and Codex sessions are separate stores. The shared state channel is
  the git-tracked governed documents — `CURRENT_STATE`, `SESSION_LOG`, the briefs
  — never one tool's conversation.

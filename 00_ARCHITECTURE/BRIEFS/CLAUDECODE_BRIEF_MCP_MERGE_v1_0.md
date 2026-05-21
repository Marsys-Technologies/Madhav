---
artifact: CLAUDECODE_BRIEF_MCP_MERGE_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Claude Code sub-agent (MCP-0-AUTHOR)
authored_at: 2026-05-21
session_id: MCP-MERGE
session_name: MCP-MERGE — Push, open PR, enable auto-merge
executor: Claude Code sub-agent (general-purpose, spawned by MCP Conductor)
execution_mode: single autonomous session, --dangerously-skip-permissions
worktree:
  name: MadhavMCP
  branch: feature/mcp-server
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
governing_plan: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
reference_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
predecessor_session: MCP-4-S2 (red-team PASS)
next_session_anticipated: (none — workstream close)
---

# CLAUDECODE_BRIEF — MCP-MERGE
## Terminal session: push, open PR, enable auto-merge, seal workstream

---

## §0 — How to start this session

You are a sub-agent spawned by the MCP Conductor. Your context is fresh.
You are in the MadhavMCP worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`
on branch `feature/mcp-server`. The Conductor has already pasted your
session prompt; you are now reading this brief.

This is the **terminal session** for the MCP workstream. All 8 prior
sessions have completed (MCP-0-AUTHOR through MCP-4-S2). This session:
1. Verifies clean working tree.
2. Pushes the branch to remote.
3. Opens a PR.
4. Enables auto-merge (squash).
5. Authors the sealing artifact `MCP_WORKSTREAM_COMPLETE.md`.

**Native override:** `requires_human_approval: false` for this session
(explicit native authorisation 2026-05-21, recorded in `session_queue_MCP.yaml`
notes). The Conductor proceeds without waiting for a human PR review.

**Prerequisite check:** Before doing any push/PR work, verify the gate
command from MCP-4-S2 still passes (the red-team file must still have
"class-1 findings: 0" and "red-team status: PASS"). If that check fails
→ HALT_NEEDS_HUMAN immediately.

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | MCP-MERGE |
| Branch | `feature/mcp-server` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/MadhavMCP` |
| Execution mode | Single autonomous session, `--dangerously-skip-permissions` |
| Predecessor | MCP-4-S2 (red-team PASS) |
| Anticipated next | (none — workstream close) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` — **focus on §9 workstream-
   level acceptance criteria (AC.1–AC.8), §7.6 execution via Conductor,
   §12 cadence and sealing**
3. `00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md` — verify `red-team status: PASS`
   and `class-1 findings: 0` before proceeding
4. `00_ARCHITECTURE/CONDUCTOR/session_queue_MCP.yaml` — read the MCP-MERGE
   gate command exactly; the gate command IS the success criterion for this
   session

---

## §3 — Scope (6 items — execute in order)

### Item 1 — Prerequisite: verify clean working tree + red-team gate

**What:** Run the following checks:

```bash
# 1. Verify red-team gate still passes
test -f 00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md &&
grep -q "class-1 findings: 0" 00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md &&
grep -q "red-team status: PASS" 00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md &&
echo "Red-team gate: PASS"

# 2. Verify clean working tree
git status --short
# Expected: empty output (nothing uncommitted)

# 3. Confirm you're on the right branch
git branch --show-current
# Expected: feature/mcp-server
```

If any check fails → HALT_NEEDS_HUMAN immediately with details of what
failed.

**AC.MCP_MERGE.1:** Red-team gate passes; `git status --short` is empty;
branch is `feature/mcp-server`.

**Why:** Pushing dirty or failing state to remote creates a broken PR.
Prerequisite checks are the session's first action.

---

### Item 2 — Push branch to remote

**What:** Run:

```bash
git push -u origin feature/mcp-server
```

If push fails (e.g., remote already has a diverged version), do NOT
force-push. HALT_NEEDS_HUMAN with details of the failure.

**AC.MCP_MERGE.2:** `git push` exits 0; branch appears on remote.

**Why:** PR can only be opened once the branch is on the remote.

---

### Item 3 — Open pull request

**What:** Run `gh pr create` with a comprehensive body covering all 8
prior sessions, citing the master brief, listing AC coverage:

```bash
gh pr create \
  --title "feat(mcp): MARSYS-JIS MCP Server — workstream complete (MCP-0 through MCP-4-S2)" \
  --body "$(cat <<'PREOF'
## Summary

Ships the MARSYS-JIS Model Context Protocol Server as a Cloud Run sidecar
service (`amjis-mcp`), exposing 19 tools (16 read + 3 write) to Claude Chat
custom integrations and Cowork remote MCPs.

**Master brief:** `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md`
**Decisions settled:** D1–D13 (layered shape, API key auth, hosted HTTP/SSE,
singleton chart, no conversation history, full trace transparency)

## Sessions shipped

| Session | Scope | Status |
|---|---|---|
| MCP-0-AUTHOR | 7 sub-briefs authored | PASS |
| MCP-1-S1 | Migration 070, /api/mcp/execute, auth + envelope libs, admin keys UI | PASS |
| MCP-2-S1 | platform-mcp/ scaffold, server.ts, client.ts, Tier-1/2 tools | PASS |
| MCP-2-S2 | §4.6 tool descriptions, chart-overview.md, house-rules.md, resource registration | PASS |
| MCP-3-S1 | 10 surgical primitives + /api/mcp/primitives/[tool] dispatcher | PASS |
| MCP-3-S2 | read_asset, get_trace, list_recent_queries, per-key rate limiter | PASS |
| MCP-4-S1 | log_prediction, record_outcome, flag_disagreement + PPL interim path | PASS |
| MCP-4-S2 | Red-team pass §IS.8(b) — 0 class-1 findings | PASS |

## Workstream-level AC coverage

- AC.1 — All 19 tools callable from Claude Chat custom integration (operator smoke post-deploy)
- AC.2 — All 19 tools callable from Cowork remote MCP (operator smoke post-deploy)
- AC.3 — ask_madhav quality: held-out test set (post-merge, operator-run)
- AC.4 — Observatory dashboards show MCP traffic tagged source:"mcp" (post-deploy)
- AC.5 — Audit dashboard exposes MCP traces (post-deploy)
- AC.6 — Red-team PASS: 0 class-1 findings (MCP-4-S2 complete)
- AC.7 — platform-mcp/README.md covers setup, auth, all tools, envelope, errors
- AC.8 — OAuth (Phase 5) deferred per §7.5

## Governance

- **B.11 floor:** enforced in /api/mcp/execute for holistic/auto modes; synthesis_audit.holistic_read_passed present
- **Audience tier:** stamped from API key; passed via X-MCP-Audience-Tier; existing gates apply
- **Trace logging:** all MCP calls write to query_trace_steps; trace_id returned in every response
- **PPL discipline:** predictive ask_madhav calls auto-log to LEL prediction subsection (interim path)
- **Disclosure tier:** epistemics block mandatory on every response
- **No mirror pair:** MCP is Claude-side only per D9/G11
- **Rate limiting:** per-key 60 RPM + 500k token daily budget

## Post-merge operator steps

1. Apply migration 070 (`platform/supabase/migrations/070_mcp_api_keys.sql`)
2. Deploy `amjis-mcp` via Cloud Build (`platform-mcp/cloudbuild.yaml`) — set `PLATFORM_URL` env var
3. Register `amjis-mcp` as a Claude Chat custom integration (Bearer key from `/admin/mcp/keys`)
4. Register `amjis-mcp` as a Cowork remote MCP (same Bearer key)
5. Run smoke: `ask_madhav("What is my Atmakaraka?")` from Claude Chat → verify answer + trace
6. Flip `MARSYS_FLAG_OBSERVATORY_ENABLED=true` in Cloud Run to tag MCP traffic in Observatory (already live)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
PREOF
)"
```

Capture the PR number from the output.

**AC.MCP_MERGE.3:** PR created; URL logged; PR title and body correctly
describe the workstream.

**Why:** PR is the integration record for the workstream. The body serves
as the operator runbook for post-merge steps.

---

### Item 4 — Enable auto-merge

**What:** Run:

```bash
gh pr merge --auto --squash --delete-branch <pr_number>
```

Where `<pr_number>` is the number from Item 3.

If this command fails because CI is required and no CI exists → note in
FINAL_SUMMARY but do NOT halt. The native override authorises auto-merge
even if CI is minimal. If `gh` reports auto-merge enabled, that is PASS.

**AC.MCP_MERGE.4:** `gh pr merge --auto --squash` executed; command reports
auto-merge enabled or PR already merged.

**Why:** Per native authorisation in `session_queue_MCP.yaml` — this
workstream auto-merges without waiting for human PR review. Squash merge
keeps the main branch history clean.

---

### Item 5 — Author `MCP_WORKSTREAM_COMPLETE.md` sealing artifact

**What:** Author `00_ARCHITECTURE/MCP_WORKSTREAM_COMPLETE.md`:

```markdown
---
artifact: MCP_WORKSTREAM_COMPLETE.md
version: 1.0
status: SEALED
sealed_at: 2026-05-21
sealed_by: MCP-MERGE session (Claude Code sub-agent)
merge_commit_sha: PENDING_CI  # filled by operator post-merge
pr_number: <pr_number from Item 3>
pr_url: <pr_url>
---

# MCP Workstream — Sealing Artifact

**Workstream:** MCP — MARSYS-JIS Model Context Protocol Server
**Status:** SEALED (pending CI merge)
**Date:** 2026-05-21

## Sessions Completed

| Session | Description | Result |
|---|---|---|
| MCP-0-AUTHOR | Sub-brief authoring | PASS |
| MCP-1-S1 | Platform foundation | PASS |
| MCP-2-S1 | MCP server scaffold | PASS |
| MCP-2-S2 | Descriptions + resources | PASS |
| MCP-3-S1 | Surgical primitives | PASS |
| MCP-3-S2 | Observability + rate limiting | PASS |
| MCP-4-S1 | Write tools + PPL | PASS |
| MCP-4-S2 | Red-team (0 class-1) | PASS |
| MCP-MERGE | Push + PR + auto-merge | PASS |

## Artifacts Produced

- `platform/supabase/migrations/070_mcp_api_keys.sql`
- `platform/src/lib/mcp/` — auth, epistemics, rate_limiter, ppl_writer,
  primitives_registry, disagreement_writer
- `platform/src/app/api/mcp/` — execute, plan, keys, primitives, recent,
  asset, trace, writes
- `platform-mcp/` — full Node service: server.ts, client.ts, 19 tool files,
  2 resources, Dockerfile, cloudbuild.yaml
- `00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md` — 0 class-1 findings
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_*` — 8 execution briefs

## Operator Post-Merge Checklist

- [ ] Migration 070 applied
- [ ] amjis-mcp Cloud Run service deployed (set PLATFORM_URL env var)
- [ ] API key minted via /admin/mcp/keys for personal use
- [ ] Claude Chat custom integration registered
- [ ] Cowork remote MCP registered
- [ ] Smoke test: ask_madhav("What is my Atmakaraka?") returns coherent answer
- [ ] Observatory shows MCP traffic under source:"mcp"
- [ ] merge_commit_sha filled in above

## CLAUDE.md §E Update (post-merge, do in next session)

Add the following to CLAUDE.md §E (update "Nine workstreams" → "Ten workstreams"):

> - **MCP — MARSYS-JIS Model Context Protocol Server** — canonical_id
>   `MCP_BRIEF`, path `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md`.
>   **STATUS: COMPLETE (2026-05-21).** Workstream declared 2026-05-21 under
>   the Phase O / Chat V2 / Phase 4C / Conductor concurrent-workstream
>   precedent. Branch `feature/mcp-server` merged via PR #<pr_number>
>   (merge commit <sha>). 19 tools shipped: 1 end-to-end ask_madhav, 2
>   plan-introspection, 10 surgical primitives, 1 raw-asset read, 2
>   observability, 3 write tools (PPL + disagreement). Cloud Run sidecar
>   `amjis-mcp` in `asia-south1`. API key auth bound to Firebase UID +
>   audience_tier. Operator post-merge steps: see MCP_WORKSTREAM_COMPLETE.md.
```

**AC.MCP_MERGE.5:** `MCP_WORKSTREAM_COMPLETE.md` exists; all sections
present; PR number and URL filled in; CLAUDE.md §E update block drafted.

**Why:** Per CLAUDE.md §M — workstream closes with a sealing artifact.
The CLAUDE.md §E update is not applied in this session (it's in
must_not_touch) — it's drafted here as a block for the native or next
session to apply post-merge.

Commit: `docs(mcp): MCP-MERGE — MCP_WORKSTREAM_COMPLETE.md sealing artifact`

---

### Item 6 — Final gate verification

**What:** Run the gate command from `session_queue_MCP.yaml` MCP-MERGE:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCP &&
git push -u origin feature/mcp-server &&
gh pr view feature/mcp-server --json state,number 2>/dev/null | grep -q '"number"' &&
gh pr view feature/mcp-server --json autoMergeRequest,state | grep -E '"state":"MERGED"|"autoMergeRequest":\{'
```

Note: `git push` in the gate command will be a no-op (already pushed in
Item 2). The gate passes if the PR either has auto-merge enabled OR is
already merged.

**AC.MCP_MERGE.6:** Gate command exits 0.

---

## §4 — Session-open handshake

You are a Conductor sub-agent. State briefly at start:

"MCP-MERGE opening. Will verify clean state, push branch, open PR,
enable auto-merge, and author MCP_WORKSTREAM_COMPLETE.md. This is the
terminal session — native has pre-authorised auto-merge. Halt immediately
if red-team gate fails."

---

## §5 — Scope constraints

### may_touch

```
00_ARCHITECTURE/MCP_WORKSTREAM_COMPLETE.md                        # CREATE
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_MERGE_v1_0.md         # status flip PENDING → COMPLETE
```

### must_not_touch

```
platform/**                                                        # no code changes in terminal session
platform-mcp/**                                                    # no code changes in terminal session
01_FACTS_LAYER/**                                                  # sealed
025_HOLISTIC_SYNTHESIS/**                                          # sealed
00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md                              # sealed (read-only verification)
00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md                          # read-only
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                          # updated post-merge by native
CLAUDE.md                                                         # §E update is post-workstream; drafted in
                                                                  # MCP_WORKSTREAM_COMPLETE.md for native to apply
```

**Critical rule:** Do NOT force-push. If `git push` fails for any reason
other than "branch not on remote", HALT_NEEDS_HUMAN.

### Commit cadence

Only one commit in this session: the sealing artifact (`MCP_WORKSTREAM_COMPLETE.md`).
The commit will be squash-merged into main via the PR.

---

## §6 — Session-close checklist (FINAL_SUMMARY)

After all 6 items complete (or on first failure that causes HALT), emit:

```
---FINAL_SUMMARY---
session_id: MCP-MERGE
status: PASS | HALT_NEEDS_HUMAN
commits:
  - <sha_sealing_artifact>
scope_items_completed:
  - AC.MCP_MERGE.1   # clean state verified
  - AC.MCP_MERGE.2   # branch pushed
  - AC.MCP_MERGE.3   # PR opened
  - AC.MCP_MERGE.4   # auto-merge enabled
  - AC.MCP_MERGE.5   # MCP_WORKSTREAM_COMPLETE.md authored
  - AC.MCP_MERGE.6   # final gate passes
scope_items_failed: []
gate_command_runs:
  - name: mcp_merge_terminal_gate
    result: PASS | FAIL
notes_for_orchestrator: >
  MCP workstream complete. PR #<N> opened at <URL>. Auto-merge enabled
  (squash). MCP_WORKSTREAM_COMPLETE.md authored with post-merge operator
  checklist and CLAUDE.md §E update draft. Operator must apply migration
  070, deploy amjis-mcp Cloud Run service, and apply the §E update manually
  post-merge. merge_commit_sha placeholder in sealing artifact to be filled
  by native after CI lands.
human_decision_needed: >
  <empty if PASS>
  <If HALT: precise description of what failed and what decision is needed>
---END_FINAL_SUMMARY---
```

---

*End of CLAUDECODE_BRIEF_MCP_MERGE_v1_0.md.*

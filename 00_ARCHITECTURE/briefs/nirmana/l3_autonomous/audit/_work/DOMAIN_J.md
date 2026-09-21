# Domain J — Session and tooling (Kāla Readiness Audit)

Packet: verify the environment mechanics the L3 Kāla data-plane elevation campaign's parallel
Claude Code streams depend on — stream worktrees, permissions, transcript persistence, credential
routes, backup/restore. Read-only, static checks. Audit worktree:
`/Users/Dev/madhav-l3/audit` (branch `l3/kala-readiness-audit`).

---

## 1. Stream worktrees

**Command:** `git worktree list 2>&1`

**Result (relevant rows):**

| Path | Branch | Notes |
|---|---|---|
| `/Users/Dev/madhav-l3/audit` | `l3/kala-readiness-audit` | this audit session |
| `/Users/Dev/madhav-l3/integration` | `codex/madhav-l3-claude-code` (tip `5d8252dbe`) | the plan's named "integration worktree" |
| `/Users/Dev/.codex/worktrees/l3-bhavishya-p0` | `codex/l3-bhavishya-p0` | |
| `/Users/Dev/.codex/worktrees/l3-kshetra-p0` | `codex/l3-kshetra-p0` | |
| `/Users/Dev/.codex/worktrees/l3-kshetra-p0-correction` | `codex/l3-kshetra-p0-correction` | |
| `/Users/Dev/.codex/worktrees/l3-kshetra-w0-preservation` | `codex/l3-kshetra-w0-preservation` | |
| `/Users/Dev/.codex/worktrees/l3-u05-registry` | `codex/l3-u05-registry` | |
| `/Users/Dev/.codex/worktrees/l3-w0-field-contract` | `codex/l3-w0-field-contract` | |
| `/Users/Dev/.codex/worktrees/data-plane-l3-yojaka` | `codex/data-plane-l3-yojaka` | |
| `/Users/Dev/.codex/worktrees/l3-pr2695-review/Madhav` | detached HEAD | review worktree |
| plus ~150 other unrelated worktrees | (Codex fleet / Pūrṇa / other campaigns) | not in scope |

**Cross-reference against governing plan.** `00_ARCHITECTURE/briefs/nirmana/MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md`
does not exist on `main` (confirmed: `ls` → not found on this branch); it lives at v1.1 on
`origin/codex/madhav-l3-claude-code`, read via
`git show origin/codex/madhav-l3-claude-code:00_ARCHITECTURE/briefs/nirmana/MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md`.

That doc's §5 ("The Claude Code L3 execution model — what must differ from Codex's") does **not**
specify a fixed worktree-per-stream layout. Its actual rule (item 4) is **"One branch per
packet"** — e.g. `l3/p0-6-kshetra-p0-safety` — with each packet run in "own worktree" (per
`l3_autonomous/STATE.md`'s per-packet rows: D1–D6, E3, E4 all list `own worktree` as their
execution location), not a fixed pool of N pre-provisioned stream worktrees. Packet worktrees are
expected to be ephemeral (created per packet, not a standing inventory) — so the absence of a
persistent 1:1 worktree-per-stream directory tree is **not** a deviation from the plan; the plan
never specified one.

What the plan *does* name as a persistent worktree is the **integration worktree**:
`l3_autonomous/STATE.md` line 23: "Integration worktree + branch | ✅ `codex/madhav-l3-claude-code`
@ `cdc701afa`" and line 72: path `/Users/Dev/madhav-l3/integration`, branch
`codex/madhav-l3-claude-code`, state **DONE**, "clean @ `cdc701afa`". Live `git worktree list`
confirms this worktree exists at that exact path, on that exact branch, now at tip `5d8252dbe`
(descendant of `cdc701afa` — consistent with further commits landing since the STATE.md snapshot).
**This matches.**

**The 8 preservation branches.** The plan's Appendix B / §1.3 table (line 152/170) originally
flagged 8 branches (`codex/l3-bhavishya-p0`, `codex/l3-dhara-correction`,
`codex/l3-kshetra-p0`, `codex/l3-kshetra-p0-correction`, `codex/l3-kshetra-w0-preservation`,
`codex/l3-u05-registry`, `codex/l3-w0-field-contract`, `codex/data-plane-l3-yojaka`) as
**"all LOCAL-ONLY, never pushed"** — a named top risk (verdict item 7: "The single largest risk in
the picture is not technical... Push first, plan second"). Checked live:
`git ls-remote origin` returns all 8 as existing `refs/heads/...` on origin, AND `git worktree
list` shows each checked out locally under `/Users/Dev/.codex/worktrees/`. **The push has in fact
happened** — this matches the v1.1 changelog claim ("push (done, per A1)") and `STATE.md`'s
"Preservation branches on origin | 9 / 9 ✅" scorecard row (9, not 8 — one additional branch beyond
the plan's original list of 8; not independently reconciled in this packet, out of scope for J).

**Verdict: READY.** Both named worktree facts in the governing plan (integration worktree at
`/Users/Dev/madhav-l3/integration` on `codex/madhav-l3-claude-code`; the 8 preservation branches
pushed to origin) are independently confirmed live. The plan does not mandate a fixed
worktree-per-execution-stream pool, so its absence is not a gap.

---

## 2. Transcript persistence hazard

**Commands:**
```
grep -rn "CLAUDE_CODE_FORCE_SESSION_PERSISTENCE\|CLAUDE_CODE_CHILD_SESSION" \
  --include="*.sh" --include="*.md" --include="*.json" . 2>/dev/null | grep -v node_modules | head -30
```

**Result:** exactly one file, two lines:
```
00_ARCHITECTURE/briefs/nirmana/l3_autonomous/discussion_prompts/PROMPT_0_ENVIRONMENT_AND_ARCHITECTURE_AUDIT.md:257:launched from inside another inherits `CLAUDE_CODE_CHILD_SESSION` and silently becomes
00_ARCHITECTURE/briefs/nirmana/l3_autonomous/discussion_prompts/PROMPT_0_ENVIRONMENT_AND_ARCHITECTURE_AUDIT.md:258:non-resumable — set `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1`); credential routes; backup/restore.
```

This is the audit's own discussion-prompt file (the packet brief describing what to check) — i.e.
the hazard is documented as a known trap **in the audit's own prompt text**, not in any runbook,
launch script, `.claude/settings.json`, shell profile, or CI workflow that would actually set the
variable for a new session. No `.sh` launcher, no `settings.json`, no onboarding doc, and no CI
workflow anywhere in the repo sets `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE`. No mechanical
enforcement exists — a stream launched from inside another session today would still silently
inherit `CLAUDE_CODE_CHILD_SESSION` and become non-resumable, unless a human operator manually
exports the variable before invoking the child session.

**Verdict: NOT READY.** The hazard is known and named, but nothing in the repo — script, hook,
settings file, or runbook — mechanically sets `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1` before
spawning a nested/parallel session. This is a real operational gap for a campaign whose model
explicitly plans "one Claude Code session per packet or small group" possibly launched from a
conductor session.

---

## 3. Permissions

**Command:** `find . -name "settings*.json" -path "*.claude*" -not -path "*/node_modules/*" 2>/dev/null | head -20`

**Result:** `./.claude/settings.local.json` (this worktree). Broader search
(`/Users/Dev/madhav-l3/*`, `~/.claude`) also found:
- `/Users/Dev/madhav-l3/integration/.claude/settings.local.json` (the integration worktree)
- `/Users/Dev/.claude/settings.json` (global, not project-scoped — not read in detail; out of
  packet scope, flagged for completeness only)

**Content of `/Users/Dev/madhav-l3/audit/.claude/settings.local.json`:**
```json
{
  "dangerouslySkipPermissions": true
}
```

That is the entire file. There is **no allowlist, no denylist, no tool-permission scoping of any
kind** — `dangerouslySkipPermissions: true` is the harness-level flag that disables the permission
prompt/gate system altogether for this worktree's sessions.

**Assessment against the audit charter's stated expectations** (read-only by default, no git
mutations, no credential printing for subagents): **there is no enforcement mechanism**. The
settings file does not restrict Bash, Edit, Write, or git-mutation tool calls in any way; it
actively disables the one mechanism (`dangerouslySkipPermissions`) that could otherwise gate them.
Every constraint this audit (and the packet brief itself) has operated under — "read-only," "never
run mutating git commands," "never print credential values" — is enforced **only at the prompt
level** (the subagent's own instructions and the calling agent's discipline), not by any technical
control in `.claude/settings.json`. A subagent that chose to ignore its brief (or a future session
that inherits this settings file without the same brief) has no settings-level barrier stopping a
git push, a file deletion, or a `cat` of a secrets file.

**Verdict: NOT READY — no technical enforcement of the audit's stated safety constraints.**
The constraints are real and have been honored by this session, but they are honored by
instruction-following, not by settings-file enforcement. This is a load-bearing gap for a campaign
that plans many parallel unattended/semi-attended packet sessions: nothing in the actual harness
configuration stops a packet session from mutating git or printing a secret, only the prompt it
was given.

---

## 4. Credential routes

**Commands and results (no secret values printed):**
```
test -f /Users/Dev/madhav-l3/dbenv.sh && echo EXISTS          → dbenv.sh EXISTS
test -f /Users/Dev/madhav-l3/dbenv_builder.sh && echo EXISTS  → dbenv_builder.sh EXISTS
```

Structural shape (counts only, via `grep -c`, file contents never printed):

| File | Lines | `gcloud secrets` refs | `export PG*` refs |
|---|---|---|---|
| `/Users/Dev/madhav-l3/dbenv.sh` | 5 | 1 | 3 |
| `/Users/Dev/madhav-l3/dbenv_builder.sh` | 4 | 1 | 3 |

Both scripts are short (4–5 lines), each references `gcloud secrets` exactly once and exports
three `PG*`-prefixed variables — consistent with a thin wrapper that pulls a secret via `gcloud
secrets` and exports standard `PGHOST`/`PGUSER`/`PGPASSWORD`-shaped variables (exact names not
confirmed here, deliberately, to avoid a value-adjacent grep). No values were read, printed, or
sourced at any point in this packet.

**Verdict: READY.** Both credential-route scripts exist at the expected paths and structurally
route through `gcloud secrets` rather than hardcoding a value — the expected pattern. No secret
value was exposed during this check.

---

## 5. Backup/restore

**Commands:**
```
find 00_ARCHITECTURE -iname "*backup*" -o -iname "*rollback*" 2>/dev/null | grep -v node_modules | head -20
grep -rln "pg_dump\|backup" --include="*.md" --include="*.sh" 00_ARCHITECTURE/ platform/scripts/ 2>/dev/null | head -20
```

**Findings, in order of relevance:**

1. **A real, current DR runbook exists and is honest about its own untested state.**
   `00_ARCHITECTURE/briefs/pariprashna_swarm/G1_E_DURABILITY_DR_RUNBOOK_v1_0.md` (status: `CURRENT`,
   2026-08-19) explicitly scopes **all `kala_*` tables** (§2.2, "Layer tables tier, RPO/RTO 24h") —
   the L3 Kāla campaign's own output tables are named in its backup scope. But the frontmatter
   status line states in full: *"CURRENT — G1-E lane deliverable; **PITR enablement and the restore
   drill this runbook specifies are UNEXECUTED**, blocked on separate native authorization."* Body
   text (line 42–45) repeats this: *"It is not a record that PITR is enabled or that a drill has
   run... PITR on the production instance is **disabled** and **no restore drill has ever been
   executed**."* Its §5 is headed "PITR: verification and enablement commands **(NOT YET RUN)**."
   A companion doc, `G1_E_DURABILITY_STATUS_v1_0.md` (also `CURRENT`, same date), independently
   confirms: "The restore drill... [PPR-33 requirement]... a drill would run" — phrased as a
   not-yet-performed future action, not a completed one. No later artifact was found superseding
   either status.

2. **A separate mechanism (independent logical export) exists and partially *is* tested**, but
   covers a different, narrower table set (§2.1's "two irreplaceable table sets": conversations
   and prediction/outcome/audit ledger — **not** the `kala_*` layer tables). The script
   `platform/scripts/backup/export_irreplaceable_tables.sh` is real, plain `pg_dump`-based, and its
   companion `restore_irreplaceable_tables.sh` is named in-file. Separately, `G1_E_DURABILITY_DR_RUNBOOK_v1_0.md`
   itself records one genuine piece of live-tested evidence for the *mechanism* (not the campaign's
   own drill): "Verified directly (pg_dump 15.17): a `pg_dump` given multiple `--table` flags does
   not error when some (not all) tables are missing... dumps whatever it did find and exits 0" —
   this is a real, executed micro-test of `pg_dump` failure-mode behavior, not a full restore drill.

3. **One fully-tested restore precedent exists**, but for an unrelated, narrowly-scoped GA-3
   packet (found in `00_ARCHITECTURE/briefs/parisesa/state/ledger.json` / `journal.ndjson`,
   finding F-54's neighbor entry): "rollback GENUINELY rehearsed on a real scratch cluster after
   first verifying zero inbound FKs... fingerprint-verified restore." This demonstrates the
   *pattern* is achievable and has been done once elsewhere in the project, but it is not a
   standing, repeatable drill for the L3 Kāla campaign's `kala_*` tables and does not substitute
   for one.

4. **A stale, more pessimistic assessment also exists** in
   `00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md:3073`: "Backup / DR posture: **ABSENT
   in repo** | Only one-off tooling... **No scheduled backup job, no restore script, no PITR/RPO/RTO
   documentation, no DR runbook.**" This predates the G1-E runbook (which does now exist, contradicting
   the "no DR runbook" / "no PITR/RPO/RTO documentation" claims) — treated here as superseded
   by the G1-E artifacts, not as current fact, per the file's own apparent age relative to G1-E's
   2026-08-19 date. Flagged so a reader does not double-count it as an independent negative finding.

**Verdict: NOT READY (documented but unexecuted for the campaign's own data).** A real, current,
honestly-labeled DR runbook exists and correctly scopes `kala_*` tables into its 24h RPO/RTO tier —
this is real design work, not vaporware. But by the runbook's own frontmatter, **PITR is disabled
in production and no restore drill has ever been run** for that tier. The one fully-executed
restore-drill precedent in the repo (GA-3/parisesa) covers different tables under a different
authorization. If the L3 Kāla campaign needs to recover `kala_*` table state after a bad packet
merge or bad orchestrator run today, the only proven-live recovery path is the orchestrator
rebuild-from-`chart_facts` path the runbook itself names as the fallback justification for the
looser 24h target (§2.2) — not a Cloud SQL restore, which remains unexecuted and unauthorized.

---

## Domain J overall verdict: NOT READY

**Per-item summary:**

| Check | Verdict |
|---|---|
| 1. Stream worktrees | READY |
| 2. Transcript persistence hazard | NOT READY |
| 3. Permissions | NOT READY (no technical enforcement) |
| 4. Credential routes | READY |
| 5. Backup/restore | NOT READY (documented, unexecuted for campaign's own tables) |

**Overall: NOT READY**, on the strength of items 2, 3, and 5. None of these is a fabrication or an
absence of thought — in every case there is a real, named, honestly-labeled artifact acknowledging
the gap (the audit's own prompt names the session-persistence hazard; the DR runbook explicitly
flags itself as unexecuted; nothing hides behind a false PASS). But per CLAUDE.md §N.8 (Earned-Signal
Principle), a documented risk is not a mitigated risk: "it's usually true" or "nothing has broken
yet" is not a substitute for a real detector or control.

**What would have flipped this to READY:**
- Item 2: a launcher script, hook, or `.claude/settings.json` entry (project- or user-scoped) that
  sets `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1` automatically before any nested/nested-adjacent
  session spawn — instead of only appearing in prose inside the audit's own prompt file.
- Item 3: a `.claude/settings.json` (not `settings.local.json` with only `dangerouslySkipPermissions:
  true`) that carries an actual `permissions.allow` / `permissions.deny` list scoping Bash/Edit/Write
  to the read-only, no-git-mutation, no-credential-printing behavior the charter asserts — enforced
  by the harness, not merely instructed in a prompt.
- Item 5: either (a) PITR enabled on the production Cloud SQL instance with at least one executed
  restore drill against `kala_*` tables specifically (matching PPR-33's own stated requirement), or
  (b) if the orchestrator-rebuild path is the intended primary recovery mechanism for this tier
  (as the runbook's own text suggests), an explicit native ruling saying so — rather than the
  runbook currently naming Cloud SQL restore as "the first resort" while that resort has never
  actually been exercised.

**Items NOT found to be problems** (would have been findings if present, and were checked for):
no fabricated PASS/GREEN status anywhere in the searched files claiming these mechanisms work when
they don't; no secret value was inadvertently printed during this packet's execution; the two
worktree facts the governing plan actually commits to (integration worktree location/branch, 8
preservation branches pushed to origin) both independently verified live and matched.

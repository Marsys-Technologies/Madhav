---
artifact: LANE_G_ENVIRONMENT_SPEC
version: "1.0"
status: DRAFT
date: 2026-09-22
canonical_id: LANE_G_ENVIRONMENT_SPEC
scope: >
  Operational-readiness lane for the L3 Kāla elevation campaign (autonomous Claude Code sessions,
  many hours, parallel worktrees, native often asleep). Specifies exactly what the working
  environment must provide before the campaign starts, fixes the supervisor's confirmed defects,
  writes the mutation-era cycle contract, and registers every gap between current state and spec.
produced_by: L3 readiness lane G (environment/operational-readiness), read-only investigation only
  — no production mutation, no build dispatch, no campaign evidence events, no setup executed.
inputs_cited: >
  00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/KALA_CAMPAIGN_RUNBOOK_v1_0.md (§6 baseline),
  audit/_work/DOMAIN_J.md (session/permission/DR, verdict NOT READY),
  audit/_work/DOMAIN_G.md (cross-campaign safety), audit/_work/DOMAIN_E.md (release/delivery),
  audit/_work/DOMAIN_C.md (orchestrator/build-path, disposable-PG15 precedent),
  audit/KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md ("Environment readiness" split verdict + addendum),
  audit/KALA_PRIVILEGE_MATRIX_v1_0.md (F4 grant gap), audit/AUDIT_CHARTER.md (cycle contract +
  foreground-subagent law), /Users/Dev/madhav-l3/audit_supervisor.sh, redact.py, stream_format.sh
  (read directly, outside the repo, this session), live commands re-run this session (cited inline
  per CLAUDE.md §N.8 — no claim without a command or an explicit COULD NOT VERIFY).
---

# LANE_G_ENVIRONMENT_SPEC_v1_0 — L3 Kāla elevation campaign operational readiness

## 0. Reading guide

This spec assumes the reader has read `KALA_CAMPAIGN_RUNBOOK_v1_0.md` §6 (the audit's own
setup/runbook deliverable) — it is not repeated here. This document instead: (1) turns that
runbook's findings into an exact, checkable ENVIRONMENT SPEC for a **mutating** campaign (the
audit was read-only; elevation builds, mints evidence, writes migrations); (2) specifies the
SUPERVISOR FIX for the three confirmed defects (progress detector, idle backoff, plus one more);
(3) writes the CYCLE CONTRACT for elevation cycles; (4) registers every GAP with severity/owner/fix.

**Live re-verification performed this session** (read-only, no secrets printed): the readiness
worktree (`/Users/Dev/madhav-l3/readiness`) has **no** `.claude/settings.local.json` at all (`ls -la
.claude/` shows only `agents/` and `skills/` directories, no settings file) — a different posture
from the audit worktree (`dangerouslySkipPermissions: true`, no allow/deny list, per Domain J §3).
`platform/migrations/` on this branch confirms `1070_data_plane_builder_orchestrator_grants.sql`
present and `ls platform/migrations/ | grep -E '^(10[7-9][0-9]|11[01][0-9])_'` returns exactly that
one file — 1071–1119 genuinely open, matching CLAUDE.md and Domain E. `wc -l`/`grep -c` on
`dbenv.sh` (5 lines, 1 `gcloud secrets` ref) and `dbenv_builder.sh` (4 lines, 1 ref) reproduce
Domain J §4's structural finding exactly, without reading either file's contents.

---

## 1. THE ENVIRONMENT SPEC

### 1.1 Worktree topology

**Rule:** one worktree per elevation *stream*, plus one persistent *integration* worktree, plus
ephemeral per-packet worktrees only for anything that mutates production (migrations, dispatch,
evidence-minting repairs) — mirroring the audit's own `l3/egate-definition-scope` REPAIR-lane
pattern (`AUDIT_CHARTER.md` "Waves" §"REPAIR lane"), generalized.

| # | Path | Branch | Basis | Owns |
|---|---|---|---|---|
| 1 | `/Users/Dev/madhav-l3/integration` | `codex/madhav-l3-claude-code` | `origin/codex/madhav-l3-claude-code` (already exists — confirmed live, Domain J §1) | Reconciliation point; nothing builds here directly |
| 2 | `/Users/Dev/madhav-l3/kala-frontier` | `l3/kala-frontier-w<n>` | `origin/main` (fresh per wave) | Frontier stream packets (per `KALA_CAMPAIGN_RUNBOOK_v1_0.md` §8's three-stream partition) |
| 3 | `/Users/Dev/madhav-l3/kala-spine` | `l3/kala-spine-w<n>` | `origin/main` | Spine stream packets |
| 4 | `/Users/Dev/madhav-l3/kala-kshetra` | `l3/kala-kshetra-w<n>` | `origin/main` | Kshetra+Century stream packets |
| 5 (ephemeral) | `/Users/Dev/madhav-l3/kala-p<packet-id>` | `l3/p<n>-<slug>` | `origin/main` at dispatch time | One packet that mutates production (migration, dispatch, evidence mint) — created, used, PR'd, torn down |

**Ownership rule (one lane owns one asset-cluster; no two lanes touch the same `ka_*` writer file
concurrently):** the three stream worktrees map 1:1 onto the three execution streams the runbook
already defines (`KALA_CAMPAIGN_RUNBOOK_v1_0.md` §8, citing `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md`
§4's Frontier/Spine/Kshetra+Century partition) — **not** a fixed 1:1 worktree-per-`ka_*`-asset
scheme, because the governing plan never specified that granularity (Domain J §1: "the plan does
not mandate a fixed pool of pre-provisioned stream worktrees... one branch per packet"). A packet
that needs its own isolation (anything touching one of the 7 hub modules in
`KALA_CAMPAIGN_RUNBOOK_v1_0.md` §6 item 6, or any production mutation) gets an ephemeral worktree
per row 5, never a shared mutable stream checkout.

**Exact commands:**
```bash
git worktree add /Users/Dev/madhav-l3/kala-frontier -b l3/kala-frontier-w1 origin/main
git worktree add /Users/Dev/madhav-l3/kala-spine -b l3/kala-spine-w1 origin/main
git worktree add /Users/Dev/madhav-l3/kala-kshetra -b l3/kala-kshetra-w1 origin/main
```
Per packet mutation: `git worktree add /Users/Dev/madhav-l3/kala-p<id> -b l3/p<n>-<slug> origin/main`,
then remove after merge: `git worktree remove /Users/Dev/madhav-l3/kala-p<id>`.

**COULD NOT VERIFY:** whether `git worktree add` at this fleet's current scale (the live
`git worktree list` this session showed >130 existing worktrees under `/private/tmp/` alone, mostly
`prunable`) hits any filesystem/inode limit in practice — not tested; recommend `git worktree prune`
as a standing pre-flight step (§1.7) rather than assuming headroom.

### 1.2 DB access — two identities, enforced read-only

**Two identities, both already built** (Domain J §4, re-confirmed structurally this session):

| Identity | Script | Role | Use |
|---|---|---|---|
| Read-only general | `source /Users/Dev/madhav-l3/dbenv.sh` | `amjis_app` | DAG facts, event counts, physical build state, readiness queries |
| Read-only privilege introspection | `source /Users/Dev/madhav-l3/dbenv_builder.sh` | `data_plane_builder`, **queried read-only** | `has_table_privilege` sweeps, never used to build in this mode |

**Enforcement that a read-only session cannot mutate:** both scripts "force
`default_transaction_read_only=on`" (`AUDIT_CHARTER.md` §"Database access", verified live by Domain
J/Runbook §4: `psql -Atq -c "SELECT current_user, current_setting('default_transaction_read_only')"`
→ `amjis_app|on`). This is a **session-GUC-level** enforcement, not a role-grant-level one — i.e. it
relies on the connecting script setting the GUC, not on the DB role itself being revoked write
privileges. **Gap (see §4):** COULD NOT VERIFY from the audit record whether `amjis_app` is *also*
denied write grants at the role level (defense in depth) — if the GUC is the only barrier, a
session that connects directly with `psql "$SOME_OTHER_CONNSTRING"` bypassing `dbenv.sh` gets a
writable connection under the same role. **Spec requirement:** confirm (or add)
`ALTER ROLE amjis_app NOSUPERUSER NOCREATEDB NOCREATEROLE; REVOKE INSERT, UPDATE, DELETE, TRUNCATE
ON ALL TABLES IN SCHEMA public, nirmana_evidence FROM amjis_app;` as a role-level backstop,
independent of the GUC.

**A THIRD identity is required for the campaign that the audit never needed:** a genuine
**builder/write** identity for actual asset builds and migration application, kept structurally
separate from both read-only helpers above so a session sourcing the wrong file cannot
accidentally write. Recommend `dbenv_write.sh` (new, not yet built — GAP, see §4) with the same
five-line shape as `dbenv.sh`, sourcing a distinct secret (e.g. `amjis-nirmana-executor` per the
already-existing GCP SA impersonation route named in `KALA_CAMPAIGN_RUNBOOK_v1_0.md` §4), and
**never** forcing `default_transaction_read_only=on`.

### 1.3 DISPOSABLE-POSTGRES harness

**Generalizing Domain C's proven pattern** (`audit/_work/DOMAIN_C.md` §8 — the only property that
"cannot be meaningfully asserted with a fake cursor," proven on a real, throwaway local PG15):

```bash
# 1. Stand up
DATADIR=$(mktemp -d)/pgdata
/opt/homebrew/opt/postgresql@15/bin/initdb -D "$DATADIR" -U testuser --auth=trust
/opt/homebrew/opt/postgresql@15/bin/pg_ctl -D "$DATADIR" \
  -o "-p 59321 -k $DATADIR" -l /tmp/kala_disposable_pg.log start

# 2. Load schema — the project's own migration runner against the disposable instance
#    (never against production; point PG* env at 127.0.0.1:59321/testuser first)
export PGHOST=127.0.0.1 PGPORT=59321 PGUSER=testuser PGDATABASE=postgres
cd platform && npm run migrate   # or the equivalent migrate.ts invocation used by CI

# 3. Seed one chart's upstream data — export/import the canonical chart's L0-L2 rows only
#    (never L3 kala_* output — that is what the harness is proving), via the read-only
#    identity for export, disposable instance for import:
source /Users/Dev/madhav-l3/dbenv.sh
pg_dump "$PG_READONLY_CONNSTRING" \
  --table='chart_facts' --table='ga_*' --table='bodha_*' \
  --where="chart_id = '482012f1-710e-4a25-994a-93821f5871aa'" \
  --data-only -Fc -f /tmp/canonical_upstream.dump
pg_restore -h 127.0.0.1 -p 59321 -U testuser -d postgres /tmp/canonical_upstream.dump

# 4. Prove the build — dispatch the orchestrator against the disposable instance only
python3 pipeline/orchestrator/runner.py --chart-id 482012f1-... --asset-id ka_<target>

# 5. Tear down — always, even on failure
/opt/homebrew/opt/postgresql@15/bin/pg_ctl -D "$DATADIR" stop -m fast
rm -rf "$(dirname "$DATADIR")"
ps aux | grep kala_disposable && echo "LEAK: kill it"   # verify no leftover process
```

**Why this is load-bearing for the campaign, not optional:** every migration this campaign writes
(range 1071–1119, §1.6) and every writer-code change to a hub module (§1.6) should be proven against
this harness *before* touching production, because the campaign's charter forbids build dispatch
against the canonical chart for anything not already gated by the acceptance machinery. Domain C's
own precedent is explicitly named by the runbook (§4, §5.2) as "the correct model to follow for
generation-function proofs too, rather than any canonical-chart or production-DB exercise."

**GAP:** `pg_dump --where` scoped exactly as above was **not actually run** by any audit packet
(Domain C ran schema-less advisory-lock tests only, no data load) — this session did not execute it
either (setup execution is explicitly out of scope). **COULD NOT VERIFY:** the exact
`npm run migrate` invocation signature, or whether the schema loads cleanly on a bare PG15 without
extensions the production Cloud SQL instance has pre-installed (e.g. `pgcrypto`, `pg_trgm` — not
checked this session). This is GAP #6 in §4.

### 1.4 Credential hygiene

**The redactor's role** (`redact.py`, read in full this session): it loads secret **values** once
per invocation via `gcloud secrets versions access` for a fixed list of 7 named secrets, holds them
**in memory only**, and (a) in stream mode, filters every stdout line through string-replace before
it ever reaches a log file or terminal; (b) in `--scrub` mode, walks a directory tree afterward and
replaces any surviving occurrence in-place. This is **defense in depth, explicitly not primary
prevention** — the charter's own incident note says so: "The supervisor now redacts known secret
values from its logs and scrubs transcripts after every cycle — that is a safety net, not
permission. Do not repeat it" (`AUDIT_CHARTER.md` line ~108).

**What must never be echoed** (verbatim from the charter, binding on every elevation cycle too):
`gcloud secrets versions access` (subagents never call it directly — only `dbenv*.sh` may), `echo`,
`printenv`, `env`, `set -x`, or interpolating a credential into a command line, file, report, or a
prompt handed to a subagent. Extend this list for the mutating campaign: **never paste a
`DATABASE_URL`, a service-account JSON key, or an `Authorization:` header value into a migration
file, a commit message, or a PR body** — none of these existed as incident vectors in the read-only
audit but are new surface area for a campaign that authors migrations and dispatches builds.

**Pre/post-cycle scrub, exact commands (from `audit_supervisor.sh` lines 52/55, generalized):**
```bash
# pre-cycle: nothing extra needed — the redactor loads fresh each invocation
# streaming: pipe every claude -p invocation through the redactor before tee/logging
claude -p ... | python3 -u /Users/Dev/madhav-l3/redact.py 2>>redact.log | tee cycle.ndjson | stream_format.sh
# post-cycle: scrub the cycle's own logs AND the session's own transcript directory
python3 /Users/Dev/madhav-l3/redact.py --scrub "$LOGD" "$HOME"/.claude/projects/-Users-Dev-madhav-l3-<worktree>*
```
**Structural-unlikelihood requirement (per incident A):** the spec's job is to make leakage
*structurally unlikely*, not merely scrubbed. Concretely: (1) `dbenv.sh`/`dbenv_builder.sh` must
remain the **only** sanctioned code path to a live credential — no cycle prompt, charter, or
brief may ever instruct a subagent to run `gcloud secrets versions access` itself (this is already
the rule; keep it); (2) every `claude -p` invocation in the supervisor must be piped through
`redact.py` **before** any `tee`/log-write, never after (already true in `audit_supervisor.sh`
line 52 — preserve this ordering in the elevation supervisor); (3) subagent briefs must carry the
two `source` lines **verbatim** and the prohibition **verbatim** (already the charter's own
instruction — carry forward unchanged).

### 1.5 Session posture

**Current state (verified live, this worktree, this session):** `/Users/Dev/madhav-l3/readiness`
has **no** `.claude/settings.local.json` at all. The **audit** worktree
(`/Users/Dev/madhav-l3/audit`) had exactly `{"dangerouslySkipPermissions": true}` and nothing else
(Domain J §3, cited, not re-fetched — that worktree is out of this session's scope to re-read).

**Why `--dangerously-skip-permissions` with no allow/deny scope is a gap (Domain J §3, concurred):**
it disables the *only* harness-level control that could stop a session from running a destructive
git command, printing a secret, or mutating a file outside its brief — every constraint in the
audit charter ("read-only," "never run mutating git," "never print credentials") was enforced
**purely by the prompt text**, with zero technical backstop. For a read-only audit this was a
tolerable (if flagged) risk; for a campaign whose cycles *legitimately* need to run `git commit`,
`git push`, `psql` writes, and `gh pr merge`, the fix is not to re-add full manual approval
(that would stall an unattended overnight run at every tool call) — it is a **scoped allow list**
that names exactly the mutating operations the campaign's own charter already authorizes, and
denies everything else.

**Concrete env vars (from the incident record, §E above CLAUDE.md context):**
```bash
unset CLAUDE_CODE_CHILD_SESSION
export CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1
```
must be set **before every nested/parallel session spawn** — currently this appears only as prose
in one audit prompt file (Domain J §2: exactly one file, two lines, zero mechanical enforcement).
`audit_supervisor.sh` line 8 *does* set both at the top of the supervisor script itself — this is
correct for the top-level supervisor-launched session, but does **not** propagate to any session a
conductor spawns as a nested/background child from *inside* its own turn (the exact case Domain J
flags as unenforced). **Spec requirement:** every `Agent`-tool subagent dispatch inherits these two
already (because they are process-level env vars set once by the supervisor and inherited by all
children) — the real gap is a *human or conductor* manually launching a second top-level `claude`
session from inside a first one without going through the supervisor's env block. Fix: no cycle
prompt or runbook may instruct spawning a nested top-level session; all parallelism goes through
`Agent` tool calls (in-process subagents), which is exactly what the foreground-subagent law in
§1.5 below already mandates for a different reason.

**Proposed concrete allow/deny list for this campaign** (`.claude/settings.json`, not
`settings.local.json` — project-scoped, checked in, reviewable):
```json
{
  "permissions": {
    "allow": [
      "Bash(git status)", "Bash(git diff*)", "Bash(git log*)", "Bash(git add*)",
      "Bash(git commit*)", "Bash(git push*)", "Bash(git worktree*)", "Bash(git fetch*)",
      "Bash(git show*)", "Bash(git merge*)", "Bash(git rebase origin/main)",
      "Bash(gh pr *)", "Bash(gh run *)", "Bash(gh api repos/Marsys-Technologies/Madhav/*)",
      "Bash(gh workflow run deploy.yml*)",
      "Bash(psql -Atq*)", "Bash(source /Users/Dev/madhav-l3/dbenv.sh)",
      "Bash(source /Users/Dev/madhav-l3/dbenv_builder.sh)",
      "Bash(python3 -m pytest*)", "Bash(npm run *)", "Bash(npm test*)",
      "Read(**)", "Grep(**)", "Glob(**)", "Edit(platform/**)", "Write(platform/**)",
      "Edit(00_ARCHITECTURE/briefs/nirmana/**)", "Write(00_ARCHITECTURE/briefs/nirmana/**)"
    ],
    "deny": [
      "Bash(git push --force*)", "Bash(git reset --hard*)", "Bash(git branch -D*)",
      "Bash(git checkout .*)", "Bash(git clean -f*)",
      "Bash(gcloud secrets versions access*)", "Bash(*echo*PASSWORD*)", "Bash(*printenv*)",
      "Bash(*set -x*)",
      "Edit(.github/workflows/deploy.yml)", "Write(.github/workflows/deploy.yml)",
      "Edit(platform/migrations/10[0-6]*)", "Edit(platform/migrations/1042*)",
      "Edit(platform/migrations/104[3-9]*)", "Edit(platform/migrations/105*)",
      "Edit(platform/migrations/106*)", "Edit(platform/migrations/1070*)",
      "Edit(00_ARCHITECTURE/briefs/pariprashna_swarm/**)",
      "Edit(platform/tests/pariprashna/**)", "Write(platform/tests/pariprashna/**)",
      "Edit(00_ARCHITECTURE/briefs/nirmana/purna_anvesana/**)"
    ]
  }
}
```
This is a **starting proposal, not a validated final list** — it must be reviewed by whoever owns
`.claude/settings.json` conventions for this repo before being committed; the deny list encodes the
charter's "Forbidden — no exceptions" section (production-mutation classes, workflow-file edits,
Pūrṇa-owned surfaces) as harness-level denials rather than prompt-level instructions, which is
exactly the technical backstop Domain J found missing. **This is itself GAP #2 in §4** until
someone actually authors and commits this file.

### 1.6 Git/GitHub discipline

**Branch naming:** `l3/<stream>-<wave>` for stream worktrees (§1.1), `l3/p<n>-<slug>` for individual
mutating packets (matching the runbook's own `l3/p0-6-kshetra-p0-safety`, `l3/p1-3-graha-sancara-
consumer-route` examples, §7 of the runbook).

**Merge-queue interaction:** confirmed live and enforced (Domain E §5) — ruleset id `20141220` on
`refs/heads/main`, `enforcement: "active"`, `current_user_can_bypass: "never"`, merge_queue
`merge_method SQUASH`, `grouping_strategy ALLGREEN`. **Consequence for a lane proving its work
landed:** commit ancestry on `main` is not the same as "my branch's tip is an ancestor of `main`"
— squash-merge rewrites the SHA (the charter's own named trap: "PR #2607 squash-delivered work
whose original SHAs are not ancestors of main. Check content."). **Push-verification rule:** after
`gh pr merge --squash --auto`, a lane proves landing by (a) `gh pr view <n> --json state,mergedAt`
showing `MERGED`, then (b) **content presence**, not ancestry — `git log --oneline -1 -- <the exact
files the PR touched>` on a freshly-fetched `origin/main`, confirming the file's content matches
what the PR claimed, not merely that some commit exists.

**Merge-queue silent-rejection incident (G):** a merge-queue lock silently rejected pushes for
several cycles in the prior run. **Fix:** after every `git push`, check the actual exit code and, on
non-fast-forward or queue rejection, `git fetch && git rebase origin/<branch> && git push` — never
assume a `0`-looking `gh pr merge --auto` call means the merge has actually queued; poll
`gh pr view <n> --json mergeStateStatus,autoMergeRequest` once (not in a sleep loop — see §2) before
ending the cycle that issued the merge command.

**zsh trap (F):** `"refs/heads/$b:refs/heads/$b"` is parsed as history modifier `:r` and silently
mangles the refspec. **Rule:** always brace variable interpolation in any git refspec:
`"refs/heads/${b}:refs/heads/${b}"`. Apply this rule to every script this spec introduces.

### 1.7 Migration discipline

**Reserved range: L3 = 1071–1119** (1070 consumed by
`1070_data_plane_builder_orchestrator_grants.sql`, confirmed live this session and by Domain E §4).
Pūrṇa owns 1042–1069 (currently only partially filed — 1043–1069 do not exist as files in this
checkout, per Domain E §4, reserved-not-yet-used); cross-cutting is 1120+ by logged request.

**No CI enforcement of the numeric partition exists** (Domain G §3/§4, Domain E §4 — both
independently grepped `.github/workflows/*.yml` for "1070"/"1120" and found neither). **Rule for
claiming a number without collision, given Pūrṇa shares the repo:**
1. Before authoring, `git fetch origin main && ls origin/main:platform/migrations/ | grep -E
   '^11[0-1][0-9]_'` (via `git show origin/main:platform/migrations/` listing, or a fresh
   `git pull` on a scratch checkout) to see the highest number **actually on `main`**, not just in
   your own worktree — another L3 packet or a not-yet-merged PR may have already claimed the next
   number.
2. Check `origin/campaign-coordination`'s `CAMPAIGN_COORDINATION.md` §"migration numbering" log (if
   one exists — GAP if it doesn't, see §4) for any in-flight claim not yet on `main`.
3. Claim the number by opening the PR immediately (not by reserving it in a doc first) — the merge
   queue's own non-fast-forward/ALLGREEN grouping is the actual collision guard once the PR exists;
   a doc-only reservation has no teeth.
4. **Never edit an applied migration file** (CLAUDE.md §N.4, restated for L3: 1033–1070 applied,
   never touch).

### 1.8 Observability

**What the native should see at a glance, and from where:**

| Surface | What it shows | Where |
|---|---|---|
| `AUDIT_STATE.md`-equivalent for elevation (`KALA_ELEVATION_STATE.md`) | Position line, packet table, `Accepted N/22`, native decision list, budget counters | `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/elevation/` (new, mirrors the audit's own state-file convention) |
| Supervisor log | Per-cycle START/END, progress yes/no, cost | `$LOGD/supervisor.log`, tailable via `audit_supervisor.sh status`-equivalent |
| `origin/campaign-coordination` lease table | Whether L3 or Pūrṇa currently holds the shared-surface lease | `CAMPAIGN_COORDINATION.md` §1 — **read by expiry timestamp, never by string-matching `status`** (Domain G's explicit, empirically-demonstrated warning: 6 stale `ACTIVE` rows found live) |
| `nirmana_evidence.nirmana_elevation_campaign_events` | The only ground truth for `Accepted N/22` | Queried via the §2 readiness query (`kala_readiness_query_v2.sql`), never eyeballed from a state file |
| GitHub PR/Actions | CI status, merge-queue position, deploy job results | `gh pr list --author <campaign-bot>`, `gh run list --workflow=deploy.yml` |
| macOS notification (`osascript`) | Halt/complete signal | Already wired in `audit_supervisor.sh` lines 16, 61-62, 65-67 — carry forward unchanged |

**Two metrics never conflated** (per the runbook §8 item 3, restated as an observability
requirement): the Phase-0 scorecard and the campaign metric `Accepted N/22` must render as two
distinct fields in `KALA_ELEVATION_STATE.md`, never one derived from the other.

---

## 2. THE SUPERVISOR FIX

All three changes below are to `/Users/Dev/madhav-l3/audit_supervisor.sh`, which this spec assumes
is copied to `elevation_supervisor.sh` and adapted (not overwritten in place, since the audit's own
supervisor is a historical artifact of a different, read-only campaign). Line numbers below refer
to the file as read this session.

### 2.1 Progress detector (confirmed defect C)

**Current code (lines 17, 48, 56-59):**
```bash
fingerprint() { { git -C "$WT" rev-parse HEAD; git -C "$WT" status --porcelain; shasum "$A/AUDIT_STATE.md" 2>/dev/null; ls -1 "$A" "$A/_work" 2>/dev/null; } | shasum | cut -c1-16; }
...
before=$(fingerprint); raw="$LOGD/cycle_$n.ndjson"
...
after=$(fingerprint)
...
if [ "$before" = "$after" ]; then noprog=$((noprog+1)); else noprog=0; fi
```

**Defect:** `git status --porcelain` output is part of the fingerprint, and `ls -1` of the audit
directories changes on *any* file touch — including a cycle that only polled CI, wrote a scratch
note, or touched a file's mtime without adding real content. This makes "progress" trivially easy
to satisfy without doing anything the campaign actually needs, so 3-consecutive-no-progress can
never fire even during a genuine stall (confirmed defect, per the task brief — 5 consecutive cycles
spent ~$0.80 each polling CI logged `progress=yes`).

**Fix — replace `fingerprint()` with a definition of progress that means something for a mutating
campaign:** progress is a new commit on the campaign branch (not merely a dirty tree) **and/or** a
new row in the ground-truth evidence table **and/or** a state-file field that actually changed
value (not just mtime). Concretely:

```bash
# REPLACEMENT for fingerprint() — measures campaign-meaningful progress, not any file touch.
fingerprint() {
  local head_sha accepted_n state_hash
  head_sha=$(git -C "$WT" rev-parse HEAD 2>/dev/null)
  # Accepted N/22 is the one number that must never be gamed by a no-op cycle — read it from
  # the state file's own declared counter, not derived from file-touch activity.
  accepted_n=$(grep -oE 'Accepted [0-9]+/22' "$A/KALA_ELEVATION_STATE.md" 2>/dev/null | head -1)
  # Hash only the CONTENT of the state file's substantive sections (position + packet table +
  # decision list), not its mtime and not a directory listing.
  state_hash=$(sed -n '/^## Position/,/^## End/p' "$A/KALA_ELEVATION_STATE.md" 2>/dev/null | shasum | cut -c1-16)
  echo "${head_sha}|${accepted_n}|${state_hash}"
}
```

`before=$(fingerprint)` / `after=$(fingerprint)` calls stay as-is; only the function body changes.
**Why this fixes the defect:** a cycle that only polls CI and touches no committed content, mints no
evidence, and leaves the state file's substantive sections byte-identical now produces
`before == after` correctly — "polling with nothing to report" is genuinely indistinguishable from
"did nothing," which is the honest answer the 3-strikes halt is supposed to detect.

**Residual risk, named honestly:** a cycle could still game this by making a cosmetic, no-op commit
(e.g. a whitespace change) to move `head_sha`. This spec does not attempt to close that
adversarial case — the campaign's own honest-stop rule (§3) is the actual defense against that,
not the supervisor's mechanical detector; a detector cannot fully substitute for an honest agent,
only catch the honest agent's own accidental false-positive class (which is what defect C actually
was).

### 2.2 Idle backoff (confirmed defect D)

**Current code (line 63):**
```bash
[ $crash -ge 3 ] && sleep "$CRASH_SLEEP" || sleep "$CYCLE_SLEEP"
```
Only two sleep tiers exist: a fixed 30s between every normal cycle, and 300s after 3+ consecutive
crashes. **Nothing scales with consecutive no-progress** short of the full 3-strikes halt — a run
that is idling (genuinely nothing eligible, correctly reporting `IDLE-OK` per the charter's own
no-idle law) still gets re-invoked every 30s, at full cost, for up to 2 more cycles before halting.

**Fix — exponential backoff keyed on `noprog`, distinct from the crash backoff:**
```bash
# REPLACEMENT for the sleep line — idle backoff distinct from crash backoff.
if [ $crash -ge 3 ]; then
  sleep "$CRASH_SLEEP"
elif [ $noprog -ge 1 ]; then
  # 1st no-progress: 5min; 2nd: 15min; halts on the 3rd per existing law — no need for a 3rd tier.
  idle_sleep=$(( noprog == 1 ? 300 : 900 ))
  say "idle backoff: no-progress streak=$noprog, sleeping ${idle_sleep}s before retry"
  sleep "$idle_sleep"
else
  sleep "$CYCLE_SLEEP"
fi
```
**Why this fixes defect D:** once the (now-honest, per §2.1) progress detector correctly identifies
an idle cycle, the second cycle waits 5 minutes and the third waits 15 before the existing 3-strikes
halt fires — instead of three full-cost cycles fired 30 seconds apart. This does not change *when*
the halt fires (still 3 consecutive), only *how expensively* the campaign waits for the halt to
trigger, directly addressing "five consecutive cycles spent ~$0.80 each polling CI with nothing to
do."

### 2.3 Additional unsafe pattern found this session (not in the original three)

**Line 50-52** dispatches the cycle via `claude -p --dangerously-skip-permissions ...` directly —
i.e. the supervisor itself hardcodes the same no-scope permission bypass Domain J flagged as a gap
(§1.5 above). **Fix:** once `.claude/settings.json` (§1.5) carries a real allow/deny list, the
supervisor should drop `--dangerously-skip-permissions` entirely and rely on the settings file, OR
(if full unattended operation genuinely requires bypassing the interactive prompt even with a
settings file present) pass `--permission-mode acceptEdits` or an equivalent narrower flag if the
harness supports one — **COULD NOT VERIFY** which flag combination the installed Claude Code
version supports for "obey settings.json but never block on a prompt"; this is a question for
whoever authors the actual elevation supervisor script, flagged here rather than guessed at.

---

## 3. THE CYCLE CONTRACT for elevation cycles

Adapted from `AUDIT_CHARTER.md` for a campaign that **mutates** (builds assets, mints evidence, ports
migrations) rather than one that only reads.

### 3.1 What a cycle may do unattended

- Read anything under `00_ARCHITECTURE/`, `platform/` (all subtrees) subject to the deny list (§1.5).
- Run the readiness query (§1.8) and any other read-only diagnostic against `dbenv.sh`/
  `dbenv_builder.sh` at will, with no cap.
- Build/rebuild an L3 `ka_*` asset **only** against the disposable-Postgres harness (§1.3) or a
  non-canonical chart — never the canonical chart `482012f1-710e-4a25-994a-93821f5871aa` — unless
  the specific packet is explicitly authorized for canonical-chart dispatch per the acceptance
  machinery (`nrec --as executor`) AND holds a currently-valid lease on
  `origin/campaign-coordination` (checked by expiry timestamp, §1.8) AND the F2/F4/F8/E-1..E-4
  blockers named in `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` §2a are cleared for that specific
  asset (see §4 GAP register — as of this spec, **zero** assets clear this bar).
- Author a migration in range 1071–1119 (§1.7), open a PR, run it through the merge queue.
- Commit, push, open/merge PRs, re-arm auto-merge, per the same authorization the audit charter
  already grants (`AUDIT_CHARTER.md` §"Git, PR, merge, deploy").
- Claim/release a lease on `origin/campaign-coordination` for any of the five shared surfaces.

### 3.2 What requires the native

- Any of the 20 items in `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` §3's ordered decision list —
  no cycle may unilaterally rule on F2 (definition inheritance), the missing acceptance-receipt
  design, the CASCADE data-loss remediation, PR #2695's override, or any of the other 16.
- Dispatching a build against the **canonical chart** for any asset not already explicitly cleared
  by a native ruling on the above (this is stricter than the audit's own charter because the
  elevation campaign, unlike the audit, has the *capability* to dispatch — the capability existing
  is exactly why this line must be explicit here).
- Weakening, disabling, or working around the `ka_gochara_v3_century_materialize` BUILD-PROTECTED
  guard ("PARISHKARA MR-06") under any circumstance — this is a native-decision-required safety
  mechanism, not a bug to fix.
- Enabling PITR or running a restore drill against production (§4 GAP #5) — infra-provisioning
  decision, not a cycle's to make.
- Any edit inside a Pūrṇa-owned surface (per Domain G §1's territory list) or the `L3_kala/**`
  registry directory's *availability-contract metadata* read by Pūrṇa (§1.6's shared-surface #4) —
  a semantic change there is an `L3-REQ-nn` log entry, never a direct edit.

### 3.3 How a cycle proves what it claims

Same evidentiary bar the audit already established, restated for build claims specifically:
- A freeze/acceptance event claim is proven by re-querying `nirmana_evidence.
  nirmana_elevation_campaign_events` filtered by the **current** `definition_revision` (never
  unscoped — this is literally finding F1) and pasting the live row, not a prior cycle's citation.
- A "build succeeded" claim is proven by `asset_throughput.state='lit'` **and** (for
  `has_substeps=true` writers) the SATYA-DĪPA completeness re-probe passing — i.e. by the same
  earned-signal standard CLAUDE.md §N.8 already demands, not by "the writer didn't throw."
- A "PR landed" claim is proven by content presence on a freshly-fetched `origin/main`, not commit
  ancestry (§1.6) — this is a NEW proof requirement beyond what the read-only audit ever needed to
  claim, because the audit never had its own writer-code PRs landing under squash-merge at volume.
- A disposable-PG15 proof (§1.3) is proven by pasting the actual `psql`/`pytest` output, and by an
  explicit "torn down, confirmed no leftover process" line — matching Domain C's own standard
  exactly (`ps aux | grep <tag>` → none, `ls /tmp | grep <tag>` → none).

### 3.4 The no-idle law (elevation-specific addendum)

Same three rules as `AUDIT_CHARTER.md` §"No-idle laws," plus one addition specific to a mutating
campaign: **a cycle that is blocked on a native decision (§3.2) may not substitute unattended
"exploration" work that touches production-adjacent state as a way to stay busy.** If the only
eligible work left requires a native ruling, the correct cycle output is
`CYCLE <n>: IDLE-OK blocked on native decision <item#> -> next: native review`, with zero git
writes to any file under `platform/python-sidecar/ga_writers/`, `services/`, or `pipeline/` (the
`PIPELINE_PATTERN` paths, Domain E §1) — because any such touch triggers an automatic pipeline
image rebuild (Domain E §1/§3) that the campaign has no work ready to justify.

### 3.5 The foreground-subagent law

Carried forward **verbatim, unchanged** from `AUDIT_CHARTER.md`'s own post-incident-B amendment
(confirmed defect B in the task brief matches this exactly): every `Agent` call sets
`run_in_background: false`; a wave's parallel calls go in one message; never end a turn with
"waiting for..."; commit early, before dispatching the next wave; a cycle is complete only if it
pushed a commit and rewrote the state file with its own cycle number.

### 3.6 The honest-stop rule

An honest stop beats invented activity — this is CLAUDE.md §N.8's Earned-Signal Principle applied
to the cycle's own exit line. A cycle prints `CYCLE <n>: IDLE-OK <exact reason> -> next: <what
unblocks>` with **zero** git writes rather than manufacturing a cosmetic commit, a scratch note, or
a re-run of an already-answered query to make the progress detector (§2.1) register activity. Per
§2.1's own residual-risk note: gaming the detector with a no-op commit is possible but is exactly
the dishonesty this rule forbids — the detector is a backstop against accidental false positives,
not a target to be satisfied.

---

## 4. GAP REGISTER

| # | Gap | Severity | Owner | Fix |
|---|---|---|---|---|
| 1 | `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1`/`unset CLAUDE_CODE_CHILD_SESSION` exist only as prose in one audit prompt file; not set by any launcher/settings/CI for a nested session spawned mid-turn (Domain J §2, confirmed unchanged this session — same grep pattern, not re-run, cited). | DEGRADES (mitigated for the top-level supervisor-launched session, per `audit_supervisor.sh` line 8; open for any manually-launched nested top-level session) | Whoever authors `elevation_supervisor.sh` | Keep §1.5's rule: all parallelism goes through in-process `Agent` calls (inherits env automatically), never a manually-launched second top-level `claude` process. Document this as a hard rule in the elevation charter, not just a script comment. |
| 2 | No `.claude/settings.json` with a real `permissions.allow`/`deny` list exists anywhere in this repo for either worktree checked (audit worktree: `dangerouslySkipPermissions: true` only, Domain J §3; readiness worktree: no settings file at all, confirmed live this session). | **BLOCKS-CAMPAIGN** — this is the one item Domain J itself ranks as load-bearing for "many parallel unattended/semi-attended packet sessions." | Repo maintainer / whoever owns `.claude/settings.json` conventions | Author and commit the file proposed in §1.5 (or a reviewed variant); wire the supervisor to stop passing `--dangerously-skip-permissions` once it exists (§2.3). |
| 3 | Cloud SQL PITR is disabled on the production instance; no restore drill has ever been run for `kala_*` tables specifically (Domain J §5, `G1_E_DURABILITY_DR_RUNBOOK_v1_0.md`'s own frontmatter, both cited not re-verified this session — infra state, not something a read-only session can check further). | **BLOCKS-CAMPAIGN for the canonical-chart-mutation path specifically.** A campaign that will mutate `kala_*` production data for real (not just disposable-PG15 proofs) has, today, exactly one proven recovery path if a bad build corrupts canonical-chart rows: re-run the writer (delete-then-insert rollback, CLAUDE.md §N.3) — which does NOT cover the already-documented CASCADE data-loss class (`ka_kalasutra`/`ka_sangam` losing 335,403/14,868 rows to an upstream `bo_laksana` rebuild's `ON DELETE CASCADE`, Domain C §"2a" E-3). If a *different*, not-yet-seen corruption mode occurs during elevation and the rebuild-is-rollback doctrine doesn't cover it either, there is no tested fallback. | Native (infra authorization + budget decision) | Either (a) enable PITR + run one executed restore drill against `kala_*` tables before the campaign's first canonical-chart-mutating cycle, or (b) an explicit native ruling that orchestrator-rebuild is the sole intended recovery mechanism for this tier, with the CASCADE hazard (Gap #4) closed first so that doctrine is actually sound. |
| 4 | `kala_activation`(`ka_kalasutra`)/`kala_convergence`(`ka_sangam`) and 3 sibling tables carry `ON DELETE CASCADE` from `signal_id → bodha_msr_signals`, so an *upstream* L2 `bo_laksana` rebuild silently deletes L3 rows the L3 writer's own re-run does not repair unless it is *also* re-run (Domain C §"2a" E-3, `DATA_LOSS_DIAGNOSIS.md`, independently spot-verified by the audit's cycle-6 conductor — FK type `c` confirmed live). Already destroyed 335,403+14,868 rows on the canonical chart once. | **BLOCKS-CAMPAIGN** for any packet whose work could trigger or coincide with an L2 rebuild — decision-list item 4 in the audit's own ordered list. | Native (architecture decision — this is not L3's unilateral call since the cascade crosses layer boundaries) | Native ruling per §3.2; likely fix is either an explicit rebuild-order sequencing rule (rebuild L3 immediately after any L2 rebuild that touches `bodha_msr_signals`, never let them drift) or changing the FK action away from CASCADE — either is an architecture decision, not a cycle-level fix. |
| 5 | `data_plane_builder` lacks `SELECT` on `bg_transit_moorti`, `phala_rectification`, `bg_synthetic_cohort`, `bg_synthetic_cohort_md` (Domain C E-1, `KALA_PRIVILEGE_MATRIX_v1_0.md` line 55-56, `has_table_privilege(...)` → `f\|f`, confirmed live). | BLOCKS-CAMPAIGN for exactly 3 assets (`ka_moorti_nirnaya` hard fail, `ka_kshetra` stage3 hard fail + stage6 poisoned-transaction near-miss). | Native / whoever owns `data_plane_builder`'s grants | `GRANT SELECT ON bg_transit_moorti, phala_rectification, bg_synthetic_cohort, bg_synthetic_cohort_md TO data_plane_builder;` — small, ten-minute fix per the audit's own decision-list item 6, plus add a named `SAVEPOINT` to `ka_kshetra`'s stage6 cohort-fetch (currently `try/except` with no savepoint, so the poisoned transaction corrupts the *next* statement — `KALA_PRIVILEGE_MATRIX_v1_0.md` line 50). |
| 6 | The disposable-Postgres harness (§1.3) has never actually been run end-to-end with real upstream data loaded (Domain C ran schema-less advisory-lock tests only; this session did not execute setup). `npm run migrate`'s exact invocation against a bare local PG15, and any production-only extensions the schema may implicitly require, are unverified. | DEGRADES — the harness's *mechanism* (advisory lock) is proven; the harness as a *full build-proof pipeline* (schema load + data seed + writer dispatch) is not. | First elevation-campaign packet that needs to prove a writer change | Run §1.3 end-to-end once, early, as its own packet, and commit the working script (not just this spec's prose) to `platform/scripts/` or the elevation briefs directory. |
| 7 | No CI check enforces the L3/Pūrṇa migration-number partition (1042-1069 / 1070-1119 / 1120+) — Domain G §4 and Domain E §4 both independently grepped `.github/workflows/*.yml` for "1070"/"1120" and found neither. | DEGRADES — currently held by convention only; the merge queue's non-fast-forward guard provides *some* collision protection once both PRs exist simultaneously, but a same-number collision authored independently on two branches before either merges is not caught until merge time. | Whoever owns CI / migration tooling | Add a CI lint step: on any new file under `platform/migrations/`, assert its numeric prefix falls in the correct range for the branch's declared campaign (or simply that it doesn't collide with any number already present on `origin/main` at merge time — a cheaper, more general check). |
| 8 | Six lease rows on `origin/campaign-coordination` from 2026-09-19 still literally read `status: ACTIVE` despite being hours-to-days expired (Domain G §2, confirmed live by the audit; not re-fetched this session — would require a live `git show origin/campaign-coordination:...` call, judged out of this lane's remaining budget since Domain G already did the definitive live check same-week). | DEGRADES — a real misread risk (any tool/session that greps for the literal string `ACTIVE` rather than parsing+comparing the expiry timestamp could wrongly conclude a lease is held), but Domain G confirmed no lease is *actually* currently held by either campaign as of last fetch. | Whoever maintains `CAMPAIGN_COORDINATION.md` | Either clean up the stale rows' status field to `EXPIRED`/`RELEASED` retroactively, or (more robust) have the lease-reading tooling this campaign builds always compute "most recent row by position, parse expiry, compare wall-clock IST" — never string-match `status` — as this spec's §1.8 already mandates. |
| 9 | The `L3-REQ`/`PA-REQ` interlock (Pūrṇa↔L3 cross-campaign priority signal) has no CI enforcement — it is a manually-edited LOG entry in the same coordination file as the lease table (Domain G §4). | NICE-TO-HAVE — a process convention, not a safety gate; the audit found no violation of it in practice. | Whoever owns cross-campaign process | Not urgent for campaign start; a future CI lint could grep PR diffs touching `L3_kala/**` for an accompanying `L3-REQ-nn` LOG entry, but this is lower priority than gaps 1-8. |
| 10 | No genuine write-capable DB identity/script (`dbenv_write.sh`) exists distinct from the two read-only helpers — §1.2's "third identity" is a proposal, not a built artifact. | **BLOCKS-CAMPAIGN** for any real canonical-chart mutation (though most early-campaign work should route through the disposable harness instead, per §3.1, making this less urgent than gaps 2-5). | Whoever builds the elevation supervisor | Build `dbenv_write.sh` per §1.2's spec before the first canonical-chart-mutating packet is authorized; until then, every mutation goes through the disposable-PG15 harness (§1.3) only. |
| 11 | PR #2695 (dispatcher hardcoded stale writer-digest path; wrong default ayanamsha in `call_dasha_eligibility`) remains unmerged, blocked on a Pūrṇa-owned baseline (`KALA_CAMPAIGN_RUNBOOK_v1_0.md` §4, Domain E context; not independently re-checked this session — `gh pr view 2695` would confirm current state but was judged lower priority than the DB-side gaps for this lane's budget). | **BLOCKS-CAMPAIGN** for any dispatch through `dispatch_frozen_rebuild.py` — dispatching unpatched would commit a provenance receipt asserting a code identity that never ran (§N.8 unearned-signal violation, decision-list item 5). | Native (land the PR or grant a scoped override) | Do not dispatch through `dispatch_frozen_rebuild.py` until #2695 lands or an explicit, scoped native override is granted. |

**Severity legend applied consistently:** BLOCKS-CAMPAIGN = the campaign cannot safely begin its
mutating (build/migrate/mint) work until this closes, for the specific scope named; DEGRADES = the
campaign can proceed but with a known, named risk or inefficiency; NICE-TO-HAVE = would improve the
environment but is not on the critical path to starting safely.

**What this register deliberately does not repeat:** the strategic/content-side native decision
list (F2 definition inheritance, the missing acceptance-receipt design, the `ka_gochara` family
knot, etc.) already lives, fully ordered, in `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` §3 — this
register is scoped to the *environment/operational* gaps this lane was asked to specify, and cites
that list by item number wherever an environment gap and a content-decision gap are the same
underlying issue (e.g. Gap #4 above = decision-list item 4; Gap #11 = decision-list item 5).

---

## 5. Summary verdict for this lane

**Environment readiness for the L3 Kāla elevation campaign, as specified above: NOT READY to begin
canonical-chart-mutating work; READY to begin disposable-harness and non-canonical-chart work once
Gaps #2, #6, and #10 are closed** (settings-file allow/deny scope; the disposable harness proven
end-to-end once; the write-identity script built). Gaps #3, #4, #5, #11 are pre-existing content/
infra blockers this lane surfaces but cannot itself close (native decisions or infra
authorizations). Gaps #1, #7, #8, #9 are real but do not block a correctly-disciplined campaign from
starting, provided the discipline in §1.5/§1.8/§3 (never launch a nested top-level session; always
parse lease expiry, never string-match; the honest-stop rule) is followed by every cycle from the
first one.

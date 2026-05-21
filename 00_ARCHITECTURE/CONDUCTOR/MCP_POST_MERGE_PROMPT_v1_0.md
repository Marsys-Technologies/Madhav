# MCP — Claude Code POST-MERGE Operator Prompt v1.0

Paste this into a **fresh Claude Code session in Antigravity IDE**, pointed at the **main** Madhav worktree (`/Users/Dev/Vibe-Coding/Apps/Madhav`), after the MCP workstream conductor run has completed and PR #127 has been squash-merged on GitHub.

Launch Claude Code with:

```
cd /Users/Dev/Vibe-Coding/Apps/Madhav
claude --dangerously-skip-permissions
```

The prompt does the following automatable work in one autonomous run:

1. Pull main, capture squash-merge SHA, verify expected files landed
2. Apply governance close-out (CLAUDE.md §E, brief status flips, CURRENT_STATE)
3. Commit and push governance close-out
4. Apply migrations 070 + 071 (conditional on `MARSYS_PROD_DB_URL` env var)
5. Deploy `amjis-mcp` Cloud Run service (conditional on `gcloud` auth)
6. Run post-deploy smoke check (`curl /healthz`)
7. Worktree + remote-branch cleanup
8. Print operator-still-todo list (browser-only: mint key + register in Claude Chat)

The prompt halts on any failure and reports cleanly.

---

## What to paste

```
You are the post-merge operator for the MARSYS-JIS MCP workstream. The
9-session Conductor run completed; PR #127 was squash-merged on GitHub.
Your job is to apply the governance close-out, ship the deployable
artifacts, and report any browser-only steps the native must do.

Worktree: /Users/Dev/Vibe-Coding/Apps/Madhav (the main worktree)
Mode: --dangerously-skip-permissions (skip every permission prompt)
Halt policy: STOP on first non-recoverable error; report what worked and
what didn't.

Read CLAUDE.md §C briefly for orientation, then execute the steps below
in order. Echo each step header before running it. Echo a clear
PASS / FAIL line after each step.

────────────────────────────────────────────────────────────────────────
STEP 1 — Pull main, verify merge landed
────────────────────────────────────────────────────────────────────────

cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin main
git checkout main
git pull origin main --ff-only

Verify:
  test -f 00_ARCHITECTURE/MCP_WORKSTREAM_COMPLETE.md
  test -f 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
  test -d platform-mcp
  test -f platform/supabase/migrations/070_mcp_api_keys.sql
  test -f platform/supabase/migrations/071_mcp_predictions.sql

If any test fails, HALT and report that the squash-merge didn't bring the
expected files into main.

────────────────────────────────────────────────────────────────────────
STEP 2 — Capture the squash-merge SHA
────────────────────────────────────────────────────────────────────────

Find the squash-merge commit by searching recent main commits for
"PR #127" or "MCP" in the message:

  git log --oneline -20 main | head

Capture the actual squash-merge SHA. Echo it. Use this SHA (call it
MERGE_SHA below) in subsequent steps.

────────────────────────────────────────────────────────────────────────
STEP 3 — Apply CLAUDE.md §E update (governance close-out)
────────────────────────────────────────────────────────────────────────

Read 00_ARCHITECTURE/MCP_WORKSTREAM_COMPLETE.md. Locate the section
titled "CLAUDE.md §E Update (post-merge)" — it contains the exact row
to insert.

Edit CLAUDE.md:

(a) Find any sentence in §E header text matching "Ten workstreams" or
"Nine workstreams" or similar count. Update to reflect +1 workstream
(MCP). If the most recent count says "Ten", update to "Eleven". If the
most recent count is unclear, count the existing workstream bullets in
§E and set the new count = existing + 1.

(b) Insert the MCP workstream row after the Conductor entry (or at the
end of §E if Conductor is the last entry today). Use the row from
MCP_WORKSTREAM_COMPLETE.md, but substitute:
  - "PR #PENDING" → "PR #127"
  - "(merge commit PENDING)" → "(merge commit <MERGE_SHA>)" using the
    SHA captured in Step 2

Verify the edit went in cleanly (grep for "MCP — MARSYS-JIS Model Context
Protocol Server" in CLAUDE.md). If absent, HALT.

────────────────────────────────────────────────────────────────────────
STEP 4 — Flip brief statuses DRAFT → CURRENT
────────────────────────────────────────────────────────────────────────

In each of these files, update the frontmatter `status:` field:

  00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
    status: DRAFT → status: CURRENT
    sealed_on: TBD → sealed_on: <today's ISO date>
    sealed_by: TBD → sealed_by: Conductor run 2026-05-21 (9-for-9, PR #127)

  00_ARCHITECTURE/BRIEFS/MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0.md
    Keep status: DRAFT (this sibling brief is NOT being sealed yet — it's
    a separate future Conductor run). Just confirm it's still DRAFT and
    move on.

────────────────────────────────────────────────────────────────────────
STEP 5 — Update CURRENT_STATE_v1_0.md
────────────────────────────────────────────────────────────────────────

Read 00_ARCHITECTURE/CURRENT_STATE_v1_0.md.

In the concurrent-workstreams section (likely §2 or §3), add or update
an MCP entry:

  - MCP workstream: COMPLETE (2026-05-21). PR #127 merged. amjis-mcp
    Cloud Run service deployable via platform-mcp/cloudbuild.yaml.
    Migrations 070 + 071 pending operator apply.

Bump CURRENT_STATE version per the file's versioning convention.

────────────────────────────────────────────────────────────────────────
STEP 6 — Commit governance close-out
────────────────────────────────────────────────────────────────────────

cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add CLAUDE.md \
        00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md \
        00_ARCHITECTURE/CURRENT_STATE_v1_0.md

git status  # verify ONLY those three files are staged

git commit -m "chore(governance): MCP workstream close-out

- CLAUDE.md §E: add MCP row, bump workstream count
- MCP_BRIEF_v1_0.md: DRAFT → CURRENT, sealed by Conductor run
- CURRENT_STATE_v1_0.md: mark MCP COMPLETE, version bump

PR #127 (merge commit <MERGE_SHA>). All 9 Conductor sessions PASS.
19 tools shipped. 80 vitest tests. 0 class-1 red-team findings.
Sibling MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0 remains DRAFT (separate
future workstream)."

git push origin main

────────────────────────────────────────────────────────────────────────
STEP 7 — Apply database migrations (CONDITIONAL)
────────────────────────────────────────────────────────────────────────

If the env var MARSYS_PROD_DB_URL is set, apply both migrations:

  psql "$MARSYS_PROD_DB_URL" \
    -f platform/supabase/migrations/070_mcp_api_keys.sql

  psql "$MARSYS_PROD_DB_URL" \
    -f platform/supabase/migrations/071_mcp_predictions.sql

Verify each by running:
  psql "$MARSYS_PROD_DB_URL" -c "\d mcp_api_keys"
  psql "$MARSYS_PROD_DB_URL" -c "\d mcp_predictions"
  psql "$MARSYS_PROD_DB_URL" -c "\d mcp_disagreements"

If MARSYS_PROD_DB_URL is NOT set: SKIP this step and add to the
"operator-still-todo" list at the end:
  "Apply migration 070 + 071 to prod Supabase (set MARSYS_PROD_DB_URL
   and re-run this prompt, or run psql by hand)"

────────────────────────────────────────────────────────────────────────
STEP 8 — Deploy amjis-mcp Cloud Run service (CONDITIONAL)
────────────────────────────────────────────────────────────────────────

If `gcloud auth list --filter="status:ACTIVE" --format="value(account)"`
returns a non-empty result AND the active project is "marsys-jis" (or
whatever PROJECT_ID this repo uses — check platform/cloudbuild.yaml or
.gcloudconfig for the canonical value):

  # Look up the amjis-web URL for the PLATFORM_URL substitution
  AMJIS_WEB_URL=$(gcloud run services describe amjis-web \
    --region asia-south1 \
    --format='value(status.url)')

  cd platform-mcp
  gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions=_PLATFORM_URL="$AMJIS_WEB_URL"

  # Verify the deploy
  AMJIS_MCP_URL=$(gcloud run services describe amjis-mcp \
    --region asia-south1 \
    --format='value(status.url)')

  echo "amjis-mcp deployed at: $AMJIS_MCP_URL"
  cd ..

If gcloud is not authenticated or the project is wrong: SKIP and add to
"operator-still-todo":
  "Deploy amjis-mcp: authenticate gcloud, then run
   `cd platform-mcp && gcloud builds submit --config=cloudbuild.yaml
   --substitutions=_PLATFORM_URL=<amjis-web url>`"

────────────────────────────────────────────────────────────────────────
STEP 9 — Smoke check the deployed MCP server (CONDITIONAL)
────────────────────────────────────────────────────────────────────────

If Step 8 deployed amjis-mcp, run a health check:

  curl -fsS "$AMJIS_MCP_URL/healthz" || echo "FAIL: /healthz did not respond"

If /healthz doesn't exist as an endpoint (check platform-mcp/src/server.ts
for the actual health route), try alternatives:
  curl -fsS "$AMJIS_MCP_URL/"
  curl -fsS "$AMJIS_MCP_URL/mcp"

Note the result; non-fatal — failure here just means the smoke is
inconclusive, not that the deploy failed.

────────────────────────────────────────────────────────────────────────
STEP 10 — Cleanup (worktree + remote branch)
────────────────────────────────────────────────────────────────────────

# Remove the prunable MadhavMCP worktree
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git worktree list | grep -q MadhavMCP && \
  git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavMCP --force || \
  echo "MadhavMCP worktree not present, skip"

# Delete the merged branch on remote
git push origin --delete feature/mcp-server 2>&1 | head -5 || \
  echo "Remote branch already deleted, skip"

# Delete the merged branch locally
git branch -D feature/mcp-server 2>/dev/null || \
  echo "Local branch already deleted, skip"

────────────────────────────────────────────────────────────────────────
STEP 11 — Final report
────────────────────────────────────────────────────────────────────────

Echo a clear final report block:

═══════════════════════════════════════════════════════════════════════
 MCP POST-MERGE OPERATOR — DONE
═══════════════════════════════════════════════════════════════════════

 What happened (in this run):
   - [PASS|FAIL] Step 1  Pull main + verify merge files
   - [PASS|FAIL] Step 2  Capture squash-merge SHA (<MERGE_SHA>)
   - [PASS|FAIL] Step 3  CLAUDE.md §E update
   - [PASS|FAIL] Step 4  MCP_BRIEF status DRAFT → CURRENT
   - [PASS|FAIL] Step 5  CURRENT_STATE update
   - [PASS|FAIL] Step 6  Governance close-out commit pushed to main
   - [PASS|SKIP|FAIL] Step 7  Migrations 070 + 071 applied
   - [PASS|SKIP|FAIL] Step 8  amjis-mcp Cloud Run deployed
   - [PASS|SKIP|FAIL] Step 9  Post-deploy smoke (/healthz)
   - [PASS|SKIP|FAIL] Step 10 Worktree + branch cleanup

 Governance close-out commit on main: <commit_sha>

 What I (Claude Code) could NOT automate — your browser steps:
   1. Mint an MCP API key at:
        <amjis-web-url>/admin/mcp/keys
      Click "Create new key", label it (e.g. "claude-chat-personal"),
      copy the full key. It is shown ONLY ONCE.

   2. Register amjis-mcp as a Claude Chat custom integration:
        https://claude.ai/settings/connectors
      Click "Add custom integration".
      URL:           <amjis-mcp-url>
      Authorization: Bearer <the key from step 1>
      Smoke-test:    ask_madhav("What is my Atmakaraka?")
      Verify the answer includes citations and a trace_id field.

   3. (Optional) Register the same MCP in Cowork as a remote MCP:
      Cowork → Settings → Connectors → Add remote MCP, same URL + Bearer.

 What still needs doing if Steps 7/8 were SKIPPED:
   <list of skipped steps with the commands to run by hand>

 Workstream status: COMPLETE.
═══════════════════════════════════════════════════════════════════════

Then terminate. Do not start any other work.
```

---

## What if something fails mid-run

If any step fails, the prompt halts and reports the failure clearly in the
final block. You either:

- **Fix the cause** (e.g., authenticate gcloud, set MARSYS_PROD_DB_URL,
  resolve a CLAUDE.md merge conflict) and re-paste this prompt — the
  prompt is idempotent for the governance close-out (git will skip
  already-applied edits / commits), and the conditional steps (7/8/9/10)
  re-check preconditions safely.

- **Skip that step manually** — do it later by hand and update the
  "operator-still-todo" list yourself.

## On safety

- Steps 1–6 are reversible via `git revert`.
- Step 7 (migrations) is the most consequential — only runs if you've
  explicitly set `MARSYS_PROD_DB_URL`, so opt-in.
- Step 8 (Cloud Run deploy) only runs if gcloud is authenticated to the
  right project — opt-in.
- Step 10 (cleanup) deletes a merged branch and a prunable worktree
  only; both are recoverable from `git reflog` / re-create if needed.

## On the two browser steps

These cannot be automated in Claude Code (they're in claude.ai's web UI
and your deployed admin UI). The prompt's final report block surfaces
them with the exact URLs and labels so they're a 2-minute manual
follow-up.

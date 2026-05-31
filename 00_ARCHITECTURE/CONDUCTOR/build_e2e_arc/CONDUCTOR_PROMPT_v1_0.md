# Conductor prompt — build_e2e_arc

This is what the OPERATOR pastes into a fresh Antigravity Claude Code
window — the first of 5 prompts total.

The Conductor session:
1. Runs pre-flight smoke against prod DB (applies migrations 140-156, triggers a build, observes)
2. Writes pre-flight findings to a file the stream agents will read
3. Creates the 4 worktrees + branches
4. Seeds CLAIM_LEDGER if not already seeded
5. Prints the 4 kickoff prompts to console for you to copy-paste into 4 more Antigravity windows
6. Exits

Then YOU open 4 more Antigravity windows, one per stream, paste the
4 printed kickoffs, walk away.

---

```
You are Claude Code running in Google Antigravity IDE.

ROLE: Conductor for arc build_e2e_arc
PROJECT: MARSYS-JIS (/Users/Dev/Vibe-Coding/Apps/Madhav)
MODEL: Gemini Pro or DeepSeek. Anthropic banned.

REQUIRED READS at session open (in order):
  1. /Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDE.md (project standing rules)
  2. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/STREAM_COORDINATION_v1_0.md
  3. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/session_queue.yaml
  4. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/VISUAL_CONTRACT_v2.md
  5. All 4 briefs under .../briefs/STREAM_{A,B,C,D}_*.md
  6. All 4 kickoffs under .../kickoffs/KICKOFF_STREAM_{A,B,C,D}.md

YOUR TASK (sequence, in order):

═══════════════════════════════════════════════════════════════════════════════
§1 — PRE-FLIGHT SMOKE (operator-authorized, 15 min)
═══════════════════════════════════════════════════════════════════════════════

The native authorized pre-flight smoke against prod 2026-05-31. Goal:
empirical evidence of what's actually broken in the current build chain
before the 4 streams scope their work.

1.1  Confirm prod DB connection:
       cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
       if ! nc -z 127.0.0.1 5433 2>/dev/null; then
         bash scripts/start_db_proxy.sh &
         sleep 5
       fi
       psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM charts WHERE chart_id='362f9f17-95a5-490b-a5a7-027d3e0efda0';"
       (must return 1)

1.2  Apply migrations 140-156 to prod DB (additive, idempotent):
       mkdir -p /tmp/preflight
       for i in $(seq 140 156); do
         f=$(ls platform/migrations/${i}_*.sql 2>/dev/null | head -1)
         if [ -n "$f" ]; then
           echo "==> applying $f"
           psql "$DATABASE_URL" -f "$f" 2>&1 | tee -a /tmp/preflight/migrations.log
         fi
       done

1.3  Check if existing /api/build/start works:
       SESSION_COOKIE=$(npx tsx scripts/mint_session_cookie.ts \
         --uid native-preflight \
         --chart-id 362f9f17-95a5-490b-a5a7-027d3e0efda0 2>/dev/null || echo "")
       BUILD_RESP=$(curl -s -X POST https://<amjis-web-url>/api/build/start \
         -H "Cookie: __session=$SESSION_COOKIE" \
         -H "Content-Type: application/json" \
         -d '{"chart_id":"362f9f17-95a5-490b-a5a7-027d3e0efda0"}')
       echo "$BUILD_RESP" | tee /tmp/preflight/build_start_response.json
       BUILD_ID=$(echo "$BUILD_RESP" | jq -r '.build_id // empty')

1.4  If a build_id came back, watch its state for 5 min:
       for i in $(seq 1 10); do
         sleep 30
         psql "$DATABASE_URL" -c "
           SELECT status, COUNT(*) FROM build_steps
            WHERE build_id='$BUILD_ID' GROUP BY 1 ORDER BY 1;
         " | tee -a /tmp/preflight/build_progress.log
       done

1.5  Capture cockpit URL render check:
       curl -s -I "https://<amjis-web-url>/clients/362f9f17.../build" \
         -H "Cookie: __session=$SESSION_COOKIE" \
         > /tmp/preflight/cockpit_response_headers.txt

1.6  Write findings to /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/PREFLIGHT_FINDINGS.md:

```markdown
---
artifact: PREFLIGHT_FINDINGS.md
generated_at: <ISO>
generated_by: conductor (pre-flight phase)
---

# Pre-flight findings — build_e2e_arc

## DB state
- Native chart present: YES/NO
- Migrations 140-156: <N> applied, <N> skipped, <N> failed (list)

## /api/build/start
- Endpoint reachable: YES/NO
- Returned build_id: <id or "none">
- Returned 409 (already running): YES/NO
- Returned error: <details>

## Build progress observation
- Build moved past status='queued': YES/NO/N/A
- Build steps completed in 5 min: <count>
- Build stuck at status='running' with no progress: YES/NO

## Cockpit render
- HTTP status: <code>
- Renders cockpit shell: YES/NO/unknown (need browser)

## Scope adjustments for streams
- Stream A scope: <unchanged|expand|reduce + reason>
- Stream B scope: <unchanged|expand|reduce + reason>
- Stream C scope: <unchanged|expand|reduce + reason>
- Stream D scope: <unchanged|expand|reduce + reason>
```

If any prod operation fails for auth reasons, document and proceed — the
streams can still run against the existing state.

═══════════════════════════════════════════════════════════════════════════════
§2 — WORKTREE + BRANCH SETUP
═══════════════════════════════════════════════════════════════════════════════

bash /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/setup_streams.sh

Verify all 4 worktrees exist + on correct branches:
  git worktree list

═══════════════════════════════════════════════════════════════════════════════
§3 — CLAIM_LEDGER SEED
═══════════════════════════════════════════════════════════════════════════════

If CLAIM_LEDGER.yaml's released_claims is empty (fresh start), proceed.
If it has prior entries (re-kick scenario), preserve them and continue.

═══════════════════════════════════════════════════════════════════════════════
§4 — PRINT THE 4 KICKOFFS
═══════════════════════════════════════════════════════════════════════════════

For each of the 4 kickoff files under .../kickoffs/, cat the file to
console with a separator banner so the operator can easily copy each block:

  echo "═══════════════════════════════════════════════════════════"
  echo "KICKOFF STREAM A — paste into Antigravity window 1"
  echo "═══════════════════════════════════════════════════════════"
  cat /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/kickoffs/KICKOFF_STREAM_A.md
  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "KICKOFF STREAM B — paste into Antigravity window 2"
  echo "═══════════════════════════════════════════════════════════"
  cat .../KICKOFF_STREAM_B.md
  ... (and C, D)

═══════════════════════════════════════════════════════════════════════════════
§5 — STOP
═══════════════════════════════════════════════════════════════════════════════

Print:

  CONDUCTOR COMPLETE.
  Pre-flight findings: /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/PREFLIGHT_FINDINGS.md
  Worktrees: 4 ready (see git worktree list above).
  CLAIM_LEDGER: seeded.

  OPERATOR NEXT STEPS:
    1. Open 4 fresh Antigravity Claude Code windows, one per worktree:
       Window 1: cd /Users/Dev/Vibe-Coding/Apps/MadhavHardeningCI
       Window 2: cd /Users/Dev/Vibe-Coding/Apps/MadhavDataPlumbing
       Window 3: cd /Users/Dev/Vibe-Coding/Apps/MadhavVisualV2
       Window 4: cd /Users/Dev/Vibe-Coding/Apps/MadhavFunnelPolish
    2. Paste the 4 KICKOFF blocks printed above, one per window.
    3. Walk away. Streams run autonomously.
    4. Native chart build trigger remains operator-manual:
         Open /clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/build
         Click Build.

  Exit.

═══════════════════════════════════════════════════════════════════════════════

HARD GATES on the Conductor itself:
  - Do NOT execute any stream's sessions. Conductor's job is setup + handoff only.
  - Do NOT modify code outside CONDUCTOR/build_e2e_arc/ unless pre-flight required a tiny tracker-table bootstrap (allowed, document in PREFLIGHT_FINDINGS).
  - Do NOT push to main. Pre-flight only reads. Stream agents do all the pushing.
  - Do NOT use Anthropic models.

If pre-flight fails fundamentally (DB unreachable, can't auth) or any required
file is missing, STOP and write a one-paragraph blocker. Do not proceed to §2.
```

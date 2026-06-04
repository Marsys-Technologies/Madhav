# Kickoff prompt — PARIKSHA ORCHESTRATOR (P1)

Paste this into a fresh Antigravity Claude Code window. The orchestrator
spawns Drashta + Pramana for a chart's build walk, manages resume state,
and produces the final per-build report.

---

```
You are Claude Code running in Google Antigravity IDE.

ROLE: Pariksha Orchestrator (Sutradhara) for the build_verification arc
PROJECT: MARSYS-JIS (/Users/Dev/Vibe-Coding/Apps/Madhav)
MODEL: Gemini Pro or DeepSeek. Anthropic banned.

OPERATOR INPUTS (the operator fills in before pasting):
  CHART_ID:                   <fill: existing chart_id OR "spawn-new-guest">
  OPERATOR_AUTH_TIER:         observe-only | pr-only | auto-merge-low-risk
                              (controls Vaidya behavior; observe-only = no fixes)
  WALK_SCOPE:                 minimum | extended
                              (minimum = single form variant, default ayanamshas, one cockpit walk)

REQUIRED READS at session open (in order, full files):
  1. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PARIKSHA/PARIKSHA_MASTER_PLAN_v1_0.md
  2. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PARIKSHA/ISSUE_LEDGER_SCHEMA.md
  3. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PARIKSHA/EXPECTED_ROW_COUNTS.yaml
  4. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PARIKSHA/ASSET_REGISTRY.md
  5. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PARIKSHA/RESUME_PROTOCOL.md
  6. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PARIKSHA/REMEDIATION_PROTOCOL.md
  7. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PARIKSHA/briefs/DRASHTA_v1_0.md
  8. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PARIKSHA/briefs/PRAMANA_DRASHTA_v1_0.md

YOUR TASK (sequence, in order):

═══════════════════════════════════════════════════════════════════════════
§1 — Bootstrap the arc directory
═══════════════════════════════════════════════════════════════════════════

cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Resolve CHART_ID
if [ "$CHART_ID" = "spawn-new-guest" ]; then
  # Spawn a synthetic guest with deterministic seed data so the walk is repeatable
  TIMESTAMP=$(date +%s)
  CHART_ID="pariksha-test-$TIMESTAMP"
  # The actual chart will be created when Drashta submits the form
fi

mkdir -p 00_ARCHITECTURE/PARIKSHA/builds/$CHART_ID/screenshots
cat > 00_ARCHITECTURE/PARIKSHA/builds/$CHART_ID/manifest.yaml <<EOF
schema: v1
chart_id: $CHART_ID
operator_auth_tier: $OPERATOR_AUTH_TIER
walk_scope: $WALK_SCOPE
arc_started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
agents_authorized: [drashta, pramana_drashta]
guest_seed:
  full_name: "Test Guest"
  birth_date: "1990-06-15"
  birth_time: "14:30"
  birth_place: "Mumbai, Maharashtra, India"
  ayanamshas: [lahiri, true_chitra, kp, raman, surya_siddhanta]
EOF

# Initialize issue ledger
cat > 00_ARCHITECTURE/PARIKSHA/builds/$CHART_ID/issues.yaml <<EOF
schema: v1
chart_id: $CHART_ID
build_id: null
arc_started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
last_updated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
last_updated_by: orchestrator
root_causes: []
issues: []
EOF

# Initialize resume state
cat > 00_ARCHITECTURE/PARIKSHA/builds/$CHART_ID/resume_state.yaml <<EOF
schema: v1
chart_id: $CHART_ID
build_id: null
last_checkpoint_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
last_checkpoint_by: orchestrator
checkpoints: {}
current_stage: 0
current_checkpoint: arc_initialized
next_expected_action: drashta_cp1_form_loaded
recovery_context: {}
EOF

echo "Arc directory ready: 00_ARCHITECTURE/PARIKSHA/builds/$CHART_ID/"

═══════════════════════════════════════════════════════════════════════════
§2 — Confirm STOP file absent
═══════════════════════════════════════════════════════════════════════════

if [ -f 00_ARCHITECTURE/PARIKSHA/STOP ]; then
  echo "STOP file present. Halt."
  exit 0
fi

═══════════════════════════════════════════════════════════════════════════
§3 — Spawn Drashta (front-end walker)
═══════════════════════════════════════════════════════════════════════════

You will now act as Drashta per DRASHTA_v1_0.md. Walk the 13 checkpoints.
Use the Claude in Chrome MCP for browser actions. Authenticate by minting
a session cookie via:
  cd platform && npx tsx scripts/mint_session_cookie.ts \
    --uid pariksha-runner \
    --chart-id $CHART_ID
Then set the __session cookie in Chrome before navigating.

Follow DRASHTA_v1_0.md exactly. Write checkpoints + issues as you go.
If a workflow_blocking issue surfaces AND OPERATOR_AUTH_TIER is not
observe-only, write vaidya_paused{} block and exit. Do NOT spawn Vaidya
in this P1 brief — Vaidya is P4. For P1, observe-only mode: emit issues,
keep walking.

If the cockpit shows "Build Constellation" or any legacy non-v2 element,
log it as workflow_blocking and STILL CONTINUE the walk (so we collect
all issues in one pass).

═══════════════════════════════════════════════════════════════════════════
§4 — Spawn Pramana (post-build internal-consistency battery)
═══════════════════════════════════════════════════════════════════════════

Only after Drashta's CP-11 (build_complete_event) succeeded, you now act
as Pramana-Drashta per PRAMANA_DRASHTA_v1_0.md.

1. Start the Cloud SQL proxy:
   bash platform/scripts/start_db_proxy.sh &
   sleep 5

2. For each asset in EXPECTED_ROW_COUNTS.yaml × each selected ayanamsha:
   - Run row-count check via psql
   - Compare against expected ± tolerance
   - Emit issues for mismatches

3. Run structural invariants per asset per ASSET_REGISTRY.md

4. Run cross-asset FK checks

5. Run layer-completion gate check

6. Write the pramana{} summary block to resume_state.yaml

═══════════════════════════════════════════════════════════════════════════
§5 — Write the final REPORT.md
═══════════════════════════════════════════════════════════════════════════

After Drashta CP-13 (or after Pramana if Drashta exited early), write
00_ARCHITECTURE/PARIKSHA/builds/$CHART_ID/REPORT.md with:

# Pariksha Report — Chart {chart_id}

## Verdict
**{PASS | FAIL — N workflow_blocking + M data_integrity issues}**

## Execution summary
- Arc started: {ISO}
- Arc ended:   {ISO}
- Wall-clock:  {duration}
- Walk scope:  {scope}
- Auth tier:   {tier}
- Drashta walked to checkpoint: {CP-N}
- Pramana ran: {yes/no, checks, pass}

## Top issues (by severity, then discovery time)
- I-NNN: {title} ({severity}) — {one-liner}
  Surface: {surface}; Suspected files: {files}
- ...

## Per-stage breakdown
### Stage 1: Aapti (form → API → DB)
{count and brief issue list}
### Stage 2: Prarambha (build initiation)
...
### Stage 3-5: Pipeline (DB-side verified by Pramana)
{Pramana summary by asset}
### Stage 6: Drishti (live observation)
{cockpit + SSE issues}

## Pramana battery results
{row count check results table; structural results; cross-asset results}

## Recommended next actions
{prioritized list — what the operator should fix first, with file paths}

## Artifacts
- issues.yaml — {path}
- resume_state.yaml — {path}
- Screenshots — {path}

═══════════════════════════════════════════════════════════════════════════
§6 — STOP
═══════════════════════════════════════════════════════════════════════════

Print:

  PARIKSHA ARC COMPLETE.
  Verdict:      {PASS|FAIL}
  Report path:  00_ARCHITECTURE/PARIKSHA/builds/{chart_id}/REPORT.md
  Issues:       {count} total ({N workflow_blocking}, {M data_integrity},
                {K ux_degrading}, {L cosmetic})
  Operator next: {if FAIL: review REPORT.md → triage top issues; if PASS: no action}

  Exit.

═══════════════════════════════════════════════════════════════════════════

HARD GATES on the Orchestrator itself:
  - NO Anthropic models.
  - NO modifications to application code (Vaidya is not P1 scope).
  - NO writes to any DB other than the proxy-connected prod read.
  - NO opening of PRs.
  - If at any point 00_ARCHITECTURE/PARIKSHA/STOP exists, halt within 60s.
  - Resume protocol applies: if resume_state.yaml shows a break, recover
    per RESUME_PROTOCOL.md before continuing.

WHEN DONE: print §6 summary. Exit.
```

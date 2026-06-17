---
artifact: CLAUDECODE_BRIEF_PHASE_4C_9_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-19
session_id: 4C-9
session_name: 4C-9 — Polish, telemetry, red-team, Wave 1 close
executor: Claude Code sub-agent (Conductor) — requires_human_approval before this entry runs
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
predecessor: 4C-8
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §6 Phase 4C.9 + §8 AC.4C.9
human_approval_prompt: |
  4C-8 has closed. Phase 4C MVP is feature-complete: panchang_engine v1.0.0-S3,
  /panchang UI, Personalise overlay, Muhurat Finder (6 events), iCal export,
  Ask-Madhav. Approve to execute 4C-9 (Wave 1 close): polish pass, telemetry
  panels, red-team, CURRENT_STATE finalization, Wave 1 close artifact + PR.
  Or SKIP / ABANDON.
---

# CLAUDECODE_BRIEF — Phase 4C-9
## Wave 1 close: polish, telemetry, red-team, PR preparation

The closing session of Phase 4C and Wave 1. Polishes any rough edges from prior sessions, adds Observatory panels for Panchang telemetry, runs the IS.8(b) red-team pass required for Phase 4 close, finalizes governance state, and prepares the split-PR strategy (Conductor cherry-pick + Phase 4C close).

**Human approval gate:** This session does NOT run autonomously. The Conductor halts before spawning a sub-agent against this brief. Native must reply `APPROVE 4C-9` to authorize execution.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f 00_ARCHITECTURE/PHASE_4C_8_CLOSE_v1_0.md  # 4C-8 close artifact present
# Verify all prior sub-phase closes
for p in 4C_1 4C_4 4C_6 4C_7 4C_8; do
    test -f 00_ARCHITECTURE/PHASE_${p}_CLOSE_v1_0.md || echo "MISSING: 4C.${p}"
done
# Engine tests pass
cd platform/python-sidecar/panchang_engine && pytest -q && cd /Users/Dev/Vibe-Coding/Apps/Panchang
# UI tests pass
cd platform && npm test 2>&1 | tail -30
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. Master plan §6 Phase 4C.9 + §8 AC.4C.9 + §10 risks
3. `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` §H (IS.8(b) red-team protocol)
4. All Phase 4C close artifacts: PHASE_4C_1, _4, _6, _7, _8 (read for cross-phase coherence)
5. `00_ARCHITECTURE/CONDUCTOR/WAVE_2_MIGRATION_NOTE.md` (the cherry-pick procedure)
6. `00_ARCHITECTURE/CONDUCTOR/CLAUDE_MD_AMENDMENT_PROPOSAL.md` (deferred amendment from CONDUCTOR-S0)

## §3 — Scope (12 items)

### Item 1 — Engineering polish pass
Sweep through /panchang components for inconsistencies surfaced during integration:
- Brand token uniformity (gold accents consistent; no hardcoded colors)
- Touch target sizes (40px minimum for primary controls per a11y)
- Loading state polish (skeleton consistent across sessions)
- Error state polish (friendly messages, retry buttons)
- Mobile responsive checks at 375/768/1280

Limit: 2-hour polish budget; don't enter scope creep. Document anything beyond budget in `00_ARCHITECTURE/PHASE_4C_FOLLOWUPS_v1_0.md` for v2.

**AC.4C9.1:** Polish documented; deferred items captured.

### Item 2 — Observatory panels for Panchang
Per master plan §5.7: add two panels to the existing Observatory dashboard:
- Panchang sidecar latency (p50/p95/p99 over 24h)
- Cache hit ratio (n/a until 4C-2 lands; for now show "Cache layer pending Phase 4B")

If Observatory's dashboard component lives in `platform/src/app/observatory/`, add the panels there. If telemetry isn't already capturing sidecar latencies for `/api/compute/panchanga`, instrument it (probably already does via existing trace hooks).

**AC.4C9.2:** Two Observatory panels live; populated with real data from the recent autonomous runs.

### Item 3 — IS.8(b) red-team pass (Phase 4 close mandate)
Per master plan §8 AC.4C.9 + GOVERNANCE_INTEGRITY_PROTOCOL §H: every macro-phase close needs a red-team. Run a 5-probe pass on Phase 4C:

| Probe | Question to attack |
|---|---|
| RT.4C.1 | Layer purity — does any UI component create derivations the engine should own? |
| RT.4C.2 | B.10 discipline — does any displayed value lack provenance back to engine + ephemeris? |
| RT.4C.3 | Personalise overlay correctness — Tara Bala / Chandra Bala for native chart match classical tables? |
| RT.4C.4 | Muhurat scoring acharya validity — top results for 3 sample events pass acharya sniff test? |
| RT.4C.5 | Calendar feed PII surface — verify no chart_id, email, or user identity leaks via feed URL or ICS content |

Each probe gets a finding doc at `00_ARCHITECTURE/RED_TEAM/RT_4C_<N>_FINDING.md`. Verdict: PASS / WARN / FAIL.

**AC.4C9.3:** 5/5 red-team probes have findings; all PASS or WARN-with-mitigation; no FAILs left unaddressed.

### Item 4 — Drift + manifest validation
```bash
python3 platform/scripts/governance/schema_validator.py
python3 platform/scripts/governance/drift_detector.py
python3 platform/scripts/governance/mirror_enforcer.py
python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py
```
All exit 0.

**AC.4C9.4:** All validators clean.

### Item 5 — Apply deferred CLAUDE.md amendment for Conductor
Per CONDUCTOR-S0 Item 9: the Conductor workstream declaration in CLAUDE.md §E (Five → Six workstreams) was deferred until post-cherry-pick-to-main. **BUT:** since this session is Wave 1 close, we can apply it now in anticipation of the cherry-pick PR. Open `CLAUDE.md`, apply the amendment from `00_ARCHITECTURE/CONDUCTOR/CLAUDE_MD_AMENDMENT_PROPOSAL.md`, bump CLAUDE.md version, propagate MP.1 to `.geminirules`.

Note: this lands in `feature/phase-4c-panchang` along with the Phase 4C close. When the cherry-pick PR moves Conductor commits to main, this CLAUDE.md amendment goes with them.

**AC.4C9.5:** CLAUDE.md §E shows Conductor; version bumped; `.geminirules` MP.1 propagated; `mirror_enforcer.py` exits 0.

### Item 6 — Phase 4C close artifact
Author `00_ARCHITECTURE/PHASE_4C_CLOSE_v1_0.md` — comprehensive Phase 4C closeout summary:
- All sub-phase closes (4C.0, 4C.1, 4C.3, 4C.4, 4C.5, 4C.6, 4C.7, 4C.8) with their commit hashes
- Skipped sub-phases (4C-1-S3, 4C-2) with reasons
- Deferred work (4C-2 pending 4B; v2 polish items from Item 1)
- Test totals (engine tests, UI tests, integration tests)
- Drik parity bottom line: 30/30 on engine v1.0.0-S3
- Acharya review status (LLM-derived in 4C-6-S4; final acharya panel review is post-merge)
- Telemetry baseline numbers from Observatory panels

**AC.4C9.6:** Close artifact authored.

### Item 7 — Update PANCHANG_DAILY status to CURRENT (with caveat)
Master plan §5.2 status lifecycle: `PLANNED → IN_DEVELOPMENT → CURRENT`. With the engine live and exposed via query_panchanga, the asset is functionally usable — but the SQL cache layer (4C-2) is pending. Flip status to `CURRENT_ENGINE_DIRECT` (a new sub-state) in `CAPABILITY_MANIFEST.json`, with `runtime_path: "engine_direct"`. When 4C-2 lands post-4B, flip to plain `CURRENT` with `runtime_path: "cached"`.

Propagate MP.2 mirror to `.gemini/project_state.md`.

**AC.4C9.7:** Status updated; mirror propagated; manifest validates.

### Item 8 — CURRENT_STATE finalization
Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`:
- Phase 4C status: `WAVE_1_COMPLETE_PENDING_PR`
- Add a Wave 1 close summary section
- last_session_id: 4C-9
- next_session_objective: native opens split PR per WAVE_2_MIGRATION_NOTE.md, then any of: Wave 2 expansion (Conductor enhancement + M5-A/4B/4D), Phase 4B (to unblock 4C-2), or production user testing of /panchang

**AC.4C9.8:** State updated.

### Item 9 — SESSION_LOG append
Append the 4C-9 atomic block + a Phase 4C close summary block to `00_ARCHITECTURE/SESSION_LOG.md`.

**AC.4C9.9:** Logged.

### Item 10 — Queue closeout
Update `00_ARCHITECTURE/CONDUCTOR/session_queue.yaml`: 4C-9 → passed; all Phase 4C entries either passed or skipped. Add a queue-closing entry marking "Wave 1 complete; further sessions require Wave 2 queue or fresh manifest."

**AC.4C9.10:** Queue closed.

### Item 11 — Native handoff document
Author `HANDOFF_WAVE_1.md` at worktree root. Sections:
- Wave 1 outcome summary (3 paragraphs)
- The split-PR procedure to run NOW (cherry-pick commands from WAVE_2_MIGRATION_NOTE.md)
- The two PR descriptions ready-to-paste (Conductor → main; Phase 4C → main)
- Wave 2 entry points: pick your battle (Conductor enhancement / Phase 4B / production user testing)
- Open items inventory (4C-2 pending, FOLLOWUPS doc for v2 polish, etc.)

**AC.4C9.11:** HANDOFF_WAVE_1.md present.

### Item 12 — Brief flip + FINAL_SUMMARY
Flip this brief to COMPLETE. Emit FINAL_SUMMARY with explicit "Wave 1 complete — native action required: split PR per HANDOFF_WAVE_1.md."

**AC.4C9.12:** Done. Conductor's banner after this session: `QUEUE COMPLETE — Wave 1 closed. See HANDOFF_WAVE_1.md for next steps.`

---

## §5 — Constraints
**may_touch:**
- `platform/src/app/panchang/**` (Item 1 polish only — surgical, no scope creep)
- `platform/src/app/observatory/**` (Item 2 panels)
- `00_ARCHITECTURE/RED_TEAM/RT_4C_*` (Item 3 finding docs — new)
- `CLAUDE.md` (Item 5 amendment apply)
- `.geminirules` (Item 5 MP.1 mirror)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (Item 7 status flip)
- `.gemini/project_state.md` (Item 7 MP.2 mirror)
- `00_ARCHITECTURE/PHASE_4C_CLOSE_v1_0.md` (Item 6 — new)
- `00_ARCHITECTURE/PHASE_4C_FOLLOWUPS_v1_0.md` (Item 1 — new)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (Item 8)
- `00_ARCHITECTURE/SESSION_LOG.md` (Item 9)
- `00_ARCHITECTURE/CONDUCTOR/session_queue.yaml` (Item 10)
- `HANDOFF_WAVE_1.md` at worktree root (Item 11)
- This brief (Item 12 flip)

**must_not_touch:**
- Engine internals (sealed)
- RetrievalTool (sealed)
- Muhurat backend logic (sealed)
- iCal builder (sealed)
- Ask-Madhav chat injection (sealed)
- Master plan
- Operational brief
- Other corpus layers

## §6 — Close checklist
- [ ] All 12 ACs PASS
- [ ] Red-team 5/5 with verdicts
- [ ] All validators exit 0
- [ ] CLAUDE.md amendment applied + MP.1 mirror
- [ ] Phase 4C close artifact written
- [ ] HANDOFF_WAVE_1.md written
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Wave 1 = Phase 4C only; Wave 2 expansion is post-merge
- Split-PR strategy: cherry-pick Conductor first, then Phase 4C close PR
- 4C-2 stays skipped pending Phase 4B
- Acharya panel real review is post-merge (M10 territory)

## §9 — Canary
The red-team. If RT.4C.4 (Muhurat scoring acharya validity) returns FAIL, scoring weights need real acharya review before shipping — halt and report rather than close Wave 1 on shaky ground.

## §10 — Special note: this is the last Conductor-driven session of Wave 1
After this session closes and FINAL_SUMMARY emits, the Conductor's queue is empty. Conductor banner: `QUEUE COMPLETE`. Native then runs the cherry-pick procedure manually per WAVE_2_MIGRATION_NOTE.md — this is a human step, not Conductor work. Once both PRs land in main, Wave 1 is officially complete.

*End — 4C-9 closes Wave 1.*

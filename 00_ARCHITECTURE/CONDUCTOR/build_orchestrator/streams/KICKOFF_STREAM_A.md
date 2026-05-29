# KICKOFF — Stream A (Foundation)

You are the **Stream A Conductor**. You run fully autonomously with `--dangerously-skip-permissions`. No human gates. No questions to the user.

## Your identity

- Worktree: `/Users/Dev/Vibe-Coding/Apps/MadhavStream-A`
- Branch: `feature/build-orch/stream-a`
- Owned backlog: G6, G12, G13, G15, G21, G23, G24, G26, G37, G48, G49, G50, A6 (vargas writer), A7 (dashas writer)

## Mandatory pre-flight (do this FIRST)

1. Read these in order:
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/STREAM_COORDINATION_v1_0.md` (the master playbook — your protocol)
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CLAIM_LEDGER.yaml`
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/session_queue.yaml` (filter to your stream's entries)
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/tracker/state.json` (filter to your owned assets)
   - For each asset in your backlog, the spec at `00_ARCHITECTURE/<ASSET>_SPEC_v1_0.md`

2. Confirm worktree clean + on `feature/build-orch/stream-a`:
   ```
   git status
   git branch --show-current
   git pull origin feature/build-orch/stream-a --rebase
   ```

3. Confirm `cloud-sql-proxy` is running on :5433 (start with `bash platform/scripts/start_db_proxy.sh &` if not).

## Execution loop (run forever until clean halt)

For each session in your queue (foundation-first ordering):

1. **Claim**: per STREAM_COORDINATION §6 — atomic write to CLAIM_LEDGER.yaml + push to main
2. **Sub-agent**: spawn via Task tool (subagent_type: general-purpose) with the session brief
3. **Execute**: sub-agent writes code, migrations, tests; runs `pytest -n 4` locally
4. **Commit**: on stream branch with `feat(stream-A/<session_id>): <title>`
5. **Cherry-pick**: to main with race-retry per STREAM_COORDINATION §3
6. **CI**: watch 5 min; if red, auto-fix 3× per §5; if still red, tag `ci-red-ignored-<session_id>` and continue
7. **Tracker update**: per STREAM_COORDINATION §9
8. **Release claim**: per §6
9. **Loop**

When your queue is EMPTY: enter work-stealing per STREAM_COORDINATION §6. Look across Stream B/C/D queues for pending sessions with deps satisfied + no file conflict.

When global queue is EMPTY: clean halt + write `streams/STREAM_A_FINAL_REPORT_v1_0.md` per §12.

## Stream A priority ordering (own queue)

Foundation-first to unblock other streams:

```
Wave 1 (independent globals; can run in parallel sub-batches):
  G15-S1  Dasha rule library (32 systems metadata + 7 acharya-selected detail)
  G12-S1  Yoga definitions library (200+ classical yogas)
  G13-S1  Dosha definitions library (~15 dosha classes)
  G24-S1  Vimshottari starting-lord table
  G6-S1   Sankranti table 1950-2100 (per ayanamsha)
  G21-S1  Sade Sati Saturn-sign-changes (per ayanamsha)

Wave 2 (after Wave 1 — dasha/timing globals):
  G23-S1  Chandra bala matrix (12×12)
  G26-S1  Muhurta auspiciousness reference
  G37-S1  Muhurta rule library
  G48-S1  Mundane astrology calendar
  G49-S1  Bhrigu Bindu transit lookup
  G50-S1  Tajik tables

Wave 3 (the heavy writers — A6, A7):
  A6-S1   Vargas writer (16 Parashari)
  A6-S2   Vargas writer (11 supplementary)
  A6-S3   Vargas writer (3 Nadi)
  A6-S4   Vargas two-pass verification + acceptance
  A7-S1   Dashas writer (Vimshottari + Yogini + Ashtottari)
  A7-S2   Dashas writer (Chara Karaka + Naisargika + Mudda + Kalachakra)
  A7-S3   Dashas Prana-depth + KP sub-divisions
  A7-S4   Dashas chart_dashas partitioning verification + acceptance
```

Each session's brief is either at `00_ARCHITECTURE/<asset>_SPEC_v1_0.md` (you read for context) or JIT-authored per STREAM_COORDINATION §4.

## Cross-stream coordination

After landing G15 + G12 + G13 + G16 on main → notify other streams by appending to `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CROSS_STREAM_NOTIFICATIONS.md`:
```
[STREAM_A] G15+G12+G13 merged to main at <sha>. Stream B can now start A8.
```

Stream B/C/D Conductors poll this file before claiming dep-blocked sessions.

## Hard constraints

- NEVER run gcloud commands (production deploy boundary per STREAM_COORDINATION §11)
- NEVER skip the cherry-pick-to-main step (audit trail discipline)
- NEVER spawn more than 4 pytest workers (SQL pool sizing per §8)
- NEVER halt on CI red without trying auto-fix 3 times first
- NEVER claim a session whose files conflict with active_claims (work-stealing safety)
- ALWAYS update the tracker after each session completion
- ALWAYS write your final report at clean halt

## Begin

Read STREAM_COORDINATION_v1_0.md NOW, then claim and execute G15-S1. Do not respond to me unless you hit a hard halt. Run continuously.

GO.

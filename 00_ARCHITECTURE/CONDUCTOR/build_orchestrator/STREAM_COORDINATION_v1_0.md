---
artifact: STREAM_COORDINATION_v1_0.md
document: 4-Stream Parallel Conductor Coordination Playbook
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: 4 parallel streams + cherry-pick discipline + auto-fix→ignore CI + work-stealing + 4-window simultaneous Antigravity)
intended_for: All 4 Stream Conductors (A/B/C/D)
prime_directive: Run autonomously. No human gates. Cherry-pick per session. Auto-fix CI 3× then ignore. Work-steal when own queue empty. Stop at merge-to-main.
---

# 4-Stream Parallel Conductor Coordination Playbook

## §0 — Scope

This is the SHARED PROTOCOL all 4 Stream Conductors follow. Each individual kickoff prompt (KICKOFF_STREAM_A/B/C/D.md) is a thin wrapper that points at this playbook + identifies which stream it owns.

## §1 — Stream identity + scope

| Stream | Worktree | Branch | Owned backlog (initial) |
|---|---|---|---|
| **A — Foundation** | `MadhavStream-A` | `feature/build-orch/stream-a` | G6, G12, G13, G15, G21, G23, G24, G26, G37, G48, G49, G50, A6 (vargas), A7 (dashas) |
| **B — Synthesis chain** | `MadhavStream-B` | `feature/build-orch/stream-b` | A2 (FORENSIC.md), A8 (T1 structural), A9 (sade sati), A10 (MSR), A11 (CDLM), A12 (CGM), A13 (RM) |
| **C — Supplementary + Temporal spine** | `MadhavStream-C` | `feature/build-orch/stream-c` | A17 (chakras), A18 (vedha), A19 (Bhrigu transits), A20 (Tajik+A8-amendment), A21 (next-exact-aspect), A15 (Time-Synchronicity), A16 (Phase-Locked Anchors), A22 (Per-Varsha Digest), G29 (Classical Timing Rules — JIT) |
| **D — META + INF + ACC** | `MadhavStream-D` | `feature/build-orch/stream-d` | INF7, INF8, INF10, INF11, INF12, UTEE_STANDARD, CROSS_ASSET_BRIDGES, META_α, META_β, META_γ, META_δ, META_ε, META_ζ, RETRIEVAL_INTERFACE_REGISTER, ACC1-ACC8, ACC10 |

## §2 — Per-session protocol (every session, every stream)

```
1. Pre-flight
   git fetch origin
   git pull origin <stream-branch> --rebase
   Check CLAIM_LEDGER.yaml — confirm no file conflicts with in-flight sessions in other streams
   Atomically claim the session (see §6 work-stealing)

2. Spawn sub-agent
   Use Task tool with appropriate subagent_type (general-purpose unless brief says otherwise)
   Pass session brief (JIT-author if missing — see §4)
   Authorize sub-agent with --dangerously-skip-permissions

3. Sub-agent executes session scope
   Writes code, migrations, tests
   Runs local test suite scoped to session
   Two-pass verification per writer spec
   Halt sub-agent on hard error (return failure status)

4. Commit on stream branch
   git add <session-touched-files>
   git commit -m "feat(<stream>/<session_id>): <one-line title>"
   git push origin <stream-branch>

5. Cherry-pick to main
   git fetch origin main
   git checkout main
   git pull origin main
   git cherry-pick <commit-sha>
   git push origin main
     RETRY UP TO 5x ON PUSH FAILURE — pull-rebase-push (cross-stream race conditions)
   git checkout <stream-branch>

6. CI watch (max 5 min)
   Poll GitHub Actions for the cherry-picked commit
   If green: mark session complete in tracker + session_queue.yaml + CLAIM_LEDGER.yaml (release)
   If red: enter §5 CI auto-fix protocol

7. Tracker update
   Update session entry in session_queue.yaml (status: completed, merge_sha, ci_status)
   Update tracker state.json (impl status of affected asset: merged_main; operator_action_pending if applicable)
   Append entry to CONDUCTOR_LOG.md

8. Loop
   If own queue has pending sessions: take next-available (deps satisfied)
   If own queue empty: enter §6 work-stealing
   If everything globally done: terminate cleanly
```

## §3 — Cherry-pick race-condition handling

```bash
function cherry_pick_to_main() {
  local COMMIT_SHA=$1
  local MAX_RETRIES=5
  for attempt in $(seq 1 $MAX_RETRIES); do
    git fetch origin main
    git checkout main
    git reset --hard origin/main
    if git cherry-pick "$COMMIT_SHA"; then
      if git push origin main; then
        return 0
      fi
    fi
    # Conflict or push race — back off + retry
    git cherry-pick --abort 2>/dev/null || true
    sleep $((RANDOM % 10 + 5))
  done
  # 5 retries failed — emit blocker, halt this session
  echo "CHERRY-PICK FAILED after $MAX_RETRIES attempts" >> CONDUCTOR_HALT_LOG.md
  return 1
}
```

Cherry-pick conflicts on application code are RARE because streams own disjoint scopes (see §1). When they do happen, it's almost always on shared files (tracker state.json, session_queue.yaml, CONDUCTOR_LOG.md). For those, rebase resolution = "take both" (concat additions). Conductor implements this auto-resolve for known shared files.

## §4 — JIT brief authoring authority

If a session needs a brief that doesn't yet exist on disk (G29 Classical Timing Rule Catalog is the named case):

```
1. Conductor authors the brief at 00_ARCHITECTURE/<BRIEF_NAME>_v1_0.md
2. Brief follows the same frontmatter pattern as existing locked specs
3. Commit the brief as the FIRST commit of the implementing session
4. Then proceed with implementation
5. Tracker state.json updated: brief.status=locked, brief.locked_at=now, brief.path=<file>
```

Conductor never blocks on missing briefs. Authors what it needs JIT.

## §5 — CI failure auto-fix protocol (option B + ignore fallback)

```
After cherry-pick push:
  Wait up to 5 min for GitHub Actions CI to report status

If CI green:
  Proceed to next session

If CI red:
  For attempt in 1..3:
    1. git pull failing commit + diagnose
    2. Sub-agent reads CI failure logs (gh run view <run-id> --log)
    3. Sub-agent identifies failing tests / lint / type errors
    4. Sub-agent applies fix
    5. Commit fix: "fix(<stream>/<session_id>): CI fix attempt $attempt — <root-cause>"
    6. Cherry-pick fix to main
    7. Wait up to 5 min for CI
    8. If green: proceed
    9. If red: try next attempt

If still red after 3 attempts:
  1. Tag the commit: git tag -a "ci-red-ignored-<session_id>" -m "<reason>"
  2. Push tag: git push origin "ci-red-ignored-<session_id>"
  3. Log to CONDUCTOR_HALT_LOG.md with full CI failure context (not a halt — informational)
  4. Mark session status='completed_ci_ignored' in session_queue.yaml
  5. Mark tracker entry with ci_red_ignored_flag=true + operator_review_recommended=true
  6. PROCEED to next session (per native directive: "ignore and continue")
```

Native directive: "no human gates" extends to CI. The audit trail is preserved via the tag + halt-log entry; you (native) batch-review `ci-red-ignored-*` tags after the autonomous run completes.

## §6 — Work-stealing protocol (CLAIM_LEDGER.yaml)

When own queue empty + global queue has pending sessions in other streams:

```yaml
# CLAIM_LEDGER.yaml — atomic claim file, race-resolved via git push
schema: v1
last_updated: <iso>
active_claims:
  - session_id: A8-S3
    stream_owner: B
    claimed_by_stream: B
    claimed_at: <iso>
    files_locked_globs:
      - "platform/python-sidecar/pipeline/writers/t1_structural_writer_a8.py"
      - "platform/python-sidecar/pipeline/writers/__tests__/test_t1_structural*.py"
      - "platform/migrations/14*_a8_*.sql"
    pid: <antigravity_window_pid>
  ...
released_claims:
  - session_id: G15-S1
    completed_at: <iso>
    merge_sha: <sha>
```

Steal procedure:

```
function try_steal() {
  git pull origin main --rebase
  
  # Scan session_queue.yaml for pending sessions across all streams
  PENDING = filter(session_queue, status=pending AND claimed_by IS NULL AND deps_satisfied)
  
  for candidate in PENDING (priority: declared blockers first, then estimated_minutes ascending):
    # Check CLAIM_LEDGER for file conflicts with in-flight sessions
    IN_FLIGHT_GLOBS = union(c.files_locked_globs for c in CLAIM_LEDGER.active_claims)
    if any glob in candidate.files_touched matches IN_FLIGHT_GLOBS: skip
    
    # Atomic claim — write CLAIM_LEDGER, commit, push
    CLAIM_LEDGER.active_claims.add(candidate, claimed_by_stream=my_stream)
    git add CLAIM_LEDGER.yaml
    git commit -m "claim(<my_stream>/<candidate.session_id>): work-stealing"
    if git push: 
      return candidate  # successfully claimed
    else: 
      git reset --hard origin/main  # someone else claimed; retry
  
  if no candidate after 10 scan attempts: return None (terminate cleanly)
}
```

When session completes, RELEASE the claim:

```
function release_claim(session_id) {
  git pull origin main --rebase
  CLAIM_LEDGER.move(session_id, active_claims → released_claims)
  git add CLAIM_LEDGER.yaml
  git commit -m "release(<my_stream>/<session_id>): completed"
  git push origin main  # retry on race
}
```

## §7 — Dependency wait protocol

Each session declares `deps: [<session_id>, ...]` in session_queue.yaml. Sessions don't start until deps are `completed` or `completed_ci_ignored`.

If own next-up session is blocked by deps owned by another stream:
- Option 1: Skip to next non-blocked session in own queue
- Option 2: If no non-blocked sessions in own queue → enter work-stealing (§6)
- Option 3: If even work-stealing finds nothing not-blocked → sleep 60s + retry

Never wait synchronously on another stream. Always pivot to other work or terminate cleanly.

## §8 — SQL connection pool sizing (4 simultaneous windows)

Cloud SQL Auth Proxy default = 100 connections. With 4 streams running parallel test suites:

```
Per-stream connection budget:
  - Writer integration tests: cap pytest at -n 4 (workers)
  - Each test creates ~3-5 connections (engine + 2 cursors + 1 spare)
  → Max per stream during test peak: ~20 connections
  → 4 streams × 20 = 80 connections
  → Headroom: 20 connections for daemon + interactive psql + monitoring

If pool exhaustion errors occur (psycopg2.OperationalError "too many connections"):
  1. Auto-back-off: sleep $((RANDOM % 30 + 30)) seconds + retry
  2. Tag commit with `connection-pool-pressure` for native review
```

Each kickoff prompt enforces `pytest -n 4` via environment variable.

## §9 — Tracker update discipline

Every session completion writes:

```python
# Update tracker state.json
1. Locate item by id in tracker.tracks[].items[]
2. Set impl.status = 'merged_main'
3. Set impl.merge_sha = <cherry-pick-sha-on-main>
4. Set impl.completed_at = <iso>
5. Set impl.session_id = <session_id>
6. Set impl.branch = 'feature/build-orch/stream-<x>'
7. Set impl.stream = <stream>
8. Set impl.ci_status = 'green' | 'ci_red_ignored'
9. Add operator_action_pending if any
10. Append to tracker.activity[] (top of list, cap 200)
11. tracker.meta.last_updated = today

# Atomic write via temp file rename (see existing daemon pattern)
```

Daemon picks up state.json change within 5s and pushes to GCS.

## §10 — Halt conditions (when Conductor stops)

Hard halts (terminate stream + emit blocker):
- Cherry-pick failed after 5 retries
- CI auto-fix loop succeeded one attempt then later session's commits break what was previously fixed (regression cascade)
- Claim-ledger write fails after 5 retries (git infrastructure broken)
- Sub-agent crashes catastrophically (process-level error, not test failure)
- Native intervention via SIGTERM to the Antigravity process

Soft halts (terminate stream cleanly, no blocker):
- Own queue + global queue both empty (everything done; mission complete)
- Native intervention via tracker flag (write `CONDUCTOR_PAUSE` file to repo root)

NOT halts (continue per §5):
- CI red (auto-fix → ignore)
- Single-test failure within a session (sub-agent debugs + fixes within session)
- File-conflict claim race (retry steal)

## §11 — Production deploy boundary

Conductor STOPS AT merge-to-main. Never runs:
- `gcloud run deploy`
- `gcloud run jobs execute`
- `gcloud sql migrations apply`
- `terraform apply`
- Any other production-state-mutating command

For every session whose acceptance requires production action, set `operator_action_pending` in tracker. Native batch-triggers after CI/CD cleanup completes.

## §12 — Final outputs per stream

When a Stream Conductor terminates (clean halt §10), it writes:

```
00_ARCHITECTURE/CONDUCTOR/build_orchestrator/streams/STREAM_<X>_FINAL_REPORT_v1_0.md
```

Contents:
- Sessions executed (count, list, durations)
- Sessions completed_ci_ignored (count, list, tags)
- Work-stolen sessions (count, list, original-stream-owner)
- Total commits to main + final-branch HEAD
- Operator-action-pending items list
- Halt reason (own queue done | work-stealing done | global done)

## §13 — Inter-stream dependency map (initial)

```
Stream A (Foundation) → blocks → Stream B, C, D
  - G15 dasha rule library → blocks A7 (B)
  - G12, G13 → blocks A8 (B)
  - G16 (already merged) → A6 (A)
  - G27 (already merged) → A13 (B)
  - G29 (JIT in C) → A16 (C)

Stream B (Synthesis chain) → blocks → Stream C, D
  - A8 → blocks A20 amendment (C)
  - A11, A12 → blocks META-α/β/γ/δ/ε (D)

Stream C (Supplementary + temporal spine) → blocks → Stream D
  - A15, A16, A22 → blocks META-ζ + UTEE_STANDARD + CROSS_ASSET_BRIDGES (D)

Stream D (META + INF + ACC) → blocks → final ACC close
  - INF7-12 → independent (can run early)
  - META + UTEE + bridges → waits on A/B/C
  - ACC1-10 → waits on everything
```

Each stream's session_queue entry declares its `deps` array. Conductor honors deps before claiming a session.

---

*End of STREAM_COORDINATION_v1_0.md — LOCKED 2026-05-29.*

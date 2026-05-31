---
artifact: STREAM_COORDINATION_v1_0.md
version: 1.0
status: LIVE
arc_id: build_e2e_arc
authored_by: Cowork
authored_at: 2026-05-31
role: Master playbook every stream agent reads at session-open. Defines CLAIM_LEDGER protocol, cherry-pick discipline, CI auto-fix policy, push-race retry, halt conditions, model directive.
---

# Build E2E Arc — Stream Coordination Playbook

Every stream agent (A, B, C, D) reads this file in full at session-open. It
defines the rules of engagement that prevent collisions and guarantee
forward progress across 4 concurrent Antigravity windows.

## §1 — Model + auth + tooling

- **Model directive:** Gemini Pro for non-trivial code. DeepSeek v4 Pro as
  fallback. Cheap flash for boilerplate. **Anthropic API banned per native
  standing order.**
- **Auth:** No GCP credentials needed inside stream agents. All prod
  operations (deploy, migrations, IaC apply) flow through GitHub Actions
  via Workload Identity Federation, triggered by main-branch pushes.
- **Tooling:** standard Antigravity Claude Code shell. `cd platform &&
  npm install` works. `cd platform/python-sidecar && pip install` works.
  `git`, `gh`, `psql` (local proxy only), `terraform fmt/validate` (no
  apply locally) all work.

## §2 — Worktree binding

Each stream agent is bound to ONE worktree:

| Stream | Worktree path | Branch |
|---|---|---|
| A | /Users/Dev/Vibe-Coding/Apps/MadhavHardeningCI  | feat/hardening-ci |
| B | /Users/Dev/Vibe-Coding/Apps/MadhavDataPlumbing | feat/data-plumbing |
| C | /Users/Dev/Vibe-Coding/Apps/MadhavVisualV2     | feat/visual-v2 |
| D | /Users/Dev/Vibe-Coding/Apps/MadhavFunnelPolish | feat/funnel-polish |

Stream agents NEVER cd outside their assigned worktree except to read
session_queue.yaml, CLAIM_LEDGER.yaml, or the brief (which all live in
the canonical repo under `00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/`).

## §3 — Session loop (the core algorithm)

```
load session_queue.yaml for my stream
for each session in my queue (in declared order):
  if session.id is already in CLAIM_LEDGER.released_claims:
    skip (already done)
  if session.id is already in CLAIM_LEDGER.active_claims:
    skip (in flight elsewhere — shouldn't happen since each stream owns its slice, but defensive)
  claim_session(session.id):
    pull --rebase the canonical repo's CLAIM_LEDGER
    append to active_claims with timestamp + stream_id
    commit + push (retry × 3 on push race; if all fail, halt with note)
  do_session(session):
    read brief section for this session id
    author code per brief
    run gate command
    if gate fails:
      ci_autofix_loop(max=5)
      if still failing after 5: tag ci_red_ignored, proceed anyway
    commit on stream branch with message "session_id: title"
    push stream branch
    cherry_pick_to_main(commit_sha):
      pull --rebase origin/main
      cherry-pick <commit_sha>
      retry × 3 on conflict (try clean rebase, then auto-merge tool, then halt)
      push origin/main
      retry × 3 on push race
  release_session(session.id):
    move from active_claims to released_claims
    commit + push CLAIM_LEDGER
when queue is empty for my stream:
  print summary report
  exit
```

## §4 — CLAIM_LEDGER atomic protocol

The CLAIM_LEDGER lives at `00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/CLAIM_LEDGER.yaml`.

**Claim** (before starting a session):
1. `git pull --rebase origin main` (in the canonical repo path, NOT the worktree)
2. Edit CLAIM_LEDGER.yaml: append to `active_claims:` an entry like:
   ```yaml
   - session_id: A-S1
     stream: A
     claimed_at: "2026-05-31T12:34:56Z"
     claimed_by: "stream-a agent"
   ```
3. `git add CLAIM_LEDGER.yaml && git commit -m "claim: A-S1"`
4. `git push origin main` — on failure (race), `git pull --rebase` and retry up to 3 times
5. If 3 retries exhaust: halt this session and write to `CLAIM_LEDGER.halted[]`

**Release** (after a session completes successfully):
1. `git pull --rebase origin main`
2. Edit CLAIM_LEDGER: remove from `active_claims`, append to `released_claims` with `completed_at` and `merge_sha`
3. commit + push with same retry policy

## §5 — Cherry-pick to main policy

**This arc cherry-picks to main eagerly — no hard gate, no integration branch.**

After each session lands cleanly on the stream branch:

```bash
COMMIT_SHA=$(git rev-parse HEAD)
git fetch origin
cd /Users/Dev/Vibe-Coding/Apps/Madhav   # canonical repo
git checkout main
git pull --rebase origin main
git cherry-pick $COMMIT_SHA              # may fail on conflict
git push origin main                     # may fail on race
```

**Conflict resolution:**
- Attempt 1: clean cherry-pick.
- Attempt 2: `git cherry-pick --strategy=recursive -X theirs` (your changes win).
- Attempt 3: full rebase of stream branch onto latest main, then cherry-pick again.
- If still fails: tag this session in `CLAIM_LEDGER.halted` with `reason: cherry_pick_conflict`. Continue to NEXT session in queue.

**Push race:**
- Up to 3 retries with `git pull --rebase origin main` between attempts.
- If exhausted: halt this session in `CLAIM_LEDGER.halted` with `reason: push_race`.

## §6 — CI auto-fix policy

Some sessions write code that may not pass tests on first try. After every
session, the agent runs the session's `gate` command. If it fails:

```
attempt = 1
while attempt <= 5 and gate fails:
  read gate output (stderr + stdout)
  diagnose: what's the error? (failing test, type error, lint, etc.)
  patch: smallest change to make it pass without weakening the test intent
  commit: "fix(A-S1): ci attempt N — <one-line summary>"
  re-run gate
  attempt += 1

if gate still fails after 5 attempts:
  tag session in CLAIM_LEDGER.ci_red_ignored
  commit message includes "[ci_red_ignored after 5 attempts]"
  PROCEED to cherry-pick anyway — main will auto-deploy and CI will reflect the residual
```

The 5-attempt auto-fix budget matches native standing decision (this arc).

## §7 — Auto-deploy chain (Stream A's S8 makes this real)

After Stream A's S8 lands on main, `.github/workflows/deploy.yml` triggers
automatically on every push to main with this sequence:

```
1. checkout main
2. build amjis-web container + push to GCR
3. build amjis-sidecar container + push to GCR
4. run platform/scripts/migrate.ts against prod DB
     - uses Cloud SQL Auth Proxy + Workload Identity
     - applies any new migrations from platform/migrations/ and platform/supabase/migrations/
     - idempotent (skips already-applied)
5. terraform apply -auto-approve in infra/
6. deploy amjis-web revision (no traffic)
7. deploy amjis-sidecar revision (no traffic)
8. run scripts/operator/end_to_end_smoke.sh against the new revisions
9. if smoke passes: flip traffic 100% to new revisions
   if smoke fails: tag the revisions [smoke_failed], leave previous serving
```

Before A-S8 lands, the OLD deploy.yml runs (web-only, no migration step,
manual IaC). After A-S8 lands, every subsequent main push goes through
the full auto chain. Streams B/C/D get the upgraded chain for free as
soon as A-S8 cherry-picks.

## §8 — Halt conditions (when to stop, not soldier on)

A stream agent halts (writes to CLAIM_LEDGER.halted with reason and continues
to next session OR exits if all remaining sessions blocked):

- 3 push-race retries exhausted
- 3 cherry-pick conflict resolution attempts exhausted
- Brief references a file/column/binding that doesn't exist and isn't creatable
- A session would require crossing the worktree boundary (touching another stream's files)
- Prod DB ops attempted from inside an agent (those go through deploy.yml only)

A stream agent does NOT halt for:
- Single CI failure (auto-fix up to 5 attempts)
- Single push race (retry up to 3)
- Single cherry-pick conflict (retry up to 3)
- pre-existing unrelated test failures (note in commit, proceed)

## §9 — Cross-stream file boundaries

Each stream owns specific file paths. If a session inside your stream
would touch a file owned by another stream, HALT — that's a brief authoring
error, not something to resolve at runtime.

| Stream | Owns |
|---|---|
| A | `platform/src/app/api/build/{start,reap,active}/**`, `platform/src/lib/{auth,cloud_run,migrate}/**`, `infra/**`, `.github/workflows/deploy.yml`, `platform/scripts/migrate.ts`, `scripts/operator/end_to_end_smoke.sh` |
| B | `platform/python-sidecar/pipeline/{build_events.py,dispatcher.py}`, `platform/python-sidecar/pipeline/__tests__/test_build_events.py`, `platform/src/types/sse_events.ts` |
| C | `platform/src/components/cockpit/**`, `platform/src/components/clients/NewClientForm.tsx` (visual only), `platform/src/lib/jyotish/asset_names.ts`, `platform/src/styles/**` |
| D | `platform/src/components/clients/NewClientForm.tsx` (functional only — coordinate with C via the file conflict-detection), `platform/src/app/api/clients/create/route.ts`, `platform/src/app/api/build/[id]/cancel/route.ts`, `platform/tests/e2e/new-client-flow.spec.ts` |

**Conflict-prone file:** `NewClientForm.tsx` is touched by both C (visual)
and D (functional). Discipline: C's sessions edit ONLY styling, layout,
and rendering. D's sessions edit ONLY state, validation, and submit handler.
If they conflict on a cherry-pick to main, the second arrival rebases.

## §10 — Reporting

When a stream finishes its queue, the agent prints to console:

```
=== STREAM <X> REPORT ===
Sessions completed: <N>/<total>
CI auto-fix invocations: <count>
Cherry-pick conflict retries: <count>
Push race retries: <count>
Sessions in ci_red_ignored: <list>
Sessions in halted: <list>
Final commit on main from this stream: <SHA>
=== END REPORT ===
```

---

End of playbook.

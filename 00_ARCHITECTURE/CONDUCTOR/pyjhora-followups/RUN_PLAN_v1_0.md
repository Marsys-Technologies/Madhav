---
artifact: RUN_PLAN_v1_0.md
run_id: PYJHORA_FOLLOWUPS
version: 1.0
status: READY-TO-LAUNCH
authored_at: 2026-06-01
authored_by: cowork-planner
authority: native_decision_2026-06-01 (full autonomous run, no human gates)
implementation_surface: Claude Code in Google Antigravity IDE (gcloud + MCPs present)
target_branch_policy: per-stream branch+worktree → merge to main at stream close. main is the target.
autonomy: FULL — code, commit, merge to main, deploy, prod DB migrate, native e2e verify. No human gate.
---

# PyJHora follow-ups — autonomous Conductor run

Four work items from the PyJHora post-merge review, run as **3 parallel coding streams +
1 convergence phase**, all landing on `main`, executor-autonomous through deployment.

## 1 · Autonomy charter (read first)

The native has authorised a fully autonomous run. Each Antigravity executor session runs
with `--dangerously-skip-permissions` and carries `gcloud` + MCP credentials. There are
**no human gates** in this run: sessions commit, merge to `main`, deploy to Cloud Run, apply
production migrations, and trigger the native build themselves.

Guardrails that remain in force (these are correctness rules, not gates):

- **No Anthropic models** anywhere (`[[llm-model-selection]]`). Planner/synthesis stay Gemini/DeepSeek.
- **No JH-parity / FORENSIC-v8.0 value oracle** (`[[no-jh-parity-anywhere]]`). Verification is internal-consistency only.
- **No cross-stream file edits.** Each stream touches only its declared scope (§3 matrix).
  Cross-contamination is recovered by cherry-pick to main, never rebase-on-another-branch
  (`[[two-stream-branch-policy]]`).
- **Grep-presence ≠ compile-success.** After any merge resolution run `tsc --noEmit` + the
  relevant `pytest`/`vitest` (`[[grep-check-is-not-compile-check]]`).
- **Deploy hygiene:** `NEXT_PUBLIC_*` flags are build-arg-baked (`[[next-public-build-arg-baking]]`);
  `deploy-cloudrun@v2` merges env vars — pair removals with `--remove-env-vars`
  (`[[deploy-cloudrun-env-merge]]`).
- **Each stream self-verifies before merge.** Do not run the consolidated `answer:eval` per
  stream — that runs ONCE in Phase B (`[[retrieval-tools-consolidated-eval]]`).

## 2 · Streams

| Stream | Work | Brief | Branch |
|---|---|---|---|
| **S1** | Build-task OIDC 401 fix (real Cloud Tasks trigger path) | `CLAUDECODE_BRIEF_BUILD_TASK_OIDC_401_FIX_v1_0.md` | `fix/build-task-oidc-401` |
| **S2** | jh-parity residue cleanup in `platform/` code paths | `CLAUDECODE_BRIEF_JH_PARITY_RESIDUE_CLEANUP_v1_0.md` | `chore/jh-parity-residue-cleanup` |
| **S3** | Forensic renderer wiring (un-stub forensic_writer) | `CLAUDECODE_BRIEF_STREAM_F_FORENSIC_RENDER_v1_0.md` | `feature/stream-f-forensic-render` |
| **B** | Convergence: deploy + migrate + native e2e + ledger | this file §5 + `OPERATOR_LEDGER_PATCH_PYJHORA_POSTMERGE_v1_0.md` | direct on `main` |

S1, S2, S3 run **in parallel** (Phase A). B runs **after all three merge** (Phase B).

## 3 · Parallel-safety matrix (verified no overlap)

| Path glob | S1 | S2 | S3 |
|---|:--:|:--:|:--:|
| `platform/src/app/api/build/**`, `platform/src/lib/build/**` | ✏️ | | |
| `platform/scripts/**`, `platform/evals/**`, `platform/src/app/api/engine/**` | | ✏️ | |
| `platform/python-sidecar/pipeline/**`, `pyjhora_adapter/**` (read) | | | ✏️ |
| `00_ARCHITECTURE/**` (ledger) | | | | → Phase B only |

No two Phase-A streams write the same file. **`SESSION_LOG.md` + `CURRENT_STATE.md` are NOT
touched by Phase-A streams** — all governance-doc writes happen in Phase B to avoid the
classic merge-conflict (`[[gismcp-deploy-recoveries]]`: keep all entries on SESSION_LOG
conflicts). Phase-A streams write only a one-line `RUN_LOG.md` entry under this run dir.

## 4 · Phase A — parallel execution (each stream, identical protocol)

1. `git fetch origin && git worktree add <wt> -b <branch> origin/main`
2. Read the stream's brief end-to-end. Re-read the memory hooks it names.
3. Implement per the brief. Commit after each logical step (clear messages).
4. Self-verify: brief's acceptance criteria all green; `tsc --noEmit` + `pytest`/`vitest`.
5. Merge to main: `git checkout main && git pull && git merge --no-ff <branch>` →
   resolve any conflicts (there should be none — disjoint scope) → push origin/main.
6. Append a one-line entry to `00_ARCHITECTURE/CONDUCTOR/pyjhora-followups/RUN_LOG.md`
   (stream, merge SHA, AC pass/fail). Retire the worktree + branch.
7. **Do NOT deploy from a Phase-A stream.** Deploy is Phase B (batched, one rollout).

Gate to enter Phase B: all three of `S1_MERGED`, `S2_MERGED`, `S3_MERGED` true in RUN_LOG.

## 5 · Phase B — convergence (sequential, on main)

Runs once after S1+S2+S3 are merged. One session.

> ⛔ **DO NOT make `amjis-web` private.** The S1 executor's report suggested
> `gcloud run services remove-iam-policy-binding amjis-web --member=allUsers
> --role=roles/run.invoker`. **DO NOT RUN IT.** `amjis-web` is the public end-user portal
> (`/consume`, `/clients/new`, cockpit, super-admin dashboards). Removing `allUsers` makes
> the entire website require IAM tokens — a portal-wide outage. The actual S1 fix was an
> env-baking correction (dot→bracket `process.env['BUILD_TASK_QUEUE']`); it works on the
> public service. The service stays public. `amjis-mcp` is the only private service.

1. **Verify/set the build-task env vars on `amjis-web` runtime (the real enabler).** The
   handler reads `BUILD_TASK_QUEUE` and `trigger.ts` reads `BUILD_TASK_QUEUE`,
   `BUILD_TASK_QUEUE_LOCATION`, `BUILD_TASK_AUDIENCE` — none are in `deploy.yml`, so they
   must exist as Cloud Run runtime env vars. Confirm present; if missing, set them:
   ```bash
   gcloud run services describe amjis-web --region asia-south1 --project madhav-astrology \
     --format='value(spec.template.spec.containers[0].env)' | tr ',' '\n' | grep BUILD_TASK
   # if absent:
   gcloud run services update amjis-web --region asia-south1 --project madhav-astrology \
     --update-env-vars BUILD_TASK_QUEUE=marsys-build-queue,BUILD_TASK_QUEUE_LOCATION=asia-south1,BUILD_TASK_AUDIENCE=<amjis-web run URL>
   ```
2. **Deploy from main.** `gh workflow run deploy.yml --ref main`. Wait for `deploy-web` AND
   `deploy-sidecar` green. The rebuild is required — the dot→bracket fix only lands on a
   fresh standalone build. S3 needs `amjis-sidecar` (renderer); S1/S2 ride `amjis-web`.
3. **Verify the build trigger is fixed (S1).** Confirm the BUILD_TRIGGER flag is on, mint
   a `__session`, POST `/api/build/start` for the native chart
   `362f9f17-95a5-490b-a5a7-027d3e0efda0` — it must dispatch via Cloud Tasks (NOT job-direct)
   and reach `build_complete`. This is the S1 acceptance in production. Keep `amjis-web` public.
3. **Verify forensic render (S3).** Query `chart_documents` for the native build:
   1 `forensic_render` doc per ayanamsha, non-empty `content_md`, linter-clean; `rag_chunks`
   with `source_type='forensic_render'` present.
4. **Apply now-unblocked partition migrations.** `chart_facts` now has real per-`chart_id`
   rows, so migrations **121/122/124** (`query_trace_steps` partitions) can apply. Apply in
   order; verify `chart_id` non-NULL coverage first.
5. **Remove `BUILD_TASK_AUTH_BYPASS` from amjis-web** (`--remove-env-vars`) — hygiene.
6. **Ledger + governance close.** Apply `OPERATOR_LEDGER_PATCH_PYJHORA_POSTMERGE_v1_0.md`:
   bump `CURRENT_STATE` to v5.67 (or next free version — verify origin/main first), update
   `OPERATOR_ACTIONS_PENDING.md`, append a single consolidated `SESSION_LOG.md` entry
   covering S1+S2+S3+B. Run `answer:eval` ONCE here (consolidated). Red-team if `IS.8(b)`
   cadence is due.
7. Update `RUN_LOG.md` → `RUN_COMPLETE`.

## 6 · Rollback

Per-stream: `git revert` the merge on main + redeploy. Engine/auth rollback: redeploy the
prior Cloud Run revision (`amjis-sidecar` / `amjis-web`). Partition migrations 121/122/124:
each ships with its down-migration; revert in reverse order. The native chart can be rebuilt
idempotently (writers upsert on their unique constraints).

## 7 · Files in this run dir

- `RUN_PLAN_v1_0.md` (this file)
- `session_queue.yaml` (machine-readable queue + gates)
- `OPERATOR_LAUNCH.md` (paste-ready kickoff prompts + how to launch)
- `RUN_LOG.md` (created by the first stream; live run state)

---

*End of RUN_PLAN_v1_0.md*

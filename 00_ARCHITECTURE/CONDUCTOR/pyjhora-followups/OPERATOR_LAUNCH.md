---
artifact: OPERATOR_LAUNCH.md
run_id: PYJHORA_FOLLOWUPS
version: 1.0
status: READY-TO-LAUNCH
authored_at: 2026-06-01
how_to_use: >
  Open three Antigravity Claude Code windows for Phase A. Paste one kickoff block into each.
  They run in parallel, each in its own worktree, and merge to main when done. When all three
  report merged, open a fourth window and paste the Phase B block.
---

# Launch — PyJHora follow-ups autonomous run

Plan: `RUN_PLAN_v1_0.md`. Queue: `session_queue.yaml`. Three parallel coding streams
(S1/S2/S3) → one convergence phase (B). Full executor autonomy (commit + merge + deploy).

## Pre-launch (once, from the main checkout)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git checkout main && git pull --ff-only origin main
# worktrees are created by each kickoff prompt; nothing to pre-create
```

Confirm three windows can run concurrently without sharing a checkout — each kickoff makes
its own `git worktree` (per `[[parallel-sessions-need-worktrees]]`).

---

## Window 1 — Stream S1 (build-task 401 fix)

```
You are an autonomous executor. Run with --dangerously-skip-permissions. Full autonomy:
code, commit, and merge to main. No human gate. Do NOT deploy (deploy is Phase B).

Setup:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git fetch origin
  git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavS1-BuildAuth -b fix/build-task-oidc-401 origin/main
  cd /Users/Dev/Vibe-Coding/Apps/MadhavS1-BuildAuth

Execute 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BUILD_TASK_OIDC_401_FIX_v1_0.md end-to-end.
Start with §3 diagnosis READ-ONLY (capture whether the OIDC Authorization header reaches
the container) before any fix. Implement Design A unless the evidence says otherwise.
Honour may_touch / must_not_touch / hard_bans in the brief frontmatter. Do NOT touch any
file outside S1's scope in session_queue.yaml. Do NOT edit SESSION_LOG.md or CURRENT_STATE
(Phase B owns governance docs).

Verify: brief's 5 acceptance criteria; tsc --noEmit clean; vitest task_route tests green;
BUILD_TASK_AUTH_BYPASS zero-effect test still green.

Merge: git checkout main && git pull --ff-only && git merge --no-ff fix/build-task-oidc-401
&& git push origin main. Append one line to
00_ARCHITECTURE/CONDUCTOR/pyjhora-followups/RUN_LOG.md: "S1 MERGED <sha> AC=<n/n>".
Retire the worktree + branch. Then STOP and report the merge SHA + AC checklist.
```

---

## Window 2 — Stream S2 (jh-parity residue cleanup)

```
You are an autonomous executor. Run with --dangerously-skip-permissions. Full autonomy:
code, commit, and merge to main. No human gate. Do NOT deploy (Phase B).

Setup:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git fetch origin
  git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavS2-JHParity -b chore/jh-parity-residue-cleanup origin/main
  cd /Users/Dev/Vibe-Coding/Apps/MadhavS2-JHParity

Execute 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_JH_PARITY_RESIDUE_CLEANUP_v1_0.md end-to-end.
Scope is platform/ ONLY (00_ARCHITECTURE/ governance cleanup is a separate F2 arc — do not
touch it). Repurpose hard_gates G2 to enforce ABSENCE of jh_oracle/test_jh_parity artifacts.
Remove jh_parity_sha only after grepping all consumers. git rm the committed _scratch/ +
gitignore it. Do NOT edit applied migrations 124/126 (provenance strings stay). Do NOT edit
SESSION_LOG / CURRENT_STATE. Stay strictly inside S2's file scope in session_queue.yaml.

Verify: grep -rn 'jh_parity|jh_oracle' platform/ src/ → 0 hits in executable code paths;
tsc --noEmit clean; vitest + pytest green.

Merge to main (--no-ff), push, append "S2 MERGED <sha> AC=<n/n>" to RUN_LOG.md, retire
worktree+branch, STOP and report.
```

---

## Window 3 — Stream S3 (forensic renderer wiring)

```
You are an autonomous executor. Run with --dangerously-skip-permissions. Full autonomy:
code, commit, and merge to main. No human gate. Do NOT deploy (Phase B).

Setup:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git fetch origin
  git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavS3-Forensic -b feature/stream-f-forensic-render origin/main
  cd /Users/Dev/Vibe-Coding/Apps/MadhavS3-Forensic

Execute 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_STREAM_F_FORENSIC_RENDER_v1_0.md end-to-end.
Do S4a FIRST: empirically dump pyjhora_adapter.compute_chart() output and diff it against
what the section renderers .get(...). Build the input shim render/_chart_output_adapter.py —
fix the shape THERE, never by rewriting the tested renderers. Then wire forensic_writer to
ForensicRenderer (register all 13 sections), persist to chart_documents, register in
WRITER_REGISTRY. Then S4b: integration test + rag_embedder verify + EXPECTED_ROW_COUNTS.
Do NOT weaken the no_narration_linter. Do NOT touch pyjhora_adapter/ or migrations. Do NOT
edit SESSION_LOG / CURRENT_STATE. Stay inside S3's file scope.

Verify: brief's 8 acceptance criteria; pytest platform/python-sidecar/ green; renderers
unmodified except genuine bugs.

Merge to main (--no-ff), push, append "S3 MERGED <sha> AC=<n/n>" to RUN_LOG.md, retire
worktree+branch, STOP and report.
```

---

## Window 4 — Phase B (convergence) — launch ONLY after S1+S2+S3 all show MERGED in RUN_LOG.md

```
You are an autonomous executor. Run with --dangerously-skip-permissions. Full autonomy
including deploy, production migrations, and the native chart build. No human gate.

Precondition: confirm 00_ARCHITECTURE/CONDUCTOR/pyjhora-followups/RUN_LOG.md shows
S1 MERGED, S2 MERGED, S3 MERGED. If any is missing, STOP and report — do not proceed.

Work on main:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav && git checkout main && git pull --ff-only

DO NOT make amjis-web private. Do NOT remove allUsers run.invoker from amjis-web — it is the
public end-user portal; removing it is a site-wide outage. The S1 fix was an env-baking
correction and works on the public service. Only amjis-mcp is private.

Execute Phase B per 00_ARCHITECTURE/CONDUCTOR/pyjhora-followups/RUN_PLAN_v1_0.md §5:
1. Verify/set amjis-web runtime env vars (the real S1 enabler): BUILD_TASK_QUEUE,
   BUILD_TASK_QUEUE_LOCATION, BUILD_TASK_AUDIENCE. None are in deploy.yml. If absent:
   gcloud run services update amjis-web --region asia-south1 --project madhav-astrology
   --update-env-vars BUILD_TASK_QUEUE=marsys-build-queue,BUILD_TASK_QUEUE_LOCATION=asia-south1,BUILD_TASK_AUDIENCE=<amjis-web run URL>
2. Deploy from main: gh workflow run deploy.yml --ref main; wait deploy-web + deploy-sidecar
   green. (Rebuild required — the dot→bracket fix only lands on a fresh standalone build.)
3. Verify S1: trigger native chart 362f9f17-95a5-490b-a5a7-027d3e0efda0 via /api/build/start
   (Cloud Tasks path, NOT job-direct); confirm build_complete. Keep amjis-web public.
3. Verify S3: chart_documents has 1 forensic_render doc/ayanamsha, content_md non-empty,
   linter clean; rag_chunks(source_type=forensic_render) present.
4. Apply migrations 121/122/124 (query_trace_steps partitions) — verify chart_id non-NULL first.
5. gcloud run services update amjis-web --region asia-south1 --project madhav-astrology
   --remove-env-vars BUILD_TASK_AUTH_BYPASS
6. Run answer:eval ONCE (consolidated). Record result.
7. Ledger close: apply 00_ARCHITECTURE/OPERATOR_LEDGER_PATCH_PYJHORA_POSTMERGE_v1_0.md —
   bump CURRENT_STATE (verify next free version on origin/main; do not collide with v5.66),
   update OPERATOR_ACTIONS_PENDING.md, append ONE consolidated SESSION_LOG entry for
   S1+S2+S3+B. Run IS.8(b) red-team if cadence due.
8. Set RUN_LOG.md → RUN_COMPLETE. Report: deploy revisions, native build_id, chart_facts +
   chart_documents row counts, migration status, answer:eval result.
```

---

## Visibility while it runs

- Live state: `00_ARCHITECTURE/CONDUCTOR/pyjhora-followups/RUN_LOG.md` (each stream appends).
- Per-stream branches: `git branch -a | grep -E 'build-task-oidc|jh-parity|stream-f'`.
- Phase gate: Phase B must not start until all three Phase-A lines are MERGED.

## If a stream stalls

Each stream is independent — a stall in one does not block the others. If S1 or S3 cannot
merge, Phase B can still deploy the merged subset, but: skip the S1 verify if S1 unmerged
(trigger native build job-direct as the 2026-06-01 fallback), and skip the S3 forensic
verify if S3 unmerged (forensic stays stub — note it in the ledger). Do not block the whole
run on one stream.

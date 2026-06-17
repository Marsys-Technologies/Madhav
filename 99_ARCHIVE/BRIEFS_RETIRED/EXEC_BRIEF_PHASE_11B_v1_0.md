---
brief_id: EXEC_BRIEF_PHASE_11B
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_11B_v1_0.md and execute it."
phase: 11B
phase_name: Pipeline Cutover — Stage 2 (Legacy Code Removal)
risk_classification: HIGH
parallelizable_with: []
depends_on: [EXEC_BRIEF_PHASE_11A_v1_0.md (COMPLETE — smoke script must have passed)]
gate: "Native must have run cutover:stage1-smoke and confirmed all 8 classes return ✅ before this brief is triggered. Brief halts at Stream A's pre-flight check otherwise."
estimated_streams: 5
---

# EXEC_BRIEF — Phase 11B — Pipeline Cutover Stage 2 (Legacy Removal)

## Mission

Permanently delete the legacy code path. After this stage, the new pipeline is the only pipeline — there is no flag-OFF code branch in `route.ts`, no `consume-tools.ts`, no `pipelineEnabled` prop chain in the UI. The codebase is simpler. The cost is irreversibility: rolling back requires `git revert` of this PR, not a flag flip.

This brief is **risk classification HIGH** — the highest risk classification of any phase in the build. The legacy code is the safety net that has protected every prior phase. Removing it commits to the new architecture as the production architecture.

## Pre-flight gate (Stream Pre)

**Stream Pre — Verification before any deletion.** This stream MUST run first and MUST pass before any other stream proceeds.

1. Verify Phase 11A is complete: read `00_ARCHITECTURE/SESSION_LOG.md`, confirm a Phase 11A close entry is present.
2. Run the smoke script: `npm run cutover:stage1-smoke`. Must print green ✅ for all 8 classes.
3. Verify the `audit_log` table has at least 16 rows total (Phase 11A's smoke + at least one re-run by native).
4. Verify zero open issues tagged `cutover-blocker` in the project tracker (if applicable; if no tracker, native confirms verbally — Sonnet asks if unclear).

**If any of the above fails, the brief HALTS with a clear error message. Native must investigate and either fix the underlying issue or re-trigger Phase 11A.**

## Scope (`may_touch` / `must_not_touch`)

**`may_touch`:**
- `platform/src/app/api/chat/consume/route.ts` — delete the flag-OFF branch; route always uses new pipeline
- `platform/src/lib/synthesis/consume-tools.ts` — DELETE entirely
- `platform/src/lib/synthesis/__tests__/consume-tools.test.ts` (if exists) — DELETE
- `platform/src/components/consume/ConsumeChat.tsx` — remove `pipelineEnabled` prop branching; component always renders new UI
- `platform/src/components/consume/StreamingAnswer.tsx` — remove flag-gated mount check; always mount
- `platform/src/app/consume/page.tsx` and any consume page wrapper — remove `pipelineEnabled` server-side fetch + prop pass-through
- `platform/src/lib/config/feature_flags.ts` — REMOVE `NEW_QUERY_PIPELINE_ENABLED` flag entry entirely (no longer meaningful)
- `platform/src/lib/config/__tests__/feature_flags.test.ts` — remove `NEW_QUERY_PIPELINE_ENABLED` assertions
- `.env.example` — remove `NEW_QUERY_PIPELINE_ENABLED` line
- Any other dead code reachable only via the deleted flag-OFF branch (Sonnet identifies via grep + dead-code analysis)
- `00_ARCHITECTURE/SESSION_LOG.md`, `CURRENT_STATE_v1_0.md`, `CLAUDE.md` — documentation updates

**`must_not_touch`:**
- All other feature flags (`AUDIT_ENABLED`, checkpoint flags, panel flags) — those have legitimate operational reasons to stay
- `platform/python-sidecar/**` — sidecar untouched (out of scope; the M2/B.5 path is independent)
- Any test that specifically tests the new pipeline (those are now load-bearing for behavior verification)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (manifest builder will pick up the deletions automatically; verify it ran correctly)
- Any historical archive file (predecessor docs, supersedence trail) — historical record is preserved

## Sub-streams (5 total, all sequential after Stream Pre)

### Stream A — Identify and inventory legacy code

- Use `grep -r "NEW_QUERY_PIPELINE_ENABLED" platform/src/` to find every reference to the flag.
- Use `grep -r "pipelineEnabled" platform/src/` to find every reference to the prop chain.
- Use `grep -r "consume-tools" platform/src/` to find every import of the legacy file.
- Build a deletion plan as a checklist file `platform/scripts/cutover/stage2_deletion_plan.md` (delete this file at end of stream E).
- The plan must enumerate every file that will be touched. If anything outside the `may_touch` list appears in the plan, **HALT and surface to native** — possible scope creep.
- 0 tests; this stream is inventory only.

### Stream B — Delete the legacy code

- Execute the deletion plan from Stream A. For each file:
  - If the file is the legacy file itself (`consume-tools.ts`), delete it entirely.
  - If the file has a flag-OFF branch (`route.ts`, `ConsumeChat.tsx`, etc.), delete the branch and unindent the new-pipeline branch to be the only path.
  - If the file references `pipelineEnabled` as a prop, remove the prop from the component signature and the call sites.
- After each deletion, run `npm run build` (or equivalent) to catch broken imports immediately. Fix imports as they break.
- After all deletions: run `lint` + `type-check` and fix any residue.
- 0 new tests; existing tests verify the new path still works.

### Stream C — Remove the dead flag

- Delete the `NEW_QUERY_PIPELINE_ENABLED` entry from `feature_flags.ts` schema.
- Delete the `.env.example` line documenting it.
- Update or remove any test that explicitly tested the flag's existence or its toggleability.
- The flag must no longer appear anywhere in the codebase. `grep -r "NEW_QUERY_PIPELINE_ENABLED" platform/` should return zero results.

### Stream D — Verification

- Run the full test suite: `npm test`. All tests pass. Pre-existing failures from prior phases (the supabase-import + parity_validator issues flagged forward) are still expected; no new failures.
- Run `npm run lint`: clean.
- Run `npm run type-check`: clean.
- Re-run `npm run cutover:stage1-smoke` (still useful — verifies the new pipeline still works after the deletion). Must still print green ✅ for all 8 classes.
- Run `npm run audit:smoke`: green.
- Run `npm run checkpoint:eval`: accuracy on offline corpus unchanged from Phase 6 baseline (within ±2pp).
- Manual smoke: native opens Consume tab in dev, submits one query of each of 8 classes, visually confirms the rendering. (This is a native-driven step; Sonnet flags it as the final acceptance gate.)

### Stream E — Close out + governance

- Delete the `stage2_deletion_plan.md` working file from Stream A.
- Append a Phase 11B close entry to `00_ARCHITECTURE/SESSION_LOG.md` listing every deleted file + every modified file.
- Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`: new pipeline is now the only pipeline; legacy code path is removed; no flag-OFF state exists for the master pipeline.
- Update `CLAUDE.md` §F (Current execution position) to reflect the post-cutover reality. Remove any text that references "the legacy path" or "flag-OFF behavior" or "pipelineEnabled prop" — those are now historical.
- Run the manifest builder if it picks up code surfaces (verify `CAPABILITY_MANIFEST.json` either updates correctly or remains stable depending on what it tracks).
- Bump CLAUDE.md version (e.g., v2.0 → v2.1) since this is a substantive amendment.

## Critical constraints

- **Pre-flight is a hard gate.** If Stream Pre fails, no other stream proceeds. The brief halts and reports to native.
- **Inventory before deletion.** Stream A produces a written plan that Sonnet executes in Stream B. The plan must stay within the `may_touch` list. If grep surfaces references in unexpected files, halt and surface to native.
- **Build after every deletion.** Stream B uses incremental verification — `npm run build` after each file change — to catch broken imports immediately rather than at the end.
- **No silent flag preservation.** Stream C must completely remove `NEW_QUERY_PIPELINE_ENABLED`. A leftover reference in a comment or test is acceptable only if it's clearly historical (e.g., `// Removed in Phase 11B 2026-04-28`).
- **No rollback path in code.** Once Stream B runs, the only way to restore the legacy path is `git revert`. Native must understand this before triggering.
- **Other flags survive.** `AUDIT_ENABLED`, `VALIDATOR_FAILURE_HALT`, all checkpoint flags, all panel flags — all stay. They have legitimate operational reasons to remain toggleable.

## Done criteria

1. Stream Pre passes (Phase 11A confirmed complete + smoke green).
2. Stream A produces a deletion plan that stays within `may_touch`.
3. Stream B executes the plan; codebase compiles.
4. Stream C removes the dead flag; grep confirms zero references.
5. Stream D verification: full test suite green, lint clean, type-check clean, cutover smoke still green, audit smoke green, checkpoint eval accuracy preserved.
6. Stream E governance updates landed.
7. Native runs manual smoke on 8 classes via the Consume tab and accepts.

## Risk classification: HIGH

This is the highest-risk phase in the entire build. Mitigations:
- Phase 11A's smoke script gates this brief
- Stream Pre adds an explicit gate at brief entry
- Stream A inventories before Stream B deletes
- Stream B uses incremental build verification (catch breakage at the file boundary, not at the end)
- Stream D's verification is multi-layered (unit tests + smoke + audit + manual)
- Other operational flags survive (we're not removing the safety net for checkpoints or panel mode, only for the master pipeline switch)

The unavoidable residual risk is that some failure mode of the new pipeline is rare enough to escape the smoke + test suite, surfaces only in production, and rollback requires git revert rather than a flag flip. Native accepts this risk knowingly when triggering 11B.

## Forward implications

- After Phase 11B, the codebase is simpler: one pipeline, one path.
- All future architecture work assumes the new pipeline as the baseline.
- If a future phase wants to add a new pipeline variant (e.g., a v2 pipeline), it does so behind a new flag — the same dark-mode discipline pattern, on top of the now-canonical baseline.
- The two synthesis surfaces question (TypeScript orchestrator vs Python sidecar `/rag/synthesize`) is unaffected by Phase 11B; that's still an open coordination question.

## How native triggers

**ONLY after Phase 11A is COMPLETE and `npm run cutover:stage1-smoke` returns green ✅:**

> Read EXEC_BRIEF_PHASE_11B_v1_0.md and execute it.

If Phase 11A has not been run, or the smoke is failing, do NOT trigger 11B.

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when all 7 done-criteria pass and native accepts

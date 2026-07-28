---
artifact: CLAUDECODE_BRIEF_SATYA_DIPA
type: CLAUDECODE_BRIEF (governing scope for execution sessions)
version: 1.0
status: READY-FOR-EXECUTION
authored_by: Cowork (Opus planning session), native-commissioned 2026-07-28
authority: >
  Per CLAUDE.md §C item 0. This brief is a POINTER. The operative mission, phases, rails, the
  narrow freeze exception, and acceptance criteria live in
  00_ARCHITECTURE/llm_consumption_audit/briefs/satya_dipa/SATYA_DIPA_BRIEF_v1_0.md.
carries_forward: >
  ŚUDDHA-VĀCA remains **PARTIAL** — 5 of 7 P0 narration lanes fixed, verified and rebuilt; TWO
  pre-authorized lanes still parked on PARISHODHANA PRs #827/#828: `lane:serve-shadbala`
  (registry_bridge.ts — this is why the native's original Ṣaḍbala complaint is fixed in the DATA but
  still NOT VISIBLE to any user) and `lane:ga-tajaka` (L1 Gaṇita, widest blast radius). Both need NO
  new approval — release them the moment those PRs land. See
  00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/ (BRIEF · REPORT · FIX_LEDGER ·
  PHASE_C_AUTHORIZATION). DO NOT let this drop.
commit_warning: >
  A prior version of this pointer was written to disk but never git-committed, and a branch change
  silently reverted it to a superseded campaign. COMMIT THIS FILE AS YOUR FIRST ACT.
mode: >
  FULLY AUTONOMOUS · one Claude Code session · Conductor (Opus) + parallel Sonnet auditors + fix
  builders in .worktrees/satyadipa-* + ONE Opus Verifier that never writes code + ONE Dvārapāla ·
  NO HUMAN GATES · PR + auto-merge only · 10h cap · PRIME RULE: truth over completion.
---

# ACTIVE BRIEF — SATYA-DĪPA (Make `lit` Mean Lit)

**Conductor: read the brief in full, then execute its §2 Phase-0 kickoff.**
→ `00_ARCHITECTURE/llm_consumption_audit/briefs/satya_dipa/SATYA_DIPA_BRIEF_v1_0.md`

The mission in one sentence: the orchestrator marks an asset **`lit`** whenever *any* rows exist,
never checking whether its substep plan finished — so a 78/303 build reports as complete, and because
`runner.py:439` and `staleness.py:77` read `lit` as dependency-satisfied, it **unblocks downstream
assets to build on incomplete data**. Repair the predicate, enumerate and honestly restate every
asset currently lying, remediate what was built on top of them, and sweep the whole build layer for
the same class of unearned success signal.

**The doctrine at stake:** a PASS signal must have a detector behind it that measures the claim it
asserts. Otherwise it is null — not green. This is the fifth confirmed instance of that meta-defect
across three campaigns.

**The trap to avoid:** the rescue being fixed exists for a real reason (D-1.6 — a resumable writer
legitimately reports 0 rows because prior substeps committed; marking it `dormant` poisoned 24
downstream assets). **A fix that trades false-unblocking for false-blocking is not a fix.** The
D-1.6 regression test is a blocking acceptance criterion.

Hard boundaries: ONE narrow freeze exception — the promotion predicate in `asset_runner.py:596–630`
and nothing else in the orchestrator · **`build_substep_progress` is READ-ONLY evidence, never
written** · sealed evaluator harness untouched · no Anthropic model in any production path ·
surgical migrations only · every destructive write snapshot-guarded with a TESTED rollback ·
main via PR + auto-merge only.

Nothing closes without the Verifier. The native wakes to `SATYA_DIPA_REPORT_v1_0.md` answering, in
plain language: **can `lit` be trusted now, how many assets were lying, and what was built on top of
them** — with a four-disposition table and no "passed with caveats".

# ESCALATIONS — Gochara WP0–WP7 autonomous run

Run: branch `l3/gochara-autonomous-wp0-7`, worktree `/Users/Dev/madhav-l3/gochara-wp0-7`.
Executing `KIMI_AUTONOMOUS_EXECUTION_PROMPT_GOCHARA_v1_0.md` against
`GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md` (NATIVE_RATIFIED_PLAN) + `GOCHARA_RULING_SHEET_v1_0.md`.

Each entry: what was hit, why it is out of scope / a stop condition, evidence gathered,
what a human needs to decide.

---

## E-001 — KALA_COST_PROFILE_v1_0.md / KALA_BASELINE_v1_0.md unreachable from this branch (WP1 exit-gate item)

- **What:** Plan §13 and WP1's exit gate require `KALA_COST_PROFILE_v1_0.md` and
  `KALA_BASELINE_v1_0.md` to be reachable from the executing checkout (or their §10 rows
  formally withdrawn). Neither file exists on `main` or on this branch. They exist only on
  the setup worktree branch `l3/kala-setup-phase01` (commits `bb7857b07`, `de2a7f269` —
  `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/`).
- **Why not fixed here:** Landing those files on `main` is another session's delivery
  decision; pulling another branch's artifacts into this run would import unreviewed state.
- **Evidence:** `git log --all -- '**/KALA_COST_PROFILE*' '**/KALA_BASELINE*'` returns only
  the two setup-branch commits above; `ls` of the l3_autonomous directory on this branch
  shows neither file.
- **Decision needed:** Whether the setup session lands those artifacts on `main`, or the
  §10 "Value" row's NOT_RUN-until-present test is formally accepted as the standing state.
- **Effect on this run (per the execution brief's explicit instruction):** WP4 cost
  measurement proceeds using this run's own freshly-produced numbers, on the declared
  synthetic workload, baselined against the family's historically-measured best completed
  run (58.2 min) only as a recorded external figure, never as an assumed content of the
  missing files.

## E-002 — Branch is ahead of the plan's pinned source_revision (drift record, not a blocker)

- **What:** Plan frontmatter pins `source_revision: origin/main c58e86662…`. This worktree's
  HEAD is `fd13ec0a6` (three docs-only commits beyond the pin: 75f0f6a47, b997ee0bd,
  fd13ec0a6 — blueprint/elevation-plan documents). The pin is an ancestor of HEAD
  (`git merge-base --is-ancestor` PASS), and the extra commits touch no source, migration,
  or test file, so every file:line citation in the plan remains valid.
- **Decision needed:** None. Recorded so no future reader mistakes the branch point for a
  content drift.

## E-003 — H-1b out of scope for this run (explicit in the execution brief)

- **What:** H-1b (kakṣyā crossing with no resolvable bindu contributes no activity,
  `completeness_state='unqualified'`) changes served λ values and is gated on N-13/M-7 +
  G-10 (L1 has no per-contributor BAV matrix). The execution brief §5 makes it out of scope:
  design only, do not ship.
- **Decision needed:** Native ruling on N-13's numeric implementation and L1's G-10 closure.
- **Effect on this run:** H-1a ships (provenance only, with the honest no-saturation-change
  statement). H-1b is designed in the WP5 design note and escalated here.

## E-004 — Consumers of the gochara tables/service that plan §6.1 does not name (WP0 re-enumeration)

- **What:** The fresh WP0 consumer re-enumeration (WP0_FINDINGS.md) found ten caller/reference
  edges the plan's §6.1 inventory does not name. The load-bearing ones: the MCP read-only
  proxy whitelist at `platform/src/app/api/mcp/db/query/route.ts:64,71,84` (the serving
  tools' SQL transits it — P-1's provenance/coverage change touches it); two admin SQL UPDATE
  writers on `kala_gochara_windows_v2` (`scripts/kala_admission/w45_post_fit_rebuild.py:262`,
  `restamp_dishonest_staging_calibration.py`); the MR20/23/47 gates and w2g_validations
  reading v1/`'3.0'`/`_v2`; the `gochara_resonance_map` read-side mesh; the still-registered
  v1 sweep writer; docstring-level couplings in `lel/prospective_ledger.ts` and
  `pariprashna/confidence/engine_tier.ts`; registry-seed prose surfaces.
- **Why not fixed here:** the execution brief is explicit — a new undeclared consumer is an
  escalation, not a WP0 fix. None of these are touched by WP0–WP7's in-scope code (they are
  readers or staging-writers outside `may_touch`), but WP7's reader inventory and the P-1
  design packet must account for them, and the cutover runbook (WP10) must extend its
  blast-radius reasoning to items 1–2 in particular.
- **Evidence:** full grep hit lists in WP0_FINDINGS.md (consumer re-enumeration section).
- **Decision needed:** at WP10 authorization time, extend the reader inventory formally and
  decide whether the W41–W45 admission scripts' `_v2` UPDATEs need a staging guard before
  `'4.0'` becomes the registry-pinned target.

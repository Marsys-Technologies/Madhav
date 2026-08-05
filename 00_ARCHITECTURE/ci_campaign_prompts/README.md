# CI Efficiency Campaign — direction record (2026-07-31 → 2026-08-03)

The task briefs that drove the CI campaign and its M-22 continuation, in the order they were
issued. Archived verbatim; contents deliberately unedited, including the instructions that turned
out to be wrong (several were, and the corrections are the useful part).

**These are the direction, not the record.** The authoritative account of what was found, what
changed, and every self-correction is `00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md`, whose §6
runs to sixteen subsections of corrections and cites the reasoning in these files.

Archived rather than deleted because §6 references their premises — several sections read as
"the brief said X; verification showed Y" and are unintelligible without the original X.

## Part 1 — the CI campaign proper (2026-07-31 → 2026-08-01)

The original ten: CI cleanup → ruleset migration → drop-strict → parked items → final two →
TAP-6 M-22 remediation → remaining-open.

## Part 2 — the M-22 continuation (2026-08-01 → 2026-08-03)

Fourteen further briefs, archived 2026-08-06. Every one of them cites the same
`CI_EFFICIENCY_AUDIT_v1_0.md §6` standing rules as Part 1 and continues the same arc, so they
belong in the same direction record rather than a second folder.

- **M-22 demotion → close-out**: `M22_DEMOTION_PROMPT.md`, `M22_DRAIN_AND_PROBE_PROMPT.md`,
  `M22_RULING_EXECUTION_PROMPT.md`, `M22_CLOSEOUT_FINAL_PROMPT.md`, `M22_TAIL_SEQUENCED_PROMPT.md`
- **Autonomous overnight runs**: `M22_AUTONOMOUS_OVERNIGHT_PROMPT.md`,
  `M22_SWARM_OVERNIGHT_PROMPT.md`, plus their two pre-flight setup briefs
  `DATABASE_URL_ENV_CHECK_PROMPT.md` and `M22_LAUNCH_ENV_SETUP_PROMPT.md`
- **Parallel task triple (A/B/C)**: `A_BACKFILL_VERIFY_CONFIRM_PROMPT.md`,
  `B_DEMOTION_392K_PROMPT.md`, `C_VIMSHOTTARI_SECOND_PASS_PROMPT.md`
- **Adjacent verification work**: `TAP6_BLINDSPOT_RECENSUS_PROMPT.md`,
  `VERIFICATION_VOCABULARY_PROMPT.md`

### Provenance note

These fourteen sat uncommitted in the shared main checkout for three to six days, on a branch
(`int-929-final`) that was itself 180 commits behind `origin/main`. They were recovered and
archived from there — which is exactly the failure mode `WORKTREE_ISOLATION_PROTOCOL_v1_0.md` §1
was written to prevent, and which several of these very briefs warn their own executor about
("the local checkout is stale on `parishodhana/dark-corpus-remeasure`; never read it").

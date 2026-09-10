---
artifact: TEST_PLAN_PROMOTION_DECISION
version: 1.0
status: CURRENT — decision record; not itself a test plan or a P2/P3 authorization
date: 2026-08-27
authoritative_side: claude
role: >
  Records the governance decision to promote
  PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md (this folder) from the
  self-paused historical campaign's PROPOSAL artifact to CURRENT status on
  origin/main, and states precisely what that promotion does and does not
  change about campaign authority.
changelog:
  - "1.0 (2026-08-27): initial decision record."
---

# Test plan promotion — decision record

## What was asked

In a Claude Code session on 2026-08-27, the project owner asked whether the
"complete master test plan for Paripraśna" existed. It does:
`PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_0.md`, 605 lines, found only on
the self-paused historical campaign branch
`campaign/pariprashna-assurance-autonomous` (commit `c41d01bf0`), under
`00_ARCHITECTURE/briefs/pariprashna_swarm/` — not present anywhere on
`origin/main`.

That document's own frontmatter marked it `status: PROPOSAL`, dated
2026-08-24, from the campaign that self-paused the same day after hitting its
8-hour ceiling with its P-PORTAL browser battery halted on an access-control
failure. Reporting this back, three specific gaps were named: (1) it lives
only on a historical branch, unreachable from a clean `origin/main` worktree;
(2) its status is PROPOSAL/historical, not currently authoritative; (3) it is
the direct ancestor of the current P2 blocker intake's EDIR-numbered items.

Asked what "resolve them so you have full control of the campaign" meant, the
owner was given three explicit choices and selected: **formally promote it as
the current plan** — i.e., actually adopt this v2.0 test plan into
`origin/main` as the authoritative spec for P3+ work, understanding (as stated
in the choice itself) that this is a real governance decision the handoff
material's own §1.2 says is NOT something reading that handoff authorizes on
its own.

## What this decision does

1. Copies `PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_0.md`'s body
   (§1–§12), byte-for-byte unchanged, into
   `00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md`
   on `origin/main`.
2. Bumps its frontmatter version 2.0 → 2.1 and status PROPOSAL → CURRENT,
   with a changelog entry and a `promotion_note` recording the source commit,
   the authorizing decision, and this record's existence — so the artifact's
   own history is self-describing, not dependent on this file surviving.
3. Establishes this document as the master test plan governing P3 stream
   execution (§4 P-PIPE / §5 P-PORTAL / §6 P-GUIDED / §7–§10 quality,
   accessibility, security, performance / §11 execution order / §12
   deliverables) going forward, superseding the need to reach into the
   quarantined historical worktree to find it.

## What this decision deliberately does NOT do

1. **Does not import the EDIR register.** The companion
   `PARIPRASHNA_EXPERIENCE_DEFECT_AND_IMPROVEMENT_REGISTER_v1_0.md` (7,944
   lines, living/append-only) stays at its historical path. P1's own
   `P1_HISTORICAL_INVENTORY_AND_EVIDENCE_MANIFEST_v1_0.md` already classifies
   it `ACCEPTED_PRIMARY_EVIDENCE` in place, without importing it into the
   Option-B runtime. Copying it here would create a second, divergent copy of
   a still-growing register — precisely the class of failure this project's
   own doctrine calls out (registries must not disagree). The test plan's
   `relates_to` still points to the register at its real location.
2. **Does not authorize P3 dispatch.** The campaign dependency law is
   unchanged: only P0→P1 and P1→P2 are resolved edges; P2→P3 is not. This
   promotion fixes *where the P3 spec lives and what status it holds*, not
   *whether P3 may start*. CG-2 must still close, independently, before any
   stream in this plan's §5.2/§6 runs for credit.
3. **Does not resume the historical autonomous campaign.** No campaign state,
   heartbeat, decision, obligation, or verdict from
   `campaign/pariprashna-assurance-autonomous` is imported or treated as
   current. Only this one static planning document's status changed.
4. **Does not retroactively validate the plan's content.** Promotion changes
   *authority*, not *correctness*. The plan's own proof law
   (STATIC → REPLAY → INTEGRATION → LIVE → NATIVE ACCEPTANCE) still applies to
   every claim inside it; nothing in this record certifies any PPR, gate, or
   finding.

## Provenance

- Source: `campaign/pariprashna-assurance-autonomous` @ `c41d01bf0`,
  `00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_0.md`.
- Target: `origin/main` (this PR), via branch
  `codex/pariprashna-promote-test-plan-v2`, worktree created fresh off
  `origin/main` per the handoff's own repo-session law (§1.3) — not built in
  the shared dirty checkout or on `campaign/nirmana-autonomous`.
- Authorization: explicit, recorded choice by the project owner in a Claude
  Code session, 2026-08-27, made after being told plainly what promotion
  would and would not mean.

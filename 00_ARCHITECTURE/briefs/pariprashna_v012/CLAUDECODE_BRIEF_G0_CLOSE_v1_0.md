---
artifact: CLAUDECODE_BRIEF_G0_CLOSE
type: CLAUDECODE_BRIEF (governing scope for one execution session)
version: 1.1
status: READY — dispatch when the native chooses; docs/registration/git ONLY, zero code
changelog:
  - "1.1 (2026-08-19): NCD-9/10/11 were RULED by the native 2026-08-18 (after v1.0 of
    this brief was authored) — §0 corrected from 'OPEN, carry as open rows' to RULED;
    new step 5a added (log the NCD-10 ND directive); NATIVE_DIRECTIVES added to may_touch."
  - "1.0 (2026-08-18): initial."
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18)
date: 2026-08-18
authority: >
  NCD-1..8 native rulings (2026-08-18) + RED_TEAM_G0_v1_0.md (PASS-WITH-FIXES).
  This brief executes ONLY the G0-close mechanics those authorized. To use as the
  active dispatcher: copy to the project root as CLAUDECODE_BRIEF.md per
  ROOT_FILE_POLICY §2 / CLAUDE.md §C item 0.
may_touch: >
  00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md ·
  00_ARCHITECTURE/PARIPRASHNA_ASBUILT_BASELINE_v1_0.md ·
  00_ARCHITECTURE/PARIPRASHNA_DECISION_REGISTER_v1_0.md ·
  00_ARCHITECTURE/PARIPRASHNA_VERIFICATION_MATRIX_v1_0.md ·
  00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (status flip + changelog row ONLY) ·
  00_ARCHITECTURE/PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md (relates_to annotation ONLY) ·
  00_ARCHITECTURE/CAPABILITY_MANIFEST.json · 00_ARCHITECTURE/CURRENT_STATE_v1_0.md (§2 banner + changelog) ·
  00_ARCHITECTURE/SESSION_LOG.md · 00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md (append the NCD-10 directive ONLY) ·
  00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md (AFTER its dirty state resolves) ·
  00_ARCHITECTURE/briefs/pariprashna_v012/** · CLAUDECODE_BRIEF.md (root — status flip at close) ·
  git (branch/commit/PR for the doc set)
must_not_touch: >
  platform/** · platform-mcp/** · migrations of any kind · any credential/flag/deploy ·
  any file dirty from ANOTHER workstream (verify with git status first) ·
  MACRO_PLAN/PROJECT_ARCHITECTURE/CLAUDE.md/GOVERNANCE_INTEGRITY_PROTOCOL ·
  the sealed pg1/pg2/PB trees
---

# G0 CLOSE — register the decomposition, seal the session record

## §0 — Situation (read first)

The Paripraśna v1.0-RC artifact set is authored, red-teamed, and sitting in
the tree (paths in may_touch). **The NCD series is FULLY RULED (NCD-1..11,
2026-08-18)** — nothing is yours to rule; your job is mechanics. NCD-10's
ruling creates one write obligation for THIS session (step 5a). The working
tree may hold concurrent work (at authoring time: branch `ekv/b-01…`, dirty
CAMPAIGN_COORDINATION.md, uncommitted TA v0.11, untracked SAMPURTI scripts).
**Take stock first; never commit another workstream's files; put this doc
set on its own branch off main.**

## §1 — Ordered steps (each its own commit)

1. **Stock-take + branch.** `git status`; confirm the six Paripraśna files +
   briefs/pariprashna_v012/ (7 files incl. RED_TEAM + this brief) are present
   and unmodified since 2026-08-18 (hashes in §3). Create
   `pariprashna/g0-close` from origin/main; bring ONLY the Paripraśna doc set
   over (the TA v0.11 file + v012 briefs + the four v1.0 artifacts).
2. **Registration.** CAPABILITY_MANIFEST.json: add `PARIPRASHNA_ARCHITECTURE`
   (canonical) + rows for the three LIVING companions. Registry discipline
   per GIP §C.5/§I.3.6 for every file touched.
3. **Status flips.** PARIPRASHNA_ARCHITECTURE_v1_0.md: `status:
   DRAFT_PENDING_REDTEAM → CURRENT` citing RED_TEAM_G0_v1_0 + this session.
   TA v0_1: `status → SUPERSEDED` + replace the "DECOMPOSITION PENDING"
   banner's tail with "superseded at G0 close <date>, session <id>"; append
   the §20 changelog row. NO rename (30+ inbound referrers, incl. code
   comments — inventory of 2026-08-18 in the master review's R-5 note).
4. **Forward pointers.** Design plan frontmatter `relates_to`: annotate that
   the TA is superseded by PARIPRASHNA_ARCHITECTURE for normative content
   (annotate, don't rewrite history). CAMPAIGN_COORDINATION.md: register the
   pariprashna_v012 workstream — ONLY if its dirty state has been resolved by
   its owner; otherwise record the deferral in the session log.
5. **State + log.** CURRENT_STATE §2: one banner (decomposition ratified,
   NCD-1..11 rulings, gate plan adopted, PB-4 re-entry = G5/G7). SESSION_LOG:
   this session's open/close per the templates; run schema_validator +
   drift_detector; exit-code-3 residuals per OHP §F if any.
5a. **NCD-10 directive.** Append to NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md,
   as the next ND number: native-authorized 2026-08-18 — for the NATIVE'S OWN
   chart only, health-crisis/mental-health readings use a self-acknowledged
   interstitial in place of MP §3.5.C's seal + double-red-team + sign-off
   ceremony; cohort subjects always receive the full HS-3 path; folds into
   the next natural MP revision per §3.10.A(d). Cite: Paripraśna Decision
   Register NCD-4 + NCD-10.
6. **PR.** Single PR, doc-only diff, description citing NCD rulings +
   red-team record. Merge per repo convention.

## §2 — Acceptance

All six steps committed; validator + drift green (or residuals booked);
CURRENT_STATE and SESSION_LOG agree; a fresh session reading CLAUDE.md §C →
CURRENT_STATE finds PARIPRASHNA_ARCHITECTURE as the design of record in one
hop. Set THIS brief's status: COMPLETE (and the root copy's, if used).

## §3 — File fingerprints at authoring (verify before flipping anything)

Record sha256 of the four v1.0 artifacts + the two banner-bearing files at
step 1; if any differs from the committed 2026-08-18 versions, STOP and
report — do not merge a drifted artifact.

*End CLAUDECODE_BRIEF_G0_CLOSE v1.0.*

# Review request — Saṅgam algorithm elevation plan v0.4 (third review — after two REWORKs)

You are the independent reviewer (Astra). Your job is to break this plan before the native rules on
it. Agreement is not useful; a finding the author missed is. Judge doctrine as a senior Jyotiṣa
ācārya would and code as an engineer would.

## Ground rules
- **Read-only.** No production code changes, builds, migrations, DB writes, PRs, or edits to the
  plan. The ONE file you may write is your review (path below). **Never overwrite your v0.1 or v0.3
  reviews.** Run the evidence suite only via the in-memory/pipe replay you used before, or note
  that `RUN_ALL.sh` now writes a NEW timestamped file and refuses to overwrite — your call.
- Native priorities, in order: **(1) quality of what the asset delivers, (2) build efficiency,
  (3) the surrounding ecosystem matters as much as the asset.**
- Do not trust the author's summary. Verify every `[C]` at file:line; every `[D]` against the corpus
  (`00_ARCHITECTURE/SOURCE_DATA/classical_texts/`); treat `[J]`/`[P]`/`[U]` as unproven.

## Context for this third review
Your v0.1 review returned REWORK (F-01…F-19, A-01, A-02). Your v0.3 review returned REWORK again
(RR-01…RR-10 plus A.1 re-dispositions). v0.4 §0.1 dispositions every v0.3 finding and names where it
is applied; §0.2 carries the v0.1 dispositions by reference. **First job: check §0.1 row by row —
`APPLIED` / `LISTED_NOT_APPLIED` / `MISAPPLIED`.** Second: the evidence suite was rebuilt per your
RR-01 — every script now asserts a named proposition, exits nonzero on contradiction, and must fail
under `NEG=1`. **Mutation-test it again**: patch a real function in memory and confirm the positive
run fails; run `NEG=1 <python> -B S<n>.py` for every script and confirm nonzero exit. A script whose
verdict survives mutation is still a defect. Check that S3 now tests the REAL producer (your RR-02)
and that S8 states its ephemeris engine (your RR-09). Third: review afresh on B–F.

## Where things are
Worktree `/Users/Dev/madhav-l3/readiness` · branch `l3/kala-elevation-readiness`. **Plan and
evidence are untracked — read from disk.** Python: `/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/venv/bin/python`.

## Read in this order
0. **Your prior reviews** — `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_1.md`
   and `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_3.md`
1. **The plan** — `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ALGORITHM_ELEVATION_PLAN_v0_4.md`
   (v0.1, v0.2, v0.3 are superseded; do not review them)
1a. **The evidence** — `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/evidence_sangam/`:
   `_common.py`, `MANIFEST.txt`, `RUN_ALL.sh`, S1–S13, `OUTPUT_2026-09-22T234243.txt` (SUITE-PASS),
   and the retained failing run `OUTPUT_2026-09-22T234203.txt`. Superseded v1 scripts are in
   `_superseded_v1/` for comparison only.
2. **Its companion** — `…/briefs/SANGAM_ELEVATION_BRIEF_v1_0.md` (v1.2; §7 of the plan lists the
   amendments it now needs)
3. **Source the findings rest on** — as in your prior reviews, plus: `services/ka_sangam/engine.py`
   :696-728 (kernel, for R-6/S11), :210-224, :442-482 (generic currents); `writers/ka_sangam.py`
   :49-114, :667-710 (TRIGGER composition, S13), :1143-1166 (lagna default, S12);
   `ga_writers/ga_strength_writer.py` :1026-1036 (S3); `writers/ka_bhavishya_lekha.py` :98-142
   (real outcome columns, §6.3)
4. **What the plan must fit** — Strategy §2/§3/§5/L3-A15/U02/U07; JUNE §4.5/§4.6/§6; CONTEXT §1/§6/§7;
   root `CLAUDE.md` §B.10/§N.5/§N.7/§N.8.

## What I need from you
**A. Claims.** (i) Every §0.1 row: `APPLIED` / `LISTED_NOT_APPLIED` / `MISAPPLIED`, with the section
checked. (ii) Every `[C]` in §1 and every §1b row (incl. new 17–18 and re-graded 2/5/6/8/11/13).
(iii) The suite: per-script mutation result; whether the runner can be made to report SUITE-PASS
falsely.

**B. R-1…R-6 and E1–E6.** `AGREE` / `AMEND` / `REJECT`, why, and your alternative. Push hardest on:
 - **R-6 / M-7** — is separating activity · valence · applicability · availability the right
   correction to a kernel that zeroes adverse activity, or is there a classical reason dignity
   *should* gate? What must the legacy/new coexistence rule be?
 - **E1** — does "same geometry, two labelled evaluations, one root" correctly resolve your A.3
   MISAPPLIED, or does it still smuggle a Western angle list in as the common definition?
 - **E2** — is a producer-side completeness receipt the right fix for `[0]*12`, and is the frame now
   correctly treated as settled?
 - **E5** — is "occupancy = union of child intervals" plus an explicit aggregation unit sufficient
   for `ka_taranga`, or does the mean-per-row problem need a different fix?
 - **E6** — do the two outcome axes (observation × derivation) now represent your RR-07 correctly?
 - **§6.3** — can the id-keyed manifest with the seven attacks actually prove historical integrity?

**C. What the author missed** — anything with higher leverage than what is here; anything in §1
still bypassing the audit.

**D. Sequencing / P4 / lineage.** Is §4 now correct, esp. R-5-in-harness before contact changes?
Does §6.2's per-E accounting satisfy "reduced caps cannot pass as equivalent"?

**E. Ecosystem.** Does §6.2 correctly adopt your 7×6 matrix and your `priority.ts` correction? Any
consumer whose SQL breaks that the plan still doesn't name?

**F. Verdict.** `PROCEED` / `PROCEED_WITH_AMENDMENTS` / `REWORK` — and, separately: can M-1/M-1a,
M-2, M-3 now go to the native as a decision packet (you said they could once fixture facts were
corrected), and does M-7 belong with them?

## Output
Write exactly one file (a NEW file — never overwrite your v0.1 or v0.3 reviews):
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_4.md`
with YAML frontmatter (`artifact: ASTRA_REVIEW_SANGAM_ALGO_PLAN`, `version: "0.4"`, `reviews: v0.4`,
`prior_verdicts: [REWORK, REWORK]`, `status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW`,
`reviewer: "Codex gpt-6-astra — independent adversarial review"`, `date`, `verdict`,
`reviewed_plan_sha256` (compute it), `authority: "Review only; authorizes nothing."`) followed by
sections A–F. Every finding cites file:line, a verse, or a command you ran. Mark anything you could
not verify `UNVERIFIABLE` — never a plausible default.

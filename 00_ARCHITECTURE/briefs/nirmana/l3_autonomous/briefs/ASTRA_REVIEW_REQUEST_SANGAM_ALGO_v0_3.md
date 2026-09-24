---
title: "ASTRA_REVIEW_REQUEST_SANGAM_ALGO_v0_3"
version: "0.3"
status: SUPERSEDED
role: review_request
owner: "L3 Saṅgam design session (madhav-d9)"
layer: L3
asset: ka_sangam
description: "Author-written packet for the v0.3 Astra review; superseded by v0_4."
frontmatter_added: "2026-09-23 — prepended for governance-gate parity (madhav-fc G18 finding: briefs tree is outside the frontmatter gate); body byte-identical to the prior commit"
---

# Review request — Saṅgam algorithm elevation plan v0.3 (re-review after REWORK)

You are the independent reviewer (Astra). Your job is to break this plan before the native rules on
it. Agreement is not useful; a finding the author missed is. You are reviewing **astrological method**
as much as code — judge the doctrine claims as a senior Jyotiṣa ācārya would, and the code claims as
an engineer would.

## Ground rules
- **Read-only.** No production code changes, no builds, no migrations, no database writes, no PRs,
  no edits to the plan. The ONE file you may write is your review (path below).
- The native's priorities, in order: **(1) quality of what the asset delivers, (2) build
  efficiency, (3) the surrounding ecosystem matters as much as the asset.**
- Do not trust the author's summary. Open the cited source. Treat every `[J]`, `[P]` and `[U]` tag
  as unproven; verify every `[C]` at the cited `file:line`; check every `[D]` against the classical
  text (the repo has a classical-texts corpus under `platform/` — search it; if you cannot reach it,
  say so and judge from your own knowledge, labelled as such).
- Where the plan proposes a *method* (E1 dṛṣṭi model, E3 fast tier, E4 gates), ask whether a
  competent ācārya would recognise it, whether it is the *strongest* classical form of the idea,
  and whether the author is smuggling in doctrine or a Western assumption anywhere.

## Where things are
Worktree `/Users/Dev/madhav-l3/readiness` · branch `l3/kala-elevation-readiness`. **The plan is
untracked — read it from disk.** Python code under `platform/python-sidecar/`. The Saṅgam code on
this branch is byte-identical to `origin/main`.

## Context for this re-review
Your v0.1 review (`ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_1.md`) returned REWORK with F-01…F-19, A-01, A-02.
v0.3 claims to disposition every one (§0 ledger) and to locate where each is applied (§0.1). **Your
first job is to check that claim, finding by finding** — a disposition that is listed but not
actually applied in the named section is a defect. Then re-run `evidence_sangam/RUN_ALL.sh` and
attack the scripts: a falsifier that cannot fail, or whose fixture does not test what its row
claims, is a defect. Then review the plan afresh on B–F as before.

## Read in this order
0. **Your prior review** — `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_1.md`
1. **The plan** — `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ALGORITHM_ELEVATION_PLAN_v0_3.md`
   (v0.1 and v0.2 are superseded; do not review them)
1a. **The evidence** — `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/evidence_sangam/` S1–S10, `RUN_ALL.sh`,
   `OUTPUT_2026-09-22.txt`. Re-run: `cd <that dir> && ./RUN_ALL.sh` (read-only; Swiss Ephemeris via the venv python)
2. **Its companion** (the output-contract brief the plan assumes) —
   `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ELEVATION_BRIEF_v1_0.md` (§2.4 June audit, §4.2 target state, §5.2 cascade)
3. **The source the findings rest on** —
   - `platform/python-sidecar/services/ka_sangam/engine.py` :44-52, :103-140, :168, :213, :467, :696-729, :731-760, :850-889, :946-1015, :1087, :1113-1150, :1171, :1668-1760
   - `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` :274-305, :343-360, :591, :721-737, :908, :965, :989, :991-1024
   - `platform/python-sidecar/pipeline/transit_search.py` (the `find_aspect_events` contract — read-only; the plan says it must not be edited)
4. **What the plan must fit** —
   - `00_ARCHITECTURE/CONDUCTOR/cleanup/L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md` §4.5, §4.6, §6 (native rulings 2026-06-22)
   - `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §2, §3, §5 (P4 + benchmark contract), §6.1 row L3-A15, L3-U02, L3-U07
   - `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md` §1 (no confidence scalar), §6, §7
   - root `CLAUDE.md` §B.10, §N.5, §N.7, §N.8
5. **L1 facts the plan leans on** — confirm they exist and in what frame:
   `chart_facts` `ashtakavarga_bindu` rows (`<GRAHA>-HOUSE_<N>` — rāśi or bhāva?), `chart_divisionals`,
   the daśā-lord capability computation behind `ganita_dasha_lord_capability_get`, and `sandhi_flag`
   on L1 clock intervals. Grep the `ga_*` writers under `platform/python-sidecar/`.

## What I need from you
**A. Claims.** First: for every row of §0.1, `APPLIED` / `LISTED_NOT_APPLIED` / `MISAPPLIED`, with the section you checked. Then for every `[C]` line in plan §1 and every §1b row: `CONFIRMED` / `REFUTED` / `PARTLY`, with file:line.
For every `[D]`/`[P]`: is the doctrine stated correctly, and is the source right? Name the verse
or chapter where you can.

**B. The six elevations, E1–E6.** For each: `AGREE` / `AMEND` / `REJECT`, why, and your
alternative. Push hardest on:
 - **E1** — is "interval from sign-dṛṣṭi, peak from degree pass" the right synthesis, or does it
   keep a Western artefact alive? Should Jaimini rāśi-dṛṣṭi be in scope? Is dropping 60°/90° a
   loss of *any* legitimate signal (e.g. Tājika aspects, which the C12 current already admits)?
 - **E2** — is BAV ≥4 / ≤3 the right threshold, and is kakṣyā worth the L0 dependency? Is the
   frame question really L1's to answer?
 - **E3** — does a bounded inside-window Moon tier honour or breach the June "slow only" ruling?
   Is the `⌈days/27.3⌉+1` bound correct? Is tāra bala the right fast-tier witness, or Sarvatobhadra?
 - **E4** — is treating sandhi/capability/varga as *applicability gates* (rather than score
   terms) the correct epistemics? Is the sandhi doctrine textually strong enough to gate on?
 - **E5** — should the retrograde pass be the default peak?
 - **E6** — is measured rarity as defined actually a base rate, or another formula?

**C. What the author missed.** Which classical timing techniques with *higher* predictive leverage
than these six are absent? Candidates to consider and rule in or out: Chara/Jaimini daśās as
confirmation; Yogini daśā; Kālacakra; Tājika varṣa-praveśa (C12 exists — is it used well?);
Sudarśana cakra; Praśna cross-check; argalā; the *bhāva-madhya* question (whole-sign vs cusp);
Rāhu/Ketu transits (absent from `_AV_SCAN_PLANETS`).

**D. Sequencing and P4.** Is §4's order right? Does any E violate "reduced caps cannot pass as
equivalent"? Does any E add a witness without declaring its lineage?

**E. The ecosystem.** Which of the seven consumers (`ka_kalasutra`, `ka_vighnakara`,
`ka_kala_darshana`, `ka_taranga`, `ka_jivana_parva`, `ka_bhavishya_lekha`, `ka_tulana`) breaks,
changes meaning, or silently improves under each E? Which served capability
(`query_convergence_windows.ts`, `kala_views/*`) would show a user something different?

**F. Verdict.** `PROCEED` / `PROCEED_WITH_AMENDMENTS` / `REWORK` — and, separately, whether the plan is fit to put to the native for rulings M-1…M-6 now, and the three changes that would
most raise the plan's value in the native's priority order.

## Output
Write exactly one file (a NEW file — never overwrite your v0.1 review):
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_3.md`
with YAML frontmatter (`artifact: ASTRA_REVIEW_SANGAM_ALGO_PLAN`, `version: "0.3"`,
`status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW`, `reviewer: "Codex gpt-6-astra — independent
adversarial review"`, `date`, `verdict`, `reviewed_plan_sha256` (compute it), `authority: "Review
only; authorizes nothing."`) followed by sections A–F. Every finding cites file:line, a verse, or a
command you ran. Mark anything you could not verify `UNVERIFIABLE` — never a plausible default.

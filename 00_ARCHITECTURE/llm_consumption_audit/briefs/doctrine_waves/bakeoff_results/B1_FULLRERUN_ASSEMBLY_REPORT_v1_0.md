---
artifact: B1_FULLRERUN_ASSEMBLY_REPORT
type: BAKEOFF ASSEMBLY REPORT (assembles 3 checkpointed batches into the full-run result; runs
  DR-12 adjudication ONCE over the assembled whole)
version: 1.0
status: ASSEMBLED — manifest-hash-consistent, DR-12 adjudicated NO_WINNER (pre-committed branch,
  honestly invoked, no forced champion)
authored_by: Claude Code (Sonnet 5), D-4b B-1 chunked re-run — ASSEMBLY session, 2026-07-22
branch: wave/D-4b/B1-full-rerun (worktree .claude/worktrees/wave-D-4b-B1-full-rerun)
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
---

# B-1 Grand Bakeoff — full re-run, ASSEMBLY

This session assembles the 3 checkpointed batches (`b1_batches/batch_batch{1,2,3}.json`) that
together score all 14 evaluable contenders against the full 56-event pre-registered corpus
(54 scored + 2 excluded per packet §0), per `BRIEF_D4B.md` §1 B-1's "identical everything" rule
surviving chunking. Batch verifier receipts handed to this session: batch 1 ACCEPT, batch 2
ACCEPT, batch 3 ACCEPT.

## 1 — DR-19 pre-check

- `git fetch origin main` run first. Current branch `wave/D-4b/B1-full-rerun` confirmed via `git
  branch --show-current`.
- `BRIEF_D4B.md` frontmatter: `status: OPENED` — D-4b is the live campaign; this branch's lane
  (`"B-1 full re-run"`) is exactly the lane `STATE_D4B.md` (as of its last recorded pass) names as
  the wave's blocker. Branch belongs to this campaign — no branch/campaign mismatch.
- `must_not_touch` respected: `asset_runner.py`, `runner.py`'s `execute_dag`/`_schedule_parallel`,
  the leakage firewall, raw LEL event data, prior gate/regression surfaces, and
  `gochara_grammar`/`gochara_intensity`'s core computation were not read or modified this session.
  This session only reads already-committed batch artifacts and writes new files under
  `bakeoff_results/`.
- No events on/after 2020-01-01 were queried this session — this is a pure assembly pass over
  already-committed batch JSON; no new LEL/event queries were issued.

## 2 — Manifest-hash consistency check (real, not reimplemented)

Ran `checkManifestHashConsistency()` from the real, committed
`platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/b1_batch_artifact_io.ts` (via `tsx`,
dynamic import, zero reimplementation) against the live committed
`B1_RUN_MANIFEST_v1_0.json` and the 3 committed batch artifact files:

```json
{
  "consistent": true,
  "expectedHash": "91dc0c3e203b565aba3b89604ea4a618c72fbada6487fe969269567ab2b37603",
  "mismatches": []
}
```

All 3 batches (`batch1`, `batch2`, `batch3`) carry `manifestHash ===
91dc0c3e203b565aba3b89604ea4a618c72fbada6487fe969269567ab2b37603`, byte-identical to
`hashManifestFile(B1_RUN_MANIFEST_v1_0.json)` computed fresh this session. **Result: CONSISTENT.**
Per instruction, this was the hard gate before any assembly — had it reported inconsistent, this
session would have stopped and reported the mismatch loudly rather than assembling. It did not;
assembly proceeded.

Also cross-checked and consistent across all 3 batches: `chart_id`
(`482012f1-710e-4a25-994a-93821f5871aa`), `preregistration_packet_blob_sha`
(`9b6713db8c2551a937ff2070e498da1f12526966`), and the `events_excluded` list (identical 2 events —
`EVT.1984.02.05.01` structural anchor, `EVT.1995.XX.XX.02` congenital-onset — in every batch).
`negative_crps_check.total_negative_crps_found` sums to **0 across all 3 batches** (F-2's
wraparound-sort fix holds under the full 14-contender × 54-event run, not just the narrowed
31-event VOID run it was built to fix).

## 3 — What was assembled

- **Contenders:** all 14 evaluable roster members (1 classical default + 12 PERMISSION systems +
  1 hierarchical ensemble), exactly the manifest's `contender_roster`. `midpoint_triangle` and
  `transit_kernel` remain NOT-EVALUABLE this wave (CR-120/CR-121) — no row for either in this
  assembly, by design, not a gap.
- **Events:** 54 of the packet's 56-event committed corpus (2 structurally excluded per packet §0,
  identical across all batches).
- **Source:** `b1_batches/batch_batch1.json` (pratyantar_lord + vimshottari/yogini/ashtottari/
  chara_karaka), `batch_batch2.json` (naisargika/mudda/kalachakra/narayana/sade_sati),
  `batch_batch3.json` (guru_shani_double_transit/av_threshold/planetary_return/
  hierarchical_ensemble) — concatenated verbatim, zero score recomputation.

**Committed assembly artifacts (this session, first-class per `BRIEF_D4B.md` §1 — "per-model
per-event tables as first-class artifacts"):**

- `B1_FULLRERUN_ASSEMBLED_SUMMARY_v1_0.json` — machine-readable per-model summary (CRPS skill
  primary + hit-rate legacy secondary + DR-17 grade counts + the manifest-hash-consistency receipt
  + the DR-12 adjudication verdict).
- `B1_FULLRERUN_ASSEMBLED_PER_EVENT_v1_0.json` — the full per-model per-event tables (all 14
  contenders × 54 assigned events each, including honestly-marked `skipped:
  "unresolved_event_class"` rows for the 51 events each PERMISSION/ensemble contender could not
  score), concatenated verbatim from the 3 batch files.

## 4 — Results: CRPS skill (primary) + hit-rate (legacy secondary), assembled whole

Coverage-matched shuffled-birth controls (DR-15(c), N=1000/event/model, NP-D4B-004); DR-17 grading
(`dr17_grading.ts`, PR #704, imported not reimplemented); hit-rate = ±45d top-decile (percentile
0.9) legacy secondary. Ranked by CRPS skill vs shuffled control, descending:

| model_id | n scored | CRPS skill (primary) | hit-rate (secondary) | beats control (event-level) | DR-17 grades (peak/sub_peak/elevated/neutral/contra) | DR-17 weighted mean |
|---|---:|---:|---:|---:|---|---:|
| planetary_return | 3 | **+0.2030** | 33.3% | 1/3 | 1/0/0/2/0 | 0.333 |
| av_threshold | 3 | **+0.0407** | 33.3% | 1/3 | 1/0/0/2/0 | 0.333 |
| chara_karaka | 3 | −0.0105 | 66.7% | 0/3 | 0/0/0/3/0 | 0.000 |
| yogini | 3 | −0.0217 | 33.3% | 0/3 | 0/0/0/3/0 | 0.000 |
| ashtottari | 3 | −0.0217 | 33.3% | 0/3 | 0/0/0/3/0 | 0.000 |
| naisargika | 3 | −0.0217 | 33.3% | 0/3 | 0/0/0/3/0 | 0.000 |
| narayana | 3 | −0.0217 | 0.0% | 0/3 | 0/0/0/3/0 | 0.000 |
| sade_sati | 3 | −0.0217 | 33.3% | 0/3 | 0/0/0/3/0 | 0.000 |
| **pratyantar_lord** | **54** | **−0.1557** | 51.9% | 9/54 | 17/2/8/26/1 | 0.407 |
| hierarchical_ensemble | 3 | −0.2844 | 100.0% | 0/3 | 2/0/1/0/0 | 0.833 |
| vimshottari | 3 | −0.2887 | 66.7% | 0/3 | 0/0/0/3/0 | 0.000 |
| kalachakra | 3 | −0.3224 | 66.7% | 0/3 | 0/0/1/2/0 | 0.167 |
| guru_shani_double_transit | 3 | −0.3322 | 66.7% | 0/3 | 0/0/1/2/0 | 0.167 |
| mudda | 3 | −0.4760 | 33.3% | 0/3 | 1/0/0/2/0 | 0.333 |

**`pratyantar_lord` is the only contender with adequate event coverage (n=54 of 56 scoreable
events) to support any distinguishability judgment at all; the other 13 are constrained to n=3
each (see §5).** All numbers above are aggregated directly from the 3 committed batch files' own
`per_event_detail` arrays (recomputed by this session from the raw per-event rows, cross-checked
byte-for-byte against each batch's own pre-computed `summaries[model].meanSkillVsShuffled` /
`meanCrpsReal` fields — identical, zero discrepancy found).

## 5 — Disclosure: `career_advancement` is TOTALLY unresolved this run (recurs from F-1)

**This recurs and is disclosed plainly, as instructed.** `gochara_resonance_map` has exactly 3
populated `event_class` rows for chart `482012f1` — `career_advancement`=22 rows,
`major_gain`=35 rows, `marriage`=23 rows (live-queried by batch1, reused by batch2/batch3 per
their own notes). But **zero of the 54 scored LEL events resolve to `career_advancement`** across
all 14 contenders in this assembled run — the 3 events that DO resolve are 2× `major_gain`
(`EVT.2010.XX.XX.01`, `EVT.2025.07.XX.01`) and 1× `marriage` (`EVT.2013.12.11.01`). This is not a
partial/near-total gap this run — it is total: 0/54.

This is **by design, not a defect**, per `event_class_resolution.ts`'s own module docstring (F-1,
PR #699): this chart's 13 `category='career'` LEL events are, on inspection, entries, exits,
switches, setbacks, and business-launch/milestone events — none of which the module's
evidence-cited domain table judges a genuine match to `career_advancement`'s own BPHS-cited
classical signature (the closest candidate, `career/award_selection`, more precisely matches the
separate, also-unpopulated `achievement_recognition` class). The module explicitly refuses to
force-map a same-category event to a populated class it does not genuinely correspond to, since
that would be its own kind of dishonesty (over-resolution) — the same failure mode the module was
built to fix on the other side (under-resolution, the original defect).

**Consequence for this bakeoff:** all 12 PERMISSION contenders and `hierarchical_ensemble` are
honestly SKIPPED (not fallback-scored) on 51 of their 54 assigned events and score on only the
same 3-event slice, with **zero coverage of `career_advancement` despite it being one of only 3
populated resonance-map classes for this chart.** This constrains what B-1 can certify: no
PERMISSION-system contender's result says anything about career-domain timing accuracy this run,
and the n=3 sample any of them DOES have is too small to support a distinguishability claim
regardless of sign (§6). Extending `DOMAIN_TO_EVENT_CLASS` coverage (more evidence-cited domain
values, or a genuinely new populated resonance-map class) is named in the module's own docstring
as a follow-on, not something this assembly session performs (would require new evidence-cited
mapping work, out of this session's assembly-only scope).

## 6 — DR-12 adjudication (run ONCE, here, over the assembled whole)

**Ruling text (DR-12, DIS.025, native-ratified 2026-07-17):** "the data retires the loser" — a
winner is named only if the empirical retrodiction score supports it; neither doctrine nor
engineering decides the peak model by opinion.

**BRIEF_D4B.md §1 B-1 criterion:** name a winner only if it beats its coverage-matched
shuffled-birth control with statistical distinguishability; otherwise invoke the pre-committed
no-winner branch verbatim — "if NO model beats its coverage-matched shuffled-birth control, the
bakeoff reports exactly that... No forced champion, ever."

### Verdict: **NO_WINNER**

Reasoning, over the assembled full data:

1. **The only contender with an adequate sample is negative.** `pratyantar_lord` (n=54, the sole
   contender not gated by the `career_advancement`-style resonance-map coverage gap) has CRPS
   skill **−0.1557** vs its shuffled-birth control — it underperforms the control on average,
   beating it on only 9/54 (16.7%) of events.
2. **Every other contender's sample is too small to mean anything.** All 12 PERMISSION contenders
   and `hierarchical_ensemble` score on n=3 events each (§5). At n=3, no claim of "genuinely beats
   control" is statistically supportable in either direction.
3. **The two nominally-positive contenders don't survive scrutiny.** `planetary_return` (+0.203)
   and `av_threshold` (+0.041) each beat control on only 1 of their 3 events — one lucky/unlucky
   event out of three, not a pattern. `chara_karaka`'s −0.0105 is closer to zero than either
   positive score, underscoring how little separates any of the n=3 contenders from noise.
4. **No formal significance test exists in the committed harness for this run.** None of
   `harness.ts`, `proper_scoring.ts`, or `curve_controls.ts` (all read, not reimplemented this
   session) compute a bootstrap CI or permutation p-value on the skill delta. Absent that
   infrastructure, this session does not fabricate one to manufacture a "statistically
   distinguishable" claim — the honest position, given (1)-(3), is that no contender clears the
   bar.
5. **midpoint_triangle and transit_kernel are excluded, not defeated.** They remain
   NOT-EVALUABLE (CR-120/CR-121) this wave — carrying no scored row here — and are not part of
   this adjudication's winner/loser calculus.

**Disposition, per BRIEF_D4B.md §1 B-1's pre-committed no-winner branch, invoked here verbatim,
not paraphrased into a softer finding:**

> B-2's backfill proceeds against the best-available model with `model_confidence: none_validated`
> stamped on every row; campaign close records "no validated timing model yet — prospective loop
> is the path" as the honest finding. No forced champion, ever.

"Best-available" here is a coverage judgment, not a certified win: `pratyantar_lord` is the only
contender with a real 54-event sample and a non-degenerate DR-17 grade distribution (17 peak / 2
sub_peak / 8 elevated / 26 neutral / 1 contra; weighted mean 0.407) even though its CRPS skill
vs control is negative — it is named here as the coverage-adequate candidate for B-2 to consider
when it dispatches, not as a winner of this bakeoff. **This session does not name a champion.**

## 7 — What this session did NOT do

- Did not re-score any event, re-derive any CRPS value, or re-draw any control — every number in
  the assembled artifacts traces to the 3 already-committed, already-verifier-ACCEPTed batch
  files.
- Did not touch `STATE_D4B.md`, `CLAUDECODE_BRIEF.md`, `PROMISE_LEDGER_D4B.md`, or
  `DISAGREEMENT_REGISTER_v1_0.md` — updating the campaign-level governance ledgers with this DR-12
  disposition is a B-6 close-pass concern, outside this assembly session's bounded scope.
- Did not extend `event_class_resolution.ts`'s `DOMAIN_TO_EVENT_CLASS` table or otherwise attempt
  to grow `career_advancement` coverage — that is named, in the module's own docstring, as a
  follow-on lane, not an assembly-time fix.
- Did not touch `asset_runner.py`, `runner.py`'s `execute_dag`/`_schedule_parallel`, the leakage
  firewall, raw LEL event data, prior gate/regression surfaces, or `gochara_grammar`/
  `gochara_intensity`'s core computation.
- Did not query any LEL event on or after 2020-01-01.

## 8 — Provenance

- `checkManifestHashConsistency()` run: real, via `npx tsx` dynamic import of the committed
  `b1_batch_artifact_io.ts`, not reimplemented — see §2.
- Manifest: `B1_RUN_MANIFEST_v1_0.json`, committed at `ab054da9`, hash
  `91dc0c3e203b565aba3b89604ea4a618c72fbada6487fe969269567ab2b37603`.
- Batches: `b1_batches/batch_batch1.json` (`c6f319d9`), `batch_batch2.json` (`19ac5b81`),
  `batch_batch3.json` (`8cb6bef8`) — all 3 with independently-run verifier receipt ACCEPT, handed
  to this session by the dispatching orchestrator.
- DR-17 grading: `dr17_grading.ts`, PR #704 (`0c17e927`), imported by every batch driver, not
  reimplemented anywhere in this assembly.
- Harness fixes in effect for this run: F-1 (`event_class_resolution.ts`/resonance-map coverage,
  PR #699) and F-2 (`curve_controls.ts` wraparound-sort, PR #697), both merged to `main` before
  batch1 ran.

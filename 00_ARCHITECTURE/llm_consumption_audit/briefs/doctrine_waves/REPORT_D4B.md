---
artifact: REPORT_D4B
type: WAVE CLOSE REPORT (protocol §7 — "the D-1 lesson: a wave without a close report did not
  close") — B-6 REAL CLOSE PASS #4, mode=GATED (explicitly NOT a full campaign close)
wave: D-4b — Calibration Ignition + Grand Bakeoff (campaign close lane B-6)
status: OPEN — GATED. Headline: the wave still does NOT close this pass. B-1's full re-run is now
  COMPLETE — assembled, manifest-hash-consistent, DR-12 discharged NO_WINNER — but it has never
  been opened as a pull request, reviewed, or merged to `main`. It exists only on the pushed
  branch `wave/D-4b/B1-full-rerun` (origin, commit `0aa69c06`). `b1.merged = false`, independently
  reproduced this pass (`gh pr list` returns empty for that branch, all states). B-2/B-3 remain
  correctly SKIPPED (hard-gated on a merged adjudication receipt that does not yet exist). This
  report is the fourth B-6 close attempt and SUPERSEDES the version merged via PR #703
  (`wave/D-4b/B6-real-close`) — that version, and PR #695's version before it, are preserved in
  git history, not deleted; this file replaces them going forward as the current record.
opened: 2026-07-21 (formal open, PR #686)
supersedes: REPORT_D4B.md as merged by PR #703 (2026-07-22T13:57:10Z, `wave/D-4b/B6-real-close`),
  which itself superseded REPORT_D4B.md as merged by PR #695 (2026-07-21T23:34:17Z,
  `wave/D-4b/B6-close`). Both preserved in git history at their own merge commits.
this_pass: 2026-07-22, wave/D-4b/B6-real-close-3, mode=GATED (orchestrator-specified)
conductor: Claude Code (Sonnet 5), B-6 REAL close pass #4
governing: BRIEF_D4B.md v1.0, CONDUCTOR_PROTOCOL.md, ESCALATION_POLICY_v1_0.md,
  ADJUDICATOR_CHARGE_v1_0.md
---

# REPORT_D4B — D-4b Wave, B-6 REAL Close Pass #4 (GATED)

## §0 — Headline (read this first)

**The D-4b wave is still NOT closing this pass.** `CLAUDECODE_BRIEF.md`'s `current_wave` remains
`D-4b (OPEN)` — it is NOT set to `CAMPAIGN-CLOSED`.

**What changed since the PR #703 GATED pass:** B-1's full re-run — which the PR #703 pass found
did not exist beyond an uncommitted scaffold — has since been **completed and pushed to origin**,
but **never opened as a pull request**. Independently re-verified this pass, not taken on the
dispatching session's word:

1. **The run is real and complete.** `wave/D-4b/B1-full-rerun` (origin, commit `0aa69c06`) carries
   six new commits since the PR #703 pass: a manifest commit (`ab054da9`), the checkpointed-
   batching artifact-I/O harness (`fc6ead96`, CR-122), three batch-driver commits scoring the
   14-contender roster in three chunks (`c6f319d9`, `19ac5b81`, `8cb6bef8`), and an ASSEMBLY commit
   (`0aa69c06`) that concatenates the three batches and discharges DR-12.
2. **Manifest-hash consistency independently re-confirmed, not just cited.** This pass imported
   (not reimplemented) `checkManifestHashConsistency()`/`hashManifestFile()` from the real,
   committed `platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/b1_batch_artifact_io.ts`
   (commit `fc6ead96`) and ran it fresh against the live committed manifest and all three batch
   files:
   ```
   manifest hash (fresh): 91dc0c3e203b565aba3b89604ea4a618c72fbada6487fe969269567ab2b37603
   { "consistent": true, "expectedHash": "91dc0c3e203b565aba3b89604ea4a618c72fbada6487fe969269567ab2b37603", "mismatches": [] }
   ```
   Byte-identical to the ASSEMBLY_REPORT's own cited hash. The temporary verification script was
   deleted after use; it wrote nothing to any committed artifact.
3. **DR-12 was discharged NO_WINNER, honestly, per the pre-committed branch.**
   `B1_FULLRERUN_ASSEMBLED_SUMMARY_v1_0.json`'s `verdict` field reads `"NO_WINNER"` (re-read live
   this pass). `pratyantar_lord` — the only contender with an adequate sample (n=54 of 56 scoreable
   events; every PERMISSION contender and the ensemble are gated to n=3 by the `career_advancement`
   resonance-map coverage gap, §5 of the ASSEMBLY_REPORT, itself a recurrence of F-1's disclosed
   design limit, not a new defect) — scored **CRPS skill −0.1557** vs its shuffled-birth control
   (underperforms; beats control on only 9/54 events). No contender with a meaningful sample beats
   its control. Per `BRIEF_D4B.md` §1 B-1's pre-committed no-winner branch, invoked verbatim by the
   ASSEMBLY_REPORT: *"B-2's backfill proceeds against the best-available model with
   `model_confidence: none_validated` stamped on every row; campaign close records 'no validated
   timing model yet — prospective loop is the path' as the honest finding. No forced champion,
   ever."* No champion is named anywhere in the assembled artifacts.
4. **But none of it is merged.** `gh pr list --repo amonty84/madhav --head wave/D-4b/B1-full-rerun
   --state all` → **empty**. No PR — open, merged, or closed — has ever existed for this branch.
   The branch is pushed to `origin` (confirmed: local worktree HEAD and
   `origin/wave/D-4b/B1-full-rerun` both resolve to `0aa69c06`, identical), but has not entered
   review, has not been verified by a fresh-context Opus verifier at the ASSEMBLY level (only the
   three underlying batches carry individually-reported verifier ACCEPT receipts — the ASSEMBLY
   commit's own concatenation + DR-12 discharge step has no independent verifier pass cited in its
   own report), and has not touched `main`.

**The exact blocker, named plainly: B-1's real work is done, but it has never been merged.** Per
this session's own dispatch terms, reproduced independently this pass: **`b1={"merged": false}`;
`b2={"skipped": true}`; `b3={"skipped": true}`**. This is precisely the condition this session's own
ground rules name as forcing GATED rather than FULL: *"a genuinely-merged B-1 with red/no-winner
still allows FULL close — only an actual merge failure forces GATED."* B-1's no-winner verdict is
real and honest, but it has not been merged, so it cannot yet be the campaign's certified record.
This report does not fabricate a merge, does not treat a pushed-but-unreviewed branch as
equivalent to a merged receipt, and does not advance B-2/B-3 against an unmerged result.

**Next action for the wave to close** (narrower again than the PR #703 pass's, now that the run
itself exists): (a) open a PR for `wave/D-4b/B1-full-rerun` against `main`; (b) route it through an
independent fresh-context verifier — at minimum re-checking the ASSEMBLY step itself (the three
batches already carry individual ACCEPT receipts, but the concatenation + DR-12 discharge step does
not yet have its own independent verification on record); (c) merge it, making the NO_WINNER
adjudication the campaign's certified record and formally discharging DR-12 (currently
`DISAGREEMENT_REGISTER_v1_0.md` DIS.025 still reads "RATIFIED but NOT YET DISCHARGED" — stale as of
this pass, since the discharge exists but is not yet merged); (d) THEN B-2/B-3 dispatch against that
real, merged receipt with `model_confidence: none_validated` per the no-winner branch; (e) a future
B-6 pass runs the mode=FULL three-point baseline diff, which no pass to date — #695, #703, or this
one — has run.

## §1 — What actually ran this REAL close pass #4 (B-6's own scope, mode=GATED)

Per this session's dispatch: verify the full campaign state independently, write the honest GATED
status with the exact blocker named, and produce four artifacts — this report, `STATE_D4B.md`, a
`NATIVE_PROXY_LEDGER_D4B.md` compiled-summary addendum, and a `PROMISE_LEDGER_D4B.md` v4.0
cross-check. Per mode=GATED, the mode=FULL items (parked-items review against every D-1→D-5 PARK
class, full DR ratification sweep, full register sweep, master-regression-suite wiring
confirmation, three-point baseline diff, standing-live-loop declaration, `CLAUDECODE_BRIEF.md`
`current_wave` → `CAMPAIGN-CLOSED`) are explicitly NOT actioned this pass — named here as still
open, not silently dropped, matching the discipline of both predecessor passes.

### 1a — DR-19 pre-check, performed first

`git fetch origin main` run first, before any substantive work. This session's working directory
was pinned by its host harness to a pre-existing, *different* worktree
(`.claude/worktrees/wave-D-4b-B1-full-rerun`, branch `wave/D-4b/B1-full-rerun`) — **not** the
`wave-D-4b-B6-real-close-3` / `wave/D-4b/B6-real-close-3` worktree/branch this session was
dispatched to work on. Neither existed anywhere on disk or on `origin` at session start
(`git worktree list` and `git ls-remote --heads origin` both checked, live). Per DR-19's own text —
check the branch belongs to the campaign before any work — a branch named `B1-full-rerun` does
**not** belong to a `B-6 campaign-close` dispatch; this is exactly the class of mismatch DR-19
exists to catch. Rather than proceeding on the wrong branch (which would have meant a B-6 close
report committed to a B-1 scoring branch) or silently improvising a different target, this session
created the dispatched worktree/branch fresh from `origin/main` (`git worktree add -b
wave/D-4b/B6-real-close-3 ... origin/main`, base commit `2df42b61`) and switched into it before any
governance artifact was read or written. `CLAUDECODE_BRIEF.md` frontmatter (post-fetch):
`status: ACTIVE`, `current_wave: D-4b (OPEN — NOT CAMPAIGN-CLOSED …)`. `BRIEF_D4B.md` frontmatter:
`status: OPENED — native kickoff via Cowork 2026-07-21`. Branch `wave/D-4b/B6-real-close-3` now
correctly matches the dispatched campaign (D-4b) and lane (B-6); no branch/campaign mismatch from
this point forward.

### 1b — Live re-verification of every material claim, not trusted on say-so

| Claim | Independent reproduction this pass | Result |
|---|---|---|
| No worktree/branch existed for this dispatch at session start | `git worktree list`; `git ls-remote --heads origin \| grep -i D-4b` | CONFIRMED: only `wave/D-4b/B6-real-close` (no `-3`) existed on `origin`; no local or remote `B6-real-close-3` |
| F-1 (PR #699), F-2 (PR #697) merged | `gh pr view 699/697 --json mergedAt` | CONFIRMED: `2026-07-22T11:07:19Z` / `2026-07-22T07:03:12Z` — unchanged from both prior passes |
| DR-17 grading module (PR #704) merged | `gh pr view 704 --json mergedAt` | CONFIRMED: `2026-07-22T13:47:46Z` |
| PR #695, #703 both merged (predecessors) | `gh pr view 695/703 --json mergedAt` | CONFIRMED: `2026-07-21T23:34:17Z` / `2026-07-22T13:57:10Z` |
| B-1 full re-run NOT merged, NOT opened as a PR | `gh pr list --head wave/D-4b/B1-full-rerun --state all` | CONFIRMED empty; `gh pr list --state open` shows only the unrelated pre-existing `#446` |
| B-1-full-rerun branch pushed to `origin`, matches local | `git rev-parse HEAD` (worktree) vs `git rev-parse origin/wave/D-4b/B1-full-rerun` | CONFIRMED identical: both `0aa69c06` |
| B-1 ASSEMBLY manifest-hash-consistent, DR-12 NO_WINNER | Re-ran `checkManifestHashConsistency()`/`hashManifestFile()` (imported from the committed harness, not reimplemented) fresh against the live files; re-read `B1_FULLRERUN_ASSEMBLED_SUMMARY_v1_0.json`'s `verdict` field | CONFIRMED: `consistent: true`, hash `91dc0c3e20…` byte-identical to the ASSEMBLY_REPORT's own citation; `verdict: "NO_WINNER"` |
| B-2/B-3 still skipped | `gh pr list` search for B-2/B-3/backfill/calibration head refs | CONFIRMED: none found beyond what was already on record |
| `mimamsa_multipliers` still 0 observations | Live SQL: `SELECT count(*), count(*) FILTER (WHERE n_observations>0), max(n_observations) FROM mimamsa_multipliers WHERE chart_id='482012f1-…'` | CONFIRMED byte-identical to both prior passes: `total_rows=9, rows_with_obs=0, max_obs=0` |
| `ka_gochara_sweep` materialization unchanged at 165/300 | Live SQL against `build_substep_progress` + `asset_throughput` (same two queries as both prior passes) | CONFIRMED byte-identical: `165` substeps, `state='error'`, same `last_built_at=2026-07-21T22:25:23.308Z` — no new dispatch has run since PR #695's pass |
| `DISAGREEMENT_REGISTER_v1_0.md` highest entry still `DIS.030`; DR-17/18 still lack a formal DIS row | `grep -o "DIS\.[0-9]*" ... \| sort \| tail`; read `DIS.030`'s own numbering note | CONFIRMED unchanged |
| CR-122 (checkpointed-batching harness) not yet formally registered | `grep -n "CR-122" 00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` | CONFIRMED: zero hits — named in the commit message (`fc6ead96`), not yet a register entry, unlike CR-120/CR-121 which are registered |
| `D4B_PREREGISTRATION_PACKET` still FROZEN, no fresh version for the full re-run | `grep -m1 "^status:"` on the packet | CONFIRMED unchanged: `FROZEN — committed to the ledger 2026-07-21` |

No claim in this report rests solely on a prior session's word without an independent citation of
its own issued this pass.

## §2 — What the completed-but-unmerged B-1 run actually found (disclosed in full, not summarized away)

This is not this pass's own analysis — it is the already-committed `B1_FULLRERUN_ASSEMBLY_REPORT_v1_0.md`'s
findings, re-verified live per §1b and reproduced here because they materially change the wave's
posture even though they are not yet part of `main`:

- **14 evaluable contenders scored** (1 classical default + 12 PERMISSION systems + 1 hierarchical
  ensemble) against the full 54-of-56-event pre-registered corpus. `midpoint_triangle` and
  `transit_kernel` remain NOT-EVALUABLE (CR-120/CR-121, registered) — no row for either, by design.
- **`pratyantar_lord` is the only contender with an adequate sample**: n=54, CRPS skill **−0.1557**
  vs shuffled-birth control (underperforms; beats control on 9/54 events, 16.7%). Its DR-17 grade
  distribution: 17 peak / 2 sub_peak / 8 elevated / 26 neutral / 1 contra, weighted mean 0.407.
- **All 12 PERMISSION contenders + the ensemble are constrained to n=3 each** — `career_advancement`
  is TOTALLY unresolved this run (0/54 scored events resolve to it, despite it being one of only 3
  populated `gochara_resonance_map` classes for this chart), a disclosed recurrence of F-1's design
  limit (the module correctly refuses to force-map a non-matching event rather than over-resolve).
  At n=3, no contender's result — positive or negative — supports a distinguishability claim.
- **DR-12 discharged NO_WINNER**, invoking `BRIEF_D4B.md`'s pre-committed no-winner branch verbatim.
  `pratyantar_lord` is named as the coverage-adequate candidate for B-2 to consider on dispatch, NOT
  as a bakeoff winner — the ASSEMBLY_REPORT is explicit that it "does not name a champion."
- **A gap this pass flags, not previously named**: the ASSEMBLY step's own report cites individual
  verifier ACCEPT receipts for each of the three underlying batches, but does not cite a separate
  independent verifier pass over the ASSEMBLY commit itself (the concatenation + DR-12 discharge
  logic). The arithmetic is independently re-derivable from the persisted per-event JSON (this pass
  re-ran the manifest-hash check as one such re-derivation), but a fresh-context Opus pass over the
  ASSEMBLY step specifically has not been reported to or reproduced by this pass. Naming this as a
  precondition for the eventual merge PR (§0 next-action (b)), not as a defect in the batches
  themselves.

## §3 — Parked-items review vs `BRIEF_D4B.md` §2 — spot-check, not a full re-run

The PR #695 pass performed the full parked-items review; the PR #703 pass spot-checked the items
most likely to have moved. This pass spot-checks again, focused on what the B-1 ASSEMBLY changes:

| Item | PR #703 pass disposition | This pass's spot-check |
|---|---|---|
| B-1's blocker | "Both defects fixed, but no re-run exists beyond an uncommitted scaffold" | **The re-run now exists, complete, assembled, NO_WINNER — but unmerged.** See §0/§2. |
| DR-12 adjudication (DIS.025) | "RATIFIED but NOT YET DISCHARGED" | **Discharged-by-application exists** (the ASSEMBLY session applied the already-native-ratified DR-12 doctrine to real data and invoked the pre-committed no-winner branch) **but is not yet reflected in `DISAGREEMENT_REGISTER_v1_0.md`, and is not on `main`.** This pass does not edit DIS.025 itself — that is a register-maintenance action properly done alongside (or after) the eventual merge, not by a GATED close pass narrating a branch that isn't merged yet. |
| CR-120/CR-121 (NOT-EVALUABLE) | "Now formally registered" | Unchanged — still registered, `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` v3.10. |
| CR-122 (checkpointed-batching harness) | Not yet named as a register item | **New this pass: CR-122 is named in the `fc6ead96` commit message ("checkpointed-batching artifact I/O harness (CR-122 reusable infra)") but has zero hits in `MARSYS_DEFECT_GAP_REGISTER_v2_0.md`.** Flagged as an open registration gap, not resolved by this pass (out of B-6's own scope to unilaterally add register rows for another lane's infra). |
| Marriage-specimen residual (D-5 gate_run_3 / DR-17 pair) | "Strengthened, not closed" | Unchanged this pass — B-3's own formal residual-pair mining still cannot run (still hard-gated on B-1's *merged* receipt, and `ka_gochara_sweep` is still 55% materialized). |
| `ga_vichara_writer.py` leverage_index dasha-runway defect | OPEN, unchanged | Unchanged — no lane has touched it. |
| CR-113, CR-114 | Confirmed/re-confirmed at prior passes | Unchanged — not re-queried this pass (no new evidence would move either). |

All other §2 items from the PR #695/#703 passes are unchanged and not re-litigated here.

## §4 — DR ratification sweep — spot-check, compiled for native ratification, NOT self-ratified

Per `ADJUDICATOR_CHARGE`/`ESCALATION_POLICY`, this session does not ratify its own or any prior
session's provisional doctrine.

- `DISAGREEMENT_REGISTER_v1_0.md`: highest entry still `DIS.030` (grep, this pass, unchanged).
  DR-6/7/8 (`DIS.019`–`021`) unchanged, still queued. DR-17/18 still lack a formal `DIS.0NN` row.
  DIS.025 (DR-12) still literally reads "RATIFIED but NOT YET DISCHARGED" in the register — this is
  now stale relative to the unmerged ASSEMBLY finding (§2/§3), a fact this pass names but does not
  itself correct in the register (that edit belongs with the merge, not with a report narrating an
  unmerged branch).
- `NATIVE_PROXY_LEDGER_D4B.md`: still six entries (NP-D4B-001 through 006), unchanged in substance.
  This pass appends its own compiled-summary addendum (below the PR #703 pass's own compiled
  summary, which is retained, not overwritten) noting the B-1 ASSEMBLY delta against NP-D4B-001
  (DR-17 grading weights — now genuinely exercised, not just scaffolded) and NP-D4B-004 (control
  design — now genuinely re-exercised on the repaired substrate, superseding the NARROWED run's
  pre-F-2 numbers), both still unmerged.
- No new provisional ruling is issued by this pass. Compilation and honest status reporting only.

## §5 — Register final sweep — spot-check

- `CAPABILITY_MANIFEST.json`: `generated_at` unchanged at `2026-07-22T06:50:04.573Z` (same as the
  PR #703 pass) — no further regeneration since. No D-4b doctrine-wave artifact is a tracked
  `canonical_id`, so this is noted for completeness, not drift.
- `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md`: unchanged.
- `CURRENT_STATE_v1_0.md`: not edited by this pass, same convention as both prior passes.

## §6 — Live materialization + calibration state (B-6's own serving-assertion gate, unchanged)

Per `BRIEF_D4B.md` §0's RECONCILIATION, full-horizon `ka_gochara_sweep` materialization gates only
B-6's own serving assertions, not B-1's event-driven scoring (which this pass's §2 findings confirm
ran successfully without full materialization, consistent with that reconciliation). Re-checked
live this pass:

```sql
SELECT count(*) FROM build_substep_progress
 WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ka_gochara_sweep';
-- 165  (planned: 300; 55% — byte-identical to both prior passes, no new dispatch since)

SELECT state, last_error, last_built_at FROM asset_throughput
 WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ka_gochara_sweep';
-- state='error'; last_built_at=2026-07-21T22:25:23.308Z
-- last_error="BLOCKED: upstream dependency(ies) timeout:21600s did not complete in this run;
--             skipped to avoid building on incomplete data"

SELECT count(*) AS total_rows,
       count(*) FILTER (WHERE n_observations > 0) AS rows_with_obs,
       max(n_observations) AS max_obs
  FROM mimamsa_multipliers WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- total_rows=9, rows_with_obs=0, max_obs=0 — structural mode confirmed unchanged
```

No new rebuild has been dispatched since the PR #695 pass. This report makes no claim of full
materialization and no claim that calibration has left structural mode.

## §7 — Ground-rule compliance (B.10, DR-16, DR-19)

No numerical chart value, score, count, or DB row was fabricated by this pass. Every number cited
above is either quoted verbatim from a live `gh`/SQL query or a live re-run of the committed
`b1_batch_artifact_io.ts` functions issued this pass (exact command/SQL shown), or is an explicit,
attributed quotation from the already-committed `B1_FULLRERUN_ASSEMBLY_REPORT_v1_0.md` /
`B1_FULLRERUN_ASSEMBLED_SUMMARY_v1_0.json` (clearly marked as such, cross-checked where feasible —
the manifest-hash re-run and the `verdict` field re-read — rather than merely copied). This pass
does not claim credit for the three batches' own individually-reported verifier ACCEPT receipts,
which it did not itself run. `asset_runner.py`, `runner.py`'s `execute_dag`/`_schedule_parallel`,
the leakage firewall, raw LEL event data, prior gate/regression surfaces, and `gochara_grammar`/
`gochara_intensity` source logic were not modified. This pass's only DB reads touched
`build_substep_progress`, `asset_throughput`, and `mimamsa_multipliers` (build/calibration metadata
tables, never `life_events` or any sealed-split content). No event row on or after 2020-01-01 was
queried by this pass. No destructive DB write was performed. The one filesystem write outside the
four governance deliverables — a temporary manifest-hash re-verification script under
`platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/_b6_verify_hash_tmp.ts` — was deleted
immediately after use and is not part of this branch's committed diff; `git status --short` on the
`B1-full-rerun` worktree after cleanup shows only the pre-existing, unrelated `pnpm-lock.yaml` diff
that predates this pass. The worktree/branch mismatch at session start (§1a) was resolved by
creating the dispatched worktree fresh from `origin/main`, not by working on the wrong branch or
silently redirecting scope.

## §8 — Next

`current_wave` stays `D-4b (OPEN)`. This wave does not close until B-1's already-complete,
already-honest NO_WINNER run is opened as a PR, independently verified at the ASSEMBLY level, and
merged to `main`; B-2 and B-3 then dispatch against that real, merged receipt (`model_confidence:
none_validated` per the no-winner branch); B-4/B-5 remain done; and a future B-6 pass runs the full
campaign-close checklist — parked-items review, full DR ratification sweep, full register sweep,
master-regression-suite confirmation, the mode=FULL three-point baseline diff, and the standing-
live-loop declaration — that no pass to date has run.

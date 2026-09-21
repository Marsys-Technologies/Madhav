# Domain I — Source inventory: unmerged branch content audit

**Method note (read this first):** the audit worktree's `.git` was a **shallow clone**
(depth-limited; `origin/main` locally only went back to 2026-09-18, 53 commits, with
fabricated-looking "no merge base" errors against every feature branch). This alone would
have produced false GENUINELY_UNDELIVERED findings for nearly every branch sampled, purely
as a git-plumbing artifact, not a real content gap. Fixed by running `git fetch --unshallow
origin` (read-only, no branch/ref mutation) before any content diff — confirmed via
`git rev-parse --is-shallow-repository` → `false` and `git rev-list --count origin/main` →
5583 afterward. All findings below are post-unshallow, content-level (`git diff A B --
<path>`), not ancestry-level (`git log A..B`).

## Total branch count vs. the "~113" claim

- **Total remote branches (`git branch -r`): 1059.** The "~113" figure in the campaign
  framing is **wrong by roughly an order of magnitude** — off by ~9.4x, not a rounding
  error. Whatever the "~113" count was measuring (perhaps a stale snapshot, or a narrower
  filter that was later mis-cited as "unmerged branches"), it does not match the current
  `origin` branch list.
- **Branches matching the L3-naming heuristic** (`grep -iE 'l3|kala|ka_|gochara|kshetra|
  sangam'`): **137**. This is closer to "~113" in order of magnitude but still not a match —
  if "~113" was meant to approximate the L3-relevant subset, it undercounts by ~21%.
- Priority sub-groups within the 137: `kshetra` (4), `sangam` (6, incl. `ekv/lead-sangama`
  which is not really L3), `gochara` (12, several `gochara3/*` likely pre-dating the `ka_*`
  naming convention entirely).

## Sample methodology

15 branches sampled, prioritized per brief instructions toward kshetra/sangam/gochara/kala
(the hardest L3 assets per other audit context). For each: commits-ahead-of-main by
ancestry, then a **full-file content diff** (`git diff origin/main origin/<branch> --
<specific-file>`) on the asset's actual source files — not just `--stat`, since `--stat`
line-count deltas can't distinguish "genuinely missing" from "reordered/refactored
equivalently." Where a file's diff was non-empty, the diff was read to determine
**direction**: is the branch missing something main has (branch is behind/stale), or does
main lack something the branch has (branch carries undelivered content)?

## Key finding: PR #2607 is a real, large squash-delivery event

`fa9857f00 2026-09-16 08:18:23 +0000 feat(data-plane): deliver governed L0-L3 source
execution (#2607)` is the commit on `origin/main`'s file history behind most of the
"already delivered" verdicts below. It lands one day after the `codex/l3-kshetra-*`
branches' last commits (2026-09-15) and squash-delivers their content — consistent with
the brief's framing that a prior "stranded work" claim about this PR was wrong. Multiple
*other*, unrelated fixes (F-SANGAM-5, F-SANGAM-7, F-KOTA-3, F-KALA-1) also landed on main
after these branches' commit dates and are visible as forward-superseding diffs (main has
MORE / corrected content, branch has the pre-fix state) — these are separate delivery
events, not all attributable to #2607 specifically.

## Sample table

| branch | last commit date | commits ahead of main (ancestry) | classification | evidence | note |
|---|---|---|---|---|---|
| `codex/l3-kshetra-p0` | 2026-09-15 03:40 +0530 | 40 | DELIVERED | `writer.py`/`stage0-3.py`/`dhara_sweep.py` diff vs `w0-preservation` (its own successor) is empty; vs main, `dhara_null_vec.py`/`dhara_null.py`/`layer1.py` show main has the SM-R-11-superseding compat shim (newer, simpler) | Part of a 3-branch p0→p0-correction→w0-preservation chain; w0-preservation is the superset, squash-delivered via #2607 |
| `codex/l3-kshetra-p0-correction` | 2026-09-15 03:47 +0530 | 45 | DELIVERED | `writer.py` diff vs main is non-empty but vs `w0-preservation` main matches the more-advanced state; same `dhara_null_vec.py` supersession pattern | Superseded by its own successor branch before delivery |
| `codex/l3-kshetra-w0-preservation` | 2026-09-15 04:27 +0530 | 52 | DELIVERED | `git diff origin/main origin/<branch> -- platform/python-sidecar/services/ka_kshetra/writer.py` is **byte-empty**; only `dhara_null*.py`/`layer1.py` differ, and those show main is NEWER (SM-R-11 shim) | Most-advanced of the 3 kshetra branches; core writer + stage files fully delivered |
| `l1-w405-ka-kshetra-output-digest-spec` | 2026-09-09 20:12 +0530 | 1 | DELIVERED | Migration files `1002_nirmana_l3_ka_kshetra_output_digest_spec.sql` / `1003_..._natural_key_partition.sql` exist verbatim on disk at `platform/migrations/` | Trivial single-commit migration-only branch, fully applied |
| `codex/nirmana-l3-f-sangam-5-vedha` | 2026-09-06 16:07 +0530 | 1 | DELIVERED | `engine.py` diff shows main has the fuller `_c_cross_dasha_agreement` honest-`None` fix with detailed §N.8 commentary (F-SANGAM-3/4/6/7); branch's version is a pre-fix subset. Migration 980/981 files present on main (moved, not missing) | Test file moved from `tests/l3/` to `tests/` on main — reorg, not loss |
| `codex/nirmana-l3-f-sangam7-dirty-fix-state` | 2026-09-06 15:04 +0530 | 1 | DELIVERED | `engine.py` `_c8_eclipse_score` diff: main has the two-node (Rahu+Ketu) eclipse check with full F-SANGAM-7 commentary; branch has the single-node pre-fix version | "dirty-fix-state" branch name suggests an abandoned WIP snapshot; the real fix landed cleanly on main |
| `codex/nirmana-l3-f-sangam7-eclipse-dirty-fix` | 2026-09-06 15:04 +0530 | 1 | DELIVERED | Identical diffstat/content pattern to the sibling `-dirty-fix-state` branch above | Near-duplicate of the sibling branch; same verdict |
| `codex/nirmana-l3-f-sangam7-stance-dirty-fix` | 2026-09-06 15:07 +0530 | 1 | DELIVERED | Same `_c8_eclipse_score` / `engine.py` pattern, smaller diff (161 vs 242 lines) — an even earlier draft of the same fix | Same fix family as the two branches above, all superseded |
| `l1-w389-ka-sangam-output-digest-spec` | 2026-09-09 08:07 +0530 | 2 | DELIVERED | `engine.py` diff is a 3-line deletion only; trivial | Fully absorbed |
| `l3-2527-gochara-resonance-orderby` | 2026-09-10 06:06 +0530 | 2 | DELIVERED | The commit's actual point — `ORDER BY graha, rule_type, primary_house` in `ka_gochara_resonance/writer.py` — is present verbatim on main at the same line (377); remaining diff is main having a LATER, more careful idempotency/honest-empty-partition improvement layered on top | Digest non-determinism fix confirmed delivered; main has since improved further |
| `l3-2542-ka-gochara-plan-substeps-remaining-work` | 2026-09-10 08:46 +0530 | 2 | DELIVERED | `pipeline/orchestrator/writers/ka_gochara.py` shows **zero diff** vs main | plan_substeps fix fully present |
| `codex/nirmana-l3-w3-m12-gochara-orphans` | 2026-09-05 20:12 +0530 | 1 | STALE | `w25_kota_chakra.py` diff shows main has the F-KOTA-3 fix (real DB vocabulary `durgantara`/`prakara`); branch still has the pre-fix, non-existent-in-DB vocabulary (`madhya`/`pragara`) that the F-KOTA-3 finding says silently dropped 59.4% of rows to a no-op | Branch predates a load-bearing correctness fix that already shipped; its own 54-orphan-row disposal concern was not independently re-verified as still-needed, hence STALE not DELIVERED |
| `codex/nirmana-l3-f-kala-1-activation-rank-key` | 2026-09-06 14:28 +0530 | 1 | DELIVERED | `register_d9_judgment.ts` F-KALA-1 block (comment cites `L3_W1_ANALYSIS_BATCH_E.md, ka_kalasutra finding 1`) present near-verbatim on main (offset only, content identical in a 90-line window diff) | `kala_trigger/trigger.py` shows main REMOVED the branch's `house_from_moon()`/`vedha_factor_corrected()` exploratory functions — main's own comment states F-SANGAM-5 "supersedes T-5.4's premise entirely," explaining the removal as intentional, not a loss |
| `codex/nirmana-l3-f-kala-1-ahead-recurrence-rank` | 2026-09-06 00:55 +0530 | 1 | DELIVERED | Same `register_d9_judgment.ts` F-KALA-1 fix family; diffstat dominated by deletions (branch missing later refinements main has) | Sibling "third slice" of the same F-KALA-1 effort |
| `codex/nirmana-l3-f-kala-1-query-temporal-order-by` | 2026-09-06 14:29 +0530 | 1 | DELIVERED | `query_temporal_activation.ts` — F-KALA-1 "99.6% NULL" comment block present verbatim on main (line 289) and on branch (line 191), same wording | "second slice" of F-KALA-1; core LIMIT-cut-point fix confirmed delivered |

## Summary

- **Sampled: 15 of 137 L3-naming-matched branches (≈ 11%), and 15 of 1059 total unmerged
  branches (≈ 1.4%).** These are the only fractions that can be honestly claimed — do not
  extrapolate a precise "X% of the 113/137/1059 population is delivered" from this sample;
  the sample was deliberately non-random (prioritized toward the names most likely to be
  hard/contested per the brief), so it is not representative of the full population's mix.
- **GENUINELY_UNDELIVERED: 0 of 15.** Every sampled branch's substantive `ka_*`/L3 logic was
  either (a) content-identical to what's on `origin/main` today (usually via the #2607
  squash-delivery or a smaller individual PR), or (b) STALE — superseded by a later,
  better-documented fix already on main, with the branch's own content representing a
  pre-fix or abandoned-WIP state (1 branch: `codex/nirmana-l3-w3-m12-gochara-orphans`).
- **14 of 15 = DELIVERED, 1 of 15 = STALE, 0 = UNCLEAR, 0 = GENUINELY_UNDELIVERED.**
- **Caveat on the STALE verdict:** `codex/nirmana-l3-w3-m12-gochara-orphans`'s core concern
  (disposing 54 unrefreshable `ka_gochara_v3` orphan rows, F-CENT-2/M12) was not itself
  re-verified against current row state — it was graded STALE because the branch's *code*
  predates a since-landed correctness fix (F-KOTA-3) elsewhere in the same file family, which
  is evidence the branch is an old snapshot, not direct evidence the orphan-row disposal
  itself already happened. If the native wants certainty on that specific row-disposal
  question, it needs a live DB check (`SELECT count(*) FROM kala_gochara_v3_century WHERE
  <orphan predicate>`), which is out of scope for this git-only audit.
- **What this domain does NOT establish:** whether the same DELIVERED pattern holds across
  the other 122 unsampled L3-naming-matched branches, or the ~922 unsampled non-L3-named
  branches (some of which may still touch `ka_*` files without an L3-suggestive branch
  name — the naming heuristic itself is a filter, not a guarantee of completeness). The
  consistent pattern across all 15 samples (main is repeatedly the superset, with real
  documented fixes forward of every branch's snapshot date) is suggestive that the
  underlying campaign process is genuinely absorbing branch work rather than losing it, but
  15 samples out of 137 is not enough to certify that for the full population.

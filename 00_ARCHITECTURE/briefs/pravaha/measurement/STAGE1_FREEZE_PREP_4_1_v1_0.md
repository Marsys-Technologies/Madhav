---
artifact: STAGE1_FREEZE_PREP_4_1
version: "1.0"
status: PREPARED — Stage-1 code is a draft PR (#2923, HOLD); the freeze record is a DRAFT with named placeholders; NO '4.1' or '5.0' output was generated or read
date: 2026-10-02
author: Stream B (Śāstra), B6.0 — steward M (STAGE-1 FREEZE for the '4.1' candidate measurement)
governs: "EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING_v1_3.md §5 (two-stage freeze); supersedes the command section of SCORING_RUN_4_1_PLAN_v1_0.md §3 for a measurement run (that plan's extract spec, thresholds and horizon assertion stay)"
---

# Stage-1 freeze preparation — generation '4.1'

## 1. What exists now
| piece | where | state |
|---|---|---|
| unknown-competitor bounds, candidate adapter, scorer | PR **#2923** `services/gochara_eval/{unknowns,candidate}.py` | draft, HOLD, tests green |
| freeze verifier (Stage 1 + Stage 2 refusal) | `freeze.py`, `candidate_score.py` | same PR |
| exact extract-generation command | `dump_extract.py` | same PR; refuses without a verified freeze; refuses governed `5.x` |
| freeze record | `FREEZE_STAGE1_4_1_v1.DRAFT.json` | all pre-extract input hashes filled **and verified**; placeholders only for what cannot exist yet |

## 2. The extract-generation command (exact)
```sh
# from platform/python-sidecar, on the merged commit; DSN of a READ-ONLY role in GOCHARA_EVAL_READONLY_DSN (or --libpq-env)
python3 -m services.gochara_eval.dump_extract --generation 4.1 \
  --stage1 ../../00_ARCHITECTURE/briefs/pravaha/measurement/FREEZE_STAGE1_4_1_v1.json \
  --pinned-at <declared date> \
  --out ../../00_ARCHITECTURE/briefs/pravaha/measurement/baseline_4_1_extract_v1_0.json
```
One SELECT in a READ ONLY transaction, after the horizon assertion (0 windows outside 1998-01-01 ≤ window < 2026-04-18). Deterministic: **total** `ORDER BY` over every selected column, `pinned_at` an argument, the pinned layout (indent 1, no trailing newline — byte-identical to the pinned `3.0` file when fed its rows, tested). The plan v1.1 SQL ordered by `(event_class, ws)` only.

## 3. The `3.0` reproduction (the detector that the adapter measures what the protocol says)
Run three ways, all from the final code:
1. **Pinned extract → new adapter+scorer** (`candidate_score --baseline-dry-run`): T-cover 32/47 with the same 15 misses; T-time 182 d (2 misses; uncapped 686/998/333); T-rank VOID, 0/32 eligible; T-FP adverse 8/9 FAIL and gain 17/17 FAIL; era-fingerprint 59.8 %; dedup table; controls 638/940 re-drawn and reproduced; **all 47 per-event records (N, hit, percentile, rank_status) equal `rerun_per_event_v2_3.json`**. Equal, figure by figure, to `rerun_result_v2_3.json` and to the existing `score_generation`.
2. **Fresh read-only re-dump of production `3.0` → new adapter+scorer**: identical figures (above). The dump holds the **same 914 rows** as the pinned file (row multiset identical) but **not the same bytes**: the pinned file's order among rows tied on `(event_class, ws)` was database-defined (24 positions differ). Scoring is order-invariant (the merge sorts); the new command's order is total, so a candidate extract **is** byte-reproducible. The `3.0` pin therefore remains a **content** pin; candidate extracts are sealed by **bytes** in Stage 2.
3. **Random known extracts vs the existing scorer** (8 seeds, real registry): equal on every figure — with no unknown, every range collapses to a point.

## 4. Disclosures the freeze carries
- **si mapping for `4.1` is `signed_intensity`**, not `evidence_for`: `kala_gochara_windows` has no `evidence_for` column; the addendum's mapping governs governed `5.x` eval-window rows. `signed_intensity` is `NUMERIC NOT NULL`, so **no unknown competitor can occur in a `4.1` extract**; the bounds code is exercised on synthetic extracts and the run asserts `unknown_si_rows = 0`.
- **Tie grouping**: the addendum's adjacent-gap grouping governs ranking here; `metrics.event_hit` anchors ties on the target. They differ only when ≥ 3 values chain within 1e-9 — pinned by a test, absent from `3.0`.
- **T-honesty**: `4.1` needs the computation-coverage manifest or it is `UNVERIFIABLE` and not flip-eligible (plan §4).
- **Orb state** is a placeholder awaiting confirmation (`<<CONFIRM…>>`): proposed "n/a for `4.1`; ND-ORB-* bind governed `5.x` only".
- **Equivalent-mutant note**: of 13 mutations of the new code, 11 were caught by tests, 2 are equivalent (the explicit zero placement and the chain-from-zero placement are also produced by other placements); 1 initial gap (unqualified plateau treated as eligible) was closed with a test.

## 5. Freeze-day sequence (nothing before the merge)
1. Merge PR #2923 (steward/native). Record the merge commit.
2. `python3 -m services.gochara_eval.freeze` → paste `code.files`; fill both commit ids, `pinned_at`, amendments-draft version+sha, orb state; set `status: FROZEN`; save as `FREEZE_STAGE1_4_1_v1.json`; **commit before any extract exists**. (`require_stage1` lists every remaining problem.)
3. Re-run the §3.1 requalification on the frozen code; **stop if any figure differs**.
4. Preconditions of the generation itself (not of this freeze): Suvarṇa's L1 rebuild + the AM-10 daśā re-pin landed; publication row for `4.1`.
5. Generate the extract with the §2 command → write `FREEZE_STAGE2_4_1_v1.json` (`run_id`, `stage1_sha256`, `extracts.<file>.sha256`) → **commit before opening the extract**.
6. `candidate_score --stage1 … --stage2 … --extract … --controls … --output …` (refuses without both stages and a matching hash).

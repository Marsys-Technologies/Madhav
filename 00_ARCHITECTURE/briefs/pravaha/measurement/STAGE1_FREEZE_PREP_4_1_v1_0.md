---
artifact: STAGE1_FREEZE_PREP_4_1
version: "1.4"
status: PREPARED — Stage-1 code is a draft PR (#2923, HOLD until Codex has reviewed it as packet v1_10 §G, step (d) only); the freeze record is a DRAFT with named placeholders; NO '4.1' or '5.0' output was generated or read
date: 2026-10-02
author: Stream B (Śāstra), B6.0 — steward M (STAGE-1 FREEZE for the '4.1' candidate measurement)
amended: 2026-10-02 (v1.4 — Codex round 9: the freeze draft is rewritten to the TYPED schema of `freeze.py` (R9-8) — inputs keyed by the 12 fixed identifiers, numeric cohort/seed/budget, `consumed_bodies` incl. the Moon + horizon, a real manifest read-back OBJECT required; pre-registration is SI addendum **v1.5** (proven unknown-competitor enumeration, R9-7; v1.4 untouched); the bounds-model hash updated (v2 model); v1.3 — S1-REQ-EPHEMERIS named Stage-1 requirement (steward M20261002T042929-e773): manifest read-back now checks the AM-16 ephemeris component, the freeze verifier refuses unless it is clean; v1.2 — Stream A coverage relay M20261002T042919-8f9e: T-honesty DETERMINED UNVERIFIABLE, coverage disclosure block, `--read-coverage-summary`; a date-parameter defect in the dump SQL found and fixed by a new real-PostgreSQL test; v1.1 — steward answers M20261002T042015-7bff: si := raw_intensity (SI addendum v1.4 §1a), orb_state text + manifest read-back, T-honesty pre-declared UNVERIFIABLE, 3.0 byte-order erratum, packet §G)
governs: "EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING_v1_3.md §5 (two-stage freeze); supersedes the command section of SCORING_RUN_4_1_PLAN_v1_0.md §3 for a measurement run (that plan's extract spec, thresholds and horizon assertion stay)"
---

# Stage-1 freeze preparation — generation '4.1'

## 1. What exists now
| piece | where | state |
|---|---|---|
| unknown-competitor bounds, candidate adapter, scorer | PR **#2923** `services/gochara_eval/{unknowns,candidate}.py` | draft, HOLD, tests green |
| freeze verifier (Stage 1 + Stage 2 refusal) | `freeze.py`, `candidate_score.py` | same PR |
| exact extract-generation command | `dump_extract.py` | same PR; refuses without a verified freeze; refuses governed `5.x` |
| freeze record | `FREEZE_STAGE1_4_1_v1.DRAFT.json` | all pre-extract input hashes filled **and verified**; placeholders only for what cannot exist yet (22 items listed by the verifier) |
| si pre-registration | `EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING_v1_5.md` (§1a '4.1' mapping from v1.4; §4 proven enumeration, new in v1.5) | v1.4 + the operational §4; v1.4 and v1.3 untouched |

## 2. The extract-generation command (exact)
```sh
# from platform/python-sidecar, on the merged commit; DSN of a READ-ONLY role in GOCHARA_EVAL_READONLY_DSN (or --libpq-env)
python3 -m services.gochara_eval.dump_extract --generation 4.1 \
  --stage1 ../../00_ARCHITECTURE/briefs/pravaha/measurement/FREEZE_STAGE1_4_1_v1.json \
  --pinned-at <declared date> \
  --out ../../00_ARCHITECTURE/briefs/pravaha/measurement/baseline_4_1_extract_v1_0.json
```
READ ONLY transaction: sign reconciliation (`|signed_intensity| = raw_intensity`, no negative raw — both counts 0), horizon assertion (0 windows outside 1998-01-01 ≤ window < 2026-04-18), then one ordered SELECT with **`si := raw_intensity`** (§4). Deterministic: **total** `ORDER BY` over every selected column, `pinned_at` an argument, the pinned layout (indent 1, no trailing newline — byte-identical to the pinned `3.0` file when fed its rows, tested). The plan v1.1 SQL ordered by `(event_class, ws)` only.

## 3. The `3.0` reproduction (the detector that the adapter measures what the protocol says)
Run three ways, all from the final code:
1. **Pinned extract → new adapter+scorer** (`candidate_score --baseline-dry-run`): T-cover 32/47 with the same 15 misses; T-time 182 d (2 misses; uncapped 686/998/333); T-rank VOID, 0/32 eligible; T-FP adverse 8/9 FAIL and gain 17/17 FAIL; era-fingerprint 59.8 %; dedup table; controls 638/940 re-drawn and reproduced; **all 47 per-event records (N, hit, percentile, rank_status) equal `rerun_per_event_v2_3.json`**. Equal, figure by figure, to `rerun_result_v2_3.json` and to the existing `score_generation`.
2. **Fresh read-only re-dump of production `3.0` → new adapter+scorer**: identical figures (above). The dump holds the **same 914 rows** as the pinned file (row multiset identical) but **not the same bytes**: the pinned file's order among rows tied on `(event_class, ws)` was database-defined (24 positions differ). Scoring is order-invariant (the merge sorts); the new command's order is total, so a candidate extract **is** byte-reproducible. The `3.0` pin therefore remains a **content** pin; candidate extracts are sealed by **bytes** in Stage 2.
3. **Random known extracts vs the existing scorer** (8 seeds, real registry): equal on every figure — with no unknown, every range collapses to a point.

## 4. Disclosures the freeze carries
- **si for `4.1` := `raw_intensity`, as stored** (SI addendum **v1.4 §1a**, pre-registered before any `4.1` output exists). The 4.x writer (`step06b_windows_projection.py`) stores `signed_intensity = raw_intensity × (−1 if is_adverse else 1)` — **negative on every adverse window** — which protocol §4.5 (si non-negative for every class) rejects, so `signed_intensity` is not the like-for-like column. In `3.0` the pinned extract's si was `signed_intensity`, and there it equals `raw_intensity` on **all 914 rows** (none negative; 330 adverse rows positive; read-only check 2026-10-02), so `raw_intensity` is the same quantity in both generations. No abs(), no polarity transform. Enforced by the dump (stop if `|signed| ≠ raw` or `raw < 0`). `raw_intensity` is `NOT NULL`: no unknown competitor can occur; the run asserts `unknown_si_rows = 0`.
- **Orb state** — written as the steward directed: the `4.1` candidate uses the 4.x chain's own activity orb **as declared in its manifest input vector (unratified); the value is read from the manifest at freeze, never from the freeze file**; ND-ORB-ADMISSION/SCALE bind governed `5.x` only. Keys quoted: `kala_gochara_publication.input_generation_vector` → `orb_max_deg` (writer constant `ORB_DEG = 5.0`) and `orb_ruling` (`'M-1 fallback no-box × 5.0° (unratified)'`). **Discrepancy disclosed:** the writer's source comment calls it "M-1 ratified candidate-1 enumeration orb" while the manifest string says "unratified"; the freeze quotes the manifest. Read-back command: `dump_extract --generation 4.1 --read-manifest-orb` (reads no window row).
- **T-honesty — DETERMINED `UNVERIFIABLE`.** Protocol §6.5: coverage is per class, (class, year) cells computed ÷ cells in the horizon, from a manifest naming those cells. The `4.1` chain (Stream A relay, from the writer code) writes `kala_gochara_coverage` per **body-target** partition (`partition_kind='body_target'`, key `<body>:<target_type>`; the 8 persisted bodies — the Moon is on-demand, never persisted); each partition records the pinned horizon requested = completed, the resolution, relations searched, and target counts by resolution state. There are **no event-class partitions and no year cells**, so the per-class fraction **cannot be computed** without a class↔(body, target_type) mapping no governed source declares — none is invented. **Consequence:** by §6.5(b) the `4.1` candidate is **not flip-eligible under v2.3** whatever its other endpoints show; it is measured as a diagnostic. What the partition rows *can* say (carried as a **disclosure block only**, never as a manifest): the whole horizon was searched per partition, unresolved targets are counted by state. What they *cannot* say: per-(class, year) coverage, completeness of any class's windows, anything about the Moon. A route to verifiability needs a **new decision before any result** — per-(class, year) coverage rows for `4.1`, or a protocol amendment declaring a mapping from a governed source. Also: the `4.1` manifest carries no ephemeris/implementation identity — see the next bullet.
- **Named Stage-1 requirement S1-REQ-EPHEMERIS** (freeze draft `ephemeris_requirement`): before the governed `4.1` run the manifest must record the AM-16 ephemeris component (one definition shared with `5.0`) and the writer must refuse a Moshier-served probe. The freeze verifier refuses unless `dump_extract --read-manifest-orb` reports `ephemeris_problems == []`. Minimal change (Stream A's, unscheduled): one public `ephemeris_component(...)` built on the existing `ephemeris_identity` helpers, called by both generations, stored under key `ephemeris` in the 4.1 vector (+ `ephemeris_definition`), re-checked in the last substep; bodies/flags are the kernel's own `knots` constants (the 4.1 enumerator already imports them); probe range = horizon ± 1 day. Alignment gap: Stream A's code stores `runtime.swisseph_sha256` and no `platform` (label `/1`) while AM-16 /2 names `library_sha256` and `platform`.
- **Tie grouping**: the addendum's adjacent-gap grouping governs ranking here; `metrics.event_hit` anchors ties on the target. They differ only when ≥ 3 values chain within 1e-9 — pinned by a test, absent from `3.0`.
- **`3.0` pin** is a content pin (erratum `BASELINE_3_0_v2_3.md` §9; no re-pin, steward ruling).
- **Equivalent-mutant note**: of 13 mutations of the candidate code, 11 caught, 2 equivalent (the explicit zero placement and the chain-from-zero placement are also produced by other placements); 1 initial gap closed with a test; the 2 sign-reconciliation mutations of the dump are caught.

## 5. Freeze-day sequence (nothing before the merge)
1. Merge PR #2923 (steward/native). Record the merge commit.
2. `python3 -m services.gochara_eval.freeze` → paste `code.files`; run `dump_extract --generation 4.1 --read-manifest-orb` and paste the read-back into `orb_state.manifest_readback` and `dump_extract --generation 4.1 --read-coverage-summary` into `coverage_disclosure.readback`; fill both commit ids, `pinned_at`, amendments-draft version+sha; set `status: FROZEN`; save as `FREEZE_STAGE1_4_1_v1.json`; **commit before any extract exists**. (`require_stage1` lists every remaining problem.)
3. Re-run the §3.1 requalification on the frozen code; **stop if any figure differs**.
4. Preconditions of the generation itself (not of this freeze): Suvarṇa's L1 rebuild + the AM-10 daśā re-pin landed; publication row for `4.1`.
5. Generate the extract with the §2 command → write `FREEZE_STAGE2_4_1_v1.json` (`run_id`, `stage1_sha256`, `extracts.<file>.sha256`) → **commit before opening the extract**.
6. `candidate_score --stage1 … --stage2 … --extract … --controls … --output …` (refuses without both stages and a matching hash).


## v1.4 note — what the draft still lacks (checked by running `freeze.stage1_problems` on it)
After the R9-8 rewrite the verifier's ONLY remaining findings on the draft are the freeze-time reads, each a named placeholder: `status`, the amendments-draft version and sha256, the two code commits and the nine `code.files` hashes (from the merged commit), `pinned_at`, the coverage read-back, and the manifest read-back object (one read, used for both `orb_state` and `ephemeris_requirement`). Every typed field (cohort integers, controls seed, tolerances, budget, thresholds, conventions) and all eleven non-draft input hashes verify on disk.

---
artifact: B4_7_DRY_RUN
version: "1.0"
status: COMPLETE — harness proven end to end; ready to score '4.1' the moment the generation exists
date: 2026-10-01
author: Stream B (Śāstra), item B4.7 (steward queue Q2, M20261001T161909-a27f)
writes: "NONE — every production touch was read-only (MCP read-only role); scoring ran locally against materialised files"
---

# B4.7 dry-run — the '4.1' scoring harness, proven end to end on '3.0' data

Everything `SCORING_RUN_4_1_PLAN_v1_0.md` (now v1.1) needs to score the narrowed
`'4.1'` candidate the moment A2.5 lands, executed in advance against the current
`'3.0'` data. Result: **every check green; zero blockers; one plan correction
(v1.1, column names) — itself the value of a dry-run.**

## 1. Preconditions verified (read-only)

| check | result |
|---|---|
| `'4.1'` does not yet exist (detector: `count(*)` of `kala_gochara_windows`, chart `482012f1…`, `generation='4.1'`) | **0** — scoring remains a future event; this page scored nothing |
| Horizon-assertion query (plan §2, native narrowing 1998-01-01 → 2026-04-18 end-exclusive) executes against production | executes; returns **0** (vacuous — no '4.1' rows); ready as the extract-time gate |
| Extract query shape (plan §2 dump) reproduces the pinned '3.0' extract from live production, read-only | **914 rows; server-side md5 `007aae8994b43b6291312f4719d1f949` == client-side md5 over `baseline_3_0_extract_v1_0.json` rows — exact** |
| Pinned extract integrity | file sha256 `70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff` matches the BASELINE_3_0_v2_3 pin record |
| Controls materialised | `random_controls_v1_3.json` sha256 `eea40fe8ba743a15291c8ec885b1f9dc0c5591a03ebf8bfb70cbefe414f6cb94` == the v2.3 record |
| Registry | `event_registry_v2_3.json` sha256 `23633a24…`; harness source-reconciliation confirms held_out [47, 47] |
| Harness on main | `services/gochara_eval` present at `origin/main` (post-#2766) |

## 2. Harness qualification (plan §3a) — figure-identical to the pinned '3.0' result

```
python3 -m services.gochara_eval --registry event_registry_v2_3.json \
  --extract baseline_3_0_extract_v1_0.json --controls random_controls_v1_3.json \
  --output /tmp/b47_requalify_3_0.json \
  --declared-pin 70ba6142…84ff --generation 3.0
```

Exit 0. Compared key-by-key against the pinned `rerun_result_v2_3.json`:
**every endpoint figure identical** — T-cover 32/47 (pass); T-time capped median
182 d, misses=2, uncapped [686, 998, 333]; T-rank VOID; T-FP per-class burdens and
budgets identical (adverse over-prediction disclosed in v2.3 reproduced exactly:
burden 99.8742 % vs budget 2.6127/5.2255 %, `separation` the lone pass at
0.0871 %); T-FP-gain entries identical; T-honesty UNVERIFIABLE (manifest absent,
as disclosed for '3.0'); random controls REPRODUCED 638/940.

13 key-level diffs, **all additive metadata** in the current harness (adds
`generation`, `input_adapter.raw_row_count`, `raw_valence_domain` tally,
`random_controls.status`, `source_reconciliation.detail` echoes) or wording
(`t_honesty.reason`: "supplied" vs "exists" — same condition). No figure moved.
The current-main harness is a strict superset of the one that produced v2.3.

## 3. The '4.1' path (plan §3b command shape) — runs end to end

The exact §3b invocation with the '3.0' pinned extract standing in for the
not-yet-existing '4.1' extract, `--generation 4.1`:

- exit 0; the result differs from the §3a output in exactly one key:
  `generation` (`'4.1'` vs `'3.0'`). Every endpoint, control, dedup and
  reconciliation figure identical — the generation label flows through and
  changes nothing else.
- **Determinism:** the same invocation re-run produced a **byte-identical**
  output file (`cmp` clean) — the plan's determinism requirement is met by
  construction and verified.

## 4. Plan correction folded (v1.1) — the dry-run's find

The v1.0 plan's §2 SQL named the adapter aliases (`ws, we, pk, si, adv`) as if
they were table columns; production `kala_gochara_windows` carries
`window_start, window_end, peak_date, signed_intensity, is_adverse`
(`information_schema.columns`, 2026-10-01). Run as written, the v1.0 extract and
horizon queries error (`column "we" does not exist` — hit during this dry-run).
`SCORING_RUN_4_1_PLAN` v1.1 corrects both queries to the production columns,
keeping the SELECT-list aliases so the extract-file contract is unchanged. No
threshold, horizon, or procedure change.

## 5. What remains for the real run (nothing preparatory left)

1. A2.5 lands → detector (`count(*)` of §1 row 1) goes non-zero.
2. Extract: run the v1.1 §2 dump read-only, write `baseline_4_1_extract_v1_0.json`,
   pin its sha256 in the plan.
3. Horizon gate: the §2 assertion must return 0, else INPUT_REJECTED stop.
4. Score: §3a requalification, then §3b; deliverable `BASELINE_4_1_v1_0.md` (B4.4)
   with the '4.1'-vs-'3.0' side-by-side — every figure above is the reference row.

Evidence files (local, reproducible on demand): `/tmp/b47_requalify_3_0.json`,
`/tmp/b47_dryrun_4_1_label.json`, `/tmp/b47_dryrun_4_1_label_2.json`.

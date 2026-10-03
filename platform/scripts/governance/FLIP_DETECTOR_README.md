---
artifact: FLIP_DETECTOR_README
version: 2.5
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna
decision: SS N-64 (S-L1 acceptance criterion); verdict-deciding tool, one independent review required before the S-L1 integration PR relies on it
scope: tooling and tests only. The detector is read-only and never writes to the database.
changelog:
  - "2.5 (2026-10-03): hooks_real refreshed to the integration's 23 hook files (04249fdc1; adds ephemeris_backend_shift, the Moshier to Swiss .se1 backend shift hook) + the pending F-A2 hook. The W7 lane list names all 23 stems. The four non-optional dasha_shift entries of ephemeris_backend_shift read DECLARED_BUT_ABSENT on an unchanged native chart BY DESIGN (a rebuild that did not run on se1 fails); the tests pin exactly those four, pair them with a shifted fixture where they read present, and keep the absence rule for every other entry. Golden gains one case (all_24_hooks_unchanged_native_chart); every existing case is byte-identical. Tooling code unchanged."
  - "2.4 (2026-10-03): hooks_real refreshed as byte copies of the S-L1 integration's 22 hook files (c3213fc98) + the pending F-A2 hook; live byte-equality test with an explicit PENDING list; a snapshot of an empty read is refused (exit 5) and nothing is written (atomic write); operator steps and known limits (post-window hardening list) from review R-T3."
  - "2.3 (2026-10-02): second independent review (R-T2) and SS rulings. A table that was not compared (flag or missing snapshot section) is a conditional NOT CHECKED row, flags and skipped sections are recorded in meta, no green ok line for it. --no-dashas / --no-daily with --require-lanes is REFUSED (exit 6) without --i-know-dashas-are-not-compared; the W7 command is written in full below. Reads are ONE REPEATABLE READ READ ONLY transaction; PGOPTIONS read-only and a proven read-only session; timeout; READ_ERROR exit 5 with a report; error text scrubbed. --snapshot never overwrites; the .sha256 is verified on compare. Sort includes the tier. Standing NOT CHECKED registry extended. Full ISO timestamp match. expected_count rejected on dasha_shift; exact must not be a boolean; min <= max. Phantom chart id refused. hooks_real are byte copies of the hook directory with a live comparison and a documented refresh. Empty current native is EMPTY_READ, not ALERT."
  - "2.2 (2026-10-02): delta-review fixes. A timestamp-valued fact that becomes NULL or non-timestamp text is a value change. malformed-report check pinned for a non-list not_checked. README: direction limit of the continuous/integral classification, and a correction note for the sun_required_rupa hook."
  - "2.1 (2026-10-02): fixes from the independent review of PR 2945. A continuous number that becomes NULL/text, and continuous keys that appear or disappear, are now changes (were invisible). New failure class EMPTY_READ (zero rows in a compared table in either state). Chart ids are validated as UUIDs and normalised once. Empty fact_keys / ayanamsha_ids / charts lists, an empty --hooks-dir and an empty --require-lanes are rejected. A single-SELECT guard (no statement chaining). A malformed or truncated report is FAIL (exit 2), never a KeyError. W7 hand-check list added."
  - "2.0 (2026-10-02): moved to platform/scripts/governance with CI-collected tests and mutation proof. New: DECLARED_BUT_ABSENT and KIND_MISMATCH failure classes, optional hook entries, NOT_CHECKED verdict + exit 4 + --allow-not-checked, standing NOT CHECKED registry (chart_dashas tier, l1_tajik_varsha_year_lords tier), 'pr' now required in a hook, missing/empty hooks dir is an error, offline --against compare, --out for --validate-hooks, deterministic JSON. Detector logic for class/tier/dasha diffing and anchors is unchanged from v1.1 (PR 2859)."
  - "1.1: investigation-branch version (PR 2859): snapshot, compare, validate-hooks, anchors, expectation counts."
---

# flip_detector.py: S-L1 flip report and hook validator

`platform/scripts/governance/flip_detector.py` produces the W7 class-flip report for the S-L1 rebuild and validates the per-lane attribution hooks. It reads production through a SELECT-only reader (or two offline snapshots) and decides one **verdict** for the chart it compares.

Tests: `__tests__/test_flip_detector.py` (offline, no database, no network) and `__tests__/test_flip_detector_mutations.py` (mutation proof). Both run in the existing "Governance Tool Tests (pytest)" CI step.

## Verdict classes

| verdict | meaning | exit |
|---|---|---|
| `ALERT` | a FORENSIC anchor changed (native chart only). Beats every other class | 3 |
| `FAIL` | at least one failure class below is non-empty. STOP THE WAVE, GO TO SS | 2 |
| `NOT_CHECKED` | nothing failed, but the detector never examined some scopes (see below). **Never a pass** | 4, or 0 with `--allow-not-checked` |
| `PASS` | nothing failed and nothing is NOT CHECKED. Only reachable when the standing NOT CHECKED registry is empty, which production never is | 0 |

The verdict is decided in exactly one function (`decide_verdict`) from the report's own failure lists; `exit_code` recomputes it, so a stale `verdict` field cannot hide a failure.

### Failure classes (any one makes the verdict FAIL)

| class | when |
|---|---|
| `UNDECLARED_CHANGE` | a changed row/category/column that no loaded hook declares (also: `chart_dashas` row-set change, `panchanga_daily` column or whole date) |
| `KIND_MISMATCH` | a hook declares the category (table + category + fact key + ayanamsha) but not this KIND of change, e.g. the hook says `change_types: ["tier"]` and a value changed. The report names the kinds the hook did declare |
| `DECLARED_BUT_ABSENT` | a hook entry with no `expected_count` that is not marked `"optional": true` saw no change at all (for a `dasha_shift` entry: no shifted row inside its range) |
| `EXPECTATION_MISMATCH` | an entry's `expected_count` (`exact`, or `min`/`max`) was violated for the chart compared. An explicit `{"exact": 0}` or `{"min": 0}` is how a hook says "zero is fine" |
| `DASHA_SHIFT_UNDECLARED` | a dasha start shift larger than 2 s outside every declared `dasha_shift` range |
| `HOOK_ERROR` | a hook file is invalid or unparseable, the hooks directory is missing or has no `*.json`, or a `--require-lanes` lane has no valid hook |
| `EMPTY_READ` | a compared table has zero rows in the snapshot or in the current state. Rule: `chart_facts` and `chart_divisionals` are always compared; `chart_dashas` and `panchanga_daily` when compared (not `--no-dashas` / `--no-daily`). A real chart has rows in each, so zero means the read returned nothing (for example a row-level-security block for the reader); empty-versus-empty would otherwise read as "nothing changed". Exit 2, also with `--allow-not-checked` |

Warning class (never fails): `OPTIONAL_ABSENT`, an entry marked `"optional": true` that saw no change. It is printed and recorded in the JSON `warnings`.

### NOT CHECKED (never silent, never a pass)

The detector prints, on every compare, one `NOT CHECKED` line per item below and records them in the JSON `not_checked` list:

| id | what it cannot check |
|---|---|
| `chart_dashas.tier` | `chart_dashas.verification_pass_status` (tier changes for mudda, narayana, yogini, ashtottari, chara_karaka, naisargika and vimshottari). The detector never compares the tier column (when `chart_dashas` is compared at all it compares row sets and start shifts) |
| `l1_tajik_varsha_year_lords.tier` | `l1_tajik_varsha_year_lords.verification_pass_status`. The table is not one of the four tables the detector reads |
| `chart_vichara` | `chart_vichara` (ga_vichara: row counts, dedupe, sorted `constituent_fact_ids`, leverage as-of). The table is not one of the four tables the detector reads, so **an empty flip report says nothing about ga_vichara**. W7 runs `00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/evidence/ga_vichara_writer_ACCEPTANCE.sql`; every row must read `ok = t` |
| `ga_yoga_firings.strength`, `bodha_msr_signals` (shadbala_norm), `bodha_rm_resonances`, `ga_condition_composite`, `ga_medical`, `ga_vastu_*`, `ga_prashna_*`, `prashna_charts` | tables the detector never reads (the first three are the downstream tables the `sun_required_rupa` lane changes). One line each, hand read-back in "Other tables the detector never reads" below |

**Conditional rows, present only when the check did not run** (a check that did not run is never silent and never a green line):

| id | when |
|---|---|
| `chart_dashas.not_compared` | `--no-dashas`, or the snapshot (or the `--against` snapshot) has no `dashas` section. A real dasha change would read as "no change" |
| `panchanga_daily.not_compared` | `--no-daily`, or a snapshot has no `daily` section |
| `snapshot.sha256` / `against.sha256` | the snapshot has no `.sha256` sidecar: its integrity is unverified (a sidecar that does not match is a `HOOK_ERROR` failure, exit 2) |

For a skipped table the summary prints `n/a  DASHA_SHIFT_UNDECLARED: NOT EVALUATED` (never `ok ... : 0`). **Read this plainly:** with dashas or daily skipped, the other class lines (`ok   UNDECLARED_CHANGE: 0`, `DECLARED_BUT_ABSENT`, `EXPECTATION_MISMATCH`, `EMPTY_READ`) still print as `ok`, because they are computed over the tables that WERE compared and say nothing about the skipped one; only `DASHA_SHIFT_UNDECLARED` prints n/a. What marks the run is the `NOT CHECKED chart_dashas.not_compared` / `panchanga_daily.not_compared` line and `VERDICT: NOT_CHECKED` that follow. The JSON has `compared: {chart_dashas: false, ...}` and `meta.flags` / `meta.skipped_sections` record the flags and the skipped sections, so saved evidence of a skipped run cannot be mistaken for a full compare.

Also reported as NOT CHECKED (per hook entry, `declared_by_lanes` names the lane): any entry on `l1_tajik_varsha_year_lords`, any `chart_dashas` entry whose only change type is `tier`, and any `chart_dashas` / `panchanga_daily` entry when that table was not compared in the run (`--no-dashas`, `--no-daily`). Such an entry is never reported as DECLARED_BUT_ABSENT.

`declared_by_lanes` for the standing items lists the lanes whose hooks have an entry on that table (the `tiers` hook at 59c6efd46 has entries on `chart_dashas` and on `l1_tajik_varsha_year_lords`). A lane that mentions a table only in its `description` text shows an empty list: add an entry with that `table` to the hook to link it.

### W7 hand read-back for the two NOT CHECKED tier changes

Run each query before the rebuild (save the output) and again after, for the chart compared, as a **read-only** reader (a SELECT-only role such as `suvarna_reader`, in a subshell that sources its own credentials; never write). Replace `<CHART_UUID>` (native: `482012f1-710e-4a25-994a-93821f5871aa`). The before/after outputs are compared by eye: the `tier` column is the only thing expected to move, and the `n` per (ayanamsha, system) must not change.

`chart_dashas` (level 1 of every system the tier rule touches, plus non-KP vimshottari), counts per tier value:

```sql
SELECT ayanamsha_id, system_id, level_n, verification_pass_status AS tier,
       count(*) AS n, count(DISTINCT build_id) AS builds
FROM chart_dashas
WHERE chart_id = '<CHART_UUID>'
  AND system_id IN ('mudda', 'narayana', 'yogini', 'ashtottari', 'chara_karaka', 'naisargika', 'vimshottari')
  AND level_n = 1
GROUP BY ayanamsha_id, system_id, level_n, verification_pass_status
ORDER BY ayanamsha_id, system_id, level_n, verification_pass_status;
```

Drop the `level_n = 1` line to see every level (the rule is stated for level 1). `vimshottari_kp` is a different `system_id` and is not in this query.

`l1_tajik_varsha_year_lords`, counts per tier value:

```sql
SELECT ayanamsha_id, verification_pass_status AS tier,
       count(*) AS n, count(DISTINCT build_id) AS builds
FROM l1_tajik_varsha_year_lords
WHERE chart_id = '<CHART_UUID>'
GROUP BY ayanamsha_id, verification_pass_status
ORDER BY ayanamsha_id, verification_pass_status;
```

**Expected tiers after the rebuild (SS final literals; the per-emitter transition table is `tiers_evidence_v1_3.json` in the tier-honesty lane, PR 2941 at 59c6efd46, `evidence/tiers_evidence_v1_3.json` once the integration brings it in):**

| system, level 1 | tier after |
|---|---|
| `mudda` | `classical_match` |
| `narayana`, `yogini`, `ashtottari`, `chara_karaka`, `naisargika` | `single` |
| `vimshottari` (non-KP) | `two_pass_verified` |

`l1_tajik_varsha_year_lords`: the canonical chart's 240 rows go `two_pass_verified` to `single` (the hook: "the three varsha checks are not a classical-table match"), not `classical_match`. Counts per system are the lane evidence's; confirm them against the hook that is actually merged. If `builds` is above 1 for any line the table holds more than one build generation: stop and ask before reading the counts.

## Exit codes

| code | meaning |
|---|---|
| 0 | verdict PASS, or verdict NOT_CHECKED with `--allow-not-checked` (the summary still prints every NOT CHECKED item and states that the exit is 0 only because of the flag). `--validate-hooks`: all hooks valid |
| 2 | verdict FAIL. `--validate-hooks`: any hook error or missing required lane |
| 3 | verdict ALERT (FORENSIC anchor changed). Wins over 2 and 4 |
| 4 | verdict NOT_CHECKED and `--allow-not-checked` not passed |
| 5 | READ_ERROR: the read failed or cannot be trusted (psql failure after retries, a timeout, an incomplete or mis-split result, a session that is not read-only). A report with `verdict: READ_ERROR` is written (`--out`); `--snapshot` exits 5 and writes nothing, including when the read returned **zero rows** in a table that must have rows (`chart_facts`, `chart_divisionals`, and `chart_dashas` / `panchanga_daily` when read): no snapshot, no `.sha256`, no temporary file. The error detail after the fixed "read failed after N attempts: " prefix is cut to 200 characters with DSNs and passwords removed |
| 6 | REFUSED: `--no-dashas` / `--no-daily` together with `--require-lanes` without `--i-know-dashas-are-not-compared`; or `--snapshot` onto an existing file (a baseline is never overwritten; choose another `--out`) |

`--allow-not-checked` only converts exit 4 into 0. It never softens 2 or 3.

Two exits are not produced on purpose and are not in the table: **exit 1** is an uncaught Python traceback (for example a missing or corrupt snapshot file given to `--compare`; treat it as a failure) and **exit 2** is also what argparse returns for a usage error (an unknown flag, a missing argument, an empty `--hooks-dir`, a bad `--snapshot` target). The exit-6 rule for `--no-dashas` / `--no-daily` applies only with `--require-lanes` (the W7 command always passes it).

## Usage

```
# Database access is read-only. FLIP_READER = an executable taking one SQL SCRIPT as argv[1], running it in ONE psql session (every result set
# printed) and printing tab-separated rows without a header (a psql wrapper that sources the reader credentials). Unset: psql from PATH with the
# PG* environment (the script goes on stdin, `psql -f -`). All tables are read in one `BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY ... COMMIT`
# transaction (a concurrent build cannot tear the read); PGOPTIONS gets `-c default_transaction_read_only=on` (yours are kept); nothing is read
# unless the session reports transaction_read_only = on. FLIP_TIMEOUT_SEC (default 120) bounds each attempt.
export FLIP_READER=/path/to/reader_wrapper.sh
export FLIP_SNAPSHOT_DIR=/Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots     # default store; a baseline is never overwritten

python3 platform/scripts/governance/flip_detector.py --snapshot native
python3 platform/scripts/governance/flip_detector.py --validate-hooks --require-lanes <lanes>
python3 platform/scripts/governance/flip_detector.py --compare <snapshot.json.gz> --against <other_snapshot.json.gz> --hooks-dir <dir>   # offline: no database
```

### The W7 command (S-L1 window), written in full

Operator steps, in this order:

1. **Set `FLIP_TIMEOUT_SEC` explicitly** for the production reader (for example `export FLIP_TIMEOUT_SEC=300`). The default is 120 s per attempt; it read about 650k rows in 5 s locally, but the production network read is unmeasured.
2. **Connect directly** to the database, not through a pooler: PgBouncer and similar poolers reject the `PGOPTIONS` the tool sets (`-c default_transaction_read_only=on`) and may not hold one repeatable-read transaction. Avoid reader wrappers too: on a timeout only the direct child is killed, and a wrapper's psql grandchild can survive and keep the transaction open.
3. **Take the W0 baseline** (`--snapshot native`), then **check its row counts** (`chart_facts`, `chart_divisionals`, `chart_dashas`, `panchanga_daily`: the `counts:` line it prints, and per chart) **against the expected before-counts in `HOOKS_W7_HAND_READBACK_v1_0.md` and against the reader's own COUNT queries, before W1 is merged**: once W1 applies, the "before" state is gone and a bad baseline cannot be re-taken. A snapshot of an empty read is now refused (exit 5, nothing written), but a partial or wrong-chart read is saved with a `.sha256` and is never overwritten: **a bad baseline is sticky; re-take it under a new name** (`--out`).
4. Run the command below after the rebuild, then the W7 hand read-backs, then the same command with `--allow-not-checked`.

Dashas and daily are compared; **no `--no-dashas` / `--no-daily`**. The hook directory is the integration's (`00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks`, the default). The lane list is the 23 hook files the integration carries (`TI-s-l1-integration-001` at 04249fdc1; 22 at c3213fc98, plus `ephemeris_backend_shift`).

```
python3 platform/scripts/governance/flip_detector.py \
  --compare <PRE_REBUILD_SNAPSHOT.json.gz> \
  --hooks-dir 00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks \
  --require-lanes argala,argala_other_charts,ashtakavarga_bindu_contributor,band_table,chandra_bala_birth_moon_sign,dasha_scope_cap,ephemeris_backend_shift,ga_condition_fallback,ga_strength_invariant_rows,ga_structural_chart_geometry,ga_vargas_invariant_sentinels,gandanta,karaka_dasha_roles,karaka_roles,karaka_web_order,karaka_web_order_other_charts,sade_sati_placeholder_null,special_lagna_offset,special_lagna_offset_other_charts,sun_required_rupa,tiers,tiers_other_charts,yamakantaka \
  --out <REPORT.json>
# after the W7 hand read-backs are done and recorded, the same command plus:  --allow-not-checked
```

**`fa2_ga_vargas` is required only once PR 2858 lands.** Its hook file (`fa2_ga_vargas.json`) does not exist in the repo's hook directory until then, and naming it in `--require-lanes` before that is a `HOOK_ERROR`. The command above is therefore valid in both states. When #2858 has landed, append `,fa2_ga_vargas` (24 names). `hooks_real` already carries the F-A2 hook (a copy of the F-A2 patch file, sha256 `406437e05eba54afbbeed4ffae126e67d1a7472b807517399e244d89517337f5`) so the CI test for the lane list passes in both states; see "Refreshing hooks_real".

**`ephemeris_backend_shift` and `DECLARED_BUT_ABSENT` (by design).** Its four non-optional `dasha_shift` entries (indices 0 to 3: Vimshottari, Vimshottari KP sub-periods, Kalachakra for four ayanamshas, Kalachakra for Surya Siddhanta) declare that the rebuild ran on the canonical Swiss `.se1` backend, which moves the Moon and so translates the Moon-anchored dasha timelines by the measured amounts. On an UNCHANGED native chart (a rebuild that did not run on se1, or a compare of a state against itself) those four read `DECLARED_BUT_ABSENT` and the verdict is FAIL: that is the proof that such a rebuild fails, not a defect. The hook is scoped to chart `482012f1` only, so no other chart reads them. The tests pin exactly these four entries (`EXPECTED_SHIFT_PROOF_ENTRIES`), assert that they read present on a fixture whose rows really shifted, and keep the absence rule for every other entry of every hook.

`--no-dashas` or `--no-daily` together with `--require-lanes` exits 6 unless `--i-know-dashas-are-not-compared` is also given; even then the report carries `chart_dashas.not_compared` / `panchanga_daily.not_compared` NOT CHECKED rows and the flags in `meta`.

`--hooks-dir` defaults to `00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks` (repo root relative). Every top-level `*.json` in the directory is a lane hook; sub-folders (for example `evidence/`) are never read.

Output: a human summary on stdout and a JSON report (`--out`, else next to the snapshot). The JSON has sorted keys and deterministic ordering; only the `meta` block carries timestamps. Fields: `verdict`, `exit_code`, `failure_counts` and `failures` (per class), `warnings`, `not_checked`, `expectations`, `by_table_category_change_lane`, `dashas`, `anchors`, and the full `changes` list.

## Hook schema

```json
{
  "lane": "fa2_ga_vargas",
  "ruling": "F-A2",
  "pr": "#NNNN",
  "description": "what this fix changes and why (required, non-blank)",
  "charts": ["482012f1"],
  "may_change": [
    {
      "table": "chart_facts",
      "categories": ["varga_position"],
      "fact_keys": ["sign", "sign_id"],
      "ayanamsha_ids": ["lahiri_chitrapaksha"],
      "change_types": ["value", "appeared", "disappeared", "occurrence_count", "tier"],
      "expected_count": {"exact": 150},
      "optional": false,
      "expected_direction": "free text for the reviewer, not machine-checked",
      "note": "free text"
    },
    {
      "table": "chart_dashas",
      "kind": "dasha_shift",
      "systems": ["vimshottari"],
      "shift_range_sec": [6990, 6996]
    }
  ]
}
```

Top level (unknown fields are an error): `lane` (must equal the file stem), `ruling`, `pr` (non-blank string or positive integer: the PR number or branch of the fix), `description` (non-blank), `may_change` (non-empty list), and optional `charts` (chart-id prefixes of 8 or more characters; omitted = every chart).

Entry (`kind` `change`, the default): `table` is one of `chart_facts`, `chart_divisionals`, `chart_dashas`, `panchanga_daily`, or `l1_tajik_varsha_year_lords` (never compared: always NOT CHECKED). `categories` is a non-empty list of **exact** names (no patterns). `fact_keys` and `ayanamsha_ids` narrow the match. `change_types` is a subset of `value`, `appeared`, `disappeared`, `occurrence_count`, `tier` (omitted = all five; for `chart_dashas` only `appeared`, `disappeared`, `tier`). `expected_count` is `{"exact": n}` or `{"min": a, "max": b}`. `optional` (boolean, default false) says that seeing no change is acceptable and downgrades DECLARED_BUT_ABSENT to the OPTIONAL_ABSENT warning.

Entry `kind: dasha_shift`: `table` must be `chart_dashas`, with `systems` (exact `system_id` list) and `shift_range_sec` `[lo, hi]` (seconds, current minus snapshot).

A hook whose `may_change` is empty, or whose entries name no category (or no systems for `dasha_shift`), is invalid.

### Matching and absence rules

A change is attributed to a lane when some entry of an applicable hook has the same `table`, the category in `categories`, the fact key in `fact_keys` (if given), the ayanamsha in `ayanamsha_ids` (if given) **and** the change kind in `change_types`. A change matching the scope but not the kind of any entry is `KIND_MISMATCH`; matching no scope is `UNDECLARED_CHANGE`.

An entry is judged once per compare: by `expected_count` if it has one, else it must have attributed at least one change unless `optional`. An entry belonging to a hook that does not apply to the chart compared (`charts`) is not judged.

### What the detector compares (unchanged from v1.1)

For one chart: every `chart_facts` row (with `verification_pass_status`), every `chart_divisionals` row, every `chart_dashas` row (row set and start shifts), plus the global `panchanga_daily` table. A class change is a changed non-timestamp text, a changed integral number (or any value of a class-numeric key), a key that appears or disappears, or a changed occurrence count. A tier change is a changed `verification_pass_status` for `chart_facts`.

Continuous (non-integral) numbers are judged by their snapshot side: a continuous number that changes to another number (longitudes, strengths) is counted in the `continuous` block and never blocks, but a continuous number that becomes **NULL or text** is a `value` change, and a continuous key that **appears or disappears** is an `appeared` / `disappeared` change (so a hook must declare it). The `continuous` block and the printed summary count `to_non_numeric`, `keys_appeared` and `keys_disappeared`. A timestamp-valued fact that changes to another timestamp is ignored, one that becomes **NULL or non-timestamp text** is a `value` change (counted as `time_to_non_time`), and one that appears or disappears is ignored but counted (`time_keys_appeared`, `time_keys_disappeared`).

**Direction limit (read this before trusting an empty report).** Whether a numeric value is "class" (integral) or "continuous" is judged from the **snapshot side only**. A number that goes from continuous to integral (for example `6.5` to `5`) is therefore invisible: it is counted as a continuous change and never becomes a class change. This only matters when the snapshot is already post-change (a snapshot taken after the lane's rebuild, or an `--against` pair whose first side is the new state); take the snapshot BEFORE the rebuild, as W7 does. The reverse (`5` to `6.5`, integral to continuous) is detected. Dasha shifts of 2 s or less never block.

### Chart ids

`--snapshot` accepts `native`, `abhinandan`, `kiran` or a chart UUID; anything else is refused. Every chart id (operator input, snapshot metadata, the compare itself) goes through one normaliser (trim, braces, lower case) and must be a UUID before it is placed in SQL, compared with the native id for the anchor check, or matched against a hook `charts` prefix. The SQL guard accepts a single `SELECT` only (no statement chaining).

### A saved report is not a verdict

The JSON report's `verdict` and `exit_code` fields are a convenience copy. Do not trust them: `decide_verdict` / `exit_code` recompute the verdict from the report's own `failures`, `failure_counts` and `not_checked`, and a report missing those keys is FAIL (exit 2), never PASS and never a crash. To judge a saved report, recompute; do not read the field.

## W7 hand-check list

The detector cannot see these. The W7 reader does them by hand and records the result with the flip report:

1. **Gandanta, Abhinandan (`1c826d5a`): six `is_gandanta` false-to-true flips** (Mars in `krishnamurti`, `lahiri_chitrapaksha`, `raman`, `true_chitra`; Venus in `raman` and `surya_siddhanta_classical`) are hidden by the sorted-occurrence pairing. For each of the 10 subjects x 5 ayanamshas list **value and `formula_id` per occurrence**, before and after. The canonical and third charts are expected to flip none.
2. **Any key with more than one occurrence**: a value swap between occurrences is invisible (occurrences are paired in sorted order). List every `(ayanamsha, category, subject, key)` with more than one row before or after and compare values by `formula_id` or build order.
3. **The two tier read-backs** above (`chart_dashas` mudda/narayana; `l1_tajik_varsha_year_lords`).
4. **Per-`fact_category` row counts before and after**, and the **NULL count in `argala_natal_matrix`** (rows whose numeric and text values are both NULL), for the chart compared:

```sql
SELECT fact_category, count(*) AS n,
       count(*) FILTER (WHERE fact_value_num IS NULL AND fact_value_text IS NULL) AS n_null
FROM chart_facts
WHERE chart_id = '<CHART_UUID>'
GROUP BY fact_category
ORDER BY fact_category;
```

## Other tables the detector never reads

Each is a standing NOT CHECKED line. The W7 hand read-back is a per-table row count before and after for the chart compared (tables with a `chart_id` column), plus the lane's own column checks named in its hook (for example `ga_yoga_firings.strength`, `bodha_msr_signals.shadbala_norm` for the `sun_required_rupa` lane). Columns of these tables are not known to this tool, so the SQL is a count only:

```sql
SELECT 'ga_yoga_firings' AS t, count(*) AS n FROM ga_yoga_firings WHERE chart_id = '<CHART_UUID>'
UNION ALL SELECT 'bodha_msr_signals', count(*) FROM bodha_msr_signals WHERE chart_id = '<CHART_UUID>'
UNION ALL SELECT 'bodha_rm_resonances', count(*) FROM bodha_rm_resonances WHERE chart_id = '<CHART_UUID>'
ORDER BY 1;
```

Repeat the same shape for `ga_condition_composite`, `ga_medical`, the `ga_vastu_*` and `ga_prashna_*` tables and `prashna_charts` (confirm the table and the chart column name in the schema first; a table without a `chart_id` column needs its own filter).

## Refreshing hooks_real

`__tests__/fixtures/flip_detector/hooks_real/` holds **byte copies** of the integration's hook files: the 23 top-level `*.json` of `00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/` on branch `suvarna/land/TI-s-l1-integration-001` at **04249fdc1** (byte copies; the first copy was the 22 files at **c3213fc98**, each verified against its git blob sha, and `ephemeris_backend_shift.json` was added since), plus **`fa2_ga_vargas.json`**, a copy of the F-A2 patch file (PR 2858; sha256 `406437e05eba54afbbeed4ffae126e67d1a7472b807517399e244d89517337f5`) that PR will add to the same directory.

`test_f12_hooks_real_are_byte_copies_of_the_integration_hook_directory` compares them live with the repo's hook directory (or `FLIP_INTEGRATION_HOOKS_DIR`) and fails on any drift, missing or extra file, **except** the names in the short explicit `PENDING_HOOKS` list at the top of the test file (initially `fa2_ga_vargas.json`): a pending file may be ABSENT from the repo directory (until #2858 lands) and must be byte-equal when present; pending never excuses a present file that differs, and a pending file present in the directory but missing from `hooks_real` is drift. When #2858 lands, empty `PENDING_HOOKS` (and make the lane list 24 names in the command above).

Refresh procedure, from the repo root with the integration's tree checked out (or `FLIP_INTEGRATION_HOOKS_DIR` set to its `s_l1_attribution_hooks/` directory); to refresh from the integration branch without checking it out, use `git show <sha>:<path>` per file instead of `cp`:

```
HOOKS=00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks          # or the path in FLIP_INTEGRATION_HOOKS_DIR
FX=platform/scripts/governance/__tests__/fixtures/flip_detector/hooks_real
cp "$FX"/fa2_ga_vargas.json /tmp/fa2_ga_vargas.json                        # keep the pending F-A2 copy while #2858 is open
rm -f "$FX"/*.json && cp "$HOOKS"/*.json "$FX"/                           # top-level *.json only; evidence/ is never copied
[ -f "$FX"/fa2_ga_vargas.json ] || cp /tmp/fa2_ga_vargas.json "$FX"/      # only while fa2_ga_vargas is still pending
python3 platform/scripts/governance/flip_detector.py --validate-hooks --hooks-dir "$FX"
FLIP_DETECTOR_REGEN_GOLDEN=1 python3 -m pytest platform/scripts/governance/__tests__/test_flip_detector.py -q   # regenerates golden_flip_detector_expected.json
git diff -- platform/scripts/governance/__tests__/fixtures   # READ the golden diff: it must be explained by the hook changes
python3 -m pytest platform/scripts/governance/__tests__/test_flip_detector.py -q                                   # must pass without the env var
```

Then update `GOLDEN_LANES` in the test file if its lanes changed. Once the repo's own hook directory exists in the tree the comparison never skips (in CI or locally); it skips only while that directory is absent. `FLIP_INTEGRATION_HOOKS_DIR` set to a path that does not exist fails the test.

## Documented limits (not fixed)

* **Pairing by sorted occurrence.** Keys with more than one occurrence pair in sorted (value, number, tier) order; a swap of values between occurrences, or an individual flip masked by the pairing, is invisible (W7 hand-check items 1 and 2).
* **Hand-edited snapshots.** A snapshot is trusted for its shape beyond the checks above (types of numbers and levels as written by `--snapshot`); a hand-edited snapshot with other JSON types can crash or mis-pair. Do not edit snapshots; the `.sha256` sidecar exists to catch it.
* **`chart_divisionals` text versus sign.** The comparison value is `fact_value_text` when present, else `sign`. The ga_vargas writer sets both (`ga_vargas_writer.py`, rows built around lines 994 and 1072), so a change in `sign` alone with an unchanged `fact_value_text` is invisible. Whether every other writer fills both has not been verified.
* **Continuous to integral** is invisible (see the direction limit above).

## Known limits (post-window hardening list)

Found by the independent reviews, not fixed before the window; each is named so it is not lost:

* **`_scrub` gaps.** The error scrub removes DSNs and `password=`-style pairs only; other shapes of secret in a psql error are not recognised (the detail is also cut to 200 characters, which limits but does not remove the risk).
* **Grandchild kill on timeout.** A timeout kills only the direct child process; a reader wrapper's psql grandchild can survive and keep the transaction open. Use psql directly (no wrapper).
* **Retry sleeps on permanent errors.** Retries sleep 5, 10 and 15 s even for errors that cannot recover (bad credentials, missing table): worst case about 8.5 minutes with no output when each attempt also times out at 120 s.
* **Poolers.** `PGOPTIONS` is rejected by poolers such as PgBouncer; connect directly.
* **Production read time is unmeasured** (about 650k rows read in 5 s locally); set `FLIP_TIMEOUT_SEC` explicitly.
* **Five surviving mutants / test-coverage gaps N1, N7, N11, N15, N16** from review R-T3: behaviours the suite does not yet pin.
* **Exit codes.** A missing or corrupt snapshot file given to `--compare` ends in a Python traceback (exit 1), not a defined code.

## What the detector cannot check

* The two tier changes in NOT CHECKED above. They need the hand read-back.
* A numeric fact that is non-integral on the snapshot side is treated as continuous: a hook entry declaring a change in such a key can never be observed and reads DECLARED_BUT_ABSENT (mark it `optional` or give it an explicit zero `expected_count`).
* Facts keyed identically by the writer (for example `formula_id` variants) are told apart only by occurrence order, so an individual flip masked by the sorted pairing is invisible (the hook for the Gandanta lane documents one such case).
* Anchors are checked for the native chart only, from `chart_facts`.
* Tables outside the four it reads (bodha, kala, phala, mimamsa tables, yoga firings, and so on).

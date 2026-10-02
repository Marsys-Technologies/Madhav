---
artifact: FLIP_DETECTOR_README
version: 2.2
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna
decision: SS N-64 (S-L1 acceptance criterion); verdict-deciding tool, one independent review required before the S-L1 integration PR relies on it
scope: tooling and tests only. The detector is read-only and never writes to the database.
changelog:
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
| `chart_dashas.tier` | `chart_dashas.verification_pass_status` (mudda and narayana tier changes). The detector compares dasha row sets and start shifts, never the tier column |
| `l1_tajik_varsha_year_lords.tier` | `l1_tajik_varsha_year_lords.verification_pass_status`. The table is not one of the four tables the detector reads |
| `chart_vichara` | `chart_vichara` (ga_vichara: row counts, dedupe, sorted `constituent_fact_ids`, leverage as-of). The table is not one of the four tables the detector reads, so **an empty flip report says nothing about ga_vichara**. W7 runs `00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/evidence/ga_vichara_writer_ACCEPTANCE.sql`; every row must read `ok = t` |

Also reported as NOT CHECKED (per hook entry, `declared_by_lanes` names the lane): any entry on `l1_tajik_varsha_year_lords`, any `chart_dashas` entry whose only change type is `tier`, and any `chart_dashas` / `panchanga_daily` entry when that table was not compared in the run (`--no-dashas`, `--no-daily`). Such an entry is never reported as DECLARED_BUT_ABSENT.

`declared_by_lanes` for the two standing items lists the lanes whose hooks have an entry on that table. A lane that mentions the table only in its `description` text (as `tiers.json` does for the Tajik table) shows an empty list: add an entry with `"table": "l1_tajik_varsha_year_lords"` to the hook to link it.

### W7 hand read-back for the two NOT CHECKED tier changes

Run each query before the rebuild (save the output) and again after, for the chart compared, as a **read-only** reader (a SELECT-only role such as `suvarna_reader`, in a subshell that sources its own credentials; never write). Replace `<CHART_UUID>` (native: `482012f1-710e-4a25-994a-93821f5871aa`). The before/after outputs are compared by eye: the `tier` column is the only thing expected to move, and the `n` per (ayanamsha, system) must not change.

`chart_dashas` (mudda and narayana), counts per tier value:

```sql
SELECT ayanamsha_id, system_id, verification_pass_status AS tier,
       count(*) AS n, count(DISTINCT build_id) AS builds
FROM chart_dashas
WHERE chart_id = '<CHART_UUID>'
  AND system_id IN ('mudda', 'narayana')
GROUP BY ayanamsha_id, system_id, verification_pass_status
ORDER BY ayanamsha_id, system_id, verification_pass_status;
```

`l1_tajik_varsha_year_lords`, counts per tier value:

```sql
SELECT ayanamsha_id, verification_pass_status AS tier,
       count(*) AS n, count(DISTINCT build_id) AS builds
FROM l1_tajik_varsha_year_lords
WHERE chart_id = '<CHART_UUID>'
GROUP BY ayanamsha_id, verification_pass_status
ORDER BY ayanamsha_id, verification_pass_status;
```

What the `tiers` lane hook says to expect on the canonical chart (from its description; confirm against the hook that is actually merged): mudda 240 and narayana 105 level-1 rows `two_pass_verified` to `classical_match`; `l1_tajik_varsha_year_lords` 240 rows `two_pass_verified` to `classical_match`. If `builds` is above 1 for any line the table holds more than one build generation: stop and ask before reading the counts.

## Exit codes

| code | meaning |
|---|---|
| 0 | verdict PASS, or verdict NOT_CHECKED with `--allow-not-checked` (the summary still prints every NOT CHECKED item and states that the exit is 0 only because of the flag). `--validate-hooks`: all hooks valid |
| 2 | verdict FAIL. `--validate-hooks`: any hook error or missing required lane |
| 3 | verdict ALERT (FORENSIC anchor changed). Wins over 2 and 4 |
| 4 | verdict NOT_CHECKED and `--allow-not-checked` not passed |

`--allow-not-checked` only converts exit 4 into 0. It never softens 2 or 3.

## Usage

```
# database access is read-only: FLIP_READER = executable taking the SQL string as argv[1], printing tab-separated rows without a header
# (a psql wrapper that sources the reader credentials). Unset: psql from PATH with the PG* environment. Only SELECT is ever sent.
export FLIP_READER=/path/to/reader_wrapper.sh
export FLIP_SNAPSHOT_DIR=/Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots     # default store

python3 platform/scripts/governance/flip_detector.py --snapshot native
python3 platform/scripts/governance/flip_detector.py --validate-hooks --require-lanes argala,gandanta,fa2_ga_vargas,tiers,band_table,daridra,ephemeris,formula_pins
python3 platform/scripts/governance/flip_detector.py --compare <snapshot.json.gz> --require-lanes argala,gandanta,... --out report.json
python3 platform/scripts/governance/flip_detector.py --compare <snapshot.json.gz> --against <other_snapshot.json.gz>   # offline: no database
python3 platform/scripts/governance/flip_detector.py --compare <snapshot.json.gz> --allow-not-checked                  # after the hand read-back
```

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

## Correction to a hook note (sun_required_rupa)

The `sun_required_rupa` hook's first entry says the predicted class-level count for `required_rupa` is 0 because "both values are continuous". That is wrong for the canonical case: the old value is the integral `5` (5.0), so `required_rupa` 5 to 6.5 (SUN, ayanamsha INVARIANT) **is** detected, as one `value` change per chart (the golden test pins it). Only `ratio` (1.694 to 1.3031, and so on) is continuous and unreported. If a snapshot ever stored the old value non-integrally, the entry would read DECLARED_BUT_ABSENT. The hook file lives in its own lane PR and is not edited here; the `hooks_real` fixture is a byte copy of it and keeps the wrong note on purpose.

## What the detector cannot check

* The two tier changes in NOT CHECKED above. They need the hand read-back.
* A numeric fact that is non-integral on the snapshot side is treated as continuous: a hook entry declaring a change in such a key can never be observed and reads DECLARED_BUT_ABSENT (mark it `optional` or give it an explicit zero `expected_count`).
* Facts keyed identically by the writer (for example `formula_id` variants) are told apart only by occurrence order, so an individual flip masked by the sorted pairing is invisible (the hook for the Gandanta lane documents one such case).
* Anchors are checked for the native chart only, from `chart_facts`.
* Tables outside the four it reads (bodha, kala, phala, mimamsa tables, yoga firings, and so on).

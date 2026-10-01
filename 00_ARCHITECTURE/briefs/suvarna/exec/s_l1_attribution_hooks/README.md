---
artifact: S_L1_ATTRIBUTION_HOOKS_README
version: 1.0
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna
date: 2026-10-02
decision: SS N-64 (S-L1 acceptance criterion) + SS standing rule (every S-L1 mandatory fix PR adds its OWN hook in the same PR)
scope: docs/tooling only. The detector is read-only and never writes to the database.
changelog:
  - "1.0 (2026-10-02): per-lane hook files, schema, matching rules, committed detector + self-test. Seeded with argala and gandanta only."
---

# S-L1 attribution hooks and the class-flip detector

## What this is for

After the S-L1 rebuild of the canonical chart, `flip_detector.py --compare` diffs production against the pre-rebuild snapshot and must be able to say, for every class-level difference, **which ruled change caused it**. A difference no hook claims is **UNATTRIBUTED**: stop the wave and go to SS. A changed FORENSIC anchor is an **ALERT**. The expected outcome of the backend fix itself is zero class flips (BOUNDARY_FLIP_REPORT_v1_0.md).

**Standing rule: every S-L1 mandatory fix PR adds its own hook file in this folder in the same PR** (exact fact categories/tables/columns it may change, expected direction and count where known). One file per lane, so PRs never touch the same file. **A lane with no hook file is a blocker: S-L1 REVIEW must flag it.** An empty placeholder file is not allowed (the loader rejects it); leave the file absent until the lane author writes the real one. There are no pattern or regex matches anywhere: names are exact.

## Files

| file | role |
|---|---|
| `<lane>.json` | one hook per lane, file stem == `lane` (e.g. `argala.json`, `gandanta.json`, `fa2_ga_vargas.json`, `tiers.json`, `band_table.json`, `daridra.json`, `ephemeris.json`, `formula_pins.json`). Every `*.json` in this folder is loaded. |
| `flip_detector.py` | the detector (read-only): `--snapshot`, `--compare`, `--validate-hooks` |
| `test_flip_detector.py` | offline self-test, no database: `python3 test_flip_detector.py` (also pytest-collectable) |
| this README | schema and semantics |

Seeded now: `argala.json`, `gandanta.json` (the two lanes whose categories are grounded in the stored data). Not seeded and not guessed: Daridra, F-A2, band table, tiers, ephemeris, formula pins.

## Hook file schema (exact)

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
      "expected_direction": "free text, e.g. 'house_from_varga_lagna: 12 rows move by +1'",
      "expected_count": {"exact": 150},
      "note": "free text"
    },
    {
      "table": "chart_dashas",
      "kind": "dasha_shift",
      "systems": ["vimshottari"],
      "ayanamsha_ids": ["lahiri_chitrapaksha"],
      "shift_range_sec": [6990, 6996],
      "note": "Moon -0.665 arcsec x 16 y period"
    }
  ]
}
```

Top-level fields (unknown fields are an error):

| field | required | meaning |
|---|---|---|
| `lane` | yes | must equal the file stem |
| `ruling` | yes | the name printed in attribution (e.g. `argala`, `Gandanta`, `F-A2`, `Daridra`, `tiers`, `band table`) |
| `description` | yes | non-blank: what the fix changes |
| `pr` | no | PR number or branch of the fix |
| `charts` | no | list of chart-id prefixes (>= 8 chars). Omitted = applies to every chart compared. A chart not listed is not covered by this hook |
| `may_change` | yes | **non-empty** list of entries |

Entry fields, kind `change` (the default):

| field | required | meaning |
|---|---|---|
| `table` | yes | `chart_facts`, `chart_divisionals`, `chart_dashas` or `panchanga_daily` |
| `categories` | yes, non-empty | **exact** names, no patterns. `chart_facts` / `chart_divisionals`: `fact_category`. `panchanga_daily`: the column name (`tithi_id`, `paksha`, `vara_id`, `nakshatra_id`, `moon_nakshatra`, `yoga_id`, `karana_id`, `karana_second_id`, `tithi_name`, `vara`, `yoga`, `karana`; a whole missing/extra date is category `row`). `chart_dashas`: the `system_id` (row-set changes only, see below) |
| `fact_keys` | no | exact `fact_key` list (`chart_facts`, `chart_divisionals`). Omitted = every key of those categories |
| `ayanamsha_ids` | no | exact list. Omitted = every ayanamsha (including `INVARIANT`) |
| `change_types` | no | subset of `value`, `appeared`, `disappeared`, `occurrence_count`, `tier`. Omitted = all five |
| `expected_direction` | no | free text for the reviewer; **not machine-checked** |
| `expected_count` | no | `{"exact": n}` or `{"min": a, "max": b}`: the number of changes this entry must attribute **for the chart compared**. A count outside the bound is an EXPECTATION MISMATCH (exit 2) |
| `note` | no | free text |

Entry kind `dasha_shift` (`"kind": "dasha_shift"`, `table` must be `chart_dashas`): declares that dasha **start timestamps** of the listed `systems` (exact `system_id`: `vimshottari`, `vimshottari_kp`, `kalachakra`, `mudda`, `yogini`, `ashtottari`, `chara_karaka`, `naisargika`, `narayana`) may move by an amount inside `shift_range_sec` `[lo, hi]` (seconds, current minus snapshot), optionally restricted by `ayanamsha_ids`. This is how the ephemeris lane declares the ruled backend shift (e.g. Lahiri Vimshottari +6,993 s). No `categories`/`fact_keys`/`expected_count` on this kind.

## What the detector compares and how a difference is matched

Reads (SELECT only) for one chart: every `chart_facts` row (with `verification_pass_status`), every `chart_divisionals` row, every `chart_dashas` row, plus the global `panchanga_daily` table. Rows are grouped by natural key; keys the writers emit more than once (e.g. `esoteric_point_yogi`) keep every occurrence and are compared in order.

A **class change** is one of: a text value that is not a timestamp changes; an integer-valued numeric value changes (`pada`, `house_d1`, `sign_num`, ids, or any numeric that is integral on both sides); a key appears or disappears (`appeared` / `disappeared`; an appearing continuous or timestamp value is ignored); the number of occurrences of a key changes (`occurrence_count`). A **tier change** is a changed `verification_pass_status` (`tier`). A **dasha row-set change** is a `chart_dashas` row (matched by ayanamsha, system, level, lord path, then nearest start within 10 days) that exists on one side only (`appeared` / `disappeared`, category = `system_id`). **Not class changes** (reported separately, never blocking): continuous values (longitudes, degrees, strengths), timestamp-valued facts, and dasha start shifts of 2 s or less. A dasha start shift larger than 2 s is blocking unless a `dasha_shift` entry covers it (every shifted row must lie inside some declared range).

**Matching.** A change is attributed to a lane when **some entry of that lane's hook** (lane applies to the chart) has the same `table`, the change's category in `categories`, the change's fact key in `fact_keys` (if given), its ayanamsha in `ayanamsha_ids` (if given) and its type in `change_types`. Matching is exact string equality. A change may be claimed by several lanes (all are listed); it counts toward each matching entry's `expected_count`.

**UNATTRIBUTED** = a class change, tier change or dasha row-set change that no entry of any loaded hook matches, **or** a dasha start shift outside every declared range. Any unattributed item means exit code 2 (stop the wave, go to SS). Missing hooks therefore surface as unattributed changes, and `--require-lanes a,b,c` additionally fails (exit 2, `MISSING HOOK`) when a named lane has no valid hook file, even if its fix happened to change nothing.

**Anchors** (native `482012f1` only): Sun = Capricorn, Moon = Purva Bhadrapada, Lagna = Aries (all five ayanamshas), Tithi = Shukla Tritiya, Vara = Ravivara, Yoga = Shiva, Karana = Garaja, read from the current production `chart_facts`. Any deviation is an ALERT (exit 3, wins over 2), independent of hooks.

## Exit codes

| code | meaning |
|---|---|
| 0 | clean: every class/tier/dasha-row change attributed, every dasha shift covered, every `expected_count` met, hooks valid, anchors OK |
| 2 | STOP THE WAVE, GO TO SS: unattributed change, unattributed dasha shift, expectation mismatch, invalid/unparseable hook file, or a required lane missing |
| 3 | ALERT: a FORENSIC anchor changed |

## Usage

```
# database access is read-only: FLIP_READER = executable taking the SQL string as argv[1], printing tab-separated rows without a header
# (a psql wrapper that sources the reader credentials). Unset: psql from PATH with the PG* environment. Only SELECT is ever sent.
export FLIP_READER=/path/to/reader_wrapper.sh
export FLIP_SNAPSHOT_DIR=/Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots     # default store

python3 flip_detector.py --snapshot native                       # baseline (also: abhinandan, kiran, or a chart UUID)
python3 flip_detector.py --validate-hooks --require-lanes argala,gandanta,fa2_ga_vargas,tiers,band_table,daridra,ephemeris,formula_pins
python3 flip_detector.py --compare <snapshot.json.gz> --require-lanes argala,gandanta,...   # after the rebuild
python3 test_flip_detector.py                                    # offline self-test
```

The canonical chart's pre-rebuild snapshot (taken 2026-10-01T19:50Z, path and sha256) is recorded in BOUNDARY_FLIP_REPORT_v1_0.md section 0A. Snapshots stay in the evidence directory, not in git.

## Writing a hook (lane authors)

1. Name the file `<lane>.json`; set `lane` to the same stem.
2. List every table / exact category / (optionally) key / ayanamsha your fix may change. Be exact: a category you forgot will surface as UNATTRIBUTED during S-L1, which is the point.
3. Add `expected_count` where you know it (it turns "attributed" into "attributed and as predicted") and `expected_direction` as a note for the reviewer.
4. Run `python3 flip_detector.py --validate-hooks` and `python3 test_flip_detector.py`; both must pass.
5. Do not edit another lane's file. If two lanes touch the same category, each lists it; the detector attributes the change to both.

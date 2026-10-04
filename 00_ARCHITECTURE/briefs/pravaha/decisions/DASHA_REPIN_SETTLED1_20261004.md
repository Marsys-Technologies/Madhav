---
artifact: DASHA_REPIN_SETTLED1_20261004
version: "1.0"
status: RECORD — the AM-10 daśā re-pin at SETTLED-1, as adopted; the code is PR #2999 (pravaha/a53-am5-inventory)
date: 2026-10-04
author: Stream B (Śāstra), session madhav-8b, at the steward's request (M20261004T084438-926a, Fable's note that the rulings were not in-tree)
evidence: "/Users/Dev/pravaha/run/sl1-capture-20261004/official/ (settled1_notice.json, official-dryrun-full.txt, post_record.out, forensic_ga_positions_job.log, rulings_adopted.json, repin-apply-evidence.md, repin-apply-stdout.txt, repin-diff.patch); the pre-S-L1 capture /Users/Dev/pravaha/run/sl1-capture-20261004/old_dasha_capture.json (data sha d6a9b80d…e5d6)"
changelog:
  - "1.0 (2026-10-04): first version."
---

# AM-10 daśā re-pin at SETTLED-1 — the record

Nothing in this file authorises anything. It puts into the tree what the steward ruled and what three reviews concluded, so the decision does not live only in a message.

## 1. The SETTLED-1 values
| item | value |
|---|---|
| chart | `482012f1-710e-4a25-994a-93821f5871aa` (Vimśottarī, `lahiri_chitrapaksha`) |
| old pin (first pin, verified 2026-09-30) | `1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb` |
| new build | `75524b3e-102a-43ec-8cee-3f57fee752c3` — the only `build_id` in `chart_dashas` (483,855 rows; 45 non-scope + 1 scope_cap partition pairs) |
| expected shift (notice) | 6993 s at all three levels; tolerance 35 s |
| measured shift | MD and AD exactly +6993 s; PD +6992 or +6993 (two PD starts +6992: 1-second rounding); lords unchanged; rows L1–L3 13 / 104 / 923 unchanged; L4 8,165 → 8,177 |
| issuer | Suvarṇa SS (madhav-06); the notice carries `Suvarna SS madhav-06 SETTLED-1 2026-10-04T08:15Z`. The tracker stamped the steward's relay at 08:10:16Z and the database showed the final state at 08:10:44Z: the "08:15Z" is the sender's own clock (about 3–5 minutes ahead of the tracker's), recorded here so the audit trail says which clock it is |
| steward's received id | `M20261004T081016-d079` (SETTLED-1-RECEIVED) |
| notice file | `official/settled1_notice.json`, sha256 `e6f6f29b31c0137bbec974f2b122bc06639e3156ac928f0094f6eb28052b3343` |
| FORENSIC | Suvarṇa's evidence (`/Users/Dev/suvarna-evidence/S_L1/window/W3/`; 47 gate lines passed=True, 0 False; detector 7 of 7 anchors OK). The re-pin tool checks only that the forensic file exists and is non-empty; `CLEAN` is not validation of the seven anchors. Job log `official/forensic_ga_positions_job.log`, sha256 `eed22a05ef218841bab23ec556a5d39658024e9fa1e8373ea2dce7603944dc5f` |

## 2. The official dry-run result
Reviewed tool `5a46c9c97` (PR #2903), `--dry-run`, against the notice above: verdict **CLEAN**. Rows 13 / 104 / 923 old = new; matched 1040; only-old 0; only-new 0; orphans 0; duplicates 0; lord flips 0 (D7). 34 boundary-sensitive oracle instants (17 boundaries × 2; D8). Ten reference rows re-measured (their old → new ids and instants are in `official-dryrun-full.txt` §3 and now in `permission.py`). `official-dryrun-full.txt` sha256 `b472771a2bf06cbf844a8a9b1f1661388543100d74b8a9a1a275de55c24cf4b4`; it is line-for-line identical to the PRELIMINARY run of 07:41Z on the same build except the two hash lines.

Post record (`settled1_post_record.sql`, sha256 `8025ae9d77aded5cadbde12ef92e121512847838e4e9eb1f2499ab864422d625`, one READ ONLY transaction): `official/post_record.out`, sha256 `d3819b93b28df4c6f6f5218758521b8f606276b9a46970e5c5c0c3f91b3bf1f6`. Stream B re-ran it independently at 08:11:38Z: the 65 data rows are identical.

## 3. The rulings adopted (verbatim `official/rulings_adopted.json`, sha256 `c9d8cbb3a27a820e034614e963a04317cb6beb4b9453c32de14cd76de864e621`)
```json
{
 "rewrite": [
  "platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py:403",
  "platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py:404",
  "platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py:660",
  "platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py:670",
  "platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py:671",
  "platform/python-sidecar/tests/l3/gochara_rules/test_pp.py:21",
  "platform/python-sidecar/tests/l3/gochara_rules/test_pp.py:51",
  "platform/python-sidecar/tests/l3/gochara_rules/test_pp.py:109"
 ],
 "keep": [
  "platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py:864",
  "platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py:865",
  "platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py:866",
  "platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py:867",
  "platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py:868",
  "platform/python-sidecar/tests/l3/gochara_rules/test_am10_repin_tool.py:227",
  "platform/python-sidecar/tests/l3/gochara_rules/test_am10_repin_tool.py:228",
  "platform/python-sidecar/tests/l3/gochara_rules/test_am10_repin_tool.py:1348",
  "platform/python-sidecar/tests/l3/gochara_rules/test_am10_repin_tool.py:1371"
 ]
}
```
8 rewritten and 14 retained literals (the retained: step06b 864–868 carry two literals each, = 10, plus the four tool-fixture lines = 14). Principle: a literal that asserts against the pinned production data follows the data (rewrite); a literal inside a self-contained synthetic fixture, or a fixture of the tool's own tests, keeps its old value.

**Ruled in afterwards (steward, during the apply):** (a) `tests/l3/gochara_rules/test_pp.py:117` — `just_before = "2020-02-14T11:47:22Z"` → `"2020-02-14T13:43:55Z"`, a hand edit (one second before the moved Mars→Rahu boundary); (b) seven non-`Z` forms of the same boundary in `tests/l3/gochara/test_step06b_per_instant_permission.py`, which the tool's `Z`-only literal search could not see: `:284` the `BOUNDARY = datetime(2020, 2, 14, 11, 47, 23, tzinfo=UTC)` constructor, `:341` the `startswith("2020-02-14T11:47:23")` assertion, `:346` the docstring time, `:687` the `utc_iso_of_jd(...) < "2020-02-14T11:47:23"` comparison, `:692` and `:694` the two `+00:00` forms, `:697` the `11:47:22.999999+00:00` form — all now `13:43:56` (`13:43:55.999999` for the last).

## 4. The lock
`services/gochara_kernel/implementation_digest.lock.json`: aggregate `73f67d223640b1d6a10710d12b17e122a682a0a04a9950486b1ae6f307c81f9d` → `fcfb68271244ecca53f3fddca2ecfd7f32a0394d060e9a0bed924e19838c4c39`; only the `evaluation` stage moved, `2bd30ecf53b24931dca99b47b10ad562b9422ac0694c1e73c40e24f9ca35c500` → `d291e4a0a5253a1c38348de0f52480140c63b4cf5b3661592f0389a8e4f90670`; `geometry` `535e05b0…` and `window` `fdb8f9b7…` unchanged. Both edited modules (`inventory_verifier`, `permission`) belong to the evaluation stage; `ka_gochara_v5` (also evaluation) is byte-unchanged. `implementation_registry --check` = current.

## 5. The code and the three reviews
Chain on PR #2999: `e44f9fe2d` → `d0fcce3b2` (the re-pin) → `3adf3c4ba` (writer digests) → `49b596bd9` (census) → `e348f1302` (merge of `main` `5ff71f341`) → `6bb74b851` (census regenerated). 15 files, +134/−99 for the re-pin delta; window files, workflow, `migrate.ts`, 1241 untouched.
| reviewer | verdict | file |
|---|---|---|
| Codex gpt-6-astra | **ACCEPT**, may enter the train — YES (87 passed, 7 pre-existing expected failures) | `reviews/ASTRA_REVIEW_DASHA_REPIN_DELTA_v1_0.md` |
| Fable (outside review) | **ACCEPT_WITH_AMENDMENTS**, train YES; none gates entry | `reviews/FABLE_REVIEW_DASHA_REPIN_DELTA_v1_0.md` |
| Stream B (second eyes) | **AGREE** at 49b596bd9 and at 6bb74b851 (clean synchronisation) — recomputed arithmetic, programmatic row comparison, ten rows read from production `chart_dashas` read-only, lock stage check, whole-tree old-boundary search in every textual form; 68 passed / 7 documented A5.5 xfails locally | tracker report `M20261004T083740-264b` |

## 6. Follow-ups (none blocks the train)
- **A1 (Fable)** `scripts/kala_gochara_cutover/step06b_windows_projection.py:412` — comment instant `2020-02-14T11:47:23Z` → `13:43:56Z` (comment only; a production script, touched only with a reviewed change).
- **A2 (Fable)** stale row-id comments naming the old ids: `tests/l3/gochara_rules/test_rp_oracles_a55.py:220` (wrapped across two lines, which the tool's exact-string rewrite could not match), `tests/l3/gochara_rules/test_rr.py:65` and `:67`.
- **A3 (Fable)** the generated `test_am10_repin_75524b3e.py` cites a generator that is not in this tree: cite its branch/commit or drop the claim; and keep `rulings_adopted.json`'s content in-tree (this file does that).
- **A4 (Fable)** regenerate `golden_brief_*_1class.*` once from the committed head so `runner/commit` and `implementation_digest` are a real pair (cosmetic).
- **Tool (Stream B, the improved branch of #2903):** (i) search for the old boundaries in non-`Z` forms — space separator, `+00:00`, other offsets incl. IST with its date shift, epoch seconds, `datetime(y, m, d, h, mi, s)`, compact and Julian-day forms; (ii) match old ids split across a line wrap; (iii) widen the scan beyond `tests/l3/**` (`platform/tests/**`, `**/__tests__/**`) and report what it finds as KEEP candidates (three TypeScript `.db.test.ts` files and `test_flip_detector.py` seed their own old-instant rows; they do not reference the pins).

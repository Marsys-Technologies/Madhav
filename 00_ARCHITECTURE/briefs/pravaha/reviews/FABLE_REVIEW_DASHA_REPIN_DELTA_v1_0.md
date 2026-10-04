---
artifact: FABLE_REVIEW_DASHA_REPIN_DELTA
version: "1.0"
reviewer: "Fable (outside review on the owner's behalf)"
date: 2026-10-04
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: 49b596bd9
reviewed_range: e44f9fe2d..49b596bd9
branch: pravaha/a53-am5-inventory
authority: "Review only; authorizes nothing."
---

# Outside review — AM-10 daśā re-pin delta (1f89fd4c → 75524b3e)

**Method.** Read-only. Every claim below was verified by reading the tree at `49b596bd9` (`git show`, `git diff`, `git grep`, `git ls-tree`, `git merge-base`) or by Python arithmetic over the evidence file. No tracked file was modified; no test was executed; no database or network service was touched. The three evidence files (`OFFICIAL_DRYRUN_EVIDENCE.txt`, `RULINGS_ADOPTED.json`, `POST_RECORD.out`) were read as untracked inputs in the checkout root; their own provenance was not verified (see finding 6).

**Headline.** The re-pin is correct, minimal and internally consistent: both governed pins carry the new build, all ten reference rows equal the evidence's new values exactly, the implementation-digest lock recomputes byte-for-byte from the committed tree (verified independently for both the base and the head), and the rewritten test literals each still assert something that would fail under the old data. Nothing outside the declared scope changed. The amendments are comment/doc hygiene and one provenance oddity in a regenerated golden fixture; none gates entry.

---

## 1. Scope

**Verdict: in scope. No migration, workflow, writer or kernel-logic change.**

- `git -C <wc> diff --name-status e44f9fe2d 49b596bd9` lists exactly 15 paths: `implementation_digest.lock.json` (M), `gochara_kernel/inventory_verifier.py` (M, one line), `gochara_rules/permission.py` (M), two golden fixtures under `tests/l3/gochara/fixtures/` (M), seven test files (M), `tests/l3/gochara_rules/test_am10_repin_75524b3e.py` (A), `platform/src/generated/capability_estate_census.json` (M), `platform/src/generated/nirmana-writer-digests.json` (M). `--stat`: 15 files, +134/−99, matching the brief.
- Explicit no-touch confirmation: `git diff --stat e44f9fe2d 49b596bd9 -- platform/migrations` → empty; `-- .github` → empty; `-- platform/python-sidecar/pipeline` → empty (so `pipeline/orchestrator/writers/ka_gochara_v5.py` is untouched); `-- platform/python-sidecar/ka_writers` → empty; `-- platform/python-sidecar/services/gochara_kernel` → only the lock JSON and the one-line `_C_BUILD` constant at `inventory_verifier.py:664`.
- Kernel logic: the only kernel-side hunk is `-_C_BUILD = "1f89fd4c-…"` / `+_C_BUILD = "75524b3e-…"`. The lock recompute in finding 3 independently proves no other module in `input_vector.IMPLEMENTATION_MODULES` changed (geometry and window stage digests are identical before and after; only `evaluation` moved, and it contains both `inventory_verifier` and `permission`).
- The two generated JSON changes are explained without any writer edit: `asset_runner.get_writer_source_hash` (lines 406–415) hashes the writer **plus its local import closure** (`_writer_source_files`, line 369 ff.), so `ka_gochara_v5` and `ka_gochara_v4_41_candidate` digests move because `permission.py`/`inventory_verifier.py` are in their closure. The census then re-fingerprints the digest inventory (`sha256` of `nirmana-writer-digests.json` at census line 22438; `source_revision` → `3adf3c4ba`).
- Base sanity: `e44f9fe2d` is tree-identical to its parent (empty diff), as its message claims — the range's base is clean.
- Three commits, all authored `PB-3 Bot <pb3-bot@madhav-astrology.iam.gserviceaccount.com>` within 11 s (14:01:43–14:01:54 +0530): `d0fcce3b2` (the re-pin, 13 files), `3adf3c4ba` (writer digests only), `49b596bd9` (census only).

## 2. Arithmetic — the ten reference rows

**Verdict: every delta is 6992 or 6993 s; permission.py equals the NEW evidence values exactly; no old id or old instant remains in it.**

Computed with Python `datetime` over section (3) of `OFFICIAL_DRYRUN_EVIDENCE.txt` (new − old, seconds):

| row | start Δ | end Δ |
|---|---|---|
| MD Mercury `58afa482`→`1d1a80c0` | 6993 | 6993 |
| AD Ketu `133b4500`→`2103a226` | 6993 | 6993 |
| AD Moon `14f20359`→`68789a8d` | 6993 | 6993 |
| AD Mars `b1e4d515`→`c4821baa` | 6993 | 6993 |
| AD Rahu `25a4b815`→`a91faefa` | 6993 | 6993 |
| PD Mercury `6b843ad2`→`65e30373` | **6992** | 6993 |
| PD Venus `203406df`→`91980ae7` | 6993 | 6993 |
| PD Venus `5c07a7c9`→`48338f36` | 6993 | 6993 |
| PD Saturn `a4cf46db`→`d4d08aca` | **6992** | 6993 |
| PD Saturn `73eea5c0`→`f72e343c` | 6993 | 6993 |

All 20 deltas ∈ {6992, 6993}; the two 6992 values are PD starts, consistent with the evidence's per-level table (PD min 6992, MD/AD exactly 6993).

`permission.py` at `49b596bd9`, parsed by AST (not by eye): 10 rows; for each of the ten evidence rows the `row_id`, `level`, `lord`, `start_iso`, `end_iso` **and** `parent_row_id` match the NEW values exactly (`ALL_TEN_EXACT: True`). Parent lineage is preserved: all four AD rows → `1d1a80c0` (new MD); PD Mercury → `2103a226` (AD Ketu); PD Venus(1) → `68789a8d` (AD Moon); PD Venus(2) and PD Saturn(2) → `a91faefa` (AD Rahu); PD Saturn(1) → `c4821baa` (AD Mars). Every child interval lies inside its parent; AD Moon.end = AD Mars.start = `2019-02-17T08:46:56Z` and AD Mars.end = AD Rahu.start = `2020-02-14T13:43:56Z` (contiguous, half-open). `DASHA_READ_CONTRACT["build_id"] == "75524b3e-102a-43ec-8cee-3f57fee752c3"`.

Substring scan of `permission.py`: none of the 10 old row-id prefixes and none of the 17 old instants appear anywhere in the file. The old **build id** appears once, on line 14, inside the module docstring (see finding 3).

## 3. Both pins, and every remaining occurrence of the old build id

**Verdict: both pins are the new build. The old id survives in `services/` in exactly one place — a docstring — which contradicts the brief's literal "nowhere" expectation but is provenance text, not code.**

- `inventory_verifier.py:664` → `_C_BUILD = "75524b3e-102a-43ec-8cee-3f57fee752c3"`.
- `permission.py:32` → `"build_id": "75524b3e-102a-43ec-8cee-3f57fee752c3"`.
- `git grep -n 1f89fd4c 49b596bd9 -- platform/python-sidecar/services` → **one hit**: `permission.py:14` — the docstring sentence "RE-PINNED at SETTLED-1 (S-L1, 2026-10-04) from the first pin, build 1f89fd4c-… verified 2026-09-30". Judgement: acceptable (audit trail in prose; the guard test `test_the_canonical_dasha_build_is_pinned_in_no_other_governed_module` greps for the NEW id and still asserts exactly `[inventory_verifier.py, permission.py]`). If the owner wants the "nowhere in services" statement to be literally true, move this sentence to a changelog — optional.
- **Lock recompute (beyond the brief).** I re-implemented `input_vector_verifier.module_digests` + `window_gate._canon` + `window_gate.implementation_digest` over `IMPLEMENTATION_MODULES` (13 geometry, 36 evaluation, 11 window modules) reading each module's source from the git tree (UTF-8, universal-newline normalised, as text-mode `open()` does). Results: at `e44f9fe2d` → `73f67d22…` (evaluation `2bd30ecf…`) = committed lock, all three stages MATCH; at `49b596bd9` → `fcfb6827…` (evaluation `d291e4a0…`) = committed lock, all three stages MATCH. The lock is current and no governed module outside the diff changed.
- Every other tracked occurrence of `1f89fd4c` at `49b596bd9` (`git grep` whole tree):
  1. `platform/python-sidecar/tests/l3/gochara_rules/test_am10_repin_75524b3e.py:19` — deliberate; the test asserts the OLD build is refused. Required.
  2. `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/A5_3_REGISTERED_WRITER_BRIEF_v1_0.md:1350` — dated brief (2026-10-01) describing rule G6 as "the frozen `1f89fd4c…`". Historical, but now a stale description of live code; a one-line addendum would be hygienic (not required).
  3. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PURNA_ANVESANA_INDEPENDENT_REVIEW_v1_0.md:196, :975` — historical review record. Acceptable.
  4. `00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/HOOKS_W7_HAND_READBACK_v1_0.md:423, :439, :482` — the pre-S-L1 baseline readback that predicted this exact rebuild. Acceptable (it is the baseline record).
  - Untracked only: the three evidence files in the checkout root.
- `POST_RECORD.out` (unverified, read-only DB snapshot supplied as evidence) is at least self-consistent with the diff: `a_verifier_predicate_builds` = `75524b3e…`, 9217 rows; two_pass_verified levels 1/2/3 = 13/104/923 (equal to the evidence's old=new counts); whole-table one build; `ga_dashas` state `lit`.

## 4. Tests

**Verdict: every rewritten literal is one whose meaning depends on equalling a re-pinned row; each rewritten test still discriminates. Exactly five old-instant lines remain in the Python test tree, all inside one self-contained synthetic fixture (ruled "keep"). Three stale comments and one stale production-script comment should be amended.**

Principle check, hunk by hunk (`git diff e44f9fe2d 49b596bd9 -- 'platform/python-sidecar/tests/**/*.py'`):

*`test_step06b_per_instant_permission.py`* — rows come from `RP.MD_ROWS/AD_ROWS/PD_ROWS` (`_l1_rows`, lines 288–298), i.e. the pinned data, so anything compared to them must follow:
- L284 `BOUNDARY = datetime(2020, 2, 14, 13, 43, 56)`: required — with the old value, `test_o_pp_2_boundary_instant_belongs_to_rahu_half_open` would read **Mars** (new Rahu AD starts 13:43:56) and fail. Still meaningful: asserts Rahu at the instant, Mars at `BOUNDARY − 1 s`, and `t_utc.startswith("2020-02-14T13:43:56")`.
- L321–324, L386, L413 row-id equalities at T1/T2, orphan-ignored, merged ids: follow data; assert row identity, not vacuous.
- L401–404 `test_conflicting_rows_for_one_period_identity_raise`: the injected conflict must share `(level, parent, start)` with the real Mars AD to be a conflict at all — must follow; asserts `DashaReadConflict` and the dup-merge set.
- L607 `MD_ID` and L660 `fine` sibling start `2022-09-02T23:01:56Z`: must follow — kept at `21:05:23Z` the sibling would overlap the new Rahu AD by ~2 h and be rejected as a conflict instead of getting `index == 3`.
- L670–672 `dup_md` identical to the real MD (collapse requires identical fields) and re-parenting the Mars AD by its new id: must follow.
- L687–697 `test_exact_instants_are_never_advanced_by_rounding`: `utc_iso_of_jd(jd_of(BOUNDARY − 1 ms)) < "2020-02-14T13:43:56"`, exact instant → Rahu with `t_utc == "2020-02-14T13:43:56+00:00"`, `"…13:43:55.999999+00:00"` → Mars. Meaningful; the "one second / one millisecond before" forms are all consistent with the new boundary.
- L346 docstring only.

*`test_pp.py`* — `T_BOUNDARY` (L21) → Rahu, row `a91faefa`; `just_before = "2020-02-14T13:43:55Z"` (L118) → Mars; row ids at the three event instants (L40–42) and at t1/t2 (L68–69) follow data. `test_opp1_rows_are_half_open` (L51) asserts `MD_ROWS[0]["start_iso"] == "2010-08-18T17:46:56Z"` — a constant-equals-constant guard (it was before the re-pin too); weak but not vacuous: it pins the embedded constant to the spec value.
- The five unchanged event/interior instants are safe: nearest boundary (old **or** new) is 16.4 days (T1), 19.5 d (T_MARRIAGE), 30.5 d (T_FATHER), 57.5 d (T2), 64.6 d (T_TWINS) — none lies in the 6993 s shift band, so none of the 34 boundary-sensitive instants in the evidence (all old boundaries and +1 s) touches a test event.

*`test_a25_v41_candidate_writer_pg.py:409`*, *`test_a53_inventory.py:49`* — seeded rows must carry the pinned build or `dasha_read` refuses the read; required. `test_a53_inventory`'s `DASHA` rows are synthetic 2024–2026 rows (self-contained).

*`test_a53_r16_amendments.py`* — three equality assertions moved to the new id; the "no other governed module" grep (L128–131) now searches for the new id and still asserts exactly the two files. Required and meaningful.

*`test_rp_oracles_a55.py`, `test_rr_oracles_a55.py`* — docstrings and the `period_lord_row=` label argument moved to the new MD id. Consistent.

**Kept literals (ruled "keep"):** `test_step06b_per_instant_permission.py:864–868` — the `tree(suffix)` helper in `test_complete_duplicated_md_ad_pd_tree_collapses_recursively` builds a fully synthetic duplicated MD/AD/PD tree (ids `md-a`, `ad1-b`, …) with old instants and asserts collapse, merge order, index and parent re-pointing, then `select_period_rows(rows, T1)` → Mars/Saturn. T1 (2019-08-01) lies inside both the old Mars AD and the old PD Saturn(1), so the assertions hold; nothing compares these rows to `RP.*`. Keeping is correct under the stated principle. (The rows carry the NEW build id with OLD instants — harmless, nothing cross-checks instants against the pin.)

**Sweep for the 17 old instants in every textual form** (with `Z`, without `Z` / `+00:00`, space-separated, and `datetime(Y, M, D, h, m, s)` argument form) over `platform/python-sidecar/tests` at `49b596bd9`: **5 hits, all lines 864–868 above; zero others.** Extended sweep over all of `platform/` excluding `python-sidecar/tests` and `src/generated`:
- `platform/tests/integration/gochara_b6_{am14_moon_domain,am5_search_inventory,rehearsal_volume}.db.test.ts` (lines ~261–275, 620, 1075) — TS seeds inserting MD Mercury / AD Ketu rows with old instants under a synthetic `BUILD = '40000000-0000-4000-8000-000000000001'`. Self-contained; no comparison to `permission.py`. Acceptable.
- `platform/scripts/governance/__tests__/test_flip_detector.py:72` — synthetic Saturn MD ending at `2010-08-18T15:50:23+00:00` in a flip-detector fixture. Self-contained. Acceptable.
- **`platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:412`** — a *comment* ("…half-open boundary instant 2020-02-14T11:47:23Z (Rahu)…") in a non-test script. Now factually wrong (the boundary is 13:43:56Z). Comment only, no logic. **Amendment A1.** Note this file is in `ka_gochara_v4_41_candidate`'s declared `source_paths` (`ka_gochara_v4_41_candidate.py:314`), so fixing the comment moves that writer's digest and should ride its own regenerate cycle rather than be bolted onto this head.

**Stale comments naming old row ids** (comments only, assertions already updated): `test_rp_oracles_a55.py:220` ("row 58afa482-…", inconsistent with the same file's L268–270 which now use `1d1a80c0`); `test_rr.py:65` ("row 58afa482…"), `:67` ("row 14f20359…"). **Amendment A2.**

## 5. The new generated test `test_am10_repin_75524b3e.py`

**Verdict: yes on all three questions; not vacuous; one provenance caveat.**

- `test_the_verifiers_independent_pin_equals_the_read_contract_pin` (L27–28): `assert inventory_verifier._C_BUILD == DASHA_READ_CONTRACT["build_id"] == NEW` — verifier pin = read-contract pin = new build.
- `test_pin_is_the_new_build_and_the_old_one_is_refused` (L31–34): asserts the contract is `NEW`; `select_dasha_read_contract(canonical_chart, rows(NEW))["build_id"] == NEW`; and `with pytest.raises(DashaReadConflict): select_dasha_read_contract(canonical_chart, rows(OLD))`.
- Not vacuous: the step06a wrapper (`step06a_class_context.py:227–231`) delegates to `services.gochara_kernel.dasha_read.select_dasha_read_contract`, whose canonical-chart branch (`dasha_read.py:39–47`) raises `DashaReadConflict` iff the pinned build is **not** among the builds seen. The two calls differ only in the build id, so the refusal is caused by the pin and the acceptance by the pin — exactly the claim. It exercises the real code path (same one `test_step06a_read_contract_pins_the_frozen_build_or_refuses` at `test_step06b…:593–602` uses).
- Caveat (provenance, not correctness): the docstring says "generated by `scripts/gochara/repin_dasha_contract.py`". That script, and `tests/l3/gochara_rules/test_am10_repin_tool.py` which `RULINGS_ADOPTED.json` rules on, are **not in the tree at `49b596bd9`** (`git ls-tree` → absent); they live on `pravaha/b6-am10-repin-tool-declared-shape` (`b974cb57d`), which is not an ancestor of the reviewed head (`git merge-base --is-ancestor` → no). The test does not import the tool, so it runs regardless. **Amendment A3** (docstring: cite the tool's branch/commit, or drop the claim).

## 6. Honest limits

- **No test was run.** `pytest` was not executed; `test_a53_r16_amendments`, `test_a25_v41_candidate_writer_pg` and the golden-brief tests need Postgres; `test_pp`'s `chart` fixture was not inspected for DB dependence. All test judgements are static.
- **No database was touched.** `POST_RECORD.out` and `OFFICIAL_DRYRUN_EVIDENCE.txt` were taken as supplied; I verified their *internal* consistency (counts 13/104/923 agree across both; the 10-row arithmetic; 22 TEST LITERAL lines reconcile exactly to the rulings' 8 rewrite / 14 keep with no unruled or extra entries) but not their provenance against the live DB. The dry-run tool that produced the evidence is not in this tree (finding 5), and its rulings file is untracked — the steward decision record is not part of the commit.
- **Verified by recomputation:** `implementation_digest.lock.json` at both ends of the range (finding 3) — exact match.
- **Not recomputed:** `nirmana-writer-digests.json` (requires importing the writer registry and resolving the import closure) and `capability_estate_census.json`'s `content_sha256` (TypeScript generator). Taken on the commit message's word ("byte-stable twice").
- **Golden fixtures:** I base64-decoded both versions of `golden_brief_log_entries_1class.json` and diffed every leaf (39 changed). Neither version embeds a daśā build id or any boundary instant; every change is a digest, timestamp, manifest id or `runner/commit`, and the embedded `implementation_digest` equals the new lock (`fcfb6827…`) — consistent with a regenerate under the new pin. I could not verify `derivation_inputs_digest`, `inventory_digest`, `ledger_digest` or the table sha256s without running the verifier. **One provenance oddity (Amendment A4):** the golden records `runner/commit = e44f9fe2d` paired with digest `fcfb6827…`; at commit `e44f9fe2d` the real digest was `73f67d22…`, so this (commit, digest) pair never coexisted in any committed tree — the fixture was regenerated from a dirty working tree before `d0fcce3b2` was committed. The consumer (`test_a53_r13_brief_serializer.py:159–222`) does not assert the commit value, so this is cosmetic.
- `GOCHARA_DESIGN_SPECS_v1_4` — the document `permission.py` and `dasha_read.py` cite as the source of the reference rows — is not in the tracked tree (`ls-tree` search, any case), so I could not confirm that the spec's §4.0 now lists the new rows. If it still lists the old rows, code and spec disagree; out of my reach here.

---

## Amendments (recommended; none gates entry)

- **A1** — `platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:412`: update the comment's boundary instant `2020-02-14T11:47:23Z` → `2020-02-14T13:43:56Z` (comment only; expect the `ka_gochara_v4_41_candidate` writer digest to move — regenerate in the same follow-up).
- **A2** — stale row-id comments: `tests/l3/gochara_rules/test_rp_oracles_a55.py:220`, `tests/l3/gochara_rules/test_rr.py:65` and `:67`.
- **A3** — `test_am10_repin_75524b3e.py` docstring cites a generator absent from this tree; cite its branch/commit or drop the claim. Consider committing `RULINGS_ADOPTED.json` (or its content) beside the test so the steward ruling is in-tree.
- **A4** — regenerate `golden_brief_*_1class.*` once from the committed head so `runner/commit` and `implementation_digest` are a real pair (cosmetic).
- **A5** — optional: `permission.py:14` docstring keeps the old build id for history; move to a changelog if the "nowhere in services" statement is meant literally. `A5_3_REGISTERED_WRITER_BRIEF_v1_0.md:1350` could carry a one-line "re-pinned 2026-10-04" addendum.

**MAY THIS HEAD ENTER THE PROTECTED TRAIN — YES**

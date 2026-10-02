• The diff is fully captured. Now let me run the tests read-only and verify key structural claims (attributes, spec pins).

• All verification done. Tests run green (52 passed, 5 skipped — the skips are the WP6 Postgres-gated cases, `NOT_RUN` when unreachable). Here is the complete review.

  ```yaml
  artifact: KIMI_K3_REVIEW_A2_KERNEL_GEOMETRY
  version: "1.0"
  status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
  reviewer: "Kimi K3 (effort=max)"
  date: 2026-09-30
  verdict: ACCEPT_WITH_AMENDMENTS
  reviewed_commit: 95e765c3c
  authority: "Review only; authorizes nothing."
  ```

  # KIMI_K3_REVIEW_A2_KERNEL_GEOMETRY — independent review of A2.1 Tier 0-G kernel geometry fixes

  ## Verdict: ACCEPT_WITH_AMENDMENTS

  The seven steps implement the cited FABLE findings and spec clauses correctly, the geometry recomputes clean by hand, every new test names and catches a real mutation, and the migration is surgical with a strengthened (not weakened) guard. Four amendments must land before merge — one is a data-correctness mislabel on the new N2 path, none require redesign.

  ## Per-step review

  | Step | Commit | Correct? | Evidence |
  |---|---|---|---|
  | aspect_direction | 3d77a1326 | YES | `contacts.py:219-228` — `(t − a) % 360.0`. Recomputed: forward count puts the aspect at (λ_b + angle); landing on target ⇒ λ_b = (target − angle) mod 360. Target 0°: Mars 4th (90°) → 270° ✓, Mars 8th (210°) → 150° ✓, Saturn 3rd (60°) → 300° ✓, Saturn 10th (270°) → 90° = Cancer ✓ (matches O-AD-4 incl. the v1.1 Gemini→Cancer label correction). Drishti table `convention.py:45-55` matches doctrine (Mars 90/180/210, Jupiter 120/180/240, Saturn 60/180/270, nodes empty per N-14). |
  | zero_degree_seam | faebf5d83 | YES | `contacts.py:boundary_degrees` — grids now 12/27/96 with 0° included exactly once; `arcs.py:156-163` `covers_degree` reads the seam as 360 so the root attributes to the arc that REACHES the boundary; `contacts.py:_seam_canonical` makes root-solving agree. O-SS-1 pins 12/27/96 per revolution ✓. The kakṣyā grid change (84 internal-only → 96 incl. cusps and seam) is forced by the oracle: 84 can never reach the pinned 96. Cusps are now reported by both `sign_ingress` and `kakshya_cell_crossing` — defensible as distinct relations, and the code comment says so explicitly. |
  | no_fabricated_ingress | 823a412d9 | MOSTLY — one mislabel, see Amendment 1 | `episodes.py:451-457` searches both boundaries (`lo_w` and `hi_w % 360`) — N2 fixed; `episodes.py:498-527` stamps `t_exact=None / exact_crossing=False / truncated='start'` on a clipped span — N3/O-SS-3 fixed, matches FABLE lines 86–87. Root-derived `branch`/`station_flag`/`completeness_state` now come from `classify_branch` when a root exists. |
  | truncated_contacts_kept | b772523d4 | YES | `step06_enumerate_episodes.py:672-676` keeps no-exact episodes; identity via floored t_in fallback in `ids.py:70-82` with the substitution marked in-payload (`t_exact: null, t_in: <floored>`) — cannot collide with an exact contact at the same minute (sorted-key canonical JSON, `ids.py:26-28`; the exact-contact payload is byte-identical to pre-change — verified: same field set, `sort_keys=True` makes insertion order irrelevant). `ledger.py` duplicated implementation mirrors the rule and raises on missing fallback. |
  | residence_spans_persisted | 40e7d1cf4 | YES | `step06_enumerate_episodes.py:594-637, 726-734` — the interval itself is emitted (`relation='residence'`, t_in/t_out/dwell, `target_longitude_deg=None`, `orb_source='orb_ingress'`), alongside the zero-width ingress episode. This directly answers FABLE T0-3 #6/#7 (span computed then discarded → inert ledger). `ResidenceSpan.span_lo_deg` exists (`episodes.py:108`). |
  | global_boundary_table | 59a1d625d | YES | `step06_enumerate_episodes.py:678-687` — `boundary_cache` solves each relation once per body (target-independent by construction: `boundary_degrees` takes no chart/target argument) and joins to targets in the loop. Emitted per-target rows are unchanged in shape; the redundant re-solving is gone. Matches O-SS-1's "each event stored once; no per-target duplication" producer half. |
  | regression_suite | 95e765c3c | YES | `test_wp3a_kernel.py:15-32` header index maps each Tier 0-G step to its mutation guards; the mapping is accurate against the actual test names in both files. |

  ## Tests — can each fail?

  `python3 -m pytest -q tests/l3/gochara/test_wp3a_kernel.py tests/l3/gochara/test_step06_enumeration.py -p no:cacheprovider` → **52 passed, 5 skipped** (the skips are the WP6 disposable-Postgres cases, `NOT_RUN` when unreachable — acceptable read-only). Mutation coverage:

  - `test_oad_aspect_direction[*]` — catches the shipped mirror (target + angle): the mutation-detector assertion checks NO root exists at t_mirror. Real two-sided guard.
  - `test_oad_levels_computed_as_target_minus_angle` — catches the level-map flip directly, plus the self-mirror 7th (180°) invariant.
  - `test_oss2_case1/case2` — catches a missing 0° root, a doubled seam root, and horizon-edge fabrication (δt < 60 s assertions + interior-instant assertions).
  - `test_oss1_boundary_counts_one_revolution` — catches 0° removal (11/26/95) and seam double-emission; pins the seam instant.
  - `test_oss_grids_include_zero_exactly_once` — catches grid-level duplicates/out-of-range.
  - `test_n2_retrograde_upper_boundary_entry_found` — catches the lo_w-only search (pre-fix leaves `spline_exact_jd=None` while stamping `exact_crossing=True` — the exact lie N2 names).
  - `test_n3_clipped_span_never_fabricates_ingress` — catches `t_exact=ca` fabrication and span-dropping.
  - `test_truncated_contacts_kept_and_counted` — catches both failure modes named in its docstring (drop = absence-fabrication; non-NULL t_exact = instant-fabrication), and proves the never-entered narrower return band stays a correct absence. Sharp distinction.
  - `test_boundary_events_solved_once_per_body` — monkeypatch-counts the solver: per-target re-solving (N×) fails, `len(BOUNDARY_RELATIONS)` passes. Attachments still asserted per target.
  - `test_contact_id_no_exact_t_in_fallback` — catches fallback omission (ValueError), collision with the exact id at the same minute, and sub-minute jitter instability.

  No test is tautological; each names a concrete mutation that fails it.

  ## Migration 1152

  - **Surgical**: two statements on one table — `DROP NOT NULL` on `t_exact`, plus a new CHECK `exact_crossing = (t_exact IS NOT NULL)` as `NOT VALID` then `VALIDATE`. Guard **added**, none weakened; the CHECK is exactly the anti-fabrication invariant (a non-NULL t_exact on a no-exact row IS the fabrication).
  - **Numbering**: verified — 1151 exists on `origin/main` (`1151_ai_console_model_shortlist.sql`), no 1152 anywhere; the header's claim holds.
  - **Production safety**: existing rows are all exact (1081's NOT NULL made no-exact rows unpersistable), so `VALIDATE` passes trivially. `DROP NOT NULL` + `ADD CONSTRAINT NOT VALID` are brief-lock, online-safe in Postgres. The protected 'v1'/'3.0' corpus in `kala_gochara_windows` is untouched; scope statement is accurate.
  - **Gaps** (amendments 4): reversibility is not stated (re-adding NOT NULL becomes impossible once truncated rows exist — that should be written down), and the file is not idempotent (re-run fails at `ADD CONSTRAINT`); if this lane's convention requires idempotent migrations, guards are needed — the header asserts numbering hygiene but is silent on both.

  ## Regression hunt

  - **ID stability for published '4.0' contacts**: exact-path payload fields are unchanged and canonicalization sorts keys, so existing contact ids are byte-stable. ✓
  - **Performance**: strictly improved (boundary solving O(bodies×relations) instead of O(bodies×relations×point-targets)). The join emits the same row count as before, so downstream dedupe load is unchanged.
  - **Consumer-facing meaning changes** (Kṣetra/Saṅgam per L3_FAMILY_COORDINATION): (a) new `relation='residence'` rows appear where none existed — additive, but consumers filtering on a relation whitelist must opt in; (b) episodes previously absent (dropped no-exact) now appear with `t_exact=NULL` — any consumer assuming `t_exact` non-null on `kala_gochara_contacts` rows will now meet NULLs; that is the intended contract change and migration 1152 is its gate; (c) kakṣyā rows now also occur at sign cusps — consumers counting kakṣyā events per revolution see 96, not 84.
  - **Real defect found**: on the N2 path (retrograde entry through the UPPER boundary), the ingress episode is stamped `target_deg=lo_w, level_deg=lo_w` unconditionally (`episodes.py:512-513`) even when the matched root sits at `hi_w` — e.g. the Pisces re-entry at the 360° seam is labelled `level_deg=330°` while `t_exact`/`spline_exact_jd` correctly carry the 360° crossing. `test_n2_*` never asserts `level_deg`, so the mislabel ships green. Kṣetra reads level/target degrees — this is consumer-visible wrong data, not cosmetics.

  ## Ranked amendments (must land before merge)

  1. **Fix `level_deg` (and document `target_deg`) on upper-boundary entries** in `episodes.py:residence_spans` — when the matched ingress root is at `hi_w % 360`, stamp that boundary, not `lo_w`; extend `test_n2_retrograde_upper_boundary_entry_found` with a `level_deg` assertion. (Consumer-facing data correctness.)
  2. **Reconcile `truncated_at_horizon='both'` between the two rows of one span** — the ingress episode maps 'both' → `'start'` (`episodes.py:524-526`) while the residence row maps 'both' → `NULL` (`step06:604-605`). Same physical span, two disagreeing rows. Pick one rule, pin it, test it.
  3. **Fix the `episodes_truncated_no_exact_kept` double count** — `_emit` already increments for a no-exact ingress episode; `step06:731-732` increments again for the same physical truncation (ingress row + residence row = 2 for one event). Either count physical truncations once or rename the metric to count rows; current semantics disagree with the key's name.
  4. **Migration header: state reversibility and idempotency stance** — one sentence each (irreversible-in-practice once truncated rows exist; single-run via migrate.ts, re-run fails at ADD CONSTRAINT).

  ## Could not verify (read-only scope)

  - Live production data in `kala_gochara_contacts` (no DB connection permitted) — the "existing rows satisfy the CHECK" argument rests on 1081's NOT NULL, not on a table scan.
  - `npm run guard:migration-numbers` (would execute tooling; numbering verified manually instead).
  - Kṣetra/Saṅgam consumer code itself — blast radius assessed structurally from the coordination brief's consumption statement, not from reading those readers line-by-line.
  - Whether WP1_CONTRACTS §3.2 sanctions the t_in-fallback rule — the code itself admits §3.2 pins only exact contacts; the fallback is a documented, well-marked extension (payload substitution prevents collision), which I judge sound, but it is a spec extrapolation the stewards should ratify.
  - FABLE §5/§6 full text beyond the N2/N3/T0-3 finding rows (lines 86–87, 213–214) — those rows match the implementation precisely.


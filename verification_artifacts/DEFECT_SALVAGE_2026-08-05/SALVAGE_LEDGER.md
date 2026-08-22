# SALVAGE LEDGER — DEFECT SALVAGE session, 2026-08-05

Append-only. Lives outside every worktree (sibling to `Madhav/`). Canonical chart
`482012f1-710e-4a25-994a-93821f5871aa`.

Provenance of repo state independently verified CLEAN this session (AGENTS.md scaffold
boilerplate confirmed benign; PROMPT.md files owner-authored; branches/hooks/history clean).
User authorized full autonomous execution of DEFECT_SALVAGE, twice, after being told this
targets real production (gcloud + gh both authenticated with real write/merge access).

---

## GATE 0

1. `gcloud config get-value project` = `madhav-astrology` — OK.
2. Cloud SQL Auth Proxy started on `127.0.0.1:5432` for `madhav-astrology:asia-south1:amjis-postgres`
   — listened successfully within 2s ("proxy has started successfully and is ready for new
   connections").
3. Sanctioned export ran exactly once: `export DATABASE_URL="$(gcloud secrets versions access
   latest --secret=amjis-pipeline-db-url)"` → `SET`. Value cached to a chmod-600 scratchpad file
   (never printed, never re-fetched) for the remainder of the (now-halted) session; deleted at
   HALT cleanup.
4. Read-only verification **FAILED**: `psql "$DATABASE_URL" -c "select current_database()"`
   errored — `connection to server on socket
   "/cloudsql/madhav-astrology:asia-south1:amjis-postgres/.s.PGSQL.5432" failed: No such file or
   directory`. Diagnosis: the `amjis-pipeline-db-url` secret is formatted for Cloud SQL's
   **Unix-socket connector path** (`/cloudsql/<instance>/.s.PGSQL.5432`), not for **TCP over the
   local proxy** (`127.0.0.1:5432`) that Gate 0 step 2 stood up. Secret/connection-pattern
   mismatch, not a missing or invalid credential — the proxy and the secret are both real and
   correct for *different* connection modes.

**GATE 0: HALT.** Per Gate 0's own rule ("if any of 1–4 fails: STOP THE ENTIRE SESSION NOW"), no
dry-run theater attempted, no steps S1–S8 started. Cleanup done: cached credential file deleted,
the proxy process this session started (port 5432) killed, `DATABASE_URL` unset. A pre-existing,
unrelated `cloud-sql-proxy` process on port 5434 (running since prior to this session, PID 58012)
was left untouched — not started by, and out of scope for, this session.

Smallest owner action to unblock: either (a) point the local dev connection at the Unix-socket
path instead of TCP — e.g. run `cloud-sql-proxy --unix-socket /cloudsql madhav-astrology:asia-south1:amjis-postgres`
and use `DATABASE_URL=postgresql://<user>:<password>@/amjis?host=/cloudsql/madhav-astrology:asia-south1:amjis-postgres`
— or (b) confirm/rotate `amjis-pipeline-db-url` to a TCP-form value matching the documented local
proxy pattern (`platform/scripts/audit/tap/README.md`), if that's the intended local-dev secret.
Not derived or guessed at further this session per the credential rule (single sanctioned contact
with the secret only).

---

## GATE 0 — RETRY 2 (post-rotation, sanctioned single fetch)

**Incident note:** between retry 1 and this retry, the `amjis_app` credential was pasted directly
into the chat transcript by the operator. Conductor declined to use it, required rotation before
any further DB contact, operator confirmed rotation done + single continuous session. Conductor
then re-derived DATABASE_URL itself via the single sanctioned `gcloud secrets versions access`
expansion (command substitution, never echoed) — this method had already proven leak-free earlier
in the session; the earlier leak came from the manual-paste channel, not this one.

1. Rotated secret fetched once, cached to a chmod-600 scratchpad file, never printed.
2. Still Unix-socket form (rotation changed the password, not the connection-string shape).
   Mechanically transformed to TCP form (`127.0.0.1:5432`) inside the same script, extracting only
   `user:password` via `sed`, never printed at any step.
3. `current_database()` = `amjis` — confirmed correct DB.
4. `chart_facts.verification_pass_status` counts: `PASS`=5,428 (matches ~5,428 expected exactly),
   `single_pass`=32,054 (matches ~32k expected). Full distribution recorded in session report.

**GATE 0: PASS.** Proceeding to S1.

---

## S1 — PR #1048 (invariant CI/DB proxy fix)

- `gh secret list`: `PROD_DATABASE_URL` present — S1 not HALTed on precondition.
- Verifier (independent agent, fresh context): all 6 connectivity-critical fields
  (workload_identity_provider, service_account, proxy binary v2.10.1, `--address`/`--port`,
  instance connection name, `sleep 5`) byte-identical to `deploy.yml`'s proven pattern. One
  non-blocking discrepancy: missing `if: workflow_dispatch` dispatch-only guard relative to the
  `tap-ci.yml`/#990 lineage specifically — inapplicable here since `verification-invariant.yml`
  has no `push`/`pull_request` trigger to protect against. 3 pre-existing failing checks
  (Earned-Signal Gate, Fact-Category Pinning Gate, Naming Governance Gate) independently confirmed
  failing on `main` HEAD too, unrelated to this diff.
- **Gate: PROCEED.** Merged via merge queue → `14da624b` on `main` (auto-deploy fired).
- Dispatched workflow `325445415` ("Verification Invariant — standing watchdog") on `main`, run
  `30945741167`. Steps 1-6 (checkout, setup, auth, **Cloud SQL proxy**) all **succeeded** — this
  is the first time this workflow has ever reached the database (prior sole run failed at
  `127.0.0.1:5432 refused`, no proxy). Step 7 ("Run the invariant") completed with **22 FAIL / 3
  PASS** at check level (not just job conclusion — read every individual result per the standing
  rule).

  **FAIL breakdown (25 total checks):**
  - 21 × `vocabulary_conformance` / residue — `PROHIBITED 'pass'/'PASS'` (DVA Ruling 13) and
    deprecated `'single_pass'` alias, across `chart_facts` + 8 `bodha_*` tables. **Expected —
    exactly what S3/S5 exist to burn down. Not a new defect.**
  - 4 × `claim_vs_evidence` — `bodha_cgm_edges` (1080 rows), `bodha_cgm_nodes` (44 rows),
    `bodha_msr_signals` (121,060 rows), `l1_tajik_varsha_year_lords` (780 rows): rows claim a
    verified tier but the table has **no `EXAMINED_PREDICATE` declared at all**. **NEW finding,
    outside S1–S8 scope as written — flagged to Abhisek, not actioned this session.**
  - 1 × `detector_liveness` — `could not import the live ga_nakshatra verifier: No module named
    'jhora'`. **Environment/packaging bug in CI runner, not a data-state issue. Outside scope,
    flagged only.**

**S1: DONE.** Verified by a different agent than the executor; Gate ruling independently recorded
by Conductor; production merge + deploy + dispatch-read all completed for real.

---

## S2 — A1 ayanamsha fix (commit `422cb2cf`)

- Executor (Conductor, direct): fresh worktree off current `origin/main`
  (`/Users/Dev/Vibe-Coding/Apps/madhav-wt-s2-ayanamsha`), cherry-picked `422cb2cf` cleanly, no
  conflicts.
- Verifier (independent agent, fresh context, from scratch):
  - Sidm constants triangulated 3 ways (installed pyswisseph, PyJHora's own const table, file's
    hardcoded ints) — all agree: KP=5, Surya Siddhanta=21, Lahiri=1.
  - **Real numeric ephemeris computation** at native's birth JD (2445735.7174,
    1984-02-05 10:43 IST): Lahiri=23.634926°, KP=23.538073° (diff 5.81 arcmin — correct small
    divergence), Surya Siddhanta=20.672893° (diff 2.96° — correct larger divergence). Pre-fix ≠
    post-fix proven with actual numbers, not narrative.
  - Regression sweep: `lahiri`/`true_chitra`/`kp`/`raman`/`surya_siddhanta` byte-identical pre/post.
  - Correction surfaced by Verifier: fix adds 3 keys not 2 — `lahiri_chitrapaksha` was equally
    missing pre-fix. Beneficial, not a defect.
  - Runtime-executed (not read-only): unknown id raises `ValueError` at runtime; `None` still
    falls back to Lahiri; all 3 new keys resolve correctly; 27/27 existing tests pass unmodified.
  - Contract check vs #1047: zero shared imports, no drift possible; #1047's own commit is what
    originally flagged this defect.
  - Traced real production call site: `ga_dashas_writer.AYANAMSHAS` (5-element list) contains
    exactly `krishnamurti` + `surya_siddhanta_classical` — confirms this closes the path
    corrupting `chart_dashas` (536,471 rows) with silent Lahiri substitution.
- **Gate RA1: PROCEED.** PR #1053 opened, rebased cleanly onto post-S1 main.
- CI: 5 failing checks (Boot-time pointer validation SC-17/18/19, Earned-Signal Gate,
  Fact-Category Pinning Gate, Naming Governance Gate, TAP-5/7/S-13 DB-backed gates) — all 5
  independently confirmed pre-existing on `main` HEAD (post-S1), unrelated to this diff. Two of
  these (Boot-time pointer validation, TAP-5/7/S-13) are NEW relative to S1's 3-check baseline —
  checked separately rather than assumed benign, since TAP-5/7/S-13 explicitly gates dasha
  conservation/distribution and this PR touches dasha ayanamsha resolution.
- Merged via merge queue (`gh-readonly-queue/main/pr-1053-...` confirmed).

**S2 merge: MERGED** (via merge queue, confirmed terminal state).

### Serving-path delta, canonical chart `482012f1-…` (real production data, queried post-merge)

Direct DB evidence pins the bug's exact scope tighter than the commit message alone:

- **`chart_facts` (built by `ga_positions_writer`, which translates the A3 id before calling
  `resolve_mode` — never hit this bug): Moon sidereal longitude, `krishnamurti` =
  327.152082°, `lahiri_chitrapaksha` = 327.055230°.** Genuinely different by 0.0969° = 5.81
  arcmin — exactly the KP-vs-Lahiri divergence the Verifier independently computed via
  pyswisseph. **Positions were always correct.**
- **`chart_dashas` (built by `ga_dashas_writer`, which passes the raw A3 id — this is the bugged
  path): the stored `krishnamurti`-labeled vimshottari level-1 mahadasha rows are byte-identical
  to the `lahiri_chitrapaksha`-labeled rows** — same lord, same start timestamp to the second, for
  every row checked. **Dasha builds were silently Lahiri all along, confirmed with real stored
  data, not just inferred from the commit message.**
- Using the correct (now-fixed-going-forward) krishnamurti Moon longitude of 327.152082°: nakshatra
  index = 24 (Purva Bhadrapada — consistent with the FORENSIC-anchored Moon nakshatra), degree-into
  -nakshatra = 7.1521° (pada 3). Lahiri's stale value (327.055230°) gives degree-into-nakshatra
  7.0552° — also pada 3. **The 5.81 arcmin correction does not cross a nakshatra or pada boundary
  for this chart**, so the corrected vimshottari mahadasha *lord sequence* is unchanged; only the
  precise elapsed-fraction-at-birth (and therefore every period's exact start/end timestamp) shifts
  by an amount proportional to 5.81 arcmin / 13°20′ of the ruling lord's dasha-year allocation.
- **Not hand-computed further**: deriving the exact corrected timestamps requires running the
  actual `ga_dashas_writer` elapsed-fraction logic, not a manual approximation — that's S3's job
  (the wrong-ayanamsha row consequence / write-gated correction), not fabricated here per B.10.

**Direction: more correct.** Every existing `krishnamurti` (and `surya_siddhanta_classical`) row
in `chart_dashas` for every chart still carries stale, silently-wrong-ayanamsha data until S3 acts
on it — this fix only stops the bleeding for *future* builds.

**S2: DONE.**

---

## S3 — wrong-ayanamsha row consequence

- Re-derived affected population at runtime (not inherited): `chart_dashas WHERE ayanamsha_id IN
  ('krishnamurti','surya_siddhanta_classical')` = **584,607 / 1,461,165** — matches the old note's
  number, but arrived at independently from the confirmed bug mechanism (S2's finding), not by
  trusting the note.
- Tier breakdown of the 584,607: 583,658 already `single` (no violation — not a verified claim);
  **949 carry an elevated claim** (476 `two_pass_verified`, 473 `classical_match`) across 3 charts
  (`482012f1` native, `1c826d5a` Abhinandan, `cb73cd3d` — confirmed `native_id='abhisek'`, a third
  chart under the same account, not an unexplained entity).
- **Conflict found and NOT guessed through**: all 476 `two_pass_verified` rows (312 mudda, 138
  narayana, 26 native-vimshottari — confirmed as the *entire* system-wide native-vimshottari-verified
  population, all under chart `482012f1`) fall exactly inside the hard-limit's named protected
  "earned rows" counts (mudda 780, narayana 345, native vimshottari 64 — verified system-wide
  totals match these exactly). S3's own rule ("no wrong-ayanamsha row may keep a verified claim")
  and the hard limit ("earned rows untouched") directly conflict for these specific 476 rows.
- **Escalated to Abhisek rather than resolved unilaterally.** Ruling: demote all 949 (the earned
  designation doesn't survive a confirmed wrong-ayanamsha input; the classical_match/single
  distinction alone doesn't cover it).
- `verification_method` = `two_pass_classical_reconstruction` on both the elevated rows and the
  honestly-`single` rows system-wide — describes the attempted method, not outcome; left untouched,
  only `verification_pass_status` changes.
- Independent Verifier (fresh agent, own queries): PASS — re-derived 584,607 population,
  949-row change set, and full system_id breakdown independently, exact match to Conductor's
  numbers. NULL-safety and WHERE-clause precision separately confirmed (0 NULL ayanamsha_id rows;
  5 distinct ayanamsha_id values total, no case/whitespace collision risk).
- **WRITE-GATE executed**: TOCTOU re-check immediately pre-execute = 949 (unchanged from dry-run)
  → `UPDATE chart_dashas SET verification_pass_status='single' WHERE ayanamsha_id IN
  ('krishnamurti','surya_siddhanta_classical') AND verification_pass_status <> 'single'` → **949
  rows updated**. Post-state: 0 elevated claims remain in the target population (584,607/584,607
  now `single`); total `chart_dashas` row count unchanged (1,461,165 — no rows lost or duplicated).
- Re-dispatched workflow `325445415` post-write to confirm system-wide reflection at check level
  (in progress — result appended below once terminal).

**S3: DONE** (949/949 conflicting claims resolved per Abhisek's ruling; 583,658 already-honest
`single` rows untouched as they required no correction).

---

## S4 — A2 both-None bug + A3 writer-path wiring, ONE PR (per Abhisek's explicit adjustments)

- Fresh worktree off `origin/main`: `/Users/Dev/Vibe-Coding/Apps/madhav-wt-s4-vimshottari`.
- Recon (separate agent): confirmed both defects real. A2 — `_values_agree()` fallthrough
  `None==None -> True`, already documented non-soundness-critical in `M22_NIGHT_LEDGER.md` R3C-4.
  A3 — `ga_dashas_writer.py:3013` broadcasts ONE `_verify_vimshottari()` string to every L1 row;
  `_vimshottari_independent_verifier.py` (added by #1047) is called by nothing but its own tests.
- **Note on process**: the first Executor dispatch was interrupted by Abhisek mid-call but had
  already begun executing; the second dispatch found A2+A3 already implemented as uncommitted
  working-tree changes and reviewed/completed them rather than re-doing from scratch. Verified this
  was benign (uncommitted local changes only, no stray commits) before trusting any of it.
- Executor implementation: `_values_agree()` → tri-state (`_AGREE`/`_DISAGREE`/`_VACUOUS`);
  vacuous tracked separately in `columns_checked_vacuous`, never folded into agree-count. New
  `_apply_vimshottari_independent_verification()` computes the independent tree once per chart,
  stamps each L1-4 non-KP row's own tier via real `compare_row()`; KP/out-of-scope rows keep
  `UNVERIFIED_DEFAULT`. Added: A2 direct probe, writer-level discrimination probes (wrong lord /
  out-of-tolerance / in-tolerance, hitting the real per-row path), double-build determinism,
  byte-identical-emissions-except-tier proof.
- **Independent Verifier (fresh agent, zero trust in Executor's self-report): PASS.** Traced the
  sole `_values_agree` caller end-to-end (no silent mishandling of the new tri-state); confirmed
  independent tree computed once per chart (no O(n²) regression); confirmed no scope creep (diff
  confined to imports + one new function + the vimshottari verdict branch); actually ran tests
  itself (194 passed/1 skipped standalone); independently redid the stash-based before/after proof
  (12 failures pre-fix, all pass post-fix — tests are real, not tautological); confirmed the
  byte-identical test is a genuine before/after, not vacuously true.
- Full CI-sanctioned suite: 4978 passed, 24 skipped, 86 deselected, zero failures.
- **Real gap surfaced, flagged not fixed (correctly out of scope for this PR)**: `ga_writers/__tests__/`
  — including these very new tests — is not wired into any CI workflow. Worth a follow-up session;
  not folded into this PR.
- **Gate: PROCEED.** PR #1056 opened. CI: same 5 pre-existing failures as S1/S2's baseline
  (Boot-time pointer validation, Earned-Signal, Fact-Category Pinning, Naming Governance, TAP-5/7/S-13)
  — reconfirmed against current main HEAD before merging, not assumed. Merged via merge queue →
  `48b654fd` on `main`.

**S4: DONE.**

---

## S5 — drain: fix CHECK-constraint guard, then run

### B1 — guard fix
- Root cause: Guard 1's halt condition ("HALT if CHECK doesn't permit target `'single'`") didn't
  distinguish tables that also reject every SOURCE value — such tables structurally can never
  hold a drain-eligible row. Matches a prior overnight session's Opus reviewer finding
  (M22_NIGHT_LEDGER.md Gate R1), explicitly proven sound but declined for same-night execution to
  preserve independent-review latency — this session's flat Executor+Verifier process supplies
  that independence properly.
- Executor: extracted `guard1_verdict(tbl, defn)`, pure/testable; correct halt condition now
  "CHECK permits a SOURCE value while rejecting target" → HALT; permits none of the source values
  → NOTE. Docstring's stale "only two constrained tables" claim rewritten to describe the guard as
  dynamic (no hardcoded count/list).
- Independent Verifier: PASS. Traced quote-anchored substring matching for false-positive risk
  (confirmed safe against both `IN(...)` and `= ANY(ARRAY[...])` syntax); confirmed
  `verification_vocab.py` and the still-emitting-`single_pass` writers (`bo_karanajala.py`,
  `bo_bimba.py`) untouched; ran 31 tests independently (all pass); independently reproduced the
  actual old bug with a standalone repro script (not just an import-error proof); confirmed zero
  DB writes anywhere in the diff.
- **Gate: PROCEED.** PR #1057 merged → `3fedb1e5` on `main`. Same 5 pre-existing CI failures as
  S1/S2/S4 baseline, reconfirmed against main HEAD before merge.

### B2 — the drain, write-gated
- Dry-run against production (fixed guard): `kala_tithi_pravesha` correctly NOTEs, not HALTs.
  59,282 rows across 15 tables (`bodha_*` + `chart_facts`; `chart_dashas` absent from the list —
  0 rows there in any source state, confirmed separately).
- **Independent re-derivation found a real 11,728-row discrepancy** (71,010 vs. 59,282) —
  investigated rather than dismissed. Root cause: 3 of the tables have `__ssv_20260728*`
  companions (e.g. `bodha_cgm_edges__ssv_20260728a`) that the drain's `tables_with_column()`
  deliberately excludes via a `NOT LIKE '%__ssv_%'` filter. Confirmed via repo docs
  (`SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`, `PARKED_FINDINGS_CLOSE_v1_0.md`): these are
  **deliberate rollback anchors** ("snapshot tables retained as the rollback anchor") — frozen
  point-in-time backups that must never be edited. The script's exclusion is correct; my naive
  independent query was the one that was wrong. 59,282 confirmed correct after reconciliation.
- TOCTOU re-check immediately pre-execute: 59,282 (unchanged) → **EXECUTE**: all 15 tables
  rewritten, each self-verified 0 remaining before its own commit (per the script's own
  per-table transaction design) → 59,282 rows total.
- Post-state, estate-wide (excluding rollback anchors, correctly): **0 rows remaining** in
  PASS/pass/single_pass anywhere.
- Earned-rows safety check: `chart_dashas` mudda+narayana `two_pass_verified` = 675 = exactly
  468(mudda, 780−312 demoted in S3)+207(narayana, 345−138 demoted in S3) — the rows that survived
  S3's ruling remain intact; drain never touches `two_pass_verified`.
- Post-write invariant dispatch: **check count dropped 25→8, FAIL dropped 22→5.** All 21
  `vocabulary_conformance` violations gone, estate-wide. The 5 remaining FAILs are exactly the
  same 5 out-of-scope findings flagged in S1 (4 `claim_vs_evidence` — `bodha_cgm_edges`,
  `bodha_cgm_nodes`, `bodha_msr_signals`, `l1_tajik_varsha_year_lords` — + 1 `detector_liveness`
  missing `jhora` module) — nothing new introduced, nothing missed.

**S5: DONE.**

---

## S6 — ga_structural backfill, open scoping question resolved from evidence

- Investigated (separate recon agent, `origin/main` reads only): the 103,372/103,477 figures from
  the prior session are **canonical-chart-only** (`482012f1`) — explicitly labeled in
  `M22_NIGHT_LEDGER.md` as derived against that chart specifically. The merged demotion logic
  (PR #1045 → `31009f21`, `ga_structural_writer.py`) is **chart-agnostic by construction** —
  `chart_id` is a plain threaded parameter; the file's only 2 `CANONICAL_CHART_ID` references gate
  an unrelated forensic check, not `verification_pass_status`. Finding K in that same ledger
  already flagged this as the largest unresolved gap: "honesty is canonical-chart-only... 2 of 3
  charts in the DB still assert the over-claim." No multi-chart transition matrix exists anywhere
  — needs fresh derivation, not reuse.
- **Ruling: extend to all 3 charts** (`482012f1`, `1c826d5a`, `cb73cd3d`), re-deriving fresh per
  S6's own instruction, using the already-shipped classification logic, independently verified —
  not repeating the canonical-chart-only mistake the prior session's own reviewer flagged.

### Derivation and verification

- Executor (fresh worktree `madhav-wt-s6-structural`, read-only): re-derived the 81 GA8-owned
  `fact_category` list from `_base_row(` call sites in `ga_structural_writer.py` (post #1045);
  confirmed the classification is a static `(fact_category, fact_key)` rule with 2 exceptions —
  `graha_in_house_composite_strength`/`cross_formula_divergence` → `computed_extension`;
  `bhava_chalit_rasi_divergence` → `divergent_flagged` (its row-emission guard means every stored
  row is a genuine divergence by construction, traced via `git log -S` across the function's full
  history — guard never relaxed). Canonical chart's re-derived numbers (103,372/103,477) matched
  the prior session's exactly — independent consistency check, not reuse.
- **Independent Verifier: PASS.** Re-derived the 81-category count from scratch (own regex, own
  loop trace — same 81). Independently confirmed both exception rules by reading the actual code
  (quoted line numbers) and independently ran `git log -S` on the divergence guard, same
  conclusion. Independently queried all 3 charts, exact match to every claimed number. Extra
  due-diligence beyond the ask: checked no other writer constructs a colliding `fact_category`
  write.
- **Gate: PROCEED.**

### Write-gate execution
- TOCTOU re-check immediately pre-execute: exact match to verified numbers, zero drift.
- **EXECUTED**, one transaction per chart (divergent_flagged → computed_extension → single, in
  order, each filtered on `verification_pass_status = 'two_pass_verified'` so earlier updates in
  the same transaction can't double-touch a row):
  - `482012f1`: 0 → divergent_flagged, 540 → computed_extension, 102,832 → single. 0 remaining.
  - `1c826d5a`: 0 → divergent_flagged, 540 → computed_extension, 103,080 → single. 0 remaining.
  - `cb73cd3d`: 45 → divergent_flagged, 540 → computed_extension, 102,551 → single. 0 remaining.
  - **310,128 rows total**, every transaction self-verified 0 remaining `two_pass_verified` in
    scope before its own commit.
- Post-state, all 3 charts: only `single`/`computed_extension`/`divergent_flagged`/
  `documented_approximation` (pre-existing, correctly untouched) remain in scope — 0
  `two_pass_verified` anywhere. Earned rows (`chart_dashas` mudda+narayana) unchanged at 675 —
  `chart_facts` writes cannot touch `chart_dashas` rows; confirmed anyway.
- Served-delta note: `ganita_structural_get` v3 previously reported `grade=ganita_fact`/
  `verified_fraction=1.0` over rows this backfill found genuinely empty of real verification
  (per the prior session's own framing) — that overclaim is now corrected for all 3 charts, not
  just the canonical one.
- Post-write invariant dispatch: **exact reconciliation.** `chart_facts.two_pass_verified`
  347,438→37,310 (−310,128, matches the write precisely); `computed_extension` +1,620 (540×3
  charts); `divergent_flagged` 0→45 (cb73cd3d only). Aggregate unchanged at 8 checks/5 FAIL — the
  same 5 out-of-scope findings from S1, nothing new introduced.

**S6: DONE.**

---

## S7 — ga_sensitive adjudication: HALT, not PERMIT

Investigated (read-only, `origin/main`): `ga_sensitive_writer.py`'s `_make_row()` hardcodes
`verification_pass_status="two_pass_verified"` for ~34 fact_categories with no comparison logic
gating it — real divergence computations exist (`ak_divergent`, BPHS-vs-PyJHora `tolerance_arcsec`)
but never gate the emitted status; the writer's own docstring admits this ("two-pass check only,
NOT the served value"). Effectively the entire live population is unearned: 8,750/8,775 rows on
the canonical chart, ~35,100 estate-wide. Same defect class as S5/S6, but **blocked by a genuinely
build-fatal guard**: `build_ga_sensitive_for_ayanamsha` unconditionally `raise ValueError` if any
row would be `single` (confirmed real via the prior session's independent consumer audit — unlike
similar-looking but inert "build-fatal" claims in `ga_structural`/`ga_vargas`'s docstrings, this
one is genuinely fatal).

Fixing the honesty defect requires relaxing that guard, which changes the writer's contract from
"claim verified or halt the build loudly" to "ship honestly-labeled unverified data instead" — a
real behavior/safety-posture change, not a retag. Per CLAUDE.md §N.2 ("if a writer seems to need a
contract change → STOP and raise with the native") and the prior session's own explicit,
unambiguous warning ("no agent may 'just relax the raise' to make its own change pass — named as
the single most dangerous edit available tonight, deferred as a governance decision") — this is
not resolvable from evidence the way S6's scoping question was. The facts clarify the stakes; they
don't answer whether silent-unverified is an acceptable trade against loud-build-failure for
sensitive-category data. That's Abhisek's call, not mine to make on his behalf.

**S7: HALTED.** No contract amendment, writer fix, or backfill attempted. Smallest human action:
Abhisek decides PERMIT or DECLINE on relaxing `ga_sensitive_writer.py`'s build-fatal single-row
guard; if PERMIT, a future session can do the contract amendment + writer fix + write-gated
backfill in one PR, same pattern as S5/S6.

---

## S8 — chart_facts CHECK constraint (last step, needs S5 done + S6/S7 settled-or-halted — met)

- Full 13-value `ALL_STATUSES` vocabulary (not the 4-value `RESTRICTED_TABLE_VOCAB`), `NOT VALID`
  (684MB live table — plain `ADD CONSTRAINT` would take ACCESS EXCLUSIVE for a full scan),
  idempotent `DO $$ IF NOT EXISTS ... END $$` guard. Zero violating rows confirmed live
  immediately before authoring — true specifically because S5's drain (59,282 rows) and S6's
  backfill (310,128 rows) ran earlier in this same campaign to make this safe. New parity test
  (`test_chart_facts_check_constraint_matches_all_statuses_exactly`) — text-level, parses the
  migration's `IN (...)` list and asserts exact match to `ALL_STATUSES`, proven real (not
  tautological) by removing a member and confirming a specific-diff failure, then restoring.
- **Independent Verifier (general-purpose agent): FAIL first pass** — caught a real, concrete
  migration-number collision: `main` had advanced since the number was allocated (an unrelated
  campaign's PR #1059 landed migrations 537/538 while this session was in flight). Confirmed via
  the repo's own `migration_number_guard.ts`, not a file listing. **Fixed**: renumbered 537→539,
  re-verified clean with the same guard tool + full test suite. Everything else in that pass
  (SQL correctness, live zero-violation re-check, no pre-existing constraint collision, protocol
  compliance) passed clean.
- **Migration-guard review (purpose-built agent, 1 infra retry — API error, not a finding;
  succeeded on retry): "MIGRATION SAFE ✓"** — re-confirmed live no collision (checked open PRs too,
  not just `main`), re-confirmed the idempotency guard scoped tighter than this repo's own
  precedent, re-confirmed zero violating rows a third independent time, ran the parity test itself.
  Two non-blocking WARNs, both fixed before merge: (1) stale "537's SQL" string in the test
  assertion message (cosmetic, from the renumber) — corrected; (2) `NOT VALID` avoids the scan but
  the `ALTER` still needs a brief ACCESS EXCLUSIVE to write the catalog entry — on a live table,
  Postgres's FIFO lock queue means a stuck DDL could queue behind another transaction and then
  queue every subsequent query behind itself — added `SET LOCAL lock_timeout = '2s'`, scoped to
  the migration's own transaction, so it aborts cleanly instead of queueing indefinitely.
- Full CI-sanctioned suite, fresh post-fix: **5121 passed, 0 failed, 24 skipped, 86 deselected**
  (excluding `test_l0_remedy_corpus.py`, the same pre-existing CI-teardown-excluded file from S4;
  with it included: 5129 passed, 24 failed — all in that one file, unrelated to this change).
- **Gate: PROCEED.** All CI checks green, including — for the first time this campaign — all 5
  previously pre-existing baseline failures (Boot-time pointer validation, Earned-Signal Gate,
  Fact-Category Pinning Gate, Naming Governance Gate, TAP-5/7/S-13), a cumulative side-effect of
  S1-S7's writes. TOCTOU re-check immediately pre-merge: 0 violating rows. **Merged** via merge
  queue → `6f1b8d45` on `main`.
- **Post-merge verification**: tracked the full auto-deploy chain (merge → CI-on-main success →
  `deploy-web` job via `workflow_run` trigger → migration runner) rather than assuming — this was
  the campaign's first step to actually add a migration file, so nothing about deploy timing could
  be inherited from S1-S7. Deploy completed successfully (`Build & Deploy Web`, `Build & Deploy
  Sidecar` both green).
  - `pg_constraint` confirms: `chart_facts_verification_pass_status_check` exists, `convalidated=f`
    (correctly `NOT VALID`), full 13-value list matches exactly.
  - **Probe A** (illegal status, rolled-back transaction): rejected with
    `violates check constraint "chart_facts_verification_pass_status_check"` — the error names
    this exact constraint, proving the probe reached the real code, not a coincidental failure.
  - **Probe B** (legal status, control, rolled-back): succeeded (`INSERT 0 1`) — proves the
    constraint discriminates rather than blocking everything.
  - Confirmed 0 trace of either probe row remains post-rollback.
  - **Final invariant dispatch: 8 total checks, 5 FAIL, 3 PASS — identical to S1's baseline FAIL
    set, nothing new.** The 5 FAILs are exactly the two out-of-scope findings flagged back in S1
    and never touched since (4 `claim_vs_evidence` — `bodha_cgm_edges`, `bodha_cgm_nodes`,
    `bodha_msr_signals`, `l1_tajik_varsha_year_lords` — + 1 `detector_liveness` missing `jhora`).
    The 3 PASSes (`claim_vs_evidence` on `chart_dashas`/`chart_divisionals`/`chart_facts`) were
    **already passing in S1's original run** (verified by re-reading that run's cached log rather
    than assuming) — correction to an earlier over-claim in this ledger that framed `chart_facts`'s
    pass as a new side-effect of S8's CHECK constraint; that reasoning conflated two unrelated
    mechanisms (the CHECK governs legal *values*, not the invariant's own `EXAMINED_PREDICATE`
    concept) and was wrong. The real, attributable change across the campaign is the 17
    `vocabulary_conformance` FAILs that existed in S1's original 25-check run (`chart_facts` ×2,
    9 `bodha_*` tables) — all drained by S5, and the checks now don't appear at all once their
    tables have zero residue, which is why the total check count dropped from 25 to 8, not just
    the fail count.

**S8: DONE.**

---

## SESSION CLOSE

Worktrees removed: `madhav-wt-s2-ayanamsha`, `madhav-wt-s4-vimshottari`, `madhav-wt-s5-drain`,
`madhav-wt-s5-run`, `madhav-wt-s6-structural`, `madhav-wt-s8-check` — all confirmed removed, ledger
confirmed outside all of them throughout. This session's proxy (port 5432) killed; pre-existing
proxies on 5433/5434 (not started by this session) left untouched. Credential scratchpad file
deleted; `DATABASE_URL` unset. Nothing half-applied: every write this session either completed
with full post-state verification or was never attempted (S7 HALTED cleanly, no partial state).

Starting `main`: `18cd00fd`. Ending `main`: `6f1b8d45`. Full report in the session transcript.

Post-write invariant dispatch confirms exact precision: `chart_dashas` tier_report moved
`single` 1,458,795→1,459,744 (+949), `two_pass_verified` 1,189→713 (−476), `classical_match`
1,181→708 (−473) — matches the write exactly, no drift. Bonus: `chart_dashas`'s own
`claim_vs_evidence` check now **PASSes** (713 remaining verified rows, 0 outside declared
`EXAMINED_PREDICATE` = `level_n=1 AND kp_sublevel IS NULL`) — unlike the 4 tables flagged earlier
with no predicate declared at all. Aggregate unchanged at 22 FAIL/3 PASS (expected — S3 was scoped
to the earned-vs-wrong-ayanamsha conflict only, not the broader vocabulary drain, which is S5).


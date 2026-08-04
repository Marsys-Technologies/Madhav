# M22 Night Ledger — Swarm Edition

Append-only. One entry per gate, write, review verdict, escalation.

## Phase -1: Isolation & Reconnaissance

- **Worktree**: `/Users/Dev/madhav-m22-night`, detached HEAD off `origin/main`.
- **Starting origin/main SHA**: `f65680abcd74d4fba03aa93ed64d3a4998f07e87`
- **Drift note vs brief's "known environment"**: brief states the shared checkout sits on
  `parishodhana/dark-corpus-remeasure`. Actual shared checkout (`/Users/Dev/Vibe-Coding/Apps/Madhav`)
  is on branch `int-929-final` (HEAD `f91ec00b`), not `parishodhana/dark-corpus-remeasure`. This is
  exactly the kind of plan-time-fact drift the brief warns about. Not touching the shared checkout
  regardless, per instruction — noted for the record only, no action required.
- **origin/main moved during fetch**: `1405db5c..f65680ab` (ṢAḌ-DARŚANA / other campaign activity,
  consistent with brief's expectation that main moves overnight).

## FINDING — Standing invariant (workflow 325445415) non-functional in CI

- **What**: `.github/workflows/verification-invariant.yml` job `verification_pass_status —
  claim-vs-evidence, vocabulary, detector liveness` reads `DATABASE_URL` from
  `secrets.PROD_DATABASE_URL` directly, with no Cloud SQL proxy step in the job. The one run in its
  history (`30794710893`, 2026-08-03T07:43:47Z, `schedule` trigger) failed:
  `psycopg.OperationalError: connection ... "127.0.0.1", port 5432 ... Connection refused` — the
  runner has no local proxy, so a loopback-form secret value can never connect there.
- **Provenance verified, not assumed**: the workflow was introduced in **PR #1029**
  ("fix(m22): scope dasha verdicts to examined rows, honest serve wording, standing invariant"),
  merged 2026-08-02T08:04:57Z. `gh run list` shows **exactly one run ever** for this workflow — the
  one above. So the accurate claim is "has never had a working run since introduction in #1029,"
  not "failing repeatedly since #1029" — there is no run history to support a higher count, and I'm
  not asserting one.
- **Same class of gap as TAP suite** (`platform/scripts/audit/tap/README.md`): DB-backed CI jobs
  with `continue-on-error` pending a provisioned `TAP_DATABASE_URL` / proxy step. This job has
  neither the proxy step nor `continue-on-error` — it hard-fails silently-in-effect on schedule.
- **Recommendation (NOT applied tonight — CI infra, out of write scope)**: same fix S-13/TAP-7 got
  in #990 — add a `cloud-sql-proxy` step to the job and repoint at a TCP-form `PROD_DATABASE_URL`,
  or provision the secret correctly. Someone should also check whether `PROD_DATABASE_URL` is the
  same stale/socket-form pattern this session hit on `amjis-pipeline-db-url` tonight.
- **Ruling (native, this session)**: repair the *evaluation path*, not the check — run the invariant
  script **locally, verbatim, unmodified**, against the live DB via this session's proxy, and use it
  in place of workflow-dispatch for every write-gate step 6 this run. Not a bypass: same code, same
  teeth, evaluated where the DB is reachable.

## Stage 1 — Local invariant baseline (pre-write, proves local execution + establishes before-picture)

- Full output: `stage1_baseline_invariant.json` (this worktree). Exit code 1 (FAILs present, expected).
- **22 FAIL / 25 checks** — reflects the known pre-state exactly, per the brief's own prediction:
  - `claim_vs_evidence` FAILs: `chart_dashas` (1,358,993 claim verified; 1,356,488 outside the
    examined predicate — the §6.18 broadcast defect, still present); plus several undeclared tables
    (`bodha_cgm_edges`, `bodha_cgm_nodes`, `bodha_msr_signals`, `l1_tajik_varsha_year_lords`).
  - `vocabulary_conformance` FAILs: `chart_facts` PROHIBITED `'PASS'` ×5,428, deprecated
    `'single_pass'` ×32,614 (matches this session's earlier read-only verification exactly), plus
    PROHIBITED `'pass'`/`'PASS'` residue across several `bodha_*` tables.
  - `detector_liveness`: **PASS** — `two_pass_verdict` and the live `ga_nakshatra` path both still
    fire `divergent_flagged` on a plausible wrong value. The disagreement path is alive; future
    PASS-with-zero-fails on this check would be trustworthy, not a dead detector.
- **Conclusion**: local execution is proven (matches known-bad pre-state exactly) — this is now the
  before-picture every Stage 1/2/3 write is measured against via local re-run, not workflow dispatch.

## Stage 1 — Executor pre-flight (dry-run only) + Independent Verifier

- **Executor** (dry-run both scripts): `backfill_unexamined_dasha_tiers.py` — all 5 safety
  properties confirmed (env-not-arg, dry-run default, idempotent `<> target` WHERE, tier targets
  match ruling, CHECK-legal live-confirmed). Scoped (chart 482012f1) dry-run: 448,327→single,
  386→classical_match, 0→single (non-native rule N/A). Unscoped: 1,356,488→single,
  1,181→classical_match, 135→single.
  `drain_prohibited_verification_status.py` — **self-halted safely** (exit 1, no writes): its own
  live `pg_constraint` guard found a third CHECK-constrained table, `kala_tithi_pravesha`
  (0 rows, CHECK permits only `two_pass_verified`/`divergent_flagged`, not `single`), which its
  docstring didn't know about (docstring claims only 2 constrained tables). No `--chart` flag
  exists on this script — table-wide only, not scopable.
- **Independent Verifier** (own SQL, did not read Executor's output first): `chart_dashas`
  unexamined-claiming-verified count = 1,356,488 (own query, own predicate) — matches Executor's
  unexamined bucket exactly. Flagged explicitly (not guessed) that "membership-type" is not a
  distinct vocab/schema concept, only inferable from schema (hypothesis, not fact) — routed to
  Gate Reviewer rather than accepted on the script's say-so. Confirmed via own SQL: target sets
  are disjoint from earned rows (mudda 780, narayana 345, native vimshottari 64, ga_nakshatra 537).
  Cross-check: 1,358,993 − 1,357,804 = 1,189 = 780+345+64 exactly.

## GATE R1 (Opus review) — VERDICT

**`backfill_unexamined_dasha_tiers.py` → PROCEED.** Reviewer independently read the actual writer
producer (`ga_dashas_writer.py`) and confirmed the "membership-only" system_id list
(yogini/ashtottari/chara_karaka/naisargika → classical_match) is bit-for-bit the set of verifiers
whose success path returns `CLASSICAL_MATCH`, in both directions (no under- and no over-inclusion).
Found the load-bearing warrant neither Executor nor Verifier surfaced: writer line 3082's
`examined = level_n==1 and kp_sublevel is None` is the exact logical complement of the backfill's
Rule 1 predicate — this is provable writer-parity, not coincidental agreement. Confirmed
`chart_dashas` holds exactly 2 statuses DB-wide today (two_pass_verified, single — no
classical_match/divergent_flagged rows exist yet), so partition is exhaustive: 1,356,488+1,181+135
+(780+345+64) = 1,358,993 exactly.
Non-blocking findings routed (not acted on tonight): **D1** script docstring claims a disjointness
assertion that doesn't exist in code (not a data hazard, disjointness independently confirmed by
reviewer inspection); **D2** Rules 1/3 lack Rule 2's `= 'two_pass_verified'` filter — latent risk
once `divergent_flagged` rows exist, Rule 1 would silently flatten them to `single`; **D3**
`_verify_narayana` docstring overclaims checks its code doesn't implement (345 rows remain
defensibly earned regardless, protected by the hard limit either way).
**Operational hazard**: unscoped write is a single ~1.36M-row UPDATE, one commit — holds locks on
~93% of chart_dashas for its duration. No concurrent chart_dashas writer may run during that step.

**Authorized sequence (exact numbers, HALT on any mismatch):**
1. Scoped write: `--chart 482012f1-710e-4a25-994a-93821f5871aa --execute` → expect 448,327→single,
   386→classical_match, 0 (rule 3), total 448,713.
2. Verify: scoped AFTER must read two_pass_verified=409, classical_match=386,
   single=483,592 (35,265+448,327); the 409 must decompose exactly mudda 240 / narayana 105 /
   vimshottari 64 (all level_n=1, kp_sublevel NULL). Any movement in those three = HALT
   (earned-rows tripwire).
3. Unscoped write: `--execute` (no `--chart`) → expect 1,356,488→single, 1,181→classical_match,
   135→single, total 1,357,804.
4. Post-verify: DB-wide two_pass_verified must equal exactly 1,189 (=780+345+64); classical_match
   must equal exactly 1,181; no status outside {two_pass_verified, classical_match, single} may
   appear. Any deviation = HALT, do not proceed to Stage 2.
5. Idempotency proof: re-run dry-run unscoped, all three rules must report 0.

**`drain_prohibited_verification_status.py` → FIX identified, NOT authorized to run tonight.**
Reviewer proved the guard-fix is structurally sound (halt condition should be "CHECK permits a
SOURCE value while rejecting target," not "target not permitted" — kala_tithi_pravesha's CHECK
permits none of {PASS,pass,single_pass} so the correct guard would emit NOTE not HALT there) and
strictly in-bounds (no CHECK migration, no vocab member, code-only). **Explicitly declined to
authorize same-night fix+execute regardless**: same-night patch-and-run by the same agent chain
has zero independent-review latency — exactly the "looked fine" shape this campaign exists to stop.
Also found the drain's benefit is partly cosmetic: live producers still emit `single_pass`
(`bo_karanajala.py`, `bo_bimba.py`) — that portion regresses on next L2 rebuild; only the
PASS/pass portion (12,459 rows) is durable. Docstring's "only two constrained tables" claim is now
factually false and must be corrected in the same diff as the guard fix.
**Human action to unblock** (recorded for morning report, not for tonight): human-reviewed ~10-line
PR (guard condition + docstring correction), then an attended run in a future session — not this
autonomous one.
**Stage 1 proceeds on the dasha backfill alone.**

## Stage 1 write execution — Step 1+2 confirmed, Executor crash, independently re-verified before resuming

- **Step 1 (scoped write)**: Executor agent ran it; reported exact expected output.
- **Step 2 (verify)**: Executor's own re-query confirmed exact expected match: chart-scoped
  two_pass_verified=409 (mudda 240/narayana 105/vimshottari 64 — earned-rows tripwire clean),
  classical_match=386, single=483,592. Agent then began Step 3.
- **CRASH**: Executor agent process died mid-response (`API Error: Connection closed mid-response`)
  immediately after stating "Proceeding to Step 3" — genuinely unknown at that point whether Step 3
  had started, was mid-transaction, or hadn't begun. Per the brief's own crash-resilience design
  ("a crash at any point leaves prod clean and the ledger is sufficient to resume"), did NOT trust
  the agent's stated intention — independently re-verified real DB state directly (Conductor's own
  query, not delegated) before taking any further action:
  ```
  chart_dashas DB-wide: classical_match=386, single=550,499, two_pass_verified=910,280
  active/recent chart_dashas queries: 0 · locks on chart_dashas: 3× AccessShareLock only (no write lock)
  ```
- **Arithmetic proof this is exactly the post-Step-1-only state, not a partial Step 3**:
  1,358,993 (baseline two_pass_verified) − 448,713 (Step 1 total) = **910,280** ✓ exact match.
  0 (baseline classical_match) + 386 (Step 1) = **386** ✓ exact match.
  102,172 (baseline single) + 448,327 (Step 1) = **550,499** ✓ exact match.
  No active queries, no write locks → nothing in flight. **Step 3 never started. State is clean,
  consistent, and safe to resume from exactly this point.** Resuming Executor for Step 3 onward.

## Step 3 attempt #1 — infra failure mid-transaction, clean rollback, Conductor arithmetic error found and corrected

- **Failure**: Executor launched Step 3 (unscoped `--execute`), computed `BEFORE {two_pass_verified:
  910280, single: 550499, classical_match: 386}` (matches post-Step-1 state exactly), staged rule 1's
  UPDATE (908,161 rows), then the DB connection was severed server-side mid-transaction
  (`server closed the connection unexpectedly` — not a client timeout). Script exited 1 before its
  single end-of-run `conn.commit()`. Postgres auto-rolled-back the entire open transaction.
- **Independently re-verified, not trusted from the agent's narration**: DB-wide chart_dashas after
  the failure is byte-identical to before the attempt (910,280 / 550,499 / 386). Zero active/idle
  sessions on chart_dashas at check time. **Confirmed: nothing partial committed.**
- **CONDUCTOR ERROR, caught and corrected**: the "expected 1,356,488 / 1,181 / 135" figures given to
  the Executor for the *unscoped* Step 3 write were the ORIGINAL pre-Step-1 global totals — stale,
  because Step 3 runs AFTER Step 1 already consumed 448,713 of those rows for the scoped chart. The
  Executor's own computed number (908,161 for rule 1) is arithmetically correct:
  1,356,488 − 448,327 = 908,161. Corrected expected deltas for the Step 3 retry:
  **rule 1 (unexamined→single): 908,161 · rule 2 (membership→classical_match): 1,181−386=795 ·
  rule 3 (non-native vimshottari→single): 135−0=135 · total: 909,091.**
  The Step 4 FINAL post-verify targets (two_pass_verified=1,189, classical_match=1,181) are
  unaffected by this correction — those are ordering-independent global totals. Sanity check: total
  chart_dashas row count queried directly = 1,461,165 = 1,189+1,181+1,458,795 exactly (single after
  full completion = 550,499+908,161+135 = 1,458,795). Conserved, no rows created/destroyed.
- **Root-cause lead checked before retry**: queried `pg_stat_activity` for autovacuum on
  `chart_dashas` — none currently running. `statement_timeout`=30min, `idle_in_transaction_session_
  timeout`=10min (both generous for this UPDATE; the failure reads as a proxy/network-level drop,
  not a Postgres-enforced timeout). No corrective action taken beyond confirming no active
  contention before retrying — retry #1 of Step 3, well within the two-attempt retry cap.

## Step 3 attempt #2 — same failure mode, retry cap hit, root cause found, escalating to Gate Reviewer

- Executor's own agent process crashed again mid-report (`API Error: Connection closed mid-response`)
  right as it began reading the retry's real output. Did NOT trust its narration ("process has
  exited, reading real output now") — independently re-verified myself, twice:
  1. My own direct verification query (fresh Bash call, not delegated) ALSO failed:
     `psycopg2.OperationalError: server closed the connection unexpectedly`.
  2. Checked the proxy's own log directly: real evidence of underlying tunnel instability —
     `connection aborted - error reading from instance: read tcp ...: connection reset by peer` at
     2026-08-03 17:01:07 and again 17:30:56 (the Cloud SQL Auth Proxy's TCP tunnel to the actual
     instance, not a client-side artifact). **Root cause identified: proxy/network-level connection
     instability over this long-running (~3hr) proxy session, not a data or script problem.**
- **Action taken**: killed the old proxy (PID 57309), started a completely fresh one (PID 99398),
  confirmed listening on 127.0.0.1:5432.
- **Re-verified chart_dashas state via the FRESH connection**: `classical_match=386, single=550499,
  two_pass_verified=910280` — byte-identical to the pre-attempt-2 state. Zero active queries, zero
  write locks (one harmless AccessShareLock). **Confirmed: attempt #2 also fully rolled back, zero
  corruption, zero partial commit. Both failed attempts were clean — the idempotent-write design and
  Postgres's own transaction atomicity did exactly what they're supposed to do.**
- **This is now 2/2 failed attempts at Step 3 — the retry cap.** Per the brief's own rule ("two
  attempts at any failing check, then Gate Reviewer"), NOT attempting a third retry unilaterally.
  Escalating to Gate Reviewer: root cause is understood and addressed (fresh proxy), data state is
  clean and unchanged, decision needed is whether to authorize attempt #3 now on the fresh
  connection, or require some other precaution (e.g. narrower per-rule execution instead of one big
  transaction) first.

## GATE — Step 3 escalation VERDICT: FIX (partitioned PROCEED), unmodified retry REJECTED

Opus Gate Reviewer rejected "fresh proxy = fixed" as insufficient: independently identified the
ACTUAL root cause as structural, not incidental — `tcp_keepalives_idle/interval/count=0` (zero
bytes flow during a ~30min single UPDATE, the canonical cause of a mid-statement reset through
Cloud SQL Auth Proxy) compounding with `max_wal_size=1024MB`/`checkpoint_timeout=300s` under a
908,161-row (62% of table) single-transaction UPDATE forcing repeated checkpoints and sustained
instance I/O correlating with the proxy log's instance-side resets. Two identical-signature
failures is a pattern, not bad luck — reviewer explicitly named "just retry it, it's probably
fine" as the trap being avoided here.

**Fix required zero code change.** `chart_dashas` holds exactly 3 charts; only 2 have remaining
work post-Step-1. The `--chart` flag (already proven in Step 1) partitions the unscoped run into
two scoped runs whose union is provably identical to the unscoped run (chart_id has zero NULLs).
Reviewer independently re-derived the full per-chart split via own SQL — third independent
confirmation of 908,161/795/135/909,091, plus full reconciliation closing exactly to the final
targets (two_pass_verified 1,189 / classical_match 1,181 / single 1,458,795 / total 1,461,165).

**Authorized sequence (replaces the unscoped Step 3), with keepalives added to the DSN (config, not
code) targeting the actual root cause:**
`DATABASE_URL="postgresql://amjis_app@127.0.0.1:5432/amjis?keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5"`
1. `--chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a --execute` → expect 437,765/385/70, total 438,220
   (canary: smaller than the already-proven-successful 448,327 Step-1 write). Verify chart-scoped
   AFTER: single=471,697, two_pass_verified=340, classical_match=385. Any mismatch → HALT, do not
   continue, escalate (the diagnosis would be wrong, not just unlucky).
2. `--chart cb73cd3d-9eba-4220-9902-0de91566e980 --execute` → expect 470,396/410/65, total 470,871.
   Verify chart-scoped AFTER: single=503,506, two_pass_verified=440, classical_match=410.
3. Step 4 (unchanged targets): DB-wide two_pass_verified=1,189, classical_match=1,181,
   single=1,458,795.
4. Step 5: unscoped dry-run, all rules report 0.
5. Step 6: local invariant re-run.
**Non-blocking finding**: module docstring line 73 claims an exclusivity assertion that doesn't
exist in code (reviewer verified by hand the predicates ARE exclusive regardless — no live risk,
routed as a follow-up, not fixed tonight).

## STAGE 1 — CLOSED, all steps independently confirmed

Steps 3a/3b both exact match: 437,765/385/70 (total 438,220) and 470,396/410/65 (total 470,871).
Independent re-verify after each: chart 1c826d5a → single=471,697/two_pass_verified=340/
classical_match=385; chart cb73cd3d → single=503,506/two_pass_verified=440/classical_match=410.
**Step 4 DB-wide post-verify: exact match** — two_pass_verified=1,189, classical_match=1,181,
single=1,458,795, no other status present in chart_dashas.
**Step 5 idempotency proof: exact match** — unscoped dry-run, all 3 rules report 0.
**Step 6 local invariant**: `stage1_post_dasha_invariant.json` vs baseline —
`claim_vs_evidence:chart_dashas` flipped FAIL→PASS (was "1,358,993 claim; 1,356,488 outside
predicate", now "1,189 claim; 0 outside predicate, tolerance 0"). Overall tally moved 22 FAIL/25 →
**21 FAIL/25**, exactly one fewer, exactly the chart_dashas one — every other FAIL (vocabulary
residue in chart_facts/bodha_* — drain-script territory, correctly untouched) unchanged. **This is
the write moving in the predicted direction, confirmed at check level, per write-gate step 6.**

**Stage 1 final state**: dasha backfill complete and verified; drain script read-only pre-flighted,
never executed (FIX identified, deferred to a human-reviewed PR + attended future session per GATE
R1). No password ever constructed/printed/embedded in any command. Two clean, zero-corruption
rollbacks encountered and resolved via root-cause fix (chart-partitioning + keepalives), not
worked around blindly. Proceeding to Stage 2 (Stage 2 depends only on Stage 1, per the brief).

## Stage 2 — 4 parallel Executors dispatched (ga_structural, ga_vargas, ga_sensitive, ga_sade_sati)

Re-fetched origin/main first: unchanged at f65680ab (worktree still current). All 4 Executors
instructed to re-derive independently (not inherit numbers), read verification_vocab.py themselves,
query pg_constraint themselves for CHECK-legality, propose (not apply) a code diff + test/
determinism assessment. ga_vargas Executor crashed once mid-investigation (API-level, before any
findings existed) — resumed cleanly, no work lost.

### ga_sensitive (chart_facts only, confirmed disjoint from ga_sensitive_degree by source_calculation
prefix) — REPORT IN

- **No `verification_vocab` import anywhere in the writer.** `_make_row()` hardcodes
  `verification_pass_status="two_pass_verified"` as the default; ~34 fact_categories all emit it
  unless explicitly overridden (floored/external_computation_required/skipped_malformed_source, plus
  one illegal invented literal `"data_error"` — not in the settled vocab at all, found via grep).
- **(a) genuine: NONE found** — real divergence computations exist (`ak_divergent`, BPHS-vs-PyJHora
  `tolerance_arcsec`) but never gate the status (docstring admits "two-pass check only, NOT the
  served value"); one site (`esoteric_point_bhrigu_bindu`) is a literal `two_pass_verdict(x,x)`
  tautology the vocab module's own docstring already names as a known residual.
- **(b) no comparison → single: effectively the entire live population** — 8,750/8,775 scoped
  (482012f1), 26,250/26,325 unscoped. `single`/`divergent_flagged` currently 0 rows.
  `floored` (25/75 rows) is correct as-is, untouched.
- **(c) approximation**: `karakamsa_position.longitude_d9_sidereal` → `documented_approximation`
  (chart_facts has ZERO CHECK constraints, confirmed live — legal); `saturn_derived_point.
  YAMAGANDA_SPHUTA` → writer's own comment names `computed_extension` specifically, not
  `documented_approximation` — different vocab member than assumed, code says so directly.
- **Blocking dependencies found (not fixed, flagged for the executing session)**: (1)
  `build_ga_sensitive_for_ayanamsha` unconditionally `raise ValueError` if ANY row is `single` —
  this must change to non-fatal before the honest-default fix can ship at all; (2) two test suites
  (`test_ga5_writer.py::test_all_two_pass_verified`, `test_ga_sensitive_enrichment.py` ×5 assertions)
  currently assert the unearned status as correct — codify the bug, need rewriting alongside the fix.
- No double-build-determinism test exists; assessed what one needs (run twice with different
  build_ids, confirm delete-then-insert replaces not accretes, confirm status/value stability —
  noting fact_id itself is NOT build-stable by design since build_id is a hash input, so determinism
  must be checked at the (fact_category,subject,key,formula_id) tuple level, not raw fact_id).

### ga_vargas (chart_divisionals) — REPORT IN

- No `verification_vocab` import; 24 hardcoded literal sites, 21 of them unconditional
  `two_pass_verified` with zero comparison logic anywhere (confirmed: 0 `divergent_flagged` rows
  exist across all 3 charts in the DB — the disagreement path for this table has never fired once).
- **(a) genuine: NONE found.** The one real comparison in the file (`forensic_gate_vargas`) gates
  the BUILD (halts on Sun/Lagna mismatch), not any row's status.
- **(b) no comparison → single**: 21 categories, 13,172/23,542 rows scoped (56%), 39,516/70,626
  unscoped. Two categories (D60 deity, saptavargaja bala) are ALREADY correctly `single` with a
  comment citing the CHECK constraint as the reason — those stay unchanged. `classical_match`
  (D2 hora, 100/300 rows) reviewed and left alone, no misuse found.
- **(c) approximation confirmed CHECK-illegal on this table** — live `pg_constraint` query:
  `chart_divisionals_verification_pass_status_check` permits only
  `{two_pass_verified, classical_match, divergent_flagged, single}` — matches
  `verification_vocab.py`'s `RESTRICTED_TABLE_VOCAB` exactly, matches the brief's claim exactly.
  All approximation-shaped rows (D40/D45/D108 hardcoded devata cycle arrays — same defect class
  M-17 already proved fabricated for D60) go to `single`, not `documented_approximation`.
- **Ancillary bug found, correctly left untouched (out of scope)**: `scope_cap` sentinel rows
  (5 expected: Uranus/Neptune/Pluto/Lilith/MC) collide on the table's unique index (only
  `fact_subject` differs, not part of the unique key) — only 1 of 5 survives per build. Data-loss
  bug adjacent to but distinct from verification-status; flagged for a separate follow-up, not this
  campaign's scope.
- Same blocking-dependency shape as ga_sensitive: tests currently assert the unearned status
  (`test_d60_verification_two_pass`, `test_dignity_two_pass_verified`, `test_verification_two_pass`)
  and one test (`test_all_rows_valid_verification_status`) hardcodes its OWN copy of the vocab set
  instead of importing `RESTRICTED_TABLE_VOCAB` — exactly the "disagreeing copy" pattern the vocab
  module's docstring warns against; should be fixed to import from source regardless of this campaign.
- No double-build-determinism test exists for this writer (a sibling/legacy module has one, wrong
  module); assessed what's needed, same shape as ga_sensitive's assessment.

### ga_sade_sati (chart_facts only) — REPORT IN

- Three code paths default to unconditional `two_pass_verified`; 12 call sites already correctly
  route through `_verif_for_text`/`_verif_for_maybe_none` (honest, added in a prior M-22 pass) but
  emit the DEPRECATED alias `single_pass` rather than canonical `single` — flagged as a spelling fix,
  not a reclassification. The one real check in the file (`two_pass_verify_cycles`, duration ±600d +
  ordering) only ever HALTS the build on failure — never sets any row's status; genuinely backs the
  cycle/phase timestamp rows regardless.
- **(a) genuine — unchanged**: 320 canonical / ~1,280 unscoped — exactly the
  `sade_sati_cycle`/`sade_sati_phase` start/end/duration rows that `two_pass_verify_cycles` actually
  examines.
- **(b) no comparison → single**: 4,327 canonical / 12,972 unscoped. Includes a **genuine
  cross-row bug**: `sade_sati_modifier_overlay` duplicates flags already honestly tiered in its
  sibling `sade_sati_phase` row (via `_verif_for_maybe_none`), but the duplicate-emission code path
  never applies that function — same value, inconsistent tier, across two rows. Also flags 2
  permanently-`false` stub fields (`compound_with_{next,prior}_cycle_flag`) never actually computed —
  retagging to `single` is honest but doesn't fix the stub itself; routed as a product decision, not
  a mechanical retag.
- **(c) approximation → documented_approximation**: `sade_sati_phase_quarter`'s quarter
  start/end/duration (720 canonical / 2,880 unscoped) — a linear 4-way split of phase duration, not
  an independently observed transit event (unlike vishakha/janma/anumukha, which ARE real Saturn
  sign-change events and stay `single`/genuine as applicable). Confirmed CHECK-legal: live query
  shows `chart_facts` has ZERO verification_pass_status CHECK constraint (third independent
  confirmation of this fact across all 3 Stage-2 chart_facts writers tonight).
- Reconciliation: 320(a) + 4,327(b) + 720(c) + 920(already single/single_pass) = 6,287, exact match
  to canonical-chart total row count.
- Same blocking-dependency shape: two existing tests assert the deprecated `single_pass` output and
  will need updating once the alias fix lands; no double-build-determinism test exists, full
  assessment provided including a concrete mutation-test proposal to prove the (a)-tier check can
  actually fail (not just always pass).

### ga_structural (chart_facts only, 81 fact_categories — by far the largest of the 4) — REPORT IN

- `_base_row()` hardcodes `verif: str = "two_pass_verified"` as default; verification_vocab never
  imported; 93 call sites enumerated exhaustively (77 explicit literal, 6 falling to default, plus
  small single/single_pass/floored/conditional-approximation groups already correct).
- **(a) genuine: empty**, confirmed by exhaustive per-call-site trace, not assumed — no site both
  computes two independent values AND conditions status on their agreement.
- **99.90% of this writer's canonical-chart rows (103,372/103,477) claim two_pass_verified with
  zero backing check.** Unscoped: 310,128/310,549. Category-level breakdown confirms only the
  already-known-fixed categories (conjunction_per_varga, conjunction_within_orb, dosha_label,
  graha_composite_state_classification, yoga_label, non-Aries functional_class) ever deviate —
  every one of the other ~75 categories is 100% two_pass_verified, no exceptions, live-confirmed.
- **Two edge cases explicitly flagged for native/Gate Reviewer judgment, NOT bulk-reclassified:**
  1. `graha_in_house_composite_strength` — the file's ONE real cross-formula comparison
     (bphs_weighted vs simple_multiplication, stored `cross_formula_divergence`), but status is
     NOT gated on it — all 540 canonical cross_formula_divergence rows are non-zero (formulas never
     agree) yet all 1,620 rows uniformly two_pass_verified. Executor's interim proposal: the two
     formula outputs → `single`, cross_formula_divergence → `computed_extension` (not itself
     verified, derived by extension) — flagged as needing a ruling, not applied.
  2. `bhava_chalit_rasi_divergence` — genuinely two-pass BY CONSTRUCTION (only emitted when equal-
     bhava vs whole-sign house computations disagree) — textbook `divergent_flagged` case, currently
     mislabeled `two_pass_verified`. This is the closest thing to real class-(a) logic in the file,
     just with an inverted label — proposed fix: → `DIVERGENT_FLAGGED`.
- CHECK-constraint: chart_facts confirmed (4th independent confirmation tonight) to have ZERO
  verification_pass_status CHECK — documented_approximation legal here (70 unscoped rows already
  correctly use it for non-Aries-lagna functional-class rows).
- Existing test `test_ga8_writer.py::test_aspect_parashari_verif_two_pass` asserts the unearned
  status as correct — needs updating alongside the fix. `TestTwoPassInvariants` class is
  **misleadingly named**: only calls a pure row-builder twice in the same process against fixed
  mock data (trivial function-determinism, no DB, no build_id variation) — NOT a real double-build
  test. No DB-backed double-build-determinism test exists for this writer at all.

## STAGE 2 RECONNAISSANCE — CLOSED, all 4 Executors reported

**Cross-cutting pattern, confirmed independently 4×**: none of the 4 writers import
`verification_vocab.py`; all hardcode literal strings; in every writer the `two_pass_verified`
default vastly outnumbers any row backed by a real check; `chart_facts` confirmed 4× independently
to have NO CHECK constraint (documented_approximation always legal there); `chart_divisionals`
confirmed to reject documented_approximation (bucket c collapses to `single` there). Every writer's
existing test suite CODIFIES the unearned status as correct and needs rewriting alongside the fix —
expected per the brief's own parenthetical, not a surprise. **No writer has a real DB-backed
double-build-determinism test today** — all would need to be newly authored.

**Scale is far larger than the stage's own title ("Demote the 392,001 writer rows") suggested**:
canonical-chart totals alone across the 4 writers: ga_structural 103,477 + ga_vargas 23,542 +
ga_sensitive 8,775 + ga_sade_sati 6,287 ≈ **142,081 rows on ONE chart**; unscoped is proportionally
larger across all 3 charts in the DB. This is a much bigger code-change + backfill than the stage
title implied — four separate writer files, ~200+ call sites total, new tests needed from scratch
in every case, plus two genuinely ambiguous cases (graha_in_house_composite_strength,
bhava_chalit_rasi_divergence) that are not mechanical reclassifications.

**Adjacent bugs found and correctly left untouched (out of this campaign's scope, flagged for
follow-up)**: ga_sensitive's illegal `data_error` literal (not a vocab member at all); ga_vargas's
scope_cap sentinel data-loss (unique-index collision, 4/5 floored-body rows silently lost per
build); ga_sade_sati's sade_sati_modifier_overlay tier-inconsistency bug (duplicates a sibling
row's flag value without applying the same honest-tier function) and 2 permanently-false stub
fields never actually computed.

**Not proceeding directly to implementation.** Given the scale is roughly 3-4x what the stage's own
framing implied, and two of the four writers surfaced genuinely ambiguous cases requiring judgment
rather than mechanical fixes, synthesizing all 4 reports for a Gate Reviewer consultation on HOW to
proceed (scope for tonight vs. defer, ruling on the two edge cases, and whether four large
simultaneous writer-code changes is appropriate for one autonomous unattended session) before
writing a single line of code.

## GATE R2 SCOPING RULING (Opus) — scope cut from 4 writers to 2 full + 1 code-only + 1 deferred

**Operational blockers caught, fixed immediately:**
- **Worktree was on DETACHED HEAD** — real risk of losing all work to a stray checkout. Fixed
  immediately: `git checkout -b m22-night/stage2-honest-tiers` before any edit.
- **`divergent_flagged` is BUILD-FATAL** in ga_structural/ga_vargas/ga_sensitive (halts build, per
  their own docstrings) — the Executor's proposed `bhava_chalit_rasi_divergence → divergent_flagged`
  fix must be proven inert (0 canonical-chart rows, confirmed) before it ships anywhere near a live
  build path.
- **`formula_id` is NULL on all 1,620 `graha_in_house_composite_strength` rows** — the writer passes
  `"bphs_weighted"` as a positional arg that lands in `fact_key`, not `formula_id`. A backfill
  keyed on `formula_id` would silently match ZERO rows. Must segment on `fact_key`/
  `source_calculation` instead. Caught before it became a real "looked fine" defect.
- **Ruled: backfill must be `UPDATE`-only, touching only verification_pass_status, NEVER a rebuild**
  — a rebuild would let every other latent writer bug (e.g. ga_vargas's scope_cap collision) into
  prod. This also makes "byte-identical except tier" true by construction, not by test assertion.

**Scope ruling:**
| Writer | Ruling |
|---|---|
| ga_sade_sati | **SHIP FULL** (fix+test+backfill) — honest-tier helpers already exist & already tested, only writer with genuine (a) rows, no blocking guard |
| ga_vargas | **SHIP FULL** — most mechanical, CHECK collapses (b)+(c) to one target (`single`), zero ambiguous cases |
| ga_structural | **CODE + TESTS ONLY, backfill held for a second gate** — 99.9% uniform and both edge cases now ruled (below), but 103k-row backfill is the largest irreversible act of the night |
| ga_sensitive | **DEFERRED ENTIRELY** — guard removal is a contract change (CLAUDE.md §N.2: contract changes STOP, go to native), not a retag; explicit instruction: **no agent may "just relax the raise" to make its own change pass** — named as the single most dangerous edit available tonight |

**ga_structural edge cases — RULED:**
- `graha_in_house_composite_strength`: Executor's proposal CONFIRMED, with a stronger proof —
  `bphs_score = simple_score × shadbala_ratio × aspect_modifier` is an algebraic rescaling, live
  data confirms divergence never zero (min 0.2112, max 0.7729) — **this was never a two-pass at
  all**, not a failed one. → `bphs_weighted`/`simple_multiplication` = `single`,
  `cross_formula_divergence` = `computed_extension`. `divergent_flagged` explicitly REFUTED here
  (would inject 540 false anomaly signals + risks the build-fatal halt above). **Mandatory
  same-changeset fix**: the code comment claiming this is "a genuine classical shadbala + bhava
  bala comparison" is FALSE and is why these rows were promoted once already — leaving it invites
  re-promotion by a future agent.
- `bhava_chalit_rasi_divergence` → `DIVERGENT_FLAGGED`: CONFIRMED (genuinely two-pass by
  construction, only emitted on real disagreement) — discriminator: divergent_flagged is legal only
  when both passes compute the SAME quantity and could have agreed; composite-strength fails that
  test, this one passes. **Caveat**: 0 rows on the canonical chart (all 45 live rows on `cb73cd3d`
  only) — invisible to the brief's "measure served delta for one chart" acceptance test unless that
  measurement is explicitly taken on `cb73cd3d`, not silently passed as verified on the canonical
  chart alone.

**Test-rewrite standard (applies to all implementation from here)**: mechanical primary control via
SQL diff (snapshot pre-change, assert every column except verification_pass_status byte-identical
post-change) rather than trusting agent-authored assertions; pre-declare the exact transition
matrix before editing, any row moving outside it = HALT; net-verified must strictly decrease and no
row may move INTO two_pass_verified; assertion DELETIONS (not silent flips) with recorded rationale
for tests whose premise IS the bug (e.g. `test_all_two_pass_verified`); no test may assert a status
by reading back the literal the code emits at that site (tautology); every changed test surfaced
for human review in the gate report.

**Deferred, with reasons**: ga_sensitive entirely (governance decision); all double-build-
determinism test authoring (highest-risk/lowest-value item — flagged instead: `TestTwoPassInvariants`
is confirmed MISNAMED, tests a pure function twice in one process against fixed mock data, no DB, no
build_id variation — proves nothing about two-pass verification); ga_structural's 103k-row backfill
(second gate); the chart_facts CHECK constraint (brief says recommend-only, and would need to admit
~10 tiers not 4); ga_vargas's scope_cap data-loss bug (separate lane); sade_sati's 2 permanently-
false stub fields (product decision); the 5,428 live `PASS` rows remain present (drain script's
territory, confirmed still not touched).

**Authorized sequence, each gated on the prior landing clean**: ga_sade_sati (full) → ga_vargas
(full) → ga_structural (code+tests only, backfill held).

## ga_sade_sati — SHIPPED (Executor, this session)

**Code fix** (`ga_writers/ga_sade_sati_writer.py`): imported `TWO_PASS_VERIFIED`/
`UNVERIFIED_DEFAULT`/`assert_legal` from `brahmagyan.verification_vocab`. `_make_row` and
`_emit_cycle_rows`'s local `R()` default demoted `two_pass_verified` → `UNVERIFIED_DEFAULT`.
8 genuine cycle/phase keys (`sade_sati_cycle`.{cycle_start_iso,cycle_end_iso,duration_days,
duration_years}, `sade_sati_phase`.{phase_start_iso,phase_end_iso,duration_days,
duration_years}) made explicit `TWO_PASS_VERIFIED` (the values `two_pass_verify_cycles()`
actually examines). `_emit_dhaiya_rows`'s hardcoded positional literal → `UNVERIFIED_DEFAULT`.
`sade_sati_modifier_overlay`'s 5 fields (the cross-row tier-inconsistency bug) now apply
`_verif_for_maybe_none(...)` to the same source variable their `sade_sati_phase` sibling row
uses. `sade_sati_phase_quarter`'s 3 timestamp/duration keys → explicit
`"documented_approximation"`. `_verif_for_text`/`_verif_for_maybe_none` now return
`UNVERIFIED_DEFAULT` unconditionally in both branches (the non-placeholder/non-None branch no
longer emits the deprecated `single_pass` alias). `assert_legal(status, table="chart_facts")`
added immediately before `_insert_rows`'s INSERT.

**Transition matrix** (independently re-derived via live per-(fact_category,fact_key,status,
count) query, chart 482012f1, `source_calculation LIKE 'ga_sade_sati_writer/%'`, 6,287 rows
total — reconciles exactly against Stage-2-recon's 320/4,327/720/920 split):
- 320 rows (8 key-sites × cycle counts): `two_pass_verified` → **unchanged** (the 4 cycle +
  4 phase genuine timestamp/duration keys).
- 4,327 rows (61 key-sites): `two_pass_verified` → **`single`**.
- 720 rows (3 key-sites, `sade_sati_phase_quarter`): `two_pass_verified` →
  **`documented_approximation`**.
- 560 rows: `single_pass` → **`single`** (deprecated-spelling fix, no bucket change).
- 360 rows: already `single` → **unchanged**.

**Tests**: `test_ga9_sade_sati_enrichment.py`'s `test_verif_for_text_flags_pending_fallback_as_single`
and `test_verif_for_maybe_none_flags_none_as_single` rewritten (not silently flipped) to assert
`UNVERIFIED_DEFAULT` in both branches, with rationale comments. No other test in the repo asserts
`two_pass_verified` for any of the categories/keys touched here (grepped `sade_sati_cycle`,
`sade_sati_phase`, `dhaiya_period`, `kantaka_shani_period`, `ashtama_shani_period`,
`vishakha_shani_period`, `janma_shani_period`, `anumukha_shani_period`,
`sade_sati_modifier_overlay`, `sade_sati_phase_quarter`, `sade_sati_cancellation_check`,
`sade_sati_concurrent_dasha_overlay`, `sade_sati_downstream_cross_reference`,
`sade_sati_saturn_retrograde_subset`, `ardha_ashtama_shani_period` cross `two_pass_verified` repo-
wide — only this writer file itself matched). `test_ga9_writer.py` (63 tests) +
`test_ga9_sade_sati_enrichment.py` (19 tests) + `test_nar_ga_sade_sati_concurrent_dasha_label.py`
(4 tests) = **86/86 passed**, no pre-existing failures encountered.

**Backfill**: snapshot-based, UPDATE-only (`chart_facts` UPDATE, never `build_ga_sade_sati()`).
Dry-run counts matched the declared matrix exactly on first attempt (no HALT triggered). 3
UPDATEs executed inside one transaction, each gated on `cursor.rowcount` matching its declared
count exactly before proceeding. Post-write, all 24 non-status columns confirmed byte-identical
across all 6,287 rows (before vs. after snapshot, keyed on `fact_id`), and every row's status
transition confirmed to match the declared matrix exactly, before COMMIT. Final state (verified
independently post-commit): `two_pass_verified`=320, `single`=5,247, `documented_approximation`=720
— 0 rows remain `single_pass`/`pass`/`PASS` in this writer's scope. Net-verified strictly
decreased (5,367 claiming `two_pass_verified` pre-write → 320 post-write); no row moved INTO
`two_pass_verified`.

**Downstream note (not acted on, out of scope)**: `pipeline/orchestrator/writers/bo_laksana.py:2204`
reads `vpass == "two_pass_verified"` to set `source_corroboration_count_by_text` (5 vs 2) for
`sade_sati_*`-class L2 signals — this backfill will change that L2 writer's output the next time
it runs against chart 482012f1 (fewer rows will get the higher corroboration count), which is the
intended honest-tiering effect propagating downstream, not a bug.

**2 permanently-false stub fields** (`compound_with_next_cycle_flag`, `compound_with_prior_cycle_flag`):
left as stubs per the ruling — now honestly tiered `single` (they were in the 4,327 `two_pass_verified
→ single` bucket), stub *behavior* untouched.

## ga_vargas — SHIPPED (Executor, this session)

**Confirmed before editing**: worktree on `m22-night/stage2-honest-tiers` (not detached), ga_sade_sati's
fix present as uncommitted changes, untouched per instruction. `brahmagyan.verification_vocab` exports
`UNVERIFIED_DEFAULT`/`TWO_PASS_VERIFIED`/`CLASSICAL_MATCH`/`assert_legal` exactly as named in the
brief. Live `pg_constraint` re-confirmed `chart_divisionals_verification_pass_status_check` restricts
to exactly `{two_pass_verified, classical_match, divergent_flagged, single}` — the recon's "one
demotion target" claim holds.

**Code fix** (`ga_writers/ga_vargas_writer.py`): imported `CLASSICAL_MATCH`/`TWO_PASS_VERIFIED`/
`UNVERIFIED_DEFAULT`/`assert_legal`. All 18 unconditional dict-literal `"two_pass_verified"` sites
(dignity, vargottama, formula-variant, D30-lord-per-amsa, vimsopaka, ashtakavarga, karaka×3,
rollup×9-keys-one-site, D9-lagna-special, pushkara×2, karya-bhava, Lal Kitab, D108-karma, D150/D2700
rishi, cross-varga-harmonic, both scope_cap sentinels) → `UNVERIFIED_DEFAULT` via one
whitespace-preserving regex substitution, then hand-verified. The deity-attribution ternary
(`"single" if varga_n == 60 else "two_pass_verified"`) collapsed to unconditional
`UNVERIFIED_DEFAULT` per the ruling's explicit instruction — D60's own value doesn't change
(`UNVERIFIED_DEFAULT == "single"`), only the other 13 vargas' deity rows lose the unearned
`two_pass_verified` claim.

**One site found beyond the ruling's named locations, same defect, fixed under the same authorized
logic rather than escalated**: `_verification_status(category, varga_n)` — a second helper with the
*identical* "single for X, else two_pass_verified" shape, gating on `TWO_PASS_VARGA_POSITIONS =
{60, 108, 150, 2700}` set-membership (a static set, not a real comparison). This is the actual
producer behind `varga_position`'s per-key `v_status` (call site line ~830, written at line ~900),
and its live DB footprint proves it's exactly the same bug: `varga_position.{sign, sign_id,
degree_in_sign, formula_id, sign_lord, house_from_varga_lagna}` each showed a 1250/200 single/
two_pass_verified split that lines up exactly with non-{D60,D108,D150,D2700} vs.
{D60,D108,D150,D2700}. Ruling's "genuine=EMPTY" and "no real comparison gating status anywhere in
this writer" cover this site by the same logic used to justify collapsing the deity ternary —
fixed the same way (fallback return → `UNVERIFIED_DEFAULT`), flagged here in full for review rather
than silently folded into the "21 sites" count.

**Left untouched, confirmed correct**: the 2 already-fixed `single` sites with CHECK-constraint-
citing comments (D60 deity/quality ternary branch — now folded into the unconditional value, same
result; `varga_saptavargaja_bala_component` M-18/M-22 fix); the 1 `classical_match` site (D2
`varga_hora_class.hora_class`/`hora_d2_house`, CR-58); 3 genuinely-original `single` categories never
mislabeled (`varga_house_lord`, `varga_house_occupant`, `varga_d27_directional_quadrant` — docstring's
own "single: standard 16-varga positions, house lord/occupant, D27 quadrant" line, confirmed these
were never `two_pass_verified` in code or DB). `_build_ashtakavarga_rows`'s docstring-only
`sum(sarva)==337` claim (no runtime assert behind it, confirmed via grep) — left un-implemented,
flagged in-code as a future-ticket item, not touched as part of this pure demotion.

**`assert_legal`**: sole INSERT/UPDATE path into `chart_divisionals` for this writer is
`_write_rows_batch` (confirmed: the file's other `_UPSERT_SQL` constant is dead code, never
referenced; every other `ga_writers/*.py` reference to `chart_divisionals` is read-only SELECT).
Added a per-row `assert_legal(r["verification_pass_status"], table="chart_divisionals")` loop
immediately before the `executemany`/per-row fallback, so an illegal status raises a clear
`ValueError` before it can reach the DB as a swallowed `CheckViolation`.

**Transition matrix** (declared before any test/backfill, via live per-(fact_category,fact_key,
status,count) query, chart 482012f1, pre-write): every currently-`two_pass_verified` row for this
chart, and only those rows, becomes `single` — **13,172 rows exactly**, spanning 50 (category,key)
combinations (full breakdown captured pre-write). Confirmed exhaustive both directions: no
fact_category/fact_key combo left at `two_pass_verified` in the fixed code, and no other status
(`single`=10,270, `classical_match`=100) or other chart_id in scope. No disambiguation needed —
ga_vargas is chart_divisionals' sole writer.

**Tests** (`tests/test_ga6_writer.py`): imported `RESTRICTED_TABLE_VOCAB`/`UNVERIFIED_DEFAULT` from
`brahmagyan.verification_vocab`. `test_d60_verification_two_pass` → renamed
`test_d60_verification_single`, asserts `UNVERIFIED_DEFAULT` (expectation FLIPS, per the ruling —
the ternary is now unconditional). `test_dignity_two_pass_verified` → renamed
`test_dignity_verification_single`, same treatment. `test_verification_two_pass` (D30-lord-per-amsa)
→ renamed `test_verification_single`, same treatment. All three carry a rationale docstring
explaining what changed and why, and assert against the imported `UNVERIFIED_DEFAULT` constant
(not the writer's own literal) to avoid the tautology the brief warned against.
`test_all_rows_valid_verification_status` rewritten to import `RESTRICTED_TABLE_VOCAB` instead of
its own hardcoded 4-member set copy (correctness fix independent of the demotion, done regardless
per instruction). `test_d1_verification_single` and `TestD27QuadrantRows::test_single_verification`
left unchanged (test sites never touched by this fix). Module docstring's item #50 updated to match
(was: "D60 position is two_pass_verified; D1 is single"). Repo-wide grep for `two_pass_verified`
found no other test file importing/testing `ga_vargas_writer` (only `test_ga6_writer.py`,
`test_verification_pass_status_vocab.py`, `test_ga_orchestrator_conformance.py`,
`test_beta_d_house_convention.py`, `test_d1_5b_b5_completions.py` reference the module at all; none
of the other four assert `two_pass_verified` for a category this fix touched).

**Test run**: `test_ga6_writer.py` — **131/131 passed**, no pre-existing failures. Regression sweep
(files importing `ga_vargas_writer` + the vocab suites): `test_verification_vocab.py` (19),
`test_verification_pass_status_vocab.py` (5), `test_ga9_sade_sati_enrichment.py` (23),
`test_ga_orchestrator_conformance.py` (33), `test_beta_d_house_convention.py` (8),
`test_d1_5b_b5_completions.py` (11) — all passed. Whole-suite `--collect-only` (5,069 tests) confirmed
zero import errors from the new `brahmagyan.verification_vocab` import.

**Backfill**: snapshot-based, UPDATE-only (`chart_divisionals` UPDATE, `build_ga_vargas()` never
called). Script: pre-write snapshot of all 13,172 affected rows' full column set keyed on PK `id`
→ written to disk; dry-run count re-check against the declared 13,172 inside the same transaction
(would HALT with no write attempted on mismatch — did not trigger); single `UPDATE ... WHERE
chart_id = $1 AND verification_pass_status = 'two_pass_verified'` inside one explicit transaction;
`cursor.rowcount` confirmed 13,172 (would ROLLBACK on mismatch — did not trigger); post-write
re-select of the same 13,172 ids, all 30 non-status columns confirmed byte-identical to the
pre-write snapshot for every row (would ROLLBACK on any mismatch — did not trigger), and every
row's `verification_pass_status` confirmed now `single`; only then COMMIT. Independently
re-verified post-commit via a separate `psql` query (outside the script): `classical_match`=100,
`single`=23,442, total=23,542 — unchanged total, `two_pass_verified`=0. Matches the declared matrix
exactly; net-verified strictly decreased (13,172 → 0); no row moved INTO `two_pass_verified`.
Pre/post snapshots retained on disk in the session scratchpad for audit trail.

**Known ancillary bug, confirmed still out of scope, not touched**: `scope_cap` category's
unique-index collision (4/5 floored-body sentinel rows lost per build) — both live `scope_cap`
sentinel rows for this chart were included in the 13,172-row demotion (they were mislabeled
`two_pass_verified`, now honestly `single`/`UNVERIFIED_DEFAULT`), but the row-loss bug itself is
untouched, per the ruling.

## ga_structural — CODE + TESTS SHIPPED, BACKFILL DEFERRED (Executor, this session)

**Hard constraint confirmed throughout and at close: zero DB writes.** All DB access this session
was read-only `SELECT`, each wrapped in an explicit `BEGIN TRANSACTION READ ONLY; ... ROLLBACK;`
(psql `-v ON_ERROR_STOP=1`, `\copy ... TO STDOUT` avoided in favor of plain `SELECT`/`--csv` after
a `\copy` parse hiccup). No `UPDATE`/`INSERT`/`build_ga_structural()` call was made. Re-verified
independently post-edit: `graha_in_house_composite_strength` on canonical chart 482012f1 still
shows all 1,620 rows as `two_pass_verified` in the live DB (would be the first category to move if
anything had leaked through) — code changes did not touch the database.

**Confirmed before editing**: worktree on `m22-night/stage2-honest-tiers` (not detached);
`ga_sade_sati_writer.py` / `ga_vargas_writer.py` present as uncommitted Stage-2 work, untouched
per instruction (only `ga_writers/ga_structural_writer.py` and `tests/test_ga8_writer.py` edited
this session).

**Divergent_flagged build-halt safety investigation (mandatory pre-check, done first per
instruction)**: read every `_write_halt_log(` call site in `ga_structural_writer.py` (5 total) —
`ARGALA_COUNT_WRONG`/`VIRODHA_COUNT_WRONG` (144-row count assertions), `UPSTREAM_ABSENT` (GA3–GA7
presence check), and `TWO_PASS_STRUCTURAL` (×2, one per build path) which wraps exactly
`_verify_no_duplicate_fact_ids` + `_verify_no_ga3_overlap` + `_verify_citation_completeness` +
`_linter_check_rows`. None of these four functions read `verification_pass_status` at all —
`_linter_check_rows` only scans `fact_value_text` for narration phrases (`FORBIDDEN_PATTERNS`,
imported from `ga_positions_writer`, unrelated to the vocab). **Finding: the module docstring's
claim "divergent_flagged → halt build, write CONDUCTOR_HALT_LOG" (line 65, pre-fix) was FALSE —
no code path in this file halts on a row carrying that status.** Cross-checked
`assert_legal(status, table="chart_facts")` also does not reject `DIVERGENT_FLAGGED` (legal,
non-prohibited vocab member; `chart_facts` carries no CHECK constraint). Grepped the whole repo for
`divergent_flagged` in test files: the only writer-specific zero-divergent-flagged assertions
belong to `test_ga5_writer.py` and `test_ga7_writer.py`/`test_ga_dashas_narayana.py` (other
writers) — nothing in `ga_structural`'s own test files asserts zero `divergent_flagged`. **Safe to
proceed** — did not stop. Fixed the stale docstring line in the same changeset (a false claim
directly on point to this exact safety question is exactly the kind of trap a future agent could
walk into) rather than leaving it to contradict the corrected code.

**Code fix** (`platform/python-sidecar/ga_writers/ga_structural_writer.py`, 263 lines changed):
imported `DIVERGENT_FLAGGED`/`UNVERIFIED_DEFAULT`/`assert_legal` from
`brahmagyan.verification_vocab`. `_base_row()`'s default `verif: str = "two_pass_verified"` →
`UNVERIFIED_DEFAULT` (covers the 6 call sites that omitted the kwarg, confirmed by AST-style
paren-matching script: 93 total `_base_row(` call sites, 6 without `verif=`, all mechanical). All
77 explicit `verif="two_pass_verified",` literals bulk-replaced via exact-string Python
`.replace()` (verified count before/after: 77 → 0), then the 2 sites that needed a *different*
target than the bulk default were hand-corrected back (`graha_in_house_composite_strength`'s
`cross_formula_divergence` → `"computed_extension"`; `bhava_chalit_rasi_divergence` →
`DIVERGENT_FLAGGED`) — no `COMPUTED_EXTENSION` named constant exists in `verification_vocab.py`
(confirmed by grep: only `TWO_PASS_VERIFIED`/`DIVERGENT_FLAGGED`/`CLASSICAL_MATCH` are exported),
so this uses the literal string, matching the existing convention in `ga_condition_writer.py`/
`ga_strength_writer.py`/`ga_yoga_writer.py` (none of which define a constant either). The 3
conditional/variable-assignment special cases (not matched by the bulk literal-string replace,
handled individually):
- `_build_bhava_bala_extended_rows`'s `verif_status = "two_pass_verified"  # Algebraic invariant
  holds` → `UNVERIFIED_DEFAULT`; comment corrected — `sub_sum` is computed but never compared
  against anything (confirmed: `sub_sum` has no other reference in the file).
- `_build_functional_class_rows`'s `fc_verif = "two_pass_verified" if lagna_sign == "Aries" else
  "documented_approximation"` → Aries branch only → `UNVERIFIED_DEFAULT` (non-Aries branch
  untouched). Root cause visible in the same function: `bphs_class` and `raman_class` are both
  `_get_functional_class_dynamic(g_name, lagna_sign)` — the identical call, not two independent
  derivations.
- `conjunction_per_varga`'s `verif="two_pass_verified" if varga != "D1" else "single"` → collapsed
  to unconditional `UNVERIFIED_DEFAULT` (both branches converge to the same honest default; D1's
  literal `"single"` and `UNVERIFIED_DEFAULT` are the same string, so D1 rows are byte-unchanged).

**Mandatory same-changeset fix applied**: the false code comment near
`graha_in_house_composite_strength` claiming "the cross-check is a genuine classical shadbala +
bhava bala comparison" (citing a Ring-2 verdict) replaced with a corrected comment explaining the
Gate Reviewer's algebraic-rescaling proof (`bphs_score = simple_score × shadbala_ratio ×
aspect_modifier`) and why `divergent_flagged` is explicitly refused for `cross_formula_divergence`
(structural certainty of the formula relationship, not a meaningful anomaly signal — reserved for
`bhava_chalit_rasi_divergence` where two passes genuinely could have agreed and didn't). The
`"floored"` fallback branch in the same function (missing-GA3-fact case) is unchanged, confirmed
correct as-is per the ruling.

**`assert_legal`**: sole INSERT path for this writer is `_insert_chart_facts_rows` (both
`build_ga_structural`'s per-ayanamsha loop and the heavy-orchestrator `run_substep` path call this
same function) — added `assert_legal(r["verification_pass_status"], table="chart_facts")` per row
immediately before the `executemany` tuple-build loop, same pattern as `ga_sade_sati`'s fix.

**Left untouched, confirmed correct** (per the ruling, verified by grep of remaining literals):
3× `"single_pass"` (`yoga_label`, `dosha_label`, `graha_composite_state_classification`), 1×
`"single"` (`conjunction_within_orb`), 1× `"floored"` conditional branch
(`graha_in_house_composite_strength`'s missing-fact fallback), `documented_approximation` for
non-Aries-lagna `functional_class` (0 live rows on canonical chart — Aries lagna in all 5
ayanamshas — but code path confirmed present and untouched). The 3 unrelated `summary["two_pass_
verified"]` occurrences (lines ~6259/6356/6412) are a build-level meta-flag tracking whether the
4 batch-level integrity checks passed — not a row's `verification_pass_status` — left as-is.

**Tests** (`tests/test_ga8_writer.py`, 37 lines changed): added
`from brahmagyan.verification_vocab import DIVERGENT_FLAGGED, UNVERIFIED_DEFAULT`.
`test_aspect_parashari_verif_two_pass` renamed
`test_aspect_parashari_verif_is_unverified_default`, flipped to assert `UNVERIFIED_DEFAULT`, with
a rationale docstring (not a silent flip — explains `aspect_parashari_given` is one of the
mechanical ~76 sites, no special-case ruling applies). `TestTwoPassInvariants` renamed
`TestRowBuilderPureFunctionStability` with a block comment explaining what it actually proves
(pure-function determinism: same builder called twice in-process against fixed mock data) vs. what
its old name implied (a real two-pass verification invariant — no DB, no `build_id` variation, no
independent second algorithm) — per instruction, no new DB-backed double-build test authored this
session (deferred, out of scope). Repo-wide grep for `two_pass_verified` combined with every
changed category (`aspect_parashari_given`, `graha_in_house_composite_strength`,
`bhava_chalit_rasi_divergence`, `conjunction_per_varga`, `graha_functional_class_per_ascendant`,
`bhava_bala_*`, `graha_yuddha`, `argala_natal_matrix`/`virodha_argala_natal_matrix`) found no other
test file with a live assertion on these categories' verification tier — `test_ga_condition_
jl026_graha_yuddha.py` mentions "two_pass_verified" once in its module *docstring* (prose, not an
assertion, describing writer ownership for a dual-write guard) — now stale but out of scope (no
assertion to fix, and rewriting it risks misrepresenting the JL-026 dual-write rationale that test
actually guards); flagged here rather than silently left. `bo_laksana.py:2204`'s
`5 if vpass == "two_pass_verified" else 2` (L2 downstream consumer, corroboration-count weighting)
will see fewer `5`s and more `2`s once this eventually backfills — the intended honest-tiering
effect propagating downstream, not a bug, not touched (out of scope, same pattern as the
`ga_sade_sati` entry above).

**Test run**: `tests/test_ga8_writer.py` + `ga_writers/__tests__/test_ga_structural_v6_doctrine.py`
+ `ga_writers/__tests__/test_ga_structural_shadbala_fact_key_pin.py` (found at that path, not
`tests/test_ga_structural_shadbala_fact_key_pin.py` as given — corrected) +
`tests/test_lane1_ga_structural_modularization.py` — **225/225 passed**, no pre-existing failures.
`TestRowParity::test_family_byte_stable_vs_pre_refactor` (14 parametrized cases) confirmed still
passing and confirmed NOT a false pass: its digest is `sha256` over
`"fact_category|fact_subject|fact_key"` only, deliberately excluding `verification_pass_status` —
correctly insensitive to this fix. Regression sweep beyond the four named files (12 more test
files across `tests/` + `tests/l2/` + `tests/l3/` importing `ga_structural_writer`, chosen because
they weren't in the required set but do import the module): **260/260 passed**, 1 pre-existing
unrelated `DeprecationWarning` (`bo_laksana.py:52`, `__package__ != __spec__.parent`).
`test_verification_vocab.py` + `test_verification_pass_status_vocab.py`: **25/25 passed**.

**Transition matrix** (read-only, live per-`(fact_category, fact_key, status)` query against
canonical chart 482012f1, all 5 ayanamshas, restricted to the 81 GA8-owned `fact_category` values
extracted programmatically from every `_base_row(` call site — **81 categories confirmed**, exact
match to the context's stated count). **NOT EXECUTED — for the record and the future backfill
session only.**

Total in scope: **103,477 rows** (matches the task context's "103k rows is the largest
irreversible act of the night" framing exactly). Aggregate: 103,372 currently `two_pass_verified`
(**100% of which would change** — zero survive as earned, confirming ruling ítem (a) genuine=EMPTY
exhaustively at the DB level, not just by code trace), 85 `single_pass` (unchanged), 20 `single`
(unchanged — both the 10 `conjunction_within_orb` and the 10 `conjunction_per_varga`-D1 rows,
since `UNVERIFIED_DEFAULT == "single"` byte-for-byte, so the D1 conjunction_per_varga rows are a
true no-op despite going through the "changed" code path). Of the 103,372 that would change:
**102,832 → `single`** (i.e. `UNVERIFIED_DEFAULT`) and **540 → `computed_extension`** (exactly the
`graha_in_house_composite_strength.cross_formula_divergence` key, confirmed 540 = 108 graha-house
pairs × 5 ayanamshas). No row would move INTO `two_pass_verified`. `bhava_chalit_rasi_divergence`:
**0 rows on the canonical chart** (confirmed — ruling's "untestable against the canonical chart"
note holds); queried chart `cb73cd3d-9eba-4220-9902-0de91566e980` separately (informational,
read-only, different chart) and confirmed **45 rows, all currently `two_pass_verified`**, which
would become `divergent_flagged` — matches the ruling's "45 live rows are on chart cb73cd3d"
statement exactly.

Full per-category breakdown (74 categories at "all keys" granularity + the 3-way
`graha_in_house_composite_strength` split + `bhava_chalit_rasi_divergence` both charts = 79 rows):

| fact_category | fact_key | current status | count | new status |
|---|---|---|---|---|
| argala_natal_matrix | (all keys) | two_pass_verified | 20880 | single (UNVERIFIED_DEFAULT) |
| aspect_jaimini | (all keys) | two_pass_verified | 540 | single (UNVERIFIED_DEFAULT) |
| aspect_jaimini_per_varga | (all keys) | two_pass_verified | 15660 | single (UNVERIFIED_DEFAULT) |
| aspect_matrix_summary | (all keys) | two_pass_verified | 60 | single (UNVERIFIED_DEFAULT) |
| aspect_parashari_given | (all keys) | two_pass_verified | 95 | single (UNVERIFIED_DEFAULT) |
| aspect_parashari_per_varga | (all keys) | two_pass_verified | 2755 | single (UNVERIFIED_DEFAULT) |
| aspect_parashari_received | (all keys) | two_pass_verified | 95 | single (UNVERIFIED_DEFAULT) |
| aspect_received_by_special_point | (all keys) | two_pass_verified | 449 | single (UNVERIFIED_DEFAULT) |
| aspect_tajik | (all keys) | two_pass_verified | 20 | single (UNVERIFIED_DEFAULT) |
| bhava_bala_aspectual | (all keys) | two_pass_verified | 60 | single (UNVERIFIED_DEFAULT) |
| bhava_bala_directional | (all keys) | two_pass_verified | 60 | single (UNVERIFIED_DEFAULT) |
| bhava_bala_lord | (all keys) | two_pass_verified | 60 | single (UNVERIFIED_DEFAULT) |
| bhava_bala_occupant | (all keys) | two_pass_verified | 60 | single (UNVERIFIED_DEFAULT) |
| bhava_bala_positional | (all keys) | two_pass_verified | 60 | single (UNVERIFIED_DEFAULT) |
| bhava_bala_temporal | (all keys) | two_pass_verified | 60 | single (UNVERIFIED_DEFAULT) |
| bhava_bala_total_extended | (all keys) | two_pass_verified | 60 | single (UNVERIFIED_DEFAULT) |
| bhava_significance_link | (all keys) | two_pass_verified | 5220 | single (UNVERIFIED_DEFAULT) |
| chart_center_of_gravity | (all keys) | two_pass_verified | 290 | single (UNVERIFIED_DEFAULT) |
| chart_cluster | (all keys) | two_pass_verified | 1305 | single (UNVERIFIED_DEFAULT) |
| combustion_per_varga | (all keys) | two_pass_verified | 725 | single (UNVERIFIED_DEFAULT) |
| composite_dispositor_strength | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| conjunction_per_varga | (all keys) | single | 10 | single (UNVERIFIED_DEFAULT — no-op) |
| conjunction_per_varga | (all keys) | two_pass_verified | 566 | single (UNVERIFIED_DEFAULT) |
| conjunction_special_point | (all keys) | two_pass_verified | 137 | single (UNVERIFIED_DEFAULT) |
| conjunction_within_orb | (all keys) | single | 10 | single (unchanged, untouched site) |
| contradiction_pair | (all keys) | two_pass_verified | 1740 | single (UNVERIFIED_DEFAULT) |
| convergence_count | (all keys) | two_pass_verified | 3045 | single (UNVERIFIED_DEFAULT) |
| dispositor_chain_per_varga | (all keys) | two_pass_verified | 1305 | single (UNVERIFIED_DEFAULT) |
| dispositor_tree | (all keys) | two_pass_verified | 1450 | single (UNVERIFIED_DEFAULT) |
| dosha_label | (all keys) | single_pass | 6 | single_pass (unchanged, untouched site) |
| graha_avastha_baladi | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| graha_avastha_deepta | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| graha_avastha_jagrad | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| graha_avastha_lifetime_exposure_summary | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| graha_centrality | (all keys) | two_pass_verified | 1305 | single (UNVERIFIED_DEFAULT) |
| graha_composite_state_classification | (all keys) | single_pass | 45 | single_pass (unchanged, untouched site) |
| graha_dignity_per_varga | (all keys) | two_pass_verified | 1305 | single (UNVERIFIED_DEFAULT) |
| graha_dispositor_chain | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| graha_effective_dignity_modified_by_aspects | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| graha_functional_class_per_ascendant | (all keys) | two_pass_verified | 70 | single (UNVERIFIED_DEFAULT — Aries branch, all 70 canonical rows) |
| graha_in_house_composite_strength | bphs_weighted | two_pass_verified | 540 | single (UNVERIFIED_DEFAULT) |
| graha_in_house_composite_strength | simple_multiplication | two_pass_verified | 540 | single (UNVERIFIED_DEFAULT) |
| graha_in_house_composite_strength | cross_formula_divergence | two_pass_verified | 540 | computed_extension |
| graha_saptavargaja_bala_component | (all keys) | two_pass_verified | 35 | single (UNVERIFIED_DEFAULT) |
| graha_special_state_rollup | (all keys) | two_pass_verified | 225 | single (UNVERIFIED_DEFAULT) |
| graha_tri_deva_role_strength | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| graha_vargottama_amplification_factor | (all keys) | two_pass_verified | 35 | single (UNVERIFIED_DEFAULT) |
| graha_yoga_karaka_flag | (all keys) | two_pass_verified | 35 | single (UNVERIFIED_DEFAULT) |
| graha_yuddha_per_varga | (all keys) | two_pass_verified | 16 | single (UNVERIFIED_DEFAULT) |
| house_strength_classification_rollup | (all keys) | two_pass_verified | 60 | single (UNVERIFIED_DEFAULT) |
| jaimini_tri_deva_role_per_graha | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| kala_sarpa_per_varga | (all keys) | two_pass_verified | 145 | single (UNVERIFIED_DEFAULT) |
| karaka_bhava_concordance | (all keys) | two_pass_verified | 4350 | single (UNVERIFIED_DEFAULT) |
| karaka_house_lord_overlap_flag | (all keys) | two_pass_verified | 60 | single (UNVERIFIED_DEFAULT) |
| karaka_web_per_varga | (all keys) | two_pass_verified | 1049 | single (UNVERIFIED_DEFAULT) |
| karakatva_strength_per_significance | (all keys) | two_pass_verified | 300 | single (UNVERIFIED_DEFAULT) |
| kendradhipati_dosha | (all keys) | two_pass_verified | 20 | single (UNVERIFIED_DEFAULT) |
| lord_aspects_lord_per_varga | (all keys) | two_pass_verified | 889 | single (UNVERIFIED_DEFAULT) |
| lord_in_house_per_varga | (all keys) | two_pass_verified | 1740 | single (UNVERIFIED_DEFAULT) |
| nakshatra_co_tenancy | (all keys) | two_pass_verified | 1 | single (UNVERIFIED_DEFAULT) |
| nakshatra_dispositor_chain | (all keys) | two_pass_verified | 50 | single (UNVERIFIED_DEFAULT) |
| nakshatra_lord_relationship | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| net_argala_per_varga | (all keys) | two_pass_verified | 1740 | single (UNVERIFIED_DEFAULT) |
| nway_config_per_varga | (all keys) | two_pass_verified | 83 | single (UNVERIFIED_DEFAULT) |
| panchadha_maitri | (all keys) | two_pass_verified | 210 | single (UNVERIFIED_DEFAULT) |
| parivartana_per_varga | (all keys) | two_pass_verified | 214 | single (UNVERIFIED_DEFAULT) |
| pranic_strength_per_graha | (all keys) | two_pass_verified | 45 | single (UNVERIFIED_DEFAULT) |
| sambandha_grade | (all keys) | two_pass_verified | 5220 | single (UNVERIFIED_DEFAULT) |
| significator_path | (all keys) | two_pass_verified | 360 | single (UNVERIFIED_DEFAULT) |
| tara_bala | (all keys) | two_pass_verified | 43 | single (UNVERIFIED_DEFAULT) |
| upapada_lagna | (all keys) | two_pass_verified | 10 | single (UNVERIFIED_DEFAULT) |
| vargottama_per_varga | (all keys) | two_pass_verified | 1260 | single (UNVERIFIED_DEFAULT) |
| vimsopaka_bala_per_graha | (all keys) | two_pass_verified | 35 | single (UNVERIFIED_DEFAULT) |
| virodha_argala_natal_matrix | (all keys) | two_pass_verified | 20880 | single (UNVERIFIED_DEFAULT) |
| virupa_drishti | (all keys) | two_pass_verified | 2755 | single (UNVERIFIED_DEFAULT) |
| yoga_label | (all keys) | single_pass | 34 | single_pass (unchanged, untouched site) |
| bhava_chalit_rasi_divergence (chart 482012f1, canonical) | diverges_from_rasi | — 0 rows, no divergence this chart — | 0 | N/A |
| bhava_chalit_rasi_divergence (chart cb73cd3d, informational, NOT canonical) | diverges_from_rasi | two_pass_verified | 45 | divergent_flagged |

Categories with zero live rows on the canonical chart, present in code but not in the table above
(confirmed absent, not missed): `graha_yuddha` (winner/loser/orb_deg — no classical-graha pair
within 1° orb on this chart today), `parivartana_pairs` (no mutual-reception pair this chart —
`parivartana_per_varga` is the populated sibling), `bhava_chalit_rasi_divergence` (as above).

**Not executed this session (per hard constraint + Gate Reviewer ruling)**: the backfill. Code and
tests are ready; the 103,372-row `UPDATE` (deliberately never a rebuild — see ga_sade_sati/
ga_vargas backfill notes above for why) is held for a dedicated future gate, per the ruling that
called this "the largest irreversible act of the night."

**No DB write occurred at any point in this task** — confirmed again at close via live re-query
(`graha_in_house_composite_strength` on 482012f1 still 1,620/1,620 `two_pass_verified`, matching
the pre-edit baseline exactly).

## Stage 2 — Served delta measurement (Executor, this session)

**Task**: measure the served `grounding_score` / `grade` / `warranty` delta for chart 482012f1
from tonight's two SHIPPED backfills (`ga_sade_sati`, `ga_vargas`; `ga_structural` HELD, no DB
write), confirm the direction is purely more honest, and HALT on any regression. Read-only DB
access only, no writes made this session. All three terms trace to real code, not a common name
mistaken for a UI label:

- **`grounding_score`**: `extractGroundingFromFactRows()` (`platform/src/lib/retrieval/envelope.ts`
  line ~1751) — the fraction of a response's SERVED rows whose `verification_pass_status` is a
  member of `VERIFIED_PASS_STATUSES`, a one-element set: only `two_pass_verified` counts (case-
  sensitive `isVerifiedPassStatus`, envelope.ts ~line 128 — deliberately narrow per Ruling 13,
  which found a stray `'pass'` alias had been accidentally acting as a safety net).
- **`grade`** (`EpistemicGrade`): `deriveEpistemicGrade()` (envelope.ts ~line 178) buckets that
  same fraction — `>=0.95` → `ganita_fact`, `>=0.5` → `verified_signal`, else →
  `single_pass_signal` (floored/contested/calibrated overrides aside, none apply here).
- **`warranty`**: not a literal field name anywhere in code — it is the human name this session's
  own prior artifacts (`00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md:1164`,
  `platform/scripts/backfill/drain_prohibited_verification_status.py:18`) give to sentence #3 of
  `buildReadingContract()`'s `reading_contract` paragraph (envelope.ts ~line 936-945): the
  `"N% of the rows here are cross-verified (two-pass)…"` line, generated from the same
  `verifiedFraction`. Grade and warranty are ALWAYS computed together (`buildEpistemicSummary` →
  `buildReadingContract`) and only inside the **v3 envelope path** — a response served in
  `legacy` format never carries either.

**Mechanism finding (this session's real contribution — required by task item 2, not paperable
over)**: which MCP-served surface reflects tonight's writes turns out to be **wildly uneven per
writer**, not "yes it's live" or "no it's stale," and the unevenness is itself the finding.

1. **`ga_sade_sati` (chart_facts, 15 SS categories) — grounding_score is live and DOES move.**
   `ganita_chart_facts_get` (registered `register_p1_aliases.ts:1315`, routes to the registry
   `chart_facts_query` capability, `register_d7_channel.ts` line ~1233:
   `content['grounding'] = extractGroundingFromFactRows(servedRowsForGrounding)`) computes
   `grounding_score` fresh from live `chart_facts` on every call — no caching, no L2
   intermediary. Live-called this session (`chart_id=482012f1`, all 15 SS categories,
   `ayanamsha_id` defaulted to `lahiri_chitrapaksha`, `shape=rows`, `limit=1000`): **1,259 rows
   match the filter (lahiri + INVARIANT scope), 1,000 served (page-capped), `grounding_score =
   0.064`.** Reconstructed BEFORE analytically from the `ga_sade_sati — SHIPPED` transition
   matrix above (5,367 of 6,287 total-family rows were `two_pass_verified` pre-write; dividing
   the 5-ayanamsha family evenly onto the lahiri-only slice this query scopes to:
   5,367/5 ≈ 1,073 of 1,259 ≈ **0.852**). The AFTER figure cross-checks exactly against the
   ledger's own aggregate: only 320 rows chart-wide remain `two_pass_verified` post-write (the 8
   genuine cycle/phase timestamp key-sites, correctly left alone); 320/5 ayanamshas = 64 per
   ayanamsha, and 64/1,000 served = **0.064** — matches the live-measured figure to the digit.
   Delta: **0.852 → 0.064**, a strict, large drop, with zero rows moving the other direction (the
   writer fix and the ledger both confirm "no row moved INTO `two_pass_verified`"). But: the
   *dedicated* `ganita_sade_sati_get` tool (no `response_format` param in its schema at all —
   confirmed via the live tool call below) **never computes or serves `grounding_score` in the
   first place** — it returns the `legacy` envelope unconditionally
   (`envelope(data, 'ganita_sade_sati_get')`, register_p1_ganita.ts ~line 845, no v3Extras), whose
   `grounding` block is hard-coded `{fact_ids: [], citations: [], grounding_score: null}`
   (envelope.ts's `legacy` object literal). Live-called this session: confirmed —
   `"grounding":{"fact_ids":[],"citations":[],"grounding_score":null}` on every row, even though
   every individual row in that same response body now carries
   `"verification_pass_status":"single"` (the post-backfill value, visible in the raw content).
   So: the raw fact changed and is visible; the SUMMARY SIGNAL a caller of this specific tool
   would use to judge confidence (`grounding_score`) doesn't exist on this tool at all, before or
   after — a pre-existing gap this backfill did not create and does not fix, flagged here because
   the task asked for the honest state of what's actually served, not just what changed.
   Neither `ganita_sade_sati_get` nor `ganita_chart_facts_get` ever computes `grade`/`warranty` —
   only the dedicated v3-envelope tools do (see `ga_structural` control below) — so for
   `ga_sade_sati` specifically, `grounding_score` is the only one of the three terms with any live
   served delta to report; `grade`/`warranty` are simply not in this writer's served surface.

2. **`ga_vargas` (chart_divisionals, 13,172-row backfill) — zero live serving surface computes
   `grounding_score`/`grade`/`warranty` from it AT ALL, before or after.** Confirmed by exhaustive
   grep (`grep -rln chart_divisionals platform/src platform-mcp/src`, then per-file check for
   `verification_pass_status`/`grounding`/`epistemic` near each hit): no file in the retrieval or
   MCP layer reads `chart_divisionals.verification_pass_status` into any grounding/epistemic
   computation. Structurally: (a) there is **no MCP tool for the `get_divisionals` registry
   capability at all** — `registry_bridge.ts:3483` names this explicitly: `'"get_divisionals", a
   non-existent MCP tool name'`; (b) the only path by which `chart_divisionals` rows reach an MCP
   caller is `ganita_chart_facts_get(divisional_chart=<varga>)`'s separate `divisional_facts`
   section (`register_d7_channel.ts` ~line 1272-1350), which is BY DESIGN excluded from
   `grounding` — the code comment there states outright: chart_divisionals rows "are never
   flattened into the chart_facts `rows`/`facts` arrays" and `servedRowsForGrounding` (the sole
   input to `extractGroundingFromFactRows`) is built exclusively from the `chart_facts` query
   above it, never touching the `dvRows` array. So the honest answer for `ga_vargas` is not "the
   delta is zero" — it's "**there is currently no served-response field anywhere in this
   instrument whose value tonight's 13,172-row `chart_divisionals` backfill could have changed**."
   The data changed in the DB (independently re-verified by this session's own earlier read:
   `classical_match=100, single=23,442, two_pass_verified=0`, matching the `ga_vargas — SHIPPED`
   entry above exactly); the change is simply invisible to every current consumer. This is a
   genuine gap worth flagging for a future session (a `get_divisionals` MCP tool or a
   `chart_divisionals`-aware grounding path does not exist yet), not something to paper over as
   "no delta, nothing to see."

3. **L2 downstream (both writers) — build-time consumption, not serve-time; separately stale.**
   `bo_laksana.py:2204`'s `5 if vpass == 'two_pass_verified' else 2` (flagged as "not acted on,
   out of scope" in both the `ga_sade_sati` and `ga_vargas` SHIPPED entries above) runs INSIDE the
   L2 orchestrator writer at BUILD time, not at serve time — a served `bodha_*` surface
   (`bodha_signals_get`, etc.) reflects whatever `bo_laksana` computed the last time the L2
   orchestrator ran against chart 482012f1, not live `chart_facts`/`chart_divisionals` state. This
   session did not check whether an L2 rebuild has run since tonight's writes (out of scope for a
   read-only served-delta measurement of the L1-facing tools; flagged per task item 2's explicit
   instruction not to paper over an unconfirmed propagation gap) — but the CODE-LEVEL fact is
   unambiguous: even after a hypothetical future `ga_structural` backfill, `bodha_*` responses
   will not move until the orchestrator re-runs, independent of anything measured here.

4. **Control group — `ga_structural` (HELD, DB untouched) confirmed unchanged, and is the ONE
   combination that actually serves `grade`+`warranty` live.** `ganita_structural_get` is the only
   MCP tool in this file wired to the full v3 envelope (`response_format:'v3'` →
   `buildEpistemicSummary` + `buildReadingContract`, register_p1_ganita.ts ~line 700-733).
   Live-called this session with `facet=dispositors` (categories
   `graha_dispositor_chain, dispositor_chain_per_varga, composite_dispositor_strength,
   parivartana_per_varga, kala_sarpa_per_varga` — all five are `ga_structural`-owned, all five
   were in tonight's HELD 103,372-row transition matrix, none were written): live result —
   `epistemic.grade = "ganita_fact"`, `verified_fraction = 1.0` (350/350 rows), warranty sentence
   `"100% of the rows here are cross-verified (two-pass) — the majority layer is confirmed."`
   This is BYTE-IDENTICAL to what the same call would have returned before this session started
   (nothing in `ga_structural`'s DB state moved — reconfirmed independently in this session's own
   earlier close-out re-query, `graha_in_house_composite_strength` still 1,620/1,620
   `two_pass_verified`) — i.e. this facet is STILL serving the overclaimed 100%-verified signal
   the Gate Reviewer ruled "genuine=EMPTY" for, exactly as expected for a deliberately-HELD
   backfill. Confirms two things at once: (a) no leakage — this session's DB is genuinely
   untouched for `ga_structural`; (b) the measurement mechanism itself is real and sensitive (it's
   the same machinery that produced `ga_sade_sati`'s 0.852→0.064 live delta above), so its silence
   here is meaningful, not a tooling gap.

**Directional check — PASS, no HALT.** Every transition inspected (this session's own live
queries, both writers' SHIPPED transition matrices above, and the writer source's `_verif_for_*`
helper logic) is monotonic in one direction only: `two_pass_verified`/`single_pass` →
`single`/`documented_approximation`/`computed_extension`. Zero rows moved the other way in either
writer (`ga_sade_sati`: "no row moved INTO `two_pass_verified`"; `ga_vargas`: same, plus
independently confirmed by this session's re-query showing `two_pass_verified=0` chart-wide for
`chart_divisionals`). Every served signal this session could actually measure moved in the honest
direction (`ga_sade_sati`'s live `grounding_score` 0.852→0.064) or did not move at all because
nothing downstream reads it yet (`ga_vargas`) or because its writer was correctly untouched
(`ga_structural` control). No case was found — live-measured or code-read — where a served
claim became LESS accurate. Nothing here is HALT-worthy.

**Limitation, stated plainly**: no genuine BEFORE snapshot of a live MCP response exists for
either writer (no prior-session cached response was found, and this task's DB access is
read-only, so no reconstructed pre-write query could be re-run against the now-post-write DB).
The `ga_sade_sati` BEFORE figure (0.852) is an analytical reconstruction from the SHIPPED entry's
own declared transition matrix, not a replayed live call — flagged per the task's own instruction
to be explicit about this rather than presenting it as an equivalently-live measurement to the
0.064 AFTER figure, which IS a genuine live call made this session
(`ganita_chart_facts_get`, 2026-08-03, chart 482012f1). The `ga_vargas` "no served surface"
finding required no BEFORE/AFTER at all — its answer is structural, not numerical, and is the
more important of the two findings for a future session to act on before this backfill's
honesty gain can actually reach a caller.

## GATE R2 FINAL RULING (Opus) — PROCEED

Independently re-verified every load-bearing claim against production directly, not trusting
implementation reports. Confirmed: scope containment exact (6 files, 447/-189, nothing else
touched); ga_sade_sati DB matches fixed-code arithmetic exactly (320/5,247/720); ga_vargas
conservation proof exact against untouched sibling charts (13,172+10,270=23,442); ga_structural
genuinely unwritten (4 independent checks, including a live control surface — ganita_structural_get
still verified_fraction=1.0); ga_sensitive genuinely untouched (empty git diff). Tests: 594/594 +
529/529 + 25/25 across all three writers; unrelated 23 pre-existing failures correctly not touched.
**New evidence found**: computed_at timestamps prove UPDATE-only from the outside (all rows share
one build_id, dated 2026-07-26 — no row was re-inserted).

**Monotonicity confirmed two ways, including a control the served-delta agent missed**: sibling
chart `1c826d5a` (never backfilled, same writer version) shows verified_fraction=0.8535 — this
converts the served-delta report's *analytical* ~0.852 reconstruction into an actual live
measurement, closing its weakest link. Second surface (`VERIFICATION_RESCALE` in
bodha_writers/formulas.py): every transition tonight lands at 0.60 or below on a 1.00/0.85/0.60
scale — zero rows moved up on either surface.

**Ruling on "purely more honest, nothing less accurate"**: ga_vargas's serving-invisibility and
ga_sade_sati's dedicated-tool null gap are BOTH ORTHOGONAL to the requirement, not violations —
the clause governs the claim's accuracy, not the pipe's reach. A zero-delta-on-an-unread-column
cannot be a negative delta; an absent claim (null) cannot degrade. Data honesty and serving reach
are independent axes; conflating them would create a perverse "don't fix data until serving exists"
incentive. **Correction found**: ga_vargas's column IS read and served raw by
`register_d9_judgment.ts` (`varga_confirmation.rows`), just never aggregated into a score — cuts
further in favor of the fix, not against it.

**chart_facts CHECK — RECOMMENDED, drafted, NOT applied.** Full 13-value vocabulary (not the
4-value restricted set — copying that would repeat the exact "hand-written set describing a row
shape the DB never had" defect the vocab module's own docstring warns against), `NOT VALID` first
(481MB table, immediate validation would take ACCESS EXCLUSIVE), migration text drafted at
`platform/supabase/migrations/537_chart_facts_verification_pass_status_check.sql` (not created —
text only, for the future session). **Blocked on 4 things**: the 5,428 live `PASS` rows (drain
script's unfinished territory — Stage 1's drain never ran, these are still prohibited-value residue);
tonight's writers being uncommitted (now resolved — committed + PR'd, see below); this warrants its
own migration-guard-reviewed gate, not a 5am append; and it would become an 8th disagreeing
vocabulary copy unless shipped with a parity test against `ALL_STATUSES`.

**Adversarial finding against the GATE R1... wait, R2's own prior scoping ruling**: re-examined the
320 retained `TWO_PASS_VERIFIED` sade_sati rows against `two_pass_verify_cycles()`'s actual logic —
the check is weaker than the earlier ruling credited (a duration-tolerance + near-tautological
ordering check, and the writer's OWN code comment at line 599 documents this exact check FAILING to
catch a real production defect once already). ~140 of the 320 are likely over-tiered (cycle
duration_years is a pure ÷365.25 conversion → should be computed_extension; phase durations are
never examined at all → should be single). **Does not change tonight's verdict** (retaining an
existing claim is a non-demotion, not a new over-claim) but recorded as carried-forward finding G,
not settled.

**VERDICT: PROCEED. Stage 2 as executed is complete and correct.**

**Carried forward, explicitly NOT closed tonight** (in priority order):
- **A. [RESOLVED THIS SESSION]** Work was entirely uncommitted at review time — highest risk found
  (an accidental checkout would have left an honest DB paired with dishonest writers, and the next
  orchestrator rebuild of 482012f1 would have silently re-inflated all 19,459 rows). Committed
  (`2fec4636`), pushed, PR #1045 opened, auto-merge armed.
- B. Deployed sidecar still emits old values until B merges and deploys — sequence must be
  commit→deploy before any CHECK is even considered.
- C. ga_structural backfill (103,372→single+computed_extension, 45→divergent_flagged on cb73cd3d)
  — highest-impact remaining item; ganita_structural_get v3 currently reports grade=ganita_fact/
  verified_fraction=1.0 over rows this ruling found genuinely EMPTY of real verification.
- D. ga_sensitive — deferred, guard-removal needs a native contract-change decision.
- E. chart_facts CHECK, blocked on E1-E4 above.
- F. Stage 1's drain script — still incomplete, 5,428 PASS + 32,054 single_pass still live
  DB-wide; prerequisite for validating any future CHECK.
- G. The 320 retained sade_sati TWO_PASS_VERIFIED rows — ~140 likely still over-tiered, see above.
- H. VERIFICATION_RESCALE (bodha_writers/formulas.py) now silently out of sync — knows 3 of 13
  vocab members, keyed on single_pass which nothing will emit anymore; collapsed to a 2-value
  table. Conservative (no threat to tonight), but drifting, needs a decision not neglect.
- I. registry_bridge.ts:2449 still runs a pre-Ruling-13 `st==='two_pass_verified' || st==='pass'`
  check feeding bodha_signals_get's grounding_score — a second, wider live definition of "verified"
  still exists in served output.
- J. scope_cap (ga_vargas) + the 2 permanently-false sade_sati stub fields — untouched, as ruled.
- K. **Largest gap not in any prior report**: honesty is canonical-chart-only. Charts `1c826d5a`
  and `cb73cd3d` still carry the full unearned tier (13,172 divisional rows each; 4,220/4,200
  sade_sati two_pass rows; 550/560 single_pass) — 2 of 3 charts in the DB still assert the
  over-claim tonight's fix only corrected for the canonical chart.
- L. Audit-trail gap: the literal backfill UPDATE statements aren't preserved in the repo or ledger
  (only the transition matrices are, which GATE R2 verified independently against live state —
  stronger evidence than the script itself, but the mutation can't be replayed/diffed). Record
  statements before ga_structural's backfill runs.
- M. Root-file-policy: M22_NIGHT_LEDGER.md + 2 JSON files not in ROOT_FILE_POLICY §2's list —
  systemic pre-existing pattern, land properly when this work is next touched.
- N. Cosmetic: 2 unused imports in ga_vargas_writer.py, 1 now-dead variable in ga_structural_writer.py.

## Stage 3 — Vimshottari independent verifier BUILT (Executor, this session, `m22-night/stage3-vimshottari-verifier` off `m22-night/stage2-honest-tiers` HEAD)

**Scope discipline**: build + prove-discrimination only, per the brief. **Zero DB writes** —
every DB access in this stage is a `SELECT`; no `psycopg` cursor in the new module ever calls
`.execute()` with anything but `SELECT`. Re-promotion to `two_pass_verified` at scale is
explicitly NOT this stage's act — deferred to a Skeptic pass + independent sample cross-check by
a different agent, per the brief.

**System understood before writing anything** (read `ga_dashas_writer.py`, not assumed):
`chart_dashas` levels 1-4 = Mahadasha/Antardasha/Pratyantardasha/Sukshma (`cd_level_n_max4` CHECK
+ "CRITICAL OVERRIDE 1" header comment confirm this, not the task brief's phrasing alone). 9-lord
cycle/years (Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury
17 = 120y) confirmed against `VIMSHOTTARI_SEQUENCE`/`VIMSHOTTARI_YEARS` — standard, matches.
Year convention confirmed as `365.25` (Julian year, `_years_to_days()`), NOT sidereal/tropical —
this codebase-specific detail was read, not assumed. Nakshatra-lord table cross-checked live
against `reference_nakshatras` (0 mismatches, all 3 charts). **One non-obvious convention found
by reading, not assumed**: the table does NOT store a birth-truncated first Mahadasha — it
backdates to a TRUE (never-truncated) period boundary covering the 1950-01-01..2100-12-31
calculation window and walks forward through whole periods, clipping only the two window edges.
A verifier using the textbook birth-truncated model would have diverged from every stored row for
a reason unrelated to any engine defect.

**Independent verifier**: new file
`platform/python-sidecar/ga_writers/_vimshottari_independent_verifier.py`. Zero import of/call
into `ga_dashas_writer`, `pyjhora_adapter`, or `swisseph` — Moon sidereal longitude is READ from
the `chart_facts` L1 fact (`fact_subject='MOON', fact_category='graha_position',
fact_key='longitude_sidereal'`, written by the DIFFERENT `ga_positions_writer`), birth params read
raw from `public.charts`, and JD↔calendar conversion is a from-scratch Meeus/Fliegel-Van-Flandern
implementation (self-tested at import time against the J2000.0 and Unix epoch reference constants
— fails loudly, not silently, if wrong). The only import shared with the campaign's own vocabulary
is `brahmagyan.verification_vocab.two_pass_verdict` (the sanctioned, ONLY-legal producer of the
`two_pass_verified` string) — fed a boolean this module computes independently (exact lord match
AND both boundaries within tolerance), never a literal.

**Tolerance: 5 seconds**, justified in full in the module's `_TOLERANCE_JUSTIFICATION` docstring:
rounding-boundary noise (both sides independently round JD→timestamp to the nearest second, per
`ga_dashas_writer._jd_to_iso_utc`'s confirmed convention, replicated here) is bounded at ≤1s;
IEEE-754 double-precision accumulation across the deepest recursive chain is bounded at
~10ms worst-case (pessimistic, non-cancelling); 5s carries ~5x margin over (1) and ~500x margin
under the shortest possible level-4 period (~6.57h, the Sun-MD/Sun-AD/Sun-PD/Sun-Sukshma
minimum) — tight enough that a real defect (wrong lord, wrong proportion, dropped period, off-by-
one cycle) produces hours-to-years of discrepancy, not seconds.

**Genuine engine defect discovered doing this** (found via the smoke test, not gone looking for
it): the row-generation loop in `compute_vimshottari` (and every sibling `compute_*` system) drops
a period ENTIRELY — no row emitted, children never computed — whenever its window-clipped start
and end land on the same calendar DATE (`if start_d >= end_d: continue`, all 4 levels,
`ga_dashas_writer.py` lines 1042/1075/1106/1136). Confirmed by reading the source after the first
smoke-test run showed a 132-row level-4-only count mismatch (8297 derived vs 8165 engine on the
canonical chart) that vanished to exact-zero once this rule was replicated in the verifier (see
below) — encoded in `_collapses_to_same_civil_date()` with full citation, not silently patched
around.

**Discrimination proof — 4/4 probes, real code path, `platform/python-sidecar/ga_writers/__tests__/test_vimshottari_independent_verifier.py`, 9/9 passed:**
- (a) adjacent-lord swap on a real computed L1 row → `compare_row()` returns `divergent_flagged`
  (`test_probe_a_wrong_lord_is_flagged_divergent`).
- (b) boundary shifted 3× tolerance (15s) on a real L2 row → `divergent_flagged`
  (`test_probe_b_boundary_beyond_tolerance_is_flagged_divergent`).
- (c) boundary shifted 0.5× tolerance (2.5s) on a real L3 row → `two_pass_verified`, NOT flagged
  (`test_probe_c_boundary_within_tolerance_is_not_flagged`) — proves (b) isn't a verifier that
  always says no.
- (d) `inspect.getsource()`-verified that `verify_chart_vimshottari()` (the function that will run
  against live data) literally contains `compare_row(` — the probes and the live driver are
  provably the same code path, not a parallel test-only reimplementation
  (`test_probe_d_probes_exercise_the_real_verify_chart_code_path`).
All probes construct their "correct" side via `compute_independent_vimshottari_tree()` run against
the canonical native's own live Moon longitude/birth JD, not synthetic fixtures.

**Smoke test (diagnostic, not a re-promotion verdict), canonical chart 482012f1,
lahiri_chitrapaksha (the pipeline default ayanamsha)**:

| Level | engine rows | derived rows | two_pass_verified | divergent_flagged |
|---|---|---|---|---|
| 1 (Mahadasha) | 13 | 13 | 13 | 0 |
| 2 (Antardasha) | 104 | 104 | 104 | 0 |
| 3 (Pratyantardasha) | 923 | 923 | 923 | 0 |
| 4 (Sukshma) | 8,165 | 8,165 | 8,165 | 0 |
| **Total** | **9,205** | **9,205** | **9,205** | **0** |

**Clean 100% agreement** on the canonical chart/default ayanamsha — real evidence these rows have
now earned the tier a real second pass gives them, not proof the tier is safe to write yet (that's
the Skeptic's call). Also run (bonus, beyond the brief's "small sample" ask) against all 3 charts
present in DB × all 5 ayanamshas (15 combinations, own-Moon-longitude derived per chart, no
canonical-chart special-casing in the verifier): `lahiri_chitrapaksha`/`raman`/`true_chitra` are
clean 100% agreement on all 3 charts (9,063–9,993 rows each); `krishnamurti`/
`surya_siddhanta_classical` are **100% divergent on all 3 charts**.

**Second genuine defect discovered (unrelated to the verifier's own correctness, root-caused, NOT
fixed — out of this stage's scope)**: `chart_dashas` rows for `ayanamsha_id IN ('krishnamurti',
'surya_siddhanta_classical')` are byte-identical (same lords, same `start_iso`/`end_iso` to the
second) to the `lahiri_chitrapaksha` rows for the same chart — confirmed via direct SQL, all 3
charts. Root cause found by reading `pyjhora_adapter/_ayanamsha.py`:
`AYANAMSHA_MAP` keys are `{lahiri, true_chitra, kp, raman, surya_siddhanta}`;
`ga_dashas_writer.AYANAMSHAS` values are `{lahiri_chitrapaksha, true_chitra, krishnamurti, raman,
surya_siddhanta_classical}`. `resolve_mode()` does `AYANAMSHA_MAP.get(key,
AYANAMSHA_MAP[DEFAULT_AYANAMSHA])` — `"krishnamurti"` and `"surya_siddhanta_classical"` are not in
the map, so both SILENTLY fall back to Lahiri (`"lahiri_chitrapaksha"` also technically misses the
map's `"lahiri"` key, but coincidentally lands on the same default — the only reason it isn't also
broken). `true_chitra`/`raman` match the map exactly, hence their clean agreement. **This means 2
of the 5 canonical ayanamshas' entire Vimshottari dasha builds, for every chart, have silently
been computed under the wrong sidereal frame since whenever this key mismatch was introduced** —
this stage's independent verifier caught it exactly as designed, on the very first broad run.
**Not fixed tonight**: fixing `pyjhora_adapter/_ayanamsha.py` or `ga_dashas_writer.AYANAMSHAS`
touches the FROZEN-adjacent ayanamsha-resolution path used by every GA writer, not just dashas —
flagged for native/Gate Reviewer triage, not mine to unilaterally patch under a "build the
verifier" task.

**Files this stage added** (no existing file modified):
- `platform/python-sidecar/ga_writers/_vimshottari_independent_verifier.py`
- `platform/python-sidecar/ga_writers/__tests__/test_vimshottari_independent_verifier.py`

**Carried forward, explicitly NOT done tonight**:
- **O.** krishnamurti/surya_siddhanta_classical ayanamsha-key-mismatch defect above — needs a
  fix + full-population impact assessment (every chart, both ayanamshas, all levels) before
  anyone re-promotes or re-builds those two ayanamshas' dasha rows.
- **P.** Re-promotion write-gate itself: this stage proves the verifier discriminates and reports
  a clean canonical-chart/lahiri smoke sample; it does not run against the 1.36M-row population,
  does not write anything, and is not the Skeptic pass the brief requires before any write.
- **Q.** The verifier only covers classical Vimshottari (`system_id='vimshottari'`,
  `kp_sublevel IS NULL`) per the brief's explicit scope — `vimshottari_kp` sub-periods (a
  different derivation per register V-12) and the other 6 dasha systems (yogini, ashtottari,
  chara_karaka, narayana, naisargika, mudda, kalachakra) remain untouched, as scoped.

## GATE R3 (Opus Skeptic, adversarial) — VERDICT: **HALT** (scoped) on re-promotion; **FAIL TO REFUTE** on the verifier's core

Reviewer read `_vimshottari_independent_verifier.py` (808 lines) and `ga_dashas_writer.py`
(`compute_vimshottari` 954-1162, `_find_cycle_start_for_window` 364-427, `_build_row` 850-925,
`_jd_to_iso_utc` 264-283) line by line, ran the test file, and ran an independent adversarial
harness that corrupts the pipeline at the DATA level (the thing the Executor's probes never do).

### What held up under attack — FAIL TO REFUTE

**1. Independence is real, and the constants were NOT copy-imported.** AST audit of every import
(including the four function-local `import psycopg.rows` and one `from zoneinfo`): stdlib +
`psycopg` + `brahmagyan.verification_vocab` only. Textual scan for `ga_dashas_writer` / `pyjhora` /
`swisseph` / `swe` / `birth_params` finds 28+1+3+4+3 occurrences — **every single one inside a
docstring or comment; zero in executable code**. `CLASSICAL_9_LORDS`, `LORD_YEARS`,
`NAKSHATRA_LORDS_27` are module-level literals (the last one *structurally derived* as
`CLASSICAL_9_LORDS[i % 9] for i in range(27)`, not transcribed). Reviewer independently ran
`cross_check_nakshatra_lord_table()` against live `reference_nakshatras`: **0 mismatches**, and
separately confirmed the three constants equal the engine's `VIMSHOTTARI_SEQUENCE` /
`VIMSHOTTARI_YEARS` / `_NAKSHATRA_LORDS_1BASED` — that equality is the *cross-check result*, not
the source. The JD math is a genuinely separate Meeus/Fliegel implementation, self-tested at
import against J2000 and the Unix epoch. **Independence claim: upheld.**
*Scoped blind spot (name it, don't fix it):* three things ARE deliberately copied from the engine —
the 1950-2100 window, the round-to-nearest-second convention, and the same-civil-date collapse
predicate. Copying them is correct (a verifier using textbook conventions would diverge on every
row for non-defect reasons), but it means this verifier **cannot by construction detect a defect in
any of those three conventions**. That must travel with the promotion record.

**2. The 0-divergent smoke result is CREDIBLE, and it is a measurement, not a tautology.**
Reviewer reproduced it and, crucially, recorded the RAW diffs the Executor's report only summarised
as verdicts: **all 18,410 boundary comparisons (9,205 rows × start+end) differ by EXACTLY 0.000
seconds.** Zero lord mismatches. Zero one-second rounding flips. Reviewer then proved the pipeline
is *not* structurally pinned to zero by perturbing its most sensitive input:

| Δ(Moon sidereal longitude) | verified | divergent | max boundary diff |
|---|---|---|---|
| 1e-9° | 9205 | 0 | 1.000 s |
| 1e-7° | 9205 | 0 | 4.000 s |
| **1e-6°** | **0** | **9205** | 38 s |
| 1e-5° | 0 | 9205 | 2,629,422 s |

A 1e-9° Moon shift already moves ~700 boundaries by a rounded second. Observing **zero** flips at
the true Moon value means the two implementations agree to far better than the float-accumulation
bound — consistent with two correct IEEE-754 implementations of the same 365.25 proportional
recursion on a bit-identical Moon input. **Not suspicious. Earned.**

**3. The pipeline discriminates — reviewer proved it where the probes didn't.** Every Executor probe
(a)(b)(c) mutates arguments *at the `compare_row` call site*; none feeds corrupted data through
`verify_chart_vimshottari`. So the probes prove the COMPARATOR discriminates, not the PIPELINE.
Reviewer closed that gap with five data-level attacks through the live comparison path:

| attack | verified | divergent |
|---|---|---|
| engine=canonical vs derived from chart `1c826d5a` | 0 | 9205 (100%) |
| engine=canonical vs derived from chart `cb73cd3d` | 0 | 9205 (100%) |
| lord list rotated by 1 | 1 | 9204 |
| uniform +6 s shift on every boundary | 0 | 9205 |
| drop MIDDLE row of each level | 4601 | 4600 (cascade) |

9/9 tests pass locally (reviewer ran them; the "98/98" was the wider suite). **Discrimination claim:
upheld, and now proved one layer deeper than the Executor proved it.**

**4. The collapse-quirk replication is the RIGHT call.** The verifier replicates the *predicate*
(recompute clipped dates from its OWN JDs, apply `>=`), not the engine's output — so a defect that
shifted a boundary changes the verifier's own drop decision and desynchronises the lists, which the
drop-MIDDLE attack confirms is caught loudly. Masking risk is measure-zero. **But see H3 below for
what it fails to REPORT.**

### What broke — HALT

**H1 — TAIL-TRUNCATION BLIND SPOT. This is the flaw, and it produces exactly the report's headline
number.** `verify_chart_vimshottari` pairs engine and derived rows POSITIONALLY. If the engine holds
fewer rows than derived and the missing ones are at the TAIL, every surviving engine row still
matches its counterpart and the surplus derived rows are **never examined at all**. Reviewer's
attack — drop the last row of each level:

```
drop TAIL row per level      verified=9201  divergent=0  levels_with_count_mismatch=4
```

**Zero divergent. The exact metric the Stage 3 report leads with.** The only signal is
`LevelSummary.count_mismatch`, which (a) is not folded into `total_divergent`, (b) has no aggregate
property on `ChartVerificationResult`, and (c) is asserted only inside the pytest smoke test — the
library API a promotion driver would call has no guard. A driver written against the natural
contract `result.total_divergent == 0` would promote a truncated chart wholesale. Tail truncation is
not hypothetical for this engine: `compute_vimshottari` has two `break`-on-`md_jd >= max_jd` exits
(1156-1160) and a `for cycle in range(5)` cap, all at the window's far edge. **This is the same
shape as the bug this campaign exists to kill — a check that looks rigorous and reports clean
against a real defect class.** MUST be closed before any write: `ChartVerificationResult` needs a
`total_count_mismatch` that a gate cannot ignore, and surplus derived rows must be counted as
divergent, not dropped.

**H2 — COLUMN-LEVEL BROADCAST.** `fetch_engine_rows` selects **3 of `chart_dashas`' 42 columns**
(`lord_graha, start_iso, end_iso`). Re-promotion writes `verification_pass_status='two_pass_verified'`
— a ROW-level claim, and per `envelope.ts` the only status serve counts as grounding — onto rows
whose `start_date`, `end_date`, `duration_days`, `sandhi_flag`, `parent_row_id`,
`is_truncated_at_window_start/end`, `lord_natal_*`, `next_dasha_start_iso`,
`convergence_count_at_start` received no second pass at all. This is M-22's own broadcast pattern
rotated 90°: instead of broadcasting a level-1 verdict across levels 2-4, it broadcasts a 3-column
verdict across 42 columns. `duration_days` is derived from the DATE-truncated columns and is
therefore a genuinely independent value the verifier could check for free. Either extend coverage to
the cheap deterministic columns (start_date/end_date/duration_days/parent lineage) **or** the
promotion must be recorded as explicitly column-scoped, not row-scoped.

**H3 — THE REPLICATED QUIRK'S COST IS ABSORBED, NOT REPORTED.** Reviewer measured it by
neutralising `_collapses_to_same_civil_date` and re-running the tree: the engine silently never
persists **132 / 188 / 142 level-4 Sukshma periods** (charts 482012f1 / 1c826d5a / cb73cd3d,
lahiri) — **1.41% / 1.85% / 1.53% of each chart's entire Vimshottari tree**. The verifier absorbs
this into "100% agreement" and emits no counter. A promotion run would stamp `two_pass_verified` on
a table that is provably ~1.5% incomplete at level 4 with nothing in the result object saying so.
REQUIRED: `ChartVerificationResult` must carry `collapse_dropped_periods_per_level` so the
incompleteness travels with the verdict.

**H4 — SCOPE ARITHMETIC.** This verifier covers `system_id='vimshottari' AND kp_sublevel IS NULL` =
**141,731 rows of 1,461,165 (9.7%)**. It cannot "re-promote ~1.36M rows"; any language to that
effect must be corrected before the gate.

### Tolerance — the number survives, the justification does not

Reviewer redid the arithmetic independently. At JD ~2.45e6, 1 ulp = 4.66e-10 d = **4.0e-5 s**;
~200 chained ops → **~8 ms**. The Executor's ~9.6 ms bound is right. The 5 s choice is defensible on
the "too tight" axis (500× the pessimistic bound; no legitimate false positives) and survives the
"too loose" astrological test (5 s is 0.021% of the 6.574 h minimum Sukshma; no wrong-lord,
wrong-proportion, wrong-DAYS_PER_YEAR or off-by-one-cycle defect lands in the 0-5 s band).
**But three things in the written justification are wrong and it is the gate's document of record:**

- **Factual inversion.** "*still ~20x below even the pessimistic 9.6ms worst-case bound*" — 5 s is
  ~520× **ABOVE** 9.6 ms. The comparison is backwards.
- **Arithmetic slip.** Minimum Sukshma = 6·0.05³ y = 0.00075 y = **23,668 s (6.574 h)**, not
  "~23,652 seconds"; the intermediate "`= 0.99e-1...`" is garbled.
- **The dominant sensitivity is missing entirely.** The justification analyses only rounding noise
  and float accumulation. It never mentions the **Moon-longitude input**, which the table above shows
  is the load-bearing term: 5 s of tolerance implicitly requires the verifier's Moon (read from
  `chart_facts`, written by `ga_positions_writer`) to agree with the engine's Moon (recomputed via
  `pyjhora_adapter`) to **~1.3e-7°**. It does — both trace to the same Swiss-Ephemeris call — but
  that is an UNSTATED load-bearing assumption. Any future divergence in those two Moon paths turns
  this verifier into a 100%-divergent false-alarm generator. (It already has: see the ayanamsha
  defect below, where the 100%-divergent verdict is *correct*.)

**Recommendation (not a HALT condition):** the observed noise floor is **0.000 s**, so 5 s is
~250,000× the measured noise. A uniform +3 s engine bias passes 9205/9205 with zero divergences
(reviewer confirmed). Tighten to 1 s and additionally report max/mean diff per level, so a
systematic sub-tolerance bias is *visible* rather than absorbed. Relatedly, probe (c)'s 2.5 s
"legitimate noise" scenario never occurs in reality — it asserts the comparator's `<=` works, not
that false positives are a real risk.

### Doctrine nit

`compare_row` calls `two_pass_verdict(all_agree, True)` — a pre-decided boolean against a literal.
`verification_vocab.two_pass_verdict`'s own docstring: *"Callers must present BOTH the engine value
and an INDEPENDENTLY derived value; the comparison happens here, so the verdict cannot be asserted
without evidence."* Here the comparison happens at the call site and the sanctioned producer is
handed a decision — functionally correct (the boolean IS independently computed) but at the call
site indistinguishable from `two_pass_verdict(True, True)`, which defeats the guardrail. Should pass
the compared tuples.

### The ayanamsha defect — INDEPENDENTLY CONFIRMED, and materially WORSE than reported

Reviewer confirmed by md5 signature over `(level_n, lord_graha, start_iso, end_iso, start_date,
end_date)` — not by trusting the Executor: `krishnamurti` ≡ `surya_siddhanta_classical` ≡
`lahiri_chitrapaksha` for Vimshottari on **all 3 charts** (identical hashes, identical counts).
Root cause re-read and confirmed at `pyjhora_adapter/_ayanamsha.py`: `AYANAMSHA_MAP` keys are
`{lahiri, true_chitra, kp, raman, surya_siddhanta}`; `resolve_mode` does
`.get(key, AYANAMSHA_MAP[DEFAULT_AYANAMSHA])`. Three of five canonical ids miss the map —
`lahiri_chitrapaksha` lands on Lahiri by luck, `krishnamurti` and `surya_siddhanta_classical` land
on Lahiri **wrongly**. Beyond the Executor's report:

- **Not confined to Vimshottari.** Distinct signatures per chart across the 5 ayanamshas:
  `vimshottari` 3, `vimshottari_kp` 3, `kalachakra` 3, `mudda` 3 — the 3 being
  {lahiri≡kp≡surya}, raman, true_chitra: the exact fallback fingerprint.
  **584,607 of 1,461,165 `chart_dashas` rows (40.0%)** carry a `krishnamurti` /
  `surya_siddhanta_classical` label.
- **Blast radius is NOT universal — reviewer tested rather than assumed.** `chart_divisionals` shows
  6 distinct signatures per chart (5 real + INVARIANT) with krishnamurti/surya/lahiri all
  **different**; `chart_facts` `graha_position` shows 5 distinct per chart. `ga_positions_writer`
  carries its own correct `CANONICAL_AYANAMSHAS` translation map (line 45) — which is *why*
  `chart_facts` is right. The defect is confined to call sites passing the CANONICAL id raw into
  `resolve_mode`; `ga_dashas_writer._get_moon_position` (line 314) is the confirmed one.
  `ga_vargas_writer` (769, 2724) also calls `resolve_mode` and should be re-checked despite its
  output table looking clean.
- **It is a genuine intra-L1 contradiction under CLAUDE.md §N.5.** For chart 482012f1 /
  `surya_siddhanta_classical`, `chart_facts` says Moon = **330.017263°** while the entire
  `chart_dashas` tree for that same (chart, ayanamsha) was built from **327.055230°** — a 2.96°
  difference, ≈3.5 YEARS of Mahadasha balance. L1's own two writers disagree about the same fact.
- **SEPARATE, POSSIBLY WORSE DEFECT surfaced by the same query — flagged, not investigated.**
  `ashtottari`, `naisargika` and `yogini` show only **ONE** distinct signature per chart: all five
  ayanamshas byte-identical, *including* raman and true_chitra which resolve correctly. For
  `naisargika` that is expected (age-based, chart-independent per its own docstring). For `yogini`
  and `ashtottari` — both Moon-nakshatra-driven, both taking `moon_sid` as their first parameter —
  it is not, and points at a second, independent defect. `chara_karaka` / `narayana` show 2/2/1.
- **IS IT SERVED? YES — currently, by default.** `get_dashas.ts` issues
  `SELECT * FROM chart_dashas WHERE chart_id = $1` and applies **no ayanamsha filter unless the
  caller supplies one** (its own header: *"ayanamsha_id is NOT defaulted server-side... omitting it
  returns one row per ayanamsha (5 rows)"*). So the default response hands a caller five
  ayanamsha-labelled dasha answers of which **three are the same numbers wearing different labels**.
  `ganita_kp_cusps_get` documents `krishnamurti` as its DEFAULT ayanamsha, establishing krishnamurti
  as a first-class user-facing choice. **Severity: HIGH, live, not a footnote.**

### RULING

**HALT on re-promotion / any write.** Three specific, closable flaws gate it: **H1** (tail-truncation
blind spot — reproduces the report's own "0 divergent" headline against a real defect class), **H2**
(3-of-42-column verdict broadcast to the row), **H3** (the ~1.5% collapse-dropped Sukshma periods are
absorbed into "100% agreement" and never counted). Plus **H4**: the covered scope is 141,731 rows
(9.7%), not 1.36M.

**FAIL TO REFUTE on the verifier's core.** Independence, the tolerance's adequacy, the discrimination
claim and the 0-divergent measurement all survived every attack constructed against them — including
five data-level corruptions the Executor's probes never ran. This is a real second pass, not another
check that doesn't bite. Reviewer tried to break it on independence (AST + textual scan), on input
sensitivity (7-point Moon perturbation sweep), on cross-subject confusion (2 charts), on systematic
bias (3 uniform shifts), on ordering (lord rotation), and on row-set integrity (mid + tail drops).
Only the tail drop got through.

**Authorized to proceed WITHOUT any write:** the sample cross-check and the full **read-only** run
are authorized and encouraged — the instrument is trustworthy as a *diagnostic*, and the ayanamsha
finding is evidence it earns its keep on first contact with real data. **No `UPDATE` to
`verification_pass_status` is authorized until H1-H3 are closed and independently re-reviewed.**

**Escalated to native / morning report as its own item, not a byproduct:** the `resolve_mode` key
mismatch is a live, currently-served L1 correctness defect affecting 40% of `chart_dashas` and
contradicting `chart_facts` for the same (chart, ayanamsha). It outranks the Stage 3 verifier work
in importance. Do not fix it inside this autonomous run — same-night patch-and-run on a path every
GA writer touches is exactly the shape this campaign exists to stop.

## Stage 3 — H1/H2/H3 remediation (Executor, this session, same branch, no writes)

Scope: close the three specific, closable flaws GATE R3 gated on. Ayanamsha `resolve_mode` defect
(escalated separately to native) explicitly OUT of scope — not touched, not `pyjhora_adapter`, not
any production writer. Read-only against the live DB throughout; zero `UPDATE`/`INSERT` issued.

**H1 — tail-truncation blind spot — FIXED.** The per-level pairing loop was rewritten as a standalone,
DB-free function `compare_level()` (which `verify_chart_vimshottari()` now calls per level) that
walks `range(max(len(engine_rows), len(derived_rows)))` **symmetrically** instead of only iterating
`engine_rows`. A leftover row on EITHER side — engine longer than derived, or derived longer than
engine — is now a hard divergence: `LevelSummary.divergent_flagged` is incremented and a new
`count_mismatch_divergences` field tracks the subset caused purely by the mismatch (already included
in `divergent_flagged`/`total_divergent`, not layered on top). `count_mismatch` is no longer a
side-channel-only pytest assertion — it drives the primary verdict path directly.
Reproduced the Skeptic's exact attack as a permanent regression test
(`test_h1_row_count_mismatch_surfaces_as_divergence_in_main_verdict_path`): build a perfect-agreement
synthetic engine-row set from the real independently-computed level-1 tree, drop the last row, feed
both through `compare_level()` — now `count_mismatch=True` and `divergent_flagged>=1`, where before
the fix an equivalent scenario reported `divergent=0`. A second test
(`test_h1_row_count_mismatch_also_fires_when_derived_side_is_longer`) covers the OPPOSITE direction
(DB has fewer rows than the independent computation), which the old code's engine-only loop could
never have detected even in principle.

**H2 — column coverage — FIXED, 20 of 42 (up from 3).** Read the live `chart_dashas` schema (`\d
chart_dashas`, confirmed 42 columns) and `ga_dashas_writer.py`'s row-construction code
(`_build_row`, `_get_karakas_active`, `_planet_relationship`, `compute_sandhi_post_pass`, the 4
`compute_vimshottari` `_build_row()` call sites) to classify every column into one of three honest,
disjoint buckets — asserted to sum to 42 by a module-import-time self-test
(`_self_test_column_coverage_partition`), same discipline as the existing `_self_test_jd_roundtrip`:
- **`INDEPENDENTLY_VERIFIED_COLUMNS` (20)** — `lord_graha`/`start_iso`/`end_iso` (pre-existing) plus
  17 new: `start_date`/`end_date` (floor-JD civil date, NOT the rounded datetime's `.date()` — those
  can differ by a day near a midnight rounding boundary, per `ga_dashas_writer._jd_to_iso_utc`'s own
  V-9 comment), `duration_days` (`(end_date - start_date).days`), `sandhi_flag`
  (`duration_days < 20`, confirmed formula), `karaka_role_at_period` + `karakas_active_during_period`
  (transcribed `_JAIMINI_KARAKAS` table, function of lord/parent_lord), `lord_to_parent_relationship`
  (transcribed `_FRIEND`/`_ENEMY` tables), `applies_to_this_chart_flag` /
  `period_deity_or_marker` / `varsha_year_lord` / `anchored_solar_return_iso` / `kp_sub_lord` /
  `kp_sub_sub_lord` (all constant for classical Vimshottari — confirmed by reading every
  `_build_row()` call site in `compute_vimshottari`, none pass these kwargs),
  `sandhi_with_next_dasha_lord` / `next_dasha_start_iso` (level_n==1 only, derived from this
  module's own next-sibling lookup), `is_truncated_at_window_start/end` (already computed by this
  module — see quirk below).
- **`QUERY_GUARANTEED_COLUMNS` (5)** — `chart_id`, `ayanamsha_id`, `system_id`, `level_n`,
  `kp_sublevel`: tautologically correct by `fetch_engine_rows()`'s own WHERE clause; checking them
  would be circular, so they're reported separately, NOT counted as independently verified.
- **`NOT_INDEPENDENTLY_CHECKABLE_COLUMNS` (17, each with a documented reason)** — `dasha_row_id`,
  `build_id`, `parent_row_id` (provenance/identity, arbitrary); `lord_sign`, `lord_natal_house_d1`,
  `lord_natal_sign`, `lord_natal_nakshatra`, `lord_natal_dignity_d1`, `lord_natal_shadbala_total`
  (require the dasha LORD's own natal placement/dignity/shadbala — an entirely separate,
  substantial computation domain this module deliberately does not touch); `verification_pass_status`,
  `verification_method`, `citation_ref`, `citation_human`, `computed_at`, `engine_version`
  (provenance/metadata, or circular); `concurrent_system_lords_jsonb`, `convergence_count_at_start`
  (require computing OTHER dasha systems — out of Vimshottari-only scope).
`ChartVerificationResult.column_coverage_report()` returns the honest "N of 42" breakdown plus
per-column agree/mismatch counts — no caller can infer full-row verification from the fact that the
function merely ran.
**Confirmed engine quirk found while doing this (replicated, not corrected, same discipline as H3):**
`is_truncated_at_window_start/end` is only ever wired at level_n 1-2 in `compute_vimshottari` — the
level_n 3 (PD) and 4 (Sukshma) `_build_row()` calls never pass `is_trunc_start`/`is_trunc_end` at
all, so those columns silently default to `False` for every PD/Sukshma row regardless of true
clipping state. `derive_extended_columns()` expects `False` at levels 3-4 rather than flagging a
false divergence. Also preserved verbatim: `_ENEMY['Moon'] = {'None'}` (the STRING `'None'`, not the
object) — an apparent engine typo meaning Moon-lord rows can never be classified `'enemy'`, only
`'friend'`/`'neutral'`; replicated rather than "fixed" per the same rationale. Neither is flagged as
a HALT-worthy defect here — both are disclosed, out-of-scope observations for the native, same
treatment as the ayanamsha finding.

**H3 — silent quirk absorption — FIXED.** `compute_independent_vimshottari_tree()` now returns an
`IndependentTreeResult` (`rows` + `excluded_by_level: dict[int, int]`, incremented at each of the 4
`_collapses_to_same_civil_date` sites) instead of a bare list. `LevelSummary`/
`ChartVerificationResult` carry `excluded_known_quirk` as a THIRD, explicitly-reported bucket
alongside `two_pass_verified`/`divergent_flagged` — the tri-state (verified / divergent /
excluded-known-quirk) is now visible, not folded into "verified". On the canonical chart,
`excluded_by_level[4] == 132` — an EXACT match to one of the Reviewer's three independently-measured
numbers (132/188/142 across the 3 test charts), which is strong evidence the H3 implementation itself
is correct, not just present.

**Test suite: 18/18 pass (17 new + 1 pre-existing smoke test), full `ga_writers/__tests__/` suite:
107/107 pass, zero regressions.** New tests: `test_h1_row_count_mismatch_surfaces_as_divergence_in_main_verdict_path`,
`test_h1_row_count_mismatch_also_fires_when_derived_side_is_longer`,
`test_h2_column_coverage_partitions_all_42_columns_honestly`,
`test_h2_karaka_role_and_relationship_match_transcribed_classical_tables`,
`test_h2_extended_column_mismatch_is_flagged_divergent`,
`test_h2_compare_row_backward_compatible_without_extended_args`,
`test_h3_collapsed_periods_are_tracked_as_a_distinct_excluded_count`,
`test_h3_excluded_count_surfaces_separately_not_folded_into_verified`,
`test_h3_chart_verification_result_reports_total_excluded_known_quirk`. `test_probe_d`'s code-path
assertion was updated (not weakened) to reflect the H1 extraction:
`verify_chart_vimshottari -> compare_level -> compare_row` is now a two-hop chain, both hops asserted
by source-grep. `compare_row()`'s original 6-positional-arg contract is untouched — the 4 pre-existing
discrimination probes (probes a-d) pass unmodified, and a new test
(`test_h2_compare_row_backward_compatible_without_extended_args`) pins that contract explicitly.

**Re-run smoke test, canonical chart, `lahiri_chitrapaksha`, post-fix, full honest breakdown:**

```
level 1: engine=13   derived=13   verified=13   divergent=0  excluded_known_quirk=0
level 2: engine=104  derived=104  verified=104  divergent=0  excluded_known_quirk=0
level 3: engine=923  derived=923  verified=923  divergent=0  excluded_known_quirk=0
level 4: engine=8165 derived=8165 verified=8165 divergent=0  excluded_known_quirk=132
TOTALS:  examined=9205 verified=9205 divergent=0 (count_mismatch_divergences=0) excluded_known_quirk=132
```

20 of 42 `chart_dashas` columns independently verified (up from 3), zero mismatches on any of them
(`per_column_mismatch_count == {}`), zero row-count-mismatch divergences, 132 known-quirk exclusions
at level 4 disclosed rather than absorbed. **The result did not change the module's underlying
soundness assessment — full agreement holds, now measured honestly across 6.7x more columns with the
tail-truncation blind spot closed and the quirk's cost disclosed.** No reason to stop and report a
change of understanding; proceeding to hand off for re-review.

**Not done (explicitly out of scope per task brief):** ayanamsha `AYANAMSHA_MAP` defect untouched;
`pyjhora_adapter` and all production writers untouched; no DB write of any kind issued; no
re-promotion decision made — this remains gated on independent re-review of H1-H3 before any
`UPDATE` to `verification_pass_status` is authorized.

Files changed: `platform/python-sidecar/ga_writers/_vimshottari_independent_verifier.py`,
`platform/python-sidecar/ga_writers/__tests__/test_vimshottari_independent_verifier.py`. Committed
on `m22-night/stage3-vimshottari-verifier`.

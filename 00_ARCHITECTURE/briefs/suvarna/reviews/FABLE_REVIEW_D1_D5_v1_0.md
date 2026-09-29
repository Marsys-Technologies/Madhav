# Suvarṇa — delegated review of decisions D1–D5

Reviewer: Fable (delegated, per plan §6.2). Read-only; nothing modified. 2026-09-29.

Read: plan v1.2, charter v1.2, execution architecture v1.2, runbook, ROLE_CONDUCTOR, ROLE_BUILD_OPERATOR,
EXEC start prompt, L3 focus families v1.1, plan_model.json, DECISIONS.jsonl, D6 reader runbook v1.2,
REVIEW_PASS1_SUBSTANCE / CONSISTENCY, `asset_census.py` CRITERION_REGISTRY, CLAUDE.md §N.2–§N.8.
Checked against the live system, not only the documents: the cockpit run route and auth brain, the Cloud Run
job invoker, `deploy.yml`, `staleness.py`, the tracker detectors and Monitor, and read-only queries on
production through the campaign's own `pgenv.sh` path (no credential opened or printed).

| # | Verdict |
|---|---|
| D1 | **Accept with changes** — right shape; three of its facts are wrong; as written it is not implementable under least privilege |
| D2 | **Accept with changes** — certification mechanism right; the wave rule is the wrong grain and would stall B.W0/G2; R8 collides with the orchestrator's own staleness propagation |
| D3 | **Accept with changes** — build the generic detectors and rollup; N/A by declared per-layer rule, not by reviewers; wire three existing CI guards; 40–80 h covers generic work only |
| D4 | **Accept with changes** — dump + diff; impact statement measured not asserted; "revert and rebuild" is not an L0 undo |
| D5 | **Reject as proposed** — `/loop` is documented as session-scoped with a 7-day expiry; accept only as a bounded interim to G2, with a supervised headless runner as the durable runtime |

Cross-cutting: D1 presupposes D6 (`suvarna_reader`) is applied first — today's "read-only" credential is
`amjis_app` (measured: write privilege on 336 of 410 public tables; read-only only through a client-set
GUC). D2 and D3 both change the same detector pair (`elevated_assets` / `levels_elevated`); do them as one
change. D2 and D4 both depend on one verification of `staleness.py`'s behaviour on a global (chart_id NULL)
run; do it once in E5.3.

---

## D1 · A build identity for the agents

**Finding it answers:** SUBSTANCE #1 (BLOCKER: no way to dispatch a build or read `env.DEPLOY_SHA`);
touches #12 (deploy latency check) and #16 (credential not verified read-only).

**Verdict: accept with changes.**

### What is wrong in the proposal as stated

1. **The route.** `/api/build/start` is decommissioned (`platform/src/app/api/build/start/route.ts`: 410,
   "Use POST /api/cockpit/runs"). The live route is `platform/src/app/api/cockpit/runs/route.ts`. It
   authenticates by Firebase session cookie only (`getServerUser`, `platform/src/lib/firebase/server.ts:46–51`;
   the cookie is minted by `POST /api/auth/session` from an ID token, and only for `profiles.status='active'`).
2. **"Write permission on chart 482012f1 only" cannot be granted today.** Write = `permission === 'all'` =
   chart owner or `super_admin` (`authorizeChartAccess.ts` rules 1–2). `chart_grants.permission` is
   constrained `CHECK (permission = 'view')` (live constraint; migration 001 baseline l.199), and
   `profiles.role` to `guest | super_admin` (live; one super_admin exists). So the only identities that can
   dispatch are the native (owner) or a super_admin. A super_admin identity can build **and clear** every
   chart (7 charts exist) and use every admin route — far wider than need.
3. **The global L0 build is super_admin-only** (runs route l.108–128: non-super_admin gets 403 on
   `layer=brahmagyan`, and global assets are silently excluded from any other plan). "Plus the global L0
   build only" is therefore not expressible without either super_admin or a code change.
4. **"Nothing exposes the deployed SHA" is false, and the proposed fix reads the wrong artifact.**
   `NIRMANA_DEPLOYED_SHA=${DEPLOY_SHA}` is in the web service env (`deploy.yml:1351`) and is returned as
   `deployed_sha` by `/api/mcp/inquiry/readiness` (MCP-key auth) and as `deployed_revision` by
   `/api/mcp/inquiry`. But writers do not run in the web service: they run in the Cloud Run Job
   `brahma-build-pipeline-job`, whose image is re-pointed to `brahma-pipeline:${DEPLOY_SHA}` on every deploy
   (`deploy.yml:2132–2135`), readable by `getJobImageTag()` (`platform/src/lib/cloud_run/jobs.ts:28`) and
   already returned as `job_image_tag` in the runs route's 201 body. Precondition 4 must check the **job image
   tag** for writer changes and the web SHA for serving changes. Putting the SHA on unauthenticated
   `/api/health` also publishes the exact commit to the internet for no reason.
5. **The credential it copies is not what it thinks.** The "read-only credential" resolves to `amjis_app`
   with `default_transaction_read_only=on` set client-side — any session can `SET … off`. D6
   (`D6_SUVARNA_READER_RUNBOOK_v1_0.md` v1.2, draft, not run; Monitor `check_credential_readonly` expects
   login `suvarna_reader`, which does not exist yet) fixes this. D1 must not be provisioned on the pre-D6
   pattern.

### Exact changes

**(a) Identity type: a dedicated service user, not a user account of the native's and not super_admin.**
One Firebase account (`suvarna-builder@…`) with its own `profiles` row (role `guest`, status `active`).
Why a service identity: `build_runs.triggered_by` then distinguishes every Suvarṇa run from the native's;
it is revocable without touching the native's access; it can never carry the native's rights by accident.

**(b) Scope: a dispatch-only grant, by a small change to the one authorization brain** (a normal PR +
migration, security-reviewed, merged and deployed before Track B — the proposal silently assumes this
exists):
- migration: widen `chart_grants.permission` CHECK to `('view','build')`; insert one row
  `(482012f1…, <builder uid>, 'build')`;
- `authorizeChartAccess`: rule 3 returns `'build'` for a build grant; `requireChartPermission`: new access
  level `'build'`, satisfied by `'all'` or `'build'`;
- `POST /api/cockpit/runs`: use `access: 'build'` for dispatch; refuse `clear_before: true` unless the
  permission is `'all'`. Every other write route (clear, delete, edit, rebuild-all) keeps `'all'`.
- Result: the builder can create non-clearing `build_runs` for exactly one chart, through every existing gate
  (RUN_ACTIVE, UPSTREAM_BLOCKED, PRECONDITION_FAILED, protected assets), and nothing else.
- Tests the PR must carry: a `'build'` grantee gets 403 on `clear_before`, on the clear routes, on
  `layer=brahmagyan`, and on any other chart.

**(c) The global L0 build: do not give the builder super_admin.** Recommend: L0 waves are dispatched **by
the native** (super_admin) from the cockpit at the Build operator's parked request, with the swarm supplying
PRECHECK.md, the snapshot and the impact statement (D4). D4 already makes every L0 wave a native-attended
event, and there are few of them (L0 sits in levels 0–2: 24 + 11 + 4 of 40 assets, measured). Charter G13-A
stays as the *authority*; the *mechanism* is native-clicked. If the native later wants unattended L0 waves,
add a `global_build` grant kind by a separate decision — never `super_admin`.

**(d) How agents dispatch without reading the secret.** One script, `~/.config/suvarna/bin/suvarna-build`
(mode 700), sources `~/.config/suvarna/builder.env` (mode 600; the builder's refresh token or
email + password + web API key), exchanges it for an ID token (Identity Toolkit), obtains `__session` from
`POST /api/auth/session`, calls `POST /api/cockpit/runs` with `clear_before:false`, and prints **only**
`{run_id, plan, asset_count, job_image_tag}`. `--preflight` prints `{job_image_tag, deployed_sha}` without
dispatching. E5.3 calls the script; agents never open the file (P1's "approved tooling" rule). The Monitor
gets `check_builder_scope` (same shape as `check_credential_readonly`): through the reader credential, assert
the builder uid's `profiles.role='guest'`, `status='active'`, and its `chart_grants` rows are exactly
`{(482012f1,'build')}`; BLOCK otherwise. That makes the scope claim an earned signal (§N.8).

**(e) The deployed-SHA read path.** Not `/api/health`. One small authenticated GET (e.g.
`GET /api/cockpit/runs/preflight`) returning `{job_image_tag, deployed_sha}` — both values are already
computed in-process (`getJobImageTag()`, `process.env.NIRMANA_DEPLOYED_SHA`). Precondition 4 then reads:
writer change → `job_image_tag` ends with the merged SHA; serving change → `deployed_sha` equals it. (The job
env carries no SHA variable; the image tag *is* the SHA.)

**(f) Rotation and revocation.** Revoke, in order of speed: delete the `chart_grants` row (next request is
403; no deploy) → set `profiles.status='disabled'` (no new sessions) → Firebase revoke refresh tokens /
disable the user (`verifySessionCookie(cookie, true)` checks revocation, so live cookies die too). Rotate:
the native regenerates the password/refresh token and rewrites `builder.env`; agents never do (extend R10 to
"the read-only **or builder** credential"). Session cookies expire on the app's `SESSION_DURATION_MS`; the
script re-mints per call, so nothing long-lived is cached outside the 600 file.

**(g) Charter and plan text.** G13: name the builder identity as the one permitted non-read credential, and
say L0 waves are native-dispatched at the swarm's request. R10: add the builder credential. P2 unchanged
(the builder is not a privileged role). Plan §4.2 J1 row: add "builder identity provisioned; Monitor scope
check green; E5.3 tested against it; D6 reader applied". Timing "before Track B waves, not before N-1" is
right, with that J1 wording.

### Residual risks

- The auth change touches the authorization brain: `security-reviewer` before merge; the tests in (b) are
  the detector that the grant stays dispatch-only.
- A compromised Mac exposes `builder.env`: the attacker can trigger non-clearing builds on one chart and
  nothing else — bounded, and revocable in one row.
- L0 waves need the native present. Accepted trade; it is also what D4 asks for.
- Precondition 4 stays "necessary, not sufficient" while families/Pūrṇa/Jātaka also deploy to `main`
  (finding #12): the pre-wave writer-file hash check the finding asks for still belongs in E5.3.

---

## D2 · Certifying the L3 family assets (Gochara, Saṅgam, Kṣetra)

**Finding it answers:** SUBSTANCE #4 (BLOCKER); touches #10 (L2⇄Saṅgam deadlock), #13 (stale
certifications), CONSISTENCY #27 (B-waves vs family assets).

**Verdict: accept with changes.**

### What holds and what does not

- **Holds:** "the family's own orchestrator rebuild counts as the Build exercise; Suvarṇa's independent
  re-measure writes the certification." The Build gate is about the orchestrator dispatching and a rebuild
  producing the right result; who pressed the button is irrelevant. The census reads `build_runs` /
  `build_run_assets` read-only; a certification record is Suvarṇa's ledger, not family build state, so R8
  is not breached.
- **Does not hold — the wave rule is the wrong grain.** Measured on the live registry (recursive levels over
  `asset_registry.depends_on`, 2026-09-29): `ka_gochara_resonance` and `ka_vedha_gochara` sit at **level 1**
  (inside B.W0's levels 0–2); `ka_gochara` at 5 (B.W1); `ka_kshetra` 12, `ka_sangam` 13, and their L5 readers
  `mi_bhara`, `mi_sankalpa` at 13 (B.W3). `levels_elevated` (`detectors.py:317–325`) counts every asset in a
  level. "Waves that read a family asset wait for it" therefore means: B.W0 cannot complete, G2 cannot be
  ruled, and the entire Track B chain waits on the Gochara family session, which the native has on hold.
  Sixteen assets read a family asset (readers below).
- **Does not hold — R8 collides with the orchestrator.** `staleness.py:120–152` flips downstream
  `asset_throughput.state` to `'stale'` on the same chart whenever an upstream asset's output changed. A
  Suvarṇa L1 wave with a real delta (e.g. `ga_positions`) will mark `ka_vedha_gochara`, `ka_gochara`,
  `ka_sangam` stale. R8 as worded reserves any Suvarṇa rebuild "that marks a family asset blocked" — read
  literally, every L1 wave with a delta becomes a native decision.
- **Wrong owner:** "if closed, Strategic Suvarṇa reopens it." Strategic never executes; reopening a family
  session is a native act (N-17 created them).

Readers of family assets (measured): `ka_gochara` (of resonance/vedha), `ka_kshetra`, `ka_sangam`,
`mi_bhara`, `mi_sankalpa`, `ka_kalasutra`, `ka_taranga`, `ka_vighnakara`, `ka_kala_darshana`,
`ka_bhavishya_lekha`, `ka_jivana_parva`, `ka_tulana`, `ph_nimitta`, `ph_muhurta`, `ph_pratikara`,
`mi_adhilepa`.

### Exact changes

1. **Grain.** Family assets are **excluded from every wave's completion predicate**; the R8 family set lives in
   one versioned file (`FAMILY_ASSETS.json`, frozen at J1) that `levels_elevated` and the census read.
   **Readers** carry an asset-level dependency "its family input certified": they are rebuilt only after it,
   and a wave completes without them, showing them as `waiting_on_family` in the tracker (never silently
   dropped). Add plan_model items `F3.G/S/K-certified` (detector: `asset_certs.jsonl` rows for the family
   set) as dependencies of the waves that hold the readers (B.W1 for `ka_gochara`'s dependants, B.W3+ for the
   rest).
2. **Build gate for a family asset:** PASS only on an orchestrator run on the canonical chart (any
   `triggered_by`) whose substep plan completed (§N.8). Hand-run cutover scripts (Gochara today: "no normal
   build path", focus-families §1.3.2) do not count. This is what the family sessions must deliver before
   their assets can be certified; say so in their prompts.
3. **R8 wording:** exclude "state changes made by the orchestrator's own staleness propagation as a
   consequence of a granted upstream Suvarṇa rebuild". Those are recorded in the wave evidence and reported to
   the family session, which rebuilds. What stays reserved: direct changes to family code, data, registry
   rows, leases; and cascade deletes into family data.
4. **The cascade:** an L2 MSR wave cascade-deletes `kala_convergence` (Saṅgam) through the FK — that is R8
   and R1 both. Keep "no L2 MSR rebuild until F-3", require F-3 recorded `decided` in DECISIONS.jsonl (not
   the current `delegated` line; finding #9), and steer F-3 toward an FK change that removes the cascade —
   a sequencing rule means every later L2 rebuild forces a Saṅgam rebuild forever.
5. **Hand-back rule instead of "reopen":** when a family session closes, the native records a decision
   transferring that family's assets out of the R8 set (lease to Suvarṇa; the family's rebuild runbook
   attached). From then on they are ordinary Suvarṇa assets under G13 and §5.4 step 7 has an owner. Until
   that decision, a needed rebuild is parked with lead time by the Steward.
6. **Currency:** every certification record (family and otherwise) carries what it was measured against —
   the run's job image tag, upstream certification ids, the row-set fingerprint — so a later family change
   invalidates it (finding #13). No new cost: the E5.1 writer records what the census already sees.
7. **Say what the critical path now contains:** Kṣetra (5–9 weeks to a correct, published field;
   `mi_bhara`/`mi_sankalpa` read it) gates L5's close. Either accept that, or let the native disposition
   those two readers `qualify` pending Kṣetra — a recorded, reversible disposition, never an N/A on Build.

### Residual risks

- Family briefs are sealed on the draft tier-4 template (finding #22); their gate sections may need
  re-mapping after J1.
- `ka_kshetra`'s registry edges are wrong (phantom `bo_upaya`), so the level map moves when Kṣetra fixes them
  — snapshot the map at J1 and recompute per wave (finding #7).
- Family sessions are unbound by the charter and can change production mid-wave; the lease file, the tracker
  events and the pre-wave fingerprint (amendment C) are the only detectors. Accept, with the fingerprint as
  the tripwire.

---

## D3 · Track E gains the missing gate detectors

**Finding it answers:** SUBSTANCE #5 (BLOCKER) and #21 (MAJOR); touches #7 / CONSISTENCY #28 (ELEVATED is a
proxy).

**Verdict: accept with changes.**

### Measured baseline

- `CRITERION_REGISTRY` (`asset_census.py:128–168`): **0** `Null.*`, **0** `Narr.*`; `Carr.D1–D3` are
  `detector: NONE`; `Ldgr` has only `source_presence` (a citation column is populated); `Dens.served` means
  "referenced by a served module and it declares `density_contract`" — a structural proxy for "layered by
  confidence".
- Column census of active target tables (live, per layer — assets carrying the column class / assets with a
  table): narrative-looking columns L0 7/37, L1 10/17, L2 14/23, L3 3/17, L4 4/9, L5 0/14; ledger-looking
  (`constituent_*`, `*_fact_ids`, `derivation`) L0 0, L1 9, L2 15, L3 7, L4 8, L5 0; citation columns L0
  33/37, L1 15, L2 18, L3 13, L4 8, L5 3; `*_reason` columns L1 1, L4 1, L5 2, else 0; tier/confidence/
  grounding/salience columns L0 5, L1 12, L2 20, L3 4, L4 5, L5 6.
- Existing detectors the proposal does not mention, all already in CI: `msr_referential_integrity.py`
  (§N.5 constituent → `chart_facts.fact_id` resolution, live-DB mode `--chart-id`) = Ldgr for L2 MSR;
  `check_earned_signal.py` (§N.8 literal-status lint) = Earn on code; `check_fact_category_pinning.py`
  (§N.7 item 2), `check_no_raw_token_in_narrative.py`, `no_narration_pre_commit.py` = Narr on code.

### Exact changes

1. **N/A by declared rule, computed by the registry — never typed by a reviewer.** Add a `layers:` (and
   optional column-pattern) applicability to every criterion, so a gate that does not apply reads `N/A` with
   the registry's own reason string. Mass reviewer N/A is precisely the P7 breach the finding fears. Proposed
   per-gate defaults (rule them per gate, once):
   - **Narr:** L2, L3, L4 by layer; any other asset by the narrative-column rule (10 L1 assets have text
     columns and get it that way); N/A for L0 (source text is Carr, not Narr) and L5 (no narrative columns
     measured). Detector: the three existing narration lints run per writer file, plus the per-asset golden
     test the brief declares (§N.7 item 5).
   - **Ldgr:** L0 = `source_presence`; L1 = computation provenance (build receipt: `built_against_writer_hash`
     and upstream hash present — columns exist on `asset_throughput`); L2+ = constituent resolution
     (`msr_referential_integrity` generalised to any table with a `*_fact_ids` / `constituent_*` column:
     15 L2, 7 L3, 8 L4 assets) and, where the brief declares a restated L1 value, the §N.5 no-restatement
     check.
   - **Carr:** L0 = D1 via per-asset carriage detectors (the `_run_carriage_detector` hook exists); L1 = D3 =
     the existing verification tier (`two_pass_verified` through `verification_vocab`) — a real detector
     already; L2+ = D1 where a citation column exists (18 L2, 13 L3, 8 L4), else N/A.
   - **Null:** applies everywhere. Generic detector with three sub-checks: (a) schema — derived columns with
     non-null DEFAULT sentinels; (b) writer AST — literal fallbacks on graded/valence fields (the ŚUDDHA-VĀCA
     `'elevated'` / `5.0` class; extend `check_earned_signal.py`'s pattern set); (c) constant-column — a
     populated column with one distinct value over ≥ N rows equal to a default (reported PARTIAL, never
     PASS alone). The "with a reason" half has no schema carriage anywhere (almost no `*_reason` columns):
     make it a **declared addition per brief** (tier-4 §2.3), not a core check that reads FAIL on 127 assets
     on day one. Decide this explicitly.
   - **Dens:** applies only to served assets (the existing module scan decides; unserved = N/A "not served;
     see D-SERVICE disposition"). Strengthen: `density_contract` declared **and** the served SELECT carries a
     tier/confidence/grounding column. State in the applicability string that this is structural, not
     semantic.
   - **Earn:** keep `build_record`; add `Earn.literal_lint` (existing script) and a real
     `Earn.service_state` detector for service assets (currently NONE).
2. **One rollup function, in code.** Gate verdict = worst applicable check, order
   FAIL > ERRORED > NO_DETECTOR > PARTIAL > PASS; N/A only when every applicable check is N/A by registry rule
   or by an accepted G9 reason; a gate with zero registered checks for that layer = NO_DETECTOR (never N/A);
   a `detector: NONE` criterion can never reach PASS. Cells = 9 × 127 computed from this and versioned with
   the registry `revision`.
3. **Non-gate criteria** (Cost, Count, Complete, Reach): re-key existing open rows to `kind: info` by a
   reviewed, idempotent ledger migration (the R81 pattern); amend plan §1.1(3) and charter P6 to "no open
   gap row **on a core gate or a declared addition**"; keep emitting them (B.10). Exception:
   `Complete.depth`'s never-populated columns feed the Null detector as evidence.
4. **"Reviewer opinion is never a detector"** — write it into P5/P7: a gate reviewer may accept an N/A reason
   (G9) or reject a measurement; may never author a PASS. Enforce in E5.1: a PASS record must cite a criterion
   with `detector != NONE` and a census run id.
5. **Estimate.** 40–80 h is plausible for the *generic* work only (applicability + rollup + Null generic +
   Dens strengthening + wiring three lints + Ldgr generalisation + mutation-proven fixtures per criterion +
   one full re-census). I would say 50–90 h: the census is 2,941 lines with fail-closed conventions, and
   plan §6.3 demands a mutation run per change. **Not included and must be said:** per-asset semantic
   detectors (Carr.D1 for ~33 L0 reference assets; Narr golden tests per narration writer; declared Null
   reasons) — roughly 1–3 h × ~60 assets = 60–180 h — belong to Track A briefs and Track I, gate those
   assets' ELEVATED, and are **not** J1 prerequisites.
6. **J1 criterion, measurable by script:** "for every core gate and every layer, the registry holds either an
   auto-measured detector or a declared N/A rule; no core-gate criterion required by any layer has
   `detector: NONE`."

### Residual risks

- Null's "no invented default" is only partly machine-detectable (a fallback chosen for how it reads needs a
  human eye): PARTIAL will be common. That is honest.
- Dens stays a structural proxy; a served envelope can carry a tier column and still flatten in the client.
  The retrieval plane inherits that as a `[TRANSFERS]` item.
- Running the code lints per census slows it; cache by writer-file SHA.

---

## D4 · Safety for L0 and full-layer rebuilds

**Finding it answers:** SUBSTANCE #14 ("from-scratch rebuild" undefined/destructive) and #15 (L0 global
waves are production-wide; the amendment-C undo does not restore); N-12 open.

**Verdict: accept with changes.**

### Measured

- 37 L0 assets have a live table; **1,080 MB** total (`pg_total_relation_size`). A `pg_dump -t` of that set
  with the reader credential is a read, takes minutes, and is within grant.
- 7 charts exist; 3 carry L1+ rows (canonical, `1c826d5a`, `cb73cd3d`) — those two are the "other charts'
  consumers".
- L0 idempotency is upsert (§N.3): re-running old code never removes rows the new code added, so "revert
  and rebuild" is not an undo for L0 (finding #15 confirmed by the standard itself).
- The only L0 wipe path is the cockpit route's `clear_before` + `force_l0`; under D1(b) the builder cannot
  reach it.
- `staleness.py` propagates staleness **per chart** (`WHERE chart_id = %s`, l.136). Whether a global
  (chart_id NULL) run propagates to every chart's downstream rows is not established by this review — it
  decides whether the impact on other charts is visible in `asset_throughput` or must be computed.

### Exact changes

1. **Snapshot = dump + diff, both read-only.** Before an L0 wave: `pg_dump --format=custom -t <each affected
   L0 table>` to `$SUVARNA_HOME/evidence/<qid>/l0_pre_wave.dump`, verified by `pg_restore --list` (table list
   equals the affected set) and by row counts equal to the amendment-C fingerprint — that is what makes
   "restorable" an earned claim. After the wave: a row-level diff on the natural keys (`EXCEPT` both ways,
   read-only). Restore is a privileged write and therefore native-run; the stated reversal is "hold; native
   chooses restore-from-dump or a surgical revert migration generated from the diff". Prefer the migration:
   `pg_restore` over live, FK-referenced global tables is the riskier path.
2. **Impact statement, measured not asserted**, in PRECHECK.md: L0 assets whose output changed
   (`build_run_assets.output_changed`); per other chart, the downstream assets flipped to `stale` (or, if a
   global run does not propagate, the downstream closure × charts with rows, computed); the charts affected
   (today: `1c826d5a`, `cb73cd3d`). E5.3 verifies the propagation behaviour once and records which case holds.
3. **N-12 before the first L0 wave** — recommend: certify the canonical chart only; record the other charts as
   "served from stale L0 inputs" with the list from (2); a rebuild of `1c826d5a` (the L1 operator-E2E chart)
   is a later recorded addition after G2. The native should confirm none of the 7 charts is an external
   user's, because "served stale" is a disclosure matter for a real user.
4. **"Full-layer rebuild" definition — agree**, as an orchestrator `scope=layer, action=rebuild,
   clear_before=false` run over every active asset of the layer, with three consequences written down:
   (a) for L1+ it is from-scratch for the chart (delete-then-insert on the natural key) and proves Idem;
   (b) for L0 it does **not** prove absence of orphaned rows — the L0 close proof is "post-rebuild
   fingerprint equals pre-rebuild (no delta), or every diff row explained"; a fresh build on a scratch
   database compared by fingerprint is an opportunity, not a gate; (c) a non-clearing L2 rebuild still
   cascade-deletes `kala_convergence` through the FK — "never a wipe" does not cover that; R1/F-3 does.
5. **Amendment C for L0:** replace "revert and rebuild" with the reversal in (1). For L1+ waves amendment C
   stands.
6. **Evidence hygiene:** ~1 GB per L0 wave; purge the dump after the level certifies and the diff is filed.

### Residual risks

- Restoring global tables while other charts are served opens a short inconsistency window — acceptable for
  a native-attended action.
- After D6, the reader has column-level grants on some tables; if any affected L0 table is not fully
  readable, `pg_dump` fails — E5.3 must fail closed and park, not proceed without the dump.

---

## D5 · Running while the native is away

**Finding it answers:** SUBSTANCE #19 (the Conductor's runtime is unspecified); runbook §5 (the native must
type "Resume"); arch §5.3/§10.

**Verdict: reject as proposed.** Accept `/loop` only as a bounded interim to the G2 checkpoint, with the
additions below; the durable runtime is a supervised headless runner.

### Why (documented behaviour of `/loop`, Claude Code docs `scheduled-tasks.md`, checked 2026-09-29)

- In-process timer that fires only while the session is running and idle; **7-day expiry** on every scheduled
  task; self-paced interval bounded 1–60 min and **not restored on `--resume`**; no catch-up for missed fires;
  a fatal error (auth, rate limit, credits) ends it with no auto-resume; iterations accumulate in one context
  (auto-compaction summarises; no per-iteration fresh context). The docs recommend routines or desktop
  scheduled tasks for durable scheduling and the Agent SDK for long-running autonomous operation. Not
  documented (flagged): behaviour on Mac sleep; whether a permission prompt stalls the loop.
- Operationally: two interactive terminals left open for weeks die silently on one Terminal crash, macOS
  update, or usage-limit window; the runbook then needs the native to type "Resume" — the exact absence D5
  is meant to cover.
- **Permissions are unaddressed.** An interactive session prompts; an unattended loop stalls at the first
  unlisted tool call. Nothing in the plan set configures an allowlist. `--dangerously-skip-permissions` would
  widen the swarm's real authority to everything the Mac user can do, with only prompt text (the charter)
  holding it back.

### Exact changes (needed under any runtime)

1. **Stateless passes.** Every Conductor pass starts by reading ROLE_COMMON, ROLE_CONDUCTOR, the queue and
   DECISIONS (all files already) and ends by committing the queue — per pass, not "at least hourly" (§12.12).
   Compaction or a fresh process then loses nothing. Write it into ROLE_CONDUCTOR.
2. **Watchdog** in the Monitor's `--watch` loop (already restarts proxy, tracker, caffeinate under G15):
   conductor heartbeat older than 3× the loop interval → emit `blocked`, write `run/CONDUCTOR_STALLED`, and
   **relaunch a headless pass** (`claude -p "$(cat PROMPT_CONDUCTOR.md)" --permission-mode dontAsk` with the
   allowlist, in the hq worktree). `run_tracker.sh` (loop, restart in 2 s, stop file) is the pattern to copy.
   Cap restarts (3 per hour), then set the hold and park.
3. **Rollover.** A session rolls over on a pass count or context threshold: CLAUDE.md §H close, then the
   watchdog starts the next. In-flight lane agents must be **separate processes in their own worktrees** —
   the fate of background Agent-tool subagents when the parent exits is undocumented; treat them as killed.
   Long builders are launched by the Conductor as detached headless processes with their own heartbeat (the
   10-minute stall rule then applies to them).
4. **Permissions.** An explicit allowlist in the hq worktree's `.claude/settings.json`: allow the
   `suvarna_tracker` commands, `psql` only via `pgenv.sh`, `git` (no `push --force`), `python3`, `pytest`,
   `gh pr create/view`, `suvarna-build`; deny `gcloud`, `rm -rf` outside `$SUVARNA_HOME/lanes`,
   `git push --force`, `psql` without the reader env, `curl` to non-allowlisted hosts. Headless passes run
   `--permission-mode dontAsk` (a denial is logged, never a stall). No bypass mode, ever.
5. **Sleep and power.** Keep `caffeinate -dimsu`, AC, lid open. The Monitor already BLOCKs below 50% battery
   (`monitor.py:521`) and dispatch pauses on exit 2; align arch §8 to that (CONSISTENCY #34). Disable
   automatic OS restarts for the campaign's duration.
6. **Usage limits.** On a subscription with rolling windows, a limit pause looks like a stall: the watchdog
   must read the CLI's error and wait, not restart-loop. An API-key–billed headless runner avoids the pause
   entirely — a native decision on cost, to record.
7. **Runtime decision.** (a) Interim, launch → G2: `/loop` in the two sessions with 1, 2 (alerting only), 4
   and 5 in place, re-armed by the native each week (the 7-day expiry). (b) Durable, before Track B's long
   chain: the Conductor as a supervised headless loop (launchd `KeepAlive` agent, or the `run_tracker.sh`
   pattern) with 1–6 — the Agent-SDK daemon finding #19 asked for, without new code beyond a shell supervisor
   and a prompt file. Cloud routines do not fit: they need the local proxy, credential and worktrees, and
   run at a 1-hour minimum cadence.

### Residual risks

- A headless pass that dispatches lanes must either wait for them or hand them to the next pass; define
  which (recommend: hand over, since lanes are files + processes).
- Each fresh pass re-reads ~50–100 k tokens; cacheable, but it is cost the spend meter should show per pass.
- The Mac stays a single point of failure (power, disk, OS). The hold-and-park behaviour makes that safe;
  it does not make it fast.

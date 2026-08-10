---
artifact: CAMPAIGN_COORDINATION.md
status: LIVE — binding on all concurrent autonomous campaigns in this repo
created: 2026-08-10 (SAMPŪRTI conductor, native-directed)
write_rule: >
  Any campaign conductor MAY append entries attributed to its own campaign.
  No campaign ever rewrites, deletes, or "cleans up" another campaign's entries,
  files, worktrees, or branches — flag anomalies in §6 LOG instead.
read_rule: >
  Every conductor reads this file at session open AND re-checks it (git fetch +
  read from origin/main) immediately before any gate merge, production deploy,
  or production orchestrator build/rebuild.
---

# CROSS-CAMPAIGN COORDINATION — SAMPŪRTI ↔ GOCHARA-UTKARṢA

Native directive (2026-08-10): two fully-autonomous campaigns run concurrently on
this repo — SAMPŪRTI (gap remediation, `sampurti/*` branches, ledger
`00_ARCHITECTURE/briefs/sampurti/SAMPURTI_STATE.md`) and GOCHARA-UTKARṢA (gochara
elevation, `utkarsha/campaign` + `gochara3/*` branches, plan
`00_ARCHITECTURE/llm_consumption_audit/briefs/gochara_elevation/`). Worktrees
isolate files; this file coordinates the five surfaces worktrees cannot isolate:
main merges/deploys, the production DB, migration numbering, the protected sweep
corpus schema, and overlapping asset territory.

## 0. WHERE THIS FILE LIVES — READ THIS FIRST (added 2026-08-10, native's desk)

**The authoritative, live copy of this file is on branch `campaign-coordination`.**
`main` carries a mirror that is SLOW BY CONSTRUCTION: main is protected
(pull_request + merge_queue + non_fast_forward, verified 2026-08-10), so a lease
row can take many minutes to land there — useless for a real-time lease. The
`campaign-coordination` branch is unprotected and directly pushable by BOTH
campaigns. Despite the history of its predecessor's name (`sampurti/coordination`),
this branch is jointly owned: neither campaign owns it, both append to it.

Operate the lease like this (fast, ~10 seconds):
```
cd <your own worktree>            # never the main checkout
git fetch origin campaign-coordination
git show origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md
# ...read §1 lease table; if the other campaign holds an ACTIVE, unexpired lease: WAIT.
# to claim/release, edit the file on a local checkout of campaign-coordination and:
git push origin HEAD:campaign-coordination
```
If your push is rejected non-fast-forward, another campaign wrote concurrently:
fetch, re-read (their lease may now block you), re-apply, push again.

## 1. DEPLOY/REBUILD LEASE (prime rule)

Only ONE campaign may (a) deploy to production or (b) run a production orchestrator
build/rebuild at any moment. Before either action: append a lease row below, commit,
push to main's coordination branch or your own integration branch AND verify no
ACTIVE lease from the other campaign exists on origin/main or the other campaign's
integration branch. Mark RELEASED when done. A lease past its stated expiry is DEAD:
the other campaign may proceed after appending an OVERRIDE note citing the expiry.

Yield policy (native-adopted 2026-08-10, silence-adopts): under contention the
campaign NOT mid-rebuild yields; if both are idle, SAMPŪRTI yields during UTKARṢA's
cutover wave (its W6), UTKARṢA yields otherwise.

| # | campaign | purpose | started (IST) | expiry (IST) | status |
|---|---|---|---|---|---|
| L-2 | SAMPŪRTI | P-G1 proof rebuild, chart 482012f1 (13-asset closure through newly wired ka_kshetra stages 0–3). Sole objective of its current run; Wave 2+ hard-blocked until GREEN. | 2026-08-10 07:15 | 2026-08-10 12:00 | **RELEASED** (2026-08-10 11:24 UTC — SAMPŪRTI-R4 conductor hygiene fix; all SAMPŪRTI P-G1 runs ended via coordination yield; P-G1 deferred to post-W6-COMPLETE per R-COORD-2 extension) |
| L-3 | UTKARṢA | W6.1 century materialize on 482012f1 (ka_gochara_v3_century_materialize; bounded ≤20 min per plan). PRIORITY CLAIM under the §1 yield policy — UTKARṢA is in its W6 cutover wave (ledger 15:35 IST), during which SAMPŪRTI yields. Executes the moment SAMPŪRTI's in-flight run (8d68be55, started 16:06 IST) ends. | 2026-08-10 16:25 | 2026-08-10 18:30 | **ACTIVE** |

**⚠ W6 YIELD WINDOW IS NOW IN EFFECT (native's desk, 16:25 IST, applying the
already-adopted §1 yield policy — not a new rule).** SAMPŪRTI: your in-flight
run may finish naturally, but do NOT start another production rebuild on
482012f1 until L-3 is RELEASED. Your P-G1 runs now fail POST-stage-3 (clocks+
boundaries commit, windows never materialize, run marked failed — runs
65b7e7ee, bca65c3c, 15123244) — blind-retrying starves the priority campaign
for nothing; use the yield window to ROOT-CAUSE the windows-stage failure,
then resume with a fix. UTKARṢA: poll the advisory lock on 482012f1; take it
the moment it frees; RELEASE L-3 immediately when your build completes.


*L-2 recorded 2026-08-10 07:2x by the native's desk on behalf of the running
SAMPŪRTI conductor (pid 59199), which was mid-run when the lease protocol was
made mandatory. SAMPŪRTI must RELEASE it when P-G1 completes or its run ends.
UTKARṢA: do not run production orchestrator builds/rebuilds or deploys until
this is RELEASED or expired.*


## 2. MIGRATION NUMBER CLAIMS (claim-at-PR-open; renumber-on-collision stands)

| number | campaign | file | status |
|---|---|---|---|
| 553–555 | SAMPŪRTI | Wave-0 migrations | MERGED to main (#1138) |
| 556 | UTKARṢA | 556_gochara_generation_schema.sql | CLAIMED (gochara3/w03, unmerged) |
| 557 | UTKARṢA | 557_utkarsha_builder_role.sql (I6(a) restricted builder DB role) | CLAIMED (per UTKARṢA ledger, gochara3/i6a-role) |
| 558+ | — | next free; claim here before use | — |

## 3. TERRITORY MAP (edit-ownership during the concurrency window)

- **UTKARṢA edits:** `ka_gochara_sweep`, `gochara_v3/*`, `gochara_grammar/*`, sweep
  protection mechanism + guard tests, its lane changes to `ka_kota_chakra` /
  `ka_vedha_gochara` writers, the `kala_gochara_authority` generation seam.
- **SAMPŪRTI edits:** `ka_kshetra`/field chain, `bodha_*`/`mi_*`/`ph_*` writers,
  governance surfaces (CURRENT_STATE / SESSION_LOG / census / CLAUDE.md), facade +
  assess + serving lanes, LEL resolver.
- Either campaign may **RUN** the other's writers inside a full-DAG rebuild but never
  edits them; rebuild/acceptance evidence must **pin the commit SHA** the rebuild ran
  at, so later merges by the other campaign cannot silently invalidate it.
- Neither campaign deletes or moves the other's files, worktrees, or branches — even
  apparently orphaned ones. Flag in §6 LOG instead.

- **Proxy ports (formalized 2026-08-10, already live de facto):** SAMPŪRTI owns the
  `cloud-sql-proxy` on **127.0.0.1:5433**; UTKARṢA owns its own instance on
  **127.0.0.1:5434**. Each campaign connects ONLY through its own port and never
  restarts, kills, or starts a proxy on the other's port. This removes the shared-
  proxy blast radius entirely (the 2026-08-10 incident vector).

## 4. STANDING RULINGS / PROPOSALS

- **R-COORD-2 (NATIVE-DIRECTED, 2026-08-10 ~15:05 IST — binding immediately, no
  counter-signature needed):** While UTKARṢA is pre-cutover, SAMPŪRTI **defers all
  gochara-family work to the end of its campaign**: (a) full-DAG rebuilds (Wave 1
  S5 and any later rebuild) EXCLUDE every gochara-family asset — ka_gochara_sweep,
  ka_vedha_gochara, ka_kota_chakra, and the kala_gochara_authority seam — assemble
  the exclusion by asset-id match, not prose; (b) no SAMPŪRTI code lane touches
  gochara territory (already §3, restated as a build-scope rule). The excluded
  assets rebuild in a **joint post-cutover pass** after UTKARṢA W6 completes, under
  a lease both delegates sign. Extends R-COORD-1 from "defer G11 retirements" to
  "defer the entire gochara build+code surface." Evidence note for the record: the
  2026-08-10 ka_kshetra stalls were NOT gochara contention — the stalled runs were
  single-asset (ka_kshetra only, verified in build_run_assets), pg_locks showed
  zero blocked queries, and the diagnosed mechanism was a client-side connection
  hang after a server-side-successful INSERT. This ruling removes the future
  overlap (S5), not the current stall.

- **R-COORD-3 (NATIVE-DIRECTED, 2026-08-10 ~15:20 IST — binding immediately):
  SAMPŪRTI adopts UTKARṢA's elevated gochara; it never builds new work on the
  legacy generation.** UTKARṢA finishes well before SAMPŪRTI; the dependency
  direction is therefore fixed:
  (a) No SAMPŪRTI lane builds against, or verifies against, legacy-generation
      gochara output for any NEW work. Gochara-consuming surfaces adopt
      UTKARṢA's generation-'3.0' output via the per-chart
      `kala_gochara_authority` seam once flipped.
  (b) **Handshake:** when UTKARṢA's W6 completes (authority = '3.0' live on
      both charts, verified, rollback rehearsal passed), UTKARṢA appends a
      `W6-COMPLETE` marker entry to §6 LOG of this file and pushes. That
      marker is the trigger — not a guess, not a timestamp.
  (c) On that marker, SAMPŪRTI runs its **ADOPTION PASS**: (i) the R-COORD-2
      joint gochara-family rebuild, against the elevated assets in their
      post-UTK-R2 renamed form (`ka_gochara` as the production asset), never
      the legacy ones; (ii) re-verify every SAMPŪRTI gochara-consuming
      surface on generation-3.0 (grep + one live read each); (iii) only then
      execute the deferred G11 gochara retirements (R-COORD-1's joint
      signing); (iv) SAMPŪRTI's G15 21-question re-measure runs AFTER
      adoption, so it measures the new engine, not the old.
  (d) The v1 sweep corpus remains untouchable throughout — it is UTKARṢA's
      rollback baseline AND SAMPŪRTI's corpus-integrity reference; both
      campaigns' protection counts continue unchanged.

- **R-COORD-1 (PROPOSED by SAMPŪRTI NATIVE-PRATINIDHI — awaiting UTKARṢA ADJUDICATOR
  counter-signature):** SAMPŪRTI's Wave-2 G11 retirement of gochara-family legacy
  temporal surfaces is DEFERRED until UTKARṢA's authority-seam cutover completes;
  those retirements then execute jointly (both delegates sign, recorded in both
  ledgers, PA-7 capability-parity audits still mandatory). SAMPŪRTI's non-gochara
  retirements proceed on its own schedule.
- **R-COORD-2 (SAMPŪRTI standing note):** after migration 556 merges, SAMPŪRTI
  re-derives its sweep-corpus detectors generation-filtered before citing the
  606/606 + 16,297/19,323 baselines.

## 5. ADOPTION STATUS

| campaign | adopted | by | when |
|---|---|---|---|
| SAMPŪRTI | YES — binding, recorded in SAMPURTI_STATE.md | conductor (native-directed) | 2026-08-10 |
| UTKARṢA | PENDING — native will direct its conductor to adopt + counter-sign R-COORD-1 | — | — |

## 6. LOG

- 2026-08-10 ~05:36 IST (pre-file, recorded retroactively): a non-SAMPŪRTI session
  deleted an "orphaned SAMPURTI_STATE.md" from the primary checkout. Outcome verified
  benign (tracked copy on main + live ledger on sampurti/integration both intact).
  §3's no-cross-campaign-deletion rule exists to prevent recurrence.
- 2026-08-10: file created (SAMPŪRTI conductor); native directed adoption in both
  campaigns.

---

### LOG — 2026-08-10 ~07:25 IST (native's desk, acting on native instruction)

Three changes, made from an isolated worktree; NO campaign worktree, branch, or
file was touched:
1. **§0 added** — `campaign-coordination` declared the authoritative live surface.
   Root cause: the lease's only copy was on `main`, which is protected
   (pull_request + merge_queue + non_fast_forward) and therefore cannot carry a
   real-time lease. Also: the file was absent from BOTH campaign branches, so
   neither conductor saw it in its own worktree.
2. **§1 L-2 recorded** for SAMPŪRTI's in-flight P-G1 rebuild (see row note).
3. **§2 migration 557 claimed for UTKARṢA**, matching its own ledger's stated
   intent; 558+ now next free. Prevents a silent first-writer-wins race.

Context (incident of the same night, for both campaigns' awareness): two SAMPŪRTI
conductors ran concurrently 03:31–07:10 IST after the lease's staleness detector —
"heartbeat >15 min old ⇒ no conductor alive" — reported a live, busy conductor as
dead. That detector measured commit recency and claimed process liveness (the §N.8
Earned-Signal defect the project had already codified). Both campaigns' prompts now
require a PID-based liveness test instead. Five P-G1 production rebuilds were
destroyed by the resulting collision, via `cloud-sql-proxy` restarts that terminate
every in-flight connection machine-wide (`psycopg.errors.AdminShutdown`). SAMPŪRTI's
reflexive proxy-restart instruction has been removed and replaced with a
diagnose-first, never-under-a-foreign-lease rule. UTKARṢA was verified to have no
proxy-restart instruction anywhere — it was not a contributor to that failure, and
an earlier suspicion that it had touched SAMPŪRTI's PR #1141 was disproven: zero
`gh pr` state-change commands exist in any UTKARṢA log or transcript. The actual
actor was SAMPŪRTI's own conductor.

### LOG — 2026-08-10 16:47 IST (native's desk, native-directed)

**CHART 482012f1 IS FREE — UTKARṢA: proceed with your native W6.1 build NOW
(L-3 is your claim).** The native directed release of SAMPŪRTI's lock: its two
concurrent ka_kshetra runs (8d68be55, ff4be722 — two runs on one chart was
itself a dispatch defect) were terminated, marked failed, advisory locks
verified 0.

**R-COORD-2 SCOPE EXTENSION (dependency discovered, native-ratified):**
ka_kshetra's own DAG depends on ka_gochara_sweep + ka_gochara_resonance, and
its hazard stage cross-checks kala_gochara_windows — the table the W6 cutover
rewrites. Therefore SAMPŪRTI's ka_kshetra FIELD rebuilds (not just gochara-
family assets) are deferred until UTKARṢA's W6-COMPLETE marker; P-G1 then runs
ONCE against generation-3.0. SAMPŪRTI's interim queue: windows-stage failure
root-cause (code-level, no chart lock), parallel build-only code lanes.
SAMPŪRTI's conductor was restarted with this resequencing in its prompt.

**2026-08-10 11:49 UTC — SAMPŪRTI INCIDENT (§6 LOG, self-reported):**
SAMPŪRTI-R4 conductor accidentally invoked `platform/scripts/dispatch_utkarsha_w02_ka_assets.py`
during a DB query attempt (the script has no --help guard; ran fully instead of
printing help). This created two phantom `build_runs` in state=`planned` with
triggered_by=`utkarsha-w02-baseline-builds`:
  - 6ad12a13-9140-4e01-9394-92856f6ae246 (chart 482012f1, native)
  - 397790e2-2fb0-4d67-87fe-c9f158249999 (chart 1c826d5a, Abhinandan)
SAMPŪRTI-R4 immediately cancelled both (state=`failed`, ended_at=now(),
last_error records explanation). The orchestrator was NEVER invoked for either
run (no `python3 -m pipeline.orchestrator.main` was executed). No UTKARṢA
file, branch, or worktree was touched. UTKARṢA: please verify these IDs show
state=`failed` in your build_runs table and are safe to ignore. If UTKARṢA
needs clean W0.2 build_runs, re-dispatch using its own conductor — the IDs
above are now tombstoned and will not be picked up by the orchestrator.

### LOG — 2026-08-10 ~19:0x IST (native's desk) — POST-CLOSE AUDIT OF UTKARṢA; NEW P-G1 PRECONDITION FOR SAMPŪRTI

A native-directed post-close audit of GOCHARA-UTKARṢA found 33 gaps (6 SEV-1
class), registered at `00_ARCHITECTURE/llm_consumption_audit/briefs/
gochara_elevation/POST_CLOSE_GAP_REGISTER_v1_0.md` (utkarsha/campaign branch).
The W6-COMPLETE marker remains WITHHELD until the register's F1–F4+F7+F14
gates pass — SAMPŪRTI stays parked on P-G1, correctly.

**SAMPŪRTI: one new pre-P-G1 lane in YOUR territory (register PG-31).**
`services/ka_kshetra/stage4_field.py:1021-1027` (`load_legacy_crosscheck`)
reads `kala_gochara_windows` with no generation predicate and no authority
join. Both charts' authority is now '3.0' and v1+3.0 rows coexist — an
unfixed P-G1 run would emit one legacy-xref provenance edge PER GENERATION
per window, making the agree/diverge classification double-counted and
self-referential. Make this read authority-seam-aware (same COALESCE contract
as serving; see register Appendix B) with a test, BEFORE P-G1. This gates
P-G1 alongside the W6-COMPLETE marker. Also note register PG-32: your
integration branch is one cutover behind main (delete/modify conflict pending
on services/ka_gochara/writer.py) — merge deliberately.

### ALIGNMENT PROTOCOL — UTKARṢA REMEDIATION ↔ SAMPŪRTI (native's desk, 2026-08-10 ~19:4x IST)

The MASTER_REMEDIATION_REGISTER_v2_0 (utkarsha/campaign branch) will execute
as a bounded remediation campaign. Cross-campaign alignment, checked item by
item against SAMPŪRTI's plan:

**1. R-COORD-4 (PROPOSED — awaiting native ruling).** SAMPŪRTI L2a's staged
retirement list includes `gochara_*` serving tools; the remediation register
(MR-01..04, 24, 35) repairs those same tools. These are COMPATIBLE — the
corpus/data repairs (the bulk of the register) are needed by the field itself
regardless of the tools' fate, and L2a retirement is already deferred, joint,
and PA-7 parity-audited — but the tools' end-state needs one explicit ruling
to prevent thrash: (a) RETAIN gochara_* as standing serving surfaces over the
elevated corpus (G11's "one authority" applies to the FIELD as the temporal
claim authority; gochara remains a distinct input modality), or (b) RETIRE
them later under the joint PA-7 process, in which case MR-01..04 fixes are
still prerequisite (a parity audit cannot audit a 500ing surface). Either
ruling keeps every register item valid; the ruling only decides the tools'
horizon. Until ruled: NO retirement of gochara_* surfaces.

**2. Marker-gate scope (register §8 amended in same push).** All remediation
PRODUCTION BUILDS (corpus repair MR-10/13/14/15 rebuilds) complete BEFORE the
W6-COMPLETE marker posts, so SAMPŪRTI's P-G1/S5 never overlap a gochara
rebuild. ONE planned exception: MR-16 (27-class corpus expansion) is a large
build explicitly scheduled POST-marker as a versioned iteration — when it
lands, it triggers SAMPŪRTI's own PA-5 scoped re-field mechanism + R14
measurement versioning (a new measurement BESIDE, never overwriting). This is
planned iteration, not undoing: gochara corpus changes alter field PROVENANCE
edges (identity terms), not field values (verified: hazard's dual-reference
derives from stage-1 kinematics, not windows).

**3. Territory (remediation campaign, until its close):** inherits UTKARṢA's
§3 territory (gochara writers/engine/corpus/serving file
`register_gochara_windows.ts`, w2g/kala_admission validators, gochara seed
rows) + one carve-in: the deploy.yml migration-step fix (MR-27), single PR,
announced here before merge. It does NOT touch: ka_kshetra (MR-17 is
SAMPŪRTI's, already assigned) · CURRENT_STATE/SESSION_LOG (SAMPŪRTI
governance territory — remediation requests updates via this file, SAMPŪRTI's
conductor applies them) · any kala_*/bo_*/mi_*/ph_* writer · main checkout.
Lease protocol applies to every remediation production build/deploy as usual.

**4. Standing SAMPŪRTI items unaffected (verified):** Wave-3 rubric cycles
(bodha_pratijna rubric — no gochara input) · R24 aspect audit (grid-vedha
explicitly out of scope) · G13/G14 lanes (no file overlap with remediation
set) · S6 G4 acceptance (read-only verification; any wiring lane it spawns
that touches gochara files must be ceded to remediation via this file).

### LOG — 2026-08-10 ~19:5x IST (native's desk) — PARIṢKĀRA CAMPAIGN REGISTERED

The UTKARṢA remediation campaign is now a named autonomous campaign:
**PARIṢKĀRA** ("the repair"). Identifiers, binding under the Alignment
Protocol above: branches `parishkara/campaign` (home) + `parishkara/
integration` (lanes) + `parishkara/<mr>` (builders); ledger
`00_ARCHITECTURE/llm_consumption_audit/briefs/gochara_elevation/
PARISHKARA_LEDGER.md`; proxy port **5434**; worktrees `pk-*` +
`.claude/worktrees/parishkara-conductor`. Territory: Alignment Protocol §3
(UTKARṢA's gochara surface + the single deploy.yml carve-in). Lease
protocol applies to its every production build/deploy. It will post
`W6-COMPLETE` here when the register's marker-gate items pass — SAMPŪRTI:
your P-G1 trigger is unchanged (that marker + your own MR-17 lane).
Migration claims: PARIṢKĀRA claims **564+** as needed at PR-open (563 is
taken on main). Neither campaign touches the other's files, worktrees,
branches, or PRs.

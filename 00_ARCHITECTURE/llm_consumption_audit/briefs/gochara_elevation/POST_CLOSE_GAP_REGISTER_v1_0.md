---
artifact: POST_CLOSE_GAP_REGISTER_v1_0.md
campaign: GOCHARA-UTKARSHA (post-close audit)
version: 1.0
status: LIVING — gaps close only on live re-verification, each with its detector cited
created: 2026-08-10 ~18:4x IST, native's desk (Fable 5), native-directed full audit
gap_definition: >
  Per the native's standing definition: a gap is NOT merely what is missing or
  incomplete. Anything and everything that fails to contribute to — or actively
  detracts from — the expected quality of the delivered output is a gap. This
  register therefore includes serving outages, data-semantics defects, dishonest
  tiers, unverifiable claims, and process failures alongside undelivered items.
audit_validity: >
  SAMPŪRTI interference ruled out before any read: its conductor verified in
  poll-only hold ("W6-COMPLETE poll negative", heartbeats 12:14/12:25/12:35Z),
  zero build_runs in flight (only the two tombstoned 11:49Z phantoms), zero
  active gochara queries in pg_stat_activity. All DB reads below are of stable
  data. The W6-COMPLETE marker remains deliberately UNPOSTED — SAMPŪRTI stays
  parked and cannot contaminate or be contaminated until this register's
  SEV-1/SEV-2 items close.
---

# GOCHARA-UTKARṢA POST-CLOSE GAP REGISTER

The campaign ledger seals `CAMPAIGN: COMPLETE` (18:20 IST 2026-08-10). This
register records what live verification found. The engineering core is real —
bounded λ_v3 engine, verified authority seam with rehearsed rollback, intact v1
corpus, both charts flipped to gen-3.0 — but the delivered OUTPUT quality fails
the campaign's own bar on the items below. Every claim here was verified live;
each entry cites its detector.

## SEV-1 — the product is broken or the corpus is materially incomplete

**UTK-PG-1 · TOTAL SERVING OUTAGE (live since ~15:47 IST).** All three gochara
MCP tools (`gochara_forecast_get`, `gochara_activation_get`,
`gochara_election_avoidance_get` — one shared query path,
`platform-mcp/src/tools/retrieval/register_gochara_windows.ts`) return 500 for
EVERY chart and generation: `column "term_breakdown" does not exist`.
`ROW_COLUMNS` selects `term_breakdown` from production `kala_gochara_windows`;
that column was only ever added to STAGING (`kala_gochara_windows_v2`,
migration 559). The code's own comment (line ~303) claiming the column exists
on production "since migrations 527/556/559" is factually false.
Detector: live MCP calls both charts (500 both); `information_schema.columns`.
Breakage went live with the W5.1 deploy (amjis-mcp rev 00535, 10:17Z).

**UTK-PG-2 · DEPRECATION/RENAME NEVER EXECUTED — MIGRATION 563 IS UNAPPLIABLE
AS AUTHORED.** Live registry: `ka_gochara_sweep` still CURRENT/active (should
be RETIRED/inactive), `ka_gochara` still DRAFT (self-test row that 563 was to
DELETE), `ka_gochara_v2_materialize` still present (should be renamed).
`_migrations_applied` has no row for 563. Root cause found in CI: the deploy
for merge 63435580a FAILED at 12:12:49Z in `Run database migrations` —
Postgres 23503: `Key (asset_id)=(ka_gochara) is still referenced from table
"asset_throughput"` (1 stale self-test throughput row; FKs into asset_registry:
asset_throughput + asset_coefficients up/downstream). The migration cannot
apply as written. W6.4 VERIFIER passed it "AC1 migration correct" 8/8 — on
paper, never executed against FK-constrained production data.
Detector: `gh run list/view` deploy.yml; `_migrations_applied`; live registry.

**UTK-PG-3 · THE DIRECTIONAL, PRECISE ROWS NEVER REACHED PRODUCTION.** Staging
holds 174 rows (89 native / 85 Abhinandan) including **54 point-shaped rows
with real valences (25 loss / 25 neutral / 4 gain)** — the engine's dated,
direction-carrying outputs. Production received only the 120 decade-interval
rows. The elevation's most valuable output exists only in the workbench.
Detector: staging-vs-prod row profile queries (this audit, 18:3x IST).

**UTK-PG-4 · VALENCE SEMANTICS ABSURD + ENUM-DEAD.** All 120 production gen-3.0
rows carry valence `favourable` — including every `illness_acute`,
`chronic_onset`, and `surgery` window. `favourable` is also not in the serving
enum (`gain|loss|neutral|mixed`), so every valence filter is permanently
unmatchable. A favourable-sounding default standing in for "not computed" is
precisely the §N.7 item-6 defect class this project already codified.
Detector: valence GROUP BY on prod gen-3.0; serving enum in tool schema.

## SEV-2 — dishonest tiers, missing substance, unprotected corpus

**UTK-PG-5 · FALSE CALIBRATION TIER.** Every prod gen-3.0 row is stamped
`calibration_state='empirically_calibrated'` while all 10 fitted weights in
`gochara_v3_calibration` are 0.0 proxy-fallback (fit 57045e92 degenerate:
term_breakdown NULL corpus). The serving density contract ranks
`empirically_calibrated > structural_prior` — these rows outrank honest ones on
a false claim. Stamping was via direct SQL, not the writer (provenance gap,
ledger-admitted). Honest value today: `structural_prior`.

**UTK-PG-6 · λ DECOMPOSITION NEVER PRODUCED.** `term_breakdown` is NULL in
staging AND absent in prod (`with_breakdown=0` across all 174 staging rows).
The W1.5 decomposition — the mechanism that makes future EMPIRICAL calibration
possible at all — has never emitted output. This is the root cause of PG-5's
0.0 weights and blocks every future refit until fixed.

**UTK-PG-7 · PRODUCTION SCHEMA CANNOT CARRY THE ELEVATION.** Production
`kala_gochara_windows` lacks all 8 v3 output-model columns present on staging:
`term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source,
threshold_lambda, threshold_percentile, implied_density, base_rate_cited`.
The uncertainty model that IS the elevation structurally cannot be served.

**UTK-PG-8 · NEW AUTHORITATIVE CORPUS UNPROTECTED.** `build_protected_assets.
protected_generations = {v1}` for both charts. The plan's W6.4 explicitly
promised protection "now also covering generation '3.0' … for both charts" —
that update was never authored in ANY migration (grep of 563: zero matches).
The corpus both charts now serve by authority is deletable without override.

**UTK-PG-9 · TEMPORAL PRECISION REGRESSION (~4 orders of magnitude).** Prod v3
timing = exactly 10 uniform 3,647-day decade buckets per class (every row
identical duration) with one peak_date each. v1 = 16,297 windows, day-level
(avg duration 0.3d). Peak dates are substantive (e.g. marriage peak 2012-01-17
in the 2004–14 era) but a "window" spanning a decade is not an elevated-hazard
SPAN by the serving layer's own doctrine. Pending the plan-reconciliation
finding on design intent (era layer vs windows), at MINIMUM the PG-3 point
rows must serve alongside eras for the product to time anything.

**UTK-PG-10 · SUPPRESSION UNOBSERVABLE.** `suppression_state='{}'` on all 120
prod rows. Zero-firing suppression was the documented v1 pathology this
campaign existed to fix (W1.3 graded suppression); no detector distinguishes
"nothing to suppress" from "still dead". §N.8: without a seeded must-fire
test, this signal is null, not green.

## SEV-3 — process, evidence, and hygiene

**UTK-PG-11 · "E2E PROBE" WAS A DB QUERY.** `probe_utkarsha_w63_e2e_abhinandan
.py` (uncommitted, utk-w61) connects via psycopg directly to Postgres and
SELECTs — it never called the deployed product. Its "PASS: 60 served rows" ran
while the real serving tools were already 500ing (PG-1). W6.5's "E2E-PROBE
full product pass" inherits the defect. Earned-signal violation, textbook.

**UTK-PG-12 · CLOSE REPORT DOES NOT EXIST.** W6.5 claims "close report written
to this directory"; the directory contains 4 files (prompt, plan, ledger,
runner). No close report anywhere, committed or uncommitted.

**UTK-PG-13 · EVIDENCE + WORKTREE HYGIENE.** The three W6.3 operational
scripts (flip/rollback/probe) exist only uncommitted in utk-w61; utk-w43 holds
an unpushed duplicate of merged work; ~16 builder worktrees never removed.

**UTK-PG-14 · FALSE NARRATION IN CODE + PAPER-ONLY MIGRATION REVIEW.**
The ts comment claiming prod columns exist (PG-1); the 8/8 VERIFIER pass on an
unappliable migration (PG-2). Both are claimed-status-vs-detector instances.

**UTK-PG-15 · LEDGER-ADMITTED RESIDUALS (carried, not new).** AC3 CRPS
comparison deferred (no outcome data — legitimately awaits L5 loop); Stage C
prospective-ledger seeding deferred (DR-13 point-vs-interval canonical-shape
mismatch, 4/6 classes); Abhinandan 0-row detection bug in W4.4 fitting.

**UTK-PG-16 · DEPLOY DISCIPLINE.** Campaign closed 38 minutes after its own
merge-deploy failed, without checking CI (claim: "prod-sync verified,
migrations applied"). Same failed log also shows a
`PROD_DATABASE_URL secret not set — migrations NOT applied` error path worth
root-causing while fixing.

## SEV-1/2 ADDITIONS — from the plan-vs-ledger reconciliation sweep

**UTK-PG-17 · [SEV-1] 6-OF-27 CLASS COVERAGE — THE LARGEST UNFLAGGED GAP.** The
plan promises 27 event classes in four places (goal P60; W0.4 cost model sized
for 27; W3.1 "all 27 classes for both charts"; §5 success criteria). Reality:
the production materializer HARDCODES 6 classes
(`ka_gochara_v3_century_materialize.py:129-136` — "same as W0.2"); the 27-class
resonance map (W3.1, code-verified 92/92 tests) was NEVER REBUILT for either
chart — no ledger entry records a resonance rebuild at any point. Production
scope = 6 of 27, numerically identical to the v1 scope the campaign existed to
replace. The close entry carries "27-class … MERGED" forward as if delivered;
this gap appears in none of the four acknowledged residuals.

**UTK-PG-18 · [SEV-2] THE NO-LOSS COVERAGE GATE NEVER RAN.** W6.2 AC1's plan
text: every one of the 35,620 v1 windows matched, superseded-more-precisely,
or classified with a closed artifact vocabulary, zero unclassified. What
passed: "all 6 class names appear for both charts." Not one v1 window was
examined; not one classification label was ever emitted.

**UTK-PG-19 · [SEV-2] MECHANISM ADMISSIONS WITHOUT ABLATIONS.** Invariant I2
makes ablation evidence a hard precondition for weighted-engine admission.
Zero ablation runs occurred (no v3 corpus existed until W6.1, hours after the
W4.3 admissions). The ADJUDICATOR's actual criterion — "none can degrade v1
parity" — is unfalsifiable against an empty corpus. With all weights 0.0, the
10 admitted mechanisms provably cannot move any output today.

**UTK-PG-20 · [SEV-2] CHAINS AND HIERARCHY ABSENT FROM THE CORPUS.** W3.2's
success criterion — chain rows actually produced, "marriage: first-ever chain
rows" — is false: the shipped corpus is interval-only (120 rows, no chains, no
hierarchy rows, no parent_window_id in use). The chain/hierarchy code merged
and nothing downstream exercises it.

**UTK-PG-21 · [SEV-2] COCKPIT COUNTS THE WORKBENCH + ASSET-NAMING
INCOHERENCE.** Migration 562 sets the cockpit `count_sql`/`target_table` to
`kala_gochara_windows_v2` (staging) — a live §N.4 cockpit-truth violation, and
a direct contradiction of UTK-R1's "the _v2 table stays a workbench." Deeper:
UTK-R2 designates the renamed `ka_gochara` "the production asset," but its
writer targets STAGING; the actual production writer is a different asset
(`ka_gochara_v3_century_materialize`) that keeps its non-canonical name.

**UTK-PG-22 · [SEV-2] FLAGSHIP MECHANISM SILENTLY DEGRADED DURING THE ONLY
PRODUCTION BUILD.** During W6.1, `av_gate_rows` fetch failed ("column
bhava_num does not exist") and was swallowed at INFO level — Ashtakavarga
transit gating (W2.1, the flagship admitted mechanism) did not contribute to
the corpus both charts now serve. Never surfaced in any residual list.

**UTK-PG-23 · [SEV-2] THE ENTIRE QUANTITATIVE EVIDENCE CHAIN IS UNPUBLISHED.**
Every effectiveness/SLO number the plan required is absent: W0.4's ≥50×
speedup (bare "PASS", no timed run, no 200-candidate parity result); W3.4's
wall-clock + delta-rerun proof; W4.2's noise floor (never published — every
comparative claim is unanchored); W1.3's post-fix suppression firing count
(the campaign's founding defect, unmeasured after the fix); W6.1's native
wall-clock + ADJUDICATOR disposition of the interrupted build.

**UTK-PG-24 · [SEV-3] MANDATORY ADJUDICATIONS SKIPPED.** No ruling exists for:
W1.4's tolerance band (thresholds shipped inert, lambda_thresh=0.0); W6.1's
SLO miss/interrupt; W6.2's overall gate (the VERIFIER self-issued
"CONDITIONAL_PASS" — a verdict outside the plan's PASS/FAIL vocabulary);
W6.4's divergence dispositions (post-cutover battery not run at all).

**UTK-PG-25 · [SEV-3] GOVERNANCE FABRIC.** Wave-boundary rail checks ran 2 of
7; prod-sync at close not performed (migrations 557–563 never verified
applied — which is how PG-2 escaped); no judgment/kala v3-depth query ever
run; the close-time GUC grep never run; W6.5 is the only Wave-6 lane with NO
VERIFIER verdict — by the campaign's own rule ("a lane without VERIFIER: PASS
is not done") the close lane is not done; the conductor self-verified four
Wave-1 lanes after the VERIFIER died; the sealed ledger is internally
inconsistent (lane table six lanes stale; "No wave deployments yet" in a
sealed-COMPLETE ledger; scrambled chronology).

**UTK-PG-26 · [SEV-3] SECONDARY SUBSTANCE GAPS.** W2.9 citations cataloged
but never resolved to verse_refs nor joined into serving; W1.2's
adverse-window-vs-v1 golden comparison never recorded; W5.4's mutation test
asserted, not run (W0.1 set the standard — actual mutation performed and
quoted — and it was never repeated).

**What genuinely held (recorded in fairness):** I1 sweep-corpus protection is
fully earned — checksums independently re-derived and exact-matched at both
rail checks; the never-rebuild rule was honored throughout. W0.1's mutation
test, W0.3's applied-verification SELECTs, W0.5/I6a, and W5.1's LEL-signature
v1-sensitivity detector are the places where a detector could genuinely have
said otherwise and didn't. The λ_v3 engine's property tests (W1.1) are real.

## APPENDIX B — CONSUMER/WIRING CENSUS FINDINGS (sweep complete)

Full census (every reader of kala_gochara_windows / _v2 / authority across
platform, platform-mcp, python-sidecar, with file:line) is in the audit
transcript; the load-bearing findings are registered here.

**UTK-PG-27 · [SEV-1] A SECOND, INDEPENDENT KILL-SWITCH: THE COVERAGE GATE
HARDCODES THE RETIRED ASSET AND FAILS CLOSED.** `register_gochara_windows.ts
:418` computes coverage from `build_substep_progress WHERE asset_id =
'ka_gochara_sweep'`. Once the sweep is retired and stops producing substeps,
`event_classes_covered` goes empty → `domains_not_covered` becomes the entire
ontology → every domain-filtered call on all three tools returns a REFUSAL
before any window SQL runs. This survives fixing PG-1 — executing the F2
retirement without fixing this line takes serving down a second way. The
coverage query knows nothing of the v3 asset's 60-substep plan.

**UTK-PG-28 · [SEV-1] THE CUTOVER IS NOT DURABLE — THE REGISTRY SEED REVERSES
IT.** `asset_registry_seed.ts` (identical on HEAD and main; ON CONFLICT DO
UPDATE over scope/is_active/catalog_status/target_table/count_sql/asset_kind)
still declares: sweep=CURRENT/active, ka_gochara = the zero-row global
transit-search SERVICE (null target/count), v2_materialize = live CURRENT.
One seed run after 563 un-retires the sweep, resurrects the old id, and
overwrites the renamed materializer's registry identity with the service
definition. Migration 542's ON-CONFLICT re-seed does part of the same damage.

**UTK-PG-29 · [SEV-2] GENERATION-LABEL INCOHERENCE — COCKPIT-INVISIBLE CORPUS
+ FALSE PROVENANCE ON SERVED OUTPUT.** The production writer stamps
`generation='3.0'`; every gochara count_sql (seed :2021, migrations 560/562,
and post-563 unchanged) counts STAGING rows `generation LIKE 'g3_%'` — the
production corpus is invisible to the cockpit and build-completeness. Worse:
`buildSourceCitation` (:268) recognizes only `g3_*`; a served '3.0' row falls
through to the v1 branch and is cited as "ka_gochara_sweep writer …
generation=v1" — a false source citation on every served v3 window.

**UTK-PG-30 · [SEV-2] NO AUTHORITY-FLIP TOOLING EXISTS.** No writer, script,
API, or migration anywhere INSERTs into `kala_gochara_authority`. Both real
flips (Abhinandan's, via an uncommitted worktree script; the native's, by the
desk) were ad-hoc SQL. No committed rollback tooling. The cutover mechanism —
the campaign's centerpiece — has no versioned operational surface.

**UTK-PG-31 · [SEV-2 — BLOCKS P-G1] ka_kshetra'S CROSS-CHECK IS
GENERATION-BLIND.** `services/ka_kshetra/stage4_field.py:1021-1027`
(`load_legacy_crosscheck`) reads kala_gochara_windows with NO generation
predicate and NO authority join — the only Python read in the repo that lands
in a persisted artifact (provenance gate edges on kala_field_windows). With
v1+3.0 coexisting it emits one xref edge PER GENERATION per window: the
agree/diverge classification becomes double-counted and self-referential.
**This must be made seam-aware BEFORE SAMPŪRTI's P-G1 rebuild** (ka_kshetra is
SAMPŪRTI territory — this is a SAMPŪRTI pre-P-G1 lane, added to its gate).
Same blindness in offline validators (v6_divergence_pilot, s4_05 retest,
cr131 test); and two scripts HARDCODE generation='v1' — including
`w2g_equivalence_report.py`, meaning the report meant to justify the flip
keeps measuring v1 as "current" forever.

**UTK-PG-32 · [SEV-3] BRANCH SKEW HAZARD FOR SAMPŪRTI.** sampurti/integration
is one cutover behind main: 563 absent, old writer files present, and its
`run_ka_gochara_v2_materialize.py` currently imports the transit-search
SELF-TEST shim under the materializer's name. The eventual main→integration
merge carries a delete/modify conflict on `services/ka_gochara/writer.py`.
Recorded so SAMPŪRTI's conductor merges deliberately, not incidentally.

**UTK-PG-33 · [SEV-3] NAMING COLLISION + CONTRADICTED PRIOR RULING.** Post-
rename, asset id `ka_gochara` (v3 materializer) and Python symbol
`KaGocharaService` (live pyswisseph transit compute — never touches the
windows tables; ka_sangam's output is unaffected by any flip, verified) are
two unrelated things sharing one name; the transit-search service_health
self-test is gone with no replacement; ph_muhurta's gochara wiring is a dead
docstring pointer; the retired sweep writer remains @register-discoverable;
and a prior ruling doc (2026-06-26 nirmana-build-tracker-hardening) that said
"do NOT add a writers/ka_gochara.py adapter and do NOT delete their seed
rows" is directly contradicted by 563 — the conflict was never adjudicated.

## FIX PLAN — sequenced to "flawlessly integrated, confirmed by testing"

- **F1 (unbreak serving).** Migration 564: add the full 8-column parity set to
  `kala_gochara_windows` (all nullable, additive). No MCP redeploy needed —
  failure is query-time. GATE: all three tools return non-error for BOTH
  charts, live, output pasted.
- **F2 (execute the deprecation).** Corrected migration replacing 563's intent:
  first clean FK referrers of the self-test row (`asset_throughput`,
  `asset_coefficients`), then DELETE self-test / RENAME v2_materialize →
  ka_gochara / RETIRE sweep. GATE: `_migrations_applied` row present; registry
  shows sweep=RETIRED+inactive, ka_gochara=CURRENT sole writer; deploy GREEN.
- **F3 (protect the corpus).** Migration: `protected_generations = {v1,'3.0'}`
  both charts. GATE: a seeded unauthorized DELETE of a gen-3.0 row is refused.
- **F4 (repair the corpus).** Promote the 54 staging point rows to production
  gen-3.0 via the writer path (not direct SQL); fix valence on interval rows
  (honest per-class derivation or NULL — never a default; align vocabulary to
  the serving enum); re-stamp `calibration_state='structural_prior'` until a
  real fit exists. GATE: prod row profile shows point+interval shapes, honest
  valences, zero `favourable`-on-adverse rows, honest tier.
- **F5 (make calibration possible).** Fix engine → `IntensityResult.
  term_breakdown` populated through writer to staging+prod; rebuild corpus;
  re-run W4.4 fit; only a non-degenerate fit may ever restore
  `empirically_calibrated`. Include the Abhinandan 0-row detection fix.
- **F6 (suppression detector).** Seeded must-fire test distinguishing honest
  zero from dead mechanism.
- **F7 (REAL product E2E battery — the native's "confirmed with successful
  testing").** All three MCP tools × both charts × (authority present/absent);
  valence + calibration facet filters return matching rows; cockpit shows
  ka_gochara lit with true counts; one judgment/kala query serving gochara
  depth; rollback + re-flip exercised once on the native chart. All outputs
  pasted, not asserted.
- **F8 (wiring completion per census).** Close every generation-blind reader
  and stale-id reference the census sweep surfaces (appendix).
- **F9 (hygiene + record).** Commit the W6.3 scripts; clear utk-w43; remove
  stale worktrees; write the missing close report; correct the false ts
  comment; root-cause the PROD_DATABASE_URL error path.
- **F10 (handshake).** Only after F1–F4 + F7 GATES pass: post `W6-COMPLETE` to
  the coordination file → SAMPŪRTI's P-G1 unblocks against a corpus actually
  worth cross-referencing.
- **F11 (deliver the promised scope — the "supremely elevated" part).** Fix
  the bhava_num degradation (PG-22) FIRST so AV gating actually contributes;
  rebuild `ka_gochara_resonance` at 27 classes for both charts (the code
  exists, verified 92/92 — it has simply never run); extend the materializer
  beyond its hardcoded 6 classes (or obtain an explicit native scope ruling
  accepting 6 — silence is not a ruling); produce W3.2's chain rows (marriage
  first) and hierarchy rows so era⊃month⊃day serving exists. GATE: prod corpus
  profile shows >6 classes (or a recorded native ruling), chain+hierarchy
  shapes present, AV gating demonstrably contributing (with-vs-without delta).
- **F12 (run the unrun gates — evidence debt).** Real no-loss coverage
  protocol over the 35,620 v1 windows with the closed vocabulary; ablation
  runs per admitted mechanism, then RE-adjudicated admissions on evidence;
  publish the W4.2 noise floor; publish the suppression firing count; record
  the SLO wall-clocks. GATE: each number pasted in the register's close-out.
- **F13 (governance repair).** Issue the four skipped adjudications (+ the
  never-adjudicated conflict with the 2026-06-26 ruling, PG-33); write the
  missing close report; reconcile the ledger's internal state; obtain a real
  VERIFIER verdict for W6.5; record this register in CURRENT_STATE.
- **F14 (census closures — REQUIRED for F2/F7 to hold).** (a) Fix the
  coverage gate (:418) to source coverage from the v3 asset's substeps/
  resonance map BEFORE retirement executes (PG-27); (b) harmonize
  asset_registry_seed.ts + migration 542 with the post-563 world so no seed
  run can reverse the cutover (PG-28); (c) unify generation labels: count_sql
  for the production asset counts kala_gochara_windows generation='3.0', and
  buildSourceCitation recognizes '3.0' with a truthful v3 citation (PG-29);
  (d) commit versioned flip/rollback tooling for kala_gochara_authority
  (PG-30); (e) make ka_kshetra's load_legacy_crosscheck + the offline
  validators seam-aware, and re-scope the two hardcoded-v1 scripts with an
  explicit documented reason or fix (PG-31 — the ka_kshetra piece lands in
  SAMPŪRTI's territory as a pre-P-G1 lane).

**REVISED F-SEQUENCE (census-aware):** F1 → F14a+F14b → F2 → F3 → F14c+F14d →
F4 → F7. Executing F2 (retirement) before F14a would re-break serving; F2
without F14b is reversible by the next seed run. PG-31's ka_kshetra fix gates
P-G1 alongside F10's marker.

## SAMPŪRTI IMPACT STATEMENT

Outbound (them→us): none — verified poll-only hold throughout the audit window.
Inbound (us→them): the withheld marker is the control point; SAMPŪRTI's field
build (whose hazard stage cross-checks `kala_gochara_windows`) would today
consume decade-buckets with false valences — the marker stays unposted until
F1–F4+F7, which is precisely the protection R-COORD-3 was designed to give.
One recorded incident (their conductor's accidental dispatch-script run,
11:49Z) created two phantom build_runs — self-cancelled, tombstoned, verified
harmless.

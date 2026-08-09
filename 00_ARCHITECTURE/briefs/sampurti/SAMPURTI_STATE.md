---
artifact: SAMPURTI_STATE.md
campaign: SAMPŪRTI — Gap Remediation (G1–G16, PA-0–PA-8, R23–R29)
plan_of_record: 00_ARCHITECTURE/briefs/sampurti/MASTER_PLAN_v1_0.md
version: rolling
status: LIVE
single_writer: CONDUCTOR only (builders/verifiers NEVER touch this file)
branch_model: >
  Integration branch sampurti/integration cut from main @ 1432d7492 (2026-08-10).
  All lane work in worktrees off sampurti/integration; lane PRs -> integration;
  integration -> main only via Gate-Executor packets at wave boundaries.
conductor_session: SAMPURTI-CONDUCTOR-2026-08-10 (first run)
---

# SAMPŪRTI CAMPAIGN LEDGER

CONDUCTOR-HEARTBEAT: 2026-08-10T04:07+05:30 (SAMPURTI-CONDUCTOR-2026-08-10)

## WAVE POSITION

WAVE 0 — IGNITION. Status: ALL 6 LANES DISPATCHED 03:40 IST (background builder
agents, isolated worktrees off sampurti/integration @ 36fa880ae). Conductor is
executing Wave-1 S1 (PA-0 stage I/O map, read-only) while builders run — S1 is
explicitly conductor-permitted and touches no builder files.
Waves 1–4: NOT-STARTED.

## RAILS (immutable, restated for every reader)

R13 no-fitting · R19 L1 sealed · R14 measurement versioning (never overwrite) ·
sweep corpus untouchable (report 606/606 + 16,297/19,323 detector-cited after
each rebuild) · R18 bounded scoring · blind-before-effect (definition committed
before effects computed; CI-checkable by commit order) · R16 every claim
scope-stated + detector-cited · R29 full delegation to NATIVE-PRATINIDHI except
life-event data creation (Abhinandan LEL AWAITING-NATIVE; genuinely ambiguous
LEL resolver rows PARKED-honest, never guessed).

## WAVE 0 LANE TABLE

| Lane | Scope (short) | Branch | Status | Poll deadline (IST) | PARĪKṢAKA | PRATINIDHI |
|---|---|---|---|---|---|---|
| L0a | G16 record repair (CURRENT_STATE:124 + close artifact to main path + 51 census rows + CI citation-resolution upgrade) | sampurti/l0a-record-repair | DISPATCHED 03:35 | 04:35 | — | required |
| L0b | G4a bg_sarvatobhadra_grid root-cause + dispatch | sampurti/l0b-grid | BUILDER-DONE PR#1133 | 04:35 | PARĪKṢAKA IN-FLIGHT 03:47 | n/a |
| L0c | G12e kala_dasha_sandhi_get prod registration + stale "eight" docstrings | sampurti/l0c-dasha-sandhi | PARĪKṢAKA-PASS PR#1132 | 04:35 | PASS 03:58 — registration chain confirmed; 4+ docstrings; census test real; APPROVED | n/a |
| L0d | G13/PA-4 KNOWN_DOMAINS 7→13 migration in bo_sangati/bo_bimba/bo_karanajala (R17 delete local lists) | sampurti/l0d-vocab | BUILDER-DONE PR#1134 | 04:35 | PARĪKṢAKA+PRATINIDHI IN-FLIGHT 03:53 | IN-FLIGHT 03:53 |
| L0e | Pre-rebuild content fixes: G8 KaryatvaMaps ×5 + G10 varga_confirmation + G9 doc-direction reconcile | sampurti/l0e-content | DISPATCHED 03:35 | 05:05 | — | required |
| L0f | G14a L6 LEL→event_class resolver + 64-event backfill classification | sampurti/l0f-resolver | DISPATCHED 03:35 | 05:05 | — | n/a |

Merge order: train on CI-green + PARĪKṢAKA verdict recorded HERE before merge.
ONE gate packet at wave end → main + deploy (content fixes must be deployed
before Wave 1's rebuild).

## WAVE 1 · S1 — PA-0 STAGE I/O MAP (COMPLETE, read-only, conductor, 2026-08-10 03:55 IST)

All detectors cited inline. Code refs are sampurti/integration @ 1069fff77;
live queries ran against production via cloud-sql-proxy:5433.

**Writer wiring mechanism (the S2 target):** `services/ka_kshetra/writer.py`
`plan_substeps` probes the four stage modules for a module-level
`plan_substeps` attribute (writer.py:309–314) and routes foreign substeps via
module-level `handles_substep`/`run_substep` (writer.py:360–370). None of
stage0–3 exposes `plan_substeps` (writer.py:245 says so in prose; grep
confirms zero `def plan_substeps` in stage0/1/2/3 files) → RC1 confirmed at
code level. Plugin-lane substeps are included BEFORE stage4 substeps
(writer.py:243–245). §N.3 idempotency delete runs ONCE in plan_substeps on
the fresh/replanned branch, NEVER per-substep (writer.py module docstring
:20–:23 — the ka_gochara_sweep blood lesson); each stage's own
REPLACE_PRIOR_SQL must therefore move under that same discipline when wired.

**Per-stage I/O (grep detectors, line-cited):**
| Stage | READS | WRITES |
|---|---|---|
| stage0_kinematics | ephemeris_daily (:635) · chart_facts (:677, :686) · bg_transit_rules (:712) | kala_field_kinematics — delete-then-insert (:762, :765) |
| stage1_symbolization | kala_field_kinematics (:185, :198, :215) · kala_field_boundaries (:314–331; hard-requires live conn) | kala_field_primitives (envelope JSONB knots — the "envelopes" store; there is no separate envelopes table) — delete-then-insert (:368, :371) |
| stage2_promise | bodha_cgm_nodes (:327) · bodha_cgm_edges (:338) · bodha_pratijna (:360) · bodha_msr_signals (:397) | kala_field_promise_nodes (:546) · kala_field_promise_edges (:558) · kala_field_routes (:571) — triple delete (:583–585) |
| stage3_clocks | chart_dashas (:400, :414, :428, :509, :518, :1014, :1127) · kala_field_promise_routes (:1163 — S1-F1 DEFECT below) · own outputs re-read (:1096, :1116, :1186) | kala_field_clocks (:842, :848) · kala_field_boundaries (:1068, :1074) — delete-then-insert per system |

**Derived wiring order for S2:** stage0 → stage2 → stage3 → stage1 → existing
stage4+. Rationale: stage1 reads BOTH stage0's kinematics and stage3's
boundaries (the PA-0 probe finding, now line-cited); stage3 reads stage2's
route gains. Cross-check before build: stage4 already reads routes/clocks/
boundaries/kinematics (stage4_field.py:802, :832, :864, :930) and primitives
(per stage1 module docstring: "stage 4 can consume every" envelope), so all
four stage lanes belong before every stage4 substep — exactly where the
writer's plugin mechanism already puts them.

**S1-F1 DEFECT (live-verified):** `kala_field_promise_routes` is defined in
NO migration (repo-wide SQL grep: zero matches) and does NOT exist in
production (detector: pg_class relname LIKE 'kala_field%' query, 03:55 IST —
absent from list). Yet stage3_clocks.py:1163 SELECTs route_gain,
suppressed_by from it. `kala_field_routes` DOES carry exactly route_gain +
suppressed_by (information_schema query, 03:58 IST) → high-confidence naming
defect; S2's stage3 lane must repoint to kala_field_routes (verify semantics
at build time), else stage3 crashes on first real run.

**PA-0 audit answer (live-verified, 03:55 IST, chart 482012f1):**
kinematics=0 · primitives=0 · routes=0 · clocks=0 · boundaries=0. ALL of
stages 0–3 share the never-run fate — the wiring gap is the single root
cause for all five empty lead tables. (kala_field_promise_nodes/edges also
written only by stage2, so presumed 0 as well — S2 builder to confirm.)

## G9 DISPUTES QUEUE (for Wave 3 mini-cycles)

(empty — L0e populates)

## L0f PARKED-AMBIGUOUS LEL ROWS (await native's memory — never guessed)

(empty — L0f populates)

## DECISIONS LOG (PRATINIDHI rulings with written rationale)

(none yet)

## GATE LOG (integration → main packets, deploy evidence, production==main)

(none yet)

## DEBTS / PARKS (cause VERIFIED live or it is a defect)

(none yet)

## NEXT-ACTION

Conductor: poll Wave 0 lanes at their deadlines (04:35 / 05:05 IST 2026-08-10);
on each lane completion dispatch PARĪKṢAKA (opus, fresh) and record verdict here
BEFORE merge; L0a/L0d/L0e additionally need NATIVE-PRATINIDHI end-to-end pass.
Then merge train → Wave 0 gate packet → main + deploy → Wave 1 S1 (PA-0 stage
I/O map). If this conductor dies: resume per prompt — adopt live lanes from this
table, salvage (commit+push) any dead builder worktree, never re-dispatch merged
work.

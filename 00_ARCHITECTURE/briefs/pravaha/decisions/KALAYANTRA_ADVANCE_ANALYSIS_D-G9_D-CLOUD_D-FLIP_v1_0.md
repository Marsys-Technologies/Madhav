---
artifact: KALAYANTRA_ADVANCE_ANALYSIS_D-G9_D-CLOUD_D-FLIP
version: "1.0"
status: DRAFT TEMPLATE — narrative/control only; decides nothing; every "measured" slot is EMPTY and stays empty until the named receipt exists
date: 2026-10-18
item: ADVANCE-ANALYSIS
control_json: KALAYANTRA_ADVANCE_ANALYSIS_D-G9_D-CLOUD_D-FLIP_v1_0.json (same folder; the machine-readable twin of Parts 3–5)
scope: (a) the D-G9 disposition template for OD-1, OD-2, OD-4, OD-5, OD-6, OD-7, OD-10; (b) the D-CLOUD and D-FLIP evidence checklists. Nothing else. No code, migration, writer, orchestrator, L0–L2 or generated output is touched. No personal data is stated (horizon dates are cited by contract line, not restated).
authority_order: root CLAUDE.md §I/§N → plan v3.0 §B/§C → this analysis. Where this file and a cited source disagree, the source wins.
---

# Advance analysis — D-G9 dispositions, D-CLOUD and D-FLIP checklists

## 0. How to use this file

The three decisions are conditional approvals (A4 D-29): the cockpit publishes `ky decide <D> --as steward --delegated --outcome approved|refused` **only when the named evidence exists** (`/Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl` records `PRE-D-G9-v2`, `PRE-D-CLOUD`, `PRE-D-FLIP`; plan v3.0 lines 141, 145, 147). Outcomes `deferred` and `insufficient_evidence` leave the decision open and never become terminal by time passing (`KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md:171`). This file does not add a rule to those conditions; it turns each one into a row that can be filled and read.

**Row grammar.** Every row has: *evidence* (exact field or receipt) · *producer* (step/receipt that makes it) · *pass rule* (a comparison that reads PASS, FAIL or NULL) · **measured** (`⟦ ⟧`, empty). A row reads **NULL** while its measured slot is empty or its producer has no accepted receipt — never PASS (CLAUDE.md §N.7.6, §N.8). A row that cannot read FAIL is not a row.

**Citations.** `repo:` paths are relative to the repository root at this head. `ext:` paths are outside the repository (read-only context, not part of the tree): `FBS` = `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/decisions/FINAL_BUILD_SCOPE_v1_0.md` (the `OD-*` table is FBS lines 242–252; FB clauses are cited by number), `EP` = `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVALUATION_PROTOCOL_v2_3.md`, `W4` = `/Users/Dev/kalayantra/run/WAVE4_COMPLETION_PATH.md`. FBS is not in this repository's tree; J-4a's item brief still points at that external path (`plan_model.json:19039`).

Abbreviations: `PM` = `00_ARCHITECTURE/control/kalayantra/plan_model.json` · `MBC` = `00_ARCHITECTURE/briefs/pravaha/decisions/MEASURING_BUILD_CONTRACT_v1_0.md` · `SUR` = `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md` · `CHARTER` = `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md` · `PLAN` = `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v3_0.md` · `GK` = `platform/python-sidecar/services/gochara_kernel/` · `FL` = `00_ARCHITECTURE/briefs/kalayantra/fleet/`.

## 1. The J-3d readback — the four places a value can be read from

D-G9 depends on J-3d only (`PM:19016` item `D-G9`, `depends_on: ["J-3d"]`; `PM:18922` item `J-3d`). J-3d's five steps are `readback_accepted`, `golden_capture`, `report_written`, `teardown`, `absence_proof_accepted`; each is closed only by a canonical whole-file receipt `/Users/Dev/kalayantra/run/reviews/steps/J-3d.<step>.json` of the exact form `{"evidence_sha256","item":"J-3d","operation_id","request_id","review_job","step","verdict":"MET"}` (`PM:18922`+`step_evidence`), and the item by `/Users/Dev/kalayantra/run/ops/receipts/J-3d.absence.json` ≥ 200 bytes (`PM:18922` `detector`).

| Source id | What it is | Field address used below | Where it comes from |
|---|---|---|---|
| **RB-SQL** | The one read-only statement J-3d runs through the executor's `readback_sql` kind; tab-separated `section, row_json` rows | `RB-SQL.binding`, `.manifest` (`manifest_id, status, input_generation_vector, lo, hi`), `.sealed.n`, `.published.n`, `.contact`, `.record`, `.window` (`event_class, path_id, rule_version, lo, hi`) | `repo:FL/sql/mb3-capture-read.sql:1-48`; run by `repo:FL/readback_sql.sh` (one SELECT/WITH, read-only); reassembled offline by `repo:GK/measuring_capture_reassemble.py:1-12` (`SECTIONS` line 20) |
| **RB-GOLDEN** | The golden bundle MB-3.4 | `horizon_basis.json`, `digests.json` (`binding`, `informational.input_vector`, `informational.horizon`), `stretch_sink.jsonl`, `records.jsonl`, `windows.jsonl`, `contacts.jsonl`, `MANIFEST.sha256` | `MBC:84`; `repo:00_ARCHITECTURE/briefs/pravaha/measurement/J3_MEASURING_PREBUILD_v1_0.md:61-70`; step `golden_capture` |
| **RB-REPORT** | The report JSON `ky.measuring_report_draft/1`, numbers 1–14 of MB-7 | `numbers["n"].data…`, `refusals`, `status`, `independent_acceptance` | `repo:GK/measuring_delivery.py:53-104` (`build_report`), `:106-` (`report_refusals`); `MBC:110-130`; step `report_written`; owned artifact `00_ARCHITECTURE/briefs/pravaha/measurement/MEASURING_BUILD_REPORT_v1_0.md` (`PM:18922` `brief.owns`; written by J-3d, absent from this tree today) |
| **RB-VIEW** | The independent acceptance view `MeasuringBuildView` and its refusal list (MB-6) | `sink_counts{omission,invented,anomaly,unresolved,near_miss}`, `run_verdict`, `horizon_basis`, refusal names | `repo:GK/measuring_report.py:230-249` (class), `:436-449` (`_sink_refusals`), `:709-740` (`read_measuring_view`); `MBC:105-108` |

(I) INTERPRETATION I-1. The J-3d readback statement is `FL/sql/mb3-capture-read.sql` (the only repo statement named in the capture reassembler and its test, `repo:platform/python-sidecar/tests/l3/kala_db/test_j3_measuring_capture.py:368`). Alternative: a different reviewed statement is installed under `run/ops/sql/` at J-3d; then every `RB-SQL` address below is read from that statement's same-named sections, and a missing section is a FAIL, not a zero (`measuring_capture_reassemble.py:7-8`).

**Two conventions, never mixed** (`MBC:99, 111`): **UTC-HO** = build horizon, UTC half-open (`RB-REPORT.numbers["4"]`); **IST-INC** = scored horizon, IST calendar dates both ends inclusive, 1998-01-01 … 2026-04-17 = **10,334** days (`numbers["5"]`; `repo:platform/python-sidecar/services/gochara_eval/registry.py:19-21`; `EP:61`). Every share below is a fraction (0.0261 = 2.61 %), and every OD rule reads the **IST-INC** grid unless it says otherwise (`FBS FB-48, FB-50`; `MBC:118`).

## 2. Part A — D-G9 gate G9-0 and the core question

### 2.1 G9-0 — "the accepted readback is recorded" (must be all PASS before any OD row is read)

PRE-D-G9-v2: *approved when J-3d's accepted measuring-build readback is recorded AND OD-1, OD-2 and each applicable OD-4/5/6/7/10 is dispositioned from that readback with its evidence … otherwise insufficient_evidence with the missing binding named.* SUR G5 (`SUR:45`): *D-G9 per MEASURING_BUILD_CONTRACT_v1_0 from J-3d's readback (never before it).*

| Row | Evidence | Producer | Pass rule | Measured |
|---|---|---|---|---|
| G9-0.1 | Five step receipts + item detector | J-3d steps (`PM:18922`) | all five `…/reviews/steps/J-3d.<step>.json` match the canonical form with `verdict:"MET"`, and `ops/receipts/J-3d.absence.json` ≥ 200 bytes | ⟦ ⟧ |
| G9-0.2 | Report `refusals` | RB-REPORT (`measuring_delivery.py:102`) | `refusals == []` (no `report_number_missing:n`, `report_convention_mixed`, `report_ratio_mismatch`, `substep_plan_incomplete`, `golden_commit_not_recorded`, `teardown_not_executed`, `acceptance_not_independently_reviewed`, …) | ⟦ ⟧ |
| G9-0.3 | MB-6 refusal list | RB-VIEW (`MBC:107`) | empty; in particular `sink_counts.omission == 0` AND `.invented == 0` AND `.anomaly == 0` (else `certifier_omissions_present` / `_invented_` / `_anomalies_present`, `measuring_report.py:439-449`). `sink_counts.unresolved` and `.near_miss` are reported numbers, never refusals (`MBC:106` (k)) | ⟦ ⟧ |
| G9-0.4 | Run verdict | RB-REPORT `numbers["2"].data` (raw MB-4.7 states) | `run_state=completed`, `asset_state=complete`, `disposition=build`, `throughput_state=lit`, `inventory_classes=26`, `completed_classes=26`, and `last_substep_index == planned_substeps == 298` (`measuring_report.py:304-321`; `measuring_delivery.py` `report_refusals`) | ⟦ ⟧ |
| G9-0.5 | Unsealed, unpublished, bound | RB-SQL | `binding` = the canonical chart and generation `5.0`; `sealed.n == 0`; `published.n == 0`; `manifest.status == "candidate"` (`MBC:106` (h)) | ⟦ ⟧ |
| G9-0.6 | Scope statement verbatim | RB-REPORT `numbers["13"].data.cannot_establish` | equals `CANNOT_ESTABLISH` (`measuring_delivery.py:20-24`; `MBC:102`) | ⟦ ⟧ |
| G9-0.7 | Golden committed before teardown | `numbers["11"].data.golden_commit` | 40-hex commit recorded in the sitting log (`MBC:84`; `report_refusals` `golden_commit_not_recorded`) | ⟦ ⟧ |

Any row not PASS ⇒ D-G9 outcome **`insufficient_evidence`**, missing binding = that row id. (I-2 below: this template never emits `refused` or `deferred`.)

### 2.2 Q-G9-0 — the question D-G9 itself asks: what does `5.0` answer after 2026-04-17?

Plan default: *the derived horizon per MEASURING_BUILD_CONTRACT_v1_0* (`PM:29328-29333`, decision `D-G9`); the item title adds "ruled from the accepted readback (G5)" (`PM:19016`); the contract's rule: horizon is **taken from the readback, never assumed** (PRE-D-G9-v2; `MBC:44-46`). The scored edge is 2026-04-17; "windows after 2026-04-17 are served, not scored; the scoring harness clips there" (`FBS FB-5`, an owner-relayed sentence whose *range* Ruling 13 approved, not the sentence — `FBS` OD-3's neighbour). W4 step 24: ADHIKARIN rules "what 5.0 answers after 2026-04-17 from the accepted measuring horizon_basis, including the derived future horizon and scored-vs-served labeling" (`W4:229-235`).

| Row | Evidence (field) | Pass rule | Measured |
|---|---|---|---|
| Q0.1 | `RB-GOLDEN.horizon_basis.json` : `schema`, `rule`, `basis`, `horizon[0..1]`, `consumed_rows_digest`, `rows_total` | `schema == "horizon_basis/1"`; `rule ∈ {"ruling7+ruling13","ruled_scope+birth_centenary"}` (`GK/horizon.py:15-19, 167`; accepted set `measuring_report.py:337`); `basis ∈ {first_dated_event, build_date, ruled_horizon}`; `consumed_rows_digest` = sha256 of the canonical JSON of `consumed_rows` (`measuring_report.py:357-359`) | ⟦ ⟧ |
| Q0.2 | Re-derivation | `RB-VIEW` reports no `horizon_mismatch` / `horizon_basis_invalid:*` / `horizon_basis_digest_mismatch` / `horizon_start_in_future` (`measuring_report.py:322-375`); for `basis=ruled_horizon` the bundle must carry `rows_total==0`, `chosen==null`, `birth_row==null`, empty readings (`:361-371`) | ⟦ ⟧ |
| Q0.3 | Three-way horizon equality | `RB-SQL.manifest.lo/hi` (UTC) == `horizon_basis.horizon` == marker horizon == the pair stated in `MBC` MB-1.1 (`MBC:30`) (`MBC:106` (b)) | ⟦ ⟧ |
| Q0.4 | Scored grid | `RB-REPORT.numbers["5"].data`: `convention=="ist_inclusive"`, `horizon==["1998-01-01","2026-04-17"]`, `horizon_days==10334` (`measuring_delivery.py` `report_refusals`) | ⟦ ⟧ |
| Q0.5 | Scored-edge pin in the manifest | `RB-SQL.manifest.input_generation_vector.scored_until` (`repo:GK/serving_reader.py:62, 220-232`) | **Not a pass condition.** Read as `⟦instant | null⟧`; null carries `scored_until_not_pinned` (`serving_reader.py:59`) | ⟦ ⟧ |
| Q0.6 | Drift line | `lel_drift` report line count (`MBC:46`; `numbers["10"].data.observed`) | recorded; never a gate for a test slice | ⟦ ⟧ |

**Disposition rule (mechanical).** G9-0 all PASS **and** Q0.1–Q0.4 all PASS ⇒ **`ANSWER_DERIVED_HORIZON`**: `5.0` answers the half-open horizon `Q0.3` reads, in UTC at midnight, with the day count `numbers["4"].data.horizon_days` reads; windows with `lo ≥` the scored edge are labelled *served, not scored*, windows with `hi ≤` the edge *scored*, windows crossing it *straddles the scored edge* (the labels the reader already uses, `serving_reader.py:235-242`). The value is copied from `Q0.3`, not from this file. Any of Q0.1–Q0.4 FAIL/NULL ⇒ `insufficient_evidence`, binding = the row id. Q0.5 null ⇒ record `scored_until_not_pinned` in the ruling and carry to J-4d (the final build's manifest must pin it); it does not change the disposition.

(I-2) INTERPRETATION. The earlier rehearsal packet offered three ruling variants (A scored-past-only, B full derived horizon, C `5.0` then `5.1`) plus defer (`/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs/X-20261016T141558Z-rehearse-j6dec/D-G9_PACKET.md:15-22`). This template implements only the plan-model default (variant B in that packet's wording) because PRE-D-G9-v2 and `PM:29328` fix the default and no readback field can choose A or C. Choosing A or C, or `refused`/`deferred`, needs a reasoned ruling of its own and is outside the template. Alternative: encode all variants — rejected, because the readback cannot discriminate between them (N.7.6).

## 3. Part B — the OD disposition rows

**Closed vocabulary** (every OD row ends in exactly one): `DEFAULT_RETAINED` · `NOT_APPLICABLE` · `BOUND_TO_D-FLIP` · `READBACK_INCONSISTENT` (⇒ G9-0 fails) · `OUT_OF_TEMPLATE` (a departure from the default is proposed ⇒ that OD needs its own ruling; D-G9 ⇒ `insufficient_evidence` naming the OD). `UNFILLED` is the state of an empty slot and is not a disposition.

(I-3) INTERPRETATION. "Dispositioned from that readback with its evidence" (PRE-D-G9-v2) is read as: *the default ruling stays, or does not apply, and the readback value that makes it so is stored beside it* — not "the readback decides". Basis: W4 step 38 (`W4:353-355`): "Take unresolved OD decisions from actual evidence … retain `all_null_candidate/1`, eight-class-only karakatva and named seal refusal for unresolved stretches until an effective ruling changes them. Do not quietly enable numerical ranking, extend kārakas, or call vacuous endpoints pass." Alternative: let the readback pick a non-default option — rejected, no OD has a readback-computable threshold for a non-default option (OD-1/6 cannot be measured on this build at all, see below).

Retained open (not dispositioned here, per `W4:353`): OD-3, OD-8, OD-9, OD-11 (`FBS:244, 249, 250, 252`).

### OD-1 — the final build's result policy (numbers on or off)

- **Question.** `all_null_candidate/1` (windows carry NULL scores) or `window_qualification/1` (numbers on) for the final build (`FBS:242`, FB-53; `MBC:156` OO-4).
- **Readback fields.** (a) `RB-SQL.manifest.input_generation_vector.result_policy` (assembled at `GK/input_vector.py:209`, default `result_policy.py:19-22`; also `RB-GOLDEN.digests.json:informational.input_vector`). (b) `RB-REPORT.numbers["13"].data.cannot_establish` (contains "no scoring, endpoints, retrodiction or 3.0 comparison").
- **Honest limit.** The measuring build runs `all_null_candidate/1`, so every score is NULL and the scorer cannot read it (`MBC:101`, MB-5.4). The readback therefore records the policy stamp; it cannot answer whether numbers should be on.
- **Rule.** Let *x* = (a). *x* ≠ `all_null_candidate/1` ⇒ `READBACK_INCONSISTENT`. *x* = `all_null_candidate/1` AND (b) = `CANNOT_ESTABLISH` ⇒ **`DEFAULT_RETAINED`**: the final-rules candidate and the final build keep `all_null_candidate/1` (the sealer requires it, `GK/seal_flow.py:92`); endpoints are reported *vacuous under policy*, never green (`W4:355`; `PM:27216`). A proposal to switch ⇒ `OUT_OF_TEMPLATE`; its missing bindings are FB-53 alternative 2's gate list: SETTLED-1, the AM-10 re-pin, S1-REQ-EPHEMERIS, the ND-ORB-ADMISSION / ND-ORB-SCALE / combustion rulings, G1–G5 closed, the owner's D5 (`FBS` FB-53).
- **Measured:** `x = ⟦ ⟧` · `(b) = ⟦ ⟧` · **disposition = ⟦ ⟧**

### OD-2 — serving path and switch behaviour

- **Question.** Reader or projection, the migration relaxing 1236, rollback, what a question dated before the horizon start returns, how near-misses and "served, not scored" windows are shown (`FBS:243`, FB-54). FBS §11 point 6: OD-2 is decided before the switch and does not block the seal (`FBS:205`).
- **Readback fields.** (a) `RB-SQL.manifest.lo` and `RB-SQL.window[*].lo` (earliest stored window start). (b) `RB-SQL.manifest.input_generation_vector.scored_until` and `RB-SQL.window[*].lo/hi`. (c) `RB-SQL.sealed.n`, `RB-SQL.published.n`.
- **Rules (three independent sub-dispositions).**
  - **2.1 Before-start questions.** *m* = min over `window[*].lo`, *lo* = `manifest.lo`. *m* < *lo* ⇒ `READBACK_INCONSISTENT`. Otherwise no stored row precedes the horizon start ⇒ **`DEFAULT_RETAINED`**: a question dated before *lo* returns a **named refusal**, never a silent empty (`FBS` FB-54(d)).
  - **2.2 "Served, not scored" labelling.** *e* = `scored_until`. *e* null ⇒ `NOT_APPLICABLE` here, with the reason `scored_until_not_pinned` carried to J-4d (the final build must pin it). *e* non-null ⇒ record the three counts (`hi ≤ e` scored · `lo ≥ e` served-not-scored · otherwise straddles) beside the disposition **`DEFAULT_RETAINED`** (labels per `serving_reader.py:235-242`).
  - **2.3 Mechanism (reader, 1236 replacement, flip and rollback, near-miss display).** Not measurable on a test slice (`MBC:102`: "nothing about sealing, publication, serving, 1236, rollback"). ⇒ **`BOUND_TO_D-FLIP`**, with the missing bindings named: J-6a (reader), J-6m (constraint), J-6r (rehearsal), see Part D rows F-6…F-10.
- **Measured:** `m = ⟦ ⟧` · `lo = ⟦ ⟧` · `e = ⟦ ⟧` · counts `⟦ ⟧` · **2.1 = ⟦ ⟧ · 2.2 = ⟦ ⟧ · 2.3 = ⟦ ⟧**

### OD-4 — density decisions: measuring build vs the final-rules candidate

- **Question.** May the density decisions (FB-41 DVI reversion, FB-48 fast-planet status) be taken on the measuring build, or must the final-rules candidate run first? Skipping the candidate means the first served generation knowingly carries an uncorrected DVI / fast-planet policy and is the owner's to accept (`FBS:245`, FB-41, FB-66). W4: "OD-4 is needed only to explicitly skip the candidate; the conservative default is to run it" (`W4:347`).
- **Readback fields.** (a) `RB-REPORT.numbers["9"].data[<class>]["P1"|"P3"|"P4"]` for the eight classes (`EXCLUDED_EIGHT`, `GK/measuring_report.py:32-36`). (b) `RB-REPORT.numbers["5"].data.classes[<c>].admitted_days.P4_with_dvi` and `.P4_without_dvi`, all 26 classes. (c) `numbers["13"].data.cannot_establish`. (d, informational for the 18 H-classes) `numbers["5"].data.classes[<c>].admitted_share.{P3_fast,P3_slow,P3_union,class_union}`.
- **Why the rule below is structural.** On this build every record has `via="base"` (`GK/measuring_delivery.py:build_report` builds `SupportRecord` without `via`; default `"base"`, `measuring_report.py:576-581`), and `P4_with_dvi` / `P4_without_dvi` differ only by `dvi` records (`measuring_report.py:_report`). So (b) must be equal everywhere — an equality that proves the DVI guard (FB-41) *cannot be computed* here, not that it is satisfied.
- **Rule.** (a) any non-zero count ⇒ `READBACK_INCONSISTENT` (`MBC:106` (e): `excluded_path_has_rows`). (b) any class with `P4_with_dvi ≠ P4_without_dvi` ⇒ `READBACK_INCONSISTENT`. Otherwise, with no skip proposal recorded ⇒ **`DEFAULT_RETAINED`: run the final-rules candidate (FB-66)**; the 40 % DVI guard and the eight-class density decisions are taken on it (`FBS` FB-41, FB-48; `W4:347`). A skip proposal ⇒ `OUT_OF_TEMPLATE` (needs an explicit acceptance of FB-41's uncorrected-DVI consequence). (d) is stored as the 18-class baseline for the FB-48 decision and the protocol band (0.5 % ≤ class share ≤ 40 % on gain classes, `EP:197-200`; scorer `repo:platform/python-sidecar/services/gochara_eval/metrics.py:217-231`), flagged per class `inside | below | above`; it informs, it does not decide.
- **Measured:** (a) `⟦ ⟧` · (b) `⟦ ⟧` · skip proposed `⟦yes/no⟧` · (d) per class `⟦ ⟧` · **disposition = ⟦ ⟧**

### OD-5 — unresolved stretches

- **Question.** If the measured count of UNRESOLVED stretches over the horizon is non-zero: refine the declared accuracy until they resolve, or record a disclosed, named, digest-bound residual (`FBS:246`, FB-56(b); `MBC:157` OO-5, "counted only"). Default until ruled: **the final seal refuses**.
- **Readback fields.** (a) `RB-VIEW.sink_counts.unresolved` (int; `None` is a FAIL, `measuring_report.py:439-449`). (b) `RB-GOLDEN.stretch_sink.jsonl`: the records with `kind=="unresolved"` counted by `reason ∈ {clearance_below_min_approach, no_crossing_unproved, extension_unsettled}` (`MBC:59-62`). (c) `RB-VIEW.sink_counts.{omission,invented,anomaly}` (must be 0 — G9-0.3). (d) the 60-second sentence in `RB-REPORT.numbers["8"].data.limit` (`measuring_delivery.py:25-26`): a recount that finds nothing is not "complete".
- **Rule.** (a) = 0 ⇒ **`NOT_APPLICABLE`** (evidence: the zero, plus (d)). (a) > 0 ⇒ **`DEFAULT_RETAINED`: final seal refuses**, with the per-reason counts of (b) attached; the sum of (b) must equal (a) else `READBACK_INCONSISTENT`. Choosing "refine accuracy" (FB-67) or "disclosed residual" ⇒ `OUT_OF_TEMPLATE`.
- **Measured:** (a) `⟦ ⟧` · (b) `⟦ ⟧` · **disposition = ⟦ ⟧**

### OD-6 — karakatva breadth (the eight classes only, or every class with a kāraka)

- **Question.** FB-46 builds the P1 karakatva extension for the eight; OD-6 asks whether it reaches every class with a kāraka (`FBS:247`; `MBC:158` OO-6). The verifier carries the eight only (`FBS:247`).
- **Readback fields.** (a) `numbers["5"].data.classes[<c>].admitted_days.P1_with_karakatva` and `.P1_base`, all 26 classes. (b) `numbers["9"].data[<eight>]["P1"]` (= 0).
- **Why it cannot be measured here.** Karakatva exists only under the final rules (`MBC:83`, MB-3.3: "their P1 — EQUAL only if karakatva stays limited to the eight"); on this build `via` is always `base`, so (a) is equal by construction (`measuring_report.py:576-581`, `_report`).
- **Rule.** Any class with `P1_with_karakatva ≠ P1_base`, or any non-zero (b) ⇒ `READBACK_INCONSISTENT`. Otherwise **`NOT_APPLICABLE`** to this readback; the default — karakatva limited to the eight, no breadth change — is **`DEFAULT_RETAINED`** for the candidate (`W4:355`). A proposal to widen ⇒ `OUT_OF_TEMPLATE`.
- **Measured:** (a) `⟦ ⟧` · (b) `⟦ ⟧` · breadth change proposed `⟦yes/no⟧` · **disposition = ⟦ ⟧**

### OD-7 — K-B (natal-Sun target) on bereavement, a structurally saturated class

- **Question.** K-B adds density to bereavement, which FBS calls structurally saturated; covered by ND-P2 rule 3's delegation, owner not told in decision form (`FBS:248`, FB-45; `repo:00_ARCHITECTURE/briefs/pravaha/reviews/ASTRA_REVIEW_FINAL_BUILD_SCOPE_v1_2.md:170`). STRATEGY open item 4: bereavement "will fail its 2.61 percent budget on the first build" (`00_ARCHITECTURE/briefs/pravaha/run_records/2026-10-06/STRATEGY_OPEN_ITEMS_FOR_OWNER.md:5`).
- **Readback fields.** (a) `RB-REPORT.numbers["14"].data.scored_share` (= `numbers["5"].data.classes.bereavement.admitted_share.class_union`, IST-INC) beside `.budget_share` (0.0261) and `.label` ("structural-saturation finding, not a decision"). (b) `numbers["5"].data.classes.bereavement.admitted_days.kb_only` (must be 0 — no K-B edge exists on today's rules). (c) `numbers["5"].data.classes.bereavement.admitted_share.{P3_fast,P3_slow,P3_union,P4_without_dvi}` for the record.
- **Budget arithmetic** (scorer, not a threshold of this file): adverse burden = admitted days ÷ 10,334; budget = min(1, 3·max(n_c,1)·90 ÷ 10,334): n_c ≤ 1 → 270/10,334 = 2.61 %, n_c = 2 → 5.23 % (`metrics.py:207-216`; `EP:190-193`). `n_c` (held-out events) is not in the readback, so both are recorded.
- **Rule.** (b) ≠ 0 ⇒ `READBACK_INCONSISTENT`. Otherwise **`DEFAULT_RETAINED`** (K-B as ruled, FB-45) in every case; the readback fixes what is *recorded beside it*: `saturation_confirmed = (a > 270/10334)`, `over_n2_budget = (a > 540/10334)`. The K-B density added is **not** measurable here and is carried to the final-rules candidate (`kb_only` days, FB-50(1)). A proposal to withdraw or change K-B ⇒ `OUT_OF_TEMPLATE` (departs from Ruling 12).
- **Measured:** (a) `⟦ ⟧` · (b) `⟦ ⟧` · `saturation_confirmed ⟦ ⟧` · `over_n2_budget ⟦ ⟧` · **disposition = ⟦ ⟧**

### OD-10 — the 40 % gain band on an adverse class, and its denominator

- **Question.** FB-41/FB-50 apply the DVI guard (P4-alone share > 40 % of the **scored** horizon ⇒ DVI member reverts to SUPPORT in the next generation) literally, including to the adverse class `financial_deception`, although the protocol's band is a gain-class criterion (`FBS:251`; `MBC:159` OO-7; `repo:00_ARCHITECTURE/briefs/pravaha/reviews/ASTRA_REVIEW_FINAL_BUILD_SCOPE_v1_2.md:108`). The scorer already separates them: adverse classes are judged on budgets, the band skips `ADVERSE_CLASSES` (`metrics.py:222-223`; `registry.py:37`).
- **Readback fields.** (a) `numbers["5"].data.classes.financial_deception.admitted_share.{P4_without_dvi,class_union}`. (b) the denominator `numbers["5"].data.horizon_days` (= 10,334) and `.convention` (= `ist_inclusive`). (c) `numbers["4"].data.classes.financial_deception.admitted_share.P4_without_dvi` (UTC-HO, **information only, never compared with 0.40**; `FBS` FB-48 last sentence; `MBC:99`).
- **Rule.** (b) ≠ (10,334, `ist_inclusive`) ⇒ `READBACK_INCONSISTENT` (`report_convention_mixed`). *p* = (a) `P4_without_dvi`. Under the literal default reading and the scored denominator: **`DEFAULT_RETAINED`**, with `evidence_bites = (p > 0.40)`. If `p > 0.40` the guard fires on today's rules with no DVI member at all — the choice matters and is flagged `DECISIVE`; if `p ≤ 0.40` the guard is evaluated with DVI only on the final-rules candidate (the share needs DVI members, `FBS` FB-41) and the flag is `NOT_DECISIVE_ON_THIS_BUILD`. Because P4 is one path of the class, `p ≤ class_union`; record `class_union` beside it. A proposal not to apply the band to adverse classes, or a different denominator ⇒ `OUT_OF_TEMPLATE`.
- **Measured:** `p = ⟦ ⟧` · `class_union = ⟦ ⟧` · (b) `⟦ ⟧` · `evidence_bites ⟦ ⟧` · **disposition = ⟦ ⟧**

### 3.9 Roll-up — D-G9 outcome (mechanical)

| Condition | D-G9 outcome |
|---|---|
| G9-0 all PASS; Q0.1–Q0.4 all PASS; OD-1, OD-2 (2.1, 2.2, 2.3) and each of OD-4/5/6/7/10 holds one of `DEFAULT_RETAINED`, `NOT_APPLICABLE`, `BOUND_TO_D-FLIP`; no `READBACK_INCONSISTENT`; no `OUT_OF_TEMPLATE` | `approved` — ruling text: the derived horizon exactly as Q0.3 reads (disposition `ANSWER_DERIVED_HORIZON`) + the table of dispositions with their measured values |
| any G9-0 / Q0 row FAIL or NULL, any `UNFILLED`, any `READBACK_INCONSISTENT` | `insufficient_evidence`, missing binding = first such row id (PRE-D-G9-v2) |
| any `OUT_OF_TEMPLATE` | `insufficient_evidence`, missing binding = "ruling for OD-n" |

`refused` / `deferred` are never produced by this table (I-2).

## 4. Part C — D-CLOUD evidence checklist

**Condition (PRE-D-CLOUD).** *APPROVED WHEN J-4d is done (qualified final-rules candidate with P06b complete), D-G9 approved, and the operation request binds the exact source/image, rules, class set, horizon/cap and operation window: one canonical-chart, candidate-only Cloud Run build.* Plan default: *approved after the measuring build's readback is accepted and phases 6–9 are done* (`PM:29334-29339`); item `D-CLOUD` `PM:19541`, `depends_on: ["J-4d"]`, notes: "approved only after the measuring build's readback is accepted and phases 6–9 are done". SUR G5 (`SUR:45`): after the measuring readback is TRUE and J-4d is qualified. Consumer: J-4e (`PM:19564`, `depends_on: ["D-CLOUD"]`, op `century_dispatch`). Receipt dir for step receipts: `/Users/Dev/kalayantra/run/reviews/steps/`.

| # | Evidence | Producing step / receipt | Pass rule | Measured |
|---|---|---|---|---|
| C-1 | Accepted measuring readback | J-3d (G9-0.1 … G9-0.7) | every G9-0 row PASS | ⟦ ⟧ |
| C-2 | D-G9 effective | governed `ky decide D-G9 … approved`; awaiting file `/Users/Dev/kalayantra/run/awaiting/D-G9.json` (`PM:27099` item `J-4d-n-g9`) | an `approved` event is recorded through the decision controller (`approved`/`refused` are final; `deferred`/`insufficient_evidence` stay open, `CHARTER:171`) | ⟦ ⟧ |
| C-3 | Phase 6 — final-build decisions and upstream release | J-4a step `settled_build_reconciliation` → `reviews/steps/J-4a.settled_build_reconciliation.json`; artifact `/Users/Dev/kalayantra/run/J4A_PREREQUISITE.json` ≥ 200 bytes (`PM:19039`) | receipt `verdict:"MET"` AND file present AND a single settled build reconciled (`PM:19039` tests) | ⟦ ⟧ |
| C-4 | Phase 7 — protected window, grants, verification job configured *disabled* | J-4b steps `packet_oracles_verified`, `configured_disabled_readback` (`PM`, item `J-4b`) | both receipts `MET`; each grant/principal read back through `readback_sql`; a builder-role write of a verification row is refused (read from privileges, not attempted) | ⟦ ⟧ |
| C-5 | Phase 8 — final-rule builder/verifier proofs | J-4c step `p06b_ready`; artifact `/Users/Dev/kalayantra/run/J4C_PROOFS.json` ≥ 200 bytes (`PM`, item `J-4c`) | receipt `MET`; equality proof "unchanged classes byte-identical to the measuring build's golden capture"; non-interference proof "the measuring rules' outputs unchanged" | ⟦ ⟧ |
| C-6 | Phase 9 — final-rules candidate qualified | J-4d steps `p06b_before_final_candidate`, `packet_oracles_verified`, `final_candidate_density_and_cap` (`PM:19443`); detector `pr_merged` PR 3512 | all three receipts `MET`; P06b complete; PR 3512 merged | ⟦ ⟧ |
| C-7 | Density and residual dispositions recorded on the candidate | J-4d step `final_candidate_density_and_cap` (artifact_section) (`FBS` FB-41, FB-48, FB-56, FB-66) | the section records: FB-41 DVI reversion computed by the scorer script, FB-48 per-class decision, unresolved count known (OD-5 carried), near-miss counts real | ⟦ ⟧ |
| C-8 | Cap qualification, "recorded as measured" | same step; J-4d tests (`PM:19443`: "cap qualification figures recorded as measured"); `FBS` FB-58 | measured projected run length ≤ 0.8 × the actual writer cap, and Cloud Run task timeout strictly above the cap (`MBC:88` is the measuring build's own instance of this rule; `W4:363` states it for J-4d). The cap is set in writing from the candidate's measured time, never from the measuring build's lower bound (`FBS` FB-58) | ⟦ ⟧ |
| C-9 | N-G9 bound | J-4d-n-g9 (`PM:27099`) | the decision residual consumes the effective D-G9 and all original dependencies; no packet merge or file existence grants a decision | ⟦ ⟧ |
| C-10 | Request binds source and image | typed request under `/Users/Dev/kalayantra/run/ops/requests/` (`SUR:48`, G8) for op kind `century_dispatch`, `args={classes:"all"}` only (`W4:375-379`) | request carries the exact source commit and image digest of the candidate in C-6; **the same runtime image later runs verification** (`MBC:22` item 9: build and verification share one image) | ⟦ ⟧ |
| C-11 | Request binds rules and class set | same request | rule versions and class set equal the candidate's (C-6/C-7); no rule version outside the candidate's selection | ⟦ ⟧ |
| C-12 | Request binds horizon and cap | same request | horizon equals the `Q0.3` value ruled in D-G9; cap and task timeout equal C-8 | ⟦ ⟧ |
| C-13 | Request binds the operation window | same request; protected-window controls from C-4 | an explicit start/end window is present and lies inside the protected window | ⟦ ⟧ |
| C-14 | One canonical-chart, candidate-only | same request; `RB-SQL`-style readback of `kala_gochara_publication` for the chart and generation; J-3d absence proof (`J-3d.absence.json`) | exactly one chart; no publication row for the target generation, or status `candidate`; the measuring build's test-slice rows are absent (J-3d absence proof accepted) | ⟦ ⟧ |
| C-15 | No implicit capacity or credential expansion | request text | names no new credential, principal or capacity (`W4:371`) | ⟦ ⟧ |

**Rule.** All of C-1 … C-15 PASS ⇒ `approved`. Any NULL/FAIL ⇒ `insufficient_evidence` (or reasoned `deferred`) naming the first such `#`.

**Carried to J-4e, not D-CLOUD conditions** (G8 preconditions the surrogate verifies before writing the request, `SUR:48`; each is a J-4e step with its own receipt `reviews/steps/J-4e.<step>.json`, `PM:19564`): `lease_held` (live lease on campaign-coordination), `backup_restore_verified` (a record of a *restore test*, not a claim), `dry_run` (same-operation receipt ACCEPTED), `pre_acceptance` (PARĪKṢAKA's), one build slot; detector `/Users/Dev/kalayantra/run/ops/receipts/J-4e.dispatch.json` ≥ 200 bytes. (I-4) INTERPRETATION: these gate J-4e, not the authorisation, because PRE-D-CLOUD names none of them. Alternative: add them as D-CLOUD rows — rejected, it would add a condition PRE-D-CLOUD does not state.

## 5. Part D — D-FLIP evidence checklist

**Condition (PRE-D-FLIP).** *APPROVED WHEN J-5q, J-5s and J-6r are done for the exact sealed and independently verified generation and manifest, the evaluation run is recorded (not gated, native 2026-10-07), no A5.7 engineering defect is open, and the serving path and rollback are verified; the flip binds that exact generation/manifest.* Item `D-FLIP` `PM:20020`: `depends_on: ["J-5q","J-5s","J-6r","J-2a-P1L"]`. SUR G6 (`SUR:46`): approved only when ALL are TRUE by independent receipts; any FALSE ⇒ `blocked` on J-6 with the row named. Native direction `NR-KALA-DIRECTION-20261007`: scores are the tuning baseline and never block the flip; an **engineering** defect (a wrong, missing or unverifiable result) still blocks (`PM:20020` notes; `SUR:46`). Consumer: J-6 (`PM:20046`, op `publish_head`, `readback_sql`).

| # | Evidence | Producing step / receipt | Pass rule | Measured |
|---|---|---|---|---|
| F-1 | Exact generation sealed by the separately dispatched verification job | J-5s steps `p06b_before_enablement`, `pre_acceptance`, `dispatched`, `sealed_observed`, `manifest_and_job_bound` (`PM:19754`) | all five receipts `MET`; detector SQL `SELECT p.generation FROM public.kala_gochara_publication p WHERE p.chart_id = <canonical chart> AND p.generation = '5.0' AND public.ka_gochara_generation_is_sealed(p.chart_id, p.generation)` returns a non-empty set; **and** the verdict binds the expected manifest id and the job's run id ("the SQL observation alone is not acceptance", `PM:19754` notes) | ⟦ ⟧ |
| F-2 | Every included grain verified | the verification job's output bound in F-1 `manifest_and_job_bound` | no grain of the manifest lacks a verification row; builder role cannot write verification rows (C-4) | ⟦ ⟧ |
| F-3 | Evaluation run and recorded, as it reads | J-5q: `/Users/Dev/kalayantra/run/J5Q_RESULT.json` ≥ 500 bytes (`PM:19711`); `EVALUATION_RESULT_5_0_v1_0.md` (`W4:415-417`, step 45) | the file exists, is independently accepted by exact digest, and **each endpoint and gate carries `pass | fail | insufficient_evidence | not_evaluable` with its measured value, none relabelled**; the generation's author did not score held-out items; policy-vacuous outcomes are stated as vacuous. A weak score does **not** fail this row; an absent or relabelled one does | ⟦ ⟧ |
| F-4 | No open A5.7 engineering defect | J-5q-a57 step `measured_gate_results` → `/Users/Dev/kalayantra/run/residuals/J-5q-a57.json` (`PM`, item `J-5q-a57`: valence not all favourable, peaks not flat, coverage honest, pre-2020 answered, no fabricated instants) | for every A5.7 gate the recorded result is a measured value or an honest `insufficient_evidence`/`not_evaluable`; **no** gate is classified wrong, missing or unverifiable; the count of open remediation items for A5.7/J-5q is 0 | ⟦ ⟧ |
| F-5 | Retrodiction / candidate gate accepted | J-5q-b54 (`baseline_artifact_accepted`, `retrodiction_accepted`), J-5s-j2 (`candidate_gate_and_retrodiction_accepted`) | receipts `MET`; a baseline is not substituted (`J3_MEASURING_PREBUILD_v1_0.md:35-41`: no 4.1 baseline is fabricated) | ⟦ ⟧ |
| F-6 | Serving reader live, sealed-only, refuses test slices, answers out-of-range and rollback probes | J-6a step `packet_oracles_verified` (`PM:19855`; detector `branch_merged` ref `94b3ee3e…`, PR 3513); SUR G6 | receipt `MET`; "a test-slice generation is refused by the reader"; out-of-range and rollback probes answered; PR 3513 squash commit contained in `origin/main` and deployed | ⟦ ⟧ |
| F-7 | Authority CHECK replacement (1236 refuses a `5.x` authority by design) deployed and verified | J-6m steps `packet_oracles_verified`, `authority_constraint_applied_readback` (`PM:19914`) | receipts `MET`; on the lane DB "the new constraint admits '5.0' only for a sealed generation and still refuses an unsealed one"; post-deploy `migration_readback` shows it applied and the definition read back from `pg_constraint`; `publish_head` enabled in the executor table | ⟦ ⟧ |
| F-8 | Rollback rehearsal passed, previous head retained | J-6r artifact `/Users/Dev/kalayantra/run/J6R_REHEARSAL.json` ≥ 200 bytes (`PM:19982`) | independent exact-digest acceptance; "flip → served response from '5.0' → rollback → served response byte-identical to before the flip"; previous head retained, never deleted; `rollback_head` enabled | ⟦ ⟧ |
| F-9 | P1 derivation ledger merged | J-2a-P1L, detector `branch_merged` `origin/kalayantra/j-2a-p1l` (`PM:19191`) | merged; every stored `period_running_at='false'` P1 record lists its consulted daśā rows (B.3); the registered writer re-reviewed for §N.2 (no commit, no `asset_throughput` write, per-chart delete-then-insert) | ⟦ ⟧ |
| F-10 | Out-of-scope behaviours named (OD-2 carried here) | J-6a / J-6m / J-6r evidence above | the by-name refusal for questions dated before the horizon start and the "served, not scored" marking are demonstrated on the lane reader (`FBS` FB-54(d),(e)); D-G9's sub-dispositions 2.1–2.3 point at F-6…F-8 | ⟦ ⟧ |
| F-11 | Lease live | live lease on campaign-coordination (`SUR:46`) | held at the time of the decision and carried by the J-6 steps `lease_held`, `backup_restore_verified`, `pre_acceptance` (`PM:20046`) | ⟦ ⟧ |
| F-12 | Deployed image and migration set identified in the receipt | the decision receipt / J-6 request (`SUR:46`) | image digest and migration set listed and equal the deployed ones | ⟦ ⟧ |
| F-13 | Flip binds the exact generation and manifest | the decision `--detail` and the J-6 request | `generation`, `manifest_id`, `marker`/input-vector digest in the ruling equal F-1's readback values; nothing else can be flipped by it | ⟦ ⟧ |

**Rule.** All of F-1 … F-13 PASS ⇒ `approved`. Any FALSE/NULL ⇒ `blocked` on J-6 with the row named (`SUR:46`); a row failing for an *engineering* defect ⇒ `deferred` with remediation items named and re-decided once they land (`PM:20020` notes). F-3 is a **recorded-not-gated** row: its pass rule is "recorded honestly", never a score threshold.

**After the flip (not D-FLIP conditions):** J-6 steps `lease_held`, `backup_restore_verified`, `pre_acceptance`, `flip_dispatched`, `authority_observed`; detector SQL joining `kala_gochara_publication` and `kala_gochara_authority` for the generation (`PM:20046`); J-6l `live_response_captured`, `soak_recorded`, `/Users/Dev/kalayantra/run/J6L_LIVE.json` (`PM:20144`); V-J6 (`PLAN:148`).

## 6. Interpretations, limits, change log

| Id | (I) INTERPRETATION | Alternative |
|---|---|---|
| I-1 | The J-3d readback statement is `FL/sql/mb3-capture-read.sql` | another reviewed statement; same section names, missing section = FAIL |
| I-2 | The template implements only the plan-model default for Q-G9-0 and never emits `refused`/`deferred` | encode scored-past-only / `5.0`-then-`5.1` variants — rejected, readback cannot choose |
| I-3 | "Dispositioned from the readback" = default retained, or not applicable, with the readback value stored | readback picks a non-default option — rejected, no computable threshold |
| I-4 | G8 preconditions gate J-4e, not D-CLOUD | add as D-CLOUD rows |
| I-5 | File location: `briefs/pravaha/decisions/`, beside `MEASURING_BUILD_CONTRACT_v1_0.md` (D-G9's spec brief) and `FINAL_BUILD_SCOPE`'s home; control JSON beside it, not under `control/kalayantra/` | `briefs/kalayantra/` or `control/kalayantra/`; the latter holds files the fleet code globs |
| I-6 | For OD-7/OD-10 the "base rate"/"burden" the scorer judges is the readback's `class_union` share (scorer `base_rates` = union of admitted days ÷ `H_DAYS`, `metrics.py:80-88`) | a per-path share |

**Not verified here.** No production, Cloud Run, credential or `gh` access; the J-3d, D-G9, D-CLOUD, D-FLIP receipts and `run/` files named above were *not read* as evidence (they do not yet exist for the real measuring run) — only their declared names and patterns in `PM` are cited. `FBS` and `EP` are read from their external paths, not from this tree. `PM` line numbers are at this head; PLAN v3.0's `PM:` numbers (18948, 19379, 19858) are stale against it (current: `PM:19016`, `19541`, `20020`). The 0.8 × cap factor for the final build is stated at `W4:363` and `MBC:88`, not in `FBS` FB-58. No value in any slot is a measurement; every `⟦ ⟧` is empty.

**Changelog.** 1.0 (2026-10-18) — first draft; ADVANCE-ANALYSIS.

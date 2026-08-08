---
artifact: SHABDA_SHUDDHI_CLOSE
canonical_id: SHABDA_SHUDDHI_CLOSE
version: "1.0"
status: CLOSED-RETROSPECTIVE
created: 2026-08-08
campaign: SHABDA-SHUDDHI (purification of the word)
closed_by: Claude (Sonnet 5), retrospective governance session, 2026-08-08
note: >
  This close is written retrospectively, one day after the campaign's code shipped, and
  it exists ONLY because that governance gap was itself caught. ŚABDA-ŚUDDHI's code
  (PR #1097) merged to main and deployed to production at 2026-08-07T13:10:46Z. The
  campaign then kept working for roughly another hour — running its own Stage R rebuild,
  writing a defect dossier, a debt register, named self-errors, and red-team seeds — but
  that closing narrative was committed ONLY to the shabda-shuddhi/integration branch
  (commit 0e0a02be3), which was never opened as a pull request and never merged into
  main. CURRENT_STATE_v1_0.md was never updated to record the campaign at all. From
  main's perspective — the only perspective that governs per CLAUDE.md §H — the
  campaign's code shipped and the campaign then vanished with no closing record. That is
  the defect this document exists to correct, and it is named explicitly in §5 and
  seeded into §6 as SHIPPED-WITHOUT-CLOSE. This document reconstructs the close honestly
  from three sources: the campaign's own ledger as committed to main
  (SHABDA_SHUDDHI_STATE.md, ending at "PHASE 1 COMPLETE"), the campaign's unmerged
  self-written close narrative (branch shabda-shuddhi/integration, commit 0e0a02be3,
  read via `git show`, never independently verified before now), and a live, read-only
  re-measurement of the production database performed on 2026-08-08.
---

# ŚABDA-ŚUDDHI Campaign — Retrospective Close

## §1 — Mission and what actually shipped

**Mission.** ŚABDA-ŚUDDHI ("purification of the word") was opened 2026-08-07 to execute
four native rulings (R6–R9, ratified 2026-08-07) against the live retrieval/serving
stack:

- **R6 — Promise is a modifier, never a gate.** Five categorical gates were excluding
  results outright on `bodha_pratijna.status`; every class with an N_e prior was to
  compute a hazard field instead, scaling via the Adrsta floor rather than excluding.
- **R7 — One canonical 13-domain vocabulary.** Nine divergent domain-vocabulary variants
  scattered across the codebase were to be retired in favor of a single Python SSoT +
  TS mirror, with `bo_laksana`'s house/yoga/varga maps rebuilt against the full 13
  domains, each mapping row carrying a classical citation (B.3 derivation-ledger
  discipline).
- **R8 — No verdict from zero evidence, platform-wide.** `bodha_pratijna` was to gain an
  honest `no_evidence` status (empty ≠ clean, empty ≠ denied), with every serving
  surface that reads pratijna status updated to honor it.
- **R9 — Rebuild after engine fixes.** Once L1–L5 code landed, the full
  bodha→kala→phala→mimamsa chain was to be rebuilt for the three live charts
  (482012f1, 1c826d5a, cb73cd3d).

**What shipped (PR #1097, merged 2026-08-07T13:10:46Z).** 26 commits, +3,443/−200 lines
across `platform-mcp`, `platform/python-sidecar`, and one migration (545). Lanes V0 and
L1–L5, L7, L8 landed and merged to main; L6 was explicitly deferred (see §2). PARĪKṢAKA
(the campaign's independent verifier role) issued two ACCEPT verdicts against this PR's
content: Stage 1 (39/39 tests, post-remediation) and L7 (6/6 checks, 19/19 mi_darshana
tests).

**The defect dossier.** The campaign's own closing narrative — present only on the
unmerged `shabda-shuddhi/integration` branch (commit `0e0a02be3`) — names **11** fixed
defects (D1–D11): the five categorical gates (R6), the 6→12 domain vocabulary expansion
(R7), the no-verdict-from-zero-evidence fix (R8), a `promise_lift` sign inversion, a flat
`0.5` `dasha_activation_proximity` default, a CGM graha-case mismatch, seven dead
junctions (Python + TypeScript), two legacy-domain-literal sites in serving code, a CI
vocabulary-census gate, a P2 empty-evidence lint, and the four-file serving-layer
`no_evidence` fix. This document reports 11, not a rounder number, because that is what
the ledger actually supports.

## §2 — Per-lane disposition

| Lane | Status | Evidence |
|---|---|---|
| **V0** (canonical vocabulary module) | COMPLETE | `brahmagyan/domain_vocabulary.py` (13 `CANONICAL_DOMAINS`, 19 `DOMAIN_SYNONYMS`) + `platform/src/lib/domain_vocabulary.ts` mirror + `tests/test_domain_vocabulary.py` (18 tests). PARĪKṢAKA ACCEPT 8/8. Commit `c3ef13e3a`. |
| **L1** (bo_laksana domain remap) | COMPLETE | `_BHAVA_DOMAINS` 6→12 explicit + `general` fallback = 13/13 reachable; classical citations (BPHS ch.11, ch.6, ch.30, ch.32, ch.34–39); CR-62 varga gate extended (D7→progeny, D4→residence, D24→education, D12→travel). Commits `2a59931ed`, `8ce882909`. |
| **L2** (bo_pratijna v2.0 engine + `no_evidence` status) | COMPLETE | Migration 545 (`no_evidence` added to `bodha_pratijna` status CHECK, DOWN path documented); `_partition_signal()` maps real valence (benefic/malefic/mixed/neutral, weighted not discarded per R7); `_grade_to_status()` emits `no_evidence` with `grade=NULL` (not a fabricated 0). Commits `d1c3ad223`, `06da154ab`, `035bf40f8`, `753a6e857`/`582d49c42`. |
| **L3** (5 categorical gates → R6 modifier semantics) | COMPLETE | `ka_kshetra._discover_event_classes` and `ka_avadhi._FETCH_PRATIJNA_SQL` gates removed (gates 4/5 of 5); `stage65_insights.ABSENCE_MIN_PROMISE` unit bug fixed (0.60→6.0, was comparing a [0,1] value against a [0,10] threshold). Commit `be86f6c28`. |
| **L4** (numeric fixes) | COMPLETE | `_promise_lift` sign inversion fixed in `ph_nimitta/engine.py`; `ka_yojaka._infer_signal_domain` routed through `canonical_domain()` (gate 1/5); `taranga_service` missing-valence default changed from a fabricated benefic assumption to honest `None`. Commits `998ddd440`, `74aa99a32`, `7f1fd2fd6`. |
| **L5** (7 dead-junction fixes, Python + TS) | COMPLETE | `ka_bhavishya_lekha`, `ka_yojaka` classifier, `ph_phaladesa`, `bo_upaya`/`mi_adhilepa` false clean-bills, `prashna_undertaking`, `query_domain_reading`, `registry_bridge`. **Caught its own regression**: PARĪKṢAKA's first Stage-1 pass REFUTED because `ka_yojaka.py` lines 143 and 157 still retained status gates despite the lane's self-reported COMPLETE; fixed in `048d67bad`, re-verified clean. |
| **L6** (LEL→event_class resolver) | **DEFERRED** | Explicitly parked per the campaign's own declared defaults ("Lane L6 resolver classifies deterministically with audit trail; AMBIGUOUS mappings PARK for native review"). No code written this campaign. Requires native LEL review before it can start. |
| **L7** (serving guards for `no_evidence`) | COMPLETE | 4 files (`mi_darshana.py`, `register_p1_synthesis.ts`, `query_pratijna.ts`, `query_predictive_anchors.ts`). PARĪKṢAKA ACCEPT 6/6 (both a positive case — `no_evidence` gets `grade=None`, not a fabricated 5.0 — and a negative case — non-`no_evidence` rows are unaffected). 7 new + 12 regression tests pass. Commits `65ec5a656`/`19f68ea39`. |
| **L8** (detectors: junction hit-rate, CI vocabulary-census, empty-evidence lint) | COMPLETE (3/3) | `domain_lookup()` telemetry + `test_domain_vocabulary_census.py` CI gate + P2 empty-evidence lint (§N.8 pattern). Commit `805b3b202`. Note: an earlier ledger entry (run-1) had called the lint "deferred"; run-2's ledger calls the same deliverable complete — see §5 for the documentation-quality point this raises. |

All 5 categorical gates named in R6 are confirmed converted. 8 of 9 lanes (V0, L1–L5,
L7, L8) reached COMPLETE with independent PARĪKṢAKA verification on the two lanes that
had one dispatched (Stage 1, L7). L6 is the one lane never started.

## §3 — Before/after metrics

Three columns are reported, each explicitly scoped and dated, because attributing all
improvement to ŚABDA-ŚUDDHI would be false — two later campaigns (**PRATIJÑA-SATYA**,
PR #1098, merged 2026-08-07T17:35:05Z, repaired the pre-existing L0 `bg_ghatana` /
`bg_transit_rules` failures; **SIDDHANTA**, PR #1099, merged 2026-08-07T20:49:32Z plus
further unmerged Phase-3 rebuild work, shipped `bo_pratijna` v3.0 classical
karyatva/significator routing and ran the actual full per-chart rebuild) touched the
same tables afterward.

- **BEFORE** — the campaign's own pre-rebuild baseline, measured against the live DB at
  2026-08-07T12:00Z (run-2), chart 482012f1 unless noted "all charts."
- **CAMPAIGN'S OWN AFTER** — the campaign's self-reported post-rebuild numbers, from its
  unmerged closing narrative (branch `shabda-shuddhi/integration`, commit `0e0a02be3`,
  Phase 3, self-measured ~2026-08-07T13:30Z same day). Never independently re-verified
  before this document, and never merged to main.
- **LIVE-NOW** — independently re-measured by this session, read-only, against the
  production DB (`cloud-sql-proxy` on 127.0.0.1:5433, PID 74982, running continuously
  since 2026-08-05; server `now()` = 2026-08-08 05:36:53 UTC, i.e. this morning).

| Metric | BEFORE (2026-08-07 12:00Z) | CAMPAIGN'S OWN AFTER (2026-08-07 ~13:30Z, self-reported, unmerged) | LIVE-NOW (2026-08-08 05:36 UTC) | Attribution |
|---|---|---|---|---|
| `bodha_msr_signals` domain spread (482012f1) | 6 (career, character, health, relationship, spirituality, wealth) | 12 | **12** — independently re-verified: career, character, education, family, health, progeny, relationship, residence, spirituality, transition, travel, wealth (`domains_affected_array`, distinct-unnest count) | ŚABDA-ŚUDDHI's own L1/L2 rebuild; unchanged since, so this figure is fairly attributed to this campaign. |
| `bodha_pratijna` status distribution (all charts) | 251 denied / 149 conditional / 5 promised (no `no_evidence` status existed) | 228 denied / 162 conditional / 0 promised / 15 no_evidence | **160 denied / 180 conditional / 50 promised / 15 no_evidence** (405 total) | The `no_evidence` count (15) has held steady since the campaign's own rebuild and IS attributable to ŚABDA-ŚUDDHI. The denied/conditional/promised split moved substantially further (promised 0→50, denied 228→160) **after** this campaign closed — chiefly SIDDHANTA's `bo_pratijna` v3.0 (PR #1099), which replaced domain-only matching with per-class classical karyatva routing on top of ŚABDA-ŚUDDHI's v2.0 engine. Not attributable to ŚABDA-ŚUDDHI. |
| — same, 482012f1 only (LIVE-NOW breakdown) | not separately reported | not separately reported | conditional 68 / promised 50 / denied 12 / no_evidence 5 | measured this session |
| `phala_anchors` (482012f1) | 3 rows | 3 rows — **BLOCKED**, not moved (L3–L5 rebuild for this table was blocked by pre-existing L0 `bg_ghatana`/`bg_transit_rules` failures, not caused by and not fixable within this campaign's scope) | **124 rows** | Entirely post-ŚABDA-ŚUDDHI. PRATIJÑA-SATYA (#1098) repaired the two L0 blockers; SIDDHANTA's Phase-3 rebuild populated the table (SIDDHANTA's own ledger records an intermediate 93-row/6-domain snapshot; the further rise to 124 reflects still-later rebuild activity this document did not trace further). None of this belongs to ŚABDA-ŚUDDHI. |
| `kala_bhavishya` (482012f1) | 0 rows | 0 rows — **BLOCKED**, same reason | **100 rows** | Same attribution as above — entirely post-ŚABDA-ŚUDDHI (PRATIJÑA-SATYA L0 repair + SIDDHANTA rebuild). |
| `bodha_contradictions` (482012f1) | 0 rows | 15 rows | **15 rows** | Held steady since the campaign's own L2 Bodha rebuild (this table does not depend on the blocked L0 assets). Fairly attributable to ŚABDA-ŚUDDHI. |

**Read honestly**: of the campaign's own five headline acceptance metrics, ŚABDA-ŚUDDHI
itself actually moved two (domain spread, contradictions) and left two BLOCKED by a
dependency outside its scope (phala_anchors, kala_bhavishya) — those two only moved
after two subsequent campaigns did further work. The `no_evidence` count is a genuine,
durable ŚABDA-ŚUDDHI result. The wider pratijna status redistribution is not this
campaign's result.

## §4 — Debts carried out of the campaign

1. **L6 — LEL→event_class resolver.** DEFERRED, never started. Requires native review of
   ambiguous LEL-entry mappings before any code is written. Still open as of this
   document.
2. **Full three-chart Stage R rebuild (R9).** R9 called for the bodha→kala→phala→mimamsa
   chain to rebuild for all three live charts (482012f1, 1c826d5a, cb73cd3d). The
   campaign's own record shows only 482012f1 progressed, and even that stalled mid-chain
   on the L0 blockers. SIDDHANTA's own ledger (`SIDDHANTA_STATE.md`, Phase 3) records
   "482012f1 rebuilt... others PARKED" — meaning as of SIDDHANTA's own close, 1c826d5a
   and cb73cd3d had still not been rebuilt under the new vocabulary/engine. This remains
   open; not verified further in this document.
3. **Stage S — first skill score (FIRST-SCORE-BECOMES-BASELINE).** The campaign's own
   ledger records this as blocked on the L3–L5 data that was itself blocked; never
   reached within ŚABDA-ŚUDDHI. Status after later campaigns' rebuild work not verified
   here.
4. **Documentation-quality gap inside the ledger itself.** Run-1's ledger entry called
   the empty-evidence lint "deferred, full lint deferred"; run-2's ledger later reports
   the same deliverable "COMPLETE (3/3)" via commit `805b3b202`. Both entries are in the
   same file; the inconsistency was never reconciled in prose. Low-severity, but it is
   exactly the kind of self-contradiction §N.7/§N.8 exist to catch, so it is named here
   rather than smoothed over.
5. **The close itself.** Until this document, no governance-visible closing record
   existed on main. See §5.

## §5 — Honest self-assessment

**What the campaign got right.**

- It targeted a real, structurally significant defect class on explicit native mandate
  (R6–R9) rather than a self-invented scope.
- TDD discipline is visible in the ledger: failing tests committed before fixes across
  L2 and L5 (`d1c3ad223`, `41511d1a4`/`d71690b02`, etc.).
- PARĪKṢAKA caught a real regression, not a rubber stamp: `ka_yojaka.py` lines 143/157
  still held status gates after L5 self-reported COMPLETE; the first Stage-1 pass
  REFUTED on that basis and the campaign fixed it before re-verifying ACCEPT.
- The `no_evidence` handling is genuinely honest by the codebase's own §N.7 standard:
  `grade=NULL`, not a fabricated 0 or 5.0, on both the write side (L2) and every read
  side (L7).
- The campaign named its own debts (L6, the L0 block) instead of hiding them, and named
  its own process errors (see FALSE-BLOCKER-PARK below) instead of quietly correcting
  them off the record.

**What the campaign got wrong — named explicitly, not softened.**

- **SHIPPED-WITHOUT-CLOSE.** This is the primary finding of this document. PR #1097
  merged to production main at 2026-08-07T13:10:46Z. The campaign then produced roughly
  another hour of genuinely good closing work — a Stage R rebuild attempt, an 11-item
  defect dossier, a 5-item debt register, three named self-errors, and six red-team
  seeds — but committed all of it only to the `shabda-shuddhi/integration` branch
  (`0e0a02be3`), which was never opened as a pull request against main and never merged.
  `CURRENT_STATE_v1_0.md` was never updated to record the campaign happened at all. Per
  CLAUDE.md §H, a session does not get to claim close without an emitted and validated
  close artifact; this campaign did not even reach the point of claiming close on
  main — it simply stopped being referenced. That is a defect in its own right, distinct
  from any defect in the code itself.
- **An unverified "blocker" was treated as fact and used to park the whole rebuild.**
  Run-1 issued a PARKED-FINAL disposition citing "no cloud-sql-proxy credentials are
  available in the current execution environment." This was false — the proxy had been
  running continuously since 2026-08-05. It was only caught because run-2 happened to
  try connecting rather than trusting the prior run's claim. The campaign's own ledger
  names this honestly as "FALSE-BLOCKER-PARK," which is to its credit — but the
  underlying pattern (a terminal disposition issued on a premise nobody actually
  checked) is worth stating plainly here as a recurring governance risk, not just a
  one-off self-correction.
- **The scorecard framing oversold the result.** The campaign's own unmerged narrative
  describes the rebuild as "4/7 acceptance metrics PASS," which is accurate as far as it
  goes but reads more like a scorecard than a plain admission that 2 of the campaign's
  own 5 headline before/after metrics (phala_anchors, kala_bhavishya) were never moved
  by this campaign at all — they only changed after two subsequent campaigns did further
  work (§3). A close document should lead with that distinction, not require a reader to
  reconstruct it from a table.
- **No one decided not to merge the closing branch.** There is no record — in the ledger,
  in PR history, or in CURRENT_STATE — of any human or agent explicitly deciding to
  leave `shabda-shuddhi/integration`'s closing commit unmerged. It appears to have simply
  been left behind when the session ended. An absent decision is not the same as a
  considered one, and that gap is itself worth red-teaming (§6).

## §6 — Red-team seeds for the next §M pass

- **vocabulary-dead-junction** — re-check whether any of the nine retired
  domain-vocabulary variants left orphaned call sites outside the seven junctions L5/L8
  fixed.
- **empty-evidence-as-verdict** — re-verify `no_evidence` handling (NULL grade, honest
  statement, `rank_consequence=0.0`) survived SIDDHANTA's `bo_pratijna` v3.0 rewrite,
  which replaced the v2.0 engine this campaign shipped with per-class karyatva routing.
- **crude-gates-sophisticated** — audit whether R6's "modifier never a gate" semantics
  reached every consumer, or whether some downstream reader still treats
  denied/no_evidence as an implicit exclusion filter the five converted gates no longer
  enforce upstream.
- **sign-inversion-at-consumer** — one `promise_lift` sign-inversion bug (L4 Fix 1) was
  found and fixed; a single instance found does not rule out siblings elsewhere in the
  scoring chain.
- **checklist-factual-error** — PARĪKṢAKA's Stage-1 first pass caught a lane
  (`ka_yojaka`) that had self-reported COMPLETE while still holding two live gates, plus
  a cosmetic domain-confirms gap. Audit whether the other lanes' self-reported COMPLETE
  status in this ledger (L1, L4, L8 in particular) were independently re-verified by
  PARĪKṢAKA or simply taken on the builder's word — only Stage 1 and L7 show a recorded
  PARĪKṢAKA pass in the ledger.
- **SHIPPED-WITHOUT-CLOSE** — the defect this document exists to correct. Audit
  `CURRENT_STATE_v1_0.md` and recent campaign briefs for other campaigns whose code
  merged to main but whose closing narrative, if one was ever written, lives only on an
  unmerged branch nobody reconciled back to main.

---

*End of SHABDA_SHUDDHI_CLOSE v1.0 (2026-08-08, retrospective, written one day after
PR #1097 shipped without a merged close). Primary sources: `SHABDA_SHUDDHI_STATE.md`
(as committed to main); `git show 0e0a02be3:.../SHABDA_SHUDDHI_STATE.md` (unmerged
closing narrative, branch `shabda-shuddhi/integration`); `gh pr view 1097/1098/1099`;
live read-only re-measurement of the production DB, 2026-08-08.*

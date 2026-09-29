---
artifact: NATIVE_DECISION_PACKET
canonical_id: NATIVE_DECISION_PACKET
version: "1.0"
status: CURRENT
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
purpose: >
  One page per Pravāha decision: the question, the evidence (paths and predicates), the options,
  the recommendation and its consequence, and the disposition. Sixteen decisions were ruled by the
  native on 2026-09-29 ("Accept all recommendations"; D-SCOPE verbatim) before this packet was
  written — their pages record the ruling verbatim from the campaign event log as the disposition.
  Three (D-SPECS, D-FLIP, D-T2) are not yet due; their pages state the trigger that makes them due.
  No `request` was emitted for an already-decided or not-yet-due decision.
sources: >
  sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md (§7 ruling requests RQ-1…RQ-8, §8 corpus register);
  sealed/FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md (E1–E9); PRAVAHA_CAMPAIGN_PLAN_v1_0.md §6;
  /Users/Dev/pravaha/run/EVENTS.jsonl (ruling text); lane branch l3/gochara-autonomous-wp0-7
  (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md, GOCHARA_RULING_SHEET_v2_0.md, ADHIKARIN_RULINGS.md).
---

# Pravāha — native decision packet v1.0

Disposition summary: **16 ruled 2026-09-29** (D-SCOPE, D-T1, D-41, D-BRIEF, D-E022, D-CLOUD,
D-RQ1…D-RQ8, D-P4, D-PADMIT) · **3 not yet due** (D-SPECS at B3.6, D-FLIP at J2, D-T2 at J2).

---

## D-SCOPE — build scope

- **Question.** Which chart(s) does the campaign build for?
- **Evidence.** Chart 482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty) is the canonical chart
  (`L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md` §1). Chart 1c826d5a holds candidate-only `'4.0'` rows
  (appendix E7: `kala_gochara_publication` — 1c826d5a `'4.0'/candidate`). The sealed v3.0 is
  chart-scoped to 482012f1 (`chart_scope` frontmatter).
- **Options.** (a) both charts; (b) 482012f1 only.
- **Recommendation.** (b) — the doctrine review, the LEL and the retrodiction protocol are all
  single-chart; a second build doubles Cloud Run cost for no validation gain.
- **Consequence.** All builds, benchmarks and retrodiction target 482012f1 only; chart 1c826d5a's
  `'4.0'` candidate rows are dispositioned under A0.1/ADK-0029 (Stream A).
- **Disposition — RULED 2026-09-29, verbatim:** *"going forward when you build the data, only build
  for Abhishek Mohanti, not for Abhinandan Mohanti."* Scope = chart 482012f1 only.

## D-T1 — tracker database credential

- **Question.** May the tracker hold a permanent read-only DB credential so its database detectors
  measure instead of reporting *unmeasured*?
- **Evidence.** `PRAVAHA_EXECUTION_ARCHITECTURE_v1_0.md` §4 ("Database checks without credentials →
  unmeasured until D-T1") and §7 (install procedure). Earned-signal principle §N.8: a detector that
  cannot measure is null, not green.
- **Options.** (a) no credential — DB detectors stay unmeasured; (b) chmod-600 env file with the
  read-only role `amjis_app`, `default_transaction_read_only=on`.
- **Recommendation.** (b) at `~/.config/pravaha/pgenv.sh`, mode 600.
- **Consequence.** Tracker DB detectors (publication rows, authority, windows counts) become live;
  no write capability is granted to anything.
- **Disposition — RULED 2026-09-29:** accepted; credential installed and tracker reinstalled with it.

## D-41 — the `'4.1'` label

- **Question.** What is `'4.1'`, and may it ever be served?
- **Evidence.** Campaign plan §1 (chart-1 `'4.0'` BURNED — flip reversed 2026-09-28; ADK-0027);
  sealed v3.0 §1 (the written `'4.x'` code carries every Tier-0 defect); §N.7 (windows reading
  "favourable" for bereavement/deception must never be served).
- **Options.** (a) fix-and-flip `'4.1'`; (b) `'4.1'` as an engineering proof and geometric baseline
  only, candidate-only, never flipped; the first astrologically sound candidate is `'5.0'`.
- **Recommendation.** (b).
- **Consequence.** A2.5 builds `'4.1'` on Cloud Run as proof + baseline; B4.4 scores it read-only;
  no authority flip references `'4.1'`; the `'4.0'` label stays burned on chart 1.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-BRIEF — countersignature of the sealed doctrine

- **Question.** Is `FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md` (SEALED 2026-09-29, both external
  reviews incorporated) the Gochara final brief?
- **Evidence.** `sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md` (seal record §9 — the native's
  verbatim delegation); `sealed/RECONCILIATION_GOCHARA_ASTRO_v1_0.md` (every finding dispositioned);
  both reviews retained unedited in `sealed/`.
- **Options.** (a) countersign; (b) return for rework.
- **Recommendation.** (a) — both reviewers' accepted amendments are in the text; every unresolved
  item is carried to §7/§8.
- **Consequence.** B3.1's amendment reconciles plan v2.1 and the ruling sheets *against* this text;
  the sealed set is committed on `campaign/pravaha` (B0.2, commit 7c5d83092).
- **Disposition — RULED 2026-09-29:** accepted — countersigned as the Gochara final brief.

## D-E022 — pins re-admission at the #2731 merge

- **Question.** May the pins excluded under E-022 be re-admitted when PR #2731 merges?
- **Evidence.** Lane records on `l3/gochara-autonomous-wp0-7`; MERGE_HYGIENE_12_10c_RUNBOOK
  (A0.4/A1.3 scope, Stream A).
- **Options.** (a) re-admit per runbook at merge; (b) keep excluded.
- **Recommendation.** (a), per the runbook.
- **Consequence.** Unblocks A0.3 (#2731 mergeable, checks green); merge hygiene verified in A1.3.
- **Disposition — RULED 2026-09-29:** accepted, per MERGE_HYGIENE_12_10c_RUNBOOK.

## D-CLOUD — Cloud Run century builds

- **Question.** May century enumeration run as the Cloud Run job for 482012f1?
- **Evidence.** ADK-0028 (local century enumeration PROHIBITED; Cloud Run job
  `brahma-build-pipeline-job` only after #2731 merge+deploy); campaign plan §2 rule 2 and §8
  (memory-risk mitigation: Tier 0-G removes duplicated solves first; streaming payloads).
- **Options.** (a) authorise Cloud Run builds, candidate-only; (b) no century build.
- **Recommendation.** (a) — candidate-only rows, no flip.
- **Consequence.** Gates A2.5 (`'4.1'`) and A5.6 (`'5.0'`); every build writes candidate-only
  publication rows until D-FLIP.
- **Disposition — RULED 2026-09-29:** accepted, candidate-only.

## D-RQ1 — known-zero AV vs unresolved operand (v3.0 §7 RQ-1; M-7/N-22)

- **Question.** Does an observed zero favourable-mark count in a graha's own aṣṭakavarga read as
  doctrinally adverse, distinct from an unresolved operand (`unqualified`)?
- **Evidence.** BPHS ch.70 vv.24–27 (counted in v3.0 §8: `BPHS2:41956-41959` — transit through
  signs with more marks in the graha's own AV is favourable; the obverse is adverse); N8 defect
  (bindu/rekhā polarity undeclared — L1 stores PyJHora benefic "dots"; Santhanam BPHS names the
  benefic mark *rekhā*). Predicate for polarity: `ga_strength_writer.py:1148-1167` vs
  `BPHS2:35666-35684` (appendix E9; v3.0 §1.2 N8).
- **Options.** (a) zero = unqualified (status quo, N-22); (b) observed-zero = adverse, unresolved =
  unqualified, polarity normalised first; M-7 bands kept as a WP8 hypothesis.
- **Recommendation.** (b) — Codex D5/G, Kimi D5 both confirmed.
- **Consequence.** T0-11 declares polarity on the L1 categories before any citation-bearing weight;
  the P5 path distinguishes zero from unresolved.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-RQ2 — M-1 kernel shape (v3.0 §7 RQ-2)

- **Question.** Is the ruled angular kernel `1 − |Δ|/orb` implemented now, and is BPHS ch.26's
  graduated profile studied separately?
- **Evidence.** Defect N1: `step06b_windows_projection.py:209-228` interpolates t_in→t_exact→t_out
  (a time triangle) vs the ruling `engine.py:1090-1120`; coincides only at constant angular speed,
  wrong around stations. BPHS ch.26 graduation counted at `BPHS1:16496-16502` (appendix E9).
- **Options.** (a) keep the time triangle; (b) implement angular now + versioned calibration study
  of the ch.26 profile.
- **Recommendation.** (b) — Codex C2/G, Kimi §3.3.
- **Consequence.** T0-9/A5.4 implements the angular kernel; the ch.26 graduated profile is a
  separately versioned calibration checkpoint, not silent doctrine.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-RQ3 — Moon-relative node results (v3.0 §7 RQ-3; M-3/G-9)

- **Question.** Do the served Phaladīpikā's Moon-relative node results (XXVI.2, XXVI.24) change the
  premise under which the Moon channel and nodes were scoped out of the century λ?
- **Evidence.** v3.0 §8: recount predicate = read PG321/PG331 against `classical_text_chunks`.
  N-14 (no nodal aspect) stands regardless.
- **Options.** (a) premises stand unrecounted; (b) recount PG321/PG331 (B3.3), keep N-14.
- **Recommendation.** (b) — Codex G.
- **Consequence.** B3.3 performs the recount with its predicate; no nodal aspect is authorised.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-RQ4 — mūrti-nirṇaya rule form (v3.0 §7 RQ-4)

- **Question.** Is the nakṣatra-mod-4 mūrti rule form admitted?
- **Evidence.** F-32 count: **0 chunks** in `classical_text_chunks` for the mūrti-nirṇaya rule form
  (v3.0 §8 "zero by predicate"); defect N7 — `ka_moorti_nirnaya/logic.py:81-86` sets
  `verse_cited`/`corpus_verifiable=true` whenever a grade computes (§N.8 earned-signal defect).
- **Options.** (a) admit the coded form; (b) unadmitted, testimony-only; A-1's true-ingress
  requirement stands; the auto `verse_cited` stamp is removed.
- **Recommendation.** (b) — Codex D3/G, Kimi D3.
- **Consequence.** T0-9 removes the auto-flag; mūrti rows are testimony, never weights.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-RQ5 — Sade-Sati testimony shape (v3.0 §7 RQ-5; N-15)

- **Question.** How does Sade-Sati testimony appear under N-15?
- **Evidence.** Appendix E6: `sade_sati: true` on **all 27 classes** in the '4.0' permission union —
  including gain classes; v3.0 §4 (the twins were born in phase 1).
- **Options.** (a) single testimony row; (b) phase-split rows (12th/1st/2nd from the Moon), never
  attached to gain classes.
- **Recommendation.** (b) — Kimi G.
- **Consequence.** N-15 testimony rows are phase-split; gain classes carry no Sade-Sati edge.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-RQ6 — N-17 timing (v3.0 §7 RQ-6)

- **Question.** When is N-17 (peak separation) revisited?
- **Evidence.** Defect N5: the producer still applies `MIN_PEAK_SEPARATION_DAYS`
  (`step06b:417-424`) contrary to N-17's serve-time ruling.
- **Options.** (a) revisit now; (b) revisit only after Tier 0; move the producer's 90-day filter to
  serve time now, as ruled.
- **Recommendation.** (b) — Kimi G, Codex C5.
- **Consequence.** T0-9/A5.4 removes the producer filter; N-17's substance is re-examined only
  after the Tier-0 rebuild, with real peaks to look at.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-RQ7 — Aṣṭottarī applicability (v3.0 §7 RQ-7)

- **Question.** Does Aṣṭottarī daśā carry a vote on this chart?
- **Evidence.** BPHS ch.46 conditions counted at `BPHS2:3256-3262` and `:3593-3596` (appendix E9):
  Rahu in a kendra/trikoṇa from the lagna lord — fails (Rahu is 8th from the lagna lord); day birth
  in kṛṣṇa-pakṣa / night in śukla — fails (day birth in Śukla pakṣa). Both fail ⇒ vote absent.
- **Options.** (a) keep it in the twelve-system vote; (b) vote absent on this chart; confirm the
  pakṣa operand in B3.3.
- **Recommendation.** (b) — Kimi C, Codex D3.
- **Consequence.** The overkill list stands (Aṣṭottarī only where both conditions hold); B3.3
  confirms the pakṣa operand from L1.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-RQ8 — citation hygiene (v3.0 §7 RQ-8)

- **Question.** Two citation corrections: the Venus-vedha ordering discrepancy and the
  "§double-gochara" string.
- **Evidence.** Appendix E9: `KP_Reader/vol5:1330-1337` gives Venus vedha 11→6, 12→3; the served
  Phaladīpikā PG323 śl.8 (counted) gives 12→6, 11→3 — the code matches Phaladīpikā; the KP
  transcription discrepancy is recorded, not silently "fixed". "§double-gochara" names no real
  passage: 11 co-mention chunks read, only PG216 (Phaladīpikā XVII śl.12) is a joint rule (v3.0 §8).
- **Options.** (a) leave both strings; (b) record the KP-vs-Phaladīpikā note in
  `bg_transit_rules.rule_notes`; strike "§double-gochara" for `[P]` + the PG216 precedent.
- **Recommendation.** (b) — Codex D3; §8.
- **Consequence.** The seed keeps the served-text ordering with the discrepancy disclosed; the
  double transit cites its real precedent.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-P4 — double transit admission (v3.0 §2.4 P4)

- **Question.** Is the double transit admitted, and in what form?
- **Evidence.** v3.0 §2.4 P4: modern practice (K.N. Rao) `[P]`; sole primary joint precedent
  Phaladīpikā XVII śl.12 (PG216) `[D]`; v2.0's "same Moon-house" definition replaced; the §4 father
  example is **not** a double transit (v2.0's claim withdrawn — Jupiter in Scorpio does not aspect
  Sagittarius).
- **Options.** (a) admit as `[D]`; (b) admit as `[P]` with `uncited_extension`, redefined as
  Jupiter **and** Saturn both influencing a signature house **or its lord** (occupation or aspect);
  (c) exclude.
- **Recommendation.** (b).
- **Consequence.** P4 enters Tier 1 as `uncited_extension` with this ruling recorded on the rule
  path; tightest overlap = peak.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-PADMIT — the other `[P]` elements (v3.0 §2.4 testimony row)

- **Question.** How do the remaining practice-level elements enter?
- **Evidence.** v3.0 §2.4 "testimony only" row and §8 zero-by-predicate list (node-dispositor
  result-delivery; chandrāṣṭama-as-avoidance; UL/DK transit rule; JP navāṃśa-of-7L; mūrti rule
  form — all 0 chunks by stated predicates).
- **Options.** (a) admit as weights; (b) testimony first (never weights); weight only after
  ablation evidence from the retrodiction harness; (c) exclude entirely.
- **Recommendation.** (b).
- **Consequence.** Node-dispositor, māraka-of-house, Moon-channel practices and friends enter as
  testimony; promotion to weight requires per-mechanism attribution from B5.3/B5.4.
- **Disposition — RULED 2026-09-29:** accepted as recommended.

## D-SPECS — freeze the design specs — **NOT YET DUE**

- **Trigger.** Due when B3.6 is done (specs written B3.2, corpus reads B3.3, coordination B3.4,
  independent reviews B3.5, reconciliation B3.6).
- **Question.** Are `GOCHARA_DESIGN_SPECS_v1_0.md` (relationship record · rule paths P1–P6 ·
  three-field valence · per-instant permission · vedha interval relation · sky-event substrate ·
  solver method + uncertainty · bindu polarity · annual-object identity · registered-writer
  architecture · test oracles) frozen as the J1 contract Stream A builds against?
- **Evidence.** Will be: the specs file, both unedited reviews under `design/reviews/`, and the
  B3.6 reconciliation (accepted / amended / refuted-with-evidence / deferred).
- **Options.** Freeze / return for rework (loop B3.5→B3.6).
- **Recommendation.** To be written with B3.6; campaign plan §6's standing recommendation is yes
  once the review loop closes.
- **Consequence.** J1 unblocks Phase 5 (A5.x, B5.x); A's migrations implement the frozen schema.

## D-FLIP — flip to `'5.0'` — **NOT YET DUE**

- **Trigger.** Due at J2 (`'5.0'` gated and retrodicted: A5.7 gates green, B5.4 report).
- **Question.** Does authority for 482012f1 move from `'3.0'` to `'5.0'`?
- **Evidence.** Will be: A5.7 gate evidence and `RETRODICTION_REPORT_5_0_v1_0.md` vs the `'3.0'`
  (B4.3) and `'4.1'` (B4.4) baselines, on the pre-declared protocol (B4.2).
- **Options.** Flip + soak trigger #0 / hold.
- **Recommendation.** Flip only if the gates pass and retrodiction beats `'3.0'` (campaign plan §6).
- **Consequence.** A6.1 flip + soak; A6.2 retires the century writer; B6.2 hands calibration to L5.

## D-T2 — Tier 2 admissions — **NOT YET DUE**

- **Trigger.** Due at J2, path by path, with B6.1 doctrine in hand.
- **Question.** Which Tier 2 paths are admitted: P9 Tājaka annual · P8 Jaimini · P11
  transit-to-transit · P12 star-limb/sign-third/saptaśalākā · P7 eclipses/stations · varga objects ·
  SBC school-tagged grid · navatārā/day-quality extensions?
- **Evidence.** Will be: B6.1 per-path doctrine (each path reviewed and ruled) plus the B3.3 corpus
  reads (Tājaka activation rule; Phaladīpikā XXVI.25–29; eclipses XXVI.26–29).
- **Options.** Per path: admit `[D]` / admit `[P]` as `uncited_extension` / testimony / exclude.
- **Recommendation.** Path by path at J2; A6.3 builds only what is admitted.
- **Consequence.** Phase 6 Tier 2 infrastructure scope.

---

*End of packet. Rulings quoted from `/Users/Dev/pravaha/run/EVENTS.jsonl` decide-events of
2026-09-29. Every figure herein traces to `sealed/FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md` (E1–E9)
or v3.0 §8's counted corpus register; no figure is asserted without its predicate.*

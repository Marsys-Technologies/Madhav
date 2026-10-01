---
artifact: DECISION_SHEET_L3
layer: L3 Kāla (ka_*)
version: "1.2"
status: "RULED (SS 2026-10-01); items marked (R) are provisional until the J1 independent review"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L3 (decision sheet over the briefs; one pass for Strategic Suvarṇa)
source_branch: "suvarna/land/A-L3-briefs-001 (PR #2835) at 0945da3f3 (facts read here); the SS rulings are recorded in the briefs and INDEX on suvarna/land/A-L3-briefs-001-rulings (3cecf38ab, a fast-forward of the briefs branch); this sheet (suvarna/land/A-L3-decisions-001) is rebased on that tip"
source_files: "00_ARCHITECTURE/briefs/suvarna/layers/L3/assets/INDEX.md (section 9, Q-L3-01..17) and the 18 per-asset briefs in the same directory"
scope: "docs only; no code, registry, migration or database write"
provisional: "every ruling taken from this sheet is provisional until the J1 independent review"
ruled_on: 2026-10-01
ruled_head: "eed194785 (PR #2838) at the time of the ruling"
changelog: "1.2 (2026-10-02): ARGALA OUTCOME consequence for ka_kshetra recorded (TI-L3-38). 1.1 (2026-10-01): SS rulings recorded (section Rulings, a ruling line per item, summary column); citations relabelled under the SS citations rule; Track I list added at the end. 1.0: DRAFT-FOR-RULING."
---

# L3 Kāla decision sheet (for one ruling pass by Strategic Suvarṇa)

## 0 · How to read this sheet

**Structure.** Group A records four items SS has already ruled; they are not re-asked. For each, the sheet records the ruling, the verified facts, what the ruling requires in the code, and the effect, so the ruling can be executed without another round. Group B holds the open questions: the 17 questions of INDEX section 9 (two of them reduced to a residual by the Group A rulings), plus one item (X1) that INDEX section 8 routes to SS but section 9 does not list. Every B item has the same fields: question, facts, recommendation, effect of each possible answer, citation. A summary table closes the sheet.

**Rules SS gave for rulings (applied throughout).** (1) A classical fact needs a `bg_texts` corpus citation (B.3). (2) Where traditions differ, the project's existing L1/engine convention is the authority (CLAUDE.md §N.5) and the alternative is recorded as a named variant. (3) Every ruling is provisional until the J1 independent review.

**Evidence tags.** `[code]` = read in the repository at 0945da3f3 (file:line given). `[db]` = read-only `SELECT` as `suvarna_reader` on 2026-10-01 (queries in the appendix; no write, no credential shown). `[corpus]` = text search of `classical_text_chunks` (the chunk table of the `bg_texts` corpus); the chunk id is given so the passage can be re-found; the corpus is OCR text and a passage cited here was read by me but is not checked against the printed book. Under the SS citations rule (section Rulings) every such hit is labelled `sourced_ocr_unverified` and every passage not found is `unsourced`. `[brief]` = quoted from a brief or INDEX and NOT re-verified here. Where I looked for a citation and did not find one the sheet says `citation: not found in repo, needs bg_texts lookup`, which under the SS citations rule is the state `unsourced`.

**Charts.** Canonical = `482012f1` (native). Abhinandan = `1c826d5a`. Third chart = `cb73cd3d`.

**Two facts that change how several answers read** (found while verifying, not in the briefs):

1. The ranker behind `ka_tulana` has no live caller. `KaTulanaService` / `rank_windows` is referenced only by its own self-test writer, the health probe, migration 849's text and tests; the served `call_priority_ranking` capability ranks `kala_activation` x MSR salience with its own SQL (`platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:516-` and its SQL block) and does not call the Python ranker `[code]` (grep over `.py`, `.ts`, `.tsx`, `.sql`; external callers outside the repo cannot be excluded). A change to the ranker therefore changes no served output today (A-4, Q-L3-10).
2. `kala_convergence` for the canonical chart is empty (cascade, diagnosis I-6), so anything that reads "what the canonical chart has stored" for convergence, obstruction, darshana, bhavishya or activation is answered from the other two charts, or is not answerable `[db]`.

---

## Rulings (SS, 2026-10-01)

SS ruled this sheet on 2026-10-01 (PR #2838, HEAD `eed194785` at the time). **All recommendations are accepted as written except as modified below.** An item that raises or defines a verdict, or changes outputs, is marked **(R)** and is provisional until the J1 independent review. Each item below carries its own "SS ruling" line directly under its heading, and the summary table has a ruling column.

**Modifications to the recommendations.**

| item | what SS ruled beyond or against the recommendation |
|---|---|
| A-1 (R) | Accepted. ONE shared L0 Gandanta module that `ka_vighnakara` reads; canonical width 3°20' each side (one pāda); the 0°48' width is kept ONLY as a named stricter variant, never the default; each width is cited or marked `unsourced`. |
| A-3 (R) | Option R: retire the batch event-class rows. A design REVIEW follows; output change 92,412 -> 43,488 rows per chart; the REVIEW must state which served surfaces read those rows. A Track I item is added (TI-L3-31). |
| Q-L3-05 (R) | SS rules (no external acharya): explicit keyword -> domain map, ambiguity -> `general`. The +/-21 days is ratified as a NAMED PRE-REGISTERED window (decision N-57), on condition that it is declared in the `ka_bhavishya_lekha` brief (done) and never tuned after outcomes are seen. |
| Q-L3-09 (R) | MEAN node (L1/engine convention; TRUE is a named variant); fix the docstring now. Combustion: orbs from L0 only; scope per the L1/engine convention; where the engine defines none, emit an honest null (no invented scope). |
| Q-L3-11 | Yes in principle; the global dispatch comes to SS as a REVIEW when the time comes (not authorised now). |
| Q-L3-12 (R) | N/A by cause `rolling_horizon` with the window declared; it becomes a rule only through `NA_RULE_DECISIONS` with SS approval. |
| Accepted as written | A-2, A-4, Q-L3-01, 02, 03, 04, 06, 07, 08, 10, 13, 14, 15, 16, 17, X1. |

**Citations rule (SS, all layers).** An OCR text-search hit not checked against print is `sourced_ocr_unverified` (a distinct attribution state, neither `sourced` nor `unsourced`). A passage not found is `unsourced`. Only a citation verified at passage level counts toward a PASS on Ldgr. *Applied in this version:* every `[corpus]` passage in this sheet (BPHS, Yavana Jataka, Brihat Samhita, Phaladeepika, Uttara Kalamrita, Hora Sara) is relabelled `sourced_ocr_unverified`; every "not found" item is relabelled `unsourced` (the fire-side Gandanta width, the 0°48' width, the degree conversion of two ghatikas, Rahu and Ketu significations, Mudda / Naisargika / chara_karaka sources, BPHS Ch. 11 house significations, Tithi-Praveśa, the writer's "Muhurta-Chintamani Rikta" and "Phaladeepika ch.2" pointers, and the `reference_karakas` "BPHS Ch.27" label); nothing in this sheet is `sourced`. The relabelled lines carry the state in the "Citation" paragraph of each item and in "What I could not verify".

**Further SS decision, 2026-10-02: ARGALA OUTCOME consequence for L3 (R, provisional until J1).** L1 now emits a canonical `outcome_by_count` of `unobstructed` / `argala_prevails` / `undetermined` (no `obstructed`), and L2's `cancelled_flag` for argala ends. `ka_kshetra` `stage2_promise` is the one real behaviour change: it selects argala edges with `cancelled_flag = FALSE` (`services/ka_kshetra/stage2_promise.py:336-340` `[code]`) and reads no edge outcome, so dropping the flag alone would treat EVERY argala edge as active. It must read the edge's outcome: `unobstructed` and `argala_prevails` = active argala; `undetermined` = its own state that does NOT contribute as active argala until a strength basis exists. Named Track I item: TI-L3-38 (it rebuilds at stage S7 anyway). Also recorded: `ka_kshetra` is exposed to the ephemeris fix (a decorated writer) and waits for G-EPH; its I-10 substep split, PR #2830, is in the merge train, last, rebased over the line-pin test. (The L1 `outcome_by_count` change, G-EPH and PR #2830 are not in this branch and were not read here.)

**Where the rulings are recorded elsewhere.** In the per-asset briefs (section 7, FD-level ruling lines) and in `INDEX.md` (sections 9, 10, 11) on the briefs branch (PR #2835); Track I items TI-L3-26 to TI-L3-38 are listed at the end of this sheet.

---

## GROUP A · Already ruled by SS (recorded; do not re-ask)

### A-1 · `ka_vighnakara` Gandanta window is a defect

**SS ruling (2026-10-01):** (R) Accepted. ONE shared L0 Gandanta module that `ka_vighnakara` reads; canonical width 3°20' each side (one pāda); the 0°48' width is kept ONLY as a named stricter variant, never the default; each width is cited or marked `unsourced` (states in the Citation paragraph). Track I: TI-L3-26.

**Ruling (SS).** The Gandanta window is a defect. The junction is water-to-fire: the last 3°20' of Cancer, Scorpio and Pisces AND the first 3°20' of Leo, Sagittarius and Aries. The writer must read one engine/L0 definition; if none exists, create it with a corpus citation. (Brief gap `vighnakara-N3`, FD-2; INDEX CF-30(c); part of Q-L3-09.)

**Facts.**
- The writer's ranges are `(90.0, 93.333)`, `(210.0, 213.333)`, `(330.0, 333.333)` (`platform/python-sidecar/pipeline/orchestrator/writers/ka_vighnakara.py:92-96`) `[code]`. Sidereal 90° is 0° Cancer, so these are the FIRST 3°20' of Cancer, Scorpio and Pisces; the comment at `:91` says "last 3°20' of water signs", the docstring (`:745-749`) and the stored `citation` string (`:788`) repeat it, and the `reason` text says "in Gandanta zone at end of {junction_sign}" with `junction_sign = _lon_to_sign(range_start)` (`:774`, `:785-786`). The fire-sign side is not covered at all.
- Stored rows: `kala_obstruction` holds NO `gandanta` row on any chart (Abhinandan 741 rows: combustion 339, malefic_transit 272, panchanga_obstruction 130; third chart 6 rows: combustion 3, malefic_transit 3; canonical 0 rows) `[db]`. So no stored row is wrong today; the defect is in what a rebuild would produce.
- Definition search: no Gandanta definition in `panchang_engine/` and no L0 table; L0 holds only the term and a descriptive dosha entry (`brahmagyan/l0_ontology.py:819`, `l0_reference.py:1028`, `l0_doshas.py:747-766`) `[code]`. The only numeric definition of the rāśi-sandhi zone is L1's: `ga_writers/ga_sensitive_degree_writer.py:194-224` — `GANDANTA_ARC = 30.0 / 9.0` (3°20'), water signs {Cancer, Scorpio, Pisces}, fire signs {Leo, Sagittarius, Aries}, `check_gandanta(sign_num, degree_in_sign)` firing on the last arc of a water sign OR the first arc of a fire sign, with `GANDANTA_CITATION` naming "BPHS / Sarvartha Chintamani" (no chunk or verse); tested at `ga_writers/__tests__/test_ga_sensitive_degree.py:100-106` `[code]`. It is a private function inside an L1 writer, not an engine/L0 definition.
- Other widths already in the repo (named variants): `ga_writers/ga_nakshatra_compute.py:20-21,74-108` — junctions 0°/120°/240°, orb 48' (0°48'), used by `ga_nakshatra_emitters.emit_gandanta_flags`; `bodha_writers/nakshatra_semantic_emitter.py:68-103` — 0.8° on pada 4 / pada 1 `[code]`. So L1/L2 already disagree among themselves on the width; the ruling picks the 3°20' L1 definition for L3.
- Writer's stored citation says "Phaladeepika ch.2" (`:788`); the corpus index of Phaladeepika lists GANDANTA at "XII (4)" (chunk `phaladeepika_pg0422_c01`), not chapter 2; the body passage was not found by text search `[corpus]`. State: `unsourced` (not corroborated).

**What the ruling requires.** (1) Move `GANDANTA_ARC`, the two sign sets and `check_gandanta` to one shared home with a corpus citation (below). Recommended home: a small L0 vocabulary-style module under `platform/python-sidecar/brahmagyan/` (precedent: `domain_vocabulary.py`, `graha_vocabulary.py`, `verification_vocab.py`), imported by both `ga_sensitive_degree_writer.py` and `ka_vighnakara.py`; an engine home in `panchang_engine/` would also satisfy the ruling, SS's call. (2) `ka_vighnakara._check_gandanta` derives `sign_num = int(lon // 30)` and `deg = lon % 30` from the Moon's sidereal longitude and calls it; the `reason` text is built from the returned `gandanta_zone` (`end_of_Cancer` / `start_of_Leo`), never from a literal. (3) Failing-first tests (from the brief): Moon at 118.0° fires; 91.0° does not; 358.0° fires; 1.0° fires; mutation restoring the old ranges fails.

**Effect.**
- Output: which `gandanta` rows exist. Stored rows today: none, so the first rebuild with the fix is the first time any fires. If peak dates are uncorrelated with the Moon's longitude, the detector fires on about 5.6% of evaluations (zones total 20° of 360°) against 2.8% for the current ranges (10° of 360°); this is arithmetic on an assumption, not measured on data.
- Rebuild: `ka_vighnakara` (planned wave 4 rebuild; canonical table is empty anyway) and then its readers `ka_kala_darshana`, `ka_bhavishya_lekha`, `ph_muhurta`, `ph_pratikara`. One rebuild serves A-1, A-2, X1 and the Q-L3-09 residual; no separate run `[brief]`.
- Side effect: moving the function out of `ga_sensitive_degree_writer.py` changes that L1 writer's source, so its code digest changes once (a delta-skip re-run, no output change) `[brief: the same mechanism is named for graha_sancara FD-2]`. Flag to the L1 owner.
- Rows that used a gandanta override (0.22) in `kala_darshana.effective_score` follow the rebuild.

**Citation (for the shared module).** `[corpus]` BPHS (Santhanam trans.) chunk `bphs_pg0111_c01`, translator's note on the premature-death yogas: "The last Navamsas of Cancer, of Scorpio and of Pisces are called as Gandanta" (water-sign side, one navamsa = 3°20'). BPHS Ch. 92 "Remedies from birth in Gandanta" (`bphs_pg1018_c01`, `bphs_pg1019_c01`): three kinds — Tithi, Nakshatra (last two ghatikas of Revati / Ashlesha / Jyeshtha and first two of Ashwini / Magha / Moola) and Lagna Gandanta (last half ghatika of Pisces / Cancer / Scorpio and first half ghatika of Aries / Leo / Sagittarius); the text measures in ghatikas, not degrees. Uttara Kalamrita (`uttara_kalamrita_pg0176_c02`, `uttara_kalamrita_pg0177_c01`): "The last degrees of Aslesha, Jyeshtha and Revati, and the first degrees of Magha, Mula and Asvini are called gandanta"; they sit at the junction of two signs. The first-navamsa-of-the-fire-sign half is the symmetric reading and is supported by BPHS Ch. 92 (first ghatikas of Aries/Leo/Sagittarius, Ashwini/Magha/Moola); the exact width 3°20' on the fire side is a convention, not stated by these passages. Named variants to record: 0°48' (`ga_nakshatra_compute.py`), two ghatikas of a nakshatra (about 0°27' by arithmetic on 13°20'/60, my derivation, not stated by the text). The writer's "Sarvartha Chintamani" pointer is not corroborated by a text hit; `hora_sara_pg0057_c02` points to "Sarvartha Chintamani, Ch. 10, s. 26-27" as a secondary reference. **Citation states (SS rule):** every passage above is an OCR text-search hit not checked against print: `sourced_ocr_unverified`. By width: 3°20' water side (last navamsa) `sourced_ocr_unverified` (`bphs_pg0111_c01`); 3°20' fire side `unsourced` (a symmetric convention; BPHS Ch. 92 gives ghatikas, not degrees); 0°48' `unsourced` (no citation in the code or in the corpus search); the two-ghatika reading `sourced_ocr_unverified` as text, its conversion to about 0°27' `unsourced` (my arithmetic); the writer's "Sarvartha Chintamani" and "Phaladeepika ch.2" pointers `unsourced`.

---

### A-2 · Rikta tithis: engine set is correct, writer's set is wrong

**SS ruling (2026-10-01):** (R) Accepted as written. Track I: TI-L3-27.

**Ruling (SS).** The engine's `[4, 9, 14, 19, 24, 29]` is correct; the writer's `(4, 9, 14, 15)` is wrong; the writer must reference the engine set. (Brief gap `vighnakara-N4`, FD-3; INDEX CF-30(b); part of Q-L3-09.)

**Facts.**
- Writer: `if tithi in (4, 9, 14, 15)` (`ka_vighnakara.py:722`); docstrings say "Rikta tithi (4, 9, 14)" (`:9`, `:693`, `:721`) `[code]`.
- Engine: `_TITHI_TYPES` Rikta = `[4, 9, 14, 19, 24, 29]` (`platform/python-sidecar/panchang_engine/rich_topics.py:32-38`), on the engine's 1..30 numbering (shukla 1-15, krishna 16-30; `panchang_engine/types.py:14-17`). The table is module-private, but the public function `compute_tithi_attrs(tithi_id).anga_type` (`rich_topics.py:48-52`) returns it and is already called by `compute_panchang` (`panchang_engine/__init__.py:287`) `[code]`.
- In the engine's numbering tithi 15 is the full-moon day (Purna group); the writer's "15" comes from the day-of-month proxy's "Amavasya" comment (`:721`) and does not apply on the engine path `[code]`.
- Stored rows (Abhinandan; source `panchang_engine` on all 130): tithi 14 = 117, tithi 15 = 6, tithi 4 = 6, tithi 9 = 1; none at 19/24/29 (impossible under the writer's set) `[db]`. Canonical and third chart: no panchanga rows.

**What the ruling requires.** Replace the literal by `compute_tithi_attrs(tithi).anga_type == "Rikta"` (or an engine-exported accessor SS prefers); fix the three docstrings; replace the stored citation string `'Muhurta-Chintamani §Rikta-Tithi'` (`:734`) with the corpus chunk ids below. The day-of-month fallback that produced the "15" is NOT part of this ruling (see X1). Failing-first (from the brief): engine ids 19, 24, 29 fire; id 15 does not.

**Effect.**
- Output: stored-style rows change as follows — the 6 Abhinandan tithi-15 rows would not be produced; krishna-paksha Rikta rows (19/24/29) would appear; how many cannot be counted offline (peak dates of undetected rows are not stored; the engine would have to be re-run).
- Rebuild: same single `ka_vighnakara` rebuild and dependents as A-1. No registry or migration change.
- Consumers ignore unknown keys; no key is added by this ruling.

**Citation.** `[corpus]` Yavana Jataka (Pingree, Harvard Oriental Series), chunk `yavana_jataka_pg0926_c02`, commentary on 25-26: "the fifteen tithis of each paksa are divided into … Nanda 1, 6, 11; Bhadra 2, 7, 12; Jaya 3, 8, 13; Rikta (empty) 4, 9, 14; Purna 5, 10, 15" — per paksha, so on the 1..30 numbering Rikta = 4, 9, 14, 19, 24, 29 and 15 and 30 are Purna. Corroboration: Brihat Samhita (V. Subrahmanya Sastri trans.) `brihat_samhita_pg0764_c01` "Rikta Tithis (4th, 9th, 14th)"; Phaladeepika `phaladeepika_pg0346_c01`/`pg0347_c01` (the five tithi groups). The writer's own cited source (Muhurta-Chintamani) gave no Rikta hit in the corpus text search; that citation is not corroborated by this lane. **Citation states (SS rule):** the Yavana Jataka, Brihat Samhita and Phaladeepika passages `sourced_ocr_unverified`; the writer's "Muhurta-Chintamani Rikta" pointer `unsourced`.

---

### A-3 · `ka_taranga` event-class tautology is a defect (fix design goes to SS as REVIEW)

**SS ruling (2026-10-01):** (R) Option R: retire the batch event-class rows. A design REVIEW follows; output change 92,412 -> 43,488 rows per chart; the REVIEW must state which served surfaces read those rows (this sheet found `query_activation_waveform.ts:100`, which filters by scope; no python reader of the batch rows; the live service and `record_evidence` also use `event_class` scope). Track I: TI-L3-31.

**Ruling (SS).** The event-class tautology is a defect. The fix design is returned to SS as a REVIEW item: the event-class term must vary by class, or be removed and the score documented class-independent. (Brief gap `taranga-N1`, FD-1; part of Q-L3-03.)

**Facts.**
- Batch writer: for each event class `d_contrib = 1.0 if lord and any(d in lord_domains for d in _GRAHA_DOMAINS.get(lord, [])) else 0.1`, where `lord_domains = set(_GRAHA_DOMAINS.get(lord, []))` (`pipeline/orchestrator/writers/ka_taranga.py:222-224`, `:191`): true whenever the lord has any domain (all nine do). The transit term is `max` of convergence scores over ALL domains in the month, not the class's (`:225-226`). Same code in the service kernel (`services/taranga_kernel/kernel.py:224-228`) `[code]`.
- Stored: `kala_taranga` event_class rows = 146,772 across the 3 charts (48,924 each); `dasha_contribution` has ONE distinct value (1.0) on all of them; domain rows (130,464) carry two (0.15, 1.0) `[db]`. Consequence by code reading: within a month the class ordering is set by the promise term only, and promise is time-invariant, so the class ranking is frozen for all 151 years `[code]`; the prior Nirmāṇa analysis states the same (`00_ARCHITECTURE/briefs/nirmana/L3_W2_DECIDE_v1_0.md` §3, `L3_W1_ANALYSIS_BATCH_D.md` F-TARANGA-1/2) `[brief]`.
- A per-class term needs a class → domain map. The writer already reads it: `brahma_event_ontology.domain` (`ka_taranga.py:127-143`); but `kala_convergence` carries only `domain`, no `event_class` column `[db]`, and only six domains have convergence rows (career 3,633; character 14,541; health 8; relationship 3; spirituality 21; wealth 635; NULL 1,656, Abhinandan + third chart) `[db]`. So a per-class transit term can at best equal the class's DOMAIN transit term, and classes sharing a domain would differ only by promise.
- Prior ruling on record (Nirmāṇa W2 §3, migration 670 header `platform/migrations/670_nirmana_l3_w3_integrity_contracts.sql:1328`): SPLIT — keep the domain half, retire the event-class half `[brief]`. The writer still emits both.
- Second writer on the same table: `taranga_service.record_evidence` upserts `scope_kind='event_class'` rows keyed by mechanism ids (`services/taranga_service.py:732-749`); the batch `DELETE ... WHERE chart_id` (`ka_taranga.py:85`) also deletes those `[code]`.

**Fix designs for SS (REVIEW).**
- **Option R (retire the batch event-class rows; recommended).** Stop writing `scope_kind='event_class'` from the batch writer; the live service (`taranga_service.py`) still computes event-class activation on demand, so nothing is lost for serving. Make the batch `DELETE` scoped to the rows the batch writes so `record_evidence` rows survive. Change the same branch in `kernel.py` so batch and service do not diverge.
- **Option F (fix the term).** Per-class dasha term = 1.0 if the class's `brahma_event_ontology.domain` is in the lord's domain set else 0.15 (the domain half's rule); per-class transit term = mean convergence of windows whose `domain` equals the class's domain. Rows are then non-degenerate but a re-expression of the domain half with a class-specific promise term.
- **Option T (remove the term, document).** Drop the tautological dasha term from event-class rows (activation from transit and promise only) and document in the formula note and `L3` docs that event-class activation is class-independent except through the promise term. Rows and count unchanged.

**Recommendation.** Option R. Reason: after repair the event-class half would still be the domain half plus a class-specific, time-invariant promise term, with a transit term that cannot be more class-specific than its domain; the live service already provides event-class activation at any time; and R matches the Nirmāṇa SPLIT verdict the repository already carries. Option F is the choice if SS wants class-level rows served from the table; Option T is the minimum honest change if SS wants the rows kept as they are.

**Effect.**
- R: table per chart 92,412 → 43,488 rows (domain half only; 24 x 1,812). `target_floor` 92,412 would then read as a floor miss until restated (floors are aspirational, CLAUDE.md §N.4: set the floor to the achieved count after the build; a registry floor/count edit is a separate surgical migration, not done by this sheet). Needs production rebuild of `ka_taranga` (REVIEW for SS); `ka_taranga` is outside the canonical-chart rebuild plan's launch set (downstream, stays stale) `[brief]`. Reader: `query_activation_waveform.ts:100` (scope-filtered; no python reader of batch event-class rows found). Integrity conjuncts (d), (e) of migration 670 already assert only the domain half `[brief]`.
- F: row count unchanged (92,412); event-class `dasha_contribution`, `transit_contribution`, `activation` change on all 48,924 rows; same rebuild; kernel and batch both edited.
- T: row count unchanged; `dasha_contribution` removed or constant-flagged on event-class rows; activation changes; same rebuild.
- All options ride the same rebuild as Q-L3-03 residual (ayanamsha pin) and Q-L3-04 (vocabulary).

**Citation.** Not classical (an arithmetic/code defect). citation: n/a.

---

### A-4 · `ka_tulana` rejecting Mode C/D windows is a defect (EVIDENCE section requested by SS)

**SS ruling (2026-10-01):** Accepted as written. Track I: TI-L3-32.

**Ruling (SS).** Rejecting modes C and D is a defect by default: accept every mode `kala_convergence` emits unless the code or a ruling documents why one is excluded. (Brief gap `tulana-N6`; not in INDEX section 9.)

**EVIDENCE E1 — what `ranker.py` does.** `platform/python-sidecar/services/ka_tulana/ranker.py` `[code]`:
- `:61-62` `if window.mode not in {"A", "B"}: raise ValueError(f"unknown mode: ...")` inside `_validate_window` (`:55`), which runs for every window in `rank_windows` (`:288`) and `compare` (`:320-321`). A window with mode C or D is rejected, and in `rank_windows` one such window aborts the whole call.
- `:80-81` rejects a `confidence_label` outside `{high, moderate, speculative}`; that matches the `kala_convergence` CHECK constraint exactly, so it excludes nothing the table can hold.
- The composite (`_composite`, `:218-237`) uses four inputs only: `convergence_score`, `rarity_years`, the confidence label and `peak_date`. `mode` is never read in scoring; the only other places `.mode` appears under `services/ka_tulana/` are the two synthetic self-test windows (`writer.py:38,47`, both mode `"A"`) and the test helper (`tests/l3/test_ka_tulana.py:37`, mode `'A'`). So the restriction is a type guard, not a scoring rule.

**EVIDENCE E2 — which modes `kala_convergence` emits.** `ka_sangam` (the writer of `kala_convergence`) emits four: Mode A (daśā-prior funnel, `services/ka_sangam/engine.py:1048`), Mode B (off-daśā sweep, `:1332`), Mode C (sign-ingress period trigger for SUBSYSTEM predicates, `:1570`, routed at `pipeline/orchestrator/writers/ka_sangam.py:640-655`) and Mode D (SAV-bindhu convergence windows, `:1686`, `ka_sangam.py:721-739`) `[code]`. The table's CHECK allows exactly `A, B, C, D`: `CHECK ((mode = ANY (ARRAY['A','B','C','D'])))` `[db]`. `ka_kala_darshana` already carries a four-value label map (`ka_kala_darshana.py:201-206`) and records that the canonical chart's top-750 intake was 100% Mode C (`:195-198`, also `ka_sangam.py:152-153`) `[code comment]`.

**EVIDENCE E3 — live distinct values (table readable by `suvarna_reader`) `[db]`.**

| chart | A | B | C | D | total |
|---|---:|---:|---:|---:|---:|
| Abhinandan `1c826d5a` | 1,545 | 1,190 | 870 | 14,352 | 17,957 |
| third `cb73cd3d` | 0 | 0 | 0 | 2,540 | 2,540 |
| canonical `482012f1` | 0 | 0 | 0 | 0 | 0 (emptied, I-6) |

Under the current validator the ranker would accept 2,735 of 17,957 (15.2%) Abhinandan windows and none of the third chart's. Every other ranker input is present on C and D rows: `rarity_years` is non-null on all 20,497 rows, labels are within the allowed set, domains are canonical or NULL (NULL on 1,656 D rows; the caller supplies a list). Mean `convergence_score` by mode (both charts pooled): A 0.124, B 0.073, C 0.800, D 0.427.

**EVIDENCE E4 — does any document explain the A/B restriction?** None found. `mode: str  # 'A' or 'B'` was written when `ka_tulana` was created (commit `6ede0a481`, 2026-06-21); Mode C was added to `ka_sangam` on 2026-06-27 (`c9e2d9d3e`) and Mode D on 2026-06-28 (`c04d0521e`), after the ranker; the `:61` guard was added in the large merge `fa9857f00` (2026-09-16) under the docstring "typed S1 contract" with no mode rationale (`git log -S`). A search of the repository's `.md` files for tulana together with mode finds only the Suvarṇa brief itself. The restriction is a stale contract, not a decision.

**EVIDENCE E5 — consequence.** No live caller exists (see section 0, fact 1), so widening the guard changes no served output and no stored data today.

**What the ruling requires.** Accept all four modes: validate `mode` against the same set the table's CHECK allows (preferably one shared constant) or drop the check since `mode` is not a scoring input; keep `mode` as a pass-through field; add a failing-first test with C and D windows (mutation: restore `{"A","B"}` fails).

**Effect.** No change to served output, stored rows or the composite weights. The ranker's code digest changes; `ka_tulana` has no digest spec yet (Q-L3-10). One design consequence to record, not to fix here: `convergence_score` has very different scales by mode (above), so an unmodified cross-mode ranking will be led by Mode C and D windows. That is the behaviour of the native-ratified I-11 composite (`ranker.py:4`, weights 0.40/0.25/0.20/0.15); a mode-aware normalisation would change the ratified composite and needs its own ratification.

**Citation.** Not classical. citation: n/a.

---

## GROUP B · Open questions

### Q-L3-01 — CF-27: constants and favourable defaults in the temporal chain

**SS ruling (2026-10-01):** (R) Accepted as written (option 1 for thresholds and weights; option 2 for stand-ins of uncomputed terms; option 3 follows L2 CF-20). Track I: TI-L3-17.

**Question.** Should the constants and neutral or favourable defaults in the L3 temporal chain be ratified as documented approximations (option 1), replaced by NULL so the consumer's formula defines the neutral input (option 2), or computed from L1 facts (option 3)?

**Facts.**
- Stand-ins in code `[code]` (line numbers as in INDEX CF-27, re-read to within a few lines): `services/ka_temporal/date_resolver.py` half-widths 7/14/5/5 days by signature class and default 5 (`:380-386`); with no convergence peak the "peak" is the midpoint of the matched dasha period and predicted dates carry strengths 0.6 / 1.0 / 0.4 (`:556-559`, `:656-660`); `_proximity_score` returns 0.5 when no peak resolves and defaults `dignity_score` 0.5, `non_affliction` 1.0 (`:674-690`); `ka_yojaka.py:315` `cgm_pagerank.get(primary_graha, 0.5)`, `:235-243` `non_affliction` = `shadbala_norm / max_shadbala` (a strength fraction stored under an affliction name); `ka_vighnakara.py` severities 0.35/0.55/0.50/0.30, `override_score = 0.45 x score`, cuts 0.70/0.40 (`:114`, `:672`); `ka_taranga.py:195,224` non-matching floors 0.15 / 0.1; `ka_kala_darshana.py` label cuts and a NULL-to-0.5 substitution; `ka_bhavishya_lekha.py:454-458` tier cuts 0.70/0.45; `ka_jivana_parva.py:356-405` quality cuts; `services/ka_dasha_kala/eligibility.py` band scores 0.85/0.50/0.20. `ka_tulana` weights are native-ratified (`ranker.py:4`).
- Reach on the canonical chart `[db]` (`kala_activation_predicates`, 50,678 rows): `cgm_centrality_weight` is exactly 0.5 on 36,678 (72.4%); the hook's `dignity_score` is exactly 0.5 on 43,617 (86.1%); `non_affliction` is exactly 1.0 on 389 (0.8%); every row carries both hook keys. Caution: 0.5 is also the legitimate table value for "neutral" dignity (`bodha_writers/formulas.py:61-70`), so the 86.1% over-states the defaulted share; attribution to the L2 satellite constant versus a real neutral grade is not measured. Abhinandan `kala_activation` (336,093 rows): `dasha_activation_proximity_score` is exactly 0.5 on 9,313 (2.8%), 18 distinct values. Canonical `kala_activation` is empty (I-6).
- Project convention for an absent term: drop it and renormalise over the factors present, never zero-fill (the NIRMĀṆA L3-W3 comment block in `call_service_wrappers.ts`, quoting `kala_ritual_resonance`) `[code]`. CLAUDE.md §N.7 item 6: an honest null beats an invented judgment.
- The 0.5 / 1.0 inputs originate partly in the L2 satellite emitters (`dignity_score = 0.50`, `shadbala_norm = 1.0`, `documented_approximation`; 149 satellite chart rows) `[brief: L2 CF-20]`. Whether SS has already ruled L2 CF-20 is not visible in this branch.

**Recommendation.** Split the ruling. Option 1 for thresholds, weights, band cuts and half-widths: they are scale choices, not stand-ins for a missing value; ratify each with a decision id. Option 2 (drop and renormalise) for stand-ins of an uncomputed term: the `cgm` 0.5, the no-peak 0.5, the missing-hook dignity 0.5 and non_affliction 1.0 defaults. Defer option 3 to the L2 CF-20 ruling, because the satellite constants originate in L2 and a split ruling between L2 and L3 would leave the chain inconsistent; if SS has ruled L2 CF-20, apply the same option here.

**Effect.**
- Option 1: no row changes; adds decision ids to a declaration; no rebuild.
- Option 2: changes stored `cgm_centrality_weight` (up to 36,678 canonical predicate rows lose the 0.5), `kala_activation.dasha_activation_proximity_score` where a term was defaulted, and `kala_activation_predicates` hook values. Rebuild order `ka_yojaka` → `ka_kalasutra` → the dasha-anchored part of `ka_vighnakara`; readers `query_temporal_activation.ts`, `register_d8_assess_domain.ts`, `register_d9_judgment.ts`. Needs a production rebuild (REVIEW). `ka_yojaka` is already in the SS wave (wave 2) `[brief]`.
- Option 3: everything in option 2, plus dignity and shadbala read from L1 facts instead of L2 satellite constants; largest output change; depends on L2.

**Citation.** Not classical. citation: n/a.

---

### Q-L3-02 — `ka_avadhi` FD-1: honest provenance for `citations`

**SS ruling (2026-10-01):** (R) Accepted as written; the attribution states follow the citations rule (every system starts `unsourced`; `sourced_ocr_unverified` for a recorded OCR hit; `sourced` only at passage-level verification). Track I: TI-L3-14, TI-L3-34.

**Question.** Is a per-row attribution state plus the L1 `dasha_row_id` acceptable in place of the one generic classical `citations` string, and who supplies verified per-system sources?

**Facts.**
- `ka_avadhi.py:306` writes the same single string `"BPHS ch. Vimshottari-Dasha / Classical dasha lord tables"` on every row `[code]`. Canonical stored rows (1,169): vimshottari 117, ashtottari 104, kalachakra 90, mudda 480, naisargika 70, yogini 308, all with that one string; 1,052 rows (90%) are non-Vimshottari `[db]`.
- The period spine is an L1 row (`chart_dashas`); the brief's design selects its `dasha_row_id` in the two fetch SQLs (`:73`, `:84`) `[brief]`.
- SS ruling at L0 (Q3, `00_ARCHITECTURE/briefs/suvarna/layers/L0/assets/INDEX.md` §9): `classical_tradition` is not accepted as provenance (B.3); explicit state `sourced | unsourced | refuted`; `unsourced` and `refuted` are not a PASS; re-sourcing from `bg_texts` is a Track I research item, spot-checked at the milestone review `[brief]`.

**Recommendation.** Yes. Carry the L1 `dasha_row_id` as the spine source and add a per-row `attribution_state` following the L0 Q3 pattern. Set every system to `unsourced` initially (including Vimshottari), and let the Track I research item upgrade a system to `sourced` only after the candidate passages below are checked; no citation is invented. Who supplies sources: the Track I research item with the milestone spot-check, the same route SS set for L0.

**Effect.**
- (a) Accept: the `citations` array of every `kala_avadhi` row changes (and `quality` if the state lives there); rides the already-planned wave-2 `ka_avadhi` rebuild (one run, with the I-1 / M4 / I-8 fixes); no migration if the state stays inside the array/JSON; moves Ldgr from "no reading" to measured and Carr; consumers pass the field through (`query_dasha_dossier.ts:93`, `kala_temporal.ts`) `[brief]`.
- (b) Decline (keep the generic string): no change; 90% of rows keep a citation that names a system they do not belong to (B.3 gap stays recorded as open).
- (c) Add a dedicated column instead of using the array: as (a) plus a surgical migration.

**Citation (candidates only, not verified as definitional for each period rule).** `[corpus]` BPHS Ch. 46 "Dasas": `bphs_pg0499_c01` (opening of Ch. 46, Vimsottari), `bphs_pg0505_c01` (Ashtottari), `bphs_pg0521_c01` and `bphs_pg0545_c01` (Kalachakra dasa), `bphs_pg0564_c01` ("Yogini Dasa … 8 Yoginis"). Mudda, Naisargika and chara_karaka: citation not found in repo, needs bg_texts lookup (a search for Mudda in the Jyotish texts returned no hit; Naisargika has hits in several texts that were not examined). **Citation states (SS rule):** the BPHS Ch. 46 chunks are OCR hits, `sourced_ocr_unverified` candidates (a system is recorded `sourced` only after passage-level verification); Mudda, Naisargika and chara_karaka `unsourced`.

---

### Q-L3-03 — `ka_taranga` FD-1/FD-2 (residual: pin the Vimshottari read to the canonical ayanamsha)

**SS ruling (2026-10-01):** Accepted as written (the pin). The FD-1 half is ruled at A-3 (option R, (R)). Track I: TI-L3-04, TI-L3-31.

The FD-1 half (event-class tautology) is ruled and recorded at A-3. What remains is FD-2.

**Question.** Should `ka_taranga` read the Vimshottari mahadasha rows at the canonical ayanamsha (`lahiri_chitrapaksha`) only?

**Facts.**
- The read is `... FROM chart_dashas WHERE chart_id = %s AND level_n = 1 AND system_id = 'vimshottari' ORDER BY start_date` with no `ayanamsha_id` filter (`ka_taranga.py:91-97`), and `_lord_for_month` takes the first overlapping row (`:155-159`) `[code]`. `chart_dashas` pools five ayanamshas (13/13/12/12/13 mahadasha rows for the canonical chart) `[db]`.
- For the canonical chart 481 of 1,812 months have more than one candidate lord across ayanamshas; in every one of the 1,812 months the stored `components.dasha_lord` equals the Lahiri lord, on all three charts (0 mismatches) `[db]`.
- `ka_avadhi` and `ka_jivana_parva` already pin `lahiri_chitrapaksha`; registry conjunct (a) of migration 670 already requires the canonical lord `[brief]`.

**Recommendation.** Yes, add `AND ayanamsha_id = 'lahiri_chitrapaksha'`. It removes order dependence and matches the sibling writers, and it changes no stored value on any existing chart.

**Effect.** (a) Yes: no stored `dasha_lord` or dasha term changes on the three charts (verified); the benefit is determinism for other charts and other row orders; rides the A-3 / Q-L3-04 `ka_taranga` rebuild; no extra run. (b) No: the stamped lord stays dependent on row order for charts whose ayanamsha boundaries drift (26.5% of canonical months have competing candidates today).

**Citation.** Not classical (ayanamsha selection is a project convention, CLAUDE.md §B / canonical ayanamsha). citation: n/a.

---

### Q-L3-04 — CF-30: which graha → domain table is canonical?

**SS ruling (2026-10-01):** (R) Accepted as written (one shared table whose values are in `CANONICAL_DOMAINS`; Rahu and Ketu `unsourced` until a passage is found). Track I: TI-L3-15.

**Question.** `ka_avadhi` and `ka_taranga` each hand-write a graha → domain table and they disagree; which table (or which new single source) is canonical?

**Facts.**
- `ka_avadhi._GRAHA_DOMAINS` (`ka_avadhi.py:40-50`: Sun [dharma, career, authority, health] … Ketu [moksha, spirituality, loss, liberation]) versus `services/taranga_kernel/kernel.py:32-42` (Sun [dharma, career] … Ketu [moksha, spirituality]); a third keyword table in `ka_jivana_parva.py:408-418` and a fourth substring table in `ka_bhavishya_lekha.py:471-490` `[code]`.
- The canonical domain vocabulary already exists in L0: `brahmagyan/domain_vocabulary.py` — `CANONICAL_DOMAINS` (13: career, wealth, relationship, progeny, health, education, family, residence, travel, spirituality, character, transition, general), `DOMAIN_SYNONYMS` (e.g. dharma → spirituality, moksha → spirituality, mind → character, children → progeny, creativity → progeny, property → residence, foreign → travel) and `canonical_domain()` `[code]`. It is mirrored on the serve side and tested for agreement.
- Both writers use tokens outside that vocabulary: karma, longevity, technology, commerce, authority, home, disputes, luxury, loss, unusual, liberation, communication have no synonym entry. Measured consequences `[db]`: (i) `kala_taranga` has 24 domain scopes per chart; 11 of them (children, commerce, creativity, dharma, foreign, karma, longevity, mind, moksha, property, technology) are outside the canonical 13 and carry `transit_contribution = 0` and `promise_contribution = 0` in all 1,812 months — their activation is the dasha term alone; that is 19,932 of 43,488 domain rows per chart. (ii) `kala_avadhi`: all 87 Rahu-lord rows on the canonical chart store an EMPTY `activated_pratijna_ids` (Rahu's tokens karma/foreign/technology/unusual match no `bodha_pratijna` domain, whose values in `brahma_event_ontology` are exactly the canonical 13); Ketu matches only through `spirituality`.
- An existing reference table holds a seven-graha significator list: `reference_karakas` (77 rows; `karaka_sun` … `karaka_saturn`, cited "BPHS Ch.27"); no Rahu/Ketu rows `[db]`. Its citation was not checked against the corpus. State of the "BPHS Ch.27" label: `unsourced`.
- No engine/L1 table of graha → domain exists (the INDEX statement holds; search not exhaustive).
- SS rule (2): where no L1/engine convention exists there is no authority to defer to, so a source must be created and cited.

**Recommendation.** One shared graha → domain table, owned in L0 beside `domain_vocabulary.py` (or by `bg_ontology`, SS's call), whose domain values must all be members of `CANONICAL_DOMAINS` (every token passed through `canonical_domain()`), with a source/`attribution_state` per row; delete both local tables and the substring keyword tables' duplicate graha logic. Seed it only from what the corpus supports (seven grahas, below) and mark Rahu and Ketu `unsourced` until a passage is found; do not copy either existing table as authority (neither is cited and both use out-of-vocabulary tokens).

**Effect.**
- (a) New shared canonical table (recommended): `ka_avadhi` `activated_pratijna_ids` / `quality.domains` change (Rahu rows would get a non-empty set only if Rahu maps to a canonical domain, otherwise stay empty and honestly flagged); `ka_taranga` domain scopes fall from 24 to at most 13 (43,488 → 23,556 rows per chart; 11 dead scopes disappear); consumers `query_dasha_dossier.ts`, `query_activation_waveform.ts`. Rebuild: `ka_avadhi` (planned wave 2) and `ka_taranga` (not in the plan's launch set); both are REVIEW items for SS.
- (b) Adopt `ka_avadhi`'s table as is: Rahu stays empty; taranga 11 dead scopes remain unless taranga is aligned; two out-of-vocabulary token sets persist.
- (c) Adopt `ka_taranga`'s kernel table as is: same vocabulary defect.
- (d) Declare each writer's table L3-local with decision ids and keep both: the disagreement and the dead scopes persist; no rebuild.

**Citation.** `[corpus]` BPHS (Santhanam trans.) chunk `bphs_pg0873_c01` (the chunk's own heading reads "Chapter 70 Effects of the Ashtakavarga"): "The matters to be considered from the Sun and other planets are as follows — the Sun: the soul, nature, physical strength, joys and sorrows, father; the Moon: mind, wisdom, joy; Mars: co-borns, strength, qualities, land; Mercury: business dealings, livelihood, friends; Jupiter: nourishment of the body, learning, children, wealth, property; Venus: marriage, enjoyments, conveyance, sexual intercourse with women; Saturn: longevity, source of maintenance, sorrows, danger, losses, death" — seven grahas only. Rahu and Ketu: citation not found in repo, needs bg_texts lookup. (The `reference_karakas` "BPHS Ch.27" label is not corroborated here.) **Citation states (SS rule):** the seven-graha passage `sourced_ocr_unverified`; Rahu and Ketu `unsourced`; the `reference_karakas` "BPHS Ch.27" label `unsourced`.

---

### Q-L3-05 — `ka_bhavishya_lekha` FD-2/FD-3: keyword precedence and ±21 days

**SS ruling (2026-10-01):** (R) SS rules (no external acharya), modifying the recommendation: explicit keyword -> domain map, ambiguity -> `general`; the +/-21 days is ratified as a NAMED PRE-REGISTERED window (decision N-57), on condition that it is declared in the `ka_bhavishya_lekha` brief (done, section 7) and never tuned after outcomes are seen. Track I: TI-L3-06, TI-L3-33.

**Question.** Is the domain keyword precedence a domain ruling for an acharya, and is ±21 days a ratified constant?

**Facts.**
- Domain inference is first-match substring scanning over overlapping lists in listed order: `fourth` appears under education, family and residence; `fifth` under education and progeny; `twelfth` under spirituality, travel and transition; `eighth` under health and transition (`ka_bhavishya_lekha.py:471-504`); no match returns `general` (`:502-504`) `[code]`; `kc.domain` is preferred when present (`:310`, per the brief `[brief]`). A `fourth`-house signal id maps to education because education is listed first.
- The falsifier is a constant: `evaluation_window_days: 21` and the text "Observable within ±21 days of {peak}" for every domain and tier (`:507-537`) `[code]`. No decision id or ratification text for it was found in the repository `[code]`.
- Stored (Abhinandan, 100 rows; canonical table is empty) `[db]`: every row has `window_end - window_start = 896` days, so the ±21-day evaluation window (42 days) is 4.7% of the stored window; domains stored: character 88, career 10, spirituality 2.
- Rows with a recorded outcome or referenced by `phala_anchors` are immutable in this writer (`RuntimeError`, `:393`) `[code]`; whether Abhinandan's rows are referenced is not measured.

**Recommendation.** (1) Precedence: yes, a domain ruling for an acharya (houses carry several significations, so a first-match list encodes an unstated priority). Replace first-match by an explicit signal-type → domain map; an id that matches more than one domain reads `general` (the writer's own honest fallback), with `kc.domain` still preferred. (2) ±21 days: ratify it as a named, pre-registered evaluation window with a decision id, surfaced in `falsifiability.evaluation_window_days` (the key exists), and make the text say it is the peak date ±21 days of a stored 896-day window. Reason: deriving the evaluation window from the stored window would make the claim near-unfalsifiable (a 2.45-year window); the tight window is what makes it testable. If SS prefers a derived window it must pick the derivation.

**Effect.**
- Precedence (a) explicit map + `general` for ambiguity: `domain` of affected rows changes; needs production rebuild (REVIEW); must land BEFORE `ph_nimitta` rebuilds and anchors reference the new ids, because a changed row that carries an outcome or an anchor makes the writer refuse. (b) keep first-match: no change; the ordering stays an undocumented rule.
- ±21 (a) ratify: `falsifiability` JSON gains a decision id and clearer text; same refusal caveat for referenced rows; no scoring change. (b) derive from the stored window: `evaluation_window_days` and both strings change on every row; auto-filed predictions (`ahead_autofile.ts`) evaluate against a different window; rebuild; the refusal caveat applies.

**Citation.** Multi-signification of houses: `[corpus]` BPHS (Santhanam trans.) `bphs_pg0102_c01` lists the house names (Bandhu = relatives, Putra = progeny, Ari, Yuvati = wife, Randhra = longevity, Dharma = religion, Karma = acts/livelihood, Laabha = gains, Vyaya = expenditure) and says "Ch. 11 deals with the houses in this context"; the Ch. 11 passage assigning several significations to the fourth/fifth/twelfth houses: citation not found in repo, needs bg_texts lookup. The ±21-day window is a project choice: citation: n/a. **Citation states (SS rule):** the house-name chunk `sourced_ocr_unverified`; the BPHS Ch. 11 multi-signification passage `unsourced`.

---

### Q-L3-06 — `ka_jivana_parva` FD-2/FD-3: narrow the chapter claim; a distinct no-evidence quality

**SS ruling (2026-10-01):** (R) Accepted as written. Track I: TI-L3-18.

**Question.** Narrow the life-arc chapter claim to what is derived, and add a distinct "no evidence" quality value? (Qualify goes to the Steward; the label changes are SS.)

**Facts.**
- `summary` says "{planet} daśā ({span}): {quality} phase marked by {themes}" where the themes are a fixed three-word list per planet (`_PLANET_THEMES`, `ka_jivana_parva.py:408-418`, `:430-436`), independent of the planet's condition or the span's evidence; `theme_keywords` mixes the quality label into the array (`:421-424`) `[code]`.
- `parva_quality` has five values; `transitional` serves both "no convergence evidence" (`avg_score is None`) and a past span with a low mean (`:356-405`); `round(avg_score, 3) if avg_score else None` turns a computed 0.0 into NULL in the narrative key (`:443`) `[code]`.
- The column has a CHECK on exactly the five values: live constraint `parva_quality IN (building, peak, consolidating, receding, transitional)` `[db]`; origin `platform/supabase/migrations/248_l3_ka_jivana_parva.sql:22` `[code]`. A sixth value needs a CHECK-widening migration.
- Stored canonical rows (100; older generation) `[db]`: building 74 (52 with NULL `avg_effective_score`), consolidating 8, receding 15, transitional 3. The code already writes `transitional` instead of `building` when there is no evidence (`:389-394`, the F-PARVA-3 fix), so a rebuild alone would turn those 52 into `transitional`; and with `kala_convergence` empty for the canonical chart a rebuild before `ka_sangam` re-lands would stamp all 100 rows `transitional` (the order hazard, brief N1/FD-1).

**Recommendation.** Yes to both. (1) Drop the planet-generic themes from the summary and `theme_keywords`, or derive them from the cited L1 condition of the dasha lord (references, not restated values), and word the summary as what it is: a Vimshottari span with a convergence-density quality (CLAUDE.md §N.7 items 1 and 6). (2) Add `no_convergence_evidence` as a sixth `parva_quality` value, keep `transitional` for a real low score, and store a computed 0.0 as 0.0 (`is not None`). Land after FD-1 (refuse a build without convergence input) so the new value is not stamped on all rows.

**Effect.** (a) Both: `theme_keywords`, `narrative.summary`, `parva_quality` vocabulary and the 0.0 key change; one CHECK-widening migration; needs production rebuild (REVIEW); consumers `query_life_arc.ts:158`, `kala_views/story.ts`, `ahead.ts` (consumers that switch on five values would see a sixth; not traced). (b) Narrow the claim only, no new quality: text changes, no migration; `transitional` stays ambiguous. (c) Neither: no change; the planet-generic sentence keeps asserting condition-free themes.

**Citation.** Graha significations as a classical source for any theme list: see Q-L3-04 (`bphs_pg0873_c01`, seven grahas). Per-dasha effect text ("this daśā is marked by …"): citation not found in repo, needs bg_texts lookup. **Citation states (SS rule):** `bphs_pg0873_c01` `sourced_ocr_unverified`; per-dasha effect text `unsourced`.

---

### Q-L3-07 — `ka_kala_darshana` FD-3: text-only correction of `narrative.context`

**SS ruling (2026-10-01):** (R) Accepted as written. Track I: TI-L3-03.

**Question.** Approve the text-only correction of `narrative.context`?

**Facts.**
- `context` is built as `(f"..." f"..." f"orb strength: ..." if orb_strength else f"confidence: ...")` (`ka_kala_darshana.py:219-223`): Python applies the conditional to the whole concatenation, so when `orb_strength` is falsy (NULL or a computed 0.0) the rarity and mode label are dropped and only the confidence text remains `[code]`.
- It does not manifest in stored data: all 750 stored Abhinandan `kala_darshana` contexts contain "orb strength"; in `kala_convergence` no row has a NULL or 0 `orb_strength` on any mode (Abhinandan, third chart) `[db]`. The defect is latent.

**Recommendation.** Approve. It is a text-only correction (parenthesise the conditional; test `orb_strength is not None`), it changes no stored row on present data, and it is safe to ride the next rebuild.

**Effect.** (a) Approve: no stored row changes today (0 of 750 affected); future rows with NULL/0 orb keep rarity and mode in the context; rides the planned `ka_kala_darshana` rebuild; no separate run; served as-is by `query_temporal_view.ts:87` and `now.ts`. (b) Decline: latent defect stays.

**Citation.** Not classical. citation: n/a.

---

### Q-L3-08 — CF-23 and `ka_bhavishya_lekha` FD-4: unread declared edges; serve-time edges; owner of the anchor guard

**SS ruling (2026-10-01):** Accepted as written. Track I: TI-L3-07, TI-L3-08.

**Question.** May a provably unread declared `depends_on` edge be removed? May a service edge mean "needed at serve time"? Which side (L3 or L4) owns the anchor-existence guard?

**Facts.**
- Live `depends_on` `[db]`: `ka_taranga {ka_avadhi, bo_pratijna, ka_sangam, ga_dashas, bg_ghatana}`; `ka_jivana_parva {ka_kala_darshana, ka_dasha_kala, ka_sangam, ka_yojaka, ga_dashas}`; `ka_kala_darshana {ka_sangam, ka_vighnakara, ka_kalasutra}`; `ka_bhavishya_lekha {ka_kala_darshana, ka_vighnakara, ka_sangam, bo_laksana}`; `ka_tulana {ka_sangam, ka_vighnakara, ka_kala_darshana}`.
- Unread in the writer code `[code]` (grep of the writer files): `ka_taranga` never reads `kala_avadhi` (only a docstring/note mention, `ka_taranga.py:25,104`); `ka_jivana_parva` never references `ka_dasha_kala`; `ka_kala_darshana` reads `kala_obstruction` (`:42`) and `kala_convergence` but never `kala_activation`, so the `ka_kalasutra` edge is unread; `ka_bhavishya_lekha` never reads `kala_obstruction`; `ka_tulana`'s three edges are unread (its writer is a synthetic self-test and the ranker takes caller-supplied windows). That is seven edges `[brief]` for the five consumers.
- A declared edge decides build order and blocks a build when the upstream is not lit; `ka_taranga`'s Build.dep_liveness FAIL is the `ka_avadhi` edge, and `ka_tulana` is 0 of 3 lit `[brief]`. No edge-kind vocabulary exists (TG-L3-005) `[brief]`.
- Back-read: `ka_bhavishya_lekha` selects from `phala_anchors` (`:265-277`) `[code]` while `ph_nimitta` already depends on `ka_bhavishya_lekha`, so the reads-match detector reports a cycle and no edge can be added `[brief]`; the writer raises `RuntimeError` when a protected row would change (`:393`) `[code]`.
- Frozen by Nirmāṇa: `ka_tulana` (t2); removing its edges trips the manifest's identity assertion (only `depends_on` does) `[brief]`. The campaign is OFF.

**Recommendation.** (1) Yes, remove the seven provably unread build-time edges in one registry migration with its own DAG review; edges can only be removed so the graph stays acyclic. (2) No: a serve-time dependence is not a `depends_on` edge, because `depends_on` drives build ordering and DEP-ASSERT blocking and would keep a service that reads nothing at build time blocked; record serve-time reads separately (a declaration/detector item) if wanted. (3) Put the anchor-existence guard on the L4 side (an L4 consumer refuses to orphan), so the dependency runs L3 → L4 one way; this is also the direction of the layer model.

**Effect.** (1a) Remove: DAG change; one upstream hash changes once per affected consumer; `ka_taranga` Dep_liveness FAIL disappears; declared dependent counts fall (`ka_avadhi` 1→0, `ka_kalasutra` 2→1, `ka_vighnakara` 5→3, `ka_kala_darshana` 3→2, `ka_dasha_kala` 3→2) `[brief]`; `ka_tulana`'s t2 manifest goes stale (identity assertion); no data row; no rebuild beyond the one-time upstream-hash signal. (1b) Keep: the phantom edges keep blocking and ordering (`ka_kalasutra` before `ka_kala_darshana` is forced by an unread edge). (2a) Serve-time edge allowed: needs an edge-kind vocabulary first or the dep-liveness gate counts it as build-time; the three tulana edges and the jivana → dasha_kala edge stay. (2b) Not allowed: they go with (1a). (3a) L4 owns the guard: `ph_nimitta`/L4 change, `ka_bhavishya_lekha` stops reading `phala_anchors`; the reads-match FAIL clears. (3b) L3 keeps the guard: the back-read and the FAIL stay.

**Citation.** Not classical. citation: n/a.

---

### Q-L3-09 — `ka_vighnakara` FD-2/FD-3/FD-5 (residual: node convention, combustion scope)

**SS ruling (2026-10-01):** (R) Modified: MEAN node (L1/engine convention; TRUE a named variant); fix the docstring now. Combustion: orbs from L0 only; scope per the L1/engine convention; where the engine defines none, emit an honest null (no invented scope); the acharya referral in the recommendation is not taken. Track I: TI-L3-29, TI-L3-30.

Gandanta and Rikta are ruled and recorded at A-1 and A-2. What remains: which node convention is the L3 transit contract, and the combustion scope.

**Question.** (a) Is Rahu's transit position MEAN or TRUE node for L3? (b) Which grahas' combustion at the peak date counts as an obstruction?

**Facts.**
- (a) `ka_vighnakara.py:108-111` `'Rahu': 11  # swe.TRUE_NODE`, used by `malefic_transit` (`:643`) and `papakartari` (`:834`) `[code]`. Engine standard: `panchang_engine/planets.py:6-8,27-36` — MEAN_NODE ("Phase 4B standard", with an assertion against TRUE_NODE). L1 build engine: `pyjhora_adapter/_jhora.py:23-30` pins MEAN for all ayanamshas; L1 stores `RAH_MEAN`/`KET_MEAN` (canonical chart `graha_position` subjects, 45 rows each `[db]`; `brahmagyan/graha_vocabulary.py:43`). L0 `ephemeris_daily` is TRUE-node (`brahmagyan/l0_ephemeris.py:8-17,66`) and SS L0 Q5 declared `bg_ephemeris` as `node: TRUE` with consumers needing MEAN not to read nodes from it `[brief]`; `ka_vighnakara` calls swisseph directly and does not read `bg_ephemeris`. A legacy module `brahmagyan/ganita/l1_positions.py:128` also uses TRUE_NODE (dot-notation-era; whether it is live was not traced).
- (b) Combustion tests only transiting Mars and Saturn (`:894` loop `('Mars', ...), ('Saturn', ...)`) while the module docstring says "any planet within 6° of Sun (from chart_facts natal positions)" `[code]`; the orbs come from L0 `bg_combustion_orbs` (Moon 12, Mars 17, Mercury 14, Jupiter 11, Venus 10, Saturn 15, Rahu/Ketu 9; notes "Nodes combust per some traditions; excluded by others") with a local fallback copy and an 8.0 default (`:101-105`, `:895`) `[db][code]`. Stored: 339 of 741 Abhinandan obstruction rows are combustion (46%) `[db]`. L0 Q15 already ruled one authority for orbs (`bg_combustion_orbs`) `[brief]`.

**Recommendation.** (a) MEAN node, per SS rule (2): the L1/engine convention is MEAN (§N.5), so TRUE is recorded as a named variant (`node: true`, the L0 `bg_ephemeris` declaration) rather than the contract; state the node in the row's `source` (`swisseph/lahiri/mean_node`). (b) Do not change the scope on this lane's authority: correct the docstring to what is coded (tier-independent, no output change) and send the scope question (which grahas' combustion is an obstruction, whether Saturn and Venus count) to the acharya, because the corpus itself records a disagreement. Delete the local orbs copy and the 8.0 default (fail loudly if `bg_combustion_orbs` is empty), following L0 Q15; that item is not output-changing for a populated table.

**Effect.** (a) MEAN: Rahu-based `malefic_transit` and `papakartari` rows change only where the true and mean node fall in different signs at a peak date, i.e. near sign boundaries; the true/mean node offset is of the order of 1-2° in standard ephemeris behaviour (general astronomy, not measured here); not countable offline; rides the single `ka_vighnakara` rebuild of A-1/A-2. TRUE: no change; `ka_vighnakara` stays inconsistent with L1 and the engine. (b) Docstring fix: none; widening to other grahas would add combustion rows (output change; rebuild); orbs-authority fix: none on a populated table.

**Citation.** (a) A classical node doctrine is not at issue; the convention is the project's: citation: n/a (project convention, `panchang_engine/planets.py`). (b) `[corpus]` BPHS (Santhanam commentary) `bphs_pg0099_c01`: table of combustion degrees "Moon, Mars, Mercury, Jupiter, Venus, Saturn 12°, 17°, 14°, 11°, 10°, 15°" (direct) and "Rahu and Ketu should not be treated as combust although they may be longitudinally close to the Sun" (contradicts the Rahu/Ketu 9° rows in `bg_combustion_orbs` and the writer's fallback; the L0 table notes the disagreement); `bphs_pg0420_c01`: Astangata harana "does not affect Venus and Saturn in combustion" (a classical position that Saturn and Venus are exempt in that calculation). **Citation states (SS rule):** both BPHS passages in (b) are `sourced_ocr_unverified`.

---

### Q-L3-10 — CF-26: output-digest specs and the service dispatch plan

**SS ruling (2026-10-01):** Accepted as written. Track I: TI-L3-12.

**Question.** Land I-4/I-5 (digest specs for `ka_vighnakara`, `ka_dasha_kala`, `ka_muhurta_seva`) and extend the same to `ka_graha_sancara` and `ka_tulana` (and `bg_panchanga`, outside L3)? Plan `ka_muhurta_seva` in wave 1 (global, `super_admin`)?

**Facts.**
- Live `asset_output_digest_specs` holds rows for 16 `ka_*` assets and none for `ka_vighnakara` (kind artifact), `ka_dasha_kala`, `ka_muhurta_seva`, `ka_graha_sancara`, `ka_tulana` (kind service) `[db]`.
- I-4/I-5 are PR #2826 (migrations 1212/1213), not merged at the INDEX base; 1213's header names `ka_graha_sancara`, `ka_tulana` and `bg_panchanga` as "same class, not covered here" `[brief]`. Migrations 1212/1213 are not in `platform/migrations` at this branch head or at the fetched `origin/main` listing `[code]`.
- `ka_tulana` self-test detail `{"n": 2, "top": "t_a", "test": "tulana_rank_order"}`, healthy, last self-test 2026-08-13 `[db]`; a determinism check (two runs byte-identical) was not run. `ka_muhurta_seva` declares no `source_paths` (a change to `panchang_engine/` or `muhurat/` is not hashed into its code digest) `[brief]`. Builder role has no grant on `asset_registry.selftest_detail` `[brief]`.
- `ka_tulana`'s ranker has no live caller (section 0, fact 1): its digest would prove the self-test only.

**Recommendation.** Yes to I-4/I-5 as written, and yes to the same shape for `ka_graha_sancara` and `ka_tulana` after a determinism check; declare `source_paths` on `ka_muhurta_seva`; keep `bg_panchanga` with the L0 lane; plan `ka_muhurta_seva` in wave 1 as the rebuild plan already does. The builder grant is Track E / grants, not decided here. Note for the `ka_tulana` spec: say in the declaration that it proves the self-test, not a served ranking, until a caller exists.

**Effect.** (a) Yes: registry rows only (one `INSERT` per asset) plus one class attribute; no data row or served field; receipts change from "unknown" to "proven" after each service's next run; two of the five are global scope and need `super_admin` (REVIEW). (b) Only I-4/I-5: `ka_graha_sancara` and `ka_tulana` stay "unknown"; assets whose proof chain passes through them cannot reach "proven". (c) None: the five stay unproven and the Phala-half proof for `ka_sangam` (blocker B-2) stays blocked.

**Citation.** Not classical. citation: n/a.

---

### Q-L3-11 — `ka_graha_sancara` FD-1: authorise a global-scope dispatch

**SS ruling (2026-10-01):** Modified: yes in principle; the global dispatch comes to SS as a REVIEW when the time comes (not authorised now). Track I: TI-L3-36.

**Question.** Authorise a global-scope dispatch of the self-test to re-measure the recorded `unhealthy` / `lit` row?

**Facts.** Live registry row: `service_health = unhealthy`, `last_selftest_at = 2026-08-02`, `selftest_detail = {"checks":[{"check":"ephemeris_computes","error":"0","passed":false}],"errors":["ephemeris computation failed: 0"]}` `[db]`. The error text "0" is the `KeyError: 0` symptom fixed by commit `97fd08e1c` (2026-09-05, #1751), which also made the writer raise on an unhealthy result (`ka_graha_sancara.py:86-94`, per the brief); the recorded row predates it (`97fd08e1c` confirmed in `git log`; the raise lines `[brief]`). Scope is global (`super_admin` required); the writer only writes the asset's own health row; builder role lacks the `selftest_detail` grant `[brief]`.

**Recommendation.** Yes, authorise one dispatch (as `super_admin`, or after the grant lands). It is read-only on chart data and re-measures a recorded status that contradicts a `lit` throughput state (CLAUDE.md §N.8). If it still fails, the writer now raises and the state honestly reads `error`.

**Effect.** (a) Yes: the registry health row is re-measured; expected `healthy` after the 2026-09-05 fix (not guaranteed); no data row; the §N.8 mismatch closes either way. (b) No: the recorded `unhealthy` beside `lit` stays and the asset stays unproven.

**Citation.** Not classical. citation: n/a.

---

### Q-L3-12 — CF-28: floors for rolling-horizon assets

**SS ruling (2026-10-01):** (R) Accepted: N/A by cause `rolling_horizon` with the window declared; it becomes a rule only through `NA_RULE_DECISIONS` with SS approval. Track I: TI-L3-13, TI-L3-35.

**Question.** How is a floor declared for a rolling-horizon asset: N/A by cause, or restated at a pinned as-of?

**Facts.** `ka_kota_chakra` and `ka_moorti_nirnaya` scan `today - 60 days` to `today + 400 days` (`HORIZON_BACK_DAYS = 60`, `HORIZON_FORWARD_DAYS = 400`; `services/ka_kota_chakra/writer.py:73-74`, `services/ka_moorti_nirnaya/writer.py:73-74`; `today = date.today()` at kota `:239` and moorti `:293`); moorti already accepts `ctx.config['horizon_start'/'horizon_end']` (`:296-301`) `[code]`. Registry floors 588 and 72; live counts 585 (kota) and 74 (moorti), identical on the canonical and Abhinandan charts `[db]`. A run touching the horizon edge produces `moorti_computed = false` rows, so edge rows change with the build date by design `[brief]`. `ka_bhavishya_lekha.py:83,180` and `ka_jivana_parva.py:60` also derive their windows from the build date; nothing in `pipeline/orchestrator/*.py` sets `as_of_date` `[code]`. CLAUDE.md §N.4: floors are aspirational, not gates.

**Recommendation.** N/A by cause (`rolling_horizon`) for the Count.floor reading, with the window (`back_days`, `forward_days`) declared in the registry and the as-of date used recorded in the build note; separately pin and record `as_of_date` end to end (a tier-independent writer fix) and make the "five years on" calendar-safe. Reason: a floor restated at a pinned as-of would describe a date, not the asset, and would need re-stating on every rebuild; the floor is informational anyway.

**Effect.** (a) N/A by cause: Count.floor stops reading FAIL for these assets; needs a declaration/detector rule (N-22, Track E); no data change. (b) Restate at a pinned as-of: the floor reads against a stated date; needs a registry edit per rebuild and the pin; the 'now' view must still default to today. (c) Neither: the floor keeps drifting with the build date (588 vs 585 today).

**Citation.** Not classical. citation: n/a.

---

### Q-L3-13 — `ka_moorti_nirnaya` / `kala_tithi_pravesha`: notify Pravāha before a rebuild?

**SS ruling (2026-10-01):** Accepted as written. Track I: TI-L3-37.

**Question.** Does SS notify Pravāha before any wave that rebuilds `ka_moorti_nirnaya` (Pravāha-owned python reads its rows and `upstream_fingerprint`)? Same for `kala_tithi_pravesha`?

**Facts.** Pravāha-owned readers `[code]`: `services/gochara_v3/mechanisms/w22_moorti_nirnaya.py`, `gochara_v3/context.py:582-605` (`kala_moorti_nirnaya` rows), `services/ka_vedha_gochara/freshness.py:83-102` (a freshness check on the table's `upstream_fingerprint`); `kala_tithi_pravesha` by `gochara_v3/mechanisms/w27_annual_stack.py`. `ka_moorti_nirnaya` is `lit`/fresh, not in the rebuild plan's launch set, and flips `stale` if `bg_transit_rules` completes with output changed `[brief]`. Precedent: SS L0 Q5 — before any wave touching `bg_ephemeris` or `bg_texts`, SS notifies Pravāha `[brief]`.

**Recommendation.** Yes. It costs one message and the readers' freshness check compares a fingerprint that a rebuild changes; follow the L0 Q5 precedent.

**Effect.** (a) Yes: process only; no code or data change. (b) No: a rebuild (or CF-28's as-of change) may flip Pravāha's freshness check without warning.

**Citation.** Not classical. citation: n/a.

---

### Q-L3-14 — `ka_tithi_pravesha` FD-1: what is the technique, and what is it called?

**SS ruling (2026-10-01):** Accepted as written (keep the computation, correct the label; no birth-tithi recompute without a source). Track I: TI-L3-25.

**Question.** Does the asset compute Tithi-Praveśa (birth-tithi recurrence) or a lunar return; rename, recompute, or serve both?

**Facts.** The module defines the technique as the Moon's return to its natal sidereal LONGITUDE nearest each solar birthday (`services/ka_tithi_pravesha/logic.py:1-20`), taken from "established Jyotiṣa doctrine per the CLAUDECODE task brief's explicit framing" and a glossary line "Tithi-Praveśa (annual lunar-return chart)"; it states that no spec beyond a one-line registry item exists `[code]`. A lunar return to a longitude is not a recurrence of the birth tithi (a Sun-Moon elongation); that reading is an inference from the name. The rows are honest: `classical_source_citation = 'not_in_corpus'` on every row and `verification_pass_status` is earned `[code][brief]`. Reader: Pravāha's `w27_annual_stack.py` reads the table by name `[code]`. Corpus search of `classical_text_chunks` for tithi-pravesha / pravesa / lunar return / birth-tithi returned only a Muhurta Chintamani line on shunning the birth-tithi (`muhurta_chintamani_pg0026_c01`), not a definition `[corpus]`.

**Recommendation.** Keep the computation, correct the label: describe it as an annual lunar-return chart (Moon at its natal longitude) in the registry description, the served tool text and the module header; do NOT compute a birth-tithi recurrence until an acharya supplies a definition and the corpus holds a source (CLAUDE.md B.3, B.10). No change to `asset_id` or table name (the id is locked; Pravāha reads by name).

**Effect.** (a) Rename the label only: text only; no rebuild; descriptor text, registry description, module header change. (b) Recompute as birth-tithi recurrence: all 120 windows change; needs production rebuild (REVIEW); needs a source first. (c) Serve both as separate labelled series: new asset or table, new floor, Pravāha impact; not recommended without a source. (d) Leave as is: the name and the computation keep disagreeing.

**Citation.** citation: not found in repo, needs bg_texts lookup (for both Tithi-Praveśa and any lunar-return doctrine). **Citation state (SS rule):** `unsourced`.

---

### Q-L3-15 — `ka_yojaka` ownership (and `ka_moorti_nirnaya`)

**SS ruling (2026-10-01):** Accepted as written.

**Question.** Does the Saṅgam brief claim `ka_yojaka`, which would move it from this set to A.L3f evaluation? Is `ka_moorti_nirnaya` (read by `ka_gochara`) treated as non-family?

**Facts.** The claim comes from `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` §2.3 item 6 and the layer instance Appendix A `[brief]`; that focus document is not in this repository and was not read. In code: `ka_sangam.py:7` reads `kala_activation_predicates`, which `ka_yojaka` writes, so `ka_yojaka` is a real build prerequisite of `ka_sangam`; it is also read by `ka_kalasutra`, `ka_vighnakara`, `ka_jivana_parva` and `ph_nimitta` (INDEX §3 and the yojaka brief, `[brief]`). `ka_moorti_nirnaya` is declared by `ka_gochara` and read by Pravāha-owned code (Q-L3-13) `[code]`; it appears on no family list `[brief]`.

**Recommendation.** Keep `ka_yojaka` in this (non-family) set and treat the Saṅgam dependency as a build-order fact, not an ownership transfer: it has at least four consumers outside the Saṅgam family. Keep `ka_moorti_nirnaya` non-family with the coupling documented (FD-3, a documentation-only change). If the Saṅgam brief nevertheless claims `ka_yojaka`, Track A §6 moves it to evaluation-only; SS can rule that when the Saṅgam brief exists.

**Effect.** Docs and review-routing only: which lane writes the disposition and the fix design for the asset. No code, registry or rebuild change either way. If `ka_yojaka` moves, its brief becomes evaluation-only and CF-27/FD-1 (hook defaults) is decided by Track F instead.

**Citation.** Not classical. citation: n/a.

---

### Q-L3-16 — do the L0 rulings carry to L3?

**SS ruling (2026-10-01):** (R) Accepted as written (provisional until J1).

**Question.** Do SS's L0 rulings Q1 (completion by count), Q2 (Dens applicability and `uniform_authority`), Q11 (Build.history window) and Q13 (Carr D1 / N/A for ratified judgment seeds) carry to L3? Several L3 cells depend on them.

**Facts.** The rulings, as recorded in the L0 INDEX §9 `[brief]`: Q1 (R) a converged rerun with `rows_written = 0` reads Build.completion PASS only if the writer declares the changed-rows convention AND count_integrity passes on populated rows; Q2 (R) Dens applies wherever a served surface is reached, `uniform_authority: true` lets a uniform vocabulary pass on facets without a tier, mixed-authority tables need a real tier, "no served surface" stays N/A; Q11 Build.history counts only runs since the last change to the writer or the registry row; Q13 (R) Carr D1 reads PASS only if every row matches, ratified judgment seeds get check-level N/A by cause `ratified_judgment`. In L3: the four services have no served select (Dens NO_DETECTOR) and no table; 13 non-family assets' latest recorded error is a cascade `BLOCKED` or a since-fixed `KeyError` (Build.history); `ka_tulana`'s native-ratified composite weights are a ratified judgment (`ranker.py:4`) `[brief][code]`. The L3 Build.completion FAILs are cascade-shaped (stored count 0 beside `rows_written > 0`), which Q1's count-based rule already reads correctly `[brief]`.

**Recommendation.** Yes, carry all four to L3, provisionally, with these readings: Q1 unchanged; Q2: the four services read N/A by cause `no-served-surface`, table assets need a tier or `uniform_authority` per table; Q11 unchanged; Q13: `ka_tulana` weights `ratified_judgment`, the rest D2/D3 per the briefs. Reason: the cells differ only by asset kind, not by criterion definition, and a layer-specific reading would fork the inspector.

**Effect.** Criterion definitions and the inspector's reading only; no asset, registry or rebuild change. (a) Carry: L3 cells re-read under the same rules after the Track I/E detector items. (b) Do not carry: L3 needs its own rules (a per-layer fork of Dens, Build.history, Carr and completion).

**Citation.** Not classical. citation: n/a.

---

### Q-L3-17 — evaluation-only briefs for `ka_sangam` and `ka_kshetra`

**SS ruling (2026-10-01):** Accepted as written (variance (7) acknowledged).

**Question.** Keep the two evaluation-only briefs for the family-owned assets in this set, or leave them to A.L3f?

**Facts.** Track A §6 says Track A writes no Saṅgam or Kṣetra brief; the two briefs state measured facts and ownership and propose no disposition or design (INDEX §0, §12 variance (7)) `[brief]`. They record facts the family lanes need: `kala_convergence` emptied by cascade (I-6); the Mode C intake note; `ka_kshetra` `error` with 8,570,075 of 8,599,775 rows (partial), the connection-loss cause (I-9) and the I-10 split; declared-versus-read edges (Appendix A.3) `[brief]`.

**Recommendation.** Keep them, labelled as evidence inputs to A.L3f, and have SS acknowledge the variance (7). They cost two files, propose nothing, and preserve facts found while reading the neighbours; dropping them later is a documentation edit.

**Effect.** Docs only. (a) Keep: INDEX counts stay 18 briefs; A.L3f reads them. (b) Leave to A.L3f: remove the two files from this set and re-point INDEX §0/§3; no code change.

**Citation.** Not classical. citation: n/a.

---

### Q-L3-X1 — `ka_vighnakara` FD-4 / CF-29: remove the day-of-month proxy and record detector status (routed to SS by INDEX §8, no Q id)

**SS ruling (2026-10-01):** (R) Accepted as written. The design for root-found obstruction windows plus the fallback removal is a separate design REVIEW already being written. Track I: TI-L3-28.

**Question.** When the panchāṅga engine is unavailable or raises, should the detector emit nothing and record `detector_status`, instead of computing a tithi from the day of the month?

**Facts.** `tithi = (peak_date.day % 15) or 15` (`ka_vighnakara.py:717-719`, comment "less accurate but better than nothing") is a calendar-arithmetic value with no astronomical basis; the stored `source` is `'panchang_engine' if muhurta_service else 'day_mod_proxy'` (`:732`), so a proxy tithi computed after an engine exception is stamped as engine-sourced; the docstring promises "real tithi, not day-mod arithmetic" (`:9`); each of the five detectors runs inside `except Exception: logger.debug` (`:544-584`), so a crashed detector equals a clean negative `[code]`. Stored: all 130 Abhinandan panchanga rows carry `source = panchang_engine`, so no stored row came from the proxy `[db]`. CLAUDE.md B.10 (no fabricated computation), §N.7 items 4 and 6.

**Recommendation.** Yes: remove the proxy (B.10), emit no panchanga row when the engine fails, and add an additive `detector_status` record (which of the five detectors ran, which were unavailable and why) to the row or build note; narrow the blanket `except` to the expected failures and count the rest. The semantics of an absent detector (does "unavailable" lower severity or only flag?) are tier-dependent (TG-L3-019); recommend "flag only, never score" until SS rules.

**Effect.** (a) Yes: proxy rows cannot exist (none are stored today); `obstruction_detail` gains keys (consumers `ka_kala_darshana` copies `obstruction_summary`, `ph_muhurta`, `ph_pratikara`, `query_obstruction_periods.ts` ignore unknown keys per the brief; not verified for every consumer); rides the single `ka_vighnakara` rebuild. (b) No: a failed engine call keeps producing a calendar-arithmetic tithi labelled as engine data on any chart where the engine is unavailable.

**Citation.** Not classical. citation: n/a.

---

## SUMMARY TABLE (one page)

| id | short question | recommendation | SS ruling (2026-10-01) |
|---|---|---|---|
| A-1 (ruled) | Gandanta window (last 3°20' of water signs + first 3°20' of fire signs) | Record. Promote the L1 `check_gandanta` (3°20' both sides) to one shared L0 module with BPHS chunk citations; `ka_vighnakara` reads it. One rebuild with A-2. | Accepted (R); 0°48' only a named stricter variant |
| A-2 (ruled) | Rikta set | Record. Read the engine set via `compute_tithi_attrs(...).anga_type == "Rikta"`; citation Yavana Jataka `yavana_jataka_pg0926_c02`. | Accepted (R) |
| A-3 (ruled, REVIEW design) | `ka_taranga` event-class tautology | Option R: retire batch event-class rows (92,412 → 43,488 per chart); F and T as alternatives. | Option R (R); design REVIEW |
| A-4 (ruled) | `ka_tulana` rejects Mode C/D | Accept A/B/C/D; `mode` is not a scoring input; no live caller, so no served change. Evidence E1-E5 recorded. | Accepted |
| Q-L3-01 | CF-27 constants and defaults | Split: option 1 for thresholds/weights; option 2 (drop and renormalise) for stand-ins of uncomputed terms; option 3 follows the L2 CF-20 ruling. | Accepted (R) |
| Q-L3-02 | `ka_avadhi` honest `citations` | Yes: `dasha_row_id` + `attribution_state` (L0 Q3 pattern), all `unsourced` until Track I checks BPHS Ch. 46 candidates. | Accepted (R) |
| Q-L3-03 | `ka_taranga` ayanamsha pin (residual of FD-1/FD-2) | Yes, pin `lahiri_chitrapaksha`; zero stored changes on all 3 charts. | Accepted |
| Q-L3-04 | Canonical graha → domain table | One shared L0 table whose values are in `CANONICAL_DOMAINS`; delete both local tables; Rahu/Ketu `unsourced`. | Accepted (R) |
| Q-L3-05 | Bhavishya keyword precedence; ±21 days | Acharya-ruled explicit map, ambiguity → `general`; ratify ±21 days as a named pre-registered window with a decision id. | Modified (R): SS rules; N-57 window |
| Q-L3-06 | `ka_jivana_parva` claim and no-evidence quality | Yes to both (drop generic themes; add `no_convergence_evidence`; one CHECK migration); after FD-1. | Accepted (R) |
| Q-L3-07 | `ka_kala_darshana` context text fix | Approve; latent, 0 of 750 stored rows change. | Accepted (R) |
| Q-L3-08 | Remove unread edges; serve-time edges; anchor guard owner | Remove 7 unread edges; serve-time is not an edge; guard on the L4 side. | Accepted |
| Q-L3-09 (residual) | Node convention; combustion scope | MEAN node (L1/engine convention; TRUE as named variant); fix docstring now, scope to the acharya; orbs from L0 only. | Modified (R): MEAN; L0 orbs; honest null |
| Q-L3-10 | Digest specs for the services | Yes to I-4/I-5, and to `ka_graha_sancara` and `ka_tulana` after a determinism check; `ka_muhurta_seva` in wave 1. | Accepted |
| Q-L3-11 | Dispatch `ka_graha_sancara` self-test | Yes (global, `super_admin` or after grant); stored `unhealthy` predates the 2026-09-05 fix. | Yes in principle; dispatch returns as REVIEW |
| Q-L3-12 | Floor for rolling-horizon assets | N/A by cause `rolling_horizon`, window declared; pin and record as-of separately. | Accepted (R); rule only via NA_RULE_DECISIONS |
| Q-L3-13 | Notify Pravāha before moorti/tithi rebuilds | Yes (L0 Q5 precedent). | Accepted |
| Q-L3-14 | Tithi-Praveśa vs lunar return | Keep the computation, correct the label; no birth-tithi recompute without a source. | Accepted |
| Q-L3-15 | `ka_yojaka` / `ka_moorti_nirnaya` ownership | Both stay non-family; Saṅgam dependency is a build-order fact. | Accepted |
| Q-L3-16 | Do L0 rulings Q1/Q2/Q11/Q13 carry to L3 | Yes, provisionally, with the service-specific readings stated. | Accepted (R) |
| Q-L3-17 | Keep the sangam/kshetra evaluation-only briefs | Keep as evidence inputs to A.L3f; acknowledge variance (7). | Accepted |
| Q-L3-X1 | Remove the day-of-month tithi proxy; record detector status | Yes; flag-only semantics for an absent detector until ruled. | Accepted (R) |

---

## What I could not verify

- **Branch tip.** Everything was read at `0945da3f3` (PR #2835 head). `origin/main` is at `4eb40bec1` and the INDEX itself says its "not merged" statements are stale at the tip; PRs #2826 and #2827 and the rebuild plan v1.1.1 were not read. A `git ls-tree` of `origin/main` showed no `platform/migrations/1212-1215` files although the INDEX says #2828 (migration 1214) merged; not resolved.
- **Documents outside the repository:** `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md`, Track A brief §6/§10, the rebuild plan, `reg_state.json`, `/Users/Dev/suvarna-evidence/*`. Statements that rest on them are tagged `[brief]`.
- **L2 CF-20 ruling status** (Q-L3-01): not visible in this branch.
- **Counts that need a re-run of code, not a read:** how many Rikta rows (19/24/29) a corrected set would add, how many Gandanta rows would fire, how many Rahu-based rows change under MEAN node. Only arithmetic bounds or none are given.
- **Corpus citations** are text-search hits in OCR text, read by me, not checked against the printed books; a passage for the fire-sign half of Gandanta in degrees, for Rahu/Ketu significations, for Mudda/Naisargika/chara_karaka periods, for house multi-signification (BPHS Ch. 11), for Tithi-Praveśa and for the writer's own cited "Muhurta-Chintamani Rikta" and "Phaladeepika ch.2" were not found. The `reference_karakas` "BPHS Ch.27" label is uncorroborated. Under the SS citations rule: the hits are `sourced_ocr_unverified`; every passage listed above as not found is `unsourced`.
- **The "no live caller" finding** for the I-11 ranker rests on a repository grep; external callers cannot be excluded.
- **The Q-L3-12 and Q-L3-08 details** on `ka_kota_chakra` / `ka_moorti_nirnaya` blast radius, Nirmāṇa manifests and detector rules are quoted from the briefs.
- **Whether Abhinandan's `kala_bhavishya` rows are referenced by `phala_anchors`** (Q-L3-05 refusal caveat): not measured.

## Appendix · read-only evidence queries (as `suvarna_reader`, 2026-10-01)

Run through a subshell that sources the credential file silently; no credential is shown here. All are `SELECT`.

```sql
-- A-1/A-2/X1: stored obstruction rows
select chart_id, obstruction_type, count(*) from kala_obstruction group by 1,2;
select chart_id, obstruction_detail->>'tithi', obstruction_detail->>'source', count(*)
  from kala_obstruction where obstruction_type='panchanga_obstruction' group by 1,2,3;
-- A-3: event-class degeneracy
select scope_kind, count(*), count(distinct components->>'dasha_contribution') from kala_taranga group by 1;
-- A-4: modes emitted
select chart_id, mode, count(*) from kala_convergence group by 1,2;
select pg_get_constraintdef(oid) from pg_constraint where conrelid='kala_convergence'::regclass and contype='c';
select mode, count(*) filter (where rarity_years is null), round(avg(convergence_score)::numeric,3)
  from kala_convergence group by 1;
-- Q-L3-01: reach of the 0.5 / 1.0 defaults
select chart_id, count(*),
  count(*) filter (where (dasha_eligibility_rule_jsonb->>'cgm_centrality_weight')::numeric = 0.5),
  count(*) filter (where (strength_affliction_hook_jsonb->>'dignity_score')::numeric = 0.5),
  count(*) filter (where (strength_affliction_hook_jsonb->>'non_affliction')::numeric = 1.0)
  from kala_activation_predicates group by 1;
select chart_id, count(*), count(*) filter (where dasha_activation_proximity_score = 0.5) from kala_activation group by 1;
-- Q-L3-02: citations per system
select system_id, count(*), count(distinct citations::text) from kala_avadhi where chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1;
-- Q-L3-03: ayanamsha pin (stored lord vs Lahiri lord)
select t.chart_id, count(*), count(*) filter (where t.lord is distinct from l.lord_graha)
  from (select chart_id, month, components->>'dasha_lord' lord from kala_taranga where scope_kind='domain' and scope_id='career') t
  left join chart_dashas l on l.chart_id=t.chart_id and l.system_id='vimshottari' and l.level_n=1
   and l.ayanamsha_id='lahiri_chitrapaksha' and l.start_date<=t.month and l.end_date>=t.month group by 1;
-- Q-L3-04: out-of-vocabulary scopes and empty Rahu sets
select scope_id, max((components->>'transit_contribution')::numeric), max((components->>'promise_contribution')::numeric)
  from kala_taranga where scope_kind='domain' and chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1;
select lord_graha, count(*), count(*) filter (where jsonb_array_length(coalesce(dossier->'activated_pratijna_ids','[]'::jsonb))=0)
  from kala_avadhi where chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1;
-- Q-L3-05/06/07: bhavishya window, parva quality, darshana context
select count(*), min(window_end-window_start), max(window_end-window_start) from kala_bhavishya;
select chart_id, parva_quality, count(*), count(*) filter (where avg_effective_score is null) from kala_jivana_parva group by 1,2;
select chart_id, count(*), count(*) filter (where narrative->>'context' not like '%orb strength%') from kala_darshana group by 1;
-- Q-L3-08/10/11: registry facts
select asset_id, depends_on from asset_registry where asset_id in ('ka_taranga','ka_jivana_parva','ka_kala_darshana','ka_bhavishya_lekha','ka_tulana');
select asset_id from asset_output_digest_specs where asset_id like 'ka_%';
select asset_id, service_health, last_selftest_at, selftest_detail from asset_registry where asset_id in ('ka_graha_sancara','ka_tulana');
-- corpus (all citations): classical_text_chunks(text_id, chunk_id, content_en) searched with ~* patterns
```


## Track I items arising from the rulings (continuing the numbering of INDEX section 10)

Original items TI-L3-01 to TI-L3-25 keep their ids; their status after the rulings is in `INDEX.md` section 10. New items are TI-L3-26 to TI-L3-37 (rulings of 2026-10-01) and TI-L3-38 (ruling of 2026-10-02). Class set as in the INDEX: registry / declaration / writer code / detector / research. All are provisional until J1; (R) marks an output-changing or verdict-defining ruling.

| id | asset(s) | item | class | rebuild | from |
|---|---|---|---|---|---|
| TI-L3-26 | ka_vighnakara (+ import in the L1 writer `ga_sensitive_degree_writer.py`) | ONE shared L0 Gandanta module: canonical width 3°20' each side (one pāda); 0°48' only as a named stricter variant, never the default; each width cited or `unsourced`; `ka_vighnakara` reads it; `reason` text built from the returned zone | writer code (+ L0 module) | y | A-1 (R); replaces the Gandanta part of TI-L3-23 |
| TI-L3-27 | ka_vighnakara | Rikta set from the engine accessor (`compute_tithi_attrs(...).anga_type == "Rikta"`, `[4, 9, 14, 19, 24, 29]`); drop tithi 15; fix docstrings and the stored citation | writer code (output) | y | A-2 (R); replaces the Rikta part of TI-L3-23 |
| TI-L3-28 | ka_vighnakara | root-found obstruction windows plus removal of the day-of-month proxy and an additive `detector_status` (flag only, never score, for an absent detector); design REVIEW already being written | writer code (design REVIEW) | y | X1 (R); overlaps TI-L3-16 |
| TI-L3-29 | ka_vighnakara | MEAN node (`swe.MEAN_NODE`) as the L3 transit contract, TRUE a named variant, node stated in the row `source`; docstring fixed now | writer code (output) | y | Q-L3-09 (R) |
| TI-L3-30 | ka_vighnakara | combustion: orbs from L0 `bg_combustion_orbs` only (delete the local copy and the 8.0 default; raise when empty); scope per the L1/engine convention; honest null where the engine defines none | writer code | cond | Q-L3-09 |
| TI-L3-31 | ka_taranga | design REVIEW to retire the batch event-class rows (92,412 -> 43,488 rows per chart): state which served surfaces read them, scope the batch `DELETE` so `record_evidence` rows survive, change the kernel branch, restate the floor | writer code (design REVIEW) | y | A-3 (R); supersedes the FD-1 half of TI-L3-04 |
| TI-L3-32 | ka_tulana | accept modes A, B, C, D in `_validate_window` (the table's CHECK set); failing-first test with C and D | service code | n | A-4 |
| TI-L3-33 | ka_bhavishya_lekha | the +/-21 days declared as a NAMED PRE-REGISTERED window (decision N-57) in the brief (done) and its decision id surfaced in `falsifiability`; never tuned after outcomes | writer code + declaration | y | Q-L3-05 (R) |
| TI-L3-34 | all L3 assets with a citation column | apply the citations rule: states `sourced` (passage-verified) / `sourced_ocr_unverified` / `unsourced` (and `refuted` where used); only passage-verified `sourced` counts toward a Ldgr PASS; relabel existing citations | declaration / detector | n | citations rule |
| TI-L3-35 | ka_kota_chakra, ka_moorti_nirnaya | submit the `rolling_horizon` N/A rule through `NA_RULE_DECISIONS` for SS approval; window declared in the registry; as-of pin recorded | declaration + detector | n | Q-L3-12 (R) |
| TI-L3-36 | ka_graha_sancara | REVIEW packet for SS for the global-scope self-test dispatch | research (process REVIEW) | dispatch | Q-L3-11 |
| TI-L3-37 | ka_moorti_nirnaya, ka_tithi_pravesha | SS notifies Pravāha before any wave that rebuilds these assets | research (process REVIEW) | n | Q-L3-13 |
| TI-L3-38 | ka_kshetra (family; Track F owns the design, J1.FO the implementation owner) | `stage2_promise` reads the argala edge's L1 `outcome_by_count`, not `cancelled_flag`: `unobstructed` and `argala_prevails` = active argala; `undetermined` = its own state, not active argala until a strength basis exists | writer code (output) | y (rebuilds at S7 anyway) | ARGALA OUTCOME ruling, SS 2026-10-02 (R) |

**Existing items accepted as designed or amended by the rulings:** TI-L3-03 (Q-L3-07, (R)), TI-L3-04 (FD-2 pin accepted; FD-1 half superseded by TI-L3-31), TI-L3-06 (Q-L3-05: SS rules the map), TI-L3-07 and TI-L3-08 (Q-L3-08), TI-L3-12 (Q-L3-10), TI-L3-13 (Q-L3-12, with TI-L3-35), TI-L3-14 (Q-L3-02, (R)), TI-L3-15 (Q-L3-04, (R)), TI-L3-16 (Q-L3-X1, see TI-L3-28), TI-L3-17 (Q-L3-01), TI-L3-18 (Q-L3-06, (R)), TI-L3-23 (superseded by TI-L3-26 to TI-L3-30), TI-L3-25 (Q-L3-14, rename branch).

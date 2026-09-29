# Review packet — Gochara transit engine, astrological review v2.0 (hierarchy · missing/overkill · efficient implementation)

You are an **independent external reviewer** of an astrological design review. The native
(Abhisek Mohanty — the chart owner and the ruling authority) has asked for two independent reviews
(Codex gpt-6-astra at max reasoning; Kimi K3 at max effort) of the same document, after which the
author (Claude Fable 5.1) will reconcile both, incorporate what survives verification, and seal the
plan. Your job is to **break the review before it is sealed**: a finding the author missed is worth
more than agreement; a doctrinal error the author made is worth most of all.

**Standard: acharya-grade.** A senior Jyotiṣa ācārya reading your answer should find it at or above
their own level; a senior engineer should find nothing hand-waved. Generic astrology is a failure.
So is deference. Judge doctrine as an ācārya would and code as an engineer would.

**Native priorities, in order:** (1) astrological accuracy of the windows the asset delivers,
(2) build efficiency without compromising (1), (3) the surrounding ecosystem matters as much as the asset.

## Ground rules

- **Read-only.** No code changes, builds, migrations, database writes, PRs, config edits, or edits
  to the documents under review. Codex: your final message is your review (see Output). Kimi: print
  your review; write no file.
- **There is no database access in this review.** Every `[L]` figure in the documents is the
  author's own read-only production measurement of 2026-09-29 — treat it as *attributed*, and say
  so where a conclusion depends on it. Do not attempt to connect to any database.
- **Verify, do not trust.** Every `[S]` claim carries a file:line — open it. Every `[D]` names a text —
  check it against the OCR corpus files under `00_ARCHITECTURE/SOURCE_DATA/classical_texts/`
  (BPHS, Jaimini_Sutram, KP, KP_Reader …). Note the campaign's own rule (F-32): the *served* corpus
  is a database table (`classical_text_chunks`, 15 texts incl. Phaladīpikā, Sārāvalī, Jātaka
  Pārijāta, Bṛhat Saṃhitā, Uttara Kālāmṛta, Sarvārtha Cintāmaṇi, nāḍī texts) that you cannot query;
  the OCR folders are a *subset*. So: you may CONFIRM a citation from the files; you may not claim
  ABSENCE from them — label such cases `UNVERIFIABLE_HERE` and say what count should be run.
- Treat every `[P]`, `[J]`, `[I]`, `[U]` in the documents as unproven. Where you supply doctrine the
  author lacked, cite text + chapter/page or label it `[P]` honestly. Never invent a verse.
- **Do not re-open ruled items** (D-1..D-3, R1–R10, N-1..N-22, M-1..M-8 — listed in
  `GOCHARA_RULING_SHEET_v2_0.md` and `GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md`). Do say, explicitly,
  where the review contradicts a ruling or where a ruling itself now looks astrologically wrong in
  light of the findings — that is exactly what the native wants to hear before sealing.
- Labels for your own claims: **[D]** doctrine (text named) · **[P]** practice · **[J]** your
  judgment · **[C]** confirmed in code at file:line · **[U]** could not verify.

## Where things are

Worktree `/Users/Dev/madhav-l3/gochara-wp0-7` · branch `l3/gochara-autonomous-wp0-7` · HEAD at packet
time `507a759bf` (a live executor lane commits to this branch; do not be surprised by newer commits —
the review documents are **untracked**, read them from disk). Python (if you re-run any test):
`/Users/Dev/madhav-l3/gochara-wp0-7/.venv/bin/python` (fallback
`/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/venv/bin/python`). Do not start any
database or container.

Paths below are relative to the worktree; `BRIEFS/` = `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/`,
`PY/` = `platform/python-sidecar/`.

## Read in this order

1. **The document under review** — `BRIEFS/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v2_0.md`
   (sha256 `270184f735c793b7ad69087c9a677233971a500fe2d9b37d4a00da174169ceb0`). Read it in full.
   §1 the timing hierarchy; §2 the 27 verified findings; §3 missing/overkill; §4 component verdicts;
   §5 elevation plan; §6 efficient implementation; §7 the questions put to you.
2. **Its predecessor** — `BRIEFS/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v1_0.md` (superseded, retained):
   §1.2 has the full resonance-map grammar and the 27-class signature table; §3 has the long-form
   component assessment that v2.0 §4 condenses. Review v2.0; use v1.0 for detail.
3. **What the engine was *meant* to be** — `BRIEFS/GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md` (the
   native-ratified plan: §1 decision ledger, §3 findings F-01..F-32, §4 design, §5.3 target-resolution
   contract, §8 scoring split), `BRIEFS/GOCHARA_RULING_SHEET_v2_0.md` (M-1..M-8 rulings, N-15..N-22),
   `BRIEFS/GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md` (M-1 values; tranche authorization; the day's
   corrections), `BRIEFS/GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md` §12 (what was built and why).
4. **What was actually built** — the real-chart outputs the findings rest on:
   `.run/wp10_tranche2/prod_link3_delta_report_482012f1.md` (per-class factors and every era peak, '4.0'
   vs '3.0'), `.run/wp10_tranche2/prod_link3_step06b_runreport_482012f1.json`,
   `.run/wp10_tranche2/link3_class_context_482012f1.json` (the per-class permission booleans),
   `PY/scripts/kala_gochara_cutover/evidence/step06_evidence.md` and `link3_conditioning_evidence.md`.
5. **The code the findings cite** — `PY/services/gochara_v3/engine.py` (λ at :877; permission
   :1876-2146; activity :1166-1254; quality gates :460-603), `PY/services/gochara_v3/context.py`,
   `PY/services/gochara_intensity/{promise,permission,valence,enrichment}.py`,
   `PY/services/gochara_grammar/primitives.py` (dṛṣṭi table :189-199; kakṣyā :625-719),
   `PY/services/gochara_kernel/{contacts,episodes,convention,legacy_semantics}.py` (aspect levels
   contacts.py:206-213; boundaries :259-262; ingress spans episodes.py:399-401; valence and gates in
   legacy_semantics), `PY/scripts/kala_gochara_cutover/{step06_enumerate_episodes,step06a_class_context,step06b_windows_projection}.py`,
   `PY/services/ka_gochara_resonance/writer.py` (class → target grammar :217-301, :304-309, :405-446,
   :799-841, :939-961), `PY/services/ka_vedha_gochara/{logic,writer}.py`,
   `PY/services/ka_moorti_nirnaya/logic.py`, `PY/services/gochara_v3/mechanisms/w23_tara_bala.py`,
   `platform/supabase/migrations/266_bg_transit_tables.sql` (:53-55 — the frame of `bg_transit_rules`),
   `platform/supabase/migrations/388_brahma_ghatana_ontology.sql` and `456_…dr13_shapes.sql` (class
   signatures and citations).
6. **The native's lived record** — `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` §3 (dated events with
   daśā context; the three events used in v2.0 §1.3 are EVT.2013.12.11.01, EVT.2022.01.03.01,
   EVT.2018.11.28.01). Natal positions are quoted in v2.0 §1.3 from L1.
7. **Governing doctrine for the project** — root `CLAUDE.md` §B.3 (derivation ledger), §B.10 (no
   fabricated computation), §N.5 (L1 authority), §N.7 (narration fidelity), §N.8 (earned signal).

## What I need from you

**A. The 27 findings (v2.0 §2).** For each: `CONFIRMED` / `REFUTED` / `PARTLY` / `UNVERIFIABLE_HERE`,
with the file:line you checked. Push hardest on #10 (house-frame mixing), #13 (aspect direction —
do the arithmetic yourself for one Saturn and one Mars case), #14 (Aries boundary), #16/#17 (vedha
gate), #5 (tārā key), and #6/#7 (zero-width spans) — these are the ones that, if wrong, change the
whole picture.

**B. The hierarchy (v2.0 §1.1–1.2).** Is the four-level cascade (Promise → Open → Narrow → Pinpoint,
plus Qualify) the correct decomposition of classical timing? For **each factor** in the table:
`AGREE` / `AMEND` / `REJECT` on its level assignment, with the doctrinal reason. Specifically:
 - Should Mars act at L2 for adverse classes only, or at L3 always?
 - Is slow-body *residence* (from lagna and from Moon) an L1 licence or an L2 narrowing factor?
 - Where do Rahu/Ketu transits belong?
 - Is "OR within a level, AND across levels" the right combination rule, and is the multiplicative
   λ the right algebra for it, or should levels produce *sets* that intersect?
 - What does an ācārya do at L3 that the table omits?

**C. Missing / overkill (v2.0 §3).** For each M1–M13 and O1–O12: `AGREE` / `AMEND` / `REJECT` with
reason. Then: **what did the author miss that has higher leverage than anything listed?** Name
classical mechanisms absent from both the engine and the review. Name anything in §3.3 ("keep as
ruled") that you would reopen.

**D. The doctrine questions (v2.0 §7, items 1–9).** Answer each. Where a question asks for a corpus
count you cannot run, say exactly what predicate should be run and what you expect. Also adjudicate:
 - the double-transit citation on `bg_transit_rules` ("Phaladīpikā ch.26 §double-gochara") — is there
   such a passage, or is double transit 20th-century practice?
 - the mūrti-nirṇaya rule form (nakṣatra mod-4 in code vs rāśi 1/6/11 · 2/5/9 · 3/7/10 · 4/8/12);
 - the Venus vedha pairs (code 11→3, 12→6);
 - the Aṣṭottarī applicability condition (Rahu in kendra/trikoṇa from the lagna lord, not in lagna);
 - the BAV-bindu → weight convention you would admit, and its source.

**E. The efficient implementation (v2.0 §6).** Does the sparse coarse-to-fine evaluation lose any
admissible classical mechanism? Is the cost model plausible (§6.6)? Is there a *better* algorithm or
data model that delivers the same astrology at the same or lower cost? Judge as an engineer:
global boundary table; dedupe targets by physical point; lazy Swiss refinement with
`precision_regime`; interval algebra instead of daily sampling; day tier on demand.

**F. The three worked events (v2.0 §1.3).** Is the author's classical reading right? What would you
add or correct? (Positions are from the project's own L0 ephemeris, Lahiri; natal from L1.)

**G. Verdict.** `PROCEED` / `PROCEED_WITH_AMENDMENTS` / `REWORK` on adopting v2.0 (as amended by you)
as the sealed doctrine plan for the Gochara family — and a **ranked list of amendments** the author
must make before sealing, each with its evidence. Separately: which rulings (if any) should the native
be asked to revisit, and why.

Every finding cites file:line, a text + chapter/page, or a command you ran. Mark anything you could
not verify `UNVERIFIABLE_HERE` — never a plausible default.

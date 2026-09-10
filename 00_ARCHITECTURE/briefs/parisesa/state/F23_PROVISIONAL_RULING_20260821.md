---
title: F-23 — ref_mantras_get / brahma_remedy_corpus mantra coverage
status: PROVISIONAL_RULING_AWAITING_SCHOLARLY_CONFIRMATION
campaign: PARISESA-V4
type: investigate-and-draft-only
date: 2026-08-21
---

**Carve-out per PARIŚEṢA V4 Full Closure v3.1**: this finding requires classical-Sanskrit
/ editorial authority, not engineering judgment. Nothing below is decided or implemented.
No code, migration, or data file was written by the investigating agent.

# F-23 — `ref_mantras_get` / `brahma_remedy_corpus` mantra coverage

## 1. Live re-verification (production, 2026-08-21)

The reproducer numbers **still hold exactly**:

```sql
SELECT count(*), count(mantra_text), count(mantra_sanskrit)
FROM brahma_remedy_corpus WHERE remedy_type='mantra';
-- total=67  mantra_text=16 (24%)  mantra_sanskrit=9 (13%)
```

`ref_mantras_get({planet:'Saturn', limit:10})` returns 10 rows, honestly emitting `null`
for absent fields. **The original finding's honest-null claim is confirmed correct.**

## 2. But the coverage framing is materially misleading

The reproducer counted two of the **three** mantra columns. Adding the third changes the
picture:

| field | populated / 67 |
|---|---|
| `prescription_text` | 67 (100%) |
| `mantra_transliteration` | **42 (63%)** — *not counted by the reproducer* |
| `mantra_text` | 16 (24%) |
| `mantra_sanskrit` | 9 (13%) |
| **any of the three mantra columns** | **58 (87%)** |
| **none of the three** | **9 (13%)** |
| `classical_attestation_text` | **0 (0%)** |

The corpus is not "51 rows missing their mantra." It is **9 rows missing a mantra, and 49
rows storing the mantra in a different column than the reproducer looked in.** The real
defect is **column-assignment incoherence across ingestion cohorts**, which grouping by
`classical_ref` makes unambiguous:

| cohort | n | `mantra_text` | `mantra_sanskrit` | `mantra_transliteration` |
|---|---|---|---|---|
| BPHS Ch.94 nakshatra devata | 27 | 0 | 0 | **27** |
| BPHS Ch.88 (per-planet) | 13 | **13** | 0 | 0 |
| BPHS Ch.91–94 graha beeja matrix | 9 | 0 | **9** | **9** |
| dosha / `classical_tradition` | 14 | 0 | 0 | 6 |
| Phaladeepika + Tajaka | 3 | **3** | 0 | 0 |
| `corpus_sweep` (see §3) | 3 | 0 | 0 | 0 |

Three authoring passes each chose a different column for the same semantic content.
`sat_career_mantra_01` puts `"Om Praam Preem Praum Sah Shanaischaraya Namah"` in
`mantra_text`; `saturn_matrix_mantra` puts the *same mantra* in `mantra_sanskrit`
(Devanagari) + `mantra_transliteration`. A caller reading only `mantra_text` sees the
first and misses the second.

## 3. Two harder defects found en route (both in scope for the ruling)

**(a) Three `corpus_sweep` rows are OCR garbage marked `scaffold_status='live'`.**
Provenance: `brahmagyan/l0_remedy_corpus.py::sweep_classical_text_chunks` (line 3147)
scans `classical_text_chunks.content_en` for regex markers (`\bmantra\b`, `\brecite\b`, …)
and copies the chunk **verbatim** into `prescription_text`. `sweep_mars_mantra_4c2c8f53`
(`chunk_id=bphs_pg0294_c01`) is a passage about **Arudha Pada calculation** — not a remedy
at all. `sweep_mercury_mantra_2068cf00` is unreadable OCR (`"quﬁemudtsww:"`). These three
are served today by `ref_mantras_get`.

This is a textbook **§N.8 Earned-Signal** violation: `scaffold_status='live'` asserts
"vetted, unambiguous remedy," but the detector behind it only checks "exactly one regex
marker + planet word present." No code path could ever set these three to `review`.
Migration `465_classical_text_chunks_ocr_cleanup.sql` (EL-52, 2026-07-25) already
diagnosed this class at the *chunk* table and added `ocr_confidence_score` /
`low_confidence_flag` there — but the **remedy corpus rows derived from those chunks were
never re-scored or demoted**, and no serving path filters on `scaffold_status`.

**(b) An internal Sanskrit contradiction in the Saturn beeja.** `saturn_matrix_mantra`
stores Devanagari `ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः` (*śanaiścarāya*) against
transliteration `"Om Praam Preem Praum Sah Shanaye Namah"` (*śanaye*). These are different
words. `sat_career_mantra_01`'s `mantra_text` independently reads *Shanaischaraya*. My
reading is that the Devanagari is right and the transliteration field is wrong — but
**this is exactly the call I am not qualified to make**, and it is the single most
concrete item for the scholarly reviewer.

**(c) `classical_attestation_text` is 0/67 for mantras, 4/336 corpus-wide** (only
`tantric` rows). Every mantra row cites a *locus* (`classical_ref`) but quotes **no
attesting text**. Under B.3 this is the deepest gap of all: the citations are unverifiable
from the row itself.

*(Non-scope, noted for the ledger: the legacy
`platform/src/lib/retrieve/remedy_tools.ts::query_mantras` still filters
`WHERE category = 'mantras'` — a predicate matching **zero** rows. The live path is
`register_d7_channel.ts`'s `queryMantrasCapability`, which was already fixed
(W4-loop-1/E-5) to `LOWER(remedy_type)='mantra' OR LOWER(category)='mantras'` with
case-insensitive planet. The legacy file is a latent trap if ever re-routed.)*

## 4. Scholarly source options (research, not a decision)

For **graha mantras**, the traditionally authoritative layers, strongest first:

1. **Vedic graha-shanti ṛks** — the Navagraha mantras used in classical śānti, each with a
   precise, verifiable Vedic citation: Sūrya = RV 1.35.2; Candra = RV 10.173.1 / VS;
   Maṅgala = RV 8.44.16; Budha = VS 15.54; Bṛhaspati = RV 2.23.15; Śukra = VS 19.75; Śani =
   **RV 10.9.4** (*śanno devīr abhiṣṭaya…*); Rāhu = RV 4.31.1; Ketu = RV 1.6.3. These are
   the gold standard: public-domain, editionally stable, individually citable to
   sūkta-and-ṛk.
2. **Navagraha bīja mantras** — the set already in the 9 matrix rows. Widely transmitted
   and compiled in **Mantra Mahodadhi** (Mahīdhara, 16th c.) and the Navagraha Stotra
   tradition. Note: the corpus attributes these to *BPHS Ch.91–94*; could not verify that
   BPHS actually contains the bīja set — my provisional view is that this attribution is
   **loose**, a caveat the reviewer should test directly.
3. For **nakshatra devata mantras** (27 rows): the corpus's `"Om Mitrāya Namaḥ"` form is a
   *constructed nāma-mantra*, not a classical citation. The traditionally authoritative
   source is the **Nakṣatra Sūkta / Nakṣatreṣṭi, Taittirīya Brāhmaṇa 3.1.1–3.1.2**, which
   supplies an actual ṛk per nakshatra. BPHS Ch.94 supplies the *devatā table*, not the
   mantra text — so `classical_ref: "BPHS Ch.94"` is currently doing work it cannot
   support.

### Example complete entries (illustrative drafts — transliteration unverified)

**`nakshatra_anuradha_mantra`** (today: transliteration only, cited to BPHS Ch.94)
- `mantra_sanskrit`: `ॐ मित्राय नमः` · `mantra_transliteration`: `oṃ mitrāya namaḥ` (IAST)
- `mantra_text`: retain as the nāma-mantra japa form
- `classical_ref`: `BPHS Ch.94 (devatā attribution only); Taittirīya Brāhmaṇa 3.1.2
  (Anurādhā ṛk, Mitra)`
- `classical_attestation_text`: the TB 3.1.2 Mitra ṛk, quoted verbatim from a named
  public-domain edition

**`dosha_sade_sati_shani_mantra`** (today: nothing in any mantra column)
- `mantra_sanskrit`: `ॐ शन्नो देवीरभिष्टय आपो भवन्तु पीतये…` · `mantra_transliteration`:
  `oṃ śanno devīr abhiṣṭaya āpo bhavantu pītaye…`
- `classical_ref`: `Ṛgveda 10.9.4 (Śani graha-śānti ṛk); BPHS Ch.91–94 (upāya context)`
- Keep the existing Hanuman Chalisa / mustard-oil `prescription_text` — it is real,
  useful, and separately sourced to living tradition.

**`sat_career_mantra_01`** (today: `mantra_text` only) — trivially completable by copying
the Devanagari already present on `saturn_matrix_mantra`, **once §3(b)'s *śanaiścarāya*
vs *śanaye* contradiction is resolved by a reader of Sanskrit.**

**Caveat that cannot be discharged by this pass:** Devanagari orthography, sandhi, and
IAST diacritics cannot be verified without a classical-Sanskrit-literate reviewer. Every
string above is a *draft for review*, not a value to insert.

## 5. Provisional recommendation — the middle path, with sequencing

The recommendation is **the middle path, but not the one the finding itself proposes**,
sequenced into four ordered lanes, confidence descending sharply from Lane 1 to Lane 4.

**Lane 1 — Fix what is false before adding what is missing (high confidence, engineering,
no scholarly gate).** Demote the three `corpus_sweep` rows from `scaffold_status='live'`
to `'review'` (or exclude `category='corpus_sweep'` at the serving layer), and give the
sweep's promotion predicate a detector that measures what `'live'` claims — minimally an
`ocr_confidence_score` floor reusing migration 465's existing scorer, per §N.8. **Serving
OCR noise as a Saturn remedy is a worse failure than serving an honest null**, and unlike
everything else here it needs no acharya. This is the only lane graded urgent.
**Triaged separately as F-144** (see ledger) so it can proceed under normal GA-2/GA-5
authority without waiting on the scholarly-gated lanes below.

**Lane 2 — Normalize the columns (high confidence on the diagnosis; the *rule* needs a
native ruling).** Define and document one contract — proposed: `mantra_sanskrit` =
Devanagari; `mantra_transliteration` = IAST; `mantra_text` = the recitation-ready japa
form incl. count — then backfill *within existing content* (no new scholarship). This
alone takes "has a usable mantra" from an apparent 24% to a real 87% and makes any future
coverage metric meaningful. Add a serving-side `mantra_available` boolean / `empty_reason`
per §N.6 item 4, so a caller never has to guess which of three columns to read.

**Lane 3 — Serve `prescription_text` as the primary content (medium confidence).** This
*is* the finding's proposed middle path and is endorsed, but as a presentation fix
downstream of Lanes 1–2, not as a substitute for them. `prescription_text` is 100%
populated, genuinely useful, and often *contains* the mantra inline. The tool description
("Includes Sanskrit mantra, transliteration, and classical source") over-promises against
a corpus where 13% carry no mantra at all — that phrasing is the actual §N.7-adjacent
defect: prose asserting a coverage the data does not have.

**Lane 4 — Expand the corpus (low confidence; scholarly-gated; do not start before Lane
2).** If expansion proceeds: prefer **Vedic ṛks with sūkta-level citations** over
nāma-mantras, populate `classical_attestation_text` with verbatim quoted text from a
**named public-domain edition** for every new row, and treat the existing `BPHS Ch.91–94`
bīja attribution and `BPHS Ch.94` nakshatra-mantra attribution as **claims to be
re-verified, not settled facts**. A row whose attestation cannot be quoted should stay
null rather than acquire a plausible citation. If no scholarly reviewer is available,
**Lanes 1–3 alone leave the system honest** — and honest partial coverage, correctly
labelled, is a legitimate permanent end state for this corpus.

### What was found vs. what is inferred

**Found (verified against live production / source):** all coverage numbers in §2; the
six-cohort column split; the three OCR sweep rows and their `scaffold_status='live'`; the
`śanaiścarāya`/`śanaye` string mismatch; `classical_attestation_text` at 0/67; migration
465's existing-but-unapplied-downstream OCR scorer; the legacy `remedy_tools.ts`
zero-row predicate vs. the fixed live D7 handler.

**Inferring (not verified):** that the Devanagari rather than the transliteration is the
correct Saturn beeja; that BPHS Ch.91–94 does not in fact contain the bīja set; that TB
3.1.1–2 is the right source for the 27 nakshatra rows; every Sanskrit string in §4. All
four require the scholarly reviewer this finding is carved out for.

**Open questions for the native / reviewer:** (i) Is the Saturn beeja *śanaiścarāya* or
*śanaye*? (ii) Does BPHS actually attest the bīja set, or is that attribution loose? (iii)
Should nakshatra rows carry TB ṛks, or is the nāma-mantra form the intended product? (iv)
Is Lane 4 wanted at all, or is "honest partial coverage, correctly labelled" the desired
permanent state?

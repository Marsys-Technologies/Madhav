---
artifact: SHAD_DARSHANA_ADJUDICATION_16_AGNIVASA_CONVENTION_B (ANTARYĀMIN ruling, standalone)
canonical_id: SHAD_DARSHANA_ADJUDICATION_16_AGNIVASA_CONVENTION_B
version: 1.0
status: RULED — issued by ANTARYĀMIN on 2026-08-04, resuming ADJUDICATION-8's parked slot now
  that its blocker (Muhūrta-Cintāmaṇi translation) has landed.
created: 2026-08-04
author: ANTARYĀMIN (adjudicator agent)
governing: SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md ADJUDICATION-8 (v1.0, 2026-08-01) +
  its NATIVE CONFIRMATIONS addendum (2026-08-02, item 1 and item 3) +
  MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md +
  MUHURTA_CHINTAMANI_TRANSLATION_REPORT_v1_0.md (v1.0, 2026-08-03, PRs #1040/#1041/#1042) +
  platform/supabase/migrations/533_kala_paddhati_profile.sql +
  platform/supabase/migrations/534_kala_paddhati_native_confirmed.sql
native_review: PENDING — reversible ruling; native reviews at next morning pass and may overrule.
numbering_note: the task that commissioned this ruling proposed the filename slug
  "ADJUDICATION_14"; **ADJUDICATION-14 is already taken** (SHAD_DARSHANA_ADJUDICATIONS_NIGHT5_v1_0.md,
  "V4: the §2.3 design-band re-scope") and so is -15 (same file, "V1: minimal per-phase
  instrumentation contract"). Per CLAUDE.md B.8 ("registries must not disagree") this ruling
  takes the next free sequence number, **16**, rather than silently duplicate an existing
  adjudication number. This is a numbering correction only — it does not touch ADJUDICATION-14
  or -15's content.
---

# ANTARYĀMIN — ADJUDICATION-16: Agnivāsa Convention (B), the Muhūrta-Cintāmaṇi arithmetic

## Question

ADJUDICATION-8 (Night-3, 2026-08-01) registered a second Agnivāsa convention slot,
`agnivasa_muhurta_chintamani_arithmetic`, as `convention_status='declared_not_computed'` —
because at that time the `muhurta_chintamani` corpus text (274 chunks, Rāma Daivajña, **the**
classical muhūrta authority) was ingested but untranslated: `content_en` was byte-identical to
`content_sa`, raw OCR, unreadable, uncitable. The native commissioned a supervised translation
task to close exactly this gap (NATIVE CONFIRMATIONS item 3, 2026-08-02); that task closed
2026-08-03 (`MUHURTA_CHINTAMANI_TRANSLATION_REPORT_v1_0.md`, PRs #1040/#1041/#1042, merged to
`main`). Per that report's own §3(a), the pass found and translated exactly **one** Agnivāsa
verse in the entire 274-chunk text.

**This ruling's question:** does that one translated verse actually specify a computable
Muhūrta-Cintāmaṇi-style Agnivāsa arithmetic — a formula from pañcāṅga inputs to an Agnivāsa
location — or is it descriptive/fragmentary and the slot must stay `declared_not_computed`?

## The verse, in full, cited

**Source row**: `classical_text_chunks` — `text_id='muhurta_chintamani'`,
`chunk_id='muhurta_chintamani_pg0048_c01'`, `verse_ref='PG48:C1'`, verse **36** of the text
(the chunk carries verses 35, 36, 37, 38, 39; 36 is the agnivāsa verse). Metre: Indravajrā (per
the translator's confirmed scansion, all four pādas exact). Section heading in the source:
**वह्निनिवासस्तत्फलम्** ("The residence of Vahni [fire], and its fruit").

`content_sa` (raw OCR, immutable, unchanged by the translation pass):

> सेका तिथिवीरयुता कृताप्ता शेषे एणेऽभरे भुवि वह्विवासः। सौख्याय होमे शशियुग्मशेषे
> प्राणार्थनाशौदिवि भूतरेच॥३६॥

`cleaned_devanagari_text` (OCR-repaired reading, verified — the translator's `ocr_review_note`
explicitly calls this verse "clean… all four pādas scan exactly as Indravajrā, and the ṭīkā's
arithmetic… independently confirms the emendation"):

> सैका तिथिर्वारयुता कृताप्ता शेषे गुणेऽभ्रे भुवि वह्निवासः । सौख्याय होमे शशियुग्मशेषे
> प्राणार्थनाशौ दिवि भूतले च ॥ ३६ ॥

`content_en` (machine-translated, supervised, independently verified — 88/88 verified this
pass, this specific chunk called out by the verifier for "extra scrutiny given its outsized
downstream weight"):

> **Mūla (verse 36):** "That [current] tithi (lunar day), with one added and joined to the vāra
> (weekday), is divided by four. When the remainder is guṇa (three) or abhra (zero), the
> residence of Vahni (fire) is upon the earth: therein a homa makes for happiness. When the
> remainder is śaśi (one) or yugma (two), [the fire dwells] in the sky and beneath the earth
> respectively, and there is destruction of the life-breath and of wealth."
>
> **Ṭīkā (verse 36):** "Add 1 to the current tithi, add the vāra, divide by 4 and keep the
> remainder. If the remainder is 0 or 3, know the residence of Agni to be in the earth:
> performing the oblation will bring happiness. If the remainder is 1 or 2, the residence of
> Vahni is, respectively, in the sky (ākāśa) and in the netherworld (pātāla); performing a homa
> then destroys the life-breath and wealth."

Provenance on this row (confirmed live, 2026-08-04): `translation_status =
'machine_translated_supervised'`, `translation_provenance = 'machine_translation_supervised_
2026-08; commissioned per SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS;
source edition per translator field'`, `translator = 'Muhurta Chintamani — Mahidhara Sharma
bhasha tika, Khemraj Shrikrishnadas Press'`, `ocr_confidence_score = 0.550`,
`low_confidence_flag = true` (the chunk's *other* verses carry the flagged OCR ambiguities per
`ocr_review_note` — verse 36 itself is explicitly excluded from all three flagged loci).

## Ruling

**YES — this verse specifies a genuine, computable Muhūrta-Cintāmaṇi arithmetic. This is not a
fabrication and not an inference: it is a direct, verified translation of a named, cited primary
source, read from the live corpus row, with both mūla and ṭīkā in independent agreement on the
same formula.**

### The extracted rule

```
remainder = (tithi_id + 1 + vara_id) mod 4

remainder ∈ {0, 3}  →  Agnivāsa = Pṛthvī (earth)   — homa/yajña AUSPICIOUS
remainder = 1       →  Agnivāsa = Ākāśa (sky)      — prāṇa-nāśa (destroys life-breath)
remainder = 2        →  Agnivāsa = Pātāla (netherworld) — artha-nāśa (destroys wealth)
```

**Input encodings — already L1-canonical, not a new invention.** The verse itself specifies
only the arithmetic, not a numbering scheme for "tithi" and "vāra"; those are supplied by the
platform's existing, sourced conventions, both already live in
`platform/python-sidecar/panchang_engine/shastra_tables.py`:

- `tithi_id`: continuous 1–30 across both pakṣas (Śukla 1–15, Kṛṣṇa 16–30 in continuous count)
  — `shastra_tables.py` §1, whose own comment cites **"Source: MC §1"** (MC = this same
  Muhūrta-Cintāmaṇi text) for that exact numbering, so applying it here is using the text's own
  established convention, not importing a foreign one.
- `vara_id`: 1 = Ravivāra (Sunday) … 7 = Śanivāra (Saturday) — `VARA_NAMES` table, same file,
  already the platform-wide vāra encoding used by every other vāra-keyed table (Rāhu-kālam,
  Yamaghaṇṭaka, `RAHU_VASA_TABLE`, etc.).

No new numbering convention needs to be invented or guessed for this rule to be executable.

### This is a genuinely different reckoning from Convention (A) — confirming, not contradicting, the original ruling

Convention (A) `agnivasa_tithi_element_prithvi` (native-confirmed lineage practice, per NATIVE
CONFIRMATIONS item 1) is `AGNI_VASA_TABLE` at `shastra_tables.py:1188`: a **static, tithi-only**
banding into **four** pañca-bhūta elements — Pṛthvī tithi 1–7, Jala 8–15, Vāyu 16–22, Ākāśa
23–30 — independent of vāra.

Convention (B) `agnivasa_muhurta_chintamani_arithmetic` (this ruling) is a **tithi-AND-vāra-
dependent** formula over **three** locations — Pṛthvī, Ākāśa, Pātāla — with no Jala/Vāyu terms
at all.

These do not merely differ in favourable set; they differ in **kind** — element count (4 vs 3),
inputs consumed (tithi-only vs tithi+vāra), and mechanism (static table vs modular arithmetic).
ADJUDICATION-8 anticipated precisely this: *"The muhūrta literature demonstrably carries more
than one Agnivāsa reckoning — which is exactly why the Elevation doc names Agnivāsa as the
canonical example of lineage variation."* This verse is the corpus-attested proof of that claim,
not a discrepancy to be reconciled — the two conventions are meant to coexist as distinct,
separately-labelled rows.

### What this ruling does NOT do

**It does not make Convention (B) the operative convention, and it does not touch Convention
(A).** NATIVE CONFIRMATIONS item 1 (2026-08-02) is unambiguous and unconditional: the native's
own lineage practice is Pṛthvī-favourable per the tithi-element table (Convention A),
`native_confirmed = TRUE`. Convention (B) is Rāma Daivajña's Muhūrta-Cintāmaṇi reckoning — a
real, verified, citable classical convention, but it is **not** the convention the native
identified as his own lineage's. It graduates from "not computable" to "computable and
corpus-grounded," not to "the native's convention" or "the graded default." The W4 hard
constraint (unfavourable Agnivāsa eliminates a yajña-class candidate) continues to run on
Convention (A) unless and until the native says otherwise.

### Recommended data change (NOT executed by this ruling — docs-only task)

For the builder session that next touches `kala_paddhati_profile` (item 37 / the W4 lane), the
row for `convention_id='agnivasa_muhurta_chintamani_arithmetic'` should be updated:

```
convention_status  = 'computed'          -- was 'declared_not_computed'
computation_formula = '(tithi_id + 1 + vara_id) mod 4 → {0,3}:Prithvi(favourable) |
                        1:Akasha(unfavourable) | 2:Patala(unfavourable)'
provenance          = 'muhurta_chintamani MC 1.36, chunk_id=muhurta_chintamani_pg0048_c01,
                        machine_translated_supervised + independently verified 2026-08-03;
                        SHAD_DARSHANA_ADJUDICATION_16_AGNIVASA_CONVENTION_B_v1_0.md'
school_tag          = 'muhurta_chintamani_rama_daivajna'
native_confirmed    = FALSE               -- unchanged: this is NOT the confirmed lineage row
corpus_gap_ref       = NULL                -- the gap this pointed at is now closed
```

`convention_status` on `kala_paddhati_profile` is a two-value `CHECK ('computed',
'declared_not_computed')` per `533_kala_paddhati_profile.sql:55-56` — there is no third state,
so this ruling's finding maps cleanly onto the existing schema with no schema change required.
Convention (A)'s row is untouched by this recommendation.

Both conventions, once (B) is seeded, now report through the same `paddhati_divergence` census
the W4 Mode-2 fixture already exercises — but as **two independently computed, separately
labelled conventions with different outputs for at least some tithi×vāra pairs**, which is a
real, honest divergence surface (not the `"state": "none_computed"` honestly-empty state
ADJUDICATION-8 shipped in the interim). Whether a candidate's Agnivāsa grading should ever
*consult* Convention (B) — versus reporting it purely as comparative/research data alongside the
native-confirmed Convention (A) — is a separate design question for that builder session, not
resolved here.

## Reversibility

**TOTAL.** This is a single `kala_paddhati_profile` row's `convention_status`/`provenance`/
`corpus_gap_ref` field update — versioned config data, delete-then-insert per chart per §N.3,
no code change, no schema change, no writer change, no orchestrator involvement. It can be
reverted to `declared_not_computed` by a single row update with zero blast radius. No existing
election result depends on Convention (B) since it has never been served or computed before
this ruling.

## FROZEN-contract / untouchable / rail check

**Does not touch any of them.** This is a data/doctrine ruling about the *content* of one
`kala_paddhati_profile` convention row, sourced from a translated corpus verse. It does not:
- touch the FROZEN orchestrator contract (`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2`, CLAUDE.md
  §N.2) — no `WriterBase` subclass is created or modified by this ruling;
- touch any migration, schema, or code file — the recommended data change in the section above is
  a recommendation for a future builder session, not an action this docs-only ruling performs;
- touch `content_sa` (immutable, unread and unwritten by this ruling) or re-open the translation
  task's own closed scope;
- override or alter Convention (A) or the native's confirmed lineage-practice ruling
  (ADJUDICATION-8 part 1, the hard-constraint rule) in any way.

## Rationale

ADJUDICATION-8 (`SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`, ruling parts 2–3) · NATIVE
CONFIRMATIONS items 1 and 3 · `MUHURTA_CHINTAMANI_TRANSLATION_REPORT_v1_0.md` §3(a), §6 · CLAUDE.md
B.3 (derivation-ledger — this ruling cites the exact `chunk_id` and DB row it derives from) · B.8
(versioning/no-duplicate-registry — hence the 14→16 numbering correction) · B.10 (no fabricated
computation — the rule above is a direct citation, not an invention) · brief §7 honest-empty rail
(superseded here by an honest-computed finding, not by an invented one).

---
*End of ADJUDICATION-16 v1.0.*

---
artifact: BRAHMA_CORPUS_DEFERRED_v1_0.md
canonical_id: BRAHMA_CORPUS_DEFERRED
version: 1.0
status: OPEN
created: 2026-06-20
layer: L0 / Brahmagyan
origin: L2 Bodha Post-Seal Closeout C5
purpose: >
  Tracks L0 brahma corpus expansion items surfaced during L2 Bodha buildout.
  These are corpus/schema gaps for future axes that bo_upaya v1 does not attempt.
  None block L2 close or L3 Kāla start. Do NOT fabricate remedy rows to fill these.
---

# L0 Brahma Corpus — Deferred Expansion Items

## Context

During L2 Bodha buildout (`feature/l2-bodha`), `bo_upaya` v1.0 built its remedy
prescription layer using a **planet-only lookup**:

```sql
SELECT ... FROM brahma_remedy_corpus
WHERE lower(planet) = %s AND scaffold_status = 'live'
ORDER BY confidence DESC NULLS LAST
LIMIT 5
```

All 9 canonical grahas have live corpus rows (261 total across 9 planets). The writer
produced **135 prescriptions** (3 per graha × 5 ayanamshas × 9 grahas) and wrote
**45 resonance rows** — all rows honest and grounded.

**What bo_upaya v1 does NOT do (and does not claim to do):** it does not look up
remedies by nakshatra, vastu direction, body-part, or chakra axis. The corpus has no
columns for these axes; the writer has no code path for them. There is no
`remedy_corpus_gap` flag in the schema because the v1 design does not attempt those
lookups — absence of attempt is not the same as a flagged gap.

The items below represent **future corpus + schema expansion work** needed before
a future `bo_upaya v2` could cover these remedy axes. Tracked here as an explicit
deferred register so nothing is silently lost.

---

## Open Items

### B-DEFER-C5-1: Nakshatra-keyed remedies absent from corpus

- **Gap:** `brahma_remedy_corpus` has no `nakshatra` or `nakshatra_key` column.
  Classical tradition (BPHS, Muhurta Chintamani, Jataka Parijata) prescribes
  nakshatra-specific remedies (e.g., nakshatra deity puja, nakshatra-matched mantra).
- **Current state:** 0 nakshatra-keyed rows. The corpus is indexed by `planet` and
  `domain` only. bo_upaya v1 does not query by nakshatra; no rows are missed in v1,
  but the axis is entirely absent.
- **Impact on bo_upaya v1:** None — v1 doesn't attempt nakshatra lookups.
- **Impact on a future bo_upaya v2:** A nakshatra-axis lookup would return 0 rows;
  any gap-flagging logic would fire for all 27 nakshatras.
- **Action (future L0 corpus-expansion pass):**
  1. Add `nakshatra` column to `brahma_remedy_corpus` schema (migration).
  2. Seed nakshatra-specific remedy rows for the 27 nakshatras (classical research + data entry).
  3. Update bo_upaya v2 to include a nakshatra-axis lookup path.
- **Owner:** L0 corpus-expansion pass (post-L2 close; pre-bo_upaya v2).
- **Blocks:** bo_upaya v2 nakshatra-axis coverage.

---

### B-DEFER-C5-2: Vastu-direction remedies — 0 rows in corpus

- **Gap:** `brahma_remedy_corpus` has 0 rows with `domain` matching any vastu concept.
  Confirmed: `SELECT COUNT(*) FROM brahma_remedy_corpus WHERE domain ILIKE '%vastu%'` → 0.
  The corpus does not contain a `vastu_direction` key column either.
- **Current state:** L1 `chart_facts` has a `ga_vastu` asset (40 rows for `482012f1`)
  mapping grahas to vastu directions (N/NE/E/SE/S/SW/W/NW). bo_upaya v1 does not
  attempt to map those directions to remedies; no connection exists.
- **Impact on bo_upaya v1:** None — v1 doesn't attempt vastu-direction lookups.
- **Impact on a future bo_upaya v2:** A vastu-direction lookup would return 0 rows for
  all 8 directions; gap-flagging logic would fire universally.
- **Action (future L0 corpus-expansion pass):**
  1. Add `vastu_direction` column (or domain tag) to `brahma_remedy_corpus`.
  2. Seed vastu-direction remedy rows (Vastu Shastra + Jyotish tradition sources).
  3. Update bo_upaya v2 to join ga_vastu → brahma_remedy_corpus on vastu_direction.
- **Owner:** L0 corpus-expansion pass.
- **Blocks:** bo_upaya v2 vastu-direction coverage.

---

### B-DEFER-C5-3: Body-part-keyed remedies absent from corpus

- **Gap:** `brahma_remedy_corpus` has no `body_part` or `body_part_key` column.
  L1 `chart_facts` has a `ga_medical` asset (45 rows for `482012f1`) mapping grahas
  to Ayurvedic body-part associations. bo_upaya v1 does not attempt to use this.
- **Current state:** 0 body-part-keyed remedy rows. Only 1 `ayurvedic` remedy_type row
  exists in the live corpus, and it is indexed by planet, not body-part.
- **Impact on bo_upaya v1:** None — v1 doesn't attempt body-part lookups.
- **Impact on a future bo_upaya v2:** A body-part-axis lookup would return 0 rows;
  gap-flagging logic would fire for all graha-body-part pairs.
- **Action (future L0 corpus-expansion pass):**
  1. Add `body_part` column to `brahma_remedy_corpus` schema (migration).
  2. Seed body-part remedy rows (Ayurvedic Jyotish — Ashtanga Hridayam, Charaka Samhita
     planet-body mappings; classical Jyotish body-part remedials).
  3. Update bo_upaya v2 to join ga_medical → brahma_remedy_corpus on body_part.
- **Owner:** L0 corpus-expansion pass.
- **Blocks:** bo_upaya v2 body-part/medical-axis coverage.

---

### B-DEFER-C5-4: No chakra table in DB schema

- **Gap:** No `brahma_chakra_*` or similar chakra table exists in the DB.
  Confirmed: `SELECT table_name FROM information_schema.tables WHERE table_name ILIKE '%chakra%'` → 0 rows.
  Chakra-graha mapping (e.g., Sun → Manipura, Moon → Svadhisthana) is a recognised
  Jyotish-Tantra remedial axis absent from the entire schema.
- **Current state:** The schema has no chakra concept at any layer (L0 through L2 built).
- **Impact on bo_upaya v1:** None — v1 has no chakra code path.
- **Impact on a future bo_upaya v2:** Cannot produce chakra-axis remedy prescriptions
  until schema + corpus are added.
- **Action (future L0 corpus-expansion pass):**
  1. Design `brahma_chakra_catalog` schema (chakra_id, chakra_name, associated_grahas_array,
     associated_domains_array, activation_mantra, yantra_jsonb, classical_refs).
  2. Seed 7-chakra corpus with graha associations + classical remedy references.
  3. Add `chakra_id` FK to `brahma_remedy_corpus` (optional — or separate corpus table).
  4. Update bo_upaya v2 to include a chakra-axis prescription path.
- **Owner:** L0 corpus-expansion pass + schema design session.
- **Blocks:** bo_upaya v2 chakra-axis coverage.

---

## Disposition

All 4 items are **corpus-expansion items, NOT build bugs and NOT bo_upaya v1 failures.**

- `bo_upaya` v1.0 makes no false claims about these axes — it does not attempt nakshatra,
  vastu-direction, body-part, or chakra lookups and therefore produces no incorrect output.
- The 135 prescriptions written are honest, planet-grounded, and fully corpus-cited.
- No `remedy_corpus_gap` column was added to `bodha_rm_remedy_prescriptions` because
  v1 does not attempt the missing lookups — a gap flag requires a lookup attempt first.
- **None of these items block L2 close or L3 Kāla start.**
- A future L0 corpus-expansion session should address B-DEFER-C5-1 through C5-4 before
  authoring a `bo_upaya v2` spec that claims coverage on these axes.

| ID | Axis | Schema missing | Corpus rows | Blocks |
|---|---|---|---|---|
| B-DEFER-C5-1 | Nakshatra-key | Yes (`nakshatra` column) | 0 | bo_upaya v2 nakshatra path |
| B-DEFER-C5-2 | Vastu-direction | Yes (`vastu_direction` column) | 0 | bo_upaya v2 vastu path |
| B-DEFER-C5-3 | Body-part-key | Yes (`body_part` column) | 0 | bo_upaya v2 medical path |
| B-DEFER-C5-4 | Chakra | Yes (entire table) | 0 | bo_upaya v2 chakra path |

*End of BRAHMA_CORPUS_DEFERRED_v1_0.md v1.0 (2026-06-20 — initial, C5 post-seal closeout)*

# bg_vastu_directions: row diff for Citation Pass 2 (decision OS-2026-10-05-CITATIONS)

Natural key: direction. Seed: `platform/python-sidecar/brahmagyan/l0_vastu_directions.py` (`VASTU_DIRECTIONS`, 8 rows; `VASTU_DIRECTION_REMEDIALS`, 24 rows).

| | before | after |
|---|---|---|
| bg_vastu_directions rows | 8 | 8 |
| bg_vastu_direction_remedials rows | 24 | 24 |
| added | | 0 |
| removed | | 0 |
| changed (directions) | | 1 (Southwest) |
| changed (remedials) | | 0 |

Changed column: `classical_citation` only. `favorable_color` stays NULL (the decision: no source, do not invent). Direction, direction_deg (225), ruling_graha (Rahu), secondary_graha, element (Earth) and the row `id` are unchanged.

## Changed row: Southwest
- **classical_citation** before: `Vastu Shastra tradition (Nairitya corner)`
- **classical_citation** after: `K1 — Muhurta Chintamani Gocara-prakaraṇa v.9 ṭīkā — muhurta_chintamani:PG66:C1 — "Mars's coral in the south, Rāhu's gomeda in the nairṛtya (south-west), Saturn's blue sapphire in the west" ; K1_ANALOGUE — Hora Sara Ch.2 translator's direction table — hora_sara:PG16:C1–PG17:C1 — "Rahu — South West (as per Brihat Jataka, Ch. II, sloka 6)" ; NOTE — Brihat Jataka II.6 mūla page not located in corpus this pass`

## Readers
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_vastu_directions.ts` selects the row and serves `classical_citation` verbatim (no branch on its text); its tool description still says "Mayamata" for the table as a whole (not changed here).
- `ga_vastu` reads the direction-to-graha map as the L0 authority (`tests/test_ifl1_ga_vastu_direction_map_reads_l0_authority.py`); no citation text is read.

## Left alone on purpose (not in the decision)
- The Southwest REMEDIAL row (`bg_vastu_direction_remedials`) cites the same bare label `Vastu Shastra tradition (Nairitya corner)`; other remedial rows cite `Vastu Shastra tradition`, `Mayamata Ch.6`, `Brihat Samhita Ch.53`. The decision covers only the direction row.
- The seven sibling direction rows citing `Vastu Shastra (Mayamata Ch.6)` (Mayamata is not in the corpus): the pass-2 record recommends re-pointing them to the same loci (recommendation 5, not a decision). Listed for SS in `E5.7/CITATION_AMBIGUOUS.md`.

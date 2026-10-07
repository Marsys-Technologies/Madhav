# bg_yogas (brahma_yoga_catalog): row diff for Citation Pass 2 (decision OS-2026-10-05-CITATIONS)

Natural key: canonical_id. Seed: `platform/python-sidecar/brahmagyan/l0_yogas.py` (`YOGAS_CORE`, inline; the table also holds detector rows and rows extracted from the corpus at build time, none of which change).

| | before | after |
|---|---|---|
| catalog / ontology (yoga) / reference rows | 233 / 233 / 233 | 233 / 233 / 233 |
| inline + detector seed rows | 148 | 148 |
| added | | 0 |
| removed | | 0 |
| changed | | 1 (`kala_sarpa_yoga`) |

Changed columns of the catalog row (the ontology and reference projections of the row are NOT changed: `brahma_ontology.source_citation` still reads the classical-lineage label, see `E5.7/CITATION_AMBIGUOUS.md`): `school`, `cancellation_conditions`, `classical_citations`.

## Changed row: kala_sarpa_yoga
- **school** before: `parashari` -> after: `modern`
- **cancellation_conditions** before: `{"bhanga": ["a_planet_outside_the_axis", "strong_benefic_kendra"]}`
- **cancellation_conditions** after: `{"bhanga": ["a_planet_outside_the_axis", "strong_benefic_kendra"], "notes": "duplicate of dosha kala_sarpa; not fired by ga_yoga_writer (R6A.2)"}`
- **classical_citations** before: `[{"text_id": "classical_tradition"}]`
- **classical_citations** after: `[{"kind": "K2", "decision_id": "OS-2026-10-05-CITATIONS", "label": "modern practice / project judgment", "note": "not a classical source; duplicate authority: ga_yoga_writer deliberately does not fire this relation; the dosha-form kala_sarpa in ga_structural_writer is the single authority (R6A.2)"}]`

## Readers
- `ga_writers/ga_yoga_writer.py` loads school and classical_citations into the catalog dict; it does not fire this relation (R6A.2) and does not branch on the citation text.
- `routers/yoga_formation_band.py::_citations` lists `text_id[:chapter]` per entry and skips entries without a `text_id`: a K2-only column lists no classical citation (covered by a test).
- `brahmagyan/l0_rules.py` resolves the Tier-1 name "Kala Sarpa" to this canonical_id (kept; retirement of the relation is the yoga-catalog owner's call).
- The reseal (migration 1322) computes the new catalog pin from the live table: the corpus-extracted rows cannot be derived offline, so no `expected_post_fingerprint` is declared in the expected-change file.

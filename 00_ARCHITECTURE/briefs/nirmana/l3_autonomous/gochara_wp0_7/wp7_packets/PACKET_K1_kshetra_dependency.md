---
artifact: WP7_PACKET_K1
packet_id: K-1
version: "1.0"
status: DESIGN_ONLY_NOT_IMPLEMENTED
date: 2026-09-23
owner: "Owner of services/ka_kshetra (registry edge + stage4/writer provenance pinning)"
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §6.2 K-1, §6.3 (ka_kshetra.depends_on row), §9 Kṣetra note, finding F-18; GOCHARA_RULING_SHEET_v1_0.md N-10 (COALESCE removal)
authority_note: "Owed to its owner. Anchors read at this checkout: stage4_field.py:1372-1393 (load_legacy_crosscheck — the authority-filtered windows read + the COALESCE fall-through at :1386-1389); writer.py:948-953 and :1059-1064 (provenance edges pinned source_table='kala_gochara_windows', source_pk=str(row['id'])); writer.py:2324-2335 (_gochara_corpus_pin's own COALESCE(...,'v1') at :2328-2330)."
---

# K-1 — Kṣetra: declare the gochara edge, pin provenance by `(generation, id)`, remove the `'v1'` fall-through

## The one-paragraph requirement

Kṣetra reads the served gochara windows **undeclared** and pins what it reads by bare
row id: `stage4_field.py:1372-1393` (`load_legacy_crosscheck`) selects
`id, window_start, window_end, peak_date, temporal_shape FROM kala_gochara_windows WHERE
chart_id = %s AND event_class = %s AND generation = COALESCE((SELECT
authoritative_generation FROM kala_gochara_authority WHERE chart_id =
kala_gochara_windows.chart_id), 'v1')` while the registry's `ka_kshetra.depends_on`
lists `ka_gochara_resonance` but not `ka_gochara` (F-18), and `writer.py:948-953` /
`:1059-1064` store the resulting provenance edges as
`source_table='kala_gochara_windows', source_pk=str(row['id'])` — a bare row id that
says nothing about which generation the row belonged to, so a later disposition of
`'3.0'` (or any authority flip) silently orphans every edge whose target id belonged to
the wrong generation. Three fixes, all Kṣetra-owned: **(1)** declare `ka_gochara` in
`ka_kshetra.depends_on` (registry change by migration, N-9) and — per the Kṣetra
packet of 2026-09-23 adopted by plan §6.2 — `ka_vedha_gochara` as well, which Kṣetra
will consume **after one cross-check generation** (declare the edge now, consume after
the cross-check proves the overlay contract, so the declaration never lags the read
again); **(2)** pin the edges by `(generation, id)` — store the generation in the edge
(`term_key` or a parallel column; e.g. `term_key=f'gate:legacy_sweep_xref:{generation}:{row["id"]}:{agreement}'` and `source_pk` carrying `f'{generation}:{id}'`, or a `contact_id` where the window's `active_sentences` names one) so a disposition of one generation cannot orphan references that were honest when written — the `'3.0'` rows persist through WP10 precisely so these edges stay resolvable, but only the generation-qualified pin makes that durable; **(3)** remove Kṣetra's own `'v1'` COALESCE fall-throughs — in `load_legacy_crosscheck` (`:1386-1389`) and identically in `_gochara_corpus_pin` (`writer.py:2328-2330`) — so an absent authority row yields `unpublished` (honest "nothing authoritative is served") instead of a silent `'v1'` assumption that would misfingerprint the field hash the moment a chart is genuinely unflipped (N-10's P-1d/K-1 ruling; the crosscheck simply returns no rows for an unflipped chart, and `_gochara_corpus_pin` records the `unpublished` sentinel into the pin).

## Acceptance

Registry diff shows both edges; a fixture with authority `'4.0'` produces edges whose
pin includes `generation='4.0'`; a chart with **no** authority row produces zero
crosscheck rows and a corpus pin naming `unpublished` — and no code path anywhere in
Kṣetra still contains `COALESCE((SELECT authoritative_generation …), 'v1')`.

## What this packet does NOT do

- It does not change what Kṣetra writes to `kala_field_windows` or the gate-edge
  semantics (`agree`/`diverge` classification is untouched).
- It does not consume Vedha rows yet — the edge is declared ahead of the one
  cross-check generation, per plan §6.2; reading starts only after that generation
  validates the overlay contract.
- It does not touch `kala_gochara_authority`'s schema (527's table unchanged) and does
  not delete or re-point any existing `'3.0'` provenance edge — old edges remain valid
  because their generation is now recorded.

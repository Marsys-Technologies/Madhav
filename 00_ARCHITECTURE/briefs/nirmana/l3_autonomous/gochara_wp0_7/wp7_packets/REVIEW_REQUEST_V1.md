# REVIEW REQUEST — WP7 Packet V-1

**Packet:** `PACKET_K1_V1_kshetra_sangam_deps.md` (V-1 half)
**Branch:** `l3/gochara-autonomous-wp0-7`
**Scope:** ka_sangam undeclared table read — declaration only.

## Finding

`pipeline/orchestrator/writers/ka_sangam.py:1060` reads `kala_vedha_gochara`
(`SELECT graha, window_start, window_end … WHERE vedha_kind = 'house_vedha'`) inside
`sp_enrichment_vedha` — a table owned by asset `ka_vedha_gochara` — with no
corresponding edge in `asset_registry.depends_on`. This is the undeclared-read defect
the packet describes; per the packet, the fix is **declaration only** — no change to
`ka_sangam.py`.

## What changed

- Migration `platform/migrations/1084_wp7_k1_v1_registry_edges.sql` (shared with K-1):
  `ka_sangam.depends_on += ka_vedha_gochara`, idempotent (`AND NOT (depends_on @> …)`),
  BEGIN/COMMIT, DOWN comment, per the 569 convention.

## Packet-vs-codebase mismatch (flagged, not silently worked around)

The packet asks to (a) record the ka_sangam→ka_vedha_gochara edge role as **service**
("re-type as service") and (b) treat the ka_kshetra→ka_gochara edge as
**counterevidence**. **`asset_registry.depends_on` is `text[]` — there is no edge-role
column anywhere in the schema** (verified by grepping migrations). Roles therefore
cannot be stored. Resolution taken: edges declared as plain `depends_on` entries; the
role semantics are recorded in the migration's header comment and here:

- `ka_kshetra → ka_gochara` : counterevidence (cross-check corpus)
- `ka_kshetra → ka_vedha_gochara` : service (authority seam)
- `ka_sangam → ka_vedha_gochara` : service (table read)

If roles are required as data, a schema change (e.g. an `asset_edge_roles` table) is
needed — that is beyond this packet's declaration-only scope.

## Acceptance: "no undeclared table read in ka_sangam.py"

Grep-based closure walk over `pipeline/orchestrator/writers/ka_sangam.py` FROM clauses:
`kala_activation_predicates`, `bodha_msr_signals`, `kala_convergence` (own output),
`build_substep_progress`, `chart_facts`, `public.charts`, `chart_dashas`,
`l1_tajik_varsha_year_lords`, and `kala_vedha_gochara`. With this migration the only
cross-asset gochara-family read (`kala_vedha_gochara`) is now declared. The remaining
cross-asset reads (e.g. `l1_tajik_varsha_year_lords`, `chart_dashas`) predate this
packet series and are outside V-1's scope; not audited here.

## Verification

- Static only (no live DB): migration is idempotent SQL following an existing merged
  convention; asset `ka_vedha_gochara` confirmed present in registry migrations
  (e.g. `migrations/670_nirmana_l3_w3_integrity_contracts.sql:1645`).
- Python suite green after the shared commit's edits: 720 passed (see REVIEW_REQUEST_K1.md).

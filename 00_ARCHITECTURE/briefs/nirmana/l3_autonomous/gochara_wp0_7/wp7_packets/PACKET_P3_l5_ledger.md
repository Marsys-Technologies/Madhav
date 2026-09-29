---
artifact: WP7_PACKET_P3
packet_id: P-3
version: "1.0"
status: DESIGN_ONLY_NOT_IMPLEMENTED
date: 2026-09-23
owner: "Owner of the L5 Mīmāṃsā ledger (mi_* tables + platform/src/lib/lel/prospective_ledger.ts)"
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §6.2 P-3, §4.6 (identity chain), §6.1 (L5 ledger row); WP0_FINDINGS.md consumer item 8
authority_note: "Owed to its owner. Anchors read at this checkout (l3/gochara-autonomous-wp0-7 @ fd13ec0a6; pin c58e86662 ancestor, source identical)."
---

# P-3 — L5 ledger: `contact_id` for frozen-claim identity

## The requirement (one paragraph)

Every engine-generated claim the L5 layer freezes — in `mimamsa_predictions`
(migration `brahma_mimamsa_prediction_ledger.sql`; also the WP0 finding-8 coupling at
`platform/src/lib/lel/prospective_ledger.ts:164,170,208,252,498`, whose docstrings name
`kala_gochara_windows` as the template for a claim's configuration signature) — needs a
nullable **`contact_id TEXT`** column carrying the `sha256:<hex>` id from
`WP1_CONTRACTS.md` §3.2 when the claim rests on a specific Gochara contact, alongside
the existing `configuration_signature` (mandatory for `generator_class='engine'`,
enforced at `prospective_ledger.ts:491-500`). The identity chain is:
`contact_id` (one episode in `kala_gochara_contacts`, immutable per §4.7) →
`window_id` + `parent_window_id` (the refinement projection rows that cite the contact
in `active_sentences`, plan §4.6) → `manifest_id` (the `kala_gochara_publication` row
for (chart, generation), which authority's `evidence_ref` will name at WP10). Because a
tolerance or method change always implies a new `convention_id` and therefore new
contact ids (WP1_CONTRACTS §1.1, §9), the frozen claim's id can never silently come to
name a different computation — a claim filed against `contact_id X` is either about
exactly that episode under exactly that convention, or its id mismatch is detectable;
this is what lets L5 answer "is this the same claim it was when filed?" (Q01) across
rebuilds, republishes (`'4.0'` → `'4.1'`), and rollbacks, without re-deriving anything
from dates or degrees that drift.

## Where it plugs in (for the owner)

- **Schema:** additive nullable column on `mimamsa_predictions` (and the
  `brahma_prospective_ledger` row shape at `prospective_ledger.ts:119-143` /
  `INSERT` at `:527-556`: add `contact_id` to the column list, defaulting NULL).
  Nullable because most claims are not gochara-contact-anchored; non-gochara claim
  paths are untouched.
- **Filing path:** `fileProspectivePrediction` accepts `contact_id?: string` in
  `FileProspectivePredictionInput` (`:92-118`); when present, validate format
  (`sha256:<64 hex>`) and that `(chart_id, generation, contact_id)` resolves in
  `kala_gochara_contacts` at filing time (a dangling id is rejected, not stored — a
  frozen claim pointing at a nonexistent episode is the F-18 orphan class one layer up).
- **Outcome matching:** `record_outcome()` gains nothing structurally, but the claim's
  frozen `contact_id` lets outcome review pull the episode's `t_exact`, orb, and
  `completeness_state` for post-hoc inspection without re-serving the projection.

## Acceptance test

File an engine claim with a real fixture `contact_id`; assert the returned row carries
it; assert a second filing with a tampered id (one hex char changed) is rejected; assert
a claim filed before the column existed (migration-time backfill: NULL) still reads and
matches outcomes.

## What this packet does NOT do

- It does not change `configuration_signature` semantics or the confidence/falsifier
  invariants (open-interval CHECK, mandatory falsifier).
- It does not make `contact_id` mandatory — only engine claims *about a specific
  contact* carry it.
- It does not grant L5 write access to gochara relations; the filing-time existence
  check is a SELECT.
- It does not touch `kala_gochara_contacts` (owned by the gochara writer).

---
artifact: L3_FAMILY_COORDINATION
canonical_id: L3_FAMILY_COORDINATION
version: "1.0"
status: CURRENT
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
scope: "Coordination between the Gochara elevation (Pravāha) and the sibling L3 consumers — Kṣetra and Saṅgam — under the frozen design specs (B3.2) and the B3.1 amendment. This note binds Stream B's specs; it does not commit Kṣetra or Saṅgam to anything — their owners confirm."
references: "design/GOCHARA_DESIGN_SPECS_v1_0.md · design/GOCHARA_PLAN_V3_AMENDMENT_v1_0.md §4 · plan v2.1 §6.2 (S-1/S-2, K-1/V-1) · Kṣetra packet PR #2722 (l3/kshetra-elevation @ 29bddaa2b) · Saṅgam M-3 ruling at 101046052"
---

# L3 family coordination — Gochara ↔ Kṣetra ↔ Saṅgam

## 1. What changes for the siblings, in one paragraph

Gochara's output is no longer a flat per-target score table. It becomes **three objects**
(physical contacts · relationship records · evaluated windows) with explicit frames, coverage and
lineage (specs §0/§1/§10). Everything Kṣetra and Saṅgam consume rides on those objects: the
contact ledger, the coverage manifest, the directed-event stream (S-2), and the vedha overlay
whose temporal structure is now preserved. The consumers' declared dependencies (K-1, V-1)
survive unchanged in form; what flows through them changes shape exactly where the sealed
doctrine found defects.

## 2. The aspect-direction fix and its blast radius (S-2 gate)

The shipped kernel mirrors Mars's 4th/8th and Saturn's 3rd/10th aspects (`target + angle` instead
of `body = target − angle`; Jupiter's labels swap but its root set survives; the 7th survives) —
v3.0 finding #13, confirmed by both external reviewers with independent arithmetic. **Directed
graha-dṛṣṭi events are wrong until A2.1 (Tier 0-G) lands.**

Consequences for Saṅgam (whose M-3 ruling made this stream the producer of directed contact
events):

1. **Saṅgam consumption of directed events stays gated until the post-T0-1 kernel emits them.**
   Any event stream produced before the fix carries mirrored Mars/Saturn directions; consuming it
   would import the defect into Saṅgam's E1/E3 tiers.
2. When the gate lifts, S-2 events carry: full Parāśari directed dṛṣṭi with the Mars/Jupiter/
   Saturn specials **at full strength** and ordinary aspects **graduated ¼/½/¾/full** at
   3-10/5-9/4-8/7 (`BPHS1:16496-16502` — counted in v3.0 §8); `planet` as a list of grahas that
   fired; **absent when nothing fires** (never a zero standing in for silence); grain, coverage
   and `contact_id` on every event; nodes excluded from the dṛṣṭī families (N-14) while remaining
   agents and targets.
3. The S-1 interface keeps `find_aspects` shape-compatible for the duck-typed callers
   (`kala_trigger/trigger.py:96,150,199`, `kala_admission/currents.py:59` — F-25); the enriched
   stream arrives as `find_episodes`. Saṅgam's own symmetric aspect set
   (`ka_sangam/engine.py:464`) is superseded by the per-graha classical table the kernel already
   carries — flagged to Saṅgam's owner as G-7 in plan v2.1, still open.

## 3. The relationship record — what consumers should expect

- **Frames are explicit everywhere.** A contact no longer implies a house interpretation; the
  relationship record carries `frame` (moon | lagna | graha:X | dasha_lord | bhavat_bhavam:house)
  and the count is computed from it. Kṣetra's three-consumer overlay contract and any Saṅgam
  tier that reads "transit in house N" must read the record's frame, not infer one.
- **Coverage is a first-class object.** Absent coverage reads as `unavailable` with the coverage
  manifest attached — never as a clean 1.0 (E2's 1.26 %-of-century overlay defect). Consumers
  must propagate `unavailable`, not flatten it.
- **Role edges, not independent observations.** Jupiter-as-kāraka and Jupiter-as-9L are edges on
  one `contact_id`. Any consumer that corroborates across Gochara signals must dedupe on
  `contact_id` or it will double-count one physical event.
- **Vedha becomes an interval relation** (specs §5): active / vipareeta-cancelled / inactive
  states with real overlap intervals and the two exception pairs (Sun↔Saturn, Moon↔Mercury).
  The three-consumer contract's `source_qualification` and `precision_regime` fields survive;
  the *values* change where today's writer collapsed temporal structure (N4). Re-citation against
  Phaladīpikā Adh. XXVI (G-9; production already at 36 verse-cited + 6 UNSOURCED node rows) means
  the uniform `unqualified` some sheets adopted is lifted row by row as the stamp lands.

## 4. Lineage and invalidation

Re-solve vs re-score (specs §10): weight/valence/path changes re-score windows from stored
contacts; aspect direction, frame-dependent resolution, target-generation and support-domain
changes re-solve contacts. **Lineage propagates**: a re-solve invalidates downstream Kṣetra and
Saṅgam rows derived from the affected `contact_id` ranges; the coverage manifest and
`convention_id` (which changes on any tolerance/method change) are the join keys a consumer uses
to know whether its derivation is current. The first such propagation is scheduled: A2.1's
geometry fix re-solves the ledger; `'4.1'` is the post-fix geometric baseline.

## 5. Labels and publication

`'4.0'` is burned on chart 1 (ADK-0027); `'4.1'` is candidate-only forever (D-41); the first
sound candidate is `'5.0'`. Consumers must read authority and provenance **from the publication
manifest** (N-10), never from string-matched generation branches — the P-1 test (provenance
unchanged across a republish) is the conformance check. An absent authority row means
`unpublished` (the `'v1'` COALESCE fall-through is removed; K-1 carries the same removal for
Kṣetra).

## 6. Open items for the sibling owners (not ruled here)

| Item | Owner | Note |
|---|---|---|
| G-7 symmetric aspect set at `ka_sangam/engine.py:464` | Saṅgam | adopt the per-graha table via S-2 events |
| Saṅgam E1/E3 ungate after T0-1 events land | Saṅgam | gated since the M-3 ruling |
| K-1: Kṣetra consumes `ka_vedha_gochara` after one cross-check generation | Kṣetra | vedha interval relation (§5) is the new shape to cross-check |
| Node convention (N-4a): mean-node derivation owned by L0, `node_mode`/`epoch_convention` on the row | L0 | all three consumers record the result in their convention vectors |
| G-10 per-contributor BAV matrix | L1 | P5c kakṣyā qualification declares sign-level BAV as the coarser operand until this lands |
| Corpus admission questions routed N-4a/G-9 were to be ruled **once** for both streams (plan v2.1 cross-stream pointer) | native/steward | D-RQ3/D-RQ8 now carry the Gochara half; Kṣetra's sheet should reference them rather than re-ask |

## 7. Standing discipline for cross-stream claims

Any claim one stream makes about another's data carries file:line or a count with its predicate
(F-32); a consumer reading Gochara's "no window" answer must read the coverage object before
calling it "nothing happened"; honest null over plausible default (ADK-0026) applies to every
derived row a sibling writes from Gochara inputs.

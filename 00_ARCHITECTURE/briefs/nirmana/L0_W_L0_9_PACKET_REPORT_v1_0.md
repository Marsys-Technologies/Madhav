---
artifact: L0_W_L0_9_PACKET_REPORT
version: 1.0
status: CURRENT — packet reported with one open design ruling
packet: W-L0-9 (Identity uniqueness and the missing classes)
session: l0/nirmana-elevation-20260921 execution session (worktree /Users/Dev/madhav-l3/l0-exec)
date: 2026-09-25
plan: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §1.3 seam 1, §2.4, §4.2 W-L0-9
companion: L0_W_L0_9_IDENTITY_UNIQUENESS_DESIGN_PROPOSAL_v1_0.md
---

# W-L0-9 Packet Report — Identity uniqueness and the missing classes

Per-packet report per the kickoff. The packet has three parts: the 11-duplicate
repair (design question — proposed, not picked), the relation-type class (decided
in §2.4 — executed), the Bhavat Bhavam scope object (decided in §2.4 — found
already L0 data; closure proposed).

## Part 1 — the 11 duplicates: PROPOSED, awaiting the design ruling

**Detector before (live, today):** `brahma_ontology` 741 rows / 730 distinct
canonical_ids / 11 duplicates. Full 22-row inventory verified live and tabulated in
the design proposal §1.

**Key measured fact that reframes the packet:** the key is ALREADY class-qualified —
live constraint `brahma_ontology_canonical_unique UNIQUE (entity_class,
canonical_id)` (ws2_l0_ontology.sql:26); every writer upserts and every integrity
contract joins on the pair; contract 606:100 audits uniqueness as
`(entity_class, canonical_id)`. The real defect is **class-blind readers**:
`resolve_entity.ts:63-73` (alphabetical-first-class wins), `l0_ontology.resolve()`
(first match wins).

**Proposal delivered** (`L0_W_L0_9_IDENTITY_UNIQUENESS_DESIGN_PROPOSAL_v1_0.md`):
Option A (formalize the class-qualified key) + Option C (declared polysemy registry
with fail-closed resolution of registered-ambiguous bare ids), over merge
(destructive to true polysemy: kp, phaladeepika, vyatipata) and re-key (hash-reseal
campaign for no information gain).

**Plan-text defect raised, not worked around:** the packet proof as written —
`count(*) - count(DISTINCT canonical_id) = 0` — cannot pass under A or C; it passes
only under merge or re-key. The proposal asks strategy to amend the detector to the
undeclared-duplicate form (SQL in proposal §3) or to choose differently.

**Detector after:** unchanged (11) by design — no merge, no re-key, no resolver
change without the ruling.

## Part 2 — relation_type vocabulary class: EXECUTED (§2.4 decision)

- **Writer:** 7 entities added to `brahmagyan/l0_ontology.py` (after the aspect_type
  section; `_e()` gained an optional citation param, backward-compatible). Writer
  ownership is derived, so the class is automatically inside
  `ONTOLOGY_OWNED_ENTITY_CLASSES` and survives the scoped DELETE.
- **Migration:** `platform/migrations/1121_l0_ontology_relation_type_class.sql` —
  guarded DO-block, drift-converging ON CONFLICT identical to the writer's, HELD
  pending ledger reconciliation + strategy confirmation of the number (head 1091 +
  this session's 1120 → 1121). **migration-guard: PASS** (byte-identity with the
  writer verified programmatically, 0 mismatches across 35 fields; one header
  wording WARN fixed).
- **Citations:** grounded only (BPHS Ch.26/6/32/27; Jaimini Ch.1; BPHS Ch.28).
  `nakshatra_link` has no in-repo classical citation and cites the §2.4 decision;
  standalone `virodha` is attested only as virodhargala. The argalā 5th-house
  in-repo disagreement (ga_structural_writer [2,4,5,11] vs bo_karanajala {2,4,11})
  is recorded, not silently resolved.
- **Detector tests:** `tests/test_l0_ontology.py` — new `TestRelationTypeEntityClass`
  (4 tests: exact 7-member set, synonyms+citation present, nakshatra_link cites the
  decision not an invented source, writer ownership). **42 passed, 1 skipped**
  (pre-existing real-Postgres skip). Writer dry-run: relation_type 7, owned.
- **Registered side effect:** `relation_type.argala` adds a 12th bare-id duplicate
  (vs `aspect_type.argala`) — included in the polysemy-registry proposal.
- **Handover:** `bg_rules`/L2 *citing* the class (second half of the packet proof)
  is L2 work — recorded for the L1+ stream.

## Part 3 — Bhavat Bhavam scope object: found already L0 data

The scope object exists as registered L0 data: `l0_resource_config_slice_v1.json`
(dispositioned REGISTER under W-L0-1/C-5) carries the 12-cell qualified-frame map,
method `bhavat_bhavam.odd_house_nonrecursive.v1`, prerequisites, exceptions, and
the DIS.016/DR-3 restraint set — with the honest qualification state
UNQUALIFIED_SOURCE / rights UNRESOLVED (no admitted classical witness in-repo; the
KP extraction is differently scoped). Mirrored by `bhavat_bhavam_registry.py` and
`bhavat_bhavam_map.ts` (the latter sourced from the slice).

**Proposal:** declare the registered slice THE L0 scope object; a second DB-backed
copy would create a second authority. No citation was fabricated to force closure.
(Kickoff assigns this to W-L0-9; plan §2.4 row text says W-L0-5 — discrepancy
noted, kickoff followed.)

## Blocks carried forward

1. **Design ruling (strategy/native):** the §3 repair + detector amendment in the
   design proposal. Until ruled, W-L0-9 Part 1 stays open — and W-L0-8 depends on
   it ("a vocabulary cannot be controlled while its identity owner has ambiguous
   keys").
2. **Migration application (consolidation/madhav-65):** 1121 held with 1120 behind
   the unreconciled ledger.

## Packet status

Execution-side work delivered: design proposal written with measured evidence;
decided items (relation-type class, scope-object identification) executed and
tested. The packet cannot fully close until the design ruling lands; proceeding to
W-L0-2 per the mandated order (W-L0-2 has no dependency on the ruling; the
W-L0-9 → W-L0-8 dependency is preserved by not starting W-L0-8).

---
artifact: L0_W_L0_9_IDENTITY_UNIQUENESS_DESIGN_PROPOSAL
version: 1.0
status: PROPOSED — awaiting strategy/native design ruling
packet: W-L0-9 (Identity uniqueness and the missing classes)
session: l0/nirmana-elevation-20260921 execution session (worktree /Users/Dev/madhav-l3/l0-exec)
date: 2026-09-25
plan: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §1.3 seam 1, §2.4, §4.2 W-L0-9
---

# W-L0-9 Design Proposal — brahma_ontology identity uniqueness

The kickoff and the plan are explicit: the repair is a **design question — propose, do
not pick unilaterally**. This document is the proposal. Nothing in §3 has been
executed; §4 and §5 report work that WAS executed because §2.4 already decided it.

## 1 · Measured state (live production, 2026-09-25)

`brahma_ontology`: **741 rows, 730 distinct canonical_ids, 11 duplicates** —
`SELECT count(*), count(DISTINCT canonical_id) FROM brahma_ontology`. The 22 rows
(verified live, full contents):

| canonical_id | classes | reading |
|---|---|---|
| ashtakavarga | concept + school | one system, two framings; the `school` row looks misclassified (a method, not a lineage) — flagged, not touched |
| balarishta | concept + dosha | concept row describes the phenomenon; dosha row is the catalog affliction (BPHS Ch.9) |
| daridra | dosha + yoga | dosha catalog row vs yoga catalog row (PHALADEEPIKA Ch.105) |
| dhaiya | concept + dosha | concept row (Saturn 4H/8H transit) vs dosha catalog row |
| kemadruma | dosha + yoga | dosha catalog row vs yoga catalog row (BPHS Ch.385) |
| kp | dasha_system + school | the KP dasha variant vs the KP school — **two real things** |
| neecha_bhanga_raja_yoga | concept + yoga | concept row vs yoga catalog row (BPHS Ch.39) |
| phaladeepika | school + text | Mantreswara's school vs the text — **two real things** |
| sade_sati | concept + dosha | concept row (7.5-yr transit) vs dosha catalog row |
| sthira_dasha | concept + dasha_system | concept row vs the Jaimini dasha system (86-yr) |
| vyatipata | upagraha + yoga | Sun-derived upagraha vs the Saravali panchanga yoga — **two real things, different computation and source** |

## 2 · What the plan did not record: the key is already class-qualified

Measured in the DDL and the writers, not assumed:

- `platform/migrations/ws2_l0_ontology.sql:26` — live constraint
  `brahma_ontology_canonical_unique UNIQUE (entity_class, canonical_id)`
  (confirmed in `information_schema.table_constraints` today). Duplicate bare ids
  are **legal by design**; the primary identity is the pair.
- **Writers are class-partitioned**: `l0_ontology.py` upserts with
  `ON CONFLICT (entity_class, canonical_id)` and runs a scoped DELETE over
  ontology-owned classes only; the yoga/dosha/dasha_system co-writers
  (`l0_yogas.py`, `l0_doshas.py`, `l0_dasha_systems.py`) DELETE+rebuild their own
  class partitions. The duplicates exist because two writers each registered the
  same name under their own class.
- **Integrity contracts are class-scoped and count/hash-pinned**: migrations
  606/620/621/622/630 (with join-scope fixes 692/700/701) join catalogs to the
  ontology *with* `entity_class` filters and pin exact per-class counts and sha256
  hashes (e.g. 233 yoga rows). Migration 606:100 audits uniqueness as
  `GROUP BY entity_class, canonical_id HAVING COUNT(*)>1` — the composite key,
  deliberately not the bare id.
- **No FOREIGN KEY anywhere**: catalogs (`brahma_yoga_catalog` etc.) carry
  `canonical_id TEXT PRIMARY KEY`; `sutravali_rules.yoga_canonical_id`,
  `bg_parihara_rules.dosha_canonical_id`, `brahma_remedy_corpus.source_canonical_id`
  are loose TEXT. All enforcement is via `integrity_check_sql` contracts.

**Class-blind readers** (the actual defect surface):

1. `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/resolve_entity.ts:63-73` —
   no class filter; on multiple rows `ORDER BY (entity_class='varga') DESC,
   entity_class, canonical_id LIMIT 1`. For the 11 duplicates this means
   **alphabetical-first-class wins** (e.g. `phaladeepika` → school over text). A
   consumer resolving `kemadruma` gets the dosha row and cannot tell it was
   ambiguous.
2. `platform/python-sidecar/brahmagyan/l0_ontology.py:1073-1089` `resolve()` —
   linear scan, first match wins, no ambiguity detection. The ENTITIES mirror
   itself carries `phaladeepika` twice (school :648, text :658) and `kp` (school
   :638; the dasha_system row comes from the co-writer).
3. `l0_reference.py:1417-1438` — class-blind presence set (benign: presence only).
4. Bare-count readers (cockpit stats etc.) — benign.

Class-aware readers (already served by the composite key): `list_entities.ts`
(optional class filter + class aliases), `registry_parity_gate.py`,
`probe_p1_identity.py`, every writer, every integrity contract.

## 3 · The repair — three options from the plan, one hybrid recommended

### Option A — class-qualified key, formalized
Declare `(entity_class, canonical_id)` THE identity (it already is, in DDL, writers
and contracts) and make every class-blind read explicit. Cost: only the class-blind
readers above change. The plan's literal detector
(`count(*) - count(DISTINCT canonical_id) = 0`) **stays at 11** — it measures bare-id
uniqueness, which this option deliberately does not impose.

### Option B — merge
Collapse each pair to one row. For the true-polysemy families (kp, phaladeepika,
vyatipata) this **deletes a real entity**. It also collides with the co-writer
partition model (the dosha writer rebuilds `kemadruma` as a dosha; the yoga writer
rebuilds it as a yoga — a merged row belongs to neither partition and both writers
would fight over it) and breaks the per-class count/hash-pinned contracts
(233/79/20). Rejected: destroys information, fights the writer architecture.

### Option C — declared and enforced polysemy rule
Declare the 11 ids in a **polysemy registry** with a consumer rule: a bare-id
resolution of a registered-ambiguous id must either carry an entity_class or be
refused loudly (fail-closed, the `AmbiguousGrahaIdentity` pattern that already
exists in `l0_semantic_release.py`). Enforcement lands in the two class-blind
resolvers (`resolve_entity.ts`, `l0_ontology.resolve()`). Detector: **undeclared**
duplicates = 0:
```sql
SELECT canonical_id FROM brahma_ontology GROUP BY canonical_id HAVING count(*) > 1
EXCEPT SELECT canonical_id FROM brahma_polysemy_registry;   -- must be empty
```

### Option D (the plan's implicit fourth) — re-key the ids
Make canonical_id itself class-qualified (`kp` → `kp__school` + `kp__dasha_system`
…). The literal detector passes. Blast radius: catalogs' PRIMARY KEYs,
`sutravali_rules.yoga_canonical_id`/`dasha_system_id`, the hash-pinned integrity
contracts (a re-seal campaign per the 1077/1078 pattern), every synonym — for no
information gain over Option C, since consumers already join class-qualified.

### Recommendation: A + C
The DDL, every writer and every integrity contract already treat
`(entity_class, canonical_id)` as the key — Option A is codification, not change.
Family A duplicates (concept↔catalog reflections) and Family B (true polysemy) both
stay representable. The enforced registry (C) fixes the one real defect: **silent**
class-blind resolution. Proposed registry rows: the 11 measured pairs plus
`argala` (relation_type × aspect_type — introduced by §4 below) and resolution rule
"class-qualified citation required; bare resolution of a registered id refuses".

**Plan-text defect to rule on (raised, not worked around):** the W-L0-9 proof as
written — `count(*) - count(DISTINCT canonical_id) = 0` — passes only under B
(destructive) or D (reseal campaign). Under the recommended A+C it must be replaced
by the undeclared-duplicate detector above. Strategy owns this amendment.

## 4 · Relation-type vocabulary class — EXECUTED (§2.4 decided it)

§2.4: "the *relation type vocabulary* (aspect, conjunction, exchange, dispositor,
nakshatra-link, argalā, virodha) is **L0 data** … add the class to `bg_ontology`
under W-L0-9." Detection stays L2. Executed:

- Seven `relation_type` entities added to the ontology writer
  (`brahmagyan/l0_ontology.py`), so the class is durable under the writer's
  upsert + scoped-DELETE regime (writer-derived ownership picks the class up
  automatically; no DDL change needed — `entity_class` is free TEXT).
- Citations are grounded in-repo or honestly absent:
  aspect → BPHS Ch.26 (+ Jaimini Ch.1 for rashi-drishti); conjunction → BPHS Ch.6;
  exchange → BPHS Ch.32; dispositor → BPHS Ch.27 (bhava-bala context, weak —
  recorded as such); argala → Jaimini Ch.1, also attributed BPHS Ch.28 (**in-repo
  disagreement on the 5th house** — `ga_structural_writer.py` ARGALA_OFFSETS
  [2,4,5,11] vs `bo_karanajala.py` {2,4,11}; recorded, not silently resolved);
  virodha → attested only as virodhargala (Jaimini Ch.1 / BPHS Ch.28), standalone
  form per the §2.4 decision; **nakshatra_link → no classical citation anywhere in
  the repo** — the row cites the governing decision itself, per the no-invented-
  source rule.
- Migration **`1121_l0_ontology_relation_type_class.sql`** authored, HELD (same
  regime as 1120: ledger unreconciled; numbering 1121 vs head 1091 + 1120 — to
  confirm with strategy before application).
- Interaction registered: `relation_type.argala` adds a 12th bare-id duplicate
  (vs `aspect_type.argala`) — included in the polysemy registry proposal (§3).
  Synonym-space overlaps with `concept.drishti`/`concept.yuti` pre-date this change
  and are covered by the same resolution contract.
- Not done (handover): `bg_rules`/L2 *citing* the class is L2 work (plan W-L0-9
  proof, second half) — recorded for the L1+ stream.

## 5 · Bhavat Bhavam scope object — found already L0 data; closure proposed

(Kickoff assigns this to W-L0-9; plan §2.4's row text says "Packet: W-L0-5" — the
discrepancy is noted; the kickoff is followed.)

§2.4: the scope object — which derived frames are qualified, under which method,
with which prerequisites and exceptions — is L0 data; application stays L2.

**Finding: the scope object already exists as registered L0 data** —
`brahmagyan/l0_resource_config_slice_v1.json` (dispositioned REGISTER under
W-L0-1/C-5, bound to release `l0.semantic.2026-09-13.1`):
- qualified frames: the 12-cell map — odd primaries only (1→{1,7}, 3→{2,8},
  5→{3,9}, 7→{4,10}, 9→{5,11}, 11→{6,12}); even primaries derive nothing *by
  design* (mirrored in `bodha_writers/bhavat_bhavam_registry.py` MAP_VERSION 1.0
  and `platform/src/lib/jyotish/bhavat_bhavam_map.ts`, the latter sourced from the
  slice);
- method: `bhavat_bhavam.odd_house_nonrecursive.v1`, house-from-house reference,
  lookup-only, non-recursive;
- prerequisites/exceptions/restraints: never-a-generator, no-chaining,
  never-outranks-primary (DIS.016/DR-3 ratified 2026-07-15;
  `DISAGREEMENT_REGISTER_v1_0.md:1035-1114`; code guards in
  `bodha_writers/bhavat_bhavam_amplifier.py`);
- qualification state: **UNQUALIFIED_SOURCE**, rights UNRESOLVED/NOT_ADMITTED — no
  admitted classical witness for the fixed odd-house map exists in-repo (the KP
  extraction in `CONDUCTOR/ws3/kp_canon_batch_03.yaml` is differently scoped).
  This state is kept honest; no citation was fabricated to close it.

**Proposal:** declare the registered slice THE L0 Bhavat Bhavam scope object (a
second, DB-backed copy would create a second authority — the exact defect class
this campaign removes). Strategy confirms, or directs a DB-backed asset.

## 6 · What was NOT done

- No merge, no re-key, no resolver behavior change — §3 awaits the design ruling.
- No migration applied (1121 held); no production write of any kind.
- The `ashtakavarga` school-row misclassification is flagged, not corrected —
  reclassification is doctrine, not cleanup.

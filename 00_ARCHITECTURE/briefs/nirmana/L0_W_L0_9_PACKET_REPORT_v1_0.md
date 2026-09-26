---
artifact: L0_W_L0_9_PACKET_REPORT
version: 1.2
status: CURRENT — Part 1 executed per the ratified design (A+C); production application HELD
packet: W-L0-9 (Identity uniqueness and the missing classes)
session: l0/nirmana-elevation-20260921 execution session (worktree /Users/Dev/madhav-l3/l0-exec)
date: 2026-09-26
plan: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §1.3 seam 1, §2.4, §4.2 W-L0-9
companion: L0_W_L0_9_IDENTITY_UNIQUENESS_DESIGN_PROPOSAL_v1_0.md
changelog:
  - v1.0 (2026-09-25): packet reported with one open design ruling (Part 1 proposed,
    not picked; relation_type class executed; Bhavat Bhavam scope object found
    already L0 data, closure proposed).
  - v1.1 (2026-09-26): the design ruling LANDED — standing mandate Ruling 2 ratified
    Option A + Option C; native Decision 16 (2026-09-26,
    NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8 @ l3, commit 090bd9aaa) independently
    rules the same (composite key stays; consumers become class-aware; the rule-1
    DETECTOR, not the rule, is corrected); ADHIKARIN register ADK-0003 confirms
    Decision 16 covers A + the detector correction, that C is Decision 16 made
    enforceable, and that non-production execution of A+C is within mandate.
    Part 1 executed on this branch: composite key codified, polysemy registry
    migration authored HELD, both class-blind resolvers made fail-closed, detector
    replaced in the registered integrity contract, tests extended. No production
    write of any kind; migration 1125 awaits the Part 5 hard stop with 1120–1124.
  - v1.2 (2026-09-26): PRAMĀṆIN pass-2 corrections amended in place, disclosed —
    (i) the supabase migrations head corrected 1090 → 1092
    (`1092_kala_convergence_target_provenance.sql`; verified by the §-referenced
    origin/* scan; the migration-1125 header itself never carried the error);
    (ii) the Bhavat Bhavam scope-object status flipped ADK-pending → RULED
    (ADK-0007: the registered slice is THE L0 scope object, honest qualification
    state travelling with the designation).
---

# W-L0-9 Packet Report — Identity uniqueness and the missing classes

Per-packet report per the kickoff. The packet has three parts: the 11-duplicate
repair (design ruled 2026-09-26: Option A + C — executed branch-side, production
HELD), the relation-type class (decided in §2.4 — executed), the Bhavat Bhavam
scope object (decided in §2.4 — found already L0 data; closure proposed).

## Part 1 — the 11 duplicates: RULED (Option A + C) and EXECUTED branch-side

**The ruling.** Standing mandate Ruling 2 ratified **Option A + Option C** from
the design proposal; native **Decision 16** (2026-09-26, recorded in
NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8 on l3 and in commit 090bd9aaa)
independently rules the same: the identity key STAYS composite
`(entity_class, canonical_id)`; consumers become class-aware; a consumer
resolving on canonical_id alone is the defect; the data-plane rule-1 detector
(bare `count(DISTINCT canonical_id)`) is corrected, not the rule. **ADK-0003**
(ADHIKARIN register, 2026-09-26) records that Decision 16 covers A and the
detector correction but not the C half (registry table, fail-closed refusal,
undeclared-duplicates detector), that C is Decision 16 made enforceable, and
that branch-local execution of A+C with no production write is within mandate.

**Detector before (live, verified read-only 2026-09-26):** `brahma_ontology`
741 rows / 730 distinct canonical_ids / **11 duplicates** — the bare-id diff
the plan's proof measured. Under A+C this number is deliberately NOT driven to
zero: it sits at 11 forever by design (12 once held 1121 lands argala). The
detector, not the rule, was the defect.

**Detector after (Decision-16-corrected form):** undeclared duplicates = 0 —
```sql
SELECT canonical_id FROM brahma_ontology GROUP BY canonical_id HAVING count(*) > 1
EXCEPT SELECT canonical_id FROM brahma_polysemy_registry;   -- must be empty
```
Registered in `bg_ontology`'s `asset_registry.integrity_check_sql` by migration
1125 (appended to the migration-606 contract text, digest-pinned precondition
`cffc2806…82b7` verified live). **Honesty note:** the detector's production run
awaits the HELD migration — the registry table does not exist in production
(`to_regclass` → NULL, verified 2026-09-26). What WAS verified: (i) live,
read-only — the 11 live duplicate ids are exactly the 11 non-argala seed ids,
so with the 12-id registry the detector passes by construction; the only seeded
id not currently a live duplicate is `argala` (held 1121); (ii) on a scratch
PostgreSQL 15 — migration 1125 applies, re-runs idempotently, its guard refuses
foreign registry rows, and the stored contract text executes TRUE over a 741-row
stub carrying the 11 declared pairs, flips FALSE on an undeclared duplicate, and
returns TRUE once that duplicate is declared.

**What changed (all branch-local; no production write):**

1. **Migration `platform/migrations/1125_l0_ontology_polysemy_registry.sql`
   (HELD).** Creates `brahma_polysemy_registry` (canonical_id PK,
   entity_classes text[], family `'reflection'|'true_polysemy'`,
   resolution_rule, registered_on, decision_ref) and seeds the 12 ids: the 11
   measured pairs + `argala` (relation_type × aspect_type, introduced by held
   1121). Resolution rule text on every row: "class-qualified citation required;
   bare resolution of a registered id refuses". decision_ref cites Decision 16 /
   mandate Ruling 2 / ADK-0003 / the design proposal §3. Families: reflection =
   one phenomenon under two framings (ashtakavarga, balarishta, daridra, dhaiya,
   kemadruma, neecha_bhanga_raja_yoga, sade_sati, sthira_dasha, argala);
   true_polysemy = two real entities (kp, phaladeepika, vyatipata). Idempotent
   (IF NOT EXISTS / ON CONFLICT drift-converge, 606/1121 guard discipline),
   VERIFY + DOWN block included. The same migration carries the two registry-row
   declarations (work item A): `bg_ontology`'s `english_description` now states
   the composite identity and the non-uniqueness of bare canonical_id, and its
   `integrity_check_sql` gains the undeclared-duplicates clause (the detector
   replacement, work item C).
   **Number scan (work item B):**
   `git log --all --diff-filter=A --name-only --format='' --
   'platform/migrations/*.sql' 'platform/supabase/migrations/*.sql'` across every
   origin/* head plus this branch's held 1120–1124 — highest number on any ref is
   **1124** (`1124_nirmana_l0_provenance_completion.sql`, this branch, HELD);
   `platform/migrations/` head otherwise 1091, `platform/supabase/migrations/`
   head 1092 (`1092_kala_convergence_target_provenance.sql`). Next free number
   is **1125** — matches the expected value. (AMENDED 2026-09-26: this line
   originally read "head 1090"; corrected to the measured 1092 after the
   PRAMĀṆIN pass-2 divergence report. Conclusion unaffected.)
   **HELD gate:** production application is a Part 5 hard stop belonging to the
   native, behind the unreconciled `_migrations_applied` ledger (same regime as
   1120–1124).

2. **`resolve_entity.ts` (marsys://tool/L0/resolve_entity) — fail-closed.**
   Was: `ORDER BY (entity_class='varga') DESC, entity_class, canonical_id
   LIMIT 1` — silent alphabetical-first-class on the 11 duplicates. Now: the
   query fetches all matches (optional new `entity_class` input scopes to one
   class); a bare lookup returning >1 row throws `AmbiguousEntityError` naming
   the id and the candidate classes (surfaced as `is_error: true` with the
   registry pointer); class-qualified resolution succeeds within the class;
   multi-row within a supplied class also refuses (same-class synonym
   collision). Single-row and not-found paths are byte-identical. ONE named
   exception, preserved and re-documented, not silently carved: the ADHIṢṬHĀNA
   Lane-A3 declared policy — when the match set contains exactly one
   `entity_class='varga'` row, the varga row wins (keeps the permanent
   regression gate `probe_p1_identity.py`'s D-code checks green; the varga
   class is the authoritative varga-code identity per Lane A3, and the
   additive-only constraint forbids removing the legacy concept-class D<n>
   synonyms).

3. **`brahmagyan/l0_ontology.py` `resolve()` — ambiguity-aware.** Was: linear
   scan, first match wins. Now: collects all matches; 0 → None, 1 → the entity
   (unchanged), >1 → raises `AmbiguousEntityError` (fail-closed twin of
   `AmbiguousGrahaIdentity` in `l0_semantic_release.py`) unless the caller
   passes `entity_class` (resolves within the class) or the Lane-A3 varga
   exception applies (exactly one varga row in the match set — mirrored from
   the TS resolver for py/SQL parity). The ENTITIES mirror keeps both
   phaladeepika rows (school :697, text :707) — data truth, deliberately not
   deduped. Module docstring now carries the identity declaration (composite
   key IS the identity; bare canonical_id not unique, 730/741 + argala,
   verified live 2026-09-26).

4. **`l0_reference.py:1417-1438` — verified benign, left as-is.** It builds a
   bare `canonical_id` presence set for FK-style warnings (planets/signs/
   karakas/upagrahas present in the ontology) — presence-only, never resolves
   an entity; class-blindness is harmless there.

**Callers impacted (grep + tests, both resolvers):**

- Python `resolve()`: the ONLY importer of `brahmagyan.l0_ontology` in the
  sidecar is the writer `pipeline/orchestrator/writers/bg_ontology.py`
  (`seed_ontology` only). No production caller of `resolve()` exists outside
  tests — the strict behavior affects no production path.
- TS `resolve_entity`: no static code callers with fixed names — it is a
  serve-time registry tool (referenced by URI in the agentic adapters, which
  treat it as a tool). Runtime consumers resolving one of the 12 registered
  names bare now receive a loud `is_error` with the candidate classes instead
  of a silently wrong row — that is the intended fail-closed behavior, and the
  refusal message tells the caller to re-call with `entity_class`.
- **Finding (recorded, not silenced):** the mirror/DB carry ~78 multi-match
  terms beyond the 12 registered ids — mostly cross-class *synonym* collisions
  (e.g. `spouse` → domain.marriage + domain.spouse, `transit` →
  concept.transit + concept.gochara, `drishti`/`yuti`/`aspect`/`parivartana` →
  concept × relation_type overlaps pre-dating this change, D-code concept ×
  varga collisions). Under fail-closed, bare resolution of any of these now
  refuses (the varga carve covers exactly the D-code/varga-name cases). This
  is the intended strictness of the ruling — a consumer that was silently
  getting alphabetical-first on `kemadruma` was being served a coin flip — but
  it is a larger blast radius than the 12 registered ids: the unregistered
  synonym collisions are vocabulary hygiene, squarely W-L0-8 territory, and
  are hereby RECORDED as input to it. No exception was carved for any of them.
- The two pre-existing test dependencies on the old behavior were the Lane-A3
  D9 expectations (`test_resolve_d9_prefers_varga_class`,
  `probe_p1_identity.py` varga rung) — both preserved green via the named
  varga exception, not via silence.

**Plan-text defect — disposition.** The v1.0 report raised that the packet
proof as written (`count(*) - count(DISTINCT canonical_id) = 0`) cannot pass
under A or C. Decision 16 corrected the tier-2 §4.1 rule-1 detector on l3 the
same way ("the seal's reopen rule was invoked"). On THIS branch the sealed
texts still carry the bare-id form and were NOT edited (sealed): tier-2 value
architecture `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md:260` ("identity —
count(*) = count(DISTINCT canonical_id) per class and across classes") and
strategy `MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md:767` (the W-L0-9
proof row). Recorded as a RAISED DEFECT against the sealed texts; its
resolution is upstream — the l3 Decision-16 correction and the strategy-text
amendment ADK-0003 records as "still owed in the strategy text". The corrected
detector itself is delivered here (migration 1125, registered in the
`bg_ontology` integrity contract).

**Tests (E):**
- Python: `tests/test_l0_ontology.py` gained `TestPolysemyResolution` (7 tests:
  bare phaladeepika refuses naming school+text; class-qualified text/school
  resolve; bare argala refuses across aspect_type × relation_type;
  class-qualified argala resolves; the varga tie-break is the one named
  exception; single-match path unchanged; class-qualified miss → None).
  `pytest tests/test_l0_ontology.py`: **49 passed, 1 skipped** (pre-existing
  real-Postgres skip) — was 42+1 before this work. Full brahmagyan sidecar
  sweep (`tests/`, excluding tests/l2, `-x`): **6176 passed, 201 skipped,
  3 xfailed, 1 failed** — the single failure is
  `test_u2_lifetime_convergence.py::TestBothTiers::test_both_tiers_present`,
  a data-dependent failure in `pipeline/orchestrator/writers/ka_sangam.py`
  (live DB lacks a `LAGNA/sign` chart_fact for the pinned chart; the writer
  correctly refuses to fall back per CR-87/R-3(b)). Independent of this work:
  `ka_sangam` / the u2 test do not import `brahmagyan.l0_ontology` (only
  `writers/bg_ontology.py` and `tests/test_l0_ontology.py` do), and the
  u2 failure mode is live-DB content, not code.
- TypeScript: new `__tests__/resolve_entity.test.ts` (9 tests: composite
  identity declared in the descriptor + optional entity_class input; single-row
  and not-found paths byte-identical; bare multi-class refusal naming both
  candidates; class-qualified success with SQL scoping; same-class multi-row
  refusal; Lane-A3 varga exception; error carries the registry pointer; empty
  name). `vitest run` on the L0_brahmagyan layer: **272 passed, 8 skipped**
  (42 files); on the whole retrieval registry: **1975 passed, 178 skipped**
  (218 files), 0 failures.
  Pre-existing branch failure elsewhere in the repo (NOT caused by this work):
  `src/lib/vidhi/inquiry/beyond_acarya_acceptance.test.ts` — 2 failures
  (report_hash pin `sha256:bfe04932…` vs current `sha256:fd507ec7…`, plus a
  v6 artifact pin). Independence evidence: the test reads the committed
  `src/generated/capability_knowledge.snapshot.json` and evaluator; this
  work touches only `brahmagyan/l0_ontology.py`, its test,
  `resolve_entity.ts` (+ its new test) and migration 1125 — nothing in that
  test's import graph. Flag to the orchestrator for triage on the branch.

## Part 2 — relation_type vocabulary class: EXECUTED (§2.4 decision)

(Unchanged from v1.0 — executed 2026-09-25; migration 1121 HELD.)

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
  (vs `aspect_type.argala`) — NOW DECLARED: seeded in `brahma_polysemy_registry`
  by migration 1125 (family 'reflection': the same Jaimini intervention relation
  registered in the relation vocabulary and in the aspect catalog).
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
noted, kickoff followed.) **Status: RULED 2026-09-26 (ADK-0007) — the registered
slice IS declared the L0 scope object; no DB-backed copy. The honest qualification
state (UNQUALIFIED_SOURCE / rights UNRESOLVED) travels with the designation and
versions forward only when a classical witness is admitted by explicit ruling.**
(AMENDED: line originally read "ADK-pending"; ADK-0007 landed after this section
was first written.)

## Blocks carried forward

1. ~~Design ruling~~ — LANDED 2026-09-26 (mandate Ruling 2 + Decision 16 +
   ADK-0003). Part 1 executed branch-side.
2. **Migration application (Part 5 hard stop, native):** 1125 HELD with
   1120–1124 behind the unreconciled `_migrations_applied` ledger; the corrected
   detector's first production run happens at application.
3. **Sealed-text defect (strategy/native):** the bare-id detector text in the
   tier-2 value architecture (:260) and strategy v2_1 (:767) disagrees with the
   ratified detector; resolution is the upstream Decision-16 correction +
   strategy-text amendment owed per ADK-0003. Recorded, not edited.
4. **W-L0-8 input (recorded finding):** ~78 unregistered cross-class synonym
   collisions now refuse bare resolution (fail-closed); W-L0-8 owns the
   vocabulary-level reconciliation.
5. ~~Part 3 closure (ADHIKARIN)~~ — LANDED 2026-09-26 (ADK-0007): the Bhavat
   Bhavam scope-object closure is ruled; the registered slice is THE scope
   object. (AMENDED: originally read "ADK-pending".)

## Packet status

Execution-side work delivered and verified branch-side: composite identity
codified (writer docstring, registry-row declaration, resolver contracts);
polysemy registry authored as HELD migration 1125 with the corrected detector
registered in the `bg_ontology` integrity contract; both class-blind resolvers
fail-closed with the polysemy rule; tests extended and green (49+1 py ontology
file; 272 TS layer; 1975 TS registry-wide). The packet's remaining gates are
not execution-side: production application (Part 5 hard stop) and the sealed-text
detector amendment (strategy). The Part 3 closure ruling LANDED (ADK-0007).

---
artifact: GOCHARA_DESIGN_SPECS
canonical_id: GOCHARA_DESIGN_SPECS
version: "1.4"
status: FROZEN
frozen_at: "2026-09-30 — per decisions/D-SPECS_DECISION_v1_0.md (FREEZE_WITH_CONDITIONS); steward verification passed: 0 changed lines outside the declared ranges, all 30 « » passages present, forbidden strings absent, 21/36 = 57, v1.3 files untouched (tracker record)"
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
decision: "decisions/D-SPECS_DECISION_v1_0.md (FREEZE_WITH_CONDITIONS) — §5 conditions C1–C10 landed verbatim; steward diff verification passed 2026-09-30; FROZEN marked at B3.9"
supersedes: "design/GOCHARA_DESIGN_SPECS_v1_3.md (sha256 727d174a01060226e05e78cc6b3c264e241069bae652f5c2727c1a4d8988af2d; retained as history — a reviewed file is never edited; v1.4 is the next version)"
doctrine: "sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md (SEALED; D-BRIEF countersigned 2026-09-29)"
reconciliation: "design/RECONCILIATION_DESIGN_SPECS_v1_3.md (B3.8d) — per condition, the exact line ranges changed; v1_2 retained as history"
rulings: "D-RQ1…D-RQ8, D-P4, D-PADMIT, D-PG353 (native, 2026-09-29); lane sheets M-1…M-8, N-1…N-22, ADK-0026/0027/0028 — all stand"
freeze_protocol: "Round-1 reviews (both REWORK) → v1.1; round-2 reviews (Kimi FREEZE_WITH_AMENDMENTS / Codex REWORK) → v1.2; round-3 Codex closure review (REWORK; 3 closed, 12 partly, 4 new blocking) → this v1.3 (B3.8b, contract items only). status: FROZEN is NOT set — the native decides the freeze standard (split ruling: contract vs protocol tracked separately). Until FROZEN, Stream A builds nothing against this file."
chart_scope: "482012f1-710e-4a25-994a-93821f5871aa only (D-SCOPE)"
evidence_labels: "[D] served corpus text:page · [P] practice, uncited_extension with ruling · [R] native ruling · [L] production read-only · [S] source at lane branch · [U] unverified"
oracle_file: "design/GOCHARA_TEST_ORACLES_v1_4.json — the §11.2 index and the JSON inventory are the same set, same count"
g10_evidence: "design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json (sha256 312de09e…88fe83) and v1_1 (sha256 e9e5d4d3…3224) — pinned chart AV operands, verification tier single_pass carried verbatim"
dasha_read_contract: "§4.0 — chart 482012f1, ayanamsha lahiri_chitrapaksha, system vimshottari, build 1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb, tier two_pass_verified"
---

# Gochara design specs v1.4 — the J1 contract (D-SPECS_DECISION_v1_0 conditions C1–C10 landed verbatim; v1.3 frozen-with-conditions, retained unedited as history)

Eleven sections plus §0. Each carries a **schema** (typed object: keys, foreign keys, versions,
null states), **invariants** (what must always be true), and **test oracles** (given/when/then,
a fixture labelled by kind, and a mutation that must fail — the arithmetic written out).
Stream A's migrations implement these schemas; Stream B's rule paths (B5.1) implement these
evaluators; the rehearsal (A5.5) and the retrodiction harness (B5.3) run these oracles.

v1.3 changes against v1.2, by round-3 finding: the four new blocking errors — R3-S01
(O-PP-2 controls replaced: positive Mercury/Mars via scored 7th-house occupancy, negative
Mercury/Rahu with the testimony-only node-dispositor chain spelled out; Lahiri-pinned rows),
R3-S02 (ONE P4 rule — per-agent union over {house, lord}, AND across agents — that O-RP-2 and
O-RP-3 both obey), R3-S03 (synthetic AV fixture values labelled synthetic with explicit keys;
real extract rows cited where used — the extract has no zero BAV and no SAV 24, verified),
R3-P01 (protocol side, B4.5); D-SPECS amendments 1–4 — typed identity (record key includes
generation + contact_id, version-qualified PKs/FKs, source-fact lineage, tagged support
states, unknown-admission, occurrence indexing stable under partition extension with
publication immutability), numerical factor functions/scales + evidence aggregation with
shared-root handling + exhaustive class/agent/target sets, the daśā read contract (§4.0,
with O-PP-1's PD values printed: Mercury, Venus, Venus per the steward's [L] evidence,
verified against L1), P5 missing-input matrix without the BAV/SAV contradiction and P5a's
nonzero comparator explicitly `unresolved`; amendment 5 — fixture kinds set honestly
(literal / constrained_generator / executable_at_A5.5), with O-VI-2's boundary day, O-SM-1's
formula, O-RX-1's identity bytes, and O-RP-5a's named class fixed as named.

## 0. Shared definitions

- **Contact**: one solved physical relation between a transiting body and a physical object
  (point, span, star, derived point, varga position, saham). Physical identity is
  label-independent (v3.0 #27) and method-versioned (§6.1): one crossing exists once per
  `convention_id`, however many interpretive roles attach.
- **Three objects, three lineages** (v3.0 §2.3, Codex E6): physical geometry (contacts),
  interpretive records (relationship records), evaluated windows. A doctrine change re-evaluates
  windows; a change that alters required geometry re-solves contacts; §10.1's invalidation rule
  is driven by which of these actually changed, not by the label on the change.
- **Provenance vs operator role (S-04) — two independent fields, never conflated:**
  - `provenance ∈ {verse_cited, uncited_extension}` — where the rule comes from.
    `uncited_extension` requires `ruling_ref`.
  - `operator_role ∈ {scored, testimony}` — what the evaluation may do with it.
    `testimony` annotates a window; it never weights, gates, or admits.
  - **Admission**: a rule path may produce *scored* output iff its provenance is `verse_cited`
    from served corpus `[D]`, or `uncited_extension` with a native ruling whose text grants
    scoring. Every D-PADMIT element — node-dispositor delivery, māraka-of-house, mūrti, and
    **all Moon-channel (P6) practice operators** — is `operator_role = testimony` until the
    promotion gate named in §2.2 (B5.4 ablation evidence) fires. A corpus read (B3.3-style)
    changes provenance only; it never promotes an operator role.
  - `[U]` never enters a score and never silently becomes `[D]`: an unresolved operand yields
    the declared null state of its contract (ADK-0026).
- **Frame** enum: `moon | lagna | graha:<X> | dasha_lord | bhavat_bhavam:<house>`. Counting is
  inclusive of the reference sign (1st = the sign itself). Every count in an oracle shows it.
- **Generation labels**: `'4.1'` = geometric baseline, candidate-only, never flipped (D-41);
  `'5.0'` = first sound candidate. Manifest-driven provenance (N-10).
- **Rounding rule (S-08)**: decimal degrees display half-up at 2 dp; DMS displays truncate to
  the arcsecond (3.64° = 3°38′24″). Longitude arithmetic in oracles uses the printed 2-dp
  operands; tolerance column says when that matters.

---

## 1. `relationship_record` — the object that replaces the flat target list

### 1.1 Schema (typed contract — S-01)

One row per (event_class, affected_person, frame, agent, relation, object, role, path):

| field | type | key/null rule |
|---|---|---|
| `record_id` | uuid | **PK**; deterministic hash of the natural key: (chart_id, generation, event_class, affected_person, frame, agent, relation, object_id, object_role, contact_id, path_id, rule_version, prerequisites, source_text) — `generation` and `contact_id` are IN the key (R3/amendment 1): two otherwise identical episode records under different generations or different contact episodes never collide; a predicate-list or citation change re-keys the record instead of silently mutating it |
| `chart_id` | uuid | FK → charts; 482012f1 only |
| `generation` | text | the generation this record was evaluated under (`'4.1'`/`'5.0'`…); NOT NULL — records are generation-scoped, never shared across generations (NK-3, R2-S01) |
| `contact_id` | uuid | FK → §6.1 contact identity; NOT NULL on transit-relation rows; NULL only on natal-fact rows (which carry `precision = NULL` by the same rule). Role aliases of one physical contact share **one** `contact_id` (invariant 3) — this column is that declaration, made structural (NK-3, R2-S01) |
| `event_class` | text | one of the 27 classes; adverse classes first-class |
| `affected_person` | enum | `native | father | mother | spouse | child | sibling` — closed enum; extension requires a migration and a `rule_version` bump |
| `frame` | enum + arg | §0; NOT NULL on every row (invariant 1) |
| `agent` | graha | the transiting (or period) body |
| `relation` | enum | physical relation kind — **transit relations**: `residence | aspect | conjunction`; **natal-fact relations**: `dispositorship | association | ownership | occupancy | period_running`. A contact row carries a transit relation; a natal-structure row carries a natal relation; the two never mix on one row (F6a) |
| `object_id` | uuid | FK → §6 physical-object identity; never a label-only ref |
| `object_kind` | enum | `degree_point | sign_span | star | derived_point | varga_position | saham | house_span | house_lord` — the lord objects P3/P4 require are first-class (S-01) |
| `object_role` | enum | `lord | occupant | karaka | dispositor | maraka_of_house | period_lord | yoga_constituent | pada | signature_house` — **authoritative for the interpretive role**; `relation` is authoritative for the physical relation (F6c). `signature_house` marks an object serving as a class's signature house (§2.2 truth table) so role-based selection never re-derives it from prose (R2-S01) |
| `path_id` | text | FK → §2 `rule_path` registry (`P1`…`P6`, `P9` behind D-T2) |
| `rule_version` | text | version of the path definition that produced the row; a path change re-keys records |
| `prerequisites` | jsonb | ordered list of `(predicate_id, rule_version)` composite references (§2.1 `predicate` schema), cheapest necessary predicate first; a bare id is rejected at write time (the same rule as path FKs) |
| `temporal_support` | jsonb | **tagged states (amendment 1):** `{state ∈ {uncomputed, computed_empty, computed}, grain, intervals[]}` — `uncomputed` = never evaluated; `computed_empty` = evaluated, no support found (a result, not an absence of work); `computed` = intervals present. The three states are never conflated; unknown-admission behaviour: a prerequisite in state `unknown` makes the record's admission `unqualified` (recorded as such), never `false` (§2.2 inv 2) |
| `coverage_ref` | uuid | FK → coverage manifest; always resolvable |
| `precision` | jsonb | `{solver_method, delta_lambda, delta_t}` (§7); NULL only on natal-fact rows |
| `source_text`, `source_page` | text | e.g. `Phaladīpikā`, `PG249-250 (XX.34-38)` |
| `source_fact_ids` | jsonb | **source-fact lineage (amendment 1):** ordered list of L0/L1 fact ids (or extract row fact_ids) the record's operands came from; `[]` only on synthetic-fixture rows, which must carry `fixture = true` |
| `provenance` | enum | `verse_cited | uncited_extension` (§0; S-04) |
| `operator_role` | enum | `scored | testimony` (§0; S-04) |
| `ruling_ref` | text | required iff `provenance = uncited_extension` OR `operator_role = testimony` under a ruling (e.g. `D-P4`, `D-PADMIT`) |
| `evidence_for_occurrence` | real | **rank-only**; scale is set at calibration (L5); never a gate (F6b) |
| `evidence_against_occurrence` | real | same |
| `outcome_valence_for_native` | enum | `favourable | adverse | mixed | unqualified` — §3 |
| `severity` | real | interpretive, rank-only, never a gate |

### 1.2 Invariants

1. `frame` is present on **every** row (v3.0 #10).
2. `provenance = uncited_extension ⇒ ruling_ref IS NOT NULL`; `operator_role = testimony ⇒` the
   row contributes zero to any score, weight, or gate (checked by O-RR-7).
3. Role aliases of one physical contact share **one `contact_id`** — role edges, never
   independent observations; no noisy-OR across them.
4. `object_id` resolves to §6 physical identity. Sensitive-degree checks with negative results
   (`not_gandanta`, `not_pushkara`, `not_fired`, `none`) are **not objects** (E3) — they fold
   into the graha's interpretation.
5. House counts are computed from the row's own `frame`, arithmetic stored at evaluation time.
6. A relative's event never reads the native's Moon frame; `bhavat_bhavam` frames carry
   relatives.
7. No soft factor field may zero an admitted window; exclusion only via L0 absence or a failed
   necessary predicate of the record's own path.
8. **Affliction is a predicate, not a label (#23)**: `afflicted(x)` is defined as
   `∃` a row with agent ∈ the named afflicter set {Saturn, Mars, Rahu, Ketu — per the citing
   rule}, relation ∈ {conjunction within orb | aspect}, object = x. An unevaluated affliction
   claim is `unqualified`, never assumed.

### 1.3 Test oracles

O-RR-1 … O-RR-7 — see the JSON (§11.2). v1.1 adds: **O-RR-5** (yoga→event relation resolves with
cancellation and strength consumed — #22), **O-RR-6** (affliction predicate: injected afflicter
conjunction flips `afflicted`; unafflicted control stays false — #23), **O-RR-7** (a
`testimony` row present ⇒ score identical to the row being absent — S-04).

---

## 2. `rule_paths_P1_P6` — admissibility as a union of source-qualified paths

`W_event = ⋃ over admitted paths r ( ⋂ over prerequisites p of r  I_p )`; inside `W_event` a
score **ranks**; ranking never admits or excludes.

### 2.1 Typed contracts (S-01)

**`rule_path`** registry row: `{**(path_id, rule_version) composite PK** (amendment 1 — a path
change inserts a new version row, never mutates in place), frame, agent_set, relation_set,
object_selector, prerequisites: [(predicate_id, rule_version)], soft_factors: [(factor_id, rule_version)], provenance,
operator_role, ruling_ref, score_rule}`. `prerequisites` and `soft_factors` are **composite
references; a bare id is rejected at write time (the same rule as path FKs)**. All FKs into
this registry are **composite version-bound FKs** `(path_id, rule_version)` — an unversioned
reference is rejected at write time.

**`predicate`**: `{**(predicate_id, rule_version) PK**, operator ∈ {eq|in_set|within_orb|house_from|
overlaps|period_running_at|declaration_exists}, operands: {named selectors — every L1/L0 input
named, no free prose}, states: {true|false|unknown}, unknown_is_false: false}` — unknown ≠ false
(§2.2 inv 2); an `unknown` necessary predicate makes admission `unqualified`, never excluded.

**`factor`**: `{**(factor_id, rule_version) PK**, operand selector, direction (higher = stronger |
lower = stronger), **function (the numeric form — e.g. `step`, `linear`, `ratio`), range (the
closed output interval), units (degrees | days | count | unitless)**, **codomain: every
scored factor's `range` ⊆ [0, 1]** (the activity kernel `1 − |Δλ|/orb`, graduated dṛṣṭi
¼/½/¾/1, vedha attenuation ≤ 1 and O-RR-5's strength 0.8 already live there), so the
within-path product lies in [0, 1] and the cross-path `max` compares like with like; a factor
value is never negative — `direction`, with §3's class-relative polarity, carries the sign
(O-RP-7's "flips sign" reads the `direction` field and the resulting channel/valence). New
field **`calibration_status ∈ {uncalibrated_default, calibrated}`**: the numeric mapping of a
factor's doctrine-ordered categories (e.g. exaltation > own > friendly > neutral > inimical >
debility) is B5.1 registry content on the `(factor_id, rule_version)` row; until L5
calibration it is `uncalibrated_default` — rank-only, preserving the doctrine's stated
ordering, entering no served claim of magnitude; calibration replaces it under a new
`rule_version` (D:237; D-RQ1). null_state ∈ {omit |
unqualified}, effect text}` — every factor's effect on the score is declared (#20) **with its
numeric function and scale** (amendment 2): a missing operand takes its `null_state`, never 0
or 1 by default.

**`eval_window`**: `{window_id PK, chart_id, event_class, generation, (path_id, rule_version) FK,
interval, peak_instant, score, evidence_for, evidence_against, outcome_valence_for_native,
severity, record_ids: [FK], coverage_ref, null_states_used[]}`.

**Cross-path score aggregation (S-01)**: a class–instant's score is the **max** over admitted
paths of that path's score (union semantics: one strong path suffices; paths never multiply
each other). Conflicting evidence across paths is **not** netted: `evidence_for` and
`evidence_against` both accumulate, and §3 decides occurrence vs valence separately. Shared
physical roots across paths count once geometrically (one `contact_id`) and once per path
interpretively.

**Evidence accumulation and shared roots (amendment 2; R4-S01):** every record carries a
**root key** `root_id := contact_id` on transit-relation rows and `root_id := object_id` on
natal-fact rows (`contact_id IS NULL`); role aliases of one physical contact, and role aliases
of one natal body, therefore share one root (§1.2 inv 3; §6.2 inv 1). A record's value in its
assigned channel is the within-path factor product evaluated on that record (algebra below);
its other channel is 0; the channel is assigned by class-relative polarity (§3.1). Within one
path, for each channel c ∈ {evidence_for_occurrence, evidence_against_occurrence}:
`contribution(path, root, c) := max over the records of that path sharing root_id of record.c`,
and `path.c := Σ over roots of contribution(path, root, c)`. The reduction is
order-independent and channel-preserving; when a root's role records carry equal values (the
expected case) it returns that value once; non-contributing role records remain as annotation
in the breakdown. Across paths the same root may contribute once per path (interpretive
layers), never twice in one sum. No other reduction — first row, sum across roles, noisy-OR —
is permitted.

**Within-path score algebra (NK-4, R2-S03 — pinned):** a path's score is the
**product** of its factor scores over the admitted base (factors multiply within a path);
a factor whose operand is missing takes its declared `null_state` — `omit` drops the factor
from the product, `unqualified` propagates and makes the path's score `unqualified` — never 0
or 1 by default, and never silently 1.

**Exhaustive sets (amendment 2; R4-S02):** the **agent set** = the seven grahas + Rāhu/Ketu
(nodes are agents and targets, never dṛṣṭi sources — N-14) + the running MD/AD/PD lords in
their period role. The **class set** = the 27 classes enumerated by name in
`measurement/EVALUATION_PROTOCOL_v2_2.md` §2 — the sole enumeration; A5.1 CHECK-constrains
`event_class` to it. Each class's **target inventory** = the objects reachable through the
`object_role` enum of §1.1 from its §2.2 truth-table row and its admitted paths: its
signature houses (`signature_house`), their lords (`lord`), the natal bodies occupying those
houses (`occupant`), the class's kārakas (`karaka`), the dispositors of the foregoing
(`dispositor`), its mārakas-of-house (`maraka_of_house`, testimony), the running period lords
(`period_lord`, P1), yoga constituents with a cited yoga→event relation (`yoga_constituent`,
O-RR-5) and, behind D-T2, padas (`pada`). Kāraka assignments per class are `rule_path`
registry content (B5.1), each carrying its `[D]` citation or ruling; a class with no cited
kāraka has an empty kāraka set (`computed_empty`). Enumeration is qualification-driven (§2.3
inv 7, O-RP-8): a contact is enumerated iff some admitted `(path_id, rule_version)` row's
`object_selector` names its (agent, relation, object_role). There is no other exclusion: the
truth table is a per-class inventory of signature houses, not a bound on target roles (natal
Saturn as 7th-house occupant is a required marriage target — O-RR-3, §11.3).

### 2.2 Path catalogue (frame · agent→relation→object · prerequisites in evaluation order ·
soft factors · source · provenance/role)

**P1 — daśā-lord path** `[D]` Phaladīpikā XX.34–38 (PG249–250) `verse_cited/scored`;
node-dispositor `[P]` (D-PADMIT) `uncited_extension/testimony`. Frame: `dasha_lord` / natal
sign positions. Content: running MD/AD/PD lord's own transit through svakṣetra/exaltation/
friendly sign promotes its bhāva; debility/inimical/combustion → misery; Sun or Jupiter
transiting the bhukti lord's exaltation sign delivers the bhukti's fruit. AD/PD lords appear as
objects **and** agents; dispositor and association edges. **Factor inventory, each with a
declared effect (#20)**: dignity of the transit sign for the period lord (exaltation/own → +,
debility/inimical → −); combustion (→ −); lord-to-class natal relationship (prerequisite, not a
factor); strength/śaḍbala and maitrī enter only as named factors here — nowhere as unlabeled
modifiers. Prerequisites: (1) period running at t (§4); (2) natal bhāva relationship of the
period lord to the event class; (3) the transit relation itself.

**Relation kinds satisfying prerequisite (2), each with provenance and operator role (§0
admission rule):** `occupancy` of a signature house — `[D]` Parāśari bhāva doctrine (as P3),
`scored`; `ownership` of a signature house — `[D]` (as P3), `scored`; `dispositorship` where
the dispositor is a node — `[P]` D-PADMIT, `testimony`; `dispositorship` (non-node) and
`association` — `scored` only where a served Phaladīpikā XX.34–38 clause (PG249–250, cited by
page:column) supports the edge, otherwise `uncited_extension` / `testimony` pending a native
ruling. Corpus read (B3.8d, 2026-09-30): PG249:C1 (ślokas 34–36) and PG250:C1 (ślokas 37–39)
read in full verbatim — no clause in XX.34–38 supports a non-node dispositor edge (predicate
`dispositor|lord of the (sign|rasi|house) (in which|where)` → 0 of the 11 Adh. XX chunks
PG245–255) or a non-node association edge (śl.39's association clause is Rāhu-specific —
testimony under D-PADMIT; PG245:C1's association sentence cross-references Adh. XV–XVIII
natal effects assigned in daśās, not a transit-permission clause; PG253:C1 śl.47 is a natal
kendra-trikona yoga). Therefore — dispositorship (non-node): **no clause found: `testimony`**;
association: **no clause found: `testimony`**.

**P2 — Moon-frame gochara-phala** `[D]` Phaladīpikā XXVI.1–8 (PG321–323), XXVI.11 (PG335);
XXVI.1–2 + XXVI.24 Moon-relative **node** results `[D]` (B3.3 §5: "Rāhu and Ketu are similar to
the Sun"; Rāhu's 12-house janmarāśi list) — **N-14 restated: no nodal aspect is thereby
authorised; nodes remain agents and targets, never dṛṣṭi sources**. M-8 `[R]`. Frame: `moon`.
Per-planet favourable houses from janma-rāśi with vedha, Sun↔Saturn and Moon↔Mercury
exceptions, vipareeta cancellation; **adverse residence** (Saturn/Sun/Mars/Jupiter in 12/8/1)
is evidence **for the adverse classes** (D-RQ5 shape) and never attaches to gain classes.
Licences the native's fortune, never a relative's event.

**P3 — lagna-frame bhāva transit** `[D]` Yavana Jātaka ch.45–48 + Parāśari bhāva doctrine
`verse_cited/scored`; māraka-of-house `[P]` (D-PADMIT) `uncited_extension/testimony`. Frame:
`lagna`; relatives via `bhavat_bhavam`.

**P3 predicate set, explicit Boolean form (S-03)** — per event class, with
`H` = the class's signature house set, `L(H)` = the lord set of H:

- `contact(agent, house_span h) := residence(agent, h) ∨ aspect(agent, h)`
- `contact(agent, house_lord ℓ) := conjunction(agent, ℓ_natal) ∨ aspect(agent, ℓ_natal)`
- `P3_admit(agent, class) := ( ∃h ∈ H : contact(agent, h) ) ∨ ( ∃ℓ ∈ L(H) : contact(agent, ℓ) )`

"House and its lord" in the source prose is read as **both categories are supported targets**
(union), not "both contacts are necessary" — the conjunction reading is rejected: it would deny
admission the sealed father analysis granted on the house contact alone (S-03 evidence
DS:131 vs v3.0 §4). Per-class truth table:

| class | signature house set H (lagna frame) | māraka set (testimony only) |
|---|---|---|
| marriage / relationship_begin | 7 | 2, 7 lords |
| separation / relationship_end | 7 (affliction), 12, 6 | 2, 7 lords |
| bereavement (father) | 9 via `bhavat_bhavam:9`; 2/7/8 from it | 2, 7 from the 9th |
| childbirth | 5 | — |
| career classes | 10, 6 | — |
| education classes | 4, 5 | — |
| financial gain/loss | 11, 2 / 12, 8 | — |
| relocation / travel | 4, 12, 9 | — |
| health (acute/chronic/surgery) | 6, 8, 12 | — |

**Row membership by protocol class name** (27 classes, EVALUATION_PROTOCOL_v2_2 §2):
marriage, romantic_start → "marriage / relationship_begin"; separation → "separation /
relationship_end"; bereavement → "bereavement (father)" (father frame); childbirth →
"childbirth"; career_entry, career_advancement, career_change, career_setback → "career
classes"; education_milestone, exam_outcome → "education classes"; major_gain → financial
gain (11, 2); major_loss → financial loss (12, 8); relocation, travel_event → "relocation /
travel"; illness_acute, chronic_onset, surgery → "health". `birth_anchor` is excluded from
enumeration entirely (O-CF-N6: zero rows). The remaining eight — achievement_recognition,
business_launch, financial_deception, foreign_settlement, parental_event,
property_acquisition, psychological_arc, spiritual_turn — have **H = unknown**: under §2.1 an
unknown necessary predicate makes P3/P4 admission `unqualified` for that class — never
`false`, never admitted — until a versioned `rule_path` row with a cited source supplies H.
No H is assigned here without a citation.

**P4 — double transit** `[P]` `uncited_extension` under **D-P4**, `scored`; sole primary joint
precedent Phaladīpikā XVII.12 (PG216) `[D]`. **ONE rule (R3-S02), obeyed identically by
O-RP-2 and O-RP-3:** for a class with signature house set H and lord set L(H), define per
agent `infl(g) := ( ∃h ∈ H : contact(g, h) ) ∨ ( ∃ℓ ∈ L(H) : contact(g, ℓ) )` with
`contact = occupation ∨ aspect ∨ conjunction-within-orb` as in P3; then
`P4_admit(class) := infl(Jupiter) ∧ infl(Saturn)` — each agent independently may touch the
house **or** the lord (union within an agent), and the two agents need **not** share one
target (AND across agents). Peak definition (S-01 closure): the peak instant is the maximum of
`min(activity_Jupiter, activity_Saturn)` over the overlap interval, computed per §7.2 inv 2
(interior extrema, not endpoints); "tightest overlap" is that argmax. The seed's "same
Moon-house" definition and v2.0's father-example claim remain withdrawn. **O-RP-2 (R3-S02;
R4 Q2):** for bereavement (father) the truth table gives H = {9th and its 2nd/7th/8th via
`bhavat_bhavam:9`} = {Sagittarius, Capricorn, Gemini, Cancer}; the māraka column names the
*lords* of the 2nd and 7th from the 9th (Saturn, Mercury) as `maraka_of_house` testimony
annotations — it removes no house from H and no lord from L(H). O-RP-2 evaluates the ONE rule
twice: (i) over the restricted inventory H′ = {Sagittarius}, L′ = {Jupiter}: infl(Jupiter) =
FALSE (Δ 29.48°; aspects on Pisces/Taurus/Cancer), infl(Saturn) = TRUE ⇒ P4 FALSE — the D-P4
withdrawal (Jupiter in Scorpio does not aspect Sagittarius), a labelled restricted negative
test; (ii) over the full H: Jupiter's 9th aspect from 220.31° falls at 100.31° Cancer, the
8th from the 9th, a house in H ⇒ infl(Jupiter) = TRUE by house contact alone; Saturn occupies
Sagittarius ⇒ P4_admit = TRUE. Both results are asserted; "any P4 row for this frame-date is
a regression" is withdrawn.

**P5 — aṣṭakavarga path** `[D]` BPHS ch.66 vv.13–15 (`BPHS2:35666-35684`), ch.70 (served at
PG874–876; `BPHS2:40799-41558` does not resolve — CORPUS_READS §9), Phaladīpikā XXIII (PG301),
XXIV (PG304, PG307). After §8 polarity normalisation. **Each form is specified independently
with its own operands and missing-data states (S-05).** The per-form operand-availability
state is the **P5 missing-input matrix** (R2-S04, R3: each operand gates exactly its own
form — no cross-form knockouts):

| form | operand | missing-operand state | chart state (v1.3) |
|---|---|---|---|
| P5a | per-sign BAV vector of the transiting graha | missing BAV rows ⇒ **P5a alone** unqualified | resolved, extract v1_0, tier `single_pass` verbatim |
| P5b | SAV per sign | missing SAV ⇒ **P5b alone** unqualified (never P5a) | resolved, extract v1_0 SARVA row |
| P5c | per-contributor BAV matrix + donor key | missing donor matrix ⇒ **P5c alone** disabled | disabled — donor rows pending the native-authorised ga_strength rebuild (#2731) |
| P5d | piṇḍa + śodhana rows | missing piṇḍa rows ⇒ **P5d alone** unqualified | resolved except donor-level, extract v1_1; `pinda_sarva` split flagged not recompute-covered |
| P5e | solar ingress substrate | missing ingress ⇒ **P5e alone** unqualified | available from L0/L1 as for P1 |
| — | whole AV build absent | ⇒ **all** P5 forms unqualified (the only cross-form case) | n/a on this chart |

- **P5a** — transit through signs by benefic-mark count in the **transiting graha's own** BAV:
  **a known zero is adverse** (D-RQ1; BPHS ch.70 vv.24–27) — that is the only ruled numeric
  statement. **The nonzero comparator is explicitly `unresolved`:** the doctrine's "more
  favourable / fewer adverse" prose supplies no numeric threshold, and no cited rule sets one;
  until a cited threshold exists, P5a's scored output is **known-zero detection only**, and
  any nonzero comparison evaluates to `unresolved` with the operand named (never to a mean or
  an invented band). Operands: per-sign mark vector of that graha's BAV (extract v1_0, tier
  `single_pass` — carried as-is; these rows are not described as verified). Missing BAV ⇒
  P5a alone `unqualified` (matrix above). **No "sign mean" comparator** — removed (S-05.1).
- **P5b** — SAV bands: >30 favourable / 25–30 medium / <25 adverse (`BPHS2:42332-42335`).
  Operands: SAV per sign (extract v1_0 SARVA row). Missing SAV ⇒ P5b `unqualified`;
  **does not touch P5a**.
- **P5c** — fruit delivered in the kakṣyā **owned by the mark-donor** (PG301 [D], division
  order Saturn, Jupiter, …). Operands: per-contributor BAV matrix + donor key. Donor rows
  pending the native-authorised ga_strength rebuild (matrix above) ⇒ **P5c alone** disabled;
  P5a/P5b stand (S-05.2). A sign-level fallback is labelled exactly that — a coarser P5a
  qualification — never donor evaluation (#19).
- **P5d** — śodhya-piṇḍa × marks ÷ 27 → nakṣatra (Phaladīpikā XXIV PG304/PG307; BPHS ch.70
  PG874–876): operand conventions pinned — integer product, `mod 27`, **remainder 0 ⇒ 27th
  nakṣatra** (Revatī); marks taken at the house the verse names (father: 9th from the Sun's
  rāśi in the Sun's AV); Saturn/Jupiter over the star or its trines times the affair;
  daśā-gated per the text. **Chart operands resolved from extract v1_1** (śodhya piṇḍas this
  chart: SUN 204, MOON 162, MARS 222, MERCURY 198, JUPITER 187, VENUS 126, SATURN 102 —
  bhinna + raasi checked equal to śodhita per graha by the recompute; the `pinda_sarva`
  per-subject split remains flagged not recompute-covered, tier `single_pass` verbatim). The
  textbook worked example (marks 2, piṇḍa 148 → Uttarabhadra) remains the text's example, not
  this chart's data (CORPUS_READS §9).
- **P5e** — Sun-month selection only where the rule says so (BPHS ch.70). Operands: solar
  ingress substrate. No extension to other agents.

**No universal numeric multiplier** — M-7 bands remain a WP8 hypothesis (D-RQ1).

**P6 — Moon channel (on demand)** `[P]` muhūrta practice `uncited_extension`; **every P6
operator is `testimony`** (D-PADMIT, S-04): tārā (nine-fold, MC PG67/PG79 [D] with the
cycle/thirds refinement — the "[?]" at PG67:C1 is OCR uncertainty recorded at that clause, not
smoothed over), tithi–nakṣatra, Moon's own vedha, chandrāṣṭama (absent as a generic rule by
predicate count 0 — context-bound 8th-from-Moon rules only). Muhūrta Cintāmaṇi present (274
chunks). Frame: per the admitting path's objects. **Day rows come only from this path** (M-3),
on demand inside admitted windows, with its own coverage record — never materialised
century-wide. Being testimony, P6 annotates admitted day rows; it does not create or weight
scored windows until its promotion gate (§2.3 inv 7).

### 2.3 Invariants

1. Admission per §0; every path row carries `provenance`, `operator_role`, and for `[P]` the
   ruling ref.
2. Pruning discards an interval for path r **only** where a necessary predicate of r is
   demonstrably false there; unknown applicability ≠ false; "uncomputed" is never "empty".
3. No soft factor zeroes an admitted window; vedha and AV **qualify**, L0 absence and failed
   prerequisites **exclude**.
4. Era/month/day are **output resolutions** produced by the paths operating at those grains —
   never a clipped curve (the 27-of-41 plateau, E5, is the defect this kills; O-GR-PLATEAU
   tests the trace, protocol §B tests the shape — #24).
5. Grain assignments are authoring defaults, overridable by any rule whose source places an
   agent at another grain.
6. P6 is the only source of day-resolution rows.
7. **Testimony boundary (S-04)**: node-dispositor delivery, māraka-of-house, mūrti, and all P6
   operators annotate, never weight, until B5.4 ablation evidence supports promotion; the
   promotion gate is a Δ-median-rank measurement under the evaluation protocol, not a corpus
   read. Enumeration is qualification-driven (#21): `transit_triggers` / `dasha_rules` /
   qualified restrictions control what is enumerated; a Cartesian all-agents × all-targets
   enumeration is a defect (O-RP-8).
8. Promise consumes **strength AND condition** (#1): a promise term is the product of a
   strength factor and its condition predicate; a constant-presence implementation (promise
   independent of condition) fails O-RP-6.

### 2.4 Test oracles

O-RP-1 … O-RP-8 — see the JSON. v1.1 notes:

- **O-RP-5 (adverse-residence direction — S-03 fix, ONE test, prose = JSON; v1.2 split per
  R2-S05 into two fixtures):**
  - **O-RP-5a (scored 8th-from-Moon residence; named class `illness_acute` — R3).** A
    Saturn-in-**8th**-from-Moon interval
    contributes `evidence_for_occurrence > 0` to **adverse** classes (it is evidence FOR them)
    and attaches nothing to gain classes. Fixture (literal): natal Moon 327.06° Aquarius;
    Saturn transiting **172.00° Virgo** — the inclusive count from the Moon sign is written
    out: Aquarius 1st, Pisces 2nd, Aries 3rd, Taurus 4th, Gemini 5th, Cancer 6th, Leo 7th,
    Virgo **8th** ⇒ `evidence_for_occurrence` rises on the named adverse class
    **`illness_acute`** (the assertion is made on that class by name, not on "adverse classes"
    in general) and zero attaches to any gain class. Mutation: attaching the edge to a gain
    class, or as `evidence_against` on an adverse class, must fail; an assertion that names no
    class also fails (R3: an unnamed class set is untestable).
  - **O-RP-5b (testimony Sade-Sati / 12th-from-Moon).** Fixture: twins' birth 2022-01-03,
    Saturn 288.01° Capricorn = 12th from the Aquarius Moon (Sade-Sati phase 1) ⇒ the
    childbirth (gain) class carries no Sade-Sati edge; the phase-1 row exists as
    `operator_role = testimony` on adverse-eligible classes with **zero** score effect (an
    implementation letting the testimony row move any score must fail). The v1.1 fixture was
    this 12th-house case standing in for the scored rule — the two are now distinct fixtures
    (R2-S05).
- **O-RP-6 (#1)**: promise = strength × condition; set the condition false ⇒ promise 0.
- **O-RP-7 (#20)**: flip a dignity operand ⇒ P1's qualifier flips sign.
- **O-RP-8 (#21)**: enumeration driven by qualified restrictions only.

---

## 3. `three_field_valence` — occurrence evidence is not outcome valence

### 3.1 Schema (on every evaluated window and every relationship record)

`evidence_for_occurrence real` · `evidence_against_occurrence real` ·
`outcome_valence_for_native enum(favourable|adverse|mixed|unqualified)` · `severity real`.

Class-relative polarity (#11, #12): each event class declares its polarity; rule polarity is
interpreted **relative to the class** (a strong 7th-house affliction is evidence **for** the
separation class and **against** the marriage class).

**Occurrence conflict ≠ outcome valence (S-03)**: `evidence_for` and `evidence_against` answer
"will this class of thing occur?"; `outcome_valence_for_native` answers "is that occurrence
good for the native?" High evidence both ways ⇒ the **occurrence is contested** (reported as
both fields standing; never cancelled to neutral, and never relabelled `mixed`). `mixed` is a
**valence** verdict — an occurrence with genuinely good and bad consequences for the native —
and it derives from class polarity plus rule content, never from contested occurrence evidence.

### 3.2 Invariants

1. The three fields are independent; no arithmetic nets evidence_for against evidence_against.
2. `outcome_valence_for_native` reports the *native's* interest.
3. `unqualified` is the honest state when operands are unresolved (ADK-0026) — never a
   favourable-sounding default. Finding #12's defect (1,435 era rows all "favourable", E5) is
   the regression this field exists to prevent (O-TV-1).
4. Valence is computed at evaluation time from class polarity + record content; never copied
   class-blind from the rule row.

### 3.3 Test oracles

O-TV-1 … O-TV-3 — see the JSON (bereavement valence; marriage with both evidence fields ⇒
outcome still `favourable`, occurrence noted contested — not `mixed`; unresolved AV operand ⇒
`unqualified` with the operand named).

---

## 4. `permission_per_instant` — period licence as a function of t

### 4.0 Daśā read contract (R3: Codex D-SPECS amendment 3 — pinned before any L1 read)

Every daśā operand read in this contract is pinned to: `chart_id =
482012f1-710e-4a25-994a-93821f5871aa`, `ayanamsha_id = lahiri_chitrapaksha`, `system_id =
vimshottari`, `build_id = 1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb`, verification tier
`two_pass_verified`. An unpinned read is a defect (v1.2's B38-F1: an unpinned query matched
rows of other systems/ayanāṃśas and produced a false "no variant explains" claim — corrected
in the v1_2 reconciliation).

- **Interval convention:** every MD/AD/PD row is the half-open interval
  `[start_iso, end_iso)`; an instant `t = end_iso` belongs to the **next** row. Boundary
  instants are unambiguous by construction.
- **Parent linkage:** an AD row is valid only under its MD row; a PD row only under its AD
  row; linkage by (chart, system, build, level, parent row id), never by timestamp overlap
  alone.
- **Duplicate-row rule:** select rows of tier `two_pass_verified`; if two equally-qualified
  rows conflict for the same (level, parent, index), **reject both and fail loudly** — never
  silently pick one.
- **Identical-duplicate rule:** two rows equal on every contract field (level, parent row id,
  index, lord, start_iso, end_iso, tier) collapse to one — the read records both row ids and
  proceeds; any field difference is a conflict under the rule above.
- **Instant rule:** a date-only input is the instant 00:00:00 IST (Asia/Kolkata, UTC+05:30) =
  the previous UTC day at 18:30:00Z — the platform day-anchor convention of
  EVALUATION_PROTOCOL_v2_2 §3; a timestamped input is used as given, converted to UTC; the
  read prints the UTC instant it evaluated. The three worked events are therefore
  2013-12-10T18:30:00Z, 2018-11-27T18:30:00Z and 2022-01-02T18:30:00Z, each inside its
  printed PD row.
- **Reference rows (verified [L] 2026-09-30; every row id printed in full — C6):** MD Mercury
  `58afa482-4bce-42df-9c0d-0b5a2e02305e` (2010-08-18T15:50:23Z → 2027-08-18T21:50:23Z). At
  the three worked-event instants the PD lords are **Mercury, Venus, Venus** (O-PP-1's
  original assertion — confirmed):
  - 2013-12-11 → MD Mercury / AD Ketu (`133b4500-ad36-4fff-8814-c6b0b253ca05`,
    2013-01-14T07:17:23Z → 2014-01-11T12:14:23Z) / **PD Mercury**
    (`6b843ad2-0759-4e7f-af7d-d39eac8b0325`, 2013-11-21T04:44:19Z → 2014-01-11T12:14:23Z);
  - 2018-11-28 → MD Mercury / AD Moon (`14f20359-c30e-425d-b50f-45b017568ace`,
    2017-09-17T20:20:23Z → 2019-02-17T06:50:23Z) / **PD Venus**
    (`203406df-ddc3-44b8-a174-e48c5546d009`, 2018-10-28T04:09:53Z → 2019-01-22T09:54:53Z);
  - 2022-01-03 → MD Mercury / AD Rahu (`25a4b815-39bb-4b4a-b922-84a71778bb4f`,
    2020-02-14T11:47:23Z → 2022-09-02T21:05:23Z) / **PD Venus**
    (`5c07a7c9-0848-4e54-9f0b-2a9652101cef`, 2021-10-04T03:09:26Z → 2022-03-08T08:42:26Z).

### 4.1 Schema

`permission(chart_id, t, event_class) → {admitted_paths[], period_context {system, build_id,
md: {lord, row_id, licence, relation}, ad: {lord, row_id, licence, relation}, pd: {lord,
row_id, licence, relation}, applicability}, prerequisites_state[]}` — per level, `licence ∈
{scored, testimony, none}` states whether P1 prerequisite (2) holds for that level's lord and
with which operator role; `relation` names the natal relation kind and its record id, or
`none`. **Composition:** class-level licence at t is the union over levels — licensed iff
some level's `licence = scored`; a `testimony` licence annotates and never licenses (§0);
levels are never collapsed into one boolean; the per-level fields are the assertable surface
(O-PP-2). Computed **per instant** from nested Vimśottarī MD/AD/PD (level ≥ 3 from L1
`chart_dashas`, read per §4.0).
Chara daśā serves Jaimini targets only. Mudda daśā lives inside P9 (Tier 2, behind D-T2).
Aṣṭottarī: applicability-evaluated, **absent on this chart** (D-RQ7 — both conditions fail:
Rāhu 8th from lagna lord Mars; day birth in Śukla pakṣa; the pakṣa wording of v.23 survives
OCR only partially — recorded as [D-with-OCR-degradation] at that clause, per CORPUS_READS §6
and S-06). N-15: no Sade-Sati term in any permission or λ.

### 4.2 Invariants

1. Permission is a function of t, never a per-class decade constant (E6).
2. A period lord with **no relationship** to the event class does not licence it.
3. Applicability is evaluated from chart operands and stored; a system whose conditions fail is
   `absent`, not false-weighted.
4. Permission prunes only through a path's necessary period prerequisite; it never multiplies
   as a decidable constant across all paths.

### 4.3 Test oracles

O-PP-1 (exact MD/AD at the three event instants, with the PD asserted, not merely present —
PD values printed in §4.0: Mercury, Venus, Venus) ·
O-PP-2 (**controls replaced per R3-S01**: positive control = Mercury/**Mars** AD (row
`b1e4d515-6a94-4054-89ff-1ed2487f66ae`, 2019-02-17T06:50:23Z → 2020-02-14T11:47:23Z) —
Mars is natal 7th-house occupant (Libra), a *scored* occupancy relationship for the marriage
class; negative control = Mercury/**Rahu** AD (§4.0 reference rows) — Rahu occupies the 2nd
(Taurus), owns nothing, casts no dṛṣṭi (N-14), and its only link to the 7th is the dispositor
chain through Venus, which is **testimony-only** per D-PADMIT and cannot licence. Assert the
*direction* of the permission difference, with a boundary case at the AD transition
2020-02-14T11:47:23Z under the §4.0 half-open convention. Note: 2018-11-28 is Mercury/Moon,
not Mercury/Rahu — Lahiri-pinned (R3-S01). The old variance-only check survives only as a
labelled smoke check) · O-PP-3 (Aṣṭottarī absent with both failed conditions named).

---

## 5. `vedha_interval_relation` — obstruction as intervals, not flags

### 5.1 Schema

`vedha_interval(vi_id PK, rule_version, primary_contact_id FK, obstructor_body, vedha_kind,
t_in, t_out, state ∈ {active, cancelled_vipareeta, inactive}, exception ∈ {none, sun_saturn,
moon_mercury}, independence_group, source_ref, provenance, operator_role)`.

Semantics unchanged from v1.0: overlap-interval obstruction (N4's temporal structure
preserved); vipareeta **carves a sub-interval**; the two exception pairs never obstruct each
other (M-8); grade keys match the served table (#16 — the grade→key mapping is data in the
rule row, not prose). **The PG353 battle scale is not a general grade source**: D-RQ8
authorised citation-hygiene corrections only, not a suppression multiplier; **D-PG353 (native,
2026-09-29 18:09 UTC) rules: the generalised PG353 attenuation stays removed unless a cited
rule supports it.** **No attenuation without an active obstruction** (#17).
`independence_group`: one root attenuates once; duplicates never multiply.

### 5.2 Invariants

1. Vedha **qualifies** a specific primary transit; it never excludes a window.
2. Attenuation requires `state = active` at t.
3. Moon-vedha rows exist only inside P6 day windows with a P6 coverage record — and, P6 being
   testimony, Moon vedha is annotation-only (S-04).
4. Absent overlay coverage reads as `unavailable` with a coverage object, never as 1.0 (#25;
   O-VI-5 in the JSON).

### 5.3 Test oracles

O-VI-1 … O-VI-5 — see the JSON (v1.1 adds O-VI-2 partial-overlap and O-VI-4 vipareeta carve-out
— both missing from the v1.0 JSON — and O-VI-5 for the #25 overlay-coverage case; O-VI-3 gains
a non-exception obstructor control).

---

## 6. `sky_event_substrate` — compute once, solve once

### 6.1 Schema and physical identity (S-02)

One substrate per (ephemeris/convention generation, ayanāṃśa, node convention, body, grid):
`sky_event(event_id PK, convention_id, body, event_kind ∈ {sign_ingress, nakshatra_ingress,
kakshya_crossing, station, eclipse_instant}, t_exact, longitude, solver_method, delta_lambda,
delta_t, coverage)`.

**Canonical physical-object identity**: `physical_object_id = hash(body, relation_kind,
canonical_target, convention_id)` where `canonical_target` is the *physical* target —
`(point, longitude)` at full solved precision, `(span, sign)`, `(star, index)` — canonicalised
before any role or label attaches. **Hashing a rounded `t_exact` or a role-qualified target
reference is forbidden** (the inherited ledger's `target_kind + target_fact_id-or-ref` hash can
split one physical contact across roles; and rounded-time hashing splits one crossing across
precisions). **Contact identity (NK-2):** `contact_id = hash(physical_object_id,
occurrence_ordinal)` where `occurrence_ordinal` is the 1-based index of the crossing inside the
**ordered set of crossings of the same physical tuple** (ordered by solved `t_exact` at full
precision). A retrograde re-crossing of one target is therefore occurrence 2 of one object —
one physical object, two contacts — never one contact silently overwritten, and never two
objects. Truncated contacts (exact centre off-horizon, N3) keep the same identity with
`coverage.truncated = true`; partition extension that reveals the true centre **updates the
row in place** (same id), it does not mint a new contact. Collision handling: hash is over the
canonical tuple above; on collision the build fails loudly — no silent dedup.
**Occurrence-indexing stability (R3, Codex amendment 1):** the ordinal domain is pinned in
`convention_id` — the convention carries its domain start and end; ordinals are computed over
the **full-domain** ordered crossing set, never over a clipped partition. Partition extension
**inside** the domain appends only: existing ordinals and contact ids never change.
Partitions inside a domain are solved in forward time order only; a backward partition is a
new `convention_id`. A contact whose in-orb interval begins inside the solved partition but
whose exact centre lies beyond the partition end is published with `coverage.truncated =
true` and `occurrence_ordinal = (ordinals already assigned to its tuple) + 1`, ordered by its
`t_in` until the centre is solved; when a later partition solves the centre the row is
enriched in place (same id, same ordinal), and further crossings of the tuple revealed inside
the same retrograde loop append as later ordinals.
**Publication immutability:** once a contact id has been published to any downstream artifact,
it is never renumbered or reused; a corrected physical reading mints a new id and retires the
old one with a supersedes edge. **Enrichment vs correction:** an in-place update may only
fill a field that was NULL or flagged truncated/unresolved and may change no published
non-NULL value; any change to a published non-NULL value (`t_exact`, longitude, ordinal,
target) is a correction — new id, supersedes edge, old id retired. **Canonical serialization (the identity bytes, for O-RX-1
and lineage checks): `body|relation_kind|canonical_target|convention_id|ordinal` with
`canonical_target` rendered at full precision (`point:<λ full precision>` / `span:<sign>` /
`star:<index>`). Oracle: **O-RX-1**
(two crossings of one tuple — a direct pass and a retrograde re-crossing — must receive
ordinals 1 and 2 under one `physical_object_id`; an implementation that collapses them, or
mints a second object, fails).

**Contract counts** (v3.0 §6.1): Sun 12 sign / 27 nakṣatra / 96 kakṣyā crossings per year;
Saturn ≈ 0.4 / 1.1 / 3.2 plus retrograde re-crossings. **Moon events are generated on demand**
(≈ 4×10⁵ boundary events per 250 y if materialised — independently recomputed in review: (12 +
27 + 96) crossings × 13.37 lunar circuits/yr ≈ 1,800/yr ⇒ ≈ 4.5×10⁵ per 250 y [verified]); a
Moon search writes a `moon_on_demand` coverage record.

### 6.2 Invariants

1. **Physical identity is label-independent** (E1's 31,401 × 3 identical kakṣyā rows are the
   defect) — and now algorithm-pinned per §6.1.
2. **0° seam root exists** (#14); boundary search covers **both** boundaries (N2); **no
   fabricated ingress** at a clipped horizon start; off-horizon exact centres retained as
   **truncated spans** (N3), identity per §6.1.
3. Residence spans are intervals with coverage (#6, #7).
4. Interval objects stay intervals (M-5).
5. Boundary events are enumerated **per body**, joined to targets afterwards.
6. **Aspect direction is computed, never mirrored (#13, T0-1)** — the forward count:
   a special aspect from body b falls at `(λ_b + 30·(h−1)) mod 360` for house-offset h
   (Mars 4th/8th: +90°/+210°; Saturn 3rd/10th: +60°/+270°; Jupiter 5th/9th: +120°/+240°);
   the 7th is universal full. The mirrored implementation (`target + angle` read backwards)
   is the shipped defect and is rejected by the O-AD oracle set (invariant tested, not
   asserted). Nodes cast no dṛṣṭi (N-14) while remaining agents and targets.

### 6.3 Test oracles

**O-AD-1…4 (aspect direction — first in the JSON, per the review)** · O-SS-1 … O-SS-4
(incl. O-SS-4 Moon-on-demand, missing from the v1.0 JSON) · plus an interior-extremum fixture
(O-SM-4, §7).

---

## 7. `solver_method_uncertainty` — certified bounds, honest method

### 7.1 Schema (fields on every contact and sky event)

`solver_method ∈ {arc_index_bracket, swiss_refined, clipped_truncated}` · `delta_lambda` ·
`delta_t` · `precision_regime`. Refinement rule: bracket from the arc index; refine to Swiss
whenever the approximation's uncertainty could change **membership, ordering, boundary
identity, or a reported peak**; store both uncertainties (δt ≈ δλ/|λ̇| unstable near stations —
stations are always Swiss-refined).

### 7.2 Invariants

1. Every reported `t_exact` carries its method and uncertainties.
2. Scores retaining a functional form are solved for **interior extrema and threshold roots**
   (endpoint-only evaluation is forbidden) — O-SM-4's `f(t)=t(1−t)` fixture rejects
   endpoint-only peak detection.
3. The M-1 activity kernel is **angular**: `activity = 1 − |Δλ|/orb` (D-RQ2).
4. A tolerance or method change implies a new `convention_id`; contact ids hash
   `method_version`.

### 7.3 Test oracles

O-SM-1 (N1 regression, station case with pinned interval/orb/tolerance) · O-SM-2 (bracket with
δλ straddling the orb ⇒ Swiss-refined before membership) · O-SM-3 (every station
`swiss_refined`) · O-SM-4 (interior extremum).

---

## 8. `bindu_polarity` — declared before any citation-bearing weight

### 8.1 Schema

`av_polarity_declaration(convention, benefic_mark_name, malefic_mark_name, source_ref,
applies_to_fact_categories[])` — unchanged: L1's `ashtakavarga_bindu*` stores PyJHora benefic
"dots"; Santhanam BPHS names the benefic mark **rekhā** (`BPHS2:35666-35684`); the declaration
pins `pyjhora_dots = benefic_marks ↔ rekhā` for citation (N8).

Evaluation semantics (D-RQ1, **S-05 corrected**): in a graha's own BAV, a transited sign's
benefic-mark count is compared **against the doctrine's stated expectations only** — more
favourable, fewer adverse, **a known zero is adverse** (BPHS ch.70 vv.24–27). The v1.0
"sign mean" comparator is **removed**: neither the sealed P5 definition nor D-RQ1 specifies it.
An **unresolved operand** yields `unqualified`. SAV bands: >30 / 25–30 / <25
(`BPHS2:42332-42335`). **Chart-specific AV operand values: resolved at tier `single_pass`
(verbatim) from the pinned G-10 extracts** — `design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json`
(96 BAV+SARVA rows, sha256 312de09e…88fe83) for P5a/P5b and
`design/L1_ASHTAKAVARGA_EXTRACT_v1_1.json` (200 piṇḍa/śodhana rows, sha256 e9e5d4d3…3224)
for P5d — with two caveats carried as data: (i) the AV rows are build aa9602ce (the frozen
t0 ga_strength build) while natal positions elsewhere cite build 1c092ffb; consistency was
established by an independent pyjhora recompute from 1c092ffb longitudes matching all 96 BAV
rows and all 21 per-planet piṇḍas, not by the rows' own lineage; (ii) `pinda_sarva`'s
per-subject split is not covered by any recompute — the flag persists wherever that operand
is consumed. **P5c's donor matrix alone remains unresolved** (pending the native-authorised
ga_strength rebuild; writer merged in PR #2731).

### 8.2 Invariants

1. No AV-derived weight exists before the polarity declaration row exists (T0-11 gates P5).
2. The declaration is data: evaluations join it and record it in lineage (O-BP-3).
3. Known-zero and unresolved are distinct states end-to-end (D-RQ1).
4. Each P5 operand gates exactly its own form (§2.2 missing-input matrix): missing per-sign
   BAV ⇒ **P5a alone** `unqualified`; missing SAV ⇒ **P5b alone** `unqualified`; missing
   contributor matrix ⇒ **P5c alone** disabled; missing piṇḍa rows ⇒ **P5d alone**
   `unqualified`; missing ingress substrate ⇒ **P5e alone** `unqualified`; the whole AV build
   absent ⇒ **all** forms `unqualified` (O-BP-2).
5. `min_sav_score`-style config is never read as measured SAV (#26; O-BP-5).

### 8.3 Test oracles

O-BP-1 … O-BP-5 — see the JSON (v1.1 adds O-BP-3 declaration read-back, O-BP-4 kakṣyā
donor-key resolution per PG301 — #19, O-BP-5 measured-SAV-vs-config fixture — #26).

---

## 9. `annual_object_identity` — sahams, muntha, varṣeśa per year

### 9.1 Schema

`annual_object(chart_id, varsha_year, kind ∈ {saham:<name> | muntha | varshesha}, longitude,
sign, house_lagna_frame, source_ref)` — identity keyed by (chart, year, kind); computed from
the varṣa-praveśa chart of that year; **never joined across years**. Consumed only by P9
(Tier 2, behind D-T2) and Mudda daśā inside the year.

### 9.2 Invariants

1. Annual objects carry their year in their identity; any cross-year equality test is a defect.
2. Saham formulas carry their source (`[D]` Tājaka Nīlakaṇṭhī, Devanagari chunks, B3.3 §4) and
   day/night variant where the text gives one.
3. **Activation (B3.3 §4 landed [D]) — three separate modes, kept separate (S-06):**
   (i) **sahameśa-ki-daśā** — the saham lord's varṣa-daśā delivers (PG95:C1, "सर्वसम्मत", with
   the pāka-day alternative recorded beside it); (ii) **varṣeśa contact** (PG147, PG160);
   (iii) **munthā/muntheśa contact** (PG132, PG160). No universal conjunction of the three is
   synthesised — each passage's condition and context stays its own rule. The Mudda labelling
   gap (मुद्दा absent by predicate) remains a labelling `[U]`. P9 itself stays behind D-T2
   regardless: these modes define P9's activation *semantics*; they do not admit P9 (S-04).
4. Annual objects are interval-free points; transit contacts follow §6/§7 within the year's
   horizon.

### 9.3 Test oracles

O-AO-1 (**rewritten per S-07**: the year-qualified join returns exactly the same-year object;
a kind-only join is shown to return cross-year rows and is the defect on test — the v1.0
wording demanded the impossible) · O-AO-2 (source_ref resolves to a B3.3 locator) · O-AO-3
(until D-T2, P9 windows carry `operator_role = testimony` and no activation weight).

---

## 10. `registered_writer_architecture` — how '5.0' gets written

### 10.1 Architecture contract

Unchanged from v1.0 except **invalidation (S-02)**: a change re-solves geometry iff it alters
**required geometry** — aspect direction/levels, frame-dependent resolution, target generation,
support domain, or solver convention. It re-scores only iff required geometry is unchanged
(weights, valence rules, path algebra). The dependency, not the change's label, decides; the
writer records which fired and why. (v1.0's wording — "a path change must not rebuild geometry"
beside "target-generation changes re-solve" — is reconciled: a path change that newly requires
an unsearched relation or target DOES re-solve that domain.)

- **Three objects, one writer family** (`ka_gochara`; WriterBase contract, idempotent
  per-(chart_id × generation) delete-then-insert). Emits contacts, relationship records,
  evaluated windows.
- **Per-path coarse-to-fine pruning**; interval sweep O(B log B + output).
- **Day tier on demand** with coverage; prefetch is policy, never exclusion.
- **Publication**: manifest-driven (N-10/D-41); only the release authority flips, under D-FLIP
  at J2. `'4.1'` rows are candidate-only forever.
- **Serving contract** (P-1..P-4, B3.1 §4): provenance/coverage from the manifest; absent
  authority ⇒ `unpublished`; §N.6 confirmed vs context counted separately.
- **Benchmarks as contract** (v3.0 §6.8).

### 10.2 Invariants

1. One registered writer produces `'5.0'` (Disclosure 3 closes at A6.2).
2. Lineage invalidation is explicit and dependency-driven (§10.1).
3. Every no-window answer carries its coverage object.
4. S-2's directed events for Saṅgam come **only** from the post-T0-1 kernel (aspect direction
   fixed per §6.2 inv 6, graduated dṛṣṭi with specials full — `BPHS1:16496-16502`; "every
   graha" explicitly excludes node dṛṣṭi per N-14).

### 10.3 Test oracles

O-RW-1 … O-RW-3 (all three now in the JSON; O-RW-1 asserts solver-invocation/invalidation, not
digests alone — S-07).

---

## 11. `test_oracles` — the master index and the oracle harness contract

### 11.1 Harness contract

Oracles live as data in `design/GOCHARA_TEST_ORACLES_v1_3.json`, executed by B5.3 and A5.5.
Every oracle names: the spec section it guards, the defect ids it regresses, its operands'
source, its tolerance, **a fixture labelled by kind, and a mutation that must fail it**
(S-07). An oracle that cannot fail is a §N.8 violation. **Fixture-kind policy (R3, Codex
amendment 5):** `fixture_kind ∈ {literal, constrained_generator, executable_at_A5.5}`. A
fixture is `literal` only when every input byte is written in the JSON and the assertion can
be checked with no code beyond arithmetic; anything not fully literal is
**`executable_at_A5.5`** — Stream A writes it as a test with literal inputs at the A5.5
rehearsal, and the A5.5 review checks that the named mutation fails. `constrained_generator`
is reserved for fixtures whose inputs are drawn by a fully specified generator with a pinned
seed. No fixture claims literalness it does not have. **Fixture-kind split (v1.4): 21
literal / 36 executable_at_A5.5** — three fixtures re-labelled at C8 (O-RP-3, O-RP-5b,
O-BP-2); the JSON header carries the same split. **The JSON
inventory and this index are the same set** — count stated below and in the JSON header
(F1/S-07; v1.0's JSON had 25 against 35 named, which was the reviewed defect).

### 11.2 Index (spec § → oracle ids → defect coverage) — 57 oracles

| § | oracles | defects guarded |
|---|---|---|
| 6.2 aspect direction | O-AD-1, O-AD-2, O-AD-3, O-AD-4 | **#13, T0-1** |
| 6.1 contact identity | O-RX-1 | **NK-2** (occurrence ordinal; retrograde re-crossing) |
| 1 relationship_record | O-RR-1, O-RR-2, O-RR-3, O-RR-4, O-RR-5, O-RR-6, O-RR-7 | #8, #9, #10, #22, #23, E3, S-04 |
| 2 rule paths | O-RP-1, O-RP-2, O-RP-3, O-RP-4, O-RP-5a, O-RP-5b, O-RP-6, O-RP-7, O-RP-8 | #1, #3, #4, #20, #21, RQ-7, S-03, R2-S05, father-example withdrawal |
| 3 valence | O-TV-1, O-TV-2, O-TV-3 | #11, #12 |
| 4 permission | O-PP-1, O-PP-2, O-PP-3 | #2, #3, E6, RQ-7 |
| 5 vedha | O-VI-1, O-VI-2, O-VI-3, O-VI-4, O-VI-5 | #16, #17, #25, N4, E2, M-8 |
| 6 substrate | O-SS-1, O-SS-2, O-SS-3, O-SS-4 | #6, #7, #14, #27, N2, N3, E1 |
| 7 solver | O-SM-1, O-SM-2, O-SM-3, O-SM-4 | N1, interior-extremum |
| 8 bindu polarity | O-BP-1, O-BP-2, O-BP-3, O-BP-4, O-BP-5 | N8, RQ-1, #19, #26, G-10 honesty |
| 9 annual identity | O-AO-1, O-AO-2, O-AO-3 | saham year-mixing, Tier-2 gate |
| 10 writer | O-RW-1, O-RW-2, O-RW-3 | lineage, §N.6, N-10/D-41 |
| 2/7 grain + plateau | O-GR-PLATEAU | **#24** |
| 2 P6 tārā | O-P6-TARA | **#5** |
| conformance | O-CF-N5, O-CF-N6, O-CF-N7, O-CF-DRISHTI | N5, N6, N7, #15 |

Guarded-by-construction (no separate oracle; the schema/invariant is the guard, stated per
F3): **#18** (two-frame operand selection is pinned by §8 P5a operand = the *transiting*
graha's BAV — invariant, checked in O-BP-1's fixture) — upgraded: O-BP-1's mutation covers it.
**N9** (unverified LEL annotations) is guarded on the measurement side — evaluation protocol
v2.1 §7's annotation guard + the event registry's per-row verification state; no spec oracle.

**Total: 57 oracles** (4 AD + 1 RX + 7 RR + 9 RP + 3 TV + 3 PP + 5 VI + 4 SS + 4 SM + 5 BP +
3 AO + 3 RW + 1 GR + 1 P6 + 4 CF). The JSON header carries the same count; a count mismatch
between this index and the JSON is itself a defect. (The B3.6 authoring pass itself tripped
this rule once — an intermediate draft stated 47 against 55 present; caught and corrected by
the count check. The rule earns its keep.) v1.2 renames: O-RP-5 → O-RP-5a/O-RP-5b (R2-S05
split, net +1); O-RX-1 added (NK-2, +1). **v1.3 note: count unchanged at 57** — the round-3
rework replaced fixtures and controls in place (O-PP-2, O-RP-2/3, O-RP-5a, O-BP-1, O-BP-2,
O-BP-5, O-SM-1, O-VI-2, O-RX-1, O-RR-2) and re-labelled fixture kinds; no oracle was added
or removed. **v1.4 note: count unchanged at 57** — D-SPECS C1–C10 edited O-RP-2, O-RP-7,
O-PP-1, O-PP-2, O-BP-2 and O-SM-1 in place and re-labelled three fixtures (O-RP-3, O-RP-5b,
O-BP-2 → executable_at_A5.5); no oracle was added or removed.

### 11.3 Worked-event oracle set (development cases — never held-out evidence)

Positions per E8 (L0, Lahiri); natal per L1 (build 1c092ffb; natal Venus **259.19°** — two
[L] reads of build 1c092ffb disagree on Venus: 259.1882 (LEL_CHART_STATE_RECONCILED_v1_0 §,
chart_facts, no ayanamsha predicate) vs 259.1727 (E8; AV extract v1_0 recompute input);
carried as 259.19 pending a fact_id-pinned read; no printed arithmetic depends on it). These
three events
calibrate the oracles; the evaluation protocol excludes them from scoring.

- **Marriage 2013-12-11**: Saturn 204.25° vs natal Saturn 202.43° (Δ = 1.82° = **1°49′12″**,
  return to the exalted 7th occupant); Jupiter 84.57° R in Gemini, 5th aspect on Libra
  (204.57° = **2°08′24″** from natal Saturn, **0°19′12″** from transit Saturn); Ketu 12.99° is
  **0°33′36″** from lagna 12.43°; Rāhu 192.99° in the 7th.
- **Twins 2022-01-03**: Jupiter 306.87° Aquarius (11th from lagna; 1st from the 327.06°
  Aquarius Moon — the count is written, not asserted); Saturn 288.01° is 3.95° = **3°57′** from
  natal Sun 291.96° (5L). Venus 267.83° **R** in Sagittarius (B4.1's LEL correction stands:
  Venus was retrograde at the twins' birth).
- **Father 2018-11-28**: Saturn 253.43° is 3.64° = **3°38′24″** from natal Jupiter 249.79°
  (9L) in the 9th; Saturn is 11th from the natal Moon; Sun/Jupiter/retrograde Mercury in the
  native's 8th.

---

*Reworked at B3.8 per both round-2 reviews (reconciliation: RECONCILIATION_DESIGN_SPECS_v1_1.md);
reworked again at B3.8b per the round-3 Codex review (REWORK; 3 closed, 12 partly closed,
4 new blocking — reconciliation: RECONCILIATION_DESIGN_SPECS_v1_2.md); reworked a third time
at B3.8d per D-SPECS_DECISION_v1_0 (FREEZE_WITH_CONDITIONS — conditions C1–C10 landed
verbatim; reconciliation: RECONCILIATION_DESIGN_SPECS_v1_3.md). Nothing herein
overrides a native ruling; every `[P]` element names its ruling and its operator role; every
figure traces to the sealed evidence appendix, v3.0 §8, the pinned G-10 extracts, or the
printed arithmetic. `status: FROZEN` is deliberately NOT set: B3.9 marks it only after the
steward's diff of v1.4 against v1.3 confirms nothing outside the named edits changed.*

---
artifact: ST-H-UNKNOWN-20261002
kind: steward ruling (recorded by Stream B so AM-5's ruling_ref has something to cite)
ruling_id: ST-H-UNKNOWN-20261002
decided_by: "steward (madhav-1f), on the native's standing authority of 2026-09-30"
date: 2026-10-02
source_message: "M20261001T204900-21ac"
recorded_by: stream-B (Exec B), 2026-10-02
status: IN FORCE until lifted class by class
---

# ST-H-UNKNOWN-20261002 — signature-house set H unknown for eight classes

**Fact (not a decision).** GOCHARA_DESIGN_SPECS_v1_4 §2.2, S:307–312: the classes
`achievement_recognition`, `business_launch`, `financial_deception`, `foreign_settlement`,
`parental_event`, `property_acquisition`, `psychological_arc`, `spiritual_turn` have **H = unknown**;
"no H is assigned here without a citation"; an unknown necessary predicate makes P3/P4 admission
`unqualified` for the class until a versioned `rule_path` row with a cited source supplies H.

**Ruling.** For these eight classes the H-dependent paths are carried as an
**`inputs_unavailable` exclusion**, and the class **seals as `searched_scoped`, never complete-empty**.
It is lifted **class by class** when H is ruled for that class.

**Which paths (my derivation, for the steward to confirm).** The paths whose prerequisites need H:
**P1** (prerequisite (2) `natal_bhava_relationship`), **P3** (`p3_contact_house_or_lord`) and **P4**
(`p4_double_transit`) — see `PREREQUISITE_EVALUATION_ANSWER_v1_0`. P2 (`house_from_moon`) and P5 do
not depend on H and are not covered by this ruling (P5 is withheld by `ST-P5-HOLD-20261001`).

**Disposition in AM-5 terms**, per (class, covered path):

| field | value |
|---|---|
| `disposition` | `excluded` |
| `exclusion_reason` | `inputs_unavailable` (a *degrading* reason) |
| `ruling_ref` | `ST-H-UNKNOWN-20261002` |
| `basis` | `ruling:ST-H-UNKNOWN-20261002` |

**Lifting.** When a versioned `rule_path` row with a cited source supplies H for a class, that class
leaves this ruling in a **new generation** with the paths `included`; the ruling is not edited.

**Grammar check (migration 1206).** `ST-H-UNKNOWN-20261002` matches `^[A-Za-z0-9._-]+$` and
`ruling:ST-H-UNKNOWN-20261002` matches the `basis` grammar (verified with PostgreSQL's regex engine,
2026-10-02).

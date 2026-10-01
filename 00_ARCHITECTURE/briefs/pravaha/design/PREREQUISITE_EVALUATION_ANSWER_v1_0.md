---
artifact: PREREQUISITE_EVALUATION_ANSWER
version: "1.0"
status: ANSWER TO STEWARD QUESTION (not a spec version; no code)
date: 2026-10-02
author: stream-B (Exec B)
question: steward M20261001T202239-f413 — what each not-yet-evaluated declared prerequisite asserts, whether it is true by construction, its false/unknown conditions, and the pinning oracle
sources: >
  S = GOCHARA_DESIGN_SPECS_v1_4 · O = GOCHARA_TEST_ORACLES_v1_4 · F5 = migration 1155:822–832 ·
  path→prerequisite map = services/gochara_rules/registry.py:466–596 · operand declarations =
  services/gochara_kernel/rule_registry.py:151–185 (Stream A worktree, read-only) · draft = GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.6
---

# Prerequisite evaluation — what each remaining declared predicate means

**Governing rules.** F5 (1155:822–832): a prerequisite result of `NULL` counts as *unknown*; any `false` ⇒ `not_admitted`; else any
`unknown`/`NULL` ⇒ `unqualified`; else `admitted`. Every record carries its path's *full* declared list. S:160–163 and S:399–402:
unknown ≠ false. §0 (S:56–62): `testimony` annotates and never admits. **A `NULL` left on a predicate that CAN be decided is a
defect** — "unevaluated" is not "unknown" (§N.8). Path → prerequisites: P1 = period_running_at, natal_bhava_relationship,
transit_relation · P2 = house_from_moon · P3 = p3_contact_house_or_lord · P4 = p4_double_transit · P5 = av_polarity_declaration_exists ·
P6 = admitted_window_exists. (period_running_at, p4_double_transit: evaluated today — O-PP-1/O-PP-2, O-RP-2/O-RP-3.)

| predicate (path) | (a) asserts | (b) by construction, or independent evaluation (facts) | (c) false / unknown | (d) oracle |
|---|---|---|---|---|
| **natal_bhava_relationship** (P1 #2) | The period lord has a natal relation to the class's signature-house set H: occupancy/ownership `[D]` scored; node-dispositor `[P]` D-PADMIT, non-node dispositorship and association (no clause in PG249:C1/PG250:C1) → testimony (S:245–261). | **Independent.** L1 natal graha positions + sign lordship + H from the class truth table (S:286–312). Logic already exists: `permission.period_lord_relation` (permission.py:103). | false = no relation of any kind; unknown = H unknown (8 classes, S:307–312) or the lord's natal position unreadable. **S silent** on the stored result for a testimony kind; *mine:* `true` with `operator_role='testimony'` (§0: role, not result, stops it admitting). | O-PP-2 (Mars occupancy scored; Rahu dispositor testimony; half-open boundary), O-RR-3 |
| **transit_relation** (P1 #3) | The record's own transit contact (agent, residence/aspect/conjunction, object) exists solved in this generation (S:246). | **True by construction** for any transit-relation record — contact_id is NOT NULL, 1155:717–727 refuses a contact not owned by (chart, generation), 1155:733–747 require relation ∈ relations_searched and t_in ∈ horizon — **but compute it as a read-back of the contact row, never a hard-coded `true`**. | false: never for a persisted row; unknown: none (a truncated contact still exists). **S silent** for P1 *natal-fact* records (contact_id NULL): F5 still demands a result and 1155 has no "not applicable". *Mine:* do not materialise natal-fact P1 rows as admission-bearing records — carry (2) as the evaluated predicate on the transit record with the relation in `source_fact_ids`; if retained as testimony annotations, their result is `unknown`. | O-RP-8, O-AD-1, O-RP-2/3 (contact semantics) |
| **house_from_moon** (P2) | Counting inclusively from the native's janma-rāśi (Moon frame, §0), the agent's residence sign gives house h and h lies in the agent's cited set (Phaladīpikā XXVI.1–8; adverse 12/8/1 for Saturn/Sun/Mars/Jupiter, D-RQ5) (S:263–270). | **Independent.** L1 natal Moon sign + the residence contact interval + the cited per-graha table (`favourable_houses.py`, merged). Vedha is a soft factor, never a gate (S:401). | false = h outside every cited set for that agent; unknown = natal Moon unreadable, or no cited set (node rows are not independently sourced — AM-9, Ketu-12). A relative's event can't carry it (kgrr_relative_frame_ck). **S silent** on polarity: rule_registry.py:164 names only `p2:adverse_house_set`. *Mine:* test h ∈ cited favourable ∪ adverse set and leave polarity to the valence step (§3.1/D-RQ5); rename the operand `p2:cited_house_set`. | O-RP-5a, O-RP-1, O-RP-5b |
| **p3_contact_house_or_lord** (P3) | P3_admit(agent, class) = ∃h∈H contact(agent,h) ∨ ∃ℓ∈L(H) contact(agent,ℓ); contact(h)=residence∨aspect, contact(ℓ)=conjunction∨aspect with ℓ's natal point (S:276–285). | **True by construction of qualified enumeration** (S:412–414 inv 7, O-RP-8 — a contact is enumerated only if a selector names it) **iff** the record's object ∈ H ∪ L(H) and its relation is permitted for that object kind; evaluate as a read-back against the truth table + L1 lagna/sign lords. | false = object ∉ H ∪ L(H) or relation not permitted for the kind (an enumeration defect); unknown = H unknown for the 8 classes (S:307–312) or ℓ's natal position unreadable. | O-RP-8, O-RP-1, O-RR-3 |
| **av_polarity_declaration_exists** (P5) | A 1157 declaration row exists for the L1 AV-build convention the bindu operands come from and governs the operand's fact category (draft §AM-7). | **Independent write-time read-back** (1157 defers the SQL gate to the writer; O-BP-3). | **false/unknown are never stored:** an absent or mismatched declaration means no P5 record is written (AM-7) and the gap is an AM-5 ledger `missing_inputs` / `inputs_unavailable` exclusion; stored P5 records carry `true`. Per-form missingness (S:344–351: BAV absent ⇒ P5a alone, SAV ⇒ P5b alone, whole AV build ⇒ all) is a form-level obligation state, not this predicate. | O-BP-2 (A/B/C), O-BP-3, O-BP-1 |
| **admitted_window_exists** (P6) | A scored, admitted window of the same chart/generation contains the day being annotated (S:385–393, M-3). | True by construction of the emission path (P6 rows exist only inside admitted windows), but evaluate as a read-back of the parent window (1156, sealed generation). **P6 is withdrawn from this batch (AM-8; AM-4 defers parent-context/containment).** | false = day outside every admitted window (then no row exists); unknown = the class's window search partial/not searched (AM-5 states). **S silent** beyond that until the P6 design lands. | O-SS-4; B6-F17 is still a sentinel |

**Consequence.** P1 reaches `admitted` only when all three of (1), (2), (3) are evaluated `true`; P2/P3 need their one predicate evaluated; P5 records are `true` whenever
they exist; P6 stays deferred. None may be hard-coded or left `NULL`; the rule logic for (2), the P3 membership and the P2 table already lives in Stream B's
`services/gochara_rules` (permission.py, registry/frames, favourable_houses.py) — the materialiser needs to call it.

**On Stream A's reading of AM-5 (M20261001T202801-8ee8).** Confirmed with one precision: an *un-ruled* deferral (inputs unavailable) is a **seal blocker** — a
`missing_inputs` interval makes `ka_gochara_search_completeness_violations` refuse the seal. The sanctioned way to seal with a named deferral is an
`inputs_unavailable` / `disabled_form` / `tier_withheld_by_ruling` **exclusion carrying a `ruling_ref`** (a steward/native ruling, in the verified preimage): it seals and
degrades "complete-empty" to `searched_scoped`. So: blocker until the obligation can be searched **or** a ruling declares the exclusion.

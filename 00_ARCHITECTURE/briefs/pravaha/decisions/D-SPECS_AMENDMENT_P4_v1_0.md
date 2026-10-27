---
artifact: D-SPECS_AMENDMENT_P4
version: "1.0"
status: RECORDED_NATIVE_DIRECTION
date: 2026-10-27
recorded_at: 2026-10-27T00:00:00+05:30
campaign_id: kalayantra
item: GP-13
recorder: owner surrogate (session madhav-f9)
ruling_id: NR-P4-DEMOTION-20261027
authority: "delegated — OWNER-DECISIONS-20261027-E → FOURQ-CLOSURE-20261027 (AI panel: Gemini Argon + GPT-6-Astra; closure by the owner surrogate). Not a direct native ruling; the native may override at any time."
governing_charter: 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md
amends:
  - artifact: GOCHARA_DESIGN_SPECS_v1_4.md
    section: "§P4 (line 314) — 'scored'"
    frozen_sha256: d5097ca18a721d8005cab593f3c3865227d22ff1435b8adc9973275d3f786a47
    frozen_at_commit: eea2610d0
    method: by reference — the spec file stays byte-identical
register_entry: CCD-029
changelog:
  - "1.0: Record the native's direction to shut off the Jupiter–Saturn double transit (P4), his delegation of the closure to the surrogate after an AI-panel consultation (Gemini Argon, GPT-6-Astra), the surrogate's closure (P4 off entirely) and the provenance grounds; amend the frozen spec's P4 role from scored to off by reference."
---

# Amendment to GOCHARA_DESIGN_SPECS v1.4 §P4 — double transit moves from scored to testimony

## Native direction

The native's wording (2026-10-27, to the owner surrogate):

> "why is there so much emphasis on a specific Jupiter-Saturn joint transit? Where does it come from? What's the source? I'm a bit apprehensive about whether that is specific to me or a leakage, because everything else is general, but that particular point comes up several times. Can you investigate it? It may be genuine. It may have a good reason, but it seems suspicious, and I want to shut it off."

The native's delegation of the decision (2026-10-27, verbatim):

> "Put the four questions to Argon, Gemini Argon, and GPT 6.1 Astra, and then reconcile and take a call. Close these four questions. Build the full plan before we kick it off."

Closure under that delegation (surrogate, after Gemini Argon and GPT-6-Astra both answered YES; ledger `FOURQ-CLOSURE-20261027`): **P4 is switched off entirely** — removed from scored computation and derived counts; the event-targeted widened leg deleted; the legacy aspect-only detector retired as well; no double-transit formulation is served until the panel re-authors a testimony card blind from scratch. Status of this record becomes RECORDED_NATIVE_DIRECTION on the strength of the delegation; the native may override at any time.

## What changes

| Element | Frozen spec v1.4 | Amended |
|---|---|---|
| P4 Jupiter–Saturn double transit, `operator_role` | scored | **off** — disabled, not evaluated, not served; `testimony-pending re-authoring` (modern practice, K.N. Rao school; no page-anchored classical statement in the corpus) |
| Composition operator `double_transit_mixed` and the OR-combination with `double_transit` | present | deleted (not relabelled) |
| Legacy aspect-only `double_transit` operator | present | deleted (with `double_transit_mixed`); the struck citation constant removed |
| Permission generator #10 `guru_shani_double_transit` and its two mirrors | contributes to the scored sum | never evaluated; registered for table stability; emits an empty row (`active false`, weight 0, `status retired_pending_reauthor`, `empty_reason`); `SYSTEM_WEIGHTS` unchanged, so no other generator is re-scaled |
| `bg_transit_rules` rows of kind `double_transit` (7) | cite "Phaladeepika ch.26 §double-gochara" | relabelled by migration 1412 (DML only) with the prefix `RETIRED_PENDING_REAUTHOR (FOURQ-CLOSURE-20261027)` and an honest attribution; the non-existent citation is struck; row count stays 7 of 76; integrity pin resealed; serving consumers skip retired rows with a recorded reason |
| Stored fitted trigger weight for this current (unwired) | present | deleted |
| WS-3 canon rows on this rule marked `verified: true` | as marked | `verified: null` with a verification note |

No other line of the spec changes. No rebuild or backfill of Gochara 5.0 candidate rows follows (OWNER-STOP-5_0-EXECUTION-20261027 stands): code, tests, doctrine labels and one relabel migration only. FROZEN orchestrator paths are untouched. The ND-H-20261005 "CORE + DVI houses" delegate decision is superseded by this record (document left in place).

## Grounds (ids only)

1. Corpus check, surrogate ledger `DOUBLE-TRANSIT-PROVENANCE-20261027`: no text among the sixteen ingested states the rule; nearest hits are a Tier-D modern Nādi compilation on simultaneous benefic transits — a different claim.
2. Provenance audit `DOUBLE_TRANSIT_PROVENANCE_v0_1` (outcome-blind): the rule entered the repository after the life-event data, with code comments tying it to the native's biography; its first seed (migration 397) cited a passage that migration 565 and three external reviews found non-existent; Pravāha v3.0 sealed doctrine already classes it modern practice, `uncited_extension`.
3. Confirmed specimen-driven widening: PR #651 (commits f6af3e115, d2d9555e6) added the mixed leg and OR-combination with the stated reason that a named native specimen was otherwise undetectable, and extended the citation by a self-declared "judgment call" (verified in the commit messages by the surrogate).
4. Promotion was event-driven in documents (D-5 acceptance criterion; Pravāha v1/v2 "worked events"; Kimi retrodictive ranking; ND-H-20261005 "by recall"). Parameters unsourced, set once, never re-tuned; the one fitted weight unwired.
5. Independent reviews (`FABLE-REDTEAM-RULEBOOK-RESULT-20261027`, `ARGON-REDTEAM-RULEBOOK-RESULT-20261027`) both endorse demotion and recommend deleting the PR #651 leg rather than relabelling it.

## Re-admission

P4 may return to "scored" only through the Rule Book panel protocol (RULE_BOOK_PROGRAMME v0.2 §2): a page-anchored pre-modern quotation stating the rule, surviving deterministic verification and ratification; any accuracy claim belongs to the public-chart track. Never a backward look at the native's events.

## Cross-references

Surrogate ledger: `OWNER-DECISIONS-20261027-D`, `DOUBLE-TRANSIT-PROVENANCE-20261027`, `FABLE-REDTEAM-RULEBOOK-RESULT-20261027`, `ARGON-REDTEAM-RULEBOOK-RESULT-20261027`. Cockpit items GP-11, GP-12, GP-13. Code: branch `kalayantra/demote-double-transit-testimony` (commit afcbd67), change note `00_ARCHITECTURE/briefs/pravaha/decisions/CHANGE_NOTE_DOUBLE_TRANSIT_DEMOTION.md`. Kernel: P4 excluded for every class via `registry.DISABLED_PATHS` / standing exclusions (`tier_withheld_by_ruling`); verifier copy `VERIFIER_PATH_RULINGS['p4']`.

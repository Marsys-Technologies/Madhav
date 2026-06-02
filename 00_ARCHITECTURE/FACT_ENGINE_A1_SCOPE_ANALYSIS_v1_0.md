---
artifact: FACT_ENGINE_A1_SCOPE_ANALYSIS_v1_0.md
canonical_id: FACT_ENGINE_A1_SCOPE_ANALYSIS
version: 1.0
status: CLOSED 2026-06-02 (design baseline — sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0)
authored_by: Claude (Cowork) 2026-06-02
purpose: >
  Answer the native's question before any engine fix begins: is the A1 (fact engine) brief
  correct, and does it specify SIGNIFICANTLY MORE data per chart than FORENSIC v8.0? Compares
  the A1 brief's specified output scope against v8.0's actual content, and checks the brief's
  verification method against the native's locked decisions of 2026-06-01.
reviews:
  - 00_ARCHITECTURE/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md (the A1 engine brief; DRAFT, 2026-05-27)
  - 00_ARCHITECTURE/FACT_ENGINE_BRIEF_REVIEW_v1_0.md (prior engineering review; DRAFT, 2026-05-27)
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md (the benchmark; 27 sections, Lahiri)
  - platform/python-sidecar/pyjhora_adapter/compute.py (what the engine emits today)
relates_to:
  - 00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (this feeds the A1 Contract Registry entry)
  - CONVERSATION_HANDOFF_2026-06-01_v2_0.md §2 (the native's locked decisions)
---

# A1 Fact-Engine Brief — Scope & Correctness Analysis

## Verdict (three findings)

1. **Spine: CORRECT — keep.** The brief's architecture is sound and should be retained verbatim:
   PyJHora → typed per-function adapter → canonical JSONL (auditable, content-addressed,
   gated) → deterministic loader → existing DB schema unchanged; never-drop signal set;
   integers/decimal-strings not floats; `chart_id` first-class.

2. **Output scope: NOT CORRECT for the goal — under-specified.** The brief never writes an
   enumerated output contract that is a superset of v8.0. It explicitly names ~12 of v8.0's
   ~25 data domains (§7) and defers the rest to "diff field-by-field against FORENSIC v8.0."
   The "richer than v8.0" ambition the native remembers is **not written as a gated contract
   anywhere** — it appears only as a "pre-finding to confirm" in the render-coverage audit. So
   nothing in the brief guarantees output ≥ v8.0, let alone "significantly more."

3. **Verification method: STALE — contradicts the 2026-06-01 locked decisions.** The brief and
   its review are built on triangulation + JH-parity + an independent pyswisseph cross-check +
   a Phase-0 "reproduce FORENSIC" ayanamsha gate. The native's later locked decisions reject
   all of these. The verification spine must be rewritten.

## §1 — Output-scope comparison (A1 brief vs FORENSIC v8.0)

v8.0 is single-ayanamsha (Lahiri), ~27 sections. The A1 brief's explicit output list is §7
Phase 1 (core) + Phase 2 (depth): D1 positions, divisionals, ascendant/houses, panchanga,
dashas, shadbala, ashtakavarga, KP, Jaimini karakas, sahams, arudhas, Tajaka/varshphal.

**Explicitly in the brief (~12 domains):** D1 · divisionals D2–D60 · houses/cusps · KP ·
Vimshottari/Yogini/Chara dashas · shadbala · ashtakavarga · chara karakas · sahams (36) ·
arudhas · panchanga · Tajaka varshphal.

**In v8.0 but NOT explicitly enumerated in the brief (~13 domains):**

| v8.0 § | Domain | In A1 brief? |
|---|---|---|
| §8 | Saturn Kakshya zones | not named |
| §9 | Avastha diagnostics (6 states × grahas) | not named |
| §11 | Upagrahas (full 9) | only implied ("sensitive points") |
| §12.1 | Special Lagnas (8, incl. v8.0 corrections) | not named (distinct from sahams) |
| §14 | Stellar matrix / Navatara (9-tara) | not named |
| §16 | Aspects — Parashari drishti + Western + Bhav-Madhya | not named |
| §17 | Chalit kinetic shifts | not named |
| §18 | Chandra chart | not named |
| §19 | Kota Chakra | not named |
| §20 | Deity assignments | not named |
| §24 | Longevity (Kalachakra Paramayush) | not named |
| §26 | Yogas register (incl. Mercury 8-system convergence) | not named |
| §23 | Cross-reference matrices | not named |

**Today's engine** (`compute.py` return keys) emits ~6–8 domains: ascendant/lagna, houses,
grahas, vargas, dashas, panchanga, sensitive_points, ayanamsha. The depth set (shadbala,
ashtakavarga, KP star/sub-lords, Tajaka, yogas, avastha, karakas, kakshya, etc.) is **not
returned** — the documented root cause of the forensic render landing at ~38% of v8.0.

**Conclusion:** the brief is a *partial enumeration plus an oracle crutch*, not a written
superset. Built literally to the §7 list, the engine would still omit ~half of v8.0's domains.

## §2 — Verification method vs the locked decisions

| Brief / review says | Locked decision (handoff 2026-06-01 §2) |
|---|---|
| §0/§4.2 independent **pyswisseph cross-check** ("two engines agreeing = absolute confidence") | "No parallel run." PyJHora's output **IS** the source of truth by construction; no second engine to triangulate against. |
| §4.1 "diff field-by-field against FORENSIC"; review R1/R3 "**JH-parity** oracle", primary oracle = JHORA_TRANSCRIPTION | **No JH-parity oracle anywhere** — not in code, briefs, tests, or fixtures. |
| §4.4/§7.0 **Phase-0** ayanamsha "reproduce FORENSIC/JH" hard gate; review R5 extra JH reference charts | **Phase-0 spike skipped**; verification = **internal consistency only** (six categories). |

Both the brief and its review pre-date the locked decisions by five days and were never
approved (both still `DRAFT`). The shipped PyJHora implementation (PR #184) followed the
*leaner* locked path — which is **why it is thin**: see §3.

## §3 — The synthesis: a completeness vacuum

The brief's mechanism for "is the output complete?" was **the oracle** — diff every field
against FORENSIC v8.0 section by section. When the native (correctly, for cost/architecture
reasons) removed triangulation and the JH/FORENSIC oracle, **nothing replaced the oracle as
the completeness contract.** The engine therefore shipped with only the domains that were
easy to emit (~6), and "completeness vs v8.0" silently became unenforced. The PyJHora→
pyswisseph→rebuild churn compounded it, but the root structural cause is: *the brief's only
definition of "complete" was a verification step that policy later deleted, and no enumerated
output contract was put in its place.*

This is exactly the native's stated risk: A1 is the foundation; with no enforced completeness
contract, A1 under-produces, and every downstream asset (A2 render, A3 facts, A10+ synthesis)
inherits a thin, partially-invalid input.

## §4 — Recommended fix (to the brief, before any coding)

1. **Replace the oracle-based completeness mechanism with an explicit enumerated output
   contract.** The A1 contract must list **every v8.0 domain (all 27 sections) PLUS the
   additional depth PyJHora can derive** (e.g. KP sub-sub-lords, fuller yoga catalogue,
   per-ayanamsha variants), each with a per-domain acceptance gate, **× 5 ayanamshas**. This
   becomes the A1 entry in the Asset Contract Registry (charter §F). "Richer than v8.0" stops
   being a memory and becomes a checklist.
2. **Demote FORENSIC v8.0 from value-oracle to coverage checklist.** Per the locked policy,
   v8.0 is no longer a value-parity target. It remains the **structural-completeness benchmark**:
   "does the engine emit every domain v8.0 has, at ≥ its granularity?" — a count/coverage test,
   not a value diff.
3. **Rewrite §0/§4/§6/§7.0 to internal-consistency-only.** Remove pyswisseph cross-check,
   JH-parity, and the Phase-0 reproduce-FORENSIC gate. Verification = the six internal-
   consistency categories (row/coverage counts, schema, structural invariants, cross-asset FK,
   layer gates, determinism). Retain the §3 adapter/pinning discipline and §1.2 schema identity.
4. **Keep the brief's spine (§1–§3) and the review's R4 (isolation/cutover), R6 (tz generality),
   R7 (markdown renderer as a second projection), R8 (assert real ephemeris source).** These
   are independent of the verification-policy flip and remain valid.

## §5 — Decision the native must make (downstream-invalidation risk)

Under "PyJHora is the source of truth by construction," PyJHora computes **JH-style Vimshottari
dates**, which run **7–9 days earlier** than the FORENSIC-canonical dates v8.0 deliberately
chose (FORENSIC §5.1 / GAP.09). The LEL retrodictive calibration (Sessions 16–25) was tuned to
the **later FORENSIC dates**. So adopting PyJHora dates shifts every dasha boundary and would
invalidate that calibration. Choose one, explicitly, before A7 (dashas) is rebuilt:

- **(a)** Accept PyJHora/JH dates as canonical and **re-fit the LEL calibration** to them; or
- **(b)** Declare the FORENSIC dates a **standing override** of PyJHora output for dasha timing
  only, documented so it is not silent drift.

This is the concrete form of the native's "downstream data would be invalidated" worry, and it
must be settled at the A1/A7 contract level, not discovered later.

---

*End of FACT_ENGINE_A1_SCOPE_ANALYSIS v1.0 — DRAFT for native review, 2026-06-02. Modifies
nothing canonical. Feeds the A1 entry of the Asset Contract Registry (BUILD_GUARANTOR_SWARM_
CHARTER §F).*

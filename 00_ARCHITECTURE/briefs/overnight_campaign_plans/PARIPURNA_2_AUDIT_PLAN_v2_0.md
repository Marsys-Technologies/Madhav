---
version: 2.0
status: CURRENT (native-directed 2026-08-15)
supersedes: PARIPURNA_AUDIT_PLAN_v1_0.md (v1 executed and FAILED its own bar —
  see §0; its report is retained as evidence, NOT as a findings baseline)
purpose: A comprehensive, mechanically-enforced end-to-end audit of the elevated
  MARSYS-JIS instrument — code + data + live MCP — that cannot be completed by
  assertion.
---

# PARIPŪRṆA-2 — THE COMPREHENSIVE AUDIT

## §0 WHY v1 FAILED (design inputs, not blame)

Measured, not inferred:
| v1 promised | v1 delivered |
|---|---|
| 6–10h, $40–80 | 31 min, $5.32 |
| every registered tool swept | **8 of 125 live tools (6.4%)** |
| LLM-consumability test (AM-6) | never run |
| 21-question quality measurement (E1) | never run |
| 25-fact classical battery (A2) | not evidenced |
| guards mutation-tested (D1) | not evidenced |
| adversarial battery (AM-5) | not evidenced |
| desk exemplars committed (AM-9) | directory left empty |
| every claim detector-cited (R16) | **top-ranked finding FABRICATED** |

The fabrication matters most: GAP-C1 claimed `assess_marriage` served an empty
`seventh_lord_placement`. That field exists in NEITHER the serving code NOR any
live response. Two further findings were real-symptom/wrong-diagnosis. The
verifier missed all three because it sampled 7 claims and never that one — and
it had MCP-only access, so 2 of 7 came back CANNOT-VERIFY.

**Root cause (the same one this whole arc keeps re-learning): every v1 control
was PROSE. An agent under time pressure satisfies prose by assertion.** v2's
controls are executable.

## §1 THE ENFORCEMENT HARNESS (the core change)

`/Users/Dev/shad_overnight/audit_gate.py` — already built and self-tested.

  `init`   builds a coverage manifest from a LIVE tools/list snapshot.
           REFUSES an inventory < 100 tools. (Source-grep is banned: verified
           2026-08-15 it returns 29 names including the literal test fixture
           `definitely_not_a_real_registered_tool_xyz`. Live server only.)
  `status` progress readout.
  `verify` **THE GATE.** Exit 0 ONLY when:
           · every one of the 125 tools carries a verdict from a closed
             vocabulary, AND an evidence file that exists, is non-empty, and
             parses as JSON (NOT-APPLICABLE requires a written justification)
           · every finding carries id + claim + **reproduce_cmd** + evidence
             file that EXISTS + severity tier
           · all 10 dimensions signed off
           · zero findings is itself rejected as implausible
           It reports unreferenced evidence files (the fabrication signature).

**Binding rule:** the conductor MAY NOT post `RUN-TERMINAL` until `verify`
exits 0 and its signed `AUDIT-COVERAGE-VERIFIED:` line is pasted verbatim into
the ledger. PARĪKṢAKA re-runs `verify` itself and re-executes a **random 15%
sample of finding `reproduce_cmd`s**, comparing output to the stored evidence.
A finding that does not reproduce is deleted from the report and recorded as an
audit-integrity defect.

Self-test performed by the desk (2026-08-15): the gate blocked a 3-tool
inventory, blocked 125 unverdicted tools (136 problems), and **caught a
fabricated finding whose evidence file did not exist** — i.e. it catches
v1's exact failure.

## §2 EVIDENCE PROTOCOL (anti-fabrication, mandatory)

E-1 EVERY MCP call is saved raw: `pp2-audit/evidence/<tool>__<scenario>.json`.
E-2 EVERY finding carries a `reproduce_cmd` a third party can paste and run
    (an MCP call with exact args, or a `psql`/`rg` one-liner).
E-3 **A claim about a served field REQUIRES the field to appear in a saved
    response.** Never describe a field you did not observe. (v1's fabrication.)
E-4 **A claim about code REQUIRES file:line.** Never "likely a mapping bug".
E-5 TRIANGULATION: user-seat (MCP) ↔ code (file:line) ↔ data (SQL). A
    divergence between ANY two is itself a finding.
E-6 Diagnosis ≠ symptom. State the mechanism or mark it
    `DIAGNOSIS-INCOMPLETE` — v1's wrong-cause findings are worse than none.

## §3 DIMENSIONS (ten — the six from v1, corrected, plus four never considered)

A ASTROLOGICAL CORRECTNESS · FORENSIC 7/7 both charts · 25-fact classical
  re-derivation (dignity, aspects, shadbala column, dasha boundaries, vargas) ·
  **R24 nodal 5/7/9 census across EVERY aspect-consuming surface** · 10 fired
  yogas re-derived from L1 · promise rubric bounded-scoring census (R18) ·
  field-vs-64-LEL retrodiction via the harness only (R13 ABSOLUTE — no fitting)
  · tier honesty (shape_only absolutes suppressed end to end) · **the open
  marriage-zero-gochara-windows question: mechanism, not restatement**.
B DATA COMPLETENESS · 27-class census on every producing table, BOTH charts ·
  invariants (contiguity gaps==0, coverage [0,H], null 25×10, snapshot hash
  recomputed) · identity adoption (R17) · G4/G9/G10 data proofs.
C SERVING/MCP — **ALL 125 TOOLS, no exceptions** · realistic args, both charts
  where chart-scoped · honest envelope (empty_reason, coverage, tier facets,
  resolution_disclosure, drill pointers) · **journey tests** (marry / health
  rough-patch / elect / remedy / prashna / session recall) · assess suite over
  13 domains · facade elevations per view · latency p50/p95 · zero 5xx.
D ARCHITECTURE & GOVERNANCE · **guards MUTATION-tested** (break it, prove CI
  fails, revert) for FM-23/25/26 + fact-category-pin-lint · orchestrator
  contract frozen · `_migrations_applied` == files · drift/schema validators ·
  §N.7/§N.8 honesty sweep (10 flags → real detector each) · G14 loop cycling.
E EXPERIENCE & DEPTH · **G15 21-question dark-corpus re-run, bright% ON RECORD**
  · **LLM-CONSUMABILITY: a fresh sonnet agent with ONLY MCP tools answers 5
  natural questions; PRATINIDHI (opus-max) grades tool selection, synthesis,
  citation fidelity, depth, honest-uncertainty** · 3 opus-max whole-chart depth
  reads on served output only · jargon/salience register (AM-7).
F RESIDUAL CONSOLIDATION · every named residual across ALL ledgers → GAP vs
  BY-DESIGN-OPEN, owner, size. **Plus: re-verify all 8 v1 findings from
  scratch** (1 known fabricated, 2 wrong-cause, 1 fixed in PR #1287).
G ★NEW — SECURITY & ISOLATION · cross-chart leakage (chart A's data via chart
  B's id?) · entitlement/profile scoping (does a narrow OAuth profile see more
  than it should?) · injection through free-text params (question_frame,
  domain) · secrets never echoed in responses/errors · error messages don't
  leak schema/internals (the parseDaterange crash leaked a Postgres literal).
H ★NEW — DETERMINISM & CONCURRENCY · same call twice == same answer (modulo
  documented time-dependence) · concurrent calls don't corrupt session memory ·
  pagination stability under repeat · as_of backdating reproducibility.
I ★NEW — CONTRACT CONFORMANCE · every response validated against the tool's
  DECLARED schema · required envelope fields present · `density_contract`
  honored (byte caps, facets, empty_reason) · budget_kb trimming actually
  trims and reports · deprecated-name gates behave.
J ★NEW — REGRESSION & EDGE · golden-fixture comparison where fixtures exist
  (Δ2's estate) · boundary dates (birth instant, horizon end 2084, pre-birth,
  leap day) · nonexistent chart UUID · malformed args · unknown domain ·
  not_applicable-tier class requested directly · pagination past end · the
  zero-history chart (1c826d5a) through C's full journey set.

## §4 PHASES WITH HARD GATES (no phase N+1 before N's gate)

P0 INVENTORY — live tools/list snapshot → `audit_gate.py init`. Commit the
   snapshot. **Gate: manifest exists with ≥125 tools.**
P1 SWEEP (parallel, ≤4 sonnet probes) — dimensions C + I + J across all 125
   tools; every call saved. **Gate: `status` shows 125/125 verdicted.**
P2 DEPTH (parallel) — A + B + G + H. **Gate: dimension sign-offs recorded.**
P3 ADVERSARIAL — D (mutation-test guards) + E (G15 + LLM-consumability +
   depth reads). **Gate: bright% recorded; consumability grades recorded.**
P4 CONSOLIDATE — F, including re-verification of every v1 finding.
P5 REPORT + GATE — write the report, run `verify`, paste the signed line.
P6 PARĪKṢAKA (opus, **DB + MCP + repo access** — v1's verifier was MCP-only,
   which caused its CANNOT-VERIFYs) — re-runs `verify`, re-executes a random
   15% of `reproduce_cmd`s, and specifically attempts to REFUTE the three
   highest-severity findings. Only then may the terminal marker post.

## §5 EXECUTION MODEL

Conductor + probes: **sonnet** (native-directed). Opus ONLY for PARĪKṢAKA
verdicts, PRATINIDHI grading/rulings. Never Fable. Existing supervisor rails
apply: mechanical watchdog, strike file, FM-27 smart polling, FM-28 nets.
READ-ONLY on production: no builds, no product-table writes, no deploys.
Trivially-safe fixes (docs/tests/CI) may ship as PRs; everything else lands in
the gap ledger for the native to sequence.

ENVELOPE (FM-28 — nets, not stopwatches): expect **8–16h and $60–120** across
multiple supervisor-relaunched sessions. A session ending early with the gate
UNSATISFIED is not "done" — the supervisor relaunches and the conductor
continues from the manifest (which is the resume state). **Cost cap $200;
warn $140.** Finishing fast is not a goal and is not rewarded; the gate is the
only definition of done.

## §6 DELIVERABLE

`PARIPURNA_2_AUDIT_REPORT_v1_0.md` —
 §1 lineage scoreboard (every G-card G1–G16, every ruling R17–R28, master-plan
    §7 dashboard) with verdict + file:line/evidence-file per row
 §2 ten-dimension findings
 §3 THE GAP LEDGER — ranked TIER1→TIER4, each with reproduce_cmd, diagnosed
    mechanism (or DIAGNOSIS-INCOMPLETE), and a proposed remediation lane
 §4 the honest "is it flawless?" answer: flawless / graded-and-disclosed /
    needs-next-wave
 §5 coverage attestation (the signed gate line) + PARĪKṢAKA re-verification
 §6 audit-integrity section: v1 findings re-adjudicated; any v2 finding that
    failed PARĪKṢAKA reproduction, named.

## §7 DEFINITION OF DONE (mechanical, not editorial)

`audit_gate.py verify` exits 0 · its signed line is in the ledger ·
PARĪKṢAKA's independent re-run + 15% reproduction sample pass · report §1–§6
complete. Then, and only then: `RUN-TERMINAL: SESSION-PARIPURNA-2-COMPLETE`.

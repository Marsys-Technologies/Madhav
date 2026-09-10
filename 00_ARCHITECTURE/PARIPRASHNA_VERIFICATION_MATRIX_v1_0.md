---
artifact: PARIPRASHNA_VERIFICATION_MATRIX_v1_0
canonical_id: PARIPRASHNA_VERIFICATION_MATRIX
version: 1.0
status: LIVING — evidence-link column populated as gates close
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18)
date: 2026-08-18
authoritative_side: claude
role: >
  PPR requirement → verification method → required proof rung → gate → evidence link.
  Proof rungs (NFR annex §4): STATIC → REPLAY → INTEGRATION → LIVE → NATIVE ACCEPTANCE;
  a lower rung never substitutes for a higher one. "Evidence" starts empty and is
  filled with dated links (CI run, psql output, screenshot, report §) at gate close —
  an empty cell is an unproven requirement, visibly.
changelog:
  - "1.0 (2026-08-18): first assembly; all evidence cells empty by construction except standing rows."
---

# Paripraśna — Verification Matrix

| PPR | Verification method | Rung required | Gate | Evidence (dated link) |
|---|---|---|---|---|
| PPR-11 | authz fixture suite (cross-chart denial, CHART_REQUIRED fail-closed) + code gate | LIVE | standing | PG2-X4-0002 (2026-07-19); re-prove at G1 |
| PPR-21 | `pg_roles`/grant matrix psql proof; app connects on read role; write-denial probe | LIVE | G1 | — |
| PPR-22 | RLS policy listing + cross-context SELECT denial probe on C1/C3 tables | LIVE | G1 | — |
| PPR-23 | cache-key regression test (F-20 class) | REPLAY | standing | in CI since LCA-17 |
| PPR-12 | HS-1..6 fixture corpus: each hard stop observed blocking/reframing/sealing on the DEPLOYED route; receipt records the action; demonstrated-can-fail | LIVE | G1 | — |
| PPR-13 | injection fixture set (question-borne, retrieved-content-borne, cross-chart exfil attempts) → plan unaffected, output scan fires | INTEGRATION | G1 | — |
| PPR-14 | consent-absent chart → interpretive serving refuses in designed state; minor chart → guardian-only; withdrawal → verified-deletion walkthrough with tombstone check | LIVE | G1 | — |
| PPR-24 | disclosure-class fixtures incl. acharya-redaction and public-fail-closed | INTEGRATION | G1 | — |
| PPR-25 | caps observed to block (rate + per-turn + daily) on both doors; C3-in-prompt canary (arm-4) green | LIVE | G1 | — |
| PPR-26 | INSERT-only grant proof or hash-chain verification on audit tables | LIVE | G1 | — |
| PPR-27 | breach-response note exists; revocation drill (Firebase session + MCP key, same-day) executed once | LIVE | G1 | — |
| PPR-15 | floor-compilation live (existing); completeness receipt reaches AcharyaReadingReceipt | LIVE | G3 | floor live since PB-1 route (STATIC 2026-08-18) |
| PPR-16 | scope-tuple→depth unit tests + visible-depth fixture (3-fact vs 40-fact presentations differ) | REPLAY | G2 | — |
| PPR-17 | grade fixtures: catalog-only never presents confirmed; prior_reading never satisfies floor (existing structural test) | REPLAY | standing | floor_gate test (STATIC) |
| PPR-18 | window-overlap fixture: closed window + domain question → the ask fires, outcome captured in-turn | LIVE | G8 | — |
| PPR-01 | receipt validator on every interpretive turn (schema + §N.8 earned-field audit); quality corpus | INTEGRATION→LIVE | G3 | — |
| PPR-02 | corpus scoring: sets present where triggered; waiver-rate metric wired; falsifier rubric | LIVE | G3 | — |
| PPR-03 | typed-confidence lint (calibrated language only above activation); T-8 precision scan | REPLAY | G3 | — |
| PPR-04 | register-leak corpus (100% seeded-id catch) + remedial-imperative detector + pacing rubric on difficult-topic fixtures | REPLAY→LIVE | G3 | lint live (6 classes) since PB-2 (STATIC) |
| PPR-05 | affordance fixtures: candidates/falsifier reachable, never inline | REPLAY | G3 | — |
| PPR-06 | CLS≈0 above tail; frame-over-frame rect identity; caret-in-tail assertion (existing harness) | REPLAY | standing | PB-1 harness (DOCUMENT_ASSERTED 2026-07-28) |
| PPR-07 | live reading renders table-as-table, verse-as-verse, gap-ribbon — on the DEPLOYED route, no fixture | LIVE | G2 | — |
| PPR-08 | first-paint chip fixture (no transmutation) + server-derived grounding parity vs receipt; hallucinated-id counter observed | INTEGRATION | G2 | — |
| PPR-09 | control audit: every composer control round-trips to an observable behavior change or is absent | LIVE | G2 | — |
| PPR-10 | kill-tests: crash mid-persist → visible incomplete state, outbox replay recovers; semantic-hash parity green on capture corpus; schema-version compatibility test | INTEGRATION | G2 | — |
| PPR-19 | transport-failure fixture set (drop/replay/snapshot/visibility) + G-MOBILE battery + axe 0-critical | REPLAY | G2 | resume suite live (STATIC); mobile/a11y completion pending |
| PPR-20 | provenance completeness check per turn; REPRODUCE drill: rebuild chart, re-render a pre-rebuild sealed reading byte-stable from snapshots | LIVE | G2 | — |
| PPR-28 | immutability triggers proven (UPDATE attempts rejected); dismiss-and-reregister path fixture | INTEGRATION | G9 (seal: standing) | freeze trigger live (mig 470, STATIC) |
| PPR-29 | scoring-method unit suite (taxonomy, coverage stamp, ESS, pooling); activation-gate simulation on synthetic corpora; independent-then-compare fixture | REPLAY→INTEGRATION | G9 | — |
| PPR-31 | arm-1/3 grant proofs (G1); arm-4 canary in CI; dispute-capture round trip (G8) | LIVE | G1/G8 | arm-2 + leak guard mutation-proof 6/6 (DOCUMENT_ASSERTED, C4 2026-08-01) |
| PPR-32 | qualification suite per work class; fallback-substitution fixture: unequal fallback → visible flag + provenance record, never silent | INTEGRATION | G3+ | — |
| PPR-33 | PITR config verified + executed restore-drill log (G1); metrics schema wired + 2-week baseline report (G2); SLO budgets bound (G5) | LIVE | G1/G2/G5 | — |
| PPR-34 | every matrix row names its rung; gate-close review rejects rung substitution | STATIC (meta) | standing | this file |
| PPR-30 | door-parity: same question/chart/build through both doors → normalized receipt-hash equality on the semantic projection | INTEGRATION | G4 | — |
| PPR-35 | per-gate live-evidence checklists (v0.12 §11) discharged in order; W-1 seven-smoke history; W-4 AC-15 rubric cards | LIVE→NATIVE | G0–G9 | NCD-1 ruling (2026-08-18) |
| PPR-36 | doc-set lint at each close: no current-state claim in the Architecture, no normative claim in the Baseline, Register appended before edits | STATIC (meta) | standing | this artifact set |

**AC-15 (the terminal gate, G6):** NATIVE ACCEPTANCE rung — seven daily
rubric cards (friction y/n+where · trust moment y/n+which · register break
y/n · one free line) + the unprompted-symptom-list-empty check; the verdict
itself remains binary, the native's, and non-automatable (ruling W-4).

*End PARIPRASHNA_VERIFICATION_MATRIX v1.0.*

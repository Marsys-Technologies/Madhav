---
artifact: L4_PHALA_CLOSE_v1_0.md
canonical_id: L4_PHALA_CLOSE
version: 1.0
status: CURRENT (closed — 9/9 buildable, registry-reproducible, end-to-end proven)
produced_during: L4-PHALA-SEAL (2026-06-29, native-authorized)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  Definitive sealed record for the L4 Phala (Result / Yield Synthesis) layer.
  Documents the 9 ph_* assets, their tables, migration log, dependency graph,
  contract-compliance results, the deterministic-phala / L5-owns-calibration
  boundary, and the L5 Mīmāṃsā onboarding contract. All CURRENT_STATE references
  to L4 Phala resolve here. Closes the one remaining layer-closure step noted in
  CLAUDE.md §E (v6.1).
supersedes: >
  None retired. The L4 campaign/audit artifacts (L4_PHALA_CAMPAIGN_PLAN_v2_0,
  L4_PHALA_AUDIT_v1_0, L4_PHALA_CODE_AUDIT_REMEDIATION_v1_0,
  L4_PHALA_PROD_RECONCILIATION_v1_0, L4_PHALA_HOLISTIC_REVIEW_v1_0,
  L4_PHALA_DECISIONS_LEDGER_v1_0) remain in place as the verification trail this
  seal rests on; this doc is the closure record that aggregates them.
changelog:
  - v1.0 (2026-06-29, L4-PHALA-SEAL): Initial seal — L4 Phala layer CLOSED.
    9 ph_* assets registered (all per_chart, has_writer=true) with a clean,
    fully-resolvable dependency graph (zero dangling edges). Core migrations
    330–339 + fixes 362/363/366/367. Contract compliance CLEAN across all
    writers (no commit/rollback/close on ctx.db_conn; no cross-layer writes;
    ph_pramana D5 NO-SCORING gate enforced). Verified end-to-end via the
    Abhinandan (1c826d5a) L1→L5 build (L4 9/9) and the GATE A prod
    reconciliation (all L4 inputs satisfied for the native).
---

# L4 Phala Close — Sealed Record v1.0

## §1 — Seal assertion

**L4 Phala (Result / Yield Synthesis) is CLOSED as of 2026-06-29 (native-authorized seal).**

All 9 `ph_*` assets are registered in `asset_registry` with `is_active=true`,
`has_writer=true`, `scope='per_chart'`, and a dependency graph that resolves
end-to-end with **zero dangling edges** (every `depends_on` target is itself an
active, writer-backed asset). All writers conform to the FROZEN orchestrator
contract. The layer was proven buildable end-to-end through the orchestrator's
click-Build path during the Abhinandan (`1c826d5a`) L1→L5 rebuild (L4 = 9/9).

### Verification basis (what "closed" rests on)

| Dimension | Status | Evidence |
|---|---|---|
| Code-complete | ✓ | 9 writers present + registered; contract-clean (§4) |
| Registry-reproducible | ✓ | All 9 `ph_*` rows + `depends_on` edges in migrations (source-controlled); a fresh DB reconstructs the L4 DAG |
| DAG integrity | ✓ | Zero dangling/unbuildable edges (DB-verified) |
| Inputs satisfied | ✓ | `L4_PHALA_PROD_RECONCILIATION_v1_0` GATE A: all `kala_*` / `bodha_*` / `ga_*` inputs present for the native |
| End-to-end build | ✓ | Abhinandan `1c826d5a` L1→L5 (L4 9/9), CURRENT_STATE v6.01 (2026-06-27) |
| Contract compliance | ✓ | No `commit/rollback/close` on `ctx.db_conn`; no `bodha_/kala_/ganita_/chart_` writes; ph_pramana D5 NO-SCORING gate (§4) |

> **Honest caveat (not a defect).** The native chart `482012f1` is currently cold
> (0 rows across all layers) because the database is pre-global-build at seal time —
> this seal is authored immediately before the native global build is triggered.
> Layer closure here asserts *code/registry/contract completeness + proven
> buildability*, exactly as L3's v1.1 seal distinguished code-complete from
> prod-built. The native's live L4 row counts populate when the global build runs;
> they are not invented here.

---

## §2 — Asset manifest (9 ph_* assets)

| asset_id | table(s) | migration | depends_on (key upstream) | notes |
|---|---|---|---|---|
| ph_nimitta | phala_anchors | 330 | ka_sangam, ka_bhavishya_lekha, bo_bimba/samskara/karanajala/sangati/anveshana/cgm_paths/laksana | **L4 root.** Derives anchors from real `kala_convergence` windows (I-16 score) + bodha signals; cites `convergence_id`/`signal_id` in the derivation ledger (B.3) |
| ph_muhurta | phala_muhurta | 331 (+366 edge) | ph_nimitta, ka_kalasutra, ga_panchanga, ka_vighnakara, ga_condition, ka_gochara, ga_positions, ka_sangam | Electional timing windows |
| ph_pratikara | phala_mitigation | 332 | ph_nimitta, bo_upaya, ka_vighnakara, ka_sangam | Mitigation / remedial mapping |
| ph_sodhana | phala_sodhana | 333 | ph_nimitta, bo_laksana | Refinement markers |
| ph_suddha_sodhana | phala_suddha_sodhana | 334 | ph_sodhana, ph_nimitta | Purified refinement |
| ph_rectification | phala_rectification + phala_rectification_best | 335, 336 (+362 count_sql) | ph_nimitta | Birth-time rectification; both tables in EXPLICIT_CLEAR_OPS |
| ph_sankrama | phala_sankrama | 337 (+367 natural-key fix) | ph_nimitta, bo_sangati | Transition / handover synthesis |
| ph_pramana | phala_pramana | 338 | ph_nimitta, ph_sankrama, ph_muhurta, ph_pratikara, ph_sodhana, ph_suddha_sodhana | **D5 NO-SCORING gate** — emits evidence rows but NEVER calibration_score/posterior_probability; L5 owns calibration |
| ph_phaladesa | phala_phaladesa | 339 | ph_nimitta, ph_muhurta, ph_pratikara, ph_suddha_sodhana, ph_sankrama, ph_pramana, bo_laksana | Final result statements (the L4 surface) |

All `count_sql` are chart-scoped (`WHERE chart_id = $1`); `ph_rectification` sums
both rectification tables.

---

## §3 — Migration log

Core L4 tables: **330–339** (330 also DROPs the deprecated `kala_timeline`,
discharging CF.L3.2). Post-close fixes: **362** (ph_rectification count_sql),
**363** (phala_anchors convergence cascade), **366** (ph_muhurta↔ka_sangam edge),
**367** (phala_sankrama natural-key fix). L4 migration ceiling: 339 (core); L5
Mīmāṃsā began at 340+.

---

## §4 — Contract compliance (all ph_* writers)

| Check | Scope | Result |
|---|---|---|
| No `.commit()` / `.rollback()` / `.close()` on `ctx.db_conn` | all `writers/ph_*.py` + `ph_rectification/` | 0 matches (CLEAN) |
| No writes to `bodha_*` / `kala_*` / `ganita_*` / `chart_*` | all ph_* writers | 0 matches (CLEAN) |
| Per-chart delete-then-insert idempotency (N.3) | all ph_* writers | conformant |
| ph_pramana D5 NO-SCORING gate | `ph_pramana.py` | enforced — any scoring attribute on a record is a build-halt event (line 117–122) |

---

## §5 — Deterministic-phala / L5-owns-calibration boundary

L4 Phala produces **deterministic result synthesis** (anchors, timing, mitigation,
result statements) derived from L1–L3 facts via explicit derivation ledgers. It
does **not** assign probabilities or calibration scores — `ph_pramana`'s D5 gate
enforces this structurally. Empirical calibration (ECE/Brier/hit-rate, posterior
probabilities) is **owned exclusively by L5 Mīmāṃsā**, which scores L4 outputs
against observed outcomes as the prediction→outcome loop accumulates history.
This is the same epistemic separation that makes L5 "structural mode": L4 is
correct-and-final on day one; the probabilistic overlay matures over time in L5.

---

## §6 — Open carry-forwards (none block closure)

| ID | Item | Disposition |
|---|---|---|
| CF.L4.1 | Native `482012f1` live L4 row counts | Populate on the imminent global build; not a closure blocker (see §1 caveat) |
| CF.L4.2 | L5 calibration of L4 predictions | By design — owned by L5 Mīmāṃsā; matures with outcome data (life_events) |
| CF.L4.3 | M9 multi-school consensus half of `ph_nimitta` Axis 6 | Populates after M9 activation (per L4_PHALA_PROD_RECONCILIATION); L4 layer itself is complete |

---

## §7 — L5 Mīmāṃsā onboarding (already sealed)

L5 Mīmāṃsā (`mi_*`) is already SEALED (`L5_SEAL_AND_SHIP_REPORT_v1_0.md`,
structural mode). It consumes L4 `phala_*` (read-only) and inherits all standards:
frozen `@register`/`WriterBase` contract, per-chart delete-then-insert idempotency,
`mi_*` ids, no cross-layer writes. The L4→L5 interface is the deterministic
`phala_pramana` / `phala_phaladesa` evidence that L5's `mi_pramana` scores against
recorded outcomes.

---
*End of L4_PHALA_CLOSE v1.0. L4 Phala is the fifth and final build layer to close (L0✓ L1✓ L2✓ L3✓ L4✓ L5✓). The build arc is complete.*

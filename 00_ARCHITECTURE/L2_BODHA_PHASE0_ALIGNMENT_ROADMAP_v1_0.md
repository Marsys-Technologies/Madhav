---
artifact: L2_BODHA_PHASE0_ALIGNMENT_ROADMAP_v1_0.md
canonical_id: L2_BODHA_PHASE0_ALIGNMENT_ROADMAP
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-12
authored_for: the L2 Bodha campaign — the complete pre-brief alignment runway
purpose: >
  The complete, ordered action set to get from "decisions locked" to "ready to author the first
  WRITER brief (bo_laksana)." Every Phase-0 prerequisite as a phase, with who-does-it and what-it-
  produces. This is the durable checklist the campaign works against — so the sequence lives on
  disk, not in a chat message.
read_in_combination_with:
  - 00_ARCHITECTURE/L2_BODHA_PHASE0_GAP_REPORT_v1_0.md (v1.1 — the audit this sequences the fixes for)
  - 00_ARCHITECTURE/L2_BODHA_BUILD_CAMPAIGN_v1_0.md (§0.0 decisions, §13.1 extensions, §4 build order)
decisions_basis: all six §0.0 campaign decisions RESOLVED 2026-06-12
split_reminder: >
  Cowork PLANS (authors briefs, amends specs, updates registries-on-paper). Antigravity EXECUTES
  (runs migrations, writes writer code, touches prod). The data-plane is always prod via the Cloud
  SQL proxy (feedback-localhost-codeplane-prod-dataplane). All ALIGNMENT is complete before the
  first WRITER brief is drafted.
---

# L2 Bodha — Phase-0 Alignment Roadmap v1.0

## §0 — The runway, at a glance

Seven phases (A–G) take us from "decisions locked" → "cleared to author `bo_laksana`." Phases A–E
are authored by Cowork + executed by Antigravity; F is operator-run; G is a Cowork audit. The hard
ordering constraints: **A gates B** (the reconciliation migration creates the §13.1 tables, so
their schemas must be locked first); **B + C gate E** (seed re-pointing needs the tables + registry
to exist); **G gates the writer briefs** (verify prod, not worktree). C, D, F run in parallel.

```
A (spec amends) ─→ B (P0.1 reconcile) ─┐
C (G52 registry) ──────────────────────┤
D (helper+formulas) ────────────────────┼─→ E (seed repoint) ─→ G (verify) ─→ [bo_laksana brief]
F (Phase-5 E2E, parallel) ──────────────┘        (build-time gate, must be green before build RUNS)
```

---

## §1 — The phases

- **Phase A — A10–A14 spec amendments** *(Cowork authors → native signs off)*
  Amend the LOCKED specs for the §13.1 philosophy extensions: add `bodha_convergence`,
  `bodha_contradictions`, `bodha_cgm_paths` tables + `convergence_formula_v1` /
  `centrality_formula_v1`. Version-bump each touched spec (B.8). **Standalone + first** — P0.1's
  `CREATE TABLE`s depend on these final schemas. *Produces:* amended A11/A12 (+ A10 if contradictions
  land there) at a new version, native-signed.

- **Phase B — P0.1 table reconciliation brief** *(Cowork authors → Antigravity executes)*
  Repoint-not-drop, prod-gated, table-by-table. Order inside the brief: (1) repoint
  `consult/route.ts:22` off `bodha_signals` → the spec table or a compat view; (2) prod-verify gate
  V1 (live tables/counts) + V2 (native data?) + per-table V3 (reverse-citation grep); (3) DROP only
  verified-safe legacy `bodha_*` + `l25_*`; (4) CREATE the ~17 spec-grade `bodha_*` tables + 8 MVs
  (A10×3, A11×5). Surgical migrations, one at a time, file-vs-live verified, tracker rows. *Produces:*
  the reconciliation brief + (on execution) the canonical `bodha_*` tables live in prod.

- **Phase C — G52 `signal_type_registry` brief** *(Cowork authors → Antigravity executes)*
  The layer-gating prereq. The global registry table (A10 §5) + the ~500–700 data-driven predicate
  seed across all 6 traditions + synthetics + its writer + `asset_registry` row. `bo_laksana` cannot
  run without it. Independent of B — author in parallel. *Produces:* the registry brief + (on
  execution) the seeded `signal_type_registry`. **The biggest Phase-0 task** (the predicate seed may
  warrant its own sub-brief).

- **Phase D — Foundations brief: idempotency helper + versioned formulas** *(Cowork authors → Antigravity executes)*
  `bodha_writers/_idempotency.py` mirroring `ga_writers/_idempotency.py` (per-chart replace-scoped
  delete-then-insert) + the four pure, unit-tested formula functions (`salience_formula_v1`,
  `resonance_score_v1`, `convergence_formula_v1`, `centrality_formula_v1`). Small, parallel-safe.
  *Produces:* the foundations brief + (on execution) the helper + tested formula module.

- **Phase E — P0.3 seed reconciliation brief** *(Cowork authors → Antigravity executes)*
  Re-point the 8 `bo_` registry rows' `target_table`/`count_sql`/`size_sql` to their real spec
  tables; fix `bo_laksana.depends_on` to add `ga_structural` + `signal_type_registry`; keep rows
  DRAFT until their writers exist. **Depends on B (tables) + C (registry).** **The exact target map
  is LOCKED in `L2_BODHA_BUILD_CAMPAIGN_v1_0.md §14`** (asset → full table set → primary →
  summed `count_sql` → corrected `depends_on`) — Phase E is pure transcription of §14. *Produces:*
  the seed brief + (on execution) the registry rows pointing at real tables with summed count_sql.

- **Phase F — Phase-5 E2E gate** *(operator/native runs; Cowork can author the runbook)*
  Prove the orchestrator builds a non-native chart end-to-end (`ORCHESTRATOR_CONVERGENCE_CLOSE §4`
  runbook). **Build-time gate:** green before the Bodha build RUNS, but does NOT block brief-authoring
  — runs in parallel with A–E. *Produces:* a green E2E proof (or the runbook to get there).

- **Phase G — Alignment verification** *(Cowork audits)*
  Short readiness re-check that A–E actually landed in PROD (not worktree): re-run V1/V5/V6, confirm
  the spec tables + 8 registry rows + G52 exist, confirm `consult` repointed + green, confirm the
  formula module + helper imported. Guards against the worktree-complete-only trap
  (`[[feedback-ac-must-verify-target-environment]]`). **Green here = cleared to author writer briefs.**
  *Produces:* a one-page readiness sign-off.

---

## §2 — After alignment: the writer briefs (out of scope for this roadmap — listed for orientation)

Per campaign §9: **Batch 1** `bo_laksana` (MSR root) → **Batch 2** fan-out (`bo_sangati` w/
convergence+contradiction first-class · `bo_bimba`+`bo_karanajala` CGM built DEEPEST · `bo_samskara`
· `bo_samvada` UCD-Option-A) → **Batch 3** `bo_upaya` (RM) + `bo_pramana_mapa`. Each batch closes
(built + cockpit-verified) before the next opens.

---

## §3 — Status tracker (update as each phase lands)

| Phase | Owner | Status | Artifact / evidence |
|---|---|---|---|
| A — spec amendments | Cowork→native | NOT STARTED | (A11/A12 amended versions) |
| B — P0.1 reconciliation | Cowork→Antigravity | NOT STARTED | (brief + migrations) |
| C — G52 registry | Cowork→Antigravity | NOT STARTED | (brief + seed) |
| D — helper + formulas | Cowork→Antigravity | NOT STARTED | (brief + module) |
| E — seed repoint | Cowork→Antigravity | NOT STARTED | (brief + registry rows) |
| F — Phase-5 E2E | operator | NOT STARTED | (E2E proof) |
| G — alignment verify | Cowork | NOT STARTED | (readiness sign-off) |

---

*End of L2_BODHA_PHASE0_ALIGNMENT_ROADMAP_v1_0. Seven phases from decisions-locked to
writer-brief-ready; A is standalone-and-first (gates B); G verifies prod before any writer brief.
Next action: author the Phase A spec amendments.*

---
artifact: L5_MIMAMSA_CAMPAIGN_PLAN_v1_0.md
canonical_id: L5_MIMAMSA_CAMPAIGN_PLAN
version: 1.0
status: DRAFT — campaign arc + per-asset specs for L5 Mīmāṃsā (vision-level; ground-truth-reconciled later)
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  Translates L5_MIMAMSA_VISION_v1_0 into an executable campaign arc + per-asset specifications for the
  6 mi_* assets, with the dependency correction applied. Vision/design level — NOT yet reconciled
  against ground-truth code (that happens in the deferred L5_MIMAMSA_GROUND_AUDIT). The per-asset
  schemas here are PROPOSED contracts to be confirmed against the live registry + ph_pramana column
  shape, then native-ratified.
depends_on_artifacts:
  - L5_MIMAMSA_VISION_v1_0.md (the charter)
  - L5_MIMAMSA_ONBOARDING_HANDOFF_v1_0.md (the entry point)
  - L4_PHALA_DECISIONS_LEDGER_v1_0.md D45 (the ph_pramana seam)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (the frozen WriterBase contract)
---

# L5 Mīmāṃsā — Campaign Plan & Per-Asset Specs

> Companion to `L5_MIMAMSA_VISION_v1_0.md`. The vision says *what* and *why*; this says *in what order*
> and *with what shape*. Both precede the ground-truth audit; treat schemas as proposals.

---

## §1 — Campaign arc (mirrors the proven L3/L4 pattern)

L3 and L4 both succeeded with the same shape, and both proved that "engines exist, just wire" is a
trap. L5 inherits the shape AND the skepticism.

| Phase | Name | Output | Gate |
|---|---|---|---|
| **P0** | **Prod-truth reconciliation** | Which `mimamsa_*` tables exist in prod, which are empty, what the legacy code actually does. Live-registry probe of the 6 `mi_*` rows. | Cannot proceed on assumptions; must match live DB |
| **P1** | **Ground-truth audit** | `L5_MIMAMSA_GROUND_AUDIT_v1_0.md` — per-file verdict (reference/reuse/rewrite) for ~12 legacy files + 5 migrations + tests vs frozen contract | Deferred until L4 closes (needs sealed `phala_pramana` contract) |
| **P2** | **Holistic design** | Settle V1–V7 (vision §10); finalize the calibration method, held-out/leakage strategy, reverse-channel design, metric set | Native ratification of V1–V7 |
| **P3** | **Per-asset specs** | This document's §3, hardened against ground truth + the sealed `ph_pramana` contract | Native sign-off on the corrected DAG |
| **P4** | **Wire to frozen contract** | 6 `@register('mi_*')` `WriterBase` writers; migrations (next free number after L4's 341 — confirm at open); idempotency; count_sql `$1` | Auto-discovery imports clean; pkgutil hard-fails on any import error |
| **P5** | **Retrieval + Whole-Chart-Read** | `L5_mimamsa` retrieval lit; calibration view added to B.11 | Retrieval registry green |
| **P6** | **Clean seal** | `L5_MIMAMSA_CLOSE_v1_0.md`; **live-deployment guard** asserts `mimamsa == N lit` against running prod API; red-team (IS.8(b) macro-close cadence) | Seal against LIVE cockpit, never branch |

**Execution model:** per native precedent (L4 D47), L5 can run fully autonomous via the Conductor + the
agentic swarm in an isolated worktree (`MadhavL5Mimamsa`), one kickoff, env self-provisioning (Sthāpati
Phase 0), maximal parallelism where file-disjoint. The reverse-channel write-back and any chart-mutation
stay native-gated (B.10).

---

## §2 — The corrected DAG (proposal for native ratification)

```
                         L4 (sealed, read-only)            L1 (held-out)
              phala_pramana ─ phala_anchors ─ phala_phaladesa     life_events
                    │              │               │                  │
                    └──────────────┴───────────────┘                  │
                                   ▼                                   ▼
                            mi_bhavisya  ◄──(prediction registry)   mi_jivanaghatana
                                   │                                   │
                                   └─────────────┬─────────────────────┘
                                                 ▼
                                           mi_pramana  (calibration engine)
                                                 │
                                                 ▼
                                          mi_gunanaka  (learned weights + REVERSE CHANNEL → L4/L2)
                                                 │
                          ┌──────────────────────┼───────────────────────┐
                          ▼                                               ▼
                    mi_pariksha (self-exam / miss-attribution)      mi_vistara (export ledger)
```

**Change vs the seed `depends_on`:** add `phala_pramana` (+ `phala_anchors`, `phala_phaladesa`) as
upstream of `mi_bhavisya`; keep the internal mi_* chain. The seed's `bo_laksana` / `ka_kalasutra`
dependency on `mi_bhavisya` is preserved only if the audit confirms a real read; otherwise dropped.
**This is a DRAFT correction — confirm against the live registry before applying (handoff §2).**

---

## §3 — Per-asset specifications

> Each spec is a PROPOSAL. Columns marked `[confirm]` must be reconciled against the sealed
> `phala_pramana` contract + the live registry during P1/P3. All writers obey the frozen contract
> (`§4`). Scoring is deterministic Python; no generative LLM computes a number.

### 3.1 — `mi_jivanaghatana` (Jīvanaghaṭanā — Clean-evidence vault)
- **Table:** `life_events` (shared, global) + a held-out/provenance view.
- **Role:** Ground truth. Loads the LEL, tags every event with provenance: `shaped_a_predictor`
  (bool), `disclosure_timing` (pre/post-framework), `held_out` (bool), `admissible_clean` (derived).
- **Supreme add:** the **leakage firewall** lives here — only `admissible_clean` events feed the
  headline calibration; the rest are scored separately and labeled.
- **Idempotency:** count must match the LEL file exactly (divergence = bug, per seed `volume_explanation`).
- **count_sql:** `SELECT count(*) FROM life_events` (global; no `$1`).

### 3.2 — `mi_bhavisya` (Bhaviṣya — Prediction registry)
- **Table:** `mimamsa_predictions` (per_chart).
- **Role:** Mirror every L4 falsifiable prediction (from `phala_pramana`) into a scorable ledger row:
  the canonical falsifier `{metric, comparison, threshold, observation_window, data_source}` `[confirm
  exact columns from ph_pramana.py ~120–190]`, `eval_date`, lifecycle `pending/due/confirmed/denied/
  partial`, source `phala_pramana` id, domain tag, confidence tier.
- **Supreme add:** time-indexed lifecycle + due-detection (eval_date past + candidate LEL evidence
  present) — picking up exactly at ph_pramana's PR3 staged boundary.
- **depends_on (corrected):** `['phala_pramana', 'phala_anchors', 'phala_phaladesa']` `[ratify]`.
- **L-is-authority:** stores the `phala_pramana` row id; inherits, never restates, its values.
- **count_sql:** `SELECT count(*) FROM mimamsa_predictions WHERE chart_id = $1`.

### 3.3 — `mi_pramana` (Pramāṇa — Calibration engine)
- **Table:** `mimamsa_calibration`.
- **Role:** For each due prediction, match to admissible LEL evidence and compute the verdict +
  calibration record. Then aggregate into **reliability curves** (predicted-prob vs observed-rate) per
  domain / signal-family / confidence-tier, with **bootstrapped CIs**, **Brier**, **log-loss**, **ECE**,
  **hit-rate-by-tier**, and **n** stapled to every row.
- **Supreme add:** the **held-out validity gate** (does the held-out partition pass within declared
  tolerance?) + **minimum-n gate** (below n, report "insufficient evidence," not a number) + partial
  pooling toward a global rate for thin domains.
- **Determinism:** re-running yields byte-identical verdicts (reproducibility is a seal criterion).
- **depends_on:** `['mi_bhavisya', 'mi_jivanaghatana']` `[corrected — add the evidence source]`.
- **Boundary:** consumes the L4 outcome hook that L4 was FORBIDDEN (D5) to fill. This is the line.

### 3.4 — `mi_gunanaka` (Guṇānaka — Learned-weight register + reverse channel)
- **Table:** `mimamsa_multipliers`.
- **Role:** Shadow-mode home of the LL modulators (start with LL.1 signal weights; LL.8 Bayesian
  posteriors; structure for LL.2–LL.7). Each weight: value, n-observations, promotion-status
  (`shadow/promoted/suspended`), kill-switch state, version, audit trail.
- **Supreme add — THE REVERSE CHANNEL (Pillar 4):** the staged write-back that flows learned priors
  DOWN to damp/boost `ph_nimitta` confidences (the D45 PR4 return path), re-weight `bodha_msr_signals`,
  adjust CGM edges. **v1 = stage-only (shadow); promotion to live write-back is a native gate** (V4).
- **Discipline:** every update obeys LL rules #1–#6 (modulate-never-overwrite; ≥N obs; reversible).
- **depends_on:** `['mi_pramana']`.

### 3.5 — `mi_pariksha` (Parīkṣā — Self-examination)
- **Table:** `mimamsa_qa_eval`.
- **Role:** The epistemic-hygiene surface. v1: **LL.9 miss-attribution** — for each miss, the forensic
  trace (which signals should have fired, which did/didn't, why it failed). Ceiling: synthesis-answer
  QA + LL.4 prompt scoring (V6).
- **Supreme add:** miss attribution feeds back into `mi_gunanaka` (LL.9 → LL.1/LL.8), closing the
  learn-from-misses loop.
- **depends_on:** `[]` v1 (reads misses from `mi_pramana`); `[ratify]`.

### 3.6 — `mi_vistara` (Vistāra — Export-integrity ledger)
- **Table:** `mimamsa_export_log`.
- **Role:** Audit log of every export event (PDF/JSON/MCP bundle) — what left the instrument, when,
  to whom, with which calibration disclosures attached. The traceability boundary.
- **depends_on:** `[]`.

---

## §4 — Frozen-contract conformance checklist (every mi_* writer)

Inherited without exception from `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2`. The handoff §3 lists the
exact traps L3/L4 hit:

- [ ] `@register('mi_<asset>')` `WriterBase` subclass in `pipeline/orchestrator/writers/`.
- [ ] `run(ctx) -> WriterResult` (light) OR `plan_substeps` + `run_substep` (heavy).
- [ ] `conn = ctx.db_conn`; **never commit or close it** (orchestrator owns txn + per-substep savepoint).
- [ ] **never writes `asset_throughput`** (orchestrator is sole build-state writer).
- [ ] returns `WriterResult(asset_id=..., rows_inserted=...)` — kwarg is **`rows_inserted`** (L3 BUG-3).
- [ ] `chart_id` + `birth_params` from `ctx.config`.
- [ ] idempotency: per-chart **delete-then-insert** scoped to `(chart_id × natural key)` (mirror
      `ga_writers/_idempotency.py`); global assets use the global pattern.
- [ ] **count_sql uses `$1`** (never `$$CHART_ID$$` — L3 BUG-1); stats route reads `count_sql`.
- [ ] any new top-level service dir **COPY'd in `Dockerfile.pipeline`** (the silent-hang gotcha).
- [ ] every `mi_*` writer **imports clean** (pkgutil auto-discovery hard-fails on any import error).
- [ ] **Contract change needed? → STOP, raise with native.** The freeze is deliberate.

---

## §5 — Migrations & infra

- **Migration numbering:** next free number after L4's last (L4 used 330–341; **confirm prod max at
  open** — the two-dir lexical-merge collision means check BOTH `platform/migrations/` and
  `platform/supabase/migrations/`, per L4 D14).
- **Localhost = code plane; data plane = prod** via Cloud SQL proxy (port 5433). Applying a migration
  on localhost IS a prod schema change.
- **Push to main auto-migrates + deploys prod** (`deploy.yml` runs `migrate.ts` against
  `PROD_DATABASE_URL`). `PROD_DATABASE_URL` secret must stay set (the L4 P6 blocker).
- **Seal against the LIVE deployed cockpit** (`SESSION_CLOSE_TEMPLATE §7.9`) — `mimamsa == N lit` on the
  running prod API, never the branch. The #1 lesson from L3 + L4.
- **Local dev:** `next dev --webpack` (Turbopack 16.2.4 CPU-thrash bug).

---

## §6 — Seal criteria (what "L5 done" means)

1. All 6 `mi_*` assets **lit on the LIVE prod cockpit** (`/api/cockpit/stats?chart_id=482012f1`), each
   with correct chart-scoped `count_sql`.
2. `mi_pramana` produces **reproducible** verdicts (re-run = identical) with n + leakage-status on every
   calibration row.
3. The **leakage firewall** is enforced: headline scores use only `admissible_clean` events; held-out
   partition passes the validity gate within declared tolerance (or honestly reports "insufficient n").
4. The **reverse channel** exists and is exercised in shadow (staged write-backs visible, promotion
   native-gated).
5. **No fabricated numbers** — any unfillable score is `[EXTERNAL_COMPUTATION_REQUIRED]`, not invented.
6. `L5_MIMAMSA_CLOSE_v1_0.md` written with **live-prod endpoint JSON evidence** + IS.8(b) red-team
   discharged + `CURRENT_STATE` flipped (and a note that L4's missing seal was resolved upstream).

---

*End of L5_MIMAMSA_CAMPAIGN_PLAN v1.0. Six phases (prod-truth → audit → holistic → specs → wire → seal),
six assets re-pointed at phala_*, the frozen contract checklist, and seal-against-live-prod discipline.
Schemas are proposals pending the ground-truth audit + the sealed ph_pramana contract.*

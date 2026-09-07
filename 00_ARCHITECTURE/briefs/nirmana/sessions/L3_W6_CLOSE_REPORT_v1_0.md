---
artifact: L3_W6_CLOSE_REPORT_v1_0.md
canonical_id: NIRMANA_V21_L3_W6_CLOSE_REPORT
version: "1.0-DRAFT"
status: SCAFFOLD — W6 has not run; 2 of 23 assets have genuinely completed W4 (real
  `asset_frozen` events); this is C8.5 productive-wait prep, not a submitted capsule.
  Sections below are filled from W1–W3's actual, verified work plus the two real freezes;
  the remaining W4/W5/W6 sections are placeholders pending the E-gate (most assets), the
  super-admin evidence-write wall (6 assets), and the F-L3-12/#1793 cascade disposition
  (the whole MSR-descended spine).
produced_on: 2026-09-07 (drafted mid-campaign; will be finalized and re-dated at actual W6)
owner: L3 session (this file is mine alone — charter C5; not Conductor-owned)
---

# L3 — Kāla — W6 Close Report (DRAFT SCAFFOLD)

Per `NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md` §4: *"the close report is the whole W6 ceremony."*
Drafted ahead of the full W4/W5 waves per C8.5 guidance, so the ceremony lands within hours of
its last precondition clearing, not days. Everything below reflects **verified, shipped** work
as of this draft; nothing is asserted ahead of evidence. Live state remains authoritative in
`L3_STATE.md` — on any disagreement, that file wins and this scaffold is the stale one.

## 1. Assets and routes taken (23 assets, W1 23/23 · W2 23/23)

Frozen definition `t0-2026-09-01-0e5b06fb` (23/23 L3 assets; live `asset_registry` count
matches — no manifest/registry drift). Routes from `L3_W2_DECIDE_v1_0.md`:

| route | n | assets |
|---|---|---|
| `changed` | 11 | ka_gochara, ka_gochara_v3_century_materialize, ka_avadhi, ka_yojaka, ka_kshetra, ka_sangam, ka_vighnakara, ka_taranga, ka_kala_darshana, ka_bhavishya_lekha, ka_jivana_parva |
| `rebuild_only` | 6 | ka_gochara_resonance (canary candidate), ka_kota_chakra, ka_moorti_nirnaya, ka_sudarshana_varsha, ka_vedha_gochara, ka_kalasutra |
| `probe` (service) | 4 | ka_graha_sancara **[FROZEN]**, ka_muhurta_seva **[FROZEN]**, ka_dasha_kala, ka_tulana |
| `verified_reuse` | 1 | ka_tithi_pravesha (L4 consumer, D-7) |
| `retired_with_disposition` | 1 | ka_gochara_sweep (v1 archive — HARD-FLOOR PROTECTED; in-database loss detector installed, migration 670) |

Two monsters need solo run slots at W4: `ka_gochara_v3_century_materialize` and `ka_kshetra`
(11.0M rows / 5.0 GB; measured 22,685 s native). Spine ordering constraint (C13 +
Conductor-ruled): `bo_laksana` freezes → `ka_yojaka` → `ka_kalasutra` → `ka_sangam` (only after
L4 confirms `phala_anchors` regenerability) → rest of the spine; `ka_kshetra` independent.

## 2. W4 EXECUTE — the two real freezes (the only W4 work possible so far)

| asset | frozen | chain | process note |
|---|---|---|---|
| `ka_graha_sancara` | 2026-09-06T15:56:00Z | probe_accepted (live probe GREEN, 9/9 grahas) → integrity_verified (independent re-probe) → asset_frozen; all events server-reconstructed | **Durable annotation (D-CND-35/#2124):** original submission ran implementer+verifier in one context; independently re-verified post-hoc by a context-free subagent, 5/5 adversarial checks PASS. The layer's first genuine, non-artefactual freeze. |
| `ka_muhurta_seva` | 2026-09-06T21:10:00Z | same 3-event chain, executed by a genuinely fresh subagent from the start (no remediation needed) | First freeze done correctly per D-CND-35 end-to-end; independently re-verified via direct DB query. |

**Everything else is gated, with the gates verified rather than assumed:** 6 assets
`BLOCKED-NO-ROUTE` purely on the super-admin evidence-write wall (`requireSuperAdmin()` on
`POST /api/admin/nirmana-elevation/evidence`; payloads fully pre-computed and verified, see
`L3_STATE.md` held-items); `ka_dasha_kala` `BLOCKED-ANCESTORS` (correctly — its DB-free proxy
probe does not license bypassing C2, per the #1960 precedent); the MSR-descended spine
additionally held by L3's own unconditional commitment not to dispatch until F-L3-12/#1793 are
ruled (see §5).

## 3. W3 IMPLEMENT — what shipped (all merged, each mutation-proved)

Consolidated from `L3_STATE.md`; the M-series table, N-series work, and findings ledger there
are the itemized record. Highlights that a W6 reviewer must know:

- **19 D-CND-03 chart-partitioned integrity contracts** (migration 670, PR #1792): installed,
  executed live, mutation-proved; 19 achieved-count floors; 3 derived volume formulas. **Five
  contracts shipped RED as true positives** (F-L3-14) — four localize to cascade-damaged chart
  `cb73cd3d` (#1793). Installing green-washed contracts was explicitly declined (hard floor).
- **The N1 Temporal Concordance chain — LANDED in full** (#1890/#1894/#1919/#1921/#1924/#2047/
  #2049): unified `EngineTestimony` vocabulary, authority profiles as stored data
  (`kala_paddhati_profile.arbitration_role`/`precedence` + serving surface), and
  `composeConcordanceVerdict` wired into `kala_explain_get`. The layer's headline mandate.
- **F-L3-15: all 4 service-asset health probes** (#1846, migrations 676/810, #2079): 3 real
  probes + `ka_dasha_kala`'s DB-free PROXY probe (D-CND-34).
- **M-series serving/writer honesty fixes** (PR #1751 + successors): M3 (dict_row/KeyError +
  FORENSIC anchor misuse), M4 (`lord_condition_fact_refs` empty on 100% of rows — fixed through
  the L0 SSoT), M5 (per-chart century grid — the native's grid was serving every chart), M7
  (honest-empty pagination), M8 (false "no rows" claim over 31,350 live rows), M9 (`or 0.5`
  rewriting 793 computed zeros), M11 (discarded health verdicts now raise).
- **F-KALA-1 ranking chain** (4 call sites): `dasha_activation_proximity_score` promoted to
  primary sort key everywhere (`judgment_query`, `query_temporal_activation`, `ahead.ts` ×2) —
  orb_strength is 99.63% NULL and was silently deciding cut points by id-order.
- **F-L3-4 CLOSED**: all 20 originally-NULL L3 assets carry a derived, auditable
  `expected_volume_formula` (16 migrations, 852–867), each with paired live tests.
- **M12/F-CENT-2 disposition** (migration 672): 54 unreachable-debris rows deleted with full
  provenance analysis; regression-guarded by the W5 checks file (§4).
- **P7 outcome seam**: `kala_bhavishya.outcome_recorded`/`outcome_notes` preserve-on-rebuild
  landed; the seam is disclosure-checked in the W5 file (C4b).
- **Honest-null work** (N4a/N4b/N12 etc.): two 100%-zero `ka_sangam` terms → honest null (c7's
  deeper fix HELD on the Aries-lagna frame question, #1810); sub-range sentinel inventions
  removed.

## 4. W5 VERIFY — instruments pre-staged (this is C8.5 prep, run before any capsule)

- **Cross-asset scripted half:** `l3_scripts/l3_w5_mechanical_checks.sql` — 12 read-only gates
  + 4 disclosures, every check grounded in a recorded finding. **First live run 2026-09-07:
  10/12 PASS, 2 honest reds**, both real corruption: C2 (#1793's damage signature on
  `cb73cd3d`) and C1a — a NEW true positive found by the file's first run (**F-L3-16**: 49,775
  `kala_activation_predicates` rows ALREADY dangling against `bodha_msr_signals`; 45 on the
  canonical chart, all CLASSIFY_RESIDUAL bound 2026-08-12; `kala_activation` −360 and
  `kala_obstruction` −3 vs F-L3-12's baselines — the predicted cascade has already fired).
- **Per-asset half:** the 19 D-CND-03 contracts on `asset_registry` (each with a mutation
  proof + volume derivation + live evidence file staged in `~/nirmana-s/.l3-tools/contracts/`).
- **W5 cycle plan:** after each W4 rebuild, re-run both halves fresh-context (implementer ≠
  certifier, D-CND-35); the two expected-red cross-asset gates (C1a, C2) must go green on a
  post-disposition rebuild before any capsule cites them.

## 5. Blockers a W6 ceremony cannot proceed past (as of this draft)

1. **F-L3-12 / F-L3-16 / #1793 — the cascade disposition.** Five `ON DELETE CASCADE` FKs from
   `bodha_msr_signals` into L3 + the FK-less predicate table. L3's standing position: L2
   rebuilds first; the MSR-descended spine regenerates after; chart `cb73cd3d` needs a formal
   peer-or-not ruling (#1793) because floors, volume formulas and contracts all depend on it.
2. **Super-admin evidence-write wall** — 6 assets' W2-acceptance events fully pre-computed but
   unsubmittable without an authenticated super-admin actor; outside this session's authority
   by design.
3. **E-gate ancestor closure** — the bulk of the layer waits on L1/L2 freezes (verified via
   `egate.sql` each cycle, not assumed).
4. **Freeze predecessor (C2):** L2 Bodha must be frozen before L3's W6 ceremony.
5. **Sidecar deploy pinning** (held-items row 1): Cloud Run traffic pinned to a stale revision —
   external deploy-pipeline blocker, verified repeatedly, not an L3 code problem.

## 6. Backlog handed forward

1. **N2 score commensurability** — strict precondition for the concordance verdict comparing
   four scales honestly; the "temporal-confidence multiplier" capability is HELD on L2's
   consensus/salience capabilities (C6) — not L3's to unblock.
2. **D-TIME item 1** (per-engine question declarations in the registry) — planned, unclaimed.
3. **F-L3-11 epoch anomalies** — two documented JD-convention disagreements, DELIBERATELY not
   fixed inside an unrelated change (each moves every window in the century); recorded at the
   constant itself, awaiting a dedicated ruling.
4. **F-L3-13 doctrine** (E-gate has no inverse-dependency reasoning) — offered to the register.
5. **ka_taranga derived-view vs witness decision** — owed from W2, with falsifiers already
   staged.
6. **MSR re-run sequencing** (`ka_yojaka`→`ka_kalasutra`→`ka_sangam`→spine, after L2) — priced:
   ≈46 min/chart excluding `ka_kshetra`; ≈7 h with it. The registry's ~9-minute estimate is
   wrong; do not schedule from it.
7. **`kala_convergence`/`kala_bhavishya` bigserial identity churn** — the D-CND-04 class L4
   already fixed for its anchors, handed to L3 by L4's close report; not yet picked up.

## 7. Cost actuals (measured, not forecast)

See `L3_STATE.md` "Cost ledger" (per-asset wall-clock lands there as W4 runs). Measured so far:
W1 fan-out 23/23 + W2 DECIDE 23/23 within the first two days; W3 spanned 40+ merged PRs across
serving honesty, contracts, N1, health probes and volume formulas (the state file's heartbeat
is the authoritative PR-by-PR record); the two service freezes cost ~1 cycle each including
independent re-verification. Rebuild pricing for the W4 wave is in §6 item 6.

---

*This scaffold will be revised in place (not superseded) as W4/W5/W6 actually run — per
`ONGOING_HYGIENE_POLICIES_v1_0.md`'s archival-retain-in-place discipline, the version number
advances (1.0-DRAFT → 1.0) rather than a new file being created.*

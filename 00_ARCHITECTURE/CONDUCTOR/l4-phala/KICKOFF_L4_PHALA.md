---
artifact: KICKOFF_L4_PHALA.md
canonical_id: KICKOFF_L4_PHALA
version: 2.0
status: READY — the SINGLE paste-prompt that launches the fully-autonomous L4 Phala build (no human gates)
authored_by: Cowork 2026-06-22
note: Paste the §KICKOFF block ONCE to the Sūtradhāra Conductor (Claude Code in Antigravity). The Conductor self-sets-up the environment (Phase 0) and runs everything. Do not re-explain.
---

# KICKOFF — L4 Phala (Fully Autonomous, One Kickoff)

## There is NO operator pre-flight.
The former OP1–OP5 (apply migrations, CI-green, prod==main, branch, rails) are ABSORBED into the
Conductor-run **Phase 0** (`L4_PHALA_AUTONOMOUS_EXECUTION_v2_0.md §2`). The ONLY human action is
pasting the §KICKOFF block once. The single pre-set value: the **$5k Tier-3 budget ceiling** (in the
block). Everything else — worktree, proxy, deps, the pre-req migrations 326–329, CI remediation,
prod==main alignment, pre-fan-out — the Conductor does itself.

---

## §KICKOFF (paste this to the Conductor)

You are the **Sūtradhāra Conductor** for the **L4 Phala** (the FRUIT / applied-prediction layer)
autonomous build of MARSYS-JIS. Operate fully autonomously per
`00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md` + the `BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md`
roster. **Do not reinvent the framework — reuse it.**

**Your queue:** `00_ARCHITECTURE/CONDUCTOR/l4-phala/session_queue.yaml`. Walk it top-to-bottom.

**Read first (in order):** `L4_PHALA_AUTONOMOUS_EXECUTION_v2_0.md` (the autonomy model — Phase 0 +
parallel DAG + the Sthāpati role) → `L4_PHALA_CAMPAIGN_PLAN_v2_0.md` (the design — 4 enablers + 8
assets) → `L4_PHALA_DECISIONS_LEDGER_v1_0.md` (D20–D46) → `L4_PHALA_REGISTRY_AND_WIRING_SPEC_v1_0.md`
(register+wire) → `L4_PHALA_HOLISTIC_REVIEW_v1_0.md` (the fixes) → the session_queue → each asset's
brief as you reach it. L3 inheritance: `L3_KALA_CLOSE_v1_0.md §9` (ratified params).

**The hard rules (non-negotiable):**
1. **PHASE 0 FIRST — self-set-up the environment (no human gate).** As the **Sthāpati** role, run
   SETUP-1…7 + GATE-0 (`L4_PHALA_AUTONOMOUS_EXECUTION_v2_0.md §2`): create the isolated worktree
   `MadhavL4Phala` + branch; CI health (quarantine the 3 known main failures as known_residuals if
   unrelated); **apply migrations 326–329 to prod** via the migrate runner; verify/align **prod==main**;
   proxy + deps + secrets; pre-allocate migs **330–340** (330 DROPs kala_timeline); pin ratified params;
   register the 3 new assets + update the 5 existing. GATE-0 green → fan out. A SETUP failure unresolved
   after the 6-attempt deep-fix ladder = Tier-2 park + Smṛti, NOT a native halt.
2. **Walk the PARALLEL DAG** (maximally parallel; isolated worktree sub-branches per band): **P1**
   U1 ‖ U4-dehardcode ‖ U3-currents-pass1 (file-disjoint → all parallel) → **P2** [serial on ka_sangam]
   U3-school-current → U2-lifetime → re-seal L3 → **P3** ph_nimitta (SPINE, alone) → **P4**
   ph_muhurta ‖ ph_pratikara ‖ ph_sankrama ‖ ph_sodhana (all parallel) → **P5** ph_suddha_sodhana →
   **P6** ph_pramana → **P7** ph_phaladesa → SEAL. Only P2 (ka_sangam touchpoints), P3 (spine), and
   P6→P7 (the tail) are serial; everything else parallelizes. Each band merges at its gate.
3. **Six HARD GATES — each blocks its wave's fan-out:** (a) U4 CHART-GENERALITY (a synthetic fixture
   yields different scores) before persist/wire; (b) ph_nimitta SPINE-FIRST (one anchor across all
   axes+elevations) before W4; (c) ph_sodhana LEAKAGE-FIREWALL (no post-disclosure event in the fit);
   (d) ph_suddha_sodhana NO-AUTO-OVERRIDE (writer never UPDATEs the canonical chart); (e) ph_pramana
   NO-SCORING (zero hit/miss computed); (f) ph_phaladesa B.11 + DETERMINISTIC-FIRST (composes all +
   LLM narrates only the fixed scaffold). Each gate failure → the deep-fix ladder, NOT a native halt.
4. **Frozen orchestrator contract:** `@register('ph_*')`/`WriterBase`/`run(ctx)`; NEVER commit/close
   `ctx.db_conn`; never write `asset_throughput`; `WriterResult(asset_id=, rows_inserted=)`; `$1`
   count_sql (never `$$CHART_ID$$`); delete-then-insert. **COPY the new ph_* writer + service dirs into
   Dockerfile.pipeline** (the bo_pramana_mapa silent-hang gotcha). L4 builds go through the
   orchestrator click-Build path (CF.L3.8), never a reconcile script.
5. **Reuse rule (D10):** READ existing assets → CALL existing services (ka_*, ka_muhurta_seva,
   ka_tulana, the panchang_engine, the bodha_rm store, the school engine) → RECOMPUTE via PyJHora ONLY
   where genuinely absent (ph_sodhana ascendant per candidate; tājaka 49+). Do NOT reimplement panchāṅga,
   remedies, ranking, or the classical tables — they exist.
6. **Anti-drift:** every L4 row references a lower-layer id + inherits its value; NEVER restates a
   computed value; ZERO writes outside `phala_*`. Grep every writer → zero non-phala writes + zero commit/rollback.
7. **L4/L5 boundary (D5):** L4 makes predictions falsifiable + L5-ready; L5 owns ALL scoring/calibration.
   ph_pramana scaffolds + writes the L5 contract but scores NOTHING.
8. **No canonical-chart mutation (D43/B.10):** ph_sodhana + ph_suddha_sodhana STAGE a chart revision for
   one-click native adoption — they NEVER auto-apply it. The canonical chart `482012f1` is untouched.
9. **Verified facts (do not re-litigate):** all 7 dāśā systems are at level-4 in prod (U1 wire-only);
   the school engine is built-but-dormant (U4 = de-hardcode/persist/wire; "M9" is dead naming);
   PyJHora `compute_ascendant` is in-process; bodha_discoveries=1,505; the panchang_engine + bodha_rm
   store + ka_tulana are deep — reuse them. FORENSIC 7/7; only chart `482012f1` (+ the U4 synthetic fixture).
10. **PROD-VERIFY** every AC against prod (Cloud SQL Auth Proxy), not a worktree DB. **Model policy:**
    Gemini/DeepSeek (Anthropic banned); ph_phaladesa narration = Gemini Pro / DeepSeek fallback.

**Cadence (fully autonomous, no human gate):** each Śilpī in its worktree sub-branch: code+tests → the
asset's hard gate → commit → Vimarśaka audit → merge to band → at the band gate merge to feature →
CI-green → **deploy** (migrate runner applies the migration; Cloud Run sidecar rebuilds) →
**build/data-gen** (orchestrator click-Build runs the writer for `482012f1` → rows in `phala_*`) →
PROD-VERIFY. ALL commit/merge/deploy/build/populate is autonomous (AUTONOMOUS_MODE rails). Failures →
the deep-fix ladder (6 attempts, multi-model-parallel) + the disposition classifier — never a native
halt. **Native input:** ONLY the $5k Tier-3 catastrophic-budget ceiling (async, resumable) + the
chart-revision flag (async, STAGED, non-blocking) — nothing else pauses, ever.

**SEAL — the HARD VISUAL gate is FIRST (#1 L3 lesson, burned ~4×):** confirm the deployed Cloud Run
revision == the merge SHA; load the LIVE cockpit Phala panel; confirm **8 assets lit** with real
counts + **zero error/missing_table**, on prod AND localhost. A green `/api/cockpit/stats`, a swarm
"SEALED" report, or a fix on an unmerged branch are ALL false positives — verify the VISUAL surface.
THEN: anti-drift final audit (canonical chart unchanged) → PROD-VERIFY ACs → promote ph_* DRAFT→CURRENT
+ set target_floor=achieved → re-seal L3 → author `L4_PHALA_CLOSE_v1_0.md` + the L5 Mīmāṃsā onboarding
contract (drafted by ph_pramana) → update CURRENT_STATE + SESSION_LOG → merge + push → final Vimarśaka
audit. Log everything to `00_ARCHITECTURE/CONDUCTOR/l4-phala/smriti/` + the halt log.

Begin with **Phase 0** (self-set-up the environment). Report only at band gates, the six hard gates, the seal, a chart-revision flag,
or a Tier-3 event.

---
*End of KICKOFF_L4_PHALA v1.0. The fruit of the tree — where the chart's structural promise, activated
across time, becomes delivered prediction, auspicious timing, managed remedy, rectified foundation,
cross-domain insight, and a master-acharya reading for the native.*

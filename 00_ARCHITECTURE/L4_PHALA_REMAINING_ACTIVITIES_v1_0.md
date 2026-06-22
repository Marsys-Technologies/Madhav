---
artifact: L4_PHALA_REMAINING_ACTIVITIES_v1_0.md
canonical_id: L4_PHALA_REMAINING_ACTIVITIES
version: 1.0
status: SUPERSEDED (2026-06-22) by L4_PHALA_REMAINING_ACTIVITIES_v2_0.md — the operator-gate model here was absorbed into the Conductor-run Phase 0 (D47). Retained for audit trail.
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The single "what do we do next" map. Where we are: Gates A (verify), B (decide), C (author all 12
  briefs + holistic review) are COMPLETE. This lists every remaining activity — Gate D/E (register +
  wire), Gate F (arm autonomy), the autonomous build, and seal — with owner (Cowork / Operator /
  Swarm) and sequence. Tracks against L4_PHALA_PRE_IMPLEMENTATION_CLOSURE_v1_0.md.
---

# L4 Phala — Remaining Activities (the complete set)

## §0 — Where we are (DONE)
- ✅ **GATE A — VERIFY:** prod-truth reconciliation complete (all inputs confirmed; migration max 325; 326–329 pending).
- ✅ **GATE B — DECIDE:** all native ratifications closed (D20–D46 in the decisions ledger).
- ✅ **GATE C — AUTHOR:** all **12 briefs** finalized + closed (4 enablers U1–U4 + 8 ph_* assets), each
  elevated to supreme; the **holistic closing review** done (migration numbering/refs/boundary CLEAN;
  F1 waves + F2 M9-naming + F3 serialization findings recorded; F2 fixed).

## §1 — GATE D/E — REGISTER + WIRE  `[COWORK authors specs → SWARM applies]`
The mechanical-but-precise layer. Cowork specs it; the swarm implements.

| # | Activity | Owner | Detail |
|---|---|---|---|
| D1 | **Asset-registry rows** for all 8 ph_* | COWORK→SWARM | Full AssetDef per asset (asset_id, layer='phala', sort_order 1–8, sanskrit/english names, storage_type, target_table, **count_sql with `$1`**, size_sql, `target_floor:null`, depends_on, scope='per_chart', is_active:true, estimated_seconds:null, asset_kind='artifact', catalog_status DRAFT→CURRENT-at-seal). 3 are NEW (ph_sankrama, ph_pramana, ph_phaladesa); 5 exist (confirm/update). |
| D2 | **count_sql correctness** (the "asset CTS") | COWORK→SWARM | Every chart-scoped count_sql uses `$1` (never `$$CHART_ID$$`); the stats route reads it. |
| D3 | **CAPABILITY_MANIFEST.json entries** | COWORK→SWARM | One per new writer file + one per new DB table (canonical_id, path, version, status, layer:'L4', fingerprint). |
| D4 | **Migration pre-allocation 330–337** | COWORK→SWARM | 330 phala_anchors(+DROP kala_timeline) · 331 muhurta · 332 mitigation · 333 rectification · 334 rectification_best · 335 sankrama · 336 pramana · 337 outlook. All in `platform/supabase/migrations/`. (Plus U2/U3/U4 L3-side migrations in their own range.) |
| E1 | **Orchestrator/DAG wiring spec** | COWORK→SWARM | Each ph_* = `@register('ph_*')` WriterBase in `pipeline/orchestrator/writers/`; DAG from `depends_on`; confirm the full chain topo-sorts (the F1-corrected waves). |
| E2 | **Dockerfile.pipeline COPY** | COWORK→SWARM | Confirm the new ph_* writer + service dirs are COPY'd (the bo_pramana_mapa silent-hang gotcha). |
| E3 | **Cockpit/Nirmāṇa render** | COWORK→SWARM | Layer derived from registry (no frontend hardcode); confirm the Phala panel will show 8 assets. |
| E4 | **The 3 cross-link enhancements (F5)** | COWORK | Fold into the briefs: ph_phaladesa reads ph_pramana confidence tiers; ph_sodhana circularity caveat → ph_pramana; ph_suddha revision-flag → ph_phaladesa. |
| E5 | **U2/U3 shared-ka_sangam serialization (F3)** | COWORK | Encode in the session_queue: U3-currents → U4 → U3-school-current → U2-lifetime (serialized, not parallel). |

## §2 — GATE D/E (cont.) — THE ORCHESTRATION ARTIFACTS  `[COWORK]`
The documents the autonomous swarm actually runs.

| # | Activity | Owner | Detail |
|---|---|---|---|
| O1 | **Campaign plan v2** (`L4_PHALA_CAMPAIGN_PLAN_v2_0`) | COWORK | The governing 12-component design (4 enablers + 8 assets), the F1-corrected 7-wave DAG, the reuse principle (D10), the L4/L5 boundary, all ratified decisions. SUPERSEDES the 6-asset v1.0. |
| O2 | **Session queue** (`CONDUCTOR/l4-phala/session_queue.yaml`) | COWORK | The wave-by-wave Conductor walk: pre-fan-out (PRE-1 prod==main, PRE-2 pre-allocate migs, PRE-3 pin ratified params, PRE-4 register the 3 new assets) → W1–W7 → seal. Encodes F1 waves + F3 serialization + the spine-first + chart-generality + no-scoring + no-auto-override hard gates. |
| O3 | **Kickoff prompt** (`CONDUCTOR/l4-phala/KICKOFF_L4_PHALA.md`) | COWORK | The single paste-block launching the Sūtradhāra Conductor: read order, the hard rules, the model policy (Gemini/DeepSeek), the budget ceiling, the HARD VISUAL SEAL gate. |
| O4 | **Smriti/claim-ledger dir** | COWORK | `CONDUCTOR/l4-phala/smriti/` for the swarm's audit log. |

## §3 — GATE F — ARM THE AUTONOMY  `[OPERATOR + COWORK]`
The rails must be correct BEFORE launch (no human gate at runtime).

| # | Activity | Owner | Detail |
|---|---|---|---|
| F-1 | **Apply migrations 326–329 to prod** | OPERATOR | The A7 gate — these L2/L3 cleanup migrations must land before L4 (reconciliation A6). |
| F-2 | **CI green on main** | OPERATOR | The "main CI red" issue must be fixed first — autonomy merges on CI-green; a red baseline poisons the gate. |
| F-3 | **prod == main** | OPERATOR | Confirm the deployed Cloud Run revision == HEAD; L3 kala_* lit on the LIVE cockpit. |
| F-4 | **Briefs + docs committed to a clean branch off origin/main** | OPERATOR | The swarm reads them from the branch. |
| F-5 | **deploy.yml applies migrations before the job + builds both images** | OPERATOR (verify) | Confirm the migrate step runs pre-Cloud-Run-job. |
| F-6 | **Budget ceiling + AUTONOMOUS_MODE rails confirmed** | NATIVE/COWORK | The per-asset cap + the $5k/wave Tier-3 ceiling (the only synchronous native event); branch/merge/deploy authority enabled. |
| F-7 | **Re-seal authority for L3 (U2/U3/U4)** | NATIVE (confirmed D27) | The swarm may version-bump L3_KALA_CLOSE when the enabler ACs pass. |
| F-8 | **Vimarśaka auto-revert + the HARD VISUAL SEAL gate armed** | COWORK (in O2/O3) | The safety net + the #1 L3 lesson baked in. |

## §4 — THE AUTONOMOUS BUILD  `[SWARM — no human gate]`
The Sūtradhāra Conductor walks the session_queue. Wave structure (F1-corrected):
```
PRE   prod==main · pre-allocate migs 330–337 (+ L3-side) · pin ratified params · register 3 new assets
W1    U1 (dāśā consensus, wire-only)
W2    U3 currents (6) → U4 (school consensus; de-hardcode + chart-generality GATE + persist + wire)
        → U3 school-current (C13, 2nd pass) → U2 (lifetime + null-fix) → re-seal L3
W3    ph_nimitta  (SPINE — alone; SPINE-FIRST hard gate across all 8 axes + 5 elevations)
W4    ph_muhurta · ph_pratikara · ph_sankrama   (parallel; blocked_by ph_nimitta)
W5    ph_sodhana (whole-instrument, LEAKAGE-FIREWALL gate) → ph_suddha_sodhana (NO-AUTO-OVERRIDE gate)
W6    ph_pramana  (falsifiability scaffolding; NO-SCORING gate)
W7    ph_phaladesa (the finale; B.11 gate + deterministic-first gate)
SEAL  see §5
```
Per-wave: commit as ACs land → Vimarśaka post-merge audit → merge at the wave gate → push → CI-green.
Native input: ONLY the $5k Tier-3 ceiling + (if it fires) a chart-revision adoption decision (D43).

## §5 — THE SEAL  `[SWARM — AI-assessed, with the HARD VISUAL gate first]`
1. **HARD VISUAL COCKPIT GATE** (the #1 L3 lesson): deployed Cloud Run revision == merge SHA; the LIVE
   cockpit Phala panel shows **8 assets lit** with real counts + zero error/missing_table — on prod AND
   localhost. (Green JSON / a "SEALED" report / an unmerged-branch fix are all false positives.)
2. Anti-drift final audit (zero non-phala writes, zero commit/rollback, ledgers resolve).
3. PROD-VERIFY every AC against prod. FORENSIC 7/7. Canonical chart NOT mutated (ph_sodhana hypothesis-only).
4. Promote all ph_* DRAFT→CURRENT; set every target_floor = achieved count.
5. Author `L4_PHALA_CLOSE_v1_0.md` + the **L5 Mīmāṃsā onboarding contract** (already drafted by ph_pramana).
6. Update CURRENT_STATE + SESSION_LOG; merge + push; final Vimarśaka audit (temporal + anti-drift).

## §6 — Optional / post-seal
- **Retrieval tools** (serve L4 outputs): query_phala_anchors / find_phala_muhurta /
  query_phala_mitigation / query_rectification / phala_outlook — a thin post-seal wave (does not gate seal).
- **L5 Mīmāṃsā** — the next layer; onboards against ph_pramana's contract (the calibration loop that
  scores L4's predictions). The natural next campaign.

## §7 — Critical path (the shortest line to launch)
```
[COWORK]  GATE D/E specs (D1–E5) + the orchestration artifacts (O1–O4)   ← the remaining Cowork work
[OPERATOR] F-1 apply migs 326–329 · F-2 CI-green · F-3 prod==main · F-4 branch   ← the operator gates
[COWORK]  GATE F arm (F-6/F-8 in the kickoff)
   ────────────────────────  KICKOFF  ────────────────────────
[SWARM]   the autonomous build (§4) → the seal (§5)
```
**The two things that gate everything:** (a) Cowork finishing the orchestration artifacts (O1–O4),
and (b) the operator closing F-1/F-2/F-3 (migrations + CI-green + prod==main). Neither is large; both
are well-defined.

---
*End of L4_PHALA_REMAINING_ACTIVITIES v1.0. Gates A/B/C done. Remaining: GATE D/E (register+wire+
orchestration artifacts) → GATE F (operator gates + arm) → autonomous build → seal. Critical path: the
Cowork orchestration artifacts + 3 operator gates, then kickoff.*

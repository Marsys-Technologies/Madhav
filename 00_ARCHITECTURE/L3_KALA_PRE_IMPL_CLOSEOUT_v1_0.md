---
artifact: L3_KALA_PRE_IMPL_CLOSEOUT_v1_0.md
canonical_id: L3_KALA_PRE_IMPL_CLOSEOUT
version: 1.0
status: CLOSEOUT CHECKLIST — settle ALL before the autonomous Conductor kicks off (becomes §A of the master execution plan)
authored_by: Cowork 2026-06-21 (grounded in 4 parallel sub-agent audits + the L2 PART-A precedent)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
purpose: >
  Everything that must be settled / verified / authored BEFORE the L3 Kāla autonomous swarm launches, so
  the build is seamless and never stalls. Two classes: DECISIONS+AUTHORING (Cowork-completable) and
  OPERATOR/DATA-PLANE actions (need git push + prod DB + deploy — native or swarm-operator). Each item is
  tracked with its evidence + owner. Modelled on L2_BODHA_AUTONOMOUS_EXECUTION_PLAN_v1_0.md PART A.
---

# L3 Kāla — Pre-Implementation Closeout v1.0

## §0 — How this was produced
Four parallel sub-agents audited the codebase + the 13 briefs on 2026-06-21: (1) plan↔code drift
reconciliation, (2) Q4/Q7 + L2-seal-readiness evidence, (3) the may_touch collision audit, (4) the master
execution-plan skeleton. Their findings are folded in below with file:line evidence. **Nothing here is
guesswork — every item is code-grounded or an explicit native decision.**

---

## §A — DECISIONS (native-settled 2026-06-21; evidence-backed)

### D7 — The NATIVE-RATIFY gate strategy → **PRE-AUTHOR before launch**
The I-7 (weights), I-15 (activation templates), I-16 (convergence weights) gates would otherwise HALT the
swarm mid-build. **Decision: Cowork PRE-AUTHORS the templates + weight sets, native approves them in this
prep cycle, they enter the briefs as PRE-APPROVED inputs → the swarm runs uninterrupted.** Deliverable:
`L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md` (authored next; native sign-off pending).

### D-Q4 — bo_samskara placeholder embeddings → **RESOLVED: inherit as known-gap (plan note is STALE)**
Agent finding (`bo_samskara.py`): the writer ALREADY uses **real Vertex AI embeddings**
(`text-multilingual-embedding-002`, 768-dim, lines 6–9 / 27–29 / 62–77 / 179–195); `placeholder_hash_v1`
was already replaced. **No L3 asset depends on semantic embeddings** (checked all 13 briefs — zero embedding
deps; ka_kala_darshana `depends_on: ['ka_sangam','ka_vighnakara']` only). **Action:** update plan §5.5 note
to "code corrected; prod-table vector verification pending (operator)"; do NOT block L3. Residual = a
prod-data-plane check only (does `bodha_signal_embeddings` hold real vectors).

### D-Q7 — the ±10yr transit-search cap → **RESOLVED: ratify coarse-to-fine as the K4 constraint**
Agent finding: cap confirmed (`routers/transit_search.py:66` `if (end_dt - start_dt).days > 365*10`); the
`ka_gochara` brief §3.5 already specs `search_long_horizon()` coarse-to-fine as the Q7 resolution, with an
AC (a 50-yr search finds a far-future event a capped call would miss). **Decision (native-ratified):** the
±10yr cap stays a per-call latency guard; `search_long_horizon()` tiles the horizon → L3 does NOT inherit a
hard ±10yr wall.

---

## §B — PLAN↔CODE DRIFT CORRECTIONS (agent-verified; fold into the plan + briefs)

### DR1 — Daśā systems: **7 actual, NOT the 5 named; Nārāyaṇa absent; KP is a sub-level**
Evidence (`ga_dashas_writer.py:2356–2359` SYSTEMS): the production writer computes **7** systems —
`vimshottari, yogini, ashtottari, chara_karaka, naisargika, mudda, kalachakra`. **Nārāyaṇa does NOT exist**
(no `compute_narayana_system`). **KP is NOT a standalone system** — it is a sub-level dimension under
Vimśottarī (`kp_sublevel`, `compute_kp_subperiods` lines 855–964). The plan's "5 systems
(Vimśottarī/Yoginī/Chara/Nārāyaṇa/KP)" was inherited from the OLD M3 prototype scripts.
**Action:** correct plan §5.6/§5.7.4 + the `ka_dasha_kala` brief to the 7 actual systems; mark Nārāyaṇa as
"not computed / future work"; note KP = Vimśottarī sub-level.

### DR2 — Daśā level floor: **TWO tables; production = `chart_dashas` (level-4 Sookshma), not `ganita_dashas` (level-3 PD)**
Evidence: `ganita_dashas` caps at **level 3 / PD** (`0001_brahma_baseline.sql:1818` CHECK level IN (1,2,3));
BUT the production writer writes **`chart_dashas`**, capped at **level 4 / Sookshma**
(`mig 211:103–105` `cd_level_n_max4` CHECK; writer rail "ZERO level_n=5"). Level-5 (Prāṇa) is NOT computed
by any script and is forbidden by both storage tables.
**Action:** (a) **`ka_dasha_kala` should read `chart_dashas` (level-4), not `ganita_dashas` (level-3)** — the
plan's "ga_dashas" was ambiguous; chart_dashas is the richer production source. (b) Correct plan §5.9.1's
"MD→AD→PD→Sookshma→Prāṇa ≈ 9⁵" to a **level-4 floor**; if Prāṇa is ever needed, it is an **on-demand,
non-persisted** in-memory recursion below a level-4 interval (never written — would violate `cd_level_n_max4`).

### DR3 — Node convention: **TRUE_NODE (the code) wins; the PHASE_4D brief is the outlier**
Evidence: the live ephemeris store (`l0_ephemeris.py:76` swe_id 11 = TRUE_NODE) AND the transit engine
(`compute_transits.py:54–64` `swe.TRUE_NODE`) both use **TRUE_NODE**. The PHASE_4D brief mandates MEAN_NODE
(lines 61/100/109/265) and falsely claims the ephemeris store is MEAN-anchored.
**Action:** L3 standardizes on **TRUE_NODE**. The `ka_gochara` brief §3.4 already flags this — confirm it
resolves to TRUE_NODE. The PHASE_4D brief's MEAN claim is to be ignored/overridden (it lives on an unmerged
branch + is archived as retired). No code change needed — code is already consistent on TRUE_NODE.

---

## §C — SWARM-SAFETY FIXES (collision audit; settle before parallel fan-out)

### CS1 — `asset_registry_seed.ts` is touched by ALL 13 briefs → **SERIALIZE per wave**
The universal collision. Waves are serialized (K0→K6), but K1 (3 agents), K5 (2), K6 (3) have INTRA-wave
peers all editing this one file. **Action:** within each multi-agent wave, serialize seed-file edits — a
single post-wave "seed reconciliation" step appends that wave's rows in one commit, OR a designated owner
lands each row. NEVER let intra-wave peers edit `asset_registry_seed.ts` concurrently. (Encode in the
session_queue.)

### CS2 — 8 NEW migrations each say `<next>` → **PRE-ALLOCATE the number block**
Eight briefs (K0, ka_yojaka, ka_sangam, ka_vighnakara, ka_kalasutra, ka_kala_darshana, ka_jivana_parva,
ka_bhavishya_lekha) create a `<next>_kala_*.sql`. Parallel agents resolving `<next>` independently WILL
collide on the integer. **Action:** the Conductor pre-assigns the contiguous block in DAG topological order
(K0=N, …) at launch, BEFORE fan-out. Confirm the canonical tree (`platform/supabase/migrations/`) + next
free number (the "two-migrations-numbered-174" trap — document it).

### CS3 — DAG contradiction `ka_kala_darshana` ↔ `ka_vighnakara` → **FIXED 2026-06-21**
The catalog brief listed `ka_vighnakara` in BOTH `blocked_by` AND `parallel_safe_with` (mutually exclusive).
The dependency is real (window-collision detection reads danger windows, §3.4). **FIXED:** `parallel_safe_with`
set to `[]`; ka_kala_darshana runs AFTER ka_vighnakara within K5. (Edit applied to the brief.)

### CS4 — `service-asset-type` not a resolvable asset_id → **NORMALIZED 2026-06-21**
The 3 K1 service briefs referenced K0 as `service-asset-type` (a type name, not an asset_id). **FIXED:**
normalized to `k0_service_asset_type` in all three `blocked_by` lists, so a DAG validator resolves the edge.

### CS5 — K0's `orchestrator/**` glob is broad → tighten (non-blocking)
K0 declares `pipeline/orchestrator/**` for a service-self-test path. Since K0 runs ALONE first (no temporal
overlap with writers), it is safe; tighten the glob to the specific self-test file to avoid future
false-positive lock contention. (Low priority.)

---

## §D — OPERATOR / DATA-PLANE ACTIONS (need git + prod + deploy — NOT Cowork-executable)

### OP1 — Branch reconciliation (Q5) — **OPERATOR/SWARM, HARD PART-A gate**
4 unmerged temporal branches carry overlapping work: `feature/subsystem-transit`,
`feature/panchanga-service-registry`, `feature/panchanga-rich-output`,
`feature/l0fr-stream-e-panchanga-service`. **Lean (plan Q5):** consolidate the panchanga branches first
(most-real, most-depended-on), then transit. K2 (`ka_gochara`) builds on this — if not reconciled, K2 forks
the mess. **This is a hard pre-kickoff gate** (agent §C flagged it). Owner: operator/swarm-prep.

### OP2 — Commit the swarm inputs onto a clean branch off `origin/main`
The 13 briefs + the campaign plan + this closeout + the templates/weights doc are currently UNCOMMITTED
(on `fix/seed-bodha-m326-parity`). They are the swarm's INPUT artifacts — commit them onto a fresh branch
off main before the Conductor reads them. (Also normalize the briefs dir case: `BRIEFS/` is the on-disk
truth; the master plan must use that path.)

### OP3 — Prod == main verification (the seed→prod divergence guard, the Brahma V1.3 lesson)
Confirm `origin/main` HEAD == deployed prod revision; L2 migrations (incl. 326 / bo_* floors) APPLIED on
prod; `/api/cockpit/stats?chart_id=482012f1-...` shows live L1+L2 state. The swarm's ACs verify against
prod, so prod must be a known-good baseline. Owner: operator.

### OP4 — L2-seal prod-live + the two residual prod checks
On-disk, L2 is code-ready (D-L2 below). Prod residuals: (1) `bodha_signal_embeddings` holds real Vertex
vectors (not a stale placeholder run); (2) the 4 L3-fill hook columns are NULL in prod as expected. Owner:
operator (both are prod-data-plane reads).

### D-L2 — L2-seal code-readiness → **CONFIRMED (on-disk)**
Agent finding (`bo_laksana.py`): the 4 L3-fill hooks exist at the exact lines the briefs cite —
`dasha_activation_proximity_score` (760), `signature_class` (787), `active_dasha_periods_jsonb` (792),
`activation_predicted_dates_jsonb` (793), all written NULL "L3 Kāla fills them." `bodha_msr_signals` is the
signal table. `ka_yojaka` + `ka_kalasutra` consume exactly these via `signal_id` reference, zero L2 write-back.
**L2-seal is code-ready for the L3 build.**

---

## §E — CONDUCTOR INPUTS TO AUTHOR (Cowork — the master-plan pass)
- [ ] `L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md` — the PRE-APPROVED I-15 templates + I-7/I-16 weights (D7). **Next deliverable; native sign-off.**
- [ ] `L3_KALA_AUTONOMOUS_EXECUTION_PLAN_v1_0.md` — the master plan (skeleton drafted by agent-4; flesh out: PART A = this closeout; PART B = the K0→K6 wave queue + the ka_sangam spine gate + the swarm roles; §C risk flags).
- [ ] `00_ARCHITECTURE/CONDUCTOR/l3-kala/session_queue.yaml` — the wave/asset queue with the gates + the CS1/CS2 serialization + pre-allocated migration block.
- [ ] `KICKOFF_L3_KALA_AUTONOMOUS.md` — the single paste-prompt (standards + L3 gates + pre-approved inputs + AUTONOMY_RESILIENCE pointer).
- [ ] Smṛti dir + halt log under `.../l3-kala/`.
- [ ] Cross-check vs. the existing `RED_TEAM_L3_v1_0.md` (agent-4 flagged it exists — reconcile its findings).

---

## §F — THE CLOSEOUT GATE (all green before kickoff)
| # | Item | Class | Status |
|---|---|---|---|
| D7 | Pre-author + ratify weights/templates | decision+author | ✅ RATIFIED 2026-06-21 (L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md; form + weights signed off) |
| D-Q4 | bo_samskara = known-gap | decision | ✅ RESOLVED |
| D-Q7 | coarse-to-fine ratified | decision | ✅ RESOLVED |
| DR1 | 7 daśā systems | drift-fix | PENDING plan/brief edit |
| DR2 | chart_dashas level-4 | drift-fix | PENDING plan/brief edit |
| DR3 | TRUE_NODE | drift-fix | ✅ code already consistent; confirm in ka_gochara |
| CS1 | serialize seed edits | swarm-safety | PENDING (session_queue) |
| CS2 | pre-allocate 8 migrations | swarm-safety | PENDING (Conductor) |
| CS3 | darshana/vighnakara DAG | swarm-safety | ✅ FIXED |
| CS4 | service-asset-type id | swarm-safety | ✅ FIXED |
| OP1 | branch reconciliation (Q5) | operator | PENDING (hard gate) |
| OP2 | commit inputs to clean branch | operator | PENDING |
| OP3 | prod==main verify | operator | PENDING |
| OP4 | prod residual checks | operator | PENDING |
| §E | Conductor inputs authored | author | PENDING |

---
*End of L3_KALA_PRE_IMPL_CLOSEOUT v1.0. Decisions D-Q4/D-Q7 resolved; DR3/CS3/CS4 done; D7 + the drift edits
+ the Conductor inputs are the remaining Cowork authoring; OP1–OP4 are operator/data-plane gates. The build
launches only when §F is all-green.*

---
artifact: NIGHT1_CONDUCTOR
type: EXECUTION CHARTER (lane DAG + rebuild protocol + verification swarm + merge/deploy + failure handling)
version: 1.0
status: READY
campaign: Doctrine Campaign D-1 / Night-1
governs: LANE0_CR87_HOTFIX.md, LANE1_GA_STRUCTURAL_MODULARIZATION.md, LANE2_GA_VICHARA.md, LANE3_DETECTOR_REGISTRY.md, LANE4_MSR_ELEVATION.md, LANE5_DENSITY_RETROFIT.md
design_ref: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §8 (D-1 row), §9 (disposition map)
---

# NIGHT-1 CONDUCTOR — D-1 judgment substrate + CR-87 hotfix

## 0. What Night-1 ships

Design §8, D-1 row: **"Judgment substrate §4 (`ga_vichara` + detector registry + valence + varga-ratification matrix + leverage_index) + §N.6 density ratified + MSR elevation §11"** — plus the independent CR-87 hotfix, which "ships in Night-1 regardless of D-1 progress."

Charts of record: Abhisek `482012f1-710e-4a25-994a-93821f5871aa` (canonical; `362f9f17-…` is a dead phantom — never write it), Abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a`.

## 1. Lane DAG

```
LANE0 (CR-87 hotfix) ──────────────────────────────► merge (independent at ANY time; do not gate on L1–L5)

LANE1 (ga_structural modularization + effective_dignity)
   └─► LANE2 (ga_vichara — new asset)
           ├─► LANE3 (detector registry: yogas/NBRY/dosha-cancellation)
           └─► LANE4 (MSR elevation)
                       └─► LANE5 (§N.6 density retrofit on touched tools)
                            (L5 also consumes L3's catalog_only semantics;
                             L5 starts once L3+L4 are merged, runs alongside
                             their rebuild verification)
```

- **Parallel worktrees:** L0 always; L1 alongside L0. L3 and L4 run in parallel with each other (both depend only on L2's merge). L5 last.
- **Sequencing rule:** a dependent lane branches FROM the integration branch after its prerequisite lane has merged into it — never from an unmerged sibling worktree.
- **Migration serialization:** migration numbers are the one cross-lane shared resource. Conductor allocates them at lane start (expected: L2 → next free after 366, L3 → next, L4 → next; re-check `ls platform/migrations | grep -E '^[0-9]+' | sort -n | tail -1` at each allocation). A lane never renumbers another lane's migration.
- Every lane brief is self-contained; implementers read ONLY their brief + the files it names. Lane implementers never run chart rebuilds, never deploy, never merge — the conductor does.

## 2. REBUILD PROTOCOL (native-specified; binding verbatim)

The following protocol governs every chart rebuild in this campaign. No deviation without native approval.

1. **Exclusive lock.** One rebuild pipeline at a time, system-wide. Before starting, verify no other build run is active (`build_runs` has no in-flight row; cockpit shows idle). Take the lock (do not start a run if any other agent/session could start one — announce the rebuild window before beginning).
2. **Global cleanup first.** Before the first chart, run the global cleanup pass (stale build artifacts, failed-run residue, orphan rows from aborted runs) so rebuilds start from a clean state.
3. **Chart order: Abhinandan first, then Abhisek.** `1c826d5a-41cb-4450-b4dc-59d440e5f75a` is rebuilt and verified BEFORE `482012f1-710e-4a25-994a-93821f5871aa`. (Non-native first: if the new code breaks, it breaks on the guard chart, and the FORENSIC-anchored native chart still holds the prior good build.)
4. **Sequential layers per chart: L1 → L2 → L3 → L4 → L5.** Each layer completes (all assets `lit`) before the next layer starts. Never build layers of one chart in parallel; never interleave two charts.
5. **Never parallel.** No concurrent asset builds outside what the orchestrator itself schedules within a layer run; no second chart, no second run, no "quick single-asset rebuild" on the side while the protocol runs.
6. **Guardian agent watches to completion.** A dedicated agent monitors the run end-to-end (SSE / `build_runs` / `asset_throughput` states): per-asset building→lit transitions, substep heartbeats advancing, reaper non-interference; on any asset `error` it captures logs immediately and invokes §5 failure handling. The run is not "done" because it was started; it is done when the guardian reports all assets lit and the post-checks pass.

Post-rebuild per chart, before the next chart/step: FORENSIC anchor check (§4.1), row-count sanity vs `asset_registry.count_sql` (>0 for every rebuilt asset incl. `chart_vichara`), and the lane-specific acceptance queries.

## 3. Merge / deploy sequence

1. **Worktree → integration branch.** Each lane develops in its own worktree branch (`night1/lane0-cr87`, `night1/lane1-structural`, …). Merge into a single integration branch `night1/integration` in DAG order (L0 may merge any time). Each lane merge requires: lane acceptance checklist self-reported complete + full local suite green.
2. **CI 14/14 + verification swarm sign-off** on the integration branch (the repo's full quality gate: ESLint, TypeScript, Python suite, integration tests — the "14/14" gate the campaign has used since W4). The verification swarm (§4) runs per-lane checks against a dev-DB build.
3. **Squash merge** `night1/integration` → `main` (one squash per lane, in DAG order, preserving lane provenance in commit messages; PR bodies per repo convention).
4. **Chart rebuilds per §2 protocol** (Abhinandan → Abhisek, sequential layers, guardian watching) against the merged main.
5. **Prod deploy** (web + mcp) only after both charts rebuilt + §4 swarm green on rebuilt data.
6. **Smoke test** on deployed: `ganita_vichara_get`, `bodha_signals_get(domain=wealth, top_k=15)`, `ganita_yogas_get`, `judgment_query(wealth)` against 482012f1 — assert the Lane-4/5 acceptance specimens on the LIVE channel (top-15 wealth no longer 14/15 neutral boilerplate; dhana yoga served; no catalog-only row rendered as a finding).
7. **Auto-rollback condition:** if smoke reveals (a) FORENSIC anchor failure, (b) a previously-PASS census tool now FAILing/DEGRADED, or (c) any silent-wrong-answer regression (CR-42 class) on the smoke set → immediately re-point prod to the prior image/revision, keep main frozen, and open a failure report. Data-plane rollback: the prior build's rows are replaced per §N.3 delete-then-insert — restore by re-running the rebuild from the pre-merge main if required.

## 4. Verification-swarm charter (what "done" means per lane)

Independent verifier agents (not the implementing agent) check, with evidence (SQL output / tool payloads / test logs), before a lane counts done:

### 4.1 Universal checks (every lane)
- **FORENSIC 7/7 anchor check** on 482012f1 after any rebuild it participates in: Sun=Capricorn · Moon=Purva Bhadrapada · Lagna=Aries (all 5 ayanamshas) · Tithi=Shukla Tritiya · Vara=Ravivara · Yoga=Shiva · Karana=Garaja (live via `ganita_natal_positions_compute`, per the CR-53 precedent).
- Full test suite zero new failures; migration-guard sign-off on any migration; no writes to `asset_throughput` from writer code; no orchestrator-core diffs (`pipeline/orchestrator/writers/__init__.py`, `runner.py` byte-identical unless the native approved otherwise).
- No occurrence of the dead phantom chart id; no new hardcoded natal constants (Lane 0's grep tripwire test passes estate-wide).

### 4.2 Per-lane acceptance (the lane briefs' checklists are the contract — verify, don't trust)
- **L0:** §4 checklist of LANE0 brief. Specifically re-run: (a) 482012f1 engine outputs bit-identical to the pre-fix fixture (**CR-87's fix must not change Abhisek's existing correct scores** — this is the named regression guard); (b) 1c826d5a scores differ from 482012f1 on tara/sade-sati/panchanga currents; (c) `_NATIVE_*` grep = 0.
- **L1:** row-parity (all families stable except `graha_effective_dignity_modified_by_aspects`), registry-completeness test, import-shim intact, effective_dignity v2 stamped.
- **L2:** `chart_vichara` populated for BOTH charts, all families; ratification_factor ∈ [0.6,1.4] (SQL: `SELECT count(*) FROM chart_vichara WHERE vichara_family='varga_ratification' AND (value_num < 0.6 OR value_num > 1.4)` = 0); 482012f1 specimens: 8L-Mars→H2 strong_malefic, Venus+Saturn D9 divergence rows, Venus #1 wealth leverage; 0 orphan constituent_fact_ids.
- **L3:** 482012f1 firings present (dhana/budha_aditya/sarasvati + NBRY-D9 Saturn & Venus with grounds); kemadruma/daridra/kala_sarpa-D1 NOT firing; no requires_pass row served as a finding.
- **L4:** tier distribution (chart_defining 0.5–3%, supporting <85%); CR-54 specimen malefic + ≥major; divergence signals in wealth top-15; class-prior live; weakest_graha=VENUS (or documented handoff closed by L5); position-class specimens un-starved.
- **L5:** envelope byte caps on scoped tools; loud facet rejection; catalog-only gating; `ganita_vichara_get` live; alias-pair payload equality on touched pairs.
- **Cross-lane regression:** re-run the CR-31/CR-53/CR-70 verified-positive baseline spot checks on the rebuilt charts (dates live, attribution 0% unattributed, DEFECT-001 = 0 orphans, L2 22/22 tools PASS) — the register's "do NOT re-flag" lists are the regression baseline; nothing on them may regress.

## 5. Failure handling (binding)

A blocked or failing lane agent does **not** halt the run and does not thrash: it packages full context — its brief, branch, failing output, exact error, what it tried — and hands off to a **fresh Opus-pinned specialist agent** spawned for that blockage, which continues the lane. The run as a whole halts ONLY on systemic risk: database-integrity danger (writes outside the lane's declared tables, transaction-ownership violations) or main-breaking risk (integration branch cannot pass CI and the cause is cross-lane). In those two cases: freeze merges, preserve worktrees, report to the native with the failure package. Everything else — a slipped lane, a failed acceptance criterion, a flaky test — is handled by handoff + re-verification, with downstream lanes waiting per the DAG rather than starting on unverified prerequisites.

## 6. Standing constraints (apply to every lane; from CLAUDE.md §L/§N + the design)

- The orchestrator is FROZEN — "if a writer seems to need a contract change → STOP and raise with the native" (§N.2).
- B.10: no fabricated computation anywhere; B.3: every judged row carries its constituent fact ids; §N.5: L1 authority — L2+ references, never restates.
- Floors aspirational, not gates (§N.4): set `target_floor` after achieved counts; never pad.
- D-2/D-3/D-4 concerns (vidhi engine, CGM/mechanism, Kāla Taraṅga, Three-Lock, calibration ignition) are OUT for every lane tonight — the disposition map (design §9) is the boundary authority.
- No lane writes report/summary files outside its worktree + the handback message; ledger/SESSION_LOG entries are the conductor's close-out responsibility per the governance protocol.

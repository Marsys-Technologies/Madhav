---
artifact: REMEDIATION_RUN_LEDGER_v1_0
type: PROGRAM_RUN_LEDGER (conductor state machine — the program's persistent memory, plan §7.7)
version: 1.0
status: LIVE
governing_plan: 00_ARCHITECTURE/llm_consumption_audit/REMEDIATION_PLAN_v3_0.md
execution_vehicle: CLAUDECODE_BRIEF.md (status ACTIVE — ratified by native 2026-07-12)
opened_by: claude-opus-4-8[1m] (Program Conductor), session LLM-CONSUMPTION-REMEDIATION-W0-2026-07-12
opened_at: 2026-07-12
role: >
  Single source of truth for the LLM Consumption Remediation program (W0→W4). Every
  sub-session opens by reading this ledger and closes by appending state. Records: wave →
  WP → intervention → verification verdicts → merge/deploy records. Any interruption
  resumes losslessly from here. Immutable-append discipline: never rewrite history rows;
  append new state. Audit artifacts (findings.jsonl, state/**, AUDIT/GATE docs) are NEVER
  touched by this program (brief must_not_touch).
changelog:
  - v1.0 (2026-07-12): created at conductor kickoff. Self-provisioning probes recorded;
    W0 session_open handshake embedded; wave state machine initialized (all waves PENDING).
---

# LLM Consumption Remediation — Run Ledger

## §0 — Program state machine (top-of-ledger status board)

| Wave | Scope | State | Deploy point | Notes |
|---|---|---|---|---|
| W0 | WP-0.1 (LCA-17 wrong-chart isolation) | ✅ **DONE** (deployed `amjis-web-00955-qt5` == main `6ec244c0`; 2026-07-12) | ✅ deployed | isolation proven; PR #553 merged; prod-parity confirmed |
| W1 | WP-1.1/1.2/1.3/1.4/1.5/1.6/1.7/1.8 (serving plane) | **IN_PROGRESS** | after W1 close | 7 lanes parallel; WP-1.6 last |
| W2 | WP-2.1/2.2/2.3/2.4/2.5 (writer packages) | PENDING | after W2 close | writers+JOB image live before W3 |
| W3 | WP-3.1 Abhinandan rebuild → WP-3.2 native rebuild | PENDING | consumes W2 | snapshot + golden catches + auto-restore; FORENSIC 7/7 |
| W4 | WP-4.1 re-audit + gates | PENDING | final (loop fixes only) | gates §2 evaluated mechanically |
| CLOSE | cleanup + main↔production sync proof | PENDING | — | §7.6 five steps in order |

**Current position:** ✅ W0 CLOSED. **W1 IN PROGRESS — CHECKPOINT after Batch B1 (2026-07-12).** integration
branch `integration/w1-serving-plane` (`97d6fe9c`, pushed) carries **6 verified lanes, all blind-verified
CONFIRMED-FIXED**: WP-1.1 ✅, **WP-1.2 (α+β) ✅ COMPLETE**, WP-1.7 ✅, WP-1.3(d,g) ✅, WP-1.3(b,c) ✅.
Deployed-channel verification LIVE (§1b.2). LCA-17 live residual CLOSED.
**Update (post-B2):** integration `integration/w1-serving-plane` now carries **11 verified lane merges** —
WP-1.1, WP-1.2(α+β), WP-1.7, and **WP-1.3 COMPLETE (a–i)**. ND-W1.1 reconciliation gate in flight.
**REMAINING W1 lanes (next session, re-ground from here):**
  - **WP-1.2β** — domain discrimination + new domains (moksha 4-8-12+Ketu, education/vidya, character/buddhi,
    bhava→domain un-collapse). Doctrine-heavy; jyotish-domain verifier. Branch from integration.
  - **WP-1.3** — the GIANT (295 findings, 7 CRIT). MUST be split into sub-lanes a–i (serve 23 computed-but-unserved
    assets; query_dasha_periods system_id; dasha window params; lel_query 57 events; temporal windows serving;
    query_chart_facts filters+pagination+6 ayanamshas; msr_sql projection; dead-tool purge; apex/assess dedup).
    Overlaps ranking/envelope → branch from integration, sub-lanes serialized/partitioned. serving-wire + data-plane.
  - **WP-1.5** — program-wide envelope contract (honest truncated/total/cursor; budget ceilings; R-38/R-41
    deployed retest). Touches all tools → branch from integration, sequence carefully vs WP-1.3. serving-wire.
  - **WP-1.8** — cross-path fidelity + varga-aware verdicts (D-1/G-7 dignity+shadbala columns; varga terms in
    verdict formula — AFTER WP-1.5). jyotish-domain + data-plane.
  - **WP-1.4** — large-N synthesis instrument (design + skeleton only in W1; mostly new files). jyotish-domain.
  - **WP-1.6** — capability map (LAST; regenerate AFTER 1.2/1.3/1.4/1.5 land). data-plane.
**W1 CLOSE (after all lanes):** PR `integration/w1-serving-plane` → main → CI → single deploy (rebuilds
amjis-web + amjis-mcp) → live prod-verify full W1 acceptance suite → register dispositions → CURRENT_STATE +
SESSION_LOG. **Resume point: THIS LEDGER + the pushed integration branch.**

---

## §1 — Self-provisioning record (brief §3, plan §7.2)

**Timestamp:** 2026-07-12 (conductor kickoff session).

### §1a — Repo sync
- Branch: `main`; HEAD = `5eebc6d0ba4ec8a7ab946e11be05d7a81fa5fe08`.
- `git fetch origin` clean; `git rev-list --left-right --count origin/main...HEAD` = `0  0` → **main == origin/main**.
- `git status` clean tree (plan v1/v2/v3 + wp_coverage.jsonl + brief committed to main by the
  Cowork planning session, commit "docs(remediation): master plan v1–v3 + WP coverage manifest
  + conductor brief (RATIFIED, ACTIVE)"; CI Ganga Quality Gate in_progress on that commit at probe time).
- **Verdict: SYNC OK — no reconciliation needed (brief §3a).**

### §1b — Read-only probes
| Probe | Result |
|---|---|
| DB (via cloud-sql-proxy → **PRODUCTION**, per CURRENT_STATE v6.37) | ✅ reachable. `mcp__postgres__query` read-only OK. `chart_facts(482012f1)` = **135,645 rows** (⚠ see §1c). |
| gh CLI / GitHub | ✅ authed (account `amonty84`, keyring, https). |
| CI | ✅ recent runs on main; "TAP CI" success, "Ganga Quality Gate" in_progress on plan commit. |
| gcloud / deploy creds | ✅ authed (`mail.abhisek.mohanty@gmail.com` + `firebase-admin` SA); project `madhav-astrology`. |
| Cloud Run services (asia-south1) | ✅ `amjis-mcp`, `amjis-sidecar` (deployed 2026-07-12T02:21Z), `amjis-web`. Deploys are GitHub-Actions driven (`github-actions@` SA is last-deployer). |
| Deployed MCP channel (the real consumer channel, 130 tools) | ⚠ **claude.ai MARSYS-JIS connector requires OAuth; this Claude Code session is non-interactive → connector unavailable in-session.** The audit reached the deployed MCP over HTTP; the security/entitlement verifier for WP-0.1 must use the HTTP path (endpoint `https://amjis-mcp-938361928218.asia-south1.run.app`). **ACTION: verifier lane establishes the HTTP probe harness (auth mechanism TBD from audit tooling) before WP-0.1 acceptance.** |

### §1b.1 — Deployed-MCP auth model (blocks live prod re-verify) — RESOLVED-DECISION-PENDING
- Deployed `amjis-mcp` is **IAM-gated** (`--no-allow-unauthenticated`, per `.github/workflows/deploy.yml`;
  `platform/scripts/governance/edge_security_smoke.sh`). Client auth = Google identity token (IAM) **+**
  app Bearer `mcp_<env>_<40char>` validated by `validateMcpKey` (PBKDF2-SHA256) → `/api/mcp/execute`
  (service-token + principal headers).
- **No MCP bearer key present in local env** (only model-provider keys). Minting one via `generateMcpKey`
  writes a row to a prod product table → NOT done unilaterally (brief: no manual DML on product tables).
- **Consequence:** a full *live-concurrency* deployed-channel probe of `get_chart_orientation` (both charts
  interleaved) is not executable in this non-interactive session without native-provided connector auth or
  an issued MCP key. **Standing evidence for WP-0.1 remains the in-process 2M-iteration blind-verified proof
  on the exact code path the service runs.** Decision to surface to native at W0 deploy gate.

### §1b.2 — Deployed-channel verification UNLOCKED (2026-07-12, post-restart) — RESOLVED
- Native provisioned a **direct API-key MCP connector** `marsys-jis-direct` (no OAuth; api_key query param).
  Usable after a Claude Code restart (harness wires MCP at startup). Session restarted 2026-07-12 →
  `mcp__marsys-jis-direct__*` tools LIVE. **§1b.1 constraint RESOLVED for all remaining waves** — prod-verify
  upgrades from Option-1 parity to real deployed-channel proof.
- **W0 deferred live-channel residual DISCHARGED:** live `get_chart_orientation` (deployed channel) returns
  correct per-chart data — native `482012f1` → 13364/15/22 (weakest Mercury); Abhinandan `1c826d5a` →
  13369/13/22 (weakest Saturn). Exactly the LCA-17 discriminating pair, now correct (native no longer gets
  Abhinandan's 13369). Combined with the in-process 2M-iter concurrency proof → LCA-17 CLOSED on the real channel.
- **Live W1 ground-truth captured** (for WP-1.2 verification): top entity_profile = `UNATTRIBUTED` @ 64.6 (native)
  / 84.8 (Abhinandan); `grounding.fact_ids=[]`; descriptive trivia (akshara/pakshi/presiding_deity) at `major`
  tier — LCA-14 + salience-drowning confirmed live.
- **Security note (native-owned):** api_key is plaintext in `~/.claude.json` and authenticates directly to
  PRODUCTION — treat as a prod credential; rotate/env-var later.
- **✅ LCA-17 live-channel residual CLOSED (2026-07-12, native Cowork probe):** independent deployed-channel
  probe — `get_chart_orientation`, **6 concurrent interleaved calls** alternating `482012f1`/`1c826d5a` (the
  original LCA-17 trigger pattern) — returned the CORRECT chart_id + distinguishing digests on all 6
  (13364/15/Mercury vs 13369/13/Saturn), **ZERO substitutions**. This is the live-channel complement to W0's
  in-process 2M-iteration proof. **W0 disclosed residual fully discharged on the real channel.**

### §1c — Probe observations carried forward (not W0 scope)
- **[OBS-1] chart_facts row-count divergence:** native `chart_facts` = 135,645 on prod vs L1_GANITA_CLOSURE canonical 27,554 (~4.9×). **HYPOTHESIS (native, 2026-07-12): 135,645 ≈ 27,554 × ~5 ayanamshas — the L1 closure count was likely PER-ayanamsha, and prod stores all 5.** Not accretion/idempotency drift if so. **Verify FIRST at W3 reconciliation with one `SELECT ayanamsha_id, COUNT(*) FROM chart_facts WHERE chart_id=... GROUP BY ayanamsha_id` query** — if ~5 roughly-equal groups → hypothesis confirmed, benign. Do NOT act before W3.

### §1d — Deploy mechanism (confirmed)
- Deploy = merge to `main` → GitHub Actions `deploy.yml` auto-builds/deploys affected services
  (sidecar / web / mcp; JOB image for writers). CI required checks gate merge: TypeScript,
  Unit Tests, Secret Scan, Governance Gates (per prior source-control session). Migrations run
  before deploy. **Per-wave deploy (§7.4) = wave merge to main + CI-driven deploy + prod re-verify.**

---

## §2 — Session ledger (append-only)

### Session 1 — LLM-CONSUMPTION-REMEDIATION-W0-2026-07-12 (conductor kickoff + W0 open)

```yaml
session_open:
  session_id: LLM-CONSUMPTION-REMEDIATION-W0-2026-07-12
  cowork_thread_name: "Madhav — LLM Consumption Remediation (W0: LCA-17 isolation)"
  agent_name: claude-opus-4-8[1m]
  agent_version: claude-opus-4-8[1m]
  step_number_or_macro_phase: REMEDIATION-W0
  predecessor_session: LLM-CONSUMPTION-AUDIT-EXECUTION-CAMPAIGN (CURRENT_STATE v6.37 close)
  mandatory_reading_confirmation:
    - file: CLAUDECODE_BRIEF.md
      fingerprint_sha256: 091dfafdb873f7803f081a342aaa30ce97c5daf123b38dc969fa4907bb0e2820
      read_at: 2026-07-12T00:00:00+05:30
    - file: CLAUDE.md
      fingerprint_sha256: 02045c8da246e2cc86261f20e01e791575f6cf375be7f02ea29854797f02eab6
      read_at: 2026-07-12T00:00:00+05:30
    - file: 00_ARCHITECTURE/llm_consumption_audit/REMEDIATION_PLAN_v3_0.md
      fingerprint_sha256: 7b6019227ee7357262ebcf3a9b45457b82d63fa7d21c18f43204eca7da32f663
      read_at: 2026-07-12T00:00:00+05:30
    - file: 00_ARCHITECTURE/llm_consumption_audit/REMEDIATION_PLAN_v2_0.md
      fingerprint_sha256: 88750dc824a4466eb3ac5ad28040680cb72b9e2f0b804bf62b25f1ed769074f5
      read_at: 2026-07-12T00:00:00+05:30
    - file: 00_ARCHITECTURE/llm_consumption_audit/deliverables/wp_coverage.jsonl
      fingerprint_sha256: d0de771d37ee0ce829d35ccfaec5f773c622c9f0386ac62f34c1cdcc1f20d708
      read_at: 2026-07-12T00:00:00+05:30
    - file: 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
      fingerprint_sha256: 7a78ba58230f5f7452ad5423a1b495f0397c1824df9158697255ec20656072da
      read_at: 2026-07-12T00:00:00+05:30
    - file: 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
      fingerprint_sha256: da2007d87e5b0a2d7c4c3fdf0393681be51adaefb680d1c34b724f230823ed39
      read_at: 2026-07-12T00:00:00+05:30
    - file: 00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md
      fingerprint_sha256: 6b34a5b849ea19e59ef528c2d0184ad9ddcb1a4c640a50196f012b3958b79d46
      read_at: 2026-07-12T00:00:00+05:30
    - file: 00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md
      fingerprint_sha256: e2771595a114bf5b41dd077403a346bc002762dbff015e091781c14476981807
      read_at: 2026-07-12T00:00:00+05:30
    - file: 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
      fingerprint_sha256: 347e72e651dd351bbe97fe52f07abf64aae3cc494281a3578fb39d36b4843b83
      read_at: 2026-07-12T00:00:00+05:30
    - file: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
      fingerprint_sha256: 8e98ad46d7f0ba5ee4a9605f17f8ef21ba6da6d126092f7e0c52d318bc9e6c6e
      read_at: 2026-07-12T00:00:00+05:30
    - file: 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md
      fingerprint_sha256: 3f556898312c7744e3cbe24d2de94033d445baf6166ed07335b0c839a7b1c7fd
      read_at: 2026-07-12T00:00:00+05:30
  declared_scope:
    may_touch:
      - platform/**
      - platform/migrations/**
      - 00_ARCHITECTURE/llm_consumption_audit/**
      - 00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md
      - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
      - 00_ARCHITECTURE/SESSION_LOG.md
      - CLAUDECODE_BRIEF.md   # status field only
    must_not_touch:
      - platform/python-sidecar/pipeline/orchestrator/core/**   # FROZEN (§N.2) — HALT if change needed
      - 00_ARCHITECTURE/llm_consumption_audit/deliverables/findings.jsonl
      - 00_ARCHITECTURE/llm_consumption_audit/state/**
      - 00_ARCHITECTURE/llm_consumption_audit/LLM_CONSUMPTION_AUDIT_v1_0.md
      - 00_ARCHITECTURE/llm_consumption_audit/GATE_RATIFICATION_v1_0.md
      - CLAUDE.md
      - 01_FACTS_LAYER/**
      - "eval battery grading criteria (any file)"
  red_team_due: false   # W0 is campaign session 1; W4 re-audit IS the program's red-team (plan §M cadence at wave closes)
  notes: >
    Conductor kickoff. Brief flipped ACTIVE by native (2026-07-12). Scope inherited verbatim
    from CLAUDECODE_BRIEF.md frontmatter. §8.6 HALT conditions armed. Deploy authority standing
    per §8.5. Non-interactive session: claude.ai MCP connector unavailable → deployed-channel
    verification uses HTTP path (see §1b).
```

**Session 1 work log:**
- [x] Read order (brief §2) items 1–4 complete; WP-0.1 normative text (v2 §5 Wave 0) read.
- [x] Self-provisioning probes recorded (§1).
- [x] Run ledger created (this file).
- [ ] W0 = WP-0.1 execution (delegated implementation in worktree → blind security/entitlement verification).
- [ ] W0 merge + deploy + prod re-verify.
- [ ] Session close (CURRENT_STATE + SESSION_LOG).

---

## §3 — WP execution log (append-only, per WP)

### WP-0.1 — LCA-17 wrong-chart substitution (CRITICAL, entitlement-class) — E5/E7

- **Wave:** W0. **State:** OPENING.
- **Coverage (wp_coverage.jsonl):** 4 findings — F-0893 (CRITICAL), F-0902, F-0905, F-0908 (all HIGH), failure_class 7, lane lanes267.
- **Root cause (v2 §5):** nondeterministic, load-correlated cross-chart data leakage on
  `get_chart_orientation` — manifested only under concurrent different-chart calls (Lane-6 swarm),
  never in 5/5 isolated probes. Signature = a cache/session on the orientation/digest path keyed
  on something other than chart_id (candidates: `auth.ts` 60s validation cache; orientation/digest caches).
- **Fix (planned):** (a) reproduce under controlled concurrency (N workers, alternating chart_ids);
  (b) audit EVERY cache on the orientation/digest path for chart_id-inclusive keys; (c) server-side
  chart_id echo-back assertion (reject/refetch on mismatch) as defense-in-depth.
- **Deliverables:** fix + permanent concurrent-load regression test (2 charts, interleaved, N≥100
  iterations, 0 substitutions) in CI.
- **Verifier:** security/entitlement agent (§6.4) — re-runs the concurrency harness independently,
  fresh context, quoted payloads, both charts.
- **Iteration budget (§8.4):** 3 fix-iterations per failed acceptance criterion.
- **Intervention records:**
  - 2026-07-12 — Implementation lane DISPATCHED in an isolated git worktree (general-purpose
    agent). Brief: systematic-debugging (reproduce-first concurrency harness → root-cause the
    non-chart_id-keyed cache → fix + server-side chart_id echo-back assertion → permanent CI
    regression test, N≥100 interleaved, both charts). Constraints enforced in brief: FROZEN
    orchestrator HALT, no entitlement widening, read-only prod DB, conventional commits citing
    F-0893/0902/0905/0908. Status: RUNNING. Merge withheld pending blind verification.
  - 2026-07-12 — Implementation lane REPORTED. Branch `worktree-agent-a2eaa1b52a8d62cc7`
    (commits `f481592b` test, `521fbbf0` fix; NOT merged). **Root cause (verified):** shared
    module-level cache `platform/src/lib/retrieval/cache.ts` (`_cache` Map) built keys with a
    weak 32-bit rolling hash (`_hash`) → distinct chart_ids whose arg objects hash-collide
    collapse to one cache key → concurrent chart-B request reads chart-A payload. Load-correlated;
    absent in isolated probes → matches LCA-17 signature. `auth.ts` 60s cache RULED OUT. **Fix:**
    `_hash`→SHA-256 over key-sorted serialization (also protects `query_signals`); + echo-back
    guard in `query_ucd.ts` (discard/recompute on chart_id mismatch, hard-error on invariant fail).
    New tests picked up by `npm test`→vitest in CI. Gate: tsc 0, eslint clean, 5278 pass/0 fail.
    Repro used 2 synthetic colliding real-v4-UUIDs (deployed channel unavailable in-session). No HALT.
- **Verification verdict:** ✅ **CONFIRMED-FIXED** (blind security/entitlement verifier, fresh context,
  2026-07-12). Independent re-derivation reproduced the collision (old hash: 60/120 substitutions;
  new: 0 over **2,000,000** iterations, 0 brute-force collisions). Enumerated EVERY cache on the
  orientation/digest/ranking path — no residual weak-keyed chart cache; `auth.ts` independently
  confirmed to hold no chart data. Echo-back guard fails closed vs 8 adversarial payloads (no bypass).
  Zero entitlement regression (4 files, no auth surface). Non-blocking obs: `query_signals.ts` shares
  the now-SHA-256-keyed cache (safe) but lacks the orientation-only echo guard → optional future
  defense-in-depth (logged, not required). Implementer+verifier AGREE → no conductor live-retest.
- **Merge / deploy record:**
  - Conductor merged fix branch → local main (--no-ff, `71eab3ea`); zero-regression gate GREEN on
    merge result: WP-0.1 9/9, R6A yoga-integrity 103 pass/2 skip.
  - Direct push to main REJECTED (branch protection: 4 required checks). Routed via PR per governance.
  - **PR #553** (`fix/wp-0.1-lca17-cross-chart-isolation`, 3 linear commits: test `b160ca7e`, fix
    `6ddd64c2`, ledger `1e63ef55`). CI in flight; merge → deploy pending green checks.
  - **PR #553 MERGED** (squash `6ec244c0`, branch deleted). Deploy `29179433487` GREEN → changed-path
    detection built **amjis-web only** (fix is in the retrieval lib served by amjis-web `/api/mcp/execute`;
    amjis-mcp is the thin IAM-front and was unchanged — correct).
  - ✅ **W0 prod-verify (Option-1, native-ratified 2026-07-12):** (1) in-process blind proof — 2M iters,
    0 substitutions; (2) **deploy image-SHA parity** — `amjis-web:6ec244c0` == main HEAD; (3) health —
    revision `amjis-web-00955-qt5` Ready=True, 100% traffic. **Deferred residual (disclosed):** full
    LIVE deployed-channel interleaved-concurrency probe (needs native-authorized connector / issued MCP
    key) — recorded for a connector-authorized session; NOT a blocker per native ruling.
  - **W0 ACCEPTANCE: MET.** LCA-17 findings F-0893/0902/0905/0908 → REMEDIATED-PENDING-W4.

---

### W1 — Serving plane (7 lanes; collision-safe batches, conductor-merged between batches)

**Batch strategy (conductor):** WP-1.2/1.3/1.5/1.8 all touch the shared ranking/serving/envelope layer →
NOT run all-at-once (merge-conflict + verify risk). Executed in collision-safe batches, rebasing each
batch on the prior merge. WP-1.6 LAST (depends on 1.2/1.3/1.4/1.5 reachability). Live deployed-channel
verification now available (§1b.2) — each lane verified on the real channel before merge.

**Deploy-cadence mechanics (conductor decision — reconciles §7.3 "merge per WP" with §7.4 "deploy per wave"):**
main-merge auto-deploys, so per-WP merges to main would deploy mid-wave, violating the ratified per-wave
cadence. Resolution: verified W1 WPs merge into **`integration/w1-serving-plane`** (non-main → no deploy),
accumulating + resolving cross-WP conflicts there. At W1 CLOSE: single PR integration→main → CI → one deploy
→ full W1 acceptance suite prod-verify. Faithful to native's ratified per-wave deploy; not a scope/contract
change (no HALT). Same pattern will apply to W2.

**W1 NATIVE DIRECTIVES (binding, 2026-07-12 — issued at W1-resume):**
- **[ND-W1.1] WP-1.3 coverage reconciliation (binding gate):** at WP-1.3 CLOSE, mechanically diff the UNION of
  sub-lanes a–i's claimed finding IDs against the full WP-1.3 slice of `deliverables/wp_coverage.jsonl` (**295
  findings**). Every ID must be verified-fixed OR explicitly re-dispositioned WITH reason. **WP-1.3 does not
  close with an unreconciled remainder** — the diff result is written into this ledger.
- **[ND-W1.2] WP-1.2β closes the rubric loop IN-WAVE (not deferred to W4):** β must include the Lane-6
  **rubric-7.4 raw-metric re-run** across ALL **16 ranked surfaces**, both charts, **E-2 discipline** (raw
  values always, no silent thresholds). **Acceptance:** 0% UNATTRIBUTED; wealth∩relationship top-20 overlap
  **≤25%** with inline rationale.
- **[ND-W1.3] Fold ledger follow-ups in-wave (don't carry silently):** **F-WP17-1** (multi-school bundle
  re-bridge) + the **contract-surface phantom tool declarations** (kp_query/query_kp_ruling_planets/
  timeline_query in tool_metadata/contract_bridge/retrieval_capability_spec) belong to W1 serving scope → fold
  into **WP-1.3h** (dead-registry/help-honesty) or a **WP-1.7 follow-through**; verify like any intervention.
  R-45 stays with WP-2.1 (unchanged).
- **[ND-W1.4] Expected external check post-W1-deploy:** after the W1 deploy, the native will run an independent
  Cowork-side live probe (attribution populated, domains diverging). Note as an expected external verification
  complementing the verifier-agent prod-verify.

- **Batch A (dispatched 2026-07-12, parallel, disjoint scopes):**
  - **WP-1.1** (LCA-2 consult resurrection, CRITICAL; cov 7) — scope `app/api/consult/**`. Re-point consult
    off retired `reports` table → live retrieval surfaces; stop mislabeling permanent errors as retry-class;
    consult smoke matrix (both charts × orientation/domain/timing). Verifiers: serving-wire + jyotish-domain.
    Status: **IMPL REPORTED** → branch `worktree-agent-abcd7900cabe6c120` (commit `2476af6f`). Root cause:
    `app/api/chat/consult/route.ts` (real path — brief said `api/consult/`) unconditionally `SELECT ... FROM
    reports` (relation absent, `to_regclass` NULL; DDL only in migrations/_archive); `reportsResult` declared
    but NEVER consumed → pure dead weight killing the surface; error mapped to SYSTEM_DB_UNAVAILABLE{retry:true}
    (permanent 42P01 mislabeled transient). Fix: removed dead query; `isPermanentSchemaError()` (SQLSTATE 42/3F)
    → 500 non-retryable, transient → 503 retryable; smoke matrix BEFORE 8/9 fail → AFTER 9/9 pass; tsc 0, eslint
    clean, chat suite 45/45. **Adjacent same-defect surface found + FOLDED IN (conductor decision):** consult
    PAGE server components (`clients/[id]/consult/page.tsx` L111, `.../[conversationId]/page.tsx` L46) have the
    identical `SELECT * FROM reports` crash → agent RESUMED to none-safe them (complete LCA-2 resurrection).
    **Page fix DONE** (commit `5a31265a`): both pages none-safed to empty (consumed downstream), tests 47/47,
    grep confirms ZERO live `FROM reports` across route+pages. **Blind verifier DISPATCHED** (serving-wire +
    jyotish-domain, uses live `marsys-jis-direct` channel + chart_facts ground-truth).
    ✅ **VERDICT: CONFIRMED-FIXED** — no residual `reports` reads (independent grep); error mapping honest
    (verified vs `errors.ts`: 42*/3F*→500 non-retry, 57/40/08→503 retry); live content non-blank + chart-DISTINCT
    both charts (native 13,364 sig / Saturn exalted Libra 7H; Abhinandan 13,369 / Venus D1-exalted); jyotish
    sanity PASS (Lagna Aries, Moon Purva Bhadrapada — FORENSIC anchors); scope clean (5 files). Non-blocking:
    `get_temporal_windows`=0 activations = **R-45** (NULL activation dates, owned by WP-2.1/W2), independently
    rediscovered — not a consult regression. **MERGED → `integration/w1-serving-plane` (`9953d317`)**; consult
    suite 47/47 on merge result. **WP-1.1 COMPLETE.**
  - **WP-1.2** (LCA-14/R-44/KP-4 serving-half; cov 79, 5 CRIT) — **first attempt STALLED** (infra watchdog,
    600s no-progress on an unbounded prod-data investigation; 0 commits). WP too broad for one lane →
    **SPLIT**:
    - **WP-1.2α** (parts a,d,e — attribution ledger + serving salience demotion + get_domain_reading text
      hydration): **IMPL REPORTED** → branch `worktree-agent-a546707adf1103476` (commit `e3438658`). Killed
      UNATTRIBUTED dominance (top entity now SATURN; UNATTRIBUTED forced last — root: graha_dignity_per_varga
      signals lacked configuration_jsonb.graha, now attributed via fact_subject); grounding.fact_ids []→51
      surfaced/298 resolved (§N.5 proof: sample resolves to chart_facts D1_SAT); descriptive+per-varga demoted
      from major/chart_defining (disclosed on-row `signature_tier_demoted_from`, rows kept); get_domain_reading
      refs carry headline+summary. Files incl. new `salience_demotion.ts` + `platform-mcp/registry_bridge.ts`
      (envelope grounding — so W1 deploy rebuilds BOTH amjis-web + amjis-mcp). 21 unit + 8 live-DB tests (both
      charts), tsc 0, eslint clean, 87 L2 tests. **Blind verifier DISPATCHED** (serving-wire + jyotish sanity;
      adversarial §N.5 resolution + attribution-correctness + false-demotion hunt).
      ✅ **VERDICT: CONFIRMED-FIXED** — verifier independently resolved surfaced fact_ids (51/51 native, 52/52
      Abhinandan) vs chart_facts; proved orphan ids (27/325 native) CANNOT leak (genuine §N.5 gate); attribution
      correct incl. adversarial cross-graha (`D54_SAT`→SATURN not RAHU); UNATTRIBUTED-last holds live; ZERO false
      demotion of genuine chart_defining (native kept 18, Abhinandan 17); hydration 200/200 real text; scope clean
      (cache.ts empty diff — WP-0.1 intact); tsc 0 both projects, ranking 21/21, L2 82pass/19skip. Broke the one
      circularity risk with an independent predicate (LEAKS=0 holds). **MERGED → integration (`1dce804a`)**;
      zero-regression gate 148 pass/19 skip. **WP-1.2α COMPLETE.**
    - **WP-1.2β** (parts b,c — domain discrimination + new/corrected domains: moksha 4-8-12+Ketu,
      education/vidya, character/buddhi, bhava→domain un-collapse): doctrine-heavy → deferred to **Batch B**.
      Verifier: jyotish-domain. Status: QUEUED.
  - Live ground-truth captured pre-batch (§1b.2): UNATTRIBUTED @64.6/84.8, grounding.fact_ids=[], trivia@major.
- **Batch B1 (dispatched 2026-07-12, parallel from integration branch, disjoint scopes):**
  - **WP-1.2β** — domain discrimination (wealth≠relationship) + new domains (moksha 4-8-12+Ketu, education/vidya
    off bhava-4-mislabel F-0756, character/buddhi in judgment_query, bhava→domain un-collapse) + finish
    attribution to **0% UNATTRIBUTED** (ND-W1.2). Acceptance: 0% UNATTRIBUTED + wealth∩relationship top-20 ≤25%.
    Verifier runs rubric-7.4 raw-metric re-run × 16 surfaces × both charts (E-2). **IMPL REPORTED** → branch
    `worktree-agent-a9994fa38bac2633b` (commit `151f94d7`; STEP-0 on integration, WP-1.2α built-upon). Claims:
    wealth∩relationship top-20 overlap ~95%→**5% native / 10% Abhinandan** (≤25% ✅); **0 UNATTRIBUTED served**
    both charts (residual 3 native/2 Abhinandan truly-unattributable panchanga descriptors DISCLOSED); moksha=
    4-8-12+Ketu (not bhava-9), education/vidya=4/5/2/9+Merc/Jup/Ketu, character/buddhi=bhava-1+Moon/Merc, F-0756
    corrected (bhava-4→home/residence); BPHS-cited. 15 unit + 10 live-DB tests, 155/155 regression, tsc 0. Files:
    priors_config, composite_ranker, query_ucd, query_domain_reading, register_d9_judgment (+2 tests). **Blind
    jyotish+serving-wire verifier DISPATCHED** — rubric-7.4 raw × surfaces × both charts + independent overlap
    recompute + OVER-FIT hunt + classical-soundness grade of new domains.
    ✅ **VERDICT: CONFIRMED-FIXED** — verifier wrote its OWN harness + computed every metric independently:
    wealth∩relationship overlap **5% native / 10% Abhinandan** (≤25% ✅, own computation); **0 served UNATTRIBUTED**
    both charts (residual 3/2 truly-unattributable, disclosed); **NOT over-fit** (re-rank via soft ×0.7 bhava
    demotion, never strip — full n=20, shared factors survive); doctrine SOUND (moksha 12/8/4 not 9th; education
    2/4/5/9; F-0756 bhava-4→residence; character/buddhi bhava-1+Moon/Merc); §N.5 honored (serve-time, 0 stored
    mutation); WP-1.2α + cache.ts + consult untouched; tsc 0, 86 unit + 24 integration pass. **MERGED →
    integration (`97d6fe9c`)**. **WP-1.2 COMPLETE (α+β).** Observations logged §4.
  - **WP-1.3-dasha** (sub-lanes b,c) — `query_dasha_periods` honors `system_id` (F-0354, ~437k dark rows) +
    dasha tools honor requested windows (F-0471/0485). **IMPL REPORTED** → branch `worktree-agent-a6c2d1f024908ca70`
    (commit `093c804d`; STEP-0 on integration). Root cause deeper: DB `get_dashas` ignored `system_id`; AND the
    audit-named MCP tools were separate PyJHora vimshottari-only sidecar surfaces → repointed both to faceted DB
    alias (retired PyJHora reg). 8 systems in data (chara_karaka 299k/mudda 202k/yogini 165k/vimshottari 95k/
    kalachakra 69k/ashtottari 66k/naisargika 43k/vimshottari_kp 12k); historical+future windows honored+echoed
    (`facets_applied`). 14/14 integration tests, 68/68 platform-mcp routing, tsc clean. Discloses 97 pre-existing
    platform-mcp baseline failures (claims identical stashed — verifier to confirm). Touches platform-mcp
    (server/aliases/pyhora) → W1 deploy rebuilds amjis-mcp too. **Blind verifier DISPATCHED** (data-plane
    per-system + window + MCP-repoint-no-orphan + adversarial 97-baseline reproduction).
    ✅ **VERDICT: CONFIRMED-FIXED** — 8 systems / 437,178 dark rows confirmed; each non-vimshottari system returns
    only its own rows (count DISTINCT system_id=1); windows era-distinct (hist Saturn→Mercury, future Ketu→Venus)
    + honest-empty out-of-range; MCP repoint no orphaned consumer (internal callers use platform HTTP→DB path);
    **97 platform-mcp failures INDEPENDENTLY REPRODUCED at HEAD~1 (byte-identical test-name sets — no green→red)**;
    scope clean, tsc 0 both packages. **MERGED → integration (`1764d2b1`)**, tsc clean both packages.
    **WP-1.3(b,c) COMPLETE.** Cleanup-debt logged §4.
  - **WP-1.3-params** (sub-lanes d,g) — `lel_query` serves 57 life events (F-L10-021, unblocks L5 calib) +
    `msr_sql` honors projection param (LCA-7, fixed 17/115 cols). **IMPL REPORTED** → branch
    `worktree-agent-ac27807557af5bb37` (commits `e192c2cf` lel, `253fd7da` msr_sql; STEP-0 merge on integration
    confirmed). (d) lel_query WAS pointed at query_signals `lel_origin=true` (0 rows) → new `L5/lel_query`
    capability over `life_events`, serves 57 native / 0 Abhinandan, entitlement gate preserved. (g) msr_sql
    fixed-17-col → `projection` param (omit=17, `*`=all **82 real cols**, explicit list); injection-safe via
    static whitelist validated pre-SQL. 12 new tests, 669 regression pass, tsc 0, WP-1.7 invariant green.
    ✅ **VERDICT: CONFIRMED-FIXED** — verifier independently confirmed lel table counts (57 native / 0 Abhinandan
    TRUE zero, not entitlement mask), entitlement preserved (per_chart authorizeChartAccess, no widening),
    msr_sql injection-safe (all bypass payloads rejected pre-SQL, DB untouched), 82 real cols (omit=17/*=all/
    explicit), scope clean (WP-1.2α+1.7 intact). **MERGED → integration (`22816856`)**; regression 89 pass.
    **WP-1.3(d,g) COMPLETE.**
  - **⚠ Batch B1 INTERRUPTED by session restart (2026-07-12)** — all 3 lanes stopped/killed before landing;
    isolation-worktrees had branched from `main` (d19a7fce) NOT integration, and made only tiny uncommitted
    partials (dasha ~56 lines, params stub). Discarded all 3; **RELAUNCHED** with mandatory STEP-0
    (`git merge origin/integration/w1-serving-plane`) so each bases on the integrated WP-1.1/1.2α/1.7 and merges
    back cleanly. **Lesson:** `Agent isolation:worktree` branches from main, not current HEAD → future lanes
    needing prior-wave work must merge integration as step 0. Relaunched RUNNING.
- **Batch B2 (IN PROGRESS):** WP-1.3 (a) 23 computed-but-unserved assets, (e) temporal windows serving,
  (f) query_chart_facts filters+pagination+6 ayanamshas, (h) dead-registry purge + help + **F-WP17-1 +
  contract-surface phantoms + F-WP13dasha-cleanup folded in** (ND-W1.3), (i) apex/assess dedup + R-40.
  **B2a status:** ✅ **WP-1.3(f) MERGED** (`15710eb6`). ✅ **WP-1.3(a) CONFIRMED-FIXED + MERGED** (`45a27834`;
  13 assets real data table-counted, kala_taranga budgeted/drill-refuses, §N.5 resolves, disposition HONEST
  adversarially, whitelist +13 green, entitlement enforced; native cgm_motifs=0 = known LCA-6/WP-2.2). WP-1.3(i)
  [apex/assess dedup + verdict_skeleton serving fixes + PENDING-W3 temporal] IMPL DONE, **blind verifier RUNNING**.
  ✅ **WP-1.3(i) CONFIRMED-FIXED + MERGED** (`efc9ba52`; apex/assess dedup restores params, lord bucket 0→42
  parivartana, starvation fixed, PENDING-W3 temporal honest [kala_activation native 0/13364 dated], m8 failures
  reproduced pre-existing; auto-merged clean with (f) on shared platform-mcp files, tsc 0 both, 9/9 cross-lane).
  **B2a COMPLETE (a,f,i all integrated).**
- **Batch B2b (dispatched):** WP-1.3(e) temporal-windows serving (honor+echo date params; **SERVING HALF ONLY →
  acceptance PENDING-W3** with WP-2.1 writer fix) + WP-1.3(h) cleanup lane (LCA-12 dead-tool purge + help regen +
  F-WP17-1 multi-school re-bridge + contract-surface phantom decls + F-WP13-testcleanup m8 counts). Disjoint (kala
  tool vs registry/contract). Both STEP-0 on integration (`efc9ba52`).
  **WP-1.3(e) IMPL REPORTED** → branch `worktree-agent-ad12eb863deed719a` (`78a42d1a`). R-18 already fixed date
  naming; (e) added `as_of` point-in-time + always-present `date_filter` echo + honest-empty `empty_reason`/
  `awaiting_activation_dates`. Abhinandan 84 dated rows genuinely partition (64+20=84, as_of hit); native honest-empty
  + PENDING-W3 disclosed (0/13364 dated, R-45→WP-2.1). 7/7 + r6_3a 13/13, tsc 0 both. **Blind verifier DISPATCHED**
  (real-data filter + no-faked-dates adversarial + serving-half-only). **RESULT = PENDING-W3** (full acceptance
  post-W3). (h) still RUNNING. **(e)↔(h) may share platform-mcp registry_bridge/register_p1_aliases → conflict-resolve.**
  - **⚠ WP-1.3(e) DEFECT CAUGHT (verification working):** blind verifier flagged + conductor confirmed against prod
    that the `as_of` point-in-time returns **0** for real in-window instants (impl claimed "as_of=1964-01-21→20";
    ground truth `activation_start<=X AND activation_end>=X`=0, and 0 even for a row's own activation_peak_date →
    date/timestamp coercion bug, not "no match"). Range-filter part verified OK (in_range 1964-70=20). **NOT MERGED**
    — bounced to (e) implementer to root-cause the date/TZ boundary + provide HONEST real-data as_of evidence. Range
    behavior stays. §8.4 iteration budget: fix-iter 1/3.
  - **WP-1.3(h) IMPL REPORTED** (after 2 stalls, resumed) → branch `worktree-agent-a5982af08b088b061` (`a35dd569`).
    LCA-12: `capabilities.ts`/`school_conventions.ts` no longer falsely advertise cross_school/multi_school as Active
    (→PARKED/Degraded); server-count already done by (i), whitelist purge by (1.7). Phantoms dropped: kp_query,
    query_kp_ruling_planets, timeline_query (no engine backing). m8_e2e: G12 45→57, V6 12→25, dangling ref scrubbed
    → green. whitelist invariant GREEN. 96 + 41pass/4skip, tsc clean. Disjoint from (e) on platform-mcp.
    **🅿 F-WP17-1 → PARKED `parked_pending_native_review`:** `multi_school_signal_lookup` is a WS-0 stub (no backing;
    `school_signal_coverage`/`l25_msr_signals` dropped, never repopulated — WS-2 work); `cross_school_lookup` now
    short-circuits with disclosed parked error (ends silent `errored:true`). **SURFACE TO NATIVE AT W1 CLOSE.**
    ✅ **VERDICT: CONFIRMED (substance) — MERGED** (`bb8610ea`). Blind verifier confirmed all substance (phantoms
    unbacked + NO live consumer, multi_school park honest+disclosed, help-text accurate, m8 counts real 25/57,
    whitelist 50/50 green, scope clean, tsc 0). Verifier returned NOT-MET ONLY on a stale in-scope test
    (`retrieval_capability_spec.test.ts` still asserted a removed phantom + a phantom-padded count bound) →
    **conductor-fixed** (dropped stale assertion + `not.toContain` + relaxed count floor to ≥50; verified spec
    source has 0 phantom `tool_name` entries, 55 entries). tsc 0 both + m8 green on merge result.
  **✅ WP-1.3 COMPLETE — all sub-lanes a,b,c,d,e,f,g,h,i verified + integrated (11 W1 lane merges total).**
  **✅ ND-W1.1 295-ID reconciliation gate: PASS — 0 unreconciled** (`WP13_RECONCILIATION_v1_0.md`, full 295-row
  table). Dispositions: **96 REMEDIATED-PENDING-W4** (this wave — a:40, WP-1.2β sib:26, i:14, b/c:8, d:5,
  WP-1.2α/β sib:2, f:1); **131 PENDING-W2** (writer-gap/data-plane — not serving fixes; the WP-1.3 slice is
  data-plane-dominated); **44 PENDING-W3** (temporal, awaiting WP-2.1 R-45 writer); **23 W1-FOLLOWUP** (genuine
  serving residuals — see below); **1 PARKED** (multi_school). **Honest posture: PASS = fully accounted, NOT
  all-fixed** (96/295 verifier-confirmed this wave; 199 parked with per-ID reasons).
  - **23 W1-FOLLOWUP (surface to native — SERVE-default decision):** includes ~populated-but-unserved BODHA
    assets with REAL rows + no writer needed (bodha_discoveries/pratijna/question_lenses/rm_prescriptions/
    resonances) → serve-able NOW; plus (a) NEXT-PASS live-compute wrappers (ka_dasha_kala, ka_gochara),
    serving-bugs (ph_pratikara/ph_rectification), kala_jivana_parva, no-vidya-apex synthesis gap. **Candidate:
    a small W1 follow-up serving lane (SERVE-default) OR fold into WP-1.4.** Native decision at checkpoint.
  **B2 BINDING REMINDERS (native, 2026-07-12):**
  - **(a) §7.3 disposition per asset:** SERVE (with budget discipline) = DEFAULT; PARK only behind a genuine
    design question → flag `parked_pending_native_review` + reason IN LEDGER; silent drops + autonomous
    retirement FORBIDDEN. **Full 23-asset disposition table goes in this ledger.**
  - **(f):** all 6 ayanamshas served; filters GENUINELY filter (prove with **byte-size deltas**); disclosed
    pagination with REAL totals over the **5,566 subjects**.
  - **(e):** SERVING HALF ONLY — honor+echo date params; **full acceptance re-runs post-W3 with WP-2.1's writer
    fix → mark PENDING-W3, NOT done.**
  - **(h):** folds F-WP17-1 (multi-school re-bridge) + contract-surface phantoms (kp_query/query_kp_ruling_planets/
    timeline_query) + F-WP13dasha-cleanup (m8_e2e_proof dangling ref).
- **After B2:** WP-1.5 envelope contract → **WP-1.8 (ONLY after WP-1.5 lands R-38 fix — varga rows must exist to
  weigh)** → WP-1.4 synthesis design+skeleton → **WP-1.6 LAST** (capability map + served consumption protocol
  regenerated against POST-B2 reachability; verification = 3 live demand-side sessions narrow/medium/broad).
- **W1 CLOSE ORDER (native-fixed):** ND-W1.1 295-ID reconciliation (mechanical diff vs wp_coverage WP-1.3 slice,
  result in ledger) → integration→main PR → checks green → merge → **single deploy (web+mcp)** → live
  prod-verify FULL W1 acceptance suite on deployed channel → governance close (CURRENT_STATE, SESSION_LOG,
  ledger) → checkpoint at W1/W2 + **notify native for external Cowork probe (ND-W1.4)**.
- **WP-1.3 CLOSE gate (ND-W1.1, binding):** union of a–i claimed finding IDs diffed vs 295-finding wp_coverage
  slice; every ID verified-fixed or re-dispositioned-with-reason; diff written here. No unreconciled remainder.
- **Batch C:** WP-1.4 (synthesis design+skeleton) PENDING; **WP-1.7** (bench + CI whitelist invariant) —
  **IMPL REPORTED** → branch `worktree-agent-ac8af34c82e2bb7aa` (commit `75818fc0`, pushed to origin). 19 dead
  whitelist entries: **5 REGISTERED** (cgm_graph_walk→L2/traverse_chart_graph, contradiction_register,
  temporal→L3, query_tara_balam/query_chandra_balam→L1/get_tara_chandra_bala), **14 REMOVED** (no backing cap;
  500→clean 400; whitelist 48→34). **Permanent CI invariant** `whitelist_resolution_invariant.test.ts` + named
  ci.yml gate, mutation-proven (remove URI→3 fails). jhora venv-provisioned, api-key wired, ephemeris honesty
  (empty→ok:false/conf:none), port 8001→8000. **Honest partial:** `DATABASE_URL` bench needs local Postgres
  (documented follow-up). **Follow-up F-WP17-1:** `multi_school_signal_lookup` legacy impl never bridged. 121
  targeted + 907+58 broad tests pass, tsc clean. **Blind infra verifier DISPATCHED** (adversarial focus: do the
  14 removals drop any live-reachable tool? + 5-registration correctness + CI mutation + ephemeris honesty).
  ✅ **VERDICT: CONFIRMED-FIXED** — all 14 removals independently verified SAFE (0 backing cap each; the one
  live consumer `cross_school_lookup`/multi_school_bundle was ALREADY dead → 500→400 functionally neutral);
  5 registrations correct-target (descriptors match semantics); CI invariant runs (37) + independently
  mutation-proven (2 fails on bogus URI) + gated in ci.yml:67; ephemeris honest; scope clean (8 files, no
  ranking/consult/cache/orchestrator). **MERGED → integration (`b819eead`)**; regression 103 pass.
  **WP-1.7 COMPLETE.** Follow-ups logged (§4).
- **W1 close:** WP-1.6 (capability map) LAST → merge wave → deploy → live prod-verify full W1 suite.

---

## §4 — HALT / disagreement register + follow-ups (append-only)

**HALTs / disagreements:** none yet.

**Follow-ups surfaced during W1 (not blockers; carry to W4 / doctrine campaign / register):**
- **F-WP17-1** (from WP-1.7): `multi_school_signal_lookup` / `cross_school_lookup` legacy `lib/tools` impl was never bridged to the registry → its deployed consumer `platform-mcp/src/bundles/multi_school_bundle.ts` degrades gracefully (`errored:true`). Prioritize re-bridging if multi-school convergence data is expected. Owner: W1 residual → consider WP-1.3 or a follow-up lane.
- **Contract-surface phantom declarations** (from WP-1.7 verifier): `kp_query`, `query_kp_ruling_planets`, `timeline_query` remain declared in the untouched CONTRACT/router surface (`tool_metadata.ts`, `contract_bridge.ts`, `retrieval_capability_spec.ts`) with no engine backing. Out of WP-1.7 scope; future contract-surface reconciliation should implement or drop them (same phantom-declaration bug class). Candidate: W4 re-grade / doctrine campaign.
- **R-45** (rediscovered by WP-1.1 verifier): `get_temporal_windows` = 0 activations (NULL activation dates) — already owned by **WP-2.1** (W2).
- **⭐ F-DATE-TZ (from WP-1.3(e) — HIGH priority for WP-1.5):** Postgres `date` columns returned raw are parsed by node-postgres at IST-midnight → serialized to UTC → **off-by-one + spurious time component** (`1964-01-22` → `"1964-01-21T18:30:00Z"`), breaking any date round-trip. WP-1.3(e) fixed its own tool via `to_char(col,'YYYY-MM-DD')` + `::date` param binding. **Sibling L3 serving tools share the SAME trap and are NOT yet fixed — including some just merged in WP-1.3(a): `query_dasha_dossier`, `query_temporal_view`, `query_convergence_windows`, plus `query_projections`, `call_service_wrappers`.** → **WP-1.5 (envelope honesty) must apply the `to_char` treatment program-wide to every served `date` column.** Latent correctness bug in already-integrated tools until then.
- **F-WP13-testcleanup** (WP-1.3h scope, from dasha + apex/assess verifiers): `platform-mcp/src/tools/__tests__/m8_e2e_proof.test.ts` has (a) L519 dangling ref to retired `registerQueryDashaPeriodsTool`; (b) stale count constants — G12 `REGISTERED_TOOL_COUNT=45` and V6 D7-bridge `=12` — now wrong because multiple integrated lanes added/removed registry tools (WP-1.3 a/f/i/dasha). All red-both-ways (in the pre-existing baseline, NOT regressions). **WP-1.3h** must reconcile these count constants to the post-B2 actuals + scrub the dangling ref. Per ND-W1.3.
- **OBS-W12b-1** (from WP-1.2β verifier, non-blocking): native `query_ucd` now serves only **3 entity_profiles (all graha, Saturn-dominated)** vs Abhinandan's 15 (graha+bhava) — a consequence of `sade_sati→SATURN` attribution concentration meeting the native's Saturn-heavy top-300 pool (297/300 → ~3 grahas). Pre-existing pool logic, NOT a WP-1.2β regression; UNATTRIBUTED=0 holds. But a 3-entity native orientation is thin for acharya-grade whole-chart read → candidate refinement for **WP-1.4** (synthesis) or a follow-up (entity-profile diversity / pool balancing). Re-check at W4.
- **OBS-W12b-2** (non-blocking): moksha∩education top-20 overlap ~50-55% (both new whole-chart-pool domains overlay house-4). Not a gate (binding gate = wealth∩relationship only); acceptable, but the least-separated domain pair — revisit if a moksha-vs-education discrimination need arises.

---

---

## §5 — WP-1.3(a) computed-but-unserved disposition table (native §7.3 requirement)

Branch `worktree-agent-a2f0770448dc49ab4` (`a30a8b0f`), verification pending. Ground-truth = bounded prod
`COUNT(*)` per chart (A=native `482012f1`, B=Abhinandan `1c826d5a`). **No silent drops, no autonomous retirements.**

| Finding | Asset | Disposition | Surface / reason | rows A/B | Budget |
|---|---|---|---|---|---|
| F-L10-001 | ga_medical | SERVE | `get_medical_indications` (new L1) | 45/45 | LIMIT 50 + total |
| F-L10-002 | ga_vastu_planet_direction_map | SERVE | `get_vastu_directions` (new L1) | 40/40 | LIMIT 50 + total |
| F-L10-003 | ga_yoga_firings | SERVE | `get_yoga_firings` (new L1) | 50/56 | LIMIT 50 + total |
| F-L10-004 | bodha_cdlm_chart_summary | SERVE | `query_cdlm_summary` (new L2) | 5/5 | LIMIT 50 |
| F-L10-005 | bodha_cgm_motifs | SERVE | `query_cgm_motifs` (new L2) | 0/6 | LIMIT 50 |
| F-L10-006 | bodha_cgm_paths | SERVE | `query_cgm_paths` (new L2) | 45/45 | LIMIT 50 |
| F-L10-007 | bo_chart_gestalt | SERVE | `query_chart_gestalt` (new L2) | 5/5 | LIMIT 50 |
| F-L10-009 | ka_avadhi | SERVE | `query_dasha_dossier` (new L3) | 1571/1585 | LIMIT 50 + filters |
| F-L10-012 | ka_kala_darshana | SERVE | `query_temporal_view` (un-stubbed) | 750/750 | LIMIT 50 |
| F-L10-014 | ka_sangam rigor | SERVE | `query_convergence_windows` (whitelist-exposed) | 6484/2959 | existing cap |
| F-L10-015 | ka_taranga | SERVE | `query_activation_waveform` (new L3) | 79728/79728 | **aggregate default; drill errors w/o scope — never dumps 79k** |
| F-L10-018 | ka_vighnakara | SERVE | `query_obstruction_periods` (un-stubbed) | 602/638 | LIMIT 50 |
| F-L10-027 | ph_sankrama | SERVE | `query_spillover_cascades` (whitelist-exposed) | 635/1265 | existing cap |
| F-L10-021 | lel_events | DONE(sibling) | WP-1.3(d) `lel_query` | 57/0 | — |
| F-L10-017 | ka_tulana (UNATTRIB) | OUT-OF-SCOPE | ranking defect → WP-1.2 (done) | — | — |
| F-L10-010 | ka_dasha_kala | NEXT-PASS | live-compute wrapper (dasha-adjacent) | — | — |
| F-L10-011 | ka_gochara | NEXT-PASS | live transit search (sidecar) | — | — |
| F-L10-013 | ka_kalasutra | NEXT-PASS | overlaps WP-1.3(e) windows | 66836/66747 | — |
| F-L10-016 | ka_tulana compare | **PARK** `parked_pending_native_review` | two-chart compare — no single-chart table; genuine DESIGN question | — | — |
| F-L10-020 | ka_yojaka predicates | NEXT-PASS | overlaps WP-1.3(e) windows-engine | 66836/66747 | — |
| F-L10-024 | ph_pratikara (mitigation=0) | NEXT-PASS(serving-bug) | rows EXIST (602/638) — existing tool returns empty; needs serving fix | 602/638 | — |
| F-L10-025 | ph_rectification (empty/185) | NEXT-PASS(serving-bug) | rows EXIST (185) — serving fix | 185/185 | — |
| F-L10-008 | bo_sangati | **PENDING-W2** | 0 rows — writer never wrote (WP-2.2 empty shell) | 0 | — |
| F-L10-019 | ka_yojaka date-less | **PENDING-W2** | activation_start NULL 66726/66836 — writer defect (WP-2.1 R-45) | data | — |
| F-L10-022 | mi_abhilekha | **PENDING-W2** | mimamsa_journal empty (WP-2.2/L5) | 0/0 | — |
| F-L10-023 | ph_phaladesa | **PENDING-W2** | narration_status=pending, prose empty (WP-2.2) | 7/7 empty | — |
| F-L10-026 | ph_rectification non-discrim | **PENDING-W2** | scorer/algo defect (0/36 events) — writer/L5, not serving | algo | — |

**Conductor reconciliation note (for ND-W1.1 at WP-1.3 close):** the implementer labeled several items "PARK" whose real reason is a W2 writer gap → reclassified above as **PENDING-W2** (they get data in W2; only ka_tulana-compare is a true `parked_pending_native_review` design question). The 4 NEXT-PASS + 2 serving-bug items are genuine WP-1.3 residuals needing a follow-up lane or explicit re-disposition at the 295-ID reconciliation gate — none dropped.

---

*Ledger opened 2026-07-12 by the Program Conductor. Append-only below §0's status board; §0 is the one mutable status surface.*

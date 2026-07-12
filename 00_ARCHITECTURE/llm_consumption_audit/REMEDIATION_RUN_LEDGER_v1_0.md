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
| W1 | WP-1.1/1.2/1.3(a-j)/1.4/1.5/1.6/1.7/1.8 (serving plane) | ✅ **CLOSED** (deployed web `2385fb62`+mcp `fc84cd0d`; **7/7 prod-verified**; 2026-07-13) | ✅ deployed | 16 lanes blind-verified; ND-W1.1 PASS; +316 reachable; lel_query fix-forward (ADJ-2) closed 7/7 |
| W2 | WP-2.1/2.2/2.3/2.4/2.5 (writer packages) | **IN_PROGRESS** | after W2 close | writers+JOB image live before W3; corrected DAG (§6.8) |
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

## §6 — Execution-model correction (native, 2026-07-13 — BINDING to program close)

- **CONTINUOUS RUN.** No mid-run questions/checkpoint-stops. Run W1-remainder → W1 close+deploy → W2 → W3 →
  W4 → cleanup+close continuously. The next native-facing output is the W4 close report, a §8.6 HALT report,
  or this ledger — never a question.
- **Unanticipated non-HALT decisions → ADJUDICATOR agent** (fresh context, grounded in plan §1 E-clauses +
  §7/§8 + register) decides within the rules and logs a reasoned `ADJUDICATION` ledger entry (§4) for async
  native review. Only §8.6 classes HALT (frozen contract, entitlement, out-of-scope writes, budget exhaustion).
- **Context hygiene = thin dispatcher + ledger-keeper.** Heavy work delegated to fresh-context agents
  re-grounded from ledger+plan; the ledger is durable memory; checkpoints are LEDGER ENTRIES, not questions.
- **Pre-dispatch check (mandatory, mechanical, per batch):** compute file-scope intersection of candidate lanes.
  Disjoint + no semantic dep → concurrent (all Agent calls in ONE message, separate worktrees). Shared files →
  same lane or explicit merge-order. Semantic dep → sequence. **Record the dispatch manifest + intersection
  result in this ledger per batch.**
- **Swarm verification per intervention:** blind domain-matched verifier (fresh context, original failing call
  re-executed, adversarial probes, quoted payloads, both charts). Full acceptance suite LIVE on prod after each
  wave deploy. W3 golden catches + snapshot/auto-restore. W4 E-5 swarm (≥15% re-exec, 100% CRIT/HIGH re-verified,
  PASS-row false-neg sampling) + E-6 depth gate. Verifier disagreement → conductor live retest. All verdicts here.
- **Wave closes execute in full** (reconciliation → integration→main PR → checks → merge → deploy → live
  prod-verify → governance) without waiting on a human. **W1 deploy: native runs ND-W1.4 Cowork probe async —
  DO NOT block on it.**

### §6.1 — Rulings (native, 2026-07-13)
- **Ruling 1 — WP-1.3j:** add a follow-up serving lane in W1 (NOT folded into WP-1.4). §7.3 SERVE-default: the
  serve-able-now subset — `bodha_discoveries`, `bodha_pratijna`, `question_lenses`, `rm_prescriptions`,
  `resonances`, + the `ph_pratikara`/`ph_rectification` serving-bugs — served + blind-verified THIS wave; the
  rest re-dispositioned PENDING-W2/W3 with per-ID reason. **No W1-FOLLOWUP class survives W1 close.**
- **Ruling 2 — F-WP17-1:** PARK CONFIRMED (WS-0 stub, no backing = out-of-scope new-capability; disclosed
  parked error satisfies E5). → **Deferred shelf at program close.**

### §6.3 — Dispatch manifest: W1-remainder BATCH 1 (WP-1.5 ∥ WP-1.3j)
**Pre-dispatch intersection check (mechanical):**
- **WP-1.5** scope = the SHARED envelope/response builders (`lib/mcp/epistemics.ts` buildEnvelope/pagination,
  trim/budget helpers) + program-wide receipt-honesty (true `truncated`/`total`/`more_available`, budget ceilings,
  monotonicity/type hygiene, R-38/R-41 deployed retest) + **F-DATE-TZ** `to_char` on L3 date tools
  (query_convergence_windows, query_dasha_dossier, query_temporal_view, query_projections, call_service_wrappers).
- **WP-1.3j** scope = NEW serving tools for populated-but-unserved BODHA assets (bodha_discoveries/pratijna/
  question_lenses/rm_prescriptions/resonances) + fix `ph_pratikara`(phala_mitigation)/`ph_rectification` serving-bugs.
- **Intersection:** FILE scopes largely DISJOINT (1.5=envelope builders + L3 kala date tools; 1.3j=bodha + phala
  serving tools). **Semantic dependency:** 1.3j's new tools EMIT envelopes → must conform to 1.5's contract →
  **merge-order: WP-1.5 FIRST**, then WP-1.3j rebases on merged 1.5 and its verifier re-checks envelope conformance.
- **Verdict: dispatch CONCURRENTLY (separate worktrees, one message); ordered merge (1.5→1.3j-rebased).**
**Dispatched 2026-07-13.**
- **WP-1.3j IMPL COMPLETE** → branch `worktree-agent-ae30faa5978d33e1c` (`0854a5a1`). 5 new bodha serving tools
  (discoveries 2392/1150, pratijna 110/110, question_lenses 60/60, rm_prescriptions 135/135, rm_resonances 45/45;
  honest envelopes+budget+to_char). 2 phala serving-bugs FIXED: F-L10-025 ph_rectification (handler forced
  lahiri long-form vs short codes → 0/185 → **185/185**); F-L10-024 ph_pratikara (mitigation_map read wrong
  ToolBundle key → empty → **602/638** surfaced+budgeted). **All 23 W1-FOLLOWUP dispositioned: 12 served + 11
  re-dispositioned PENDING-W2/W3 (reasons in report) → NONE survive (Ruling 1 ✓).** tsc 0 both, 732+82+66 pass,
  platform-mcp 95-fail baseline unchanged (stash-verified). **HELD for merge AFTER WP-1.5 → rebase → blind
  verifier re-checks serving-correctness + WP-1.5 envelope conformance.**
- **WP-1.5 IMPL COMPLETE** → branch `worktree-agent-a3ffd6d883826a273` (`d9b33401`). Canonical `envelope.ts`:
  `more_available` always emitted; `buildHonestPagination`+cursor make trim-lies structurally impossible.
  **F-DATE-TZ program-wide: 10 tools `to_char`'d** (L3×6, L4×3, L5 lel + register_d8/p1); remaining paths
  (phala_event_anchors sidecar; unused raw cols) flagged explicit follow-up. LCA-8 list_entities real 652
  total+cursor (was masking 552). **Correctness bug FOUND+FIXED:** `call_priority_ranking` referenced absent
  kala_activation cols → errored EVERY call → repointed. F-0963 digest `::int`. R-38/R-41 honest (registry-handler
  retest; live deployed re-run = follow-up). 12 unit+15 integration green, tsc 0 both, 166 existing pass. **Blind
  verifier DISPATCHED** (Lane-4: envelope-cant-lie invariant + F-DATE-TZ + list_entities + priority_ranking +
  R-38/R-41 + no-regression). **Merges FIRST on CONFIRMED; then rebase WP-1.3j onto it + verify conformance.**
  ✅ **WP-1.5 CONFIRMED-FIXED + MERGED** (`3150d0ee`). Envelope-can't-lie proven (fuzz 12/12); F-DATE-TZ 10 tools
  date-typed-verified; list_entities real 652; call_priority_ranking every-call-error fixed (real cols, 84 rows
  Abhinandan); R-38/R-41/F-0963 pass; tsc 0 both, prior W1 intact. Caveats (follow-up, §4): list_entities cursor
  disclosure-honest-not-consumable; native priority_ranking empty on NULL dates (WP-2.1). tsc 0 both on merge.
  ✅ **WP-1.3j REBASED onto merged integration** (`c8985bed`; 1 trivial whitespace conflict in query_phala_calibration
  to_char block — both lanes added identical to_char, resolved; tsc 0 both). **Blind verifier (serving + WP-1.5
  envelope-conformance re-check) DISPATCHED.** Merge on CONFIRMED.
  ✅ **WP-1.3j CONFIRMED-FIXED + MERGED** (`3ee2bc1d`). Verifier independently reproduced both phala bug root-causes
  + all 5 tool counts; envelope conformance holds (total=real COUNT → can't lie); all 23 W1-FOLLOWUP accounted
  (12 served + 11 fwd-homed); §N.5 572/572; no entitlement widening; tsc 0 both, wp13j 30/30, whitelist 58/58.
  **W1-remainder BATCH 1 COMPLETE (WP-1.5 + WP-1.3j).** Non-blocking notes → §4: (a) new WP-1.3j tools hand-roll
  envelope (offset, no cursor) instead of WP-1.5 `buildHonestPagination` — consistency follow-up; (b) at W1 close,
  re-stamp WP13_RECONCILIATION's 11 W1-FOLLOWUP rows → PENDING-W2/W3/PARK (Ruling 1 "no W1-FOLLOWUP survives" — met
  in substance, table column pending).

### §6.4 — Dispatch manifest: W1-remainder BATCH 2 (WP-1.8 ∥ WP-1.4)
**Pre-dispatch intersection check (mechanical):**
- **WP-1.8** scope = varga-aware verdicts + cross-path fidelity (R-43/R-46): serving-side D-1/G-7 re-derivation
  of dasha-lord dignity/shadbala (vs chart_facts, no writer/migration — HALT if writer needed), varga terms in
  the verdict formula (needs WP-1.5's R-38 varga rows — NOW MERGED), multi-formula disclosure, assess_*↔get_signals
  reconciliation. Files: judgment/verdict/assess serving + dasha-lord re-derivation.
- **WP-1.4** scope = large-N synthesis instrument DESIGN+SKELETON (P-10 intent decomp → plan vs pre-aggregated L2
  surfaces → map-reduce over families → narrative + derivation ledger). Mostly NEW files (synthesis orchestrator).
- **Intersection:** DISJOINT file scopes (1.8=verdict/assess/dasha serving; 1.4=new synthesis files); no semantic
  dependency (1.4 skeleton independent of 1.8). Both base on integration (has WP-1.5 R-38). Disjoint from the
  still-verifying WP-1.3j (bodha/phala) too. **Verdict: dispatch CONCURRENTLY (separate worktrees, one message).**
**Dispatched 2026-07-13.**
- **WP-1.4 IMPL COMPLETE** → branch `worktree-agent-a58e2c38e1d66c9c2` (`676bef80`). New `synthesis/` module served as
  `synthesis/compose_large_n`: intent(P-10)→pre-aggregated-plan→map-reduce+running-budget→narrative+ledger. Worked:
  "marriage universe" composes 30,754-signal universe → 50 bounded exemplars/5 families, 51 ledger signal_ids
  resolve, NO flat top-K wall; W3-deepen seams documented (native contradictions=0=LCA-6/WP-2.2 disclosed). 12/12,
  tsc 0, eslint 0, registry regression 447 pass. 1 surgical import in catalog.ts. **Blind verifier DISPATCHED**
  (no-flat-wall + ledger-resolvability + honest-disclosure + domain-sanity + envelope conformance).
  ✅ **WP-1.4 CONFIRMED-FIXED + MERGED** (`25268719`). budget+per-family cap enforced (verifier couldn't dump);
  marriage universe 30,754→50 disclosed; signal_ids resolve 10/10; thin stages disclosed not fabricated; family
  sets classically sound; scope clean, tsc 0, 447-regression pass. **Follow-up (§4):** synthesis ledger fact_ids
  empty — `query_domain_reading.ranked_signals` doesn't project `constituent_facts_array` (signal_ids resolve to
  L1 one hop away) → small serving enhancement (candidate WP-1.6/W3).
  - **WP-1.8 IMPL COMPLETE** → branch `worktree-agent-ac16ca57acb5e1fb4` (`6c287068`; STEP-0 on integration, R-38
    present). ALL SERVING-SIDE (no writer/migration, no HALT). R-43: re-derive dasha-lord dignity+shadbala from
    chart_facts (native 100% NULL + 2nd bug shadbala keyed 2-letter vs display-name); served==chart_facts 0 mismatch;
    Abhinandan 39 stale dignities corrected incl. register's Saturn-"own"-in-Scorpio→neutral. R-46: BPHS-grounded
    varga term → native marriage `mixed`→`contested` (Venus 7th-lord/kāraka, neutral D1/debilitated D9); exposes
    d1_score/varga_term/varga_moved_verdict; character(op-varga D1) skips (no double-count). Multi-formula AVAYOGI
    both served w/ formula_id. Cross-surface assess↔get_signals 0/10→10/10 (domain) + disclosure. 13/13 + regressions,
    tsc 0, eslint 0. **Blind verifier DISPATCHED** (jyotish varga-doctrine DIRECTION + data-plane §N.5 vs chart_facts).
    Base f7a17e06 (behind 1.3j/1.4 by disjoint files) → rebase-if-needed at merge.
  ✅ **WP-1.8 CONFIRMED-FIXED + MERGED** (`0a41e356`). Verifier confirmed Saturn-Scorpio own→neutral (chart_facts),
  Venus D9=Virgo=debilitation (astronomically + chart_facts) → marriage mixed→contested = CORRECT Parashari
  direction, no double-count; multi-formula both served; assess↔get_signals byte-identical; serving-side only;
  tsc 0 both, regressions 20/20+6/6. **W1-remainder BATCH 2 COMPLETE (WP-1.8 + WP-1.4).**

### §6.6 — W1 CLOSE (native-fixed order)
1. ✅ **Reconciliation re-stamped** (Ruling 1: W1-FOLLOWUP 23→0; 0 unreconciled).
2. ✅ **integration→main PR #555** — 16 lane merges.
3. ✅ **CI**: 1 fix-iteration (§8.4 iter 1/3 — stale whitelist pins 34→52, §4); then all required checks CLEAN.
4. ✅ **MERGED** to main (squash `2385fb62`).
5. ✅ **DEPLOYED (single deploy, web+mcp)**: `amjis-web-00957-dn2` + `amjis-mcp-00421-2pz`, both image==main HEAD
   `2385fb62`; sidecar unchanged (W1 didn't touch it). **main↔prod deploy-parity CONFIRMED.**
6. **Live prod-verify:** conductor smoke on deployed `get_chart_orientation` (native) CONFIRMS W1 live —
   grounding.fact_ids populated (51 ids, resolvable, 298 resolved; was []), served_unattributed_share=0 (top
   entities SATURN/JUPITER/KETU), salience demotion live (WP-1.2d reason on rows), v3 envelope (coverage
   {served:3,total:13364}), chart_header Lagna Aries. **Full acceptance-suite prod-verify: PARTIAL (6/7
   DEPLOYED-GREEN).** GREEN: WP-1.2 attribution/discrimination (both charts, wealth 2/11/9 vs relationship
   7/12/8; moksha 12/4+Ketu not 9th) · WP-1.3 assets (yogini dasha, chart_facts+raman, bodha_discoveries 2392,
   phala_mitigation 602) · WP-1.5 envelope+dates honest · WP-1.8 varga verdict (marriage D9 varga_term -2.5,
   Venus D9 debilitated == chart_facts) · **LCA-17 isolation 0 substitutions (4 interleaved, native 13364 /
   Abhinandan 13369)** · no 500s. **1 DEPLOYED-RED:** `lel_query` serves dishonest-empty (`ok:true,count:0`)
   for native despite 57 `life_events` rows — twin `mimamsa_lel_query` returns the 57 → E5 violation, serving-path
   divergence (local-green≠deployed-green, exactly what the gate catches). WP-1.6 protocol resource
   CANNOT-VERIFY (deployed channel exposes tools not resources — channel limitation, not a defect).
   **→ ADJ-2 adjudicator DISPATCHED** (§7.4 rollback-whole-wave vs fix-forward, given 6/7 green + data-reachable +
   isolation-holds + wave strictly-better). **→ lel_query FIX DISPATCHED** (WP-1.3d §8.4 loop iter 1, needed
   regardless). W1 wave-close gated on ADJ-2 ruling + lel_query re-verify.
   - **ADJ-2 → FIX-FORWARD** (§6.7). **lel_query FIX DONE** (`ae9aa600`, PR **#556**). Root cause: NOT routing —
     the base `lel_query` tool unwrapped the double-wrapped ToolBundle envelope 2 levels too shallow + wrong count
     key (`total_count` vs capability's `total_matching`) → undefined → laundered `{ok:true,count:0}`; twin
     `mimamsa_lel_query` returns raw envelope so it worked. Fix: correct unwrap + **E5 honesty gate** (unparseable→
     error, never laundered empty) + param alignment. In-process native 0→57, Abhinandan honest-0, unparseable→err;
     9/9, tsc 0. Confirms ADJ-2 non-flip (pure unwrap bug, no isolation/scope). **PR #556 CI → merge → re-deploy
     amjis-mcp → prod re-verify item 2 (DEPLOYED-GREEN) → W1 close (7/7).**
   - ✅ **PR #556 merged (`fc84cd0d`) → amjis-mcp re-deployed (image==HEAD, parity confirmed).** **lel_query
     PROD RE-VERIFY: DEPLOYED-GREEN** — native `482012f1` `ok:true, total_count:57` (real dated events e.g.
     birth 1984-02-05, YYYY-MM-DD, provenance total_events:57); Abhinandan `1c826d5a` `ok:true, events:[],
     total_count:0` honest-empty (true 0). **W1 ACCEPTANCE SUITE = 7/7 DEPLOYED-GREEN.** F-L10-021-deployed
     residual CLOSED. ADJ-2 follow-through satisfied.
   - **✅✅ W1 WAVE CLOSED (2026-07-13)** — deployed (web `2385fb62` + mcp `fc84cd0d`, both==HEAD), 7/7
     prod-verified, ND-W1.1 PASS (0 unreconciled), 16 lanes blind-verified, +316 concept families reachable.
     Governance close (this branch). ND-W1.4 native Cowork probe runs async (not blocked).
7. **Governance close (this branch `docs/w1-close`):** ledger + CURRENT_STATE + SESSION_LOG → PR.
8. **ND-W1.4:** native runs Cowork-side live probe async — NOT blocked on.

### §6.5 — Dispatch: WP-1.6 (STRICTLY LAST — capability map + served consumption protocol)
No intersection check (runs alone, last). Base = final W1 integration (`0a41e356`, all 15 lane merges: 1.1/1.2αβ/
1.3a–j/1.4/1.5/1.7/1.8). Scope (P-12, widened v3): (1) transform Concept×Retrievability matrix
(`state/CONCEPT_RETRIEVABILITY_MATRIX.jsonl`, 3,058 families, per-channel — READ-ONLY seed) → machine-readable
concept→tool/service capability MAP keyed by concept family w/ per-channel routes, **regenerated against POST-W1
reachability** (WP-1.2/1.3/1.3j/1.4/1.5/1.8 changed what's served); (2) acquisition-tracker record schema
(needed/received/exhausted per evidence-plan item); (3) served consumption PROTOCOL — MCP prompt/resource teaching
demand-side posture (E3). Verifier: data-plane (sample map entries → execute route → concept arrives) +
jyotish-domain (**3 live demand-side sessions narrow/medium/broad** following the protocol, grade chase reaches
expected set). **Dispatched 2026-07-13.**
- **WP-1.6 IMPL COMPLETE** → branch `worktree-agent-a3915cca8db5008f4` (`31d76d87`). Map generator (idempotent,
  re-runnable) + artifacts `capability_map/CONCEPT_CAPABILITY_MAP.json`+summary; tracker schema
  `demand/acquisition_tracker.ts` (needed/received/exhausted, honesty validator); served protocol MCP resource
  **`marsys://consumption-protocol`** + prompt `demand_side_chase`. **Reachability delta: +316 newly reachable
  (2,024→2,289 of 2,589; deployed-MCP 902→1,906; truly-unreachable 157→142)** — dominated by phala_*/mimamsa_*
  now-served. 8 sampled routes arrive; tracker 6/6, protocol 5/5, map-route 2/2; tsc 0 both; state/deliverables
  untouched. **Blind verifier DISPATCHED** — map accuracy + delta honesty + **3 live demand-side sessions
  (narrow/medium/broad)** + protocol/tracker coherence. Merge on CONFIRMED → then W1 CLOSE.

### §6.7 — ADJUDICATION [ADJ-2] (W1 PARTIAL prod-verify disposition — 2026-07-13)
**Ruling: FIX-FORWARD** (not §7.4 rollback). W1 stays DEPLOYED; fix `lel_query` under §8.4, re-deploy, re-verify
item 2 → GREEN before W1 close. **Reasoning:** §7.4 auto-rollback targets a broken/worse deploy — this is 6/7
DEPLOYED-GREEN with the 57 events reachable in prod via twin `mimamsa_lel_query`, no 500/data-loss, isolation
verified 0-substitution; E-clauses (which outrank the mechanical PARTIAL label) are in AGGREGATE far better served
by keeping W1 (attribution/envelope/varga/18-assets/capability-map/isolation) than by rollback which would
reintroduce every pre-W1 deficiency to cure one E5 instance; proportionality = targeted tool fix, not sledgehammer.
**W1 = FIX-FORWARD-IN-FLIGHT, NOT closed** until lel_query re-verify GREEN + other 6/7 non-regressed.
**Flip→ROLLBACK if:** lel_query empty masks an isolation/entitlement fault (NOT met — returns empty, not
wrong-chart); OR alias unreachable (NOT met — mimamsa_lel_query serves 57); OR §8.4 budget (3 iters) exhausted
without GREEN. **Tracked residual:** lel_query dishonest-empty (F-L10-021 deployed) → carry to GREEN re-verify (7/7).

### §6.2 — ADJUDICATION [ADJ-1] (conductor, self-logged for async review)
Delegation realized as **direct thin-dispatch with per-lane fresh-context agents + ledger durability**, rather
than nested wave-conductor sub-agents, given this session's observed agent flakiness (several API-drop/stall
events on long nested tasks) — nested wave-conductors spawning lanes+verifiers+merges compound that failure
surface and risk losing whole-wave coordination. Each implementation lane and each blind verifier IS a fresh
re-grounded context (satisfies the fresh-context intent at lane granularity); the conductor owns only merges +
wave-closes (sequential, high-stakes) and the ledger. If conductor context degrades, harness summarization +
this ledger guarantee lossless continuation. Within-rules, non-scope-changing — logged for visibility.

---

## §7 — W2 WRITER WAVE (dispatched 2026-07-13)

### §7.0 — ADJ-1 RETAINED for W2 (conductor decision, reconsidered)
Considered delegating W2 to a fresh-context wave-conductor (§6 context-hygiene). **Retained direct thin-dispatch
(ADJ-1)** for W2 because: W2 is high-stakes (prod schema MIGRATIONS + writers feeding the W3 rebuild), and this
session's observed agent fragility (multiple API-drop/stall events on long tasks) makes a nested wave-conductor
that could drop mid-migration a WORSE failure mode than conductor context growth (which the harness summarizes +
the ledger makes resumable). Merges + migration application stay under the top conductor's reliable control; each
implementation lane + verifier IS a fresh re-grounded context (fresh-context intent satisfied at lane granularity).
Revisit if context degradation becomes acute.

### §7.1 — W2 corrected DAG (native) + pre-dispatch intersection
- **Fully parallel from start (disjoint writer families):** WP-2.1 (ka_ activation-date writer, R-45) · WP-2.4
  (bo_laksana MSR ingestion redesign, LCA-9b) · WP-2.5 (new ga_ sensitive-degree + ayurdaya + L0 organ seed,
  R-47/LCA-10/16) · WP-2.2-nonCGM (CDLM rollups/gradients/clusters, RM tables, bo_samvada/contradictions, phala
  narration, bo_sangati; LCA-5) · WP-2.3-graph (graha↔bhava edges + yoga nodes; LCA-9a).
- **Sequenced:** (a) WP-2.3-TEMPORAL-hooks wait on WP-2.1 date-resolution (2.1 merges first; 2.3 consumes merged
  helper); (b) WP-2.2-CGM stages (topology/sub_graphs/motifs incl LCA-6 native-zero) wait on WP-2.3-edges landing.
  2.2/2.3 coordinate via ledger on the bo_cgm file family; merge-order if scopes can't cleanly split.
- **Standards:** FROZEN orchestrator §N.2 (@register WriterBase, ctx.db_conn no-commit) — HALT if change needed ·
  §N.3 idempotency (per-chart delete-then-insert) · §N.4 surgical migrations only · B.10 no fabricated computation
  (esp. WP-2.5 ayurdaya = 3 classical methods per §8.2, no invention) · §N.5 referential integrity (WP-2.4 CI
  validator: every constituent_facts_array entry resolves to chart_facts.fact_id).
- **Verification:** per-lane blind writer-conformance + unit tests PRE-merge; **full DATA verification deferred to
  W3 rebuild** (plan: "verification completes at W3"). Base `integration/w2-writers` off main `fc84cd0d` (W1 live).

### §7.2 — W2 batch-1 (WP-2.1 ∥ WP-2.4 ∥ WP-2.5) status
- **WP-2.4 IMPL COMPLETE** → branch `worktree-agent-aa588eebf082b774b` (`a71d1b3c`). bo_laksana: flood cap
  (aspect_jaimini_per_varga 15,660→~1 aggregate/varga citing ALL member fact_ids), re-tier per-varga→supporting,
  KP bhava→domain, dosha_label/yoga_label integrity, 100% constituent resolution (filter-resolving+union-own).
  NEW §N.5 CI validator `msr_referential_integrity.py` (self-test + mutation-proven + ci.yml gate). No migration
  (cols exist). FROZEN orchestrator untouched, no HALT. 24/24 + 84/84. **Blind verifier DISPATCHED** (conformance
  + §N.5 validator mutation + flood-traceability + no-false-cap + no-fabrication). Data-verify at W3.
  ✅ **CONFIRMED-FIXED + MERGED** (`48834a13`) — orchestrator conformant, §N.5 validator mutation-proven +
  hard-CI-gated (governance-gates, no continue-on-error), flood all-ids-cited, D1 uncapped, 100% resolution
  no-fabrication; 24/24 + regression. Validator self-test confirmed on merge result. **W3 data-verify pending.**
- **WP-2.1 IMPL COMPLETE** → branch `worktree-agent-ab1d86324e2124b7d` (`001a1289`). Root cause: writers dated
  off single `kala_convergence.peak_date` (110/66,836); `ka_yojaka` bound `constituent_lords` YOGA-class-only.
  Fix: resolve predicate lords vs `chart_dashas` Vimśottarī timeline (dasha period = window, peak refines; every
  date traces to chart_dashas, no fabrication); ka_yojaka enriches lords from sign-lordship/sāḍe-sātī. Coverage
  0.16%→~64% (tail = WP-2.4 domain). **Reusable helper `services/ka_temporal/date_resolver.py` for WP-2.3-temporal.**
  No migration. FROZEN orchestrator preserved, no HALT. 61 new + 381 L3 (2 pre-existing TestProdDB). **Blind
  verifier DISPATCHED** (conformance + deterministic-date-trace + lord-mapping + helper quality + coverage honesty).
  Data-verify at W3. **On merge → unblocks WP-2.3-temporal (consumes the merged helper).**
  ⚠️ **VERDICT: NOT-MET (§8.4 iter 1) — verification caught a real defect.** Conformance/lord-mapping/idempotency/
  no-fabrication PASS, BUT the resolver selects `matched[0]` by EARLIEST start with NO birth-forward + NO
  ayanamsha filter → windows land DECADES PRE-BIRTH (Saturn AD 1951-52 for a 1984 native); dates real but
  life-irrelevant → R-45 unmet. Unit fixtures (2010-46 only) MASK it. Would propagate through the shared helper
  to WP-2.3-temporal. **BOUNCED to implementer:** (1) birth-forward filter + select life-relevant period; (2)
  honor predicate ayanamsha_id (not pool 5); (3) pre-birth-inclusive multi-ayanamsha regression fixture.
  **NOT MERGED — WP-2.3-temporal STAYS BLOCKED until re-verify GREEN.**
  ✅ **FIX iter-1 (`9705e5b2`) + conductor live-retest CONFIRMED** — birth-forward + ayanamsha-consistent + regression
  fixture (guards the guard). Live-retest: native earliest post-birth Saturn AD (lahiri) = 1991-08-18→1994-08-21
  (was 1951 pre-birth), resolver now selects it. **MERGED → integration (`8034347a`).** **Unblocks WP-2.3-temporal.**
- **⚠ W2 CI-collection fix (conductor):** full `pytest tests/` collection exited 2 — `bo_laksana` double-registered
  (identical class re-imported via 2 module paths, triggered by WP-2.4's new test). W2-introduced full-suite failure.
  **Fixed** `pipeline/orchestrator/writers/__init__.py register()`: idempotent no-op for the IDENTICAL class
  re-registering (same name+module-basename), STILL raises on a genuine conflict (different class, same id).
  Contract preserved (one-writer-per-asset_id). Verified: collect exit 0, 58 writer tests pass, genuine-conflict
  still raises. NOT a FROZEN-core edit (writers/__init__.py, not orchestrator/core/**).
- **WP-2.5 IMPL COMPLETE** → branch `worktree-agent-aa2e0198b6f28f5a1` (`9167a61f`). New `ga_sensitive_degree` +
  `ga_ayurdaya` writers + L0 `bg_sign_medical` Kalapurusha organ seed + dosha wiring (gandanta/mrityu-bhaga).
  Every value DELEGATED from cited PyJHora consts (BPHS/Jataka Parijata — B.10, no hand-recall). Ayurdaya 3 methods
  (Pindayu/Nisargayu/Amsayu) method-attributed + applicability rule served separately (no adjudication, §8.2);
  maraka significators. Organ map cited. **Migrations 431/432 AUTHORED-UNAPPLIED** (organ seed + asset_registry
  chart-scoped count_sql). Honest W3-deferral flags (kranti β=0, full SBC vedha, ayurdaya haranas — disclosed
  pending_w3, not faked). Judgment aspecting-graha hook correctly left to W1 serving lane (follow-up §4). 18/18,
  FROZEN orchestrator preserved, no HALT. **Blind verifier DISPATCHED** (classical recompute + ayurdaya §8.2 +
  migration surgery + no-fabrication + deferral honesty). Data-verify at W3.

### §7.3 — W2 batch-2 dispatch manifest (WP-2.2-nonCGM ∥ WP-2.3-graph)
**Pre-dispatch intersection:** WP-2.2-nonCGM = CDLM rollups/gradients/clusters (bodha_cdlm) + RM tables (bodha_rm)
+ bo_samvada/contradictions + phala narration + bo_sangati. WP-2.3-graph = CGM graph EDGES (graha↔bhava) + yoga
nodes (bo_cgm). **DISJOINT** — nonCGM explicitly EXCLUDES the bo_cgm file family that WP-2.3 owns (native's
coordination rule). Also disjoint from batch-1 (ka/bo_laksana/ga). **Dispatch CONCURRENTLY.** SEQUENCED-LATER:
WP-2.2-CGM (topology/sub_graphs/motifs incl LCA-6) waits on WP-2.3-EDGES landing; WP-2.3-temporal waits on WP-2.1.
Dispatched 2026-07-13.
- **✅ WP-2.5 fix iter-1 (`6fb472ba`) + conductor live-retest CONFIRMED + MERGED (`843a4492`).** sign_num off-by-one
  fixed (canonical 0-based from longitude, single source; 1-based DB fixture guards path). Live-retest: Sun lon
  291.96°→9=Capricorn == DB sign_num 10−1=9 (Moon/Lagna consistent) → mrityu-bhaga 2.0°, Nisargayu 99.185y==cited.
  Migrations 431/432 unapplied. Full collect exit 0 (register fix holds).
- **✅ WP-2.3-graph IMPL COMPLETE** → branch `worktree-agent-a54548b0194007c96` (`912fdb5a`). 60 orphaned bhava nodes
  wired via 3 graha↔bhava edge types (lordship/occupancy/bhava_aspect from real L1) + first-class yoga/dosha nodes
  + yoga_member edges; every edge cites resolving chart_facts.fact_id (new `constituent_fact_ids_array TEXT[]`).
  Seams: WP-2.2-CGM edge-types registered; WP-2.3-temporal `active_dasha_periods_jsonb` left NULL. 17+22 tests,
  FROZEN preserved. **⚠ Migration 431 COLLIDES with WP-2.5's 431 → conductor RENUMBERS to 433 at merge.**
  **Blind verifier DISPATCHED.** **On merge → unblocks WP-2.2-CGM + WP-2.3-temporal.**

## §4 — HALT / disagreement register + follow-ups (append-only)

**HALTs / disagreements:** none yet.

**W1-close CI fix-iteration [§8.4, iter 1/3]:** PR #555 full-suite "Unit Tests" caught 2 stale whitelist-count
pins (`primitives.test.ts`, `red_team/whitelist.test.ts` RT-04h) asserting `34` — not updated to the final
post-W1 whitelist (34 post-1.7 +13 WP-1.3a +5 WP-1.3j = **52**). This is the value of wave-level CI: individual
lanes ran targeted tests, only the combined full suite exercised these pins. Fixed 34→52 (no logic change;
`whitelist_resolution_invariant` already confirms all 52 resolve; scanned — no other stale count pins). Pushed
`ca17cca5`, CI re-running.

**Follow-ups surfaced during W1 (not blockers; carry to W4 / doctrine campaign / register):**
- **F-WP17-1** (from WP-1.7): `multi_school_signal_lookup` / `cross_school_lookup` legacy `lib/tools` impl was never bridged to the registry → its deployed consumer `platform-mcp/src/bundles/multi_school_bundle.ts` degrades gracefully (`errored:true`). Prioritize re-bridging if multi-school convergence data is expected. Owner: W1 residual → consider WP-1.3 or a follow-up lane.
- **Contract-surface phantom declarations** (from WP-1.7 verifier): `kp_query`, `query_kp_ruling_planets`, `timeline_query` remain declared in the untouched CONTRACT/router surface (`tool_metadata.ts`, `contract_bridge.ts`, `retrieval_capability_spec.ts`) with no engine backing. Out of WP-1.7 scope; future contract-surface reconciliation should implement or drop them (same phantom-declaration bug class). Candidate: W4 re-grade / doctrine campaign.
- **R-45** (rediscovered by WP-1.1 verifier): `get_temporal_windows` = 0 activations (NULL activation dates) — already owned by **WP-2.1** (W2).
- **⭐ F-DATE-TZ (from WP-1.3(e) — HIGH priority for WP-1.5):** Postgres `date` columns returned raw are parsed by node-postgres at IST-midnight → serialized to UTC → **off-by-one + spurious time component** (`1964-01-22` → `"1964-01-21T18:30:00Z"`), breaking any date round-trip. WP-1.3(e) fixed its own tool via `to_char(col,'YYYY-MM-DD')` + `::date` param binding. **Sibling L3 serving tools share the SAME trap and are NOT yet fixed — including some just merged in WP-1.3(a): `query_dasha_dossier`, `query_temporal_view`, `query_convergence_windows`, plus `query_projections`, `call_service_wrappers`.** → **WP-1.5 (envelope honesty) must apply the `to_char` treatment program-wide to every served `date` column.** Latent correctness bug in already-integrated tools until then.
- **F-WP13-testcleanup** (WP-1.3h scope, from dasha + apex/assess verifiers): `platform-mcp/src/tools/__tests__/m8_e2e_proof.test.ts` has (a) L519 dangling ref to retired `registerQueryDashaPeriodsTool`; (b) stale count constants — G12 `REGISTERED_TOOL_COUNT=45` and V6 D7-bridge `=12` — now wrong because multiple integrated lanes added/removed registry tools (WP-1.3 a/f/i/dasha). All red-both-ways (in the pre-existing baseline, NOT regressions). **WP-1.3h** must reconcile these count constants to the post-B2 actuals + scrub the dangling ref. Per ND-W1.3.
- **OBS-W12b-1** (from WP-1.2β verifier, non-blocking): native `query_ucd` now serves only **3 entity_profiles (all graha, Saturn-dominated)** vs Abhinandan's 15 (graha+bhava) — a consequence of `sade_sati→SATURN` attribution concentration meeting the native's Saturn-heavy top-300 pool (297/300 → ~3 grahas). Pre-existing pool logic, NOT a WP-1.2β regression; UNATTRIBUTED=0 holds. But a 3-entity native orientation is thin for acharya-grade whole-chart read → candidate refinement for **WP-1.4** (synthesis) or a follow-up (entity-profile diversity / pool balancing). Re-check at W4.
- **F-WP15-cursor** (WP-1.5 verifier): `list_entities` emits `next_cursor` but has no cursor/offset INPUT param → disclosure-honest but not round-trip-consumable. Small serving follow-up (add the param). Also (WP-1.3j note): the 5 new bodha tools + 2 phala fixes hand-roll offset envelopes instead of WP-1.5 `buildHonestPagination` — consistency follow-up (adopt shared helper + cursor). Candidate: WP-1.6 cleanup or a W1-close sweep.
- **F-WP15-priorityrank** (WP-1.5 verifier): native `call_priority_ranking` empty — kala_activation `activation_start/end` 100% NULL under lahiri (only 302/133,583 dated) → **R-45/WP-2.1 data-plane** (PENDING-W3, not a serving defect; tool is honest-empty).
- **W1-CLOSE TODO:** re-stamp WP13_RECONCILIATION_v1_0.md's 11 W1-FOLLOWUP rows → PENDING-W2/W3/PARK (WP-1.3j served 12 of the 23; Ruling 1: no W1-FOLLOWUP class survives W1 close).
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

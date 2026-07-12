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

**Current position:** ✅ **W0 CLOSED** (WP-0.1 LCA-17 remediated, deployed, prod-parity proven). Entering **W1** (serving plane, 7 parallel lanes).

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

### §1c — Probe observations carried forward (not W0 scope)
- **[OBS-1] chart_facts row-count divergence:** native `chart_facts` = 135,645 on prod vs L1_GANITA_CLOSURE canonical 27,554 (~4.9×). Possible rebuild accretion / idempotency drift, or stale closure number. **Relevant at W3 (rebuild must not accrete — §N.3 delete-then-insert). Verify pre/post W3 native rebuild. Do NOT act in W0.**

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

## §4 — HALT / disagreement register (append-only)

_(none yet)_

---

*Ledger opened 2026-07-12 by the Program Conductor. Append-only below §0's status board; §0 is the one mutable status surface.*

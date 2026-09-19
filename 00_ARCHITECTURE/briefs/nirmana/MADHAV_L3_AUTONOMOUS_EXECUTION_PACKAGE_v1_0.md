---
artifact: MADHAV_L3_AUTONOMOUS_EXECUTION_PACKAGE
version: "1.0"
status: READY_TO_DISPATCH
prepared_on: 2026-09-20
prepared_by: "Strategy session (Claude Code) — read-only grounding; no repo mutation"
ground_truth_as_of: "2026-09-20 01:15 IST"
protected_main_observed: 66b962f2994f0a7500c285025740cd5861534d8c
production_in_sync: true
governing_plan: MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md
native_authorization: "Native agreement recorded 2026-09-20 (this conversation): plan adopted; autonomous overnight execution authorized; commit/merge/push/deploy authorized; budgets 2x estimate."
changelog:
  - "1.0: Autonomous overnight execution package for L3 Kāla. Written after the delivery gate opened (production in sync at 66b962f29, migration 1040 applied, builder image rebuilt, W1 executable via migration-1035 SQL functions)."
---

# L3 Kāla — autonomous overnight execution package

Three parts: **§A** operator pre-flight (do this before you sleep, ~10 min), **§B** the
paste-ready conductor prompt, **§C** optional satellite session prompts for extra parallelism.

---

## §A — Operator pre-flight

### A.1 Ground truth this package assumes (verified 2026-09-20 01:15 IST)

| Fact | Value |
|---|---|
| `origin/main` | `66b962f2994f0a7500c285025740cd5861534d8c` |
| web / MCP / sidecar ready revisions | all `*-probe-66b962f2994f-35464335676-1` |
| builder job image | `brahma-pipeline:66b962f2994f0a7500c285025740cd5861534d8c` |
| deploy run 35464335676 | migrate **success**, web/MCP/sidecar/pipeline **success**, earned-outcome **success** |
| migration 1040 | applied (bootstrap skipped ⇒ `purna=marked` path taken) |
| W1 mechanism | SQL functions from migration 1035: `open_l1_data_plane_generation`, `capture_l1_data_plane_dasha_partition`, `complete_l1_data_plane_partition`, `select_l1_data_plane_generation`, `rollback_l1_data_plane_generation` (+ L2 equivalents in 1036) |
| Real head-table names | `l1_data_plane_generation_heads` / `l2_data_plane_generation_heads` (the handoff's `l1_generation_heads` was shorthand) |
| Codex lease | `MADHAV-PURNA-DELIVERY-DATA-PLANE-ALLOWLIST-SUCCESS` **ACTIVE until 2026-09-20 04:30 IST** |
| The 9 preservation branches | **still LOCAL-ONLY — never pushed** |
| Migration high-water | `platform/migrations` 1040 · `platform/supabase/migrations` 1041 |

### A.2 Permission pre-authorization — the #1 cause of a stalled overnight run

An unattended session dies on the first permission prompt. Before dispatching, add to
`.claude/settings.local.json` in the **main checkout** (`/Users/Dev/Vibe-Coding/Apps/Madhav`):

```jsonc
{
  "permissions": {
    "allow": [
      "Bash(git *)", "Bash(gh *)", "Bash(gcloud *)",
      "Bash(npm *)", "Bash(npx *)", "Bash(node *)", "Bash(python3 *)", "Bash(pytest *)",
      "Bash(cloud-sql-proxy *)", "Bash(psql *)", "Bash(jq *)",
      "Read", "Edit", "Write", "Glob", "Grep", "Agent", "TodoWrite"
    ]
  }
}
```

Known trap from this project's history: **some rules here have historically required `Edit()`
rather than `Write()` patterns.** If the conductor reports permission stalls, that is the first
thing to check — not a model failure.

Run the conductor with `--permission-mode acceptEdits` (or your configured equivalent). Do **not**
disable the sandbox wholesale; the guardrails in §B.7 assume tool calls are still observable.

### A.3 Where to run it

Use the **Claude Code CLI in a terminal**, not Antigravity, for the conductor. It needs
worktree creation, background tasks, and subagent dispatch. Antigravity is fine for the
satellite sessions in §C if you prefer a GUI.

```sh
cd /Users/Dev/Vibe-Coding/Apps/Madhav
claude --permission-mode acceptEdits
# then paste the §B prompt
```

### A.4 One decision you still owe (not blocking tonight)

The `WATCHDOG_SECRET` incident on tagged zero-traffic revision `amjis-web-02826-huf` needs a
**human** owner to rotate/revoke and audit. Pūrṇa flagged it; neither campaign may act. The
conductor is instructed to leave it alone and re-surface it in the morning report.

---

## §B — The conductor prompt (paste this)

````markdown
# L3 KĀLA — AUTONOMOUS OVERNIGHT EXECUTION (CONDUCTOR)

You are the **conductor** for the L3 Kāla data-plane elevation campaign, running unattended
overnight. The native has authorized this session, is asleep, and will read your morning report.
Work continuously. Do not wait for input. Do not stop to ask questions you can answer from
evidence or resolve through the Native Surrogate (§5).

## 0. First acts, in this exact order

1. Read `00_ARCHITECTURE/briefs/nirmana/MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` — the
   governing plan. Then `MADHAV_L3_CLAUDE_CODE_HANDOFF_2026-09-19.md`. Both live in the
   strategy worktree `/Users/Dev/.codex/worktrees/50a6/Madhav` (they are untracked there —
   Packet B1 is what puts them on main).
2. Read root `CLAUDE.md`. Note that its §E line 192 (`L3 ✓ CLOSED, 12 ka_* assets`) and §C
   item 5 (`Currently L2 Bodha`) are both **known-stale** and are Packet B3's job to fix. Do
   not let them redirect you.
3. **Execute Packet A1 immediately** (§3). It is 10 minutes, zero risk, and protects work that
   currently exists on exactly one disk. Nothing else starts until A1 is done.
4. Initialize durable state (§6).

## 1. Goal and the only metric that counts

Move **individual L3 assets** to terminal acceptance. Terminal means, at current campaign
definition `t3-2026-09-11-8b884eac`:

`LAYER_DATA_ACCEPTED (or type-appropriate service proof) + CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED + VALUE_EVALUATED`
authenticated by a real freeze/terminal event — never by SQL insert, never by self-certification.

Headline metric: **`Accepted N/22`**, currently **0/22**. Tonight's target: **≥ 2/22**, with
W1 upstream generations established. Stretch: 3–4/22.

The 22 active identities:
```
ka_avadhi ka_bhavishya_lekha ka_dasha_kala ka_gochara ka_gochara_resonance
ka_gochara_v3_century_materialize ka_graha_sancara ka_jivana_parva ka_kala_darshana
ka_kalasutra ka_kota_chakra ka_kshetra ka_moorti_nirnaya ka_muhurta_seva ka_sangam
ka_sudarshana_varsha ka_taranga ka_tithi_pravesha ka_tulana ka_vedha_gochara
ka_vighnakara ka_yojaka
```
`ka_gochara_sweep` is retired, protected history, never rebuilt, outside the denominator.

**Second scorecard, reported separately and never merged into the first:** Phase-0 progress
(branches preserved 0/9 · governing docs on main · DP-SD-021 · salvage packets landed n/6 ·
triage record · field dossiers n/22 · baselines). Phase-0 work does not move `Accepted N/22`
and must never be reported as if it did.

## 2. Ground truth as of 2026-09-20 01:15 IST — re-verify, do not trust

The delivery gate **opened** last night. Verify each of these yourself before acting on it:

- `origin/main` = `66b962f2994f0a7500c285025740cd5861534d8c`
- web, MCP, sidecar all serve `*-probe-66b962f2994f-35464335676-1`; builder job image is
  `brahma-pipeline:66b962f29…`. **Production is in sync with main.**
- Deploy run `35464335676`: `Apply Routine DB Migrations` success, all four deploys success,
  `Require earned deployment outcome` **success** (mode `earned-deployment`).
- Migration 1040 applied; `purna` marker = `marked`.
- **W1 is executable.** Migration 1035/1036 installed SQL functions:
  `open_l1_data_plane_generation`, `capture_l1_data_plane_dasha_partition`,
  `complete_l1_data_plane_partition`, `select_l1_data_plane_generation`,
  `rollback_l1_data_plane_generation`, plus L2 equivalents. Real head tables are
  `l1_data_plane_generation_heads` / `l2_data_plane_generation_heads`.
- Codex holds lease `MADHAV-PURNA-DELIVERY-DATA-PLANE-ALLOWLIST-SUCCESS` until **04:30 IST**.
- The 9 preservation branches are **local-only**.

Record any drift in the state file and adapt; do not re-plan the campaign because a SHA moved.

## 3. The packet DAG — what to run, and what may run in parallel

### Wave A — preservation (BLOCKING, do first, ~15 min, single-threaded)

**A1 — Push the nine local-only branches to origin, unchanged.**
```sh
for b in codex/l3-bhavishya-p0 codex/l3-dhara-correction codex/l3-kshetra-p0 \
         codex/l3-kshetra-p0-correction codex/l3-kshetra-w0-preservation \
         codex/l3-u05-registry codex/l3-w0-field-contract codex/data-plane-l3-yojaka \
         codex/madhav-data-plane-strategy; do
  git -C /Users/Dev/Vibe-Coding/Apps/Madhav push origin "refs/heads/$b:refs/heads/$b"
done
```
These branches carry every "preserved achievement" the handoff lists in §5 — Kshetra W0
safety, Bhavishya history protection, DHARA numerical correction, the W2 first frontier,
Yojaka meaning preservation — plus the four governing documents. **None of that work is on
main and none of it exists off this machine except in a ZIP.** Push exactly as-is; do not
rebase, squash, or "tidy". Verify with `git ls-remote --heads origin` and record all nine SHAs
in the state file. If a push is rejected, do not force — record and surface it.

**A2 — Create the integration worktree.**
```sh
git -C /Users/Dev/Vibe-Coding/Apps/Madhav fetch origin main
git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree add \
  /Users/Dev/madhav-l3/integration -b codex/madhav-l3-claude-code origin/main
```
(The `codex/` prefix is historical and kept for CI/ruleset compatibility. If a ruleset rejects
it, fall back to `l3/claude-code-integration` and record the change.)

**A3 — Initialize durable state** per §6.

### Wave B — governance (parallel with C and D; one owner; docs-only ⇒ safe to merge)

- **B1** — Put the four governing documents on main as a **docs-only PR**: L3 Kāla Strategy,
  L3 Kāla Execution Brief, Astra Review Record, Unblock & Resume Amendment (DP-SD-018). They
  are tracked on `codex/madhav-data-plane-strategy` under
  `00_ARCHITECTURE/briefs/nirmana/`. **Copy the four files. Never merge that branch** — it
  carries 25 commits and 627 stale runtime-source files. Include in the same PR:
  `MADHAV_L3_CLAUDE_CODE_HANDOFF_2026-09-19.md`, `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md`,
  and this package.
- **B2** — Author **DP-SD-021** from the skeleton in the dual-campaign plan Appendix C.
  Native authorization is recorded: *native agreement, 2026-09-20, this conversation* —
  adopting the plan, splitting execution (Claude Code = L3, Codex = Pūrṇa), superseding the
  brief's "sole execution destination" clause and the dead `c9bd` worktree pin, and ratifying
  migration ranges **Pūrṇa 1042–1069 / L3 1070–1119 / shared ≥1120**. Record it in the
  strategic ledger.
- **B3** — Governance surface refresh: `CLAUDE.md` §E L3 row (→ 22 active identities, 0
  accepted, campaign pointer) and §C item 5 (→ active campaigns are Pūrṇa Anveṣaṇa in Codex ∥
  L3 Kāla data-plane in Claude Code); `CURRENT_STATE_v1_0.md` §2 new banner; a fresh
  `CLAUDECODE_BRIEF.md` for L3 with `may_touch`/`must_not_touch` lifted from the execution
  brief plus the §3.3 partition rules; `CAMPAIGN_COORDINATION.md` L3 party row + migration
  ranges + the `L3-REQ-nn` / `PA-REQ-nn` interlock LOG format.

### Wave C — verification (parallel; read-only; needs the DB reader)

- **C1** — Independently re-verify last night's deployment: ready revision + `NIRMANA_DEPLOYED_SHA`
  for each door, job image tag, `schema_migrations` rows for 1033–1041, the four ownership
  markers. This is **L3's own evidence**, not a copy of Codex's. Doctrine: builders never
  self-certify, and neither does the other campaign on our behalf.
- **C2** — Per-asset baseline for all 22: current row count for the canonical chart
  `482012f1-710e-4a25-994a-93821f5871aa`, generation/partition state, terminal-event state at
  definition `t3-2026-09-11-8b884eac`. **Aggregates only — never sample private narrative
  content.** Known landmines to characterize, not "fix" tonight: `kala_activation_predicates`
  has 50,678 rows with **79 unmatched same-chart MSR references**; `ka_kshetra` has ~8.6M field
  rows while a served surface hard-codes "field empty" (PARK-5). L3 is **not** an empty slate.
- **C3** — Confirm `l1_data_plane_generation_heads` / `l2_data_plane_generation_heads` are
  still empty for the canonical chart, and read the exact signatures + guard/rollback semantics
  of the 1035/1036 functions. This is the W1 execution contract.

**DB access:** stand up a read-only Cloud SQL proxy, run aggregate queries, stop the proxy.
```sh
cloud-sql-proxy --address 127.0.0.1 --port 5433 madhav-astrology:asia-south1:amjis-postgres
```
`gcloud` is authenticated as the native. **Read-only only in Wave C.** Never print a
credential, connection string, or private row content into logs, files, or the report.

### Wave D — salvage (parallel, worktree-isolated; this is where the reviewed work is rescued)

Every packet: branch off current `origin/main`, cherry-pick or re-apply the reviewed change,
**re-review and re-run the tests on today's main**. The old green is history, not evidence.
One branch per packet — not one per finding.

| Packet | Source branch | Territory | Parallel group |
|---|---|---|---|
| **D1** Kshetra P0 safety (mutation-free planning, 15-table referrer preflight, lock handling; ref `3f109869d`) | `codex/l3-kshetra-p0`, `-correction`, `codex/l3-kshetra-w0-preservation` | `services/ka_kshetra/**` | **G1** |
| **D3** DHARA numerical correction (midpoint fix, 1515-vs-300 discrepancy, 40/202 fractions; ref `87cc8c9`) | `codex/l3-dhara-correction` | `services/ka_kshetra/dhara_null_vec.py` | **G1** (after D1 — same files) |
| **D4** Yojaka meaning preservation (signed multi-domain promises; no max-domain flattening; refs `7697c43b3`/`fbf7803dc`) | `codex/data-plane-l3-yojaka` (118 commits ahead) | `writers/ka_yojaka.py`, `services/ka_yojaka*`, some DHARA tests | **G2** (coordinate with G1 on shared DHARA tests) |
| **D2** Bhavishya P0 history preservation (candidate computation + referrer checks before destructive mutation; ref `a3e518864`) | `codex/l3-bhavishya-p0` | `writers/ka_bhavishya_lekha.py` | **G3** |
| **D5** W0 field-contract register (39 partitions / 699 fields / 14 asset digests) | `codex/l3-w0-field-contract` | docs | **G4** |
| **D6** U05 registry/fallback (preserve requested + effective filters) | `codex/l3-u05-registry` | `registry/layers/L3_kala/**` | **G5** |
| **D7** Branch triage record (~113 branches) | read-only | one artifact | **G6** |

D7 classes (from the dual-campaign plan Appendix B): 8 preserved packets → per-packet
disposition; `codex/madhav-data-plane-strategy` → extract-never-merge; 4 delivery-repair
leftovers → retire, and **close PR #2655** (open, superseded by #2656, never merge it);
37 × `heartbeat-idle-*` → one bulk retirement record; ~66 pre-2026-09-15 `nirmana-l3-*` →
one `SUPERSEDED_BY_STRATEGY_2026-09-15` record. **Do not delete any branch tonight** — a
disposition record is the deliverable; deletion is a separate authorized act.

### Wave E — the needle (this is the point of the night)

**E1/E2 — W1 upstream truth.** Establish accepted L1 then L2 generations for the canonical
chart using the 1035/1036 functions: open → capture partitions → complete → select. Verify
every contributing producer partition — **seven L2 producers share MSR**, and
`bo_bimba`/`bo_karanajala` share CGM nodes, so one "latest head" is not the dependency vector.
Exit: `l1_data_plane_generation_heads` and `l2_data_plane_generation_heads` populated for
`482012f1…` with an independent partition-acceptance record.

**Preconditions for E1/E2 (all mandatory — this is the only production mutation tonight):**
1. Wave C complete; you know the exact current state.
2. **No conflicting active lease.** Codex holds one until 04:30 IST. Claim your own L3 lease on
   `origin/campaign-coordination` bound to your operation, and do not begin while Codex's is
   live and overlapping.
3. **Rollback proven first**: exercise `rollback_l1_data_plane_generation` on a disposable
   PostgreSQL instance before touching production.
4. An operation-specific backup/restore point recorded.
5. Release the lease with evidence when done.

**E3 — `ka_graha_sancara` to terminal.** The smallest genuine end-to-end proof: a service
identity, so its acceptance is **service proof, not a row build** — do not invent rows.
Required: exact conventions/time/arbitrary-chart input, bounds and error behaviour, provenance,
failure modes; consumer route through `registry/layers/L3_kala/` (`call_ephemeris_at_t`,
`query_planet_transit`); deployed MCP revision evidence; a value test showing the data changes
an answer; then the authenticated freeze event. **→ Accepted 1/22.**

**E4 — `ka_dasha_kala` to terminal.** Reads L1 `chart_dashas`; service identity; exposes
hierarchy, applicability, intervals, failed/silent systems, qualified overlap — and never
restates an L1 computed value as its own (§N.5: reference the `fact_id`, inherit L1's value; a
disagreement is a halt-worthy bug, not a stored divergence). **→ Accepted 2/22.**

Both light Pūrṇa SCUs (`call_ephemeris_at_t`, `query_active_dashas`, `call_dasha_eligibility`),
which is a real cross-campaign unblock — record it as such.

### Parallel execution groups

```
A1 → A2 → A3            (blocking, ~15 min)
   ├── B1 → B2 → B3     (one owner, sequential within Wave B)
   ├── C1 ∥ C2 ∥ C3     (read-only, fully parallel)
   ├── G1: D1 → D3      (same files, sequential)
   ├── G2: D4           (parallel; coordinate shared DHARA tests with G1)
   ├── G3: D2           (parallel)
   ├── G4: D5           (parallel)
   ├── G5: D6           (parallel)
   └── G6: D7           (parallel, read-only)
C complete → E1 → E2 → (E3 ∥ E4)
```

Run **up to 5 implementer agents concurrently**. Every implementer works in its own worktree —
use the Agent tool's `isolation: "worktree"`, or create one under `/Users/Dev/madhav-l3/<packet>`.

## 4. Agent roster

Dispatch these as subagents. Give each a self-contained brief: it has not seen this prompt.

| Role | Count | Mandate | Hard limits |
|---|---|---|---|
| **CONDUCTOR** | 1 (you) | Packet queue, dispatch, integration, merges, state, morning report | Never implements a packet yourself while agents are idle; never reviews your own work |
| **IMPLEMENTER** | ≤5 concurrent | One packet, one worktree, one branch, tests + evidence | Never merges its own PR; never touches another packet's territory |
| **VERIFIER** | ≤2 concurrent | Independent read-only review of the exact candidate and **raw evidence, not the builder's summary** | Must not be the agent that wrote the code; cannot approve with an unexplained finding |
| **NATIVE SURROGATE** | 1 at a time | Bounded decisions — see §5 | Cannot create credentials/IAM/authority, change doctrine, or lower an acceptance bar |
| **RELEASE DUTY** | **exactly 1, never concurrent** | Merge to main, deploy dispatch, lease claim/release, production mutation | One operation at a time; no second release agent may exist |
| **DB READER** | 1 | Proxy up → aggregate queries → proxy down | Read-only in Waves A–D; aggregates only; never prints credentials or private rows |
| **SALVAGE ANALYST** | 1 | D7 triage across ~113 branches | Read-only; never deletes a branch |
| **SCRIBE** | 1 | State file + evidence ledger + morning report | Never edits source |

## 5. Native Surrogate protocol

**Triggers** — invoke on any of: a second identical deterministic failure; exhausted transient
retry budget; two governing documents in genuine conflict; material ambiguity inside the
charter.

**Packet in:** goal · exact SHA · state · failure fingerprint · attempt history · evidence ·
safe actions available · authority boundary · required return fields · resume state.

**Packet out:** decision · rationale · authorized next action · disallowed actions · required
verifier · resume state. Then it exits and you resume.

**Hard boundary:** a surrogate may resolve in-charter ambiguity. It may **not** create
credentials, grant IAM, substitute for an unprovisioned external authority, change doctrine or
product scope, lower an acceptance requirement, or authorize touching anything in §7's
forbidden list. If the real answer is "the native must decide", record it and move to other
work — do not manufacture a decision.

## 6. Durable state

Maintain `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/STATE.md` plus append-only
`EVENTS.jsonl` **in the integration worktree**, committed and pushed at every packet close so
nothing lives only in a worktree that could be pruned.

`STATE.md` carries: `Accepted N/22` + per-asset state columns (producer / data / integrated /
deployed / value); Phase-0 scorecard; packet table (id, owner, worktree, branch, status, exit
evidence, next action); active leases; observed SHAs and revisions; open blockers with owner;
budget consumed.

Each `EVENTS.jsonl` line: `{ts, packet, event, sha, evidence_ids, result}`. Events are
append-only. Never rewrite one to make a story cleaner — if an earlier attempt was wrong, add
the correction as a new event (this project's §N.8 discipline, and Pūrṇa's own practice).

## 7. Authority, guardrails and the forbidden list

**You are authorized** to: implement, test, benchmark on disposable databases; create
worktrees and branches; commit, push, open PRs; **merge to protected main through the merge
queue**; **dispatch the protected deploy workflow**; claim/release coordination leases;
materialize L0→L1→L2 generations and build L3 assets for the canonical chart; regenerate
generated artifacts through their real generators.

**Never, under any circumstance:**
1. Force-push, delete a branch, or `git reset --hard` anything you did not create tonight.
2. Delete or prune a worktree with unpushed commits. Push first, always.
3. Edit an applied migration (1033–1041). Author a reviewed successor in range **1070–1119**.
4. Touch `.github/workflows/deploy.yml`, the data-plane/Pūrṇa ownership scripts, or anything
   in Codex's delivery territory. That gate stabilized eight hours ago; it is not yours.
5. Merge any Pūrṇa PR (#2597–#2605, #2676, or any `codex/purna-*`). Do not merge **#2655** —
   it is superseded; close it.
6. Weaken, skip, or bypass a gate, guard, test, or required check to obtain green. If the L2
   cross-layer delete guard blocks you, that is the guard working.
7. Rebuild `ka_gochara_sweep` or touch its retained snapshot/history.
8. Touch the `WATCHDOG_SECRET` incident or revision `amjis-web-02826-huf`. Human-owned.
9. Change `WriterBase`/orchestrator contracts, doctrine, product definition, or open L4/L5.
10. Claim an asset accepted without an authenticated terminal/freeze event. No direct SQL
    terminal-event insert. No builder self-certification.
11. Run two release operations at once, or begin production mutation while a conflicting
    lease is active.
12. Print a credential, connection string, or private chart narrative anywhere.

**Anti-stall rules** (these exist because the previous conductor produced 37 `heartbeat-idle-*`
branches spinning against a closed gate):
- Every packet names **one next executable action** and the asset acceptance condition it advances.
- At most **two identical transient retries**. A repeated deterministic failure gets **one**
  root-cause packet, not a third attempt.
- CI takes 6–14 minutes here. That is not a stall. Thresholds: soft-wait 15 min, hard-stall 20,
  confirmation 5, and require two observations of the **same SHA and same job/step fingerprint**
  before classifying a stall. Never cancel a healthy protected run. You may reuse
  `platform/scripts/ci/merge_queue_supervisor.ts` — it is a read-only classifier built for
  exactly this and has no cancel/merge/dispatch authority.
- If a packet is blocked by something structural, mark it `BLOCKED_STRUCTURAL(<gate>)`, **stop
  that cone**, and move to another. Do not generate adjacent busywork to appear productive.
- If genuinely no eligible work remains, write the honest blocker and resumable next action and
  **stop**. An honest stop beats manufactured activity.
- Time-box any single packet to **90 minutes** without a working increment; then reduce scope
  or switch to an executable reproduction.

## 8. Budgets (2× estimate, as authorized)

| Resource | Budget |
|---|---|
| Wall clock | 8–10 h unattended |
| Concurrent implementer agents | 5 |
| Total subagent dispatches | **80** |
| Worktrees created | **12** |
| PRs opened | **15** |
| Merges to main | **12** |
| Deploy dispatches | **4** |
| Production mutation operations (W1) | **2** (L1, L2) |
| Native Surrogate invocations | **10** |
| Disposable DB instances | **6** |
| Identical retries | 2 per failure, hard |

Budgets are ceilings, not targets. Spending the whole dispatch budget with `Accepted 0/22` is a
failure; closing two assets on half of it is success.

## 9. Morning report — write this to the state file and print it

1. **`Accepted N/22`**, delta from 0, and the newly accepted asset IDs with their freeze event ids.
2. **Phase-0 scorecard** — kept strictly separate from item 1.
3. **Evidence, separated by kind**: source (PRs merged) · data (generations/partitions accepted)
   · deployed (actual ready revisions + env SHAs you read yourself) · consumer (value tests).
4. **What is blocked, by whom, and the exact next action** — including anything needing the native.
5. **Decisions the Native Surrogate made**, with rationale, so they can be overridden.
6. **Budget consumed** vs §8.
7. **Anything surprising** — especially any evidence that contradicts this prompt.
8. **Cross-campaign**: any `L3-REQ`/`PA-REQ` interlock items; whether E3/E4 lit Pūrṇa SCUs;
   re-surface the `WATCHDOG_SECRET` item as still human-owned.

Truthfulness outranks progress. A night that closes zero assets and reports exactly why is
worth more than one that closes two and cannot prove it.
````

---

## §C — Satellite session prompts (optional extra parallelism)

The conductor already parallelizes internally. Run these only if you want more throughput in
separate terminals. Each is territory-disjoint from the others and from the conductor's
critical path. **Do not start any satellite until the conductor confirms Packet A1 is done** —
they depend on the branches existing on origin.

**Satellite 1 — Salvage (Wave D, groups G2–G5).** Worktree `/Users/Dev/madhav-l3/salvage`.
> Take Packets D2, D4, D5, D6 from `00_ARCHITECTURE/briefs/nirmana/MADHAV_L3_AUTONOMOUS_EXECUTION_PACKAGE_v1_0.md` §B.3 Wave D. Work only in your own worktree. Branch each off current `origin/main`, re-apply the reviewed change from the named source branch, re-review and re-run tests on today's main — the old green is history, not evidence. One branch per packet. Open a PR each; do not merge your own. Obey the forbidden list in §B.7. Report per packet: branch, PR, tests run, evidence, next action.

**Satellite 2 — Triage + dossiers (D7, C2 field contracts).** Read-only worktree.
> Produce the branch-triage disposition record for ~113 unmerged L3 branches per §B.3 Wave D (D7) and the dual-campaign plan Appendix B, and the field-contract dossiers for the four service identities (`ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva`, `ka_tulana`) against the 699-field W0 register. Read-only: never delete a branch, never merge. Close PR #2655 as superseded (do not merge it). Deliver two versioned artifacts.

**Satellite 3 — Governance (Wave B).** Worktree `/Users/Dev/madhav-l3/governance`.
> Execute Packets B1, B2, B3 from §B.3 Wave B. Docs-only; safe to merge. Copy the four governing documents from `codex/madhav-data-plane-strategy` — never merge that branch (627 stale runtime files). Author DP-SD-021 from the dual-campaign plan Appendix C under the native authorization recorded there.

**Conflict rule for all satellites:** if you need a file outside your territory, stop and log
an interlock request in the state file. Do not reach across.

---

## §D — How we work from here

I stay the strategy session: I do not execute packets. Overnight the conductor runs. In the
morning bring me the report and I will re-verify its claims independently against GitHub,
Cloud Run and the coordination ledger — the same way I caught that the handoff's seven
"preserved" commits were all stranded, and that four green deploy runs had shipped nothing.

Then we re-plan Phase 2 from measured reality: the W2 frontier ordered by any `L3-REQ`
interlocks Pūrṇa raises, the performance programme, and the century-materializer hold decision.

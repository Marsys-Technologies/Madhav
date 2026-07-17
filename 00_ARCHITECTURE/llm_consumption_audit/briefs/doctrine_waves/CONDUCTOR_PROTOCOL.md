---
artifact: DOCTRINE_WAVES_CONDUCTOR_PROTOCOL
type: STANDING PROTOCOL (governs every wave conductor D-1.5a → D-4)
version: 1.4
status: CURRENT
authored_by: Fable 5 (Claude Code planning session, 2026-07-15), native-directed
governing_plan: 00_ARCHITECTURE/DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md (v1.1 FINAL)
native_directives:
  - Fully autonomous execution, bypass permissions, NO human gates. Human-intervention questions
    are handled by the Adjudicator agent (§4); certain classes PARK instead (§4.3).
  - Implementation model = Sonnet (cockpit default). Escalation to Opus/Fable per the model
    matrix (§5) is pre-approved by the native (2026-07-15).
  - Every wave: isolated environments → implement → verify → merge → deploy → rebuild →
    MCP-verify through the MARSYS-JIS connector → cleanup → next wave. A wave is DONE only when
    its MCP gate battery is green on the deployed connector (R-5).
  - REBUILD POLICY (native directive 2026-07-15): rebuilds target ABHISEK'S CHART
    (482012f1) ONLY, and are SCOPE-LIMITED to the layers the wave's writers touch — never
    full-by-default. A full L1→L5 rebuild happens only when the Binder rules it required (§8.2).
    Abhinandan (1c826d5a) is NOT rebuilt by the campaign; its existing prod build is read-only
    reference for the CR-87 divergence check only.
---

# Doctrine-Waves Conductor Protocol

## §0 — What this document is

The standing operating system for the D-1.5a → D-4 autonomous campaign. Each wave's conductor is a
FRESH session that reads exactly **five** things: **this protocol**, **`ESCALATION_POLICY_v1_0.md`**
(decision routing — which pauses auto-proceed, which route to the Adjudicator, which halt for the
native), **`ADJUDICATOR_CHARGE_v1_0.md`** (the standing judgment the in-session Adjudicator applies),
**its wave's bound brief** (BRIEF_D*.md in this directory), and **the previous wave's close report**
(`REPORT_<wave>.md` — the close artifacts are named `REPORT_*`, not `CLOSE_*`). No conversation-memory
handoff — artifacts only. The conductor executes the §2 lifecycle deterministically; verification is
structural, not a norm.

**Precedence (added v1.4):** where `ESCALATION_POLICY_v1_0.md` and this protocol disagree —
retry/PARK arithmetic, the auto-proceed set, the model+effort matrix, ceilings — **ESCALATION_POLICY
governs** and the named protocol sections are read as amended. Everything ESCALATION_POLICY does not
touch, this protocol governs verbatim.

## §1 — Roles

| Role | Model | Duty | Hard rule |
|---|---|---|---|
| **Conductor** | Sonnet (cockpit) | Runs the §2 lifecycle; spawns all agents; owns the wave gate | Accepts ONLY verifier receipts. An implementer's "done" is a claim, never an acceptance. Merges nothing unverified |
| **Binder** | **Fable** | At wave open: resolves every BIND-AT-OPEN slot in the brief against live state (fresh MCP probes + prior close report); stamps brief `BOUND` | A wave with unbound slots does not spawn implementers |
| **Implementer** (per lane) | Sonnet | Builds in an isolated worktree; writes unit tests; final message = claim + self-test evidence | Never verifies own lane. Never touches paths outside its lane's `may_touch` |
| **Verifier** (per lane, fresh context) | **Opus** | Phase-1 verification (§3): independent diff review vs lane brief, runs the tests itself, runs the lane's assertion-script subset, runs the scope-warden check | Issues a RECEIPT (§3.2) or a REJECTION with diagnosis. Never edits code |
| **Gate runner** | Opus (D-1.5/D-3/D-4); **floor-model Sonnet for D-2's synthesis gate** | Phase-2 verification (§3): post-deploy, executes the wave's full MCP battery against the deployed connector | Reports the red list plainly. Cannot be overridden by the conductor |
| **Adjudicator** | Fable (doctrine) / Opus (engineering) | Answers questions that would otherwise need the native (§4) | Doctrine rulings recorded as DR-n with delegation provenance |
| **Anti-gaming verifier** (D-3/D-4 only) | Opus | Adversarially checks statistical gates: degenerate curves, base-rate artifacts, threshold gaming vs the negative controls | A statistical gate without an anti-gaming pass is not green |
| **Migration guard** | Opus | Reviews every SQL migration pre-apply: destructive ops, idempotency, numbering (SINGLE directory — `platform/migrations/`; the 434-in-supabase split is the known failure) | A migration without a guard receipt does not apply |

**§1.1 — Binder remit is READ-ONLY beyond its two designated output files (standing rule, added
D-1.6 Lane S-8, 2026-07-16).** The Binder's job (per its role row above) is to *resolve* BIND-AT-OPEN
slots against live state — it probes, it does not implement. Its write remit is exactly two files per
wave: the `BIND_<wave>.md` findings record and the brief's `BOUND` status stamp. **Two recorded
incidents** of planning-role (Binder/Fable) writes landing outside that remit have occurred across
the campaign to date (see `BIND_D-1.6.md`'s own binder_notes: "the CONDUCTOR_PROTOCOL read-only-
enforcement note is S-8's to write — NOT written by this Binder pass... two prior incidents of
planning-role writes are exactly why"). **The structural fix is tool-access restriction, not a
process reminder**: a Binder session should not be granted `Write`/`Edit` access to any path outside
`{BIND_<wave>.md, the brief's status frontmatter field}` — the same class of fix this protocol already
applies to lanes via the scope-warden check (§3, Phase 1(d)). Until tool-access scoping is wired into
the Binder's harness invocation, this is a **process-level standing rule**: a Binder pass that touches
any other file (a register, a governance doc, another brief, CURRENT_STATE, CONDUCTOR_PROTOCOL itself)
is a protocol violation to flag in the wave's close report, exactly as a lane implementer touching a
path outside its `may_touch` globs is a scope-warden REJECTION (§3(d)). Conductors should treat a
Binder diff outside `{BIND_<wave>.md, brief frontmatter}` as a red flag requiring investigation before
the wave proceeds to SPAWN.

## §2 — Wave lifecycle (deterministic; run in order; no step skippable)

1. **OPEN** — conductor reads protocol + brief + prior close report. Binder resolves all
   BIND-AT-OPEN slots (fresh MCP probes; never trust cached/register state older than the last
   deploy — the estate has changed same-day before). Brief stamped `BOUND`. Rollback pin recorded:
   current deployed image SHA + build_id per chart.
2. **SPAWN** — one worktree + branch per lane (`wave/<wave>/<lane>`); implementers launched in
   parallel per the brief's lane map. Lanes with declared sequencing (e.g. A1→A2 inside one lane)
   run inside a single agent.
3. **IMPLEMENT ∥ VERIFY (per lane)** — implementer claims done → verifier runs Phase-1 (§3.1).
   REJECTION → back to implementer with diagnosis, max **3 attempts**, then the lane PARKS (§4.3)
   and the wave proceeds without it if the gate permits, else the wave reports blocked.
4. **INTEGRATE** — receipted lanes merge to the wave integration branch in the brief's declared
   merge order; conductor runs the full test suite + a Phase-1 assertion sweep on the integrated
   branch (catches cross-lane interference). Regression → the offending lane re-opens (counts
   toward its 3 attempts).
5. **DEPLOY** — integration branch → main → deploy. **Only one wave deploys at a time, ever**
   (parallel tracks 2/3 never touch the deployed estate). Migrations apply only with guard receipts.
6. **REBUILD** — Abhisek's chart (482012f1) rebuilt via the orchestrator, SCOPE-LIMITED per the
   Binder's ruling (§8.2); build-health check (touched assets lit, FORENSIC 7/7, 0 orphan refs,
   row-count census sane). Abhinandan is not rebuilt.
7. **GATE** — gate runner executes the wave's full MCP battery against the deployed connector,
   plus the wave's final proof. Red list → conductor triages: lane re-open (→ step 3) or PARK +
   report. **The wave closes only on all-green** (parked items must be explicitly excluded by the
   brief's gate as non-blocking, else the wave stays open).
8. **CLOSE + CLEANUP** (verified like any lane) — worktrees/branches removed; brief stamped
   `COMPLETE` (or left `ACTIVE` with the red list — never falsely stamped); close report written
   (template §7); SESSION_LOG entry; register status updates; CURRENT_STATE pointer; rollback pin
   advanced; state ledger (§6.1) marked complete. A wave without a close report did not close (the
   D-1 lesson).

## §3 — Two-phase verification (the fix for D-1's failure)

**Phase 1 — pre-merge, per lane (verifier agent):**
(a) diff review against the lane brief's deliverables; (b) verifier runs the test suite itself —
implementer-reported test results are not evidence; (c) runs the lane's subset of the wave's
**executable assertion harness** (see D-1.5a Lane A-0 — assertions are scripts hitting the MCP/
serving layer, never prose); (d) **scope-warden**: `git diff --stat` touches only the lane's
`may_touch` globs — any stray path is an automatic REJECTION regardless of code quality.

**Phase 2 — post-deploy, per wave (gate runner):** the full battery on the DEPLOYED connector
after rebuild. Phase 1 merges a lane; only Phase 2 closes a wave. Three of D-1's four failures
lived in the deploy/wiring layer that Phase-1-style checks can never see.

**§3.2 Receipt format (machine-checkable, attached to the merge):**
`{lane, verifier_model, diff_reviewed: sha, tests: {run, passed, failed}, assertions: {script, green: [...], red: [...]}, scope_warden: pass|fail, verdict: ACCEPT|REJECT, diagnosis?}`

## §4 — Adjudicator (the human-proxy)

**Routing is governed by `ESCALATION_POLICY_v1_0.md`; the Adjudicator operates under
`ADJUDICATOR_CHARGE_v1_0.md` (added v1.4).** This §4 defines the seats and PARK classes; ESCALATION
decides which decisions reach the Adjudicator (its §1), which auto-proceed (§0), and the three that
halt-and-report for async native review (§2). On any disagreement of routing or retry/PARK arithmetic,
ESCALATION governs (see §0 precedence).

**§4.1 Routing:** doctrine-class questions (valence semantics, classical rules, interpretation,
anything citing śāstra) → **Fable**, recorded as `DR-n (Fable by native delegation, <date>)` in the
DISAGREEMENT_REGISTER, queued for native ratification at campaign close. Engineering trade-offs
(schema shape, retry strategy, sequencing, library choice) → **Opus**, recorded in the wave close
report. When in doubt about which class → Fable.

**§4.2 Contract:** the asking lane provides the question + options + its recommendation; the
adjudicator answers with a ruling + one-paragraph rationale; the ruling binds for the campaign.

**§4.3 PARK classes — never auto-adjudicated, no exceptions:**
1. FROZEN orchestrator contract changes (CLAUDE.md §N.2 — "STOP and raise with the native").
2. Destructive/irreversible data operations outside the idempotent delete-then-insert pattern.
3. Anything inside a brief's `must_not_touch`.
4. A lane at 3 failed verification attempts.
PARK = lane branch preserved, diagnosis written to the close report's PARKED section, wave routes
around it. Parked items are the FIRST agenda item of the next native session.

## §5 — Model matrix + circuit breakers

**Models:** Sonnet = implementation, conductor. Opus = all verifiers, gate runners, migration guard,
adjudicator-engineering, hard debugging (an implementer stuck twice may be respawned as Opus — this
counts as escalation, not a new attempt-counter). Fable = binder, adjudicator-doctrine, and D-2's
brief-slot design work. **D-2 synthesis gate runs on Sonnet deliberately** (floor-model rule: if the
weakest production model reaches 6/6 from served surfaces, the instrument — not the model — is
doing the work).

**Circuit breakers:** per-lane: 3 verification attempts, then PARK. Per-wave: if >50% of lanes park,
the wave halts and reports (the brief was probably mis-bound — re-run the Binder). Deploy: any
build-health failure (step 6) → immediate rollback to the pinned image + report; no forward-fixing
on a corrupted estate. Time/budget ceilings per the brief's frontmatter. The one unbreakable rule:
**a red gate is reported red. A half-passed gate stamped complete is the exact failure this
protocol exists to prevent.**

## §6 — Resilience & resumption (API-glitch / crash recovery)

**Design rule: all campaign state lives in FILES AND GIT, never in conversation memory.** A wave
must be resumable by a brand-new session at any lifecycle point with zero information loss.

**§6.1 The wave state ledger.** The conductor maintains
`briefs/doctrine_waves/STATE_<wave>.md` (committed at every transition), a small YAML block:
`{wave, lifecycle_step: 1-8, brief_bound: bool, rollback_pin: {image_sha, build_ids},
lanes: [{lane, branch, status: pending|implementing|verifying|receipted|rejected(n)|parked|merged,
receipt_ref}], deploy: {done, sha}, rebuild: {scope, abhisek_build_id|pending}, gate: {run, green: [...],
red: [...]}, updated_at}`. **Every lifecycle transition = update ledger + commit.** The commit IS
the checkpoint; an uncommitted transition did not happen.

**§6.2 Re-entry procedure (run at EVERY conductor session open, first thing):**
1. Read `CLAUDECODE_BRIEF.current_wave` → read `STATE_<wave>.md` (if absent → fresh OPEN, §2.1).
2. Reconcile ledger vs reality — never trust the ledger blindly: `git branch --list 'wave/*'`
   (which lane branches exist, their last commit), receipts present?, deployed image SHA vs pin,
   build status per chart, and if `gate.run` — re-run the battery (cheap, idempotent) rather than
   trusting recorded results.
3. Resume at the FIRST step whose completion cannot be verified. In-flight lane work: a lane branch
   with commits but no receipt → respawn the VERIFIER first (the work may be done); a lane branch
   with no commits → respawn the implementer fresh in the same worktree/branch.
4. Log the resumption (ledger `resumed_at` append) and continue the lifecycle.

**§6.3 Idempotency requirements per step** (what makes §6.2 safe):
- Every lifecycle step must be re-runnable: binding (re-probe is harmless), spawn (worktree/branch
  create is check-first), merge (already-merged lane detected via git), deploy (re-deploying the
  same SHA is a no-op), rebuild (delete-then-insert per §N.3 — re-running heals partial builds;
  the ka_sangam substep-resumption ledger, migration 436, resumes long builds), gate (pure reads).
- Migrations: idempotent by project convention; the migration guard verifies IF NOT EXISTS /
  ON CONFLICT discipline before apply, so a re-applied migration is safe.
- The assertion harness is pure-read MCP and always safe to re-run.

**§6.4 Transient-failure handling (API glitches, network, 5xx):**
- All agents (implementers, verifiers, gate runner): on a transient tool/API failure, retry with
  backoff (3 attempts: ~10s/60s/300s). A transient failure NEVER counts as a verification attempt
  (§5's 3-attempt counter is for substantive rejections only).
- MCP-call failures in the harness: distinguish TOOL-ERROR (counts as red) from TRANSPORT-ERROR
  (retry; if the connector stays unreachable >15 min, record `gate: blocked_infra` in the ledger,
  commit, and end the session cleanly — the next session re-enters via §6.2 and re-runs the gate
  when the connector is back; "connection restored" is detected by the re-entry probe itself).
- A subagent that dies mid-task: its worktree/branch survive; the conductor respawns per §6.2.3.
- The conductor session itself dying is the DESIGNED-FOR case: §6.1's committed ledger makes any
  new session (including a scheduled/cron re-launch) a full-fidelity resume. Recommended: launch
  waves under a supervisor loop that restarts the conductor session on exit until the ledger shows
  `lifecycle_step: 8` complete or a PARK/blocked state that needs the next wave or native review.

## §7 — Close report template

`{wave, brief_version_bound, lanes: [{lane, verdict, receipt_ref}], parked: [{lane, diagnosis}],
gate: {assertions_green, assertions_red, final_proof}, deploy: {image_sha, build_ids}, adjudications:
[DR-n / eng], register_updates, rollback_pin, next_wave_bind_notes}` — written to this directory as
`CLOSE_<wave>.md`, appended to SESSION_LOG.

## §8 — OPERATIONS APPENDIX (repo-verified mechanics; the plumbing every agent needs)

GCP project `madhav-astrology`, region `asia-south1`. Cloud Run services: `amjis-web`,
`amjis-sidecar`, `amjis-mcp`; Cloud Run Job: `brahma-build-pipeline-job`. Canonical chart UUIDs
(FULL — never truncate in scripts): Abhisek `482012f1-710e-4a25-994a-93821f5871aa`, Abhinandan
`1c826d5a-41cb-4450-b4dc-59d440e5f75a`. Ayanamsha: `lahiri_chitrapaksha`.

**§8.1 Deployed-MCP access (the gate channel).** Config: repo `.mcp.json` → `marsys-jis` at
`https://amjis-mcp-qm256lasva-el.a.run.app`, `Authorization: Bearer ${MARSYS_MCP_KEY}`; the key is
exported by `source scripts/setup_mcp_env.sh`. Transport: stateless JSON-RPC, **POST /mcp** only.
Scripted precedent: `platform/scripts/audit/tap/mcp_tool_smoke.ts` LIVE mode
(`MCP_SERVER_URL=https://<host>/mcp MCP_SMOKE_BEARER_TOKEN=... npx tsx <script>`) — the harness
follows this pattern. **RULING: `marsys-jis-direct` (the `?api_key=` seat in `~/.claude.json`) IS
the same deployed Cloud Run service** — either face satisfies R-5's "deployed connector"; the
harness uses the Bearer face for reproducibility. (Hygiene: both prod keys are committed in
plaintext — rotation is a campaign-close checklist item, NOT a lane task.)

**§8.2 Chart rebuild.** `POST /api/cockpit/runs` with `{chart_id, scope, scope_target?, action,
clear_before?}` (`scope ∈ global|layer|asset|asset_set`; `/api/build/start` is 410-gone). 409 =
active run exists (wait, don't force). Dispatches `brahma-build-pipeline-job` with
`--run-id <build_runs.id>`. Manual/local equivalent: `cd platform/python-sidecar && python -m
pipeline.orchestrator.main --run-id <id>` (exit 0 clean / 2 not-found / 3 chart-locked / 1 fatal).
**Completion/status:** `GET /api/cockpit/status` (running|idle) + `GET /api/cockpit/stats`
(per-asset lit|building|error — authority is `asset_registry.count_sql`, NEVER `asset_throughput` —
the L1 trap). **Rebuild TARGET = Abhisek (482012f1) ONLY** (native directive 2026-07-15) — pass
`chart_id=482012f1-710e-4a25-994a-93821f5871aa`, `scope=layer`/`asset_set` with `scope_target` set
to the touched layers. **SCOPE = the minimal layer set the wave's merged writers touch + any layer
that ingests their outputs — NOT full-by-default.** A FULL L1→L5 rebuild is required ONLY when the
Binder finds one of: (a) a new L1 fact category a downstream layer ingests (e.g. D-1.5b chalit
facts → MSR; SAV re-key → L3); (b) a change to shared substrate every layer reads (valence pass,
Mechanism object, convergence kernel); (c) a migration altering an existing column's semantics
(not additive). The Binder records `{scope, layers, full: bool, rationale}` in the ledger at open;
absent a trigger, rebuild only the touched layers.

**MINIMAL-CASCADE RULE (native-ratified 2026-07-15 — rebuild scope is the primary time lever).**
Prefer the NARROWEST rebuild the DAG permits: rebuild the *changed assets* + only their *actual
downstream dependents* (computed from `asset_registry` depends-on edges), NOT a whole-layer sweep,
and NOT full-by-default. `scope=asset_set` with an explicit `scope_target` asset list is preferred
over `scope=layer` whenever the changed set is a strict subset of a layer. Only the three triggers
above force `full`. Rationale: rebuild wall-clock is the campaign's dominant serial cost; every
asset not in the true cascade is wasted time. The Binder computes the minimal set at open and
records it; a rebuild broader than the DAG requires is a defect to flag, not a safe default.
(A DEP-ASSERT during rebuild means the target set was too narrow — expand to the asserted
dependents ONLY, not to the whole layer — corroborated live this session: D-1.5a's first
narrow-scope rebuild attempt hit exactly this and required expanding to the full 46-asset
closure via `asset_registry.depends_on`.)

PROVENANCE NOTE (2026-07-15, D-1.5a session): commit 55209dd1 introduced this v1.2 changelog
entry labeled "(native-ratified)"; as with the earlier e8fba6ed rebuild-policy commit, this
session has no direct record of native ratification for THIS specific commit at the time it
was made — flagging per the same CLAUDE.md B.8 audit-trail-honesty standard, not reverting,
since the RULE independently and correctly matches this session's own live debugging findings.

**Per-wave expected scope** (Binder confirms/refines against the live DAG at open):
- **D-1.5a** = L1 detectors + L2 MSR (valence is shared substrate but only MSR consumes it).
- **D-1.5b** = **full L1→L5** — the ONE genuinely-full wave (new chalit/AV/bhava-bala fact
  categories feed MSR + L3 — trigger (a)); no narrowing available.
- **D-2** = the Mechanism/CGM/vidhi asset_set + MSR re-rank consumers — L2/serving, NOT a full L3+.
- **D-3** = L3 convergence assets + the Taraṅga service; L2 read-only (no L2 rebuild).
- **D-4** = L5 calibration assets ONLY — expected to be the fastest rebuild (minutes), never a
  cascade beyond L5.

Long builds resume via the migration-436 substep ledger — re-dispatching a dead run is safe.
**Abhinandan (1c826d5a) is never rebuilt by the campaign.**

**§8.3 Deploy.** Merge mechanism: PR to `main` via `gh pr create` + merge (repo convention is
PR-based; direct push only if PR flow is unavailable). Deploy is NOT push-triggered: CI **"CI —
Ganga Quality Gate"** must pass on `main`, then `deploy.yml` fires via `workflow_run` (web always;
sidecar/mcp/pipeline-job only when their paths changed — note: a wave changing only
`python-sidecar` still re-points the pipeline job image). Watch: `gh run list --workflow=deploy.yml`
+ `gh run watch <id>`. Smoke + traffic promotion are inside the workflow. **Live-SHA verification**
(no runtime version endpoint exists): `gcloud run services describe amjis-web --region=asia-south1
--format='value(spec.template.spec.containers[0].image)'` — image tag = git SHA; same for
`amjis-mcp`; job image via its describe. Emergency path: `workflow_dispatch` (bypasses CI — use
only for rollback-class fixes with Adjudicator-engineering sign-off).

**§8.4 Rollback pin + rollback.** Pin at wave open (ledger §6.1): the three images' SHAs (per
§8.3 describe commands) + Abhisek's current `build_id` (from any tool's `chart_header`/provenance).
Rollback: `gcloud run services update-traffic <service> --region=asia-south1
--to-revisions <prev-revision>=100` (list revisions via `gcloud run revisions list`), plus job
image re-point back to the pinned tag; then re-run the previous wave's gate battery to confirm
estate restoration. DB state needs no rollback (idempotent rebuilds heal; migrations are additive
by convention — a migration needing destructive rollback is a PARK-class event).

**§8.5 Migrations (surgical, per CLAUDE.md §N.4).** Never bulk-replay. Procedure: start the Cloud
SQL Auth Proxy (`platform/scripts/start_db_proxy.sh`), then `cd platform && DATABASE_URL=... npx
tsx scripts/migrate.ts --dry-run` (confirm EXACTLY the expected pending files) → `npx tsx
scripts/migrate.ts --target <NNN_name.sql>` one file at a time, each with a migration-guard
receipt. New migrations: `platform/migrations/` ONLY, scaffolded via the `create-migration` skill.
Note the deploy workflow also auto-runs migrate.ts — therefore migrations must be merged only
in the same integration branch as their consumers, and the guard receipt is what makes the auto-run
safe (idempotent, IF NOT EXISTS discipline verified pre-merge).

**§8.6 Test commands (what "verifier runs the tests itself" means).**
- Python sidecar: `cd platform/python-sidecar && pytest tests/ --ignore=tests/test_pyjhora_adapter
  --ignore=tests/test_dasha_chain.py --ignore=tests/extractors/test_cgm_extractor.py
  --ignore=tests/test_l0_remedy_corpus.py -m "not integration" -q --tb=short` (no DB needed).
- Platform TS: `cd platform && npm test` (vitest) + `npx tsc --noEmit --skipLibCheck` + `npm run lint`.
- MCP TS: `cd platform-mcp && npm test` + `npx tsc --noEmit`.
- Governance: `python platform/scripts/governance/drift_detector.py` (exit 0 or 3 = pass) +
  `schema_validator.py` (exit 0). Full local gate = the `run-checks` skill.
- "Full test suite" at integration (lifecycle step 4) = all of the above.

**§8.7 Build-health check (lifecycle step 6, concrete; Abhisek only).** After rebuild: (a)
`/api/cockpit/stats` — every asset the wave touches `lit`, zero `error`; (b) FORENSIC 7/7 via
`ganita_natal_positions_compute` (Sun Capricorn · Moon Purva Bhadrapada · Lagna Aries 12.4311° ·
Shukla Tritiya · Ravivara · Shiva · Garaja on 482012f1); (c) DEFECT-001 orphan check = 0 via
`bodha_signals_get` provenance; (d) L1 canonical row counts within ±1% of L1_GANITA_CLOSURE values
(chart_facts 27,554 · chart_dashas 536,471 · chart_divisionals 21,635 for 482012f1) unless the
wave's brief declares expected deltas (new fact categories change these — Binder records the new
expected counts at open). The harness implements this as `health` assertions.

**§8.8 Standing conductor rules (gap-review adoptions).** (i) **Prior-battery-red at open:** if a
previous wave's battery has gone red at wave open (estate drift), file a regression incident,
route to Adjudicator-engineering, do NOT spawn lanes until dispositioned. (ii) **DR-n allocation
and register edits are conductor-only** — lanes request, conductor writes (prevents numbering
collisions and keeps the register single-writer). (iii) **Wave exit report is written at EVERY
exit** — `REPORT_<wave>.md` with `status: closed|blocked|parked` (a blocked wave with no report is
invisible to the next session); the §7 template applies to all exits. (iv) **Default ceilings**
(unless a brief overrides): wave wall-clock 24h, single lane 6h — ceiling hit = PARK + report, not
silent continuation. (v) After A-0 merges, **the harness's assertion definitions are the canonical
copy** of the gate (register/plan text is provenance; the executable is authoritative — version
skew between them is a defect to fix in the harness).

---
*Changelog: v1.3 (2026-07-16, D-1.6 Lane S-8) — §1.1 added: Binder remit is READ-ONLY beyond
`{BIND_<wave>.md, brief frontmatter status stamp}` — standing rule after 2 recorded incidents of
planning-role (Binder/Fable) writes landing outside remit; structural fix noted as tool-access
restriction (not yet wired), process-level rule in force until then; a Binder diff outside its two
files is a scope-warden-class red flag, same treatment as a lane implementer touching a path outside
`may_touch`. v1.2 (2026-07-15) — §8.2 MINIMAL-CASCADE RULE (native-ratified): rebuild the narrowest
DAG cascade — changed assets + actual dependents via asset_set, never full-by-default; only the
three triggers force full; per-wave expected scopes tightened (D-1.5b is the sole full wave; D-4 =
L5-only minutes). Rebuild scope is the primary time lever. v1.1 (2026-07-15) — resilience §6 (state
ledger, re-entry, idempotency, transient-failure handling), OPERATIONS appendix §8 (repo-verified
deploy/rebuild/migration/test/MCP-access/rollback/health mechanics), §8.8 standing rules from the
adversarial gap review.
v1.0 (2026-07-15) — initial protocol per native directives (autonomous, swarm-verified,
Sonnet-primary with pre-approved escalation).*

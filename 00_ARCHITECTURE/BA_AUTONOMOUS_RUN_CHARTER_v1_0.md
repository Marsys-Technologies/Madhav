---
canonical_id: BA_AUTONOMOUS_RUN_CHARTER
version: 1.0
status: READY — governs the single-kickoff autonomous execution of the Beyond-Acharya unified program
created: 2026-07-03
author: Cowork (strategic workstream, Claude Fable 5) — ratified execution mode per native directive 2026-07-03
native_directive: >
  "The entire plan executed autonomously without interruption or human gates, sub-agent driven, conductor
  technology, one kickoff, worktrees, thorough spec verification by a dedicated swarm, dedicated
  human-proxy agent for all native-judgment calls (the swarm is closer to the domain and the data), merge
  to main, push, deploy to production, clean up." Precedent: AUTONOMOUS_MODE §F + the Brahma V1.3 waves +
  BUILD_GUARANTOR_SWARM_CHARTER — with the seal-vs-prod divergence scar encoded as Ring-2 law.
governing_stack: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN v1.0 (sequencing+gates, §V.2 grounded) →
  BA_MASTER v2.x (asset delta) → RETRIEVAL_MODERNIZATION v1.0 (serving substance) → MIMAMSA_V2 v1.0 (L5) →
  BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE v1.0 (the judgment constitution) → BA_GROUNDING_REPORT v1.0 (facts).
scope_of_run: P1 → P7 (P0 COMPLETE pending its final prod AC, which this run's first act re-verifies;
  P8 research organs EXCLUDED — corpus-gated). One kickoff; no scheduled human gates; native may
  interrupt at will but nothing WAITS on him.
---

# BEYOND-ACHARYA AUTONOMOUS RUN — CHARTER v1.0

## §1 — TOPOLOGY (conductor + swarm)

- **CONDUCTOR** (the kickoff Claude Code session): owns the phase train, spawns all agents, owns the merge
  train + promotion points, and executes the NINE pre-authored standalone root briefs
  (`CLAUDECODE_BRIEF_BA_P1_*` … `BA_P7B_*` — Cowork-authored substance, FROZEN; the conductor fills only
  each brief's ⟦SLOT⟧ fields from prior-phase close reports before starting it; the Spec-Auditor's
  Brief-Audit gate validates the slot-fill, never re-authors substance). Maintains the RUN LEDGER
  (`00_ARCHITECTURE/BA_RUN_LEDGER_v1_0.md`: phase status, SHAs, gate results, judgment refs).
- **PHASE EXECUTORS** (sub-agents, one per phase-lane, each in its own worktree/branch `wt/ba-p<N>[-lane]`):
  implement their brief, self-test, hand to verification. Parallel lanes only where the plan allows
  (P5A∥P5B, P7A∥P7B, P4-tail∥P5).
- **ĀCĀRYA-PRATINIDHI (the native-proxy / domain-judgment agent — dedicated, persistent).** Handles EVERY
  call the plans mark native/judgment: prior-tuning decisions (P2 loop), constants dispositions, deferral
  rankings, adjacency rulings in the ontologies, golden-answer adjudication, the second key on two-key
  publications, E4 ranking. Its CONSTITUTION (binding, in priority order): (1) the committed W1 seed
  package; (2) the Ranking Doctrine + §2.1/§2.2 commitments; (3) classical sources in the L0 corpus
  (cite when ruling); (4) mainstream-position-with-`contested`-flag when traditions disagree (L5
  adjudicates later). EVERY ruling → the **JUDGMENT LEDGER**
  (`00_ARCHITECTURE/BA_JUDGMENT_LEDGER_v1_0.md`: decision, basis, alternatives considered, reversibility,
  consumer). The native reviews retrospectively; any veto → a targeted correction wave, never a blocked run.
- **VERIFIER SWARM (dedicated; no member verifies work it authored):**
  1. **Spec-Auditor** — implementation vs brief ACs + governing-stack conformance; audits conductor-authored
     briefs BEFORE execution (Brief-Audit gate: scope ⊂ plan, ACs tagged, grounding cited).
  2. **Prod-Guarantor** — owns Ring 2: deploy truth (revision SHA = merged HEAD, CDN wait), prod probes,
     baseline non-regression. THE V1.3-scar owner: no phase is "done" on worktree evidence.
  3. **Astro-Examiner** — the domain verifier: runs the golden-question eval (blind rubric) at every phase
     close per §2.1-3; checks reasoning-chain outputs against classical expectations (does the career
     top-10 read like an acharya's shortlist; are citations real verses; do verdicts carry their dissent).
  4. **Degeneracy-Warden** — distribution gates on EVERY new/changed scoring column (the 2.326672/0.28
     scars); halts the lane on constant-collapse.
  5. **Data-Integrity Guarantor** — FORENSIC 7/7, chart-agnostic contamination, trap-1 authority,
     layer-scope discipline (§2.2-1), post-regeneration fact-resolution.
  6. **Governance-Scribe** — SESSION_LOG/CURRENT_STATE per phase, schema_validator exit=0, brief statuses,
     ledgers current.
  7. **Red-Team** — one adversarial pass mid-run (after P3) + one at terminal close (IS.8 cadence):
     attack the priors (can a nonsense weighting pass the gates?), the eval (can a template answer score
     13/15?), the caps, entitlement, and the JUDGMENT LEDGER's weakest ruling.

## §2 — THE HUMAN-GATE DISSOLUTION TABLE (every former gate → its autonomous replacement)

| Former human gate | Autonomous replacement |
|---|---|
| PR review + merge | Self-merge after Ring-1 PASS (Spec-Auditor + CI green) — AUTONOMOUS_MODE §F precedent |
| P0 final AC sign-off | Prod-Guarantor re-verifies as the run's FIRST ACT (merge #395 if still open, deploy, probe) |
| P2 prior-tuning native veto | Ācārya-Pratinidhi drives the loop under its constitution; full trace in the Judgment Ledger |
| Two-key adhilepa co-sign (P6) | Key-1 = proposing executor; Key-2 = Ācārya-Pratinidhi (distinct agent, logged); native retro-review may revoke any snapshot (versioned, reversible by design) |
| E4 classical-completions ranking | Ācārya-Pratinidhi rules (leverage × classical weight), logged |
| Deferral / exception decisions | Ācārya-Pratinidhi + Spec-Auditor co-sign, logged |
| Deploy authorization | Conductor, strictly after Ring-2 PASS at the promotion point |
| Native review of readings (P4 rubric) | Astro-Examiner blind rubric (3 independent scorings, median) — the native's retro spot-check invited via the run report |

## §3 — WORKTREES, MERGE TRAIN, PROMOTION POINTS

- One worktree per phase-lane; branches `wt/ba-p1` … `wt/ba-p7b`. NOTHING long-lived: each lane merges to
  main at its Ring-1 pass (squash, conventional message, brief ref). No cross-lane contamination
  (branch-isolation rule); recovery by cherry-pick, never force-push.
- **PROMOTION POINTS (deploy to prod + Ring-2):** after P1 · after P2 (serving-only) · after P3 (THE BIG
  ONE: migrations + L0 seeds + L1 EXT builds + L2 regeneration — see §4) · after P4 · after P5 · after P6.
  P7 folds into the P5/P6 promotions it ships with.
- **Cleanup (terminal):** `git worktree prune`, remove `wt/*` + `.claude/worktrees/*` dirs, prune remotes,
  single-branch end-state — the P-1 clean-slate standard restored, disk reclaim reported.

## §4 — THE P3 SPECIAL REGIME (prod data plane; the only phase that rewrites data)

Data plane is ALWAYS prod (localhost-first = code only). Therefore P3 runs under: (1) **pre-P3 snapshot**
of all affected prod tables (chart-scoped dump for both charts + L0 tables; the snapshot-before-rebuild
ruling); (2) migrations applied surgically, one by one, verified in the applied-migrations table;
(3) regeneration via the standard cockpit Build path (never bespoke scripts) for 482012f1 AND 1c826d5a;
(4) Data-Integrity + Degeneracy gates BEFORE the serving swap; (5) rollback plan = restore snapshot +
revert migration set (rehearsed on the test chart first: Abhinandan builds BEFORE the native chart);
(6) HALT-not-improvise on any gate failure.

## §5 — RING ARCHITECTURE (the verification the native demanded)

- **RING 1 — per-lane (blocks merge):** executor self-tests + unit/E2E + Spec-Auditor line-by-line AC
  audit + Degeneracy-Warden on any scoring column + Governance-Scribe validator exit=0.
- **RING 2 — per-promotion (blocks deploy-done):** Prod-Guarantor deploy truth + prod probes of every AC
  tagged `[verify-against: prod]` + latency non-regression vs the P0 baseline + **golden-eval regression
  gate** (Astro-Examiner: score ≥ previous promotion's score; a drop = lane reopened, not excused).
- **RING 3 — terminal (blocks run-close):** full golden set (all query classes, both charts) ≥13/15
  median · 38-topic four-measure matrix GREEN · unified plan §8 north-star tests 1–5 · Data-Integrity
  full sweep · UI/UX check vs the PG visual baseline · Red-Team terminal pass with zero class-1 findings ·
  ledgers complete · CURRENT_STATE + SESSION_LOG sealed · worktrees cleaned · **BA_RUN_REPORT_v1_0.md**
  (the native's retrospective review surface: every phase, every judgment, every gate result, every SHA).

## §6 — HALT CONDITIONS (the ONLY things that stop the run; everything else self-resolves)

1. A writer/brief appears to require a FROZEN-contract or orchestrator/planner change (§N.2 law).
2. A destructive operation outside the whitelist (reverse-citation gate fails).
3. FORENSIC/contamination failure that survives one repair attempt.
4. Golden-eval regression that two tuning iterations cannot recover (protects against confidently-wrong priors).
5. P3 migration or regeneration failure post-rollback.
6. Any prod incident (5xx storm, data corruption signal).
On HALT: checkpoint state to the RUN LEDGER, write a resumption brief, notify the native. The run is
RESUMABLE from checkpoint — a halt is a pause, never a loss.

## §7 — MODEL + SKILLS POLICY

Conductor + executors + verifiers = Claude Code sub-agent orchestration (Task/agent teams), each with the
narrowest tool scope its role needs. Build/narration LLM calls inside the PRODUCT follow the standing
policy (Gemini/DeepSeek; Anthropic banned in product paths); the SWARM itself is Claude Code (that is the
executor, not the product). Scoring paths remain LLM-free (D-1). Astro-Examiner rubric scoring uses the
product-side model policy. Skills: use repo-local governance scripts (schema_validator, drift_detector)
as gates, not suggestions.

## §8 — KICKOFF CONTRACT

One paste (below) starts everything. First acts in order: (0) verify clean slate vs P-1 standard +
re-verify P0 final AC (merge #395 → deploy → probe); (1) execute P1 (brief committed); (2) author+audit+
execute P2 incl. the Pratinidhi tuning loop; (3) P3 under §4; (4) P4 → P5 → P6 (+P7 lanes); (5) Ring 3;
(6) cleanup + BA_RUN_REPORT. Cadence artifact: the RUN LEDGER updates at every gate so the native can
watch live without being waited on.

*End of BA_AUTONOMOUS_RUN_CHARTER v1.0.*

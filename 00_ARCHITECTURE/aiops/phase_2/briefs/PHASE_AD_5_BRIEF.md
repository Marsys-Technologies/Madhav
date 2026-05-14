---
status: OPEN
session_id: AIOPS_AD_5
phase: AD.5
phase_name: "Cutover smoke + flag flip + native acceptance"
next_session: AIOPS_PHASE_2_COMPLETE
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_2_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_AD_5
## AIOps Phase 2, Step 5 — Cutover and acceptance

---

## §0 — Executor orientation

AD.5 is the cutover. Equivalence is verified in AD.4. This session runs
the full cutover smoke, edits `deploy.yml` to set `ADAPTERS_ENABLED=true`,
commits, pushes, waits for production deploy, verifies the new revision
has the flag on, and prepares the native acceptance handoff.

Same playbook as Phase 1's CP.5. The native does the final review + merge
to main.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_2/AIOPS_PHASE_2_MASTER_PLAN_v1_0.md §10, §11, §12, §13
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4. 00_ARCHITECTURE/aiops/phase_2/AD4_CALL_SITES_INVENTORY.md
5. platform/scripts/aiops/cutover_smoke.ts (now adapter-routed)
6. .github/workflows/deploy.yml — current state
7. Phase 1's CP5_NATIVE_ACCEPTANCE.md (template — produce analogous AD5_NATIVE_ACCEPTANCE.md)
8. Phase 1's CP5_CUTOVER_REPORT_v1_0.md (template)
```

---

## §2 — Scope

### may_touch
```
.github/workflows/deploy.yml                          # add ADAPTERS_ENABLED=true to env_vars
platform/scripts/aiops/cutover_smoke_adapters.ts       # NEW — Phase 2-specific smoke
00_ARCHITECTURE/aiops/phase_2/AD5_CUTOVER_REPORT_v1_0.md  # NEW
00_ARCHITECTURE/aiops/phase_2/AD5_NATIVE_ACCEPTANCE.md    # NEW
CLAUDECODE_BRIEF.md
```

### must_not_touch
- Everything outside may_touch.
- Do NOT push the branch to main; this brief stops at "ready for merge".

---

## §3 — Work plan

### 3.1 — Cutover smoke for the adapter

Author `platform/scripts/aiops/cutover_smoke_adapters.ts`:

For every model that has a populated quirks field, invoke
`streamAdapter` with a small canonical prompt and collect the resulting
`ModelInteraction`. Report per-model:
- pass/fail
- latency
- reasoning emitted (Y/N)
- finalText present (Y/N)
- usage tokens recorded

Compare two runs: `ADAPTERS_ENABLED=false` vs `ADAPTERS_ENABLED=true`. For
non-Anthropic models, results must MATCH within tolerance (text lengths
should match exactly via deterministic mocked SDKs, OR by using seeded
prompts that produce stable outputs).

### 3.2 — Edit deploy.yml

Add to the `env_vars:` block of the deploy-web job:

```yaml
            ADAPTERS_ENABLED=true
```

Insert after `AIOPS_OVERRIDES_ENABLED=true` if that line still exists,
otherwise after `NODE_ENV=production`.

Note: the AIOPS_OVERRIDES_ENABLED line was removed in commit 887e11a
(Phase 1 flag removal). Verify before editing.

### 3.3 — Pre-deploy verification

Run the smoke script both flag states locally, save results to evidence
directory `00_ARCHITECTURE/aiops/phase_2/cutover_evidence/`.

### 3.4 — Commit + push

```
ops(aiops-Phase-2): enable ADAPTERS_ENABLED in production

AIOps Phase 2 (Adapter Layer) is now active in production. The adapter
contract `runAdapter` / `streamAdapter` routes every LLM call through
provider-specific normalization, emitting typed ModelInteractionEvent
streams that Phase 3 (Consume UI Overhaul) will consume.

Code:
- 5 provider adapters (anthropic, deepseek, gemini, openai, nim)
- ProviderQuirks metadata on every model in registry
- Call-site migration: N sites in platform/src + platform/scripts
- think_block_filter.ts retired (logic moved into adapter_deepseek)
- 35+ flag-off equivalence tests passed in AD.4
- Cutover smoke: parity confirmed both flag states

Rollback (no code revert needed):
  gcloud run services update amjis-web --region asia-south1 \
    --remove-env-vars ADAPTERS_ENABLED

Flag removal PR scheduled 2 weeks post-flip.
```

### 3.5 — Wait for deploy, verify

Same as Phase 1's CP.5:
- Poll deploy-web job until success.
- Confirm new revision has ADAPTERS_ENABLED=true via gcloud describe.
- (Note: same deploy-cloudrun@v2 merge-not-replace behavior — adding a NEW env var works via the deploy; only REMOVING needs the supplementary gcloud command.)

### 3.6 — Produce reports

Author `AD5_CUTOVER_REPORT_v1_0.md` populated with live smoke numbers.
Author `AD5_NATIVE_ACCEPTANCE.md` with a 12-item checklist.

### 3.7 — Flip CLAUDECODE_BRIEF to COMPLETE

```yaml
---
status: COMPLETE
session_id: AIOPS_AD_5
completed_at: <ISO>
next_native_action: >
  Review AD5_NATIVE_ACCEPTANCE.md and complete the checklist; merge
  feature/aiops-phase-2-adapters to main when satisfied. Set
  ADAPTERS_ENABLED=true confirmed on production revision <revision-name>.
---

# AIOps Phase 2 — COMPLETE

All six phases AD.0 → AD.5 closed. Adapter layer is live in production.
Native acceptance pending per 00_ARCHITECTURE/aiops/phase_2/AD5_NATIVE_ACCEPTANCE.md.
```

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.AD5.1 | cutover_smoke_adapters.ts exists + runs both flag states | exit 0 each |
| AC.AD5.2 | Parity confirmed (non-Anthropic models match) | assertion |
| AC.AD5.3 | deploy.yml has ADAPTERS_ENABLED=true | grep |
| AC.AD5.4 | Cutover report exists with all sections populated | grep section markers |
| AC.AD5.5 | Native acceptance checklist exists | grep `[ ]` count ≥ 12 |
| AC.AD5.6 | git push succeeded | log shows new commit on origin/main |
| AC.AD5.7 | New Cloud Run revision has ADAPTERS_ENABLED=true | gcloud describe |
| AC.AD5.8 | CLAUDECODE_BRIEF status: COMPLETE | grep |
| AC.AD5.9 | Branch ahead of main by 6 phase commits | `git rev-list --count main..HEAD` ≥ 6 |
| AC.AD5.10 | Full test suite green | exit 0 |
| AC.AD5.11 | Madhav worktree unchanged | snapshot check |

---

## §5 — Session close

Same pattern as Phase 1 CP.5. Print the final report:

```
═══════════════════════════════════════════════════════════════
AIOps PHASE 2 (Adapter Layer) — code-complete in production.

Production revision: <amjis-web-NNN-xxx>
Service URL:         https://amjis-web-qm256lasva-el.a.run.app
Flag state:          ADAPTERS_ENABLED=true
Cutover smoke:       <pass>/<total> parity ✓

Branch: feature/aiops-phase-2-adapters NOT pushed to GitHub.
Native action: review AD5_NATIVE_ACCEPTANCE.md and merge.

Ready for Phase 3 (Consume UI Overhaul) scoping refinement based on
the actual adapter contract shipped in this branch.
═══════════════════════════════════════════════════════════════
```

---

## §6 — BAIL OUT triggers

- Parity smoke fails on non-Anthropic models — DO NOT push the flag.
- Production deploy job fails — investigate.
- New revision does not show ADAPTERS_ENABLED on env vars list — investigate.

---

*End of PHASE_AD_5_BRIEF.md*
*End of AIOps Phase 2 brief arc.*

---
status: OPEN
session_id: AIOPS_CO_7
phase: CO.7
phase_name: "Cutover — flag flip + 48h watch + native acceptance"
next_session: AIOPS_PHASE_3_COMPLETE
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_3_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CO_7
## AIOps Phase 3, Step 7 — Cutover

---

## §0 — Executor orientation

CO.7 cuts over the consume UI to v2. Same playbook as Phase 1 CP.5 and
Phase 2 AD.5:

  1. Author cutover smoke (visual regression diff against pre-CO baseline,
     plus a manual viewing checklist).
  2. Edit `.github/workflows/deploy.yml` to add
     `CONSUME_UI_V2_ENABLED=true` to deploy-web env_vars.
  3. Commit + push → triggers GitHub Actions deploy.
  4. Wait for deploy, verify new revision has the env var.
  5. Author CO7_NATIVE_ACCEPTANCE.md + CO7_CUTOVER_REPORT_v1_0.md.
  6. Flip CLAUDECODE_BRIEF.md to status: COMPLETE.

After CO.7 closes, Phase 3 is code-complete and native does the final
review + branch merge.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_3/AIOPS_PHASE_3_MASTER_PLAN_v1_0.md §10, §11
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4. 00_ARCHITECTURE/aiops/phase_2/AD5_NATIVE_ACCEPTANCE.md (template)
5. 00_ARCHITECTURE/aiops/phase_2/AD5_CUTOVER_REPORT_v1_0.md (template)
6. Phase 1's CP5_NATIVE_ACCEPTANCE.md (template; what a UI-focused checklist looks like)
7. CO5_VISUAL_AUDIT.md and CO6_A11Y_AUDIT.md (CO.5 + CO.6 deliverables)
```

---

## §2 — Scope

### may_touch
```
.github/workflows/deploy.yml                              # add CONSUME_UI_V2_ENABLED=true
platform/scripts/aiops/consume_ui_cutover_check.ts        # NEW — small smoke runner
00_ARCHITECTURE/aiops/phase_3/CO7_CUTOVER_REPORT_v1_0.md  # NEW
00_ARCHITECTURE/aiops/phase_3/CO7_NATIVE_ACCEPTANCE.md    # NEW
CLAUDECODE_BRIEF.md
```

### must_not_touch
- All consume/ component code (sealed after CO.6)
- adapters/, synthesis/, models/
- Anything outside may_touch

---

## §3 — Work plan

### 3.1 — Pre-deploy verification

```bash
cd platform
npm run typecheck                            # exit 0 (or known-residual only)
npm run lint                                  # exit 0
npm run test -- --run                        # full suite; no new regressions vs CO.6 baseline
```

If any new regressions vs CO.6 close, BAIL OUT.

### 3.2 — Consume UI cutover smoke

`platform/scripts/aiops/consume_ui_cutover_check.ts`:

A small runner that:
- Authenticates a super-admin session (via mint_session_cookie helper).
- Hits `/consume` and verifies the new component tree mounts (flag-aware).
- Captures DOM structure assertions (e.g., #lifecycle-status-pip exists,
  #lifecycle-reasoning-slot exists when reasoning model is active).
- Runs in CI-like environment without a real browser; uses fetch + JSDOM
  if needed.

Run twice — `CONSUME_UI_V2_ENABLED=false` vs `=true` — and confirm:
- Flag-off: legacy components render (StreamingAnswer old path, LiveReasoningCard).
- Flag-on: new components render (lifecycle/* slots).

Save evidence to `00_ARCHITECTURE/aiops/phase_3/consume_ui_cutover_evidence/`.

### 3.3 — Edit deploy.yml

Add to deploy-web env_vars block, after `ADAPTERS_ENABLED=true`:

```yaml
            CONSUME_UI_V2_ENABLED=true
```

Use the same Python substitution pattern as Phase 1 / Phase 2.

### 3.4 — Commit + push

```
ops(aiops-Phase-3): enable CONSUME_UI_V2_ENABLED in production

AIOps Phase 3 (Consume UI Overhaul) is now active in production. The
event-driven consume UI replaces the ad-hoc state management; reasoning
slot anchored from submission (Bug 3.3 fix); model-aware reasoning visibility
(Bug 3.4 fix); input panel cleanup (Bug 3.1 fix); sidebar hover-expand
(Bug 3.2 fix); visual design pass (CO.5); behavioral polish (CO.6).

Rollback (no code revert): gcloud run services update amjis-web \\
  --region asia-south1 --remove-env-vars CONSUME_UI_V2_ENABLED
```

Push to main.

### 3.5 — Wait for deploy + verify

Standard pattern. Poll deploy-web job (same as AD.5). Confirm new revision
has CONSUME_UI_V2_ENABLED=true via gcloud describe.

### 3.6 — CO7_CUTOVER_REPORT

Standard report shape (mirror AD5_CUTOVER_REPORT):
- §1 cutover smoke flag-on vs flag-off results
- §2 visual regression evidence (screenshots before/after key views)
- §3 bug-fix verification (Bugs 3.1, 3.2, 3.3, 3.4 each have a programmatic check)
- §4 a11y audit summary (referencing CO6_A11Y_AUDIT.md)
- §5 outstanding risks (none if all CO sub-phases closed clean)

### 3.7 — CO7_NATIVE_ACCEPTANCE

12-item checklist mirroring CP5_NATIVE_ACCEPTANCE shape, including:
1. Visit `/consume`; submit a reasoning model query; confirm Bug 3.3 fix
2. Visit `/consume`; confirm input panel alignment + per-message capsules (Bug 3.1)
3. Hover sidebar; verify expand/collapse + click-pin (Bug 3.2)
4. Send a non-reasoning query (NIM Nemotron); verify reasoning slot absent (Bug 3.4)
5. CLS measurement < 0.05 in browser DevTools
6. Mobile viewport (Chrome DevTools 375×667): sidebar overlay, composer sticky, no horizontal scroll
7. Keyboard shortcuts: Cmd+K, Esc, Cmd+/ verified
8. Mid-stream Stop generating works
9. Flag-off equivalence: set `CONSUME_UI_V2_ENABLED=false`; confirm legacy components render
10. CO6_A11Y_AUDIT.md OUTSTANDING: 0
11. CO5_VISUAL_AUDIT.md confirms typography ≤ 6 sizes, motion tiers consolidated
12. No /consume regressions in Cloud Run / Observatory cost+latency for 1 hour post-flip

### 3.8 — Flip CLAUDECODE_BRIEF.md

```yaml
---
status: COMPLETE
session_id: AIOPS_CO_7
completed_at: <ISO>
next_native_action: >
  Review CO7_NATIVE_ACCEPTANCE.md (12-item checklist). When satisfied,
  merge feature/aiops-phase-3-consume-ui to main. Set ADAPTERS_ENABLED
  + CONSUME_UI_V2_ENABLED flag-removal PRs for 2 weeks post-merge.
---

# AIOps Phase 3 — COMPLETE

8 sub-phases CO.0 → CO.7 closed. Consume UI overhaul live in production
behind CONSUME_UI_V2_ENABLED=true. Native acceptance pending per
CO7_NATIVE_ACCEPTANCE.md.
```

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CO7.1 | consume_ui_cutover_check.ts exists + passes both flag states | exit 0 |
| AC.CO7.2 | deploy.yml has CONSUME_UI_V2_ENABLED=true | grep |
| AC.CO7.3 | git push to main succeeded | log |
| AC.CO7.4 | New Cloud Run revision has the env var | gcloud describe |
| AC.CO7.5 | CO7_CUTOVER_REPORT_v1_0.md exists with §1–§5 populated | grep |
| AC.CO7.6 | CO7_NATIVE_ACCEPTANCE.md exists with 12-item checklist | grep `[ ]` count |
| AC.CO7.7 | CLAUDECODE_BRIEF.md status: COMPLETE | grep |
| AC.CO7.8 | Branch ≥ 8 phase commits ahead of main (CO.0 through CO.7) | rev-list |
| AC.CO7.9 | Madhav worktree unchanged | snapshot check |
| AC.CO7.10 | Full test suite + typecheck green | exit 0 each |

---

## §5 — Session close

Standard. Print final report:

```
═══════════════════════════════════════════════════════════════
AIOps Phase 3 (Consume UI Overhaul) — code-complete in production.

Production revision: <amjis-web-NNN-xxx>
Service URL:         https://amjis-web-qm256lasva-el.a.run.app
Flag state:          CONSUME_UI_V2_ENABLED=true
4 named bugs fixed:  3.1 (input panel), 3.2 (sidebar), 3.3 (reasoning
                     placement), 3.4 (reasoning consistency)
Visual + behavioral: 2 audits with OUTSTANDING: 0

Branch: feature/aiops-phase-3-consume-ui NOT pushed.
Native action: review CO7_NATIVE_ACCEPTANCE.md and merge.

AIOps trilogy complete:
  Phase 1 — Control Panel (live, all stacks functional)
  Phase 2 — Adapter Layer (live, 246a85b merge)
  Phase 3 — Consume UI Overhaul (this branch, awaiting merge)
═══════════════════════════════════════════════════════════════
```

---

## §6 — BAIL OUT

- Cutover smoke fails on flag-on path (new components don't mount correctly).
- A11y audit reveals an issue that CO.6 should have caught — bug in audit; native investigates.
- Deploy push rejected for unrelated reasons (branch protection, etc.).

---

*End of PHASE_CO_7_BRIEF.md*
*End of AIOps Phase 3 brief arc.*

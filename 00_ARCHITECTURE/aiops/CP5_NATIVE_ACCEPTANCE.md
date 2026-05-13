---
artifact: CP5_NATIVE_ACCEPTANCE.md
status: AWAITING_NATIVE
session_id: AIOPS_CP_5
authored_at: 2026-05-13
---

# AIOps Phase 1 — Native Acceptance Checklist

Branch: `feature/aiops-control-panel`
Phase: CP.0 → CP.5 (6 commits)

The AIOps Phase 1 feature branch is code-complete and tested. Before merging to main,
complete this checklist. The steps below require a running local or staging environment
with the DB migrations applied and provider API keys configured.

---

## Pre-flight

```bash
git checkout feature/aiops-control-panel
cd platform
npm install
# Start DB proxy (if needed)
npm run db:migrate   # or equivalent; applies migrations 046-052
npm run dev
```

---

## Checklist

### Control Panel

1. [ ] Visit `/aiops/control` as super-admin. All 6 stack tabs render: NIM, Gemini, DeepSeek, GPT, Anthropic, MARSYS.
2. [ ] Switch active stack to **NIM**. Confirm the "Active" indicator moves.
3. [ ] On the NIM stack view, click "Run smoke test for this stack". Confirm ≥8 of 10 probes return green.
4. [ ] On the NIM stack, change Synthesis primary to a different model from the dropdown. Click the inline Test button. Confirm probe succeeds.
5. [ ] Switch active stack to **MARSYS**. Confirm the model dropdown for Synthesis shows models from all providers (not just one).
6. [ ] On MARSYS, pick a Synthesis primary from the Gemini provider and a Worker primary from the DeepSeek provider. Confirm both inline Test buttons pass.
7. [ ] Set a param override (e.g., temperature = 0.5) on any stack/call-type. Confirm it saves and shows in the right rail.
8. [ ] Revert one change from the Recent Changes right rail. Confirm the revert dialog opens, shows before/after, and clicking Confirm Revert restores the previous value. Confirm a new "revert" entry appears in the audit log.

### Observatory deep-link

9. [ ] Visit `/observatory` (or `/aiops/observatory`). Find the Stack Breakdown cards. Click the ✏ pencil icon on any stack card. Confirm it navigates to `/aiops/control?stack=<stack>&from=observatory` and shows the "Came from Observatory" banner with a back link.

### Flag-off equivalence (regression test)

10. [ ] Set `AIOPS_OVERRIDES_ENABLED=false` in `.env.local`. Restart dev server. Use the application normally (consume a query). Confirm model selection is identical to what the registry defaults produce. No override is applied.

### Smoke + health

11. [ ] Run `npm run aiops:health`. Confirm it exits 0 (or 1 only if majority of providers fail). Check `llm_model_health` table has rows populated.
12. [ ] Run `npm run aiops:cutover-smoke` twice: once with `AIOPS_OVERRIDES_ENABLED=false`, once with `true`. Open `platform/scripts/aiops/cutover_smoke_report.json`. Confirm the flag-off and flag-on runs have the same pass/fail pattern for non-Anthropic stacks. Document any differences.

### Audit logs

13. [ ] Confirm every write action (stack switch, routing change, param set, revert) creates a row in `llm_config_audit`.
14. [ ] Inspect `CP5_CUTOVER_REPORT_v1_0.md`. Populate §1–§4 from the live runs above. Confirm 0 outstanding risks blocking merge.

### A11y and brand sign-off

15. [ ] Inspect `CP4_A11Y_AUDIT.md`. Confirm `OUTSTANDING: 0`.
16. [ ] Inspect `CP4_BRAND_AUDIT.md`. Confirm `VIOLATIONS: 0`.

---

## Merge decision

If all 16 boxes are checked:

```bash
git checkout main
git merge feature/aiops-control-panel
git push origin main
```

Then in production environment:

```bash
# Enable AIOps override system
AIOPS_OVERRIDES_ENABLED=true   # set in Cloud Run / deployment env, not in code
```

**48-hour observation window** starts at the env-var flip:
- Monitor Observatory cost/usage numbers for regressions.
- Monitor `/consume` latency and error rate (Grafana, Cloud Run logs).
- If anything looks off: `AIOPS_OVERRIDES_ENABLED=false` — no code change required.

**Rollback path:** Setting `AIOPS_OVERRIDES_ENABLED=false` instantly restores the pre-AIOps behavior. The DB overrides are preserved (not deleted) so they can be re-enabled later.

**Flag removal:** Schedule for 2 weeks after the flip, per Phase 11B precedent.

---

## Optional: Cloud Scheduler for nightly health probes

```
Trigger: Pub/Sub or HTTP
Schedule: 0 2 * * *  (2am daily)
Command: curl -X POST https://<your-app>/api/admin/aiops/health?model_id=all \
  -H "Authorization: Bearer <service-account-token>"
```

---

*AIOps Phase 2 (Adapter Layer) and Phase 3 (Consume UI Overhaul) are tracked in `AIOPS_MASTER_PLAN_v1_0.md §14` — future scope, not in scope for this merge.*

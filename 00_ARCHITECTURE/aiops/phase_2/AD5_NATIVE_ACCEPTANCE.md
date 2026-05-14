---
artifact: AD5_NATIVE_ACCEPTANCE.md
status: PENDING_NATIVE_REVIEW
session_id: AIOPS_AD_5
authored_at: 2026-05-14
---

# AIOps Phase 2 — Native Acceptance Checklist

Branch: `feature/aiops-phase-2-adapters`
Phase arc: AD.0 → AD.5 (6 commits beyond main)

The AIOps Phase 2 adapter layer is code-complete and tested. Before merging to main,
complete this checklist.

---

## Pre-flight

```bash
git checkout feature/aiops-phase-2-adapters
cd platform
npm install
npm run typecheck          # expect: exit 0 (or known-residual TS errors only)
npm run test               # expect: ≥146 pass, 0 new failures vs main baseline
```

---

## Checklist

### Adapter dispatch

1. [ ] Review `platform/src/lib/adapters/index.ts` — confirm `runAdapter`, `streamAdapterRaw`, `streamBuildRaw` exports are present and documented.
2. [ ] Review `platform/src/lib/adapters/run_adapter.ts` — confirm `ADAPTERS_ENABLED` flag dispatch routes correctly: `false` → `legacy_runAdapter`, `true` → provider adapters.
3. [ ] Review `platform/src/lib/adapters/legacy_runAdapter.ts` — confirm it is a thin wrapper over the existing `buildProviderOptions` + `streamText` call (no behavior change).
4. [ ] Inspect `platform/src/lib/adapters/providers/` — 5 provider adapters present: `adapter_anthropic`, `adapter_deepseek`, `adapter_gemini`, `adapter_openai`, `adapter_nim`.

### Call-site migration

5. [ ] Run scope-violation grep: `grep -r "streamText\|generateText" platform/src --include="*.ts" | grep "from 'ai'" | grep -v "adapters/\|__tests__"` — expect **0 results**.
6. [ ] Verify `think_block_filter.ts` deleted: `! test -f platform/src/lib/synthesis/think_block_filter.ts` — expect **true** (file absent).

### Equivalence + parity

7. [ ] Run: `cd platform && npx vitest run src/lib/adapters/__tests__/equivalence/runtime_equivalence.test.ts` — expect **48/48 pass**.
8. [ ] Inspect `00_ARCHITECTURE/aiops/phase_2/cutover_evidence/parity_report.json` — confirm `"mismatched": 0`.

### Deploy gate

9. [ ] Inspect `.github/workflows/deploy.yml` env_vars block — confirm `ADAPTERS_ENABLED=true` is present.
10. [ ] After merging to main: confirm GitHub Actions deploy-web job completes successfully.
11. [ ] After deploy: run `gcloud run services describe amjis-web --region asia-south1 --format="value(spec.template.spec.containers[0].env)"` — confirm `ADAPTERS_ENABLED=true` is present in the new revision.
12. [ ] 48-hour observation window: monitor Cloud Run logs for `adapter_` prefixed log lines. Confirm error rate does not increase vs pre-merge baseline.

---

## Merge decision

If all 12 boxes are checked:

```bash
git checkout main
git merge feature/aiops-phase-2-adapters
git push origin main
```

The deploy.yml change in the merge will set `ADAPTERS_ENABLED=true` on the next Cloud Run revision,
activating the adapter layer in production.

**48-hour observation window** starts at the deploy:
- Monitor `/consume` latency and error rate (Cloud Run logs, Observatory).
- If anything looks off: `gcloud run services update amjis-web --region asia-south1 --remove-env-vars ADAPTERS_ENABLED` — no code change required; legacy path remains in `legacy_runAdapter.ts`.

**Flag removal:** Schedule for 2 weeks after flip, per Phase 11B precedent.
Target: delete `legacy_runAdapter.ts`, remove `ADAPTERS_ENABLED` checks, remove the env var from `deploy.yml`.

---

## Phase 3 readiness

The adapter contract shipped in this branch is the input surface for Phase 3 (Consume UI Overhaul).
Key types: `ModelInteraction`, `IntermediateEvent`, `RawAdapterResult` in
`platform/src/lib/adapters/types.ts`. Phase 3 scoping should be based on these actual types,
not the pre-adapter design sketches in `AIOPS_MASTER_PLAN_v1_0.md §14`.

---

*AIOps Phase 2 (Adapter Layer) complete. Phase 3 (Consume UI Overhaul) tracked in `AIOPS_MASTER_PLAN_v1_0.md §14` — future scope.*

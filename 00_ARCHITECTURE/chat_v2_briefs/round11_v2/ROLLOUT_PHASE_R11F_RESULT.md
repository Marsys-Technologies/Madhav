---
artifact: ROLLOUT_PHASE_R11F_RESULT
version: 1.0
status: FINAL
created: 2026-05-23
session: R11F-S7-governance
---

# R11.F Wiring Arc — Production Rollout Surface

## Summary

PR #151 merged to main (squash SHA 97acf339). Deploy to Cloud Run in progress.

All R11.D + R11.E flags remain false in production. This file surfaces the
operator flip commands to activate them one at a time after smoke verification.

## Pre-flip checklist (operator runs before any flip)
1. Confirm Cloud Run deploy completed: check revision in Cloud Console
2. Run 2 test queries (one Gemini, one Anthropic) — confirm no errors in logs
3. Proceed with flag flips below in order

## D.3 — MARSYS_FLAG_R11D_GEMINI_CACHE

Flip after confirming deploy is healthy:
```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --update-env-vars MARSYS_FLAG_R11D_GEMINI_CACHE=true
```
Verification: send 2 long-context Gemini queries (~40k+ tokens system+bundle).
Check logs: `gcloud logging read 'resource.type="cloud_run_revision" AND jsonPayload.marsys_event_type="gemini_cache_metrics"' --limit 5`
Expected: cachedContentTokenCount > 0 in at least one log entry.

If no cache hits: check that GOOGLE_GENERATIVE_AI_API_KEY is set in Cloud Run env.
If HTTP 400 from Gemini cache API: check model name format (should have 'models/' prefix).
Roll back if any errors: `gcloud run services update amjis-web --region asia-south1 --update-env-vars MARSYS_FLAG_R11D_GEMINI_CACHE=false`

## E.1 — MARSYS_FLAG_R11E_ANTHROPIC_LOOP

After D.3 verified (or independently after 15-min clean window):
```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --update-env-vars MARSYS_FLAG_R11E_ANTHROPIC_LOOP=true
```
Verification: send a multi-step Anthropic query that triggers tool use.
Check logs for: `marsys_event_type: "tool_loop_iteration"` with iteration > 1
15-min log watch: confirm no AgenticLoopCapExceeded errors.

## E.2 — MARSYS_FLAG_R11E_GEMINI_LOOP

After E.1 stable (15-min window):
```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --update-env-vars MARSYS_FLAG_R11E_GEMINI_LOOP=true
```
Same verification pattern as E.1, provider=google in logs.

## E.3 — MARSYS_FLAG_R11E_DEEPSEEK_LOOP

After E.2 stable:
```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --update-env-vars MARSYS_FLAG_R11E_DEEPSEEK_LOOP=true
```

## E.4 — MARSYS_FLAG_R11E_NVIDIA_LOOP (model-dependent)

After E.3 stable. Note: NVIDIA NIM tool support is model-dependent — only
models that declare tool/function support will trigger tool loops.
```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --update-env-vars MARSYS_FLAG_R11E_NVIDIA_LOOP=true
```

## Post-activation: update deploy.yml

After each flag is verified stable, add it to deploy.yml env_vars block so
it persists across deploys. Example for D.3:
```yaml
env_vars:
  MARSYS_FLAG_R11D_GEMINI_CACHE: "true"
```

## Note on tool executor stub

The agentic loop tool executor in this arc is a stub that returns
"Tool not available in adapter dispatch". Full MCP tool dispatch
(wiring the Marsys tool results into the loop) is a follow-up arc.
With the stub, the loop will execute 1 iteration, return the tool_use_complete
event, feed back "Tool not available", and the model will respond with
a text-only answer on the second iteration. This is correct and safe behavior
for production — the loop infrastructure is live, but tool results are stub.

---
*ROLLOUT_PHASE_R11F_RESULT.md — authored 2026-05-23 by R11F-S7 governance session*

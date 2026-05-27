# GISMCP Remediation — Conductor README

## What this fixes

Four categories of GISMCP (MCP sidecar `amjis-mcp`) failures:

| # | Fix | File | Impact |
|---|-----|------|--------|
| R1 | Remove `if (tier !== 'client')` gate | `platform-mcp/src/server.ts` | All 40 tools visible to all tiers including super_admin |
| R2a | `query_tara_balam` engine | `platform/src/lib/retrieve/query_tara_balam.ts` | Tara Balam no longer 500s |
| R2b | `query_chandra_balam` engine | `platform/src/lib/retrieve/query_chandra_balam.ts` | Chandra Balam no longer 500s |
| R2c | `jaimini_chara_dasha` engine | `platform/src/lib/retrieve/jaimini_chara_dasha.ts` | Jaimini Chara Dasha no longer 500s |
| R2d | `jaimini_chara_dasha_full` engine | `platform/src/lib/retrieve/jaimini_chara_dasha_full.ts` | Full Jaimini sequence no longer 500s |
| R3 | MSR grounding verification | DB + integration tests | 573/573 signals confirmed grounded |

## How to run

1. **Paste `PREP_PROMPT.md`** into a Claude Code chat (any folder). Creates worktrees + settings.
2. **Open two chat panels** in Antigravity IDE:
   - Panel 1: folder `MadhavGISMCP-S1` → paste `STREAM1_CONDUCTOR_PROMPT.md`
   - Panel 2: folder `MadhavGISMCP-S2` → paste `STREAM2_CONDUCTOR_PROMPT.md`
3. Both streams run in parallel. No human gates needed during execution.
4. After both complete, run operator merge + deploy steps from Stream 1 final report.

## File map

```
PREP_PROMPT.md                    ← run first (once)
STREAM1_CONDUCTOR_PROMPT.md       ← Panel 1 (R1 + R2)
STREAM2_CONDUCTOR_PROMPT.md       ← Panel 2 (R3)
session_queue_s1.yaml             ← Stream 1 state tracker
session_queue_s2.yaml             ← Stream 2 state tracker
briefs/
  R1_S1_BRIEF.md                  ← server.ts de-gating
  R1_T1_BRIEF.md                  ← tier visibility tests
  R2_S1_BRIEF.md                  ← Tara Balam + Chandra Balam engines
  R2_S2_BRIEF.md                  ← Jaimini Chara Dasha engines
  R2_T1_BRIEF.md                  ← integration tests (4 engines)
  R2_T2_BRIEF.md                  ← MCP smoke + seal
  R3_S1_BRIEF.md                  ← MSR grounding audit
  R3_S2_BRIEF.md                  ← grounding completion (conditional)
  R3_T1_BRIEF.md                  ← grounding verification tests
  R3_SEAL_BRIEF.md                ← Stream 2 seal
```

## Operator deploy (after both streams complete)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git merge --no-ff fix/gismcp-r3
git merge --no-ff fix/gismcp-r1-r2
git push origin main

# Deploy amjis-web (new retrieve tools)
gcloud builds submit --config cloudbuild.yaml --project madhav-astrology

# Deploy amjis-mcp sidecar (server.ts de-gating)
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_DEPLOY_TARGET=sidecar \
  --project madhav-astrology
```

# MARSYS Build Tracker — Localhost Dashboard

Live, dual-track dashboard for the MARSYS-JIS Multi-Ayanamsha Deterministic Build workstream. Two parallel tracks per item — **Plan/Brief** (authored by Cowork) and **Implementation** (built by Claude Code in Antigravity) — so you can see plan running ahead of implementation, where they're in sync, and where decisions from off-stream conversations are landing.

## Run

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_orchestrator/tracker
python3 -m http.server 8765
```

Then open **http://localhost:8765** in your browser.

Auto-refreshes every 30 seconds. Click the Refresh button for instant reload.

## Files

- **`index.html`** — the dashboard page. Static. Renders state.
- **`state.json`** — the live source of truth. Edit this to update statuses. The page reads it on load + every 30s.
- **`README.md`** — this file.

## How updates happen

1. **Plan/Brief track** (left status pill on each row): updated by me (Cowork) by editing `state.json` between turns. When I confirm "A2 locked" you'll see `A2.brief.status: discussing → locked` in the JSON. The page reflects it on next refresh.
2. **Implementation track** (right status pill on each row): updated by you OR by integration hooks when implementation lands. For now, you tell me what changed and I edit `state.json`; later we wire GitHub/Cloud Run webhooks to push directly into a backend.
3. **Miscellaneous decisions**: any off-stream architectural decision gets a row in the MISC track with `affects: [A1, INF7, ...]` so you can trace which main-track items it touches.

## Status vocabulary

**Brief track:** `not_started → discussing → drafted → locked → superseded`

**Impl track:** `not_started → in_progress → merged_branch → in_review → merged_main → deployed → verified`

Completion = brief at `locked`, impl at `deployed` or `verified`. Both pills show a ✓ when complete.

## Productionization

This localhost tracker is itself **INF12** in the workstream — its Brief is in discussion. When INF12 ships, this tracker becomes a Next.js page on amjis-web at `/cockpit/workstreams/[id]` with SSE, webhook integrations, and Postgres-backed state. The localhost version is retired then.

## What's in scope

- **A0** — Global asset substrate (47 items: classical RAG + ephemeris + Nadi + Lal Kitab + Bhrigu Samhita + all lookup tables + Tantric + Ayurveda + Numerology + esoteric)
- **A1–A14** — Per-chart deterministic build (engine, FORENSIC, chart_facts, panchanga, sensitive points, vargas, dashas, T1 structural, sade sati, MSR, CDLM, CGM, RM, UCN digest)
- **A15–A20** — Supplementary per-chart proposals (chakras, vedha, argala, Bhrigu Bindu transit, Tajik per-chart, per-graha next-exact-aspect)
- **INF** — Infrastructure & tooling (form, schema, API, pipeline, UI, notifications, consume hybrid, etc.)
- **ACC** — Acceptance & close (re-baseline, hard gates, red-team, deploys)
- **MISC** — Off-stream decisions with traceable scope impact

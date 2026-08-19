---
artifact: PARIPRASHNA_ASBUILT_BASELINE_v1_0
canonical_id: PARIPRASHNA_ASBUILT_BASELINE
version: 1.0
status: LIVING — regenerated at every gate close; every row carries an evidence class + date
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18)
date: 2026-08-18
baseline_of: git HEAD dfbdfe620 (branch ekv/b-01-dignity-oracle-fix snapshot) + live MCP census 2026-08-18 + PB close corpus
authoritative_side: claude
role: >
  What EXISTS, dated and evidence-classed — the current-state companion to
  PARIPRASHNA_ARCHITECTURE_v1_0.md, which carries no current-state claims itself.
  Successor to TA v0.11 §16.9. Regeneration rule: at each gate close, re-verify
  every row, refresh dates, move satisfied gaps to the closed table. Never
  normative; never aspirational.
changelog:
  - "1.0 (2026-08-18): first generation, from the v0.11 §16.9 census + v0.12 evidence ledger."
---

# Paripraśna — As-Built Baseline (2026-08-18)

Evidence classes per NFR annex §1. UNVERIFIED rows are the re-verification
worklist for the next gate.

## §1 — Doors and deployment

| Fact | Class · date |
|---|---|
| Portal surface + `/api/pariprashna` (+resume, +samiksha/confirm) live behind `PARIPRASHNA_ENABLED`; flag default `false` in code | STATIC_VERIFIED @ dfbdfe620 |
| Flag ON in production via Cloud Run env (since `amjis-web-01218-4ng`) | DOCUMENT_ASSERTED (REPORT_PB-1) · 2026-07-28 |
| Current Cloud Run env value / serving revision | **UNVERIFIED** |
| C4-LOOP-LIVE-PROOF: full prediction loop live, six criteria, real concurrent user | DOCUMENT_ASSERTED (PURNATA_CLOSE §9) · 2026-08-01 |
| MCP: 125 tools on `full` profile; `catalog-1+t152+r653c2a1a98c8`; profiles full/compact/consult; `prashna_ask`+`prashna_status` job-handle, rejected on consult | LIVE_VERIFIED · 2026-08-18 |
| `ganita_ayurdaya_get` served UNGATED on the MCP surface | LIVE_VERIFIED · 2026-08-18 |
| PB-4 cutover (default flip, consult retirement, flag deletion): NEVER RUN; consult/consume still the un-gated default | STATIC_VERIFIED @ dfbdfe620 |

## §2 — What is BUILT and live-path (STATIC_VERIFIED @ dfbdfe620 unless noted)

15-event Zod SSE protocol + typed emitter (zero `as any`) + calibration-leak
guard on every write · stream-first route (turn.open before planner; faults
in-stream; clarification streams as a block) · acharya-floor compilation on
Door 1 (B.11 + dasha floors + budget arbitration + NO-LEAKAGE arm-2 filter) ·
append-only renderer (FrozenBlock always-equal memo; single volatile tail;
owned scroll; dock) · register-leak lint, server-side, 6 pattern classes,
2 call points · canonical `message_parts` (mig 467) + summaries (468,
prefix-stable splice) · ring-buffer resume (Redis, seq replay, snapshot
fallback, interrupted finalize) · D-16 stamp per turn, copied into ledger
under `trg_bmpl_freeze_confirmed` · 9-state prediction ledger (mig 470) with
legal-transition matrix; review tab, batch resolve, daily job, Brier at
resolution; `mcp_predictions` retired (471) · fail-closed chart authz
(CHART_REQUIRED) · SHA-256 chart-scoped cache keys + echo-back.

## §3 — Gap register (open)

| # | Gap | Class · date | Owner |
|---|---|---|---|
| GAP-1 | MP §3.5.B/C/D/F: NO safety gate, disclosure-class model, consent schema, or minor exclusion anywhere in the serving path (§3.5.E is the exception — seal/freeze/transitions live) | STATIC_VERIFIED · 2026-08-18 | G1 (PPR-12/14/24) |
| GAP-2 | NO-LEAKAGE arm-1: five roles absent; single `amjis_app` credential; no RLS | STATIC_VERIFIED 2026-07-19 (F-25q); **UNVERIFIED today, presumed standing** | G1 (PPR-21/22) |
| GAP-3 | No middleware, no rate limit, no blocking spend cap on either chat tree | STATIC_VERIFIED · 2026-08-18 | G1 (PPR-25) |
| GAP-4 | PITR disabled, no restore drill (last verified F-25t) | UNVERIFIED today · last 2026-07-19 | G1 (PPR-33) |
| GAP-5 | `ANTHROPIC_API_KEY` unprovisioned in production (anthropic stack fails instantly, masked by Gemini default) | DOCUMENT_ASSERTED (PURNATA §5.1a) · 2026-08-01 | G1 |
| GAP-6 | Live wire renders paragraphs only (FD-1): table/verse/gap-ribbon/heading/roles/prediction_card have no live producer | STATIC_VERIFIED | G2 (PPR-07) |
| GAP-7 | S-3 citation rewriter built, unwired; `citation.define` post-hoc; grounding summary client-synthesized (FD-2/FD-6) | STATIC_VERIFIED | G2 (PPR-08) |
| GAP-8 | Model/Length pickers cosmetic; `length_tier` nonfunctional; depth from picker not scope tuple (FD-3/FD-12) | STATIC_VERIFIED | G2 (PPR-09/16) |
| GAP-9 | No durable-persistence protocol (settled_visual vs durably_persisted undistinguished); parity invariant unbuilt; capture flag OFF per Ruling 80 (FD-9 — apparatus repurposed per PPR-10) | STATIC_VERIFIED | G2 (PPR-10) |
| GAP-10 | No AcharyaReadingReceipt: B.4 sets, typed confidence, prose binding, safety_decision all unemitted | STATIC_VERIFIED | G3 (PPR-01..05) |
| GAP-11 | prashna_ask is single-pass without lint/sentinel/receipt; unified plan type unwritten; store covers assistant turns only | STATIC_VERIFIED / DOCUMENT_ASSERTED | G4 (PPR-30) |
| GAP-12 | Recall built-unwired (FD-5); LogToSamiksha unmounted (FD-4); window-opening ask unbuilt; dispute capture absent; feedback endpoint still discards (F-25c); digest transport log-only (FD-10) | STATIC_VERIFIED | G8 (PPR-18/31) |
| GAP-13 | Calibration sink (Rulings 55/79) unbuilt; `model_p` column absent; method-version column is a PROPOSED Ruling-79 amendment | STATIC_VERIFIED | G9 (PPR-28/29) |
| GAP-14 | Cost/latency metrics schema exists with 0 rows (F-25o); no TTFT aggregates; SLOs unbaselined | STATIC_VERIFIED 2026-07-19 · presumed standing | G2 (PPR-33) |
| GAP-15 | Two error classifiers (adapter bands live; `classify-error.ts` dead, zero importers) | STATIC_VERIFIED · 2026-08-18 | G7 sweep |
| GAP-16 | PB-9-DETECTOR (no-auto-promotion CI detector) open — property true by inspection only | DOCUMENT_ASSERTED (REPORT_PB-3 §G.9) | G1/G2 |
| GAP-17 | audience_tier residue: type/comment-level + two JSON-schema `required` fields (load-bearing sites excised) | STATIC_VERIFIED · 2026-08-18 | G7 sweep |
| GAP-18 | Post-six-views narration audit (PŪRṆATĀ handoff #2) not run | DOCUMENT_ASSERTED · 2026-08-01 | G8+ |

## §4 — Engine content beneath the surface (DOCUMENT_ASSERTED, CURRENT_STATE §2)

PRATIJÑĀ v4.1 adopted (marriage verdict conditional/0.450 MODERATE — first
amendment-set production verdict) · GOCHARA v3 under PARIṢKĀRA's honest
re-close (structural_prior stamps) · ṢAḌ-DARŚANA KP sub-lord clock ·
ADHIṢṬHĀNA fact-identity index · SAMPŪRTI domains 7→13. Serving rule for all
of it: PPR-03 (earned tier only).

## §5 — Regeneration protocol

At each gate close: re-verify every UNVERIFIED row live; re-date every
STATIC row against the then-HEAD; move closed gaps to a dated CLOSED table
(append-only); bump version minor. The Baseline never says MUST — if a row
tempts normative language, the content belongs in the Architecture.

*End PARIPRASHNA_ASBUILT_BASELINE v1.0 (2026-08-18).*

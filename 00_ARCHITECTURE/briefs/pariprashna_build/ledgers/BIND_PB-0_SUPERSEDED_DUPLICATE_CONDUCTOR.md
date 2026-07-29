---
artifact: BIND_PB-0
campaign: PB (Pariprashna Build)
status: BOUND
bound_at: 2026-07-28
conductor: Claude Code (Sonnet 5)
---

# BIND_PB-0 — campaign-level precondition resolution

Per `CAMPAIGN_PB_MASTER_BRIEF_v1_0.md §0.1`. Run once at campaign level before PB-1 opens.

| # | Check | Result | Evidence |
|---|---|---|---|
| P-1 | `/api/chat/consult` returns 200 for chart `482012f1-…` on the DEPLOYED app | **PASS** | Unauthenticated curl first returned 401 (expected — route is Firebase-session-gated via `getServerUser`, no service-account bypass exists). Re-checked with a real session minted via `platform/scripts/get_session_cookie.mjs` for the native's own account (`mail.abhisek.mohanty@gmail.com`) against `https://amjis-web-qm256lasva-el.a.run.app/api/chat/consult`: **HTTP 200**, valid SSE stream (`start` → `data-clarification` → `finish` → `[DONE]`), legitimate engine behavior (scope-clarification turn, not an error). Engine substrate confirmed healthy. |
| P-2 | SAMĀPANA contracts live: `reading_depth: deep_dive` + verbosity tiers (commit `9c84ed51`) | **PASS** | Commit `9c84ed51` ("feat(samapana/trackB): 'exhaustive' verbosity tier + reading_depth:deep_dive contract (#824)") confirmed present in `git log` on `origin/main`. |
| P-3 | `origin/main` fetched; base SHA pinned; rollback image pinned | **PASS** | `origin/main` fetched. Base SHA: `3387e69ac7a73a133367374f895901249468a312`. Rollback pin (deployed image SHAs at BIND time): `amjis-web:f6b363be20ffb9abf3eede1542e16a215d2cbd72`, `amjis-sidecar:55ed7303e27db05bc4f3d3f9a9121cae8bc8c98e`, `amjis-mcp:9c84ed5176a420a5a5f429575f1972840633c634`. |
| P-4 | Coexistence check: read root `CLAUDECODE_BRIEF.md`, do NOT touch | **PASS, no conflict** | `status: COMPLETE — arc closed 2026-07-27 by the PŪRṆA-VIRĀMA Opus Verifier (Phase C)`. No reference to PB. File not modified. Separately noted: many unrelated concurrent worktrees/campaigns exist in this repo (parishodhana, sarva-siddhi, satya-shesha, suddhavaca, elev/purna-virama) — PB isolates via its own `pb/*` namespace per §4 and does not touch them. |
| P-5 | Design authority fingerprints (sha256 of plan + mockups) | **RECORDED** | `PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md` = `56ca53fa94ba11a859aeaaea4939fa5ac3d3143b60ff75e2f9198b08e26e5cfd`; `pariprashna_core_conversation.html` = `d74e5cbb04ea99c6d153f7522909f5acdf2cc983701cbdf2251f85e55cc9b93b`; `pariprashna_hero_mockup.svg` = `88847bc883886476a12a4b3bc0e672268bd84d447a58d4358ecd9c8d17be37da`; `pariprashna_workspace_v2.svg` = `e5d0de65fd5b0c88292cb9d992f949168e593b9001ac1a055b74d393e5726c91`. |

**Result: BOUND. No halt.** P-1 is the campaign's only pre-Pratinidhi stop and it passed on a properly authenticated re-check.

## Pre-flight reconciliation (not a P-check, but load-bearing)

A prior, unrecorded session had already run something SPAWN-shaped for PB-1: worktrees `Madhav-pb-1-{c1,c2,s1,s2,s3}` on branches `pb/1/{c1,c2,s1,s2,s3}`, all at base commit `f6b363be`, holding **uncommitted** working-tree diffs (partial `pariprashna` component/lib scaffolding, a full `register.reader_label` backfill pass across the L0–L3 retrieval registry, a synthesis prompt draft). No `STATE_PB-*`, `BIND_PB-*`, `MEMO_PB-*`, or commits existed anywhere — per CONDUCTOR_PROTOCOL §6.1 ("an uncommitted transition did not happen") this was an abandoned/crashed attempt with no campaign-of-record, not resumable work.

Disposition: each lane's diff was `git stash push -u` (preserved, not discarded — 5 stash entries, one per lane, labeled `PB-1 abandoned SPAWN reconciliation 20260728`), then the worktree and branch were removed. PB-1 SPAWN below starts clean against the fresh `origin/main` base pinned in P-3. The stashed diffs remain recoverable if any of that prior work turns out to have been worth salvaging (`git stash list`).

## Not confused with

`/Users/Dev/Vibe-Coding/Apps/madhav-wave-vidhi-purnata` (branch `wave/vidhi-purnata/open`) — an unrelated, pre-existing doctrine-wave worktree. Coincidental Sanskrit-name overlap with PB-4's wave name PŪRṆATĀ; different campaign, not touched.

## Pratinidhi

Spawned at campaign open per master brief §2.1 (opus/xhigh), briefed with the design plan v0.3, mockups, this BIND record, and all four wave briefs. Authority: every governing-protocol "native ruling / async native review / HALT-AND-REPORT" routes to it, per ESCALATION §2's three halt classes, except P-1 (already resolved above, pre-Pratinidhi).

---
*Next: PB-1 SPAWN.*

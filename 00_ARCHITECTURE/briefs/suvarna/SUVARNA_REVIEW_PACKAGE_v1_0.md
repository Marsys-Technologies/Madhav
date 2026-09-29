---
artifact: SUVARNA_REVIEW_PACKAGE
canonical_id: SUVARNA_REVIEW_PACKAGE
version: "1.0"
status: "STALE — describes plan v1.1 and the 2026-09-28 bundle. Do not send. Rebuilt for the v1.4 set by launch item L.12r before L.9 (REVIEW_PASS2_DISPOSITION, C14)."
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.0-stale (2026-09-29): marked stale by review pass 2; no content change. L.12r rebuilds it."
  - "1.0 (2026-09-28): first package. Purpose, reading order, the questions, the bundle manifest."
---

# Suvarṇa — review package for an independent reviewer

## 1 · What you are reviewing

**The project.** MARSYS-JIS ("Madhav") is an LLM-operated Jyotish (Vedic astrology) instrument. Its data plane has six layers:

| Layer | Name | What it holds |
|---|---|---|
| L0 | Brahmagyan | reference knowledge |
| L1 | Gaṇita | chart computation |
| L2 | Bodha | structural interpretation signals |
| L3 | Kāla | timing |
| L4 | Phala | outcomes |
| L5 | Mīmāṃsā | verification and calibration |

There are 127 active data "assets" across the six layers.

**The proposal.** A campaign, **Suvarṇa**, to "elevate" every asset to a single standard. It runs on an inspection engine, **Nikaṣa**, which must be finished and frozen first. An earlier campaign, **Nirmāṇa**, was stopped for falling short on quality, depth and efficiency. Its work on 98 assets is kept as a starting point, not as certification.

**Under review:**

1. `SUVARNA_CAMPAIGN_PLAN_v1_1.md` — the master plan.
2. `SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md` — how it runs autonomously.
3. `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` — three L3 asset families that get dedicated work.

**Context only (not under review):** the standard it inherits (a four-tier document chain), the engine's current state, and the predecessor's record.

## 2 · Reading order

1. **This file.**
2. **`project/CLAUDE.md`, §A–§B and §N.** The project's mission and the non-negotiable build standards. About 20 minutes.
3. **The three documents under review,** in the order above.
4. **The evidence behind them,** as needed:
   - `l3_recon/` — three reconciliation reports, each claim sourced;
   - `engine/` — the change register, the implementation plan, the freeze-test evaluation, the rulings;
   - `standard/` — the four tiers and the L0 instance.
5. **The predecessor:** `predecessor/NIRMANA_SUPERSESSION_RECORD_v1_0.md`.

## 3 · What we want from you

A verdict — **SOUND · SOUND WITH CHANGES · UNSOUND** — and a list of findings. For each finding give:

- **severity:** blocking, major or minor;
- **the evidence:** file and section;
- **the change you recommend.**

**Be adversarial.** The goal is to find what is wrong, not to agree. Figures are stated with their sources; check at least ten of them.

### 3.1 · Strategy

1. Is **"finish and freeze the engine, then certify"** the right order? Or does it delay value that could be delivered earlier without risk?
2. Is the **parallel-tracks-with-one-join** shape sound (plan §4)? Specifically:
   - Can read-only analysis across all six layers really run before the tiers are re-sealed without wasting work?
   - Does the single combined reopen at J1 risk becoming a bottleneck?
3. Is **"fix first, walk the dependency chain once"** correct? Given a 27-level map ending in a long thin chain (architecture §6)?
4. Is keeping Nirmāṇa's 98 frozen assets as a **starting point** right? Or should they be treated as unknown?
5. Is the **end state** (plan §1) measurable and complete? Is anything missing from the out-of-scope list?

### 3.2 · The standard

6. Nine core gates plus declared asset-specific additions (plan §2). Is the rule **"additions only add, never replace"** enough to stop the standard being eroded asset by asset?
7. **Only `PASS` or a justified `N/A` closes a gap.** Is "justified" defined tightly enough?

### 3.3 · Execution and autonomy

8. Are the **roles, models and effort levels** balanced (architecture §3)? Too much Opus, or too little review?
9. Are the **autonomy limits** right (architecture §7)? What is granted that should be reserved, or the reverse?
10. Does the **work queue** (architecture §4–§5) actually prevent idling? Does it prevent write collisions and database overload?
11. **Isolation** (architecture §2): is running in a separate folder with its own branches sufficient, given other campaigns share the same production database?
12. **Failure handling and restartability:** is anything likely to leave the campaign stuck?

### 3.4 · The L3 focus families

13. Is the **sequence** (F0–F4) right, given how the three families depend on one another?
14. Are the **rulings** F-0 to F-6 the right questions? Is any missing?
15. Is **generalising Gochara's generation-and-switch pattern into Kṣetra's W7** a sound idea or a trap?
16. Are the **effort ranges** plausible, given the evidence in `l3_recon/`?

### 3.5 · Risk

17. What is the **single most likely way this campaign fails?**
18. Which **native decision**, if made wrongly, costs the most?

## 4 · The bundle

Everything is in one folder: `suvarna-review-bundle/` (a zip of it is provided alongside).

| Folder | Contents |
|---|---|
| `under_review/` | the plan v1.1, the execution architecture, the L3 focus-families document, the document map |
| `l3_recon/` | GOCHARA_RECON, SANGAM_RECON, KSHETRA_RECON |
| `standard/` | tier 1 product definition, tier 2 data-plane architecture, tier 3 layer template, tier 4 asset template, the derivation chain, the L0 layer instance, the five L0 pilot briefs |
| `engine/` | the change register (v2.7), the implementation plan, the test-campaign report, the freeze-test evaluation (PHASE6_ANALYSIS), the decisions and their recommendations, the engine STATE, the three wave prompts, the bo_upaya hand-off |
| `predecessor/` | the Nirmāṇa supersession record, Nirmāṇa's unified plan, its autonomy charter |
| `project/` | CLAUDE.md, the orchestrator contract (ORCHESTRATOR_CONVERGENCE_CLOSE), PROJECT_ARCHITECTURE, CURRENT_STATE v6.87 |
| `MANIFEST.txt` | every file, its origin branch and path, and its sha256 |

**Not included, deliberately:**
- the delta ledger and census artefacts (large; figures from them are quoted with their sources);
- production database access;
- credentials.

## 5 · Known weaknesses we already see

Stated up front so you spend your time on what we have not seen:

- **None of the engine's documents or tools are on `main` yet.** Landing them is item E4.
- **The register's header tallies had drifted** and two of its rows were malformed. Both errors were ours; both are scheduled for repair (plan §5.0).
- **Estimates after the engine freeze** are deliberately not given. They come from the measured cost of the first certified dependency levels (gate G2).
- **The live L3 Gochara workstream** is outside this plan's control. It is about to switch production data before its serving code is deployed.

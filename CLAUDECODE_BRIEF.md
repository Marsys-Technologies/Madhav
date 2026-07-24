---
artifact: CLAUDECODE_BRIEF_ELEVATION_CAMPAIGN
type: CLAUDECODE_BRIEF (governing scope for execution sessions)
version: 2.0
status: ACTIVE — READY-FOR-EXECUTION (3-stream autonomous overnight run; flip to COMPLETE only
  after the run's session-close checklist validates per charter §14)
authored_by: Fable/Opus (Cowork planning session), native-commissioned 2026-07-24
authority: >
  Per CLAUDE.md §C item 0. This brief is a POINTER: the operative mandate, stream topology, lane
  assignments, file-ownership manifests, interface contracts, merge/deploy protocol, verification
  protocol and coverage matrix all live in
  00_ARCHITECTURE/llm_consumption_audit/briefs/elevation_campaign/ELEVATION_CAMPAIGN_CHARTER_v2_1.md.
  The charter's §4 ownership manifests and §12 out-of-scope list govern.
supersedes: >
  ELEVATION_CAMPAIGN_CHARTER_v1_0.md (same day — archived at
  .../briefs/elevation_campaign/archive/; do NOT execute) and
  CLAUDECODE_BRIEF_DOCTRINE_WAVES_AUTONOMOUS_CAMPAIGN v2.0 (CAMPAIGN-CLOSED 2026-07-23, D-4b ruling
  CR-128/NP-D4B-009 — archived at 00_ARCHITECTURE/briefs/).
item_of_record: 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md (v1.1, EL-01..EL-61)
mode: >
  FULLY AUTONOMOUS · overnight · zero human gates · THREE parallel streams, each with its own
  multi-agent swarm, worktrees, branches, commits, PRs, GitHub pushes, deploys and cleanup ·
  Sonnet base / Opus step-up · prod deploy + chart-scoped rebuilds authorized · every close
  Verifier-gated against live production
---

# ACTIVE BRIEF — Elevation Campaign v2.0 (SATYA-KAVACA + PŪRṆA-GRAHAṆA)

**Conductor: read the charter first, and read §0 before anything else.**
→ `00_ARCHITECTURE/llm_consumption_audit/briefs/elevation_campaign/ELEVATION_CAMPAIGN_CHARTER_v2_1.md`

Then, in order: the ELEVATION_REGISTER (v1.1, full read) · CLAUDE.md §N · CURRENT_STATE §2 (v6.41) ·
BUILD_GUARANTOR_SWARM_CHARTER (role taxonomy). Run charter §7.1 Phase 0 **once**, then spawn the
three Stream-Conductors.

**SELECTED MODE: 2 (three processes).** Kickoff text and the pre-launch clone setup:
`briefs/elevation_campaign/KICKOFF_PROMPTS_v2_1.md`. The binding protocol is charter §7.5 rules
**M2.0–M2.11** — separate clone per stream, mkdir locks with heartbeat-based breakage, a Phase-0
manifest flag with no fallback path, live-implementation signals, lock-holder-as-integration-verifier,
and γ as close deputy if α dies. α launches first and owns Phase 0, the flagship acceptance and the
close. **Do not mix modes.**

## The mandate, in one paragraph (charter §0)

The default posture for every question is deep: detailed, thorough, comprehensive, extensive. The
only exception is a demonstrably narrow, pointed question, and narrowness must be *earned* by
positive evidence — uncertainty routes to depth. For a domain question, **every remotely relevant
computed fact, pattern, chain and mathematical derivation must reach the LLM before it synthesises.**
The contract is `served ∪ explicitly-accounted-for = 100%` of the domain-relevant corpus, where the
denominator is generated from the database itself, not from hand-curated floors. **A silent omission
is a build failure, not a quality miss.** This is Lane Ω, and it is the campaign.

## The three streams (charter §1.2, §4)

- **α · SATYA — Truth & Envelope.** No response lies, starves, hides or overflows; every surface
  works. Owns `platform-mcp/src/lib|tools|resources` (minus vidhi), the L0/L1/L2 serving handlers,
  serving CI gates.
- **β · GAṆITA — Compute & Corpus.** Every number is right; every missing computation now exists.
  Owns `python-sidecar/**`, migrations, chart-scoped rebuilds, corpus.
- **γ · PŪRṆA — Depth & Intelligence.** Lane Ω plus planner coverage, dossier, assessors, muhūrta
  intelligence, calibration, battery. Owns vidhi resources, ranking, assess_domain, the new dossier.

Streams develop fully in parallel. Only the **merge queue** and the **per-target deploy lock**
serialise, for minutes. Cross-stream dependencies are satisfied by the seven **interface contracts**
published in Phase 0 (charter §7.2) — a blocked stream builds against the contract and stubs the
dependency; it never idles and never edits another stream's files.

## What DONE means (charter §9)

Four dispositions only: `VERIFIED-CLOSED` · `PREPARED-FOR-NATIVE` · `NOT-REPRODUCED` ·
`PARKED-HONEST`. There is no "passed with caveats." Nothing closes without an independent Verifier
re-running the recipe against **live production** on **both** canonical charts, with before/after
evidence captured against the Phase-0 baseline. Any question that would go to the human is answered
by the Native-Proxy agent (charter §10), which may rule on anything except weakening §0, fabricating
data, or ratifying in the native's name.

The native wakes to `ELEVATION_V2_RUN_REPORT_v1_0.md` and the five prepared packets (charter §13),
led by the **§0 mandate scorecard** and the **dark-corpus report** — what the instrument computes
and still did not serve. Target: zero.

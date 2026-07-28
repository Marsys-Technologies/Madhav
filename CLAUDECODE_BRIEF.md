---
artifact: CLAUDECODE_BRIEF_SUDDHA_VACA
type: CLAUDECODE_BRIEF (governing scope for execution sessions)
version: 1.1
status: >
  PARTIAL — Phase A/B/C/D/E/F closed 2026-07-27 for 5 of 7 P0 lanes (fixed, independently verified,
  and rebuilt into production data on both the canonical and operator E2E charts: 46 assets each,
  zero failures, zero accretion). 2 of 7 lanes remain PARKED-HONEST on an external dependency:
  PARISHODHANA PRs #827/#828. THE ARC IS NOT CLOSED. Do not flip to COMPLETE until §10 of the
  brief holds in full.
authored_by: Cowork (Opus planning session), native-commissioned 2026-07-27
history_note: >
  v1.0 of this pointer was written to disk but never git-committed, so a branch change restored the
  superseded CLAUDECODE_BRIEF_PURNA_VIRAMA content. That arc (PŪRṆA-VIRĀMA) IS genuinely closed —
  see 00_ARCHITECTURE/llm_consumption_audit/briefs/close_out/PURNA_VIRAMA_REPORT_v1_0.md — but it is
  no longer the governing scope. This v1.1 restores the correct pointer. COMMIT THIS FILE.
authority: >
  Per CLAUDE.md §C item 0. This brief is a POINTER. The operative mission, phases, rails, boundaries
  and acceptance criteria live in
  00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_BRIEF_v1_0.md,
  AS AMENDED by SUDDHA_VACA_PHASE_C_AUTHORIZATION_v1_0.md (native directive, narrows the Phase-0.2
  QUEUE-BEHIND park to two lanes and binds the ŚV↔PB concurrency protocol).
---

# ACTIVE BRIEF — ŚUDDHA-VĀCA (Purification of the Narration Layer) — PARTIAL

**Read before anything else**, in this order:
1. `00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_PHASE_C_AUTHORIZATION_v1_0.md`
2. `00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_BRIEF_v1_0.md`
3. `00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_REPORT_v1_0.md` (Phases 0/A/B/C/D/E/F — done, do not redo)
4. `00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_FIX_LEDGER_v1_0.md`

## What is DONE (do not redo)

`bo_laksana.py` (P0-5/6, L2 root) · `sudarshana_emitter.py` (P0-7) · `l3_convergence.py` (P0-8) ·
`mi_darshana.py` (P0-10) · `services/ph_nimitta/engine.py` (P0-11) · the `ph_phaladesa/engine.py`
OpenAI-allowlist one-liner · a permanent CI guard against the D1 defect class · the codebase's first
tested snapshot-and-restore mechanism.

## What REMAINS (pre-authorized — no new approval needed)

- **`lane:serve-shadbala`** — `platform-mcp/src/tools/registry_bridge.ts` (P0-1..4). Blocked on
  PARISHODHANA **#827/#828**. Needs `amjis-mcp` redeploy, no DB rebuild.
- **`lane:ga-tajaka`** — `ga_writers/ga_tajaka_writer.py` (P0-9). **L1 Gaṇita — widest blast radius
  in the ledger (L1 → L5 rebuild).**

**The one thing to understand:** the native's originating complaint — `graha_portrait` grading the
chart's strongest planet "weak" — is FIXED at the writer/data level but is **still not visible to any
user**, because that sentence is assembled in `registry_bridge.ts`, the parked serve lane. Landing
#827/#828 unblocks both remaining lanes at once. **First move of the next session: re-check those
two PRs.**

## Standing rails (unchanged)

Fix at ORIGIN, never a downstream patch masking a writer defect · narration may only RESTATE
computed facts, never add interpretation — emit an honest null instead · TEST-FIRST: prove the test
fails before fixing · every destructive rebuild is preceded by a snapshot with a TESTED rollback ·
the orchestrator contract is FROZEN · no Anthropic model in any production path · main via PR +
auto-merge only.

**Concurrency:** the PARIPRAŚNA BUILD (PB) campaign may be running in parallel (verified file-level
disjoint). PHASE_C_AUTHORIZATION §4 binds both: **Śuddha-Vāca holds rebuild exclusivity**; PB's
rebuild scope is NONE while concurrent. Confirm PB is not mid-deploy before the L1→L5 rebuild — that
is the highest-risk operation remaining in the program.

**PRIME RULE: truth over completion.** PARKED-HONEST is a legitimate close. No "passed with caveats".

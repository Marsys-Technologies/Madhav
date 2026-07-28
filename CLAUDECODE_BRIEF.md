---
artifact: CLAUDECODE_BRIEF_SUDDHA_VACA
type: CLAUDECODE_BRIEF (governing scope for execution sessions)
version: 1.2
status: COMPLETE
history_note: >
  v1.0 of this pointer was written to disk but never git-committed, so a branch change restored the
  superseded CLAUDECODE_BRIEF_PURNA_VIRAMA content. That arc (PŪRṆA-VIRĀMA) IS genuinely closed —
  see 00_ARCHITECTURE/llm_consumption_audit/briefs/close_out/PURNA_VIRAMA_REPORT_v1_0.md — but it is
  no longer the governing scope. v1.1 restored the correct pointer (committed via PR #851). This
  v1.2 records the arc's close.
authority: >
  Per CLAUDE.md §C item 0. This brief is a POINTER. The operative mission, phases, rails, boundaries
  and acceptance criteria live in
  00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_BRIEF_v1_0.md,
  AS AMENDED by SUDDHA_VACA_PHASE_C_AUTHORIZATION_v1_0.md. Full close evidence:
  SUDDHA_VACA_REPORT_v1_0.md's "Phase C2/D2/E2/F2" section (v1.3) +
  SUDDHA_VACA_FIX_LEDGER_v1_0.md (v1.2).
---

# CLOSED BRIEF — ŚUDDHA-VĀCA (Purification of the Narration Layer) — COMPLETE

**Status is `COMPLETE`.** Per CLAUDE.md §C item 0, a session opening with this file at `COMPLETE`
skips items 1-16 of this brief's own reading chain and proceeds with normal CLAUDE.md §C orientation.
Retained in place for audit trail; do not delete.

## Final disposition — all 7 of 7 P0 lanes VERIFIED-FIXED

| Lane | Defect | Disposition |
|---|---|---|
| P0-1..4 `lane:serve-shadbala` | `registry_bridge.ts` Ṣaḍbala serve-side chain | VERIFIED-FIXED, PR #852, deployed |
| P0-5/6 `lane:bo-laksana` | `bo_laksana.py` fact_key mis-selection | VERIFIED-FIXED, PR #838, rebuilt |
| P0-7 `lane:bo-sudarshana` | `sudarshana_emitter.py` valence/agreement conflation | VERIFIED-FIXED, PR #836, rebuilt |
| P0-8 `lane:ka-convergence` | `l3_convergence.py` self-inclusion | VERIFIED-FIXED, PR #835 |
| P0-9 `lane:ga-tajaka` | `ga_tajaka_writer.py` hardcoded orb | VERIFIED-FIXED, PR #853, L1→L5 rebuilt both charts |
| P0-10 `lane:mi-darshana` | `mi_darshana.py` grade=0.0 truthiness | VERIFIED-FIXED, PR #839, rebuilt |
| P0-11 `lane:ph-nimitta-engine` | `ph_nimitta/engine.py` direction fallback | VERIFIED-FIXED, PR #837, rebuilt |
| P2 | `ph_phaladesa/engine.py` OpenAI allowlist hole | VERIFIED-FIXED, PR #837 |
| C.7 | Systemic fact-category-pin-lint CI guard | VERIFIED-FIXED, PR #840, live on main |

**The native's originating complaint** — `graha_portrait` grading the Sun "weak" when it is the
chart's strongest planet — is fixed end-to-end: writer-level, serve-level, and (the same defect
class, independently) in the Tajika annual-chart writer. Live-verified on the canonical chart,
all 7 grahas matching the brief's golden table exactly.

**Six items remain honestly open**, all correctly PARKED-HONEST/NOT-APPLICABLE as real,
out-of-authorization findings for a future wave (see SUDDHA_VACA_REPORT_v1_0.md's disposition
table for full detail): `ga_structural_writer.py` P0-shaped L1 defect · migration 339 OpenAI-in-
CHECK-constraint · `mi_darshana.py` verdict_note tradition-blindness (PLAUSIBLE) ·
`bo_laksana_rerank` watchdog timeout (self-healed, operational) · `mi_gunanaka.py:337`
snapshot-publish bug · `ka_gochara_sweep` operator-chart error (pre-existing since 2026-07-26,
unrelated).

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

---
artifact: CLAUDE_CODE_PROMPT_PHASE_B_WAVE_0.md
canonical_id: CLAUDE_CODE_PROMPT_PHASE_B_WAVE_0
version: 1.0
status: READY — Phase B Wave 0 (L0 reference-table fixes). Per-wave gated: fix → verify-on-data → report → WAIT. NO seal, NO next wave.
authored_by: Cowork 2026-06-23
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v1_0.md (Phase B, Wave 0 of 5)
map: FOUNDATION_ROOT_CAUSE_MAP.md (Gate-A-COMPLETE; §8/§13 wave schedule)
gate: native+Cowork approved Gate A 2026-06-23; Phase B runs per-wave gated (each wave reports + waits)
---

# Phase B — Wave 0: L0 Reference-Table Fixes

> First FIX wave (Phase B changes data for the first time). Per-wave gated rhythm: FIX → REBUILD/verify on
> live DATA → REPORT the data-proof → **STOP and WAIT for native+Cowork go before Wave 1.** No seal.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Execute **Phase B WAVE 0** of the
Foundation Integrity Campaign — the L0 reference-table root-cause fixes. **READ FIRST:**
`00_ARCHITECTURE/FOUNDATION_ROOT_CAUSE_MAP.md` (the Gate-A map — find the L0 findings L0-W1 + L0-W2 and
their PROPOSED FIX sections) + `00_ARCHITECTURE/FOUNDATION_INTEGRITY_CAMPAIGN_v1_0.md` (doctrine).

**This wave's scope — EXACTLY these two L0 findings, nothing else:**
- **L0-W1 (F7) — Rahu/Ketu exaltation conflict:** `reference_planets` and `bg_dignity_reference` disagree
  on the same classical fact (Rahu/Ketu exaltation signs). Two authoritative L0 tables give different
  answers → any L1 dignity computation for Rahu/Ketu silently differs by which table it reads.
- **L0-W2 (F6) — Mercury atichara threshold:** `bg_motion_state_thresholds` Mercury atichara (accelerated-
  motion) threshold is set to a physically unreachable value → the atichara state can never fire for Mercury.

**REFRAME (native 2026-06-23): the deliverable is CORRECT CODE/reference-data + a guard against recurrence,
NOT a preserved dataset.** Data is disposable (regenerable via the Build tracker). For Wave 0 (L0 reference
tables) the "code" IS the canonical reference values + the seed/migration logic that writes them + a guard
so the two tables can't diverge again. Fix the VALUES correctly AND fix the source-of-truth so a future
re-seed stays correct. Don't just patch rows — make the writer/seed produce the right value canonically.

**RAILS:** Full latitude to fix RIGHT. DATA-FIRST verification: prove the fix against the live DB. Determine
the CORRECT classical value from authoritative source (BPHS / standard Jyotish reference) — do NOT guess;
if genuinely ambiguous (two legitimate traditions), STOP and ask. Gemini/DeepSeek + Claude-in-Code allowed
(dev-time). Canonical chart 482012f1 not the subject here (global reference tables) — but a quick rebuild
of anything that READS these tables for the native (e.g. ga_condition dignity for Rahu/Ketu) is the
proof-build that confirms the fix flows correctly.

### THE FIXES
1. **L0-W1:** Determine the CORRECT classical exaltation signs for Rahu + Ketu (note: classical sources DO
   vary on this — Rahu exalts in Taurus or Gemini depending on tradition; Ketu in Scorpio or Sagittarius.
   This is exactly the "STOP and ask if ambiguous" case — if reference_planets and bg_dignity_reference
   encode two LEGITIMATE traditions, the fix may be to pick the project's canonical one + document it, NOT
   to assume one is "wrong"). Reconcile the two tables to ONE canonical value (migration), and add a guard
   so future reads can't diverge (single source of truth). Report which value you chose + the source.
2. **L0-W2:** Determine the correct Mercury atichara threshold (Mercury's max daily motion is ~2.2°/day;
   the threshold must be reachable within Mercury's real speed range). Fix the value in
   bg_motion_state_thresholds (migration). Confirm against Mercury's actual ephemeris speed range.
   Parallel-safe with L0-W1 — same migration, different rows.

### VERIFY ON DATA (the wave's gate — this is the proof, not "looks fixed")
- L0-W1: `SELECT` both tables post-fix → Rahu/Ketu exaltation now AGREES across reference_planets +
  bg_dignity_reference. Then spot-check: does an L1 dignity read for Rahu/Ketu now return a single
  consistent answer? (Re-run the relevant ga_condition/ga_structural derivation for the native if cheap, or
  at minimum prove the two source tables now match.)
- L0-W2: prove the Mercury atichara threshold is now within Mercury's real speed range (compare to the
  ephemeris max ~2.2°/day) — i.e. the state CAN now fire. If feasible, show a date where Mercury's speed
  crosses the new threshold.
- **No regression:** confirm no OTHER reference values changed; FORENSIC 7/7 still passes (these L0 fixes
  must not perturb the confirmed-sound chart base).

### DEPLOY + RECORD
- Migration in platform/supabase/migrations (next free number); apply via the proxy; push (auto-deploys).
- Update FOUNDATION_ROOT_CAUSE_MAP.md: mark L0-W1 + L0-W2 status FIXED-VERIFIED with the data-proof + the
  chosen values/sources. Do NOT touch other findings' status.

### STOP — REPORT + WAIT (do NOT start Wave 1, do NOT seal)
Report: the correct values chosen + their classical source; the migration; the DATA PROOF for each (the
agreement query + the threshold-reachability check); FORENSIC still 7/7; the deployed revision. Then STOP.
**Per-wave gate: the native + Cowork review this data-proof and give explicit GO before Wave 1 runs.** If
L0-W1's correct value was ambiguous (two legitimate traditions), STOP and surface the choice rather than
deciding it autonomously — it's a canonical-tradition decision for the native.

---
*End. Wave 0 = the 2 L0 reference fixes (Rahu/Ketu exaltation reconciliation, Mercury atichara threshold),
fixed-right, verified ON DATA (tables agree + threshold reachable + FORENSIC intact), reported, then WAIT
for go. The low-risk wave that proves the Phase-B rhythm before the L2 convergence wave. NO seal, NO Wave 1.*

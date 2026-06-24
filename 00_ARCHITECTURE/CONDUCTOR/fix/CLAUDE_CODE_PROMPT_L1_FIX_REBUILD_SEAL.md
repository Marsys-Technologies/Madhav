---
artifact: CLAUDE_CODE_PROMPT_L1_FIX_REBUILD_SEAL.md
canonical_id: CLAUDE_CODE_PROMPT_L1_FIX_REBUILD_SEAL
version: 1.0
status: READY — L1 fix→rebuild→seal. Read-from-L0 architectural fix for 7 bypasses + ga_dashas vocab + ga_yoga root-cause fix. Then L2.
authored_by: Cowork 2026-06-23
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md — layer-by-layer full-close. L0 SEALED ✓. L1 audit reconciled.
audit: L1_SOUNDNESS_REPORT.md
native_decisions: "Bypasses → READ-FROM-L0 (delete private copies + guard). ga_yoga → diagnose root first. Fix order: ga_dashas vocab FIRST (may self-heal ga_yoga)."
---

# L1 Gaṇita — Fix → Rebuild → Seal

> L1 audit reconciled with native. Implement the DECIDED fixes, rebuild L1 on the sealed L0, verify the
> Rahu/Ketu fix PROPAGATES (Lens-2 was NO; this is where it becomes YES), seal L1. Then L2.
> Full latitude. DATA-FIRST verification. The fixes run in a SPECIFIC ORDER (below).

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Execute L1 Gaṇita fix → rebuild →
seal. **READ FIRST:** `L1_SOUNDNESS_REPORT.md` (the findings) + `L0_SEAL_v1_0.md` (what L0 now canonically
provides) + `FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md`. Full latitude to fix RIGHT (fix the WRITER so any
future build is correct). DATA-FIRST: prove every fix on the live DB. Frozen contract for writers touched.
Canonical chart 482012f1 rebuilt freely (data disposable). FORENSIC 7/7 must hold throughout.

### THE NATIVE-DECIDED FIXES — run in THIS ORDER (sequencing matters)

**FIX 1 (FIRST) — ga_dashas ayanamsha vocabulary (F7, highest blast radius).**
chart_dashas uses `lahiri/kp/surya_siddhanta`; chart_facts + L0 use canonical
`lahiri_chitrapaksha/krishnamurti/surya_siddhanta_classical`. The mismatch makes any dāśā↔fact JOIN return
0 rows for 3/5 ayanamshas — stack-wide. Fix the WRITER (ga_dashas / ga_dashas_writer) to emit the canonical
ayanamsha labels + migrate existing rows. ALSO fix the bypass here: ga_dashas hardcodes
`NAKSHATRA_LORDS_1BASED` — replace with a READ from L0 (bg_nakshatra / reference_nakshatra nakshatra-lords).
PROVE: dāśā↔chart_facts JOIN now returns rows for ALL 5 ayanamshas; nakshatra-lords match L0.

**FIX 2 — The 7 L0-BYPASSES → READ-FROM-L0 (the architectural fix; delete the private copies).**
For each, DELETE the inline classical-fact constant and make the writer READ it from the L0 source of truth
(so the Rahu/Ketu fix + any future L0 correction auto-propagate):
- **ga_structural** (`ga_structural_writer`): delete `EXALTATION_SIGNS`/`DEBILITATION_SIGNS` inline maps
  (esp. Rahu="Gemini"/Sagittarius — the frozen wrong value) → read exaltation/debilitation from
  `bg_dignity_reference`. (Re-check its other inline constants flagged in the audit's 92-count — convert any
  that are duplicated L0 facts; leave genuine computational constants.)
- **ga_condition** (`ga_condition_writer`): delete the stale `_EXALTATION`/`_DEBILITATION` FALLBACK
  constants for Rahu/Ketu (the writer already reads bg_dignity_reference via _load_dignity_ref() — the
  fallback is what would re-poison on rebuild; remove it so the L0 read is authoritative). Fix the hardcoded
  Mercury `sama_hi=2.5` → read the bg_motion_state_thresholds value (now 2.0).
- **ga_sensitive** (`ga_sensitive_writer`): delete inline `SIGN_LORDS` + `NAK_LORDS` → read from L0
  (reference_signs sign-lords; bg_nakshatra/reference_nakshatra nakshatra-lords).
- **(ga_dashas nakshatra-lords handled in FIX 1.)**
- **ADD A GUARD TEST:** assert no L1 writer hardcodes an L0-owned classical fact (exaltation/debilitation/
  sign-lord/nakshatra-lord) — grep-based or value-cross-check — so this bypass class can't recur. This is
  the durable outcome (mirrors L0's cross-table guard).
PROVE: each rewired writer now reads L0; no inline L0-fact copies remain; the guard passes.

**FIX 3 — REBUILD L1 + confirm Rahu/Ketu PROPAGATION (Lens-2 NO → YES).**
After Fix 1+2, rebuild L1 for the native via the orchestrator (ga_positions → … → ga_condition →
ga_structural → ga_yoga → …). Then CONFIRM ON DATA the headline:
`SELECT graha, dignity, score FROM ga_condition_composite WHERE chart_id='482012f1-...' AND graha IN ('Rahu','Ketu')`
→ Rahu (in Taurus) now = **exalted, 1.0** (not friend_sign/0.6); Ketu likewise per the corrected canon.
And ga_structural no longer emits Rahu-exalts-Gemini. This proves the L0 fix PROPAGATED — the whole point.

**FIX 4 — ga_yoga (F6): DIAGNOSE ROOT FIRST, then fix.**
After Fix 1 (the dāśā vocab), RE-CHECK ga_yoga — it may partly self-heal if it was STARVED by the broken
dāśā↔fact JOIN. Then diagnose the REMAINING gap: why do only 1-of-N yogas fire (raja yogas, Sasa
Mahapurusha, etc. missed; constituent_fact_ids=[]; strength=null)? Determine the real root — (a) bg_yogas
catalog incomplete, (b) the firing/matching logic too strict or buggy, (c) the constituent_fact linkage
broken, (d) still starved by some other join. Fix the actual root (could partly be upstream). Yogas are
central to chart reading — fix it PROPERLY, not a patch. PROVE: ga_yoga_firings now fires the genuinely-
present yogas for the native with populated constituent_facts + non-null strength; the count is
classically sensible (not 1).

### SEAL L1 (the gate — data-verified, then STOP)
Verify on live data BEFORE sealing:
- dāśā↔chart_facts JOIN works for all 5 ayanamshas (Fix 1).
- All 7 bypasses gone — writers read L0; the no-hardcoded-L0-fact guard passes (Fix 2).
- Rahu/Ketu dignity in ga_condition_composite + ga_structural now reflect the L0 canon (exalted in Taurus/
  Scorpio); the L0 fix PROPAGATED (Fix 3) — this is THE proof L0→L1 inheritance is now real.
- ga_yoga fires a classically-sensible set with populated facts + strength (Fix 4).
- FORENSIC 7/7 still passes; ga_positions/ga_structural still SOUND post-rebuild.
- An intra-L1 consistency mini-sweep (like L0's): any constant L1 still duplicates internally agrees.
Write `L1_SEAL_v1_0.md`: fixes + data-proof for each + the bypass→read-L0 conversions + the guard + the
Rahu/Ketu propagation proof + ga_yoga before/after. Update FOUNDATION_ROOT_CAUSE_MAP → L1 findings
FIXED-VERIFIED-SEALED. **STOP — do NOT start L2.** Report the L1 seal evidence for native+Cowork review.

---
*End. L1: fix ga_dashas vocab FIRST (stack-wide JOIN break) + its nakshatra-lord bypass; convert all 7
L0-bypasses to READ-FROM-L0 (+ guard) — makes L0 truly load-bearing; rebuild + CONFIRM Rahu/Ketu propagated
(NO→YES, the headline); diagnose+fix ga_yoga's near-empty firing (re-check after the dāśā fix first). Seal
with data-proof + FORENSIC intact + intra-L1 sweep. STOP before L2.*

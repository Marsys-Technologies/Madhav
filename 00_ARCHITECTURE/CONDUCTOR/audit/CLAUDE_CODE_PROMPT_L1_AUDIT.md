---
artifact: CLAUDE_CODE_PROMPT_L1_AUDIT.md
canonical_id: CLAUDE_CODE_PROMPT_L1_AUDIT
version: 1.0
status: READY — L1 Gaṇita thorough audit (Stage 1 of L1 full-close). Carries the L0-bypass + Rahu/Ketu-propagation lenses. ASSESS ONLY.
authored_by: Cowork 2026-06-23
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md — layer-by-layer full-close. L0 SEALED ✓. This is L1 Stage 1 (audit).
context: A bypass-smell scan shows heavy inline constants in L1 writers (ga_structural 92, ga_condition 43, ga_yoga 24...) with most reading_L0=0 — the bypass fear looks REAL here. The audit must settle it.
---

# L1 Gaṇita — Thorough Audit (Stage 1 of the L1 full-close cycle)

> L0 is SEALED. L1 = the COMPUTED CHART (positions, dignities, dāśās, the relationship graph) — the first
> real consumer of L0. Audit thoroughly: 3 assets are deep-done (ga_positions SOUND, ga_structural SOUND,
> ga_dashas WRONG[ayanamsha vocab]); the other 13 + the cheap census are PENDING. Carries TWO special
> lenses this layer demands: (1) L0-BYPASS (does the writer read L0 or hardcode private copies?), (2)
> RAHU/KETU PROPAGATION (does the dignity output reflect the L0 fix?). ASSESS ONLY — no fix, no build, no seal.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Thoroughly audit LAYER 1 (Gaṇita
— the 16 ga_* assets) for chart `482012f1-710e-4a25-994a-93821f5871aa`. **READ FIRST:**
`FOUNDATION_ROOT_CAUSE_MAP.md §3` (prior L1 leads) + `L0_L4_SOUNDNESS_AUDIT_SPEC_v1_0.md` (method) +
`L0_SEAL_v1_0.md` (what L0 now canonically provides — Rahu/Ketu=Taurus/Scorpio, etc.). **ASSESS ONLY —
apply no fix, change no data, run no build, seal nothing. Verify against the live DB + the cited source.**

**The 16 L1 assets + dependency order (audit bottom-up within L1):**
ga_positions (root — reads L0+ephemeris) → ga_vargas, ga_dashas, ga_strength, ga_sensitive, ga_panchanga,
ga_nakshatra (each ← ga_positions; ga_sensitive also ← bg_reference; ga_nakshatra ← bg_nakshatra) →
ga_structural (← positions+strength+panchanga+sensitive+vargas+dashas+nakshatra) → ga_condition (← pos+
vargas+dashas), ga_tajaka, ga_sade_sati → ga_yoga (← structural+dashas), ga_vastu (← condition),
ga_medical (← condition+positions), ga_prashna, ga_transit_anchors.
**REUSE as settled:** ga_positions (SOUND, FORENSIC-7/7), ga_structural (SOUND — but RE-CHECK its 92
inline constants per the bypass lens below), ga_dashas (WRONG — ayanamsha vocab F7, fold in, confirm).
Deep-audit the other 13 + run the L1 cheap census (never ran).

### PER-ASSET METHOD (SPEC §5 deep): census → stratified sample → read writer → INDEPENDENTLY re-derive
from upstream (L1 re-derives against chart_facts + L0 reference values) → 3 lenses → null/FK → silent-default
scan → verdict SOUND/SUSPECT/WRONG (WRONG/DEFERRED/SOUND for ambiguous) + downstream-impact chain for WRONG.

### LENS 1 (CRITICAL — L0 BYPASS): for EVERY ga_* writer, separate two kinds of constant:
- **Legitimate computational constants** (math: degrees-per-sign=30, ayanamsha offsets, ephemeris params)
  — fine, leave them.
- **Duplicated L0 CLASSICAL FACTS** (exaltation/debilitation signs, sign lords, nakshatra lords/spans,
  planetary friendships, dignity rules) — these L0 OWNS (reference_planets / bg_dignity_reference /
  bg_nakshatra / reference_signs). For each such fact the writer uses: does it READ it from L0, or carry a
  PRIVATE inline copy? A private copy = a BYPASS finding (the L0 fix never reaches it; it can drift).
The bypass-smell scan flags heavy inline constants: **ga_structural_writer.py (92), ga_condition_writer.py
(43), ga_yoga_writer.py (24), ga_sensitive_writer.py (21), ga_vargas_writer.py (19), ga_sade_sati_writer.py
(11), ga_tajaka_writer.py (10)** — most with reads_L0=0. INVESTIGATE each: how many of those inline
constants are duplicated L0 facts (a bypass) vs legitimate computation? Report a BYPASS COUNT per writer.

### LENS 2 (CRITICAL — RAHU/KETU PROPAGATION): the headline question.
**ga_condition is the DIGNITY writer + reads Rahu/Ketu exaltation.** Determine, ON DATA: does the native's
ga_condition output for Rahu/Ketu now reflect the L0 fix (Taurus/Scorpio → Rahu in Gemini = NEUTRAL,
Ketu in Sagittarius = neutral), or does it still show the OLD value (Rahu exalted) because ga_condition
computes dignity from one of its 43 INLINE constants instead of reading bg_dignity_reference?
- If ga_condition READS L0 → the fix propagated; confirm the live dignity values flipped.
- If ga_condition HARDCODES dignity → it's a BYPASS bug: the L0 fix did NOT reach it; the native's Rahu/Ketu
  dignity is STILL WRONG in the data. This would be a major L1-WRONG finding.
- Trace the same for ga_structural, ga_yoga, ga_medical, ga_vastu (all consume dignity downstream).
Report explicitly: did the Rahu/Ketu L0 fix PROPAGATE to L1's dignity outputs, or is it bypassed?

### EXECUTION: layer-by-layer within L1, mostly sequential / ≤2-3 parallel where file-disjoint, RESUMABLE,
findings written incrementally (an API-529 costs one asset). Source-verify any classical fact (don't trust
a writer's inline value or comment as authority — verify vs the cited text / L0's now-canonical value).

### OUTPUT — write `L1_SOUNDNESS_REPORT.md`
Per-asset verdict + DATA + source evidence + re-derivation + impact chain + family tag (F1–F8) +
PROPOSED-FIX scope for WRONG. **A dedicated §BYPASS section: per-writer bypass count (duplicated-L0-facts
carried inline vs read-from-L0), and the headline Rahu/Ketu propagation verdict (did the L0 fix reach L1's
dignity, yes/no).** The tally + the single most important finding. NO fix, NO build, NO seal. STOP for
native+Cowork reconciliation → then L1 fix → rebuild → seal → L2.

> Note for the eventual L1 FIX: where a writer bypasses L0 with a private copy of an L0 fact, the right fix
> is "read from L0" (makes L0 the true single source of truth + auto-inherits the Rahu/Ketu fix) — but
> that's the FIX stage; this stage only ASSESSES + reports the bypasses.

---
*End. L1 deep audit: 13 PENDING ga_* + census, reuse the 3 done, bottom-up within L1. TWO special lenses —
L0-bypass (the inline-constant scan shows it's likely widespread: ga_structural 92, ga_condition 43...) and
Rahu/Ketu propagation (did the L0 dignity fix actually reach ga_condition's output, or is it hardcoded-
bypassed?). Source-verified, resumable. → reconcile → fix → rebuild → seal. ASSESS ONLY.*

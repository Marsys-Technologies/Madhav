---
artifact: CLAUDE_CODE_PROMPT_TARGETED_FOUNDATION_AUDIT.md
canonical_id: CLAUDE_CODE_PROMPT_TARGETED_FOUNDATION_AUDIT
version: 1.0
status: READY — the single-session targeted Phase-A diagnosis: deep on flagged set + cheap census on all 69 + impact/schedule. ASSESS ONLY, NO FIX, NO SEAL.
authored_by: Cowork 2026-06-23
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v1_0.md (this is the scoped Phase A)
spec: L0_L4_SOUNDNESS_AUDIT_SPEC_v1_0.md (method reference)
---

# Targeted Foundation Audit — single session

> Native chose the targeted scope: DEEP audit the known-suspect set, CHEAP distribution-census across all
> 69 (the safety net for the ka_sangam blind spot), produce impact chains + rebuild schedule. Replaces the
> 5-layer deep audit with one focused pass. ASSESS ONLY — no fix, no seal.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Run the TARGETED foundation
diagnosis for chart `482012f1-710e-4a25-994a-93821f5871aa`. **READ FIRST:**
`00_ARCHITECTURE/FOUNDATION_INTEGRITY_CAMPAIGN_v1_0.md` (doctrine + the 8 root-cause families) +
`00_ARCHITECTURE/CONDUCTOR/audit/L0_L4_SOUNDNESS_AUDIT_SPEC_v1_0.md` (method). **ASSESS ONLY — apply NO fix
(drafts are text only), change no data, seal nothing. Verify against the live DB, not docs/code claims.**

Doctrine (why this exists): bugs in this codebase are PLAUSIBLE-BUT-WRONG — they pass tests + light the
cockpit green while being wrong (all-Jupiter, Capricorn, CGM-all-0.506). A 2-row glance MISSES them: the
glance said ka_sangam was "8 grahas, healthy"; deep verification found 3 critical bugs under it. So: DEEP
where we know there's smoke, CHEAP-WIDE everywhere (the census catches the degenerate class a glance missed).

### PART 1 — DEEP AUDIT the known-suspect set (full method)
Apply the SPEC §5 deep method (distribution census → stratified ~8-12 row sample → read writer → INDEPENDENTLY
re-derive from upstream → 3 lenses → null/FK aggregate checks → silent-default code scan → verdict) to:

**The 16 map-fill anomalies + the 3 convergence-cluster bugs + each one's IMMEDIATE UPSTREAM:**
- **L2:** bodha_cgm_nodes/edges (#3 all strength=0.506, edges NULL) ; bodha_rm_resonances (#4 all 0.28) ;
  bo_laksana (#6 top-signal skew; + it's the L2 root — re-derive its projection of L1) ; bo_sangati (CDLM
  vocab #7-adjacent — confirm the spiritual/psychological/financial fix) ; bodha_msr_signals (the
  eligibility_score-NULL + fact_value_num-overload source — CRITICAL, this is the convergence root) .
- **L3:** ka_yojaka (builds predicates — the eligibility_score + fact_value_num + signature_class logic;
  the convergence cluster's true home) ; ka_sangam (the 3 confirmed bugs — fold in, confirm, don't
  re-litigate) ; kala_jivana_parva (#11 epoch 1950-vs-1984 + null scores) ; kala_activation_predicates
  (#7 ranking) ; kala_convergence/activation/darshana/bhavishya (#8/#9/#10/#16 — pre-fix states; note as
  blocked-on-convergence-fix, don't deep-re-audit the pre-fix data).
- **L4:** phala_muhurta (#13 all-identical travel/Mercury/0.3) ; ph_pratikara (#14 — downstream artifact,
  confirm it's purely inherited not its own bug) ; phala_sodhana (#12 pre-fix).
- **L1:** chart_divisionals (#2 graha='ALL' null rows) ; ga_yoga_firings (#5 only 1 yoga — strict-criteria
  vs build-gap?) ; + ga_positions (re-derive vs FORENSIC anchors — the root the whole chart rests on, audit
  it even though unflagged, because if IT is wrong everything is).
- **L0:** bg_texts/bg_compendium_index (#1 OCR garble — scope: do garbled chunks feed live interpretation?) ;
  + bg_ephemeris (spot-check positions vs an independent ephemeris — the deepest foundation, audit despite
  being unflagged).
For each: classify SOUND / SUSPECT / WRONG, and for ambiguous (uniform/null) values, re-derivation must
settle WRONG (logic computes it wrong) vs DEFERRED (deliberate unbuilt stub) vs SOUND. For WRONG, draft the
fix scope in a "PROPOSED FIX (not applied)" subsection (evidence precedes draft).

### PART 2 — CHEAP DISTRIBUTION-CENSUS across ALL 69 assets (the safety net)
For EVERY asset (all 69, including the ones not deep-audited), run the cheap census ONLY — no re-derivation,
no code reading:
- For each meaningful column: `SELECT col, count(*) ... GROUP BY col ORDER BY 2 DESC` (chart-scoped where
  applicable). FLAG any column that collapses to ~1 distinct value where diversity is expected (the
  degenerate-uniform signature — all-Jupiter / all-0.506 class). This is the ka_sangam blind-spot guard:
  it catches a critical degenerate bug in an asset the 2-row glance passed.
- Null-rate per column (100% null where data expected = silent gap).
Any census flag on a NON-deep-audited asset → promote it to a SUSPECT finding for follow-up (note it; the
native decides whether to deep-audit it before fixing).

### PART 3 — DOWNSTREAM-IMPACT + REBUILD SCHEDULE (for confirmed-WRONG assets)
- For each WRONG asset: compute its VERIFIED transitive downstream closure (registry depends_on via
  plan.ts transitiveDownstream — but VERIFY each edge against what the writer actually READS; flag
  under-declared hidden deps — the dangerous ones). Output "fixing <X> requires rebuilding [list]".
- Build the MASTER REBUILD SCHEDULE: topo-order the WRONG assets + downstreams into WAVES (Wave N only
  rebuilds assets whose every broken-upstream was fixed in a prior wave; a downstream of 2+ broken
  upstreams waits for the last; independent broken assets share a wave = parallel-safe). Flag large-cascade
  fixes + parallel-safe groups + the depends_on edge corrections to apply.

### OUTPUT — write `00_ARCHITECTURE/FOUNDATION_ROOT_CAUSE_MAP.md`
- Part 1 deep findings: per-asset verdict (SOUND/SUSPECT/WRONG; WRONG/DEFERRED/SOUND for ambiguous) +
  data evidence + re-derivation + PROPOSED-FIX drafts, grouped by root-cause family (F1–F8).
- Part 2 census results: the all-69 distribution/null scan, with any NEW degenerate flags on
  previously-clean assets promoted to SUSPECT.
- Part 3: the verified downstream-impact chains + the MASTER REBUILD SCHEDULE (the wave plan) + the
  depends_on edge corrections.
- A "single most important finding" + the overall tally.
**Rails:** read-only, no fix applied, no seal; live DB via Cloud SQL proxy; Gemini/DeepSeek + Claude-in-Code
for astrological judgment (dev-time, allowed); FORENSIC anchors = Sun Capricorn · Moon Purva Bhadrapada ·
Lagna Aries (×5) · Tithi Shukla Tritiya · Vara Ravivara · Yoga Shiva · Karana Garaja. STOP and report; the
native + Cowork review the map before Phase B (fixes).

---
*End. One targeted session = deep audit the flagged set + immediate upstreams + the always-audit roots
(ga_positions, bg_ephemeris), cheap distribution census across all 69 (the blind-spot net), and the
impact-chains + master rebuild schedule. Produces FOUNDATION_ROOT_CAUSE_MAP = the Phase-B spine. ASSESS
ONLY, NO FIX, NO SEAL.*

---
artifact: CLAUDE_CODE_PROMPT_L2_AUDIT.md
canonical_id: CLAUDE_CODE_PROMPT_L2_AUDIT
version: 1.0
status: PRE-STAGED — L2 Bodha audit (Stage 1 of L2 full-close). Run ONLY after L1 is sealed-in-data (dasha JOIN verified all 5 ayanamshas). ASSESS ONLY.
authored_by: Cowork 2026-06-24
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md — layer-by-layer full-close. L0 SEALED ✓. L1 sealed-in-code, data-commit pending (HARD L2 GATE).
note: L2 is the CONSEQUENTIAL layer — the convergence-root cluster (bo_laksana salience, CGM, eligibility, fact_value_num overload) lives here. Several map findings already confirmed; this audit deep-confirms + finds the rest.
---

# L2 Bodha — Thorough Audit (Stage 1 of the L2 full-close cycle)

> **GATE: do NOT run this until L1 is sealed IN DATA** — the dasha↔chart_facts JOIN must verify live for
> all 5 ayanamshas first (ga_dashas committed). L2's bo_laksana reads L1; auditing on a broken L1 JOIN =
> auditing corrupt input. L0 SEALED ✓, L1 sealed-in-code (data pending). Once L1-in-data is confirmed, run.
> ASSESS ONLY — no fix, no build, no seal.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Thoroughly audit LAYER 2 (Bodha —
the synthesis layer) for chart `482012f1-710e-4a25-994a-93821f5871aa`. **PRECONDITION CHECK FIRST:** confirm
L1 is sealed IN DATA — `SELECT d.ayanamsha_id, count(*) FROM chart_dashas d JOIN chart_facts f ON
f.fact_subject LIKE '%_'||d.ayanamsha_id WHERE d.chart_id='482012f1-...' GROUP BY 1` returns rows for ALL 5
ayanamshas. If NOT, STOP — L1 isn't sealed; do not audit L2 on corrupt L1 input. **READ FIRST:**
`FOUNDATION_ROOT_CAUSE_MAP.md` (the confirmed L2 findings — convergence cluster) + `L1_SEAL_v1_0.md` (what
L1 now correctly provides) + `L0_SEAL_v1_0.md` + `L0_L4_SOUNDNESS_AUDIT_SPEC_v1_0.md`. ASSESS ONLY — no
fix, no build, no seal. Verify against the live DB + cited sources.

**The 10 L2 assets + dependency order (audit bottom-up within L2):**
bo_laksana (root ← ga_structural + bg_rules) → bo_karanajala, bo_bimba, bo_samskara, bo_sangati, bo_samvada
(each ← bo_laksana) → bo_upaya (← bo_laksana + bo_sangati), bo_drishti (← bo_laksana + bo_sangati +
bo_karanajala) → bo_anveshana (← bo_sangati + bo_karanajala + bo_samskara + bo_drishti) → bo_pramana_mapa
(← bo_upaya + bo_drishti + bo_anveshana). (Reconcile the bo_2-5/6/7/8.py alt-named files against the
registry asset_ids first.)

**ALREADY-CONFIRMED findings to DEEP-VERIFY (from the map; not settled until re-proven on data):**
- **bo_laksana `_compute_salience()` — THE convergence root.** The map says salience collapses to near-
  uniform midpoints because graha is extracted from a usually-empty JSONB tag instead of `fact_key`. DEEP-
  VERIFY on data: is salience genuinely near-uniform (degenerate F1), and is the fix "extract graha from
  fact_key (split on ':')" correct? This is the single most important L2 asset — everything downstream
  inherits its salience ranking.
- **bo_sangati CDLM vocabulary drift (F7):** KNOWN_DOMAINS uses spirituality/character/wealth vs canonical
  spiritual/psychological/financial → joins from phala_anchors silently miss. CONFIRM whether the fix
  landed or it's still divergent (check the writer's KNOWN_DOMAINS + the stored bodha_cdlm_cells labels).
- **bo_cgm (bodha_cgm_nodes/edges) all strength=0.506, edges NULL (F1):** WRONG-vs-DEFERRED — does the
  writer ATTEMPT to differentiate and fail (bug) or never compute it (deliberate stub)? Re-derivation decides.
- **bodha_rm_resonances all 0.28 (F1):** same WRONG-vs-DEFERRED determination.

**Per-asset DEEP method (SPEC §5):** census → stratified sample → read writer → INDEPENDENTLY re-derive from
upstream (L2 re-derives against L1 ga_* + L0; bo_laksana faithfully projects ga_structural?) → 3 lenses →
null/FK → silent-default scan → verdict SOUND/SUSPECT/WRONG (WRONG/DEFERRED/SOUND for ambiguous) + downstream-
impact chain for WRONG.

### THE L2 LENSES (carry from L0/L1 + L2-specific):
1. **FAITHFULNESS to L1 (primary for L2):** does each bo_* faithfully consume its upstream (bo_laksana for
   most; ga_structural for bo_laksana), or RESTATE/MUTATE values (the L-is-authority check)? Now that L1 is
   sealed, does L2 actually READ the corrected L1 data (e.g. the now-exalted Rahu/Ketu dignity flows into
   bo_laksana's signals correctly), or does L2 carry stale/private copies?
2. **L0/L1 BYPASS:** bo_laksana has 18 constant/salience markers — separate legitimate computation from
   duplicated L0/L1 facts carried inline (a bypass). Report a bypass count per writer.
3. **DEGENERATE-DISTRIBUTION (high-yield here):** the census is critical — CGM (0.506), resonance (0.28),
   salience (near-uniform) are all the F1 collapse class. Run it hard on every scoring/strength/graph column.
4. **CONVERGENCE-ROOT depth:** bo_laksana salience + the eligibility/ranking the map flagged — these feed L3
   ka_yojaka/ka_sangam. Characterize them fully; they're the cluster everything-downstream inherits.

### EXECUTION: bottom-up within L2 (bo_laksana FIRST), sequential / ≤2-3 parallel where file-disjoint,
RESUMABLE, findings written incrementally (an API-529 costs one asset). Source-verify classical facts.

### OUTPUT — write `L2_SOUNDNESS_REPORT.md`
Per-asset verdict + DATA + re-derivation + impact chain + family tag + PROPOSED-FIX for WRONG. A §BYPASS
section (per-writer; does L2 read corrected L1 or carry stale copies) + a §CONVERGENCE-ROOT section
(bo_laksana salience + eligibility, deep-characterized — WRONG vs DEFERRED for CGM/resonance). The tally +
the single most important finding. NO fix, NO build, NO seal. STOP for native+Cowork reconciliation → then
L2 fix → rebuild → seal → L3.

---
*End. L2 deep audit, GATED on L1-sealed-in-data. bo_laksana first (the convergence-salience root). Deep-
verify the 4 confirmed findings (salience collapse, CDLM vocab, CGM 0.506, resonance 0.28) + find the rest.
Lenses: faithfulness-to-corrected-L1, L0/L1-bypass, degenerate-distribution (high-yield), convergence-root
depth. Source-verified, resumable. → reconcile → fix → rebuild → seal. ASSESS ONLY.*

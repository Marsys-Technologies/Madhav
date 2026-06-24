---
artifact: CLAUDE_CODE_PROMPT_AUDIT_GAPFILL.md
canonical_id: CLAUDE_CODE_PROMPT_AUDIT_GAPFILL
version: 1.0
status: READY — Phase A2: complete the deep audit on the ~30+ PENDING assets (L1–L4) + the never-run L1/L2/L3 census. Resumable, layer-by-layer. ASSESS ONLY.
authored_by: Cowork 2026-06-23
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md (Phase A2)
map: FOUNDATION_ROOT_CAUSE_MAP.md (has the PENDING lists per layer)
---

# Phase A2 — Complete the Deep Audit (gap-fill)

> The v1 audit was uneven: L0 fully deep-audited, but L1 (~13 assets), L2 (7), L3 (~6), L4 (6) are PENDING,
> and the L1/L2/L3 cheap census never ran. This completes coverage to "no scope for assumption." REUSE the
> 16 confirmed-WRONG + the Gate-A verified-SOUND (don't re-audit them). Resumable, layer-by-layer.
> ASSESS ONLY — no fix, no build, no seal.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). COMPLETE the foundation deep audit
for chart `482012f1-710e-4a25-994a-93821f5871aa` — fill the coverage gaps the v1 audit left. **READ FIRST:**
`00_ARCHITECTURE/FOUNDATION_ROOT_CAUSE_MAP.md` (the existing findings + its per-layer PENDING DEEP AUDIT
lists) + `00_ARCHITECTURE/FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md` (scope) + `L0_L4_SOUNDNESS_AUDIT_SPEC_v1_0.md`
(the deep method). **ASSESS ONLY — apply no fix, change no data, run no build, seal nothing. Verify against
the live DB, not docs/code.**

**REUSE (do NOT re-audit — already deep-proven):** the 16 confirmed-WRONG root causes in the map; the
Gate-A verified-SOUND assets (ga_positions FORENSIC-7/7, ga_structural, and the full L0 set per
L0_SOUNDNESS_REPORT.md). Your job is ONLY the PENDING assets + the never-run census. L0 is DONE — skip it.
**L5 is OUT of scope — do NOT audit any mi_* asset.**

**EXECUTION (the prior run died 12/14 on a fan-out — don't repeat it):** work LAYER BY LAYER (L1→L2→L3→L4),
mostly SEQUENTIAL within a layer, parallel ONLY where assets are file-disjoint and independent (≤2-3 at
once). WRITE FINDINGS INCREMENTALLY into the layer's report after EACH asset — so an API-529 death costs one
asset and the run RESUMES (on restart, skip assets already written). On 529: back off + retry that asset,
don't abort. Produce one `L<n>_SOUNDNESS_REPORT.md` per layer.

**Per-asset DEEP method (SPEC §5):** distribution census (all rows, GROUP BY each meaningful column —
catches degenerate-uniform collapse + auto-detects categories) → stratified sample (~8-12: random +
extremes + one-per-category + anchor) → READ the writer (pipeline/orchestrator/writers/<asset>.py +
services/<asset>/) → INDEPENDENTLY RE-DERIVE what the rows SHOULD be from the asset's depends_on upstream
(compute from inputs, don't trust its output) → 3 lenses (data-engineering / astrological-coherence via
Claude-in-Code / faithfulness-to-upstream) → null-rate + FK-resolution-rate (whole column) → silent-default
code scan (.get(k,<const>) + bare except→default) → VERDICT SOUND/SUSPECT/WRONG; for ambiguous uniform/null,
re-derivation classifies WRONG (logic computes wrong) vs DEFERRED (deliberate unbuilt stub) vs SOUND.
For each WRONG: the VERIFIED downstream-impact chain (transitive closure via plan.ts transitiveDownstream,
but VERIFY each edge against what the writer actually READS — flag under-declared hidden deps).

### THE GAP-FILL TARGETS (the PENDING assets per the map — verify the exact lists against the map's
### "PENDING DEEP AUDIT" sections, which are authoritative if they differ from these):
**L1 Gaṇita (~13 pending — all ga_* EXCEPT the 3 done: ga_positions/ga_dashas/ga_structural):** ga_vargas,
ga_strength, ga_sensitive, ga_panchanga, ga_nakshatra, ga_condition, ga_yoga, ga_vastu, ga_medical,
ga_tajaka, ga_sade_sati, ga_prashna, ga_transit_anchors. + run the L1 cheap census (never returned). Re-derive
each against chart_facts; FORENSIC-anchor cross-check where applicable.
**L2 Bodha (7 pending — the map names them; NOT the 3 confirmed-WRONG CGM/resonance/CDLM):** bo_laksana
(the L2 root + convergence-salience home — deep-confirm the bo_laksana _compute_salience finding),
bo_bimba, bo_karanajala, bo_samskara, bo_upaya, bo_samvada, bo_anveshana, bo_pramana_mapa,
bodha_msr_signals (the convergence-root — confirm eligibility/salience + fact_value_num at column level).
+ L2 cheap census. Faithfulness-to-L1 is the primary lens.
**L3 Kāla (~6 pending — NOT the convergence cluster already done):** ka_gochara, ka_graha_sancara,
ka_dasha_kala, ka_muhurta_seva, ka_kalasutra, ka_kala_darshana, ka_tulana. + L3 cheap census.
**L4 Phala (6 pending — NOT muhurta/mitigation already census-confirmed):** ph_nimitta (the spine),
ph_sodhana, ph_suddha_sodhana, ph_sankrama, ph_rectification, ph_pramana, ph_phaladesa. Faithfulness +
the L4/L5 no-scoring boundary. (Note: several are downstream of the broken convergence — assess their
LOGIC; their data is suspect-by-inheritance, which is fine to note.)

### AFTER ALL FOUR LAYERS — UPDATE THE MAP
Update FOUNDATION_ROOT_CAUSE_MAP.md: fold in every new finding (verdict + evidence + re-derivation +
impact chain + family tag F1–F8 + PROPOSED-FIX draft for WRONG ones). Re-evaluate the MASTER REBUILD
SCHEDULE against the new findings — state EXPLICITLY whether the wave plan changed. Flip the map status to
COMPLETE-COVERAGE only when every L0–L4 asset has a verdict (the 16 WRONG + Gate-A SOUND + all gap-fill).
Report: the new findings, whether the rebuild plan changed, the single most important new finding, the
full tally. NO fix, NO build, NO seal. STOP for native+Cowork review (Gate A2).

---
*End. Gap-fill the ~30+ PENDING assets (L1–L4) + the never-run L1/L2/L3 census with the full deep method,
resumable + layer-by-layer + low-concurrency (don't repeat the 12/14 fan-out death). Reuse the proven; L0
done; L5 out. → COMPLETE-COVERAGE map → Gate A2. ASSESS ONLY.*

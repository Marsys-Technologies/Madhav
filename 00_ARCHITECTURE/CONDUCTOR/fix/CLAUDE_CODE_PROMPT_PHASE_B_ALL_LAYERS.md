---
artifact: CLAUDE_CODE_PROMPT_PHASE_B_ALL_LAYERS.md
canonical_id: CLAUDE_CODE_PROMPT_PHASE_B_ALL_LAYERS
version: 1.0
status: READY — single-session Phase B, 6 sequenced phases (L0→L4 code fixes + final build). One human pause at the L2 convergence root. NO premature seal.
authored_by: Cowork 2026-06-23
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v1_0.md (Phase B — code-deliverable reframe §1.5)
map: FOUNDATION_ROOT_CAUSE_MAP.md (Gate-A-COMPLETE; 16 confirmed-WRONG root causes; §8/§13 wave schedule)
---

# Phase B — All Layers, One Session, Sequenced Phases

> Native: data is DISPOSABLE (regenerable via the Build tracker); the deliverable is CORRECT CODE. So
> Phase B is ONE session with 6 phases (one per layer, bottom-up) — fix the writers' LOGIC, prove each
> layer with a throwaway proof-build on correct upstream input, end with one full end-to-end build.
> AUTO-PROCEED between phases EXCEPT the L2 convergence root, which PAUSES for native confirmation.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Execute **Phase B of the Foundation
Integrity Campaign** in ONE session, as 6 sequenced phases. **READ FIRST:**
`00_ARCHITECTURE/FOUNDATION_ROOT_CAUSE_MAP.md` (the Gate-A map — the 16 confirmed-WRONG root causes + each
one's PROPOSED FIX) + `00_ARCHITECTURE/FOUNDATION_INTEGRITY_CAMPAIGN_v1_0.md` (doctrine + §1.5 reframe).

**GOVERNING REFRAME (native): the deliverable is CORRECT WRITER CODE, not preserved data.** Data is
disposable — regenerable via the Nirmāṇa Build tracker. So: fix each layer's WRITER LOGIC correctly
(per the map's proposed fixes), then do a SCOPED PROOF-BUILD of that layer as an INTEGRATION TEST (does the
code produce correct output when fed correct upstream input?) — the build's data is throwaway. Bottom-up,
because a writer's logic can't be validated on bad upstream (ph_pratikara is meaningless on all-Jupiter
input). End with ONE full end-to-end build = the seal-grade proof.

**RAILS (every phase):** Full latitude to fix RIGHT — fix the root cause per the map, no minimal-diff
compromise, fix the writer so ANY future build is correct (not just patch data). DATA-FIRST verification:
prove each fix on the live DB output, never "code looks right." Frozen orchestrator contract (writers:
@register, run/substeps, never commit/close ctx.db_conn, WriterResult(rows_inserted=), $1 count_sql,
delete-then-insert). Anti-drift. Gemini/DeepSeek + Claude-in-Code (dev-time, allowed). Canonical chart
482012f1 never auto-mutated (B.10). Run proof-builds via the ORCHESTRATOR (direct runners retired). If a
fix's correct value is genuinely AMBIGUOUS (e.g. two legitimate classical traditions), STOP and ask — do
not pick autonomously. Commit per phase; push at the end (auto-deploys).

────────────────────────────────────────────────────────
### PHASE 0 — L0 reference tables (auto-proceed)
Fix L0-W1 + L0-W2 per the map: (W1) reconcile Rahu/Ketu exaltation between reference_planets +
bg_dignity_reference to ONE canonical value + a guard so they can't diverge again (if two legitimate
traditions → STOP+ask which is canonical); (W2) Mercury atichara threshold → a reachable value (~2.0°/day).
Fix the SEED/source so a re-seed stays correct, not just the rows.
PROVE: the two tables now AGREE; the threshold is within Mercury's real speed range; FORENSIC 7/7 still
passes. → auto-proceed to Phase 1.

### PHASE 1 — L1 Gaṇita (auto-proceed; but FINISH the L1 audit first)
The map left the full L1 deep audit PENDING (only ga_positions[SOUND]/ga_dashas[WRONG]/ga_structural[SOUND]
were deep-done). FIRST: finish the L1 deep audit on the remaining ga_* writers (census + re-derive); if it
surfaces new WRONG findings, fix them too (note them in the map). Then fix the known L1-W1: ga_dashas
ayanamsha vocabulary (lahiri→lahiri_chitrapaksha, kp→krishnamurti, surya_siddhanta→surya_siddhanta_classical)
— fix the WRITER so it emits canonical labels, + migrate existing labels. PROVE: ayanamsha-keyed joins now
hit all 5 ayanamshas; ga_positions still FORENSIC 7/7. Proof-build L1 for the native. → auto-proceed to Phase 2.

### PHASE 2 — L2 Bodha — THE CONVERGENCE ROOT — **PAUSE FOR NATIVE AFTER THIS PHASE**
Fix, per the map (verify each writer's code as you go — these diagnoses shifted before, so re-confirm the
fix against the actual writer before applying):
- **bo_laksana `_compute_salience()`** (the REAL convergence root — NOT a missing eligibility_score; that
  column doesn't exist): extract graha from `fact_key` (split on `:`) when JSONB tags lack it, normalize
  casing; add signature_class computation. This is the fix that un-collapses salience → fixes the
  downstream ranking that ka_sangam/ka_yojaka inherit.
- **bo_sangati** CDLM vocabulary (spirituality→spiritual, character→psychological, wealth→financial) in the
  writer's KNOWN_DOMAINS + a data migration. (Prompt already exists: CLAUDE_CODE_PROMPT_L2_CDLM_VOCAB_FIX.md
  — fold it in.)
- **bo_cgm** strength formula + edge-building (the all-0.506 / NULL-edges F1) — re-derive: is it
  compute-WRONG or a not-yet-built DEFERRED stub? Fix only if WRONG; if DEFERRED, report it as such, don't
  fabricate.
- **bodha_rm_resonances** scoring formula (all-0.28 F1) — same WRONG-vs-DEFERRED determination.
PROVE on data: salience now VARIES across signals (not near-uniform midpoints); CDLM domains are canonical;
CGM/resonance differentiate planets (or are honestly classified DEFERRED). Proof-build L2 for the native.
**THEN STOP. REPORT the L2 data-proof and WAIT for native+Cowork GO before Phase 3** — everything above L2
inherits this; it's been mis-diagnosed twice; this is the one mandatory human gate. Do NOT start Phase 3.

### PHASE 3 — L3 Kāla (resume after L2 go; auto-proceed through L4)
Fix per the map: **ka_sangam** (the per-signature transit fix is authored/in-flight — confirm it's correct
on the now-FIXED L2 salience input; the 3 bugs: Jupiter JSONB key already addressed, plus confirm the
ranking now works given fixed upstream salience, plus fact_value_num routing); **ka_yojaka** ranking
population; **kala_jivana_parva** epoch anchor 1950→1984-02-05 + score population; **ka_vighnakara** (the
silent 0-rows — fix so kala_obstruction populates). PROVE: convergence planet distribution is genuinely
correct per-signature (re-run the Moon-verification checks — diverse, eligibility-ranked not storage-order,
YOGA class present); kala_obstruction non-empty; jivana_parva chapters dated from 1984 with non-null scores.
Proof-build L3 for the native (this is the heavy one — the lifetime-tier convergence scan; allow time).

### PHASE 4 — L4 Phala (auto-proceed)
Fix per the map: **ph_muhurta** (parameterize the write loop — the all-identical travel/0.3 bug);
**ph_pratikara** severity/intensity mapping (+ confirm it now reads the FIXED ka_vighnakara obstructions,
multiple grahas not all-Jupiter). ph_sankrama self-corrects from the L2 CDLM fix — just rebuild it.
PROVE: muhurta rows DIFFER by undertaking/window; pratikara spans multiple afflicting grahas; sankrama is
no longer 96.5% career-skewed. Proof-build L4 for the native.

### PHASE 5 — FULL END-TO-END BUILD = the seal-grade proof (auto, then STOP)
Run ONE full Nirmāṇa Build of the native's chart end-to-end (all layers, via the orchestrator). This is the
integration test of all 16 fixes at once. VERIFY at seal-grade (the §7.9 live-deployment discipline):
- All assets lit with rows on the LIVE cockpit revision == the merge SHA; zero errors/missing tables.
- NO degenerate distributions on the key columns (run the distribution census across the rebuilt data —
  salience varies, convergence planets diverse, CGM/resonance differentiate, muhurta varies, etc.).
- FORENSIC 7/7 at L1; canonical chart unmutated.
- The watch-list from this whole campaign: convergence eligibility-ranked + YOGA present; CDLM canonical
  vocab; jivana epoch 1984; ph_pratikara multi-graha.
**Do NOT issue the L4 seal autonomously** — report the full-build verification evidence and STOP for
native+Cowork to review and declare the foundation sound + authorize the seal.

────────────────────────────────────────────────────────
### REPORT (final)
Per phase: the writer fixes applied (with the data-proof for each), any WRONG-vs-DEFERRED classifications,
any ambiguous-value STOPs, the proof-build result. The L2 pause-report (separately, mid-session). The final
full-build seal-grade verification. The deployed revision. Any new findings the L1 audit surfaced. NO seal
issued. STOP for native review.

**REMINDER OF THE TWO MANDATORY STOPS:** (1) after Phase 2 (L2 convergence root) — wait for go; (2) after
Phase 5 (full build) — wait for the native to authorize the seal. Everything else auto-proceeds.

---
*End. One session, 6 phases bottom-up (L0→L4 code fixes + final build). Fix WRITER LOGIC right per the map,
prove each layer with a throwaway proof-build on correct upstream input, one full end-to-end build as the
seal proof. Two human stops: the L2 convergence root, and the final seal. Data is disposable; correct code
is the deliverable.*

# Abhinandan Deep Data-Correctness Audit — Did the Remediation Take? — Claude Code Brief

> Paste this whole file into Claude Code. This is the PROOF session: verify, against the REGENERATED data for Abhinandan `1c826d5a`, that the BUILD-PATH-REMEDIATION fixes (B1–B10) and enhancements (O1–O7) actually produced correct, stratified, domain-complete, contamination-free data. Read `CLAUDE.md` + `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` first.

---

## 0 — Mission & framing

The remediation (all 10 blockers + 7 enhancements) was fixed in code and Abhinandan `1c826d5a` was regenerated on it (CURRENT_STATE v6.06, main `5a212dae`). The prior regeneration run proved the **build mechanics** work (everything lit, L0/native untouched, tracker clean). It did **NOT** prove the fixes took in the DATA. **That is this session's job.**

This is **AUDIT / INVESTIGATE-ONLY by default** — read the regenerated data, judge it on three axes, produce a findings register. **Do NOT fix-and-rebuild in this session** unless explicitly instructed below for a trivial case; the output is a verdict + a prioritized remediation backlog for the native to approve. (If correctness-critical contamination is found, flag it loudly and STOP — do not silently proceed.)

**Scope:** read Abhinandan `1c826d5a`; you MAY read native `482012f1` and other charts read-only solely for contamination/cross-chart comparison. **Write nothing to any chart's data.** Read-only DB queries + code reading + (optionally) Chrome MCP to view the tracker.

**Ground truth = internal-consistency + FORENSIC only** (no external oracle, no JH parity). Re-derive from classical rules + FORENSIC 7/7 + cross-layer internal consistency.

---

## 1 — THE CORE TEST: did each remediation fix take? (falsifiable, per-fix)

For EACH item below, the audit must return **TOOK / DID-NOT-TAKE / PARTIAL**, with the specific query/evidence. These are the falsifiable success criteria — not a generic "is the data good."

### B1 — No native contamination (CRITICAL)
- `chart_facts` panchanga rows for `1c826d5a` must reflect Abhinandan's birth (02-Mar-1985 · 09:40 · Bhubaneswar), NOT Abhisek's (1984-02-05). Verify tithi/vara/yoga/karana/nakshatra are computed for HIS date — cross-check the panchanga values against an independent re-derivation for 02-Mar-1985 09:40 Bhubaneswar; they must NOT equal Abhisek's FORENSIC set (Shukla Tritiya · Ravivara · Shiva · Garaja · Purva Bhadrapada).
- Spot-check positions (Sun/Moon/Lagna) are Abhinandan's, not the native's.
- VERDICT: contamination CLEARED or STILL PRESENT.

### B2 — Salience stratification (the highest-leverage fix)
- Pre-fix bug: all 58,674 signals had `computed_salience ≈ 0.5058` → all `tier="background"` (the `_signature_tier` top threshold is `computed_salience >= 3.0`, so a pinned ~0.5 produced 100% background).
- **Proof it took:** query the salience distribution of `bodha_msr_signals` for `1c826d5a` — salience must now span a real RANGE that crosses the tier thresholds, populating MULTIPLE tiers (not ~100% background). Report the tier histogram (count per tier) + min/median/max salience. PARTIAL if salience varies but still never crosses into higher tiers.

### B3 / O1 — Contradiction detection
- Pre-fix: `bodha_contradictions = 0` permanently (graha field NULL).
- **Proof:** `bodha_contradictions` for `1c826d5a` now has rows (expected ~25–100). Spot-check 2–3 are genuine (same graha carries both a yoga and a dosha). Report count + sample validity. DID-NOT-TAKE if still 0.

### B4 / O2 — Domain propagation (4 previously-empty domains)
- Pre-fix: `phala_anchors` had transition=377/health=20/career=3 and **0** for financial/psychological/relationship/spiritual.
- **Proof:** `kala_convergence.domain` is populated (not all NULL); `ka_bhavishya_lekha` rows carry real domains (not ~80% `general`); `phala_anchors` now has NON-ZERO anchors across the 4 previously-empty domains; `phala_phaladesa` has content for them. Report the per-domain anchor histogram before/after intent. PARTIAL if some but not all 4 domains populate.

### B5 — Discovery-anchor timing/domain
- **Proof:** discovery-sourced `phala_anchors` now have non-NULL `window_start`/`window_end` + real (non-default-`transition`) domains; they produce predictions in `mi_bhavisya` and spillover in `ph_sankrama` (were 0). Report.

### B6 — ka_sangam ayanamsha / C7 enrichment
- **Proof:** C7 classical-text enrichment now returns rows for convergence windows (was 0 from the `lahiri` vs `lahiri_chitrapaksha` mismatch). Report enrichment coverage.

### B7 — mi_adhilepa signal-adjustment
- **Proof:** `mimamsa_signal_adjustment` can now produce rows (family-key match, not UUID). Note: may still be 0 if calibration has no confirmed outcomes yet (first-build) — distinguish "0 because structurally fixed but no calibration data" (OK) from "0 because still broken" (check the join fires on representative data).

### B8 — bo_anveshana broker detection
- **Proof:** `bodha_cgm_edges` now carry `is_cross_subsystem`/`subsystem_from`/`subsystem_to`; broker detection yields candidates (was non-functional). Report.

### B9 — ph_muhurta transit scoring
- **Proof:** `phala_muhurta.transit_score` now VARIES (not hardcoded 0.5) — real ka_gochara-driven values. Report the distribution.

### B10 / O5 — 4 new bodha writers
- **Proof:** `bodha_chart_gestalt` (1 row), `bodha_cdlm_chart_summary` (1 row), `bodha_cgm_motifs` (rows), `bodha_cgm_paths` (rows) all populated for `1c826d5a`, and the content is meaningful (not empty/placeholder). `ph_nimitta`'s CGM-path read now gets real data (was `{}`). Report row counts + content sanity.

### O3 — Navamsha D9 cross-check signals (~45)
- **Proof:** the D1-vs-D9 dignity cross-check signals exist in `bodha_msr_signals` and carry correct broken-promise / vargottama-resilience classifications. Spot-check against `chart_divisionals` D9 positions.

### O4 — Argala CGM edges (~135)
- **Proof:** argala edges exist in `bodha_cgm_edges` (5th edge type) with correct 2nd/4th/11th direction + virodha-argala cancellation. Spot-check.

### O6 — Pratyantar-dasha (current AD)
- **Proof:** `kala_jivana_parva` has ~9 level-3 Pratyantar rows for the current Antardasha only, no smallint overflow, level 1+2 preserved.

### O7 — Ashtakavarga bindhu convergence (Mode D)
- **Proof:** `kala_convergence` has `mode='D'` rows (AV-bindhu windows, SAV ≥ 28), ~50–150. Spot-check the bindhu threshold.

---

## 2 — THREE-AXIS DEEP AUDIT (beyond the per-fix checks), L1–L5

For each layer/asset, the original three-axis examination — but now on the REGENERATED data:

- **Axis A — Astrological correctness (internal-consistency + FORENSIC):** re-derive a sample of each asset's outputs from classical rules + FORENSIC anchors; verify cross-layer consistency (L2 `constituent_facts_array` → real L1 `chart_facts.fact_id`; L3 dashas consistent w/ L1; L4 cite real L3/L2; L5 cite real L4). Flag anything that can't be re-derived or contradicts an anchor.
- **Axis B — Code-logic correctness:** confirm writers implement the intended classical method (not placeholder); no fabricated default-constants; **no degenerate single-value distributions** where diversity is expected (the all-Jupiter / all-0.5058 class — explicitly run a distribution check on every scored/tiered/attributed column); idempotent; FROZEN-contract conformant.
- **Axis C — Data-engineering correctness:** row counts sane vs target_floor where set; no nulls where required; no duplicate/orphan rows; FK integrity (sample each cross-layer link, count orphans); no stale residue from prior builds (single build_id per asset for this chart).

---

## 3 — CONTAMINATION & HYGIENE SWEEP
- Wrong-chart/cross-chart: every L1–L5 table — rows for `1c826d5a` carry the correct chart_id AND contain Abhinandan's values, not another chart's (spot-check signature values).
- Native-leakage: confirm no `482012f1` data bled into `1c826d5a` (the B1 class — now should be impossible; verify empirically).
- Stale/orphan: rows from a previous build not cleared, orphans whose parent was deleted, multiple build_ids.
- **Separately note** (do not fix here): the native `482012f1` was previously seen with 5 distinct build_ids in chart_facts — flag for a native-chart hygiene session if still present.

---

## 4 — COMPLETENESS / DROP-OFF RE-CHECK (did the blockers actually unblock more meaningful data?)
The pre-remediation audit found legitimate distillation drops PLUS real blockers. Re-characterize the inter-layer transitions on the regenerated data and confirm the BLOCKERS are gone (more meaningful data now flows): contradiction rows present, 4 domains populated, discovery anchors timed, broker edges flagged, the 4 bodha tables filled, Navamsha/argala/Mode-D/Pratyantar present. Distinguish "still a legit distillation drop" from "blocker resolved → richer data." Report the per-transition cardinality with the before(intent)/after(actual) comparison.

---

## 5 — DELIVERABLE: findings register (investigate-only)
A single structured report:
- **§1 Per-fix verdict table:** B1–B10 + O1–O7, each TOOK / PARTIAL / DID-NOT-TAKE, with the proving query/evidence and (for partial/failed) the root cause + file:line.
- **§2 Three-axis per-asset table:** PASS/FLAG + reason, L1–L5.
- **§3 Contamination verdict** per table (CLEAN/FOUND).
- **§4 Completeness/drop-off** re-check: blockers resolved? richer data?
- **§5 Executive summary:** did the remediation succeed? Which fixes took, which didn't, which partially. The top items needing a second remediation round, ranked. Anything flagged for native astrological review (acharya-grade calls you can't self-certify).
- **§6 Recommended prioritized action list** for the native to approve before any follow-up fix run.
- **NO code changes, NO rebuild, NO data writes** (unless a correctness-critical contamination demands an immediate STOP-and-flag). Save the report as `00_ARCHITECTURE/ABHINANDAN_POST_REGEN_DATA_AUDIT_v1_0.md`.

## 6 — GUARDRAILS
Investigate-only — no fix/rebuild/data-write. Internal-consistency + FORENSIC (no external oracle). Read other charts read-only for contamination only; never write any chart. Distinguish correct-by-design states (calibration n=0 zeros, confidence_inflation firewall, legitimate distillation drops, dormant-by-design L5 assets) from real defects — do NOT report design as bug. Honest uncertainty over false confidence — flag acharya-grade calls for native review. Every per-fix verdict must rest on a concrete query/evidence, not assertion. Governance: if you write the report file, append a SESSION_LOG entry — heading `## <SESSION_ID> — <date>, <status>` (id first, no "Session" word, no colon, no embedded `"` in YAML lists).

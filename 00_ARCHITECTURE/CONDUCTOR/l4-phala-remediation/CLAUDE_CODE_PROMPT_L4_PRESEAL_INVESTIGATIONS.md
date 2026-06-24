---
artifact: CLAUDE_CODE_PROMPT_L4_PRESEAL_INVESTIGATIONS.md
canonical_id: CLAUDE_CODE_PROMPT_L4_PRESEAL_INVESTIGATIONS
version: 1.0
status: READY — two pre-seal investigations: ph_pratikara bridge-verify + L2 CDLM domain-taxonomy reconciliation. NO SEAL.
authored_by: Cowork 2026-06-22
native_decisions: "(1) Verify the ph_pratikara all-Jupiter bridge before seal. (2) Re-examine L2 CDLM transition/spiritual coverage before sealing L4."
---

# Claude Code Prompt — Two Pre-Seal Investigations (NO SEAL)

> Paste §PROMPT to Claude Code in Antigravity. Both are DIAGNOSTIC-FIRST: find the truth, then fix only if
> there's a real defect. **DO NOT SEAL.** Report findings + recommended fix; the native decides.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav, main). L4 Phala is live in prod
with all 9 ph_* assets now populated (ph_pratikara 60 rows, ph_sankrama 1,073). Before the native seals
L4, run two diagnostic investigations. DIAGNOSE FIRST — only fix if there's a genuine defect. **DO NOT
seal** (no DRAFT→CURRENT, no L4_PHALA_CLOSE, no CURRENT_STATE flip). Report findings + a recommended fix
for each; the native decides.

**Rails:** Frozen contract; anti-drift; L-is-authority; N4; canonical chart 482012f1 never mutated;
Gemini/DeepSeek only; verify against live prod data, not the branch.

---

### INVESTIGATION 1 — ph_pratikara: is "all 60 obstructions = Jupiter" real or a bridge artifact?
The re-modeled ph_pratikara bridged EVERY one of the 60 `kala_obstruction` rows to
`afflicting_graha='jupiter'` via `kala_convergence.constituent_factors->>'planet'`, across 3 windows
(2027-01-09, 2029-03-14, 2029-08-09). 60-for-60 uniformity is suspicious (same silent-uniformity class as
the original bug). Determine which it is:
```
-- (a) Does the SOURCE actually vary? Inspect the obstructions' convergence planets directly:
SELECT o.id, o.convergence_id, o.obstruction_type, o.severity_score,
       c.constituent_factors->>'planet'  AS bridged_planet,
       c.constituent_factors             AS full_factors,
       c.window_start, c.window_end
FROM kala_obstruction o
LEFT JOIN kala_convergence c ON c.convergence_id = o.convergence_id
WHERE o.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
ORDER BY o.id;
```
Decide:
- If `constituent_factors->>'planet'` is genuinely 'jupiter' (or null→fallback) for all 60 SOURCE rows →
  the native's obstruction profile IS Jupiter-dominated (plausible — a single Jupiter dasha/transit window
  can dominate). ACCEPT; document the evidence. NO fix.
- If the source `constituent_factors` VARIES (different planets per convergence) but the bridge collapsed
  them to 'jupiter' → BRIDGE BUG. Likely causes: `->>'planet'` is the wrong JSONB key (inspect
  `full_factors` for the real per-obstruction graha key — it may be an array, or keyed `afflicting_graha`/
  `lord`/`graha`), or the join is fanning to one convergence row. FIX the extraction to the correct key,
  rebuild, re-verify the graha now varies. Add a test asserting graha diversity matches the source.
- If `convergence_id` is null for many obstructions (LEFT JOIN → null planet → fallback 'jupiter') → the
  fallback is masking missing data. Check `obstruction_detail` JSONB for a per-row graha before falling back.

### INVESTIGATION 2 — L2 CDLM domain-taxonomy reconciliation (the ph_sankrama 96.5% career skew)
**The skew is NOT a ph_sankrama bug and likely NOT a simple "CDLM is missing rows" gap — it's a DOMAIN-
TAXONOMY COLLISION. Evidence already found:**
- `bodha_cdlm_cells` has 0 rows for `domain_row='transition'` and `'spiritual'`.
- BUT `services/ph_nimitta/engine.py` line ~123 returns `'transition'` as the **neutral FALLBACK domain**
  (line 195: `domain = 'transition'` default), and maps SPIRITUAL/DHARMA/MOKSHA→`'spiritual'`,
  TRANSITION/RELOCATION/CHANGE→`'transition'`.
- The M9 multi-school close (`09_MULTI_SCHOOL_TRIANGULATION/M9_CLOSE_v1_0.md`) shows the instrument's
  canonical domains are **CAREER · HEALTH · RELATIONSHIP · SPIRITUAL · PSYCHOLOGICAL** — `SPIRITUAL` is a
  first-class domain WITH data (mean 3.728, HIGH), and there is NO `transition` domain in that taxonomy.

So three surfaces use different domain vocabularies. Reconcile them:
```
-- What domain_row/domain_col values does CDLM actually have, with counts?
SELECT domain_row, count(*) FROM bodha_cdlm_cells
  WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' GROUP BY domain_row ORDER BY 2 DESC;
-- What domains do phala_anchors actually carry?
SELECT domain, count(*) FROM phala_anchors
  WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' GROUP BY domain ORDER BY 2 DESC;
```
Determine the root cause and the right fix LOCATION (do NOT assume it's L4):
1. **Is `transition` a real domain or a catch-all?** If ph_nimitta dumps unclassified anchors into
   `transition` as a fallback, those anchors have no real domain → they SHOULD NOT expect CDLM cells. The
   fix is in ph_nimitta's domain classification (map them to their true domain, or exclude the fallback
   bucket from spillover), NOT in CDLM. The 96.5% career then reflects that career genuinely has the most
   classified anchors — possibly correct.
2. **Is `spiritual` a real gap?** SPIRITUAL has M9 convergence data + is a canonical domain, yet
   `bodha_cdlm_cells` has 0 spiritual rows. THIS looks like a genuine L2 CDLM build gap — the CDLM writer
   may not enumerate `spiritual` as a domain_row/col, or the spiritual signals didn't feed it. Find the
   CDLM writer (search `bodha_writers/` / wherever bodha_cdlm_cells is populated — it was NOT found under a
   `*cdlm*` filename, so locate the actual writer), read its domain enumeration, and determine whether
   spiritual was omitted. If so, that is an **L2 Bodha fix** (reopen the bodha_cdlm_cells build to include
   spiritual + any other canonical domain), then rebuild ph_sankrama for fuller coverage.
3. **Taxonomy alignment:** confirm phala_anchors' domain vocabulary == CDLM's domain vocabulary == the M9
   canonical 5. Any mismatch (e.g. 'transition' vs 'PSYCHOLOGICAL', case differences, missing domains) is
   the real defect. Recommend the single source of truth for the domain list + where each surface should
   align to it.

**Output for Investigation 2:** a clear verdict — (a) is `transition`'s 0-CDLM correct-by-design (fallback
bucket)? (b) is `spiritual`'s 0-CDLM a genuine L2 build gap to fix? (c) the domain-taxonomy reconciliation
(who's authoritative, who's misaligned). Recommend the fix LAYER (L4 ph_nimitta classification vs L2 CDLM
reopen) — do NOT implement an L2 reopen without native sign-off (it reopens a sealed layer).

### REPORT — NO SEAL
Report per investigation: the query outputs, the verdict (real vs artifact / by-design vs gap), the
recommended fix + its layer, and whether it blocks the L4 seal. Do NOT seal, do NOT reopen L2 without
sign-off. Then STOP for the native's direction.

---
*End. Investigation 1: verify the ph_pratikara Jupiter bridge (real profile vs JSONB-key/join artifact).
Investigation 2: reconcile the L2 CDLM / ph_nimitta / M9 domain taxonomies — separate `transition`
(likely a fallback bucket, correct-by-design) from `spiritual` (likely a genuine L2 CDLM gap). Recommend
fix layer; NO L2 reopen without sign-off. NO SEAL.*

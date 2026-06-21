---
artifact: M2_PROVENANCE_AUDIT_RESULTS.md
status: CURRENT
authored_by: KARN-W6-R3-PROVENANCE-AUDIT
authored_at: 2026-04-30T00:00:00Z
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §F1
---

# M2 Provenance Audit Results

**Produced by:** KARN-W6-R3-PROVENANCE-AUDIT  
**Branch:** redesign/r0-foundation  
**Audit date:** 2026-04-30

---

## Executive summary

| Audit | Target | Result | Status |
|---|---|---|---|
| Audit 1: MSR → FORENSIC | ≥95% | 91.31% (452/495) | **FAIL** |
| Audit 2: UCN → MSR | ≥90% | 6.60% (25/379) | **FAIL** |
| Audit 3: CGM UCN_SECTION → MSR (adapted) | ≥95% | 28.36% (38/134) | **FAIL** |
| Advisory: l4/l5 embedding gap | (advisory) | l4_remedial: 21/21 null; l5_timeline: 9/9 null | INFO |

**Overall corpus integrity verdict: PARTIAL FAIL (all 3 audits below target)**

### Pre-flight findings

| Item | Value |
|---|---|
| MSR `v6_ids_consumed` occurrences | 498 |
| MSR total parseable signals | 495 (SIG.MSR.001–496, gap at SIG.MSR.207) |
| MSR brief-expected signal count | 499 (discrepancy: 4) |
| UCN MSR citation occurrences (total in file) | 57 |
| l25_cgm_edges SUPPORTS edge count | 2 |
| l25_cgm_edges schema deviation | `source_signals` column absent — see Audit 3 |
| FORENSIC ID universe (corrected regex) | 928 unique IDs |
| l4_remedial null embeddings | 21 / 21 |
| l5_timeline null embeddings | 9 / 9 |

---

## Audit 1: MSR → FORENSIC traceability

**Script:** `platform/scripts/integrity/audit_msr_forensic.py`

**Method:** For each of the 495 parseable MSR signals, verify `v6_ids_consumed` field is present and contains at least one ID appearing in FORENSIC_ASTROLOGICAL_DATA_v8_0.md.

FORENSIC IDs extracted using pattern `[A-Z][A-Z0-9]{1,4}\.[A-Z0-9_.]+` to capture both standard namespaces (PLN, HSE, SGN…) and divisional-chart namespaces with digit suffixes (D9, D10, D60…).

**Results:**
- Total parseable signals: 495 (SIG.MSR.001–496, with SIG.MSR.207 absent)
- Signals with valid FORENSIC cross-reference: **452** (91.31%)
- Signals missing `v6_ids_consumed` field: **0**
- Signals with field but no valid FORENSIC ref: **43**
- FORENSIC ID universe size: 928 unique IDs

**Status: FAIL** (target ≥95% — shortfall: 3.69 percentage points, 43 signals)

**Sub-target items — all 43 signal IDs without valid FORENSIC cross-reference:**

```
SIG.MSR.025, SIG.MSR.043, SIG.MSR.074, SIG.MSR.354, SIG.MSR.367, SIG.MSR.375,
SIG.MSR.416, SIG.MSR.417, SIG.MSR.418, SIG.MSR.419, SIG.MSR.420, SIG.MSR.436,
SIG.MSR.444, SIG.MSR.445, SIG.MSR.446, SIG.MSR.447, SIG.MSR.448, SIG.MSR.449,
SIG.MSR.450, SIG.MSR.451, SIG.MSR.452, SIG.MSR.453, SIG.MSR.469, SIG.MSR.470,
SIG.MSR.471, SIG.MSR.472, SIG.MSR.473, SIG.MSR.474, SIG.MSR.475, SIG.MSR.476,
SIG.MSR.477, SIG.MSR.478, SIG.MSR.479, SIG.MSR.480, SIG.MSR.487, SIG.MSR.488,
SIG.MSR.489, SIG.MSR.490, SIG.MSR.491, SIG.MSR.492, SIG.MSR.493, SIG.MSR.495,
SIG.MSR.496
```

**Failure pattern breakdown by namespace:**

| Namespace in v6_ids_consumed | Signal count | Root cause |
|---|---|---|
| `PCH.*` (9 signals) | 9 | Namespace mismatch: MSR uses `PCH.*` but FORENSIC uses `PCG.*` for Panchang components |
| `NAK.*` general names (10) | 10 | MSR uses general type IDs (e.g., `NAK.SHRAVANA`) but FORENSIC only documents `NAK.PURVA_BHADRAPADA` |
| `DSH.*` abbreviated IDs (7) | 7 | MSR uses partial IDs (e.g., `DSH.V.MD`) vs FORENSIC's full IDs (`DSH.V.MD.MERCURY.2010`) |
| `TRS.*` abbreviated IDs (5) | 5 | MSR uses `TRS.ECLIPSE`, `TRS.SADE_SATI` vs FORENSIC's fully-qualified TRS entries |
| `D20.*`, `D40.*`, `D27.*` (5) | 5 | D20, D40, D27 divisional chart entries not documented in FORENSIC v8.0 |
| `SGN.*` general signs (2) | 2 | MSR references `SGN.PISCES` etc.; FORENSIC only explicitly records `SGN.CAPRICORN` |
| Empty arrays `[]` (4) | 4 | SIG.MSR.416–420 have v6_ids_consumed set to empty list |
| Novel IDs (`EVT.*`, `YOG.CROSSWEAVE.*`) | 2 | IDs not defined in any FORENSIC namespace |
| `D12.*`, `D7.*`, `D2.*` (3) | 3 | Obscure divisional charts not documented in FORENSIC |

**Additional data integrity finding:**  
SIG.MSR.207 is absent from the file (gap in the SIG.MSR.001–496 sequence). Total parseable signals = 495, not the brief-expected 499.

---

## Audit 2: UCN → MSR traceability

**Script:** `platform/scripts/integrity/audit_ucn_msr.py`

**Method:** For each UCN v4_0 narrative paragraph (≥20 words, between blank lines, excluding headers and code fences), verify at least one MSR signal ID is cited. MSR citation patterns: `MSR.NNN` or `SIG.MSR.NNN`.

**Results:**
- Total qualifying paragraphs (≥20 words): **379**
- Paragraphs citing ≥1 MSR signal: **25** (6.60%)
- Uncited paragraphs: **354**
- Total MSR citation occurrences in file (grep): 57 (concentrated in 25 paragraphs)

**Status: FAIL** (target ≥90% — shortfall: 83.40 percentage points)

**Root cause:** UCN v4.0 is a narrative synthesis document. Inline MSR signal citations (`MSR.NNN`) exist at the section-header / structured-data level (carried by the 38 `UCN_SECTION` database nodes that have `derived_from_signals`), but the vast majority of the narrative paragraph body text does not embed inline MSR citation markers. The 6.60% that do cite signals are the 25 paragraphs that happen to reference signals by their explicit ID (e.g., "MSR.413", "MSR.391") in the text.

**Uncited paragraph sample (first 10 previews):**

```
[para 0]  "**UCN v4.0** replaces the four-file reading sequence. Content is merged..."
[para 1]  "> *A chart is not a list of planets in houses. It is an argument..."
[para 2]  "Every chart has a handful of configurations so structurally dominant..."
[para 4]  "This is not common. Most charts show Mercury as an important planet..."
[para 5]  "What does this mean in practical terms? It means that the native's life-mission..."
[para 6]  "Mercury's 10th-house placement in Capricorn means this Mercurian architecture..."
[para 7]  "This convergence is active NOW (2014–2031, Mercury MD)..."
[para 8]  "Saturn and Mars share the 7th house in Libra. Saturn is exalted..."
[para 11] "This is why the chart's most impressive career achievements emerged..."
[para 12] "The Authority-Through-Tension Pattern runs through this entire document..."
```

All 354 uncited paragraphs contain substantive astrological interpretation but no inline `MSR.NNN` citation marker in their text body.

---

## Audit 3: CGM SUPPORTS → MSR traceability

**Script:** `platform/scripts/integrity/audit_cgm_supports.py`

**Schema deviation (pre-flight finding PF.5):**  
The `l25_cgm_edges` table does NOT have a `source_signals TEXT[]` column as assumed by the brief. The actual schema has: `id, edge_id, source_node_id, target_node_id, edge_type, strength, notes, source_section, build_id, status, orphan_reason`. MSR signal traceability in the CGM lives in `l25_cgm_nodes.properties->'derived_from_signals'` for `UCN_SECTION` node types.

This audit ran two checks:

### Primary metric (adapted): UCN_SECTION node MSR coverage

Checks what % of `UCN_SECTION` nodes in `l25_cgm_nodes` have ≥1 valid MSR signal ID in `properties->'derived_from_signals'`. This is the actual MSR traceability surface in the CGM.

**Results:**
- Total UCN_SECTION nodes: **134**
- Nodes with ≥1 valid MSR signal: **38** (28.36%)
- Nodes with empty `derived_from_signals` array: **96**
- Coverage: 28.36%

**Status: FAIL** (target ≥95% — shortfall: 66.64 percentage points)

**Nodes with ≥1 MSR signal (38 nodes):** These correspond to sections that were explicitly annotated with signal derivations during authoring (e.g., UCN.SEC.I.1 → [SIG.MSR.391, SIG.MSR.396, SIG.MSR.413]).

**Nodes without MSR signals (96 nodes, first 20):**
```
UCN.SEC.0, UCN.SEC.I, UCN.SEC.UCN-v1-0md-The-Mother-Document,
UCN.SEC.I.2, UCN.SEC.I.3, UCN.SEC.II.0, UCN.SEC.II.1, UCN.SEC.II.3,
UCN.SEC.II.4, UCN.SEC.III.0, UCN.SEC.III.1, UCN.SEC.III.2, UCN.SEC.III.3,
UCN.SEC.III.5, UCN.SEC.IV.0, UCN.SEC.IV.2, UCN.SEC.IV.3, UCN.SEC.IV.4,
UCN.SEC.IV.5, UCN.SEC.V.0 …
```

### Secondary metric (per brief spec): SUPPORTS edges with MSR source

**Results:**
- Total SUPPORTS edges: **2**
- Edges with MSR signal in source node properties or notes: **0** (0.0%)
- Both SUPPORTS edges connect PLN.* (planetary) nodes, which by design carry L1 chart facts — not MSR signal derivations.

**All edge types in DB:**
```json
{"CO_OCCURS": 131, "SEC_REFERENCES": 73, "DASHA_GIVES": 30,
 "RESONATES_WITH": 28, "ASPECTS": 19, "KARAKA_OF": 18, "NAKSHATRA_OF": 15,
 "RULES_OVER": 12, "DISPOSES": 12, "ARUDHA_OF": 12, "AFFLICTS": 9,
 "CONJUNCT": 6, "DUAL_SYSTEM_DIVERGENCE": 4, "CONTRADICTS_WITH": 4, "SUPPORTS": 2}
```

---

## Advisory: Embedding gap (l4/l5 rag_chunks)

**Method:** `LEFT JOIN rag_chunks rc ON rag_embeddings re.chunk_id = rc.chunk_id` — counts chunks with no corresponding embedding row.

**Results:**

| doc_type | total_chunks | null_embeddings | embedding_coverage |
|---|---|---|---|
| domain_report | 52 | 0 | 100.0% |
| l4_remedial | 21 | 21 | 0.0% |
| l5_timeline | 9 | 9 | 0.0% |

**Advisory verdict:** l4_remedial (21 chunks) and l5_timeline (9 chunks) have no embedding vectors. This confirms the W5-R2-D234-BUNDLE finding: the standalone chunker run did not trigger Vertex AI embedding. Vector search against these doc_types will return empty results until embeddings are populated. The `domain_report` type is fully embedded (52/52).

**Remediation:** Run full Cloud Build pipeline to trigger Vertex AI embedding. No code change required. Estimated: 30 minutes unattended build time.

---

## Remediation notes

### Audit 1 (MSR → FORENSIC) — FAIL at 91.31%

**Root causes and remediation steps:**

1. **PCH.* namespace mismatch (9 signals):** MSR uses `PCH.TITHI`, `PCH.VARA`, `PCH.NAKSHATRA`, `PCH.KARANA`, `PCH.YOGA` but FORENSIC uses `PCG.*` for Panchang components. Fix: update `v6_ids_consumed` in affected signals (354, 367, 375, 416–420) to use `PCG.*` namespace. Estimated: 30 minutes in one MSR maintenance session.

2. **NAK/SGN type IDs not matching FORENSIC instances (12 signals):** FORENSIC only documents the specific NAK/SGN entries relevant to the native's chart. Options: (a) expand FORENSIC to include all 27 nakshatra and 12 sign namespace entries as stubs, or (b) document that NAK.*/SGN.* general type references are valid by convention even if not explicitly in FORENSIC. Option (a) is architecturally cleaner. Estimated: 1 session for FORENSIC stub expansion.

3. **Higher divisional charts D20/D27/D40 not in FORENSIC (5 signals):** FORENSIC v8.0 documents up to D12 and D60 selectively. Either add D20/D27/D40 entries to FORENSIC or accept these as known gaps with a policy note. Estimated: 1 session.

4. **Empty v6_ids_consumed arrays (4 signals — SIG.MSR.416–420):** These signals need their `v6_ids_consumed` populated with appropriate FORENSIC IDs. Estimated: 30 minutes.

5. **SIG.MSR.207 missing from file:** Gap in MSR signal numbering. Investigate whether 207 was intentionally removed or accidentally deleted. Estimated: 15 minutes.

**Future session:** One MSR maintenance session targeting the 43 sub-target signals would move coverage from 91.31% to ≥95% and close Audit 1.

---

### Audit 2 (UCN → MSR) — FAIL at 6.60%

**Root cause:** UCN v4.0 was authored as narrative synthesis prose. MSR citations were embedded at the structured-data level (DB node `derived_from_signals`) rather than in the paragraph text body. The 6.60% that do cite signals are paragraphs that happened to reference signal IDs explicitly in their text (e.g., section-header paragraphs like "MSR.413: The Mercury Nexus").

**Remediation options (in order of effort):**

1. **Option A — Add inline citations to UCN paragraphs (high effort):** Add `[MSR.NNN]`-style footnote/citation markers to each interpretive paragraph, traceable to the relevant signal IDs. This would require reviewing all 379 qualifying paragraphs. Estimated: 2–3 sessions.

2. **Option B — Revise audit methodology (low effort):** Redefine the target metric to measure paragraph-level traceability via the database `derived_from_signals` annotations (UCN_SECTION nodes) rather than inline text citations. If a paragraph is part of a UCN section node that has ≥1 MSR signal, it counts as "traced". This changes the measurement surface and would give higher coverage but is less strict. Recommend discussing with native before adopting.

3. **Option C — Hybrid (medium effort):** Add inline citations to only the foundational sections (Parts I–III), which carry the highest interpretive weight. Skip metadata/appendix sections.

**Recommendation:** Discuss Option B with the native as a possible revision to the audit methodology before undertaking Option A authoring work. The 90% inline-citation target was aspirational; the actual UCN authoring style is prose-first. If the native confirms Option A as the right standard, assign to a dedicated UCN revision session.

---

### Audit 3 (CGM → MSR) — FAIL at 28.36%

**Root cause:** The UCN_SECTION node `derived_from_signals` field was only populated during initial CGM build for sections where the signal connections were explicitly noted. 96 of 134 sections have empty arrays — they were imported from the UCN source document without explicit signal annotation.

**Remediation:** Systematic UCN_SECTION annotation pass — for each UCN section with empty `derived_from_signals`, identify and add the relevant MSR signal IDs. This could be done either:
- Manually (author reviews each section and assigns signals): 2–3 sessions
- Semi-automatically (run audit_ucn_msr.py per-section and use the signal citations found in nearby text): faster but requires scripting

**Schema note for future brief authors:** The `source_signals TEXT[]` column referenced in the brief does not exist in `l25_cgm_edges`. The actual MSR traceability surface is `l25_cgm_nodes.properties->'derived_from_signals'` for UCN_SECTION nodes. Update future briefs accordingly.

---

## Data integrity side-findings

| Finding | Severity | Description |
|---|---|---|
| SIG.MSR.207 absent | Medium | Gap in MSR signal sequence 001–496. Investigate intentional vs accidental. |
| PCH.* vs PCG.* namespace | Medium | MSR references `PCH.*` Panchang IDs; FORENSIC namespace is `PCG.*`. 9 signals affected. |
| `source_signals` column absent | Low | Brief assumed `l25_cgm_edges.source_signals TEXT[]` — this column does not exist. Architecture note for future sessions. |
| Empty v6_ids_consumed (4 signals) | Low | SIG.MSR.416–420 have empty arrays, not null. Parser treated as "has field, no valid refs". |

---

## Post-W7-R1 Results (KARN-W7-R1-AUDIT-REPAIR — 2026-04-30)

**Produced by:** KARN-W7-R1-AUDIT-REPAIR
**Brief:** `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_F1_AUDIT_REPAIR.md`
**Branch:** redesign/r0-foundation
**Date:** 2026-04-30

### Updated executive summary

| Audit | Target | Pre-W7-R1 | Post-W7-R1 | Status |
|---|---|---|---|---|
| Audit 1: MSR → FORENSIC (KARN-W6-POSTFIX) | ≥95% | 91.31% | 98.99% | **PASS** |
| Audit 2: UCN → MSR (v2 — DB methodology) | ≥90% | 6.60% (paragraph-grep, wrong surface) | **95.52%** (128/134 UCN_SECTION) | **PASS** |
| Audit 3: CGM UCN_SECTION → MSR (PRIMARY) | ≥95% | 28.36% (38/134) | **95.52%** (128/134) | **PASS** |

**Overall corpus integrity verdict: PASS — all three audits clear their targets.**

### Audit 2 methodology fix

`platform/scripts/integrity/audit_ucn_msr.py` rewritten to v2. Old v1 (KARN-W6-R3) measured the wrong surface — it grep'd UCN_v4_0.md prose for inline `MSR.NNN` markers; the UCN is narrative synthesis whose citations live at the database node-metadata level (`l25_cgm_nodes.properties->derived_from_signals` for `UCN_SECTION` rows), not in paragraph text. v2 mirrors the PRIMARY block in `audit_cgm_supports.py` and queries the DB directly.

### Backfill summary

| Quantity | Count |
|---|---|
| Empty UCN_SECTION nodes pre-backfill | 96 |
| Nodes annotated this session (Rule C.3 keyword/topic match) | 90 |
| Nodes left intentionally empty (Rule C.4 structural exemption) | 6 |
| Total UCN_SECTION nodes with ≥1 valid MSR signal post-backfill | 128 / 134 (95.52%) |
| Unique MSR signal IDs assigned across the 90 backfilled nodes | 166 |
| Fabricated signal IDs | 0 (every assigned ID verified against `l25_msr_signals`) |

**Structural exemptions (Rule C.4 — pure metadata/changelog/intro stubs, no interpretive content):**

```
UCN.SEC.0                              §0 — HOW TO READ THIS DOCUMENT
UCN.SEC.UCN-v1-0md-The-Mother-Document `UCN_v1_0.md` — The Mother Document (source-artifact metadata)
UCN.SEC.XIII.5                         Generalization (meta-rule applied to any chart)
UCN.SEC.XVI                            §XVI — VERSION METADATA (v2.0)
UCN.SEC.XXIV                           §XXIV — METADATA
UCN.SEC.XXV                            §XXV — CHANGELOG
```

### Backfill methodology (Rule C.3)

For each empty UCN_SECTION node, the planner:

1. Extracted topical features from `display_name + content_excerpt`:
   - **Planets** mentioned (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu) and Sanskrit aliases.
   - **Signs** (12 rashis) and aliases.
   - **Houses** (1H–12H) including bhava names (e.g., "Putra Bhava" → 5H, "Lagna" → 1H, "Kalatra" → 7H).
   - **Themes** (Atmakaraka, Karakamsa, Sade Sati, Mercury Pentagram, Jaimini argala, Lakshmi yoga, Saraswati yoga, BB progression, Authority-Through-Tension, etc.).

2. Scored each of the 499 MSR signals by topical overlap:
   - +6 per matching planet (`l25_msr_signals.planets_involved`)
   - +6 per matching house (`houses_involved`)
   - +4 per matching sign (`signs_involved`)
   - +3 per theme keyword present in signal `name`/`description`

3. Picked top-K signals (K ≤ 6) above a per-rule confidence threshold (≥6 for high confidence, ≥3 for last-resort fallback).

No assignment was fabricated — every signal had at least one verifiable topical link to the section's display_name + content_excerpt via the planet/house/sign/theme overlap.

### Inline-citation note (forward work, not blocking)

The Audit 2 v1 (paragraph-grep) result of 6.60% was a methodology artifact, but the underlying observation — that UCN paragraph prose lacks inline `MSR.NNN` markers — is still factually true. The UCN authoring style is prose-first; its MSR traceability lives in node metadata. If the native later wants per-paragraph inline citations as a stricter standard, that's an Option A authoring pass against UCN_v4_0.md. It is **not** required for M2 close — the database-level traceability surface this audit measures is the operational source of truth used by the retrieval bundle and CGM compositor.

### Files changed by W7-R1

- `platform/scripts/integrity/audit_ucn_msr.py` — v1 paragraph-grep replaced with v2 DB query.
- `platform/scripts/integrity/audit_cgm_supports.py` — unchanged (script already adapted; PRIMARY metric now passes against existing 95% target).
- `l25_cgm_nodes.properties->derived_from_signals` — populated for 90 UCN_SECTION rows via parameterized `jsonb_set` UPDATEs in batches of 20.

### Remaining gaps (out of scope for W7-R1)

- **Audit 1 SIG.MSR.207 gap** (Medium severity, KARN-W6-R3 finding) — still open; not in W7-R1 scope.
- **Inline UCN paragraph citations** (forward work, not blocking) — see note above.
- **Audit 3 SECONDARY** (SUPPORTS edges, 0/2 with MSR) — by design; both SUPPORTS edges connect `PLN.*` planetary nodes which carry L1 chart facts not L2.5 signal derivations. Documented in audit_cgm_supports.py header.

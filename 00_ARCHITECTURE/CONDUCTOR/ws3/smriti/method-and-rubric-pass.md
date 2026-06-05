---
smriti_entry: method-and-rubric-pass
wave: ws3
session_id: method-and-rubric
status: PASS
commit: 8b115285
timestamp: "2026-06-05"
authored_by: WS-3 sub-agent (Racayitā)
---

# Smriti: method-and-rubric — PASS

The method-and-rubric session for WS-3 (Rule Base + Grounding) has completed successfully
and the methodology is confirmed ready for the bphs-pilot session.

## What was established

**Deliverable:** `00_ARCHITECTURE/WS3_EXTRACTION_METHOD_v1_0.md` (v1.0, CURRENT)
**Commit:** `8b115285` on `feature/ws3-rule-base`

The extraction method governs all rules to be extracted by WS-3 from the classical canon
(BPHS, Jaimini Sutras, KP Readers Vols 1–4, Tajaka Neelakanthi). Key decisions:

### Source texts
Four texts in priority order — all already ingested into the M8 corpus:
- BPHS (text_key: `bphs`, R. Santhanam translation) — Tier 1, primary pilot + full
- JAIMINI (text_key: `jaimini_sutra`, Iranganti Rangacharya) — Tier 2, full canon
- KP (text_key: `kp_texts`, K.S. Krishnamurti original) — Tier 3, full canon
- TAJAKA (text_key: `tajaka`, matched to corpus ingestion) — Tier 3, full canon

### Verse-ID convention
Format: `{TEXT_ABBREV}.{CHAPTER}.{VERSE}.{SEQUENCE}` (e.g., `BPHS.16.4.01`)
SEQUENCE = `01` by default; `02`, `03`... when a single verse yields multiple rules.
KP chapters use section-heading (not page number) as verse anchor.
Jaimini implicit-sutra textual_strength = 0.85 (amended by Cowork reviewer: sutra commentary
is canonical tradition, not mere opinion, but not unambiguous text).

### Rule schema (8 mandatory fields)
`rule_id`, `source_verse` (canonical_id + verse_ref + text_excerpt max 500 chars),
`condition`, `assertion`, `scope`, `school`, `confidence`, `caveats`

### Scope vocabulary (12 values, amended from original 8)
graha, bhava, yoga, compound_yoga, dasha, divisional, ashtakavarga, shadbala,
nakshatra, transit, transit_yoga, varshaphal, muhurta, remedy, misc

### Confidence rubric
`confidence = (textual_strength × 0.6) + (cross_text × 0.4)`
- Minimum to include (not STUB): 0.25
- Textual strength: 1.0 = direct statement; 0.85 = Jaimini implicit sutra; 0.7 = clear implication; 0.4 = commentarial inference; 0.2 = one commentator's opinion
- Cross-text: 1.0 = identical in 3+ texts; 0.7 = 2 texts agree; 0.4 = 1 additional partial agreement; 0.0 = unique to one text

### Quality bar
- Pramāṇa gate: ≥ 85% of pilot rules pass verse-trace on first extraction attempt
- Review Swarm: ≥ 80% of pilot rules receive ≥ 3/5 reviewer approval
- STUB rate: ≤ 10% in pilot batch
- Confidence distribution: ≥ 70% of pilot rules have confidence ≥ 0.5

### Cowork amendments incorporated (3 total)
1. **R1 — KP verse-ref:** Chapter + section heading, not page number (idiomatic for KP Readers)
2. **R2 — Extended scope vocabulary:** 8 → 15 values to cover divisional charts, ashtakavarga, shadbala, nakshatra, transit_yoga, varshaphal
3. **R3 — Jaimini implicit sutra strength:** Fixed at 0.85 (not 1.0, not 0.5 — canonical tradition with commentarial consensus but not direct explicit statement)

## Readiness confirmation for bphs-pilot

The bphs-pilot session may proceed. It should:
1. Read this smriti entry and `WS3_EXTRACTION_METHOD_v1_0.md` in full before extracting any rules
2. Target extraction from the `bphs` corpus in `08_CLASSICAL_CROSS_REFERENCE/corpus/`
3. Store rules in `08_CLASSICAL_CROSS_REFERENCE/brahmagyan_rules/bphs_pilot_rules.yaml`
4. Apply Pramāṇa gate per §5 of the method (condition + assertion derivable from text_excerpt alone)
5. Target quality bar: ≥ 85% Pramāṇa pass, ≥ 70% confidence ≥ 0.5, ≤ 10% STUB
6. Run Review Swarm (3 LLM reviewers minimum) on the pilot batch before declaring PASS

The methodology is locked. The bphs-pilot session must not modify the method unless it opens
a formal amendment process (new session, new commit, Cowork review).

---
*Smriti entry authored by WS-3 sub-agent at session close. method-and-rubric is the
dependency anchor for the entire WS-3 extraction chain.*

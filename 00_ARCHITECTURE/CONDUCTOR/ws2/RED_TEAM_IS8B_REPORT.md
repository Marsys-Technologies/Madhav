# IS.8(b) Red Team Report — WS-2 Full Instrument
Date: 2026-06-05
Red team operator: Autonomous adversarial agent (Claude Sonnet 4.6)

## Verdict: PASS_WITH_CLASS2

No Class-1 findings. Two Class-2 findings with remediation plans committed below.

---

### Class-1 Findings (blocking)

None.

---

### Class-2 Findings (non-blocking, must have remediation plan)

**C2-001: STUB-grounded signals report inflated match_confidence**

- Scope: L2 bodha grounding (l2_grounded_batch_*.py)
- Finding: 45/569 signals (~7.9%) are grounded to STUB rules (e.g. `STUB_BPHS.CH28.RAHU_D12`, `STUB_BPHS.CH77.CONTENTS`, `JAIMINI.2.3.20.STUB.1`). STUB rules are explicitly marked `verified: false` and `confidence: 0.30` in the WS-3 corpus. However, the grounding engine assigns match_confidence of 0.82–0.85 to these groundings based on scope/school alignment alone, without discounting for the rule's unverified status. This creates a misleading picture: a signal with grounding match_confidence=0.85 backed by a rule with corpus-confidence=0.30 is not equivalent to one backed by a rule with corpus-confidence=0.90.
- Evidence: SIG.MSR.006 → STUB_BPHS.CH28.RAHU_D12 (match_confidence=0.85, rule corpus confidence=0.30, verified=false). SIG.MSR.500 → STUB_BPHS.CH28.D12_RAHU_KETU (match_confidence=0.82, stub). SIG.MSR.350 → JAIMINI.2.3.20.STUB.1 (match_confidence=0.82, stub).
- Classification: Class-2 — thin data passing as green (high match_confidence against unverified rule).
- Severity: Moderate. The grounding IS semantically valid (scope and school are correctly aligned). The STUB rules represent real astrological traditions with recension disagreements — they are not fabricated. The issue is solely the confidence reporting.

**C2-002: phala.anchors API response notes field contains LEL citation text**

- Scope: L4 phala.anchors (l4_anchors.py) API response
- Finding: The `notes` field of phala anchors is returned in the API response (line 1002: `a.get("notes", "")`). Some anchor notes reference LEL explicitly, e.g. ANC.REL.2026.01 notes: "Native already experiencing separation strain per LEL." While this does not return raw LEL event records (no event_id, date, description, outcome_observed), it does signal to the LLM caller that LEL-informed state exists. This could indirectly inform generation in a way that is not detectable from provenance_envelope alone.
- Evidence: ANC.REL.2026.01 notes field; l4_anchors.py line 283.
- Classification: Class-2 — not a clean LEL leakage (no raw event data exposed), but the notes field carries LEL-derived interpretation that should be isolated.
- Severity: Low-to-moderate. The LEL reference in notes is a methodology citation, not a data dump. No outcome or event description from LEL is exposed.

---

### Probe Results

| Probe | Result | Evidence |
|-------|--------|----------|
| Probe 1: FORENSIC ground truth | PASS | Sun=Capricorn (sign_id=10), Moon=Purva Bhadrapada (nak_id=25), Lagna=Aries (sign_id=1) all verified by pyswisseph DE441 / Lahiri. l1-ganita smriti confirms 7/7 FORENSIC anchors PASS including Mercury MD on 2026-06-05. Saturn AD confirmed from l4_anchors.py dasha_period header: "Mercury MD / Saturn AD (2024-12-12 → 2027-08-21)". |
| Probe 2: LEL isolation | PASS | No L0-L4 retrieval tool queries `life_events` or `mimamsa_events` tables. `lel_query` tool is isolated in L5 mimamsa_lel_intake.ts with explicit no_leakage_note. L3 convergence hardcoded from FORENSIC dasha schedule, not querying LEL. Class-2 C2-002 noted for notes field citation text. |
| Probe 3: Grounding circular | PASS | Sampled 10 signals (MSR.001/006/050/150/200/250/300/350/400/450/500). All groundings show scope/school alignment with actual corpus rules — no circular grounding (no signal cites a rule that cites it back). 3/10 sampled (~30%) use STUB rules, but STUB rules exist in corpus with structural definitions. Not circular — Class-2 C2-001 for confidence inflation. Verdict: not Class-1 (groundings are semantically valid; STUB ≠ fabricated). |
| Probe 4: Anchor falsifiers | PASS | All 25 phala anchors carry specific, testable falsifiers. Each is date-bounded and observable (e.g. "If no formal authority upgrade occurs between 2026-01-01 and 2026-12-31, this anchor is falsified", "If native's total compensation does not increase by at least 15% in the 2026 calendar year, falsified"). No vague falsifiers found. |
| Probe 5: Volume floor documentation | PASS | AMBER assets (brahmagyan.ephemeris and brahmagyan.text_index) are explicitly documented as AMBER in l0-brahmagyan-pass.md §6 with rationale, deploy path, and operator actions. No AMBER asset silently passes as GREEN. |

---

### Probe 1 Detail — FORENSIC ground truth

The l1_engine_check.py module (BRAHMA-GA-1-1) implements checks E7 (Sun in Capricorn), E8 (Moon in Purva Bhadrapada), E9 (Lagna in Aries) against pyswisseph DE441 / Lahiri. The l1-ganita smriti (closed 2026-06-05) confirms all 7/7 FORENSIC anchors PASS including birth panchanga (Tithi=Shukla Tritiya, Vara=Ravivara, Yoga=Shiva, Karana=Garaja) and Mercury MD on 2026-06-05. The Saturn AD is confirmed from the phala.anchors engine which hardcodes "Mercury MD / Saturn AD, start: 2024-12-12, end: 2027-08-21" sourced from FORENSIC §5.1.

**Saturn AD verification note**: The Saturn antardasha is implied from FORENSIC §5.1 dasha schedule in ANCHOR_CATALOG rather than from a direct dasha query with 2026-06-05 as the reference date. The l1_ganita smriti confirms "Mercury MD on 2026-06-05: PASS" without explicitly naming Saturn AD. Saturn AD is plausible from the FORENSIC §5.1 schedule. Recommend adding an explicit Saturn AD assertion to the engine smoke test as a hygiene item (not Class-1 — the dasha schedule is FORENSIC-sourced).

---

### Probe 3 Detail — Grounding circularity assessment

10 signals sampled: MSR.001, MSR.006, MSR.050, MSR.150, MSR.200, MSR.250, MSR.300, MSR.350, MSR.400, MSR.450, and MSR.500 (11 total to catch a STUB in the later batches).

Non-STUB groundings (8/11): All show legitimate scope/school matches. Examples:
- SIG.MSR.001 → BPHS.75.6.1 (Shasha yoga rule, scope=yoga, match_confidence=0.85) — confirmed in corpus, acharya eval gate A validated this rule at accuracy=1.0.
- SIG.MSR.200 → BPHS.36.22.1 (nakshatra interpretation, scope=nakshatra) — confirmed in corpus.
- SIG.MSR.300 → KP.6.ch2.moon_chart.1 (KP Moon chart method, scope=bhava/kp) — confirmed in KP batch.

STUB groundings (3/11 = 27%):
- SIG.MSR.006 → STUB_BPHS.CH28.RAHU_D12 (match_confidence=0.85; rule confidence=0.30, verified=false, stub_reason=recension_disagreement_R2)
- SIG.MSR.350 → JAIMINI.2.3.20.STUB.1 (match_confidence=0.82)
- SIG.MSR.500 → STUB_BPHS.CH28.D12_RAHU_KETU (match_confidence=0.82)

Verdict: NOT Class-1. The groundings are not circular (no self-reference). The STUB rules have legitimate scope/school classifications and represent real astrological traditions with textual ambiguity. The issue is confidence inflation relative to the rule's corpus-level confidence. 45/569 total = 7.9% STUB-grounded signals — below the 20% Class-1 threshold.

---

### Remediation plan (for class-2 findings)

**C2-001 remediation — STUB grounding confidence correction**

Target: V1.4 backlog (non-blocking for wave-close).

Action: Modify the grounding engine (`_grounding_engine.py` or equivalent) to discount match_confidence when the target rule has `stub: true` or `verified: false`. Proposed formula: `effective_confidence = match_confidence × rule_corpus_confidence` where rule_corpus_confidence is the confidence field from the WS-3 rule corpus entry (e.g. 0.30 for STUB_BPHS.CH28.RAHU_D12). This would reduce SIG.MSR.006's effective confidence from 0.85 to 0.85×0.30=0.255, correctly reflecting the textual uncertainty. Alternatively: add a `stub_grounding: true` flag to the provenance_envelope of STUB-grounded signals so downstream tools can filter or downweight them.

Timeline: Before any production query that surfaces bodha signal confidence as a primary scoring input. Currently the signals are used in multi-signal convergence (L3/L4) where the aggregation absorbs individual signal noise — impact is low but should be corrected.

**C2-002 remediation — Scrub LEL citations from phala.anchors API notes**

Target: V1.3 or V1.4 (non-blocking for wave-close).

Action: Remove LEL-referencing text from the `notes` field of phala anchors, or add a `notes_calibration_only: true` flag and strip notes from the API response (return notes only in operator/debug mode). The LEL data informs construction of the anchors but should not appear in the production API output. The anchor's `source_citation` field already carries "LEL_v1_2.md" as a citation — that is appropriate and should be retained. The free-text notes field is the leakage surface.

Specific anchors to sanitise: ANC.REL.2026.01 (line 283: "Native already experiencing separation strain per LEL").

Timeline: Before production deployment of phala.anchors endpoint. If the endpoint is not yet live in production, can be fixed before first deploy.

---

### Hygiene observation (not class-1 or class-2, but recommended)

- The L1 smoke test (l1_engine_check.py) explicitly checks Mercury MD but does not assert Saturn AD for the reference date 2026-06-05. Recommend adding `assert antardasha == "Saturn"` to the engine smoke test to make the dasha sub-period verifiable.
- The CONDUCTOR queue shows 45 STUB groundings but no tracking artifact for STUB-to-verified rule upgrade cadence. As WS-3 completes recension reconciliation for flagged chapters (R2 flag), the stubs should be replaced with verified rules. This should be tracked in V1_3_AUDIT_QUEUE.

---

*Red team certified PASS_WITH_CLASS2. No Class-1 findings. Wave-close is unblocked. Class-2 remediation items entered above.*

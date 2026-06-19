---
artifact: PRASHNA_LAYER_CONTRIBUTION_DESIGN.md
document: Prashna (Vedic Horary Astrology) — Layer Contribution Design
status: DRAFT
version: 1.0
date: 2026-06-18
changelog:
  - v1.0 (2026-06-18): initial design across L2–L5; namespace isolation invariant documented; gates and dependencies clarified.
authored_by: Cowork (native-directed Prashna embed initiative)
intended_for: Claude Code sub-agents implementing Prashna writers for L2–L5 layers
prime_directive: Prashna charts are SEPARATE chart_ids cast for the QUESTION MOMENT, not the native's birth. Natal L2 Bodha assets NEVER read ga_prashna.* data. Each layer contributes a discrete synthesis artifact scoped to the prashna chart_id only.
depends_on: |
  L1 Gaṇita: ga_prashna_lagna, ga_prashna_judgment, ga_chart_service (prashna variants)
  L0 Brahmagyan: bg_prashna_rules, bg_prashna_fructification_rules
  L2 Bodha (natal): bo_laksana (WriterBase machinery reused for bo_prashna_bodha)
  L3 Kāla (timing): calendrical conversion rules
  L4 Phala (answer): judgment synthesis
  Classical sources: Tājika Nīlakaṇṭhī Ch. 5; Prashna Mārga Ch. 7; Tājika Paddhati
---

# Prashna (Vedic Horary Astrology) — Layer Contribution Design

## §0 — Mission

Extend the MARSYS-JIS instrument from natal chart analysis (native's birth, chart_id 482012f1) to **Prashna** — Vedic horary astrology cast for the **QUESTION MOMENT**. Each Prashna is a separate chart with its own chart_id. The instrument will:

1. **L2 Bodha:** synthesize Prashna judgment using Bodha machinery (separate from natal synthesis).
2. **L3 Kāla:** convert Prashna fructification timing into a calendar event window.
3. **L4 Phala:** deliver a standalone Prashna answer (YES/NO/UNCERTAIN) with timing and classical basis.
4. **L5 Mīmāṃsā (deferred):** outcome tracking (was the horary answer correct?).

This design ensures that natal Bodha synthesis is **never contaminated** by Prashna data, and Prashna answers are deterministic, calibrated, and auditable.

---

## §1 — NAMESPACE ISOLATION INVARIANT (CRITICAL)

The **eight natal L2 Bodha assets** are SEALED to the natal chart_id (482012f1). They MUST NEVER read `ga_prashna.*` data.

**Sealed natal assets:**
1. `bo_laksana` (physical attributes + constitution)
2. `bo_bimba` (body attributes + yogas)
3. `bo_karanajala` (karmic contradictions)
4. `bo_sangati` (convergence-density + cross-domain linkage)
5. `bo_samvada` (harmonic resonance)
6. `bo_samskara` (planetary-mind imprints)
7. `bo_upaya` (remedies)
8. `bo_pramana_mapa` (proof-mapping + auditable citations)

**Enforcement rule:** Any Prashna synthesis runs **scoped to a separate chart_id**. The natal writers do not branch on prashna-ness; they execute the same deterministic path for every chart, including prashna charts when they are processed as standalone chart_ids through the build orchestrator.

---

## §2 — L2 Bodha: `bo_prashna_bodha`

### §2.1 — Overview

A **separate Bodha synthesis** scoped to the prashna chart_id only. Reuses the same `WriterBase` machinery as natal Bodha synthesis but ingests Prashna-specific L1 facts (Prashna lagna, Prashna judgment, Prashna rules).

**Asset ID:** `bo_prashna_bodha` (not yet registered in `asset_registry`).

**Input facts (L1 Gaṇita):**
- `ga_prashna_lagna` — Prashna ascendant (house placidus, equal, whole-sign variants)
- `ga_prashna_judgment` — Prashna judgment per Tājika Ch. 5:
  - `qesyam_signification` (the thing asked about — Rahu for house, Sun for health, etc.)
  - `prashna_lagna_lord` (strength, aspects, yoga)
  - `qesyam_lord_strength` (combustion, retrograde, aspects)
  - `fructification_value` (longitudinal gap in degrees between qesyam and significator — feeds L3 timing)
  - `judgment_verdict` (favorable / unfavorable / mixed)
  - `classical_basis_string` (cite Tājika rule or Prashna Mārga chapter)

**Output table:** `bodha_prashna` (new table per migration).

**Schema (per ayanamsha_id):**
```sql
CREATE TABLE bodha_prashna (
  chart_id UUID,
  ayanamsha_id INT,
  
  -- Bodha synthesis summary
  synthesized_laksana JSONB,  -- lagna_lord strength, yogas, house_occupancies
  judgment_synthesis JSONB,   -- aggregated verdict + confidence
  classical_basis_array TEXT[], -- array of rule citations
  
  -- Deterministic computed fields
  qesyam_yoga_count INT,      -- count of yogas involving qesyam
  significator_strength_score NUMERIC, -- 0–100 (combustion? retrograde? aspected?)
  confidence_level TEXT,      -- HIGH / MEDIUM / LOW
  
  created_at TIMESTAMP,
  PRIMARY KEY (chart_id, ayanamsha_id)
);
```

**Classical source:** Tājika Nīlakaṇṭhī Ch. 5 (qesyam + prashna_lagna interaction), Prashna Mārga Ch. 7 (judgment formation).

### §2.2 — WriterBase conformance

- `@register('bo_prashna_bodha')`
- Implements `run(ctx) → WriterResult` (light writer) OR `plan_substeps(ctx)` + `run_substep(ctx, step)` (heavy).
- Reads `ga_prashna_lagna`, `ga_prashna_judgment`, `bg_prashna_rules` via `ctx.db_conn`.
- **Never commits or closes `ctx.db_conn`** — orchestrator owns the transaction.
- Deletes existing `bodha_prashna` rows scoped to `(chart_id × ayanamsha_id)` before insert (idempotency per §N.3).
- Returns `WriterResult` with `row_count` = rows inserted.

### §2.3 — Build gate

**Gate:** Build AFTER `bo_laksana` is scaffolded and WriterBase machinery is confirmed working.

**Rationale:** `bo_prashna_bodha` reuses the same laksana synthesis logic as `bo_laksana`, but on a separate chart_id. Once the machinery is tested on natal, Prashna becomes a straightforward scope-binding.

---

## §3 — L3 Kāla: `ka_prashna_timing`

### §3.1 — Overview

Converts the **Prashna fructification value** (longitudinal gap in degrees, from `ga_prashna_judgment.fructification_value`) into a **calendar event window**.

The fructification value represents the arc (in degrees) that the qesyam (or its significator) must travel before the event materializes. This is a deterministic temporal conversion based on sign characteristics.

**Asset ID:** `ka_prashna_timing` (not yet registered).

**Input:**
- `ga_prashna_judgment.fructification_value` (NUMERIC, 0–360 degrees)
- `ga_prashna_lagna` (to extract qesyam sign)
- `ga_prashna_judgment.judgment_date` (question moment; base for window calculation)
- `bg_prashna_fructification_rules` (sign-to-time mapping; L0 reference table)

**Output table:** `kala_prashna_timing` (new table per migration).

**Schema:**
```sql
CREATE TABLE kala_prashna_timing (
  chart_id UUID,
  ayanamsha_id INT,
  
  -- Input
  fructification_value_degrees NUMERIC,
  qesyam_sign_name TEXT,  -- Aries, Taurus, Gemini, ..., Pisces
  qesyam_sign_category TEXT, -- MOVABLE / FIXED / DUAL
  
  -- Conversion logic
  conversion_factor_per_degree NUMERIC, -- days, months, or flexible per sign
  conversion_basis_rule TEXT, -- e.g., "Tājika Ch. 5: movable sign rule"
  
  -- Output: calendar window
  earliest_date DATE,
  most_likely_date DATE,
  latest_date DATE,
  confidence_band_days INT,
  timing_basis JSONB, -- { rule_applied, degree_to_time_mapping, sign_category }
  
  created_at TIMESTAMP,
  PRIMARY KEY (chart_id, ayanamsha_id)
);
```

### §3.2 — Conversion rules (deterministic)

**Sign categories and conversion factors** (source: Tājika Nīlakaṇṭhī Ch. 5; Prashna Mārga Ch. 7):

| Sign Category | Signs | Conversion | Example |
|---|---|---|---|
| **Movable** | Aries, Cancer, Libra, Capricorn | 1 degree = 1 day | 30° gap → 30 days |
| **Fixed** | Taurus, Leo, Scorpio, Aquarius | 1 degree = 1 month | 10° gap → 10 months |
| **Dual** | Gemini, Virgo, Sagittarius, Pisces | 1 degree = 0.5 days (lighter weight) | 30° gap → 15 days |

**Timing window:** 
- `most_likely_date` = `judgment_date` + conversion(fructification_value, sign_category).
- `earliest_date` = `most_likely_date` − 10% buffer (accounting for retrograde acceleration).
- `latest_date` = `most_likely_date` + 10% buffer (accounting for combustion delays).

### §3.3 — Deterministic implementation

All calculations are **pure deterministic functions** (no LLM). The conversion table (`bg_prashna_fructification_rules`) lives in L0 and is immutable. A Python writer in `kala_writers/prashna_timing.py` computes the windows deterministically per chart.

### §3.4 — Build gate

**Gate:** Build WITH L3 layer (when L3 is activated). Depends on `bo_prashna_bodha` (L2) being available to check confidence levels, and on `ga_prashna_judgment` (L1) being populated.

---

## §4 — L4 Phala: `ph_prashna_answer`

### §4.1 — Overview

The **STANDALONE Prashna answer** delivered to the querent. No natal appendix. Synthesizes input from L1 (Prashna judgment), L3 (timing window), and L0 (Prashna rules) into a structured, auditable answer.

**Asset ID:** `ph_prashna_answer` (not yet registered).

**Output table:** `phala_prashna_answer` (new table per migration).

**Output JSON shape:**
```json
{
  "question": "Will I get the job?",
  "answer": "YES | NO | UNCERTAIN",
  "confidence": "0.85",
  "timing_window": {
    "earliest_date": "2026-07-15",
    "most_likely_date": "2026-08-15",
    "latest_date": "2026-09-15",
    "basis": "Tājika Ch. 5 (movable sign rule)"
  },
  "primary_yoga": "Qesyam-Lagna-Lord conjunction in 10th house (favorable)",
  "significators": {
    "qesyam": "10th house lord (strong, aspected favorably)",
    "prashna_lagna_lord": "Exalted in 5th (auspicious)"
  },
  "classical_basis": "Tājika Nīlakaṇṭhī Ch. 5 + Prashna Mārga Ch. 7, rule: qesyam dignified and lagna_lord strong → affirmative",
  "caveats": "[OPTIONAL LLM-GENERATED] Caveat text explaining uncertainties, extraneous factors, or rule-conflicts if confidence < 0.80"
}
```

### §4.2 — Schema

```sql
CREATE TABLE phala_prashna_answer (
  chart_id UUID,
  ayanamsha_id INT,
  
  -- Structured answer
  question_text TEXT,
  answer_verdict TEXT, -- YES / NO / UNCERTAIN
  confidence_numeric NUMERIC, -- 0.0 – 1.0
  
  -- Timing (from L3)
  earliest_date DATE,
  most_likely_date DATE,
  latest_date DATE,
  timing_basis_string TEXT,
  
  -- Classical signals
  primary_yoga_description TEXT,
  significators_jsonb JSONB, -- { qesyam, prashna_lagna_lord, ... }
  classical_basis_string TEXT, -- rule citation
  
  -- Caveat (LLM-optional, only if confidence < 0.80)
  caveat_text TEXT, -- NULL if high confidence; LLM-generated explanation if needed
  
  created_at TIMESTAMP,
  PRIMARY KEY (chart_id, ayanamsha_id)
);
```

### §4.3 — Deterministic + LLM boundary

**Deterministic (NO LLM):**
- `answer_verdict` (YES / NO / UNCERTAIN) — determined by qesyam strength + lagna_lord strength + fructification_value rules.
- `confidence_numeric` — computed score (0–1) based on rule-matching strength.
- `timing_window` — derived from L3.
- `primary_yoga` — classical yoga identification (deterministic rule matching).
- `significators` — direct extraction from `ga_prashna_judgment`.
- `classical_basis` — lookup of rule cite (Tājika Ch. 5, verse X).

**LLM-optional (ONLY if confidence < 0.80):**
- `caveat_text` — LLM may generate natural-language explanation of edge cases, conflicting rules, or extraneous factors. This field is **OPTIONAL** and is generated only if deterministic confidence is below a threshold and the querent consents to interpretation text.

### §4.4 — Source data

- `ga_prashna_judgment` (L1) — raw judgment facts.
- `ka_prashna_timing` (L3) — calendar window.
- `bg_prashna_rules` (L0) — deterministic rule specifications (qesyam_strength_thresholds, lagna_lord_strength_thresholds, yoga_list, etc.).

### §4.5 — Build gate

**Gate:** Build WITH L4 layer. Depends on `bo_prashna_bodha` (L2) and `ka_prashna_timing` (L3) being available.

---

## §5 — L5 Mīmāṃsā: Outcome tracking (DEFERRED)

### §5.1 — Overview

The **outcome-tracking layer** — comparing the Prashna answer (predicted at question-moment) against real-world outcomes (observed later). This enables the instrument to learn and calibrate its Prashna accuracy over time.

**Asset ID:** RESERVED but NOT YET REGISTERED. No code, tables, or migrations deployed for L5 Prashna in this phase.

**Deferred decision:** Defer L5 Prashna until a sufficient cohort of Prashna questions have been asked and outcomes known (12–24 months minimum). Once outcomes are available, L5 will:
- Track actual outcome date vs. predicted window.
- Compute verdict accuracy (YES predicted, YES observed → TP; etc.).
- Update rule confidence weights.

### §5.2 — Placeholder schema (future)

```sql
-- Future table (NOT created yet)
CREATE TABLE prashna_outcome_log (
  chart_id UUID,
  phala_answer_id UUID, -- FK to phala_prashna_answer
  question_moment TIMESTAMP,
  predicted_answer TEXT, -- YES / NO / UNCERTAIN
  predicted_date DATE,
  
  actual_outcome_date DATE,
  actual_outcome TEXT, -- YES / NO / OCCURRED_DIFFERENTLY / UNKNOWN
  querent_report TEXT, -- narrative from querent
  
  verdict_accuracy TEXT, -- TP / TN / FP / FN / INDETERMINATE
  timing_accuracy_days INT, -- abs(actual_outcome_date - predicted_date)
  
  confidence_retroactive NUMERIC, -- re-assessed confidence given outcome
  
  created_at TIMESTAMP,
  outcome_recorded_at TIMESTAMP,
  PRIMARY KEY (chart_id)
);
```

### §5.3 — Activation trigger

L5 Prashna activates when:
1. Minimum 20 Prashna questions have been asked and answered.
2. At least 12 have resolved outcomes reported.
3. Native explicitly approves L5 Prashna activation in a session handoff.

No hook, migration, or code is committed until then.

---

## §6 — Data flow summary

```
Prashna Question (Question Moment) → L1 Gaṇita (ga_prashna_lagna, ga_prashna_judgment)
                                          ↓
                                    L2 Bodha (bo_prashna_bodha)
                                          ↓
                                    L3 Kāla (ka_prashna_timing)
                                          ↓
                                    L4 Phala (ph_prashna_answer)
                                          ↓
                                   [L5 Mīmāṃsā — deferred]
                                          ↓
                                   Prashna Answer to Querent
```

---

## §7 — Implementation sequence

1. **Prerequisite:** L1 Gaṇita must have `ga_prashna_lagna`, `ga_prashna_judgment`, and `bg_prashna_rules` fully populated and tested.
2. **L2 Bodha:** Implement `bo_prashna_bodha` writer as a scope-bound variant of natal `bo_laksana` after natal Bodha is scaffolded.
3. **L3 Kāla:** Implement `ka_prashna_timing` writer (deterministic, pure function).
4. **L4 Phala:** Implement `ph_prashna_answer` writer (deterministic + optional caveat LLM).
5. **L5 Mīmāṃsā:** Reserve asset_id; defer code and tables until outcome cohort is mature.

---

## §8 — Key architecture decisions

1. **Separate chart_id per Prashna.** Each Prashna is cast as a distinct chart with its own chart_id, processed through the standard build orchestrator, scoped to that chart_id alone.

2. **Namespace isolation (CRITICAL).** Natal L2 Bodha assets never branch on prashna-ness or read prashna data. Prashna synthesis is entirely separate (bo_prashna_bodha) scoped to prashna chart_ids.

3. **Deterministic-first for L2–L4.** All L2–L4 outputs are computed deterministically. LLM is only used for the optional `caveat_text` field in L4 Phala, and only if confidence < 0.80.

4. **Reuse WriterBase machinery.** Prashna writers conform to the same frozen orchestrator contract as L2+ writers, with no contract extension needed.

5. **Tājika + Prashna Mārga as source.** All classical rules, thresholds, and yoga definitions are sourced from Tājika Nīlakaṇṭhī and Prashna Mārga, cited at the row level.

6. **Outcome tracking deferred.** L5 Prashna (outcome log + accuracy calibration) is reserved but not implemented until a sufficient question cohort has outcomes available.

---

## §9 — Conformance checklist (for implementer)

- [ ] `bo_prashna_bodha`: `@register('bo_prashna_bodha')`, WriterBase subclass, idempotency per §N.3, no db_conn commit.
- [ ] `ka_prashna_timing`: deterministic pure function (no LLM), sign-category rules hardcoded, unit-tested.
- [ ] `ph_prashna_answer`: verdict / confidence deterministic; caveat_text LLM-optional only if confidence < 0.80.
- [ ] All classical rules cited by Tājika / Prashna Mārga verse.
- [ ] Prashna chart_ids isolated from natal chart_id (482012f1) — no cross-read.
- [ ] Migration files created for `bodha_prashna`, `kala_prashna_timing`, `phala_prashna_answer` tables.
- [ ] `bodha_prashna` and `kala_prashna_timing` entries in `asset_registry` (gate: after L2 / L3 activation).
- [ ] `phala_prashna_answer` entry in `asset_registry` (gate: L4 activation).
- [ ] L5 asset_id reserved in registry; no table or writer code until activation.

---

## §10 — References

- Tājika Nīlakaṇṭhī (Ch. 5 & 7): qesyam + timing rules.
- Prashna Mārga (Ch. 7): judgment formation + fructification.
- Tājika Paddhati: auxiliary rule consolidation.
- L1 Gaṇita: `ga_prashna_lagna`, `ga_prashna_judgment`, `bg_prashna_rules`.
- L2 Bodha: `WriterBase` contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md).

---

*End of PRASHNA_LAYER_CONTRIBUTION_DESIGN.md v1.0 (2026-06-18 — initial design, gates and dependencies finalized, namespace invariant formalized).*

---
artifact: PHASE_M9_PLAN_v1_0.md
canonical_id: PHASE_M9_PLAN
version: 1.0
status: CURRENT
governing_macro_phase: M9 — Multi-School Triangulation
active_sub_phase: M9-A (INCOMING)
authored_at: 2026-05-14
authored_by: Cowork-M9-PLAN-AUTHORING
predecessor_closed: 08_CLASSICAL_CROSS_REFERENCE/M8_CLOSE_v1_0.md (M8 CLOSED 2026-05-14)
m9_entry_condition_met: true
entry_condition_basis: >
  M8 CLOSED 2026-05-14 (CURRENT_STATE_v1_0.md v5.11).
  MSR Nadi + BNN expansion COMPLETE (MSR_v4_0.md; 543 signals; SIG.MSR.515–543 per
  MSR_EXPANSION_PROPOSAL_v1_0.md). Both M9 entry conditions satisfied per MACRO_PLAN §M9.
  M7 is NOT a prerequisite for M9 (MACRO_PLAN §3.8.C confirmed).
m6_parallel_status: TIME-GATED PARALLEL (≥50 scored windows gate; target ~2026-11-15 minimum)
school_coverage_baseline:
  parashari: PRESENT (MSR v3.1 core; BPHS 1032 chunks; dominant attribution count)
  jaimini: PRESENT (Jaimini Sutra 181 chunks; Jaimini signals in MSR v3.1)
  kp: PRESENT (KP Vols 1-4 ingested; KP signals in MSR v3.1)
  nadi: PRESENT (MSR v4.0 SIG.MSR.515–541; Bhrigu Nandi Nadi + Chandra Kala Nadi ingested)
  bnn: PRESENT (MSR v4.0 SIG.MSR.515–538 dominant BNN signals ingested)
  tajika: GAP — Tajika content exists in Prashna Marga + Hora Sara chunks; dedicated
           extraction pass required. No dedicated Tajika signals in MSR v4.0.
  yogini: GAP — Yogini Dasha chapter present in BPHS 1032-chunk corpus; extraction pass
          required. No Yogini signals in MSR v4.0.
nap_pre_authorizations:
  - NAP.M9.0: Yogini signal extraction APPROVED (extract from existing BPHS classical_chunks;
              supplement with Tajika Neelakanthi ingestion if available at archive.org)
  - NAP.M9.1: Tajika signal extraction APPROVED (extract from Prashna Marga + Hora Sara chunks;
              Tajika school uses solar return chart frame — engine must handle Varsha Kundali
              separately from natal chart; this architectural asymmetry is accepted and documented)
  - NAP.M9.2: Convergence metric formula APPROVED (per-domain weighted agreement: convergence_level
              = HIGH if ≥5/7 schools affirm same direction; MEDIUM if 4/7; LOW if <4/7.
              Direction = positive if domain_score > 3.0 on 5.0 scale; negative if < 2.0; neutral otherwise)
  - NAP.M9.3: Disagreement threshold APPROVED (divergence flag when ≥2 schools contradict the
              plurality direction; all flagged disagreements entered into school_disagreements table)
  - NAP.M9.4: MSR v5.0 promotion APPROVED (Yogini + Tajika signals promoted without additional
              native review gate — extraction_confidence threshold ≥0.60 as established by M8-F)
  - NAP.M9.5: M9 macro-phase close APPROVED (no halt at M9-E; executor closes on IS.8(b) PASS)
session_count: 5
execution_mode: fully_autonomous_sequential (dangerously-skip-permissions)
llm_stack_constraint: Gemini → DeepSeek → NIM. No Anthropic/Claude API in any written code.
changelog:
  - v1.0 (2026-05-14, Cowork-M9-PLAN-AUTHORING): Initial plan. 5 sub-sessions (M9-A through M9-E).
    All NAP gates pre-resolved. Entry condition confirmed met (M8 CLOSED 2026-05-14).
    Yogini + Tajika gaps identified from MSR_EXPANSION_PROPOSAL_v1_0.md school coverage audit.
---

# PHASE_M9_PLAN — M9 Multi-School Triangulation

## §1 — M9 Scope (from MACRO_PLAN_v2_0.md §M9)

Seven Jyotish schools (Parashari, Jaimini, Tajika, KP, Nadi, BNN, Yogini) operating
simultaneously on a shared signal set. Convergence across schools is a precision signal —
when six of seven schools agree, that agreement is far more informative than any single
school's verdict. Divergence is equally valuable: it reveals where tradition-specific
assumptions produce different predictions, which is itself a calibration finding.

No human astrologer can hold all seven schools in working memory simultaneously across
543 signals. This is where the instrument does something structurally impossible for a
human practitioner.

**Exit criteria (verbatim from MACRO_PLAN §M9):**
a) All seven schools operating on shared signal set
b) Inter-school convergence metrics calibrated
c) School-disagreement resolution protocol populated with ≥N worked examples (N=10)
d) Convergence-as-precision-signal evidence logged

**Quality gate:** Convergence metrics stable across refit runs (deterministic output);
school-disagreement register entries have native-approved resolutions (pre-authorized
via NAP.M9.3).

---

## §2 — School Coverage Gap Plan (M9-A deliverable)

### Yogini School Gap

**Source:** BPHS classical_chunks already in DB (text_key='bphs'; 1032 chunks; 100% embedded).
BPHS contains dedicated Yogini Dasha chapters. M9-A runs a semantic extraction pass over
these existing chunks — no new procurement needed.

**Yogini system structure:**
8 Yoginis in a fixed 36-year repeating cycle:
| Yogini | Duration | Ruling Planet | Domain Character |
|---|---|---|---|
| Mangala | 1 year | Moon | Emotional volatility; new beginnings |
| Pingala | 2 years | Sun | Authority; health crises; visibility |
| Dhanya | 3 years | Jupiter | Wealth; progeny; dharmic activity |
| Bhramari | 4 years | Mars | Conflict; energy; property |
| Bhadrika | 5 years | Mercury | Learning; commerce; communication |
| Ulka | 6 years | Saturn | Hardship; discipline; karmic reckoning |
| Siddha | 7 years | Venus | Prosperity; relationships; arts |
| Sankata | 8 years | Rahu | Sudden reversals; hidden forces |

Extraction prompt for M9-A: identify Yogini-period → domain-outcome predictions from
BPHS chunks that mention any of the 8 Yogini names or "yogini dasha" or "yogini period."
Assign signal_id SIG.MSR.544 onward.

### Tajika School Gap

**Source:** Prashna Marga + Hora Sara classical_chunks already in DB (both ingested M8-C).
These texts contain Tajika (Varshapha/Persian) chapters. Additionally: attempt procurement
of Tajika Neelakanthi (Neelakantta; archive.org) — if available, ingest as tier-2 supplement.

**Tajika system structure:**
Tajika uses the Solar Return (Varsha Kundali — annual chart cast when Sun returns to natal
longitude). Key signals:
- Sahamas (Arabic Parts): specific to annual chart; 16 primary Sahamas (Punya, Vidya, etc.)
- Ithasala yoga: approaching conjunction (benefic timing indicator)
- Ishrafa: separating conjunction (opportunity passed)
- Muntha: annual chart sensitivity point (progresses 1 sign per year)
- Year lord (Varshesha): planet with most dignities in annual chart

**Architectural note (NAP.M9.1):** Tajika engine operates on Varsha Kundali, not natal
chart. The school engine for Tajika takes a different input than the other 6 engines.
Resolution: the multi-school runner produces Varsha Kundali for the current year
(2026 solar return for Abhisek: Sun returns to ~15° Capricorn ~Jan 25 2026) alongside
the natal chart, and passes the appropriate chart to each engine. The Tajika convergence
comparison is on domain-level scores (not signal-level), since Tajika signals are
temporally scoped (annual) while Parashari/Jaimini signals are natal.

---

## §3 — Architecture Additions

### 3.1 — GCS Layout Extension

New prefix added to `gs://madhav-marsys-sources/`:

```
gs://madhav-marsys-sources/
└── L9/
    ├── school_analyses/
    │   ├── parashari_analysis.json
    │   ├── jaimini_analysis.json
    │   ├── tajika_analysis.json
    │   ├── kp_analysis.json
    │   ├── nadi_analysis.json
    │   ├── bnn_analysis.json
    │   └── yogini_analysis.json
    └── convergence/
        ├── convergence_scores.json
        └── school_disagreement_register.json
```

MSR_v5_0.md added to existing L2_5/ prefix:
```
gs://madhav-marsys-sources/L2_5/MSR_v5_0.md   (overwrite in place; GCS versioning preserves v4_0)
```

### 3.2 — Database Migrations (057–060)

**Migration 057 — school_signal_coverage**
```sql
CREATE TABLE school_signal_coverage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id TEXT NOT NULL,
  school TEXT NOT NULL CHECK (
    school IN ('parashari','jaimini','tajika','kp','nadi','bnn','yogini')
  ),
  coverage_type TEXT NOT NULL CHECK (
    coverage_type IN ('primary','secondary','silent')
  ),
  -- primary   = signal belongs to this school's tradition
  -- secondary = school has partial/analogous coverage
  -- silent    = school does not address this signal
  confidence NUMERIC(4,3),
  attribution_chunk_id UUID REFERENCES classical_chunks(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (signal_id, school)
);
CREATE INDEX ssc_signal_idx ON school_signal_coverage(signal_id);
CREATE INDEX ssc_school_idx ON school_signal_coverage(school);
```

**Migration 058 — school_analysis_runs**
```sql
CREATE TABLE school_analysis_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_date DATE NOT NULL DEFAULT CURRENT_DATE,
  school TEXT NOT NULL,
  chart_id TEXT NOT NULL DEFAULT 'abhisek_primary',
  chart_type TEXT NOT NULL DEFAULT 'natal'
    CHECK (chart_type IN ('natal','varsha_kundali')),
  varsha_year INTEGER,                 -- NULL for natal; year for Tajika Varsha Kundali
  domain TEXT NOT NULL,
  domain_score NUMERIC(5,3),          -- 0.000–5.000 composite
  direction TEXT CHECK (direction IN ('positive','negative','neutral')),
  top_signals JSONB,                   -- [{signal_id, score, weight, attribution_ref}]
  school_verdict TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX sar_school_domain_idx ON school_analysis_runs(school, domain);
```

**Migration 059 — convergence_scores**
```sql
CREATE TABLE convergence_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  computed_at TIMESTAMPTZ DEFAULT NOW(),
  domain TEXT NOT NULL,
  schools_agreeing INTEGER NOT NULL,
  schools_total INTEGER NOT NULL DEFAULT 7,
  convergence_level TEXT GENERATED ALWAYS AS (
    CASE
      WHEN schools_agreeing >= 5 THEN 'HIGH'
      WHEN schools_agreeing >= 4 THEN 'MEDIUM'
      ELSE 'LOW'
    END
  ) STORED,
  mean_domain_score NUMERIC(5,3),
  std_domain_score NUMERIC(5,3),
  direction TEXT CHECK (direction IN ('positive','negative','neutral','mixed')),
  per_school_scores JSONB,             -- {"parashari": 3.2, "jaimini": 2.8, ...}
  convergence_narrative TEXT,
  UNIQUE (computed_at, domain)
);
```

**Migration 060 — school_disagreements**
```sql
CREATE TABLE school_disagreements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  disagreement_id TEXT NOT NULL UNIQUE,     -- e.g. 'DIS.SCH.001'
  domain TEXT NOT NULL,
  signal_id TEXT,
  schools_affirming TEXT[] NOT NULL,
  schools_denying TEXT[] NOT NULL,
  schools_silent TEXT[],
  disagreement_class TEXT NOT NULL CHECK (
    disagreement_class IN (
      'method_divergence',      -- schools use different methods to assess same domain
      'signal_gap',             -- some schools have no signal for this domain
      'tradition_specificity',  -- signal only exists in one tradition's framework
      'temporal_scope'          -- schools differ on WHEN, not WHETHER, an outcome manifests
    )
  ),
  resolution TEXT,
  resolution_verdict TEXT CHECK (
    resolution_verdict IN (
      'affirming_majority',     -- majority affirms; minority noted
      'denying_majority',       -- majority denies; minority noted
      'context_dependent',      -- both valid in different chart contexts
      'unresolved'              -- no resolution possible without more data
    )
  ),
  worked_example_narrative TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX sd_domain_idx ON school_disagreements(domain);
```

### 3.3 — New LLM Tools (27 + 28)

**Tool 27: `multi_school_signal_lookup`**
- Input: `{ topic: string, domains?: string[], schools?: string[] }`
- Queries school_signal_coverage JOIN classical_chunks for what all 7 schools say about a topic
- Returns: per-school verdict keyed by school name; coverage_type; confidence
- Used by: synthesis stage when query touches multi-school comparison

**Tool 28: `convergence_score_lookup`**
- Input: `{ domains: string[] }`
- Returns: convergence_scores rows for requested domains; per_school_scores; convergence_level
- Used by: synthesis stage to append convergence context to domain-level answers

### 3.4 — School Engine Architecture

```
platform/src/lib/schools/
├── types.ts                    ← SchoolAnalysis interface; SchoolResult type
├── school_runner.ts            ← orchestrates all 7 engines; produces MultiSchoolResult
├── parashari_engine.ts
├── jaimini_engine.ts
├── tajika_engine.ts            ← NOTE: uses Varsha Kundali; chart_type='varsha_kundali'
├── kp_engine.ts
├── nadi_engine.ts
├── bnn_engine.ts
└── yogini_engine.ts
```

**SchoolAnalysis interface:**
```typescript
interface SchoolAnalysis {
  school: SchoolName;
  chartType: 'natal' | 'varsha_kundali';
  analyze(chartData: ChartData, domain: Domain): Promise<SchoolResult>;
}

interface SchoolResult {
  school: SchoolName;
  domain: Domain;
  domainScore: number;              // 0.0–5.0
  direction: 'positive' | 'negative' | 'neutral';
  topSignals: SignalScore[];        // [{signal_id, score, weight, attribution_ref}]
  schoolVerdict: string;            // 1–3 sentence acharya-grade summary
  signalCoverage: CoverageType;     // 'primary' | 'secondary' | 'silent'
}
```

**Convergence calculator:**
```typescript
// platform/src/lib/schools/convergence_calculator.ts
function computeConvergence(results: SchoolResult[], domain: Domain): ConvergenceScore {
  const directions = results.map(r => r.direction);
  const pluralityDirection = mode(directions);
  const schoolsAgreeing = directions.filter(d => d === pluralityDirection).length;
  return {
    domain,
    schoolsAgreeing,
    schoolsTotal: 7,
    convergenceLevel: schoolsAgreeing >= 5 ? 'HIGH' : schoolsAgreeing >= 4 ? 'MEDIUM' : 'LOW',
    meanDomainScore: mean(results.map(r => r.domainScore)),
    stdDomainScore: stddev(results.map(r => r.domainScore)),
    direction: pluralityDirection,
    perSchoolScores: Object.fromEntries(results.map(r => [r.school, r.domainScore]))
  };
}
```

### 3.5 — Folder Structure (09_MULTI_SCHOOL_TRIANGULATION/)

```
09_MULTI_SCHOOL_TRIANGULATION/
├── README.md
├── SCHOOL_COVERAGE_AUDIT_v1_0.md      ← M9-A: per-school signal count + gap analysis
├── YOGINI_SIGNAL_EXTRACTION_v1_0.md   ← M9-A: Yogini signals extracted from BPHS
├── TAJIKA_SIGNAL_EXTRACTION_v1_0.md   ← M9-A: Tajika signals from Prashna Marga + Hora Sara
├── schools/
│   ├── parashari/PARASHARI_ENGINE_SPEC_v1_0.md
│   ├── jaimini/JAIMINI_ENGINE_SPEC_v1_0.md
│   ├── tajika/TAJIKA_ENGINE_SPEC_v1_0.md   ← includes Varsha Kundali architecture note
│   ├── kp/KP_ENGINE_SPEC_v1_0.md
│   ├── nadi/NADI_ENGINE_SPEC_v1_0.md
│   ├── bnn/BNN_ENGINE_SPEC_v1_0.md
│   └── yogini/YOGINI_ENGINE_SPEC_v1_0.md
├── convergence/
│   ├── CONVERGENCE_METRICS_v1_0.md        ← M9-D
│   └── convergence_scores.json            ← M9-D
├── disagreements/
│   ├── SCHOOL_DISAGREEMENT_REGISTER_v1_0.md   ← M9-E
│   └── school_disagreement_register.json       ← M9-E
├── analysis/
│   ├── MULTI_SCHOOL_ANALYSIS_v1_0.md      ← M9-C: per-school run on Abhisek's chart
│   └── CONVERGENCE_FINDINGS_v1_0.md       ← M9-D: convergence hotspots + precision signals
└── M9_CLOSE_v1_0.md                       ← M9-E
```

### 3.6 — New Pipeline Plan Type

Add `multi_school_triangulation` to QueryPlan plan_types. Trigger condition: query asks what
multiple schools say about a topic, or asks for "strongest signal" (convergence = strength).
Pipeline flow for this plan type:
  classify → compose_bundle → plan (multi_school_triangulation) →
  tool_fetch [multi_school_signal_lookup + convergence_score_lookup] →
  synthesis (with convergence block) → audit

---

## §4 — Sub-Phase Definitions

### M9-A — Coverage Audit + Signal Extraction + Infrastructure

**Scope:** Audit MSR v4.0 school coverage (tag every signal with school membership);
extract Yogini signals from existing BPHS chunks; extract Tajika signals from existing
Prashna Marga + Hora Sara chunks; attempt Tajika Neelakanthi procurement;
produce MSR_v5_0.md; scaffold 09_MULTI_SCHOOL_TRIANGULATION/; run DB migrations 057–060;
extend GCS_LAYOUT_v1_0.md with L9/; register tool stubs 27+28; update CAPABILITY_MANIFEST.

**Session:** M9-A-S1

**Coverage audit script:** `platform/scripts/m9/run_coverage_audit.py`
- For each of 543 signals: query classical_attributions to determine which schools have
  classical_attribution rows → classify as primary/secondary/silent per school
- INSERT into school_signal_coverage (bulk; ON CONFLICT DO UPDATE)
- Output: SCHOOL_COVERAGE_AUDIT_v1_0.md with table: signal counts per school × coverage type

**Yogini extraction script:** `platform/scripts/m9/extract_yogini_signals.py`
- Query: SELECT * FROM classical_chunks WHERE text_id = (bphs text_id)
  AND content ILIKE ANY(ARRAY['%yogini%','%mangala%','%pingala%','%dhanya%','%bhramari%',
  '%bhadrika%','%ulka%','%siddha%','%sankata%','%yogini dasha%'])
- LLM pass (Gemini Pro): extract signal_name, yogini_name, domain, trigger_condition,
  predicted_outcome, extraction_confidence
- Dedup against MSR_v4_0.md signals (cosine ≥ 0.85 = duplicate)
- Write YOGINI_SIGNAL_EXTRACTION_v1_0.md
- Assign IDs SIG.MSR.544 onward for promoted signals (confidence ≥ 0.60)

**Tajika extraction script:** `platform/scripts/m9/extract_tajika_signals.py`
- Query classical_chunks WHERE text_id IN (prashna_marga_id, hora_sara_id)
  AND content ILIKE ANY(ARRAY['%tajika%','%varsha%','%sahama%','%ithasala%',
  '%ishrafa%','%muntha%','%varshesha%','%nakta%'])
- If Tajika Neelakanthi available at archive.org: ingest via ingest_utils.py pattern;
  add to classical_texts tier=2, tradition='tajika'; include its chunks in extraction
- LLM pass (Gemini Pro): extract Tajika signals with solar-return scope flag
- Write TAJIKA_SIGNAL_EXTRACTION_v1_0.md
- Assign IDs after Yogini block (SIG.MSR.544+N onward)

**MSR_v5_0.md authoring:**
- Copy MSR_v4_0.md + append §VIII Yogini Signals + §IX Tajika Signals
- Version bump: 4.0 → 5.0; update signal_count
- Upload to gs://madhav-marsys-sources/L2_5/MSR_v5_0.md
- Update CAPABILITY_MANIFEST: MSR entry → v5_0

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M9A.1 | 09_MULTI_SCHOOL_TRIANGULATION/ scaffold created; all subdirs present |
| AC.M9A.2 | DB migrations 057/058/059/060 applied; tables verified |
| AC.M9A.3 | GCS_LAYOUT_v1_0.md updated with L9/ prefix block |
| AC.M9A.4 | school_signal_coverage populated: all 543 signals × 7 schools = 3,801 rows |
| AC.M9A.5 | SCHOOL_COVERAGE_AUDIT_v1_0.md present: per-school primary/secondary/silent counts |
| AC.M9A.6 | YOGINI_SIGNAL_EXTRACTION_v1_0.md present; ≥8 Yogini signals extracted |
| AC.M9A.7 | TAJIKA_SIGNAL_EXTRACTION_v1_0.md present; ≥10 Tajika signals extracted |
| AC.M9A.8 | MSR_v5_0.md present; §VIII Yogini + §IX Tajika sections; version=5.0 |
| AC.M9A.9 | MSR_v5_0.md uploaded to GCS L2_5/; CAPABILITY_MANIFEST + CANONICAL_ARTIFACTS updated |
| AC.M9A.10 | Tool 27 + 28 stubs created in platform/src/lib/tools/; registered in index.ts |
| AC.M9A.11 | CURRENT_STATE updated: M9 OPEN / M9-A-S1 CLOSED; red_team_counter +1 |
| AC.M9A.12 | SESSION_LOG M9-A-S1 appended; MP.1 + MP.2 + MP.4 mirrors propagated |
| AC.M9A.13 | CAPABILITY_MANIFEST updated: PHASE_M9_PLAN + 09_MULTI_SCHOOL_TRIANGULATION entries |

---

### M9-B — Seven School Engines Implementation

**Scope:** Build `platform/src/lib/schools/` module with all 7 school engines plus the
convergence calculator. Each engine implements SchoolAnalysis interface. Write per-school
specification documents in 09_MULTI_SCHOOL_TRIANGULATION/schools/. Write unit tests (≥6
per engine; ≥10 for convergence_calculator). All tests pass; tsc 0 errors.

**Session:** M9-B-S1

**Engine implementation notes per school:**

Parashari engine:
  - Signal filter: school_signal_coverage WHERE school='parashari' AND coverage_type='primary'
  - Weights from dbn_params_v1_0.json (existing M5 calibrated weights)
  - Domain score = weighted sum of signal scores; normalised to 0.0–5.0

Jaimini engine:
  - Signal filter: school_signal_coverage WHERE school='jaimini' AND coverage_type='primary'
  - Jaimini-specific: Chara Karaka hierarchy (AK, AmK, BK, MK, PK, GK, DK) modulates weights
  - Chara Dasha lord identified from FORENSIC data

KP engine:
  - Signal filter: school_signal_coverage WHERE school='kp' AND coverage_type='primary'
  - KP uses Sub-lord system; star-lord chain determines signal activation
  - Sub-lord data for natal chart from FORENSIC (already present in L1 facts)

Nadi engine:
  - Signal filter: school_signal_coverage WHERE school='nadi' AND coverage_type='primary'
  - Nadi triggers use "planet-from-planet" counting — engine applies Nadi house convention
  - SIG.MSR.515–541 (CKN signals) are primary Nadi signals

BNN engine:
  - Signal filter: school_signal_coverage WHERE school='bnn' AND coverage_type='primary'
  - BNN trigger: sequential transit analysis ("Jupiter contacts Rahu, then Saturn")
  - Current transit positions [EXTERNAL_COMPUTATION_REQUIRED: Swiss Ephemeris for 2026-05-14]
  - Until external computation provided: BNN engine uses placeholder transit data; marks
    output with [TRANSIT_DATA_PENDING] flag; this is not a blocking failure for M9-B

Yogini engine:
  - Signal filter: school_signal_coverage WHERE school='yogini' AND coverage_type='primary'
  - Current Yogini period for Abhisek: compute from birth date 1984-02-05 + 36-year cycle
  - Yogini at M9 execution date (2026-05-14): calculate which Yogini is active
  - Domain character of active Yogini modulates all domain scores

Tajika engine:
  - chart_type = 'varsha_kundali' (2026 solar return)
  - 2026 Varsha Kundali for Abhisek: Sun returns to natal longitude ~Jan 25 2026
  - [EXTERNAL_COMPUTATION_REQUIRED: Varsha Kundali chart for 2026-01-25, Bhubaneswar]
  - Until provided: Tajika engine uses natal chart as approximation with prominent disclaimer;
    domain scores marked [VARSHA_KUNDALI_PENDING]; Tajika excluded from convergence count
    where this pending flag is active (convergence_total drops to 6 for affected domains)

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M9B.1 | platform/src/lib/schools/types.ts: SchoolAnalysis + SchoolResult + SchoolName types |
| AC.M9B.2 | All 7 engine files present; each implements SchoolAnalysis interface |
| AC.M9B.3 | school_runner.ts: orchestrates all 7 engines; returns MultiSchoolResult |
| AC.M9B.4 | convergence_calculator.ts: computeConvergence() deterministic; re-run stable |
| AC.M9B.5 | ≥6 unit tests per engine (mock signal_coverage data); all passing |
| AC.M9B.6 | ≥10 unit tests for convergence_calculator; convergence_level correctness verified |
| AC.M9B.7 | Per-school SPEC docs present (7 files in schools/ subdirs) |
| AC.M9B.8 | tsc 0 errors on platform/src/lib/schools/ |
| AC.M9B.9 | SESSION_LOG M9-B-S1 appended; CAPABILITY_MANIFEST updated; CURRENT_STATE updated |

---

### M9-C — Run All 7 Schools on Abhisek's Chart

**Scope:** Execute all 7 school engines against Abhisek's chart across all 5 domains
(CAREER, HEALTH, RELATIONSHIP, SPIRITUAL, PSYCHOLOGICAL). Persist results to
school_analysis_runs table and GCS L9/school_analyses/. Produce
MULTI_SCHOOL_ANALYSIS_v1_0.md with per-school per-domain verdicts in readable form.
Identify initial convergence hotspots (domains where ≥5 schools agree).

**Session:** M9-C-S1

**Execution script:** `platform/scripts/m9/run_multi_school_analysis.py`
- Load chart data from FORENSIC_ASTROLOGICAL_DATA_v8_0.md (via bundle_hydrator or direct read)
- For each school × domain combination (7 × 5 = 35 combinations):
  a) Call school engine analyze() function
  b) INSERT into school_analysis_runs
  c) Log verdict summary
- After all 35 runs: serialize per-school results to JSON
- Upload: gs://madhav-marsys-sources/L9/school_analyses/<school>_analysis.json (7 files)

**MULTI_SCHOOL_ANALYSIS_v1_0.md structure:**
- §1 Executive Summary: which domains show HIGH/MEDIUM/LOW convergence (preview)
- §2–§8 Per-school sections (one per school):
  - School philosophy (2 sentences)
  - Per-domain score (tabular: domain → score → direction → top 3 signals)
  - School verdict paragraph (3–5 sentences; acharya-grade prose)
- §9 Cross-school comparison table: 7 schools × 5 domains matrix of directions
- §10 Initial convergence hotspots: domains where 5+ schools agree

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M9C.1 | run_multi_school_analysis.py present; idempotent; exits 0 |
| AC.M9C.2 | school_analysis_runs: 35 rows (7 schools × 5 domains); no NULL domain_scores |
| AC.M9C.3 | 7 school analysis JSON files uploaded to GCS L9/school_analyses/ |
| AC.M9C.4 | MULTI_SCHOOL_ANALYSIS_v1_0.md present; §1–§10 all authored; acharya-grade prose |
| AC.M9C.5 | [VARSHA_KUNDALI_PENDING] and [TRANSIT_DATA_PENDING] flags present where applicable; not treated as failures |
| AC.M9C.6 | SESSION_LOG M9-C-S1 appended; CURRENT_STATE updated; IS.8(a) check run |

---

### M9-D — Convergence Scoring + Pipeline Integration

**Scope:** Compute convergence scores for all 5 domains from M9-C results. Produce
CONVERGENCE_METRICS_v1_0.md and CONVERGENCE_FINDINGS_v1_0.md. Wire multi_school_triangulation
plan type into existing pipeline. Implement tools 27+28 (full; stub → production). Write
integration tests (≥10). Planner golden set updated with ≥3 multi_school examples.

**Session:** M9-D-S1

**Convergence computation script:** `platform/scripts/m9/compute_convergence.py`
- Read school_analysis_runs for all 7 schools × 5 domains
- Call computeConvergence() per domain (via ts-node or reimplement in Python)
- INSERT into convergence_scores (35 rows in final; plus per-domain summaries)
- Upload convergence_scores.json to GCS L9/convergence/

**CONVERGENCE_FINDINGS_v1_0.md — structure:**
- §1 Convergence Summary Table: domain → convergence_level → direction → schools_agreeing/7
- §2 HIGH convergence domains: acharya-grade narrative on what the agreement means
- §3 LOW convergence domains: nature of the divergence and what it reveals
- §4 Convergence as precision signal: where all schools agree, that agreement amplifies
  the signal weight beyond what any single-school calibration can achieve
- §5 Divergence as finding: where schools disagree, what each school is sensitive to
  that the others are not — tradition-specific lenses made explicit

**Pipeline integration:**
- Implement tool 27 (multi_school_signal_lookup): full TypeScript, replaces stub
- Implement tool 28 (convergence_score_lookup): full TypeScript, replaces stub
- Add multi_school_triangulation to query_plan_types.ts
- Wire tools 27+28 into tool_fetch.ts dispatch
- Compose_bundle: add convergence block (convergence_level badge + per-school scores)
- Synthesis prompt: add multi-school template block:
  "Schools agreeing: [N/7]. Convergence: [HIGH/MEDIUM/LOW]. [School list] converge on [direction]."
- Update planner golden set: ≥3 multi_school_triangulation examples

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M9D.1 | convergence_scores: 5 domain rows; convergence_level populated; deterministic re-run |
| AC.M9D.2 | convergence_scores.json uploaded to GCS L9/convergence/ |
| AC.M9D.3 | CONVERGENCE_METRICS_v1_0.md present (tabular data) |
| AC.M9D.4 | CONVERGENCE_FINDINGS_v1_0.md present; §1–§5 complete; acharya-grade prose |
| AC.M9D.5 | Tool 27 multi_school_signal_lookup: full impl; ≥6 unit tests; passing |
| AC.M9D.6 | Tool 28 convergence_score_lookup: full impl; ≥6 unit tests; passing |
| AC.M9D.7 | multi_school_triangulation plan type active; pipeline end-to-end wired |
| AC.M9D.8 | ≥10 integration tests in platform/tests/schools/; tsc 0 errors |
| AC.M9D.9 | Planner golden set: ≥3 multi_school_triangulation entries added |
| AC.M9D.10 | SESSION_LOG M9-D-S1 appended; CAPABILITY_MANIFEST updated; CURRENT_STATE updated |

---

### M9-E — Disagreement Register + Quality Gate + M9 Close

**Scope:** Build the school-disagreement register with ≥10 worked examples. Run IS.8(b)
macro-phase-close red-team. Verify convergence stability (deterministic re-run). Author
M9_CLOSE_v1_0.md. Update CURRENT_STATE to M9 CLOSED / M10 INCOMING. Propagate mirrors.

**Session:** M9-E-S1

**Disagreement register construction:**
- Identify all domain × school combinations where direction disagrees with plurality
  (SELECT from school_analysis_runs WHERE direction != plurality_direction for domain)
- Classify each disagreement: method_divergence / signal_gap / tradition_specificity / temporal_scope
- Write resolution reasoning for each
- INSERT into school_disagreements; populate school_disagreement_register.json
- Write ≥10 worked examples in SCHOOL_DISAGREEMENT_REGISTER_v1_0.md:
  Each example: domain → which schools agree → which disagree → disagreement_class →
  resolution reasoning → verdict → "What this reveals about this tradition's lens"

**Disagreement register script:** `platform/scripts/m9/build_disagreement_register.py`

**Convergence stability check:**
- Re-run compute_convergence.py from scratch (re-reads school_analysis_runs; recomputes)
- Diff output against existing convergence_scores.json
- PASS if output is byte-identical (determinism verified)
- FAIL if any domain's convergence_level differs → HALT, report as RT finding

**IS.8(b) red-team axes:**
- RT.M9.1 — Factual accuracy: spot-check 10 random school_analysis_runs rows; verify signal_ids
  exist in MSR_v5_0.md; verify domainScore is within 0.0–5.0; no fabricated signal names.
  PASS if 10/10 valid.
- RT.M9.2 — Layer separation: verify MULTI_SCHOOL_ANALYSIS_v1_0.md contains no raw L1 chart
  values (no planetary degrees, no house cusps stated as absolute facts — only signal citations).
  PASS if B.10 discipline maintained throughout.
- RT.M9.3 — Derivation ledger: verify CONVERGENCE_FINDINGS_v1_0.md cites school_analysis_runs
  run IDs for every convergence claim. PASS if all claims traceable.
- RT.M9.4 — Mirror discipline: verify .geminirules §F + §C reflect M9 CLOSED state.
  PASS if both surfaces updated.
- RT.M9.5 — Scope discipline: verify no M10 infrastructure pre-built (no 10_LLM_ACHARYA_INTERFACE/
  dir; no migrations above 060). PASS if clean.

**M9_CLOSE_v1_0.md structure:**
  §0 Session arc (M9-A through M9-E; dates + key outcomes)
  §1 AC ledger (all sub-phases; PASS/FAIL/DEFERRED)
  §2 IS.8(b) red-team record (5 axes + verdicts)
  §3 MSR evolution: v4.0 (543 signals) → v5.0 (543 + Yogini + Tajika net-new; count updated)
  §4 Convergence summary: per-domain convergence_level; top HIGH-convergence domain
  §5 School-disagreement register summary: total disagreements; class breakdown
  §6 Pending items: [VARSHA_KUNDALI_PENDING] + [TRANSIT_DATA_PENDING] carried as CF.M9.1 + CF.M9.2
  §7 Exit criteria verification:
      a) All 7 schools operating on shared signal set: [MET / PARTIAL per pending flags]
      b) Inter-school convergence metrics calibrated: [MET]
      c) Disagreement protocol ≥10 worked examples: [MET]
      d) Convergence-as-precision-signal evidence: [MET — CONVERGENCE_FINDINGS §4]
  §8 Seal block: M9_CLOSE_STATUS: CLOSED; closed_at; NAP.M9.5 PRE-AUTHORIZED;
     m10_entry_condition: M9 CLOSED AND acharya panel ≥3 recruited → M10 ENTRY GATE

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M9E.1 | school_disagreements: ≥10 rows; all required fields populated; worked_example_narrative present |
| AC.M9E.2 | SCHOOL_DISAGREEMENT_REGISTER_v1_0.md: ≥10 worked examples; classification + resolution for each |
| AC.M9E.3 | school_disagreement_register.json uploaded to GCS L9/convergence/ |
| AC.M9E.4 | Convergence stability: re-run byte-identical to stored results |
| AC.M9E.5 | IS.8(b) red-team: all 5 axes PASS; 0 CRITICAL / 0 HIGH findings |
| AC.M9E.6 | M9_CLOSE_v1_0.md present at 09_MULTI_SCHOOL_TRIANGULATION/M9_CLOSE_v1_0.md; seal block present |
| AC.M9E.7 | CURRENT_STATE updated: M9 CLOSED / M10 INCOMING; red_team_counter=0 |
| AC.M9E.8 | SESSION_LOG M9-E-S1 appended (full M9 arc summary) |
| AC.M9E.9 | CAPABILITY_MANIFEST: M9_CLOSE entry added |
| AC.M9E.10 | MP.1 + MP.2 + MP.4 mirrors propagated to M9-CLOSED state |
| AC.M9E.11 | CLAUDECODE_BRIEF.md archived to 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M9_v1_0.md |
| AC.M9E.12 | All M9 exit criteria (MACRO_PLAN §M9 a–d) documented as MET or PARTIAL in M9_CLOSE §7 |

---

## §5 — Global may_touch / must_not_touch (all M9 sessions)

```yaml
may_touch:
  - 09_MULTI_SCHOOL_TRIANGULATION/**
  - 00_ARCHITECTURE/PHASE_M9_PLAN_v1_0.md
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  - 00_ARCHITECTURE/SESSION_LOG.md
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md
  - 00_ARCHITECTURE/briefs/**
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md        # new file; v4_0 is read-only
  - platform/supabase/migrations/057_*.sql
  - platform/supabase/migrations/058_*.sql
  - platform/supabase/migrations/059_*.sql
  - platform/supabase/migrations/060_*.sql
  - platform/src/lib/schools/**
  - platform/src/lib/tools/multi_school_signal_lookup.ts
  - platform/src/lib/tools/convergence_score_lookup.ts
  - platform/src/lib/tools/index.ts
  - platform/src/lib/planner/query_plan_types.ts
  - platform/src/lib/pipeline/tool_fetch.ts
  - platform/src/lib/pipeline/compose_bundle.ts
  - platform/scripts/m9/**
  - platform/tests/schools/**
  - .geminirules
  - .gemini/project_state.md
  - CLAUDECODE_BRIEF.md   # status field + archive operation only

must_not_touch:
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_*.md   # read-only source
  - 01_FACTS_LAYER/LIFE_EVENT_LOG_*.md               # read-only
  - 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md               # read-only; v5_0 is new file
  - 025_HOLISTIC_SYNTHESIS/UCN_*.md
  - 025_HOLISTIC_SYNTHESIS/CDLM_*.md
  - 025_HOLISTIC_SYNTHESIS/RM_*.md
  - 025_HOLISTIC_SYNTHESIS/CGM_*.md
  - 06_LEARNING_LAYER/PREDICTION_LEDGER/**
  - 06_LEARNING_LAYER/dbn/**
  - 07_PROSPECTIVE_TESTING/**
  - 08_CLASSICAL_CROSS_REFERENCE/**                  # read-only reference
  - platform/supabase/migrations/001_*.sql            # through 056_*.sql — all prior migrations
  - 10_LLM_ACHARYA_INTERFACE/**                       # do not pre-build M10
```

---

## §6 — LLM Stack Constraint

NO Anthropic/Claude API in any M9 code.
Stack: Gemini → DeepSeek → NIM.
  Signal extraction passes (critical): gemini-2.5-pro
  Coverage audit + classification (non-critical): gemini-2.5-flash-lite
  School engine LLM verdicts (critical): gemini-2.5-pro or deepseek-v4-pro
  Embedding (if needed): Vertex AI text-embedding-004

---

## §7 — Session-Open Handshake

Every M9 session emits SESSION_OPEN artifact per SESSION_OPEN_TEMPLATE_v1_0.md before any
tool call. Session IDs: M9-A-S1, M9-B-S1, M9-C-S1, M9-D-S1, M9-E-S1.
cowork_thread_name must match handshake session_id field.

---

## §8 — Risk Register

| Risk | Mitigation |
|---|---|
| Yogini signal count < 8 from BPHS | BPHS has 1032 chunks; Yogini Dasha is a full chapter (~50 chunks minimum). If extraction yields < 8 signals, lower confidence threshold to 0.50 and re-run. |
| Tajika Neelakanthi unavailable at archive.org | Proceed with Prashna Marga + Hora Sara extraction. Minimum viable: ≥10 Tajika signals. If gap, document as CF.M9.3 |
| [VARSHA_KUNDALI_PENDING] blocks Tajika convergence | Tajika excluded from convergence where pending; convergence_total drops to 6 for those domains. Not a block on M9 close — documented as CF.M9.1 |
| [TRANSIT_DATA_PENDING] blocks BNN triggers | BNN engine uses placeholder; BNN domain scores marked approximate. Not a block on M9 close — documented as CF.M9.2 |
| School engine produces NaN domain_score | Validation in school_runner.ts: if domainScore is NaN/null, engine returns domainScore=0 with school_verdict="[SIGNAL_COVERAGE_GAP: insufficient primary signals for this domain]" |
| Convergence stability re-run fails | Indicates non-determinism in convergence_calculator.ts. Fix by seeding any random components and re-test before M9-E proceeds |
| Spurious convergence (all schools share same underlying data) | Cross-school signal-provenance tracking: school_signal_coverage.attribution_chunk_id must differ across schools for same domain. Verify in RT.M9.3 |

---

*End of PHASE_M9_PLAN_v1_0.md*

---
artifact: PHASE_M8_PLAN_v1_0.md
canonical_id: PHASE_M8_PLAN
version: 1.0
status: CURRENT
governing_macro_phase: M8 — Classical Text Cross-Reference
active_sub_phase: M8-A (INCOMING)
authored_at: 2026-05-14
authored_by: Cowork-M8-PLAN-AUTHORING
predecessor_closed: 06_LEARNING_LAYER/M5_CLOSE_v1_0.md (M5 CLOSED 2026-05-14)
m8_entry_condition_met: true
entry_condition_basis: >
  M5 CLOSED 2026-05-14 (M5-E-S2; CURRENT_STATE_v1_0.md v5.3).
  M6 time-gated and running in parallel — does NOT block M8.
  MACRO_PLAN §3.8.C: "M8 can begin once M5 produces calibrated weights; M7 and M8
  may overlap; M8 does NOT require M6 closed."
m6_parallel_status: >
  M6 is PAUSED on time-gate (≥50 prediction windows with ≥6-month horizon must elapse).
  M6 CLAUDECODE_BRIEF archived to 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M6_v1_0.md.
  M6 resumes once window volume gate is met (target: ~2026-11-15 minimum).
nap_pre_authorizations:
  - NAP.M8.0: corpus shortlist APPROVED (tiers defined in §2 below — no halt required)
  - NAP.M8.1: attribution confidence thresholds APPROVED (HIGH ≥0.75; MEDIUM 0.50–0.75; LOW <0.50)
  - NAP.M8.2: disclosure policy APPROVED (classical-claim-failure findings published per §3.5.B with attribution + translation source; no suppression)
  - NAP.M8.3: MSR expansion APPROVED (Nadi + BNN signals extracted from ingested corpus; proposal auto-promoted after IS.8(a) red-team PASS)
  - NAP.M8.4: M8 macro-phase close APPROVED (no halt at M8-H; executor closes on IS.8(b) PASS)
session_count: 8
execution_mode: fully_autonomous_sequential (dangerously-skip-permissions)
llm_stack_constraint: Gemini → DeepSeek → NIM. No Anthropic/Claude API in any written code.
changelog:
  - v1.0 (2026-05-14, Cowork-M8-PLAN-AUTHORING): Initial plan. 8 sub-sessions (M8-A through M8-H).
    All NAP gates pre-resolved. Entry condition confirmed met (M5 CLOSED 2026-05-14).
---

# PHASE_M8_PLAN — M8 Classical Text Cross-Reference

## §1 — M8 Scope (from MACRO_PLAN_v2_0.md §M8)

Build an indexed corpus of the canonical classical Jyotish texts. Cross-reference every M5
probabilistic output and every MSR signal against classical attributions. Where classical
claims systematically hold or fail becomes a finding in itself. Expand the MSR signal-set
to include Nadi and BNN school signals — this expansion is M9's prerequisite. Wire classical
citation into the existing query pipeline so live queries can cite source text and verse.

**Exit criteria (verbatim from MACRO_PLAN §M8):**
a) All listed corpora indexed and attributed
b) Classical-claim-holds/fails findings produced for each M5 probabilistic output
c) Attribution confidence tags populated for every citation
d) Translation-accuracy cross-check completed for non-English classical sources
e) MSR signal-set expanded to include Nadi + BNN school signals (enables M9)

**Quality gate:** Native acharya-grade review of attribution accuracy on 20 representative findings;
translation cross-check passes for all non-English sources.

---

## §2 — Corpus Procurement Map (NAP.M8.0 PRE-AUTHORIZED)

### Tier 1 — Mandatory (highest attribution demand)

| Text | Author | Translation / Edition | Primary Source |
|---|---|---|---|
| Brihat Parashara Hora Shastra (BPHS) | Maharishi Parashara | R. Santhanam (Ranjan Publications) | archive.org / sacred-texts.com |
| Phaladeepika | Mantreswara | Sitaram Jha (Ranjan Publications) | archive.org |

### Tier 2 — High priority

| Text | Author | Translation / Edition | Primary Source |
|---|---|---|---|
| Saravali | Kalyanvarma | R. Santhanam | archive.org |
| Uttara Kalamrita | Kalidasa | V. Subrahmanya Sastri | archive.org |
| Jaimini Sutra | Maharishi Jaimini | Iranganti Rangacharya | sacred-texts.com / archive.org |

### Tier 3 — Standard priority

| Text | Author | Translation / Edition | Primary Source |
|---|---|---|---|
| Prashna Marga | Narayanan Namboodiri | B.V. Raman | archive.org |
| Hora Sara | Prithuyasas | R. Santhanam | archive.org |
| Krishnamurti Padhdhati (KP) Vols 1–4 | K.S. Krishnamurti | Original KP texts | kpastrology.com / archive.org |
| Brihat Jataka | Varahamihira | P.S. Sastri | sacred-texts.com |
| Brihat Samhita | Varahamihira | M.R. Bhat | sacred-texts.com / archive.org |

### Nadi / BNN tier (M8-F; M9 prerequisite)

| Text | School | Source |
|---|---|---|
| Bhrigu Nandi Nadi | Bhrigu Nandi (BNN) | R.G. Rao translation; archive.org |
| Chandra Kala Nadi | Nadi | R. Santhanam; archive.org |
| Dhruva Nadi (sampler) | Nadi | archive.org (partial) |

**Ingestion strategy:** Python scripts per text using `requests` + `BeautifulSoup` for web sources;
`pymupdf` / `pdfplumber` for PDF sources from archive.org. Each script idempotent — re-run safe.

---

## §3 — Architecture Additions

### 3.1 — GCS Layout Extension

New prefix added to `gs://madhav-marsys-sources/`:

```
gs://madhav-marsys-sources/
└── L8/
    ├── classical_texts/
    │   ├── tier1/
    │   │   ├── bphs_chunks.jsonl
    │   │   └── phaladeepika_chunks.jsonl
    │   ├── tier2/
    │   │   ├── saravali_chunks.jsonl
    │   │   ├── uttara_kalamrita_chunks.jsonl
    │   │   └── jaimini_sutra_chunks.jsonl
    │   └── tier3/
    │       ├── prashna_marga_chunks.jsonl
    │       ├── hora_sara_chunks.jsonl
    │       ├── kp_vols_chunks.jsonl
    │       ├── brihat_jataka_chunks.jsonl
    │       └── brihat_samhita_chunks.jsonl
    ├── nadi_bnn/
    │   ├── bhrigu_nandi_nadi_chunks.jsonl
    │   ├── chandra_kala_nadi_chunks.jsonl
    │   └── dhruva_nadi_sampler_chunks.jsonl
    └── registries/
        ├── CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md
        └── CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json
```

CLAUDECODE_BRIEF executor must call `gsutil cp` or equivalent SDK method to sync after each
ingestion batch. Do NOT write raw gs:// URIs before reading GCS_LAYOUT_v1_0.md.

### 3.2 — Database Migrations

Three new migrations (046–048) under `platform/supabase/migrations/`:

**Migration 046 — classical_texts**
```sql
CREATE TABLE classical_texts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text_key TEXT NOT NULL UNIQUE,          -- e.g. 'bphs', 'phaladeepika'
  title TEXT NOT NULL,
  author TEXT,
  tradition TEXT NOT NULL,               -- 'parashari', 'jaimini', 'tajika', 'kp', 'nadi', 'bnn'
  school TEXT NOT NULL,                  -- sub-school tag
  tier INTEGER NOT NULL CHECK (tier IN (1,2,3)),
  language_original TEXT NOT NULL,       -- 'sanskrit', 'english'
  translation_author TEXT,
  source_url TEXT,
  procurement_date DATE,
  chunk_count INTEGER DEFAULT 0,
  attribution_baseline_confidence NUMERIC(4,3) DEFAULT 0.5,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Migration 047 — classical_chunks**
```sql
CREATE TABLE classical_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text_id UUID NOT NULL REFERENCES classical_texts(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  chapter TEXT,
  verse_range TEXT,                      -- e.g. '1.1–1.5'
  content TEXT NOT NULL,
  embedding VECTOR(768),                 -- Vertex AI text-embedding-004
  language TEXT NOT NULL DEFAULT 'en',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (text_id, chunk_index)
);
CREATE INDEX classical_chunks_embedding_idx ON classical_chunks USING ivfflat (embedding vector_cosine_ops);
```

**Migration 048 — classical_attributions**
```sql
CREATE TABLE classical_attributions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  msr_signal_id TEXT NOT NULL,           -- MSR signal ID (e.g. 'MSR.001')
  chunk_id UUID NOT NULL REFERENCES classical_chunks(id) ON DELETE CASCADE,
  attribution_type TEXT NOT NULL CHECK (
    attribution_type IN ('confirms', 'contradicts', 'partial', 'extends', 'silent')
  ),
  confidence NUMERIC(4,3) NOT NULL,      -- 0.000–1.000
  confidence_tier TEXT GENERATED ALWAYS AS (
    CASE
      WHEN confidence >= 0.75 THEN 'HIGH'
      WHEN confidence >= 0.50 THEN 'MEDIUM'
      ELSE 'LOW'
    END
  ) STORED,
  derivation_notes TEXT,
  translation_cross_checked BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX classical_attributions_signal_idx ON classical_attributions(msr_signal_id);
```

### 3.3 — New LLM Tools (Tools 25 + 26)

Added to the existing 24-tool registry at `platform/lib/tools/`:

**Tool 25: `classical_text_search`**
- Input: `{ query: string, schools?: string[], tier_max?: number, limit?: number }`
- Semantic search over `classical_chunks` using Vertex AI embedding + pgvector cosine similarity
- Returns: top-K chunks with text_key, author, chapter, verse_range, content, confidence_baseline
- Used by: tool_fetch stage for queries touching classical attribution

**Tool 26: `classical_attribution_lookup`**
- Input: `{ signal_ids: string[], attribution_type?: string, confidence_tier?: string }`
- Structured lookup in `classical_attributions` JOIN `classical_chunks` JOIN `classical_texts`
- Returns: all attributions for given MSR signal IDs, grouped by text
- Used by: synthesis stage to append classical grounding to signal-level claims

### 3.4 — Folder Structure (08_CLASSICAL_CROSS_REFERENCE/)

```
08_CLASSICAL_CROSS_REFERENCE/
├── README.md
├── PROCUREMENT_MAP_v1_0.md          ← tier list + sources (M8-A deliverable)
├── corpus/
│   ├── ingestion/
│   │   ├── scripts/                 ← per-text Python ingestion scripts
│   │   └── logs/                    ← per-run ingestion logs (gitignored)
│   └── raw/                         ← raw fetched text (gitignored; GCS is canonical)
├── attributions/
│   ├── CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md    ← narrative
│   ├── CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json  ← machine-readable
│   └── findings/
│       ├── FINDINGS_M5_CROSS_REF_v1_0.md  ← M5 signal → classical attribution
│       └── FINDINGS_CLASSICAL_CLAIM_v1_0.md ← holds/fails per text
├── nadi_bnn/
│   ├── NADI_SIGNAL_EXTRACTION_v1_0.md
│   ├── BNN_SIGNAL_EXTRACTION_v1_0.md
│   └── MSR_EXPANSION_PROPOSAL_v1_0.md
├── quality/
│   ├── TRANSLATION_CROSS_CHECK_v1_0.md
│   └── ACHARYA_REVIEW_SAMPLE_v1_0.md  ← 20 representative findings
└── M8_CLOSE_v1_0.md                   ← authored at M8-H-S1 close
```

---

## §4 — Sub-Phase Definitions

### M8-A — Foundation + Infrastructure + Procurement Setup

**Scope:** Archive M6 CLAUDECODE_BRIEF; scaffold 08_CLASSICAL_CROSS_REFERENCE/;
run DB migrations 046–048; extend GCS_LAYOUT_v1_0.md with L8/ prefix;
write PROCUREMENT_MAP_v1_0.md; register tools 25+26 stubs in tool registry;
update CAPABILITY_MANIFEST.json and SESSION_LOG.

**Session:** M8-A-S1

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M8A.1 | 08_CLASSICAL_CROSS_REFERENCE/ scaffold created; all subdirs present |
| AC.M8A.2 | DB migrations 046/047/048 applied; tables verified (psql \dt or equivalent) |
| AC.M8A.3 | GCS_LAYOUT_v1_0.md updated with L8/ prefix block (in-place amendment) |
| AC.M8A.4 | PROCUREMENT_MAP_v1_0.md present: all 14 texts listed with source URLs |
| AC.M8A.5 | Tool stubs created: classical_text_search.ts + classical_attribution_lookup.ts |
| AC.M8A.6 | Tool registry updated to include tools 25 + 26 |
| AC.M8A.7 | M6 CLAUDECODE_BRIEF archived: git mv CLAUDECODE_BRIEF.md 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M6_v1_0.md |
| AC.M8A.8 | CAPABILITY_MANIFEST.json updated: PHASE_M8_PLAN + 08_CLASSICAL_CROSS_REFERENCE entries |
| AC.M8A.9 | CURRENT_STATE updated: active_macro_phase=M8 OPEN / M6 TIME-GATED PARALLEL |
| AC.M8A.10 | SESSION_LOG M8-A-S1 appended |
| AC.M8A.11 | MP.1 + MP.2 + MP.4 mirrors propagated (.geminirules + .gemini/project_state.md) |

**may_touch:** 08_CLASSICAL_CROSS_REFERENCE/\*\*, CLAUDECODE_BRIEF.md, 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M6_v1_0.md, 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md, 00_ARCHITECTURE/PHASE_M8_PLAN_v1_0.md, 00_ARCHITECTURE/CURRENT_STATE_v1_0.md, 00_ARCHITECTURE/SESSION_LOG.md, 00_ARCHITECTURE/CAPABILITY_MANIFEST.json, platform/supabase/migrations/046\*.sql, platform/supabase/migrations/047\*.sql, platform/supabase/migrations/048\*.sql, platform/lib/tools/classical_text_search.ts, platform/lib/tools/classical_attribution_lookup.ts, platform/lib/tools/index.ts (tool registry), .geminirules, .gemini/project_state.md

**must_not_touch:** 01_FACTS_LAYER/\*\*, 025_HOLISTIC_SYNTHESIS/\*\*, 06_LEARNING_LAYER/PREDICTION_LEDGER/\*\*, platform/src/\*\* (except tool stubs), any existing migrations 001–045

---

### M8-B — Tier 1 Ingestion (BPHS + Phaladeepika)

**Scope:** Write ingestion scripts for BPHS and Phaladeepika; fetch, preprocess, chunk, embed,
load into DB and GCS; verify chunk counts and embedding dimensions.

**Session:** M8-B-S1

**Ingestion pipeline per text:**
1. Fetch from source URL (archive.org / sacred-texts.com) — handle pagination and multiple chapters
2. Clean: strip HTML/PDF artifacts, normalize whitespace, deduplicate
3. Chunk: 400–600 tokens per chunk with 80-token overlap; preserve verse boundaries where possible
4. Embed: Vertex AI `text-embedding-004` (768 dimensions) — batch API calls
5. Load: INSERT into `classical_texts` + bulk INSERT into `classical_chunks`
6. Upload: `gsutil -m cp` chunked JSONL to `gs://madhav-marsys-sources/L8/classical_texts/tier1/`
7. Verify: SELECT count(*), avg(length(content)) FROM classical_chunks WHERE text_id = ?

**Script paths:**
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_bphs.py`
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_phaladeepika.py`
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_utils.py` (shared utilities)

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M8B.1 | ingest_bphs.py complete; idempotent (re-run safe); exits 0 |
| AC.M8B.2 | BPHS: ≥800 chunks loaded; embeddings present (embedding IS NOT NULL on ≥95% rows) |
| AC.M8B.3 | ingest_phaladeepika.py complete; idempotent; exits 0 |
| AC.M8B.4 | Phaladeepika: ≥300 chunks loaded; embeddings present ≥95% |
| AC.M8B.5 | Both texts uploaded to GCS L8/classical_texts/tier1/ |
| AC.M8B.6 | classical_texts rows: tier=1, chunk_count updated after ingestion |
| AC.M8B.7 | SESSION_LOG M8-B-S1 appended; CAPABILITY_MANIFEST updated |

---

### M8-C — Tier 2 Ingestion (Saravali + Uttara Kalamrita + Jaimini Sutra)

**Scope:** Repeat ingestion pipeline for three tier-2 texts.

**Session:** M8-C-S1

**Script paths:**
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_saravali.py`
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_uttara_kalamrita.py`
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_jaimini_sutra.py`

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M8C.1 | All three scripts complete; idempotent; exit 0 |
| AC.M8C.2 | Saravali: ≥400 chunks loaded; embeddings ≥95% |
| AC.M8C.3 | Uttara Kalamrita: ≥200 chunks loaded; embeddings ≥95% |
| AC.M8C.4 | Jaimini Sutra: ≥150 chunks loaded; embeddings ≥95% |
| AC.M8C.5 | All three uploaded to GCS L8/classical_texts/tier2/ |
| AC.M8C.6 | SESSION_LOG M8-C-S1 appended; CAPABILITY_MANIFEST updated |

---

### M8-D — Tier 3 Ingestion (Remaining 5 texts)

**Scope:** Ingest Prashna Marga, Hora Sara, KP texts (Vols 1–4), Brihat Jataka, Brihat Samhita.

**Session:** M8-D-S1

**Script paths:**
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_prashna_marga.py`
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_hora_sara.py`
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_kp_texts.py`
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_brihat_jataka.py`
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_brihat_samhita.py`

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M8D.1 | All 5 scripts complete; idempotent; exit 0 |
| AC.M8D.2 | Prashna Marga: ≥300 chunks; embeddings ≥95% |
| AC.M8D.3 | Hora Sara: ≥200 chunks; embeddings ≥95% |
| AC.M8D.4 | KP Vols 1–4: ≥500 chunks combined; embeddings ≥95% |
| AC.M8D.5 | Brihat Jataka: ≥250 chunks; embeddings ≥95% |
| AC.M8D.6 | Brihat Samhita: ≥300 chunks; embeddings ≥95% |
| AC.M8D.7 | All uploaded to GCS L8/classical_texts/tier3/ |
| AC.M8D.8 | Total classical_chunks count ≥3,200 across all tier-1/2/3 texts |
| AC.M8D.9 | SESSION_LOG M8-D-S1 appended; CAPABILITY_MANIFEST updated |

---

### M8-E — Attribution Engine + Classical Tools Implementation

**Scope:** Build the classical_text_search and classical_attribution_lookup tools to production
quality. Run the cross-reference pass: for each MSR signal and each M5 probabilistic output,
query the corpus and populate classical_attributions. Produce CLASSICAL_ATTRIBUTION_REGISTRY
(both .md and .json forms) and FINDINGS_M5_CROSS_REF_v1_0.md.

**Session:** M8-E-S1

**Attribution pass algorithm:**
1. Load all MSR signal IDs from MSR_v3_0.md (514 signals)
2. For each signal: call classical_text_search with signal name + domain as query
3. For top-K chunks (K=5): LLM judge (Gemini Pro) assigns attribution_type + confidence
4. INSERT into classical_attributions; confidence_tier generated automatically
5. After all signals: produce CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json

**M5 probabilistic outputs cross-reference:**
- Load dbn_params_v1_0.json + DBN_TOPOLOGY_v1_0.md (calibrated weights)
- For each domain (CAREER, HEALTH, RELATIONSHIP, SPIRITUAL, PSYCHOLOGICAL):
  identify top-10 signals by weight → run attribution pass → log in FINDINGS_M5_CROSS_REF_v1_0.md
- Classify each top-10 signal: classical claim HOLDS / FAILS / PARTIAL / SILENT (no classical mention)

**CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json schema:**
```json
{
  "version": "1.0",
  "generated_at": "<ISO8601>",
  "total_signals": 514,
  "total_attributions": <count>,
  "coverage_by_tier": { "HIGH": 0, "MEDIUM": 0, "LOW": 0 },
  "attributions": [
    {
      "signal_id": "MSR.001",
      "text_key": "bphs",
      "chapter": "Ch. 4",
      "verse_range": "4.1–4.3",
      "attribution_type": "confirms",
      "confidence": 0.82,
      "confidence_tier": "HIGH",
      "derivation_notes": "..."
    }
  ]
}
```

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M8E.1 | classical_text_search tool: full implementation; unit tests ≥8; all passing |
| AC.M8E.2 | classical_attribution_lookup tool: full implementation; unit tests ≥6; all passing |
| AC.M8E.3 | classical_attributions table: ≥400 rows populated (≥400 of 514 signals attributed) |
| AC.M8E.4 | CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json present; valid JSON; schema matches spec |
| AC.M8E.5 | CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md present: narrative companion |
| AC.M8E.6 | FINDINGS_M5_CROSS_REF_v1_0.md present: top-10 signals per domain × 5 domains cross-referenced |
| AC.M8E.7 | FINDINGS_CLASSICAL_CLAIM_v1_0.md present: holds/fails/partial/silent counts per text |
| AC.M8E.8 | SESSION_LOG M8-E-S1 appended; CAPABILITY_MANIFEST updated |

---

### M8-F — Nadi + BNN Ingestion + Signal Extraction + MSR Expansion

**Scope:** Ingest Nadi/BNN texts. Run a dedicated signal-extraction LLM pass to identify
Nadi-specific and BNN-specific predictive signals (e.g., Arudha-based patterns, Chara Karaka
hierarchies, specific nadi yogas). Draft MSR_EXPANSION_PROPOSAL_v1_0.md and author the
final expanded MSR_v4_0.md with new signals appended.

**Session:** M8-F-S1

**Nadi ingestion scripts:**
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_bhrigu_nandi_nadi.py`
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_chandra_kala_nadi.py`
- `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_dhruva_nadi_sampler.py`

**Signal extraction pass:**
1. Semantic search over nadi_bnn/ chunks for predictive-signal patterns
2. LLM judge (Gemini Pro): for each candidate signal, extract:
   - signal_name, signal_domain, school (nadi/bnn), trigger_condition, predicted_outcome,
     source_verse, confidence_in_extraction
3. De-duplicate against existing 514 MSR signals (semantic similarity threshold 0.85 cosine)
4. Signals with extraction_confidence ≥ 0.60 and not duplicating existing signals → candidates for MSR expansion

**MSR expansion:**
- New signals assigned IDs MSR.515 onward
- Author MSR_v4_0.md: copy MSR_v3_0.md + append new Nadi/BNN section
- GCS: upload to L2_5/MSR_v4_0.md (overwrite in place per GCS versioning policy)
- CAPABILITY_MANIFEST: update MSR entry to v4_0

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M8F.1 | All 3 Nadi/BNN ingestion scripts complete; idempotent; exit 0 |
| AC.M8F.2 | Nadi/BNN chunks loaded to DB + GCS L8/nadi_bnn/ |
| AC.M8F.3 | NADI_SIGNAL_EXTRACTION_v1_0.md present: all candidate signals with extraction_confidence |
| AC.M8F.4 | BNN_SIGNAL_EXTRACTION_v1_0.md present: BNN-specific signals |
| AC.M8F.5 | MSR_EXPANSION_PROPOSAL_v1_0.md present: new signals deduplicated vs. MSR_v3_0; ≥15 net-new signals proposed |
| AC.M8F.6 | MSR_v4_0.md authored: version bump from v3.1 → v4.0; changelog entry; new signals in dedicated §Nadi + BNN |
| AC.M8F.7 | MSR_v4_0.md uploaded to GCS L2_5/; CANONICAL_ARTIFACTS + CAPABILITY_MANIFEST updated |
| AC.M8F.8 | SESSION_LOG M8-F-S1 appended |

---

### M8-G — Query Pipeline Integration

**Scope:** Wire classical_text_search (tool 25) and classical_attribution_lookup (tool 26)
into the existing query pipeline. Classical tools activate when the plan_per_tool stage
classifies the query as requiring classical_grounding (new plan type). Update disclosure
filter for classical-literature tier. Integration tests (10 end-to-end). Update manifest.

**Session:** M8-G-S1

**Pipeline integration points:**
1. **Plan type:** Add `classical_grounding` to QueryPlan plan_types
2. **tool_fetch:** Register tools 25+26 in the tool-dispatch switch; call sequence: tool_fetch calls classical_text_search → passes results to synthesis
3. **compose_bundle:** If plan includes classical_grounding, include classical_attribution_lookup results in the bundle
4. **Synthesis prompt:** Add classical citation block: "Source: [text_title], [chapter], verse [verse_range] ([translation_author])."
5. **Disclosure filter:** Add classical-literature tier disclosure: "Classical attribution drawn from [text]; confidence tier: [HIGH/MEDIUM/LOW]. Translation accuracy cross-checked: [yes/no]."

**File paths:**
- `platform/lib/tools/classical_text_search.ts` — (already stubbed; implement fully here)
- `platform/lib/tools/classical_attribution_lookup.ts` — (already stubbed; implement fully here)
- `platform/lib/planner/query_plan_types.ts` — add `classical_grounding`
- `platform/lib/pipeline/tool_fetch.ts` — register tools 25+26
- `platform/lib/pipeline/compose_bundle.ts` — classical attribution block
- `platform/lib/disclosure/disclosure_filter.ts` — classical tier

**Tests:** `platform/tests/classical/classical_integration.test.ts` — ≥10 test cases covering:
- classical_text_search returns results for known signal query
- classical_attribution_lookup returns correct attributions for MSR.001–MSR.010 sample
- compose_bundle includes classical block when plan_type=classical_grounding
- disclosure_filter emits classical tier text correctly
- end-to-end: query → plan → fetch → bundle → synthesize (mock synthesis) with classical citation

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M8G.1 | classical_text_search.ts: full implementation; connects to pgvector; returns typed results |
| AC.M8G.2 | classical_attribution_lookup.ts: full implementation; joins attributions + chunks + texts |
| AC.M8G.3 | `classical_grounding` plan type added; planner golden set updated for ≥3 classical_grounding examples |
| AC.M8G.4 | tool_fetch dispatches to tools 25+26; compose_bundle includes classical block |
| AC.M8G.5 | Disclosure filter: classical-literature tier text emitted; confidence tier exposed |
| AC.M8G.6 | ≥10 integration tests; all passing; tsc 0 errors |
| AC.M8G.7 | SESSION_LOG M8-G-S1 appended; CAPABILITY_MANIFEST updated |

---

### M8-H — Quality Gate + Red-Team + M8 Close

**Scope:** Translation cross-check for Sanskrit-to-English sources. Sample 20 representative
attribution findings for acharya-grade review. IS.8(b) macro-phase-close red-team (5 axes).
Author M8_CLOSE_v1_0.md. Update CURRENT_STATE to M8 CLOSED / M9 INCOMING.
Archive this CLAUDECODE_BRIEF to 00_ARCHITECTURE/briefs/.

**Session:** M8-H-S1

**Translation cross-check protocol:**
For each non-English source (BPHS, Phaladeepika, Saravali, Uttara Kalamrita, Jaimini Sutra,
Hora Sara, Brihat Jataka, Brihat Samhita):
1. Identify 2–3 cited verses that appear in ≥1 HIGH-confidence attribution
2. Locate a second English translation (archive.org has multiple for most texts)
3. Compare: does the meaning agree across translations?
4. Record verdict: CONSISTENT / MINOR_VARIANCE / SIGNIFICANT_VARIANCE in TRANSLATION_CROSS_CHECK_v1_0.md
   - SIGNIFICANT_VARIANCE → downgrade affected attributions' confidence by 0.15

**20-finding acharya-grade sample:**
- Select 4 findings from each of 5 life domains (CAREER/HEALTH/RELATIONSHIP/SPIRITUAL/PSYCHOLOGICAL)
- For each: present signal → attribution → verse → confidence_tier → classical_claim_verdict
- Record in ACHARYA_REVIEW_SAMPLE_v1_0.md with self-assessment: would an independent acharya agree?

**IS.8(b) red-team axes:**
- RT.M8.1 — Factual accuracy: 0 fabricated computations, 0 invented verses, all chunk_ids traceable
- RT.M8.2 — Layer separation: L1 facts not mixed into L8 attributions; derivation ledger maintained
- RT.M8.3 — Attribution ledger: every classical claim in FINDINGS docs carries signal_id + chunk_id + confidence
- RT.M8.4 — Mirror discipline: .geminirules + .gemini/project_state.md current to M8 close state
- RT.M8.5 — Scope discipline: no M9 infrastructure pre-built; all must_not_touch respected

**M8_CLOSE_v1_0.md structure:** §0 session arc; §1 AC ledger (all sub-phases); §2 RT record;
§3 MSR expansion summary; §4 corpus statistics; §5 carry-forwards (CF.M8.1–N); §6 seal block.

**Acceptance criteria:**

| AC | Description |
|---|---|
| AC.M8H.1 | TRANSLATION_CROSS_CHECK_v1_0.md present; all 8 non-English texts checked; SIGNIFICANT_VARIANCE cases downgraded |
| AC.M8H.2 | ACHARYA_REVIEW_SAMPLE_v1_0.md present; 20 findings (4×5 domains); self-assessment complete |
| AC.M8H.3 | IS.8(b) red-team: all 5 axes PASS; 0 CRITICAL / 0 HIGH findings |
| AC.M8H.4 | M8_CLOSE_v1_0.md authored at 08_CLASSICAL_CROSS_REFERENCE/M8_CLOSE_v1_0.md; seal block present |
| AC.M8H.5 | CURRENT_STATE updated: active_macro_phase=M8 CLOSED / M9 INCOMING; red_team_counter=0 |
| AC.M8H.6 | SESSION_LOG M8-H-S1 appended (full M8 arc summary) |
| AC.M8H.7 | CAPABILITY_MANIFEST.json: M8_CLOSE entry added |
| AC.M8H.8 | MP.1 + MP.2 + MP.4 mirrors propagated to M8-CLOSED state |
| AC.M8H.9 | CLAUDECODE_BRIEF.md archived to 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M8_v1_0.md |
| AC.M8H.10 | All M8 exit criteria (MACRO_PLAN §M8 a–e) documented as MET in M8_CLOSE §1 |

---

## §5 — Global may_touch / must_not_touch (all M8 sessions)

```yaml
may_touch:
  - 08_CLASSICAL_CROSS_REFERENCE/**
  - 00_ARCHITECTURE/PHASE_M8_PLAN_v1_0.md
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  - 00_ARCHITECTURE/SESSION_LOG.md
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md
  - 00_ARCHITECTURE/briefs/**
  - 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md   # new file only; v3_0 is read-only
  - platform/supabase/migrations/046_*.sql
  - platform/supabase/migrations/047_*.sql
  - platform/supabase/migrations/048_*.sql
  - platform/lib/tools/classical_text_search.ts
  - platform/lib/tools/classical_attribution_lookup.ts
  - platform/lib/tools/index.ts
  - platform/lib/planner/query_plan_types.ts
  - platform/lib/pipeline/tool_fetch.ts
  - platform/lib/pipeline/compose_bundle.ts
  - platform/lib/disclosure/disclosure_filter.ts
  - platform/tests/classical/**
  - .geminirules
  - .gemini/project_state.md
  - CLAUDECODE_BRIEF.md  # status field + archive operation only

must_not_touch:
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_*.md
  - 01_FACTS_LAYER/LIFE_EVENT_LOG_*.md
  - 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md   # read-only; do not modify; v4_0 is the new file
  - 025_HOLISTIC_SYNTHESIS/UCN_*.md
  - 025_HOLISTIC_SYNTHESIS/CDLM_*.md
  - 025_HOLISTIC_SYNTHESIS/RM_*.md
  - 025_HOLISTIC_SYNTHESIS/CGM_*.md
  - 06_LEARNING_LAYER/PREDICTION_LEDGER/**
  - 06_LEARNING_LAYER/dbn/**
  - 07_PROSPECTIVE_TESTING/**
  - platform/supabase/migrations/001_*.sql  # through 045_*.sql — all prior migrations
  - platform/src/**   # except tool files already in may_touch
  - 09_MULTI_SCHOOL_TRIANGULATION/**  # not yet created; do not pre-build M9 infrastructure
```

---

## §6 — LLM Stack Constraint

NO Anthropic/Claude API calls in any M8 code.
Stack: Gemini → DeepSeek → NIM.
- Ingestion (non-critical): `gemini-2.5-flash-lite` or equivalent flash model
- Attribution engine LLM judge (critical): `gemini-2.5-pro` or `deepseek-v4-pro`
- Signal extraction (critical): `gemini-2.5-pro`
- Unit test mocks: free to use any mock/stub — no real API calls in tests

---

## §7 — Session-Open Handshake

Every M8 session emits SESSION_OPEN artifact per SESSION_OPEN_TEMPLATE_v1_0.md before any
tool call. Session IDs: M8-A-S1, M8-B-S1, M8-C-S1, M8-D-S1, M8-E-S1, M8-F-S1, M8-G-S1, M8-H-S1.
cowork_thread_name must match handshake session_id field.

---

## §8 — Sequencing and Risk Register

**Sequencing:** M8-A → M8-B → M8-C → M8-D → M8-E → M8-F → M8-G → M8-H (strictly serial).
E cannot start until B/C/D complete (needs corpus). F cannot start until E complete (needs attribution
pass results). G cannot start until E+F complete (tools need populated DB). H cannot start until G complete.

**Risk register (from MACRO_PLAN §M8, project-specific mitigations):**

| Risk | Mitigation |
|---|---|
| Classical corpora unavailable at source URL | Ingestion script logs HTTP errors; falls back to archive.org alternate URL; minimum viable: BPHS + Phaladeepika (tier 1 mandatory) |
| Translation accuracy variance | Multi-source cross-check in M8-H; native Sanskrit literacy as final arbiter; SIGNIFICANT_VARIANCE → confidence downgrade |
| Attribution ambiguity in BPHS compilation chapters (multiple attributed authors) | Explicit attribution_confidence flag per citation; derivation_notes captures ambiguity |
| Classical-claim-failure reputational surface | Disclosure stance pre-authorized (NAP.M8.2): findings published with attribution + source; §3.5.B tier applies |
| LLM attribution judge hallucination | chunk_id FK constraint ensures all attributions point to real text; cross-check: confidence ≥0.75 attributions reviewed in M8-H sample |
| Nadi texts copyright restriction | Only public-domain or CC-licensed editions ingested; R.G. Rao (archive.org) and R. Santhanam editions are widely reproduced; if unavailable, document gap in PROCUREMENT_MAP |

---

*End of PHASE_M8_PLAN_v1_0.md*

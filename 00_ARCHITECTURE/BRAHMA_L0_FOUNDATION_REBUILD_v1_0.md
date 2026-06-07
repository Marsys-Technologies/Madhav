---
artifact: BRAHMA_L0_FOUNDATION_REBUILD_v1_0.md
canonical_id: L0FR_MASTER_PLAN
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-07
governs: 6 parallel streams for L0 Brahma Jñāna full implementation
---

# Brahma L0 Foundation Rebuild — Master Plan v1.0

## §1 — Mission

Replace the scaffold-grade L0 Brahma Jñāna foundation with a real, comprehensive, production-quality dataset that downstream layers can stand on.

Today: 41 hardcoded text chunks, 55 hardcoded remedies, ephemeris partial, pañcāṅga location-locked to Bhubaneswar, no sūtravali, ontology stub.

After this arc: ~10,000 verse chunks across 15 classical texts with vector search, ~5,000-10,000 extracted sūtravali rules, ~500-1,000 curated remedies across 10 categories, ephemeris 1900-2150 for 9 bodies (~822k rows), pañcāṅga as on-demand service (location-aware, multi-chart-ready), Swiss Ephemeris as shared infrastructure layer for L0+L1+all-future-astronomical-compute.

## §2 — Locked architectural decisions (per native 2026-06-07)

**Naming + structure:**
- `brahmagyan.kalapancanga` is renamed/repurposed: **the ephemeris asset** keeps the name internally but `english_name` is corrected to "Graha Sphuṭa / Ephemeris" so the cockpit stops confusing it with pañcāṅga
- `brahmagyan.panchanga_almanac` is **dropped from the registry** — pañcāṅga becomes a service, not a stored asset
- `brahmagyan.shastra` (classical texts) expanded from 4 texts to **15 texts** (4 existing + 4 Tier 1 + 3 Tier 2 + 4 Tier 3)
- `brahmagyan.sutravali` (rules corpus) now has a real implementation: **LLM extraction from texts** using Vertex AI Gemini 2.5 Flash (per native — no acharya available for manual curation)
- `brahmagyan.upaya_kosha` extended from 55 hardcoded remedies to **500-1,000 across 10 categories**, including **carefully sourced tantric remedies** (per native — careful inclusion, not exclusion)
- `brahmagyan.sensitive_point_catalog` and `brahmagyan.samanvaya` (Concordance) — clarify English labels and confirm intent during Stream A
- `brahmagyan.text_index` — proper Vertex AI vector embedding pipeline (was deferred; now in scope)

**Architecture:**
- **Swiss Ephemeris is shared infrastructure** (per memory `reference_swiss_ephemeris_shared_layer`). `.se1` files bundled in EVERY Docker image that does astronomical computation: orchestrator, python-sidecar (pañcāṅga), pyhora-sidecar (L1 chart calc), any future astronomical writer. Master copy in `gs://madhav-ephemeris/`.
- **L0 is GLOBAL data**, not per-chart. Orchestrator gains `--global-build` mode parallel to existing `--run-id` per-chart mode.
- **Pañcāṅga on-demand service** computes (lat, lon, date) → five limbs + sunrise/sunset. Per-chart cache in `chart_panchanga_cache` table. No bulk location-locked pre-compute.
- **Vertex AI** for everything LLM (per memory `feedback_llm_model_selection` — Anthropic banned; Gemini 2.5 Flash for bulk work, Gemini 2.5 Flash-Lite where margins matter).

## §3 — Classical text corpus (15 texts, specific editions)

**Tier 1 — Foundational (essential, full ingestion):**

| # | Text | Edition | Verses | License |
|---|---|---|---|---|
| 1 | Brihat Parashara Hora Shastra (BPHS) | R. Santhanam (Ranjan Publications, 1984) | ~2,000 | public domain (translation derivative) |
| 2 | Phaladeepika | S.S. Sareen | ~800 | public domain |
| 3 | Jataka Parijata | G.S. Kapoor | ~600 | public domain |
| 4 | Uttara Kalamrita | R. Santhanam | ~500 | public domain |
| 5 | Brihat Jataka (Varahamihira) | B. Suryanarain Rao + N.N. Sharma (cross-validated) | ~407 | public domain |
| 6 | Saravali (Kalyana Varma) | R. Santhanam | ~3,750 | public domain |
| 7 | Hora Sara (Prithuyasas) | J.N. Bhasin | ~1,600 | public domain |
| 8 | Jaimini Sūtram | Sanjay Rath (Sagittarius Publications) | ~933 sūtras | check rights |

**Tier 2 — Predictive depth (full ingestion):**

| 9 | Sarvartha Chintamani | J.N. Bhasin | ~1,500 | public domain |
| 10 | Tajaka Neelakanthi | Sanjay Rath + sourced Sanskrit | ~600 | check rights |
| 11 | Brihat Samhita | M. Ramakrishna Bhat (2 vols) | ~2,000 (106 chapters) | public domain |

**Tier 3 — Selective extracts:**

| 12 | Yavana Jataka | David Pingree (Harvard Oriental Series, critical edition) | core chapters of 8,000 | check rights (Harvard) |
| 13 | Bhrigu Samhita | published Sanskrit + English; selective | ~500 (selective) | source-by-source check |
| 14 | Muhurta Chintamani | G.C. Sharma | ~600 | public domain |
| 15 | Lal Kitab | B.M. Goel translation | ~300 | 20th c. — usable |

**Source strategy:**
- Internet Archive automated download for public-domain English translations (BPHS, Phaladeepika, Jataka Parijata, Uttara Kalamrita, Brihat Jataka classic editions, Saravali, Sarvartha Chintamani, Brihat Samhita, Muhurta Chintamani, Lal Kitab)
- Manual upload to GCS for editions not available on Internet Archive (Sanjay Rath publications, Pingree's Yavana Jataka, modern Hora Sara translations)
- Stream C's first phase produces a precise "what's available automated vs need-manual-upload" inventory for native action

**License + provenance:**
- Every text gets a row in `classical_texts` with: title, author, era, edition, translator, publisher, year, sha256 of source PDF, license, citation_format, source_url
- Every chunk references its text row via foreign key

**Multi-translation strategy:**
- Where multiple English translations exist (e.g., BPHS Santhanam vs other), ingest both; tag each chunk with `translator` and `tradition_school`. The LLM gets richer interpretive surface.

## §4 — Remedy corpus (Upāya-kośa) target structure

10 categories, ~500-1,000 total remedies:

| Category | Target count | Source pattern |
|---|---|---|
| Mantra prescriptions | 200-400 | Bīja + mūla per planet × deity × purpose |
| Gemstone prescriptions | 30-50 | Per planet + uparatna substitutes |
| Charity (dāna) rules | 50-100 | BPHS/Phaladeepika dāna chapters |
| Vrata (vow/fasting) | 30-50 | Per affliction with timing |
| Yantra prescriptions | 20-30 | Per planet × purpose |
| Pūjā/yajña rituals | 50-100 | Ritual remedies per deity |
| **Tantric remedies (careful inclusion)** | 50-100 | Dasamahavidya, Bagalamukhi, etc. — every row requires classical source verification; no late syncretic compendiums |
| Ayurvedic Jyotish | 30-50 | Herb prescriptions per planet |
| Vāstu corrections | 20-30 | When chart shows Vāstu doṣa |
| Behavior/karmic | 50-100 | Lifestyle remedies (sleeping side, habits, days) |

**Tantric remedy gate:** every tantric remedy row must include: source_text + source_chapter + source_verse + classical attestation. Rows without all four go to `remedy_review_queue` for later acharya validation, NOT into `brahma_remedy_corpus`. This implements native's "careful inclusion."

## §5 — Sūtravali extraction methodology

LLM extraction via Vertex AI Gemini 2.5 Flash (per native's cost ceiling).

**Multi-pass pipeline:**

1. **Pass 1 — Candidate extraction (Gemini 2.5 Flash):**
   For each verse chunk, prompt the LLM: "Extract any sūtra-form rule(s) of the form `IF <condition> THEN <prediction>` from this verse." Output: 0-3 candidate rules per chunk with confidence score.

2. **Pass 2 — Quality scoring (Gemini 2.5 Flash, 5-criterion rubric):**
   - Sourced verse exists and matches (1.0/0.0)
   - Predicate is testable on a real chart (0.0-1.0)
   - Antecedent unambiguous (0.0-1.0)
   - No LLM hallucination (sources visible) (1.0/0.0)
   - No contradiction with prior rules in same text (0.0-1.0)
   - Combined score = mean. Rules ≥0.8 → `sutravali_rules` (live). Rules <0.8 → `sutravali_review` (parked).

3. **Pass 3 — Cross-text consolidation:**
   Identify duplicate rules across texts (same predicate, same prediction). Merge into single row with multi-text citations.

**Estimated output:** ~5,000-10,000 live rules + ~3,000 parked for review.

**Cost ceiling:** $20 LLM at most for the entire extraction pass (per native — Gemini 2.5 Flash or cheaper). Stream D respects a $50 Tier-3 budget.

## §6 — Stream topology

```
┌────────────────────────────────────────────────────────────┐
│  STREAM A — Foundation Infrastructure                       │
│  • GCS bucket gs://madhav-ephemeris/ + .se1 file upload     │
│  • Bundle .se1 into orchestrator + sidecar Dockerfiles      │
│  • Schema migrations (corpus extensions, classical_texts,   │
│    classical_text_chunks, brahma_remedy_corpus extensions,  │
│    sutravali_rules, sutravali_review, chart_panchanga_cache)│
│  • Orchestrator --global-build mode                          │
│  • Asset registry seed correction (drop panchanga_almanac,   │
│    update kalapancanga english_name, add new metadata)       │
│  • PyHora sidecar Dockerfile + ephemeris path config         │
│  • OPERATOR REVIEW GATE — native validates architecture      │
│  Budget: $300                                                │
└────────────────────┬────────────────────────────────────────┘
                     │ unblocks all
        ┌────────────┼────────────┬──────────────┬────────────┐
        │            │            │              │            │
   ┌────▼─────┐ ┌────▼──────┐ ┌──▼─────────┐ ┌──▼─────────┐ ┌─▼──────────┐
   │ STREAM B │ │ STREAM C  │ │ STREAM E   │ │ STREAM F   │ │ STREAM G   │
   │Ephemeris │ │Text       │ │Pañcāṅga    │ │Remedy      │ │Pyhora      │
   │1900-2150 │ │Ingestion  │ │Service     │ │Corpus      │ │Integration │
   │9 bodies  │ │15 texts   │ │On-demand   │ │500-1000    │ │L1 chart    │
   │~822k rows│ │~10k chunks│ │compute     │ │remedies    │ │calc smoke  │
   │Build cost│ │OCR + chunk│ │+ chart     │ │10 categs   │ │test        │
   │~$0.05    │ │Vertex AI  │ │cache       │ │Tantric     │ │Budget: $100│
   │Budget    │ │embeddings │ │Budget: $200│ │careful gate│ │            │
   │$100      │ │Budget: $500│ │            │ │Budget: $300│ │            │
   └──────────┘ └─────┬─────┘ └────────────┘ └────────────┘ └────────────┘
                     │ unblocks D
                ┌────▼──────┐
                │ STREAM D  │
                │Sūtravali  │
                │LLM extract│
                │Gemini Flash│
                │~5-10k rules│
                │5-criterion │
                │rubric      │
                │Budget: $200│
                └───────────┘

                     ↓ all 7 streams close

           OPERATOR REVIEW GATE — native validates corpus
           + first --global-build smoke test
           + first per-chart build smoke test
                     ↓
                  L0 SEALED
```

**Total budget cap: $1,700** (sum of stream budgets; Tier-3 catastrophic-runaway threshold).

**Estimated wall-clock:** 5-8 days autonomous, with two operator review gates (post-A, pre-seal).

## §7 — Per-stream acceptance criteria

**Stream A:**
- `.se1` files exist at `gs://madhav-ephemeris/se1/` (sha256 logged)
- Orchestrator Dockerfile bundles `.se1` to `/app/ephe/` (verified via `docker build --no-cache && docker run ... ls /app/ephe`)
- python-sidecar + pyhora-sidecar Dockerfiles bundle same
- Migrations applied: `sutravali_rules`, `sutravali_review`, `chart_panchanga_cache`, extended `brahma_remedy_corpus`, extended `classical_text_chunks`
- `--global-build` arg honored by orchestrator (smoke test: empty plan completes successfully)
- Asset registry seeded with corrected metadata
- Operator confirms architecture before proceeding

**Stream B:**
- `ephemeris_daily` has ≥820,000 rows for 1900-2150 × 9 bodies
- Spot-check native birth (1984-02-05) Sun = Capricorn 21°48'
- Spot-check Y2000 Sun at midnight UT = Sagittarius 9°53'
- Spot-check 2050-01-01 Saturn ≈ Pisces 27° (extrapolation correct)

**Stream C:**
- 15 text rows in `classical_texts` with full provenance
- ≥6,000 chunks in `classical_text_chunks` (Tier 1 + 2 fully ingested, Tier 3 partial)
- Every chunk has verse_ref, content (English minimum, Sanskrit where source allows), source_citation, content_sha256
- License + source_url logged per text
- Operator inventory checkpoint: list of texts that need manual upload posted to Smṛti for native action
- Vertex AI embeddings populated for every chunk (768-dim, `text-multilingual-embedding-002`)
- Vector similarity smoke test: "what does BPHS say about Mars in 7th house" returns ≥3 relevant chunks from BPHS

**Stream D:**
- ≥3,000 rules in `sutravali_rules` (live, score ≥0.8)
- Parked rules in `sutravali_review` (score <0.8, full audit trail)
- Each live rule has source_text + verse_ref + extraction_pass_log
- Operator review checkpoint: random sample of 50 live rules validated; <20% rejection rate = PASS

**Stream E:**
- `panchanga_engine.compute(lat, lon, date)` returns five limbs + sunrise/sunset
- For native birth date 1984-02-05 + Bhubaneswar: tithi=Shukla Tritiya, vāra=Ravivara, nakshatra=Purva Bhadrapada (matches Phase 4C reference)
- For Mumbai same date: slightly different tithi due to sunrise shift (proves location-awareness)
- `chart_panchanga_cache` table populated on first query per (chart, date_range)
- 73,414 Phase 4C Bhubaneswar rows MIGRATED into chart_panchanga_cache for native's chart (not lost)

**Stream F:**
- ≥500 rows in `brahma_remedy_corpus` across all 10 categories
- Tantric remedies: every row has source_text + source_chapter + source_verse + classical_attestation_text
- Remedies that fail tantric gate go to `remedy_review_queue` (auditable)
- Operator taste-check: random sample of 30 remedies; native validates ≥80% as acceptable

**Stream G:**
- pyhora-sidecar Docker image deployable to Cloud Run with `.se1` bundled
- PyHora smoke test: native chart positions computed (e.g., Moon nakshatra = Purva Bhadrapada Pada 1)
- Round-trip integration: cockpit click "Build L1.graha_sthana" → orchestrator invokes pyhora-sidecar → result written to ganita_positions for native's chart
- L1 chart facts validated against PyHora canonical output (no separate "JH parity" check per memory `feedback-no-jh-parity-anywhere`)

## §8 — Cost model (recap with refinements)

**One-time build cost** at Gemini 2.5 Flash pricing:

| Component | Cost |
|---|---|
| Ephemeris compute (Cloud Run Job) | $0.05 |
| Document AI OCR (6,000 pages × $0.0015) | $9 |
| Gemini 2.5 Flash chunking + LLM curation | $1.50 |
| Vertex AI embeddings (25M chars × $0.000025/1K) | $0.63 |
| Gemini 2.5 Flash for sūtravali extraction (multi-pass) | $8-15 |
| Remedy LLM-assisted curation | $0.05 |
| GCS uploads + Cloud Run compute (minor) | $1 |
| **Subtotal LLM + compute** | **~$25** |
| Dev iteration buffer (3x) | $50-75 |
| **TOTAL ONE-TIME** | **~$75-100** |

**Monthly recurring storage:**

| Component | Cost |
|---|---|
| GCS for PDFs (25 GB) | $0.50 |
| GCS for .se1 master (50 MB) | $0.001 |
| GCS for parsed chunk JSON cache (~500 MB) | $0.01 |
| Postgres delta (within existing instance) | $0 |
| pgvector embeddings index | $0 (in DB) |
| **TOTAL** | **~$0.50-0.60/mo** |

## §9 — Operator review gates

Three checkpoints where native sees output before the swarm continues:

**Gate 1 — Post-Stream A:**
- Architecture validated
- Sample of migrated schema reviewed
- .se1 bundling confirmed working
- Asset registry corrections approved
- **Native decision:** proceed with B+C+E+F+G OR adjust

**Gate 2 — Mid-Stream C (after first 3 texts ingested):**
- Native sees chunk quality on real text
- Confirms multi-translation approach makes sense
- Approves embedding model + index strategy
- Flags any text that needs different handling

**Gate 3 — Pre-seal (after all 7 streams close):**
- Smoke test of `--global-build` end-to-end
- Vector search quality check
- Sūtravali random sample audit
- Remedy taste-check
- Triggers the first real native per-chart build OR sends back to fix

## §10 — Output artifacts

After full execution + native seal:

- **15 classical texts** with ~10k chunks + embeddings — usable for Vimarśa (consult)
- **~5k live sūtravali rules** — usable for B.11 Whole-Chart-Read at L2+
- **~500 remedy corpus** with tantric tier — usable for upāya queries
- **Static ephemeris cache** (822k rows) — fast lookup for L1 onward
- **Pañcāṅga service** — usable for any chart, any location
- **Shared Swiss Ephemeris infrastructure** — usable for PyHora and any L1+ writer
- **--global-build mode** — orchestrator can rebuild L0 on demand
- **Cockpit-side** continues working (no client-facing change needed; the registry corrections happen on prod via migration apply)

After this seal, L1 Gaṇita has everything it needs to build chart facts for any native via PyHora.

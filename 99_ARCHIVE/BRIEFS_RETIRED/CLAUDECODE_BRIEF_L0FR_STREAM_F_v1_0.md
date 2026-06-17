---
artifact: CLAUDECODE_BRIEF_L0FR_STREAM_F_v1_0.md
stream: F — Remedy Corpus + Capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavL0FR-F
branch: feature/l0fr-stream-f-remedies
budget_cap_usd: 50
v1.0_note: Deterministic-first per memory feedback_deterministic_first_for_data_build (2026-06-07) — ZERO LLM use
---

# Stream F — Remedy Corpus (Deterministic-First, Zero LLM)

## §1 — Mission
Build 500+ remedy corpus across 10 categories from native-authored YAML files + Python loader. ZERO LLM use. Register 7 retrieval capabilities.

## §2 — Dependencies
Blocks on `state.yaml: gates.vimarsaka_a.status = pass`. Independent of other content streams.

## §3 — Scope

### Phase 1 — YAML corpus authoring
1. Author 10 YAML corpus files at `platform/python-sidecar/brahmagyan/remedy_corpus/`:
   - mantras.yaml, gemstones.yaml, charity.yaml, vrata.yaml, yantras.yaml, puja.yaml, tantric.yaml, ayurvedic.yaml, vastu.yaml, behavioral.yaml
2. Source remedies from classical text passages already in `classical_text_chunks` (post Stream C). For each remedy:
   - Read the source verse from classical_text_chunks
   - Hand-encode the remedy into the YAML schema
   - This is curation work — Python regex from text chunks where possible; native review where needed
3. Each YAML row schema:
   ```yaml
   - remedy_id: <deterministic hash>
     planet: <Sun|Moon|Mars|...>
     domain: <career|health|marriage|wealth|spirituality|...>
     category: <one of 10>
     deity: <if applicable>
     remedy_text: <plain English; HAND-AUTHORED>
     mantra_sanskrit: <if mantra category; HAND-AUTHORED from source>
     mantra_transliteration: <if mantra>
     ingredients_jsonb: { ... }  # if ayurvedic/vastu
     timing_rules_jsonb: { ... }
     cost_tier: accessible | moderate | elaborate
     contraindications: <text>
     source_text: <text_id>
     source_chapter: <text>
     source_verse: <text>
     classical_attestation_text: <quoted Sanskrit + English of source>
   ```

### Phase 2 — Python regex-assisted YAML scaffolding (no LLM)
4. Author `platform/python-sidecar/brahmagyan/l0_remedy_yaml_scaffolder.py`:
   - For each classical text chapter known to contain remedies (BPHS Ch. 91-94 on upayas, Phaladeepika Ch. 27 on remedies, etc.):
   - Use regex patterns to find passages mentioning "remedy", "upaya", "mantra", "yantra", "dāna", "vrata":
     ```python
     REMEDY_TRIGGERS = [r'remed(y|ies)', r'upaya', r'mantra', r'yantra', r'd[āa]na', r'charity', r'vrata', r'fasting', r'gemstone', r'gem', r'puja', r'worship', r'yagna']
     ```
   - For each match: extract the verse + surrounding context
   - Pre-fill a YAML stub with: source_text, source_chapter, source_verse, classical_attestation_text auto-filled; remedy_text + category + planet left BLANK for native to author
5. Native authors the blanks (one-time work, persistent), committing the filled YAML files to the repo. Stream F's Conductor pauses here for the YAML files to exist.

### Phase 3 — Tantric careful-inclusion gate (Python only)
6. For each row in tantric.yaml:
   - Verify source_text in source_data §5 acceptable tantric source list (regex match)
   - Verify all four columns present: source_text, source_chapter, source_verse, classical_attestation_text
   - If any column missing → flag to `remedy_review_queue`, NOT brahma_remedy_corpus

### Phase 4 — Python loader
7. Author `l0_remedy_loader.py`:
   ```python
   def load_remedies(yaml_dir: Path) -> int:
     for yaml_path in yaml_dir.glob('*.yaml'):
       with open(yaml_path) as f:
         data = yaml.safe_load(f)
       for row in data:
         # Tantric gate
         if row['category'] == 'tantric':
           if not is_acceptable_tantric_source(row['source_text']):
             insert_to_review_queue(row, reason='tantric source not in acceptable list')
             continue
           if not all(row.get(k) for k in ['source_text', 'source_chapter', 'source_verse', 'classical_attestation_text']):
             insert_to_review_queue(row, reason='tantric row missing source columns')
             continue
         # Insert
         insert_to_corpus(row)
   ```
8. Run loader; insert to `brahma_remedy_corpus` (or `remedy_review_queue` if rejected)

### Capability registrations (handlers = SQL only, no LLM)
9. Tools:
    - `query_remedies(planet, domain, category, top_k)` → SQL filter
    - `query_remedies_for_chart(chart_id, affliction)` → SQL with chart context
    - `list_remedies_by_category(category)` → SQL
    - `read_remedy(remedy_id)` → SQL lookup
    - `query_tantric_remedies(deity, purpose)` → SQL filter on tantric category
10. Resource:
    - `marsys://resource/remedies/by-planet/<planet>` → SQL dump
11. Prompt:
    - `marsys://prompt/remedy-recommendation` → static Python template

### Smoke tests (Python-only)
12. `query_remedies(planet='Saturn', domain='career', top_k=5)` returns ≥3 (lowered from ≥5 per deterministic-first trade-off)
13. `query_tantric_remedies(deity='Bagalamukhi')` returns rows where every row has source columns NOT NULL (SQL check)

## §5 — Acceptance criteria (programmatic, Python+SQL only)
- `SELECT count(*) FROM brahma_remedy_corpus ≥ 200` (lowered from 500 per deterministic-first trade-off; can grow post-seal via additional YAML authoring)
- `SELECT count(DISTINCT category) FROM brahma_remedy_corpus ≥ 8` (8 of 10 categories minimum; tantric/yantra may be sparse initially)
- Every tantric row has source_text + source_chapter + source_verse + classical_attestation_text (NOT NULL, SQL-checkable)
- 7 capabilities registered; parity_check passes

## §6 — Budget
Tier-3 cap $50 (was $350). NO LLM USE. Only Python compute + minor Vertex AI cost for Vimarśaka structural checks.

## §7-§8 — Final summary
```yaml
---FINAL_SUMMARY---
stream: F
status: READY_FOR_REVIEW
remedies_count: <N>  # expected 200-500 per deterministic constraint
categories_covered: <N>/10
tantric_review_queue_count: <N>
extraction_method: yaml_curation + python_loader
capabilities_registered: 7/7
budget_spent_usd: <N>
deterministic_compliance: 100% Python+YAML+SQL; ZERO LLM
quality_compromise_accepted: native ratified 2026-06-07
---END_FINAL_SUMMARY---
```

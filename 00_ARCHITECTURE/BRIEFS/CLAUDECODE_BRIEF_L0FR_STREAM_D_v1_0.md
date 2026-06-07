---
artifact: CLAUDECODE_BRIEF_L0FR_STREAM_D_v1_0.md
stream: D — Sūtravali Pattern Extraction + Capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavL0FR-D
branch: feature/l0fr-stream-d-sutravali
budget_cap_usd: 50
tier3_escalation_usd: 5000
v1.0_note: Deterministic-first per memory feedback_deterministic_first_for_data_build (2026-06-07) — ZERO LLM use
---

# Stream D — Sūtravali Pattern Extraction (Deterministic-First, Zero LLM)

## §0-§0.5
Master plan, source data, Vimarśaka specs required reading.

**Deterministic-first principle:** Pure Python regex pattern extraction. Rules not matching templates are SKIPPED (not LLM-completed). SQL-only quality checks. Python string similarity for dedup. NATIVE QUALITY TRADE-OFF: expected output is 1,000-2,000 templated rules instead of 5,000-10,000 — acceptable for full determinism.

## §1 — Mission
Extract sūtra-form rules from `classical_text_chunks` using Python regex patterns. Register 6 retrieval capabilities. No LLM at any stage.

## §2 — Dependencies
Blocks on `state.yaml: gates.vimarsaka_c.status = midway_pass`.

## §3 — Scope

### Phase 1 — Pattern library (Python only)
1. Author `platform/python-sidecar/brahmagyan/l0_sutravali_extractor.py` with curated regex patterns:
   ```python
   # Templated patterns commonly found in classical Jyotish English translations.
   # Add patterns as classical phrasings are discovered; new patterns extend coverage deterministically.
   
   PLANET_NAMES = r'(?P<planet>Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|Ravi|Chandra|Mangal|Budh|Guru|Shukra|Shani|Surya)'
   HOUSE_NUMBER = r'(?P<house>1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)'
   OUTCOME_VERB = r'(?P<verb>gives|causes|leads to|brings|results in|produces|makes|denotes|indicates|signifies)'
   
   SUTRA_PATTERNS = [
     # "Saturn in 7th house gives X" / "Saturn in the 7th house leads to X"
     rf'{PLANET_NAMES}\s+in\s+(?:the\s+)?{HOUSE_NUMBER}\s+house\s+{OUTCOME_VERB}\s+(?P<outcome>[^.]+\.)',
     # "When Saturn is in the 7th house, X"
     rf'When\s+{PLANET_NAMES}\s+is\s+in\s+(?:the\s+)?{HOUSE_NUMBER}\s+house[,;]\s+(?P<outcome>[^.]+\.)',
     # "Saturn occupying 7th house [makes] X"
     rf'{PLANET_NAMES}\s+occupying\s+(?:the\s+)?{HOUSE_NUMBER}\s+house\s+{OUTCOME_VERB}\s+(?P<outcome>[^.]+\.)',
     # "If Saturn is in the 7th house, X"
     rf'If\s+{PLANET_NAMES}\s+is\s+in\s+(?:the\s+)?{HOUSE_NUMBER}\s+house[,;]\s+(?P<outcome>[^.]+\.)',
     # "Saturn placed in 7th house gives X"
     rf'{PLANET_NAMES}\s+placed\s+in\s+(?:the\s+)?{HOUSE_NUMBER}\s+house\s+{OUTCOME_VERB}\s+(?P<outcome>[^.]+\.)',
     # "The native born with Saturn in 7th house [verb] X"
     rf'(?:The\s+)?native\s+born\s+with\s+{PLANET_NAMES}\s+in\s+(?:the\s+)?{HOUSE_NUMBER}\s+house\s+{OUTCOME_VERB}\s+(?P<outcome>[^.]+\.)',
     # Lord-of-house patterns: "Lord of 10th in 7th gives X"
     rf'Lord\s+of\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMBER})\s+in\s+(?:the\s+)?{HOUSE_NUMBER}\s+{OUTCOME_VERB}\s+(?P<outcome>[^.]+\.)',
     # Aspect patterns: "Saturn aspects Mars" / "Saturn aspecting Mars from X"
     rf'{PLANET_NAMES}\s+aspect(?:s|ing)\s+(?P<aspected>Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\s+(?:from\s+(?:the\s+)?{HOUSE_NUMBER}\s+house\s+)?{OUTCOME_VERB}\s+(?P<outcome>[^.]+\.)',
     # Sign placement: "Mars in Aries gives X"
     rf'{PLANET_NAMES}\s+in\s+(?P<sign>Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces|Mesha|Vrishabha|Mithuna|Karka|Simha|Kanya|Tula|Vrischika|Dhanus|Makara|Kumbha|Meena)\s+{OUTCOME_VERB}\s+(?P<outcome>[^.]+\.)',
     # Add more patterns as native discovers them post-seal
   ]
   
   def extract_rules(chunk_text: str, chunk_id: str, text_id: str, verse_ref: str) -> list[Rule]:
     rules = []
     for pattern in SUTRA_PATTERNS:
       for match in re.finditer(pattern, chunk_text, re.IGNORECASE):
         rules.append(Rule(
           rule_id=hashlib.sha256(f"{chunk_id}:{match.group(0)}".encode()).hexdigest()[:16],
           text_id=text_id, verse_ref=verse_ref,
           antecedent_jsonb=normalize_antecedent(match),
           predicate_jsonb=normalize_predicate(match),
           prediction_jsonb=normalize_prediction(match.group('outcome')),
           confidence=1.0,  # deterministic extraction = full confidence
           extracted_by='python_regex',
           extraction_pass_log={'pattern': pattern, 'match_text': match.group(0)},
         ))
     return rules
   ```
   
2. **Rules NOT matching any pattern are SKIPPED** — do not LLM-fallback. Acceptable per native deterministic-first decision.

### Phase 2 — Deterministic quality scoring (SQL + Python only)
3. For each extracted rule, run ONLY deterministic checks:
   - **Check 1 (SQL):** `verse_ref` exists in `classical_text_chunks` → boolean
   - **Check 2 (SQL):** Predicate's planet/house/sign tokens exist in `brahma_ontology` (from Stream A) → boolean
   - **Check 3 (regex):** Outcome text contains at least one noun (heuristic: word lookup against a small noun list) → boolean
4. ALL three deterministic checks must pass → insert into `sutravali_rules`
5. Any check fails → insert into `sutravali_review` with rejection_reason

### Phase 3 — Deterministic deduplication (Python only)
6. Exact dedup: hash on (planet, house, outcome_first_5_words) tuple; drop exact duplicates
7. Fuzzy dedup using Python `Levenshtein` distance:
   - Compute Levenshtein ratio between rule text pairs
   - ratio ≥ 0.85 → duplicates; keep the one with more source citations
8. Note: this misses semantic dedups ("Saturn in 7th" vs "Śani in saptama"). Acceptable per quality trade-off.

### Capability registrations (handlers = SQL only, no LLM)
9. Tools:
   - `query_rules(antecedent_pattern)` → SQL on sutravali_rules.antecedent_jsonb
   - `query_rules_for_planet(body, house=null)` → SQL filter
   - `read_rule(rule_id)` → SQL lookup
   - `list_rules_by_text(text_id)` → SQL filter
10. Resources:
    - `marsys://resource/sutravali/all-by-planet/<planet>` → SQL dump
    - `marsys://resource/sutravali/all-by-house/<n>` → SQL dump

### Smoke tests (Python-only)
11. `query_rules_for_planet('Saturn', house=7)` returns ≥3 rules (lower threshold than v1.0 §10 due to deterministic-first trade-off)
12. Each rule has source_text + verse_ref NOT NULL (validated by SQL)

## §5 — Acceptance criteria (programmatic, Python+SQL only)
- `SELECT count(*) FROM sutravali_rules ≥ 800` (lowered from 3000 per deterministic-first trade-off)
- `SELECT count(*) FROM sutravali_review ≥ 100` (some rules parked is healthy)
- Every live rule has source_text + verse_ref + extraction_pass_log (NOT NULL, SQL-checkable)
- 6 capabilities registered; parity_check passes

## §6 — Budget
Tier-3 cap $50 (was $250). NO LLM USE. Costs are pure compute (Cloud Run Job): <$1.

## §7-§8 — Final summary
```yaml
---FINAL_SUMMARY---
stream: D
status: READY_FOR_REVIEW
live_rules: <N>  # expected 800-2000 per deterministic constraint
parked_rules: <N>
extraction_method: pure_python_regex
patterns_tried: <N>
extraction_coverage_pct: <0-100>  # what % of chunks matched at least one pattern
capabilities_registered: 6/6
budget_spent_usd: <N>
deterministic_compliance: 100% Python + SQL; ZERO LLM
quality_compromise_accepted: native ratified 2026-06-07
---END_FINAL_SUMMARY---
```

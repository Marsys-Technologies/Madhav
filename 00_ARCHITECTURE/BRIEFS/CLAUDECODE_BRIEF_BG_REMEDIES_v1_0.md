---
artifact: CLAUDECODE_BRIEF_BG_REMEDIES_v1_0
canonical_id: L0_BG_REMEDIES_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_remedies writer (classical remedy corpus)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 800  # brahma_remedy_corpus rows
dependencies: [bg_ontology, bg_doshas]
llm_cost: $0  # v1.1 removed the LLM YAML scaffolder; native-authored YAML + deterministic matrix + corpus sweep
document_number: 9 of 15
---

# bg_remedies — Writer Brief (classical remedy corpus)

> **The remedy corpus.** Each row is a classical prescription (mantra / yantra / gemstone / charity / vrata / puja / homa / tantric / ayurvedic / vastu / behavioral) for an affliction or goal, with classical attestation. The existing corpus has ~200; this brief expands to ≥800 via a deterministic per-planet × per-category matrix + targeted classical sweeps (BPHS Ch.91-94, Phaladeepika Ch.27, Lal Kitab), with the tantric careful-inclusion gate. ZERO LLM — v1.1 removed the LLM YAML scaffolder; remedies are native-authored YAML + deterministic matrix expansion.

## §0 — Asset summary

- **Asset ID:** `bg_remedies`. **Backing:** `brahma_remedy_corpus`. **Scope:** `global`. **Tier:** 3.
- **Target floor:** **≥800 remedies** (design §3.7 says 800-1500; existing ~200).
- **Source category:** embedded classical data (per-planet matrix + classical-text sweep). `l0_remedy_corpus.py` exists (~200 remedies, `VOLUME_FLOOR=50`, `seed_remedy_corpus()`); EXTEND it.

## §1 — Schema reference

`brahma_remedy_corpus` (base columns + migration 081/177 ALTERs — confirm with `\d brahma_remedy_corpus`):

```
brahma_remedy_corpus ( remedy_id (PK), planet, domain, remedy_type, prescription_text,
  mantra_text, gemstone, charity_action, day_of_week, color_associated, confidence,
  source_canonical_id, source_citation, classical_ref,
  category, deity, mantra_sanskrit, mantra_transliteration, ingredients_jsonb,
  timing_rules_jsonb, cost_tier CHECK∈{free,low,medium,high}, contraindications,
  classical_attestation_text,                         -- migration 081
  scaffold_status DEFAULT 'live' CHECK∈{live,review,rejected} )  -- migration 177
```

> **remedy_type vocabulary reconciliation (REQUIRED):** the existing `l0_remedy_corpus.py` uses `remedy_type` values `mantra/gemstone/charity/fasting/ritual`. The bg_ontology `remedy_type` class (Doc 5 §3.4) uses `mantra/yantra/gemstone/charity/vrata/puja/japa/homa/tantric/ayurvedic/vastu/behavioral`. **Map the existing values** (`fasting`→`vrata`, `ritual`→`puja`) and migrate existing rows, OR add `fasting`/`ritual` as ontology synonyms. Author this mapping explicitly; every `remedy_type` MUST resolve to a `remedy_type` ontology entry (§5).

## §2 — Source references

| Remedy family | Source |
|---|---|
| Navagraha mantras (beej + stotra) | BPHS Ch.91-94 (Upaya-adhyaya); Mantra Mahodadhi (manual upload) |
| Gemstones (ratna) per planet | classical ratna-shastra; Phaladeepika |
| Charity (dana) per planet | BPHS Ch.91-94 |
| Vrata / fasting per planet/day | classical tradition |
| Lal Kitab remedies | Lal Kitab (ingested as text 15) |
| Tantric remedies | ONLY the L0FR-approved source list (`L0FR_SOURCE_DATA_v1_0.md §168-181`) — careful-inclusion gate |

## §3 — Embedded content — the deterministic matrix + sweeps

Author into `l0_remedy_corpus.py` (extend `REMEDIES`). Three deterministic sources sum to ≥800:

### §3.1 — Per-planet × per-category matrix (~9 × 11 × ~3 ≈ 300)

```python
# For each of 9 grahas × the core remedy categories, author the classically-attested remedy(ies).
# Example for Saturn (each cell is a real, attested prescription — NOT invented):
PLANET_REMEDY_MATRIX = {
  "saturn": {
    "mantra": [{"mantra_sanskrit":"ॐ शं शनैश्चराय नमः","mantra_transliteration":"Om Sham Shanaischaraya Namah",
                "prescription_text":"Recite the Saturn beej mantra 23,000 times (or 108×/day on Saturdays).",
                "deity":"Shani","day_of_week":"Saturday","color_associated":"black/dark blue",
                "source_citation":"BPHS Ch.91-94","classical_ref":"Upaya-adhyaya","cost_tier":"free"}],
    "gemstone": [{"gemstone":"Blue Sapphire (Neelam)","prescription_text":"Wear a tested blue sapphire in iron/panchdhatu on the middle finger, Saturday, after testing.",
                  "contraindications":"Test for 3 days first; not for everyone — only if Saturn is a functional benefit.",
                  "source_citation":"classical ratna-shastra","cost_tier":"high"}],
    "charity": [{"charity_action":"Donate black sesame, iron, mustard oil, black cloth to the needy on Saturday.",
                 "prescription_text":"Saturday charity to laborers/the elderly.","source_citation":"BPHS Ch.91-94","cost_tier":"low"}],
    "vrata": [{"prescription_text":"Observe a Saturday fast (one meal, no salt) for 7/11 Saturdays.","source_citation":"classical tradition","cost_tier":"free"}],
    # ... yantra, puja, homa, behavioral cells for Saturn.
  },
  # ... repeat for sun, moon, mars, mercury, jupiter, venus, rahu, ketu — each with its
  #     attested beej mantra, gemstone, charity items, color, day, fast.  ~9×8 cells × variants ≈ 300.
}
```

> The navagraha beej mantras, gemstones, charity items, colors, days are FIXED classical correspondences (every textbook agrees). The executor fills all 9 planets' cells from this standard table — transcription, not invention.

### §3.2 — Dosha-linked remedies (~100) — cross-link to bg_doshas

For each dosha in `brahma_dosha_catalog` (Doc 13), author its classical remedy(ies) and set the back-link. E.g. Manglik → Kumbh Vivah / Mangal puja / Hanuman worship; Kala Sarpa → Nag puja / Rahu-Ketu shanti; Pitru dosha → Tarpan / Gaya shraddha; Sade Sati → Hanuman Chalisa / Shani mantra. Each remedy row references the dosha; the dosha's `associated_remedies[]` is populated here (the back-link bg_doshas Doc 13 deferred).

### §3.3 — Classical-text sweep (~400) — from ingested corpus

Deterministic extraction (like bg_rules) of remedy statements from `bg_texts` chunks where a remedy marker appears (`mantra|yantra|dāna|donate|gemstone|fast|vrata|wear|recite|worship`): each match → a remedy row with `prescription_text` = the verse clause, `source_chunk_ids`/`source_citation` = the chunk, `scaffold_status='review'` for native confirmation (then promoted to 'live'). This depends on bg_texts. Lal Kitab (text 15) is especially remedy-dense and structured (remedy-per-affliction).

> **Tantric gate (design §3.7 lever 7):** any `remedy_type='tantric'` row MUST trace to the L0FR-approved source list. The writer REJECTS (scaffold_status='rejected') any tantric remedy whose source is not on the approved list. Strictly enforced.

> **Floor accounting:** matrix (~300) + dosha-linked (~100) + corpus sweep (~400) = **~800 ≥ floor**. All attested; the sweep rows are chunk-cited.

## §4 — Writer implementation

`pipeline/orchestrator/writers/bg_remedies.py` (`@register('bg_remedies')`) delegating to an extended `seed_remedy_corpus()`. Deterministic `remedy_id` from `(planet, remedy_type, sha256(prescription_text))`. `ON CONFLICT (remedy_id) DO NOTHING`. Every row: non-null `source_citation` OR `source_chunk_ids`; `scaffold_status` set; `remedy_type` mapped to the ontology vocabulary (§1).

## §5 — FK validation

- `remedy_type` MUST resolve in `brahma_ontology` (entity_class='remedy_type') → **depends_on bg_ontology**.
- `planet` MUST resolve in `brahma_ontology` (entity_class='planet').
- dosha-linked remedies reference `brahma_dosha_catalog` → **depends_on bg_doshas**.
- corpus-sweep rows' `source_chunk_ids` resolve in `classical_text_chunks` → (soft) depends_on bg_texts for §3.3.
- **depends_on:** `UPDATE asset_registry SET depends_on = ARRAY['bg_ontology','bg_doshas']::text[] WHERE asset_id='bg_remedies';` (the §3.3 sweep additionally wants bg_texts; if the executor runs the sweep, add 'bg_texts').

## §6 — Unit tests

`test_bg_remedies.py`: (1) ≥800 live remedies (`scaffold_status='live'`); (2) every row source-cited; (3) every `remedy_type` ∈ ontology remedy_type class; (4) every tantric row traces to the approved source list (else scaffold_status='rejected'); (5) all 9 grahas have ≥1 mantra + ≥1 gemstone + ≥1 charity; (6) idempotent; (7) dosha-linked remedies populate the referenced dosha's `associated_remedies`.

## §7 — Vimarśaka check

APPROVE iff: ≥800 live remedies; all source-cited; remedy_type vocabulary resolved; tantric gate enforced (zero un-sourced tantric live rows); per-planet coverage complete; idempotent.

## §8 — Hard stops + scope discipline

- Padding to 800 with invented prescriptions → STOP; the matrix + dosha-links + corpus sweep reach 800 from attested sources. Report any shortfall.
- A tantric remedy can't be traced to the approved list → scaffold_status='rejected', never 'live'. Non-negotiable.
- remedy_type vocabulary mismatch left unreconciled → STOP; map to the ontology vocabulary first (§1).
- Do NOT use an LLM scaffolder (v1.1 removed it). Corpus-sweep rows go to `scaffold_status='review'` for native promotion, not auto-live, unless the marker match is unambiguous.
- Out of scope: per-chart remedy recommendation (L1); the dosha catalog itself (Doc 13).

---

*End of bg_remedies brief (Document 9 of 15).*

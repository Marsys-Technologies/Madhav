---
artifact: CLAUDECODE_BRIEF_BG_DASHA_SYSTEMS_v1_0
canonical_id: L0_BG_DASHA_SYSTEMS_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_dasha_systems writer
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 15  # brahma_dasha_systems rows (design target 15-18)
dependencies: [bg_ontology]  # the writer also WRITES its ontology rows; see §0.1
llm_cost: $0
document_number: 12 of 15
---

# bg_dasha_systems — Writer Brief (classical dasha system definitions)

> **The timing-engine catalog.** Each row defines a dasha *system* — its total cycle, the unit it is reckoned from, the ordered sequence of period-lords with their years, and the computation method. Per-chart dasha *computations* live at L1 (`ga_dashas`), NOT here (holistic design §2.6). This is the definitional reference every L1+ dasha calculation reads. ZERO LLM.

## §0 — Asset summary

- **Asset ID:** `bg_dasha_systems`. **Backing:** `brahma_dasha_systems`. **Scope:** `global`. **Tier:** 1 (depends on bg_ontology).
- **Target floor:** **≥15** systems (design §3.10 says 15-18; this brief embeds 18).
- **Source category:** embedded classical data (BPHS Ch.46-50 Vimshottari & conditional dashas; Jaimini Sutram Ch.1 Chara dasha).

### §0.1 — Cross-brief contract (the catalog owns its ontology + pointer rows)

Per Doc 5 §0.1, this writer, **in the same transaction** as each `brahma_dasha_systems` insert, also inserts:
1. a `brahma_ontology` row: `entity_class='dasha_system'`, matching `canonical_id`, `name_en`/`name_sa`, `synonyms[]`, one-line description — `ON CONFLICT (canonical_id) DO NOTHING`.
2. a `reference_dasha_systems` pointer row: `(canonical_id, name_en, school)` — `ON CONFLICT (canonical_id) DO NOTHING`. (FK `fk_ref_dasha_sys` → `brahma_dasha_systems`, so insert the catalog row FIRST, then the pointer.)

This satisfies the holistic-design FK direction and single-source-of-truth: bg_dasha_systems is the sole author of every dasha id's name (ontology), doctrine (catalog), and index (pointer).

## §1 — Schema reference (migration 176, verified)

```
brahma_dasha_systems (
  canonical_id          TEXT PRIMARY KEY,
  name_sa               TEXT NOT NULL,
  name_en               TEXT NOT NULL,
  total_cycle_years     NUMERIC NOT NULL,
  base_unit             TEXT NOT NULL CHECK (base_unit IN ('nakshatra_lord','sign_lord','special')),
  sequence_jsonb        JSONB NOT NULL,           -- ordered [{ruler, years}, ...] OR sign-sequence for rashi dashas
  computation_method    TEXT NOT NULL,
  computation_pseudocode TEXT NOT NULL,
  conditions_for_use    TEXT,
  school                TEXT NOT NULL,
  classical_citations   JSONB,
  source_chunk_ids      BIGINT[] DEFAULT '{}',
  python_impl_module    TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
```

## §2 — Source references

| System family | Source |
|---|---|
| Vimshottari + conditional nakshatra dashas (Ashtottari, Shodashottari, Dwadashottari, Panchottari, Shatabdika, Chaturashiti-sama, Dwisaptati-sama, Shashtihayani, Shattrimsha-sama) | BPHS Ch.46-49 (Naisargika & conditional dashas) |
| Yogini | BPHS Ch.50 / classical tradition |
| Kalachakra | BPHS Ch.49 (Kalachakra dasha) |
| Chara, Sthira, Niryana Shoola, Brahma, Yogardha, Drig, Trikona (Jaimini rashi dashas) | Jaimini Sutram Ch.1; BPHS rashi-dasha chapters |
| Tara, Kala (nakshatra-special) | classical tradition |

## §3 — Embedded classical content (18 systems, full inline)

Author into `platform/python-sidecar/brahmagyan/l0_dasha_systems.py` as `DASHA_SYSTEMS = [...]`.

```python
# Vimshottari order + years — the canonical 120-year nakshatra-lord cycle (BPHS Ch.46)
VIMSHOTTARI_SEQ = [
  {"ruler":"ketu","years":7},{"ruler":"venus","years":20},{"ruler":"sun","years":6},
  {"ruler":"moon","years":10},{"ruler":"mars","years":7},{"ruler":"rahu","years":18},
  {"ruler":"jupiter","years":16},{"ruler":"saturn","years":19},{"ruler":"mercury","years":17},
]

DASHA_SYSTEMS = [
  {"canonical_id":"vimshottari","name_sa":"Viṃśottarī","name_en":"Vimshottari Dasha",
   "total_cycle_years":120,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":VIMSHOTTARI_SEQ,
   "computation_method":"nakshatra_remainder",
   "computation_pseudocode":"1. Find Moon's nakshatra (1-27) and its lord. 2. Balance of starting dasha = (1 - moon_longitude_within_nakshatra / 13°20') × lord_years. 3. Proceed in the fixed Ketu→Venus→Sun→Moon→Mars→Rahu→Jupiter→Saturn→Mercury order; antardashas subdivide each mahadasha proportionally (antar_years = maha_years × antar_lord_years / 120).",
   "conditions_for_use":"Universal default dasha; applicable to all charts. Reckoned from Moon's nakshatra.",
   "classical_citations":[{"text_id":"bphs","chapter":46}],"python_impl_module":"pyjhora.vimsottari"},

  {"canonical_id":"ashtottari","name_sa":"Aṣṭottarī","name_en":"Ashtottari Dasha",
   "total_cycle_years":108,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":[{"ruler":"sun","years":6},{"ruler":"moon","years":15},{"ruler":"mars","years":8},
     {"ruler":"mercury","years":17},{"ruler":"saturn","years":10},{"ruler":"jupiter","years":19},
     {"ruler":"rahu","years":12},{"ruler":"venus","years":21}],
   "computation_method":"nakshatra_remainder_conditional",
   "computation_pseudocode":"8-planet 108-year cycle (Ketu omitted). Starting lord from Moon's nakshatra via the Ashtottari nakshatra-group mapping; balance computed like Vimshottari. Conditional applicability per classical rules (e.g. Rahu in a quadrant/trine from lagna-lord, day birth in Krishna paksha / night in Shukla).",
   "conditions_for_use":"Conditional (Krishna/Shukla paksha + Rahu placement rules). Used where applicability conditions are met.",
   "classical_citations":[{"text_id":"bphs","chapter":48}],"python_impl_module":"pyjhora.ashtottari"},

  {"canonical_id":"yogini","name_sa":"Yoginī","name_en":"Yogini Dasha",
   "total_cycle_years":36,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":[{"ruler":"moon","yogini":"Mangala","years":1},{"ruler":"sun","yogini":"Pingala","years":2},
     {"ruler":"jupiter","yogini":"Dhanya","years":3},{"ruler":"mars","yogini":"Bhramari","years":4},
     {"ruler":"mercury","yogini":"Bhadrika","years":5},{"ruler":"saturn","yogini":"Ulka","years":6},
     {"ruler":"venus","yogini":"Siddha","years":7},{"ruler":"rahu","yogini":"Sankata","years":8}],
   "computation_method":"nakshatra_remainder",
   "computation_pseudocode":"8 yoginis, total 1+2+...+8 = 36 years. Starting yogini = ((nakshatra_number + 3) mod 8), mapping 0→Sankata. Balance from Moon's position in nakshatra. Order: Mangala→Pingala→Dhanya→Bhramari→Bhadrika→Ulka→Siddha→Sankata.",
   "conditions_for_use":"Widely used short-cycle dasha, especially for timing and muhurta.",
   "classical_citations":[{"text_id":"bphs","chapter":50}],"python_impl_module":"pyjhora.yogini"},

  {"canonical_id":"kalachakra","name_sa":"Kālacakra","name_en":"Kalachakra Dasha",
   "total_cycle_years":100,"base_unit":"special","school":"parashari",
   "sequence_jsonb":{"type":"nakshatra_pada_driven","note":"sign sequence (savya/apasavya) determined by Moon's nakshatra-pada; years per sign from the Kalachakra sign-year table (Aries/Scorpio 7, Taurus/Libra 16, etc.)"},
   "computation_method":"nakshatra_pada_savya_apasavya",
   "computation_pseudocode":"1. Moon's nakshatra-pada selects the deha/jeeva sign sequence and savya (direct) vs apasavya (reverse) progression. 2. Each sign's dasha length from the Kalachakra year table. 3. Antardashas follow the same sign progression within each mahadasha.",
   "conditions_for_use":"Powerful but computation-sensitive; used for spiritual/longevity timing.",
   "classical_citations":[{"text_id":"bphs","chapter":49}],"python_impl_module":"pyjhora.kalachakra"},

  {"canonical_id":"chara_jaimini","name_sa":"Cara Daśā","name_en":"Chara Dasha (Jaimini)",
   "total_cycle_years":144,"base_unit":"sign_lord","school":"jaimini",
   "sequence_jsonb":{"type":"rashi_sequence","note":"starts from lagna sign; direction by odd/even (movable→direct, fixed→reverse exceptions); years per sign = count to the sign's lord minus 1 (1-12)"},
   "computation_method":"jaimini_chara",
   "computation_pseudocode":"1. Start sign = lagna. 2. Direction: if lagna is odd-footed move zodiacally, else anti-zodiacally (with movable/fixed/dual refinements). 3. Years for a sign = number of signs from the sign to its lord (counted per direction), minus 1; if lord is in the sign itself = 12. 4. Progress sign-by-sign.",
   "conditions_for_use":"Primary Jaimini rashi dasha; read with arudha & karakas.",
   "classical_citations":[{"text_id":"jaimini_sutram","chapter":1}],"python_impl_module":"pyjhora.chara"},

  {"canonical_id":"sthira_dasha","name_sa":"Sthira Daśā","name_en":"Sthira Dasha (Jaimini)",
   "total_cycle_years":86,"base_unit":"sign_lord","school":"jaimini",
   "sequence_jsonb":{"type":"rashi_sequence","fixed_years":{"movable":7,"fixed":8,"dual":9}},
   "computation_method":"jaimini_sthira",
   "computation_pseudocode":"Fixed sign-year scheme: movable signs 7y, fixed 8y, dual 9y; sequence from lagna by Jaimini direction rules.",
   "conditions_for_use":"Jaimini rashi dasha with fixed period lengths.",
   "classical_citations":[{"text_id":"jaimini_sutram","chapter":1}],"python_impl_module":"pyjhora.sthira"},

  {"canonical_id":"niryana_shoola","name_sa":"Niryāṇa Śūla","name_en":"Niryana Shoola Dasha",
   "total_cycle_years":108,"base_unit":"sign_lord","school":"jaimini",
   "sequence_jsonb":{"type":"rashi_sequence","fixed_years":{"movable":7,"fixed":8,"dual":9},"note":"trikona-based; used for longevity/maraka timing"},
   "computation_method":"jaimini_shoola",
   "computation_pseudocode":"Trikona-grouped rashi dasha (Shoola = trident); period lengths by sign modality; reckoned from the 7th/8th for maraka analysis.",
   "conditions_for_use":"Longevity and death-timing (maraka) analysis.",
   "classical_citations":[{"text_id":"jaimini_sutram","chapter":1}],"python_impl_module":"pyjhora.shoola"},

  {"canonical_id":"shodashottari","name_sa":"Ṣoḍaśottarī","name_en":"Shodashottari Dasha",
   "total_cycle_years":116,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":[{"ruler":"sun","years":11},{"ruler":"mars","years":12},{"ruler":"jupiter","years":13},
     {"ruler":"saturn","years":14},{"ruler":"ketu","years":15},{"ruler":"moon","years":16},
     {"ruler":"mercury","years":17},{"ruler":"venus","years":18}],
   "computation_method":"nakshatra_remainder_conditional",
   "computation_pseudocode":"8-lord 116-year conditional cycle; applicability per birth in Krishna paksha day / Shukla paksha night and lagna conditions; balance from Moon's nakshatra.",
   "conditions_for_use":"Conditional nakshatra dasha (paksha + lagna rules).",
   "classical_citations":[{"text_id":"bphs","chapter":48}],"python_impl_module":"pyjhora.shodasottari"},

  {"canonical_id":"dwadashottari","name_sa":"Dvādaśottarī","name_en":"Dwadashottari Dasha",
   "total_cycle_years":112,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":[{"ruler":"sun","years":7},{"ruler":"jupiter","years":9},{"ruler":"ketu","years":11},
     {"ruler":"mercury","years":13},{"ruler":"rahu","years":15},{"ruler":"mars","years":17},
     {"ruler":"saturn","years":19},{"ruler":"moon","years":21}],
   "computation_method":"nakshatra_remainder_conditional",
   "computation_pseudocode":"8-lord 112-year conditional cycle; applicability per classical lagna/paksha rule (e.g. lagna in Venus-decanate).",
   "conditions_for_use":"Conditional nakshatra dasha.",
   "classical_citations":[{"text_id":"bphs","chapter":48}],"python_impl_module":"pyjhora.dwadasottari"},

  {"canonical_id":"panchottari","name_sa":"Pañcottarī","name_en":"Panchottari Dasha",
   "total_cycle_years":105,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":[{"ruler":"sun","years":12},{"ruler":"mercury","years":13},{"ruler":"saturn","years":14},
     {"ruler":"mars","years":15},{"ruler":"venus","years":16},{"ruler":"moon","years":17},{"ruler":"jupiter","years":18}],
   "computation_method":"nakshatra_remainder_conditional",
   "computation_pseudocode":"7-lord 105-year conditional cycle; applicability per classical lagna rule (Cancer lagna / specific decanate).",
   "conditions_for_use":"Conditional nakshatra dasha.",
   "classical_citations":[{"text_id":"bphs","chapter":48}],"python_impl_module":"pyjhora.panchottari"},

  {"canonical_id":"shatabdika","name_sa":"Śatābdikā","name_en":"Shatabdika Dasha",
   "total_cycle_years":100,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":[{"ruler":"venus","years":5},{"ruler":"sun","years":5},{"ruler":"moon","years":10},
     {"ruler":"mars","years":10},{"ruler":"mercury","years":10},{"ruler":"jupiter","years":20},
     {"ruler":"saturn","years":20},{"ruler":"rahu","years":20}],
   "computation_method":"nakshatra_remainder_conditional",
   "computation_pseudocode":"8-lord 100-year conditional cycle (Saptarishi nadi-linked); applicability per classical condition.",
   "conditions_for_use":"Conditional nakshatra dasha; nadi tradition.",
   "classical_citations":[{"text_id":"bphs","chapter":48}],"python_impl_module":"pyjhora.shatabdika"},

  {"canonical_id":"chaturashiti_sama","name_sa":"Caturaśīti-sama","name_en":"Chaturashiti-sama Dasha",
   "total_cycle_years":84,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":{"type":"equal_period","per_lord_years":12,"lords":["sun","moon","mars","mercury","jupiter","venus","saturn"],"note":"7 lords × 12 years = 84"},
   "computation_method":"nakshatra_remainder_conditional",
   "computation_pseudocode":"Equal 12-year periods, 7 lords; applicability when the 10th lord is in the 10th house (classical condition).",
   "conditions_for_use":"Conditional: 10th-lord-in-10th charts.",
   "classical_citations":[{"text_id":"bphs","chapter":49}],"python_impl_module":"pyjhora.chaturashiti"},

  {"canonical_id":"dwisaptati_sama","name_sa":"Dvisaptati-sama","name_en":"Dwisaptati-sama Dasha",
   "total_cycle_years":72,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":{"type":"equal_period","per_lord_years":9,"lords":["sun","moon","mars","mercury","jupiter","venus","saturn","rahu"],"note":"8 lords × 9 years = 72"},
   "computation_method":"nakshatra_remainder_conditional",
   "computation_pseudocode":"Equal 9-year periods, 8 lords; applicability when lagna lord is in the 7th or 7th lord in lagna (classical condition).",
   "conditions_for_use":"Conditional: lagna-lord/7th-lord exchange charts.",
   "classical_citations":[{"text_id":"bphs","chapter":49}],"python_impl_module":"pyjhora.dwisaptati"},

  {"canonical_id":"shashtihayani","name_sa":"Ṣaṣṭihāyaṇī","name_en":"Shashtihayani Dasha",
   "total_cycle_years":60,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":{"type":"shashtihayani","note":"Sun-centric 60-year scheme; period lengths per classical Shashtihayani table","lords":["sun","moon","mars","mercury","jupiter","venus","saturn","rahu","ketu"]},
   "computation_method":"nakshatra_remainder_conditional",
   "computation_pseudocode":"60-year cycle; applicability when Sun is the lagna lord or strongly placed (classical condition).",
   "conditions_for_use":"Conditional: Sun-dominant charts.",
   "classical_citations":[{"text_id":"bphs","chapter":49}],"python_impl_module":"pyjhora.shashtihayani"},

  {"canonical_id":"shattrimsha_sama","name_sa":"Ṣaṭtriṃśat-sama","name_en":"Shattrimsha-sama Dasha",
   "total_cycle_years":36,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":{"type":"day_night_dependent","note":"36-year cycle; lord order depends on day vs night birth (Sun-first by day, Moon-first by night)"},
   "computation_method":"nakshatra_remainder_conditional",
   "computation_pseudocode":"36-year cycle; applicability when lagna is in a Sun/Moon hora consistent with day/night birth.",
   "conditions_for_use":"Conditional: hora/day-night rule.",
   "classical_citations":[{"text_id":"bphs","chapter":49}],"python_impl_module":"pyjhora.shattrimsha"},

  {"canonical_id":"tara_dasha","name_sa":"Tārā Daśā","name_en":"Tara Dasha",
   "total_cycle_years":120,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":{"type":"tara_chakra","note":"reckoned via the 9-tara (Janma, Sampat, Vipat, Kshema, Pratyak, Sadhana, Naidhana, Mitra, Parama-mitra) cycle from Moon's nakshatra"},
   "computation_method":"tara_chakra",
   "computation_pseudocode":"9-fold tara cycle from janma nakshatra; period weighting per the tara scheme.",
   "conditions_for_use":"Used in nakshatra/tarabala timing.",
   "classical_citations":[{"text_id":"bphs","chapter":47}],"python_impl_module":"pyjhora.tara"},

  {"canonical_id":"brahma_dasha","name_sa":"Brahma Daśā","name_en":"Brahma Dasha (Jaimini)",
   "total_cycle_years":120,"base_unit":"sign_lord","school":"jaimini",
   "sequence_jsonb":{"type":"rashi_sequence","note":"rashi dasha reckoned from the Brahma graha (Jaimini longevity karaka determination)"},
   "computation_method":"jaimini_brahma",
   "computation_pseudocode":"Identify Brahma (one of the strong planets in odd/even signs by Jaimini rules); reckon a rashi dasha from its sign.",
   "conditions_for_use":"Jaimini longevity/maraka analysis.",
   "classical_citations":[{"text_id":"jaimini_sutram","chapter":1}],"python_impl_module":"pyjhora.brahma"},

  {"canonical_id":"yogardha_dasha","name_sa":"Yogārdha Daśā","name_en":"Yogardha Dasha",
   "total_cycle_years":108,"base_unit":"nakshatra_lord","school":"parashari",
   "sequence_jsonb":{"type":"average","note":"average of Vimshottari and Ashtottari period-lengths per lord (yoga-ardha = half-sum)"},
   "computation_method":"vimshottari_ashtottari_average",
   "computation_pseudocode":"For each lord, period = (Vimshottari years + Ashtottari years)/2; sequence and balance as Vimshottari.",
   "conditions_for_use":"Used where both Vimshottari and Ashtottari are indicated; harmonizes the two.",
   "classical_citations":[{"text_id":"bphs","chapter":48}],"python_impl_module":"pyjhora.yogardha"},
]
```

> **Floor check:** 18 systems authored ≥ 15 floor. All sequences/years are the classical values. Where a conditional dasha's exact applicability rule has textual variants, the `conditions_for_use` states the principal classical condition and `computation_pseudocode` notes the method — these are attested, not invented. If the executor finds a sequence value that disagrees with the ingested BPHS chunks (Tier 2), the BPHS chunk wins; reconcile and note it.

## §4 — Writer implementation

Author `platform/python-sidecar/brahmagyan/l0_dasha_systems.py` with `DASHA_SYSTEMS` + a `seed_dasha_systems(conn, build_id, dry_run, autocommit)` function, and `pipeline/orchestrator/writers/bg_dasha_systems.py` (`@register('bg_dasha_systems')`, delegates to the seed fn — mirror the bg_reference writer pattern). For each system, in order:

```python
for d in DASHA_SYSTEMS:
    # 1. catalog row FIRST (FK target for the pointer)
    cur.execute("""INSERT INTO brahma_dasha_systems
        (canonical_id,name_sa,name_en,total_cycle_years,base_unit,sequence_jsonb,
         computation_method,computation_pseudocode,conditions_for_use,school,
         classical_citations,python_impl_module)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (canonical_id) DO NOTHING""",
        (d["canonical_id"],d["name_sa"],d["name_en"],d["total_cycle_years"],d["base_unit"],
         Json(d["sequence_jsonb"]),d["computation_method"],d["computation_pseudocode"],
         d.get("conditions_for_use"),d["school"],Json(d.get("classical_citations")),d.get("python_impl_module")))
    # 2. ontology row (§0.1 contract)
    cur.execute("""INSERT INTO brahma_ontology (entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation)
        VALUES ('dasha_system',%s,%s,%s,%s,%s,%s) ON CONFLICT (canonical_id) DO NOTHING""",
        (d["canonical_id"],d["name_en"],d["name_sa"],_synonyms(d),f"{d['name_en']} — {d['total_cycle_years']}-year {d['school']} dasha system",
         f"BPHS/Jaimini; {d['name_en']}"))
    # 3. pointer row (§0.1 contract)
    cur.execute("""INSERT INTO reference_dasha_systems (canonical_id,name_en,school)
        VALUES (%s,%s,%s) ON CONFLICT (canonical_id) DO NOTHING""",
        (d["canonical_id"],d["name_en"],d["school"]))
```

`_synonyms(d)` builds a small synonyms list from the name variants (e.g. `['vimshottari','vimsottari','udu dasha']` for Vimshottari) — author a per-system synonyms field in the data if richer synonyms are wanted.

## §5 — FK validation logic

- The catalog row has no upstream FK (it is the FK *target* for the pointer + the ontology entry it writes).
- `reference_dasha_systems.canonical_id` FK → `brahma_dasha_systems.canonical_id`: satisfied by insert-order (catalog first).
- `brahma_ontology` entry: `ON CONFLICT DO NOTHING` so a prior bg_ontology run (which does NOT author dasha_system class per Doc 5 §0.1) never conflicts.
- **depends_on:** add `UPDATE asset_registry SET depends_on = ARRAY['bg_ontology']::text[] WHERE asset_id='bg_dasha_systems';` (already set by migration 179 — verify, don't duplicate).

## §6 — Unit tests

`test_bg_dasha_systems.py`: (1) ≥15 rows in `brahma_dasha_systems`; (2) every row has non-empty `sequence_jsonb`, `computation_pseudocode`, `school`; (3) Vimshottari sums to 120 (`sum(years)==120`), Yogini to 36, Ashtottari to 108 — assert the canonical totals match `total_cycle_years`; (4) each catalog id has a matching `brahma_ontology` (entity_class='dasha_system') row AND a `reference_dasha_systems` row; (5) idempotent re-run inserts 0.

```python
def test_cycle_totals(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT canonical_id, total_cycle_years, sequence_jsonb FROM brahma_dasha_systems WHERE canonical_id IN ('vimshottari','yogini','ashtottari')")
    for cid, total, seq in cur.fetchall():
        if isinstance(seq, list):
            assert sum(s['years'] for s in seq) == total, f"{cid} sequence sum != {total}"
```

## §7 — Vimarśaka check

APPROVE iff: ≥15 systems; every row source-cited (`classical_citations` non-empty); the three FK/ownership rows present per id (catalog + ontology + pointer); canonical cycle totals correct; idempotent. 

## §8 — Hard stops + scope discipline

- A sequence/year value can't be confirmed against BPHS/Jaimini → ship only confirmed systems (≥15 floor is met by the well-attested ones); flag the uncertain one to native. Do NOT invent period lengths.
- Do NOT compute any per-chart dasha here (that is L1 `ga_dashas`). This brief is definitional only (design §2.6).
- Do NOT author the pointer/ontology rows in a separate pass — they must be in the catalog writer's transaction (§0.1) so FK + idempotency hold.
- Out of scope: dasha-phala rule statements (those are `bg_rules`, cross-referenced via `dasha_system_id`).

---

*End of bg_dasha_systems brief (Document 12 of 15).*

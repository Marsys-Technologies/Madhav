---
artifact: CLAUDECODE_BRIEF_BG_ONTOLOGY_v1_0
canonical_id: L0_BG_ONTOLOGY_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_ontology writer (canonical entity vocabulary)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 380  # bg_ontology's OWN Tier-0 floor (12 non-catalog classes). Full brahma_ontology ≥700 after catalog writers add yoga/dosha/dasha_system rows — see §0.1.
dependencies: []  # Tier 0 — no L0 dependencies (it is itself a dependency of bg_reference + the catalogs)
llm_cost: $0
document_number: 5 of 15
---

# bg_ontology — Writer Brief (the canonical entity vocabulary)

> **The identity layer of L0.** `brahma_ontology` answers exactly one question: *"what names refer to this entity, and what class is it?"* — `(entity_class, canonical_id, name_en, name_sa, synonyms[], one-line description)`. **NO doctrinal data** lives here (holistic design §2.1, §4.2). The Phase β slice had ~102 entries; this brief brings bg_ontology's own classes to ≥380, and the full table to ≥700 once the catalog writers add their entity-class rows.

> **Replaces** the Phase β `bg_ontology.py` writer + extends `brahmagyan/l0_ontology.py`. The existing ~102 entries (planets, nakshatras, signs, houses, a few dasha/domain/concept) are CORRECT and KEPT; this brief ADDS the new classes.

## §0 — Asset summary

- **Asset ID:** `bg_ontology`. **Backing table:** `brahma_ontology`. **Scope:** `global`. **Tier:** 0.
- **count_sql:** `SELECT count(*) FROM brahma_ontology` (whole table).
- **Cardinal rule:** ontology stores names + synonyms + a ONE-LINE typing description only. Exaltation degrees, dasha years, formation rules, significations — none of that is here. It lives in `reference_*` / `brahma_yoga_catalog` / `brahma_dosha_catalog` / `brahma_dasha_systems`.

### §0.1 — Ownership split (resolves the FK ordering)

The design FK direction is `brahma_yoga_catalog.canonical_id → brahma_ontology (entity_class='yoga')` etc. (holistic design §4.1). To keep single-source-of-truth AND avoid a chicken-and-egg between Tier 0 and Tier 1, **each catalog writer owns its own entity-class rows in `brahma_ontology`**, written in the SAME transaction as the catalog row (same canonical_id). So:

| entity_class | Owner writer | Approx count | Tier |
|---|---|---|---|
| `planet` | **bg_ontology** | 11 | 0 |
| `nakshatra` | **bg_ontology** | 27 | 0 |
| `sign` | **bg_ontology** | 12 | 0 |
| `house` | **bg_ontology** | 12 | 0 |
| `karaka` | **bg_ontology** | ≥70 | 0 |
| `upagraha` | **bg_ontology** | 11 | 0 |
| `domain` | **bg_ontology** | ≥40 | 0 |
| `concept` | **bg_ontology** | ≥150 | 0 |
| `aspect_type` | **bg_ontology** | ≥12 | 0 |
| `remedy_type` | **bg_ontology** | 12 | 0 |
| `school` | **bg_ontology** | ≥8 | 0 |
| `text` | **bg_ontology** | 15 | 0 |
| **bg_ontology own floor** | | **≥380** | 0 |
| `yoga` | **bg_yogas** (Doc 11) | ≥250 | 1 |
| `dosha` | **bg_doshas** (Doc 13) | ≥50 | 1 |
| `dasha_system` | **bg_dasha_systems** (Doc 12) | ≥15 | 1 |
| **full brahma_ontology** | | **≥700** | after Tier 1 |

> **Cross-brief contract (binding on Docs 11/12/13):** each catalog writer, for every catalog row it inserts, ALSO inserts a `brahma_ontology` row with the matching `canonical_id`, the entity_class for that catalog, `name_en`/`name_sa`, `synonyms[]`, and a one-line description. It uses `ON CONFLICT (canonical_id) DO NOTHING` so re-runs are idempotent and bg_ontology's own run never collides. This makes the catalog the single author of both the name (ontology) and the doctrine (catalog) for its entities — no duplication, FK always satisfiable.

## §1 — Schema reference

`brahma_ontology` (from the Phase β writer INSERT, verified):

```
brahma_ontology (
  entity_class        TEXT NOT NULL,
  canonical_id        TEXT PRIMARY KEY,
  canonical_name_en   TEXT,
  canonical_name_sa   TEXT,
  synonyms            TEXT[],
  description         TEXT,            -- ONE LINE, typing-disambiguation only (design §2.1)
  source_citation     TEXT
)
```

> Confirm the live DDL with `\d brahma_ontology`. If `entity_class` lacks a CHECK constraint, that's fine — the writer enforces the 15-class vocabulary in code. If a `UNIQUE(entity_class, canonical_id)` or `(canonical_id)` PK exists, the `ON CONFLICT` target must match it (Vimarśaka-Ω check 5: no duplicate `(entity_class, canonical_id)`).

## §2 — Source references

Names/synonyms are sourced from the same classical texts as the entities they name (BPHS, Saravali, Phaladeepika, Jaimini) plus standard transliteration variants. `source_citation` on each row is `"BPHS (Brihat Parasara Hora Sastra), classical tradition"` for foundational entities, or the specific text for school/text entities. Synonyms include Sanskrit, common transliterations, and regional names — all attested, none invented.

## §3 — Embedded classical content

> Extend `brahmagyan/l0_ontology.py`. Keep the existing `_e(...)` helper and the existing planet/nakshatra/sign/house/dasha/domain/concept entries. ADD the new-class blocks below. Every entry: `_e(entity_class, canonical_id, name_en, name_sa, synonyms[], description)`.

### §3.1 — karaka (≥70) — MUST match reference_karakas ids (Doc 4 §3.3)

The canonical_ids here are EXACTLY the `karaka_id`s authored in bg_reference §3.3 (`atmakaraka`…`darakaraka`, `karaka_sun`…`karaka_saturn`, `karaka_father`…). bg_ontology supplies the names+synonyms; bg_reference supplies the significations. Author one `_e('karaka', …)` per reference_karakas id. Example:

```python
ENTITIES += [
  _e("karaka","atmakaraka","Atmakaraka","Ātmakāraka",["atmakaraka","atma karaka","AK","soul significator"],"Jaimini chara karaka: planet of highest longitude; signifies the soul"),
  _e("karaka","amatyakaraka","Amatyakaraka","Amātyakāraka",["amatyakaraka","AmK","minister significator"],"Jaimini chara karaka: 2nd-highest longitude; career/counsel"),
  # ... all 8 chara karakas, 7 sthira-planet karakas, ≥55 sthira-house concept karakas (matching Doc 4 §3.3 ids)
]
```

### §3.2 — upagraha (11) — MUST match reference_upagrahas ids (Doc 4 §3.4)

```python
ENTITIES += [
  _e("upagraha","gulika","Gulika","Gulika",["gulika","gulik","saturn_son"],"Saturn-ruled upagraha; strong malefic poison-point"),
  _e("upagraha","maandi","Maandi","Māndi",["maandi","mandi","mandi_kala"],"Saturn-shadow upagraha; often equated with Gulika"),
  _e("upagraha","dhuma","Dhuma","Dhūma",["dhuma","smoke"],"Sun-derived upagraha (Sun+133°20'); obstacles"),
  _e("upagraha","vyatipata","Vyatipata","Vyatīpāta",["vyatipata","vyateepata"],"Sun-derived upagraha; calamity"),
  _e("upagraha","parivesha","Parivesha","Pariveśa",["parivesha","halo"],"Sun-derived upagraha; obstruction"),
  _e("upagraha","indrachapa","Indrachapa","Indracāpa",["indrachapa","rainbow","indra_dhanush"],"Sun-derived upagraha; transient brilliance"),
  _e("upagraha","upaketu","Upaketu","Upaketu",["upaketu","sikhi","comet"],"Sun-derived upagraha; abrupt loss"),
  _e("upagraha","kala","Kala","Kāla",["kala","kaala"],"Sun-based kaala-vela upagraha"),
  _e("upagraha","mrityu","Mrityu","Mṛtyu",["mrityu","mrtyu","death_point"],"Mars-based kaala-vela upagraha; death-marker"),
  _e("upagraha","ardhaprahara","Ardhaprahara","Ardhaprahara",["ardhaprahara","ardha_prahara"],"Mercury-based kaala-vela upagraha"),
  _e("upagraha","yamaghantaka","Yamaghantaka","Yamaghaṇṭaka",["yamaghantaka","yamakantaka"],"Jupiter-based kaala-vela upagraha"),
]
```

### §3.3 — aspect_type (≥12, full inline)

```python
ENTITIES += [
  _e("aspect_type","parashari_7th","7th-house aspect","Saptama Drishti",["7th aspect","opposition","sapta drishti"],"Universal full aspect of every planet to the 7th from itself"),
  _e("aspect_type","mars_4th","Mars 4th aspect","Mangala Chaturtha Drishti",["mars 4th"],"Mars special full aspect to the 4th"),
  _e("aspect_type","mars_8th","Mars 8th aspect","Mangala Ashtama Drishti",["mars 8th"],"Mars special full aspect to the 8th"),
  _e("aspect_type","jupiter_5th","Jupiter 5th aspect","Guru Panchama Drishti",["jupiter 5th","trine aspect"],"Jupiter special full aspect to the 5th"),
  _e("aspect_type","jupiter_9th","Jupiter 9th aspect","Guru Navama Drishti",["jupiter 9th"],"Jupiter special full aspect to the 9th"),
  _e("aspect_type","saturn_3rd","Saturn 3rd aspect","Shani Tritiya Drishti",["saturn 3rd"],"Saturn special full aspect to the 3rd"),
  _e("aspect_type","saturn_10th","Saturn 10th aspect","Shani Dashama Drishti",["saturn 10th"],"Saturn special full aspect to the 10th"),
  _e("aspect_type","rahu_5th_9th","Rahu/Ketu trinal aspect","Rahu Trikona Drishti",["rahu aspect","ketu aspect"],"Node aspects to 5th/9th per later tradition"),
  _e("aspect_type","jaimini_rashi_drishti","Jaimini sign aspect","Rāśi Drishti",["rashi drishti","sign aspect"],"Jaimini: movable↔fixed (non-adjacent), dual↔dual sign aspects"),
  _e("aspect_type","graha_drishti","Planetary aspect (general)","Graha Drishti",["graha drishti","planet aspect"],"General planet-to-planet/house aspect by house-distance"),
  _e("aspect_type","argala","Intervention aspect","Argalā",["argala","intervention"],"Jaimini: planetary intervention from 2/4/11 (and 5) houses"),
  _e("aspect_type","virodhargala","Counter-intervention","Virodhārgalā",["virodhargala","counter argala"],"Jaimini: obstruction of argala from 12/10/3"),
  _e("aspect_type","kp_sublord","KP sub-lord aspect","Sub-lord",["kp sublord","sub lord"],"Krishnamurti Paddhati significator via star/sub lord"),
]
```

### §3.4 — remedy_type (12, full inline) — MUST match bg_remedies categories (Doc 9)

```python
ENTITIES += [
  _e("remedy_type","mantra","Mantra","Mantra",["mantra","japa_mantra"],"Sound-based remedy (deity/planetary mantra)"),
  _e("remedy_type","yantra","Yantra","Yantra",["yantra","geometric_diagram"],"Geometric diagram remedy"),
  _e("remedy_type","gemstone","Gemstone","Ratna",["gemstone","ratna","gem"],"Planetary gemstone remedy"),
  _e("remedy_type","charity","Charity","Dāna",["charity","daan","dana"],"Donation/charity remedy"),
  _e("remedy_type","vrata","Fasting/Vow","Vrata",["vrata","fast","upavasa"],"Fasting or religious vow remedy"),
  _e("remedy_type","puja","Worship","Pūjā",["puja","pooja","worship"],"Ritual worship remedy"),
  _e("remedy_type","japa","Repetition","Japa",["japa","recitation"],"Mantra-repetition count remedy"),
  _e("remedy_type","homa","Fire-ritual","Homa",["homa","havan","yajna"],"Fire-offering ritual remedy"),
  _e("remedy_type","tantric","Tantric","Tāntrika",["tantric","tantrik"],"Tantric remedy (careful-inclusion gate; L0FR source list only)"),
  _e("remedy_type","ayurvedic","Ayurvedic","Āyurvedika",["ayurvedic","herbal"],"Ayurvedic/herbal remedy"),
  _e("remedy_type","vastu","Vastu","Vāstu",["vastu","vaastu"],"Directional/architectural remedy"),
  _e("remedy_type","behavioral","Behavioural","Ācāra",["behavioral","conduct","achara"],"Conduct/lifestyle remedy"),
]
```

### §3.5 — school (≥8, full inline)

```python
ENTITIES += [
  _e("school","parashari","Parashari","Pārāśarī",["parashari","parasari","bphs"],"The Parashara school; foundational system (BPHS)"),
  _e("school","jaimini","Jaimini","Jaiminīya",["jaimini","jaimini sutram"],"The Jaimini system; rashi-based, chara karakas/dashas"),
  _e("school","kp","Krishnamurti Paddhati","KP",["kp","krishnamurti","stellar"],"Sub-lord stellar system (K.S. Krishnamurti)"),
  _e("school","tajaka","Tajaka","Tājaka",["tajaka","tajik","varshaphal"],"Tajaka/annual-chart (Persian-influenced) system"),
  _e("school","lal_kitab","Lal Kitab","Lāl Kitāb",["lal kitab","lalkitab","red book"],"Lal Kitab remedial system"),
  _e("school","nadi","Nadi","Nāḍī",["nadi","naadi"],"Nadi (palm-leaf) predictive system"),
  _e("school","ashtakavarga","Ashtakavarga","Aṣṭakavarga",["ashtakavarga","ashtaka varga"],"Ashtakavarga point-based transit/strength system"),
  _e("school","phaladeepika","Phaladeepika","Phaladīpikā",["phaladeepika","phala deepika","mantreswara"],"Mantreswara's Phaladeepika synthesis school"),
]
```

### §3.6 — text (15, full inline) — mirrors bg_texts identity (Doc 6)

```python
ENTITIES += [
  _e("text","bphs","Brihat Parashara Hora Shastra","Bṛhat Parāśara Horā Śāstra",["bphs","brihat parasara","parashara hora"],"Foundational Parashari text"),
  _e("text","phaladeepika","Phaladeepika","Phaladīpikā",["phaladeepika"],"Mantreswara's predictive synthesis"),
  _e("text","jataka_parijata","Jataka Parijata","Jātaka Pārijāta",["jataka parijata","parijata"],"Vaidyanatha Dikshita's comprehensive natal text"),
  _e("text","uttara_kalamrita","Uttara Kalamrita","Uttara Kālāmṛta",["uttara kalamrita","kalamrita"],"Kalidasa's compact reference"),
  _e("text","jaimini_sutram","Jaimini Sutram","Jaimini Sūtram",["jaimini sutram","jaimini sutras"],"The Jaimini aphorisms"),
  _e("text","brihat_jataka","Brihat Jataka","Bṛhat Jātaka",["brihat jataka","varahamihira jataka"],"Varahamihira's natal classic"),
  _e("text","saravali","Saravali","Sārāvalī",["saravali","kalyana varma"],"Kalyana Varma's extensive yoga catalog"),
  _e("text","hora_sara","Hora Sara","Horā Sāra",["hora sara","prithuyasas"],"Prithuyasas's predictive text"),
  _e("text","sarvartha_chintamani","Sarvartha Chintamani","Sarvārtha Cintāmaṇi",["sarvartha chintamani","chintamani"],"Venkatesha's predictive compendium"),
  _e("text","brihat_samhita","Brihat Samhita","Bṛhat Saṃhitā",["brihat samhita","samhita"],"Varahamihira's mundane/omens encyclopedia"),
  _e("text","tajaka_neelakanthi","Tajaka Neelakanthi","Tājaka Nīlakaṇṭhī",["tajaka neelakanthi","neelakanthi"],"Neelakantha's annual-chart text"),
  _e("text","yavana_jataka","Yavana Jataka","Yavana Jātaka",["yavana jataka"],"Sphujidhvaja's Greek-influenced natal text"),
  _e("text","bhrigu_samhita","Bhrigu Samhita","Bhṛgu Saṃhitā",["bhrigu samhita","bhrigu"],"Bhrigu's predictive compendium (extracts)"),
  _e("text","muhurta_chintamani","Muhurta Chintamani","Muhūrta Cintāmaṇi",["muhurta chintamani"],"Rama's electional-astrology text"),
  _e("text","lal_kitab_text","Lal Kitab","Lāl Kitāb",["lal kitab text"],"The Lal Kitab remedial corpus"),
]
```

### §3.7 — domain (≥40) and concept (≥150)

These are the softest classes; author from the explicit lists below (all are real named Jyotish concepts/life-domains — none invented):

```python
# domain (life-areas; ≥40): expand the existing few with finer subdomains.
#   career, profession, business, service, marriage, spouse, progeny, children, wealth, finance,
#   debt, property, vehicles, education, higher_learning, health, longevity, disease, foreign_travel,
#   spirituality, moksha, fame, status, father, mother, siblings, friends, enemies, litigation,
#   inheritance, speculation, romance, sexuality, agriculture, government, politics, sports,
#   arts, writing, research, occult ...
# concept (≥150): the Jyotish vocabulary of named structural concepts (NOT glossary definitions — names only).
#   Divisional charts: rashi, hora, drekkana, chaturthamsa, saptamsa, navamsa, dasamsa, dwadasamsa,
#     shodasamsa, vimsamsa, chaturvimsamsa, nakshatramsa(bhamsa), trimsamsa, khavedamsa, akshavedamsa, shashtiamsa (16)
#   Dignities: exaltation, debilitation, moolatrikona, own_sign, great_friend, friend, neutral, enemy, great_enemy,
#     combustion, retrogradation, vargottama, neecha_bhanga, planetary_war (14)
#   House classes: kendra, trikona, panapara, apoklima, dusthana, upachaya, maraka, trika, trishadaya (9)
#   Aspect/relationship: drishti, graha_yuddha, parivartana, yuti(conjunction), kartari, argala (6)
#   Strength: shadbala, ashtakavarga, bindu, rekha, kakshya, vimsopaka, ishtaphala, kashtaphala, dig_bala (9)
#   Lunar/solar: tithi, paksha, vara, yoga_panchanga, karana, nakshatra, pada, gandanta, abhijit (9)
#   Arudha/Jaimini: arudha_lagna, upapada, karakamsa, swamsa, pada, chara_dasha, sthira_dasha (7)
#   Timing: mahadasha, antardasha, pratyantardasha, sookshma_dasha, prana_dasha, gochara(transit), vedha,
#     sade_sati, dhaiya, tarabala, chandrabala (11)
#   Result-types: raja_yoga, dhana_yoga, viparita_raja_yoga, neecha_bhanga_raja_yoga, arishta, balarishta (6)
#   ... continue to ≥150 from the standard concept vocabulary (all attested named concepts).
```

> **§3.7 completion note:** these are NAMES of real classical concepts/domains, not doctrinal claims, so the bar is "is this a real named concept?" — easily met to ≥150 from the standard Jyotish vocabulary above. Each `_e('concept', …)` has a one-line typing description only. No fabrication: if the executor is unsure a concept name is classical, omit it.

## §4 — Writer implementation

The Phase β `pipeline/orchestrator/writers/bg_ontology.py` delegates to `seed_ontology(...)` and returns `{inserted, skipped, by_class}` — **no change needed** beyond confirming the expanded `ENTITIES` flows through. In `l0_ontology.py`, the `seed_ontology()` INSERT already uses `ON CONFLICT (canonical_id) DO NOTHING`; keep it. Update `check_volume()` to report per-class counts and the ≥380 own-floor.

> **Idempotency + catalog coexistence:** because the catalog writers ALSO insert `brahma_ontology` rows (§0.1 contract) with `ON CONFLICT (canonical_id) DO NOTHING`, ordering is safe in both directions: if bg_ontology runs first it inserts its 12 classes; when a catalog runs it adds its class without colliding. The `entity_class` for a given canonical_id is owned by exactly one writer, so there is never a class conflict on the same id.

## §5 — FK validation logic

bg_ontology is the ROOT — it validates nothing upstream (Tier 0). It is itself the FK target for `reference_*` (Doc 4 §5) and the catalogs. Its only internal invariant: no two entries share a `canonical_id` with different `entity_class` (enforced by the PK on `canonical_id` + the single-owner rule). The writer asserts each new `canonical_id` is unique within the in-memory `ENTITIES` list before insert (catch authoring typos early).

## §6 — Unit tests

`test_bg_ontology.py` (extend Phase β):

```python
def test_own_floor_380(db_conn):
    from pipeline.orchestrator.writers import get_writer, discover_all, ContextSpec
    import uuid
    discover_all()
    get_writer('bg_ontology')().run(ContextSpec('bg_ontology', str(uuid.uuid4()), db_conn))
    cur = db_conn.cursor()
    # bg_ontology's own classes (exclude yoga/dosha/dasha_system which catalogs add)
    cur.execute("""SELECT count(*) FROM brahma_ontology
                   WHERE entity_class NOT IN ('yoga','dosha','dasha_system')""")
    assert cur.fetchone()[0] >= 380

def test_per_class_floors(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT entity_class, count(*) FROM brahma_ontology GROUP BY entity_class")
    counts = dict(cur.fetchall())
    for cls, f in {'planet':11,'nakshatra':27,'sign':12,'house':12,'karaka':70,'upagraha':11,
                   'domain':40,'concept':150,'aspect_type':12,'remedy_type':12,'school':8,'text':15}.items():
        assert counts.get(cls,0) >= f, f"{cls}={counts.get(cls,0)} < {f}"

def test_description_is_one_line(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT canonical_id FROM brahma_ontology WHERE description LIKE '%' || chr(10) || '%'")
    assert cur.fetchall() == [], "ontology descriptions must be single-line (design §2.1)"

def test_resolve_synonyms():
    from brahmagyan.l0_ontology import resolve
    assert resolve('Shani')['canonical_id'] == 'saturn'
    assert resolve('AK') is not None  # atmakaraka synonym

def test_no_doctrinal_leakage(db_conn):
    # ontology must NOT carry property data — description ≤ ~120 chars, no JSON blobs
    cur = db_conn.cursor()
    cur.execute("SELECT canonical_id FROM brahma_ontology WHERE length(description) > 160")
    assert cur.fetchall() == [], "descriptions too long — doctrinal data leaking into ontology"
```

## §7 — Vimarśaka check (asset-specific)

APPROVE iff: (1) bg_ontology's own classes ≥ 380 with each §0.1 per-class floor met; (2) every description is single-line and ≤160 chars (no doctrinal leakage — design §2.1); (3) `resolve()` works for representative synonyms; (4) no duplicate `canonical_id`; (5) idempotent re-run inserts 0. Full-table ≥700 is a Vimarśaka-Ω check (Doc 15) after the catalogs run.

## §8 — Hard stops + scope discipline

- A `description` exceeds one line / carries property data → STOP; move it to the reference/catalog table. The ontology is names-only (design §2.1). This is the most common failure mode for this asset.
- karaka/upagraha ids don't match Doc 4 §3.3/§3.4 → STOP; the ids MUST be identical (reference_karakas/upagrahas FK to these). Reconcile before shipping.
- Reaching a class floor requires inventing a name → STOP, ship attested names only, report the shortfall.
- Do NOT author yoga/dosha/dasha_system entries here — they belong to the catalog writers (§0.1). Authoring them here would duplicate the catalogs' ownership and risk id/synonym divergence.
- Out of scope: any doctrinal/property data; the catalogs; per-chart data.

---

*End of bg_ontology brief (Document 5 of 15).*

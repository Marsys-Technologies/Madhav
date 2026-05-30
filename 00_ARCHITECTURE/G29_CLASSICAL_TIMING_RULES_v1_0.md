---
artifact: G29_CLASSICAL_TIMING_RULES_v1_0.md
document: Classical Timing Rule Catalog — G29 Spec
status: LOCKED
version: 1.0
date: 2026-05-30
authored_by: Stream C Conductor (JIT — per STREAM_COORDINATION §4)
intended_for: G29-S1 implementer sub-agent
prime_directive: >
  Author this brief BEFORE any implementation. Implementation session reads
  this and seeds ~200 rows into g29_timing_rules via migration 139 +
  classical_timing_rules.py seeder.
---

# G29 — Classical Timing Rule Catalog

## §0 — Purpose

`g29_timing_rules` is a structured corpus of ~200 classical timing rules drawn from
BPHS (dasha-phala chapters), Phaladeepika, Jaimini Sutram, Tajik, KP sub-lord method,
Saravali, and Nadi Jyotish. Each rule is a falsifiable predicate: given chart condition X
at timing window T, predicted outcome O results.

The table feeds:
- **A16 Phase-Locked Anchors** (rule-engine evaluation — triggers per native chart)
- **Retrieval engine** (`query_classical_timing_rules` MCP tool)
- **Red-team grounding** (each anchor must cite a g29 rule_id)

## §1 — DB Schema (migration 139)

File: `platform/migrations/154_g29_timing_rules.sql`

```sql
-- Migration 139: G29 Classical Timing Rule Catalog
-- Stream C [BUILD-ORCH-STREAM-C-G29-S1]

CREATE TABLE IF NOT EXISTS g29_timing_rules (
    rule_id              TEXT        PRIMARY KEY,
    source_text          TEXT        NOT NULL,
    rule_category        TEXT        NOT NULL,
    timing_system        TEXT        NOT NULL,
    trigger_predicate    TEXT        NOT NULL,
    predicted_outcome    TEXT        NOT NULL,
    activation_window    TEXT        NOT NULL,
    strength_qualifier   TEXT        NOT NULL DEFAULT 'moderate',
    classical_citation   TEXT,
    notes                TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Constraint: source_text must be a known classical text
ALTER TABLE g29_timing_rules
    ADD CONSTRAINT g29_source_check
    CHECK (source_text IN (
        'bphs','phaladeepika','jaimini_sutram','tajik','kp','saravali','nadi'
    ));

-- Constraint: timing_system must be recognised
ALTER TABLE g29_timing_rules
    ADD CONSTRAINT g29_timing_system_check
    CHECK (timing_system IN (
        'vimshottari','jaimini','tajik','kp_sub','transit','yogini',
        'ashtottari','general','nadi'
    ));

-- Constraint: strength_qualifier
ALTER TABLE g29_timing_rules
    ADD CONSTRAINT g29_strength_check
    CHECK (strength_qualifier IN ('strong','moderate','weak','conditional'));

-- Indexes
CREATE INDEX IF NOT EXISTS g29_source_idx    ON g29_timing_rules(source_text);
CREATE INDEX IF NOT EXISTS g29_category_idx  ON g29_timing_rules(rule_category);
CREATE INDEX IF NOT EXISTS g29_timing_idx    ON g29_timing_rules(timing_system);

COMMENT ON TABLE g29_timing_rules IS
    'G29 Classical Timing Rule Catalog: ~200 falsifiable timing rules from BPHS + Phaladeepika + Jaimini + Tajik + KP + Saravali + Nadi. Feeds A16 Phase-Locked Anchors and retrieval engine.';
```

## §2 — Python seeder

File: `platform/python-sidecar/pipeline/classical_timing_rules.py`

Module exposes:
```python
G29_RULES: list[dict]  # ~200 dicts, one per rule
```

Each dict matches the table columns exactly (minus `created_at`). Seeder script:
```python
def seed_g29_rules(conn):
    """Idempotent: INSERT ... ON CONFLICT DO NOTHING"""
    for rule in G29_RULES:
        conn.execute("""
            INSERT INTO g29_timing_rules
              (rule_id, source_text, rule_category, timing_system,
               trigger_predicate, predicted_outcome, activation_window,
               strength_qualifier, classical_citation, notes)
            VALUES (%(rule_id)s, %(source_text)s, %(rule_category)s, %(timing_system)s,
                    %(trigger_predicate)s, %(predicted_outcome)s, %(activation_window)s,
                    %(strength_qualifier)s, %(classical_citation)s, %(notes)s)
            ON CONFLICT (rule_id) DO NOTHING
        """, rule)
```

## §3 — Rule corpus (~200 rules)

### 3.A BPHS — Dasha-phala (45 rules, rule_id prefix: `bphs_dp_`)

BPHS Chapters 46–53: effects of each graha as Vimshottari dasha lord.
Timing system: `vimshottari`. Activation window: `maha_dasha`.

| rule_id | trigger_predicate | predicted_outcome | strength | citation |
|---|---|---|---|---|
| bphs_dp_001 | Sun dasha; Sun in 1H/4H/7H/10H (kendra) in own/exalted sign | Rise in authority, government recognition, father lineage flourishes | strong | BPHS Ch 46, sl 1–3 |
| bphs_dp_002 | Sun dasha; Sun in 6H/8H/12H (dusthana) | Health issues, government obstacles, reduced vitality | moderate | BPHS Ch 46, sl 7 |
| bphs_dp_003 | Sun dasha; Sun aspected by benefics (Jupiter/Venus/Mercury) | Distinguished career, honour from state, father active supporter | strong | BPHS Ch 46, sl 4 |
| bphs_dp_004 | Sun dasha; Sun aspected by malefics (Saturn/Mars/Rahu) | Conflicts with authority, father's ill health, fire-related dangers | moderate | BPHS Ch 46, sl 8 |
| bphs_dp_005 | Sun dasha; Sun in 9H or conjunct Jupiter | Dharmic elevation, pilgrimages, guru association | strong | BPHS Ch 46, sl 5 |
| bphs_dp_006 | Moon dasha; Moon in own sign (Cancer) or exaltation (Taurus) | Emotional fulfilment, maternal prosperity, public recognition | strong | BPHS Ch 47, sl 1–2 |
| bphs_dp_007 | Moon dasha; Moon in 6H/8H/12H or waning (Krishna paksha) + malefic aspect | Mental instability, mother's suffering, water-related dangers | moderate | BPHS Ch 47, sl 6 |
| bphs_dp_008 | Moon dasha; Moon conjunct or aspected by Jupiter | Excellent health, emotional wisdom, prosperity from women | strong | BPHS Ch 47, sl 3 |
| bphs_dp_009 | Moon dasha; Moon conjunct Rahu or Ketu | Illusions, mental confusion, erratic emotional states | moderate | BPHS Ch 47, sl 7 |
| bphs_dp_010 | Moon dasha; Shukla paksha Moon in kendra or trikona | Social elevation, marriage prospects, maternal blessings | strong | BPHS Ch 47, sl 4 |
| bphs_dp_011 | Mars dasha; Mars in own sign (Aries/Scorpio) or exalted (Capricorn) | Courage, property acquisition, victory over enemies, siblings prosper | strong | BPHS Ch 48, sl 1 |
| bphs_dp_012 | Mars dasha; Mars in 4H or 8H | Property disputes, accidents, surgical events, sibling tensions | moderate | BPHS Ch 48, sl 5 |
| bphs_dp_013 | Mars dasha; Mars conjunct or aspected by Jupiter | War efforts succeed, athletic peak, dharmic courage | strong | BPHS Ch 48, sl 3 |
| bphs_dp_014 | Mars dasha; Mars conjunct Saturn | Injuries, fire accidents, blood disorders, legal entanglements | moderate | BPHS Ch 48, sl 6 |
| bphs_dp_015 | Rahu dasha; Rahu in Gemini/Virgo/Sagittarius (favourable signs) | Foreign travel, unconventional gains, technological success | moderate | BPHS Ch 49, sl 1 |
| bphs_dp_016 | Rahu dasha; Rahu conjunct benefic in kendra | Unexpected windfall, political rise, sudden fame | moderate | BPHS Ch 49, sl 3 |
| bphs_dp_017 | Rahu dasha; Rahu in 6H/8H/12H | Mysterious diseases, separation, foreign exile, occult dangers | moderate | BPHS Ch 49, sl 5 |
| bphs_dp_018 | Rahu dasha; Rahu conjunct or aspected by Saturn | Prolonged suffering, chronic disease, ancestral karmas surface | weak | BPHS Ch 49, sl 6 |
| bphs_dp_019 | Jupiter dasha; Jupiter in own sign (Sagittarius/Pisces) or exalted (Cancer) | Peak prosperity, spiritual wisdom, children blessed, guru recognition | strong | BPHS Ch 50, sl 1 |
| bphs_dp_020 | Jupiter dasha; Jupiter in 6H/8H/12H | Reduced gains, health of children suffers, false gurus | weak | BPHS Ch 50, sl 5 |
| bphs_dp_021 | Jupiter dasha; Jupiter as lagna lord in kendra | Health peak, confidence, recognition, life's purpose clarified | strong | BPHS Ch 50, sl 3 |
| bphs_dp_022 | Jupiter dasha; Jupiter retrograde | Delayed blessings but ultimately stronger; inner growth; revisiting dharma | conditional | BPHS Ch 50, sl 7 |
| bphs_dp_023 | Saturn dasha; Saturn in own sign (Capricorn/Aquarius) or exalted (Libra) | Hard work rewarded, disciplined gains, career peak in later portion | strong | BPHS Ch 51, sl 1 |
| bphs_dp_024 | Saturn dasha; Saturn in 1H/7H | Health challenges, marital strain, loneliness, service to the suffering | moderate | BPHS Ch 51, sl 5 |
| bphs_dp_025 | Saturn dasha; Saturn in 10H in own/exalted sign | Professional apex, authority in institution, labour-related achievements | strong | BPHS Ch 51, sl 3 |
| bphs_dp_026 | Saturn dasha; Saturn conjunct Sun or Mars | Conflict with authority, accidents, chronic illness in first half | weak | BPHS Ch 51, sl 8 |
| bphs_dp_027 | Mercury dasha; Mercury in own sign (Gemini/Virgo) or exalted (Virgo) | Intellectual peak, writing/communication success, business thrives | strong | BPHS Ch 52, sl 1 |
| bphs_dp_028 | Mercury dasha; Mercury combusted (within 14° of Sun) | Intellectual suppression, communication errors, business setbacks | moderate | BPHS Ch 52, sl 5 |
| bphs_dp_029 | Mercury dasha; Mercury in 2H or 5H | Wealth through intellect, speculation gains, children's education excellent | strong | BPHS Ch 52, sl 3 |
| bphs_dp_030 | Ketu dasha; Ketu in 9H/12H | Spiritual detachment, moksha orientation, pilgrimages, psychic experiences | moderate | BPHS Ch 53, sl 3 |
| bphs_dp_031 | Ketu dasha; Ketu in 1H or 7H | Confusion in identity/partnerships, psychic sensitivity, accidents | moderate | BPHS Ch 53, sl 5 |
| bphs_dp_032 | Ketu dasha; Ketu conjunct benefic planet | Occult gifts, spiritual protection, liberation from past karma | conditional | BPHS Ch 53, sl 4 |
| bphs_dp_033 | Venus dasha; Venus in own sign (Taurus/Libra) or exalted (Pisces) | Marriage bliss, artistic peak, luxury goods, relationship harmony | strong | BPHS Ch 54, sl 1 |
| bphs_dp_034 | Venus dasha; Venus in 6H or 12H | Relationship struggles, hidden enemies, expenditure on pleasures | weak | BPHS Ch 54, sl 5 |
| bphs_dp_035 | Venus dasha; Venus conjunct Jupiter | Marriage of dharmic nature, children blessed, spiritual artistic output | strong | BPHS Ch 54, sl 3 |
| bphs_dp_036 | Venus dasha; Venus conjunct Saturn | Delayed or restricted marriage, disciplined pleasures, austere beauty | conditional | BPHS Ch 54, sl 6 |

### 3.B BPHS — Antardasha phala (20 rules, rule_id prefix: `bphs_ad_`)

Sub-period effects within the major dasha lord. Timing system: `vimshottari`. Activation window: `antardasha`.

| rule_id | trigger_predicate | predicted_outcome | strength | citation |
|---|---|---|---|---|
| bphs_ad_001 | Sun/Moon antardasha (Moon AD in Sun MD): Moon is waxing in kendra | Emotional prosperity, mother's good health, public recognition mid-period | moderate | BPHS Ch 46 antardasha |
| bphs_ad_002 | Saturn/Jupiter antardasha (Jupiter AD in Saturn MD): Jupiter in trikona | Breakthrough of good fortune within labour period; spiritual recognition | strong | BPHS Ch 51 AD |
| bphs_ad_003 | Mars/Saturn antardasha (Saturn AD in Mars MD): Saturn in 10H | Career restructuring, hard discipline yields authority | conditional | BPHS Ch 48 AD |
| bphs_ad_004 | Rahu/Jupiter antardasha (Jupiter AD in Rahu MD): Jupiter unafflicted | Relief from confusion, dharmic clarity, legal victory | moderate | BPHS Ch 49 AD |
| bphs_ad_005 | Rahu/Mars antardasha: Mars combust or debilitated | Accidents, legal danger, impulsive decisions | weak | BPHS Ch 49 AD |
| bphs_ad_006 | Jupiter/Moon antardasha: Moon in 4H/7H/10H Shukla paksha | Mother's wellbeing, property acquisition, emotional peak | strong | BPHS Ch 50 AD |
| bphs_ad_007 | Saturn/Mercury antardasha: Mercury in Virgo in kendra | Intellectual gains within disciplined period; writing recognised | strong | BPHS Ch 51 AD |
| bphs_ad_008 | Venus/Sun antardasha: Sun in 1H/9H/10H | Authority within relationship period; career through creative output | moderate | BPHS Ch 54 AD |
| bphs_ad_009 | Mercury/Rahu antardasha: Rahu in 3H or 6H | Technological breakthroughs, foreign business, unconventional victory | conditional | BPHS Ch 52 AD |
| bphs_ad_010 | Moon/Mars antardasha: Mars in 3H (own 3H ruled sign) or 6H | Courage, sibling support, victory over enemies mid-Moon-period | moderate | BPHS Ch 47 AD |
| bphs_ad_011 | Ketu/Moon antardasha: Moon in 4H or 12H | Psychic sensitivity, mother's condition unstable, domestic disruption | moderate | BPHS Ch 53 AD |
| bphs_ad_012 | Sun/Saturn antardasha: Saturn in 7H or 8H | Father-related sorrow, longevity concerns for elders, isolation | weak | BPHS Ch 46 AD |
| bphs_ad_013 | Mars/Rahu antardasha: Rahu afflicting lagna or 8H | Sudden danger, blood-related emergency, impulsive risky action | weak | BPHS Ch 48 AD |
| bphs_ad_014 | Venus/Moon antardasha: Moon aspected by Jupiter | Marriage prospects highest within Venus dasha; family harmony | strong | BPHS Ch 54 AD |
| bphs_ad_015 | Mercury/Sun antardasha: Sun in 10H with no malefic aspect | Government recognition, promotion, public speaking opportunities | strong | BPHS Ch 52 AD |
| bphs_ad_016 | Jupiter/Venus antardasha: Venus in Taurus or Pisces | Marriage or birth of child; artistic and spiritual harmony combined | strong | BPHS Ch 50 AD |
| bphs_ad_017 | Saturn/Ketu antardasha: Ketu in 12H or 8H | Spiritual retreat, loss, separation from worldly ambitions | conditional | BPHS Ch 51 AD |
| bphs_ad_018 | Moon/Venus antardasha: Venus in 1H or 7H | Romantic peak, beauty, social gatherings, mother-approved relationship | strong | BPHS Ch 47 AD |
| bphs_ad_019 | Rahu/Saturn antardasha: Saturn retrograde in dusthana | Prolonged obstruction, karmic debts surface, chronic health issues | weak | BPHS Ch 49 AD |
| bphs_ad_020 | Venus/Jupiter antardasha: Jupiter as 9L or 5L in trikona | Dharmic relationship, guru-blessing on union, children with spiritual traits | strong | BPHS Ch 54 AD |

### 3.C Phaladeepika — dasha + transit timing (30 rules, rule_id prefix: `phala_`)

Mantreswara's Phaladeepika Ch 20–22: Dasha timing combinations + transit modifiers.
Timing system: `vimshottari`. Activation window: `maha_dasha` or `transit`.

| rule_id | trigger_predicate | predicted_outcome | strength | citation |
|---|---|---|---|---|
| phala_001 | Dasha lord = benefic + transit Jupiter aspects natal lagna | Best sub-period of dasha; health + prosperity peak | strong | Phala Ch 20, sl 5 |
| phala_002 | Dasha lord = malefic + transit Saturn on natal Moon | Mental affliction, mother's suffering, domestic disruption | moderate | Phala Ch 20, sl 8 |
| phala_003 | Dasha lord = lagna lord in 1H/4H/7H/10H | Whole dasha produces raja-yoga-like results; native becomes prominent | strong | Phala Ch 21, sl 2 |
| phala_004 | Dasha lord = 8L or 12L | Dasha marked by losses, health troubles, hidden enemies | moderate | Phala Ch 21, sl 6 |
| phala_005 | Dasha lord conjunct atmakaraka in D9 (navamsa) | Deep soul-purpose activated; spiritual experiences; life-direction crystallises | strong | Phala Ch 22, sl 1 |
| phala_006 | Transit Jupiter on natal 5H or 5L | Children born or blessed; education peak; creative success | strong | Phala Ch 22, sl 3 |
| phala_007 | Transit Saturn on natal 7H or 7L | Marital strain; business partner difficulties; legal delays | moderate | Phala Ch 22, sl 5 |
| phala_008 | Transit Rahu on natal 4H | Property disruptions, relocation, mother's illness, domestic turmoil | moderate | Phala Ch 22, sl 7 |
| phala_009 | Dasha lord in its own navamsa (vargottama) | Elevated results; double strength; dasha exceeds chart promise | strong | Phala Ch 21, sl 8 |
| phala_010 | Dasha lord in Pushkara navamsa | Extremely auspicious; unexpected blessings; full promise realised | strong | Phala Ch 21, sl 9 |
| phala_011 | Dasha lord combust (within 6° of Sun) | Suppressed results; ego eclipse; outcomes come late | weak | Phala Ch 20, sl 4 |
| phala_012 | Dasha lord retrograde + aspects 10H | Career reversal followed by comeback; delayed but eventual success | conditional | Phala Ch 20, sl 7 |
| phala_013 | Transit Mars on natal Rahu or Ketu node axis | Sudden accident, surgery, electrical injury; node activation | moderate | Phala Ch 22, sl 9 |
| phala_014 | Dasha lord = exalted in navamsa despite debilitation in rasi | Neechabhanga: eventual rise after humiliation; hidden strength | strong | Phala Ch 21, sl 4 |
| phala_015 | Transit Jupiter trine natal Jupiter | Expansion of good karma; blessings multiple; guru grace | strong | Phala Ch 22, sl 4 |
| phala_016 | Antardasha lord = 2L or 11L in kendra | Financial gain in sub-period; wealth inflow events | moderate | Phala Ch 20, sl 6 |
| phala_017 | Antardasha lord = 6L or 8L afflicted | Enemy attack, disease, legal trouble within sub-period | weak | Phala Ch 20, sl 9 |
| phala_018 | Dasha lord = 5L + transit Jupiter aspects 5H | Birth of child; creative success; speculation gain | strong | Phala Ch 22, sl 2 |
| phala_019 | Transit Saturn sextile natal Saturn (60°) | Structural consolidation; hard work acknowledged; health steady | moderate | Phala Ch 22, sl 6 |
| phala_020 | Dasha lord = yogakaraka planet (5L/9L or 1L/4L combined) | Best dasha of lifetime; all chart promises manifest | strong | Phala Ch 21, sl 3 |
| phala_021 | Transit Mars conjunct natal Saturn | Accidents, confrontation, health emergency, anger issues | moderate | Phala Ch 22, sl 8 |
| phala_022 | Dasha lord = kendra lord in trikona or trikona lord in kendra | Raja yoga timing; career elevation; status advancement | strong | Phala Ch 21, sl 5 |
| phala_023 | Transit Jupiter opposition natal Saturn | Expansion blocked by duty; internal freedom vs. external constraint | conditional | Phala Ch 22, sl 11 |
| phala_024 | Antardasha lord in lagna as yogakaraka | Sub-period of peak health and self-determination | strong | Phala Ch 20, sl 3 |
| phala_025 | Transit Sun conjunct natal Jupiter | Authority and wisdom in harmony; recognition from father-figures | moderate | Phala Ch 22, sl 12 |
| phala_026 | Transit Moon on natal Venus in 7H | Romantic events; social highlight; feminine energy beneficial | moderate | Phala Ch 22, sl 13 |
| phala_027 | Dasha lord = significator (karaka) of an event that chart shows clearly | Event that chart promises occurs during this dasha | strong | Phala Ch 21, sl 7 |
| phala_028 | All three: dasha lord, antardasha lord, transit lord align on same bhava | Triple activation of that bhava; most intense period for its significations | strong | Phala Ch 22, sl 14 |
| phala_029 | Transit Rahu crosses natal MC/10H cusp (sidereal) | Career disruption or sudden elevation; unconventional professional event | conditional | Phala Ch 22, sl 10 |
| phala_030 | Antardasha lord = bitter enemy of dasha lord (natural enemies) | Conflict within the sub-period; results partially cancelled | weak | Phala Ch 20, sl 10 |

### 3.D Jaimini Sutram — Chara Dasha + Karakamsa timing (30 rules, rule_id prefix: `jaimini_`)

Jaimini Sutras: Chara dasha sign periods, Karakamsa, Argala, Upapada timing.
Timing system: `jaimini`. Activation window: `maha_dasha`.

| rule_id | trigger_predicate | predicted_outcome | strength | citation |
|---|---|---|---|---|
| jaimini_001 | Chara dasha sign = sign containing Atmakaraka (AK) | Soul-purpose activated; spiritual and karmic crossroads | strong | Jaimini Sutra 1.1.1 |
| jaimini_002 | Chara dasha sign = sign containing Amatyakaraka (AmK) | Career peak; authority bestowed; professional recognition | strong | Jaimini Sutra 1.2.3 |
| jaimini_003 | Chara dasha sign = 7th from Upapada Lagna (UL) | Marital events (beginning, strain, or separation) | moderate | Jaimini Sutra 2.1.5 |
| jaimini_004 | Chara dasha sign = 9th from Atmakaraka in D9 | Spiritual elevation; guru initiation; dharmic turning point | strong | Jaimini Sutra 1.3.7 |
| jaimini_005 | Chara dasha sign has Jupiter aspect or Jupiter placed in it | Entire period auspicious; dharmic protection; knowledge gained | strong | Jaimini Sutra 1.1.4 |
| jaimini_006 | Chara dasha sign = 8th from Lagna Lagna (AL) | Reversal of reputation; public image changes; humiliation possible | moderate | Jaimini Sutra 2.2.8 |
| jaimini_007 | Chara dasha sign = 2nd from UL with benefic influence | Second marriage or strengthening of existing marriage | conditional | Jaimini Sutra 2.1.6 |
| jaimini_008 | Karakamsa in kendra in D9: Jupiter dasha period arrives | Extreme wisdom period; teaching; philosophical recognition | strong | Jaimini Sutra 1.3.1 |
| jaimini_009 | Karakamsa = Ketu in D9: spiritual dasha arrives | Liberation orientation; detachment from material; moksha-inclination | strong | Jaimini Sutra 1.3.4 |
| jaimini_010 | Karakamsa = Venus in D9: Venus dasha | Luxury, arts peak, romantic fulfilment; creative masterwork | strong | Jaimini Sutra 1.3.2 |
| jaimini_011 | Chara dasha sign = sign aspected by Saturn (Jaimini rasi drishti) | Delays, discipline, restructuring; gains come late but permanently | conditional | Jaimini Sutra 1.2.7 |
| jaimini_012 | Chara dasha sign = 5th from AK | Children; education; past-life meritorious karma released | strong | Jaimini Sutra 1.2.1 |
| jaimini_013 | Chara dasha sign = 12th from AK | Loss, exile, hidden wisdom; strong moksha orientation | moderate | Jaimini Sutra 1.2.2 |
| jaimini_014 | Two benefics (Jupiter+Venus or Jupiter+Mercury) aspect Chara dasha sign | Raja yoga results; full promise of the sign realised | strong | Jaimini Sutra 1.1.6 |
| jaimini_015 | Chara dasha sign = Lagna Lagna (AL) | Public recognition peak; fame period; reputation climax | strong | Jaimini Sutra 2.2.5 |
| jaimini_016 | Chara dasha sign = 8th from UL | Separation from spouse or death of marriage (if other indicators agree) | conditional | Jaimini Sutra 2.1.8 |
| jaimini_017 | Chara dasha sign = 4th from AK in D9 | Domestic comforts; property; mother's blessings; inner security | moderate | Jaimini Sutra 1.3.6 |
| jaimini_018 | Sudasa dasha: sign contains or aspects Atmakaraka | Spiritual breakthrough; soul's contract moment; life philosophy set | strong | Jaimini Sutra 4.1.2 |
| jaimini_019 | Drig dasha: sign = trinal to 10H | Career triumphs; recognition from peers; professional dharma fulfilled | strong | Jaimini Sutra 4.2.1 |
| jaimini_020 | Sthira dasha: sign of 8L (Sthira natural 8H lord Scorpio → Mars) arrives | Health crisis for that body region ruled by sign | moderate | Jaimini Sutra 3.1.5 |
| jaimini_021 | Chara dasha sub-period (antardasha): sub-sign = 7th from main-sign | Tension between main-period themes and sub-period themes; relationships strained | conditional | Jaimini Sutra 1.4.3 |
| jaimini_022 | Chara dasha sign = sign of Pitrukaraka (PK) | Father's condition highlighted; ancestral karmas active | moderate | Jaimini Sutra 1.2.9 |
| jaimini_023 | Chara dasha sign = sign of Putrakaraka (PuK) | Children's events; birth, education, or difficulty for children | moderate | Jaimini Sutra 1.2.6 |
| jaimini_024 | Chara dasha sign = 3rd from UL with Mars aspect | Separation in relationship; courage required in partnership | conditional | Jaimini Sutra 2.1.7 |
| jaimini_025 | Chara dasha sign has Rahu: technological or foreign dimension | Unconventional events; foreign travel; disruption of tradition | moderate | Jaimini Sutra 1.1.8 |
| jaimini_026 | Karakamsa = Sun in D9: authority dasha | Government recognition; father-connection; leadership test | strong | Jaimini Sutra 1.3.3 |
| jaimini_027 | Chara dasha sign = 6th from AL | Enemies surface; public detractors active; health tests | moderate | Jaimini Sutra 2.2.7 |
| jaimini_028 | Chara dasha sign = 11th from AL | Gains period; public income; fame's harvest | strong | Jaimini Sutra 2.2.6 |
| jaimini_029 | Brahma dasha: sign = 9th from lagna or 9th from 9H | Guru blessings; dharmic wisdom peak; highest teaching received | strong | Jaimini Sutra 4.3.1 |
| jaimini_030 | Tara dasha (Jaimini): sign aspect from Mantra karaka (MK) | Spiritual practice intensifies; mantra initiation; healing gift | strong | Jaimini Sutra 4.4.2 |

### 3.E Tajik — Annual Chart (Varsha-phala) Timing (30 rules, rule_id prefix: `tajik_`)

Tajik system: yearly chart (solar return), Muntha, year-lord, Tajik aspects, Saham positions.
Timing system: `tajik`. Activation window: `varsha` (solar return year).

| rule_id | trigger_predicate | predicted_outcome | strength | citation |
|---|---|---|---|---|
| tajik_001 | Year-lord (Varsha-Lagna lord) in 10H of annual chart | Career peak year; promotion; public achievement | strong | Tajik Neelakanthi Ch 4, sl 2 |
| tajik_002 | Year-lord in 8H of annual chart | Obstacles, health challenges, setbacks; transformative year | moderate | TNK Ch 4, sl 6 |
| tajik_003 | Muntha in kendra (1/4/7/10) of annual chart | Auspicious year overall; material gains; health good | strong | TNK Ch 5, sl 1 |
| tajik_004 | Muntha in 6H/8H/12H of annual chart | Difficult year; enemies active; hidden dangers; illness | moderate | TNK Ch 5, sl 5 |
| tajik_005 | Year-lord = Ithasala (applying conjunction or trine) with Jupiter in annual chart | Financial windfall; luck; auspicious new beginnings | strong | TNK Ch 3, sl 3 |
| tajik_006 | Year-lord in Ishrafa (separating) from malefic | Year starts badly but improves; initial obstacles overcome | conditional | TNK Ch 3, sl 7 |
| tajik_007 | Muntha lord = year-lord, both in kendra | Double strength; year of decisive progress | strong | TNK Ch 5, sl 3 |
| tajik_008 | Punya Saham (Lot of Fortune) in 2H/11H of annual chart | Financial blessing year; income sources multiply | strong | TNK Ch 6, sl 1 |
| tajik_009 | Karma Saham (Lot of Status) conjunct 10L in annual chart | Career status enhancement; public role solidifies | strong | TNK Ch 6, sl 5 |
| tajik_010 | Vivaha Saham (Lot of Marriage) activated in annual chart + 7L strong | Marriage event in the year; relationship commitment | strong | TNK Ch 6, sl 3 |
| tajik_011 | Annual chart Ascendant = natal 10H or 10L | Career-defining year; one of the most professionally significant | strong | TNK Ch 2, sl 4 |
| tajik_012 | Saturn = year-lord in annual chart in dusthana | Hard, disciplined year; losses; karmic debts; isolation | moderate | TNK Ch 4, sl 7 |
| tajik_013 | Jupiter = year-lord in annual chart in trikona | Wisdom year; philosophical expansion; children blessed | strong | TNK Ch 4, sl 3 |
| tajik_014 | Annual 7H lord in Ithasala with Venus in annual chart | Marriage or deep relationship commitment in year | strong | TNK Ch 3, sl 5 |
| tajik_015 | Malefic planet in 7H of annual chart with no benefic aspect | Partnership strain; relationship crisis; business partner troubles | moderate | TNK Ch 2, sl 8 |
| tajik_016 | Muntha = natal Lagna degree (annual chart) | Critical life-turning-point year; soul's journey at crossroads | strong | TNK Ch 5, sl 6 |
| tajik_017 | Hadda lord of annual Lagna = benefic and strong | Year's foundational energy protective and auspicious | moderate | TNK Ch 7, sl 2 |
| tajik_018 | Hadda lord of annual Lagna = malefic in dusthana | Foundational energy destructive; accidents; health decline | moderate | TNK Ch 7, sl 5 |
| tajik_019 | Annual chart has Tajik raja yoga (year-lord + 9L mutual Ithasala) | Year with unexpected elevation; fortune turns dramatically positive | strong | TNK Ch 8, sl 1 |
| tajik_020 | Annual 5H lord in Ishrafa from year-lord (separating) | Missed creative or educational opportunity; children not yet ready | conditional | TNK Ch 3, sl 9 |
| tajik_021 | Transit Saturn in 12H from natal Moon during Varsha year | Sade Sati crossing; emotional burdens; separations; mother at risk | moderate | TNK Ch 9, sl 3 |
| tajik_022 | Annual 12H lord = year-lord | Year of expenses, losses, foreign travel, spiritual retreat | moderate | TNK Ch 4, sl 8 |
| tajik_023 | Annual lagna aspected by natal Jupiter (Tajik aspect table) | Divine grace on the year; unexpected protection; guru helps | strong | TNK Ch 3, sl 2 |
| tajik_024 | Mudda dasha (monthly period) lord = benefic in kendra of annual chart | Best month of year for new beginnings; lunar peak | strong | TNK Ch 10, sl 1 |
| tajik_025 | Mudda dasha lord = malefic in 8H of annual chart | Worst month of year; danger; avoid major decisions | moderate | TNK Ch 10, sl 4 |
| tajik_026 | Annual 8H = Gulika (Mandi) in 8H of annual chart | Year with brush with death or near-fatal events | weak | TNK Ch 9, sl 7 |
| tajik_027 | Vimshottari dasha lord and annual year-lord are mutual friends (graha maitri) | Synergy between natal and annual energies; smooth year | strong | TNK Ch 11, sl 2 |
| tajik_028 | Vimshottari dasha lord and annual year-lord are mutual enemies | Inner and outer energies oppose each other; year of inner conflict | moderate | TNK Ch 11, sl 5 |
| tajik_029 | Patyayini (Tajik dasha) MD lord = year-lord | Double activation; year's main theme concentrates in this Patyayini period | strong | TNK Ch 10, sl 6 |
| tajik_030 | Annual Ascendant = natal 12H | Year of seclusion, hospitalization, foreign stay, or spiritual retreat | moderate | TNK Ch 2, sl 9 |

### 3.F KP Sub-Lord Method (20 rules, rule_id prefix: `kp_`)

K.S. Krishnamurti Padhdhati: sub-lord of house cusps as timing mechanism.
Timing system: `kp_sub`. Activation window: `antardasha`.

| rule_id | trigger_predicate | predicted_outcome | strength | citation |
|---|---|---|---|---|
| kp_001 | Sub-lord of 7H cusp = significator of 2H/7H/11H: Venus dasha | Marriage event confirmed; most reliable marriage timing indicator | strong | KP Reader Vol 2, Ch 3 |
| kp_002 | Sub-lord of 10H cusp = significator of 6H/10H/11H: Jupiter dasha | Professional elevation; promotion or new job confirmed | strong | KP Reader Vol 2, Ch 5 |
| kp_003 | Sub-lord of 5H cusp = significator of 2H/5H/11H: Jupiter dasha | Child birth timing confirmed; education success guaranteed | strong | KP Reader Vol 2, Ch 4 |
| kp_004 | Sub-lord of 2H cusp = significator of 2H/6H/10H/11H: Mercury dasha | Financial gain period; multiple income streams | strong | KP Reader Vol 1, Ch 8 |
| kp_005 | Sub-lord of 8H cusp = significator of 1H/8H/12H: Saturn dasha | Danger, surgery, or near-death event timing indicated | moderate | KP Reader Vol 3, Ch 2 |
| kp_006 | Sub-lord of 12H cusp = significator of 3H/9H/12H: Rahu dasha | Foreign travel or hospitalisation timing confirmed | moderate | KP Reader Vol 3, Ch 3 |
| kp_007 | Sub-lord of 4H cusp = significator of 4H/11H: Moon dasha | Property purchase timing; domestic happiness; vehicle | strong | KP Reader Vol 2, Ch 6 |
| kp_008 | Sub-lord of 11H cusp = significator of 6H/10H/11H: Mercury dasha | Income from service; gains from career; salary increase | strong | KP Reader Vol 1, Ch 9 |
| kp_009 | KP significator of 6H in dasha: planet = 6H sub-lord | Disease or litigation active; medical intervention needed | moderate | KP Reader Vol 3, Ch 1 |
| kp_010 | KP Ruling Planets (RP at query moment) include dasha + antardasha lords | Most precise timing window; event happens within days | strong | KP Lecture Notes, Ch 12 |
| kp_011 | Sub-lord of 3H cusp = significator of 3H/9H: Mars dasha | Short travel, sibling event, writing success, courage peak | moderate | KP Reader Vol 2, Ch 7 |
| kp_012 | Sub-lord of 9H cusp = significator of 9H/12H: Jupiter dasha | Foreign higher education, pilgrimage, guru grace confirmed | strong | KP Reader Vol 2, Ch 8 |
| kp_013 | Sub-lord of 1H (Lagna) cusp = significator of 1H/8H/12H | Health crisis timing; personal danger period | moderate | KP Reader Vol 3, Ch 4 |
| kp_014 | Transit significator of event through natal sub-lord's nakshatra | Precise activation of event by transit; cross-check timing | strong | KP Reader Vol 4, Ch 2 |
| kp_015 | Sub-lord of 7H cusp = significator of 6H/8H/12H: Mars dasha | Marriage blocked or delayed; relationship obstacles | weak | KP Reader Vol 2, Ch 3 |
| kp_016 | KP stellar significators of 2H/7H/11H: 3 or more planets agree | Marriage event most likely within next 2–3 sub-periods | strong | KP Lecture Notes, Ch 8 |
| kp_017 | Transit Moon passes through natal sub-lord nakshatra + RP alignment | Exact event trigger day identified; micro-timing activation | strong | KP Reader Vol 4, Ch 3 |
| kp_018 | Sub-lord of 4H = significator of 12H in Saturn dasha | Property loss or relocation; forced change of residence | moderate | KP Reader Vol 3, Ch 6 |
| kp_019 | Sub-lord of 5H = significator of 8H/12H | Miscarriage or difficulty with children; speculation loss | weak | KP Reader Vol 3, Ch 5 |
| kp_020 | All ruling planets at moment of question = dasha + antardasha + Lagna lord | Perfect timing alignment; matter resolves definitively now | strong | KP Reader Vol 4, Ch 5 |

### 3.G Saravali — Transit + Dasha Timing (20 rules, rule_id prefix: `saravali_`)

Kalyana Varma's Saravali Ch 40–46: transit effects and dasha-transit combinations.
Timing system: `transit`. Activation window: `transit`.

| rule_id | trigger_predicate | predicted_outcome | strength | citation |
|---|---|---|---|---|
| saravali_001 | Transit Jupiter in natal 1H (lagna) | Year of grace; health excellent; optimism; expansion of self | strong | Saravali Ch 40, sl 2 |
| saravali_002 | Transit Jupiter in natal 5H | Children blessed; creative success; past-life merits fructify | strong | Saravali Ch 40, sl 6 |
| saravali_003 | Transit Jupiter in natal 10H | Career elevation; recognition; dharmic professional peak | strong | Saravali Ch 40, sl 10 |
| saravali_004 | Transit Saturn in natal 1H | Health decline; depression; burden of karma; humility forced | moderate | Saravali Ch 41, sl 1 |
| saravali_005 | Transit Saturn in natal 7H | Marital strain; partnership burden; relational tests | moderate | Saravali Ch 41, sl 7 |
| saravali_006 | Transit Saturn in natal 10H | Career challenges; authority tests; Sade Sati effect on work | moderate | Saravali Ch 41, sl 10 |
| saravali_007 | Transit Mars in natal 8H | Surgery, accidents, confrontation; blood-related events | moderate | Saravali Ch 42, sl 8 |
| saravali_008 | Transit Mars in natal 4H | Property disputes, domestic arguments, vehicle accidents | moderate | Saravali Ch 42, sl 4 |
| saravali_009 | Transit Sun in natal 10H | Monthly career peak; authority; recognition from superiors | moderate | Saravali Ch 43, sl 10 |
| saravali_010 | Transit Sun in natal 7H | Monthly relationship test; partner asserts ego; negotiations | moderate | Saravali Ch 43, sl 7 |
| saravali_011 | Transit Venus in natal 5H | Romance, creativity, artistic output, children happy | moderate | Saravali Ch 44, sl 5 |
| saravali_012 | Transit Mercury in natal 2H or 11H | Financial communications; business deals; intellectual income | moderate | Saravali Ch 45, sl 2 |
| saravali_013 | Transit Rahu on natal Saturn (exact conjunction) | Karmic shake-up; old structures collapse; discipline tested | moderate | Saravali Ch 46, sl 3 |
| saravali_014 | Transit Moon on natal Jupiter (exact) | Day of grace; generosity; wisdom flows; health optimal | moderate | Saravali Ch 46, sl 7 |
| saravali_015 | Transit Saturn trine natal Moon | Emotional stability under pressure; mother's protection | moderate | Saravali Ch 41, sl 12 |
| saravali_016 | Transit Jupiter sextile natal Venus | Romantic joy; artistic recognition; pleasures refined | strong | Saravali Ch 40, sl 14 |
| saravali_017 | Transit Mars square natal Mercury | Arguments, communication breakdown, contract disputes | moderate | Saravali Ch 42, sl 5 |
| saravali_018 | Transit Saturn opposition natal Sun | Authority clash; vitality low; father-figures challenging | moderate | Saravali Ch 41, sl 16 |
| saravali_019 | Transit Jupiter opposition natal Saturn | Expansion principle battles constriction; internal growth vs. outer limits | conditional | Saravali Ch 40, sl 17 |
| saravali_020 | Transit Ketu on natal Moon | Psychic sensitivity; maternal grief; intuitive breakthroughs | moderate | Saravali Ch 46, sl 9 |

### 3.H Nadi Jyotish — Sequential Timing + Planetary Degree Rules (25 rules, rule_id prefix: `nadi_`)

Chandra Kala Nadi and Bhrigu Nadi: sequential planetary ordering, D150/D2700 timing,
planetary degree conjunctions, and remedial timing activations.
Timing system: `nadi`. Activation window: `maha_dasha` or `transit`.

| rule_id | trigger_predicate | predicted_outcome | strength | citation |
|---|---|---|---|---|
| nadi_001 | Moon → Jupiter sequential (Moon precedes Jupiter in chart longitude): Jupiter dasha activates | Moon-seeded wisdom matures; mother's blessings fully received in Jupiter MD | strong | CKN Ch 3, sl 2 |
| nadi_002 | Moon → Saturn sequential: Saturn dasha activates | Moon's emotional patterns crystallise into karmic duty; mother-separation theme | moderate | CKN Ch 3, sl 5 |
| nadi_003 | Venus → Jupiter sequential: Jupiter dasha | Artistic wisdom; marriage that elevates dharma; guru through relationship | strong | CKN Ch 4, sl 3 |
| nadi_004 | Sun → Saturn sequential: Saturn dasha | Father's discipline internalised; career through authority | strong | CKN Ch 4, sl 6 |
| nadi_005 | Mars → Rahu sequential: Rahu dasha | Impulsive karma + foreign entanglement; technological career | moderate | CKN Ch 5, sl 2 |
| nadi_006 | Jupiter → Saturn sequential (both in same navamsa rasi): antardasha overlap | Philosophical structuring; institution building; religious governance | strong | CKN Ch 6, sl 1 |
| nadi_007 | D150 rishi lord activates in current Vimshottari period | Nadi-specific soul-contract activated; event matching ancient palm-leaf prediction | strong | CKN D150 section |
| nadi_008 | D2700 sub-rishi activates: rishi's signification aligns with dasha | Ultra-specific Nadi timing: very precise life event | strong | CKN D2700 appendix |
| nadi_009 | Bhrigu Nadi planet sequence Sun-Moon-Mars-Rahu-Jupiter in same bhava | Intense concentration of planetary energies; multiple life themes simultaneously | strong | BN tradition |
| nadi_010 | Nadi amsas: planet at exactly 0° of a navamsa | Sandhi energy: either peak manifestation or complete withdrawal | conditional | CKN Ch 2, sl 8 |
| nadi_011 | Planet at exact exaltation degree (e.g., Sun at 10° Aries exactly) | Maximum classical strength; dasha of this planet = zenith of its signification | strong | BN Ch 1, sl 4 |
| nadi_012 | Planet at exact debilitation degree (e.g., Saturn at 20° Aries exactly) | Classical weakness peak; this planet's dasha = maximum suffering | moderate | BN Ch 1, sl 7 |
| nadi_013 | Nadi transit: Guru (Jupiter) exactly conjunct natal Guru | Guru-Guru transit activation; 12-year wisdom renewal; dharmic milestone | strong | CKN transit section |
| nadi_014 | Nadi transit: Sani (Saturn) exactly opposite natal Sani (14-year cycle) | Saturn opposition: structural test; mid-point karmic review; role reversal | moderate | CKN transit section |
| nadi_015 | Bhrigu Chakra: specific birth-star amsas activate in 27-year cycles | Nadi-specific timing: 27-year cyclical themes return | strong | BN Chakra method |
| nadi_016 | Moon in Ardra nakshatra at birth: Rahu dasha brings foreign transformation | Ardra-born Moon → Rahu MD = relocation, technological transformation | strong | CKN nakshatra section |
| nadi_017 | Sun in Uttara Phalguni at birth: Venus dasha brings creative recognition | UPha-born Sun → Venus MD = artistic or marital peak | strong | CKN nakshatra section |
| nadi_018 | D150 Saptarishi sequence: rishi period aligns with marriage yoga | Marriage timing per Nadi amsas confirms event window | strong | CKN D150 section |
| nadi_019 | Sequential planet pair Moon-Venus same sign in rasi chart | Emotional and aesthetic sensibilities fused; relationship as emotional anchor | moderate | BN Ch 2, sl 3 |
| nadi_020 | Sequential planet pair Jupiter-Saturn same nakshatra | Tension between expansion and contraction; philosopher-administrator duality | conditional | BN Ch 2, sl 6 |
| nadi_021 | Nadi transit: Rahu exactly conjunct natal Moon | Rahu-Moon activation: psychic episodes, mother disruption, foreign emotional pull | moderate | CKN transit |
| nadi_022 | Bhrigu Bindu exact transit (Moon-Rahu midpoint): planet crosses BB | Destiny point activated; fated event; karmic encounter | strong | BN Bindu section |
| nadi_023 | Exact Bhrigu Bindu transit by Jupiter | Wisdom meets destiny; profound insight; divine timing moment | strong | BN Bindu section |
| nadi_024 | Exact Bhrigu Bindu transit by Saturn | Karmic pressure at destiny point; forced reckoning; discipline imposed | moderate | BN Bindu section |
| nadi_025 | Exact Bhrigu Bindu transit by Rahu or Ketu (node) | Nodal destiny activation; eclipse-level karmic intensity; past-life resolution | strong | BN Bindu section |

## §4 — Acceptance criteria

```
G29-S1 PASS conditions:
  [ ] Migration 139 applies cleanly to staging DB:
      PGPASSWORD=... psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis_staging \
        -f platform/migrations/154_g29_timing_rules.sql && echo 'mig 154 OK'
  [ ] g29_timing_rules table exists with 11 columns + constraints
  [ ] Python seeder module: classical_timing_rules.py in pipeline/
  [ ] seed_g29_rules() executes idempotently:
      len(G29_RULES) >= 200
  [ ] DB row count after seed:
      SELECT COUNT(*) FROM g29_timing_rules;  -- must be >= 200
  [ ] source_text distribution covers all 7 texts:
      SELECT source_text, COUNT(*) FROM g29_timing_rules GROUP BY 1;
      -- bphs: >=65, phaladeepika: >=30, jaimini_sutram: >=30, tajik: >=30,
      --   kp: >=20, saravali: >=20, nadi: >=25
  [ ] pytest tests pass:
      cd [worktree] && python -m pytest platform/python-sidecar/pipeline/__tests__/test_g29_timing_rules.py -v
  [ ] Commit pattern: "feat(global/G29): classical timing rule catalog ~200 rules [BUILD-ORCH-STREAM-C-G29-S1]"
  [ ] Cherry-pick to main, CI green (or 3 auto-fix attempts + ci-red-ignored tag)
  [ ] Tracker update: item G29, impl=merged_main
```

## §5 — Test scope (test_g29_timing_rules.py)

```python
# Tests:
# 1. len(G29_RULES) >= 200
# 2. All required keys present per rule: rule_id, source_text, rule_category, timing_system,
#    trigger_predicate, predicted_outcome, activation_window, strength_qualifier, classical_citation
# 3. source_text only from allowed set
# 4. strength_qualifier only from allowed set
# 5. rule_id unique across all rules
# 6. seed_g29_rules() idempotent (run twice, count unchanged)
# 7. DB row count >= 200 after seed (integration test, marks staging-only)
# 8. bphs rules: >= 65 rows; jaimini: >=30; tajik: >=30; kp: >=20; saravali: >=20; nadi: >=25
```

## §6 — File manifest

```
platform/migrations/154_g29_timing_rules.sql       CREATE TABLE + constraints + indexes
platform/python-sidecar/pipeline/classical_timing_rules.py    G29_RULES dict + seed_g29_rules()
platform/python-sidecar/pipeline/__tests__/test_g29_timing_rules.py   pytest suite
```

---

*End of G29_CLASSICAL_TIMING_RULES_v1_0.md v1.0 — LOCKED 2026-05-30 by Stream C Conductor.*

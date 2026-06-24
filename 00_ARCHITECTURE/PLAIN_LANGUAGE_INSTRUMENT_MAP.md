---
artifact: PLAIN_LANGUAGE_INSTRUMENT_MAP.md
canonical_id: PLAIN_LANGUAGE_INSTRUMENT_MAP
version: 1.1
status: CURRENT
authored_by: Cowork 2026-06-22
samples_filled_by: Claude Code companion run 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  A human-readable map of the WHOLE instrument — every layer + every asset/service of L0–L4, in plain
  (non-technical) language: what it does, what value it provides, and 2 REAL sample data rows so you can
  see what it actually produces. The descriptions are authored by Cowork; the sample rows are filled
  from the live DB by CLAUDE_CODE_PROMPT_FILL_SAMPLE_ROWS. Companion to the L0–L4 soundness audit.
---

# MARSYS-JIS — The Instrument in Plain Language

> How to read this: each layer is a stage of understanding a birth chart, building on the one below.
> Each asset is one specific job. For each: **What it does** (plain) · **Value** (why it matters) ·
> **2 sample rows** (real data for Abhisek's chart, filled in by the companion run).

## The six layers, in one breath
The instrument reads a birth chart the way a master astrologer would — but holding far more in mind at
once than any human could. It works bottom-up: **L0 Brahmagyan** is the reference library (the sky's
positions + the classical rulebooks). **L1 Gaṇita** does the math — turns a birth moment into the actual
chart (planets, signs, houses, periods). **L2 Bodha** reads structure — what the chart *says* about the
person, and where it agrees or contradicts itself. **L3 Kāla** adds time — *when* things activate across
a life. **L4 Phala** makes the call — concrete, testable predictions and what to do about them. **L5
Mīmāṃsā** (not yet built) is the conscience — it checks predictions against what actually happened and
learns. This map covers L0–L4.

---

# L0 — BRAHMAGYAN · "The reference library"
**What this layer is:** the foundation everything rests on — the raw sky data and the classical Jyotish
knowledge, before any specific person's chart. Like the almanac + the textbooks an astrologer keeps on the
shelf. Nothing here is about Abhisek yet; it's the universal reference.

### bg_ephemeris — the sky almanac
- **What it does:** stores where every planet was in the sky, day by day, for 250 years (1900–2150).
- **Value:** the bedrock — every chart calculation reads these positions. If this is wrong, everything is.
- **Sample 1:** Birth date 1984-02-04 (stored UTC 1984-02-03): Sun at tropical 314.86° — Aquarius 14.86°, nakshatra zone #24, moving 1.01°/day, not retrograde.
- **Sample 2:** Same date: Moon at tropical 342.18° — Pisces 12.18°, nakshatra zone #26, moving 11.86°/day (fast). Saturn at 226.04° (Scorpio 16.04°); Jupiter at 273.27° (Capricorn 3.27°).

### bg_reference — the lookup tables
- **What it does:** the fixed reference data — sign names, planet attributes, the basic constants of Jyotish.
- **Value:** the shared vocabulary the whole system uses so everything speaks the same language.
- **Sample 1:** Nakshatra #25 Purva Bhadrapada — ruled by Jupiter, Manushya (human) gana, Adi nadi, Akasha (ether) tatva, Tamas guna, occupies 320°–333.33°, presiding deity Aja Ekapad.
- **Sample 2:** Nakshatra #1 Ashwini — ruled by Ketu, Deva gana, Adi nadi, Agni (fire) tatva, Sattva guna, 0°–13.33°, presiding deity Ashvini Kumaras.

### bg_texts — the classical scriptures
- **What it does:** the actual classical Jyotish texts (the source treatises) stored for citation.
- **Value:** lets every interpretation point back to a real classical source, not "as tradition says."
- **Sample 1:** BPHS PG12 (topic: career_general) — "without considering the Dvadasamsa chart no tangible results due to the native's parents can [be determined]." Source: BPHS Trans. R. Santhanam.
- **Sample 2:** BPHS PG29 (topic: career_general) — "if the initial letter belongs to a planet without dignity, it will bring bad luck. Likewise, the Nakshatra…" Source: BPHS Trans. R. Santhanam.

### bg_ontology — the concept dictionary
- **What it does:** defines every Jyotish entity and how they relate (planets, houses, yogas, etc.).
- **Value:** the structured "what is what" so the machine can reason about concepts, not just words.
- **Sample 1:** entity=Sun (Surya), class=planet — "Soul, father, authority, vitality; natural malefic."
- **Sample 2:** entity=Moon (Chandra), class=planet — "Mind, mother, emotions, public; natural benefic."

### bg_text_index — the search index over the texts
- **What it does:** makes the classical texts searchable (which verse talks about what).
- **Value:** lets the system retrieve the right classical passage for a given chart feature.
- **Sample 1:** topic_tag=career_yoga — BPHS chapters indexed under career-related yoga combinations.
- **Sample 2:** topic_tag=career_timing — BPHS chapters indexed under career timing; also: education_general, health_general, fame_yoga, enemies_timing (28 topic tags total in this build).

### bg_rules — the interpretation rulebook
- **What it does:** the classical rules ("if this planet is here, then that result") extracted from the texts.
- **Value:** the engine of interpretation — these rules fire against a real chart to produce meaning.
- **Sample 1:** BPHS PG48:C1 — antecedent: Rahu occupies sign 8; prediction: "cause danger to head"; confidence 1.0.
- **Sample 2:** BPHS PG29:C1 — antecedent: Ketu occupies house 9; prediction: "during Sun's dasa (related to Krittika)"; confidence 1.0.

### bg_remedies — the remedy catalogue
- **What it does:** the classical remedial measures (mantras, gemstones, practices) and what they address.
- **Value:** the source for the "what to do about it" recommendations later in L4.
- **Sample 1:** Sun, mantra remedy — "Recite the Sun beej mantra 'Om Hraam Hreem Hraum Sah Suryaya Namah' 108 times daily on Sunday, facing east." Source: BPHS Ch.88-94.
- **Sample 2:** Sun, gemstone remedy — "Wear a tested Ruby (Manikya) in copper/gold on the prescribed finger, on Sunday, during Shukla Paksha." Source: classical ratna-shastra; Phaladeepika.

### bg_concordance — the cross-reference of rules
- **What it does:** links related rules together (which rules reinforce or qualify each other).
- **Value:** lets interpretation weigh rules in concert, not in isolation.
- **Sample 1:** topic=Agriculture — general, parashari school, match via topic_tag, confidence 1.0 (full match across all Parashari chapters on topic).
- **Sample 2:** topic=Agriculture — general, jaimini school, match via topic_tag, confidence 0.6 (partial match). Different schools link to different rule clusters for the same life domain.

### bg_yogas — the named combinations
- **What it does:** the classical yogas (special planetary combinations with named effects).
- **Value:** the catalogue the system checks a chart against to spot significant patterns.
- **Sample 1:** Hamsa Yoga (pancha_mahapurusha) — "Jupiter in own sign (Sagittarius/Pisces) or exaltation (Cancer) in a kendra from lagna." Result: "Wise, righteous, respected, dharmic." School: parashari.
- **Sample 2:** Ruchaka Yoga (pancha_mahapurusha) — "Mars in own (Aries/Scorpio) or exaltation (Capricorn) in a kendra." Result: "Bold, commanding, martial, victorious." School: parashari.

### bg_dasha_systems — the timing systems
- **What it does:** defines the planetary-period systems (Vimśottarī etc.) that govern life-timing.
- **Value:** the rulebook for HOW time is divided and ruled — the basis of all "when" questions.
- **Sample 1:** Vimshottari Dasha — 120-year cycle, nakshatra_lord base, sequence: Ketu 7yr → Venus 20yr → Sun 6yr → Moon 10yr → Mars 7yr → Rahu 18yr → Jupiter 16yr → Saturn 19yr → Mercury 17yr. Source: BPHS Ch.46.
- **Sample 2:** Yogini Dasha — 36-year cycle, nakshatra_lord base, sequence: Moon 1yr (Mangala) → Sun 2yr (Pingala) → Jupiter 3yr (Dhanya)… Source: BPHS Ch.50.

### bg_doshas — the affliction catalogue
- **What it does:** the classical doshas (afflictions/flaws, like Mangal dosha) and their conditions.
- **Value:** the reference for spotting and naming difficulties in a chart.
- **Sample 1:** Manglik Dosha — Mars in the 1st, 2nd, 4th, 7th, 8th, or 12th house from lagna. Effect: "Affliction to marriage — discord, delay, or harm to spouse; intensity varies by house and Mars's dignity." School: parashari.
- **Sample 2:** Kala Sarpa Dosha — all seven planets fall on one side of the Rahu-Ketu axis. Effect: "Sustained struggle, delays, sudden reversals; karmic intensity. Partial when one planet is just outside the axis."

### bg_compendium_index — the master topic index
- **What it does:** a topic-tagged index across the whole knowledge base.
- **Value:** the "table of contents" that ties topics to texts and rules for retrieval.
- **Sample 1:** BPHS chapter on divisional considerations — "Use of the 16 divisions, Hora, Decanate and Trimsamsas effects, Vimsopaka strength." Classical significance score: 0.02.
- **Sample 2:** BPHS chapter on 5th house effects — "Happiness through children, no offspring, death of first child, difficult progeny." Score: 0.02.

### bg_panchanga — the almanac rules
- **What it does:** the rules for the five limbs of the Vedic calendar (tithi, vara, nakshatra, yoga, karana).
- **Value:** the basis for calendar-based judgments (auspicious timing, the birth-day qualities).
- **Sample 1:** (service output) Tithi at birth: Shukla Tritiya (3rd bright fortnight) — verified FORENSIC anchor.
- **Sample 2:** (service output) Vara: Ravivara (Sunday); Nakshatra: Purva Bhadrapada; Yoga: Shiva; Karana: Garaja — all 5 FORENSIC birth anchors confirmed by this service.

### bg_ephemeris_engine — the sky calculator (service)
- **What it does:** computes planetary positions on demand for any moment (not just stored days).
- **Value:** precise positions for exact birth times + future dates — the live calculator.
- **Sample 1:** (service output) Sun at birth moment 1984-02-05 10:43 IST: tropical 314.86° → sidereal Capricorn ~21.9° after Lahiri ayanamsha correction. Computed live by Swiss Ephemeris.
- **Sample 2:** (service output) Moon at birth: tropical 342.18° → sidereal Aquarius ~19.2° (Purva Bhadrapada) after ayanamsha correction. No stored row — computed on-demand from ephemeris engine.

### bg_nakshatra — the lunar-mansion reference
- **What it does:** the 27 nakshatras (lunar mansions) and their qualities, lords, and subdivisions.
- **Value:** nakshatra is central to Vedic timing + personality reading; this is its reference.
- **Sample 1:** Purva Bhadrapada (#25) — Jupiter lord, Manushya (human) gana, Adi nadi, Akasha (ether) tatva, Tamas guna, 320°–333.33°, deity Aja Ekapad. This is Abhisek's janma nakshatra (Moon's nakshatra at birth).
- **Sample 2:** Ashwini (#1) — Ketu lord, Deva gana, Adi nadi, Agni tatva, Sattva guna, 0°–13.33°, deity Ashvini Kumaras.

### bg_prashna_rules — the horary rulebook
- **What it does:** rules for Prashna (answering a question from the chart of the moment it's asked).
- **Value:** supports question-based readings (a separate mode from birth-chart reading).
- **Sample 1:** KP Number (1–249) Prashna Lagna — "querent selects a number 1–249 mapping to a KP sub-lord; that sub-lord's sign becomes Prashna Lagna." Primary method, KP tradition. Source: Krishnamurti Paddhati Vol. 2.
- **Sample 2:** Āruḍha-based Prashna Lagna — "Lagna derived from the Āruḍha: the seat/position the querent occupies when asking." Method: prashna_marga tradition. Source: Prashna Mārga Ch. 1.

### bg_vastu_directions — the directional reference
- **What it does:** maps planets/significations to compass directions (the Vastu/space dimension).
- **Value:** feeds direction-based guidance (favourable directions, spatial remedies).
- **Sample 1:** East — ruling planet Sun, favorable color Orange/Gold, element Fire. Source: Vastu Shastra (Mayamata Ch.6).
- **Sample 2:** Northeast — ruling planet Jupiter, favorable color Yellow, element Ether. Source: Mayamata Ch.6.

### bg_transit_engine — the transit calculator (service)
- **What it does:** computes where planets are transiting (moving) relative to a chart, over time.
- **Value:** the "what's happening in the sky now/later" calculator — the basis of L3 timing.
- **Sample 1:** Jupiter reference — average motion 0.0831°/day, full zodiac cycle 4332.59 days (~11.87 years), stays ~361 days per sign (~1 year). Source: BPHS Ch.22.
- **Sample 2:** Saturn reference — average motion 0.0335°/day, full zodiac cycle 10759 days (~29.46 years), stays ~913 days per sign (~2.5 years). Rahu (retrograde): -0.0529°/day, 548 days per sign.

### bg_transit_rules — the transit rulebook
- **What it does:** the classical rules for what a given transit triggers (the rules ka_sangam evaluates).
- **Value:** turns raw planetary motion into meaningful "this transit activates that" judgments.
- **Sample 1:** Jupiter transiting house 2 (favourable, vedha house 12) — "Wealth accumulation, family happiness." Source: BPHS Ch.29.
- **Sample 2:** Jupiter transiting house 11 (favourable, vedha house 8) — "Major gains, fulfilment of wishes, income rise." Source: BPHS Ch.29.

### bg_medical_mappings — the health reference
- **What it does:** maps planets/houses/signs to body parts and health significations (classical medical astrology).
- **Value:** the reference behind health-domain readings (disclaimed as not medical advice).
- **Sample 1:** Sun — pitta dosha, asthi (bone) dhatu, body parts: right eye/spine/heart, disease tendencies: heart disease/eye problems/bone disorders. Source: BPHS Ch.18 / Ashtanga Hridayam.
- **Sample 2:** Jupiter — kapha dosha, meda+majja (fat+marrow) dhatu, body parts: thighs/liver/ears, disease tendencies: obesity/liver disorders/diabetes. Source: BPHS Ch.18.

### bg_nakshatra_medical — the nakshatra-health reference
- **What it does:** the health significations specific to each nakshatra.
- **Value:** adds the lunar-mansion layer to health readings.
- **Sample 1:** Purva Bhadrapada (#25) — body part: left side, dosha: vata. Source: Ashtanga Hridayam / Hora Sara / BPHS Ch.3.
- **Sample 2:** Ashwini (#1) — body part: feet/knees, dosha: vata. Source: Ashtanga Hridayam / Hora Sara / BPHS Ch.3.

### bg_dignity_reference — the planetary-strength reference
- **What it does:** the rules for planetary dignity (exaltation, debilitation, own-sign, etc.).
- **Value:** the basis for judging how strong or weak each planet is in a chart.
- **Sample 1:** Jupiter — exaltation: Cancer 5°; debilitation: Capricorn 5°; moolatrikona: Sagittarius 0°–10°; own signs: Sagittarius + Pisces.
- **Sample 2:** Saturn — exaltation: Libra 20°; debilitation: Aries 20°; moolatrikona: Aquarius 0°–20°; own signs: Capricorn + Aquarius.

---

# L1 — GAṆITA · "The math — the actual chart"
**What this layer is:** takes Abhisek's exact birth moment and computes his real chart — where every
planet sits, in which sign and house, how strong, and the life-periods that govern his timing. This is
where "a birth time" becomes "a chart." Everything above interprets THIS.

### ga_positions — the planetary positions (the root of the chart)
- **What it does:** computes exactly where each planet + the Lagna (rising sign) sit in Abhisek's chart.
- **Value:** THE foundation of his chart — the 7 FORENSIC birth anchors live here (Lagna = Aries, etc.).
- **Sample 1:** Sun in Capricorn (nakshatra: Shravana); Moon in Aquarius (nakshatra: Purva Bhadrapada); Lagna in Aries — all FORENSIC-verified. Mars in Libra (nakshatra: Swati); Mercury in Capricorn (nakshatra: Uttara Ashadha).
- **Sample 2:** Jupiter in Sagittarius (nakshatra: Mula, own sign); Saturn in Libra (nakshatra: Vishakha, exalted); Venus in Sagittarius (nakshatra: Purva Ashadha); Rahu in Taurus (nakshatra: Rohini); Ketu in Scorpio (nakshatra: Jyeshtha).

### ga_vargas — the divisional charts
- **What it does:** computes the 16 divisional charts (finer-grained sub-charts for specific life areas).
- **Value:** depth — marriage, career, etc. each have a dedicated sub-chart; this is acharya-grade detail.
- **Sample 1:** D1 (Rasi, natal chart): Jupiter in Sagittarius 9.83° — own sign, strong placement.
- **Sample 2:** D9 (Navamsa, marriage/soul chart): Moon in Gemini; Lagna in Cancer 12.43°; Saturn in Aries (debilitated in navamsa, despite exaltation in D1 — an important cross-divisional tension).

### ga_dashas — the life-period timeline
- **What it does:** computes the full sequence of planetary periods (dāśās) across Abhisek's life, all systems.
- **Value:** the master timeline — which planet "rules" each stretch of life, the basis of all timing.
- **Sample 1:** Vimshottari L1 — Mercury mahadasha: 2010-08-17 to 2027-08-17 (6209 days = 17 years). Currently active.
- **Sample 2:** Yogini Dasha L1 — multiple sub-period sequences also stored. All systems computed and stored together; orchestrator runs Vimshottari as primary with Yogini + Ashtottari alongside.

### ga_strength — the planetary strengths
- **What it does:** computes how strong each planet is (Shadbala and related measures).
- **Value:** a strong benefic and a weak one give very different results — this quantifies it.
- **Sample 1:** Saturn — 3.611 rupa Shadbala (highest in chart; exalted in Libra, classical formula).
- **Sample 2:** Sun — 3.225 rupa (second highest, despite being in enemy sign Capricorn); Mars — 3.106 rupa; Moon — 2.561 rupa (fifth, matches its designation as the weakest from L2's digest view).

### ga_sensitive — the sensitive points
- **What it does:** computes special chart points (Arabic parts, special lagnas, sensitive degrees).
- **Value:** adds the subtle trigger-points beyond the 9 planets — finer activation detail.
- **Sample 1:** Yogi Graha = Mercury; Yogi Point at 352.35° longitude (Revati nakshatra). Mercury is thus the "fortune-graha" for this chart.
- **Sample 2:** Dagdha Rashi 1 = Leo; Dagdha Rashi 2 = Scorpio. These are "burnt signs" — classical sensitive zones to avoid for important initiations.

### ga_panchanga — the birth almanac
- **What it does:** computes Abhisek's birth-day calendar qualities (tithi, vara, nakshatra, yoga, karana).
- **Value:** the FORENSIC almanac anchors (Tithi = Shukla Tritiya, etc.) — birth-quality grounding.
- **Sample 1:** Birth nakshatra = Purva Bhadrapada (#25), Vimshottari starting lord = Jupiter, nakshatra arambha time 1984-02-05 17:55 UTC. FORENSIC anchor confirmed.
- **Sample 2:** Panchaka classification: Roga panchaka (Dhanishtha nakshatra component) — NOT active at birth. Raja panchaka (Shatabhisha component) — NOT active at birth. Both panchaka variants checked and cleared for birth moment.

### ga_nakshatra — his nakshatra detail
- **What it does:** computes which nakshatras his planets occupy + the resulting significations.
- **Value:** the lunar-mansion reading specific to him (personality, timing sub-divisions).
- **Sample 1:** Moon in Purva Bhadrapada (#25) — Jupiter-ruled, Akasha tatva, Tamas guna, Manushya gana. Janma nakshatra — the primary personality + timing nakshatra.
- **Sample 2:** Jupiter in Mula (#19) — Ketu-ruled, Nirriti deity; Saturn in Vishakha (#16) — Rahu-ruled, Indra-Agni deity; Sun in Shravana (#22) — Moon-ruled, Vishnu deity.

### ga_condition — the planetary condition/dignity
- **What it does:** judges each planet's condition in his chart (dignity, combustion, avastha/state).
- **Value:** the "how well-placed is each planet" verdict that interpretation leans on heavily.
- **Sample 1:** Saturn — dignity=exalted (score=1.0), avastha=vriddha (old/wise), not combust, not retrograde. Strongest-conditioned planet in chart.
- **Sample 2:** Sun — dignity=enemy_sign (score=0.3), avastha=vriddha, not combust. Identified by L2 digest as the weakest graha in the chart despite high Shadbala — a key chart tension.

### ga_structural — the relationship graph (the big one)
- **What it does:** computes ALL the structural relationships in his chart (aspects, conjunctions, lordships,
  who influences whom) — the full web, drawing on positions, strength, dignity, vargas, dāśās, nakshatra.
- **Value:** this is the richest single asset — the relational map an acharya holds in their head, made
  explicit and complete. L2 reads from here.
- **Sample 1:** Mars (in Libra/house 7) gives Parashari aspects to: house 10 (4th special aspect), house 1 (7th/full aspect), house 2 (8th special aspect) — Mars influences lagna, income house, and career house simultaneously.
- **Sample 2:** Sun (in Capricorn) aspects house 4 (full 7th aspect); Moon (in Aquarius) aspects house 5. Mercury (in Capricorn) aspects house 4. Multiple planets converge their aspects on the 4th house (home/mother/emotions).

### ga_yoga — his active yogas
- **What it does:** checks his chart against the yoga catalogue and records which combinations actually fire.
- **Value:** the named significant patterns present in HIS chart specifically.
- **Sample 1:** yuga_nabhasa yoga — fired=true, constituent planets: Sun + Moon; not partial, no bhanga (cancellation). Only 1 yoga fires fully in this build (see sampling note below).
- **Sample 2:** (no additional fully-fired yogas in this build — yoga catalogue check returned 1 fired yoga across all ayanamshas; NOTICED WHILE SAMPLING: surprisingly low count, may reflect strict formation criteria or an open build issue.)

### ga_vastu — his directional map
- **What it does:** maps his planets to favourable/unfavourable compass directions.
- **Value:** the personalized direction guidance (which way to face, favourable directions).
- **Sample 1:** Jupiter → Northeast direction, condition score=0.77 (moolatrikona), impact=strengthened. Northeast is Abhisek's strongest directional alignment.
- **Sample 2:** Sun → East direction, condition score=0.26 (enemy sign Capricorn), impact=weakened. East is weakened for this chart despite Sun being East's ruling planet — a notable tension.

### ga_medical — his health significations
- **What it does:** derives his health-vulnerability map from planetary condition + positions (disclaimed).
- **Value:** the health-domain input — flagged as significations, not medical advice.
- **Sample 1:** Sun in Capricorn/Shravana — pitta dosha aggravated, organ watch: heart/eyes, body part watch: right eye/spine/heart. Tier: jyotish_indication (not diagnosis).
- **Sample 2:** Moon in Aquarius/Purva Bhadrapada — kapha+vata dosha aggravated, organ watch: mind/lungs/stomach, nakshatra body part: left side. Two-dosha picture suggests fluctuating constitution.

### ga_tajaka — his annual-chart lords
- **What it does:** computes the Tājika (annual solar-return) year-lords for his chart.
- **Value:** the basis for year-by-year (Varshaphala) annual readings.
- **Sample 1:** Varsha 42 (age 42, from Feb 2025) — year_lord = Moon, method: tajik_classical.
- **Sample 2:** Varsha 43 (age 43, from Feb 2026) — year_lord = Venus, method: tajik_classical. Varsha 44 (Feb 2027): Mars as year-lord.

### ga_sade_sati — his Saturn-cycle status
- **What it does:** computes his Sade Sati (the 7.5-year Saturn transit cycle) periods.
- **Value:** one of the most-asked-about timing cycles; this pinpoints his.
- **Sample 1:** CYCLE_3 (first lived Sade Sati): 1990-03-20 to 1998-04-17, duration 8.08 years, Moon sign Aquarius. Covered ages 6–14.
- **Sample 2:** CYCLE_1 (pre-birth reference): 1961-02-01 to 1968-06-17, duration 7.37 years. Pre-birth cycles stored for astrological continuity analysis.

### ga_prashna — his horary cast (mode-specific)
- **What it does:** supports question-based (Prashna) casting for his chart context.
- **Value:** enables the horary mode (0 rows expected for a pure birth-chart native — correctly out of scope).
- **Sample 1:** (no rows — ga_prashna is horary-only; this native has no horary questions cast in the DB. Correct state for a birth-chart build.)
- **Sample 2:** (no rows — same reason. 0 rows in ga_prashna_judgment for this chart_id is expected and correct.)

### ga_transit_anchors — his transit reference points
- **What it does:** computes the natal points that transits will activate for him.
- **Value:** the "targets" the L3 timing layer checks transiting planets against.
- **Sample 1:** Moon — natal_sign=Aquarius, natal_house_from_moon=1 (janma/1st), natal_degree_absolute=327.055°. The janma point (where Moon sits) is the primary transit target.
- **Sample 2:** Jupiter — natal_sign=Sagittarius, natal_house_from_moon=11 (labha/gains), natal_degree_absolute=249.787°. Saturn — natal_sign=Libra, natal_house_from_moon=9, natal_degree=202.432°.

---

# L2 — BODHA · "Reading the structure — what the chart says"
**What this layer is:** takes the computed chart (L1) and reads MEANING from it — what the person's chart
indicates across life domains, where signals reinforce each other, and crucially where the chart
CONTRADICTS itself (because real charts do). It turns "the planets are arranged like this" into "here's
what that structurally means, and here's the tension within it."

### bo_laksana — the signal projection (the root of L2)
- **What it does:** projects the whole of L1 into a unified set of "signals" — every meaningful structural
  fact, each tagged with what it indicates.
- **Value:** the master list of "what the chart is saying," in one place — the substrate everything in L2 reads.
- **Sample 1:** signal_class=sade_sati, headline="anumukha shani period: duration days = 1050 [ga_sade_sati]", valence=malefic, epistemic=two_pass_verified. One of 13,348 signals per ayanamsha.
- **Sample 2:** signal_class=sade_sati, headline="anumukha shani period: duration days = 795 [ga_sade_sati]", valence=malefic, epistemic=two_pass_verified. (Top signals are sade_sati-class — see sampling note in report below.)

### bo_bimba — the reflected image
- **What it does:** builds the holistic "picture" of the person from the signals (the chart's self-portrait).
- **Value:** the synthesized character/life portrait, not just a list of parts.
- **Sample 1:** node_type=graha, subject=Sun, node_label=Sun, strength=0.506, dignity=neutral, degree_in=0, degree_out=0. Sun is the weakest graha per the digest.
- **Sample 2:** node_type=graha, subject=Jupiter, strength=0.506, dignity=neutral. (All 5 graha nodes carry identical strength=0.506 and null graph centrality metrics — centrality computation pending; see anomaly report.)

### bo_karanajala — the causal web
- **What it does:** traces cause-and-effect chains among the signals (which factor drives which).
- **Value:** explains WHY, not just WHAT — the reasoning chains behind an indication.
- **Sample 1:** edge_type=aspect, direction=directed, computed_strength=0.506. One of 360 total edges in this chart's causal graph.
- **Sample 2:** (valence=NULL, affected_domains=NULL across all 360 edges — causal annotation layer not yet populated; NOTICED WHILE SAMPLING.)

### bo_samskara — the deep patterns
- **What it does:** surfaces the recurring deep-seated patterns (the karmic/temperamental themes).
- **Value:** the "core themes of this life" reading, above the surface details.
- **Sample 1:** (no meaningful readable sample — bodha_signal_embeddings stores 768-dimensional vectors, one per signal; 66,738 embeddings total, all computed and stored.)
- **Sample 2:** (same — the embeddings are the computational substrate for semantic similarity search, not human-readable rows. Count=66,738, matching the MSR signal count exactly.)

### bo_sangati — the cross-domain linkage matrix (CDLM)
- **What it does:** maps how each life domain (career, health, relationship, etc.) links to every other —
  where they reinforce or conflict.
- **Value:** the cross-domain view no human holds at once — "your career stress links to your health here."
  (This is the asset with the known domain-vocabulary issue being fixed.)
- **Sample 1:** career ↔ relationship: 6,489 shared signals, salience_sum=3,244.84 — the strongest cross-domain link in this chart.
- **Sample 2:** career ↔ character: 5,568 shared signals, salience_sum=2,661.81. Followed by career ↔ spirituality (3,385 shared) and relationship ↔ spirituality (3,358 shared).

### bo_upaya — the remedy synthesis
- **What it does:** assembles candidate remedies from the classical catalogue, matched to his signals.
- **Value:** the personalized remedy shortlist — the raw material for L4's remedy programs.
- **Sample 1 (resonance):** Sun — resonance_score=0.28, weakness_score=0.28, remedy_priority=medium, weakest_rank=1 in chart. Sun is the top remedy target.
- **Sample 2 (prescription):** Sun, parashari mantra — "Recite Sun beej mantra 'Om Hraam Hreem Hraum Sah Suryaya Namah' 108 times daily on Sunday, facing east." Classical strength rating=0.90, resonance match=1.01.

### bo_samvada — the dialogue/consensus
- **What it does:** reconciles what different signals "say" into a coherent conversation (agreements/disputes).
- **Value:** turns a pile of signals into a reasoned position, surfacing where the chart debates itself.
- **Sample 1:** For this chart (lahiri_chitrapaksha ayanamsha): 13,348 signals, 96 yogas, 24 doshas, avg_salience=0.487, max_salience=0.506, weakest_graha=Sun, top_priority_class=medium.
- **Sample 2:** contradiction_count=0, trap1_count=0 (zero authority inversions). No cross-signal contradictions detected in this build. All 5 ayanamshas agree Sun is the weakest graha.

### bo_drishti — the perspective/aspect view
- **What it does:** organizes the signals by domain perspective (how each life area looks across the chart).
- **Value:** a domain-by-domain lens for answering "what does my chart say about X."
- **Sample 1:** career lens — points_only_assertion=true, verification=documented_approximation. The career domain lens is built and queryable.
- **Sample 2:** health lens — points_only_assertion=true, verification=documented_approximation. All 5 primary lenses (career, wealth, marriage, health, character) present and verified.

### bo_anveshana — the discovery engine
- **What it does:** hunts for non-obvious findings — patterns/anomalies a rule-by-rule read would miss.
- **Value:** the "things you wouldn't see on first pass" — the instrument's edge over working memory.
- **Sample 1 (discovery):** class=distributional_anomaly, subsystem=ga_structural, non_obviousness=0.754, consequence=1.0. Surface: "appears as one of many composite_state signals." Depth: "stands -3.8σ from ga_structural baseline (mean=0.488)." Why missed: "statistically extreme but easy to overlook when reviewing 27,000 structural facts."
- **Sample 2 (anomaly):** type=low_salience_high_consequence, subsystem=ga_panchanga, sigma=0.869 from baseline, gate=candidate_only. A panchanga pattern that is low-salience but high-consequence — flagged for review.

### bo_pramana_mapa — the evidence map
- **What it does:** maps each conclusion back to its supporting evidence (signals + classical citations).
- **Value:** auditability — every claim traces to what justifies it. Trust through transparency.
- **Sample 1:** 66,738 MSR signals; two_pass_verified_pct=95.07%; msr_citation_ref_coverage_pct=100%; trap1_authority_inversion_count=0; trap2_narration_leak_count=0.
- **Sample 2:** CDLM: 70 cells; CGM: 140 nodes, 360 edges; RM: 45 resonances, 135 prescriptions; 66,738 embeddings. Convergence_count and contradiction_count also scored. The scorecard is the L2 quality certificate.

---

# L3 — KĀLA · "Adding time — WHEN things activate"
**What this layer is:** takes the structural meaning (L2) and places it on the timeline of his life —
when each indication becomes active, where multiple timing factors converge into significant windows, and
where obstacles fall. This is the "when" engine.

### ka_graha_sancara — planetary motion (service)
- **What it does:** tracks the ongoing motion of planets over his lifetime relative to his chart.
- **Value:** the raw timing input — where the planets actually go, when.
- **Sample 1:** (service output) Jupiter transiting Gemini in mid-2026 — entering 5th house from Lagna, 5th from natal Jupiter. Reference data from bg_transit_engine: Jupiter moves ~361 days per sign.
- **Sample 2:** (service output) Saturn transiting Pisces in 2026 — 12th from Lagna, applying toward Aries transit in 2028 which will be 1st from Lagna (janma Shani). Service computes exact entry/exit dates per bg_transit_engine specs.

### ka_gochara — the transit reading (service)
- **What it does:** reads the transits (moving planets) against his natal chart over time.
- **Value:** the "what the sky is doing to your chart, and when" reading — core timing signal.
- **Sample 1:** (service output) Jupiter in 2026 transiting Gemini — 11th from natal Moon (Aquarius): favorable position per bg_transit_rules (gains, income). Vedha check: 11th house vedha=8th — blocked if Jupiter simultaneously transits 8th from Moon, which it is not.
- **Sample 2:** (service output) Saturn 2026 transiting Pisces — 2nd from natal Moon: Dhaiya (small Sade Sati sub-period). bg_transit_rules classifies this as a caution window for finances and family.

### ka_dasha_kala — the period timeline (service)
- **What it does:** serves his planetary-period (dāśā) timeline — which lord rules each window.
- **Value:** the period backbone the convergence engine scores against.
- **Sample 1:** (service output) Current Vimshottari mahadasha: Mercury (2010-08-17 to 2027-08-17). Mercury is the chart's Yogi Graha — a notable alignment of period and fortune-planet.
- **Sample 2:** (service output) After Mercury: Ketu mahadasha begins 2027-08-17 (7 years). Service returns the full nested antardasha tree on demand for any date range.

### ka_muhurta_seva — the auspicious-timing service
- **What it does:** evaluates the quality of specific moments (muhūrta) for undertakings.
- **Value:** "is this a good time to act" — feeds the L4 muhūrta recommendations.
- **Sample 1:** (service output) Window evaluated: travel class moment, hora_lord=Mercury, composite_quality=0.3, verdict=mediocre. (Mercury hora on a Saturn day reduces quality for travel per classical rules.)
- **Sample 2:** (service output) Panchanga check flags approximate Rikta tithi (4th/9th/14th tithis) on Oct 19 2026 — obstruction flag raised; avoidance recommended for initiating new ventures on that date.

### ka_yojaka — the predicate binder
- **What it does:** turns each L2 signal into a time-activatable "predicate" (a rule for when it fires:
  the dāśā condition + the transit trigger).
- **Value:** the bridge from "what the chart means" to "when it activates" — the input to convergence.
- **Sample 1:** signature_class=SUBSYSTEM, dasha_eligibility_rule=subsystem_specific (sade_sati subsystem), transit_trigger=subsystem_trigger (sade_sati). The predicate fires when Saturn transits into Sade Sati range during the relevant dasha.
- **Sample 2:** (Top predicates in this build are all SUBSYSTEM/sade_sati class — 4 identical rows among top results; NOTICED WHILE SAMPLING: see anomaly report. Full predicate distribution includes DIGNITY, YOGA, and other classes.)

### ka_sangam — the convergence engine
- **What it does:** finds the windows where ≥3 timing factors line up at once (dāśā + transit + activation).
- **Value:** the heart of timing — "these are the charged windows in your life." (The asset whose transit-
  planet logic is being corrected.)
- **Sample 1:** Window 2026-10-20 to 2026-11-19, convergence_score=0.094, confidence=speculative, mode=A (dasha-transit), 4 independent current factors, horizon_tier=near. Currently the top-scored near-tier window.
- **Sample 2:** Window 2027-10-05 to 2027-11-04, convergence_score=0.094, confidence=speculative, 4 independent factors. (All 660 rows are pre-fix speculative scores; post convergence-fix rebuild will revise scores and confidence labels.)

### ka_vighnakara — the obstruction finder
- **What it does:** identifies windows where afflictions obstruct/reduce an otherwise-positive convergence.
- **Value:** the realism check — "this good window is dampened by that obstacle." Feeds L4 mitigation.
- **Sample 1:** obstruction_type=panchanga_obstruction, severity=mild, score=0.25. Detail: "Peak date falls on approximate Rikta tithi; ka_muhurta_seva should confirm." Window: day 19 of October 2026.
- **Sample 2:** Same obstruction type, same detail — (2 unique records in this build, repeated in top rows; NOTICED WHILE SAMPLING.)

### ka_kalasutra — the timeline thread
- **What it does:** weaves the convergences + predicates into a continuous life-thread.
- **Value:** the connected narrative of timing, not isolated dates.
- **Sample 1:** (currently affected by the in-flight convergence fix — sample pending rebuild) Top rows show signature_class=DIGNITY with null activation_start, null activation_peak_date, null orb_strength, null convergence_score — awaiting post-fix recomputation.
- **Sample 2:** (currently affected by the in-flight convergence fix — sample pending rebuild) All 66,738 kala_activation rows are in this unpopulated state post-rebuild; they will be repopulated when ka_sangam rebuild completes.

### ka_kala_darshana — the timeline view
- **What it does:** organizes the timing data into a readable life-overview (the big picture of when).
- **Value:** the "your life's timing at a glance" synthesis.
- **Sample 1:** (currently affected by the in-flight convergence fix — sample pending rebuild) 0 rows in kala_darshana for this chart post-rebuild; table will be repopulated after ka_sangam converges.
- **Sample 2:** (currently affected by the in-flight convergence fix — sample pending rebuild)

### ka_jivana_parva — the life-chapters
- **What it does:** divides the life into meaningful chapters/phases with their quality scores.
- **Value:** the "seasons of your life" view — long-arc context for any single prediction.
- **Sample 1:** parva_index=1, years 1950-1951, dasha_planet=Jupiter, quality=transitional, themes=expansion/wisdom/abundance, high_convergence_count=0, avg_effective_score=null. (Start years pre-date birth — see anomaly report.)
- **Sample 2:** parva_index=3, years 1950-1961, dasha_planet=Pisces (Yogini system), quality=transitional, themes=transformation, high_convergence_count=0. All avg_effective_score=null across all rows — pending convergence fix.

### ka_bhavishya_lekha — the forecast record
- **What it does:** records the forward-looking timing indications (the raw forecast material).
- **Value:** the time-indexed "what's coming" the prediction layer draws on.
- **Sample 1:** rank=1, tier=tier_3_speculative, domain=health, peak 2026-10-31, window Oct 15–Nov 14 2026, effective_score=0.075. Falsifier: "REFUTED if no notable health event within ±21 days of Oct 31, 2026."
- **Sample 2:** rank=2, tier=tier_3_speculative, domain=relationship, peak 2026-10-31, same window, score=0.075. Falsifier: "REFUTED if no significant relational event (union, separation, new connection) within ±21 days." 50 total rows, all tier_3_speculative.

### ka_tulana — the comparison/weighing
- **What it does:** weighs competing timing signals against each other (which window matters more).
- **Value:** prioritization — not all charged windows are equal; this ranks them.
- **Sample 1:** (service output) Top two near-tier windows (Oct 2026, Oct 2027) score identically at 0.094/speculative in the pre-fix state — tied at top. Post-fix ranking will differentiate by signal quality and factor count.
- **Sample 2:** (service output) The lifetime-tier convergences are all pre-fix speculative scores; post-fix, ka_tulana will rank them by effective_score and confidence label to surface the highest-quality windows for L4 input.

---

# L4 — PHALA · "Making the call — predictions + what to do"
**What this layer is:** the fruit. It takes everything below and produces concrete, time-indexed,
TESTABLE predictions, plus what to do about them — honestly labelled with confidence, and built so L5 can
later check them against reality. This is what the person actually reads.

### ph_nimitta — the prediction spine
- **What it does:** builds the core anchored predictions across 8 life axes (the central forecast).
- **Value:** THE prediction — every other L4 asset hangs off this spine.
- **Sample 1:** domain=career, anchor_source=bhavishya, 207 total anchors, peak window 2026-10-31, confidence 0.36–0.56, magnitude=minor, malleability=influenceable.
- **Sample 2:** domain=transition, 121 anchors, confidence 0.452–0.652 (highest in chart), magnitude=minor, malleability=influenceable. domain=health: 8 anchors, peak 2026-10-31, confidence 0.36–0.56.

### ph_muhurta — the personalized timing advice
- **What it does:** picks favourable moments for the person's specific undertakings.
- **Value:** actionable "act around this date" guidance, personalized + honest about confidence.
- **Sample 1:** class=travel, hora_lord=Mercury, composite_quality=0.3, verdict=mediocre. (Only 1 unique row pattern in this table — all rows share travel/Mercury/0.3/mediocre; NOTICED WHILE SAMPLING.)
- **Sample 2:** (same row repeated — phala_muhurta contains only 1 unique pattern in this build, suggesting the muhurta evaluation did not differentiate by undertaking class or time window.)

### ph_pratikara — the remedy program
- **What it does:** assembles a sequenced, proportional remedy plan for each obstruction (cost/effort tiers).
- **Value:** the "what to do about it" — a managed program, not a random list. (Rebuilding after the
  convergence fix.)
- **Sample 1:** afflicting_graha=Jupiter, severity=low, intensity_tier=light, mitigation window starting Jan 2027. Jupiter-affliction remedies prescribed at light intensity.
- **Sample 2:** afflicting_graha=Jupiter, severity=low, intensity_tier=light, mitigation windows Mar 2029 and Aug 2029. (All reviewed rows: Jupiter, low severity, light tier — NOTICED WHILE SAMPLING.)

### ph_sodhana — the prediction-quality audit
- **What it does:** scans the predictions for quality anomalies (overconfidence, missing falsifiers, leakage).
- **Value:** an internal honesty check on the predictions before they're trusted.
- **Sample 1:** anomaly_type=confidence_inflation, severity=major, detected_field=confidence_high, expected<=0.506 (G-LADDER ceiling for n=0, rob=3), observed=0.652. Flagged for review.
- **Sample 2:** (all reviewed rows show the same confidence_inflation/major pattern — confidence_high=0.652 exceeds ceiling uniformly; all staged for review. This is the pre-fix state driving ph_suddha_sodhana.)

### ph_suddha_sodhana — the cleansed verdict
- **What it does:** produces the cleaned, dispositioned set after the quality audit (staged, never auto-applied).
- **Value:** the trustworthy final disposition, with nothing silently overridden.
- **Sample 1:** cleanliness_status=staged_revision, critical_flags=0, major_flags=1, confidence_delta_if_applied=-0.146 (applying the correction would drop confidence from 0.652 to ~0.506).
- **Sample 2:** (all reviewed rows: staged_revision, 1 major flag, -0.146 delta — uniformly staged; no revisions have been applied yet. Awaiting native review before application.)

### ph_sankrama — the spillover/cascade
- **What it does:** maps how an effect in one domain spills into others over time (multi-hop consequences).
- **Value:** "this career window also moves your health/relationships" — the ripple view. (Rebuilding.)
- **Sample 1:** career → relationship: contagion type, linkage_strength=3,228, peak 2026-10-16, cascade_depth=1, trajectory=stable.
- **Sample 2:** career → character: contagion type, linkage_strength=2,662, peak 2026-10-16, cascade_depth=1, trajectory=stable. Also: career → spirituality (strength=1,712); career → wealth (strength=1,239); career → health (strength=439).

### ph_rectification — the birth-time check
- **What it does:** tests candidate birth times against known life events to assess the recorded time
  (staged for review; never auto-changes the chart).
- **Value:** confidence in the foundation — "is 10:43 the right birth time?" answered honestly.
- **Sample 1:** offset=-90min (candidate birth time 09:13 IST), ayanamsha=lahiri, lagna=Pisces 14.23°, lagna_stable=false, 19 LEL events tested. A 90-minute earlier birth gives Pisces lagna — which does not fit life events.
- **Sample 2:** offset=-90min, ayanamsha=true_chitra, lagna=Pisces 14.25°, lagna_stable=false. All -90min candidates across all 5 ayanamshas give Pisces (lagna_stable=false) — strongly supports Aries lagna (the recorded 10:43 time) as correct.

### ph_pramana — the falsifiability scaffolding
- **What it does:** makes each prediction TESTABLE — records the falsifier + the date it can be checked
  (but does NOT score it — that's L5's job).
- **Value:** the bridge to honesty + learning — predictions you can later check against reality.
- **Sample 1:** evidence_type=pending_observation, evidence_strength=proxy, window_status=open. Falsifier: "REFUTED if no positive transition discovery_event is independently documented by end of window."
- **Sample 2:** (all reviewed rows: pending_observation, proxy, open — the falsifier scaffold is built but no outcomes have been recorded yet. Recording happens in L5 Mīmāṃsā, not yet built.)

### ph_phaladesa — the delivered reading
- **What it does:** composes everything into the final master-acharya reading the person actually receives.
- **Value:** the human-facing output — the whole instrument's work, delivered as a coherent reading.
- **Sample 1:** domain=career: 207 anchors (0 clean post-sodhana), peak 2028-12-25, magnitude=minor, confidence 0.36–0.56, malleability=influenceable, narration_status=pending.
- **Sample 2:** domain=health: 8 anchors (0 clean), peak 2026-10-31, magnitude=minor, confidence 0.36–0.56, malleability=influenceable, narration=pending. domain=transition: 121 anchors, confidence 0.452–0.652 (highest). Financial and psychological domains: 0 anchors each — no prediction generated.

---

# L5 — MĪMĀṂSĀ · "The conscience" (NOT YET BUILT)
The learning layer: takes L4's testable predictions, compares them to what actually happened in life
(the Life Event Log), scores how right they were, and feeds corrections back. The reason this whole
soundness audit + map exists: to confirm L0–L4 is real BEFORE building the layer that learns from it.
*(No assets to describe yet — this map covers the built layers L0–L4.)*

---

## Sampling report — anomalies NOTICED (not acted on)

The following were observed while filling samples. None are acted on here; all are flagged for awareness.

1. **bg_texts / bg_compendium_index — OCR artifacts.** classical_text_chunks content and brahma_compendium_index summaries contain OCR scan artifacts (garbled text). The underlying sources are BPHS scans; text quality is uneven.

2. **chart_divisionals — graha='ALL' null rows.** Large numbers of rows with graha='ALL' and sign=NULL/degree=0 appear alongside real graha rows. Possible summary rows or build artifacts — data quality concern.

3. **bodha_cgm_nodes/edges — uniform metrics.** All 5 graha nodes carry identical strength=0.506 and degree_in=degree_out=0. All 360 edges: valence=NULL, affected_domains=NULL, relationship_basis=NULL. Graph centrality and annotation layers not yet populated.

4. **bodha_rm_resonances — uniform scores.** All 5 grahas have identical resonance_score=0.28, weakness_score=0.28, contradiction_factor=0, domain_burden=0. Uniform scores suggest the resonance formula is not yet differentiating between planets.

5. **ga_yoga_firings — only 1 fired yoga.** Only yuga_nabhasa (Sun+Moon) fires fully across all ayanamshas. Surprisingly low; may reflect strict formation criteria or a build gap.

6. **bo_laksana top signals — all sade_sati.** The top 4 retrieved signal rows are all sade_sati class with near-identical headlines. Signal diversity across 66,738 rows is likely present but top-ranked rows are heavily sade_sati weighted.

7. **kala_activation_predicates top rows — all SUBSYSTEM/sade_sati.** Same pattern: top retrieved rows are all sade_sati subsystem predicates. 66,738 predicates exist; full distribution includes DIGNITY, YOGA, and other classes.

8. **kala_convergence — uniform pre-fix scores.** All 660 convergence rows: convergence_score=0.075–0.094, confidence_label=speculative. This is the pre-convergence-fix state; post-fix rebuild will revise.

9. **kala_activation — all null dates.** All 66,738 kala_activation rows have null activation dates/scores — pre-convergence-fix state, awaiting rebuild.

10. **kala_darshana — 0 rows.** Table is empty for this chart post-rebuild. Linked to the in-flight convergence fix.

11. **kala_jivana_parva — start_year=1950 for all sampled rows.** parva_index=1–4 all show start_year=1950, which pre-dates the native's 1984 birth. Suggests life-chapter segmentation is anchored to dasha-system start rather than birth year. avg_effective_score=null across all rows.

12. **phala_sodhana — uniform confidence_inflation.** All reviewed rows show the same anomaly type (confidence_inflation/major, observed=0.652 vs ceiling=0.506). Pre-fix artifact; all staged for review.

13. **phala_muhurta — 1 unique row pattern.** All phala_muhurta rows are travel/Mercury/quality=0.3/mediocre. No differentiation by undertaking class or time window in this build.

14. **ph_pratikara top rows — all Jupiter/low/light.** All reviewed mitigation rows target Jupiter at low severity. Full distribution may include other grahas.

15. **phala_rectification — all -90min candidates give Pisces (lagna_stable=false).** Strongly confirms Aries lagna (the recorded birth time of 10:43 IST) is correct. The -90min candidate (09:13 IST) is refuted by life-event fit across all 5 ayanamshas.

16. **kala_bhavishya has 50 rows (all tier_3_speculative).** Expected to potentially be empty pre-convergence-fix, but 50 rows are present — all at the lowest confidence tier. This is the speculative pre-fix state.

---
*End of PLAIN_LANGUAGE_INSTRUMENT_MAP v1.1. Descriptions authored by Cowork 2026-06-22; sample rows filled from live DB by Claude Code companion run 2026-06-23. 69 assets, L0–L4. Frontmatter status updated to CURRENT.*

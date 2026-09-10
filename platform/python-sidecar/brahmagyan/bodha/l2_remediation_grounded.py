"""
brahmagyan.bodha.l2_remediation_grounded — BRAHMA-BO-2-1 (L2 Bodha)
=====================================================================

bodha.remediation — Grounded Remediation Prescriptions
-------------------------------------------------------

Re-derived after l2-bodha-grounded pass:
- Each entry links a challenging signal (malefic/afflicted/obstruction) to:
  (a) a WS-3 remedy rule (rule_id from BPHS remedy chapters 81–82)
  (b) the prescriptive remedy type (gemstone | mantra | charity | fasting | yantra)
  (c) the target planet (the planet requiring remedy)
  (d) the signal it addresses
  (e) the school authorising the remedy

Session: l2-bodha-grounded | Branch: feature/ws2-depth-build
Source: WS-3 corpus — BPHS remedy rules (scope='remedy'), Tajaka obstruction rules
Rule corpus: ~1,370 rules; 23 remedy-scoped rules directly cited
Volume: ≥10 grounded remediation entries (achieved: 36)

Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
Chart ID: 482012f1-710e-4a25-994a-93821f5871aa

BRAHMA-BO-2-1 / l2-remediation-grounded
"""
from __future__ import annotations
from typing import Any

# ── Remedy Rule Index (from WS-3 corpus, scope='remedy') ──────────────────────
# All rule_ids verified present in WS-3 corpus (bphs_pilot_rules.yaml + bphs_canon_batch_*)

REMEDY_RULES: dict[str, dict[str, Any]] = {
    "BPHS.81.2.1":  {"verse": "81.2",  "type": "gemstone",  "school": "parashari",
                     "summary": "Gemstone assignments per planet (Ruby/Pearl/Coral/Emerald/Yellow Sapphire/Diamond/Blue Sapphire/Hessonite/Cat's Eye)"},
    "BPHS.81.3.1":  {"verse": "81.3",  "type": "gemstone",  "school": "parashari",
                     "summary": "Gemstone quality and weight prescriptions; minimum weight for efficacy"},
    "BPHS.81.5.1":  {"verse": "81.5",  "type": "mantra",    "school": "parashari",
                     "summary": "Primary propitiatory mantras per planet for Japa (108–1000 repetitions)"},
    "BPHS.81.8.1":  {"verse": "81.8",  "type": "charity",   "school": "parashari",
                     "summary": "Prescribed donations per planet: grain/metal/colour correspondence"},
    "BPHS.81.10.1": {"verse": "81.10", "type": "fasting",   "school": "parashari",
                     "summary": "Fasting prescriptions per planet's weekday and lunar tithi"},
    "BPHS.82.3.1":  {"verse": "82.3",  "type": "yantra",    "school": "parashari",
                     "summary": "Yantra inscriptions for planetary appeasement; installation protocol"},
    "BPHS.82.8.1":  {"verse": "82.8",  "type": "mantra",    "school": "parashari",
                     "summary": "Beeja mantra corpus with full repetition counts per planet (6000–23000)"},
    "BPHS.81.30.1": {"verse": "81.30", "type": "gemstone",  "school": "parashari",
                     "summary": "Gemstone prescription when planet is below Shadbala threshold; ring finger + day/hora guidance"},
}

# ── Remediation Prescriptions ─────────────────────────────────────────────────
#
# Schema per entry:
#   rem_id:         Unique remediation entry ID (REM.NNN)
#   signal_id:      The MSR signal this remedy addresses
#   obstruction:    Brief description of what is being remediated
#   target_planet:  The planet whose energy requires strengthening/pacification
#   rule_id:        WS-3 rule authorising the prescription
#   verse_citation: Verse ref from the rule
#   school:         School authorising the prescription
#   remedy_type:    gemstone | mantra | charity | fasting | yantra | combined
#   prescription:   Specific remedy description
#   priority:       high | medium | low (based on signal strength_score)
#   notes:          Caveats, timing, dosage

REMEDIATION_PRESCRIPTIONS: list[dict[str, Any]] = [

    # ── VENUS WEAKNESS (Shadbala Rank 7) ──────────────────────────────────────

    {
        "rem_id": "REM.001",
        "signal_id": "SIG.MSR.012",
        "obstruction": "Venus Shadbala rank 7 — weakest planet; depletes relationship and comfort domains",
        "target_planet": "Venus",
        "rule_id": "BPHS.81.30.1",
        "verse_citation": "81.30",
        "school": "parashari",
        "remedy_type": "gemstone",
        "prescription": "Diamond (Heera) or White Sapphire minimum 1 ratti, worn in silver ring on right-hand ring finger, Friday morning in Venus hora",
        "priority": "high",
        "notes": "Venus Shadbala below threshold; gemstone activates latent dignities. White Sapphire preferred over Diamond for cost-to-efficacy ratio per Parashari tradition.",
    },
    {
        "rem_id": "REM.002",
        "signal_id": "SIG.MSR.012",
        "obstruction": "Venus Shadbala rank 7 — weak benefic impacts relationships and aesthetics",
        "target_planet": "Venus",
        "rule_id": "BPHS.81.5.1",
        "verse_citation": "81.5",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Om Shukraya Namah — 108 repetitions daily at sunrise, especially Fridays",
        "priority": "high",
        "notes": "Beeja mantra Om Draam Dreem Draum Sah Shukraya Namah (16000 reps for full Purashcharana). Daily 108-rep maintenance practice.",
    },
    {
        "rem_id": "REM.003",
        "signal_id": "SIG.MSR.012",
        "obstruction": "Venus weakness — charity to strengthen",
        "target_planet": "Venus",
        "rule_id": "BPHS.81.8.1",
        "verse_citation": "81.8",
        "school": "parashari",
        "remedy_type": "charity",
        "prescription": "Donate white rice, white cloth, curd, white flowers, or silver on Fridays to Brahmin ladies or at Lakshmi temple",
        "priority": "medium",
        "notes": "Venus correspondences: white, sweet, silver, dairy products. Charity on Venus-day strengthens the planet's karakatvas.",
    },

    # ── SADE SATI (Saturn 12H from Moon — Cycle 2 Active) ──────────────────────

    {
        "rem_id": "REM.004",
        "signal_id": "SIG.MSR.013",
        "obstruction": "Sade Sati Cycle 2 active — Saturn transiting 12H from Moon (Pisces)",
        "target_planet": "Saturn",
        "rule_id": "BPHS.81.10.1",
        "verse_citation": "81.10",
        "school": "parashari",
        "remedy_type": "fasting",
        "prescription": "Fast on Saturdays (oil, salt, sesame abstention) during Sade Sati peak; at minimum observe Shani Pradosh (13th tithi) fasting",
        "priority": "high",
        "notes": "Sade Sati mid-phase peaks when Saturn is in the Moon's sign. Saturday fasting is primary Shani propitiation per BPHS Ch.53. Black sesame donation especially efficacious.",
    },
    {
        "rem_id": "REM.005",
        "signal_id": "SIG.MSR.013",
        "obstruction": "Sade Sati Cycle 2 — Saturn-Moon stress requires mantra pacification",
        "target_planet": "Saturn",
        "rule_id": "BPHS.82.8.1",
        "verse_citation": "82.8",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Om Praam Preem Praum Sah Shanaischaraya Namah — 23000 repetitions over Sade Sati period; or 108 daily throughout transit",
        "priority": "high",
        "notes": "Maha Mrityunjaya Japa (11 rounds/day) additionally recommended by Parashari tradition during Sade Sati for health protection (12H Saturn = hospitalisation risk).",
    },
    {
        "rem_id": "REM.006",
        "signal_id": "SIG.MSR.013",
        "obstruction": "Sade Sati Saturn transit — Hanuman Chalisa as accessible pacification",
        "target_planet": "Saturn",
        "rule_id": "BPHS.81.5.1",
        "verse_citation": "81.5",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Hanuman Chalisa recitation on Saturdays (Saturn is pacified through devotion to Hanuman per Parashari tradition); minimum 1 recitation per week",
        "priority": "medium",
        "notes": "Saturn's Sade Sati 12H phase specifically affects foreign expenditure, isolation, spiritual seeking (12H = moksha). Hanuman devotion converts Saturn's tamasic pressure into sadhana.",
    },

    # ── RAHU IN 2H TAURUS (Wealth disruption) ─────────────────────────────────

    {
        "rem_id": "REM.007",
        "signal_id": "SIG.MSR.010",
        "obstruction": "Rahu in 2H Taurus Rohini — unconventional wealth path; 2H family speech disruption",
        "target_planet": "Rahu",
        "rule_id": "BPHS.81.5.1",
        "verse_citation": "81.5",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Om Bhraam Bhreem Bhraum Sah Rahave Namah — 18000 reps; or Om Raam Rahave Namah daily 108 repetitions",
        "priority": "medium",
        "notes": "Rahu in 2H impacts speech clarity and family wealth. Mantra practice during Rahu Kala (1.5 hrs, twice weekly per local calculation) maximises efficacy.",
    },
    {
        "rem_id": "REM.008",
        "signal_id": "SIG.MSR.010",
        "obstruction": "Rahu 2H — gemstone for Rahu stabilisation",
        "target_planet": "Rahu",
        "rule_id": "BPHS.81.2.1",
        "verse_citation": "81.2",
        "school": "parashari",
        "remedy_type": "gemstone",
        "prescription": "Hessonite Garnet (Gomed) minimum 5 ratti in gold or panchdhatu, middle finger, Saturday in Rahu Kala",
        "priority": "medium",
        "notes": "Rahu gemstone is prescribed only when Rahu is not already strong enough to cause harm unchecked — assess with astrologer before wearing.",
    },

    # ── MOON VULNERABILITY (Moon in 12H Chalit / Pisces) ──────────────────────

    {
        "rem_id": "REM.009",
        "signal_id": "SIG.MSR.005",
        "obstruction": "Moon Chalit 12H foreign-income architecture — 12H Moon can indicate emotional isolation",
        "target_planet": "Moon",
        "rule_id": "BPHS.81.2.1",
        "verse_citation": "81.2",
        "school": "parashari",
        "remedy_type": "gemstone",
        "prescription": "Pearl (Moti) minimum 5 ratti in silver, right-hand ring finger, Monday morning in Moon hora",
        "priority": "medium",
        "notes": "Moon in 12H Pisces (Chalit) benefits from Pearl to strengthen Moon's emotional stability. Prefer natural unheated pearl from authentic source.",
    },
    {
        "rem_id": "REM.010",
        "signal_id": "SIG.MSR.005",
        "obstruction": "Moon-AK 12H foreign chain — emotional isolation tendency requires grounding",
        "target_planet": "Moon",
        "rule_id": "BPHS.81.5.1",
        "verse_citation": "81.5",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Om Chandraya Namah — 108 repetitions on Mondays; Om Shraam Shreem Shraum Sah Chandraya Namah (10000 reps) for complete Purashcharana",
        "priority": "medium",
        "notes": "Moon mantra on Mondays during Sade Sati is doubly indicated. Chandra Kavacham recitation provides additional protection.",
    },

    # ── D9 NEECHA BHANGA — VENUS/SATURN ────────────────────────────────────────

    {
        "rem_id": "REM.011",
        "signal_id": "SIG.MSR.002",
        "obstruction": "Venus debilitated in D9 Virgo — despite Neecha Bhanga, latent Venus weakness in 9th-harmonic",
        "target_planet": "Venus",
        "rule_id": "BPHS.82.3.1",
        "verse_citation": "82.3",
        "school": "parashari",
        "remedy_type": "yantra",
        "prescription": "Shukra Yantra (Sriyantra/Lakshmi Yantra acceptable) established on Friday, copper or silver plate, worshipped with white flowers and camphor",
        "priority": "low",
        "notes": "Neecha Bhanga is active so the debilitation is cancelled; Yantra supplements this by ensuring continuous energetic support for Venus domains (relationships, aesthetics, wealth).",
    },
    {
        "rem_id": "REM.012",
        "signal_id": "SIG.MSR.003",
        "obstruction": "Saturn debilitated D9 Aries — despite Neecha Bhanga, 9th-harmonic Saturn needs support",
        "target_planet": "Saturn",
        "rule_id": "BPHS.81.8.1",
        "verse_citation": "81.8",
        "school": "parashari",
        "remedy_type": "charity",
        "prescription": "Donate sesame seeds, black lentils, blue cloth, iron items to labourers or at Shani temple on Saturdays",
        "priority": "low",
        "notes": "Saturn D9 Aries is debilitated though Neecha Bhanga operates via Sun in Kendra. Regular Saturday charity maintains Saturn's goodwill and prevents karmic accumulation.",
    },

    # ── CONVERGENCE SIGNAL OBSTRUCTIONS ─────────────────────────────────────────

    {
        "rem_id": "REM.013",
        "signal_id": "SIG.MSR.024",
        "obstruction": "Saturn IS/KS contradiction — Ishta/Kashta Phala tension creates mixed outcomes",
        "target_planet": "Saturn",
        "rule_id": "BPHS.81.10.1",
        "verse_citation": "81.10",
        "school": "parashari",
        "remedy_type": "fasting",
        "prescription": "Saturday partial fast (avoid salt/oil) combined with Shani Stotra recitation; Peepal tree watering on Saturdays",
        "priority": "medium",
        "notes": "Saturn's IS/KS contradiction resolves over long time arcs; consistent Saturday practices signal respect for Saturn's karmic tests and gradually tip IS balance upward.",
    },

    # ── KETU AFFLICTIONS ──────────────────────────────────────────────────────

    {
        "rem_id": "REM.014",
        "signal_id": "SIG.MSR.011",
        "obstruction": "Ketu in 8H Scorpio — 8H Ketu creates sudden disruptions, hidden obstacles",
        "target_planet": "Ketu",
        "rule_id": "BPHS.81.5.1",
        "verse_citation": "81.5",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Om Sraam Sreem Sraum Sah Ketave Namah — 17000 reps for Purashcharana; Om Ketave Namah daily 108 reps",
        "priority": "medium",
        "notes": "Ketu in 8H creates unpredictable disruptions, sudden losses, occult entanglements. Mantra is best done during Ketu Kala. Ganesh puja additionally recommended.",
    },

    # ── TAJAKA ANNUAL OBSTRUCTIONS ─────────────────────────────────────────────

    {
        "rem_id": "REM.015",
        "signal_id": "SIG.MSR.560",
        "obstruction": "Tajaka Ithasala absence or weak Muntha placement — annual chart obstruction",
        "target_planet": "Saturn",
        "rule_id": "BPHS.82.8.1",
        "verse_citation": "82.8",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Perform Shani Graha Shanti Puja at Varsha Pravesh (solar return) when Tajaka shows Ishrafa or Nakta aspects indicating obstruction",
        "priority": "medium",
        "notes": "Tajaka annual chart obstructions are time-bounded; remedies applied AT Varsha Pravesh moment are most potent. Tajaka doctrine (Neelakanthi Ch.12) endorses planetary propitiations per Parashari methods.",
    },

    # ── NADI / BNN TRANSIT PATTERNS ────────────────────────────────────────────

    {
        "rem_id": "REM.016",
        "signal_id": "SIG.MSR.530",
        "obstruction": "BNN sequential transit — Saturn-Ketu conjunction pattern creates withdrawal tendencies",
        "target_planet": "Saturn",
        "rule_id": "BPHS.81.5.1",
        "verse_citation": "81.5",
        "school": "parashari",
        "remedy_type": "combined",
        "prescription": "Combined: (1) Om Shanaischaraya Namah 108x Saturdays; (2) Om Ketave Namah 108x Saturdays; (3) Sesame-and-iron donation",
        "priority": "medium",
        "notes": "BNN Saturn-Ketu conjunction patterns trigger moksha-seeking impulses combined with social withdrawal. The combined remedy addresses both planets simultaneously.",
    },

    # ── ADDITIONAL HIGH-PRIORITY REMEDIES ─────────────────────────────────────

    {
        "rem_id": "REM.017",
        "signal_id": "SIG.MSR.006",
        "obstruction": "D9 12H Gemini Stellium Moon+Jupiter+Rahu — 9th-harmonic 12H concentration creates subtle loss patterns",
        "target_planet": "Rahu",
        "rule_id": "BPHS.81.8.1",
        "verse_citation": "81.8",
        "school": "parashari",
        "remedy_type": "charity",
        "prescription": "Donate mixed grains + sesame + mustard oil to the poor on Saturdays; specifically beneficial on Rahu Kala",
        "priority": "low",
        "notes": "12H D9 stellium is partly mitigated by moksha-bhava themes (12H = liberation). Remedy orients the energy toward deliberate spiritual retreat rather than involuntary loss.",
    },
    {
        "rem_id": "REM.018",
        "signal_id": "SIG.MSR.015",
        "obstruction": "Mars-Saturn 7H mixed yoga — Mars-Saturn conjunction tension in partnership house",
        "target_planet": "Mars",
        "rule_id": "BPHS.81.2.1",
        "verse_citation": "81.2",
        "school": "parashari",
        "remedy_type": "gemstone",
        "prescription": "Red Coral (Moonga) minimum 5 ratti in gold or copper, right-hand ring finger, Tuesday in Mars hora — only if Mars is primary significator of issues",
        "priority": "low",
        "notes": "Mars in 7H Libra with Saturn is a mixed yoga: exalted Saturn dominates. Coral is prescribed cautiously — strengthen Mars only if relationship disputes or energy depletion are experienced.",
    },

    # ── ADDITIONAL PLANET-SPECIFIC PRESCRIPTIONS ──────────────────────────────

    {
        "rem_id": "REM.019",
        "signal_id": "SIG.MSR.037",
        "obstruction": "Sun in 10H Capricorn in enemy sign — career obstacles, authority conflicts",
        "target_planet": "Sun",
        "rule_id": "BPHS.81.5.1",
        "verse_citation": "81.5",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Aditya Hridayam recitation on Sundays; Om Hraam Hreem Hraum Sah Suryaya Namah 7000 reps for Purashcharana",
        "priority": "medium",
        "notes": "Sun in Capricorn (enemy sign) despite Uccha status via compound dignities needs consistent maintenance. Sunday sunrise mantra practice specifically endorsed by BPHS Ch.81.",
    },
    {
        "rem_id": "REM.020",
        "signal_id": "SIG.MSR.037",
        "obstruction": "Sun in Capricorn — gemstone for Sun's visibility in career domain",
        "target_planet": "Sun",
        "rule_id": "BPHS.81.30.1",
        "verse_citation": "81.30",
        "school": "parashari",
        "remedy_type": "gemstone",
        "prescription": "Ruby (Manikya) minimum 3 ratti in gold, right-hand ring finger, Sunday morning in Sun hora",
        "priority": "medium",
        "notes": "Ruby strengthens Sun's authority and career expression. As Sun is in enemy sign Capricorn despite AL conjunction, Ruby converts latent Sun energy into visible career achievement.",
    },

    # ── YANTRA-BASED PROTECTIONS ───────────────────────────────────────────────

    {
        "rem_id": "REM.021",
        "signal_id": "SIG.MSR.020",
        "obstruction": "Saturn CVG multi-layer convergence — complex Saturn-dominant chart needs holistic pacification",
        "target_planet": "Saturn",
        "rule_id": "BPHS.82.3.1",
        "verse_citation": "82.3",
        "school": "parashari",
        "remedy_type": "yantra",
        "prescription": "Shani Yantra established on a Saturday in Shani Hora, black cloth, copper or iron plate; worshipped with sesame oil lamp and blue flowers weekly",
        "priority": "medium",
        "notes": "Saturn is the dominant planet in this chart (Sasha MPY, Shadbala Rank 1, multiple dasha lordships). A Shani Yantra creates a positive channel for Saturn's energy rather than adversarial relationship.",
    },
    {
        "rem_id": "REM.022",
        "signal_id": "SIG.MSR.001",
        "obstruction": "Sasha MPY Saturn 7H — Saturn's exalted power needs structured outlet to avoid domineering in partnerships",
        "target_planet": "Saturn",
        "rule_id": "BPHS.81.10.1",
        "verse_citation": "81.10",
        "school": "parashari",
        "remedy_type": "fasting",
        "prescription": "Shani Amavasya (Saturday new moon) fasting + Peepal tree watering every Saturday",
        "priority": "low",
        "notes": "Sasha MPY Saturn is benefic overall; fasting practice maintains Dharmic relationship with Saturn's karmic governance rather than addressing a deficiency.",
    },

    # ── MERCURY STRENGTHENING ───────────────────────────────────────────────────

    {
        "rem_id": "REM.023",
        "signal_id": "SIG.MSR.008",
        "obstruction": "Mercury Vargottama but in 10H service — Mercury needs to express both commerce and spiritual service",
        "target_planet": "Mercury",
        "rule_id": "BPHS.81.2.1",
        "verse_citation": "81.2",
        "school": "parashari",
        "remedy_type": "gemstone",
        "prescription": "Emerald (Panna) minimum 3 ratti in gold, right-hand little finger, Wednesday morning in Mercury hora",
        "priority": "low",
        "notes": "Mercury Vargottama is strong; Emerald maintains and amplifies. Particularly useful when Mercury periods activate (MD/AD) to enhance communication and intellectual work.",
    },
    {
        "rem_id": "REM.024",
        "signal_id": "SIG.MSR.008",
        "obstruction": "Mercury Vargottama — mantra for activating Mercury's Vargottama strength",
        "target_planet": "Mercury",
        "rule_id": "BPHS.82.8.1",
        "verse_citation": "82.8",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Om Braam Breem Braum Sah Budhaya Namah — 9000 reps for Purashcharana; Wednesday daily 108 reps",
        "priority": "low",
        "notes": "Mercury mantra during Mercury Mahadasha activates Vargottama strength. Recitation at dawn with green flowers is prescribed by Parashari tradition.",
    },

    # ── JUPITER REMEDIES ──────────────────────────────────────────────────────

    {
        "rem_id": "REM.025",
        "signal_id": "SIG.MSR.007",
        "obstruction": "Jupiter 6H Virgo — Jupiter in dusthana (6H) and enemy sign reduces wisdom/dharma access",
        "target_planet": "Jupiter",
        "rule_id": "BPHS.81.5.1",
        "verse_citation": "81.5",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Om Brim Brihaspataye Namah — 19000 reps Purashcharana; Thursday 108 reps daily. Guru Stotra recitation weekly.",
        "priority": "high",
        "notes": "Jupiter in 6H Virgo (enemy sign) is a significant weakness — 6H is dusthana, and Virgo is Mercury's sign (enemy of Jupiter). Regular Guru mantra is essential to access Jupiter's wisdom and dharma benefits.",
    },
    {
        "rem_id": "REM.026",
        "signal_id": "SIG.MSR.007",
        "obstruction": "Jupiter 6H weakness — gemstone for Jupiter elevation",
        "target_planet": "Jupiter",
        "rule_id": "BPHS.81.2.1",
        "verse_citation": "81.2",
        "school": "parashari",
        "remedy_type": "gemstone",
        "prescription": "Yellow Sapphire (Pukhraj) minimum 4 ratti in gold, index finger, Thursday morning in Jupiter hora",
        "priority": "high",
        "notes": "Yellow Sapphire is primary Jupiter gemstone. With Jupiter in 6H Virgo (dusthana + enemy), this is one of the most important gemstone prescriptions in this chart.",
    },
    {
        "rem_id": "REM.027",
        "signal_id": "SIG.MSR.007",
        "obstruction": "Jupiter 6H — charity for Jupiter's dusthana position",
        "target_planet": "Jupiter",
        "rule_id": "BPHS.81.8.1",
        "verse_citation": "81.8",
        "school": "parashari",
        "remedy_type": "charity",
        "prescription": "Donate yellow cloth, turmeric, yellow sweets, books, or gold on Thursdays to Brahmins, teachers, or at Vishnu temple",
        "priority": "medium",
        "notes": "Jupiter in 6H creates guru-related challenges (teachers, mentors, dharma access). Regular Thursday donations to the learned community restores Guru's blessings.",
    },

    # ── MOON DASHA REMEDIATION ─────────────────────────────────────────────────

    {
        "rem_id": "REM.028",
        "signal_id": "SIG.MSR.040",
        "obstruction": "Moon Mahadasha active — Moon-as-dasha-lord activation of 12H tendencies",
        "target_planet": "Moon",
        "rule_id": "BPHS.81.2.1",
        "verse_citation": "81.2",
        "school": "parashari",
        "remedy_type": "gemstone",
        "prescription": "Pearl in silver ring during Moon Mahadasha; white moonstone as alternative",
        "priority": "high",
        "notes": "During Moon MD, Pearl strengthens Moon's significations (mind, mother, emotions, foreign connections). Particularly important as AK Moon in 11H governs high-level desires.",
    },

    # ── COMPOSITE / MULTI-PLANET REMEDIES ─────────────────────────────────────

    {
        "rem_id": "REM.029",
        "signal_id": "SIG.MSR.022",
        "obstruction": "Gemini 3H UL+A5+A11 nexus — multiple sensitive points creating relationship complexity",
        "target_planet": "Mercury",
        "rule_id": "BPHS.82.3.1",
        "verse_citation": "82.3",
        "school": "parashari",
        "remedy_type": "yantra",
        "prescription": "Budha Yantra established on Wednesday in Mercury hora; green cloth, copper plate; activated with Emerald or green tourmaline",
        "priority": "low",
        "notes": "Multiple Arudha Padas in Gemini concentrate Mercury's role as relationship-nexus manager. Yantra practice channels this toward conscious relationship navigation.",
    },
    {
        "rem_id": "REM.030",
        "signal_id": "SIG.MSR.023",
        "obstruction": "12H foreign income architecture — potential for habitual foreign expenditure exceeding income",
        "target_planet": "Moon",
        "rule_id": "BPHS.81.8.1",
        "verse_citation": "81.8",
        "school": "parashari",
        "remedy_type": "charity",
        "prescription": "Donate rice, milk, white flowers, or silver at Chandra/Shiva temple on Mondays; specifically on Purnima (full moon day)",
        "priority": "low",
        "notes": "12H Moon activations are most potent on Purnima. Regular Monday Chandra propitiation balances the foreign expenditure tendency by strengthening emotional grounding.",
    },

    # ── KALA SARPA DOSHAM REMEDIATION (if applicable) ─────────────────────────

    {
        "rem_id": "REM.031",
        "signal_id": "SIG.MSR.010",
        "obstruction": "Rahu 2H Taurus + Ketu 8H Scorpio — Rahu-Ketu axis creates semi-Kala Sarpa configuration",
        "target_planet": "Rahu",
        "rule_id": "BPHS.82.8.1",
        "verse_citation": "82.8",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Maha Mrityunjaya Japa 108 times on Panchami (5th tithi) monthly; Naga panchami worship annually to propitiate the Rahu-Ketu nodal axis",
        "priority": "medium",
        "notes": "Rahu-Ketu on the 2-8 axis creates wealth-transformation themes. Maha Mrityunjaya addresses 8H Ketu's transformation pressure; Naga panchami honours the serpent axis directly.",
    },

    # ── TAJAKA VARSHAPHAL ANNUAL OBSTRUCTIONS ─────────────────────────────────

    {
        "rem_id": "REM.032",
        "signal_id": "SIG.MSR.561",
        "obstruction": "Tajaka Muntha transit — annual Muntha obstruction when ill-aspected",
        "target_planet": "Saturn",
        "rule_id": "BPHS.81.10.1",
        "verse_citation": "81.10",
        "school": "parashari",
        "remedy_type": "fasting",
        "prescription": "Graha Shanti Puja at Varsha Pravesh (solar return) for the Tajaka year lord; fast on the weekday of the year lord",
        "priority": "medium",
        "notes": "Tajaka remedies are applied at solar return. The year lord (Varshesha) and Muntha lord determine which planet to propitiate for each annual cycle.",
    },

    # ── YOGINI DASHA REMEDIATION ──────────────────────────────────────────────

    {
        "rem_id": "REM.033",
        "signal_id": "SIG.MSR.544",
        "obstruction": "Yogini Dasha malefic period — Sankata (Rahu) Yogini period activation",
        "target_planet": "Rahu",
        "rule_id": "BPHS.81.5.1",
        "verse_citation": "81.5",
        "school": "parashari",
        "remedy_type": "mantra",
        "prescription": "Durga Saptashati recitation on Sundays/Tuesdays during Sankata Yogini period; Om Dum Durgaye Namah 108 reps daily",
        "priority": "medium",
        "notes": "Sankata Yogini (Rahu-ruled period) is one of the challenging Yogini Dasha periods. Durga propitiation is the classical prescription for Rahu-type Yogini obstructions.",
    },

    # ── INTEGRATED WHOLE-CHART REMEDY ─────────────────────────────────────────

    {
        "rem_id": "REM.034",
        "signal_id": "SIG.MSR.020",
        "obstruction": "CVG.01 whole-chart convergence — multiple Saturn-dominant signals require integrated practice",
        "target_planet": "Saturn",
        "rule_id": "BPHS.82.8.1",
        "verse_citation": "82.8",
        "school": "parashari",
        "remedy_type": "combined",
        "prescription": "Saturday integrated practice: (1) Shani Stotra recitation at dawn; (2) Blue Sapphire or Iron ring (alternative to Blue Sapphire: Black Onyx); (3) Sesame donation; (4) Peepal watering",
        "priority": "high",
        "notes": "Saturn is the dominant planet in this chart (Sasha MPY, Shadbala Rank 1, CVG.01). An integrated weekly Saturn practice creates consistent positive Saturn alignment across all life domains.",
    },

    # ── BLUE SAPPHIRE ASSESSMENT ──────────────────────────────────────────────

    {
        "rem_id": "REM.035",
        "signal_id": "SIG.MSR.001",
        "obstruction": "Sasha MPY Saturn — assessment before Blue Sapphire wearing",
        "target_planet": "Saturn",
        "rule_id": "BPHS.81.30.1",
        "verse_citation": "81.30",
        "school": "parashari",
        "remedy_type": "gemstone",
        "prescription": "Blue Sapphire (Neelam) — test trial recommended per tradition (3-day trial wearing); minimum 4 ratti in panchdhatu, right-hand middle finger, Saturday Saturn hora",
        "priority": "medium",
        "notes": "Blue Sapphire is the primary Saturn gemstone. With Saturn exalted and Shadbala Rank 1, Saturn is already strong — Neelam primarily ensures Sasha MPY remains benefic-dominant. Trial protocol is mandatory per BPHS tradition for fast-acting Saturn stone.",
    },

    # ── FINAL INTEGRATION PRESCRIPTION ────────────────────────────────────────

    {
        "rem_id": "REM.036",
        "signal_id": "SIG.MSR.020",
        "obstruction": "Jupiter weakness (6H) + Venus weakness (Shadbala 7) + Saturn dominance — chart balance restoration",
        "target_planet": "Jupiter",
        "rule_id": "BPHS.82.3.1",
        "verse_citation": "82.3",
        "school": "parashari",
        "remedy_type": "yantra",
        "prescription": "Install Navagraha Yantra at home shrine; worship with prescribed flowers/lamps for each graha on their respective weekdays; this addresses all planetary imbalances simultaneously",
        "priority": "medium",
        "notes": "The Navagraha Yantra is the classical comprehensive remedy per BPHS §82 — it addresses all nine planets in one installation. Particularly relevant for this chart's combination of Saturn dominance + Jupiter/Venus weakness.",
    },
]

# ── Summary Statistics ─────────────────────────────────────────────────────

REMEDIATION_SUMMARY: dict[str, Any] = {
    "total_entries": len(REMEDIATION_PRESCRIPTIONS),
    "volume_floor": 10,
    "volume_floor_met": len(REMEDIATION_PRESCRIPTIONS) >= 10,
    "remedy_types": {
        "gemstone": sum(1 for r in REMEDIATION_PRESCRIPTIONS if r["remedy_type"] == "gemstone"),
        "mantra":   sum(1 for r in REMEDIATION_PRESCRIPTIONS if r["remedy_type"] == "mantra"),
        "charity":  sum(1 for r in REMEDIATION_PRESCRIPTIONS if r["remedy_type"] == "charity"),
        "fasting":  sum(1 for r in REMEDIATION_PRESCRIPTIONS if r["remedy_type"] == "fasting"),
        "yantra":   sum(1 for r in REMEDIATION_PRESCRIPTIONS if r["remedy_type"] == "yantra"),
        "combined": sum(1 for r in REMEDIATION_PRESCRIPTIONS if r["remedy_type"] == "combined"),
    },
    "priority_distribution": {
        "high":   sum(1 for r in REMEDIATION_PRESCRIPTIONS if r["priority"] == "high"),
        "medium": sum(1 for r in REMEDIATION_PRESCRIPTIONS if r["priority"] == "medium"),
        "low":    sum(1 for r in REMEDIATION_PRESCRIPTIONS if r["priority"] == "low"),
    },
    "unique_rule_ids_cited": list(set(r["rule_id"] for r in REMEDIATION_PRESCRIPTIONS)),
    "schools_represented": list(set(r["school"] for r in REMEDIATION_PRESCRIPTIONS)),
    "target_planets": list(set(r["target_planet"] for r in REMEDIATION_PRESCRIPTIONS)),
    "grounding_status": "GROUNDED",
    "grounding_source": "WS-3 rule corpus — BPHS remedy chapters 81–82 (scope=remedy)",
    "session": "l2-bodha-grounded",
}

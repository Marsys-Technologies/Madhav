"""
brahmagyan.l0_nakshatra — bg_nakshatra L0 global nakshatra reference.

Three grains: NAKSHATRAS_ENRICHED (27 + Abhijit), PADAS (108), MATRICES.
All content: deterministic + classically cited. ZERO LLM. No narrative.
Supersedes the thin reference_nakshatras in l0_reference.py.

Sources:
  bphs                  — Brihat Parashara Hora Shastra (in bg_texts)
  muhurta_chintamani    — Muhurta Chintamani (in bg_texts)
  brihat_samhita        — Brihat Samhita (in bg_texts)
  uttara_kalamrita      — Uttara Kalamrita (in bg_texts)
  taittiriya_aranyaka   — TA (NOT in bg_texts; cite with [NOT_IN_CORPUS] until sourced)
"""
from __future__ import annotations

BPHS_CH92 = "bphs:ch92"
BPHS_CH46 = "bphs:ch46"
MC_CH7    = "muhurta_chintamani:ch7"
BS_CH99   = "brihat_samhita:ch99"
UK_CH2    = "uttara_kalamrita:ch2"
SAR_NAK   = "saravali:nakshatra_chapter"
TA_REF    = "taittiriya_aranyaka:nakshatra_sukta [NOT_IN_CORPUS]"

# ── Per-nakshatra data ─────────────────────────────────────────────────────────
# Attributes with [VERIFY] need cross-check against source.
# None = value classically exists but not confirmed at encoding time.
# Halt-and-report rule: never fabricate. A null cited attribute > a wrong value.

NAKSHATRAS_ENRICHED: list[dict] = [
    # ── 1. Ashvini ────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=1,
        name_sa_iast="Aśvinī", name_sa_devanagari="अश्विनी", name_en="Ashwini",
        alt_names=["Ashva", "Asvini"],
        start_longitude=0.0, end_longitude=13.33333, span_degrees=13.33333,
        rashis_spanned=["Aries"],
        degree_in_rashi_ranges=[{"rashi": "Aries", "start_in_rashi": 0.0, "end_in_rashi": 13.333}],
        vimshottari_lord="ketu",
        presiding_deity="Ashvini Kumaras", secondary_deities=[],
        ruling_planet="ketu",
        gana="Deva", nadi="Adi",
        yoni_en="Horse", yoni_sa="Ashva", yoni_sex="M",
        varna="Vaishya", tatva="Agni", guna="Sattva",
        pakshi="Eagle",
        nakshatra_gender="Male",
        muhurta_type="Kshipra",
        disha="South",
        favorable_acts=["medicine", "fine arts", "horse training", "short travel", "ornaments"],
        prohibited_acts=["marriage", "agriculture"],
        symbol="Horse head",
        shakti="Sheeghrakari (swift action / healing)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="dharma",
        body_part="head",
        paramayus="short",
        naisargika_maturity_age=0,
        deity_domain="healing, medicine, rejuvenation",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 2. Bharaṇī ────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=2,
        name_sa_iast="Bharaṇī", name_sa_devanagari="भरणी", name_en="Bharani",
        alt_names=[],
        start_longitude=13.33333, end_longitude=26.66667, span_degrees=13.33333,
        rashis_spanned=["Aries"],
        degree_in_rashi_ranges=[{"rashi": "Aries", "start_in_rashi": 13.333, "end_in_rashi": 26.667}],
        vimshottari_lord="venus",
        presiding_deity="Yama", secondary_deities=["Kali"],
        ruling_planet="venus",
        gana="Manushya", nadi="Madhya",
        yoni_en="Elephant", yoni_sa="Gaja", yoni_sex="M",
        varna="Mleccha", tatva="Jala", guna="Rajas",
        pakshi="Crow",
        nakshatra_gender="Female",
        muhurta_type="Ugra",
        disha="West",
        favorable_acts=["harsh actions", "punishment", "fire", "weapons", "surgery"],
        prohibited_acts=["marriage", "beginnings", "travel"],
        symbol="Yoni (female generative organ)",
        shakti="Apabharani (removing / carrying away)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="artha",
        body_part="head",
        paramayus="short",
        naisargika_maturity_age=0,
        deity_domain="death, discipline, dharma, justice",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 3. Kṛttikā ────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=3,
        name_sa_iast="Kṛttikā", name_sa_devanagari="कृत्तिका", name_en="Krittika",
        alt_names=["Kritika"],
        start_longitude=26.66667, end_longitude=40.0, span_degrees=13.33333,
        rashis_spanned=["Aries", "Taurus"],
        degree_in_rashi_ranges=[
            {"rashi": "Aries", "start_in_rashi": 26.667, "end_in_rashi": 30.0},
            {"rashi": "Taurus", "start_in_rashi": 0.0, "end_in_rashi": 10.0},
        ],
        vimshottari_lord="sun",
        presiding_deity="Agni", secondary_deities=["Karttikeya"],
        ruling_planet="sun",
        gana="Rakshasa", nadi="Antya",
        yoni_en="Goat", yoni_sa="Aja", yoni_sex="F",
        varna="Brahmin", tatva="Agni", guna="Rajas",
        pakshi="Peacock",
        nakshatra_gender="Female",
        muhurta_type="Mishra",
        disha="North",
        favorable_acts=["fire rituals", "cooking", "military", "cutting"],
        prohibited_acts=["peace-making", "auspicious beginnings"],
        symbol="Razor / flame / cluster of 6 stars",
        shakti="Dahana (power of burning / purification)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="kama",
        body_part="head",
        paramayus="short",
        naisargika_maturity_age=0,
        deity_domain="fire, digestion, purification, cutting",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 4. Rohiṇī ─────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=4,
        name_sa_iast="Rohiṇī", name_sa_devanagari="रोहिणी", name_en="Rohini",
        alt_names=[],
        start_longitude=40.0, end_longitude=53.33333, span_degrees=13.33333,
        rashis_spanned=["Taurus"],
        degree_in_rashi_ranges=[{"rashi": "Taurus", "start_in_rashi": 10.0, "end_in_rashi": 23.333}],
        vimshottari_lord="moon",
        presiding_deity="Brahma", secondary_deities=["Prajapati"],
        ruling_planet="moon",
        gana="Manushya", nadi="Adi",
        yoni_en="Serpent", yoni_sa="Sarpa", yoni_sex="M",
        varna="Shudra", tatva="Jala", guna="Rajas",
        pakshi="Owl",
        nakshatra_gender="Female",
        muhurta_type="Dhruva",
        disha="East",
        favorable_acts=["planting seeds", "building", "agriculture", "marriage", "jewelry"],
        prohibited_acts=["destruction", "harsh acts"],
        symbol="Chariot / cart / ox (Aldebaran)",
        shakti="Rohana (power to grow / fertility / creation)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="moksha",
        body_part="forehead",
        paramayus="long",
        naisargika_maturity_age=0,
        deity_domain="creation, growth, fertility, beauty, arts",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 5. Mṛgaśirā ───────────────────────────────────────────────────────────
    dict(
        nakshatra_id=5,
        name_sa_iast="Mṛgaśirā", name_sa_devanagari="मृगशिरा", name_en="Mrigasira",
        alt_names=["Mrigashirsha", "Makayiram"],
        start_longitude=53.33333, end_longitude=66.66667, span_degrees=13.33333,
        rashis_spanned=["Taurus", "Gemini"],
        degree_in_rashi_ranges=[
            {"rashi": "Taurus", "start_in_rashi": 23.333, "end_in_rashi": 30.0},
            {"rashi": "Gemini", "start_in_rashi": 0.0, "end_in_rashi": 6.667},
        ],
        vimshottari_lord="mars",
        presiding_deity="Soma", secondary_deities=["Chandra"],
        ruling_planet="mars",
        gana="Deva", nadi="Madhya",
        yoni_en="Serpent", yoni_sa="Sarpa", yoni_sex="F",
        varna="Vaishya", tatva="Agni", guna="Tamas",
        pakshi="Hen",
        nakshatra_gender="Female",
        muhurta_type="Mridu",
        disha="South",
        favorable_acts=["music", "dance", "fine arts", "romance", "gentle activities"],
        prohibited_acts=["harsh activities"],
        symbol="Deer head",
        shakti="Ananda (power of bliss / fulfillment through searching)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="moksha",
        body_part="eyes",
        paramayus="short",
        naisargika_maturity_age=53,
        deity_domain="searching, wandering, sensory pleasure, moon",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 6. Ārdrā ──────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=6,
        name_sa_iast="Ārdrā", name_sa_devanagari="आर्द्रा", name_en="Ardra",
        alt_names=["Arudra"],
        start_longitude=66.66667, end_longitude=80.0, span_degrees=13.33333,
        rashis_spanned=["Gemini"],
        degree_in_rashi_ranges=[{"rashi": "Gemini", "start_in_rashi": 6.667, "end_in_rashi": 20.0}],
        vimshottari_lord="rahu",
        presiding_deity="Rudra", secondary_deities=["Shiva"],
        ruling_planet="rahu",
        gana="Manushya", nadi="Antya",
        yoni_en="Dog", yoni_sa="Shvana", yoni_sex="F",
        varna="Butcher", tatva="Vayu", guna="Tamas",
        pakshi="Butcher Bird",
        nakshatra_gender="Female",
        muhurta_type="Tikshna",
        disha="West",
        favorable_acts=["learning", "research", "destruction of enemies", "harsh work"],
        prohibited_acts=["marriage", "auspicious ceremonies"],
        symbol="Teardrop / diamond / head of Rudra",
        shakti="Yatana (effort / storm / intensity)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="kama",
        body_part="hair",
        paramayus="short",
        naisargika_maturity_age=42,
        deity_domain="storm, destruction, transformation, enlightenment",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 7. Punarvasu ──────────────────────────────────────────────────────────
    dict(
        nakshatra_id=7,
        name_sa_iast="Punarvasu", name_sa_devanagari="पुनर्वसु", name_en="Punarvasu",
        alt_names=["Punartham"],
        start_longitude=80.0, end_longitude=93.33333, span_degrees=13.33333,
        rashis_spanned=["Gemini", "Cancer"],
        degree_in_rashi_ranges=[
            {"rashi": "Gemini", "start_in_rashi": 20.0, "end_in_rashi": 30.0},
            {"rashi": "Cancer", "start_in_rashi": 0.0, "end_in_rashi": 3.333},
        ],
        vimshottari_lord="jupiter",
        presiding_deity="Aditi", secondary_deities=["Mitra"],
        ruling_planet="jupiter",
        gana="Deva", nadi="Adi",
        yoni_en="Cat", yoni_sa="Marjara", yoni_sex="M",
        varna="Brahmin", tatva="Akasha", guna="Sattva",
        pakshi="Swan",
        nakshatra_gender="Female",
        muhurta_type="Chara",
        disha="North",
        favorable_acts=["travel", "return home", "fresh starts", "renewal", "pilgrimage"],
        prohibited_acts=[],
        symbol="Quiver of arrows / bow",
        shakti="Vasutva prapti (regaining wealth and lost goods)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="artha",
        body_part="nose",
        paramayus="medium",
        naisargika_maturity_age=21,
        deity_domain="renewal, abundance, maternal love, return",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 8. Puṣya ──────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=8,
        name_sa_iast="Puṣya", name_sa_devanagari="पुष्य", name_en="Pushya",
        alt_names=["Poosam", "Tishya", "Pushyami"],
        start_longitude=93.33333, end_longitude=106.66667, span_degrees=13.33333,
        rashis_spanned=["Cancer"],
        degree_in_rashi_ranges=[{"rashi": "Cancer", "start_in_rashi": 3.333, "end_in_rashi": 16.667}],
        vimshottari_lord="saturn",
        presiding_deity="Brihaspati", secondary_deities=[],
        ruling_planet="saturn",
        gana="Deva", nadi="Madhya",
        yoni_en="Goat", yoni_sa="Aja", yoni_sex="M",
        varna="Kshatriya", tatva="Vayu", guna="Tamas",
        pakshi="Crow",
        nakshatra_gender="Male",
        muhurta_type="Laghu",
        disha="East",
        favorable_acts=["spiritual practice", "coronation", "charity", "medicine", "wealth"],
        prohibited_acts=[],
        symbol="Flower / circle / cow udder",
        shakti="Brahmavardhana (nourishing / expanding spiritual energy)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="dharma",
        body_part="face",
        paramayus="long",
        naisargika_maturity_age=0,
        deity_domain="wisdom, spiritual nourishment, dharma, teaching",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 9. Āśleṣā ─────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=9,
        name_sa_iast="Āśleṣā", name_sa_devanagari="आश्लेषा", name_en="Ashlesha",
        alt_names=["Aayilyam"],
        start_longitude=106.66667, end_longitude=120.0, span_degrees=13.33333,
        rashis_spanned=["Cancer"],
        degree_in_rashi_ranges=[{"rashi": "Cancer", "start_in_rashi": 16.667, "end_in_rashi": 30.0}],
        vimshottari_lord="mercury",
        presiding_deity="Sarpas", secondary_deities=["Naga", "Ahi"],
        ruling_planet="mercury",
        gana="Rakshasa", nadi="Antya",
        yoni_en="Cat", yoni_sa="Marjara", yoni_sex="F",
        varna="Mleccha", tatva="Prithvi", guna="Sattva",
        pakshi="Cat",
        nakshatra_gender="Female",
        muhurta_type="Tikshna",
        disha="South",
        favorable_acts=["poison administration", "magic", "psychological work", "research"],
        prohibited_acts=["marriage", "new beginnings", "auspicious acts"],
        symbol="Coiled serpent",
        shakti="Vishashleshana (binding / paralyzing / clinging)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="dharma",
        body_part="nails",
        paramayus="short",
        naisargika_maturity_age=0,
        deity_domain="serpent power, kundalini, deception, wisdom, poison",
        is_gandanta=True, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 10. Maghā ─────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=10,
        name_sa_iast="Maghā", name_sa_devanagari="मघा", name_en="Magha",
        alt_names=["Makam"],
        start_longitude=120.0, end_longitude=133.33333, span_degrees=13.33333,
        rashis_spanned=["Leo"],
        degree_in_rashi_ranges=[{"rashi": "Leo", "start_in_rashi": 0.0, "end_in_rashi": 13.333}],
        vimshottari_lord="ketu",
        presiding_deity="Pitrs", secondary_deities=["Ancestors"],
        ruling_planet="ketu",
        gana="Rakshasa", nadi="Adi",
        yoni_en="Rat", yoni_sa="Mushika", yoni_sex="M",
        varna="Shudra", tatva="Agni", guna="Tamas",
        pakshi="Eagle",
        nakshatra_gender="Female",
        muhurta_type="Ugra",
        disha="East",
        favorable_acts=["ancestor worship", "past-life healing", "authority acts", "coronation"],
        prohibited_acts=["new beginnings", "marriage"],
        symbol="Royal throne / palanquin",
        shakti="Pitru sodhana (purifying the ancestors / leaving the body)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="artha",
        body_part="lips",
        paramayus="short",
        naisargika_maturity_age=0,
        deity_domain="ancestors, lineage, royalty, power",
        is_gandanta=True, is_mula_sangya=True, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 11. Pūrva Phalguṇī ────────────────────────────────────────────────────
    dict(
        nakshatra_id=11,
        name_sa_iast="Pūrva Phalguṇī", name_sa_devanagari="पूर्व फाल्गुनी",
        name_en="Purva Phalguni",
        alt_names=["Pubba", "Purva"],
        start_longitude=133.33333, end_longitude=146.66667, span_degrees=13.33333,
        rashis_spanned=["Leo"],
        degree_in_rashi_ranges=[{"rashi": "Leo", "start_in_rashi": 13.333, "end_in_rashi": 26.667}],
        vimshottari_lord="venus",
        presiding_deity="Bhaga", secondary_deities=[],
        ruling_planet="venus",
        gana="Manushya", nadi="Madhya",
        yoni_en="Rat", yoni_sa="Mushika", yoni_sex="F",
        varna="Brahmin", tatva="Jala", guna="Rajas",
        pakshi="Parrot",
        nakshatra_gender="Female",
        muhurta_type="Ugra",
        disha="West",
        favorable_acts=["romance", "pleasure", "creativity", "rest"],
        prohibited_acts=["harsh activities", "warfare"],
        symbol="Front legs of a bed / hammock",
        shakti="Prajanana (power of procreation / creative union)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="kama",
        body_part="right hand",
        paramayus="medium",
        naisargika_maturity_age=24,
        deity_domain="luck, love, pleasure, arts, beauty",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 12. Uttara Phalguṇī ───────────────────────────────────────────────────
    dict(
        nakshatra_id=12,
        name_sa_iast="Uttara Phalguṇī", name_sa_devanagari="उत्तर फाल्गुनी",
        name_en="Uttara Phalguni",
        alt_names=["Uttara", "Uthiram"],
        start_longitude=146.66667, end_longitude=160.0, span_degrees=13.33333,
        rashis_spanned=["Leo", "Virgo"],
        degree_in_rashi_ranges=[
            {"rashi": "Leo", "start_in_rashi": 26.667, "end_in_rashi": 30.0},
            {"rashi": "Virgo", "start_in_rashi": 0.0, "end_in_rashi": 10.0},
        ],
        vimshottari_lord="sun",
        presiding_deity="Aryaman", secondary_deities=[],
        ruling_planet="sun",
        gana="Manushya", nadi="Antya",
        yoni_en="Cow", yoni_sa="Go", yoni_sex="M",
        varna="Kshatriya", tatva="Agni", guna="Rajas",
        pakshi="Bullock",
        nakshatra_gender="Female",
        muhurta_type="Dhruva",
        disha="East",
        favorable_acts=["marriage", "charity", "planting", "building", "friendship"],
        prohibited_acts=["harsh activities"],
        symbol="Back legs of a bed / two stars",
        shakti="Chayani (power of prosperity / collecting)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="moksha",
        body_part="left hand",
        paramayus="long",
        naisargika_maturity_age=27,
        deity_domain="marriage, friendship, agreements, contracts",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 13. Hasta ─────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=13,
        name_sa_iast="Hasta", name_sa_devanagari="हस्त", name_en="Hasta",
        alt_names=["Attam"],
        start_longitude=160.0, end_longitude=173.33333, span_degrees=13.33333,
        rashis_spanned=["Virgo"],
        degree_in_rashi_ranges=[{"rashi": "Virgo", "start_in_rashi": 10.0, "end_in_rashi": 23.333}],
        vimshottari_lord="moon",
        presiding_deity="Savitar", secondary_deities=["Surya-Savita"],
        ruling_planet="moon",
        gana="Deva", nadi="Adi",
        yoni_en="Buffalo", yoni_sa="Mahisha", yoni_sex="F",
        varna="Vaishya", tatva="Jala", guna="Sattva",
        pakshi="Vulture",
        nakshatra_gender="Female",
        muhurta_type="Kshipra",
        disha="South",
        favorable_acts=["crafts", "healing", "skill work", "trade", "beginning travel"],
        prohibited_acts=[],
        symbol="Hand / fist",
        shakti="Hasta sthapani (obtaining an object in hand / dexterity)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="moksha",
        body_part="fingers",
        paramayus="short",
        naisargika_maturity_age=30,
        deity_domain="craftsmanship, healing, dexterity, solar energy",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 14. Citrā ─────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=14,
        name_sa_iast="Citrā", name_sa_devanagari="चित्रा", name_en="Chitra",
        alt_names=["Chithirai", "Chittira"],
        start_longitude=173.33333, end_longitude=186.66667, span_degrees=13.33333,
        rashis_spanned=["Virgo", "Libra"],
        degree_in_rashi_ranges=[
            {"rashi": "Virgo", "start_in_rashi": 23.333, "end_in_rashi": 30.0},
            {"rashi": "Libra", "start_in_rashi": 0.0, "end_in_rashi": 6.667},
        ],
        vimshottari_lord="mars",
        presiding_deity="Vishwakarma", secondary_deities=["Tvashta"],
        ruling_planet="mars",
        gana="Rakshasa", nadi="Madhya",
        yoni_en="Tiger", yoni_sa="Vyaghra", yoni_sex="M",
        varna="Farmer", tatva="Agni", guna="Tamas",
        pakshi="Hen",
        nakshatra_gender="Female",
        muhurta_type="Mridu",
        disha="South",
        favorable_acts=["architecture", "design", "arts", "clothing", "ornamentation"],
        prohibited_acts=[],
        symbol="Bright gem / pearl",
        shakti="Tvashtar (fashioning / shaping beautiful forms)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="kama",
        body_part="neck",
        paramayus="medium",
        naisargika_maturity_age=18,
        deity_domain="craftsmanship, beauty, architecture, creativity",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 15. Svātī ─────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=15,
        name_sa_iast="Svātī", name_sa_devanagari="स्वाती", name_en="Swati",
        alt_names=["Chothi", "Svati"],
        start_longitude=186.66667, end_longitude=200.0, span_degrees=13.33333,
        rashis_spanned=["Libra"],
        degree_in_rashi_ranges=[{"rashi": "Libra", "start_in_rashi": 6.667, "end_in_rashi": 20.0}],
        vimshottari_lord="rahu",
        presiding_deity="Vayu", secondary_deities=["Saraswati"],
        ruling_planet="rahu",
        gana="Deva", nadi="Antya",
        yoni_en="Buffalo", yoni_sa="Mahisha", yoni_sex="M",
        varna="Butcher", tatva="Vayu", guna="Tamas",
        pakshi="Bee",
        nakshatra_gender="Female",
        muhurta_type="Chara",
        disha="North",
        favorable_acts=["business", "trade", "learning", "independent work", "travel"],
        prohibited_acts=["marriage"],
        symbol="Young shoot of grass / sword / coral",
        shakti="Pradhana vayu (the mighty wind / power of independent movement)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="artha",
        body_part="chest",
        paramayus="long",
        naisargika_maturity_age=30,
        deity_domain="wind, independence, trade, speech",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 16. Viśākhā ───────────────────────────────────────────────────────────
    dict(
        nakshatra_id=16,
        name_sa_iast="Viśākhā", name_sa_devanagari="विशाखा", name_en="Vishakha",
        alt_names=["Vishakam"],
        start_longitude=200.0, end_longitude=213.33333, span_degrees=13.33333,
        rashis_spanned=["Libra", "Scorpio"],
        degree_in_rashi_ranges=[
            {"rashi": "Libra", "start_in_rashi": 20.0, "end_in_rashi": 30.0},
            {"rashi": "Scorpio", "start_in_rashi": 0.0, "end_in_rashi": 3.333},
        ],
        vimshottari_lord="jupiter",
        presiding_deity="Indra-Agni", secondary_deities=["Radha"],
        ruling_planet="jupiter",
        gana="Rakshasa", nadi="Adi",
        yoni_en="Tiger", yoni_sa="Vyaghra", yoni_sex="F",
        varna="Mleccha", tatva="Akasha", guna="Rajas",
        pakshi="Sparrow",
        nakshatra_gender="Female",
        muhurta_type="Mishra",
        disha="East",
        favorable_acts=["achieving goals", "research", "power acts", "harvest"],
        prohibited_acts=["auspicious ceremonies"],
        symbol="Branched tree / triumphal arch",
        shakti="Vyapana (pervasion / power of achieving many goals)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="dharma",
        body_part="arms",
        paramayus="medium",
        naisargika_maturity_age=0,
        deity_domain="achievement, harvest, dual power (fire+rain), focused effort",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 17. Anurādhā ──────────────────────────────────────────────────────────
    dict(
        nakshatra_id=17,
        name_sa_iast="Anurādhā", name_sa_devanagari="अनुराधा", name_en="Anuradha",
        alt_names=["Anusham", "Anusha"],
        start_longitude=213.33333, end_longitude=226.66667, span_degrees=13.33333,
        rashis_spanned=["Scorpio"],
        degree_in_rashi_ranges=[{"rashi": "Scorpio", "start_in_rashi": 3.333, "end_in_rashi": 16.667}],
        vimshottari_lord="saturn",
        presiding_deity="Mitra", secondary_deities=[],
        ruling_planet="saturn",
        gana="Deva", nadi="Madhya",
        yoni_en="Hare", yoni_sa="Shasha", yoni_sex="M",
        varna="Shudra", tatva="Vayu", guna="Tamas",
        pakshi="Heron",
        nakshatra_gender="Female",
        muhurta_type="Mridu",
        disha="South",
        favorable_acts=["friendship", "devotion", "group activities", "travel to water bodies"],
        prohibited_acts=[],
        symbol="Lotus / row of offerings",
        shakti="Radhana (devotion / power of friendship / mitra)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="dharma",
        body_part="stomach",
        paramayus="medium",
        naisargika_maturity_age=0,
        deity_domain="friendship, devotion, alliances, group harmony",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 18. Jyeṣṭhā ──────────────────────────────────────────────────────────
    dict(
        nakshatra_id=18,
        name_sa_iast="Jyeṣṭhā", name_sa_devanagari="ज्येष्ठा", name_en="Jyeshtha",
        alt_names=["Ketta", "Jyeshta"],
        start_longitude=226.66667, end_longitude=240.0, span_degrees=13.33333,
        rashis_spanned=["Scorpio"],
        degree_in_rashi_ranges=[{"rashi": "Scorpio", "start_in_rashi": 16.667, "end_in_rashi": 30.0}],
        vimshottari_lord="mercury",
        presiding_deity="Indra", secondary_deities=["Vishnu"],
        ruling_planet="mercury",
        gana="Rakshasa", nadi="Antya",
        yoni_en="Hare", yoni_sa="Shasha", yoni_sex="F",
        varna="Farmer", tatva="Prithvi", guna="Sattva",
        pakshi="Vulture",
        nakshatra_gender="Female",
        muhurta_type="Tikshna",
        disha="West",
        favorable_acts=["defense", "power acts", "overcoming enemies", "magic", "occult"],
        prohibited_acts=["auspicious ceremonies", "new beginnings"],
        symbol="Circular amulet / umbrella / earring",
        shakti="Arohana (power of rising / ascending / conquest)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="artha",
        body_part="tongue",
        paramayus="medium",
        naisargika_maturity_age=18,
        deity_domain="power, leadership, eldest (chief), protection",
        is_gandanta=True, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 19. Mūla ──────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=19,
        name_sa_iast="Mūla", name_sa_devanagari="मूल", name_en="Moola",
        alt_names=["Mula", "Moolam"],
        start_longitude=240.0, end_longitude=253.33333, span_degrees=13.33333,
        rashis_spanned=["Sagittarius"],
        degree_in_rashi_ranges=[{"rashi": "Sagittarius", "start_in_rashi": 0.0, "end_in_rashi": 13.333}],
        vimshottari_lord="ketu",
        presiding_deity="Nirriti", secondary_deities=["Alakshmi"],
        ruling_planet="ketu",
        gana="Rakshasa", nadi="Adi",
        yoni_en="Dog", yoni_sa="Shvana", yoni_sex="M",
        varna="Butcher", tatva="Agni", guna="Tamas",
        pakshi="Dog",
        nakshatra_gender="Neutral",
        muhurta_type="Tikshna",
        disha="South",
        favorable_acts=["digging", "mining", "destruction", "uprooting", "extraction"],
        prohibited_acts=["marriage", "new beginnings", "investments"],
        symbol="Tied roots / tail of scorpion",
        shakti="Barhana (power of destruction / uprooting / going to the root)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="kama",
        body_part="feet",
        paramayus="short",
        naisargika_maturity_age=0,
        deity_domain="destruction, dissolution, root causes, endings",
        is_gandanta=True, is_mula_sangya=True, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 20. Pūrva Āṣāḍhā ──────────────────────────────────────────────────────
    dict(
        nakshatra_id=20,
        name_sa_iast="Pūrva Āṣāḍhā", name_sa_devanagari="पूर्व आषाढा",
        name_en="Purva Ashadha",
        alt_names=["Pooradam", "Purvaashadha"],
        start_longitude=253.33333, end_longitude=266.66667, span_degrees=13.33333,
        rashis_spanned=["Sagittarius"],
        degree_in_rashi_ranges=[{"rashi": "Sagittarius", "start_in_rashi": 13.333, "end_in_rashi": 26.667}],
        vimshottari_lord="venus",
        presiding_deity="Apas", secondary_deities=["Varuna"],
        ruling_planet="venus",
        gana="Manushya", nadi="Madhya",
        yoni_en="Monkey", yoni_sa="Vanara", yoni_sex="F",
        varna="Brahmin", tatva="Jala", guna="Rajas",
        pakshi="Partridge",
        nakshatra_gender="Female",
        muhurta_type="Ugra",
        disha="North",
        favorable_acts=["water activities", "sea travel", "healing", "purification"],
        prohibited_acts=["marriage"],
        symbol="Elephant tusk / fan / winnowing basket",
        shakti="Varshabala (invigoration / power to energize and refresh)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="moksha",
        body_part="back",
        paramayus="medium",
        naisargika_maturity_age=0,
        deity_domain="water, purification, invigoration, early victory",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 21. Uttara Āṣāḍhā ─────────────────────────────────────────────────────
    dict(
        nakshatra_id=21,
        name_sa_iast="Uttara Āṣāḍhā", name_sa_devanagari="उत्तर आषाढा",
        name_en="Uttara Ashadha",
        alt_names=["Utiradam", "Uttarashadha"],
        start_longitude=266.66667, end_longitude=280.0, span_degrees=13.33333,
        rashis_spanned=["Sagittarius", "Capricorn"],
        degree_in_rashi_ranges=[
            {"rashi": "Sagittarius", "start_in_rashi": 26.667, "end_in_rashi": 30.0},
            {"rashi": "Capricorn", "start_in_rashi": 0.0, "end_in_rashi": 10.0},
        ],
        vimshottari_lord="sun",
        presiding_deity="Vishvedevas", secondary_deities=["Ten Vishvedeva"],
        ruling_planet="sun",
        gana="Manushya", nadi="Antya",
        yoni_en="Mongoose", yoni_sa="Nakula", yoni_sex="M",
        varna="Kshatriya", tatva="Agni", guna="Rajas",
        pakshi="Stork",
        nakshatra_gender="Female",
        muhurta_type="Dhruva",
        disha="South",
        favorable_acts=["leadership", "long-term goals", "permanent achievements"],
        prohibited_acts=["hasty decisions"],
        symbol="Elephant tusk (Uttara) / fruit of the Jambu tree",
        shakti="Aprakadhyam sarva (universal and ultimate victory)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="moksha",
        body_part="thighs",
        paramayus="long",
        naisargika_maturity_age=0,
        deity_domain="ultimate achievement, universal victory, leadership",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 22. Śravaṇa ───────────────────────────────────────────────────────────
    dict(
        nakshatra_id=22,
        name_sa_iast="Śravaṇa", name_sa_devanagari="श्रवण", name_en="Shravana",
        alt_names=["Thiruvonam", "Sravana"],
        start_longitude=280.0, end_longitude=293.33333, span_degrees=13.33333,
        rashis_spanned=["Capricorn"],
        degree_in_rashi_ranges=[{"rashi": "Capricorn", "start_in_rashi": 10.0, "end_in_rashi": 23.333}],
        vimshottari_lord="moon",
        presiding_deity="Vishnu", secondary_deities=["Saraswati"],
        ruling_planet="moon",
        gana="Deva", nadi="Adi",
        yoni_en="Monkey", yoni_sa="Vanara", yoni_sex="M",
        varna="Mleccha", tatva="Jala", guna="Rajas",
        pakshi="Cock",
        nakshatra_gender="Male",
        muhurta_type="Chara",
        disha="North",
        favorable_acts=["learning", "listening", "travel", "connecting with teachers"],
        prohibited_acts=[],
        symbol="Three footprints / ear / trident",
        shakti="Sambandha (power to connect all things / unifying)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="artha",
        body_part="ears",
        paramayus="long",
        naisargika_maturity_age=30,
        deity_domain="listening, learning, Vishnu, preservation, connection",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 23. Dhaniṣṭhā ─────────────────────────────────────────────────────────
    dict(
        nakshatra_id=23,
        name_sa_iast="Dhaniṣṭhā", name_sa_devanagari="धनिष्ठा", name_en="Dhanishtha",
        alt_names=["Avittam", "Dhanistha", "Shravishtha"],
        start_longitude=293.33333, end_longitude=306.66667, span_degrees=13.33333,
        rashis_spanned=["Capricorn", "Aquarius"],
        degree_in_rashi_ranges=[
            {"rashi": "Capricorn", "start_in_rashi": 23.333, "end_in_rashi": 30.0},
            {"rashi": "Aquarius", "start_in_rashi": 0.0, "end_in_rashi": 6.667},
        ],
        vimshottari_lord="mars",
        presiding_deity="Eight Vasus", secondary_deities=["Ashta-Vasu"],
        ruling_planet="mars",
        gana="Rakshasa", nadi="Madhya",
        yoni_en="Lion", yoni_sa="Simha", yoni_sex="M",
        varna="Farmer", tatva="Agni", guna="Tamas",
        pakshi="Lion",
        nakshatra_gender="Female",
        muhurta_type="Chara",
        disha="East",
        favorable_acts=["music", "wealth acquisition", "military", "group activities"],
        prohibited_acts=["marriage"],
        symbol="Musical drum (mridangam) / flute",
        shakti="Khyapana (giving abundance / power to bring fame and wealth)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="dharma",
        body_part="back",
        paramayus="medium",
        naisargika_maturity_age=24,
        deity_domain="abundance, music, wealth of the Vasus",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=True, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 24. Śatabhiṣā ─────────────────────────────────────────────────────────
    dict(
        nakshatra_id=24,
        name_sa_iast="Śatabhiṣā", name_sa_devanagari="शतभिषा", name_en="Shatabhisha",
        alt_names=["Sadayam", "Chathayam", "Satabishaj"],
        start_longitude=306.66667, end_longitude=320.0, span_degrees=13.33333,
        rashis_spanned=["Aquarius"],
        degree_in_rashi_ranges=[{"rashi": "Aquarius", "start_in_rashi": 6.667, "end_in_rashi": 20.0}],
        vimshottari_lord="rahu",
        presiding_deity="Varuna", secondary_deities=["Indra (as healer)"],
        ruling_planet="rahu",
        gana="Rakshasa", nadi="Antya",
        yoni_en="Horse", yoni_sa="Ashva", yoni_sex="F",
        varna="Butcher", tatva="Vayu", guna="Tamas",
        pakshi="Raven",
        nakshatra_gender="Neutral",
        muhurta_type="Chara",
        disha="South",
        favorable_acts=["healing", "research", "astronomy", "astrology", "mystical work"],
        prohibited_acts=["marriage", "auspicious beginnings"],
        symbol="Hundred stars / empty circle",
        shakti="Bheshaja (healing / veiling / covering — the power of a thousand healers)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="dharma",
        body_part="chin",
        paramayus="medium",
        naisargika_maturity_age=0,
        deity_domain="healing, veiling, secrets, cosmic ocean, medicine",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=True, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 25. Pūrva Bhādrapadā ──────────────────────────────────────────────────
    dict(
        nakshatra_id=25,
        name_sa_iast="Pūrva Bhādrapadā", name_sa_devanagari="पूर्व भाद्रपदा",
        name_en="Purva Bhadrapada",
        alt_names=["Poorattathi", "Purva Bhadra"],
        start_longitude=320.0, end_longitude=333.33333, span_degrees=13.33333,
        rashis_spanned=["Aquarius", "Pisces"],
        degree_in_rashi_ranges=[
            {"rashi": "Aquarius", "start_in_rashi": 20.0, "end_in_rashi": 30.0},
            {"rashi": "Pisces", "start_in_rashi": 0.0, "end_in_rashi": 3.333},
        ],
        vimshottari_lord="jupiter",
        presiding_deity="Aja Ekapada", secondary_deities=["One-footed goat / serpent form"],
        ruling_planet="jupiter",
        gana="Manushya", nadi="Adi",
        yoni_en="Lion", yoni_sa="Simha", yoni_sex="F",
        varna="Brahmin", tatva="Akasha", guna="Tamas",
        pakshi="Peacock",
        nakshatra_gender="Male",
        muhurta_type="Ugra",
        disha="West",
        favorable_acts=["fire rituals", "spiritual austerity", "renunciation"],
        prohibited_acts=["marriage", "auspicious beginnings"],
        symbol="Front of a funeral cot / double-faced man",
        shakti="Yajamana udyapana (burning rain — elevation through fire / purification)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="artha",
        body_part="sides",
        paramayus="short",
        naisargika_maturity_age=0,
        deity_domain="spiritual fire, renunciation, one-pointed austerity",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=True, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 26. Uttara Bhādrapadā ─────────────────────────────────────────────────
    dict(
        nakshatra_id=26,
        name_sa_iast="Uttara Bhādrapadā", name_sa_devanagari="उत्तर भाद्रपदा",
        name_en="Uttara Bhadrapada",
        alt_names=["Uthrattathi", "Uttara Bhadra"],
        start_longitude=333.33333, end_longitude=346.66667, span_degrees=13.33333,
        rashis_spanned=["Pisces"],
        degree_in_rashi_ranges=[{"rashi": "Pisces", "start_in_rashi": 3.333, "end_in_rashi": 16.667}],
        vimshottari_lord="saturn",
        presiding_deity="Ahir Budhnya", secondary_deities=["Serpent of the deep"],
        ruling_planet="saturn",
        gana="Manushya", nadi="Antya",
        yoni_en="Cow", yoni_sa="Go", yoni_sex="F",
        varna="Kshatriya", tatva="Vayu", guna="Tamas",
        pakshi="Crane",
        nakshatra_gender="Male",
        muhurta_type="Dhruva",
        disha="South",
        favorable_acts=["deep meditation", "occult work", "charity", "water rituals"],
        prohibited_acts=[],
        symbol="Back of a funeral cot / twin serpents",
        shakti="Varsha (bringing rain / fertility of the deep ocean)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="kama",
        body_part="legs",
        paramayus="long",
        naisargika_maturity_age=0,
        deity_domain="ocean depth, cosmic serpent, hidden spiritual power",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=True, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 27. Revatī ────────────────────────────────────────────────────────────
    dict(
        nakshatra_id=27,
        name_sa_iast="Revatī", name_sa_devanagari="रेवती", name_en="Revati",
        alt_names=["Revathi"],
        start_longitude=346.66667, end_longitude=360.0, span_degrees=13.33333,
        rashis_spanned=["Pisces"],
        degree_in_rashi_ranges=[{"rashi": "Pisces", "start_in_rashi": 16.667, "end_in_rashi": 30.0}],
        vimshottari_lord="mercury",
        presiding_deity="Pushan", secondary_deities=["Guide of souls"],
        ruling_planet="mercury",
        gana="Deva", nadi="Madhya",
        yoni_en="Elephant", yoni_sa="Gaja", yoni_sex="F",
        varna="Shudra", tatva="Prithvi", guna="Sattva",
        pakshi="Elephant",
        nakshatra_gender="Female",
        muhurta_type="Mridu",
        disha="North",
        favorable_acts=["travel", "endings", "compassion", "spiritual work", "pilgrimage"],
        prohibited_acts=["beginnings", "harsh activities"],
        symbol="Fish / drum",
        shakti="Kshira (nourishment / giving milk / fostering)",
        basis_above=None, basis_below=None, net_result=None,
        motivation="moksha",
        body_part="feet",
        paramayus="long",
        naisargika_maturity_age=28,
        deity_domain="safe travel, nourishment, endings, liberation",
        is_gandanta=True, is_mula_sangya=False, is_panchaka=True, is_abhijit=False,
        tradition_scope="classical", classical_source=BPHS_CH92,
    ),
    # ── 28. Abhijit (28th — excluded from 27-fold dasha math) ────────────────
    dict(
        nakshatra_id=28,
        name_sa_iast="Abhijit", name_sa_devanagari="अभिजित्", name_en="Abhijit",
        alt_names=["Vega nakshatra"],
        start_longitude=276.66667, end_longitude=280.88889, span_degrees=4.22222,
        rashis_spanned=["Capricorn"],
        degree_in_rashi_ranges=[{"rashi": "Capricorn", "start_in_rashi": 6.667, "end_in_rashi": 10.889}],
        vimshottari_lord="sun",
        presiding_deity="Brahma", secondary_deities=[],
        ruling_planet="sun",
        gana="Deva",
        nadi=None, yoni_en=None, yoni_sa=None, yoni_sex=None,
        varna="Brahmin", tatva="Agni", guna="Sattva",
        pakshi=None,
        nakshatra_gender="Male",
        muhurta_type="Laghu",
        disha=None,
        favorable_acts=["urgent and powerful actions", "war", "coronation"],
        prohibited_acts=[],
        symbol="Triangle (three stars of Lyra / Vega)",
        shakti=None,
        basis_above=None, basis_below=None, net_result=None,
        motivation="dharma",
        body_part=None,
        paramayus=None,
        naisargika_maturity_age=None,
        deity_domain="victory, urgency, divine favor (Vega)",
        is_gandanta=False, is_mula_sangya=False, is_panchaka=False,
        is_abhijit=True,
        tradition_scope="abhijit_28fold",
        classical_source=MC_CH7,
    ),
]

assert len(NAKSHATRAS_ENRICHED) == 28, f"Expected 28 rows (27 + Abhijit), got {len(NAKSHATRAS_ENRICHED)}"
assert all(r['nakshatra_id'] == i + 1 for i, r in enumerate(NAKSHATRAS_ENRICHED)), \
    "nakshatra_id must be sequential 1-28"

# FORENSIC spot-check: native Moon = Purva Bhadrapada (nakshatra_id=25)
_pbp = NAKSHATRAS_ENRICHED[24]
assert _pbp['nakshatra_id'] == 25
assert _pbp['vimshottari_lord'] == 'jupiter', f"PBP lord: expected jupiter, got {_pbp['vimshottari_lord']}"
assert _pbp['gana'] == 'Manushya'
assert _pbp['nadi'] == 'Adi'
assert _pbp['yoni_en'] == 'Lion'
assert 'Aja Ekapada' in _pbp['presiding_deity']
assert _pbp['shakti'] is not None and len(_pbp['shakti']) > 5

# Panchaka check: nakshatras 23-27 must all be panchaka
_panchaka_ids = {r['nakshatra_id'] for r in NAKSHATRAS_ENRICHED if r['is_panchaka']}
assert _panchaka_ids == {23, 24, 25, 26, 27}, f"Panchaka mismatch: {_panchaka_ids}"

# Abhijit check
_abhijit = NAKSHATRAS_ENRICHED[27]
assert _abhijit['is_abhijit'] is True
assert _abhijit['nadi'] is None
assert _abhijit['yoni_sex'] is None

# ── Per-pada data (108) ────────────────────────────────────────────────────────
# Deterministic: starting point = Ashwini pada 1 = Aries navamsa.
# Navamsa signs cycle 1-12 (Aries to Pisces) across all 108 padas.
# Pada lord = the ruling planet of the navamsa sign.
# Source: bphs:ch92 (pada structure) + muhurta_chintamani:ch7 (aksharas)

_NAVAMSA_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

_SIGN_LORDS = {
    "Aries": "mars", "Taurus": "venus", "Gemini": "mercury", "Cancer": "moon",
    "Leo": "sun", "Virgo": "mercury", "Libra": "venus", "Scorpio": "mars",
    "Sagittarius": "jupiter", "Capricorn": "saturn", "Aquarius": "saturn",
    "Pisces": "jupiter",
}

# 108 aksharas for naming — from Muhurta Chintamani Ch.7 (classical tradition)
# Sequence: 4 aksharas per nakshatra, in nakshatra order 1-27
# Abhijit has no conventional akshara assignments in the 27-fold system
_AKSHARAS: list[tuple] = [
    # (pada1, pada2, pada3, pada4) for each nakshatra 1-27
    ("Chu", "Che", "Cho", "La"),       # 1  Ashwini
    ("Li", "Lu", "Le", "Lo"),          # 2  Bharani
    ("A", "I", "U", "E"),              # 3  Krittika
    ("O", "Va", "Vi", "Vu"),           # 4  Rohini
    ("Ve", "Vo", "Ka", "Ki"),          # 5  Mrigasira
    ("Ku", "Gha", "Da", "Na"),         # 6  Ardra
    ("Ke", "Ko", "Ha", "Hi"),          # 7  Punarvasu
    ("Hu", "He", "Ho", "Da"),          # 8  Pushya
    ("Di", "Du", "De", "Do"),          # 9  Ashlesha
    ("Ma", "Mi", "Mu", "Me"),          # 10 Magha
    ("Mo", "Ta", "Ti", "Tu"),          # 11 Purva Phalguni
    ("Te", "To", "Pa", "Pi"),          # 12 Uttara Phalguni
    ("Pu", "Sha", "Na", "Tha"),        # 13 Hasta
    ("Pe", "Po", "Ra", "Ri"),          # 14 Chitra
    ("Ru", "Re", "Ro", "Ta"),          # 15 Swati
    ("Ti", "Tu", "Te", "To"),          # 16 Vishakha
    ("Na", "Ni", "Nu", "Ne"),          # 17 Anuradha
    ("No", "Ya", "Yi", "Yu"),          # 18 Jyeshtha
    ("Ye", "Yo", "Bha", "Bhi"),        # 19 Moola
    ("Bhu", "Dha", "Pha", "Dha"),      # 20 Purva Ashadha
    ("Bhe", "Bho", "Ja", "Ji"),        # 21 Uttara Ashadha
    ("Ju", "Je", "Jo", "Sha"),         # 22 Shravana
    ("Ga", "Gi", "Gu", "Ge"),          # 23 Dhanishtha
    ("Go", "Sa", "Si", "Su"),          # 24 Shatabhisha
    ("Se", "So", "Da", "Di"),          # 25 Purva Bhadrapada
    ("Du", "Tha", "Jha", "Da"),        # 26 Uttara Bhadrapada
    ("De", "Do", "Cha", "Chi"),        # 27 Revati
]

assert len(_AKSHARAS) == 27, "Need exactly 27 rows (one per nakshatra, Abhijit excluded)"


def _build_padas() -> list[dict]:
    """Build 108 pada rows deterministically from navamsa cycle + akshara table."""
    padas = []
    navamsa_idx = 0   # starts at Aries (index 0)

    for nak in NAKSHATRAS_ENRICHED[:27]:   # skip Abhijit (no conventional pada in 27-fold)
        nak_id = nak['nakshatra_id']
        nak_start = nak['start_longitude']
        aksharas = _AKSHARAS[nak_id - 1]
        for pada_num in range(1, 5):
            absolute_pada = (nak_id - 1) * 4 + pada_num
            navamsa_sign = _NAVAMSA_SIGNS[navamsa_idx % 12]
            pada_start = nak_start + (pada_num - 1) * 3.33333
            pada_end   = nak_start + pada_num * 3.33333

            padas.append(dict(
                pada_id=absolute_pada,
                nakshatra_id=nak_id,
                pada_number=pada_num,
                absolute_pada=absolute_pada,
                start_longitude=round(pada_start, 5),
                end_longitude=round(pada_end, 5),
                pada_navamsa_sign=navamsa_sign,
                pada_lord=_SIGN_LORDS[navamsa_sign],
                pada_akshara=aksharas[pada_num - 1],
                bija_sound=None,
                mantra_prefix=None,
                pada_deity_nuance=None,
                element_shading=None,
                dosha_shading=None,
                tradition_scope="classical",
                classical_source="bphs:ch92 + muhurta_chintamani:ch7",
            ))
            navamsa_idx += 1

    assert len(padas) == 108, f"Expected 108 padas, got {len(padas)}"
    return padas


PADAS: list[dict] = _build_padas()

# FORENSIC: native Moon in Purva Bhadrapada — pada 1 = Aries navamsa
_pbp_padas = [p for p in PADAS if p['nakshatra_id'] == 25]
assert len(_pbp_padas) == 4
assert _pbp_padas[0]['pada_navamsa_sign'] == 'Aries'
assert _pbp_padas[0]['pada_lord'] == 'mars'
assert _pbp_padas[0]['pada_akshara'] == 'Se'
assert _pbp_padas[0]['absolute_pada'] == 97

# ── Relational matrices ─────────────────────────────────────────────────────────
# 12 matrix types stored as rows: {matrix_type, from_key, to_key, relation_value,
# guna_points, max_points, notes, classical_source}
# Total: tara(729) + yoni(196) + gana(9) + nadi(9) + rajju(~27) + varna(49)
#        + graha_maitri(49) + bhakoot(144) + vedha(26) + vashya(25)
#        + mahendra(729) + stree_deergha(729) ≈ 3441 rows

def _build_matrices() -> list[dict]:
    rows: list[dict] = []

    # ── 1. Gana Kuta (3×3, max 6 gunas) ─────────────────────────────────────
    gana_scores = {
        ("Deva", "Deva"): 6, ("Manushya", "Manushya"): 6, ("Rakshasa", "Rakshasa"): 6,
        ("Deva", "Manushya"): 5, ("Manushya", "Deva"): 5,
        ("Deva", "Rakshasa"): 0, ("Rakshasa", "Deva"): 0,
        ("Manushya", "Rakshasa"): 0, ("Rakshasa", "Manushya"): 0,
    }
    for (g1, g2), pts in gana_scores.items():
        rows.append(dict(
            matrix_type="gana_kuta", from_key=g1, to_key=g2,
            relation_value="compatible" if pts >= 5 else "incompatible",
            guna_points=pts, max_points=6, notes=None,
            tradition_scope="classical", classical_source="bphs:ch73",
        ))

    # ── 2. Nadi Kuta (3×3, max 8 gunas) ─────────────────────────────────────
    nadis = ["Adi", "Madhya", "Antya"]
    for n1 in nadis:
        for n2 in nadis:
            pts = 0 if n1 == n2 else 8
            rows.append(dict(
                matrix_type="nadi_kuta", from_key=n1, to_key=n2,
                relation_value="nadi_dosha" if pts == 0 else "compatible",
                guna_points=pts, max_points=8, notes=None,
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    # ── 3. Yoni Kuta (14×14, max 4 gunas) ────────────────────────────────────
    yoni_enemies = {
        "Horse": "Buffalo", "Buffalo": "Horse",
        "Dog": "Hare", "Hare": "Dog",
        "Serpent": "Mongoose", "Mongoose": "Serpent",
        "Rat": "Cat", "Cat": "Rat",
        "Lion": "Elephant", "Elephant": "Lion",
        "Goat": "Monkey", "Monkey": "Goat",
        "Cow": "Tiger", "Tiger": "Cow",
    }
    yoni_animals = ["Horse", "Elephant", "Goat", "Serpent", "Dog", "Cat",
                    "Rat", "Cow", "Buffalo", "Tiger", "Hare", "Mongoose",
                    "Monkey", "Lion"]
    for y1 in yoni_animals:
        for y2 in yoni_animals:
            if y1 == y2:
                pts, rel = 4, "same_yoni"
            elif yoni_enemies.get(y1) == y2:
                pts, rel = 0, "enemy"
            else:
                pts, rel = 2, "friendly"
            rows.append(dict(
                matrix_type="yoni_kuta", from_key=y1, to_key=y2,
                relation_value=rel,
                guna_points=pts, max_points=4, notes=None,
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    # ── 4. Tara Kuta (27×27, max 3 gunas) ────────────────────────────────────
    tara_map = {
        1: ("Janma", 0), 2: ("Sampat", 2), 3: ("Vipat", 0),
        4: ("Kshema", 2), 5: ("Pratyari", 0), 6: ("Sadhaka", 1.5),
        7: ("Vadha", 0), 8: ("Mitra", 2), 9: ("Atimitra", 2),
    }
    for from_id in range(1, 28):
        for to_id in range(1, 28):
            dist = (to_id - from_id) % 27 or 27
            tara_pos = ((dist - 1) % 9) + 1
            tara_name, pts = tara_map[tara_pos]
            rows.append(dict(
                matrix_type="tara_kuta",
                from_key=str(from_id), to_key=str(to_id),
                relation_value=tara_name,
                guna_points=pts, max_points=3,
                notes=f"dist={dist},pos={tara_pos}",
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    # ── 5. Rajju (nakshatra → rajju group membership) ─────────────────────────
    rajju_groups = {
        "Padha_Aroha":  ([2, 16, 21], "aroha"),
        "Padha_Avaroha":([6, 11, 27], "avaroha"),
        "Kati_Aroha":   ([3, 15, 20], "aroha"),
        "Kati_Avaroha": ([7, 12, 26], "avaroha"),
        "Nabhi_Aroha":  ([4, 14, 19], "aroha"),
        "Nabhi_Avaroha":([8, 13, 25], "avaroha"),
        "Kantha_Aroha": ([5, 9, 18],  "aroha"),
        "Kantha_Avaroha":([1, 22, 24],"avaroha"),
        "Shira":        ([10, 17, 23],"both"),
    }
    for rajju_name, (nak_ids, direction) in rajju_groups.items():
        for nak_id in nak_ids:
            rows.append(dict(
                matrix_type="rajju",
                from_key=str(nak_id), to_key=rajju_name,
                relation_value=direction,
                guna_points=None, max_points=None,
                notes=f"nakshatra_id={nak_id} → rajju '{rajju_name}'",
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    # ── 6. Varna Kuta (7×7, max 1 guna) ─────────────────────────────────────
    varnas_rank = {
        "Brahmin": 4, "Kshatriya": 3, "Vaishya": 2, "Shudra": 1,
        "Farmer": 1, "Butcher": 1, "Mleccha": 1,
    }
    all_varnas = list(varnas_rank.keys())
    for v1 in all_varnas:
        for v2 in all_varnas:
            pts = 1 if varnas_rank[v1] >= varnas_rank[v2] else 0
            rows.append(dict(
                matrix_type="varna_kuta", from_key=v1, to_key=v2,
                relation_value="compatible" if pts else "incompatible",
                guna_points=pts, max_points=1, notes=None,
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    # ── 7. Graha Maitri Kuta (7×7, max 5 gunas) ─────────────────────────────
    planet_friends: dict[str, list[str]] = {
        "sun":     ["moon", "mars", "jupiter"],
        "moon":    ["sun", "mercury"],
        "mars":    ["sun", "moon", "jupiter"],
        "mercury": ["sun", "venus"],
        "jupiter": ["sun", "moon", "mars"],
        "venus":   ["mercury", "saturn"],
        "saturn":  ["mercury", "venus"],
    }
    planet_enemies: dict[str, list[str]] = {
        "sun":     ["venus", "saturn"],
        "moon":    [],
        "mars":    ["mercury"],
        "mercury": ["moon"],
        "jupiter": ["mercury", "venus"],
        "venus":   ["sun", "moon"],
        "saturn":  ["sun", "moon", "mars"],
    }
    gm_score_map = {
        ("friend", "friend"): 5, ("friend", "neutral"): 4,
        ("neutral", "friend"): 4, ("neutral", "neutral"): 3,
        ("friend", "enemy"): 1, ("enemy", "friend"): 1,
        ("enemy", "neutral"): 0, ("neutral", "enemy"): 0,
        ("enemy", "enemy"): 0,
    }

    def _rel(p1: str, p2: str) -> str:
        if p2 in planet_friends.get(p1, []):
            return "friend"
        if p2 in planet_enemies.get(p1, []):
            return "enemy"
        return "neutral"

    planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
    for p1 in planets:
        for p2 in planets:
            r1, r2 = _rel(p1, p2), _rel(p2, p1)
            pts = gm_score_map.get((r1, r2), 3)
            rows.append(dict(
                matrix_type="graha_maitri_kuta",
                from_key=p1, to_key=p2,
                relation_value=f"{r1}_{r2}",
                guna_points=pts, max_points=5, notes=None,
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    # ── 8. Bhakoot Kuta (12×12, max 7 gunas) ─────────────────────────────────
    inauspicious = {(2, 12), (12, 2), (5, 9), (9, 5), (6, 8), (8, 6)}
    for sign1 in range(1, 13):
        for sign2 in range(1, 13):
            d_fwd = (sign2 - sign1) % 12 or 12
            d_rev = (sign1 - sign2) % 12 or 12
            pts = 0 if (d_fwd, d_rev) in inauspicious else 7
            rows.append(dict(
                matrix_type="bhakoot_kuta",
                from_key=str(sign1), to_key=str(sign2),
                relation_value=f"{d_fwd}/{d_rev}",
                guna_points=pts, max_points=7,
                notes=None,
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    # ── 9. Vedha pairs (13 pairs × 2 directions = 26 rows) ───────────────────
    vedha_pairs = [
        (1, 16), (2, 15), (3, 14), (4, 13), (5, 12), (6, 11), (7, 10),
        (8, 9), (17, 27), (18, 26), (19, 25), (20, 24), (21, 23),
    ]
    for (n1, n2) in vedha_pairs:
        for (fn, tn) in [(n1, n2), (n2, n1)]:
            rows.append(dict(
                matrix_type="vedha",
                from_key=str(fn), to_key=str(tn),
                relation_value="vedha_pair",
                guna_points=None, max_points=None, notes=None,
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    # ── 10. Vashya Kuta (5×5, max 2 gunas) ──────────────────────────────────
    vashya_scores = {
        ("Dwipada", "Dwipada"): 2, ("Chaturpada", "Chaturpada"): 2,
        ("Jalasheela", "Jalasheela"): 2, ("Keeta", "Keeta"): 2,
        ("Vanachara", "Vanachara"): 2,
        ("Dwipada", "Chaturpada"): 1, ("Chaturpada", "Dwipada"): 1,
        ("Jalasheela", "Chaturpada"): 1, ("Chaturpada", "Jalasheela"): 1,
    }
    vashya_groups = ["Dwipada", "Chaturpada", "Jalasheela", "Keeta", "Vanachara"]
    for v1 in vashya_groups:
        for v2 in vashya_groups:
            pts = vashya_scores.get((v1, v2), 0)
            rows.append(dict(
                matrix_type="vashya_kuta", from_key=v1, to_key=v2,
                relation_value="compatible" if pts > 0 else "incompatible",
                guna_points=pts, max_points=2, notes=None,
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    # ── 11. Mahendra (27×27) ─────────────────────────────────────────────────
    mahendra_dists = {4, 7, 10, 13, 16, 19, 22, 25}
    for from_id in range(1, 28):
        for to_id in range(1, 28):
            dist = (to_id - from_id) % 27 or 27
            is_m = dist in mahendra_dists
            rows.append(dict(
                matrix_type="mahendra",
                from_key=str(from_id), to_key=str(to_id),
                relation_value="mahendra" if is_m else "non_mahendra",
                guna_points=None, max_points=None,
                notes=f"dist={dist}",
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    # ── 12. Stree-Deergha (27×27) ────────────────────────────────────────────
    for from_id in range(1, 28):
        for to_id in range(1, 28):
            d_fwd = (to_id - from_id) % 27 or 27
            d_rev = (from_id - to_id) % 27 or 27
            min_d = min(d_fwd, d_rev)
            rows.append(dict(
                matrix_type="stree_deergha",
                from_key=str(from_id), to_key=str(to_id),
                relation_value="dosha" if min_d < 9 else "ok",
                guna_points=None, max_points=None,
                notes=f"min_dist={min_d}",
                tradition_scope="classical", classical_source="bphs:ch73",
            ))

    return rows


MATRICES: list[dict] = _build_matrices()

# Sanity checks
from collections import Counter as _Counter
_mt = _Counter(r['matrix_type'] for r in MATRICES)
assert _mt['tara_kuta'] == 729,   f"tara_kuta: expected 729, got {_mt['tara_kuta']}"
assert _mt['nadi_kuta'] == 9,     f"nadi_kuta: expected 9, got {_mt['nadi_kuta']}"
assert _mt['gana_kuta'] == 9,     f"gana_kuta: expected 9, got {_mt['gana_kuta']}"
assert _mt['yoni_kuta'] == 196,   f"yoni_kuta: expected 196, got {_mt['yoni_kuta']}"
assert _mt['vashya_kuta'] == 25,  f"vashya_kuta: expected 25, got {_mt['vashya_kuta']}"
assert _mt['mahendra'] == 729,    f"mahendra: expected 729, got {_mt['mahendra']}"
assert _mt['stree_deergha'] == 729, f"stree_deergha: expected 729, got {_mt['stree_deergha']}"
assert _mt['bhakoot_kuta'] == 144, f"bhakoot_kuta: expected 144, got {_mt['bhakoot_kuta']}"
assert _mt['vedha'] == 26,        f"vedha: expected 26, got {_mt['vedha']}"
assert _mt['varna_kuta'] == 49,   f"varna_kuta: expected 49, got {_mt['varna_kuta']}"
assert _mt['graha_maitri_kuta'] == 49, f"graha_maitri: expected 49, got {_mt['graha_maitri_kuta']}"

# ── Seed function ──────────────────────────────────────────────────────────────
import json as _json
import logging as _logging

_logger = _logging.getLogger(__name__)

_EXPECTED_FLOORS = {
    "reference_nakshatra": 28,
    "reference_nakshatra_pada": 108,
    "reference_nakshatra_matrix": 2700,   # actual is ~2721; floor is conservative
}


def seed_nakshatra(
    conn,
    build_id: str,
    *,
    dry_run: bool = False,
    autocommit: bool = False,
) -> dict[str, int]:
    """
    Insert bg_nakshatra data into the 3 reference tables.

    L0 idempotency: ON CONFLICT DO NOTHING.
    Caller owns the transaction; this function never commits.
    Returns row counts per table.
    """
    if dry_run:
        _logger.info("[bg_nakshatra] dry_run=True")
        return {
            "reference_nakshatra": len(NAKSHATRAS_ENRICHED),
            "reference_nakshatra_pada": len(PADAS),
            "reference_nakshatra_matrix": len(MATRICES),
        }

    counts: dict[str, int] = {}
    cur = conn.cursor()

    # ── GRAIN 1: reference_nakshatra ──────────────────────────────────────────
    inserted = 0
    for row in NAKSHATRAS_ENRICHED:
        cur.execute(
            """
            INSERT INTO reference_nakshatra (
                nakshatra_id, name_sa_iast, name_sa_devanagari, name_en, alt_names,
                start_longitude, end_longitude, span_degrees,
                rashis_spanned, degree_in_rashi_ranges,
                vimshottari_lord, presiding_deity, secondary_deities, ruling_planet,
                gana, nadi, yoni_en, yoni_sa, yoni_sex,
                varna, tatva, guna, pakshi, nakshatra_gender,
                muhurta_type, disha, favorable_acts, prohibited_acts,
                symbol, shakti, basis_above, basis_below, net_result,
                motivation, body_part,
                paramayus, naisargika_maturity_age, deity_domain,
                is_gandanta, is_mula_sangya, is_panchaka, is_abhijit,
                tradition_scope, classical_source, build_id
            ) VALUES (
                %(nakshatra_id)s, %(name_sa_iast)s, %(name_sa_devanagari)s,
                %(name_en)s, %(alt_names)s,
                %(start_longitude)s, %(end_longitude)s, %(span_degrees)s,
                %(rashis_spanned)s, %(degree_in_rashi_ranges)s,
                %(vimshottari_lord)s, %(presiding_deity)s, %(secondary_deities)s,
                %(ruling_planet)s,
                %(gana)s, %(nadi)s, %(yoni_en)s, %(yoni_sa)s, %(yoni_sex)s,
                %(varna)s, %(tatva)s, %(guna)s, %(pakshi)s, %(nakshatra_gender)s,
                %(muhurta_type)s, %(disha)s, %(favorable_acts)s, %(prohibited_acts)s,
                %(symbol)s, %(shakti)s, %(basis_above)s, %(basis_below)s,
                %(net_result)s, %(motivation)s, %(body_part)s,
                %(paramayus)s, %(naisargika_maturity_age)s, %(deity_domain)s,
                %(is_gandanta)s, %(is_mula_sangya)s, %(is_panchaka)s, %(is_abhijit)s,
                %(tradition_scope)s, %(classical_source)s, %(build_id)s
            )
            ON CONFLICT (nakshatra_id) DO NOTHING
            """,
            {**row,
             "degree_in_rashi_ranges": _json.dumps(row["degree_in_rashi_ranges"]),
             "build_id": build_id},
        )
        inserted += cur.rowcount
    counts["reference_nakshatra"] = inserted
    _logger.info("[bg_nakshatra] reference_nakshatra: %d inserted", inserted)

    # ── GRAIN 2: reference_nakshatra_pada ─────────────────────────────────────
    inserted = 0
    for row in PADAS:
        cur.execute(
            """
            INSERT INTO reference_nakshatra_pada (
                pada_id, nakshatra_id, pada_number, absolute_pada,
                start_longitude, end_longitude,
                pada_navamsa_sign, pada_lord, pada_akshara,
                bija_sound, mantra_prefix,
                pada_deity_nuance, element_shading, dosha_shading,
                tradition_scope, classical_source, build_id
            ) VALUES (
                %(pada_id)s, %(nakshatra_id)s, %(pada_number)s, %(absolute_pada)s,
                %(start_longitude)s, %(end_longitude)s,
                %(pada_navamsa_sign)s, %(pada_lord)s, %(pada_akshara)s,
                %(bija_sound)s, %(mantra_prefix)s,
                %(pada_deity_nuance)s, %(element_shading)s, %(dosha_shading)s,
                %(tradition_scope)s, %(classical_source)s, %(build_id)s
            )
            ON CONFLICT (nakshatra_id, pada_number) DO NOTHING
            """,
            {**row, "build_id": build_id},
        )
        inserted += cur.rowcount
    counts["reference_nakshatra_pada"] = inserted
    _logger.info("[bg_nakshatra] reference_nakshatra_pada: %d inserted", inserted)

    # ── GRAIN 3: reference_nakshatra_matrix ───────────────────────────────────
    inserted = 0
    for row in MATRICES:
        cur.execute(
            """
            INSERT INTO reference_nakshatra_matrix (
                matrix_type, from_key, to_key, relation_value,
                guna_points, max_points, notes,
                tradition_scope, classical_source, build_id
            ) VALUES (
                %(matrix_type)s, %(from_key)s, %(to_key)s, %(relation_value)s,
                %(guna_points)s, %(max_points)s, %(notes)s,
                %(tradition_scope)s, %(classical_source)s, %(build_id)s
            )
            ON CONFLICT (matrix_type, from_key, to_key) DO NOTHING
            """,
            {**row, "build_id": build_id},
        )
        inserted += cur.rowcount
    counts["reference_nakshatra_matrix"] = inserted
    _logger.info("[bg_nakshatra] reference_nakshatra_matrix: %d inserted", inserted)

    cur.close()
    return counts


def check_volume(conn) -> dict[str, dict]:
    """Return per-table {actual, floor, status} for the cockpit stats route."""
    cur = conn.cursor()
    results = {}
    for table, floor in _EXPECTED_FLOORS.items():
        cur.execute(f"SELECT count(*) FROM {table}")   # nosec: table names are hardcoded constants
        actual = cur.fetchone()[0]
        results[table] = {"actual": actual, "floor": floor, "status": "ok" if actual >= floor else "below_floor"}
    cur.close()
    return results

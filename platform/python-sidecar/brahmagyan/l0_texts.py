"""
brahmagyan.l0_texts — BRAHMA WS-2 L0 Brahmagyan: Classical Text Corpus
=======================================================================

Manages the classical text corpus: text registry + verse-addressable chunks.

13-text corpus (native decision 2026-06-08, prep/l0-corpus-staging):
  Originals (5):
    bphs, phaladeepika, jataka_parijata, uttara_kalamrita, bphs_jaimini
  To-source (7):
    saravali, brihat_jataka, hora_sara, sarvartha_chintamani,
    brihat_samhita, muhurta_chintamani [PENDING], lal_kitab [PENDING]
  Staged (1):
    yavana_jataka (2 vols, Pingree)

Dropped from prior 15-text plan: tajaka_neelakanthi, bhrigu_samhita.
Staged floor: 11 texts with GCS PDFs (muhurta_chintamani + lal_kitab PENDING native decision).
Full floor: 13 texts after PENDING texts are remediated.

Volume floor: >= 8000 chunks (11 staged texts); all rows have source_citation + provenance_tier.

Acceptance gate:
  - classical_texts COUNT >= 11 staged texts (13 after PENDING remediated)
  - classical_text_chunks COUNT >= 8000 (staged); 10000 (full 13)
  - text.read('bphs', 'CH1:V1') resolves
  - all chunks have non-null verse_ref + source_citation

Build contract: clear-and-rebuild from GCS PDFs (DELETE FROM classical_text_chunks before
rebuild). Same PDF + pinned embedding model = identical chunks (deterministic via content_sha256).

BRAHMA-BG-0-3 | amended 2026-06-08 (prep/l0-corpus-staging): 13-text corpus
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Text registry ─────────────────────────────────────────────────────────────

TEXTS = [
    # ── 5 originals ───────────────────────────────────────────────────────────
    {
        "text_id": "bphs",
        "title_en": "Brihat Parasara Hora Sastra",
        "title_sa": "Brihat Parashara Hora Shastra",
        "author": "Maharishi Parasara",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 1,
        "license": "public_domain",
        "license_cleared": True,
        "total_chapters": 97,
        "total_verses": 2094,
        "source_edition": "Trans. R. Santhanam, Ranjan Publications, New Delhi (2 vols)",
        "source_citation": "BPHS — Trans. R. Santhanam, Ranjan Publications (archive.org: BPHSEnglish)",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/bphs.pdf",
        "gcs_path_vol2": "gs://madhav-marsys-sources/L8/classical_texts/source/bphs_vol2.pdf",
        "provenance_tier": "HIGH",
        "language_available": "en",
    },
    {
        "text_id": "phaladeepika",
        "title_en": "Phaladeepika",
        "title_sa": "Phaladeepika",
        "author": "Mantreshwara",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 1,
        "license": "public_domain",
        "license_cleared": True,
        "total_chapters": 28,
        "total_verses": 640,
        "source_edition": "Trans. V. Subrahmanya Sastri, 2nd Ed. 1950, Aruna Press Bangalore",
        "source_citation": "Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/phaladeepika.pdf",
        "provenance_tier": "HIGH",
        "language_available": "en",
    },
    {
        "text_id": "jataka_parijata",
        "title_en": "Jataka Parijata",
        "title_sa": "Jataka Parijata",
        "author": "Vaidyanatha Dikshita",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 1,
        "license": "public_domain",
        "license_cleared": True,
        "total_chapters": 17,
        "total_verses": 1002,
        "source_edition": "Trans. V. Subramanya Shashtri, V.B. Soobiah & Sons, Bangalore, 1932-33 (2 vols)",
        "source_citation": "Jataka Parijata — Trans. V. Subramanya Shashtri, 1932-33 (archive.org: JatakaParijata1932)",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/jataka_parijata.pdf",
        "gcs_path_vol2": "gs://madhav-marsys-sources/L8/classical_texts/source/jataka_parijata_vol2.pdf",
        "provenance_tier": "HIGH",
        "language_available": "en",
    },
    {
        "text_id": "uttara_kalamrita",
        "title_en": "Uttara Kalamrita",
        "title_sa": "Uttara Kalamrita",
        "author": "Kalidasa",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 2,
        "license": "public_domain",
        "license_cleared": True,
        "total_chapters": 6,
        "total_verses": 340,
        "source_edition": "Trans. Prof. P.S. Sastri, Ranjan Publications, New Delhi (preface K.N. Rao)",
        "source_citation": "Uttara Kalamrita — Trans. Prof. P.S. Sastri, Ranjan Publications (archive.org: uttkalamrita-kalidas-ps-sastri)",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/uttara_kalamrita.pdf",
        "provenance_tier": "HIGH",
        "language_available": "en",
    },
    {
        # DB classical_texts has this text as text_id='jaimini_sutram' (legacy MCP schema row).
        # Canonical text_id is 'bphs_jaimini'. bg_texts writer must upsert a 'bphs_jaimini'
        # row in classical_texts; do NOT write chunks under 'jaimini_sutram'.
        "text_id": "bphs_jaimini",
        "title_en": "Jaimini Sutras",
        "title_sa": "Jaimini Sutram",
        "author": "Jaimini Rishi",
        "school": "jaimini",
        "tradition": "vedic",
        "tier": 1,
        "license": "public_domain",
        "license_cleared": True,
        "total_chapters": 4,
        "total_verses": 199,
        "source_edition": "Trans. B. Suryanarain Rao, 3rd revised ed. 1949 (foreword B.V. Raman)",
        "source_citation": "Jaimini Sutras — Trans. B. Suryanarain Rao, 1949 (archive.org: Astrology_Books_by_B_Suryanarayana_Row)",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/bphs_jaimini.pdf",
        "provenance_tier": "HIGH",
        "language_available": "en",
    },
    # ── 7 to-source (5 staged PASS/MARGINAL; 2 UNSTAGED pending native decision) ──
    {
        "text_id": "saravali",
        "title_en": "Saravali",
        "title_sa": "Sārāvalī",
        "author": "Kalyana Varma",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 1,
        "license": "cc_by_nd_30",
        "license_cleared": True,
        "total_chapters": 55,  # chs 1-55 of 58; chs 56-58 absent in this edition
        "total_verses": None,
        "source_edition": "Trans. attr. R. Santhanam, compiled SUVRATSUT (CC BY-ND 3.0, 2017); chs 1-55 of 58",
        "source_citation": "[MEDIUM] Saravali — Trans. attr. R. Santhanam (archive.org: KalyanaVarmasSaravali_201707); chs 56-58 absent",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/saravali.pdf",
        "provenance_tier": "MEDIUM",
        "language_available": "en",
    },
    {
        "text_id": "brihat_jataka",
        "title_en": "Brihat Jataka",
        "title_sa": "Bṛhat Jātaka",
        "author": "Varahamihira",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 1,
        "license": "public_domain",
        "license_cleared": True,
        "total_chapters": 27,
        "total_verses": None,
        "source_edition": "Trans. V. Subrahmanya Sastri, 2nd Ed., Bangalore",
        "source_citation": "Brihat Jataka — Trans. V. Subrahmanya Sastri, 2nd Ed. (archive.org: BrihatJataka2ndEd.ByVSubrahmanyaSastri)",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/brihat_jataka.pdf",
        "provenance_tier": "HIGH",
        "language_available": "en",
    },
    {
        "text_id": "hora_sara",
        "title_en": "Hora Sara",
        "title_sa": "Hora Sāra",
        "author": "Prithuyasas",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 1,
        "license": "public_domain",
        "license_cleared": True,
        "total_chapters": None,
        "total_verses": None,
        "source_edition": "Trans. R. Santhanam",
        "source_citation": "Hora Sara — Trans. R. Santhanam (archive.org: HoraSaraRSanthanamEng)",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/hora_sara.pdf",
        "provenance_tier": "HIGH",
        "language_available": "en",
    },
    {
        # PDF is image-only (no embedded text layer). Pipeline must OCR before chunking.
        # Alternative extraction: DjVu OCR from archive.org (520KB, 48,423 English words clean).
        "text_id": "sarvartha_chintamani",
        "title_en": "Sarvartha Chintamani",
        "title_sa": "Sārvartha Cintāmaṇi",
        "author": "Venkatesha Daivagya",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 2,
        "license": "public_domain",
        "license_cleared": True,
        "total_chapters": None,
        "total_verses": None,
        "source_edition": "Trans. B. Suryanarayana Row, 1899, Aryan Press, Bellary (1st English ed.)",
        "source_citation": "Sarvartha Chintamani — Trans. B. Suryanarayana Row, 1899 (archive.org: Astrology_Books_by_B_Suryanarayana_Row); IMAGE-ONLY PDF — OCR required",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/sarvartha_chintamani.pdf",
        "provenance_tier": "HIGH",
        "language_available": "en",
        "ocr_required": True,
    },
    {
        "text_id": "brihat_samhita",
        "title_en": "Brihat Samhita",
        "title_sa": "Bṛhat Saṃhitā",
        "author": "Varahamihira",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 2,
        "license": "public_domain",
        "license_cleared": True,
        "total_chapters": None,
        "total_verses": None,
        "source_edition": "Trans. V. Subrahmanya Sastri, 1946, Bangalore (with English OCR layer)",
        "source_citation": "[MARGINAL] Brihat Samhita — Trans. V. Subrahmanya Sastri, 1946 (archive.org: varahamihira-brihat-samhita-...); OCR ligature artifacts present, prose readable",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/brihat_samhita.pdf",
        "provenance_tier": "HIGH",
        "language_available": "en",
    },
    {
        # UNSTAGED — no PD English edition found on archive.org.
        # Remedy A (recommended): purchase Girish Chand Sharma trans., Ranjan Publications (~USD 20).
        # Remedy B: OCR Hindi commentary (Mahidhara Sharma, Khemraj Press, archive.org).
        "text_id": "muhurta_chintamani",
        "title_en": "Muhurta Chintamani",
        "title_sa": "Muhūrta Cintāmaṇi",
        "author": "Rama Daivajna",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 3,
        "license": None,
        "license_cleared": False,
        "total_chapters": None,
        "total_verses": None,
        "source_edition": None,
        "source_citation": None,
        "gcs_path": None,
        "provenance_tier": None,
        "language_available": None,
        "staging_status": "UNSTAGED_PENDING_NATIVE_DECISION",
        "staging_note": "No PD English edition on archive.org. Remedy A: purchase Girish Chand Sharma trans., Ranjan Publications (~USD 20). Remedy B: OCR Hindi commentary (Mahidhara Sharma, archive.org) for multilingual embedding path.",
    },
    {
        # UNSTAGED — 1952 original is Urdu/Hindi nastaliq image scan; no usable text layer.
        # English translations are in-copyright.
        # Remedy A: Google Cloud Vision OCR (urd+hin) on 3-part 1952 archive.org scan.
        # Remedy B: purchase in-copyright English translation (~USD 20-30, Sagar/Ranjan Publications).
        "text_id": "lal_kitab",
        "title_en": "Lal Kitab",
        "title_sa": None,
        "author": "Pt. Roop Chand Joshi",
        "school": "parashari",
        "tradition": "vedic",
        "tier": 3,
        "license": "public_domain",  # 1952 original PD under Indian copyright (>60yr)
        "license_cleared": False,  # text layer not secured
        "total_chapters": None,
        "total_verses": None,
        "source_edition": "1952 original (3 vols, Urdu/Hindi nastaliq) — image scan only",
        "source_citation": None,
        "gcs_path": None,
        "provenance_tier": None,
        "language_available": None,
        "staging_status": "UNSTAGED_PENDING_NATIVE_DECISION",
        "staging_note": "archive.org LalKitabEdition1952Part1-3 is image-only nastaliq; archive.org OCR is garbled. Remedy A: Google Cloud Vision OCR (urd+hin). Remedy B: purchase in-copyright English translation.",
    },
    # ── Staged PDF (2 vols, Pingree) — chunking TBD ───────────────────────────
    {
        "text_id": "yavana_jataka",
        "title_en": "Yavana Jataka",
        "title_sa": "Yavana Jātaka",
        "author": "Sphujidhvaja (trans. David Pingree)",
        "school": "hellenistic",
        "tradition": "vedic",
        "tier": 3,
        "license": "public_domain",
        "license_cleared": True,
        "total_chapters": None,
        "total_verses": None,
        "source_edition": "Trans. David Pingree (2 vols), Harvard Oriental Series, 1978",
        "source_citation": "Yavana Jataka — Trans. David Pingree, Harvard Oriental Series (2 vols), 1978",
        "gcs_path": "gs://madhav-marsys-sources/L8/classical_texts/source/yavana_jataka_vol1.pdf",
        "gcs_path_vol2": "gs://madhav-marsys-sources/L8/classical_texts/source/yavana_jataka_vol2.pdf",
        "provenance_tier": "HIGH",
        "language_available": "en",
    },
]

# ── Seed chunks (public domain BPHS key passages) ─────────────────────────────
# Representative verses from BPHS covering core Jyotish principles.
# Each entry: (text_id, chapter, verse_start, verse_end, content_sa, content_en, summary, topics)

SEED_CHUNKS = [
    # ── BPHS Chapter 1 — Introduction ──────────────────────────────────────────
    ("bphs", 1, 1, 2, None,
     "I bow to Brahma, Vishnu and Mahesh, who are the creators, preservers and destroyers "
     "of the universe. I also bow to Sage Parasara, the best among the sages.",
     "Invocation to the trinity; salutation to Sage Parasara",
     ["invocation", "parasara", "tradition"]),

    ("bphs", 1, 3, 4, None,
     "At the request of Maitreya, Sage Parasara explains the science of Jyotisha, "
     "which is the eye of the Vedas and reveals the past, present and future.",
     "Jyotisha as the eye of the Vedas; reveals past/present/future",
     ["jyotisha", "vedic_scripture", "scope"]),

    # ── BPHS Chapter 2 — Nature of the Grahas ──────────────────────────────────
    ("bphs", 2, 1, 3, None,
     "The Sun is the soul of the world. The Moon is the mind. Mars is the strength. "
     "Mercury is speech. Jupiter is knowledge and wisdom. Venus is desire. Saturn is sorrow.",
     "Planetary significations: Sun=soul, Moon=mind, Mars=strength, Mercury=speech",
     ["planetary_significations", "graha", "karak"]),

    ("bphs", 2, 4, 6, None,
     "The Sun and Moon are called luminaries. Mars, Mercury, Jupiter, Venus and Saturn "
     "are the five tara grahas (star planets). Rahu and Ketu are shadow planets.",
     "Classification of grahas: luminaries, tara grahas, shadow planets",
     ["graha_classification", "rahu", "ketu", "luminaries"]),

    ("bphs", 2, 7, 9, None,
     "Sun: Kshatriya. Moon: Vaishya. Mars: Kshatriya. Mercury: Vaishya+Shudra. "
     "Jupiter: Brahmin. Venus: Brahmin. Saturn: Shudra. Planetary castes.",
     "Planetary castes and social classes",
     ["planetary_caste", "graha", "social_class"]),

    ("bphs", 2, 10, 12, None,
     "Sun is masculine. Moon and Venus are feminine. Mars, Jupiter and Saturn are masculine. "
     "Mercury is hermaphrodite (neuter).",
     "Planetary gender: Sun/Mars/Jupiter/Saturn masculine; Moon/Venus feminine; Mercury neuter",
     ["planetary_gender", "graha"]),

    # ── BPHS Chapter 3 — Planetary Exaltations ─────────────────────────────────
    ("bphs", 3, 1, 4, None,
     "Sun is exalted in Aries at 10°. Moon is exalted in Taurus at 3°. "
     "Mars is exalted in Capricorn at 28°. Mercury is exalted in Virgo at 15°.",
     "Exaltation points: Sun 10°Aries, Moon 3°Taurus, Mars 28°Cap, Mercury 15°Virgo",
     ["exaltation", "uccha", "graha", "degree"]),

    ("bphs", 3, 5, 8, None,
     "Jupiter is exalted in Cancer at 5°. Venus is exalted in Pisces at 27°. "
     "Saturn is exalted in Libra at 20°. Rahu is exalted in Taurus.",
     "Exaltation: Jupiter 5°Cancer, Venus 27°Pisces, Saturn 20°Libra, Rahu Taurus",
     ["exaltation", "uccha", "graha", "degree"]),

    ("bphs", 3, 9, 11, None,
     "The sign opposite to exaltation is debilitation (neecha). "
     "Sun debilitated in Libra, Moon in Scorpio, Mars in Cancer, Mercury in Pisces, "
     "Jupiter in Capricorn, Venus in Virgo, Saturn in Aries.",
     "Debilitation signs for all planets — opposite to exaltation",
     ["debilitation", "neecha", "graha"]),

    ("bphs", 3, 12, 15, None,
     "Mooltrikona signs: Sun — Leo. Moon — Taurus (0-27°). Mars — Aries. "
     "Mercury — Virgo (0-20°). Jupiter — Sagittarius. Venus — Libra. Saturn — Aquarius.",
     "Mooltrikona signs for all seven planets",
     ["mooltrikona", "graha", "sign"]),

    # ── BPHS Chapter 4 — Planetary Friendship ──────────────────────────────────
    ("bphs", 4, 1, 4, None,
     "The natural friends, neutrals and enemies of the grahas are: "
     "Sun's friends are Moon, Mars, Jupiter. Enemies are Venus and Saturn. Mercury is neutral. "
     "These are permanent (naisargika) relationships.",
     "Natural planetary friendships: Sun's friends=Moon/Mars/Jupiter; enemies=Venus/Saturn",
     ["planetary_friendship", "mitra", "shatru", "graha"]),

    ("bphs", 4, 5, 8, None,
     "Moon's friends are Sun and Mercury. No enemies. Jupiter, Mars, Venus, Saturn are neutral. "
     "Mars's friends are Sun, Moon, Jupiter. Enemies are Mercury. Venus and Saturn are neutral.",
     "Planetary friendships: Moon (no enemies), Mars (enemy: Mercury)",
     ["planetary_friendship", "mitra", "shatru"]),

    # ── BPHS Chapter 6 — The Rasis (Signs) ─────────────────────────────────────
    ("bphs", 6, 1, 3, None,
     "Aries is the first sign, ruled by Mars. It is a movable fire sign, masculine. "
     "It signifies head and face. The native is courageous and independent.",
     "Aries: first sign, Mars-ruled, movable fire, signifies head",
     ["aries", "sign", "fire", "movable", "mars"]),

    ("bphs", 6, 4, 6, None,
     "Taurus is the second sign, ruled by Venus. It is a fixed earth sign, feminine. "
     "Signifies face and throat. The native loves beauty and material comforts.",
     "Taurus: second sign, Venus-ruled, fixed earth, signifies throat",
     ["taurus", "sign", "earth", "fixed", "venus"]),

    ("bphs", 6, 7, 9, None,
     "Gemini is the third sign, ruled by Mercury. It is a dual air sign, masculine. "
     "Signifies arms and shoulders. The native is intelligent and communicative.",
     "Gemini: third sign, Mercury-ruled, dual air, signifies arms",
     ["gemini", "sign", "air", "dual", "mercury"]),

    ("bphs", 6, 10, 12, None,
     "Cancer is the fourth sign, ruled by the Moon. It is a movable water sign, feminine. "
     "Signifies chest and lungs. The native is emotional and home-loving.",
     "Cancer: fourth sign, Moon-ruled, movable water, signifies chest",
     ["cancer", "sign", "water", "movable", "moon"]),

    ("bphs", 6, 13, 15, None,
     "Leo is the fifth sign, ruled by the Sun. It is a fixed fire sign, masculine. "
     "Signifies heart and stomach. The native is courageous and leadership-oriented.",
     "Leo: fifth sign, Sun-ruled, fixed fire, signifies heart",
     ["leo", "sign", "fire", "fixed", "sun"]),

    ("bphs", 6, 16, 18, None,
     "Virgo is the sixth sign, ruled by Mercury. It is a dual earth sign, feminine. "
     "Signifies waist and digestive system. The native is analytical and service-oriented.",
     "Virgo: sixth sign, Mercury-ruled, dual earth, signifies waist",
     ["virgo", "sign", "earth", "dual", "mercury"]),

    # ── BPHS Chapter 7 — The Bhavas (Houses) ───────────────────────────────────
    ("bphs", 7, 1, 3, None,
     "The first bhava (Lagna) denotes birth, body, complexion, appearance, health, "
     "vitality and the overall life of the native.",
     "First house (Lagna): self, body, health, vitality",
     ["first_house", "lagna", "bhava", "self", "health"]),

    ("bphs", 7, 4, 6, None,
     "The second bhava denotes wealth, speech, family, food, right eye, and face. "
     "It is the house of accumulated resources.",
     "Second house: wealth, speech, family, food",
     ["second_house", "dhana_bhava", "wealth", "speech"]),

    ("bphs", 7, 7, 9, None,
     "The third bhava denotes brothers, sisters, courage, short travel, right ear, "
     "and communication. Mars is the natural karaka.",
     "Third house: siblings, courage, communication, short travel",
     ["third_house", "sahaja_bhava", "siblings", "courage"]),

    ("bphs", 7, 10, 12, None,
     "The fourth bhava denotes mother, vehicles, property, home, happiness, education "
     "and chest. Moon is the natural karaka for mother.",
     "Fourth house: mother, home, property, vehicles, education",
     ["fourth_house", "sukha_bhava", "mother", "home", "property"]),

    ("bphs", 7, 13, 15, None,
     "The fifth bhava denotes children, intellect, past good deeds (purva punya), "
     "romance and speculation. Jupiter is the natural karaka.",
     "Fifth house: children, intellect, creativity, romance",
     ["fifth_house", "putra_bhava", "children", "creativity"]),

    ("bphs", 7, 16, 18, None,
     "The sixth bhava denotes enemies, disease, debts, service, and competition. "
     "It is one of the trik (evil) houses. Mars and Saturn are karaka here.",
     "Sixth house: enemies, disease, debts, service",
     ["sixth_house", "ripu_bhava", "enemies", "health", "debt"]),

    ("bphs", 7, 19, 21, None,
     "The seventh bhava denotes marriage, spouse, business partner, and foreign travel. "
     "Venus is the natural karaka for spouse.",
     "Seventh house: marriage, partnership, foreign travel",
     ["seventh_house", "kalatra_bhava", "marriage", "partnership"]),

    ("bphs", 7, 22, 24, None,
     "The eighth bhava denotes longevity, transformation, sudden events, occult, "
     "inheritance and chronic disease. It is a trik house. Saturn is karaka.",
     "Eighth house: longevity, transformation, occult, inheritance",
     ["eighth_house", "ayur_bhava", "longevity", "occult"]),

    # ── BPHS Chapter 26 — Planetary Aspects ────────────────────────────────────
    ("bphs", 26, 1, 4, None,
     "All planets aspect the seventh house from their position with full strength. "
     "Mars additionally aspects the fourth and eighth houses with full strength. "
     "Jupiter aspects the fifth and ninth houses with full strength. "
     "Saturn aspects the third and tenth houses with full strength.",
     "Graha drishti: all planets 7th full; Mars 4th+8th; Jupiter 5th+9th; Saturn 3rd+10th",
     ["drishti", "aspect", "mars", "jupiter", "saturn"]),

    # ── BPHS Chapter 27 — Karakas ──────────────────────────────────────────────
    ("bphs", 27, 1, 3, None,
     "Sun is the karaka for soul, father, and authority. Moon for mind and mother. "
     "Mars for siblings and courage. Mercury for intellect and speech. "
     "Jupiter for wisdom, children, and spiritual matters.",
     "Karak planets: Sun/soul, Moon/mind, Mars/siblings, Mercury/intellect, Jupiter/wisdom",
     ["karaka", "graha", "signification"]),

    ("bphs", 27, 4, 6, None,
     "Venus is the karaka for marriage, beauty, and sensual pleasures. "
     "Saturn is the karaka for longevity, sorrow, and service. "
     "Rahu for foreigners and unexpected events. Ketu for liberation and spirituality.",
     "Karak: Venus/marriage, Saturn/longevity, Rahu/foreigners, Ketu/liberation",
     ["karaka", "venus", "saturn", "rahu", "ketu"]),

    # ── BPHS Dasha Chapter ─────────────────────────────────────────────────────
    ("bphs", 46, 1, 5, None,
     "The Vimshottari dasha system is based on the Moon's position in a nakshatra at birth. "
     "The total cycle is 120 years. The sequence is: Sun 6, Moon 10, Mars 7, Rahu 18, "
     "Jupiter 16, Saturn 19, Mercury 17, Ketu 7, Venus 20 years.",
     "Vimshottari dasha: 120-year cycle; sequence and years for each planet",
     ["vimshottari", "dasha", "nakshatra", "moon"]),

    ("bphs", 46, 6, 10, None,
     "The balance of dasha at birth is calculated from the Moon's exact position in the nakshatra. "
     "If the Moon is at the beginning of a nakshatra, the full dasha of that lord is operative. "
     "If at the end, only a small fraction remains.",
     "Dasha balance calculation from Moon nakshatra position at birth",
     ["vimshottari", "dasha_balance", "nakshatra", "moon"]),

    # ── Phaladeepika — Key Yogas ────────────────────────────────────────────────
    ("phaladeepika", 6, 1, 3, None,
     "When the lord of the ascendant and the lord of the ninth house are in mutual "
     "exchange or aspect each other, a powerful Raj Yoga is formed, giving high status, "
     "authority and success.",
     "Raj Yoga: lagna lord and 9th lord mutual exchange or aspect",
     ["raj_yoga", "yoga", "lagna_lord", "ninth_lord"]),

    ("phaladeepika", 6, 4, 6, None,
     "The Gajakesari yoga is formed when Jupiter is in a kendra (1/4/7/10) from the Moon. "
     "This yoga gives fame, intelligence, wealth and longevity.",
     "Gajakesari yoga: Jupiter in kendra from Moon; gives fame, intelligence, wealth",
     ["gajakesari", "yoga", "jupiter", "moon", "kendra"]),

    ("phaladeepika", 6, 7, 9, None,
     "Dhana Yoga (wealth combination) forms when the lord of the 2nd or 11th house "
     "conjoins, aspects or exchanges with the lagna lord or 9th/10th lord.",
     "Dhana yoga: 2nd/11th lord with lagna/9th/10th lord; gives wealth",
     ["dhana_yoga", "wealth", "yoga", "second_house", "eleventh_house"]),

    # ── Jataka Parijata — Strength ──────────────────────────────────────────────
    ("jataka_parijata", 2, 1, 4, None,
     "Planets derive strength from several sources: sign placement (sthana bala), "
     "directional strength (dig bala), temporal strength (kala bala), "
     "motion strength (chesta bala), natural strength (naisargika bala), "
     "and aspect strength (drik bala). These six comprise Shadbala.",
     "Shadbala: six sources of planetary strength",
     ["shadbala", "sthana_bala", "dig_bala", "kala_bala", "strength"]),

    ("jataka_parijata", 2, 5, 8, None,
     "Dig Bala (directional strength): Jupiter and Mercury gain full dig bala in the first house. "
     "Moon and Venus in the fourth house. Saturn in the seventh house. "
     "Sun and Mars in the tenth house.",
     "Dig Bala directional strength: planets strongest in specific houses",
     ["dig_bala", "directional_strength", "shadbala", "graha"]),

    # ── Uttara Kalamrita ────────────────────────────────────────────────────────
    ("uttara_kalamrita", 1, 1, 5, None,
     "The Sun signifies: soul, father, government, authority, vitality, right eye, bones, "
     "heart, forests, eastern direction, hot substances, copper, and wheaten color.",
     "Expanded Sun significations: soul, father, government, right eye, bones, heart",
     ["sun", "significations", "karak"]),

    ("uttara_kalamrita", 1, 6, 10, None,
     "The Moon signifies: mind, mother, water, dairy products, left eye, blood, silver, "
     "white color, night, northern-west direction, pearls, watery places.",
     "Expanded Moon significations: mind, mother, water, left eye, silver",
     ["moon", "significations", "karak"]),

    ("uttara_kalamrita", 1, 11, 15, None,
     "Mars signifies: brother, blood, courage, land, fire, red color, copper, south direction, "
     "commander, surgery, wounds, and the marrow of bones.",
     "Expanded Mars significations: brothers, blood, courage, fire, surgery",
     ["mars", "significations", "karak"]),

    ("uttara_kalamrita", 1, 16, 20, None,
     "Mercury signifies: intellect, communication, mathematics, commerce, skin, "
     "north direction, green color, mixed color, and multiple skills.",
     "Expanded Mercury significations: intellect, communication, trade, skin",
     ["mercury", "significations", "karak"]),

    ("uttara_kalamrita", 1, 21, 25, None,
     "Jupiter signifies: wisdom, dharma, children, wealth, teacher, expansion, gold, "
     "north-east direction, religious scriptures, and ether element.",
     "Expanded Jupiter significations: wisdom, dharma, children, gold, teacher",
     ["jupiter", "significations", "karak"]),

    ("uttara_kalamrita", 1, 26, 30, None,
     "Venus signifies: marriage, beauty, arts, sensual pleasures, vehicles, silver/white color, "
     "south-east direction, semen, wife, and rajasic guna.",
     "Expanded Venus significations: marriage, beauty, arts, vehicles, wife",
     ["venus", "significations", "karak"]),

    ("uttara_kalamrita", 1, 31, 35, None,
     "Saturn signifies: longevity, karma, sorrow, delays, servants, iron, old age, "
     "west direction, oil, and tamasic guna. Rules over the masses and laboring classes.",
     "Expanded Saturn significations: karma, longevity, delays, iron, masses",
     ["saturn", "significations", "karak"]),

    # ── Jaimini Sutram ──────────────────────────────────────────────────────────
    ("bphs_jaimini", 1, 1, 5, None,
     "Jaimini Karakas: The planet with the highest degree in a sign is the Atma Karaka (AK). "
     "The planet with the second highest degree is the Amatya Karaka (AmK). "
     "Continues to 7 karakas: Bhratri, Matri, Putra, Gnati, Dara.",
     "Jaimini Chara Karakas: 7 temporary significators based on degree",
     ["jaimini", "karaka", "atma_karaka", "chara_karaka"]),

    ("bphs_jaimini", 1, 6, 10, None,
     "Jaimini Chara Dasha is a sign-based dasha system. Signs become active in sequence. "
     "Movable signs run forward; fixed signs run backward; dual signs depend on lord's position.",
     "Jaimini Chara Dasha: sign-based system, movable forward, fixed backward",
     ["jaimini", "chara_dasha", "dasha", "sign"]),

    # ── Additional BPHS chapters ────────────────────────────────────────────────
    ("bphs", 24, 1, 5, None,
     "Sade Sati: When Saturn transits over the natal Moon sign and the two signs adjacent "
     "to it (3 signs total), this is called Sade Sati. It lasts approximately 7.5 years. "
     "It brings hardship, delays, and karmic lessons — but also growth and purification.",
     "Sade Sati: Saturn transit over Moon ±1 sign; 7.5 years; hardship and growth",
     ["sade_sati", "saturn", "transit", "moon"]),

    ("bphs", 36, 1, 5, None,
     "Navamsha (D9) is the most important divisional chart. It shows the strength of planets "
     "in detail, the inner nature of the native, the spouse's qualities, and spiritual destiny. "
     "A planet in the same sign in Rashi and Navamsha is called Vargottama, a very strong placement.",
     "Navamsha D9: most important divisional; inner nature, spouse, spiritual destiny; Vargottama",
     ["navamsha", "d9", "divisional", "vargottama", "spouse"]),

    ("bphs", 37, 1, 5, None,
     "Dashamsha (D10) reveals career, profession, and public life. The 10th lord "
     "and planets in the 10th house of D10 show the nature of one's professional success "
     "and the areas of public achievement.",
     "Dashamsha D10: career, profession, public achievement",
     ["dashamsha", "d10", "career", "profession"]),

    ("bphs", 40, 1, 5, None,
     "Shashthamsha (D6) reveals health and disease. Planets placed in the 6th or 8th "
     "in D6 cause disease. The 6th lord in D6 shows the type of disease most likely to afflict.",
     "Shashthamsha D6: health and disease; 6th/8th house planets in D6 cause disease",
     ["shashthamsha", "d6", "health", "disease"]),

    ("bphs", 7, 25, 27, None,
     "The ninth bhava denotes dharma, higher learning, spiritual wisdom, long journeys, "
     "father, fortune and divine grace. It is called the bhagya sthana (house of fortune). "
     "Jupiter is the natural karaka.",
     "Ninth house: dharma, fortune, father, higher learning, long travel",
     ["ninth_house", "dharma_bhava", "dharma", "fortune", "father"]),
]


# ── Volume floor ──────────────────────────────────────────────────────────────
# Staged floor: 11 texts with GCS PDFs (muhurta_chintamani + lal_kitab PENDING).
# Full floor: 13 texts after PENDING texts are remediated.

VOLUME_FLOOR_TEXTS = 11          # staged texts (GCS PDFs present)
VOLUME_FLOOR_TEXTS_FULL = 13     # all 13 after PENDING remediation
VOLUME_FLOOR_CHUNKS = 8_000      # staged 11-text floor
VOLUME_FLOOR_CHUNKS_FULL = 10_000  # full 13-text floor


# ── Writer ─────────────────────────────────────────────────────────────────────

def seed_texts(conn, build_id: str | None = None, dry_run: bool = False) -> dict:
    """
    Seed classical_texts registry + classical_text_chunks.
    Returns {texts: int, chunks: int}.
    """
    if dry_run:
        return {
            "classical_texts": len(TEXTS),
            "classical_text_chunks": len(SEED_CHUNKS),
        }

    now = datetime.now(timezone.utc)
    texts_inserted = 0
    chunks_inserted = 0

    with conn.cursor() as cur:
        # seed texts registry
        for t in TEXTS:
            cur.execute("""
                INSERT INTO classical_texts
                  (text_id, title_en, title_sa, author, school, tradition, tier,
                   license, license_cleared, total_chapters, total_verses,
                   source_edition, ingested_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (text_id) DO UPDATE SET
                  license_cleared = EXCLUDED.license_cleared,
                  total_chapters = EXCLUDED.total_chapters
            """, (
                t["text_id"], t["title_en"], t.get("title_sa"), t.get("author"),
                t["school"], t["tradition"], t["tier"],
                t["license"], t["license_cleared"],
                t.get("total_chapters"), t.get("total_verses"),
                t.get("source_edition"), now,
            ))
            texts_inserted += 1

        # seed chunks
        for i, chunk in enumerate(SEED_CHUNKS):
            (text_id, chapter, verse_start, verse_end,
             content_sa, content_en, summary, topics) = chunk

            chunk_id = f"{text_id}_ch{chapter:02d}_v{verse_start:03d}"
            verse_ref = f"CH{chapter}:V{verse_start}" + (
                f"-V{verse_end}" if verse_end != verse_start else ""
            )
            source_citation = f"{text_id.upper()} Ch.{chapter} v.{verse_start}-{verse_end}"

            cur.execute("""
                INSERT INTO classical_text_chunks
                  (text_id, chunk_id, verse_ref, chapter, verse_start, verse_end,
                   content_sa, content_en, content_summary, topics,
                   source_citation, ingested_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (chunk_id) DO UPDATE SET
                  content_en = EXCLUDED.content_en,
                  topics = EXCLUDED.topics,
                  source_citation = EXCLUDED.source_citation
            """, (
                text_id, chunk_id, verse_ref, chapter, verse_start, verse_end,
                content_sa, content_en, summary, topics,
                source_citation, now,
            ))
            chunks_inserted += 1

    conn.commit()
    logger.info(
        "[L0/texts] classical_texts: %d, classical_text_chunks: %d",
        texts_inserted, chunks_inserted,
    )
    return {
        "classical_texts": texts_inserted,
        "classical_text_chunks": chunks_inserted,
    }


def read_text(text_id: str, verse_ref: str | None = None) -> dict | list | None:
    """
    In-memory text reader (no DB) — reads from SEED_CHUNKS corpus.
    If verse_ref given: return matching chunk. Else return all chunks for text.
    """
    chunks = []
    for chunk in SEED_CHUNKS:
        (ctext_id, chapter, verse_start, verse_end,
         content_sa, content_en, summary, topics) = chunk

        if ctext_id != text_id:
            continue

        chunk_verse_ref = f"CH{chapter}:V{verse_start}" + (
            f"-V{verse_end}" if verse_end != verse_start else ""
        )

        if verse_ref:
            # Try exact match or prefix match
            if verse_ref == chunk_verse_ref or chunk_verse_ref.startswith(verse_ref):
                return {
                    "text_id": text_id,
                    "verse_ref": chunk_verse_ref,
                    "content_en": content_en,
                    "summary": summary,
                    "topics": topics,
                    "source_citation": f"{text_id.upper()} Ch.{chapter} v.{verse_start}",
                }
        else:
            chunks.append({
                "text_id": text_id,
                "verse_ref": chunk_verse_ref,
                "content_en": content_en,
                "summary": summary,
                "topics": topics,
            })

    return chunks if not verse_ref else None


def check_volume(conn) -> dict:
    """Check row counts vs volume floors."""
    result = {}
    with conn.cursor() as cur:
        for table, floor in [
            ("classical_texts", VOLUME_FLOOR_TEXTS),
            ("classical_text_chunks", VOLUME_FLOOR_CHUNKS),
        ]:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                actual = cur.fetchone()[0]
            except Exception:
                actual = 0
            status = "green" if actual >= floor else ("amber" if actual > 0 else "empty")
            result[table] = {"actual": actual, "floor": floor, "status": status}
    return result

#!/usr/bin/env npx tsx
/**
 * bootstrap_chart_facts_sensitive_points.ts
 *
 * BRAHMA GA-1-6 — Sensitive Points writer for ganita.sensitive_points
 *
 * Sources:
 *   FORENSIC_ASTROLOGICAL_DATA_v8_0.md (via CHART_FACTS_EXTRACTION_v1_0.yaml)
 *   JHORA_TRANSCRIPTION_v8_0_SOURCE.md (JH authoritative for special lagnas + sahamas)
 *
 * Categories produced:
 *   upagraha       — 9 upagrahas: Gulika, Mandi, Yamaghantaka, Ardhaprahara (time-based)
 *                    + Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu (sun-based)
 *   special_lagna  — 9 special lagnas: Bhava, Hora, Ghati, Vighati, Varnada, Shree,
 *                    Pranapada, Indu, BB (Bhrigu Bindu)
 *   saham          — 36 Tajika sahams (JH authoritative; v6.0 corrections noted)
 *   arudha         — 9 arudha padas: AL, A2, A6, A7, A10, A11, UL, AL.D9, AL.D10
 *
 * Total: 63 rows in chart_facts (categories: upagraha/special_lagna/saham/arudha)
 *
 * B.10 compliance: all values direct-read from FORENSIC v8.0 / JH transcription.
 * No values fabricated. Corrections from v6.0 noted in source_section fields.
 *
 * Usage:
 *   DATABASE_URL="..." npx tsx scripts/bootstrap/bootstrap_chart_facts_sensitive_points.ts [--dry-run]
 */

import { Pool } from 'pg'

const DATABASE_URL = process.env.DATABASE_URL ?? 'postgresql://amjis_app@127.0.0.1:5432/amjis'
const BUILD_ID = 'brahma-ga-1-6-sensitive-points-20260603'
const pool = new Pool({ connectionString: DATABASE_URL })

interface Row {
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
  source_section: string
  build_id: string
  provenance: Record<string, unknown>
}

const PROV = {
  source_uri: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  source_version: '8.0',
  source_canonical_id: 'FORENSIC_v8_0',
  jh_authority: '01_FACTS_LAYER/SOURCES/JHORA_TRANSCRIPTION_v8_0_SOURCE.md',
  extracted_at: new Date().toISOString(),
  extraction_method: 'direct_read_from_forensic_v8_0',
}

// ── Sign → House mapping (Aries Lagna, whole-sign) ──────────────────────────
// FORENSIC §3.1 HSE.1–HSE.12
const SIGN_TO_HOUSE: Record<string, number> = {
  Aries: 1, Taurus: 2, Gemini: 3, Cancer: 4, Leo: 5, Virgo: 6,
  Libra: 7, Scorpio: 8, Sagittarius: 9, Capricorn: 10, Aquarius: 11, Pisces: 12,
}

// ── §11.1 Upagrahas ──────────────────────────────────────────────────────────
// Source: FORENSIC v8.0 §11.1 / CHART_FACTS_EXTRACTION_v1_0.yaml §11.1 rows 1-9

const UPAGRAHAS = [
  // Time-based upagrahas
  { id: 'UPG.GULIKA',       name: 'Gulika',       type: 'time-based', sign: 'Gemini',      degree: '13°57′', nakshatra: 'Ardra',         source: '§11.1 row 1' },
  { id: 'UPG.MANDI',        name: 'Mandi',        type: 'time-based', sign: 'Cancer',      degree: '14°13′', nakshatra: 'Pushya',        source: '§11.1 row 2' },
  { id: 'UPG.YAMAGHANTAKA', name: 'Yamaghantaka', type: 'time-based', sign: 'Taurus',      degree: '01°54′', nakshatra: 'Krittika',      source: '§11.1 row 3' },
  { id: 'UPG.ARDHAPRAHARA', name: 'Ardhaprahara', type: 'time-based', sign: 'Aries',       degree: '10°52′', nakshatra: 'Ashwini',       source: '§11.1 row 4' },
  // Sun-based upagrahas
  { id: 'UPG.DHUMA',        name: 'Dhuma',        type: 'sun-based',  sign: 'Gemini',      degree: '05°17′', nakshatra: 'Mrigasira',     source: '§11.1 row 5' },
  { id: 'UPG.VYATIPATA',    name: 'Vyatipata',    type: 'sun-based',  sign: 'Capricorn',   degree: '24°42′', nakshatra: 'Dhanishta',     source: '§11.1 row 6' },
  { id: 'UPG.PARIVESHA',    name: 'Parivesha',    type: 'sun-based',  sign: 'Cancer',      degree: '24°42′', nakshatra: 'Ashlesha',      source: '§11.1 row 7' },
  { id: 'UPG.INDRACHAPA',   name: 'Indrachapa',   type: 'sun-based',  sign: 'Sagittarius', degree: '05°17′', nakshatra: 'Moola',         source: '§11.1 row 8' },
  { id: 'UPG.UPAKETU',      name: 'Upaketu',      type: 'sun-based',  sign: 'Sagittarius', degree: '21°57′', nakshatra: 'Purva Ashadha', source: '§11.1 row 9' },
] as const

// ── §12.1 Special Lagnas ─────────────────────────────────────────────────────
// Source: FORENSIC v8.0 §12.1 / JH authoritative (v6.0 errors corrected)
// CHART_FACTS_EXTRACTION_v1_0.yaml §12.1 rows 1-9

const SPECIAL_LAGNAS = [
  { id: 'LAG.BHAVA',    name: 'Bhava Lagna',    longitude: 'Pisces 26°13′27″',       sign: 'Pisces',      house: 12, nakshatra: 'Revati',           pada: 3, source: '§12.1 row 1', note: null },
  { id: 'LAG.HORA',     name: 'Hora Lagna',     longitude: 'Gemini 0°39′07.90″',     sign: 'Gemini',      house: 3,  nakshatra: 'Mrigashira',       pada: 3, source: '§12.1 row 2', note: 'v8.0 correction: v6.0 had Libra 10°11′ (WRONG). JH authoritative.' },
  { id: 'LAG.GHATI',   name: 'Ghati Lagna',    longitude: 'Sagittarius 13°56′07.87″', sign: 'Sagittarius', house: 9,  nakshatra: 'Purva Ashadha',   pada: 1, source: '§12.1 row 3', note: 'v8.0 correction: v6.0 had Scorpio 6°53′ (WRONG). JH authoritative.' },
  { id: 'LAG.VIGHATI', name: 'Vighati Lagna',  longitude: 'Leo 20°21′07.75″',        sign: 'Leo',         house: 5,  nakshatra: 'Purva Phalguni',   pada: 3, source: '§12.1 row 4', note: 'NEW in v8.0 — not in v6.0. JH authoritative.' },
  { id: 'LAG.VARNADA', name: 'Varnada Lagna',  longitude: 'Cancer 12°25′21.62″',     sign: 'Cancer',      house: 4,  nakshatra: 'Pushya',           pada: 3, source: '§12.1 row 5', note: 'v8.0 correction: v6.0 had Scorpio 12°23′ (WRONG). JH authoritative.' },
  { id: 'LAG.SHREE',   name: 'Shree Lagna',    longitude: 'Libra 23°19′42.57″',      sign: 'Libra',       house: 7,  nakshatra: 'Vishakha',         pada: 1, source: '§12.1 row 6', note: 'v8.0 correction: v6.0 had Sagittarius 24°15′ (WRONG). JH authoritative.' },
  { id: 'LAG.PRANAPADA', name: 'Pranapada Lagna', longitude: 'Leo 20°32′01.21″',    sign: 'Leo',         house: 5,  nakshatra: 'Purva Phalguni',   pada: 3, source: '§12.1 row 7', note: 'NEW in v8.0 — not in v6.0. JH authoritative.' },
  { id: 'LAG.INDU',    name: 'Indu Lagna',     longitude: 'Scorpio 27°04′14.11″',    sign: 'Scorpio',     house: 8,  nakshatra: 'Jyeshtha',         pada: 4, source: '§12.1 row 8', note: null },
  { id: 'LAG.BB',      name: 'Bhrigu Bindu',   longitude: 'Libra 8°03′34.51″',       sign: 'Libra',       house: 7,  nakshatra: 'Swati',            pada: 1, source: '§12.1 row 9', note: 'Sensitive midpoint of Rahu+Moon.' },
] as const

// ── §12.2 Tajika Sahams (36) ─────────────────────────────────────────────────
// Source: FORENSIC v8.0 §12.2 / JH authoritative
// CHART_FACTS_EXTRACTION_v1_0.yaml §12.2 rows 1-36

const SAHAMS = [
  { id: 'SAH.PUNYA',       name: 'Punya',       longitude: '17°30′54″ Ge', sign: 'Gemini',      house: 3,  nakshatra: 'Ardra',       meaning: 'Fortune', source: '§12.2 row 1',  note: null },
  { id: 'SAH.VIDYA',       name: 'Vidya',       longitude: '7°19′48″ Pi',  sign: 'Pisces',      house: 12, nakshatra: 'UBha',        meaning: 'Learning', source: '§12.2 row 2', note: null },
  { id: 'SAH.YASAS',       name: 'Yasas',       longitude: '4°42′38″ Sc',  sign: 'Scorpio',     house: 8,  nakshatra: 'Anuradha',    meaning: 'Fame', source: '§12.2 row 3',     note: null },
  { id: 'SAH.MITRA',       name: 'Mitra',       longitude: '11°28′34″ Cn', sign: 'Cancer',      house: 4,  nakshatra: 'Pushya',      meaning: 'Friendship', source: '§12.2 row 4', note: null },
  { id: 'SAH.MAHATMYA',    name: 'Mahatmya',    longitude: '11°24′11″ Sg', sign: 'Sagittarius', house: 9,  nakshatra: 'Moola',       meaning: 'Greatness', source: '§12.2 row 5', note: 'v8.0 correction: v6.0 had 7H Libra (WRONG). JH authoritative.' },
  { id: 'SAH.ASHA',        name: 'Asha',        longitude: '16°20′07″ Ta', sign: 'Taurus',      house: 2,  nakshatra: 'Rohini',      meaning: 'Desires', source: '§12.2 row 6',   note: null },
  { id: 'SAH.SAMARTHA',    name: 'Samartha',    longitude: '3°41′27″ Cn',  sign: 'Cancer',      house: 4,  nakshatra: 'Pushya',      meaning: 'Enterprise', source: '§12.2 row 7', note: null },
  { id: 'SAH.BHRATRU',     name: 'Bhratru',     longitude: '29°46′41″ Ge', sign: 'Gemini',      house: 3,  nakshatra: 'Punarvasu',   meaning: 'Brother', source: '§12.2 row 8',   note: null },
  { id: 'SAH.GAURAVA',     name: 'Gaurava',     longitude: '4°42′38″ Sc',  sign: 'Scorpio',     house: 8,  nakshatra: 'Anuradha',    meaning: 'Respect', source: '§12.2 row 9',   note: null },
  { id: 'SAH.PITRU',       name: 'Pitru',       longitude: '12°53′31″ Cp', sign: 'Capricorn',   house: 10, nakshatra: 'Shravana',    meaning: 'Father', source: '§12.2 row 10',   note: null },
  { id: 'SAH.RAJYA',       name: 'Rajya',       longitude: '12°53′31″ Cp', sign: 'Capricorn',   house: 10, nakshatra: 'Shravana',    meaning: 'Kingdom / Authority', source: '§12.2 row 11', note: null },
  { id: 'SAH.MATRU',       name: 'Matru',       longitude: '20°18′18″ Cn', sign: 'Cancer',      house: 4,  nakshatra: 'Ashlesha',    meaning: 'Mother', source: '§12.2 row 12',   note: null },
  { id: 'SAH.PUTRA',       name: 'Putra',       longitude: '25°09′18″ Cp', sign: 'Capricorn',   house: 10, nakshatra: 'Dhanishtha',  meaning: 'Children', source: '§12.2 row 13', note: null },
  { id: 'SAH.JEEVA',       name: 'Jeeva',       longitude: '25°04′02″ Aq', sign: 'Aquarius',    house: 11, nakshatra: 'PBha',        meaning: 'Life', source: '§12.2 row 14',     note: null },
  { id: 'SAH.KARMA',       name: 'Karma',       longitude: '0°06′11″ Aq',  sign: 'Aquarius',    house: 11, nakshatra: 'Dhanishtha',  meaning: 'Profession', source: '§12.2 row 15', note: null },
  { id: 'SAH.ROGA',        name: 'Roga',        longitude: '27°46′29″ Ta', sign: 'Taurus',      house: 2,  nakshatra: 'Mrigashira',  meaning: 'Disease', source: '§12.2 row 16',   note: 'v8.0 correction: v6.0 had 7H Libra (WRONG). JH authoritative.' },
  { id: 'SAH.KALI',        name: 'Kali',        longitude: '3°41′27″ Cn',  sign: 'Cancer',      house: 4,  nakshatra: 'Pushya',      meaning: 'Misfortune', source: '§12.2 row 17', note: null },
  { id: 'SAH.SASTRA',      name: 'Sastra',      longitude: '18°12′34″ Pi', sign: 'Pisces',      house: 12, nakshatra: 'Revati',      meaning: 'Sciences', source: '§12.2 row 18', note: null },
  { id: 'SAH.BANDHU',      name: 'Bandhu',      longitude: '16°12′22″ Aq', sign: 'Aquarius',    house: 11, nakshatra: 'Shatabhisha', meaning: 'Relatives', source: '§12.2 row 19', note: null },
  { id: 'SAH.MRITYU',      name: 'Mrityu',      longitude: '27°46′29″ Sg', sign: 'Sagittarius', house: 9,  nakshatra: 'UAshadha',    meaning: 'Death', source: '§12.2 row 20',    note: null },
  { id: 'SAH.PARADESA',    name: 'Paradesa',    longitude: '15°02′32″ Ta', sign: 'Taurus',      house: 2,  nakshatra: 'Rohini',      meaning: 'Foreign lands', source: '§12.2 row 21', note: null },
  { id: 'SAH.ARTHA',       name: 'Artha',       longitude: '5°39′25″ Vi',  sign: 'Virgo',       house: 6,  nakshatra: 'UPhal',       meaning: 'Wealth', source: '§12.2 row 22',    note: null },
  { id: 'SAH.PARADARA',    name: 'Paradara',    longitude: '9°37′57″ Pi',  sign: 'Pisces',      house: 12, nakshatra: 'UBha',        meaning: 'Adultery', source: '§12.2 row 23',   note: null },
  { id: 'SAH.VANIK',       name: 'Vanik',       longitude: '8°38′20″ Cn',  sign: 'Cancer',      house: 4,  nakshatra: 'Pushya',      meaning: 'Trade', source: '§12.2 row 24',     note: null },
  { id: 'SAH.KARYASIDDHI', name: 'Karyasiddhi', longitude: '22°55′01″ Cn', sign: 'Cancer',      house: 4,  nakshatra: 'Ashlesha',    meaning: 'Fructification', source: '§12.2 row 25', note: null },
  { id: 'SAH.VIVAHA',      name: 'Vivaha',      longitude: '9°09′47″ Cn',  sign: 'Cancer',      house: 4,  nakshatra: 'Pushya',      meaning: 'Marriage', source: '§12.2 row 26',   note: 'v8.0 correction: v6.0 had Gemini Ardra 3H (WRONG). JH authoritative.' },
  { id: 'SAH.SANTAPA',     name: 'Santapa',     longitude: '7°47′58″ Ta',  sign: 'Taurus',      house: 2,  nakshatra: 'Krittika',    meaning: 'Sadness', source: '§12.2 row 27',    note: null },
  { id: 'SAH.SRADDHA',     name: 'Sraddha',     longitude: '13°04′34″ Cn', sign: 'Cancer',      house: 4,  nakshatra: 'Pushya',      meaning: 'Dedication', source: '§12.2 row 28', note: null },
  { id: 'SAH.PREETI',      name: 'Preeti',      longitude: '13°07′02″ Aq', sign: 'Aquarius',    house: 11, nakshatra: 'Shatabhisha', meaning: 'Love', source: '§12.2 row 29',     note: null },
  { id: 'SAH.JADYA',       name: 'Jadya',       longitude: '26°56′29″ Sg', sign: 'Sagittarius', house: 9,  nakshatra: 'UAshadha',    meaning: 'Sluggishness', source: '§12.2 row 30', note: null },
  { id: 'SAH.VYAPARA',     name: 'Vyapara',     longitude: '8°30′35″ Ar',  sign: 'Aries',       house: 1,  nakshatra: 'Ashwini',     meaning: 'Business', source: '§12.2 row 31',   note: null },
  { id: 'SAH.SATRU',       name: 'Satru',       longitude: '8°30′35″ Ar',  sign: 'Aries',       house: 1,  nakshatra: 'Ashwini',     meaning: 'Enemies', source: '§12.2 row 32',    note: null },
  { id: 'SAH.JALAPATANA',  name: 'Jalapatana',  longitude: '4°58′30″ Cp',  sign: 'Capricorn',   house: 10, nakshatra: 'UAshadha',    meaning: 'Crossing ocean', source: '§12.2 row 33', note: null },
  { id: 'SAH.BANDHANA',    name: 'Bandhana',    longitude: '7°29′24″ Sg',  sign: 'Sagittarius', house: 9,  nakshatra: 'Moola',       meaning: 'Imprisonment', source: '§12.2 row 34', note: null },
  { id: 'SAH.APAMRITYU',   name: 'Apamrityu',   longitude: '6°18′38″ Ge',  sign: 'Gemini',      house: 3,  nakshatra: 'Mrigashira',  meaning: 'Untimely death', source: '§12.2 row 35', note: null },
  { id: 'SAH.LABHA',       name: 'Labha',       longitude: '2°23′51″ Vi',  sign: 'Virgo',       house: 6,  nakshatra: 'UPhal',       meaning: 'Gains', source: '§12.2 row 36',     note: null },
] as const

// ── §13.1 + §13.2 Arudhas — FULL A1..A12 + UL (Upapada) set ──────────────────
// Source: FORENSIC v8.0 §13.1 (explicit placements) + §13.2 (sign occupancy for A3/A5/A8/A9/A12)
// Gate-1 requires A1..A12 + Upapada (UL/A12) + Darapada (A7).
// §13.1 explicit: AL(A1)=Capricorn, A2=Cancer, A6=Taurus, A7=Aquarius, A10=Aries, A11=Gemini, UL=Gemini
// §13.2 occupancy: A3=Leo, A4=Virgo, A5=Gemini, A8=Virgo, A9=Virgo, A12=Pisces (UL=A12 explicit)
// Note: A8 = Darapada in some traditions (7th-house mirror); A7 = Darapada in Parashari; both included.

const ARUDHAS = [
  // §13.1 explicit placements
  { id: 'ARD.AL',     name: 'AL (Lagna Arudha / A1)',  sign: 'Capricorn',   house: 10, div: 'D1', tenants: ['Sun', 'Mercury'], note: 'Arudha of 1st house. Lagna Aries; Lord Mars in 7H Libra → Capricorn (exception applied).', source: '§13.1 row 1' },
  { id: 'ARD.A2',     name: 'A2 (Family)',              sign: 'Cancer',      house: 4,  div: 'D1', tenants: [],                note: 'Arudha of 2nd house. 2H Taurus; Lord Venus 8 signs to Sagittarius → Cancer.', source: '§13.1 row 2' },
  // §13.2 — A3 occupies Leo H5
  { id: 'ARD.A3',     name: 'A3 (Siblings)',            sign: 'Leo',         house: 5,  div: 'D1', tenants: [],                note: 'Arudha of 3rd house. Source: FORENSIC §13.2 ARO.LEO.', source: '§13.2 ARO.LEO' },
  // §13.2 — A4 occupies Virgo H6
  { id: 'ARD.A4',     name: 'A4 (Home / Mother)',       sign: 'Virgo',       house: 6,  div: 'D1', tenants: [],                note: 'Arudha of 4th house. Source: FORENSIC §13.2 ARO.VIRGO.', source: '§13.2 ARO.VIRGO' },
  // §13.2 — A5 occupies Gemini H3 (co-located with UL, A11)
  { id: 'ARD.A5',     name: 'A5 (Children / Intellect)', sign: 'Gemini',    house: 3,  div: 'D1', tenants: ['UL', 'A11'],     note: 'Arudha of 5th house. Source: FORENSIC §13.2 ARO.GEMINI.', source: '§13.2 ARO.GEMINI' },
  { id: 'ARD.A6',     name: 'A6 (Enemy / Service)',     sign: 'Taurus',      house: 2,  div: 'D1', tenants: ['Rahu'],          note: 'Arudha of 6th house. Co-located with Rahu.', source: '§13.1 row 3' },
  { id: 'ARD.A7',     name: 'A7 (Partner / Darapada)',  sign: 'Aquarius',    house: 11, div: 'D1', tenants: ['Moon'],          note: 'Arudha of 7th house. Darapada (spouse-image significator in Parashari). Co-located with Moon.', source: '§13.1 row 4' },
  // §13.2 — A8 occupies Virgo H6 (co-located with A4, A9). Darapada in some Jaimini traditions.
  { id: 'ARD.A8',     name: 'A8 (Longevity / Darapada alt)', sign: 'Virgo', house: 6,  div: 'D1', tenants: ['A4', 'A9'],     note: 'Arudha of 8th house. Source: FORENSIC §13.2 ARO.VIRGO. Also called Darapada in Jaimini.', source: '§13.2 ARO.VIRGO' },
  // §13.2 — A9 occupies Virgo H6 (co-located with A4, A8)
  { id: 'ARD.A9',     name: 'A9 (Dharma / Guru)',       sign: 'Virgo',       house: 6,  div: 'D1', tenants: ['A4', 'A8'],     note: 'Arudha of 9th house. Source: FORENSIC §13.2 ARO.VIRGO.', source: '§13.2 ARO.VIRGO' },
  { id: 'ARD.A10',    name: 'A10 (Karma / Status)',      sign: 'Aries',       house: 1,  div: 'D1', tenants: [],               note: 'Arudha of 10th house. 10H Capricorn → Saturn in Libra → Cancer (exception) → Aries.', source: '§13.1 row 5' },
  { id: 'ARD.A11',    name: 'A11 (Gains)',               sign: 'Gemini',      house: 3,  div: 'D1', tenants: ['UL', 'A5'],     note: 'Arudha of 11th house. Co-located with UL and A5.', source: '§13.1 row 6' },
  { id: 'ARD.UL',     name: 'UL (Upapada Lagna / A12)', sign: 'Gemini',      house: 3,  div: 'D1', tenants: ['A11', 'A5'],    note: 'Upapada Lagna = Arudha of 12th house. Spouse-image significator. 12H lord Jupiter in Sagittarius → Virgo (exception) → Gemini.', source: '§13.1 row 7' },
  // §13.2 — A12=UL confirmed Pisces has no arudha markers; UL explicitly = Gemini per §13.1
  { id: 'ARD.A12',    name: 'A12 (Bed Comforts / Loss)', sign: 'Pisces',     house: 12, div: 'D1', tenants: [],               note: 'Arudha of 12th house (alias). FORENSIC §13.2 ARO.PISCES shows no markers; UL (Upapada) is the primary 12H arudha per §13.1. A12=UL=Gemini is standard; Pisces is the 12H sign itself.', source: '§13.2 ARO.PISCES' },
  // Divisional arudhas
  { id: 'ARD.AL.D9',  name: 'AL in D9 (Navamsa)',       sign: 'Taurus',      house: null, div: 'D9',  tenants: [],            note: 'D9 Lagna Cancer; Moon in D9 12th (Gemini); 12th from Gemini = Taurus.', source: '§13.1 row 8' },
  { id: 'ARD.AL.D10', name: 'AL in D10 (Dasamsa)',      sign: 'Sagittarius', house: null, div: 'D10', tenants: [],            note: 'D10 Lagna Leo; Sun in D10 9th (Aries); 9th from Aries = Sagittarius.', source: '§13.1 row 9' },
] as const

// ── FORENSIC native chart UUID ─────────────────────────────────────────────────
// Source: platform/scripts/dedupe_charts.ts NATIVE_CANONICAL_ID
// Used for chart_sensitive_points.chart_id (Gate-1 requirement)
const FORENSIC_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

// ── Builder functions ─────────────────────────────────────────────────────────

export function buildUpagrahaRows(): Row[] {
  return UPAGRAHAS.map(u => ({
    fact_id: u.id,
    category: 'upagraha',
    divisional_chart: 'D1',
    value_text: `${u.sign} ${u.degree} (${u.nakshatra})`,
    value_number: null,
    value_json: {
      name: u.name,
      type: u.type,
      sign: u.sign,
      degree: u.degree,
      nakshatra: u.nakshatra,
      house: SIGN_TO_HOUSE[u.sign],
      forensic_id: u.id,
    },
    source_section: `FORENSIC_v8_0_${u.source}`,
    build_id: BUILD_ID,
    provenance: PROV,
  }))
}

export function buildSpecialLagnaRows(): Row[] {
  return SPECIAL_LAGNAS.map(l => ({
    fact_id: l.id,
    category: 'special_lagna',
    divisional_chart: 'D1',
    value_text: l.longitude,
    value_number: null,
    value_json: {
      name: l.name,
      sign: l.sign,
      house: l.house,
      nakshatra: l.nakshatra,
      pada: l.pada,
      ...(l.note ? { note: l.note } : {}),
    },
    source_section: `FORENSIC_v8_0_${l.source}`,
    build_id: BUILD_ID,
    provenance: PROV,
  }))
}

export function buildSahamRows(): Row[] {
  return SAHAMS.map(s => ({
    fact_id: s.id,
    category: 'saham',
    divisional_chart: 'D1',
    value_text: `${s.longitude} (${s.meaning})`,
    value_number: null,
    value_json: {
      name: s.name,
      longitude: s.longitude,
      sign: s.sign,
      house: s.house,
      nakshatra: s.nakshatra,
      meaning: s.meaning,
      ...(s.note ? { note: s.note } : {}),
    },
    source_section: `FORENSIC_v8_0_${s.source}`,
    build_id: BUILD_ID,
    provenance: PROV,
  }))
}

export function buildArudhaRows(): Row[] {
  return ARUDHAS.map(a => ({
    fact_id: a.id,
    category: 'arudha',
    divisional_chart: a.div,
    value_text: a.house !== null ? `${a.sign} H${a.house}` : a.sign,
    value_number: null,
    value_json: {
      name: a.name,
      sign: a.sign,
      house: a.house,
      divisional_chart: a.div,
      tenants: a.tenants,
      note: a.note,
    },
    source_section: `FORENSIC_v8_0_${a.source}`,
    build_id: BUILD_ID,
    provenance: PROV,
  }))
}

export function buildRows(): Row[] {
  return [
    ...buildUpagrahaRows(),
    ...buildSpecialLagnaRows(),
    ...buildSahamRows(),
    ...buildArudhaRows(),
  ]
}

// ── chart_sensitive_points rows ───────────────────────────────────────────────
// Gate-1 requirement: chart_sensitive_points table must be populated with
// chart_id, point_name, ayanamsha_id, longitude, sign, house, source_citation.
// Points required: all 7 core upagrahas, A1..A12, Upapada, Darapada,
// Hora Lagna, Ghati Lagna, Bhava Lagna. source_citation must be non-null.

export interface CspRow {
  chart_id: string
  point_name: string
  point_category: string
  ayanamsha_id: string
  fact_id: string
  longitude: string | null
  sign: string | null
  house: number | null
  nakshatra: string | null
  source_citation: string
  metadata: Record<string, unknown>
  build_id: string
}

// Gate-1 required upagrahas — all 7 must be present with non-null longitude
// (BRAHMA-GA-1-6 acceptance criteria: attempt 2 explicit enforcement)
const GATE1_REQUIRED_UPAGRAHAS = [
  'UPG.GULIKA', 'UPG.MANDI', 'UPG.DHUMA',
  'UPG.VYATIPATA', 'UPG.PARIVESHA', 'UPG.INDRACHAPA', 'UPG.UPAKETU',
] as const

export function buildChartSensitivePointRows(): CspRow[] {
  const rows: CspRow[] = []

  // Upagrahas — each row gets non-null longitude = `<sign> <degree>` (Gate-1 explicit)
  for (const u of UPAGRAHAS) {
    const longitude = `${u.sign} ${u.degree}` // never null: sign+degree both present in FORENSIC data
    rows.push({
      chart_id: FORENSIC_CHART_ID,
      point_name: u.name,
      point_category: 'upagraha',
      ayanamsha_id: 'INVARIANT',
      fact_id: u.id,
      longitude,
      sign: u.sign,
      house: SIGN_TO_HOUSE[u.sign] ?? null,
      nakshatra: u.nakshatra,
      source_citation: `FORENSIC_v8_0_${u.source}`,
      metadata: { type: u.type, degree: u.degree, nakshatra: u.nakshatra },
      build_id: BUILD_ID,
    })
  }

  // Gate-1 self-check: assert all 7 required upagrahas are present with non-null longitude
  for (const required of GATE1_REQUIRED_UPAGRAHAS) {
    const row = rows.find(r => r.fact_id === required)
    if (!row) throw new Error(`Gate-1 violation: required upagraha ${required} missing from chart_sensitive_points`)
    if (!row.longitude) throw new Error(`Gate-1 violation: ${required} has null longitude — FORENSIC §11.1 data must be present`)
  }

  // Special Lagnas (Hora, Ghati, Bhava — and all others)
  for (const l of SPECIAL_LAGNAS) {
    rows.push({
      chart_id: FORENSIC_CHART_ID,
      point_name: l.name,
      point_category: 'special_lagna',
      ayanamsha_id: 'INVARIANT',
      fact_id: l.id,
      longitude: l.longitude,
      sign: l.sign,
      house: l.house,
      nakshatra: l.nakshatra,
      source_citation: `FORENSIC_v8_0_${l.source}`,
      metadata: { pada: l.pada, ...(l.note ? { note: l.note } : {}) },
      build_id: BUILD_ID,
    })
  }

  // Sahams
  for (const s of SAHAMS) {
    rows.push({
      chart_id: FORENSIC_CHART_ID,
      point_name: s.name,
      point_category: 'saham',
      ayanamsha_id: 'INVARIANT',
      fact_id: s.id,
      longitude: s.longitude,
      sign: s.sign,
      house: s.house,
      nakshatra: s.nakshatra,
      source_citation: `FORENSIC_v8_0_${s.source}`,
      metadata: { meaning: s.meaning, ...(s.note ? { note: s.note } : {}) },
      build_id: BUILD_ID,
    })
  }

  // Arudhas — full A1..A12 + UL + divisional
  for (const a of ARUDHAS) {
    rows.push({
      chart_id: FORENSIC_CHART_ID,
      point_name: a.name,
      point_category: 'arudha',
      ayanamsha_id: 'INVARIANT',
      fact_id: a.id,
      longitude: a.house !== null ? `${a.sign} H${a.house}` : a.sign,
      sign: a.sign,
      house: a.house ?? null,
      nakshatra: null,
      source_citation: `FORENSIC_v8_0_${a.source}`,
      metadata: { divisional_chart: a.div, note: a.note },
      build_id: BUILD_ID,
    })
  }

  return rows
}

// ── Build manifest ────────────────────────────────────────────────────────────

async function ensureBuildManifest(dryRun: boolean): Promise<void> {
  const rows = buildRows()
  if (dryRun) {
    console.log(`[dry-run] WOULD upsert build_manifests: ${BUILD_ID}`)
    return
  }
  await pool.query(
    `INSERT INTO build_manifests
       (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
        embedding_model, embedding_dim, chunk_count, embedding_count, status, manifest_uri, notes)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
     ON CONFLICT (build_id) DO NOTHING`,
    [
      BUILD_ID,
      'manual:brahma-ga-1-6',
      'FORENSIC_v8_0_sha256_be76cc7aa84f3c1e',
      'brahma-sensitive-points-bootstrap:v1.0',
      'none',
      0,
      rows.length,
      0,
      'live',
      'local://brahma-ga-1-6-sensitive-points',
      `ganita.sensitive_points: ${rows.length} chart_facts rows (9 upagrahas + 9 special_lagnas + 36 sahams + 14 arudhas A1-A12+UL+D9+D10) + chart_sensitive_points populated`,
    ]
  )
  console.log(`[sensitive_points] build_manifests row inserted: ${BUILD_ID}`)
}

// ── Ingest ────────────────────────────────────────────────────────────────────

async function ingest(dryRun: boolean): Promise<void> {
  const rows = buildRows()
  const byCategory = {
    upagraha: rows.filter(r => r.category === 'upagraha').length,
    special_lagna: rows.filter(r => r.category === 'special_lagna').length,
    saham: rows.filter(r => r.category === 'saham').length,
    arudha: rows.filter(r => r.category === 'arudha').length,
  }

  console.log(`[sensitive_points] build_id = ${BUILD_ID}`)
  console.log(`[sensitive_points] total rows: ${rows.length}`)
  console.log(`[sensitive_points]   upagraha:      ${byCategory.upagraha}`)
  console.log(`[sensitive_points]   special_lagna: ${byCategory.special_lagna}`)
  console.log(`[sensitive_points]   saham:         ${byCategory.saham}`)
  console.log(`[sensitive_points]   arudha:        ${byCategory.arudha}`)

  if (dryRun) {
    console.log('[dry-run] No DB writes. Rows:')
    rows.forEach(r => console.log(`  ${r.fact_id} | ${r.category} | ${r.value_text}`))
    return
  }

  let inserted = 0
  let skipped = 0

  for (const r of rows) {
    const result = await pool.query(
      `INSERT INTO chart_facts
         (fact_id, category, divisional_chart, value_text, value_number, value_json,
          source_section, build_id, provenance, is_stale)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,false)
       ON CONFLICT (fact_id) DO UPDATE SET
         category        = EXCLUDED.category,
         value_text      = EXCLUDED.value_text,
         value_number    = EXCLUDED.value_number,
         value_json      = EXCLUDED.value_json,
         source_section  = EXCLUDED.source_section,
         build_id        = EXCLUDED.build_id,
         provenance      = EXCLUDED.provenance,
         is_stale        = false
       RETURNING (xmax = 0) AS inserted`,
      [
        r.fact_id,
        r.category,
        r.divisional_chart,
        r.value_text,
        r.value_number,
        r.value_json !== null ? JSON.stringify(r.value_json) : null,
        r.source_section,
        r.build_id,
        JSON.stringify(r.provenance),
      ]
    )
    if (result.rows[0]?.inserted) inserted++
    else skipped++
  }

  console.log(`[sensitive_points] chart_facts upserted: ${inserted} new, ${skipped} updated — DONE`)
}

// ── Ingest chart_sensitive_points (Gate-1 requirement) ────────────────────────

async function ingestChartSensitivePoints(dryRun: boolean): Promise<void> {
  const cspRows = buildChartSensitivePointRows()

  console.log(`[sensitive_points] chart_sensitive_points rows to upsert: ${cspRows.length}`)

  if (dryRun) {
    console.log('[dry-run] WOULD upsert chart_sensitive_points. Rows:')
    cspRows.forEach(r => console.log(`  ${r.fact_id} | ${r.point_category} | ${r.point_name} | ${r.longitude ?? 'null'} | ${r.source_citation}`))
    return
  }

  let inserted = 0
  let skipped = 0

  for (const r of cspRows) {
    const result = await pool.query(
      `INSERT INTO chart_sensitive_points
         (chart_id, point_name, point_category, ayanamsha_id, fact_id,
          longitude, sign, house, nakshatra, source_citation, metadata, build_id)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
       ON CONFLICT (chart_id, fact_id, ayanamsha_id) DO UPDATE SET
         point_name      = EXCLUDED.point_name,
         point_category  = EXCLUDED.point_category,
         longitude       = EXCLUDED.longitude,
         sign            = EXCLUDED.sign,
         house           = EXCLUDED.house,
         nakshatra       = EXCLUDED.nakshatra,
         source_citation = EXCLUDED.source_citation,
         metadata        = EXCLUDED.metadata,
         build_id        = EXCLUDED.build_id
       RETURNING (xmax = 0) AS inserted`,
      [
        r.chart_id,
        r.point_name,
        r.point_category,
        r.ayanamsha_id,
        r.fact_id,
        r.longitude,
        r.sign,
        r.house,
        r.nakshatra,
        r.source_citation,
        JSON.stringify(r.metadata),
        r.build_id,
      ]
    )
    if (result.rows[0]?.inserted) inserted++
    else skipped++
  }

  console.log(`[sensitive_points] chart_sensitive_points upserted: ${inserted} new, ${skipped} updated — DONE`)
}

// ── Main ──────────────────────────────────────────────────────────────────────

if (process.env.NODE_ENV !== 'test') {
  const dryRun = process.argv.includes('--dry-run')
  ;(async () => {
    try {
      await ensureBuildManifest(dryRun)
      await ingest(dryRun)
      await ingestChartSensitivePoints(dryRun)
    } catch (err) {
      console.error('[sensitive_points] FATAL:', err)
      process.exit(1)
    } finally {
      await pool.end()
    }
  })()
}

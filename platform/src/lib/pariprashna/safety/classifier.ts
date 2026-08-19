/**
 * Paripraśna safety — THE DETERMINISTIC QUERY CLASSIFIER (lane G1-A, PPR-12).
 *
 * SAFETY_PRIVACY_TENANCY §3: "Deterministic-first (§N.4): keyword/domain
 * classifier + capability-class rules; an LLM assist may RAISE severity, never
 * lower it." This module is the deterministic half, and it is PURE — no DB, no
 * network, no clock, no flag read. That is what lets the adversarial suite throw
 * a few hundred paraphrases at it in milliseconds.
 *
 * ── THREE DETECTOR FAMILIES ──────────────────────────────────────────────────
 *  1. PHRASE patterns — an explicit ask, matched against the normalized text
 *     (word-bounded) or the squashed text (spelling-evasion proof).
 *  2. COMBINATION rules — a lexicon term plus a second lexicon term. This is
 *     what catches the paraphrase nobody wrote a phrase for: "which year does
 *     my Ayurdaya conclude" is `mortality_term` × `temporal_specificity`, and
 *     neither half alone is an HS-1 ask.
 *  3. CAPABILITY/DOMAIN rules — a planner domain (`health`, `longevity`) or an
 *     authorized capability (`get_ayurdaya`) implies its class regardless of how
 *     the question was worded. This is the family that survives a question with
 *     no English mortality words in it at all.
 *
 * ── THE ONE ARCHITECTURAL RULE ───────────────────────────────────────────────
 * There is NO code path in this file that removes, downgrades, or excuses a
 * detection. No negation handling, no "hypothetical" exemption, no
 * "third-person so it's fine" branch. Displacement framing ("asking for a
 * friend", "for a character in my novel", "purely hypothetically") is a
 * documented evasion pattern, so it is recorded as an evasion marker and RAISES
 * severity — it never lowers it. If you find yourself wanting to add an
 * exemption to reduce false positives, the correct move is to make the PATTERN
 * narrower, not to add a branch that can be triggered by the attacker's own text.
 */

import {
  MIN_SQUASHED_PATTERN_LENGTH,
  normalizeForClassification,
  spanHash,
  type NormalizedQueryText,
} from './normalize'
import {
  SAFETY_CLASSES,
  maxSeverity,
  type SafetyClass,
  type SafetyDetection,
  type SafetyEvasionMarker,
  type SafetySeverity,
} from './types'

// ═══════════════════════════════════════════════════════════════════════════
// 1. PHRASE PATTERNS
// ═══════════════════════════════════════════════════════════════════════════

interface PhrasePattern {
  id: string
  cls: SafetyClass
  severity: SafetySeverity
  /** Word-bounded match against `normalized`. */
  re?: RegExp
  /** Substring match against `squashed`. Each entry MUST be >= 8 chars. */
  squashed?: string[]
}

/**
 * The named-undertaking guard (hardening round, C-1).
 *
 * Used ONLY by `hs2.plan_and_means_disclosure`, the one HS-2 pattern whose
 * words carry no self-harm vocabulary of their own. "I have a plan and a date
 * picked" is a suicide-risk disclosure when the object is unnamed and an
 * ordinary muhūrta question when it is named — and naming a wedding, a shop
 * opening or a gṛha-praveśa is overwhelmingly what this product's users are
 * doing when they type that sentence.
 *
 * Same construction and same justification as `MUNDANE_REMAINDER_GUARD` below:
 * a narrowing of the pattern to its actual meaning, not an exemption branch. An
 * attacker who appends "for my business launch" is left with a sentence that
 * contains no self-harm content for any control to act on.
 */
const BENIGN_UNDERTAKING_GUARD =
  `(?![^.?!]{0,40}\\b(business|wedding|marriage|shaadi|engagement|launch|company|startup|` +
  `shop|store|office|griha ?pravesh\\w*|house ?warming|housewarming|move|moving|relocat\\w+|` +
  `trip|travel|journey|yatra|flight|surgery|operation|procedure|exam|interview|admission|` +
  `registration|puja|pooja|havan|yagna|ceremony|event|project|investment|purchase|` +
  `property|car|vehicle|loan|course|treatment|conception|pregnancy|baby|naming|namkaran)\\b)`

/**
 * HS-2 — suicide-adjacent (MP §3.5.C, "disallowed under all audience tiers").
 *
 * Calibration note, stated because it is a real design choice and not an
 * accident: HS-2 is deliberately OVER-inclusive. Its consequence is a fixed,
 * calm, non-analytic response with support-resource framing. The cost of a
 * false positive is one reader receiving a supportive message instead of an
 * astrological reading; the cost of a false negative is the failure mode this
 * whole lane exists to prevent. Those are not symmetric, and the thresholds
 * here are set accordingly.
 */
const HS2_PATTERNS: PhrasePattern[] = [
  {
    id: 'hs2.suicide_stem',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    re: /\bsuicid\w*\b/,
    squashed: ['suicide', 'suicidal', 'commitsuicide'],
  },
  {
    id: 'hs2.self_killing',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    re: /\b(kill|killing|hurt|harm|harming|injure|injuring|cut)\s+(my\s?self|myself|him\s?self|her\s?self|them\s?selves|one\s?self)\b/,
    squashed: [
      'killmyself',
      'killingmyself',
      'harmmyself',
      'hurtmyself',
      'selfharm',
      'selfharming',
      'selfinjury',
      'selfdestruction',
    ],
  },
  {
    id: 'hs2.end_my_life',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    re: /\b(end|ending|take|taking|finish|finishing)\s+(my|his|her|their|one's)\s+(own\s+)?(life|lives)\b/,
    squashed: ['endmylife', 'endmyownlife', 'takemyownlife', 'endinglife', 'endingitall'],
  },
  {
    id: 'hs2.not_want_to_live',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    re: /\b(don'?t|do not|dont|no longer|cannot|can'?t|cant|never)\s+(want|wish|care)\s+to\s+(live|be alive|go on|carry on|exist|be here)\b/,
    squashed: [
      'dontwanttolive',
      'donotwanttolive',
      'nolongerwanttolive',
      'dontwanttobealive',
      'dontwanttoexist',
      'dontwanttobehere',
    ],
  },
  {
    id: 'hs2.want_to_die',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    re: /\b(want|wish|wanted|wishing|wanting|hoping|hope|ready|prefer)\s+(to\s+)?(be\s+)?(die|dead|death|not be here|not exist|disappear forever)\b/,
    squashed: ['wanttodie', 'wishiwasdead', 'wanttobedead', 'readytodie', 'wishtodie'],
  },
  {
    id: 'hs2.no_reason_to_live',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    re: /\b(no|without any|lost my|there'?s no)\s+(reason|point|purpose|will|desire)\s+(to|in|for)\s+(live|living|go on|going on|be here|continue|continuing)\b/,
    squashed: ['noreasontolive', 'nopointinliving', 'nopointtoliving', 'nothinglefttolivefor'],
  },
  {
    id: 'hs2.better_off_dead',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    re: /\b(better off|best)\s+(if i (was|were)\s+)?(dead|gone|not here|without me)\b/,
    squashed: ['betteroffdead', 'betteroffwithoutme', 'everyonewouldbebetteroff'],
  },
  {
    id: 'hs2.euphemism',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    re: /\b(unalive|kms|off myself|do myself in|check out early|permanent solution|final exit|exit bag|end it all|end things)\b/,
    squashed: [
      'unalive',
      'unaliving',
      'offmyself',
      'domyselfin',
      'permanentsolution',
      'finalexit',
      'enditall',
      'endthings',
      'checkoutearly',
    ],
  },
  {
    id: 'hs2.cessation_euphemism',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    // Found by the round-2 adversarial probe: none of these contain a word from
    // any earlier HS-2 pattern, and all of them are how people actually say it.
    re: /\b(sleep forever|never wake up|not wake up|stop existing|cease to exist|stop being here|make (it|the pain|everything) stop (forever|permanently)|end the pain (forever|permanently)|make the hurting stop|just give up on everything|disappear forever)\b/,
    squashed: [
      'sleepforever',
      'neverwakeup',
      'notwakeup',
      'ceasetoexist',
      'stopexisting',
      'makethepainstop',
      'endthepainforever',
    ],
  },
  {
    id: 'hs2.hinglish_devanagari',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    // The native is in India and the cohort is undefined; Hinglish and
    // Devanagari are realistic inputs, not exotic ones. Devanagari cannot be
    // matched with `\b` (JS word boundaries are ASCII-based) and vanishes from
    // the squashed form entirely, so these run WITHOUT word boundaries against
    // the normalized text.
    re: /(khud ?ku?shi|khudkhushi|atmahatya|atmaghat|apni jaan (dena|de|le)|jaan dena|jaan de ?d|आत्महत्या|ख़ुदकुशी|खुदकुशी|अपनी जान)/,
    squashed: ['khudkushi', 'khudkhushi', 'atmahatya', 'jaandena'],
  },

  {
    id: 'hs2.hindi_verb_forms',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    // HARDENING ROUND, H-1 — the Hindi/Hinglish VERB forms.
    //
    // The sibling above covers the NOUNS (ख़ुदकुशी, आत्महत्या — "suicide" as a
    // thing). It says nothing about the two commonest ways a person actually
    // discloses this in Hindi, which are verbs:
    //   · मैं मरना चाहता हूँ  / "main marna chahta hoon"  — I want to die
    //   · मैं जीना नहीं चाहता / "main jeena nahi chahta"  — I don't want to live
    // Both went through the first build as `proceed`. Noun-only coverage of a
    // language is coverage of the clinical register, not of how anyone speaks.
    re: new RegExp(
      `\\bmar(na|ne|ni)\\s+chah\\w+` +
        `|\\b(ji|jee)(na|ne)\\s+(nahi+n?|nai)\\s+chah\\w+` +
        `|\\b(nahi+n?|nai)\\s+(ji|jee)(na|ne)\\b` +
        `|\\bab\\s+(ji|jee)(na|ne)\\s+(nahi+n?|nai)\\b` +
        `|\\bzinda\\s+(nahi+n?|nai)\\s+rehna\\b|\\bnahi+n?\\s+rehna\\s+chah\\w+` +
        `|(मरना चाह|मरने की इच्छा|जीना नहीं चाह|नहीं जीना|अब नहीं जीना|ज़िंदा नहीं रहना|जिंदा नहीं रहना)`,
    ),
    squashed: ['marnachahta', 'marnachahti', 'marnechahta', 'jeenanahichahta', 'jinanahichahta'],
  },

  {
    id: 'hs2.odia_self_death',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    // HARDENING ROUND, H-1 — ODIA, HS-2 side. Same reasoning as the HS-1 Odia
    // pattern above (the native's own state language, previously zero
    // coverage), and the same honest scope note: the death/live verb stems and
    // the ātmahatyā noun, not the whole language.
    //
    //   · ମୁଁ ମରିବାକୁ ଚାହେଁ            / "mun maribaku chahen"      — I want to die
    //   · ମୋତେ ବଞ୍ଚିବାକୁ ଇଚ୍ଛା ନାହିଁ   / "mote banchibaku ichha nahin" — I don't want to live
    //   · ଆତ୍ମହତ୍ୟା                    / "atmahatya"                 — suicide
    re: new RegExp(
      `\\bmari(baku|bara|ba)\\s+(chah\\w+|ichh?a)\\b` +
        `|\\bbanchi(baku|bara|ba)\\s+(ichh?a|iccha|man)?\\s*nah\\w*\\b` +
        `|\\bbanchi(baku|bara|ba)\\s+chahun?\\s*nah\\w*\\b` +
        `|\\batma\\s?hatya\\b|\\batma\\s?ghata\\b` +
        `|(ମରିବାକୁ ଚାହେଁ|ମରିବାକୁ ଇଚ୍ଛା|ଆତ୍ମହତ୍ୟା|ଆତ୍ମଘାତ|ବଞ୍ଚିବାକୁ ଇଚ୍ଛା ନାହିଁ|ବଞ୍ଚିବାକୁ ଚାହୁଁନାହିଁ)`,
    ),
    squashed: ['maribakuchahen', 'maribakuichha', 'banchibakuichhanahin', 'banchibakuichhanahi'],
  },
  {
    id: 'hs2.self_harm_adjacent_astrology',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    // MP §3.5.C names the astrological form explicitly: "ideation signals,
    // self-harm-adjacent house/lord combinations". A user asking the instrument
    // to find the ideation combination in a chart is asking for HS-2 output
    // even with no first-person distress language anywhere in the question.
    re: /\b(ideation|self[-\s]?harm|self[-\s]?destructive|atmaghata|atmahatya)\b/,
    squashed: ['suicidalideation', 'selfharmyoga', 'atmaghata', 'atmahatya', 'selfdestructiveyoga'],
  },

  // ═════════════════════════════════════════════════════════════════════════
  // HARDENING ROUND, C-1 — METHOD, PRACTICE, ELECTION, AND PLAN DISCLOSURE.
  //
  // The first build's HS-2 set was built around how people describe the WISH
  // ("I want to die", "no reason to live"). Three adversaries independently
  // found that it says nothing at all about the MEANS, the PRACTICE, or the
  // ELECTION — and that the last of those is the shape this particular
  // instrument invites. "What is the most auspicious muhūrta to leave this
  // body voluntarily?" is a question only an astrology product ever receives,
  // and it went through as `proceed`, classes `[]`.
  //
  // These four patterns are written as STRUCTURE (method-verb × self-directed;
  // election-term × self-death target), not as a fixed phrase list, so a
  // paraphrase nobody anticipated still lands.
  // ═════════════════════════════════════════════════════════════════════════

  {
    id: 'hs2.method_self_directed',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    // METHOD-VERB × SELF-DIRECTED. Four sub-shapes, because the means take
    // four different grammatical forms and one alternation for all of them
    // would be unreadable:
    //  (a) transitive method verb + a reflexive pronoun;
    //  (b) positional verb + a lethal-position object (the "in front of a
    //      train" family, which has no reflexive pronoun in it at all);
    //  (c) an incision verb + a self-owned body part;
    //  (d) a consumption verb + a TOTALIZING quantifier + a medication noun.
    //      The quantifier is load-bearing: "should I take my pills during this
    //      dasha?" is an ordinary question, "swallow ALL my pills" is not.
    re: new RegExp(
      `\\b(hang|hanging|shoot|shooting|drown|drowning|suffocate|suffocating|asphyxiate|` +
        `asphyxiating|poison|poisoning|starve|starving|electrocute|electrocuting|immolate|` +
        `immolating|overdose|overdosing)\\s+(my\\s?self|myself|him\\s?self|her\\s?self|` +
        `them\\s?selves|one\\s?self)\\b` +
        `|\\b(overdose|od)\\s+(on|with)\\b` +
        `|\\b(jump|jumping|leap|leaping|step|stepping|throw|throwing|lie|lying|lay|laying)\\s+` +
        `(off|in ?front of|onto|under|before|from|out of)\\b[^.?!]{0,30}\\b(train|bridge|` +
        `building|traffic|truck|lorry|bus|roof|terrace|balcony|cliff|ledge|window|track|rail|` +
        `railway|metro|platform)\\b` +
        `|\\b(slit|slitting|slash|slashing|cut|cutting)\\s+(my|his|her|their)\\s+` +
        `(wrists?|throat|veins?|arteries)\\b` +
        `|\\b(swallow|swallowing|take|taking|consume|consuming|down|downing)\\s+` +
        `(all|the whole|a whole|every|an entire|the entire|a full)\\s+` +
        `(of\\s+)?(my\\s+|the\\s+)?(pills?|bottle|tablets?|medication|meds|packet|strip|` +
        `sleeping pills?|sedatives?|painkillers?)\\b`,
    ),
    squashed: [
      'hangmyself',
      'shootmyself',
      'drownmyself',
      'poisonmyself',
      'suffocatemyself',
      'asphyxiatemyself',
      'overdosemyself',
      'slitmywrists',
      'cutmywrists',
      'slitmythroat',
      'jumpinfrontofatrain',
      'stepinfrontofatrain',
      'jumpoffabridge',
      'jumpoffabuilding',
      'swallowallmypills',
      'takeallmypills',
      'takethewholebottle',
    ],
  },

  {
    id: 'hs2.indic_self_death_practice',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    // These are REAL Indic self-death practices and they are live vocabulary
    // for this instrument's actual user base — not contrived evasion strings.
    // A Jyotiṣa product that catches "kill myself" and not `jal samādhi` has
    // localized its safety gate to the wrong culture.
    //
    // NOTE the compounds. Bare `samadhi` is deliberately ABSENT: samādhi is an
    // ordinary yogic/spiritual term and "Samādhi yoga" is a real chart
    // combination, so matching it alone would refuse a large class of
    // legitimate questions. Only the compounds that name the ACT are here.
    re: new RegExp(
      `\\b(jal\\s?samadhi|jala\\s?samadhi|agni\\s?samadhi|samadhi\\s?maran\\w*|` +
        `prayopave[sz]\\w*|praya\\s?upave[sz]\\w*|santhara|santhaara|sallekhana|salekhana|` +
        `icch?h?a\\s?-?\\s?mrityu|icch?h?a\\s?-?\\s?mrtyu|iccha\\s?-?\\s?maran\\w*|` +
        `atma\\s?visarjan\\w*|atma\\s?arpan\\w*|deha\\s?-?\\s?tyaga|dehatyaga|` +
        `self\\s?-?immolat\\w*|voluntary death|willing death|self\\s?-?willed death)\\b` +
        `|(जल ?समाधि|अग्नि ?समाधि|प्रायोपवेश|संथारा|सल्लेखना|इच्छा ?मृत्यु|देहत्याग|आत्मविसर्जन)`,
    ),
    squashed: [
      'jalsamadhi',
      'jalasamadhi',
      'agnisamadhi',
      'samadhimaran',
      'prayopavesa',
      'prayopavesha',
      'sallekhana',
      'icchamrityu',
      'ichhamrityu',
      'dehatyaga',
      'selfimmolation',
      'voluntarydeath',
      'santhara',
    ],
  },

  {
    id: 'hs2.election_for_self_death',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    // ELECTION-TERM × SELF-DEATH TARGET — the shape this product is uniquely
    // exposed to. "Which day is best for…", "the most auspicious muhūrta
    // to…", "pick me a date to…" are the instrument's own idiom, and asking it
    // to ELECT a self-death is asking it to participate.
    //
    // The target half is pinned to a SELF-directed death, never a bare
    // `death`/`die`. "Which tithi is auspicious for my father's death
    // anniversary?" is an ordinary and frequent śrāddha question, and a bare
    // `death` would refuse it. The `(?!\s+anniversar…)` lookahead is a second
    // narrowing on the same point — belt and braces on the one false positive
    // that would hurt most.
    re: new RegExp(
      `\\b(muhurt\\w*|muhurat\\w*|tithi|auspicious|shubh\\w*|good day|best day|best time|` +
        `good time|right time|which day|what day|which date|what date|which time|what time|` +
        `pick (me )?(a|the) (date|day|time|moment)|choose (a|the) (date|day|time|moment)|` +
        `elect(ion|ional)?|favou?rable (day|time|moment|date))\\b` +
        `[^.?!]{0,60}` +
        `\\b((my|my own) (death|passing|demise|exit|end)(?!\\s+(anniversar\\w+|rite|rites|` +
        `ritual|ceremony|puja|shraddh\\w*|tithi))|` +
        `(me|myself|i) (to )?(die|pass away|depart|go)\\b|` +
        `leave (this|my|the) (body|world) (voluntar\\w+|willing\\w*|by choice)|` +
        `leav\\w+ (this|my|the) body|give up (my |the )?(body|life|prana|breath)|` +
        `renounce (my )?(body|life)|end (my|this) life|end it all|end things|` +
        `stop eating (until|till)|fast\\w* (un)?til+ (death|i die))`,
    ),
    // No squashed entries: the two halves are separated by up to 60 characters
    // of arbitrary text, which the squashed surface (a single contiguous
    // substring test with no word boundaries) cannot express. The evasion
    // coverage for this shape comes from the OTHER patterns an evader's
    // sentence still contains.
    squashed: [],
  },

  {
    id: 'hs2.plan_and_means_disclosure',
    cls: 'hs2_suicide_adjacent',
    severity: 'hard_stop',
    // "I have a plan and a date picked." / "I have been planning how I would
    // do it." These are the standard clinical risk-assessment signals (plan +
    // means + timeline, with an ANAPHORIC "it" that has no antecedent), and
    // both went through the first build as `proceed`.
    //
    // ── THE HONEST PART ──────────────────────────────────────────────────
    // These two are the OVER-INCLUSIVE TAIL of an already-deliberately-
    // over-inclusive class, and unlike every other pattern in this file they
    // carry no self-harm vocabulary at all — the words alone are compatible
    // with a wedding, a business launch, or a relocation. That is why they
    // carry `BENIGN_UNDERTAKING_GUARD`: a NAMED undertaking in the same
    // sentence resolves the anaphor, and a resolved anaphor is not this
    // signal. That guard is a narrowing of the pattern to its meaning, the
    // same move `MUNDANE_REMAINDER_GUARD` makes above — and note what an
    // evader gains by triggering it: a sentence with no self-harm content
    // left in it for any control to act on, which is not a bypass of anything.
    re: new RegExp(
      `\\b(i have|i've|ive|there is|theres)\\s+(a |the )?(plan|method|means|way)\\b` +
        `[^.?!]{0,40}\\b(and|with)\\b[^.?!]{0,25}\\b(a |the )?(date|day|time)\\b` +
        `[^.?!]{0,15}\\b(picked|chosen|set|decided|fixed|in mind|sorted)\\b` +
        BENIGN_UNDERTAKING_GUARD +
        `|\\b(been )?(planning|thinking about|thought about|figur\\w+ out|work\\w+ out|` +
        `research\\w+|decid\\w+)\\s+(exactly )?how (i|he|she|they) (would|will|could|might|can)\\s+` +
        `do it\\b` +
        BENIGN_UNDERTAKING_GUARD,
    ),
    squashed: [],
  },
]

/**
 * The mundane-remainder guard.
 *
 * "How many years are left…" and "years remaining…" are mortality phrasings
 * ONLY when the thing running out is a life. A lease, a dasha, a warranty and a
 * degree all "have years left" too, and three of those were real false
 * positives this suite caught. This lookahead names the mundane objects
 * explicitly and is shared by the two patterns that need it, so the list cannot
 * drift between them.
 *
 * Note what it is: a narrowing of the pattern to its actual meaning. It is not
 * an exemption an attacker can invoke — appending "in my dasha" to a
 * date-of-death question does not buy an answer, because every other HS-1
 * pattern in the question still fires.
 */
const MUNDANE_REMAINDER_GUARD =
  `(?!\\s+(on|in|of|for|under|with)\\s+(my|this|the|his|her|their)?\\s*(\\w+\\s+){0,2}` +
  `(lease|contract|mortgage|loan|emi|visa|warranty|subscription|membership|term|project|course|` +
  `degree|tenure|sentence|dasha|dasa|antardasha|antar|bhukti|period|transit|gochara|mahadasha|` +
  `sub ?period|battery|tank|budget|policy|plan))`

/** HS-1 — an explicit, individualized date-of-death ask. */
const HS1_PATTERNS: PhrasePattern[] = [
  {
    id: 'hs1.date_of_death_literal',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    re: /\b(date|day|time|moment|year|month|hour)\s+(of|for)\s+(my|his|her|their|the subject'?s?|this person'?s?)?\s*(death|demise|passing|dying|end|departure|exit)\b/,
    squashed: [
      'dateofdeath',
      'dayofdeath',
      'timeofdeath',
      'yearofdeath',
      'monthofdeath',
      'dateofmydeath',
      'dateofdemise',
      'dateofpassing',
    ],
  },
  {
    id: 'hs1.when_will_i_die',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    re: /\b(when|what date|which date|what year|which year|what age|which age|what day|which month|how soon)\b[^.?!]{0,60}\b(die|dies|death|demise|pass away|passes away|passing away|pass on|expire|expires|perish|no longer be here|leave this world|leave the body|depart)\b/,
    squashed: [
      'whenwilidie',
      'whenwillidie',
      'whenamigoingtodie',
      'whendoidie',
      'whenwillipassaway',
      'whatyearwillidie',
      'whatagewillidie',
      'whenwillideath',
      'howsoonwillidie',
    ],
  },
  {
    id: 'hs1.how_long_left',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    re: new RegExp(
      `\\b(how (long|much longer|much more time|much time|many years|many more years|many months|many days))\\b` +
        `[^.?!]{0,50}\\b(left${MUNDANE_REMAINDER_GUARD}|remain(ing)?${MUNDANE_REMAINDER_GUARD}|to live|do i have|have i got|` +
        `going to be around|until (i|he|she|they) (die|go|leave))\\b`,
    ),
    squashed: [
      'howlongdoihaveleft',
      'howlonghaveigot',
      'howmanyyearsdoihaveleft',
      'howmuchtimedoihaveleft',
      'howlongdoihavetolive',
      'howmanyyearsleft',
    ],
  },
  {
    id: 'hs1.live_until',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    re: /\b(live|survive|last)\s+(un)?til\w*\s+(what|which|when|age|the age)\b|\b(up to|till|until)\s+what\s+age\b|\bwhat age will (i|he|she|they) (live to|reach|make it to)\b/,
    squashed: ['liveuntilwhatage', 'livetillwhatage', 'uptowhatage', 'tillwhatagewillilive'],
  },
  {
    id: 'hs1.terminal_dasha_ask',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    // Chart-native phrasings of the same ask. `maraka` is the classical
    // death-inflicting lord; asking which dasha "ends the life" is a
    // date-of-death request wearing Sanskrit.
    re: /\b(marak\w*|maran\w*|mrityu|mrtyu|mrutyu|apamrityu|mrityu ?bhaga|badhaka)\b[^.?!]{0,60}\b(when|dasha|dasa|period|antar\w*|bhukti|year|date|age|time|timing)\b|\b(which|what)\b[^.?!]{0,40}\b(dasha|dasa|antar\w*|bhukti|transit|gochara)\b[^.?!]{0,40}\b(kill|end my life|end his life|end her life|bring death|cause death|be fatal|prove fatal|finish me)\b/,
    squashed: ['marakadasha', 'mrityudasha', 'mrityubhaga', 'deathinflictingperiod', 'fataldasha'],
  },
  {
    id: 'hs1.euphemism',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    // Round-2 adversarial finding: every one of these asks for a date of death
    // while containing NO word from any earlier HS-1 pattern. English has a
    // very large euphemism vocabulary for exactly this, and a classifier that
    // only knows "die" and "death" is a classifier that only stops the polite.
    re: /\b(six feet under|kick(ing)? the bucket|meet (my|his|her|their) maker|pushing up daisies|shuffle off|bite the dust|breathe (my|his|her|their) last|final curtain|cross(ing)? over|go to (my|his|her|their) grave|in the ground|expiry date|expiration date|(my|his|her|their) (time|number) is up|last year (i'?ll|i will) be breathing|stop breathing|no longer be breathing)\b/,
    squashed: [
      'sixfeetunder',
      'kickthebucket',
      'meetmymaker',
      'pushingupdaisies',
      'bitethedust',
      'breathemylast',
      'finalcurtain',
      'gotomygrave',
      'expirydate',
      'expirationdate',
      'mytimeisup',
      'mynumberisup',
      'stopbreathing',
    ],
  },
  {
    id: 'hs1.hinglish_devanagari',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    // Romanized Hindi and Devanagari, same reasoning as the HS-2 sibling.
    // `marunga`/`marungi`/`marega` are the first-person and third-person future
    // of मरना (to die) — the `maran\w*` stem does not reach them, which the
    // round-2 probe caught.
    //
    // ── HARDENING ROUND, H-2: THE `mar\w*` WILDCARD WAS A DEMOGRAPHIC BUG ──
    // This pattern used to read `kab\s+mar\w*|mar\w*\s+kab`, i.e. "kab" next to
    // ANY word starting with `mar`. In the language this gate exists to serve,
    // that is not a rare collision — it is three of the most common questions
    // the product receives, all of which were being SEALED with no reading:
    //   · "Meri marriage kab hogi?"      — marriage timing (`marriage kab`)
    //   · "Shani kab margi hoga?"        — Saturn retrograde→direct (`kab margi`)
    //   · "Margashirsha kab shuru hoga?" — a lunar month (`margashirsha kab`)
    // A safety control that refuses to answer "when will I marry" for Hinglish
    // speakers, and only for Hinglish speakers, is not a safety control; it is
    // a defect that happens to fail in the strict direction.
    //
    // The wildcard is now an explicit list of the DEATH-VERB conjugations,
    // word-bounded. `margi`, `marriage` and `margashirsha` are not among them
    // and cannot be: none of `-unga -ungi -ega -egi -enge -oge -ogi -na -ne`
    // completes any of those words. Coverage of the genuine asks is unchanged
    // — proven by the Hinglish cases in the adversarial suite, which are
    // asserted alongside the three false positives above.
    re: new RegExp(
      `\\bkab\\s+mar(unga|ungi|ega|egi|enge|oge|ogi|na|ne)\\b` +
        `|\\bmar(unga|ungi|ega|egi|enge)\\s+kab\\b` +
        `|\\bmar(unga|ungi|ega|egi|enge)\\b` +
        `|\\bmarne\\b|\\bmarna\\s+hai\\b` +
        `|\\bmaut\\s+kab\\b|\\bkab\\s+maut\\b` +
        `|(मैं कब मर|कब मरूं|मृत्यु कब|कब मृत्यु|मौत कब|कब मौत)`,
    ),
    squashed: ['kabmarunga', 'kabmarungi', 'kabmarega', 'kabmarna'],
  },

  {
    id: 'hs1.odia_when_will_i_die',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    // HARDENING ROUND, H-1 — ODIA.
    //
    // The native is in Bhubaneswar, Odisha. Odia is the state language and the
    // first language of the cohort most likely to reach this instrument, and
    // the first build's coverage of it was ZERO — English, Hindi and Hinglish
    // only. "mun kebe maribi" is the plainest possible way to ask this
    // question in the native's own state and it went through as `proceed`.
    //
    // Odia script, like Devanagari, cannot be matched with `\b` (JS word
    // boundaries are ASCII-only) and vanishes from the squashed form, so the
    // script alternation runs unbounded; the romanized half is word-bounded.
    //
    // SCOPE, STATED HONESTLY: this covers the death-verb (ମରିବା / mariba) and
    // mṛtyu forms, not the full language. It is a real and substantial
    // improvement over nothing; it is not a claim of Odia completeness, and a
    // native-speaker review would very likely add to it.
    re: new RegExp(
      `\\bkebe\\s+mari\\w*\\b|\\bmari(bi|ba|biki|jibi|jiba)\\b` +
        `|\\bmrityu\\s+kebe\\b|\\bkebe\\s+mrityu\\b|\\bjibana\\s+sesa\\b` +
        `|(କେବେ ମରି|ମରିବି|ମରିବ|ମରିଯିବି|ମୃତ୍ୟୁ କେବେ|କେବେ ମୃତ୍ୟୁ)`,
    ),
    squashed: ['kebemaribi', 'kebemariba', 'munkebemaribi'],
  },
  {
    id: 'hs1.maximum_age',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    // "What is the maximum age indicated by my chart?" is a date-of-death
    // request with the noun swapped. So is "how many years is my ayush".
    //
    // Two alternations, because the two halves need different evidence:
    //  (a) `maximum life ?span|longevity|ayush` — the NOUN is already
    //      mortality-specific, so no further pinning is needed;
    //  (b) `maximum age|years` — "the maximum age of the Jupiter transit
    //      effect" is an ordinary question (a real false positive this suite
    //      caught), so this half additionally requires the chart or the native
    //      in the same sentence.
    re: /\b(maximum|max|total|full|allotted|granted|indicated) (life ?span|longevity|ayush|ayurdaya)\b|\b(maximum|max|total|full|indicated|allotted|granted) (age|years)\b[^.?!]{0,40}\b(chart|horoscope|kundli|kundali|native|for me|my life)\b|\b(my|his|her|their|the native'?s) (maximum|max|total|full|allotted|granted) (age|years|life ?span|longevity)\b|\b(age|years) (indicated|allotted|granted|given) (by|in|for) (my|the|his|her|their) (chart|horoscope|kundli|kundali)\b/,
    // `maximumage` is deliberately ABSENT from the squashed list even though it
    // is long enough. The squashed surface cannot see the lookahead-style
    // context the `re` above uses, and "the maximum age of the Jupiter transit
    // effect" squashes to a string containing `maximumage` — a real false
    // positive this suite caught. A squashed entry must be unambiguous with NO
    // surrounding context, not merely long; `maximumlifespan` is, `maximumage`
    // is not.
    squashed: ['maximumlifespan', 'totallifespan', 'allottedyears', 'grantedyears', 'allottedlifespan'],
  },
  {
    id: 'hs1.pass_in_year',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    // Sentence-completion bait ("the native will pass in the year ___").
    re: /\b(will|would|shall|does|did|is going to)\s+pass\s+(in|on|at|during)\s+(the\s+)?(year|month|decade|\d{4})\b/,
    squashed: ['willpassintheyear', 'willpassinthemonth'],
  },
  {
    id: 'hs1.years_remaining',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    // "on a scale of years remaining", "how many years are left".
    re: new RegExp(`\\b(years|months|days)\\s+(remaining|left)${MUNDANE_REMAINDER_GUARD}`),
    // No squashed entries, deliberately: `yearsremaining` / `yearsleft` are
    // exactly as true of a lease, a visa and a dasha as of a life, and the
    // squashed surface cannot see the guard that distinguishes them. Losing the
    // spelling-evasion coverage for this one phrasing is the right trade — an
    // evader who writes "y.e.a.r.s r.e.m.a.i.n.i.n.g" is caught by the far less
    // ambiguous patterns their question also contains.
    squashed: [],
  },
  {
    id: 'hs1.death_prediction_request',
    cls: 'hs1_date_of_death',
    severity: 'hard_stop',
    re: /\b(predict|calculate|compute|tell me|give me|show me|reveal|estimate|pinpoint|forecast)\b[^.?!]{0,50}\b(death|demise|passing|end of (my|his|her|their) life|dying|mortality date)\b/,
    squashed: [
      'predictmydeath',
      'predictdeath',
      'calculatemydeath',
      'calculatedateofdeath',
      'tellmewhenidie',
      'estimatemydeath',
      'forecastmydeath',
    ],
  },
]

/** HS-4 — mortality-window / longevity domain (aggregate framing only). */
const HS4_PATTERNS: PhrasePattern[] = [
  {
    id: 'hs4.longevity_terms',
    cls: 'hs4_mortality_window',
    severity: 'review_required',
    re: /\b(ayurdaya|ayurdaaya|ayu[rs]?[- ]?daya|alpayu|madhyayu|purnayu|dirghayu|deerghayu|ayush|longevity|life ?span|life expectancy|life ?length)\b/,
    squashed: [
      'ayurdaya',
      'ayurdaaya',
      'alpayu',
      'madhyayu',
      'purnayu',
      'dirghayu',
      'longevity',
      'lifespan',
      'lifeexpectancy',
    ],
  },
  {
    id: 'hs4.mortality_terms',
    cls: 'hs4_mortality_window',
    severity: 'review_required',
    // `dying` carries a negative lookahead for "dying to/for" — "I'm dying to
    // know what my Jupiter return brings" is an idiom, not a mortality query,
    // and it was a REAL false positive this suite caught. Note what the carve-
    // out is and is not: it is a narrowing of the PATTERN (an idiom the word
    // participates in), not an exemption branch an attacker can trigger. "When
    // am I dying?" still matches; "dying to know when I die" still matches on
    // `die`.
    re: /\b(mortality|marak\w*|maran\w*|mrityu|mrtyu|mrutyu|death|deaths|dying(?!\s+(?:to|for)\b)|demise|deceased|fatal|fatality|terminal illness)\b/,
    squashed: ['mortality', 'marakasthana', 'deathindicator', 'deathyoga', 'terminalillness'],
  },
  {
    id: 'hs4.survival_ask',
    cls: 'hs4_mortality_window',
    severity: 'review_required',
    // The SUBJECT is pinned to a person. "Will my business survive the quarter?"
    // was a real false positive: the survival verb alone is not a mortality
    // signal, the survival of a PERSON is. Widening this back to a bare
    // `will ... survive` would re-open it.
    re: /\b(will|would|can|could|is|are|am)\s+(i|he|she|they|we|my (father|mother|dad|mum|mom|son|daughter|wife|husband|partner|child|children|brother|sister|friend)|the (native|subject|patient)|this (native|person|chart ?holder))\b[^.?!]{0,40}\b(survive|make it|pull through|live through|come out alive|outlive|be alive)\b/,
    squashed: ['willisurvive', 'willimakeit', 'willilivethrough', 'willicomeoutalive'],
  },
]

/** HS-3 — health-crisis and mental-health domains. */
const HS3_PATTERNS: PhrasePattern[] = [
  {
    id: 'hs3.mental_health_terms',
    cls: 'hs3_mental_health',
    severity: 'review_required',
    re: /\b(depression|depressed|depressive|anxiety|anxious|panic attacks?|bipolar|schizophreni\w*|psychosis|psychotic|ptsd|ocd|adhd|eating disorder|anorexi\w*|bulimi\w*|mental (health|illness|breakdown)|nervous breakdown|psychiatr\w*|therapy|therapist|counsel?ling|antidepressant\w*|addiction|alcoholism|substance abuse|self ?esteem crisis|burnout)\b/,
    squashed: [
      'depression',
      'bipolardisorder',
      'schizophrenia',
      'panicattack',
      'mentalhealth',
      'mentalillness',
      'nervousbreakdown',
      'eatingdisorder',
      'antidepressant',
      'substanceabuse',
    ],
  },
  {
    id: 'hs3.health_crisis_terms',
    cls: 'hs3_health_crisis',
    severity: 'review_required',
    re: /\b(cancer|carcinoma|tumou?r|malignan\w*|chemotherapy|chemo|radiotherapy|leukemia|leukaemia|stroke|heart attack|cardiac arrest|kidney failure|renal failure|liver failure|organ failure|hiv|aids|sepsis|coma|paralysis|paralysed|paralyzed|amputation|transplant|dialysis|icu|intensive care|life support|ventilator|surgery|operation|biopsy|diagnos\w*|prognosis|remission|relapse|chronic illness|incurable|untreatable|palliative|hospice)\b/,
    squashed: [
      'chemotherapy',
      'radiotherapy',
      'heartattack',
      'cardiacarrest',
      'kidneyfailure',
      'organfailure',
      'intensivecare',
      'lifesupport',
      'palliativecare',
      'terminaldiagnosis',
    ],
  },
  {
    id: 'hs3.recovery_ask',
    cls: 'hs3_health_crisis',
    severity: 'review_required',
    re: /\b(will|would|can|could|am i going to)\b[^.?!]{0,40}\b(recover|get better|be cured|beat (it|this|the (cancer|illness|disease))|heal completely)\b/,
    squashed: ['williprecover', 'willirecover', 'willigetbetter', 'willibecured', 'willibeatthis'],
  },
]

const ALL_PHRASE_PATTERNS: PhrasePattern[] = [
  ...HS2_PATTERNS,
  ...HS1_PATTERNS,
  ...HS4_PATTERNS,
  ...HS3_PATTERNS,
]

/**
 * The reviewed exceptions to MIN_SQUASHED_PATTERN_LENGTH.
 *
 * An escape hatch on a safety guard is a liability, so this one is a
 * module-level ALLOWLIST keyed by the exact string rather than a boolean an
 * author can set on a new pattern. Adding an entry is a diff someone reads, and
 * each entry carries the argument for why the substring is unambiguous with no
 * word boundary around it.
 *
 *  · `suicide` / `unalive` — there is no English word that contains either as a
 *    substring and is about anything else. `suicided`, `unalived` are the only
 *    extensions and both are in scope. Both are HS-2, where over-triggering
 *    costs a reader one supportive message and under-triggering costs what this
 *    lane exists to prevent.
 *  · `alpayu` / `purnayu` — Sanskrit longevity-class terms. They are not
 *    substrings of any English word, and inside Devanagari-transliterated text
 *    they appear only in the longevity context they name. Their HS-4
 *    consequence is a review path, not a refusal.
 */
const SHORT_SQUASHED_ALLOWLIST = new Set(['suicide', 'unalive', 'alpayu', 'purnayu'])

/** Absolute floor. Nothing below this, allowlisted or not. */
const ABSOLUTE_MIN_SQUASHED_LENGTH = 6

// Load-time guard: the squashed surface has no word boundaries, so a short
// pattern there is a false-positive generator. Failing at import is deliberate —
// a future author who adds `['die']` finds out immediately, not in production.
for (const p of ALL_PHRASE_PATTERNS) {
  for (const s of p.squashed ?? []) {
    if (s.length < ABSOLUTE_MIN_SQUASHED_LENGTH) {
      throw new Error(
        `[pariprashna/safety] squashed pattern "${s}" in ${p.id} is below the ABSOLUTE ` +
          `floor (${ABSOLUTE_MIN_SQUASHED_LENGTH}). There is no allowlist entry for a string this short.`,
      )
    }
    if (s.length < MIN_SQUASHED_PATTERN_LENGTH && !SHORT_SQUASHED_ALLOWLIST.has(s)) {
      throw new Error(
        `[pariprashna/safety] squashed pattern "${s}" in ${p.id} is shorter than ` +
          `MIN_SQUASHED_PATTERN_LENGTH (${MIN_SQUASHED_PATTERN_LENGTH}). Squashed matching ` +
          `has no word boundaries; use a word-bounded \`re\` instead.`,
      )
    }
    if (!/^[a-z0-9]+$/.test(s)) {
      throw new Error(
        `[pariprashna/safety] squashed pattern "${s}" in ${p.id} contains characters that ` +
          `normalization strips; it can never match.`,
      )
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 2. COMBINATION LEXICONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Tier-A mortality lexicon: unambiguous. One hit is HS-4 on its own.
 *
 * `dying` carries the same "dying to/for" idiom narrowing as the HS-4 phrase
 * pattern above, for the same reason and with the same limits.
 * `(my|his|her|their) life (ends|…)` is here rather than in tier B because the
 * END of a life is not the ambiguous sense of the word "life".
 */
const MORTALITY_TERMS_A =
  /\b(death|dying(?!\s+(?:to|for)\b)|die|dies|died|dead|demise|deceased|passing away|passed away|pass away|passes away|perish\w*|expire[sd]?|mortality|mortal|marak\w*|maran\w*|mrityu|mrtyu|mrutyu|ayurdaya|ayurdaaya|ayush|alpayu|madhyayu|purnayu|dirghayu|longevity|life ?span|life expectancy|end of life|final days|last days|last breath|final breath|funeral|cremation|obituary|leave this world|leave the body)\b|\b(my|his|her|their|the) (life|lifetime) (ends|ending|will end|is over|finishes|runs out)\b|\b(end|ending|conclusion|close|terminal point|end ?point|final point) of (my|his|her|their|the) (life|lifetime|days|life ?span)\b/

/**
 * Tier-B lifespan lexicon: AMBIGUOUS on its own ("what does my life look
 * like?"). Counts only in combination with a duration/limit marker, which is
 * what turns "my life" into "how much of my life is left".
 */
const LIFESPAN_TERMS_B =
  /\b(live|living|alive|survive|surviving|lifetime|my life|his life|her life|their life|remain alive|still be here|still around|be around|be here|around for|here for)\b/

/** Duration/limit markers — the half that makes tier B into a mortality ask. */
const DURATION_LIMIT_TERMS =
  /\b(how long|how many years|how many months|how many more|how much more|years left|time left|time remaining|remaining years|until when|till when|up to what|until what|till what|how much longer|before it ends|before the end|final year|last year of)\b/

/**
 * Temporal specificity — the half that turns HS-4 into HS-1.
 *
 * `the (year|date|…)` and `(resulting|final|…) (year|…)` are here because both
 * were REAL misses this suite caught ("hint at the year my life ends",
 * "compute my alpayu class and give me the resulting year"). They are broad on
 * their own — which is safe, because this lexicon NEVER fires alone: HS-1 needs
 * a tier-A mortality term in the SAME query.
 */
const TEMPORAL_SPECIFICITY_TERMS =
  // `kab` (Hindi/Urdu) and `kebe` (Odia) are "when", and their absence here was
  // a real gap the round-3 suite caught: "meri mrityu kab hogi" carried a
  // tier-A mortality term (`mrityu`) and an explicit demand for a time, and
  // landed on HS-4 rather than HS-1 purely because this lexicon was
  // English-only. Adding them here rather than as another phrase pattern is
  // the general fix — it upgrades EVERY mortality term in the tier-A lexicon,
  // in either language, not just the one phrasing the test happened to name.
  //
  // Safe by construction, and this is the reason this lexicon is allowed to be
  // broad: it NEVER fires alone. HS-1 needs a tier-A mortality term in the same
  // query, so "meri marriage kab hogi" and "Shani kab margi hoga" — which have
  // no mortality term at all — remain untouched. Word-bounded, so `kabhi`
  // ("ever") does not match.
  /\b(when|kab|kebe|what date|which date|exact date|what year|which year|what month|which month|what day|which day|what age|which age|at what age|how old|exact|exactly|precise\w*|specific date|specifically when|pinpoint|to the (day|month|year)|timing of|time of|date for|the (year|date|day|month|age)|(resulting|final|specific|approximate|estimated) (year|age|date|month|day|time)|(terminal|end|final|cut ?off) ?point|conclude\w*|runs? out|how far)\b/

/** Displacement / hypothetical framing. RAISES; can never lower. */
const EVASION_MARKERS: Array<{ id: string; re: RegExp }> = [
  { id: 'hypothetical', re: /\b(hypothetical\w*|theoretical\w*|purely academic|just curious|thought experiment|in theory|for argument'?s sake)\b/ },
  { id: 'third_party_displacement', re: /\b(asking for (a|my) (friend|colleague|relative)|for a friend|a friend of mine|my client|someone (i know|else)|a person with|this person|a hypothetical (person|native|client))\b/ },
  { id: 'fiction_framing', re: /\b(for (a|my) (novel|story|book|screenplay|character|game|roleplay)|fictional (character|native)|in my story|as a character)\b/ },
  { id: 'role_play_override', re: /\b(pretend|imagine you (are|were)|act as if|ignore (your|the|all) (previous |prior )?(instructions|rules|guidelines|safety)|no filters?|without (any )?(restrictions|guardrails|safety))\b/ },
  { id: 'indirect_ask', re: /\b(don'?t tell me directly|without saying it|hint at|imply|between the lines|you know what i mean|read between)\b/ },
  { id: 'academic_framing', re: /\b(for research purposes|for a (study|paper|thesis|dissertation)|academically speaking|as a case study)\b/ },
  {
    id: 'completion_bait',
    // "Complete this sentence: the native will pass in the year ___". Asking
    // for a COMPLETION rather than an ANSWER is one of the oldest ways past a
    // refusal, and it is a marker, not an excuse.
    re: /\b(complete (this|the) sentence|fill in the blanks?|finish (this|the) sentence|continue the (text|sentence|passage)|what comes next|_{3,})\b/,
  },
]

// ═══════════════════════════════════════════════════════════════════════════
// 3. DOMAIN / CAPABILITY RULES
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Planner domain → class. Domains arrive from the plan, not the question, so
 * this family fires on a question with no trigger words in it at all.
 *
 * NOTE the ordering constraint this creates and does not hide: the SafetyPolicyGate
 * runs BEFORE the planner (PPR-12 — "a blocked class must never build a
 * retrieval plan"), so at gate time there IS no plan and this family sees only
 * whatever domains a caller supplied. It is wired for the second call site —
 * `reclassifyWithPlan`, run by the plan stage against the produced plan — which
 * is how a class that only becomes visible after planning still gets caught
 * before synthesis. This is stated rather than glossed: the pre-plan pass is
 * query-only, and that is a real limit of running before the planner.
 */
export const DOMAIN_CLASS_RULES: Array<{ domain: RegExp; cls: SafetyClass; severity: SafetySeverity }> = [
  { domain: /^(longevity|mortality|ayurdaya|lifespan)$/i, cls: 'hs4_mortality_window', severity: 'review_required' },
  { domain: /^(health|medical|disease|illness|body)$/i, cls: 'hs3_health_crisis', severity: 'review_required' },
  { domain: /^(mental_health|mental|psyche|psychology|mind)$/i, cls: 'hs3_mental_health', severity: 'review_required' },
]

/**
 * Capability → class. The registry's own mortality/medical capabilities.
 * Shared with `sensitive_capabilities.ts`, which owns the canonical list; this
 * map only says which CLASS each one implies.
 */
export const CAPABILITY_CLASS_RULES: Record<string, SafetyClass> = {
  get_ayurdaya: 'hs4_mortality_window',
  ganita_ayurdaya_get: 'hs4_mortality_window',
  assess_health: 'hs3_health_crisis',
  get_medical_indications: 'hs3_health_crisis',
  ganita_medical_get: 'hs3_health_crisis',
  query_medical_mappings: 'hs3_health_crisis',
  query_nakshatra_medical: 'hs3_health_crisis',
  query_sign_medical: 'hs3_health_crisis',
  ref_sign_medical_get: 'hs3_health_crisis',
}

// ═══════════════════════════════════════════════════════════════════════════
// The classifier
// ═══════════════════════════════════════════════════════════════════════════

export interface ClassifierInput {
  /** The reader's question text. */
  queryText: string
  /** Planner domains, when a plan already exists (the post-plan pass). */
  domains?: readonly string[]
  /** Authorized capability names, when a plan already exists. */
  capabilities?: readonly string[]
}

export interface ClassificationResult {
  detections: SafetyDetection[]
  evasion_markers: SafetyEvasionMarker[]
  classes: SafetyClass[]
  severity: SafetySeverity
  /** Exposed for tests and debugging; never persisted. */
  normalized: NormalizedQueryText
}

/**
 * The matched text from the FIRST normalized surface that matches, or null.
 *
 * `surfaces` is `NormalizedQueryText.normalizedAll` — the `1 → i` and `1 → l`
 * readings of the same query (normalize.ts's header explains why there are
 * two). A pattern needs only one of them, so this is an OR across surfaces and
 * can only ever find MORE than a single-surface match could.
 */
function firstMatch(surfaces: readonly string[], re: RegExp): string | null {
  for (const s of surfaces) {
    const m = s.match(re)
    if (m) return m[0]
  }
  return null
}

function pushDetection(
  out: SafetyDetection[],
  cls: SafetyClass,
  severity: SafetySeverity,
  detector: string,
  rule: string,
  span: string,
  surface: SafetyDetection['surface'],
): void {
  out.push({ cls, severity, detector, rule, matched_span_hash: spanHash(span), surface })
}

/**
 * Run every deterministic detector.
 *
 * Pure. Same input → same output, forever. No branch in here can return fewer
 * detections than the patterns produced.
 */
export function classifyQuery(input: ClassifierInput): ClassificationResult {
  const norm = normalizeForClassification(input.queryText ?? '')
  const detections: SafetyDetection[] = []
  const evasion: SafetyEvasionMarker[] = []

  // ── Family 1: phrase patterns. ────────────────────────────────────────────
  //
  // Every pattern runs against EVERY normalized surface (`normalizedAll` — the
  // `1 → i` and `1 → l` readings; see normalize.ts's header). A pattern needs
  // only ONE surface to match, which is exactly what makes the leet `1`
  // ambiguity non-destructive: `ki11 myself` matches on the l-surface, `d1e`
  // matches on the i-surface, and a query containing both is caught twice.
  // `firstMatch` stops at the first surface that hits, so a query with no
  // ambiguous glyph (the overwhelming majority) does exactly the work it did
  // before — `normalizedAll` has one entry.
  for (const p of ALL_PHRASE_PATTERNS) {
    if (p.re) {
      const m = firstMatch(norm.normalizedAll, p.re)
      if (m) pushDetection(detections, p.cls, p.severity, 'phrase', p.id, m, 'query')
    }
    for (const s of p.squashed ?? []) {
      if (norm.squashedAll.some((sq) => sq.includes(s))) {
        pushDetection(detections, p.cls, p.severity, 'phrase_squashed', `${p.id}:${s}`, s, 'query')
      }
    }
  }

  // ── Family 2: combination rules. ──────────────────────────────────────────
  const mortalityA = firstMatch(norm.normalizedAll, MORTALITY_TERMS_A)
  const lifespanB = firstMatch(norm.normalizedAll, LIFESPAN_TERMS_B)
  const durationLimit = firstMatch(norm.normalizedAll, DURATION_LIMIT_TERMS)
  const temporal = firstMatch(norm.normalizedAll, TEMPORAL_SPECIFICITY_TERMS)

  if (mortalityA) {
    pushDetection(
      detections,
      'hs4_mortality_window',
      'review_required',
      'combination',
      'mortality_term_present',
      mortalityA,
      'query',
    )
    if (temporal) {
      // A mortality term plus a demand for a specific time IS a date-of-death
      // request, however it was phrased. This is the rule that catches the
      // paraphrases no phrase pattern anticipates.
      pushDetection(
        detections,
        'hs1_date_of_death',
        'hard_stop',
        'combination',
        'mortality_term_x_temporal_specificity',
        `${mortalityA}|${temporal}`,
        'query',
      )
    }
    if (durationLimit) {
      // A mortality term plus a DURATION demand is the same request stated as a
      // quantity rather than a point: "how many years is my ayush" wants a
      // number that resolves to a date. Caught by the round-2 probe.
      pushDetection(
        detections,
        'hs1_date_of_death',
        'hard_stop',
        'combination',
        'mortality_term_x_duration_limit',
        `${mortalityA}|${durationLimit}`,
        'query',
      )
    }
  }

  if (lifespanB && durationLimit) {
    // "how long will I live", "how many years do I have", "until when will I
    // still be around" — tier B only counts here, with the limit marker.
    pushDetection(
      detections,
      'hs4_mortality_window',
      'review_required',
      'combination',
      'lifespan_term_x_duration_limit',
      `${lifespanB}|${durationLimit}`,
      'query',
    )
    pushDetection(
      detections,
      'hs1_date_of_death',
      'hard_stop',
      'combination',
      'lifespan_term_x_duration_limit_is_individualized',
      `${lifespanB}|${durationLimit}`,
      'query',
    )
  }

  // ── Family 3: domain + capability rules. ──────────────────────────────────
  for (const d of input.domains ?? []) {
    for (const rule of DOMAIN_CLASS_RULES) {
      if (rule.domain.test(d)) {
        pushDetection(detections, rule.cls, rule.severity, 'domain', `domain:${d}`, d, 'domain')
      }
    }
  }
  for (const c of input.capabilities ?? []) {
    const cls = CAPABILITY_CLASS_RULES[c]
    if (cls) {
      pushDetection(detections, cls, 'review_required', 'capability', `capability:${c}`, c, 'capability')
    }
  }

  // ── Evasion markers. Recorded, and they RAISE. ────────────────────────────
  for (const e of EVASION_MARKERS) {
    const m = firstMatch(norm.normalizedAll, e.re)
    if (m) evasion.push({ marker: e.id, matched_span_hash: spanHash(m) })
  }

  // ── Class implication: HS-1 implies HS-4 by construction. ─────────────────
  // A date-of-death request IS a mortality-window request, so the HS-4 controls
  // (aggregate framing, the full HS-3 review path) apply to it too. Stated as a
  // derivation rather than duplicated into every HS-1 pattern.
  if (detections.some((d) => d.cls === 'hs1_date_of_death') && !detections.some((d) => d.cls === 'hs4_mortality_window')) {
    detections.push({
      cls: 'hs4_mortality_window',
      severity: 'review_required',
      detector: 'implication',
      rule: 'hs1_implies_hs4',
      matched_span_hash: spanHash('hs1_implies_hs4'),
      surface: 'query',
    })
  }

  // ── Evasion raises severity of everything already detected. ───────────────
  // One step up the total order, never down, and never from `none`: a
  // displacement marker on a question with NO detected class is not itself a
  // safety event (people say "hypothetically" about career questions too).
  const raised: SafetyDetection[] = evasion.length
    ? detections.map((d) => ({ ...d, severity: raiseOneStep(d.severity) }))
    : detections

  const classes = SAFETY_CLASSES.filter((c) => raised.some((d) => d.cls === c))
  const severity = raised.reduce<SafetySeverity>((acc, d) => maxSeverity(acc, d.severity), 'none')

  return { detections: raised, evasion_markers: evasion, classes, severity, normalized: norm }
}

function raiseOneStep(s: SafetySeverity): SafetySeverity {
  if (s === 'none') return 'none'
  if (s === 'advisory') return 'review_required'
  return 'hard_stop'
}

/**
 * The post-plan pass (PPR-12's "plan-time" enforcement point).
 *
 * Re-runs the classifier with the plan's own domains and authorized
 * capabilities folded in, and returns the UNION with the pre-plan result.
 * Union, not replacement: a class detected before planning can never be
 * un-detected by a plan that happens not to mention it.
 */
export function reclassifyWithPlan(
  prior: ClassificationResult,
  input: ClassifierInput,
): ClassificationResult {
  const next = classifyQuery(input)
  const detections = [...prior.detections, ...next.detections.filter((d) => d.surface !== 'query')]
  const evasion_markers = prior.evasion_markers.length ? prior.evasion_markers : next.evasion_markers
  const classes = SAFETY_CLASSES.filter((c) => detections.some((d) => d.cls === c))
  const severity = detections.reduce<SafetySeverity>((acc, d) => maxSeverity(acc, d.severity), 'none')
  return { detections, evasion_markers, classes, severity, normalized: prior.normalized }
}

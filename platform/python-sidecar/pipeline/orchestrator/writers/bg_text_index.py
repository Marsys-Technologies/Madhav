"""
bg_text_index writer — deterministic topic_tag classifier over classical_text_chunks.

Per CLAUDECODE_BRIEF_BG_TEXT_INDEX_v1_0.md (Doc 7 of 15) and holistic design v1.1 §2.2:
  - This is a measurement asset, not a data store.
  - The writer UPDATEs classical_text_chunks.topic_tag using a deterministic keyword-rule classifier.
  - ZERO LLM — pure Python keyword/regex matching against reference_topic_tags vocabulary.
  - The cockpit metric is: SELECT count(DISTINCT topic_tag) FROM classical_text_chunks
      WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL
  - Target floor: ≥400 distinct topic_tag values present on embedded chunks.

Performance design: two-stage classification.
  Stage 1: broad string.lower() token scan to detect candidate families (planet present? domain keyword?).
  Stage 2: apply only the relevant compiled regexes for the matched family.
  This avoids scanning all ~2000 rules against every chunk.

BRAHMA-BG-0-7 | L0 Brahmagyan Build — bg_text_index asset (Doc 7 of 15)
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult

logger = logging.getLogger(__name__)

# ── Ordinal suffix helper ─────────────────────────────────────────────────────

def _ordinal(n: int) -> str:
    """Return proper English ordinal for house/lord tag names.
    Matches reference_topic_tags format: 1→'1st', 2→'2nd', 3→'3rd', 4→'4th'...12→'12th'.
    """
    if n == 1:   return "1st"
    elif n == 2: return "2nd"
    elif n == 3: return "3rd"
    else:        return f"{n}th"


# ── Planet/sign/house name tables ─────────────────────────────────────────────

# Lowercase token sets for stage-1 fast scan
PLANET_TOKENS: dict[str, frozenset[str]] = {
    "sun":     frozenset(["sun", "surya", "ravi", "soorya", "arka", "aditya", "divakara"]),
    "moon":    frozenset(["moon", "chandra", "soma", "indu", "nishakar", "chandrama"]),
    "mars":    frozenset(["mars", "mangal", "mangala", "kuja", "angaraka", "bhauma", "chevvai"]),
    "mercury": frozenset(["mercury", "budha", "budh", "saumya", "boddha"]),
    "jupiter": frozenset(["jupiter", "guru", "brihaspati", "brahaspati", "devaguru"]),
    "venus":   frozenset(["venus", "shukra", "sukra", "sita", "bhargava"]),
    "saturn":  frozenset(["saturn", "shani", "sani", "manda", "sanaischara"]),
    "rahu":    frozenset(["rahu"]),
    "ketu":    frozenset(["ketu"]),
}

# All planet tokens combined for quick stage-1 detection
_ALL_PLANET_TOKENS: frozenset[str] = frozenset(
    t for tokens in PLANET_TOKENS.values() for t in tokens
)

# House ordinal names (lowercase) for stage-1 detection
HOUSE_TOKENS: dict[int, list[str]] = {
    1:  ["1st", "first", "lagna", "ascendant", "udaya"],
    2:  ["2nd", "second", "dhana", "dhan"],
    3:  ["3rd", "third", "sahaja", "bhratra"],
    4:  ["4th", "fourth", "sukha", "bandhu", "matru"],
    5:  ["5th", "fifth", "putra", "suta"],
    6:  ["6th", "sixth", "shatru", "ari", "ripu"],
    7:  ["7th", "seventh", "kalatra", "yuvati", "jamitra"],
    8:  ["8th", "eighth", "mrityu", "randhra", "ayu"],
    9:  ["9th", "ninth", "dharma", "bhagya", "pitru"],
    10: ["10th", "tenth", "karma", "rajya"],
    11: ["11th", "eleventh", "labha", "aya"],
    12: ["12th", "twelfth", "vyaya", "moksha"],
}

_ALL_HOUSE_TOKENS: frozenset[str] = frozenset(
    t for tokens in HOUSE_TOKENS.values() for t in tokens
)

# Sign names (tag_suffix → [lowercase terms])
SIGN_NAMES: dict[str, list[str]] = {
    "aries":       ["aries", "mesha"],
    "taurus":      ["taurus", "vrishabha", "vrisha"],
    "gemini":      ["gemini", "mithuna"],
    "cancer":      ["cancer", "karka", "karkata", "kataka"],
    "leo":         ["leo", "simha", "singh"],
    "virgo":       ["virgo", "kanya"],
    "libra":       ["libra", "tula"],
    "scorpio":     ["scorpio", "vrishchika", "vrischika"],
    "sagittarius": ["sagittarius", "dhanus", "dhanu"],
    "capricorn":   ["capricorn", "makara"],
    "aquarius":    ["aquarius", "kumbha"],
    "pisces":      ["pisces", "meena", "mina"],
}

_ALL_SIGN_TOKENS: frozenset[str] = frozenset(
    t for tokens in SIGN_NAMES.values() for t in tokens
)

# Domain keyword tokens for stage-1 detection
DOMAIN_KEYWORD_TOKENS: dict[str, frozenset[str]] = {
    "marriage":      frozenset(["marriage", "wife", "husband", "spouse", "kalatra", "vivaha", "patni", "dampatya"]),
    "career":        frozenset(["career", "profession", "karma", "livelihood", "occupation", "business", "trade", "employment"]),
    "wealth":        frozenset(["wealth", "dhana", "money", "riches", "financial", "fortune", "treasury", "artha"]),
    "health":        frozenset(["health", "disease", "illness", "sickness", "ailment", "rog", "roga", "vitality"]),
    "education":     frozenset(["education", "learning", "study", "knowledge", "vidya", "wisdom", "academic", "degree"]),
    "progeny":       frozenset(["progeny", "children", "child", "son", "daughter", "putra", "apatya", "offspring", "fertility", "conception"]),
    "property":      frozenset(["property", "land", "house", "bhumi", "griha", "building", "estate", "residence"]),
    "father":        frozenset(["father", "pitru", "pita", "pitri", "paternal"]),
    "mother":        frozenset(["mother", "matru", "mata", "maternal"]),
    "siblings":      frozenset(["sibling", "brother", "sister", "bhratra", "sahaja"]),
    "longevity":     frozenset(["longevity", "lifespan", "ayu", "ayurdaya", "death"]),
    "spirituality":  frozenset(["spirituality", "moksha", "liberation", "spiritual", "divine", "meditation", "samadhi", "renunciation", "sanyasa"]),
    "foreign_travel":frozenset(["foreign", "abroad", "travel", "journey", "voyage", "overseas", "videsh", "pravasa"]),
    "occult":        frozenset(["occult", "tantra", "mantra", "magic", "mystical"]),
    "enemies":       frozenset(["enemy", "enemies", "foe", "rival", "opponent", "shatru", "ripu"]),
    "friends":       frozenset(["friend", "mitra", "ally", "companion"]),
    "government":    frozenset(["government", "king", "ruler", "authority", "rajya", "raja", "official"]),
    "politics":      frozenset(["politic", "election", "parliament", "minister", "democracy", "vote"]),
    "fame":          frozenset(["fame", "celebrity", "renowned", "famous", "glory", "kirti", "yashas", "reputation"]),
    "status":        frozenset(["status", "rank", "position", "dignity", "prestige", "respect", "maryada"]),
    "romance":       frozenset(["romance", "love", "passion", "amour", "lover", "romantic", "courtship"]),
    "sexuality":     frozenset(["sexual", "sexuality", "lust", "libido", "sensual", "erotic", "kama"]),
    "speculation":   frozenset(["speculation", "gambling", "lottery", "risk", "wager", "bet"]),
    "vehicles":      frozenset(["vehicle", "conveyance", "vahana", "automobile", "transport", "chariot"]),
    "litigation":    frozenset(["litigation", "lawsuit", "legal", "court", "judge", "tribunal", "dispute"]),
    "debts":         frozenset(["debt", "loan", "borrow", "liability", "creditor", "arrear"]),
    "agriculture":   frozenset(["agriculture", "farming", "crop", "harvest", "farm", "field", "cultivation"]),
    "arts":          frozenset(["arts", "art", "music", "dance", "painting", "sculpture", "creative", "artist", "kala", "aesthetic"]),
    "research":      frozenset(["research", "investigation", "inquiry", "exploration", "scholarship"]),
    "inheritance":   frozenset(["inheritance", "legacy", "bequest", "inherit", "ancestral", "daya"]),
    "sade_sati":     frozenset(["sade", "sati"]),
    "dhaiya":        frozenset(["dhaiya", "ashtama"]),
    "gochara":       frozenset(["gochara", "transit"]),
    "dasha":         frozenset(["vimshottari", "ashtottari", "yogini", "kalachakra", "chara", "jaimini", "dasha"]),
}

_ALL_DOMAIN_TOKENS: frozenset[str] = frozenset(
    t for tokens in DOMAIN_KEYWORD_TOKENS.values() for t in tokens
)

# Timing/yoga detector tokens
_TIMING_TOKENS = frozenset(["timing", "period", "time", "dasha", "when", "year", "age", "predict", "fructif"])
_YOGA_TOKENS = frozenset(["yoga", "combination", "rajyoga", "conjunction", "planetary"])
_LORDSHIP_TOKENS = frozenset(["lord"])


# ── Compiled regex patterns (stage-2, applied only when stage-1 hits) ─────────

def _pat(*parts: str) -> re.Pattern:
    return re.compile("|".join(parts), re.I)


def _pp(planet: str) -> str:
    """Regex alternation for planet names."""
    syns = list(PLANET_TOKENS[planet])
    return r"(?:" + "|".join(re.escape(s) for s in syns) + r")"


def _hp(house_num: int) -> str:
    """Regex alternation for house ordinals/names."""
    terms = HOUSE_TOKENS[house_num]
    return r"(?:" + "|".join(re.escape(t) for t in terms) + r")"


def _sp(sign: str) -> str:
    """Regex alternation for sign names."""
    terms = SIGN_NAMES[sign]
    return r"(?:" + "|".join(re.escape(t) for t in terms) + r")"


# Build per-planet × house regex dict: planet_house_patterns[planet][house_num] = Pattern
def _build_planet_house_patterns() -> dict[str, dict[int, re.Pattern]]:
    result: dict[str, dict[int, re.Pattern]] = {}
    for planet in PLANET_TOKENS:
        pp = _pp(planet)
        result[planet] = {}
        for h in range(1, 13):
            hp = _hp(h)
            result[planet][h] = re.compile(
                pp + r".{0,60}" + hp + r"|\b" + hp + r".{0,40}" + pp,
                re.I,
            )
    return result


# Build per-planet × sign regex dict
def _build_planet_sign_patterns() -> dict[str, dict[str, re.Pattern]]:
    result: dict[str, dict[str, re.Pattern]] = {}
    for planet in PLANET_TOKENS:
        pp = _pp(planet)
        result[planet] = {}
        for sign in SIGN_NAMES:
            sp = _sp(sign)
            result[planet][sign] = re.compile(
                pp + r".{0,50}" + sp + r"|\b" + sp + r".{0,40}" + pp,
                re.I,
            )
    return result


# Build lordship regex dict: lordship_patterns[from_h][to_h] = Pattern
def _build_lordship_patterns() -> dict[int, dict[int, re.Pattern]]:
    result: dict[int, dict[int, re.Pattern]] = {}
    for fh in range(1, 13):
        hp_from = _hp(fh)
        result[fh] = {}
        for th in range(1, 13):
            hp_to = _hp(th)
            result[fh][th] = re.compile(
                r"\blord\b.{0,25}" + hp_from + r".{0,50}" + hp_to +
                r"|\b" + hp_from + r".{0,20}\blord\b.{0,50}" + hp_to,
                re.I,
            )
    return result


# Build dasha system patterns: dasha_patterns[system][planet] = Pattern
def _build_dasha_patterns() -> dict[str, dict[str, re.Pattern]]:
    result: dict[str, dict[str, re.Pattern]] = {}
    dasha_systems = {
        "vimshottari": r"\bvimshottari\b",
        "ashtottari":  r"\bashtottari\b",
        "yogini":      r"\byogini\b",
        "kalachakra":  r"\bkalachakra\b",
        "chara_jaimini": r"\b(?:chara|jaimini)\b",
    }
    dasha_planets = ["sun", "moon", "mars", "mercury", "jupiter"]
    for sys_name, sys_pat in dasha_systems.items():
        result[sys_name] = {}
        for planet in dasha_planets:
            pp = _pp(planet)
            result[sys_name][planet] = re.compile(
                sys_pat + r".{0,40}" + pp + r"|" + pp + r".{0,40}" + sys_pat,
                re.I,
            )
    return result


# Build domain patterns: domain_patterns[domain] = {yoga: Pattern, timing: Pattern, general: Pattern}
def _build_domain_patterns() -> dict[str, dict[str, re.Pattern]]:
    domain_specs: list[tuple[str, str]] = [
        ("marriage",       r"marriage|wife|husband|spouse|kalatra|vivaha|patnī|patni|strī|stri|jaya|dampatya"),
        ("career",         r"career|profession|karma|livelihood|occupation|business|trade|commerce|employment|vocation"),
        ("wealth",         r"wealth|dhana|money|riches|financial|affluence|fortune|treasury|artha"),
        ("health",         r"health|disease|illness|sickness|ailment|rog\b|roga|constitution|vitality"),
        ("education",      r"education|learning|study|knowledge|vidya|wisdom|school|college|academic|degree"),
        ("progeny",        r"progeny|children|child|son\b|daughter|putra|apatya|offspring|fertility|conception|womb"),
        ("property",       r"property|land\b|bhumi|griha|building|estate|residence"),
        ("father",         r"\bfather\b|pitru|pita\b|pitri|paternal"),
        ("mother",         r"\bmother\b|matru|mata\b|maternal"),
        ("siblings",       r"sibling|brother|sister|co.?born|bhratra|sahaja"),
        ("longevity",      r"longevity|long.?life|lifespan|ayu\b|ayurdaya|span.?of.?life|length.?of.?life|\bdeath\b"),
        ("spirituality",   r"spirituality|moksha|liberation|spiritual|divine|meditation|samadhi|renunciation|sanyasa"),
        ("foreign_travel", r"foreign|abroad|travel|journey|voyage|overseas|distant.?land|videsh|pravasa"),
        ("occult",         r"occult|tantra|mantra|magic|sorcery|mystical|hidden.?knowledge"),
        ("enemies",        r"\benem(?:y|ies)\b|foe\b|rival|opponent|adversary|shatru|ripu|\bari\b"),
        ("friends",        r"\bfriend|mitra\b|ally\b|companion"),
        ("government",     r"government|king\b|ruler|authority|rajya|raja\b|official|political.?power"),
        ("politics",       r"politic|election|parliament|minister|democracy|vote"),
        ("fame",           r"\bfame\b|celebrity|renowned|famous|glory|kirti|yashas|reputation"),
        ("status",         r"\bstatus\b|rank\b|position\b|dignity|prestige|respect|maryada"),
        ("romance",        r"romance|love\b|passion|amour|paramour|lover|romantic|courtship"),
        ("sexuality",      r"sexual|sexuality|lust|libido|sensual|erotic|kama\b|intercourse"),
        ("speculation",    r"speculation|gambling|lottery|risk\b|wager|bet\b"),
        ("vehicles",       r"vehicle|conveyance|vahana|automobile|transport|chariot|\bcar\b"),
        ("litigation",     r"litigation|lawsuit|legal\b|court\b|judge\b|tribunal|dispute"),
        ("debts",          r"\bdebt|loan\b|borrow|liability|creditor|arrear|\brin\b"),
        ("agriculture",    r"agriculture|farming|crop|harvest|farm\b|field\b|cultivation"),
        ("arts",           r"\barts?\b|music|dance|painting|sculpture|creative|artist|\bkala\b|aesthetic"),
        ("research",       r"research|investigation|inquiry|exploration|scholarship"),
        ("inheritance",    r"inheritance|legacy|bequest|inherit|ancestral.*property|daya\b"),
    ]
    result: dict[str, dict[str, re.Pattern]] = {}
    for domain, kw_pat in domain_specs:
        result[domain] = {
            "yoga":    re.compile(
                r"(?:" + kw_pat + r").{0,80}(?:yoga|combination|rajyoga|dhana.?yoga|conjunction|planetary.?combination)",
                re.I,
            ),
            "timing":  re.compile(
                r"(?:" + kw_pat + r").{0,80}(?:timing|period|time\b|dasha|when\b|year\b|age\b|predict|fructif)",
                re.I,
            ),
            "general": re.compile(r"(?:" + kw_pat + r")", re.I),
        }
    return result


# Compile all patterns once at module import
_PLANET_HOUSE = _build_planet_house_patterns()
_PLANET_SIGN  = _build_planet_sign_patterns()
_LORDSHIP     = _build_lordship_patterns()
_DASHA        = _build_dasha_patterns()
_DOMAIN       = _build_domain_patterns()

# Special patterns (high priority, checked first)
_SADE_SATI_PAT  = re.compile(r"\bsade[\s\-]?sati\b", re.I)
_DHAIYA_PAT     = re.compile(r"\bdhaiya\b|\bashtama\s+shani\b", re.I)
_GOCHARA_GEN_PAT= re.compile(r"\bgochara\b.{0,40}\b(?:general|transit|movement)\b|\btransit\s+general\b", re.I)
_JUP_TRANSIT_PAT= re.compile(r"\b(?:jupiter|guru|brihaspati)\b.{0,40}\bgochara\b|\bgochara\b.{0,40}\b(?:jupiter|guru)\b|\bjupiter\s+transit\b", re.I)
_SAT_TRANSIT_PAT= re.compile(r"\b(?:saturn|shani|sani)\b.{0,40}\bgochara\b|\bgochara\b.{0,40}\b(?:saturn|shani)\b|\bsaturn\s+transit\b", re.I)
_RAHU_TRANSIT_PAT=re.compile(r"\b(?:rahu|north\s+node)\b.{0,40}\bgochara\b|\bgochara\b.{0,40}\brahu\b|\brahu\s+transit\b", re.I)


# ── Fast word tokeniser ────────────────────────────────────────────────────────

_NON_ALNUM = re.compile(r"[^a-z0-9\s]")

def _tokens(text: str) -> frozenset[str]:
    """Lowercase word-token set from text (fast, no regex)."""
    lowered = text.lower()
    cleaned = _NON_ALNUM.sub(" ", lowered)
    return frozenset(cleaned.split())


# ── Main classifier ────────────────────────────────────────────────────────────

def classify_chunk(text: str, valid_tags: frozenset[str]) -> str | None:
    """
    Two-stage deterministic classifier.

    Stage 1: fast token-set intersection to detect candidate families.
    Stage 2: apply compiled regexes only for detected families.

    Returns first matching valid tag, or None.
    """
    toks = _tokens(text)

    # ── Priority 1: Special period/transit rules ──────────────────────────────
    if "sade" in toks or "sati" in toks:
        if _SADE_SATI_PAT.search(text):
            if "sade_sati" in valid_tags:
                return "sade_sati"

    if "dhaiya" in toks or ("ashtama" in toks and "shani" in toks):
        if _DHAIYA_PAT.search(text):
            if "dhaiya" in valid_tags:
                return "dhaiya"

    # ── Priority 2: Dasha system × planet ────────────────────────────────────
    has_dasha = bool(toks & DOMAIN_KEYWORD_TOKENS["dasha"])
    if has_dasha:
        for sys_name, planet_pats in _DASHA.items():
            for planet, pat in planet_pats.items():
                if toks & PLANET_TOKENS[planet]:
                    if pat.search(text):
                        tag = f"{sys_name}_{planet}_dasha"
                        if tag in valid_tags:
                            return tag

    # ── Priority 3: Lordship rules ────────────────────────────────────────────
    has_lord = "lord" in toks
    has_house = bool(toks & _ALL_HOUSE_TOKENS)
    if has_lord and has_house:
        for fh in range(1, 13):
            fh_toks = frozenset(HOUSE_TOKENS[fh])
            if not (toks & fh_toks):
                continue
            for th in range(1, 13):
                th_toks = frozenset(HOUSE_TOKENS[th])
                if not (toks & th_toks):
                    continue
                if _LORDSHIP[fh][th].search(text):
                    tag = f"lord_{_ordinal(fh)}_in_{_ordinal(th)}"
                    if tag in valid_tags:
                        return tag

    # ── Priority 4: Planet-in-house ───────────────────────────────────────────
    has_planet = bool(toks & _ALL_PLANET_TOKENS)
    if has_planet and has_house:
        for planet, planet_toks in PLANET_TOKENS.items():
            if not (toks & planet_toks):
                continue
            for h in range(1, 13):
                h_toks = frozenset(HOUSE_TOKENS[h])
                if not (toks & h_toks):
                    continue
                if _PLANET_HOUSE[planet][h].search(text):
                    tag = f"{planet}_in_{_ordinal(h)}"
                    if tag in valid_tags:
                        return tag

    # ── Priority 5: Planet-in-sign ────────────────────────────────────────────
    has_sign = bool(toks & _ALL_SIGN_TOKENS)
    if has_planet and has_sign:
        for planet, planet_toks in PLANET_TOKENS.items():
            if not (toks & planet_toks):
                continue
            for sign, sign_terms in SIGN_NAMES.items():
                sign_toks = frozenset(sign_terms)
                if not (toks & sign_toks):
                    continue
                if _PLANET_SIGN[planet][sign].search(text):
                    tag = f"{planet}_in_{sign}"
                    if tag in valid_tags:
                        return tag

    # ── Priority 6: Transit tags (gochara) ───────────────────────────────────
    if "gochara" in toks or "transit" in toks:
        if has_planet:
            if (toks & PLANET_TOKENS["jupiter"]) and _JUP_TRANSIT_PAT.search(text):
                if "jupiter_transit" in valid_tags:
                    return "jupiter_transit"
            if (toks & PLANET_TOKENS["saturn"]) and _SAT_TRANSIT_PAT.search(text):
                if "saturn_transit" in valid_tags:
                    return "saturn_transit"
            if (toks & PLANET_TOKENS["rahu"]) and _RAHU_TRANSIT_PAT.search(text):
                if "rahu_transit" in valid_tags:
                    return "rahu_transit"
        if _GOCHARA_GEN_PAT.search(text):
            if "gochara_general" in valid_tags:
                return "gochara_general"

    # ── Priority 7: Domain triads (yoga > timing > general) ──────────────────
    for domain, domain_toks in DOMAIN_KEYWORD_TOKENS.items():
        if domain in ("sade_sati", "dhaiya", "gochara", "dasha"):
            continue
        if not (toks & domain_toks):
            continue
        if domain not in _DOMAIN:
            continue
        pats = _DOMAIN[domain]
        # yoga first (most specific)
        if pats["yoga"].search(text):
            tag = f"{domain}_yoga"
            if tag in valid_tags:
                return tag
        # then timing
        if pats["timing"].search(text):
            tag = f"{domain}_timing"
            if tag in valid_tags:
                return tag
        # then general
        if pats["general"].search(text):
            tag = f"{domain}_general"
            if tag in valid_tags:
                return tag

    return None


# ── Writer ────────────────────────────────────────────────────────────────────

@register("bg_text_index")
class TextIndexWriter(WriterBase):
    asset_id = "bg_text_index"

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn

        if ctx.dry_run:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM classical_text_chunks WHERE embedding IS NOT NULL AND topic_tag IS NULL"
                )
                unclassified = cur.fetchone()[0]
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"dry_run=True; {unclassified} unclassified embedded chunks would be classified",
            )

        # ── Step 1: Load vocabulary from reference_topic_tags ─────────────────
        with conn.cursor() as cur:
            cur.execute("SELECT canonical_id FROM reference_topic_tags")
            rows = cur.fetchall()
        valid_tags: frozenset[str] = frozenset(r[0] for r in rows)
        logger.info("[bg_text_index] loaded %d valid tags from reference_topic_tags", len(valid_tags))

        if not valid_tags:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="HALT: reference_topic_tags is empty — vocabulary must be seeded first (bg_reference dependency)",
            )

        # ── Step 2: Check classical_text_chunks upstream ──────────────────────
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM classical_text_chunks WHERE embedding IS NOT NULL")
            embedded_count = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM classical_text_chunks WHERE embedding IS NOT NULL AND topic_tag IS NULL"
            )
            unclassified_count = cur.fetchone()[0]

        logger.info(
            "[bg_text_index] upstream: %d embedded chunks, %d unclassified (NULL topic_tag)",
            embedded_count, unclassified_count,
        )

        if embedded_count == 0:
            logger.info(
                "[bg_text_index] classical_text_chunks has no embedded chunks — returning 0 (floors-are-aspirational)"
            )
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="upstream empty: 0 embedded chunks; floor=0; rerun after bg_texts pipeline completes",
            )

        if unclassified_count == 0:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(DISTINCT topic_tag) FROM classical_text_chunks "
                    "WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL"
                )
                distinct_tags = cur.fetchone()[0]
            logger.info(
                "[bg_text_index] all chunks already classified; distinct_tags=%d (idempotent)", distinct_tags
            )
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"idempotent: all {embedded_count} embedded chunks already classified; distinct_tags={distinct_tags}",
            )

        # ── Step 3: Load unclassified embedded chunks ─────────────────────────
        with conn.cursor() as cur:
            cur.execute(
                "SELECT chunk_id, content_en FROM classical_text_chunks "
                "WHERE embedding IS NOT NULL AND topic_tag IS NULL"
            )
            chunk_rows = cur.fetchall()

        logger.info("[bg_text_index] classifying %d chunks...", len(chunk_rows))

        # ── Step 4: Classify + batch UPDATE ──────────────────────────────────
        tagged = 0
        skipped_no_match = 0
        skipped_invalid_tag = 0
        batch: list[tuple[str, str]] = []  # (tag, chunk_id)
        BATCH_SIZE = 500

        def _flush(b: list[tuple[str, str]]) -> int:
            if not b:
                return 0
            with conn.cursor() as cur:
                cur.executemany(
                    "UPDATE classical_text_chunks SET topic_tag = %s WHERE chunk_id = %s AND topic_tag IS NULL",
                    b,
                )
                return cur.rowcount

        for i, (chunk_id, content_en) in enumerate(chunk_rows):
            if not content_en:
                skipped_no_match += 1
                continue

            tag = classify_chunk(content_en, valid_tags)

            if tag is None:
                skipped_no_match += 1
                continue

            if tag not in valid_tags:
                logger.warning(
                    "[bg_text_index] SKIP chunk_id=%s: tag '%s' not in reference_topic_tags",
                    chunk_id, tag,
                )
                skipped_invalid_tag += 1
                continue

            batch.append((tag, chunk_id))

            if len(batch) >= BATCH_SIZE:
                n = _flush(batch)
                tagged += n
                batch.clear()
                logger.info(
                    "[bg_text_index] progress: tagged %d / %d chunks...", tagged + skipped_no_match, len(chunk_rows)
                )

        if batch:
            n = _flush(batch)
            tagged += n

        # ── Step 5: Measure cockpit metric ───────────────────────────────────
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(DISTINCT topic_tag) FROM classical_text_chunks "
                "WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL"
            )
            distinct_tags = cur.fetchone()[0]

        duration = time.time() - t0
        logger.info(
            "[bg_text_index] COMPLETE: tagged=%d, distinct_tags=%d, skipped_no_match=%d, "
            "skipped_invalid_tag=%d, duration=%.1fs",
            tagged, distinct_tags, skipped_no_match, skipped_invalid_tag, duration,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=tagged,
            duration_seconds=duration,
            notes=(
                f"tagged={tagged}; distinct_topic_tags={distinct_tags}; "
                f"skipped_no_match={skipped_no_match}; skipped_invalid_tag={skipped_invalid_tag}; "
                f"embedded_chunks={embedded_count}; unclassified_before={unclassified_count}"
            ),
        )

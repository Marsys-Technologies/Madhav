"""carriage_d1.py: the generic D1 (source correspondence) engine for the Carr gate (SS N-72 S2, N-73 (2): for an asset that
TRANSCRIBES classical content the applicable carriage check is D1, a match to a cited source; D3 is for computed assets).

Pure functions. No database, no network, no clock: asset_census.py passes in the fetched passages and the asset's rows, so
every case is testable from fixtures. An asset DECLARES its D1 in asset_declarations.json (`carriage.applies = "D1"` plus a
`carriage.spec`); an asset without a spec is never measured here.

THE SPEC (validated by `validate_spec`, read by `d1_measure`):
  matcher          the name of a rule engine in MATCHERS (a STATED matching rule; `ordinal_count_direction_effect_v2` first)
  table            the asset's own table (it must be the registry target_table; asserted by the caller)
  chunk_ids        the declared passage chunks, IN PAGE ORDER (classical_text_chunks.chunk_id); the span is cut from their join
  span             {start, end?}: markers; the passage is the join text from `start` (to `end`, else to the end of the join)
  fields           {claimant, count, direction, effect}: which columns of the table carry the claim
  direction_words  {stored value: word the translation uses}, e.g. {"backward": "rear"}: a DECLARED equivalence
  anchor_stems     word stems a passage uses to name the unit the effect is attached to (OCR variants listed), e.g. ["Latt", "Latin"]
  effect_marker    optional: the passage marker after which the effect sentences begin (OCR text); declared but ABSENT = NO_DETECTOR
  effect_end       optional: the marker that ends the effect section; declared but ABSENT = NO_DETECTOR
  effect_frame_words  lower-case words that may stand next to an effect phrase inside its clause ("will", "in", ...): part of the
                   STATED boundary rule (below)
  expected_rows    the number of rows the table must hold (completeness: a dropped row is not a PASS)
  extra_fields     other columns checked per row: {column, kind: "equals", value} or {column, kind: "passage_text", condition{text,start,end[,start_after,ocr_stops]}, condition_evidence, repairs[{from,to,evidence}]}
A PASS needs every row to match AND the row count to equal `expected_rows` AND no duplicate claimant. Any miss is PARTIAL naming the rows (L0 Q13).
`unsourced` and `refuted` are capped at NO_DETECTOR (anchor matching cannot tell a contradicted source from one not found). Anything that cannot be established
(a missing chunk, a hash that verifies against neither preimage, a missing span marker, an unreadable or empty table) is
NO_DETECTOR, never PASS, and the reason is in the record.

STATED READS (a D1 measurement makes exactly these two read-only SELECTs, listed in every record as `reads`): (1) classical_text_chunks WHERE
chunk_id IN (the declared chunk ids); (2) the asset's own table, restricted to the declared claim columns (and `chart_id = <census chart>`
when the table has that column).

WHAT A D1 PASS DOES AND DOES NOT SAY (stated in every record, `claims`): the match is against the ENGLISH translation
(`content_en`) only; the Sanskrit column is not matched (it is reported when NULL); the passages are OCR text not checked
against the printed book (`citation_state` is the one the declaration states, e.g. sourced_ocr_unverified); the stored chunk
hashes were verified with the text_id-prefixed preimage sha256(utf8(text_id + '::' + content_en)) of bg_texts.py `_sha256`,
or with the plain sha256(content_en) (named in the record), and a chunk whose stored hash matches neither is unreadable.
"""
from __future__ import annotations

import difflib
import hashlib
import unicodedata
import re

CITATION_STATES = ("sourced", "sourced_ocr_unverified", "unsourced", "refuted")
CITATION_CAPPED_STATES = ("unsourced", "refuted")    # a PASS/PARTIAL resting on one is capped at NO_DETECTOR (shared by name with asset_census.CITATION_CAPPED_STATES; a test pins agreement)
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_CHUNK_ID = re.compile(r"[a-z0-9][a-z0-9_]*")
_STEM = re.compile(r"[A-Za-z]{2,24}")
MARKER_MAX = 120
NOT_VERIFIED = None
NO_DET, PASS_V = "NO_DETECTOR", "PASS"
READS = ("classical_text_chunks WHERE chunk_id IN (the declared chunk ids)",
         "the asset's own table: the declared claim and extra columns (chart-scoped when the table has chart_id)")


class SpecError(ValueError):
    """A D1 spec is malformed."""


def _ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# ───────────────────────── passage verification ─────────────────────────

def preimages(text_id: str, content_en: str) -> dict:
    """The two hash preimages a stored chunk hash may be checked against, named."""
    return {"text_id::content_en": hashlib.sha256(f"{text_id}::{content_en}".encode("utf-8")).hexdigest(),
            "content_en": hashlib.sha256(content_en.encode("utf-8")).hexdigest()}


def verify_chunk(chunk: dict) -> dict:
    """{chunk_id, text_id, stored_sha256, preimage, computed_sha256, verified, content_sa_null, reason}. `verified` is True only
    when the stored `content_sha256` equals sha256 of the text_id-prefixed preimage (the bg_texts.py convention) or of the bare
    content_en. Anything else, including an absent hash, an absent text or a non-str field, is unreadable (never verified)."""
    cid = chunk.get("chunk_id")
    out = dict(chunk_id=cid, text_id=chunk.get("text_id"), stored_sha256=chunk.get("content_sha256"), preimage=None,
               computed_sha256=None, verified=False, content_sa_null=chunk.get("content_sa") in (None, ""), reason="")
    en, tid, stored = chunk.get("content_en"), chunk.get("text_id"), chunk.get("content_sha256")
    if not (isinstance(en, str) and en.strip()):
        out["reason"] = "content_en is empty or not text"
        return out
    if not (isinstance(tid, str) and tid):
        out["reason"] = "text_id is absent"
        return out
    if not (isinstance(stored, str) and re.fullmatch(r"[0-9a-f]{64}", stored)):
        out["reason"] = "the stored content_sha256 is absent or malformed"
        return out
    for name, h in preimages(tid, en).items():
        if h == stored:
            out.update(preimage=name, computed_sha256=h, verified=True)
            return out
    out["reason"] = ("the stored content_sha256 matches neither sha256(text_id + '::' + content_en) nor sha256(content_en): "
                     "the passage is unreadable for D1 (it may have changed since it was hashed)")
    return out


def chunks_digest(chunks_in_order: list[dict]) -> str:
    """sha256 over the declared chunks' (chunk_id, stored hash) in declared order: which stored passages were read."""
    h = hashlib.sha256()
    for c in chunks_in_order:
        h.update(f"{c['chunk_id']}:{c['stored_sha256']};".encode("utf-8"))
    return h.hexdigest()


def span_digest(segment: str) -> str:
    """sha256 of the CUT SPAN as read (whitespace-normalised join text from the start marker to the end marker): the identity of
    the passage a verdict was reached against. Text outside the span does not change it; any change inside it does, so a
    certificate bound to the old value is stale."""
    return hashlib.sha256(segment.encode("utf-8")).hexdigest()


def cut_span(joined: str, span: dict):
    """(segment, reason). The join text from span.start (to span.end when given). reason is non-empty when a marker is absent."""
    i = joined.find(span["start"])
    if i < 0:
        return None, f"the span start marker {span['start']!r} is absent from the declared passage"
    seg = joined[i:]
    end = span.get("end")
    if end:
        j = seg.find(end, len(span["start"]))
        if j < 0:
            return None, f"the span end marker {end!r} is absent after the start marker"
        seg = seg[:j]
    return seg, ""


# ───────────────────────── the matching rule: ordinal count + direction + effect (v2) ─────────────────────────
# STATED RULE (ordinal_count_direction_effect_v2), per row, over the cut segment (whitespace-normalised, English only):
#   count      the row's count n appears as an ordinal ("12th", whole token) followed, with NO other ordinal in between and within
#              90 characters without ';' or '.', by "that of <claimant>" / "that occupied by the <claimant>" (the page header an
#              OCR page break leaves, "Adh. XXVI MX", is allowed between "that" and "of");
#   direction  after that count the first of the declared direction words decides: it must be the word of the stored direction;
#   effect     the stored effect must EQUAL the claimant's WHOLE passage clause, never a window of the section:
#              (1) the effect section (from `effect_marker` to `effect_end`, both declared and present) is cut into CLAUSES at
#                  sentence punctuation (. ; ? !) and at a capitalised word that starts a new clause (the OCR often drops the full
#                  stop; a unit-anchor word or a claimant name is not such a start);
#              (2) the spec declares, per claimant, `effect_clauses[claimant] = {clause, effect}` (reviewed, with the document the
#                  mapping was read from in `effect_clauses_evidence`): the clause text as the passage gives it and the effect text the
#                  table stores for it. A claimant with a stored effect and no declared clause is a miss (the detector does not guess);
#              (3) the stored effect must equal the declared effect (lower-case words and digits only, so case, spacing and
#                  punctuation do not matter and nothing else does); the declared clause must equal, in the same normalisation,
#                  the one passage clause that holds THIS claimant's unit anchor ("Latta of <X> [and <Y>]", "<X>'s Latta"; stems
#                  declared); and the clause minus the effect's words may contain ONLY the unit anchor words and the declared
#                  `effect_frame_words` (so the effect is the whole content of the clause: no tail, no borrowed or concatenated text);
#              (4) an effect made only of anchor and frame words is a miss; a NULL effect needs NO anchor of this claimant in the
#                  effect section (nothing is invented for a row the passage gives no effect for).
#   extra      each declared extra column: `equals` an exact declared value, or `passage_text`: the spec DECLARES the condition
#              ({text, start, end}, per claimant if it differs, with `condition_evidence`); the declared text must equal ONE WHOLE
#              passage sentence and the stored value's words, after the declared OCR repairs, must equal the declared text: a prefix, a
#              suffix, extra passage text, a dropped opener, negation or reordering all break it. WHOLE SENTENCE (enforced by code):
#              the `start` begins with a declared sentence opener (`sentence_openers`, a subset of If/When/Where/Whenever/While/Should),
#              occurs once and follows the passage start or a stop+space; where the OCR LOST that stop the spec declares an
#              `ocr_lost_stop` {text = the last <= 5 words before the start, evidence, observed_garble}; `end` is a stop after it; the cut
#              holds exactly ONE stop-before-space-or-end (its terminal one), apart from <= 2 declared `ocr_stops` {text, evidence,
#              observed_garble} whose following passage text starts with a lower-case letter or digit (a real sentence end is
#              followed by a capital); the cut is <= 1.5 x the declared text. A per-claimant condition must share the shared start
#              and lost-stop text. Repairs are {from, to, evidence}: plain text, <= 8, <= 40 characters a side, WORD FOR WORD (equal
#              word counts, each word pair and the whole >= 60% alike), so a repair neither adds nor drops a word; an applied
#              repair's `to` must be a run of the sentence. NOT DETECTABLE: a repair that turns one real word into another real word
#              (even of opposite sense: "sick" -> "sickness", "anguishes" -> "anguish"): every repair is a claim the strategist reads.
#   Normalisation (stated): NFKC + lower-case; words are runs of letters/digits/combining marks of any script; ONLY punctuation,
#   symbols and whitespace are ignored. Benign variants accepted: case, spacing, punctuation of the stored effect/condition.
#   A declared effect may omit frame words that the clause carries (the frame words are tolerated around the effect INSIDE the clause);
#   the stored effect must equal the declared effect, so a frame-padded stored effect ("There will be quarrel in the") is a miss.

_COUNT_REACH = 90
MAX_REPAIRS = 8
REPAIR_MAX = 40
REPAIR_MIN_SIMILARITY = 0.6
REPAIR_MAX_DIFF = 0.4                   # a repair differs from its target in at most 40% of the characters
ALLOWED_OPENERS = ("If", "When", "Where", "Whenever", "While", "Should")
MAX_OCR_STOPS = 2
LOST_STOP_MAX_WORDS = 5
CUT_GROWTH = 1.5                        # the cut may not exceed 1.5 x the declared condition text
HATCH_NOTE_MAX = 200


def _ordinal(n: int) -> str:
    return rf"\b{n}(?:st|nd|rd|th)\b"


def _norm_effect(eff: str) -> str:
    return re.sub(r"\s+", " ", eff.strip()).rstrip(".").strip()


def _effect_ok_text(e: str) -> bool:
    return len(e) >= 5 and bool(re.search(r"[A-Za-z]{4,}", e))


def _toks(text: str) -> list:
    """The normalisation under which an effect, a clause and a condition are compared: NFKC, lower-case, and the text split into runs of
    letters / digits / combining marks (ANY script). Only punctuation, symbols and whitespace are ignored: a non-ASCII letter or a stray
    combining mark is part of its word ("Quarrel\u00e9" and "quarrel" + U+0301 are NOT "quarrel"); nothing is stripped or folded."""
    out, cur = [], []
    for ch in unicodedata.normalize("NFKC", text).lower():
        if ch.isalnum() or unicodedata.category(ch).startswith("M"):
            cur.append(ch)
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return out


def _anchors(sec: str, stems: list) -> list:
    """[(name, start, end, tokens)] unit anchors in `sec`: "Latta of [the] X [and Y]" and "X's Latta" (stems declared; OCR variants)."""
    st = "|".join(rf"{re.escape(x)}\w*" for x in stems)
    out = []
    for m in re.finditer(rf"(?:{st})\s+of\s+(?:the\s+)?([A-Z][a-z]+)(?:\s+and\s+([A-Z][a-z]+))?", sec):
        for nm in (m.group(1), m.group(2)):
            if nm:
                out.append((nm, m.start(), m.end(), _toks(m.group(0))))
    for m in re.finditer(rf"([A-Z][a-z]+)'s\s+(?:{st})", sec):
        out.append((m.group(1), m.start(), m.end(), _toks(m.group(0))))
    return sorted(out, key=lambda a: a[1])


def _clauses(sec: str, anchors: list, stems: list) -> list:
    """[(start, end)] clause spans of the effect section: cut after . ; ? ! and before a capitalised word that starts a clause (the
    previous word is lower-case, no punctuation between; a unit-anchor stem or a claimant name is not a clause start)."""
    names = {a[0] for a in anchors}
    stem_re = re.compile("|".join(rf"{re.escape(x)}\w*" for x in stems))
    cuts = [0]
    for m in re.finditer(r"[.;?!]\s+", sec):
        cuts.append(m.end())
    for m in re.finditer(r"(?<=[a-z])\s+([A-Z][a-z]+)\b", sec):
        w = m.group(1)
        if w in names or stem_re.fullmatch(w):
            continue
        cuts.append(m.start(1))
    cuts = sorted(set(cuts)) + [len(sec)]
    return [(a, b) for a, b in zip(cuts, cuts[1:]) if sec[a:b].strip()]


def _remove_run(tokens: list, run: list):
    """tokens without the first contiguous occurrence of `run`, or None when it does not occur."""
    n = len(run)
    for i in range(len(tokens) - n + 1):
        if tokens[i:i + n] == run:
            return tokens[:i] + tokens[i + n:]
    return None


def _effect_matches(eff: str, claimant: str, sec: str, spec: dict):
    """True only when the stored effect equals the claimant's declared effect AND the declared clause is exactly the claimant's whole
    passage clause with nothing but anchor and frame words around the effect (rule (1)-(4) above)."""
    e = _norm_effect(eff)
    if not _effect_ok_text(e):
        return False
    key = claimant.strip().lower()
    decl = next((v for k, v in (spec.get("effect_clauses") or {}).items() if k.strip().lower() == key), None)
    if not isinstance(decl, dict):
        return False
    frame = {w.lower() for w in spec.get("effect_frame_words", [])}
    etoks = _toks(e)
    if etoks != _toks(decl["effect"]):
        return False
    anchors = _anchors(sec, spec["anchor_stems"])
    mine = [a for a in anchors if a[0].lower() == key]
    if not mine:
        return False
    anchor_words = set()
    for a in anchors:
        anchor_words.update(a[3])
        anchor_words.add(a[0].lower())
    if not [t for t in etoks if t not in frame and t not in anchor_words]:
        return False                                              # only anchor / frame words: no effect at all
    holders = []
    for c0, c1 in _clauses(sec, anchors, spec["anchor_stems"]):
        if any(c0 <= a[1] and a[2] <= c1 for a in mine):
            holders.append(_toks(sec[c0:c1]))
    if len(holders) != 1 or holders[0] != _toks(decl["clause"]):
        return False
    left = _remove_run(holders[0], etoks)
    return left is not None and all(t in frame or t in anchor_words for t in left)


def _condition_decl(ef: dict, claimant) -> dict:
    """The declared {text, start, end, ...} for this claimant: the per-claimant entry when the spec declares one, else the shared one.
    A per-claimant entry is only a declared SUB-CLAUSE of the shared sentence: it must carry the shared condition's `start` and
    `ocr_lost_stop` text, else it is refused ({}), so a claimant cannot be pointed at some other passage sentence."""
    shared = ef.get("condition") or {}
    key = claimant.strip().lower() if isinstance(claimant, str) else None
    for k, v in (ef.get("by_claimant") or {}).items():
        if k.strip().lower() == key:
            same = isinstance(v, dict) and v.get("start") == shared.get("start") and _lost_text(v) == _lost_text(shared)
            return v if same else {}
    return shared


def _lost_text(decl: dict):
    lost = decl.get("ocr_lost_stop")
    return lost.get("text") if isinstance(lost, dict) else None


def _hatch_ok(h) -> bool:
    """A declared escape hatch: {text, evidence, observed_garble}, all non-blank strings (the note <= 200 chars, the text <= 40)."""
    return (isinstance(h, dict) and set(h) == {"text", "evidence", "observed_garble"}
            and all(isinstance(h[k], str) and h[k].strip() for k in h) and len(h["text"]) <= REPAIR_MAX
            and len(h["observed_garble"]) <= HATCH_NOTE_MAX)


_STOP_AT_BREAK = re.compile(r"[.;?!](?=\s|\Z)")


def _cut_sentence(seg: str, decl: dict, openers=None):
    """The tokens of ONE WHOLE passage sentence named by the declaration, or None. The sentence runs from the declared `start` marker
    to the declared `end` marker, INCLUSIVE, and is accepted only when:
      * `start` occurs exactly once in the passage and begins with a declared sentence opener (`openers`, a subset of
        ALLOWED_OPENERS): a mid-sentence fragment is not a start;
      * `start` is a TRUE sentence start: the passage start, or a stop (. ; ? !) and whitespace before it. A capital after a lower-case
        word is NOT a sentence start. Where the OCR LOST that stop, the spec declares `ocr_lost_stop` {text, evidence, observed_garble}:
        `text` is the last <= 5 words immediately before the start;
      * `end` is a stop and occurs after `start`, and the cut holds EXACTLY ONE stop-followed-by-space-or-end: its terminal one. At
        most 2 stops the OCR scattered inside the sentence are declared in `ocr_stops` ({text ending in a stop, evidence,
        observed_garble}); each must occur in the cut, never at its end, and be followed by a lower-case letter or a digit;
      * the cut is at most 1.5 x the declared condition text."""
    start, end, text = decl.get("start"), decl.get("end"), decl.get("text")
    if not (isinstance(start, str) and isinstance(end, str) and isinstance(text, str) and start and end and start[0].isupper()
            and end[-1] in ".;?!"):
        return None
    first = re.match(r"[A-Za-z]+", start)
    if not (first and isinstance(openers, (list, tuple)) and first.group(0) in openers and first.group(0) in ALLOWED_OPENERS):
        return None
    if seg.count(start) != 1:
        return None
    i = seg.find(start)
    before = seg[:i]
    lost = decl.get("ocr_lost_stop")
    if not (re.search(r"(?:\A|[.;?!]\s+)\Z", before)
            or (_hatch_ok(lost) and 1 <= len(lost["text"].split()) <= LOST_STOP_MAX_WORDS
                and re.search(r"(?:\A|\s)" + re.escape(lost["text"].strip()) + r"\s+\Z", before))):
        return None
    j = seg.find(end, i)
    if j < 0:
        return None
    cut = seg[i:j + len(end)]
    if len(cut) > CUT_GROWTH * len(text):
        return None
    scrub = cut
    stops = decl.get("ocr_stops") or []
    if not (isinstance(stops, list) and len(stops) <= MAX_OCR_STOPS):
        return None
    for h in stops:
        if not (_hatch_ok(h) and h["text"][-1] in ".;?!" and h["text"] in cut):
            return None
        for m in re.finditer(re.escape(h["text"]), cut):
            rest = cut[m.end():].lstrip()
            if not (rest and (rest[0].islower() or rest[0].isdigit())):
                return None
        scrub = scrub.replace(h["text"], h["text"][:-1])
    if len(_STOP_AT_BREAK.findall(scrub)) != 1:
        return None
    return _toks(cut)


def _apply_repairs(val: str, repairs: list, sentence: list):
    """The stored value with the declared OCR repairs applied as PLAIN text (no regex, no case folding), or None when an applied repair
    maps to words that are not a contiguous run of the passage sentence: a repair may only turn a stored form into the passage form of
    the SAME location, never import text."""
    for rp in repairs or []:
        if rp["from"] in val:
            to = _toks(rp["to"])
            if len(rp["from"].split()) != len(rp["to"].split()):          # word for word: a repair neither adds nor drops a word
                return None
            if not to or not any(sentence[k:k + len(to)] == to for k in range(len(sentence) - len(to) + 1)):
                return None
            val = val.replace(rp["from"], rp["to"])
    return val


def _extra_ok(row: dict, ef: dict, seg: str, claimant=None) -> bool:
    """`equals`: the exact declared value. `passage_text`: the stored value's words, after the declared OCR repairs, must EQUAL the
    words of the DECLARED condition, and the declared condition must equal ONE WHOLE passage sentence (_cut_sentence): the value is the
    condition, not a run that merely contains it (no prefix, suffix, dropped opener or extra passage text). `anchors` (optional) are
    a redundant extra check on the STORED value only: the equality above is what decides."""
    col, kind = ef["column"], ef["kind"]
    v = row.get(col)
    if not (isinstance(v, str) and v.strip()):
        return False
    if kind == "equals":
        return v == ef["value"]
    decl = _condition_decl(ef, claimant)
    sentence = _cut_sentence(seg, decl, ef.get("sentence_openers"))
    if sentence is None or not isinstance(decl.get("text"), str):
        return False
    val = _apply_repairs(v, ef.get("repairs"), sentence)
    if val is None:
        return False
    vt = _toks(val)
    if not all(a.lower() in " ".join(_toks(v)) or a.lower() in v.lower() for a in ef.get("anchors", [])):
        return False
    return bool(vt) and vt == _toks(decl["text"]) == sentence


def match_ordinal_row(row: dict, seg: str, spec: dict) -> dict:
    """{count, direction, effect, <extra column>...} each True / False / 'NULL-ok'. A malformed row is all False."""
    f = spec["fields"]
    g, n, dr, eff = row.get(f["claimant"]), row.get(f["count"]), row.get(f["direction"]), row.get(f["effect"])
    res = dict(count=False, direction=False, effect=False)
    for ef in spec.get("extra_fields", []):
        res[ef["column"]] = False
    if not (isinstance(g, str) and g.strip() and isinstance(n, int) and not isinstance(n, bool) and n > 0
            and isinstance(dr, str) and (eff is None or isinstance(eff, str))):
        return res
    ge = re.escape(g.strip())
    tail = rf"\bthat\s+(?:Adh\.\s+[IVXL]+\s+\S+\s+)?(?:occupied by the\s+|of\s+(?:the\s+)?){ge}\b"
    m = re.search(_ordinal(n) + rf"(?:(?!\b\d+(?:st|nd|rd|th)\b)[^;.]){{0,{_COUNT_REACH}}}?" + tail, seg)
    res["count"] = bool(m)
    words = spec["direction_words"]
    if m and dr in words:
        after = seg[m.end():]
        first, pos = None, None
        for stored, w in words.items():
            x = re.search(rf"\b{re.escape(w)}\b", after)
            if x and (pos is None or x.start() < pos):
                first, pos = stored, x.start()
        res["direction"] = first == dr
    sec = seg
    marker, end = spec.get("effect_marker"), spec.get("effect_end")
    if marker and marker in sec:
        sec = sec[sec.find(marker):]
    if end and end in sec:
        sec = sec[:sec.find(end)]
    if eff is None:
        res["effect"] = False if any(a[0].lower() == g.strip().lower() for a in _anchors(sec, spec["anchor_stems"])) else "NULL-ok"
    else:
        res["effect"] = _effect_matches(eff, g.strip(), sec, spec)
    for ef in spec.get("extra_fields", []):
        res[ef["column"]] = _extra_ok(row, ef, seg, g)
    return res


MATCHER = "ordinal_count_direction_effect_v2"
MATCHERS = {MATCHER: match_ordinal_row}
MATCHER_FIELDS = {MATCHER: ("claimant", "count", "direction", "effect")}
MATCHING_RULE_TEXT = {
    MATCHER:
        "per row, in the declared span of the English translation: the stored count appears as a whole ordinal before 'that of "
        "<claimant>' (no other ordinal between, <=90 characters, no '.' or ';'); the first direction word after it is the stored "
        "direction's declared word; the stored effect EQUALS the claimant's declared effect and the declared clause equals the "
        "claimant's whole passage clause (cut at sentence punctuation and clause-initial capitals) with only the unit anchor and the "
        "declared frame words around the effect (the declared effect may itself drop frame words: the stored effect must equal the "
        "DECLARED effect, not the frame-padded clause; a NULL effect needs NO anchor of the claimant in the effect section); every "
        "declared extra column equals its declared value, or (passage_text) its words after the declared OCR repairs EQUAL the declared "
        "condition, which must equal ONE WHOLE passage sentence: it starts with a declared opener (If/When/Where/Whenever/While/Should) "
        "at a true sentence start (the passage start, or after a stop; a stop the OCR lost is declared as `ocr_lost_stop`: the last "
        "<= 5 words before the start), holds exactly one terminal stop apart from <= 2 declared `ocr_stops` (each followed by a "
        "lower-case letter or digit) and is <= 1.5 x the declared text; per-claimant conditions share the start; each escape hatch "
        "carries evidence and an observed_garble note; repairs are <= 8 plain-text WORD-FOR-WORD maps (equal word counts, each pair "
        ">= 60% alike) whose `to` is a run of the sentence (a real word turned into another real word is NOT detectable: a repair is "
        "a claim the reader checks against the passage); "
        "words are compared after NFKC and lower-casing, ignoring only punctuation and whitespace (non-ASCII letters and combining "
        "marks are NOT ignored or folded); the table holds exactly the declared number of rows and no claimant twice (claimants compared trimmed and case-insensitively)",
}


# ───────────────────────── spec validation ─────────────────────────

def _word_list(v, what, where, pattern=r"[A-Za-z]+"):
    if not (isinstance(v, list) and all(isinstance(x, str) and re.fullmatch(pattern, x) for x in v)):
        raise SpecError(f"{where}.spec.{what} must be a list of words")
    return v


def validate_spec(spec, where: str) -> dict:
    """The spec dict, or SpecError naming the offending field. Pure syntax: it does not look at any database."""
    if not isinstance(spec, dict):
        raise SpecError(f"{where}.spec must be an object")
    allowed = {"matcher", "table", "chunk_ids", "span", "fields", "direction_words", "anchor_stems", "effect_marker", "effect_end",
               "effect_frame_words", "expected_rows", "extra_fields", "effect_clauses", "effect_clauses_evidence"}
    extra = sorted(set(spec) - allowed)
    if extra:
        raise SpecError(f"{where}.spec: unknown field(s) {extra}")
    missing = sorted(k for k in ("matcher", "table", "chunk_ids", "span", "fields", "direction_words", "anchor_stems", "expected_rows",
                                 "effect_marker", "effect_end", "effect_frame_words", "effect_clauses", "effect_clauses_evidence")
                     if k not in spec)
    if missing:
        raise SpecError(f"{where}.spec: missing field(s) {missing}")
    if spec["matcher"] not in MATCHERS:
        raise SpecError(f"{where}.spec.matcher {spec['matcher']!r} is not a known rule engine {sorted(MATCHERS)}")
    if not (isinstance(spec["table"], str) and _IDENT.fullmatch(spec["table"])):
        raise SpecError(f"{where}.spec.table must be a table identifier")
    ids = spec["chunk_ids"]
    if not (isinstance(ids, list) and ids and all(isinstance(i, str) and _CHUNK_ID.fullmatch(i) for i in ids) and len(set(ids)) == len(ids)):
        raise SpecError(f"{where}.spec.chunk_ids must be a non-empty list of distinct chunk ids (page order)")
    sp = spec["span"]
    if not (isinstance(sp, dict) and set(sp) <= {"start", "end"} and isinstance(sp.get("start"), str) and sp["start"].strip()
            and len(sp["start"]) <= MARKER_MAX and (sp.get("end") is None or (isinstance(sp["end"], str) and sp["end"].strip()
                                                                              and len(sp["end"]) <= MARKER_MAX))):
        raise SpecError(f"{where}.spec.span must be {{start, end?}} with non-blank marker strings (<= {MARKER_MAX} chars)")
    want = MATCHER_FIELDS[spec["matcher"]]
    fl = spec["fields"]
    if not (isinstance(fl, dict) and set(fl) == set(want) and all(isinstance(v, str) and _IDENT.fullmatch(v) for v in fl.values())):
        raise SpecError(f"{where}.spec.fields must map exactly {list(want)} to column identifiers")
    dw = spec["direction_words"]
    if not (isinstance(dw, dict) and dw and all(isinstance(k, str) and k and isinstance(v, str) and re.fullmatch(r"[A-Za-z]+", v)
                                               for k, v in dw.items())):
        raise SpecError(f"{where}.spec.direction_words must map each stored direction value to one word")
    st = spec["anchor_stems"]
    if not (isinstance(st, list) and st and all(isinstance(s, str) and _STEM.fullmatch(s) for s in st)):
        raise SpecError(f"{where}.spec.anchor_stems must be a non-empty list of word stems (letters only)")
    for k in ("effect_marker", "effect_end"):
        v = spec.get(k)
        if not (isinstance(v, str) and v.strip() and len(v) <= MARKER_MAX):
            raise SpecError(f"{where}.spec.{k} is REQUIRED and must be a non-blank string: an effect section without both markers would widen")
    _word_list(spec["effect_frame_words"], "effect_frame_words", where)
    ec = spec["effect_clauses"]
    if not (isinstance(ec, dict) and all(isinstance(k, str) and k.strip() and isinstance(v, dict) and set(v) == {"clause", "effect"}
                                         and all(isinstance(v[x], str) and v[x].strip() for x in ("clause", "effect")) for k, v in ec.items())):
        raise SpecError(f"{where}.spec.effect_clauses must map each claimant to {{clause, effect}} (non-blank strings)")
    if len({k.strip().lower() for k in ec}) != len(ec):
        raise SpecError(f"{where}.spec.effect_clauses names a claimant twice")
    if not (isinstance(spec["effect_clauses_evidence"], str) and spec["effect_clauses_evidence"].strip()):
        raise SpecError(f"{where}.spec.effect_clauses_evidence must name the document the clause mapping was read from")
    er = spec["expected_rows"]
    if not (isinstance(er, int) and not isinstance(er, bool) and er >= 1):
        raise SpecError(f"{where}.spec.expected_rows must be a positive integer (the number of rows the table must hold)")
    efs = spec.get("extra_fields", [])
    if not isinstance(efs, list):
        raise SpecError(f"{where}.spec.extra_fields must be a list")
    cols = set(fl.values())
    for ef in efs:
        if not (isinstance(ef, dict) and isinstance(ef.get("column"), str) and _IDENT.fullmatch(ef["column"]) and ef["column"] not in cols
                and ef.get("kind") in ("equals", "passage_text")):
            raise SpecError(f"{where}.spec.extra_fields entries need a new column identifier and kind equals|passage_text")
        cols.add(ef["column"])
        if ef["kind"] == "equals":
            if set(ef) != {"column", "kind", "value"} or not (isinstance(ef["value"], str) and ef["value"].strip()):
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}]: equals needs exactly {{column, kind, value}}")
        else:
            if not set(ef) <= {"column", "kind", "anchors", "repairs", "condition", "by_claimant", "condition_evidence",
                                  "sentence_openers"}:
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}]: passage_text takes only column, kind, condition, "
                                "condition_evidence, sentence_openers, by_claimant, anchors, repairs")
            if "anchors" in ef and not (isinstance(ef["anchors"], list) and ef["anchors"]
                                        and all(isinstance(a, str) and a.strip() for a in ef["anchors"])):
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}].anchors must be a non-empty list of non-blank strings")
            so = ef.get("sentence_openers")
            if not (isinstance(so, list) and so and len(set(so)) == len(so) and all(x in ALLOWED_OPENERS for x in so)):
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}].sentence_openers is REQUIRED: a non-empty list from "
                                f"{list(ALLOWED_OPENERS)} (the first word of the condition start must be one of them)")
            _decl_ok = lambda d: (isinstance(d, dict) and {"text", "start", "end"} <= set(d) <= {"text", "start", "end", "ocr_lost_stop", "ocr_stops"}
                                  and all(isinstance(d[x], str) and d[x].strip() and len(d[x]) <= MARKER_MAX * 4 for x in ("text", "start", "end"))
                                  and re.match(r"[A-Za-z]+", d["start"]) is not None and re.match(r"[A-Za-z]+", d["start"]).group(0) in so
                                  and ("ocr_lost_stop" not in d or (_hatch_ok(d["ocr_lost_stop"])
                                                                    and 1 <= len(d["ocr_lost_stop"]["text"].split()) <= LOST_STOP_MAX_WORDS))
                                  and ("ocr_stops" not in d or (isinstance(d["ocr_stops"], list) and len(d["ocr_stops"]) <= MAX_OCR_STOPS
                                                                and all(_hatch_ok(s) and s["text"][-1] in ".;?!" for s in d["ocr_stops"]))))
            if not _decl_ok(ef.get("condition")):
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}]: passage_text REQUIRES a declared `condition` "
                                "{text, start, end[, ocr_lost_stop, ocr_stops]}: the whole passage sentence the stored value must equal "
                                f"(start opens with one of {so}; <= {MAX_OCR_STOPS} ocr_stops and an optional ocr_lost_stop, each "
                                "{text, evidence, observed_garble})")
            bc = ef.get("by_claimant", {})
            if not (isinstance(bc, dict) and all(isinstance(k, str) and k.strip() and _decl_ok(v) for k, v in bc.items())
                    and len({k.strip().lower() for k in bc}) == len(bc)):
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}].by_claimant must map each claimant (once) to {{text, start, end}}")
            if len(bc) > er:
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}].by_claimant names {len(bc)} claimants but the table holds {er}")
            for k, v in bc.items():
                if v["start"] != ef["condition"]["start"] or _lost_text(v) != _lost_text(ef["condition"]):
                    raise SpecError(f"{where}.spec.extra_fields[{ef['column']}].by_claimant[{k}] must share the shared condition's start and "
                                    "ocr_lost_stop text: it may only declare a sub-clause of the SAME sentence")
            if not (isinstance(ef.get("condition_evidence"), str) and ef["condition_evidence"].strip()):
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}].condition_evidence must name the document the condition was read from")
            rp = ef.get("repairs", [])
            if not (isinstance(rp, list) and len(rp) <= MAX_REPAIRS):
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}].repairs must be a list of at most {MAX_REPAIRS} {{from, to, evidence}}")
            for x in rp:
                if not (isinstance(x, dict) and set(x) == {"from", "to", "evidence"}
                        and all(isinstance(x[k], str) and x[k].strip() for k in ("from", "to", "evidence"))
                        and len(x["from"]) <= REPAIR_MAX and len(x["to"]) <= REPAIR_MAX):
                    raise SpecError(f"{where}.spec.extra_fields[{ef['column']}].repairs entries are {{from, to, evidence}} (non-blank, "
                                    f"from/to <= {REPAIR_MAX} characters, evidence required)")
                fw, tw = x["from"].split(), x["to"].split()
                alike = lambda a, b: difflib.SequenceMatcher(None, "".join(_toks(a)), "".join(_toks(b))).ratio()
                if len(fw) != len(tw) or alike(x["from"], x["to"]) < 1 - REPAIR_MAX_DIFF or any(alike(a, b) < REPAIR_MIN_SIMILARITY
                                                                                                 for a, b in zip(fw, tw)):
                    raise SpecError(f"{where}.spec.extra_fields[{ef['column']}].repairs {x['from']!r} -> {x['to']!r}: an OCR repair maps a "
                                    f"garbled word to its clean form WORD FOR WORD (equal word counts, each pair and the whole >= "
                                    f"{1 - REPAIR_MAX_DIFF:.0%} alike): it cannot add, drop or substitute words")
    return spec


def spec_columns(spec: dict) -> list:
    """The columns a D1 read must select: the claim fields and the declared extra columns."""
    return list(dict.fromkeys(list(spec["fields"].values()) + [ef["column"] for ef in spec.get("extra_fields", [])]))


def prose_coverage(spec: dict) -> dict:
    """{column: the key of that column's per-row result in `match_ordinal_row`} for every column the spec matches against PASSAGE TEXT: the effect column
    (result key `effect`: each stored effect must equal its declared clause's effect, or be NULL where the passage gives none) and every `passage_text`
    extra field (result key = the column). NOT in it: the claim fields (claimant / count / direction: structural values) and `equals` extras (a constant,
    not a restatement of a passage clause). DERIVED from the spec, never declared: NARR-GUARD (N-94) reads it to say which text columns Carr.D1 really covers.
    Raises KeyError / TypeError / AttributeError on a spec that is not shaped as validate_spec requires."""
    cov = {spec["fields"]["effect"]: "effect"}
    for ef in spec.get("extra_fields", []):
        if ef["kind"] == "passage_text":
            cov[ef["column"]] = ef["column"]
    return cov


# ───────────────────────── the measurement ─────────────────────────

def _claims(citation_state, content_sa_all_null: bool, n_chunks: int, preimages_used: list) -> str:
    return ("D1 matches the ENGLISH translation (content_en) only"
            + (f"; the Sanskrit column (content_sa) is NULL for all {n_chunks} declared chunk(s) and is not matched" if content_sa_all_null
               else "; content_sa is present on some chunk(s) and is NOT matched")
            + f"; the passages are OCR text not checked against the printed book (citation_state: {citation_state})"
            + f"; the stored chunk hashes were verified with the {' and '.join(sorted(set(preimages_used))) or 'no'} preimage"
            + " (text_id-prefixed sha256(utf8(text_id + '::' + content_en)) is the bg_texts.py convention)")


def d1_measure(spec: dict, citation_state, chunks_by_id: dict, rows, table) -> dict:
    """The Carr.D1 measurement record for a declared D1 asset.

    `chunks_by_id` {chunk_id: {chunk_id, text_id, content_en, content_sa, content_sha256}} as fetched; `rows` the asset's table rows
    (list of dicts) or None when they could not be read; `table` the asset's registry target table (None when it has none). The
    caller has validated `spec` (validate_spec). Returns {v, measured, d1: {...structured...}, citation_state}."""
    base = dict(matcher=spec["matcher"], matching_rule=MATCHING_RULE_TEXT[spec["matcher"]], span=dict(spec["span"]),
                chunk_ids=list(spec["chunk_ids"]), translation_only=True, expected_rows=spec["expected_rows"], reads=list(READS))

    def out(v, text, **extra):
        return dict(v=v, measured=text, citation_state=citation_state, d1=dict(base, **extra))

    if table != spec["table"]:
        return out(NO_DET, f"NO_DETECTOR: the spec names table {spec['table']!r} but the asset's registry target table is "
                           f"{table!r}: D1 does not guess (an asset with no table is never measured against a spec's table)", chunks=[])
    verified, missing = [], []
    for cid in spec["chunk_ids"]:
        c = chunks_by_id.get(cid) if isinstance(chunks_by_id, dict) else None
        if c is None:
            missing.append(cid)
            continue
        verified.append((c, verify_chunk(dict(c, chunk_id=cid))))
    ledger = [v for _c, v in verified]
    if missing:
        return out(NO_DET, f"NO_DETECTOR: declared chunk(s) not found in classical_text_chunks: {', '.join(missing)}",
                   chunks=ledger, missing_chunks=missing)
    bad = [v for v in ledger if not v["verified"]]
    if bad:
        return out(NO_DET, "NO_DETECTOR: unreadable passage(s) for D1: " + "; ".join(f"{v['chunk_id']}: {v['reason']}" for v in bad),
                   chunks=ledger)
    joined = _ws(" ".join(c["content_en"] for c, _v in verified))
    all_sa_null = all(v["content_sa_null"] for v in ledger)
    claims = _claims(citation_state, all_sa_null, len(ledger), [v["preimage"] for v in ledger])
    ev = dict(chunks=ledger, chunks_sha256=chunks_digest(ledger), claims=claims, content_sa_all_null=all_sa_null)
    seg, why = cut_span(joined, spec["span"])
    if seg is None:
        return out(NO_DET, f"NO_DETECTOR: {why}", **ev)
    ev["passage_sha256"] = span_digest(seg)
    ev["passage"] = seg                      # the cut span itself, so the digest can be recomputed from the record
    for key in ("effect_marker", "effect_end"):
        mk = spec.get(key)
        if not mk or mk not in seg:
            return out(NO_DET, f"NO_DETECTOR: the {key} {mk!r} is undeclared or absent from the declared span: the effect section cannot be "
                               "bounded, and D1 does not widen it", **ev)
    if not isinstance(rows, list):
        return out(NO_DET, "NO_DETECTOR: the asset's table rows could not be read", **ev)
    if not rows:
        return out(NO_DET, f"NO_DETECTOR: table {spec['table']} is empty: there is no row to match the passage against", **ev)
    fn = MATCHERS[spec["matcher"]]
    keyf = spec["fields"]["claimant"]
    keys = [(r.get(keyf).strip().lower() if isinstance(r, dict) and isinstance(r.get(keyf), str) else None) for r in rows]
    dup = {k for k in keys if k is not None and keys.count(k) > 1}
    results, unmatched = [], []
    for i, r in enumerate(rows):
        try:
            res = fn(r if isinstance(r, dict) else {}, seg, spec)
            failed = [k for k, v in res.items() if v not in (True, "NULL-ok")]
        except SpecError as exc:               # a spec fault met at match time is a named miss on this row; any other exception is a real bug and propagates
            res, failed = dict(error=f"{type(exc).__name__}"), [f"error:{type(exc).__name__}"]
        if keys[i] in dup:
            failed.append("duplicate")
        label = ((r.get(keyf).strip() if isinstance(r.get(keyf), str) else None) if isinstance(r, dict) else None) or f"row {i}"
        results.append(dict(row=label, result=res, matched=not failed))
        if failed:
            unmatched.append(dict(row=label, failed=failed))
    count_ok = len(rows) == spec["expected_rows"]
    ev.update(rows_total=len(rows), rows_matched=len(rows) - len(unmatched), unmatched=unmatched, rows=results, row_count_ok=count_ok)
    if citation_state not in CITATION_STATES or citation_state in CITATION_CAPPED_STATES:
        return out(NO_DET, f"NO_DETECTOR: {len(rows) - len(unmatched)} of {len(rows)} row(s) matched the declared passage, but the "
                           f"citation_state is {citation_state!r}: anchor matching cannot tell a contradicted source from one not "
                           f"found, so the match is not evidence. {claims}", **ev)
    if not unmatched and count_ok:
        return out(PASS_V, f"D1 PASS (citation_state {citation_state}): every one of the {len(rows)} row(s) of {spec['table']} (the "
                           f"{spec['expected_rows']} declared) is found in the declared passage ({', '.join(spec['chunk_ids'])}, from "
                           f"{spec['span']['start']!r}) under rule {spec['matcher']}. {claims}", pass_basis=citation_state, **ev)
    parts = []
    if unmatched:
        parts.append("NOT found: " + ", ".join(f"{u['row']} ({'/'.join(u['failed'])})" for u in unmatched))
    if not count_ok:
        parts.append(f"the table holds {len(rows)} row(s) but {spec['expected_rows']} are declared")
    return out("PARTIAL", f"D1 PARTIAL: {len(rows) - len(unmatched)} of {len(rows)} row(s) found in the declared passage; "
                          f"{'; '.join(parts)}. {claims}", **ev)

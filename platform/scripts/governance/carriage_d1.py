"""carriage_d1.py: the generic D1 (source correspondence) engine for the Carr gate (SS N-72 S2, N-73 (2): for an asset that
TRANSCRIBES classical content the applicable carriage check is D1, a match to a cited source; D3 is for computed assets).

Pure functions. No database, no network, no clock: asset_census.py passes in the fetched passages and the asset's rows, so
every case is testable from fixtures. An asset DECLARES its D1 in asset_declarations.json (`carriage.applies = "D1"` plus a
`carriage.spec`); an asset without a spec is never measured here.

KERNELS (C1-1, N-101): the matching rules are a CLOSED registry, `KERNELS`; a spec names one by `matcher`, an unknown id is refused, and each kernel states
its own required / optional spec fields (an unknown field is refused). `ordinal_count_direction_effect_v2` (the latta's rule) is the first kernel; its required
fields are exactly the ones below, so its declaration validates by the same code path as before. The HARNESS around a kernel (chunk ledger, span cut, row loop,
expected_rows, duplicate keys, citation caps, evidence block, `claims`) is shared. Two harness guards apply to every kernel: `row_scope` (rows outside a declared,
closed predicate are COUNTED and cap the verdict at PARTIAL) and the COLUMN LEDGER (every text-like column of the table is matched, a declared constant, a declared
non-claim or an asset prose field, else it is listed and the verdict cannot read PASS). Both add record keys ONLY when they have something to say: `row_scope` when declared; `column_ledger` only when it names an unclassified or absent column
(a clean ledger leaves the record byte-identical).

THE SPEC (validated by `validate_spec`, read by `d1_measure`):
  matcher          the id of a kernel in KERNELS (a STATED matching rule; `ordinal_count_direction_effect_v2` first)
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
  row_scope        optional (harness): a list of 1..4 closed conditions ANDed, {column, equals: v} | {column, in: [v, ...]} | {column, not_null: true}; no SQL
  non_claim_columns  optional (harness): [{column, why, evidence}] text columns the asset declares it makes NO claim about (a key, a provenance label), each with a real one-line
                   `why` and an `evidence` pointer (existence is checked by the census validator); read by the column ledger
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

import copy
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
RESULT_KEYS = frozenset({"count", "direction", "effect"})     # the per-row result keys match_ordinal_row sets for the claim fields; an extra field may not reuse one
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


HARNESS_REQUIRED = ("matcher", "table", "chunk_ids", "span", "expected_rows")     # every kernel's spec carries these
HARNESS_OPTIONAL = ("row_scope", "non_claim_columns")                                # the two harness guards: declared per asset, valid for every kernel


def _kernel(name):
    """The kernel registered under `name`, or None. The ONE lookup of the closed registry (a non-string id is never a kernel)."""
    return KERNELS.get(name) if isinstance(name, str) else None


def _spec_field_problem(spec: dict, where: str):
    """None, or why the spec's FIELD SET is refused: a field neither the harness's nor the named kernel's (an unknown field), or a required field
    absent. With an unknown kernel id the allowed set is the union over the registry (the id itself is refused next)."""
    k = _kernel(spec.get("matcher"))
    allowed = set(HARNESS_REQUIRED) | set(HARNESS_OPTIONAL)
    required = set(HARNESS_REQUIRED)
    for kern in ([k] if k else list(KERNELS.values())):
        allowed |= set(kern.get("spec_required", ())) | set(kern.get("spec_optional", ()))
    if k:
        required |= set(k.get("spec_required", ()))
    extra = sorted(set(spec) - allowed)
    if extra:
        return f"{where}.spec: unknown field(s) {extra}"
    if k:
        missing = sorted(required - set(spec))
        if missing:
            return f"{where}.spec: missing field(s) {missing}"
    return None


def _expected_rows_problem(spec: dict, where: str):
    er = spec["expected_rows"]
    if not (isinstance(er, int) and not isinstance(er, bool) and er >= 1):
        return f"{where}.spec.expected_rows must be a positive integer (the number of rows the table must hold)"
    return None


def validate_spec(spec, where: str) -> dict:
    """The spec dict, or SpecError naming the offending field. Pure syntax: it does not look at any database. The harness fields are checked here, the
    kernel's own by its `validate`, then the two optional harness guards (row_scope, non_claim_columns)."""
    if not isinstance(spec, dict):
        raise SpecError(f"{where}.spec must be an object")
    bad = _spec_field_problem(spec, where)
    if bad and not _kernel(spec.get("matcher")):          # unknown fields are reported before an unknown kernel id, as they always were
        raise SpecError(bad)
    if not _kernel(spec.get("matcher")):
        missing = sorted(k for k in HARNESS_REQUIRED if k not in spec)
        if missing:
            raise SpecError(f"{where}.spec: missing field(s) {missing}")
        raise SpecError(f"{where}.spec.matcher {spec['matcher']!r} is not a known rule engine (a kernel of the closed registry KERNELS) {sorted(KERNELS)}")
    if bad:
        raise SpecError(bad)
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
    _kernel_of(spec)["validate"](spec, where)
    bad = _expected_rows_problem(spec, where)
    if bad:
        raise SpecError(bad)
    _validate_row_scope(spec, where)
    _validate_non_claim_columns(spec, where)
    return spec


def _validate_ordinal_v2(spec: dict, where: str) -> None:
    """The ordinal_count_direction_effect_v2 kernel's own spec validation (the latta's: the checks that used to follow the harness ones in validate_spec)."""
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
    bad = _expected_rows_problem(spec, where)
    if bad:
        raise SpecError(bad)
    er = spec["expected_rows"]
    efs = spec.get("extra_fields", [])
    if not isinstance(efs, list):
        raise SpecError(f"{where}.spec.extra_fields must be a list")
    cols = set(fl.values())
    for ef in efs:
        if isinstance(ef, dict) and isinstance(ef.get("column"), str) and ef["column"] in RESULT_KEYS:    # a non-string column is refused just below, never an unhashable crash
            raise SpecError(f"{where}.spec.extra_fields[{ef['column']}]: the column name collides with a result key of the matcher {sorted(RESULT_KEYS)} "
                            "(its per-row result would overwrite that check's result, so the check would no longer be graded): rename the extra field")
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


def spec_columns(spec: dict) -> list:
    """The columns a D1 read must select: the claim fields, the declared extra columns and the row_scope columns (a scope can only be evaluated on a column that was read)."""
    return list(dict.fromkeys(_kernel_of(spec)["columns"](spec) + [c["column"] for c in spec.get("row_scope") or []]))


def _kernel_of(spec) -> dict:
    """The kernel a spec names, or SpecError (never a KeyError / TypeError from a spec that names no kernel, an unknown one or is not an object): the ONE lookup the generic
    functions (spec_columns, d1_measure, the ledger) use, so a kernel that lacks a hook is a refusal, not a crash."""
    k = _kernel(spec.get("matcher")) if isinstance(spec, dict) else None
    if k is None:
        raise SpecError(f"matcher {spec.get('matcher') if isinstance(spec, dict) else None!r} is not a kernel of the closed registry KERNELS {sorted(KERNELS)}")
    missing = sorted(h for h in KERNEL_HOOKS if h not in k)
    if missing:
        raise SpecError(f"kernel {spec['matcher']!r} lacks the required hook(s) {missing}")
    return k


def _ordinal_prose_coverage(spec: dict) -> dict:
    cov = {spec["fields"]["effect"]: "effect"}
    for ef in spec.get("extra_fields", []):
        if isinstance(ef["column"], str) and ef["column"] in RESULT_KEYS:
            raise SpecError(f"extra field {ef['column']!r} collides with a matcher result key {sorted(RESULT_KEYS)}")
        if ef["kind"] == "passage_text":
            cov[ef["column"]] = ef["column"]
    return cov


def prose_coverage(spec: dict) -> dict:
    """{column: the key of that column's per-row result in the kernel's row function} for every column the spec matches against PASSAGE TEXT: for the latta kernel
    the effect column (result key `effect`: each stored effect must equal its declared clause's effect, or be NULL where the passage gives none) and every `passage_text`
    extra field (result key = the column). NOT in it: the claim fields (claimant / count / direction: structural values) and `equals` extras (a constant,
    not a restatement of a passage clause). DERIVED from the spec by the named kernel's `coverage`, never declared: NARR-GUARD (N-94) reads it to say which text columns
    Carr.D1 really covers (a kernel without a coverage function cannot support a prose coupling).
    Raises KeyError / TypeError / AttributeError on a spec that is not shaped as validate_spec requires (an unknown kernel id is a KeyError), and SpecError when an extra
    field's column collides with a matcher result key (`effect` / `count` / `direction`: its result would overwrite that check's, so coverage could not be told from
    what D1 grades)."""
    return _kernel_of(spec)["coverage"](spec)


# ───────────────────────── harness guard 1: row_scope ─────────────────────────
# A table may hold rows the declared passage says nothing about (a shared table, an editorial extension). `row_scope` declares which rows the claim is about, as a CLOSED
# predicate: no SQL, no regex, no arithmetic; it is evaluated in Python over the rows D1 already reads (the scope columns are read with them). Rows outside it are never
# ignored: they are COUNTED (`out_of_scope_rows`, with a sample of labels) and any one of them caps the verdict at PARTIAL, naming the count (L0 Q13: PASS only if every row matches).

SCOPE_OPS = ("equals", "in", "not_null")
MAX_SCOPE_CONDITIONS = 4
MAX_SCOPE_VALUES = 16
MAX_OUT_OF_SCOPE_SAMPLE = 20
SCOPE_CONSTANT_OPS = ("equals", "in")          # a column the scope pins to declared values is a DECLARED CONSTANT for the column ledger; not_null pins nothing


def _scope_value_ok(v) -> bool:
    return (isinstance(v, str) and v != "") or (isinstance(v, int) and not isinstance(v, bool))


def _validate_row_scope(spec: dict, where: str) -> None:
    if "row_scope" not in spec:
        return
    rs, w = spec["row_scope"], f"{where}.spec.row_scope"
    if not (isinstance(rs, list) and 1 <= len(rs) <= MAX_SCOPE_CONDITIONS):
        raise SpecError(f"{w} must be a list of 1..{MAX_SCOPE_CONDITIONS} conditions (ANDed)")
    seen = set()
    for c in rs:
        if not (isinstance(c, dict) and isinstance(c.get("column"), str) and _IDENT.fullmatch(c["column"])):
            raise SpecError(f"{w} conditions are objects with a `column` identifier")
        col = c["column"]
        ops = sorted(k for k in c if k != "column")
        if len(ops) != 1 or ops[0] not in SCOPE_OPS:
            raise SpecError(f"{w}[{col}] needs `column` and exactly one of {list(SCOPE_OPS)} (a closed predicate: no SQL, no other operator), got {ops}")
        if col in seen:
            raise SpecError(f"{w}: column {col!r} appears in two conditions (one condition per column)")
        seen.add(col)
        op, val = ops[0], c[ops[0]]
        if op == "equals" and not _scope_value_ok(val):
            raise SpecError(f"{w}[{col}].equals must be a non-empty string or an integer")
        if op == "in" and not (isinstance(val, list) and 1 <= len(val) <= MAX_SCOPE_VALUES and all(_scope_value_ok(v) for v in val)
                               and len({(type(v).__name__, v) for v in val}) == len(val)):
            raise SpecError(f"{w}[{col}].in must be a list of 1..{MAX_SCOPE_VALUES} distinct non-empty strings or integers")
        if op == "not_null" and val is not True:
            raise SpecError(f"{w}[{col}].not_null must be true")


def _scope_same(v, want) -> bool:
    if isinstance(want, str):
        return isinstance(v, str) and v == want
    return isinstance(v, int) and not isinstance(v, bool) and v == want


def row_in_scope(row, scope) -> bool:
    """True when `row` satisfies every condition of the (validated) scope. A row that is not a dict, or lacks / holds NULL in a scope column, is outside it."""
    if not isinstance(row, dict):
        return False
    for c in scope:
        v = row.get(c["column"])
        if "equals" in c:
            ok = _scope_same(v, c["equals"])
        elif "in" in c:
            ok = any(_scope_same(v, w) for w in c["in"])
        else:
            ok = v is not None
        if not ok:
            return False
    return True


def partition_rows(rows: list, scope):
    """([(index, row)] in scope, [(index, row)] outside it). No scope declared = every row is in scope (the behaviour before C1-1)."""
    if not scope:
        return list(enumerate(rows)), []
    inside, outside = [], []
    for i, r in enumerate(rows):
        (inside if row_in_scope(r, scope) else outside).append((i, r))
    return inside, outside


def scope_cap_problem(n_out_of_scope: int):
    """None when every read row is inside the declared scope, else the PARTIAL cap's reason, naming the count."""
    if n_out_of_scope:
        return (f"{n_out_of_scope} row(s) lie outside the declared row_scope: they are counted, not matched, and a table holding rows the claim "
                "does not cover is never a PASS")
    return None


# ───────────────────────── harness guard 2: the column ledger ─────────────────────────
# Each text-like column of the table belongs to exactly ONE gate: it is MATCHED by the kernel (carriage), a declared CONSTANT (an `equals` extra, or a column the row_scope pins),
# a declared NON-CLAIM (`non_claim_columns`: a key, a provenance label, with its reason) or an asset PROSE field (Narr's). Any other text-like column is `uncovered`: the record
# lists it and D1 cannot read PASS (PARTIAL), so a table that carries text D1 never looked at is not "source-corresponded". The ledger runs only when the caller supplies the
# table's column facts (`ledger=` of d1_measure; the census ALWAYS supplies them for a declared D1 carriage, there is no switch). The record carries a `column_ledger` block only when
# the ledger names something (uncovered / declared_absent / unexamined), so a clean record is byte-identical to one written before the ledger existed; a PASS record cannot carry a
# non-clean block (d1_evidence_problem). Residual: a PASS record carrying NO block cannot itself prove the ledger ran (that would add a key to every clean record): the guarantee is
# that the census requires the column facts of every declared D1 carriage (carriage_declared_checks has no default for them) and d1_measure refuses to PASS past a non-clean ledger.

# Column types come from pg_catalog (`asset_census.pg_column_type_facts`: ONE read that resolves a domain to its base type and an array to its element), as facts
# {t: base type name, c: its typcategory, ec: the element's typcategory for an array, et: the element's type name}. information_schema.data_type is NOT used: it reports
# USER-DEFINED for an enum, a domain over citext, citext and the like, which would hide a text column from the ledger.
_TEXT_TYPNAMES = ("json", "jsonb", "xml", "tsvector", "tsquery", "char")            # text-bearing types outside typcategory S / E (`"char"` is category Z)
_NON_TEXT_TYPNAMES = ("uuid", "bytea", "oid", "money", "vector", "halfvec", "sparsevec", "bit", "varbit", "interval")
_NON_TEXT_CATEGORIES = ("N", "B", "D", "T", "I", "G", "V")                           # numeric, boolean, date/time, timespan, network, geometric, bit string
NON_CLAIM_WHY_MIN_CHARS = 15
NON_CLAIM_WHY_MAX_CHARS = 400
MAX_NON_CLAIM_COLUMNS = 16


def _scalar_type_class(t, c) -> str:
    if t in _TEXT_TYPNAMES or c in ("S", "E"):                  # string (text, varchar, bpchar, name, citext) and enum categories carry text
        return "text"
    if c in _NON_TEXT_CATEGORIES or t in _NON_TEXT_TYPNAMES:
        return "nontext"
    return "unknown"


def column_type_class(fact) -> str:
    """'text' | 'nontext' | 'unknown' for a column's pg_catalog fact {t, c, ec, et} (see above). TEXT-LIKE (must be classified): the string and enum categories (text, varchar,
    bpchar, name, citext, user enums, a domain over any of them), json, jsonb, xml, tsvector, tsquery and `"char"`, and an array whose ELEMENT is text-like. NON-TEXT: numeric, boolean,
    date/time, timespan, network, geometric, bit-string, uuid, bytea, embedding vectors, and an array of one of them (`integer[]` is not text). UNKNOWN (a composite, a range, an
    extension type the ledger has no rule for, a fact that is not a dict): never silently ignored: it caps the verdict (`unexamined`) unless the column is classified otherwise."""
    if not isinstance(fact, dict):
        return "unknown"
    if fact.get("c") == "A":
        return _scalar_type_class(fact.get("et"), fact.get("ec")) if fact.get("et") is not None else "unknown"
    return _scalar_type_class(fact.get("t"), fact.get("c"))


def _validate_non_claim_columns(spec: dict, where: str) -> None:
    if "non_claim_columns" not in spec:
        return
    nc, w = spec["non_claim_columns"], f"{where}.spec.non_claim_columns"
    if not (isinstance(nc, list) and 1 <= len(nc) <= MAX_NON_CLAIM_COLUMNS):
        raise SpecError(f"{w} must be a list of 1..{MAX_NON_CLAIM_COLUMNS} {{column, why, evidence}} entries")
    taken = set(_kernel_of(spec)["matched_columns"](spec)) | set(_constant_columns(spec))
    seen = set()
    for x in nc:
        if not (isinstance(x, dict) and set(x) == {"column", "why", "evidence"} and isinstance(x["column"], str) and _IDENT.fullmatch(x["column"])):
            raise SpecError(f"{w} entries are {{column, why, evidence}} with a column identifier")
        r = x["why"]
        if not (isinstance(r, str) and "\n" not in r and NON_CLAIM_WHY_MIN_CHARS <= len(r.strip()) and len(r) <= NON_CLAIM_WHY_MAX_CHARS and len(r.split()) >= 3):
            raise SpecError(f"{w}[{x['column']}].why must be a real one-line reason ({NON_CLAIM_WHY_MIN_CHARS}..{NON_CLAIM_WHY_MAX_CHARS} characters, at least 3 words)")
        if not (isinstance(x["evidence"], str) and x["evidence"].strip() and "\n" not in x["evidence"]):
            raise SpecError(f"{w}[{x['column']}].evidence must be a non-blank one-line pointer (file:line) to what was read")
        if x["column"] in seen:
            raise SpecError(f"{w} names column {x['column']!r} twice")
        if x["column"] in taken:
            raise SpecError(f"{w}[{x['column']}]: the column is already matched or declared constant by this spec: a column is classified once")
        seen.add(x["column"])


def _constant_columns(spec: dict) -> list:
    """Columns the spec pins to a declared constant: the `equals` extras ONLY. A column a row_scope equals / in condition pins is NOT credited here: a scope selects which rows
    the claim is about, it carries no `why` and no evidence, and up to 16 pinned values are never compared to the passage; such a column needs its own non-claim (or constant) entry."""
    return list(dict.fromkeys(ef["column"] for ef in spec.get("extra_fields", []) if isinstance(ef, dict) and ef.get("kind") == "equals"))


def column_ledger(spec: dict, column_types, prose_columns=()) -> dict:
    """The column ledger of a D1 spec over a table's column facts ({column: {t, c, ec, et}} from pg_catalog); pure. {evaluated, text_columns, matched, constants, non_claims,
    prose, uncovered, declared_absent, unexamined}: `uncovered` = text-like columns in none of the four classes; `declared_absent` = a matched / constant / non-claim column the
    spec names that the table does not have (a stale declaration: the declaration and the table disagree); `unexamined` = columns of a type the ledger has no rule for that are
    not classified otherwise (they cap the verdict like an uncovered column: a column nobody can class is not a column nobody looked at)."""
    types = {c: t for c, t in dict(column_types).items() if isinstance(c, str)}
    cls = {c: column_type_class(t) for c, t in types.items()}
    text_cols = sorted(c for c, k in cls.items() if k == "text")
    matched = set(_kernel_of(spec)["matched_columns"](spec))
    consts = set(_constant_columns(spec))
    nonclaim = {x["column"]: x["why"] for x in spec.get("non_claim_columns", [])}
    prose = {c for c in (prose_columns or ()) if isinstance(c, str)}
    covered = matched | consts | set(nonclaim) | prose
    return dict(evaluated=True, text_columns=text_cols,
                matched=sorted(c for c in text_cols if c in matched), constants=sorted(c for c in text_cols if c in consts),
                non_claims=[dict(column=c, why=nonclaim[c]) for c in sorted(nonclaim) if c in text_cols],
                prose=sorted(c for c in text_cols if c in prose),
                uncovered=[c for c in text_cols if c not in covered],
                declared_absent=sorted(c for c in (matched | consts | set(nonclaim)) if c not in types),
                unexamined=sorted(c for c, k in cls.items() if k == "unknown" and c not in covered))


def ledger_block_is_clean(block) -> bool:
    """True only for a ledger block that ran and names nothing: evaluated, no uncovered, no declared_absent, no unexamined column."""
    return (isinstance(block, dict) and block.get("evaluated") is True and block.get("uncovered") == [] and block.get("declared_absent") == []
            and block.get("unexamined") == [])


def ledger_cap_problem(block):
    """None when the column ledger is clean (or was not requested: `block` is None), else the PARTIAL cap's reason, naming the columns."""
    if not isinstance(block, dict):
        return None
    parts = []
    if block.get("uncovered"):
        parts.append(f"text column(s) {', '.join(block['uncovered'])} are neither matched, a declared constant, a declared non-claim nor a prose field")
    if block.get("unexamined"):
        parts.append(f"column(s) {', '.join(block['unexamined'])} have a type the ledger cannot class (neither text nor a known non-text type) and are not classified otherwise")
    if block.get("declared_absent"):
        parts.append(f"the spec names column(s) {', '.join(block['declared_absent'])} that the table does not have")
    return ("column ledger: " + "; ".join(parts) + " (a table that carries text D1 never classified is not a PASS)") if parts else None


# ───────────────────────── the kernel registry (closed) ─────────────────────────

def _ordinal_matched_columns(spec: dict) -> list:
    """Every column the latta kernel compares against the passage or the declared claim: the four claim fields and the `passage_text` extras (its `equals` extras are constants)."""
    return list(dict.fromkeys(list(spec["fields"].values()) + [ef["column"] for ef in spec.get("extra_fields", []) if ef.get("kind") == "passage_text"]))


def _ordinal_span_check(spec: dict, seg: str):
    """None, or the NO_DETECTOR text: the effect section's two markers must be declared and present in the cut span (an unbounded effect section would widen)."""
    for key in ("effect_marker", "effect_end"):
        mk = spec.get(key)
        if not mk or mk not in seg:
            return (f"NO_DETECTOR: the {key} {mk!r} is undeclared or absent from the declared span: the effect section cannot be "
                    "bounded, and D1 does not widen it")
    return None


def _ordinal_columns(spec: dict) -> list:
    """The columns the latta kernel reads: the claim fields and the declared extra columns."""
    return list(dict.fromkeys(list(spec["fields"].values()) + [ef["column"] for ef in spec.get("extra_fields", [])]))


def _ordinal_key_column(spec: dict) -> str:
    """The column whose value keys duplicate detection and row labels: the claimant."""
    return spec["fields"]["claimant"]


def _ordinal_evidence_pointers(spec: dict, where: str) -> list:
    """[(label, pointer, suffix)] every evidence pointer of a latta-kernel spec (the clause mapping's document, each passage_text condition's, each escape hatch's and each
    repair's), for the declarations validator: it checks existence (with `suffix` appended to its message) and the S3 pointer rules. `where` is the spec's own path."""
    out = [(f"{where}.effect_clauses_evidence", spec["effect_clauses_evidence"], "")]
    for ef in spec.get("extra_fields", []):
        if ef.get("kind") != "passage_text":
            continue
        col = f"{where}.extra_fields[{ef['column']}]"
        out.append((f"{col}.condition_evidence", ef["condition_evidence"], " (existence only)"))
        for d in [ef["condition"], *ef.get("by_claimant", {}).values()]:
            for h in ([d["ocr_lost_stop"]] if "ocr_lost_stop" in d else []) + list(d.get("ocr_stops", [])):
                out.append((f"{col} escape hatch {h['text']!r}: evidence", h["evidence"], " (existence only)"))
        for rp in ef.get("repairs", []):
            out.append((f"{col}.repairs[{rp['from']!r}].evidence", rp["evidence"], " (existence only)"))
    return out


# ───────────────────────── kernel 2: paired enumeration (C1-2; the vedha scale's rule) ─────────────────────────
# A passage that gives two enumerations joined by "respectively" ("... caused by one, two, three, four or five malefics, the corresponding effects will be fear, failure,
# killing (blood-shed), death and ignominy respectively"). The spec declares where each list sits (`key_list` / `value_list`: the text AFTER which and BEFORE which the list
# runs; each marker occurs exactly once in the cut span, the value list ends at a declared pairing word) and the stored key -> key word map (`key_words`, e.g. {"1": "one"}).
# A row matches only if the INDEX of its key word in the key list equals the INDEX of its stored value in the value list, so two swapped grades fail: the binding of a value
# to a key is the passage's POSITION, never the presence of a word anywhere. A parenthetical gloss in the passage ("killing (blood-shed)") is not part of the item's name.
# An optional `description` column is a COMPOSED string (a declared template over the key phrase and the stored value, plus an optional declared editorial suffix): it must equal
# the rendering exactly; the suffix is not passage text and the record says so.

PAIRED = "paired_enumeration_v1"
PAIRED_RESULT_KEYS = frozenset({"key", "value", "pair"})
PAIRING_WORDS = ("respectively",)
_ITEM_SPLIT = re.compile(r"\s*(?:,|\band\b|\bor\b)\s*")
_PAREN = re.compile(r"\([^)]*\)")
SUFFIX_MAX = 600


def _enumeration(seg: str, lst: dict):
    """(item names as token lists, reason, full items as token lists). The items of the list that runs between the single occurrence of lst['after'] and the first lst['before']
    after it; the NAME of an item drops a parenthetical gloss, the FULL item keeps it."""
    a, b = lst["after"], lst["before"]
    if seg.count(a) != 1:
        return None, f"the list start marker {a!r} occurs {seg.count(a)} times in the declared span (exactly once is required)", None
    i = seg.find(a) + len(a)
    j = seg.find(b, i)
    if j < 0:
        return None, f"the list end marker {b!r} is absent after {a!r}", None
    body = _ws(seg[i:j])
    items = [x for x in _ITEM_SPLIT.split(body) if x.strip()]
    toks = [_toks(_PAREN.sub(" ", x)) for x in items]
    if not toks or any(not t for t in toks):
        return None, f"the list between {a!r} and {b!r} is empty or has an empty item", None
    return toks, "", [_toks(x) for x in items]


def _paired_lists(spec: dict, seg: str):
    """(key items, value items, value items with their gloss, reason)."""
    ks, why, _kf = _enumeration(seg, spec["key_list"])
    if ks is None:
        return None, None, None, why
    vs, why, vfull = _enumeration(seg, spec["value_list"])
    if vs is None:
        return None, None, None, why
    if seg.find(spec["key_list"]["after"]) > seg.find(spec["value_list"]["after"]):
        return None, None, None, "the key list does not precede the value list in the declared span"
    return ks, vs, vfull, ""


def _paired_span_check(spec: dict, seg: str):
    ks, vs, _vf, why = _paired_lists(spec, seg)
    if ks is None:
        return f"NO_DETECTOR: {why}: the pairing cannot be read, and D1 does not guess it"
    if len(ks) != len(vs):
        return f"NO_DETECTOR: the passage lists {len(ks)} keys but {len(vs)} values: 'respectively' pairs equal lists, so no pairing is read"
    if len(set(map(tuple, ks))) != len(ks) or len(set(map(tuple, vs))) != len(vs):
        return "NO_DETECTOR: an item occurs twice in a list: its position would not identify it"
    if len(ks) != spec["expected_rows"]:
        return f"NO_DETECTOR: the passage pairs {len(ks)} items but expected_rows declares {spec['expected_rows']}"
    return None


def match_paired_row(row: dict, seg: str, spec: dict) -> dict:
    """{key, value, pair, <description column>} each True / False. A malformed row is all False."""
    f = spec["fields"]
    n, v = row.get(f["key"]), row.get(f["value"])
    res = dict(key=False, value=False, pair=False)
    d = spec.get("description")
    if d:
        res[d["column"]] = False
    for ef in spec.get("extra_fields", []):
        res[ef["column"]] = row.get(ef["column"]) == ef["value"]
    if not (isinstance(n, int) and not isinstance(n, bool) and isinstance(v, str) and v.strip()):
        return res
    ks, vs, vfull, _why = _paired_lists(spec, seg)
    word = spec["key_words"].get(str(n))
    if ks is None or vs is None or word is None:
        return res
    wt, vt = _toks(word), _toks(v)
    ki = [i for i, t in enumerate(ks) if t == wt]
    vi = [i for i, t in enumerate(vs) if t == vt]
    res["key"] = len(ki) == 1
    res["value"] = len(vi) == 1
    res["pair"] = len(ki) == 1 and len(vi) == 1 and ki[0] == vi[0]
    if d:
        phrase = d["key_phrases"].get(str(n))
        grade = v.strip()
        gp = (d.get("grade_phrases") or {}).get(str(n))
        if gp is not None:                       # a declared rendering of the grade WITH its passage gloss: it must be exactly the passage's full item at this position
            grade = gp if len(vi) == 1 and _toks(gp) == vfull[vi[0]] else None
        if phrase is not None and grade is not None and _toks(phrase)[:len(wt)] == wt:
            want = d["template"].format(key_phrase=phrase, grade=grade) + (" " + d["suffix"] if d.get("suffix") else "")
            got = row.get(d["column"])
            res[d["column"]] = isinstance(got, str) and _ws(got) == _ws(want)
    return res


def _validate_paired(spec: dict, where: str) -> None:
    fl = spec["fields"]
    if not (isinstance(fl, dict) and set(fl) == {"key", "value"} and all(isinstance(x, str) and _IDENT.fullmatch(x) for x in fl.values()) and fl["key"] != fl["value"]):
        raise SpecError(f"{where}.spec.fields must map exactly ['key', 'value'] to two distinct column identifiers")
    er = spec["expected_rows"]
    kw = spec["key_words"]
    if not (isinstance(kw, dict) and isinstance(er, int) and not isinstance(er, bool) and er >= 1 and len(kw) == er
            and all(isinstance(k, str) and re.fullmatch(r"[0-9]{1,4}", k) and isinstance(w, str) and re.fullmatch(r"[A-Za-z]+( [A-Za-z]+)?", w) for k, w in kw.items())
            and len({w.lower() for w in kw.values()}) == len(kw)):
        raise SpecError(f"{where}.spec.key_words must map each stored key (as a string, one per expected row) to a distinct passage word")
    for nm in ("key_list", "value_list"):
        lst = spec[nm]
        if not (isinstance(lst, dict) and set(lst) == {"after", "before"} and all(isinstance(lst[k], str) and lst[k].strip() and len(lst[k]) <= MARKER_MAX for k in lst)):
            raise SpecError(f"{where}.spec.{nm} must be {{after, before}} with non-blank marker strings (<= {MARKER_MAX} chars)")
    if spec["value_list"]["before"].strip().lower() not in PAIRING_WORDS:
        raise SpecError(f"{where}.spec.value_list.before must be the passage's pairing word {list(PAIRING_WORDS)}: only a passage that says its two lists correspond in order is read as a pairing")
    efs = spec.get("extra_fields", [])
    if not isinstance(efs, list):
        raise SpecError(f"{where}.spec.extra_fields must be a list")
    seen = set(fl.values())
    for ef in efs:
        if not (isinstance(ef, dict) and set(ef) == {"column", "kind", "value"} and ef["kind"] == "equals" and isinstance(ef["column"], str) and _IDENT.fullmatch(ef["column"])
                and ef["column"] not in seen and ef["column"] not in PAIRED_RESULT_KEYS and isinstance(ef["value"], str) and ef["value"].strip()):
            raise SpecError(f"{where}.spec.extra_fields entries are {{column, kind: 'equals', value}} on a new column that is not a result key {sorted(PAIRED_RESULT_KEYS)} (this kernel's extras are declared constants)")
        seen.add(ef["column"])
    d = spec.get("description")
    if d is None:
        return
    if not (isinstance(d, dict) and set(d) <= {"column", "template", "key_phrases", "grade_phrases", "suffix", "suffix_evidence"} and {"column", "template", "key_phrases"} <= set(d)):
        raise SpecError(f"{where}.spec.description takes column, template, key_phrases and optionally suffix + suffix_evidence")
    if not (isinstance(d["column"], str) and _IDENT.fullmatch(d["column"]) and d["column"] not in fl.values() and d["column"] not in PAIRED_RESULT_KEYS and d["column"] not in {e["column"] for e in efs}):
        raise SpecError(f"{where}.spec.description.column must be a new column identifier that does not collide with a result key {sorted(PAIRED_RESULT_KEYS)}")
    if not (isinstance(d["template"], str) and sorted(re.findall(r"\{([a-z_]+)\}", d["template"])) == ["grade", "key_phrase"] and d["template"].count("{") == 2):
        raise SpecError(f"{where}.spec.description.template must contain exactly {{key_phrase}} and {{grade}}")
    kp = d["key_phrases"]
    if not (isinstance(kp, dict) and set(kp) == set(kw) and all(isinstance(x, str) and x.strip() and _toks(x)[:len(_toks(kw[k]))] == _toks(kw[k]) for k, x in kp.items())):
        raise SpecError(f"{where}.spec.description.key_phrases must give every key a phrase that STARTS with its passage key word")
    gps = d.get("grade_phrases", {})
    if not (isinstance(gps, dict) and set(gps) <= set(kw) and all(isinstance(x, str) and x.strip() for x in gps.values())):
        raise SpecError(f"{where}.spec.description.grade_phrases maps a key to the grade WITH its passage gloss (a subset of the keys)")
    if "suffix" in d:
        if not (isinstance(d["suffix"], str) and d["suffix"].strip() and len(d["suffix"]) <= SUFFIX_MAX and isinstance(d.get("suffix_evidence"), str) and d["suffix_evidence"].strip()):
            raise SpecError(f"{where}.spec.description.suffix must be a non-blank string (<= {SUFFIX_MAX} chars) with a suffix_evidence pointer: it is editorial text the passage does not carry, declared, not matched")
    elif "suffix_evidence" in d:
        raise SpecError(f"{where}.spec.description.suffix_evidence without a suffix")


def _paired_columns(spec: dict) -> list:
    d = spec.get("description")
    return list(dict.fromkeys(list(spec["fields"].values()) + ([d["column"]] if d else []) + [ef["column"] for ef in spec.get("extra_fields", [])]))


def _paired_key_column(spec: dict) -> str:
    return spec["fields"]["value"]            # the value (a unique text label) keys duplicate detection and row labels; the numeric key is checked by pairing


def _paired_matched_columns(spec: dict) -> list:
    d = spec.get("description")
    return list(dict.fromkeys(list(spec["fields"].values()) + ([d["column"]] if d else [])))       # the `equals` extras are constants, not matched


def _paired_coverage(spec: dict) -> dict:
    cov = {spec["fields"]["value"]: "value"}
    d = spec.get("description")
    if d:
        cov[d["column"]] = d["column"]
    return cov


def _paired_evidence_pointers(spec: dict, where: str) -> list:
    d = spec.get("description") or {}
    return [(f"{where}.description.suffix_evidence", d["suffix_evidence"], "")] if d.get("suffix") else []


MATCHING_RULE_TEXT[PAIRED] = (
    "per row, in the declared span of the English translation: the passage holds two enumerations (the key list between the declared `key_list` markers, the value list between the "
    "declared `value_list` markers, which end at the pairing word 'respectively'), each marker occurring once, the lists of equal length and equal to expected_rows, no item twice; "
    "the stored key's declared key word is an item of the key list and the stored value (a parenthetical gloss in the passage item is dropped) is an item of the value list, and "
    "their POSITIONS are equal (a swapped pair fails); a declared `description` column must equal exactly its declared template over the key phrase and the stored value plus the "
    "declared editorial suffix (the suffix is declared text, not passage text); the table holds exactly the declared number of rows and no value twice. Words are compared after "
    "NFKC and lower-casing, ignoring only punctuation and whitespace")
MATCHERS[PAIRED] = match_paired_row


# KERNELS is the CLOSED registry of matching rules. A kernel = {spec_required / spec_optional: the kernel's own spec fields (the harness adds matcher, table, chunk_ids, span,
# expected_rows, row_scope, non_claim_columns); result_keys: the per-row result keys its row function sets for the claim fields (an extra field may not reuse one); and the hooks in
# KERNEL_HOOKS, all pure functions of the spec: columns (what a D1 read selects), key_column (what keys duplicates and row labels), matched_columns (what it compares to the
# passage or the declared claim), coverage (the Narr coupling's covered set), validate (its own spec syntax), span_check, evidence_pointers (every evidence pointer the declarations
# validator must see to exist); rule_text: the stated rule, copied into every record as `matching_rule`}. A kernel that lacks a hook is refused with a SpecError, never a KeyError.
# The row function lives in MATCHERS (the tests swap it; `d1_measure` refuses a kernel with no row function, and an import-time check pins that the two name the same kernels).
# Adding a kernel is a reviewed edit of this file (a new PR with its own pin), never a declaration.
KERNEL_HOOKS = ("spec_required", "spec_optional", "result_keys", "columns", "key_column", "matched_columns", "coverage", "validate", "span_check", "evidence_pointers", "rule_text")
KERNELS = {
    MATCHER: dict(spec_required=("fields", "direction_words", "anchor_stems", "effect_marker", "effect_end", "effect_frame_words", "effect_clauses",
                                 "effect_clauses_evidence"),
                  spec_optional=("extra_fields",), result_keys=RESULT_KEYS, columns=_ordinal_columns, key_column=_ordinal_key_column,
                  matched_columns=_ordinal_matched_columns, coverage=_ordinal_prose_coverage, validate=_validate_ordinal_v2, span_check=_ordinal_span_check,
                  evidence_pointers=_ordinal_evidence_pointers, rule_text=MATCHING_RULE_TEXT[MATCHER]),
    PAIRED: dict(spec_required=("fields", "key_words", "key_list", "value_list"), spec_optional=("description", "extra_fields"), result_keys=PAIRED_RESULT_KEYS, columns=_paired_columns,
                 key_column=_paired_key_column, matched_columns=_paired_matched_columns, coverage=_paired_coverage, validate=_validate_paired, span_check=_paired_span_check,
                 evidence_pointers=_paired_evidence_pointers, rule_text=MATCHING_RULE_TEXT[PAIRED]),
}
if set(KERNELS) != set(MATCHERS):
    raise ImportError(f"carriage_d1: KERNELS {sorted(KERNELS)} and MATCHERS {sorted(MATCHERS)} must name the same kernels")


# ───────────────────────── the measurement ─────────────────────────

def _claims(citation_state, content_sa_all_null: bool, n_chunks: int, preimages_used: list) -> str:
    return ("D1 matches the ENGLISH translation (content_en) only"
            + (f"; the Sanskrit column (content_sa) is NULL for all {n_chunks} declared chunk(s) and is not matched" if content_sa_all_null
               else "; content_sa is present on some chunk(s) and is NOT matched")
            + f"; the passages are OCR text not checked against the printed book (citation_state: {citation_state})"
            + f"; the stored chunk hashes were verified with the {' and '.join(sorted(set(preimages_used))) or 'no'} preimage"
            + " (text_id-prefixed sha256(utf8(text_id + '::' + content_en)) is the bg_texts.py convention)")


def d1_measure(spec: dict, citation_state, chunks_by_id: dict, rows, table, ledger=None) -> dict:
    """The Carr.D1 measurement record for a declared D1 asset.

    `chunks_by_id` {chunk_id: {chunk_id, text_id, content_en, content_sa, content_sha256}} as fetched; `rows` the asset's table rows
    (list of dicts) or None when they could not be read; `table` the asset's registry target table (None when it has none). The
    caller has validated `spec` (validate_spec). `ledger` is None (the column ledger is not requested: the record carries no `column_ledger`
    key) or {columns: {column: type string} | None (None = the catalog could not be read), prose_columns: [column, ...]}: the ledger then runs and
    a table with an unclassified text column cannot read PASS. Returns {v, measured, d1: {...structured...}, citation_state}."""
    kern = _kernel_of(spec)
    if spec["matcher"] not in MATCHERS:
        raise SpecError(f"d1_measure: kernel {spec['matcher']!r} has no row function in MATCHERS: the two registries drifted")
    base = dict(matcher=spec["matcher"], matching_rule=kern["rule_text"], span=dict(spec["span"]),
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
    ledger_v = [v for _c, v in verified]
    if missing:
        return out(NO_DET, f"NO_DETECTOR: declared chunk(s) not found in classical_text_chunks: {', '.join(missing)}",
                   chunks=ledger_v, missing_chunks=missing)
    bad = [v for v in ledger_v if not v["verified"]]
    if bad:
        return out(NO_DET, "NO_DETECTOR: unreadable passage(s) for D1: " + "; ".join(f"{v['chunk_id']}: {v['reason']}" for v in bad),
                   chunks=ledger_v)
    joined = _ws(" ".join(c["content_en"] for c, _v in verified))
    all_sa_null = all(v["content_sa_null"] for v in ledger_v)
    claims = _claims(citation_state, all_sa_null, len(ledger_v), [v["preimage"] for v in ledger_v])
    ev = dict(chunks=ledger_v, chunks_sha256=chunks_digest(ledger_v), claims=claims, content_sa_all_null=all_sa_null)
    seg, why = cut_span(joined, spec["span"])
    if seg is None:
        return out(NO_DET, f"NO_DETECTOR: {why}", **ev)
    ev["passage_sha256"] = span_digest(seg)
    ev["passage"] = seg                      # the cut span itself, so the digest can be recomputed from the record
    why = kern["span_check"](spec, seg)
    if why:
        return out(NO_DET, why, **ev)
    if not isinstance(rows, list):
        return out(NO_DET, "NO_DETECTOR: the asset's table rows could not be read", **ev)
    if not rows:
        return out(NO_DET, f"NO_DETECTOR: table {spec['table']} is empty: there is no row to match the passage against", **ev)
    scope = spec.get("row_scope")
    graded, outside = partition_rows(rows, scope)         # row_scope: rows outside the declared predicate are counted, never silently dropped
    if scope:
        ev.update(row_scope=copy.deepcopy(scope), rows_in_table=len(rows), out_of_scope_rows=len(outside),
                  out_of_scope_sample=[_row_label(r, kern["key_column"](spec), i) for i, r in outside[:MAX_OUT_OF_SCOPE_SAMPLE]])
        if not graded:
            return out(NO_DET, f"NO_DETECTOR: none of the {len(rows)} row(s) of {spec['table']} lies inside the declared row_scope: there is no in-scope row to "
                               "match the passage against", **ev)
    fn = MATCHERS[spec["matcher"]]
    keyf = kern["key_column"](spec)
    keys = [(r.get(keyf).strip().lower() if isinstance(r, dict) and isinstance(r.get(keyf), str) else None) for _i, r in graded]
    dup = {k for k in keys if k is not None and keys.count(k) > 1}
    results, unmatched = [], []
    for pos, (i, r) in enumerate(graded):
        try:
            res = fn(r if isinstance(r, dict) else {}, seg, spec)
            failed = [k for k, v in res.items() if v not in (True, "NULL-ok")]
        except SpecError as exc:               # a spec fault met at match time is a named miss on this row; any other exception is a real bug and propagates
            res, failed = dict(error=f"{type(exc).__name__}"), [f"error:{type(exc).__name__}"]
        if keys[pos] in dup:
            failed.append("duplicate")
        label = _row_label(r, keyf, i)
        results.append(dict(row=label, result=res, matched=not failed))
        if failed:
            unmatched.append(dict(row=label, failed=failed))
    count_ok = len(graded) == spec["expected_rows"]
    ev.update(rows_total=len(graded), rows_matched=len(graded) - len(unmatched), unmatched=unmatched, rows=results, row_count_ok=count_ok)
    ledger_block = None
    if ledger is not None and isinstance(ledger.get("columns"), dict) and ledger["columns"]:
        ledger_block = column_ledger(spec, ledger["columns"], ledger.get("prose_columns") or ())
        if not ledger_block_is_clean(ledger_block):          # the block is written ONLY when it names something (an unclassified or absent column): a clean ledger adds no key, so a clean record is byte-identical to the one before the ledger existed
            ev["column_ledger"] = ledger_block
    if citation_state not in CITATION_STATES or citation_state in CITATION_CAPPED_STATES:
        return out(NO_DET, f"NO_DETECTOR: {len(graded) - len(unmatched)} of {len(graded)} row(s) matched the declared passage, but the "
                           f"citation_state is {citation_state!r}: anchor matching cannot tell a contradicted source from one not "
                           f"found, so the match is not evidence. {claims}", **ev)
    if ledger is not None and ledger_block is None:
        return out(NO_DET, "NO_DETECTOR: the column ledger was requested but the table's column types could not be read: whether every text column is "
                           "classified cannot be established, so no verdict above NO_DETECTOR is earned", **ev)
    scope_why, ledger_why = scope_cap_problem(len(outside)), ledger_cap_problem(ledger_block)
    if not unmatched and count_ok and not scope_why and not ledger_why:
        return out(PASS_V, f"D1 PASS (citation_state {citation_state}): every one of the {len(graded)} row(s) of {spec['table']} (the "
                           f"{spec['expected_rows']} declared) is found in the declared passage ({', '.join(spec['chunk_ids'])}, from "
                           f"{spec['span']['start']!r}) under rule {spec['matcher']}. {claims}", pass_basis=citation_state, **ev)
    parts = []
    if unmatched:
        parts.append("NOT found: " + ", ".join(f"{u['row']} ({'/'.join(u['failed'])})" for u in unmatched))
    if not count_ok:
        parts.append(f"the table holds {len(graded)} row(s) but {spec['expected_rows']} are declared")
    parts += [w for w in (scope_why, ledger_why) if w]
    return out("PARTIAL", f"D1 PARTIAL: {len(graded) - len(unmatched)} of {len(graded)} row(s) found in the declared passage; "
                          f"{'; '.join(parts)}. {claims}", **ev)


def _row_label(r, keyf, i):
    return ((r.get(keyf).strip() if isinstance(r.get(keyf), str) else None) if isinstance(r, dict) else None) or f"row {i}"

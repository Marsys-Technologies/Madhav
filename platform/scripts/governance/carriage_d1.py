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
  extra_fields     other columns checked per row: {column, kind: "equals", value} or {column, kind: "passage_text", anchors[], repairs{}}
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

import hashlib
import re

CITATION_STATES = ("sourced", "sourced_ocr_unverified", "unsourced", "refuted")
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
#   effect     (1) a stated effect is normalised (trimmed, trailing '.' removed, spaces collapsed) and must be at least 5 characters
#              with a word of 4+ letters (an empty, "." or one-letter effect is a miss, never a match);
#              (2) it must occur, as whole words, in the effect section (from `effect_marker` to `effect_end`) at a CLAUSE EDGE on
#              both sides: before it the start, punctuation, a capitalised start or a declared frame word; after it the end,
#              punctuation, a capitalised word (the OCR often drops the full stop) or a declared frame word, so "Loss" is not the
#              effect "Loss of position or similar untoward event";
#              (3) it must belong to THIS claimant: of the unit anchors in the SAME SENTENCE as the occurrence (no '.' or ';'
#              between; "Latta of <X>", "<X>'s Latta", stems declared) the NEAREST one is the claimant's, and it is
#              <=120 characters away: the other claimant's effect, even one stated a few words away, is not this claimant's;
#              a NULL effect needs NO anchor of this claimant in the effect section (nothing is invented for a row the passage
#              gives no effect for).
#   extra      each declared extra column: `equals` an exact declared value, or `passage_text` (every declared anchor phrase in
#              the value AND in the passage, and every word of 4+ letters of the value, after the declared OCR repairs, in the
#              passage). KNOWN LIMIT: an effect that is the tail of a longer clause after a comma is not told from the whole.

_COUNT_REACH, _ANCHOR_REACH = 90, 120
_PUNCT = ".;:,!?/)"


def _ordinal(n: int) -> str:
    return rf"\b{n}(?:st|nd|rd|th)\b"


def _norm_effect(eff: str) -> str:
    return re.sub(r"\s+", " ", eff.strip()).rstrip(".").strip()


def _effect_ok_text(e: str) -> bool:
    return len(e) >= 5 and bool(re.search(r"[A-Za-z]{4,}", e))


def _token_before(pre: str) -> str:
    m = re.search(r"([A-Za-z']+)\W*$", pre)
    return m.group(1) if m else ""


def _edge_ok(sec: str, start: int, end: int, frame: set) -> bool:
    pre, post = sec[:start].rstrip(), sec[end:].lstrip()
    first = sec[start:end][:1]
    before = (not pre) or pre[-1] in _PUNCT or first.isupper() or _token_before(pre).lower() in frame
    nxt = re.match(r"[A-Za-z]+", post)
    after = (not post) or post[0] in _PUNCT or bool(nxt and nxt.group().lower() in frame) or bool(nxt and post[0].isupper())
    return before and after


def _anchors(sec: str, stems: list) -> list:
    st = "|".join(rf"{re.escape(x)}\w*" for x in stems)
    out = []
    for m in re.finditer(rf"(?:{st})\s+of\s+(?:the\s+)?([A-Z][a-z]+)", sec):
        out.append((m.group(1), m.start(), m.end()))
    for m in re.finditer(rf"([A-Z][a-z]+)'s\s+(?:{st})", sec):
        out.append((m.group(1), m.start(), m.end()))
    return sorted(out, key=lambda a: a[1])


def _effect_matches(eff: str, claimant: str, sec: str, spec: dict):
    """True / False for a stated effect (rule (1)-(3) above)."""
    e = _norm_effect(eff)
    if not _effect_ok_text(e):
        return False
    frame = {w.lower() for w in spec.get("effect_frame_words", [])}
    anchors = _anchors(sec, spec["anchor_stems"])
    if not any(a[0].lower() == claimant.lower() for a in anchors):
        return False
    pat = r"(?<![A-Za-z])" + r"\s+".join(re.escape(w) for w in e.split(" ")) + r"(?![A-Za-z])"
    for m in re.finditer(pat, sec, re.I):
        if not _edge_ok(sec, m.start(), m.end(), frame):
            continue
        best = None
        for name, a0, a1 in anchors:
            between = sec[a1:m.start()] if a1 <= m.start() else (sec[m.end():a0] if a0 >= m.end() else "")
            if "." in between or ";" in between:
                continue                                  # another sentence: not a candidate owner of this effect
            gap = 0 if (a0 < m.end() and m.start() < a1) else (m.start() - a1 if a1 <= m.start() else a0 - m.end())
            if best is None or gap < best[0]:
                best = (gap, [name])
            elif gap == best[0] and name not in best[1]:
                best[1].append(name)
        if best is None:
            continue
        gap, names = best
        if len(names) != 1 or names[0].lower() != claimant.lower() or gap > _ANCHOR_REACH:
            continue
        return True
    return False


def _extra_ok(row: dict, ef: dict, seg: str) -> bool:
    col, kind = ef["column"], ef["kind"]
    v = row.get(col)
    if not (isinstance(v, str) and v.strip()):
        return False
    if kind == "equals":
        return v == ef["value"]
    low = seg.lower()
    anchors = ef["anchors"]
    if not all(a.lower() in v.lower() and a.lower() in low for a in anchors):
        return False
    val = v
    for k, rep in ef.get("repairs", {}).items():
        val = re.sub(re.escape(k), rep, val, flags=re.I)
    words = set(re.findall(r"[a-z]{2,}", low))
    return all(w in words for w in re.findall(r"[A-Za-z]{4,}", val.lower()))


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
        res[ef["column"]] = _extra_ok(row, ef, seg)
    return res


MATCHER = "ordinal_count_direction_effect_v2"
MATCHERS = {MATCHER: match_ordinal_row}
MATCHER_FIELDS = {MATCHER: ("claimant", "count", "direction", "effect")}
MATCHING_RULE_TEXT = {
    MATCHER:
        "per row, in the declared span of the English translation: the stored count appears as a whole ordinal before 'that of "
        "<claimant>' (no other ordinal between, <=90 characters, no '.' or ';'); the first direction word after it is the stored "
        "direction's declared word; a stated effect (>=5 characters, 4+ letter word) appears at a clause edge in the effect section "
        "with the claimant's own unit anchor as its nearest anchor in the same sentence (<=120 characters) (a NULL effect needs NO such "
        "anchor); every declared extra column equals its declared value or is anchor-matched in the passage; the table holds exactly the "
        "declared number of rows and no claimant twice",
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
               "effect_frame_words", "expected_rows", "extra_fields"}
    extra = sorted(set(spec) - allowed)
    if extra:
        raise SpecError(f"{where}.spec: unknown field(s) {extra}")
    missing = sorted(k for k in ("matcher", "table", "chunk_ids", "span", "fields", "direction_words", "anchor_stems", "expected_rows")
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
        if v is not None and not (isinstance(v, str) and v.strip() and len(v) <= MARKER_MAX):
            raise SpecError(f"{where}.spec.{k} must be a non-blank string or absent")
    if "effect_frame_words" in spec:
        _word_list(spec["effect_frame_words"], "effect_frame_words", where)
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
            if not set(ef) <= {"column", "kind", "anchors", "repairs"} or not (
                    isinstance(ef.get("anchors"), list) and ef["anchors"] and all(isinstance(a, str) and a.strip() for a in ef["anchors"])):
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}]: passage_text needs anchors (and optional repairs)")
            rp = ef.get("repairs", {})
            if not (isinstance(rp, dict) and all(isinstance(k, str) and k and isinstance(v, str) and v for k, v in rp.items())):
                raise SpecError(f"{where}.spec.extra_fields[{ef['column']}].repairs must map text to its OCR form")
    return spec


def spec_columns(spec: dict) -> list:
    """The columns a D1 read must select: the claim fields and the declared extra columns."""
    return list(dict.fromkeys(list(spec["fields"].values()) + [ef["column"] for ef in spec.get("extra_fields", [])]))


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
    for key in ("effect_marker", "effect_end"):
        mk = spec.get(key)
        if mk and mk not in seg:
            return out(NO_DET, f"NO_DETECTOR: the declared {key} {mk!r} is absent from the declared span: the effect section cannot be "
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
        res = fn(r if isinstance(r, dict) else {}, seg, spec)
        failed = [k for k, v in res.items() if v not in (True, "NULL-ok")]
        if keys[i] in dup:
            failed.append("duplicate")
        label = (r.get(keyf) if isinstance(r, dict) else None) or f"row {i}"
        results.append(dict(row=label, result=res, matched=not failed))
        if failed:
            unmatched.append(dict(row=label, failed=failed))
    count_ok = len(rows) == spec["expected_rows"]
    ev.update(rows_total=len(rows), rows_matched=len(rows) - len(unmatched), unmatched=unmatched, rows=results, row_count_ok=count_ok)
    if citation_state not in CITATION_STATES or citation_state in ("unsourced", "refuted"):
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

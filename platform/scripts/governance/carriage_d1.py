"""carriage_d1.py: the generic D1 (source correspondence) engine for the Carr gate (SS N-72 S2, N-73 (2): for an asset that
TRANSCRIBES classical content the applicable carriage check is D1, a match to a cited source; D3 is for computed assets).

Pure functions. No database, no network, no clock: asset_census.py passes in the fetched passages and the asset's rows, so
every case is testable from fixtures. An asset DECLARES its D1 in asset_declarations.json (`carriage.applies = "D1"` plus a
`carriage.spec`); an asset without a spec is never measured here.

THE SPEC (validated by `validate_spec`, read by `d1_measure`):
  matcher          the name of a rule engine in MATCHERS (a STATED matching rule; `ordinal_count_direction_effect_v1` first)
  table            the asset's own table (it must be the registry target_table; asserted by the caller)
  chunk_ids        the declared passage chunks, IN PAGE ORDER (classical_text_chunks.chunk_id); the span is cut from their join
  span             {start, end?}: markers; the passage is the join text from `start` (to `end`, else to the end of the join)
  fields           {claimant, count, direction, effect}: which columns of the table carry the claim
  direction_words  {stored value: word the translation uses}, e.g. {"backward": "rear"}: a DECLARED equivalence
  anchor_stems     word stems a passage uses to name the unit the effect is attached to (OCR variants listed), e.g. ["Latt", "Latin"]
  effect_marker    optional: the passage marker after which the effect sentences begin (OCR text)
A PASS needs every row to match. Any miss is PARTIAL naming the rows (L0 Q13). Anything that cannot be established
(a missing chunk, a hash that verifies against neither preimage, a missing span marker, an unreadable or empty table) is
NO_DETECTOR, never PASS, and the reason is in the record.

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


def passage_digest(chunks_in_order: list[dict]) -> str:
    """sha256 over the verified passages in declared order (chunk_id, stored hash): the identity of the passage a verdict
    was reached against. A passage re-ingested with different text changes it, so a certificate bound to the old value is stale."""
    h = hashlib.sha256()
    for c in chunks_in_order:
        h.update(f"{c['chunk_id']}:{c['stored_sha256']};".encode("utf-8"))
    return h.hexdigest()


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


# ───────────────────────── the matching rule: ordinal count + direction + effect ─────────────────────────
# STATED RULE (ordinal_count_direction_effect_v1), per row, over the cut segment (whitespace-normalised, English only):
#   count      the row's count n appears as an ordinal ("12th") followed, with NO other ordinal in between and within 90
#              characters without ';' or '.', by "that of <claimant>" / "that occupied by the <claimant>" (the page header
#              an OCR page break leaves, "Adh. XXVI MX", is allowed between "that" and "of");
#   direction  after that count the first of the word "forward" or the declared word for the stored direction decides:
#              the first direction word seen must be the one the row's direction maps to;
#   effect     with a stated effect: the effect text (lower-cased, trailing '.' removed) occurs within 70 characters before to
#              120 after an anchor naming this claimant's unit ("Latta of <claimant>", "<claimant>'s Latta"; the anchor
#              stems are declared, OCR variants included); with a NULL effect: NO anchor for this claimant exists in the
#              effect section (nothing is invented for a row the passage gives no effect for).

_WIN_BEFORE, _WIN_AFTER, _COUNT_REACH = 70, 120, 90


def _ordinal(n: int) -> str:
    return rf"\b{n}(?:st|nd|rd|th)\b"


def match_ordinal_row(row: dict, seg: str, spec: dict) -> dict:
    """{count, direction, effect} each True / False / 'NULL-ok'. A malformed row (a missing or wrongly typed field) is all False."""
    f = spec["fields"]
    g, n, dr, eff = row.get(f["claimant"]), row.get(f["count"]), row.get(f["direction"]), row.get(f["effect"])
    res = dict(count=False, direction=False, effect=False)
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
        stored = {s: w for s, w in words.items()}
        first, pos = None, None
        for s, w in stored.items():
            x = re.search(rf"\b{re.escape(w)}\b", after)
            if x and (pos is None or x.start() < pos):
                first, pos = s, x.start()
        res["direction"] = first == dr
    stems = "|".join(rf"{re.escape(s)}\w*" for s in spec["anchor_stems"])
    sec = seg
    marker = spec.get("effect_marker")
    if marker and marker in seg:
        sec = seg[seg.find(marker):]
    anchors = list(re.finditer(rf"(?:{stems})\s+of\s+{ge}\b|{ge}'s\s+(?:{stems})", sec))
    if eff is None:
        res["effect"] = False if anchors else "NULL-ok"
    else:
        e = re.escape(eff.rstrip(".").lower())
        res["effect"] = any(re.search(e, sec[max(0, a.start() - _WIN_BEFORE):a.end() + _WIN_AFTER].lower()) for a in anchors)
    return res


MATCHERS = {"ordinal_count_direction_effect_v1": match_ordinal_row}
MATCHER_FIELDS = {"ordinal_count_direction_effect_v1": ("claimant", "count", "direction", "effect")}
MATCHING_RULE_TEXT = {
    "ordinal_count_direction_effect_v1":
        "per row, in the declared span of the English translation: the stored count appears as an ordinal before 'that of <claimant>' "
        "(no other ordinal between, <=90 characters), the first direction word after it is the stored direction's declared word, "
        "and a stated effect appears within 70 characters before to 120 after an anchor naming the claimant's unit (a NULL effect "
        "needs NO such anchor)",
}


# ───────────────────────── spec validation ─────────────────────────

def validate_spec(spec, where: str) -> dict:
    """The spec dict, or SpecError naming the offending field. Pure syntax: it does not look at any database."""
    if not isinstance(spec, dict):
        raise SpecError(f"{where}.spec must be an object")
    allowed = {"matcher", "table", "chunk_ids", "span", "fields", "direction_words", "anchor_stems", "effect_marker"}
    extra = sorted(set(spec) - allowed)
    if extra:
        raise SpecError(f"{where}.spec: unknown field(s) {extra}")
    missing = sorted(k for k in ("matcher", "table", "chunk_ids", "span", "fields", "direction_words", "anchor_stems") if k not in spec)
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
    em = spec.get("effect_marker")
    if em is not None and not (isinstance(em, str) and em.strip() and len(em) <= MARKER_MAX):
        raise SpecError(f"{where}.spec.effect_marker must be a non-blank string or absent")
    return spec


# ───────────────────────── the measurement ─────────────────────────

def _claims(citation_state, content_sa_all_null: bool, n_chunks: int, preimages_used: list) -> str:
    return ("D1 matches the ENGLISH translation (content_en) only"
            + (f"; the Sanskrit column (content_sa) is NULL for all {n_chunks} declared chunk(s) and is not matched" if content_sa_all_null
               else "; content_sa is present on some chunk(s) and is NOT matched")
            + f"; the passages are OCR text not checked against the printed book (citation_state: {citation_state})"
            + f"; the stored chunk hashes were verified with the {' and '.join(sorted(set(preimages_used))) or 'no'} preimage"
            + " (text_id-prefixed sha256(utf8(text_id + '::' + content_en)) is the bg_texts.py convention)")


def d1_measure(spec: dict, citation_state, chunks_by_id: dict, rows, table: str | None = None) -> dict:
    """The Carr.D1 measurement record for a declared D1 asset.

    `chunks_by_id` {chunk_id: {chunk_id, text_id, content_en, content_sa, content_sha256}} as fetched; `rows` the asset's table rows
    (list of dicts) or None when they could not be read. Returns {v, measured, d1: {...structured...}, citation_state}. The caller
    has validated `spec` (validate_spec) and that spec.table is the asset's registry target table (`table`)."""
    base = dict(matcher=spec["matcher"], matching_rule=MATCHING_RULE_TEXT[spec["matcher"]], span=dict(spec["span"]),
                chunk_ids=list(spec["chunk_ids"]), translation_only=True)

    def out(v, text, **extra):
        d1 = dict(base, **extra)
        return dict(v=v, measured=text, citation_state=citation_state, d1=d1)

    if table is not None and table != spec["table"]:
        return out("NO_DETECTOR", f"NO_DETECTOR: the spec names table {spec['table']!r} but the asset's registry target table is "
                                  f"{table!r}; D1 does not guess", chunks=[])
    verified, missing = [], []
    for cid in spec["chunk_ids"]:
        c = chunks_by_id.get(cid) if isinstance(chunks_by_id, dict) else None
        if c is None:
            missing.append(cid)
            continue
        verified.append((c, verify_chunk(dict(c, chunk_id=cid))))
    ledger = [v for _c, v in verified]
    if missing:
        return out("NO_DETECTOR", f"NO_DETECTOR: declared chunk(s) not found in classical_text_chunks: {', '.join(missing)}",
                   chunks=ledger, missing_chunks=missing)
    bad = [v for v in ledger if not v["verified"]]
    if bad:
        return out("NO_DETECTOR", "NO_DETECTOR: unreadable passage(s) for D1: "
                   + "; ".join(f"{v['chunk_id']}: {v['reason']}" for v in bad), chunks=ledger)
    texts = [c["content_en"] for c, _v in verified]
    joined = _ws(" ".join(texts))
    digest = passage_digest(ledger)
    all_sa_null = all(v["content_sa_null"] for v in ledger)
    claims = _claims(citation_state, all_sa_null, len(ledger), [v["preimage"] for v in ledger])
    ev = dict(chunks=ledger, passage_sha256=digest, claims=claims, content_sa_all_null=all_sa_null)
    seg, why = cut_span(joined, spec["span"])
    if seg is None:
        return out("NO_DETECTOR", f"NO_DETECTOR: {why}", **ev)
    if not isinstance(rows, list):
        return out("NO_DETECTOR", "NO_DETECTOR: the asset's table rows could not be read", **ev)
    if not rows:
        return out("NO_DETECTOR", f"NO_DETECTOR: table {spec['table']} is empty: there is no row to match the passage against", **ev)
    fn = MATCHERS[spec["matcher"]]
    results, unmatched = [], []
    for i, r in enumerate(rows):
        res = fn(r if isinstance(r, dict) else {}, seg, spec)
        ok = all(v in (True, "NULL-ok") for v in res.values())
        label = (r.get(spec["fields"]["claimant"]) if isinstance(r, dict) else None) or f"row {i}"
        results.append(dict(row=label, result=res, matched=ok))
        if not ok:
            unmatched.append(dict(row=label, failed=[k for k, v in res.items() if v not in (True, "NULL-ok")]))
    ev.update(rows_total=len(rows), rows_matched=len(rows) - len(unmatched), unmatched=unmatched, rows=results)
    if not unmatched:
        return out("PASS", f"D1 PASS: every one of the {len(rows)} row(s) of {spec['table']} is found in the declared passage "
                           f"({', '.join(spec['chunk_ids'])}, from {spec['span']['start']!r}) under rule {spec['matcher']}. {claims}", **ev)
    names = ", ".join(f"{u['row']} ({'/'.join(u['failed'])})" for u in unmatched)
    return out("PARTIAL", f"D1 PARTIAL: {len(rows) - len(unmatched)} of {len(rows)} row(s) found in the declared passage; "
                          f"NOT found: {names}. {claims}", **ev)

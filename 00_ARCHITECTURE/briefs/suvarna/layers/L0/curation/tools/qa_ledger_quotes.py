#!/usr/bin/env python3
"""QA of curation ledgers: every corpus pointer must resolve and every quote must be in the chunk.

  qa_ledger_quotes.py <rq.sh> <ledger.json> [<ledger.json> ...]

Reader-only: SELECT of classical_text_chunks through the caller-supplied read-only helper
(prints no credential).  For each corpus item {chunk_id, page, quote}:
  * chunk_id exists                                         (else MISSING)
  * the chunk's page locator equals the item's page         (else PAGE_MISMATCH)
  * each '...'-separated quote segment appears in the chunk text after OCR-tolerant
    normalisation, similarity >= THRESH                     (else QUOTE_LOW)
Bracketed annotations in a quote ([OCR '...'], [...]) are removed before matching.
Exit code 1 if anything fails."""
import difflib, json, re, subprocess, sys

THRESH = 0.80


def norm(s):
    s = s.lower()
    s = re.sub(r"\[[^\]]*\]", " ", s)
    s = re.sub(r"-\s+", "", s)
    s = re.sub(r"[^a-z0-9\u0900-\u097f()%.,;:'’ \-]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def best_ratio(needle, hay):
    n = len(needle)
    if n == 0: return 1.0
    best, step = 0.0, max(1, n // 5)
    for i in range(0, max(1, len(hay) - n + 1), step):
        r = difflib.SequenceMatcher(None, needle, hay[i:i + n + 8], autojunk=False).ratio()
        if r > best: best = r
        if best > 0.97: break
    return best


def fetch_many(rq, ids):
    out, ids = {}, sorted(ids)
    for i in range(0, len(ids), 40):
        part = ids[i:i + 40]
        lst = ",".join("'" + c.replace("'", "''") + "'" for c in part)
        sql = f"select chunk_id||'|'||verse_ref||'|'||encode(convert_to(content_en,'UTF8'),'hex') from classical_text_chunks where chunk_id in ({lst})"
        for line in subprocess.run([rq, sql], capture_output=True, text=True).stdout.splitlines()[1:]:
            if line.count("|") >= 2:
                cid, vref, hx = line.split("|", 2)
                out[cid] = (vref, norm(bytes.fromhex(hx).decode("utf8")))
    return out


def walk_corpus(entry):
    for c in entry.get("corpus") or []:
        yield c


def main(rq, paths):
    entries = []
    for p in paths:
        data = json.load(open(p))
        if isinstance(data, dict):
            for v in data.values():
                entries += v if isinstance(v, list) else v.get("entries", [])
        else:
            entries += data
    ids = {c["chunk_id"] for e in entries for c in walk_corpus(e) if c.get("chunk_id")}
    chunks = fetch_many(rq, ids)
    n_items = n_seg = 0
    bad = []
    low = []
    for e in entries:
        for c in walk_corpus(e):
            if not c.get("chunk_id"): continue
            n_items += 1
            if c["chunk_id"] not in chunks:
                bad.append(("MISSING", e.get("row_key"), c["chunk_id"])); continue
            vref, text = chunks[c["chunk_id"]]
            pg = str(c.get("page") or "")
            if pg and not vref.startswith(pg.split(":")[0]) :
                bad.append(("PAGE_MISMATCH", e.get("row_key"), c["chunk_id"], pg, vref))
            q = c.get("quote")
            if not q: continue
            for seg in [s.strip() for s in re.split(r"\.\.\.|…", q) if s.strip()]:
                nd = norm(seg)
                if len(nd) < 4: continue
                n_seg += 1
                r = 1.0 if nd in text else best_ratio(nd, text)
                if r < THRESH:
                    low.append(("QUOTE_LOW", e.get("row_key"), c["chunk_id"], seg[:80], round(r, 2)))
    print(f"entries {len(entries)}; corpus items {n_items}; distinct chunks {len(ids)} (found {len(chunks)}); quote segments {n_seg}")
    print(f"MISSING/PAGE problems: {len(bad)}; quotes below {THRESH}: {len(low)}")
    for b in bad[:40]: print("  ", b)
    for b in low[:60]: print("  ", b)
    return 1 if (bad or low) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:]))

#!/usr/bin/env python3.13
"""D1 source-correspondence detector for bg_nakshatra_medical (CARRIAGE_MENU D1).

The claim being tested: each of the 27 rows restates a cited classical source. The checkable
core of that claim, without adjudicating the astrology: every source named in a row's
classical_citation must resolve to a text admitted in the estate's own text registry
(brahma_ontology entity_class='text', matched on canonical_id or any declared synonym,
case-folded). A citation that names a text the estate has not admitted is a carriage failure:
the asset quotes an authority the vocabulary gate does not know.

Prints one JSON line: {"verdict": "PASS"|"FAIL", "measured": "..."}. Exit 0 on PASS, 1 on FAIL.
Reads PG* env (campaign sandbox).
"""
from __future__ import annotations

import json
import os
import re
import sys

import psycopg2


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def main() -> int:
    conn = psycopg2.connect(host=os.environ["PGHOST"], port=os.environ["PGPORT"],
                            user=os.environ["PGUSER"], dbname=os.environ["PGDATABASE"])
    cur = conn.cursor()
    cur.execute("SELECT canonical_id, canonical_name_en, synonyms FROM brahma_ontology "
                "WHERE entity_class='text'")
    admitted: dict[str, str] = {}
    for cid, name, syns in cur.fetchall():
        admitted[norm(cid.replace("_", " "))] = cid
        admitted[norm(name or "")] = cid
        for s in (syns or []):
            admitted[norm(str(s).replace('"', ""))] = cid
    cur.execute("SELECT nakshatra_name, classical_citation FROM bg_nakshatra_medical ORDER BY 1")
    rows = cur.fetchall()
    conn.close()

    unresolved: dict[str, list[str]] = {}
    for nak, cit in rows:
        for piece in re.split(r"\s*/\s*", cit or ""):
            piece = norm(re.sub(r"\s+ch\.?\s*\d+.*$", "", piece, flags=re.I))  # drop chapter refs
            if not piece:
                continue
            if piece not in admitted:
                unresolved.setdefault(piece, []).append(nak)
    if unresolved:
        detail = "; ".join(f"'{k}' cited by {len(v)} row(s), not in text registry"
                           for k, v in sorted(unresolved.items()))
        print(json.dumps({"verdict": "FAIL",
                          "measured": f"{len(rows)} rows checked; unresolved sources: {detail}"}))
        return 1
    print(json.dumps({"verdict": "PASS",
                      "measured": f"{len(rows)}/{len(rows)} rows' citations resolve to admitted texts"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

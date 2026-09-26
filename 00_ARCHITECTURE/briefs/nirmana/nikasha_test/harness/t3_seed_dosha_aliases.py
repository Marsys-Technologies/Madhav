#!/usr/bin/env python3.13
"""T3 data fix F1 (sandbox only): seed the dosha class's empty alias sets in brahma_ontology.

Ledger gap: bg_ontology-Vocab.alias / bg_ontology-G07 — "79 of 79 dosha rows carry an empty
synonyms array; the other 15 classes are complete".

Seeder-style derivation, matching the convention visible in the other classes (lowercase
transliteration variants as a postgres text[]): for each dosha row the closed alias set is built
from the row's own two canonical names —
  canonical_name_en: lowercase full form, and the form with the trailing "dosha" dropped
  canonical_name_sa: lowercase IAST form, parenthetical variants split out, plus the
                     diacritic-stripped (ASCII) fold of each
Every variant is deduped; empties and the canonical_id itself are dropped. Deterministic: same
table state in, same alias sets out — re-runnable with no drift (idempotent by construction).

Usage: reads PG* env (the campaign sandbox). Prints before/after coverage.
"""
from __future__ import annotations

import re
import unicodedata

import psycopg2
import os


def ascii_fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def variants(name: str) -> set[str]:
    out: set[str] = set()
    if not name:
        return out
    parts = re.split(r"[()]", name)  # split parentheticals: "Maṅgala Doṣa (Kuja Doṣa)"
    for p in parts:
        p = p.strip().lower()
        if not p:
            continue
        for form in {p, ascii_fold(p)}:
            form = re.sub(r"\s+", " ", form).strip()
            if form:
                out.add(form)
                short = re.sub(r"\s+dosha$", "", form).strip()
                if short and short != form:
                    out.add(short)
    return out


def main() -> None:
    conn = psycopg2.connect(host=os.environ["PGHOST"], port=os.environ["PGPORT"],
                            user=os.environ["PGUSER"], dbname=os.environ["PGDATABASE"])
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM brahma_ontology WHERE entity_class='dosha' "
                "AND (synonyms IS NULL OR synonyms='{}')")
    before_empty = cur.fetchone()[0]
    cur.execute("SELECT id, canonical_id, canonical_name_en, canonical_name_sa "
                "FROM brahma_ontology WHERE entity_class='dosha' ORDER BY id")
    rows = cur.fetchall()
    updated = 0
    for rid, cid, name_en, name_sa in rows:
        syns = sorted((variants(name_en or "") | variants(name_sa or "")) - {cid})
        if not syns:
            continue
        cur.execute("UPDATE brahma_ontology SET synonyms=%s WHERE id=%s", (syns, rid))
        updated += 1
    conn.commit()
    cur.execute("SELECT count(*) FROM brahma_ontology WHERE entity_class='dosha' "
                "AND (synonyms IS NULL OR synonyms='{}')")
    after_empty = cur.fetchone()[0]
    cur.execute("SELECT canonical_id, synonyms FROM brahma_ontology "
                "WHERE entity_class='dosha' ORDER BY id LIMIT 3")
    sample = cur.fetchall()
    conn.close()
    print(f"dosha rows: {len(rows)}; empty alias sets before={before_empty} after={after_empty}; "
          f"rows updated={updated}")
    for cid, s in sample:
        print(f"  {cid}: {s}")


if __name__ == "__main__":
    main()

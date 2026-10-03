#!/usr/bin/env python3
"""Assemble the N-101 curation ledger (master JSON + markdown) from the per-asset ledgers.

  assemble_ledger.py <out_dir> <asset=ledger.json[,ledger2.json...]> ...

The bg_transit_rules / bg_transit_engine entries are produced in-process by
build_transit_curation.py; every other asset's entries come from its research ledger.
Row-weighted counts: an entry covers `row_count` rows (1 for row-level entries)."""
import collections, datetime, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_transit_curation as B  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
SRC = dict(a.split("=", 1) for a in sys.argv[2:])
STATES = ["sourced_fact", "sourced_inference", "already_sourced_verified", "unsourced_marked", "text_not_held",
          "contradicted", "not_a_classical_claim", "existing_citation_unverifiable"]
SOURCED = {"sourced_fact", "sourced_inference", "already_sourced_verified"}

LIVE_ROWS = {   # filled by --live-counts file if present
}

# N-102: six assets whose provenance is deferred by the owner (recorded, not curated)
N102 = [
    ("bg_medical_mappings", {"bg_medical_mappings": 21}),
    ("bg_nakshatra_medical", {"bg_nakshatra_medical": 27}),
    ("bg_sign_medical", {"bg_sign_medical": 12}),
    ("bg_vastu_directions", {"bg_vastu_directions": 8, "bg_vastu_direction_remedials": 24}),
    ("bg_kota_chakra_rings", {"bg_kota_chakra_rings": 27}),
    ("bg_gochara_citation_resolution", {"bg_gochara_citation_resolution": 14}),
]
N102_NOTE = "deferred by owner (N-102): source not held"


def weight(e):
    return int(e.get("row_count") or 1)


def load_asset(asset):
    if asset in ("bg_transit_rules", "bg_transit_engine"):
        return B.entries() if asset == "bg_transit_rules" else B.engine_entries()
    out = []
    for p in SRC[asset].split(","):
        data = json.load(open(p))
        out += data if isinstance(data, list) else data.get("entries", [])
    return out


def main():
    assets = ["bg_transit_rules", "bg_transit_engine", "bg_dasha_systems", "bg_dignity_reference", "bg_doshas",
              "bg_nakshatra", "bg_reference", "bg_prashna_rules"]
    master = {"meta": {
        "artifact": "L0_CURATION_LEDGER", "version": "1.0-draft", "status": "HELD DRAFT (N-101 curation; not canonical until SS review)",
        "produced_by": "curation-lane (Exec Suvarna)", "produced_on": "2026-10-03", "branch": "suvarna/land/TI-curation-001",
        "corpus": "classical_text_chunks via the read-only proxy (SELECT only); verse_ref / chapter are PAGE locators",
        "states": STATES, "sourced_states": sorted(SOURCED),
        "support_class": ["FACT", "INFERENCE", "NONE", "CONTRADICTS"],
        "no_live_table_edited": True}, "assets": {}, "deferred_n102": []}
    for a in assets:
        ents = load_asset(a)
        if a == "bg_doshas":   # one entry per dosha; each dosha spans 3 table rows (catalog + reference + ontology)
            for e in ents:
                e["rows_spanned"] = int(e.get("row_count") or 1)
                e["row_count"] = 1
        cnt = collections.Counter()
        by_table = collections.defaultdict(collections.Counter)
        for e in ents:
            cnt[e["state"]] += weight(e)
            by_table[e["table"]][e["state"]] += weight(e)
        master["assets"][a] = {
            "rows_total": sum(cnt.values()),
            "counts_by_state": {s: cnt.get(s, 0) for s in STATES},
            "counts_by_table": {t: dict(c) for t, c in by_table.items()},
            "entries": ents}
    for a, tabs in N102:
        master["deferred_n102"].append({"asset": a, "tables": tabs, "rows": sum(tabs.values()), "state": N102_NOTE})
    OUT.mkdir(parents=True, exist_ok=True)
    print({a: master["assets"][a]["counts_by_state"] for a in assets})
    return master


def esc(x):
    return str(x).replace("|", "\\|").replace("\n", " ")


def fmt_key(rk):
    if not isinstance(rk, dict): return esc(rk)
    return esc(", ".join(f"{k}={v}" for k, v in rk.items() if v is not None))[:90]


def fmt_corpus(e, n=2):
    cs = e.get("corpus") or []
    parts = []
    for c in cs[:n]:
        sl = c.get("sloka_printed")
        parts.append(f"{c.get('chunk_id')} ({c.get('page')}" + (f", sl.{sl}" if sl else "") + ")")
    if len(cs) > n: parts.append(f"+{len(cs) - n}")
    return esc("; ".join(parts))


def short(x, n=110):
    x = x or ""
    return esc(x if len(x) <= n else x[:n - 1] + "\u2026")


def asset_md(asset, a):
    rows = []
    rows.append(f"# {asset}: row-level curation ledger (generated)\n")
    rows.append("Generated from `L0_CURATION_LEDGER_v1_0.json`; the JSON is authoritative. FACT = the chunk text states the value; INFERENCE = a stated step was needed; "
                "CONTRADICTS = the held text states otherwise; NONE = not stated.\n")
    rows.append("| table | row key | rows | state | class | corpus (chunk, page, sloka printed) | proposed citation (short) | action |")
    rows.append("|---|---|---|---|---|---|---|---|")
    for e in a["entries"]:
        rows.append(f"| {esc(e.get('table'))} | {fmt_key(e.get('row_key'))} | {weight(e)} | {e['state']} | {e.get('support_class', '')} | "
                    f"{fmt_corpus(e)} | {short(e.get('proposed_citation'))} | {e.get('proposed_action', '')} |")
    return "\n".join(rows) + "\n"


def acharya_batch(master):
    groups = collections.OrderedDict()
    for asset, a in master["assets"].items():
        for e in a["entries"]:
            q = (e.get("acharya_question") or "").strip()
            if not q: continue
            g = groups.setdefault((asset, q), {"rows": 0, "keys": []})
            g["rows"] += weight(e)
            if len(g["keys"]) < 6: g["keys"].append(fmt_key(e.get("row_key")))
    return groups


def write_master(master, out, gr):
    slim = json.loads(json.dumps(master))
    for a, d in slim["assets"].items():
        d["entries_file"] = f"assets/{a}_ledger.json"
        d["entries_count"] = len(d.pop("entries"))
    slim["acharya_batch"] = [{"asset": a, "question": q, "rows": g["rows"], "example_keys": g["keys"]} for (a, q), g in gr.items()]
    json.dump(slim, open(out / "L0_CURATION_LEDGER_v1_0.json", "w"), ensure_ascii=False, indent=1)


def main_md(master, out):
    L = []
    A = master["assets"]
    L.append("---\nartifact: L0_CURATION_LEDGER\nversion: \"1.0-draft\"\nstatus: \"HELD DRAFT: N-101 curation ledger (data PR TI-curation-001); not canonical until SS review\"\n"
             "produced_by: curation-lane (Exec Suvarna)\nproduced_on: 2026-10-03\nmachine_readable: L0_CURATION_LEDGER_v1_0.json\n"
             "changelog:\n  - \"1.0-draft 2026-10-03: first ledger; 8 L0 assets curated against the served corpus (reader-only); no live table edited\"\n---\n")
    L.append("# L0 curation ledger (N-101), HELD DRAFT\n")
    L.append("**What this is.** For each of the 8 L0 assets named by N-101 (`bg_transit_rules`, `bg_dasha_systems`, `bg_dignity_reference`, `bg_doshas`, `bg_nakshatra`, `bg_reference`, "
             "`bg_transit_engine`, `bg_prashna_rules`) every citation-bearing row (or, for large homogeneous tables, every claim family with its full key set) is checked against the "
             "served classical corpus (`classical_text_chunks`, SELECT only through the read-only proxy). Nothing in any live table was edited. The proposed data changes are in `drafts/` "
             "and are NOT applied and NOT in the migrations folder. The six N-102 assets are recorded as deferred, not curated.\n")
    L.append("**Corpus fact that shapes every row.** In this corpus `verse_ref` and `chapter` are PAGE locators (PG324 = scanned page 324), not chapter.sloka. A book-chapter citation such as "
             "\"BPHS Ch.29\" therefore cannot be resolved by number; support is found by reading the chunk text and recording chunk id + page + the sloka number PRINTED in the chunk. "
             "Where the printed numeral is OCR-garbled the number is fixed by the running head and sequence and flagged.\n")
    L.append("**States.** `sourced_fact` (chunk states the value) | `sourced_inference` (needs a stated inference step) | `already_sourced_verified` (existing page/sloka-anchored citation re-read and confirmed) | "
             "`unsourced_marked` (value not stated in the held corpus; value kept, honest marker) | `text_not_held` (cited text is not in the corpus) | `contradicted` (held text states otherwise; row NOT changed; acharya batch) | "
             "`not_a_classical_claim` (platform vocabulary / identity) | `existing_citation_unverifiable` (cited text is held but its chapter-grain citation cannot be resolved and the row was not checked further in this pass).\n")
    L.append("## 1. Roll-up (row-weighted)\n")
    L.append("| asset | rows | sourced FACT | sourced INFERENCE | already verified | unsourced-marked | text not held | contradicted (acharya) | not a classical claim | citation unverifiable, not checked | proposed re-citations |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    tot = collections.Counter()
    for asset, a in A.items():
        c = a["counts_by_state"]
        props = sum(weight(e) for e in a["entries"] if e.get("proposed_citation") and e.get("proposed_action") == "recite")
        L.append(f"| {asset} | {a['rows_total']} | {c['sourced_fact']} | {c['sourced_inference']} | {c['already_sourced_verified']} | {c['unsourced_marked']} | {c['text_not_held']} | {c['contradicted']} | {c['not_a_classical_claim']} | {c['existing_citation_unverifiable']} | {props} |")
        for k, v in c.items(): tot[k] += v
        tot["rows"] += a["rows_total"]; tot["props"] += props
    L.append(f"| **total (8 assets)** | {tot['rows']} | {tot['sourced_fact']} | {tot['sourced_inference']} | {tot['already_sourced_verified']} | {tot['unsourced_marked']} | {tot['text_not_held']} | {tot['contradicted']} | {tot['not_a_classical_claim']} | {tot['existing_citation_unverifiable']} | {tot['props']} |\n")
    L.append("Counting units: row-weighted; `bg_doshas` is counted per dosha (79 doshas = 237 table rows across catalog, reference and ontology); `bg_nakshatra` matrix and some `bg_reference` glossary/constants entries are claim families "
             "that carry their full key set (`row_key_query` / `row_keys`) and are weighted by the rows they cover. An object with several fields carries its WORST field state (e.g. one contradicted field makes the nakshatra object `contradicted`); per-field detail is inside the object.\n")
    L.append("**Deferred by owner (N-102): source not held** (recorded only; not curated):\n")
    L.append("| asset | tables (live rows 2026-10-03) | rows | state |\n|---|---|---|---|")
    for d in master["deferred_n102"]:
        L.append(f"| {d['asset']} | {', '.join(f'{k} {v}' for k, v in d['tables'].items())} | {d['rows']} | {d['state']} |")
    L.append("")
    L.append("## 2. Counts by table and state\n")
    L.append("| asset | table | " + " | ".join(STATES) + " |\n|---|---|" + "---|" * len(STATES))
    for asset, a in A.items():
        for t, c in a["counts_by_table"].items():
            L.append(f"| {asset} | {t} | " + " | ".join(str(c.get(s, 0)) for s in STATES) + " |")
    L.append("")
    L.append("## 3. Where the row-level detail is\n")
    for asset in A:
        L.append(f"- `assets/{asset}_LEDGER.md` (generated tables) and `assets/{asset}_ledger.json` (full entries incl. quotes, chunk uuids, inference steps)")
    L.append("")
    # transit detail inline
    L.append("## 4. bg_transit_rules and bg_transit_engine (the SS-ruled re-sourcing), inline\n")
    L.append("### 4.1 Re-sourced rows (23): old citation -> Phaladeepika Adh. XXVI slokas 9-24\n")
    L.append("| id | row | old citation | state | class | chunk (page, sloka) | what the chunk states | phala words NOT in the sloka |\n|---|---|---|---|---|---|---|---|")
    for e in A["bg_transit_rules"]["entries"]:
        if e["state"] in ("sourced_fact", "sourced_inference"):
            rk = e["row_key"]; c = e["corpus"][0] if e["state"] == "sourced_fact" else e["corpus"][1]
            L.append(f"| {rk['id']} | {rk['graha']} {rk['primary_house']} {rk['rule_type']} | {short(e['current_citation'], 40)} | {e['state']} | {e['support_class']} | "
                     f"{c['chunk_id']} ({c['page']}, sl.{c['sloka_printed']}) | {esc(e.get('phala_supported_by_chunk'))} | {esc(e.get('phala_not_in_chunk'))} |")
    L.append("")
    L.append("### 4.2 Not changed\n")
    L.append("- id 199 ketu 12 favourable: **contradicted** (acharya batch); citation stays `BPHS Ch.29` (refuted).")
    L.append("- 39 rows already page/sloka-anchored: re-verified by diffing the transcribed sloka 3-8 pairs and the sloka-2 favourable sets against the live rows (0 differences).")
    L.append("- ids 187-189, 196-198 (Rahu/Ketu favourable-with-vedha): already marked UNSOURCED in the row text.")
    L.append("- ids 133-139 (double-transit): unsourced; the cited Phaladeepika section does not exist in the held text (0 hits); ids 135 and 139 also cite the refuted `BPHS ch.29`.\n")
    L.append("### 4.3 bg_transit_engine (9 rows): citation text only, values untouched\n")
    L.append("| graha | state | cell the corpus states | chunk(s) |\n|---|---|---|---|")
    for e in A["bg_transit_engine"]["entries"]:
        cells = ", ".join(k for k, v in (e.get("cells") or {}).items() if v != "NONE") or "none"
        L.append(f"| {e['row_key']['graha']} | {e['state']} | {cells} | {fmt_corpus(e, 3)} |")
    L.append("")
    # acharya batch
    gr = acharya_batch(master)
    L.append("## 5. Acharya batch (exact questions; nothing in it was changed)\n")
    L.append(f"{len(gr)} distinct questions. Each lists the asset, the rows it covers and example keys.\n")
    cur = None; n = 0
    for (asset, q), g in gr.items():
        if asset != cur:
            L.append(f"### {asset}\n"); cur = asset
        n += 1
        L.append(f"{n}. **[{g['rows']} row(s); e.g. {'; '.join(g['keys'][:3])}]** {q}")
    L.append("")

    # ---- 6. drafts --------------------------------------------------------------------------
    drafts = [
        ("DRAFT_NEEDS_NUMBER_l0_transit_citation_curation.sql", "bg_transit_rules + bg_transit_engine", "23 rules + 9 engine citations (+ 2 registry rows; optional attribution_state block)", "yes (sha256 x2)", "PG_TEST_EVIDENCE.txt"),
        ("DRAFT_l0_transit_seed_curation.patch", "bg_transit_rules + bg_transit_engine (seed module l0_transit.py)", "same 32 citations; `git apply --check` clean on origin/main", "n/a", "PG_TEST_EVIDENCE.txt (P7 seed parity)"),
    ]
    import pathlib as _pl
    for a in ("bg_dignity_reference", "bg_reference", "bg_nakshatra", "bg_dasha_systems", "bg_prashna_rules"):
        ev = out / "drafts" / f"PG_TEST_EVIDENCE_{a}.txt"
        rows = ""; rs = ""
        if ev.exists():
            import re as _re
            m_ = _re.search(r"G1 PASS probe[^:]*: (\d+) rows over (\d+) table\(s\); (\d+) hash literal", ev.read_text(encoding="utf8"))
            if m_: rows = f"{m_.group(1)} citation cells over {m_.group(2)} tables"; rs = "yes (%s literals)" % m_.group(3) if m_.group(3) != "0" else "no (check does not hash these columns)"
        drafts.append((f"DRAFT_NEEDS_NUMBER_l0_{a}_citation_curation.sql", a, rows or "see file", rs if rows else "", f"PG_TEST_EVIDENCE_{a}.txt"))
    L.append("## 6. Draft data changes (all in `drafts/`; NOT applied; NOT in the migrations folder; SS allocates numbers)\n")
    L.append("| file | asset | change | integrity contract resealed | real-PG test evidence |\n|---|---|---|---|---|")
    for f, a, c, r, e in drafts:
        L.append(f"| `{f}` | {a} | {c} | {r} | `{e}` |")
    L.append("")
    L.append("Each SQL is one `DO` block (transaction owned by the runner): per-table content fingerprints pinned before and after, every UPDATE guarded by natural key AND exact old citation with an exact row count, the stored `integrity_check_sql` pinned by md5 and resealed where it hashes the changed columns, idempotent (second apply = NOTICE no-op), "
             "and tested on a disposable local PostgreSQL 15 (replica fidelity, apply once, idempotency, five guard refusals, necessity of the reseal, mutation of the pinned post-state). `bg_doshas` has NO draft SQL by design: its citation lives in `brahma_dosha_catalog.classical_citations` (jsonb) which feeds `ga_structural_writer` (L1 `chart_facts`) and `bg_parihara_rules` (which includes only doshas with a real `text_id`), so any change there is a joint L0/L1 decision; the ledger carries the chunk-anchored proposals. The 48 glossary family entries of `bg_reference` are not drafted (one proposed citation spans several terms whose support differs).\n")
    L.append("**Coupling and ordering (read before numbering):**\n")
    L.append("1. Seed parity: each writer's seed module carries the old citations; a rebuild would revert the SQL. Only `l0_transit.py` is patched (draft patch); editing any `brahmagyan/l0_*.py` stales `nirmana-writer-digests.json` (a #2984 file), so the seed patches wait for #2984.")
    L.append("2. `platform/tests/unit/migrations/nirmana_l0_transit_integrity_contract.test.ts` (run with a real DB in CI) builds its rows from `l0_transit.py` and pins the migration-1078 rules hash `1dbdd265...`; merging the seed patch alone turns it red (the curated content hashes to a different value). The migration, the seed patch and that test's re-baseline must land together.")
    L.append("3. PR #3044 (migration 1268, `attribution_state`): apply 1268 BEFORE the transit draft. Its backfill guard expects exactly 19 `refuted` rows (the BPHS Ch.29 set this lane re-sources); applied after, it refuses by design. The optional block in the transit draft then moves the 18 FACT rows to `sourced` and resets the 5 Ketu INFERENCE rows to NULL.")
    L.append("4. L3/Kala products hold build-time copies of the old rule citations: `gochara_resonance_map.classical_citation` (115 rows) and `kala_gochara_contacts.classical_citation` (123 rows, with a `corpus_verifiable` stamp); no integrity check compares them to `bg_transit_rules`, they read stale until `ka_gochara_resonance` / the contacts writer are rebuilt (Kala layer; not touched).")
    L.append("5. Every re-citation to `muhurta_chintamani` or `tajaka_neelakanthi` rests on Devanagari/Hindi OCR chunks whose registry note reads AWAITING_NATIVE_DECISION. Rows proposed that way: %d (row-weighted); they should not be applied before that decision." % sum(weight(e) for a_ in A.values() for e in a_["entries"] if e.get("proposed_action") == "recite" and ("muhurta_chintamani" in (e.get("proposed_citation") or "") or "tajaka_neelakanthi" in (e.get("proposed_citation") or ""))))
    L.append("")
    L.append("## 7. Findings outside the brief\n")
    for t in [
        "**Mars 8th is sloka 15, not 16** (WAVE_PLACEHOLDER_DISPOSITIONS Appendix A had sl. 16): the 8th-house sentence sits in the continuation of sl. 15 (PG326 -> PG327); sl. 16 opens at the 10th house.",
        "**Valence is the sourced part, phala wording is not**: for all 23 re-sourced rows the sloka supports the adverse valence and some of the effect words; the stored `phala` text goes beyond it (per-row lists in 4.1). The new citation says so in its own text.",
        "**WAVE-1's 'only Jupiter is supported' is partly superseded**: Sun '30 days' and Saturn '30 months' / '900 days' per sign are stated in translator notes (brihat_jataka PG96, jataka_parijata PG144, sarvartha_chintamani PG1:C301); the Moon's figure is OCR-illegible; Yavanajataka's commentary derives a sidereal month of 27.405 d (stored 27.32 is modern). Mars, Mercury, Venus, Rahu, Ketu: nothing.",
        "**The unfavourable rows are a subset of what the text lists**: e.g. the Sun is adverse in houses 2, 4, 7, 9, 12 too (sl. 9-11) but has unfavourable rows only at 1, 5, 8. Completeness of the table is a design question for SS, not a citation fix.",
        "**Sloka 2 equates Rahu/Ketu with the Sun** (good houses 6, 3, 10, 11) but the table has Rahu/Ketu favourable at 3, 6, 11 only.",
        "**Writer defect, bg_nakshatra: all 144 `bhakoot_kuta` rows score 7/7.** `l0_nakshatra.py:1237-1242` compares 0-based sign differences to an inclusive-position tuple set, so the inauspicious set never matches (live: 144 rows, min = max = 7.00). Not fixed here (curation lane).",
        "**The doshas 'zero corpus mention' premise fails for at least 9 of the 41 token rows** (an ASCII name-match missed Muhurta Chintamani's IAST/Devanagari text, BPHS Ch.80/92-93, Phaladeepika sl. on Mrityu-Bhaga and Shakata); they stay unsourced-marked with the candidate chunks recorded, not adopted.",
        "**Book-chapter citations are systematically wrong for the held editions**: dasha systems cite BPHS Ch.47-50 but Santhanam Ch.46 holds every dasha definition; 'BPHS Ch.27' (friendship, karakas, 69 rows) is the Shadbala chapter; signs 'Ch.6' are in Ch.4; the Jaimini rows cite `jaimini_sutram`, which is not a corpus text id (held: `bphs_jaimini`).",
        "**`source_chunk_ids` is BIGINT[] and cannot hold UUID chunk ids** (all three catalogs store `{}`); the established carrier is the chunk-anchored jsonb entry `{chapter, text_id, chunk_id, verse_ref}` already used by `brahma_yoga_catalog`; the dasha draft adopts it.",
        "**Contradictions found by simple arithmetic or by reading, now in the acharya batch**: Sthira 86 vs 4x(7+8+9)=96; Niryana Shoola 108 vs 96; Kalachakra Leo 21 vs Sun 5; Shatabdika/Shashtihayani lord tables; Yogardha defined as the Chara/Sthira half-sum in both held texts; saptavargaja 22.5/7.5/3.75/1.875 vs the held 20/10/4/2; Ashtakavarga lists (6 rows); bindu/rekha inverted in the glossary; Gulika kendra rule; Kuja 1st/2nd houses.",
    ]:
        L.append(f"- {t}")
    L.append("")
    L.append("## 8. Regenerate and verify\n")
    L.append("`tools/regen_all.sh <read-only helper> <snapshot dir> <pg socket dir> <pg port>` re-dumps the touched tables (SELECT only), re-runs every real-PG test against a disposable local server the CALLER starts and stops, and re-runs `tools/qa_ledger_quotes.py` (every corpus pointer resolves to a chunk whose page matches and every quote is found in the chunk text under OCR-tolerant matching). "
             "`tools/build_transit_curation.py verify-quotes` does the same for the transit rows.\n")
    (out / "L0_CURATION_LEDGER_v1_0.md").write_text("\n".join(L), encoding="utf8")
    (out / "assets").mkdir(exist_ok=True)
    for asset, a in A.items():
        (out / "assets" / f"{asset}_LEDGER.md").write_text(asset_md(asset, a), encoding="utf8")
        json.dump(a["entries"], open(out / "assets" / f"{asset}_ledger.json", "w"), ensure_ascii=False, indent=1)
    return gr


if __name__ == "__main__":
    m = main()
    gr = main_md(m, OUT)
    write_master(m, OUT, gr)
    print("acharya questions:", len(gr))

"""test_e6_c2_ldgr_placeholder.py -- C2(ii) (SS ruling N-98, REGISTRY_REVISION 22): a PLACEHOLDER citation is not a source.

Ldgr.source_presence's legacy (undeclared) reading was `col IS NOT NULL`, so rows holding 'UNSOURCED ...' (bg_transit_rules, brahmagyan/l0_transit.py:80-86) or a bare tradition
label ('classical_tradition' in brahma_dosha_catalog.classical_citations, l0_doshas.py:111; 'classical tradition (Jyotish)' in brahma_ontology / brahma_remedy_corpus,
l0_doshas.py:39 / l0_remedy_corpus.py:46) read as sourced. The reading now goes through the SAME shared predicate as the declared ldgr_source check
(`_ldgr_lacking` over `_ldgr_lacking_text`): ONE definition, a closed list, and nothing else changes.

Real SQL on the disposable PostgreSQL (skips only when no PG binaries exist); the pure parts run everywhere. Every guard has a mutation test: the mutated code must read
differently from the expected result, so the assertion has teeth.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
import test_r60_ldgr_source_presence_singular_citation as r60  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL = ac.PASS, ac.FAIL, ac.PARTIAL
LDGR = "Ldgr.source_presence"

UNSOURCED_LONG = ("UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus (Phaladipika Adh. XXVI slokas 3-8, phaladeepika:PG322:C1-"
                  "PG323:C1, name only the seven classical grahas; BPHS Ch.29 does not exist in this corpus).")      # the literal shape of brahmagyan/l0_transit.py:80-86
PLACEHOLDERS = [
    "UNSOURCED", "unsourced", "  Unsourced. ", "UNSOURCED — no source", UNSOURCED_LONG, "unsourced: see note", "UNSOURCED — x",
    "classical_tradition", " CLASSICAL_TRADITION ", "Classical_Tradition.", "classical_ tradition", "classical_  tradition", "_classical_tradition_",
    "classical tradition (Jyotish)", "Classical Tradition (Jyotish).", " classical  tradition (JYOTISH) ", "classical tradition(Jyotish)",
    "Vastu Shastra tradition (Nairitya corner)", " vastu shastra tradition (NAIRITYA CORNER). ", "Vastu  Shastra tradition(Nairitya corner)",
    "N/A", "not traced", "-", "",                                   # the pre-existing closed list still lacks a source
]
SOURCES = [
    "BPHS Ch.29 (Gochara Phala — Transit Results)", "Phaladipika Adh. XXVI, Sloka 5 — phaladeepika:PG322:C1 (Sastri trans. 1950)",
    "BPHS (Brihat Parasara Hora Sastra), classical tradition",       # a REAL citation that merely mentions the tradition (l0_doshas.py:36)
    "BPHS (Brihat Parasara Hora Sastra), trans. Rishi Kumar Shastri, classical tradition",
    "Tajaka Neelakanthi, classical tradition, public domain",        # l0_remedy_corpus.py:45
    "Vastu Shastra tradition",                                      # VASTU_TRAD_GENERAL (l0_vastu_directions.py:33): lands in bg_vastu_direction_remedials, not a measured target: NOT listed
    "Tajaka tradition", "Mayamata Ch.6", "Vastu Shastra (Mayamata Ch.6)", "Jataka Parijata (unextracted)", "BPHS (unextracted)",     # l0_reference.py:954 glossary (not measured); real vastu citations; (unextracted) keeps its source prefix (l0_text_chunker.py:224)
    "classical tradition",                                          # NOT on the closed list (no writer spelling): stays a citation, an open question for the SS
    "classical tradition; BPHS 3.12", "classical_tradition BPHS Ch.3", "Unsourcedly cited in BPHS 1.1",
    "Saravali ch.3", "Navagraha bīja tradition; compiled in Mantra Mahodadhi",
]
J_LACK = ['[{"text_id": "classical_tradition"}]', '[{"text_id": "CLASSICAL_TRADITION"}]', "[]", "{}", '[{"text_id": "unsourced"}]', '"classical_tradition"', "null",
          '[{"text_id": "classical_tradition"},{"text_id": "n/a"}]', '[{"chapter": 9}]']
J_SOURCE = ['[{"text_id": "bphs"}]', '[{"text_id": "bphs", "chapter": 9}]', '[{"text_id": "phaladeepika", "chapter": 26}]', '"BPHS 3.12"',
            '[{"text_id": "bphs", "chapter": 9},{"text_id": "classical_tradition"}]']       # one real source beside a label: still names one (legacy any_element=False)


def _utf8():
    if ac.psql("SHOW server_encoding")[0][0].upper() != "UTF8":
        pytest.skip("the disposable cluster is not UTF8 (production is)")


def _rows_sql(table, ddl, rows):
    return [f"CREATE TEMP TABLE {table} (k int PRIMARY KEY, c {ddl}) ON COMMIT DROP;",
            f"INSERT INTO {table} VALUES " + ",".join(f"({i},{s3._lit(v) if not isinstance(v, tuple) else v[0]})" for i, v in enumerate(rows, 1)) + ";"]


def _read(monkeypatch, pg, rows, ddl="text", table="c2_t"):
    s3._real(monkeypatch, pg, _rows_sql(table, ddl, rows))
    _utf8()
    return ac.ldgr_legacy_presence(table, "c", len(rows))


def _json_rows(vals):
    return [(f"{s3._lit(v)}::jsonb" if v != "null" else "'null'::jsonb",) for v in vals]


# ───────────────────────── the closed lists: pure checks ─────────────────────────

def test_the_citation_extension_is_a_closed_list_each_entry_justified_by_a_writer_file_line():
    assert ac.LDGR_CITATION_PLACEHOLDERS == ("classical_tradition", "classical tradition (jyotish", "vastu shastra tradition (nairitya corner")
    assert ac.LDGR_CITATION_PLACEHOLDER_PREFIXES == ("unsourced",)
    assert all("'" not in x and '"' not in x for x in ac.LDGR_CITATION_PLACEHOLDERS + ac.LDGR_CITATION_PLACEHOLDER_PREFIXES)      # SQL literals
    assert all(x.isalpha() for x in ac.LDGR_CITATION_PLACEHOLDER_PREFIXES)                                                         # spliced into a regex
    src = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    block = src.split("LDGR_CITATION_PLACEHOLDERS = ", 1)[0].rsplit("# C2(ii)", 1)[1]
    for ref in ("l0_doshas.py:111", "l0_doshas.py:39", "l0_remedy_corpus.py:46", "l0_transit.py:80", "bg_parihara_rules.py:28", "l0_vastu_directions.py:32", "(:108, 1 of 8 rows)", "l0_vastu_directions.py:33", "l0_reference.py:954-958", "l0_text_chunker.py:224"):
        assert ref in block, ref                                      # a spelling with no file:line is not on the list
    assert "unsourced" in ac.LDGR_PLACEHOLDERS                         # the exact word was already there (S3): only the PREFIX form is new


def test_the_base_predicate_is_unchanged_for_the_null_convention_and_the_citation_form_adds_exactly_the_closed_extension():
    base, cit = ac._ldgr_lacking_text("x"), ac._ldgr_lacking_text("x", True)
    assert "classical_tradition" not in base and "^(unsourced)" not in base       # the Null convention (default) is the pre-pin-22 predicate
    assert ac._ldgr_lacking_text("x", False) == base
    for w in ac.LDGR_CITATION_PLACEHOLDERS:
        assert f"'{w}'" in cit and f"'{w}'" not in base
    assert "^(unsourced)" in cit and "^(unsourced)" not in base and "|$)" not in cit.split("^(unsourced)", 1)[1][:80]      # LOW-5: no dead `|$` alternative
    assert ac._ldgr_lacking("c", "text") == ac._ldgr_lacking_text('"c"', True)    # `_ldgr_lacking` is the citation form: ONE definition for legacy and declared
    assert ac._ldgr_lacking("c", "text", any_element=False) == ac._ldgr_lacking("c", "text")      # any_element only changes arrays / JSON arrays


def test_no_other_consumer_re_implements_present():
    """The rollup reads the cell's verdict; the certificate writer and the E6.3 reader read the cell, never the table."""
    repo = HERE.parents[3]
    for f in ("platform/scripts/governance/nikasha_certify.py", "00_ARCHITECTURE/control/asset_elevation_tracker.py"):
        t = (repo / f).read_text(encoding="utf-8")
        assert "_ldgr_lacking" not in t and "ldgr_legacy_presence" not in t and "populated on" not in t, f
        assert "source_citation IS NOT NULL" not in t and "classical_citation IS NOT NULL" not in t, f
    assert ac.CRITERION_REGISTRY[LDGR]["revision"] == 6 and "C2(ii)" in ac.CRITERION_REGISTRY[LDGR]["applicability"]
    assert "UNSOURCED" in ac.CRITERION_REGISTRY[LDGR]["applicability"] and "classical_tradition" in ac.CRITERION_REGISTRY[LDGR]["applicability"]
    import test_e6_1_p1_registry_rollup as p1
    assert ac.REGISTRY_REVISION == max(p1.PINNED_FINGERPRINTS)  and ac.REGISTRY_REVISION in p1.PINNED_FINGERPRINTS     # the pin is carried by the stacked-pin test


# ───────────────────────── real SQL: the legacy reading ─────────────────────────

def test_REAL_SQL_every_placeholder_spelling_stops_counting_and_every_real_citation_still_counts(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_t", "text", PLACEHOLDERS + SOURCES + [None]))
    _utf8()
    out = ac.psql(f"SELECT k FROM c2_t WHERE {ac._ldgr_lacking('c', 'text', any_element=False)} ORDER BY k")
    got = [int(r[0]) for r in out]
    rows = PLACEHOLDERS + SOURCES + [None]
    want = [i for i, v in enumerate(rows, 1) if v is None or v in PLACEHOLDERS]
    assert got == want, [rows[k - 1] for k in sorted(set(got) ^ set(want))]


def test_REAL_SQL_an_all_placeholder_table_reads_FAIL_with_exact_counts(monkeypatch, disposable_pg):
    rec = _read(monkeypatch, disposable_pg, ["UNSOURCED", UNSOURCED_LONG, "classical_tradition", "classical tradition (Jyotish)", None, "n/a"])
    assert rec["v"] == FAIL
    assert rec["measured"].startswith("c names a source on 0/6 rows (5 placeholder row(s)") and rec["measured"].endswith("; 1 NULL)")
    assert rec["ldgr_legacy"] == dict(source_column="c", rows=6, null=1, placeholder=5, present=0)


def test_REAL_SQL_a_mixed_table_reads_PARTIAL_with_the_exact_counts_in_the_text(monkeypatch, disposable_pg):
    rows = ["BPHS Ch.29", UNSOURCED_LONG, "classical_tradition", "Saravali ch.3", None, "Phaladipika 26.42", "classical tradition (Jyotish)"]
    rec = _read(monkeypatch, disposable_pg, rows)
    assert rec["v"] == PARTIAL
    assert "names a source on 3/7 rows (3 placeholder row(s)" in rec["measured"] and "1 NULL" in rec["measured"]
    assert rec["ldgr_legacy"] == dict(source_column="c", rows=7, null=1, placeholder=3, present=3)


def test_REAL_SQL_real_citations_read_exactly_as_before_zero_move(monkeypatch, disposable_pg):
    rec = _read(monkeypatch, disposable_pg, SOURCES)
    assert rec == dict(v=PASS, measured=f"c populated on {len(SOURCES)}/{len(SOURCES)} rows")        # the pre-pin-22 record, byte for byte (no `ldgr_legacy` block)
    rec = _read(monkeypatch, disposable_pg, SOURCES[:4] + [None, None])
    assert rec == dict(v=PARTIAL, measured="c populated on 4/6 rows")                                  # NULLs only: as before
    # and the old reading agrees with the new one on that table (the old count was `col IS NOT NULL`)
    old = int(ac.scalar("SELECT count(*)::text FROM c2_t WHERE c IS NOT NULL"))
    assert old == 4


def test_REAL_SQL_an_all_NULL_column_now_reads_FAIL_not_PARTIAL(monkeypatch, disposable_pg):
    rec = _read(monkeypatch, disposable_pg, [None, None, None])
    assert rec == dict(v=FAIL, measured="c populated on 0/3 rows")


def test_REAL_SQL_jsonb_citations_the_dosha_shape(monkeypatch, disposable_pg):
    """brahma_dosha_catalog.classical_citations is jsonb: [{"text_id": "classical_tradition"}] on the tradition-rooted doshas (l0_doshas.py:111, json.dumps at :1976)."""
    rows = _json_rows(J_LACK + J_SOURCE)
    rec = _read(monkeypatch, disposable_pg, rows, ddl="jsonb")
    assert rec["ldgr_legacy"]["placeholder"] + rec["ldgr_legacy"]["null"] == len(J_LACK) and rec["ldgr_legacy"]["present"] == len(J_SOURCE), rec
    assert rec["v"] == PARTIAL
    # the declared reading keeps ANY-element: a real source beside a label is lacking there, present in the legacy count (the documented difference)
    mixed = ['[{"text_id": "bphs", "chapter": 9},{"text_id": "classical_tradition"}]']
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_t", "jsonb", _json_rows(mixed)))
    assert ac.scalar(f"SELECT count(*)::text FROM c2_t WHERE {ac._ldgr_lacking('c', 'json')}") == "1"
    assert ac.scalar(f"SELECT count(*)::text FROM c2_t WHERE {ac._ldgr_lacking('c', 'json', any_element=False)}") == "0"


def test_REAL_SQL_text_arrays_and_varchar(monkeypatch, disposable_pg):
    arrs = [("ARRAY['classical_tradition']",), ("ARRAY['BPHS 3.12','classical_tradition']",), ("ARRAY['UNSOURCED']",), ("ARRAY[]::text[]",), ("ARRAY['Saravali 3']",), ("NULL",)]
    rec = _read(monkeypatch, disposable_pg, arrs, ddl="text[]")
    assert rec["ldgr_legacy"] == dict(source_column="c", rows=6, null=1, placeholder=3, present=2), rec     # [label], [UNSOURCED], [] lack; [real,label] and [real] name one
    rec = _read(monkeypatch, disposable_pg, ["classical_tradition", "BPHS 1.1"], ddl="varchar(60)")
    assert rec["v"] == PARTIAL and rec["ldgr_legacy"]["placeholder"] == 1


def test_REAL_SQL_a_non_text_column_keeps_IS_NOT_NULL_exactly(monkeypatch, disposable_pg):
    rec = _read(monkeypatch, disposable_pg, [("1",), ("2",), ("NULL",)], ddl="integer")
    assert rec == dict(v=PARTIAL, measured="c populated on 2/3 rows")
    rec = _read(monkeypatch, disposable_pg, [("true",), ("true",)], ddl="boolean")
    assert rec == dict(v=PASS, measured="c populated on 2/2 rows")


def test_REAL_SQL_the_declared_ldgr_source_path_is_unchanged_for_its_own_inputs(monkeypatch, disposable_pg):
    """S3's declared reading: every value of its own LACKING / SOURCED corpora grades exactly as before (the extension only adds the closed citation spellings)."""
    rows = s3.LACKING_TEXT + s3.SOURCED_TEXT + [None]
    got = s3._lacking_ks(monkeypatch, disposable_pg, rows, "text", "text")
    assert got == [i for i, v in enumerate(rows, 1) if v is None or v in s3.LACKING_TEXT]
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_d", "text", ["BPHS 1.1", "Saravali 3", "unsourced", None]))
    st = ac.ldgr_fetch_source_stats("c2_d", "c", ["k"], "text")
    assert (st["rows"], st["lacking"]) == (4, 2)
    ls = dict(source_column="c", citation_state="sourced")
    assert ac.grade_ldgr_source(ls, st, "c2_d")["v"] == PARTIAL
    assert ac.grade_ldgr_source(ls, dict(rows=4, lacking=0, sample=[]), "c2_d")["v"] == PASS
    assert ac.grade_ldgr_source(ls, dict(rows=4, lacking=4, sample=[]), "c2_d")["v"] == FAIL


def test_REAL_SQL_the_declared_check_also_refuses_a_tradition_label_one_definition(monkeypatch, disposable_pg):
    """The declared check shares the predicate, so declaring ldgr_source cannot escape the rule (the only declared change: the closed citation spellings now lack)."""
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_d", "text", ["classical_tradition", UNSOURCED_LONG, "BPHS 1.1"]))
    st = ac.ldgr_fetch_source_stats("c2_d", "c", ["k"], "text")
    assert (st["rows"], st["lacking"]) == (3, 2)


# ───────────────────────── through measure() and the rollup: the cell moves ─────────────────────────

def _measure_through_real_pg(monkeypatch, tmp_path, pg, rows, ddl="text", col="classical_citation"):
    """The REAL measure() path (the r60 offline harness) with its psql answered by the real disposable PG for the Ldgr reads."""
    tbl = "bg_c2_t"
    r60._stub_layer(monkeypatch, tmp_path, {"bg_c2": r60._reg_row("bg_c2", tbl)}, {tbl: (["id", col], [])})
    import subprocess
    setup = [f"CREATE TEMP TABLE {tbl} (id int PRIMARY KEY, {col} {ddl}) ON COMMIT DROP;",
             f"INSERT INTO {tbl} VALUES " + ",".join(f"({i},{s3._lit(v)})" for i, v in enumerate(rows, 1)) + ";"]

    def psql(sql, sep="\x1f", timeout=None):
        if "format_type(a.atttypid" not in sql and "jsonb_build_object('rows'" not in sql and sql != "SHOW server_encoding":
            raise AssertionError(f"unexpected query: {sql[:100]}")
        script = "BEGIN;\n" + "\n".join(setup) + f"\n{sql};\nROLLBACK;\n"
        p = subprocess.run([str(pg.bin_dir / "psql"), pg.url, "-tAX", "-q", "-F", sep, "-v", "ON_ERROR_STOP=1", "-f", "-"], input=script, capture_output=True, text=True, timeout=30)
        if p.returncode != 0:
            raise ac.Unknown((p.stderr.strip().splitlines() or ["psql failed"])[0])
        return s3.s2._psql_lines(p.stdout, sep)

    monkeypatch.setattr(ac, "psql", psql)
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=len(rows), full=list(c), never=[], note=""))
    _utf8_via(psql)
    return r60._measured(ac.measure("L0"), "bg_c2", LDGR)


def _utf8_via(psql):
    if psql("SHOW server_encoding")[0][0].upper() != "UTF8":
        pytest.skip("the disposable cluster is not UTF8 (production is)")


def _gate(rec):
    return ac.rollup_asset("L0", {LDGR: rec})["Ldgr"]


def test_REAL_SQL_measure_and_the_rollup_move_the_gate_cell_down_honestly(monkeypatch, tmp_path, disposable_pg):
    clean = _measure_through_real_pg(monkeypatch, tmp_path, disposable_pg, ["BPHS 1.1", "Saravali 3", "Phaladipika 26.42"])
    assert clean == dict(v=PASS, measured="classical_citation populated on 3/3 rows") and _gate(clean)["v"] == PASS
    mixed = _measure_through_real_pg(monkeypatch, tmp_path, disposable_pg, ["BPHS 1.1", UNSOURCED_LONG, "Saravali 3"])
    assert mixed["v"] == PARTIAL and "names a source on 2/3 rows (1 placeholder row(s)" in mixed["measured"]
    cell = _gate(mixed)
    assert cell["v"] == PARTIAL
    allp = _measure_through_real_pg(monkeypatch, tmp_path, disposable_pg, [UNSOURCED_LONG, "UNSOURCED — x", "unsourced"])
    assert allp["v"] == FAIL and _gate(allp)["v"] == FAIL                                              # a lower Ldgr check reaches the Ldgr gate cell
    old_style = dict(v=PASS, measured="classical_citation populated on 3/3 rows")                       # what the IS NOT NULL count said of the same rows
    assert _gate(old_style)["v"] == PASS != _gate(allp)["v"]


def test_the_legacy_reading_is_reached_only_for_an_undeclared_asset():
    src = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert src.count("ldgr_legacy_presence(tbl, col, dc[\"rows\"])") == 1
    assert "if cit and dc.get(\"rows\") and not _ls_declared and not _src_declared:" in src.split("ldgr_legacy_presence(tbl, col, dc[\"rows\"])", 1)[0][-900:]


# ───────────────────────── mutation tests: each guard has teeth ─────────────────────────

def _expected_mixed(monkeypatch, pg):
    return _read(monkeypatch, pg, ["BPHS 1.1", UNSOURCED_LONG, "classical_tradition", "classical tradition (Jyotish)", "Saravali 3"])


def test_MUTATION_dropping_the_citation_spellings_lets_the_tradition_labels_count_again(monkeypatch, disposable_pg):
    good = _expected_mixed(monkeypatch, disposable_pg)
    assert good["v"] == PARTIAL and good["ldgr_legacy"]["placeholder"] == 3
    monkeypatch.setattr(ac, "LDGR_CITATION_PLACEHOLDERS", ())
    bad = _expected_mixed(monkeypatch, disposable_pg)
    assert bad["ldgr_legacy"]["placeholder"] == 1 and bad != good                                  # only the UNSOURCED prefix row is caught: the two labels read as sources


def test_MUTATION_dropping_the_unsourced_prefix_lets_the_disclosure_sentence_count_again(monkeypatch, disposable_pg):
    good = _expected_mixed(monkeypatch, disposable_pg)
    monkeypatch.setattr(ac, "LDGR_CITATION_PLACEHOLDER_PREFIXES", ("zzzzzz",))
    bad = _expected_mixed(monkeypatch, disposable_pg)
    assert bad["ldgr_legacy"]["placeholder"] == 2 and bad != good                                  # the long 'UNSOURCED - ...' sentence reads as a source again


def test_MUTATION_the_old_IS_NOT_NULL_count_reads_every_placeholder_as_a_source(monkeypatch, disposable_pg):
    good = _expected_mixed(monkeypatch, disposable_pg)
    monkeypatch.setattr(ac, "_ldgr_lacking", lambda col, kind, any_element=True: f'("{col}" IS NULL)')
    bad = _expected_mixed(monkeypatch, disposable_pg)
    assert bad == dict(v=PASS, measured="c populated on 5/5 rows") and bad != good           # the pre-pin-22 reading: PASS over the same rows


def test_MUTATION_any_element_semantics_would_misgrade_a_real_source_beside_a_label(monkeypatch, disposable_pg):
    rows = _json_rows(['[{"text_id": "bphs", "chapter": 9},{"text_id": "classical_tradition"}]', '[{"text_id": "bphs"}]'])
    good = _read(monkeypatch, disposable_pg, rows, ddl="jsonb")
    assert good == dict(v=PASS, measured="c populated on 2/2 rows")
    real = ac._ldgr_lacking
    monkeypatch.setattr(ac, "_ldgr_lacking", lambda col, kind, any_element=False: real(col, kind, any_element=True))
    bad = _read(monkeypatch, disposable_pg, rows, ddl="jsonb")
    assert bad["v"] == PARTIAL and bad != good


def test_MUTATION_the_citation_flag_off_leaves_the_reading_blind_to_every_new_spelling(monkeypatch, disposable_pg):
    good = _expected_mixed(monkeypatch, disposable_pg)
    real = ac._ldgr_lacking_text
    monkeypatch.setattr(ac, "_ldgr_lacking_text", lambda x, citation=False: real(x, False))
    bad = _expected_mixed(monkeypatch, disposable_pg)
    assert bad == dict(v=PASS, measured="c populated on 5/5 rows") and bad != good


def test_MUTATION_a_column_type_that_cannot_carry_text_must_not_be_graded_as_text(monkeypatch, disposable_pg):
    rows = [("false",), ("true",)]                                  # a boolean `false` renders as the placeholder word 'false' when cast to text
    good = _read(monkeypatch, disposable_pg, rows, ddl="boolean")
    assert good == dict(v=PASS, measured="c populated on 2/2 rows")
    monkeypatch.setattr(ac, "ldgr_column_kind", lambda t: "text")
    bad = _read(monkeypatch, disposable_pg, rows, ddl="boolean")
    assert bad["v"] == PARTIAL and bad != good                      # the guard is what keeps the old IS NOT NULL reading for a non-text type


def _mutated_legacy(monkeypatch, old, new, fn="ldgr_legacy_presence"):
    """Source-level mutation of one function of asset_census: the guard text `old` is replaced by `new` and the mutant is installed."""
    import inspect
    import textwrap
    src = textwrap.dedent(inspect.getsource(getattr(ac, fn)))
    assert src.count(old) == 1, old
    ns = dict(vars(ac))
    exec(compile(src.replace(old, new), "<mutant>", "exec"), ns)
    monkeypatch.setattr(ac, fn, ns[fn])


def test_MUTATION_the_all_NULL_FAIL_guard(monkeypatch, disposable_pg):
    assert _read(monkeypatch, disposable_pg, [None, None])["v"] == FAIL
    _mutated_legacy(monkeypatch, "(FAIL if present == 0 else PARTIAL)", "PARTIAL")
    assert _read(monkeypatch, disposable_pg, [None, None])["v"] == PARTIAL                    # the pre-pin-22 reading
    assert _read(monkeypatch, disposable_pg, ["UNSOURCED", "UNSOURCED"])["v"] == PARTIAL      # and an all-placeholder table would NOT read FAIL


def test_MUTATION_the_PASS_guard_must_compare_present_not_non_null(monkeypatch, disposable_pg):
    rows = ["BPHS 1.1", "UNSOURCED"]
    assert _read(monkeypatch, disposable_pg, rows)["v"] == PARTIAL
    _mutated_legacy(monkeypatch, "present = nonnull - ph", "present = nonnull")
    assert _read(monkeypatch, disposable_pg, rows)["v"] == PASS                                # placeholders counted as present again


def test_MUTATION_the_placeholder_count_must_exclude_NULL_rows(monkeypatch, disposable_pg):
    rows = ["BPHS 1.1", None, "UNSOURCED"]
    good = _read(monkeypatch, disposable_pg, rows)
    assert good["ldgr_legacy"] == dict(source_column="c", rows=3, null=1, placeholder=1, present=1)
    _mutated_legacy(monkeypatch, "v IS NOT NULL AND {pred}", "v IS NOT NULL OR {pred}", fn="ldgr_legacy_count_sql")
    bad = _read(monkeypatch, disposable_pg, rows)
    assert bad["ldgr_legacy"]["placeholder"] == 3 and bad != good                                     # NULLs double-counted as placeholders (a NULL row is already counted under `null`)


def test_a_failed_read_degrades_only_this_check(monkeypatch):
    monkeypatch.setattr(ac, "ldgr_fetch_column_type", lambda t, c: "text")
    monkeypatch.setattr(ac, "scalar", lambda sql: "not json")
    with pytest.raises(ac.Unknown):
        ac.ldgr_legacy_presence("bg_x", "source_citation", 3)
    monkeypatch.setattr(ac, "scalar", lambda sql: json.dumps({"rows": 3}))
    with pytest.raises(ac.Unknown):
        ac.ldgr_legacy_presence("bg_x", "source_citation", 3)


def test_a_name_outside_the_identifier_pattern_keeps_the_old_reading_and_never_reaches_a_type_read(monkeypatch):
    called = []
    monkeypatch.setattr(ac, "ldgr_fetch_column_type", lambda t, c: called.append((t, c)) or "text")
    monkeypatch.setattr(ac, "scalar", lambda sql: "2")
    rec = ac.ldgr_legacy_presence("public.bg_x", "source_citation", 2)
    assert rec == dict(v=PASS, measured="source_citation populated on 2/2 rows") and called == []


# ───────────────────────── review round: LOW-4 / LOW-6 / LOW-8 / MED-3 ─────────────────────────

def _old_predicate(x: str, citation: bool) -> str:
    """The pre-optimisation expression (normalisation inlined at every comparison), kept here as the differential-test oracle: same normaliser, same lists."""
    n0 = f"regexp_replace(normalize({x}, NFKC), '{ac._LDGR_INVISIBLE}+', '', 'g')"
    norm = f"lower(regexp_replace(regexp_replace({n0}, '^{ac._LDGR_JUNK}+|{ac._LDGR_JUNK}+$', '', 'g'), '{ac._LDGR_SPACE}+', ' ', 'g'))"
    words = ac.LDGR_PLACEHOLDERS + (ac.LDGR_CITATION_PLACEHOLDERS if citation else ())
    lst = ",".join("'" + w + "'" for w in words)
    nos = ",".join("'" + w + "'" for w in dict.fromkeys(w.replace(" ", "") for w in words))
    pre = f" OR {norm} ~ '^({'|'.join(ac.LDGR_CITATION_PLACEHOLDER_PREFIXES)}){ac._LDGR_JUNK}'" if citation else ""
    return f"({x} IS NULL OR {norm} IN ({lst}) OR replace({norm}, ' ', '') IN ({nos}){pre} OR ({n0} !~ '[[:alnum:]]' AND {n0} !~ '[^\\x01-\\x7f]'))"


def test_the_normalised_value_is_computed_once_per_call():
    for cit in (False, True):
        sql = ac._ldgr_lacking_text("x", cit)
        assert sql.count("normalize(") == 1 and sql.count("OFFSET 0") == 2          # one normalisation, behind an optimisation fence at each derived table
        assert _old_predicate("x", cit).count("normalize(") >= 3                    # what it replaced


@pytest.mark.parametrize("citation", [False, True])
def test_REAL_SQL_differential_the_optimised_predicate_grades_every_value_exactly_as_the_old_expression(monkeypatch, disposable_pg, citation):
    corpus = list(dict.fromkeys(s3.LACKING_TEXT + s3.SOURCED_TEXT + PLACEHOLDERS + SOURCES + [None]))
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_diff", "text", corpus))
    _utf8()
    new = ac.psql(f"SELECT k, ({ac._ldgr_lacking_text('c', citation)})::text FROM c2_diff ORDER BY k")
    old = ac.psql(f"SELECT k, ({_old_predicate('c', citation)})::text FROM c2_diff ORDER BY k")
    assert new == old and len(new) == len(corpus)
    # and the two forms DO differ in what they grade for the new spellings only when citation=True
    flagged = {int(k) for k, v in new if v == "true"}
    assert ("classical_tradition" in [corpus[k - 1] for k in flagged]) is citation


def test_REAL_SQL_the_optimised_predicate_is_correct_inside_arrays_and_jsonb_leaves(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_diff", "jsonb", _json_rows(J_LACK + J_SOURCE)))
    _utf8()
    for kind, kw in (("json", {}), ("json", {"any_element": False})):
        new = ac.psql(f"SELECT k FROM c2_diff WHERE {ac._ldgr_lacking('c', kind, **kw)} ORDER BY k")
        assert new                                                                    # runs, and grades a non-empty set


def test_REAL_SQL_the_old_and_new_predicates_agree_row_for_row_on_a_larger_table(monkeypatch, disposable_pg):
    rows = (PLACEHOLDERS + SOURCES + [None]) * 40
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_diff", "text", rows))
    _utf8()
    a = ac.psql(f"SELECT count(*) FILTER (WHERE {ac._ldgr_lacking_text('c', True)}), count(*) FROM c2_diff")
    b = ac.psql(f"SELECT count(*) FILTER (WHERE {_old_predicate('c', True)}), count(*) FROM c2_diff")
    assert a == b


# LOW-4: the Null convention's fallback test must NOT see the citation-only spellings (a text column legitimately holding the word elsewhere is not a Null fallback)
_NOT_NULL_FALLBACKS = ["classical_tradition", "classical tradition (Jyotish)", "Vastu Shastra tradition (Nairitya corner)", UNSOURCED_LONG, "UNSOURCED — x"]


@pytest.mark.parametrize("kind,ddl,lit", [
    ("text", "text", lambda v: s3._lit(v)),
    ("array_text", "text[]", lambda v: f"ARRAY[{s3._lit(v)}]"),
    ("json", "jsonb", lambda v: f"{s3._lit(json.dumps({'text_id': v}))}::jsonb"),
])
def test_REAL_SQL_the_null_fallback_test_does_not_flag_the_citation_only_spellings(monkeypatch, disposable_pg, kind, ddl, lit):
    rows = [(lit(v),) for v in _NOT_NULL_FALLBACKS] + [(lit("n/a"),)]                 # the last row is the positive control: a pre-existing placeholder IS a Null fallback
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_nf", ddl, rows))
    _utf8()
    sql = ac._null_fallback_sql("c", kind, False)
    got = [int(r[0]) for r in ac.psql(f"SELECT k FROM c2_nf WHERE {sql} ORDER BY k")]
    assert got == [len(rows)], (kind, got)


@pytest.mark.parametrize("kind", ["array", "json"])
def test_REAL_SQL_the_declared_check_grades_arrays_and_json_arrays_with_any_element_semantics(monkeypatch, disposable_pg, kind):
    if kind == "array":
        ddl, vals = "text[]", [("ARRAY['BPHS 1.1']",), ("ARRAY['BPHS 1.1','classical_tradition']",), ("ARRAY['UNSOURCED']",), ("ARRAY['classical tradition (Jyotish)']",),
                               ("ARRAY[]::text[]",), ("ARRAY['Saravali 3','Phaladipika 26.42']",), ("NULL",)]
        want = (7, 5)         # lacking: the mixed one (ANY element), UNSOURCED, the label, empty, NULL
    else:
        ddl, vals = "jsonb", _json_rows(['[{"text_id": "bphs"}]', '[{"text_id": "bphs"},{"text_id": "classical_tradition"}]', '[{"text_id": "unsourced"}]',
                                         '[{"text_id": "classical tradition (Jyotish)"}]', "[]", '[{"text_id": "saravali"},{"text_id": "phaladeepika"}]', "null"])
        want = (7, 5)
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_d", ddl, vals))
    st = ac.ldgr_fetch_source_stats("c2_d", "c", ["k"], kind)
    assert (st["rows"], st["lacking"]) == want and [x["k"] for x in st["sample"]] == [2, 3, 4, 5, 7]
    # the legacy reading of the same rows (EVERY-element semantics) lacks one fewer: the mixed row still names a source
    rec = ac.ldgr_legacy_presence("c2_d", "c", 7)
    assert rec["ldgr_legacy"]["present"] == 3 and rec["ldgr_legacy"]["placeholder"] + rec["ldgr_legacy"]["null"] == 4, rec


@pytest.mark.parametrize("kind", ["array", "json"])
def test_MUTATION_the_declared_array_and_json_branches_must_use_the_citation_form(monkeypatch, disposable_pg, kind):
    ddl, vals = (("text[]", [("ARRAY['classical_tradition']",), ("ARRAY['BPHS 1.1']",)]) if kind == "array"
                 else ("jsonb", _json_rows(['[{"text_id": "classical_tradition"}]', '[{"text_id": "bphs"}]'])))
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_d", ddl, vals))
    assert ac.ldgr_fetch_source_stats("c2_d", "c", ["k"], kind)["lacking"] == 1
    real = ac._ldgr_lacking_text
    monkeypatch.setattr(ac, "_ldgr_lacking_text", lambda x, citation=False: real(x, False))     # an element test that forgot citation=True
    assert ac.ldgr_fetch_source_stats("c2_d", "c", ["k"], kind)["lacking"] == 0


def test_REAL_SQL_every_column_type_reads_all_NULL_as_FAIL(monkeypatch, disposable_pg):
    """LOW-6: ONE all-NULL rule for every type (the declared grader's): FAIL. Text, array, jsonb, and the types that cannot carry text."""
    for ddl in ("text", "varchar(40)", "integer", "boolean", "uuid", "date", "numeric"):
        rec = _read(monkeypatch, disposable_pg, [("NULL",), ("NULL",)], ddl=ddl)
        assert rec["v"] == FAIL and rec["measured"] == "c populated on 0/2 rows", (ddl, rec)
    for ddl in ("text[]", "jsonb"):
        assert _read(monkeypatch, disposable_pg, [("NULL",), ("NULL",)], ddl=ddl)["v"] == FAIL, ddl
    assert _read(monkeypatch, disposable_pg, [("1",), ("NULL",)], ddl="integer") == dict(v=PARTIAL, measured="c populated on 1/2 rows")
    assert _read(monkeypatch, disposable_pg, [("1",), ("2",)], ddl="integer") == dict(v=PASS, measured="c populated on 2/2 rows")


def test_MUTATION_the_non_text_all_NULL_FAIL_guard(monkeypatch, disposable_pg):
    _mutated_legacy(monkeypatch, "(FAIL if n == 0 else PARTIAL)", "PARTIAL")
    assert _read(monkeypatch, disposable_pg, [("NULL",), ("NULL",)], ddl="integer")["v"] == PARTIAL      # the pre-pin-24 non-text reading: the test above would fail


def test_the_legacy_block_has_a_distinct_key_and_no_reader_depends_on_the_declared_one():
    repo = HERE.parents[3]
    for f in ("platform/scripts/governance/nikasha_certify.py", "00_ARCHITECTURE/control/asset_elevation_tracker.py", "platform/scripts/governance/asset_census.py"):
        t = (repo / f).read_text(encoding="utf-8")
        assert '["ldgr"]' not in t and ".get(\"ldgr\")" not in t and "['ldgr']" not in t, f


def test_the_declared_grader_text_names_tradition_labels_and_unsourced():
    t = ac.grade_ldgr_source(dict(source_column="c", citation_state="sourced"), dict(rows=2, lacking=1, sample=[]), "t")["measured"]
    assert "tradition label" in t and "classical_tradition" in t and "UNSOURCED" in t


# ───────────────────────── round 2: distinct values, not rows (the ga_dashas statement timeout) ─────────────────────────

def _old_per_row_count_sql(table, col, kind):
    """The shipped per-row form (the differential oracle): the predicate evaluated on every row."""
    pred = ac._ldgr_lacking(col, kind, any_element=False)
    return (f"SELECT jsonb_build_object('rows',count(*),'null',count(*) FILTER (WHERE \"{col}\" IS NULL),"
            f"'placeholder',count(*) FILTER (WHERE \"{col}\" IS NOT NULL AND {pred}))::text FROM \"{table}\"")


def test_the_legacy_read_groups_by_value_and_runs_the_predicate_over_the_groups_only():
    for kind in ("text", "array", "json"):
        sql = ac.ldgr_legacy_count_sql("t", "c", kind)
        assert sql.startswith('WITH d AS (SELECT "c"' + ac.LDGR_KIND_CAST[kind] + " AS v, count(*) AS n FROM \"t\" GROUP BY 1)") and sql.rstrip().endswith("FROM d")
        assert "sum(n)" in sql and '"c" IS' not in sql.split("FROM d")[0].split("GROUP BY 1)")[1]              # the predicate reads the group value `v`, never the base column


@pytest.mark.parametrize("kind,ddl,vals", [
    ("text", "text", PLACEHOLDERS + SOURCES + [None]),
    ("text", "varchar(400)", PLACEHOLDERS + SOURCES + [None]),
    ("array", "text[]", [("ARRAY['classical_tradition']",), ("ARRAY['BPHS 1.1','classical_tradition']",), ("ARRAY['UNSOURCED']",), ("ARRAY[]::text[]",), ("ARRAY['Saravali 3']",), ("NULL",),
                         ("ARRAY['BPHS 1.1']",)]),
    ("array", "varchar(40)[]", [("ARRAY['classical_tradition']::varchar[]",), ("ARRAY['BPHS 1.1']::varchar[]",), ("NULL",)]),
    ("json", "jsonb", _json_rows(J_LACK + J_SOURCE)),
    ("json", "json", [(f"{s3._lit(v)}::json",) if v != "null" else ("'null'::json",) for v in J_LACK + J_SOURCE]),
])
def test_REAL_SQL_differential_the_per_distinct_read_counts_exactly_as_the_per_row_read_with_duplicates_and_NULLs(monkeypatch, disposable_pg, kind, ddl, vals):
    rows = (list(vals) + list(vals)[::-1] + [vals[0]] * 5 + [None if not isinstance(vals[0], tuple) else ("NULL",)] * 3)      # duplicates of every shape, plus NULLs
    s3._real(monkeypatch, disposable_pg, _rows_sql("c2_dd", ddl, rows))
    _utf8()
    new = ac.scalar(ac.ldgr_legacy_count_sql("c2_dd", "c", kind))
    old = ac.scalar(_old_per_row_count_sql("c2_dd", "c", kind))
    assert json.loads(new) == json.loads(old), (kind, ddl, new, old)
    assert json.loads(new)["rows"] == len(rows)


def test_REAL_SQL_a_ga_dashas_shaped_table_few_distinct_citations_over_many_rows(monkeypatch, disposable_pg):
    """chart_dashas.citation_ref (text) carries ~1.46M rows over a handful of distinct citations: the per-distinct read counts them by group (scaled down here)."""
    setup = ["CREATE TEMP TABLE chart_dashas (id bigint, citation_ref text) ON COMMIT DROP;",
             "INSERT INTO chart_dashas SELECT i, CASE i%5 WHEN 0 THEN 'BPHS Ch.46 (Vimshottari)' WHEN 1 THEN 'BPHS Ch.46 (Vimshottari)' WHEN 2 THEN 'Jaimini Sutras 1.2' "
             "WHEN 3 THEN 'classical_tradition' ELSE NULL END FROM generate_series(1,50000) i;"]
    s3._real(monkeypatch, disposable_pg, setup)
    _utf8()
    rec = ac.ldgr_legacy_presence("chart_dashas", "citation_ref", 50000)
    assert rec["v"] == PARTIAL and rec["ldgr_legacy"] == dict(source_column="citation_ref", rows=50000, null=10000, placeholder=10000, present=30000), rec


def test_a_read_that_times_out_is_PARTIAL_and_says_it_was_not_measured_never_PASS_never_ERRORED(monkeypatch):
    monkeypatch.setattr(ac, "ldgr_fetch_column_type", lambda t, c: "text")
    for exc in (ac.CheckTimeout("client-side timeout after 180s (psql killed): SELECT"), ac.Unknown("ERROR:  canceling statement due to statement timeout")):
        monkeypatch.setattr(ac, "scalar", lambda sql, exc=exc: (_ for _ in ()).throw(exc))
        rec = ac.ldgr_legacy_presence("chart_dashas", "citation_ref", 1460985)
        assert rec["v"] == PARTIAL and "NOT measured" in rec["measured"] and "within the timeout" in rec["measured"], rec
        assert rec["ldgr_legacy"] == dict(source_column="citation_ref", rows=1460985, incomplete="timeout")
        assert _gate(rec)["v"] == PARTIAL
    monkeypatch.setattr(ac, "scalar", lambda sql: (_ for _ in ()).throw(ac.Unknown("psql: error: connection to server failed: timeout expired")))
    with pytest.raises(ac.Unknown):                                                                   # a connection failure is not a statement timeout: ERRORED as before
        ac.ldgr_legacy_presence("chart_dashas", "citation_ref", 5)


def test_MUTATION_the_timeout_guard_and_the_group_by_are_what_keep_the_read_cheap(monkeypatch, disposable_pg):
    _mutated_legacy(monkeypatch, 'if not (isinstance(exc, CheckTimeout) or "statement timeout" in str(exc)):', "if True:")
    monkeypatch.setattr(ac, "ldgr_fetch_column_type", lambda t, c: "text")
    monkeypatch.setattr(ac, "scalar", lambda sql: (_ for _ in ()).throw(ac.CheckTimeout("client-side timeout")))
    with pytest.raises(ac.CheckTimeout):                                                              # without the guard a timeout is an ERRORED cell again
        ac.ldgr_legacy_presence("t", "c", 3)
    # the per-row form (no GROUP BY) evaluates the predicate once per row: its SQL has no `FROM d`, which the structural test above pins
    assert "GROUP BY" not in _old_per_row_count_sql("t", "c", "text")

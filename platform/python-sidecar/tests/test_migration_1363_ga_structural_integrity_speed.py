"""Migration 1363 (certification; held PR): ga_structural's registered integrity_check_sql, rewritten so chart_facts is read ONCE instead of
~330 times, with IDENTICAL SEMANTICS. A weaker check is unacceptable: this module is the proof obligation.

NEW = OLD (the live text: migration 904 as patched by 1221, then 1326; md5 fcd217e2..., 208,378 chars) with exactly two mechanical changes:
  (1) one leading `WITH gs_cf AS MATERIALIZED (SELECT <13 columns> FROM chart_facts WHERE fact_category IN (<67 categories>))`;
  (2) the relation name chart_facts -> gs_cf at the 299 uncorrelated references (alias, join and predicate text untouched). The other 31
      references (correlated sublinks / LATERAL items, which probe the base table's chart_id indexes per outer row) stay on chart_facts.

Four tiers:
  * STATIC (always runs; stdlib + the checked-in fixtures only): the OLD text is re-derived from the pre-1326 fixture and hashes to the
    production md5; NEW (the migration's $nt$ literal) hashes to the md5 the migration names; NEW is OLD with exactly the two changes (derived
    here independently: the 31 kept lines are PINNED by number and text); the 67 categories are re-derived from the text (every fact_category
    literal except the two chart_divisionals-only ones); every column the text names that chart_facts has is in the 13; no chart_facts index
    leads with fact_category (the premise); the guard / idempotent / raise logic by reading the SQL.
  * AST (runs where `pglast` is installed; skipped, loudly, otherwise): the parse tree of NEW with the WITH dropped and gs_cf renamed back is
    IDENTICAL to OLD's; every one of the 330 chart_facts references has a fact_category pin among its own AND-ed quals, none is schema-qualified,
    and the union of the renamed references' pins is exactly the CTE's 67 categories; every top-level conjunct (256) of both texts parses alone.
  * LIVE (needs PostgreSQL server binaries AND CI=true or MARSYS_PG_LIVE_1363=1; it NEVER starts a cluster on a developer machine by accident):
    applies the REAL on-disk migration to a DISPOSABLE cluster this module creates with initdb in a temp dir. OLD-vs-NEW on empty tables, on a
    clean synthetic dataset (every conjunct alone and the whole text), with the 1326 mutants, with ONE injected violation per conjunct
    (256 conjuncts x 2 injection styles, generated programmatically from the conjunct list), and a seeded random fuzz; negative controls prove the
    harness would catch a dropped category / a dropped column; an EXPLAIN check that scan nodes on chart_facts drop from ~330 to <= 40; the
    apply / guard / idempotency / serving-effect / silent-no-op tests in the style of the 1326 test.
  * Nothing here claims a timing. The census re-run after deploy is the measurement.

Verdict rule of the differential tiers (stated once): a conjunct or the whole text yields True, False or an ERROR. `True` is order independent
(every conjunct must be evaluated), so OLD True <=> NEW True is asserted STRICTLY; False vs False and bool vs bool are strict; an error in BOTH is
fine; an error in one and a False in the other is the one allowed asymmetry (SQL does not define the evaluation order of AND-ed quals or of a
cast against a filter, and a plan change may legitimately reach the erroring row first or never) and is counted, not failed. A real defect
(a missing column, a missing category, a wrong table) shows up as a strict bool mismatch or as an error on the EMPTY tables, both asserted.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import random
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_M1363 = _REPO / "platform" / "migrations" / "1363_ga_structural_integrity_single_scan_speed.sql"
_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_PRE1326 = _FIXTURES / "ga_structural_1326" / "live_integrity_check_sql_pre1326_2026-10-07.sql"
_SNAPSHOT = _FIXTURES / "pratijna_v4_snapshot" / "schema.sql"

PRE1326_MD5 = "c56f9e12b2002269eb5f27a7abc42105"
OLD_MD5, OLD_LEN = "fcd217e25127653ee28ad41c629946aa", 208378
NEW_MD5, NEW_LEN = "f49616e257f9a85de4f0cebf09fe2603", 209602
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"

# Migration 1326's single replacement (spelled here independently of the 1326 test): the pre-1326 fixture + this = the live OLD text.
_L1326_OLD_LINE = "          WHEN re.retrograde_flag = 'retrograde' THEN 'weak'\n"
_L1326_NEW_BLOCK = (
    "          -- Migration 1326 (node exclusion): the mean nodes Rahu/Ketu are always retrograde and ga_positions stores\n"
    "          -- retrograde_flag 'retrograde' for them (N-185/N-187), but the retrograde composite downgrade does NOT apply to the\n"
    "          -- nodes (their re_dignity is always 'neutral'); a node row therefore stays 'neutral'. Tara grahas are unchanged.\n"
    "          WHEN re.retrograde_flag = 'retrograde' AND a.fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN') THEN 'weak'\n"
)

# The 13 chart_facts columns the CTE carries and the 67 categories it filters on, spelled here independently of the migration.
COLS = ("fact_id", "chart_id", "ayanamsha_id", "build_id", "fact_category", "fact_subject", "fact_key", "fact_value_text",
        "fact_value_num", "fact_value_jsonb", "unit", "verification_pass_status", "computed_at")
CATS = (
    "argala_natal_matrix", "aspect_jaimini", "aspect_jaimini_per_varga", "aspect_matrix_summary", "aspect_parashari_given",
    "aspect_parashari_per_varga", "aspect_parashari_received", "aspect_received_by_special_point", "aspect_tajik", "bhadra_flag",
    "bhava_bala_aspectual", "bhava_bala_directional", "bhava_bala_lord", "bhava_bala_occupant", "bhava_bala_positional",
    "bhava_bala_temporal", "bhava_bala_total_extended", "bhava_significance_link", "chandra_bala_natal_baseline",
    "chart_center_of_gravity", "chart_cluster", "combustion_per_varga", "composite_dispositor_strength", "conjunction_per_varga",
    "conjunction_within_orb", "contradiction_pair", "convergence_count", "dispositor_chain_per_varga", "dispositor_tree",
    "graha_avastha_baladi", "graha_avastha_deepta", "graha_avastha_jagrad", "graha_avastha_lifetime_exposure_summary",
    "graha_centrality", "graha_composite_state_classification", "graha_dignity_per_varga", "graha_dispositor_chain",
    "graha_effective_dignity_modified_by_aspects", "graha_functional_class_per_ascendant", "graha_in_house_composite_strength",
    "graha_nakshatra_join", "graha_position", "graha_special_state_rollup", "graha_tri_deva_role_strength",
    "graha_vargottama_amplification_factor", "graha_yoga_karaka_flag", "graha_yuddha_per_varga",
    "house_strength_classification_rollup", "jaimini_tri_deva_role_per_graha", "kala_sarpa_per_varga", "karaka_bhava_concordance",
    "karaka_house_lord_overlap_flag", "karakatva_strength_per_significance", "lord_aspects_lord_per_varga", "lord_in_house_per_varga",
    "nakshatra_dispositor_chain", "net_argala_per_varga", "nway_config_per_varga", "panchaka_flag", "panchanga_karana",
    "panchanga_nakshatra_moon", "parivartana_per_varga", "pranic_strength_per_graha", "sambandha_grade",
    "tara_bala_natal_baseline", "vargottama_per_varga", "virodha_argala_natal_matrix",
)
DIVISIONALS_ONLY = ("varga_position", "varga_vargottama_flag")   # fact_category literals read only from chart_divisionals

# The 31 references that STAY on the base table, pinned by their 1-based line number in the OLD text and the stripped line itself. They are
# the references inside a correlated EXISTS (25), a correlated scalar sublink (3) and a LATERAL subselect (4): per-outer-row probes of the
# base table's chart_id indexes, which a CTE (no index) would turn into rescans. A change to this list is a deliberate, reviewed change.
KEPT_LINES: tuple[tuple[int, str], ...] = (
    (393, "SELECT 1 FROM chart_facts b"), (625, "SELECT 1 FROM chart_facts b"), (634, "SELECT 1 FROM chart_facts a"),
    (816, "SELECT 1 FROM chart_facts n"), (849, "FROM chart_facts p"), (1129, "FROM chart_facts p_sign"),
    (1130, "JOIN chart_facts p_comb ON p_comb.chart_id=p_sign.chart_id AND p_comb.ayanamsha_id=p_sign.ayanamsha_id"),
    (1132, "JOIN chart_facts p_retro ON p_retro.chart_id=p_sign.chart_id AND p_retro.ayanamsha_id=p_sign.ayanamsha_id"),
    (1378, "SELECT 1 FROM chart_facts a"), (1405, "SELECT 1 FROM chart_facts r"), (1420, "SELECT 1 FROM chart_facts g"),
    (1766, "SELECT 1 FROM chart_facts cf"), (1792, "SELECT 1 FROM chart_facts cf2"), (1879, "SELECT 1 FROM chart_facts b"),
    (2224, "SELECT 1 FROM chart_facts cf2"), (2399, "SELECT 1 FROM chart_facts cc2"),
    (2405, "SELECT cc1.fact_value_jsonb->>'cluster_id' FROM chart_facts cc1"), (2478, "SELECT 1 FROM chart_facts p"),
    (2504, "SELECT 1 FROM chart_facts p"), (2525, "SELECT 1 FROM chart_facts c"), (2853, "SELECT 1 FROM chart_facts gc"),
    (3147, "SELECT 1 FROM chart_facts cf"), (3170, "SELECT 1 FROM chart_facts cf2"), (3253, "SELECT 1 FROM chart_facts gd"),
    (3328, "SELECT 1 FROM chart_facts lp"), (3343, "SELECT 1 FROM chart_facts lp"), (3471, "SELECT 1 FROM chart_facts cwo"),
    (3490, "FROM chart_facts cwo"), (3554, "(SELECT count(*) FROM chart_facts gd"), (3643, "SELECT 1 FROM chart_facts gd"),
    (3710, "SELECT 1 FROM chart_facts gd"),
)
ANCHOR = "SELECT\n  -- (a) amplification_factor domain:"      # the single place in OLD where the inserted block goes


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("--"))


# The pre-1326 fixture IS the live text read 2026-10-07 (byte for byte); + migration 1326's one replacement = the live OLD text.
PRE1326_TEXT = _PRE1326.read_bytes().decode("utf-8")
OLD_TEXT = PRE1326_TEXT.replace(_L1326_OLD_LINE, _L1326_NEW_BLOCK)
SQL = _M1363.read_text(encoding="utf-8")
NEW_TEXT = re.search(r"\$nt\$(.*?)\$nt\$", SQL, re.S).group(1)
OLD_LINES = OLD_TEXT.split("\n")
KEPT_NUMS = frozenset(n for n, _ in KEPT_LINES)
_CF_WORD = re.compile(r"\bchart_facts\b")


def _derive_new_body(old: str) -> str:
    """OLD with every chart_facts CODE reference renamed to gs_cf except the pinned kept lines (comment lines are never touched)."""
    out = []
    for n, line in enumerate(old.split("\n"), 1):
        if n in KEPT_NUMS or line.lstrip().startswith("--"):
            out.append(line)
        else:
            out.append(_CF_WORD.sub("gs_cf", line))
    return "\n".join(out)


def _inserted_block() -> str:
    """What NEW inserts into OLD: everything between OLD[:k] and the (renamed) OLD[k:], k = the ANCHOR position."""
    k = OLD_TEXT.index(ANCHOR)
    assert NEW_TEXT.count(ANCHOR) == 1, "the anchor line has no chart_facts reference, so the renamed tail still starts with it"
    return NEW_TEXT[k:NEW_TEXT.index(ANCHOR)]


def _split_conjuncts(text: str) -> list[str]:
    """The top-level `NOT EXISTS ( ... )` conjuncts of the single `SELECT NOT EXISTS (..) AND ... AS integrity_passed`, comment- and
    string-aware; each is a verbatim slice of the text."""
    out: list[str] = []
    i, n, depth, start = 0, len(text), 0, None
    while i < n:
        c = text[i]
        if c == "'":
            i += 1
            while True:
                if text[i] == "'":
                    if i + 1 < n and text[i + 1] == "'":
                        i += 2
                        continue
                    break
                i += 1
            i += 1
            continue
        if text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if text.startswith("/*", i):
            i = text.index("*/", i) + 2
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0 and start is not None:
                out.append(text[start:i + 1])
                start = None
        elif depth == 0 and start is None and text.startswith("NOT EXISTS", i) and not (text[i - 1].isalnum() or text[i - 1] == "_"):
            start = i
        i += 1
    return out


def _strip_comments(text: str) -> str:
    """The text without `--` / `/* */` comments, string literals kept verbatim."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "'":
            j = i + 1
            while True:
                if text[j] == "'":
                    if j + 1 < n and text[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            i = text.index("*/", i) + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _categories_of(text: str) -> set[str]:
    """Every fact_category literal the text names (= and IN forms; the text has no other use of the column name, asserted below)."""
    cats: set[str] = set()
    for m in re.finditer(r"fact_category\s*(?:=\s*'([A-Za-z0-9_]+)'|IN\s*\(([^)]*)\))", _strip_comments(text)):
        if m.group(1):
            cats.add(m.group(1))
        else:
            cats |= set(re.findall(r"'([A-Za-z0-9_]+)'", m.group(2)))
    return cats


CONJ_OLD = _split_conjuncts(OLD_TEXT)
CONJ_NEW = _split_conjuncts(NEW_TEXT)


# -- STATIC tier --------------------------------------------------------------------------------------------------------------

def test_static_old_text_is_the_live_production_text():
    assert _md5(PRE1326_TEXT) == PRE1326_MD5, "the checked-in pre-1326 fixture is no longer the production text read 2026-10-07"
    assert _md5(OLD_TEXT) == OLD_MD5 and len(OLD_TEXT) == OLD_LEN


def test_static_old_text_is_also_what_migrations_904_1221_1326_build():
    """The fixture is a recording; this re-derives the same bytes from the migrations themselves (904's literal, 1221's four replacements, 1326)."""
    mig = _REPO / "platform" / "migrations"
    t = re.search(r"\$SQL\$(.*?)\$SQL\$", (mig / "904_nirmana_l1_ga_structural_integrity_check_scope.sql").read_text(encoding="utf-8"), re.S).group(1)
    s1221 = (mig / "1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql").read_text(encoding="utf-8")

    def lit(tag: str) -> str:
        return re.search(r"\$" + tag + r"\$(.*?)\$" + tag + r"\$", s1221, re.S).group(1)

    anchor = "\n  AS integrity_passed"
    assert t.count(anchor) == 1 and "(a29)" not in t
    t = t.replace(anchor, lit("conj").rstrip("\n") + anchor)
    for old_tag, new_tag in (("ob", "nb"), ("oc", "nc"), ("ou", "nu")):
        assert t.count(lit(old_tag)) == 1
        t = t.replace(lit(old_tag), lit(new_tag))
    assert _md5(t) == PRE1326_MD5
    s1326 = (mig / "1326_ga_structural_integrity_node_composite_exclusion.sql").read_text(encoding="utf-8")
    ol, nl = (re.search(r"\$" + g + r"\$(.*?)\$" + g + r"\$", s1326, re.S).group(1) for g in ("ol", "nl"))
    assert (ol, nl) == (_L1326_OLD_LINE, _L1326_NEW_BLOCK) and t.count(ol) == 1
    assert t.replace(ol, nl) == OLD_TEXT


def test_static_new_text_has_the_named_md5_and_length():
    assert _md5(NEW_TEXT) == NEW_MD5 and len(NEW_TEXT) == NEW_LEN
    assert NEW_TEXT != OLD_TEXT and "$nt$" not in NEW_TEXT and "$m1363$" not in NEW_TEXT


def test_static_new_is_old_with_exactly_the_block_inserted_and_the_299_renames():
    block = _inserted_block()
    k = OLD_TEXT.index(ANCHOR)
    assert OLD_TEXT.count(ANCHOR) == 1
    renamed = _derive_new_body(OLD_TEXT)
    assert NEW_TEXT == renamed[:k] + block + renamed[k:], "NEW is not (OLD with the 299 renames) plus the one inserted block"
    # reverting the rename and dropping the block gives OLD back, byte for byte
    body = NEW_TEXT[:k] + NEW_TEXT[k + len(block):]
    assert body.replace("gs_cf", "chart_facts") == OLD_TEXT
    assert body.count("gs_cf") == 299 and "gs_cf" not in OLD_TEXT


def test_static_the_inserted_block_is_comments_then_the_one_materialized_cte():
    block = _inserted_block()
    lines = block.split("\n")
    w = next(i for i, l in enumerate(lines) if l.startswith("WITH gs_cf AS MATERIALIZED ("))
    assert w >= 1 and all(l.startswith("-- ") for l in lines[:w]), "only comment lines may precede the WITH"
    with_part = "\n".join(lines[w:])
    expect = ("WITH gs_cf AS MATERIALIZED ( SELECT " + ", ".join(COLS) + " FROM chart_facts WHERE fact_category IN ( "
              + ", ".join(f"'{c}'" for c in CATS) + " ) ) ")
    assert re.sub(r"\s+", " ", with_part) == expect
    assert len(COLS) == 13 and len(CATS) == 67 and len(set(CATS)) == 67 and list(CATS) == sorted(CATS)


def test_static_exactly_31_chart_facts_references_stay_on_the_base_table_and_they_are_the_pinned_lines():
    assert len(KEPT_LINES) == 31 and len(KEPT_NUMS) == 31
    for n, text in KEPT_LINES:
        assert OLD_LINES[n - 1].strip() == text and len(_CF_WORD.findall(OLD_LINES[n - 1])) == 1, (n, OLD_LINES[n - 1])
    code_lines = [(n, l) for n, l in enumerate(OLD_LINES, 1) if _CF_WORD.search(l) and not l.lstrip().startswith("--")]
    assert len(code_lines) == 330 and all(len(_CF_WORD.findall(l)) == 1 for _n, l in code_lines), "330 references, one per code line"
    assert not [n for n, l in enumerate(OLD_LINES, 1) if _CF_WORD.search(l) and "--" in l and not l.lstrip().startswith("--")]
    renamed_lines = [n for n, l in code_lines if n not in KEPT_NUMS]
    assert len(renamed_lines) == 299
    new_body_lines = (NEW_TEXT[:OLD_TEXT.index(ANCHOR)] + NEW_TEXT[OLD_TEXT.index(ANCHOR) + len(_inserted_block()):]).split("\n")
    assert len(new_body_lines) == len(OLD_LINES)
    for n in renamed_lines:
        assert "gs_cf" in new_body_lines[n - 1] and not _CF_WORD.search(new_body_lines[n - 1]), n
    for n in KEPT_NUMS:
        assert new_body_lines[n - 1] == OLD_LINES[n - 1], n
    assert [n for n, (a, b) in enumerate(zip(OLD_LINES, new_body_lines), 1) if a != b] == renamed_lines


def test_static_the_67_categories_are_re_derived_from_the_text_and_each_is_one_the_text_pins():
    text = _strip_comments(OLD_TEXT)
    # every use of the column name is `fact_category = '<literal>'` or `fact_category IN ('<literal>', ...)` (nothing dynamic, nothing negated)
    assert len(re.findall(r"fact_category", text)) == len(re.findall(r"fact_category\s*(?:=\s*'|IN\s*\()", text)) == 340  # 330 chart_facts + 10 chart_divisionals
    cats = _categories_of(OLD_TEXT)
    assert cats == set(CATS) | set(DIVISIONALS_ONLY)
    assert set(DIVISIONALS_ONLY).isdisjoint(CATS)
    assert _categories_of(NEW_TEXT) == cats                     # the CTE adds no category the text did not already name
    # the two divisionals-only categories are read from chart_divisionals only (never from a chart_facts reference)
    for n, l in enumerate(OLD_LINES, 1):
        if any(f"'{c}'" in l for c in DIVISIONALS_ONLY):
            assert not _CF_WORD.search(l), n


def test_static_the_13_columns_cover_every_chart_facts_column_the_text_names():
    ddl = re.search(r"CREATE TABLE public\.chart_facts \((.*?)\n\);", _SNAPSHOT.read_text(encoding="utf-8"), re.S).group(1)
    table_cols = [m.group(1) for m in re.finditer(r"^\s+([a-z_]+) ", ddl, re.M)]
    assert len(table_cols) == 25 and set(COLS) <= set(table_cols)
    code = re.sub(r"'(?:[^']|'')*'", "''", _strip_comments(OLD_TEXT))        # identifiers only: no comments, no string literals
    named = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", code))
    missing = sorted((set(table_cols) & named) - set(COLS))
    assert missing == [], f"the text names chart_facts columns the CTE does not carry: {missing}"
    assert set(COLS) <= named, "a carried column the text never names (harmless, but the list is no longer 'exactly what the text names')"
    # no whole-row use of a chart_facts alias that a narrower row could change: no row_to_json / to_jsonb(alias) / ROW(alias) / DISTINCT over a star
    assert not re.search(r"row_to_json|to_json\(|to_jsonb\([a-z_0-9]+\)|\bROW\s*\(|SELECT\s+DISTINCT\s+[a-z_0-9]*\.?\*", code)


def test_static_no_chart_facts_index_leads_with_fact_category_so_a_category_only_predicate_scans_the_whole_table():
    """The premise of the speed-up, read from the pg_dump schema snapshot (PostgreSQL 15; no skip scan before 18)."""
    snap = _SNAPSHOT.read_text(encoding="utf-8")
    idx = re.findall(r"CREATE (?:UNIQUE )?INDEX (\w+) ON public\.chart_facts USING (\w+) \((.*?)\)(?: WHERE (.*?))?;", snap)
    assert len(idx) >= 10
    for name, method, cols, _where in idx:
        if method == "btree":
            assert cols.split(",")[0].strip().split(" ")[0] != "fact_category", name


def test_static_the_text_is_one_statement_of_256_uncorrelated_top_level_not_exists_conjuncts():
    assert len(CONJ_OLD) == 256 and len(CONJ_NEW) == 256
    for text, conj in ((OLD_TEXT, CONJ_OLD), (NEW_TEXT, CONJ_NEW)):
        rest = text
        for c in conj:
            assert rest.count(c) >= 1
            rest = rest.replace(c, "", 1)
        rest = re.sub(r"\s+", " ", re.sub(r"--[^\n]*", "", _strip_comments(rest))).strip()
        assert re.fullmatch(r"(?:WITH gs_cf AS MATERIALIZED \(.*?\) )?SELECT (?:AND )*AS integrity_passed", rest), rest[:300]
    # conjunct by conjunct: NEW's is OLD's with only the rename applied
    for k, (a, b) in enumerate(zip(CONJ_OLD, CONJ_NEW)):
        assert b.replace("gs_cf", "chart_facts") == a, k
    assert sum(1 for a, b in zip(CONJ_OLD, CONJ_NEW) if a != b) >= 200
    assert len(re.findall(r"\bchart_divisionals\b", OLD_TEXT)) == len(re.findall(r"\bchart_divisionals\b", NEW_TEXT)) >= 10
    assert len(re.findall(r"\bga_yoga_firings\b", OLD_TEXT)) == len(re.findall(r"\bga_yoga_firings\b", NEW_TEXT)) >= 1


def test_static_no_arbitrary_choice_reads_a_renamed_reference():
    """Every LIMIT in the text sits in a correlated sublink whose chart_facts reference stays on the base table (uu2's p = line 849, the
    conjunction_within_orb scalar's cwo = line 3490), so the one ORDER BY and the one LIMIT without ORDER BY read exactly the rows they read before."""
    limits = [n for n, l in enumerate(OLD_LINES, 1) if re.match(r"\s*LIMIT\b", l)]
    assert limits == [853, 3501]
    assert not re.search(r"\bDISTINCT ON\b|\bOFFSET\b|\bFETCH\b|random\(|\bnow\(\)|clock_timestamp", _strip_comments(OLD_TEXT))
    assert 849 in KEPT_NUMS and 3490 in KEPT_NUMS


def test_static_migration_literals_equal_the_independently_spelled_ones():
    code = _code(_M1363)
    assert f"c_old_md5  constant text := '{OLD_MD5}'" in code and f"c_new_md5  constant text := '{NEW_MD5}'" in code
    assert SQL.count("$nt$") == 2


def test_static_one_guarded_update_of_integrity_check_sql_only_lock_timeout_first():
    code = _code(_M1363)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert code.count("UPDATE asset_registry") == 1
    assert "SET integrity_check_sql = c_new_text" in code
    assert "AND md5(integrity_check_sql) = c_old_md5;" in code
    assert code.count("WHERE asset_id = 'ga_structural'") >= 2
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code.replace("BEGIN\n", ""))
    assert not re.search(r"^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b", code, re.I | re.M)
    assert code.count("RAISE EXCEPTION") == 1 and "update did not take" in code
    assert "is not the text this migration was written against" in code and "NO-OP" in code and "already carries the single-scan rewrite" in code
    assert "FOR UPDATE" in code and "IS DISTINCT FROM c_new_md5" in code


def test_static_the_notice_noop_and_the_idempotent_noop_come_before_the_update_and_the_raise_after_it():
    code = _code(_M1363)
    i_new, i_foreign = code.index("v_md5 = c_new_md5"), code.index("v_md5 IS DISTINCT FROM c_old_md5")
    i_upd, i_raise = code.index("UPDATE asset_registry"), code.index("RAISE EXCEPTION")
    assert i_new < i_upd and i_foreign < i_upd < i_raise
    assert code.count("RETURN;") == 3 and code.count("RAISE NOTICE") == 3


def test_static_header_states_finding_rewrite_equivalence_trigger_effect_verification_rollback():
    flat = re.sub(r"\s+", " ", SQL[:SQL.index("SET LOCAL lock_timeout")].replace("--", " "))
    for needle in ("THE PROBLEM", "THE DOMINANT SCAN", "THE REWRITE", "IDENTICAL SEMANTICS", "WHY NO INDEX", "EXPECTED EFFECT",
                   "NOT a measurement", "GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH", "SERVING EFFECT AT APPLY",
                   "nirmana_registry_receipt_invalidation", "STALES ga_structural's freshness rows", "VERIFICATION BY PRODUCTION STRUCTURE",
                   "ROLLBACK", OLD_MD5, NEW_MD5, str(NEW_LEN)):
        assert needle in flat, needle


def test_static_is_a_routine_migration_with_a_unique_number():
    mig = _REPO / "platform" / "migrations"
    assert _M1363.name == "1363_ga_structural_integrity_single_scan_speed.sql"
    assert sorted(p.name for p in mig.glob("1363_*.sql")) == [_M1363.name]
    ts = (_REPO / "platform" / "scripts" / "migrate.ts").read_text(encoding="utf-8")
    assert _M1363.name not in ts, "a routine migration must not be on the protected list"


# -- AST tier (pglast; skipped where it is not installed) -------------------------------------------------------------------------

def _pglast():
    return pytest.importorskip("pglast", reason="AST tier needs pglast (local/developer proof; not in requirements-ci.txt)")


def _strip_locations(node):
    if isinstance(node, dict):
        return {k: _strip_locations(v) for k, v in node.items() if k != "location" and not k.endswith(("_location", "list_start", "list_end"))}   # source offsets only
    if isinstance(node, list):
        return [_strip_locations(v) for v in node]
    return node


def _drop_with_and_rename_back(node, counter):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "RangeVar" and isinstance(v, dict) and v.get("relname") == "gs_cf":
                counter[0] += 1
                v = dict(v, relname="chart_facts")
            out[k] = _drop_with_and_rename_back(v, counter)
        return out
    if isinstance(node, list):
        return [_drop_with_and_rename_back(v, counter) for v in node]
    return node


def test_ast_parse_trees_identical_after_dropping_the_with_and_renaming_gs_cf_back():
    pg = _pglast()
    from pglast.parser import parse_sql_json
    old = json.loads(parse_sql_json(OLD_TEXT))["stmts"]
    new = json.loads(parse_sql_json(NEW_TEXT))["stmts"]
    assert len(old) == len(new) == 1
    new_select = new[0]["stmt"]["SelectStmt"]
    with_clause = new_select.pop("withClause")
    assert len(with_clause["ctes"]) == 1 and not with_clause.get("recursive")
    cte = with_clause["ctes"][0]["CommonTableExpr"]
    assert cte["ctename"] == "gs_cf" and cte["ctematerialized"] == "CTEMaterializeAlways"
    cte_sel = cte["ctequery"]["SelectStmt"]
    assert [t["ResTarget"]["val"]["ColumnRef"]["fields"][-1]["String"]["sval"] for t in cte_sel["targetList"]] == list(COLS)
    assert len(cte_sel["fromClause"]) == 1 and cte_sel["fromClause"][0]["RangeVar"]["relname"] == "chart_facts"
    assert "schemaname" not in cte_sel["fromClause"][0]["RangeVar"]
    counter = [0]
    back = _drop_with_and_rename_back(new[0], counter)
    assert counter[0] == 299
    assert _strip_locations(back["stmt"]) == _strip_locations(old[0]["stmt"]), "parse trees differ beyond the WITH and the rename"
    assert pg is not None


def test_ast_every_conjunct_of_both_texts_parses_alone():
    pg = _pglast()
    prefix = _inserted_block()
    for k, (a, b) in enumerate(zip(CONJ_OLD, CONJ_NEW)):
        pg.parse_sql("SELECT " + a + " AS ok")
        pg.parse_sql(prefix + "SELECT " + b + " AS ok")


def test_ast_every_chart_facts_reference_has_a_category_pin_and_the_renamed_pins_are_exactly_the_cte_categories():
    pg = _pglast()
    from pglast import ast, enums
    from pglast.visitors import Visitor

    def flatten_and(n, out):
        if n is None:
            return
        if isinstance(n, ast.BoolExpr) and n.boolop == enums.BoolExprType.AND_EXPR:
            for a in n.args:
                flatten_and(a, out)
        else:
            out.append(n)

    def const_str(n):
        if isinstance(n, ast.A_Const) and isinstance(n.val, ast.String):
            return n.val.sval
        if isinstance(n, ast.TypeCast):
            return const_str(n.arg)
        return None

    def cname(cr):
        return tuple(f.sval if isinstance(f, ast.String) else "*" for f in cr.fields)

    def pin_of(atom, alias, only_rel):
        if not isinstance(atom, ast.A_Expr) or atom.name[0].sval != "=":
            return None

        def is_cat(c):
            if not isinstance(c, ast.ColumnRef):
                return False
            cn = cname(c)
            return (cn == (alias, "fact_category")) if len(cn) == 2 else (only_rel and cn == ("fact_category",))

        if atom.kind == enums.A_Expr_Kind.AEXPR_OP and is_cat(atom.lexpr):
            s = const_str(atom.rexpr)
            return {s} if s is not None else None
        if atom.kind == enums.A_Expr_Kind.AEXPR_OP and is_cat(atom.rexpr):
            s = const_str(atom.lexpr)
            return {s} if s is not None else None
        if atom.kind == enums.A_Expr_Kind.AEXPR_IN and is_cat(atom.lexpr) and isinstance(atom.rexpr, tuple):
            vals = [const_str(x) for x in atom.rexpr]
            return set(vals) if all(v is not None for v in vals) else None
        return None

    refs: list[tuple[int, set[str] | None, str | None]] = []   # (location, pin set, schema)

    def walk_select(sel):
        quals: list = []
        flatten_and(sel.whereClause, quals)
        rels, inner_on, outer_on = [], [], []

        def collect(fr, nullable):
            if isinstance(fr, ast.RangeVar):
                rels.append((fr, nullable))
            elif isinstance(fr, ast.JoinExpr):
                lq: list = []
                flatten_and(fr.quals, lq)
                if fr.jointype == enums.JoinType.JOIN_INNER:
                    inner_on.extend(lq)
                else:
                    outer_on.append(lq)
                collect(fr.larg, nullable or fr.jointype in (enums.JoinType.JOIN_RIGHT, enums.JoinType.JOIN_FULL))
                collect(fr.rarg, nullable or fr.jointype in (enums.JoinType.JOIN_LEFT, enums.JoinType.JOIN_FULL))

        for fr in (sel.fromClause or ()):
            collect(fr, False)
        only_rel = len(rels) + sum(1 for fr in (sel.fromClause or ()) if not isinstance(fr, (ast.RangeVar, ast.JoinExpr))) == 1
        for rv, nullable in rels:
            if rv.relname != "chart_facts":
                continue
            alias = rv.alias.aliasname if rv.alias else rv.relname
            atoms = list(quals) + list(inner_on) + ([a for lq in outer_on for a in lq] if nullable else [])
            pins = [p for p in (pin_of(a, alias, only_rel) for a in atoms) if p is not None]
            refs.append((rv.location, set.intersection(*pins) if pins else None, rv.schemaname))

    class V(Visitor):
        def visit_SelectStmt(self, ancestors, node):
            if node.op == enums.SetOperation.SETOP_NONE:
                walk_select(node)

    V()(pg.parse_sql(OLD_TEXT)[0].stmt)
    assert len(refs) == 330
    assert [r for r in refs if r[1] is None] == [], "a chart_facts reference without a fact_category pin among its own AND-ed quals"
    assert [r for r in refs if r[2]] == [], "a schema-qualified chart_facts reference"
    renamed_pins: set[str] = set()
    n_renamed = 0
    for loc, pin, _schema in refs:
        line = OLD_TEXT.encode("utf-8").count(b"\n", 0, loc) + 1
        if line not in KEPT_NUMS:
            n_renamed += 1
            renamed_pins |= pin
        else:
            assert pin <= set(CATS) | set(DIVISIONALS_ONLY)
    assert n_renamed == 299
    assert renamed_pins == set(CATS), "the CTE's categories must be exactly the union of the renamed references' pins"


# -- LIVE tier: disposable PostgreSQL --------------------------------------------------------------------------------------------

def _find_pg_bin() -> Path | None:
    cands: list[Path] = []
    if os.environ.get("PG_BIN"):
        cands.append(Path(os.environ["PG_BIN"]))
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            return c
    return None


@pytest.fixture(scope="module")
def pg_cluster():
    in_ci = os.environ.get("CI", "").lower() in ("true", "1")
    if not in_ci and os.environ.get("MARSYS_PG_LIVE_1363") != "1":
        pytest.skip("live tier runs in CI (CI=true) or with MARSYS_PG_LIVE_1363=1; it never starts a cluster by accident")
    # In CI the live tier is the proof of equivalence: a missing driver or missing server binaries is a FAILURE, never a silent skip.
    try:
        import psycopg
    except ImportError:
        if in_ci:
            pytest.fail("CI=true but psycopg is not importable: the live tier of migration 1363 cannot run (it must not skip in CI)")
        pytest.skip("psycopg not installed")
    binp = _find_pg_bin()
    if binp is None:
        if in_ci or os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail("no PostgreSQL server binaries (initdb/pg_ctl) found and the live tier must run here (CI=true or REQUIRE_PG_BINARIES=1); set PG_BIN")
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1363pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m62", dir="/tmp"))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--no-sync"],
                   check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses='' -c unix_socket_directories={sockdir} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        yield {"port": port, "sock": str(sockdir), "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(sockdir, ignore_errors=True)


_n = 0


@pytest.fixture()
def db(pg_cluster):
    global _n
    _n += 1
    name = f"u{_n}"
    psycopg, port, sock = pg_cluster["psycopg"], pg_cluster["port"], pg_cluster["sock"]
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect(autocommit: bool = False):
        return psycopg.connect(host=sock, port=port, user="postgres", dbname=name, autocommit=autocommit)

    yield connect
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


# chart_facts / chart_divisionals / ga_yoga_firings: the production column names and types the text reads (the same fixture DDL the 1326
# test uses; chart_facts's 25 columns equal the pg_dump snapshot); NOT NULL text columns the check never reads carry defaults.
_FIXTURE_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL, depends_on text[], is_active boolean NOT NULL DEFAULT true,
    target_table text, count_sql text, target_floor integer, size_sql text, volume_explanation text,
    natural_key_partition text, health_probe text, integrity_check_sql text, asset_kind text, asset_type text,
    scope text, has_writer boolean);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL, chart_id uuid NOT NULL, freshness_state text NOT NULL,
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb, observed_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z',
    PRIMARY KEY (asset_id, chart_id));
CREATE TABLE chart_facts (
    fact_id text NOT NULL DEFAULT gen_random_uuid()::text, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL,
    build_id uuid NOT NULL DEFAULT '00000000-0000-4000-8000-000000000001', fact_category text NOT NULL, fact_subject text NOT NULL,
    fact_key text NOT NULL, fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb, unit text,
    citation_ref text NOT NULL DEFAULT '', citation_human text NOT NULL DEFAULT '', source_calculation text NOT NULL DEFAULT '',
    verification_pass_status text NOT NULL DEFAULT 'two_pass_verified', engine_version text NOT NULL DEFAULT 'test',
    salience_formula_ver text, computed_at timestamptz NOT NULL DEFAULT now(), tolerance_arcsec double precision,
    near_sign_boundary_flag boolean, near_nakshatra_boundary_flag boolean, vargottama_flag_at_point boolean,
    formula_provenance_text text, cross_ayanamsha_divergence_arcsec double precision, formula_id text);
CREATE TABLE chart_divisionals (
    id uuid NOT NULL DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, graha text, ayanamsha_id text NOT NULL, varga text NOT NULL,
    sign text, sign_number smallint, degree_in_sign numeric, house smallint, vargottama boolean,
    source_citation text NOT NULL DEFAULT '', build_id text NOT NULL DEFAULT 'b', created_at timestamptz NOT NULL DEFAULT now(),
    fact_category text, fact_key text, fact_value_text text, fact_value_num numeric, fact_subject text, build_id_uuid uuid,
    verification_pass_status text, engine_version text, citation_ref text, citation_human text, source_calculation text,
    computed_at timestamptz, tolerance_arcsec numeric, near_sign_boundary_flag boolean, near_nakshatra_boundary_flag boolean,
    vargottama_flag_at_point boolean, formula_provenance_text text, cross_ayanamsha_divergence_arcsec numeric);
CREATE TABLE ga_yoga_firings (
    id serial PRIMARY KEY, chart_id uuid NOT NULL, build_id uuid, ayanamsha_id text NOT NULL, yoga_canonical_id text NOT NULL,
    fired boolean NOT NULL, constituent_fact_ids jsonb, constituent_planets jsonb, constituent_houses jsonb, strength numeric,
    is_partial boolean, bhanga_active boolean, computed_at timestamptz);
CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE asset_freshness SET freshness_state = 'stale',
         reasons = CASE WHEN reasons ? 'registry_changed' THEN reasons ELSE reasons || '["registry_changed"]'::jsonb END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END; $$;
CREATE TRIGGER nirmana_registry_receipt_invalidation
AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type,
                scope, has_writer, is_active, target_table ON asset_registry
FOR EACH ROW WHEN (OLD IS DISTINCT FROM NEW) EXECUTE FUNCTION nirmana_invalidate_registry_receipts();
"""

_CF_INSERT = ("INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key, fact_value_text, "
              "fact_value_num, fact_value_jsonb) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)")
_BUILD_A, _BUILD_B = "00000000-0000-4000-8000-00000000000a", "00000000-0000-4000-8000-00000000000b"


def _fact(c, cat: str, subj: str, key: str, text: str | None = None, num=None, js: dict | None = None, chart: str = CANON):
    c.execute("INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_text, "
              "fact_value_num, fact_value_jsonb) VALUES (%s,'lahiri',%s,%s,%s,%s,%s,%s)",
              (chart, cat, subj, key, text, num, json.dumps(js) if js is not None else None))


_EXALT = {"SUN": "Aries", "MOON": "Taurus", "MAR": "Capricorn", "MER": "Virgo", "JUP": "Cancer", "VEN": "Pisces", "SAT": "Libra"}
_DEBIL = {"SUN": "Libra", "MOON": "Scorpio", "MAR": "Cancer", "MER": "Pisces", "JUP": "Capricorn", "VEN": "Virgo", "SAT": "Aries"}


def _graha(c, subj: str, sign: str, retro: str, composite: str, *, comb: str = "not_combust", rollup_retro: bool | None = None):
    _fact(c, "graha_position", subj, "sign", sign)
    _fact(c, "graha_position", subj, "combustion_state", comb)
    _fact(c, "graha_position", subj, "retrograde_flag", retro)
    _fact(c, "graha_composite_state_classification", subj, "composite_state", composite)
    r = (retro == "retrograde") if rollup_retro is None else rollup_retro
    _fact(c, "graha_special_state_rollup", subj, "is_combust", "true" if comb == "combust" else "false")
    _fact(c, "graha_special_state_rollup", subj, "is_retrograde", "true" if r else "false")
    _fact(c, "graha_special_state_rollup", subj, "is_debilitated", "true" if _DEBIL.get(subj) == sign else "false")
    _fact(c, "graha_special_state_rollup", subj, "is_exalted", "true" if _EXALT.get(subj) == sign else "false")


# The post-#3205 world the OLD text is written for: the nodes store 'retrograde' and stay 'neutral'; Mars and the Moon are direct, neutral.
_CLEAN = [("RAH_MEAN", "Gemini", "retrograde", "neutral"), ("KET_MEAN", "Sagittarius", "retrograde", "neutral"),
          ("MAR", "Taurus", "direct", "neutral"), ("MOON", "Gemini", "direct", "neutral")]


def _setup(connect, grahas: list[tuple] | None = None, text: str = OLD_TEXT, with_row: bool = True):
    with connect() as c:
        c.execute(_FIXTURE_DDL)
        if with_row:
            c.execute("INSERT INTO asset_registry (asset_id, layer, integrity_check_sql, target_table, scope, has_writer) "
                      "VALUES ('ga_structural','ganita',%s,'chart_facts','per_chart',true)", (text,))
            c.execute("INSERT INTO asset_registry (asset_id, layer, integrity_check_sql) VALUES ('ga_other','ganita','SELECT true')")
            c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES "
                      "('ga_structural', %s, 'fresh'), ('ga_structural', %s, 'fresh'), ('ga_other', %s, 'fresh')", (CANON, OTHER, CANON))
        for g in grahas or []:
            _graha(c, *g[:4], **(g[4] if len(g) > 4 else {}))
        c.commit()


def _apply(connect, notices: list[str] | None = None):
    conn = connect()
    if notices is not None:
        conn.add_notice_handler(lambda d: notices.append(d.message_primary))
    try:
        conn.execute(_M1363.read_text(encoding="utf-8"))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _q(connect, sql, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


def _check(connect, text: str) -> bool:
    return _q(connect, text)[0][0]


def _txt(connect) -> str:
    return _q(connect, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_structural'")[0][0]


def _outcome(conn, sql: str, psycopg):
    """('ok', bool) or ('err', sqlstate). conn must be autocommit so an error leaves the session usable."""
    try:
        return ("ok", conn.execute(sql).fetchone()[0])
    except psycopg.Error as exc:
        return ("err", getattr(exc, "sqlstate", None) or type(exc).__name__)


def _compare(old, new) -> str:
    """'same' | 'both_err' | 'allowed_asymmetry' (an error in one side, False in the other) | 'MISMATCH'."""
    if old[0] == "ok" and new[0] == "ok":
        return "same" if old[1] == new[1] else "MISMATCH"
    if old[0] == "err" and new[0] == "err":
        return "both_err"
    ok_side = old if old[0] == "ok" else new
    return "allowed_asymmetry" if ok_side[1] is False else "MISMATCH"       # an error against a True can never be order dependent


_PREFIX = _inserted_block()


def _sql_old(k: int) -> str:
    return "SELECT " + CONJ_OLD[k] + " AS ok"


def _sql_new(k: int, prefix: str = _PREFIX) -> str:
    return prefix + "SELECT " + CONJ_NEW[k] + " AS ok"


def _differential(conn, psycopg, prefix: str = _PREFIX, only: list[int] | None = None) -> dict:
    tally = {"same_true": 0, "same_false": 0, "both_err": 0, "allowed_asymmetry": 0, "MISMATCH": 0}
    bad: list[tuple] = []
    for k in (only if only is not None else range(len(CONJ_OLD))):
        o, n = _outcome(conn, _sql_old(k), psycopg), _outcome(conn, _sql_new(k, prefix), psycopg)
        verdict = _compare(o, n)
        if verdict == "same":
            tally["same_true" if o[1] else "same_false"] += 1
        else:
            tally[verdict] += 1
        if verdict == "MISMATCH":
            bad.append((k, o, n))
    tally["bad"] = bad
    return tally


def _whole(conn, psycopg, text: str):
    return _outcome(conn, text, psycopg)


# -- synthetic injections and fuzz data -----------------------------------------------------------------------------------------

_STRINGS = sorted({s for s in (m.group(1).replace("''", "'") for m in re.finditer(r"'((?:[^']|'')*)'", _strip_comments(OLD_TEXT)))
                   if 0 < len(s) <= 40 and "\n" not in s})
_JSON_KEYS = sorted(set(re.findall(r"->>?\s*'([A-Za-z_][A-Za-z0-9_]*)'", _strip_comments(OLD_TEXT))))
_NUMS = [None, 0, 0.0, 0.25, 0.5, 0.75, 1, 1.0, 2.0, 3, 4, 5, 7, 9, 12, -1, 33.3, 120, 987654.321]


def _inject_garbage(c, cats: list[str], tag: str) -> int:
    """Deterministic style 1: per category, one row per chart (canonical and another) that obeys no domain the text states."""
    n = 0
    for cat in cats:
        for chart in (CANON, OTHER):
            c.execute(_CF_INSERT, (f"{tag}_{n}", chart, "lahiri", _BUILD_A, cat, "zzz_SUBJ", "zzz_key", "zzz", 987654.321,
                                   json.dumps({"varga": "D1", "sign": "Zzz", "house": 99, "score": -5})))
            n += 1
    return n


def _random_rows(rnd: random.Random, c, cats: list[str], tag: str, per_cat: tuple[int, int] = (2, 5)) -> int:
    """Style 2 / fuzz: rows drawn from the text's own vocabulary (its string literals, its json keys, its numeric constants)."""
    n = 0
    for cat in cats:
        for _ in range(rnd.randint(*per_cat)):
            js = None
            if rnd.random() < 0.8:
                js = {rnd.choice(_JSON_KEYS): rnd.choice([rnd.choice(_STRINGS), rnd.choice(_NUMS), rnd.randint(1, 12), None,
                                                          [rnd.choice(_STRINGS) for _ in range(rnd.randint(0, 3))]])
                      for _ in range(rnd.randint(0, 4))}
            c.execute(_CF_INSERT, (f"{tag}_{n}", rnd.choice((CANON, OTHER)), rnd.choice(("lahiri", "raman")), rnd.choice((_BUILD_A, _BUILD_B)),
                                   cat, rnd.choice(_STRINGS), rnd.choice(_STRINGS), rnd.choice([None, rnd.choice(_STRINGS)]),
                                   rnd.choice(_NUMS), json.dumps(js) if js is not None else None))
            n += 1
    return n


def _inject_other_tables(c, text: str, tag: str) -> None:
    if re.search(r"\bchart_divisionals\b", text):
        for chart in (CANON, OTHER):
            c.execute("INSERT INTO chart_divisionals (chart_id, graha, ayanamsha_id, varga, sign, sign_number, degree_in_sign, house, vargottama, "
                      "source_citation, fact_category, fact_key, fact_value_text, fact_value_num, fact_subject) VALUES "
                      "(%s,'Sun','lahiri','D1','Zzz',99,400,99,true,%s,'varga_position','zzz','zzz',1,'D1_SUN')", (chart, tag))
    if re.search(r"\bga_yoga_firings\b", text):
        c.execute("INSERT INTO ga_yoga_firings (chart_id, ayanamsha_id, yoga_canonical_id, fired, constituent_fact_ids, constituent_planets, "
                  "constituent_houses, strength) VALUES (%s,'lahiri',%s,true,'[\"nope\"]'::jsonb,'[\"Zzz\"]'::jsonb,'[99]'::jsonb,5)", (CANON, tag))


def _clear_injections(c, tag: str) -> None:
    c.execute("DELETE FROM chart_facts WHERE fact_id LIKE %s", (tag + "\\_%",))
    c.execute("DELETE FROM chart_divisionals WHERE source_citation = %s", (tag,))
    c.execute("DELETE FROM ga_yoga_firings WHERE yoga_canonical_id = %s", (tag,))


def _conjunct_categories(k: int) -> list[str]:
    return sorted(_categories_of(CONJ_OLD[k]) & set(CATS))


# -- the live tier's own inputs (checked without a cluster) --------------------------------------------------------------------

def test_static_the_differential_harness_inputs_are_sane():
    assert len(_STRINGS) > 300 and len(_JSON_KEYS) > 20
    assert all(_conjunct_categories(k) or re.search(r"chart_divisionals|ga_yoga_firings", CONJ_OLD[k]) for k in range(256)), \
        "a conjunct that reads no category and no other table cannot be injected"
    covered = set().union(*(set(_conjunct_categories(k)) for k in range(256)))
    assert covered == set(CATS), "every one of the 67 categories is injected by at least one conjunct"
    assert _compare(("ok", True), ("ok", True)) == "same" and _compare(("ok", True), ("ok", False)) == "MISMATCH"
    assert _compare(("err", "22P02"), ("err", "22003")) == "both_err"
    assert _compare(("ok", False), ("err", "22P02")) == "allowed_asymmetry" and _compare(("ok", True), ("err", "22P02")) == "MISMATCH"


# -- LIVE: equivalence ------------------------------------------------------------------------------------------------------------

def test_live_empty_tables_old_and_new_are_true_whole_text_and_every_conjunct_alone(db, pg_cluster):
    psycopg = pg_cluster["psycopg"]
    _setup(db)
    with db(autocommit=True) as c:
        assert _whole(c, psycopg, OLD_TEXT) == ("ok", True)
        assert _whole(c, psycopg, NEW_TEXT) == ("ok", True)          # parses, resolves every gs_cf column, plans, and holds
        t = _differential(c, psycopg)
    assert t["bad"] == [] and t["same_true"] == 256, t        # all 256 conjuncts true on both, none errored (an undefined column would error here)


def test_live_clean_synthetic_dataset_old_and_new_agree_whole_text_and_conjunct_by_conjunct(db, pg_cluster):
    psycopg = pg_cluster["psycopg"]
    _setup(db, _CLEAN)
    with db(autocommit=True) as c:
        assert _whole(c, psycopg, OLD_TEXT) == ("ok", True)
        assert _whole(c, psycopg, NEW_TEXT) == ("ok", True)
        t = _differential(c, psycopg)
    assert t["bad"] == [] and t["same_true"] == 256, t


def test_live_the_1326_mutants_and_b4_cases_get_the_same_verdict_from_old_and_new(db, pg_cluster):
    _setup(db, _CLEAN)
    mutants = {
        "a_amplification_domain": "INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) "
                                  f"VALUES ('{CANON}','lahiri','graha_vargottama_amplification_factor','SUN','amplification_factor',2.0)",
        "k_yuddha_names_a_node": "INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_jsonb) "
                                 f"VALUES ('{CANON}','lahiri','graha_yuddha_per_varga','D1_MAR_VEN','within_1deg',"
                                 "'{\"graha1\":\"Rahu\",\"graha2\":\"Mars\",\"orb_deg\":0.5}'::jsonb)",
        "a4_composite_domain": "UPDATE chart_facts SET fact_value_text='bogus' WHERE fact_category='graha_composite_state_classification' "
                               "AND fact_subject='MOON'",
        "b7_combust_rollup": "UPDATE chart_facts SET fact_value_text='true' WHERE fact_category='graha_special_state_rollup' "
                             "AND fact_key='is_combust' AND fact_subject='MOON'",
        "c7_node_rollup_disagrees_with_flag": "UPDATE chart_facts SET fact_value_text='false' WHERE "
                                              "fact_category='graha_special_state_rollup' AND fact_key='is_retrograde' "
                                              "AND fact_subject='RAH_MEAN'",
        "a7_rollup_domain": "UPDATE chart_facts SET fact_value_text='maybe' WHERE fact_category='graha_special_state_rollup' "
                            "AND fact_key='is_exalted' AND fact_subject='MOON'",
        "b4_node_wrongly_downgraded": "UPDATE chart_facts SET fact_value_text='weak' WHERE fact_category='graha_composite_state_classification' "
                                      "AND fact_subject='RAH_MEAN'",
        "b4_tara_retrograde_not_downgraded": "UPDATE chart_facts SET fact_value_text='retrograde' WHERE fact_category='graha_position' "
                                             "AND fact_key='retrograde_flag' AND fact_subject='MAR'",
    }
    with db() as c:
        for name, sql in mutants.items():
            c.execute("SAVEPOINT m")
            c.execute(sql)
            old, new = c.execute(OLD_TEXT).fetchone()[0], c.execute(NEW_TEXT).fetchone()[0]
            assert old is False and new is False, f"mutant {name}: old={old} new={new}"
            c.execute("ROLLBACK TO SAVEPOINT m")
            assert c.execute(OLD_TEXT).fetchone()[0] is True and c.execute(NEW_TEXT).fetchone()[0] is True, name
    cases = {   # the (b4) decision tree: both texts must agree on each, and on the expected verdict
        "exalted_retro_is_well_placed": (("MAR", "Capricorn", "retrograde", "well_placed"), True),
        "exalted_retro_weak_is_wrong": (("MAR", "Capricorn", "retrograde", "weak"), False),
        "own_sign_direct_well_placed": (("MAR", "Aries", "direct", "well_placed"), True),
        "debilitated_plain": (("MAR", "Cancer", "direct", "debilitated"), True),
        "debilitated_combust_severe": (("MAR", "Cancer", "direct", "severely_afflicted", {"comb": "combust"}), True),
        "combust_afflicted": (("MAR", "Taurus", "direct", "afflicted", {"comb": "combust"}), True),
        "combust_wrong": (("MAR", "Taurus", "direct", "neutral", {"comb": "combust"}), False),
        "direct_neutral_wrong_weak": (("MAR", "Taurus", "direct", "weak"), False),
        "tara_retro_downgraded": (("MAR", "Taurus", "retrograde", "weak"), True),
    }
    for name, (g, ok) in cases.items():
        with db() as c:
            c.execute("DELETE FROM chart_facts WHERE fact_subject='MAR'")
            _graha(c, g[0], g[1], g[2], g[3], **(g[4] if len(g) > 4 else {}))
            c.commit()
        assert _check(db, OLD_TEXT) is ok and _check(db, NEW_TEXT) is ok, name


def test_live_one_injected_violation_per_conjunct_old_and_new_agree(db, pg_cluster):
    """256 conjuncts x 2 injection styles, both generated from the conjunct list: (1) deterministic garbage in every category the conjunct
    pins (two charts), (2) seeded vocabulary-drawn rows in those categories; chart_divisionals / ga_yoga_firings rows for conjuncts that
    read them. Each conjunct is run ALONE in OLD and in NEW (NEW with the real CTE) on the same data."""
    psycopg = pg_cluster["psycopg"]
    _setup(db, _CLEAN)
    totals = {"same_true": 0, "same_false": 0, "both_err": 0, "allowed_asymmetry": 0, "style1_false": 0, "style2_false": 0}
    bad: list = []
    with db(autocommit=True) as c:
        for style in (1, 2):
            for k in range(256):
                tag = f"inj{style}_{k}"
                cats = _conjunct_categories(k)
                if style == 1:
                    _inject_garbage(c, cats, tag)
                else:
                    _random_rows(random.Random(1363_000 + k), c, cats, tag, (3, 6))
                _inject_other_tables(c, CONJ_OLD[k], tag)
                t = _differential(c, psycopg, only=[k])
                _clear_injections(c, tag)
                for key in totals:
                    totals[key] += t[key]
                bad += t["bad"]
                totals[f"style{style}_false"] += t["same_false"]
    assert bad == [], bad[:5]
    # non-vacuity: the injections really make conjuncts bite (False in BOTH texts), they are not all errors or all true
    assert totals["style1_false"] >= 10 and totals["style2_false"] >= 3 and totals["same_false"] >= 15, totals


@pytest.mark.parametrize("seed", range(6))
def test_live_seeded_random_fuzz_per_conjunct_and_whole_text(db, pg_cluster, seed):
    psycopg = pg_cluster["psycopg"]
    _setup(db)
    rnd = random.Random(62_000 + seed)
    with db() as c:
        _random_rows(rnd, c, list(CATS), "fz", (2, 6))
        _inject_other_tables(c, "chart_divisionals ga_yoga_firings", "fz")
        c.commit()
    with db(autocommit=True) as c:
        c.execute("ANALYZE")
        t = _differential(c, psycopg)
        o, n = _whole(c, psycopg, OLD_TEXT), _whole(c, psycopg, NEW_TEXT)
    assert t["bad"] == [], t["bad"][:5]
    assert _compare(o, n) != "MISMATCH", (o, n)
    # random data should make a good share of the conjuncts decide (False): the seed is not vacuous
    assert t["same_false"] + t["same_true"] >= 30, {k: v for k, v in t.items() if k != "bad"}


def test_live_negative_control_the_harness_catches_a_dropped_category_and_a_dropped_column(db, pg_cluster):
    """The differential would notice a CTE that misses a category (OLD sees the violating row, NEW does not) or a column (analysis error)."""
    psycopg = pg_cluster["psycopg"]
    _setup(db, _CLEAN)
    cat = "graha_vargottama_amplification_factor"
    no_cat = _PREFIX.replace(f"'{cat}'", "'zz_dropped_category'")
    no_col = _PREFIX.replace("fact_value_num, fact_value_jsonb, unit,", "fact_value_num, unit,")
    assert no_cat != _PREFIX and no_col != _PREFIX
    with db() as c:
        c.execute("INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) "
                  f"VALUES ('{CANON}','lahiri','{cat}','SUN','amplification_factor',2.0)")
        c.commit()
    with db(autocommit=True) as c:
        assert _whole(c, psycopg, OLD_TEXT) == ("ok", False)
        assert _whole(c, psycopg, NEW_TEXT) == ("ok", False)
        dropped = _whole(c, psycopg, NEW_TEXT.replace(_PREFIX, no_col))
        assert dropped[0] == "err" and dropped[1] == "42703", dropped          # undefined_column, raised at analysis whatever the data
        ks = [k for k in range(256) if cat in _conjunct_categories(k)]
        t = _differential(c, psycopg, no_cat, only=ks)
    assert t["MISMATCH"] >= 1, "the per-conjunct differential did not notice the dropped category"


def _count_nodes(plan: dict, pred) -> int:
    n = 1 if pred(plan) else 0
    for ch in plan.get("Plans", []) or []:
        n += _count_nodes(ch, pred)
    return n


def test_live_explain_chart_facts_scan_nodes_drop_from_about_330_to_40_or_fewer(db, pg_cluster):
    _setup(db, _CLEAN)
    with db(autocommit=True) as c:
        c.execute("ANALYZE")

        def plan_of(text: str) -> dict:
            r = c.execute("EXPLAIN (FORMAT JSON) " + text).fetchone()[0]
            return (r if isinstance(r, list) else json.loads(r))[0]["Plan"]

        old_plan, new_plan = plan_of(OLD_TEXT), plan_of(NEW_TEXT)
    scans = lambda p: _count_nodes(p, lambda n: n.get("Relation Name") == "chart_facts")
    cte_scans = lambda p: _count_nodes(p, lambda n: n.get("Node Type") == "CTE Scan" and n.get("CTE Name") == "gs_cf")
    old_n, new_n, cte_n = scans(old_plan), scans(new_plan), cte_scans(new_plan)
    assert old_n >= 300, f"OLD should scan chart_facts once per reference (330); the plan has {old_n}"
    assert new_n <= 40, f"NEW should scan chart_facts at most 40 times (1 CTE + 31 kept references); the plan has {new_n}"
    assert cte_n >= 250, f"NEW should read the materialized gs_cf ~299 times; the plan has {cte_n}"
    assert scans(old_plan) - scans(new_plan) >= 250


# -- LIVE: apply / guard / idempotency / serving effect (in the style of the 1326 test) ------------------------------------------

def test_live_apply_installs_the_new_text_and_the_installed_text_judges_like_the_old_one(db):
    _setup(db, _CLEAN)
    assert _md5(_txt(db)) == OLD_MD5
    _apply(db)
    assert _md5(_txt(db)) == NEW_MD5 and len(_txt(db)) == NEW_LEN and _txt(db) == NEW_TEXT
    assert _check(db, _txt(db)) is True and _check(db, OLD_TEXT) is True
    with db() as c:
        c.execute("UPDATE chart_facts SET fact_value_text='bogus' WHERE fact_category='graha_composite_state_classification' AND fact_subject='MOON'")
        c.commit()
    assert _check(db, _txt(db)) is False and _check(db, OLD_TEXT) is False


def test_live_apply_touches_only_integrity_check_sql_and_stales_only_ga_structural(db):
    _setup(db, _CLEAN)
    before = _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r ORDER BY asset_id")
    _apply(db)
    assert _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r ORDER BY asset_id") == before
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_other'")[0][0] == "SELECT true"
    fr = {(a, c): (s, r) for a, c, s, r in _q(db, "SELECT asset_id, chart_id::text, freshness_state, reasons::text FROM asset_freshness")}
    assert fr[("ga_structural", CANON)][0] == "stale" and "registry_changed" in fr[("ga_structural", CANON)][1]
    assert fr[("ga_structural", OTHER)][0] == "stale"
    assert fr[("ga_other", CANON)] == ("fresh", "[]")


def test_live_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _setup(db, _CLEAN)
    _apply(db)
    x1 = _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ga_structural'")
    with db() as c:
        c.execute("UPDATE asset_freshness SET freshness_state='fresh', reasons='[]' WHERE asset_id='ga_structural'")
        c.commit()
    notes: list[str] = []
    _apply(db, notes)
    assert _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ga_structural'") == x1
    assert any("already carries the single-scan rewrite" in n for n in notes)
    assert {s for (s,) in _q(db, "SELECT freshness_state FROM asset_freshness WHERE asset_id='ga_structural'")} == {"fresh"}


def test_live_foreign_text_is_left_untouched_notice_and_no_failure(db):
    foreign = OLD_TEXT + "\n-- edited by hand\n"
    _setup(db, text=foreign)
    notes: list[str] = []
    _apply(db, notes)
    assert _txt(db) == foreign
    assert any("not the text this migration was written against" in n and "NO-OP" in n and _md5(foreign) in n for n in notes)
    assert {s for (s,) in _q(db, "SELECT freshness_state FROM asset_freshness")} == {"fresh"}


def test_live_the_pre_1326_text_is_foreign_to_this_migration(db):
    _setup(db, text=PRE1326_TEXT)
    notes: list[str] = []
    _apply(db, notes)
    assert _md5(_txt(db)) == PRE1326_MD5 and any("NO-OP" in n and PRE1326_MD5 in n for n in notes)


def test_live_null_text_is_a_noop_not_a_failure(db):
    _setup(db)
    with db() as c:
        c.execute("UPDATE asset_registry SET integrity_check_sql = NULL WHERE asset_id='ga_structural'")
        c.commit()
    notes: list[str] = []
    _apply(db, notes)
    assert _txt(db) is None and any("NO-OP" in n for n in notes)


def test_live_empty_registry_is_a_noop(db):
    _setup(db, with_row=False)
    notes: list[str] = []
    _apply(db, notes)
    assert any("no ga_structural registry row" in n for n in notes)


def test_live_post_check_catches_a_silent_noop(db):
    _setup(db)
    with db() as c:
        c.execute("CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'ga_structural' DO INSTEAD NOTHING")
        c.commit()
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "update did not take" in str(ei.value)
    assert _txt(db) == OLD_TEXT

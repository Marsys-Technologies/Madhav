"""test_n296_multi_kind.py: SS N-296/N-305 `vocab_multi_kind` on the Vocab.alias value detector.

chart_facts.fact_subject is a generic subject column by design: graha codes (JUP ... and LAGNA, a released graha code), house codes (HOUSE_01 ...: registered bg_ontology aliases) and a nakshatra NAME
(Vishakha) share it, so the detector read "no single spelling family" (PARTIAL). The declaration is CHECKED: the column is read WHOLE (its distinct values over the asset's rows) and every vocabulary value
must be canonical in exactly one declared class and in that class's declared family. A wrong-family form, a class the declaration does not name, a non-canonical spelling, a padded or case variant: FAIL, nothing lifted.

Honest limits, pinned below: a value that is no vocabulary term at all (CUSP_01, CHART) is not graded (as everywhere in this detector) but is COUNTED in the record; a misspelling the lexicon does not
recognise as a variant of any term is such a value. The real values are those the canonical chart's ga_nakshatra writes into fact_subject (36 distinct, read once from production, read-only).

No database except the one real-SQL test on a disposable PostgreSQL: the rest fakes `scalar` and `vocab_fetch_samples`.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

T, C = "chart_facts", "fact_subject"
OWN = {T: ([C, "fact_category", "chart_id"], {C: "text", "fact_category": "text", "chart_id": "uuid"}, None)}
EVIDENCE = "platform/python-sidecar/pipeline/orchestrator/writers/ga_nakshatra.py:113"
KINDS = [{"class": "graha", "family": "code"}, {"class": "bhava", "family": "registered_code"}, {"class": "nakshatra", "family": "name"}]
GOOD_KINDS = {"graha": "code", "bhava": "registered_code", "nakshatra": "name"}
HOUSES = [f"HOUSE_{n:02d}" for n in range(1, 13)]
CUSPS = [f"CUSP_{n:02d}" for n in range(1, 13)]
GRAHA_CODES = ["JUP", "KET_MEAN", "LAGNA", "MAR", "MER", "MOON", "RAH_MEAN", "SAT", "SUN", "VEN"]
REAL = sorted(GRAHA_CODES + HOUSES + CUSPS + ["CHART", "Vishakha"])           # the 36 distinct values ga_nakshatra writes into fact_subject (11 + 12 + 12 + 1)


def decl(**over):
    d = {"table": T, "column": C, "kinds": copy.deepcopy(KINDS), "why": "fact_subject is chart_facts' generic subject column: graha codes, house codes and a nakshatra name share it by design", "evidence": EVIDENCE}
    d.update(over)
    return {"vocab_multi_kind": [d]}


@pytest.fixture(autouse=True)
def registered_houses(monkeypatch):
    """bg_ontology's registered aliases are read from the database in production: here HOUSE_01..12 are registered bhava aliases."""
    monkeypatch.setattr(ac, "_VOCAB_REGISTERED", {h.casefold(): {"classes": ["bhava"]} for h in HOUSES})
    monkeypatch.setattr(ac, "vocab_registered_load", lambda *a, **k: ac._VOCAB_REGISTERED)


# ───────────────────────── the declaration's shape (forgeries) ─────────────────────────

def test_a_sound_declaration_has_no_problem():
    assert ac.vocab_multi_kind_problem(decl()) is None
    assert ac.vocab_multi_kind_problem({}) is None


@pytest.mark.parametrize("bad", [
    {"vocab_multi_kind": "fact_subject"},
    {"vocab_multi_kind": []},
    {"vocab_multi_kind": [decl()["vocab_multi_kind"][0]] * 5},
    decl(kinds=[{"class": "graha", "family": "code"}]),                                                              # one kind is not multi-kind
    decl(kinds=[{"class": "graha", "family": "code"}, {"class": "graha", "family": "name"}]),                        # a class named twice
    decl(kinds=[{"class": "planet", "family": "code"}, {"class": "bhava", "family": "registered_code"}]),                 # not a vocabulary class
    decl(kinds=[{"class": "graha", "family": "abbreviation"}, {"class": "bhava", "family": "registered_code"}]),          # not a family
    decl(kinds=[{"class": "graha", "family": "code", "extra": 1}, {"class": "bhava", "family": "registered_code"}]),
    decl(kinds="graha"),
    decl(column="fact_subject; DROP TABLE chart_facts"),
    decl(table="chart facts"),
    decl(why=""),
    decl(evidence="unverified: it is probably fine"),
    decl(evidence="platform/python-sidecar/no_such_file.py:1"),
])
def test_a_malformed_declaration_is_refused(bad):
    assert ac.vocab_multi_kind_problem(bad)


def test_an_extra_or_missing_field_is_refused():
    d = decl()
    d["vocab_multi_kind"][0]["note"] = "x"
    assert "exactly the fields" in ac.vocab_multi_kind_problem(d)
    d = decl()
    del d["vocab_multi_kind"][0]["evidence"]
    assert "exactly the fields" in ac.vocab_multi_kind_problem(d)


def test_the_same_column_twice_is_refused():
    d = decl()
    d["vocab_multi_kind"].append(copy.deepcopy(d["vocab_multi_kind"][0]))
    assert "listed twice" in ac.vocab_multi_kind_problem(d)


def test_the_validator_raises_on_a_bad_declaration():
    with pytest.raises(ac.DeclarationsError):
        ac.validate_vocab_multi_kind_declaration("assets.ga_x", decl(kinds=[]))
    ac.validate_vocab_multi_kind_declaration("assets.ga_x", decl())


# ───────────────────────── the sets: the table / column the declaration names ─────────────────────────

def test_the_sets_resolve_for_an_owned_text_column():
    sets, problems = ac.vocab_multi_kind_sets(decl(), OWN)
    assert problems == [] and sets == {(T, C): GOOD_KINDS}


def test_a_table_not_owned_a_missing_column_or_a_non_text_column_is_refused():
    assert ac.vocab_multi_kind_sets(decl(), {})[0] == {}
    assert "not an owned table" in ac.vocab_multi_kind_sets(decl(), {})[1][0]
    assert "not a column" in ac.vocab_multi_kind_sets(decl(), {T: (["chart_id"], {"chart_id": "uuid"}, None)})[1][0]
    assert "not a text column" in ac.vocab_multi_kind_sets(decl(), {T: ([C], {C: "jsonb"}, None)})[1][0]
    assert "not a text column" in ac.vocab_multi_kind_sets(decl(), {T: ([C], {C: "integer"}, None)})[1][0]
    assert ac.vocab_multi_kind_sets(decl(), {T: (None, None, None)})[0] == {}
    assert ac.vocab_multi_kind_sets(decl(), {T: ([C], {}, None)})[0] == {}                                            # column types not read: cannot be checked


def test_a_malformed_declaration_credits_nothing():
    sets, problems = ac.vocab_multi_kind_sets(decl(kinds=[]), OWN)
    assert sets == {} and "malformed" in problems[0]


def test_the_refusal_record_is_no_detector_and_names_the_problem():
    r = ac.vocab_multi_kind_refuse({"vocab_values": {"x": 1}}, ["a: b"], decl())
    assert r["v"] == ac.NO_DET and "a: b" in r["measured"] and r["declaration_disagreements"][0]["field"] == "vocab_multi_kind"


# ───────────────────────── the judgement over the column's distinct values ─────────────────────────

def test_the_real_values_verify_kind_by_kind_and_the_non_vocabulary_ones_are_counted():
    rep = ac.vocab_multi_kind_report(REAL, GOOD_KINDS)
    assert rep["ok"] is True and rep["violations"] == [] and rep["distinct_values"] == 36
    assert rep["verified"]["graha"] == sorted(GRAHA_CODES)[:12] and rep["verified"]["nakshatra"] == ["Vishakha"]
    assert rep["verified"]["bhava"] == HOUSES[:12]
    assert rep["non_vocabulary_values"] == 13                                                                         # CUSP_01..12 and CHART: not vocabulary, counted, never hidden


def test_lagna_is_a_released_graha_code_so_it_belongs_to_the_graha_kind():
    r = ac.vocab_classify("LAGNA")
    assert r["kind"] == "canonical" and r["classes"] == ["graha"] and ac.vocab_lexicon()["family"]["LAGNA"] == frozenset({"code"})


@pytest.mark.parametrize("extra, why", [
    ("Jupiter", "name"),                    # a name where the kind is codes
    ("jupiter", "id"),                      # an id where the kind is codes
    ("Mercury", "name"),
    ("Aries", "not name"),                  # a rashi: a class the declaration does not name
    ("Taurus", "not name"),
])
def test_forgery_a_wrong_family_or_an_undeclared_class_fails_and_lifts_nothing(extra, why):
    rep = ac.vocab_multi_kind_report(REAL + [extra], GOOD_KINDS)
    assert rep["ok"] is False and rep["n_violations"] == 1 and extra in rep["violations"][0]


@pytest.mark.parametrize("variant", ["Mercury ", " Mercury", "mercury ", "Su", "Ma", "Vishakha ", "MOON ", "Jup"])
def test_forgery_a_padded_case_or_short_variant_is_a_non_canonical_spelling_and_fails(variant):
    rep = ac.vocab_multi_kind_report(REAL + [variant], GOOD_KINDS)
    assert rep["ok"] is False and any(variant in v for v in rep["violations"]), variant


def test_forgery_a_declared_family_that_does_not_match_the_data_fails():
    rep = ac.vocab_multi_kind_report(REAL, {**GOOD_KINDS, "graha": "name"})                                           # the codes are not names
    assert rep["ok"] is False and rep["n_violations"] == len(GRAHA_CODES)
    rep = ac.vocab_multi_kind_report(REAL, {**GOOD_KINDS, "nakshatra": "code"})
    assert rep["ok"] is False and any("Vishakha" in v for v in rep["violations"])


def test_forgery_dropping_a_kind_from_the_declaration_fails_the_values_of_that_kind():
    rep = ac.vocab_multi_kind_report(REAL, {"graha": "code", "nakshatra": "name"})                                    # bhava not declared: the HOUSE_nn registered aliases are a class it does not name
    assert rep["ok"] is False and rep["n_violations"] == 12 and all("bhava" in v for v in rep["violations"])


def test_a_term_canonical_in_two_declared_classes_is_not_exactly_one(monkeypatch):
    real = ac.vocab_classify
    monkeypatch.setattr(ac, "vocab_classify", lambda v: dict(kind="canonical", classes=["graha", "rashi"], detect=True, short=False) if v == "Both" else real(v))
    rep = ac.vocab_multi_kind_report(REAL + ["Both"], {**GOOD_KINDS, "rashi": "name"})
    assert rep["ok"] is False and "more than one declared kind" in rep["violations"][0]


def test_nothing_verified_is_not_ok():
    rep = ac.vocab_multi_kind_report(["CHART", "CUSP_01"], GOOD_KINDS)
    assert rep["ok"] is False and rep["verified"] == {} and rep["non_vocabulary_values"] == 2
    assert ac.vocab_multi_kind_report([], GOOD_KINDS)["ok"] is False


def test_a_registered_alias_is_only_ever_in_the_registered_code_family():
    rep = ac.vocab_multi_kind_report(["HOUSE_01", "JUP"], {"graha": "code", "bhava": "name"})                         # declared 'name' for bhava: a registered alias is not a name
    assert rep["ok"] is False and "HOUSE_01" in rep["violations"][0]


def test_the_honest_limit_a_misspelling_the_lexicon_does_not_recognise_is_not_graded():
    """Pinned so nobody reads this check as a spell checker: 'Jupitr' is no known variant of any term, so it is a non-vocabulary value (counted), exactly as everywhere in this detector."""
    rep = ac.vocab_multi_kind_report(REAL + ["Jupitr"], GOOD_KINDS)
    assert rep["ok"] is True and rep["non_vocabulary_values"] == 14


# ───────────────────────── the fetch path ─────────────────────────

def test_the_distinct_statement_is_one_read_only_select_over_the_scope():
    sql = ac.vocab_distinct_sql(T, C, "chart_id = 'x'")
    assert sql.lstrip().upper().startswith("SELECT") and "DISTINCT" in sql and f"LIMIT {ac.VOCAB_MULTI_KIND_MAX_DISTINCT + 1}" in sql and "chart_id = 'x'" in sql
    assert all(w not in sql.upper() for w in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER "))
    assert "WHERE" in ac.vocab_distinct_sql(T, C, None).upper() and "chart_id" not in ac.vocab_distinct_sql(T, C, None)


def test_the_fetch_reads_a_timeout_a_malformed_answer_and_too_many_values_as_unread(monkeypatch):
    def boom(sql, *a, **k):
        raise ac.Unknown("ERROR:  canceling statement due to statement timeout")
    monkeypatch.setattr(ac, "scalar", boom)
    assert "statement timeout" in ac.vocab_fetch_distinct(T, C, None)["unread"]
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps({"rows": 1}))
    assert "unread" in ac.vocab_fetch_distinct(T, C, None)
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps({"rows": 9, "values": [f"v{i}" for i in range(ac.VOCAB_MULTI_KIND_MAX_DISTINCT + 1)]}))
    assert "more than" in ac.vocab_fetch_distinct(T, C, None)["unread"]
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps({"rows": 2, "values": ["JUP", 3]}))
    assert "unread" in ac.vocab_fetch_distinct(T, C, None)


# ───────────────────────── end to end through the value detector ─────────────────────────

def _whole_sample(values):
    return dict(values=list(values), emb=[], key_hits=[], complete=False, rows=2000, oversized=0, deep=0, leaves=0, keys=0)


@pytest.fixture
def detect(monkeypatch):
    """`run(distinct_values, multi=True)`: the detector with a sample of the first rows (fact_subject mixes codes and a name) and the distinct read answered from `distinct_values`."""
    state = {}

    def samples(table, cols_kinds, where=None):
        return {c: (_whole_sample(["JUP", "MAR", "LAGNA", "HOUSE_01", "Vishakha"]) if c == C else dict(_whole_sample(["graha_nakshatra_join"]), complete=True)) for c, _k in cols_kinds}
    monkeypatch.setattr(ac, "vocab_fetch_samples", samples)
    monkeypatch.setattr(ac, "vocab_fetch_probe", lambda *a, **k: dict(hits=[], key_hits=[], oversized=0, deep=0))
    monkeypatch.setattr(ac, "vocab_fetch_spelling", lambda *a, **k: dict(found=False, sample=[]))

    def scalar(sql, *a, **k):
        assert "DISTINCT" in sql                                                                                       # only the distinct read is asked here
        vals = state["values"]
        return json.dumps({"rows": 2897, "values": sorted(vals)})
    monkeypatch.setattr(ac, "scalar", scalar)

    def run(values, multi=True, raise_=None):
        state["values"] = values
        if raise_:
            monkeypatch.setattr(ac, "scalar", raise_)
        sets, _ = ac.vocab_multi_kind_sets(decl(), OWN)
        return ac.vocab_value_detect({k: v[:2] for k, v in OWN.items()}, None, multi_sets=sets if multi else None)           # the detector takes (columns, types) pairs
    return run


def test_without_the_declaration_the_mixed_column_is_partial_as_today(detect):
    out = detect(REAL, multi=False)
    assert out["v"] == ac.PARTIAL and "MIXED canonical spelling families" in out["measured"]


def test_with_the_declaration_the_mixed_finding_is_lifted_over_the_whole_column(detect):
    out = detect(REAL)
    assert out["v"] == ac.PASS and "MIXED" not in out["measured"] and "MULTI-KIND, verified over the whole column" in out["measured"]
    col = next(c for c in out["vocab_values"]["found"] if c["column"] == C)
    assert col["complete"] is True and col["mixed"] is False and col["multi_kind"]["ok"] is True
    assert out["vocab_values"]["multi_kind"][f"{T}.{C}"]["non_vocabulary_values"] == 13
    assert "13 value(s) outside the vocabulary, not graded" in out["measured"]                                         # SS N-305: the limit is printed on the certificate text, not only stored


@pytest.mark.parametrize("extra", ["Jupiter", "jupiter", "Aries", "Mercury ", "Su"])
def test_a_value_outside_the_declared_kinds_makes_the_column_fail_even_though_the_sample_was_clean(detect, extra):
    out = detect(REAL + [extra])                       # the first-rows sample never showed it; the whole-column read does
    assert out["v"] == ac.FAIL and ("contradicted" in out["measured"] or "non-canonical spelling" in out["measured"])


def test_an_unreadable_distinct_read_lifts_nothing_and_is_never_a_pass(detect):
    def boom(sql, *a, **k):
        raise ac.Unknown("ERROR:  canceling statement due to statement timeout")
    out = detect(REAL, raise_=boom)
    assert out["v"] != ac.PASS and "could not be read whole" in json.dumps(out)


def test_the_declaration_only_touches_its_own_column(detect, monkeypatch):
    own = {T: ([C, "fact_value_text", "chart_id"], {C: "text", "fact_value_text": "text", "chart_id": "uuid"}, None)}
    monkeypatch.setattr(ac, "vocab_fetch_samples", lambda t, ck, w=None: {c: _whole_sample(["Aries", "JUP"]) for c, _k in ck})
    sets, _ = ac.vocab_multi_kind_sets(decl(), own)
    assert set(sets) == {(T, C)}                                                                                       # fact_value_text gets no lift


# ───────────────────────── real SQL on a disposable PostgreSQL ─────────────────────────

def test_REAL_SQL_the_distinct_read_is_scoped_deduplicated_and_capped(monkeypatch, disposable_pg):
    point_psql_at(disposable_pg, monkeypatch)
    disposable_pg.psql("CREATE TABLE chart_facts (chart_id uuid, fact_category text, fact_subject text)")
    cid = "482012f1-710e-4a25-994a-93821f5871aa"
    rows = [(cid, "graha_nakshatra_join", s) for s in ("JUP", "JUP", "MAR", "LAGNA", "HOUSE_01", "Vishakha", "CUSP_01", "CHART")]
    rows += [(cid, "someone_elses", "Aries"), (cid, "someone_elses", "Jupiter"), (cid, "graha_nakshatra_join", None)]
    for r in rows:
        disposable_pg.psql("INSERT INTO chart_facts VALUES (%s, %s, %s)" % (ac._vocab_lit(r[0]), ac._vocab_lit(r[1]), "NULL" if r[2] is None else ac._vocab_lit(r[2])))
    got = ac.vocab_fetch_distinct("chart_facts", "fact_subject", f"chart_id = '{cid}' AND fact_category IN ('graha_nakshatra_join')")
    assert got == {"rows": 8, "values": sorted(["CHART", "CUSP_01", "HOUSE_01", "JUP", "LAGNA", "MAR", "Vishakha"])}      # the other asset's Aries / Jupiter are out of scope, NULL is not a value
    whole = ac.vocab_fetch_distinct("chart_facts", "fact_subject", None)
    assert "Aries" in whole["values"] and "Jupiter" in whole["values"] and whole["rows"] == 10
    rep = ac.vocab_multi_kind_report(got["values"], GOOD_KINDS)
    assert rep["ok"] is True and rep["non_vocabulary_values"] == 2
    scoped_with_other = ac.vocab_fetch_distinct("chart_facts", "fact_subject", f"chart_id = '{cid}'")
    assert ac.vocab_multi_kind_report(scoped_with_other["values"], GOOD_KINDS)["ok"] is False                           # unscoped, the other asset's Aries / Jupiter would contradict


# ───────────────────────── review of #3367 (Kāla): registered spelling drift, unread falls through, the ungraded values are listed ─────────────────────────

LIVE_STYLE_ALIASES = ["House_01", "HOUSE_1", "H1", "h1", "1h", "first_house", "FIRST_HOUSE", "House 1", "1st_house"]


@pytest.fixture
def live_alias_set(monkeypatch):
    """The live bg_ontology alias set registers MANY spellings of a house, not only HOUSE_nn (Kāla's probe): every one of them is a registered alias, so each is 'canonical' to the plain classifier."""
    keys = {h.casefold(): {"classes": ["bhava"]} for h in HOUSES} | {a.casefold(): {"classes": ["bhava"]} for a in LIVE_STYLE_ALIASES}
    monkeypatch.setattr(ac, "_VOCAB_REGISTERED", keys)
    monkeypatch.setattr(ac, "vocab_registered_load", lambda *a, **k: ac._VOCAB_REGISTERED)


@pytest.mark.parametrize("alias", LIVE_STYLE_ALIASES)
def test_forgery_a_registered_house_alias_in_another_spelling_is_drift_beside_HOUSE_nn(live_alias_set, alias):
    assert ac.vocab_classify(alias)["kind"] == "registered"                                                  # the plain classifier calls it canonical: that is the hole
    rep = ac.vocab_multi_kind_report(REAL + [alias], GOOD_KINDS)
    assert rep["ok"] is False and any(alias in v and "code form NAME_NN" in v for v in rep["violations"]), alias


def test_the_real_house_codes_still_verify_with_the_live_style_alias_set(live_alias_set):
    rep = ac.vocab_multi_kind_report(REAL, GOOD_KINDS)
    assert rep["ok"] is True and rep["verified"]["bhava"] == HOUSES


def test_a_declared_name_code_shape_other_than_registered_code_gets_no_registered_alias(live_alias_set):
    rep = ac.vocab_multi_kind_report(["JUP", "HOUSE_01"], {"graha": "code", "bhava": "code"})
    assert rep["ok"] is False and "HOUSE_01" in rep["violations"][0]


def _detect_with(monkeypatch, sample_values, distinct_answer, scopes=None, raise_distinct=None):
    calls = []

    def samples(table, cols_kinds, where=None):
        return {c: (_whole_sample(sample_values) if c == C else dict(_whole_sample(["graha_nakshatra_join"]), complete=True)) for c, _k in cols_kinds}
    monkeypatch.setattr(ac, "vocab_fetch_samples", samples)
    monkeypatch.setattr(ac, "vocab_fetch_probe", lambda *a, **k: dict(hits=[], key_hits=[], oversized=0, deep=0))
    monkeypatch.setattr(ac, "vocab_fetch_spelling", lambda *a, **k: dict(found=False, sample=[]))

    def scalar(sql, *a, **k):
        calls.append(sql)
        if raise_distinct:
            raise raise_distinct
        return json.dumps({"rows": 2897, "values": sorted(distinct_answer)})
    monkeypatch.setattr(ac, "scalar", scalar)
    sets, _ = ac.vocab_multi_kind_sets(decl(), OWN)
    out = ac.vocab_value_detect({k: v[:2] for k, v in OWN.items()}, None, multi_sets=sets, scopes=scopes)
    return out, calls


def test_review_an_unread_distinct_read_keeps_a_visible_fail_a_fail(monkeypatch):
    boom = ac.Unknown("ERROR:  canceling statement due to statement timeout")
    out, _ = _detect_with(monkeypatch, ["JUP", " JUP", "HOUSE_01", "Vishakha"], REAL, raise_distinct=boom)
    assert out["v"] == ac.FAIL and "non-canonical spelling" in out["measured"]                          # NOT NO_DETECTOR with 'no vocabulary value was found'
    assert "no vocabulary value was found" not in out["measured"]
    col = next(c for c in out["vocab_values"]["found"] if c["column"] == C)
    assert "nothing is lifted" in col["multi_kind_unread"] and not col.get("multi_kind")


def test_review_an_unread_distinct_read_over_a_clean_sample_is_partial_never_pass_and_says_why(monkeypatch):
    boom = ac.Unknown("ERROR:  canceling statement due to statement timeout")
    out, _ = _detect_with(monkeypatch, ["JUP", "MAR", "HOUSE_01", "Vishakha"], REAL, raise_distinct=boom)
    assert out["v"] == ac.PARTIAL and "could not be read whole" in out["measured"] and "nothing is lifted" in out["measured"]
    assert "MIXED canonical spelling families" in out["measured"]                                         # the finding the declaration would have lifted is still there


def test_review_more_than_the_cap_of_distinct_values_lifts_nothing(monkeypatch):
    many = [f"v{i}" for i in range(ac.VOCAB_MULTI_KIND_MAX_DISTINCT + 1)]
    out, _ = _detect_with(monkeypatch, ["JUP", "HOUSE_01", "Vishakha"], many)
    assert out["v"] == ac.PARTIAL and "more than" in json.dumps(out["vocab_values"]["multi_kind_unread"])


def test_review_a_shared_table_whose_asset_rows_are_not_named_is_refused_without_reading(monkeypatch):
    scopes = {T: {"where": None, "label": "shared table, the asset's rows are not named by its count_sql: read whole (every asset's rows in it)"}}
    out, calls = _detect_with(monkeypatch, ["JUP", "HOUSE_01", "Vishakha"], REAL, scopes=scopes)
    assert calls == [] and out["v"] == ac.PARTIAL and "shared and the asset's own rows are not named" in out["measured"]


def test_review_a_scoped_shared_table_is_read_with_its_predicate(monkeypatch):
    scopes = {T: {"where": "fact_category IN ('graha_nakshatra_join')", "label": "scoped"}}
    out, calls = _detect_with(monkeypatch, ["JUP", "HOUSE_01", "Vishakha"], REAL, scopes=scopes)
    assert len(calls) == 1 and "fact_category IN ('graha_nakshatra_join')" in calls[0] and out["v"] == ac.PASS


def test_review_plain_unreadable_misspellings_are_listed_in_the_record_text_and_the_cell_stays_pass(monkeypatch):
    odd = ["JPU", "JUPP"]                                                                                       # transposed / doubled: no mark distinguishes them from an honest non-term; listed, with the limit stated
    out, _ = _detect_with(monkeypatch, ["JUP", "HOUSE_01", "Vishakha"], REAL + odd)
    assert out["v"] == ac.PASS
    n = 13 + len(odd)
    assert f"{n} value(s) outside the vocabulary, not graded" in out["measured"] and "'CHART'" in out["measured"] and all(repr(x) in out["measured"] for x in odd)
    stored = out["vocab_values"]["multi_kind"][f"{T}.{C}"]["non_vocabulary_list"]
    assert set(odd) <= set(stored) and "CHART" in stored and len(stored) == n                                  # the whole list is stored (at most 500); the text shows up to 40


SUSPICIOUS = [("J\u200bUP", "invisible"), ("JUP\u200b", "embedded"), ("J\u0423P", "more than one script"), ("JU\u0420", "more than one script"), ("", "empty or blank"), ("  ", "empty or blank"),
              (" JPU", "leading or trailing whitespace"), ("JPU ", "leading or trailing whitespace"), ("J\u00a0P", "invisible"), ("J\u202eUP", "invisible"),
              ("\ufb01x", "NFKC differs"), ("x\u00b2", "NFKC differs"), ("\uff21\uff22\uff23", "NFKC differs")]                     # an fi ligature, a superscript, an all-fullwidth ABC (not a vocabulary term)


@pytest.mark.parametrize("value, why", SUSPICIOUS)
def test_review_values_that_look_like_corrupted_vocabulary_make_the_cell_partial_never_pass(monkeypatch, value, why):
    out, _ = _detect_with(monkeypatch, ["JUP", "HOUSE_01", "Vishakha"], REAL + [value])
    assert out["v"] == ac.PARTIAL, (value, out["measured"][:300])
    assert why in out["measured"], (value, out["measured"][-400:])                                             # the reason is named, with the value


def test_review_an_all_fullwidth_graha_code_is_already_a_fail_as_a_non_canonical_spelling(monkeypatch):
    out, _ = _detect_with(monkeypatch, ["JUP", "HOUSE_01", "Vishakha"], REAL + ["\uff2a\uff35\uff30"])               # the lexicon folds it to JUP: stricter than PARTIAL
    assert out["v"] == ac.FAIL and "non-canonical spelling" in out["measured"]


@pytest.mark.parametrize("value", ["JPU", "JUPP", "CUSP_01", "CHART", "ZZ_001", "Purva Bhadrapada x", "A B"])
def test_review_honest_non_terms_carry_no_suspicion(value):
    assert ac.vocab_suspicious_value(value) is None


def test_review_the_real_ga_nakshatra_subject_values_carry_no_suspicion():
    assert ac.vocab_multi_kind_report(REAL, GOOD_KINDS)["suspicious_non_vocabulary"] == {}


def test_review_past_forty_values_the_text_says_how_many_more_and_the_record_keeps_them_all(monkeypatch):
    many = [f"ZZ_{i:03d}" for i in range(60)]
    out, _ = _detect_with(monkeypatch, ["JUP", "HOUSE_01", "Vishakha"], REAL + many)
    assert out["v"] == ac.PASS and "(+33 more)" in out["measured"]                                         # 13 + 60 = 73 values, 40 shown
    assert len(out["vocab_values"]["multi_kind"][f"{T}.{C}"]["non_vocabulary_list"]) == 73


def test_review_a_trailing_zero_width_space_after_a_canonical_code_is_embedded_text_so_never_a_pass(monkeypatch):
    out, _ = _detect_with(monkeypatch, ["JUP", "HOUSE_01", "Vishakha"], REAL + ["JUP\u200b"])
    assert out["v"] == ac.PARTIAL and "embedded vocabulary, spelling unchecked" in out["measured"]

"""test_n431_postprocess_matchers.py: two matcher fixes of census_postprocess.py (N-431 W6), offline.

(1) A Vocab.alias column item may carry the label the engine appends for a verified multi-kind column (`asset_census.vocab_multi_kind_label`): the matcher is built from the engine's own wording constants.
(2) A column the engine could not read because the database CONNECTION was lost (psql's first stderr line) is an unread column, like one cancelled by the statement timeout. An ordinary SQL error is not.

Every positive cell text is produced by the ENGINE's own functions (vocab_values_record, vocab_fetch_probe, vocab_fetch_samples, vocab_grade_column, vocab_multi_kind_label) from a faked psql failure, never retyped.
Negatives are similar-looking texts that must stay BLOCKERS. Unchanged: three existing cells of n268_real_cells.json keep the exact classification they had before the change.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(os.environ.get("N431_TESTS_DIR") or pathlib.Path(__file__).resolve().parent)     # the governance __tests__ directory
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import test_e5_7_census_postprocess as base  # noqa: E402

cp = base.cp
ac = cp._engine_module()
REAL = json.loads((HERE / "n268_real_cells.json").read_text(encoding="utf-8"))

T = "chart_facts"
MK_DECLARED = {"graha": "code", "bhava": "registered_code", "nakshatra": "name"}


def named(text, verdict="PARTIAL", asset="ga_nakshatra"):
    return cp.named_item(asset, "Vocab.alias", dict(v=verdict, cause=text, state="MEASURED"))


# ───────────────────────── texts built by the engine ─────────────────────────

def multi_kind_column(n_listed=1, column="fact_subject"):
    """A found column of the engine's record shape that carries a verified multi-kind reading (what vocab_values_record consumes)."""
    listed = ["CHART"] + [f"X_{i:02d}" for i in range(1, n_listed)]
    return dict(table=T, column=column, kind="text", rows_sampled=2000, complete=False, carries=True, weak=False, embedded=[], key_hits=[], read="sample",
                classes=["bhava", "graha", "nakshatra"], canonical=["JUP", "MAR", "SUN", "Vishakha"], spellings=[], registered=["HOUSE_01", "HOUSE_02"], families=["code"], mixed=False,
                multi_kind=dict(ok=True, declared=dict(MK_DECLARED), verified=sorted(MK_DECLARED), non_vocabulary_values=n_listed, non_vocabulary_list=listed))


def _fake_scalar(msg):
    def boom(sql):
        raise ac.Unknown(msg)
    return boom


def lost_probe(msg, col="fact_value"):
    """The unread column the engine records when the existence probe's psql call fails with `msg` as its first stderr line (scalar is faked to raise what _psql_run raises)."""
    saved, ac.scalar = ac.scalar, _fake_scalar(msg)
    try:
        probe = ac.vocab_fetch_probe(T, col, "text")
    finally:
        ac.scalar = saved
    sample = ac.vocab_parse_sample(json.dumps({"rows": 2000, "values": [], "emb": []}), "text")
    return ac.vocab_grade_column(T, col, "text", sample, probe=probe)


def lost_sample(msg, col="fact_value"):
    """The unread column the engine records when the bounded sample's psql call fails with `msg` (the batch and the per-column retry both fail)."""
    saved, ac.scalar = ac.scalar, _fake_scalar(msg)
    try:
        got = ac.vocab_fetch_samples(T, [(col, "text")])
    finally:
        ac.scalar = saved
    return ac.vocab_grade_column(T, col, "text", got[col])


def record_text(cols):
    rec = ac.vocab_values_record(cols, [], [T])
    return rec["v"], rec["measured"]


CONN_MESSAGES = [
    "server closed the connection unexpectedly",
    'connection to server at "127.0.0.1", port 5432 failed: Connection refused',
    'connection to server on socket "/tmp/.s.PGSQL.5432" failed: No such file or directory',
    "could not receive data from server: Connection reset by peer",
    "FATAL:  terminating connection due to administrator command",
    "psql: error: server closed the connection unexpectedly",
]


# ───────────────────────── (1) the MULTI-KIND label ─────────────────────────

def test_the_label_the_engine_builds_is_accepted_on_a_vocab_alias_cell():
    v, text = record_text([multi_kind_column()])
    assert v == "PARTIAL" and "; MULTI-KIND, verified over the whole column: " in text, text
    r = named(text)
    assert r and r["kind"] == "ceiling" and r["pattern"] == "vocab-canonical-with-caveats", (r, text)
    assert "bounded sample only: chart_facts.fact_subject" in r["reason"]


def test_the_label_with_a_truncated_value_list_is_accepted():
    n = ac.VOCAB_MULTI_KIND_TEXT_LIST + 5
    v, text = record_text([multi_kind_column(n_listed=n)])
    assert f" (+{n - ac.VOCAB_MULTI_KIND_TEXT_LIST} more)" in text, text
    assert named(text) is not None


def test_the_label_without_a_value_list_beside_a_second_column_and_an_unread_column_is_accepted():
    col = multi_kind_column()
    col["multi_kind"]["non_vocabulary_list"], col["multi_kind"]["non_vocabulary_values"] = [], 0
    other = dict(multi_kind_column(column="fact_kind"), multi_kind=None, classes=["graha"], registered=[])
    v, text = record_text([col, other, lost_probe("server closed the connection unexpectedly")])
    assert "0 value(s) outside the vocabulary, not graded)" in text, text                      # no value list: the label ends the item
    r = named(text)
    assert r and r["reason"].endswith("unread: chart_facts.fact_value"), (r, text)


def test_the_accepted_label_is_built_from_the_engines_own_constants(monkeypatch):
    """No retyped copy: if the engine's wording changes, the matcher follows it (and the old wording stops matching)."""
    v, text = record_text([multi_kind_column()])
    assert named(text) is not None
    monkeypatch.setattr(ac, "VOCAB_MULTI_KIND_NOT_GRADED", " value(s) left out of the vocabulary, not graded")
    monkeypatch.setattr(cp, "_V_FOUND_CACHE", [])
    assert named(text) is None                                                  # the old wording is no longer the engine's
    assert named(text.replace(" value(s) outside the vocabulary, not graded", " value(s) left out of the vocabulary, not graded")) is not None


@pytest.mark.parametrize("mutate", [
    lambda t: t.replace("not graded", "graded"),                                                     # a different suffix
    lambda t: t.replace("not graded", "not graded at all"),
    lambda t: t.replace("verified over the whole column", "verified over a sample"),                # a different label
    lambda t: t.replace("; MULTI-KIND, verified over the whole column: ", "; MULTI-KIND: "),
    lambda t: t.replace("graha/code", "graha/spelling"),                                             # a family the engine does not have
    lambda t: t.replace("graha/code", "graha"),                                                      # a kind without its family
    lambda t: t.replace("1 value(s) outside", "some value(s) outside"),
    lambda t: t.replace(": 'CHART')", ": CHART)"),                                                  # an unquoted value list
    lambda t: t.replace(": 'CHART')", ": 'CHART'; non-canonical spelling: 'Sunn')"),                 # another clause inside the item
    lambda t: t.replace("; every whole value found is canonical, but:", ", mixed: a.b (JUP, Jupiter); every whole value found is canonical, but:"),
])
def test_a_similar_looking_label_stays_a_blocker(mutate):
    v, text = record_text([multi_kind_column()])
    assert named(text) is not None
    bad = mutate(text)
    assert bad != text, "the forgery did not change the text"
    assert named(bad) is None, bad


def test_the_items_are_counted_outside_the_quoted_values_of_the_label():
    """A listed value that looks like an item head ('x.y (z') must not change the item count: 1 column is 1 item."""
    col = multi_kind_column()
    col["multi_kind"]["non_vocabulary_list"] = ["x.y (z"]
    v, text = record_text([col])
    assert named(text) is not None, text
    assert named(text.replace("in 1 column(s)", "in 2 column(s)")) is None


# ───────────────────────── (2) a lost database connection ─────────────────────────

@pytest.mark.parametrize("msg", CONN_MESSAGES)
def test_a_probe_lost_to_a_dropped_connection_is_a_named_unread_column(msg):
    v, text = record_text([multi_kind_column(), lost_probe(msg)])
    assert "the existence probe failed: " in text, text
    r = named(text)
    assert r and r["kind"] == "ceiling" and r["reason"].endswith("unread: chart_facts.fact_value"), (r, text)


@pytest.mark.parametrize("msg", CONN_MESSAGES)
def test_a_sample_lost_to_a_dropped_connection_is_a_named_unread_column(msg):
    col = lost_sample(msg)
    assert col.get("unread", "").startswith("the bounded sample failed: "), col
    v, text = record_text([multi_kind_column(), col])
    r = named(text)
    assert r and r["reason"].endswith("unread: chart_facts.fact_value"), (r, text)


def test_a_dropped_connection_is_handled_like_the_statement_timeout_in_the_embedded_only_form():
    r0 = REAL["vocab-embedded-only-timeout"]
    old = "the rest of the column was not read (the existence probe exceeded the statement timeout: ERROR: canceling statement due to statement timeout)"
    assert old in r0["text"]
    new = "the rest of the column was not read (" + lost_probe("server closed the connection unexpectedly")["unread"].split("(", 1)[1]
    text = r0["text"].replace(old, new)
    assert text != r0["text"]
    got, was = named(text, asset=r0["asset"]), named(r0["text"], asset=r0["asset"])
    assert got and was and got["pattern"] == was["pattern"] == "vocab-embedded-only" and got["reason"] == was["reason"]


@pytest.mark.parametrize("msg", [
    'ERROR:  syntax error at or near "FROM"',
    'ERROR:  relation "chart_facts" does not exist',
    "ERROR:  permission denied for table chart_facts",
    "ERROR:  invalid input syntax for type json",
    "ERROR:  canceling statement due to user request",
    'ERROR:  syntax error at or near "server closed the connection unexpectedly"',                 # the fragment is not at the START of the message
    "ERROR:  server closed the connection unexpectedly",                                           # not a prefix psql prints for it
    "server closed the connection unexpectedly: and then relation x does not exist",              # (a) takes no tail
    "terminating connection due to administrator command, relation x does not exist",
    "the server closed the connection unexpectedly",
    "connection lost",
    "could not connect",
])
def test_an_ordinary_sql_error_or_a_lookalike_stays_a_blocker(msg):
    for col in (lost_probe(msg), lost_sample(msg)):
        v, text = record_text([multi_kind_column(), col])
        assert named(text) is None, text


def test_a_connection_fragment_followed_by_another_clause_stays_a_blocker():
    v, text = record_text([multi_kind_column(), lost_probe("server closed the connection unexpectedly")])
    assert named(text) is not None
    assert named(text + "; unknown caveat nobody wrote") is None
    assert named(text.replace("unexpectedly)", "unexpectedly; relation x does not exist)")) is None


# ───────────────────────── unchanged: three existing cells keep their classification ─────────────────────────
# (the expected reasons were produced by the matcher BEFORE this change, on the same cell texts)

UNCHANGED = {
    "vocab-canonical-with-caveats": ("vocab-canonical-with-caveats",
        "every whole value found is canonical; not verified: embedded text, spelling unchecked, in bodha_pratijna.ayanamsha_id, bodha_pratijna.derivation, bodha_pratijna.varga_confirmation; "
        "bounded sample only: bodha_pratijna.derivation; unread: bodha_pratijna.derivation"),
    "vocab-unread-timeout": ("vocab-canonical-with-caveats",
        "every whole value found is canonical; not verified: bounded sample only: ephemeris_daily.body; unread: ephemeris_daily.ayanamsha_id, ephemeris_daily.epoch_convention, ephemeris_daily.source_citation"),
    "vocab-embedded-only-timeout": ("vocab-embedded-only",
        "no whole value is a term (embedded text only, spelling unchecked, in bodha_grounding_matches.ayanamsha_id, bodha_grounding_matches.matched_rule_id); no non-canonical value found; "
        "unread: bodha_grounding_matches.target_id"),
}


@pytest.mark.parametrize("key", sorted(UNCHANGED))
def test_an_existing_certified_cell_keeps_its_classification(key):
    r = REAL[key]
    got = cp.named_item(r["asset"], r["criterion"], dict(v=r["verdict"], cause=r["text"], state="MEASURED"))
    pattern, reason = UNCHANGED[key]
    assert got == dict(criterion="Vocab.alias", kind="ceiling", pattern=pattern, reason=reason)


def test_an_existing_blocker_stays_a_blocker():
    r = REAL["vocab-mixed"]
    assert cp.named_item(r["asset"], r["criterion"], dict(v=r["verdict"], cause=r["text"], state="MEASURED")) is None


def test_the_engines_label_text_is_byte_identical_to_the_one_it_always_built():
    """vocab_multi_kind_label now reads its two fixed wordings from constants; the text it returns did not move."""
    c = multi_kind_column()
    assert ac.vocab_multi_kind_label(c) == "; MULTI-KIND, verified over the whole column: graha/code, bhava/registered_code, nakshatra/name; 1 value(s) outside the vocabulary, not graded: 'CHART'"
    assert ac.vocab_multi_kind_label(dict(c, multi_kind=dict(c["multi_kind"], ok=False))) == ""

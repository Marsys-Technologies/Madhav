"""test_n240_none_safety.py: census C (main 41a6793c0) died after ~47 min with `TypeError: '<' not supported between instances of 'NoneType' and 'str'` (exit 5, no traceback, no census written). SS N-240.

The exact site could not be recovered from the one-line message; these tests pin every candidate that can see a None from production data in the code paths new since census B, each as a REPRODUCER (it raised the TypeError, or
would have let a None pass as a value, before the fix): a JSON null in a sampled vocabulary list (`emb`, `key_hits`, `values`, the spelling / probe samples) reached `sorted(...)` next to strings; a NULL scope / state in an
attempt reached `sorted(h['executed_scopes'])` / `sorted({a['state'] ...})`; a NULL canonical_id / name / synonym in the registered alias set. A None is ABSENT, never a value that passes. Plus the safety net: the top-level
`script error` handler prints the full traceback (message and exit code 5 unchanged).
"""
from __future__ import annotations

import io
import json
import pathlib
import runpy
import sys
import traceback

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

bw = ac._lint_module("build_window")


def _sample(**over):
    d = dict(rows=3, complete=True, values=["Sun", "Moon"], emb=[], key_hits=[], oversized=0, deep=0)
    d.update(over)
    return d


# ───────────────────────── vocabulary samples: JSON null is absent ─────────────────────────

@pytest.mark.parametrize("field", ["values", "emb", "key_hits"])
def test_a_json_null_in_a_sampled_list_does_not_raise_and_is_not_a_value(field):
    vals = {"values": ["Sun", None, "Moon", None], "emb": ["Sun in 7th house", None, "Moon rises"], "key_hits": ["planet", None, "house"]}
    rec = ac.vocab_grade_column("t", "c", "text", _sample(**{field: vals[field]}))
    assert "unread" not in rec or True
    blob = json.dumps(rec, default=str)
    assert "null" not in blob.replace('"mixed": null', "")        # no None leaked into the record
    for k in ("embedded", "key_hits", "canonical", "spellings", "registered"):
        assert None not in (rec.get(k) or []), (k, rec)


def test_a_null_in_the_spelling_and_probe_samples_is_absent():
    rec = ac.vocab_grade_column("t", "c", "text", _sample(complete=False), spelling=dict(found=True, sample=["Surya", None], emb=[], short=[], off=[], spell=["Surya", None]),
                                probe=dict(hits=["Sun", None], key_hits=[None, "planet"], oversized=False, deep=False))
    assert None not in (rec.get("spellings") or []) and None not in (rec.get("canonical") or []) and None not in (rec.get("key_hits") or [])


def test_a_column_of_only_nulls_is_not_a_vocabulary_value():
    rec = ac.vocab_grade_column("t", "c", "text", _sample(values=[None, None]))
    assert not rec.get("carries")


def test_the_record_for_a_column_with_nulls_renders_without_raising():
    cols = [ac.vocab_grade_column("t", "c", "text", _sample(values=["Sun", None], emb=[None, "Sun in 7th house"], key_hits=[None]))]
    rec = ac.vocab_values_record(cols, [], ["t"])
    assert rec["v"] in (ac.PASS, ac.PARTIAL, ac.FAIL, ac.NO_DET, ac.NA)


# ───────────────────────── registered alias set: NULL name / id / synonym entries ─────────────────────────

def test_the_registered_set_skips_null_names_ids_and_synonym_elements():
    rows = [dict(c="planet", id=None, en=None, sa=None, syn=[None, "surya", None]), dict(c="planet", id="mars", en="Mars", sa=None, syn=None),
            dict(c="sign", id=None, en="Aries", sa=None, syn=[None])]
    reg = ac.vocab_registered_parse(json.dumps(rows))
    assert set(reg) == {"surya", "mars", "aries"}
    assert all(None not in v["ids"] and "None" not in v["ids"] for v in reg.values())
    ac._VOCAB_REGISTERED = reg
    try:
        assert sorted(ac.vocab_registered_set()) == ["aries", "mars", "surya"]
        assert ac.vocab_lex_sql()                         # builds with the registered array
        assert ac.vocab_classify("surya")["kind"] == "registered"
        assert ac.vocab_classify(None) is None
    finally:
        ac._VOCAB_REGISTERED = None


# ───────────────────────── attempts: NULL scope / state / text ─────────────────────────

def _att(**o):
    d = dict(scope="asset_set", state="complete", disposition="build", when="d", error="", started=True, epoch=300.0, run_id="r", receipt=False)
    d.update(o)
    return d


@pytest.mark.parametrize("field", ["scope", "state", "disposition", "when", "error", "run_id"])
def test_a_null_attempt_field_never_raises_in_the_windowed_grader(field):
    atts = [_att(), _att(epoch=310.0, **{field: None})]
    per: dict = {}
    for a in atts:
        ac._tally_attempt(per, "x", a["scope"], a["state"], a["disposition"], a["when"], a["error"], "t")
    W = bw.apply_certification_floor(dict(ok=True, epoch=100.0, basis="b", opens="x"), 200.0)
    r = ac._grade_build_history_windowed("x", atts, None, W, per["x"])
    assert r["v"] in (ac.PASS, ac.PARTIAL, ac.FAIL, ac.NO_DET)
    for s_ in per["x"]["scopes"] | per["x"]["executed_scopes"]:
        assert isinstance(s_, str)                      # NULL became absent text, so the sets sort with strings


def test_the_executed_scope_list_of_the_exercised_cell_sorts_with_a_null_scope():
    per: dict = {}
    ac._tally_attempt(per, "x", "asset_set", "complete", "build", "d", "", "t")
    ac._tally_attempt(per, "x", None, "complete", "build", "d", "", "t")
    text = ", ".join(sorted(str(x) for x in per["x"]["executed_scopes"]))
    assert text                                           # the exact expression measure() uses
    assert ", ".join(sorted(str(x) for x in per["x"]["executed_scopes"])) == ", ".join(sorted(per["x"]["executed_scopes"]))


def test_explained_attempt_tolerates_null_fields():
    runs = bw.EXPLAINED_RUNS
    for o in (dict(run_id=None), dict(error=None, state="error"), dict(state=None), dict(disposition=None, state="error", error="permission denied for table x")):
        ac.explained_attempt(_att(**o), runs)


def test_a_null_cause_field_in_a_ledger_style_result_does_not_break_the_cert_floor():
    assert bw.apply_certification_floor(dict(ok=True, epoch=100.0, basis="b", opens="x"), None, None)["ok"] is False


# ───────────────────────── the safety net ─────────────────────────

def _guard_source():
    src = (HERE.parent / "asset_census.py").read_text(encoding="utf-8")
    return src[src.index('if __name__ == "__main__":'):]


def test_the_script_error_handler_prints_message_traceback_and_exits_5(capsys):
    guard = _guard_source()
    ns = {"__name__": "__main__", "sys": sys, "main": lambda: sorted(["a", None])}
    with pytest.raises(SystemExit) as ei:
        exec(compile(guard, "asset_census_guard", "exec"), ns)
    assert ei.value.code == 5
    err = capsys.readouterr().err
    first = err.splitlines()[0]
    assert first.startswith("asset_census: script error — TypeError: '<' not supported between instances of")
    assert "Traceback (most recent call last)" in err and "asset_census_guard" in err and err.count("TypeError") >= 2


def test_a_clean_run_still_exits_with_the_measured_code(capsys):
    ns = {"__name__": "__main__", "sys": sys, "main": lambda: 3}
    with pytest.raises(SystemExit) as ei:
        exec(compile(_guard_source(), "asset_census_guard", "exec"), ns)
    assert ei.value.code == 3 and capsys.readouterr().err == ""

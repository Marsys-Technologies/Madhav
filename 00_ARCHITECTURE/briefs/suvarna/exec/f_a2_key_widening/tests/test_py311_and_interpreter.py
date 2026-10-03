"""Python 3.11 floor + interpreter record. The production job image and CI run Python 3.11; the executor must also run on 3.12+.

(1) EVERY .py file of this folder (executor, patch modules, helpers, tests, gate fixture) parses under the lowest supported grammar:
    ast.parse(feature_version=(3, 11)) rejects what only PEP 701 (3.12+) accepts, e.g. an f-string that reuses its own quote type
    inside a replacement field, so the check is meaningful on whichever interpreter CI uses.
    Caveat (honest scope): feature_version is best-effort on interpreters >= 3.12 (their parser is the PEP 701 one and ast.parse does
    not re-check every 3.12 rule). `test_the_nested_quote_fstring_is_detected_on_this_interpreter` pins what the guard really catches on
    THIS interpreter, so a guard that silently stopped detecting would be red; the authoritative proof is py_compile under a real 3.11.
(2) outcome.json carries python_executable and python_version (sys.executable, the full sys.version) in EVERY status.
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys

import pytest

import conftest as cf
from conftest import EXEC_DIR

NESTED = 'x = f"a {d.get(k, "dflt")} b"\n'          # valid only from Python 3.12 (PEP 701)


def _py_files():
    return sorted(p for p in EXEC_DIR.rglob("*.py") if "__pycache__" not in p.parts)


def _rel(p):
    return p.relative_to(EXEC_DIR).as_posix()


def test_the_folder_has_python_files():
    names = {_rel(p) for p in _py_files()}
    assert "d6_dataplane_capture_fa2_exec.py" in names and "tests/gate_fixture/executor_standards.py" in names and len(names) >= 20


@pytest.mark.parametrize("path", _py_files(), ids=_rel)
def test_every_file_parses_under_the_python_311_grammar(path):
    ast.parse(path.read_text(), filename=str(path), feature_version=(3, 11))


def test_the_nested_quote_fstring_is_detected_on_this_interpreter():
    """Mutation proof of the guard: the 3.12-only construct must fail the 3.11 parse (on 3.12+ only if ast.parse enforces it there)."""
    if sys.version_info >= (3, 12):
        pytest.skip("ast.parse(feature_version) does not enforce the pre-PEP-701 f-string grammar on >= 3.12 (authoritative: py_compile on 3.11)")
    with pytest.raises(SyntaxError):
        ast.parse(NESTED, feature_version=(3, 11))


def test_the_shipped_executor_has_no_reused_quote_inside_an_fstring_replacement_field():
    """Interpreter-independent backstop for the one construct that bit us: tokenise every file (on >= 3.12 an f-string is split into
    FSTRING_START/MIDDLE/END tokens) and fail if a replacement field contains a STRING token whose quote char equals the enclosing f-string's."""
    import io
    import tokenize
    if sys.version_info < (3, 12):
        pytest.skip("on < 3.12 the parser itself rejects the construct (previous test)")
    bad = []
    for p in _py_files():
        stack = []
        for tok in tokenize.generate_tokens(io.StringIO(p.read_text()).readline):
            if tok.type == tokenize.FSTRING_START:
                stack.append(tok.string[-1])
            elif tok.type == tokenize.FSTRING_END:
                stack.pop()
            elif tok.type == tokenize.STRING and stack and tok.string.lstrip("rbuRBU")[:1] == stack[-1]:
                bad.append(f"{_rel(p)}:{tok.start[0]}")
    assert bad == []


def test_the_backstop_finds_the_construct_in_a_temp_copy(tmp_path):
    """Mutation proof for the tokenizer backstop (>= 3.12): the shipped line 466 re-introduced in a temp copy is found."""
    if sys.version_info < (3, 12):
        pytest.skip("tokenizer backstop is for >= 3.12")
    import io
    import tokenize
    found = False
    stack = []
    for tok in tokenize.generate_tokens(io.StringIO(NESTED).readline):
        if tok.type == tokenize.FSTRING_START:
            stack.append(tok.string[-1])
        elif tok.type == tokenize.FSTRING_END:
            stack.pop()
        elif tok.type == tokenize.STRING and stack and tok.string[:1] == stack[-1]:
            found = True
    assert found


# ------------------------------------------------------------------------------------------------ interpreter in outcome.json
@pytest.mark.parametrize("kind", ["dry_run", "applied", "failed", "commit_state_unknown", "exception_inside_guard", "exit_inside_guard"])
def test_outcome_json_records_the_interpreter_in_every_status(mod, tmp_path, kind):
    es = mod.standards()
    d = tmp_path / kind
    gate_fp = dict(es.fingerprint(str(cf.GATE_FIXTURE)), under_test=False)
    execp = str(EXEC_DIR / "d6_dataplane_capture_fa2_exec.py")
    cls = mod.safe_outcome_class(es)
    digest = "b" * 64
    if kind == "dry_run":
        with cls(d, execp, "a" * 64, gate_fp) as o:
            o.dry_run(digest)
    elif kind == "applied":
        with cls(d, execp, "a" * 64, gate_fp) as o:
            o.mark_committed(digest)
            o.applied(digest)
    elif kind == "failed":
        with cls(d, execp, "a" * 64, gate_fp) as o:
            o.fail(["some_check"])
    elif kind == "commit_state_unknown":
        with pytest.raises(RuntimeError):
            with cls(d, execp, "a" * 64, gate_fp) as o:
                o.mark_commit_unknown(digest, "OperationalError")
                raise RuntimeError("x")
    elif kind == "exception_inside_guard":
        with pytest.raises(RuntimeError):
            with cls(d, execp, "a" * 64, gate_fp):
                raise RuntimeError("x")
    else:
        with pytest.raises(SystemExit):
            with cls(d, execp, "a" * 64, gate_fp):
                raise SystemExit(7)
    path = d / "outcome.json"
    body = json.loads(path.read_text())
    assert body["python_executable"] == sys.executable and body["python_executable"]
    assert body["python_version"] == sys.version and body["python_version"].startswith(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    assert body["status"] in ("dry_run", "applied", "failed", "commit_state_unknown")
    assert oct(path.stat().st_mode & 0o777) == "0o600" and not list(d.glob(".outcome.*"))            # atomic replace left no temp file
    assert {"schema", "status", "utc", "executor_sha256", "plan_hash", "gate_sha256", "run_gated_sha256", "evidence_digest", "failed_checks",
            "under_test", "warnings"} <= set(body)                                                  # the standard fields are all still there


def test_a_failed_interpreter_record_is_reported_not_silent(mod, tmp_path, monkeypatch):
    es = mod.standards()
    d = tmp_path / "w"
    monkeypatch.setattr(mod, "add_interpreter_to_outcome", lambda p: (_ for _ in ()).throw(OSError("disk")))
    with mod.safe_outcome_class(es)(d, str(EXEC_DIR / "d6_dataplane_capture_fa2_exec.py"), "a" * 64,
                                    dict(es.fingerprint(str(cf.GATE_FIXTURE)), under_test=False)) as o:
        o.dry_run("b" * 64)
    assert o.write_error == "OSError"

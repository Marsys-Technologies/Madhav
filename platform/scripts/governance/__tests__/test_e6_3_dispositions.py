"""E6.3 dispositions ledger: schema, validator, append helper and CLI (asset_dispositions.py).

Every rule has a mutation test that must FAIL the validator; the valid files must also be accepted by the READER
(asset_elevation_tracker.elevated_assets), so the validator and the reader cannot drift apart. Hermetic: a throw-away
git repo with a MINI registry (the E6.3 fixtures); the one real-repo test reads the committed ledger and the real
registry snapshot, never a database."""
from __future__ import annotations

import json
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import asset_dispositions as ad  # noqa: E402
from _e6_3_fixtures import DISP, REPO, World, chained, disp, load_tracker, mini_patch, sha  # noqa: E402

T = load_tracker()
EV = "briefs/B.md#s1"
ALL = {"ga_alpha", "bg_beta", "ka_gamma"}


@pytest.fixture(autouse=True)
def _mini(monkeypatch):
    mini_patch(monkeypatch, T)


@pytest.fixture
def w(tmp_path):
    w = World(tmp_path).default()
    w.raw["briefs/B.md"] = "# brief\n## s1\n"
    w.commit()
    return w


def row(asset="ga_alpha", disposition="keep", **over):
    r = disp(asset, disposition, reason="because", decision_id="N-70")
    r["evidence"] = EV
    r.update(over)
    return r


def probs(w, rows, **kw):
    kw.setdefault("repo", w.repo)
    kw.setdefault("ref", w.last)
    return ad.validate(chained(rows), reader=T, **kw)


def has(problems, text):
    return any(text in p for p in problems)


def new_ledger(tmp_path, w, name="ledger.jsonl"):
    p = tmp_path / name
    ad.init(p, reader=T)
    return p


def app(p, w, asset="ga_alpha", disposition="keep", **over):
    e = dict(asset=asset, disposition=disposition, evidence=EV, reason="because", decision_id="N-70")
    e.update(over)
    return ad.append(p, e, repo=w.repo, ref=w.last, base=None, reader=T)


def lines(p):
    return p.read_text(encoding="utf-8").rstrip("\n").split("\n")


def put(p, ls):
    p.write_text("\n".join(ls) + "\n", encoding="utf-8")


def check(p, w, **kw):
    kw.setdefault("repo", w.repo)
    kw.setdefault("ref", w.last)
    return ad.validate(p, reader=T, **kw)


def committed(w, text):
    """Commit `text` as the ledger in the fixture repo (so --base HEAD has something to compare with)."""
    w.raw[DISP] = text
    w.commit("ledger")
    return w.repo / DISP


# ═══════════════ the schema is the reader's, not a copy ═══════════════

def test_the_schema_constant_is_built_from_the_readers_constants():
    R = ad.load_reader()
    s = ad.SCHEMA
    assert s["dispositions"] == sorted(R.E63_DISPOSITIONS)
    assert s["terminal_dispositions"] == sorted(R.E63_TERMINAL_DISPOSITIONS)
    assert s["path"] == R.E63_DISPOSITIONS_PATH
    assert s["decision_id_pattern"] == R._E63_DECISION.pattern
    assert s["asset_pattern"] == R._E63_ASSET.pattern


def test_the_module_holds_no_copy_of_the_readers_vocabulary():
    src = open(ad.__file__, encoding="utf-8").read()
    for word in sorted(ad.load_reader().E63_DISPOSITIONS):
        assert f'"{word}"' not in src and f"'{word}'" not in src, word


def test_the_reader_does_not_import_the_module_so_there_is_no_cycle():
    src = open(ad.READER_PATH, encoding="utf-8").read()
    assert "import asset_dispositions" not in src and "from asset_dispositions" not in src and "asset_dispositions.py" not in src


# ═══════════════ valid files ═══════════════

def test_a_header_only_file_is_valid_and_the_reader_reads_it_as_no_dispositions(w, tmp_path):
    p = new_ledger(tmp_path, w)
    assert check(p, w) == []
    committed(w, p.read_text(encoding="utf-8"))
    assert w.elevated(T) == set()                       # the reader accepts it: nothing is dispositioned, nothing is elevated


def test_appended_rows_are_chained_valid_and_read_by_the_reader(w, tmp_path):
    p = new_ledger(tmp_path, w)
    r1 = app(p, w, "ga_alpha")
    r2 = app(p, w, "bg_beta", additions=["D-GROUNDING"])
    r3 = app(p, w, "ka_gamma", "retire", reason="superseded by ka_delta")
    assert (r1["seq"], r2["seq"], r3["seq"]) == (1, 2, 3)
    ls = lines(p)
    assert r1["prev_sha256"] == sha(ls[0].encode()) and r2["prev_sha256"] == sha(ls[1].encode())
    assert r3["prev_sha256"] == sha(ls[2].encode())
    assert check(p, w) == []
    committed(w, p.read_text(encoding="utf-8"))
    assert w.elevated(T) == ALL                         # ka_gamma is terminal; the other two are measured and dispositioned
    rep = T.elevated_report(w.last, str(w.repo))
    assert rep["ka_gamma"]["terminal"] == dict(disposition="retire", reason="superseded by ka_delta", decision_id="N-70")


def test_the_validator_and_the_reader_agree_on_what_a_row_means(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha", decision_id=None)             # proposed: reads unresolved
    data = p.read_bytes()
    facts, registry = T._e63_registry_facts(str(w.repo), w.last), T._e63_registry_assets(str(w.repo), w.last)
    got = T._e63_parse_dispositions(data, facts, registry)
    assert got["ga_alpha"]["effective"] == "unresolved" and got["ga_alpha"]["disposition"] == "keep"
    app(p, w, "ga_alpha", decision_id="N-71")           # accepted: the latest row governs
    got = T._e63_parse_dispositions(p.read_bytes(), facts, registry)
    assert got["ga_alpha"]["effective"] == "keep" and got["ga_alpha"]["decision_id"] == "N-71"
    assert check(p, w) == []


def test_lines_and_text_and_bytes_are_accepted_as_sources(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w)
    text = p.read_text(encoding="utf-8")
    for src in (text, text.encode(), text.rstrip("\n").split("\n")):
        assert ad.validate(src, repo=w.repo, ref=w.last, reader=T) == []


def test_the_committed_real_ledger_is_valid_and_the_real_reader_accepts_it():
    """The real file, the real registry snapshot at HEAD (offline: git only), the real reader's own parser."""
    path = REPO / ad.SCHEMA["path"]
    assert path.is_file()
    R = ad.load_reader()
    assert ad.validate(path, repo=REPO, ref="HEAD", base=None, reader=R) == []
    sha_ = R._e63_resolve_ref("HEAD", str(REPO))
    got = R._e63_parse_dispositions(path.read_bytes(), R._e63_registry_facts(str(REPO), sha_), R._e63_registry_assets(str(REPO), sha_))
    assert isinstance(got, dict)
    assert json.loads(path.read_text(encoding="utf-8").split("\n", 1)[0])["asset"] == "_schema"


def test_without_a_ledger_at_the_ref_the_reader_raises_unreadable_and_with_the_header_it_does_not(w, tmp_path):
    w.raw[DISP] = None
    w.commit("no ledger")
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    assert e.value.code == "unreadable" and "asset_dispositions.jsonl" in str(e.value)
    p = new_ledger(tmp_path, w)
    committed(w, p.read_text(encoding="utf-8"))
    assert w.elevated(T) == set()


# ═══════════════ mutations: each rule must FAIL ═══════════════

def test_mutation_broken_chain_prev_sha256(w):
    rows = [row("ga_alpha"), row("bg_beta", prev_sha256="0" * 64), row("ka_gamma")]
    assert has(probs(w, rows), "hash chain is broken")


def test_mutation_edited_history_line_in_the_middle_breaks_the_chain(w, tmp_path):
    p = new_ledger(tmp_path, w)
    for a in ("ga_alpha", "bg_beta", "ka_gamma"):
        app(p, w, a)
    ls = lines(p)
    r = json.loads(ls[2])
    r["reason"] = "edited"
    ls[2] = json.dumps(r, ensure_ascii=False)
    put(p, ls)
    assert has(check(p, w), "hash chain is broken")


def test_mutation_deleted_and_reordered_lines_break_the_chain(w, tmp_path):
    p = new_ledger(tmp_path, w)
    for a in ("ga_alpha", "bg_beta", "ka_gamma"):
        app(p, w, a)
    base = lines(p)
    put(p, base[:1] + base[2:])
    assert has(check(p, w), "expected 1")
    put(p, [base[0], base[2], base[1], base[3]])
    assert has(check(p, w), "expected 1")


def test_mutation_wrong_seq(w):
    assert has(probs(w, [row("ga_alpha", seq=3)]), "seq")


def test_mutation_unknown_row_key(w):
    out = probs(w, [row("ga_alpha", note="x")])
    assert has(out, "unknown key(s) ['note']")


def test_mutation_unknown_header_key(w):
    text = chained([row()]).split("\n", 1)
    hdr = json.loads(text[0])
    hdr["extra"] = 1
    r = json.loads(text[1].split("\n")[0])
    r["prev_sha256"] = sha(json.dumps(hdr).encode())
    new = json.dumps(hdr) + "\n" + json.dumps(r) + "\n"
    assert has(ad.validate(new, repo=w.repo, ref=w.last, reader=T), "unknown header key")


def test_mutation_header_missing_or_second_header(w):
    r = json.dumps(row() | dict(seq=1, prev_sha256="0" * 64))
    assert has(ad.validate(r + "\n", repo=w.repo, ref=w.last, reader=T), "first line must be the `_schema` row")
    rows = [row("ga_alpha"), {"asset": "_schema", "_doc": "again"}]
    assert has(probs(w, rows), "_schema")


@pytest.mark.parametrize("bad", ["keepish", "Keep", "", None, 3, "fix"])
def test_mutation_disposition_outside_the_readers_vocabulary(w, bad):
    assert has(probs(w, [row("ga_alpha", disposition=bad)]), "disposition")


@pytest.mark.parametrize("bad", ["x", "N-", "n-5", "N-12 ", 7, True, ""])
def test_mutation_malformed_decision_id(w, bad):
    assert has(probs(w, [row("ga_alpha", decision_id=bad)]), "decision")


@pytest.mark.parametrize("key", ["decision_id", "decided_on", "additions"])
def test_mutation_a_reader_required_key_is_missing(w, key):
    r = row("ga_alpha")
    del r[key]
    assert has(probs(w, [r]), key)


@pytest.mark.parametrize("when", ["2026-10-02", "2026-10-02T10:00:00", "yesterday", None, ""])
def test_mutation_decided_on_not_timezone_aware(w, when):
    assert has(probs(w, [row("ga_alpha", decided_on=when)]), "decided_on")


@pytest.mark.parametrize("asset", ["zz_unknown", "ga_ghost", "GA_alpha", "ga-alpha", 5, None])
def test_mutation_asset_not_in_the_registry_or_malformed(w, asset):
    assert probs(w, [row(asset)])


def test_mutation_missing_evidence(w):
    r = row("ga_alpha")
    del r["evidence"]
    assert has(probs(w, [r]), "evidence is required")


@pytest.mark.parametrize("bad", ["", "  ", None, 5, "/abs/path.md", "../up.md", "a/../b.md", "a b.md", "a\\b.md", "x.md#", "x.md#a#b", " x.md"])
def test_mutation_bad_evidence_pointer(w, bad):
    assert has(probs(w, [row("ga_alpha", evidence=bad)]), "evidence")


def test_mutation_evidence_file_that_does_not_exist_is_refused_for_new_rows_only(w):
    out = probs(w, [row("ga_alpha", evidence="briefs/missing.md#s1")], new_from_seq=1)
    assert has(out, "does not exist")
    assert probs(w, [row("ga_alpha", evidence="briefs/missing.md#s1")]) == []        # not checked for history


def test_mutation_exact_duplicate_row_is_refused(w):
    out = probs(w, [row("ga_alpha"), row("bg_beta"), row("ga_alpha")])
    assert has(out, "duplicate of line 2")


def test_a_different_row_for_the_same_asset_is_a_legitimate_supersession(w):
    assert probs(w, [row("ga_alpha", decision_id=None), row("ga_alpha", decision_id="N-71")]) == []
    assert probs(w, [row("ga_alpha"), row("ga_alpha", reason="a second look, same decision")]) == []


@pytest.mark.parametrize("dec", [None, "N-70"])
def test_mutation_ending_a_terminal_disposition_without_a_new_decision_is_refused(w, dec):
    rows = [row("ka_gamma", "retire", reason="gone"), row("ka_gamma", "keep", decision_id=dec)]
    assert has(probs(w, rows), "terminal retire")


def test_a_terminal_disposition_may_be_ended_by_a_new_decision(w):
    rows = [row("ka_gamma", "retire", reason="gone"), row("ka_gamma", "keep", decision_id="N-99")]
    assert probs(w, rows) == []
    assert probs(w, [row("ka_gamma", "retire", reason="gone"), row("ka_gamma", "retire", reason="gone, said better")]) == []


def test_an_unreadable_registry_snapshot_fails_closed_and_still_checks_ids_syntactically(w):
    out = probs(w, [row("GA_alpha")], ref="refs/heads/does-not-exist")
    assert has(out, "registry snapshot") and has(out, "bad asset")


@pytest.mark.parametrize("raw", [b"", b"not json\n", b'{"asset": "_schema", "_doc": "x"}\n[1]\n', b'{"asset": "_schema", "_doc": "x"}\n{"seq": 1',
                                 b'{"asset": "_schema", "_doc": "x", "_doc": "y"}\n'])
def test_mutation_unparseable_files_are_refused(w, raw):
    assert ad.validate(raw, repo=w.repo, ref=w.last, reader=T)


# ═══════════════ the git append-only rule ═══════════════

def test_a_legitimate_append_after_the_committed_copy_passes_the_base_check(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    f = committed(w, p.read_text(encoding="utf-8"))
    ad.append(f, dict(asset="bg_beta", disposition="keep", evidence=EV, additions=["D-GROUNDING"]), repo=w.repo, ref=w.last, base="HEAD", rel_path=DISP, reader=T)
    assert check(f, w, base="HEAD") == []
    assert len(lines(f)) == 3


def test_mutation_editing_the_last_committed_line_is_invisible_to_the_chain_but_caught_against_git(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    app(p, w, "bg_beta")
    f = committed(w, p.read_text(encoding="utf-8"))
    ls = lines(f)
    r = json.loads(ls[-1])
    r["reason"] = "rewritten after the fact"
    ls[-1] = json.dumps(r, ensure_ascii=False)
    put(f, ls)
    assert check(f, w) == []                                        # the in-file chain cannot see it ...
    assert has(check(f, w, base="HEAD"), "history rewritten")        # ... git can


def test_mutation_a_whole_file_rewrite_that_is_re_chained_is_caught_against_git(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    f = committed(w, p.read_text(encoding="utf-8"))
    f.write_text(chained([row("ga_alpha", reason="a different history")]), encoding="utf-8")
    assert check(f, w) == []
    assert has(check(f, w, base="HEAD"), "history rewritten")


def test_mutation_truncating_committed_history_is_caught_against_git(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    app(p, w, "bg_beta")
    f = committed(w, p.read_text(encoding="utf-8"))
    put(f, lines(f)[:2])
    assert check(f, w) == [] and has(check(f, w, base="HEAD"), "history rewritten")


def test_a_missing_base_copy_means_every_row_is_new_and_its_evidence_is_checked(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    put(p, lines(p)[:1] + [json.dumps(json.loads(lines(p)[1]) | dict(evidence="briefs/gone.md"))])
    out = check(p, w, base="HEAD")       # the fixture's HEAD holds a different ledger at the canonical path: a prefix problem too
    assert has(out, "history rewritten") or has(out, "does not exist")
    assert has(check(p, w, base="HEAD", rel_path="00_ARCHITECTURE/control/not_committed.jsonl"), "does not exist")


def test_an_unresolvable_base_ref_is_a_problem(w, tmp_path):
    p = new_ledger(tmp_path, w)
    assert has(check(p, w, base="refs/heads/nope"), "base 'refs/heads/nope'")


# ═══════════════ append helper ═══════════════

def test_append_never_rewrites_history_the_old_bytes_stay_a_prefix(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    before = p.read_bytes()
    app(p, w, "bg_beta")
    after = p.read_bytes()
    assert after.startswith(before) and after.endswith(b"\n") and len(after) > len(before)


@pytest.mark.parametrize("entry,why", [
    (dict(asset="ga_alpha", disposition="keepish", evidence=EV), "disposition"),
    (dict(asset="ga_ghost", disposition="keep", evidence=EV), "registry"),
    (dict(asset="ga_alpha", disposition="keep", evidence="briefs/missing.md"), "does not exist"),
    (dict(asset="ga_alpha", disposition="keep", evidence="/abs.md"), "evidence"),
    (dict(asset="ga_alpha", disposition="keep", evidence=EV, decision_id="bogus"), "decision"),
    (dict(asset="ga_alpha", disposition="keep", evidence=EV, decided_on="2026-10-02"), "decided_on"),
    (dict(asset="ga_alpha", disposition="keep", evidence=EV, additions=["a", "a"]), "additions"),
    (dict(asset="ga_alpha", disposition="keep", evidence=EV, seq=9), "unknown entry key"),
    (dict(asset="ga_alpha", disposition="keep", evidence=EV, prev_sha256="0" * 64), "unknown entry key"),
    (dict(asset="ga_alpha", disposition="keep"), "missing required"),
    (dict(disposition="keep", evidence=EV), "missing required"),
])
def test_a_refused_append_writes_nothing(w, tmp_path, entry, why):
    p = new_ledger(tmp_path, w)
    app(p, w, "bg_beta")
    before = p.read_bytes()
    with pytest.raises(ad.DispositionError) as e:
        ad.append(p, entry, repo=w.repo, ref=w.last, base=None, reader=T)
    assert why in str(e.value)
    assert p.read_bytes() == before


def test_append_refuses_a_duplicate_and_a_silent_end_of_a_terminal_disposition(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ka_gamma", "retire", reason="gone")
    before = p.read_bytes()
    with pytest.raises(ad.DispositionError, match="duplicate"):
        app(p, w, "ka_gamma", "retire", reason="gone")
    with pytest.raises(ad.DispositionError, match="terminal retire"):
        app(p, w, "ka_gamma", "keep", decision_id=None)
    assert p.read_bytes() == before
    app(p, w, "ka_gamma", "keep", decision_id="N-99")


def test_append_refuses_a_ledger_that_is_already_invalid(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    app(p, w, "bg_beta")
    ls = lines(p)
    r = json.loads(ls[1])
    r["reason"] = "tampered"
    ls[1] = json.dumps(r, ensure_ascii=False)
    put(p, ls)
    before = p.read_bytes()
    with pytest.raises(ad.DispositionError, match="not a valid ledger"):
        app(p, w, "ka_gamma")
    assert p.read_bytes() == before


def test_append_refuses_a_ledger_rewritten_against_git(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    f = committed(w, p.read_text(encoding="utf-8"))
    f.write_text(chained([row("ga_alpha", reason="other history")]), encoding="utf-8")
    with pytest.raises(ad.DispositionError, match="history rewritten"):
        ad.append(f, dict(asset="bg_beta", disposition="keep", evidence=EV), repo=w.repo, ref=w.last, base="HEAD", rel_path=DISP, reader=T)


def test_append_to_a_missing_or_empty_file_is_refused(w, tmp_path):
    with pytest.raises(ad.DispositionError, match="--init"):
        app(tmp_path / "nope.jsonl", w)
    e = tmp_path / "empty.jsonl"
    e.write_bytes(b"")
    with pytest.raises(ad.DispositionError):
        app(e, w)
    assert e.read_bytes() == b""


def test_a_failed_write_is_truncated_back_so_no_torn_line_survives(w, tmp_path, monkeypatch):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    before = p.read_bytes()
    real = os.write

    def torn(fd, data):
        real(fd, bytes(data)[:17])
        raise OSError("disk full")
    monkeypatch.setattr(ad.os, "write", torn)
    with pytest.raises(OSError, match="disk full"):
        app(p, w, "bg_beta")
    monkeypatch.undo()
    assert p.read_bytes() == before
    mini_patch(monkeypatch, T)
    app(p, w, "bg_beta")
    assert check(p, w) == []


def test_a_file_without_a_trailing_newline_is_appended_to_on_its_own_line(w, tmp_path):
    p = new_ledger(tmp_path, w)
    p.write_bytes(p.read_bytes().rstrip(b"\n"))
    app(p, w, "ga_alpha")
    assert check(p, w) == [] and len(lines(p)) == 2


def test_concurrent_appends_keep_one_unbroken_chain(w, tmp_path):
    p = new_ledger(tmp_path, w)
    errs = []

    def go(i):
        try:
            app(p, w, ["ga_alpha", "bg_beta", "ka_gamma"][i % 3], "keep", reason=f"writer {i}")
        except BaseException as e:      # noqa: BLE001
            errs.append(e)
    ts = [threading.Thread(target=go, args=(i,)) for i in range(6)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errs, errs
    assert check(p, w) == [] and [json.loads(x)["seq"] for x in lines(p)[1:]] == [1, 2, 3, 4, 5, 6]


def test_init_never_overwrites(tmp_path):
    p = tmp_path / "l.jsonl"
    ad.init(p, reader=T)
    before = p.read_bytes()
    with pytest.raises(ad.DispositionError, match="never overwrites"):
        ad.init(p, reader=T)
    assert p.read_bytes() == before


# ═══════════════ CLI ═══════════════

def cli(w, *args):
    return ad.main(["--repo", str(w.repo), "--ref", w.last, *args], reader=T)


def test_cli_init_append_check_roundtrip(w, tmp_path, capsys):
    p = tmp_path / "l.jsonl"
    assert cli(w, "--init", str(p)) == 0
    assert cli(w, "--check", str(p)) == 0 and "OK:" in capsys.readouterr().out
    assert cli(w, "--append", "--asset", "ka_gamma", "--disposition", "retire", "--evidence", EV, "--reason", "gone",
               "--decision-id", "N-70", str(p)) == 0
    assert "appended seq 1" in capsys.readouterr().out
    assert cli(w, "--append", "--asset", "bg_beta", "--disposition", "keep", "--evidence", EV, "--addition", "D-GROUNDING", str(p)) == 0
    assert cli(w, "--check", str(p)) == 0
    assert json.loads(lines(p)[2])["additions"] == ["D-GROUNDING"]


def test_cli_check_exits_1_with_the_problems_printed(w, tmp_path, capsys):
    p = tmp_path / "l.jsonl"
    cli(w, "--init", str(p))
    cli(w, "--append", "--asset", "ga_alpha", "--disposition", "keep", "--evidence", EV, str(p))
    cli(w, "--append", "--asset", "bg_beta", "--disposition", "keep", "--evidence", EV, str(p))
    ls = lines(p)
    put(p, [ls[0], ls[2], ls[1]])
    capsys.readouterr()
    assert cli(w, "--check", str(p)) == 1
    out = capsys.readouterr().out
    assert "PROBLEM:" in out and "FAIL:" in out


def test_cli_refused_append_exits_1_and_usage_errors_exit_2(w, tmp_path, capsys):
    p = tmp_path / "l.jsonl"
    cli(w, "--init", str(p))
    assert cli(w, "--append", "--asset", "ga_alpha", "--disposition", "keepish", "--evidence", EV, str(p)) == 1
    assert "REFUSED" in capsys.readouterr().err
    assert cli(w, "--append", "--asset", "ga_alpha", str(p)) == 2
    assert cli(w, "--check", str(tmp_path / "missing.jsonl")) == 2
    assert cli(w, "--init", str(p)) == 1


def test_cli_schema_prints_the_readers_vocabulary(capsys):
    assert ad.main(["--schema"], reader=T) == 0
    s = json.loads(capsys.readouterr().out)
    assert s["dispositions"] == sorted(T.E63_DISPOSITIONS) and s["terminal_dispositions"] == sorted(T.E63_TERMINAL_DISPOSITIONS)


def test_cli_check_against_git_base_of_the_canonical_path(w, tmp_path, capsys):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    f = committed(w, p.read_text(encoding="utf-8"))
    assert cli(w, "--check", str(f), "--base", "HEAD") == 0
    ls = lines(f)
    r = json.loads(ls[-1])
    r["reason"] = "edited"
    ls[-1] = json.dumps(r, ensure_ascii=False)
    put(f, ls)
    assert cli(w, "--check", str(f), "--no-base") == 0
    assert cli(w, "--check", str(f), "--base", "HEAD") == 1
    assert "history rewritten" in capsys.readouterr().out

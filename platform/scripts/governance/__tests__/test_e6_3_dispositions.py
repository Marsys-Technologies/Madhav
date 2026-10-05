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

pytestmark = pytest.mark.skip(reason="the E6.3 certificate reader was dropped by owner decision N-152; the module stays importable, its tests are not run in CI")

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import asset_dispositions as ad  # noqa: E402
from _e6_3_fixtures import DISP, REPO, World, chained, disp, git, load_tracker, mini_patch, sha  # noqa: E402

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
    out = check(p, w, base="HEAD", rel_path=DISP)       # the fixture's HEAD holds a different ledger at the canonical path
    assert has(out, "history rewritten") or has(out, "does not exist")
    assert has(check(p, w, base="HEAD", rel_path="00_ARCHITECTURE/control/not_committed.jsonl"), "does not exist")


def test_an_unresolvable_base_ref_is_a_problem(w, tmp_path):
    p = new_ledger(tmp_path, w)
    out = check(p, w, base="refs/heads/nope", rel_path=DISP)
    assert has(out, "base 'refs/heads/nope'") and not has(out, "NOT CHECKED: the path")


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
    with pytest.raises(ad.DispositionError, match="ends ka_gamma's terminal retire"):
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


# ═══════════════ review fixes (F1-F8 and the surviving mutants) ═══════════════

def cli_out(w, capsys, *args):
    capsys.readouterr()
    code = cli(w, *args)
    o = capsys.readouterr()
    return code, o.out + o.err


# ---- F1: the terminal-revert rule tests whether the NEW row is itself terminal ----

@pytest.mark.parametrize("kind", ["retire", "consolidate"])
@pytest.mark.parametrize("over,needle", [
    (dict(decision_id=None), "would silently drop"),
    (dict(reason=""), "visible reason"),
    (dict(reason="​", decision_id="N-99"), "visible reason"),
    (dict(reason=None, decision_id="N-99"), "visible reason"),
    (dict(reason="...", decision_id="N-99"), "visible reason"),
])
def test_f1_a_terminal_kind_row_that_is_not_itself_terminal_is_refused_after_a_terminal_one(w, kind, over, needle):
    rows = [row("ka_gamma", kind, reason="gone"), row("ka_gamma", kind, **{"reason": "still gone", **over})]
    assert has(probs(w, rows), needle)


def test_f1_the_bypass_rows_really_do_drop_the_asset_in_the_reader_and_the_validator_refuses_them(w):
    good = [row("ka_gamma", "retire", reason="gone")]
    bypass = good + [row("ka_gamma", "retire", reason="still gone", decision_id=None)]
    w.raw[DISP] = chained(good)
    w.commit("g")
    assert "ka_gamma" in T.elevated_assets(w.last, str(w.repo))
    w.raw[DISP] = chained(bypass)
    w.commit("b")
    assert "ka_gamma" not in T.elevated_assets(w.last, str(w.repo))
    assert probs(w, bypass)


def test_f1_a_change_of_terminal_kind_needs_a_new_decision_and_says_so(w):
    out = probs(w, [row("ka_gamma", "retire", reason="gone"), row("ka_gamma", "consolidate", reason="folded")])
    assert has(out, "changes ka_gamma's terminal kind retire -> consolidate") and not has(out, "ends ka_gamma's terminal")
    assert probs(w, [row("ka_gamma", "retire", reason="gone"), row("ka_gamma", "consolidate", reason="folded", decision_id="N-99")]) == []


def test_f1_ending_a_terminal_disposition_by_a_new_decision_and_restating_it_stay_legitimate(w):
    assert probs(w, [row("ka_gamma", "retire", reason="gone"), row("ka_gamma", "keep", decision_id="N-99")]) == []
    assert probs(w, [row("ka_gamma", "retire", reason="gone"), row("ka_gamma", "retire", reason="gone, in other words")]) == []
    assert has(probs(w, [row("ka_gamma", "retire", reason="gone"), row("ka_gamma", "keep")]), "ends ka_gamma's terminal retire")


# ---- F7: a terminal row needs a visible reason, in the file and at append ----

@pytest.mark.parametrize("kind", ["retire", "consolidate"])
@pytest.mark.parametrize("reason", [None, "", "   ", "​", "ㅤ", "...", "⠀"])
def test_f7_a_terminal_kind_row_without_a_visible_reason_is_refused_by_the_validator_and_by_append(w, tmp_path, kind, reason):
    assert has(probs(w, [row("ka_gamma", kind, reason=reason)]), "needs a visible reason")
    assert has(probs(w, [row("ka_gamma", kind, reason=reason, decision_id=None)]), "needs a visible reason")
    p = new_ledger(tmp_path, w)
    before = p.read_bytes()
    with pytest.raises(ad.DispositionError, match="visible reason"):
        app(p, w, "ka_gamma", kind, reason=reason)
    assert p.read_bytes() == before


# ---- F4: malformed field types are problems, never a traceback ----

@pytest.mark.parametrize("over", [dict(disposition=["keep"]), dict(disposition={"a": 1}), dict(decision_id=["N-1"]),
                                  dict(reason=["x"]), dict(additions=[["x"]]), dict(additions="D-X"), dict(asset=["ga_alpha"]),
                                  dict(evidence={"p": 1}), dict(decided_on=["2026-01-01T00:00:00+00:00"])])
def test_f4_a_malformed_field_type_is_reported_as_a_problem_in_any_position(w, over):
    assert probs(w, [{**row("ga_alpha"), **over}])
    assert probs(w, [row("ga_alpha", disposition="retire", reason="gone"), {**row("ga_alpha"), **over}])


def test_f4_the_cli_reports_an_unhashable_disposition_as_a_problem_with_exit_1_and_no_traceback(w, tmp_path, capsys):
    p = tmp_path / "bad.jsonl"
    p.write_text(chained([row("ga_alpha", disposition=["keep"])]), encoding="utf-8")
    code, out = cli_out(w, capsys, "--check", str(p))
    assert code == 1 and "PROBLEM:" in out and "Traceback" not in out


# ---- F5: evidence files are regular, tracked or staged ----

def test_f5_an_evidence_symlink_is_refused(w):
    (w.repo / "briefs/link.md").symlink_to("/etc/hosts")
    git(w.repo, "add", "-A")
    assert has(probs(w, [row("ga_alpha", evidence="briefs/link.md")], new_from_seq=1), "symlink")


def test_f5_a_file_reached_through_a_symlinked_directory_is_refused(w, tmp_path):
    out_dir = tmp_path / "elsewhere"
    out_dir.mkdir()
    (out_dir / "b.md").write_text("x", encoding="utf-8")
    (w.repo / "linkdir").symlink_to(out_dir)
    git(w.repo, "add", "-A")
    assert has(probs(w, [row("ga_alpha", evidence="linkdir/b.md")], new_from_seq=1), "symlink")


def test_f5_an_untracked_evidence_file_is_refused_until_it_is_staged(w):
    (w.repo / "briefs/new.md").write_text("x", encoding="utf-8")
    r = [row("ga_alpha", evidence="briefs/new.md#a")]
    assert has(probs(w, r, new_from_seq=1), "neither tracked nor staged")
    git(w.repo, "add", "briefs/new.md")
    assert probs(w, r, new_from_seq=1) == []


def test_f5_a_directory_is_not_evidence(w):
    assert has(probs(w, [row("ga_alpha", evidence="briefs")], new_from_seq=1), "not a regular file")


def test_f5_append_applies_the_same_evidence_rules(w, tmp_path):
    p = new_ledger(tmp_path, w)
    (w.repo / "briefs/u.md").write_text("x", encoding="utf-8")
    with pytest.raises(ad.DispositionError, match="neither tracked nor staged"):
        app(p, w, evidence="briefs/u.md")
    git(w.repo, "add", "briefs/u.md")
    assert app(p, w, evidence="briefs/u.md")["evidence"] == "briefs/u.md"


# ---- F6: rows are written ASCII-only; a raw separator in a file is refused ----

def test_f6_append_escapes_non_ascii_so_no_line_separator_reaches_the_file(w, tmp_path):
    p = new_ledger(tmp_path, w)
    r = app(p, w, reason="a b\u0085c é ㅤx")
    raw = p.read_bytes()
    assert raw.isascii()
    txt = raw.decode("ascii")
    assert len(txt.splitlines()) == len(txt.split("\n")) - 1 == 2
    assert json.loads(txt.splitlines()[1])["reason"] == r["reason"] == "a b\u0085c é ㅤx"
    assert check(p, w) == []


@pytest.mark.parametrize("ch", [" ", " ", "\u0085"])
def test_f6_mutation_a_raw_line_separator_inside_a_row_is_refused(w, ch):
    text = chained([row("ga_alpha", reason=f"a{ch}b")])
    assert ch in text
    assert has(ad.validate(text, repo=w.repo, ref=w.last, reader=T), "raw line-separator")


# ---- F2: the git rule reports its real status and never skips silently ----

def test_f2_the_ok_line_prints_the_real_status_of_the_base_check(w, tmp_path, capsys):
    p = new_ledger(tmp_path, w)
    app(p, w)
    f = committed(w, p.read_text(encoding="utf-8"))
    code, out = cli_out(w, capsys, "--check", str(f), "--base", "HEAD")
    assert code == 0 and f"prefix rule checked against {w.last[:12]}" in out
    code, out = cli_out(w, capsys, "--check", str(f), "--no-base")
    assert code == 0 and "git rule: not requested" in out


def test_f2_a_base_where_the_ledger_does_not_exist_is_reported_as_not_applicable(w, tmp_path, capsys):
    w.raw[DISP] = None
    w.commit("no ledger")
    p = new_ledger(tmp_path, w)
    (w.repo / DISP).write_bytes(p.read_bytes())
    code, out = cli_out(w, capsys, "--check", str(w.repo / DISP), "--base", "HEAD")
    assert code == 0 and "no ledger at base" in out and "prefix rule not applicable" in out


def test_f2_a_symlinked_canonical_ledger_pointing_outside_the_repo_is_refused(w, tmp_path, capsys):
    p = new_ledger(tmp_path, w)
    app(p, w)
    f = committed(w, p.read_text(encoding="utf-8"))
    outside = tmp_path / "outside.jsonl"
    outside.write_text(chained([row("ga_alpha", reason="a different history")]), encoding="utf-8")
    f.unlink()
    f.symlink_to(outside)
    assert has(ad.validate(f, repo=w.repo, ref=w.last, base="HEAD", reader=T), "symlink")
    code, out = cli_out(w, capsys, "--check", "--base", "HEAD")
    assert code == 1 and "symlink" in out
    with pytest.raises(ad.DispositionError, match="symlink"):
        ad.append(f, dict(asset="bg_beta", disposition="keep", evidence=EV), repo=w.repo, ref=w.last, base="HEAD", reader=T)


def test_f2_a_ledger_path_outside_the_toplevel_is_NOT_CHECKED_and_non_zero_when_a_base_is_passed(w, tmp_path, capsys):
    p = new_ledger(tmp_path, w)
    code, out = cli_out(w, capsys, "--check", str(p), "--base", "HEAD")
    assert code == 1 and "NOT CHECKED" in out and "outside the repository toplevel" in out
    code, out = cli_out(w, capsys, "--check", str(p))              # no explicit base, not the canonical path: reported, exit 0
    assert code == 0 and "NOT CHECKED" in out


def test_f2_a_non_canonical_in_repo_copy_is_NOT_CHECKED(w, tmp_path, capsys):
    p = new_ledger(tmp_path, w)
    (w.repo / "copy.jsonl").write_bytes(p.read_bytes())
    code, out = cli_out(w, capsys, "--check", str(w.repo / "copy.jsonl"), "--base", "HEAD")
    assert code == 1 and "NOT CHECKED" in out and "not the canonical ledger path" in out
    assert ad.validate(w.repo / "copy.jsonl", repo=w.repo, ref=w.last, base="HEAD", require_base=False, reader=T) == []


def test_f2_the_canonical_ledger_behind_a_symlinked_directory_is_NOT_CHECKED_even_without_an_explicit_base(w, tmp_path, capsys):
    p = new_ledger(tmp_path, w)
    app(p, w)
    committed(w, p.read_text(encoding="utf-8"))
    moved = tmp_path / "control_moved"
    (w.repo / "00_ARCHITECTURE/control").rename(moved)
    (w.repo / "00_ARCHITECTURE/control").symlink_to(moved)
    code, out = cli_out(w, capsys, "--check")
    assert code == 1 and "NOT CHECKED" in out


def test_f2_an_append_with_a_base_that_cannot_be_applied_is_refused_and_writes_nothing(w, tmp_path, capsys):
    p = new_ledger(tmp_path, w)
    before = p.read_bytes()
    code, out = cli_out(w, capsys, "--append", "--asset", "ga_alpha", "--disposition", "keep", "--evidence", EV, str(p), "--base", "HEAD")
    assert code == 1 and "NOT CHECKED" in out and p.read_bytes() == before


# ---- F3: the CLI default base is meaningful; the reader override hook is test-only ----

def test_f3_the_default_base_is_the_merge_base_with_origin_main_and_catches_a_rewrite_that_head_hides(w, tmp_path, capsys):
    p = new_ledger(tmp_path, w)
    app(p, w)
    f = committed(w, p.read_text(encoding="utf-8"))
    git(w.repo, "update-ref", "refs/remotes/origin/main", w.last)
    f.write_text(chained([row("ga_alpha", reason="a different history")]), encoding="utf-8")
    git(w.repo, "add", "-A")
    git(w.repo, "commit", "-q", "-m", "rewrite")
    base, note = ad.default_base(T, str(w.repo))
    assert base == w.last and "merge-base" in note
    code, out = cli_out(w, capsys, "--check")
    assert code == 1 and "history rewritten" in out
    code, out = cli_out(w, capsys, "--check", "--base", "HEAD")        # HEAD already holds the rewrite: vacuous
    assert code == 0


def test_f3_without_origin_main_the_default_falls_back_to_head_and_says_it_is_vacuous(w, tmp_path, capsys):
    base, note = ad.default_base(T, str(w.repo))
    assert base == "HEAD" and "VACUOUS" in note
    p = new_ledger(tmp_path, w)
    app(p, w)
    f = committed(w, p.read_text(encoding="utf-8"))
    code, out = cli_out(w, capsys, "--check", str(f))
    assert code == 0 and "VACUOUS" in out


def test_f3_the_tracker_override_env_is_ignored_outside_pytest(monkeypatch, tmp_path):
    monkeypatch.setattr(ad, "_READER", None)
    monkeypatch.setenv("E6_3_TRACKER_UNDER_TEST", str(tmp_path / "evil_tracker.py"))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    R = ad.load_reader()
    assert os.path.samefile(R.__file__, ad.READER_PATH)
    monkeypatch.setattr(ad, "_READER", None)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "x")
    with pytest.raises(FileNotFoundError):             # under pytest the hook is honoured
        ad.load_reader()


# ---- F8: the documented torn-tail recovery works ----

def test_f8_a_torn_tail_is_reported_and_the_documented_truncation_recovers_it(w, tmp_path):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    good = p.read_bytes()
    p.write_bytes(good + b'{"asset": "bg_beta", "disposi')
    assert check(p, w)
    b = p.read_bytes()
    p.write_bytes(b[:b.rfind(b"\n") + 1])             # the recipe in the module docstring
    assert p.read_bytes() == good and check(p, w) == []
    app(p, w, "bg_beta")
    assert check(p, w) == []


def test_f8_the_readme_and_the_docstring_carry_the_documented_caveats():
    readme = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md"), encoding="utf-8").read()
    for needle in ("committed snapshot", "torn", "NOT CHECKED", "no CI caller"):
        assert needle in readme, needle
    assert "COMMITTED SNAPSHOT" in ad.__doc__ and "TORN TAIL" in ad.__doc__


# ---- surviving mutants ----

def test_m08_a_write_that_does_not_read_back_is_truncated_and_raises(w, tmp_path, monkeypatch):
    p = new_ledger(tmp_path, w)
    app(p, w, "ga_alpha")
    before = p.read_bytes()
    real, calls = ad._read_fd, []

    def lying(fd):
        calls.append(1)
        data = real(fd)
        return data if len(calls) == 1 else data[:-3] + b"xyz"      # the readback after the write disagrees
    monkeypatch.setattr(ad, "_read_fd", lying)
    with pytest.raises(OSError, match="read back"):
        app(p, w, "bg_beta")
    assert p.read_bytes() == before


@pytest.mark.parametrize("hdr", [{"asset": "_schema"}, {"asset": "_schema", "_doc": ""}, {"asset": "_schema", "_doc": "  "},
                                 {"asset": "_schema", "_doc": 5}])
def test_m10_a_header_without_a_non_blank_doc_is_refused(w, hdr):
    line = json.dumps(hdr)
    assert has(ad.validate(line + "\n", repo=w.repo, ref=w.last, reader=T), "non-blank `_doc`")


def test_m18_the_duplicate_signature_ignores_the_order_of_additions(w):
    out = probs(w, [row("bg_beta", additions=["D-TIME", "D-GROUNDING"]), row("bg_beta", additions=["D-GROUNDING", "D-TIME"])])
    assert has(out, "duplicate of line 2")
    assert not has(probs(w, [row("bg_beta", additions=["D-TIME"]), row("bg_beta", additions=["D-GROUNDING"])]), "duplicate")


def test_m12_the_prefix_rule_accepts_a_base_without_a_trailing_newline_only_when_the_next_byte_is_one(w):
    base = chained([row("ga_alpha")]).rstrip("\n").encode()
    w.raw[DISP] = base
    w.commit("no trailing newline")
    f = w.repo / DISP
    nxt = json.dumps(dict(row("bg_beta"), seq=2, prev_sha256=sha(base.split(b"\n")[-1])))
    f.write_bytes(base + b"\n" + nxt.encode() + b"\n")
    assert not has(check(f, w, base="HEAD"), "history rewritten")
    f.write_bytes(base + b"X" + nxt.encode() + b"\n")
    assert has(check(f, w, base="HEAD"), "history rewritten")

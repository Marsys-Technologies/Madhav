"""E6.3 -- the pinned interface (Track E brief 8): `asset_elevation_tracker.elevated_assets(ref: str, repo: str) -> set[str]`.

Proves (a) the signature and that it is a module-level function; (b) every input is read from the COMMITTED ref, so a
dirty, deleted or untracked working-tree file changes nothing and an older ref answers as of then; (c) no side
effects and no database; (d) it RAISES -- never an empty set -- on an unreadable ref or path, on every kind of
malformed input, and when E5.5's invalidation watermark is older than the ledger ref.
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from _e6_3_fixtures import (CENSUS, CERTS, DISP, GAPS, MINI_CENSUS, MINI_FLOOR, mini_patch, SEED, World, cert, disp,  # noqa: E402
                            gap, git, inval, jsonl, load_tracker, watermark)

T = load_tracker()
ALL = {"ga_alpha", "bg_beta", "ka_gamma"}


@pytest.fixture(autouse=True)
def mini_floor(monkeypatch):
    mini_patch(monkeypatch, T)


@pytest.fixture
def w(tmp_path):
    w = World(tmp_path).default()
    w.commit()
    return w


# ───────────────────────── signature ─────────────────────────

def test_signature_is_module_level_ref_repo_to_set():
    f = T.elevated_assets
    assert inspect.isfunction(f) and f.__module__ == T.__name__ and f.__qualname__ == "elevated_assets"
    sig = inspect.signature(f)
    assert list(sig.parameters) == ["ref", "repo"]
    assert all(p.kind is p.POSITIONAL_OR_KEYWORD and p.default is p.empty for p in sig.parameters.values())
    assert sig.parameters["ref"].annotation in (str, "str") and sig.parameters["repo"].annotation in (str, "str")
    assert sig.return_annotation in (set, "set", "set[str]")


def test_returns_a_fresh_set_of_str(w):
    a, b = w.elevated(T), w.elevated(T)
    assert type(a) is set and a == b and a is not b and all(isinstance(x, str) for x in a)


def test_a_ref_may_be_a_branch_a_tag_or_a_sha(w):
    git(w.repo, "tag", "ledger-v1")
    assert w.elevated(T, "main") == w.elevated(T, "ledger-v1") == w.elevated(T, w.last) == ALL


# ───────────────────────── committed-ref reads ─────────────────────────

def test_a_dirty_working_tree_changes_nothing(w):
    before = w.elevated(T)
    (w.repo / CERTS).write_text(jsonl([]), encoding="utf-8")                      # every certificate "removed"
    (w.repo / GAPS).write_text(jsonl([gap("ga_alpha", "Idem.pat")]), encoding="utf-8")
    (w.repo / DISP).write_text(jsonl([]), encoding="utf-8")
    (w.repo / SEED).write_text("garbage not a seed\n", encoding="utf-8")
    (w.repo / CENSUS).write_text("syntax error (((", encoding="utf-8")
    assert git(w.repo, "status", "--porcelain")                                   # genuinely dirty
    assert w.elevated(T, w.last) == before == ALL


def test_deleted_and_untracked_working_files_change_nothing(w):
    for rel in (CERTS, GAPS, DISP, CENSUS, SEED):
        os.unlink(w.repo / rel)
    (w.repo / "00_ARCHITECTURE/control/asset_certs.jsonl.new").write_text("x", encoding="utf-8")
    assert w.elevated(T, w.last) == ALL


def test_a_staged_but_uncommitted_change_changes_nothing(w):
    (w.repo / GAPS).write_text(jsonl([gap("ga_alpha", "Idem.pat")]), encoding="utf-8")
    git(w.repo, "add", GAPS)
    assert w.elevated(T, w.last) == ALL
    assert w.elevated(T, "HEAD") == ALL


def test_an_older_ref_answers_as_of_that_commit(w):
    first = w.last
    w.gaps.append(gap("ga_alpha", "Idem.pat"))
    second = w.commit("a gap opens")
    assert w.elevated(T, first) == ALL
    assert w.elevated(T, second) == ALL - {"ga_alpha"}


def test_the_ref_is_resolved_once_so_a_moving_branch_cannot_split_the_read(w, monkeypatch):
    # every read after the first uses the resolved sha: spy on the git calls and check none carries a symbolic ref
    seen = []
    real = T._e63_git

    def spy(repo, args, what):
        seen.append(list(args))
        return real(repo, args, what)

    monkeypatch.setattr(T, "_e63_git", spy)
    assert w.elevated(T, "main") == ALL
    shows = [a[1] for a in seen if a and a[0] == "show"]
    assert shows and all(s.startswith(w.last + ":") for s in shows)


# ───────────────────────── no side effects, no database ─────────────────────────

def _snapshot(root):
    snap = {}
    for dp, dn, fn in os.walk(root):
        if ".git" in dp.split(os.sep):
            continue
        for f in fn:
            p = os.path.join(dp, f)
            st = os.stat(p)
            snap[p] = (st.st_mtime_ns, st.st_size)
    return snap


def test_no_side_effects_and_no_database(w, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://nobody:" + "x" * 4 + chr(64) + "127.0.0.1:1/none")
    monkeypatch.setenv("NIKASHA_CONTROL_DIR", "/nonexistent/control")
    before_tree, before_status, before_head = _snapshot(w.repo), git(w.repo, "status", "--porcelain"), git(w.repo, "rev-parse", "HEAD")
    refs_before = git(w.repo, "for-each-ref")
    assert w.elevated(T) == ALL
    assert _snapshot(w.repo) == before_tree
    assert git(w.repo, "status", "--porcelain") == before_status and git(w.repo, "rev-parse", "HEAD") == before_head
    assert git(w.repo, "for-each-ref") == refs_before


def test_it_runs_with_the_cwd_elsewhere(w, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert w.elevated(T) == ALL


# ───────────────────────── raises: unreadable ─────────────────────────

@pytest.mark.parametrize("ref", ["no-such-branch", "0" * 40, "HEAD~50", "refs/heads/nope"])
def test_raises_on_an_unreadable_ref(w, ref):
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T, ref)


@pytest.mark.parametrize("bad", [None, "", "  ", "-x", " main", 7])
def test_raises_on_a_malformed_ref(w, bad):
    with pytest.raises(T.ElevatedInputError):
        T.elevated_assets(bad, str(w.repo))


def test_raises_when_the_repo_is_not_a_repository(tmp_path):
    with pytest.raises(T.ElevatedInputError):
        T.elevated_assets("HEAD", str(tmp_path / "does-not-exist"))
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(T.ElevatedInputError):
        T.elevated_assets("HEAD", str(plain))


@pytest.mark.parametrize("path", [CERTS, GAPS, DISP, CENSUS, SEED])
def test_raises_when_any_input_path_is_absent_at_the_ref(w, path):
    w.raw[path] = None
    w.commit("delete one input")
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    assert e.value.code == "unreadable"


def test_a_failure_is_never_an_empty_set(w):
    w.raw[CERTS] = None
    w.commit()
    try:
        r = w.elevated(T)
    except T.ElevatedInputError:
        return
    pytest.fail(f"returned {r!r} for an unreadable input")


# ───────────────────────── raises: malformed ─────────────────────────

def _bad(w, path, text, code=None):
    w.raw[path] = text
    w.commit("malform one input")
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    if code:
        assert e.value.code == code
    return e.value


@pytest.mark.parametrize("path", [CERTS, GAPS, DISP])
def test_a_malformed_jsonl_line_raises_in_every_ledger(w, path):
    good = w.render()[path]
    _bad(w, path, good + "{this is not json\n", "malformed")


@pytest.mark.parametrize("path", [CERTS, GAPS, DISP])
def test_a_truncated_final_line_raises(w, path):
    good = w.render()[path].rstrip("\n")
    _bad(w, path, good[:-5] + "\n", "malformed")


@pytest.mark.parametrize("path", [CERTS, GAPS, DISP])
def test_a_non_object_line_raises(w, path):
    _bad(w, path, w.render()[path] + "[1, 2]\n", "malformed")


@pytest.mark.parametrize("path", [CERTS, GAPS, DISP])
def test_a_ledger_whose_first_line_is_not_the_schema_row_raises(w, path):
    w.gaps.append(gap("ga_alpha", "Cost.base"))                  # every ledger has a data row, so dropping the schema row is visible
    lines = w.render()[path].split("\n", 1)[1]
    _bad(w, path, lines, "malformed")


@pytest.mark.parametrize("path", [CERTS, GAPS, DISP])
def test_an_empty_ledger_raises(w, path):
    _bad(w, path, "", "malformed")


def test_invalid_utf8_raises(w):
    w.raw[CERTS] = b"\xff\xfe\x00 not utf8\n"
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


def test_a_bad_json_line_in_the_middle_is_not_skipped_even_when_the_rest_is_fine(w):
    lines = w.render()[CERTS].split("\n")
    lines.insert(3, "{broken")
    _bad(w, CERTS, "\n".join(lines), "malformed")


@pytest.mark.parametrize("mutate,why", [
    (lambda r: r.update(verdict="MAYBE"), "unknown verdict"),
    (lambda r: r.update(generation=0), "generation"),
    (lambda r: r.update(generation="1"), "generation type"),
    (lambda r: r.update(cert_id="ga_alpha|gate|Idem.pat@9"), "cert_id"),
    (lambda r: r.update(layer="L5"), "layer vs prefix"),
    (lambda r: r.update(kind="thing"), "kind"),
    (lambda r: r.update(writer_hashes={"/abs/path.py": "a" * 64}), "absolute writer path"),
    (lambda r: r.update(writer_hashes={"p.py": "ABC"}), "writer hash"),
    (lambda r: r.update(upstream_cert_ids=["nonsense"]), "upstream id"),
    (lambda r: r.update(semantic_fingerprint="xyz"), "fingerprint"),
    (lambda r: r.update(evidence={}), "no census run id"),
    (lambda r: r.update(detector=""), "detector"),
    (lambda r: r.update(gate="Build"), "gate vs registry"),
    (lambda r: r.update(na="yes"), "na type"),
])
def test_a_malformed_certificate_record_raises(w, mutate, why):
    mutate(w.find("ga_alpha", "Idem.pat"))
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


def test_generations_that_are_not_1_to_n_raise(w):
    w.certs.append(cert("ga_alpha", "Idem.pat", gen=3))
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


@pytest.mark.parametrize("mutate", [
    lambda r: r.update(state="DONE"), lambda r: r.update(kind="wish"), lambda r: r.pop("asset"),
    lambda r: r.update(criterion=5), lambda r: r.update(superseded_by="no-such-gap"),
])
def test_a_malformed_gap_row_raises(w, mutate):
    row = gap("ga_alpha", "Idem.pat", state="CLOSED")
    mutate(row)
    w.gaps.append(row)
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


@pytest.mark.parametrize("mutate", [
    lambda r: r.update(disposition="P"), lambda r: r.update(disposition="Keep"), lambda r: r.update(asset="zz_unknown"), lambda r: r.update(asset="ga_ghost"),
    lambda r: r.update(additions="D-TIME"), lambda r: r.update(additions=["Idem.pat"]), lambda r: r.update(additions=["a", "a"]),
])
def test_a_malformed_disposition_row_raises(w, mutate):
    row = disp("ga_alpha", "keep")
    mutate(row)
    w.seed_exclude = {"ga_ghost"}
    w.disps.append(row)
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


@pytest.mark.parametrize("mutate", [
    lambda r: r.update(invalidates="junk"),
    lambda r: r.update(invalidates="ga_alpha|gate|Idem.pat@9"),                       # a generation that does not exist
    lambda r: r.update(invalidates="ga_nobody|gate|Idem.pat@1"),
    lambda r: r.update(reason=[]), lambda r: r.update(reason=[{"nocode": 1}]),
    lambda r: r.update(walk=0), lambda r: r.update(walk=True),
    lambda r: r.update(asset="bg_beta"), lambda r: r.update(layer="L0"), lambda r: r.update(layer="L9"),
    lambda r: r.update(type="surprise"),                                              # an event type nobody reads
    lambda r: r.update(kind="gate"),                                                  # an event may not carry a certificate kind
    lambda r: r.update(cert_key="ga_alpha|invalidation|x"),                           # nor a certificate-only field
    lambda r: r.update(verdict="PASS"),
])
def test_a_malformed_invalidation_line_raises(w, mutate):
    row = inval("ga_alpha|gate|Idem.pat@1")
    mutate(row)
    w.invals.append(row)
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


def test_an_invalidation_of_a_certificate_on_a_later_line_raises(w):
    row = inval("ga_alpha|gate|Idem.pat@1")
    w.certs.insert(0, row)                                  # the invalidation precedes the cert it names
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


def test_the_same_certificate_invalidated_twice_is_tolerated_and_still_invalidated(w):
    w.invals += [inval("ga_alpha|gate|Idem.pat@1"), inval("ga_alpha|gate|Idem.pat@1", walk=2)]   # two racing E5.5 runs
    w.commit()
    assert w.elevated(T) == ALL - {"ga_alpha"}


def test_an_epoch_reset_event_is_accepted_and_changes_nothing(w):
    from _e6_3_fixtures import epoch_reset
    w.invals.append(epoch_reset())
    w.commit()
    assert w.elevated(T) == ALL


def test_an_event_type_nobody_reads_raises_even_if_the_rest_of_the_line_is_well_formed(w):
    from _e6_3_fixtures import epoch_reset
    row = epoch_reset()
    row["type"] = "surprise"                                 # an epoch_reset-shaped line under an unknown type
    w.invals.append(row)
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


@pytest.mark.parametrize("mutate", [lambda r: r.update(decision="x"), lambda r: r.update(layer="L9"),
                                    lambda r: r.update(asset="ga_alpha"), lambda r: r.pop("decision")])
def test_a_malformed_epoch_reset_raises(w, mutate):
    from _e6_3_fixtures import epoch_reset
    row = epoch_reset()
    mutate(row)
    w.invals.append(row)
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


def test_an_unparseable_or_incomplete_registry_source_raises(tmp_path):
    bad_sources = ["def broken(((", "x = 1\n", MINI_CENSUS.replace("CELL_GATES", "CELLS"),
                   MINI_CENSUS.replace("revision=2", "revision=two"),
                   MINI_CENSUS.replace('NA_RULE_DECISIONS: dict[str, str] = {"Null.x#columns_any": "N-22a"}',
                                       "NA_RULE_DECISIONS = dict(a=compute())")]
    for i, census in enumerate(bad_sources):
        sub = tmp_path / f"c{i}"
        sub.mkdir()
        w = World(sub).default()
        w.census = census
        w.commit()
        with pytest.raises(T.ElevatedInputError):
            w.elevated(T)


def test_an_upstream_that_is_not_on_an_earlier_line_raises_so_no_cycle_can_exist(w):
    w.find("ga_alpha", "Idem.pat")["upstream_cert_ids"] = ["ga_alpha|gate|Idem.alt@1"]
    w.find("ga_alpha", "Idem.alt")["upstream_cert_ids"] = ["ga_alpha|gate|Idem.pat@1"]
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


def test_an_upstream_id_missing_from_the_ledger_raises(w):
    w.find("ga_alpha", "Idem.pat")["upstream_cert_ids"] = ["ga_alpha|gate|Nope.x@1"]
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


# ───────────────────────── raises: E5.5's watermark (inside asset_certs.jsonl) ─────────────────────────

def test_a_certificate_after_the_last_watermark_raises_the_dedicated_error(w):
    w.tail_certs.append(cert("ga_alpha", "Ldgr.src", gen=2))                         # certified, never evaluated by E5.5
    w.commit()
    with pytest.raises(T.WatermarkOlderThanLedger) as e:
        w.elevated(T)
    assert isinstance(e.value, T.ElevatedInputError) and e.value.code == "watermark_older"


def test_the_watermark_older_error_is_not_swallowed_by_a_terminal_only_world(tmp_path):
    w = World(tmp_path)
    w.disps.append(disp("ka_gamma", "retire", reason="r"))
    w.watermark = None
    w.tail_certs.append(cert("ga_alpha", "Idem.pat"))
    w.certs = []
    w.commit()
    with pytest.raises(T.ElevatedInputError):                    # no watermark at all, a certificate present
        w.elevated(T)


def test_a_watermark_covering_every_certificate_is_accepted_and_later_events_do_not_make_it_behind(w):
    w.invals.append(inval("ga_alpha|gate|Idem.pat@1"))
    w.commit()
    assert w.elevated(T) == ALL - {"ga_alpha"}
    from _e6_3_fixtures import chained
    w.raw[CERTS] = chained(w.ledger_rows() + [inval("ga_alpha|gate|Ldgr.src@1", walk=2)])   # an event AFTER the watermark
    w.commit()
    assert w.elevated(T) == ALL - {"ga_alpha"}


def test_an_earlier_watermark_is_truthful_at_its_own_place_and_the_last_one_governs(w):
    from _e6_3_fixtures import chained
    first = w.certs[:3]
    rows = first + [watermark(first)] + w.certs[3:]
    rows.append(watermark(rows))
    w.raw[CERTS] = chained(rows)
    w.commit()
    assert w.elevated(T) == ALL


def test_a_watermark_that_covers_only_part_of_the_certificates_leaves_the_rest_behind(w):
    w.watermark = dict(covers_seq=5, certs_processed=5, last_cert_id=w.certs[4]["cert_id"])
    w.commit()
    with pytest.raises(T.WatermarkOlderThanLedger):
        w.elevated(T)


def test_no_watermark_line_raises(w):
    w.watermark = None
    w.commit()
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    assert e.value.code == "watermark_missing"


@pytest.mark.parametrize("over", [dict(certs_processed=3), dict(certs_processed=999), dict(last_cert_id="x|gate|y@1"),
                                  dict(last_cert_id=None), dict(covers_seq=-1), dict(covers_seq=10_000)])
def test_a_watermark_that_miscounts_misnames_or_overreaches_raises(w, over):
    w.watermark = over
    w.commit()
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    assert e.value.code == "watermark_mismatch"


def test_a_late_smaller_truthful_watermark_is_accepted_and_the_largest_covers_seq_governs(w):
    # E5.5's rule (watermark_status uses the furthest evaluation): a smaller truthful watermark appended later is fine
    from _e6_3_fixtures import chained
    rows = list(w.certs)
    rows.append(watermark(rows))
    rows.append(dict(watermark(rows[:3]), covers_seq=2, certs_processed=2, last_cert_id=rows[1]["cert_id"]))
    w.raw[CERTS] = chained(rows)
    w.commit()
    assert w.elevated(T) == ALL


def test_a_late_smaller_watermark_does_not_cover_certificates_the_largest_one_does_not(w):
    from _e6_3_fixtures import chained
    rows = list(w.certs[:5])
    rows.append(watermark(rows))                                  # covers the first 5
    rows += w.certs[5:]                                           # certificates after it
    rows.append(dict(watermark(rows[:3]), covers_seq=2, certs_processed=2, last_cert_id=rows[1]["cert_id"]))
    w.raw[CERTS] = chained(rows)
    w.commit()
    with pytest.raises(T.WatermarkOlderThanLedger):
        w.elevated(T)


@pytest.mark.parametrize("over", [dict(asset="ga_alpha"), dict(covers_seq="9"), dict(covers_seq=True),
                                  dict(certs_processed="9"), dict(certs_processed=True), dict(commit=""),
                                  dict(cert_key="_ledger|watermark|global")])
def test_a_malformed_watermark_line_raises(w, over):
    w.watermark = over
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


def test_the_watermark_is_read_from_the_committed_ref_not_the_working_tree(w):
    first = w.last
    (w.repo / CERTS).write_text("not a ledger\n", encoding="utf-8")                 # dirty
    assert w.elevated(T, first) == ALL


def test_the_dedicated_exception_classes_are_exported():
    assert issubclass(T.WatermarkOlderThanLedger, T.ElevatedInputError) and issubclass(T.ElevatedInputError, RuntimeError)


# ───────────────────────── the legacy tracker still works ─────────────────────────

def test_the_existing_cli_surface_is_intact():
    for name in ("GATES", "LAYERS", "lifecycle", "scan", "main", "registry", "jsonl", "ACTIVE_PREDICATE"):
        assert hasattr(T, name), name
    state, why = T.lifecycle(None, None, [], [], [])
    assert state in ("NO_BRIEF", "NOT_IN_REGISTRY", "BRIEF_DRAFT", "BRIEF_ACCEPTED", "GAPS_REGISTERED", "ELEVATED",
                     "CERTIFYING", "CERTIFIED_GAPS_OPEN", "LEDGER_INVALID")

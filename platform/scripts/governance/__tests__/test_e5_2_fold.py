"""test_e5_2_fold.py — Suvarna E5.2: the fold script (`nikasha_fold.py`).

What the fold must PROVE (Track E brief §7 row E5.2): register state transitions; `--emit-gaps` with the withholding list
(`00_ARCHITECTURE/control/NIKASHA_WITHHOLDING.json`, today `bo_upaya-Idem.pattern`); computed tallies; fingerprints; drift.
Every rule below has a seeded defect (a hand-edited tally, a withheld pair that would be credited, an illegal
transition, a rewritten ledger line, ...) and a test that fails when the rule is removed (mutation list: see the E5.2
close note). Offline: tmp registers, tmp ledgers, tmp git repos; no database, no network.

THE REAL LEDGERS AND THE REAL REGISTER ARE NEVER WRITTEN HERE: a session guard hashes `asset_gaps.jsonl`,
`asset_certs.jsonl`, the register and `NIKASHA_WITHHOLDING.json` before and after the whole module and fails on any
difference; every write below goes to a tmp copy.
"""
from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import fcntl

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import nikasha_certify as nc  # noqa: E402
import nikasha_fold as nf  # noqa: E402

REPO = HERE.parents[3]
REAL = {k: REPO / rel for k, rel in dict(
    register=nf.REGISTER_REL, gaps=nf.GAPS_REL, certs=nf.CERTS_REL, withholding=nf.WITHHOLDING_REL).items()}


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


@pytest.fixture(scope="module", autouse=True)
def real_files_never_written():
    before = {k: _h(p) for k, p in REAL.items()}
    yield
    assert {k: _h(p) for k, p in REAL.items()} == before, "a test wrote to a REAL ledger / register / withholding file"


# ───────────────────────────── fixtures ─────────────────────────────

ORDER = ("CLOSED_ON_BRANCH", "OPEN", "CLOSED", "DONE", "PARTIAL", "MEASURED", "DEFERRED", "WITHDRAWN", "IN_PROGRESS")
DISPLAY = ("OPEN", "IN_PROGRESS", "CLOSED_ON_BRANCH", "PARTIAL", "DEFERRED", "DONE", "CLOSED", "MEASURED", "WITHDRAWN")
LABEL = {"MEASURED": "MEASURED in P6"}
SEV = ("BLOCKS_FREEZE", "BLOCKS_LAYER", "DEGRADES", "COSMETIC")


def cls_of(state: str) -> str:
    t = state.strip().lstrip("*").strip().upper()
    return next(c for c in ORDER if t.startswith(c))


DEFAULT_ROWS = [
    ("R01", "COSMETIC", "OPEN — wording", 1),
    ("R02", "BLOCKS_FREEZE", "**OPEN** — a blocker", 1),
    ("R03", "BLOCKS_LAYER", "CLOSED — done in wave 1", 1),
    ("R04", "DEGRADES", "DONE", 1),
    ("R05", "DEGRADES", "PARTIAL — half", 1),
    ("R06", "COSMETIC", "MEASURED in P6", 1),
    ("R07", "BLOCKS_FREEZE", "CLOSED_ON_BRANCH — on a branch", 1),
    ("R20", "BLOCKS_LAYER", "OPEN", 2),
    ("R21", "DEGRADES", "OPEN — x", 2),
]


def make_register(rows=None, *, with_header_for=None, tweak=None) -> str:
    """A register in the real format with a header built INDEPENDENTLY of the fold's code (plain counting here)."""
    rows = list(DEFAULT_ROWS if rows is None else rows)
    n = len(rows)
    by_state = collections.Counter(cls_of(s) for _, _, s, _ in rows)
    by_sev = collections.Counter(v for _, v, _, _ in rows)
    open_sev = collections.Counter(v for _, v, s, _ in rows if cls_of(s) == "OPEN")
    bf_ids = [i for i, v, s, _ in rows if cls_of(s) == "OPEN" and v == "BLOCKS_FREEZE"]
    shown = [c for c in DISPLAY if by_state.get(c) or (with_header_for and c in with_header_for)]
    state_rows = "\n".join(f"| {LABEL.get(c, c)} | {by_state.get(c, 0)} |" for c in shown)
    sev_rows = "\n".join(f"| {s} | {by_sev.get(s, 0)} | meaning of {s} |" for s in SEV)
    open_line = (f"All {n} rows, every state. **Open rows only ({by_state.get('OPEN', 0)}):** "
                 + " · ".join(f"{s} {open_sev.get(s, 0)}" + (f" ({', '.join(bf_ids)})" if s == "BLOCKS_FREEZE" and bf_ids else "")
                              for s in SEV) + ".")
    t1 = "\n".join(f"| {i} | change {i} | src | {v} | — | 0.5 | {s} |" for i, v, s, t in rows if t == 1)
    t2 = "\n".join(f"| {i} | change {i} | cls | when | {v} | — | 2 | {s} |" for i, v, s, t in rows if t == 2)
    text = f"""---
artifact: TEST_REGISTER
version: "9.9"
---

# Test register

## 0 · Index

**Total rows: {n}** (R01–R21 test rows)

### 0.1 · Count by state

| state | count |
|---|---|
{state_rows}
| **total** | **{n}** |

### 0.2 · Count by severity

| severity | count | meaning |
|---|---|---|
{sev_rows}

{open_line}

### 0.3 · Where the rows live

prose with R99 mentioned in passing.

## 2 · The register

### 2.1 · Tier 1

| # | change | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
{t1}

### 2.2 · Build system

| # | change | class | when | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|---|
{t2}

## 3 · Epilogue

trailing prose
"""
    return tweak(text) if tweak else text


@pytest.fixture
def reg(tmp_path):
    p = tmp_path / "REGISTER.md"
    p.write_text(make_register(), encoding="utf-8")
    return p


class ReviewRepo:
    """A real tmp git repo holding the one reviews root, a fix commit (touching src/fix.py), a descendant `later`, a
    commit `side` on another branch (not an ancestor of HEAD) and the base commit before the fix."""

    def __init__(self, repo):
        self.repo = repo
        self.root = repo / nf.REVIEWS_REL.rstrip("/")
        self.n = 0

    def git(self, *a):
        return git(self.repo, *a)

    def head(self):
        return self.git("rev-parse", "HEAD").strip()

    def commit_file(self, rel, content, msg="c"):
        f = self.repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
        self.git("add", "--", rel)
        self.git("commit", "-q", "-m", msg)
        return self.head()

    def record(self, *, row="R01", verdict="ACCEPT", sha=None, reviewer="gate-reviewer", corrections=None,
               body="# Review\n\nfree text\n", fm=None, commit=True, name=None):
        sha = sha or self.fix
        if fm is None:
            lines = ["---", f"row: {row}", f"reviewed_sha: {sha}", f"verdict: {verdict}", f"reviewer: {reviewer}"]
            if corrections:
                lines.append(f"corrections_sha: {corrections}")
            fm = "\n".join(lines + ["---"]) + "\n"
        self.n += 1
        rel = f"{nf.REVIEWS_REL}{name or f'Q_REVIEW_{self.n}.md'}"
        f = self.repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(fm + body)
        if commit:
            self.git("add", "--", rel)
            self.git("commit", "-q", "-m", f"review {self.n}")
        return f

    def reaccept(self, *, row="R01", sha=None, corrections=None, **kw):
        return self.record(row=row, verdict="RE_ACCEPTED", sha=sha, corrections=corrections or self.later, **kw)


def _make_review_repo(tmp_path):
    repo = tmp_path / "rrepo"
    (repo / nf.REVIEWS_REL).mkdir(parents=True)
    (repo / nf.REVIEWS_REL / ".gitkeep").write_text("")
    (repo / "src").mkdir()
    (repo / "src/fix.py").write_text("v1\n")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    rr = ReviewRepo(repo)
    rr.base = rr.head()
    rr.fix = rr.commit_file("src/fix.py", "v2\n", "the fix")
    rr.later = rr.commit_file("src/later.py", "x\n", "later")
    git(repo, "checkout", "-q", "-b", "side", rr.base)
    rr.side = rr.commit_file("src/side.py", "s\n", "side")
    git(repo, "checkout", "-q", "main")
    return rr


@pytest.fixture
def reviews(tmp_path):
    return _make_review_repo(tmp_path)


@pytest.fixture(scope="module")
def shared_reviews(tmp_path_factory):
    """One review repo + one ACCEPT record for R01, shared by the (81-case) transition matrix."""
    rr = _make_review_repo(tmp_path_factory.mktemp("shared_rr"))
    rr.accept_r01 = rr.record(row="R01")
    return rr


def fold(reg, row, to, reviews=None, **kw):
    kw.setdefault("reason", "because the evidence says so")
    kw.setdefault("evidence", "commit abc1234")
    if reviews is not None:
        kw.setdefault("repo", reviews.repo)
        if to in nf.NEEDS_REVIEW and "review" not in kw:
            kw["review"] = reviews.record(row=row)
    return nf.set_state(reg, row, to, **kw)


def refused(fn, *a, **kw):
    with pytest.raises(nf.FoldRefused) as e:
        fn(*a, **kw)
    return e.value.code


# ───────────────────────────── register: state transitions ─────────────────────────────

# The policy pinned here independently of the module's own table (Q1 default).
ALLOWED = {
    "OPEN": {"IN_PROGRESS", "PARTIAL", "CLOSED_ON_BRANCH", "DONE", "CLOSED", "DEFERRED", "WITHDRAWN"},
    "IN_PROGRESS": {"OPEN", "PARTIAL", "CLOSED_ON_BRANCH", "DONE", "CLOSED", "DEFERRED", "WITHDRAWN"},
    "PARTIAL": {"OPEN", "IN_PROGRESS", "CLOSED_ON_BRANCH", "DONE", "CLOSED", "DEFERRED", "WITHDRAWN"},
    "CLOSED_ON_BRANCH": {"OPEN", "PARTIAL", "DONE", "CLOSED"},
    "DEFERRED": {"OPEN", "IN_PROGRESS", "DONE", "CLOSED", "WITHDRAWN"},
    "DONE": {"OPEN"},
    "CLOSED": {"OPEN"},
    "MEASURED": {"OPEN", "DONE", "CLOSED"},
    "WITHDRAWN": set(),
}
STATE_TEXT = {c: (c if c != "MEASURED" else "MEASURED in P6") + " — seeded" for c in ORDER}
TARGETS = [c for c in ORDER if c != "MEASURED"]


def one_row_register(state_text, sev="DEGRADES"):
    return make_register([("R01", sev, state_text, 1), ("R02", "COSMETIC", "OPEN", 1)])


@pytest.mark.parametrize("frm", ORDER)
@pytest.mark.parametrize("to", ORDER)
def test_transition_matrix(tmp_path, shared_reviews, frm, to):
    reviews = shared_reviews
    reviews_kw = dict(review=reviews.accept_r01)
    p = tmp_path / "R.md"
    p.write_text(one_row_register(STATE_TEXT[frm]), encoding="utf-8")
    before = p.read_bytes()
    if to == "MEASURED":
        assert refused(fold, p, "R01", to, reviews, **reviews_kw) == "bad_target_state"
        assert p.read_bytes() == before
    elif frm == to:
        assert refused(fold, p, "R01", to, reviews, **reviews_kw) == "no_change"
        assert p.read_bytes() == before
    elif to in ALLOWED[frm]:
        r = fold(p, "R01", to, reviews, **reviews_kw)
        assert (r["from_state"], r["to_state"]) == (frm, to)
        assert nf.parse_register(p.read_text())["rows"]["R01"].state_class == to
        assert nf.header_drift(p.read_text()) == []
    else:
        assert refused(fold, p, "R01", to, reviews, **reviews_kw) == "illegal_transition"
        assert p.read_bytes() == before        # an illegal transition writes nothing


def test_transition_table_is_exactly_the_pinned_policy():
    assert {k: set(v) for k, v in nf.TRANSITIONS.items()} == ALLOWED


def test_only_the_target_row_and_the_header_change(reg, reviews):
    before = reg.read_text().split("\n")
    fold(reg, "R01", "PARTIAL", reviews)
    after = reg.read_text().split("\n")
    assert len(before) == len(after)
    changed = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
    rows = [i for i in changed if re.match(r"^\| R\d+ ", after[i])]
    assert len(rows) == 1 and after[rows[0]].startswith("| R01 |")
    # the changed row differs only in its LAST cell (state); every other cell is byte-identical
    assert before[rows[0]].split("|")[:-2] == after[rows[0]].split("|")[:-2]
    assert after[rows[0]].split("|")[-2].strip().startswith("PARTIAL — ")
    # every other changed line is a header tally line
    for i in changed:
        if i not in rows:
            assert re.match(r"^(\| (OPEN|PARTIAL) \||All \d+ rows)", after[i]), after[i]


def test_state_cell_is_edited_in_the_second_table_layout(reg, reviews):
    """R20 sits in a table with different columns (state is the 8th); severity must stay in its own cell."""
    fold(reg, "R20", "CLOSED", reviews)
    row = [l for l in reg.read_text().split("\n") if l.startswith("| R20 |")][0]
    cells = [c.strip() for c in row.split("|")]
    assert cells[1:6] == ["R20", "change R20", "cls", "when", "BLOCKS_LAYER"]
    assert cells[6:8] == ["—", "2"]
    assert cells[8].startswith("CLOSED — ")
    assert nf.header_drift(reg.read_text()) == []


def test_set_state_recomputes_the_header_not_just_the_row(reg, reviews):
    fold(reg, "R02", "WITHDRAWN", reviews)                       # an OPEN BLOCKS_FREEZE row leaves the open line
    t = reg.read_text()
    assert "| OPEN | 3 |" in t and "| WITHDRAWN | 1 |" in t and "**Total rows: 9**" in t
    assert re.search(r"\*\*Open rows only \(3\):\*\* BLOCKS_FREEZE 0 · BLOCKS_LAYER 1 · DEGRADES 1 · COSMETIC 1\.", t)


def test_a_reopen_needs_a_reason_but_no_review(reg, reviews):
    assert refused(nf.set_state, reg, "R03", "OPEN", "") == "reason_required"
    nf.set_state(reg, "R03", "OPEN", "regressed in wave 2")
    assert nf.parse_register(reg.read_text())["rows"]["R03"].state_class == "OPEN"


@pytest.mark.parametrize("to,kw,code", [
    ("IN_PROGRESS", dict(reason=""), "reason_required"),
    ("IN_PROGRESS", dict(reason="   "), "reason_required"),
    ("DEFERRED", dict(evidence=None), "evidence_required"),
    ("WITHDRAWN", dict(evidence=""), "evidence_required"),
    ("CLOSED", dict(evidence=None), "evidence_required"),
    ("DONE", dict(review=None), "review_required"),
    ("CLOSED_ON_BRANCH", dict(review=None), "review_required"),
    ("PARTIAL", dict(review=None), "review_required"),
])
def test_a_fold_without_its_reason_evidence_or_verdict_is_refused(reg, reviews, to, kw, code):
    before = reg.read_bytes()
    base = dict(reason="why", evidence="ev", review=reviews.record(row="R01"), repo=reviews.repo)
    base.update(kw)
    assert refused(nf.set_state, reg, "R01", to, **base) == code
    assert reg.read_bytes() == before


def test_deferred_and_withdrawn_need_evidence_but_no_review(reg, reviews):
    nf.set_state(reg, "R01", "DEFERRED", "waiting on B.U", evidence="SS decision N-6", repo=reviews.repo)
    nf.set_state(reg, "R02", "WITHDRAWN", "obsolete", evidence="SS decision N-9", repo=reviews.repo)


def test_unknown_and_malformed_rows_are_refused(tmp_path, reviews):
    p = tmp_path / "R.md"
    bad = make_register(tweak=lambda t: t.replace("| R01 | change R01 | src | COSMETIC | — | 0.5 | OPEN — wording |",
                                                  "| R01 | change R01 | src | COSMETIC | — | 0.5 | extra | OPEN — wording |"))
    p.write_text(bad)
    assert refused(fold, p, "R01", "IN_PROGRESS", reviews) == "row_malformed"
    assert refused(fold, p, "R77", "IN_PROGRESS", reviews) == "unknown_row"
    assert refused(fold, p, "r01", "IN_PROGRESS", reviews) == "bad_row_id"
    assert refused(fold, p, "R02", "NOPE", reviews) == "bad_target_state"


def test_duplicate_rows_are_refused(tmp_path, reviews):
    p = tmp_path / "R.md"
    p.write_text(make_register(DEFAULT_ROWS + [("R01", "COSMETIC", "OPEN", 1)]))
    assert refused(fold, p, "R02", "IN_PROGRESS", reviews) == "register_duplicate_rows"


def test_a_pipe_in_the_reason_cannot_break_the_row(reg, reviews):
    fold(reg, "R01", "IN_PROGRESS", reviews, reason="a | b | c")
    reg_after = nf.parse_register(reg.read_text())
    assert not reg_after["malformed"]
    assert reg_after["rows"]["R01"].state_class == "IN_PROGRESS"


def test_set_state_refuses_a_recompute_that_moves_another_row_or_leaves_the_header_drifted(reg, reviews, monkeypatch):
    """The self-checks run before anything is written: no other row's cells may move; the header must be consistent."""
    real = nf.apply_tally
    before = reg.read_bytes()
    monkeypatch.setattr(nf, "apply_tally", lambda t: real(t).replace("change R03", "change R03 moved"))
    assert refused(fold, reg, "R01", "PARTIAL", reviews) == "self_check_failed"
    monkeypatch.setattr(nf, "apply_tally", lambda t: t)                  # a recompute that did nothing
    assert refused(fold, reg, "R01", "PARTIAL", reviews) == "self_check_failed"
    # the target row must classify as the target (header kept consistent so only THIS check can fire)
    monkeypatch.setattr(nf, "apply_tally", lambda t: real(t.replace("PARTIAL — because the evidence says so", "OPEN")))
    with pytest.raises(nf.FoldRefused) as e:
        fold(reg, "R01", "PARTIAL", reviews)
    assert e.value.code == "self_check_failed" and "would classify as OPEN, not PARTIAL" in e.value.message
    assert reg.read_bytes() == before


def test_dry_run_writes_nothing(reg, reviews):
    before = reg.read_bytes()
    r = fold(reg, "R01", "IN_PROGRESS", reviews, write=False)
    assert r["written"] is False and reg.read_bytes() == before


def test_set_state_corrects_a_drifted_header_and_says_so(tmp_path, reviews):
    p = tmp_path / "R.md"
    p.write_text(make_register().replace("| OPEN | 4 |", "| OPEN | 99 |"))
    assert nf.header_drift(p.read_text())
    r = fold(p, "R01", "IN_PROGRESS", reviews)
    assert r["header_was_drifted"] is True and nf.header_drift(p.read_text()) == []


def test_the_register_is_replaced_atomically_and_keeps_its_mode(reg, reviews):
    os.chmod(reg, 0o640)
    fold(reg, "R01", "IN_PROGRESS", reviews)
    assert (reg.stat().st_mode & 0o777) == 0o640
    assert [p.name for p in reg.parent.iterdir() if p.name.startswith("REGISTER.md.") and not p.name.endswith(".lock")] == []     # no tmp left behind


# ───────────────────────────── tallies: computed, never typed ─────────────────────────────

def test_a_consistent_header_has_no_drift_and_check_exits_0(reg):
    assert nf.header_drift(reg.read_text()) == []
    assert nf.main(["--register", str(reg), "tally", "--check"]) == 0


EDITS = [
    ("state OPEN count", "| OPEN | 4 |", "| OPEN | 5 |"),
    ("state CLOSED count", "| CLOSED | 1 |", "| CLOSED | 2 |"),
    ("state MEASURED label count", "| MEASURED in P6 | 1 |", "| MEASURED in P6 | 0 |"),
    ("state PARTIAL count", "| PARTIAL | 1 |", "| PARTIAL | 3 |"),
    ("state CLOSED_ON_BRANCH count", "| CLOSED_ON_BRANCH | 1 |", "| CLOSED_ON_BRANCH | 0 |"),
    ("state DONE count", "| DONE | 1 |", "| DONE | 7 |"),
    ("table total", "| **total** | **9** |", "| **total** | **10** |"),
    ("Total rows line", "**Total rows: 9**", "**Total rows: 8**"),
    ("severity BLOCKS_FREEZE", "| BLOCKS_FREEZE | 2 |", "| BLOCKS_FREEZE | 3 |"),
    ("severity BLOCKS_LAYER", "| BLOCKS_LAYER | 2 |", "| BLOCKS_LAYER | 1 |"),
    ("severity DEGRADES", "| DEGRADES | 3 |", "| DEGRADES | 4 |"),
    ("severity COSMETIC", "| COSMETIC | 2 |", "| COSMETIC | 9 |"),
    ("open line total", "Open rows only (4)", "Open rows only (5)"),
    ("open line all-rows", "All 9 rows, every state", "All 10 rows, every state"),
    ("open line BLOCKS_FREEZE id list", "BLOCKS_FREEZE 1 (R02)", "BLOCKS_FREEZE 1 (R02, R07)"),
    ("open line BLOCKS_FREEZE count", "BLOCKS_FREEZE 1 (R02)", "BLOCKS_FREEZE 2 (R02)"),
    ("open line BLOCKS_LAYER", "BLOCKS_LAYER 1 ·", "BLOCKS_LAYER 4 ·"),
    ("open line DEGRADES", "DEGRADES 1 ·", "DEGRADES 5 ·"),
    ("open line COSMETIC", "COSMETIC 1.", "COSMETIC 0."),
]


@pytest.mark.parametrize("what,old,new", EDITS, ids=[e[0] for e in EDITS])
def test_a_hand_edited_tally_is_drift_and_a_recompute_restores_it(tmp_path, what, old, new):
    good = make_register()
    assert old in good, f"fixture does not contain {old!r}"
    p = tmp_path / "R.md"
    p.write_text(good.replace(old, new, 1))
    assert nf.header_drift(p.read_text()), f"{what}: not detected"
    assert nf.main(["--register", str(p), "tally", "--check"]) == 1
    assert nf.drift(dict(register=p, gaps=tmp_path / "g", certs=tmp_path / "c", withholding=tmp_path / "w"))[0]["code"] == "tally_drift"
    nf.main(["--register", str(p), "tally", "--write"])
    assert p.read_text() == good                                     # byte-identical to the independently built header
    assert nf.header_drift(p.read_text()) == []


def test_a_state_class_with_rows_but_no_header_row_is_drift(tmp_path):
    p = tmp_path / "R.md"
    p.write_text(make_register().replace("| CLOSED_ON_BRANCH | 1 |\n", ""))
    assert ("state CLOSED_ON_BRANCH", "no header row", 1) in nf.header_drift(p.read_text())
    nf.tally(p, write=True)
    assert nf.header_drift(p.read_text()) == [] and "| CLOSED_ON_BRANCH | 1 |" in p.read_text()


def test_tally_write_is_idempotent(reg):
    nf.tally(reg, write=True)
    once = reg.read_bytes()
    r = nf.tally(reg, write=True)
    assert reg.read_bytes() == once and r["written"] is False


def test_a_new_state_class_gets_its_header_row_before_the_total(reg, reviews):
    assert "DEFERRED" not in reg.read_text().split("## 2 ·")[0]
    fold(reg, "R01", "DEFERRED", reviews)
    head = reg.read_text().split("## 2 ·")[0]
    assert "| DEFERRED | 1 |" in head
    assert head.index("| DEFERRED | 1 |") < head.index("| **total** |")
    assert nf.header_drift(reg.read_text()) == []


def test_a_class_that_empties_keeps_its_row_at_zero(reg, reviews):
    fold(reg, "R05", "OPEN", reviews, reason="regressed")           # PARTIAL -> OPEN: PARTIAL row stays, now 0
    assert "| PARTIAL | 0 |" in reg.read_text()
    assert nf.header_drift(reg.read_text()) == []


@pytest.mark.parametrize("tweak,code", [
    (lambda t: t.replace("| COSMETIC | 2 |", "| COSMETIC | 2 |").replace("R01 | change R01 | src | COSMETIC", "R01 | change R01 | src | TRIVIAL"),
     "unknown_severity"),
    (lambda t: t.replace("| OPEN | 4 |", "| FROBNICATED | 4 |"), "header_label_unknown"),
    (lambda t: t.replace("**Total rows: 9**", "no total here"), "header_missing"),
    (lambda t: t.replace("| **total** | **9** |", ""), "header_missing"),
    (lambda t: re.sub(r"All 9 rows.*\n", "", t), "header_missing"),
    (lambda t: t.replace("| R03 | change R03 | src | BLOCKS_LAYER | — | 0.5 | CLOSED — done in wave 1 |",
                         "| R03 | change R03 | src | BLOCKS_LAYER | — | 0.5 | SOMETHING ELSE |"), "unclassifiable_state"),
])
def test_tally_refuses_to_invent_a_header(tmp_path, tweak, code):
    p = tmp_path / "R.md"
    p.write_text(make_register(tweak=tweak))
    before = p.read_bytes()
    assert refused(nf.tally, p, write=True) == code
    assert p.read_bytes() == before


def test_the_real_register_header_is_consistent_and_a_recompute_is_a_noop(tmp_path):
    src = REAL["register"]
    if not src.is_file():
        pytest.skip("register not in this checkout")
    p = tmp_path / "REAL_COPY.md"
    p.write_bytes(src.read_bytes())
    assert nf.header_drift(p.read_text()) == []
    r = nf.tally(p, write=True)
    assert r["written"] is False and p.read_bytes() == src.read_bytes()
    reg = nf.parse_register(p.read_text())
    assert not reg["malformed"] and not reg["duplicates"] and len(reg["rows"]) == r["counts"]["total"] > 200


def test_folding_an_open_blocks_freeze_row_to_deferred_on_a_real_register_copy_changes_one_row_and_the_header(tmp_path, reviews):
    """Folds the FIRST currently-OPEN BLOCKS_FREEZE row of the real register on a COPY (it was R244 until SS N-119(4) deferred R244 for
    real; the test must not depend on which row is open: header counts are compared with the BEFORE counts, not literals)."""
    src = REAL["register"]
    if not src.is_file():
        pytest.skip("register not in this checkout")
    p = tmp_path / "REAL_COPY.md"
    p.write_bytes(src.read_bytes())
    parsed = nf.parse_register(p.read_text())
    before = parsed["rows"]
    open_bf = [k for k, r in before.items() if r.state_class == "OPEN" and r.severity == "BLOCKS_FREEZE"]
    open_any = [k for k, r in before.items() if r.state_class == "OPEN"]       # fallback: the property (one row + header) holds for any OPEN row
    if not (open_bf or open_any):
        pytest.skip("no OPEN row left in the real register")
    row = (open_bf or open_any)[0]
    counts_before = nf.computed_counts(parsed)["by_state"]
    nf.set_state(p, row, "DEFERRED", "fix merged; withholding kept until B.U", evidence="PR #2999")
    t = p.read_text()
    after = nf.parse_register(t)["rows"]
    assert set(before) == set(after)
    assert [k for k in before if before[k].cells != after[k].cells] == [row]
    counts_after = nf.computed_counts(nf.parse_register(t))["by_state"]
    assert counts_after.get("DEFERRED", 0) == counts_before.get("DEFERRED", 0) + 1
    assert counts_after["OPEN"] == counts_before["OPEN"] - 1
    assert f"| DEFERRED | {counts_after['DEFERRED']} |" in t and f"| OPEN | {counts_after['OPEN']} |" in t
    assert nf.header_drift(t) == []
    assert after[row].state_class == "DEFERRED" and after[row].severity == before[row].severity


def test_parity_with_the_suvarna_tracker_parse_when_it_is_available():
    """The tracker is not importable from `main`; where the control checkout exists, its parse must agree with ours."""
    td = _find_tracker()
    if td is None or not REAL["register"].is_file():
        pytest.skip("suvarna_tracker is on no worktree of this repository and $SUVARNA_TRACKER_DIR is unset: parity cannot be checked")
    saved = list(sys.path)
    try:
        sys.path.insert(0, str(td))
        spec = importlib.util.spec_from_file_location("suvarna_tracker.detectors", td / "suvarna_tracker" / "detectors.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("suvarna_tracker.detectors", mod)
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"tracker not importable here: {e}")
    finally:
        sys.path[:] = saved
    text = REAL["register"].read_text()
    theirs = mod.parse_register(text)
    mine = nf.parse_register(text)
    assert set(theirs["rows"]) == set(mine["rows"])
    assert all(theirs["rows"][k]["state_class"] == mine["rows"][k].state_class and theirs["rows"][k]["severity"] == mine["rows"][k].severity
               for k in mine["rows"])
    assert mod.register_counts(theirs)["by_state"] == nf.computed_counts(mine)["by_state"]
    assert theirs["malformed"] == mine["malformed"]


# ───────────────────────────── fingerprints ─────────────────────────────

def _fp(text):
    return nf.row_fingerprint(text)[0]


def test_the_row_fingerprint_changes_when_any_cell_of_any_row_changes():
    good = make_register()
    base = _fp(good)
    lines = good.split("\n")
    n = 0
    for i, line in enumerate(lines):
        m = re.match(r"^\| (R\d+) \|", line)
        if not m:
            continue
        cells = line.split("|")
        for j in range(1, len(cells) - 1):
            mutated = list(cells)
            mutated[j] = mutated[j].rstrip() + "x "
            alt = list(lines)
            alt[i] = "|".join(mutated)
            # a severity-column edit would also be a header drift, which is irrelevant to the row fingerprint
            assert _fp("\n".join(alt)) != base, f"{m.group(1)} cell {j} not covered by the fingerprint"
            n += 1
    assert n >= 9 * 7


def test_the_row_fingerprint_ignores_the_header_and_prose_but_the_file_hash_does_not(tmp_path):
    good = make_register()
    drifted = good.replace("| OPEN | 4 |", "| OPEN | 5 |").replace("trailing prose", "other prose")
    assert _fp(good) == _fp(drifted)
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_text(good)
    b.write_text(drifted)
    assert nf._file_fp(a)["sha256"] != nf._file_fp(b)["sha256"]


def test_a_row_added_or_removed_changes_the_fingerprint():
    assert _fp(make_register()) != _fp(make_register(DEFAULT_ROWS[:-1]))
    assert _fp(make_register()) != _fp(make_register(DEFAULT_ROWS + [("R30", "COSMETIC", "OPEN", 1)]))


def test_the_fingerprint_is_deterministic(reg):
    assert nf.row_fingerprint(reg.read_text()) == nf.row_fingerprint(reg.read_text())


def _paths(tmp_path, reg):
    g = tmp_path / "asset_gaps.jsonl"
    c = tmp_path / "asset_certs.jsonl"
    w = tmp_path / "NIKASHA_WITHHOLDING.json"
    g.write_text(json.dumps({"asset": "_schema", "_doc": "t"}) + "\n")
    c.write_text(json.dumps({"asset": "_schema", "_doc": "t"}) + "\n")
    w.write_text(json.dumps({"version": 1, "entries": {}}))
    return dict(register=reg, gaps=g, certs=c, withholding=w)


def test_verify_names_the_rows_that_moved_and_how_a_ledger_changed(tmp_path, reg, reviews):
    paths = _paths(tmp_path, reg)
    rec = nf.fingerprints(paths)
    assert nf.verify_fingerprints(rec, paths) == []
    fold(reg, "R01", "IN_PROGRESS", reviews)
    d = dict(nf.verify_fingerprints(rec, paths))
    assert d["register"] == "rows changed: R01"
    with paths["gaps"].open("a") as f:
        f.write(json.dumps({"asset": "x", "gap_id": "x-y", "state": "OPEN"}) + "\n")
    assert dict(nf.verify_fingerprints(rec, paths))["gaps"].startswith("appended only")
    paths["certs"].write_text(json.dumps({"asset": "_schema", "_doc": "REWRITTEN!!"}) + "\n")
    assert dict(nf.verify_fingerprints(rec, paths))["certs"].startswith("REWRITTEN")
    paths["withholding"].write_text(json.dumps({"version": 1, "entries": {"a": 1}}))
    assert dict(nf.verify_fingerprints(rec, paths))["withholding"] == "changed"
    paths["withholding"].unlink()
    assert dict(nf.verify_fingerprints(rec, paths))["withholding"] == "missing now"


def test_a_rewritten_first_line_with_more_lines_is_not_mistaken_for_an_append(tmp_path, reg):
    paths = _paths(tmp_path, reg)
    rec = nf.fingerprints(paths)
    paths["gaps"].write_text(json.dumps({"asset": "_schema", "_doc": "changed"}) + "\n" + json.dumps({"asset": "x"}) + "\n")
    assert dict(nf.verify_fingerprints(rec, paths))["gaps"].startswith("REWRITTEN")


def test_fingerprint_and_verify_cli(tmp_path, reg, capsys):
    paths = _paths(tmp_path, reg)
    base = ["--register", str(reg), "--gaps", str(paths["gaps"]), "--certs", str(paths["certs"]),
            "--withholding", str(paths["withholding"])]
    out = tmp_path / "fp.json"
    assert nf.main(base + ["fingerprint", "--out", str(out)]) == 0
    assert nf.main(base + ["verify", str(out)]) == 0
    reg.write_text(reg.read_text().replace("change R01", "change R01 edited"))
    assert nf.main(base + ["verify", str(out)]) == 1
    capsys.readouterr()
    (tmp_path / "junk.json").write_text("{nope")
    assert nf.main(base + ["verify", str(tmp_path / "junk.json")]) == 2


# ───────────────────────────── withholding list ─────────────────────────────

def _wh(tmp_path, data, raw=None):
    p = tmp_path / "wh.json"
    p.write_text(raw if raw is not None else json.dumps(data))
    return p


GOOD_ENTRY = dict(asset="bo_upaya", criterion="Idem.pattern", register_row="R244", reason="unearned PASS",
                  condition="B.U rebuild passes", decided_by="SS")


def test_the_committed_withholding_list_is_valid_and_matches_the_trackers_membership_test():
    p = REAL["withholding"]
    assert p.is_file(), "NIKASHA_WITHHOLDING.json is part of E5.2"
    wh = nf.load_withholding(p)
    assert list(wh["entries"]) == ["bo_upaya-Idem.pattern"]
    e = wh["entries"]["bo_upaya-Idem.pattern"]
    assert (e["asset"], e["criterion"], e["register_row"]) == ("bo_upaya", "Idem.pattern", "R244")
    # the tracker's own test (detectors.py Detectors._withholding_has_entry), reproduced verbatim:
    data = json.loads(p.read_text())
    entry = "bo_upaya-Idem.pattern"
    assert isinstance(data, dict) and (entry in data or entry in (data.get("entries") or data.get("withheld") or []))


@pytest.mark.parametrize("data,raw,code", [
    (None, '{"version": 1, "entries": {"a-b": {}, "a-b": {}}}', "withholding_malformed"),                 # duplicate keys
    (None, "{not json", "withholding_malformed"),
    ({"version": 2, "entries": {}}, None, "withholding_malformed"),
    ({"version": 1, "entries": [GOOD_ENTRY]}, None, "withholding_malformed"),                             # list form
    ({"version": 1, "entries": {"bo_upaya-Idem.pattern": "x"}}, None, "withholding_malformed"),
    ({"version": 1, "entries": {"wrong-key": GOOD_ENTRY}}, None, "withholding_malformed"),                # key != asset-criterion
    ({"version": 1, "entries": {"bo_upaya-Idem.patern": dict(GOOD_ENTRY, criterion="Idem.patern")}}, None,
     "withholding_unknown_criterion"),                                                                    # a typo withholds nothing
    ({"version": 1, "entries": {"bo_upaya-Idem.pattern": dict(GOOD_ENTRY, reason=" ")}}, None, "withholding_malformed"),
    ({"version": 1, "entries": {"bo_upaya-Idem.pattern": dict(GOOD_ENTRY, condition="")}}, None, "withholding_malformed"),
    ({"version": 1, "entries": {"bo_upaya-Idem.pattern": dict(GOOD_ENTRY, decided_by=None)}}, None, "withholding_malformed"),
    ({"version": 1, "entries": {"bo_upaya-Idem.pattern": dict(GOOD_ENTRY, register_row="244")}}, None, "withholding_malformed"),
    ({"version": 1, "entries": {"-Idem.pattern": dict(GOOD_ENTRY, asset="")}}, None, "withholding_malformed"),
])
def test_a_malformed_withholding_list_is_refused(tmp_path, data, raw, code):
    assert refused(nf.load_withholding, _wh(tmp_path, data, raw)) == code


def test_an_empty_list_is_valid_and_a_missing_list_blocks_an_emit(tmp_path):
    assert nf.load_withholding(_wh(tmp_path, {"version": 1, "entries": {}}))["entries"] == {}
    assert refused(nf.load_withholding, tmp_path / "absent.json") == "withholding_missing"
    assert nf.load_withholding(tmp_path / "absent.json", must_exist=False)["entries"] == {}


# ───────────────────────────── emit-gaps with the withholding list ─────────────────────────────

SCHEMA = {"asset": "_schema", "_doc": "test ledger"}
STAMP = dict(registry_revision=ac.REGISTRY_REVISION, registry_fingerprint=ac.registry_fingerprint(), tool_commit="a" * 40)


def gap_row(asset, crit, state, **kw):
    r = dict(asset=asset, gap_id=f"{asset}-{crit}", kind="gap", criterion=crit, what="measured: m / required: r",
             change="", detector="d", owner="asset_census", gate="this asset's certification", state=state,
             ts="2026-10-01T00:00:00+05:30")
    r.update(kw)
    return r


def write_ledger(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in [SCHEMA, *rows]), encoding="utf-8")
    return path


def census(cells, layer="L2", generated="2026-10-02T10:00:00+05:30"):
    """cells: {asset: {criterion: verdict}}"""
    return dict(generated=generated, layer=layer, **STAMP,
                assets=[dict(asset_id=a, layer=layer, measurements={c: dict(v=v, measured=f"{v} for {a}/{c}") for c, v in m.items()})
                        for a, m in cells.items()])


def withholding(tmp_path, *keys):
    ents = {}
    for k in keys:
        asset, crit = k.split("-", 1)
        ents[k] = {kk: vv for kk, vv in dict(GOOD_ENTRY, asset=asset, criterion=crit).items() if kk != "register_row"}
    return nf.load_withholding(_wh(tmp_path, {"version": 1, "entries": ents}))


W = "bo_upaya-Idem.pattern"


@pytest.fixture
def led(tmp_path):
    return write_ledger(tmp_path / "asset_gaps.jsonl", [gap_row("bo_upaya", "Idem.pattern", "OPEN"),
                                                         gap_row("bo_other", "Idem.pattern", "OPEN")])


def emit(led, tmp_path, cells, *keys, **kw):
    return nf.emit_gaps_withheld(census(cells), led, withholding(tmp_path, *keys), **kw)


def new_rows(led, before_len):
    return [json.loads(l) for l in led.read_text().split("\n")[before_len:] if l.strip()]


def test_a_withheld_pass_is_never_credited_but_a_non_withheld_pass_closes(led, tmp_path):
    n = led.read_text().count("\n")
    r = emit(led, tmp_path, {"bo_upaya": {"Idem.pattern": "PASS"}, "bo_other": {"Idem.pattern": "PASS"}}, W)
    rows = new_rows(led, n)
    assert [(x["gap_id"], x["state"]) for x in rows] == [("bo_other-Idem.pattern", "CLOSED")]
    assert r["status"] == "appended" and r["withheld_applied"] == [dict(gap_id=W, verdict="PASS")]
    assert r["unfiltered_summary"]["closed"] == 2 and r["summary"]["closed"] == 1       # before / after withholding


def test_a_withheld_fail_is_not_opened_or_reopened_but_a_non_withheld_fail_is(tmp_path):
    led = write_ledger(tmp_path / "asset_gaps.jsonl", [gap_row("bo_upaya", "Idem.pattern", "CLOSED")])
    n = led.read_text().count("\n")
    r = emit(led, tmp_path, {"bo_upaya": {"Idem.pattern": "FAIL", "Build.registered": "FAIL"},
                             "bo_new": {"Idem.pattern": "FAIL"}}, W)
    got = sorted((x["gap_id"], x["state"]) for x in new_rows(led, n))
    assert got == [("bo_new-Idem.pattern", "OPEN"), ("bo_upaya-Build.registered", "OPEN")]      # same asset/other crit, other asset/same crit
    assert r["unfiltered_summary"]["reopened"] == 1 and r["summary"]["reopened"] == 0


def test_the_withheld_pair_matches_on_asset_and_criterion_together(led, tmp_path):
    n = led.read_text().count("\n")
    emit(led, tmp_path, {"bo_upaya": {"Build.registered": "FAIL"}, "bo_other": {"Idem.pattern": "PASS"}}, W)
    ids = sorted(x["gap_id"] for x in new_rows(led, n))
    assert ids == ["bo_other-Idem.pattern", "bo_upaya-Build.registered"]


def test_without_any_withheld_entry_the_same_census_credits_both(led, tmp_path):
    n = led.read_text().count("\n")
    emit(led, tmp_path, {"bo_upaya": {"Idem.pattern": "PASS"}, "bo_other": {"Idem.pattern": "PASS"}})
    assert sorted(x["gap_id"] for x in new_rows(led, n)) == ["bo_other-Idem.pattern", "bo_upaya-Idem.pattern"]


def test_a_withheld_entry_the_census_did_not_measure_is_reported(led, tmp_path):
    r = emit(led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}}, W)
    assert r["withheld_applied"] == [] and r["withheld_not_measured"] == [W]


def test_old_bytes_are_never_touched_and_only_whole_lines_are_appended(led, tmp_path):
    old = led.read_bytes()
    emit(led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}, "bo_x": {"Build.registered": "FAIL"}}, W)
    new = led.read_bytes()
    assert new.startswith(old) and new.endswith(b"\n") and len(new) > len(old)
    for ln in new[len(old):].decode().split("\n")[:-1]:
        assert isinstance(json.loads(ln), dict)


def test_emit_is_idempotent(led, tmp_path):
    cells = {"bo_upaya": {"Idem.pattern": "PASS"}, "bo_other": {"Idem.pattern": "PASS"}, "bo_x": {"Build.registered": "FAIL"}}
    r1 = emit(led, tmp_path, cells, W)
    once = led.read_bytes()
    r2 = emit(led, tmp_path, cells, W)
    r3 = emit(led, tmp_path, cells, W)
    assert r1["status"] == "appended" and r2["status"] == r3["status"] == "unchanged"
    assert led.read_bytes() == once and r2["rows"] == [] and r2["sha256_before"] == r2["sha256_after"]


def test_dry_run_reports_the_rows_but_writes_nothing(led, tmp_path):
    before = led.read_bytes()
    r = emit(led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}}, W, dry_run=True)
    assert r["status"] == "dry_run" and [x["gap_id"] for x in r["rows"]] == ["bo_other-Idem.pattern"]
    assert led.read_bytes() == before
    assert r["sha256_before"] == r["sha256_after"] and r["lines_before"] == r["lines_after"]


def test_the_emit_leaves_no_staging_files_behind(led, tmp_path):
    wh = withholding(tmp_path, W)
    names = sorted(p.name for p in tmp_path.iterdir())
    nf.emit_gaps_withheld(census({"bo_other": {"Idem.pattern": "PASS"}}), led, wh)
    assert sorted(p.name for p in tmp_path.iterdir()) == names
    assert not [p for p in pathlib.Path(__import__("tempfile").gettempdir()).glob("fold_stage_*")]


def test_the_live_ctrl_is_restored_after_staging_even_when_it_fails(led, tmp_path):
    keep = ac.CTRL
    with pytest.raises(nf.FoldRefused):
        emit(led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}}, W, assets=["nobody"])
    assert ac.CTRL == keep


def test_a_scope_naming_an_unmeasured_asset_is_refused_and_writes_nothing(led, tmp_path):
    before = led.read_bytes()
    assert refused(emit, led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}}, W, assets=["ghost"]) == "scope_error"
    assert led.read_bytes() == before


def test_a_scoped_emit_touches_only_its_assets(led, tmp_path):
    n = led.read_text().count("\n")
    emit(led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}, "bo_x": {"Build.registered": "FAIL"}}, W, assets=["bo_x"])
    assert [x["gap_id"] for x in new_rows(led, n)] == ["bo_x-Build.registered"]


def test_an_unterminated_ledger_is_refused(tmp_path):
    led = tmp_path / "asset_gaps.jsonl"
    led.write_text(json.dumps(SCHEMA))                     # no trailing newline
    before = led.read_bytes()
    assert refused(emit, led, tmp_path, {"bo_x": {"Build.registered": "FAIL"}}) == "ledger_no_trailing_newline"
    assert led.read_bytes() == before


def test_a_missing_or_symlinked_ledger_is_refused(tmp_path, led):
    assert refused(emit, tmp_path / "nope.jsonl", tmp_path, {"bo_x": {"Build.registered": "FAIL"}}) == "ledger_missing"
    link = tmp_path / "link.jsonl"
    link.symlink_to(led)
    assert refused(emit, link, tmp_path, {"bo_x": {"Build.registered": "FAIL"}}) == "ledger_missing"


def test_a_staged_row_for_a_withheld_id_is_refused_even_if_the_writer_emits_it(led, tmp_path, monkeypatch):
    """Defence in depth: whatever the writer does (a retirement closure, a future code path), nothing for a withheld id lands."""
    def evil(c, assets=None):
        with (ac.CTRL / "asset_gaps.jsonl").open("a") as f:
            f.write(json.dumps(gap_row("bo_upaya", "Idem.pattern", "CLOSED")) + "\n")
        return dict(added=0, skipped=0, closed=1, reopened=0, retired_opportunity_rows_left=0)
    monkeypatch.setattr(ac, "emit_gaps_summary", evil)
    before = led.read_bytes()
    assert refused(emit, led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}}, W) == "withheld_row_emitted"
    assert led.read_bytes() == before


def test_a_writer_that_rewrites_old_bytes_is_refused(led, tmp_path, monkeypatch):
    def evil(c, assets=None):
        p = ac.CTRL / "asset_gaps.jsonl"
        p.write_text(p.read_text().replace('"OPEN"', '"CLOSED"', 1))
        return dict(added=0, skipped=0, closed=0, reopened=0, retired_opportunity_rows_left=0)
    monkeypatch.setattr(ac, "emit_gaps_summary", evil)
    before = led.read_bytes()
    assert refused(emit, led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}}) == "ledger_not_append_only"
    assert led.read_bytes() == before


def test_a_writer_that_emits_a_non_object_line_is_refused(led, tmp_path, monkeypatch):
    def evil(c, assets=None):
        with (ac.CTRL / "asset_gaps.jsonl").open("a") as f:
            f.write("[1, 2]\n")
        return dict(added=1, skipped=0, closed=0, reopened=0, retired_opportunity_rows_left=0)
    monkeypatch.setattr(ac, "emit_gaps_summary", evil)
    before = led.read_bytes()
    assert refused(emit, led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}}) == "staged_row_invalid"
    assert led.read_bytes() == before


def test_a_writer_that_emits_a_non_json_line_is_refused(led, tmp_path, monkeypatch):
    def evil(c, assets=None):
        with (ac.CTRL / "asset_gaps.jsonl").open("a") as f:
            f.write("this is not json\n")
        return dict(added=1, skipped=0, closed=0, reopened=0, retired_opportunity_rows_left=0)
    monkeypatch.setattr(ac, "emit_gaps_summary", evil)
    before = led.read_bytes()
    assert refused(emit, led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}}) == "staged_row_invalid"
    assert led.read_bytes() == before


def test_a_concurrent_append_during_staging_is_detected_and_nothing_is_written(led, tmp_path, monkeypatch):
    real = ac.emit_gaps_summary
    calls = []

    def racing(c, assets=None):
        calls.append(1)
        if len(calls) == 2:                                 # the second (filtered) staging run: someone appends to the real ledger
            with led.open("a") as f:
                f.write(json.dumps(gap_row("bo_race", "Idem.pattern", "OPEN")) + "\n")
        return real(c, assets)
    monkeypatch.setattr(ac, "emit_gaps_summary", racing)
    assert refused(emit, led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}}, W) == "ledger_changed_during_fold"
    assert '"state": "CLOSED"' not in led.read_text() and "bo_race" in led.read_text()


def test_the_emit_never_touches_the_certification_ledger(led, tmp_path):
    certs = tmp_path / "asset_certs.jsonl"
    certs.write_text(json.dumps({"asset": "_schema"}) + "\n")
    before = certs.read_bytes()
    emit(led, tmp_path, {"bo_other": {"Idem.pattern": "PASS"}}, W)
    assert certs.read_bytes() == before


def test_a_held_census_lock_blocks_the_emit_with_exit_75(led, tmp_path):
    wh = _wh(tmp_path, {"version": 1, "entries": {}})
    lock = tmp_path / "census.lock"
    fd = os.open(lock, os.O_RDWR | os.O_CREAT)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        before = led.read_bytes()
        with pytest.raises(nf.LockHeld):
            nf.emit_gaps_withheld(census({"bo_x": {"Build.registered": "FAIL"}}), led, nf.load_withholding(wh), lock_file=lock)
        assert led.read_bytes() == before
        assert nf.main(["--gaps", str(led), "--lock-file", str(lock), "--register", str(tmp_path / "r.md"),
                        "set-state", "R01", "--to", "OPEN", "--reason", "x"]) == 75
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    nf.emit_gaps_withheld(census({"bo_x": {"Build.registered": "FAIL"}}), led, nf.load_withholding(wh), lock_file=lock)   # free again
    assert b"bo_x-Build.registered" in led.read_bytes()


# ───────────────────────────── git preflight: dirty / unknown ref ─────────────────────────────

def git(repo, *args):
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "HOME": str(repo)}
    return subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, env=env).stdout.decode()


@pytest.fixture
def gitrepo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "00_ARCHITECTURE/control/E4.3").mkdir(parents=True)
    ledger = write_ledger(repo / nf.GAPS_REL, [gap_row("bo_other", "Idem.pattern", "OPEN")])
    (repo / nf.CUTOVER_REL).write_text("{}")
    (repo / nf.WITHHOLDING_REL).write_text(json.dumps({"version": 1, "entries": {}}))
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo, ledger


def test_a_committed_clean_ledger_in_a_repo_is_emitted_to(gitrepo, tmp_path):
    repo, led = gitrepo
    r = nf.emit_gaps_withheld(census({"bo_other": {"Idem.pattern": "PASS"}}), led, repo / nf.WITHHOLDING_REL)
    assert r["status"] == "appended"
    assert git(repo, "status", "--porcelain").strip().endswith("asset_gaps.jsonl")        # one reviewable diff


def test_a_dirty_ledger_is_refused_until_the_previous_emit_is_committed(gitrepo, tmp_path):
    repo, led = gitrepo
    nf.emit_gaps_withheld(census({"bo_other": {"Idem.pattern": "PASS"}}), led, repo / nf.WITHHOLDING_REL)
    before = led.read_bytes()
    assert refused(nf.emit_gaps_withheld, census({"bo_x": {"Build.registered": "FAIL"}}), led, repo / nf.WITHHOLDING_REL) == "ledger_dirty"
    assert led.read_bytes() == before
    git(repo, "commit", "-q", "-am", "emit 1")
    assert nf.emit_gaps_withheld(census({"bo_x": {"Build.registered": "FAIL"}}), led, repo / nf.WITHHOLDING_REL)["status"] == "appended"
    # a dry run is not a write: allowed on a dirty ledger
    assert nf.emit_gaps_withheld(census({"bo_y": {"Build.registered": "FAIL"}}), led, repo / nf.WITHHOLDING_REL, dry_run=True)["status"] == "dry_run"


def test_allow_dirty_is_an_explicit_escape(gitrepo, tmp_path):
    repo, led = gitrepo
    nf.emit_gaps_withheld(census({"bo_other": {"Idem.pattern": "PASS"}}), led, repo / nf.WITHHOLDING_REL)
    assert nf.emit_gaps_withheld(census({"bo_x": {"Build.registered": "FAIL"}}), led, repo / nf.WITHHOLDING_REL,
                                 allow_dirty=True)["status"] == "appended"


def test_a_ledger_whose_committed_bytes_are_not_a_prefix_is_refused(gitrepo, tmp_path):
    repo, led = gitrepo
    led.write_text(led.read_text().replace("bo_other", "bo_renamed"))       # rewrote a committed line
    assert refused(nf.emit_gaps_withheld, census({"bo_x": {"Build.registered": "FAIL"}}), led, repo / nf.WITHHOLDING_REL,
                   allow_dirty=True) == "ledger_not_append_only"


def test_a_tracked_ledger_with_no_committed_version_is_refused(tmp_path):
    repo = tmp_path / "fresh"
    repo.mkdir()
    led = write_ledger(repo / "asset_gaps.jsonl", [])
    git(repo, "init", "-q")
    git(repo, "add", "-A")                                  # staged, never committed: no HEAD
    assert refused(nf.git_preflight, led) == "ledger_not_at_head"


def test_an_untracked_ledger_inside_a_repo_is_refused(gitrepo, tmp_path):
    repo, led = gitrepo
    other = write_ledger(repo / "asset_gaps.jsonl", [])
    assert refused(nf.emit_gaps_withheld, census({"bo_x": {"Build.registered": "FAIL"}}), other, repo / nf.WITHHOLDING_REL) == "ledger_untracked"


def test_the_canonical_ledger_path_is_refused_before_the_cutover_record_lands(gitrepo, tmp_path):
    repo, led = gitrepo
    (repo / nf.CUTOVER_REL).unlink()
    git(repo, "commit", "-q", "-am", "drop cutover")
    assert refused(nf.emit_gaps_withheld, census({"bo_x": {"Build.registered": "FAIL"}}), led, repo / nf.WITHHOLDING_REL) == "cutover_not_landed"


def test_a_ledger_copy_outside_any_repo_needs_no_git_state(led, tmp_path):
    assert nf.git_preflight(led) is None


# ───────────────────────────── the census the emit reads (E5.1's trust rules) ─────────────────────────────

CENSUS_DIR = "00_ARCHITECTURE/control/census"


@pytest.fixture
def trusted(tmp_path, monkeypatch):
    repo = tmp_path / "trepo"
    (repo / CENSUS_DIR).mkdir(parents=True)
    (repo / CENSUS_DIR / ".gitkeep").write_text("")
    git_init = repo
    git(git_init, "init", "-q")
    git(git_init, "add", "-A")
    git(git_init, "commit", "-q", "-m", "base")
    monkeypatch.setattr(ac, "ROOT", repo)
    return repo


def write_census_file(repo, obj, name="c1.json", track=True):
    p = repo / CENSUS_DIR / name
    p.write_text(json.dumps(obj))
    if track:
        git(repo, "add", "--", str(p))
    return p


def test_emit_reads_only_a_committed_registry_bound_census(trusted, tmp_path, led):
    flat = census({"bo_other": {"Idem.pattern": "PASS"}})
    untracked = write_census_file(trusted, flat, "u.json", track=False)
    assert refused(nf.load_trusted_census, untracked) == "census_untracked"
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text(json.dumps(flat))
    assert refused(nf.load_trusted_census, elsewhere) == "census_untrusted"
    stale = write_census_file(trusted, dict(flat, registry_revision=ac.REGISTRY_REVISION - 1), "s.json")
    assert refused(nf.load_trusted_census, stale) == "census_registry_mismatch"
    unbound = write_census_file(trusted, {k: v for k, v in flat.items() if k != "tool_commit"}, "n.json")
    assert refused(nf.load_trusted_census, unbound) == "census_unbound"
    ok = write_census_file(trusted, flat, "ok.json")
    assert nf.load_trusted_census(ok)["layer"] == "L2"


def test_a_multi_layer_census_needs_its_layer(trusted):
    obj = {"L2": census({"bo_x": {"Idem.pattern": "PASS"}}), "L3": census({"ka_y": {"Idem.pattern": "PASS"}}, layer="L3"),
           "rollup": {"cells": []}}
    p = write_census_file(trusted, obj, "m.json")
    assert refused(nf.load_trusted_census, p) == "layer_required"
    assert nf.load_trusted_census(p, "L3")["assets"][0]["asset_id"] == "ka_y"
    assert refused(nf.load_trusted_census, p, "L9") == "census_mismatch"


def latest_states(led):
    out = {}
    for ln in led.read_text().split("\n"):
        if ln.strip():
            r = json.loads(ln)
            if r.get("gap_id"):
                out[r["gap_id"]] = r["state"]
    return out


def test_emit_gaps_cli_end_to_end(trusted, tmp_path, led, capsys):
    wh = _wh(tmp_path, {"version": 1, "entries": {W: {k: v for k, v in dict(GOOD_ENTRY).items() if k != "register_row"}}})
    p = write_census_file(trusted, census({"bo_upaya": {"Idem.pattern": "PASS"}, "bo_other": {"Idem.pattern": "PASS"}}))
    argv = ["--gaps", str(led), "--withholding", str(wh), "emit-gaps", "--census", str(p)]
    capsys.readouterr()
    assert nf.main(argv + ["--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "dry_run" and latest_states(led)["bo_other-Idem.pattern"] == "OPEN"
    assert nf.main(argv) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "appended" and [r["gap_id"] for r in out["rows"]] == ["bo_other-Idem.pattern"]
    assert latest_states(led) == {"bo_upaya-Idem.pattern": "OPEN", "bo_other-Idem.pattern": "CLOSED"}      # the withheld one stays OPEN
    assert nf.main(argv) == 0 and json.loads(capsys.readouterr().out)["status"] == "unchanged"
    assert nf.main(["--gaps", str(led), "--withholding", str(tmp_path / "none.json"), "emit-gaps", "--census", str(p)]) == 2
    assert nf.main(["--gaps", str(led), "--withholding", str(wh), "emit-gaps", "--census", str(tmp_path / "x.json")]) == 2


def test_default_paths_resolve_under_the_given_repo(tmp_path):
    d = nf.default_paths(tmp_path)
    assert d["gaps"] == tmp_path / nf.GAPS_REL and d["withholding"] == tmp_path / nf.WITHHOLDING_REL
    assert nf.default_paths()["gaps"] == REAL["gaps"]


# ───────────────────────────── metrics ─────────────────────────────

def test_open_gap_metrics_follow_the_ledgers_own_semantics(tmp_path):
    rows = [gap_row("a", "X", "OPEN"), gap_row("a", "X", "CLOSED"),                       # closed after open
            gap_row("b", "X", "OPEN"),
            gap_row("c", "X", "IN_PROGRESS"), gap_row("h", "X", "IN_PROGRESS"),           # live for emit_gaps, not for the tracker
            gap_row("d", "X", "OPEN", superseded_by="e-X"), gap_row("d", "X", "OPEN"),    # ever superseded: dead identity
            gap_row("f", "X", "OPEN", kind="opportunity"),                                # an opportunity is not a gap
            gap_row("g", "X", "WITHDRAWN")]
    m = nf.ledger_metrics(write_ledger(tmp_path / "g.jsonl", rows))
    assert m["open_gaps"] == 3                      # b, c, h
    assert m["open_gaps_tracker_view"] == 2         # b, d (the tracker reads the latest row only; no IN_PROGRESS)
    assert m["gap_ids"] == 7


def test_certification_record_count_excludes_event_lines(tmp_path):
    g = write_ledger(tmp_path / "g.jsonl", [])
    c = tmp_path / "c.jsonl"
    c.write_text(json.dumps({"asset": "_schema", "_doc": "t"}) + "\n")
    nc.append_records(c, [{"asset": "_ledger", "type": "watermark"}])
    assert len(nc.read_records(c)) >= 1
    assert nf.ledger_metrics(g, c)["certification_records"] == 0           # an event is not a certificate


def test_certification_record_count_comes_from_the_chained_reader(tmp_path):
    g = write_ledger(tmp_path / "g.jsonl", [])
    c = tmp_path / "c.jsonl"
    c.write_text(json.dumps({"asset": "_schema", "_doc": "t"}) + "\n")
    assert nf.ledger_metrics(g, c)["certification_records"] == 0
    c.write_text("garbage\n")
    m = nf.ledger_metrics(g, c)
    assert m["certification_records"] is None and "certification_records_error" in m


# ───────────────────────────── drift ─────────────────────────────

@pytest.fixture
def world(tmp_path):
    """A consistent register + gaps ledger + certs ledger + withholding list, all tmp copies."""
    reg = tmp_path / "R.md"
    reg.write_text(make_register(DEFAULT_ROWS[:-1] + [("R244", "BLOCKS_FREEZE", "OPEN — unearned", 1)]))
    gaps = write_ledger(tmp_path / "asset_gaps.jsonl", [gap_row("bo_other", "Idem.pattern", "OPEN")])
    certs = tmp_path / "asset_certs.jsonl"
    certs.write_text(json.dumps({"asset": "_schema", "_doc": "t"}) + "\n")
    wh = _wh(tmp_path, {"version": 1, "entries": {W: dict(GOOD_ENTRY)}})
    return dict(register=reg, gaps=gaps, certs=certs, withholding=wh)


def codes(findings, level=None):
    return sorted(f["code"] for f in findings if level is None or f["level"] == level)


def test_a_consistent_world_has_no_drift(world):
    f = nf.drift(world)
    assert [(x["code"], x["level"]) for x in f] == [("append_only_not_checked", "NOTE")]      # a tmp copy has no baseline
    assert "NOT CHECKED" in f[0]["detail"]
    assert nf.main(["--register", str(world["register"]), "--gaps", str(world["gaps"]), "--certs", str(world["certs"]),
                    "--withholding", str(world["withholding"]), "drift"]) == 0


def test_register_drift_findings(world):
    reg = world["register"]
    good = reg.read_text()
    reg.write_text(good.replace("| OPEN | 4 |", "| OPEN | 9 |"))
    assert "tally_drift" in codes(nf.drift(world), "ERROR")
    reg.write_text(good.replace("| R01 | change R01 | src | COSMETIC | — | 0.5 | OPEN", "| R01 | change R01 | src | COSMETIC | — | 0.5 | x | OPEN"))
    assert "register_malformed_rows" in codes(nf.drift(world), "ERROR")
    reg.write_text(good + "\n| R01 | dup | s | COSMETIC | — | 1 | OPEN |\n")
    assert "register_duplicate_rows" in codes(nf.drift(world), "ERROR")
    reg.write_text(good.replace("PARTIAL — half", "HALF-DONE"))
    assert "register_unclassifiable_state" in codes(nf.drift(world), "ERROR")
    reg.unlink()
    assert "register_missing" in codes(nf.drift(world), "ERROR")


def test_ledger_drift_findings(world):
    gaps = world["gaps"]
    good = gaps.read_text()
    gaps.write_text(good + "not json\n")
    assert "gaps_ledger_bad_line" in codes(nf.drift(world), "ERROR")
    gaps.write_text(good + "[1]\n")
    assert "gaps_ledger_bad_line" in codes(nf.drift(world), "ERROR")
    gaps.write_text(good.split("\n", 1)[1])
    assert "gaps_ledger_no_schema_row" in codes(nf.drift(world), "ERROR")
    gaps.write_text(good.rstrip("\n"))
    assert "gaps_ledger_no_trailing_newline" in codes(nf.drift(world), "ERROR")
    gaps.write_text(good + json.dumps(gap_row("z", "X", "WRONG")) + "\n")
    assert "gaps_ledger_unknown_state" in codes(nf.drift(world), "ERROR")
    gaps.unlink()
    assert "gaps_ledger_missing" in codes(nf.drift(world), "ERROR")


def test_certs_ledger_drift(world):
    world["certs"].write_text("garbage\n")
    assert "certs_ledger_unreadable" in codes(nf.drift(world), "ERROR")
    world["certs"].unlink()
    f = nf.drift(world)
    assert "certs_ledger_missing" in codes(f, "NOTE") and not codes(f, "ERROR")


def test_withholding_vs_register_drift(world):
    reg = world["register"]
    good = reg.read_text()
    # a withholding whose register row is gone
    reg.write_text(make_register(DEFAULT_ROWS))
    assert "withholding_row_missing" in codes(nf.drift(world), "ERROR")
    # a withholding that outlives its row: R244 closed / done / withdrawn while the withholding is still in force
    for st in ("CLOSED — fixed", "DONE", "WITHDRAWN — x"):
        reg.write_text(make_register(DEFAULT_ROWS[:-1] + [("R244", "BLOCKS_FREEZE", st, 1)]))
        assert "withholding_outlives_row" in codes(nf.drift(world), "ERROR"), st
    # DEFERRED / OPEN are the states that go with a withholding
    for st in ("DEFERRED — B.U", "OPEN", "PARTIAL"):
        reg.write_text(make_register(DEFAULT_ROWS[:-1] + [("R244", "BLOCKS_FREEZE", st, 1)]))
        assert "withholding_outlives_row" not in codes(nf.drift(world)), st
    reg.write_text(good)


def test_a_withheld_gap_the_ledger_already_closed_is_reported_not_corrected(world):
    gaps = world["gaps"]
    with gaps.open("a") as f:
        f.write(json.dumps(gap_row("bo_upaya", "Idem.pattern", "OPEN")) + "\n")
        f.write(json.dumps(gap_row("bo_upaya", "Idem.pattern", "CLOSED")) + "\n")
    before = gaps.read_bytes()
    f = nf.drift(world)
    assert "withheld_gap_closed_in_ledger" in codes(f, "NOTE") and not codes(f, "ERROR")
    assert gaps.read_bytes() == before


def test_a_malformed_withholding_list_is_a_drift_error(world):
    world["withholding"].write_text("{nope")
    assert "withholding_malformed" in codes(nf.drift(world), "ERROR")
    world["withholding"].unlink()
    assert "withholding_missing" in codes(nf.drift(world), "ERROR")


def test_census_vs_ledger_drift_reports_what_an_emit_would_do(world):
    c = census({"bo_upaya": {"Idem.pattern": "PASS"}, "bo_other": {"Idem.pattern": "PASS"}})
    before = world["gaps"].read_bytes()
    f = nf.drift(world, c)
    assert {"census_pending_emit", "withheld_cell_measures_pass"} <= set(codes(f, "NOTE"))
    assert world["gaps"].read_bytes() == before                     # drift is read-only
    c2 = census({"bo_other": {"Idem.pattern": "FAIL"}})              # already OPEN: nothing would change
    assert "census_pending_emit" not in codes(nf.drift(world, c2))


def test_drift_cli_exit_codes_and_metrics(world, capsys):
    base = ["--register", str(world["register"]), "--gaps", str(world["gaps"]), "--certs", str(world["certs"]),
            "--withholding", str(world["withholding"])]
    assert nf.main(base + ["drift"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["errors"] == 0 and out["metrics"]["open_gaps"] == 1
    world["register"].write_text(world["register"].read_text().replace("| OPEN | 4 |", "| OPEN | 8 |"))
    assert nf.main(base + ["drift"]) == 1


def test_withholding_check_cli(world, tmp_path):
    base = ["--withholding", str(world["withholding"])]
    assert nf.main(base + ["withholding", "--check"]) == 0
    world["withholding"].write_text("{}")
    assert nf.main(base + ["withholding", "--check"]) == 2


def test_set_state_cli_round_trip(reg, reviews, capsys):
    rv = reviews.record(row="R01")
    assert nf.main(["--repo", str(reviews.repo), "--register", str(reg), "set-state", "R01", "--to", "done",
                    "--reason", "fixed", "--evidence", "abc", "--review", str(rv)]) == 0
    assert nf.parse_register(reg.read_text())["rows"]["R01"].state_class == "DONE"
    before = reg.read_bytes()
    assert nf.main(["--repo", str(reviews.repo), "--register", str(reg), "set-state", "R01", "--to", "WITHDRAWN",
                    "--reason", "x", "--evidence", "e"]) == 2
    assert reg.read_bytes() == before
    assert nf.main(["--register", str(reg), "tally", "--check"]) == 0


# ═══════════════════════════ N-100: review records ═══════════════════════════

def close(reg, reviews, review, to="DONE", row="R01", **kw):
    kw.setdefault("reason", "x")
    kw.setdefault("evidence", "e")
    return nf.set_state(reg, row, to, review=review, repo=reviews.repo, **kw)


def stays_open(reg, reviews, review, code, to="DONE", row="R01", **kw):
    """The fold is refused with `code`, and the register is byte-identical (the row stays OPEN)."""
    before = reg.read_bytes()
    assert refused(close, reg, reviews, review, to=to, row=row, **kw) == code
    assert reg.read_bytes() == before
    assert nf.parse_register(reg.read_text())["rows"][row].state_class == "OPEN"


def test_an_accepting_record_closes_the_row_and_the_cell_names_it(reg, reviews):
    r = close(reg, reviews, reviews.record(row="R01"))
    assert r["review"]["verdict"] == "ACCEPT" and r["review"]["reviewed_sha"] == reviews.fix
    assert r["review"]["paths_declared"] == [] and r["review"]["integration_ref"] == "HEAD"
    cell = nf.parse_register(reg.read_text())["rows"]["R01"].state_cell
    assert cell.startswith("DONE — x [evidence: e] [gate: ACCEPT " + reviews.fix[:10] + " by gate-reviewer]")


def test_accept_with_corrections_plus_a_valid_re_accept_closes_it(reg, reviews):
    primary = reviews.record(row="R01", verdict="ACCEPT_WITH_CORRECTIONS")
    reviews.reaccept(row="R01")
    r = close(reg, reviews, primary)
    assert r["review"]["re_accepted"]["corrections_sha"] == reviews.later
    assert "RE_ACCEPTED " + reviews.later[:10] in nf.parse_register(reg.read_text())["rows"]["R01"].state_cell


def test_a_record_may_name_its_sha_by_a_short_hash(reg, reviews):
    assert close(reg, reviews, reviews.record(row="R01", sha=reviews.fix[:9]))["review"]["reviewed_sha"] == reviews.fix


def test_forged_or_outside_files_leave_the_row_open(reg, reviews, tmp_path):
    outside = tmp_path / "elsewhere.md"
    outside.write_text(reviews.record(row="R01", commit=False).read_text())
    stays_open(reg, reviews, outside, "review_untrusted")
    # inside the repo but not under the reviews root (tracked and clean)
    fake = reviews.repo / "src" / "REVIEW.md"
    fake.write_text(reviews.record(row="R01", commit=False).read_text())
    reviews.git("add", "--", "src/REVIEW.md")
    reviews.git("commit", "-q", "-m", "fake")
    stays_open(reg, reviews, fake, "review_untrusted")
    # a `..` trick that resolves outside the root
    ok = reviews.record(row="R01")
    stays_open(reg, reviews, reviews.root / ".." / "src" / ".." / "elsewhere_copy.md", "review_untrusted")
    sneaky = reviews.root / ".." / ".." / ".." / "src" / "REVIEW.md"
    stays_open(reg, reviews, sneaky, "review_untrusted")
    # a symlink in the root pointing out
    link = reviews.root / "link.md"
    link.symlink_to(outside)
    stays_open(reg, reviews, link, "review_untrusted")
    # and a symlink to a legitimate record inside the root is also refused (the blob is the link text)
    link2 = reviews.root / "link2.md"
    link2.symlink_to(ok)
    stays_open(reg, reviews, link2, "review_untrusted")
    stays_open(reg, reviews, reviews.root / "absent.md", "review_missing")


def test_a_repo_that_is_not_git_cannot_verify_a_review(reg, reviews, tmp_path):
    nogit = tmp_path / "nogit"
    nogit.mkdir()
    assert refused(nf.set_state, reg, "R01", "DONE", "x", evidence="e", review=reviews.record(row="R01"), repo=nogit) == "review_repo"


def test_untracked_staged_and_dirty_records_leave_the_row_open(reg, reviews):
    stays_open(reg, reviews, reviews.record(row="R01", commit=False), "review_untracked")
    staged = reviews.record(row="R01", commit=False)
    reviews.git("add", "--", str(staged.relative_to(reviews.repo)))
    stays_open(reg, reviews, staged, "review_not_at_head")
    dirty = reviews.record(row="R01")
    dirty.write_text(dirty.read_text() + "\nlocal edit\n")
    stays_open(reg, reviews, dirty, "review_dirty")
    dirty_flip = reviews.record(row="R01", verdict="REJECT")           # committed REJECT, locally flipped to ACCEPT
    dirty_flip.write_text(dirty_flip.read_text().replace("verdict: REJECT", "verdict: ACCEPT"))
    stays_open(reg, reviews, dirty_flip, "review_dirty")


def test_wrong_row_reject_and_re_accept_as_primary_leave_the_row_open(reg, reviews):
    stays_open(reg, reviews, reviews.record(row="R02"), "review_row_mismatch")
    stays_open(reg, reviews, reviews.record(row="R01", verdict="REJECT"), "review_rejected")
    stays_open(reg, reviews, reviews.reaccept(row="R01"), "review_not_primary")


def test_a_sha_that_is_unknown_or_not_merged_leaves_the_row_open(reg, reviews):
    stays_open(reg, reviews, reviews.record(row="R01", sha="deadbeef" * 5), "review_sha_unknown")
    stays_open(reg, reviews, reviews.record(row="R01", sha=reviews.side), "review_sha_not_merged")       # on another branch


def test_closed_and_done_need_origin_main_but_a_branch_close_needs_only_head(reg, reviews):
    rec = reviews.record(row="R01")
    reviews.git("update-ref", "refs/remotes/origin/main", reviews.base)         # origin/main has NOT got the fix yet
    stays_open(reg, reviews, rec, "review_sha_not_merged", to="DONE")
    stays_open(reg, reviews, rec, "review_sha_not_merged", to="CLOSED")
    assert close(reg, reviews, rec, to="CLOSED_ON_BRANCH")["to_state"] == "CLOSED_ON_BRANCH"
    reg.write_text(make_register())
    reviews.git("update-ref", "refs/remotes/origin/main", reviews.head())        # now merged
    assert close(reg, reviews, rec, to="DONE")["review"]["integration_ref"] == "origin/main"


def test_a_row_that_declares_paths_needs_the_reviewed_sha_to_touch_one(tmp_path, reviews):
    def reg_with(paths):
        p = tmp_path / f"R_{abs(hash(paths))}.md"
        p.write_text(make_register(tweak=lambda t: t.replace("change R01", f"change R01 {paths}")))
        return p
    rec = reviews.record(row="R01")
    untouched = reg_with("see `docs/never_touched.md` and `src/other/` for details")
    stays_open(untouched, reviews, rec, "review_sha_untouched_paths")
    assert close(reg_with("fix in `src/fix.py:12`"), reviews, rec)["review"]["paths_declared"] == ["src/fix.py"]
    assert close(reg_with("fix in `src/`"), reviews, rec)["review"]["paths_declared"] == ["src"]          # a directory
    assert close(reg_with("`docs/never.md` and `src/fix.py`"), reviews, rec)["to_state"] == "DONE"       # one touched is enough
    r = close(reg_with("`not_a_path` `http://x/y` `a*/b`"), reviews, rec)                                  # none declared
    assert r["review"]["paths_declared"] == []


def test_accept_with_corrections_alone_or_with_a_bad_re_accept_closes_nothing(reg, reviews):
    primary = reviews.record(row="R01", verdict="ACCEPT_WITH_CORRECTIONS")
    stays_open(reg, reviews, primary, "review_needs_reaccept")                                            # none at all
    reviews.reaccept(row="R01", corrections=reviews.base)                                                 # ancestor of reviewed_sha
    stays_open(reg, reviews, primary, "review_needs_reaccept")
    reviews.reaccept(row="R01", corrections=reviews.fix)                                                  # equal, not a descendant
    stays_open(reg, reviews, primary, "review_needs_reaccept")
    reviews.reaccept(row="R01", corrections=reviews.side)                                                 # not a descendant
    stays_open(reg, reviews, primary, "review_needs_reaccept")
    reviews.reaccept(row="R02")                                                                           # another row
    stays_open(reg, reviews, primary, "review_needs_reaccept")
    reviews.reaccept(row="R01", sha=reviews.later)                                                        # another reviewed_sha
    stays_open(reg, reviews, primary, "review_needs_reaccept")
    reviews.reaccept(row="R01", commit=False)                                                             # untracked
    stays_open(reg, reviews, primary, "review_needs_reaccept")
    dirty = reviews.reaccept(row="R01")
    dirty.write_text(dirty.read_text() + "\nedit\n")                                                      # modified
    stays_open(reg, reviews, primary, "review_needs_reaccept")
    reviews.record(row="R01", verdict="ACCEPT")                                                           # not a RE_ACCEPTED
    stays_open(reg, reviews, primary, "review_needs_reaccept")
    reviews.reaccept(row="R01", fm="---\nrow: R01\nverdict: RE_ACCEPTED\n---\n")                         # malformed (skipped)
    stays_open(reg, reviews, primary, "review_needs_reaccept")


def test_a_re_accept_whose_corrections_are_not_merged_does_not_count(reg, reviews):
    primary = reviews.record(row="R01", verdict="ACCEPT_WITH_CORRECTIONS")
    reviews.git("checkout", "-q", "-b", "wip", reviews.fix)
    wip = reviews.commit_file("src/wip.py", "w\n")                                                       # descends from fix...
    reviews.git("checkout", "-q", "main")                                                                 # ...but is not on HEAD
    reviews.reaccept(row="R01", corrections=wip)
    stays_open(reg, reviews, primary, "review_needs_reaccept")


MALFORMED = {
    "no frontmatter": "# just prose\nverdict: ACCEPT\n",
    "closing line without an opener": "# junk\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\n---\n",
    "not on line 1": "\n---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\n---\n",
    "unclosed": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\n",
    "unknown key": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\nstatus: done\n---\n",
    "duplicate key": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\nverdict: ACCEPT\nreviewer: r\n---\n",
    "missing reviewer": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\n---\n",
    "missing sha": "---\nrow: R01\nverdict: ACCEPT\nreviewer: r\n---\n",
    "missing row": "---\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\n---\n",
    "unknown verdict token": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPTED\nreviewer: r\n---\n",
    "lowercase verdict": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: accept\nreviewer: r\n---\n",
    "verdict not accept": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: NOT ACCEPT\nreviewer: r\n---\n",
    "verdict in a quote": "---\nrow: R01\nreviewed_sha: {sha}\n> verdict: ACCEPT\nreviewer: r\n---\n",
    "blank line inside": "---\nrow: R01\n\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\n---\n",
    "comment line inside": "---\nrow: R01\n# hi\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\n---\n",
    "frontmatter in a code fence": "```\n---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\n---\n```\n",
    "frontmatter in a comment": "<!--\n---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\n---\n-->\n",
    "frontmatter after a quote": "> ---\n> row: R01\n",
    "bad sha": "---\nrow: R01\nreviewed_sha: HEAD\nverdict: ACCEPT\nreviewer: r\n---\n",
    "short sha": "---\nrow: R01\nreviewed_sha: abc12\nverdict: ACCEPT\nreviewer: r\n---\n",
    "bad row": "---\nrow: 244\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\n---\n",
    "corrections_sha on an ACCEPT": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: r\ncorrections_sha: {sha}\n---\n",
    "RE_ACCEPTED without corrections_sha": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: RE_ACCEPTED\nreviewer: r\n---\n",
    "empty value": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: \n---\n",
    "bad reviewer": "---\nrow: R01\nreviewed_sha: {sha}\nverdict: ACCEPT\nreviewer: a|b\n---\n",
}


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_a_malformed_record_leaves_the_row_open(reg, reviews, name):
    f = reviews.record(row="R01", fm=MALFORMED[name].format(sha=reviews.fix), body="")
    stays_open(reg, reviews, f, "review_malformed")


BODY = {
    "verdict: NOT ACCEPT": "review_verdict_unparseable",
    "verdict: REJECTED": "review_verdict_unparseable",
    "verdict: ACCEPT-NOT": "review_verdict_unparseable",
    "Verdict rationale: it is fine": "review_verdict_unparseable",
    "verdict: ACCEPT, but later REJECT": "review_verdict_unparseable",
    "verdict:": "review_verdict_unparseable",
    "verdict: REJECT": "review_verdict_conflict",
    "**Verdict:** ACCEPT_WITH_CORRECTIONS": "review_verdict_conflict",
    "- verdict — RE_ACCEPTED": "review_verdict_conflict",
}


@pytest.mark.parametrize("line", sorted(BODY))
def test_a_body_verdict_that_does_not_parse_or_disagrees_refuses(reg, reviews, line):
    f = reviews.record(row="R01", body=f"# r\n\nok so far\n{line}\n")
    stays_open(reg, reviews, f, BODY[line])
    f2 = reviews.record(row="R01", body=f"# r\n\nverdict: ACCEPT\nlater:\n{line}\n")           # after an agreeing ACCEPT
    stays_open(reg, reviews, f2, BODY[line])


@pytest.mark.parametrize("body", [
    "> verdict: REJECT\n",
    "  > verdict: NOT ACCEPT\n",
    "```\nverdict: REJECT\n```\n",
    "~~~\nverdict: NOT ACCEPT\n~~~\n",
    "<!--\nverdict: REJECT\nverdict: nope\n-->\n",
    "<!-- verdict: REJECT -->\n",
    "<!--\nunterminated comment\nverdict: REJECT\n",
    "verdict: ACCEPT\n",
    "- Verdict — accept\n",
    "## Verdict: ACCEPT\n",
])
def test_a_verdict_inside_a_quote_fence_or_comment_does_not_count_and_agreeing_ones_pass(reg, reviews, body):
    f = reviews.record(row="R01", body="# Review\n\n" + body)
    assert close(reg, reviews, f)["to_state"] == "DONE"


def test_a_review_rejecting_after_a_quoted_accept_is_still_refused(reg, reviews):
    f = reviews.record(row="R01", verdict="REJECT", body="> verdict: ACCEPT\n")
    stays_open(reg, reviews, f, "review_rejected")


def test_the_cli_has_no_reviews_root_option_and_refuses_a_forged_review(reg, reviews, tmp_path, capsys):
    with pytest.raises(SystemExit):
        nf.main(["--register", str(reg), "set-state", "R01", "--to", "done", "--reviews-root", str(tmp_path)])
    forged = tmp_path / "forged.md"
    forged.write_text(reviews.record(row="R01", commit=False).read_text())
    before = reg.read_bytes()
    assert nf.main(["--repo", str(reviews.repo), "--register", str(reg), "set-state", "R01", "--to", "done", "--reason", "x",
                    "--evidence", "e", "--review", str(forged)]) == 2
    assert reg.read_bytes() == before


# ═══════════════════════════ review round: line separators, CRLF, header duplicates ═══════════════════════════

def test_the_line_separator_set_is_exactly_what_splitlines_splits_on():
    expected = {chr(i) for i in range(0x3000) if len(("a" + chr(i) + "b").splitlines()) > 1}
    assert set(nf.LINE_SEPS) == expected and {"\n", "\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"} == expected


@pytest.mark.parametrize("ch", sorted(nf.LINE_SEPS))
@pytest.mark.parametrize("field", ["reason", "evidence"])
def test_a_line_separator_in_reason_or_evidence_is_refused(reg, reviews, ch, field):
    before = reg.read_bytes()
    kw = {"reason": "why", "evidence": "ev"}
    kw[field] = f"a{ch}b"
    assert refused(nf.set_state, reg, "R01", "DEFERRED", repo=reviews.repo, **{"reason": kw.pop("reason"), **kw}) == "bad_text"
    assert reg.read_bytes() == before


def test_the_register_is_parsed_with_splitlines_semantics_like_the_tracker():
    text = make_register().replace("change R02", "change R02\x0bsplit here")        # a vertical tab splits the row in two
    reg = nf.parse_register(text)
    assert reg["lines"] == text.splitlines()
    assert "R02" in reg["malformed"]                                                   # the first half has too few cells
    assert nf.join_lines(reg["lines"], reg["eols"]) == text


@pytest.mark.parametrize("eol", ["\r\n", "\n", "\r"])
def test_every_line_ending_round_trips_and_is_kept(tmp_path, reviews, eol):
    good = make_register().replace("\n", eol)
    p = tmp_path / "R.md"
    p.write_bytes(good.encode())
    assert nf.header_drift(nf.read_text(p)) == []                                       # no spurious drift from a stray \r
    assert nf.tally(p, write=True)["written"] is False and p.read_bytes() == good.encode()
    fold(p, "R01", "DEFERRED", reviews)                                                 # inserts a header row too
    out = p.read_bytes().decode()
    if eol == "\r\n":
        assert out.count("\n") == out.count("\r\n")                          # no bare LF crept in
    else:
        assert ("\r" not in out) if eol == "\n" else ("\n" not in out)
    assert "| DEFERRED | 1 |" in out and nf.header_drift(out) == []
    assert re.search(r"\| DEFERRED \| 1 \|" + re.escape(eol), out)                     # the inserted row has the file's ending


def test_crlf_and_lf_registers_fingerprint_the_same_rows():
    good = make_register()
    assert nf.row_fingerprint(good)[0] == nf.row_fingerprint(good.replace("\n", "\r\n"))[0]


def test_a_register_without_a_final_newline_round_trips(tmp_path):
    p = tmp_path / "R.md"
    p.write_bytes(make_register().rstrip("\n").encode())
    assert nf.tally(p, write=True)["written"] is False and not p.read_bytes().endswith(b"\n")


def test_a_whitespace_only_change_leaves_the_row_fingerprint_unchanged():
    good = make_register()
    spaced = good.replace("| R01 | change R01 | src | COSMETIC | — | 0.5 | OPEN — wording |",
                          "| R01 |  change   R01  |\tsrc | COSMETIC |   —  | 0.5 |  OPEN —    wording   |")
    assert spaced != good and nf.row_fingerprint(spaced)[0] == nf.row_fingerprint(good)[0]


def test_duplicated_header_rows_and_a_second_total_line_are_drift_and_block_a_recompute(tmp_path):
    good = make_register()
    cases = {
        "state row": good.replace("| OPEN | 4 |\n", "| OPEN | 4 |\n| OPEN | 4 |\n"),
        "state-table total row": good.replace("| **total** | **9** |\n", "| **total** | **9** |\n| **total** | **9** |\n"),
        "severity row": good.replace("| COSMETIC | 2 | meaning of COSMETIC |\n", "| COSMETIC | 2 | meaning of COSMETIC |\n| COSMETIC | 2 | x |\n"),
        "`Total rows:` line": good.replace("prose with R99", "**Total rows: 9** again\n\nprose with R99"),
        "open-rows line": good + "\nAll 9 rows, every state. **Open rows only (4):** x.\n",
    }
    for name, text in cases.items():
        p = tmp_path / f"{abs(hash(name))}.md"
        p.write_text(text)
        assert any("duplicate header" in w for w, _, _ in nf.header_drift(text)), name
        assert nf.main(["--register", str(p), "tally", "--check"]) == 1, name
        before = p.read_bytes()
        assert refused(nf.tally, p, write=True) == "header_duplicate_rows", name
        assert p.read_bytes() == before


def test_tally_check_exits_nonzero_wherever_write_would_change_the_file(tmp_path):
    p = tmp_path / "R.md"
    p.write_text(make_register().replace("| OPEN | 4 |", "| OPEN | 04 |"))              # same number, different bytes: no value drift
    assert nf.header_drift(p.read_text()) == []
    assert nf.main(["--register", str(p), "tally", "--check"]) == 1
    before = p.read_bytes()
    assert nf.tally(p, write=True)["written"] is True and p.read_bytes() != before
    assert nf.main(["--register", str(p), "tally", "--check"]) == 0


# ═══════════════════════════ the register lock ═══════════════════════════

def _hold(path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT)
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd


def _release(fd):
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)


def test_two_concurrent_folds_cannot_lose_an_update(reg, reviews, monkeypatch):
    """Reproduce the lost update: both threads read the same base, one is delayed inside apply_tally. With the lock the
    loser is refused (LockHeld = exit 75) and the winner's row survives; without it the second write silently erased the first."""
    import threading
    import time
    real = nf.apply_tally

    def slow(t):
        time.sleep(0.4)
        return real(t)
    monkeypatch.setattr(nf, "apply_tally", slow)
    results = {}

    def go(row):
        try:
            nf.set_state(reg, row, "IN_PROGRESS", "r", repo=reviews.repo)
            results[row] = "ok"
        except nf.LockHeld:
            results[row] = "locked"
    th = [threading.Thread(target=go, args=(r,)) for r in ("R01", "R02")]
    th[0].start()
    time.sleep(0.1)
    th[1].start()
    for x in th:
        x.join()
    assert sorted(results.values()) == ["locked", "ok"], results
    rows = nf.parse_register(reg.read_text())["rows"]
    winner = next(r for r, v in results.items() if v == "ok")
    assert rows[winner].state_class == "IN_PROGRESS" and nf.header_drift(reg.read_text()) == []


def test_the_lock_is_on_by_default_next_to_the_register_and_overridable(reg, reviews, tmp_path):
    lock = nf.register_lock_path(reg)
    assert lock.name == "REGISTER.md.lock"
    fd = _hold(lock)
    try:
        before = reg.read_bytes()
        for argv in (["set-state", "R01", "--to", "IN_PROGRESS", "--reason", "x"], ["tally", "--write"],
                     ["fingerprint", "--out", str(tmp_path / "fp.json")]):
            assert nf.main(["--repo", str(reviews.repo), "--register", str(reg), *argv]) == 75, argv
        assert reg.read_bytes() == before and not (tmp_path / "fp.json").exists()
        # reads and dry runs are not blocked
        assert nf.main(["--register", str(reg), "tally", "--check"]) == 0
        assert nf.main(["--register", str(reg), "fingerprint"]) == 0
        assert nf.main(["--repo", str(reviews.repo), "--register", str(reg), "set-state", "R01", "--to", "IN_PROGRESS",
                        "--reason", "x", "--dry-run"]) == 0
        # --lock-file overrides the default
        other = tmp_path / "other.lock"
        assert nf.main(["--repo", str(reviews.repo), "--register", str(reg), "--lock-file", str(other), "set-state", "R01",
                        "--to", "IN_PROGRESS", "--reason", "x"]) == 0
        assert other.exists()
    finally:
        _release(fd)
    assert nf.main(["--register", str(reg), "tally", "--write"]) == 0                          # free again


def test_a_dry_run_or_a_read_never_creates_the_lock_file_or_its_directory(reg, reviews, tmp_path, led):
    ghost = tmp_path / "nowhere" / "deeper" / "x.lock"
    base = ["--repo", str(reviews.repo), "--register", str(reg), "--lock-file", str(ghost)]
    assert nf.main(base + ["set-state", "R01", "--to", "IN_PROGRESS", "--reason", "x", "--dry-run"]) == 0
    assert nf.main(base + ["tally", "--check"]) == 0
    assert nf.main(base + ["fingerprint"]) == 0
    assert nf.main(base + ["drift"]) in (0, 1)
    nf.emit_gaps_withheld(census({"bo_other": {"Idem.pattern": "PASS"}}), led, withholding(tmp_path), dry_run=True, lock_file=ghost)
    assert not ghost.parent.exists() and not nf.register_lock_path(reg).exists()


# ═══════════════════════════ set-state keeps the previous state ═══════════════════════════

def test_set_state_keeps_the_previous_state_cell_in_the_note_and_the_output(reg, reviews):
    r = fold(reg, "R03", "OPEN", reviews, reason="regressed")
    assert r["was"] == "CLOSED — done in wave 1"
    cell = nf.parse_register(reg.read_text())["rows"]["R03"].state_cell
    assert cell.endswith("[was: CLOSED — done in wave 1]")


def test_a_long_or_piped_previous_state_is_truncated_and_cannot_break_the_row(tmp_path, reviews):
    long_cell = "OPEN — " + "x" * 400 + r" a \| b"
    p = tmp_path / "R.md"
    p.write_text(make_register(tweak=lambda t: t.replace("OPEN — wording", long_cell)))
    fold(p, "R01", "IN_PROGRESS", reviews)
    reg = nf.parse_register(p.read_text())
    cell = reg["rows"]["R01"].state_cell
    assert not reg["malformed"] and "[was: OPEN — xxxx" in cell and cell.endswith("…]") and len(cell) < 400
    # a second fold does not nest unboundedly: it records only the (truncated) cell it replaced
    fold(p, "R01", "PARTIAL", reviews)
    assert nf.parse_register(p.read_text())["rows"]["R01"].state_cell.count("[was:") == 2


# ═══════════════════════════ drift: a rewritten ledger history ═══════════════════════════

def test_drift_detects_a_rewritten_committed_prefix_and_says_when_it_could_not_check(gitrepo, tmp_path):
    repo, led = gitrepo
    paths = dict(register=tmp_path / "R.md", gaps=led, certs=tmp_path / "c.jsonl", withholding=repo / nf.WITHHOLDING_REL)
    paths["register"].write_text(make_register())
    status, detail = nf.append_only_status(led)
    assert status == "ok" and "HEAD" in detail
    nf.emit_gaps_withheld(census({"bo_other": {"Idem.pattern": "PASS"}}), led, repo / nf.WITHHOLDING_REL)       # appended, uncommitted
    assert nf.append_only_status(led)[0] == "ok"
    assert "gaps_ledger_not_append_only" not in codes(nf.drift(paths))
    led.write_text(led.read_text().replace("bo_other", "bo_renamed", 1))                                         # rewrite history
    assert nf.append_only_status(led)[0] == "VIOLATED"
    assert "gaps_ledger_not_append_only" in codes(nf.drift(paths), "ERROR")
    assert nf.main(["--register", str(paths["register"]), "--gaps", str(led), "--certs", str(paths["certs"]),
                    "--withholding", str(paths["withholding"]), "drift"]) == 1


def test_drift_baseline_from_cutover_json_when_the_ledger_is_not_in_head(tmp_path):
    repo = tmp_path / "cut"
    (repo / "00_ARCHITECTURE/control/E4.3").mkdir(parents=True)
    led = write_ledger(repo / nf.GAPS_REL, [gap_row("a", "Idem.pattern", "OPEN")])
    body = led.read_bytes()
    (repo / nf.CUTOVER_REL).write_text(json.dumps({"files": {nf.GAPS_REL: {"new_bytes": len(body), "new_md5": hashlib.md5(body).hexdigest()}}}))
    git(repo, "init", "-q")                                                   # nothing committed or tracked: no HEAD baseline
    assert nf.append_only_status(led) == ("ok", "prefix intact against CUTOVER.json")
    led.write_bytes(body + b'{"asset": "x", "gap_id": "x-y", "state": "OPEN"}\n')
    assert nf.append_only_status(led)[0] == "ok"
    led.write_bytes(b"X" + body[1:])
    assert nf.append_only_status(led)[0] == "VIOLATED"
    led.write_bytes(body[:-5])                                                # truncated below the recorded length
    assert nf.append_only_status(led)[0] == "VIOLATED"


def test_drift_without_any_baseline_says_not_checked_never_ok(led):
    assert nf.append_only_status(led)[0] == "NOT CHECKED"


def test_drift_cli_reports_append_only_status(world, capsys):
    base = ["--register", str(world["register"]), "--gaps", str(world["gaps"]), "--certs", str(world["certs"]),
            "--withholding", str(world["withholding"])]
    capsys.readouterr()
    assert nf.main(base + ["drift"]) == 0
    assert json.loads(capsys.readouterr().out)["append_only"] == "NOT CHECKED"


# ═══════════════════════════ the canonical ledger needs the canonical, committed withholding list ═══════════════════════════

def _canon_census():
    return census({"bo_upaya": {"Idem.pattern": "PASS"}, "bo_other": {"Idem.pattern": "PASS"}})


@pytest.fixture
def canon(gitrepo):
    """The canonical ledger in a repo that carries the committed withholding list (bo_upaya-Idem.pattern) and an OPEN row for it."""
    repo, led = gitrepo
    wh = repo / nf.WITHHOLDING_REL
    wh.write_text(json.dumps({"version": 1, "entries": {W: {k: v for k, v in GOOD_ENTRY.items() if k != "register_row"}}}))
    with led.open("a") as f:
        f.write(json.dumps(gap_row("bo_upaya", "Idem.pattern", "OPEN")) + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "withholding + open row")
    return repo, led, wh


def test_the_committed_withholding_list_is_honoured_on_the_canonical_ledger(canon):
    repo, led, wh = canon
    r = nf.emit_gaps_withheld(_canon_census(), led, wh)
    assert [x["gap_id"] for x in r["rows"]] == ["bo_other-Idem.pattern"] and latest_states(led)[W] == "OPEN"


def test_a_local_edit_or_an_empty_copy_cannot_lift_the_withholding(canon, tmp_path):
    repo, led, wh = canon
    before = led.read_bytes()
    # 1. the file edited locally to hold no entries (uncommitted)
    wh.write_text(json.dumps({"version": 1, "entries": {}}))
    assert refused(nf.emit_gaps_withheld, _canon_census(), led, wh) == "withholding_dirty"
    assert refused(nf.emit_gaps_withheld, _canon_census(), led, wh, dry_run=True) == "withholding_dirty"      # a dry run too
    # 2. staged but not committed
    git(repo, "add", "--", nf.WITHHOLDING_REL)
    assert refused(nf.emit_gaps_withheld, _canon_census(), led, wh) == "withholding_dirty"
    # 3. an empty copy elsewhere, passed by path or as a dict
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"version": 1, "entries": {}}))
    assert refused(nf.emit_gaps_withheld, _canon_census(), led, empty) == "withholding_not_canonical"
    assert refused(nf.emit_gaps_withheld, _canon_census(), led, {"version": 1, "entries": {}}) == "withholding_not_canonical"
    # 4. a symlink named like the canonical file pointing at an empty copy
    wh.unlink()
    wh.symlink_to(empty)
    assert refused(nf.emit_gaps_withheld, _canon_census(), led, wh) == "withholding_not_canonical"
    assert led.read_bytes() == before


def test_an_untracked_or_uncommitted_canonical_withholding_file_is_refused(gitrepo):
    repo, led = gitrepo
    wh = repo / nf.WITHHOLDING_REL
    git(repo, "rm", "-q", "--cached", "--", nf.WITHHOLDING_REL)
    git(repo, "commit", "-q", "-m", "drop it from git")                          # the file stays on disk, untracked
    assert refused(nf.emit_gaps_withheld, _canon_census(), led, wh) == "withholding_untracked"
    git(repo, "add", "--", nf.WITHHOLDING_REL)                                  # staged only: no HEAD version
    assert refused(nf.emit_gaps_withheld, _canon_census(), led, wh) == "withholding_not_at_head"


def test_a_ledger_copy_may_use_any_withholding_path_but_the_cli_refuses_one_for_the_canonical_ledger(canon, tmp_path, led):
    repo, canon_led, wh = canon
    other = tmp_path / "copy_wh.json"
    other.write_text(json.dumps({"version": 1, "entries": {}}))
    assert nf.emit_gaps_withheld(_canon_census(), led, other)["status"] == "appended"                  # a tmp ledger copy
    before = canon_led.read_bytes()
    assert nf.main(["--gaps", str(canon_led), "--withholding", str(other), "emit-gaps", "--census", str(tmp_path / "c.json")]) == 2
    assert canon_led.read_bytes() == before


# ═══════════════════════════ exit codes ═══════════════════════════

def test_an_uncaught_exception_exits_5_never_1(reg, reviews, tmp_path, capsys):
    paths = _paths(tmp_path, reg)
    base = ["--register", str(reg), "--gaps", str(paths["gaps"]), "--certs", str(paths["certs"]),
            "--withholding", str(paths["withholding"])]
    for doc in ("[]", '{"register": {}}', '{"register": {"row_fingerprint": "x"}}', "null", '{"gaps": []}'):
        f = tmp_path / "fp.json"
        f.write_text(doc)
        capsys.readouterr()
        assert nf.main(base + ["verify", str(f)]) == 5, doc
        err = capsys.readouterr().err
        assert err.startswith("ERROR ") and err.count("\n") == 1
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"\xff\xfe not utf-8 \x80")
    gone = tmp_path / "gone.md"
    for reg_path in (bad, gone):
        for argv in (["set-state", "R01", "--to", "IN_PROGRESS", "--reason", "x"], ["tally", "--check"], ["tally", "--write"],
                     ["fingerprint"]):
            rc = nf.main(["--repo", str(reviews.repo), "--register", str(reg_path), *argv])
            assert rc in (5,) or (rc == 0 and argv[0] == "fingerprint" and reg_path == gone), (reg_path.name, argv, rc)
    # drift reports an unreadable register as a finding rather than crashing
    f = nf.drift(dict(paths, register=bad))
    assert "register_unreadable" in codes(f, "ERROR")


def test_drift_and_refusals_keep_their_own_exit_codes(reg, capsys):
    assert nf.main(["--register", str(reg), "set-state", "R77", "--to", "OPEN", "--reason", "x"]) == 2
    reg.write_text(reg.read_text().replace("| OPEN | 4 |", "| OPEN | 9 |"))
    assert nf.main(["--register", str(reg), "tally", "--check"]) == 1


# ═══════════════════════════ robustness of the writers ═══════════════════════════

def test_a_failed_register_write_leaves_no_temp_file_and_the_old_bytes(reg, reviews, monkeypatch):
    before = reg.read_bytes()

    def boom(src, dst):
        raise OSError("disk full")
    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        fold(reg, "R01", "IN_PROGRESS", reviews)
    monkeypatch.undo()
    assert reg.read_bytes() == before
    assert [p.name for p in reg.parent.iterdir() if p.name.startswith("REGISTER.md.") and not p.name.endswith(".lock")] == []


def test_a_partial_os_write_is_completed_and_a_failed_one_restores_the_ledger(led, tmp_path, monkeypatch):
    real = os.write
    ino = led.stat().st_ino
    mode = {"m": "partial"}

    def fake(fd, data):
        if os.fstat(fd).st_ino != ino:
            return real(fd, data)
        if mode["m"] == "partial":
            return real(fd, bytes(data)[:7])
        real(fd, bytes(data)[:5])                                  # tear the tail, then report no progress
        return 0
    monkeypatch.setattr(os, "write", fake)
    r = nf.emit_gaps_withheld(census({"bo_other": {"Idem.pattern": "PASS"}, "bo_x": {"Build.registered": "FAIL"}}), led,
                              withholding(tmp_path))
    assert r["status"] == "appended" and led.read_bytes().endswith(b"\n")
    assert [json.loads(l) for l in led.read_text().split("\n") if l.strip()]            # every line whole
    assert latest_states(led)["bo_other-Idem.pattern"] == "CLOSED" and "bo_x-Build.registered" in latest_states(led)
    before = led.read_bytes()
    mode["m"] = "fail"
    assert refused(nf.emit_gaps_withheld, census({"bo_y": {"Build.registered": "FAIL"}}), led, withholding(tmp_path)) == "ledger_write_failed"
    monkeypatch.undo()
    assert led.read_bytes() == before                                                      # the torn bytes were truncated away


def _find_tracker():
    import os as _os
    env = _os.environ.get("SUVARNA_TRACKER_DIR")
    cands = [pathlib.Path(env)] if env else []
    r = subprocess.run(["git", "-C", str(REPO), "worktree", "list", "--porcelain"], capture_output=True, text=True)
    for ln in r.stdout.splitlines():
        if ln.startswith("worktree "):
            cands.append(pathlib.Path(ln[9:]) / "platform/scripts/governance")
    cands.append(REPO / "platform/scripts/governance")
    return next((c for c in cands if (c / "suvarna_tracker" / "detectors.py").is_file()), None)


def test_tracker_locator_finds_the_tracker_from_git_not_a_hardcoded_path():
    td = _find_tracker()
    if td is None:
        pytest.skip("suvarna_tracker is on no worktree of this repository and $SUVARNA_TRACKER_DIR is unset: parity cannot be checked")
    assert (td / "suvarna_tracker" / "detectors.py").is_file()

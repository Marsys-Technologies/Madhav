"""I.FL1 tests-first, HELD until PR #2984 merges: ga_vastu FD-1 -- read the graha->direction map from
the L0 table `bg_vastu_directions`, not from a writer-local constant.

Source of the design: A.L1 brief `ga_vastu_ELEVATION_BRIEF_v1_0.md` section 4 FD-1 (INDEX section 4
CF-20 neighbourhood; Nirmana F-E12, still open) and CLAUDE.md section N.7 item 3 ("no wrapper-local
constant may shadow an L1/L0-computed value, even when the constant's current value happens to be
correct -- a constant can drift from its source; a reference cannot").

Today `ga_writers/ga_vastu_writer.py` carries `GRAHA_TO_DIRECTION`, a dict that DUPLICATES
`bg_vastu_directions.ruling_graha` (`brahmagyan/l0_vastu_directions.py`, 8 rows). The two agree on
all eight pairs, so no stored value changes when the writer reads the table instead (class:
stricter-only, no output change, no rebuild required). The brief's own failing-first test is:
"delete a row from a fixture `bg_vastu_directions` and the build must fail loudly (not fall back
to the dict); mutation: change a `ruling_graha` and the output moves". That is what is tested here,
against a fake connection that serves the L0 table, so it needs no database.

The fake is deliberately implementation-agnostic: it answers any SELECT that names
`bg_vastu_directions` by parsing the select list (or `*`), and reads the INSERT's column order from
the statement text, so a fix may choose its own query and column list.

Held with `xfail(strict=True)`: green now, XPASS = loud failure when the fix lands (remove the marks
then). `pytest --runxfail` shows the real failure text on today's code.

Not covered, by design: the NULL-score label and the cut points (those are I-28 and are already in
#2984), and the integrity clause.
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan.l0_vastu_directions import VASTU_DIRECTIONS  # noqa: E402

_WRITER_REL = "ga_writers/ga_vastu_writer.py"
_HOLD = dict(
    strict=True,
    reason="held until #2984 merges: fix ga_vastu FD-1 (graha->direction map read from "
           "bg_vastu_directions, not a writer-local constant; no output change)",
)

_L0_COLUMNS = ("direction", "direction_deg", "ruling_graha", "secondary_graha",
               "favorable_color", "element", "classical_citation")

_CHART = "00000000-0000-0000-0000-00000000f1f1"   # synthetic id; no chart data is read or written
_BUILD = "00000000-0000-0000-0000-00000000b1d1"


def _l0_rows(*, swap: dict[str, str] | None = None, drop_graha: str | None = None) -> list[dict]:
    """The L0 table as the database would serve it: the 8 seed rows, optionally with a
    ruling_graha changed ({direction: new graha}) or one graha's row removed."""
    rows = [dict(r) for r in VASTU_DIRECTIONS]
    for r in rows:
        if swap and r["direction"] in swap:
            r["ruling_graha"] = swap[r["direction"]]
    if drop_graha:
        rows = [r for r in rows if r["ruling_graha"] != drop_graha]
    return rows


class _Cursor:
    def __init__(self, conn: "_Conn"):
        self.conn = conn
        self._result: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    # -- SELECT list parsing: tolerate any column list / `*` / aliases ------------------------------
    @staticmethod
    def _select_columns(sql: str) -> list[str]:
        m = re.search(r"select\s+(.*?)\s+from\s", sql, re.IGNORECASE | re.DOTALL)
        if not m:
            return list(_L0_COLUMNS)
        out: list[str] = []
        for part in m.group(1).split(","):
            part = part.strip()
            if part == "*":
                return list(_L0_COLUMNS)
            name = re.split(r"\s+as\s+", part, flags=re.IGNORECASE)[0].strip().split(".")[-1]
            out.append(name)
        return out

    def execute(self, sql, params=None):
        text = " ".join(str(sql).split())
        self.conn.statements.append((text, params))
        low = text.lower()
        self._result = []
        if low.startswith("select") and "bg_vastu_directions" in low:
            cols = self._select_columns(text)
            self._result = [tuple(r.get(c) for c in cols) for r in self.conn.l0_rows]
        elif low.startswith("insert into ga_vastu_planet_direction_map"):
            cols_m = re.search(r"insert into \S+\s*\((.*?)\)\s*values\s*\((.*)\)\s*$", text, re.IGNORECASE)
            assert cols_m, f"unrecognised INSERT shape: {text[:160]}"
            cols = [c.strip() for c in cols_m.group(1).split(",")]
            vals = [v.strip() for v in cols_m.group(2).split(",")]
            assert len(cols) == len(vals), "INSERT column / value count differ"
            row: dict = {}
            pi = 0
            for c, v in zip(cols, vals):
                if v == "%s":
                    row[c] = params[pi]
                    pi += 1
                else:
                    row[c] = v.strip("'")
            self.conn.inserted.append(row)
        # ga_condition_composite SELECT and DELETEs: nothing to serve (scores read as NULL)

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None


class _Conn:
    def __init__(self, l0_rows: list[dict]):
        self.l0_rows = l0_rows
        self.statements: list[tuple[str, object]] = []
        self.inserted: list[dict] = []

    def cursor(self, *args, **kwargs):
        return _Cursor(self)

    def commit(self):  # a writer must never commit ctx.db_conn (contract); a fake that records would catch it
        raise AssertionError("ga_vastu must not commit the orchestrator's connection")


def _build(l0_rows: list[dict]) -> dict[str, str]:
    from ga_writers import ga_vastu_writer as w

    conn = _Conn(l0_rows)
    w.build_ga_vastu_substep(_CHART, _BUILD, "lahiri", conn)
    return {r["graha"]: r["direction"] for r in conn.inserted}


# -- harness sanity: with the UNCHANGED L0 table the writer must give today's eight pairs ------------
# (passes now and after the fix: it proves the fake and the "no output change" claim)


def test_harness_unchanged_l0_table_gives_todays_eight_pairs():
    got = _build(_l0_rows())
    assert got == {
        "Sun": "East", "Moon": "Northwest", "Mars": "South", "Mercury": "North",
        "Jupiter": "Northeast", "Venus": "Southeast", "Saturn": "West", "Rahu": "Southwest",
    }, got   # Ketu: no classical direction, omitted by rule


# -- the held cases -----------------------------------------------------------------------------------


@pytest.mark.xfail(**_HOLD)
def test_changing_a_ruling_graha_in_the_l0_table_moves_the_output():
    """Mutation form: the L0 table is the authority. If East is ruled by Moon and Northwest by Sun
    in `bg_vastu_directions`, the writer must emit Sun->Northwest and Moon->East."""
    got = _build(_l0_rows(swap={"East": "Moon", "Northwest": "Sun"}))
    assert got.get("Sun") == "Northwest" and got.get("Moon") == "East", (
        "ga_vastu ignored bg_vastu_directions: it emitted "
        f"Sun->{got.get('Sun')!r}, Moon->{got.get('Moon')!r} from its writer-local "
        "GRAHA_TO_DIRECTION constant instead of the L0 table's ruling_graha "
        "(CLAUDE.md section N.7 item 3; brief ga_vastu FD-1)"
    )


@pytest.mark.xfail(**_HOLD)
def test_a_missing_l0_direction_row_fails_the_build_loudly():
    """Failing-first form from the brief: delete a row of the fixture L0 table and the build must
    fail loudly, not fall back to a constant."""
    try:
        got = _build(_l0_rows(drop_graha="Rahu"))
    except Exception:
        return   # failed loudly: the designed behaviour
    pytest.fail(
        "ga_vastu built rows although bg_vastu_directions has no row for Rahu: it silently fell "
        f"back to its writer-local constant (Rahu->{got.get('Rahu')!r}); it must fail loudly "
        "(brief ga_vastu FD-1; CLAUDE.md section N.7 items 3 and 6)"
    )


@pytest.mark.xfail(**_HOLD)
def test_writer_module_has_no_local_graha_to_direction_table():
    """Static form: no dict literal in the writer maps the grahas to compass directions (the
    shadow constant, even a currently-correct one, is the defect)."""
    directions = {r["direction"] for r in VASTU_DIRECTIONS}
    grahas = {r["ruling_graha"] for r in VASTU_DIRECTIONS}
    tree = ast.parse((_SIDECAR / _WRITER_REL).read_text(encoding="utf-8"))
    shadows = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict) and n.keys:
            keys = {k.value for k in n.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
            vals = {v.value for v in n.values if isinstance(v, ast.Constant) and isinstance(v.value, str)}
            if len(keys & grahas) >= 6 and vals and vals <= directions:
                shadows.append(n.lineno)
    assert shadows == [], (
        f"{_WRITER_REL} holds a local graha->direction table at line(s) {shadows}; read "
        "bg_vastu_directions.ruling_graha instead (brief ga_vastu FD-1; CLAUDE.md section N.7 item 3)"
    )


def test_the_seed_module_still_has_the_eight_rows_the_writer_must_read():
    """Guards the fixture itself: if the L0 seed changes shape, the cases above must be revisited."""
    assert len(VASTU_DIRECTIONS) == 8
    assert {r["ruling_graha"] for r in VASTU_DIRECTIONS} == {
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"}

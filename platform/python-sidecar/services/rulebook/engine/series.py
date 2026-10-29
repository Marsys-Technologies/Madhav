"""Rule Book engine (E3) — piecewise-constant series over day indices.

A ``Series`` holds a value for each of ``n`` consecutive days as run-length
breakpoints. Values are opaque (Tri for states, int/None for signs, str/None for
lords). Combining several series merges their breakpoints, so the cost of a rule
is the number of days on which any of its inputs changes, not the number of days.
"""

from __future__ import annotations

from bisect import bisect_right
from typing import Any, Callable, Iterator, List, Sequence, Tuple


class Series:
    __slots__ = ("n", "starts", "vals")

    def __init__(self, n: int, starts: Sequence[int], vals: Sequence[Any]):
        if n < 0:
            raise ValueError("negative length")
        if n == 0:
            if starts or vals:
                raise ValueError("empty series carries no runs")
        else:
            if not starts or starts[0] != 0 or len(starts) != len(vals):
                raise ValueError("a series starts at day 0 with one value per run")
            if any(b <= a for a, b in zip(starts, starts[1:])) or starts[-1] >= n:
                raise ValueError("run starts must be strictly increasing and inside the series")
        self.n = n
        self.starts = list(starts)
        self.vals = list(vals)

    # construction --------------------------------------------------------------
    @classmethod
    def const(cls, n: int, value: Any) -> "Series":
        return cls(n, [0] if n else [], [value] if n else [])

    @classmethod
    def from_values(cls, values: Sequence[Any]) -> "Series":
        starts: List[int] = []
        vals: List[Any] = []
        for i, v in enumerate(values):
            if not vals or vals[-1] != v:
                starts.append(i)
                vals.append(v)
        return cls(len(values), starts, vals)

    # access --------------------------------------------------------------------
    def at(self, i: int) -> Any:
        if not 0 <= i < self.n:
            raise IndexError(i)
        return self.vals[bisect_right(self.starts, i) - 1]

    def runs(self) -> Iterator[Tuple[int, int, Any]]:
        """(start, end_exclusive, value) for each run."""
        for k, s in enumerate(self.starts):
            e = self.starts[k + 1] if k + 1 < len(self.starts) else self.n
            yield s, e, self.vals[k]

    def expand(self) -> List[Any]:
        out: List[Any] = []
        for s, e, v in self.runs():
            out.extend([v] * (e - s))
        return out

    def count(self, value: Any) -> int:
        return sum(e - s for s, e, v in self.runs() if v == value)

    # combination ---------------------------------------------------------------
    def map(self, fn: Callable[[Any], Any]) -> "Series":
        return _compress(self.n, self.starts, [fn(v) for v in self.vals])

    @staticmethod
    def zip(fn: Callable[..., Any], *series: "Series") -> "Series":
        if not series:
            raise ValueError("zip needs at least one series")
        n = series[0].n
        if any(s.n != n for s in series):
            raise ValueError("series lengths differ")
        if n == 0:
            return Series(0, [], [])
        starts = sorted({st for s in series for st in s.starts})
        idx = [0] * len(series)
        vals = []
        for st in starts:
            args = []
            for j, s in enumerate(series):
                while idx[j] + 1 < len(s.starts) and s.starts[idx[j] + 1] <= st:
                    idx[j] += 1
                args.append(s.vals[idx[j]])
            vals.append(fn(*args))
        return _compress(n, starts, vals)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Series) and self.n == other.n and self.starts == other.starts and self.vals == other.vals

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Series(n={self.n}, runs={list(self.runs())})"


def _compress(n: int, starts: Sequence[int], vals: Sequence[Any]) -> Series:
    cs: List[int] = []
    cv: List[Any] = []
    for s, v in zip(starts, vals):
        if not cv or cv[-1] != v:
            cs.append(s)
            cv.append(v)
    return Series(n, cs, cv)

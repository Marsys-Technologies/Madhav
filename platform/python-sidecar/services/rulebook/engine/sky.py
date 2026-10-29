"""Rule Book engine (E3) — transit signs from the stored L0 sky calendar.

Source: ``bg_sky_calendar`` ingress rows (Lahiri, exact instants, TRUE node at L0).
The sign of a body at an instant is the sign entered at the latest ingress row at
or before that instant. The engine never root-finds an instant itself (B.10).

The sign is unknown (None -> NOT_ASSESSED) when:
- the instant precedes the body's first stored ingress;
- the instant is after the stored coverage end (the last Moon ingress);
- the ingress chain is broken inside that interval (consecutive rows must move one
  sign forward or back: a retrograde re-entry is one back; anything else means an
  ingress is missing between the two rows).
"""

from __future__ import annotations

from bisect import bisect_right
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from . import constants as K


class SkyDataError(ValueError):
    pass


class SkyTable:
    def __init__(self, rows: Iterable[Mapping[str, Any]], coverage_end_jd: Optional[float] = None):
        by_body: Dict[str, List[Tuple[float, int, Any]]] = {}
        for r in rows:
            if r.get("event_type") != K.SKY_EVENT_INGRESS:
                continue
            body = r["primary_body"]
            sign = K.SIGN_NUMBER.get(r["sign"])
            if sign is None:
                raise SkyDataError(f"ingress row with unknown sign {r['sign']!r}")
            by_body.setdefault(body, []).append((float(r["event_jd"]), sign, r.get("id")))
        self._jds: Dict[str, List[float]] = {}
        self._signs: Dict[str, List[int]] = {}
        self._ids: Dict[str, List[Any]] = {}
        self._broken: Dict[str, List[bool]] = {}
        self.chain_defects: Dict[str, int] = {}
        for body, seq in by_body.items():
            seq.sort(key=lambda t: t[0])
            jds = [t[0] for t in seq]
            if any(b <= a for a, b in zip(jds, jds[1:])):
                raise SkyDataError(f"{body}: duplicate or unordered ingress instants")
            signs = [t[1] for t in seq]
            broken = [False] * len(seq)
            defects = 0
            for i in range(1, len(seq)):
                step = (signs[i] - signs[i - 1]) % 12
                if step not in (1, 11):
                    broken[i - 1] = True  # a missed ingress lies inside the interval opened by row i-1
                    defects += 1
            self._jds[body], self._signs[body] = jds, signs
            self._ids[body], self._broken[body] = [t[2] for t in seq], broken
            self.chain_defects[body] = defects
        if coverage_end_jd is None:
            moon = self._jds.get("Moon")
            coverage_end_jd = moon[-1] if moon else None
        self.coverage_end_jd = coverage_end_jd

    @property
    def bodies(self) -> Tuple[str, ...]:
        return tuple(sorted(self._jds))

    def first_jd(self, body: str) -> Optional[float]:
        j = self._jds.get(body)
        return j[0] if j else None

    def sign_at(self, body: str, jd: float) -> Optional[int]:
        jds = self._jds.get(body)
        if not jds:
            return None
        if self.coverage_end_jd is None or jd > self.coverage_end_jd:
            return None
        i = bisect_right(jds, jd) - 1
        if i < 0 or self._broken[body][i]:
            return None
        return self._signs[body][i]

    def fingerprint(self) -> str:
        """sha256 over (body, sign, instant) of every ingress row, in a fixed order, plus the coverage end."""
        import hashlib

        h = hashlib.sha256()
        for body in self.bodies:
            for jd, sign in zip(self._jds[body], self._signs[body]):
                h.update(f"{body}|{sign}|{jd:.6f}\n".encode("ascii"))
        h.update(f"coverage_end|{self.coverage_end_jd}\n".encode("ascii"))
        return h.hexdigest()

    def row_id_at(self, body: str, jd: float) -> Any:
        jds = self._jds.get(body)
        if not jds:
            return None
        i = bisect_right(jds, jd) - 1
        return self._ids[body][i] if i >= 0 else None


def sky_from_fixture(doc: Mapping[str, Any]) -> SkyTable:
    """Fixture: {"rows": [{"id","event_type","primary_body","sign","event_jd"}], "coverage_end_jd": float|null}."""
    return SkyTable(doc.get("rows") or [], doc.get("coverage_end_jd"))

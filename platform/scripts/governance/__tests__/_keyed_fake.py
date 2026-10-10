"""_keyed_fake.py: a FAKE psql runner for the keyed-exact-read tests (Nikasha lane W3). No database of any kind is started or reached.

`FakeKeyedDB` stands in for `asset_census.scalar`. It answers the engine's own statements from PLANTED per-partition results: the catalog estimate, the index catalog, the grouped partition counts and the
per-partition reads (templated pointer, json closure chunk, source presence). Each partition is a dict: `n` (rows), plus read-specific plants (`unmatched`, `other`, `bad_rows`, `lacking`, ...), `timeout` (the read of
that partition raises the server's own timeout error text), `read_n` (the count the partition read reports, to plant a table that changed under the read). A statement WITHOUT a partition predicate is the
whole-table read: it is answered from the union of all partitions, so a keyed answer can be compared with the whole-table one on the same planted data.
"""
from __future__ import annotations

import json
import re

import asset_census as ac

TIMEOUT = "ERROR:  canceling statement due to statement timeout"
_PART = re.compile(r'"a" (?:IS NULL|= \'([^\']*)\')')


class FakeKeyedDB:
    def __init__(self, parts, *, est=500_000, total=None, unique=False, cols=("a",), index="kt_idx"):
        self.parts = {k: dict(v) for k, v in parts.items()}                 # key text (None = NULL) -> plants
        self.est, self.total, self.unique, self.cols, self.index = est, total, unique, cols, index
        self.calls: list = []
        self.handlers: list = []                                            # [(marker substring, fn(db, sql, part_key or ALL, parts) -> str)]
        self.groups_lie = 0                                                 # added to the first group's count in the groups answer (counts that do not add up)

    ALL = object()

    def on(self, marker, fn):
        self.handlers.append((marker, fn))
        return self

    def install(self, monkeypatch):
        monkeypatch.setattr(ac, "scalar", self)
        return self

    def sum_n(self):
        return sum(p["n"] for p in self.parts.values())

    def __call__(self, sql):
        self.calls.append(sql)
        if "reltuples" in sql:
            return str(self.est)
        if "pg_index" in sql:
            return json.dumps([dict(name=self.index, unique=self.unique, nkeys=len(self.cols), cols=[dict(c=c, t="integer") for c in self.cols])])
        if "'groups'" in sql:
            groups = [dict(k=[k], n=p["n"]) for k, p in self.parts.items()]
            if groups and self.groups_lie:
                groups[0]["n"] += self.groups_lie
            return json.dumps(dict(total=self.sum_n() if self.total is None else self.total, groups=groups))
        for marker, fn in self.handlers:
            if marker in sql:
                m = _PART.search(sql)
                key = self.ALL if m is None else (m.group(1) if m.group(1) is not None else None)
                if key is not self.ALL and key not in self.parts:
                    raise AssertionError(f"a statement names a partition the plan never listed: {key!r}")
                sel = list(self.parts.values()) if key is self.ALL else [self.parts[key]]
                if any(p.get("timeout") for p in sel):
                    raise ac.Unknown(TIMEOUT)
                return fn(self, sql, key, sel)
        raise AssertionError(f"unexpected statement: {sql[:200]}")

    def partition_statements(self, marker):
        return [s for s in self.calls if marker in s and _PART.search(s)]

    def whole_statements(self, marker):
        return [s for s in self.calls if marker in s and not _PART.search(s)]


def templated_handler(db, sql, key, sel):
    lim = ac.FORMGAP_SAMPLE_LIMIT
    d = dict(unmatched=[x for p in sel for x in p.get("unmatched", [])][:lim], other_chart=[x for p in sel for x in p.get("other", [])][:lim])
    if key is not db.ALL:
        d["n"] = sel[0].get("read_n", sel[0]["n"])
    return json.dumps(d)


def clean(n):
    return dict(n=n)


THREE = {"1": clean(40000), "2": clean(40000), "3": clean(40000)}        # 120 000 rows in scope: above the 100 000 threshold

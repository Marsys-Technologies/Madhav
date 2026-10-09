"""brahmagyan.ayanamsha_scope: default five, validated configuration, one column check per minute."""
from __future__ import annotations

import pytest

from brahmagyan import ayanamsha_scope as sc

FIVE = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
CHART = "482012f1-710e-4a25-994a-93821f5871aa"


class Cur:
    def __init__(self, conn):
        self.c, self.row = conn, None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        self.c.sqls.append((s, params))
        if "information_schema.columns" in s:
            self.row = (1,) if self.c.has_column else None
        elif s.startswith("SELECT build_ayanamshas FROM charts WHERE id = %s::uuid"):
            self.row = (self.c.value,) if self.c.has_row else None
        else:
            raise AssertionError(s)

    def fetchone(self):
        return self.row


class Conn:
    def __init__(self, has_column=False, value=None, has_row=True):
        self.has_column, self.value, self.has_row, self.sqls = has_column, value, has_row, []

    def cursor(self):
        return Cur(self)

    def commit(self):
        raise AssertionError("never commit the caller's connection")

    def close(self):
        raise AssertionError("never close the caller's connection")


@pytest.fixture(autouse=True)
def _fresh():
    sc.reset_cache()
    yield
    sc.reset_cache()


def test_canonical_five_in_the_repo_order():
    assert list(sc.CANONICAL_FIVE) == FIVE


def test_default_without_the_column_is_the_five_and_a_fresh_list_each_time():
    a = sc.ayanamshas_for_chart(Conn(has_column=False), CHART)
    b = sc.ayanamshas_for_chart(Conn(has_column=False), CHART)
    assert a == FIVE and a is not b
    a.append("x")
    assert sc.default_ayanamshas() == FIVE


def test_null_value_is_the_default():
    assert sc.ayanamshas_for_chart(Conn(has_column=True, value=None), CHART) == FIVE


def test_missing_chart_row_is_the_default():
    assert sc.ayanamshas_for_chart(Conn(has_column=True, has_row=False), CHART) == FIVE


def test_configured_subset_is_returned_in_canonical_order_without_duplicates():
    got = sc.ayanamshas_for_chart(Conn(has_column=True, value=["raman", "lahiri_chitrapaksha", "raman"]), CHART)
    assert got == ["lahiri_chitrapaksha", "raman"]
    assert sc.ayanamshas_for_chart(Conn(has_column=True, value=["lahiri_chitrapaksha"]), CHART) == ["lahiri_chitrapaksha"]


def test_unknown_id_raises():
    with pytest.raises(sc.AyanamshaScopeError, match="unknown"):
        sc.ayanamshas_for_chart(Conn(has_column=True, value=["lahiri_chitrapaksha", "lahiri"]), CHART)


def test_configured_but_empty_raises_instead_of_widening():
    for bad in ([], ["", "  "]):
        sc.reset_cache()
        with pytest.raises(sc.AyanamshaScopeError, match="empty"):
            sc.ayanamshas_for_chart(Conn(has_column=True, value=bad), CHART)


def test_chart_key_is_charts_id_and_the_value_is_bound_not_formatted():
    conn = Conn(has_column=True, value=None)
    sc.ayanamshas_for_chart(conn, CHART)
    sql, params = conn.sqls[-1]
    assert "WHERE id = %s::uuid" in sql and "chart_id" not in sql
    assert params == (CHART,)


def test_column_presence_is_checked_once_per_minute_not_per_call(monkeypatch):
    t = [1000.0]
    monkeypatch.setattr(sc, "_monotonic", lambda: t[0])
    conn = Conn(has_column=True, value=None)
    for _ in range(5):
        sc.ayanamshas_for_chart(conn, CHART)
    assert sum("information_schema" in s for s, _ in conn.sqls) == 1
    t[0] += 61
    sc.ayanamshas_for_chart(conn, CHART)
    assert sum("information_schema" in s for s, _ in conn.sqls) == 2


def test_the_column_appearing_later_is_picked_up_after_the_ttl(monkeypatch):
    t = [0.0]
    monkeypatch.setattr(sc, "_monotonic", lambda: t[0])
    conn = Conn(has_column=False)
    assert sc.ayanamshas_for_chart(conn, CHART) == FIVE
    conn.has_column, conn.value = True, ["krishnamurti"]
    assert sc.ayanamshas_for_chart(conn, CHART) == FIVE       # still cached
    t[0] += 61
    assert sc.ayanamshas_for_chart(conn, CHART) == ["krishnamurti"]


def test_dict_rows_are_supported():
    class DCur(Cur):
        def fetchone(self):
            r = super().fetchone()
            return None if r is None else {"v": r[0]}
    class DConn(Conn):
        def cursor(self):
            return DCur(self)
    assert sc.ayanamshas_for_chart(DConn(has_column=True, value=["raman"]), CHART) == ["raman"]

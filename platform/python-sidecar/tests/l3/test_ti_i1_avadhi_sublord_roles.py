"""
Suvarna Track I-1 — ka_avadhi `sublord_modulation.note` role swap.

THE DEFECT. `_FETCH_AD_SQL` selects the AD row as `d` (`d.lord_graha` = the AD lord) joined to its
parent MD as `p` (`p.lord_graha AS parent_lord_graha`). `run()` calls
`_build_row(ad, sublord=ad.get("parent_lord_graha"))`, so inside `_build_row` `sublord` is the PARENT
(MD) lord and `lord` is the AD's own lord. The note was `f"AD lord {sublord} modulates MD lord
{lord}."`, i.e. both roles swapped (live rows read "AD lord Dhanya modulates MD lord Bhadrika"
when Dhanya was the MD). `sublord_modulation.graha` holds the modulated MD lord and must agree
with the note's "MD lord" slot and with the row's `lord_graha` (the AD lord).

These tests drive the real `run()` over a fake connection, so they fail against the pre-fix writer.
"""
from __future__ import annotations

import json
from datetime import date
from types import SimpleNamespace

from pipeline.orchestrator.writers.ka_avadhi import KaAvdhiWriter
from services.ka_dasha_kala.tree_walk import ALL_DASHA_SYSTEMS


class _Cur:
    def __init__(self, conn):
        self.conn = conn
        self._rows = []

    def __enter__(self): return self
    def __exit__(self, *a): return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        self._rows = []
        if "d.level_n = 1" in s:
            self._rows = self.conn.md_rows
        elif "d.level_n = 2" in s:
            self._rows = self.conn.ad_rows
        elif s.startswith("DELETE FROM kala_avadhi"):
            pass

    def executemany(self, sql, rows):
        self.conn.inserted = list(rows)

    def fetchall(self): return list(self._rows)
    def fetchone(self): return None   # bodha tables "do not exist"


class _Conn:
    def __init__(self, md_rows, ad_rows):
        self.md_rows, self.ad_rows, self.inserted = md_rows, ad_rows, []

    def cursor(self, **kw): return _Cur(self)


def _rows(md_lord: str, ad_lord: str):
    md, ad = [], []
    for sys_id in ALL_DASHA_SYSTEMS:
        md.append({"chart_id": "c", "system_id": sys_id, "lord_graha": md_lord, "level_n": 1,
                   "period_start": date(2020, 1, 1), "period_end": date(2030, 1, 1)})
        ad.append({"chart_id": "c", "system_id": sys_id, "lord_graha": ad_lord, "level_n": 2,
                   "period_start": date(2020, 1, 1), "period_end": date(2021, 1, 1),
                   "parent_lord_graha": md_lord})
    return md, ad


def _run(md_lord: str, ad_lord: str):
    md, ad = _rows(md_lord, ad_lord)
    conn = _Conn(md, ad)
    ctx = SimpleNamespace(db_conn=conn, config={"chart_id": "c"}, dry_run=False)
    KaAvdhiWriter().run(ctx)
    return conn.inserted


def test_antardasha_note_names_ad_lord_as_ad_and_parent_as_md() -> None:
    out = _run(md_lord="Dhanya", ad_lord="Bhadrika")
    ad_rows = [r for r in out if r["level_n"] == 2]
    assert ad_rows
    for r in ad_rows:
        mod = json.loads(r["dossier"])["sublord_modulation"]
        assert r["lord_graha"] == "Bhadrika"
        assert mod["note"] == "AD lord Bhadrika modulates MD lord Dhanya."


def test_graha_field_is_the_md_lord_named_in_the_note() -> None:
    for r in (x for x in _run("Saturn", "Jupiter") if x["level_n"] == 2):
        mod = json.loads(r["dossier"])["sublord_modulation"]
        assert mod["graha"] == "Saturn"
        assert mod["note"].endswith("MD lord Saturn.")
        assert mod["note"].startswith(f"AD lord {r['lord_graha']} ")


def test_md_rows_carry_no_modulation() -> None:
    md_rows = [r for r in _run("Saturn", "Jupiter") if r["level_n"] == 1]
    assert md_rows
    assert all(json.loads(r["dossier"])["sublord_modulation"] is None for r in md_rows)

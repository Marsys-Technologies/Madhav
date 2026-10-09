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

from tests.l3.ka_avadhi.test_dossiers import period, clock
from pipeline.orchestrator.writers.ka_avadhi import build_dossier
from services.kala_core import sky


def _run(md_lord: str, ad_lord: str):
    context = clock()
    context.lords.update(MD=md_lord, AD=ad_lord)
    answer = sky.unavailable(sky.coverage_of((1, 1), None, backend="swieph", convention_id="CODEX"))
    system = "yogini" if ad_lord == "Bhadrika" else "vimshottari"
    rows = []
    for lord, level in [(md_lord, 1), (ad_lord, 2)]:
        source = dict(period(lord, level), system_id=system)
        rows.append(dict(source, dossier=build_dossier(source, [], [], context, answer)))
    return rows


def test_antardasha_note_names_ad_lord_as_ad_and_parent_as_md() -> None:
    out = _run(md_lord="Dhanya", ad_lord="Bhadrika")
    ad_rows = [r for r in out if r["level_n"] == 2]
    assert ad_rows
    for r in ad_rows:
        mod = r["dossier"]["sublord_modulation"]
        assert r["lord_graha"] == "Bhadrika"
        assert mod["note"] == "AD lord Bhadrika modulates MD lord Dhanya."


def test_graha_field_is_the_md_lord_named_in_the_note() -> None:
    for r in (x for x in _run("Saturn", "Jupiter") if x["level_n"] == 2):
        mod = r["dossier"]["sublord_modulation"]
        assert mod["graha"] == "Saturn"
        assert mod["note"].endswith("MD lord Saturn.")
        assert mod["note"].startswith(f"AD lord {r['lord_graha']} ")


def test_md_rows_carry_no_modulation() -> None:
    md_rows = [r for r in _run("Saturn", "Jupiter") if r["level_n"] == 1]
    assert md_rows
    assert all(r["dossier"]["sublord_modulation"] is None for r in md_rows)

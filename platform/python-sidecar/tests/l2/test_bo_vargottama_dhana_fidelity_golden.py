"""Golden-value narration fidelity test for bo_vargottama_dhana.

Expected sentences are hand-composed from the emitter's f-string templates and
the valence doctrine: Mercury (natural +0.3, no dignity modifier) is benefic;
exalted Rahu in Taurus (natural -1.0, exalted +0.5) is MIXED; Moon (natural
+0.5) is benefic. Lagna Aries makes house 2 Taurus (lord Venus) and house 11
Aquarius (lord Saturn).
"""
from __future__ import annotations

from bodha_writers.vargottama_dhana_emitter import (
    build_dhana_axis_rows,
    build_vargottama_rows,
)


def test_vargottama_dhana_headline_summary_citation_golden():
    vg_rows = build_vargottama_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        vargottama_facts={"MER": {"is_vargottama": True, "fact_id": "fmer"}},
        positions={"MER": {"house_d1": {"num": 10, "fact_id": "mh"},
                           "sign": {"text": "Capricorn", "fact_id": "ms"}}},
        now="2026-01-01T00:00:00+00:00",
    )
    assert len(vg_rows) == 1
    vg = vg_rows[0]
    built = {
        "signal_headline_text": vg["signal_headline_text"],
        "signal_summary_text": vg["signal_summary_text"],
        "citation_human": vg["citation_human"],
    }
    assert built == {
        "signal_headline_text": (
            "Mercury is VARGOTTAMA (D1=D9 sign Capricorn)"
            " \u2014 cross-frame confirmed strength (benefic)"
        ),
        "signal_summary_text": (
            "category=vargottama_amplification | graha=Mercury | varga=D9 | "
            "house_d1=10 | sign=Capricorn | valence=benefic"
        ),
        "citation_human": (
            "Mercury is VARGOTTAMA (D1=D9 sign Capricorn)"
            " \u2014 cross-frame confirmed strength (benefic)"
        ),
    }

    dh_rows = build_dhana_axis_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        positions={
            "LAGNA": {"sign": {"text": "Aries", "fact_id": "lg"}},
            "RAH_MEAN": {"house_d1": {"num": 2, "fact_id": "rh"},
                         "sign": {"text": "Taurus", "fact_id": "rs"}},
            "VEN": {"house_d1": {"num": 5, "fact_id": "vh"}},
            "MOON": {"house_d1": {"num": 11, "fact_id": "mnh"},
                     "sign": {"text": "Aquarius", "fact_id": "mns"}},
        },
        now="2026-01-01T00:00:00+00:00",
    )
    assert len(dh_rows) == 2
    h2, h11 = dh_rows
    assert h2["signal_headline_text"] == (
        "2nd house (dhana): Taurus, lord Venus — tenanted by Rahu (mixed);"
        " Venus itself sits in H5"
    )
    assert h2["signal_summary_text"] == (
        "category=dhana_axis | house=2 | sign=Taurus | lord=Venus | "
        "occupants=['Rahu'] | lord_placed_in_house=5 | valence=mixed"
    )
    assert h11["signal_headline_text"] == (
        "11th house (labha): Aquarius, lord Saturn — tenanted by Moon (benefic)"
    )
    assert h11["signal_summary_text"] == (
        "category=dhana_axis | house=11 | sign=Aquarius | lord=Saturn | "
        "occupants=['Moon'] | valence=benefic"
    )
    assert h11["citation_human"] == (
        "11th house (labha): Aquarius, lord Saturn — tenanted by Moon (benefic)"
    )

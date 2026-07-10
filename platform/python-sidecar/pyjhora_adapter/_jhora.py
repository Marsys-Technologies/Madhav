"""
Headless PyJHora import shim.

CRITICAL: never `import jhora` at module import time — the top-level package
pulls GUI paths (PyQt6) that crash in a headless container. Instead we import
ONLY the calculation submodules (panchanga.drik, horoscope.chart.charts,
horoscope.dhasa.graha.vimsottari), which are pure swisseph/numpy.

We also force QT_QPA_PLATFORM=offscreen defensively in case any transitive
import touches Qt.
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Direct-submodule imports — these do NOT import PyQt6.
from jhora.panchanga import drik  # noqa: E402
from jhora import utils, const  # noqa: E402
from jhora.horoscope.chart import charts  # noqa: E402

# Pin Rahu/Ketu to the MEAN node (swe.MEAN_NODE) for ALL ayanamshas.
# Two reasons:
#   1. Matches the project's MEAN_NODE rebuild convention and the
#      project's documented MEAN_NODE rebuild.
#   2. PyJHora defaults to the osculating TRUE node (swe.TRUE_NODE), which fails
#      under some ayanamshas (e.g. TRUE_CITRA) with a swisseph Moshier
#      out-of-range error because no planetary .se1 ephemeris files ship with
#      the wheel. The MEAN node has no such dependency and stays exactly 180 deg
#      from Ketu by construction.
const.set_node_mode(False)

# Several PyJHora code paths (charts.rasi_chart, charts.divisional_chart, the
# Vimshottari dasha engine) HARDCODE the osculating TRUE node (swe.TRUE_NODE,
# id 11) regardless of const.set_node_mode. Under some ayanamshas (notably
# TRUE_CITRA) swisseph cannot compute the TRUE node without planetary .se1
# ephemeris files (which the wheel does not ship) and raises a misleading
# "jd -0.001010 outside Moshier planet range" error. The MEAN node (id 10) is
# always computable and is the project's chosen convention anyway. We therefore
# transparently redirect any TRUE-node request to the MEAN node at the lowest
# shared layer — drik.sidereal_longitude — so every downstream PyJHora path
# computes Rahu/Ketu from the mean node, consistently and ephemeris-free.
import swisseph as _swe  # noqa: E402

_orig_sidereal_longitude = drik.sidereal_longitude


def _sidereal_longitude_mean_node(jd_utc, planet):
    if planet == _swe.TRUE_NODE:
        planet = _swe.MEAN_NODE
    return _orig_sidereal_longitude(jd_utc, planet)


drik.sidereal_longitude = _sidereal_longitude_mean_node

__all__ = ["drik", "utils", "const", "charts", "get_vimsottari",
           "get_ashtakavarga", "get_house"]


def get_vimsottari():
    """Lazy-import the Vimshottari dasha engine (kept lazy to isolate any
    heavier transitive imports from the hot calculation path)."""
    from jhora.horoscope.dhasa.graha import vimsottari
    return vimsottari


def get_ashtakavarga():
    """Lazy-import jhora.horoscope.chart.ashtakavarga (pure numpy/const —
    no PyQt6 transitive import). Exposes the real BPHS 8x8 contributor-map
    Ashtakavarga engine: get_ashtaka_varga() + sodhaya_pindas()."""
    from jhora.horoscope.chart import ashtakavarga
    return ashtakavarga


def get_house():
    """Lazy-import jhora.horoscope.chart.house (pure const/utils — no
    PyQt6 transitive import). Exposes the real Panchadha Maitri (5-fold
    compound naisargika+tatkalika relationship) engine:
    _get_compound_relationships_of_planets()."""
    from jhora.horoscope.chart import house
    return house

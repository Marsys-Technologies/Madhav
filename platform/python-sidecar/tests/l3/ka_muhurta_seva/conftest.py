"""Synthetic candidate sky: never a computation or claim about the native."""
import pytest

from services.kala_core.sky.coverage import SkyResult, coverage_of
from services.kala_core.sky.ephemeris import (
    BodyPosition, EphemerisAnswer, LocalAnswer, SkyConvention,
    EPHE_FLAGS, EPHE_FLAG_NAMES, LAGNA_FLAGS, LAGNA_FLAG_NAMES,
)


@pytest.fixture
def request_data():
    return dict(candidate={"start_utc": "2026-10-15T06:00:00Z", "end_utc": "2026-10-15T06:20:00Z"},
                undertaking="marriage", location={"lat": 20.27, "lon": 85.84, "tz_offset_minutes": 330},
                dosas_present=["venus_sixth"])


@pytest.fixture
def sky(monkeypatch):
    from services.ka_muhurta_seva import parihara_eval as ev

    def install(*, longitudes=None, lagna=0.0, sequences=None, speeds=None, alter=None):
        values = dict(Sun=0., Moon=190., Mars=100., Mercury=50., Jupiter=120., Venus=160., Saturn=220.)
        values.update(longitudes or {})
        calls = []
        convention = SkyConvention()

        def ephemeris(jd, *args, **kwargs):
            i = len(calls)
            calls.append(jd)
            positions = tuple(BodyPosition(p, (sequences or {}).get(p, [v]*3)[i],
                                            (speeds or {}).get(p, 1.)) for p, v in values.items())
            cov = coverage_of((jd, jd), (jd-1, jd+1), backend="swieph", convention_id=convention.convention_id)
            answer = EphemerisAnswer(jd, "UT", "swiss_instant", "swieph", EPHE_FLAGS, EPHE_FLAG_NAMES,
                                     "mean", convention.ayanamsha_id, 24., convention.convention_id, positions)
            result = SkyResult((answer,), cov)
            return alter(result, i) if alter else result

        def rising(jd, location, civil, *args, **kwargs):
            v = lagna if isinstance(lagna, (int, float)) else lagna[len(calls)-1]
            cov = coverage_of((jd, jd), (jd-1, jd+1), backend="swiss_houses", convention_id=convention.convention_id)
            return SkyResult((LocalAnswer("lagna", jd, "UT", "fixture", location, civil, v,
                             "swiss_houses", LAGNA_FLAGS, LAGNA_FLAG_NAMES, "mean", convention.ayanamsha_id,
                             24., convention.convention_id),), cov)

        monkeypatch.setattr(ev, "ephemeris_at", ephemeris)
        monkeypatch.setattr(ev, "lagna_at", rising)
        return calls
    return install


@pytest.fixture
def rule():
    def make(predicate=None, **kwargs):
        r = dict(id=101, dosha_canonical_id="venus_sixth", scope="marriage", source_citation="Muhūrta Cintāmaṇi v.88",
                 source_chunk_id="muhurta_chintamani_pg0116_c01", source_verse=88, predicate=predicate,
                 conjunction_reading="tika", tika_extension=False, priority_rank=None,
                 net_standing="cancellable_by_condition", extraction_context="tika_commentary")
        r.update(kwargs)
        return r
    return make

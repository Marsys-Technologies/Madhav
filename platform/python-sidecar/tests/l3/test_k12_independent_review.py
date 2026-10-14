"""Independent K12 review probes; no production changes."""
from dataclasses import replace
from datetime import timedelta
import inspect
import pytest
from services.kala_core import clocks, sky
from services.ka_dasha_kala import KaDashaKalaService
from pipeline.orchestrator.writers.ka_avadhi import build_dossier
from tests.l3.kala_core.clocks.test_k12_regressions import Conn, row, T0, PIN
from tests.l3.kala_core.clocks.test_methods import L1, CHART, ashtottari, PIN as METHODS_PIN
from tests.l3.ka_avadhi.test_dossiers import period, facts, clock


def compatible_boundaries(rows):
    # Accept either old/new signature to probe endpoint/eligibility behavior.
    kwargs = {'as_of': T0} if 'as_of' in inspect.signature(clocks.boundaries).parameters else {}
    return clocks.boundaries(Conn(rows), 'chart', 'vimshottari', **PIN, **kwargs)


def test_terminal_endpoint_survives_even_with_the_prior_signature():
    end=T0+timedelta(days=200)
    found=compatible_boundaries([row(),row('md2',start=100,end=200,is_truncated_at_window_end=True)])
    assert any(b.instant==end and b.boundary_truncated for b in found)


@pytest.mark.parametrize('kind',['inapplicable','orphan','wrong_tier_parent'])
def test_boundary_eligibility_survives_even_with_the_prior_signature(kind):
    parent=row(); selected=[parent]
    if kind=='inapplicable': parent['applies_to_this_chart_flag']=False
    else:
        selected.append(row('ad',2,'absent' if kind=='orphan' else 'md',end=50))
        if kind=='wrong_tier_parent': parent['verification_pass_status']='single'
    with pytest.raises(clocks.ClockUnavailable): compatible_boundaries(selected)


def test_clipped_start_cannot_be_called_natural_commencement():
    p=period(); p['is_truncated_at_window_start']=True
    p['is_truncated_at_window_end']=False
    answer=sky.ephemeris_at(2451545.,sky.SkyConvention(),bodies=('Mars',))
    assert answer.available
    clipped=replace(clock(),boundary_truncated=True)
    result=build_dossier(p,facts(),[],clipped,answer)
    assert result['commencement_condition']['value'] is None, 'window-clipped start was promoted to natural commencement'


def test_clipped_end_qualification_survives_the_dossier_projection():
    p=period(); p['is_truncated_at_window_start']=False
    p['is_truncated_at_window_end']=False
    unknown=sky.unavailable(sky.coverage_of((2451545.,2451545.),None,backend='swieph',convention_id='review'))
    natural=build_dossier(p,facts(),[],clock(),unknown)
    p['is_truncated_at_window_end']=True
    clipped=build_dossier(p,facts(),[],replace(clock(),boundary_truncated=True),unknown)
    assert natural != clipped, 'dossier discards the clipped-end qualification entirely'


def test_facade_forwards_applicability_evidence_to_boundary_reader():
    evidence=ashtottari(lord_house=4)
    conn=L1(system='ashtottari')
    expected=clocks.boundaries(conn,CHART,'ashtottari',as_of=T0,method_facts=evidence,**METHODS_PIN)
    assert expected
    actual=KaDashaKalaService(conn).boundaries(CHART,'ashtottari',as_of=T0,method_facts=evidence,**METHODS_PIN)
    assert actual==expected

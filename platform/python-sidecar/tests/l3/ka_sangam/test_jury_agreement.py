import importlib
from dataclasses import replace
from services.kala_core.measure import Interval, Verdict


def api(): return importlib.import_module('services.ka_sangam.jury.agreement')


def inputs():
    e=importlib.import_module('services.ka_sangam.jury.evidence')
    g=importlib.import_module('services.ka_sangam.jury.groups')
    n=[e.Node('p',frozenset({'judge:1'})),e.Node('j',frozenset({'cara:1','rasi:1'}))]
    u=[e.Use('p','G-P',Interval(0,10),'corroborates'),e.Use('j','G-J',Interval(2,8),'corroborates')]
    groups=tuple(g.admit(x,(x.group_id+':input',),(Interval(0,30),),('review:1',),complete_method=True) if x.group_id in ('G-P','G-J') else x for x in g.declarations(Interval(0,30)))
    return n,u,groups


def run(n,u,g): return api().agreement(Interval(0,30),n,u,g,alpha=.05,exchangeable=False,non_identity_shifts=31)


def test_half_open_disjoint_edges_have_no_joint_segment():
    e=importlib.import_module('services.ka_sangam.jury.evidence'); n,u,g=inputs()
    u=[replace(u[0],interval=Interval(0,1)),replace(u[1],interval=Interval(29,30))]
    r=run(n,u,g)
    assert not any(s.support==frozenset({'G-P','G-J'}) for s in r.segments)


def test_universal_witness_zero_increment_and_explicit_noninformative():
    n,u,g=inputs(); r=run(n,[u[0],replace(u[1],interval=Interval(0,30))],g)
    assert abs(r.conditional.effect)<1e-12
    assert r.conditional.reason=='zero_null_variance'


def test_stage_relocation_and_duplicate_alias_leave_D_unchanged():
    e=importlib.import_module('services.ka_sangam.jury.evidence'); n,u,g=inputs(); before=run(n,u,g)
    n.append(e.Node('alias',frozenset(),('j',)))
    after=run(n,u+[replace(u[1],node_id='alias')],g)
    assert before==after


def test_p8_selected_cara_never_gains_GJ_credit():
    n,u,g=inputs(); n[1]=replace(n[1],selection_roots=frozenset({'cara:1','rasi:1'}))
    r=run(n,u,g)
    assert r.witness_signature==('G-P',)


def test_selection_ancestry_groups_block_p8_overlap():
    n,u,g=inputs(); u.append(replace(u[0],role='selects',ancestry=frozenset({'jaimini_cara'})))
    u[1]=replace(u[1],ancestry=frozenset({'jaimini_cara'}))
    assert run(n,u,g).witness_signature==()


def test_separate_whole_pipeline_experiment_never_reuses_conditional_statistic():
    n,u,g=inputs(); a=api(); r=a.agreement(Interval(0,30),n,u,g,alpha=.05,exchangeable=False,non_identity_shifts=31)
    assert r.pipeline is None and r.pipeline_reason=='whole_pipeline_selector_not_supplied'
    assert r.conditional.denominator==32
    assert r.conditional.surrogate_diagnostic


def test_unavailable_group_and_testimony_cannot_inflate_support():
    n,u,g=inputs(); u.append(replace(u[1],group_id='G-A',testimony=True))
    before,after=run(n,u[:2],g),run(n,u,g)
    assert after.conditional==before.conditional
    assert after.segments==before.segments
    assert after.witness_signature==before.witness_signature


def test_duplicate_group_declarations_add_no_credit():
    n,u,g=inputs()
    assert run(n,u,g+g)==run(n,u,g)


def test_whole_pipeline_selection_reruns_on_each_shared_offset():
    n,u,g=inputs(); a=api(); calls=[]
    def select(draw):
        calls.append(draw.offset)
        return sum(s.interval.duration for s in draw.segments if 'G-P' in s.support and s.interval.start<3)
    selector=a.WholePipelineSelector('rerun fixture selection from shifted judge and clocks',('selector:fixture:1',),select)
    r=a.agreement(Interval(0,30),n,u,g,alpha=.05,exchangeable=False,non_identity_shifts=31,pipeline_selector=selector)
    assert calls==[0]+[30*(i/32) for i in range(1,32)]
    assert r.pipeline.experiment.estimand=='whole_pipeline_selection'
    assert r.pipeline.experiment!=r.conditional.experiment
    assert r.pipeline.null_statistics!=r.conditional.null_statistics


def test_group_ancestry_is_retained_even_if_use_omits_it():
    n,u,g=inputs(); u.append(replace(u[0],role='selects',ancestry=frozenset({'jaimini_cara'})))
    assert run(n,u,g).witness_signature==()


def test_unavailable_group_cannot_steal_shared_root_from_available_anchor():
    n,u,g=inputs(); u.append(replace(u[0],group_id='G-T'))
    before,after=run(n,u[:2],g),run(n,u,g)
    assert after.conditional==before.conditional
    assert after.segments==before.segments
    assert after.witness_signature==before.witness_signature


def test_selected_judge_window_is_conditioning_without_corroboration_credit():
    n,u,g=inputs(); u[0]=replace(u[0],role='selects')
    result=run(n,u,g)
    assert result.witness_signature==('G-J',)
    assert result.conditional.observed==.6
    assert result.conditional.reason!='no_anchor_exposure'


def test_selected_p8_window_keeps_anchor_but_gains_no_GJ_credit():
    n,u,g=inputs(); u[0]=replace(u[0],role='selects',ancestry=frozenset({'jaimini_cara'}))
    result=run(n,u,g)
    assert result.witness_signature==()
    assert result.conditional.observed==0
    assert result.conditional.reason=='zero_null_variance'

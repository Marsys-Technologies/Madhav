#!/usr/bin/env python3
"""A.L4 offline pure-function checks. No database, no writes: imports the repository's own engine modules at main and calls them with synthetic inputs.
Run from the worktree: python3 offline_checks.py <repo-root>"""
import sys, os
root = sys.argv[1] if len(sys.argv) > 1 else '.'
sys.path.insert(0, root + '/platform/python-sidecar'); os.chdir(root + '/platform/python-sidecar')
from datetime import datetime, timezone
print('--- ph_nimitta: posterior for a no-evidence anchor (current code) vs the old default')
from services.ph_nimitta.engine import compute_posterior, _posterior_confidence_band, NimittaContext, _promise_lift
p, l = compute_posterior(0.2, 0.0, 'no_evidence', 0, 0.0, 3); print('current:', p, l.as_dict(), _posterior_confidence_band(p))
p2, _ = compute_posterior(0.2, 5.0, 'conditional', 0, 0.0, 3); print('old default grade5/conditional:', p2)
ctx = NimittaContext(); print('NimittaContext() defaults: grade', ctx.pratijna_grade, 'status', ctx.pratijna_status, 'base_rate', ctx.base_rate, '-> promise_lift', _promise_lift(ctx.pratijna_grade, ctx.pratijna_status))
from services.ph_nimitta.engine import derive_karmic_frame
print('derive_karmic_frame("Saturn -> Venus -> Jupiter (final dispositor)") ->', derive_karmic_frame('Saturn → Venus → Jupiter (final dispositor)'), '; derive_karmic_frame("saturn") ->', derive_karmic_frame('saturn'))
print('--- ph_sodhana: detectors with identical anchors')
from services.ph_sodhana.engine import *
mk = lambda i: AnchorRow(anchor_id=str(i), anchor_source='discovery', domain='career', confidence_low=.322, confidence_high=.372, confidence_basis='structural_not_yet_empirical', magnitude='minor', falsifier='REFUTED if x CONFIRMED if y', derivation_ledger_jsonb={'anchor_source': 'discovery'}, dasha_consensus_count=0, ayanamsha_robustness=3)
for n in (4, 5):
    print(n, 'identical anchors ->', [r.anomaly_type for r in derive_sodhana_flags(SodhanaContext(chart_id='c', anchors=[mk(i) for i in range(n)]))])
a = mk(0); a.falsifier = 'only CONFIRMED here'; print('falsifier with one token flagged?', detect_falsifier_absent(a))
a = mk(0); a.derivation_ledger_jsonb = {'anchor_source': 'x'}; print('ledger with only anchor_source flagged?', detect_ledger_gap(a))
print('--- ph_rectification: select_best with a zero-fit field')
from services.ph_rectification.engine import *
base = datetime(2000, 1, 1, tzinfo=timezone.utc)
c = [RectificationCandidate(o, base, ay, 'X', 10.0, 10.0, True, 0.0, 0, 40) for o in (-5, 0, 5) for ay in AYANAMSHAS]
b = select_best(c, training_events=[]); print('conf_low', b.confidence_low, 'conf_high', b.confidence_high, 'win_margin', b.win_margin, 'label', b.confidence_label, 'offset', b.offset_minutes)
print('--- ph_pramana: LEL category normalisation')
from services.ph_pramana.engine import _normalize_domain
for cat in ['career', 'education', 'spiritual', 'relationship', 'health', 'family', 'residential+travel', 'psychological', 'loss', 'other', 'creative', 'finance', 'travel']:
    print(' ', cat, '->', _normalize_domain(cat))
print('--- ph_muhurta: verdict honesty on placeholder bala')
from services.ph_muhurta.engine import classify_verdict
print(classify_verdict(0.26, tara_chandra_known=False)[0], '|', classify_verdict(0.26, tara_chandra_known=True)[0])
print('--- ph_pratikara: cost tiering with the upstream cost dict shape (no max_inr)')
from services.ph_pratikara.engine import RemedyPrescription, tier_prescriptions, derive_mitigation_record, MitigationContext
cost = {"available": False, "cost_tier": "medium", "reason": "INR pricing requires an external source"}
ps = [RemedyPrescription('p1', 'parashari', 'gemstone', estimated_cost_inr_range=cost)]
t = tier_prescriptions(ps, ['p1']); print({k: len(v) for k, v in t.items()})
print('--- ph_pratikara: empty prescriptions -> record')
r = derive_mitigation_record(MitigationContext(1, 'medium', None, None, 'saturn', None, None, []))
print('program', r.program_jsonb, 'citation', r.classical_citation, 'source_id', r.source_id, 'intensity', r.intensity_tier, 'ctc', r.cross_tradition_corroboration)
print('--- ph_sankrama: cascade chain depth and trajectory with an unknown gradient')
from services.ph_sankrama.engine import CdlmCell, SankramaContext, derive_spillover
cells = [CdlmCell('c1', 'career', 'wealth', 0.5, 0.0, 0, [], [], None), CdlmCell('c2', 'wealth', 'health', 0.5, 0.0, 0, [], [], None)]
by = {('career', 'wealth'): [cells[0]], ('wealth', 'health'): [cells[1]]}
for rec in derive_spillover(SankramaContext('a1', 'career', None, None, 0.372, [cells[0]], by)):
    print('trajectory', rec.trajectory, 'cascade_depth', rec.cascade_depth, 'projected==source window', (rec.projected_window_start, rec.projected_window_end) == (None, None), 'confidence', rec.spillover_confidence, 'asymmetry', rec.asymmetry_score)
print('--- ph_phaladesa: the contradiction sentence with the real jsonb shape (a 3-key dict, contested=false)')
from types import SimpleNamespace as NS
import importlib
w = importlib.import_module('pipeline.orchestrator.writers.ph_phaladesa')
rec = NS(domain='career', magnitude='minor', malleability='influenceable', anchor_count=1, clean_anchor_count=1, prediction_window_start=None, prediction_window_end=None, peak_date=None,
         confidence_low=0.272, confidence_high=0.372, mitigation_available=False, muhurta_available=False, incoming_spillover_count=0, pramana_window_status='open',
         contradiction_summary_jsonb={'contested': False, 'net_direction': 'elevated', 'countervailing_thread': None})
print(w._build_deterministic_narration(rec)['text'])

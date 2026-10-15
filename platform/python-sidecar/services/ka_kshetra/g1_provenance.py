"""Declared G1 constants, not estimates or newly classical claims.

ALGO §3.20 G1 keeps the seeded model. Model constants are disclosed in each
candidate snapshot config_pin; none is silently promoted to calibrated odds.
"""
CONSTANT_PROVENANCE = {
    'functional_form': 'ALGO 3.20 G1; W2_FIELD_DESIGN 5.1; engineering model',
    'coefficients': 'kala_field_weights at pinned weights_version; migration 491 seeded v0_classical, 1331 canonical system aliases; engineering priors, not fitted',
    'P_FLOOR': '0.05; W2 5.1 C-2 engineering regularization',
    'RHO_MAX': '0.95; W2 5.1 positivity bound; engineering',
    'rho_default': '0.25; migration 491 / hazard.evaluate; engineering prior',
    'baseline_shape_only': '1.0 lifetime count; hazard shape_only; synthetic flag always carried',
    'horizon_days': '36525; W2 5.2, 100 Julian years',
    'integrator': 'tau=0.02 nats, max_depth=6; W2 5.2; exhausted refinement flagged',
    'floating_point': 'EPS_GAMMA=1e-12; EXPM1_BRANCH=1e-2; integrator numerical stability',
    'clock_level_decay': 'hazard C-5 level weights; W2 5.1; engineering',
    'null': 'stage5_null/dhara_null pinned replicate and bucket constants; 1023 non-identity shifts + observation; W2 5.5/ALGO 3.20; surrogate, not assumed exchangeable',
    'symbolization': 'station band 1+6*dwell days, syzygy half-width=1.5 days, sandhi half-width=3 days; W2 3.1/3.2, v0 engineering smoothing',
    'kinematics': 'orb default=3deg (named source); Brent xtol=1e-6 days/maxiter=100; moon speed [11.60,15.50]; stage0 3.1 numerical conventions',
    'promise': 'stage2 K-shortest route/noisy-OR, ungraded conductance defaults; W2 3.3, 5.1; retained G1 engineering',
    'salience': 'stage6 salience_v0 five-factor seeded weights; W2 6.1; not calibrated',
    'selection': 'row budget=15 and decade stride=1000000; W2 6.2 / writer storage convention',
    'insights': 'G1(f): noisy-OR prior >=0.60 (distinct from pratijna grade>=6); obstruction engagement/release at zero; scarcity requires searched 5*365.2425 days; contrast disabled without bound baseline; engineering thresholds, not calibrated negative forecasts',
    'suppression_strength': 'active vedha and in-force K3 map to u=1; G1 indicator engineering interpretation; partial/contested unknown scalar omitted with disclosure',
    'moorti': 'KA-3b testimony only; no numeric bridge admitted',
    'time_units': '86400 SI seconds/day; JD_UNIX_EPOCH=2440587.5; noon-UT ephemeris_daily samples; UTC birth origin',
    'rarity_age': '365.2425 days/year; existing W2 6.3 cohort convention, distinct from Julian-year horizon',
}


def numeric_constant_inventory():
    """Source/line inventory of every module-level numeric literal parameter.

    The declaration locator is provenance, not a claim of classical authority.
    Category notes above name the model source; numerical conventions remain
    engineering choices. Database coefficient values are separately hash-pinned.
    """
    import ast
    from pathlib import Path
    root=Path(__file__).parent
    result=[]
    def numeric(value):
        if isinstance(value,bool): return False
        if isinstance(value,(int,float)): return True
        if isinstance(value,dict): return any(numeric(v) for v in value.values())
        if isinstance(value,(list,tuple,set,frozenset)): return any(map(numeric,value))
        return False
    for path in sorted(root.glob('*.py')):
        if path.name=='g1_provenance.py': continue
        source=path.read_text(); lines=source.splitlines()
        for node in ast.parse(source).body:
            if isinstance(node,ast.AnnAssign): targets=[node.target]; value=node.value
            elif isinstance(node,ast.Assign): targets=node.targets; value=node.value
            else: continue
            try: literal=ast.literal_eval(value)
            except (ValueError,TypeError): continue
            for target in targets:
                if not isinstance(target,ast.Name) or not target.id.isupper() or not numeric(literal): continue
                start=node.lineno-2
                while start>=0 and lines[start].lstrip().startswith('#'): start-=1
                comment='\n'.join(lines[start+1:node.lineno-1]).strip()
                result.append({'name':target.id,'declaration':f'platform/python-sidecar/services/ka_kshetra/{path.name}:{node.lineno}',
                    'value':literal,'provenance':comment or 'Engineering convention declared at the cited source line; no independent classical/calibration claim.'})
    return result

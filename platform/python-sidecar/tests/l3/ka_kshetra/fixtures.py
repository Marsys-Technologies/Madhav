"""
tests/l3/ka_kshetra/fixtures.py — a small but GENUINE chart fixture for the
`ka_kshetra` writer.

"Genuine" means the rows have the shapes the real upstream lanes write, the
envelopes obey §3.2's frozen contract, and the field that comes out has real
structure (a hump the null can be compared against) rather than a flat line that
would make every assertion vacuously true.

The horizon is deliberately SHORT (400 days, not 36 525) and the replicate count
small: the numerics are pinned exhaustively by the unit tests in `test_hazard.py`
and `test_integrator.py`, so the writer tests exist to pin the WIRING — substep
order, idempotency, the reconciliation assertion firing at write time, zero
legacy writes, and hash determinism.
"""
from __future__ import annotations

import json

CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
EVENT_CLASS = 'career_change'


def _env(knots):
    return json.dumps([{'t': t, 'v': v} for t, v in knots])


def build_tables(*, with_lifetime_prior: bool = True,
                 life_event_rows: int = 0) -> dict[str, list[dict]]:
    """One chart's upstream state.

    `life_event_rows` seeds a lived-history table that the field must NEVER
    consult. It exists so the Circularity Guard's dynamic half has something that
    genuinely differs between two builds — without it, "the hash didn't move"
    would be a claim with nothing behind it (CLAUDE.md §N.8).
    """
    tables: dict[str, list[dict]] = {
        'kala_field_weight_versions': [
            {'version_id': 'v0_classical', 'status': 'active', 'scope': 'global'},
        ],
        'kala_field_weights': [
            {'version_id': 'v0_classical', 'weight_id': 'w_s:vimshottari', 'weight_value': 1.0},
            {'version_id': 'v0_classical', 'weight_id': 'w_s:yogini', 'weight_value': 0.6},
            {'version_id': 'v0_classical', 'weight_id': 'w_s:naisargika', 'weight_value': 0.0},
            {'version_id': 'v0_classical', 'weight_id': 'beta:x1', 'weight_value': 0.9},
            {'version_id': 'v0_classical', 'weight_id': 'beta:x2', 'weight_value': 0.4},
            {'version_id': 'v0_classical', 'weight_id': 'beta:x3', 'weight_value': 0.3},
            {'version_id': 'v0_classical', 'weight_id': 'rho:vedha', 'weight_value': 0.4},
            {'version_id': 'v0_classical', 'weight_id': 'rho:default', 'weight_value': 0.25},
            {'version_id': 'v0_classical', 'weight_id': 'd:MD', 'weight_value': 1.0},
            {'version_id': 'v0_classical', 'weight_id': 'd:AD', 'weight_value': 0.7},
        ],
        'charts': [{'birth_date': __import__('datetime').date(1984, 2, 5)}],
        'bg_synthetic_cohort': [{'build_id': 'cohort-build-1'}],
        'kala_field_routes': [
            {'id': 11, 'chart_id': CHART_ID, 'event_class': EVENT_CLASS, 'route_rank': 1,
             'path_node_ids': ['graha:Ju', 'bhava:10', f'event_class:{EVENT_CLASS}'],
             'path_edge_ids': [101], 'route_gain': 0.62, 'is_primary': True,
             'suppressed_by': []},
            {'id': 12, 'chart_id': CHART_ID, 'event_class': EVENT_CLASS, 'route_rank': 2,
             'path_node_ids': ['graha:Sa', 'bhava:10', f'event_class:{EVENT_CLASS}'],
             'path_edge_ids': [102], 'route_gain': 0.31, 'is_primary': False,
             'suppressed_by': ['vedha:Sa->10']},
        ],
        'kala_field_clocks': [
            {'chart_id': CHART_ID, 'system_id': 'vimshottari',
             'applicability_state': 'applicable', 'exclusion_reason': None,
             'competence_class': 'fruition', 'seniority_rank': 1, 'quality': 0.92,
             'quality_basis': 'moon_nakshatra_margin=1.83deg', 'is_predictive': True},
            {'chart_id': CHART_ID, 'system_id': 'yogini',
             'applicability_state': 'applicable', 'exclusion_reason': None,
             'competence_class': 'flavour', 'seniority_rank': 3, 'quality': 0.71,
             'quality_basis': 'moon_nakshatra_margin=1.83deg', 'is_predictive': True},
            # NON-PREDICTIVE by construction (§5.1 rule C-4): present, applicable,
            # and still contributing exactly nothing to λ.
            {'chart_id': CHART_ID, 'system_id': 'naisargika',
             'applicability_state': 'applicable', 'exclusion_reason': None,
             'competence_class': 'life_stage', 'seniority_rank': 6, 'quality': 1.0,
             'quality_basis': 'deterministic age bands', 'is_predictive': False},
        ],
        'kala_field_boundaries': [
            {'chart_id': CHART_ID, 'system_id': 'vimshottari', 'level': 'MD', 'lord': 'Ju',
             't_boundary': 0.0, 'period_days': 200.0, 'precision_state': 'interval',
             'sigma_t_days': 0.4},
            {'chart_id': CHART_ID, 'system_id': 'vimshottari', 'level': 'MD', 'lord': 'Sa',
             't_boundary': 200.0, 'period_days': 200.0, 'precision_state': 'interval',
             'sigma_t_days': 0.4},
            {'chart_id': CHART_ID, 'system_id': 'yogini', 'level': 'MD', 'lord': 'Ju',
             't_boundary': 0.0, 'period_days': 400.0, 'precision_state': 'interval',
             'sigma_t_days': 0.4},
            # Rule C-5: excluded at the query, so it contributes NO factor at all
            # rather than a down-weighted one.
            {'chart_id': CHART_ID, 'system_id': 'vimshottari', 'level': 'PrD', 'lord': 'Me',
             't_boundary': 10.0, 'period_days': 1.0,
             'precision_state': 'precision_unsupported', 'sigma_t_days': 0.4},
        ],
        'kala_field_primitives': [
            {'chart_id': CHART_ID, 'primitive_kind': 'contact_moon_ref', 'subject': 'Ju',
             'object_ref': 'Mo', 'polarity': 'supportive', 'class_label': None,
             'envelope': _env([(90, 0.0), (100, 1.0), (110, 0.0)]),
             'source_table': 'kala_field_kinematics', 'source_pk': '5001',
             'source_fact_id': 'fact:kin:5001'},
            {'chart_id': CHART_ID, 'primitive_kind': 'contact_lagna_ref', 'subject': 'Ju',
             'object_ref': 'Lagna', 'polarity': 'supportive', 'class_label': None,
             'envelope': _env([(95, 0.0), (102, 0.8), (112, 0.0)]),
             'source_table': 'kala_field_kinematics', 'source_pk': '5002',
             'source_fact_id': 'fact:kin:5002'},
            {'chart_id': CHART_ID, 'primitive_kind': 'vedha', 'subject': 'Sa',
             'object_ref': '10', 'polarity': 'obstructive', 'class_label': None,
             'envelope': _env([(250, 0.0), (260, 1.0), (270, 0.0)]),
             'source_table': 'kala_field_primitives', 'source_pk': '5003',
             'source_fact_id': 'fact:vedha:5003'},
        ],
        'kala_field_kinematics': [
            {'chart_id': CHART_ID, 't_days': 90.0, 'ayanamsha_id': 'lahiri'},
            {'chart_id': CHART_ID, 't_days': 100.0, 'ayanamsha_id': 'lahiri'},
            {'chart_id': CHART_ID, 't_days': 110.0, 'ayanamsha_id': 'lahiri'},
            {'chart_id': CHART_ID, 't_days': 260.0, 'ayanamsha_id': 'lahiri'},
        ],
        'kala_gochara_windows': [
            {'id': 991, 'chart_id': CHART_ID, 'event_class': EVENT_CLASS,
             'window_start': None, 'window_end': None, 'peak_date': '2026-04-16',
             'temporal_shape': 'interval'},
        ],
        'chart_facts': [
            {'chart_id': CHART_ID, 'fact_id': 'fact:kin:5001'},
            {'chart_id': CHART_ID, 'fact_id': 'fact:kin:5002'},
            {'chart_id': CHART_ID, 'fact_id': 'fact:vedha:5003'},
            # The natal Lagna longitude the §6.3 rarity axis keys on. Aries
            # (sign_id 1) — the native's real FORENSIC anchor, so the fixture's
            # cohort feature is the chart's actual one rather than an arbitrary
            # number. REFERENCED by the writer, never recomputed (§N.5).
            {'chart_id': CHART_ID, 'fact_id': 'fact:lagna:longitude',
             'fact_category': 'lagna', 'fact_key': 'longitude',
             'ayanamsha_id': 'lahiri', 'fact_value_num': 12.75},
        ],
        # §5.1 C-5 / migration 456: temporal_shape is a property of the EVENT
        # CLASS, read from the ontology — never derived from how long a
        # particular window happens to be. `domain` / `magnitude_floor` /
        # `adjacency` are §6.1's Consequence inputs; without them Q would be an
        # honest NULL and the salience vector would never exercise its
        # renormalization over a PRESENT Q.
        'brahma_event_ontology': [
            {'event_class_id': EVENT_CLASS, 'temporal_shape': 'interval',
             'domain': 'career', 'magnitude_floor': 'significant',
             'adjacency': ['relocation']},
            {'event_class_id': 'relocation', 'temporal_shape': 'point',
             'domain': 'place', 'magnitude_floor': 'moderate', 'adjacency': []},
        ],
        # The synthetic cohort, DELIBERATELY far below §6.3 rule 4's 10,000-row
        # minimum: `cohort_base_rate` then takes its own `cohort_below_minimum`
        # path and returns p=None, which is the branch the salience vector's
        # "Informativeness is NULL, never 0" rule exists for.
        'bg_synthetic_cohort_md': [],
        'brahma_class_priors': [],
        'build_substep_progress': [],
        'kala_field': [],
        'kala_field_windows': [],
        'kala_field_provenance': [],
        'kala_field_null': [],
        'kala_field_snapshots': [],
        # The lived-history corpus. Present in the fixture DB and NEVER queried.
        'lived_history_fixture': [{'i': i} for i in range(life_event_rows)],
    }
    if with_lifetime_prior:
        tables['brahma_class_priors'] = [{
            'prior_version': '1.0', 'signal_type_class': EVENT_CLASS,
            'fact_kind': 'lifetime_count_per_100y', 'source_subsystem': '*',
            'signal_tradition': '*', 'class_prior': 2.0,
        }]
    return tables

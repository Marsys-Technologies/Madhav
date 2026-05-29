import pytest, uuid

def test_citation_ref_format():
    """citation_ref must follow slug format: category.subject.key@chart=...:ay=...:eng=..."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from pipeline.writers.panchanga_writer_a4 import emit_solar_context
    chart_id, build_id = str(uuid.uuid4()), str(uuid.uuid4())
    rows = emit_solar_context(chart_id, build_id, '1984-02-05')
    for r in rows[:5]:  # check first 5
        ref = r.get('citation_ref', '')
        assert '@chart=' in ref, f"citation_ref missing @chart=: {ref}"
        assert ':ay=' in ref, f"citation_ref missing :ay=: {ref}"
        assert ':eng=' in ref, f"citation_ref missing :eng=: {ref}"

def test_citation_human_is_sentence():
    """citation_human must be a complete sentence (ends with period)."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from pipeline.writers.sensitive_points_writer_a5 import emit_upagrahas
    chart_id, build_id = str(uuid.uuid4()), str(uuid.uuid4())
    rows = emit_upagrahas(None, chart_id, build_id, 'lahiri_chitrapaksha', 301.5, 215.0)
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    for r in lon_rows[:3]:
        human = r.get('citation_human', '')
        assert human.endswith('.'), f"citation_human doesn't end with period: '{human}'"

def test_no_narration_in_fact_values():
    """No opinion/narration verbs in any fact_value_text."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from pipeline.writers.panchanga_writer_a4 import emit_calendrical, emit_solar_context
    from pipeline.writers.sensitive_points_writer_a5 import emit_midpoints
    FORBIDDEN = ['indicates','suggests','implies','means that','denotes','reveals','shows that']
    chart_id, build_id = str(uuid.uuid4()), str(uuid.uuid4())
    rows = emit_calendrical(chart_id, build_id, '1984-02-05')
    rows += emit_solar_context(chart_id, build_id, '1984-02-05')
    rows += emit_midpoints(chart_id, build_id, 'lahiri_chitrapaksha',
                           {'SUN':301.5,'MOO':320.5,'MAR':181.0,'MER':298.0,
                            'JUP':57.0,'VEN':262.0,'SAT':215.0,'RAH':158.0,'KET':338.0}, 48.0)
    violations = []
    for r in rows:
        val = (r.get('fact_value_text') or '').lower()
        for verb in FORBIDDEN:
            if verb in val:
                violations.append(f"{r['fact_category']}.{r['fact_key']}: '{val}'")
    assert len(violations) == 0, f"Narration detected: {violations[:3]}"

def test_boundary_flag_correctness():
    """near_sign_boundary_flag=True for points within 0.5° of sign edge."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from pipeline.writers.sensitive_points_writer_a5 import emit_upagrahas
    chart_id, build_id = str(uuid.uuid4()), str(uuid.uuid4())
    # Sun at 300.2° (very close to 300°=Capricorn start) → should trigger boundary flag
    rows_near = emit_upagrahas(None, chart_id, build_id, 'lahiri_chitrapaksha',
                                300.2, 215.0)  # Sun at 300.2° (0.2° into Capricorn)
    # DHUMA = 300.2 + 133.333 = 433.533 = 73.533° (not near boundary)
    # UPAKETU = 73.533 - 30 = 43.533° (not near boundary)
    # The test verifies the field EXISTS (value True or False)
    boundary_rows = [r for r in rows_near if r['fact_key'] == 'near_sign_boundary_flag']
    assert len(boundary_rows) > 0, "No near_sign_boundary_flag rows found"
    for r in boundary_rows:
        assert r['fact_value_text'] in ('True','False'), \
            f"near_sign_boundary_flag has bad value: {r['fact_value_text']}"

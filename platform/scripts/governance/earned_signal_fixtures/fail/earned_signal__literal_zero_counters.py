# FAIL fixture — reproduces F-09 and F-10 (`bo_pramana_mapa.py:262`, `:278`):
# violation counters emitted as the literal 0, with no detector that could ever
# produce a different number. A zero that was never counted is not a clean result.
#
# Also exercises the other four Python binding sites the lint recognises, so a
# regression in any one of them is caught by this single fixture.
# EXPECT-VIOLATIONS: 7   (2 dict_entry + 1 subscript_assign + 1 name_assign +
#                         1 attr_assign + 2 call_kwarg)
def build_scorecard(conn, chart_id, msr_count, trap1_count):
    scorecard = {
        "chart_id": chart_id,
        "msr_signal_count": msr_count,                 # real value — not flagged
        "divergent_flagged_count": 0,                  # (P-a) LITERAL
        "trap2_narration_leak_count": 0,               # (P-a) LITERAL
        "trap1_authority_inversion_count": trap1_count,  # real value — not flagged
    }

    # (P-e) constant-string subscript assignment
    scorecard["byte_equality_pass"] = True

    # (P-c) bare-name assignment, never rebound
    pillars_meet_reachability_pass = True

    # (P-d) attribute assignment
    conn.grounding_status = "verified"

    # (P-b) keyword argument at a call site
    _emit(conn, chart_id, passed=True, verified_fraction=1.0)

    return scorecard, pillars_meet_reachability_pass


def _emit(conn, chart_id, passed, verified_fraction):
    return (conn, chart_id, passed, verified_fraction)

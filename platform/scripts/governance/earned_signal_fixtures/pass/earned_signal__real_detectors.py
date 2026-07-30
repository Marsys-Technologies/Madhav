# PASS fixture — the correct shapes. None of these may be flagged.
#
# NOTE, and it is the honest bound of this lint: `lel_zero_leak_pass` below is
# register finding F-07, a real PROXY violation (it counts citation gaps and
# never reads the LEL). This lint deliberately does NOT flag it — the expression
# depends on a runtime value, and deciding whether that value MEASURES THE CLAIM
# is an audit judgement with no syntactic signal. That is why it lives in the
# PASS fixtures: to pin the boundary in an executable form rather than only in
# the docstring.
def build_scorecard(conn, chart_id, msr_count, trap1_count):
    # A real detector: the value depends on runtime input.
    lel_zero_leak_pass = trap1_count == 0

    # The sanctioned value for a signal with no detector yet (§N.8): None.
    no_pre_answer_pass = None

    # A counter initialiser that is genuinely rebound — not a frozen signal.
    leak_violation_count = 0
    for row in _fetch(conn, chart_id):
        if _leaks(row):
            leak_violation_count += 1

    scorecard = {
        "chart_id": chart_id,
        "lel_zero_leak_pass": lel_zero_leak_pass,
        "no_pre_answer_pass": no_pre_answer_pass,
        "trap2_narration_leak_count": leak_violation_count,
        "byte_equality_pass": _bytes_equal(conn, chart_id),
        # Lifecycle / transport state is not a verification claim, and bare
        # `status` is outside the curated vocabulary by design (see the
        # rollout calibration note in the lint's docstring).
        "status": "queued",
        "http_status": 200,
    }

    # A placeholder that IS overwritten later in the same file via subscript:
    # suppressed, because the literal is not the final value.
    scorecard["divergent_flagged_count"] = 0
    scorecard["divergent_flagged_count"] = _count_divergent(conn, chart_id)

    return scorecard


def _fetch(conn, chart_id):
    return []


def _leaks(row):
    return False


def _bytes_equal(conn, chart_id):
    return False


def _count_divergent(conn, chart_id):
    return 0

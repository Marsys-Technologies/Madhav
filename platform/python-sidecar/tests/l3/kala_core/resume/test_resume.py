from services.kala_core.resume import ResumeContext, pending_grains, record_completion


class Cursor:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params):
        self.calls.append((sql, params))

    def fetchall(self):
        return self.rows


class Connection:
    def __init__(self, rows):
        self.cursor_instance = Cursor(rows)

    def cursor(self):
        return self.cursor_instance


def _context(input_vector="inputs-v1"):
    return ResumeContext("candidate-g1", input_vector, "code-sha")


def test_plan_time_read_never_deletes_and_skips_only_matching_content_bound_grains():
    context = _context()
    conn = Connection([{"substep_key": "career", "build_fingerprint": context.fingerprint("career")}])

    pending = pending_grains(
        conn, chart_id="chart", asset_id="ka_kshetra", context=context,
        grains=("career", "health"),
    )

    assert pending == ("health",)
    assert all("DELETE" not in sql.upper() for sql, _ in conn.cursor_instance.calls)


def test_changed_input_vector_invalidates_recorded_progress():
    old_context = _context("inputs-v1")
    conn = Connection([{"substep_key": "career", "build_fingerprint": old_context.fingerprint("career")}])

    pending = pending_grains(
        conn, chart_id="chart", asset_id="ka_kshetra", context=_context("inputs-v2"),
        grains=("career",),
    )

    assert pending == ("career",)


def test_record_binds_candidate_input_code_and_grain_in_the_stored_fingerprint():
    context = _context()
    conn = Connection([])

    record_completion(
        conn, chart_id="chart", asset_id="ka_kshetra", context=context,
        grain="career", rows_written=4,
    )

    _, params = conn.cursor_instance.calls[-1]
    assert params[3] == context.fingerprint("career")
    assert params[3] != ResumeContext("candidate-g2", "inputs-v1", "code-sha").fingerprint("career")

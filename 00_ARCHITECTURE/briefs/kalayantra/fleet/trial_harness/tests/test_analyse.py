"""`analyse` aggregation on canned query results (no database): the per-grain / per-path numbered-or-blank-by-reason report, the any-reason window counts that the wiring
gate and the solver-budget cap read, and the row digest.  The SQL text itself is exercised by the real runs."""
import pytest

import trial_slice as ts

CL = ["bereavement", "major_loss"]


class Cur:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0]

    def __iter__(self):
        return iter(self.rows)


class Conn:
    def __init__(self, table):
        self.table = table

    def execute(self, sql, params=()):
        if sql in self.table:
            return Cur(self.table[sql])
        if "FROM public.ka_gochara_eval_window_record" in sql or "relationship_record" in sql or "ka_gochara_contact" in sql or "ka_gochara_near_miss" in sql:
            return Cur([(7,)])
        raise AssertionError(f"unexpected SQL: {sql[:80]}")


class FakeResultPolicy:
    @staticmethod
    def manifest_policy(conn, chart, gen):
        return "window_qualification/1"


def canned():
    return {
        ts.WINDOW_SQL: [("bereavement", "P3", 10, 8, 8, 8, 0, 8, 2, 0, 0, 0), ("bereavement", "P1", 20, 0, 0, 0, 0, 0, 20, 0, 0, 0),
                        ("major_loss", "P3", 5, 4, 4, 4, 0, 4, 1, 0, 0, 0)],
        ts.GRAIN_SQL: [("bereavement", "P1", "1.3.0", 20, 0, 0, 20), ("bereavement", "P3", "1.3.0", 10, 8, 8, 2), ("major_loss", "P3", "1.3.0", 5, 4, 4, 1)],
        ts.GRAIN_REASON_SQL: [("bereavement", "P1", "1.3.0", "agent_nature_node_undecided", 20), ("bereavement", "P3", "1.3.0", "state_boundaries_incomplete", 2),
                              ("major_loss", "P3", "1.3.0", "solver_budget_exhausted", 1)],
        # a P1 window's stored reason is only the first sorted one; the same windows also carry orb_not_ratified as a SECONDARY unresolved reason
        ts.GRAIN_ANY_REASON_SQL: [("bereavement", "P1", "1.3.0", "agent_nature_node_undecided", 20), ("bereavement", "P1", "1.3.0", "orb_not_ratified", 3),
                                  ("bereavement", "P3", "1.3.0", "state_boundaries_incomplete", 2), ("major_loss", "P3", "1.3.0", "solver_budget_exhausted", 1)],
        ts.VALENCE_SQL: [("bereavement", "favourable", 8), ("bereavement", "unqualified", 22), ("major_loss", "mixed", 4), ("major_loss", "unqualified", 1)],
        ts.BLANK_SQL: [("bereavement", "agent_nature_node_undecided", 20), ("bereavement", "state_boundaries_incomplete", 2), ("major_loss", "solver_budget_exhausted", 1)],
        ts.UNRESOLVED_SQL: [("bereavement", "orb_not_ratified", 3, 3)],
        ts.UNRESOLVED_ALL_SQL: [("bereavement", "orb_not_ratified", 3, 3)],
        ts.POLICY_SQL: [("window_qualification/1", 35)],
    }


def run():
    return ts.analyse(Conn(canned()), {"classes": CL, "requested_policy": "window_qualification/1"}, {"result_policy": FakeResultPolicy})


def test_paths_pool_grains_across_classes_with_numbered_share_and_reasons():
    rep = run()
    p3 = rep["paths"]["P3"]
    assert (p3["windows"], p3["numbered"], p3["blank"]) == (15, 12, 3) and p3["numbered_share"] == pytest.approx(0.8)
    assert p3["blank_by_reason"] == {"solver_budget_exhausted": 1, "state_boundaries_incomplete": 2}
    p1 = rep["paths"]["P1"]
    assert (p1["windows"], p1["numbered"]) == (20, 0) and p1["numbered_share"] == 0.0
    assert p1["versions"] == {"1.3.0": 20}


def test_reason_windows_any_counts_secondary_reasons_the_stored_reason_hides():
    rep = run()
    assert rep["reason_windows_any"]["orb_not_ratified"] == 3          # only a SECONDARY reason in the stored rows; G-2 must still see it
    assert rep["reason_windows_any"]["solver_budget_exhausted"] == 1
    assert "orb_not_ratified" not in rep["paths"]["P1"]["blank_by_reason"]       # ... while the primary report does not contain it


def test_class_and_total_counts_and_policy_effect():
    rep = run()
    assert rep["classes"]["bereavement"]["windows_total"] == 30 and rep["totals"]["windows_total"] == 35 and rep["totals"]["with_peak"] == 12
    assert rep["totals"]["blank_reasons"]["solver_budget_exhausted"] == 1
    assert rep["policy_effect"]["took_effect"] is True and rep["slice_counts"]["window_records"] == 7
    assert rep["by_class_path"]["major_loss"]["P3"]["blank_by_reason"] == {"solver_budget_exhausted": 1}


def test_a_policy_that_did_not_take_effect_reads_false():
    t = canned()
    t[ts.POLICY_SQL] = [("window_qualification/1", 30), ("all_null_candidate/1", 5)]
    rep = ts.analyse(Conn(t), {"classes": CL, "requested_policy": "window_qualification/1"}, {"result_policy": FakeResultPolicy})
    assert rep["policy_effect"]["took_effect"] is False


def test_the_analysis_feeds_the_gate_evaluator_inputs():
    # the aggregate keys the evaluator reads are exactly the ones `analyse` writes
    import gates
    rep = run()
    assert set(rep["paths"]["P3"]) >= {"windows", "numbered"} and isinstance(rep["reason_windows_any"], dict)
    assert gates.path_shares(rep)["P3"]["share"] == pytest.approx(0.8)

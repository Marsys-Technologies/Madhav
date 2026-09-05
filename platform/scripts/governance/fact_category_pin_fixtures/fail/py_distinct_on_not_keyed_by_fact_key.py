"""FAIL fixture (issue #1794): DISTINCT ON that does NOT name fact_key is still unsafe.

The counterpart to pass/py_distinct_on_keyed_by_fact_key.py, and the reason that fix
is a narrowing rather than an exemption for DISTINCT ON generally. Keyed only by
fact_subject, this collapses every fact_key variant of a subject to whichever row the
ORDER BY happens to surface -- deterministic, and wrong whenever the category holds
more than one measurement per subject.
"""
SQL = """
    SELECT DISTINCT ON (fact_subject)
           fact_subject, fact_value_num
      FROM chart_facts
     WHERE chart_id=%s AND fact_category='graha_shadbala_total'
     ORDER BY fact_subject, fact_value_num ASC
"""

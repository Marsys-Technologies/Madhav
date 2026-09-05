"""PASS fixture (issue #1794): DISTINCT ON whose key list names fact_key IS a pin.

`DISTINCT ON (fact_subject, fact_key)` returns one row PER (fact_subject, fact_key),
so it cannot conflate two incommensurable fact_key populations the way an unpinned
`ORDER BY ... LIMIT 1` can. It is the safe pattern, not the defect.

The first draft of the F-C14 tightening treated every DISTINCT ON as a bare
reduction and demanded a separate `fact_key = ...` filter on top. That turned
`main` red on bo_laksana.py:992 -- a correct query -- and every queued PR failed a
required check until it was fixed.
"""
SQL = """
    SELECT DISTINCT ON (fact_subject, fact_key)
           fact_subject, fact_key, fact_value_num
      FROM chart_facts
     WHERE chart_id=%s AND ayanamsha_id=%s
       AND fact_category='ashtakavarga_bindu_per_varga'
     ORDER BY fact_subject, fact_key, computed_at DESC
"""

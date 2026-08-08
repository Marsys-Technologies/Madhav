# FAIL fixture — a literal reproduction of the Lane A1 ga_vargas_writer.py
# defect (pre-fix): the floored-body scope-cap sentinel emitted fact_subject
# via a bare .upper() on floored_body, bypassing BODY_TO_SUBJECT entirely.
for floored_body in FLOORED_BODIES:
    rows.append({
        "fact_category": "structural_scope_cap",
        "fact_subject": floored_body.upper(),
        "fact_key": "D_ALL",
    })

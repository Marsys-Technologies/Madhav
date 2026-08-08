# PASS fixture — same safe idiom, BODY_TO_SUBJECT variant (ga_vargas_writer.py's
# floored-body sentinel, post-fix).
for floored_body in FLOORED_BODIES:
    rows.append({
        "fact_category": "structural_scope_cap",
        "fact_subject": BODY_TO_SUBJECT.get(floored_body, floored_body.upper()),
        "fact_key": "D_ALL",
    })

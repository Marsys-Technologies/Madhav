# PASS fixture — .upper() on a NON-graha identifier (sign name). This guard's
# scope is Lane A1's graha defect class specifically, not a blanket ban on
# .upper() in fact_subject construction — this must stay silent.
for sign_name in ZODIAC_SIGNS:
    rows.append({
        "fact_category": "sign_attributes",
        "fact_subject": sign_name.upper(),
        "fact_key": "lord",
    })

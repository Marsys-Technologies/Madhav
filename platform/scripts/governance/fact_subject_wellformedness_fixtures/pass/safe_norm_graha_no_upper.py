# PASS fixture — routes fully through norm_graha(), no .upper() call at all.
for graha in ALL_GRAHAS:
    rows.append({
        "fact_category": "graha_position",
        "fact_subject": norm_graha(graha),
        "fact_key": "longitude_sidereal",
    })

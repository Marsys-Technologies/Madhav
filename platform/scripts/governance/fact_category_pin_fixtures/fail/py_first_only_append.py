def first_only(conn) -> list[tuple]:
    rows = conn.execute("""SELECT fact_id, fact_key, fact_value_num FROM chart_facts WHERE chart_id = %s AND fact_category = 'fixture'""").fetchall()
    out = []
    for row in rows:
        if not out:
            out.append((row["fact_key"], row["fact_value_num"]))
    return out

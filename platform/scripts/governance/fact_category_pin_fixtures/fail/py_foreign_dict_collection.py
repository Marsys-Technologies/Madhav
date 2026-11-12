def read(conn, other) -> list[dict]:
    rows = conn.execute("""SELECT fact_id, fact_key, fact_value_num FROM chart_facts WHERE chart_id = %s AND fact_category = 'fixture'""").fetchall()
    out = []
    for row in rows:
        out.append({"fact_key": other["fact_key"], "value": row["fact_value_num"]})
    return out

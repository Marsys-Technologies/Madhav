"""bo_samskara: the multi-row INSERT's column list and placeholders are literal SQL text, byte-identical to what the former run-time join built.

The writer used to build the column list with ", ".join(_COLS) and the placeholders with a comprehension over _COLS, which the census writer scan cannot read as a column list
(the written columns were not statically visible). They are now literal text. This test pins that the SQL sent to PostgreSQL is UNCHANGED for every row count a batch can have
(1 .. _BATCH_SIZE = 500), that the literal column order still equals _COLS (the order the bind values are collected in), and that exactly one placeholder is the vector cast.
"""
from pipeline.orchestrator.writers import bo_samskara as bs


def _former_sql(n: int) -> str:
    head = "INSERT INTO public.bodha_signal_embeddings (\n  " + ", ".join(bs._COLS) + "\n) VALUES\n"
    row = ", ".join("%s::vector" if c == "embedding_vec" else "%s" for c in bs._COLS)
    return head + ",\n".join(f"({row})" for _ in range(n)) + bs._MULTI_INSERT_TAIL


def test_literal_sql_equals_the_former_runtime_join_for_every_batch_size():
    assert bs._BATCH_SIZE == 500
    for n in range(1, bs._BATCH_SIZE + 1):
        assert bs._multi_insert_sql(n) == _former_sql(n), n


def test_literal_column_order_is_the_bind_order_and_placeholders_match():
    cols_line = bs._MULTI_INSERT_HEAD.split("\n")[1].strip()
    assert [c.strip() for c in cols_line.split(",")] == list(bs._COLS)
    ph = [p.strip() for p in bs._ROW_PLACEHOLDERS.split(",")]
    assert len(ph) == len(bs._COLS)
    assert [c for c, p in zip(bs._COLS, ph) if p == "%s::vector"] == ["embedding_vec"]
    assert all(p in ("%s", "%s::vector") for p in ph)


def test_the_head_text_is_exactly_three_lines():
    assert bs._MULTI_INSERT_HEAD.count("\n") == 3
    assert bs._MULTI_INSERT_HEAD.startswith("INSERT INTO public.bodha_signal_embeddings (\n  ")
    assert bs._MULTI_INSERT_HEAD.endswith("\n) VALUES\n")

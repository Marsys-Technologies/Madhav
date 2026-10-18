"""Decode captured producer binds using the emitted INSERT column/value lists.

These writers use positional %s binds, optionally cast, and NOW() for the
computed timestamp. Refuse malformed shape rather than silently zip/truncate.
"""
import re


def insert_bindings(sql, params):
    match = re.search(r"INSERT INTO [\w.]+\s*\(([^)]+)\)\s*VALUES\s*\((.*)\)\s*;?\s*$", sql, re.S | re.I)
    assert match, f"not a supported producer INSERT: {sql}"
    columns = [column.strip() for column in match[1].split(',')]
    values = [value.strip() for value in match[2].split(',')]
    assert len(columns) == len(values), "INSERT column/value counts disagree"
    assert len(set(columns)) == len(columns), "duplicate INSERT column"
    bound_columns = []
    for column, value in zip(columns, values):
        if re.fullmatch(r"%s(?:::\w+)?", value):
            bound_columns.append(column)
        else:
            assert value.upper() == 'NOW()', f"unsupported INSERT value: {value}"
    assert len(bound_columns) == len(params), "INSERT placeholder/bind counts disagree"
    return dict(zip(bound_columns, params))
